/* The meaning half of /find (Nan, 2026-10-04: "both").
 *
 * fleetsearch/embed.py puts every page /find holds into the Vectorize index
 * `motdang-find` as a bge-m3 vector. Here the query is embedded with the SAME
 * model — a different one returns plausible nonsense rather than failing —
 * and the closest pages come back with their address, title and abstract.
 *
 * Two uses, both bounded:
 *   boost   a page the words found AND the meaning found counts up to 1.6
 *           times, read by address like a learned tap (findlearn.js), so it
 *           reorders the word matches and stays below a title tier;
 *   rescue  when the words find two pages or fewer, the closest pages by
 *           meaning are listed under their own heading.
 *
 * Any failure (no binding, AI down, index empty) answers null and /find is
 * the word search it was. */
export const MODEL = "@cf/baai/bge-m3";
const TOP_K = 20;            // the most Vectorize returns with full metadata
const FLOOR = 0.37;          // below this cosine a page is not boosted (noise tops 0.33 on the full index, 10/4)
const FULL = 0.47;           // at or above it the boost is whole
const BOOST = 0.6;           // 1.0 … 1.6
const RESCUE = 0.40;         // a rescued page must be at least this close
const MEMO = new Map();
const MEMO_MAX = 500;
const MEMO_MS = 600000;

/* The embedding call takes 0.6–4 s at the edge, and /find answers in a
 * fraction of that. So the reader waits at most BUDGET ms: an answer not back
 * by then finishes in the background, is kept in the colo's cache for a day,
 * and the next reader asking the same words gets it at once. `late` tells
 * the caller not to cache a page built without it. */
const BUDGET = 250;
const KEEP_S = 86400;
const keyOf = (k) => new Request(`https://motdang.net/__meaning?q=${encodeURIComponent(k)}`);
export async function meaningSoon(env, q, ctx) {
  const k = String(q || "").trim().toLowerCase();
  if (!env || !env.AI || !env.FIND_VEC || k.length < 2) return { hits: null, late: false };
  const memo = MEMO.get(k);
  if (memo && Date.now() - memo.at < MEMO_MS) return { hits: memo.hits, late: false };
  let cache = null;
  try { cache = caches.default; } catch { cache = null; }
  if (cache) {
    try {
      const hit = await cache.match(keyOf(k));
      if (hit) {
        const hits = await hit.json();
        remember(k, hits);
        return { hits, late: false };
      }
    } catch { /* compute it */ }
  }
  const work = meaningFor(env, k).then(async (hits) => {
    if (cache && hits) {
      await cache.put(keyOf(k), new Response(JSON.stringify(hits), {
        headers: { "content-type": "application/json", "cache-control": `public, max-age=${KEEP_S}` } }));
    }
    return hits;
  }).catch(() => null);
  try { if (ctx && ctx.waitUntil) ctx.waitUntil(work); } catch { /* no context in tests */ }
  let timer;
  const late = new Promise((r) => { timer = setTimeout(() => r(LATE), BUDGET); });
  const got = await Promise.race([work, late]);
  clearTimeout(timer);
  return got === LATE ? { hits: null, late: true } : { hits: got, late: false };
}
const LATE = Symbol("late");
function remember(k, hits) {
  if (MEMO.size >= MEMO_MAX) MEMO.delete(MEMO.keys().next().value);
  MEMO.set(k, { at: Date.now(), hits });
}

export async function meaningFor(env, q) {
  if (!env || !env.AI || !env.FIND_VEC) return null;
  const k = String(q || "").trim().toLowerCase();
  if (k.length < 2) return null;
  const memo = MEMO.get(k);
  if (memo && Date.now() - memo.at < MEMO_MS) return memo.hits;
  const e = await env.AI.run(MODEL, { text: [k] });
  const v = e && e.data && e.data[0];
  if (!v) return null;
  const r = await env.FIND_VEC.query(v, { topK: TOP_K, returnMetadata: "all" });
  const hits = ((r && r.matches) || []).filter((m) => m.metadata && m.metadata.u).map((m) => ({
    url: m.metadata.u, site: m.metadata.s || "", title: m.metadata.t || "", abstract: m.metadata.a || "",
    score: Math.round(m.score * 1000) / 1000,
  }));
  remember(k, hits);
  return hits;
}

/* address → multiplier, for sql()'s CASE. */
export function semBoost(hits) {
  const m = new Map();
  for (const h of hits || []) {
    if (h.score < FLOOR) continue;
    const t = Math.min(1, (h.score - FLOOR) / (FULL - FLOOR));
    m.set(h.url, Math.round((1 + BOOST * t) * 1000) / 1000);
  }
  return m;
}

/* The pages to list under "by meaning": close enough, and not already shown.
 * Listed when the words found five pages or fewer, or when none of the pages
 * shown is one the meaning search found too (the words matched, the sense
 * did not: "somewhere quiet to work" found a clinic). */
export function rescueRows(hits, shown, total) {
  const have = new Set((shown || []).map((r) => r.url));
  const close = (hits || []).filter((h) => h.score >= RESCUE);
  if (total > 5 && close.some((h) => have.has(h.url))) return [];
  return close.filter((h) => !have.has(h.url)).slice(0, total > 5 ? 5 : 10);
}

export function rescueHtml(rows, esc) {
  if (!rows.length) return "";
  const li = rows.map((h) => {
    let host = "";
    try { host = new URL(h.url).host; } catch { host = ""; }
    return `<li><a href="${esc(h.url)}">${esc(h.title || h.url)}</a>` +
      (h.abstract ? `<br><span class="abs">${esc(h.abstract)}</span>` : "") +
      `<br><small>${esc(host)}</small></li>`;
  }).join("");
  return `<h2 class="sem-h">ตามความหมาย · by meaning</h2><ol class="sem">${li}</ol>`;
}
