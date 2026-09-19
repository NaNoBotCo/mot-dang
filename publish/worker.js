/* mot-dang site Worker — serves the whole site out of an R2 bucket.
 *
 * WHY THIS EXISTS
 * ---------------
 * The site was published by Cloudflare Pages pulling from GitHub. When the
 * GitHub account was suspended that pipeline stopped, and because Pages keeps
 * serving its last good build, nothing looked broken — the site simply stopped
 * accepting new work. Months of pushes shipped nothing.
 *
 * There is a second, slower wall behind that one: Pages caps a project at
 * 20,000 files and docs/ is 27,577 (13,514 pages plus a .json sibling for each
 * place). So even with GitHub healthy, a full deploy no longer fits.
 *
 * R2 has no object limit and no dependency on anyone else's git host, so both
 * walls go away at once — and the 116 MB basemap archive lives in the same
 * bucket as the pages, served by the same code path.
 *
 * URL SHAPE, deliberately different from Pages
 * -------------------------------------------
 * Pages redirects /toilets.html to /toilets. Every internal link on this site
 * is written as "toilets.html" and every canonical says .html, so that default
 * put a 308 in front of ordinary navigation and left the canonical disagreeing
 * with the URL actually served. Here .html is served straight, and the
 * extensionless form resolves to the same object for anyone who types or has
 * bookmarked it. No redirects on the common path.
 *
 * CORS, AND WHY IT IS ON EVERYTHING
 * ---------------------------------
 * The licence has said "reuse it, train on it, quote it" on every page since
 * the site existed, and the data was reachable by anything that could make a
 * server-side request — and by nothing that ran in a browser, because no
 * response carried an Access-Control-Allow-Origin. An open licence a browser
 * cannot act on is an invitation with the door locked. Every response is now
 * origin-open. That is not a relaxation of a security boundary: the bucket
 * holds a public directory, it sets no cookie, keeps no session and holds no
 * credentials anywhere in this Worker, so there is nothing a cross-origin
 * reader can reach that it could not already have fetched from a server.
 *
 * THE API
 * -------
 * /api/v1/* is a query layer over one baked file (api/v1/index.json, written
 * by api_layer.py at build time), held in the isolate after the first request.
 * No database, no binding beyond the bucket that was already here. The
 * query semantics live in api.js so they can be tested without deploying.
 */

import { SCHEMA_VERSION, queryPlaces, findPlace, slugCandidates, minuteOfWeek,
         present, liftProvince, norm, parseQuery, rowMatches,
         LIMIT_DEFAULT, LIMIT_MAX } from "./api.js";
import SEARCHCORE from "./searchcore.js";
import { EdgeIndex } from "./edgesearch.js";
import { classify } from "./classify.js";

const TYPES = {
  html: "text/html; charset=utf-8",
  json: "application/json; charset=utf-8",
  geojson: "application/geo+json",
  js: "text/javascript; charset=utf-8",
  css: "text/css; charset=utf-8",
  svg: "image/svg+xml",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  webp: "image/webp",
  ico: "image/x-icon",
  woff2: "font/woff2",
  txt: "text/plain; charset=utf-8",
  xml: "application/xml; charset=utf-8",
  ics: "text/calendar; charset=utf-8",
  pdf: "application/pdf",
  apk: "application/vnd.android.package-archive",
  pmtiles: "application/octet-stream",
  /* Label glyphs for the basemap, self-hosted since 2026-08-20 so that a page
   * carrying a map asks nobody but us for anything. They would already serve
   * as octet-stream by the fallback below; named here so the type is stated
   * rather than defaulted. */
  pbf: "application/x-protobuf",
};

/* Pages are rebuilt often and must never be served stale from a CDN edge after
 * a deploy; fingerprint-free assets (fonts, images, the tile archive) never
 * change under the same name, so they get a long life. The tile archive in
 * particular is fetched in hundreds of small ranges — re-validating each one
 * would undo the point of self-hosting it. */
