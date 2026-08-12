/* มดแดง — ห้องน้ำใกล้ฉัน (Mot Dang: nearest toilet)
 *
 * The map is drawn HERE, from data baked into the app. No tile server, no
 * map library, no request leaves the phone to draw a street. The one network
 * call this app can make is a toilet report: place id + one word from a
 * closed vocabulary, nothing else, and only when you press the button.
 *
 * Sorting is by distance and NOTHING else — same rule as the site. A tier is
 * a HABIT ("places like this normally keep one"), never a claim about one
 * building; the wording we stand behind ships inside data/toilets.js and is
 * reused verbatim. A field report at a spot outranks its tier, toiletnone
 * included.
 *
 * Your own visit log lives in localStorage on this phone. It is never sent
 * anywhere, and the erase button really erases it.
 */
'use strict';

var B = window.BASEMAP, L = window.LANDMARKS, T = window.TOILETS,
    TC = window.TOILETS_CUSTOMERS;

var ORIGIN = B.origin, EXT = B.extent, Q = B.q;
var KX = Math.cos(((EXT[0] + EXT[2]) / 2) * Math.PI / 180);
var UNIT_M = 111320 / Q;              // metres per unit of y
function ux (lng) { return (lng - ORIGIN[1]) * Q * KX; }
function uy (lat) { return (lat - ORIGIN[0]) * Q; }

/* ---------- decode the packed basemap ---------- */
function decode (packed) {
  var n = packed.length / 2, pts = new Float32Array(n * 2);
  var x = 0, y = 0, minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
  for (var i = 0; i < n; i++) {
    x += packed[i * 2]; y += packed[i * 2 + 1];
    var mx = x * KX, my = y;
    pts[i * 2] = mx; pts[i * 2 + 1] = my;
    if (mx < minx) minx = mx; if (mx > maxx) maxx = mx;
    if (my < miny) miny = my; if (my > maxy) maxy = my;
  }
  return { p: pts, bb: [minx, miny, maxx, maxy] };
}
var ROADS = B.roads.map(function (r) {
  return { cls: r[0], th: r[1], en: r[2], g: decode(r[3]) };
});
var BUILDINGS = B.buildings.map(function (p) { return decode(p); });
var BNAMES = B.bnames.map(function (n) {
  return { x: n[0] * KX, y: n[1], th: n[2], en: n[3] };
});
var MOAT = (T.moat || []).map(function (c) { return [ux(c[1]), uy(c[0])]; });

/* ---------- assemble the pin lists ---------- */
// kind: 'mapped' (verified point) | 'tier' | 'customer'
var PINS = [];
T.verified.forEach(function (v, i) {
  PINS.push({ kind: 'mapped', lat: v[0], lng: v[1], th: v[2], en: v[3],
    fee: v[4], baht: v[5], hours: v[6], flags: v[7],
    x: ux(v[1]), y: uy(v[0]), key: 'v' + i });
});
var seenIds = {};
function addPlaces (rows, kind) {
  rows.forEach(function (p) {
    if (p[8] && seenIds[p[8]]) return; // same venue in both files — keep the first
    if (p[8]) seenIds[p[8]] = true;
    PINS.push({ kind: kind, tier: T.tiers[p[0]], lat: p[1], lng: p[2],
      th: p[3], en: p[4], href: p[5], hours: p[6], report: p[7], id: p[8],
      x: ux(p[2]), y: uy(p[1]), key: p[8] });
  });
}
addPlaces(T.places, 'tier');
addPlaces(TC.places, 'customer');
var REPORTS = T.reports;
var REP_BY_KEY = {};
REPORTS.forEach(function (r) { REP_BY_KEY[r.key] = r; });

