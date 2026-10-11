/* findpreview.js — what a search row shows of the place or list behind it,
 * beyond its words (Nan, 2026-10-04, over "Big bike rental": "Not enough
 * transliteration on search-responsive sub-page summaries. Not enough preview
 * anywhere."). Rendering only; the facts are baked by fleetsearch/crawl.py
 * and load.py into each row's `rich`:
 *
 *   rd    [script, text]  the name read in the script it lacks
 *   bear  [th, en]        where it stands, from the place page's bearings
 *   pr    price range, as the record states it
 *   sc    the scene the place page draws of itself when it has no photograph
 *   pv    a list's best few places: [name, url, thumb, reading, scene, lat?, lon?]
 *
 * The peek card and the drawn thumbnails are docs/front/findpeek.js
 * (assets/front/findpeek.js), which /locshare.js fetches when the page has rows
 * (preview_layer.LOADER): the page is whole without it. */

const THUMBS = "/tiles/find/";
const CELL_Z = 16;
const WEEK_MIN = 10080;
const DAYS = [["จ.", "Mon"], ["อ.", "Tue"], ["พ.", "Wed"], ["พฤ.", "Thu"], ["ศ.", "Fri"], ["ส.", "Sat"], ["อา.", "Sun"]];

const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function parse(s) {
  if (!s) return {};
  if (typeof s === "object") return s;
  try { return JSON.parse(s) || {}; } catch { return {}; }
}

function cellPos(lat, lon, hx, hy) {
  const n = 2 ** CELL_Z;
  const X = ((lon + 180) / 360) * n;
  const Y = ((1 - Math.asinh(Math.tan((lat * Math.PI) / 180)) / Math.PI) / 2) * n;
  return [((X - hx) / 2) * 100, ((Y - hy) / 2) * 100];
}

/* Two halves of one fact; the page's language shows one, a crawler both. */
const pair = (th, en) => `<span class="ol-th" lang="th">${esc(th)}</span><span class="ol-sep"> · </span>` +
                         `<span class="ol-en" lang="en">${esc(en)}</span>`;

/* The name in the script the reader lacks: a Latin reading under a Thai-only
 * name (shown in English), a Thai reading under a Latin-only one (in Thai). */
export function readingHtml(row) {
  const rd = parse(row.rich).rd;
  if (!Array.isArray(rd) || !rd[1]) return "";
  if (String(row.title || "").toLowerCase().includes(String(rd[1]).toLowerCase())) return "";   // the title already carries it
  return rd[0] === "th"
    ? `<span class="rd rd-th" lang="th">อ่านว่า ${esc(rd[1])}</span>`
    : `<span class="rd rd-en" lang="en">reads ${esc(rd[1])}</span>`;
}