function cacheFor(ext) {
  if (ext === "html" || ext === "json" || ext === "geojson" || ext === "xml")
    return "public, max-age=0, must-revalidate";
  if (ext === "pmtiles") return "public, max-age=31536000, immutable";
  /* MEASURED AND REJECTED, 2026-09-10, so nobody builds it twice: serving
   * data/index.json and vendor/ from caches.default, keyed by etag, with a
   * gzip twin baked beside each. It was deployed and measured against the
   * live site and it was SLOWER — 5.7-8.2 s where the plain path had been
   * 1.8-3.5 s, and most requests missed the cache anyway. Three reasons, all
   * of them things Cloudflare was already doing better: the edge was already
   * caching these and compressing them with BROTLI (smaller than the gzip
   * twin); finding the etag cost an extra R2 head() before every read; and
   * filling the cache cost a second full read of the same 9.4 MB object.
   * Taking a body away from the CDN to hand-cache it is a losing trade.
   *
   * Stylesheet, scripts and the icon sprite carry no ?v= fingerprint any
   * more (Nan, 2026-09-10): a fingerprint written into 96,000 pages made
   * every CSS edit a full re-upload. Instead the browser shows the copy it
   * holds and asks in the background whether it changed; a returning reader
   * is at most one page view behind after an edit, never a week. */
  if (ext === "css" || ext === "js" || ext === "svg")
    return "public, max-age=0, stale-while-revalidate=604800";
  return "public, max-age=604800";
}


const ext = (k) => {
  const i = k.lastIndexOf(".");
  return i < 0 ? "" : k.slice(i + 1).toLowerCase();
};

/* Every key this path could reasonably mean, most-likely first. Kept small on
 * purpose: each miss is a real R2 lookup. */
function candidates(pathname) {
  let p = decodeURIComponent(pathname).replace(/^\/+/, "");
  if (p === "" || p.endsWith("/")) return [p + "index.html"];
  if (p.includes(".")) return [p];
  return [p + ".html", p + "/index.html"];
}

/* Open to every origin, on every response.
 *
 * expose-headers matters more than it looks: without it a cross-origin reader
 * can see the body but not the ETag, so it cannot make a conditional request
 * and must re-download the 25 MB places.json every time. Exposing them is what
 * makes polite caching possible for the readers we most want to be polite. */
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "content-type, if-none-match, range",
  "access-control-expose-headers":
    "etag, content-length, content-range, content-type, last-modified",
  "access-control-max-age": "86400",
};

function headers(obj, key, extra) {
  const h = new Headers(extra);
  h.set("content-type", TYPES[ext(key)] || "application/octet-stream");
  h.set("cache-control", cacheFor(ext(key)));
  /* Range support is not decoration here: pmtiles is nothing but ranged reads,
   * and a client that cannot tell we accept them will refuse to try. */
  h.set("accept-ranges", "bytes");
  h.set("x-content-type-options", "nosniff");
  h.set("referrer-policy", "strict-origin-when-cross-origin");
  for (const [k, v] of Object.entries(CORS)) h.set(k, v);
  if (obj.httpEtag) h.set("etag", obj.httpEtag);
  return h;
}

/* The front page carries one meta, md-where, which home_layer.py writes empty.
 * The edge fills it with what Cloudflare already knows about the request —
 * city, coordinates, timezone, country — so the page can stand in Chiang Mai
 * or Chiang Rai before anyone taps anything. It is the carrier's idea of
 * where the request came from, not a fix on the reader; the page treats it
 * as a guess, and a tap on the pill or the locate button replaces it. */
function withWhere(res, request) {
  const cf = request.cf || {};
  const v = [cf.city || "", cf.latitude || "", cf.longitude || "", cf.timezone || "", cf.country || ""].join("|");
  return new HTMLRewriter()
    .on('meta[name="md-where"]', { element(e) { e.setAttribute("content", v); } })
    .transform(res);
}

/* ------------------------------------------------------------------ API */

/* The baked index, parsed once per isolate. A cold isolate pays one R2 GET and
 * one parse; every request after that is memory. INDEX_P (not INDEX) is what
 * is cached so that N concurrent cold requests share ONE fetch instead of
 * racing to do the same work N times. A failed load is not cached — it clears
 * the promise so the next request retries rather than inheriting an outage.
 *
 * WHY THERE IS A REVALIDATION CLOCK HERE
 * -------------------------------------
 * Cached "once per isolate" meant once per isolate FOREVER, and an isolate
 * lives as long as Cloudflare cares to keep it. README.md promises that "the
 * API ships with a content deploy, not a Worker deploy" — and it did not.
 * Measured 2026-09-07: a full content deploy put a fresh index.json in the
 * bucket (generated 09-07, 25,914 places) and /api/v1/places went on answering
 * from the 09-05 copy, 25,856 places, through three cache-busted requests. The
 * only thing that cleared it was redeploying the Worker, which is exactly the
 * step the README says a content deploy does not need.
 *
 * So the index is now revalidated against the bucket at most once every
 * REVALIDATE_MS. The check is a HEAD — metadata only, no body, no parse — and
 * it compares etags. Same etag, nothing happens and the request is still
 * answered from memory. Different etag, the parsed copy is dropped and the
 * next load picks up the new one.
 *
 * The cost is one R2 HEAD per minute per isolate, not one per request. The
 * bound on staleness is REVALIDATE_MS, not the isolate's lifetime.
 *
 * A FAILED HEAD IS NOT AN OUTAGE. If the metadata call throws, we keep serving
 * the index we already hold and try again next window. The alternative — treat
 * a blipped HEAD as "reload everything" — would turn a metadata hiccup into a
 * cold parse on every isolate at once, which is a worse failure than answering
 * from a copy that is at most a minute old. */