/* ---------- local, private state ---------- */
function lsGet (k, fb) {
  try { return JSON.parse(localStorage.getItem(k)) || fb; }
  catch (e) { return fb; }
}
function lsSet (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
var myReports = lsGet('md_my_reports', {});   // id -> {report, t}
var myVisits = lsGet('md_visits', []);        // [{t, key, th, en}]
var pendingReports = lsGet('md_pending', []); // queued when offline

/* ---------- map state ---------- */
var canvas = document.getElementById('map');
var ctx = canvas.getContext('2d');
// EXT spans both cities, so its midpoint is farmland between them. Open on
// the first baked city instead and let locate() carry a reader in Chiang Rai
// to their own — a map that opens on empty fields reads as broken.
var HOME = (B.extents && B.extents.cm) || EXT;
var view = lsGet('md_view', null) || {
  cx: (ux(HOME[3]) + ux(HOME[1])) / 2,
  cy: (uy(HOME[0]) + uy(HOME[2])) / 2,
  scale: 0.11
};
var dpr = Math.min(window.devicePixelRatio || 1, 2.5);
var W = 0, H = 0, dirty = true;
var me = null;              // {x,y,lat,lng,acc} once located
var selected = null;
var watching = false;

function resize () {
  W = canvas.clientWidth; H = canvas.clientHeight;
  canvas.width = W * dpr; canvas.height = H * dpr;
  dirty = true;
}
window.addEventListener('resize', resize);

function sx (x) { return (x - view.cx) * view.scale + W / 2; }
function sy (y) { return H / 2 - (y - view.cy) * view.scale; }
function invx (px) { return (px - W / 2) / view.scale + view.cx; }
function invy (py) { return (H / 2 - py) / view.scale + view.cy; }

function clampView () {
  view.scale = Math.max(0.004, Math.min(6, view.scale));
  var m = 3000; // units of slack beyond the baked extent
  var minx = ux(EXT[1]) - m, maxx = ux(EXT[3]) + m;
  var miny = uy(EXT[0]) - m, maxy = uy(EXT[2]) + m;
  if (me) { // never fence the reader away from where they stand
    minx = Math.min(minx, me.x - 500); maxx = Math.max(maxx, me.x + 500);
    miny = Math.min(miny, me.y - 500); maxy = Math.max(maxy, me.y + 500);
  }
  view.cx = Math.max(minx, Math.min(maxx, view.cx));
  view.cy = Math.max(miny, Math.min(maxy, view.cy));
}

/* ---------- drawing ---------- */
var ROAD_STYLE = {
  major: { w: 5.5, c: '#fffdf7', edge: '#d9c9a8', minS: 0 },
  minor: { w: 3.5, c: '#fffdf7', edge: '#e3d5bc', minS: 0.05 },
  lane:  { w: 2.0, c: '#f8f0dd', edge: null, minS: 0.22 },
  foot:  { w: 1.3, c: '#c9b074', edge: null, minS: 0.35, dash: true }
};
var TIER_MINS = 0.05;        // tier pins appear
var CUST_MINS = 0.4;         // customer-only venues appear
var BLDG_MINS = 0.3;         // buildings appear
var labelBoxes = [];

function labelFits (x, y, w, h) {
  for (var i = 0; i < labelBoxes.length; i++) {
    var b = labelBoxes[i];
    if (x < b[0] + b[2] && x + w > b[0] && y < b[1] + b[3] && y + h > b[1]) return false;
  }
  labelBoxes.push([x, y, w, h]);
  return true;
}
function visible (bb, pad) {
  return sx(bb[0]) < W + pad && sx(bb[2]) > -pad &&
         sy(bb[1]) > -pad && sy(bb[3]) < H + pad;
}

function draw () {
  if (!dirty) return;
  dirty = false;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#f2ead9';
  ctx.fillRect(0, 0, W, H);
  labelBoxes = [];
  var s = view.scale;

  // buildings — the quiet mass of the city
  if (s >= BLDG_MINS) {
    ctx.fillStyle = '#e7dcc4';
    ctx.strokeStyle = '#d5c5a2';
    ctx.lineWidth = Math.min(1, s * 0.5);
    ctx.beginPath();
    for (var i = 0; i < BUILDINGS.length; i++) {
      var b = BUILDINGS[i];
      if (!visible(b.bb, 20)) continue;
      var p = b.p;
      ctx.moveTo(sx(p[0]), sy(p[1]));
      for (var j = 2; j < p.length; j += 2) ctx.lineTo(sx(p[j]), sy(p[j + 1]));
      ctx.closePath();
    }
    ctx.fill();
    if (s > 0.5) ctx.stroke();
  }

  // the moat — four corners, drawn as water
  if (MOAT.length === 4) {
    ctx.strokeStyle = '#a8c8d8';
    ctx.lineWidth = Math.max(2, 20 * s);
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(sx(MOAT[0][0]), sy(MOAT[0][1]));
    for (var k = 1; k < 4; k++) ctx.lineTo(sx(MOAT[k][0]), sy(MOAT[k][1]));
    ctx.closePath();
    ctx.stroke();
  }

  // roads, casings first so joins knit
  var order = ['foot', 'lane', 'minor', 'major'];
  order.forEach(function (clsName) {
    var st = ROAD_STYLE[clsName];
    if (s < st.minS) return;
    var idx = B.roadClasses.indexOf(clsName);
    if (st.edge) strokeRoads(idx, Math.max(1.5, st.w * s * 2.4) + 2, st.edge, false);
    strokeRoads(idx, Math.max(1, st.w * s * 2.4), st.c, st.dash);
  });
  function strokeRoads (cls, wpx, color, dash) {
    ctx.strokeStyle = color;
    ctx.lineWidth = wpx;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.setLineDash(dash ? [wpx * 2.5, wpx * 2.5] : []);
    ctx.beginPath();
    for (var i = 0; i < ROADS.length; i++) {
      var r = ROADS[i];
      if (r.cls !== cls || !visible(r.g.bb, 30)) continue;
      var p = r.g.p;
      ctx.moveTo(sx(p[0]), sy(p[1]));
      for (var j = 2; j < p.length; j += 2) ctx.lineTo(sx(p[j]), sy(p[j + 1]));
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // road names — majors and minors once close enough
  if (s >= 0.45) {
    ctx.font = '11.5px Prompt, sans-serif';
    ctx.fillStyle = '#8a755b';
    ctx.textAlign = 'center';
    var namesDrawn = {};
    for (var ri = 0; ri < ROADS.length; ri++) {
      var rd = ROADS[ri];
      if (rd.cls > 1 || !rd.th || !visible(rd.g.bb, 0)) continue;
      if (namesDrawn[rd.th]) continue;
      namesDrawn[rd.th] = true;
      var mp = rd.g.p, mi = (mp.length >> 2) << 1;
      var lx = sx(mp[mi]), ly = sy(mp[mi + 1]);
      var tw = ctx.measureText(rd.th).width;
      if (labelFits(lx - tw / 2, ly - 12, tw, 14)) ctx.fillText(rd.th, lx, ly - 3);
    }
  }

  // building names, faint, at close zoom
  if (s >= 0.75) {
    ctx.font = '10.5px Prompt, sans-serif';
    ctx.fillStyle = '#a08b6c';
    ctx.textAlign = 'center';
    for (var bi = 0; bi < BNAMES.length; bi++) {
      var bn = BNAMES[bi];
      var bx = sx(bn.x), by = sy(bn.y);
      if (bx < -60 || bx > W + 60 || by < -20 || by > H + 20) continue;
      var bw = ctx.measureText(bn.th).width;
      if (labelFits(bx - bw / 2, by - 6, bw, 12)) ctx.fillText(bn.th, bx, by + 3);
    }
  }

  // landmarks — rich, but always beneath the toilets
  if (s >= 0.12) {
    for (var li = 0; li < L.items.length; li++) {
      var lm = L.items[li];
      var lx2 = sx(ux(lm[2])), ly2 = sy(uy(lm[1]));
      if (lx2 < -30 || lx2 > W + 30 || ly2 < -30 || ly2 > H + 30) continue;
      var cat = L.cats[lm[0]];
      if (s < 0.3) {
        ctx.fillStyle = 'rgba(160,139,108,.55)';
        ctx.beginPath(); ctx.arc(lx2, ly2, 2.5, 0, 7); ctx.fill();
      } else {
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(cat.emoji, lx2, ly2 + 4);
        if (s >= 0.5) {
          ctx.font = '11px Prompt, sans-serif';
          var lname = lm[3] || lm[4];
          var lw = ctx.measureText(lname).width;
          if (labelFits(lx2 - lw / 2, ly2 + 8, lw, 13)) {
            ctx.fillStyle = '#544636';
            ctx.fillText(lname, lx2, ly2 + 18);
          }
        }
      }
    }
  }

  // toilets — the point of everything above
  for (var pi = 0; pi < PINS.length; pi++) {
    var pin = PINS[pi];
    if (pin.kind === 'tier' && s < TIER_MINS) continue;
    if (pin.kind === 'customer' && s < CUST_MINS) continue;
    var px = sx(pin.x), py = sy(pin.y);
    if (px < -30 || px > W + 30 || py < -30 || py > H + 30) continue;
    drawPin(pin, px, py, s);
  }

  // me — the blue of every map's you-are-here
  if (me) {
    var mx = sx(me.x), my2 = sy(me.y);
    ctx.fillStyle = 'rgba(20,71,155,.15)';
    ctx.beginPath(); ctx.arc(mx, my2, Math.max(14, me.acc / UNIT_M * s), 0, 7); ctx.fill();
    ctx.fillStyle = '#14479b';
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(mx, my2, 7, 0, 7); ctx.fill(); ctx.stroke();
  }
}

function drawPin (pin, px, py, s) {
  var isSel = selected && selected.key === pin.key;
  var none = pinReport(pin) === 'toiletnone';
  // Overview zooms get dots, not pins — the city stays readable and the
  // mapped points (the certain ones) stay visible above the habit-tier crowd.
  // Mapped points stay a dot until the city has opened up. Drawn as full
  // pins at overview zoom they overlap into one dark mass over the middle of
  // Chiang Mai — 344 certainties reading as a smudge helps nobody.
  var dotUntil = pin.kind === 'mapped' ? 0.18 : (pin.kind === 'tier' ? 0.3 : 1.2);
  if (s < dotUntil && !isSel) {
    if (pin.kind === 'mapped') {
      ctx.fillStyle = T.mappedColor || '#c13a2e';
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(px, py, 4.5, 0, 7); ctx.fill(); ctx.stroke();
    } else {
      ctx.fillStyle = pin.tier ? pin.tier.color : '#c13a2e';
      ctx.globalAlpha = pin.kind === 'customer' ? 0.35 : 0.6;
      ctx.beginPath(); ctx.arc(px, py, pin.kind === 'customer' ? 2 : 3, 0, 7); ctx.fill();
      ctx.globalAlpha = 1;
    }
    return;
  }
  var r = isSel ? 16 : (pin.kind === 'customer' ? 9 : 12);
  if (isSel) {
    ctx.fillStyle = 'rgba(193,58,46,.2)';
    ctx.beginPath(); ctx.arc(px, py, r + 9, 0, 7); ctx.fill();
  }
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 2;
  if (pin.kind === 'mapped') {
    ctx.fillStyle = none ? '#a08b6c' : (T.mappedColor || '#c13a2e');
    ctx.beginPath(); ctx.arc(px, py, r, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.font = (isSel ? 15 : 12) + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('🚻', px, py + (isSel ? 5 : 4));
  } else {
    ctx.fillStyle = '#fffdf7';
    ctx.beginPath(); ctx.arc(px, py, r, 0, 7); ctx.fill();
    ctx.strokeStyle = none ? '#a08b6c' : (pin.tier ? pin.tier.color : '#c13a2e');
    ctx.lineWidth = isSel ? 3.5 : 2.5;
    ctx.stroke();
    ctx.font = (isSel ? 14 : (pin.kind === 'customer' ? 9 : 11)) + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(none ? '🚫' : (pin.tier ? pin.tier.emoji : '🚻'), px, py + 4);
  }
  var rep = pinReport(pin);
  if (rep && rep !== 'toiletnone') { // a person spoke — show the gold tick
    ctx.fillStyle = '#c08a2d';
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(px + r - 2, py - r + 2, 5, 0, 7); ctx.fill(); ctx.stroke();
  }
}

function frame () { draw(); requestAnimationFrame(frame); }

/* ---------- interaction ---------- */
var pointers = {}, lastPinch = 0, downAt = null, moved = false;
canvas.addEventListener('pointerdown', function (e) {
  canvas.setPointerCapture(e.pointerId);
  pointers[e.pointerId] = [e.clientX, e.clientY];
  downAt = [e.clientX, e.clientY]; moved = false;
});
canvas.addEventListener('pointermove', function (e) {
  if (!(e.pointerId in pointers)) return;
  var ids = Object.keys(pointers);
  var prev = pointers[e.pointerId];
  if (ids.length === 1) {
    var dx = e.clientX - prev[0], dy = e.clientY - prev[1];
    if (Math.abs(e.clientX - downAt[0]) + Math.abs(e.clientY - downAt[1]) > 6) moved = true;
    view.cx -= dx / view.scale; view.cy += dy / view.scale;
    clampView(); dirty = true;
  } else if (ids.length === 2) {
    moved = true;
    var o = pointers[ids[0] === String(e.pointerId) ? ids[1] : ids[0]];
    var d = Math.hypot(e.clientX - o[0], e.clientY - o[1]);
    if (lastPinch) {
      var f = d / lastPinch;
      zoomAt((e.clientX + o[0]) / 2, (e.clientY + o[1]) / 2, f);
    }
    lastPinch = d;
  }
  pointers[e.pointerId] = [e.clientX, e.clientY];
});
function endPointer (e) {
  delete pointers[e.pointerId];
  lastPinch = 0;
  if (!moved && downAt) tap(e.clientX, e.clientY);
  downAt = null;
  saveView();
}
canvas.addEventListener('pointerup', endPointer);
canvas.addEventListener('pointercancel', function (e) { delete pointers[e.pointerId]; lastPinch = 0; });
canvas.addEventListener('wheel', function (e) {
  e.preventDefault();
  zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.15 : 0.87);
  saveView();
}, { passive: false });

function zoomAt (px, py, f) {
  var rect = canvas.getBoundingClientRect();
  px -= rect.left; py -= rect.top;
  var wx = invx(px), wy = invy(py);
  view.scale *= f;
  view.scale = Math.max(0.004, Math.min(6, view.scale));
  view.cx = wx - (px - W / 2) / view.scale;
  view.cy = wy + (py - H / 2) / view.scale;
  clampView(); dirty = true;
}
var saveT = null;
function saveView () {
  clearTimeout(saveT);
  saveT = setTimeout(function () { lsSet('md_view', view); refreshList(); }, 350);
}

function tap (cpx, cpy) {
  var rect = canvas.getBoundingClientRect();
  var px = cpx - rect.left, py = cpy - rect.top;
  var best = null, bestD = 30; // generous thumb
  for (var i = 0; i < PINS.length; i++) {
    var pin = PINS[i];
    if (pin.kind === 'tier' && view.scale < TIER_MINS) continue;
    if (pin.kind === 'customer' && view.scale < CUST_MINS) continue;
    var d = Math.hypot(sx(pin.x) - px, sy(pin.y) - py);
    if (d < bestD) { bestD = d; best = pin; }
  }
  if (best) openCard(best);
  else { selected = null; closeCard(); dirty = true; }
}

/* ---------- distances & the nearest-first list ---------- */
function distM (lat1, lng1, lat2, lng2) {
  var R = 6371000, dLat = (lat2 - lat1) * Math.PI / 180,
      dLng = (lng2 - lng1) * Math.PI / 180;
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
          Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
function fmtDist (m) {
  return m < 1000 ? Math.round(m / 10) * 10 + ' ม.' : (m / 1000).toFixed(1) + ' กม.';
}
function pinReport (pin) {
  if (pin.id && myReports[pin.id]) return myReports[pin.id].report;
  return pin.report || '';
}
function pinName (pin) {
  if (pin.th || pin.en) return { th: pin.th || pin.en, en: pin.en };
  if (pin.kind === 'mapped') return { th: 'ห้องน้ำ (ปักหมุดไว้)', en: 'Mapped toilet' };
  return { th: 'ไม่ทราบชื่อ', en: '' };
}

function refreshList () {
  var fromLat, fromLng, fromLabel;
  if (me) {
    fromLat = me.lat; fromLng = me.lng;
    fromLabel = 'จากตำแหน่งของคุณ · from where you stand';
  } else {
    fromLat = ORIGIN[0] + view.cy / Q;
    fromLng = ORIGIN[1] + view.cx / (Q * KX);
    fromLabel = 'จากกลางแผนที่ · from the map centre (กด 📍 เพื่อใช้ตำแหน่งจริง)';
  }
  document.getElementById('near-from').textContent = fromLabel;
  var rows = PINS.map(function (p) {
    return { p: p, d: distM(fromLat, fromLng, p.lat, p.lng) };
  });
  rows.sort(function (a, b) { return a.d - b.d; }); // distance and NOTHING else
  rows = rows.slice(0, 50);
  var ol = document.getElementById('near-list');
  ol.innerHTML = rows.map(function (r) {
    var p = r.p, nm = pinName(p), rep = pinReport(p);
    var none = rep === 'toiletnone';
    var em, emCls = 'pin-em';
    if (p.kind === 'mapped') { em = '🚻'; emCls += ' mapped'; }
    else em = none ? '🚫' : (p.tier ? p.tier.emoji : '🚻');
    var sub = [];
    if (p.kind === 'mapped') {
      sub.push('ปักหมุดตำแหน่งแน่นอน');
      if (p.fee) sub.push(T.costs[p.fee] ? T.costs[p.fee].chip_th : p.fee);
    } else if (p.tier) {
      var acc = T.access[p.tier.access];
      sub.push(p.tier.th + (acc && p.tier.access !== 'public' ? ' · ' + acc.th : ''));
    }
    var badge = '';
    if (rep && !none && REP_BY_KEY[rep]) {
      badge = '<span class="row-badge">✓ ' + REP_BY_KEY[rep].th + '</span>';
    }
    var walk = Math.round(r.d / (T.walkMetresPerMinute || 80));
    return '<li data-key="' + p.key + '"' + (none ? ' class="none"' : '') + '>' +
      '<span class="' + emCls + '">' + em + '</span>' +
      '<span class="row-words"><b>' + esc(nm.th) + '</b>' +
      '<small>' + esc(sub.join(' · ')) + (nm.en && nm.en !== nm.th ? ' · ' + esc(nm.en) : '') + '</small>' +
      badge + '</span>' +
      '<span class="row-dist"><b>' + fmtDist(r.d) + '</b><small>เดิน ~' + walk + ' นาที</small></span>' +
      '</li>';
  }).join('');
  Array.prototype.forEach.call(ol.children, function (li) {
    li.addEventListener('click', function () {
      var pin = PINS.filter(function (p) { return p.key === li.dataset.key; })[0];
      if (!pin) return;
      view.cx = pin.x; view.cy = pin.y;
      if (view.scale < 0.5) view.scale = 0.6;
      clampView(); dirty = true; lsSet('md_view', view);
      openCard(pin);
    });
  });
}
function esc (s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ---------- detail card ---------- */
var cardEl = document.getElementById('card'), veil = document.getElementById('card-veil');
function openCard (pin) {
  selected = pin; dirty = true;
  var nm = pinName(pin), rep = pinReport(pin), mine = pin.id && myReports[pin.id];
  var h = '<button class="close-x" id="card-close">✕</button>';
  h += '<h2>' + esc(nm.th) + '</h2>';
  if (nm.en && nm.en !== nm.th) h += '<p class="sub">' + esc(nm.en) + '</p>';
  else h += '<p class="sub"></p>';

  if (pin.kind === 'mapped') {
    h += '<span class="tier-chip jade">📍 ปักหมุดตำแหน่งแน่นอน · mapped at this spot</span>';
    if (pin.fee && T.costs[pin.fee]) {
      h += '<span class="tier-chip">' + esc(T.costs[pin.fee].th) + ' · ' + esc(T.costs[pin.fee].en) + '</span>';
    } else if (pin.baht) {
      h += '<span class="tier-chip">' + pin.baht + ' ฿</span>';
    }
    if (pin.hours) h += '<span class="tier-chip">🕐 ' + esc(pin.hours) + '</span>';
  } else if (pin.tier) {
    h += '<span class="tier-chip" style="box-shadow:inset 0 0 0 1.5px ' + pin.tier.color + '">' +
      pin.tier.emoji + ' ' + esc(pin.tier.th) + ' · ' + esc(pin.tier.en) + '</span>';
    var accw = T.access[pin.tier.access];
    if (accw && pin.tier.access !== 'public') {
      h += '<span class="tier-chip">🚪 ' + esc(accw.th) + ' · ' + esc(accw.en) + '</span>';
    }
    if (pin.hours) h += '<span class="tier-chip">🕐 ' + esc(pin.hours) + '</span>';
  }
  if (rep && REP_BY_KEY[rep]) {
    h += '<span class="tier-chip gold">' + REP_BY_KEY[rep].emoji + ' ' +
      (mine ? 'คุณบอกไว้: ' : 'มีคนบอกไว้: ') + esc(REP_BY_KEY[rep].th) +
      ' · ' + esc(REP_BY_KEY[rep].en) + '</span>';
  }
  // The habit sentence — the words the site stands behind, verbatim.
  if (pin.kind !== 'mapped' && pin.tier) {
    h += '<div class="basis">' + esc(pin.tier.basis_th) +
      '<small>' + esc(pin.tier.basis_en) + '</small>' +
      '<small>⚠️ เป็นธรรมเนียมของประเภทนี้ ไม่ใช่การยืนยันรายแห่ง · a habit of the class, not a promise about this building</small></div>';
  }
  h += '<div class="card-actions">';
  h += '<button class="big-btn jade" id="act-go">🧭 นำทาง</button>';
  h += '<button class="big-btn quiet" id="act-visit">🗂️ บันทึกว่าฉันใช้ (ส่วนตัว)</button>';
  h += '</div>';
  if (pin.id && /^(cm|cr)-/.test(pin.id) && T.reportEndpoint) {
    h += '<div class="report-block"><b>บอกเพื่อนร่วมทาง 🙏</b>' +
      '<small>ส่งแค่คำเดียว ไม่ส่งชื่อ ไม่ส่งตำแหน่งของคุณ · one word is sent, nothing about you</small>' +
      '<div class="rep-grid">' +
      REPORTS.map(function (r) {
        return '<button data-rep="' + r.key + '">' + r.emoji + ' ' + esc(r.th) +
          '<small>' + esc(r.en) + '</small></button>';
      }).join('') + '</div></div>';
  }
  cardEl.innerHTML = h;
  cardEl.hidden = false; veil.hidden = false;
  document.getElementById('card-close').onclick = closeCard;
  veil.onclick = closeCard;
  document.getElementById('act-go').onclick = function () {
    location.href = 'geo:' + pin.lat + ',' + pin.lng + '?q=' + pin.lat + ',' + pin.lng +
      '(' + encodeURIComponent(nm.th) + ')';
  };
  document.getElementById('act-visit').onclick = function () {
    myVisits.unshift({ t: new Date().toISOString(), key: pin.key, th: nm.th, en: nm.en });
    if (myVisits.length > 500) myVisits.length = 500;
    lsSet('md_visits', myVisits);
    toast('บันทึกไว้ในเครื่องนี้เท่านั้น 🗂️ · saved on this phone only');
  };
  Array.prototype.forEach.call(cardEl.querySelectorAll('[data-rep]'), function (b) {
    b.onclick = function () { sendReport(pin, b.dataset.rep); };
  });
}
function closeCard () {
  cardEl.hidden = true; veil.hidden = true;
  selected = null; dirty = true;
}

/* ---------- reports: one word, no name ---------- */
function sendReport (pin, key) {
  myReports[pin.id] = { report: key, t: new Date().toISOString() };
  lsSet('md_my_reports', myReports);
  pin.report = key;
  var body = JSON.stringify({ placeId: pin.id, report: key });
  fetch(T.reportEndpoint, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: body
  }).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    toast('ส่งแล้ว ขอบคุณที่บอกต่อ 🙏');
  }).catch(function () {
    pendingReports.push({ placeId: pin.id, report: key });
    lsSet('md_pending', pendingReports);
    toast('ยังไม่มีเน็ต — จะส่งให้เมื่อออนไลน์ 🕊️');
  });
  openCard(pin); // re-render with the new chip
  refreshList(); dirty = true;
}
function flushPending () {
  if (!pendingReports.length || !navigator.onLine) return;
  var q = pendingReports.slice(); pendingReports = []; lsSet('md_pending', []);
  q.forEach(function (item) {
    fetch(T.reportEndpoint, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify(item)
    }).catch(function () {
      pendingReports.push(item); lsSet('md_pending', pendingReports);
    });
  });
}
window.addEventListener('online', flushPending);

/* ---------- toast ---------- */
var toastT = null;
function toast (msg) {
  var t = document.getElementById('toast');
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastT);
  toastT = setTimeout(function () { t.hidden = true; }, 2600);
}

