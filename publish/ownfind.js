/* People's own pages in /find (Nan, 2026-10-13: "Motdang should search minisites").
 *
 * Two doors, one source. fleetsearch/crawl.py reads the page maker's public feed
 * (https://sites.motdang.net/feed.json) into the index on every reload, so a
 * page is found like any other. A page made since the last reload is not in
 * the index yet, so the first page of an answer also asks the page maker
 * itself:
 *
 *   GET https://sites.motdang.net/api/find?q=<words>&lat=<lat>&lng=<lng>
 *   -> { "results": [ { name, url, kind, tier, title, tagline, about, cc, lat, lng, hours, cover, ..., score } ] }
 *
 * That call is made beside the index query, waits at most BUDGET_MS, and any
 * failure (no answer, a bad status, a body that is not what it says) is an
 * empty list: /find is the search it was. A page already in the index is not
 * shown twice; the index's copy carries the "own page" mark by its site id.
 *
 * The answer is data. Only an https address on the page maker's host is
 * taken, and every field is escaped where it is drawn. */

export const OWN_SITE = "sites";
export const OWN_HOST = "sites.motdang.net";
export const OWN_FIND = "https://sites.motdang.net/api/find";
export const BUDGET_MS = 400;
export const MAX_OWN = 10;
const KEEP = 3;                    // live-only pages joined to an answer at most

const KIND = {
  shop: ["ร้านค้า", "Shop"], food: ["ร้านอาหาร", "Food"], service: ["บริการ", "Service"],
  stay: ["ที่พัก", "Stay"], homes: ["บ้านและที่ดิน", "Homes"],
  me: ["หน้าส่วนตัว", "Personal page"], event: ["งาน", "Event"], group: ["กลุ่ม", "Group"],
};
const PLACEISH = new Set(["shop", "food", "service", "stay", "homes"]);

const str = (v, cap) => (typeof v === "string" ? v.trim().slice(0, cap) : "");
const num = (v) => (typeof v === "number" && Number.isFinite(v) ? v : null);
const onHost = (u) => typeof u === "string" && u.startsWith(`https://${OWN_HOST}/`);

/* Is it worth asking? Page one of a best-match or nearest answer to plain
 * words, with nothing narrowing it to some other site, kind or date. */
export function ownWanted(o) {
  return !!(o.q && o.q.length >= 2 && !o.adv && !o.boolQ && !o.lucky && o.page === 1 &&
            (o.sort === "rank" || o.sort === "near") && !o.site && !o.kind && !o.sec &&
            !(o.has && o.has.length) && !o.from && !o.to);
}

export function ownUrl(base, q, pin) {
  let u = `${base}?q=${encodeURIComponent(q)}`;
  /* the position is rounded to about a kilometre on the way out */
  if (pin && Number.isFinite(pin.lat) && Number.isFinite(pin.lon)) {
    u += `&lat=${pin.lat.toFixed(2)}&lng=${pin.lon.toFixed(2)}`;
  }
  return u;
}

/* The pages the page maker named, trimmed to what is drawn. [] on any fault. */
export async function ownPagesSoon(env, q, pin, opts) {
  const base = env && typeof env.OWN_FIND_URL === "string" ? env.OWN_FIND_URL : OWN_FIND;
  if (!base) return [];
  const fetchFn = (opts && opts.fetch) || globalThis.fetch;
  if (typeof fetchFn !== "function") return [];
  const budget = (opts && opts.budget) || BUDGET_MS;
  const ctl = typeof AbortController === "function" ? new AbortController() : null;
  let timer;
  try {
    const asked = (async () => {
      const res = await fetchFn(ownUrl(base, q, pin), {
        headers: { accept: "application/json" }, signal: ctl ? ctl.signal : undefined });
      if (!res || !res.ok) return [];
      const doc = await res.json();
      return Array.isArray(doc && doc.results) ? doc.results : [];
    })();
    const late = new Promise((resolve) => { timer = setTimeout(() => { if (ctl) ctl.abort(); resolve([]); }, budget); });
    const got = await Promise.race([asked.catch(() => []), late]);
    return got.filter((p) => p && typeof p === "object" && onHost(p.url) && str(p.title, 300))
              .slice(0, MAX_OWN);
  } catch { return []; } finally { clearTimeout(timer); }
}

const hhmm = (s) => {
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(s || "").trim());
  return m ? Number(m[1]) * 60 + Number(m[2]) : null;
};

