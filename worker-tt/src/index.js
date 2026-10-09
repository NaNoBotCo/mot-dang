// /tt/flow/{z}/{x}/{y}.png — TomTom's relative flow tile (green clear → red jammed), cached five minutes at the edge.
// Only tiles over northern Thailand are answered, so the key's daily allowance goes to motdang's own maps.
const BOX = { w: 96.5, e: 101.8, s: 16.8, n: 21.2 };
const HEAD = { 'access-control-allow-origin': '*', 'cache-control': 'public, max-age=300' };

function tileBox(z, x, y) {
  const n = 2 ** z, lon = (v) => v / n * 360 - 180;
  const lat = (v) => Math.atan(Math.sinh(Math.PI * (1 - 2 * v / n))) * 180 / Math.PI;
  return { w: lon(x), e: lon(x + 1), n: lat(y), s: lat(y + 1) };
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const m = url.pathname.match(/^\/tt\/flow\/(\d{1,2})\/(\d{1,6})\/(\d{1,6})\.png$/);
    if (!m) return new Response('not found', { status: 404, headers: HEAD });
    const [z, x, y] = m.slice(1).map(Number);
    const b = tileBox(z, x, y);
    if (z < 8 || z > 18 || b.e < BOX.w || b.w > BOX.e || b.n < BOX.s || b.s > BOX.n)
      return new Response(null, { status: 204, headers: HEAD });
    const key = new Request(url.origin + url.pathname);
    const cache = caches.default;
    const hit = await cache.match(key);
    if (hit) return hit;
    const up = await fetch(`https://api.tomtom.com/traffic/map/4/tile/flow/relative0/${z}/${x}/${y}.png?tileSize=256&key=${env.TOMTOM_KEY}`);
    if (!up.ok) return new Response(null, { status: 204, headers: HEAD });
    const res = new Response(up.body, { headers: { ...HEAD, 'content-type': 'image/png' } });
    ctx.waitUntil(cache.put(key, res.clone()));
    return res;
  },
};