/* ---------- locate ----------
   Two steps, deliberately. 📍 opens our own dialog; only its yes button
   reaches Android's. The map already works without any of this — it opens on
   the baked city and the list measures from the map centre — so this adds
   precision rather than unlocking the app, and a reader who says no keeps
   everything they had. No is remembered: the button goes away rather than
   sitting there ready to raise the same dialog again. */
var gpsOff = false;

function locate () {
  if (gpsOff) return;
  if (!navigator.geolocation) { toast('เครื่องนี้ไม่มีระบบตำแหน่ง'); killGps(); return; }
  if (watching) { // second press = recentre, no dialog
    document.getElementById('btn-locate').classList.add('on');
    if (me) { view.cx = me.x; view.cy = me.y; if (view.scale < 0.4) view.scale = 0.5; clampView(); dirty = true; }
    return;
  }
  document.getElementById('loc-gate').hidden = false;
  document.getElementById('loc-yes').focus();
}

function killGps () {
  gpsOff = true;
  var g = document.getElementById('loc-gate'); if (g) g.hidden = true;
  var b = document.getElementById('btn-locate');
  if (b && b.parentNode) b.parentNode.removeChild(b);
  toast('ไม่ใช้ตำแหน่ง — เลื่อนแผนที่ไปที่ที่คุณอยู่ได้เลย');
}