/* The page's week as minute-of-week intervals, Monday 00:00 = 0, which is the
 * clock the index's lamps run on (Chiang Mai). A page on another clock gets no
 * lamp rather than the wrong one. */
export function schedOf(h) {
  if (!h || !h.on) return null;
  if (!["Asia/Bangkok", "Asia/Ho_Chi_Minh", "Asia/Jakarta", undefined, null, ""].includes(h.tz)) return null;
  if (h.always) return [[0, 7 * 1440]];
  const out = [];
  (Array.isArray(h.week) ? h.week : []).slice(0, 7).forEach((day, i) => {
    for (const s of Array.isArray(day) ? day : []) {
      if (!Array.isArray(s) || s.length !== 2) continue;
      const a = hhmm(s[0]); let b = hhmm(s[1]);
      if (a == null || b == null) continue;
      if (b <= a) b += 1440;
      out.push([i * 1440 + a, i * 1440 + b]);
    }
  });
  return out.length ? out : null;
}

/* One answer of the page maker as the shape a D1 row has, so the one row
 * renderer draws it. `ctx.HAS` is the index's bit table; `own` marks the row. */
export function ownRow(p, ctx) {
  const kind = KIND[p.kind] ? p.kind : "shop";
  const title = str(p.title, 300);
  const ways = [["phone", p.phone], ["line", p.line], ["facebook", p.facebook], ["instagram", p.instagram], ["web", p.web]]
    .filter(([, v]) => str(v, 300)).map(([w]) => w);
  const iv = schedOf(p.hours);
  const ev = p.event && /^\d{4}-\d{2}-\d{2}/.test(str(p.event.start, 20))
    ? [{ d: p.event.start.slice(0, 10), t: title.slice(0, 80) }] : [];
  const lat = num(p.lat), lon = num(p.lng);
  const cover = str(p.cover, 400);
  const abs = str(p.tagline, 240) || str(p.about, 240);
  const has = (ways.length ? ctx.HAS.contact : 0) | (iv ? ctx.HAS.hours : 0) | (ev.length ? ctx.HAS.events : 0) |
              (cover.startsWith("https://") ? ctx.HAS.photo : 0);
  return {
    id: `own:${str(p.name, 80)}`, site: OWN_SITE, host: OWN_HOST, url: p.url, title, abstract: abs,
    lastmod: (str(p.updated, 20) || str(p.published, 20) || ctx.today).slice(0, 10), kb: 4,
    kind: PLACEISH.has(kind) ? "place" : "page",
    crumbs: JSON.stringify([[KIND[kind][0], null, KIND[kind][1]]]),
    thumb: "", thumbUrl: cover.startsWith("https://") && onHost(cover) ? cover : "",
    rich: JSON.stringify({ ...(ways.length ? { ways } : {}), ...(ev.length ? { ev } : {}) }),
    has, sk: null, lat, lon, own: true, iv, score: Number(p.score) || 0,
  };
}

/* Join live pages to an answer: not the ones the index already holds (its
 * copy carries the mark), the closest KEEP of them, after the first two rows
 * so the index's best matches keep their places. Returns the new rows list,
 * the pages added, and a scheds wrapper that knows their lamps. */
export function mergeOwn(rows, own, ctx, aux) {
  const have = new Set(rows.map((r) => r.url));
  /* a gold page before a free one, then by score */
  const gold = (p) => (p && p.tier === "gold" ? 1 : 0);
  const fresh = own.filter((p) => !have.has(p.url))
                   .sort((a, b) => gold(b) - gold(a) || (Number(b.score) || 0) - (Number(a.score) || 0))
                   .slice(0, KEEP).map((p) => ownRow(p, ctx));
  if (!fresh.length) return { rows, added: 0, aux };
  const extra = new Map();
  fresh.forEach((r, i) => { if (r.iv) { r.sk = -1 - i; extra.set(r.sk, r.iv); } });
  const at = Math.min(2, rows.length);
  const merged = rows.slice(0, at).concat(fresh, rows.slice(at));
  const scheds = { get: (k) => (Number(k) < 0 ? extra.get(Number(k)) : aux.scheds.get(k)) };
  return { rows: merged, added: fresh.length, aux: { ...aux, scheds } };
}

export default { ownWanted, ownUrl, ownPagesSoon, schedOf, ownRow, mergeOwn, OWN_SITE, OWN_HOST, BUDGET_MS };
