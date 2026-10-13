/* /parking/ — where to park, whether it is full, and where you left your bike.

   Places come from t/<tile>.json (tools/parking_bake.py), habits of kinds of
   place and the busy zones from model.json, readers' taps from the claims
   worker (/parking). Your own parked spot comes from the Android app
   (window.MotDangApp.park*, which notices when you stop riding and start
   walking) or, in a browser, from the "I parked here" button; it is kept on
   the phone (localStorage) and in the app's own storage. */
(function () {
'use strict';
var WORKER = 'https://mot-dang-claims.nanobotco.workers.dev/parking';
var BASE = document.documentElement.getAttribute('data-pk') || '';
var APK = BASE + 'motdang.apk';
var APP = (window.MotDangApp && typeof window.MotDangApp.parkState === 'function') ? window.MotDangApp : null;
var GATE = {th: 'ประตูท่าแพ', en: 'Tha Phae Gate', lat: 18.7876, lng: 98.9931};
var $ = function (s, r) { return (r || document).querySelector(s); };

function store(k, v) {
  try {
    if (v === undefined) return JSON.parse(localStorage.getItem(k));
    if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v));
  } catch (e) { return null; }
}
var LANG = store('md-lang') || ((navigator.language || '').slice(0, 2) === 'th' ? 'th' : (store('md-lang') || 'th'));
function L(th, en) { return LANG === 'th' ? th : en; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
function icon(id) { return '<svg class="ic" viewBox="0 0 24 24"><use href="../icons.svg#' + id + '"/></svg>'; }
function buzz(p) {
  try { if (APP && APP.vibrate) { APP.vibrate(String(p)); return; } } catch (e) {}
  try { navigator.vibrate && navigator.vibrate(p); } catch (e) {}
}

/* ------------------------------------------------------------ geometry */
function metres(a, b, c, d) {
  var k = Math.cos((a + c) / 2 * Math.PI / 180);
  return Math.hypot((c - a) * 111320, (d - b) * 111320 * k);
}
function bearing(a, b, c, d) {
  var y = Math.sin((d - b) * Math.PI / 180) * Math.cos(c * Math.PI / 180);
  var x = Math.cos(a * Math.PI / 180) * Math.sin(c * Math.PI / 180) -
          Math.sin(a * Math.PI / 180) * Math.cos(c * Math.PI / 180) * Math.cos((d - b) * Math.PI / 180);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}
var DIR8 = [['ทางเหนือ', 'north'], ['ทางตะวันออกเฉียงเหนือ', 'north-east'], ['ทางตะวันออก', 'east'],
  ['ทางตะวันออกเฉียงใต้', 'south-east'], ['ทางใต้', 'south'], ['ทางตะวันตกเฉียงใต้', 'south-west'],
  ['ทางตะวันตก', 'west'], ['ทางตะวันตกเฉียงเหนือ', 'north-west']];
function dir8(deg) { var d = DIR8[Math.round(deg / 45) % 8]; return L(d[0], d[1]); }
function fmtD(m) {
  if (m < 1000) return Math.round(m / 10) * 10 + L(' ม.', ' m');
  return (m / 1000).toFixed(m < 10000 ? 1 : 0) + L(' กม.', ' km');
}
function ago(ms) {
  var m = Math.round((Date.now() - ms) / 60000);
  if (m < 1) return L('เมื่อกี้', 'just now');
  if (m < 60) return m + L(' นาทีที่แล้ว', ' min ago');
  var h = Math.floor(m / 60), r = m % 60;
  if (h < 24) return h + L(' ชม. ', ' h ') + (r ? r + L(' นาที', ' min') : '') + L('ที่แล้ว', ' ago');
  return Math.round(h / 24) + L(' วันที่แล้ว', ' days ago');
}
function hhmm(ms) { var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
var DAYS = [['อา.', 'Sun'], ['จ.', 'Mon'], ['อ.', 'Tue'], ['พ.', 'Wed'], ['พฤ.', 'Thu'], ['ศ.', 'Fri'], ['ส.', 'Sat']];
function days(d) {
  if (d === '0123456') return L('ทุกวัน', 'daily');
  if (d === '12345') return L('จ.–ศ.', 'Mon–Fri');
  return d.split('').map(function (x) { return L(DAYS[x][0], DAYS[x][1]); }).join(L(' ', ', '));
}

/* --------------------------------------------------------------- data */
var MODEL = null, CLS = {}, LOTS = new Map(), TILES = new Set(), NOW = new Map(), HIST = new Map();
var VEH = store('md-park-veh') || 'm', FILT = new Set(), SHOW = 25;
var here = null, from = null, fromIsMe = false, map = null, mapEl = $('#pkmap'), bikeMk = null, meMk = null;

function tileKey(la, ln) { return Math.floor(la * MODEL.tile) + '_' + Math.floor(ln * MODEL.tile); }
function ensureTiles(la, ln) {
  var want = [], step = 1 / MODEL.tile;
  for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) {
    var k = tileKey(la + dy * step, ln + dx * step);
    if (!TILES.has(k) && MODEL.tiles.indexOf(k) >= 0) { TILES.add(k); want.push(k); }
  }
  return Promise.all(want.map(function (k) {
    return fetch(BASE + 't/' + k + '.json').then(function (r) { return r.json(); }).then(function (rows) {
      rows.forEach(function (r) { LOTS.set(r.id, r); });
    }).catch(function () { TILES.delete(k); });
  }));
}
function fetchNow() {
  return fetch(WORKER + '?hours=3').then(function (r) { return r.json(); }).then(function (j) {
    NOW = new Map();
    (j.reports || []).forEach(function (r) {
      if (!NOW.has(r.placeId)) NOW.set(r.placeId, []);
      NOW.get(r.placeId).push(r);
    });
    NOW.forEach(function (a) { a.sort(function (x, y) { return x.at < y.at ? 1 : -1; }); });
  }).catch(function () {});
}

/* ------------------------------------------------------------ answers
   Each answer is {v, b}: b is m (mapped), s (seen on a ride), u (usual for
   the kind of place), r (a reader's tap). A tap outranks a sighting, a
   sighting a map tag, a map tag a habit. */
function latest(reps, kinds, maxMin) {
  for (var i = 0; i < reps.length; i++) {
    var r = reps[i];
    if (kinds.indexOf(r.answer) < 0) continue;
    var t = Date.parse(r.at);
    if (maxMin && Date.now() - t > maxMin * 60000) return null;
    return {answer: r.answer, t: t};
  }
  return null;
}
function busyNow(lot) {
  var d = new Date(), wd = String(d.getDay()), h = d.getHours() + d.getMinutes() / 60, out = null;
  (MODEL.zones || []).forEach(function (z) {
    if (!out && z.d.indexOf(wd) >= 0 && h >= z.h[0] && h < z.h[1] && metres(lot.la, lot.ln, z.lat, z.lng) <= z.r)
      out = {why: L(z.th, z.en)};
  });
  var c = CLS[lot.c];
  if (!out && c) (c.busy || []).forEach(function (w) {
    if (!out && w.d.indexOf(wd) >= 0 && h >= w.h[0] && h < w.h[1]) out = {why: L('ช่วงคนเยอะของ' + c.th, 'busy hours for a ' + c.en)};
  });
  return out;
}
function usualText(lot) {
  var out = [];
  (MODEL.zones || []).forEach(function (z) {
    if (metres(lot.la, lot.ln, z.lat, z.lng) <= z.r)
      out.push(days(z.d) + ' ' + z.h[0] + ':00–' + z.h[1] + ':00 (' + L(z.th, z.en) + ')');
  });
  var c = CLS[lot.c];
  if (c) (c.busy || []).forEach(function (w) { out.push(days(w.d) + ' ' + w.h[0] + ':00–' + w.h[1] + ':00'); });
  return out;
}
function answers(lot) {
  var c = CLS[lot.c] || {}, why = lot.b || {}, A = {};
  var reps = (HIST.get(lot.id) || []).concat(NOW.get(lot.id) || []);
  reps.sort(function (x, y) { return x.at < y.at ? 1 : -1; });
  function put(k, v, cv) {
    if (v !== undefined && v !== null && v !== '') A[k] = {v: v, b: why[k] || 'm'};
    else if (cv !== undefined && cv !== null) A[k] = {v: cv, b: 'u'};
  }
  put('veh', lot.veh, c.veh);
  put('cov', lot.cov, c.covered);
  put('off', lot.off, c.off);
  put('h24', lot.h24, c.h24);
  put('hours', lot.hours, c.h24 ? null : c.hours);
  put('fee', lot.fee, c.fee);
  put('acc', lot.acc, null);
  put('att', lot.att, null);
  put('cap', lot.cap, null);
  if (lot.gue) A.gue = {v: true, b: 's'};
  var r;
  if ((r = latest(reps, ['covered']))) A.cov = {v: 'yes', b: 'r', t: r.t};
  if ((r = latest(reps, ['open24']))) A.h24 = {v: true, b: 'r', t: r.t};
  if ((r = latest(reps, ['free', 'paid']))) A.fee = {v: r.answer, b: 'r', t: r.t};
  if ((r = latest(reps, ['bigbike', 'nobigbike']))) A.big = {v: r.answer === 'bigbike', b: 'r', t: r.t};
  if ((r = latest(reps, ['gone']))) A.gone = {v: true, b: 'r', t: r.t};
  var fined = reps.filter(function (x) { return x.answer === 'fined'; });
  if (fined.length) A.fined = {v: fined.length, b: 'r', t: Date.parse(fined[0].at)};
  if ((r = latest(reps, ['full', 'space'], 75))) A.now = {v: r.answer, b: 'r', t: r.t};
  else { var bz = busyNow(lot); if (bz) A.now = {v: 'busy', b: 'u', why: bz.why}; }
  if (c.short) A.short = {v: true, b: 'u'};
  return A;
}
function state(A) { return A.now ? (A.now.v === 'full' ? 'full' : A.now.v === 'space' ? 'ok' : 'busy') : ''; }
function fits(lot, A) {
  if (A.gone) return false;
  if (A.acc && A.acc.v === 'private') return false;
  if (VEH === 'c' && ((A.veh && A.veh.v === 'm') || lot.c === 'seven')) return false;
  if (VEH === 'b' && (lot.c === 'seven' || (A.big && A.big.v === false))) return false;
  if (FILT.has('space') && A.now && A.now.v === 'full') return false;
  if (FILT.has('cov') && !(A.cov && (A.cov.v === 'yes' || A.cov.v === 'part'))) return false;
  if (FILT.has('h24') && !(A.h24 && A.h24.v === true)) return false;
  if (FILT.has('free') && !(A.fee && A.fee.v === 'free')) return false;
  if (FILT.has('off') && !(A.off && A.off.v === true)) return false;
  if (FILT.has('gue') && !lot.gue) return false;
  return true;
}

/* ------------------------------------------------------------- words */
function lotName(lot) {
  var c = CLS[lot.c];
  if (lot.k === 'v') return (LANG === 'en' && lot.en) || lot.th;
  if (lot.at) return L('ที่จอดรถ · ', 'Parking · ') + ((LANG === 'en' && lot.at[1]) || lot.at[0]);
  return (LANG === 'en' && lot.en) || lot.th;
}
function lotKind(lot) {
  var c = CLS[lot.c];
  if (lot.k === 'v' && c) return L('ที่จอดของ' + c.th + ' (มักจะมี)', 'a ' + c.en + "'s parking (usual)");
  return '';
}
function landmarkLine(la, ln) {
  var best = null;
  Object.keys(MODEL.landmarks || {}).forEach(function (p) {
    MODEL.landmarks[p].forEach(function (m) {
      var d = metres(la, ln, m[2], m[3]);
      if (d < 1500 && (!best || d < best.d)) best = {d: d, m: m};
    });
  });
  if (!best) return '';
  if (best.d < 60) return L('ที่' + best.m[0], 'at ' + best.m[1]);
  var dir = dir8(bearing(best.m[2], best.m[3], la, ln));
  return L('ห่าง' + best.m[0] + ' ' + fmtD(best.d) + ' ' + dir, fmtD(best.d) + ' ' + dir + ' of ' + best.m[1]);
}
var BASIS = {m: ['แผนที่', 'mapped'], s: ['เห็นตอนขี่', 'seen on a ride'], r: ['มีคนบอก', 'reported'], u: ['มักจะ', 'usually']};
function basis(a, lot) {
  if (!a) return '';
  var b = BASIS[a.b] || BASIS.m, s = L(b[0], b[1]);
  if (a.b === 'u' && CLS[lot.c]) s = L('มักจะเป็นแบบนี้ที่' + CLS[lot.c].th, 'usual for a ' + CLS[lot.c].en);
  if (a.b === 'r' && a.t) s += ' ' + ago(a.t);
  if (a.b === 's' && lot.seen) s += ' ' + lot.seen;
  return s;
}
function say(k, a, lot) {
  if (!a) return null;
  var v = a.v;
  switch (k) {
    case 'veh': return v === 'm' ? L('มอเตอร์ไซค์', 'Motorbikes') : v === 'cm' ? L('รถยนต์และมอเตอร์ไซค์', 'Cars and motorbikes') : L('ลานจอดรถยนต์', 'Car park');
    case 'cov': return v === 'yes' ? L('มีหลังคา', 'Covered') : v === 'part' ? L('มีหลังคาบางส่วน', 'Partly covered') : L('กลางแจ้ง', 'Open-air');
    case 'off': return v ? L('ลานจอด นอกถนน', 'Off-street') : L('ริมถนน', 'On the kerb');
    case 'h24': return v ? L('๒๔ ชั่วโมง', '24 hours') : null;
    case 'hours': return String(v);
    case 'fee': return v === 'free' ? L('ฟรี', 'Free') : v === 'paid' ? L('เสียเงิน', 'Paid') : v === 'varies' ? L('ฟรี หรือฟรีช่วงแรก', 'Free, or free for the first hours') : String(v);
    case 'acc': return v === 'private' ? L('ส่วนบุคคล', 'Private') : L('เฉพาะลูกค้า', 'Customers only');
    case 'att': return L('มีคนดูแล', 'Attendant');
    case 'cap': return '~' + v + L(' คัน', ' spaces');
    case 'gue': return L('ไม่มีป้าย — รถจอดกันเอง', 'No sign — bikes just park here');
    case 'big': return v ? L('บิ๊กไบค์จอดได้', 'Big bikes OK') : L('บิ๊กไบค์ห้ามจอด', 'No big bikes');
    case 'fined': return L('มีคนเจอล็อกล้อ/ใบสั่ง ' + v + ' ครั้ง', 'Bikes fined: ' + v + (v > 1 ? ' reports' : ' report'));
    case 'now': return v === 'full' ? L('เต็ม', 'Full') : v === 'space' ? L('ยังมีที่', 'Space') : L('น่าจะแน่น', 'Probably busy');
    case 'short': return L('จอดสั้น ๆ ตอนซื้อของ', 'Short stops while you shop');
  }
  return null;
}
function tags(lot, A) {
  var out = [];
  function t(k, cls) {
    var s = say(k, A[k], lot);
    if (!s) return;
    var u = A[k].b === 'u';
    out.push('<span class="pk-tag ' + (cls || (A[k].b === 'r' ? 'r' : A[k].b === 's' ? 's' : u ? 'u' : '')) + '">' +
      (u && k !== 'now' ? L('มักจะ', 'usually ') : '') + esc(s) +
      (k === 'now' && A.now.b === 'r' ? ' · ' + ago(A.now.t) : '') + '</span>');
  }
  if (A.now) t('now', A.now.v === 'full' ? 'bad' : A.now.v === 'space' ? 'r' : 'u');
  t('cov'); t('h24'); if (!(A.h24 && A.h24.v)) t('hours'); t('fee'); t('off'); t('gue', 's'); t('short');
  if (A.fined) t('fined', 'bad');
  if (A.big) t('big', A.big.v ? 'r' : 'bad');
  if (A.acc) t('acc', 'bad');
  return out.join('');
}

/* --------------------------------------------------------------- list */
function candidates() {
  var out = [];
  LOTS.forEach(function (lot) {
    var d = metres(from.lat, from.lng, lot.la, lot.ln);
    if (d > 4000) return;
    var A = answers(lot);
    if (!fits(lot, A)) return;
    var rank = d;
    if (VEH === 'm' && A.veh && A.veh.v !== 'c') rank -= 40;
    if (lot.k === 'v') rank += 60;
    if (A.now && A.now.v === 'full') rank += 400;
    out.push({lot: lot, A: A, d: d, rank: rank});
  });
  out.sort(function (a, b) { return a.rank - b.rank; });
  return out;
}
function render() {
  if (!MODEL || !from) return;
  var all = candidates(), list = $('#list');
  if (!list) { drawMap(all.slice(0, 300)); return; }
  $('#from').textContent = (fromIsMe ? L('ใกล้คุณ', 'Near you') : L('ใกล้', 'Near ') + (from.name || L('จุดกลางแผนที่', 'the map centre'))) +
    ' · ' + all.length + L(' ที่', ' places');
  list.innerHTML = all.slice(0, SHOW).map(function (x) {
    var lot = x.lot, st = state(x.A);
    return '<li data-id="' + esc(lot.id) + '"><span class="pk-p ' + (st || (lot.k === 'l' ? 'lot' : '')) + '">P</span>' +
      '<div class="pk-name">' + esc(lotName(lot)) + '</div>' +
      '<div class="pk-dir">' + fmtD(x.d) + ' · ' + dir8(bearing(from.lat, from.lng, lot.la, lot.ln)) +
      (lotKind(lot) ? ' · ' + esc(lotKind(lot)) : '') + '</div>' +
      '<div class="pk-tags">' + tags(lot, x.A) + '</div></li>';
  }).join('') || '<li>' + L('ยังไม่มีที่จอดในข้อมูลแถวนี้ ลองปิดตัวกรอง', 'No parking in the data here. Try fewer filters.') + '</li>';
  $('#more').hidden = all.length <= SHOW;
  drawMap(all.slice(0, 300));
}

/* ---------------------------------------------------------------- map */
function drawMap(rows) {
  if (!map) return;
  var fc = {type: 'FeatureCollection', features: rows.map(function (x) {
    return {type: 'Feature', geometry: {type: 'Point', coordinates: [x.lot.ln, x.lot.la]},
      properties: {id: x.lot.id, s: state(x.A) || (x.lot.k === 'l' ? 'lot' : 'v')}};
  })};
  var src = map.getSource('pk');
  if (src) src.setData(fc);
}
function initMap(m) {
  map = m;
  m.addSource('pk', {type: 'geojson', data: {type: 'FeatureCollection', features: []}});
  m.addLayer({id: 'pk-c', type: 'circle', source: 'pk', paint: {
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 12, 4, 16, 9],
    'circle-color': ['match', ['get', 's'], 'full', '#B3261E', 'ok', '#2E7D4F', 'busy', '#C9831A', 'lot', '#2B5C8A', '#7A6E62'],
    'circle-stroke-color': '#fff', 'circle-stroke-width': 2}});
  m.on('click', 'pk-c', function (e) { var f = e.features && e.features[0]; if (f) openLot(f.properties.id); });
  m.on('mouseenter', 'pk-c', function () { m.getCanvas().style.cursor = 'pointer'; });
  m.on('mouseleave', 'pk-c', function () { m.getCanvas().style.cursor = ''; });
  m.on('moveend', function (e) {
    if (!e.originalEvent) return;
    var c = m.getCenter();
    from = {lat: c.lat, lng: c.lng}; fromIsMe = false;
    ensureTiles(c.lat, c.lng).then(render);
  });
  placeMarkers();
  render();
}
function placeMarkers() {
  if (!map || !window.maplibregl) return;
  var p = getPark();
  if (bikeMk) { bikeMk.remove(); bikeMk = null; }
  if (p) {
    var el = document.createElement('div');
    el.className = 'pk-bike';
    el.innerHTML = icon(p.vehicle === 'car' ? 'i-ride' : 'i-scooter');
    el.addEventListener('click', function (ev) {
      ev.stopPropagation(); el.classList.remove('hop'); void el.offsetWidth; el.classList.add('hop'); buzz(30);
      location.hash = 'mine'; document.getElementById('mine').scrollIntoView({behavior: 'smooth'});
    });
    bikeMk = new maplibregl.Marker({element: el}).setLngLat([p.lng, p.lat]).addTo(map);
  }
  if (here) {
    if (!meMk) { var me = document.createElement('div'); me.className = 'pk-me'; meMk = new maplibregl.Marker({element: me}); }
    meMk.setLngLat([here.lng, here.lat]).addTo(map);
  }
}
function centreMap(la, ln, z) { if (map) map.jumpTo({center: [ln, la], zoom: z || Math.max(map.getZoom(), 15)}); }