function startWatch () {
  document.getElementById('loc-gate').hidden = true;
  document.getElementById('btn-locate').classList.add('on');
  watching = true;
  navigator.geolocation.watchPosition(function (pos) {
    var first = !me;
    me = { lat: pos.coords.latitude, lng: pos.coords.longitude,
      acc: pos.coords.accuracy || 30,
      x: ux(pos.coords.longitude), y: uy(pos.coords.latitude) };
    if (first) {
      view.cx = me.x; view.cy = me.y;
      if (view.scale < 0.4) view.scale = 0.5;
      clampView(); refreshList();
    }
    dirty = true;
  }, function () {
    /* Refused at the OS level, or no fix. Either way the map is still a map
       and the list is still sorted from its centre — so this is a note, and
       the door closes rather than staying open to ask again. */
    toast('ยังหาตำแหน่งไม่ได้ — เลื่อนแผนที่ไปที่ที่คุณอยู่ได้เลย');
    watching = false;
    killGps();
  }, { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 });
}

/* ---------- privacy & my-log pages ---------- */
var pageEl = document.getElementById('page');
function openPage (html) { pageEl.innerHTML = html; pageEl.hidden = false; }
function closePage () { pageEl.hidden = true; }

document.getElementById('btn-privacy').onclick = function () {
  openPage(
    '<button class="close-x" id="pg-close">✕</button>' +
    '<h2>ความเป็นส่วนตัว 🕊️</h2><p class="sub">ทำไมแอปนี้เงียบกับข้อมูลของคุณ</p>' +
    '<section><b class="h">แผนที่อยู่ในเครื่องทั้งหมด</b>' +
    'ถนน อาคาร และหมุดทุกอัน ติดตั้งมาพร้อมแอป การเปิดดูแผนที่ไม่เรียกหาเซิร์ฟเวอร์ใดเลย ไม่มีใครรู้ว่าคุณเปิดดูตรงไหน<br>' +
    '<small>The whole map ships inside the app. Browsing it makes no network request, to anyone.</small></section>' +
    '<section><b class="h">ตำแหน่งของคุณไม่ออกจากเครื่อง</b>' +
    'ตำแหน่งใช้เรียงรายการ "ใกล้ที่สุดก่อน" ในเครื่องเท่านั้น ไม่ถูกส่ง ไม่ถูกเก็บ<br>' +
    '<small>Your location sorts the list on this phone. It is never sent, never stored.</small></section>' +
    '<section><b class="h">การบอกต่อ ส่งแค่คำเดียว</b>' +
    'เมื่อคุณกดบอกสภาพห้องน้ำ แอปส่งรหัสสถานที่กับคำหนึ่งคำจากห้าคำ ไปที่เซิร์ฟเวอร์ของมดแดงเท่านั้น ไม่มีชื่อ ไม่มีบัญชี ไม่มีตำแหน่งของคุณติดไป<br>' +
    '<small>A report sends the place id and one word from a closed list of five, to Mot Dang\'s own worker. No name, no account, nothing about you rides along.</small></section>' +
    '<section><b class="h">บันทึกของคุณเป็นของคุณ</b>' +
    'บันทึกว่าคุณใช้ห้องน้ำที่ไหน อยู่ในเครื่องนี้เท่านั้น ลบได้ทุกเมื่อในหน้า 🗂️<br>' +
    '<small>Your visit log lives on this phone only, and the erase button really erases it.</small></section>' +
    '<section><small>ข้อมูลแผนที่ © OpenStreetMap contributors (ODbL) · motdang.net</small></section>'
  );
  document.getElementById('pg-close').onclick = closePage;
};

