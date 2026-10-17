/* edgesearch.js — searchcore's Index, read from shards instead of memory.
 *
 * Nan, 2026-09-10: "Worker can run search engine, that's fine." The page builds
 * its Index in the browser from data/index.json (537 MB of heap, measured); an
 * isolate cannot. publish/emit_edge_index.js writes the SAME postings at build
 * time as shards under api/v1/edge/, and this class walks them: the vocabulary
 * (every word and every loose key, ~6 MB) is loaded once for the fuzzy and
 * prefix scans; a posting list is fetched only when a query needs it, and kept
 * in a small cache. The ranking is searchcore's own — tiers, weights,
 * coverage, loosen-by-steps, the anchored retry, the Thai mend — line for line
 * with Index._resolve / Index.search, so tests/test_edge_search.js can hold the
 * two to the same answer.
 *
 * `load(relpath)` is whatever the host provides: R2 in the Worker,
 * fs in the tests. It returns parsed JSON or null.
 */
import SEARCHCORE from "./searchcore.js";

const { TIER_EXACT, TIER_THESAURUS, TIER_LOOSE, TIER_PARTIAL, TIER_ORDER, TIER_WEIGHT,
        norm, loose, edits, slack, hasThai } = SEARCHCORE;

const SHARDS = 256;
const CACHE_MAX = 400;   // shard files held in the isolate (≈ a few MB)

/* md5 of the word, first two bytes, mod 256 — the emitter's rule. WebCrypto's
 * digest is async and MD5 is not in it, so the emitter's choice is mirrored
 * with a tiny MD5 here. */
function md5first16(str) {
  const bytes = new TextEncoder().encode(str);
  return md5(bytes).readUInt16BE(0);
}
export function shardOf(word) { return md5first16(word) % SHARDS; }

export class EdgeIndex {
  constructor(core, load, base = "api/v1/edge/") {
    this.core = core; this.load = load; this.base = base;
    this.ready = null; this.cache = new Map();
  }
  async init() {
    if (this.ready) return this.ready;
    this.ready = (async () => {
      const [meta, vocab, ids] = await Promise.all([
        this.load(this.base + "meta.json"), this.load(this.base + "vocab.json"), this.load(this.base + "ids.json")]);
      if (!meta || !vocab || !ids) throw new Error("edge index missing");
      this.meta = meta; this.ids = ids;
      /* layout 2 (emit_edge_index.js, 2026-10-13): postings carry kept row
       * numbers and rank.json gives each one's position in index.json, which
       * is the tie order. No rank = layout 1, where the number is the position. */
      this.rank = meta.rank ? await this.load(this.base + meta.rank) : null;
      if (meta.rank && !this.rank) throw new Error("edge index missing");
      this.fields = new Map(meta.fields);           // [[name, weight], …]
      this.vocab = new Map();                        // field -> Set(words)
      this.byLen = new Map();                        // field -> Map(len -> [looseKey])
      for (const [name] of this.fields) {
        this.vocab.set(name, new Set(vocab[name] || []));
        const lk = vocab[name + "_loose"] || [];
        this.vocab.set(name + "_loose", new Set(lk));
        const buckets = new Map();
        for (const w of lk) { if (!buckets.has(w.length)) buckets.set(w.length, []); buckets.get(w.length).push(w); }
        this.byLen.set(name, buckets);
      }
      // The mending dictionary: Thai words of the name field by loose key.
      this.mend = new Map(); this.mendByLen = new Map();
      for (const w of this.vocab.get("name") || []) {
        if (!hasThai(w) || w.length < 3) continue;
        const k = loose(w); if (!k) continue;
        if (!this.mend.has(k)) { this.mend.set(k, []); if (!this.mendByLen.has(k.length)) this.mendByLen.set(k.length, []); this.mendByLen.get(k.length).push(k); }
        this.mend.get(k).push(w);
      }
      return true;
    })();
    return this.ready;
  }

  // Index.nearest, over the vocabulary instead of the postings.
  nearest(chunk) {
    chunk = norm(chunk);
    if (!chunk || !hasThai(chunk)) return this.core.seg.nearest(chunk);
    if ((this.vocab.get("name") || new Set()).has(chunk)) return null;
    const key = loose(chunk); if (!key) return null;
    const pick = (words) => words.slice().sort((a, b) => Math.abs(a.length - chunk.length) - Math.abs(b.length - chunk.length) || (a < b ? -1 : a > b ? 1 : 0))[0];
    if (this.mend.has(key)) return pick(this.mend.get(key));
    const cap = slack(key); let best = null, bestD = cap + 1;
    if (cap) {
      for (let L = key.length - cap; L <= key.length + cap; L++) {
        for (const k of (this.mendByLen.get(L) || [])) { const d = edits(key, k, cap); if (d < bestD) { best = k; bestD = d; if (d === 1) break; } }
        if (bestD === 1) break;
      }
    }
    if (best !== null) return pick(this.mend.get(best));
    return this.core.seg.nearest(chunk);
  }

  async shard(dir, word) {
    const key = dir + "/" + String(shardOf(word)).padStart(3, "0");
    let s = this.cache.get(key);
    if (s === undefined) {
      s = (await this.load(this.base + key + ".json")) || {};
      if (this.cache.size >= CACHE_MAX) this.cache.delete(this.cache.keys().next().value);
      this.cache.set(key, s);
    }
    return s[word] || null;
  }