const REVALIDATE_MS = 60_000;
let INDEX_P = null;
let INDEX_ETAG = null;
let INDEX_CHECKED = 0;

async function revalidateIndex(env) {
  const now = Date.now();
  if (!INDEX_P || now - INDEX_CHECKED < REVALIDATE_MS) return;
  INDEX_CHECKED = now;              // set BEFORE the await: a slow HEAD must
                                    // not let every concurrent request start
                                    // one of its own.
  try {
    const head = await env.SITE.head("api/v1/index.json");
    if (head && INDEX_ETAG && head.httpEtag !== INDEX_ETAG) {
      INDEX_P = null;
      INDEX_ETAG = null;
      EDGE_P = null;      // the shards were rebuilt with the index; walk the new ones
      CORE_P = null;
    }
  } catch (e) {
    /* keep what we have; try again next window */
  }
}

/* THE ENGINE AT THE EDGE (Nan, 2026-09-10: "Worker can run search engine,
 * that's fine"). searchcore — the same file the page runs — over the postings
 * publish/emit_edge_index.js wrote as shards under api/v1/edge/. The isolate
 * holds the vocabulary and the API index it already had; a posting list is
 * fetched from the bucket only when a query needs it. See edgesearch.js. */
let EDGE_P = null;
let CORE_P = null;

function edgeLoader(env) {
  return async (rel) => { const o = await env.SITE.get(rel); return o ? o.json() : null; };
}

function edgeCore(env) {
  if (!CORE_P) {
    CORE_P = (async () => {
      const [th, sg] = await Promise.all([env.SITE.get("data/search_thesaurus.json"),
                                          env.SITE.get("data/search_segdict.txt")]);
      const groups = th ? (await th.json()).groups : [];
      const seg = sg ? (await sg.text()).split("\n").filter((l) => l && l[0] !== "#") : [];
      return new SEARCHCORE.SearchCore(groups, seg);
    })().catch((e) => { CORE_P = null; throw e; });
  }
  return CORE_P;
}

function edgeIndex(env) {
  if (!EDGE_P) {
    EDGE_P = (async () => {
      const ix = new EdgeIndex(await edgeCore(env), edgeLoader(env));
      await ix.init();
      return ix;
    })().catch((e) => { EDGE_P = null; throw e; });
  }
  return EDGE_P;
}

/* /api/v1/search?q=…&limit=&offset=&province= — the words, ranked as the page
 * ranks them: tier, weight, coverage, loosen-by-steps. A city in q narrows to
 * its province (api.js liftProvince). What the page adds AFTER ranking — the
 * landmark, the tag routes, the shelf lift, the rail — stays on the page; the
 * page asks this first and repaints over it when its own index has landed. */