/* ---------------------------------------------------------- one place */
function openLot(id) {
  var lot = LOTS.get(id);
  if (!lot) return;
  var dlg = $('#lot');
  paintLot(lot);
  if (!dlg.open) { try { dlg.showModal(); } catch (e) { dlg.setAttribute('open', ''); } }
  fetch(WORKER + '?id=' + encodeURIComponent(id)).then(function (r) { return r.json(); }).then(function (j) {
    HIST.set(id, j.reports || []);
    if (dlg.open) paintLot(lot);
  }).catch(function () {});
}
function paintLot(lot) {
  var A = answers(lot), hist = HIST.get(lot.id) || [];
  var rows = [
    [L('เต็มไหมตอนนี้', 'Full right now?'), A.now ? say('now', A.now, lot) + (A.now.why ? ' — ' + A.now.why : '') : L('ไม่รู้ — กดบอกด้านล่างได้', 'Not known — tell it below'), A.now],
    [L('ปกติแน่นไหม', 'How full usually?'), usualLine(lot, hist), null],
    [L('รถอะไร', 'For'), say('veh', A.veh, lot), A.veh],
    [L('บิ๊กไบค์', 'Big bikes'), A.big ? say('big', A.big, lot) : L('ยังไม่มีใครบอก', 'Nobody has said yet'), A.big],
    [L('มีหลังคาไหม', 'Covered?'), say('cov', A.cov, lot) || L('ไม่รู้', 'Not known'), A.cov],
    [L('เปิด ๒๔ ชม.ไหม', 'Open 24 hours?'), A.h24 && A.h24.v ? say('h24', A.h24, lot) : (A.hours ? say('hours', A.hours, lot) : L('ไม่รู้', 'Not known')), A.h24 && A.h24.v ? A.h24 : A.hours],
    [L('เสียเงินไหม', 'Fee?'), say('fee', A.fee, lot) || L('ไม่รู้', 'Not known'), A.fee],
    [L('ล็อกล้อ/ใบสั่ง', 'Are bikes fined?'), A.fined ? say('fined', A.fined, lot) : L('ไม่มีรายงาน', 'No reports'), A.fined],
    [L('นอกถนนไหม', 'Off-street?'), say('off', A.off, lot) || L('ไม่รู้', 'Not known'), A.off],
    [L('จอดกันเองไหม', 'Guerrilla?'), lot.gue ? say('gue', A.gue, lot) + (lot.bikes ? L(' (เห็น ' + lot.bikes + ' คัน)', ' (' + lot.bikes + ' bikes seen)') : '') : L('ไม่ใช่ที่เราเห็น', 'Not one we saw'), A.gue]
  ];
  if (A.att) rows.push([L('คนดูแล', 'Attendant'), say('att', A.att, lot), A.att]);
  if (A.cap) rows.push([L('จุได้', 'Spaces'), say('cap', A.cap, lot), A.cap]);
  if (A.acc) rows.push([L('ใครจอดได้', 'Who may park'), say('acc', A.acc, lot), A.acc]);
  if (lot.beside) rows.push([L('อยู่ข้าง', 'Beside'), esc(lot.beside), {b: 's'}]);

  var near = [];
  LOTS.forEach(function (o) {
    if (o.id === lot.id) return;
    var d = metres(lot.la, lot.ln, o.la, o.ln);
    if (d > 700) return;
    var oA = answers(o);
    if (!fits(o, oA)) return;
    near.push({o: o, d: d, A: oA});
  });
  near.sort(function (a, b) { return a.d - b.d; });
  var c = CLS[lot.c];
  var dist = here ? fmtD(metres(here.lat, here.lng, lot.la, lot.ln)) + ' ' + dir8(bearing(here.lat, here.lng, lot.la, lot.ln)) + L(' จากคุณ', ' from you') : '';
  var tell = ['full', 'space', 'fined', 'free', 'paid', 'covered', 'open24', 'bigbike', 'nobigbike', 'gone'];
  $('#lotbody').innerHTML = '<div class="in"><button class="x" id="lotx" type="button" aria-label="close">' + icon('i-x') + '</button>' +
    '<h2>' + esc(lotName(lot)) + '</h2>' +
    '<div class="pk-dir">' + esc([dist, landmarkLine(lot.la, lot.ln)].filter(Boolean).join(' · ')) + (lot.approx ? L(' · ตำแหน่งโดยประมาณ', ' · position approximate') : '') + '</div>' +
    (c ? '<p class="pk-dir">' + esc(L(c.line_th, c.line_en)) + '</p>' : '') +
    '<table class="pk-qa">' + rows.map(function (r) {
      return '<tr><td>' + esc(r[0]) + '</td><td>' + esc(r[1] || '') + (r[2] ? '<span class="b">' + esc(basis(r[2], lot)) + '</span>' : '') + '</td></tr>';
    }).join('') + '</table>' +
    '<div class="pk-row-btns"><button type="button" class="pk-gold" id="lotpark">' + icon('i-pin') + L('จอดตรงนี้', 'I parked here') + '</button>' +
    '<a class="pk-btn" href="https://www.google.com/maps/dir/?api=1&destination=' + lot.la + ',' + lot.ln + '&travelmode=' + (VEH === 'c' ? 'driving' : 'two-wheeler') + '" target="_blank" rel="noopener">' + icon('i-route') + L('นำทาง', 'Directions') + '</a></div>' +
    '<h3>' + L('บอกคนอื่น', 'Tell the next person') + '</h3><div class="pk-tell">' + tell.map(function (k) {
      var w = MODEL.reports[k]; return '<button type="button" data-tell="' + k + '">' + esc(L(w.th, w.en)) + '</button>';
    }).join('') + '</div>' +
    '<h3>' + L('ที่จอดอื่นใกล้ ๆ', 'Other parking nearby') + '</h3>' +
    (near.length ? '<ul class="pk-nearby">' + near.slice(0, 6).map(function (x) {
      return '<li data-id="' + esc(x.o.id) + '"><span class="dot ' + state(x.A) + '"></span><span>' + esc(lotName(x.o)) +
        '<br><small class="pk-dir">' + fmtD(x.d) + ' ' + dir8(bearing(lot.la, lot.ln, x.o.la, x.o.ln)) + (x.A.now ? ' · ' + esc(say('now', x.A.now, x.o)) : '') + '</small></span></li>';
    }).join('') + '</ul>' : '<p class="pk-dir">' + L('ไม่มีในข้อมูลภายใน 700 ม.', 'None in the data within 700 m.') + '</p>') + '</div>';
  $('#lotx').onclick = function () { $('#lot').close(); };
  $('#lotpark').onclick = function () { parkAt(lot.la, lot.ln, 10, lot.id); $('#lot').close(); };
  [].forEach.call(document.querySelectorAll('[data-tell]'), function (b) {
    b.onclick = function () { report(lot, b.getAttribute('data-tell'), b); };
  });
  [].forEach.call(document.querySelectorAll('.pk-nearby li'), function (li) {
    li.onclick = function () { var o = LOTS.get(li.getAttribute('data-id')); if (o) { centreMap(o.la, o.ln); openLot(o.id); } };
  });
}
function usualLine(lot, hist) {
  var full = hist.filter(function (r) { return r.answer === 'full'; });
  var parts = [];
  if (full.length >= 2) {
    var byH = {};
    full.forEach(function (r) { var h = new Date(r.at).getHours(); byH[h] = (byH[h] || 0) + 1; });
    var top = Object.keys(byH).sort(function (a, b) { return byH[b] - byH[a]; })[0];
    parts.push(L('มีคนบอกว่าเต็มบ่อยสุดช่วง ' + top + ':00 (' + full.length + ' ครั้ง)', 'Reported full most often around ' + top + ':00 (' + full.length + ' reports)'));
  }
  var u = usualText(lot);
  if (u.length) parts.push(L('มักแน่น ', 'Usually busy ') + u.join(' · '));
  return parts.join('. ') || L('ยังไม่รู้ — ยิ่งมีคนกด "เต็ม" "ยังมีที่" ยิ่งรู้', 'Not known yet — it learns from Full and Space taps');
}
function report(lot, answer, btn) {
  fetch(WORKER, {method: 'POST', headers: {'content-type': 'application/json'},
    body: JSON.stringify({placeId: lot.id, answer: answer, vehicle: VEH === 'c' ? 'c' : 'm'})})
    .then(function (r) { return r.json(); }).then(function (j) {
      if (!j.ok) return;
      if (!NOW.has(lot.id)) NOW.set(lot.id, []);
      NOW.get(lot.id).unshift(j);
      btn.classList.add('done'); buzz(20);
      paintLot(lot); render();
    }).catch(function () {});
}

