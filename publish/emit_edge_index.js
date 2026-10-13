#!/usr/bin/env node
/* emit_edge_index.js — the search engine's postings, written at build time so
 * the Worker can run searchcore.js WITHOUT holding the index in memory.
 *
 * Nan, 2026-09-10: "Worker can run search engine, that's fine." The in-page
 * engine builds its Index from data/index.json in the browser — 537 MB of V8
 * heap for 87,833 rows, measured — which no isolate can hold. So the exact
 * thing the page builds is built here once, by the same shipped searchcore.js
 * over the same rows, and written as SHARDS: a query touches a handful of
 * small files, R2 serves them, the edge caches them, and the isolate keeps
 * only the vocabulary (for the fuzzy and prefix scans) and the API index it
 * already holds.
 *
 *   docs/api/v1/edge/meta.json         fields, weights, shard count, row count
 *   docs/api/v1/edge/vocab.json        {field: [word…], field_loose: [key…]}
 *   docs/api/v1/edge/ids.json          row number -> place id (null: retired)
 *   docs/api/v1/edge/rank.json         row number -> position in index.json (-1: retired)
 *   docs/api/v1/edge/<field>/<nnn>.json   {word: [row, row…]}   exact words
 *   docs/api/v1/edge/<field>-loose/<nnn>.json                  loose keys
 *
 * ROW NUMBERS ARE KEPT, NOT POSITIONS (Nan, 2026-10-13, "do a": R2 bills each
 * changed object). A place has a number for good, noted in the ledger
 * (MD_EDGE_ROWIDS; /srv/state/edge-rowids.json on the build server, else
 * cache/edge-rowids.json). One record added or removed used to shift every
 * later position and rewrite all 1,024 shards; now only the shards holding
 * that record's words change, plus ids.json and rank.json. rank.json keeps the
 * tie order of index.json for the reader. Words inside a shard are sorted so
 * the bytes depend on the content alone.
 *
 * Same fields and weights as build.py's pipeline (name 1.0 / shelf 0.45, the
 * province words in shelf, a held row on its name and province alone). If the
 * page's `index.add` changes, change addRow() here — tests/test_edge_search.js
 * compares the two over a sample of queries and fails on drift.
 *
 *   node publish/emit_edge_index.js [docs-dir]
 */
"use strict";
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const DOCS = path.resolve(process.argv[2] || path.join(__dirname, "..", "docs"));
const D = path.join(DOCS, "data");
require(path.join(__dirname, "..", "assets", "searchcore.js"));
const SC = globalThis.SEARCHCORE;
const SHARDS = 256;
const PROVWORDS = { cm: "เชียงใหม่ chiang mai chiangmai", cr: "เชียงราย chiang rai chiangrai" };

function addRow(index, e) {
  // THE TWIN OF THE PAGE. build.py's pipeline: name = nm|n, em|e, a, r at 1.0;
  // shelf = shelf words + province words + k at 0.45; a held row (hd) is the
  // province words alone in shelf. Shelf WORDS on the page come from the
  // category tables (MD_CATWORDS/MD_SUBWORDS); here the codes stand in for
  // them and the words ride in the thesaurus, which maps both ways.
  const f = { name: [[e.nm || e.n, e.em || e.e, e.a, e.r].filter(Boolean).join(" "), 1.0] };
  f.shelf = [e.hd ? (PROVWORDS[e.p] || "")
                  : ((e.c || []).join(" ") + " " + (e.su || []).map(s => s.replace(/-/g, " ")).join(" ") + " " + (PROVWORDS[e.p] || "") + " " + (e.k || "")), 0.45];
  index.add(e, f);
}

/* The ledger: place id -> its row number, never reused. A place that leaves
 * keeps its number (ids.json holds null there). Lost ledger = a fresh
 * numbering, correct and one full rewrite. */
const LEDGER = process.env.MD_EDGE_ROWIDS
  || (fs.existsSync("/srv/state") ? "/srv/state/edge-rowids.json" : path.join(__dirname, "..", "cache", "edge-rowids.json"));