export async function searchHandler(env, ix, sp, now = new Date()) {
  const raw = sp.get("q") || "";
  const p = parseQuery(sp);
  const q = p.q;
  const province = p.province;
  const limit = p.limit;
  const offset = p.offset;
  /* WO-87. The endpoint answered words and one province and nothing else, so
   * the results page could only ask it for a bare query — every chip the
   * reader had tapped sent them back to waiting on 6.2 MB of index. It takes
   * the page's own filters now (tag, sub, cat, near, and the rest parseQuery
   * already read), applied through the same predicate /api/v1/places uses.
   *
   * Two shapes, not one:
   *   words + filters — searchcore answers the words, the predicate narrows
   *                     its hits, and the ranking that came out of the tiers
   *                     is kept.
   *   filters, no words — there is nothing for searchcore to rank, so the
   *                     index itself is walked, in the order /api/v1/places
   *                     would walk it: nearest when a point was given, best
   *                     known otherwise. This is the case the page could
   *                     never ask about at all.
   */
  const filtered = !!(p.cat.length || p.sub.length || p.tag.length || p.lens.length
                      || p.facet.length || p.has.length || p.minAnts || p.near
                      || p.bbox || p.openNow || p.openAt != null);
  const echo = {};
  for (const k of ["q", "province", "cat", "sub", "tag", "lens", "facet", "has",
                   "min_ants", "near", "radius", "bbox", "open_now", "open_at"]) {
    if (sp.has(k)) echo[k] = sp.get(k);
  }
  const envelope = { schemaVersion: SCHEMA_VERSION, generated: ix.generated, engine: "searchcore",
                     query: { ...echo, q: raw, ...(province ? { province } : {}), limit, offset } };
  const empty = { ...envelope, total: 0, count: 0, tier: null, results: [],
                  attribution: ix.attribution, licence: ix.licence, terms: ix.terms };
  if (!q.trim() && !filtered) return empty;
  const schedules = ix.schedules || [];
  const minute = p.openAt != null ? p.openAt : (p.openNow ? minuteOfWeek(now) : null);
  const nowMinute = minuteOfWeek(now);

  let rows;      // [row, distance|null, score|null, tier|null]
  let notes = null;
  if (q.trim()) {
    const edge = await edgeIndex(env);
    const an = edge.core.analyze(q, edge);
    notes = an.notes;
    const hits = await edge.search(an, 0);
    rows = [];
    for (const h of hits) {
      const row = findPlace(ix, h.id);
      if (!row) continue;
      const d = rowMatches(row, p, schedules, minute);
      if (d === false) continue;
      rows.push([row, d, h.score, h.tier]);
    }
  } else {
    rows = [];
    for (const row of ix.places) {
      const d = rowMatches(row, p, schedules, minute);
      if (d === false) continue;
      rows.push([row, d, null, null]);
    }
    const cmpName = (a, b) => String(a[0].name).localeCompare(String(b[0].name), "th");
    if (p.near) rows.sort((a, b) => a[1] - b[1] || cmpName(a, b));
    else rows.sort((a, b) => b[0].antRank - a[0].antRank || cmpName(a, b));
  }

  const page = rows.slice(offset, offset + limit);
  const results = page.map(([row, d, score, tier]) => {
    const out = present(row, ix.base, { near: p.near }, schedules, nowMinute);
    if (score != null) { out.score = Math.round(score * 1000) / 1000; out.tier = tier; }
    if (d != null) out.distanceM = Math.round(d);
    return out;
  });
  return { ...envelope, total: rows.length, count: results.length,
           tier: rows.length && rows[0][3] != null ? rows[0][3] : null,
           notes, results, attribution: ix.attribution, licence: ix.licence, terms: ix.terms };
}

/* The 🎲 destinations. Re-read every ten minutes so an isolate that has been
 * warm across a deploy cannot keep sending readers to a page that was removed;
 * a stale face costs one 404, not an error, which is why this is a timestamp
 * rather than the etag dance loadIndex does for the 74 MB index. */
const DICE_TTL_MS = 600_000;
let DICE_P = null;
let DICE_AT = 0;

function dice(env) {
  const now = Date.now();
  if (!DICE_P || now - DICE_AT > DICE_TTL_MS) {
    DICE_AT = now;
    DICE_P = (async () => {
      const obj = await env.SITE.get("data/dice.json");
      if (!obj) throw new Error("dice not deployed");
      return JSON.parse(await obj.text());
    })().catch((e) => { DICE_P = null; throw e; });
  }
  return DICE_P;
}

function loadIndex(env) {
  if (!INDEX_P) {
    INDEX_P = (async () => {
      const obj = await env.SITE.get("api/v1/index.json");
      if (!obj) throw new Error("api index not deployed");
      INDEX_ETAG = obj.httpEtag;
      return JSON.parse(await obj.text());
    })().catch((e) => { INDEX_P = null; INDEX_ETAG = null; throw e; });
  }
  return INDEX_P;
}

/* Discovery the standard way (RFC 8631), so a client that lands on any
 * endpoint can find the documentation and the machine spec without anyone
 * having told it where they are — and so can a person reading -v output. The
 * licence link is here for the same reason it is in every body: the terms are
 * the first thing a reuser needs and the last thing they should have to hunt
 * for. Listed in access-control-expose-headers so a browser can read them. */
const API_LINKS = [
  '<https://motdang.net/api/>; rel="service-doc"',
  '<https://motdang.net/api/v1/openapi.json>; rel="service-desc"',
  '<https://motdang.net/api/v1/schema.json>; rel="describedby"',
  '<https://motdang.net/terms.html>; rel="license"',
].join(", ");