document.getElementById('btn-mylog').onclick = function () {
  var rows = myVisits.map(function (v) {
    var d = new Date(v.t);
    return '<div class="visit-row"><span>' + esc(v.th) + '</span><time>' +
      d.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' }) + ' ' +
      d.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' }) + '</time></div>';
  }).join('');
  openPage(
    '<button class="close-x" id="pg-close">✕</button>' +
    '<h2>บันทึกของฉัน 🗂️</h2><p class="sub">อยู่ในเครื่องนี้เท่านั้น · on this phone only</p>' +
    '<section>' + (rows || 'ยังไม่มีบันทึก — กด "บันทึกว่าฉันใช้" ที่ห้องน้ำที่คุณแวะ<br><small>Nothing yet. Tap "log my visit" on a toilet you stop at.</small>') + '</section>' +
    (myVisits.length ? '<button class="big-btn quiet" id="pg-erase" style="width:100%">ลบทั้งหมด · erase everything</button>' : '')
  );
  document.getElementById('pg-close').onclick = closePage;
  var er = document.getElementById('pg-erase');
  if (er) er.onclick = function () {
    myVisits = []; lsSet('md_visits', []);
    toast('ลบแล้ว ไม่เหลืออะไรเลย 🕊️');
    closePage();
  };
};

