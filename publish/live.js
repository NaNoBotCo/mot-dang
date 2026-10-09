/* /api/live — a reader's position, shared with whoever holds the link, for an
 * hour (Nan, 2026-10-01: "share my location from any screen on motdang, either
 * as a snapshot or hour-long share option").
 *
 * The snapshot needs nothing here: its link carries the point itself
 * (/live.html?p=lat,lng,acc,epoch). This is the hour.
 *
 *   POST /api/live                 → { id, tok, until }   a new share
 *   POST /api/live/<id>  {tok, lat, lng, acc}             the phone moved
 *   POST /api/live/<id>  {tok, stop: 1}                   the sharer ended it
 *   GET  /api/live/<id>            → { lat, lng, acc, at, until, now }
 *                                    or { ended: true }   for the viewer
 *
 * `tok` is the sharer's write key; the row holds its SHA-256. The link carries
 * only the id. A row whose hour is over is deleted on the next request that
 * touches the table, and a GET for it answers ended.
 *
 * D1, its own database (LIVE → motdang-live): a reload of the search index or
 * the mailing list never touches it. Without the binding every path here
 * answers 503 and the rest of the site serves as before. */

const HOUR = 3600 * 1000;
const MIN_GAP = 4000;          /* a phone that reports faster is read every 4 s */
const ID_RE = /^[a-z2-7]{16}$/;

const HEAD = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-robots-tag": "noindex",
  "access-control-allow-origin": "*",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: HEAD });
}

function rand32(n) {
  const a = "abcdefghijklmnopqrstuvwxyz234567";
  const b = crypto.getRandomValues(new Uint8Array(n));
  let s = "";
  for (const x of b) s += a[x & 31];
  return s;
}

async function sha(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

export const LIVE_SCHEMA = `CREATE TABLE IF NOT EXISTS live (
  id TEXT PRIMARY KEY, tok TEXT NOT NULL, made INTEGER NOT NULL, until INTEGER NOT NULL,
  lat REAL, lng REAL, acc REAL, at INTEGER)`;

export function ownsLive(path) {
  return path === "/api/live" || path.startsWith("/api/live/");
}

export function num(v, lo, hi) {
  const n = Number(v);
  return Number.isFinite(n) && n >= lo && n <= hi ? n : null;
}

export async function live(request, env, url, now = Date.now()) {
  const db = env.LIVE;
  if (!db) return json({ error: "not ready" }, 503);
  const id = url.pathname.slice("/api/live/".length);

  if (url.pathname === "/api/live" || url.pathname === "/api/live/") {
    if (request.method !== "POST") return json({ error: "POST to start a share" }, 405);
    await db.prepare("DELETE FROM live WHERE until < ?").bind(now - 60000).run();
    const nid = rand32(16), tok = rand32(32), until = now + HOUR;
    await db.prepare("INSERT INTO live (id, tok, made, until) VALUES (?, ?, ?, ?)")
      .bind(nid, await sha(tok), now, until).run();
    return json({ id: nid, tok, until });
  }

  if (!ID_RE.test(id)) return json({ error: "no such share" }, 404);
  const row = await db.prepare("SELECT * FROM live WHERE id = ?").bind(id).first();

  if (request.method === "GET" || request.method === "HEAD") {
    if (!row || row.until <= now) {
      if (row) await db.prepare("DELETE FROM live WHERE id = ?").bind(id).run();
      return json({ ended: true, now });
    }
    return json({ lat: row.lat, lng: row.lng, acc: row.acc, at: row.at, until: row.until, now });
  }

  if (request.method !== "POST") return json({ error: "GET or POST" }, 405);
  let b;
  try { b = await request.json(); } catch { return json({ error: "JSON body" }, 400); }
  if (!row || row.until <= now) return json({ ended: true }, 410);
  if (!b || typeof b.tok !== "string" || (await sha(b.tok)) !== row.tok)
    return json({ error: "not your share" }, 403);
  if (b.stop) {
    await db.prepare("DELETE FROM live WHERE id = ?").bind(id).run();
    return json({ ended: true });
  }
  const lat = num(b.lat, -90, 90), lng = num(b.lng, -180, 180);
  if (lat == null || lng == null) return json({ error: "lat and lng" }, 400);
  const acc = num(b.acc, 0, 100000);
  if (row.at && now - row.at < MIN_GAP) return json({ ok: true, until: row.until, held: true });
  await db.prepare("UPDATE live SET lat = ?, lng = ?, acc = ?, at = ? WHERE id = ?")
    .bind(lat, lng, acc == null ? null : Math.round(acc), now, id).run();
  return json({ ok: true, until: row.until });
}

/* /api/resolve?u=<short link> — a Google Maps short link opened out to the
 * long one, which carries the coordinates the map can read. Shares from the
 * Google Maps app arrive as maps.app.goo.gl/…, and a browser cannot follow a
 * redirect across origins to see where it lands. Only those hosts. */
const SHORT = /^https:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps|g\.co\/kgs)\//;
export async function resolve(url) {
  let u = url.searchParams.get("u") || "";
  if (u.startsWith("http://")) u = "https://" + u.slice(7);
  if (!SHORT.test(u)) return json({ error: "a maps.app.goo.gl link" }, 400);
  for (let i = 0; i < 5; i++) {
    let r;
    try { r = await fetch(u, { redirect: "manual", headers: { "user-agent": "Mozilla/5.0 (motdang.net link opener)" } }); }
    catch { return json({ url: u }); }
    const to = r.headers.get("location");
    if (!(r.status >= 300 && r.status < 400) || !to) break;
    u = new URL(to, u).toString();
    if (!SHORT.test(u)) break;
  }
  return json({ url: u });
}