/* ------------------------------------------------------- your parking */
function getPark() {
  var p = null;
  if (APP) { try { p = JSON.parse(APP.parkState() || 'null'); } catch (e) {} }
  else p = store('md-park');
  if (!p || p.left || p.lat == null) return null;
  var extra = store('md-park-extra') || {};
  if (extra.t === p.t) { p.note = p.note || extra.note; p.level = p.level || extra.level; }
  return p;
}
function history() {
  var h = null;
  if (APP && APP.parkHistory) { try { h = JSON.parse(APP.parkHistory() || '[]'); } catch (e) {} }
  return h || store('md-park-hist') || [];
}
function parkAt(la, ln, acc, lotId) {
  var p = {lat: la, lng: ln, acc: Math.round(acc || 0), t: Date.now(), how: 'told', vehicle: VEH === 'c' ? 'car' : 'bike', note: '', level: '', lot: lotId || '', left: 0};
  if (APP) { try { APP.parkHere(String(la), String(ln), String(p.acc), p.vehicle, ''); } catch (e) {} }
  else {
    var h = store('md-park-hist') || [], old = store('md-park');
    if (old && !old.left) { old.left = Date.now(); h.unshift(old); }
    store('md-park-hist', h.slice(0, 40));
    store('md-park', p);
  }
  store('md-park-photo', null);
  buzz([30, 40, 30]);
  paintMine(); placeMarkers();
  document.getElementById('mine').scrollIntoView({behavior: 'smooth'});
}
function clearPark() {
  if (APP) { try { APP.parkClear(); } catch (e) {} }
  else {
    var p = store('md-park');
    if (p) { p.left = Date.now(); var h = store('md-park-hist') || []; h.unshift(p); store('md-park-hist', h.slice(0, 40)); store('md-park', null); }
  }
  paintMine(); placeMarkers(); paintHist();
}
function saveExtra(p, note, level) {
  store('md-park-extra', {t: p.t, note: note, level: level});
  if (APP && APP.parkNote) { try { APP.parkNote(note, level); } catch (e) {} }
}
function lotFor(p) {
  if (p.lot && LOTS.get(p.lot)) return LOTS.get(p.lot);
  var best = null;
  LOTS.forEach(function (o) { var d = metres(p.lat, p.lng, o.la, o.ln); if (d < 45 && (!best || d < best.d)) best = {d: d, o: o}; });
  return best && best.o;
}
function closeAt(lot) {
  if (!lot) return null;
  var A = answers(lot);
  if (A.h24 && A.h24.v) return null;
  var h = A.hours && String(A.hours.v).match(/(\d{1,2}):(\d\d)\s*-\s*(\d{1,2}):(\d\d)/);
  if (!h) return null;
  var d = new Date(); d.setHours(+h[3], +h[4], 0, 0);
  if (+h[3] < +h[1]) d.setDate(d.getDate() + 1);
  return {t: d.getTime(), basis: A.hours.b};
}
function paintMine() {
  var box = $('#mine'), p = getPark();
  if (!p) {
    box.innerHTML = '<div class="pk-card"><button type="button" class="pk-big" id="parknow">' + icon('i-pin') + L('จอดตรงนี้', 'I parked here') + '</button>' +
      autoLine() + '</div>';
    $('#parknow').onclick = parkHereNow;
    wireAuto();
    return;
  }
  var lot = lotFor(p), close = closeAt(lot), shot = store('md-park-photo');
  var where = [lot ? lotName(lot) : '', landmarkLine(p.lat, p.lng)].filter(Boolean).join(' · ');
  var dme = here ? metres(here.lat, here.lng, p.lat, p.lng) : null;
  var away = dme == null ? '' : dme < 15 ? L('อยู่ตรงนี้', 'Right here') :
    fmtD(dme) + ' ' + dir8(bearing(here.lat, here.lng, p.lat, p.lng)) + L(' จากคุณ', ' from you');
  var warn = '';
  if (close) {
    var left = close.t - Date.now();
    if (left < 3 * 3600000) warn = '<div class="warn">' + L('ที่จอดนี้ปิด ', 'This parking closes at ') + hhmm(close.t) +
      (close.basis === 'u' ? L(' (ปกติ)', ' (usually)') : '') + (left > 0 ? ' — ' + L('อีก ', '') + Math.floor(left / 3600000) + L(' ชม. ', ' h ') + Math.round(left % 3600000 / 60000) + L(' นาที', ' min left') : '') + '</div>';
    remindClose(p, close);
  }
  var lv = ['B3', 'B2', 'B1', 'G', '1', '2', '3', '4', '5', '6', '7', '8'];
  box.innerHTML = '<div class="pk-card has">' +
    '<h2>' + icon(p.vehicle === 'car' ? 'i-ride' : 'i-scooter') + (p.vehicle === 'car' ? L('รถของคุณ', 'Your car') : L('รถของคุณ', 'Your bike')) + '</h2>' +
    '<div class="when">' + L('จอดเมื่อ ', 'Parked ') + hhmm(p.t) + ' · ' + ago(p.t) +
    (p.how === 'guessed' ? L(' · มดแดงเดาจากการขี่ของคุณ', ' · Mot Dang guessed it from your ride') : '') + '</div>' +
    (where ? '<div class="where">' + esc(where) + '</div>' : '') +
    (away ? '<div class="when">' + esc(away) + '</div>' : '') + warn +
    (p.level || p.note ? '<div class="note">' + (p.level ? L('ชั้น ', 'Level ') + esc(p.level) + (p.note ? ' · ' : '') : '') + esc(p.note || '') + '</div>' : '') +
    (shot && shot.t === p.t ? '<img class="shot" src="' + shot.data + '" alt="">' : '') +
    '<button type="button" class="pk-big" id="walkback">' + icon('i-walk') + L('พาไปที่รถ', 'Walk me back') + '</button>' +
    '<div class="pk-row-btns">' +
    '<button type="button" id="mphoto">' + icon('i-camera') + L('ถ่ายรูปที่จอด', 'Photo of the spot') + '</button>' +
    '<button type="button" id="mnote">' + icon('i-note') + L('ชั้น / จดไว้', 'Level / note') + '</button>' +
    '<button type="button" id="mfound">' + icon('i-check') + L('เอารถแล้ว', 'Got it') + '</button>' +
    (p.how === 'guessed' && APP ? '<button type="button" id="mnot">' + icon('i-x') + L('ไม่ใช่รถฉัน', 'Not mine') + '</button>' : '') +
    '</div>' +
    '<div id="notebox" hidden><div class="pk-levels">' + lv.map(function (x) {
      return '<button type="button" data-lv="' + x + '" aria-pressed="' + (p.level === x) + '">' + x + '</button>'; }).join('') + '</div>' +
    '<textarea id="notetext" placeholder="' + L('เสา C7 · ข้างประตูสีเขียว', 'Pillar C7 · by the green door') + '">' + esc(p.note || '') + '</textarea>' +
    '<button type="button" class="pk-btn pk-gold" id="notesave">' + L('บันทึก', 'Save') + '</button></div>' +
    autoLine() + '</div>';
  $('#walkback').onclick = function () { openBack(); };
  $('#mphoto').onclick = function () { $('#photo').click(); };
  $('#mnote').onclick = function () { var b = $('#notebox'); b.hidden = !b.hidden; };
  $('#mfound').onclick = clearPark;
  if ($('#mnot')) $('#mnot').onclick = function () { try { APP.parkNotMine(); } catch (e) {} paintMine(); placeMarkers(); };
  var level = p.level || '';
  [].forEach.call(box.querySelectorAll('[data-lv]'), function (b) {
    b.onclick = function () {
      level = level === b.getAttribute('data-lv') ? '' : b.getAttribute('data-lv');
      [].forEach.call(box.querySelectorAll('[data-lv]'), function (x) { x.setAttribute('aria-pressed', String(x.getAttribute('data-lv') === level)); });
    };
  });
  $('#notesave').onclick = function () { saveExtra(p, $('#notetext').value.trim().slice(0, 200), level); paintMine(); };
  wireAuto();
}
function remindClose(p, close) {
  if (!APP || !APP.parkRemind) return;
  var key = 'md-park-rem-' + p.t, at = close.t - 30 * 60000;
  if (store(key) || at < Date.now()) return;
  try { APP.parkRemind(String(at), L('ที่จอดรถปิด ' + hhmm(close.t) + ' — รถคุณยังอยู่ข้างใน', 'Your parking closes at ' + hhmm(close.t) + ' — your bike is still there')); store(key, 1); } catch (e) {}
}
function parkHereNow() {
  var btn = $('#parknow');
  btn.disabled = true; btn.lastChild.textContent = L('กำลังหาตำแหน่ง…', 'Finding where you are…');
  bestFix(12000).then(function (f) { parkAt(f.lat, f.lng, f.acc); }).catch(function () {
    btn.disabled = false; btn.lastChild.textContent = L('หาตำแหน่งไม่ได้ — กดอีกครั้ง', 'No location — tap again');
  });
}
function bestFix(ms) {
  return new Promise(function (ok, no) {
    if (!navigator.geolocation) return no();
    var best = null, id, done = function () { navigator.geolocation.clearWatch(id); best ? ok(best) : no(); };
    id = navigator.geolocation.watchPosition(function (p) {
      var f = {lat: p.coords.latitude, lng: p.coords.longitude, acc: p.coords.accuracy};
      if (!best || f.acc < best.acc) best = f;
      if (f.acc <= 15) done();
    }, function () { done(); }, {enableHighAccuracy: true, maximumAge: 0, timeout: ms});
    setTimeout(done, ms);
  });
}
var STEP_SAY = {
  location: ['ให้มดแดงรู้ตำแหน่งของคุณ', 'Let Mot Dang see your location.'],
  background: ['เลือก "อนุญาตตลอดเวลา" เพื่อจำที่จอดตอนปิดจอ', 'Choose "Allow all the time" so it notices parking with the screen off.'],
  activity: ['อนุญาต "การเคลื่อนไหวร่างกาย" เพื่อรู้ว่าคุณเริ่มเดินแล้ว', 'Allow "Physical activity" so it can tell when you start walking.'],
  notifications: ['อนุญาตการแจ้งเตือน เพื่อให้มดแดงบอกว่าจอดไว้ตรงไหน', 'Allow notifications so it can tell you where you parked.'],
  battery: ['ปิดการประหยัดแบตให้มดแดง ไม่งั้นโทรศัพท์จะหยุดมัน', 'Turn off battery saving for Mot Dang, or the phone stops it.'],
  vivo: ['ในหน้าถัดไป เปิด "เริ่มอัตโนมัติ" / "ทำงานเบื้องหลัง" ให้มดแดง', 'On the next screen, switch on Autostart / background running for Mot Dang.']
};
function autoLine() {
  if (!APP || !APP.parkWatchState) {
    return '<div class="pk-auto">' + L('ในแอป Android มดแดงรู้เองว่าคุณจอดตรงไหน ตอนลงจากรถแล้วเริ่มเดิน', 'In the Android app, Mot Dang notices where you parked when you get off and start walking.') +
      ' <a href="' + APK + '">' + L('โหลดแอป', 'Get the app') + '</a></div>';
  }
  var s = '', next = '';
  try { s = APP.parkWatchState(); } catch (e) {}
  if (s === 'off') return '<div class="pk-auto"><button type="button" class="pk-btn pk-gold" id="autoon">' + L('ให้จำที่จอดเองทุกครั้ง', 'Notice when I park') + '</button></div>';
  try { next = APP.parkSetupNext ? APP.parkSetupNext() : s.replace('needs-', ''); } catch (e) {}
  if (s === 'on' && (!next || next === 'done' || store('md-park-setup-' + next)))
    return '<div class="pk-auto">' + icon('i-check') + '<b>' + L('จำที่จอดให้อัตโนมัติ: เปิด', 'Noticing when you park: on') + '</b> <button type="button" class="pk-btn" id="autooff">' + L('ปิด', 'Turn off') + '</button></div>';
  var w = STEP_SAY[next] || STEP_SAY[s.replace('needs-', '')] || ['', ''];
  return '<div class="pk-auto">' + L(w[0], w[1]) + ' <button type="button" class="pk-btn pk-gold" id="autostep" data-step="' + esc(next) + '">' + L('ตั้งค่า', 'Set it') + '</button>' +
    (s === 'on' ? ' <button type="button" class="pk-btn" id="autoskip" data-step="' + esc(next) + '">' + L('ข้าม', 'Skip') + '</button>' : '') + '</div>';
}
function wireAuto() {
  var on = $('#autoon'), off = $('#autooff'), st = $('#autostep');
  if (on) on.onclick = function () { try { APP.parkWatch('1'); var s = APP.parkWatchState(); if (s !== 'on') APP.parkSetup(); } catch (e) {} setTimeout(paintMine, 800); };
  if (off) off.onclick = function () { try { APP.parkWatch('0'); } catch (e) {} paintMine(); };
  if (st) st.onclick = function () { try { APP.parkSetup(); } catch (e) {} setTimeout(paintMine, 1500); };
  var sk = $('#autoskip');
  if (sk) sk.onclick = function () { store('md-park-setup-' + sk.getAttribute('data-step'), 1); paintMine(); };
}
function paintHist() {
  if (!$('#hist')) return;
  var h = history().filter(function (x) { return x && x.lat != null; }).slice(0, 12);
  $('#hist').hidden = !h.length;
  $('#histlist').innerHTML = h.map(function (x, i) {
    var d = new Date(x.t), dur = x.left ? Math.round((x.left - x.t) / 60000) : 0;
    return '<li data-i="' + i + '">' + L(DAYS[d.getDay()][0], DAYS[d.getDay()][1]) + ' ' + d.getDate() + '/' + (d.getMonth() + 1) + ' ' + hhmm(x.t) +
      ' · ' + esc(landmarkLine(x.lat, x.lng) || (x.lat.toFixed(4) + ', ' + x.lng.toFixed(4))) +
      (dur ? ' · ' + (dur < 90 ? dur + L(' นาที', ' min') : Math.round(dur / 60) + L(' ชม.', ' h')) : '') +
      (x.how === 'guessed' ? L(' · เดา', ' · guessed') : '') + '</li>';
  }).join('');
  [].forEach.call(document.querySelectorAll('#histlist li'), function (li) {
    li.onclick = function () { var x = h[+li.getAttribute('data-i')]; centreMap(x.lat, x.lng, 17); window.scrollTo({top: 0, behavior: 'smooth'}); };
  });
}
$('#photo').addEventListener('change', function (e) {
  var f = e.target.files && e.target.files[0], p = getPark();
  if (!f || !p) return;
  var img = new Image(), url = URL.createObjectURL(f);
  img.onload = function () {
    var s = Math.min(1, 900 / Math.max(img.width, img.height)), c = document.createElement('canvas');
    c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    URL.revokeObjectURL(url);
    store('md-park-photo', {t: p.t, data: c.toDataURL('image/jpeg', 0.72)});
    paintMine();
  };
  img.src = url;
});