/* ---------- sheet drag ---------- */
var sheet = document.getElementById('sheet');
document.getElementById('sheet-handle').addEventListener('click', function () {
  sheet.classList.toggle('tall');
  setTimeout(resize, 300);
});

/* ---------- buttons ---------- */
document.getElementById('btn-zoom-in').onclick = function () { zoomAt(W / 2, H / 2, 1.45); saveView(); };
document.getElementById('btn-zoom-out').onclick = function () { zoomAt(W / 2, H / 2, 0.69); saveView(); };
document.getElementById('btn-locate').onclick = locate;
document.getElementById('loc-yes').onclick = startWatch;
document.getElementById('loc-no').onclick = killGps;
/* Ask Android what it already knows, so 📍 is never offered for a permission
   the OS has already refused. Unsupported here just leaves the button up. */
if (navigator.permissions && navigator.permissions.query) {
  try {
    navigator.permissions.query({ name: 'geolocation' }).then(function (st) {
      if (st.state === 'denied') { gpsOff = true;
        var b = document.getElementById('btn-locate');
        if (b && b.parentNode) b.parentNode.removeChild(b); }
    }).catch(function () {});
  } catch (e) {}
}

/* ---------- city jump ----------
   Two cities are 190 km apart. Without this, a reader in Chiang Rai whose
   phone will not give a fix has no way to reach their own city but to drag
   the map across the farmland between. The button only exists when more
   than one city is baked in. */