/* Five minutes of edge cache on every API response. The corpus changes once a
 * build, so anything shorter buys nothing; anything longer would make an
 * emergency correction take too long to reach a reader standing in a street. */
const API_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "x-content-type-options": "nosniff",
  link: API_LINKS,
  ...CORS,
  "access-control-expose-headers": CORS["access-control-expose-headers"] + ", link",
};

function apiJson(body, status = 200, extra) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...API_HEADERS,
      "cache-control": status === 200 ? "public, max-age=300" : "no-store",
      ...extra,
    },
  });
}

/* An error a person can act on: what went wrong, and where the answer is. */
const apiError = (status, error, hint) =>
  apiJson({ schemaVersion: SCHEMA_VERSION, error, hint,
            docs: "https://motdang.net/api/" }, status);

/* The short form of an error for a body: its class, then the head of its
 * message. The whole error goes to the log. */
const errCode = (e) => {
  const name = e && e.name && e.name !== "Error" ? e.name : "";
  const msg = String((e && e.message) || e || "").slice(0, 60);
  return name && msg ? `${name}: ${msg}` : name || msg || "unknown";
};

async function api(request, env, url, path, ctx) {
  /* Has the bucket been rebuilt under us? At most one HEAD a minute per
   * isolate; see REVALIDATE_MS. Placed here rather than inside loadIndex so
   * that it runs once per API request instead of once per loadIndex call —
   * a single request can make three. */
  await revalidateIndex(env);

  /* The descriptor, the spec and the schema are baked files — served straight
   * from the bucket so that what the API says about itself is written by the
   * same build that wrote the data, and cannot drift from it. */
  const baked = { "/index.json": "index", "/openapi.json": "openapi", "/schema.json": "schema" };
  if (baked[path]) {
    const obj = await env.SITE.get(`api/v1/${baked[path]}.json`);
    if (!obj) return apiError(503, "api not deployed", "the build has not been published yet");
    return new Response(obj.body, {
      headers: { ...API_HEADERS, "cache-control": "public, max-age=300" },
    });
  }

  /* The descriptor is index.json's head, not its 13,000 rows: a reader asking
   * "what is this" should not be handed several megabytes to find out. The
   * bulk file keeps its own address, named right here so it is one hop away. */
  if (path === "" || path === "/") {
    let ix;
    try { ix = await loadIndex(env); }
    catch (e) { return apiError(503, "api not deployed", String(e.message)); }
    const { places, schedules, ...head } = ix;
    return apiJson({ ...head,
      bulk: { url: ix.base + "api/v1/index.json", places: ix.count,
              note: "the whole query index in one file — take it and stop asking us" } });
  }

  if (path === "/health") {
    try {
      const ix = await loadIndex(env);
      return apiJson({ schemaVersion: SCHEMA_VERSION, ok: true,
                       generated: ix.generated, places: ix.places.length,
                       minuteOfWeekBangkok: minuteOfWeek() });
    } catch (e) {
      return apiJson({ schemaVersion: SCHEMA_VERSION, ok: false, error: String(e.message) }, 503);
    }
  }

  /* THE ANSWER IS KEPT AT THE COLO (2026-09-10). Measured that night from
   * Chiang Mai: /api/v1/health — no scan, no sort, only loadIndex — answered
   * in 3.4 s, 9.0 s and 4.1 s; nine requests landed on five colos, and two
   * in a row to SIN were both slow. api/v1/index.json is 69 MB now (88,221
   * rows) and parses to 228 MB of heap in node against a 128 MB isolate, so
   * no isolate keeps it and every request streams it from R2 again: that is
   * the seconds. The scan is 30-450 ms and the parse 300. A Worker's own
   * response is not CDN-cached, so the max-age=300 above bought nothing at
   * the edge; here the answer is put in caches.default under its own URL
   * with that same header, so the same question asked again in the same
   * colo within five minutes never touches the index. A miss costs one
   * local lookup and fetches nothing to find it. GET only.
   *
   * /search JOINS IT (WO-87, 2026-09-18). It was left out when this was
   * written, and measured from here the day the filters landed it was paying
   * the whole bill every time: 1.7 s for a filter with no words and 3.8-7.8 s
   * for one with words, on repeat, while /places answered the same question
   * in 93 ms off this cache. Nothing about the answer is per-reader — the
   * query string IS the question — and a chip is the same URL for everybody
   * who taps it, which is the shape a colo cache is for. near= carries a
   * coordinate and will mostly miss; that is the price of asking where you
   * are standing, and it is the same price it was paying before. */
  let cache = null, ckey = null;
  if ((path === "/places" || path === "/search") && request.method === "GET") {
    try {
      cache = caches.default;
      ckey = new Request(url.href);
      const hit = await cache.match(ckey);
      if (hit) {
        const r = new Response(hit.body, hit);
        r.headers.set("x-md-edge", "hit");
        return r;
      }
    } catch {
      cache = null;                    /* no cache here: computed, as before */
    }
  }

  let ix;
  try {
    ix = await loadIndex(env);
  } catch (e) {
    return apiError(503, "index unavailable", String(e.message));
  }

  if (path === "/places") {
    const res = apiJson(queryPlaces(ix, url.searchParams));
    if (cache && ckey) {
      try { ctx.waitUntil(cache.put(ckey, res.clone()).catch(() => {})); }
      catch { /* unfilled: the next asker computes it */ }
      res.headers.set("x-md-edge", "miss");
    }
    return res;
  }

  if (path === "/search") {
    try {
      const res = apiJson(await searchHandler(env, ix, url.searchParams));
      if (cache && ckey) {
        try { ctx.waitUntil(cache.put(ckey, res.clone()).catch(() => {})); }
        catch { /* unfilled: the next asker computes it */ }
        res.headers.set("x-md-edge", "miss");
      }
      return res;
    }
    catch (e) {
      /* edgesearch.js says "edge index missing" when api/v1/edge/ is not in
       * the bucket: the build that writes it has not been published, which
       * is not a fault. Anything else is a deployed engine breaking on a
       * query — said as such, and logged with the query. */
      if (/edge index missing/.test(String(e && e.message)))
        return apiError(503, "search engine not deployed",
          "the build that writes api/v1/edge/ has not been published yet — /api/v1/places?q= still answers");
      console.error("/api/v1/search fault", url.search, e);
      return apiJson({ schemaVersion: SCHEMA_VERSION, error: "search engine fault", code: errCode(e),
                       hint: "the engine broke on this query — /api/v1/places?q= still answers",
                       docs: "https://motdang.net/api/" }, 500);
    }
  }

  if (path.startsWith("/places/")) {
    const key = decodeURIComponent(path.slice(8));
    const row = findPlace(ix, key);
    if (!row) {
      /* A slug two records share resolves to neither. 300 rather than 404,
       * because the place is not missing — the key is. The candidates come
       * back as ids, which are unique, so the caller can ask again and be
       * certain of the answer instead of taking our guess. */
      const many = slugCandidates(ix, key);
      if (many.length)
        return apiJson({
          schemaVersion: SCHEMA_VERSION,
          error: "ambiguous key",
          hint: "this page slug is shared; ask again by id",
          candidates: many.map((r) => ({
            id: r.id, name: r.name,
            apiUrl: ix.base + "api/v1/places/" + r.id,
            url: ix.base + `${r.province}/p/${r.slug}.html`,
          })),
          docs: "https://motdang.net/api/",
        }, 300);
      return apiError(404, "no such place",
        "try /api/v1/places?q=… — ids and page slugs both work here");
    }
    /* The full record is the .json sibling the place page has always had, not
     * a second rendering of it. One shape, one generator, nothing to drift. */
    const obj = await env.SITE.get(`${row.province}/p/${row.slug}.json`);
    if (!obj) return apiError(404, "record not deployed", "known to the index, absent from the bucket");
    return new Response(obj.body, {
      headers: { ...API_HEADERS, "cache-control": "public, max-age=300" },
    });
  }

  if (path === "/categories")
    return apiJson({ schemaVersion: SCHEMA_VERSION, generated: ix.generated,
                     provinces: ix.provinces, categories: ix.categories,
                     attribution: ix.attribution, terms: ix.terms });

  if (path === "/tags")
    return apiJson({ schemaVersion: SCHEMA_VERSION, generated: ix.generated,
                     tags: ix.tags, lenses: ix.lenses, facets: ix.facets,
                     attribution: ix.attribution, terms: ix.terms });

  return apiError(404, "no such endpoint",
    "GET /api/v1/ lists every endpoint this version has");
}

