/* motdang.net front page — the sky and the air (2026-10-10, Nan: the weather, air and rain sections "prettier,
   much more fully featured, work much better").
   front.js hands over /data/weather.json, /data/air.json, where the reader is and their nearest rain spot;
   this draws three panels into #hours, #days3 and #airp:
     the hours  — now (temperature, feels-like, humidity, wind, UV, sun), then 24 / 48 / 72 hours of temperature
                  and rain on one chart; drag or tap it to read any hour, arrow keys too
     the week   — seven days, a temperature range bar on one scale, rain chance and millimetres; a day opens
                  to its sun, UV, wind and hours
     the air    — PM2.5 on the Thai PCD bands with PCD's advice for the band, the past week by the day and the
                  next days by the hour, the northern towns side by side
   The rain chart reads ECMWF IFS where weather.json carries it, the model weather-north checked against two
   years of airport reports; rain_cal is that record, and a tapped hour says how often it rained when IFS gave
   that chance. A reader with a known place reads their own rain spot (~11 km grid) for the first 24 hours. */
(function () {
'use strict';
var H = document.documentElement, $ = function (id) { return document.getElementById(id); };
var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
function en() { return H.classList.contains('lang-en'); }
function L(th, e) { return en() ? e : th; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
function bi(th, e, cls) { return '<span class="bi' + (cls ? ' ' + cls : '') + '"><span class="th" lang="th">' + th + '</span><span class="en" lang="en">' + e + '</span></span>'; }
var bkk = window.MDWHEN.bkk, MON_TH = window.MDWHEN.MON_TH, MON_EN = window.MDWHEN.MON_EN;
function hourKey(t) { return bkk(t).toISOString().slice(0, 13) + ':00'; }
function today() { return bkk(Date.now()).toISOString().slice(0, 10); }
function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } }
function num(x) { return typeof x === 'number' && isFinite(x); }
function r0(x) { return Math.round(x); }
function r1(x) { return Math.round(x * 10) / 10; }
var DAY_TH = ['อา.', 'จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.'], DAY_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
var DAYL_TH = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'];
function dow(d) { return new Date(d.slice(0, 10) + 'T12:00:00Z').getUTCDay(); }
function plus(d, n) { return new Date(Date.parse(d.slice(0, 10) + 'T12:00:00Z') + n * 864e5).toISOString().slice(0, 10); }
/* "today" / "tomorrow" / the weekday, for a date or an hour key */
function dayWord(t, long) {
  var d = t.slice(0, 10), td = today();
  if (d === td) return [long ? 'วันนี้' : 'วันนี้', 'today'];
  if (d === plus(td, 1)) return ['พรุ่งนี้', 'tomorrow'];
  return [(long ? 'วัน' + DAYL_TH[dow(d)] : DAY_TH[dow(d)]), DAY_EN[dow(d)]];
}
function dateStr(d) { return [+d.slice(8, 10) + ' ' + MON_TH[+d.slice(5, 7) - 1], +d.slice(8, 10) + ' ' + MON_EN[+d.slice(5, 7) - 1]]; }

/* ------------------------------------------------------------ the words for the sky */
var WMO = { 0: ['ฟ้าใส', 'Clear'], 1: ['แดดเป็นส่วนใหญ่', 'Mainly clear'], 2: ['มีเมฆบางส่วน', 'Partly cloudy'], 3: ['เมฆมาก', 'Overcast'], 45: ['หมอก', 'Fog'], 48: ['หมอกเยือกแข็ง', 'Rime fog'],
  51: ['ฝนปรอยเบา', 'Light drizzle'], 53: ['ฝนปรอย', 'Drizzle'], 55: ['ฝนปรอยหนัก', 'Heavy drizzle'], 61: ['ฝนเล็กน้อย', 'Light rain'], 63: ['ฝน', 'Rain'], 65: ['ฝนหนัก', 'Heavy rain'],
  80: ['ฝนไล่ช้าง', 'Showers'], 81: ['ฝนไล่ช้างหนัก', 'Heavy showers'], 82: ['ฝนกระหน่ำ', 'Violent showers'], 95: ['พายุฝนฟ้าคะนอง', 'Thunderstorm'], 96: ['พายุลูกเห็บ', 'Thunderstorm, hail'], 99: ['พายุลูกเห็บ', 'Thunderstorm, hail'] };
function wmo(code) {
  if (!num(code)) return ['', ''];
  if (WMO[code]) return WMO[code];
  var k = Object.keys(WMO).map(Number).filter(function (x) { return x <= code; }).pop();
  return WMO[k] || ['', ''];
}
/* WHO's UV index bands; Thai as the Department of Health words them */
function uvBand(u) {
  if (!num(u)) return null;
  return u < 3 ? ['ต่ำ', 'low', '#7cc576'] : u < 6 ? ['ปานกลาง', 'moderate', '#f2d14b'] : u < 8 ? ['สูง', 'high', '#f5a34a'] : u < 11 ? ['สูงมาก', 'very high', '#e5455a'] : ['อันตราย', 'extreme', '#b45ad6'];
}
var COMPASS_TH = ['เหนือ', 'ตะวันออกเฉียงเหนือ', 'ตะวันออก', 'ตะวันออกเฉียงใต้', 'ใต้', 'ตะวันตกเฉียงใต้', 'ตะวันตก', 'ตะวันตกเฉียงเหนือ'];
var COMPASS_EN = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
function compass(deg) { var i = ((Math.round(deg / 45) % 8) + 8) % 8; return [COMPASS_TH[i], COMPASS_EN[i]]; }
/* an arrow pointing the way the wind blows (it is named for where it comes from) */
function windArrow(deg, s) {
  s = s || 16;
  return '<svg class="wxarr" viewBox="0 0 16 16" width="' + s + '" height="' + s + '" aria-hidden="true" style="width:' + s + 'px;height:' + s + 'px;transform:rotate(' + ((deg + 180) % 360) + 'deg)"><path d="M8 1.5l4 6H9.2v7H6.8v-7H4z" fill="currentColor"/></svg>';
}
function tempCol(t) {                                 /* cool blue to hot red, by the north's own range */
  var S = [[16, [111, 180, 255]], [22, [120, 215, 200]], [27, [139, 224, 122]], [31, [255, 201, 74]], [35, [255, 122, 69]], [39, [229, 69, 90]]];
  if (t <= S[0][0]) return 'rgb(' + S[0][1] + ')';
  for (var i = 1; i < S.length; i++) if (t <= S[i][0]) {
    var a = S[i - 1], b = S[i], k = (t - a[0]) / (b[0] - a[0]);
    return 'rgb(' + [0, 1, 2].map(function (j) { return r0(a[1][j] + (b[1][j] - a[1][j]) * k); }) + ')';
  }
  return 'rgb(' + S[S.length - 1][1] + ')';
}
function rainCol(p) { return p >= 60 ? '#3d8bff' : p >= 30 ? '#7fb2ff' : '#55606f'; }

/* drawn, not emoji: sun or moon, cloud, rain, storm, fog; the groups move when tapped */
function icon(code, night, s) {
  s = s || 48;
  var sun = night ? '<path class="moon" d="M27 9a12 12 0 1 0 10 18 10 10 0 0 1-10-18z" fill="#efe6bf"/>'
    : '<circle cx="24" cy="22" r="9" fill="#ffc94a"/><g class="rays">' + [0, 45, 90, 135, 180, 225, 270, 315].map(function (a) {
      var r = a * Math.PI / 180; return '<line x1="' + r1(24 + Math.cos(r) * 13) + '" y1="' + r1(22 + Math.sin(r) * 13) + '" x2="' + r1(24 + Math.cos(r) * 17) + '" y2="' + r1(22 + Math.sin(r) * 17) + '" stroke="#ffc94a" stroke-width="2.5" stroke-linecap="round"/>'; }).join('') + '</g>';
  var cloud = '<path class="cl" d="M14 36h22a8 8 0 0 0 0-16 11 11 0 0 0-21 3 7 7 0 0 0-1 13z" fill="#dfe6ee"/>';
  var rain = '<g class="drops"><path d="M17 40l-3 6M25 40l-3 6M33 40l-3 6" stroke="#6fb4ff" stroke-width="2.5" stroke-linecap="round"/></g>';
  var bolt = '<path class="bolt" d="M26 37l-5 8h5l-3 7 8-10h-5l3-5z" fill="#ffd400"/>';
  var fog = '<g class="fog" stroke="#cfd6de" stroke-width="2.5" stroke-linecap="round"><path d="M10 40h28M14 46h22"/></g>';
  var c = num(code) ? code : 2;
  var body = c <= 1 ? sun : c === 2 ? '<g transform="translate(-6,-5) scale(.8)">' + sun + '</g>' + cloud : c === 3 ? cloud
    : c < 50 ? cloud + fog : c >= 95 ? cloud + bolt + rain : cloud + rain;
  return '<svg class="wxi" viewBox="0 0 48 52" width="' + s + '" height="' + r0(s * 52 / 48) + '" style="width:' + s + 'px;height:' + r0(s * 52 / 48) + 'px" aria-hidden="true">' + body + '</svg>';
}
function wiggle(el) {                                 /* a tap answered: the drawing does its thing once */
  if (!el || REDUCED) return;
  el.classList.remove('go'); void el.getBoundingClientRect(); el.classList.add('go');
  setTimeout(function () { el.classList.remove('go'); }, 1300);
}

/* ------------------------------------------------------------ the look */
(function () {
  var st = document.createElement('style'); st.id = 'front-wx';
  st.textContent = [
    '#fc .grid{align-items:start;grid-template-columns:minmax(0,1.7fr) minmax(19rem,1fr)}',
    '@media (max-width:820px){#fc .grid{grid-template-columns:1fr}}',
    '#fc svg.wxi,#fc svg.wxarr{display:inline-block;flex:none}',
    '#fc .wxhead{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem .6rem;justify-content:space-between;margin-bottom:.35rem}',
    '#fc .wxhead h3{margin:0}',
    '.wxsw{display:inline-flex;gap:4px;flex-wrap:wrap}',
    '.wxsw button,.wxspan button{min-height:2.3rem;padding:.15rem .7rem;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--ink);font:600 .88rem var(--sans);cursor:pointer}',
    '.wxsw button[aria-pressed=true],.wxspan button[aria-pressed=true]{background:var(--hot);border-color:var(--hot);color:#000}',
    '.wxsw button[aria-pressed=true] .en,.wxspan button[aria-pressed=true] .en{color:#000}',
    'html.lang-both .wxsw .en,html.lang-both .wxspan .en{display:none}',
    '.wxnow{display:grid;grid-template-columns:auto 1fr;gap:.2rem 1rem;align-items:center;margin:.2rem 0 .6rem}',
    '.wxbig{background:none;border:0;padding:0;cursor:pointer;line-height:0;-webkit-tap-highlight-color:transparent}',
    '.wxbig:focus-visible,.wxd:focus-visible,.wxchart:focus-visible,.wxtown:focus-visible,.wxseg:focus-visible{outline:3px dashed var(--hot);outline-offset:3px}',
    '.wxt b{display:block;font:800 2.9rem/1 var(--mono);letter-spacing:-.02em}',
    '.wxt .cond{display:block;font-size:1.05rem;font-weight:700;margin-top:.2rem}',
    '.wxt small{display:block;color:var(--mute);font-size:.92rem}',
    '.wxfacts{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:.35rem 0 0;padding:0}',
    '.wxfacts li{display:inline-flex;align-items:center;gap:.35rem;background:rgba(255,255,255,.06);border:1px solid var(--line);border-radius:10px;padding:.25rem .55rem;font-size:.9rem;line-height:1.25}',
    '.wxfacts li b{font:700 .95rem var(--mono)}',
    '.wxfacts .dot{width:.6rem;height:.6rem;border-radius:50%;display:inline-block}',
    'html.lang-both .wxfacts .bi>.en::before,html.lang-both .wxread .bi>.en::before{content:" · "}',
    '.wxarr{display:inline-block;vertical-align:-3px;color:var(--ink)}',
    '.wxsay{font-size:1.02rem;font-weight:700;margin:.3rem 0 .45rem;line-height:1.4}',
    '.wxsay .wet{color:#8fc1ff}',
    '.wxread{min-height:2.6rem;display:flex;flex-wrap:wrap;align-items:center;gap:.15rem .7rem;font-size:.93rem;background:rgba(255,255,255,.05);border-radius:10px;padding:.35rem .6rem;margin-bottom:.35rem}',
    '.wxread b{font:800 .95rem var(--mono)}',
    '.wxread .rc{color:#8fc1ff;font-weight:700}',
    '.wxread .cal{flex-basis:100%;font-size:.84rem;color:var(--mute)}',
    '.wxread svg.wxi{vertical-align:middle}',
    '.wxchart{display:block;width:100%;height:auto;touch-action:pan-y;cursor:crosshair;-webkit-tap-highlight-color:transparent;border-radius:10px}',
    '.wxspan{display:inline-flex;gap:4px;margin-top:.45rem}',
    '.wxsrc{font-size:.84rem;color:var(--mute);margin:.45rem 0 0;line-height:1.4}',
    '.wxsrc .key{display:inline-flex;align-items:center;gap:.25rem;margin-right:.6rem}',
    '.wxsrc .key i{display:inline-block;width:.9rem;height:.5rem;border-radius:2px}',
    '.wxsrc .key i.ln{height:3px;background:linear-gradient(90deg,#78d7c8,#ffc94a,#ff7a45)}',
    '.splash{transform-box:fill-box;transform-origin:center;animation:wxSplash .65s ease-out forwards}',
    '@keyframes wxSplash{from{opacity:.9;transform:scale(.3)}to{opacity:0;transform:scale(2.4)}}',
    /* the week */
    '#days{display:block}',
    '.wxd{display:grid;grid-template-columns:3.7rem 30px 3rem 2.1rem minmax(2.5rem,1fr) 2.1rem;align-items:center;gap:.4rem;width:100%;background:none;border:0;border-top:1px solid var(--line);padding:.42rem .15rem;color:var(--ink);font:600 .95rem var(--sans);text-align:left;cursor:pointer;min-height:2.9rem}',
    '.wxd:first-child{border-top:0}',
    '.wxd .dn{line-height:1.15}.wxd .dn small{display:block;font-size:.75rem;color:var(--mute);font-weight:500}',
    '.wxd .rp{font:700 .8rem var(--mono);color:#8fc1ff;line-height:1.15}.wxd .rp small{display:block;font-weight:500;color:var(--mute)}',
    '.wxd .lo,.wxd .hi{font:700 .95rem var(--mono);text-align:right}.wxd .lo{color:var(--mute)}.wxd .hi{text-align:left}',
    '.wxd .rng{position:relative;height:.45rem;border-radius:999px;background:rgba(255,255,255,.1)}',
    '.wxd .rng i{position:absolute;top:0;bottom:0;border-radius:999px}',
    '.wxd .rng s{position:absolute;top:50%;width:.7rem;height:.7rem;margin:-.35rem 0 0 -.35rem;border-radius:50%;background:#fff;border:2px solid var(--card)}',
    '.wxd[aria-expanded=true]{background:rgba(255,255,255,.05);border-radius:10px 10px 0 0}',
    '.wxdx{background:rgba(255,255,255,.05);border-radius:0 0 10px 10px;padding:.2rem .6rem .6rem;font-size:.9rem;animation:wxOpen .3s ease both}',
    '.wxdx[hidden]{display:none}',
    '.wxdx ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:.25rem .8rem}',
    '.wxdx li b{font:700 .9rem var(--mono)}',
    '.wxdx .cond{font-weight:700;margin:.15rem 0 .35rem}',
    '.wxdx svg.wxmini{display:block;width:100%;height:auto;margin-top:.45rem}',
    '@keyframes wxOpen{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}',
    /* the air */
    '#airp{margin-top:14px}',
    '.airg{display:grid;grid-template-columns:minmax(14rem,1fr) 2fr minmax(13rem,1fr);gap:1.1rem;align-items:start}',
    '@media (max-width:980px){.airg{grid-template-columns:1fr 1fr}.airg .airchart{grid-column:1/-1;order:3}}',
    '@media (max-width:620px){.airg{grid-template-columns:1fr}}',
    '.airbig{display:flex;align-items:baseline;gap:.5rem;flex-wrap:wrap}',
    '.airbig b{font:800 3rem/1 var(--mono)}',
    '.airbig small{color:var(--mute);font-size:.85rem}',
    '.airband{display:inline-block;border-radius:999px;padding:.2rem .7rem;font-weight:800;font-size:.95rem;margin:.35rem 0 .2rem}',
    '.airband .en{color:inherit!important}',
    '.airsub{font-size:.9rem;color:var(--mute);margin:.15rem 0 .5rem}',
    '.airsub b{color:var(--ink);font-family:var(--mono)}',
    '.airgauge{position:relative;display:flex;height:1.9rem;margin:.9rem 0 .25rem;gap:2px}',
    '.wxseg{flex:none;border:0;padding:0;cursor:pointer;opacity:.55;transition:opacity .15s,transform .15s}',
    '.wxseg:first-child{border-radius:6px 0 0 6px}.wxseg:last-of-type{border-radius:0 6px 6px 0}',
    '.wxseg[aria-pressed=true]{opacity:1;transform:scaleY(1.18)}',
    '.airgauge .mk{position:absolute;top:-.75rem;width:0;height:0;margin-left:-.45rem;border:.45rem solid transparent;border-top:.6rem solid #fff;transition:left .5s cubic-bezier(.2,.9,.3,1.2)}',
    '.airticks{position:relative;height:1rem;font:600 .72rem var(--mono);color:var(--mute)}',
    '.airticks span{position:absolute;transform:translateX(-50%)}',
    '.airadv{font-size:.93rem;line-height:1.45;margin:.5rem 0 0;padding:.45rem .6rem;border-radius:8px;background:rgba(255,255,255,.05);border-left:4px solid var(--hot)}',
    '.airadv b{display:block;margin-bottom:.1rem}',
    '.airvis{font-size:.92rem;margin:.5rem 0 0}',
    '.airchart h4,.airtowns h4{margin:0 0 .3rem;font-size:.98rem}',
    '.airsay{font-weight:700;margin:.1rem 0 .4rem;font-size:.98rem;line-height:1.4}',
    '.airtowns{display:flex;flex-direction:column;gap:3px}',
    '.wxtown{display:grid;grid-template-columns:6.4rem 1fr 2.6rem;align-items:center;gap:.45rem;background:none;border:0;border-radius:8px;padding:.28rem .35rem;color:var(--ink);font:600 .9rem var(--sans);text-align:left;cursor:pointer;min-height:2.4rem}',
    '.wxtown:hover{background:rgba(255,255,255,.05)}',
    '.wxtown[aria-pressed=true]{background:rgba(255,194,102,.16);box-shadow:inset 3px 0 0 var(--hot)}',
    '.wxtown .tb{height:.6rem;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}',
    '.wxtown .tb i{display:block;height:100%;border-radius:999px;transition:width .6s ease}',
    '.wxtown b{font:700 .9rem var(--mono);text-align:right}',
    '.wxtown small{display:block;font-size:.72rem;color:var(--hot);font-weight:700}',
    'html.lang-both .wxtown .bi>.en,html.lang-both .wxd .bi>.en{display:none}',
    'html[data-contrast="more"] .wxchart{background:#000}',
    '@media (max-width:420px){.wxd{grid-template-columns:3.4rem 30px 2.9rem 2rem 1fr 2rem;gap:.3rem;font-size:.9rem}.wxt b{font-size:2.4rem}}',
    /* the drawings that answer a tap */
    '.wxi.go .rays{animation:wxSpin 1.1s ease-in-out;transform-origin:24px 22px}',
    '.wxi.go .moon{animation:wxRock 1.1s ease-in-out;transform-origin:24px 22px}',
    '.wxi.go .cl{animation:wxDrift 1.1s ease-in-out}',
    '.wxi.go .drops{animation:wxFall .5s linear 2}',
    '.wxi.go .bolt{animation:wxFlash .35s steps(2) 3}',
    '.wxi.go .fog{animation:wxDrift 1.1s ease-in-out reverse}',
    '@keyframes wxSpin{to{transform:rotate(90deg)}}',
    '@keyframes wxRock{25%{transform:rotate(-14deg)}75%{transform:rotate(10deg)}}',
    '@keyframes wxDrift{50%{transform:translateX(4px)}}',
    '@keyframes wxFall{from{transform:translateY(-4px);opacity:.4}to{transform:translateY(5px);opacity:1}}',
    '@keyframes wxFlash{50%{opacity:0}}',
    '@media (prefers-reduced-motion:reduce){.wxi.go *,.splash,.wxdx,.airgauge .mk{animation:none!important;transition:none!important}}'
  ].join('');
  document.head.appendChild(st);
})();

/* ------------------------------------------------------------ state */
var S = { city: store('md-wx-city'), span: store('md-wx-span') || 24, open: null, hi: null, place: store('md-air-place'), band: null, ahi: null };
var D = { W: null, A: null, where: null, spot: null };

function cityOf() {
  var W = D.W; if (!W || !W.cities) return null;
  var id = S.city || (D.where && D.where.lat > 19.5 ? 'chiang-rai' : 'chiang-mai');
  return W.cities.filter(function (c) { return c.id === id; })[0] || W.cities[0];
}
function calOf(c) { var k = c.id === 'chiang-rai' ? 'cr' : c.id === 'chiang-mai' ? 'cm' : null; return k && D.W.rain_cal ? D.W.rain_cal[k] : null; }
/* how often it rained at the airport when IFS gave this chance, or null */
function calib(c, p) {
  var b = calOf(c); if (!b || !num(p)) return null;
  var row = null; b.forEach(function (x) { if (p >= x[0]) row = x; });
  return row ? row[1] : null;
}
/* the reader's own rain spot, only when it lies in the province on show */
function spotFor(c) { var sp = D.spot; if (!sp || !sp.hours || !sp.hours.length) return null; return (sp.lat > 19.5) === (c.id === 'chiang-rai') ? sp : null; }

/* every hour from now: rain chance and mm (spot, else IFS, else the blend), temperature, wind, UV */
function rowsOf(c) {
  var k = hourKey(Date.now()), rain = {}, blend = {}, X = {}, keys = [];
  (c.hours || []).forEach(function (h) { blend[h[0]] = [h[1], h[2], 'blend']; });
  var ifs = c.hours_ifs && c.hours_ifs.length ? c.hours_ifs : null;
  (ifs || c.hours || []).forEach(function (h) { rain[h[0]] = [h[1], h[2], ifs ? 'ifs' : 'blend']; });
  var sp = spotFor(c);
  if (sp) { Object.keys(rain).forEach(function (t) { rain[t] = blend[t] || rain[t]; }); sp.hours.forEach(function (h) { rain[h[0]] = [h[1], h[2], 'spot']; }); }
  (c.hx || []).forEach(function (h) { X[h[0]] = h; });
  keys = (c.hx && c.hx.length ? c.hx : c.hours || []).map(function (h) { return h[0]; });
  var sun = {}; (c.days || []).forEach(function (d) { sun[d.date] = [d.sunrise, d.sunset]; });
  var out = keys.filter(function (t) { return t >= k; }).map(function (t) {
    var x = X[t] || [], r = rain[t] || [], s = sun[t.slice(0, 10)];
    return { t: t, p: num(r[0]) ? r[0] : null, mm: num(r[1]) ? r[1] : null, src: r[2] || null, temp: x[1], feels: x[2], code: x[3], wind: x[4], dir: x[5], uv: x[6], hum: x[7],
      night: s && s[0] && s[1] ? (t < s[0].slice(0, 13) + ':00' || t >= s[1].slice(0, 13) + ':00') : null };
  });
  /* this hour reads the current conditions, so the chart and the big figure agree */
  var o = out[0];
  if (o) [['temp', 'temp'], ['code', 'code'], ['feels', 'feels'], ['hum', 'humidity'], ['wind', 'wind'], ['dir', 'wind_dir'], ['uv', 'uv']].forEach(function (f) { if (num(c[f[1]])) o[f[0]] = c[f[1]]; });
  if (o && (c.is_day === 0 || c.is_day === 1)) o.night = c.is_day === 0;
  return out;
}
function wet(r) { return num(r.mm) && (r.mm >= 0.3 || (r.mm >= 0.1 && r.p >= 50)); }
/* one sentence: when the rain comes, how long, how hard; or that it stays dry */
function rainSay(rs) {
  var day = rs.slice(0, 24).filter(function (r) { return num(r.p); }); if (!day.length) return null;
  function hh(r) { return r.t.slice(11, 16); }
  function when(r) { var w = dayWord(r.t); return r.t.slice(0, 10) === today() ? [hh(r), hh(r)] : [w[0] + ' ' + hh(r), w[1] + ' ' + hh(r)]; }
  var i = 0, a = -1, b = -1;
  for (; i < day.length; i++) if (wet(day[i])) { a = i; break; }
  if (a >= 0) { for (b = a; b + 1 < day.length && wet(day[b + 1]); b++); }
  var peak = day.reduce(function (m, r) { return (r.mm || 0) > (m.mm || 0) ? r : m; }, day[0]);
  if (a === 0) {
    var end = day[b + 1];
    return end ? ['ฝนตกอยู่ น่าจะซาราว ' + when(end)[0], 'Rain now, easing around ' + when(end)[1]]
      : ['ฝนตกอยู่ และน่าจะตกต่อทั้งวัน', 'Rain now, and on through the day'];
  }
  if (a > 0) {
    var s = when(day[a]), e = day[b + 1] ? when(day[b + 1]) : null, mm = r1(peak.mm);
    return ['ฝนน่าจะมา ' + s[0] + (e ? '–' + e[0].replace(/^.* /, '') : ' เป็นต้นไป') + (mm >= 0.5 ? ' หนักสุดราว ' + hh(peak) + ' (' + mm + ' มม.)' : ''),
      'Rain likely ' + (e ? 'from ' + s[1] + ' to ' + e[1].replace(/^.* /, '') : 'from ' + s[1]) + (mm >= 0.5 ? ', heaviest around ' + hh(peak) + ' (' + mm + ' mm)' : '')];
  }
  var top = day.reduce(function (m, r) { return r.p > m.p ? r : m; }, day[0]);
  if (top.p >= 30) { var w = when(top); return ['อาจมีฝนโปรยราว ' + w[0] + ' (โอกาส ' + top.p + '%)', 'A chance of a shower around ' + w[1] + ' (' + top.p + '%)']; }
  return ['ไม่น่ามีฝนใน 24 ชั่วโมงข้างหน้า', 'Dry for the next 24 hours'];
}

/* ------------------------------------------------------------ the hours panel */
function nowPanel(c, rs) {
  var r = rs[0] || {}, night = c.is_day === 0 || (c.is_day == null && r.night), fetched = Date.parse(D.W.fetched || ''), age = Date.now() - fetched;
  var td = (c.days || []).filter(function (d) { return d.date === today(); })[0], tm = (c.days || []).filter(function (d) { return d.date === plus(today(), 1); })[0];
  var w = wmo(c.code), feels = num(c.feels) ? c.feels : r.feels, wind = num(c.wind) ? c.wind : r.wind, dir = num(c.wind_dir) ? c.wind_dir : r.dir, uv = num(c.uv) ? c.uv : r.uv;
  var facts = [];
  if (num(c.humidity)) facts.push('<li>' + bi('ความชื้น', 'humidity') + ' <b>' + r0(c.humidity) + '%</b></li>');
  if (num(wind)) {
    var cp = compass(dir);
    facts.push('<li>' + (num(dir) && wind >= 1 ? windArrow(dir) : '') + bi('ลม', 'wind') + ' <b>' + r0(wind) + '</b> ' + bi('กม./ชม.' + (num(dir) && wind >= 1 ? ' จากทิศ' + cp[0] : ''), 'km/h' + (num(dir) && wind >= 1 ? ' from ' + cp[1] : '')) +
      (num(c.gust) && c.gust >= wind + 10 ? ' · ' + bi('กระโชก ' + r0(c.gust), 'gusts ' + r0(c.gust)) : '') + '</li>');
  }
  var ub = uvBand(night && td ? td.uv : uv);
  if (ub) facts.push('<li><i class="dot" style="background:' + ub[2] + '"></i>' + (night && td ? bi('UV วันนี้สูงสุด', 'UV today peaked at') : bi('UV', 'UV')) + ' <b>' + r0(night && td ? td.uv : uv) + '</b> ' + bi(ub[0], ub[1]) + '</li>');
  var sunL = null;                                     /* the next sunrise or sunset */
  [td, tm].forEach(function (d) { if (!d || sunL) return; var nk = bkk(Date.now()).toISOString().slice(0, 16);
    if (d.sunrise && d.sunrise > nk) sunL = ['พระอาทิตย์ขึ้น ' + d.sunrise.slice(11, 16), 'sunrise ' + d.sunrise.slice(11, 16)];
    else if (d.sunset && d.sunset > nk) sunL = ['พระอาทิตย์ตก ' + d.sunset.slice(11, 16), 'sunset ' + d.sunset.slice(11, 16)]; });
  if (sunL) facts.push('<li>' + bi(sunL[0], sunL[1]) + '</li>');
  if (td && num(td.max)) facts.push('<li>' + bi('วันนี้', 'today') + ' <b>' + r0(td.max) + '° / ' + r0(td.min) + '°</b></li>');
  var stale = age > 3 * 36e5 ? '<small>' + bi('ข้อมูลเมื่อ ' + (D.W.fetched ? hourKey(fetched).slice(11, 16) + ' ' + dateStr(hourKey(fetched))[0] : '–'), 'as of ' + (D.W.fetched ? hourKey(fetched).slice(11, 16) + ', ' + dateStr(hourKey(fetched))[1] : '–')) + '</small>' : '';
  return '<div class="wxnow"><button type="button" class="wxbig" aria-label="' + esc(L(w[0], w[1])) + '">' + icon(c.code, night, 76) + '</button>' +
    '<div class="wxt"><b>' + (num(c.temp) ? r0(c.temp) + '°' : '–') + '</b><span class="cond">' + bi(w[0], w[1]) + '</span>' +
    (num(feels) && Math.abs(feels - c.temp) >= 2 ? '<small>' + bi('รู้สึกเหมือน ' + r0(feels) + '°', 'feels like ' + r0(feels) + '°') + '</small>' : '') + stale + '</div>' +
    '<ul class="wxfacts">' + facts.join('') + '</ul></div>';
}

function hourLabel(r) { var w = dayWord(r.t); return [w[0] + ' ' + r.t.slice(11, 16), w[1] + ' ' + r.t.slice(11, 16)]; }
function readout(c, rs, i) {
  var r = rs[i]; if (!r) return '';
  var lab = i === 0 ? ['ตอนนี้', 'now'] : hourLabel(r), bits = ['<b>' + bi(lab[0], lab[1]) + '</b>'];
  if (num(r.code)) bits.push(icon(r.code, r.night, 22) + ' ' + bi(wmo(r.code)[0], wmo(r.code)[1]));
  if (num(r.temp)) bits.push('<b>' + r0(r.temp) + '°</b>' + (num(r.feels) && Math.abs(r.feels - r.temp) >= 2 ? ' ' + bi('รู้สึก ' + r0(r.feels) + '°', 'feels ' + r0(r.feels) + '°') : ''));
  if (num(r.p)) bits.push('<span class="rc">' + bi('ฝน ' + r.p + '%' + (r.mm >= 0.1 ? ' · ' + r1(r.mm) + ' มม.' : ''), 'rain ' + r.p + '%' + (r.mm >= 0.1 ? ' · ' + r1(r.mm) + ' mm' : '')) + '</span>');
  if (num(r.wind)) bits.push((r.wind >= 1 && num(r.dir) ? windArrow(r.dir, 14) : '') + bi('ลม ' + r0(r.wind) + ' กม./ชม.', 'wind ' + r0(r.wind) + ' km/h'));
  if (num(r.uv) && r.uv >= 1) bits.push(bi('UV ' + r0(r.uv), 'UV ' + r0(r.uv)));
  if (num(r.hum)) bits.push(bi('ชื้น ' + r0(r.hum) + '%', 'humidity ' + r0(r.hum) + '%'));
  var k = r.src === 'ifs' ? calib(c, r.p) : null;
  if (k != null && r.p >= 15) {
    var n = Math.max(0, Math.min(10, Math.round(k * 10))), st = c.id === 'chiang-rai' ? 'CEI' : 'CNX';
    bits.push('<span class="cal">' + bi('ตลอดสองปีที่ผ่านมา เมื่อแบบจำลองให้โอกาสราวนี้ ที่สนามบิน ' + st + ' ฝนตกจริง ' + (n ? n + ' ใน 10 ชั่วโมง' : 'น้อยกว่า 1 ใน 10 ชั่วโมง'),
      'over two years, when the model gave about this chance, it rained at ' + st + ' airport in ' + (n ? n + ' of 10 such hours' : 'under 1 in 10 such hours')) + '</span>');
  }
  if (r.src === 'spot') bits.push('<span class="cal">' + bi('ฝนชั่วโมงนี้: จุดพยากรณ์ใกล้คุณที่สุด', 'rain this hour: the forecast point nearest you') + '</span>');
  return bits.join(' ');
}

/* temperature line over rain bars, nights shaded, midnights marked */
function chart(rs, Wd, opt) {
  opt = opt || {};
  var n = rs.length, Hh = opt.h || 210, padT = 22, tTop = padT + 8, tBot = opt.mini ? Hh - 58 : Hh - 96, rTop = tBot + 14, rBot = Hh - 24, bw = Wd / n;
  var temps = rs.map(function (r) { return r.temp; }).filter(num), tlo = Math.min.apply(null, temps) - 1, thi = Math.max.apply(null, temps) + 1;
  if (thi - tlo < 6) { var mid = (thi + tlo) / 2; tlo = mid - 3; thi = mid + 3; }
  function ty(t) { return tBot - (t - tlo) / (thi - tlo) * (tBot - tTop); }
  var g = [], i, narrow = Wd < 520, step = n <= 24 ? (narrow ? 4 : 3) : n <= 48 ? (narrow ? 8 : 6) : (narrow ? 12 : 6);
  /* nights */
  for (i = 0; i < n; i++) if (rs[i].night) { var j = i; while (j + 1 < n && rs[j + 1].night) j++; g.push('<rect x="' + r1(i * bw) + '" y="0" width="' + r1((j - i + 1) * bw) + '" height="' + (Hh - 18) + '" fill="rgba(120,140,220,.09)"/>'); i = j; }
  /* midnights: a dashed line and the day's name */
  for (i = 1; i < n; i++) if (rs[i].t.slice(11, 13) === '00') {
    var dw = dayWord(rs[i].t); g.push('<line x1="' + r1(i * bw) + '" x2="' + r1(i * bw) + '" y1="4" y2="' + (Hh - 20) + '" stroke="rgba(255,255,255,.28)" stroke-dasharray="3 4"/>' +
      '<text x="' + r1(i * bw + 4) + '" y="14" font-size="12" font-weight="700" fill="#e6ecf5">' + esc(L(dw[0], dw[1])) + ' ' + esc(L(dateStr(rs[i].t)[0], dateStr(rs[i].t)[1])) + '</text>');
  }
  /* rain bars */
  g.push('<line x1="0" x2="' + Wd + '" y1="' + rBot + '" y2="' + rBot + '" stroke="rgba(170,180,190,.6)"/>');
  for (i = 0; i < n; i++) {
    var r = rs[i]; if (!num(r.p)) continue;
    var bh = Math.max(1.5, r.p / 100 * (rBot - rTop)), x = i * bw + Math.min(2, bw * 0.15), w = Math.max(1, bw - Math.min(4, bw * 0.3));
    g.push('<rect x="' + r1(x) + '" y="' + r1(rBot - bh) + '" width="' + r1(w) + '" height="' + r1(bh) + '" rx="' + (bw > 8 ? 2.5 : 1) + '" fill="' + rainCol(r.p) + '"/>');
    if (!opt.mini && r.mm >= 0.5 && bw >= 13) g.push('<text x="' + r1(i * bw + bw / 2) + '" y="' + r1(rBot - bh - 4) + '" font-size="11" fill="#cfe2ff" text-anchor="middle">' + r1(r.mm) + '</text>');
  }
  /* temperature */
  if (temps.length > 1) {
    var pts = [], first = -1, last = -1;
    for (i = 0; i < n; i++) if (num(rs[i].temp)) { pts.push(r1(i * bw + bw / 2) + ',' + r1(ty(rs[i].temp))); if (first < 0) first = i; last = i; }
    var gid = 'wxg' + (opt.mini ? 'm' : '') + Math.round(Math.random() * 1e6);
    g.push('<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc94a" stop-opacity=".35"/><stop offset="1" stop-color="#ffc94a" stop-opacity="0"/></linearGradient>' +
      '<linearGradient id="' + gid + 'l" x1="0" y1="' + tTop + '" x2="0" y2="' + tBot + '" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="' + tempCol(thi) + '"/><stop offset="1" stop-color="' + tempCol(tlo) + '"/></linearGradient></defs>');
    g.push('<polygon points="' + r1(first * bw + bw / 2) + ',' + tBot + ' ' + pts.join(' ') + ' ' + r1(last * bw + bw / 2) + ',' + tBot + '" fill="url(#' + gid + ')"/>');
    g.push('<polyline points="' + pts.join(' ') + '" fill="none" stroke="url(#' + gid + 'l)" stroke-width="' + (opt.mini ? 2 : 3) + '" stroke-linejoin="round" stroke-linecap="round"/>');
    /* the warmest and coolest hours, and every few hours, labelled */
    var hiI = -1, loI = -1;
    for (i = 0; i < n; i++) if (num(rs[i].temp)) { if (hiI < 0 || rs[i].temp > rs[hiI].temp) hiI = i; if (loI < 0 || rs[i].temp < rs[loI].temp) loI = i; }
    var lab = {}; lab[hiI] = 1; lab[loI] = 1;
    if (!opt.mini) for (i = 0; i < n; i += step) if (num(rs[i].temp) && Math.abs(i - hiI) > step / 2 && Math.abs(i - loI) > step / 2) lab[i] = 1;
    Object.keys(lab).forEach(function (k) {
      k = +k; if (k < 0) return; var cx = k * bw + bw / 2, cy = ty(rs[k].temp), anc = cx < 14 ? 'start' : cx > Wd - 14 ? 'end' : 'middle';
      g.push('<circle cx="' + r1(cx) + '" cy="' + r1(cy) + '" r="' + (k === hiI || k === loI ? 3.5 : 2.5) + '" fill="' + tempCol(rs[k].temp) + '"/>' +
        '<text x="' + r1(cx) + '" y="' + r1(cy - 8) + '" font-size="' + (opt.mini ? 11 : 13) + '" font-weight="700" fill="#fff" text-anchor="' + anc + '">' + r0(rs[k].temp) + '°</text>');
    });
  }
  /* hours along the foot */
  for (i = 0; i < n; i += step) {
    var tx = i === 0 ? 2 : i * bw + bw / 2;
    g.push('<text x="' + r1(tx) + '" y="' + (Hh - 5) + '" font-size="12" fill="#d3d9e0" text-anchor="' + (i === 0 ? 'start' : 'middle') + '">' + (i === 0 && !opt.mini ? esc(L('ตอนนี้', 'now')) : rs[i].t.slice(11, 13)) + '</text>');
  }
  if (!opt.mini) g.push('<g class="cur"></g><g class="fx"></g>');
  return { svg: '<svg class="' + (opt.mini ? 'wxmini' : 'wxchart') + '" width="' + Wd + '" height="' + Hh + '" viewBox="0 0 ' + Wd + ' ' + Hh + '"' + (opt.mini ? ' aria-hidden="true"' : ' tabindex="0" role="img"') + '>' + g.join('') + '</svg>', bw: bw, ty: ty, rBot: rBot, rTop: rTop, Hh: Hh };
}

function drawHours() {
  var box = $('hours'), c = cityOf(); if (!box || !c) return;
  var all = rowsOf(c), span = Math.min(S.span, all.length), rs = all.slice(0, span), Wd = Math.max(260, Math.round(box.clientWidth - 36));
  var say = rainSay(all), cities = D.W.cities.filter(function (x) { return x.id === 'chiang-mai' || x.id === 'chiang-rai'; });
  var sw = cities.length > 1 ? '<div class="wxsw" role="group" aria-label="' + esc(L('เมือง', 'city')) + '">' + cities.map(function (x) {
    return '<button type="button" data-wxcity="' + x.id + '" aria-pressed="' + (x.id === c.id) + '">' + bi(esc(x.th), esc(x.en)) + '</button>'; }).join('') + '</div>' : '';
  var h = '<div class="wxhead"><h3>' + bi('สภาพอากาศ ' + esc(c.th), 'Weather, ' + esc(c.en)) + '</h3>' + sw + '</div>' + nowPanel(c, all);
  if (say) h += '<p class="wxsay">' + '<span class="' + (/^(Rain|A chance)/.test(say[1]) ? 'wet' : '') + '">' + bi(say[0], say[1]) + '</span></p>';
  if (rs.length > 1) {
    var C = chart(rs, Wd, {});
    h += '<div class="wxread" aria-live="polite">' + readout(c, rs, S.hi == null ? 0 : Math.min(S.hi, rs.length - 1)) + '</div>' + C.svg;
    h += '<div class="wxspan" role="group" aria-label="' + esc(L('ช่วงเวลา', 'span')) + '">' + [24, 48, 72].filter(function (s) { return s <= all.length || s === 24; }).map(function (s) {
      return '<button type="button" data-wxspan="' + s + '" aria-pressed="' + (S.span === s) + '">' + bi(s + ' ชม.', s + ' h') + '</button>'; }).join('') + '</div>';
    h += '<p class="wxsrc"><span class="key"><i class="ln"></i>' + bi('อุณหภูมิ', 'temperature') + '</span><span class="key"><i style="background:#3d8bff"></i>' + bi('โอกาสฝน · ตัวเลข = มม.', 'chance of rain · number = mm') + '</span>' +
      '<span class="key"><i style="background:rgba(120,140,220,.35)"></i>' + bi('กลางคืน', 'night') + '</span>' + bi('แตะหรือลากกราฟเพื่ออ่านแต่ละชั่วโมง', 'tap or drag the chart to read any hour') +
      ' · Open-Meteo' + (rs.some(function (r) { return r.src === 'ifs'; }) ? ' (ECMWF IFS)' : '') + (spotFor(c) ? ' · ' + bi('ฝน 24 ชม.แรก ตามจุดพยากรณ์ใกล้คุณ', 'first 24 h of rain for the point nearest you') : '') + '</p>';
    box.innerHTML = h;
    wireChart(box.querySelector('svg.wxchart'), C, c, rs, box.querySelector('.wxread'));
  } else box.innerHTML = h;
  var big = box.querySelector('.wxbig'); if (big) big.onclick = function () { wiggle(big.querySelector('svg')); };
}

function wireChart(svg, C, c, rs, out) {
  if (!svg) return;
  var cur = svg.querySelector('.cur'), fx = svg.querySelector('.fx'), n = rs.length;
  function put(i, splash) {
    i = Math.max(0, Math.min(n - 1, i)); S.hi = i;
    var x = i * C.bw;
    cur.innerHTML = '<rect x="' + r1(x) + '" y="2" width="' + r1(Math.max(2, C.bw)) + '" height="' + (C.Hh - 22) + '" fill="rgba(255,255,255,.1)" stroke="#fff" stroke-width="1.5" rx="3"/>';
    out.innerHTML = readout(c, rs, i);
    svg.setAttribute('aria-label', out.textContent);
    if (splash && !REDUCED) {
      var r = rs[i], cy = num(r.p) ? C.rBot - Math.max(1.5, r.p / 100 * (C.rBot - C.rTop)) : C.rBot;
      var el = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      el.setAttribute('cx', r1(x + C.bw / 2)); el.setAttribute('cy', r1(cy)); el.setAttribute('r', '9'); el.setAttribute('fill', 'none');
      el.setAttribute('stroke', num(r.p) && r.p >= 30 ? '#8fc1ff' : '#ffc94a'); el.setAttribute('stroke-width', '2.5'); el.setAttribute('class', 'splash');
      fx.appendChild(el); setTimeout(function () { el.remove(); }, 700);
    }
  }
  function at(ev) { var b = svg.getBoundingClientRect(); return Math.floor((ev.clientX - b.left) / b.width * n); }
  var down = false;
  svg.addEventListener('pointerdown', function (ev) { down = true; put(at(ev), true); });
  svg.addEventListener('pointermove', function (ev) { if (down || ev.pointerType === 'mouse') put(at(ev), false); });
  addEventListener('pointerup', function () { down = false; });
  svg.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') { ev.preventDefault(); put((S.hi || 0) + (ev.key === 'ArrowRight' ? 1 : -1), true); }
    if (ev.key === 'Home') { ev.preventDefault(); put(0, true); }
  });
  put(S.hi == null ? 0 : S.hi, false);
}