var CITY_NAMES = { cm: ["เชียงใหม่", "Chiang Mai"], cr: ["เชียงราย", "Chiang Rai"] };
var CITY_KEYS = Object.keys(B.extents || {});
if (CITY_KEYS.length > 1) {
  var btn = document.createElement('button');
  btn.className = 'round-btn';
  btn.id = 'btn-city';
  btn.textContent = '🏙️';
  btn.setAttribute('aria-label', 'ไปอีกเมือง');
  document.querySelector('.map-controls').appendChild(btn);
  btn.onclick = function () {
    // whichever city centre is furthest from the view is the one to go to
    var far = null, farD = -1;
    CITY_KEYS.forEach(function (k) {
      var e = B.extents[k];
      var cx = (ux(e[3]) + ux(e[1])) / 2, cy = (uy(e[0]) + uy(e[2])) / 2;
      var d = Math.hypot(cx - view.cx, cy - view.cy);
      if (d > farD) { farD = d; far = { k: k, cx: cx, cy: cy }; }
    });
    view.cx = far.cx; view.cy = far.cy; view.scale = 0.11;
    clampView(); dirty = true; lsSet('md_view', view); refreshList();
    var nm = CITY_NAMES[far.k] || [far.k, far.k];
    toast(nm[0] + ' · ' + nm[1]);
  };
}

/* ---------- go ---------- */
resize();
clampView();
refreshList();
flushPending();
frame();
// NOT locate(). This used to fire on mount, which meant the very first thing
// a new installer saw was an Android permission dialog stacked over a map
// they had not looked at yet — the one moment they know least about what
// they are agreeing to, and the cheapest moment to back out entirely.
//
// The map opens on the baked city, the list is already sorted, and 📍 is
// right there in the toolbar when someone wants it. Finding the nearest
// toilet is still the job; it just no longer costs a permission up front.