async function serve(request, env, ctx) {
  const url = new URL(request.url);

  /* A preflight is answered for every path, not just /api/: a browser will
   * send one for a plain GET the moment the caller sets a header, and a 405
   * there would fail the fetch after the licence said yes. */
  if (request.method === "OPTIONS")
    return new Response(null, { status: 204, headers: CORS });

  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response("Method not allowed", {
      status: 405,
      headers: { allow: "GET, HEAD, OPTIONS", ...CORS },
    });
  }

  /* 🎲 /random — the door on 91,000 pages, rolled here instead of baked.
   *
   * It used to be one destination chosen at BUILD TIME and seeded by the
   * build date (build.py: RAND_FALLBACK). Every page carrying it was rewritten
   * when the date rolled, so the first deploy after midnight re-uploaded
   * 91,000 objects and 4.3 GiB to move a single die — the same shape as the
   * ?v= fingerprint that came out of these pages on 2026-09-10. The link is
   * now a fixed string, identical in every build, and the roll happens per
   * click, which is what a die is for.
   *
   * data/dice.json, not api/v1/index.json: the index is 74 MB and a cold
   * isolate would read all of it to answer one click. The dice file is 4,000
   * destinations in ~170 KB. A miss lands on the cm shelf rather than an
   * error — the point of the door is that it always opens on somewhere real.
   *
   * no-store because a cached 302 is a die that stopped rolling; noindex
   * because it is a door, not a page. */
  if (url.pathname === "/random" || url.pathname === "/random/") {
    let to = "/cm/index.html";
    try {
      const faces = await dice(env);
      if (faces && faces.length)
        to = "/" + faces[Math.floor(Math.random() * faces.length)];
    } catch {
      /* the shelf is a fine place to be sent */
    }
    return new Response(null, {
      status: 302,
      headers: { location: to, "cache-control": "no-store",
                 "x-robots-tag": "noindex", ...CORS },
    });
  }

  /* /api/v1/… is the machine; /api and /api/ fall through to the static
   * handler and land on the human page, api/index.html, with no redirect —
   * same rule as the rest of the site. The version lives in the path because
   * that is the promise: v1's keys never change under a reader, and the day
   * one must, it is v2 at a different address with v1 still running. */
  if (url.pathname.startsWith("/api/v1"))
    return api(request, env, url, url.pathname.slice(7), ctx);

  /* Renamed shelves. The learn/ slug said classes while the shelf held
   * gyms (WO-37, 2026-08-26); the pages moved to sport/ and every old URL
   * keeps working — a rename must never eat a bookmark or a search
   * result. 301 so crawlers move their index to the new address. */
  const renamed = url.pathname.match(/^\/(cm|cr)\/learn(\/.*|$)/);
  if (renamed) {
    const to = `/${renamed[1]}/sport${renamed[2] || "/"}`;
    return Response.redirect(url.origin + to + url.search, 301);
  }

  /* Near-misses for the Listing Sheet. /listings resolves on its own (an
   * extensionless path tries listings/index.html), but the singular and the
   * .html form did not: a path containing a dot is looked up literally and
   * nothing else is tried, so /listings.html was a 404 on a page that
   * exists. These are the forms a person types or a link drops a character
   * from, and a directory nobody can reach by guessing is a directory
   * nobody reaches. 301, so a crawler learns the real address. */
  const sheet = url.pathname.match(
    /^\/(?:listing|listings\.html|listing\.html|listing\/(.*)|add-a-listing)$/);
  if (sheet) {
    const to = sheet[1] ? `/listings/${sheet[1]}` : "/listings/";
    return Response.redirect(url.origin + to + url.search, 301);
  }

  const range = request.headers.get("range");

  for (const key of candidates(url.pathname)) {
    /* Both conditionals and ranges are handed to R2 as the raw request
     * headers, so R2 does the parsing. This is not laziness — passing the
     * If-None-Match value straight into {etagDoesNotMatch} throws, because
     * that field wants a bare etag while the header always carries quotes
     * (and may carry W/ weak tags, a comma list, or *). Range has the same
     * shape of trap with suffix and open-ended forms. Letting R2 parse both
     * removes the whole class. */
    const opts = { onlyIf: request.headers };
    if (range) opts.range = request.headers;

    const obj = await env.SITE.get(key, opts);
    if (obj === null) continue;

    /* No body means the conditional matched: unchanged since the copy the
     * reader already holds. R2 hands back a plain R2Object in that case. */
    if (obj.body == null) {
      return new Response(null, { status: 304, headers: headers(obj, key) });
    }

    const h = headers(obj, key);
    let status = 200;
    if (obj.range && range) {
      const { offset = 0, length = obj.size } = obj.range;
      const end = offset + length - 1;
      h.set("content-range", `bytes ${offset}-${end}/${obj.size}`);
      status = 206;
    }
    if (request.method === "HEAD") {
      h.set("content-length", String(obj.size));
      return new Response(null, { status, headers: h });
    }
    const res = new Response(obj.body, { status, headers: h });
    return key === "index.html" ? withWhere(res, request) : res;
  }

  /* Miss. Serve the site's own 404 page when one has been deployed, so a
   * mistyped soi still lands somewhere with the search box on it. */
  const nf = await env.SITE.get("404.html");
  if (nf) {
    return new Response(nf.body, {
      status: 404,
      headers: {
        "content-type": TYPES.html,
        "cache-control": "public, max-age=0, must-revalidate",
        ...CORS,
      },
    });
  }
  return new Response("Not found", {
    status: 404,
    headers: { "content-type": "text/plain; charset=utf-8", ...CORS },
  });
}