function rowNumbers(rows) {
  let led = { next: 0, ids: {} };
  try { const j = JSON.parse(fs.readFileSync(LEDGER, "utf8")); if (j && j.ids && Number.isInteger(j.next)) led = j; } catch (e) { /* none yet */ }
  const before = led.next;
  const seen = new Map();
  const num = rows.map(r => {
    const n = seen.get(r.id) || 0; seen.set(r.id, n + 1);
    const key = n ? r.id + "#" + n : String(r.id);     // a repeated id gets its own number
    if (!(key in led.ids)) led.ids[key] = led.next++;
    return led.ids[key];
  });
  if (led.next !== before) {
    fs.mkdirSync(path.dirname(LEDGER), { recursive: true });
    fs.writeFileSync(LEDGER + ".tmp", JSON.stringify(led));
    fs.renameSync(LEDGER + ".tmp", LEDGER);
  }
  return { num, total: led.next, added: led.next - before };
}

function shardOf(word) {
  return crypto.createHash("md5").update(word).digest().readUInt16BE(0) % SHARDS;
}

function main() {
  const t0 = Date.now();
  const rows = JSON.parse(fs.readFileSync(path.join(D, "index.json"), "utf8"));
  const thes = JSON.parse(fs.readFileSync(path.join(D, "search_thesaurus.json"), "utf8")).groups;
  const seg = fs.readFileSync(path.join(D, "search_segdict.txt"), "utf8").split("\n").filter(l => l && l[0] !== "#");
  const core = new SC.SearchCore(thes, seg);
  const index = new SC.Index(core);
  for (const e of rows) addRow(index, e);
  index.finalize();
  const { num, total, added } = rowNumbers(rows);
  const out = path.join(DOCS, "api", "v1", "edge");
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(out, { recursive: true });
  const vocab = {};
  let files = 0, bytes = 0;
  const write = (dir, post) => {
    const buckets = new Map();
    const words = Array.from(post).sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    for (const [w, ids] of words) {
      const s = shardOf(w);
      if (!buckets.has(s)) buckets.set(s, {});
      buckets.get(s)[w] = Array.from(ids, i => num[i]).sort((a, b) => a - b);
    }
    fs.mkdirSync(path.join(out, dir), { recursive: true });
    for (const [s, obj] of buckets) {
      const p = path.join(out, dir, String(s).padStart(3, "0") + ".json");
      const txt = JSON.stringify(obj);
      fs.writeFileSync(p, txt); files++; bytes += txt.length;
    }
  };
  for (const [name, post] of index.postings) { vocab[name] = Array.from(post.keys()); write(name, post); }
  for (const [name, lpost] of index.loosePostings) { vocab[name + "_loose"] = Array.from(lpost.keys()); write(name + "-loose", lpost); }
  fs.writeFileSync(path.join(out, "vocab.json"), JSON.stringify(vocab));
  const ids = new Array(total).fill(null), rank = new Array(total).fill(-1);
  rows.forEach((r, i) => { ids[num[i]] = r.id; rank[num[i]] = i; });
  fs.writeFileSync(path.join(out, "ids.json"), JSON.stringify(ids));
  fs.writeFileSync(path.join(out, "rank.json"), JSON.stringify(rank));
  const meta = { generated: new Date().toISOString().slice(0, 10), rows: rows.length, shards: SHARDS, layout: 2, rank: "rank.json",
                 fields: Array.from(index.fields.entries()), hash: "md5:be16 % " + SHARDS,
                 files, bytes, note: "postings by kept row number into ids.json; rank.json gives index.json order; built by publish/emit_edge_index.js from the shipped searchcore.js" };
  fs.writeFileSync(path.join(out, "meta.json"), JSON.stringify(meta));
  console.log(`  edge index: ${rows.length.toLocaleString()} rows · ${files} shard files · ${(bytes / 1048576).toFixed(1)} MB · ${added.toLocaleString()} new numbers · vocab ${Object.values(vocab).reduce((a, v) => a + v.length, 0).toLocaleString()} keys · ${Date.now() - t0} ms`);
}
main();