  // Index._resolve, async: {docid: tier} for one term in one field.
  async resolve(term, name, extraSlack) {
    const tiers = new Map();
    const mark = (ids, tier) => { const rank = TIER_ORDER.indexOf(tier); for (const did of ids || []) { const prev = tiers.get(did); if (prev === undefined || rank < TIER_ORDER.indexOf(prev)) tiers.set(did, tier); } };
    const words = this.vocab.get(name), lkeys = this.vocab.get(name + "_loose");
    const first = term.variants.length ? term.variants[0] : "";
    const wants = [];   // [dir, word, tier]
    if (first && words.has(first)) wants.push([name, first, TIER_EXACT]);
    for (let k = 1; k < term.variants.length; k++) { const v = term.variants[k]; if (words.has(v)) wants.push([name, v, TIER_THESAURUS]); }
    for (const lv of term.looseVariants) if (lkeys.has(lv)) wants.push([name + "-loose", lv, TIER_LOOSE]);
    const lv = term.looseOwn, cap = lv ? slack(lv) + (extraSlack || 0) : 0;
    if (cap) {
      const byLen = this.byLen.get(name) || new Map();
      for (let L = lv.length - cap; L <= lv.length + cap; L++)
        for (const w of (byLen.get(L) || [])) if (edits(lv, w, cap) <= cap) wants.push([name + "-loose", w, TIER_LOOSE]);
    }
    const lists = await Promise.all(wants.map(([dir, w]) => this.shard(dir, w)));
    lists.forEach((ids, i) => mark(ids, wants[i][2]));
    if (!tiers.size && first && first.length >= 3) {
      const pref = [];
      for (const w of words) if (w.indexOf(first) === 0 || w.indexOf(first) !== -1) pref.push(w);
      const plists = await Promise.all(pref.map(w => this.shard(name, w)));
      plists.forEach(ids => mark(ids, TIER_PARTIAL));
    }
    return tiers;
  }

  // Index.search, async. Returns [{did, id, score, tier, coverage}].
  async search(an, limit) {
    if (!an.terms.length) return [];
    const resolveAll = async (term, extra) => {
      const best = new Map();
      for (const [name, weight] of this.fields) {
        for (const [did, tier] of await this.resolve(term, name, extra)) {
          const value = TIER_WEIGHT[tier] * weight; const prev = best.get(did);
          if (prev === undefined || value > prev[0]) best.set(did, [value, tier]);
        }
      }
      return best;
    };
    const resolved = await Promise.all(an.terms.map(t => resolveAll(t, 0)));
    let anchored = false;
    for (const r of resolved) { for (const [, tier] of r) if (tier === TIER_EXACT || tier === TIER_THESAURUS) { anchored = true; break; } if (anchored) break; }
    if (anchored) for (let i = 0; i < an.terms.length; i++) if (!resolved[i].size) resolved[i] = await resolveAll(an.terms[i], 1);
    const acc = new Map();
    for (const best of resolved) for (const [did, [value, tier]] of best) {
      let row = acc.get(did); if (!row) { row = [0, TIER_EXACT, 0]; acc.set(did, row); }
      row[0] += value; row[2] += 1; if (TIER_ORDER.indexOf(tier) > TIER_ORDER.indexOf(row[1])) row[1] = tier;
    }
    const n = an.terms.length, out = [];
    for (const [did, [total, worst, matched]] of acc) {
      const coverage = matched / n;
      if (this.ids[did] == null) continue;           // a retired number from a shard one publish old
      out.push({ did, id: this.ids[did], score: total * coverage * coverage, tier: coverage < 1 ? TIER_PARTIAL : worst, coverage });
    }
    const rank = this.rank;
    out.sort((a, b) => b.score - a.score || (rank ? rank[a.did] - rank[b.did] : a.did - b.did));
    const whole = out.filter(r => r.coverage >= 1);
    const kept = whole.length ? whole : out;
    return limit ? kept.slice(0, limit) : kept;
  }
}

/* ---- a minimal MD5, for the shard key only. RFC 1321, no dependencies. ---- */
function md5(bytes) {
  const K = new Int32Array(64), S = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21];
  for (let i = 0; i < 64; i++) K[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 4294967296) | 0;
  const len = bytes.length, padLen = (((len + 8) >> 6) + 1) << 6, buf = new Uint8Array(padLen);
  buf.set(bytes); buf[len] = 0x80;
  const bits = len * 8; buf[padLen - 8] = bits & 0xff; buf[padLen - 7] = (bits >>> 8) & 0xff; buf[padLen - 6] = (bits >>> 16) & 0xff; buf[padLen - 5] = (bits >>> 24) & 0xff;
  const M = new Int32Array(buf.buffer, buf.byteOffset, padLen >> 2);
  let a0 = 0x67452301 | 0, b0 = 0xefcdab89 | 0, c0 = 0x98badcfe | 0, d0 = 0x10325476 | 0;
  const rotl = (x, c) => (x << c) | (x >>> (32 - c));
  for (let i = 0; i < M.length; i += 16) {
    let A = a0, B = b0, C = c0, D = d0;
    for (let j = 0; j < 64; j++) {
      let F, g;
      if (j < 16) { F = (B & C) | (~B & D); g = j; }
      else if (j < 32) { F = (D & B) | (~D & C); g = (5 * j + 1) % 16; }
      else if (j < 48) { F = B ^ C ^ D; g = (3 * j + 5) % 16; }
      else { F = C ^ (B | ~D); g = (7 * j) % 16; }
      const tmp = D; D = C; C = B;
      B = (B + rotl((A + F + K[j] + M[i + g]) | 0, S[j])) | 0; A = tmp;
    }
    a0 = (a0 + A) | 0; b0 = (b0 + B) | 0; c0 = (c0 + C) | 0; d0 = (d0 + D) | 0;
  }
  const out = new Uint8Array(16), dv = new DataView(out.buffer);
  dv.setInt32(0, a0, true); dv.setInt32(4, b0, true); dv.setInt32(8, c0, true); dv.setInt32(12, d0, true);
  return { readUInt16BE: (o) => (out[o] << 8) | out[o + 1] };
}