/* ------------------------------------------------------------ the week */
function drawDays() {
  var box = $('days3'), c = cityOf(); if (!box || !c) return;
  var td = today(), days = (c.days || []).filter(function (d) { return d.date >= td; }).slice(0, 7); if (!days.length) { box.innerHTML = ''; return; }
  var lo = Math.min.apply(null, days.map(function (d) { return d.min; })), hi = Math.max.apply(null, days.map(function (d) { return d.max; })), rg = Math.max(1, hi - lo);
  var hx = rowsOf(c);
  var h = '<h3>' + bi(days.length + ' วัน', days.length + ' days') + '</h3><div id="days">' + days.map(function (d, i) {
    var w = dayWord(d.date), ds = dateStr(d.date), a = (d.min - lo) / rg * 100, b = (d.max - lo) / rg * 100;
    var dot = i === 0 && num(c.temp) && c.temp >= d.min - 3 && c.temp <= d.max + 3 ? '<s style="left:' + r1(Math.max(0, Math.min(100, (c.temp - lo) / rg * 100))) + '%" title="' + r0(c.temp) + '°"></s>' : '';
    var rp = num(d.prob) ? '<span class="rp">' + d.prob + '%' + (num(d.rain) && d.rain >= 0.1 ? '<small>' + r1(d.rain) + (en() ? ' mm' : ' มม.') + '</small>' : '') + '</span>' : '<span class="rp"></span>';
    var open = S.open === d.date;
    var row = '<button type="button" class="wxd" data-wxday="' + d.date + '" aria-expanded="' + open + '" aria-controls="wxdx-' + d.date + '">' +
      '<span class="dn">' + bi(i === 0 ? 'วันนี้' : DAY_TH[dow(d.date)], i === 0 ? 'Today' : DAY_EN[dow(d.date)]) + '<small>' + bi(ds[0], ds[1]) + '</small></span>' + icon(d.code, false, 30) + rp +
      '<span class="lo">' + r0(d.min) + '°</span><span class="rng"><i style="left:' + r1(a) + '%;width:' + r1(Math.max(3, b - a)) + '%;background:linear-gradient(90deg,' + tempCol(d.min) + ',' + tempCol(d.max) + ')"></i>' + dot + '</span>' +
      '<span class="hi">' + r0(d.max) + '°</span></button>';
    var x = '<div class="wxdx" id="wxdx-' + d.date + '"' + (open ? '' : ' hidden') + '>';
    if (open) {
      var wm = wmo(d.code), ub = uvBand(d.uv), cp = num(d.wind_dir) ? compass(d.wind_dir) : null, li = [];
      if (d.sunrise && d.sunset) li.push('<li>' + bi('ขึ้น', 'sunrise') + ' <b>' + d.sunrise.slice(11, 16) + '</b></li><li>' + bi('ตก', 'sunset') + ' <b>' + d.sunset.slice(11, 16) + '</b></li>');
      if (num(d.rain)) li.push('<li>' + bi('ฝนรวม', 'rain') + ' <b>' + r1(d.rain) + '</b> ' + bi('มม.', 'mm') + '</li>');
      if (num(d.prob)) li.push('<li>' + bi('โอกาสฝนสูงสุด', 'top chance') + ' <b>' + d.prob + '%</b></li>');
      if (ub) li.push('<li>' + bi('UV สูงสุด', 'UV peak') + ' <b>' + r0(d.uv) + '</b> ' + bi(ub[0], ub[1]) + '</li>');
      if (num(d.wind)) li.push('<li>' + bi('ลมแรงสุด', 'wind up to') + ' <b>' + r0(d.wind) + '</b> ' + bi('กม./ชม.' + (cp ? ' จาก' + cp[0] : ''), 'km/h' + (cp ? ' from ' + cp[1] : '')) + '</li>');
      x += '<p class="cond">' + bi(wm[0], wm[1]) + ' · ' + r0(d.max) + '° / ' + r0(d.min) + '°</p><ul>' + li.join('') + '</ul>';
      var dayRows = hx.filter(function (r) { return r.t.slice(0, 10) === d.date; });
      if (dayRows.length >= 6) x += chart(dayRows, Math.max(220, Math.round(box.clientWidth - 60)), { mini: true, h: 120 }).svg;
    }
    return row + x + '</div>';
  }).join('') + '</div>';
  box.innerHTML = h;
}

