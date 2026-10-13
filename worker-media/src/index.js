// motdang.net/{streetphotos,photos,inat,og}/… from the bucket mot-dang-media.
// Headers follow publish/worker.js (type from the extension, etag from R2, ranges, conditionals, CORS)
// with a longer life for the picture. A miss, a path outside the four prefixes and every method other than
// GET and HEAD go to the site Worker unchanged, so the bucket can lag the site without a 404.
// motdang.net/media-check/<key> answers from the same keys; it is the route the Worker is tried on first.

const PREFIXES = {
  "streetphotos/": "public, max-age=31536000, immutable",   // a Mapillary or phone frame never changes under its name
  "inat/": "public, max-age=31536000, immutable",           // named by observation id
  "photos/": "public, max-age=2592000",                     // a pick can be replaced under its name
  "og/": "public, max-age=2592000",                         // cards are redrawn under their names
};
const TYPES = {
  jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp",
};
const CHECK = "/media-check";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "content-type, if-none-match, range",
  "access-control-expose-headers": "etag, content-length, content-range, content-type, last-modified",
  "access-control-max-age": "86400",
};

const ext = (k) => {
  const i = k.lastIndexOf(".");
  return i < 0 ? "" : k.slice(i + 1).toLowerCase();
};

function headers(obj, key, cache) {
  const h = new Headers();
  h.set("content-type", TYPES[ext(key)]);
  h.set("cache-control", cache);
  h.set("accept-ranges", "bytes");
  h.set("x-content-type-options", "nosniff");
  h.set("referrer-policy", "strict-origin-when-cross-origin");
  h.set("x-robots-tag", "notranslate");
  h.set("x-served-by", "mot-dang-media");
  for (const [k, v] of Object.entries(CORS)) h.set(k, v);
  if (obj.httpEtag) h.set("etag", obj.httpEtag);
  return h;
}

// The request as the site Worker would have had it: the test route's prefix is taken off.
function onward(request, url, path) {
  if (path === url.pathname) return request;
  const u = new URL(url);
  u.pathname = path;
  return new Request(u, request);
}

export function keyOf(pathname) {
  let key;
  try { key = decodeURIComponent(pathname).replace(/^\/+/, ""); } catch { return null; }
  if (key.includes("..") || key.endsWith("/") || !TYPES[ext(key)]) return null;
  const prefix = Object.keys(PREFIXES).find((p) => key.startsWith(p) && key.length > p.length);
  return prefix ? { key, cache: PREFIXES[prefix] } : null;
}

export async function serve(request, env) {
  const url = new URL(request.url);
  const path = url.pathname.startsWith(CHECK + "/") ? url.pathname.slice(CHECK.length) : url.pathname;
  const miss = () => env.SITE_WORKER.fetch(onward(request, url, path));

  if (request.method !== "GET" && request.method !== "HEAD") return miss();
  const hit = keyOf(path);
  if (!hit) return miss();

  const range = request.headers.get("range");
  const opts = { onlyIf: request.headers };
  if (range) opts.range = request.headers;
  let obj;
  try { obj = await env.MEDIA.get(hit.key, opts); } catch { return miss(); }
  if (obj === null) return miss();

  // No body: the conditional matched, the reader's copy is current.
  if (obj.body == null) return new Response(null, { status: 304, headers: headers(obj, hit.key, hit.cache) });

  const h = headers(obj, hit.key, hit.cache);
  let status = 200;
  if (obj.range && range) {
    const { offset = 0, length = obj.size } = obj.range;
    h.set("content-range", `bytes ${offset}-${offset + length - 1}/${obj.size}`);
    status = 206;
  }
  if (request.method === "HEAD") {
    if (obj.body) obj.body.cancel();
    h.set("content-length", String(obj.size));
    return new Response(null, { status, headers: h });
  }
  return new Response(obj.body, { status, headers: h });
}

export default {
  fetch(request, env) {
    return serve(request, env);
  },
};
