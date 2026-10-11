/* The calendar inside the search (Nan, 2026-10-01: Beer typed "events" and
 * "today" into the box and got shops named Today).
 *
 * The front page's calendar (front_layer.py → front/events.json in R2) is read
 * here and matched against the words: a when-word (today, tonight, tomorrow,
 * weekend, a weekday, in Thai or English) sets the window, an events-word
 * (events, งาน, ปฏิทิน…) asks for the calendar, and what is left has to land in
 * an event's title, venue, kind or area. The answer stands above the page hits
 * and every row leads back to the calendar (/#ev=…) and to the map. */

import { cachedGet } from "./r2cache.js";

const TTL = 10 * 60 * 1000;
let EV = null, EV_AT = 0;
export async function eventData(env) {
  if (EV && Date.now() - EV_AT < TTL) return EV;
  try {
    const o = await cachedGet(env, "front/events.json");
    if (o) { EV = await o.json(); EV_AT = Date.now(); }
  } catch { /* the old copy, or none: the page hits still answer */ }
  return EV;
}

const fold = (s) => String(s || "").toLowerCase().normalize("NFKC")
  .replace(/[’']/g, "").replace(/[^\p{L}\p{M}\p{N}]+/gu, " ").trim();
const isThai = (s) => /[฀-๿]/.test(s);

/* when-words → a window. Longest first, so "this weekend" goes before "weekend". */
const DAYS_EN = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
const DAYS_TH = ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"];
const WHEN = [
  ["this weekend", "weekend"], ["weekend", "weekend"], ["เสาร์อาทิตย์", "weekend"], ["สุดสัปดาห์", "weekend"],
  ["this week", "week"], ["สัปดาห์นี้", "week"], ["อาทิตย์นี้", "week"],
  ["tonight", "tonight"], ["คืนนี้", "tonight"], ["เย็นนี้", "tonight"],
  ["today", "today"], ["วันนี้", "today"],
  ["tomorrow", "tomorrow"], ["พรุ่งนี้", "tomorrow"],
  ...DAYS_EN.map((d, i) => [d, "d" + i]),
  ["วันพฤหัส", "d4"], ...DAYS_TH.map((d, i) => ["วัน" + d, "d" + i]),
].sort((a, b) => b[0].length - a[0].length);

/* events-words: the reader is asking for the calendar itself. */
const ASK = ["whats on", "what s on", "things to do", "happening", "calendar", "events", "event",
  "ปฏิทิน", "กิจกรรม", "อีเวนต์", "อีเว้นท์", "อีเว้นต์", "อีเวนท์", "งาน"].sort((a, b) => b.length - a.length);
const STOP = new Set(["the", "a", "an", "of", "and", "in", "on", "at", "for", "to", "is", "are", "what", "whats",
  "any", "near", "me", "this", "next", "there", "chiang", "mai", "cm", "ที่", "มี", "อะไร", "บ้าง", "ไหม", "ใน"]);

/* Lift the when- and events-words out of the query. A Latin word counts whole;
 * a Thai one counts anywhere in an unspaced run — except งาน, which sits inside
 * ทำงาน and สำนักงาน, so it counts only at the start of a run (งานดนตรี, งานวัด). */
export function readQuery(q) {
  let s = " " + fold(q) + " ", when = "", asked = false;
  for (const [w, k] of WHEN) {
    const hit = isThai(w) ? s.includes(w) : s.includes(" " + w + " ");
    if (hit) { if (!when) when = k; s = isThai(w) ? s.replace(w, " ") : s.replace(" " + w + " ", "  "); }
  }
  for (const w of ASK) {
    if (isThai(w)) {
      if (!s.includes(w)) continue;
      const rest = s.replace(w, " ");
      if (w === "งาน" && !/(^|\s)งาน/.test(s)) continue;    // ทำงาน, สำนักงาน
      s = rest; asked = true;
    } else if (s.includes(" " + w + " ")) { s = s.replace(" " + w + " ", " "); asked = true; }
  }
  const toks = s.split(/\s+/).filter((t) => t && !STOP.has(t) && (isThai(t) || t.length > 1));
  return { when, asked, toks };
}

const at = (s) => Date.parse(String(s).replace(" ", "T") + (String(s).length > 10 ? "" : "T00:00:00") + "+07:00");
const DAY = 86400000;
function span(e) {
  const s = at(e.s);
  let en;
  if (e.e) en = String(e.e).length > 10 ? at(e.e) : at(e.e) + DAY - 1;
  else en = e.ad || String(e.s).slice(11, 16) === "00:00" ? s + DAY - 1 : s + 2 * 3600e3;   // no time given: the day
  return [s, Math.max(en, s)];
}

const long = (e) => { const [s, en] = span(e); return en - s > 30 * 3600e3; };
const noTime = (e) => e.ad || String(e.s).slice(11, 16) === "00:00";
/* Order: day by day, timed rows before the all-day ones, the long runs (all October) last. */

/* The window a when-word names, in Bangkok time, as [from, to] in ms. */
export function windowFor(when, now) {
  const b = new Date(now + 7 * 3600e3), dow = b.getUTCDay();
  const mid = now - ((b.getUTCHours() * 60 + b.getUTCMinutes()) * 60 + b.getUTCSeconds()) * 1000 - b.getUTCMilliseconds();
  if (when === "today") return [now, mid + DAY];
  if (when === "tonight") return [Math.max(now, mid + 17 * 3600e3), mid + DAY + 4 * 3600e3];
  if (when === "tomorrow") return [mid + DAY, mid + 2 * DAY];
  if (when === "week") return [now, mid + 7 * DAY];
  if (when === "weekend") {
    const toSat = (6 - dow + 7) % 7;
    const from = dow === 0 ? now : Math.max(now, mid + toSat * DAY);
    return [from, mid + (dow === 0 ? 1 : toSat + 2) * DAY];
  }
  if (/^d\d$/.test(when)) {
    const k = (Number(when[1]) - dow + 7) % 7;
    return [k ? mid + k * DAY : now, mid + (k + 1) * DAY];
  }
  return [now, mid + 15 * DAY];
}

function hay(e, cats) {
  const c = cats[e.c] || {};
  return " " + fold([e.t, e.v, c.th, c.en, e.ath, e.aen].filter(Boolean).join(" ")) + " ";
}

/* The answer, or null when the calendar has nothing to say to these words. */
export function calMatch(q, data, now) {
  if (!data || !data.events) return null;
  const r = readQuery(q);
  if (!r.when && !r.asked && !r.toks.length) return null;
  /* Plain words with no when- or events-word have to be worth a row above the
   * page hits: three letters or more, or Thai. */
  if (!r.when && !r.asked && !r.toks.some((t) => isThai(t) || t.length >= 3)) return null;
  const cats = {};
  for (const c of data.cats || []) cats[c.k] = c;
  const [from, to] = windowFor(r.when, now);
  const inWin = data.events.filter((e) => { const [s, en] = span(e); return en > from && s < to; });
  const want = (e, kinds) => {
    const h = kinds ? hay(e, cats) : " " + fold(e.t + " " + e.v) + " ";
    return r.toks.every((t) => isThai(t) ? h.includes(t) : h.includes(" " + t));
  };
  /* Kind and area count only when the reader asked for the calendar or named a
   * day; "music" alone stays a search for music shops, with any event titled
   * for it shown above. */
  const loose = r.when || r.asked;
  let list = r.toks.length ? inWin.filter((e) => want(e, loose)) : inWin;
  if (!list.length && !r.asked) return null;
  const day = (e) => ymd(Math.max(at(e.s), now));
  list = list.slice().sort((a, b) => (long(a) - long(b)) || day(a).localeCompare(day(b))
    || (noTime(a) - noTime(b)) || (at(a.s) - at(b.s)));
  return { when: r.when, asked: r.asked, toks: r.toks, from, to, total: list.length, all: inWin.length,
           events: list.slice(0, loose ? 14 : 4), more: Math.max(0, list.length - (loose ? 14 : 4)), cats };
}

/* ------------------------------------------------------------ the block */
const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const MON_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
const MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAY_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const ymd = (t) => new Date(t + 7 * 3600e3).toISOString().slice(0, 10);
function dayLabel(t, now) {
  const b = new Date(t + 7 * 3600e3), d = ymd(t), k = Math.round((at(d) - at(ymd(now))) / DAY);
  const th = (k === 0 ? "วันนี้ " : k === 1 ? "พรุ่งนี้ " : "") + "วัน" + DAYS_TH[b.getUTCDay()] + " " + b.getUTCDate() + " " + MON_TH[b.getUTCMonth()];
  const en = (k === 0 ? "Today, " : k === 1 ? "Tomorrow, " : "") + DAY_EN[b.getUTCDay()] + " " + b.getUTCDate() + " " + MON_EN[b.getUTCMonth()];
  return [th, en, d];
}
const WIN_LABEL = {
  today: ["วันนี้", "today"], tonight: ["คืนนี้", "tonight"], tomorrow: ["พรุ่งนี้", "tomorrow"],
  weekend: ["เสาร์อาทิตย์นี้", "this weekend"], week: ["7 วันนี้", "the next 7 days"], "": ["15 วันข้างหน้า", "the next 15 days"],
};

/* where a row's map link goes: the venue's own pin when we know the place,
 * the events layer either way */
function mapHref(e) {
  if (e.la == null) return "";
  const m = /^(c[mr])\/p\/([a-z0-9-]+)\.html$/.exec(e.vu || "");
  return `/map.html#16/${e.la}/${e.lo}//ev=1${m ? `&pin=${m[1]}:${m[2]}` : ""}`;
}

export function calHtml(m, now) {
  if (!m) return "";
  const win = /^d\d$/.test(m.when) ? dayLabel(m.from, now).slice(0, 2) : WIN_LABEL[m.when] || WIN_LABEL[""];
  const words = m.toks.length ? ` “${esc(m.toks.join(" "))}”` : "";
  let h = `<section class="calf" aria-label="ปฏิทิน · Calendar"><h2><a href="/#soon">ปฏิทิน · Calendar</a></h2>`;
  h += `<p class="cn">${m.total ? `${m.total} งาน${words} ${win[0]} · ${m.total} event${m.total === 1 ? "" : "s"}${words} ${win[1]}`
    : `ไม่มีงาน${words} ${win[0]} · no events${words} ${win[1]}${m.all ? ` — <a href="/find?q=${encodeURIComponent(m.when || "events")}">ทั้งหมด ${m.all} งาน · all ${m.all}</a>` : ""}`}</p>`;
  let last = "", ran = false;
  const rows = [];
  for (const e of m.events) {
    const s = at(e.s), run = long(e);
    const d = ymd(Math.max(s, now));
    if (run && !ran) { rows.push(`<li class="dh">ตลอดช่วงนี้ · running now</li>`); ran = true; last = ""; }
    else if (!run && d !== last && (m.when !== "today" && m.when !== "tonight")) {
      const L = dayLabel(Math.max(s, now), now); rows.push(`<li class="dh">${L[0]} · ${L[1]}</li>`);
    }
    if (!run) last = d;
    const tm = run || noTime(e) ? "ทั้งวัน" : new Date(s + 7 * 3600e3).toISOString().slice(11, 16);
    const c = m.cats[e.c];
    const venue = e.v ? (e.vu ? `<a href="/${esc(e.vu)}">${esc(e.v)}</a>` : esc(e.v)) : "";
    const map = mapHref(e);
    rows.push(`<li><b class="tm">${tm}</b><span><a class="et" href="/#ev=${esc(e.k)}">${esc(e.t)}</a>`
      + `<span class="m">${venue ? " · " + venue : ""}${c ? ` · ${esc(c.th)} ${esc(c.en)}` : ""}`
      + (map ? ` · <a href="${map}">แผนที่ · map</a>` : "") + `</span></span></li>`);
  }
  if (rows.length) h += `<ol class="evl">${rows.join("")}</ol>`;
  const day = m.when === "today" || m.when === "tonight" ? ymd(now) : m.when ? ymd(m.from) : "";
  const links = [`<a href="/#${day ? "day=" + day : "soon"}">${m.more ? `อีก ${m.more} งานในปฏิทิน · ${m.more} more on the calendar` : "ดูในปฏิทิน · open the calendar"} →</a>`,
    `<a href="/map.html#12.4/18.78760/98.99310//ev=1">งานบนแผนที่ · events on the map</a>`];
  if (m.when === "today" || m.when === "tonight") links.push(`<a href="/#now">ร้านที่เปิดอยู่ตอนนี้ · open right now</a>`);
  h += `<p class="cm">${links.join(" · ")}</p></section>`;
  return h;
}

export const CAL_CSS = `
.calf{margin:.9em 0 1em;padding:.6em .9em .5em;border:2px solid #b8912e;border-radius:.6em;background:#fffaf0;max-width:44em}
.calf h2{margin:0;font-size:1.1em}.calf h2 a{color:#8a5a00;text-decoration:none}
.calf .cn{margin:.15em 0 .4em;color:var(--mute)}
.calf ol.evl{list-style:none;padding:0;margin:0}
.calf li{display:flex;gap:.7em;margin:0 0 .45em;align-items:baseline}
.calf li.dh{display:block;margin:.6em 0 .2em;font-weight:bold;border-bottom:1px solid var(--rule)}
.calf .tm{flex:none;width:3.6em;font-family:ui-monospace,Menlo,monospace;color:#8a5a00}
.calf .et{font-size:1.05em}.calf .m{color:var(--mute);font-size:.92em}.calf .m a{color:var(--mute)}
.calf .cm{margin:.5em 0 .1em;font-size:.95em}
`;