/* ------------------------------------------------------------ the air */
var BANDS = [[0, 15, 'excellent', 'ดีมาก', 'Very good', '#3bb2d0'], [15, 25, 'good', 'ดี', 'Good', '#4caf50'], [25, 37.5, 'moderate', 'ปานกลาง', 'Moderate', '#f6c445'],
  [37.5, 75, 'unhealthy', 'เริ่มมีผลต่อสุขภาพ', 'Starting to affect health', '#f08a3c'], [75, 1e9, 'hazardous', 'มีผลต่อสุขภาพ', 'Affects health', '#d1495b']];
/* the Pollution Control Department's advice for each band, as air4thai words it, shortened */
var ADVICE = {
  excellent: ['เหมาะสำหรับกิจกรรมกลางแจ้งและการท่องเที่ยว', 'Suits outdoor activity and travel.'],
  good: ['ทำกิจกรรมกลางแจ้งและท่องเที่ยวได้ตามปกติ', 'Outdoor activity and travel as usual.'],
  moderate: ['คนทั่วไปทำกิจกรรมกลางแจ้งได้ตามปกติ · คนที่ต้องดูแลสุขภาพเป็นพิเศษ ถ้ามีอาการ เช่น ไอ หายใจลำบาก ระคายเคืองตา ควรลดเวลากิจกรรมกลางแจ้ง',
    'Most people: outdoors as usual. People who need extra care: with a cough, short breath or sore eyes, spend less time outdoors.'],
  unhealthy: ['คนทั่วไปควรเฝ้าระวังสุขภาพ ถ้ามีอาการควรลดเวลากิจกรรมกลางแจ้ง หรือใช้อุปกรณ์ป้องกันตนเอง · คนที่ต้องดูแลสุขภาพเป็นพิเศษควรลดเวลากิจกรรมกลางแจ้ง',
    'Most people: watch for symptoms; with any, spend less time outdoors or wear a mask. People who need extra care: spend less time outdoors.'],
  hazardous: ['ทุกคนควรหลีกเลี่ยงกิจกรรมกลางแจ้งและพื้นที่ที่มีมลพิษสูง หรือใช้อุปกรณ์ป้องกันตนเอง ถ้ามีอาการควรปรึกษาแพทย์',
    'Everyone: avoid outdoor activity and smoky places, or wear a mask; see a doctor if symptoms come.']
};
function bandOf(pm) { if (!num(pm)) return null; for (var i = 0; i < BANDS.length; i++) if (pm <= BANDS[i][1]) return BANDS[i]; return BANDS[BANDS.length - 1]; }
function inkOn(hex) { var v = parseInt(hex.slice(1), 16), r = v >> 16, g = (v >> 8) & 255, b = v & 255; return (r * 299 + g * 587 + b * 114) / 1000 > 140 ? '#111' : '#fff'; }
function nearest(list) {
  var w = D.where; if (!w) return null; var best = null, bd = 1e9;
  list.forEach(function (p) { var d = Math.hypot((p.lat - w.lat) * 111, (p.lng - w.lng) * 105); if (d < bd) { bd = d; best = p; } });
  return bd < 60 ? best : null;
}
function placeOf() {
  var A = D.A; if (!A || !A.places) return null;
  var id = S.place || (D.where && D.where.lat > 19.5 ? 'chiang-rai' : 'chiang-mai');
  return A.places.filter(function (p) { return p.id === id; })[0] || A.places[0];
}
function visKm(pm) { return 3912 / (13.3 * pm + 20); }

