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
 */

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

function headers(obj, key, extra) {
  const h = new Headers(extra);
  h.set("content-type", TYPES[ext(key)] || "application/octet-stream");
  h.set("cache-control", cacheFor(ext(key)));
  /* Range support is not decoration here: pmtiles is nothing but ranged reads,
   * and a client that cannot tell we accept them will refuse to try. */
  h.set("accept-ranges", "bytes");
  h.set("x-content-type-options", "nosniff");
  h.set("referrer-policy", "strict-origin-when-cross-origin");
  if (obj.httpEtag) h.set("etag", obj.httpEtag);
  return h;
}

export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", {
        status: 405,
        headers: { allow: "GET, HEAD" },
      });
    }

    const url = new URL(request.url);

    /* Renamed shelves. The learn/ slug said classes while the shelf held
     * gyms (WO-37, 2026-08-26); the pages moved to sport/ and every old URL
     * keeps working — a rename must never eat a bookmark or a search
     * result. 301 so crawlers move their index to the new address. */
    const renamed = url.pathname.match(/^\/(cm|cr)\/learn(\/.*|$)/);
    if (renamed) {
      const to = `/${renamed[1]}/sport${renamed[2] || "/"}`;
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
        },
      });
    }
    return new Response("Not found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
};