/* ------------------------------------------------------- walk me back
   One arrow that points the way relative to where the phone faces, the
   distance in metres and steps, a buzz when you face the right way, and the
   words "turn left" rather than a map. With a trail from the app, it leads
   back the way you came instead of in a straight line through buildings. */
var B = {on: false, watch: null, heading: null, headT: 0, course: null, prev: null, ptr: -1, lastBuzz: 0, lock: null, best: Infinity, mark: null};
function openBack(dest) {
  var p = dest || getPark();
  if (!p || B.on) return;
  B.bike = !dest;
  B.on = true; B.p = p; B.best = Infinity; B.ptr = -1; B.mark = null;
  $('#bfound').textContent = B.bike ? L('เจอแล้ว', 'Found it') : L('ถึงแล้ว', "I'm here");
  var trail = B.bike ? (p.trail || []).filter(function (x) { return x && x.length >= 2; }) : [];
  B.trail = trail;
  $('#back').hidden = false; $('#back').classList.remove('arrived');
  $('#bsay').textContent = L('กำลังหาตำแหน่ง…', 'Finding where you are…');
  $('#bdist').textContent = ''; $('#bsteps').textContent = ''; $('#bhint').textContent = '';
  $('#blook').innerHTML = B.bike ? lookHtml(p) : esc(p.label || '');
  try { navigator.wakeLock && navigator.wakeLock.request('screen').then(function (l) { B.lock = l; }); } catch (e) {}
  if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission === 'function') $('#bcompass').hidden = false;
  window.addEventListener('deviceorientationabsolute', onOrient, true);
  window.addEventListener('deviceorientation', onOrient, true);
  if (navigator.geolocation) B.watch = navigator.geolocation.watchPosition(onBackFix, function () {
    $('#bsay').textContent = L('เปิดตำแหน่งก่อน', 'Turn on location first');
  }, {enableHighAccuracy: true, maximumAge: 1000, timeout: 20000});
  if (B.bike && location.hash !== '#back') history_replace('#back');
}
function closeBack() {
  B.on = false;
  if (B.watch != null) navigator.geolocation.clearWatch(B.watch);
  window.removeEventListener('deviceorientationabsolute', onOrient, true);
  window.removeEventListener('deviceorientation', onOrient, true);
  try { B.lock && B.lock.release(); } catch (e) {}
  $('#back').hidden = true;
  if (location.hash === '#back') history_replace('#mine');
}
function history_replace(h) { try { window.history.replaceState(null, '', h); } catch (e) {} }
function lookHtml(p) {
  var shot = store('md-park-photo'), bits = [];
  if (p.level) bits.push('<b>' + L('ชั้น ', 'Level ') + esc(p.level) + '</b>');
  if (p.note) bits.push(esc(p.note));
  var lot = lotFor(p);
  if (lot && lot.beside) bits.push(L('ข้าง ', 'Beside ') + esc(lot.beside));
  return bits.join(' · ') + (shot && shot.t === p.t ? '<img src="' + shot.data + '" alt="">' : '');
}
function onOrient(e) {
  var h = null;
  if (typeof e.webkitCompassHeading === 'number') h = e.webkitCompassHeading;
  else if (e.absolute && typeof e.alpha === 'number') h = 360 - e.alpha;
  if (h == null) return;
  var ang = (screen.orientation && screen.orientation.angle) || window.orientation || 0;
  B.heading = (h + ang + 360) % 360; B.headT = Date.now();
  if (B.fix) paintBack();
}
function onBackFix(pos) {
  var f = {lat: pos.coords.latitude, lng: pos.coords.longitude, acc: pos.coords.accuracy, t: Date.now()};
  if (B.prev && metres(B.prev.lat, B.prev.lng, f.lat, f.lng) > 5)
    B.course = bearing(B.prev.lat, B.prev.lng, f.lat, f.lng);
  if (!B.prev || metres(B.prev.lat, B.prev.lng, f.lat, f.lng) > 5) B.prev = f;
  B.fix = f; here = {lat: f.lat, lng: f.lng, acc: f.acc};
  paintBack();
}
function target() {
  var p = B.p, f = B.fix, tr = B.trail;
  if (!tr.length || metres(f.lat, f.lng, p.lat, p.lng) < 40) return {lat: p.lat, lng: p.lng, bike: true};
  if (B.ptr < 0) {
    var bi = 0, bd = Infinity;
    tr.forEach(function (x, i) { var d = metres(f.lat, f.lng, x[0], x[1]); if (d < bd) { bd = d; bi = i; } });
    B.ptr = bi;
  }
  while (B.ptr >= 0 && metres(f.lat, f.lng, tr[B.ptr][0], tr[B.ptr][1]) < 14) B.ptr--;
  if (B.ptr < 0) return {lat: p.lat, lng: p.lng, bike: true};
  return {lat: tr[B.ptr][0], lng: tr[B.ptr][1], step: tr.length - B.ptr, of: tr.length};
}
function paintBack() {
  if (!B.on || !B.fix) return;
  var p = B.p, f = B.fix, d = metres(f.lat, f.lng, p.lat, p.lng), t = target();
  var brg = bearing(f.lat, f.lng, t.lat, t.lng);
  var head = (Date.now() - B.headT < 3000) ? B.heading : B.course;
  var arrow = $('#barrow'), g = $('#barrowg');
  $('#bdist').textContent = fmtD(d);
  $('#bsteps').textContent = L('ประมาณ ' + Math.round(d / 0.75) + ' ก้าว · ' + Math.max(1, Math.round(d / 80)) + ' นาที',
    'about ' + Math.round(d / 0.75) + ' steps · ' + Math.max(1, Math.round(d / 80)) + ' min');
  if (d <= Math.max(12, Math.min(f.acc, 30) * 0.8)) {
    if (!$('#back').classList.contains('arrived')) buzz([80, 60, 80, 60, 220]);
    $('#back').classList.add('arrived');
    arrow.classList.add('near'); g.setAttribute('transform', 'rotate(0)');
    $('#bsay').textContent = B.bike ? L('ถึงแล้ว! รถอยู่แถวนี้', "You're there. It's right around here.") : L('ถึงแล้ว', "You're there.");
    $('#bhint').textContent = B.bike && p.level ? L('ชั้น ' + p.level, 'Level ' + p.level) : L('มองรอบ ๆ ตัว', 'Look around you.');
    return;
  }
  $('#back').classList.remove('arrived'); arrow.classList.remove('near');
  var hint = [];
  if (head == null) {
    g.setAttribute('transform', 'rotate(' + brg.toFixed(0) + ')');
    $('#bsay').textContent = L('ไป', 'Go ') + dir8(brg);
    hint.push(L('เดินสักสองสามก้าว แล้วลูกศรจะหันตามคุณ', 'Walk a few steps and the arrow turns with you.'));
  } else {
    var rel = (brg - head + 540) % 360 - 180, a = Math.abs(rel);
    g.setAttribute('transform', 'rotate(' + rel.toFixed(0) + ')');
    var side = rel < 0 ? L('ซ้าย', 'left') : L('ขวา', 'right');
    var words = a < 20 ? L('ตรงไป', 'Straight ahead') : a < 60 ? L('เยื้องไปทาง' + side, 'Bear ' + side) :
      a < 135 ? L('เลี้ยว' + side, 'Turn ' + side) : L('กลับหลังหัน', 'Turn around');
    var clock = Math.round(((rel + 360) % 360) / 30) % 12 || 12;
    $('#bsay').textContent = words;
    if (a >= 20) hint.push(L('ทาง ' + clock + ' นาฬิกา', 'at ' + clock + " o'clock"));
    arrow.classList.toggle('on', a < 20);
    if (a < 20 && Date.now() - B.lastBuzz > 2500) { buzz(25); B.lastBuzz = Date.now(); }
  }
  if (t.step) hint.push(L('ย้อนทางที่เดินมา (' + t.step + '/' + t.of + ')', 'back the way you came (' + t.step + '/' + t.of + ')'));
  if (!B.mark || Date.now() - B.mark.t > 12000) {
    if (B.mark) {
      if (d < B.mark.d - 6) hint.push(L('ใกล้ขึ้นแล้ว', 'Getting closer'));
      else if (d > B.mark.d + 8) hint.push(L('ไกลออกไป — หันกลับ', 'Getting further — turn back'));
    }
    B.mark = {t: Date.now(), d: d};
  }
  if (f.acc > 40) hint.push(L('GPS อ่อน (±' + Math.round(f.acc) + ' ม.) ออกมาที่โล่ง', 'Weak GPS (±' + Math.round(f.acc) + ' m): step out from under the roof'));
  $('#bhint').textContent = hint.join(' · ');
}
$('#backx').onclick = closeBack;
$('#bfound').onclick = function () { var bike = B.bike; closeBack(); if (bike) clearPark(); };
$('#bcompass').onclick = function () {
  DeviceOrientationEvent.requestPermission().then(function () { $('#bcompass').hidden = true; }).catch(function () {});
};
$('#barrow').addEventListener('click', function () {
  var a = $('#barrow'); a.classList.remove('wiggle'); void a.offsetWidth; a.classList.add('wiggle'); buzz(15);
});