function airChart(p, Wd) {
  var td = today(), past = (p.days || []).filter(function (d) { return d.date < td; }).slice(-7);
  var hrs = (p.hours || []).filter(function (h) { return num(h[1]) && h[0].slice(0, 10) >= td; });
  var futDays = hrs.length ? [] : (p.days || []).filter(function (d) { return d.date >= td; });
  var Hh = 170, top = 22, bot = Hh - 24, vals = past.map(function (d) { return d.pm25; }).concat(hrs.map(function (h) { return h[1]; })).concat(futDays.map(function (d) { return d.pm25; })).concat([p.pm25 || 0]);
  var mx = Math.max(40, Math.max.apply(null, vals) * 1.12), y = function (v) { return bot - v / mx * (bot - top); };
  var split = past.length ? Wd * (hrs.length ? 0.38 : 0.6) : 0, pw = past.length ? split / past.length : 0;
  var units = hrs.length || futDays.length, fw = (Wd - split) / Math.max(1, units), g = [], items = [];
  BANDS.slice(0, 4).forEach(function (b) {               /* the band floors as faint lines */
    if (b[1] > mx) return;
    g.push('<line x1="0" x2="' + Wd + '" y1="' + r1(y(b[1])) + '" y2="' + r1(y(b[1])) + '" stroke="' + BANDS[BANDS.indexOf(b) + 1][5] + '" stroke-opacity=".5" stroke-dasharray="2 4"/>' +
      '<text x="' + (Wd - 2) + '" y="' + r1(y(b[1]) - 3) + '" font-size="10" fill="' + BANDS[BANDS.indexOf(b) + 1][5] + '" text-anchor="end">' + b[1] + '</text>');
  });
  past.forEach(function (d, i) {
    var bb = bandOf(d.pm25), x = i * pw;
    g.push('<rect x="' + r1(x + 3) + '" y="' + r1(y(d.pm25)) + '" width="' + r1(pw - 6) + '" height="' + r1(bot - y(d.pm25)) + '" rx="3" fill="' + bb[5] + '"/>');
    g.push('<text x="' + r1(x + pw / 2) + '" y="' + (Hh - 7) + '" font-size="11" fill="#d3d9e0" text-anchor="middle">' + esc(L(DAY_TH[dow(d.date)], DAY_EN[dow(d.date)].slice(0, 2))) + '</text>');
    items.push({ x0: x, x1: x + pw, say: function () { var ds = dateStr(d.date), b2 = bandOf(d.pm25); return bi('เฉลี่ยวัน' + DAYL_TH[dow(d.date)] + ' ' + ds[0], DAY_EN[dow(d.date)] + ' ' + ds[1] + ', day mean') + ' <b>' + r1(d.pm25) + '</b> · ' + bi(b2[3], b2[4]); }, cx: x + pw / 2, cy: y(d.pm25) });
  });
  if (split) g.push('<line x1="' + r1(split) + '" x2="' + r1(split) + '" y1="4" y2="' + bot + '" stroke="rgba(255,255,255,.35)"/>');
  var nk = hourKey(Date.now()), nowX = null;
  hrs.forEach(function (h, i) {
    var bb = bandOf(h[1]), x = split + i * fw, fut = h[0] > nk;
    g.push('<rect x="' + r1(x) + '" y="' + r1(y(h[1])) + '" width="' + r1(Math.max(1, fw - (fw > 4 ? 1 : 0))) + '" height="' + r1(bot - y(h[1])) + '" fill="' + bb[5] + '"' + (fut ? ' fill-opacity=".7"' : '') + '/>');
    if (h[0] === nk) nowX = x + fw / 2;
    if (h[0].slice(11, 13) === '00') {
      var dw = dayWord(h[0]); g.push('<text x="' + r1(x + 3) + '" y="' + (Hh - 7) + '" font-size="11" fill="#e6ecf5" font-weight="700">' + esc(L(dw[0], dw[1])) + '</text>');
      if (i) g.push('<line x1="' + r1(x) + '" x2="' + r1(x) + '" y1="12" y2="' + bot + '" stroke="rgba(255,255,255,.2)" stroke-dasharray="3 4"/>');
    }
    items.push({ x0: x, x1: x + fw, say: function () { var b2 = bandOf(h[1]), w = dayWord(h[0]); return bi(w[0] + ' ' + h[0].slice(11, 16), w[1] + ' ' + h[0].slice(11, 16)) + ' <b>' + r1(h[1]) + '</b> · ' + bi(b2[3], b2[4]) + (fut ? ' · ' + bi('พยากรณ์', 'forecast') : ''); }, cx: x + fw / 2, cy: y(h[1]) });
  });
  futDays.forEach(function (d, i) {
    var bb = bandOf(d.pm25), x = split + i * fw;
    g.push('<rect x="' + r1(x + 3) + '" y="' + r1(y(d.pm25)) + '" width="' + r1(fw - 6) + '" height="' + r1(bot - y(d.pm25)) + '" rx="3" fill="' + bb[5] + '" fill-opacity=".7"/>');
    var dw = dayWord(d.date); g.push('<text x="' + r1(x + fw / 2) + '" y="' + (Hh - 7) + '" font-size="11" fill="#d3d9e0" text-anchor="middle">' + esc(L(dw[0], dw[1])) + '</text>');
    items.push({ x0: x, x1: x + fw, say: function () { var b2 = bandOf(d.pm25), w = dayWord(d.date); return bi(w[0] + ' (พยากรณ์ เฉลี่ยทั้งวัน)', w[1] + ' (forecast, day mean)') + ' <b>' + r1(d.pm25) + '</b> · ' + bi(b2[3], b2[4]); }, cx: x + fw / 2, cy: y(d.pm25) });
  });
  if (nowX != null) g.push('<line x1="' + r1(nowX) + '" x2="' + r1(nowX) + '" y1="10" y2="' + bot + '" stroke="#fff" stroke-width="1.5"/><text x="' + r1(nowX) + '" y="9" font-size="11" font-weight="700" fill="#fff" text-anchor="middle">' + esc(L('ตอนนี้', 'now')) + '</text>');
  if (past.length) g.push('<text x="2" y="12" font-size="11" fill="#d3d9e0">' + esc(L('สัปดาห์ที่ผ่านมา', 'past week')) + '</text>');
  g.push('<line x1="0" x2="' + Wd + '" y1="' + bot + '" y2="' + bot + '" stroke="rgba(170,180,190,.6)"/><g class="cur"></g><g class="fx"></g>');
  return { svg: '<svg class="wxchart" width="' + Wd + '" height="' + Hh + '" viewBox="0 0 ' + Wd + ' ' + Hh + '" tabindex="0" role="img">' + g.join('') + '</svg>', items: items, Hh: Hh, nowI: items.length ? (function () { for (var i = 0; i < items.length; i++) if (nowX != null && items[i].x0 <= nowX && items[i].x1 > nowX) return i; return items.length - 1; })() : 0 };
}
/* the next day's story: better or worse than today, and the cleanest hours ahead */
function airSay(p) {
  var td = today(), tm = plus(td, 1), nk = hourKey(Date.now());
  var hrs = (p.hours || []).filter(function (h) { return num(h[1]); });
  function mean(d) { var xs = hrs.filter(function (h) { return h[0].slice(0, 10) === d; }).map(function (h) { return h[1]; }); if (xs.length < 12) { var dd = (p.days || []).filter(function (x) { return x.date === d; })[0]; return dd ? dd.pm25 : null; } return xs.reduce(function (a, b) { return a + b; }, 0) / xs.length; }
  var a = mean(td), b = mean(tm), out = [];
  if (num(a) && num(b)) {
    var diff = b - a, bb = bandOf(b);
    out.push(Math.abs(diff) < 2.5 ? ['พรุ่งนี้ราวๆ เดิม เฉลี่ย ' + r0(b) + ' (' + bb[3] + ')', 'Tomorrow about the same, averaging ' + r0(b) + ' (' + bb[4].toLowerCase() + ')']
      : diff < 0 ? ['พรุ่งนี้ดีขึ้น เฉลี่ย ' + r0(b) + ' จากวันนี้ ' + r0(a), 'Cleaner tomorrow: averaging ' + r0(b) + ', against ' + r0(a) + ' today']
      : ['พรุ่งนี้แย่ลง เฉลี่ย ' + r0(b) + ' จากวันนี้ ' + r0(a), 'Smokier tomorrow: averaging ' + r0(b) + ', against ' + r0(a) + ' today']);
  }
  var ahead = hrs.filter(function (h) { return h[0] > nk; }).slice(0, 24);
  var day = ahead.filter(function (h) { var hh = +h[0].slice(11, 13); return hh >= 6 && hh <= 20; });
  if (day.length) {
    var best = day.reduce(function (m, h) { return h[1] < m[1] ? h : m; }, day[0]), w = dayWord(best[0]);
    out.push(['ช่วงกลางวันที่อากาศสะอาดสุด ' + w[0] + ' ' + best[0].slice(11, 16) + ' (' + r0(best[1]) + ')', 'cleanest daylight hour ahead: ' + w[1] + ' ' + best[0].slice(11, 16) + ' (' + r0(best[1]) + ')']);
  }
  return out;
}
function drawAir() {
  var box = $('airp'), A = D.A, p = placeOf(); if (!box || !p) return;
  var b = bandOf(p.pm25) || BANDS[1], sel = S.band != null ? BANDS[S.band] : b, td = today();
  var near = nearest(A.places);
  var h = '<div class="wxhead"><h3>' + bi('คุณภาพอากาศ ' + esc(p.th), 'The air, ' + esc(p.en)) + '</h3></div><div class="airg">';
  /* now */
  h += '<div class="airnow"><div class="airbig"><b style="color:' + b[5] + '">' + (num(p.pm25) ? r0(p.pm25) : '–') + '</b><small>PM2.5 µg/m³</small></div>' +
    '<span class="airband" style="background:' + b[5] + ';color:' + inkOn(b[5]) + '">' + bi(b[3], b[4]) + '</span>' +
    '<div class="airsub">' + (num(p.usAqi) ? 'US AQI <b>' + r0(p.usAqi) + '</b> · ' : '') + (num(p.pm10) ? 'PM10 <b>' + r0(p.pm10) + '</b> · ' : '') + (p.observed ? bi('เมื่อ ' + p.observed.slice(11, 16), 'at ' + p.observed.slice(11, 16)) : '') + '</div>';
  var cap = 100, gs = BANDS.map(function (x, i) {
    var w = (Math.min(x[1], cap) - x[0]) / cap * 100;
    return '<button type="button" class="wxseg" data-wxband="' + i + '" aria-pressed="' + (sel === x) + '" style="width:calc(' + r1(w) + '% - 2px);background:' + x[5] + '" aria-label="' + esc(L(x[3], x[4]) + ' ' + x[0] + '–' + (x[1] > 999 ? '' : x[1])) + '"></button>';
  }).join('');
  h += '<div class="airgauge">' + gs + (num(p.pm25) ? '<span class="mk" style="left:' + r1(Math.min(99, p.pm25 / cap * 100)) + '%"></span>' : '') + '</div>' +
    '<div class="airticks">' + [15, 25, 37.5, 75].map(function (v) { return '<span style="left:' + v + '%">' + v + '</span>'; }).join('') + '</div>';
  var adv = ADVICE[sel[2]];
  h += '<p class="airadv" style="border-left-color:' + sel[5] + '"><b>' + bi(sel[3] + (sel === b ? ' · ตอนนี้' : ' · ' + sel[0] + '–' + (sel[1] > 999 ? '' : sel[1])), sel[4] + (sel === b ? ' · now' : ' · ' + sel[0] + '–' + (sel[1] > 999 ? '+' : sel[1]))) + '</b>' + bi(adv[0], adv[1]) + '</p>';
  if (p.id === 'chiang-mai' && num(p.pm25)) {
    var V = visKm(p.pm25), C = Math.exp(-3.912 * 10.8 / V);
    h += '<p class="airvis">' + bi('มองได้ไกลราว ' + r0(V) + ' กม. · ' + (C > 0.1 ? 'เห็นดอยสุเทพชัด' : C > 0.01 ? 'ดอยสุเทพจางในหมอกควัน' : 'ควันบังดอยสุเทพ'),
      'You could see about ' + r0(V) + ' km · ' + (C > 0.1 ? 'Doi Suthep stands clear' : C > 0.01 ? 'Doi Suthep is fading in the haze' : 'smoke hides Doi Suthep')) + '</p>';
  }
  h += '</div>';
  /* the chart */
  var cw = box.clientWidth, Wd = Math.max(260, Math.round(cw > 980 ? cw * 0.46 : cw - 40)), AC = airChart(p, Wd), say = airSay(p);
  h += '<div class="airchart"><h4>' + bi('สัปดาห์ที่ผ่านมา และวันข้างหน้า', 'The past week and the days ahead') + '</h4>' +
    (say.length ? '<p class="airsay">' + say.map(function (s) { return bi(s[0], s[1]); }).join('<br>') + '</p>' : '') +
    '<div class="wxread" aria-live="polite"></div>' + AC.svg + '</div>';
  /* the towns */
  var mxT = Math.max(50, Math.max.apply(null, A.places.map(function (x) { return x.pm25 || 0; })));
  h += '<div class="airtowns"><h4>' + bi('เมืองทางเหนือ ตอนนี้', 'The north, now') + '</h4>' + A.places.slice().sort(function (x, y2) { return (x.pm25 || 0) - (y2.pm25 || 0); }).map(function (x) {
    var bb = bandOf(x.pm25) || BANDS[1];
    return '<button type="button" class="wxtown" data-wxplace="' + x.id + '" aria-pressed="' + (x.id === p.id) + '"><span>' + bi(esc(x.th), esc(x.en)) + (near && near.id === x.id ? '<small>' + bi('ใกล้คุณ', 'near you') + '</small>' : '') + '</span>' +
      '<span class="tb"><i style="width:' + r1(Math.max(4, (x.pm25 || 0) / mxT * 100)) + '%;background:' + bb[5] + '"></i></span><b>' + (num(x.pm25) ? r0(x.pm25) : '–') + '</b></button>';
  }).join('') + '</div></div>';
  h += '<p class="wxsrc">' + bi('แบบจำลอง CAMS ผ่าน Open-Meteo ไม่ใช่เครื่องวัดริมถนน · แถบสีตามเกณฑ์ PM2.5 ของกรมควบคุมมลพิษ · คำแนะนำย่อจาก air4thai · แตะแถบสีเพื่ออ่านคำแนะนำ แตะกราฟเพื่ออ่านแต่ละวันและชั่วโมง',
    'CAMS model via Open-Meteo, not a street-level monitor · colours are the Pollution Control Department\'s PM2.5 bands · advice shortened from air4thai · tap a colour for its advice, the chart for any day or hour') + '</p>';
  box.innerHTML = h;
  /* the chart reads where the finger is */
  var svg = box.querySelector('.airchart svg'), out = box.querySelector('.airchart .wxread'), cur = svg.querySelector('.cur'), fx = svg.querySelector('.fx'), its = AC.items;
  function put(i, splash) {
    if (!its.length) return; i = Math.max(0, Math.min(its.length - 1, i)); S.ahi = i; var it = its[i];
    cur.innerHTML = '<rect x="' + r1(it.x0) + '" y="2" width="' + r1(Math.max(2, it.x1 - it.x0)) + '" height="' + (AC.Hh - 24) + '" fill="rgba(255,255,255,.1)" stroke="#fff" stroke-width="1.5" rx="3"/>';
    out.innerHTML = it.say(); svg.setAttribute('aria-label', out.textContent);
    if (splash && !REDUCED) {
      var el = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      el.setAttribute('cx', r1(it.cx)); el.setAttribute('cy', r1(it.cy)); el.setAttribute('r', '9'); el.setAttribute('fill', 'none'); el.setAttribute('stroke', '#fff'); el.setAttribute('stroke-width', '2.5'); el.setAttribute('class', 'splash');
      fx.appendChild(el); setTimeout(function () { el.remove(); }, 700);
    }
  }
  function at(ev) { var bx = svg.getBoundingClientRect(), x = (ev.clientX - bx.left) / bx.width * Wd; for (var i = 0; i < its.length; i++) if (x < its[i].x1) return i; return its.length - 1; }
  var down = false;
  svg.addEventListener('pointerdown', function (ev) { down = true; put(at(ev), true); });
  svg.addEventListener('pointermove', function (ev) { if (down || ev.pointerType === 'mouse') put(at(ev), false); });
  addEventListener('pointerup', function () { down = false; });
  svg.addEventListener('keydown', function (ev) { if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') { ev.preventDefault(); put((S.ahi == null ? AC.nowI : S.ahi) + (ev.key === 'ArrowRight' ? 1 : -1), true); } });
  put(S.ahi == null ? AC.nowI : S.ahi, false);
}

/* ------------------------------------------------------------ taps */
document.addEventListener('click', function (ev) {
  var t = ev.target.closest && ev.target.closest('[data-wxcity],[data-wxspan],[data-wxday],[data-wxplace],[data-wxband]'); if (!t) return;
  if (t.dataset.wxcity) { S.city = t.dataset.wxcity; store('md-wx-city', S.city); S.hi = null; S.open = null; drawHours(); drawDays(); }
  else if (t.dataset.wxspan) { S.span = +t.dataset.wxspan; store('md-wx-span', S.span); S.hi = null; drawHours(); }
  else if (t.dataset.wxday) { S.open = S.open === t.dataset.wxday ? null : t.dataset.wxday; drawDays(); var nb = document.querySelector('[data-wxday="' + t.dataset.wxday + '"]'); if (nb) { nb.focus(); wiggle(nb.querySelector('svg.wxi')); } }
  else if (t.dataset.wxplace) { S.place = t.dataset.wxplace; store('md-air-place', S.place); S.band = null; S.ahi = null; drawAir(); var pb = document.querySelector('[data-wxplace="' + S.place + '"]'); if (pb) pb.focus(); }
  else if (t.dataset.wxband) { var bi2 = +t.dataset.wxband; S.band = S.band === bi2 ? null : bi2; drawAir(); var sb = document.querySelector('[data-wxband="' + bi2 + '"]'); if (sb) sb.focus(); }
});
new MutationObserver(function () { if (D.W) draw(); }).observe(H, { attributes: true, attributeFilter: ['class'] });

function draw() {
  [drawHours, drawDays, drawAir].forEach(function (f) { try { f(); } catch (e) { console.error(e); } });
}
window.MDWX = {
  /* front.js calls this from forecast(); false sends it back to its own three tiles */
  render: function (W, A, where, spot) {
    if (!W || !W.cities || !W.cities.length) return false;
    D.W = W; D.A = A; D.where = where; D.spot = spot;
    draw();
    return true;
  }
};
})();
