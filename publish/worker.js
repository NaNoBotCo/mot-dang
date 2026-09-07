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
 * holds a public directory, there are no cookies, no sessions and no
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

import { SCHEMA_VERSION, queryPlaces, findPlace, slugCandidates, minuteOfWeek } from "./api.js";

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
    }
  } catch (e) {
    /* keep what we have; try again next window */
  }
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

async function api(env, url, path) {
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

  let ix;
  try {
    ix = await loadIndex(env);
  } catch (e) {
    return apiError(503, "index unavailable", String(e.message));
  }

  if (path === "/places") return apiJson(queryPlaces(ix, url.searchParams));

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

export default {
  async fetch(request, env) {
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

    /* /api/v1/… is the machine; /api and /api/ fall through to the static
     * handler and land on the human page, api/index.html, with no redirect —
     * same rule as the rest of the site. The version lives in the path because
     * that is the promise: v1's keys never change under a reader, and the day
     * one must, it is v2 at a different address with v1 still running. */
    if (url.pathname.startsWith("/api/v1"))
      return api(env, url, url.pathname.slice(7));

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
      return new Response(obj.body, { status, headers: h });
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
  },
};