/* ------------------------------------------------------------- wiring */
function setLang(l) {
  LANG = l; store('md-lang', l);
  document.documentElement.lang = l;
  $('#lang').textContent = l === 'th' ? 'EN' : 'ไทย';
  [].forEach.call(document.querySelectorAll('[data-th]'), function (el) {
    var t = el.getAttribute('data-' + l); if (el.children.length === 0) el.textContent = t;
  });
  paintKerb(); paintMine(); paintHist(); render();
}
function paintKerb() {
  if (!$('#kerblist')) return;
  var col = {'red-white': ['#C62828', '#fff'], 'yellow-white': ['#F2C230', '#fff'], 'odd-even': ['#2B5C8A', '#fff'], 'clamp': ['#333', '#F2C230']};
  $('#kerblist').innerHTML = (MODEL ? MODEL.kerb : []).map(function (k) {
    var c = col[k.key] || ['#999', '#fff'];
    return '<li><span class="kerb" style="--a:' + c[0] + ';--b:' + c[1] + '"></span><span>' + esc(L(k.th, k.en)) + '</span></li>';
  }).join('');
}
$('#lang').onclick = function () { setLang(LANG === 'th' ? 'en' : 'th'); };
[].forEach.call(document.querySelectorAll('#veh button'), function (b) {
  b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === VEH));
  b.onclick = function () {
    VEH = b.getAttribute('data-v'); store('md-park-veh', VEH);
    [].forEach.call(document.querySelectorAll('#veh button'), function (x) { x.setAttribute('aria-pressed', String(x === b)); });
    SHOW = 25; render();
  };
});
[].forEach.call(document.querySelectorAll('#chips button'), function (b) {
  b.onclick = function () {
    var f = b.getAttribute('data-f');
    if (FILT.has(f)) FILT.delete(f); else FILT.add(f);
    b.setAttribute('aria-pressed', String(FILT.has(f)));
    SHOW = 25; render();
  };
});
if ($('#more')) $('#more').onclick = function () { SHOW += 25; render(); };
if ($('#list')) $('#list').addEventListener('click', function (e) {
  var li = e.target.closest('li[data-id]'); if (!li) return;
  var lot = LOTS.get(li.getAttribute('data-id')); if (!lot) return;
  centreMap(lot.la, lot.ln); openLot(lot.id);
});
$('#lot').addEventListener('click', function (e) { if (e.target === $('#lot')) $('#lot').close(); });

