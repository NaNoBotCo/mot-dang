/* Shops and everyday services, one place at a time (Nan, 2026-10-02: "Let's utilize the doodler
   to avoid filler"). A Chiang Mai street kit is cut once per place: a shophouse of two or three
   storeys, a teak house on posts, a concrete row, a glass front, a roadside sala or a Lanna wood
   shop; roll-up shutters, folding teak doors or a tarp; awnings, the name board, the spirit house,
   plants, motorbikes, wires, the soi dog. The place's seed deals the look and its facts steer it
   (sub-kind, brand tint, hours, road, river, old city, village, mall); the trade works in the bay.
   Scenes: office garage gov salon clothes fixit parking mall pharmacy rental convenience crafts
   bank laundry fuel tours printing busstop post secondhand pets */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.kit || !D.kit.sign) return;
var K = D.kit, paper = K.paper, jag = K.jag, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU, person = K.person, POSE = K.POSE;
var FONT = '"Sarabun",system-ui,sans-serif';
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function pick(R, a) { return a[Math.floor(R() * a.length) % a.length]; }
function deal(R, w) { var tot = 0, k, last; for (k in w) tot += w[k]; var u = R() * tot; for (k in w) { last = k; u -= w[k]; if (u <= 0) return k; } return last; }
function has(F, re) { return re.test((F.name || '') + ' ' + (F.nameEn || '') + ' ' + (F.brand || '')); }
function sub(F, s) { return (F.sub || []).indexOf(s) >= 0; }

/* ---------------------------------------------------------------- colour: hex mixing, night dims toward indigo */
var CC = {};
function rgb(h) { var n = parseInt(h.slice(1, 7), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function mixc(a, b, u) {
  var k = a + b + u; if (CC[k]) return CC[k];
  var A = rgb(a), B = rgb(b), s = '#';
  for (var i = 0; i < 3; i++) { var x = Math.round(A[i] + (B[i] - A[i]) * u); s += (x < 16 ? '0' : '') + x.toString(16); }
  return (CC[k] = s);
}
function nt(S, col, u) { return S.night ? mixc(col, '#161a33', u == null ? 0.5 : u) : col; }

/* ---------------------------------------------------------------- cut once: the still layers, keyed by size, scale, seed and state */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : null;
  if (!m || typeof document === 'undefined') { draw(c); return; }
  var k = key + '|' + [m.a, m.d, m.e, m.f].join(','), e = null, i;
  for (i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    var cv = document.createElement('canvas'); cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy); draw(q);
    e = { k: k, cv: cv, ox: ox, oy: oy }; CACHE.unshift(e); if (CACHE.length > 30) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
}
/* a small piece cut once and stamped every frame (a scooter that rides, a van that arrives) */
var SPR = {}, nspr = 0;
function sprite(S, name, w, h, draw) {
  var m = S.c.getTransform ? S.c.getTransform() : null, k = m ? Math.abs(m.a) : 1, key = name + '|' + Math.round(w) + '|' + Math.round(h) + '|' + k + '|' + (+S.night);
  if (SPR[key]) return SPR[key];
  if (typeof document === 'undefined') return null;
  if (++nspr > 60) { SPR = {}; nspr = 1; }
  var o = document.createElement('canvas'); o.width = Math.max(1, Math.ceil(w * k)); o.height = Math.max(1, Math.ceil(h * k));
  var q = o.getContext('2d'); q.setTransform(k, 0, 0, k, 0, 0); draw(q);
  return (SPR[key] = o);
}
/* a soft round glow from a cut-once disc */
var GLOW = {};
function glow(c, x, y, r, col, a) {
  var o = GLOW[col];
  if (!o && typeof document !== 'undefined') { o = GLOW[col] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(' + col + ',1)'); g.addColorStop(0.45, 'rgba(' + col + ',.4)'); g.addColorStop(1, 'rgba(' + col + ',0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o || a <= 0) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
function fp(c, pts, col) { c.fillStyle = col; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.fill(); }
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
function fe(c, x, y, rx, ry, col, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot || 0, 0, TAU); c.fill(); }
function txt(c, s, x, y, px, col, w, al) { c.font = (w || 700) + ' ' + Math.round(px) + 'px ' + FONT; c.fillStyle = col; c.textAlign = al || 'center'; c.textBaseline = 'middle'; c.fillText(s, x, y); }

/* ---------------------------------------------------------------- figures: the skeleton as doodler.js works it, arms that reach */
function joints(x, y, h, P, dir) {
  var seat = P.seat || 0.47, lean = P.lean || 0;
  function pt(o, a, l) { return [o[0] + dir * Math.sin(a) * l, o[1] + Math.cos(a) * l]; }
  var hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33];
  return { hip: hip, sh: sh };
}
/* two bones to a point, the elbow found by the law of cosines */
function solve(s, T, l1, l2, dir) {
  var vx = dir * (T[0] - s[0]), vy = T[1] - s[1], d = Math.min(Math.sqrt(vx * vx + vy * vy), l1 + l2 - 0.01), at = Math.atan2(vx, vy);
  var al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * Math.max(d, 0.01)), -1, 1)), up = at - al;
  return [up, Math.atan2(vx - Math.sin(up) * l1, vy - Math.cos(up) * l1) - up];
}
function reach(x, y, h, P, dir, hA, hB) {
  var J = joints(x, y, h, P, dir), arms = P.arms.slice(), a;
  if (hA) { a = solve(J.sh, hA, h * 0.17, h * 0.16, dir); arms[0] = a[0]; arms[1] = a[1]; }
  if (hB) { a = solve(J.sh, hB, h * 0.17, h * 0.16, dir); arms[2] = a[0]; arms[3] = a[1]; }
  return { lean: P.lean || 0, seat: P.seat || 0.47, lift: P.lift || 0, legs: P.legs, arms: arms };
}
function fig(c, d, x, y, h, P, dir) { d.dir = dir; return person(c, x, y, h, P, d); }
var SITP = { lean: 0.1, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [0.9, 0.5, 0.8, 0.6] };
var STANDP = { lean: 0.02, legs: [0.05, 0, -0.05, 0], arms: [0.15, 0.1, -0.1, 0.1] };
var CROUCH = { lean: 0.55, seat: 0.3, legs: [1.75, -2.3, 1.15, -1.55], arms: [1.3, 0.2, 1.0, 0.5] };
function crew(S, n, mix, salt) { return K.town({ r: rnd((S.seed + (salt || 7)) >>> 0), set: '_', t: 0 }, n, mix || { casual: 0.72, sin: 0.16, mohom: 0.12 }); }
function uni(d, col, low) { d.garb = 'casual'; d.long = true; d.col = col; if (low) d.low = low; return d; }
/* a talking pose: the forearm lifts now and then, |sin| bursts */
function talk(t, k) { var u = Math.max(0, Math.sin(t / 900 + k)); return { lean: 0.04, legs: [0.05, 0, -0.05, 0], arms: [0.35 + 0.6 * u, 0.6 + 0.5 * u, 0.12, 0.2] }; }
function sitTalk(t, k) { var u = Math.max(0, Math.sin(t / 1100 + k)); return { lean: 0.08, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [0.6 + 0.7 * u, 0.7 + 0.4 * u, 0.8, 0.6] }; }
function typing(t, k) { return { lean: 0.16, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [1.0 + 0.07 * Math.sin(t / 95 + k), 0.45, 0.92 + 0.07 * Math.sin(t / 110 + k + 2), 0.5] }; }

/* ---------------------------------------------------------------- the street's pieces */
var WALLS = ['#efe3c8', '#d9e8d8', '#f2d4cf', '#f3e2a6', '#cfe0ea', '#e2d9ea', '#d8d2c4', '#f0c9a0', '#bfd8c9', '#e8e8e2', '#f6efe0', '#d4e4c0', '#f2c6a8', '#c9d6e8'];
var TRIMS = ['#7a3b2a', '#2f5f6b', '#6b4a8a', '#2e6b3e', '#8a5a2a', '#3a4a6a', '#9a2f3a', '#3f6f5a'];
var SHUT = ['#9aa3a8', '#8fa9b8', '#7f9a86', '#a8a08a', '#6f8aa8', '#b0b4b8', '#5f7f9a', '#9a8a7a'];
var AWN = [['#d94b3b', '#f6efe0'], ['#2f7f6b', '#f6efe0'], ['#e8a33a', '#f6efe0'], ['#3a6fb0', '#f6efe0'], ['#8a3a6a', '#f2e6c9'], ['#d9342b', '#f2c94c'], ['#4fae8c', '#ffffff'], ['#e5567f', '#fff1f5']];
var BOARD = ['#6a3a1e', '#7a2f2a', '#2f4f3a', '#2f3f6a', '#5a2a4a', '#3a3a3a', '#7a5a1e', '#1f4f5a'];
var BIKE = ['#d9342b', '#f2f2f2', '#2a2a2a', '#3a6fb0', '#e8b84a', '#7fd8ff', '#e5567f', '#4fae8c', '#9aa3a8', '#6b4a8a', '#f08a3a'];
var CARS = ['#f2f2f2', '#c9ccd4', '#2a2a2a', '#8a1f2a', '#3a4a6a', '#d9d2c0', '#5a6a5a', '#1f3a5a'];

/* the san phra phum on its post: a gilded house under a tiered red roof with chofa horns, or a northern
   teak one with kalae; red soda with straws, a garland, figurines, and the incense pot */
function spiritHouse(q, x, y, s, S, kind, R) {
  var lan = kind === 'lanna', post = nt(S, lan ? '#6b4226' : '#f2ead8'), gold = nt(S, '#d9a53c', 0.35), red = nt(S, lan ? '#7a4a2a' : '#b8322a', 0.4);
  paper(q, rect(x - s * 0.045, y - s * 0.6, s * 0.09, s * 0.6), post, 1);
  fr(q, x - s * 0.07, y - s * 0.04, s * 0.14, s * 0.04, nt(S, '#c9b89a'));
  var py = y - s * 0.62, bw = s * 0.3, bh = s * 0.2, by = py - bh;
  paper(q, rect(x - s * 0.27, py, s * 0.54, s * 0.05), gold, 1);
  paper(q, rect(x - bw / 2, by, bw, bh), lan ? nt(S, '#8a5a32') : gold, 1);
  fr(q, x - bw * 0.16, by + bh * 0.3, bw * 0.32, bh * 0.7, nt(S, '#3a1f12'));
  for (var i = 0; i < 4; i++) fr(q, x - bw / 2 + i * bw / 3 - 1, by, 2, bh, lan ? nt(S, '#5a3520') : nt(S, '#f2d27a', 0.35));
  var r1 = by - s * 0.16, r2 = r1 - s * 0.1;
  paper(q, poly([[x - bw * 0.8, by + 1], [x - bw * 0.42, r1], [x + bw * 0.42, r1], [x + bw * 0.8, by + 1]]), red, 1);
  paper(q, poly([[x - bw * 0.5, r1 + 1], [x, r2 - s * 0.02], [x + bw * 0.5, r1 + 1]]), red, 1);
  q.strokeStyle = gold; q.lineWidth = Math.max(1, s * 0.015); q.lineCap = 'round';
  q.beginPath(); q.moveTo(x - bw * 0.8, by + 1); q.lineTo(x - bw * 0.42, r1); q.lineTo(x + bw * 0.42, r1); q.lineTo(x + bw * 0.8, by + 1); q.moveTo(x - bw * 0.5, r1); q.lineTo(x, r2 - s * 0.02); q.lineTo(x + bw * 0.5, r1); q.stroke();
  if (lan) { q.beginPath(); q.moveTo(x, r2); q.quadraticCurveTo(x - s * 0.02, r2 - s * 0.06, x - s * 0.07, r2 - s * 0.08); q.moveTo(x, r2); q.quadraticCurveTo(x + s * 0.02, r2 - s * 0.06, x + s * 0.07, r2 - s * 0.08); q.stroke(); }
  else { [[x - bw * 0.8, by + 1, -1], [x + bw * 0.8, by + 1, 1], [x, r2 - s * 0.02, 0]].forEach(function (p) { q.beginPath(); q.moveTo(p[0], p[1]); q.quadraticCurveTo(p[0] + p[2] * s * 0.03, p[1] - s * 0.05, p[0] + p[2] * s * 0.01 + (p[2] ? 0 : s * 0.02), p[1] - s * 0.08); q.stroke(); }); }
  /* offerings on the ledge: red soda with straws, flowers, figurines */
  var ly = py;
  [-0.2, -0.13].forEach(function (k) { fr(q, x + k * s, ly - s * 0.07, s * 0.035, s * 0.07, nt(S, '#d9242b', 0.3)); ln(q, [[x + k * s + s * 0.018, ly - s * 0.07], [x + k * s + s * 0.03, ly - s * 0.11]], '#f2f2f2', 1); });
  fe(q, x + s * 0.17, ly - s * 0.04, s * 0.04, s * 0.035, nt(S, '#f29a1f', 0.3));
  fe(q, x + s * 0.21, ly - s * 0.05, s * 0.025, s * 0.03, nt(S, '#ffffff', 0.4));
  /* the garland on the post */
  for (i = 0; i < 9; i++) { var a = i / 8; fe(q, x - s * 0.06 + a * s * 0.12, py + s * 0.08 + Math.sin(a * Math.PI) * s * 0.06, s * 0.016, s * 0.016, nt(S, i % 3 ? '#f7b52c' : '#fffaf0', 0.35)); }
  /* figurines at the foot: an elephant and a pair of zebras */
  var fx = x + (R() < 0.5 ? -1 : 1) * s * 0.16;
  fe(q, fx, y - s * 0.05, s * 0.05, s * 0.032, nt(S, '#8a8f99')); fr(q, fx - s * 0.04, y - s * 0.04, s * 0.012, s * 0.04, nt(S, '#8a8f99')); fr(q, fx + s * 0.025, y - s * 0.04, s * 0.012, s * 0.04, nt(S, '#8a8f99'));
  ln(q, [[fx + s * 0.05, y - s * 0.06], [fx + s * 0.07, y - s * 0.02]], nt(S, '#8a8f99'), Math.max(1, s * 0.012));
  var zx = x - (fx - x) * 0.9;
  fe(q, zx, y - s * 0.06, s * 0.04, s * 0.022, nt(S, '#f2f2f2')); fr(q, zx - s * 0.03, y - s * 0.05, s * 0.01, s * 0.05, nt(S, '#f2f2f2')); fr(q, zx + s * 0.02, y - s * 0.05, s * 0.01, s * 0.05, nt(S, '#f2f2f2'));
  q.strokeStyle = nt(S, '#1a1a1a'); q.lineWidth = 1; for (i = -1; i <= 1; i++) { q.beginPath(); q.moveTo(zx + i * s * 0.015, y - s * 0.08); q.lineTo(zx + i * s * 0.015, y - s * 0.045); q.stroke(); }
  fe(q, zx + s * 0.045, y - s * 0.085, s * 0.015, s * 0.012, nt(S, '#f2f2f2'));
  /* the incense pot */
  fe(q, x + s * 0.07, py - s * 0.01, s * 0.035, s * 0.02, nt(S, '#b8872f'));
  return [x + s * 0.07, py - s * 0.02];
}
/* incense: sticks and a thread of smoke, x = A·sin(ky − ωt) */
function smoke(c, x, y, s, t, k) {
  c.lineWidth = 1; c.strokeStyle = '#b5532f'; c.beginPath(); c.moveTo(x - 1.5, y); c.lineTo(x - 2.5, y - s * 0.07); c.moveTo(x + 1.5, y); c.lineTo(x + 2.5, y - s * 0.07); c.stroke();
  fr(c, x - 3.5, y - s * 0.075, 2, 2, '#ff7a3a'); fr(c, x + 1.5, y - s * 0.075, 2, 2, '#ff7a3a');
  c.strokeStyle = 'rgba(240,236,228,.5)'; c.beginPath();
  for (var j = 0; j < s * 0.5; j += 3) { var xx = x + Math.sin(j * 0.1 - t / 600 + k) * (1 + j * 0.08); j ? c.lineTo(xx, y - s * 0.08 - j) : c.moveTo(xx, y - s * 0.08); }
  c.stroke();
}

/* plants: bougainvillea up a post (bracts in three tones), banana, frangipani, pots of chilli and
   basil and mother-in-law's tongue, the glazed dragon jar */
var BOUG = [['#d6247a', '#e8508f', '#b01e66'], ['#f08a3a', '#f5a85a', '#d9652a'], ['#e85a9a', '#f7b5d0', '#ffffff'], ['#c2185b', '#9c1a5a', '#e04090']];
function bougain(q, x, y, h, w, S, R) {
  var pal = pick(R, BOUG), i;
  q.strokeStyle = nt(S, '#5a3a22'); q.lineWidth = Math.max(1.5, h * 0.02); q.lineCap = 'round';
  q.beginPath(); q.moveTo(x, y); q.bezierCurveTo(x - w * 0.1, y - h * 0.4, x + w * 0.15, y - h * 0.7, x + w * 0.35, y - h); q.stroke();
  for (i = 0; i < 70; i++) {
    var u = R(), bx = lerp(x, x + w * 0.4, u) + (R() - 0.3) * w * (0.2 + u * 0.7), by = y - h * (0.25 + 0.8 * u) + (R() - 0.5) * h * 0.15;
    fe(q, bx, by, h * 0.035, h * 0.03, i % 4 === 0 ? nt(S, '#3f7a3a') : nt(S, pal[i % 3], 0.45));
  }
}
function banana(q, x, y, h, S, R) {
  paper(q, poly([[x - h * 0.05, y], [x - h * 0.03, y - h * 0.55], [x + h * 0.03, y - h * 0.55], [x + h * 0.05, y]]), nt(S, '#7a9a4a'), 1);
  for (var i = 0; i < 6; i++) {
    var a = -Math.PI / 2 + (i - 2.5) * 0.45, L2 = h * (0.4 + R() * 0.15), ex = x + Math.cos(a) * L2, ey = y - h * 0.55 + Math.sin(a) * L2 + L2 * 0.25;
    paper(q, function (p) { p.beginPath(); p.moveTo(x, y - h * 0.55); p.quadraticCurveTo((x + ex) / 2 + Math.sin(a) * L2 * 0.25, (y - h * 0.55 + ey) / 2 - L2 * 0.25, ex, ey); p.quadraticCurveTo((x + ex) / 2 - Math.sin(a) * L2 * 0.1, (y - h * 0.55 + ey) / 2 + L2 * 0.05, x, y - h * 0.55); }, nt(S, i % 2 ? '#4f8a3a' : '#5fa04a'), 1);
  }
}
function frangi(q, x, y, h, S, R) {
  q.strokeStyle = nt(S, '#8a8070'); q.lineCap = 'round';
  function br(x0, y0, a, l, d) {
    var x1 = x0 + Math.cos(a) * l, y1 = y0 + Math.sin(a) * l; q.lineWidth = Math.max(1.5, l * 0.16); q.beginPath(); q.moveTo(x0, y0); q.lineTo(x1, y1); q.stroke();
    if (d < 3) { br(x1, y1, a - 0.45, l * 0.72, d + 1); br(x1, y1, a + 0.45, l * 0.72, d + 1); }
    else { for (var j = 0; j < 4; j++) fe(q, x1 + Math.cos(j * 1.6) * l * 0.25, y1 + Math.sin(j * 1.6) * l * 0.15, l * 0.28, l * 0.1, nt(S, '#3f7a3a'), j * 1.6);
      for (j = 0; j < 3; j++) { var fx = x1 + (j - 1) * l * 0.18, fy = y1 - l * 0.1; for (var p = 0; p < 5; p++) fe(q, fx + Math.cos(p * 1.257) * l * 0.07, fy + Math.sin(p * 1.257) * l * 0.07, l * 0.06, l * 0.04, nt(S, '#fffaf0', 0.3), p * 1.257); fe(q, fx, fy, l * 0.03, l * 0.03, nt(S, '#f7c64a', 0.3)); } }
  }
  br(x, y, -Math.PI / 2, h * 0.38, 0);
}
function pots(q, x0, x1, y, s, S, R) {
  var n = Math.max(1, Math.floor((x1 - x0) / (s * 0.24)));
  for (var i = 0; i < n; i++) {
    var x = x0 + (i + 0.5) * (x1 - x0) / n, k = Math.floor(R() * 5), ph = s * (0.12 + R() * 0.06);
    if (k === 0) { for (var j = 0; j < 6; j++) paper(q, poly([[x - s * 0.02 + j * s * 0.008, y - ph], [x - s * 0.06 + j * s * 0.025, y - ph - s * (0.22 + R() * 0.15)], [x - s * 0.03 + j * s * 0.02, y - ph]]), nt(S, j % 2 ? '#4f8a3a' : '#7aa04a'), 0.6); }
    else { for (j = 0; j < 9; j++) fe(q, x + (R() - 0.5) * s * 0.18, y - ph - s * (0.04 + R() * 0.14), s * 0.04, s * 0.03, nt(S, j % 2 ? '#3f7a3a' : '#5a9a4a'));
      if (k === 1) for (j = 0; j < 6; j++) fe(q, x + (R() - 0.5) * s * 0.16, y - ph - s * (0.03 + R() * 0.12), s * 0.008, s * 0.025, nt(S, '#d9242b', 0.3), 0.4);
      if (k === 2) for (j = 0; j < 4; j++) fe(q, x + (R() - 0.5) * s * 0.16, y - ph - s * (0.08 + R() * 0.1), s * 0.02, s * 0.02, nt(S, pick(R, ['#f7c64a', '#e5567f', '#ffffff', '#b692ff'])), 0); }
    paper(q, poly([[x - s * 0.08, y - ph], [x + s * 0.08, y - ph], [x + s * 0.06, y], [x - s * 0.06, y]]), nt(S, pick(R, ['#b8643a', '#a85a32', '#5a6a8a', '#e8e2d0', '#3a6a5a'])), 0.8);
  }
}
function jar(q, x, y, s, S) {
  paper(q, function (p) { p.beginPath(); p.moveTo(x - s * 0.08, y); p.bezierCurveTo(x - s * 0.2, y - s * 0.05, x - s * 0.2, y - s * 0.32, x - s * 0.08, y - s * 0.36); p.lineTo(x + s * 0.08, y - s * 0.36); p.bezierCurveTo(x + s * 0.2, y - s * 0.32, x + s * 0.2, y - s * 0.05, x + s * 0.08, y); p.closePath(); }, nt(S, '#6a3a1e'), 1);
  q.strokeStyle = nt(S, '#e8b84a', 0.4); q.lineWidth = Math.max(1, s * 0.018); q.beginPath();
  for (var a = 0; a <= 1; a += 0.05) { var xx = x - s * 0.15 + a * s * 0.3, yy = y - s * 0.18 + Math.sin(a * TAU * 1.5) * s * 0.05; a ? q.lineTo(xx, yy) : q.moveTo(xx, yy); } q.stroke();
}

/* ---------------------------------------------------------------- vehicles, side on: x is the middle, y the road, s the figure height */
function wheel(q, x, y, r, S) { fe(q, x, y - r, r, r, nt(S, '#1e1e22')); fe(q, x, y - r, r * 0.5, r * 0.5, nt(S, '#b8bcc4', 0.4)); fe(q, x, y - r, r * 0.18, r * 0.18, nt(S, '#5a5e66')); }
function scooter(q, x, y, s, col, dir, S, rack) {
  var c = nt(S, col, 0.45), dk = nt(S, '#26262a'), r = s * 0.12, X = function (u) { return x + dir * u * s; }, Y = function (v) { return y - v * s; };
  wheel(q, X(-0.36), y, r, S); wheel(q, X(0.4), y, r, S);
  ln(q, [[X(0.4), Y(0.12)], [X(0.31), Y(0.5)]], nt(S, '#9aa0a8'), Math.max(1.5, s * 0.03));
  paper(q, function (p) { p.beginPath(); p.moveTo(X(-0.56), Y(0.2)); p.quadraticCurveTo(X(-0.6), Y(0.36), X(-0.46), Y(0.41)); p.lineTo(X(-0.02), Y(0.39)); p.quadraticCurveTo(X(0.04), Y(0.3), X(0.02), Y(0.22)); p.lineTo(X(0.22), Y(0.21));
    p.quadraticCurveTo(X(0.26), Y(0.42), X(0.3), Y(0.6)); p.lineTo(X(0.36), Y(0.61)); p.quadraticCurveTo(X(0.45), Y(0.42), X(0.47), Y(0.26)); p.quadraticCurveTo(X(0.4), Y(0.31), X(0.32), Y(0.24));
    p.lineTo(X(0.28), Y(0.15)); p.lineTo(X(-0.02), Y(0.15)); p.quadraticCurveTo(X(-0.25), Y(0.13), X(-0.42), Y(0.17)); p.closePath(); }, c, 0.8);
  fp(q, [[X(-0.5), Y(0.4)], [X(-0.03), Y(0.38)], [X(0), Y(0.44)], [X(-0.44), Y(0.46)]], dk);
  fp(q, [[X(0.02), Y(0.215)], [X(0.22), Y(0.205)], [X(0.23), Y(0.17)], [X(0.02), Y(0.17)]], dk);
  ln(q, [[X(0.24), Y(0.66)], [X(0.4), Y(0.65)]], dk, Math.max(1.5, s * 0.03)); fp(q, [[X(0.28), Y(0.6)], [X(0.38), Y(0.6)], [X(0.37), Y(0.67)], [X(0.29), Y(0.67)]], c);
  ln(q, [[X(0.3), Y(0.67)], [X(0.27), Y(0.76)]], dk, 1); fe(q, X(0.27), Y(0.77), s * 0.022, s * 0.014, dk);
  fe(q, X(0.42), Y(0.47), s * 0.028, s * 0.04, S.night ? '#fff2b0' : '#f2f2e8');
  fe(q, X(-0.57), Y(0.3), s * 0.018, s * 0.014, '#d9342b');
  q.fillStyle = 'rgba(255,255,255,.22)'; q.beginPath(); q.ellipse(X(-0.3), Y(0.3), s * 0.12, s * 0.03, 0, 0, TAU); q.fill();
  if (rack) fr(q, Math.min(X(-0.58), X(-0.36)), Y(0.62), s * 0.22, s * 0.18, nt(S, rack, 0.4));
}
function bicycle(q, x, y, s, col, dir, S, basket) {
  var c = nt(S, col, 0.4), r = s * 0.17, X = function (u) { return x + dir * u * s; };
  q.lineWidth = Math.max(1.2, s * 0.018); q.strokeStyle = nt(S, '#2a2a2e');
  [X(-0.3), X(0.3)].forEach(function (wx) { q.beginPath(); q.arc(wx, y - r, r, 0, TAU); q.stroke(); });
  ln(q, [[X(-0.3), y - r], [X(-0.05), y - r], [X(-0.12), y - s * 0.4], [X(-0.3), y - r]], c, Math.max(1.5, s * 0.025));
  ln(q, [[X(-0.05), y - r], [X(0.2), y - s * 0.38], [X(-0.12), y - s * 0.38]], c, Math.max(1.5, s * 0.025));
  ln(q, [[X(0.3), y - r], [X(0.2), y - s * 0.46], [X(0.16), y - s * 0.48]], c, Math.max(1.5, s * 0.025));
  fe(q, X(-0.13), y - s * 0.42, s * 0.05, s * 0.015, nt(S, '#2a2a2e'));
  if (basket) fr(q, X(0.24) - s * 0.06, y - s * 0.52, s * 0.13, s * 0.08, nt(S, '#b8864a'));
}
/* cars: a sedan, a pickup (the north's truck), a van, a red songthaew, a bus */
function car(q, x, y, s, kind, col, dir, S) {
  var c = nt(S, col, 0.45), gl = S.night ? '#2a3550' : '#8fb4c4', X = function (u) { return x + dir * u * s; }, L = kind === 'bus' ? 2.6 : kind === 'van' ? 1.25 : 1.05, r = s * (kind === 'bus' ? 0.16 : 0.14);
  var h = kind === 'bus' ? 0.95 : kind === 'van' ? 0.62 : kind === 'songthaew' ? 0.66 : 0.46;
  if (kind === 'sedan' || kind === 'pickup') {
    paper(q, poly([[X(-L), y - s * 0.12], [X(-L), y - s * 0.28], [X(-L * 0.55), y - s * 0.3], [X(-L * 0.3), y - s * 0.46], [X(L * 0.25), y - s * 0.46], [X(L * 0.5), y - s * 0.3], [X(L), y - s * 0.26], [X(L), y - s * 0.12]]), c, 1);
    fp(q, [[X(-L * 0.25), y - s * 0.31], [X(-L * 0.12), y - s * 0.43], [X(L * 0.22), y - s * 0.43], [X(L * 0.4), y - s * 0.31]], gl);
    if (kind === 'sedan') fp(q, [[X(-L * 0.5), y - s * 0.31], [X(-L * 0.3), y - s * 0.43], [X(-L * 0.28), y - s * 0.31]], gl);
    else { fr(q, Math.min(X(-L), X(-L * 0.35)), y - s * 0.34, Math.abs(X(-L) - X(-L * 0.35)), s * 0.05, c); }
    ln(q, [[X(-0.02), y - s * 0.31], [X(-0.02), y - s * 0.14]], 'rgba(0,0,0,.3)', 1);
  } else if (kind === 'van') {
    paper(q, poly([[X(-L), y - s * 0.12], [X(-L), y - s * h], [X(L * 0.55), y - s * h], [X(L * 0.85), y - s * 0.38], [X(L), y - s * 0.3], [X(L), y - s * 0.12]]), c, 1);
    for (var i = 0; i < 4; i++) fr(q, Math.min(X(-L * 0.9 + i * 0.36 * L), X(-L * 0.9 + i * 0.36 * L + 0.3 * L)), y - s * (h - 0.06), Math.abs(0.3 * L * s), s * 0.18, gl);
    fp(q, [[X(L * 0.6), y - s * (h - 0.06)], [X(L * 0.82), y - s * 0.4], [X(L * 0.6), y - s * 0.4]], gl);
  } else if (kind === 'songthaew') {
    paper(q, poly([[X(-L), y - s * 0.12], [X(-L), y - s * 0.3], [X(L * 0.15), y - s * 0.3], [X(L * 0.2), y - s * 0.46], [X(L * 0.6), y - s * 0.46], [X(L * 0.75), y - s * 0.3], [X(L), y - s * 0.26], [X(L), y - s * 0.12]]), c, 1);
    paper(q, poly([[X(-L * 1.02), y - s * 0.3], [X(-L * 1.02), y - s * 0.68], [X(L * 0.12), y - s * 0.68], [X(L * 0.12), y - s * 0.3]]), c, 1);
    fr(q, Math.min(X(-L * 0.95), X(L * 0.06)), y - s * 0.62, Math.abs(L * 1.01 * s), s * 0.22, S.night ? '#1a1830' : '#3a2a2a');
    fp(q, [[X(L * 0.25), y - s * 0.32], [X(L * 0.3), y - s * 0.43], [X(L * 0.55), y - s * 0.43], [X(L * 0.66), y - s * 0.32]], gl);
    fr(q, Math.min(X(-L * 0.95), X(L * 0.06)), y - s * 0.7, Math.abs(L * 1.01 * s), s * 0.03, nt(S, '#f2f2f2'));
  } else {
    paper(q, poly([[X(-L), y - s * 0.12], [X(-L), y - s * h], [X(L * 0.95), y - s * h], [X(L), y - s * (h - 0.1)], [X(L), y - s * 0.12]]), c, 1);
    for (i = 0; i < 7; i++) fr(q, Math.min(X(-L * 0.92 + i * 0.27 * L), X(-L * 0.92 + i * 0.27 * L + 0.22 * L)), y - s * (h - 0.08), Math.abs(0.22 * L * s), s * 0.26, gl);
    fr(q, Math.min(X(-L), X(L)), y - s * 0.42, 2 * L * s, s * 0.05, nt(S, '#f2f2f2'));
  }
  fe(q, X(L - 0.02), y - s * 0.24, s * 0.035, s * 0.025, S.night ? '#fff2b0' : '#f2f2e8');
  wheel(q, X(-L * 0.62), y, r, S); wheel(q, X(L * 0.62), y, r, S);
}

/* ---------------------------------------------------------------- animals, alive: the soi dog asleep (it breathes), the cat on a stool (its tail), hens */
var DOGS = ['#c9925a', '#e8d2b0', '#3a2a22', '#a8743a', '#f2ead8', '#7a5a3a'];
function dog(c, x, y, s, col, t, k, awake) {
  var b = 1 + 0.035 * Math.sin(t / 700 + k), dk = mixc(col, '#000000', 0.3);
  if (!awake) {
    fe(c, x, y - s * 0.07 * b, s * 0.2, s * 0.08 * b, col);
    fe(c, x + s * 0.18, y - s * 0.05, s * 0.08, s * 0.055, col);
    fe(c, x + s * 0.24, y - s * 0.035, s * 0.04, s * 0.025, dk);
    fe(c, x + s * 0.15, y - s * 0.09, s * 0.03, s * 0.045, dk, -0.6);
    c.strokeStyle = col; c.lineWidth = Math.max(1.5, s * 0.035); c.lineCap = 'round'; c.beginPath(); c.moveTo(x - s * 0.18, y - s * 0.06); c.quadraticCurveTo(x - s * 0.3, y - s * 0.02, x - s * 0.15, y - s * 0.01); c.stroke();
    var u = (t / 3000 + k) % 1; if (u < 0.6) { c.fillStyle = 'rgba(255,255,255,' + (0.7 * Math.sin(u / 0.6 * Math.PI)).toFixed(2) + ')'; c.font = '700 ' + Math.round(Math.max(8, s * 0.09)) + 'px ' + FONT; c.textAlign = 'center'; c.fillText('z', x + s * 0.22, y - s * (0.16 + u * 0.2)); }
  } else {
    var w = Math.sin(t / 140 + k) * 0.6;
    fe(c, x, y - s * 0.14, s * 0.13, s * 0.08, col, -0.5);
    c.strokeStyle = col; c.lineWidth = Math.max(1.5, s * 0.03); c.lineCap = 'round';
    c.beginPath(); c.moveTo(x + s * 0.06, y - s * 0.18); c.lineTo(x + s * 0.08, y); c.moveTo(x - s * 0.08, y - s * 0.08); c.lineTo(x - s * 0.06, y); c.stroke();
    c.beginPath(); c.moveTo(x - s * 0.11, y - s * 0.1); c.lineTo(x - s * 0.11 - Math.cos(w) * s * 0.1, y - s * 0.12 - Math.sin(Math.abs(w) + 0.6) * s * 0.08); c.stroke();
    fe(c, x + s * 0.1, y - s * 0.27, s * 0.065, s * 0.055, col); fe(c, x + s * 0.16, y - s * 0.25, s * 0.035, s * 0.025, col);
    fe(c, x + s * 0.07, y - s * 0.31, s * 0.025, s * 0.04, dk, -0.3); fe(c, x + s * 0.19, y - s * 0.25, s * 0.012, s * 0.012, '#1a1a1a');
  }
}
function cat(c, x, y, s, col, t, k) {
  var dk = mixc(col, '#000000', 0.25), sw = Math.sin(t / 800 + k) * 0.5 + Math.sin(t / 230 + k) * 0.12;
  fe(c, x, y - s * 0.08, s * 0.09, s * 0.08, col);
  fe(c, x + s * 0.05, y - s * 0.19, s * 0.055, s * 0.05, col);
  fp(c, [[x + s * 0.01, y - s * 0.22], [x + s * 0.02, y - s * 0.28], [x + s * 0.05, y - s * 0.23]], col);
  fp(c, [[x + s * 0.06, y - s * 0.23], [x + s * 0.09, y - s * 0.28], [x + s * 0.1, y - s * 0.21]], col);
  c.strokeStyle = col; c.lineWidth = Math.max(1.4, s * 0.025); c.lineCap = 'round'; c.beginPath(); c.moveTo(x - s * 0.08, y - s * 0.03);
  c.quadraticCurveTo(x - s * 0.18, y - s * 0.02, x - s * 0.17 + Math.sin(sw) * s * 0.05, y - s * (0.12 + 0.04 * Math.cos(sw))); c.stroke();
  fe(c, x + s * 0.07, y - s * 0.2, s * 0.008, s * 0.008, '#3a5a2a');
  if (col !== dk) { fe(c, x - s * 0.02, y - s * 0.1, s * 0.03, s * 0.025, dk); }
}
function hen(c, x, y, s, t, k, col) {
  var u = Math.max(0, Math.sin(t / 380 + k * 2)), hx = x + s * 0.08, hy = y - s * 0.16 + u * s * 0.12;
  fe(c, x, y - s * 0.1, s * 0.09, s * 0.065, col); fp(c, [[x - s * 0.08, y - s * 0.12], [x - s * 0.15, y - s * 0.2], [x - s * 0.1, y - s * 0.08]], mixc(col, '#000000', 0.3));
  ln(c, [[x + s * 0.04, y - s * 0.12], [hx, hy]], col, Math.max(1.5, s * 0.04)); fe(c, hx, hy, s * 0.03, s * 0.028, col);
  fp(c, [[hx + s * 0.025, hy], [hx + s * 0.05, hy + s * 0.01], [hx + s * 0.025, hy + s * 0.015]], '#e8b84a'); fe(c, hx, hy - s * 0.03, s * 0.015, s * 0.012, '#d9242b');
  ln(c, [[x, y - s * 0.04], [x, y]], '#e8b84a', 1);
}
function moth(c, x, y, s, t) {
  var a = t / 260, mx = x + Math.cos(a) * s * 0.1 + Math.sin(a * 2.3) * s * 0.03, my = y + Math.sin(a * 1.3) * s * 0.06, fl = Math.abs(Math.sin(t / 30));
  c.fillStyle = 'rgba(240,230,200,.85)'; c.beginPath(); c.ellipse(mx - s * 0.012, my, s * 0.014, s * 0.008 + fl * s * 0.008, -0.6, 0, TAU); c.ellipse(mx + s * 0.012, my, s * 0.014, s * 0.008 + fl * s * 0.008, 0.6, 0, TAU); c.fill();
}
/* the khom, the Lanna hanging lantern: a twelve-sided drum with paper fins and a tassel; it sways,
   θ = θ₀·sin(2πt/T), and glows by night */
function khom(c, x, y, s, col, t, k, lit) {
  var th = 0.07 * Math.sin(t / 1300 + k * 1.7), L = s * 0.1, cx = x + Math.sin(th) * L, cy = y + Math.cos(th) * L;
  ln(c, [[x, y], [cx, cy]], 'rgba(40,25,10,.8)', 1);
  if (lit) glow(c, cx, cy + s * 0.08, s * 0.22, '255,190,90', 0.7 + 0.12 * Math.sin(t / 170 + k));
  c.save(); c.translate(cx, cy); c.rotate(th);
  fp(c, [[-s * 0.05, 0], [s * 0.05, 0], [s * 0.07, s * 0.05], [s * 0.05, s * 0.12], [-s * 0.05, s * 0.12], [-s * 0.07, s * 0.05]], col);
  fp(c, [[-s * 0.07, s * 0.05], [-s * 0.11, s * 0.075], [-s * 0.06, s * 0.08]], col); fp(c, [[s * 0.07, s * 0.05], [s * 0.11, s * 0.075], [s * 0.06, s * 0.08]], col);
  fr(c, -s * 0.05, s * 0.03, s * 0.1, s * 0.012, '#f2c94c'); fr(c, -s * 0.05, s * 0.09, s * 0.1, s * 0.012, '#f2c94c');
  ln(c, [[0, s * 0.12], [0, s * 0.2]], col, Math.max(1, s * 0.015)); fe(c, 0, s * 0.21, s * 0.012, s * 0.02, '#f2c94c');
  if (lit) fe(c, 0, s * 0.06, s * 0.03, s * 0.035, 'rgba(255,240,190,.75)');
  c.restore();
}

/* ---------------------------------------------------------------- the building */
var TYPES = { shop: 5, row: 2.2, teak: 1, glass: 1.4, stall: 0.8, lanna: 0.5 };
function signSize(S, F) {
  var hh = S.hh, th = F.nameTh || F.name || '', en = F.nameEn && F.nameEn !== th ? F.nameEn : '', c = S.c;
  var f1 = Math.max(11, hh * 0.19), f2 = Math.max(9, hh * 0.13);
  c.save(); c.font = '800 ' + Math.round(f1) + 'px ' + FONT; var w1 = c.measureText(th.length > 34 ? th.slice(0, 33) + '…' : th).width;
  c.font = '700 ' + Math.round(f2) + 'px ' + FONT; var w2 = en ? c.measureText(en.length > 40 ? en.slice(0, 39) + '…' : en).width : 0; c.restore();
  return { w: Math.min(Math.max(w1, w2) + hh * 0.5, hh * 7), h: en ? f1 + f2 + hh * 0.18 : f1 + hh * 0.16 };
}
/* the plan, dealt once per place and state: type, size, colours, bays, doors, what stands out front */
function plan(S, spec, st) {
  var R = rnd((S.seed ^ 0x9e3779b9) >>> 0), hh = S.hh, F = S.place || {}, d = S.deck;
  var V = spec.look ? spec.look(S, F, R) : {};
  var L = { R: R, V: V, st: st, open: st === 'open', hh: hh, F: F };
  L.type = F.inside && !V.noUnit ? 'unit' : V.type || deal(R, V.types || TYPES);
  L.sg = signSize(S, F);
  var edge = hh * 0.85, room = S.span - edge * 2;
  L.bw = Math.min(room * (S.phone ? 0.92 : 0.7), Math.max(hh * (V.w || (3.7 + R() * 1.7)), Math.min(L.sg.w + hh * 0.3, room * 0.8)));
  if (L.type === 'stall') L.bw = Math.min(L.bw, hh * 3.8);
  var u = V.at != null ? V.at : 0.12 + R() * 0.76;
  L.bx0 = S.x0 + edge + (room - L.bw) * u; L.bx1 = L.bx0 + L.bw;
  L.gf = hh * (L.type === 'stall' ? 1.2 : 1.3);
  var nb = L.type === 'stall' ? 1 : L.bw > hh * 5.2 && R() < 0.5 ? 3 : L.bw > hh * 3.9 ? 2 : 1;
  L.pil = hh * (L.type === 'teak' || L.type === 'lanna' ? 0.11 : L.type === 'stall' ? 0.07 : L.type === 'glass' ? 0.06 : 0.15);
  L.bays = []; for (var i = 0; i < nb; i++) { var a = L.bx0 + L.pil + i * (L.bw - L.pil) / nb, b = L.bx0 + (i + 1) * (L.bw - L.pil) / nb; L.bays.push({ x0: a, x1: b }); }
  L.in = { x0: L.bx0 + L.pil, x1: L.bx1 - L.pil, y0: d - L.gf + hh * 0.1, y1: d };
  L.storeys = L.type === 'shop' ? (R() < 0.5 ? 2 : 3) : L.type === 'glass' ? (R() < 0.55 ? 1 : 2) : 1;
  L.uf = hh * 0.46;
  var cap = d - hh * 2.28;
  if (L.type === 'shop') L.top = Math.max(cap, d - L.gf - L.uf * (L.storeys - 1) - hh * 0.08);
  else if (L.type === 'row') L.top = d - L.gf - L.sg.h - hh * 0.16;
  else if (L.type === 'glass') L.top = Math.max(cap, d - L.gf - L.sg.h - hh * 0.12 - (L.storeys - 1) * hh * 0.42);
  else if (L.type === 'teak') L.top = d - hh * 2.24;
  else if (L.type === 'lanna') L.top = d - hh * 2.2;
  else if (L.type === 'stall') L.top = d - L.gf - hh * 0.32;
  else L.top = d - L.gf - L.sg.h - hh * 0.1;
  L.wall = V.wall || (L.type === 'glass' ? pick(R, ['#f2f2ee', '#e2e4e6', '#3a3d44', '#d8d2c4', '#f6efe0']) : pick(R, WALLS));
  L.trim = V.trim || pick(R, TRIMS); L.shutCol = pick(R, SHUT); L.awnCol = V.awn || pick(R, AWN); L.board = V.board || pick(R, BOARD);
  L.door = V.door || (L.type === 'teak' || L.type === 'lanna' ? 'fold' : L.type === 'stall' ? 'tarp' : L.type === 'glass' || L.type === 'unit' ? 'glass' : R() < 0.8 ? 'roll' : 'fold');
  L.awn = V.awning || (L.type === 'shop' || L.type === 'row' ? deal(R, { stripe: 3, zinc: 2, none: 1.4, scallop: 1.6 }) : 'none');
  L.win = pick(R, ['slide', 'louvre', 'grille', 'slide', 'grille']); L.balcony = R() < 0.5; L.ac = R() < 0.6; L.crest = R() < 0.55;
  L.light = V.light || (R() < 0.5 ? 'warm' : 'cool');
  L.inWall = V.inWall || (L.light === 'warm' ? '#f3e2bf' : '#e3ece6');
  L.floor = V.floor || pick(R, ['#c9b89a', '#d8d2c4', '#b8a888', '#cfc8b8', '#a89070']);
  /* the shutters: up when open, down when shut, mostly down and lit beneath when quiet */
  L.shut = L.bays.map(function (b, k) { return st === 'open' ? 0 : st === 'closed' ? 1 : k === 0 && nb > 1 ? 1 : 0.74; });
  /* the name board */
  L.signAt = V.signAt || (L.type === 'stall' || L.type === 'unit' ? 'face' : R() < 0.16 ? 'stand' : 'face');
  L.signY = L.type === 'stall' ? d - L.gf - L.sg.h * 0.55 : L.type === 'teak' ? d - L.gf - L.sg.h - hh * 0.06 : d - L.gf - L.sg.h - hh * 0.06;
  if (L.type === 'lanna') L.signY = d - L.gf - L.sg.h - hh * 0.03;
  L.signX = (L.bx0 + L.bx1) / 2;
  var leftRoom = L.bx0 - S.x0 - edge * 0.6, rightRoom = S.x1 - edge * 0.6 - L.bx1;
  if (L.signAt === 'stand') { var sw = L.sg.w + hh * 0.3; if (Math.max(leftRoom, rightRoom) < sw * 0.7) L.signAt = 'face';
    else { L.standLeft = leftRoom > rightRoom; L.signX = L.standLeft ? Math.max(S.x0 + L.sg.w / 2 + hh * 0.2, L.bx0 - L.sg.w * 0.3) : Math.min(S.x1 - L.sg.w / 2 - hh * 0.2, L.bx1 + L.sg.w * 0.3); L.signY = d - hh * 0.75 - L.sg.h; } }
  L.signX = clamp(L.signX, S.x0 + L.sg.w / 2 + 4, S.x1 - L.sg.w / 2 - 4);
  /* what stands out front */
  var sides = [{ a: S.x0 + edge * 0.7, b: L.bx0 - hh * 0.08 }, { a: L.bx1 + hh * 0.08, b: S.x1 - edge * 0.7 }];
  if (L.signAt === 'stand') sides[L.standLeft ? 0 : 1].b = sides[L.standLeft ? 0 : 1].a - 1;
  L.sides = sides;
  var sp = V.noSpirit ? null : R() < 0.66 ? (sides[0].b - sides[0].a > sides[1].b - sides[1].a ? 0 : 1) : -1;
  if (sp != null && sp >= 0 && sides[sp].b - sides[sp].a > hh * 0.45) { var s0 = sides[sp]; L.spirit = { x: sp === 0 ? Math.max(s0.a + hh * 0.3, s0.b - hh * 0.35) : Math.min(s0.b - hh * 0.3, s0.a + hh * 0.35), kind: R() < 0.45 ? 'lanna' : 'gold' }; }
  else if (sp === -1 || sp != null) { L.spirit = R() < 0.4 && !V.noSpirit ? { x: R() < 0.5 ? L.bx0 + hh * 0.3 : L.bx1 - hh * 0.3, kind: 'gold', front: true } : null; }
  L.plants = []; var pk = ['boug', 'banana', 'frangi', 'pots', 'jar', 'boug', 'pots'];
  for (i = 0; i < 2; i++) { var sd = sides[i], free = sd.b - sd.a - (L.spirit && !L.spirit.front && (L.spirit.x > sd.a && L.spirit.x < sd.b) ? hh * 0.7 : 0);
    if (free > hh * 0.35 && R() < 0.8) L.plants.push({ k: pick(R, pk), x: i === 0 ? sd.a + (L.spirit && L.spirit.x < sd.b && L.spirit.x > sd.a ? 0 : free * 0.3) : sd.b - free * 0.35, side: i, w: Math.min(free, hh * 0.8) }); }
  if (R() < 0.45 && L.type !== 'unit') L.plants.push({ k: R() < 0.5 ? 'pots' : 'boug', x: R() < 0.5 ? L.bx0 + L.pil * 0.5 : L.bx1 - L.pil * 0.5, side: 2, w: hh * 0.5 });
  L.bikes = []; var nbk = V.bikes != null ? V.bikes : Math.floor(R() * 2.6), spots = [L.bx0 + hh * 0.45, L.bx1 - hh * 0.45, sides[0].b - hh * 0.5, sides[1].a + hh * 0.5].filter(function (x, k) { return k < 2 || (k === 2 ? sides[0].b - sides[0].a > hh * 1.2 : sides[1].b - sides[1].a > hh * 1.2); });
  for (i = 0; i < nbk && spots.length; i++) { var si = Math.floor(R() * spots.length), bx = spots.splice(si, 1)[0]; L.bikes.push({ x: bx, col: pick(R, BIKE), dir: R() < 0.5 ? 1 : -1, kind: R() < 0.12 ? 'bicycle' : 'scooter' }); }
  L.pole = V.noPole || L.type === 'unit' ? null : R() < 0.55 ? { x: R() < 0.5 ? L.bx0 - hh * 0.15 : L.bx1 + hh * 0.15 } : null;
  L.lanterns = []; var nl = V.lanterns != null ? V.lanterns : R() < 0.6 || S.night ? 2 + Math.floor(R() * 3) : 0;
  var lcol = pick(R, [['#d9342b', '#f08a3a'], ['#f2c94c', '#e5567f'], ['#d9342b', '#d9342b'], ['#f08a3a', '#f2c94c'], ['#4fae8c', '#f2c94c']]);
  for (i = 0; i < nl; i++) L.lanterns.push({ x: lerp(L.bx0 + hh * 0.2, L.bx1 - hh * 0.2, nl === 1 ? 0.5 : i / (nl - 1)), col: lcol[i % 2] });
  L.marigold = R() < 0.45; L.lai = R() < 0.6;
  var moo = F.moo && !F.oldCity;
  L.animal = st !== 'open' ? (R() < 0.6 ? 'dog' : 'cat') : moo && R() < 0.5 ? 'hens' : deal(R, { dog: 2, cat: 2, none: 1.5 });
  L.animalX = lerp(L.bx0 + hh * 0.4, L.bx1 - hh * 0.4, R()); L.animalCol = pick(R, DOGS);
  L.walkers = st === 'open' || !S.night ? Math.floor(R() * (S.phone ? 1.6 : 2.6)) : 0;
  L.folk = crew(S, 8, V.mix, 11);
  L.plate = F.road ? (R() < 0.5 ? 0 : 1) : -1;
  L.curb = pick(R, [['#c0392b', '#f2f2f2'], ['#e8b84a', '#f2f2f2'], ['#9a9a9a', '#9a9a9a'], ['#9a9a9a', '#9a9a9a']]);
  L.walk = pick(R, ['#cbbfa8', '#b9b1a3', '#d6c7a8', '#c2b8b0', '#a99c8a']);
  if (spec.plan) spec.plan(S, L, V, R);
  return L;
}

/* the ground: pavement tiles, a painted kerb, the road, then the place's own setting */
function backdrop(q, S, L) {
  var hh = S.hh, d = S.deck, F = S.place || {}, x0 = S.x0 - 6, w = S.span + 12, ry = d + hh * 0.2;
  if (L.type === 'unit' || L.V.mallFloor) { mallBack(q, S, L); return; }
  paper(q, rect(x0, d - 2, w, S.H - d + 8), nt(S, L.walk, 0.55), 1);
  q.strokeStyle = 'rgba(0,0,0,.12)'; q.lineWidth = 1; q.beginPath();
  for (var x = S.x0; x < S.x1; x += hh * 0.22) { q.moveTo(x, d); q.lineTo(x - hh * 0.05, ry); } q.moveTo(S.x0, d + hh * 0.1); q.lineTo(S.x1, d + hh * 0.1); q.stroke();
  fr(q, x0, ry, w, S.H - ry + 4, nt(S, '#55565e', 0.4));
  for (x = S.x0, i = 0; x < S.x1; x += hh * 0.25, i++) fr(q, x, ry - hh * 0.03, hh * 0.25, hh * 0.05, nt(S, L.curb[i % 2], 0.5));
  if (!(F.river && F.river.m < 400)) for (x = S.x0 + hh * 0.2; x < S.x1; x += hh * 0.8) fr(q, x, ry + (S.H - ry) * 0.55, hh * 0.4, Math.max(1.5, hh * 0.025), nt(S, '#e8e2d0', 0.5));
  var i;
  var Sq = {}; for (var k in S) Sq[k] = S[k]; Sq.c = q; Sq.t = 0; K.setting(Sq);
}
/* inside a mall: a polished floor, the gallery above with its rail, a glass roof on arches, the neighbours' fronts */
function mallBack(q, S, L) {
  var hh = S.hh, d = S.deck, x0 = S.x0 - 6, w = S.span + 12, gy = d - hh * 2.25, R = rnd(S.seed + 5);
  var wall = nt(S, '#efe9de', 0.25), g = q.createLinearGradient(0, 0, 0, d);
  q.save(); q.globalAlpha = 0.9; q.strokeStyle = nt(S, '#d8d2c4', 0.3); q.lineWidth = Math.max(2, hh * 0.04);
  for (var x = S.x0 + hh * 0.6; x < S.x1; x += hh * 1.6) { if (S.avoid && Math.abs(x - S.avoid.cx) < S.avoid.r) continue; q.beginPath(); q.moveTo(x - hh * 0.8, gy - hh * 0.2); q.quadraticCurveTo(x, gy - hh * 2.4, x + hh * 0.8, gy - hh * 0.2); q.stroke(); }
  q.restore();
  g.addColorStop(0, nt(S, '#f6f1e6', 0.3)); g.addColorStop(1, wall);
  q.fillStyle = g; q.fillRect(x0, gy - hh * 0.25, w, d - gy + hh * 0.25);
  for (x = S.x0 - hh * 0.3; x < S.x1; x += hh * 1.3) { fr(q, x + hh * 0.05, gy - hh * 0.22, hh * 1.2, hh * 0.18, nt(S, pick(R, ['#c9e0e8', '#f2d4cf', '#e8e0c0', '#d8e8d0']), 0.3)); }
  paper(q, rect(x0, gy - hh * 0.04, w, hh * 0.1), nt(S, '#d8d2c4', 0.3), 1);
  q.strokeStyle = 'rgba(160,200,215,.55)'; q.lineWidth = 1; q.fillStyle = 'rgba(190,225,235,.25)'; q.fillRect(x0, gy - hh * 0.32, w, hh * 0.28);
  for (x = S.x0; x < S.x1; x += hh * 0.5) { q.beginPath(); q.moveTo(x, gy - hh * 0.32); q.lineTo(x, gy - hh * 0.04); q.stroke(); }
  fr(q, x0, gy - hh * 0.34, w, hh * 0.03, nt(S, '#b8b0a0', 0.3));
  for (x = S.x0 + hh * 0.4; x < S.x1; x += hh * 1.1) { fr(q, x, gy + hh * 0.06, hh * 0.3, hh * 0.025, '#fffbe8'); }
  for (x = S.x0 - hh; x < S.x1 + hh; x += hh * 1.9) {
    var nx = x + hh * 0.1, nw = hh * 1.7;
    fr(q, nx, d - hh * 1.5, nw, hh * 1.5, nt(S, pick(R, ['#e8e2d0', '#d9e8e4', '#f0dcd0', '#e4e0f0']), 0.3));
    fr(q, nx + hh * 0.08, d - hh * 1.2, nw - hh * 0.16, hh * 1.2, nt(S, '#cfe3ea', 0.3));
    for (var j = 0; j < 4; j++) fr(q, nx + hh * (0.2 + j * 0.36), d - hh * (0.5 + (j % 2) * 0.2), hh * 0.2, hh * 0.3, nt(S, pick(R, CLOTHS), 0.3));
    fr(q, nx, d - hh * 1.48, nw, hh * 0.2, nt(S, pick(R, BOARD), 0.3));
  }
  paper(q, rect(x0, d - 2, w, S.H - d + 8), nt(S, '#e8e2d6', 0.3), 1);
  q.fillStyle = 'rgba(255,255,255,.25)'; for (x = S.x0; x < S.x1; x += hh * 0.9) q.fillRect(x, d + hh * 0.03, hh * 0.45, S.H - d);
  q.strokeStyle = 'rgba(0,0,0,.08)'; q.beginPath(); for (x = S.x0; x < S.x1; x += hh * 0.45) { q.moveTo(x, d); q.lineTo(x - hh * 0.2, S.H); } q.stroke();
}
var CLOTHS = ['#ffc266', '#ff5a8c', '#b692ff', '#7fe0a4', '#7fd8ff', '#ff9a5a', '#f2f2f2', '#e5567f', '#4fae8c', '#e2b33c', '#9b6bd6', '#f08a5d', '#6cc3c1', '#2c3e6b', '#c0392b'];

/* the room behind the bays: its wall, its floor, the strip lights and their light */
function room(q, S, L) {
  var I = L.in, hh = S.hh, d = S.deck, lit = L.open, wall = lit ? (S.night ? L.inWall : mixc(L.inWall, '#7a6a5a', 0.25)) : nt(S, '#3a3640', 0.3);
  if (L.type === 'stall') { fr(q, I.x0, I.y0 - hh * 0.1, I.x1 - I.x0, I.y1 - I.y0 + hh * 0.1, nt(S, '#c9a66b', 0.45)); q.strokeStyle = nt(S, '#9a7a4a', 0.45); q.lineWidth = 1;
    for (var x = I.x0; x < I.x1; x += hh * 0.08) { q.beginPath(); q.moveTo(x, I.y0 - hh * 0.1); q.lineTo(x + hh * 0.3, I.y1); q.moveTo(x + hh * 0.3, I.y0 - hh * 0.1); q.lineTo(x, I.y1); q.stroke(); } return; }
  fr(q, I.x0, I.y0 - hh * 0.12, I.x1 - I.x0, I.y1 - I.y0 + hh * 0.12, wall);
  fr(q, I.x0, d - hh * 0.12, I.x1 - I.x0, hh * 0.12, lit ? mixc(L.floor, '#000000', S.night ? 0 : 0.15) : nt(S, '#2a2830', 0.3));
  var g = q.createLinearGradient(0, I.y0 - hh * 0.12, 0, I.y0 + hh * 0.35); g.addColorStop(0, 'rgba(0,0,0,.28)'); g.addColorStop(1, 'rgba(0,0,0,0)'); q.fillStyle = g; q.fillRect(I.x0, I.y0 - hh * 0.12, I.x1 - I.x0, hh * 0.47);
  if (lit && L.V.tubes !== false) for (var b = 0; b < L.bays.length; b++) { var bx = (L.bays[b].x0 + L.bays[b].x1) / 2;
    fr(q, bx - hh * 0.3, I.y0 - hh * 0.06, hh * 0.6, hh * 0.035, L.light === 'warm' ? '#fff1c8' : '#f4fbff'); if (S.night) glow(q, bx, I.y0, hh * 0.9, L.light === 'warm' ? '255,226,160' : '220,240,255', 0.35); }
}

/* the front: pillars, beam, floors above, shutters or doors, awning, the name board */
function facade(q, S, L, spec) {
  var t = L.type;
  if (L.V.custom) { L.V.custom(q, S, L); if (!L.V.noBoard) boardUp(q, S, L); return; }
  if (L.V.facade) L.V.facade(q, S, L); else if (t === 'shop') fShop(q, S, L); else if (t === 'row') fRow(q, S, L); else if (t === 'glass' || t === 'unit') fGlass(q, S, L);
  else if (t === 'teak') fTeak(q, S, L); else if (t === 'lanna') fLanna(q, S, L); else fStall(q, S, L);
  if (L.V.wallArt) L.V.wallArt(q, S, L);
  doors(q, S, L);
  awning(q, S, L);
  boardUp(q, S, L);
}
function pillars(q, S, L, col, lift) {
  var d = S.deck, hh = S.hh, xs = [L.bx0 + L.pil / 2]; L.bays.forEach(function (b, i) { if (i < L.bays.length - 1) xs.push((b.x1 + L.bays[i + 1].x0) / 2); }); xs.push(L.bx1 - L.pil / 2);
  xs.forEach(function (x) { paper(q, rect(x - L.pil / 2, d - L.gf - hh * 0.02, L.pil, L.gf + hh * 0.02), col, lift || 1.1); });
}
function windows(q, S, L, x0, x1, y0, y1, k) {
  var hh = S.hh, w = x1 - x0, h = y1 - y0, fx = x0 + w * 0.18, fw = w * 0.64, fy = y0 + h * 0.18, fh = h * 0.62, R = rnd(S.seed + k * 13);
  var lit = S.night && R() < 0.45, glass = lit ? '#ffd98a' : nt(S, '#8fb4c4', 0.55);
  fr(q, fx - 2, fy - 2, fw + 4, fh + 4, nt(S, '#f2f2ee', 0.5));
  if (L.win === 'louvre') { fr(q, fx, fy, fw, fh, lit ? '#ffd98a' : nt(S, '#3a2a22')); var lc = nt(S, L.trim, 0.45);
    [fx, fx + fw * 0.75].forEach(function (sx) { fr(q, sx - fw * 0.25, fy, fw * 0.5, fh, lc); for (var i = 1; i < 7; i++) fr(q, sx - fw * 0.25, fy + i * fh / 7, fw * 0.5, 1, 'rgba(0,0,0,.25)'); }); }
  else { fr(q, fx, fy, fw, fh, glass); fr(q, fx + fw / 2 - 1, fy, 2, fh, nt(S, '#d8dade', 0.5)); q.fillStyle = 'rgba(255,255,255,.25)'; q.beginPath(); q.moveTo(fx + fw * 0.1, fy + fh); q.lineTo(fx + fw * 0.35, fy); q.lineTo(fx + fw * 0.45, fy); q.lineTo(fx + fw * 0.2, fy + fh); q.fill(); }
  if (L.win === 'grille') { q.strokeStyle = nt(S, '#f2f2ee', 0.5); q.lineWidth = 1; q.beginPath(); var cx = fx + fw / 2, cy = fy + fh;
    for (var a = 0; a <= 8; a++) { var an = Math.PI + a * Math.PI / 8; q.moveTo(cx, cy); q.lineTo(cx + Math.cos(an) * fw * 0.6, cy + Math.sin(an) * fh); } q.moveTo(cx + fw * 0.25, cy); q.arc(cx, cy, fw * 0.25, 0, Math.PI, true); q.stroke(); }
  if (L.balcony && k % 2 === 0) { fr(q, x0 + w * 0.08, y1 - h * 0.32, w * 0.84, 2, nt(S, '#f2f2ee', 0.5)); for (var i = 0; i <= 10; i++) fr(q, x0 + w * 0.08 + i * w * 0.084, y1 - h * 0.32, 1.5, h * 0.3, nt(S, '#f2f2ee', 0.5));
    if (R() < 0.5) { var cy2 = y1 - h * 0.45; ln(q, [[x0 + w * 0.12, cy2], [x0 + w * 0.88, cy2]], 'rgba(60,60,60,.6)', 1); for (i = 0; i < 4; i++) fp(q, [[x0 + w * (0.2 + i * 0.17), cy2], [x0 + w * (0.31 + i * 0.17), cy2], [x0 + w * (0.3 + i * 0.17), cy2 + h * 0.25], [x0 + w * (0.21 + i * 0.17), cy2 + h * 0.25]], nt(S, pick(R, CLOTHS), 0.5)); }
    else pots(q, x0 + w * 0.15, x0 + w * 0.45, y1 - h * 0.32, hh * 0.6, S, R); }
  if (L.ac && k % 3 === 1) { fr(q, x1 - w * 0.2, y1 - h * 0.42, w * 0.16, h * 0.32, nt(S, '#e8e8e2', 0.5)); q.strokeStyle = 'rgba(0,0,0,.3)'; q.beginPath(); q.arc(x1 - w * 0.12, y1 - h * 0.26, h * 0.1, 0, TAU); q.stroke(); }
}
function fShop(q, S, L) {
  var hh = S.hh, d = S.deck, wall = nt(S, L.wall, 0.45), dark = mixc(wall, '#000000', 0.14), x0 = L.bx0, x1 = L.bx1;
  paper(q, rect(x0, L.top, x1 - x0, d - L.gf - L.top + 2), wall, 1.6);
  for (var f = 1; f < L.storeys; f++) { var fy1 = d - L.gf - (f - 1) * L.uf, fy0 = Math.max(L.top + hh * 0.08, fy1 - L.uf);
    fr(q, x0, fy1 - 2, x1 - x0, 3, dark);
    L.bays.forEach(function (b, i) { windows(q, S, L, b.x0, b.x1, fy0, fy1, f * 3 + i); }); }
  fr(q, x0 - hh * 0.05, L.top, x1 - x0 + hh * 0.1, hh * 0.06, dark);
  if (L.crest) { var cx = (x0 + x1) / 2, cw = Math.min(hh * 0.9, (x1 - x0) * 0.3);
    paper(q, poly([[cx - cw / 2, L.top + 1], [cx - cw / 2, L.top - hh * 0.06], [cx - cw * 0.3, L.top - hh * 0.06], [cx - cw * 0.3, L.top - hh * 0.1], [cx + cw * 0.3, L.top - hh * 0.1], [cx + cw * 0.3, L.top - hh * 0.06], [cx + cw / 2, L.top - hh * 0.06], [cx + cw / 2, L.top + 1]]), wall, 1);
    if (L.storeys > 1) { var pw2 = Math.min(cw * 0.6, hh * 0.45); q.strokeStyle = nt(S, '#8a7a6a', 0.4); q.lineWidth = 1; q.strokeRect(cx - pw2 / 2, L.top + hh * 0.07, pw2, hh * 0.08); fe(q, cx, L.top + hh * 0.11, hh * 0.025, hh * 0.025, nt(S, '#8a7a6a', 0.4)); } }
  pillars(q, S, L, mixc(wall, '#000000', 0.06));
  paper(q, rect(x0 - hh * 0.03, d - L.gf - hh * 0.05, x1 - x0 + hh * 0.06, hh * 0.1), dark, 1.2);
}
function fRow(q, S, L) {
  var hh = S.hh, d = S.deck, wall = nt(S, L.wall, 0.45), dark = mixc(wall, '#000000', 0.14), x0 = L.bx0, x1 = L.bx1;
  paper(q, poly([[x0 - hh * 0.15, L.top + hh * 0.06], [x0 + hh * 0.1, L.top - hh * 0.1], [x1 - hh * 0.1, L.top - hh * 0.1], [x1 + hh * 0.15, L.top + hh * 0.06]]), nt(S, '#8a8f99', 0.4), 1.2);
  paper(q, rect(x0, L.top, x1 - x0, d - L.gf - L.top + 2), wall, 1.5);
  fr(q, x0, L.top, x1 - x0, hh * 0.04, dark);
  pillars(q, S, L, mixc(wall, '#000000', 0.06));
  paper(q, rect(x0 - hh * 0.03, d - L.gf - hh * 0.05, x1 - x0 + hh * 0.06, hh * 0.09), dark, 1.2);
}
function fGlass(q, S, L) {
  var hh = S.hh, d = S.deck, wall = nt(S, L.wall, 0.4), x0 = L.bx0, x1 = L.bx1, dk = L.wall === '#3a3d44';
  paper(q, rect(x0, L.top, x1 - x0, d - L.gf - L.top), wall, 1.6);
  if (L.storeys > 1) { var by = L.top + hh * 0.1; fr(q, x0 + hh * 0.12, by, x1 - x0 - hh * 0.24, hh * 0.24, S.night ? (S.seed % 2 ? '#ffe6a8' : '#2a3550') : nt(S, '#6f8fa0'));
    for (var x = x0 + hh * 0.12; x < x1 - hh * 0.12; x += hh * 0.4) fr(q, x, by, 1.5, hh * 0.24, wall); }
  /* the canopy slab and its downlights */
  paper(q, rect(x0 - hh * 0.18, d - L.gf - hh * 0.06, x1 - x0 + hh * 0.36, hh * 0.08), nt(S, dk ? '#2a2c30' : '#d8dade', 0.4), 1.4);
  if (L.open && S.night) for (x = x0; x < x1; x += hh * 0.6) glow(q, x + hh * 0.3, d - L.gf + hh * 0.02, hh * 0.25, '255,236,190', 0.6);
  fr(q, x0, d - L.gf - hh * 0.02, L.pil, L.gf, wall); fr(q, x1 - L.pil, d - L.gf - hh * 0.02, L.pil, L.gf, wall);
}
function glassPanes(q, S, L) {
  var hh = S.hh, d = S.deck, I = L.in, frame = nt(S, L.wall === '#3a3d44' ? '#2a2c30' : '#c9ccd4', 0.4), n = Math.max(2, Math.round((I.x1 - I.x0) / (hh * 0.7)));
  q.fillStyle = L.open ? 'rgba(170,215,230,.16)' : 'rgba(30,40,60,.55)'; q.fillRect(I.x0, d - L.gf, I.x1 - I.x0, L.gf);
  for (var i = 0; i <= n; i++) fr(q, I.x0 + i * (I.x1 - I.x0) / n - 1, d - L.gf, 2.5, L.gf, frame);
  fr(q, I.x0, d - hh * 0.06, I.x1 - I.x0, hh * 0.06, frame);
  q.fillStyle = 'rgba(255,255,255,.18)'; for (i = 0; i < n; i++) { var px = I.x0 + i * (I.x1 - I.x0) / n; q.beginPath(); q.moveTo(px + hh * 0.08, d - hh * 0.1); q.lineTo(px + hh * 0.34, d - L.gf + hh * 0.05); q.lineTo(px + hh * 0.44, d - L.gf + hh * 0.05); q.lineTo(px + hh * 0.18, d - hh * 0.1); q.fill(); }
}
function fTeak(q, S, L) {
  var hh = S.hh, d = S.deck, wood = nt(S, '#6b4226', 0.4), dark = nt(S, '#4a2c18', 0.4), x0 = L.bx0, x1 = L.bx1, uy = d - L.gf - hh * 0.5;
  paper(q, rect(x0 - hh * 0.06, uy, x1 - x0 + hh * 0.12, hh * 0.52), wood, 1.5);
  q.strokeStyle = 'rgba(0,0,0,.25)'; q.lineWidth = 1; q.beginPath(); for (var x = x0; x < x1; x += hh * 0.07) { q.moveTo(x, uy); q.lineTo(x, d - L.gf); } q.stroke();
  var nw = Math.max(1, Math.floor((x1 - x0) / (hh * 1.1)));
  for (var i = 0; i < nw; i++) { var wx = x0 + (i + 0.5) * (x1 - x0) / nw; fr(q, wx - hh * 0.16, uy + hh * 0.1, hh * 0.32, hh * 0.26, S.night && i % 2 ? '#ffd98a' : nt(S, '#2a1a12'));
    fr(q, wx - hh * 0.3, uy + hh * 0.1, hh * 0.13, hh * 0.26, dark); fr(q, wx + hh * 0.17, uy + hh * 0.1, hh * 0.13, hh * 0.26, dark); }
  fr(q, x0 - hh * 0.08, d - L.gf - hh * 0.04, x1 - x0 + hh * 0.16, hh * 0.08, dark);
  var mx = (x0 + x1) / 2, roof = nt(S, pick(rnd(S.seed + 3), ['#8a3b2a', '#6a6a72', '#7a4a2a', '#9a5a3a']), 0.4);
  paper(q, poly([[x0 - hh * 0.35, uy + hh * 0.08], [mx, L.top + hh * 0.08], [x1 + hh * 0.35, uy + hh * 0.08]]), roof, 1.6);
  q.strokeStyle = 'rgba(0,0,0,.2)'; q.beginPath(); for (i = 1; i < 6; i++) { var f = i / 6; q.moveTo(lerp(x0 - hh * 0.35, mx, f), lerp(uy + hh * 0.08, L.top + hh * 0.08, f)); q.lineTo(lerp(x1 + hh * 0.35, mx, f), lerp(uy + hh * 0.08, L.top + hh * 0.08, f)); } q.stroke();
  kalae(q, mx, L.top + hh * 0.1, hh * 0.18, nt(S, '#d9a53c', 0.35));
  pillars(q, S, L, dark, 1.3);
}
function kalae(q, x, y, s, col) {
  q.strokeStyle = col; q.lineWidth = Math.max(2, s * 0.14); q.lineCap = 'round'; q.beginPath();
  q.moveTo(x - s * 0.5, y + s * 0.4); q.quadraticCurveTo(x + s * 0.1, y - s * 0.2, x + s * 0.45, y - s * 0.75);
  q.moveTo(x + s * 0.5, y + s * 0.4); q.quadraticCurveTo(x - s * 0.1, y - s * 0.2, x - s * 0.45, y - s * 0.75); q.stroke();
}
/* lai kham: gold stencil on a dark band, a repeat of diamonds and flames */
function laiKham(q, x0, x1, y, h, col, ground) {
  if (ground) fr(q, x0, y, x1 - x0, h, ground);
  q.fillStyle = col; var step = h * 1.2;
  for (var x = x0 + step / 2; x < x1 - step / 4; x += step) { q.beginPath(); q.moveTo(x, y + h * 0.15); q.lineTo(x + h * 0.32, y + h / 2); q.lineTo(x, y + h * 0.85); q.lineTo(x - h * 0.32, y + h / 2); q.closePath(); q.fill();
    q.beginPath(); q.arc(x + step / 2, y + h / 2, h * 0.1, 0, TAU); q.fill(); }
}
function fLanna(q, S, L) {
  var hh = S.hh, d = S.deck, wood = nt(S, '#7a4a2a', 0.4), dark = nt(S, '#4a2c18', 0.4), x0 = L.bx0, x1 = L.bx1, ey = d - L.gf - hh * 0.04, mx = (x0 + x1) / 2;
  var roof = nt(S, pick(rnd(S.seed + 4), ['#8a3b2a', '#6a3a2a', '#5a5a62']), 0.4), gold = nt(S, '#d9a53c', 0.35);
  paper(q, poly([[x0 - hh * 0.4, ey + hh * 0.05], [x0 + hh * 0.3, ey - hh * 0.42], [x1 - hh * 0.3, ey - hh * 0.42], [x1 + hh * 0.4, ey + hh * 0.05]]), roof, 1.6);
  paper(q, poly([[x0 + hh * 0.15, ey - hh * 0.36], [mx, L.top + hh * 0.06], [x1 - hh * 0.15, ey - hh * 0.36]]), roof, 1.8);
  q.strokeStyle = gold; q.lineWidth = Math.max(1.5, hh * 0.025); q.beginPath(); q.moveTo(x0 - hh * 0.4, ey + hh * 0.05); q.lineTo(x0 + hh * 0.3, ey - hh * 0.42); q.moveTo(x1 + hh * 0.4, ey + hh * 0.05); q.lineTo(x1 - hh * 0.3, ey - hh * 0.42); q.moveTo(x0 + hh * 0.15, ey - hh * 0.36); q.lineTo(mx, L.top + hh * 0.06); q.lineTo(x1 - hh * 0.15, ey - hh * 0.36); q.stroke();
  /* the gable's sunburst, carved */
  q.beginPath(); for (var a = 0; a <= 8; a++) { var an = Math.PI + a * Math.PI / 8; q.moveTo(mx, ey - hh * 0.36); q.lineTo(mx + Math.cos(an) * hh * 0.3, ey - hh * 0.36 + Math.sin(an) * hh * 0.3 * 0.9); } q.lineWidth = 1; q.stroke();
  kalae(q, mx, L.top + hh * 0.08, hh * 0.16, gold);
  laiKham(q, x0 - hh * 0.05, x1 + hh * 0.05, ey, hh * 0.1, gold, nt(S, '#2a1a12', 0.3));
  pillars(q, S, L, wood, 1.3);
}
function fStall(q, S, L) {
  var hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, ry = d - L.gf, thatch = L.R && rnd(S.seed + 9)() < 0.5;
  var col = thatch ? nt(S, '#b8925a', 0.4) : nt(S, '#8a8f99', 0.4);
  [x0 + L.pil / 2, x1 - L.pil / 2].forEach(function (x) { paper(q, rect(x - L.pil / 2, ry, L.pil, L.gf), nt(S, '#c9a66b', 0.4), 1); for (var k = 1; k < 5; k++) fr(q, x - L.pil / 2, ry + k * L.gf / 5, L.pil, 2, nt(S, '#8a6a3a', 0.4)); });
  paper(q, function (p) { p.beginPath(); p.moveTo(x0 - hh * 0.3, ry + hh * 0.12); p.lineTo(x0 - hh * 0.05, L.top); p.lineTo(x1 + hh * 0.05, L.top); p.lineTo(x1 + hh * 0.3, ry + hh * 0.12);
    if (thatch) for (var x = x1 + hh * 0.3; x > x0 - hh * 0.3; x -= hh * 0.06) p.lineTo(x, ry + hh * 0.12 + ((x * 7) % 5) * hh * 0.012); p.closePath(); }, col, 1.6);
  q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; q.beginPath(); for (var x = x0 - hh * 0.2; x < x1 + hh * 0.2; x += hh * (thatch ? 0.05 : 0.09)) { q.moveTo(x, ry + hh * 0.1); q.lineTo(x + (x - (x0 + x1) / 2) * 0.05, L.top + 2); } q.stroke();
}
/* roll-up shutters (ribbed, the drum above), teak folding doors, a tarp over a stall */
function doors(q, S, L) {
  var hh = S.hh, d = S.deck, top = d - L.gf + hh * 0.02;
  if (L.type === 'glass' || L.type === 'unit') { glassPanes(q, S, L); if (L.shut[0] > 0) L.bays.forEach(function (b, i) { shutter(q, S, L, b, top, L.shut[i]); }); return; }
  L.bays.forEach(function (b, i) {
    var u = L.shut[i], w = b.x1 - b.x0;
    if (L.door === 'roll' || L.door === 'glass') shutter(q, S, L, b, top, u);
    else if (L.door === 'fold') { var n = 6, pw = w / n, col = nt(S, L.type === 'shop' || L.type === 'row' ? L.trim : '#7a4a2a', 0.45);
      if (u >= 1) { for (var k = 0; k < n; k++) { paper(q, rect(b.x0 + k * pw, top, pw - 1, d - top), col, 0.6); fr(q, b.x0 + k * pw + pw * 0.2, top + hh * 0.1, pw * 0.6, hh * 0.18, mixc(col, '#000000', 0.25)); } }
      else { var st = u > 0 ? n - 1 : 2; for (k = 0; k < st; k++) { var sx = k < st / 2 ? b.x0 + k * 3 : b.x1 - pw * 0.35 - (k - Math.ceil(st / 2)) * 3; paper(q, rect(sx, top, pw * 0.35, d - top), col, 0.6); }
        if (u > 0) { for (k = 0; k < n - 2; k++) paper(q, rect(b.x0 + pw * (0.6 + k), top, pw - 1, d - top), col, 0.6); } } }
    else if (L.door === 'tarp' && u > 0) { paper(q, function (p) { p.beginPath(); p.moveTo(b.x0, top); p.lineTo(b.x1, top); p.lineTo(b.x1 + hh * 0.05, d); for (var x = b.x1; x > b.x0; x -= hh * 0.2) p.quadraticCurveTo(x - hh * 0.1, d - hh * 0.06, x - hh * 0.2, d); p.closePath(); }, nt(S, '#2f6fb0', 0.45), 1);
      q.strokeStyle = 'rgba(255,255,255,.2)'; q.beginPath(); for (var x = b.x0 + hh * 0.2; x < b.x1; x += hh * 0.35) { q.moveTo(x, top); q.lineTo(x + hh * 0.05, d); } q.stroke(); }
  });
}
function shutter(q, S, L, b, top, u) {
  var hh = S.hh, d = S.deck, w = b.x1 - b.x0, col = nt(S, L.shutCol, 0.45), dk = mixc(col, '#000000', 0.25);
  if (u <= 0) { fr(q, b.x0, top - hh * 0.02, w, hh * 0.1, dk); fr(q, b.x0, top + hh * 0.08, w, hh * 0.04, col); return; }
  var h = (d - top) * u;
  paper(q, rect(b.x0, top, w, h), col, 0.8);
  q.fillStyle = 'rgba(0,0,0,.16)'; for (var y = top + hh * 0.04; y < top + h - 2; y += hh * 0.05) q.fillRect(b.x0, y, w, 1);
  q.fillStyle = 'rgba(255,255,255,.12)'; for (y = top + hh * 0.065; y < top + h - 2; y += hh * 0.05) q.fillRect(b.x0, y, w, 1);
  fr(q, b.x0, top + h - hh * 0.05, w, hh * 0.05, dk);
  if (u >= 1) { fr(q, (b.x0 + b.x1) / 2 - hh * 0.03, d - hh * 0.12, hh * 0.06, hh * 0.06, nt(S, '#c9a83a', 0.3)); fr(q, b.x0 + w * 0.2, d - hh * 0.06, hh * 0.08, hh * 0.04, dk); fr(q, b.x1 - w * 0.2 - hh * 0.08, d - hh * 0.06, hh * 0.08, hh * 0.04, dk); }
  else if (S.night) { var g = q.createLinearGradient(0, top + h, 0, d + hh * 0.25); g.addColorStop(0, 'rgba(255,220,150,.55)'); g.addColorStop(1, 'rgba(255,220,150,0)'); q.fillStyle = g; q.fillRect(b.x0, top + h, w, d - top - h + hh * 0.25); }
}
function awning(q, S, L) {
  var hh = S.hh, d = S.deck, y0 = d - L.gf + hh * 0.02, y1 = y0 + hh * 0.26, x0 = L.bx0 - hh * 0.06, x1 = L.bx1 + hh * 0.06, a = L.awn;
  if (a === 'none') return;
  if (a === 'zinc') { paper(q, poly([[x0, y0], [x1, y0], [x1 + hh * 0.12, y1 - hh * 0.04], [x0 - hh * 0.12, y1 - hh * 0.04]]), nt(S, pick(rnd(S.seed + 2), ['#8a8f99', '#6f8aa8', '#a85a3a', '#5f7f6a']), 0.45), 1.4);
    q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; q.beginPath(); for (var x = x0; x < x1; x += hh * 0.06) { q.moveTo(x, y0); q.lineTo(x + (x - (x0 + x1) / 2) * 0.04, y1 - hh * 0.04); } q.stroke(); return; }
  var c1 = nt(S, L.awnCol[0], 0.45), c2 = nt(S, L.awnCol[1], 0.45), n = Math.max(6, Math.round((x1 - x0) / (hh * 0.22))), sw = (x1 - x0 + hh * 0.24) / n;
  paper(q, function (p) { p.beginPath(); p.moveTo(x0, y0); p.lineTo(x1, y0); p.lineTo(x1 + hh * 0.12, y1); if (a === 'scallop') for (var k = n; k > 0; k--) p.arc(x0 - hh * 0.12 + (k - 0.5) * sw, y1, sw / 2, 0, Math.PI); else p.lineTo(x0 - hh * 0.12, y1); p.closePath(); }, c1, 1.5);
  q.fillStyle = c2; for (var k = 0; k < n; k += 2) { var xa = x0 + k * (x1 - x0) / n, xb = x0 + (k + 1) * (x1 - x0) / n, xc = x0 - hh * 0.12 + (k + 1) * sw, xd = x0 - hh * 0.12 + k * sw; q.beginPath(); q.moveTo(xa, y0); q.lineTo(xb, y0); q.lineTo(xc, y1); q.lineTo(xd, y1); q.closePath(); q.fill(); }
}
function boardUp(q, S, L) {
  var hh = S.hh, d = S.deck, F = S.place || {}, lit = L.open ? (S.night ? true : undefined) : false;
  if (L.signAt === 'stand') { var sx = L.signX, sy = L.signY; [sx - L.sg.w * 0.3, sx + L.sg.w * 0.3].forEach(function (x) { paper(q, rect(x - 2, sy, 4, d + hh * 0.1 - sy), nt(S, '#5a3a22', 0.4), 1); });
    if (L.type === 'shop' || L.type === 'row') laiKham(q, L.bx0 + hh * 0.1, L.bx1 - hh * 0.1, d - L.gf - hh * 0.32, hh * 0.18, nt(S, '#d9a53c', 0.35), nt(S, L.trim, 0.45)); }
  L.signBox = K.sign(q, L.signX, L.signY, F, hh, nt(S, L.board, 0.3), lit);
  if (L.lai && L.signAt !== 'stand' && L.signBox && (L.type === 'shop' || L.type === 'row')) { var b = L.signBox; laiKham(q, b.x0 + 4, b.x1 - 4, b.y1 - hh * 0.05, hh * 0.04, '#e8b84a'); }
}

/* the street's still things: wires on a concrete pole, the spirit house, plants, parked bikes, the road's plate, light on the pavement */
function frontStill(q, S, L) {
  var hh = S.hh, d = S.deck, F = S.place || {}, R = rnd(S.seed + 21);
  if (L.open && S.night && L.V.spill !== false) { var I = L.in, g = q.createLinearGradient(0, d, 0, d + hh * 0.5); g.addColorStop(0, L.light === 'warm' ? 'rgba(255,214,140,.4)' : 'rgba(220,240,255,.35)'); g.addColorStop(1, 'rgba(255,214,140,0)');
    q.fillStyle = g; q.beginPath(); q.moveTo(I.x0, d); q.lineTo(I.x1, d); q.lineTo(I.x1 + hh * 0.4, d + hh * 0.5); q.lineTo(I.x0 - hh * 0.4, d + hh * 0.5); q.fill(); }
  if (L.marigold && L.type !== 'unit') K.strand(q, L.in.x0 + hh * 0.05, L.in.x1 - hh * 0.05, d - L.gf + hh * 0.06, hh * 0.08, hh * 0.07, function (x, y, k) { fe(q, x, y, hh * 0.028, hh * 0.028, nt(S, k % 3 === 2 ? '#fffaf0' : k % 2 ? '#f7b52c' : '#f29a1f', 0.35)); });
  L.plants.forEach(function (p) { var pr = rnd(S.seed + Math.round(p.x));
    if (p.k === 'boug') bougain(q, p.x, d + hh * 0.02, p.side === 2 ? L.gf * 0.9 : hh * (1.2 + pr() * 0.6), p.side === 0 ? p.w : -p.w, S, pr);
    else if (p.k === 'banana') banana(q, p.x, d + hh * 0.05, hh * (1.1 + pr() * 0.4), S, pr);
    else if (p.k === 'frangi') frangi(q, p.x, d + hh * 0.05, hh * (1.3 + pr() * 0.4), S, pr);
    else if (p.k === 'jar') jar(q, p.x, d + hh * 0.08, hh, S);
    else pots(q, p.x - p.w / 2, p.x + p.w / 2, d + hh * 0.08, hh, S, pr); });
  if (L.pole) pole(q, S, L, L.pole.x);
  if (L.spirit) L.incense = spiritHouse(q, L.spirit.x, d + hh * (L.spirit.front ? 0.14 : 0.06), hh * (L.spirit.front ? 0.85 : 1), S, L.spirit.kind, R);
  L.bikes.forEach(function (b) { if (b.kind === 'bicycle') bicycle(q, b.x, d + hh * 0.16, hh * 0.9, b.col, b.dir, S, true); else scooter(q, b.x, d + hh * 0.17, hh * 0.92, b.col, b.dir, S); });
  if (L.plate >= 0 && F.road) plate(q, S, L, F.road);
  if (L.animal === 'cat') { var sx = L.animalX; fr(q, sx - hh * 0.1, d - hh * 0.2 + hh * 0.15, hh * 0.2, hh * 0.04, nt(S, '#d9342b', 0.4)); fp(q, [[sx - hh * 0.08, d + hh * 0.15], [sx - hh * 0.1, d - hh * 0.01], [sx - hh * 0.07, d - hh * 0.01], [sx - hh * 0.05, d + hh * 0.15]], nt(S, '#b82a22', 0.4)); fp(q, [[sx + hh * 0.08, d + hh * 0.15], [sx + hh * 0.1, d - hh * 0.01], [sx + hh * 0.07, d - hh * 0.01], [sx + hh * 0.05, d + hh * 0.15]], nt(S, '#b82a22', 0.4)); }
  if (!L.open && S.night && L.type !== 'unit') { var lx = L.lampX = L.in.x1 - hh * 0.3, ly = L.lampY = d - L.gf - hh * 0.12; fr(q, lx - hh * 0.06, ly - hh * 0.02, hh * 0.12, hh * 0.04, '#d8d2c4'); glow(q, lx, ly + hh * 0.05, hh * 0.5, '255,236,180', 0.6); fe(q, lx, ly + hh * 0.03, hh * 0.05, hh * 0.025, '#fff6d0'); }
}
function pole(q, S, L, x) {
  var hh = S.hh, d = S.deck, top = d - hh * 2.2, col = nt(S, '#b8b4aa', 0.45);
  paper(q, poly([[x - hh * 0.05, d + hh * 0.1], [x - hh * 0.035, top], [x + hh * 0.035, top], [x + hh * 0.05, d + hh * 0.1]]), col, 1.2);
  fr(q, x - hh * 0.25, top + hh * 0.08, hh * 0.5, hh * 0.03, col);
  var R = rnd(S.seed + 33);
  q.lineWidth = 1; for (var i = 0; i < 6; i++) { var y = top + hh * (0.1 + i * 0.05), sag = hh * (0.1 + R() * 0.2); q.strokeStyle = 'rgba(25,22,28,' + (0.55 + R() * 0.3) + ')';
    q.beginPath(); q.moveTo(S.x0 - 4, y + sag * 0.4); q.quadraticCurveTo((S.x0 + x) / 2, y + sag, x, y); q.quadraticCurveTo((x + S.x1) / 2, y + sag * (0.6 + R()), S.x1 + 4, y + sag * 0.3); q.stroke(); }
  q.strokeStyle = 'rgba(25,22,28,.7)'; q.beginPath(); for (i = 0; i < 9; i++) q.ellipse(x + hh * 0.02, top + hh * 0.5 + i * 1.5, hh * 0.08, hh * 0.035, 0, 0, TAU); q.stroke();
}
function plate(q, S, L, road) {
  var hh = S.hh, d = S.deck, side = L.sides[L.plate], s = road.length > 24 ? road.slice(0, 23) + '…' : road;
  q.font = '700 ' + Math.round(Math.max(9, hh * 0.12)) + 'px ' + FONT; var w = q.measureText(s).width + hh * 0.2, x = L.plate ? Math.min(S.x1 - w / 2 - 4, side.a + w / 2 + hh * 0.1) : Math.max(S.x0 + w / 2 + 4, side.b - w / 2 - hh * 0.1);
  if (L.spirit && Math.abs(L.spirit.x - x) < w / 2 + hh * 0.2) x = L.plate ? Math.min(S.x1 - w / 2 - 4, L.spirit.x + w / 2 + hh * 0.3) : Math.max(S.x0 + w / 2 + 4, L.spirit.x - w / 2 - hh * 0.3);
  var y = d - hh * 1.3;
  fr(q, x - 1.5, y, 3, d + hh * 0.15 - y, nt(S, '#9aa0a8', 0.4));
  paper(q, rect(x - w / 2, y - hh * 0.2, w, hh * 0.2), nt(S, '#1f6a4a', 0.35), 1);
  q.strokeStyle = 'rgba(255,255,255,.8)'; q.lineWidth = 1; q.strokeRect(x - w / 2 + 2, y - hh * 0.2 + 2, w - 4, hh * 0.2 - 4);
  txt(q, s, x, y - hh * 0.1, Math.max(9, hh * 0.12), '#ffffff', 700);
}

/* ---------------------------------------------------------------- the frame: two still layers around the trade at work, then the street alive */
var MEMO = {}, nmemo = 0;
function stateOf(S) {
  var F = S.place || {}, o = K.openNow(F.hours, S.now);
  return o === true ? 'open' : o === false ? 'closed' : S.night ? 'quiet' : 'open';
}
function draw(S0, spec, name) {
  var S = {}; for (var f in S0) S[f] = S0[f];
  var F = S.place || {}, st = stateOf(S);
  if (spec.route) { var to = spec.route(S, F); if (to && SCENE[to]) spec = SCENE[to]; }
  if (spec.state) st = spec.state(S, F, st);
  var key = [name, S.W, S.H, Math.round(S.x0), Math.round(S.x1), Math.round(S.deck), Math.round(S.hh * 10), S.seed, +S.night, st, +!!S.phone, F.id || ''].join('|');
  var L = MEMO[key]; if (!L) { if (++nmemo > 40) { MEMO = {}; nmemo = 1; } L = MEMO[key] = plan(S, spec, st); }
  var hh = S.hh, top = L.type === 'unit' || L.V.tall ? 0 : S.deck - hh * 2.6, box = [S.x0 - 8, top, S.span + 16, S.H - top + 4];
  layer(S, key + '|a', box, function (q) { backdrop(q, S, L); if (!L.V.custom) room(q, S, L); if (spec.back && L.open) spec.back(q, S, L, L.V); });
  if (spec.live && L.open) spec.live(S, L, L.V);
  layer(S, key + '|b', box, function (q) { if (spec.fore && L.open) spec.fore(q, S, L, L.V); facade(q, S, L); frontStill(q, S, L); if (spec.out) spec.out(q, S, L, L.V); });
  if (spec.street) spec.street(S, L, L.V);
  street(S, L);
  S.hits.push({ k: 'place', x0: L.bx0, x1: L.bx1, y0: L.top, y1: S.H });
}
function street(S, L) {
  var c = S.c, hh = S.hh, d = S.deck, t = S.t, i;
  var ly = L.awn !== 'none' && L.awn ? d - L.gf + hh * 0.27 : d - L.gf + hh * 0.03;
  if (L.type !== 'unit' && !L.V.custom) L.lanterns.forEach(function (p, k) { khom(c, p.x, ly, hh, p.col, t, k, S.night); });
  if (L.incense) smoke(c, L.incense[0], L.incense[1], hh, t, 1);
  var ax = L.animalX, ay = d + hh * 0.2;
  if (L.animal === 'dog') dog(c, ax, ay, hh, L.animalCol, t, 1, false);
  else if (L.animal === 'cat') cat(c, ax, d + hh * 0.11, hh * 0.9, L.animalCol, t, 2);
  else if (L.animal === 'hens') { hen(c, ax, ay, hh * 0.8, t, 1, '#c9853a'); hen(c, ax + hh * 0.3, ay + 2, hh * 0.7, t, 2, '#f2ead8'); }
  if (L.lampX != null) moth(c, L.lampX, L.lampY + hh * 0.06, hh, t);
  for (i = 0; i < L.walkers; i++) {
    var v = hh * (0.45 + 0.12 * i), span = S.span + hh * 2, dir = i % 2 ? -1 : 1, u = (t / 1000 * v + i * span * 0.47) % span, px = dir > 0 ? S.x0 - hh + u : S.x1 + hh - u, wd = L.folk[4 + i];
    var me = fig(c, wd, px, d + hh * 0.2, hh * 0.95, K.walkP(t / 1000 * TAU * 0.9 + i * 2, false), dir);
    if (i === 0 && L.open) { var hd = me.hand[1]; fp(c, [[hd[0] - hh * 0.05, hd[1]], [hd[0] + hh * 0.05, hd[1]], [hd[0] + hh * 0.06, hd[1] + hh * 0.13], [hd[0] - hh * 0.06, hd[1] + hh * 0.13]], '#f2f2ee'); }
  }
}

/* ---------------------------------------------------------------- small moving things the trades share */
function bubble(c, x, y, s, text, a) {
  if (a <= 0.02) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.font = '700 ' + Math.round(Math.max(10, s * 0.13)) + 'px ' + FONT;
  var w = c.measureText(text).width + s * 0.16, h = Math.max(14, s * 0.2);
  c.fillStyle = '#fffaf0'; c.beginPath(); c.moveTo(x - w / 2 + h / 2, y - h); c.arcTo(x + w / 2, y - h, x + w / 2, y, h / 2); c.arcTo(x + w / 2, y, x - w / 2, y, h / 2); c.lineTo(x + s * 0.02, y); c.lineTo(x - s * 0.04, y + s * 0.07); c.lineTo(x - s * 0.06, y); c.arcTo(x - w / 2, y, x - w / 2, y - h, h / 2); c.arcTo(x - w / 2, y - h, x + w / 2, y - h, h / 2); c.fill();
  c.fillStyle = '#3a2a22'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, x, y - h / 2 + 0.5); c.restore();
}
/* sparks off a grinder: each a particle on y = y₀ − v₀t + ½gt², fading */
function sparks(c, x, y, s, t, n, dir) {
  for (var i = 0; i < n; i++) {
    var u = ((t / 420) + i / n) % 1, a = -0.3 - (i * 0.37 % 1) * 1.1, v = s * (0.9 + (i * 0.61 % 1) * 0.8), px = x + dir * Math.cos(a) * v * u, py = y + Math.sin(a) * v * u + s * 1.6 * u * u;
    c.strokeStyle = 'rgba(255,' + Math.round(200 - 120 * u) + ',80,' + (1 - u).toFixed(2) + ')'; c.lineWidth = Math.max(1, s * 0.012);
    c.beginPath(); c.moveTo(px, py); c.lineTo(px - dir * Math.cos(a) * s * 0.05, py - Math.sin(a) * s * 0.05 - s * 0.02 * u); c.stroke();
  }
  glow(c, x, y, s * 0.18, '255,190,90', 0.6 + 0.3 * Math.sin(t / 40));
}
/* steam: puffs that rise, swell and thin; x = x₀ + A·sin(ky − ωt) */
function steam(c, x, y, s, t, k, n, rise) {
  for (var i = 0; i < n; i++) {
    var u = (t / 2400 + i / n + k * 0.37) % 1, yy = y - u * (rise || s * 0.4), xx = x + Math.sin(u * 5 - t / 900 + k) * s * 0.05 * (0.3 + u), r = s * (0.025 + 0.06 * u);
    c.fillStyle = 'rgba(255,255,255,' + (0.5 * Math.sin(Math.PI * u)).toFixed(3) + ')'; c.beginPath(); c.arc(xx, yy, r, 0, TAU); c.fill();
  }
}
/* a standing fan, blades turning at ω: three ellipses about the hub */
function fan(c, x, y, s, t, col) {
  ln(c, [[x, y], [x, y - s * 0.5]], col, Math.max(1.5, s * 0.025)); fe(c, x, y, s * 0.1, s * 0.025, col);
  var cx = x, cy = y - s * 0.56, r = s * 0.13;
  c.strokeStyle = col; c.lineWidth = 1; c.beginPath(); c.arc(cx, cy, r, 0, TAU); c.stroke();
  for (var i = 0; i < 3; i++) { var a = t / 60 + i * TAU / 3; fe(c, cx + Math.cos(a) * r * 0.5, cy + Math.sin(a) * r * 0.5, r * 0.45, r * 0.2, 'rgba(160,200,230,.75)', a); }
  fe(c, cx, cy, r * 0.15, r * 0.15, col);
}
/* a ceiling fan seen from the side: blades foreshortened by cos θ */
function ceilFan(c, x, y, s, t) {
  ln(c, [[x, y], [x, y + s * 0.08]], '#5a5a5a', 1.5);
  for (var i = 0; i < 3; i++) { var a = t / 90 + i * TAU / 3, w = Math.cos(a) * s * 0.28; fe(c, x + w / 2, y + s * 0.09, Math.abs(w) / 2 + 1, s * 0.012, '#6a5a4a'); }
  fe(c, x, y + s * 0.09, s * 0.03, s * 0.02, '#5a5a5a');
}
/* a wall clock showing the hour where the place stands */
function clock(c, x, y, r, now) {
  var b = new Date(now + 7 * 3600e3), m = b.getUTCMinutes() + b.getUTCSeconds() / 60, h = b.getUTCHours() % 12 + m / 60;
  fe(c, x, y, r, r, '#fffaf0'); c.strokeStyle = '#3a2a22'; c.lineWidth = Math.max(1, r * 0.12); c.beginPath(); c.arc(x, y, r, 0, TAU); c.stroke();
  ln(c, [[x, y], [x + Math.sin(h / 12 * TAU) * r * 0.5, y - Math.cos(h / 12 * TAU) * r * 0.5]], '#3a2a22', Math.max(1, r * 0.14));
  ln(c, [[x, y], [x + Math.sin(m / 60 * TAU) * r * 0.8, y - Math.cos(m / 60 * TAU) * r * 0.8]], '#3a2a22', 1);
}
/* shelves along the back wall: planks, and goods dealt into each row */
function shelves(q, x0, x1, y0, y1, rows, S, fill) {
  var col = nt(S, '#8a6a4a', 0.35), rh = (y1 - y0) / rows;
  fr(q, x0, y0, 2, y1 - y0, col); fr(q, x1 - 2, y0, 2, y1 - y0, col);
  for (var i = 0; i < rows; i++) { var yb = y0 + (i + 1) * rh; if (fill) fill(q, x0 + 3, x1 - 3, yb - 2, rh - 4, i); fr(q, x0, yb - 2, x1 - x0, 3, col); }
}
function goods(q, x0, x1, yb, h, R, pal, S, kind) {
  var x = x0;
  while (x < x1 - 3) {
    var w = h * (kind === 'bottle' ? 0.22 : 0.3 + R() * 0.5), hh2 = h * (0.5 + R() * 0.45), col = nt(S, pick(R, pal), 0.25);
    if (x + w > x1) w = x1 - x;
    if (!(w > 0.5)) break;   /* a shelf too short to stack on (a tiny canvas): w went negative and the loop never ended */
    if (kind === 'binder') { w = h * 0.2; hh2 = h * 0.92; fr(q, x, yb - hh2, w - 1, hh2, col); fr(q, x + w * 0.15, yb - hh2 * 0.8, w * 0.6, hh2 * 0.2, 'rgba(255,255,255,.75)'); fe(q, x + w * 0.45, yb - hh2 * 0.35, w * 0.16, w * 0.16, 'rgba(0,0,0,.35)'); }
    else if (kind === 'bottle') { fr(q, x + w * 0.2, yb - hh2, w * 0.6, hh2, col); fr(q, x + w * 0.35, yb - hh2 - h * 0.12, w * 0.3, h * 0.12, col); fr(q, x + w * 0.2, yb - hh2 * 0.6, w * 0.6, hh2 * 0.25, 'rgba(255,255,255,.55)'); }
    else if (kind === 'bag') { fp(q, [[x, yb], [x + w * 0.05, yb - hh2], [x + w * 0.95, yb - hh2], [x + w, yb]], col); fr(q, x + w * 0.2, yb - hh2 * 0.65, w * 0.6, hh2 * 0.3, 'rgba(255,255,255,.4)'); }
    else { fr(q, x, yb - hh2, w - 1, hh2, col); fr(q, x + w * 0.15, yb - hh2 * 0.7, w * 0.6, Math.max(1, hh2 * 0.12), 'rgba(255,255,255,.5)'); }
    x += w;
  }
}
function counter(q, x0, x1, y, S, col, glass) {
  var d = S.deck, hh = S.hh;
  if (glass) { fr(q, x0, y, x1 - x0, d - y, 'rgba(190,225,235,.35)'); q.strokeStyle = nt(S, '#c9ccd4', 0.3); q.lineWidth = 1.5; q.strokeRect(x0, y, x1 - x0, d - y); }
  else paper(q, rect(x0, y + hh * 0.04, x1 - x0, d - y - hh * 0.04), nt(S, col, 0.3), 1);
  paper(q, rect(x0 - hh * 0.04, y, x1 - x0 + hh * 0.08, hh * 0.05), nt(S, mixc(col, '#000000', 0.2), 0.3), 1);
}
function stool(q, x, y, s, col, S) {
  fe(q, x, y - s * 0.26, s * 0.12, s * 0.025, nt(S, col, 0.35));
  fp(q, [[x - s * 0.1, y - s * 0.25], [x + s * 0.1, y - s * 0.25], [x + s * 0.13, y], [x + s * 0.08, y], [x, y - s * 0.18], [x - s * 0.08, y], [x - s * 0.13, y]], nt(S, mixc(col, '#000000', 0.12), 0.35));
}
function chair(q, x, y, s, col, dir, S) {
  var c = nt(S, col, 0.35);
  fr(q, x - s * 0.12, y - s * 0.27, s * 0.24, s * 0.04, c); fr(q, x - dir * s * 0.12 - (dir > 0 ? s * 0.03 : 0), y - s * 0.55, s * 0.03, s * 0.3, c);
  ln(q, [[x, y - s * 0.24], [x, y - s * 0.05]], nt(S, '#3a3a3a'), Math.max(1.5, s * 0.02)); ln(q, [[x - s * 0.1, y], [x + s * 0.1, y]], nt(S, '#3a3a3a'), Math.max(1.5, s * 0.02));
}
function desk(q, x0, x1, S, col) {
  var d = S.deck, hh = S.hh, y = d - hh * 0.4;
  paper(q, rect(x0, y, x1 - x0, hh * 0.04), nt(S, col, 0.3), 1);
  fr(q, x0 + hh * 0.03, y + hh * 0.04, x1 - x0 - hh * 0.06, d - y - hh * 0.06, nt(S, mixc(col, '#000000', 0.15), 0.3));
  return y;
}
function screen(q, x, y, s, S, lit) {
  fr(q, x - s * 0.13, y - s * 0.2, s * 0.26, s * 0.17, nt(S, '#2a2a2e')); fr(q, x - s * 0.115, y - s * 0.19, s * 0.23, s * 0.14, lit ? '#bfe6f2' : '#3a4a5a'); fr(q, x - s * 0.02, y - s * 0.03, s * 0.04, s * 0.03, nt(S, '#2a2a2e'));
}
function digits(c, x, y, s, str, col, bg) {
  c.font = '800 ' + Math.round(s) + 'px ui-monospace,Menlo,monospace'; var w = c.measureText(str).width + s * 0.4;
  fr(c, x - w / 2, y - s * 0.65, w, s * 1.3, bg || '#141418'); c.fillStyle = col; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(str, x, y + s * 0.04);
  return w;
}
function poster(q, x, y, w, h, S, draw) {
  fr(q, x - 1, y - 1, w + 2, h + 2, nt(S, '#f2f2ee', 0.3)); q.save(); q.beginPath(); q.rect(x, y, w, h); q.clip(); draw(q, x, y, w, h); q.restore();
}

/* ================================================================ the trades */
var SCENE = {}, MATHS = {};
function addShop(name, spec, mathLine) { SCENE[name] = spec; MATHS[name] = mathLine; }

/* office: desks with screens and the person at work, a client across; the lawyer's red and green
   spines and scales, the accountant's binders, the visa agent's map and stamp, a coworking table
   of laptops, the wholesaler's cartons and hand truck; keys tap at ω, the clock keeps the hour */
addShop('office', {
  look: function (S, F, R) {
    var k = has(F, /ทนาย|law|legal|attorney|กฎหมาย|นิติ/i) ? 'law' : has(F, /บัญชี|account|audit|ภาษี|tax/i) ? 'acct' : sub(F, 'visa') || has(F, /visa|วีซ่า|immigra/i) ? 'visa'
      : sub(F, 'translation') || has(F, /แปล|translat/i) ? 'visa' : sub(F, 'coworking') || has(F, /cowork|co-work|\bhub\b|workspace|nomad/i) ? 'cowork'
      : sub(F, 'wholesale') || has(F, /ขายส่ง|ค้าส่ง|wholesale|trading|distribut|แม็คโคร|makro|express|ขนส่ง|logist/i) ? 'whole'
      : has(F, /ประกัน|insur|\baia\b|fwd|allianz|muang ?thai/i) ? 'insure' : has(F, /ลิสซิ่ง|leasing|ติดล้อ|สินเชื่อ|finance|loan|ไชโย|credit/i) ? 'loan'
      : has(F, /estate|property|อสังหา|realty|ที่ดิน/i) ? 'estate' : pick(R, ['desk', 'desk', 'acct', 'insure']);
    var V = { k: k, light: R() < 0.7 ? 'cool' : 'warm', mix: { casual: 0.86, sin: 0.09, mohom: 0.05 } };
    V.types = k === 'cowork' ? { glass: 3, teak: 1.2, lanna: 1, shop: 1 } : k === 'whole' ? { row: 3, shop: 2, stall: 0.6 } : { shop: 4, glass: 2.2, row: 1.2, teak: 0.4 };
    if (k === 'cowork') V.light = 'warm';
    if (k === 'whole') V.bikes = 0;
    return V;
  },
  plan: function (S, L, V, R) {
    var I = L.in, hh = S.hh, w = I.x1 - I.x0;
    L.desks = []; var n = V.k === 'cowork' ? 1 : clamp(Math.floor(w / (hh * 1.55)), 1, 3);
    for (var i = 0; i < n; i++) { var x = I.x0 + w * (i + 0.5) / n; L.desks.push({ x: x, client: R() < 0.6, col: pick(R, ['#c9a878', '#8a6a4a', '#e8e2d6', '#6a5a4a']) }); }
    L.staff = crew(S, 6, V.mix, 3); L.staff.forEach(function (d, k) { if (k % 2 === 0 && V.k !== 'cowork') uni(d, pick(R, ['#f2f2ee', '#cfe0f0', '#e8d8f0', '#f2e6c9']), pick(R, ['#2c2f45', '#3a3a3a'])); });
  },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 41), wy0 = I.y0 + hh * 0.02, wy1 = d - hh * 0.58, w = I.x1 - I.x0;
    if (V.k === 'whole') { shelves(q, I.x0 + hh * 0.05, I.x1 - hh * 0.05, wy0, d - hh * 0.02, 3, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#c9a06a', '#b8905a', '#d8b27a', '#e8d2a8'], S); }); return; }
    if (V.k === 'cowork') { for (var i = 0; i < 4; i++) { var px = I.x0 + w * (0.15 + i * 0.23); fr(q, px - hh * 0.14, wy0 + hh * 0.05, hh * 0.28, hh * 0.22, nt(S, ['#f2f2ee', '#fff6c0', '#c9e8d8', '#f2d4cf'][i], 0.2));
        for (var k = 0; k < 6; k++) fr(q, px - hh * 0.11 + (k % 3) * hh * 0.08, wy0 + hh * (0.08 + Math.floor(k / 3) * 0.08), hh * 0.06, hh * 0.06, pick(R, ['#ffd84a', '#ff9ac0', '#9ad8ff', '#a8f0a0'])); }
      pots(q, I.x1 - hh * 0.5, I.x1 - hh * 0.05, d, hh * 0.9, S, R); return; }
    var dark = ['#7a1f2a', '#1f4a3a', '#2a3a6a', '#5a3a1a'], bind = ['#d9342b', '#3a6fb0', '#e8b84a', '#4fae8c', '#f2f2ee', '#9b6bd6', '#2a2a2a'];
    var bx0 = I.x0 + hh * 0.05, bx1 = Math.min(I.x1 - hh * 0.05, bx0 + Math.max(hh * 0.9, w * 0.45));
    if (V.k === 'law' || V.k === 'acct' || V.k === 'desk') shelves(q, bx0, bx1, wy0, wy1, 2, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, V.k === 'law' ? dark : bind, S, 'binder'); });
    var rx = (bx1 + I.x1) / 2;
    if (V.k === 'law') { q.strokeStyle = nt(S, '#c9a83a', 0.2); q.lineWidth = 1.5; q.beginPath(); q.moveTo(rx, wy0 + hh * 0.08); q.lineTo(rx, wy0 + hh * 0.38); q.moveTo(rx - hh * 0.18, wy0 + hh * 0.13); q.lineTo(rx + hh * 0.18, wy0 + hh * 0.13);
      q.moveTo(rx - hh * 0.25, wy0 + hh * 0.25); q.lineTo(rx - hh * 0.18, wy0 + hh * 0.13); q.lineTo(rx - hh * 0.11, wy0 + hh * 0.25); q.moveTo(rx + hh * 0.25, wy0 + hh * 0.25); q.lineTo(rx + hh * 0.18, wy0 + hh * 0.13); q.lineTo(rx + hh * 0.11, wy0 + hh * 0.25); q.stroke();
      fe(q, rx - hh * 0.18, wy0 + hh * 0.25, hh * 0.07, hh * 0.02, nt(S, '#c9a83a', 0.2)); fe(q, rx + hh * 0.18, wy0 + hh * 0.25, hh * 0.07, hh * 0.02, nt(S, '#c9a83a', 0.2)); fr(q, rx - hh * 0.1, wy0 + hh * 0.38, hh * 0.2, hh * 0.03, nt(S, '#c9a83a', 0.2)); }
    else if (V.k === 'visa') { poster(q, rx - hh * 0.45, wy0 + hh * 0.05, hh * 0.9, hh * 0.45, S, function (p, x, y, ww, h) { fr(p, x, y, ww, h, '#bfe0f0'); var r2 = rnd(7); for (var j = 0; j < 7; j++) fe(p, x + ww * (0.1 + r2() * 0.8), y + h * (0.2 + r2() * 0.6), ww * (0.06 + r2() * 0.1), h * (0.08 + r2() * 0.12), '#7ab86a'); for (j = 0; j < 4; j++) { p.fillStyle = '#d9342b'; p.beginPath(); p.arc(x + ww * (0.2 + j * 0.2), y + h * (0.3 + (j % 2) * 0.3), 2, 0, TAU); p.fill(); } });
      for (i = 0; i < 3; i++) { fr(q, bx0 + hh * 0.05 + i * hh * 0.24, wy0 + hh * 0.12, hh * 0.18, hh * 0.25, nt(S, pick(R, ['#7a1f2a', '#1f2a5a', '#1f4a3a']), 0.2)); fe(q, bx0 + hh * 0.14 + i * hh * 0.24, wy0 + hh * 0.2, hh * 0.04, hh * 0.04, '#c9a83a'); } }
    else if (V.k === 'insure' || V.k === 'loan' || V.k === 'estate') { poster(q, rx - hh * 0.35, wy0 + hh * 0.04, hh * 0.7, hh * 0.48, S, function (p, x, y, ww, h) { fr(p, x, y, ww, h, V.k === 'loan' ? '#fff2b0' : '#d8ecf6');
        if (V.k === 'insure') { fp(p, [[x + ww * 0.2, y + h * 0.45], [x + ww * 0.5, y + h * 0.12], [x + ww * 0.8, y + h * 0.45]], '#d9342b'); ln(p, [[x + ww * 0.5, y + h * 0.45], [x + ww * 0.5, y + h * 0.8]], '#3a2a22', 1.5); [0.35, 0.5, 0.62].forEach(function (u, j) { fe(p, x + ww * u, y + h * (0.62 + j * 0.04), ww * 0.04, ww * 0.04, '#3a2a22'); fr(p, x + ww * u - ww * 0.04, y + h * (0.68 + j * 0.04), ww * 0.08, h * (0.25 - j * 0.04), '#3a6fb0'); }); }
        else if (V.k === 'loan') { scooter(p, x + ww * 0.45, y + h * 0.85, h * 0.9, '#d9342b', 1, { night: false }); for (var j = 0; j < 4; j++) fe(p, x + ww * 0.82, y + h * (0.82 - j * 0.09), ww * 0.1, h * 0.04, '#e8b84a'); }
        else { fp(p, [[x + ww * 0.15, y + h * 0.5], [x + ww * 0.5, y + h * 0.15], [x + ww * 0.85, y + h * 0.5]], '#8a3b2a'); fr(p, x + ww * 0.22, y + h * 0.5, ww * 0.56, h * 0.38, '#f2ead8'); fr(p, x + ww * 0.44, y + h * 0.62, ww * 0.12, h * 0.26, '#6a4a2a'); } }); }
    else if (V.k === 'acct') { fr(q, rx - hh * 0.32, wy0 + hh * 0.05, hh * 0.64, hh * 0.42, nt(S, '#f6f6f2', 0.2)); for (i = 0; i < 5; i++) fr(q, rx - hh * 0.25 + i * hh * 0.11, wy0 + hh * (0.42 - 0.06 * (i + 1 + (i % 2))), hh * 0.07, hh * 0.06 * (i + 1 + (i % 2)), ['#3a6fb0', '#4fae8c', '#e8b84a', '#d9342b', '#3a6fb0'][i]); }
    else { fr(q, rx - hh * 0.15, wy0 + hh * 0.2, hh * 0.3, hh * 0.5, nt(S, '#9aa3a8', 0.3)); for (i = 0; i < 3; i++) fr(q, rx - hh * 0.12, wy0 + hh * (0.24 + i * 0.16), hh * 0.24, 2, 'rgba(0,0,0,.3)'); }
    /* the water cooler, blue bottle up */
    var wx = I.x1 - hh * 0.18; fr(q, wx - hh * 0.08, d - hh * 0.5, hh * 0.16, hh * 0.5, nt(S, '#e8e8e2', 0.3)); fe(q, wx, d - hh * 0.6, hh * 0.08, hh * 0.1, nt(S, '#7fc0e8', 0.25));
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    if (V.k === 'whole') { var w = I.x1 - I.x0 - hh * 0.8, u = (t / 7000) % 1, p = u < 0.5 ? u * 2 : 2 - u * 2, x = I.x0 + hh * 0.4 + w * ease(p), dir = u < 0.5 ? 1 : -1, wd = L.staff[0];
      var me = fig(c, wd, x, d - hh * 0.02, hh * 0.92, reach(x, d - hh * 0.02, hh * 0.92, K.walkP(t / 1000 * TAU * 1.2, false), dir, [x + dir * hh * 0.22, d - hh * 0.55], [x + dir * hh * 0.18, d - hh * 0.52]), dir);
      fr(c, x + dir * hh * 0.08 - (dir < 0 ? hh * 0.3 : 0), d - hh * 0.78, hh * 0.3, hh * 0.25, nt(S, '#c9a06a', 0.2)); fr(c, x + dir * hh * 0.08 - (dir < 0 ? hh * 0.3 : 0), d - hh * 0.7, hh * 0.3, 2, 'rgba(0,0,0,.25)'); return; }
    if (V.k === 'cowork') { var n = Math.max(2, Math.min(5, Math.floor((I.x1 - I.x0) / (hh * 0.65))));
      for (var i = 0; i < n; i++) { var px = I.x0 + (I.x1 - I.x0) * (i + 0.5) / n, dr = i % 2 ? -1 : 1; fig(c, L.staff[i], px - dr * hh * 0.18, d - hh * 0.02, hh * 0.86, i % 3 === 2 ? sitTalk(t, i) : typing(t, i), dr); } return; }
    L.desks.forEach(function (k, i) {
      fig(c, L.staff[i * 2], k.x - hh * 0.42, d - hh * 0.02, hh * 0.9, V.k === 'visa' && i === 0 ? { lean: 0.1, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [1.1 + 0.9 * Math.pow(Math.max(0, Math.sin(t / 500)), 3), 0.3, 0.9, 0.5] } : typing(t, i), 1);
      if (k.client) fig(c, L.staff[i * 2 + 1], k.x + hh * 0.48, d - hh * 0.02, hh * 0.9, sitTalk(t, i * 2 + 1), -1);
    });
    if (L.type !== 'glass') ceilFan(c, (I.x0 + I.x1) / 2, I.y0 - hh * 0.08, hh, t);
    clock(c, I.x0 + hh * 0.25, I.y0 + hh * 0.08, hh * 0.07, S.now);
  },
  fore: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, I = L.in, R = rnd(S.seed + 43);
    if (V.k === 'whole') { for (var i = 0; i < 3; i++) { var bx = I.x1 - hh * (0.3 + i * 0.3); if (bx < I.x0 + hh * 0.3) break; for (var j = 0; j <= i % 2 + 1; j++) paper(q, rect(bx - hh * 0.13, d - hh * 0.25 * (j + 1), hh * 0.26, hh * 0.24), nt(S, '#c9a06a', 0.3), 0.8); } return; }
    if (V.k === 'cowork') { var y = desk(q, I.x0 + hh * 0.1, I.x1 - hh * 0.1, S, '#c9a878'), n = Math.max(2, Math.min(5, Math.floor((I.x1 - I.x0) / (hh * 0.65))));
      for (i = 0; i < n; i++) { var px = I.x0 + (I.x1 - I.x0) * (i + 0.5) / n, dr = i % 2 ? -1 : 1; fp(q, [[px - dr * hh * 0.02, y], [px + dr * hh * 0.02, y - hh * 0.16], [px + dr * hh * 0.05, y - hh * 0.15], [px + dr * hh * 0.02, y]], '#3a3d44'); if (S.night) glow(q, px, y - hh * 0.08, hh * 0.15, '190,225,255', 0.5);
        if (i % 2) { fr(q, px + hh * 0.12, y - hh * 0.07, hh * 0.05, hh * 0.07, '#f2f2ee'); } }
      for (i = 0; i < 3; i++) { var lx = I.x0 + (I.x1 - I.x0) * (i + 0.5) / 3; ln(q, [[lx, I.y0 - hh * 0.1], [lx, I.y0 + hh * 0.2]], '#2a2a2a', 1); fp(q, [[lx - hh * 0.1, I.y0 + hh * 0.3], [lx - hh * 0.04, I.y0 + hh * 0.2], [lx + hh * 0.04, I.y0 + hh * 0.2], [lx + hh * 0.1, I.y0 + hh * 0.3]], nt(S, '#2a2a2a', 0.2)); glow(q, lx, I.y0 + hh * 0.34, hh * 0.25, '255,220,150', S.night ? 0.8 : 0.4); }
      return; }
    L.desks.forEach(function (k) { var y = desk(q, k.x - hh * 0.3, k.x + hh * 0.3, S, k.col); screen(q, k.x - hh * 0.05, y, hh, S, true); fr(q, k.x + hh * 0.1, y - hh * 0.05, hh * 0.14, hh * 0.05, nt(S, '#f2f2ee', 0.2)); fr(q, k.x + hh * 0.12, y - hh * 0.09, hh * 0.12, hh * 0.04, nt(S, '#f2f2ee', 0.2));
      if (k.client) chair(q, k.x + hh * 0.48, d, hh, '#3a3a3a', -1, S); });
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    if (V.k === 'whole') { var x = L.bx1 + hh * 0.6; if (x < S.x1 - hh * 1.4) car(q, x + hh * 0.5, d + hh * 0.2, hh, 'pickup', pick(rnd(S.seed), CARS), -1, S); }
    if (V.k === 'loan' && L.bikes.length === 0) scooter(q, (L.bx0 + L.bx1) / 2, d + hh * 0.17, hh * 0.92, '#d9342b', 1, S);
  }
}, 'keys: y = A·sin ωt<br>the clock: θ = 2π·t/12h');

/* garage: a motorbike up on its stand with the mechanic crouched at the wheel, or a car with legs out
   from under it, tyres stacked, oil cans, the pegboard of tools; the wrench turns, the grinder throws
   sparks on parabolas, y = y₀ − v₀t + ½gt² */
addShop('garage', {
  look: function (S, F, R) {
    var k = has(F, /ยาง|tyre|tire|b-quik|ปะยาง|autobacs|cockpit/i) ? 'tyre' : F.brand || has(F, /toyota|isuzu|ford|nissan|mazda|mitsubishi|\bmg\b|chevrolet|kia|hyundai|bmw|benz|volvo|โตโยต้า|อีซูซุ|ฟอร์ด|นิสสัน|มาสด้า|ซ่อมรถยนต์|เคาะ|พ่นสี|ประดับยนต์|car\b|cars\b|auto|garage|อู่/i) ? 'car'
      : has(F, /มอเตอร์ไซค์|motor|bike|yamaha|vespa|ไบค์/i) ? 'bike' : R() < 0.55 ? 'bike' : 'car';
    var dealer = F.brand && has(F, /toyota|isuzu|ford|nissan|mazda|mitsubishi|\bmg\b|chevrolet|honda|โตโยต้า|อีซูซุ|ฟอร์ด|ฮอนด้า/i);
    return { k: k, dealer: dealer, types: dealer ? { glass: 1 } : { row: 3, stall: 2, shop: 1.6 }, door: dealer ? 'glass' : 'roll', awning: dealer ? 'none' : R() < 0.6 ? 'zinc' : 'none', light: 'cool', floor: '#8a8a86', mix: { casual: 1 }, w: 4.4 + R() * 1.2, lanterns: R() < 0.4 ? 2 : 0, sparks: R() < 0.55 };
  },
  plan: function (S, L, V, R) { L.mech = crew(S, 3, { casual: 1 }, 5); L.mech.forEach(function (d) { uni(d, pick(R, ['#2c3e6b', '#3a4a5a', '#5a6a7a', '#1f3a5a']), '#2c3e6b'); }); L.bodyCol = pick(R, BIKE); L.carCol = pick(R, CARS); },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 51), w = I.x1 - I.x0;
    /* the pegboard and its tools */
    var px0 = I.x0 + hh * 0.08, pw = Math.min(hh * 1.1, w * 0.4), py = I.y0 + hh * 0.04;
    fr(q, px0, py, pw, hh * 0.45, nt(S, '#c9a878', 0.3)); q.fillStyle = 'rgba(0,0,0,.25)'; for (var x = px0 + 4; x < px0 + pw; x += 6) for (var y = py + 4; y < py + hh * 0.45; y += 6) q.fillRect(x, y, 1, 1);
    for (var i = 0; i < 6; i++) { var tx = px0 + pw * (i + 0.5) / 6, tl = hh * (0.18 + R() * 0.12); ln(q, [[tx, py + hh * 0.06], [tx, py + hh * 0.06 + tl]], nt(S, '#5a5e66', 0.2), Math.max(2, hh * 0.025)); fe(q, tx, py + hh * 0.06, hh * 0.03, hh * 0.025, nt(S, i % 3 ? '#5a5e66' : '#d9342b', 0.2)); }
    /* oil cans */
    shelves(q, I.x1 - hh * 0.75, I.x1 - hh * 0.05, I.y0 + hh * 0.04, I.y0 + hh * 0.5, 2, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#e8b84a', '#d9342b', '#2f7f6b', '#1f4a8a', '#f2f2ee'], S); });
    /* tyres stacked */
    for (i = 0; i < 4; i++) { fe(q, I.x1 - hh * 0.3, d - hh * (0.05 + i * 0.09), hh * 0.22, hh * 0.05, nt(S, '#1e1e22')); fe(q, I.x1 - hh * 0.3, d - hh * (0.06 + i * 0.09), hh * 0.1, hh * 0.02, nt(S, '#3a3a40')); }
    fe(q, (I.x0 + I.x1) / 2, d - hh * 0.03, w * 0.25, hh * 0.03, 'rgba(0,0,0,.25)');
    /* inner tubes hung in loops, a compressor and its coiled hose, a drum of oil */
    var tx0 = px0 + pw + hh * 0.15, tx1 = I.x1 - hh * 0.85; q.strokeStyle = nt(S, '#1e1e22'); q.lineWidth = Math.max(2, hh * 0.035);
    for (x = tx0; x < tx1; x += hh * 0.2) { fr(q, x - 1, I.y0 + hh * 0.03, 3, hh * 0.04, nt(S, '#5a5e66')); q.beginPath(); q.ellipse(x, I.y0 + hh * 0.2, hh * 0.07, hh * 0.15, 0, 0, TAU); q.stroke(); }
    var cpx = I.x0 + hh * 0.35; fe(q, cpx, d - hh * 0.14, hh * 0.24, hh * 0.1, nt(S, '#c0392b', 0.3)); fr(q, cpx - hh * 0.08, d - hh * 0.36, hh * 0.18, hh * 0.13, nt(S, '#3a3a3a')); fe(q, cpx - hh * 0.18, d - hh * 0.03, hh * 0.03, hh * 0.03, nt(S, '#1e1e22')); fe(q, cpx + hh * 0.18, d - hh * 0.03, hh * 0.03, hh * 0.03, nt(S, '#1e1e22'));
    q.strokeStyle = nt(S, '#e8b84a', 0.3); q.lineWidth = 1.5; q.beginPath(); for (i = 0; i < 4; i++) q.ellipse(cpx + hh * 0.05, d - hh * 0.42 + hh * 0.08, hh * 0.08, hh * 0.04, 0, 0, TAU); q.stroke();
    if (V.k === 'tyre') { for (var row = 0; row < 2; row++) { var ry = d - hh * (0.05 + row * 0.42); fr(q, I.x0 + hh * 0.7, ry, w - hh * 1.6, 2, nt(S, '#5a5e66')); for (x = I.x0 + hh * 0.78; x < I.x1 - hh * 0.95; x += hh * 0.13) { fe(q, x, ry - hh * 0.18, hh * 0.055, hh * 0.18, nt(S, '#1e1e22')); fe(q, x, ry - hh * 0.18, hh * 0.02, hh * 0.08, nt(S, '#3a3a40')); } } }
    /* the job in the bay */
    var cx = I.x0 + w * 0.45;
    if (V.k === 'car' || V.dealer) car(q, cx + (V.dealer ? 0 : hh * 0.2), d - hh * (V.k === 'car' && !V.dealer && L.R && (S.seed % 3 === 0) ? 0.3 : 0), hh, V.dealer ? 'sedan' : S.seed % 2 ? 'pickup' : 'sedan', L.carCol, 1, S);
    else if (V.k === 'tyre') { car(q, cx + hh * 0.9, d - hh * 0.02, hh * 0.9, 'sedan', L.carCol, -1, S); fr(q, cx + hh * 0.3, d - hh * 0.55, hh * 0.25, hh * 0.55, nt(S, '#d9342b', 0.3)); fe(q, cx + hh * 0.42, d - hh * 0.62, hh * 0.22, hh * 0.05, nt(S, '#5a5e66')); }
    else { scooter(q, cx + hh * 0.25, d - hh * 0.02, hh * 0.95, L.bodyCol, -1, S); fr(q, cx + hh * 0.05, d - hh * 0.1, hh * 0.04, hh * 0.1, nt(S, '#3a3a3a')); }
    if (V.k === 'car' && !V.dealer && S.seed % 3 === 0) { [cx - hh * 0.95, cx + hh * 1.35].forEach(function (px) { paper(q, rect(px - hh * 0.05, d - hh * 1.05, hh * 0.1, hh * 1.05), nt(S, '#d9a53c', 0.3), 1); }); fr(q, cx - hh * 0.95, d - hh * 0.32, hh * 2.3, hh * 0.04, nt(S, '#5a5e66')); }
    if (V.sparks) { var vx = I.x1 - hh * 0.55; fr(q, vx - hh * 0.2, d - hh * 0.42, hh * 0.4, hh * 0.04, nt(S, '#5a5e66')); fr(q, vx - hh * 0.16, d - hh * 0.38, hh * 0.04, hh * 0.38, nt(S, '#5a5e66')); fr(q, vx + hh * 0.12, d - hh * 0.38, hh * 0.04, hh * 0.38, nt(S, '#5a5e66')); }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, w = I.x1 - I.x0, cx = I.x0 + w * 0.45;
    if (V.dealer) { fig(c, L.mech[1], cx + hh * 1.3, d - hh * 0.02, hh * 0.95, talk(t, 1), -1); fig(c, L.mech[2], cx + hh * 1.7, d - hh * 0.02, hh * 0.9, STANDP, -1); return; }
    if (V.k === 'car' && S.seed % 3 !== 0) {   /* on the creeper under the car: the feet out, wiggling */
      var wg = Math.sin(t / 300) * hh * 0.02; fr(c, cx - hh * 1.25, d - hh * 0.06, hh * 0.5, hh * 0.05, '#c9a83a');
      ln(c, [[cx - hh * 0.8, d - hh * 0.08], [cx - hh * 1.2, d - hh * 0.08 + wg]], L.mech[0].low, hh * 0.07); ln(c, [[cx - hh * 0.8, d - hh * 0.1], [cx - hh * 1.15, d - hh * 0.16 - wg]], L.mech[0].low, hh * 0.07);
      fe(c, cx - hh * 1.22, d - hh * 0.1 + wg, hh * 0.03, hh * 0.05, '#2a1a12'); fe(c, cx - hh * 1.17, d - hh * 0.18 - wg, hh * 0.03, hh * 0.05, '#2a1a12');
    } else if (V.k === 'car') { var ah = d - hh * 0.62; fig(c, L.mech[0], cx + hh * 0.3, d - hh * 0.02, hh * 0.95, reach(cx + hh * 0.3, d - hh * 0.02, hh * 0.95, STANDP, 1, [cx + hh * 0.45 + Math.sin(t / 200) * hh * 0.03, ah], [cx + hh * 0.5, ah + hh * 0.05]), 1); }
    else if (V.k === 'tyre') { var tr = t / 400; fe(c, cx + hh * 0.42, d - hh * 0.62, hh * 0.24, hh * 0.08, '#1e1e22'); ln(c, [[cx + hh * 0.42 + Math.cos(tr) * hh * 0.16, d - hh * 0.63 + Math.sin(tr) * hh * 0.04], [cx + hh * 0.42 - Math.cos(tr) * hh * 0.16, d - hh * 0.63 - Math.sin(tr) * hh * 0.04]], '#9aa0a8', 2);
      fig(c, L.mech[0], cx - hh * 0.05, d - hh * 0.02, hh * 0.95, reach(cx - hh * 0.05, d - hh * 0.02, hh * 0.95, STANDP, 1, [cx + hh * 0.25, d - hh * 0.62], [cx + hh * 0.2, d - hh * 0.55]), 1); }
    else {   /* the mechanic crouched at the front wheel, the wrench turning */
      var wx = cx + hh * 0.25 - hh * 0.37 * 0.95, wy = d - hh * 0.15, a = t / 250, hx = wx - hh * 0.05 + Math.cos(a) * hh * 0.05, hy = wy + Math.sin(a) * hh * 0.05;
      var mx = wx - hh * 0.38, me = fig(c, L.mech[0], mx, d - hh * 0.02, hh * 0.92, reach(mx, d - hh * 0.02, hh * 0.92, CROUCH, 1, [hx, hy], [wx - hh * 0.05, wy + hh * 0.02]), 1);
      ln(c, [[hx, hy], [wx, wy]], '#c9ccd4', Math.max(2, hh * 0.03));
    }
    if (V.sparks) { var vx = I.x1 - hh * 0.55, gx = vx - hh * 0.05, gy = d - hh * 0.46;
      fig(c, L.mech[1], vx - hh * 0.45, d - hh * 0.02, hh * 0.92, reach(vx - hh * 0.45, d - hh * 0.02, hh * 0.92, { lean: 0.25, legs: [0.1, 0, -0.15, 0], arms: [1, 0.5, 0.9, 0.5] }, 1, [gx - hh * 0.08, gy - hh * 0.04], [gx - hh * 0.12, gy]), 1);
      fr(c, gx - hh * 0.1, gy - hh * 0.06, hh * 0.12, hh * 0.05, '#3a6fb0'); if ((t / 2400) % 1 < 0.7) sparks(c, gx + hh * 0.04, gy, hh, t, 14, -1); }
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, R = rnd(S.seed + 53), sd = L.sides[R() < 0.5 ? 0 : 1];
    if (V.dealer) return;
    /* a tyre hung out front on a cord, the shop's old sign of the trade */
    var tx = L.bx0 + hh * 0.35, ty = d - L.gf + hh * 0.5;
    if (V.k !== 'car' || R() < 0.5) { ln(q, [[tx, d - L.gf + hh * 0.05], [tx, ty - hh * 0.2]], '#3a3a3a', 1); fe(q, tx, ty, hh * 0.24, hh * 0.24, nt(S, '#1e1e22', 0.2)); fe(q, tx, ty, hh * 0.13, hh * 0.13, nt(S, '#f2f2ee', 0.3)); q.strokeStyle = nt(S, '#5a5e66', 0.2); q.lineWidth = 1.5; q.beginPath(); for (var sp = 0; sp < 6; sp++) { q.moveTo(tx, ty); q.lineTo(tx + Math.cos(sp * 1.047) * hh * 0.12, ty + Math.sin(sp * 1.047) * hh * 0.12); } q.stroke(); }
    if (sd.b - sd.a > hh * 0.5) { var bx = (sd.a + sd.b) / 2; for (var i = 0; i < 2; i++) { paper(q, rect(bx - hh * 0.13 + i * hh * 0.28, d - hh * 0.36 + hh * 0.12, hh * 0.25, hh * 0.36), nt(S, i ? '#2f5fa8' : '#c0392b', 0.4), 0.8); fr(q, bx - hh * 0.13 + i * hh * 0.28, d - hh * 0.14, hh * 0.25, 2, 'rgba(0,0,0,.3)'); } }
  }
}, 'the wrench: θ = ωt<br>sparks: y = y₀ − v₀t + ½gt²');

/* convenience: a 7-Eleven kind of glass front lit day and night (the brand only tints the band), the
   door slides open, the chime rings and the clerk says สวัสดีค่ะ; popsicles in the freezer, beer in the
   fridge, salapao steaming; the soi dogs asleep on the cool tiles. Or a mom-and-pop shophouse with
   snacks hung on strings and the auntie fanning herself. */
var MART = { seven: ['#1f7a4a', '#f08a2a', '#2f9a5a'], lotus: ['#0f8a8a', '#7fcf9f', '#0f8a8a'], bigc: ['#2f9a3a', '#d9342b', '#2f9a3a'], cp: ['#c0392b', '#2f9a3a', '#c0392b'], fm: ['#1f6fb0', '#3fbf6f', '#1f6fb0'], mart: ['#d9342b', '#e8b84a', '#3a6fb0'] };
addShop('convenience', {
  look: function (S, F, R) {
    var k = has(F, /7-?eleven|เซเว่น|7-11/i) ? 'seven' : has(F, /lotus|โลตัส|tesco/i) ? 'lotus' : has(F, /big ?c|บิ๊กซี/i) ? 'bigc' : has(F, /cp ?fresh|ซีพี/i) ? 'cp' : has(F, /family ?mart|แฟมิลี่/i) ? 'fm' : F.brand ? 'mart' : R() < 0.55 ? 'chohuay' : 'mart';
    var V = { k: k, chain: k !== 'chohuay', light: 'cool', mix: { casual: 0.8, sin: 0.12, mohom: 0.08 } };
    if (V.chain) { V.type = 'glass'; V.wall = '#f6f6f2'; V.tint = MART[k] || MART.mart; V.board = V.tint[0]; V.w = 4.6 + R() * 1; V.floor = '#e8e6e0'; V.inWall = '#f4f7f6'; V.awning = 'none'; V.wallArt = function (q, S, L) { var y = S.deck - L.gf - S.hh * 0.16; fr(q, L.bx0, y, L.bw, S.hh * 0.05, nt(S, V.tint[0], 0.3)); fr(q, L.bx0, y + S.hh * 0.05, L.bw, S.hh * 0.025, nt(S, V.tint[1], 0.3)); fr(q, L.bx0, y + S.hh * 0.075, L.bw, S.hh * 0.025, nt(S, V.tint[2], 0.3)); }; }
    else { V.types = { shop: 3, row: 2.5, teak: 0.6 }; V.light = 'warm'; }
    return V;
  },
  plan: function (S, L, V, R) { L.doorX = L.in.x0 + (L.in.x1 - L.in.x0) * 0.18; L.clerk = crew(S, 4, V.mix, 9); if (V.chain) uni(L.clerk[0], nt(S, V.tint[0], 0.2), '#2c2f45'); L.dogs = V.chain ? 1 + (R() < 0.5 ? 1 : 0) : 0; if (V.chain) L.animal = 'none'; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 61), w = I.x1 - I.x0, snack = ['#d9342b', '#f2c94c', '#3a6fb0', '#4fae8c', '#f08a3a', '#9b6bd6', '#e5567f', '#2a2a2a'];
    /* the drinks fridge: glass doors, bottles and the brown of beer */
    var fx0 = V.chain ? I.x0 + hh * 0.05 : I.x1 - hh * 0.75, fx1 = fx0 + hh * 0.7;
    fr(q, fx0, I.y0 + hh * 0.02, fx1 - fx0, d - I.y0 - hh * 0.04, nt(S, '#d8dade', 0.2));
    shelves(q, fx0 + hh * 0.04, fx1 - hh * 0.04, I.y0 + hh * 0.06, d - hh * 0.08, 4, S, function (p, a, b, yb, h, i) { goods(p, a, b, yb, h, R, i === 1 ? ['#6a3a1a', '#2f6a2a', '#6a3a1a'] : i === 2 ? ['#d9342b', '#f08a2a', '#4fae8c', '#f2f2f2'] : ['#bfe6f2', '#f2f2f2', '#2f9a5a', '#e8b84a'], S, 'bottle'); });
    q.fillStyle = 'rgba(200,235,245,.2)'; q.fillRect(fx0, I.y0 + hh * 0.02, fx1 - fx0, d - I.y0 - hh * 0.04); fr(q, (fx0 + fx1) / 2 - 1, I.y0 + hh * 0.02, 2, d - I.y0, nt(S, '#9aa0a8', 0.2));
    /* snack shelves */
    var sx0 = V.chain ? fx1 + hh * 0.1 : I.x0 + hh * 0.05, sx1 = V.chain ? I.x1 - hh * 1.0 : fx0 - hh * 0.1;
    if (sx1 > sx0 + hh * 0.3) shelves(q, sx0, sx1, I.y0 + hh * 0.1, d - hh * 0.05, 4, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, snack, S, 'bag'); });
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    if (!V.chain) { var ax = I.x0 + (I.x1 - I.x0) * 0.42, fa = Math.sin(t / 160) * 0.5;
      fig(c, L.clerk[0], ax, d - hh * 0.02, hh * 0.9, reach(ax, d - hh * 0.02, hh * 0.9, { lean: 0.05, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [0.5, 0.6, 0.4, 0.8] }, 1, [ax + hh * 0.2, d - hh * 0.62 + fa * hh * 0.05], null), 1);
      c.save(); c.translate(ax + hh * 0.2, d - hh * 0.62 + fa * hh * 0.05); c.rotate(fa); fe(c, 0, -hh * 0.08, hh * 0.06, hh * 0.09, '#e8b84a'); c.restore(); return; }
    /* the clerk behind the counter, the customer who comes in */
    var kx = I.x1 - hh * 0.55, u = (t / 9000) % 1, open = u > 0.18 && u < 0.5 ? Math.min(1, (u - 0.18) * 12, (0.5 - u) * 12) : 0;
    fig(c, L.clerk[0], kx + hh * 0.25, d - hh * 0.02, hh * 0.92, talk(t, 2), -1);
    L.hello = [kx + hh * 0.05, d - hh * 1.0, u > 0.22 && u < 0.62 ? Math.min(1, (u - 0.22) * 10, (0.62 - u) * 10) : 0];
    if (u > 0.3 && u < 0.95) { var p = (u - 0.3) / 0.65, shelf = I.x0 + (I.x1 - I.x0) * 0.45, ix = lerp(L.doorX, shelf, ease(Math.min(1, p * 1.6))), wdir = shelf > L.doorX ? 1 : -1; fig(c, L.clerk[1], ix, d - hh * 0.02, hh * 0.92, p < 0.62 ? K.walkP(t / 1000 * TAU, false) : reach(ix, d - hh * 0.02, hh * 0.92, STANDP, -1, [ix - hh * 0.25, d - hh * 0.75], null), p < 0.62 ? wdir : -1); }
    L.doorOpen = open;
    steam(c, kx - hh * 0.15, d - hh * 0.62, hh, t, 1, 4, hh * 0.3);
  },
  fore: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 63);
    if (!V.chain) { counter(q, I.x0 + (I.x1 - I.x0) * 0.55, I.x0 + (I.x1 - I.x0) * 0.55 + hh * 0.6, d - hh * 0.45, S, '#c9a878', true); goods(q, I.x0 + (I.x1 - I.x0) * 0.55 + 2, I.x0 + (I.x1 - I.x0) * 0.55 + hh * 0.6 - 2, d - hh * 0.05, hh * 0.3, R, ['#d9342b', '#f2c94c', '#3a6fb0', '#f08a3a'], S, 'bag'); return; }
    var kx = I.x1 - hh * 0.55;
    counter(q, kx - hh * 0.3, I.x1 - hh * 0.02, d - hh * 0.45, S, V.tint[0]);
    fr(q, kx - hh * 0.25, d - hh * 0.62, hh * 0.22, hh * 0.17, nt(S, '#d8dade', 0.2)); fr(q, kx - hh * 0.23, d - hh * 0.6, hh * 0.18, hh * 0.13, 'rgba(255,240,210,.8)');
    for (var i = 0; i < 4; i++) fe(q, kx - hh * (0.2 - i * 0.045), d - hh * 0.5, hh * 0.022, hh * 0.018, '#fffaf0');
    /* the ice-cream freezer by the door: popsicles under the glass lid */
    var zx = I.x0 + (I.x1 - I.x0) * 0.42; paper(q, rect(zx - hh * 0.35, d - hh * 0.36, hh * 0.7, hh * 0.36), nt(S, '#f2f2f2', 0.2), 1); fr(q, zx - hh * 0.33, d - hh * 0.36, hh * 0.66, hh * 0.08, 'rgba(190,230,245,.8)');
    for (i = 0; i < 9; i++) { var px = zx - hh * 0.3 + i * hh * 0.07; fr(q, px, d - hh * 0.42, hh * 0.05, hh * 0.08, pick(R, ['#ff7aa8', '#ffd84a', '#7fd8ff', '#f08a3a', '#a8f0a0', '#8a5a3a'])); fr(q, px + hh * 0.018, d - hh * 0.34, hh * 0.014, hh * 0.04, '#e8d2a8'); }
    L.doorX = I.x0 + (I.x1 - I.x0) * 0.18;
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    if (!V.chain) { var R = rnd(S.seed + 65); for (var i = 0; i < 9; i++) { var sx = L.in.x0 + hh * 0.15 + i * hh * 0.18; if (sx > L.in.x1 - hh * 0.1) break; ln(q, [[sx, d - L.gf + hh * 0.05], [sx, d - L.gf + hh * 0.45]], 'rgba(60,40,30,.7)', 1);
        for (var j = 0; j < 4; j++) fp(q, [[sx - hh * 0.05, d - L.gf + hh * (0.1 + j * 0.09)], [sx + hh * 0.05, d - L.gf + hh * (0.1 + j * 0.09)], [sx + hh * 0.045, d - L.gf + hh * (0.18 + j * 0.09)], [sx - hh * 0.045, d - L.gf + hh * (0.18 + j * 0.09)]], nt(S, pick(R, ['#d9342b', '#f2c94c', '#3a6fb0', '#4fae8c', '#f08a3a', '#e5567f']), 0.35)); }
      paper(q, rect(L.in.x0 + hh * 0.1, d - hh * 0.32 + hh * 0.12, hh * 0.45, hh * 0.32), nt(S, '#d9342b', 0.35), 1); fr(q, L.in.x0 + hh * 0.1, d - hh * 0.2 + hh * 0.12, hh * 0.45, 2, '#f2f2f2');
      for (i = 0; i < 3; i++) paper(q, poly([[L.in.x1 - hh * (0.2 + i * 0.28), d + hh * 0.12], [L.in.x1 - hh * (0.32 + i * 0.28), d + hh * 0.12], [L.in.x1 - hh * (0.3 + i * 0.28), d - hh * 0.18], [L.in.x1 - hh * (0.22 + i * 0.28), d - hh * 0.18]]), nt(S, '#e8dcc0', 0.35), 0.8);
      return; }
    var I = L.in, dx = L.doorX || I.x0 + (I.x1 - I.x0) * 0.18;
    fr(q, dx - hh * 0.32, d - L.gf + hh * 0.02, hh * 0.64, hh * 0.05, nt(S, '#9aa0a8', 0.3));
    fr(q, dx - hh * 0.35, d, hh * 0.7, hh * 0.05, nt(S, '#3a6a4a', 0.3));
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    if (V.chain && L.open) { var dx = L.doorX || I.x0 + (I.x1 - I.x0) * 0.18, o = L.doorOpen || 0, pw = hh * 0.3;
      c.fillStyle = 'rgba(190,225,235,.28)'; c.fillRect(dx - pw - o * pw * 0.9, d - L.gf + hh * 0.07, pw, L.gf - hh * 0.07); c.fillRect(dx + o * pw * 0.9, d - L.gf + hh * 0.07, pw, L.gf - hh * 0.07);
      c.strokeStyle = 'rgba(160,165,170,.9)'; c.lineWidth = 2; c.strokeRect(dx - pw - o * pw * 0.9, d - L.gf + hh * 0.07, pw, L.gf - hh * 0.07); c.strokeRect(dx + o * pw * 0.9, d - L.gf + hh * 0.07, pw, L.gf - hh * 0.07);
      if (o > 0.2) K.notes(c, dx - hh * 0.1, d - L.gf + hh * 0.3, t, 2, '#f2c94c');
      if (L.hello) bubble(c, L.hello[0], L.hello[1], hh, 'สวัสดีค่ะ', L.hello[2]);
      var u = (t / 9000) % 1; if (u < 0.3) { var p = u / 0.3, wx = lerp(S.x1 + hh * 0.5, dx + hh * 0.05, p); fig(c, L.clerk[1], wx, d + hh * 0.18, hh * 0.94, K.walkP(t / 1000 * TAU, false), -1); } }
    if (V.chain) for (var i = 0; i < L.dogs; i++) dog(c, (L.doorX || I.x0) + hh * (0.55 + i * 0.5) * (i % 2 ? -1 : 1), d + hh * 0.18, hh, DOGS[(S.seed + i) % DOGS.length], t, i, false);
  },
}, 'the door: x = w·(1 − cos πu)/2<br>the chime: f = 440·2<sup>n/12</sup>');

/* ---------------------------------------------------------------- shared by the counters of the state and the bank */
/* a flag on its pole, the cloth a travelling wave, dy = A·(x/L)·sin(kx − ωt) */
var THAI = ['#d9242b', '#f2f2f2', '#2a3a8a', '#2a3a8a', '#f2f2f2', '#d9242b'];
function flag(c, px, top, w, h, t, k, cols) {
  ln(c, [[px, top - 3], [px, top + h * 4.2]], '#d8d2c4', Math.max(1.5, h * 0.06)); fe(c, px, top - 3, h * 0.06, h * 0.06, '#e8b84a');
  var N = 10, n = cols.length;
  for (var i = 0; i < n; i++) {
    c.fillStyle = cols[i]; c.beginPath();
    for (var j = 0; j <= N; j++) { var u = j / N, x = px + u * w, y = top + i * h / n + Math.sin(u * 5 - t / 300 + k) * h * 0.12 * u; j ? c.lineTo(x, y) : c.moveTo(x, y); }
    for (j = N; j >= 0; j--) { u = j / N; x = px + u * w; y = top + (i + 1) * h / n + Math.sin(u * 5 - t / 300 + k) * h * 0.12 * u + 0.5; c.lineTo(x, y); }
    c.closePath(); c.fill();
  }
}
/* the hall of a district or tambon office: two storeys, a tiled hip roof, a white-trimmed gable over the door, columns */
function fHall(q, S, L) {
  var hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, mx = (x0 + x1) / 2, wall = nt(S, L.wall, 0.4), trim = nt(S, L.trim, 0.4), u1 = d - L.gf - hh * 0.46, tile = nt(S, L.V.roof || '#b5532f', 0.4);
  paper(q, rect(x0, u1, x1 - x0, hh * 0.48), wall, 1.5);
  for (var x = x0 + hh * 0.25; x < x1 - hh * 0.2; x += hh * 0.42) { if (Math.abs(x - mx) < hh * 0.55) continue; fr(q, x - hh * 0.1, u1 + hh * 0.1, hh * 0.2, hh * 0.24, S.night && (x * 7 | 0) % 3 === 0 ? '#ffd98a' : nt(S, '#6f8fa0', 0.5)); fr(q, x - hh * 0.11, u1 + hh * 0.34, hh * 0.22, 2, trim); }
  paper(q, poly([[x0 - hh * 0.22, u1 + hh * 0.03], [x0 + hh * 0.35, L.top + hh * 0.32], [x1 - hh * 0.35, L.top + hh * 0.32], [x1 + hh * 0.22, u1 + hh * 0.03]]), tile, 1.6);
  q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; q.beginPath(); for (var i = 1; i < 5; i++) { var y = lerp(u1, L.top + hh * 0.32, i / 5); q.moveTo(lerp(x0 - hh * 0.22, x0 + hh * 0.35, i / 5), y); q.lineTo(lerp(x1 + hh * 0.22, x1 - hh * 0.35, i / 5), y); } q.stroke();
  var gw = Math.min(hh * 1.0, (x1 - x0) * 0.24);
  paper(q, poly([[mx - gw, u1 + hh * 0.48], [mx - gw, u1 + hh * 0.02], [mx, L.top], [mx + gw, u1 + hh * 0.02], [mx + gw, u1 + hh * 0.48]]), wall, 1.8);
  paper(q, poly([[mx - gw * 1.08, u1 + hh * 0.06], [mx, L.top - hh * 0.04], [mx + gw * 1.08, u1 + hh * 0.06], [mx + gw * 0.9, u1 + hh * 0.06], [mx, L.top + hh * 0.08], [mx - gw * 0.9, u1 + hh * 0.06]]), tile, 1.6);
  q.strokeStyle = nt(S, '#f2f2ee', 0.4); q.lineWidth = Math.max(1.5, hh * 0.025); q.beginPath(); q.moveTo(mx - gw * 1.08, u1 + hh * 0.06); q.lineTo(mx, L.top - hh * 0.04); q.lineTo(mx + gw * 1.08, u1 + hh * 0.06); q.stroke();
  q.strokeStyle = nt(S, '#d9a53c', 0.35); q.beginPath(); q.moveTo(mx, L.top - hh * 0.04); q.quadraticCurveTo(mx + hh * 0.02, L.top - hh * 0.12, mx + hh * 0.07, L.top - hh * 0.14); q.stroke();
  q.beginPath(); for (var a = 0; a <= 8; a++) { var an = Math.PI + a * Math.PI / 8; q.moveTo(mx, u1 + hh * 0.36); q.lineTo(mx + Math.cos(an) * gw * 0.55, u1 + hh * 0.36 + Math.sin(an) * hh * 0.26); } q.lineWidth = 1; q.stroke();
  pillars(q, S, L, nt(S, '#f6f2ea', 0.4), 1.3);
  paper(q, rect(x0 - hh * 0.04, d - L.gf - hh * 0.05, x1 - x0 + hh * 0.08, hh * 0.08), trim, 1.2);
  fr(q, x0 - hh * 0.1, d - hh * 0.04, x1 - x0 + hh * 0.2, hh * 0.04, nt(S, '#d8d2c4', 0.4)); fr(q, x0 - hh * 0.2, d, x1 - x0 + hh * 0.4, hh * 0.05, nt(S, '#cfc8b8', 0.4));
}
/* the queue: a ticket machine, rows of waiting chairs, the number board stepping on, n = n₀ + ⌊t/T⌋ */
function queueBoard(c, x, y, s, t, seed, col) { var n = (seed % 80) + Math.floor(t / 4200) % 20; return digits(c, x, y, s * 0.11, 'A' + (n < 10 ? '00' : '0') + n, col || '#ff5a3a'); }
function waitChairs(q, x0, x1, S, col) { var hh = S.hh, d = S.deck; fr(q, x0, d - hh * 0.26, x1 - x0, hh * 0.04, nt(S, col, 0.3)); for (var x = x0 + hh * 0.05; x < x1; x += hh * 0.3) { fr(q, x, d - hh * 0.26, 2, hh * 0.26, nt(S, '#5a5e66')); fr(q, x + hh * 0.18, d - hh * 0.5, hh * 0.04, hh * 0.24, nt(S, col, 0.3)); } }

/* gov: the district or tambon office with the flag waving and the queue at its counters,
   the number board stepping on; the coin-op drinking-water kiosk with a bottle filling; the police box
   with its light; the water tower of the waterworks; a photo studio's flash; a wreath shop, calm */
addShop('gov', {
  route: function (S, F) { return sub(F, 'visa') || sub(F, 'translation') ? 'office' : sub(F, 'copyshop') ? 'printing' : null; },
  look: function (S, F, R) {
    var k = has(F, /ตู้น้ำ|น้ำดื่ม|หยอดเหรียญ|drinking water|water ?(fresh|vending|station)|good ?drink|\bdd water/i) && !has(F, /ประปา/) ? 'water'
      : has(F, /ตำรวจ|police|สภ\.|ป้อม/i) ? 'police' : sub(F, 'utilities') || has(F, /ประปา|ไฟฟ้า|\bpea\b|\bpwa\b|electric|waterworks/i) ? 'utility'
      : sub(F, 'photo') || has(F, /studio|สตูดิโอ|ถ่ายรูป|photo/i) ? 'photo' : sub(F, 'funeral') || has(F, /หรีด|wreath|funeral|ฌาปน|โลงศพ|coffin/i) ? 'funeral' : 'hall';
    var V = { k: k, light: 'cool', mix: { casual: 0.6, sin: 0.25, mohom: 0.15 } };
    if (k === 'hall' || k === 'police' || k === 'utility') { V.type = 'shop'; V.facade = fHall; V.door = 'fold'; V.awning = 'none'; V.signAt = 'face'; V.w = 5.2 + R() * 0.8; V.wall = pick(R, k === 'police' ? ['#efe6d6', '#f2e8d8'] : ['#f2ead8', '#f6f2ea', '#efe3c8', '#e8eef0']); V.trim = k === 'police' ? '#6b4a2e' : pick(R, ['#8a3b2a', '#2f5f6b', '#7a5a2a']); V.roof = pick(R, ['#b5532f', '#a8432f', '#6a6a72', '#2f5f6b']); V.at = 0.3 + R() * 0.4; V.lanterns = 0; V.bikes = 1; }
    else if (k === 'water') { V.custom = kiosk; V.type = 'custom'; V.signAt = 'face'; V.noPole = R() < 0.5; V.w = 1.5; V.lanterns = 0; V.bikes = R() < 0.5 ? 1 : 0; }
    else if (k === 'photo') { V.types = { shop: 3, glass: 2, row: 1 }; V.light = 'warm'; }
    else { V.types = { shop: 2, row: 3, stall: 1 }; V.light = 'warm'; V.lanterns = 0; V.marigold = false; }
    return V;
  },
  plan: function (S, L, V, R) {
    var hh = S.hh, d = S.deck;
    L.folk2 = crew(S, 6, V.mix, 4); L.off = crew(S, 3, { casual: 1 }, 6); L.off.forEach(function (o) { uni(o, V.k === 'police' ? '#6b4a2e' : '#b8a77a', V.k === 'police' ? '#5a3a22' : '#7a6a4a'); });
    if (V.facade) { var nc = clamp(Math.floor((L.in.x1 - L.in.x0) / (hh * 1.1)), 1, 3); L.counters = []; for (var i = 0; i < nc; i++) L.counters.push(L.in.x0 + (L.in.x1 - L.in.x0) * (i + 0.5) / nc); L.storeys = 2; L.top = d - hh * 2.26; L.signY = d - L.gf - hh * 0.46 + hh * 0.1; L.flagX = L.bx0 - hh * 0.45 > S.x0 + hh ? L.bx0 - hh * 0.45 : L.bx1 + hh * 0.35; L.marigold = false; if (L.spirit && Math.abs(L.spirit.x - L.flagX) < hh * 0.5) L.spirit = null; }
    if (V.k === 'water') { L.top = d - hh * 1.8; L.signY = L.top - L.sg.h - hh * 0.1; L.in = { x0: L.bx0 + hh * 0.2, x1: L.bx1 - hh * 0.2, y0: d - hh * 0.9, y1: d }; L.animal = R() < 0.5 ? 'dog' : 'cat'; }
  },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 71), w = I.x1 - I.x0;
    if (V.facade) {
      for (var i = 0; i < L.counters.length; i++) { var cx = L.counters[i]; fr(q, cx - hh * 0.25, I.y0 + hh * 0.06, hh * 0.5, hh * 0.16, nt(S, '#2f5f6b', 0.2)); fe(q, cx, I.y0 + hh * 0.14, hh * 0.05, hh * 0.05, '#ffffff'); }
      shelves(q, I.x0 + hh * 0.05, I.x0 + hh * 0.5, I.y0 + hh * 0.3, d - hh * 0.5, 2, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#e8b84a', '#3a6fb0', '#f2f2ee', '#4fae8c'], S, 'binder'); });
      return; }
    if (V.k === 'photo') { fr(q, I.x0 + w * 0.45, I.y0, w * 0.4, d - I.y0, nt(S, pick(R, ['#7f9ab8', '#b8b4aa', '#c9a8b8', '#9ab89a']), 0.2)); fe(q, I.x0 + w * 0.65, d - hh * 0.02, w * 0.2, hh * 0.03, 'rgba(0,0,0,.15)');
      for (i = 0; i < 4; i++) { var fx = I.x0 + hh * 0.1 + (i % 2) * hh * 0.4, fy = I.y0 + hh * 0.05 + Math.floor(i / 2) * hh * 0.42; fr(q, fx, fy, hh * 0.32, hh * 0.38, nt(S, '#3a2a22', 0.2)); fr(q, fx + 3, fy + 3, hh * 0.32 - 6, hh * 0.38 - 6, nt(S, pick(R, ['#d8c8b0', '#c9e0e8', '#e8d0d8']), 0.2)); fe(q, fx + hh * 0.16, fy + hh * 0.14, hh * 0.06, hh * 0.07, nt(S, '#8a6a4a', 0.2)); fe(q, fx + hh * 0.16, fy + hh * 0.3, hh * 0.1, hh * 0.08, nt(S, pick(R, CLOTHS), 0.2)); }
      return; }
    if (V.k === 'funeral') { fr(q, I.x0, I.y0, w, hh * 0.12, nt(S, '#f2f2ee', 0.2)); for (i = 0; i < Math.floor(w / (hh * 0.55)); i++) wreath(q, I.x0 + hh * 0.3 + i * hh * 0.55, d - hh * 0.05, hh * 0.85, S, R); }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    if (V.facade && L.counters) {
      L.counters.forEach(function (cx, i) { fig(c, L.off[i % 3], cx - hh * 0.1, d - hh * 0.02, hh * 0.88, typing(t, i), 1); fig(c, L.folk2[i], cx + hh * 0.32, d - hh * 0.02, hh * 0.92, talk(t, i * 2), -1); });
      return; }
    if (V.k === 'photo') { var px = I.x0 + (I.x1 - I.x0) * 0.68, fl = (t / 3200) % 1;
      fig(c, L.folk2[0], px, d - hh * 0.02, hh * 0.9, { lean: 0, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [0.4, 0.9, 0.3, 1.0] }, -1);
      var cx2 = I.x0 + (I.x1 - I.x0) * 0.3; fig(c, L.folk2[1], cx2 - hh * 0.2, d - hh * 0.02, hh * 0.92, reach(cx2 - hh * 0.2, d - hh * 0.02, hh * 0.92, { lean: 0.2, legs: [0.1, 0, -0.1, 0], arms: [1, 0.5, 1, 0.5] }, 1, [cx2 - hh * 0.02, d - hh * 0.72], [cx2, d - hh * 0.65]), 1);
      ln(c, [[cx2, d - hh * 0.65], [cx2 - hh * 0.1, d], [cx2, d - hh * 0.65], [cx2 + hh * 0.1, d]], '#3a3a3a', 1.2); fr(c, cx2 - hh * 0.06, d - hh * 0.75, hh * 0.13, hh * 0.09, '#2a2a2e'); fe(c, cx2 + hh * 0.08, d - hh * 0.7, hh * 0.03, hh * 0.035, '#5a6a7a');
      if (fl < 0.08) { c.fillStyle = 'rgba(255,255,255,' + (0.6 * (1 - fl / 0.08)).toFixed(2) + ')'; c.fillRect(I.x0, I.y0, I.x1 - I.x0, d - I.y0); glow(c, cx2, d - hh * 0.8, hh * 0.5, '255,255,255', 1 - fl / 0.08); }
      return; }
    if (V.k === 'funeral') { var fx = I.x0 + (I.x1 - I.x0) * 0.5; fig(c, L.folk2[0], fx, d - hh * 0.02, hh * 0.9, reach(fx, d - hh * 0.02, hh * 0.9, STANDP, 1, [fx + hh * 0.22, d - hh * 0.55 + Math.sin(t / 900) * hh * 0.03], null), 1); }
  },
  fore: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, I = L.in;
    if (V.facade && L.counters) { counter(q, I.x0 + hh * 0.05, I.x1 - hh * 0.05, d - hh * 0.42, S, '#c9a878'); waitChairs(q, I.x0 + hh * 0.1, I.x0 + Math.min(hh * 1.4, (I.x1 - I.x0) * 0.4), S, '#3a6fb0');
      fr(q, I.x1 - hh * 0.3, d - hh * 0.75, hh * 0.18, hh * 0.75, nt(S, '#f2f2ee', 0.2)); fr(q, I.x1 - hh * 0.27, d - hh * 0.7, hh * 0.12, hh * 0.08, nt(S, '#3a6fb0', 0.2)); fr(q, I.x1 - hh * 0.25, d - hh * 0.55, hh * 0.08, hh * 0.02, '#2a2a2a'); }
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    if (V.k === 'utility') { var tx = L.flagX > L.bx1 ? Math.max(L.bx0 - hh * 0.6, S.x0 + hh) : Math.min(L.bx1 + hh * 0.6, S.x1 - hh), tt = d - hh * 2.2, col = nt(S, '#c9ccd4', 0.4);
      [-1, 1].forEach(function (sd) { ln(q, [[tx + sd * hh * 0.3, d + hh * 0.05], [tx + sd * hh * 0.18, tt + hh * 0.5]], col, Math.max(2, hh * 0.04)); });
      ln(q, [[tx - hh * 0.27, d - hh * 0.4], [tx + hh * 0.25, d - hh * 0.9], [tx - hh * 0.22, d - hh * 1.4]], col, 1.5);
      paper(q, function (p) { p.beginPath(); p.moveTo(tx - hh * 0.36, tt + hh * 0.5); p.lineTo(tx - hh * 0.36, tt + hh * 0.15); p.quadraticCurveTo(tx, tt - hh * 0.05, tx + hh * 0.36, tt + hh * 0.15); p.lineTo(tx + hh * 0.36, tt + hh * 0.5); p.closePath(); }, nt(S, '#5a9ad0', 0.4), 1.5);
      fr(q, tx - hh * 0.36, tt + hh * 0.3, hh * 0.72, hh * 0.05, nt(S, '#f2f2ee', 0.4)); }
    if (V.k === 'police') car(q, L.bx1 - hh * 1.1, d + hh * 0.2, hh * 0.95, 'pickup', '#f2f2f2', -1, S);
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t;
    if (V.facade && L.flagX) flag(c, L.flagX, d - hh * 2.15, hh * 0.55, hh * 0.36, t, 1, THAI);
    if (V.facade && L.counters && L.open) { var qx = (L.in.x0 + L.in.x1) / 2; queueBoard(c, qx, L.in.y0 + hh * 0.35, hh, t, S.seed); }
    if (V.k === 'police' && S.night) { var bx = L.bx1 - hh * 1.1 + hh * 0.2, on = Math.floor(t / 400) % 2; glow(c, bx, d - hh * 0.3, hh * 0.25, on ? '255,60,60' : '60,120,255', 0.9); }
    if (V.k === 'water') { var kx = (L.bx0 + L.bx1) / 2, u = (t / 6000) % 1, fill = clamp((u - 0.15) / 0.6, 0, 1), by = d - hh * 0.38;
      fig(c, L.folk2[0], kx + hh * 0.42, d + hh * 0.16, hh * 0.92, reach(kx + hh * 0.42, d + hh * 0.16, hh * 0.92, { lean: 0.2, legs: [0.1, 0, -0.1, 0], arms: [1, 0.5, 1, 0.5] }, -1, [kx + hh * 0.1, by - hh * 0.05], [kx + hh * 0.08, by - hh * 0.15]), -1);
      fr(c, kx - hh * 0.06, by - hh * 0.3, hh * 0.18, hh * 0.3, 'rgba(210,235,250,.55)'); fr(c, kx - hh * 0.06, by - hh * 0.3 * fill, hh * 0.18, hh * 0.3 * fill, 'rgba(120,190,240,.7)');
      if (u > 0.15 && u < 0.75) { c.strokeStyle = 'rgba(150,210,250,.9)'; c.lineWidth = Math.max(1.5, hh * 0.02); c.beginPath(); for (var j = 0; j < 6; j++) { var yy = d - hh * 0.92 + j * hh * 0.08 + (t / 30 % (hh * 0.08)); c.moveTo(kx + hh * 0.03, yy); c.lineTo(kx + hh * 0.03, yy + hh * 0.05); } c.stroke(); } }
  }
}, 'the flag: y = A·(x/L)·sin(kx − ωt)<br>the queue: n = n₀ + ⌊t/T⌋');
/* the drinking-water kiosk: a tank on top, the panel with its drop, the coin slot, the tap bay */
function kiosk(q, S, L) {
  var hh = S.hh, d = S.deck, x = (L.bx0 + L.bx1) / 2, w = hh * 0.8, top = d - hh * 1.65, body = nt(S, pick(rnd(S.seed + 1), ['#2f6fb0', '#1f8a9a', '#3a5fa8', '#2f9ad0']), 0.35);
  paper(q, rect(x - w * 0.9, top - hh * 0.12, w * 1.8, hh * 0.08), nt(S, '#8a8f99', 0.4), 1.3);
  paper(q, rect(x - w / 2, top, w, d - top), body, 1.6);
  paper(q, function (p) { p.beginPath(); p.ellipse(x, top + hh * 0.02, w * 0.38, hh * 0.08, 0, Math.PI, TAU); p.closePath(); }, nt(S, '#f2f2ee', 0.3), 1);
  fr(q, x - w * 0.38, top + hh * 0.12, w * 0.76, hh * 0.5, nt(S, '#f6f6f2', 0.3));
  fp(q, [[x, top + hh * 0.18], [x + hh * 0.1, top + hh * 0.34], [x, top + hh * 0.42], [x - hh * 0.1, top + hh * 0.34]], nt(S, '#3a9ad8', 0.2)); fe(q, x, top + hh * 0.35, hh * 0.1, hh * 0.08, nt(S, '#3a9ad8', 0.2));
  for (var wv = 0; wv < 3; wv++) fr(q, x - w * 0.25, top + hh * (0.47 + wv * 0.04), w * 0.5, 1.5, nt(S, '#3a9ad8', 0.2));
  fr(q, x + w * 0.22, top + hh * 0.7, hh * 0.06, hh * 0.1, nt(S, '#d8dade', 0.3)); fr(q, x + w * 0.24, top + hh * 0.73, hh * 0.02, hh * 0.05, '#2a2a2a');
  digits(q, x - w * 0.15, top + hh * 0.75, hh * 0.08, '00', '#5aff7a');
  fr(q, x - w * 0.36, d - hh * 0.75, w * 0.72, hh * 0.68, nt(S, '#1a2230', 0.2)); fr(q, x - hh * 0.04, d - hh * 0.75, hh * 0.15, hh * 0.08, nt(S, '#c9ccd4', 0.2));
  L.in = { x0: x - w / 2, x1: x + w / 2, y0: top, y1: d };
}
function wreath(q, x, y, s, S, R) {
  ln(q, [[x - s * 0.15, y], [x, y - s * 0.55], [x + s * 0.15, y]], nt(S, '#8a6a4a', 0.3), Math.max(1.5, s * 0.02));
  var cy = y - s * 0.62, r = s * 0.22, pal = pick(R, [['#f2f2ee', '#f7e08a'], ['#f2f2ee', '#b692ff'], ['#f7e08a', '#f2f2ee'], ['#f2f2ee', '#7fd8ff']]);
  for (var i = 0; i < 22; i++) { var a = i / 22 * TAU; fe(q, x + Math.cos(a) * r, cy + Math.sin(a) * r, s * 0.05, s * 0.05, nt(S, pal[i % 2], 0.3)); }
  for (i = 0; i < 8; i++) fe(q, x + Math.cos(i / 8 * TAU + 0.2) * r * 1.18, cy + Math.sin(i / 8 * TAU + 0.2) * r * 1.18, s * 0.04, s * 0.02, nt(S, '#3f7a3a', 0.3), i / 8 * TAU);
  fr(q, x - s * 0.06, cy - r * 0.6, s * 0.12, r * 1.6, nt(S, '#f6f6f2', 0.2));
}

/* salon: the barber's pole turning (its stripes a helix, y = y₀ + vt), the chair, the cape, clippers
   or the straight razor; a stylist's dryer blowing; a manicure table under its lamp; a spa bed and the
   facial steamer; mirrors with bulbs, bottles, the poster of cuts */
addShop('salon', {
  look: function (S, F, R) {
    var k = sub(F, 'barber') || has(F, /barber|บาร์เบอร์|ตัดผมชาย|babershop/i) ? 'barber' : sub(F, 'nails') || has(F, /nail|เล็บ/i) ? 'nails'
      : sub(F, 'cosmetic-tattoo') || has(F, /คิ้ว|brow|lash|ขนตา/i) ? 'brows' : sub(F, 'beauty-spa') || has(F, /spa|สปา|facial|ผิว|skin|beauty|ความงาม|clinic|คลินิก|aesthetic|wax/i) ? 'spa' : 'hair';
    var V = { k: k, light: k === 'spa' ? 'warm' : R() < 0.5 ? 'warm' : 'cool', mix: { casual: 0.85, sin: 0.15 } };
    V.types = k === 'barber' ? { shop: 3, row: 2.4, glass: 1, stall: 0.8 } : k === 'spa' ? { lanna: 2, teak: 2, glass: 2, shop: 1.4 } : { shop: 3, glass: 2.2, row: 1.2, teak: 0.5 };
    if (k === 'spa') V.inWall = pick(R, ['#f3e2bf', '#e8d8c8', '#efe0d0']);
    if (k === 'nails') V.inWall = pick(R, ['#f8e0ea', '#f3e8f0', '#fff0f4']);
    return V;
  },
  plan: function (S, L, V, R) {
    var I = L.in, hh = S.hh, w = I.x1 - I.x0; L.st = []; var n = clamp(Math.floor(w / (hh * 1.25)), 1, 3);
    for (var i = 0; i < n; i++) L.st.push(I.x0 + w * (i + 0.5) / n);
    L.pro = crew(S, 3, { casual: 1 }, 8); L.cus = crew(S, 3, V.mix, 12);
    L.pro.forEach(function (d) { uni(d, V.k === 'spa' ? '#f2e6c9' : V.k === 'nails' ? '#f7c6d8' : pick(R, ['#2a2a2a', '#f2f2ee', '#3a3a5a']), '#2a2a2a'); });
    L.cape = pick(R, ['#f2f2ee', '#2a2a2a', '#c0392b', '#3a6fb0']);
    L.poleX = L.bx0 + hh * 0.08 < S.x0 + hh ? L.bx1 - hh * 0.08 : L.bx0 + hh * 0.08;
  },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 81);
    L.st.forEach(function (x, i) {
      if (V.k === 'spa' || V.k === 'brows') { fr(q, x - hh * 0.3, I.y0 + hh * 0.08, hh * 0.6, hh * 0.3, nt(S, '#e8dcc0', 0.2)); for (var j = 0; j < 3; j++) fe(q, x - hh * 0.15 + j * hh * 0.15, I.y0 + hh * 0.3, hh * 0.06, hh * 0.04, nt(S, ['#f2f2ee', '#e8b8c8', '#c9e0c8'][j], 0.2));
        fr(q, x + hh * 0.35, d - hh * 0.55, 2, hh * 0.55, nt(S, '#5a4a3a')); for (j = 0; j < 4; j++) fe(q, x + hh * 0.36 + Math.cos(j * 1.6) * hh * 0.06, d - hh * 0.6 + Math.sin(j * 1.6) * hh * 0.04, hh * 0.04, hh * 0.03, nt(S, '#d9a0d0', 0.2)); return; }
      if (V.k === 'nails') { for (var r = 0; r < 4; r++) for (j = 0; j < 7; j++) { fe(q, x - hh * 0.3 + j * hh * 0.09, I.y0 + hh * (0.12 + r * 0.1), hh * 0.025, hh * 0.035, nt(S, pick(R, ['#e5567f', '#d9342b', '#ff9ac0', '#9b6bd6', '#f2c94c', '#7fd8ff', '#2a2a2a', '#f2e6c9']), 0.2)); } fr(q, x - hh * 0.35, I.y0 + hh * 0.5, hh * 0.7, 2, nt(S, '#c9ccd4', 0.2)); return; }
      /* a mirror framed in bulbs, a shelf of bottles below */
      var mx = x + hh * 0.22, my = I.y0 + hh * 0.06, mw = hh * 0.42, mh = hh * 0.5;
      fr(q, mx - mw / 2 - 3, my - 3, mw + 6, mh + 6, nt(S, '#3a3a3a', 0.2)); fr(q, mx - mw / 2, my, mw, mh, nt(S, '#bcd6e2', 0.2));
      q.fillStyle = 'rgba(255,255,255,.4)'; q.beginPath(); q.moveTo(mx - mw * 0.3, my + mh); q.lineTo(mx, my); q.lineTo(mx + mw * 0.12, my); q.lineTo(mx - mw * 0.18, my + mh); q.fill();
      for (j = 0; j < 4; j++) fe(q, mx - mw / 2 + j * mw / 3, my - 4, hh * 0.022, hh * 0.022, S.night ? '#fff2c0' : '#f8f0d8');
      goods(q, mx - mw / 2, mx + mw / 2, my + mh + hh * 0.1, hh * 0.1, R, ['#f2f2ee', '#3a6fb0', '#e5567f', '#2a2a2a', '#e8b84a'], S, 'bottle'); fr(q, mx - mw / 2, my + mh + hh * 0.1, mw, 2, nt(S, '#8a6a4a', 0.2));
    });
    if (V.k === 'barber') { var px = I.x0 + hh * 0.08; poster(q, px, I.y0 + hh * 0.05, hh * 0.36, hh * 0.46, S, function (p, x, y, w, h) { fr(p, x, y, w, h, '#f2ead8'); var cuts = ['#1c1410', '#3a2a22']; for (var k = 0; k < 4; k++) { var cx = x + w * (0.27 + (k % 2) * 0.46), cy = y + h * (0.28 + Math.floor(k / 2) * 0.46); fe(p, cx, cy + h * 0.04, w * 0.13, h * 0.12, '#d9a27a'); p.fillStyle = cuts[k % 2]; p.beginPath(); p.ellipse(cx, cy - h * 0.03, w * 0.15, h * (0.06 + k * 0.02), 0, Math.PI, TAU); p.fill(); fr(p, cx - w * 0.1, cy + h * 0.15, w * 0.2, h * 0.06, '#3a6fb0'); } }); }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t;
    L.st.forEach(function (x, i) {
      var cu = L.cus[i], pr = L.pro[i];
      if (V.k === 'spa' || V.k === 'brows') {   /* the bed, the guest under a towel, the steamer or the brow pen */
        var by = d - hh * 0.36; fr(c, x - hh * 0.42, by, hh * 0.82, hh * 0.06, '#f2f2ee'); fr(c, x - hh * 0.38, by + hh * 0.06, hh * 0.04, d - by - hh * 0.06, '#8a6a4a'); fr(c, x + hh * 0.32, by + hh * 0.06, hh * 0.04, d - by - hh * 0.06, '#8a6a4a');
        fe(c, x - hh * 0.32, by - hh * 0.05, hh * 0.09, hh * 0.07, cu.skin); fe(c, x - hh * 0.36, by - hh * 0.08, hh * 0.07, hh * 0.05, V.k === 'spa' && i % 2 === 0 ? '#9ad08a' : cu.hairCol || '#1c1410');
        fp(c, [[x - hh * 0.24, by], [x - hh * 0.22, by - hh * 0.1], [x + hh * 0.36, by - hh * 0.07], [x + hh * 0.38, by]], V.k === 'spa' ? '#f2e6c9' : '#c9e0e8');
        var ty = -Math.abs(Math.sin(t / 700 + i)) * hh * 0.03;
        fig(c, pr, x - hh * 0.62, d - hh * 0.02, hh * 0.9, reach(x - hh * 0.62, d - hh * 0.02, hh * 0.9, { lean: 0.3, legs: [0.1, 0, -0.1, 0], arms: [1, 0.5, 1, 0.5] }, 1, [x - hh * 0.36, by - hh * 0.12 + ty], [x - hh * 0.3, by - hh * 0.08 - ty]), 1);
        if (V.k === 'spa') { ln(c, [[x - hh * 0.1, d], [x - hh * 0.1, by - hh * 0.25], [x - hh * 0.22, by - hh * 0.2]], '#c9ccd4', 1.5); fe(c, x - hh * 0.1, by - hh * 0.28, hh * 0.06, hh * 0.05, '#f2f2ee'); steam(c, x - hh * 0.25, by - hh * 0.18, hh, t, i, 4, hh * 0.12); }
        else { ln(c, [[x - hh * 0.3, by - hh * 0.12 + ty], [x - hh * 0.34, by - hh * 0.07]], '#2a2a2a', 1.5); glow(c, x - hh * 0.3, by - hh * 0.3, hh * 0.2, '255,250,230', 0.7); }
        return; }
      if (V.k === 'nails') {   /* two at the little table, a hand under the lamp, the brush */
        var tx = x, ty2 = d - hh * 0.4;
        fig(c, pr, tx - hh * 0.35, d - hh * 0.02, hh * 0.85, reach(tx - hh * 0.35, d - hh * 0.02, hh * 0.85, SITP, 1, [tx - hh * 0.03 + Math.sin(t / 250) * hh * 0.015, ty2 - hh * 0.04], [tx - hh * 0.06, ty2 - hh * 0.02]), 1);
        fig(c, cu, tx + hh * 0.35, d - hh * 0.02, hh * 0.85, reach(tx + hh * 0.35, d - hh * 0.02, hh * 0.85, SITP, -1, [tx + hh * 0.02, ty2 - hh * 0.03], null), -1);
        glow(c, tx, ty2 - hh * 0.12, hh * 0.18, i % 2 ? '200,140,255' : '255,250,230', 0.8); return; }
      /* the chair, the guest under the cape, the barber or stylist at work */
      var cx = x - hh * 0.05, sy = d - hh * 0.02;
      var me = fig(c, cu, cx, sy, hh * 0.86, { lean: 0, seat: 0.3, legs: [1.45, -1.45, 1.38, -1.4], arms: [0.6, 0.6, 0.5, 0.7] }, 1);
      var hd = me.head; fp(c, [[hd[0] - hh * 0.04, hd[1] + hh * 0.08], [hd[0] + hh * 0.08, hd[1] + hh * 0.08], [cx + hh * 0.32, sy - hh * 0.18], [cx - hh * 0.16, sy - hh * 0.2]], L.cape);
      fr(c, cx - hh * 0.14, sy - hh * 0.28, hh * 0.04, hh * 0.3, '#3a3a3a'); fr(c, cx - hh * 0.06, sy - hh * 0.1, hh * 0.04, hh * 0.1, '#9aa0a8'); fe(c, cx, sy, hh * 0.14, hh * 0.02, '#9aa0a8');
      var wob = Math.sin(t / (V.k === 'barber' ? 140 : 300) + i) * hh * 0.03, tool = [hd[0] - hh * 0.06, hd[1] - hh * 0.02 + wob];
      fig(c, pr, cx - hh * 0.38, sy, hh * 0.95, reach(cx - hh * 0.38, sy, hh * 0.95, STANDP, 1, tool, [hd[0] - hh * 0.04, hd[1] - hh * 0.11]), 1);
      if (V.k === 'barber') { if ((S.seed + i) % 2) { fr(c, tool[0] - hh * 0.02, tool[1] - hh * 0.05, hh * 0.04, hh * 0.09, '#2a2a2a'); for (var k = 0; k < 3; k++) { var u = (t / 900 + k / 3) % 1; fr(c, tool[0] + hh * 0.02 + k * 2, tool[1] + u * hh * 0.5, 1.5, 2, 'rgba(28,20,16,' + (1 - u).toFixed(2) + ')'); } }
        else { ln(c, [[tool[0], tool[1]], [tool[0] + hh * 0.1, tool[1] + hh * 0.06]], '#dfe2ea', 2); fe(c, hd[0] + hh * 0.05, hd[1] + hh * 0.05, hh * 0.05, hh * 0.035, '#ffffff'); } }
      else { if ((S.seed + i) % 2) { fr(c, tool[0] - hh * 0.06, tool[1] - hh * 0.04, hh * 0.1, hh * 0.06, '#2a2a2e'); for (k = 0; k < 3; k++) { var u2 = (t / 500 + k / 3) % 1; ln(c, [[tool[0] + hh * (0.05 + u2 * 0.12), tool[1] - hh * 0.02 + k * 3], [tool[0] + hh * (0.08 + u2 * 0.12), tool[1] - hh * 0.02 + k * 3]], 'rgba(255,255,255,' + (0.7 * (1 - u2)).toFixed(2) + ')', 1); } }
        else { var op = Math.abs(Math.sin(t / 160)) * 0.4; ln(c, [[tool[0], tool[1]], [tool[0] + Math.cos(op) * hh * 0.08, tool[1] - Math.sin(op) * hh * 0.08]], '#dfe2ea', 1.5); ln(c, [[tool[0], tool[1]], [tool[0] + Math.cos(-op) * hh * 0.08, tool[1] - Math.sin(-op) * hh * 0.08]], '#dfe2ea', 1.5); } }
    });
  },
  fore: function (q, S, L, V) { var hh = S.hh, d = S.deck; if (V.k === 'nails') L.st.forEach(function (x) { paper(q, rect(x - hh * 0.18, d - hh * 0.42, hh * 0.36, hh * 0.04), nt(S, '#f2f2ee', 0.2), 1); fr(q, x - hh * 0.15, d - hh * 0.38, hh * 0.3, hh * 0.36, nt(S, '#e8dcd0', 0.2)); }); },
  out: function (q, S, L, V) { var hh = S.hh, d = S.deck; if (V.k !== 'barber') return; var x = L.poleX, y0 = d - L.gf + hh * 0.25; fr(q, x - hh * 0.08, y0 - hh * 0.06, hh * 0.16, hh * 0.06, nt(S, '#d8dade', 0.3)); fr(q, x - hh * 0.08, y0 + hh * 0.56, hh * 0.16, hh * 0.06, nt(S, '#d8dade', 0.3)); fe(q, x, y0 - hh * 0.08, hh * 0.05, hh * 0.04, nt(S, '#d8dade', 0.3)); },
  street: function (S, L, V) {
    if (V.k !== 'barber') return;
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.poleX, y0 = d - L.gf + hh * 0.25, h = hh * 0.56, w = hh * 0.12, off = (t / 40) % (hh * 0.24);
    if (S.night && L.open) glow(c, x, y0 + h / 2, hh * 0.45, '255,240,240', 0.5);
    c.save(); c.beginPath(); c.rect(x - w / 2, y0, w, h); c.clip(); fr(c, x - w / 2, y0, w, h, '#f6f6f2');
    for (var y = y0 - hh * 0.3 + off; y < y0 + h + hh * 0.2; y += hh * 0.24) { fp(c, [[x - w / 2, y], [x + w / 2, y - hh * 0.12], [x + w / 2, y - hh * 0.06], [x - w / 2, y + hh * 0.06]], '#d9242b'); fp(c, [[x - w / 2, y + hh * 0.12], [x + w / 2, y], [x + w / 2, y + hh * 0.06], [x - w / 2, y + hh * 0.18]], '#2a4aa8'); }
    c.fillStyle = 'rgba(255,255,255,.35)'; c.fillRect(x - w * 0.3, y0, w * 0.15, h); c.restore();
  }
}, 'the pole: a helix, y = y₀ + vt<br>the clippers: y = A·sin ωt');

/* ---------------------------------------------------------------- garments, hung from a hook at (x, y) */
function garment(q, x, y, s, kind, col, S) {
  var c = nt(S, col, 0.3), dk = mixc(c, '#000000', 0.2);
  ln(q, [[x, y], [x, y + s * 0.03]], 'rgba(60,60,60,.8)', 1); ln(q, [[x - s * 0.07, y + s * 0.06], [x, y + s * 0.03], [x + s * 0.07, y + s * 0.06]], 'rgba(60,60,60,.8)', 1);
  if (kind === 'dress' || kind === 'gown') { var L2 = kind === 'gown' ? 0.75 : 0.45; fp(q, [[x - s * 0.06, y + s * 0.05], [x + s * 0.06, y + s * 0.05], [x + s * 0.05, y + s * 0.16], [x + s * (kind === 'gown' ? 0.17 : 0.12), y + s * L2], [x - s * (kind === 'gown' ? 0.17 : 0.12), y + s * L2], [x - s * 0.05, y + s * 0.16]], c); fr(q, x - s * 0.05, y + s * 0.15, s * 0.1, s * 0.02, dk); if (kind === 'gown') fr(q, x - s * 0.16, y + s * 0.6, s * 0.32, s * 0.05, nt(S, '#e8b84a', 0.3)); }
  else if (kind === 'pants') fp(q, [[x - s * 0.07, y + s * 0.05], [x + s * 0.07, y + s * 0.05], [x + s * 0.08, y + s * 0.5], [x + s * 0.02, y + s * 0.5], [x, y + s * 0.15], [x - s * 0.02, y + s * 0.5], [x - s * 0.08, y + s * 0.5]], c);
  else { var ln2 = kind === 'jacket' ? 0.38 : 0.3; fp(q, [[x - s * 0.08, y + s * 0.05], [x - s * 0.16, y + s * (kind === 'tee' ? 0.12 : 0.28)], [x - s * 0.12, y + s * (kind === 'tee' ? 0.15 : 0.3)], [x - s * 0.09, y + s * 0.12], [x - s * 0.09, y + s * ln2], [x + s * 0.09, y + s * ln2], [x + s * 0.09, y + s * 0.12], [x + s * 0.12, y + s * (kind === 'tee' ? 0.15 : 0.3)], [x + s * 0.16, y + s * (kind === 'tee' ? 0.12 : 0.28)], [x + s * 0.08, y + s * 0.05]], c);
    if (kind === 'shirt' || kind === 'jacket') { ln(q, [[x, y + s * 0.06], [x, y + s * ln2]], dk, 1); fp(q, [[x - s * 0.04, y + s * 0.05], [x, y + s * 0.1], [x + s * 0.04, y + s * 0.05]], kind === 'jacket' ? dk : '#f2f2ee'); }
    else fe(q, x, y + s * 0.06, s * 0.03, s * 0.015, dk); }
}
function rail(q, x0, x1, y, s, S, R, kinds, pal) {
  fr(q, x0, y - 1, x1 - x0, 2.5, nt(S, '#9aa0a8', 0.3));
  for (var x = x0 + s * 0.12; x < x1 - s * 0.08; x += s * (0.12 + R() * 0.06)) garment(q, x, y, s, pick(R, kinds), pick(R, pal), S);
}
function mannequin(q, x, y, s, col, S) {
  ln(q, [[x, y], [x, y - s * 0.45]], nt(S, '#5a5e66', 0.3), Math.max(1.5, s * 0.02)); fe(q, x, y, s * 0.1, s * 0.02, nt(S, '#5a5e66', 0.3));
  fp(q, [[x - s * 0.1, y - s * 0.95], [x + s * 0.1, y - s * 0.95], [x + s * 0.08, y - s * 0.7], [x + s * 0.15, y - s * 0.45], [x - s * 0.15, y - s * 0.45], [x - s * 0.08, y - s * 0.7]], nt(S, col, 0.3));
  fe(q, x, y - s * 1.0, s * 0.05, s * 0.04, nt(S, '#e8dcc8', 0.3));
}
function guitar(q, x, y, s, col, S) {
  fe(q, x, y + s * 0.18, s * 0.11, s * 0.13, nt(S, col, 0.3)); fe(q, x, y + s * 0.02, s * 0.08, s * 0.09, nt(S, col, 0.3)); fe(q, x, y + s * 0.1, s * 0.03, s * 0.03, '#1a1a1a');
  fr(q, x - s * 0.015, y - s * 0.3, s * 0.03, s * 0.32, nt(S, '#5a3a22', 0.3)); fr(q, x - s * 0.025, y - s * 0.36, s * 0.05, s * 0.07, nt(S, '#3a2a1a', 0.3));
}

/* clothes: rails of tees and dresses, mannequins, folded stacks; the tailor at the sewing machine (the
   needle, y = A·sin ωt); bolts of cloth; a wall of shoes; buckets and brooms of a housewares shop; paint
   tins and ladders; guitars and their notes; gowns for hire; racks out on the pavement, swaying */
addShop('clothes', {
  look: function (S, F, R) {
    var k = sub(F, 'tailor') || sub(F, 'alterations') || has(F, /tailor|ตัดเย็บ|ตัดชุด|ซ่อมเสื้อ|แก้ผ้า|แก้เสื้อ|ปัก|สูท|suit|alter/i) ? 'tailor' : sub(F, 'fabric') || has(F, /ร้านผ้า|ขายผ้า|fabric|textile|ผ้าม่าน/i) ? 'fabric'
      : sub(F, 'shoes') || has(F, /รองเท้า|shoe|bata|skechers|sneaker/i) ? 'shoes' : sub(F, 'sports-shop') || has(F, /sport|กีฬา|fitness|bike shop/i) ? 'sports'
      : sub(F, 'music') || has(F, /ดนตรี|music|guitar|กีตาร์|เปียโน|piano|drum/i) ? 'music' : sub(F, 'dresshire') || has(F, /เช่าชุด|ชุดไทย|wedding|bridal|dress/i) ? 'gowns'
      : sub(F, 'diy') || has(F, /hardware|วัสดุ|ก่อสร้าง|\bสี\b|paint|diy|tool|เครื่องมือ|cotto|homepro|global house|ไทวัสดุ|dohome|บุญถาวร|toa\b/i) ? 'diy'
      : sub(F, 'home') || has(F, /ของใช้|home|house|เครื่องครัว|พลาสติก|ร้านค้า|ของชำ|เบ็ดเตล็ด/i) ? 'home' : 'clothes';
    var V = { k: k, light: 'warm', mix: { casual: 0.75, sin: 0.18, mohom: 0.07 } };
    V.types = k === 'home' || k === 'diy' ? { row: 3, shop: 2, stall: 1.2 } : k === 'gowns' ? { glass: 2, lanna: 1, shop: 2 } : k === 'tailor' || k === 'fabric' ? { shop: 3, row: 2, teak: 0.8 } : { shop: 3, glass: 2, row: 2, stall: 0.8, teak: 0.4 };
    if (k === 'diy') V.light = 'cool';
    return V;
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 4, V.mix, 15); L.pal = [pick(R, CLOTHS), pick(R, CLOTHS), pick(R, CLOTHS), pick(R, CLOTHS), '#f2f2ee', '#2c3e6b']; L.outRack = R() < 0.7 && L.open; L.rackSide = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? 0 : 1; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 91), w = I.x1 - I.x0, k = V.k, i, x;
    if (k === 'clothes' || k === 'gowns') { rail(q, I.x0 + hh * 0.08, I.x1 - hh * 0.08, I.y0 + hh * 0.08, hh * 0.9, S, R, k === 'gowns' ? ['gown', 'gown', 'dress'] : ['tee', 'shirt', 'dress', 'jacket'], L.pal);
      if (k === 'clothes') rail(q, I.x0 + hh * 0.08, I.x0 + w * 0.55, d - hh * 0.6, hh * 0.9, S, R, ['tee', 'pants', 'shirt'], L.pal);
      shelves(q, I.x1 - hh * 0.75, I.x1 - hh * 0.08, d - hh * 0.62, d - hh * 0.02, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.15; xx += hh * 0.2) for (var j = 0; j < 3; j++) fr(p, xx, yb - (j + 1) * h * 0.3, hh * 0.17, h * 0.28, nt(S, pick(R, L.pal), 0.3)); }); }
    else if (k === 'tailor' || k === 'fabric') { shelves(q, I.x0 + hh * 0.06, I.x0 + Math.max(hh * 0.9, w * 0.45), I.y0 + hh * 0.04, d - hh * 0.04, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.06; xx += hh * 0.08) { var cc = nt(S, pick(R, CLOTHS), 0.3); fr(p, xx, yb - h * 0.9, hh * 0.07, h * 0.9, cc); fr(p, xx, yb - h * 0.9, hh * 0.07, 2, mixc(cc, '#ffffff', 0.3)); } });
      if (k === 'tailor') { for (i = 0; i < 3; i++) garment(q, I.x1 - hh * (0.3 + i * 0.22), I.y0 + hh * 0.08, hh * 0.9, i % 2 ? 'jacket' : 'shirt', pick(R, ['#2c2f45', '#3a3a3a', '#5a4a3a', '#f2f2ee']), S); for (i = 0; i < 12; i++) fe(q, I.x1 - hh * 0.75 + (i % 6) * hh * 0.1, d - hh * (0.55 + Math.floor(i / 6) * 0.08), hh * 0.03, hh * 0.035, nt(S, pick(R, CLOTHS), 0.3)); } }
    else if (k === 'shoes') shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.04, 5, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.2; xx += hh * 0.22) { var cc = nt(S, pick(R, ['#2a2a2a', '#8a5a3a', '#f2f2ee', '#d9342b', '#3a6fb0', '#e8b84a']), 0.3); [0, 0.09].forEach(function (o) { fp(p, [[xx + hh * o, yb], [xx + hh * o, yb - h * 0.5], [xx + hh * (o + 0.04), yb - h * 0.55], [xx + hh * (o + 0.08), yb - h * 0.25], [xx + hh * (o + 0.09), yb]], cc); }); } });
    else if (k === 'sports') { for (i = 0; i < Math.floor(w / (hh * 0.3)); i++) garment(q, I.x0 + hh * 0.2 + i * hh * 0.3, I.y0 + hh * 0.06, hh * 0.9, 'tee', pick(R, ['#d9342b', '#3a6fb0', '#f2c94c', '#2f9a5a', '#f2f2ee']), S);
      for (i = 0; i < 7; i++) { var bx = I.x1 - hh * 0.6 + (i % 4) * hh * 0.13, by = d - hh * (0.08 + Math.floor(i / 4) * 0.13); fe(q, bx, by, hh * 0.065, hh * 0.065, nt(S, ['#f2f2ee', '#f08a3a', '#f2c94c', '#2a2a2a'][i % 4], 0.3)); } }
    else if (k === 'music') { for (i = 0; i < Math.floor(w / (hh * 0.32)); i++) guitar(q, I.x0 + hh * 0.22 + i * hh * 0.32, I.y0 + hh * 0.18, hh * 0.9, pick(R, ['#c9853a', '#8a3b2a', '#2a2a2a', '#d9342b', '#f2e6c9', '#3a6fb0']), S);
      fe(q, I.x1 - hh * 0.45, d - hh * 0.18, hh * 0.18, hh * 0.15, nt(S, '#c0392b', 0.3)); fe(q, I.x1 - hh * 0.45, d - hh * 0.18, hh * 0.12, hh * 0.1, nt(S, '#f2f2ee', 0.3)); fe(q, I.x1 - hh * 0.2, d - hh * 0.5, hh * 0.12, hh * 0.02, nt(S, '#e8b84a', 0.3)); }
    else if (k === 'home') { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.04, 3, S, function (p, a, b, yb, h, r) { for (var xx = a; xx < b - hh * 0.18; xx += hh * 0.2) { var cc = nt(S, pick(R, ['#d9342b', '#3a6fb0', '#2f9a5a', '#f2c94c', '#e5567f', '#f2f2ee']), 0.3);
          if (r % 2) for (var j = 0; j < 3; j++) fp(p, [[xx, yb - j * h * 0.18], [xx + hh * 0.17, yb - j * h * 0.18], [xx + hh * 0.15, yb - j * h * 0.18 - h * 0.2], [xx + hh * 0.02, yb - j * h * 0.18 - h * 0.2]], cc);
          else { fp(p, [[xx + hh * 0.02, yb], [xx + hh * 0.15, yb], [xx + hh * 0.17, yb - h * 0.75], [xx, yb - h * 0.75]], cc); ln(p, [[xx + hh * 0.01, yb - h * 0.75], [xx + hh * 0.085, yb - h * 0.95], [xx + hh * 0.16, yb - h * 0.75]], cc, 1); } } }); }
    else { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.04, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.14; xx += hh * 0.15) { var cc = nt(S, pick(R, ['#d9342b', '#3a6fb0', '#2f9a5a', '#f2c94c', '#f2f2ee', '#9b6bd6']), 0.3); fr(p, xx, yb - h * 0.6, hh * 0.13, h * 0.6, nt(S, '#c9ccd4', 0.3)); fr(p, xx, yb - h * 0.45, hh * 0.13, h * 0.25, cc); fe(p, xx + hh * 0.065, yb - h * 0.6, hh * 0.065, h * 0.05, nt(S, '#9aa0a8', 0.3)); } }); }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, w = I.x1 - I.x0, k = V.k;
    if (k === 'tailor') { var mx = I.x0 + w * 0.6; fig(c, L.ppl[0], mx - hh * 0.32, d - hh * 0.02, hh * 0.88, reach(mx - hh * 0.32, d - hh * 0.02, hh * 0.88, SITP, 1, [mx - hh * 0.05, d - hh * 0.46], [mx + hh * 0.05 + Math.sin(t / 600) * hh * 0.02, d - hh * 0.45]), 1); L.needle = [mx + hh * 0.08, d - hh * 0.62]; }
    else if (k === 'music') { var gx = I.x0 + w * 0.55, strum = Math.sin(t / 130) * hh * 0.03; var me = fig(c, L.ppl[0], gx, d - hh * 0.02, hh * 0.88, reach(gx, d - hh * 0.02, hh * 0.88, SITP, 1, [gx + hh * 0.12, d - hh * 0.5 + strum], [gx + hh * 0.3, d - hh * 0.62]), 1);
      c.save(); c.translate(gx + hh * 0.14, d - hh * 0.5); c.rotate(-1.1); fe(c, 0, 0, hh * 0.1, hh * 0.12, '#c9853a'); fr(c, -hh * 0.015, -hh * 0.38, hh * 0.03, hh * 0.3, '#5a3a22'); c.restore(); K.notes(c, gx + hh * 0.2, d - hh * 0.75, t, 3, '#f2c94c'); }
    else if (k === 'home' || k === 'diy') { var sx = I.x0 + w * 0.4; fig(c, L.ppl[0], sx, d - hh * 0.02, hh * 0.88, sitTalk(t, 1), 1); fig(c, L.ppl[1], sx + hh * 0.55, d - hh * 0.02, hh * 0.92, talk(t, 3), -1); }
    else { /* a shopper flicking through the rail, the seller folding */
      var bx = I.x0 + w * 0.3 + Math.sin(t / 5000) * hh * 0.2, flick = Math.sin(t / 380) * hh * 0.05;
      fig(c, L.ppl[0], bx, d - hh * 0.02, hh * 0.92, reach(bx, d - hh * 0.02, hh * 0.92, STANDP, 1, [bx + hh * 0.25 + flick, d - hh * 0.62], null), 1);
      var fx = I.x1 - hh * 0.95; fig(c, L.ppl[1], fx, d - hh * 0.02, hh * 0.9, reach(fx, d - hh * 0.02, hh * 0.9, STANDP, 1, [fx + hh * 0.2, d - hh * 0.45 - Math.abs(Math.sin(t / 700)) * hh * 0.08], [fx + hh * 0.25, d - hh * 0.42]), 1); }
  },
  fore: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 93), w = I.x1 - I.x0;
    if (V.k === 'tailor') { var mx = I.x0 + w * 0.6; desk(q, mx - hh * 0.15, mx + hh * 0.4, S, '#8a6a4a'); var y = d - hh * 0.4; paper(q, poly([[mx - hh * 0.05, y], [mx - hh * 0.05, y - hh * 0.2], [mx + hh * 0.22, y - hh * 0.2], [mx + hh * 0.22, y - hh * 0.12], [mx + hh * 0.12, y - hh * 0.12], [mx + hh * 0.12, y]]), nt(S, '#2a2a2e', 0.2), 1); fe(q, mx + hh * 0.02, y - hh * 0.16, hh * 0.02, hh * 0.02, '#e8b84a'); fr(q, mx - hh * 0.1, y - 3, hh * 0.45, 3, nt(S, pick(R, CLOTHS), 0.2));
      mannequin(q, I.x0 + hh * 0.3 > mx - hh * 0.7 ? I.x1 - hh * 0.25 : I.x0 + hh * 1.05, d, hh * 0.9, pick(R, ['#2c2f45', '#f2f2ee', '#7a1f3a']), S); }
    if (V.k === 'clothes' || V.k === 'gowns') mannequin(q, I.x0 + w * 0.08 + hh * 0.15, d, hh * 0.92, pick(R, L.pal), S);
    if (V.k === 'fabric') { counter(q, I.x0 + w * 0.5, I.x1 - hh * 0.05, d - hh * 0.42, S, '#c9a878'); fr(q, I.x0 + w * 0.52, d - hh * 0.44, w * 0.4, 3, nt(S, pick(R, CLOTHS), 0.2)); }
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, R = rnd(S.seed + 95), sd = L.sides[L.rackSide], k = V.k;
    if (!L.open) return;
    if (k === 'home' || k === 'diy') { var x0 = L.in.x0 + hh * 0.1; for (var i = 0; i < 3; i++) { var bx = x0 + i * hh * 0.24, cc = nt(S, pick(R, ['#d9342b', '#3a6fb0', '#2f9a5a', '#f2c94c']), 0.35); for (var j = 0; j < 3; j++) fp(q, [[bx, d + hh * 0.12 - j * hh * 0.07], [bx + hh * 0.2, d + hh * 0.12 - j * hh * 0.07], [bx + hh * 0.18, d - hh * 0.1 - j * hh * 0.07], [bx + hh * 0.02, d - hh * 0.1 - j * hh * 0.07]], cc); }
      if (k === 'diy') { var lx = L.in.x1 - hh * 0.3; ln(q, [[lx, d + hh * 0.12], [lx + hh * 0.18, d - hh * 1.0]], nt(S, '#c9ccd4', 0.35), 2); ln(q, [[lx + hh * 0.2, d + hh * 0.12], [lx + hh * 0.36, d - hh * 1.0]], nt(S, '#c9ccd4', 0.35), 2); for (j = 0; j < 6; j++) ln(q, [[lx + j * hh * 0.032, d + hh * 0.05 - j * hh * 0.18], [lx + hh * 0.2 + j * hh * 0.03, d + hh * 0.05 - j * hh * 0.18]], nt(S, '#c9ccd4', 0.35), 1.5); }
      else for (i = 0; i < 4; i++) { var bx2 = L.in.x1 - hh * (0.2 + i * 0.08); ln(q, [[bx2, d + hh * 0.1], [bx2 + hh * 0.03, d - hh * 0.75]], nt(S, '#c9a66b', 0.35), 2); fp(q, [[bx2 - hh * 0.05, d - hh * 0.75], [bx2 + hh * 0.1, d - hh * 0.75], [bx2 + hh * 0.06, d - hh * 1.0], [bx2 - hh * 0.01, d - hh * 1.0]], nt(S, i % 2 ? '#d9342b' : '#e8c86a', 0.35)); }
      return; }
    if (k === 'clothes' || k === 'sports' || k === 'shoes') { if (sd.b - sd.a < hh * 0.9) return; var rx0 = L.rackSide ? sd.a + hh * 0.1 : sd.b - hh * 0.95; ln(q, [[rx0, d + hh * 0.12], [rx0, d - hh * 0.95], [rx0 + hh * 0.85, d - hh * 0.95], [rx0 + hh * 0.85, d + hh * 0.12]], nt(S, '#9aa0a8', 0.35), 2);
      L.rackAt = [rx0, rx0 + hh * 0.85, d - hh * 0.95];
      }
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, t = S.t;
    if (V.k === 'tailor' && L.open && L.needle) { var y = L.needle[1] + Math.abs(Math.sin(t / 60)) * hh * 0.06; ln(c, [[L.needle[0], L.needle[1]], [L.needle[0], y + hh * 0.04]], '#dfe2ea', 1.2); }
    if (L.rackAt && L.open) { var R = rnd(S.seed + 97); for (var x = L.rackAt[0] + hh * 0.1, k = 0; x < L.rackAt[1] - hh * 0.05; x += hh * 0.14, k++) { c.save(); c.translate(x, L.rackAt[2]); c.rotate(0.06 * Math.sin(t / 900 + k * 0.7)); garment(c, 0, 0, hh * 0.85, pick(R, ['tee', 'shirt', 'dress']), pick(R, L.pal), S); c.restore(); } }
  }
}, 'the needle: y = A·|sin ωt|<br>the rail: θ = θ₀·sin(ωt + kφ)');

/* fixit: a phone opened under the ring lamp and the tweezers; a bench of computers; televisions that
   flicker; the fan on test spinning; air-conditioners on the wall and the gauges; a wall of key blanks
   and the cutter's sparks; the cobbler's hammer tapping, d = A·|sin ωt|; clocks with pendulums,
   θ = θ₀·cos(√(g/L)·t) */
addShop('fixit', {
  route: function (S, F) { return has(F, /cotto|mr\.? ?diy|homepro|global house|ไทวัสดุ|dohome|บุญถาวร|power ?mart|เพาเวอร์มาร์ท/i) ? 'clothes' : null; },
  look: function (S, F, R) {
    var k = has(F, /กุญแจ|key|locksmith/i) ? 'key' : has(F, /รองเท้า|shoe|cobbler|กระเป๋า|bag/i) ? 'shoe' : has(F, /นาฬิกา|watch|clock/i) ? 'watch'
      : has(F, /แอร์|air ?con|aircon|เครื่องปรับอากาศ|\bair\b/i) ? 'aircon' : has(F, /คอม|computer|notebook|laptop|\bpc\b|printer/i) ? 'comp'
      : has(F, /ทีวี|\btv\b|electronic|อิเล็ก|วิทยุ|radio|เครื่องเสียง|audio|camera|กล้อง|lens/i) ? 'elec'
      : has(F, /มือถือ|phone|iphone|mobile|dtac|\bais\b|true|samsung|oppo|vivo|huawei|xiaomi|โทรศัพท์|ไอโฟน|apple/i) ? 'phone'
      : has(F, /พัดลม|fan|ตู้เย็น|เครื่องซักผ้า|appliance|ไฟฟ้า|electric|ช่าง/i) ? 'appl'
      : sub(F, 'mend') ? pick(R, ['key', 'shoe', 'watch']) : sub(F, 'tech') ? pick(R, ['phone', 'phone', 'comp', 'elec']) : pick(R, ['appl', 'aircon', 'elec']);
    var V = { k: k, light: 'cool', mix: { casual: 0.9, sin: 0.1 } };
    V.types = k === 'key' || k === 'shoe' ? { stall: 3, row: 1.5, shop: 1 } : k === 'phone' || k === 'watch' ? { shop: 3, glass: 2.4, row: 1.2 } : { row: 3, shop: 3, stall: 0.6 };
    if (k === 'key' || k === 'shoe') V.w = 3 + R() * 0.8;
    return V;
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 17); L.benchX = L.in.x0 + (L.in.x1 - L.in.x0) * (0.45 + R() * 0.15); },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 101), w = I.x1 - I.x0, k = V.k, i, x, y;
    if (k === 'phone') { fr(q, I.x0 + hh * 0.06, I.y0 + hh * 0.04, w - hh * 0.12, hh * 0.5, nt(S, '#d8d2c4', 0.2)); for (x = I.x0 + hh * 0.12; x < I.x1 - hh * 0.12; x += hh * 0.13) for (y = 0; y < 3; y++) { fr(q, x, I.y0 + hh * (0.08 + y * 0.15), 1, hh * 0.03, '#5a5e66'); fr(q, x - hh * 0.035, I.y0 + hh * (0.11 + y * 0.15), hh * 0.07, hh * 0.1, nt(S, pick(R, ['#e5567f', '#2a2a2a', '#7fd8ff', '#f2c94c', '#9b6bd6', '#f2f2ee', '#4fae8c']), 0.2)); } }
    else if (k === 'comp' || k === 'elec') { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.5, 2, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.3; xx += hh * 0.34) { fr(p, xx, yb - h * 0.85, hh * 0.3, h * 0.85, nt(S, '#2a2a2e', 0.2)); fr(p, xx + 2, yb - h * 0.85 + 2, hh * 0.3 - 4, h * 0.85 - 6, k === 'comp' ? '#3a4a5a' : '#1a1a22'); } }); }
    else if (k === 'aircon') { for (i = 0; i < Math.floor(w / (hh * 0.9)); i++) { var ax = I.x0 + hh * 0.1 + i * hh * 0.9; paper(q, rect(ax, I.y0 + hh * 0.08, hh * 0.75, hh * 0.2), nt(S, '#f6f6f2', 0.2), 1); fr(q, ax + hh * 0.05, I.y0 + hh * 0.24, hh * 0.65, 2, 'rgba(0,0,0,.25)'); }
      for (i = 0; i < 2; i++) { var ox = I.x1 - hh * 0.5; paper(q, rect(ox - hh * 0.25, d - hh * (0.36 + i * 0.36), hh * 0.5, hh * 0.34), nt(S, '#e8e8e2', 0.2), 1); q.strokeStyle = 'rgba(0,0,0,.35)'; q.lineWidth = 1; q.beginPath(); q.arc(ox - hh * 0.06, d - hh * (0.19 + i * 0.36), hh * 0.12, 0, TAU); q.stroke(); } }
    else if (k === 'appl') { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.55, 2, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.2; xx += hh * 0.24) { fe(p, xx + hh * 0.1, yb - h * 0.35, hh * 0.1, h * 0.35, nt(S, pick(R, ['#f2f2ee', '#e5567f', '#f2c94c', '#c9ccd4']), 0.2)); fe(p, xx + hh * 0.1, yb - h * 0.7, hh * 0.08, h * 0.08, nt(S, '#5a5e66', 0.2)); } });
      for (i = 0; i < 3; i++) fan(q, I.x0 + hh * (0.3 + i * 0.32), d, hh * 0.85, i * 400, nt(S, pick(R, ['#3a6fb0', '#f2f2ee', '#2f9a5a', '#e5567f']), 0.2)); }
    else if (k === 'key') { fr(q, I.x0 + hh * 0.06, I.y0 + hh * 0.04, w - hh * 0.12, hh * 0.6, nt(S, '#3a3a3a', 0.2)); for (x = I.x0 + hh * 0.12; x < I.x1 - hh * 0.1; x += hh * 0.07) for (y = 0; y < 5; y++) { var kx = x + (y % 2) * hh * 0.03, ky = I.y0 + hh * (0.08 + y * 0.11); fe(q, kx, ky, hh * 0.02, hh * 0.02, nt(S, R() < 0.6 ? '#d9b84a' : '#c9ccd4', 0.2)); fr(q, kx - hh * 0.006, ky, hh * 0.012, hh * 0.06, nt(S, R() < 0.6 ? '#d9b84a' : '#c9ccd4', 0.2)); } }
    else if (k === 'shoe') { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.04, d - hh * 0.45, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.2; xx += hh * 0.22) fp(p, [[xx, yb], [xx, yb - h * 0.5], [xx + hh * 0.05, yb - h * 0.55], [xx + hh * 0.15, yb - h * 0.25], [xx + hh * 0.17, yb]], nt(S, pick(R, ['#2a2a2a', '#8a5a3a', '#5a3a22', '#f2f2ee']), 0.3)); }); }
    else if (k === 'watch') { for (i = 0; i < 4; i++) { var cx = I.x0 + hh * 0.25 + i * (w - hh * 0.5) / 3; fr(q, cx - hh * 0.09, I.y0 + hh * 0.05, hh * 0.18, hh * 0.5, nt(S, '#6a4a2a', 0.2)); fe(q, cx, I.y0 + hh * 0.14, hh * 0.07, hh * 0.07, '#fffaf0'); } }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, w = I.x1 - I.x0, k = V.k, bx = L.benchX, by = d - hh * 0.42;
    if (k === 'watch') for (var i = 0; i < 4; i++) { var cx = I.x0 + hh * 0.25 + i * (w - hh * 0.5) / 3, th = 0.3 * Math.cos(Math.sqrt(9.8 / 0.25) * t / 1000 * 0.5 + i); clock(c, cx, I.y0 + hh * 0.14, hh * 0.06, S.now + i * 3600e3 * 0);
      ln(c, [[cx, I.y0 + hh * 0.22], [cx + Math.sin(th) * hh * 0.22, I.y0 + hh * 0.22 + Math.cos(th) * hh * 0.22]], '#c9a83a', 1); fe(c, cx + Math.sin(th) * hh * 0.22, I.y0 + hh * 0.22 + Math.cos(th) * hh * 0.22, hh * 0.03, hh * 0.03, '#d9b84a'); }
    if (k === 'elec') { var R = rnd(S.seed + 103); for (var x = I.x0 + hh * 0.08, j = 0; x < I.x1 - hh * 0.36; x += hh * 0.34, j++) { var f = Math.sin(t / 400 + j * 1.7); if (j % 3 === 0) { var bars = ['#f2f2ee', '#f2c94c', '#7fd8ff', '#7fe0a4', '#e5567f', '#d9342b', '#3a6fb0']; for (var b = 0; b < 7; b++) fr(c, x + 2 + b * (hh * 0.26 / 7), I.y0 + hh * 0.08, hh * 0.26 / 7, hh * 0.14, bars[b]); } else fr(c, x + 2, I.y0 + hh * 0.08, hh * 0.26, hh * 0.14, 'rgba(120,190,230,' + (0.35 + 0.25 * f).toFixed(2) + ')'); } }
    if (k === 'shoe' || k === 'key') { var sx = I.x0 + w * 0.42, tap = Math.pow(Math.abs(Math.sin(t / 220)), 2);
      fig(c, L.ppl[0], sx, d - hh * 0.02, hh * 0.85, reach(sx, d - hh * 0.02, hh * 0.85, { lean: 0.35, seat: 0.22, legs: [1.6, -1.9, 1.5, -1.9], arms: [1, 0.5, 1, 0.5] }, 1, [sx + hh * 0.28, d - hh * (0.38 + 0.12 * tap)], [sx + hh * 0.3, d - hh * 0.3]), 1);
      if (k === 'shoe') { fr(c, sx + hh * 0.26, d - hh * 0.28, hh * 0.04, hh * 0.28, '#5a3a22'); fp(c, [[sx + hh * 0.2, d - hh * 0.28], [sx + hh * 0.22, d - hh * 0.36], [sx + hh * 0.38, d - hh * 0.33], [sx + hh * 0.4, d - hh * 0.28]], '#3a2a1a'); fr(c, sx + hh * 0.26, d - hh * (0.42 + 0.12 * tap), hh * 0.08, hh * 0.03, '#5a5e66'); }
      else { fr(c, sx + hh * 0.24, d - hh * 0.42, hh * 0.22, hh * 0.12, '#5a6a7a'); fe(c, sx + hh * 0.3, d - hh * 0.46, hh * 0.05, hh * 0.05, '#c9ccd4'); if ((t / 2000) % 1 < 0.5) sparks(c, sx + hh * 0.3, d - hh * 0.44, hh * 0.6, t, 8, 1); }
      return; }
    if (k === 'aircon') { var ax = I.x1 - hh * 1.1; fig(c, L.ppl[0], ax, d - hh * 0.02, hh * 0.9, reach(ax, d - hh * 0.02, hh * 0.9, CROUCH, 1, [ax + hh * 0.3, d - hh * 0.25], [ax + hh * 0.28, d - hh * 0.3]), 1);
      [0, 1].forEach(function (g) { var gx = ax + hh * (0.15 + g * 0.12), gy = d - hh * 0.5; fe(c, gx, gy, hh * 0.045, hh * 0.045, '#f2f2ee'); var a = -2 + Math.sin(t / 700 + g) * 0.4 + g; ln(c, [[gx, gy], [gx + Math.cos(a) * hh * 0.035, gy + Math.sin(a) * hh * 0.035]], '#d9342b', 1); }); return; }
    /* the bench: the tech under the lamp */
    fig(c, L.ppl[0], bx - hh * 0.32, d - hh * 0.02, hh * 0.88, reach(bx - hh * 0.32, d - hh * 0.02, hh * 0.88, { lean: 0.32, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [1, 0.5, 1, 0.5] }, 1, [bx - hh * 0.02 + Math.sin(t / 300) * hh * 0.02, by - hh * 0.04], [bx + hh * 0.06, by - hh * 0.03]), 1);
    if (k === 'appl') fan(c, bx + hh * 0.42, d, hh * 0.85, t, '#3a6fb0');
    if (k === 'phone') { fr(c, bx - hh * 0.02, by - hh * 0.02, hh * 0.12, hh * 0.02, '#bfe6f2'); for (var s2 = 0; s2 < 2; s2++) { var u = (t / 1800 + s2 / 2) % 1; c.strokeStyle = 'rgba(230,230,230,' + (0.6 * (1 - u)).toFixed(2) + ')'; c.lineWidth = 1; c.beginPath(); c.moveTo(bx + hh * 0.04, by - hh * 0.04 - u * hh * 0.3); c.quadraticCurveTo(bx + hh * (0.04 + 0.05 * Math.sin(u * 6)), by - hh * 0.1 - u * hh * 0.3, bx + hh * 0.03, by - hh * 0.16 - u * hh * 0.3); c.stroke(); } }
  },
  fore: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, k = V.k, bx = L.benchX, R = rnd(S.seed + 105);
    if (k === 'shoe' || k === 'key' || k === 'aircon') return;
    var y = desk(q, bx - hh * 0.12, bx + hh * 0.3, S, '#8a8070');
    if (k === 'phone' || k === 'watch') { ln(q, [[bx + hh * 0.25, y], [bx + hh * 0.2, y - hh * 0.35], [bx + hh * 0.06, y - hh * 0.32]], nt(S, '#3a3a3a', 0.2), 1.5); q.strokeStyle = '#f2f2ee'; q.lineWidth = 2; q.beginPath(); q.ellipse(bx + hh * 0.05, y - hh * 0.3, hh * 0.08, hh * 0.03, 0, 0, TAU); q.stroke(); glow(q, bx + hh * 0.05, y - hh * 0.2, hh * 0.22, '255,250,235', 0.7);
      counter(q, I.x1 - Math.min(hh * 1.0, (I.x1 - I.x0) * 0.32), I.x1 - hh * 0.04, d - hh * 0.45, S, '#c9ccd4', true);
      for (var x = I.x1 - Math.min(hh * 1.0, (I.x1 - I.x0) * 0.32) + hh * 0.08; x < I.x1 - hh * 0.1; x += hh * 0.12) { if (k === 'watch') { fe(q, x + hh * 0.04, d - hh * 0.28, hh * 0.035, hh * 0.035, nt(S, R() < 0.5 ? '#d9b84a' : '#c9ccd4', 0.2)); } else { fr(q, x, d - hh * 0.36, hh * 0.08, hh * 0.15, nt(S, '#1a1a22', 0.2)); fr(q, x + 2, d - hh * 0.35, hh * 0.08 - 4, hh * 0.04, 'rgba(255,255,255,.3)'); } } }
    if (k === 'comp' || k === 'elec') { screen(q, bx + hh * 0.12, y, hh, S, true); }
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    if (V.k === 'aircon' && L.open) { var sd = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? L.sides[0] : L.sides[1]; if (sd.b - sd.a > hh * 0.8) { var ox = (sd.a + sd.b) / 2; paper(q, rect(ox - hh * 0.25, d - hh * 0.3 + hh * 0.12, hh * 0.5, hh * 0.3), nt(S, '#e8e8e2', 0.3), 1); q.strokeStyle = 'rgba(0,0,0,.35)'; q.beginPath(); q.arc(ox - hh * 0.06, d - hh * 0.03, hh * 0.1, 0, TAU); q.stroke(); } }
  }
}, 'the tap: d = A·|sin ωt|<br>a pendulum: θ = θ₀·cos(√(g/L)·t)');

/* pharmacy: the green cross glowing on the wall (it breathes, a = a₀ + b·sin ωt), floor-to-ceiling
   shelves of little boxes, the glass counter, the pharmacist in a white coat reaching for a box and
   bagging it; the coin scale out front; a brand only tints the board */
addShop('pharmacy', {
  look: function (S, F, R) {
    var tint = has(F, /boots|บู๊ทส์/i) ? '#1f2f7a' : has(F, /watsons|วัตสัน/i) ? '#00979e' : has(F, /fascino|ฟาสซิโน/i) ? '#b0306a' : has(F, /pure|เพียว/i) ? '#3a9a3a' : pick(R, ['#1f8a4a', '#2f7f6b', '#1f6f5a', '#2a8a3a']);
    return { tint: tint, board: tint, light: 'cool', inWall: '#f0f6f2', types: { shop: 4, glass: 2.4, row: 1.4 }, mix: { casual: 0.8, sin: 0.12, mohom: 0.08 }, crossX: R() < 0.5 ? 0 : 1, scale: R() < 0.6 };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 19); uni(L.ppl[0], '#f6f6f2', pick(R, ['#2c2f45', '#3a3a3a', '#5a4a3a'])); L.crossX = V.crossX ? L.bx1 - S.hh * 0.32 : L.bx0 + S.hh * 0.32; L.crossY = S.deck - L.gf - S.hh * 0.32;
    if (L.signAt !== 'stand' && Math.abs(L.crossX - L.signX) < L.sg.w / 2 + S.hh * 0.3) L.crossY = S.deck - L.gf + S.hh * (L.awn === 'none' ? 0.42 : 0.62); },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 111);
    shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.02, d - hh * 0.04, 6, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#f2f2ee', '#e5567f', '#3a6fb0', '#f2c94c', '#4fae8c', '#f08a3a', '#9b6bd6', '#ffffff', '#7fd8ff'], S, R() < 0.3 ? 'bottle' : 'box'); });
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, w = I.x1 - I.x0, px = I.x0 + w * 0.42, u = (t / 6000) % 1, turn = u < 0.35;
    fig(c, L.ppl[0], px, d - hh * 0.02, hh * 0.92, turn ? reach(px, d - hh * 0.02, hh * 0.92, STANDP, -1, [px - hh * 0.25, d - hh * (0.75 + 0.1 * Math.sin(u * 18))], null) : reach(px, d - hh * 0.02, hh * 0.92, STANDP, 1, [px + hh * 0.3, d - hh * 0.5], [px + hh * 0.26, d - hh * 0.48]), turn ? -1 : 1);
    if (!turn) fp(c, [[px + hh * 0.27, d - hh * 0.5], [px + hh * 0.37, d - hh * 0.5], [px + hh * 0.36, d - hh * 0.38], [px + hh * 0.28, d - hh * 0.38]], '#f6f6f2');
    fig(c, L.ppl[1], px + hh * 0.75, d - hh * 0.02, hh * 0.92, talk(t, 3), -1);
  },
  fore: function (q, S, L, V) { var I = L.in, hh = S.hh, d = S.deck, w = I.x1 - I.x0, R = rnd(S.seed + 113), x0 = I.x0 + w * 0.42 + hh * 0.2;
    counter(q, x0, Math.min(I.x1 - hh * 0.05, x0 + hh * 0.5), d - hh * 0.45, S, '#c9ccd4', true); goods(q, x0 + 3, Math.min(I.x1 - hh * 0.05, x0 + hh * 0.5) - 3, d - hh * 0.25, hh * 0.15, R, ['#f2f2ee', '#e5567f', '#3a6fb0', '#4fae8c'], S, 'box');
    for (var i = 0; i < 6; i++) fr(q, x0 + hh * 0.05 + i * hh * 0.06, d - hh * 0.56, hh * 0.03, hh * 0.1, nt(S, pick(R, ['#3a6fb0', '#2f9a5a', '#f2c94c', '#d9342b']), 0.2)); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    paper(q, rect(L.crossX - hh * 0.03, L.crossY - hh * 0.02, hh * 0.06, hh * 0.04), nt(S, '#9aa0a8', 0.3), 1);
    if (V.scale && L.open) { var sd = L.sides[V.crossX ? 1 : 0]; if (sd.b - sd.a > hh * 0.5) { var sx = V.crossX ? sd.a + hh * 0.25 : sd.b - hh * 0.25; paper(q, rect(sx - hh * 0.12, d - hh * 0.62 + hh * 0.12, hh * 0.24, hh * 0.62), nt(S, '#d9342b', 0.3), 1); fe(q, sx, d - hh * 0.36, hh * 0.08, hh * 0.08, nt(S, '#fffaf0', 0.2)); fr(q, sx - hh * 0.14, d + hh * 0.08, hh * 0.28, hh * 0.05, nt(S, '#5a5e66', 0.3)); } }
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, t = S.t, x = L.crossX, y = L.crossY - hh * 0.22, s = hh * 0.36, a = L.open || S.night ? 0.85 + 0.15 * Math.sin(t / 700) : 0.55;
    if (S.night) glow(c, x, y, hh * 0.7, '90,230,140', 0.6 * a);
    var g = L.open || S.night ? 'rgba(40,200,110,' + a.toFixed(2) + ')' : '#2f7a4a';
    fr(c, x - s / 2 - 2, y - s / 2 - 2, s + 4, s + 4, '#f6f6f2'); fr(c, x - s * 0.17, y - s / 2, s * 0.34, s, g); fr(c, x - s / 2, y - s * 0.17, s, s * 0.34, g);
  }
}, 'the cross breathes: a = a₀ + b·sin ωt');

/* ---------------------------------------------------------------- a car seen from the front, for rows of parked cars */
function carFront(q, x, y, s, col, S) {
  var c = nt(S, col, 0.45), gl = S.night ? '#2a3550' : '#8fb4c4', dk = nt(S, '#1e1e22');
  fr(q, x - s * 0.42, y - s * 0.14, s * 0.12, s * 0.14, dk); fr(q, x + s * 0.3, y - s * 0.14, s * 0.12, s * 0.14, dk);
  paper(q, poly([[x - s * 0.48, y - s * 0.09], [x - s * 0.48, y - s * 0.34], [x - s * 0.37, y - s * 0.41], [x + s * 0.37, y - s * 0.41], [x + s * 0.48, y - s * 0.34], [x + s * 0.48, y - s * 0.09]]), c, 1);
  paper(q, poly([[x - s * 0.36, y - s * 0.4], [x - s * 0.28, y - s * 0.64], [x + s * 0.28, y - s * 0.64], [x + s * 0.36, y - s * 0.4]]), c, 1);
  fp(q, [[x - s * 0.31, y - s * 0.43], [x - s * 0.25, y - s * 0.61], [x + s * 0.25, y - s * 0.61], [x + s * 0.31, y - s * 0.43]], gl);
  fe(q, x - s * 0.34, y - s * 0.29, s * 0.07, s * 0.035, S.night ? '#fff2b0' : '#f2f2e8'); fe(q, x + s * 0.34, y - s * 0.29, s * 0.07, s * 0.035, S.night ? '#fff2b0' : '#f2f2e8');
  fr(q, x - s * 0.18, y - s * 0.3, s * 0.36, s * 0.07, mixc(c, '#000000', 0.35)); fr(q, x - s * 0.1, y - s * 0.18, s * 0.2, s * 0.06, nt(S, '#f2f2ee', 0.4));
}
function pSign(q, x, y, s, S) { fr(q, x - 1.5, y, 3, S.deck + S.hh * 0.12 - y, nt(S, '#9aa0a8', 0.4)); paper(q, rect(x - s / 2, y - s, s, s), nt(S, '#1f5fb0', 0.3), 1); q.strokeStyle = '#ffffff'; q.lineWidth = 1.2; q.strokeRect(x - s / 2 + 2, y - s + 2, s - 4, s - 4); txt(q, 'P', x, y - s / 2 + 1, s * 0.75, '#ffffff', 800); }

/* parking: a zinc shelter over a row of motorbikes with the attendant at the table, or an open lot of
   cars nose-out behind its booth and barrier, or a concrete car park of three decks; the barrier
   lifts, θ = (π/2)·(1 − cos πu)/2, as a car rolls in */
addShop('parking', {
  look: function (S, F, R) {
    var k = sub(F, 'motorcycle-parking') || has(F, /มอเตอร์ไซค์|motorcycle|motorbike|จักรยานยนต์/i) ? 'moto' : sub(F, 'bicycle-parking') || has(F, /จักรยาน|bicycle/i) ? 'bike' : has(F, /อาคารจอดรถ|car ?park building|multi|ชั้น/i) || R() < 0.22 ? 'deck' : 'car';
    return { k: k, type: 'custom', custom: lot, w: k === 'deck' ? 4.6 + R() * 1 : 5 + R() * 1.4, lanterns: 0, bikes: 0, noUnit: true, mix: { casual: 0.85, sin: 0.1, mohom: 0.05 } };
  },
  plan: function (S, L, V, R) {
    var hh = S.hh, d = S.deck; L.att = crew(S, 3, V.mix, 21); uni(L.att[0], pick(R, ['#2c3e6b', '#f2c94c', '#f08a3a', '#3a5a3a']), '#2c2f45'); L.animal = R() < 0.5 ? 'dog' : 'none'; L.walkers = Math.min(L.walkers, 1);
    if (V.k === 'moto' || V.k === 'bike') { L.top = d - hh * 1.42; L.signAt = 'face'; L.signY = L.top - L.sg.h - hh * 0.05; L.boothX = R() < 0.5 ? L.bx0 + hh * 0.35 : L.bx1 - hh * 0.35; }
    else if (V.k === 'deck') { L.top = d - hh * 2.26; L.signAt = 'face'; L.signY = L.top + hh * 0.03; L.boothX = L.bx1 - hh * 0.4; }
    else { L.top = d - hh * 1.9; L.boothX = L.bx1 - hh * 0.45; L.signAt = 'stand'; L.signX = clamp(L.bx0 + L.sg.w / 2 + hh * 0.2, S.x0 + L.sg.w / 2 + 4, S.x1 - L.sg.w / 2 - 4); L.signY = d - hh * 1.55 - L.sg.h; }
    L.cols = []; for (var i = 0; i < 14; i++) L.cols.push(V.k === 'moto' || V.k === 'bike' ? pick(R, BIKE) : pick(R, CARS.concat(['#d9342b', '#3a6fb0', '#f2c94c'])));
    L.spirit = L.spirit && !L.spirit.front ? L.spirit : null;
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, bx = L.boothX, u = (t / 11000) % 1;
    if (V.k === 'car' || V.k === 'deck') {   /* the barrier and the car it lets in */
      var cx = lerp(S.x1 + hh * 1.4, bx + hh * 1.2, ease(Math.min(1, u / 0.35))), up = u > 0.4 && u < 0.75 ? ease(Math.min(1, (u - 0.4) * 6, (0.75 - u) * 6)) : 0;
      if (u > 0.5) cx = lerp(bx + hh * 1.2, S.x0 - hh * 1.6, ease((u - 0.5) / 0.5));
      var ang = -up * Math.PI / 2 * 0.95, px = bx - hh * 0.32, py = d - hh * 0.4;
      c.save(); c.translate(px, py); c.rotate(-ang); for (var k = 0; k < 6; k++) fr(c, -hh * (0.2 * (k + 1)), -hh * 0.025, hh * 0.2, hh * 0.05, k % 2 ? '#f2f2f2' : '#d9342b'); c.restore();
      fr(c, px - hh * 0.04, py - hh * 0.04, hh * 0.08, d - py + hh * 0.04, '#5a5e66');
      var spr = sprite(S, 'car' + (S.seed % 5), hh * 2.4, hh * 0.7, function (q) { car(q, hh * 1.2, hh * 0.68, hh * 0.95, S.seed % 2 ? 'sedan' : 'pickup', CARS[S.seed % CARS.length], -1, S); });
      if (spr && u < 0.98) c.drawImage(spr, cx - hh * 1.2, d + hh * 0.2 - hh * 0.68, hh * 2.4, hh * 0.7);
    }
    var ax = bx + (V.k === 'moto' || V.k === 'bike' ? hh * 0.25 : -hh * 0.75), wave = Math.sin(t / 300);
    var me = fig(c, L.att[0], ax, d + hh * 0.16, hh * 0.92, reach(ax, d + hh * 0.16, hh * 0.92, STANDP, -1, [ax - hh * 0.2 - wave * hh * 0.06, d - hh * 0.6 + Math.abs(wave) * hh * 0.08], null), -1);
    if (S.night) { var hd = me.hand[0]; ln(c, [hd, [hd[0] - hh * 0.08, hd[1] - hh * 0.14]], '#ff9a3a', Math.max(2, hh * 0.04)); glow(c, hd[0] - hh * 0.04, hd[1] - hh * 0.07, hh * 0.2, '255,150,60', 0.7); }
    if (S.night) { var lx = (L.bx0 + L.bx1) / 2; glow(c, lx, d - hh * 1.3, hh * 1.2, '255,236,190', 0.25); }
  }
}, 'the barrier: θ = (π/2)·(1 − cos πu)/2');
function lot(q, S, L) {
  var V = L.V, hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, k = V.k, i, x, R = rnd(S.seed + 121);
  if (k === 'moto' || k === 'bike') {
    var top = L.top, zinc = nt(S, pick(R, ['#8a8f99', '#6f8aa8', '#a85a3a', '#5f7f6a']), 0.45);
    for (x = x0 + hh * 0.1; x <= x1 - hh * 0.05; x += Math.max(hh * 1.2, (x1 - x0 - hh * 0.15) / Math.round((x1 - x0) / (hh * 1.4)))) paper(q, rect(x - hh * 0.03, top, hh * 0.06, d - top), nt(S, '#9aa0a8', 0.4), 1);
    for (i = 0, x = x0 + hh * 0.35; x < x1 - hh * 0.35; x += hh * (k === 'bike' ? 0.26 : 0.3), i++) { if (Math.abs(x - L.boothX) < hh * 0.45) continue; if (k === 'bike') bicycle(q, x, d + hh * 0.08, hh * 0.85, L.cols[i % 14], 1, S, i % 3 === 0); else scooter(q, x, d + hh * 0.06, hh * 0.85, L.cols[i % 14], 1, S); }
    paper(q, poly([[x0 - hh * 0.15, top + hh * 0.08], [x0 - hh * 0.1, top - hh * 0.06], [x1 + hh * 0.1, top - hh * 0.06], [x1 + hh * 0.15, top + hh * 0.08]]), zinc, 1.5);
    q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; q.beginPath(); for (x = x0 - hh * 0.1; x < x1 + hh * 0.1; x += hh * 0.06) { q.moveTo(x, top - hh * 0.06); q.lineTo(x, top + hh * 0.08); } q.stroke();
    if (S.night) { fr(q, (x0 + x1) / 2 - hh * 0.3, top + hh * 0.1, hh * 0.6, hh * 0.03, '#f4fbff'); glow(q, (x0 + x1) / 2, top + hh * 0.2, hh * 1.2, '220,240,255', 0.35); }
    fr(q, L.boothX - hh * 0.25, d - hh * 0.4, hh * 0.5, hh * 0.04, nt(S, '#8a6a4a', 0.35)); fr(q, L.boothX - hh * 0.22, d - hh * 0.36, hh * 0.04, hh * 0.36, nt(S, '#8a6a4a', 0.35)); fr(q, L.boothX + hh * 0.18, d - hh * 0.36, hh * 0.04, hh * 0.36, nt(S, '#8a6a4a', 0.35));
    fr(q, L.boothX - hh * 0.1, d - hh * 0.48, hh * 0.2, hh * 0.08, nt(S, '#2f6fb0', 0.3)); fr(q, L.boothX + hh * 0.12, d - hh * 0.46, hh * 0.06, hh * 0.06, nt(S, '#f2f2ee', 0.3));
    pSign(q, L.boothX < (x0 + x1) / 2 ? x1 - hh * 0.25 : x0 + hh * 0.25, d - hh * 0.85, hh * 0.3, S);
    return; }
  if (k === 'deck') {
    var lv = [d - hh * 0.74, d - hh * 1.5], col = nt(S, pick(R, ['#c9c4b8', '#d8d2c4', '#b8b4aa']), 0.45);
    paper(q, rect(x0, L.top, x1 - x0, d - L.top), nt(S, '#5a5a62', 0.4), 1.4);
    for (i = 0; i < 3; i++) { var sy = i === 2 ? L.top : lv[1 - i] - hh * 0.0; }
    [d, lv[0], lv[1]].forEach(function (fy, j) { for (x = x0 + hh * 0.55; x < x1 - hh * 0.4; x += hh * 0.85) { if (j === 0 && Math.abs(x - L.boothX) < hh * 0.6) continue; carFront(q, x, fy - hh * 0.04, hh * 0.85, L.cols[(j * 5 + Math.round(x)) % 14], S); } if (S.night) for (x = x0 + hh * 0.5; x < x1; x += hh * 1.2) glow(q, x, fy - hh * 0.68, hh * 0.4, '255,236,190', 0.35); });
    [lv[0], lv[1], L.top + hh * 0.22].forEach(function (fy) { paper(q, rect(x0 - hh * 0.05, fy - hh * 0.14, x1 - x0 + hh * 0.1, hh * 0.14), col, 1.3); fr(q, x0 - hh * 0.05, fy - hh * 0.06, x1 - x0 + hh * 0.1, 2, 'rgba(0,0,0,.15)'); });
    for (x = x0; x <= x1; x += (x1 - x0) / 4) paper(q, rect(x - hh * 0.05, L.top + hh * 0.2, hh * 0.1, d - L.top - hh * 0.2), col, 1.2);
    pSign(q, x0 + hh * 0.3, d - hh * 0.9, hh * 0.3, S);
    L.boothX = x1 - hh * 0.4; booth(q, L.boothX, S); return; }
  /* an open lot: a low wall and trees behind, cars nose-out, painted bays */
  fr(q, x0, d - hh * 0.5, x1 - x0, hh * 0.5, nt(S, '#d8d2c4', 0.45)); for (x = x0; x < x1; x += hh * 0.5) fr(q, x, d - hh * 0.5, 2, hh * 0.5, 'rgba(0,0,0,.12)');
  for (x = x0 + hh * 0.3; x < x1 - hh * 0.2; x += hh * 0.9) { for (i = 0; i < 9; i++) fe(q, x + (R() - 0.5) * hh * 0.5, d - hh * (0.6 + R() * 0.5), hh * 0.16, hh * 0.13, nt(S, R() < 0.5 ? '#3f7a3a' : '#5a9a4a', 0.45)); }
  for (i = 0, x = x0 + hh * 0.55; x < x1 - hh * 1.0; x += hh * 1.15, i++) { carFront(q, x, d + hh * 0.06, hh * 1.1, L.cols[i % 14], S); fr(q, x + hh * 0.57, d - hh * 0.02, 2, hh * 0.14, nt(S, '#f2f2ee', 0.4)); }
  booth(q, L.boothX, S);
  pSign(q, L.boothX + hh * 0.35, d - hh * 1.05, hh * 0.32, S);
}
function booth(q, x, S) {
  var hh = S.hh, d = S.deck, w = hh * 0.55, h = hh * 1.15;
  paper(q, rect(x - w / 2, d - h, w, h), nt(S, '#f2f2ee', 0.4), 1.3); fr(q, x - w / 2 - hh * 0.05, d - h - hh * 0.05, w + hh * 0.1, hh * 0.06, nt(S, '#2f6fb0', 0.4));
  fr(q, x - w * 0.36, d - h * 0.78, w * 0.72, h * 0.32, S.night ? '#ffe2a0' : nt(S, '#8fb4c4', 0.4)); fe(q, x, d - h * 0.6, hh * 0.06, hh * 0.07, nt(S, '#5a3a2a', 0.3)); fr(q, x - hh * 0.07, d - h * 0.55, hh * 0.14, h * 0.09, nt(S, '#2c3e6b', 0.3));
}

/* mall: inside, the gallery above on its rail, a glass roof, an escalator whose steps climb, y = y₀ + vt,
   shoppers with bags on both floors, a food court steaming; outside, a frontage of glass and panels,
   doors that slide, a line of trolleys at a hypermarket */
addShop('mall', {
  look: function (S, F, R) {
    var hyper = has(F, /lotus|โลตัส|tesco|big ?c|บิ๊กซี|makro|แม็คโคร|ร้านขายของชำ|grocery|supermarket|ซูเปอร์|rimping|ริมปิง|tops|ท็อปส์/i);
    var k = hyper ? 'hyper' : F.inside || R() < 0.55 ? 'inside' : 'front';
    var V = { k: k, type: 'custom', noUnit: true, lanterns: 0, bikes: 0, mix: { casual: 0.82, sin: 0.12, mohom: 0.06 } };
    if (k === 'inside') { V.custom = mallIn; V.mallFloor = true; V.tall = true; V.noSpirit = true; V.noPole = true; V.w = 4.2; }
    else { V.custom = mallFront; V.w = k === 'hyper' ? 6.4 : 5.6 + R() * 0.6; V.at = 0.3 + R() * 0.4; V.clad = pick(R, ['#e8e2d6', '#d8d2c4', '#c9a888', '#f2ead8', '#b8c4c8']); V.band = hyper ? pick(R, ['#d9342b', '#1f8a6a', '#e8a33a', '#2f6fb0']) : pick(R, ['#3a3d44', '#6a3a2a', '#2f5f6b', '#8a6a3a']); }
    return V;
  },
  plan: function (S, L, V, R) {
    var hh = S.hh, d = S.deck;
    L.shop = crew(S, 10, V.mix, 23); L.walkers = S.phone ? 2 : 3; L.animal = 'none'; L.marigold = false;
    if (V.k === 'inside') { L.bx0 = S.x0 + hh * 0.2; L.bx1 = S.x1 - hh * 0.2; L.top = 0; L.signX = clamp((S.x0 + S.x1) / 2, S.x0 + L.sg.w / 2 + 4, S.x1 - L.sg.w / 2 - 4); L.signY = d - hh * 2.12; L.signAt = 'face'; L.plate = -1;
      L.esc = { x0: S.x0 + S.span * (R() < 0.5 ? 0.12 : 0.5), w: Math.min(S.span * 0.38, hh * 2.6) }; L.court = L.esc.x0 > S.x0 + S.span * 0.3 ? S.x0 + hh * 0.9 : S.x1 - hh * 2.1; L.walkers = 0; }
    else { L.top = d - hh * 2.26; L.signAt = 'face'; L.signY = d - L.gf - hh * 0.5 - L.sg.h * 0.5; if (L.signY < L.top + hh * 0.06) L.signY = L.top + hh * 0.06; L.doorX = (L.bx0 + L.bx1) / 2; }
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, i;
    if (V.k === 'inside') {
      var E = L.esc, gy = d - hh * 2.25, n = 6, x0 = E.x0, x1 = E.x0 + E.w;
      for (i = 0; i < n; i++) { var u = (t / 9000 + i / n) % 1, sx = lerp(x0 + hh * 0.3, x1 - hh * 0.2, u), sy = lerp(d - hh * 0.1, gy + hh * 0.05, u); fr(c, sx - hh * 0.06, sy - hh * 0.02, hh * 0.12, 2, 'rgba(60,60,70,.7)'); }
      for (i = 0; i < 2; i++) { var u2 = (t / 9000 + i * 0.5) % 1, rx = lerp(x0 + hh * 0.35, x1 - hh * 0.25, u2), ry = lerp(d - hh * 0.12, gy + hh * 0.03, u2); c.save(); c.globalAlpha = Math.min(1, u2 * 8, (1 - u2) * 8); fig(c, L.shop[i], rx, ry, hh * 0.85, STANDP, 1); c.restore(); }
      for (i = 0; i < 3; i++) { var v = hh * (0.35 + i * 0.1), span = S.span + hh * 2, dir = i % 2 ? -1 : 1, uu = (t / 1000 * v + i * span * 0.33) % span, px = dir > 0 ? S.x0 - hh + uu : S.x1 + hh - uu;
        var me = fig(c, L.shop[3 + i], px, d + hh * 0.1 + (i % 2) * hh * 0.06, hh * 0.93, K.walkP(t / 1000 * TAU * 0.8 + i * 2, false), dir); var hd = me.hand[1]; fp(c, [[hd[0] - hh * 0.06, hd[1]], [hd[0] + hh * 0.06, hd[1]], [hd[0] + hh * 0.07, hd[1] + hh * 0.14], [hd[0] - hh * 0.07, hd[1] + hh * 0.14]], CLOTHS[(i * 3 + S.seed) % CLOTHS.length]); }
      for (i = 0; i < 2; i++) { var v2 = hh * 0.3, sp2 = S.span + hh, uu2 = (t / 1000 * v2 + i * sp2 * 0.5) % sp2, gx = i ? S.x1 + hh * 0.5 - uu2 : S.x0 - hh * 0.5 + uu2; fig(c, L.shop[7 + i], gx, gy - hh * 0.06, hh * 0.6, K.walkP(t / 1000 * TAU * 0.8 + i, false), i ? -1 : 1); }
      fr(c, S.x0, gy - hh * 0.32, S.span, hh * 0.28, 'rgba(190,225,235,.22)');
      steam(c, L.court + hh * 0.55, d - hh * 0.9, hh, t, 2, 4, hh * 0.3);
      for (i = 0; i < 4; i++) khom(c, S.x0 + S.span * (0.2 + i * 0.2), d - hh * 2.65, hh, ['#d9342b', '#f2c94c', '#f08a3a', '#e5567f'][i], t, i, S.night);
      return; }
    var o = (t / 7000) % 1, op = o > 0.2 && o < 0.6 ? Math.min(1, (o - 0.2) * 10, (0.6 - o) * 10) : 0, dx = L.doorX, pw = hh * 0.3, y0 = d - L.gf + hh * 0.35;
    c.fillStyle = 'rgba(190,225,235,.35)'; c.fillRect(dx - pw - op * pw * 0.9, y0, pw, d - y0); c.fillRect(dx + op * pw * 0.9, y0, pw, d - y0);
    c.strokeStyle = 'rgba(160,165,170,.9)'; c.lineWidth = 2; c.strokeRect(dx - pw - op * pw * 0.9, y0, pw, d - y0); c.strokeRect(dx + op * pw * 0.9, y0, pw, d - y0);
    for (i = 0; i < 3; i++) { var lx = L.bx0 + (L.bx1 - L.bx0) * (0.2 + i * 0.3); khom(c, lx, d - L.gf + hh * 0.12, hh * 1.1, ['#d9342b', '#f2c94c', '#f08a3a'][i], t, i, S.night); }
  }
}, 'the escalator: y = y₀ + vt, wrapping at the top');
function mallIn(q, S, L) {
  var hh = S.hh, d = S.deck, gy = d - hh * 2.25, E = L.esc, R = rnd(S.seed + 131), x0 = E.x0, x1 = E.x0 + E.w;
  paper(q, poly([[x0, d], [x0 + hh * 0.3, d], [x1, gy + hh * 0.08], [x1 - hh * 0.3, gy + hh * 0.08]]), nt(S, '#9aa0a8', 0.3), 1.4);
  q.fillStyle = 'rgba(190,225,235,.35)'; q.beginPath(); q.moveTo(x0, d - hh * 0.05); q.lineTo(x1 - hh * 0.3, gy + hh * 0.03); q.lineTo(x1 - hh * 0.3, gy - hh * 0.3); q.lineTo(x0, d - hh * 0.38); q.fill();
  ln(q, [[x0, d - hh * 0.38], [x1 - hh * 0.3, gy - hh * 0.3]], nt(S, '#2a2a2e', 0.2), Math.max(2, hh * 0.035));
  for (var i = 0; i < 5; i++) { var bx = S.x0 + S.span * (0.08 + i * 0.21); if (bx > x0 - hh * 0.3 && bx < x1 + hh * 0.3) continue; paper(q, rect(bx - hh * 0.1, gy + hh * 0.08, hh * 0.2, hh * 0.6), nt(S, pick(R, ['#d9342b', '#2f6fb0', '#e8a33a', '#1f8a6a', '#9b6bd6']), 0.3), 1); fr(q, bx - hh * 0.08, gy + hh * 0.12, hh * 0.16, hh * 0.52, 'rgba(255,255,255,.15)'); fr(q, bx - hh * 0.1, gy + hh * 0.66, hh * 0.2, hh * 0.03, '#e8b84a'); }
  /* the food court */
  var fx = L.court; paper(q, rect(fx, d - hh * 1.05, hh * 1.2, hh * 1.05), nt(S, '#f2ead8', 0.3), 1.2); fr(q, fx, d - hh * 1.05, hh * 1.2, hh * 0.22, nt(S, '#d9342b', 0.3));
  for (i = 0; i < 3; i++) { fr(q, fx + hh * (0.08 + i * 0.38), d - hh * 0.8, hh * 0.32, hh * 0.22, '#fffaf0'); fe(q, fx + hh * (0.24 + i * 0.38), d - hh * 0.66, hh * 0.1, hh * 0.05, ['#f08a3a', '#e8c86a', '#c0392b'][i]); }
  paper(q, rect(fx, d - hh * 0.45, hh * 1.2, hh * 0.45), nt(S, '#8a6a4a', 0.3), 1);
  for (i = 0; i < 2; i++) { var tx = fx + (fx > S.x0 + S.span / 2 ? -hh * (0.5 + i * 0.7) : hh * (1.6 + i * 0.7)); fe(q, tx, d - hh * 0.38, hh * 0.22, hh * 0.04, nt(S, '#f2f2ee', 0.3)); fr(q, tx - 1.5, d - hh * 0.36, 3, hh * 0.36, nt(S, '#5a5e66', 0.3)); [-1, 1].forEach(function (sd) { fe(q, tx + sd * hh * 0.3, d - hh * 0.22, hh * 0.07, hh * 0.025, nt(S, '#d9342b', 0.3)); fr(q, tx + sd * hh * 0.3 - 1, d - hh * 0.2, 2, hh * 0.2, nt(S, '#5a5e66', 0.3)); }); }
}
function mallFront(q, S, L) {
  var V = L.V, hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, R = rnd(S.seed + 133), clad = nt(S, V.clad, 0.45), top = L.top, gtop = d - L.gf;
  paper(q, rect(x0, top, x1 - x0, gtop - top), clad, 1.7);
  if (V.k === 'hyper') { fr(q, x0, top + hh * 0.1, x1 - x0, hh * 0.18, nt(S, V.band, 0.35)); for (var i = 0; i < 6; i++) fr(q, x0 + (i + 0.3) * (x1 - x0) / 6, top + hh * 0.36, (x1 - x0) / 9, hh * 0.3, nt(S, ['#f2c94c', '#d9342b', '#7fe0a4', '#7fd8ff', '#f08a3a', '#ff9ac0'][i], 0.4)); }
  else { for (var x = x0 + hh * 0.15; x < x1 - hh * 0.1; x += hh * 0.22) fr(q, x, top + hh * 0.08, hh * 0.08, gtop - top - hh * 0.16, mixc(clad, '#000000', 0.08));
    var lw = Math.min(hh * 1.4, (x1 - x0) * 0.25); fr(q, x1 - lw - hh * 0.15, top + hh * 0.12, lw, gtop - top - hh * 0.3, S.night ? '#2a1a4a' : '#1a2230'); for (i = 0; i < 4; i++) fr(q, x1 - lw - hh * 0.1 + i * lw * 0.24, top + hh * (0.2 + (i % 2) * 0.1), lw * 0.2, hh * 0.3, ['#ff5a8c', '#f2c94c', '#7fd8ff', '#7fe0a4'][i]);
    laiKham(q, x0 + hh * 0.1, x1 - hh * 0.1, gtop - hh * 0.14, hh * 0.1, nt(S, '#d9a53c', 0.35), nt(S, V.band, 0.35)); }
  fr(q, x0 + hh * 0.06, gtop, x1 - x0 - hh * 0.12, L.gf, L.open ? (S.night ? 'rgba(255,236,190,.85)' : 'rgba(200,225,232,.95)') : nt(S, '#2a3040', 0.3));
  if (L.open) for (x = x0 + hh * 0.2; x < x1 - hh * 0.2; x += hh * 0.5) { fr(q, x, d - hh * 0.5, hh * 0.3, hh * 0.45, nt(S, pick(R, CLOTHS), 0.3)); fr(q, x + hh * 0.04, d - hh * 0.95, hh * 0.22, hh * 0.3, nt(S, pick(R, CLOTHS), 0.3)); }
  for (x = x0 + hh * 0.06; x <= x1 - hh * 0.05; x += hh * 0.45) fr(q, x - 1, gtop, 2.5, L.gf, nt(S, '#9aa0a8', 0.3));
  var cx = L.doorX; paper(q, poly([[cx - hh * 0.9, gtop + hh * 0.25], [cx + hh * 0.9, gtop + hh * 0.25], [cx + hh * 1.05, gtop + hh * 0.4], [cx - hh * 1.05, gtop + hh * 0.4]]), nt(S, V.band, 0.35), 1.4);
  if (V.k === 'hyper') for (i = 0; i < 5; i++) { var tx = x0 + hh * 0.3 + i * hh * 0.12; ln(q, [[tx, d + hh * 0.12], [tx + hh * 0.05, d - hh * 0.25], [tx + hh * 0.35, d - hh * 0.25], [tx + hh * 0.3, d + hh * 0.05]], nt(S, '#9aa0a8', 0.3), 1.5); }
  else car(q, x1 + hh * 0.2 < S.x1 - hh * 1.2 ? x1 + hh * 0.9 : x0 - hh * 0.9, d + hh * 0.2, hh * 0.9, 'songthaew', S.place && S.place.province === 'cr' ? '#2f6fb0' : '#c0392b', -1, S);
}

/* rental: scooters lined on the pavement in every colour, helmets on a rack, the curvy road on the
   wall; a visitor signing at the table while a rider rolls off, x = x₀ + vt; bicycles, big bikes or cars
   by the kind of shop */
addShop('rental', {
  look: function (S, F, R) {
    var k = sub(F, 'bicycle') || has(F, /จักรยาน(?!ยนต์)|bicycle|cycling|bike tour/i) ? 'bicycle' : has(F, /harley|royal enfield|triumph|ducati|kawasaki|bmw motorrad|big ?bike|บิ๊กไบค์|chopper/i) ? 'big'
      : has(F, /budget|hertz|avis|sixt|thai rent|car rent|รถเช่า|รถยนต์|rent a car|รถตู้|\bvan\b/i) ? 'car' : sub(F, 'motorbike') ? 'moto' : sub(F, 'rental') ? pick(R, ['moto', 'car', 'moto']) : 'moto';
    return { k: k, types: k === 'car' ? { glass: 2, shop: 2, row: 1 } : { shop: 3, row: 2.5, stall: 1, teak: 0.6 }, bikes: 0, light: 'warm', w: 3.8 + R() * 1.2, at: 0.15 + R() * 0.3, mix: { casual: 0.9, sin: 0.1 } };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 4, V.mix, 25); L.ppl[1].hairCol = pick(R, ['#d9b36a', '#8a5a2a', '#c9853a']); L.ppl[1].skin = pick(R, ['#f1c9a5', '#e3b08a']); L.cols = []; for (var i = 0; i < 12; i++) L.cols.push(pick(R, BIKE)); L.deskX = L.bx1 + S.hh * 0.55 < S.x1 - S.hh * 1.2 ? L.bx1 + S.hh * 0.5 : L.bx0 - S.hh * 0.5; if (L.spirit && Math.abs(L.spirit.x - L.deskX) < S.hh * 0.9) L.spirit = null; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 141), w = I.x1 - I.x0;
    shelves(q, I.x0 + hh * 0.06, I.x0 + Math.min(hh * 1.2, w * 0.45), I.y0 + hh * 0.1, d - hh * 0.3, 2, S, function (p, a, b, yb, h) { for (var x = a + hh * 0.1; x < b - hh * 0.05; x += hh * 0.2) { var cc = nt(S, pick(R, ['#f2f2ee', '#2a2a2a', '#d9342b', '#3a6fb0', '#e8b84a']), 0.25); p.fillStyle = cc; p.beginPath(); p.arc(x, yb - 2, hh * 0.09, Math.PI, TAU); p.fill(); fr(p, x - hh * 0.09, yb - 3, hh * 0.18, 2, '#2a2a2a'); } });
    poster(q, I.x1 - hh * 0.85, I.y0 + hh * 0.08, hh * 0.7, hh * 0.45, S, function (p, x, y, ww, h) { fr(p, x, y, ww, h, '#e8f0d8'); p.strokeStyle = '#d9342b'; p.lineWidth = 2; p.beginPath(); for (var j = 0; j <= 40; j++) { var u = j / 40; p.lineTo(x + ww * (0.1 + 0.8 * u), y + h * (0.5 + 0.3 * Math.sin(u * 22) * Math.sin(u * 3))); } p.stroke(); fe(p, x + ww * 0.1, y + h * 0.5, 2.5, 2.5, '#2a2a2a'); fe(p, x + ww * 0.9, y + h * 0.5, 2.5, 2.5, '#2a2a2a'); for (j = 0; j < 4; j++) fp(p, [[x + ww * (0.15 + j * 0.2), y + h * 0.2], [x + ww * (0.25 + j * 0.2), y + h * 0.05], [x + ww * (0.35 + j * 0.2), y + h * 0.2]], '#7aa06a'); });
    fr(q, I.x1 - hh * 0.6, d - hh * 0.65, hh * 0.35, hh * 0.25, nt(S, '#8a6a4a', 0.25)); for (var i = 0; i < 8; i++) fe(q, I.x1 - hh * 0.56 + (i % 4) * hh * 0.08, d - hh * (0.6 - Math.floor(i / 4) * 0.1), hh * 0.015, hh * 0.025, '#d9b84a');
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, R = rnd(S.seed + 143), k = V.k, x, i;
    if (k === 'car') { car(q, L.bx0 + hh * 1.1, d + hh * 0.2, hh * 0.95, 'sedan', L.cols[0] === '#2a2a2a' ? '#f2f2f2' : pick(R, CARS), 1, S); if (L.bx1 - L.bx0 > hh * 4.4) car(q, L.bx1 - hh * 1.2, d + hh * 0.22, hh * 0.95, 'van', '#f2f2f2', -1, S); }
    else if (L.open) for (i = 0, x = L.bx0 + hh * 0.35; x < L.bx1 - hh * 0.2; x += hh * (k === 'big' ? 0.55 : k === 'bicycle' ? 0.3 : 0.36), i++) {
      if (k === 'bicycle') bicycle(q, x, d + hh * 0.16, hh * 0.85, L.cols[i % 12], 1, S, i % 2 === 0);
      else if (k === 'big') { scooter(q, x, d + hh * 0.17, hh * 1.05, ['#2a2a2a', '#8a1f2a', '#3a4a3a', '#5a5e66'][i % 4], 1, S); fe(q, x - hh * 0.05, d - hh * 0.12, hh * 0.18, hh * 0.08, nt(S, '#c9ccd4', 0.4)); }
      else scooter(q, x, d + hh * 0.17, hh * 0.88, L.cols[i % 12], 1, S); }
    /* the table and the board with a scooter drawn on it */
    var hx = L.deskX < L.bx0 ? L.bx1 - hh * 0.2 : L.bx0 + hh * 0.2;
    var bx = L.deskX, dir = bx > L.bx1 ? 1 : -1;
    paper(q, rect(bx - hh * 0.25, d - hh * 0.4 + hh * 0.12, hh * 0.5, hh * 0.04), nt(S, '#8a6a4a', 0.35), 1); fr(q, bx - hh * 0.22, d - hh * 0.24, hh * 0.04, hh * 0.36, nt(S, '#8a6a4a', 0.35)); fr(q, bx + hh * 0.18, d - hh * 0.24, hh * 0.04, hh * 0.36, nt(S, '#8a6a4a', 0.35));
    fr(q, bx - hh * 0.1, d - hh * 0.3, hh * 0.16, hh * 0.03, '#f6f6f2');
    var sx = bx + dir * hh * 0.75; if (sx > S.x0 + hh * 0.9 && sx < S.x1 - hh * 0.9) { paper(q, rect(sx - hh * 0.3, d - hh * 0.95, hh * 0.6, hh * 0.5), nt(S, '#f6efe0', 0.35), 1); fr(q, sx - 1, d - hh * 0.45, 2, hh * 0.57, nt(S, '#5a3a22', 0.35));
      scooter(q, sx, d - hh * 0.6, hh * 0.38, '#d9342b', 1, S); fe(q, sx - hh * 0.12, d - hh * 0.84, hh * 0.05, hh * 0.04, '#f2f2ee'); }
    void hx;
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, bx = L.deskX, dir = bx > L.bx1 ? 1 : -1;
    if (!L.open) return;
    var pen = Math.sin(t / 120) * hh * 0.015;
    fig(c, L.ppl[1], bx + dir * hh * 0.42, d + hh * 0.16, hh * 0.95, reach(bx + dir * hh * 0.42, d + hh * 0.16, hh * 0.95, { lean: 0.3, legs: [0.1, 0, -0.1, 0], arms: [1, 0.5, 1, 0.5] }, -dir, [bx + pen, d - hh * 0.28], [bx + dir * hh * 0.06, d - hh * 0.27]), -dir);
    var me = fig(c, L.ppl[0], bx - dir * hh * 0.45, d + hh * 0.16, hh * 0.92, talk(t, 1), dir);
    var bp = L.ppl[1]; fr(c, bx + dir * hh * 0.42 + (dir > 0 ? hh * 0.02 : -hh * 0.14), d - hh * 0.62, hh * 0.12, hh * 0.22, '#3a6a4a');
    if (V.k === 'car') return;
    var u = (t / 12000) % 1; if (u < 0.55) { var p = u / 0.55, rx = lerp(L.bx0 + (L.bx1 - L.bx0) * 0.5, S.x1 + hh * 1.5, ease(p)), col = L.cols[5];
      var spr = sprite(S, 'ride' + col + V.k, hh * 1.3, hh * 0.85, function (q) { if (V.k === 'bicycle') bicycle(q, hh * 0.65, hh * 0.84, hh * 0.85, col, 1, S, true); else scooter(q, hh * 0.65, hh * 0.84, hh * 0.88, col, 1, S); });
      if (spr) c.drawImage(spr, rx - hh * 0.65, d + hh * 0.2 - hh * 0.84, hh * 1.3, hh * 0.85);
      fig(c, L.ppl[2], rx - hh * 0.08, d + hh * 0.2 - hh * 0.2, hh * 0.92, { lean: 0.1, seat: 0.3, legs: [1.3, -1.0, 1.2, -1.1], arms: [1.2, 0.2, 1.1, 0.3] }, 1);
      fe(c, rx - hh * 0.02, d + hh * 0.2 - hh * 0.2 - hh * 0.86, hh * 0.1, hh * 0.08, '#f2f2ee'); }
  }
}, 'the rider: x = x₀ + vt');

/* ---------------------------------------------------------------- the crafts' wares */
function umbrella(q, x, y, r, col, S, rot) {
  var c = nt(S, col, 0.3); q.save(); q.translate(x, y); q.rotate(rot || 0);
  q.fillStyle = c; q.beginPath(); for (var i = 0; i <= 16; i++) { var a = i / 16 * TAU, rr = i % 2 ? r : r * 0.96; q.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); } q.fill();
  q.strokeStyle = 'rgba(80,40,20,.45)'; q.lineWidth = 0.8; q.beginPath(); for (i = 0; i < 16; i++) { var b = i / 16 * TAU; q.moveTo(0, 0); q.lineTo(Math.cos(b) * r, Math.sin(b) * r); } q.stroke();
  q.fillStyle = 'rgba(255,255,255,.55)'; for (i = 0; i < 3; i++) { var a2 = i * 2.1 + 0.4; for (var p = 0; p < 5; p++) { q.beginPath(); q.ellipse(Math.cos(a2) * r * 0.55 + Math.cos(p * 1.257) * r * 0.1, Math.sin(a2) * r * 0.55 + Math.sin(p * 1.257) * r * 0.1, r * 0.08, r * 0.04, p * 1.257, 0, TAU); q.fill(); } }
  fe(q, 0, 0, r * 0.08, r * 0.08, '#5a3a22'); q.restore();
}
function elephant(q, x, y, s, col, S, dir) {
  var c = nt(S, col, 0.35), X = function (u) { return x + dir * u * s; };
  fe(q, X(0), y - s * 0.55, s * 0.42, s * 0.3, c); [-0.28, -0.12, 0.14, 0.3].forEach(function (u) { fr(q, X(u) - s * 0.06, y - s * 0.4, s * 0.12, s * 0.4, c); });
  fe(q, X(0.42), y - s * 0.7, s * 0.2, s * 0.2, c); fe(q, X(0.32), y - s * 0.66, s * 0.14, s * 0.2, mixc(c, '#000000', 0.12));
  q.strokeStyle = c; q.lineWidth = s * 0.1; q.lineCap = 'round'; q.beginPath(); q.moveTo(X(0.55), y - s * 0.62); q.quadraticCurveTo(X(0.66), y - s * 0.3, X(0.6), y - s * 0.12); q.stroke();
  fe(q, X(0.47), y - s * 0.74, s * 0.02, s * 0.02, '#1a1a1a');
}
function skein(q, x, y, s, col, S) { var c = nt(S, col, 0.3); q.strokeStyle = c; q.lineWidth = Math.max(2, s * 0.05); q.beginPath(); q.ellipse(x, y + s * 0.2, s * 0.05, s * 0.2, 0, 0, TAU); q.stroke(); fr(q, x - s * 0.05, y + s * 0.34, s * 0.1, s * 0.03, mixc(c, '#000000', 0.2)); }
function phaSin(q, x, y, w, h, S, R) { var base = nt(S, pick(R, ['#7a1f3a', '#2a3a6a', '#5a2a6a', '#1f5a4a', '#8a3a1a', '#3a2a4a']), 0.3); fr(q, x, y, w, h, base); for (var i = 0; i < 4; i++) fr(q, x, y + h * (0.15 + i * 0.14), w, h * 0.03, nt(S, pick(R, CLOTHS), 0.3)); fr(q, x, y + h * 0.78, w, h * 0.22, nt(S, '#e8b84a', 0.3)); q.strokeStyle = nt(S, '#7a1f1a', 0.3); q.lineWidth = 1; q.beginPath(); for (var zx = x, zi = 0; zx <= x + w; zx += h * 0.06, zi++) q.lineTo(zx, y + h * (zi % 2 ? 0.8 : 0.96)); q.stroke(); }
function bowl(q, x, y, s, col, S, emb) { var c = nt(S, col, 0.3); fp(q, [[x - s * 0.14, y - s * 0.14], [x + s * 0.14, y - s * 0.14], [x + s * 0.1, y - s * 0.02], [x + s * 0.06, y], [x - s * 0.06, y], [x - s * 0.1, y - s * 0.02]], c); fe(q, x, y - s * 0.14, s * 0.14, s * 0.025, mixc(c, '#ffffff', 0.25)); if (emb) for (var i = 0; i < 5; i++) fe(q, x - s * 0.09 + i * s * 0.045, y - s * 0.08, s * 0.012, s * 0.012, 'rgba(255,255,255,.7)'); }

/* crafts: a loom with its weaver (the shuttle flies, x = A·sin ωt; the heddles lift in turn; the cloth
   grows a row at a time), skeins of dyed silk and folded pha sin; Wualai silver hammered with a glint;
   red and gold of a gold shop; lacquer bowls and the brush; carved elephants and flying chips; Bo Sang
   umbrellas, one turning as it is painted; celadon on the wheel; baskets and hats */
addShop('crafts', {
  look: function (S, F, R) {
    var k = has(F, /ทอผ้า|ผ้าทอ|กี่ทอ|ผ้าไหม|weav|(^|[^a-z])looms?\b|\bsilk|textile/i) ? 'weave' : has(F, /ห้างทอง|ร้านทอง|\bทอง\b|gold/i) ? 'gold' : has(F, /เครื่องเงิน|silver|เงิน|jewel|อัญมณี|gem|pandora|diamond/i) ? 'silver'
      : has(F, /เขิน|lacquer/i) ? 'lacquer' : has(F, /ร่ม|umbrella|บ่อสร้าง|bo ?sang|sa paper|กระดาษสา/i) ? 'umbrella' : has(F, /แกะสลัก|ไม้|wood|carv|teak|furniture/i) ? 'wood'
      : has(F, /celadon|เซลาดอน|ceramic|เซรามิค|pottery|ปั้น|เครื่องปั้น/i) ? 'ceramic' : has(F, /จักสาน|basket|bamboo|ไม้ไผ่|rattan|หวาย/i) ? 'basket' : has(F, /หนัง|leather|bag|กระเป๋า/i) ? 'leather'
      : pick(R, ['umbrella', 'wood', 'weave', 'lacquer', 'silver', 'ceramic', 'basket']);
    var V = { k: k, light: 'warm', mix: { casual: 0.45, sin: 0.35, mohom: 0.2 }, table: R() < 0.75 }; if (V.table) V.bikes = 0;
    if (k === 'basket') V.types = { lanna: 2, teak: 2, shop: 2, row: 1 };
    else V.types = k === 'weave' ? { teak: 3, lanna: 2, stall: 2 } : k === 'gold' ? { shop: 3, glass: 1 } : k === 'silver' || k === 'leather' ? { shop: 3, lanna: 1.5, glass: 1, teak: 1 } : { lanna: 3, teak: 2, stall: 2, shop: 1.5 };
    if (k === 'gold') { V.inWall = '#c0392b'; V.board = '#8a1f1a'; V.lanterns = 2; }
    return V;
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 27); L.work = L.in.x0 + (L.in.x1 - L.in.x0) * (0.35 + R() * 0.25); L.cloth = []; for (var i = 0; i < 40; i++) L.cloth.push(pick(R, CLOTHS)); L.umb = [pick(R, ['#d9342b', '#f2c94c', '#2f9a5a', '#3a6fb0', '#e5567f', '#f08a3a']), pick(R, ['#f2e6c9', '#d9342b', '#9b6bd6'])]; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 151), w = I.x1 - I.x0, k = V.k, x, i;
    if (k === 'weave') { fr(q, I.x0 + hh * 0.05, I.y0 + hh * 0.06, w - hh * 0.1, 2.5, nt(S, '#6a4a2a', 0.2)); for (x = I.x0 + hh * 0.15; x < I.x1 - hh * 0.1; x += hh * 0.12) skein(q, x, I.y0 + hh * 0.06, hh, pick(R, CLOTHS.concat(['#c9a83a', '#7a1f3a', '#2a3a6a'])), S);
      shelves(q, I.x1 - Math.min(hh * 0.9, w * 0.35), I.x1 - hh * 0.05, d - hh * 0.62, d - hh * 0.02, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.2; xx += hh * 0.22) for (var j = 0; j < 2; j++) phaSin(p, xx, yb - (j + 1) * h * 0.45, hh * 0.2, h * 0.42, S, R); }); }
    else if (k === 'gold') { for (x = I.x0 + hh * 0.15; x < I.x1 - hh * 0.1; x += hh * 0.16) { q.strokeStyle = nt(S, '#f2c94c', 0.1); q.lineWidth = 1.5; q.beginPath(); q.moveTo(x - hh * 0.05, I.y0 + hh * 0.1); q.quadraticCurveTo(x, I.y0 + hh * (0.4 + (x * 13 % 3) * 0.05), x + hh * 0.05, I.y0 + hh * 0.1); q.stroke(); } }
    else if (k === 'silver' || k === 'lacquer' || k === 'ceramic') { fr(q, I.x0 + hh * 0.04, I.y0 + hh * 0.02, w - hh * 0.08, d - hh * 0.5 - I.y0, nt(S, k === 'silver' ? '#2a2f5a' : k === 'lacquer' ? '#e8d8b0' : '#5a3a2a', 0.2)); var pal = k === 'silver' ? ['#dfe2ea', '#c9ccd4', '#eef0f4'] : k === 'lacquer' ? ['#9a1f1a', '#1a1a1a', '#b8321a'] : ['#8fc0a0', '#a8d0b0', '#6fa88a', '#f2ead8'];
      shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.06, d - hh * 0.5, 2, S, function (p, a, b, yb, h) { for (var xx = a + hh * 0.15; xx < b - hh * 0.1; xx += hh * 0.3) { if (k === 'ceramic' && R() < 0.5) { var cc = nt(S, pick(R, pal), 0.3); fp(p, [[xx - hh * 0.05, yb], [xx + hh * 0.05, yb], [xx + hh * 0.08, yb - h * 0.4], [xx + hh * 0.03, yb - h * 0.75], [xx - hh * 0.03, yb - h * 0.75], [xx - hh * 0.08, yb - h * 0.4]], cc); } else bowl(p, xx, yb, hh * 1.4, pick(R, pal), S, k === 'silver'); if (k === 'lacquer') { p.strokeStyle = '#e8b84a'; p.lineWidth = 1; p.beginPath(); p.moveTo(xx - hh * 0.12, yb - h * 0.25); p.lineTo(xx + hh * 0.12, yb - h * 0.25); p.stroke(); } } }); }
    else if (k === 'umbrella') { for (i = 0; i < Math.floor(w / (hh * 0.5)); i++) umbrella(q, I.x0 + hh * 0.3 + i * hh * 0.5, I.y0 + hh * 0.28, hh * 0.22, pick(R, ['#d9342b', '#f2c94c', '#2f9a5a', '#3a6fb0', '#e5567f', '#f08a3a', '#9b6bd6', '#f2e6c9']), S, R()); }
    else if (k === 'wood') { for (i = 0; i < Math.floor(w / (hh * 0.7)); i++) { var px = I.x0 + hh * 0.1 + i * hh * 0.7; fr(q, px, I.y0 + hh * 0.06, hh * 0.6, hh * 0.45, nt(S, '#8a5a32', 0.2)); for (var j = 0; j < 3; j++) { q.strokeStyle = nt(S, '#5a3520', 0.2); q.lineWidth = 1.5; q.beginPath(); q.arc(px + hh * 0.3, I.y0 + hh * 0.28, hh * (0.06 + j * 0.06), j, j + 4); q.stroke(); } } }
    else if (k === 'basket') { for (x = I.x0 + hh * 0.2; x < I.x1 - hh * 0.1; x += hh * 0.3) { var bc = nt(S, '#c9a66b', 0.3); fp(q, [[x - hh * 0.1, I.y0 + hh * 0.2], [x + hh * 0.1, I.y0 + hh * 0.2], [x + hh * 0.07, I.y0 + hh * 0.42], [x - hh * 0.07, I.y0 + hh * 0.42]], bc); q.strokeStyle = 'rgba(90,60,30,.5)'; q.lineWidth = 1; q.beginPath(); for (var yy = I.y0 + hh * 0.24; yy < I.y0 + hh * 0.42; yy += hh * 0.04) { q.moveTo(x - hh * 0.09, yy); q.lineTo(x + hh * 0.09, yy); } q.stroke(); fe(q, x, I.y0 + hh * 0.2, hh * 0.1, hh * 0.03, mixc(bc, '#000000', 0.15)); }
      for (x = I.x0 + hh * 0.25; x < I.x1 - hh * 0.2; x += hh * 0.45) fp(q, [[x - hh * 0.2, d - hh * 0.55], [x, d - hh * 0.72], [x + hh * 0.2, d - hh * 0.55]], nt(S, '#d8b878', 0.3)); }
    else { for (x = I.x0 + hh * 0.2; x < I.x1 - hh * 0.1; x += hh * 0.3) { var lc = nt(S, pick(R, ['#8a5a32', '#5a3520', '#b8743a', '#2a2a2a', '#7a1f1a']), 0.3); fr(q, x - hh * 0.1, I.y0 + hh * 0.25, hh * 0.2, hh * 0.18, lc); ln(q, [[x - hh * 0.06, I.y0 + hh * 0.25], [x, I.y0 + hh * 0.12], [x + hh * 0.06, I.y0 + hh * 0.25]], lc, 1.5); } }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, k = V.k, x = L.work, i;
    if (k === 'weave') {   /* a frame loom seen from the front: warp, cloth growing, the shuttle, the heddles */
      var lw = hh * 1.1, lx0 = x - lw / 2, ly1 = d - hh * 0.12, ly0 = d - hh * 1.05, wood = '#6b4226';
      fr(c, lx0 - hh * 0.05, ly0, hh * 0.06, ly1 - ly0 + hh * 0.12, wood); fr(c, lx0 + lw - hh * 0.01, ly0, hh * 0.06, ly1 - ly0 + hh * 0.12, wood);
      var u = (t / 24000) % 1, rows = Math.floor(u * 40), fell = ly1 - hh * 0.04 - rows * hh * 0.012;
      for (i = 0; i < rows; i++) fr(c, lx0, ly1 - hh * 0.04 - (i + 1) * hh * 0.012, lw, hh * 0.012 + 0.5, L.cloth[i]);
      c.strokeStyle = 'rgba(240,230,210,.8)'; c.lineWidth = 0.7; c.beginPath(); for (var wx = lx0 + 2; wx < lx0 + lw; wx += 3) { c.moveTo(wx, ly0 + hh * 0.2); c.lineTo(wx, fell); } c.stroke();
      var hd = Math.sin(t / 700) * hh * 0.04; fr(c, lx0, ly0 + hh * 0.3 + hd, lw, hh * 0.03, wood); fr(c, lx0, ly0 + hh * 0.38 - hd, lw, hh * 0.03, '#8a5a32');
      fr(c, lx0 - hh * 0.03, fell - hh * 0.05 - Math.abs(Math.sin(t / 700)) * hh * 0.05, lw + hh * 0.06, hh * 0.035, wood);
      var sx = x + Math.sin(t / 700) * lw * 0.42; fe(c, sx, fell - hh * 0.025, hh * 0.08, hh * 0.022, '#c9853a'); fe(c, sx, fell - hh * 0.025, hh * 0.03, hh * 0.012, L.cloth[rows % 40]);
      fr(c, lx0 - hh * 0.05, ly0, lw + hh * 0.16, hh * 0.05, wood); fr(c, lx0 - hh * 0.05, ly1, lw + hh * 0.16, hh * 0.05, wood);
      fig(c, L.ppl[0], lx0 + lw + hh * 0.38, d - hh * 0.02, hh * 0.88, reach(lx0 + lw + hh * 0.38, d - hh * 0.02, hh * 0.88, SITP, -1, [sx + hh * 0.05, fell - hh * 0.03], [lx0 + lw - hh * 0.05, fell - hh * 0.06]), -1);
      return; }
    var P = { lean: 0.3, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [1, 0.5, 1, 0.5] }, tap = Math.pow(Math.abs(Math.sin(t / 260)), 3), wx2 = x + hh * 0.3, wy = d - hh * 0.45;
    if (k === 'gold') { fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.9, talk(t, 1), 1); fig(c, L.ppl[1], x + hh * 0.7, d - hh * 0.02, hh * 0.92, reach(x + hh * 0.7, d - hh * 0.02, hh * 0.92, STANDP, -1, [x + hh * 0.45, d - hh * 0.5], null), -1); return; }
    if (k === 'silver') { fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.88, reach(x, d - hh * 0.02, hh * 0.88, P, 1, [wx2 - hh * 0.02, wy - hh * (0.06 + 0.16 * (1 - tap))], [wx2 + hh * 0.06, wy - hh * 0.04]), 1);
      fr(c, wx2 - hh * 0.04, wy - hh * (0.1 + 0.16 * (1 - tap)), hh * 0.08, hh * 0.04, '#5a5e66'); bowl(c, wx2 + hh * 0.05, wy, hh, '#dfe2ea', S, true); if (tap > 0.85) glow(c, wx2 + hh * 0.02, wy - hh * 0.06, hh * 0.15, '255,255,255', 0.9); return; }
    if (k === 'umbrella') { umbrella(c, wx2 + hh * 0.08, wy - hh * 0.25, hh * 0.3, L.umb[0], S, t / 2500); fig(c, L.ppl[0], x - hh * 0.1, d - hh * 0.02, hh * 0.88, reach(x - hh * 0.1, d - hh * 0.02, hh * 0.88, P, 1, [wx2 - hh * 0.05, wy - hh * 0.3 + Math.sin(t / 300) * hh * 0.04], null), 1); return; }
    if (k === 'wood') { fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.88, reach(x, d - hh * 0.02, hh * 0.88, P, 1, [wx2 - hh * 0.04, wy - hh * (0.1 + 0.14 * (1 - tap))], [wx2 + hh * 0.04, wy - hh * 0.05]), 1);
      fr(c, wx2 - hh * 0.08, wy - hh * (0.14 + 0.14 * (1 - tap)), hh * 0.12, hh * 0.06, '#8a5a32'); ln(c, [[wx2 + hh * 0.04, wy - hh * 0.05], [wx2 + hh * 0.1, wy + hh * 0.02]], '#9aa0a8', 2);
      for (i = 0; i < 4; i++) { var u2 = (t / 520 + i / 4) % 1; fr(c, wx2 + hh * (0.1 + u2 * 0.25), wy - hh * 0.05 - Math.sin(u2 * Math.PI) * hh * 0.15 + u2 * hh * 0.1, 2.5, 2.5, '#d8a868'); } return; }
    if (k === 'ceramic') { var wx3 = wx2, wyy = d - hh * 0.32; fe(c, wx3, wyy, hh * 0.2, hh * 0.04, '#7a6a5a'); for (i = 0; i < 4; i++) { var a = t / 150 + i * 1.57, px = wx3 + Math.cos(a) * hh * 0.18; if (Math.sin(a) > 0) fr(c, px - 1, wyy - 1, 2, 3, '#4a3a2a'); }
      fp(c, [[wx3 - hh * 0.07, wyy - hh * 0.02], [wx3 + hh * 0.07, wyy - hh * 0.02], [wx3 + hh * 0.09, wyy - hh * 0.12], [wx3 + hh * 0.04, wyy - hh * 0.22], [wx3 - hh * 0.04, wyy - hh * 0.22], [wx3 - hh * 0.09, wyy - hh * 0.12]], '#b8865a');
      fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.88, reach(x, d - hh * 0.02, hh * 0.88, P, 1, [wx3 - hh * 0.08, wyy - hh * 0.12], [wx3 + hh * 0.02, wyy - hh * 0.2]), 1); return; }
    fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.88, reach(x, d - hh * 0.02, hh * 0.88, P, 1, [wx2 - hh * 0.04 + Math.sin(t / 400) * hh * 0.04, wy - hh * 0.06], [wx2 + hh * 0.05, wy - hh * 0.04]), 1);
    if (k === 'lacquer') { bowl(c, wx2 + hh * 0.05, wy, hh * 1.2, '#9a1f1a', S); var pr = (t / 3000) % 1; c.strokeStyle = '#e8b84a'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(wx2 - hh * 0.08, wy - hh * 0.1); c.lineTo(wx2 - hh * 0.08 + pr * hh * 0.24, wy - hh * 0.1); c.stroke(); }
    else if (k === 'basket') { fp(c, [[wx2 - hh * 0.1, wy], [wx2 + hh * 0.14, wy], [wx2 + hh * 0.1, wy - hh * 0.12], [wx2 - hh * 0.06, wy - hh * 0.12]], '#c9a66b'); ln(c, [[wx2 - hh * 0.04, wy - hh * 0.06], [wx2 + hh * 0.2 + Math.sin(t / 400) * hh * 0.05, wy - hh * 0.3]], '#d8b878', 2); }
    else { fr(c, wx2 - hh * 0.08, wy - hh * 0.12, hh * 0.18, hh * 0.12, '#8a5a32'); ln(c, [[wx2 + hh * 0.02, wy - hh * 0.06], [wx2 + hh * 0.02 + Math.sin(t / 250) * hh * 0.1, wy - hh * 0.2]], '#f2e6c9', 1); }
  },
  fore: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, k = V.k, I = L.in, R = rnd(S.seed + 153);
    if (k === 'weave') return;
    if (k === 'gold' || k === 'silver') { counter(q, L.work + hh * 0.15, Math.min(I.x1 - hh * 0.05, L.work + hh * 0.75), d - hh * 0.45, S, k === 'gold' ? '#8a1f1a' : '#c9ccd4', true); for (var x = L.work + hh * 0.22; x < Math.min(I.x1 - hh * 0.05, L.work + hh * 0.75) - hh * 0.05; x += hh * 0.1) fe(q, x, d - hh * 0.25, hh * 0.035, hh * 0.02, k === 'gold' ? '#f2c94c' : '#dfe2ea'); if (k === 'gold') glow(q, L.work + hh * 0.45, d - hh * 0.3, hh * 0.5, '255,214,90', 0.5); return; }
    var y = desk(q, L.work + hh * 0.12, L.work + hh * 0.52, S, '#8a6a4a');
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, k = V.k, R = rnd(S.seed + 155), sd = L.sides[L.spirit && L.spirit.x < L.bx0 ? 1 : 0], room = sd.b - sd.a, x;
    if (L.open && k === 'basket') for (x = L.in.x0 + hh * 0.15; x < L.in.x1 - hh * 0.1; x += hh * 0.26) { var by = S.deck - L.gf + hh * 0.08; ln(q, [[x, by], [x, by + hh * 0.1]], 'rgba(60,40,20,.8)', 1); var bc2 = nt(S, pick(R, ['#c9a66b', '#a8804a', '#d8b878']), 0.3); fp(q, [[x - hh * 0.08, by + hh * 0.1], [x + hh * 0.08, by + hh * 0.1], [x + hh * 0.1, by + hh * 0.3], [x - hh * 0.1, by + hh * 0.3]], bc2); for (var yy2 = by + hh * 0.14; yy2 < by + hh * 0.3; yy2 += hh * 0.04) fr(q, x - hh * 0.09, yy2, hh * 0.18, 1, 'rgba(70,45,20,.55)'); fe(q, x, by + hh * 0.1, hh * 0.09, hh * 0.025, mixc(bc2, '#000000', 0.2)); }
    if (L.open && V.table) { var tx0 = L.in.x0 + hh * 0.1, tx1 = Math.min(L.in.x1 - hh * 0.1, tx0 + hh * 1.3), ty = d - hh * 0.32 + hh * 0.12; paper(q, rect(tx0, ty, tx1 - tx0, hh * 0.05), nt(S, '#8a5a32', 0.3), 1); fr(q, tx0 + hh * 0.05, ty, hh * 0.04, d + hh * 0.12 - ty, nt(S, '#6b4226', 0.3)); fr(q, tx1 - hh * 0.09, ty, hh * 0.04, d + hh * 0.12 - ty, nt(S, '#6b4226', 0.3));
      fr(q, tx0, ty + hh * 0.05, tx1 - tx0, hh * 0.08, nt(S, '#c0392b', 0.3)); for (var wx = tx0 + hh * 0.15; wx < tx1 - hh * 0.1; wx += hh * 0.25) { if (k === 'umbrella') umbrella(q, wx, ty - hh * 0.1, hh * 0.1, pick(R, ['#d9342b', '#f2c94c', '#2f9a5a', '#3a6fb0']), S, R()); else if (k === 'wood') elephant(q, wx, ty, hh * 0.22, '#8a5a32', S, 1); else if (k === 'weave') { phaSin(q, wx - hh * 0.1, ty - hh * 0.08, hh * 0.2, hh * 0.08, S, R); phaSin(q, wx - hh * 0.1, ty - hh * 0.16, hh * 0.2, hh * 0.08, S, R); } else if (k === 'basket') fp(q, [[wx - hh * 0.08, ty], [wx + hh * 0.08, ty], [wx + hh * 0.06, ty - hh * 0.12], [wx - hh * 0.06, ty - hh * 0.12]], nt(S, '#c9a66b', 0.3)); else bowl(q, wx, ty, hh * 0.9, k === 'silver' ? '#dfe2ea' : k === 'lacquer' ? pick(R, ['#9a1f1a', '#1a1a1a']) : k === 'gold' ? '#f2c94c' : k === 'ceramic' ? '#8fc0a0' : '#8a5a32', S, k === 'silver'); }
      L.tableX = (tx0 + tx1) / 2; }
    if (!L.open || room < hh * 0.7) return;
    var cx = (sd.a + sd.b) / 2;
    if (k === 'wood') { elephant(q, cx - hh * 0.25, d + hh * 0.12, hh * 0.55, '#8a5a32', S, 1); if (room > hh * 1.2) elephant(q, cx + hh * 0.3, d + hh * 0.12, hh * 0.35, '#6b4226', S, -1); }
    else if (k === 'umbrella') { for (x = 0; x < Math.min(3, Math.floor(room / (hh * 0.45))); x++) { var ux = sd.a + hh * 0.25 + x * hh * 0.42; ln(q, [[ux, d + hh * 0.12], [ux, d - hh * 0.4]], nt(S, '#6b4226', 0.3), 2); umbrella(q, ux, d - hh * 0.6, hh * 0.24, pick(R, ['#d9342b', '#f2c94c', '#2f9a5a', '#3a6fb0', '#e5567f']), S, R()); } }
    else if (k === 'weave') { L.rack = [sd.a + hh * 0.1, Math.min(sd.b - hh * 0.1, sd.a + hh * 1.0), d - hh * 1.05]; ln(q, [[L.rack[0], d + hh * 0.12], [L.rack[0], L.rack[2]], [L.rack[1], L.rack[2]], [L.rack[1], d + hh * 0.12]], nt(S, '#6b4226', 0.3), 2); }
    else if (k === 'ceramic' || k === 'basket') { for (x = sd.a + hh * 0.2; x < sd.b - hh * 0.1; x += hh * 0.3) { var jc = nt(S, k === 'ceramic' ? pick(R, ['#8fc0a0', '#6a3a1e', '#b8643a']) : '#c9a66b', 0.3); fp(q, [[x - hh * 0.08, d + hh * 0.12], [x + hh * 0.08, d + hh * 0.12], [x + hh * 0.12, d - hh * 0.1], [x + hh * 0.05, d - hh * 0.25], [x - hh * 0.05, d - hh * 0.25], [x - hh * 0.12, d - hh * 0.1]], jc); } }
  },
  street: function (S, L, V) {
    if (L.tableX && L.open) { var vx = L.tableX + S.hh * 0.75, vy = S.deck + S.hh * 0.16; fig(S.c, L.ppl[1], vx, vy, S.hh * 0.94, reach(vx, vy, S.hh * 0.94, { lean: 0.25, legs: [0.05, 0, -0.05, 0], arms: [1, 0.5, 1, 0.5] }, -1, [vx - S.hh * 0.32, S.deck - S.hh * 0.24 + Math.sin(S.t / 800) * S.hh * 0.03], null), -1); }
    if (!L.rack || !L.open) return; var c = S.c, hh = S.hh, t = S.t, R = rnd(S.seed + 157);
    for (var x = L.rack[0] + hh * 0.12, k = 0; x < L.rack[1] - hh * 0.08; x += hh * 0.22, k++) { c.save(); c.translate(x, L.rack[2]); c.rotate(0.05 * Math.sin(t / 1000 + k)); phaSin(c, -hh * 0.09, 0, hh * 0.18, hh * 0.75, S, R); c.restore(); }
  }
}, 'the shuttle: x = A·sin ωt<br>the cloth: one row a beat');

/* bank: a branch in its brand's colour (no mark, a tint), tellers behind the glass, the queue board,
   chairs, the guard at the door; the ATM lit day and night, a note sliding out, x = x₀ + v·t */
var BANKS = [[/กรุงเทพ|bangkok bank|\bbbl\b/i, '#1e3f9a'], [/ออมสิน|\bgsb\b|savings/i, '#e0157f'], [/กสิกร|kasikorn|kbank/i, '#138f2d'], [/กรุงไทย|krung ?thai|\bktb\b/i, '#0aa0dc'], [/ไทยพาณิชย์|\bscb\b|siam commercial/i, '#4e2a84'],
  [/ทหารไทย|ttb|\btmb\b|ธนชาต|thanachart/i, '#1d4f91'], [/ธ\.ก\.ส|เพื่อการเกษตร|baac/i, '#3d8f3a'], [/กรุงศรี|krungsri|ayudhya/i, '#e8b020'], [/uob|ยูโอบี/i, '#0b3c8c'], [/cimb|ซีไอเอ็มบี/i, '#b0102a'],
  [/อาคารสงเคราะห์|\bghb\b/i, '#e87a1f'], [/western union/i, '#e8c400'], [/ติดล้อ|leasing|ลิสซิ่ง|ไชโย|ไทยเครดิต|credit/i, '#1f8ac9']];
addShop('bank', {
  look: function (S, F, R) {
    var tint = '#2f5f6b'; for (var i = 0; i < BANKS.length; i++) if (has(F, BANKS[i][0])) { tint = BANKS[i][1]; break; }
    var small = has(F, /western union|ติดล้อ|leasing|ลิสซิ่ง|ไชโย|exchange|แลกเงิน/i);
    return { tint: tint, board: tint, light: 'cool', inWall: '#eef2f4', floor: '#d8d2c4', types: small ? { shop: 3, row: 2 } : { glass: 4, shop: 2 }, small: small, lanterns: R() < 0.5 ? 2 : 0, bikes: R() < 0.5 ? 1 : 0, mix: { casual: 0.8, sin: 0.12, mohom: 0.08 },
      wallArt: function (q, S, L) { fr(q, L.bx0, S.deck - L.gf - S.hh * 0.14, L.bw, S.hh * 0.08, nt(S, tint, 0.35)); } };
  },
  plan: function (S, L, V, R) {
    var hh = S.hh; L.ppl = crew(S, 6, V.mix, 29); L.staff = crew(S, 3, { casual: 1 }, 31); L.staff.forEach(function (d) { uni(d, mixc(V.tint, '#ffffff', 0.35), '#2c2f45'); }); L.guard = uni(crew(S, 1, { casual: 1 }, 33)[0], '#2c3e6b', '#2c2f45'); L.guard.hair = 4;
    var left = L.sides[0].b - L.sides[0].a, right = L.sides[1].b - L.sides[1].a;
    L.atmX = V.small ? null : right > hh * 0.9 ? L.bx1 + hh * 0.45 : left > hh * 0.9 ? L.bx0 - hh * 0.45 : L.bx1 - hh * 0.35;
    if (L.atmX && L.spirit && Math.abs(L.spirit.x - L.atmX) < hh * 0.8) L.spirit = null;
    L.tell = []; var n = clamp(Math.floor((L.in.x1 - L.in.x0 - hh * 0.6) / (hh * 0.8)), 1, 3); for (var i = 0; i < n; i++) L.tell.push(L.in.x0 + hh * 0.9 + i * hh * 0.8);
    L.bikes = L.bikes.filter(function (b) { return !L.atmX || Math.abs(b.x - L.atmX) > hh * 0.8; });
  },
  back: function (q, S, L, V) { var I = L.in, hh = S.hh, d = S.deck; fr(q, I.x0, I.y0 + hh * 0.02, I.x1 - I.x0, hh * 0.08, nt(S, V.tint, 0.2)); waitChairs(q, I.x0 + hh * 0.08, I.x0 + hh * 0.7, S, V.tint); },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    L.tell.forEach(function (x, i) { fig(c, L.staff[i], x, d - hh * 0.02, hh * 0.86, typing(t, i), -1); if (i < 2) fig(c, L.ppl[i], x - hh * 0.42, d - hh * 0.02, hh * 0.92, talk(t, i), 1); });
    fig(c, L.ppl[3], I.x0 + hh * 0.38, d - hh * 0.02, hh * 0.88, sitTalk(t, 4), 1);
  },
  fore: function (q, S, L, V) { var I = L.in, hh = S.hh, d = S.deck; if (!L.tell.length) return; var x0 = L.tell[0] - hh * 0.3, x1 = Math.min(I.x1 - hh * 0.05, L.tell[L.tell.length - 1] + hh * 0.2); counter(q, x0, x1, d - hh * 0.42, S, mixc(V.tint, '#ffffff', 0.5)); fr(q, x0, d - hh * 0.85, x1 - x0, hh * 0.4, 'rgba(200,230,240,.25)'); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, x = L.atmX; if (!x) return;
    paper(q, rect(x - hh * 0.22, d - hh * 1.05, hh * 0.44, hh * 1.05 + hh * 0.1), nt(S, mixc(V.tint, '#ffffff', 0.15), 0.3), 1.3);
    fr(q, x - hh * 0.22, d - hh * 1.05, hh * 0.44, hh * 0.12, nt(S, V.tint, 0.2)); fr(q, x - hh * 0.15, d - hh * 0.82, hh * 0.3, hh * 0.22, '#1a2230'); fr(q, x - hh * 0.13, d - hh * 0.8, hh * 0.26, hh * 0.18, '#7fd0f0');
    for (var i = 0; i < 9; i++) fr(q, x - hh * 0.1 + (i % 3) * hh * 0.07, d - hh * (0.55 - Math.floor(i / 3) * 0.05), hh * 0.05, hh * 0.035, '#dfe2ea'); fr(q, x - hh * 0.12, d - hh * 0.36, hh * 0.24, hh * 0.03, '#1a1a1a');
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.atmX;
    if (x) { glow(c, x, d - hh * 0.72, hh * 0.35, '127,208,240', S.night ? 0.8 : 0.3); var u = (t / 7000) % 1, pr = u > 0.45 && u < 0.7 ? (u - 0.45) / 0.25 : 0;
      if (pr > 0) fr(c, x - hh * 0.08, d - hh * 0.35, hh * 0.16, hh * 0.08 * Math.min(1, pr * 2), '#9ad08a');
      if (!S.night || L.open || S.seed % 2) fig(c, L.ppl[4], x + hh * 0.4, d + hh * 0.16, hh * 0.94, reach(x + hh * 0.4, d + hh * 0.16, hh * 0.94, STANDP, -1, u < 0.45 ? [x + hh * 0.08 + Math.sin(t / 200) * hh * 0.02, d - hh * 0.5] : [x + hh * 0.05, d - hh * 0.33], null), -1); }
    if (L.open) { var gx = L.in.x0 + hh * 0.12; fig(c, L.guard, gx, d + hh * 0.14, hh * 0.95, { lean: 0.02, legs: [0.05, 0, -0.05, 0], arms: [0.05, 0.1, -0.05, 0.1 + 0.05 * Math.sin(t / 1500)] }, 1); }
  }
}, 'a note slides out: x = x₀ + vt');

/* laundry: a row of front-loaders, the clothes tumbling behind each round door, θ = ωt, a coin laundry
   lit at night when its name says 24 hours; or a laundry shop of shirts in plastic, the iron sliding and steaming, and shirts on
   the line outside swinging, θ = θ₀·sin(ωt + kφ) */
addShop('laundry', {
  look: function (S, F, R) {
    var coin = has(F, /หยอดเหรียญ|coin|otteri|laundrybar|wash ?(&|and) ?dry|\b24\b|สะดวกซัก|self|laundromat|อัตโนมัติ|browny/i) || R() < 0.25;
    var del = (F.services || []).some(function (s) { return /deliver/i.test(s); }) || has(F, /deliver|ดิลิเวอรี่|รับส่ง/i);
    return { k: coin ? 'coin' : 'iron', del: del, types: coin ? { glass: 4, shop: 2 } : { shop: 3, row: 3, teak: 0.6 }, light: coin ? 'cool' : 'warm', inWall: coin ? '#eef4f6' : null, bikes: del ? 0 : null, mix: { casual: 0.85, sin: 0.15 } };
  },
  plan: function (S, L, V, R) { var I = L.in, hh = S.hh, d = S.deck; L.drums = []; if (V.k === 'coin') { var n = Math.max(2, Math.floor((I.x1 - I.x0 - hh * 0.6) / (hh * 0.42))); for (var j = 0; j < n; j++) { var xx = I.x0 + hh * 0.3 + j * hh * 0.42; L.drums.push([xx, d - hh * 0.28]); if (j % 2 === 0) L.drums.push([xx, d - hh * 0.78]); } }
    L.ppl = crew(S, 3, V.mix, 35); L.tumble = []; for (var i = 0; i < 12; i++) L.tumble.push([pick(R, CLOTHS), pick(R, CLOTHS)]); L.lineSide = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? 0 : 1; L.shirts = []; for (i = 0; i < 6; i++) L.shirts.push(pick(R, CLOTHS)); },
  state: function (S, F, st) { return st === 'quiet' && has(F, /24 ?(ชั่วโมง|ชม|hour|hrs|h\b)|24\/7/i) ? 'open' : st; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 161), w = I.x1 - I.x0;
    if (V.k === 'coin') { var n = Math.max(2, Math.floor((w - hh * 0.6) / (hh * 0.42)));
      for (var i = 0; i < n; i++) { var x = I.x0 + hh * 0.3 + i * hh * 0.42; paper(q, rect(x - hh * 0.19, d - hh * 0.5, hh * 0.38, hh * 0.48), nt(S, '#f6f6f2', 0.2), 1); fe(q, x, d - hh * 0.28, hh * 0.13, hh * 0.13, nt(S, '#9aa0a8', 0.2)); fe(q, x, d - hh * 0.28, hh * 0.11, hh * 0.11, '#2a3a4a'); fr(q, x - hh * 0.15, d - hh * 0.47, hh * 0.3, hh * 0.04, nt(S, '#c9ccd4', 0.2));
        if (i % 2 === 0) { paper(q, rect(x - hh * 0.19, d - hh * 1.0, hh * 0.38, hh * 0.46), nt(S, '#e8eaee', 0.2), 1); fe(q, x, d - hh * 0.78, hh * 0.12, hh * 0.12, '#2a3a4a'); } }
      return; }
    var rx0 = I.x0 + hh * 0.08, rx1 = I.x0 + w * 0.55; fr(q, rx0, I.y0 + hh * 0.1, rx1 - rx0, 2.5, nt(S, '#9aa0a8', 0.2));
    for (x = rx0 + hh * 0.1; x < rx1 - hh * 0.05; x += hh * 0.12) { garment(q, x, I.y0 + hh * 0.1, hh * 0.85, 'shirt', pick(R, ['#f2f2ee', '#cfe0f0', '#f2e6c9', '#2c3e6b', '#e8d8f0']), S); fr(q, x - hh * 0.09, I.y0 + hh * 0.14, hh * 0.18, hh * 0.3, 'rgba(230,240,250,.35)'); }
    shelves(q, I.x0 + w * 0.6, I.x1 - hh * 0.06, I.y0 + hh * 0.06, d - hh * 0.04, 3, S, function (p, a, b, yb, h) { for (var xx = a; xx < b - hh * 0.2; xx += hh * 0.22) fe(p, xx + hh * 0.1, yb - h * 0.4, hh * 0.1, h * 0.4, nt(S, pick(R, ['#ffd1e8', '#c9e8f8', '#f7f0b0', '#d0f0d8', '#f2f2ee']), 0.2)); });
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in;
    if (V.k === 'coin') { (L.drums || []).forEach(function (p, i) { if (i % 3 === 2) return; var a = t / (i % 2 ? 260 : 330) + i, cols = L.tumble[i % 12];
        c.save(); c.beginPath(); c.arc(p[0], p[1], hh * 0.105, 0, TAU); c.clip(); fe(c, p[0], p[1] + hh * 0.05, hh * 0.11, hh * 0.06, 'rgba(120,180,230,.5)');
        for (var k = 0; k < 3; k++) fe(c, p[0] + Math.cos(a + k * 2.1) * hh * 0.05, p[1] + Math.sin(a + k * 2.1) * hh * 0.05, hh * 0.05, hh * 0.03, cols[k % 2], a + k); c.restore(); });
      var bx = I.x0 + (I.x1 - I.x0) * 0.62; var me = fig(c, L.ppl[0], bx, d - hh * 0.02, hh * 0.86, { lean: 0.15, seat: 0.27, legs: [1.45, -1.45, 1.38, -1.4], arms: [1.1, 0.9, 1.0, 1.0] }, -1);
      glow(c, me.hand[0][0], me.hand[0][1] - hh * 0.02, hh * 0.1, '190,225,255', 0.8); fr(c, me.hand[0][0] - hh * 0.02, me.hand[0][1] - hh * 0.05, hh * 0.04, hh * 0.06, '#bfe6f2'); return; }
    var ix = I.x0 + (I.x1 - I.x0) * 0.45, iy = d - hh * 0.45, sl = Math.sin(t / 600) * hh * 0.12;
    fig(c, L.ppl[0], ix - hh * 0.3, d - hh * 0.02, hh * 0.9, reach(ix - hh * 0.3, d - hh * 0.02, hh * 0.9, STANDP, 1, [ix + sl, iy - hh * 0.07], [ix + hh * 0.22, iy - hh * 0.02]), 1);
    fp(c, [[ix + sl - hh * 0.07, iy - hh * 0.02], [ix + sl + hh * 0.08, iy - hh * 0.02], [ix + sl + hh * 0.05, iy - hh * 0.07], [ix + sl - hh * 0.05, iy - hh * 0.07]], '#5a8ac0'); steam(c, ix + sl, iy - hh * 0.08, hh, t, 1, 3, hh * 0.18);
  },
  fore: function (q, S, L, V) { if (V.k === 'coin') return; var I = L.in, hh = S.hh, d = S.deck, ix = I.x0 + (I.x1 - I.x0) * 0.45, iy = d - hh * 0.45; fr(q, ix - hh * 0.15, iy, hh * 0.55, hh * 0.04, nt(S, '#cfd8e0', 0.2)); ln(q, [[ix - hh * 0.05, iy], [ix + hh * 0.25, d], [ix + hh * 0.05, iy + hh * 0.2], [ix - hh * 0.05, d]], nt(S, '#5a5e66', 0.2), 1.5);
    for (var i = 0; i < 3; i++) fe(q, I.x1 - hh * (0.3 + i * 0.25), d - hh * 0.12, hh * 0.12, hh * 0.12, nt(S, ['#ffd1e8', '#c9e8f8', '#f7f0b0'][i], 0.2)); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, sd = L.sides[L.lineSide];
    if (V.del) scooter(q, L.bx0 + hh * 0.5, d + hh * 0.17, hh * 0.92, '#3a6fb0', 1, S, '#f2f2ee');
    if (V.k === 'iron' && L.open && sd.b - sd.a > hh * 0.9) { var a = sd.a + hh * 0.1, b = Math.min(sd.b - hh * 0.1, a + hh * 1.6); fr(q, a - 1, d - hh * 0.95, 2.5, hh * 1.07, nt(S, '#9aa0a8', 0.35)); fr(q, b - 1, d - hh * 0.95, 2.5, hh * 1.07, nt(S, '#9aa0a8', 0.35)); L.line = [a, b, d - hh * 0.9]; }
  },
  street: function (S, L, V) {
    if (!L.line) return; var c = S.c, hh = S.hh, t = S.t, a = L.line[0], b = L.line[1], y = L.line[2];
    ln(c, [[a, y], [(a + b) / 2, y + hh * 0.05], [b, y]], 'rgba(60,60,60,.8)', 1);
    for (var k = 0, x = a + hh * 0.18; x < b - hh * 0.1; x += hh * 0.26, k++) { c.save(); c.translate(x, y + hh * 0.04 * Math.sin((x - a) / (b - a) * Math.PI)); c.rotate(0.12 * Math.sin(t / 700 + k * 0.8)); garment(c, 0, 0, hh * 0.85, k % 2 ? 'tee' : 'shirt', L.shirts[k % 6], S); c.restore(); }
  }
}, 'the drum: θ = ωt<br>the line: θ = θ₀·sin(ωt + kφ)');

/* fuel: a canopy over the pump islands in the brand's tint (no mark), the attendant in a cap filling a
   scooter while the counter rolls, n = ⌊vt⌋; the grade board (91, 95, E20, ดีเซล), air and the toilet
   sign a traveller looks for; or a coin pump by a shophouse, or bottles on a rack and the glass-tube
   hand pump of a village */
var FUELS = [[/ptt|ป\.ต\.ท|ปตท/i, '#1f4f9c', '#3fa9e0'], [/\bpt\b|พีที/i, '#1f8a4a', '#f2c94c'], [/bangchak|บางจาก/i, '#5aa83a', '#1f6f3a'], [/shell|เชลล์/i, '#f2c400', '#d9242b'], [/caltex|คาลเท็กซ์/i, '#d9242b', '#1f4f9c'], [/esso|เอสโซ่/i, '#1f3f9a', '#d9242b'], [/cosmo|susco|ซัสโก้/i, '#1f5fb0', '#d9242b']];
addShop('fuel', {
  look: function (S, F, R) {
    var t1 = '#2f6f8a', t2 = '#f2c94c'; for (var i = 0; i < FUELS.length; i++) if (has(F, FUELS[i][0])) { t1 = FUELS[i][1]; t2 = FUELS[i][2]; break; }
    var k = has(F, /minipump|มินิปั๊ม|หยอดเหรียญ|coin/i) ? 'mini' : has(F, /น้ำมันขวด|ปั๊มหลอด|ปั๊มหลอด/i) || (!F.brand && F.moo && !F.oldCity && R() < 0.6) ? 'bottle' : 'station';
    var V = { k: k, t1: t1, t2: t2, mix: { casual: 1 }, lanterns: 0 };
    if (k === 'station') { V.type = 'custom'; V.custom = station; V.w = 5.4 + R() * 1.2; V.bikes = 0; V.noUnit = true; }
    else { V.types = { row: 3, stall: 3, shop: 1 }; V.w = 3.2 + R() * 1; V.at = R() < 0.5 ? 0.15 : 0.75; V.bikes = 0; }
    return V;
  },
  plan: function (S, L, V, R) {
    var hh = S.hh, d = S.deck; L.att = crew(S, 3, { casual: 1 }, 37); L.att.forEach(function (a) { uni(a, V.t1, '#2c2f45'); a.hair = 4; }); L.rider = crew(S, 2, { casual: 0.8, sin: 0.2 }, 39);
    if (V.k === 'station') { L.top = d - hh * 2.2; L.canY = d - hh * 1.72; L.signAt = 'face'; L.signY = L.canY - hh * 0.02; L.pumps = [L.bx0 + L.bw * 0.3, L.bx0 + L.bw * 0.68]; L.pylon = L.bx1 + hh * 0.5 < S.x1 - hh * 0.9 ? L.bx1 + hh * 0.45 : L.bx0 - hh * 0.45; if (L.spirit && Math.abs(L.spirit.x - L.pylon) < hh * 0.7) L.spirit = null; L.bikeCol = pick(R, BIKE); L.truck = pick(R, CARS); L.animal = 'none'; L.walkers = 0; }
    else { var sd = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? L.sides[0] : L.sides[1]; L.pumpX = clamp((sd.a + sd.b) / 2, sd.a + hh * 0.4, sd.b - hh * 0.4); if (L.spirit && Math.abs(L.spirit.x - L.pumpX) < hh * 0.9) L.spirit = null; L.bikeCol = pick(R, BIKE); }
  },
  back: function (q, S, L, V) { var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 171); if (V.k === 'station') return; shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.08, d - hh * 0.04, 3, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#d9342b', '#f2c94c', '#3a6fb0', '#2f9a5a', '#f2f2ee'], S, 'bottle'); }); },
  live: function (S, L, V) { if (V.k === 'station') return; var c = S.c, hh = S.hh, d = S.deck, I = L.in, x = I.x0 + (I.x1 - I.x0) * 0.5; fig(c, L.att[1], x, d - hh * 0.02, hh * 0.88, sitTalk(S.t, 2), 1); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, x = L.pumpX;
    if (V.k === 'mini') { paper(q, rect(x - hh * 0.18, d - hh * 1.0 + hh * 0.1, hh * 0.36, hh * 1.0), nt(S, V.t1, 0.35), 1.3); fr(q, x - hh * 0.13, d - hh * 0.8, hh * 0.26, hh * 0.16, '#1a2230'); fr(q, x - hh * 0.06, d - hh * 0.55, hh * 0.12, hh * 0.08, nt(S, '#d8dade', 0.3)); fr(q, x + hh * 0.18, d - hh * 0.55, hh * 0.04, hh * 0.12, '#2a2a2a'); }
    if (V.k === 'bottle') { var rx = x - hh * 0.35; fr(q, rx, d - hh * 0.62 + hh * 0.1, hh * 0.04, hh * 0.62, nt(S, '#6b4226', 0.3)); fr(q, rx + hh * 0.42, d - hh * 0.62 + hh * 0.1, hh * 0.04, hh * 0.62, nt(S, '#6b4226', 0.3));
      for (var r = 0; r < 3; r++) { var ry = d + hh * 0.1 - r * hh * 0.21; fr(q, rx, ry - 2, hh * 0.46, 3, nt(S, '#6b4226', 0.3)); for (var b = 0; b < 4; b++) { var bx = rx + hh * 0.06 + b * hh * 0.1, col = r === 1 ? '#7fb83a' : '#e8402a'; fr(q, bx, ry - hh * 0.16, hh * 0.06, hh * 0.14, col); fr(q, bx + hh * 0.015, ry - hh * 0.2, hh * 0.03, hh * 0.04, '#e8e2d0'); fr(q, bx + hh * 0.01, ry - hh * 0.1, hh * 0.015, hh * 0.05, 'rgba(255,255,255,.45)'); } }
      var cx = x + hh * 0.35; fr(q, cx - hh * 0.12, d + hh * 0.06, hh * 0.24, hh * 0.06, nt(S, '#d9342b', 0.3)); fr(q, cx - hh * 0.03, d - hh * 0.2, hh * 0.06, hh * 0.28, nt(S, '#d9342b', 0.3)); fr(q, cx - hh * 0.09, d - hh * 0.95, hh * 0.18, hh * 0.75, 'rgba(220,235,240,.45)'); q.strokeStyle = nt(S, '#d9342b', 0.3); q.lineWidth = 2; q.strokeRect(cx - hh * 0.09, d - hh * 0.95, hh * 0.18, hh * 0.75); fe(q, cx, d - hh * 0.98, hh * 0.1, hh * 0.03, nt(S, '#d9342b', 0.3)); L.tube = [cx, d - hh * 0.95, hh * 0.75]; }
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, i;
    if (V.k === 'station') {
      L.pumps.forEach(function (px, i) { var n = Math.floor((t / 90 + i * 333) % 1000); digits(c, px, d - hh * 0.8, hh * 0.07, (n / 10).toFixed(1), '#ff6a3a', '#1a1a1a'); });
      if (L.open || S.night) { var p0 = L.pumps[0], sx = p0 + hh * 0.75; var spr = sprite(S, 'fuelbike' + L.bikeCol, hh * 1.3, hh * 0.85, function (q) { scooter(q, hh * 0.65, hh * 0.84, hh * 0.9, L.bikeCol, -1, S); });
        if (spr) c.drawImage(spr, sx - hh * 0.65, d + hh * 0.18 - hh * 0.84, hh * 1.3, hh * 0.85);
        fig(c, L.rider[0], sx + hh * 0.35, d + hh * 0.16, hh * 0.92, talk(t, 2), -1);
        var ax = p0 + hh * 0.3, tank = [sx + hh * 0.05, d - hh * 0.32], me = fig(c, L.att[0], ax, d + hh * 0.16, hh * 0.92, reach(ax, d + hh * 0.16, hh * 0.92, STANDP, 1, tank, null), 1);
        ln(c, [[p0 + hh * 0.12, d - hh * 0.6], [p0 + hh * 0.3, d - hh * 0.2], tank], '#1a1a1a', Math.max(1.5, hh * 0.025));
        car(c, L.pumps[1] + hh * 0.95, d + hh * 0.2, hh * 0.9, 'pickup', L.truck, -1, S);
        var w2 = Math.sin(t / 260); fig(c, L.att[1], L.pumps[1] + hh * 0.35, d + hh * 0.16, hh * 0.92, reach(L.pumps[1] + hh * 0.35, d + hh * 0.16, hh * 0.92, STANDP, 1, [L.pumps[1] + hh * 0.5 + w2 * hh * 0.05, d - hh * 0.62 - Math.abs(w2) * hh * 0.1], null), 1); }
      return; }
    if (!L.open) return;
    var x = L.pumpX, u = (t / 9000) % 1;
    var spr2 = sprite(S, 'fuelbike' + L.bikeCol, hh * 1.3, hh * 0.85, function (q) { scooter(q, hh * 0.65, hh * 0.84, hh * 0.9, L.bikeCol, -1, S); });
    var bx = x + hh * (V.k === 'bottle' ? 0.9 : 0.75); if (spr2 && bx < S.x1 - hh * 0.6) { c.drawImage(spr2, bx - hh * 0.65, d + hh * 0.2 - hh * 0.84, hh * 1.3, hh * 0.85); fig(c, L.rider[0], bx + hh * 0.05, d + hh * 0.2 - hh * 0.18, hh * 0.92, { lean: 0.05, seat: 0.3, legs: [1.3, -1.0, 1.2, -1.1], arms: [1.0, 0.4, 0.9, 0.5] }, -1); }
    if (V.k === 'bottle' && L.tube) { var lv = 0.25 + 0.6 * (0.5 + 0.5 * Math.cos(u * TAU)); fr(c, L.tube[0] - hh * 0.08, L.tube[1] + L.tube[2] * (1 - lv), hh * 0.16, L.tube[2] * lv, 'rgba(232,90,50,.75)'); for (i = 1; i < 5; i++) fr(c, L.tube[0] - hh * 0.08, L.tube[1] + L.tube[2] * i / 5, hh * 0.05, 1, '#1a1a1a'); }
    if (V.k === 'mini') { var n2 = Math.floor((t / 120) % 300); digits(c, x, d - hh * 0.72, hh * 0.06, (n2 / 10).toFixed(1), '#5aff7a'); }
  }
}, 'the counter: n = ⌊vt⌋');
function station(q, S, L) {
  var V = L.V, hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, cy = L.canY, t1 = nt(S, V.t1, 0.35), t2 = nt(S, V.t2, 0.35), R = rnd(S.seed + 173), i;
  /* the shop behind, then the canopy on its columns, the islands and pumps */
  var sx0 = x1 - Math.min(hh * 2.0, L.bw * 0.35), sw = Math.min(hh * 2.0, L.bw * 0.35); paper(q, rect(sx0, d - hh * 1.15, sw, hh * 1.15), nt(S, '#f2f2ee', 0.4), 1.2); fr(q, sx0 + hh * 0.1, d - hh * 0.95, sw - hh * 0.2, hh * 0.9, L.open || S.night ? (S.night ? '#ffe8b0' : nt(S, '#cfe3ea', 0.3)) : nt(S, '#2a3040', 0.3)); fr(q, sx0, d - hh * 1.15, sw, hh * 0.1, t1);
  if (L.open || S.night) goods(q, sx0 + hh * 0.15, sx0 + sw - hh * 0.15, d - hh * 0.4, hh * 0.25, R, ['#d9342b', '#f2c94c', '#3a6fb0', '#2f9a5a'], S, 'bag');
  [x0 + hh * 0.2, (x0 + x1) / 2, x1 - hh * 0.2].forEach(function (x) { paper(q, rect(x - hh * 0.06, cy, hh * 0.12, d - cy), nt(S, '#e8e8e2', 0.4), 1.2); });
  L.pumps.forEach(function (px) {
    paper(q, rect(px - hh * 0.4, d - hh * 0.08, hh * 0.8, hh * 0.1), nt(S, '#d8d2c4', 0.4), 1); for (var k = 0; k < 4; k++) fr(q, px - hh * 0.4 + k * hh * 0.2, d - hh * 0.08, hh * 0.1, hh * 0.1, nt(S, k % 2 ? '#f2f2f2' : '#d9342b', 0.4));
    paper(q, rect(px - hh * 0.16, d - hh * 0.95, hh * 0.32, hh * 0.88), nt(S, '#f2f2ee', 0.35), 1.3); fr(q, px - hh * 0.16, d - hh * 0.95, hh * 0.32, hh * 0.12, t1); fr(q, px - hh * 0.16, d - hh * 0.2, hh * 0.32, hh * 0.05, t2);
    fr(q, px - hh * 0.12, d - hh * 0.62, hh * 0.24, hh * 0.08, nt(S, '#3a3a3a', 0.3)); [-1, 1].forEach(function (sd) { fr(q, px + sd * hh * 0.17 - (sd < 0 ? hh * 0.05 : 0), d - hh * 0.62, hh * 0.05, hh * 0.12, nt(S, '#2a2a2a', 0.3)); });
  });
  paper(q, rect(x0 - hh * 0.25, cy - hh * 0.22, x1 - x0 + hh * 0.5, hh * 0.22), nt(S, '#f6f6f2', 0.35), 1.8); fr(q, x0 - hh * 0.25, cy - hh * 0.06, x1 - x0 + hh * 0.5, hh * 0.06, t1); fr(q, x0 - hh * 0.25, cy - hh * 0.22, x1 - x0 + hh * 0.5, hh * 0.03, t2);
  if (S.night) for (var x = x0 + hh * 0.3; x < x1; x += hh * 0.8) { fr(q, x - hh * 0.15, cy, hh * 0.3, 3, '#ffffff'); glow(q, x, cy + hh * 0.3, hh * 0.9, '235,245,255', 0.35); }
  /* the board on its pylon: a colour chip a grade */
  var py = L.pylon, ptop = d - hh * 2.15, grades = [['91', '#2f9a5a'], ['95', '#e8b84a'], ['E20', '#d9342b'], ['ดีเซล', '#3a6fb0']];
  paper(q, rect(py - hh * 0.05, ptop + hh * 0.9, hh * 0.1, d - ptop - hh * 0.9), nt(S, '#c9ccd4', 0.4), 1); paper(q, rect(py - hh * 0.28, ptop, hh * 0.56, hh * 1.0), t1, 1.4);
  grades.forEach(function (g, j) { var gy = ptop + hh * (0.12 + j * 0.21); fr(q, py - hh * 0.22, gy, hh * 0.44, hh * 0.17, '#f6f6f2'); fr(q, py - hh * 0.22, gy, hh * 0.1, hh * 0.17, g[1]); fr(q, py - hh * 0.08, gy + hh * 0.05, hh * 0.24, hh * 0.07, '#1a1a1a'); });
  /* the air pump and its hose */
  var ax = x0 + hh * 0.05; fr(q, ax - hh * 0.04, d - hh * 0.6, hh * 0.08, hh * 0.6, nt(S, '#f2c94c', 0.35)); q.strokeStyle = nt(S, '#1a1a1a', 0.3); q.lineWidth = 1.2; q.beginPath(); for (i = 0; i < 3; i++) q.ellipse(ax + hh * 0.08, d - hh * 0.3, hh * 0.05, hh * 0.08, 0, 0, TAU); q.stroke();
}

/* tours: a desk with the agent and travellers with backpacks, posters of the north (elephants walked
   and bathed, not ridden; the doi over a sea of mist; a waterfall that runs, y = y₀ + vt), a rack of
   brochures, the white minivan waiting with its hazards blinking */
addShop('tours', {
  look: function (S, F, R) { return { types: { shop: 3, lanna: 2, teak: 1, row: 1.4, glass: 1 }, light: 'warm', w: 3.9 + R() * 1.4, bikes: R() < 0.5 ? 0 : 1, mix: { casual: 0.9, sin: 0.1 }, van: R() < 0.75 }; },
  plan: function (S, L, V, R) { var hh = S.hh; L.ppl = crew(S, 4, V.mix, 41); [1, 2].forEach(function (i) { L.ppl[i].hairCol = pick(R, ['#d9b36a', '#8a5a2a', '#1c1410', '#c9853a']); L.ppl[i].skin = pick(R, ['#f1c9a5', '#e3b08a', '#d29a6e']); });
    L.posters = ['ele', 'doi', 'fall', pick(R, ['raft', 'wat', 'ele'])]; var room = L.sides[1].b - L.sides[1].a, rooml = L.sides[0].b - L.sides[0].a; L.vanX = V.van ? (room > hh * 2.3 ? L.bx1 + hh * 1.2 : rooml > hh * 2.3 ? L.bx0 - hh * 1.2 : null) : null; if (L.vanX && L.spirit && Math.abs(L.spirit.x - L.vanX) < hh * 1.5) L.spirit = null; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, w = I.x1 - I.x0, n = clamp(Math.floor(w / (hh * 0.62)), 2, 5), pw = hh * 0.48, ph = hh * 0.36;
    L.fall = null;
    for (var i = 0; i < n; i++) { var px = I.x0 + (w - n * hh * 0.62) / 2 + i * hh * 0.62 + hh * 0.07, py = I.y0 + hh * 0.06, kind = L.posters[i % 4];
      poster(q, px, py, pw, ph, S, function (p, x, y, ww, h) {
        if (kind === 'ele') { fr(p, x, y, ww, h, '#cfe8d8'); fr(p, x, y + h * 0.75, ww, h * 0.25, '#7aa86a'); elephant(p, x + ww * 0.42, y + h * 0.85, h * 0.6, '#7a7f88', { night: false }, 1); fig(p, { col: '#2c3e6b', low: '#2c3e6b', garb: 'mohom', skin: '#b97f52' }, x + ww * 0.1, y + h * 0.88, h * 0.45, K.walkP(1, false), 1); }
        else if (kind === 'doi') { fr(p, x, y, ww, h, '#f7d9a8'); fp(p, [[x, y + h], [x + ww * 0.3, y + h * 0.35], [x + ww * 0.55, y + h * 0.6], [x + ww * 0.8, y + h * 0.25], [x + ww, y + h * 0.5], [x + ww, y + h]], '#4d6a8a'); fr(p, x, y + h * 0.65, ww, h * 0.12, 'rgba(255,255,255,.75)'); fe(p, x + ww * 0.8, y + h * 0.2, ww * 0.08, ww * 0.08, '#f29a3a'); }
        else if (kind === 'fall') { fr(p, x, y, ww, h, '#9ac8a0'); fr(p, x + ww * 0.38, y, ww * 0.24, h, '#dff2f8'); fe(p, x + ww * 0.5, y + h * 0.95, ww * 0.35, h * 0.1, '#bfe6f2'); L.fall = [x + ww * 0.38, y, ww * 0.24, h]; }
        else if (kind === 'raft') { fr(p, x, y, ww, h, '#bfe0f0'); fr(p, x, y + h * 0.6, ww, h * 0.4, '#4b8fc9'); fe(p, x + ww * 0.5, y + h * 0.62, ww * 0.3, h * 0.07, '#e8b84a'); }
        else { fr(p, x, y, ww, h, '#f2e0b0'); fp(p, [[x + ww * 0.2, y + h], [x + ww * 0.5, y + h * 0.5], [x + ww * 0.8, y + h]], '#3f7a3a'); fp(p, [[x + ww * 0.44, y + h * 0.52], [x + ww * 0.5, y + h * 0.15], [x + ww * 0.56, y + h * 0.52]], '#d9a53c'); } });
    }
    var rx = I.x1 - hh * 0.35; fr(q, rx - hh * 0.18, d - hh * 0.75, hh * 0.36, hh * 0.75, nt(S, '#8a6a4a', 0.2)); var R = rnd(S.seed + 181); for (var r = 0; r < 4; r++) for (var j = 0; j < 3; j++) fr(q, rx - hh * 0.15 + j * hh * 0.1, d - hh * (0.7 - r * 0.17), hh * 0.08, hh * 0.12, nt(S, pick(R, CLOTHS), 0.2));
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, w = I.x1 - I.x0, dx = I.x0 + w * 0.32;
    if (L.fall) { c.save(); c.beginPath(); c.rect(L.fall[0], L.fall[1], L.fall[2], L.fall[3]); c.clip(); for (var i = 0; i < 6; i++) { var yy = L.fall[1] + ((t / 20 + i * L.fall[3] / 6) % L.fall[3]); fr(c, L.fall[0] + (i % 3) * L.fall[2] / 3, yy, 1.2, L.fall[3] * 0.15, 'rgba(120,180,220,.8)'); } c.restore(); }
    fig(c, L.ppl[0], dx - hh * 0.3, d - hh * 0.02, hh * 0.88, sitTalk(t, 0), 1);
    [0, 1].forEach(function (k) { var tx = dx + hh * (0.55 + k * 0.38), dir = -1, me = fig(c, L.ppl[1 + k], tx, d - hh * 0.02, hh * 0.95, k ? reach(tx, d - hh * 0.02, hh * 0.95, STANDP, -1, [tx - hh * 0.2, I.y0 + hh * 0.3 + Math.sin(t / 900) * hh * 0.04], null) : talk(t, 5), dir);
      fp(c, [[me.sh[0] + hh * 0.04, me.sh[1] - hh * 0.02], [me.sh[0] + hh * 0.17, me.sh[1]], [me.sh[0] + hh * 0.15, me.sh[1] + hh * 0.3], [me.sh[0] + hh * 0.04, me.sh[1] + hh * 0.28]], k ? '#d9642a' : '#2f6f5a'); });
    if (L.type !== 'glass') ceilFan(c, dx + hh * 0.3, I.y0 - hh * 0.08, hh, t);
  },
  fore: function (q, S, L, V) { var I = L.in, hh = S.hh, d = S.deck, dx = I.x0 + (I.x1 - I.x0) * 0.32; var y = desk(q, dx - hh * 0.1, dx + hh * 0.35, S, '#8a6a4a'); fr(q, dx, y - hh * 0.04, hh * 0.2, hh * 0.04, nt(S, '#f2f2ee', 0.2)); fp(q, [[dx + hh * 0.22, y], [dx + hh * 0.3, y - hh * 0.06], [dx + hh * 0.36, y - hh * 0.06], [dx + hh * 0.3, y]], nt(S, '#3a6fb0', 0.2)); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck;
    if (L.vanX) car(q, L.vanX, d + hh * 0.2, hh * 0.95, 'van', '#f2f2f2', L.vanX > L.bx1 ? -1 : 1, S);
    if (L.open) { var ax = L.bx0 + hh * 0.35; fp(q, [[ax - hh * 0.18, d + hh * 0.12], [ax - hh * 0.12, d - hh * 0.5], [ax + hh * 0.12, d - hh * 0.5], [ax + hh * 0.18, d + hh * 0.12]], nt(S, '#3a2a22', 0.3)); fr(q, ax - hh * 0.1, d - hh * 0.45, hh * 0.2, hh * 0.14, nt(S, '#9ac8a0', 0.3)); fr(q, ax - hh * 0.1, d - hh * 0.27, hh * 0.2, hh * 0.14, nt(S, '#f7d9a8', 0.3)); }
  },
  street: function (S, L, V) { if (!L.vanX || !L.open) return; var c = S.c, hh = S.hh, d = S.deck, on = Math.floor(S.t / 450) % 2, dir = L.vanX > L.bx1 ? -1 : 1; if (on) { glow(c, L.vanX + dir * hh * 1.17, d - hh * 0.06, hh * 0.12, '255,170,40', 0.95); glow(c, L.vanX - dir * hh * 1.17, d - hh * 0.06, hh * 0.12, '255,170,40', 0.95); } }
}, 'the waterfall: y = y₀ + vt');

/* printing: a copier whose light bar sweeps under the lid, x = x₀ + A·(1 − cos ωt)/2; a wide-format
   printer paying out a vinyl banner; an offset press with turning rollers; reams stacked, banners hung
   out front, a board with pages drawn on it */
addShop('printing', {
  look: function (S, F, R) {
    var k = has(F, /ป้าย|ไวนิล|vinyl|sign|อิงค์เจ็ท|inkjet|สติ๊กเกอร์|sticker|advert|ad ?media|โฆษณา|แอดมีเดีย|design/i) ? 'sign' : has(F, /โรงพิมพ์|press|offset|การพิมพ์|printing house/i) ? 'press' : has(F, /ถ่ายเอกสาร|copy|เข้าเล่ม|ปริ้น|print/i) || sub(F, 'copyshop') ? 'copy' : pick(R, ['copy', 'sign', 'press']);
    return { k: k, types: { shop: 3, row: 3, glass: 1 }, light: 'cool', mix: { casual: 0.9, sin: 0.1 } };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 43); L.ban = [pick(R, CLOTHS), pick(R, CLOTHS), pick(R, CLOTHS)]; L.mx = L.in.x0 + (L.in.x1 - L.in.x0) * (0.3 + R() * 0.2); },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 191), w = I.x1 - I.x0;
    shelves(q, I.x1 - Math.min(hh * 0.9, w * 0.35), I.x1 - hh * 0.05, I.y0 + hh * 0.06, d - hh * 0.04, 4, S, function (p, a, b, yb, h) { for (var x = a; x < b - hh * 0.2; x += hh * 0.22) for (var j = 0; j < 3; j++) fr(p, x, yb - (j + 1) * h * 0.28, hh * 0.2, h * 0.26, nt(S, j % 2 ? '#f6f6f2' : '#e8e8e2', 0.2)); });
    for (var i = 0; i < 3; i++) { var bx = I.x0 + hh * (0.15 + i * 0.4); if (bx > I.x1 - hh * 1.3) break; poster(q, bx, I.y0 + hh * 0.05, hh * 0.32, hh * 0.42, S, function (p, x, y, ww, h) { fr(p, x, y, ww, h, L.ban[i % 3]); fe(p, x + ww * 0.5, y + h * 0.35, ww * 0.3, ww * 0.3, 'rgba(255,255,255,.6)'); fr(p, x + ww * 0.15, y + h * 0.72, ww * 0.7, h * 0.08, 'rgba(255,255,255,.8)'); }); }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.mx;
    if (V.k === 'copy') { var u = 0.5 - 0.5 * Math.cos(t / 900); fr(c, x - hh * 0.3, d - hh * 0.62, hh * 0.6, hh * 0.04, '#2a2a2e'); glow(c, x - hh * 0.25 + u * hh * 0.5, d - hh * 0.6, hh * 0.12, '120,255,160', 0.9); fr(c, x - hh * 0.25 + u * hh * 0.5 - 1, d - hh * 0.61, 3, hh * 0.03, '#a8ffc8');
      fig(c, L.ppl[0], x + hh * 0.5, d - hh * 0.02, hh * 0.92, reach(x + hh * 0.5, d - hh * 0.02, hh * 0.92, STANDP, -1, [x + hh * 0.25, d - hh * 0.62], null), -1); }
    else if (V.k === 'sign') { var len = ((t / 9000) % 1) * hh * 0.55; fr(c, x - hh * 0.4, d - hh * 0.45 - 0, hh * 0.8, hh * 0.04, '#f6f6f2'); fr(c, x - hh * 0.38, d - hh * 0.41, hh * 0.76, len, '#f6f6f2'); for (var i = 0; i < 3; i++) fr(c, x - hh * 0.3 + i * hh * 0.25, d - hh * 0.41 + Math.max(0, len - hh * 0.2), hh * 0.18, Math.min(len, hh * 0.18), L.ban[i]);
      fig(c, L.ppl[0], x + hh * 0.75, d - hh * 0.02, hh * 0.92, talk(t, 1), -1); }
    else { for (var r = 0; r < 3; r++) { var rx = x - hh * 0.2 + r * hh * 0.2, ry = d - hh * 0.55, a = t / 200 * (r % 2 ? -1 : 1); fe(c, rx, ry, hh * 0.08, hh * 0.08, '#5a5e66'); ln(c, [[rx, ry], [rx + Math.cos(a) * hh * 0.07, ry + Math.sin(a) * hh * 0.07]], '#c9ccd4', 1.5); }
      fig(c, L.ppl[0], x + hh * 0.55, d - hh * 0.02, hh * 0.92, reach(x + hh * 0.55, d - hh * 0.02, hh * 0.92, STANDP, -1, [x + hh * 0.3, d - hh * 0.4 - Math.abs(Math.sin(t / 600)) * hh * 0.05], null), -1); }
  },
  fore: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, x = L.mx;
    if (V.k === 'copy') { paper(q, rect(x - hh * 0.3, d - hh * 0.58, hh * 0.6, hh * 0.58), nt(S, '#e8e8e2', 0.2), 1.2); fr(q, x - hh * 0.26, d - hh * 0.4, hh * 0.52, hh * 0.05, nt(S, '#9aa0a8', 0.2)); fr(q, x - hh * 0.26, d - hh * 0.25, hh * 0.52, hh * 0.05, nt(S, '#9aa0a8', 0.2)); fr(q, x + hh * 0.3, d - hh * 0.5, hh * 0.15, hh * 0.03, nt(S, '#f6f6f2', 0.2)); }
    else if (V.k === 'sign') { paper(q, rect(x - hh * 0.48, d - hh * 0.62, hh * 0.96, hh * 0.18), nt(S, '#3a3d44', 0.2), 1.2); fr(q, x - hh * 0.44, d - hh * 0.44, hh * 0.04, hh * 0.44, nt(S, '#3a3d44', 0.2)); fr(q, x + hh * 0.4, d - hh * 0.44, hh * 0.04, hh * 0.44, nt(S, '#3a3d44', 0.2)); fr(q, x - hh * 0.4, d - hh * 0.58, hh * 0.3, hh * 0.04, '#7fd8ff'); }
    else { paper(q, rect(x - hh * 0.35, d - hh * 0.45, hh * 0.7, hh * 0.45), nt(S, '#3a5a7a', 0.2), 1.2); fr(q, x - hh * 0.3, d - hh * 0.7, hh * 0.25, hh * 0.25, nt(S, '#f6f6f2', 0.2)); }
  },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, R = rnd(S.seed + 193);
    var bw = Math.min(L.bw * 0.8, hh * 3), bx = (L.bx0 + L.bx1) / 2 - bw / 2, by = d - L.gf - hh * 0.02;
    if (V.k === 'sign' && L.open) for (var bi = 0; bi < 3; bi++) { var vx = L.in.x0 + hh * 0.1 + bi * (L.in.x1 - L.in.x0 - hh * 0.2) / 3, vw = (L.in.x1 - L.in.x0 - hh * 0.2) / 3 - hh * 0.08; if (bi === 1) continue; paper(q, rect(vx, d - L.gf + hh * 0.3, vw, hh * 0.32), nt(S, L.ban[bi], 0.3), 1); fe(q, vx + vw * 0.25, d - L.gf + hh * 0.46, hh * 0.09, hh * 0.09, 'rgba(255,255,255,.7)'); fr(q, vx + vw * 0.45, d - L.gf + hh * 0.4, vw * 0.45, hh * 0.05, 'rgba(255,255,255,.8)'); fr(q, vx + vw * 0.45, d - L.gf + hh * 0.5, vw * 0.35, hh * 0.04, 'rgba(255,255,255,.6)'); }
    var sd = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? L.sides[0] : L.sides[1];
    if (sd.b - sd.a > hh * 0.7 && L.open) { var ax = clamp((sd.a + sd.b) / 2, sd.a + hh * 0.3, sd.b - hh * 0.3); fp(q, [[ax - hh * 0.22, d + hh * 0.12], [ax - hh * 0.16, d - hh * 0.55], [ax + hh * 0.16, d - hh * 0.55], [ax + hh * 0.22, d + hh * 0.12]], nt(S, '#f6f6f2', 0.3));
      if (V.k === 'copy') { for (var pg = 0; pg < 3; pg++) fr(q, ax - hh * 0.08 + pg * hh * 0.03, d - hh * (0.48 - pg * 0.03), hh * 0.12, hh * 0.16, pg === 2 ? '#ffffff' : '#d8dade'); }
      else if (V.k === 'sign') { fr(q, ax - hh * 0.13, d - hh * 0.45, hh * 0.26, hh * 0.14, L.ban[0]); fe(q, ax, d - hh * 0.38, hh * 0.04, hh * 0.04, '#ffffff'); }
      else { for (var cd = 0; cd < 2; cd++) fr(q, ax - hh * 0.1 + cd * hh * 0.04, d - hh * (0.44 - cd * 0.05), hh * 0.16, hh * 0.09, cd ? '#ffffff' : '#c9e0e8'); } }
  }
}, 'the copier\'s light: x = x₀ + A·(1 − cos ωt)/2');

/* busstop: a shelter with its bench and pole, people waiting, and the songthaew or bus that pulls in,
   slows, x = x₀ + (x₁ − x₀)·(1 − cos πu)/2, waits and goes; a terminal with a bus at its bay; a small
   airport with a plane climbing; a station with the train sliding in; a pier with a longtail bobbing */
addShop('busstop', {
  route: function (S, F) { return has(F, /kerry|flash ?(home|express)|j ?& ?t|ไปรษณีย์|shipsmile|\bspx\b|dhl|ems/i) ? 'post' : has(F, /suzuki|toyota|honda|yamaha|อู่|ซ่อม/i) ? 'garage' : null; },
  look: function (S, F, R) {
    var k = sub(F, 'airport') || has(F, /airport|สนามบิน|ท่าอากาศยาน/i) ? 'air' : sub(F, 'train') || has(F, /train|รถไฟ|railway/i) ? 'train' : sub(F, 'pier') || has(F, /pier|ท่าเรือ|boat|เรือ/i) ? 'pier'
      : has(F, /สถานีขนส่ง|terminal|bus station|ขนส่ง|arcade|อาเขต/i) ? 'terminal' : sub(F, 'taxi') || has(F, /taxi|แท็กซี่/i) ? 'taxi' : 'stop';
    var veh = sub(F, 'songthaew') || has(F, /songt?h?aew|สองแถว|รถแดง/i) ? 'songthaew' : k === 'terminal' || R() < 0.4 ? 'bus' : 'songthaew';
    return { k: k, veh: veh, type: 'custom', custom: busStop, noUnit: true, lanterns: 0, bikes: 0, w: k === 'stop' || k === 'taxi' ? 2.6 + R() * 1.2 : 5 + R() * 1, mix: { casual: 0.7, sin: 0.18, mohom: 0.12 },
      col: veh === 'bus' ? pick(R, ['#2f8a5a', '#2f5fb0', '#e8a33a', '#f2f2f2']) : F.province === 'cr' ? pick(R, ['#2f6fb0', '#e8b84a', '#2f9a5a']) : '#c0392b' };
  },
  plan: function (S, L, V, R) {
    var hh = S.hh, d = S.deck; L.wait = crew(S, 5, V.mix, 45); L.animal = R() < 0.4 ? 'dog' : 'none'; L.walkers = Math.min(1, L.walkers);
    L.top = V.k === 'stop' || V.k === 'taxi' ? d - hh * 1.5 : d - hh * 2.2; L.signAt = 'face'; L.signY = (V.k === 'stop' || V.k === 'taxi' ? L.top : d - L.gf - hh * 0.3) - L.sg.h - hh * 0.05;
    if (V.k === 'air' || V.k === 'train' || V.k === 'terminal') L.signY = d - L.gf - L.sg.h - hh * 0.08;
    L.stopX = L.bx0 + L.bw * 0.5; var big = V.k === 'air' || V.k === 'train' || V.k === 'terminal'; L.shelter = [L.stopX - hh * (big ? 0.95 : 1.0), L.stopX + hh * (big ? 0.35 : 0.45)]; L.waitX = (L.shelter[0] + L.shelter[1]) / 2 + hh * 0.3; L.spirit = L.spirit && !L.spirit.front ? L.spirit : null;
  },
  street: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, k = V.k, i;
    if (k === 'air') { var u = (t / 16000) % 1; if (u < 0.6) { var p = u / 0.6, px = lerp(S.x0 - hh, S.x1 + hh, p), py = d - hh * (0.6 + p * p * 2.2); c.save(); c.translate(px, py); c.rotate(-0.25 * Math.min(1, p * 3)); fe(c, 0, 0, hh * 0.55, hh * 0.08, '#f2f2f2'); fp(c, [[-hh * 0.1, 0], [hh * 0.12, 0], [-hh * 0.15, hh * 0.25]], '#d8dade'); fp(c, [[-hh * 0.45, 0], [-hh * 0.55, -hh * 0.22], [-hh * 0.42, -hh * 0.02]], V.col); for (i = 0; i < 6; i++) fe(c, -hh * 0.25 + i * hh * 0.08, -hh * 0.015, hh * 0.015, hh * 0.015, '#3a6fb0'); c.restore(); } }
    if (k === 'pier') { var bob = Math.sin(t / 700) * hh * 0.03, bx = L.bx0 + L.bw * 0.6; fp(c, [[bx - hh * 1.0, d + hh * 0.3 + bob], [bx + hh * 0.9, d + hh * 0.3 + bob], [bx + hh * 1.2, d + hh * 0.12 + bob], [bx + hh * 0.85, d + hh * 0.42 + bob], [bx - hh * 0.9, d + hh * 0.42 + bob]], '#8a4a2a'); fr(c, bx - hh * 0.95, d + hh * 0.3 + bob, hh * 1.85, hh * 0.03, '#e8b84a'); fr(c, bx - hh * 0.6, d + hh * 0.06 + bob, hh * 1.1, hh * 0.04, '#d9342b'); ln(c, [[bx - hh * 0.95, d + hh * 0.3 + bob], [bx - hh * 1.2, d + hh * 0.2 + bob]], '#5a5e66', 2); }
    if (k === 'train') { var u2 = (t / 18000) % 1, tx = u2 < 0.35 ? lerp(S.x1 + hh * 6, L.bx0 + hh * 0.5, ease(u2 / 0.35)) : u2 < 0.7 ? L.bx0 + hh * 0.5 : lerp(L.bx0 + hh * 0.5, S.x0 - hh * 8, ease((u2 - 0.7) / 0.3));
      for (i = 0; i < 3; i++) { var cx = tx + i * hh * 2.1; if (cx > S.x1 + hh || cx + hh * 2 < S.x0 - hh) continue; fr(c, cx, d - hh * 0.8 + hh * 0.2, hh * 2.0, hh * 0.72, i ? '#8a2a2a' : '#2f4f8a'); fr(c, cx, d - hh * 0.4 + hh * 0.2, hh * 2.0, hh * 0.1, '#f2e6c9'); for (var w = 0; w < 5; w++) fr(c, cx + hh * (0.12 + w * 0.38), d - hh * 0.7 + hh * 0.2, hh * 0.26, hh * 0.2, S.night ? '#ffe2a0' : '#bfe0f0'); fe(c, cx + hh * 0.4, d + hh * 0.18, hh * 0.1, hh * 0.1, '#1a1a1a'); fe(c, cx + hh * 1.6, d + hh * 0.18, hh * 0.1, hh * 0.1, '#1a1a1a'); } }
    /* the people waiting: one on the bench with a phone, one standing, one with shopping */
    var bx0 = L.waitX - hh * 0.6, leave = (k === 'stop' || k === 'terminal' || k === 'taxi') && ((t / 14000) % 1) > 0.48 && ((t / 14000) % 1) < 0.65;
    var me = fig(c, L.wait[0], bx0, d + hh * 0.02, hh * 0.86, { lean: 0.15, seat: 0.3, legs: [1.45, -1.45, 1.38, -1.4], arms: [1.1, 0.9, 1.0, 1.0] }, 1);
    glow(c, me.hand[0][0], me.hand[0][1] - hh * 0.02, hh * 0.1, '190,225,255', S.night ? 0.9 : 0.4);
    fig(c, L.wait[1], bx0 + hh * 0.55, d + hh * 0.02, hh * 0.86, sitTalk(t, 2), 1);
    if (!leave) { var sx = L.waitX + hh * 0.75; var m2 = fig(c, L.wait[2], sx, d + hh * 0.16, hh * 0.94, reach(sx, d + hh * 0.16, hh * 0.94, STANDP, 1, null, null), -1); var hd = m2.hand[1]; fp(c, [[hd[0] - hh * 0.06, hd[1]], [hd[0] + hh * 0.06, hd[1]], [hd[0] + hh * 0.07, hd[1] + hh * 0.14], [hd[0] - hh * 0.07, hd[1] + hh * 0.14]], '#f2f2ee'); }
    if (k === 'stop' || k === 'terminal' || k === 'taxi') {   /* the ride that pulls in, waits and goes */
      var u3 = (t / 14000) % 1, stopAt = L.waitX + hh * (k === 'terminal' ? 0.3 : 0.2), vx;
      if (u3 < 0.35) vx = lerp(S.x1 + hh * 2.8, stopAt, 1 - Math.pow(1 - u3 / 0.35, 2)); else if (u3 < 0.65) vx = stopAt; else vx = lerp(stopAt, S.x0 - hh * 3, Math.pow((u3 - 0.65) / 0.35, 2));
      var kind = k === 'taxi' ? 'sedan' : V.veh, spr = sprite(S, 'ride-' + kind + V.col, hh * 6, hh * 1.1, function (q) { car(q, hh * 3, hh * 1.08, hh * 0.95, kind, k === 'taxi' ? '#f2c94c' : V.col, -1, S); });
      if (spr) c.drawImage(spr, vx - hh * 3, d + hh * 0.6 - hh * 1.08, hh * 6, hh * 1.1);
    }
  }
}, 'the ride slows in: x = x₁ − (x₁ − x₀)(1 − u)²');
function busStop(q, S, L) {
  var V = L.V, hh = S.hh, d = S.deck, x0 = L.bx0, x1 = L.bx1, R = rnd(S.seed + 201), k = V.k, x;
  if (k === 'air' || k === 'train' || k === 'terminal') {
    var wall = nt(S, k === 'train' ? '#f2e6c9' : '#e8eaee', 0.45), roof = nt(S, k === 'train' ? '#8a3b2a' : '#6a6a72', 0.45), top = d - L.gf - hh * 0.32;
    if (k === 'train') { paper(q, poly([[x0 - hh * 0.3, top + hh * 0.05], [x0 + hh * 0.4, L.top + hh * 0.2], [x1 - hh * 0.4, L.top + hh * 0.2], [x1 + hh * 0.3, top + hh * 0.05]]), roof, 1.6); kalae(q, (x0 + x1) / 2, L.top + hh * 0.22, hh * 0.16, nt(S, '#d9a53c', 0.35)); }
    else if (k === 'air') { var tx2 = x1 - hh * 0.4; paper(q, rect(tx2 - hh * 0.1, L.top + hh * 0.3, hh * 0.2, d - L.top - hh * 0.3), wall, 1.4); paper(q, rect(tx2 - hh * 0.25, L.top + hh * 0.05, hh * 0.5, hh * 0.28), nt(S, '#3a5a7a', 0.4), 1.4); }
    paper(q, rect(x0, top, x1 - x0, d - top), wall, 1.6);
    for (x = x0 + hh * 0.2; x < x1 - hh * 0.2; x += hh * 0.45) fr(q, x, d - L.gf + hh * 0.2, hh * 0.32, L.gf - hh * 0.3, S.night ? '#ffe2a0' : nt(S, '#8fb4c4', 0.4));
    fr(q, x0, top, x1 - x0, hh * 0.1, k === 'terminal' ? nt(S, V.col, 0.4) : roof);
    if (k === 'terminal') { paper(q, rect(x0 - hh * 0.2, d - L.gf + hh * 0.05, x1 - x0 + hh * 0.4, hh * 0.1), nt(S, '#c9ccd4', 0.4), 1.3); for (x = x0; x <= x1; x += (x1 - x0) / 4) fr(q, x - 2, d - L.gf + hh * 0.15, 4, L.gf - hh * 0.15, nt(S, '#9aa0a8', 0.4)); }
    if (k === 'pier') return;
  }
  if (k === 'pier') { paper(q, rect(x0, d - hh * 0.06, x1 - x0, hh * 0.1), nt(S, '#8a5a32', 0.4), 1.2); for (x = x0; x < x1; x += hh * 0.4) fr(q, x, d, hh * 0.06, hh * 0.5, nt(S, '#6b4226', 0.4)); }
  /* the shelter: a curved roof on two posts, a panel behind, the bench, the pole */
  var sx0 = L.shelter[0], sx1 = L.shelter[1], st = d - hh * 1.4;
  fr(q, sx0 + hh * 0.05, st + hh * 0.15, sx1 - sx0 - hh * 0.1, hh * 0.85, k === 'stop' || k === 'taxi' || k === 'pier' ? 'rgba(190,225,235,.4)' : 'rgba(0,0,0,0)');
  if (k === 'stop' || k === 'taxi' || k === 'pier') { var pc = nt(S, pick(R, ['#e8a33a', '#2f8a5a', '#3a6fb0', '#c0392b']), 0.35); fr(q, sx0 + hh * 0.1, st + hh * 0.2, hh * 0.5, hh * 0.65, pc); fe(q, sx0 + hh * 0.35, st + hh * 0.45, hh * 0.12, hh * 0.12, 'rgba(255,255,255,.5)'); }
  [sx0 + hh * 0.05, sx1 - hh * 0.05].forEach(function (px) { paper(q, rect(px - hh * 0.03, st, hh * 0.06, d - st), nt(S, '#9aa0a8', 0.4), 1.1); });
  paper(q, function (p) { p.beginPath(); p.moveTo(sx0 - hh * 0.1, st + hh * 0.05); p.quadraticCurveTo((sx0 + sx1) / 2, st - hh * 0.2, sx1 + hh * 0.1, st + hh * 0.05); p.lineTo(sx1 + hh * 0.1, st + hh * 0.12); p.quadraticCurveTo((sx0 + sx1) / 2, st - hh * 0.12, sx0 - hh * 0.1, st + hh * 0.12); p.closePath(); }, nt(S, pick(R, ['#2f5fb0', '#2f8a5a', '#c0392b', '#6a6a72']), 0.4), 1.5);
  fr(q, sx0 + hh * 0.1, d - hh * 0.3, sx1 - sx0 - hh * 0.2, hh * 0.05, nt(S, '#8a6a4a', 0.35)); fr(q, sx0 + hh * 0.15, d - hh * 0.25, hh * 0.04, hh * 0.25, nt(S, '#5a5e66', 0.35)); fr(q, sx1 - hh * 0.2, d - hh * 0.25, hh * 0.04, hh * 0.25, nt(S, '#5a5e66', 0.35));
  var px2 = sx1 + hh * 0.2; fr(q, px2 - 1.5, d - hh * 1.25, 3, hh * 1.37, nt(S, '#9aa0a8', 0.4)); fe(q, px2, d - hh * 1.28, hh * 0.14, hh * 0.14, nt(S, '#2f5fb0', 0.3)); fe(q, px2, d - hh * 1.28, hh * 0.1, hh * 0.1, '#f6f6f2');
  fr(q, px2 - hh * 0.06, d - hh * 1.31, hh * 0.12, hh * 0.05, nt(S, V.col, 0.3)); fe(q, px2 - hh * 0.03, d - hh * 1.25, hh * 0.012, hh * 0.012, '#1a1a1a'); fe(q, px2 + hh * 0.03, d - hh * 1.25, hh * 0.012, hh * 0.012, '#1a1a1a');
  if (S.night) glow(q, (sx0 + sx1) / 2, st + hh * 0.3, hh * 0.9, '255,236,190', 0.4);
}

/* post: the red pillar box at the door, the counter with its scale (the needle settles,
   θ = θ₀·e^(−λt)·cos ωt), boxes of every size, a parcel handed over; a courier's shophouse in its
   colour, parcels to the ceiling, the scanner's red line, a rider loading up */
var COURIER = [[/kerry/i, '#f26a1f'], [/flash/i, '#f2c400'], [/j ?& ?t/i, '#d9242b'], [/\bspx\b|shopee/i, '#ee4d2d'], [/dhl/i, '#f2c400'], [/nim|นิ่ม/i, '#1f5fb0'], [/shipsmile/i, '#2f9ad0'], [/best|เบสท์/i, '#d9242b']];
addShop('post', {
  look: function (S, F, R) {
    var tint = null; for (var i = 0; i < COURIER.length; i++) if (has(F, COURIER[i][0])) { tint = COURIER[i][1]; break; }
    var k = tint ? 'courier' : has(F, /ไปรษณีย์|post office|thailand post|ปณ\./i) || R() < 0.6 ? 'thai' : 'courier';
    tint = tint || (k === 'thai' ? '#c8201e' : pick(R, ['#f26a1f', '#2f9ad0', '#2f8a5a']));
    return { k: k, tint: tint, board: k === 'thai' ? '#a81a18' : tint, light: 'cool', types: k === 'thai' ? { shop: 2, glass: 2, row: 1 } : { shop: 3, row: 3 }, mix: { casual: 0.8, sin: 0.12, mohom: 0.08 },
      wallArt: function (q, S, L) { fr(q, L.bx0, S.deck - L.gf - S.hh * 0.12, L.bw, S.hh * 0.06, nt(S, tint, 0.35)); } };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 4, V.mix, 47); uni(L.ppl[0], V.k === 'thai' ? '#f2f2ee' : V.tint, '#2c2f45'); uni(L.ppl[3], V.tint, '#2c2f45'); L.ppl[3].hair = 4; var sd = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? 0 : 1; L.boxX = sd ? L.bx1 + S.hh * 0.3 : L.bx0 - S.hh * 0.3; if (L.spirit && Math.abs(L.spirit.x - L.boxX) < S.hh * 0.6) L.spirit = null; L.bikeX = sd ? L.bx0 + S.hh * 0.55 : L.bx1 - S.hh * 0.55; L.bikes = []; L.ct = L.in.x0 + (L.in.x1 - L.in.x0) * 0.45; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 211), w = I.x1 - I.x0, card = ['#c9a06a', '#b8905a', '#d8b27a'];
    if (V.k === 'thai') shelves(q, I.x0 + hh * 0.06, I.x0 + Math.max(hh * 0.9, w * 0.35), I.y0 + hh * 0.06, d - hh * 0.04, 4, S, function (p, a, b, yb, h, r) { for (var x = a; x < b - hh * 0.1; x += hh * (0.12 + r * 0.05)) fr(p, x, yb - h * (0.3 + r * 0.15), hh * (0.1 + r * 0.05), h * (0.3 + r * 0.15), nt(S, pick(R, card), 0.2)); });
    else { for (var x = I.x0 + hh * 0.08; x < I.x1 - hh * 0.1; x += hh * 0.24) { var hgt = hh * (0.4 + R() * 0.6); for (var y = d; y > d - hgt; y -= hh * 0.16) paper(q, rect(x + (R() - 0.5) * 4, y - hh * 0.15, hh * 0.22, hh * 0.15), nt(S, pick(R, card), 0.2), 0.5); } }
    fr(q, I.x0, I.y0 + hh * 0.02, w, hh * 0.06, nt(S, V.tint, 0.2));
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.ct;
    fig(c, L.ppl[0], x - hh * 0.25, d - hh * 0.02, hh * 0.9, reach(x - hh * 0.25, d - hh * 0.02, hh * 0.9, STANDP, 1, [x + hh * 0.1, d - hh * 0.55], null), 1);
    var u = (t / 6000) % 1, held = u < 0.4, px = held ? x + hh * 0.45 : x + hh * 0.12;
    fig(c, L.ppl[1], x + hh * 0.62, d - hh * 0.02, hh * 0.92, reach(x + hh * 0.62, d - hh * 0.02, hh * 0.92, STANDP, -1, held ? [x + hh * 0.42, d - hh * 0.62] : [x + hh * 0.4, d - hh * 0.5], null), -1);
    paper(c, rect(px - hh * 0.1, d - hh * (held ? 0.72 : 0.62), hh * 0.2, hh * 0.14), '#c9a06a', 0.5);
    if (V.k === 'courier') { var sy = d - hh * 0.6; c.strokeStyle = 'rgba(255,40,40,' + (0.5 + 0.4 * Math.sin(t / 90)).toFixed(2) + ')'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(x - hh * 0.05, sy); c.lineTo(x + hh * 0.1, sy + hh * 0.08); c.stroke(); }
  },
  fore: function (q, S, L, V) { var hh = S.hh, d = S.deck, x = L.ct; counter(q, x - hh * 0.05, x + hh * 0.45, d - hh * 0.45, S, V.k === 'thai' ? '#d8d2c4' : V.tint); if (V.k === 'thai') { fr(q, x + hh * 0.05, d - hh * 0.5, hh * 0.24, hh * 0.05, nt(S, '#c9ccd4', 0.2)); fe(q, x + hh * 0.17, d - hh * 0.56, hh * 0.06, hh * 0.05, nt(S, '#f2f2ee', 0.2)); } },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, x = L.boxX;
    if (V.k === 'thai' && x > S.x0 + hh * 0.5 && x < S.x1 - hh * 0.5) { paper(q, function (p) { p.beginPath(); p.moveTo(x - hh * 0.15, d + hh * 0.12); p.lineTo(x - hh * 0.15, d - hh * 0.65); p.quadraticCurveTo(x, d - hh * 0.82, x + hh * 0.15, d - hh * 0.65); p.lineTo(x + hh * 0.15, d + hh * 0.12); p.closePath(); }, nt(S, '#d9241b', 0.3), 1.4);
      fr(q, x - hh * 0.1, d - hh * 0.55, hh * 0.2, hh * 0.03, '#1a1a1a'); fr(q, x - hh * 0.17, d - hh * 0.06, hh * 0.34, hh * 0.05, nt(S, '#8a1a18', 0.3)); fe(q, x, d - hh * 0.35, hh * 0.06, hh * 0.06, nt(S, '#f2f2ee', 0.3)); }
    if (L.open) { scooter(q, L.bikeX, d + hh * 0.17, hh * 0.92, V.k === 'thai' ? '#d9241b' : V.tint, 1, S); paper(q, rect(L.bikeX - hh * 0.62, d - hh * 0.72, hh * 0.32, hh * 0.3), nt(S, V.k === 'thai' ? '#d9241b' : V.tint, 0.3), 1); }
  },
  street: function (S, L, V) {
    if (!L.open) return; var c = S.c, hh = S.hh, d = S.deck, t = S.t, u = (t / 8000) % 1, from = (L.in.x0 + L.in.x1) / 2, to = L.bikeX - hh * 0.2, p = u < 0.5 ? u * 2 : 2 - u * 2, x = lerp(from, to, ease(p)), dir = (to > from) === (u < 0.5) ? 1 : -1;
    var me = fig(c, L.ppl[3], x, d + hh * 0.16, hh * 0.92, u < 0.5 ? reach(x, d + hh * 0.16, hh * 0.92, K.walkP(t / 1000 * TAU, false), dir, [x + dir * hh * 0.2, d - hh * 0.5], [x + dir * hh * 0.18, d - hh * 0.46]) : K.walkP(t / 1000 * TAU, false), dir);
    if (u < 0.5) paper(c, rect(x + dir * hh * 0.1 - (dir < 0 ? hh * 0.22 : 0), d - hh * 0.62, hh * 0.22, hh * 0.17), '#c9a06a', 0.5);
  }
}, 'the scale settles: θ = θ₀·e<sup>−λt</sup>·cos ωt');

/* secondhand: racks of old jackets and denim, bales tied up, someone sorting a pile; a buyer of old
   things with the hanging scale (it swings, θ = θ₀·cos ωt), bundled cardboard, sacks of bottles and a
   saleng cart heaped high; old guitars; radios, a gramophone and clocks whose pendulums swing */
addShop('secondhand', {
  look: function (S, F, R) {
    var k = has(F, /รับซื้อ|ของเก่า|recycl|รีไซเคิล|เศษ|scrap|ขยะ/i) ? 'scrap' : sub(F, 'music') || has(F, /ดนตรี|music|กีตาร์|guitar/i) ? 'music' : has(F, /antique|โบราณ|วินเทจ|vintage|collect|เฟอร์นิเจอร์|furniture|ของสะสม/i) ? 'antique' : has(F, /เสื้อผ้า|clothes|กระสอบ|bale|ญี่ปุ่น|เสื้อ/i) ? 'clothes' : pick(R, ['clothes', 'antique', 'scrap', 'clothes']);
    return { k: k, types: k === 'scrap' ? { stall: 3, row: 2 } : { shop: 2, row: 3, stall: 1.5, teak: 0.8 }, light: 'warm', mix: { casual: 0.85, sin: 0.1, mohom: 0.05 }, bikes: k === 'scrap' ? 0 : null };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 49); L.pal = ['#3a5a8a', '#6a5a3a', '#8a3a2a', '#4a6a4a', '#2a3a5a', '#a88a5a', '#7a2a3a']; L.work = L.in.x0 + (L.in.x1 - L.in.x0) * 0.55; },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 221), w = I.x1 - I.x0, k = V.k, i, x;
    if (k === 'clothes') { rail(q, I.x0 + hh * 0.08, I.x1 - hh * 0.08, I.y0 + hh * 0.08, hh * 0.9, S, R, ['jacket', 'shirt', 'pants', 'jacket'], L.pal);
      for (i = 0; i < 3; i++) { var bx = I.x0 + hh * (0.3 + i * 0.5); if (bx > I.x1 - hh * 0.3) break; paper(q, rect(bx - hh * 0.22, d - hh * 0.42, hh * 0.44, hh * 0.42), nt(S, pick(R, ['#d8d2c4', '#c9c4b8', '#b8b4aa']), 0.2), 1); ln(q, [[bx - hh * 0.22, d - hh * 0.25], [bx + hh * 0.22, d - hh * 0.25]], '#3a2a22', 1.5); ln(q, [[bx, d - hh * 0.42], [bx, d]], '#3a2a22', 1.5); } }
    else if (k === 'music') { for (i = 0; i < Math.floor(w / (hh * 0.32)); i++) guitar(q, I.x0 + hh * 0.22 + i * hh * 0.32, I.y0 + hh * 0.2, hh * 0.9, pick(R, ['#c9853a', '#8a3b2a', '#2a2a2a', '#6a4a2a', '#f2e6c9']), S); for (i = 0; i < 2; i++) { var ax = I.x1 - hh * (0.35 + i * 0.4); paper(q, rect(ax - hh * 0.17, d - hh * 0.4, hh * 0.34, hh * 0.4), nt(S, '#2a2a2a', 0.2), 1); fe(q, ax, d - hh * 0.22, hh * 0.1, hh * 0.1, nt(S, '#5a5e66', 0.2)); } }
    else if (k === 'antique') { shelves(q, I.x0 + hh * 0.06, I.x1 - hh * 0.06, I.y0 + hh * 0.06, d - hh * 0.5, 2, S, function (p, a, b, yb, h) { for (var xx = a + hh * 0.05; xx < b - hh * 0.25; xx += hh * 0.3) { var r2 = R(); if (r2 < 0.4) { fr(p, xx, yb - h * 0.6, hh * 0.24, h * 0.6, nt(S, '#8a5a32', 0.2)); fe(p, xx + hh * 0.07, yb - h * 0.3, hh * 0.04, hh * 0.04, nt(S, '#2a2a2a', 0.2)); fr(p, xx + hh * 0.13, yb - h * 0.45, hh * 0.08, h * 0.3, nt(S, '#c9a878', 0.2)); } else if (r2 < 0.7) { fp(p, [[xx + hh * 0.05, yb], [xx + hh * 0.19, yb], [xx + hh * 0.15, yb - h * 0.5], [xx + hh * 0.09, yb - h * 0.5]], nt(S, '#c9a83a', 0.2)); fp(p, [[xx, yb - h * 0.5], [xx + hh * 0.24, yb - h * 0.5], [xx + hh * 0.18, yb - h * 0.85], [xx + hh * 0.06, yb - h * 0.85]], nt(S, '#e8d8b0', 0.2)); } else { fe(p, xx + hh * 0.12, yb - h * 0.4, hh * 0.12, h * 0.38, nt(S, pick(R, ['#3a6a5a', '#8a3a2a', '#2a3a5a']), 0.2)); } } }); }
    else { for (i = 0; i < 4; i++) { var cx = I.x0 + hh * (0.25 + i * 0.32); if (cx > I.x1 - hh * 0.2) break; for (var j = 0; j < 4; j++) paper(q, rect(cx - hh * 0.14, d - hh * (0.12 + j * 0.11), hh * 0.28, hh * 0.1), nt(S, '#b8905a', 0.2), 0.5); }
      for (i = 0; i < 2; i++) { var sx = I.x1 - hh * (0.3 + i * 0.42); paper(q, function (p) { p.beginPath(); p.ellipse(sx, d - hh * 0.25, hh * 0.18, hh * 0.25, 0, 0, TAU); }, 'rgba(220,235,240,.75)', 0.8); for (j = 0; j < 6; j++) fe(q, sx + (R() - 0.5) * hh * 0.2, d - hh * (0.1 + R() * 0.3), hh * 0.035, hh * 0.06, 'rgba(160,200,220,.9)'); } }
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, I = L.in, x = L.work, k = V.k;
    if (k === 'antique') { for (var i = 0; i < 2; i++) { var cx = I.x0 + hh * (0.4 + i * 0.6), cy = d - hh * 0.48, th = 0.35 * Math.cos(t / 600 + i); fr(c, cx - hh * 0.1, cy - hh * 0.1, hh * 0.2, hh * 0.48, '#6a4a2a'); clock(c, cx, cy, hh * 0.07, S.now); ln(c, [[cx, cy + hh * 0.1], [cx + Math.sin(th) * hh * 0.2, cy + hh * 0.1 + Math.cos(th) * hh * 0.2]], '#c9a83a', 1); fe(c, cx + Math.sin(th) * hh * 0.2, cy + hh * 0.1 + Math.cos(th) * hh * 0.2, hh * 0.03, hh * 0.03, '#d9b84a'); }
      fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.88, sitTalk(t, 1), -1); return; }
    if (k === 'scrap') { var hx = x, hy = I.y0 + hh * 0.05, th2 = 0.2 * Math.cos(t / 500); ln(c, [[hx, hy], [hx + Math.sin(th2) * hh * 0.25, hy + Math.cos(th2) * hh * 0.25]], '#5a5e66', 1.5); var ex = hx + Math.sin(th2) * hh * 0.25, ey = hy + Math.cos(th2) * hh * 0.25;
      fe(c, ex, ey + hh * 0.06, hh * 0.07, hh * 0.07, '#d8d2c4'); ln(c, [[ex, ey + hh * 0.06], [ex + Math.sin(t / 300) * hh * 0.05, ey + hh * 0.02]], '#d9342b', 1); ln(c, [[ex, ey + hh * 0.13], [ex, ey + hh * 0.25]], '#5a5e66', 1.5); fr(c, ex - hh * 0.12, ey + hh * 0.25, hh * 0.24, hh * 0.14, '#b8905a');
      fig(c, L.ppl[0], hx - hh * 0.35, d - hh * 0.02, hh * 0.9, reach(hx - hh * 0.35, d - hh * 0.02, hh * 0.9, STANDP, 1, [ex - hh * 0.1, ey + hh * 0.28], null), 1); return; }
    var lift = Math.abs(Math.sin(t / 700)); var me = fig(c, L.ppl[0], x, d - hh * 0.02, hh * 0.9, reach(x, d - hh * 0.02, hh * 0.9, { lean: 0.45, legs: [0.2, -0.2, -0.1, 0], arms: [1, 0.5, 1, 0.5] }, 1, [x + hh * 0.25, d - hh * (0.3 + lift * 0.3)], [x + hh * 0.3, d - hh * (0.32 + lift * 0.28)]), 1);
    if (k === 'clothes') fp(c, [[x + hh * 0.2, d - hh * (0.3 + lift * 0.3)], [x + hh * 0.38, d - hh * (0.3 + lift * 0.3)], [x + hh * 0.36, d - hh * (0.05 + lift * 0.3)], [x + hh * 0.22, d - hh * (0.05 + lift * 0.3)]], L.pal[Math.floor(t / 1400) % 7]);
    else K.notes(c, x + hh * 0.3, d - hh * 0.7, t, 2, '#f2c94c');
  },
  fore: function (q, S, L, V) { var hh = S.hh, d = S.deck, x = L.work, R = rnd(S.seed + 223); if (V.k === 'clothes') for (var i = 0; i < 12; i++) fe(q, x + hh * (0.35 + R() * 0.4), d - hh * (0.04 + R() * 0.16), hh * 0.1, hh * 0.05, nt(S, pick(R, L.pal), 0.2), R()); },
  out: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, sd = L.sides[0].b - L.sides[0].a > L.sides[1].b - L.sides[1].a ? L.sides[0] : L.sides[1];
    if (V.k === 'scrap' && sd.b - sd.a > hh * 1.3) { var sx = (sd.a + sd.b) / 2; scooter(q, sx + hh * 0.35, d + hh * 0.17, hh * 0.9, '#3a5a8a', -1, S); fr(q, sx - hh * 0.65, d - hh * 0.3, hh * 0.75, hh * 0.25, nt(S, '#5a6a4a', 0.35)); wheel(q, sx - hh * 0.3, d + hh * 0.17, hh * 0.1, S);
      var R = rnd(S.seed + 225); for (var i = 0; i < 9; i++) paper(q, rect(sx - hh * 0.62 + (i % 3) * hh * 0.24, d - hh * (0.45 + Math.floor(i / 3) * 0.13), hh * 0.22, hh * 0.13), nt(S, pick(R, ['#b8905a', '#9aa0a8', '#d8d2c4', '#3a6fb0']), 0.35), 0.5); }
    if (V.k === 'clothes' && L.open && sd.b - sd.a > hh * 0.9) { var rx0 = sd.a + hh * 0.1; ln(q, [[rx0, d + hh * 0.12], [rx0, d - hh * 0.95], [rx0 + hh * 0.75, d - hh * 0.95], [rx0 + hh * 0.75, d + hh * 0.12]], nt(S, '#9aa0a8', 0.35), 2); L.rackAt = [rx0, rx0 + hh * 0.75, d - hh * 0.95]; }
  },
  street: function (S, L, V) { if (!L.rackAt || !L.open) return; var c = S.c, hh = S.hh, t = S.t, R = rnd(S.seed + 227); for (var x = L.rackAt[0] + hh * 0.1, k = 0; x < L.rackAt[1] - hh * 0.05; x += hh * 0.14, k++) { c.save(); c.translate(x, L.rackAt[2]); c.rotate(0.06 * Math.sin(t / 900 + k * 0.7)); garment(c, 0, 0, hh * 0.85, pick(R, ['jacket', 'shirt']), pick(R, L.pal), S); c.restore(); } }
}, 'the hanging scale: θ = θ₀·cos ωt');

/* pets: a vet in scrubs at the steel table with a dog whose tail wags, θ = θ₀·sin ωt; a groomer
   washing a dog in a tub of bubbles that rise and pop; tanks of fish swimming, x = x₀ + A·sin ωt, birds
   in cages, a cat in a box; a paw drawn on the board */
function dogStand(c, x, y, s, col, t, k, dir) {
  var dk = mixc(col, '#000000', 0.3), w = Math.sin(t / 120 + k) * 0.7, X = function (u) { return x + dir * u * s; };
  [-0.12, -0.06, 0.08, 0.14].forEach(function (u) { ln(c, [[X(u), y - s * 0.16], [X(u), y]], col, Math.max(1.5, s * 0.035)); });
  fe(c, x, y - s * 0.2, s * 0.17, s * 0.08, col);
  c.strokeStyle = col; c.lineWidth = Math.max(1.5, s * 0.03); c.lineCap = 'round'; c.beginPath(); c.moveTo(X(-0.16), y - s * 0.22); c.lineTo(X(-0.16 - Math.cos(w) * 0.1), y - s * (0.24 + Math.abs(Math.sin(w + 0.8)) * 0.1)); c.stroke();
  fe(c, X(0.19), y - s * 0.3, s * 0.07, s * 0.06, col); fe(c, X(0.25), y - s * 0.28, s * 0.04, s * 0.03, col); fe(c, X(0.16), y - s * 0.33, s * 0.025, s * 0.045, dk, -0.3 * dir); fe(c, X(0.21), y - s * 0.31, s * 0.01, s * 0.01, '#1a1a1a'); fe(c, X(0.29), y - s * 0.285, s * 0.012, s * 0.01, '#1a1a1a');
}
function paw(q, x, y, s, col) { fe(q, x, y + s * 0.15, s * 0.32, s * 0.26, col); [[-0.32, -0.18], [-0.12, -0.36], [0.12, -0.36], [0.32, -0.18]].forEach(function (p) { fe(q, x + p[0] * s, y + p[1] * s, s * 0.12, s * 0.15, col); }); }
addShop('pets', {
  look: function (S, F, R) {
    var k = sub(F, 'vet') || has(F, /คลินิก|vet|สัตว์แพทย์|โรงพยาบาลสัตว์|animal hospital|clinic|รักษาสัตว์/i) ? 'vet' : sub(F, 'grooming') || has(F, /อาบน้ำ|ตัดขน|groom|spa|สปา/i) ? 'groom' : has(F, /ปลา|fish|aqua|ตู้ปลา/i) ? 'fish' : sub(F, 'pet-shop') ? pick(R, ['shop', 'fish']) : pick(R, ['shop', 'groom']);
    return { k: k, light: 'cool', inWall: k === 'vet' ? '#eef6f6' : null, types: k === 'vet' ? { glass: 3, shop: 3 } : { shop: 3, row: 2.5, glass: 1 }, mix: { casual: 0.85, sin: 0.15 }, pawCol: pick(R, ['#2f8a7a', '#e5567f', '#3a6fb0', '#f08a3a']) };
  },
  plan: function (S, L, V, R) { L.ppl = crew(S, 3, V.mix, 51); if (V.k === 'vet') uni(L.ppl[0], '#5ab8b0', '#3a8a84'); if (V.k === 'groom') uni(L.ppl[0], '#e5567f', '#2c2f45'); L.dogCol = pick(R, DOGS); L.dog2 = pick(R, DOGS); L.fish = []; for (var i = 0; i < 12; i++) L.fish.push([R(), R(), pick(R, ['#f08a3a', '#f2c94c', '#e5567f', '#7fd8ff', '#ffffff', '#d9342b'])]); L.tanks = null; if (V.k === 'fish' || V.k === 'shop') { var I = L.in, hh = S.hh, d = S.deck, tx1 = V.k === 'fish' ? I.x1 - hh * 0.06 : I.x0 + (I.x1 - I.x0) * 0.5; L.tanks = []; for (var r = 0; r < 2; r++) for (var x = I.x0 + hh * 0.06; x < tx1 - hh * 0.3; x += hh * 0.36) L.tanks.push([x, d - hh * (0.45 + r * 0.42)]); } L.work = L.in.x0 + (L.in.x1 - L.in.x0) * 0.42; L.pawX = L.bx0 + S.hh * 0.32; L.pawY = S.deck - L.gf - S.hh * 0.3; if (L.signAt !== 'stand' && Math.abs(L.pawX - L.signX) < L.sg.w / 2 + S.hh * 0.25) { L.pawX = L.bx1 - S.hh * 0.32; if (Math.abs(L.pawX - L.signX) < L.sg.w / 2 + S.hh * 0.25) L.pawY = S.deck - L.gf + S.hh * (L.awn === 'none' ? 0.35 : 0.55); } },
  back: function (q, S, L, V) {
    var I = L.in, hh = S.hh, d = S.deck, R = rnd(S.seed + 231), w = I.x1 - I.x0, k = V.k, x, i;
    if (k === 'fish' || k === 'shop') {
      L.tanks.forEach(function (tk) { var x = tk[0], ty = tk[1], i; fr(q, x, ty, hh * 0.33, hh * 0.32, nt(S, '#5aa8d0', 0.2)); fr(q, x, ty, hh * 0.33, hh * 0.04, 'rgba(255,255,255,.4)'); for (i = 0; i < 3; i++) fp(q, [[x + hh * (0.04 + i * 0.1), ty + hh * 0.32], [x + hh * (0.06 + i * 0.1), ty + hh * 0.18], [x + hh * (0.08 + i * 0.1), ty + hh * 0.32]], nt(S, '#3f8a4a', 0.2)); fr(q, x - 1, ty + hh * 0.32, hh * 0.35, 3, nt(S, '#3a3a3a', 0.2)); });
      if (k === 'shop') { for (i = 0; i < 2; i++) { var cx = I.x0 + w * 0.62 + i * hh * 0.4; ln(q, [[cx, I.y0], [cx, I.y0 + hh * 0.1]], '#5a5e66', 1); q.strokeStyle = nt(S, '#c9a83a', 0.2); q.lineWidth = 1; q.beginPath(); q.moveTo(cx - hh * 0.13, I.y0 + hh * 0.42); q.lineTo(cx - hh * 0.13, I.y0 + hh * 0.2); q.quadraticCurveTo(cx, I.y0 + hh * 0.05, cx + hh * 0.13, I.y0 + hh * 0.2); q.lineTo(cx + hh * 0.13, I.y0 + hh * 0.42); for (var b = -2; b <= 2; b++) { q.moveTo(cx + b * hh * 0.05, I.y0 + hh * 0.42); q.lineTo(cx + b * hh * 0.05, I.y0 + hh * 0.14); } q.stroke(); fr(q, cx - hh * 0.14, I.y0 + hh * 0.42, hh * 0.28, 2, nt(S, '#c9a83a', 0.2)); }
        for (i = 0; i < 4; i++) paper(q, rect(I.x1 - hh * (0.35 + (i % 2) * 0.28), d - hh * (0.32 + Math.floor(i / 2) * 0.3), hh * 0.26, hh * 0.3), nt(S, pick(R, ['#d9342b', '#f2c94c', '#3a6fb0', '#2f8a5a']), 0.2), 0.6); } return; }
    shelves(q, I.x1 - Math.min(hh * 0.85, w * 0.32), I.x1 - hh * 0.05, I.y0 + hh * 0.06, d - hh * 0.04, 3, S, function (p, a, b, yb, h) { goods(p, a, b, yb, h, R, ['#d9342b', '#f2c94c', '#3a6fb0', '#2f8a5a', '#f2f2ee'], S, 'bag'); });
    if (k === 'groom') for (i = 0; i < 2; i++) { var gx = I.x0 + hh * (0.1 + i * 0.4); q.strokeStyle = nt(S, '#9aa0a8', 0.2); q.lineWidth = 1; q.strokeRect(gx, d - hh * 0.4, hh * 0.36, hh * 0.38); for (x = gx + hh * 0.05; x < gx + hh * 0.36; x += hh * 0.05) { q.beginPath(); q.moveTo(x, d - hh * 0.4); q.lineTo(x, d - hh * 0.02); q.stroke(); } }
    else poster(q, I.x0 + hh * 0.1, I.y0 + hh * 0.06, hh * 0.5, hh * 0.36, S, function (p, x2, y2, ww, h) { fr(p, x2, y2, ww, h, '#f2f8f8'); paw(p, x2 + ww * 0.5, y2 + h * 0.5, h * 0.35, '#5ab8b0'); });
  },
  live: function (S, L, V) {
    var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.work, k = V.k, i;
    if (L.tanks) L.tanks.forEach(function (tk, j) { for (var f = 0; f < 2; f++) { var F2 = L.fish[(j * 2 + f) % 12], u = Math.sin(t / (1400 + f * 300) + F2[0] * 9), fx = tk[0] + hh * (0.165 + u * 0.12), fy = tk[1] + hh * (0.09 + F2[1] * 0.16) + Math.sin(t / 500 + j) * 2, dr = Math.cos(t / (1400 + f * 300) + F2[0] * 9) > 0 ? 1 : -1; fe(c, fx, fy, hh * 0.03, hh * 0.017, F2[2]); fp(c, [[fx - dr * hh * 0.025, fy], [fx - dr * hh * 0.05, fy - hh * 0.015], [fx - dr * hh * 0.05, fy + hh * 0.015]], F2[2]); }
      var bu = (t / 1500 + j * 0.3) % 1; c.strokeStyle = 'rgba(255,255,255,.7)'; c.lineWidth = 0.8; c.beginPath(); c.arc(tk[0] + hh * 0.28, tk[1] + hh * 0.3 - bu * hh * 0.26, hh * 0.012, 0, TAU); c.stroke(); });
    if (k === 'fish') { fig(c, L.ppl[0], L.in.x0 + (L.in.x1 - L.in.x0) * 0.5, d - hh * 0.02, hh * 0.92, reach(L.in.x0 + (L.in.x1 - L.in.x0) * 0.5, d - hh * 0.02, hh * 0.92, STANDP, -1, [L.in.x0 + (L.in.x1 - L.in.x0) * 0.5 - hh * 0.25, d - hh * 0.55], null), -1); return; }
    if (k === 'shop') { for (i = 0; i < 2; i++) { var bx = L.in.x0 + (L.in.x1 - L.in.x0) * 0.62 + i * hh * 0.4, hop = Math.max(0, Math.sin(t / 300 + i * 2)) * hh * 0.04; fe(c, bx, L.in.y0 + hh * 0.36 - hop, hh * 0.04, hh * 0.03, ['#f2c94c', '#7fd8ff'][i]); fe(c, bx + hh * 0.03, L.in.y0 + hh * 0.33 - hop, hh * 0.02, hh * 0.02, ['#f2c94c', '#7fd8ff'][i]); }
      var bxx = L.in.x0 + (L.in.x1 - L.in.x0) * 0.62; fr(c, bxx - hh * 0.2, d - hh * 0.2, hh * 0.32, hh * 0.18, '#c9a06a'); cat(c, bxx - hh * 0.04, d - hh * 0.15, hh * 0.8, L.dogCol, t, 3); fr(c, bxx - hh * 0.2, d - hh * 0.12, hh * 0.32, hh * 0.1, '#b8905a'); return; }
    if (k === 'vet') { dogStand(c, x + hh * 0.2, d - hh * 0.45, hh * 0.85, L.dogCol, t, 1, 1); fig(c, L.ppl[0], x - hh * 0.22, d - hh * 0.02, hh * 0.92, reach(x - hh * 0.22, d - hh * 0.02, hh * 0.92, STANDP, 1, [x + hh * 0.08, d - hh * 0.62 + Math.sin(t / 800) * hh * 0.02], [x + hh * 0.18, d - hh * 0.6]), 1);
      ln(c, [[x - hh * 0.2, d - hh * 0.72], [x - hh * 0.14, d - hh * 0.6], [x - hh * 0.08, d - hh * 0.62]], '#2a2a2a', 1); fig(c, L.ppl[1], x + hh * 0.75, d - hh * 0.02, hh * 0.92, talk(t, 2), -1); return; }
    /* the tub: a dog to its chest in water, bubbles rising; the groomer with the shower */
    var tx = x + hh * 0.2; dogStand(c, tx, d - hh * 0.42, hh * 0.85, L.dogCol, t, 2, -1);
    fig(c, L.ppl[0], x - hh * 0.3, d - hh * 0.02, hh * 0.92, reach(x - hh * 0.3, d - hh * 0.02, hh * 0.92, STANDP, 1, [tx - hh * 0.08 + Math.sin(t / 300) * hh * 0.05, d - hh * 0.7], [tx - hh * 0.05, d - hh * 0.6]), 1);
    for (i = 0; i < 8; i++) { var u2 = (t / 2200 + i / 8) % 1, bx2 = tx - hh * 0.2 + (i * 0.37 % 1) * hh * 0.4 + Math.sin(u2 * 6 + i) * hh * 0.03, by2 = d - hh * 0.5 - u2 * hh * 0.5; c.strokeStyle = 'rgba(255,255,255,' + (0.9 * (1 - u2)).toFixed(2) + ')'; c.lineWidth = 1; c.beginPath(); c.arc(bx2, by2, hh * (0.015 + 0.02 * u2), 0, TAU); c.stroke(); }
    c.strokeStyle = 'rgba(180,220,250,.8)'; c.lineWidth = 1; c.beginPath(); for (i = 0; i < 4; i++) { var sx = tx - hh * 0.08 + Math.sin(t / 300) * hh * 0.05 + i * 2; c.moveTo(sx, d - hh * 0.68); c.lineTo(sx + 1, d - hh * 0.55); } c.stroke();
  },
  fore: function (q, S, L, V) {
    var hh = S.hh, d = S.deck, x = L.work;
    if (V.k === 'vet') { fr(q, x - hh * 0.08, d - hh * 0.45, hh * 0.6, hh * 0.04, nt(S, '#c9ccd4', 0.2)); fr(q, x + hh * 0.17, d - hh * 0.41, hh * 0.05, hh * 0.41, nt(S, '#9aa0a8', 0.2)); }
    if (V.k === 'groom') { var tx = x + hh * 0.2; paper(q, poly([[tx - hh * 0.32, d - hh * 0.5], [tx + hh * 0.32, d - hh * 0.5], [tx + hh * 0.28, d - hh * 0.22], [tx - hh * 0.28, d - hh * 0.22]]), nt(S, '#f2f2ee', 0.2), 1); fr(q, tx - hh * 0.3, d - hh * 0.5, hh * 0.6, hh * 0.04, 'rgba(150,200,240,.8)'); for (var i = 0; i < 6; i++) fe(q, tx - hh * 0.25 + i * hh * 0.1, d - hh * 0.5, hh * 0.05, hh * 0.035, '#ffffff'); fr(q, tx - hh * 0.25, d - hh * 0.22, hh * 0.04, hh * 0.22, nt(S, '#9aa0a8', 0.2)); fr(q, tx + hh * 0.21, d - hh * 0.22, hh * 0.04, hh * 0.22, nt(S, '#9aa0a8', 0.2)); }
  },
  out: function (q, S, L, V) { var hh = S.hh; fe(q, L.pawX, L.pawY, hh * 0.22, hh * 0.22, nt(S, '#f6f6f2', 0.3)); paw(q, L.pawX, L.pawY, hh * 0.25, nt(S, V.pawCol, 0.3)); },
  street: function (S, L, V) { if (!L.open || V.k === 'fish') return; var c = S.c, hh = S.hh, d = S.deck, t = S.t, x = L.bx0 - hh * 0.4 > S.x0 + hh * 0.8 ? L.bx0 - hh * 0.35 : L.bx1 + hh * 0.35; var me = fig(c, L.ppl[2], x, d + hh * 0.16, hh * 0.92, reach(x, d + hh * 0.16, hh * 0.92, STANDP, 1, [x + hh * 0.15, d - hh * 0.45], null), 1); ln(c, [me.hand[0], [x + hh * 0.42, d - hh * 0.05]], '#d9342b', 1); dogStand(c, x + hh * 0.5, d + hh * 0.17, hh * 0.75, L.dog2, t, 4, 1); }
}, 'the tail: θ = θ₀·sin ωt<br>a fish: x = x₀ + A·sin ωt');

/* ---------------------------------------------------------------- register: portraits are chosen by doodles_layer.place_scene, not by words */
Object.keys(SCENE).forEach(function (name) { var spec = SCENE[name]; D.addScene(name, function (S) { draw(S, spec, name); }, null, MATHS[name]); });
})();