/* ------------------------------------------------- who asked for the page */

/* THE COUNT AT THE EDGE
 * --------------------
 * Nan's decision, 2026-09-05 (notes/arrivals-2026-09-05.txt, A1): count
 * arrivals first-party — referrer host and landing path, no cookie, no third
 * party, aggregated. Until this the site had 626,640 requests in 28 days and
 * no way to say how many were people, because Worker analytics carries no
 * User-Agent and zone analytics is a permission this account's token does not
 * hold.
 *
 * WHAT IT WRITES, AND WHAT IT DELIBERATELY DOES NOT
 * ------------------------------------------------
 * One row per request into Analytics Engine: host, category, agent name,
 * path, country, status, referrer HOST, method. No IP address. No cookie. No
 * identifier of any kind, so two requests by the same person are two rows
 * that cannot be joined — this counts arrivals, it cannot follow anybody.
 *
 * The referring URL is cut down to its host on purpose: a full referrer from
 * a search engine carries the words somebody typed, which are their business
 * and not ours. Query strings are dropped from the path for the same reason.
 *
 * IT MUST NOT BE ABLE TO BREAK THE SITE
 * -------------------------------------
 * serve() runs first and its result is returned no matter what happens next.
 * The write is handed to waitUntil inside a try/catch whose failure path is to
 * do nothing at all — a missing binding, an Analytics Engine outage, or a
 * User-Agent the classifier has never seen still ends with the reader getting
 * their page. The response body is never touched, so caching, ranges and
 * streaming behave exactly as they did before.
 *
 * ONE DATASET, NOT TWO. The rows go to `traffic_eye`, the fleet dataset
 * traffic-eye already writes and its dashboard already reads, in that Worker's
 * blob order. Keep the order below in step with traffic-eye/src/collector.js:
 * position IS the schema, and a row written out of order is a silently wrong
 * number rather than an error.
 */