function locate(first) {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function (pos) {
    here = {lat: pos.coords.latitude, lng: pos.coords.longitude, acc: pos.coords.accuracy};
    from = {lat: here.lat, lng: here.lng}; fromIsMe = true;
    centreMap(here.lat, here.lng, 16);
    ensureTiles(here.lat, here.lng).then(function () { render(); paintMine(); placeMarkers(); });
  }, function () {}, {enableHighAccuracy: true, maximumAge: 30000, timeout: 15000});
}
if ($('#near')) $('#near').onclick = function () { locate(); };

function hashGo() {
  var h = location.hash;
  if (h === '#back' && getPark()) openBack();
  else if (h === '#photo' && getPark()) { document.getElementById('mine').scrollIntoView(); var b = $('#mphoto'); if (b) b.classList.add('pk-gold'); }
  else if (h === '#mine') document.getElementById('mine').scrollIntoView();
}
window.MDPark = {
  walkTo: function (la, ln, label) { openBack({lat: la, lng: ln, label: label}); },
  openLot: function (id) { openLot(id); },
  nearest: function (la, ln) {
    var best = null;
    LOTS.forEach(function (o) { var A = answers(o); if (!fits(o, A)) return;
      var d = metres(la, ln, o.la, o.ln); if (!best || d < best.d) best = {d: d, lot: o}; });
    return best;
  },
  here: function () { return here; },
  park: function () { return getPark(); },
  L: L, fmtD: fmtD, dir8: dir8, metres: metres, bearing: bearing, esc: esc, icon: icon,
  ensureTiles: function (la, ln) { return ensureTiles(la, ln); }
};
window.addEventListener('hashchange', hashGo);
document.addEventListener('visibilitychange', function () { if (!document.hidden) { paintMine(); placeMarkers(); fetchNow().then(render); } });

fetch(BASE + 'model.json').then(function (r) { return r.json(); }).then(function (m) {
  MODEL = m;
  m.classes.forEach(function (c) { CLS[c.key] = c; });
  var p = getPark(), start = p ? {lat: p.lat, lng: p.lng} : {lat: GATE.lat, lng: GATE.lng, name: L(GATE.th, GATE.en)};
  from = start;
  setLang(LANG);
  return Promise.all([ensureTiles(start.lat, start.lng), fetchNow()]);
}).then(function () {
  render(); paintMine(); paintHist();
  if (window.MDMAP) MDMAP.ready(mapEl, initMap);
  try {
    navigator.permissions && navigator.permissions.query({name: 'geolocation'}).then(function (s) { if (s.state === 'granted') locate(); });
  } catch (e) {}
  if (APP) locate();
  hashGo();
  setInterval(function () { fetchNow().then(render); }, 120000);
  setInterval(function () { if (!B.on) paintMine(); }, 60000);
});
})();