const hhmm = (m) => `${String(Math.floor((m % 1440) / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

/* Open now and until when, or when it opens next — from the week's minute
 * intervals (Monday 00:00 = 0). Null when the week holds no hours. */
export function hoursState(iv, minute) {
  if (!Array.isArray(iv) || !iv.length) return null;
  for (const [a, b] of iv) {
    for (const m of [minute, minute + WEEK_MIN]) {
      if (m >= a && m < b) {
        if (b - a >= WEEK_MIN) return { open: true, allday: true };
        return { open: true, until: b % WEEK_MIN, soon: b - m <= 60 };
      }
    }
  }
  let best = null;
  for (const [a] of iv) {
    const ahead = ((a - minute) % WEEK_MIN + WEEK_MIN) % WEEK_MIN;
    if (best === null || ahead < best[0]) best = [ahead, a % WEEK_MIN];
  }
  return best ? { open: false, at: best[1], ahead: best[0] } : null;
}

export function hoursHtml(st, minute) {
  if (!st) return "";
  if (st.open && st.allday) return `<span class="lamp on">${pair("เปิด 24 ชม.", "open 24 h")}</span>`;
  if (st.open) {
    return `<span class="lamp on${st.soon ? " soon" : ""}">${pair(`เปิดอยู่ ถึง ${hhmm(st.until)}`, `open · closes ${hhmm(st.until)}`)}</span>`;
  }
  const today = Math.floor(minute / 1440), day = Math.floor(st.at / 1440);
  const when = day === today && st.ahead < 1440 ? ["", ""]
    : day === (today + 1) % 7 ? ["พรุ่งนี้ ", "tomorrow "] : [`${DAYS[day][0]} `, `${DAYS[day][1]} `];
  return `<span class="lamp off">${pair(`เปิด${when[0] ? " " + when[0].trim() : ""} ${hhmm(st.at)}`, `opens ${when[1]}${hhmm(st.at)}`)}</span>`;
}

/* One useful line: where it stands (or how far from the reader), whether it is
 * open, the price range when the record has one. */
export function sayLine(row, iv, minute, far) {
  const rich = parse(row.rich);
  const bits = [];
  const st = hoursState(iv, minute);
  if (st) bits.push(hoursHtml(st, minute));
  if (far) bits.push(`<span class="far">📍 ${pair(far[0], far[1])}</span>`);
  else if (Array.isArray(rich.bear) && rich.bear[0]) bits.push(`<span class="bear">${pair(rich.bear[0], rich.bear[1])}</span>`);
  if (rich.pr) bits.push(`<span class="pr">฿ ${esc(rich.pr)}</span>`);
  return bits.length ? `<div class="say">${bits.join("")}</div>` : "";
}

function stripPic(it) {
  const [, , th, , sc, lat, lon] = it;
  const draw = sc ? ` data-sc="${esc(sc)}"` : "";
  if (th && th.startsWith("p/")) return `<span class="pvp"><img src="${THUMBS}${esc(th)}.webp" alt="" loading="lazy" decoding="async"></span>`;
  const m = /^g\/(\d+)_(\d+)$/.exec(th || "");
  if (m && lat != null && lon != null) {
    const [x, y] = cellPos(Number(lat), Number(lon), Number(m[1]), Number(m[2]));
    return `<span class="pvp map"${draw}><img src="${THUMBS}${esc(th)}.webp" alt="" loading="lazy" decoding="async">` +
           `<i style="left:${x.toFixed(1)}%;top:${y.toFixed(1)}%"></i></span>`;
  }
  return `<span class="pvp"${draw}></span>`;
}

/* A list's best few places as pictures you can open, instead of a count. */
export function stripHtml(row) {
  const pv = parse(row.rich).pv;
  if (!Array.isArray(pv) || !pv.length) return "";
  const items = pv.map((it) => `<a class="pvi" href="${esc(it[1])}">${stripPic(it)}` +
    `<span class="pvn">${esc(it[0])}${it[3] ? `<small class="${/[฀-๿]/.test(it[3]) ? "rd-th" : "rd-en"}">${esc(it[3])}</small>` : ""}</span></a>`).join("");
  return `<div class="pv" role="list" aria-label="ตัวอย่าง · a few of them">${items}</div>`;
}

/* What the peek script reads off a row besides its link and picture: its
 * kind, its scene, its reading. */
export function rowData(row) {
  const rich = parse(row.rich);
  const bits = [`data-k="${esc(row.kind || "page")}"`];
  if (rich.sc) bits.push(`data-sc="${esc(rich.sc)}"`);
  if (Array.isArray(rich.rd) && rich.rd[1]) bits.push(`data-rd="${esc(rich.rd[1])}"`);
  if (row.thumb && row.thumb.startsWith("p/")) bits.push(`data-ph="1"`);
  return bits.join(" ");
}

export const PEEK_BTN = `<button type="button" class="pk" aria-label="ดูก่อน · peek" title="ดูก่อน · peek"></button>`;


/* Only what the server-drawn parts need; the peek card, the drawings and the
 * eye's glyph are styled by findpeek.js. Sent with the results list, not with
 * an empty search page. */
export const PREVIEW_CSS = `html.lang-en .ol-th,html.lang-en .ol-sep,html.lang-th .ol-en,html.lang-th .ol-sep,html.lang-en .rd-th,html.lang-th .rd-en{display:none}
.rd{display:block;color:#7a4b12;font-size:.9em;font-style:italic}
.say{display:flex;flex-wrap:wrap;gap:.2em .9em;font-size:.9em;margin:.15em 0;color:var(--mute)}.say .pr{color:#0b6b3a}
.lamp::before{content:"";display:inline-block;width:.6em;height:.6em;margin-right:.35em;border-radius:50%;background:#b9ad95}
.lamp.on{color:#0b6b3a}.lamp.on::before{background:#19a64a;box-shadow:0 0 .5em #19a64a}.lamp.soon::before{background:#e0a020}
.th{border-radius:.5em}
.pv{display:flex;gap:.5em;overflow-x:auto;margin:.4em 0 .3em;padding-bottom:.4em}
.pvi{flex:0 0 7.4em;text-decoration:none;color:var(--ink);font-size:.8em;line-height:1.25}
.pvp{position:relative;display:block;aspect-ratio:4/3;border-radius:.5em;overflow:hidden;background:#f2ebdc;border:1px solid var(--rule)}
.pvp img{display:block;width:100%;height:100%;object-fit:cover}.pvp i{position:absolute;width:9px;height:9px;margin:-5px 0 0 -5px;border-radius:50%;background:var(--red);border:2px solid #fff}
.pvn small{display:block;color:#7a4b12;font-style:italic}
.pk{float:right;width:2.2em;height:1.7em;margin:0 0 .2em .5em;padding:0;border-radius:1em;background:#fff;border:1px solid var(--rule)}`;