function record(request, response, env, ms) {
  if (!env.TRAFFIC) return; // not bound — nothing to do, and nothing to say

  const url = new URL(request.url);
  const { category, agent } = classify(request.headers.get("user-agent") || "");

  let refHost = "";
  const ref = request.headers.get("referer");
  if (ref) {
    try {
      const r = new URL(ref);
      refHost = r.host === url.host ? "(same site)" : r.host;
    } catch {
      refHost = "(unparseable)";
    }
  }

  env.TRAFFIC.writeDataPoint({
    blobs: [
      url.host,                       // 1 site
      category,                       // 2 human|ai|search|social|seo|monitor|tool|other|none
      agent,                          // 3 ClaudeBot, Chrome, …
      trimPath(url.pathname),         // 4 path, no query string
      request.cf?.country || "XX",    // 5 country
      String(response.status),        // 6 status
      refHost,                        // 7 referrer host only
      request.method,                 // 8 method
    ],
    /* double1 is a literal 1 so SUM(double1) survives sampling; COUNT(*) would
     * quietly under-report if this site ever gets busy enough to be sampled. */
    doubles: [1, response.status, ms],
    indexes: [url.host],              // sampling key, per-site
  });
}

/* Paths here are high-cardinality by design — 93,577 of them — which Analytics
 * Engine handles. The cap is only so an absurd URL cannot write an unbounded
 * string. */
function trimPath(pathname) {
  return pathname.length > 96 ? pathname.slice(0, 96) + "…" : pathname;
}

export default {
  async fetch(request, env, ctx) {
    const started = Date.now();

    /* The one thing that matters. Nothing below this line can fail it. */
    const response = await serve(request, env, ctx);

    try {
      ctx.waitUntil(Promise.resolve(record(request, response, env, Date.now() - started)));
    } catch {
      /* Counting is never worth an error page. */
    }
    return response;
  },
};
