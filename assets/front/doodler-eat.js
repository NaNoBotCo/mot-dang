/* Food places, each drawn as itself (Nan, 2026-10-02: "utilize the doodler to avoid filler"). A
   restaurant, café, bar, bakery, street stall or noodle shop with no photograph of its own is cut from
   its facts: its building (shophouse, teak house, garden, riverside deck, glasshouse, mall unit, cart),
   its name on its board, a trade sign anyone can read without words, its kitchen at work, its diners,
   and its hours as shutters up or down. Six scenes: restaurant, cafe, bar, bakery, streetfood, noodle.
   The place id seeds the deal (building, colours, kitchen, props, people); the facts steer it. Still
   parts are cut once per size, seed and state into two offscreen layers; each frame draws what moves. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.kit || !D.kit.sign) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

/* ---------------------------------------------------------------- small cut pieces */
function E(x, y, rx, ry, rot) { return function (q) { q.beginPath(); q.ellipse(x, y, Math.max(0.3, rx), Math.max(0.3, ry), rot || 0, 0, TAU); }; }
function fe(c, x, y, rx, ry, col, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.3, rx), Math.max(0.3, ry), rot || 0, 0, TAU); c.fill(); }
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function pth(q, pts) { q.beginPath(); for (var i = 0; i < pts.length; i++) i ? q.lineTo(pts[i][0], pts[i][1]) : q.moveTo(pts[i][0], pts[i][1]); }
function fp(c, pts, col) { c.fillStyle = col; pth(c, pts); c.closePath(); c.fill(); }
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = Math.max(0.6, w); c.lineCap = 'round'; c.lineJoin = 'round'; pth(c, pts); c.stroke(); }
function glow(c, x, y, r, col, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, 'rgba(' + col + ',' + a + ')'); g.addColorStop(1, 'rgba(' + col + ',0)'); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); }
function txt(c, s, x, y, px, col, wt, al, maxw) { c.font = (wt || 700) + ' ' + Math.round(Math.max(7, px)) + 'px "Sarabun",system-ui,sans-serif'; c.fillStyle = col; c.textAlign = al || 'center'; c.textBaseline = 'middle'; if (maxw) c.fillText(s, x, y, maxw); else c.fillText(s, x, y); }
function pick(r, a) { return a[Math.floor(r() * a.length) % a.length]; }
function wpick(r, w) { var s = 0, k, last; for (k in w) s += w[k]; var u = r() * s; for (k in w) { last = k; u -= w[k]; if (u < 0) return k; } return last; }
function hx(h) { h = h.replace('#', ''); var n = parseInt(h, 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function mixc(a, b, u) { var A = hx(a), B = hx(b); return 'rgb(' + Math.round(lerp(A[0], B[0], u)) + ',' + Math.round(lerp(A[1], B[1], u)) + ',' + Math.round(lerp(A[2], B[2], u)) + ')'; }
function tri(u) { u = u - Math.floor(u); return u < 0.5 ? u * 2 : 2 - u * 2; }
/* steam off a dish or pot, each curl x = A·sin(ky − ωt), fading as it rises */
function steam(c, x, y, h, t, k, n, a) {
  n = n || 2; c.save(); c.strokeStyle = '#fff'; c.lineWidth = Math.max(1.1, h * 0.05); c.lineCap = 'round';
  for (var j = 0; j < n; j++) {
    var ph = (t / 2200 + j / n + k * 0.37) % 1, ox = x + (j - (n - 1) / 2) * h * 0.22;
    c.globalAlpha = (a || 0.6) * Math.sin(ph * Math.PI); c.beginPath();
    for (var i = 0; i <= 7; i++) { var f = i / 7, yy = y - (ph * 0.55 + f * 0.45) * h, xx = ox + Math.sin(f * 5 - t / 450 + j * 2 + k) * h * 0.08 * (0.4 + f); i ? c.lineTo(xx, yy) : c.moveTo(xx, yy); }
    c.stroke();
  }
  c.restore();
}
function smoke(c, x, y, h, t, k, col) {
  c.save(); c.strokeStyle = col || '#d8d4cc'; c.lineWidth = Math.max(2, h * 0.09); c.lineCap = 'round';
  for (var j = 0; j < 3; j++) { var ph = (t / 3200 + j / 3 + k) % 1; c.globalAlpha = 0.32 * Math.sin(ph * Math.PI); c.beginPath();
    for (var i = 0; i <= 7; i++) { var f = i / 7; c.lineTo(x + Math.sin(f * 4 - t / 700 + j * 2) * h * 0.14 * (0.3 + f) + f * h * 0.1, y - (ph * 0.5 + f * 0.5) * h); } c.stroke(); }
  c.restore();
}
function flames(c, x, y, w, h, t, k) {
  for (var i = 0; i < 5; i++) {
    var fx = x + (i - 2) * w * 0.2, fh = h * (0.55 + 0.45 * Math.abs(Math.sin(t / 130 + i * 1.7 + k))), sw = Math.sin(t / 170 + i) * w * 0.05;
    fp(c, [[fx - w * 0.11, y], [fx + sw, y - fh], [fx + w * 0.11, y]], i % 2 ? '#ffb02e' : '#ff6a1e');
    fp(c, [[fx - w * 0.05, y], [fx + sw * 0.6, y - fh * 0.55], [fx + w * 0.05, y]], '#ffe27a');
  }
}
function sparks(c, x, y, h, t, n) { for (var i = 0; i < n; i++) { var u = (t / 1400 + i / n) % 1; c.globalAlpha = 1 - u; fe(c, x + Math.sin(i * 2.3 + u * 5) * h * 0.18, y - u * h, 1.3, 1.3, i % 2 ? '#ffd27a' : '#ff8a3a'); } c.globalAlpha = 1; }
/* lai kham: gold flowers and scrolls stamped along a band */
function laiKham(c, x0, x1, y, s, col) {
  c.fillStyle = col || '#e8b84a'; c.strokeStyle = col || '#e8b84a'; c.lineWidth = Math.max(0.6, s * 0.12);
  for (var x = x0 + s; x < x1 - s * 0.5; x += s * 2.4) {
    for (var p = 0; p < 4; p++) { var a = p * Math.PI / 2 + 0.785; fe(c, x + Math.cos(a) * s * 0.42, y + Math.sin(a) * s * 0.42, s * 0.3, s * 0.16, col || '#e8b84a', a); }
    c.beginPath(); c.arc(x + s * 1.2, y, s * 0.35, Math.PI * 0.2, Math.PI * 1.6); c.stroke();
  }
}
function kalae(c, x, y, l, col) {
  ln(c, [[x, y], [x - l * 0.25, y - l * 0.7], [x - l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
  ln(c, [[x, y], [x + l * 0.25, y - l * 0.7], [x + l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
}

/* ---------------------------------------------------------------- the still layers, cut once */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : { a: 1, d: 1, e: 0, f: 0 }, k = key + '|' + [m.a, m.d, m.e, m.f].join(','), e = null;
  for (var i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    var cv = document.createElement('canvas'); cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    e = { k: k, cv: cv, ox: ox, oy: oy, out: draw(q) };
    CACHE.unshift(e); if (CACHE.length > 30) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
  return e;
}
/* night over what is cut so far, leaving what glows to be drawn after it */
function dusk(q, S, box, a) { q.save(); q.globalCompositeOperation = 'source-atop'; q.fillStyle = 'rgba(14,12,40,' + (a || 0.45) + ')'; q.fillRect(box[0], box[1], box[2], box[3]); q.restore(); }

/* ---------------------------------------------------------------- people at work
   arms by two-link inverse kinematics: shoulder S, hand target T, upper arm l₁, forearm l₂;
   the elbow from the law of cosines, cos α = (l₁² + d² − l₂²) / 2l₁d */
function ik(sh, T, h, dir) {
  var l1 = h * 0.17, l2 = h * 0.16, dx = T[0] - sh[0], dy = T[1] - sh[1], d = Math.max(Math.abs(l1 - l2) + 0.5, Math.min(Math.hypot(dx, dy), (l1 + l2) * 0.995));
  var phi = Math.atan2(dir * dx, dy), al = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))), up = phi - al;
  var ex = sh[0] + dir * Math.sin(up) * l1, ey = sh[1] + Math.cos(up) * l1, el = Math.atan2(dir * (T[0] - ex), T[1] - ey) - up;
  while (el > Math.PI) el -= TAU; while (el < -Math.PI) el += TAU;
  return [up, el];
}
function shoulder(x, y, h, seat, lean, dir) { var hip = [x, y - h * seat]; return [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33]; }
function worker(c, x, y, h, base, d, T1, T2) {
  var dir = d.dir || 1, lean = base.lean || 0, seat = base.seat || 0.47, sh = shoulder(x, y, h, seat, lean, dir);
  var A1 = T1 ? ik(sh, T1, h, dir) : [0.15, 0.1], A2 = T2 ? ik(sh, T2, h, dir) : [-0.1, 0.1];
  var me = K.person(c, x, y, h, { lean: lean, seat: seat, legs: base.legs || [0.06, 0, -0.06, 0], arms: [A1[0], A1[1], A2[0], A2[1]], lift: base.lift }, d);
  me.A1 = A1; me.dir = dir; me.h = h; return me;
}
function apron(c, me, d, col) {
  var h = me.h, dir = me.dir, sh = me.sh, hip = me.hip, w = h * 0.075;
  fp(c, [[sh[0] - w * 0.6, sh[1] + h * 0.06], [sh[0] + w * 0.9, sh[1] + h * 0.06], [hip[0] + w * 1.3 + dir * h * 0.02, hip[1] + h * 0.2], [hip[0] - w * 1.1, hip[1] + h * 0.2]], col);
  var e = [sh[0] + dir * Math.sin(me.A1[0]) * h * 0.17, sh[1] + Math.cos(me.A1[0]) * h * 0.17], aw = Math.max(2, h * 0.075);
  ln(c, [sh, e], d.col, aw); ln(c, [e, me.hand[0]], d.skin || '#d9a27a', aw * 0.85);
}
function hat(c, me, kind, col) {
  var h = me.h, x = me.head[0], y = me.head[1], r = h * 0.1, dir = me.dir;
  if (kind === 'toque') { fp(c, [[x - r * 0.9, y - r * 0.5], [x + r * 0.9, y - r * 0.5], [x + r, y - r * 1.5], [x - r, y - r * 1.5]], '#fbfbf7'); [-0.6, 0, 0.6].forEach(function (k) { fe(c, x + k * r, y - r * 1.75, r * 0.6, r * 0.5, '#ffffff'); }); }
  else if (kind === 'cap') { c.fillStyle = col || '#2c2f45'; c.beginPath(); c.arc(x, y - r * 0.2, r * 1.05, Math.PI, TAU); c.fill(); fp(c, [[x, y - r * 0.3], [x + dir * r * 1.9, y - r * 0.25], [x + dir * r * 1.5, y - r * 0.05]], col || '#2c2f45'); }
  else if (kind === 'band') { c.strokeStyle = col || '#fbfbf7'; c.lineWidth = r * 0.42; c.beginPath(); c.ellipse(x, y - r * 0.45, r * 1.02, r * 0.3, 0, 0, TAU); c.stroke(); fp(c, [[x - dir * r, y - r * 0.5], [x - dir * r * 1.7, y - r * 0.2], [x - dir * r * 1.5, y + r * 0.1]], col || '#fbfbf7'); }
  else if (kind === 'kerchief') { c.fillStyle = col || '#c0392b'; c.beginPath(); c.arc(x, y - r * 0.15, r * 1.08, Math.PI * 1.02, Math.PI * 1.98); c.closePath(); c.fill(); fp(c, [[x - dir * r, y - r * 0.3], [x - dir * r * 1.6, y + r * 0.2], [x - dir * r * 1.2, y + r * 0.3]], col || '#c0392b'); }
  else if (kind === 'beanie') { c.fillStyle = col || '#3a5a4a'; c.beginPath(); c.arc(x, y - r * 0.25, r * 1.08, Math.PI * 1.02, Math.PI * 1.98); c.closePath(); c.fill(); fr(c, x - r * 1.05, y - r * 0.45, r * 2.1, r * 0.3, col || '#3a5a4a'); }
  else if (kind === 'kopiah') { c.fillStyle = col || '#fbfbf7'; c.beginPath(); c.ellipse(x, y - r * 0.55, r * 1.02, r * 0.62, 0, Math.PI, TAU); c.fill(); }
  else if (kind === 'cone') { fp(c, [[x - r * 2.3, y - r * 0.35], [x, y - r * 2.3], [x + r * 2.3, y - r * 0.35]], '#e3c47e'); }
}
var SEAT = { stool: { lean: 0.14, seat: 0.3, legs: [1.5, -1.5, 1.45, -1.5] }, chair: { lean: 0.08, seat: 0.33, legs: [1.5, -1.45, 1.42, -1.45] },
  floor: { lean: 0.15, seat: 0.1, legs: [1.45, -2.9, 1.45, -2.9] }, high: { lean: 0.1, seat: 0.5, legs: [1.25, -1.05, 1.15, -1.0] } };

/* ---------------------------------------------------------------- what sits on the tables
   (c, x, y, s): centre, table line, size; each returns its steam point or null */
function plate(c, x, y, s, col) { paper(c, E(x, y - s * 0.04, s * 0.5, s * 0.12), col || '#f6f1e6', 0.6); fe(c, x, y - s * 0.06, s * 0.36, s * 0.07, 'rgba(120,90,60,.12)'); return y - s * 0.07; }
function bowl(c, x, y, s, body, soup, band) {
  var w = s, h = w * 0.42, ty = y - h;
  paper(c, function (q) { q.beginPath(); q.moveTo(x - w / 2, ty); q.bezierCurveTo(x - w / 2, y - w * 0.08, x - w * 0.22, y - w * 0.03, x - w * 0.15, y - w * 0.02); q.lineTo(x - w * 0.16, y); q.lineTo(x + w * 0.16, y); q.lineTo(x + w * 0.15, y - w * 0.02); q.bezierCurveTo(x + w * 0.22, y - w * 0.03, x + w / 2, y - w * 0.08, x + w / 2, ty); q.ellipse(x, ty, w / 2, w * 0.11, 0, 0, Math.PI, true); q.closePath(); }, body, 0.7);
  fe(c, x, ty, w * 0.47, w * 0.095, soup);
  if (band) { c.strokeStyle = band; c.lineWidth = Math.max(1, w * 0.04); c.beginPath(); c.ellipse(x, ty + h * 0.25, w * 0.47, w * 0.1, 0, 0.25, Math.PI - 0.25); c.stroke(); }
  return ty;
}
function glassCup(c, x, y, w, h, fill, lev, ice) {
  fp(c, [[x - w * 0.5, y - h], [x + w * 0.5, y - h], [x + w * 0.38, y], [x - w * 0.38, y]], 'rgba(225,240,245,.55)');
  fp(c, [[x - w * 0.46, y - h * lev], [x + w * 0.46, y - h * lev], [x + w * 0.37, y - 1], [x - w * 0.37, y - 1]], fill);
  if (ice) { fr(c, x - w * 0.25, y - h * lev + 1, w * 0.22, w * 0.2, 'rgba(255,255,255,.55)'); fr(c, x + w * 0.05, y - h * lev + 3, w * 0.2, w * 0.18, 'rgba(255,255,255,.45)'); }
  ln(c, [[x - w * 0.3, y - h * 0.85], [x - w * 0.24, y - h * 0.15]], 'rgba(255,255,255,.6)', w * 0.07);
}
function bottle(c, x, y, s, col) { fp(c, [[x - s * 0.09, y], [x - s * 0.09, y - s * 0.45], [x - s * 0.04, y - s * 0.58], [x - s * 0.035, y - s * 0.75], [x + s * 0.035, y - s * 0.75], [x + s * 0.04, y - s * 0.58], [x + s * 0.09, y - s * 0.45], [x + s * 0.09, y]], col || '#5a3212'); fr(c, x - s * 0.09, y - s * 0.36, s * 0.18, s * 0.14, 'rgba(242,230,201,.85)'); ln(c, [[x - s * 0.05, y - s * 0.42], [x - s * 0.05, y - s * 0.1]], 'rgba(255,255,255,.35)', s * 0.03); }
function rice(c, x, y, s) { fe(c, x, y - s * 0.1, s * 0.22, s * 0.13, '#fbf8ee'); fe(c, x - s * 0.05, y - s * 0.16, s * 0.1, s * 0.05, '#ffffff'); }
function egg(c, x, y, s) { fe(c, x, y, s * 0.16, s * 0.08, '#fffaf0'); fe(c, x + s * 0.02, y - s * 0.03, s * 0.07, s * 0.05, '#f7b500'); }
function herbs(c, x, y, s, n) { for (var i = 0; i < (n || 4); i++) { c.save(); c.translate(x + (i - 1.5) * s * 0.07, y); c.rotate(-0.6 + i * 0.4); fe(c, 0, -s * 0.05, s * 0.035, s * 0.08, i % 2 ? '#3f8a3a' : '#5aa83a'); c.restore(); } }
function chopsticks(c, x, y, s, a) { ln(c, [[x, y], [x + Math.cos(a) * s * 0.7, y - Math.sin(a) * s * 0.7]], '#c8a060', s * 0.035); ln(c, [[x + s * 0.04, y], [x + s * 0.04 + Math.cos(a - 0.08) * s * 0.7, y - Math.sin(a - 0.08) * s * 0.7]], '#b08a50', s * 0.035); }
var DISH = {
  krapao: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.08, t, s); fe(c, x + s * 0.13, t - s * 0.05, s * 0.18, s * 0.07, '#7a4a28'); herbs(c, x + s * 0.13, t - s * 0.08, s, 3); egg(c, x - s * 0.05, t - s * 0.2, s); return [x, t - s * 0.15]; },
  friedrice: function (c, x, y, s) { var t = plate(c, x, y, s); fe(c, x, t - s * 0.09, s * 0.28, s * 0.13, '#e8b86a'); for (var i = 0; i < 6; i++) fe(c, x - s * 0.2 + i * s * 0.08, t - s * 0.1 - (i % 2) * s * 0.06, s * 0.025, s * 0.02, ['#d9342b', '#3f8a3a', '#f7e08a'][i % 3]); fe(c, x + s * 0.3, t - s * 0.03, s * 0.08, s * 0.05, '#7cc243'); return [x, t - s * 0.15]; },
  tomyum: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.85, '#f6f2ea', '#e8642a', '#3a6db0'); fe(c, x - s * 0.12, t, s * 0.08, s * 0.03, '#f29a6a'); fe(c, x + s * 0.1, t, s * 0.06, s * 0.025, '#3f8a3a'); return [x, t]; },
  omelet: function (c, x, y, s) { var t = plate(c, x, y, s); paper(c, E(x, t - s * 0.06, s * 0.3, s * 0.1), '#f2c24a', 0.4); fe(c, x - s * 0.1, t - s * 0.09, s * 0.08, s * 0.03, '#c88a2a'); return [x, t - s * 0.1]; },
  curryrice: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.1, t, s); fe(c, x + s * 0.14, t - s * 0.05, s * 0.17, s * 0.07, '#5d9b3a'); fe(c, x + s * 0.2, t - s * 0.08, s * 0.05, s * 0.03, '#f2e6c9'); return [x, t - s * 0.1]; },
  redcurry: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.12, t, s); fe(c, x + s * 0.14, t - s * 0.05, s * 0.17, s * 0.07, '#c8452a'); fe(c, x + s * 0.18, t - s * 0.08, s * 0.05, s * 0.025, '#3f8a3a'); return [x, t - s * 0.1]; },
  khaosoi: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.9, '#f6f2ea', '#dc8a2c', '#3a6db0'); for (var i = 0; i < 5; i++) fe(c, x - s * 0.12 + i * s * 0.06, t - s * 0.05 - (i % 2) * s * 0.03, s * 0.05, s * 0.03, '#e8b04a'); fe(c, x + s * 0.24, t + s * 0.02, s * 0.06, s * 0.03, '#5c9e32'); return [x, t]; },
  saioua: function (c, x, y, s) { var t = plate(c, x, y, s); c.strokeStyle = '#a8452a'; c.lineWidth = s * 0.08; c.beginPath(); for (var a = 0; a < 3.5 * TAU; a += 0.3) { var r = s * 0.012 * a; c.lineTo(x + Math.cos(a) * r, t - s * 0.05 + Math.sin(a) * r * 0.35); } c.stroke(); return null; },
  namprik: function (c, x, y, s) { var t = plate(c, x, y, s, '#e8d8b0'); bowl(c, x, t + s * 0.02, s * 0.35, '#a85a2a', '#c8452a'); for (var i = 0; i < 4; i++) fe(c, x + (i < 2 ? -1 : 1) * s * (0.28 + (i % 2) * 0.08), t - s * 0.04, s * 0.07, s * 0.03, ['#5aa83a', '#f2e6c9', '#d8c060', '#3f8a3a'][i], i); return null; },
  kratip: function (c, x, y, s) { paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.13, y); q.lineTo(x - s * 0.16, y - s * 0.32); q.quadraticCurveTo(x, y - s * 0.46, x + s * 0.16, y - s * 0.32); q.lineTo(x + s * 0.13, y); q.closePath(); }, '#c8a060', 0.6); for (var i = 0; i < 4; i++) ln(c, [[x - s * 0.15, y - s * (0.06 + i * 0.07)], [x + s * 0.15, y - s * (0.06 + i * 0.07)]], 'rgba(90,50,20,.45)', 0.8); return null; },
  somtam: function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 9; i++) ln(c, [[x - s * 0.22 + i * s * 0.05, t - s * 0.04], [x - s * 0.15 + i * s * 0.04, t - s * 0.16 - (i % 3) * s * 0.02]], i % 3 ? '#b8d070' : '#e8a84a', s * 0.03); fe(c, x + s * 0.1, t - s * 0.12, s * 0.04, s * 0.04, '#d9342b'); fe(c, x - s * 0.08, t - s * 0.1, s * 0.035, s * 0.035, '#e8642a'); return null; },
  gaiyang: function (c, x, y, s) { var t = plate(c, x, y, s); paper(c, E(x, t - s * 0.09, s * 0.27, s * 0.12), '#b8681e', 0.4); for (var i = 0; i < 4; i++) ln(c, [[x - s * 0.2 + i * s * 0.12, t - s * 0.14], [x - s * 0.14 + i * s * 0.12, t - s * 0.02]], '#5a2a0a', s * 0.025); return null; },
  larb: function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 10; i++) fe(c, x - s * 0.22 + (i * 37 % 10) * s * 0.045, t - s * 0.05 - (i % 3) * s * 0.03, s * 0.04, s * 0.03, i % 3 ? '#8a5a3a' : '#5aa83a'); return [x, t - s * 0.08]; },
  noodle: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.9, '#f6f2ea', '#c88a4a', '#c0392b'); for (var i = 0; i < 4; i++) ln(c, [[x - s * 0.2, t - s * 0.01 + i * s * 0.012], [x + s * 0.15, t - s * 0.02 + i * s * 0.01]], '#f2e2a8', s * 0.02); fe(c, x + s * 0.12, t - s * 0.02, s * 0.08, s * 0.035, '#d87a6a'); herbs(c, x - s * 0.1, t, s, 3); chopsticks(c, x + s * 0.05, t + s * 0.02, s, 1.1); return [x, t]; },
  chickenrice: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.08, t, s); for (var i = 0; i < 4; i++) fe(c, x + s * 0.08 + i * s * 0.05, t - s * 0.12 + i * s * 0.01, s * 0.06, s * 0.04, '#f6e2b8', 0.3); fe(c, x + s * 0.32, t - s * 0.02, s * 0.06, s * 0.03, '#3f8a3a'); return null; },
  redpork: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.08, t, s); for (var i = 0; i < 4; i++) fe(c, x + s * 0.06 + i * s * 0.05, t - s * 0.12 + i * s * 0.01, s * 0.06, s * 0.035, i % 2 ? '#c8402a' : '#d8a07a', 0.3); fe(c, x + s * 0.06, t - s * 0.04, s * 0.18, s * 0.04, '#b8302a'); return null; },
  sushi: function (c, x, y, s) { paper(c, rect(x - s * 0.42, y - s * 0.08, s * 0.84, s * 0.08), '#c8925a', 0.5); for (var i = 0; i < 4; i++) { var sx = x - s * 0.3 + i * s * 0.2; fe(c, sx, y - s * 0.12, s * 0.08, s * 0.05, '#fbf8ee'); fe(c, sx, y - s * 0.17, s * 0.09, s * 0.035, ['#f08a5d', '#d8343a', '#f7d040', '#f08a5d'][i]); } return null; },
  ramen: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.95, '#2a2018', '#d8b07a', '#c0392b'); fe(c, x - s * 0.12, t - s * 0.01, s * 0.08, s * 0.04, '#fffaf0'); fe(c, x - s * 0.12, t - s * 0.02, s * 0.04, s * 0.025, '#f2a020'); fe(c, x + s * 0.1, t, s * 0.1, s * 0.035, '#d89a7a'); fp(c, [[x + s * 0.2, t - s * 0.02], [x + s * 0.3, t - s * 0.2], [x + s * 0.34, t - s * 0.18], [x + s * 0.26, t]], '#1a2a1a'); chopsticks(c, x - s * 0.05, t + s * 0.02, s, 1.2); return [x, t]; },
  matcha: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.45, '#5a3a2a', '#7ab84a'); return [x, t]; },
  dimsum: function (c, x, y, s) { paper(c, rect(x - s * 0.3, y - s * 0.2, s * 0.6, s * 0.2), '#d8b070', 0.5); for (var i = 0; i < 3; i++) ln(c, [[x - s * 0.3, y - s * (0.04 + i * 0.06)], [x + s * 0.3, y - s * (0.04 + i * 0.06)]], 'rgba(120,80,30,.4)', 0.8); for (i = 0; i < 3; i++) fe(c, x - s * 0.18 + i * s * 0.18, y - s * 0.24, s * 0.08, s * 0.06, '#f6eedc'); return [x, y - s * 0.26]; },
  duckrice: function (c, x, y, s) { var t = plate(c, x, y, s); rice(c, x - s * 0.08, t, s); for (var i = 0; i < 4; i++) fe(c, x + s * 0.06 + i * s * 0.05, t - s * 0.12 + i * s * 0.01, s * 0.06, s * 0.04, i % 2 ? '#8a3a1a' : '#a8502a', 0.3); return null; },
  tea: function (c, x, y, s) { paper(c, E(x, y - s * 0.16, s * 0.2, s * 0.16), '#f6f2ea', 0.5); fp(c, [[x + s * 0.18, y - s * 0.2], [x + s * 0.34, y - s * 0.3], [x + s * 0.2, y - s * 0.14]], '#f6f2ea'); fe(c, x, y - s * 0.32, s * 0.06, s * 0.03, '#3a6db0'); ln(c, [[x - s * 0.18, y - s * 0.16], [x + s * 0.18, y - s * 0.16]], '#3a6db0', 1); return [x + s * 0.32, y - s * 0.3]; },
  pho: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.95, '#f6f2ea', '#d8b88a', '#3a8a6a'); for (var i = 0; i < 3; i++) fe(c, x - s * 0.1 + i * s * 0.1, t - s * 0.01, s * 0.06, s * 0.03, '#a8604a'); herbs(c, x + s * 0.15, t, s, 4); fe(c, x - s * 0.22, t, s * 0.05, s * 0.025, '#5c9e32'); return [x, t]; },
  banhmi: function (c, x, y, s) { var t = plate(c, x, y, s); paper(c, E(x, t - s * 0.08, s * 0.34, s * 0.08, -0.05), '#d99a4e', 0.4); fe(c, x, t - s * 0.13, s * 0.28, s * 0.03, '#5aa83a'); fe(c, x + s * 0.05, t - s * 0.11, s * 0.2, s * 0.025, '#e8803a'); return null; },
  pizza: function (c, x, y, s) { fr(c, x - s * 0.04, y - s * 0.12, s * 0.08, s * 0.12, '#8a8a8a'); paper(c, E(x, y - s * 0.13, s * 0.48, s * 0.12), '#e0a050', 0.5); fe(c, x, y - s * 0.14, s * 0.4, s * 0.09, '#e84a2a'); fe(c, x, y - s * 0.15, s * 0.36, s * 0.075, '#f6d878'); for (var i = 0; i < 7; i++) fe(c, x - s * 0.28 + i * s * 0.09, y - s * 0.14 + (i % 2 ? 1 : -1) * s * 0.03, s * 0.035, s * 0.02, i % 2 ? '#a8241c' : '#3f8a3a'); return [x, y - s * 0.16]; },
  pasta: function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 6; i++) { c.strokeStyle = '#f2d58a'; c.lineWidth = s * 0.03; c.beginPath(); c.arc(x + (i - 2.5) * s * 0.05, t - s * 0.06, s * 0.08, Math.PI, TAU); c.stroke(); } fe(c, x, t - s * 0.1, s * 0.12, s * 0.05, '#c8402a'); herbs(c, x, t - s * 0.13, s, 2); return [x, t - s * 0.1]; },
  wine: function (c, x, y, s) { ln(c, [[x, y], [x, y - s * 0.25]], 'rgba(225,240,245,.8)', s * 0.03); fr(c, x - s * 0.1, y - 1, s * 0.2, 2, 'rgba(225,240,245,.8)'); fp(c, [[x - s * 0.1, y - s * 0.5], [x + s * 0.1, y - s * 0.5], [x + s * 0.07, y - s * 0.26], [x - s * 0.07, y - s * 0.26]], 'rgba(225,240,245,.55)'); fp(c, [[x - s * 0.09, y - s * 0.38], [x + s * 0.09, y - s * 0.38], [x + s * 0.06, y - s * 0.27], [x - s * 0.06, y - s * 0.27]], '#7a1a2a'); return null; },
  steak: function (c, x, y, s) { var t = plate(c, x, y, s); paper(c, function (q) { q.beginPath(); q.ellipse(x - s * 0.05, t - s * 0.07, s * 0.24, s * 0.1, -0.1, 0, TAU); }, '#6a2e18', 0.4); for (var i = 0; i < 3; i++) ln(c, [[x - s * 0.2 + i * s * 0.12, t - s * 0.12], [x - s * 0.14 + i * s * 0.12, t - s * 0.02]], '#3a1608', s * 0.025); for (i = 0; i < 4; i++) fr(c, x + s * 0.18 + i * s * 0.035, t - s * 0.14 + (i % 2) * s * 0.02, s * 0.025, s * 0.12, '#f2c24a'); return [x - s * 0.05, t - s * 0.12]; },
  burger: function (c, x, y, s) { var t = plate(c, x, y, s); fe(c, x, t - s * 0.04, s * 0.2, s * 0.05, '#d99a4e'); fe(c, x, t - s * 0.09, s * 0.21, s * 0.04, '#5a2e1a'); fe(c, x, t - s * 0.12, s * 0.22, s * 0.025, '#5aa83a'); paper(c, function (q) { q.beginPath(); q.ellipse(x, t - s * 0.15, s * 0.2, s * 0.12, 0, Math.PI, TAU); q.closePath(); }, '#e0a050', 0.4); for (var i = 0; i < 4; i++) fr(c, x + s * 0.24 + i * s * 0.03, t - s * 0.13 + (i % 2) * s * 0.02, s * 0.022, s * 0.11, '#f2c24a'); return null; },
  beer: function (c, x, y, s) { glassCup(c, x, y, s * 0.24, s * 0.42, '#f2b02a', 0.85); fe(c, x, y - s * 0.4, s * 0.12, s * 0.05, '#fffaf0'); bottle(c, x + s * 0.24, y, s * 0.9, '#3a5a2a'); return null; },
  curryb: function (c, x, y, s) { var t = bowl(c, x - s * 0.12, y, s * 0.5, '#c0c4c8', '#e07a2a'); fe(c, x - s * 0.12, t, s * 0.06, s * 0.02, '#fffaf0'); paper(c, E(x + s * 0.2, y - s * 0.05, s * 0.2, s * 0.06, 0.2), '#e8c088', 0.4); fe(c, x + s * 0.22, y - s * 0.07, s * 0.05, s * 0.02, '#a8642a'); return [x - s * 0.12, t]; },
  naan: function (c, x, y, s) { var t = plate(c, x, y, s, '#c0c4c8'); paper(c, E(x, t - s * 0.04, s * 0.3, s * 0.08, 0.1), '#ecc88a', 0.4); fe(c, x - s * 0.1, t - s * 0.06, s * 0.04, s * 0.02, '#a8642a'); fe(c, x + s * 0.08, t - s * 0.07, s * 0.04, s * 0.02, '#a8642a'); return null; },
  chai: function (c, x, y, s) { glassCup(c, x, y, s * 0.2, s * 0.26, '#c8925a', 0.8); return [x, y - s * 0.28]; },
  prawns: function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 4; i++) { c.strokeStyle = i % 2 ? '#f0703a' : '#e85a2a'; c.lineWidth = s * 0.06; c.beginPath(); c.arc(x - s * 0.2 + i * s * 0.13, t - s * 0.07, s * 0.07, Math.PI * 0.9, Math.PI * 2.2); c.stroke(); } lime(c, x + s * 0.32, t - s * 0.01, s * 0.06); return [x, t - s * 0.1]; },
  crab: function (c, x, y, s) { var t = plate(c, x, y, s); paper(c, function (q) { q.beginPath(); q.ellipse(x, t - s * 0.08, s * 0.2, s * 0.11, 0, Math.PI, TAU); q.closePath(); }, '#e0402a', 0.4); for (var i = -1; i <= 1; i += 2) { ln(c, [[x + i * s * 0.18, t - s * 0.06], [x + i * s * 0.3, t - s * 0.16], [x + i * s * 0.26, t - s * 0.22]], '#d8342a', s * 0.045); } return [x, t - s * 0.12]; },
  tofu: function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 4; i++) paper(c, rect(x - s * 0.22 + i * s * 0.11, t - s * 0.12 - (i % 2) * s * 0.03, s * 0.09, s * 0.09), '#e8b45a', 0.3); return null; },
  soup: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.8, '#f6f2ea', '#e8dcb0', '#5aa83a'); fe(c, x - s * 0.08, t, s * 0.07, s * 0.025, '#5aa83a'); fe(c, x + s * 0.1, t, s * 0.06, s * 0.025, '#f2e6c9'); return [x, t]; },
  bucket: function (c, x, y, s) { fp(c, [[x - s * 0.2, y - s * 0.38], [x + s * 0.2, y - s * 0.38], [x + s * 0.15, y], [x - s * 0.15, y]], '#f6f2ea'); fr(c, x - s * 0.19, y - s * 0.3, s * 0.38, s * 0.07, '#c8202a'); fr(c, x - s * 0.17, y - s * 0.16, s * 0.34, s * 0.07, '#c8202a'); for (var i = 0; i < 4; i++) fe(c, x - s * 0.15 + i * s * 0.1, y - s * 0.4, s * 0.07, s * 0.06, '#c8782a'); return null; },
  cola: function (c, x, y, s) { glassCup(c, x, y, s * 0.2, s * 0.36, '#3a1a10', 0.85, true); ln(c, [[x + s * 0.02, y - s * 0.3], [x + s * 0.08, y - s * 0.5]], '#e8e2d0', s * 0.025); return null; },
  thaitea: function (c, x, y, s) { glassCup(c, x, y, s * 0.22, s * 0.4, '#e8862a', 0.85, true); ln(c, [[x + s * 0.02, y - s * 0.32], [x + s * 0.06, y - s * 0.55]], '#2fae5a', s * 0.03); return null; },
  water: function (c, x, y, s) { glassCup(c, x, y, s * 0.2, s * 0.3, 'rgba(180,220,240,.6)', 0.8, true); return null; },
  latte: function (c, x, y, s) { paper(c, E(x, y - s * 0.02, s * 0.22, s * 0.05), '#f6f2ea', 0.3); fp(c, [[x - s * 0.15, y - s * 0.22], [x + s * 0.15, y - s * 0.22], [x + s * 0.11, y - s * 0.03], [x - s * 0.11, y - s * 0.03]], '#f6f2ea'); c.strokeStyle = '#f6f2ea'; c.lineWidth = s * 0.03; c.beginPath(); c.arc(x + s * 0.16, y - s * 0.13, s * 0.05, -1.4, 1.4); c.stroke(); fe(c, x, y - s * 0.22, s * 0.15, s * 0.03, '#c8925a'); fe(c, x, y - s * 0.22, s * 0.06, s * 0.015, '#f6e8d0'); return [x, y - s * 0.24]; },
  icedlatte: function (c, x, y, s) { glassCup(c, x, y, s * 0.22, s * 0.44, '#c8925a', 0.8, true); fp(c, [[x - s * 0.1, y - s * 0.3], [x + s * 0.1, y - s * 0.3], [x + s * 0.085, y - s * 0.03], [x - s * 0.085, y - s * 0.03]], 'rgba(90,50,20,.55)'); ln(c, [[x, y - s * 0.35], [x + s * 0.05, y - s * 0.56]], '#1a1a1a', s * 0.025); return null; },
  cake: function (c, x, y, s) { var t = plate(c, x, y, s * 0.7); fp(c, [[x - s * 0.16, t], [x + s * 0.16, t], [x + s * 0.16, t - s * 0.2], [x - s * 0.08, t - s * 0.24]], '#f6e2c8'); fr(c, x - s * 0.16, t - s * 0.13, s * 0.32, s * 0.035, '#8a4a2a'); fp(c, [[x - s * 0.16, t - s * 0.2], [x + s * 0.16, t - s * 0.2], [x - s * 0.08, t - s * 0.24]], '#f8f4ee'); fe(c, x + s * 0.06, t - s * 0.25, s * 0.035, s * 0.035, '#d8242a'); return null; },
  croissant: function (c, x, y, s) { var t = plate(c, x, y, s * 0.8); for (var i = -2; i <= 2; i++) fe(c, x + i * s * 0.07, t - s * 0.06 - (2 - Math.abs(i)) * s * 0.02, s * 0.06, s * 0.05 + (2 - Math.abs(i)) * s * 0.01, i % 2 ? '#c8822a' : '#e0a04a', i * 0.3); return null; },
  laptop: function (c, x, y, s, S) { fp(c, [[x - s * 0.3, y], [x + s * 0.3, y], [x + s * 0.26, y - s * 0.03], [x - s * 0.26, y - s * 0.03]], '#9aa0a8'); fp(c, [[x - s * 0.22, y - s * 0.03], [x - s * 0.28, y - s * 0.38], [x + s * 0.2, y - s * 0.38], [x + s * 0.22, y - s * 0.03]], '#4a4e58'); fp(c, [[x - s * 0.19, y - s * 0.06], [x - s * 0.24, y - s * 0.35], [x + s * 0.17, y - s * 0.35], [x + s * 0.19, y - s * 0.06]], S && S.night ? '#9fd0ff' : '#cfe6f8'); return null; },
  book: function (c, x, y, s) { fr(c, x - s * 0.18, y - s * 0.05, s * 0.36, s * 0.05, '#2f6db0'); fr(c, x - s * 0.16, y - s * 0.09, s * 0.32, s * 0.04, '#e8b84a'); fr(c, x - s * 0.17, y - s * 0.12, s * 0.34, s * 0.03, '#a8241c'); return null; },
  cocktail: function (c, x, y, s) { ln(c, [[x, y], [x, y - s * 0.2]], 'rgba(225,240,245,.8)', s * 0.03); fr(c, x - s * 0.09, y - 1, s * 0.18, 2, 'rgba(225,240,245,.8)'); fp(c, [[x - s * 0.18, y - s * 0.42], [x + s * 0.18, y - s * 0.42], [x, y - s * 0.2]], 'rgba(225,240,245,.55)'); fp(c, [[x - s * 0.15, y - s * 0.39], [x + s * 0.15, y - s * 0.39], [x, y - s * 0.23]], pick(K.rnd(Math.round(x)), ['#e84a7a', '#5ac8e8', '#f2a02a', '#7ae05a'])); lime(c, x + s * 0.16, y - s * 0.42, s * 0.05); return null; },
  bingsu: function (c, x, y, s) { var t = bowl(c, x, y, s * 0.6, '#c8d8e8', '#f6f2ea'); paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.27, t); q.quadraticCurveTo(x - s * 0.12, t - s * 0.42, x, t - s * 0.44); q.quadraticCurveTo(x + s * 0.12, t - s * 0.42, x + s * 0.27, t); q.closePath(); }, '#fbf6f0', 0.4); for (var i = 0; i < 5; i++) fe(c, x - s * 0.12 + i * s * 0.06, t - s * (0.22 + (i % 2) * 0.1), s * 0.04, s * 0.035, ['#d8242a', '#f7d040', '#8a4a2a', '#5aa83a', '#f08aa0'][i]); fe(c, x, t - s * 0.44, s * 0.08, s * 0.06, '#e84a6a'); return null; },
  khanom: function (c, x, y, s) { var t = plate(c, x, y, s, '#5aa83a'); for (var i = 0; i < 3; i++) { var kx = x - s * 0.2 + i * s * 0.2; for (var j = 0; j < 4; j++) fr(c, kx - s * 0.07, t - s * (0.04 + j * 0.03), s * 0.14, s * 0.03, j % 2 ? '#f6f2ea' : ['#2fae5a', '#e8508a', '#8a5ad8'][i]); } return null; }
};
function lime(c, x, y, r) { c.fillStyle = '#5c9e32'; c.beginPath(); c.arc(x, y, r, Math.PI, TAU); c.fill(); c.fillStyle = '#cfe68a'; c.beginPath(); c.arc(x, y, r * 0.78, Math.PI, TAU); c.fill(); }
/* what a diner lifts from dish to mouth; lift 0 at the dish, 1 at the mouth */
function held(c, p, dir, h, item, lift, t) {
  var u = h * 0.16, a, tip;
  if (item === 'chop') { a = lerp(0.9, -0.35, lift); tip = [p[0] + dir * Math.cos(a) * u * 1.3, p[1] + Math.sin(a) * u * 1.3]; ln(c, [p, tip], '#c8a060', u * 0.08);
    if (lift > 0.05) { c.strokeStyle = '#f2d58a'; c.lineWidth = Math.max(0.8, u * 0.05); for (var i = -1; i <= 1; i++) { c.beginPath(); for (var j = 0; j <= 5; j++) { var f = j / 5; c.lineTo(tip[0] + i * u * 0.05 + Math.sin(f * 7 + t / 200 + i) * u * 0.04, tip[1] + f * u * (0.25 + 0.8 * lift)); } c.stroke(); } } }
  else if (item === 'spoon' || item === 'fork') { a = lerp(1.0, -0.6, lift); tip = [p[0] + dir * Math.cos(a) * u, p[1] + Math.sin(a) * u]; ln(c, [p, tip], '#c9ccd2', u * 0.1); fe(c, tip[0], tip[1], u * 0.16, u * 0.09, '#c9ccd2', dir * a); if (lift > 0.1) fe(c, tip[0], tip[1] - u * 0.05, u * 0.1, u * 0.07, '#e8b86a'); }
  else if (item === 'ball') fe(c, p[0] + dir * u * 0.1, p[1] - u * 0.05, u * 0.2, u * 0.17, '#f7f3e8');
  else if (item === 'cup' || item === 'mug' || item === 'beer') { var ca = lift * 0.6 * dir; c.save(); c.translate(p[0] + dir * u * 0.1, p[1] - u * 0.1); c.rotate(-ca);
    if (item === 'beer') { fp(c, [[-u * 0.18, -u * 0.45], [u * 0.18, -u * 0.45], [u * 0.16, u * 0.15], [-u * 0.16, u * 0.15]], 'rgba(242,176,42,.9)'); fr(c, -u * 0.18, -u * 0.5, u * 0.36, u * 0.1, '#fffaf0'); }
    else { fp(c, [[-u * 0.2, -u * 0.25], [u * 0.2, -u * 0.25], [u * 0.15, u * 0.15], [-u * 0.15, u * 0.15]], item === 'mug' ? '#f6f2ea' : '#f4f1ea'); fe(c, 0, -u * 0.25, u * 0.2, u * 0.05, '#8a5a2a'); }
    c.restore(); }
  else if (item === 'leg') { ln(c, [p, [p[0] + dir * u * 0.15, p[1] - u * 0.35]], '#f2ead8', u * 0.12); fe(c, p[0] + dir * u * 0.25, p[1] - u * 0.6, u * 0.24, u * 0.34, '#b8681e', dir * 0.4); }
  else if (item === 'tongs') { a = lerp(0.6, 0.2, lift); tip = [p[0] + dir * Math.cos(a) * u * 1.4, p[1] + Math.sin(a) * u * 1.4]; ln(c, [p, tip], '#a8acb2', u * 0.09); ln(c, [p, [tip[0], tip[1] - u * 0.12]], '#a8acb2', u * 0.09); }
}

/* ---------------------------------------------------------------- out front
   the san phra phum: a gilded house on a post, a garland, red soda with straws, incense */
function spiritHouse(q, x, deck, hh, r) {
  var s = hh * (0.9 + r() * 0.2), base = deck - s * 0.62, bw = s * 0.32, bh = s * 0.2, by = base - s * 0.04, body = pick(r, ['#f2d27a', '#efe6d2', '#e8c060']);
  paper(q, rect(x - s * 0.05, base, s * 0.1, deck - base), '#e8e0d0', 0.8);
  paper(q, rect(x - s * 0.28, by, s * 0.56, s * 0.05), '#c8a050', 0.8);
  paper(q, rect(x - bw / 2, by - bh, bw, bh), body, 0.8);
  fr(q, x - bw * 0.14, by - bh * 0.78, bw * 0.28, bh * 0.78, '#8a1f1a'); q.strokeStyle = '#e8b84a'; q.lineWidth = 1; q.strokeRect(x - bw * 0.14, by - bh * 0.78, bw * 0.28, bh * 0.78);
  var ry = by - bh, rc = pick(r, ['#c0392b', '#2f6db0', '#2f8f5b']);
  paper(q, poly([[x - bw * 0.72, ry + s * 0.02], [x, ry - s * 0.2], [x + bw * 0.72, ry + s * 0.02]]), rc, 0.8);
  paper(q, poly([[x - bw * 0.48, ry - s * 0.09], [x, ry - s * 0.3], [x + bw * 0.48, ry - s * 0.09]]), mixc(rc, '#000000', 0.2), 0.8);
  ln(q, [[x - bw * 0.72, ry + s * 0.02], [x, ry - s * 0.2], [x + bw * 0.72, ry + s * 0.02]], '#e8b84a', 1.3);
  ln(q, [[x - bw * 0.48, ry - s * 0.09], [x, ry - s * 0.3], [x + bw * 0.48, ry - s * 0.09]], '#e8b84a', 1.3);
  ln(q, [[x, ry - s * 0.3], [x, ry - s * 0.42]], '#e8b84a', 1.6); fe(q, x, ry - s * 0.43, s * 0.02, s * 0.02, '#e8b84a');
  [-1, 1].forEach(function (k) { ln(q, [[x + k * bw * 0.72, ry + s * 0.02], [x + k * bw * 0.8, ry - s * 0.05]], '#e8b84a', 1.3); });
  /* the garland: marigolds along a hanging arc */
  for (var i = 0; i <= 8; i++) { var u = i / 8; fe(q, x - s * 0.26 + u * s * 0.52, by + s * 0.06 + Math.sin(u * Math.PI) * s * 0.07, s * 0.022, s * 0.022, i % 2 ? '#f29a1a' : '#f7c21a'); }
  /* red soda with straws, a figure on the shelf */
  for (i = 0; i < 2; i++) { var bx = x + s * (0.17 + i * 0.05); fp(q, [[bx - s * 0.015, by], [bx - s * 0.015, by - s * 0.07], [bx + s * 0.015, by - s * 0.07], [bx + s * 0.015, by]], '#d8242a'); ln(q, [[bx, by - s * 0.07], [bx + s * 0.01, by - s * 0.11]], '#f2f2f2', 0.8); }
  fe(q, x - s * 0.19, by - s * 0.04, s * 0.03, s * 0.04, '#f6f2ea'); fe(q, x - s * 0.19, by - s * 0.085, s * 0.015, s * 0.015, '#f6f2ea');
  return { x: x - s * 0.08, y: by };
}
function incense(c, sp, hh, t) { if (!sp) return; ln(c, [[sp.x, sp.y], [sp.x, sp.y - hh * 0.08]], '#8a3a1a', 1); fe(c, sp.x, sp.y - hh * 0.08, 1.2, 1.2, '#ff7a2a'); smoke(c, sp.x, sp.y - hh * 0.08, hh * 0.5, t, 0.3, 'rgba(235,230,220,.9)'); }
function plant(q, kind, x, deck, hh, r) {
  var i, a;
  if (kind === 'banana') {
    paper(q, poly([[x - hh * 0.05, deck], [x - hh * 0.035, deck - hh * 1.05], [x + hh * 0.035, deck - hh * 1.05], [x + hh * 0.05, deck]]), '#8aa860', 0.8);
    for (i = 0; i < 5; i++) { a = -2.4 + i * 0.55 + (r() - 0.5) * 0.2; q.save(); q.translate(x, deck - hh * 1.05); q.rotate(a);
      paper(q, function (p) { p.beginPath(); p.moveTo(0, 0); p.quadraticCurveTo(hh * 0.3, -hh * 0.16, hh * 0.62, -hh * 0.02); p.quadraticCurveTo(hh * 0.3, hh * 0.05, 0, 0); p.closePath(); }, i % 2 ? '#5f9a3a' : '#4f8a32', 0.6);
      ln(q, [[0, 0], [hh * 0.6, -hh * 0.03]], 'rgba(255,255,255,.3)', 1); q.restore(); }
  } else if (kind === 'bougain') {
    ln(q, [[x, deck], [x + hh * 0.05, deck - hh * 0.6], [x - hh * 0.1, deck - hh * 1.1]], '#6a4a2a', hh * 0.05);
    for (i = 0; i < 16; i++) { var bx = x + (r() - 0.5) * hh * 0.7, by = deck - hh * (0.45 + r() * 0.85); paper(q, E(bx, by, hh * 0.11, hh * 0.08), i % 3 ? (i % 2 ? '#d8247a' : '#e8408a') : '#3f7a32', 0.3); }
  } else if (kind === 'frangipani') {
    ln(q, [[x, deck], [x, deck - hh * 0.6], [x - hh * 0.25, deck - hh * 1.1]], '#8a8478', hh * 0.06); ln(q, [[x, deck - hh * 0.6], [x + hh * 0.28, deck - hh * 1.0]], '#8a8478', hh * 0.05);
    [[-0.25, 1.1], [0.28, 1.0], [0.02, 1.2]].forEach(function (p) { for (var k = 0; k < 5; k++) { a = k / 5 * TAU; q.save(); q.translate(x + p[0] * hh, deck - p[1] * hh); q.rotate(a); paper(q, E(hh * 0.12, 0, hh * 0.12, hh * 0.035), '#3f7a32', 0.3); q.restore(); }
      for (k = 0; k < 3; k++) { var fx = x + p[0] * hh + (k - 1) * hh * 0.06, fy = deck - p[1] * hh - hh * 0.06; for (var pp = 0; pp < 5; pp++) fe(q, fx + Math.cos(pp * 1.257) * hh * 0.022, fy + Math.sin(pp * 1.257) * hh * 0.022, hh * 0.022, hh * 0.013, '#fbf6ee', pp * 1.257); fe(q, fx, fy, hh * 0.012, hh * 0.012, '#f7c21a'); } });
  } else if (kind === 'chilli' || kind === 'marigold' || kind === 'basil') {
    paper(q, poly([[x - hh * 0.1, deck - hh * 0.2], [x + hh * 0.1, deck - hh * 0.2], [x + hh * 0.07, deck], [x - hh * 0.07, deck]]), '#b8642a', 0.5);
    paper(q, E(x, deck - hh * 0.3, hh * 0.15, hh * 0.13), '#3f7a32', 0.4);
    for (i = 0; i < 6; i++) fe(q, x + (r() - 0.5) * hh * 0.24, deck - hh * (0.22 + r() * 0.18), hh * (kind === 'chilli' ? 0.02 : 0.035), hh * (kind === 'chilli' ? 0.04 : 0.035), kind === 'chilli' ? '#d8242a' : kind === 'marigold' ? '#f29a1a' : '#5aa83a');
  } else if (kind === 'monstera') {
    paper(q, rect(x - hh * 0.11, deck - hh * 0.22, hh * 0.22, hh * 0.22), '#b8b4ac', 0.5);
    for (i = 0; i < 5; i++) { a = -1.4 + i * 0.7; var lx = x + Math.sin(a) * hh * 0.28, ly = deck - hh * 0.5 - Math.cos(a) * hh * 0.18; ln(q, [[x, deck - hh * 0.22], [lx, ly]], '#3f7a32', 1.4);
      paper(q, E(lx, ly, hh * 0.13, hh * 0.1, a), '#2f6a2a', 0.4); for (var k = 0; k < 3; k++) ln(q, [[lx, ly], [lx + Math.cos(a + k - 1) * hh * 0.13, ly + Math.sin(a + k - 1) * hh * 0.1]], 'rgba(0,30,0,.5)', 1); }
  } else if (kind === 'palm') {
    paper(q, poly([[x - hh * 0.12, deck - hh * 0.25], [x + hh * 0.12, deck - hh * 0.25], [x + hh * 0.08, deck], [x - hh * 0.08, deck]]), '#e8e0d0', 0.5);
    for (i = 0; i < 7; i++) { a = -1.3 + i * 0.43; var ex = x + Math.sin(a) * hh * 0.45, ey = deck - hh * 0.25 - Math.cos(a) * hh * 0.55; ln(q, [[x, deck - hh * 0.25], [lerp(x, ex, 0.5), lerp(deck - hh * 0.25, ey, 0.5) - hh * 0.1], [ex, ey]], '#4f8a32', 1.5);
      for (k = 1; k < 6; k++) { var px = lerp(x, ex, k / 6), py = lerp(deck - hh * 0.25, ey, k / 6) - Math.sin(k / 6 * Math.PI) * hh * 0.1; ln(q, [[px, py], [px + hh * 0.06, py + hh * 0.07]], '#5f9a3a', 1.2); ln(q, [[px, py], [px - hh * 0.06, py + hh * 0.07]], '#5f9a3a', 1.2); } }
  } else if (kind === 'bamboo') {
    for (i = 0; i < 5; i++) { var sx = x + (i - 2) * hh * 0.07, ht = hh * (1.2 + r() * 0.6); ln(q, [[sx, deck], [sx + (i - 2) * hh * 0.05, deck - ht]], '#7aa84a', hh * 0.035); for (k = 1; k < 5; k++) fr(q, sx + (i - 2) * hh * 0.05 * k / 5 - hh * 0.02, deck - ht * k / 5, hh * 0.04, 1.5, '#5a8a32');
      for (k = 0; k < 4; k++) { var ly2 = deck - ht * (0.5 + k * 0.15); q.save(); q.translate(sx + (i - 2) * hh * 0.05 * (0.5 + k * 0.15), ly2); q.rotate((k % 2 ? 1 : -1) * 0.9); fe(q, hh * 0.08, 0, hh * 0.09, hh * 0.018, '#5f9a3a'); q.restore(); } }
  } else if (kind === 'cactus') {
    paper(q, rect(x - hh * 0.09, deck - hh * 0.16, hh * 0.18, hh * 0.16), '#c8724a', 0.5); paper(q, E(x, deck - hh * 0.32, hh * 0.07, hh * 0.17), '#5a8a4a', 0.4); paper(q, E(x + hh * 0.09, deck - hh * 0.34, hh * 0.04, hh * 0.08), '#5a8a4a', 0.3);
  } else if (kind === 'coffee') {   /* a coffee shrub, red cherries along its branches */
    ln(q, [[x, deck], [x, deck - hh * 0.8]], '#6a4a2a', hh * 0.04);
    for (i = 0; i < 6; i++) { var yy = deck - hh * (0.25 + i * 0.1), w = hh * (0.32 - i * 0.04); ln(q, [[x - w, yy + hh * 0.04], [x, yy], [x + w, yy + hh * 0.04]], '#6a4a2a', 1.2);
      for (k = -2; k <= 2; k++) if (k) { paper(q, E(x + k * w * 0.45, yy + hh * 0.01, hh * 0.06, hh * 0.025, k * 0.2), '#2f6a2a', 0.2); if ((i + k) % 2) fe(q, x + k * w * 0.4, yy + hh * 0.04, hh * 0.018, hh * 0.018, '#c8202a'); } }
  }
}
function moto(q, x, deck, hh, col, dir, helmet) {
  var w = hh * 0.36, rw = hh * 0.12, y = deck - rw;
  [x - w, x + w].forEach(function (wx) { paper(q, E(wx, y, rw, rw), '#1a1a1e', 0.6); fe(q, wx, y, rw * 0.45, rw * 0.45, '#a8acb2'); });
  paper(q, function (p) { p.beginPath(); p.moveTo(x - w * 1.15 * dir, y - rw * 0.3); p.quadraticCurveTo(x - w * 1.1 * dir, y - rw * 2.6, x - w * 0.3 * dir, y - rw * 2.4); p.lineTo(x + w * 0.25 * dir, y - rw * 1.0); p.lineTo(x + w * 0.65 * dir, y - rw * 1.0); p.lineTo(x + w * 0.78 * dir, y - rw * 3.1); p.lineTo(x + w * 0.95 * dir, y - rw * 3.1); p.lineTo(x + w * 1.05 * dir, y - rw * 0.4); p.closePath(); }, col, 0.7);
  fp(q, [[x - w * 1.05 * dir, y - rw * 2.55], [x - w * 0.2 * dir, y - rw * 2.55], [x - w * 0.25 * dir, y - rw * 2.85], [x - w * 0.95 * dir, y - rw * 2.85]], '#1a1a1e');
  ln(q, [[x + w * 0.86 * dir, y - rw * 3.1], [x + w * 0.7 * dir, y - rw * 3.7], [x + w * 0.5 * dir, y - rw * 3.75]], '#2a2a2e', 2);
  fe(q, x + w * 0.98 * dir, y - rw * 2.8, rw * 0.22, rw * 0.3, '#fff6c0');
  if (helmet) { paper(q, function (p) { p.beginPath(); p.arc(x - w * 0.6 * dir, y - rw * 3.1, rw * 0.6, Math.PI, TAU); p.closePath(); }, helmet, 0.4); }
  return { x0: x - w - rw, x1: x + w + rw };
}
function bicycle(q, x, deck, hh, col, basket) {
  var r = hh * 0.14, y = deck - r;
  [x - hh * 0.26, x + hh * 0.26].forEach(function (wx) { q.strokeStyle = '#2a2a2e'; q.lineWidth = 2; q.beginPath(); q.arc(wx, y, r, 0, TAU); q.stroke(); });
  ln(q, [[x - hh * 0.26, y], [x - hh * 0.05, y - r * 1.4], [x + hh * 0.18, y - r * 1.4], [x + hh * 0.26, y], [x, y], [x - hh * 0.05, y - r * 1.4]], col, 2.2);
  ln(q, [[x + hh * 0.18, y - r * 1.4], [x + hh * 0.22, y - r * 1.9], [x + hh * 0.3, y - r * 1.95]], '#2a2a2e', 2); fr(q, x - hh * 0.1, y - r * 1.6, hh * 0.1, 3, '#2a1a12');
  if (basket) { paper(q, rect(x + hh * 0.24, y - r * 2.3, hh * 0.16, hh * 0.1), '#c8a060', 0.4); for (var i = 0; i < 4; i++) fe(q, x + hh * (0.26 + i * 0.04), y - r * 2.35, hh * 0.025, hh * 0.025, ['#f29a1a', '#e8408a', '#f7f0e0', '#d8242a'][i]); }
}
function songthaew(q, x, deck, hh, col) {
  var w = hh * 1.0, rw = hh * 0.13, y = deck - rw;
  paper(q, function (p) { p.beginPath(); p.moveTo(x - w, y - rw * 0.2); p.lineTo(x - w, y - hh * 0.72); p.lineTo(x + w * 0.35, y - hh * 0.72); p.lineTo(x + w * 0.5, y - hh * 0.42); p.lineTo(x + w, y - hh * 0.36); p.lineTo(x + w, y - rw * 0.2); p.closePath(); }, col, 0.9);
  fr(q, x - w * 0.95, y - hh * 0.66, w * 1.2, hh * 0.18, 'rgba(30,40,60,.55)'); for (var i = 1; i < 4; i++) fr(q, x - w * 0.95 + i * w * 0.3, y - hh * 0.66, 2, hh * 0.18, col);
  fp(q, [[x + w * 0.38, y - hh * 0.66], [x + w * 0.48, y - hh * 0.44], [x + w * 0.3, y - hh * 0.44], [x + w * 0.3, y - hh * 0.66]], 'rgba(30,40,60,.6)');
  fr(q, x - w, y - hh * 0.76, w * 1.36, hh * 0.05, mixc(col, '#ffffff', 0.3));
  [x - w * 0.6, x + w * 0.62].forEach(function (wx) { paper(q, E(wx, y, rw, rw), '#1a1a1e', 0.6); fe(q, wx, y, rw * 0.45, rw * 0.45, '#a8acb2'); });
}
/* a street plate on its pole: blue, white letters, the road's name */
function roadPlate(q, x, deck, hh, road) {
  var nm = /^(ถนน|ถ\.|ซอย|ซ\.|ทาง)/.test(road) || /road|rd\b|soi|street/i.test(road) ? road : 'ถนน' + road;
  var top = deck - hh * 1.35; fr(q, x - 1.5, top, 3, deck - top, '#8a8e94');
  q.font = '700 ' + Math.round(Math.max(9, hh * 0.13)) + 'px "Sarabun",system-ui,sans-serif'; var w = Math.min(q.measureText(nm).width + hh * 0.2, hh * 2);
  paper(q, rect(x - w / 2, top - hh * 0.1, w, hh * 0.2), '#1f5fa8', 0.6); q.strokeStyle = '#fff'; q.lineWidth = 1; q.strokeRect(x - w / 2 + 2, top - hh * 0.1 + 2, w - 4, hh * 0.2 - 4);
  txt(q, nm, x, top, hh * 0.13, '#fff', 700, 'center', w - 6);
}
/* a concrete pole with its cross-arms, and the tangle of wires that runs off it */
function pole(q, x, deck, hh, to, ty) {
  var top = deck - hh * 2.25; paper(q, poly([[x - hh * 0.05, deck], [x - hh * 0.035, top], [x + hh * 0.035, top], [x + hh * 0.05, deck]]), '#a8a49c', 0.8);
  fr(q, x - hh * 0.22, top + hh * 0.12, hh * 0.44, hh * 0.04, '#7a766e'); fr(q, x - hh * 0.16, top + hh * 0.3, hh * 0.32, hh * 0.035, '#7a766e');
  paper(q, rect(x + hh * 0.04, top + hh * 0.45, hh * 0.14, hh * 0.2), '#7a8288', 0.5);
  q.strokeStyle = 'rgba(25,25,30,.75)'; q.lineWidth = 1;
  for (var i = 0; i < 5; i++) { var y0 = top + hh * (0.12 + (i % 3) * 0.09), y1 = ty + hh * (0.05 + i * 0.05); q.beginPath(); q.moveTo(x + (i - 2) * hh * 0.08, y0); q.quadraticCurveTo((x + to) / 2, Math.max(y0, y1) + hh * (0.18 + i * 0.03), to, y1); q.stroke(); }
}
/* a sandwich board on the pavement */
function aframe(q, x, deck, hh, lines, night, icon) {
  var w = hh * 0.42, h = hh * 0.56;
  ln(q, [[x - w * 0.55, deck], [x - w * 0.4, deck - h]], '#6a4a2a', 2); ln(q, [[x + w * 0.55, deck], [x + w * 0.4, deck - h]], '#6a4a2a', 2);
  paper(q, poly([[x - w * 0.45, deck - hh * 0.06], [x - w * 0.38, deck - h], [x + w * 0.38, deck - h], [x + w * 0.45, deck - hh * 0.06]]), '#8a5a32', 0.6);
  fr(q, x - w * 0.36, deck - h + hh * 0.04, w * 0.72, h - hh * 0.13, '#22302a');
  if (lines) lines.forEach(function (s, i) { txt(q, s, x, deck - h + hh * (0.12 + i * 0.12), hh * (i ? 0.075 : 0.1), i ? '#f2e6c9' : '#f7d040', 700, 'center', w * 0.66); });
  else if (icon && DISH[icon]) DISH[icon](q, x, deck - h * 0.35, hh * 0.3);
}
/* the trade sign, readable without its words: a wooden disc with the thing itself on it */
function shingle(q, x, y, hh, kind, dir, night, alt) {
  var r = hh * 0.3, bx = x - dir * r * 1.3;
  ln(q, [[bx, y - r * 1.25], [x + dir * r * 0.2, y - r * 1.25]], '#2a1a12', 2.5); ln(q, [[bx, y - r * 0.7], [bx + dir * r * 0.8, y - r * 1.25]], '#2a1a12', 1.6);
  ln(q, [[x - r * 0.5, y - r * 1.25], [x - r * 0.5, y - r * 0.9]], '#2a1a12', 1); ln(q, [[x + r * 0.5, y - r * 1.25], [x + r * 0.5, y - r * 0.9]], '#2a1a12', 1);
  paper(q, E(x, y, r, r), night ? '#4a2a14' : '#6a3a1e', 1);
  q.strokeStyle = '#e8b84a'; q.lineWidth = 1.5; q.beginPath(); q.arc(x, y, r * 0.86, 0, TAU); q.stroke();
  var ink = '#f6e8c8', s = r * 0.9;
  if (kind === 'cafe') { fp(q, [[x - s * 0.42, y - s * 0.2], [x + s * 0.32, y - s * 0.2], [x + s * 0.22, y + s * 0.38], [x - s * 0.32, y + s * 0.38]], ink); q.strokeStyle = ink; q.lineWidth = s * 0.1; q.beginPath(); q.arc(x + s * 0.36, y + s * 0.06, s * 0.15, -1.3, 1.3); q.stroke(); fe(q, x - s * 0.05, y + s * 0.46, s * 0.55, s * 0.08, ink);
    for (var i = 0; i < 3; i++) { q.lineWidth = s * 0.07; q.beginPath(); q.moveTo(x - s * 0.22 + i * s * 0.18, y - s * 0.3); q.quadraticCurveTo(x - s * 0.32 + i * s * 0.18, y - s * 0.48, x - s * 0.2 + i * s * 0.18, y - s * 0.62); q.stroke(); } }
  else if (kind === 'bar') { fp(q, [[x - s * 0.36, y - s * 0.36], [x + s * 0.2, y - s * 0.36], [x + s * 0.16, y + s * 0.52], [x - s * 0.32, y + s * 0.52]], '#f2b02a'); fe(q, x - s * 0.08, y - s * 0.4, s * 0.34, s * 0.16, ink); fe(q, x - s * 0.24, y - s * 0.48, s * 0.14, s * 0.12, ink); q.strokeStyle = ink; q.lineWidth = s * 0.12; q.beginPath(); q.arc(x + s * 0.24, y + s * 0.06, s * 0.2, -1.4, 1.4); q.stroke(); }
  else if (kind === 'noodle') { fp(q, [[x - s * 0.6, y - s * 0.02], [x + s * 0.6, y - s * 0.02], [x + s * 0.3, y + s * 0.42], [x - s * 0.3, y + s * 0.42]], ink); fe(q, x, y - s * 0.02, s * 0.6, s * 0.12, '#c8642a'); ln(q, [[x - s * 0.1, y], [x + s * 0.45, y - s * 0.7]], ink, s * 0.07); ln(q, [[x + s * 0.02, y], [x + s * 0.58, y - s * 0.62]], ink, s * 0.07);
    for (i = 0; i < 3; i++) { q.strokeStyle = '#f2d58a'; q.lineWidth = s * 0.05; q.beginPath(); q.moveTo(x + s * (0.15 + i * 0.05), y - s * 0.3); q.quadraticCurveTo(x + s * (0.05 + i * 0.05), y - s * 0.15, x + s * (0.12 + i * 0.05), y); q.stroke(); } }
  else if (kind === 'bakery') { if (alt) { fp(q, [[x - s * 0.4, y], [x + s * 0.4, y], [x + s * 0.3, y + s * 0.46], [x - s * 0.3, y + s * 0.46]], '#e8a0b8'); paper(q, function (p) { p.beginPath(); p.arc(x, y, s * 0.42, Math.PI, TAU); p.closePath(); }, ink, 0.2); fe(q, x, y - s * 0.48, s * 0.1, s * 0.1, '#d8242a'); }
    else for (i = -2; i <= 2; i++) fe(q, x + i * s * 0.2, y + s * 0.1 - (2 - Math.abs(i)) * s * 0.08, s * 0.17, s * (0.17 + (2 - Math.abs(i)) * 0.05), i % 2 ? '#d8902a' : '#f2c25a', i * 0.35); }
  else if (kind === 'wok') { fp(q, [[x - s * 0.6, y - s * 0.05], [x + s * 0.45, y - s * 0.05], [x + s * 0.3, y + s * 0.3], [x - s * 0.45, y + s * 0.3]], '#2a2a2e'); ln(q, [[x + s * 0.4, y - s * 0.05], [x + s * 0.72, y - s * 0.25]], ink, s * 0.1); for (i = 0; i < 4; i++) fe(q, x - s * 0.3 + i * s * 0.15, y - s * (0.2 + (i % 2) * 0.18), s * 0.06, s * 0.05, ['#f2c24a', '#5aa83a', '#d9342b', '#f6f2ea'][i]);
    for (i = 0; i < 3; i++) fp(q, [[x - s * 0.3 + i * s * 0.25, y + s * 0.62], [x - s * 0.22 + i * s * 0.25, y + s * 0.35], [x - s * 0.14 + i * s * 0.25, y + s * 0.62]], '#ff8a2a'); }
  else { /* a plate, fork and spoon */ fe(q, x, y + s * 0.05, s * 0.42, s * 0.42, ink); fe(q, x, y + s * 0.05, s * 0.28, s * 0.28, night ? '#4a2a14' : '#6a3a1e'); fe(q, x, y + s * 0.05, s * 0.24, s * 0.24, ink);
    ln(q, [[x - s * 0.62, y + s * 0.5], [x - s * 0.62, y - s * 0.35]], ink, s * 0.08); for (i = -1; i <= 1; i++) ln(q, [[x - s * 0.62 + i * s * 0.06, y - s * 0.2], [x - s * 0.62 + i * s * 0.06, y - s * 0.45]], ink, s * 0.04);
    ln(q, [[x + s * 0.62, y + s * 0.5], [x + s * 0.62, y - s * 0.1]], ink, s * 0.08); fe(q, x + s * 0.62, y - s * 0.25, s * 0.09, s * 0.17, ink); }
}
/* khom: Lanna paper lanterns on cords, each a pendulum */
function khom(c, x, y, hh, t, k, col, night, len) {
  var th = 0.16 * Math.cos(t / 620 + k * 1.3), L = hh * (len || 0.1), lx = x + Math.sin(th) * L, ly = y + Math.cos(th) * L, r = hh * 0.065;
  ln(c, [[x, y], [lx, ly]], 'rgba(40,20,30,.8)', 1);
  if (night) glow(c, lx, ly + r, r * 3.4, '255,170,80', 0.5 + 0.12 * Math.sin(t / 300 + k));
  fe(c, lx, ly + r, r * 0.85, r, col); fp(c, [[lx - r * 0.5, ly + r * 0.15], [lx + r * 0.5, ly + r * 0.15], [lx, ly - r * 0.15]], '#e8b84a'); fr(c, lx - r * 0.55, ly + r * 1.75, r * 1.1, r * 0.2, '#e8b84a');
  ln(c, [[lx, ly + r * 1.95], [lx + Math.sin(th) * r * 0.6, ly + r * 2.9]], '#e8b84a', 1);
}
/* fairy lights on a catenary, each bulb breathing on its own phase */
function fairy(c, xa, ya, xb, yb, sag, hh, t, night, on) {
  var n = Math.max(4, Math.round(Math.abs(xb - xa) / (hh * 0.18)));
  c.strokeStyle = 'rgba(30,25,20,.7)'; c.lineWidth = 0.8; c.beginPath();
  for (var i = 0; i <= n; i++) { var u = i / n, x = lerp(xa, xb, u), y = lerp(ya, yb, u) + Math.sin(u * Math.PI) * sag; i ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
  for (i = 1; i < n; i++) { u = i / n; x = lerp(xa, xb, u); y = lerp(ya, yb, u) + Math.sin(u * Math.PI) * sag + 2;
    var a = on ? 0.65 + 0.35 * Math.sin(t / 400 + i * 2.1) : 0.25, col = ['255,214,120', '255,180,90', '255,240,190'][i % 3];
    if (night && on) glow(c, x, y, hh * 0.09, col, 0.55 * a);
    fe(c, x, y, Math.max(1.3, hh * 0.018), Math.max(1.6, hh * 0.024), on ? 'rgba(' + col + ',' + (0.55 + 0.45 * a) + ')' : 'rgba(200,200,190,.6)'); }
}
function dog(c, x, deck, hh, t, mode, col, dir) {
  var s = hh * 0.34;
  if (mode === 'sleep') { var br = 1 + 0.035 * Math.sin(t / 900);
    c.save(); c.translate(x, deck - s * 0.18); c.scale(1, br); fe(c, 0, 0, s * 0.55, s * 0.2, col); c.restore();
    fe(c, x + dir * s * 0.42, deck - s * 0.12, s * 0.17, s * 0.12, col); fe(c, x + dir * s * 0.36, deck - s * 0.2, s * 0.06, s * 0.09, mixc(col, '#000000', 0.25), dir * 0.6);
    ln(c, [[x - dir * s * 0.5, deck - s * 0.1], [x - dir * s * 0.3, deck - s * 0.02], [x, deck - s * 0.02]], col, s * 0.07);
    if (Math.sin(t / 1800) > 0.3) txt(c, 'z', x + dir * s * 0.55, deck - s * 0.5 - ((t / 40) % 10), s * 0.25, 'rgba(255,255,255,.7)', 700);
    return; }
  var wag = Math.sin(t / 120) * 0.6;
  fe(c, x, deck - s * 0.45, s * 0.32, s * 0.18, col);
  ln(c, [[x - s * 0.2, deck - s * 0.4], [x - s * 0.22, deck]], col, s * 0.1); ln(c, [[x + s * 0.18, deck - s * 0.4], [x + s * 0.2, deck]], col, s * 0.1);
  fe(c, x + dir * s * 0.32, deck - s * 0.68, s * 0.14, s * 0.15, col); fe(c, x + dir * s * 0.45, deck - s * 0.64, s * 0.08, s * 0.06, col);
  fp(c, [[x + dir * s * 0.24, deck - s * 0.78], [x + dir * s * 0.3, deck - s * 0.95], [x + dir * s * 0.36, deck - s * 0.78]], mixc(col, '#000000', 0.25));
  fe(c, x + dir * s * 0.38, deck - s * 0.72, 1, 1, '#1a1a1a');
  ln(c, [[x - dir * s * 0.3, deck - s * 0.5], [x - dir * s * (0.42 + 0.1 * Math.cos(wag)), deck - s * (0.62 + 0.15 * Math.sin(wag))]], col, s * 0.07);
}
function cat(c, x, y, hh, t, col, dir) {
  var s = hh * 0.22, sw = Math.sin(t / 700) * 0.5;
  fe(c, x, y - s * 0.4, s * 0.3, s * 0.42, col); fe(c, x + dir * s * 0.1, y - s * 0.95, s * 0.22, s * 0.2, col);
  fp(c, [[x + dir * s * -0.08, y - s * 1.05], [x - dir * s * 0.04, y - s * 1.3], [x + dir * s * 0.1, y - s * 1.12]], col); fp(c, [[x + dir * s * 0.14, y - s * 1.1], [x + dir * s * 0.26, y - s * 1.3], [x + dir * s * 0.3, y - s * 1.05]], col);
  fe(c, x + dir * s * 0.2, y - s * 0.97, 1, 1, '#d8e84a');
  c.strokeStyle = col; c.lineWidth = s * 0.12; c.lineCap = 'round'; c.beginPath(); c.moveTo(x - dir * s * 0.25, y - s * 0.1); c.quadraticCurveTo(x - dir * s * (0.7 + sw * 0.2), y - s * 0.1, x - dir * s * (0.6 + sw * 0.3), y - s * (0.6 + sw * 0.2)); c.stroke();
}
function hens(c, x, deck, hh, t) {
  for (var i = 0; i < 2; i++) { var hx2 = x + i * hh * 0.32, peck = Math.max(0, Math.sin(t / 380 + i * 2)), dir = i ? -1 : 1, s = hh * 0.18;
    fe(c, hx2, deck - s * 0.5, s * 0.4, s * 0.3, i ? '#b8642a' : '#f2ead8'); fp(c, [[hx2 - dir * s * 0.35, deck - s * 0.6], [hx2 - dir * s * 0.65, deck - s * 0.95], [hx2 - dir * s * 0.45, deck - s * 0.45]], i ? '#3a2a1a' : '#d8d0c0');
    var hdx = hx2 + dir * s * (0.35 + peck * 0.15), hdy = deck - s * (0.85 - peck * 0.6); fe(c, hdx, hdy, s * 0.16, s * 0.16, i ? '#b8642a' : '#f2ead8'); fe(c, hdx, hdy - s * 0.16, s * 0.07, s * 0.07, '#d8242a'); fp(c, [[hdx + dir * s * 0.14, hdy - s * 0.03], [hdx + dir * s * 0.3, hdy + s * 0.03], [hdx + dir * s * 0.14, hdy + s * 0.06]], '#f2b02a');
    ln(c, [[hx2, deck - s * 0.25], [hx2, deck]], '#e8a02a', 1.2); }
}
function moth(c, x, y, hh, t) { var a = t / 300, mx = x + Math.cos(a) * hh * 0.12, my = y + Math.sin(a * 2) * hh * 0.06, f = Math.abs(Math.sin(t / 40)); glow(c, x, y, hh * 0.3, '255,230,170', 0.35); fe(c, x, y, hh * 0.04, hh * 0.05, '#fff2c8'); fe(c, mx - f * 3, my, 3 * f + 1, 2, '#d8d0c0'); fe(c, mx + f * 3, my, 3 * f + 1, 2, '#d8d0c0'); }
/* a water jar for passers-by under its little roof, the old Lanna courtesy */
function waterJar(q, x, deck, hh) {
  paper(q, rect(x - hh * 0.18, deck - hh * 0.32, hh * 0.36, hh * 0.05), '#7a4a2a', 0.5); ln(q, [[x - hh * 0.15, deck - hh * 0.3], [x - hh * 0.15, deck]], '#7a4a2a', 2); ln(q, [[x + hh * 0.15, deck - hh * 0.3], [x + hh * 0.15, deck]], '#7a4a2a', 2);
  paper(q, E(x, deck - hh * 0.46, hh * 0.13, hh * 0.15), '#a8582a', 0.6); fe(q, x, deck - hh * 0.6, hh * 0.08, hh * 0.025, '#7a3a1a'); fe(q, x + hh * 0.04, deck - hh * 0.64, hh * 0.04, hh * 0.02, '#c8a060');
  ln(q, [[x - hh * 0.2, deck - hh * 0.32], [x - hh * 0.2, deck - hh * 0.85]], '#6a3a1e', 2); ln(q, [[x + hh * 0.2, deck - hh * 0.32], [x + hh * 0.2, deck - hh * 0.85]], '#6a3a1e', 2);
  paper(q, poly([[x - hh * 0.3, deck - hh * 0.8], [x, deck - hh * 1.0], [x + hh * 0.3, deck - hh * 0.8]]), '#8a3a24', 0.6); kalae(q, x, deck - hh * 1.0, hh * 0.1);
}
/* yellow flags with the red word เจ: vegetarian food is served */
function jFlag(q, x, deck, hh) { ln(q, [[x, deck], [x, deck - hh * 1.2]], '#c8a060', 2); paper(q, rect(x + 1, deck - hh * 1.18, hh * 0.3, hh * 0.4), '#f7d020', 0.5); txt(q, 'เจ', x + 1 + hh * 0.15, deck - hh * 0.98, hh * 0.22, '#d8242a', 800); }

/* ---------------------------------------------------------------- the buildings
   each: geo (its box, its open front, where its board hangs), back (shell, upper floors, the room
   behind the counter), front (posts, awning, glass), shut (what closes it) */
var WALLS = ['#eadcbc', '#cfe2d4', '#f2cdb0', '#dcd2ea', '#c2d8ea', '#ece4d0', '#f2d47e', '#b4cfa6', '#e0b0a8', '#cdc6bc', '#f4e2c8', '#bfe0dc'];
var AWN = [['#c0392b', '#f6f2ea'], ['#2f6db0', '#f6f2ea'], ['#2f8f5b', '#f6f2ea'], ['#e8b84a', '#a8241c'], ['#d8642a', '#f6f2ea'], ['#7a3a8a', '#f6f2ea'], ['#1f6a6a', '#f2d47e']];
var TEAK = ['#6b3a1e', '#7a4424', '#5a3018', '#8a5430'];
function rollShutter(q, x0, x1, y0, y1, col) {
  paper(q, rect(x0, y0, x1 - x0, y1 - y0), col || '#a8acb0', 0.8);
  for (var y = y0 + 3; y < y1; y += 4) fr(q, x0, y, x1 - x0, 1, 'rgba(0,0,0,.16)');
  fr(q, (x0 + x1) / 2 - 6, y1 - 6, 12, 3, '#5a5e64');
}
function awning(q, x0, x1, y, d, cols, hh) {
  var n = Math.max(4, Math.round((x1 - x0) / (hh * 0.32))), sw = (x1 - x0) / n;
  paper(q, function (p) { p.beginPath(); p.moveTo(x0 - hh * 0.06, y); p.lineTo(x1 + hh * 0.06, y); p.lineTo(x1 + hh * 0.12, y + d); for (var i = n; i > 0; i--) p.arc(x0 + (i - 0.5) * sw, y + d, sw / 2, 0, Math.PI); p.lineTo(x0 - hh * 0.12, y + d); p.closePath(); }, cols[0], 1.2);
  q.save(); q.beginPath(); q.moveTo(x0 - hh * 0.06, y); q.lineTo(x1 + hh * 0.06, y); q.lineTo(x1 + hh * 0.12, y + d + sw / 2); q.lineTo(x0 - hh * 0.12, y + d + sw / 2); q.closePath(); q.clip();
  for (var i = 0; i < n; i += 2) fp(q, [[x0 + i * sw, y], [x0 + (i + 1) * sw, y], [x0 + (i + 1) * sw + hh * 0.02, y + d + sw], [x0 + i * sw - hh * 0.02, y + d + sw]], cols[1]);
  q.restore(); fr(q, x0 - hh * 0.08, y, x1 - x0 + hh * 0.16, 2, 'rgba(0,0,0,.25)');
}
function tinRoof(q, x0, x1, y, d, col, hh) {
  paper(q, poly([[x0 - hh * 0.1, y], [x1 + hh * 0.1, y], [x1 + hh * 0.18, y + d], [x0 - hh * 0.18, y + d]]), col, 1);
  for (var x = x0; x < x1 + hh * 0.1; x += hh * 0.08) ln(q, [[x, y + 1], [x + (x - (x0 + x1) / 2) * 0.03, y + d - 1]], 'rgba(0,0,0,.15)', 1);
}
/* a Lanna roof in two tiers with kalae at its gables */
function lannaRoof(q, x0, x1, eave, top, col, gold) {
  var w = x1 - x0, m = (x0 + x1) / 2, h = eave - top;
  paper(q, poly([[x0 - w * 0.05, eave], [x0 + w * 0.12, top + h * 0.42], [x1 - w * 0.12, top + h * 0.42], [x1 + w * 0.05, eave]]), col, 1.4);
  paper(q, poly([[x0 + w * 0.1, top + h * 0.5], [x0 + w * 0.28, top], [x1 - w * 0.28, top], [x1 - w * 0.1, top + h * 0.5]]), mixc(col, '#000000', 0.12), 1.5);
  ln(q, [[x0 - w * 0.05, eave], [x1 + w * 0.05, eave]], gold || '#e8b84a', 1.6);
  kalae(q, x0 + w * 0.28, top, h * 0.32); kalae(q, x1 - w * 0.28, top, h * 0.32);
}
function tree(q, x, deck, hh, top, r, night) {
  paper(q, poly([[x - hh * 0.12, deck], [x - hh * 0.06, deck - hh * 1.1], [x - hh * 0.4, top + hh * 0.5], [x - hh * 0.32, top + hh * 0.45], [x, deck - hh * 1.2], [x + hh * 0.3, top + hh * 0.42], [x + hh * 0.38, top + hh * 0.48], [x + hh * 0.07, deck - hh * 1.1], [x + hh * 0.12, deck]]), night ? '#3a2a1e' : '#6a4a2e', 1);
  var g = night ? ['#1d3326', '#244030', '#1a2c22'] : ['#4f8a42', '#5f9a4a', '#3f7a3a'];
  for (var i = 0; i < 9; i++) { var a = i / 9 * Math.PI, cx = x + Math.cos(a) * hh * 0.85 * (0.6 + r() * 0.4), cy = top + hh * 0.35 - Math.sin(a) * hh * 0.22 + r() * hh * 0.1;
    paper(q, function (p) { K.circ(p, cx, cy, hh * (0.3 + r() * 0.12), i + 3); }, g[i % 3], 0.8); }
  return { x0: x - hh * 1.1, x1: x + hh * 1.1, y: top + hh * 0.45 };
}
/* the room behind the counter: tiles, the menu board, a drinks cooler, a fan */
function room(q, S, L, x0, x1, y0, style) {
  var hh = S.hh, deck = S.deck, w = x1 - x0, wc = style === 'teak' ? '#8a5a32' : style === 'bamboo' ? '#c8a868' : style === 'concrete' ? '#c8c4bc' : mixc(L.wall || '#eadcbc', '#ffffff', 0.45);
  paper(q, rect(x0, y0, w, deck - y0), wc, 0.4);
  if (style === 'tile') { fr(q, x0, deck - hh * 0.62, w, hh * 0.62, '#f2f2ee'); q.strokeStyle = 'rgba(120,140,150,.35)'; q.lineWidth = 0.7; for (var x = x0; x < x1; x += hh * 0.12) { q.beginPath(); q.moveTo(x, deck - hh * 0.62); q.lineTo(x, deck); q.stroke(); } for (var y = deck - hh * 0.62; y < deck; y += hh * 0.12) { q.beginPath(); q.moveTo(x0, y); q.lineTo(x1, y); q.stroke(); } }
  if (style === 'teak') for (x = x0; x < x1; x += hh * 0.16) fr(q, x, y0, 1, deck - y0, 'rgba(0,0,0,.2)');
  if (style === 'bamboo') { q.strokeStyle = 'rgba(90,60,20,.35)'; q.lineWidth = 1; for (x = x0 - hh; x < x1; x += hh * 0.1) { q.beginPath(); q.moveTo(x, deck); q.lineTo(x + hh * 0.8, y0); q.stroke(); q.beginPath(); q.moveTo(x, y0); q.lineTo(x + hh * 0.8, deck); q.stroke(); } }
  if (style === 'concrete') for (x = x0 + hh * 0.3; x < x1; x += hh * 0.6) for (y = y0 + hh * 0.2; y < deck; y += hh * 0.3) fe(q, x, y, 1.2, 1.2, 'rgba(0,0,0,.25)');
  q.fillStyle = 'rgba(0,0,0,.12)'; q.fillRect(x0, y0, w, hh * 0.06);
}
/* the board on the back wall shows the trade's dishes as pictures */
function menuBoard(q, x, y, hh, dishes, kind) {
  var w = hh * 1.15, h = hh * 0.42, dark = kind === 'chalk', n = Math.min(3, dishes.length);
  paper(q, rect(x - w / 2, y, w, h), dark ? '#24302a' : '#fbf8ee', 0.5); q.strokeStyle = dark ? '#8a6a3a' : '#c0392b'; q.lineWidth = 1.5; q.strokeRect(x - w / 2 + 2, y + 2, w - 4, h - 4);
  for (var i = 0; i < n; i++) { var dx = x - w / 2 + w * (i + 0.5) / n, k = dishes[i]; if (DISH[k] && k !== 'laptop' && k !== 'book') DISH[k](q, dx, y + h * 0.8, hh * 0.26); }
}
function cooler(q, x, deck, hh, lit) {
  var w = hh * 0.42, h = hh * 1.05, y = deck - h;
  paper(q, rect(x - w / 2, y, w, h), '#e8eaee', 0.8); fr(q, x - w / 2 + 3, y + hh * 0.12, w - 6, h - hh * 0.2, lit ? '#eaf6ff' : '#a8c0d0');
  fr(q, x - w / 2, y, w, hh * 0.1, '#2f6db0');
  for (var s = 0; s < 4; s++) { var sy = y + hh * (0.32 + s * 0.2); fr(q, x - w / 2 + 3, sy, w - 6, 1.5, '#9aa0a8'); for (var b = 0; b < 4; b++) { var bx = x - w / 2 + 6 + b * (w - 12) / 3.5; fp(q, [[bx - 2.5, sy], [bx - 2.5, sy - hh * 0.1], [bx - 1, sy - hh * 0.14], [bx + 1, sy - hh * 0.14], [bx + 2.5, sy - hh * 0.1], [bx + 2.5, sy]], ['#3a8a3a', '#d8242a', '#f2b02a', '#e8eef2', '#5a3212', '#2f6db0'][(b + s * 2) % 6]); } }
  ln(q, [[x + w / 2 - 5, y + hh * 0.3], [x + w / 2 - 5, y + hh * 0.6]], '#9aa0a8', 2);
}
function ceilingFan(c, x, y, hh, t) {
  ln(c, [[x, y], [x, y + hh * 0.1]], '#4a4e54', 1.5); fe(c, x, y + hh * 0.12, hh * 0.04, hh * 0.025, '#4a4e54');
  for (var i = 0; i < 3; i++) { var a = t / 90 + i * TAU / 3, l = Math.cos(a) * hh * 0.32; fe(c, x + l / 2, y + hh * 0.12, Math.abs(l) / 2 + 1, hh * 0.02, 'rgba(90,70,50,.85)'); }
}
function tube(q, x, y, hh, on) { fr(q, x - hh * 0.3, y, hh * 0.6, hh * 0.04, on ? '#ffffff' : '#c8ccd0'); if (on) glow(q, x, y + hh * 0.02, hh * 0.7, '230,245,255', 0.4); }
var BLD = {
  /* the Chiang Mai shophouse: two or three storeys, louvres or grilles upstairs, a roll-up shutter over an open front */
  shop: {
    geo: function (L, S, r) { var hh = S.hh; L.floors = +wpick(r, { 1: 0.25, 2: 0.4, 3: 0.35 }); L.gf = hh * 1.32; L.oy = S.deck - L.gf; L.uh = L.floors === 2 ? hh * 0.44 : hh * 0.3; L.top = L.oy - hh * 0.28 - (L.floors - 1) * L.uh - hh * 0.1;
      L.style = r() < 0.3 ? 'wood' : r() < 0.2 ? 'mosaic' : 'concrete'; L.roofCol = pick(r, ['#8a3a24', '#5a8ab0', '#b8643a', '#6a6e74', '#3a6a5a']); L.nb = r() < 0.75 ? [pick(r, WALLS), pick(r, WALLS), 0.7 + r() * 0.5, 0.6 + r() * 0.4] : null;
      L.ox0 = L.bx0 + hh * 0.1; L.ox1 = L.bx1 - hh * 0.1; L.bays = L.bx1 - L.bx0 > hh * 5.2 ? 3 : 2; L.signY = L.oy - hh * 0.3; L.wall = pick(r, WALLS); L.awn = r() < 0.6 ? pick(r, AWN) : null; L.tin = !L.awn && r() < 0.6 ? pick(r, ['#5a8ab0', '#b8643a', '#8a9aa8', '#3a7a5a']) : null;
      L.win = L.style === 'wood' ? pick(r, ['louvre', 'shutters']) : pick(r, ['louvre', 'glass', 'grille', 'shutters']); if (L.style === 'wood') L.wall = pick(r, TEAK); L.winCol = pick(r, ['#5a7a6a', '#7a4a2a', '#3a5a8a', '#8a6a3a', '#a8402a']); L.balcony = r() < 0.5; L.ac = r() < 0.6; L.vent = r() < 0.5; L.lit = [r() < 0.5, r() < 0.5, r() < 0.5]; L.inner = 'tile'; },
    back: function (q, S, L) {
      var hh = S.hh, x0 = L.bx0, x1 = L.bx1, w = x1 - x0, bay = w / L.bays, f, b;
      if (L.nb) [[-1, L.nb[0], L.nb[2]], [1, L.nb[1], L.nb[3]]].forEach(function (n) { var nw = hh * 0.55, nx = n[0] < 0 ? x0 - nw : x1, nt = S.deck - hh * (n[0] < 0 ? 1.55 + n[2] * 0.6 : 1.3 + n[2] * 0.4);
        paper(q, rect(nx, nt, nw, S.deck - nt), mixc(n[1], '#8a8478', 0.25), 0.8); fr(q, nx, nt, nw, hh * 0.06, mixc(n[1], '#000000', 0.25)); rollShutter(q, nx + (n[0] < 0 ? hh * 0.06 : 0), nx + nw - (n[0] < 0 ? 0 : hh * 0.06), S.deck - hh * 1.2, S.deck, '#9aa0a6');
        if (S.deck - nt > hh * 1.7) { fr(q, nx + hh * 0.08, nt + hh * 0.15, nw - hh * 0.16, hh * 0.22, '#3a4a5a'); if (S.night && n[2] > 0.95) L.glows.push([nx + hh * 0.08, nt + hh * 0.15, nw - hh * 0.16, hh * 0.22]); } });
      if (L.floors === 1) { paper(q, poly([[x0 - hh * 0.18, L.top + hh * 0.06], [x0 + hh * 0.45, L.top - hh * 0.36], [x1 - hh * 0.45, L.top - hh * 0.36], [x1 + hh * 0.18, L.top + hh * 0.06]]), L.roofCol, 1.4); for (var rx = x0 + hh * 0.3; rx < x1 - hh * 0.2; rx += hh * 0.12) ln(q, [[rx, L.top - hh * 0.34], [rx + (rx - (x0 + x1) / 2) * 0.06, L.top + hh * 0.04]], 'rgba(0,0,0,.14)', 1); }
      paper(q, rect(x0, L.top, w, S.deck - L.top), L.wall, 1.4);
      if (L.style === 'wood') for (var px0 = x0 + hh * 0.1; px0 < x1; px0 += hh * 0.11) fr(q, px0, L.top + hh * 0.1, 1, L.oy - L.top - hh * 0.38, 'rgba(0,0,0,.25)');
      if (L.style === 'mosaic') { q.save(); q.globalAlpha = 0.35; for (var my0 = L.top + hh * 0.12; my0 < L.oy - hh * 0.3; my0 += hh * 0.05) for (var mx0 = x0 + ((my0 / (hh * 0.05)) % 2) * hh * 0.025; mx0 < x1; mx0 += hh * 0.05) fr(q, mx0, my0, hh * 0.045, hh * 0.045, ((mx0 * 7 + my0 * 3) | 0) % 3 ? mixc(L.wall, '#ffffff', 0.4) : mixc(L.wall, '#000000', 0.15)); q.restore(); }
      fr(q, x0 - 3, L.top, w + 6, hh * 0.1, mixc(L.wall, '#000000', 0.18));
      if (L.vent) for (b = 0; b < L.bays; b++) for (var k = 0; k < 4; k++) { var vx = x0 + bay * (b + 0.5) + (k - 1.5) * hh * 0.09; q.strokeStyle = mixc(L.wall, '#000000', 0.3); q.lineWidth = 1; q.strokeRect(vx - hh * 0.035, L.top + hh * 0.015, hh * 0.07, hh * 0.07); q.beginPath(); q.arc(vx, L.top + hh * 0.05, hh * 0.025, 0, TAU); q.stroke(); }
      for (f = 1; f < L.floors; f++) {
        var fy = L.oy - hh * 0.28 - f * L.uh; fr(q, x0, fy + L.uh - 2, w, 3, mixc(L.wall, '#000000', 0.14));
        for (b = 0; b < L.bays; b++) {
          var wx = x0 + bay * b + bay * 0.16, ww = bay * 0.68, wy = fy + L.uh * 0.16, wh = L.uh * 0.62, lit = S.night && L.lit[(b + f) % 3]; if (lit) L.glows.push([wx, wy, ww, wh]);
          paper(q, rect(wx - 2, wy - 2, ww + 4, wh + 4), mixc(L.wall, '#000000', 0.25), 0.5);
          fr(q, wx, wy, ww, wh, lit ? '#ffd88a' : '#3a4a5a');
          if (L.win === 'louvre' || L.win === 'shutters') { var lw = L.win === 'shutters' ? ww * 0.5 : ww; for (var y = wy + 2; y < wy + wh; y += 3) { fr(q, wx, y, lw * (L.win === 'shutters' ? 0.5 : 1), 1.6, L.winCol); if (L.win === 'shutters') fr(q, wx + ww - lw * 0.5, y, lw * 0.5, 1.6, L.winCol); } }
          else { fr(q, wx + ww / 2 - 1, wy, 2, wh, '#c8ccd0'); fr(q, wx, wy + wh * 0.5, ww, 1.5, '#c8ccd0'); fr(q, wx + 2, wy + 2, ww * 0.3, wh * 0.4, 'rgba(255,255,255,.18)'); }
          if (L.win === 'grille') { q.strokeStyle = '#f2f2ee'; q.lineWidth = 1.2; for (var gx = wx; gx < wx + ww; gx += wh * 0.5) { q.beginPath(); q.moveTo(gx, wy + wh / 2); q.lineTo(gx + wh * 0.25, wy); q.lineTo(gx + wh * 0.5, wy + wh / 2); q.lineTo(gx + wh * 0.25, wy + wh); q.closePath(); q.stroke(); } }
        }
        if (f === 1 && L.balcony && L.floors > 1) { var by = L.oy - hh * 0.28 - hh * 0.04; fr(q, x0 + 4, by - hh * 0.2, w - 8, 2, '#5a5e64'); for (var bx = x0 + 6; bx < x1 - 6; bx += hh * 0.07) fr(q, bx, by - hh * 0.2, 1.2, hh * 0.2, '#5a5e64'); for (b = 0; b < 3; b++) { var px = x0 + w * (0.2 + b * 0.3); paper(q, rect(px - hh * 0.06, by - hh * 0.1, hh * 0.12, hh * 0.1), '#b8642a', 0.3); paper(q, E(px, by - hh * 0.16, hh * 0.1, hh * 0.08), b === 1 ? '#d8247a' : '#3f7a32', 0.3); } }
      }
      if (L.ac) { var ax = x0 + w * (L.floors > 2 ? 0.8 : 0.12), ay = L.oy - hh * 0.28 - L.uh * 0.95; paper(q, rect(ax - hh * 0.14, ay, hh * 0.28, hh * 0.18), '#e8eaee', 0.5); q.strokeStyle = '#9aa0a8'; q.lineWidth = 1; q.beginPath(); q.arc(ax - hh * 0.03, ay + hh * 0.09, hh * 0.065, 0, TAU); q.stroke(); }
      fr(q, x0, L.oy - hh * 0.28, w, hh * 0.28, mixc(L.wall, '#000000', 0.1));
      room(q, S, L, L.ox0, L.ox1, L.oy, L.inner);
      fr(q, L.ox0, L.oy, L.ox1 - L.ox0, hh * 0.09, '#8a8e94'); for (var sx = L.ox0; sx < L.ox1; sx += 3) fr(q, sx, L.oy, 1, hh * 0.09, 'rgba(0,0,0,.15)');
    },
    front: function (q, S, L) {
      var hh = S.hh, w = L.bx1 - L.bx0, bay = w / L.bays;
      for (var b = 0; b <= L.bays; b++) { var px = b === 0 ? L.bx0 : b === L.bays ? L.bx1 - hh * 0.1 : L.bx0 + bay * b - hh * 0.05; paper(q, rect(px, L.oy - 1, hh * 0.1, S.deck - L.oy + 1), mixc(L.wall, '#000000', 0.08), 0.6); }
      if (L.awn) awning(q, L.ox0, L.ox1, L.oy - hh * 0.02, hh * 0.16, L.awn, hh);
      else if (L.tin) tinRoof(q, L.ox0, L.ox1, L.oy - hh * 0.04, hh * 0.12, L.tin, hh);
    },
    shut: function (q, S, L) { var hh = S.hh, w = L.bx1 - L.bx0, bay = w / L.bays; if (L.style === 'wood') { BLD.teak.shut(q, S, cp(L, { wood: L.wall })); return; } for (var b = 0; b < L.bays; b++) rollShutter(q, L.bx0 + bay * b + hh * 0.06, L.bx0 + bay * (b + 1) - hh * 0.04, L.oy + hh * 0.08, S.deck, pick(K.rnd(S.seed + b), ['#a8acb0', '#9aa4ac', '#b0a89c', '#6a8aa8'])); }
  },
  /* a teak house on posts: dining underneath, plank walls and a two-tier Lanna roof above */
  teak: {
    geo: function (L, S, r) { var hh = S.hh; L.oy = S.deck - hh * 1.3; L.top = S.deck - hh * 2.3; L.ox0 = L.bx0 + hh * 0.1; L.ox1 = L.bx1 - hh * 0.1; L.signY = L.oy - hh * 0.12; L.wood = pick(r, TEAK); L.roofCol = pick(r, ['#8a3a24', '#6a4a3a', '#a8432f', '#5a3a2a']); L.posts = Math.max(3, Math.round((L.bx1 - L.bx0) / (hh * 1.6)) + 1); L.inner = r() < 0.5 ? 'teak' : 'open'; L.wall = '#c8a070'; },
    back: function (q, S, L) {
      var hh = S.hh, x0 = L.bx0, x1 = L.bx1, w = x1 - x0, uy = L.oy - hh * 0.55;
      if (L.inner === 'teak') room(q, S, L, L.ox0, L.ox1, L.oy, 'teak');
      paper(q, rect(x0, uy, w, hh * 0.55), L.wood, 1.2);
      for (var x = x0 + hh * 0.08; x < x1; x += hh * 0.1) fr(q, x, uy, 1, hh * 0.55, 'rgba(0,0,0,.25)');
      for (var i = 0; i < 3; i++) { var wx = x0 + w * (0.18 + i * 0.32), ww = hh * 0.36; fr(q, wx - ww / 2, uy + hh * 0.1, ww, hh * 0.3, S.night ? '#f2c060' : '#2a1a12'); fr(q, wx - ww, uy + hh * 0.1, ww / 2, hh * 0.3, mixc(L.wood, '#000000', 0.2)); fr(q, wx + ww / 2, uy + hh * 0.1, ww / 2, hh * 0.3, mixc(L.wood, '#000000', 0.2)); }
      lannaRoof(q, x0, x1, uy + hh * 0.02, L.top, L.roofCol);
      paper(q, rect(x0 - hh * 0.04, L.oy - hh * 0.02, w + hh * 0.08, hh * 0.12), mixc(L.wood, '#000000', 0.15), 1);
      laiKham(q, x0 + hh * 0.1, x1 - hh * 0.1, L.oy + hh * 0.04, hh * 0.035);
    },
    front: function (q, S, L) {
      var hh = S.hh, w = L.bx1 - L.bx0;
      for (var i = 0; i < L.posts; i++) { var px = L.bx0 + hh * 0.05 + (w - hh * 0.1) * i / (L.posts - 1); paper(q, rect(px - hh * 0.06, L.oy + hh * 0.08, hh * 0.12, S.deck - L.oy - hh * 0.08), mixc(L.wood, '#000000', 0.1), 0.8); fr(q, px - hh * 0.08, S.deck - hh * 0.06, hh * 0.16, hh * 0.06, '#9a948a'); }
      var sx = L.stairs > 0 ? L.bx1 : L.bx0 - hh * 0.5;
      for (i = 0; i < 6; i++) fr(q, sx, L.oy + i * hh * 0.2 - hh * 0.0, hh * 0.5, hh * 0.04, mixc(L.wood, '#000000', 0.05));
      ln(q, [[sx + (L.stairs > 0 ? hh * 0.5 : 0), S.deck], [sx + (L.stairs > 0 ? 0 : hh * 0.5), L.oy - hh * 0.3]], mixc(L.wood, '#000000', 0.2), 2.5);
    },
    shut: function (q, S, L) { var hh = S.hh, n = Math.round((L.ox1 - L.ox0) / (hh * 0.45)), pw = (L.ox1 - L.ox0) / n; for (var i = 0; i < n; i++) { paper(q, rect(L.ox0 + i * pw + 1, L.oy + hh * 0.1, pw - 2, S.deck - L.oy - hh * 0.1), mixc(L.wood, '#ffffff', 0.08), 0.5); q.strokeStyle = 'rgba(0,0,0,.3)'; q.lineWidth = 1; q.strokeRect(L.ox0 + i * pw + pw * 0.15, L.oy + hh * 0.25, pw * 0.7, hh * 0.4); q.strokeRect(L.ox0 + i * pw + pw * 0.15, L.oy + hh * 0.75, pw * 0.7, hh * 0.4); } }
  },
  /* a garden: a Lanna sala over the kitchen, a rain tree with fairy lights over the tables on the grass */
  garden: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 2.3; L.salaW = Math.min(hh * 3.4, (L.bx1 - L.bx0) * 0.62); L.sl = r() < 0.5; L.sa = L.sl ? L.bx0 : L.bx1 - L.salaW; L.sb = L.sa + L.salaW;
      L.oy = S.deck - hh * 1.5; L.ox0 = L.sa + hh * 0.15; L.ox1 = L.sb - hh * 0.15; L.signY = S.deck - hh * 1.62; L.signCx = (L.sa + L.sb) / 2; L.roofCol = pick(r, ['#a8432f', '#8a3a24', '#2f6a5a', '#6a4a3a']);
      L.treeX = L.sl ? L.bx1 - hh * 0.6 : L.bx0 + hh * 0.6; L.tr = { x0: L.treeX - hh * 1.1, x1: L.treeX + hh * 1.1 }; L.lawn = pick(r, ['#5f8a4a', '#6f9a52', '#8a7a5a']); L.umb = r() < 0.4 ? pick(r, AWN)[0] : null; L.wall = '#e8e0d0'; L.inner = 'open'; },
    back: function (q, S, L) {
      var hh = S.hh; paper(q, rect(L.bx0 - hh * 0.3, S.deck - 2, L.bx1 - L.bx0 + hh * 0.6, hh * 0.12), S.night ? '#2a3a26' : L.lawn, 0.5);
      tree(q, L.treeX, S.deck, hh, L.top + hh * 0.05, K.rnd(S.seed + 3), false);
      K.sala(q, L.sa, L.sb, S.deck, L.top + hh * 0.25, false, L.roofCol);
    },
    front: function (q, S, L) { if (L.umb) { var ux = L.treeX + (L.sl ? 0.6 : -0.6) * S.hh; ln(q, [[ux, S.deck], [ux, S.deck - S.hh * 1.25]], '#d8d0c0', 2); paper(q, function (p) { p.beginPath(); p.moveTo(ux - S.hh * 0.6, S.deck - S.hh * 1.05); p.quadraticCurveTo(ux, S.deck - S.hh * 1.45, ux + S.hh * 0.6, S.deck - S.hh * 1.05); p.closePath(); }, L.umb, 0.8); } },
    shut: function (q, S, L) {}
  },
  /* a wooden deck on posts over the river bank, a thatch or tin pavilion, lights over the water */
  river: {
    geo: function (L, S, r) { BLD.garden.geo(L, S, r); L.thatch = r() < 0.5; L.rail = pick(r, ['#8a5a32', '#6a4424', '#f2f2ee']); L.lawn = '#8a6a44'; L.umb = null; },
    back: function (q, S, L) { var hh = S.hh; tree(q, L.treeX, S.deck, hh, L.top + hh * 0.05, K.rnd(S.seed + 3), false);
      if (L.thatch) { [L.sa + hh * 0.15, L.sb - hh * 0.15].forEach(function (px) { paper(q, rect(px - 3, S.deck - hh * 1.6, 6, hh * 1.6), '#6a4424', 1); }); hut(q, L.sa, L.sb, S.deck - hh * 1.55, L.top + hh * 0.3, hh); }
      else K.sala(q, L.sa, L.sb, S.deck, L.top + hh * 0.25, false, L.roofCol); },
    front: function (q, S, L) { var hh = S.hh, a = S.x0, b = S.x1;
      paper(q, rect(a - 4, S.deck - 2, b - a + 8, hh * 0.12), '#8a5a32', 0.8); for (var x = a; x < b; x += hh * 0.25) fr(q, x, S.deck, 1, hh * 0.1, 'rgba(0,0,0,.25)');
      for (x = a + hh * 0.3; x < b; x += hh * 0.9) paper(q, rect(x - 3, S.deck + hh * 0.1, 6, S.H - S.deck), '#5a3a20', 0.6);
      fr(q, a, S.deck - hh * 0.32, b - a, 2.5, L.rail); for (x = a + hh * 0.1; x < b; x += hh * 0.45) fr(q, x, S.deck - hh * 0.32, 2.5, hh * 0.32, L.rail); },
    shut: function (q, S, L) {}
  },
  /* bamboo and leaf thatch: a village hut with a raised floor */
  hut: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 2.15; L.oy = S.deck - hh * 1.45; L.ox0 = L.bx0 + hh * 0.12; L.ox1 = L.bx1 - hh * 0.12; L.signY = L.oy - hh * 0.05; L.floorH = hh * 0.22; L.inner = r() < 0.6 ? 'bamboo' : 'open'; L.wall = '#c8a868'; L.rasta = false; },
    back: function (q, S, L) { var hh = S.hh; if (L.inner === 'bamboo') room(q, S, L, L.ox0, L.ox1, L.oy, 'bamboo'); hut(q, L.bx0, L.bx1, L.oy, L.top, hh, L.rasta); },
    front: function (q, S, L) { var hh = S.hh; [L.bx0 + hh * 0.08, L.bx1 - hh * 0.08, (L.bx0 + L.bx1) / 2].forEach(function (px) { paper(q, rect(px - hh * 0.05, L.oy, hh * 0.1, S.deck - L.oy), '#b89a5a', 0.7); for (var k = 1; k < 5; k++) fr(q, px - hh * 0.05, L.oy + k * (S.deck - L.oy) / 5, hh * 0.1, 1.5, 'rgba(60,40,10,.4)'); });
      if (L.rasta) ['#d8242a', '#f7d020', '#2f8f3a'].forEach(function (col, i) { fr(q, L.bx0, L.oy + i * hh * 0.05, L.bx1 - L.bx0, hh * 0.05, col); }); },
    shut: function (q, S, L) { var hh = S.hh; paper(q, rect(L.ox0, L.oy + hh * 0.05, L.ox1 - L.ox0, (S.deck - L.oy) * 0.7), '#c8a868', 0.5); for (var y = L.oy + hh * 0.1; y < L.oy + (S.deck - L.oy) * 0.7; y += 4) fr(q, L.ox0, y, L.ox1 - L.ox0, 1, 'rgba(90,60,20,.35)'); }
  },
  /* concrete and glass: a bare box, timber slats, a deep slab over the door */
  modern: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * (1.95 + r() * 0.3); L.oy = S.deck - hh * 1.4; L.slat = r() < 0.6; L.sl = r() < 0.5; var sw = L.slat ? (L.bx1 - L.bx0) * 0.3 : 0;
      L.ox0 = L.bx0 + hh * 0.1 + (L.sl ? sw : 0); L.ox1 = L.bx1 - hh * 0.1 - (L.sl ? 0 : sw); L.signY = L.oy - hh * 0.42; L.signCx = (L.ox0 + L.ox1) / 2; L.wall = pick(r, ['#c8c4bc', '#b8b4ac', '#e8e4dc', '#d8d0c4', '#3a3e44']); L.inner = 'concrete'; L.glass = true; },
    back: function (q, S, L) { var hh = S.hh; paper(q, rect(L.bx0, L.top, L.bx1 - L.bx0, S.deck - L.top), L.wall, 1.4);
      for (var x = L.bx0 + hh * 0.4; x < L.bx1; x += hh * 0.8) for (var y = L.top + hh * 0.2; y < L.oy; y += hh * 0.35) fe(q, x, y, 1.3, 1.3, 'rgba(0,0,0,.22)');
      paper(q, rect(L.bx0 - hh * 0.2, L.oy - hh * 0.06, L.bx1 - L.bx0 + hh * 0.4, hh * 0.08), mixc(L.wall, '#000000', 0.2), 1.2);
      room(q, S, L, L.ox0, L.ox1, L.oy, 'concrete');
      if (L.slat) { var a = L.sl ? L.bx0 + hh * 0.1 : L.ox1, b = L.sl ? L.ox0 : L.bx1 - hh * 0.1; fr(q, a, L.oy, b - a, S.deck - L.oy, '#2a2420'); for (x = a; x < b; x += hh * 0.08) paper(q, rect(x, L.oy + 2, hh * 0.05, S.deck - L.oy - 2), '#b8844a', 0.3); } },
    front: function (q, S, L) { var hh = S.hh; if (L.closed) return; fr(q, L.ox0, L.oy + hh * 0.02, L.ox1 - L.ox0, S.deck - L.oy, 'rgba(190,220,235,.14)');
      for (var i = 0; i < 3; i++) fp(q, [[L.ox0 + (L.ox1 - L.ox0) * (0.1 + i * 0.3), L.oy + hh * 0.05], [L.ox0 + (L.ox1 - L.ox0) * (0.16 + i * 0.3), L.oy + hh * 0.05], [L.ox0 + (L.ox1 - L.ox0) * (0.04 + i * 0.3), S.deck - hh * 0.1], [L.ox0 + (L.ox1 - L.ox0) * (-0.02 + i * 0.3), S.deck - hh * 0.1]], 'rgba(255,255,255,.12)');
      fr(q, L.ox0, L.oy, 3, S.deck - L.oy, '#2a2a2e'); fr(q, L.ox1 - 3, L.oy, 3, S.deck - L.oy, '#2a2a2e'); },
    shut: function (q, S, L) { var hh = S.hh; fr(q, L.ox0, L.oy, L.ox1 - L.ox0, S.deck - L.oy, 'rgba(20,24,30,.55)'); fr(q, L.ox0, L.oy, 3, S.deck - L.oy, '#2a2a2e'); fr(q, L.ox1 - 3, L.oy, 3, S.deck - L.oy, '#2a2a2e');
      var cx = (L.ox0 + L.ox1) / 2; ln(q, [[cx - hh * 0.1, L.oy + hh * 0.3], [cx, L.oy + hh * 0.2], [cx + hh * 0.1, L.oy + hh * 0.3]], '#c8ccd0', 1); paper(q, rect(cx - hh * 0.25, L.oy + hh * 0.3, hh * 0.5, hh * 0.18), '#f6f2ea', 0.4); if (L.P.hours) txt(q, 'ปิด · CLOSED', cx, L.oy + hh * 0.39, hh * 0.08, '#2a2a2e', 800, 'center', hh * 0.46); }
  },
  /* a glasshouse café: a white iron frame, panes, and a jungle inside */
  glass: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 2.25; L.oy = S.deck - hh * 1.45; L.ox0 = L.bx0 + hh * 0.1; L.ox1 = L.bx1 - hh * 0.1; L.signY = L.oy - hh * 0.38; L.frame = pick(r, ['#f2f2ee', '#2a2e2a', '#3a5a4a']); L.inner = 'green'; L.wall = '#dfe8d8'; L.glass = true; },
    back: function (q, S, L) { var hh = S.hh, m = (L.bx0 + L.bx1) / 2, rr = K.rnd(S.seed + 9);
      fp(q, [[L.bx0, S.deck], [L.bx0, L.oy], [m, L.top], [L.bx1, L.oy], [L.bx1, S.deck]], 'rgba(214,236,226,.55)');
      for (var i = 0; i < 9; i++) plant(q, pick(rr, ['banana', 'monstera', 'palm', 'bamboo']), L.bx0 + (L.bx1 - L.bx0) * (0.05 + i * 0.11), S.deck - hh * 0.02, hh * 0.7, rr);
      fr(q, L.ox0, S.deck - hh * 0.9, L.ox1 - L.ox0, hh * 0.9, 'rgba(240,236,226,.55)'); },
    front: function (q, S, L) { var hh = S.hh, m = (L.bx0 + L.bx1) / 2, f = L.frame;
      fp(q, [[L.bx0, S.deck], [L.bx0, L.oy], [m, L.top], [L.bx1, L.oy], [L.bx1, S.deck]], 'rgba(220,240,250,.1)');
      ln(q, [[L.bx0, S.deck], [L.bx0, L.oy], [m, L.top], [L.bx1, L.oy], [L.bx1, S.deck]], f, 3); ln(q, [[L.bx0, L.oy], [L.bx1, L.oy]], f, 2);
      for (var x = L.bx0 + hh * 0.5; x < L.bx1 - 5; x += hh * 0.5) { var yt = L.oy - (L.oy - L.top) * (1 - Math.abs(x - m) / (m - L.bx0)); ln(q, [[x, L.oy], [x, yt]], f, 1.2); ln(q, [[x, L.oy], [x, S.deck - hh * 0.95]], f, 1.2); }
      ln(q, [[L.bx0, S.deck - hh * 0.95], [L.bx1, S.deck - hh * 0.95]], f, 1.5); },
    shut: function (q, S, L) { fr(q, L.ox0, L.oy, L.ox1 - L.ox0, S.deck - L.oy, 'rgba(20,30,30,.35)'); }
  },
  /* a big canopy on steel legs at the roadside */
  tent: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 1.85; L.oy = S.deck - hh * 1.5; L.ox0 = L.bx0 + hh * 0.1; L.ox1 = L.bx1 - hh * 0.1; L.signY = L.oy - hh * 0.05; L.cloth = pick(r, AWN); L.inner = 'open'; L.wall = '#e8e0d0'; },
    back: function (q, S, L) {},
    front: function (q, S, L) { var hh = S.hh; [L.bx0 + hh * 0.05, L.bx1 - hh * 0.05].forEach(function (px) { ln(q, [[px, S.deck], [px, L.oy]], '#9aa0a8', 3); });
      paper(q, poly([[L.bx0 - hh * 0.1, L.oy], [L.bx0 + hh * 0.4, L.top], [L.bx1 - hh * 0.4, L.top], [L.bx1 + hh * 0.1, L.oy]]), L.cloth[1], 1.2);
      for (var i = 0; i < 5; i++) { var u = i / 4; fp(q, [[lerp(L.bx0 + hh * 0.4, L.bx1 - hh * 0.4, u) - hh * 0.12, L.top + 1], [lerp(L.bx0 + hh * 0.4, L.bx1 - hh * 0.4, u) + hh * 0.12, L.top + 1], [lerp(L.bx0 - hh * 0.1, L.bx1 + hh * 0.1, u) + hh * 0.16, L.oy], [lerp(L.bx0 - hh * 0.1, L.bx1 + hh * 0.1, u) - hh * 0.16, L.oy]], L.cloth[0]); }
      awning(q, L.bx0, L.bx1, L.oy, hh * 0.1, L.cloth, hh); },
    shut: function (q, S, L) {}
  },
  /* a unit inside a mall or a market hall, its neighbours either side */
  mall: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 2.25; L.oy = S.deck - hh * 1.35; L.ox0 = L.bx0 + hh * 0.12; L.ox1 = L.bx1 - hh * 0.12; L.signY = L.oy - hh * 0.4; L.market = /ตลาด|กาด|market|kad\b/i.test(String(L.P.inside || '')); L.inner = L.market ? 'tile' : 'concrete'; L.wall = L.market ? '#e8e0cc' : pick(r, ['#f2ece0', '#e8e4ea', '#efe8dc']); L.shopCol = pick(r, ['#2f6db0', '#c0392b', '#2f8f5b', '#3a3e44', '#a8642a']); },
    back: function (q, S, L) { var hh = S.hh, a = S.x0, b = S.x1;
      paper(q, rect(a - 4, L.top, b - a + 8, S.deck - L.top), L.market ? '#c8bca4' : '#e8e2d6', 1);
      if (L.market) { for (var x = a; x < b; x += hh * 0.5) ln(q, [[x, L.top], [x + hh * 0.25, L.top + hh * 0.25], [x + hh * 0.5, L.top]], '#7a7e84', 1.5); ln(q, [[a, L.top + hh * 0.25], [b, L.top + hh * 0.25]], '#7a7e84', 2); }
      else { fr(q, a, L.top, b - a, hh * 0.18, '#f6f4ee'); for (x = a + hh * 0.5; x < b; x += hh * 1.1) { fe(q, x, L.top + hh * 0.18, hh * 0.08, hh * 0.02, '#fffbe8'); glow(q, x, L.top + hh * 0.3, hh * 0.5, '255,250,220', 0.3); } }
      [[a, L.bx0 - hh * 0.15], [L.bx1 + hh * 0.15, b]].forEach(function (n, i) { if (n[1] - n[0] < hh * 0.4) return; var top = L.oy - hh * 0.1; paper(q, rect(n[0], top - hh * 0.3, n[1] - n[0], hh * 0.3), i ? '#5a6a7a' : '#7a5a6a', 0.6);
        if (L.market) { for (var k = 0; k < 6; k++) paper(q, E(n[0] + (n[1] - n[0]) * (k + 0.5) / 6, S.deck - hh * 0.5, hh * 0.13, hh * 0.08), ['#f29a1a', '#5aa83a', '#d8242a', '#f7d020', '#8a3a8a', '#e8642a'][(k + i) % 6], 0.4); paper(q, rect(n[0], S.deck - hh * 0.45, n[1] - n[0], hh * 0.45), '#9a7a52', 0.5); }
        else rollShutter(q, n[0] + 4, n[1] - 4, top, S.deck, '#c8ccd0'); });
      paper(q, rect(L.bx0, L.oy - hh * 0.5, L.bx1 - L.bx0, hh * 0.5), L.shopCol, 1);
      room(q, S, L, L.ox0, L.ox1, L.oy, L.inner); },
    front: function (q, S, L) { var hh = S.hh; paper(q, rect(L.bx0, L.oy - hh * 0.02, hh * 0.12, S.deck - L.oy), L.shopCol, 0.6); paper(q, rect(L.bx1 - hh * 0.12, L.oy - hh * 0.02, hh * 0.12, S.deck - L.oy), L.shopCol, 0.6);
      if (!L.market) for (var x = S.x0; x < S.x1; x += hh * 0.45) fr(q, x, S.deck + hh * 0.02, hh * 0.44, 1, 'rgba(255,255,255,.4)'); },
    shut: function (q, S, L) { var hh = S.hh; q.strokeStyle = '#8a8e94'; q.lineWidth = 1; for (var x = L.ox0; x < L.ox1; x += 6) { q.beginPath(); q.moveTo(x, L.oy); q.lineTo(x, S.deck); q.stroke(); } for (var y = L.oy; y < S.deck; y += 6) { q.beginPath(); q.moveTo(L.ox0, y); q.lineTo(L.ox1, y); q.stroke(); } fr(q, L.ox0, L.oy, L.ox1 - L.ox0, hh * 0.08, '#6a6e74'); }
  },
  /* a rooftop: the bar on the roof, glass rail, the city's windows below the deck */
  roof: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 1.9; L.oy = S.deck - hh * 1.55; L.ox0 = L.bx0 + hh * 0.1; L.ox1 = L.bx1 - hh * 0.1; L.signY = L.top - hh * 0.05; L.pergola = pick(r, ['#2a2420', '#6a4424', '#3a3e44']); L.inner = 'open'; L.wall = '#3a3e44'; },
    back: function (q, S, L) { var hh = S.hh; fr(q, S.x0, S.deck, S.span, S.H - S.deck, '#3a3e48'); for (var x = S.x0 + hh * 0.2; x < S.x1; x += hh * 0.5) fr(q, x, S.deck + hh * 0.18, hh * 0.25, hh * 0.2, (Math.floor(x) * 7) % 3 ? (S.night ? '#ffd88a' : '#7a8a9a') : '#4a5060');
      paper(q, rect(S.x0 - 4, S.deck - 2, S.span + 8, hh * 0.1), '#8a8e94', 0.8);
      for (x = L.bx0; x <= L.bx1 + 1; x += (L.bx1 - L.bx0) / 3) ln(q, [[x, S.deck], [x, L.top]], L.pergola, 3);
      for (x = L.bx0; x < L.bx1; x += hh * 0.18) fr(q, x, L.top - 2, hh * 0.08, 4, L.pergola); ln(q, [[L.bx0 - hh * 0.1, L.top], [L.bx1 + hh * 0.1, L.top]], L.pergola, 3); },
    front: function (q, S, L) { fr(q, S.x0, S.deck - S.hh * 0.38, S.span, S.hh * 0.38, 'rgba(200,230,240,.16)'); ln(q, [[S.x0, S.deck - S.hh * 0.38], [S.x1, S.deck - S.hh * 0.38]], '#c8ccd0', 2); },
    shut: function (q, S, L) {}
  },
  /* no building: the stall is the whole shop */
  cart: {
    geo: function (L, S, r) { var hh = S.hh; L.top = S.deck - hh * 1.9; L.oy = S.deck - hh * 1.5; L.ox0 = L.bx0; L.ox1 = L.bx1; L.signY = S.deck - hh * 2.05; L.inner = 'open'; L.wall = '#e8e0d0'; L.umb = pick(r, [['#d8242a', '#f6f2ea'], ['#2f6db0', '#f7d020'], ['#f29a1a', '#2f8f5b'], ['#e8408a', '#f6f2ea'], ['#2f8f5b', '#f6f2ea']]); L.lean = r() < 0.4; },
    back: function (q, S, L) { var hh = S.hh; if (L.lean && L.backdrop !== 'none') { paper(q, rect(L.bx0 - hh * 0.5, S.deck - hh * 1.6, L.bx1 - L.bx0 + hh, hh * 1.6), pick(K.rnd(S.seed), WALLS), 1); rollShutter(q, L.bx0 - hh * 0.35, L.bx1 + hh * 0.35, S.deck - hh * 1.35, S.deck, '#9aa4ac'); } },
    front: function (q, S, L) {},
    shut: function (q, S, L) {}
  }
};
BLD.reggae = { geo: function (L, S, r) { BLD.hut.geo(L, S, r); L.rasta = true; L.inner = 'bamboo'; }, back: BLD.hut.back, front: BLD.hut.front, shut: BLD.hut.shut };
/* a thatch of leaf shingles: rows of jagged strips, darker toward the eave */
function hut(q, x0, x1, eave, top, hh, rasta) {
  var w = x1 - x0, m = (x0 + x1) / 2, rows = 5;
  for (var i = 0; i < rows; i++) { var u0 = i / rows, u1 = (i + 1) / rows, y0 = lerp(top, eave, u0), y1 = lerp(top, eave, u1), hw0 = lerp(w * 0.18, w * 0.6, u0), hw1 = lerp(w * 0.18, w * 0.6, u1), pts = [[m - hw0, y0], [m + hw0, y0]];
    for (var k = 0; k <= 16; k++) { var x = lerp(m + hw1, m - hw1, k / 16); pts.push([x, y1 + (k % 2 ? hh * 0.04 : -hh * 0.01)]); }
    paper(q, poly(pts), rasta ? ['#2f8f3a', '#f7d020', '#d8242a', '#2f8f3a', '#f7d020'][i] : ['#b8945a', '#a8844a', '#9a7840', '#8a6a38', '#7a5e30'][i], 0.8); }
  ln(q, [[m - w * 0.2, top], [m + w * 0.2, top]], '#6a4a24', 3);
}

/* ---------------------------------------------------------------- the kitchens
   each station: w (its width in hh), back (what stands behind the cook), front (the counter that
   hides the cook's legs, and what sits on it), live (the cook at work and what moves).
   st: { x0, x1, top (the counter's top), cx (where the cook stands), dir (which way the cook faces), tx (the tool) } */
function counter(q, x0, x1, top, deck, kind, hh) {
  var col = { steel: '#c8ccd2', wood: '#8a5a32', tile: '#f2f2ee', concrete: '#a8a49c', teak: '#6b3a1e', red: '#a8241c', boat: '#7a4a2a', white: '#f2efe8', bamboo: '#c8a868' }[kind] || '#c8ccd2';
  if (kind === 'cart') { var cb = deck - hh * 0.18; paper(q, rect(x0, top, x1 - x0, cb - top), '#c8ccd2', 1); fr(q, x0 - 2, top - 2, x1 - x0 + 4, hh * 0.05, '#9aa0a8'); for (var w2 = 0; w2 < 3; w2++) fr(q, x0 + (x1 - x0) * (0.2 + w2 * 0.3), top + hh * 0.08, 2, cb - top - hh * 0.12, 'rgba(255,255,255,.5)');
    [x0 + hh * 0.2, x1 - hh * 0.2].forEach(function (wx) { paper(q, E(wx, deck - hh * 0.12, hh * 0.12, hh * 0.12), '#2a2a2e', 0.6); fe(q, wx, deck - hh * 0.12, hh * 0.05, hh * 0.05, '#9aa0a8'); }); ln(q, [[x0, top + hh * 0.05], [x0 - hh * 0.15, top - hh * 0.05]], '#9aa0a8', 2.5); return; }
  if (kind === 'boat') { paper(q, function (p) { p.beginPath(); p.moveTo(x0 - hh * 0.25, top - hh * 0.08); p.quadraticCurveTo(x0, deck - hh * 0.05, x0 + hh * 0.2, deck); p.lineTo(x1 - hh * 0.2, deck); p.quadraticCurveTo(x1, deck - hh * 0.05, x1 + hh * 0.25, top - hh * 0.08); p.closePath(); }, col, 1); fr(q, x0 - hh * 0.1, top + hh * 0.06, x1 - x0 + hh * 0.2, hh * 0.04, '#d8a040'); fr(q, x0, top + hh * 0.2, x1 - x0, hh * 0.03, '#2f8f5b'); return; }
  paper(q, rect(x0, top, x1 - x0, deck - top), col, 1);
  fr(q, x0 - 2, top - 2, x1 - x0 + 4, hh * 0.05, mixc(col, '#000000', 0.15));
  if (kind === 'steel') { for (var i = 0; i < 3; i++) fr(q, x0 + (x1 - x0) * (0.15 + i * 0.3), top + hh * 0.08, 2, deck - top - hh * 0.12, 'rgba(255,255,255,.45)'); }
  else if (kind === 'wood' || kind === 'teak') { for (var y = top + hh * 0.1; y < deck; y += hh * 0.1) fr(q, x0, y, x1 - x0, 1, 'rgba(0,0,0,.2)'); }
  else if (kind === 'tile') { q.strokeStyle = 'rgba(120,140,150,.4)'; q.lineWidth = 0.7; for (var x = x0; x < x1; x += hh * 0.1) { q.beginPath(); q.moveTo(x, top); q.lineTo(x, deck); q.stroke(); } for (y = top; y < deck; y += hh * 0.1) { q.beginPath(); q.moveTo(x0, y); q.lineTo(x1, y); q.stroke(); } }
  else if (kind === 'bamboo') { for (x = x0 + 2; x < x1; x += hh * 0.06) fr(q, x, top + hh * 0.05, 1.2, deck - top, 'rgba(90,60,20,.35)'); }
  else if (kind === 'red') laiKham(q, x0, x1, top + hh * 0.22, hh * 0.05, '#f2c94c');
}
function glassCase(q, x0, x1, y1, h, fill) {
  paper(q, rect(x0, y1 - h, x1 - x0, h), 'rgba(220,240,250,.35)', 0.5); if (fill) fill(x0, x1, y1, h);
  q.strokeStyle = '#c8ccd2'; q.lineWidth = 1.5; q.strokeRect(x0, y1 - h, x1 - x0, h); fp(q, [[x0 + 3, y1 - h + 2], [x0 + (x1 - x0) * 0.2, y1 - h + 2], [x0 + 3, y1 - 2]], 'rgba(255,255,255,.25)');
}
function shelf(q, x0, x1, y, hh, items) { fr(q, x0, y, x1 - x0, 2.5, '#6a4a2a'); for (var i = 0; i < items.length; i++) { var x = x0 + (x1 - x0) * (i + 0.5) / items.length; items[i](q, x, y); } }
function jar(col) { return function (q, x, y) { fp(q, [[x - 4, y], [x - 4, y - 9], [x - 2, y - 11], [x + 2, y - 11], [x + 4, y - 9], [x + 4, y]], col); }; }
function bowls(q, x, y, hh, n, col) { for (var i = 0; i < n; i++) { fp(q, [[x - hh * 0.1, y - i * hh * 0.035], [x + hh * 0.1, y - i * hh * 0.035], [x + hh * 0.06, y - i * hh * 0.035 + hh * 0.03], [x - hh * 0.06, y - i * hh * 0.035 + hh * 0.03]], col || '#f6f2ea'); fr(q, x - hh * 0.1, y - i * hh * 0.035, hh * 0.2, 1, '#c0392b'); } }
function cookHat(c, me, T) { if (T.hat) hat(c, me, T.hat, T.hatCol); }
/* a cook at the counter, hands sent to T1 (front) and T2 (back) */
function cookAt(c, S, st, d, T, T1, T2, lean) {
  var hh = S.hh; d.dir = st.dir; d.garb = 'casual'; d.long = true; d.skirt = 0;
  var me = worker(c, st.cx, S.deck, hh * 0.95, { lean: lean || 0.08 }, d, T1, T2);
  apron(c, me, d, T.apron || '#f2efe8'); cookHat(c, me, T); return me;
}
var ST = {
  /* the wok: a toss every 1.6 s, θ = 0.3·sin 2πu, rice up on h = 4v(1 − v)·h₀, flames that flare */
  wok: { w: 1.6,
    back: function (q, S, L, st) { var hh = S.hh; shelf(q, st.x0, st.x1, st.top - hh * 0.55, hh, [jar('#5a3212'), jar('#c8402a'), jar('#e8b84a'), jar('#3a2a1a'), jar('#f2efe8')]); for (var i = 0; i < 3; i++) ln(q, [[st.x0 + hh * (0.2 + i * 0.12), st.top - hh * 0.75], [st.x0 + hh * (0.2 + i * 0.12), st.top - hh * 0.45]], '#9aa0a8', 1.5); },
    front: function (q, S, L, st) { var hh = S.hh; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'steel', hh); fr(q, st.tx - hh * 0.2, st.top - hh * 0.06, hh * 0.4, hh * 0.06, '#3a3a3e');
      var gx = st.x1 - hh * 0.45 * st.dir - (st.dir > 0 ? 0 : 0), g0 = Math.min(gx, gx + st.dir * hh * 0.01); glassCase(q, st.dir > 0 ? st.x1 - hh * 0.55 : st.x0 + hh * 0.05, st.dir > 0 ? st.x1 - hh * 0.05 : st.x0 + hh * 0.55, st.top, hh * 0.3, function (a, b, y, h) { for (var i = 0; i < 4; i++) fe(q, a + (b - a) * (i + 0.5) / 4, y - h * 0.3, (b - a) * 0.1, h * 0.12, ['#d8a080', '#5aa83a', '#f2e6c9', '#e8642a'][i]); for (i = 0; i < 3; i++) fe(q, a + (b - a) * (i + 0.7) / 4, y - h * 0.68, (b - a) * 0.08, h * 0.1, ['#d9342b', '#3f8a3a', '#f7d040'][i]); });
      bowl(q, st.x0 + (st.x1 - st.x0) * 0.5, st.top, hh * 0.28, '#f6f2ea', '#fbf8ee'); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, u = (t / 1600) % 1, th = 0.3 * Math.sin(u * TAU), lift = Math.max(0, Math.sin(u * TAU)) * hh * 0.06, wx = st.tx, wy = st.top - hh * 0.1 - lift, flare = Math.pow(Math.max(0, Math.sin(t / 900)), 10);
      flames(c, wx, st.top - hh * 0.05, hh * 0.38, hh * (0.14 + flare * 0.35), t, 0);
      c.save(); c.translate(wx, wy); c.rotate(th * st.dir * 0.4); fp(c, [[-hh * 0.22, 0], [hh * 0.22, 0], [hh * 0.14, hh * 0.09], [-hh * 0.14, hh * 0.09]], '#2a2a2e'); fe(c, 0, 0, hh * 0.22, hh * 0.04, '#1a1a1e'); fe(c, 0, -hh * 0.01, hh * 0.15, hh * 0.03, T.wokFill || '#c8742a'); c.restore();
      var v = (u - 0.1) / 0.45; if (v > 0 && v < 1) for (var i = 0; i < 6; i++) fe(c, wx + (i - 2.5) * hh * 0.035 + st.dir * (v - 0.5) * hh * 0.06, wy - 4 * v * (1 - v) * hh * (0.22 + (i % 3) * 0.06), hh * 0.022, hh * 0.018, ['#fbf8ee', '#c8742a', '#5aa83a', '#d9342b', '#fbf8ee', '#f7d040'][i]);
      smoke(c, wx, wy - hh * 0.1, hh * 0.8, t, 0.2);
      var hx = wx - st.dir * hh * 0.42; ln(c, [[wx - st.dir * hh * 0.2, wy], [hx, wy - hh * 0.04]], '#2a2a2e', hh * 0.03);
      cookAt(c, S, st, d, T, [hx, wy - hh * 0.04], [wx + Math.cos(t / 300) * hh * 0.08, wy - hh * 0.12 + Math.sin(t / 300) * hh * 0.02]); }
  },
  /* the noodle cart: the strainer dips and shakes, y = A·|sin ωt|, the pot steams */
  noodle: { w: 1.75,
    back: function (q, S, L, st) { var hh = S.hh; shelf(q, st.x0, st.x1, st.top - hh * 0.6, hh, [function (q2, x, y) { bowls(q2, x, y - 2, hh, 4, T0(L).bowl); }, jar('#c8402a'), function (q2, x, y) { bowls(q2, x, y - 2, hh, 4, T0(L).bowl); }]); },
    front: function (q, S, L, st) { var hh = S.hh, T = T0(L), pot = st.tx; counter(q, st.x0, st.x1, st.top, S.deck, T.ckind || L.ckind || 'steel', hh);
      paper(q, rect(pot - hh * 0.28, st.top - hh * 0.2, hh * 0.56, hh * 0.22), '#b8bcc2', 0.6); fe(q, pot, st.top - hh * 0.2, hh * 0.28, hh * 0.04, T.soup || '#d8c08a'); ln(q, [[pot, st.top - hh * 0.24], [pot, st.top - hh * 0.16]], '#9aa0a8', 1.2);
      var ga = st.dir > 0 ? st.x1 - hh * 0.62 : st.x0 + hh * 0.06; glassCase(q, ga, ga + hh * 0.56, st.top, hh * 0.42, function (a, b, y, h) { for (var i = 0; i < 3; i++) { var nx = a + (b - a) * (i + 0.5) / 3; for (var k = 0; k < 5; k++) { q.strokeStyle = i === 1 ? '#f2d070' : '#fbf6e8'; q.lineWidth = 1; q.beginPath(); q.arc(nx + (k - 2) * 2, y - h * 0.3, h * 0.12, Math.PI, TAU); q.stroke(); } } for (i = 0; i < 5; i++) fe(q, a + (b - a) * (i + 0.5) / 5, y - h * 0.75, h * 0.06, h * 0.06, i % 2 ? '#e8d8c0' : '#d8a080'); });
      if (T.bowlsOut !== false) [0, 1].forEach(function (i) { DISH[T.dish0 || 'noodle'](q, (st.x0 + st.x1) / 2 + (i - 0.5) * hh * 0.3 - st.dir * hh * 0.25, st.top, hh * 0.32); });
      caddy(q, st.dir > 0 ? st.x0 + hh * 0.18 : st.x1 - hh * 0.18, st.top, hh); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, u = (t / 2400) % 1, pot = st.tx, py = st.top - hh * 0.2;
      steam(c, pot, py, hh * 0.9, t, 0, 3, 0.7);
      var up = u < 0.45 ? 0 : u < 0.6 ? ease((u - 0.45) / 0.15) : u < 0.88 ? 1 : 1 - ease((u - 0.88) / 0.12), shake = u > 0.6 && u < 0.88 ? Math.sin(t / 45) * hh * 0.02 : u < 0.45 ? Math.sin(t / 160) * hh * 0.01 : 0;
      var bx = pot + st.dir * hh * 0.02, by = py + hh * 0.06 - up * hh * 0.32 + shake;
      if (up > 0.3) for (var i = 0; i < 4; i++) { var dv = ((t / 300 + i / 4) % 1); fe(c, bx + (i - 1.5) * hh * 0.03, by + hh * 0.1 + dv * hh * 0.2, 1.1, 1.6, 'rgba(220,240,255,' + (1 - dv) + ')'); }
      fp(c, [[bx - hh * 0.08, by - hh * 0.02], [bx + hh * 0.08, by - hh * 0.02], [bx + hh * 0.02, by + hh * 0.12], [bx - hh * 0.02, by + hh * 0.12]], 'rgba(160,165,170,.85)');
      for (i = 0; i < 4; i++) ln(c, [[bx - hh * 0.06 + i * hh * 0.04, by], [bx - hh * 0.03 + i * hh * 0.02, by + hh * 0.09]], T.noodleCol || '#f2e2a8', 1.2);
      var hx = bx - st.dir * hh * 0.3, hy = by - hh * 0.16; ln(c, [[bx - st.dir * hh * 0.06, by - hh * 0.02], [hx, hy]], '#7a5a3a', hh * 0.025);
      cookAt(c, S, st, d, T, [hx, hy], [pot + st.dir * hh * 0.25, py - hh * 0.05]); }
  },
  /* khao kaeng: a glass cabinet of curries in trays, the ladle from tray to plate */
  curry: { w: 1.85,
    back: function (q, S, L, st) { var hh = S.hh, rx = st.dir > 0 ? st.x0 + hh * 0.25 : st.x1 - hh * 0.25; paper(q, rect(rx - hh * 0.17, st.top - hh * 0.32, hh * 0.34, hh * 0.32), '#c8ccd2', 0.6); paper(q, E(rx, st.top - hh * 0.33, hh * 0.18, hh * 0.04), '#d8dce2', 0.3); },
    front: function (q, S, L, st) { var hh = S.hh, T = T0(L), a = st.dir > 0 ? st.x0 + hh * 0.5 : st.x0 + hh * 0.06, b = st.dir > 0 ? st.x1 - hh * 0.06 : st.x1 - hh * 0.5; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'steel', hh);
      glassCase(q, a, b, st.top, hh * 0.36, function (x0, x1, y, h) { var cols = T.trays || ['#5d9b3a', '#c8452a', '#e8a02a', '#7a4a28', '#3f8a3a', '#f2e6c9', '#a8642a', '#d8c060'], n = Math.max(4, Math.round((x1 - x0) / (hh * 0.2))); for (var i = 0; i < n; i++) { var tx = x0 + (x1 - x0) * (i + 0.5) / n; paper(q, E(tx, y - h * 0.18, (x1 - x0) / n * 0.44, h * 0.13), '#d8dce2', 0.2); fe(q, tx, y - h * 0.22, (x1 - x0) / n * 0.38, h * 0.09, cols[i % cols.length]); if (i % 2) fe(q, tx + 2, y - h * 0.26, 2.5, 2, '#f2e6c9'); } }); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, u = (t / 3000) % 1, rx = st.dir > 0 ? st.x0 + hh * 0.25 : st.x1 - hh * 0.25; steam(c, rx, st.top - hh * 0.36, hh * 0.6, t, 1, 2);
      var tray = [st.tx + st.dir * hh * 0.15 * Math.sin(Math.floor(t / 3000) * 2.4), st.top - hh * 0.42], pl = [st.cx + st.dir * hh * 0.22, st.top - hh * 0.5], g = u < 0.4 ? ease(u / 0.4) : u < 0.6 ? 1 : 1 - ease((u - 0.6) / 0.4), hand = [lerp(pl[0], tray[0], g), lerp(pl[1] - hh * 0.1, tray[1], g)];
      var me = cookAt(c, S, st, d, T, hand, pl); fe(c, pl[0], pl[1], hh * 0.12, hh * 0.03, '#f6f2ea'); fe(c, pl[0], pl[1] - hh * 0.02, hh * 0.06, hh * 0.025, '#fbf8ee');
      ln(c, [hand, [hand[0] + st.dir * hh * 0.06, hand[1] + hh * 0.08]], '#9aa0a8', 1.5); fe(c, hand[0] + st.dir * hh * 0.06, hand[1] + hh * 0.09, hh * 0.03, hh * 0.018, '#9aa0a8'); }
  },
  /* the charcoal grill: skewers or chicken over embers, a woven fan beating, smoke and sparks */
  grill: { w: 1.7,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh, T = T0(L), a = st.dir > 0 ? st.x0 + hh * 0.5 : st.x0 + hh * 0.05, b = st.dir > 0 ? st.x1 - hh * 0.05 : st.x1 - hh * 0.5, y = st.top + hh * 0.05;
      paper(q, poly([[a, y], [b, y], [b - hh * 0.05, S.deck - hh * 0.05], [a + hh * 0.05, S.deck - hh * 0.05]]), '#8a8e94', 1); fr(q, a, y, b - a, hh * 0.06, '#5a5e64'); for (var x = a + hh * 0.08; x < b - hh * 0.05; x += hh * 0.12) fr(q, x, y + hh * 0.12, hh * 0.06, hh * 0.04, '#3a3e44');
      ln(q, [[a + hh * 0.1, S.deck - hh * 0.05], [a + hh * 0.06, S.deck]], '#5a5e64', 2); ln(q, [[b - hh * 0.1, S.deck - hh * 0.05], [b - hh * 0.06, S.deck]], '#5a5e64', 2);
      grillItems(q, T.grill || 'skewer', a, b, y, hh);
      if (st.dir > 0) counter(q, st.x0, a - hh * 0.05, st.top, S.deck, L.ckind || 'steel', hh); else counter(q, b + hh * 0.05, st.x1, st.top, S.deck, L.ckind || 'steel', hh);
      var px = st.dir > 0 ? st.x0 + hh * 0.22 : st.x1 - hh * 0.22; plate(q, px, st.top, hh * 0.32); if (T.grill === 'chicken') DISH.gaiyang(q, px, st.top, hh * 0.32); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, a = st.dir > 0 ? st.x0 + hh * 0.5 : st.x0 + hh * 0.05, b = st.dir > 0 ? st.x1 - hh * 0.05 : st.x1 - hh * 0.5, y = st.top + hh * 0.05, m = (a + b) / 2;
      c.save(); c.globalCompositeOperation = 'lighter'; glow(c, m, y + hh * 0.02, (b - a) * 0.6, '255,110,30', 0.32 + 0.12 * Math.sin(t / 230)); c.restore();
      smoke(c, m - hh * 0.1, y - hh * 0.05, hh * 1.1, t, 0); smoke(c, m + hh * 0.15, y - hh * 0.05, hh * 0.9, t, 0.5); sparks(c, m, y - hh * 0.02, hh * 0.6, t, 5);
      if (T.grill === 'steak') { var fl = Math.max(0, Math.sin(t / 520)), me2 = cookAt(c, S, st, d, T, [m + st.dir * hh * 0.05 + Math.sin(t / 700) * hh * 0.06, y - hh * 0.12], [m - st.dir * hh * 0.12, y - hh * 0.1 - fl * hh * 0.12], 0.18), sp = me2.hand[1]; ln(c, [sp, [sp[0] + st.dir * hh * 0.14, sp[1] + hh * 0.04]], '#9aa0a8', 2); fr(c, sp[0] + st.dir * hh * 0.12 - hh * 0.04, sp[1] + hh * 0.03, hh * 0.08, 2.5, '#c8ccd2'); if (fl > 0.3) fe(c, sp[0] + st.dir * hh * 0.14, sp[1] - fl * hh * 0.06, hh * 0.05, hh * 0.025, '#7a3418'); return; }
      var fan = Math.sin(t / 140) * 0.5, fx = m - st.dir * hh * 0.1, fy = y - hh * 0.28;
      cookAt(c, S, st, d, T, [m + st.dir * hh * 0.05 + Math.sin(t / 700) * hh * 0.06, y - hh * 0.12], [fx, fy + fan * hh * 0.06], 0.18);
      c.save(); c.translate(fx, fy + fan * hh * 0.06); c.rotate(fan); fe(c, 0, -hh * 0.1, hh * 0.08, hh * 0.1, '#c8a060'); for (var i = -1; i <= 1; i++) ln(c, [[i * hh * 0.04, -hh * 0.18], [i * hh * 0.04, -hh * 0.02]], 'rgba(90,60,20,.5)', 0.8); c.restore(); }
  },
  /* som tam: the pestle in the krok, y = |sin ωt|, a basket of green papaya, limes and chillies */
  mortar: { w: 1.55,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh, kx = st.tx; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'wood', hh);
      paper(q, poly([[kx - hh * 0.16, st.top - hh * 0.28], [kx + hh * 0.16, st.top - hh * 0.28], [kx + hh * 0.1, st.top], [kx - hh * 0.1, st.top]]), '#a8582a', 0.8); fe(q, kx, st.top - hh * 0.28, hh * 0.16, hh * 0.035, '#6a3018');
      var bx = st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3; paper(q, E(bx, st.top - hh * 0.08, hh * 0.24, hh * 0.09), '#c8a060', 0.6); for (var i = 0; i < 5; i++) paper(q, E(bx - hh * 0.14 + i * hh * 0.07, st.top - hh * (0.16 + (i % 2) * 0.04), hh * 0.06, hh * 0.08, i * 0.4), i < 3 ? '#7ab84a' : '#5c9e32', 0.2); lime(q, bx + hh * 0.12, st.top - hh * 0.2, hh * 0.04); for (i = 0; i < 4; i++) fe(q, bx - hh * 0.05 + i * hh * 0.04, st.top - hh * 0.24, hh * 0.012, hh * 0.035, '#d8242a', 0.3);
      DISH.gaiyang(q, (st.x0 + st.x1) / 2 - st.dir * hh * 0.05, st.top + 1, hh * 0.3); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, kx = st.tx, k = Math.abs(Math.sin(t / 170)), py = st.top - hh * 0.3 - k * hh * 0.18;
      ln(c, [[kx, py], [kx - st.dir * hh * 0.02, py - hh * 0.26]], '#b8844a', hh * 0.05); if (k < 0.15) for (var i = 0; i < 3; i++) fe(c, kx + (i - 1) * hh * 0.06, st.top - hh * 0.34 - (0.15 - k) * hh * 0.4, 1.5, 1.5, i % 2 ? '#d8242a' : '#9ac85a');
      cookAt(c, S, st, d, T, [kx - st.dir * hh * 0.02, py - hh * 0.14], [kx + st.dir * hh * 0.08, st.top - hh * 0.3 + Math.sin(t / 400) * hh * 0.02], 0.12); }
  },
  /* the chopping block: chickens, ducks or red pork hung in a glass box, the cleaver falling in fours */
  hang: { w: 1.65,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh, T = T0(L), a = st.dir > 0 ? st.x0 + hh * 0.55 : st.x0 + hh * 0.05, b = st.dir > 0 ? st.x1 - hh * 0.05 : st.x1 - hh * 0.55; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'steel', hh);
      paper(q, rect(a, st.top - hh * 0.62, b - a, hh * 0.62), 'rgba(220,240,250,.3)', 0.6); q.strokeStyle = '#c0392b'; q.lineWidth = 3; q.strokeRect(a, st.top - hh * 0.62, b - a, hh * 0.62); fr(q, a, st.top - hh * 0.62, b - a, hh * 0.08, '#c0392b');
      var items = T.hang || ['chicken', 'chicken', 'pork'], n = items.length; for (var i = 0; i < n; i++) { var x = a + (b - a) * (i + 0.5) / n, y = st.top - hh * 0.52; ln(q, [[x, y - hh * 0.02], [x, y + hh * 0.04]], '#9aa0a8', 1.2); hung(q, items[i], x, y + hh * 0.04, hh); }
      var cx = st.tx; paper(q, rect(cx - hh * 0.16, st.top - hh * 0.1, hh * 0.32, hh * 0.1), '#a8784a', 0.6); fe(q, cx, st.top - hh * 0.1, hh * 0.16, hh * 0.03, '#c8986a'); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, u = (t / 1800) % 1, ch = u < 0.7 ? Math.abs(Math.sin(u / 0.7 * 4 * Math.PI)) : 0.8, cx = st.tx, hy = st.top - hh * 0.13 - ch * hh * 0.18;
      if (T.soupPot) steam(c, st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3, st.top - hh * 0.65, hh * 0.5, t, 2, 2);
      cookAt(c, S, st, d, T, [cx - st.dir * hh * 0.06, hy], [cx + st.dir * hh * 0.08, st.top - hh * 0.12], 0.12);
      fp(c, [[cx - st.dir * hh * 0.05, hy], [cx + st.dir * hh * 0.1, hy], [cx + st.dir * hh * 0.1, hy + hh * 0.08], [cx - st.dir * hh * 0.02, hy + hh * 0.08]], '#c8ccd2'); if (ch < 0.12) fe(c, cx + st.dir * hh * 0.05, st.top - hh * 0.12, hh * 0.04, hh * 0.015, 'rgba(255,255,255,.7)'); }
  },
  /* the sushi counter: fish in a cold case, the knife drawn through in one stroke */
  sushi: { w: 1.85,
    back: function (q, S, L, st) { var hh = S.hh; shelf(q, st.x0, st.x1, st.top - hh * 0.62, hh, [jar('#f2efe8'), jar('#2a4a2a'), jar('#f2efe8'), jar('#5a3212')]); },
    front: function (q, S, L, st) { var hh = S.hh; counter(q, st.x0, st.x1, st.top, S.deck, 'wood', hh); fr(q, st.x0, st.top - hh * 0.04, st.x1 - st.x0, hh * 0.05, '#e8d0a8');
      glassCase(q, st.x0 + hh * 0.08, st.x1 - hh * 0.08, st.top - hh * 0.04, hh * 0.2, function (a, b, y, h) { var cols = ['#f08a5d', '#d8343a', '#f7d040', '#f6e8e0', '#f08a5d']; for (var i = 0; i < 5; i++) { var x = a + (b - a) * (i + 0.5) / 5; paper(q, rect(x - (b - a) * 0.08, y - h * 0.55, (b - a) * 0.16, h * 0.4), cols[i], 0.2); if (!(i % 2)) for (var k = 0; k < 3; k++) fr(q, x - (b - a) * 0.07 + k * (b - a) * 0.05, y - h * 0.55, 1, h * 0.4, 'rgba(255,255,255,.6)'); } });
      DISH.sushi(q, st.dir > 0 ? st.x1 - hh * 0.4 : st.x0 + hh * 0.4, st.top - hh * 0.25, hh * 0.45); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, k = tri(t / 1500), kx = st.tx + st.dir * (k - 0.5) * hh * 0.2, ky = st.top - hh * 0.34;
      fe(c, st.tx, ky + hh * 0.04, hh * 0.12, hh * 0.035, '#f08a5d');
      cookAt(c, S, st, d, T, [kx - st.dir * hh * 0.06, ky - hh * 0.02], [st.tx + st.dir * hh * 0.1, ky + hh * 0.02], 0.15);
      ln(c, [[kx - st.dir * hh * 0.02, ky], [kx + st.dir * hh * 0.18, ky + hh * 0.02]], '#e8eef2', hh * 0.025); }
  },
  /* the brick oven: fire in its mouth, the peel sliding in and out, x = A·sin ωt */
  oven: { w: 1.9,
    back: function (q, S, L, st) { var hh = S.hh, ox = st.dir > 0 ? st.x1 - hh * 0.55 : st.x0 + hh * 0.55, y = st.top - hh * 0.05; paper(q, rect(ox - hh * 0.5, y, hh * 1.0, S.deck - y), '#a8583a', 1); paper(q, function (p) { p.beginPath(); p.arc(ox, y, hh * 0.5, Math.PI, TAU); p.closePath(); }, '#b8683a', 1.2);
      for (var r2 = 1; r2 < 4; r2++) { q.strokeStyle = 'rgba(80,30,10,.35)'; q.lineWidth = 1; q.beginPath(); q.arc(ox, y, hh * 0.5 * r2 / 4, Math.PI, TAU); q.stroke(); }
      fp(q, [[ox - hh * 0.2, y], [ox - hh * 0.2, y - hh * 0.14], [ox, y - hh * 0.24], [ox + hh * 0.2, y - hh * 0.14], [ox + hh * 0.2, y]], '#1a0a04'); fr(q, ox - hh * 0.06, y - hh * 0.75, hh * 0.12, hh * 0.27, '#8a8e94'); st.ox = ox; },
    front: function (q, S, L, st) { var hh = S.hh, a = st.dir > 0 ? st.x0 : st.x1 - hh * 0.9, b = a + hh * 0.9; counter(q, a, b, st.top, S.deck, L.ckind || 'wood', hh); DISH[T0(L).ovenDish || 'pizza'](q, (a + b) / 2, st.top, hh * 0.45); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, ox = st.dir > 0 ? st.x1 - hh * 0.55 : st.x0 + hh * 0.55, y = st.top - hh * 0.05; flames(c, ox, y - hh * 0.01, hh * 0.3, hh * 0.18, t, 2); c.save(); c.globalCompositeOperation = 'lighter'; glow(c, ox, y - hh * 0.08, hh * 0.45, '255,120,40', 0.35 + 0.1 * Math.sin(t / 200)); c.restore();
      var k = 0.5 + 0.5 * Math.sin(t / 900), px = lerp(ox - st.dir * hh * 0.5, ox - st.dir * hh * 0.12, k), py = y - hh * 0.04;
      ln(c, [[px, py], [px - st.dir * hh * 0.5, py - hh * 0.08]], '#c8a060', hh * 0.03); fe(c, px, py, hh * 0.1, hh * 0.02, '#c8a060'); if (k < 0.5) fe(c, px, py - hh * 0.02, hh * 0.08, hh * 0.018, '#e8642a');
      cookAt(c, S, { cx: st.cx, dir: st.dir }, d, T, [px - st.dir * hh * 0.4, py - hh * 0.06], [px - st.dir * hh * 0.25, py - hh * 0.04], 0.15); }
  },
  /* the tandoor: a clay drum glowing at its mouth, naan slapped to its wall */
  tandoor: { w: 1.6,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh, tx = st.tx; counter(q, st.dir > 0 ? tx + hh * 0.25 : st.x0, st.dir > 0 ? st.x1 : tx - hh * 0.25, st.top, S.deck, L.ckind || 'tile', hh);
      paper(q, poly([[tx - hh * 0.22, st.top - hh * 0.05], [tx + hh * 0.22, st.top - hh * 0.05], [tx + hh * 0.26, S.deck], [tx - hh * 0.26, S.deck]]), '#b8683a', 1); fe(q, tx, st.top - hh * 0.05, hh * 0.22, hh * 0.05, '#2a0a04'); laiKham(q, tx - hh * 0.2, tx + hh * 0.2, st.top + hh * 0.15, hh * 0.04, '#f2d27a');
      DISH.naan(q, st.dir > 0 ? st.x1 - hh * 0.35 : st.x0 + hh * 0.35, st.top, hh * 0.38); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, tx = st.tx, u = (t / 2600) % 1, dip = u < 0.3 ? ease(u / 0.3) : u < 0.5 ? 1 : 1 - ease((u - 0.5) / 0.5);
      c.save(); c.globalCompositeOperation = 'lighter'; glow(c, tx, st.top - hh * 0.08, hh * 0.4, '255,120,40', 0.4 + 0.1 * Math.sin(t / 180)); c.restore(); steam(c, tx, st.top - hh * 0.1, hh * 0.5, t, 3, 2, 0.4);
      var hand = [tx - st.dir * hh * 0.05, st.top - hh * 0.25 + dip * hh * 0.2]; cookAt(c, S, st, d, T, hand, [tx - st.dir * hh * 0.1, st.top - hh * 0.3], 0.25 + dip * 0.25); if (dip < 0.6) fe(c, hand[0] + st.dir * hh * 0.04, hand[1] - hh * 0.02, hh * 0.08, hh * 0.05, '#f2dcae'); }
  },
  /* a cold cabinet of plates to cook at the table, a server carrying them */
  buffet: { w: 1.45,
    back: function (q, S, L, st) { var hh = S.hh, a = st.x0 + hh * 0.05, b = st.x1 - hh * 0.05, top = S.deck - hh * 1.05; paper(q, rect(a, top, b - a, hh * 1.05), '#e8eaee', 0.8); fr(q, a + 3, top + hh * 0.08, b - a - 6, hh * 0.9, '#eaf4fa');
      for (var s = 0; s < 4; s++) { var sy = top + hh * (0.3 + s * 0.22); fr(q, a + 3, sy, b - a - 6, 2, '#9aa0a8'); for (var k = 0; k < 4; k++) { var px = a + (b - a) * (k + 0.5) / 4; fe(q, px, sy - 2, (b - a) * 0.1, 3, '#f6f2ea'); fe(q, px, sy - 4, (b - a) * 0.07, 3, ['#e89a8a', '#5aa83a', '#f2e6c9', '#d86a6a'][(k + s) % 4]); } } },
    front: function (q, S, L, st) { var hh = S.hh, bx = (st.x0 + st.x1) / 2; paper(q, poly([[bx - hh * 0.18, S.deck - hh * 0.3], [bx + hh * 0.18, S.deck - hh * 0.3], [bx + hh * 0.14, S.deck], [bx - hh * 0.14, S.deck]]), '#c8ccd2', 0.6); for (var i = 0; i < 4; i++) bottle(q, bx - hh * 0.12 + i * hh * 0.08, S.deck - hh * 0.22, hh * 0.35, i % 2 ? '#3a5a2a' : '#5a3212'); fe(q, bx, S.deck - hh * 0.28, hh * 0.15, hh * 0.03, 'rgba(255,255,255,.6)'); },
    live: function (c, S, L, st, d, T) {}
  },
  /* seafood on ice, prawns on the grill */
  ice: { w: 1.85,
    back: function (q, S, L, st) { var hh = S.hh; q.strokeStyle = 'rgba(90,70,40,.5)'; q.lineWidth = 1; for (var x = st.x0; x < st.x1; x += hh * 0.1) { q.beginPath(); q.moveTo(x, st.top - hh * 0.7); q.lineTo(x + hh * 0.3, st.top - hh * 0.4); q.stroke(); q.beginPath(); q.moveTo(x + hh * 0.3, st.top - hh * 0.7); q.lineTo(x, st.top - hh * 0.4); q.stroke(); } for (var i = 0; i < 3; i++) fe(q, st.x0 + (st.x1 - st.x0) * (i + 0.5) / 3, st.top - hh * 0.4, hh * 0.04, hh * 0.04, '#f29a1a'); },
    front: function (q, S, L, st) { var hh = S.hh, a = st.dir > 0 ? st.x0 + hh * 0.75 : st.x0 + hh * 0.05, b = st.dir > 0 ? st.x1 - hh * 0.05 : st.x1 - hh * 0.75; counter(q, st.x0, st.x1, st.top, S.deck, 'steel', hh);
      paper(q, poly([[a, st.top], [a + hh * 0.05, st.top - hh * 0.14], [b - hh * 0.05, st.top - hh * 0.14], [b, st.top]]), '#eef4f8', 0.5); for (var i = 0; i < 18; i++) fe(q, a + (i * 37 % 18) / 18 * (b - a), st.top - hh * (0.04 + (i % 3) * 0.04), 1.6, 1.6, 'rgba(160,200,220,.6)');
      for (i = 0; i < 4; i++) { var x = a + (b - a) * (i + 0.5) / 4; if (i % 2) { paper(q, E(x, st.top - hh * 0.17, hh * 0.13, hh * 0.04, 0.1), '#a8b4c0', 0.3); fp(q, [[x + hh * 0.12, st.top - hh * 0.17], [x + hh * 0.18, st.top - hh * 0.22], [x + hh * 0.18, st.top - hh * 0.12]], '#a8b4c0'); fe(q, x - hh * 0.08, st.top - hh * 0.18, 1.2, 1.2, '#1a1a1a'); } else { for (var k = 0; k < 3; k++) { q.strokeStyle = '#e8642a'; q.lineWidth = hh * 0.035; q.beginPath(); q.arc(x - hh * 0.06 + k * hh * 0.06, st.top - hh * 0.17, hh * 0.035, Math.PI, Math.PI * 2.1); q.stroke(); } } }
      var gx = st.dir > 0 ? st.x0 + hh * 0.38 : st.x1 - hh * 0.38; fr(q, gx - hh * 0.28, st.top - hh * 0.06, hh * 0.56, hh * 0.06, '#3a3e44'); for (i = 0; i < 4; i++) { q.strokeStyle = '#f0703a'; q.lineWidth = hh * 0.04; q.beginPath(); q.arc(gx - hh * 0.18 + i * hh * 0.12, st.top - hh * 0.1, hh * 0.04, Math.PI, Math.PI * 2.1); q.stroke(); } st.gx = gx; },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, gx = st.dir > 0 ? st.x0 + hh * 0.38 : st.x1 - hh * 0.38; c.save(); c.globalCompositeOperation = 'lighter'; glow(c, gx, st.top - hh * 0.05, hh * 0.35, '255,110,30', 0.3 + 0.1 * Math.sin(t / 230)); c.restore(); smoke(c, gx, st.top - hh * 0.12, hh * 0.9, t, 0.1);
      cookAt(c, S, { cx: gx - st.dir * hh * 0.28 + st.dir * 0.0, dir: st.dir }, d, T, [gx + Math.sin(t / 600) * hh * 0.1, st.top - hh * 0.16], [gx - st.dir * hh * 0.05, st.top - hh * 0.3], 0.15); }
  }
};
/* hung in the glass: steamed chicken, roast duck, red pork */
function hung(q, k, x, y, hh) {
  if (k === 'pork') { for (var i = 0; i < 2; i++) paper(q, rect(x - hh * 0.05 + i * hh * 0.06, y, hh * 0.05, hh * 0.32), '#b8302a', 0.3); return; }
  var col = k === 'duck' ? '#8a3a14' : '#f2dca0', s = hh * 0.13; paper(q, function (p) { p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + s * 1.2, y + s * 0.6, x + s * 0.7, y + s * 2.3); p.quadraticCurveTo(x, y + s * 2.7, x - s * 0.7, y + s * 2.3); p.quadraticCurveTo(x - s * 1.2, y + s * 0.6, x, y); p.closePath(); }, col, 0.4);
  ln(q, [[x - s * 0.3, y + s * 0.1], [x - s * 0.5, y - s * 0.3]], col, s * 0.25); ln(q, [[x + s * 0.3, y + s * 0.1], [x + s * 0.5, y - s * 0.3]], col, s * 0.25); fe(q, x - s * 0.3, y + s * 1.2, s * 0.2, s * 0.6, 'rgba(255,255,255,.2)');
}
function grillItems(q, kind, a, b, y, hh) {
  var n = Math.max(3, Math.floor((b - a) / (hh * (kind === 'chicken' || kind === 'fish' ? 0.32 : 0.1)))), i, x;
  for (i = 0; i < n; i++) { x = a + (b - a) * (i + 0.5) / n;
    if (kind === 'skewer' || kind === 'mala') { ln(q, [[x - hh * 0.02, y + hh * 0.02], [x + hh * 0.03, y - hh * 0.28]], '#d8b878', 1.3); for (var k = 0; k < 4; k++) fe(q, x + k * hh * 0.01, y - hh * (0.04 + k * 0.055), hh * 0.035, hh * 0.028, kind === 'mala' ? ['#d84a2a', '#f2e6c9', '#a8302a', '#5aa83a'][k] : ['#8a4a1e', '#a8582a'][k % 2]); }
    else if (kind === 'chicken') { paper(q, function (p) { p.beginPath(); p.ellipse(x, y - hh * 0.12, hh * 0.12, hh * 0.14, 0, 0, TAU); }, '#b8681e', 0.3); ln(q, [[x - hh * 0.12, y - hh * 0.3], [x - hh * 0.12, y + hh * 0.02]], '#c8a060', 1.5); ln(q, [[x + hh * 0.12, y - hh * 0.3], [x + hh * 0.12, y + hh * 0.02]], '#c8a060', 1.5); ln(q, [[x - hh * 0.14, y - hh * 0.2], [x + hh * 0.14, y - hh * 0.2]], '#c8a060', 1.2); }
    else if (kind === 'sausage') { q.strokeStyle = '#a8452a'; q.lineWidth = hh * 0.045; q.beginPath(); for (var t2 = 0; t2 < 3 * TAU; t2 += 0.3) { var rr = hh * 0.008 * t2; q.lineTo(x + Math.cos(t2) * rr, y - hh * 0.04 + Math.sin(t2) * rr * 0.35); } q.stroke(); }
    else if (kind === 'fish') { paper(q, E(x, y - hh * 0.05, hh * 0.14, hh * 0.045), '#f2f0ea', 0.3); fp(q, [[x + hh * 0.13, y - hh * 0.05], [x + hh * 0.2, y - hh * 0.1], [x + hh * 0.2, y]], '#e8e4da'); ln(q, [[x - hh * 0.14, y - hh * 0.05], [x - hh * 0.22, y - hh * 0.12]], '#7ab84a', 1.5); }
    else if (kind === 'steak') { paper(q, function (p) { p.beginPath(); p.ellipse(x, y - hh * 0.03, hh * 0.05, hh * 0.03, 0.1, 0, TAU); }, '#7a3418', 0.2); ln(q, [[x - hh * 0.03, y - hh * 0.05], [x + hh * 0.02, y - hh * 0.01]], '#3a1608', 1); }
    else if (kind === 'corn') { paper(q, E(x, y - hh * 0.04, hh * 0.04, hh * 0.1, 1.2), '#f2c24a', 0.3); }
  }
}
function caddy(q, x, y, hh) {
  fr(q, x - hh * 0.13, y - hh * 0.02, hh * 0.26, hh * 0.02, '#c8ccd2'); ln(q, [[x, y - hh * 0.02], [x, y - hh * 0.2]], '#c8ccd2', 1.5);
  ['#f6f2ea', '#c8402a', '#a8582a', '#f2e8c8'].forEach(function (col, i) { var jx = x - hh * 0.1 + i * hh * 0.067; fp(q, [[jx - hh * 0.025, y - hh * 0.02], [jx - hh * 0.025, y - hh * 0.1], [jx + hh * 0.025, y - hh * 0.1], [jx + hh * 0.025, y - hh * 0.02]], 'rgba(230,240,245,.8)'); fr(q, jx - hh * 0.022, y - hh * 0.07, hh * 0.044, hh * 0.05, col); fr(q, jx - hh * 0.027, y - hh * 0.115, hh * 0.054, hh * 0.018, '#c8ccd2'); });
}

/* the latte art seen from above, drawn as it forms: a heart, a rosetta (leaves stacked along a
   line), or a tulip (stacked blobs); v = 0 … 1 the pour */
function latteArt(c, x, y, r, kind, v) {
  fe(c, x, y, r, r, '#f6f2ea'); fe(c, x, y, r * 0.84, r * 0.84, '#a8642a'); fe(c, x - r * 0.25, y - r * 0.25, r * 0.4, r * 0.3, 'rgba(255,220,170,.25)');
  c.fillStyle = '#fbf3e4';
  if (kind === 'heart') { var s = r * 0.55 * Math.min(1, v * 1.3); c.beginPath(); c.arc(x - s * 0.4, y - s * 0.15, s * 0.45, 0, TAU); c.arc(x + s * 0.4, y - s * 0.15, s * 0.45, 0, TAU); c.fill(); fp(c, [[x - s * 0.82, y], [x + s * 0.82, y], [x, y + s * 0.85]], '#fbf3e4'); }
  else if (kind === 'tulip') { var n = Math.ceil(v * 4); for (var i = 0; i < n; i++) { var yy = y + r * 0.45 - i * r * 0.28, w = r * (0.55 - i * 0.08); c.beginPath(); c.ellipse(x, yy, w, r * 0.17, 0, 0, TAU); c.fill(); c.fillStyle = '#a8642a'; c.beginPath(); c.ellipse(x, yy + r * 0.07, w * 0.7, r * 0.09, 0, 0, TAU); c.fill(); c.fillStyle = '#fbf3e4'; } }
  else { var m = Math.ceil(v * 8); for (i = 0; i < m; i++) { var ly = y + r * 0.6 - i * r * 0.16, lw = r * (0.62 - i * 0.06); c.strokeStyle = '#fbf3e4'; c.lineWidth = Math.max(1, r * 0.09); c.beginPath(); c.ellipse(x, ly, lw, r * 0.1, 0, Math.PI * 1.05, Math.PI * 1.95); c.stroke(); } if (v > 0.9) ln(c, [[x, y - r * 0.6], [x, y + r * 0.7]], '#fbf3e4', r * 0.06); }
}
function cakeDome(q, x, y, hh, k) {
  fr(q, x - hh * 0.03, y - hh * 0.08, hh * 0.06, hh * 0.08, '#c8ccd2'); fe(q, x, y - hh * 0.08, hh * 0.22, hh * 0.03, '#d8dce2');
  var cc = [['#f6e2c8', '#8a4a2a'], ['#5a2e1a', '#f6e2c8'], ['#f8d0dc', '#f6f2ea'], ['#f2e0a0', '#e8a02a']][k % 4];
  paper(q, rect(x - hh * 0.17, y - hh * 0.26, hh * 0.34, hh * 0.17), cc[0], 0.3); fr(q, x - hh * 0.17, y - hh * 0.19, hh * 0.34, hh * 0.03, cc[1]); fr(q, x - hh * 0.17, y - hh * 0.27, hh * 0.34, hh * 0.03, '#fbf6f0');
  for (var i = 0; i < 5; i++) fe(q, x - hh * 0.13 + i * hh * 0.065, y - hh * 0.29, hh * 0.02, hh * 0.02, i % 2 ? '#d8242a' : '#fbf6f0');
  fp(q, [[x - hh * 0.06, y - hh * 0.26], [x + hh * 0.06, y - hh * 0.26], [x + hh * 0.17, y - hh * 0.09], [x + hh * 0.06, y - hh * 0.09]], 'rgba(0,0,0,0)');
  q.save(); q.globalAlpha = 0.35; paper(q, function (p) { p.beginPath(); p.ellipse(x, y - hh * 0.09, hh * 0.22, hh * 0.3, 0, Math.PI, TAU); p.closePath(); }, '#dff0f8', 0.2); q.restore();
  ln(q, [[x - hh * 0.12, y - hh * 0.3], [x - hh * 0.16, y - hh * 0.18]], 'rgba(255,255,255,.7)', 1.5); fe(q, x, y - hh * 0.4, hh * 0.025, hh * 0.02, '#c8ccd2');
}
function pastryCase(q, a, b, top, deck, hh, kinds) {
  paper(q, rect(a, top, b - a, deck - top), '#e8e2d6', 1); paper(q, rect(a + 2, top - hh * 0.28, b - a - 4, hh * 0.28), 'rgba(220,240,250,.35)', 0.4);
  var n = Math.max(3, Math.round((b - a) / (hh * 0.22)));
  for (var row = 0; row < 2; row++) { var y = row ? top + hh * 0.2 : top - hh * 0.03; if (row) fr(q, a + 4, top + hh * 0.06, b - a - 8, hh * 0.18, 'rgba(220,240,250,.5)');
    for (var i = 0; i < n; i++) { var x = a + (b - a) * (i + 0.5) / n, k = kinds[(i + row * 2) % kinds.length], s = hh * 0.1;
      if (k === 'croissant') for (var j = -2; j <= 2; j++) fe(q, x + j * s * 0.35, y - s * 0.35 - (2 - Math.abs(j)) * s * 0.1, s * 0.3, s * (0.25 + (2 - Math.abs(j)) * 0.06), j % 2 ? '#c8822a' : '#e0a04a', j * 0.3);
      else if (k === 'bun') { fe(q, x, y - s * 0.4, s * 0.8, s * 0.5, '#d8902a'); fe(q, x - s * 0.2, y - s * 0.6, s * 0.3, s * 0.12, 'rgba(255,240,200,.5)'); }
      else if (k === 'tart') { fp(q, [[x - s * 0.8, y - s * 0.35], [x + s * 0.8, y - s * 0.35], [x + s * 0.6, y], [x - s * 0.6, y]], '#d8a050'); fe(q, x, y - s * 0.35, s * 0.7, s * 0.15, '#f2c42a'); }
      else if (k === 'donut') { fe(q, x, y - s * 0.4, s * 0.8, s * 0.4, '#d8902a'); fe(q, x, y - s * 0.5, s * 0.75, s * 0.3, ['#f08aa0', '#5a2e1a', '#f6f2ea'][i % 3]); fe(q, x, y - s * 0.5, s * 0.2, s * 0.08, '#e8e2d6'); }
      else if (k === 'slice') { fp(q, [[x - s * 0.7, y], [x + s * 0.7, y], [x + s * 0.7, y - s * 0.8], [x - s * 0.3, y - s * 0.95]], ['#f6e2c8', '#5a2e1a', '#f8d0dc', '#f2e0a0'][i % 4]); fr(q, x - s * 0.7, y - s * 0.45, s * 1.4, s * 0.12, '#fbf6f0'); fe(q, x + s * 0.2, y - s * 0.95, s * 0.12, s * 0.12, '#d8242a'); }
      else if (k === 'khanom') for (j = 0; j < 4; j++) fr(q, x - s * 0.6, y - s * (0.25 + j * 0.22), s * 1.2, s * 0.22, j % 2 ? '#f6f2ea' : ['#2fae5a', '#e8508a', '#8a5ad8', '#f2b02a'][i % 4]);
      else if (k === 'baguette') fe(q, x, y - s * 0.3, s * 1.0, s * 0.25, '#d8a050', -0.15);
      else if (k === 'icecream') { fe(q, x, y - s * 0.3, s * 0.75, s * 0.35, ['#f8d0dc', '#5a2e1a', '#c8e8a0', '#fbf2c8', '#a8d8f0'][i % 5]); }
    } }
  fr(q, a, top - hh * 0.3, b - a, 2, '#c8ccd2');
}
var ST2 = {
  /* the espresso machine: the wand hisses into the milk, then the pour, the art seen from above as it forms; the shot drips, y = ½gt² */
  espresso: { w: 1.95,
    back: function (q, S, L, st) { var hh = S.hh; shelf(q, st.x0, st.x1, st.top - hh * 0.72, hh, [jar('#5a3212'), jar('#3a2a1a'), function (q2, x, y) { for (var i = 0; i < 3; i++) fp(q2, [[x - 6 + i * 4, y], [x - 4 + i * 4, y - 7], [x + i * 4, y - 7], [x + 2 + i * 4, y]], '#f6f2ea'); }, jar('#8a5a2a'), jar('#c8a060')]); },
    front: function (q, S, L, st) { var hh = S.hh, mx = st.tx, col = L.machine || '#c8ccd2', y = st.top - hh * 0.02; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'wood', hh);
      paper(q, rect(mx - hh * 0.32, y - hh * 0.36, hh * 0.64, hh * 0.3), col, 1); fr(q, mx - hh * 0.32, y - hh * 0.36, hh * 0.64, hh * 0.05, mixc(col, '#000000', 0.2)); fr(q, mx - hh * 0.3, y - hh * 0.06, hh * 0.6, hh * 0.04, '#5a5e64');
      fe(q, mx, y - hh * 0.25, hh * 0.05, hh * 0.05, '#f6f2ea'); q.strokeStyle = '#2a2a2e'; q.lineWidth = 1; q.beginPath(); q.arc(mx, y - hh * 0.25, hh * 0.05, 0, TAU); q.stroke(); ln(q, [[mx, y - hh * 0.25], [mx + hh * 0.03, y - hh * 0.27]], '#c0392b', 1);
      [-0.16, 0.16].forEach(function (k) { fr(q, mx + k * hh - hh * 0.04, y - hh * 0.06, hh * 0.08, hh * 0.05, '#9aa0a8'); ln(q, [[mx + k * hh, y - hh * 0.03], [mx + k * hh + (k < 0 ? -1 : 1) * hh * 0.14, y - hh * 0.05]], '#1a1a1e', hh * 0.03); });
      for (var i = 0; i < 4; i++) { var cx = mx - hh * 0.22 + i * hh * 0.14; fp(q, [[cx - hh * 0.04, y - hh * 0.36], [cx + hh * 0.04, y - hh * 0.36], [cx + hh * 0.03, y - hh * 0.42], [cx - hh * 0.03, y - hh * 0.42]], '#f6f2ea'); }
      fr(q, mx - hh * 0.06, y, hh * 0.12, 2, '#3a3e44');
      var gx = mx + st.dir * hh * 0.48; fr(q, gx - hh * 0.06, y - hh * 0.3, hh * 0.12, hh * 0.3, '#2a2a2e'); fp(q, [[gx - hh * 0.09, y - hh * 0.48], [gx + hh * 0.09, y - hh * 0.48], [gx + hh * 0.04, y - hh * 0.3], [gx - hh * 0.04, y - hh * 0.3]], 'rgba(220,235,240,.6)'); fe(q, gx, y - hh * 0.36, hh * 0.05, hh * 0.04, '#5a2e12');
      if (L.cakes !== false) cakeDome(q, st.dir > 0 ? st.x0 + hh * 0.26 : st.x1 - hh * 0.26, y, hh, S.seed % 4); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, mx = st.tx, y = st.top - hh * 0.02, u = (t / 9000) % 1, wx = mx - st.dir * hh * 0.34, cup = [st.cx + st.dir * hh * 0.22, y];
      var i;
      var sg = (t / 600) % 1; fe(c, mx - hh * 0.16, y - hh * 0.0 + sg * sg * hh * 0.05, 1.2, 1.8, '#3a1a08');
      fp(c, [[cup[0] - hh * 0.06, y - hh * 0.12], [cup[0] + hh * 0.06, y - hh * 0.12], [cup[0] + hh * 0.045, y], [cup[0] - hh * 0.045, y]], '#f6f2ea'); fe(c, cup[0], y, hh * 0.08, hh * 0.015, '#f6f2ea');
      var pit, tilt = 0, me;
      if (u < 0.5) { pit = [wx, y - hh * 0.18]; ln(c, [[wx + st.dir * hh * 0.04, y - hh * 0.26], [wx, y - hh * 0.12]], '#9aa0a8', 1.5); steam(c, wx, y - hh * 0.3, hh * 0.45, t, 1, 3, 0.75);
        for (i = 0; i < 3; i++) { var ha = (t / 90 + i) % 3; c.strokeStyle = 'rgba(255,255,255,' + (0.6 - ha * 0.2) + ')'; c.lineWidth = 1; c.beginPath(); c.arc(wx, y - hh * 0.2, hh * (0.08 + ha * 0.04), -0.6 - st.dir * 0.0, 0.6); c.stroke(); } }
      else { var v = Math.min(1, (u - 0.5) / 0.38); pit = [cup[0] - st.dir * hh * 0.08, y - hh * 0.24]; tilt = 0.9 * st.dir;
        ln(c, [[pit[0] + st.dir * hh * 0.06, pit[1] + hh * 0.02], [cup[0], y - hh * 0.11]], '#fbf3e4', hh * 0.02);
        var ix = cup[0] + st.dir * hh * 0.05, iy = y - hh * 0.62; for (i = 0; i < 3; i++) fe(c, lerp(cup[0], ix, (i + 1) / 4), lerp(y - hh * 0.16, iy + hh * 0.18, (i + 1) / 4), 1.5, 1.5, 'rgba(255,255,255,.7)');
        latteArt(c, ix, iy, hh * 0.17, L.art || 'rosetta', v); }
      me = cookAt(c, S, st, d, T, [pit[0] - st.dir * hh * 0.08, pit[1] + hh * 0.02], u < 0.5 ? [wx + st.dir * hh * 0.08, y - hh * 0.3] : [st.cx + st.dir * hh * 0.12, y - hh * 0.25], 0.08);
      c.save(); c.translate(pit[0], pit[1]); c.rotate(tilt * 0.6); fp(c, [[-hh * 0.06, -hh * 0.08], [hh * 0.06, -hh * 0.08], [hh * 0.05, hh * 0.06], [-hh * 0.05, hh * 0.06]], '#d8dce2'); fp(c, [[hh * 0.06, -hh * 0.08], [hh * 0.1, -hh * 0.1], [hh * 0.06, -hh * 0.05]], '#d8dce2'); c.restore(); }
  },
  /* the pour-over: a gooseneck kettle in slow circles, x = r·cos ωt, coffee dripping into the server below */
  pourover: { w: 1.7,
    back: function (q, S, L, st) { ST2.espresso.back(q, S, L, st); },
    front: function (q, S, L, st) { var hh = S.hh, dx = st.tx, y = st.top - hh * 0.02; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'wood', hh);
      fr(q, dx - hh * 0.12, y - hh * 0.03, hh * 0.24, hh * 0.03, '#2a2a2e'); fr(q, dx - hh * 0.03, y - hh * 0.025, hh * 0.06, 2, '#7ae05a');
      paper(q, function (p) { p.beginPath(); p.moveTo(dx - hh * 0.05, y - hh * 0.28); p.lineTo(dx + hh * 0.05, y - hh * 0.28); p.quadraticCurveTo(dx + hh * 0.12, y - hh * 0.15, dx + hh * 0.08, y - hh * 0.03); p.lineTo(dx - hh * 0.08, y - hh * 0.03); p.quadraticCurveTo(dx - hh * 0.12, y - hh * 0.15, dx - hh * 0.05, y - hh * 0.28); p.closePath(); }, 'rgba(220,235,240,.5)', 0.3);
      fp(q, [[dx - hh * 0.13, y - hh * 0.42], [dx + hh * 0.13, y - hh * 0.42], [dx + hh * 0.03, y - hh * 0.29], [dx - hh * 0.03, y - hh * 0.29]], L.dripper || '#f6f2ea'); fr(q, dx - hh * 0.09, y - hh * 0.3, hh * 0.18, 2, L.dripper || '#f6f2ea');
      var kx = st.dir > 0 ? st.x1 - hh * 0.25 : st.x0 + hh * 0.25; for (var i = 0; i < 3; i++) fp(q, [[kx - hh * 0.05 + i * hh * 0.1 - hh * 0.04, y], [kx + i * hh * 0.1 - hh * 0.04, y - hh * 0.1], [kx + i * hh * 0.1, y - hh * 0.1], [kx + i * hh * 0.1 + hh * 0.01, y]], ['#e8d8c0', '#c8a080', '#f6f2ea'][i]);
      if (L.cakes !== false) cakeDome(q, st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3, y, hh, S.seed % 4); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, dx = st.tx, y = st.top - hh * 0.02, lev = 0.15 + 0.7 * ((t / 14000) % 1), a = t / 500;
      fp(c, [[dx - hh * 0.08 - (1 - lev) * 0, y - hh * 0.03 - lev * hh * 0.12], [dx + hh * 0.08, y - hh * 0.03 - lev * hh * 0.12], [dx + hh * 0.08, y - hh * 0.04], [dx - hh * 0.08, y - hh * 0.04]], 'rgba(90,40,10,.75)');
      for (var i = 0; i < 2; i++) { var dv = ((t / 450 + i * 0.5) % 1); fe(c, dx, y - hh * 0.29 + dv * dv * hh * (0.25 - lev * 0.12), 1.2, 1.7, '#5a2a0a'); }
      fe(c, dx, y - hh * 0.42, hh * 0.1, hh * 0.02, '#6a3a1a'); fe(c, dx + Math.cos(a) * hh * 0.04, y - hh * 0.43, hh * 0.03, hh * 0.01, '#c8925a');
      var kt = [dx - st.dir * hh * 0.24 + Math.cos(a) * hh * 0.025, y - hh * 0.62 + Math.sin(a) * hh * 0.012], sp = [dx + Math.cos(a) * hh * 0.035, y - hh * 0.5];
      cookAt(c, S, st, d, T, [kt[0] - st.dir * hh * 0.1, kt[1] + hh * 0.02], [st.cx + st.dir * hh * 0.1, y - hh * 0.3], 0.1);
      paper(c, E(kt[0], kt[1], hh * 0.09, hh * 0.08), L.kettle || '#2a2a2e', 0.3); fr(c, kt[0] - hh * 0.09, kt[1] + hh * 0.06, hh * 0.18, hh * 0.02, L.kettle || '#2a2a2e');
      c.strokeStyle = L.kettle || '#2a2a2e'; c.lineWidth = hh * 0.025; c.beginPath(); c.moveTo(kt[0] + st.dir * hh * 0.07, kt[1] + hh * 0.04); c.quadraticCurveTo(kt[0] + st.dir * hh * 0.2, kt[1] + hh * 0.05, sp[0] - st.dir * hh * 0.06, sp[1] - hh * 0.08); c.stroke();
      c.strokeStyle = 'rgba(210,230,240,.85)'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(sp[0] - st.dir * hh * 0.06, sp[1] - hh * 0.08); c.quadraticCurveTo(sp[0], sp[1] - hh * 0.06, sp[0], y - hh * 0.43); c.stroke();
      steam(c, dx, y - hh * 0.45, hh * 0.35, t, 2, 2, 0.5); }
  },
  /* the bar: bottles lit from behind, the taps, the shaker's beat y = A·sin 2πft, or a glass filling */
  bar: { w: 2.05,
    back: function (q, S, L, st) { var hh = S.hh, r = K.rnd(S.seed + 17);
      for (var s = 0; s < 2; s++) { var sy = st.top - hh * (0.55 + s * 0.3); fr(q, st.x0, sy, st.x1 - st.x0, 3, '#5a3a20'); var n = Math.round((st.x1 - st.x0) / (hh * 0.11));
        for (var i = 0; i < n; i++) { var x = st.x0 + (st.x1 - st.x0) * (i + 0.5) / n, bh = hh * (0.16 + r() * 0.1), col = pick(r, ['#3a6a2a', '#5a3212', '#c8a050', '#2a4a7a', '#8a2a2a', '#e8eef2', '#d8a02a']); fp(q, [[x - hh * 0.03, sy], [x - hh * 0.03, sy - bh * 0.65], [x - hh * 0.012, sy - bh * 0.8], [x - hh * 0.012, sy - bh], [x + hh * 0.012, sy - bh], [x + hh * 0.012, sy - bh * 0.8], [x + hh * 0.03, sy - bh * 0.65], [x + hh * 0.03, sy]], col); fr(q, x - hh * 0.025, sy - bh * 0.45, hh * 0.05, bh * 0.15, 'rgba(242,230,201,.8)'); } } },
    front: function (q, S, L, st) { var hh = S.hh, tx = st.tx, y = st.top; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'wood', hh); fr(q, st.x0, S.deck - hh * 0.12, st.x1 - st.x0, 2.5, '#c8a050');
      fr(q, tx - hh * 0.03, y - hh * 0.3, hh * 0.06, hh * 0.3, '#c8ccd2'); fr(q, tx - hh * 0.2, y - hh * 0.32, hh * 0.4, hh * 0.05, '#c8ccd2');
      for (var i = 0; i < 3; i++) { var hx2 = tx - hh * 0.14 + i * hh * 0.14; fr(q, hx2 - hh * 0.02, y - hh * 0.46, hh * 0.04, hh * 0.15, ['#2f6db0', '#c0392b', '#2f8f5b'][(i + S.seed) % 3]); ln(q, [[hx2, y - hh * 0.28], [hx2, y - hh * 0.22]], '#9aa0a8', 1.5); }
      fr(q, tx - hh * 0.22, y - hh * 0.03, hh * 0.44, hh * 0.03, '#3a3e44'); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, y = st.top;
      if (L.barMode === 'shake') { var s = Math.sin(t / 75) * hh * 0.05, sx = st.cx + st.dir * hh * 0.12, sy = S.deck - hh * 0.9 + s;
        cookAt(c, S, st, d, T, [sx, sy + hh * 0.06], [sx - st.dir * hh * 0.02, sy - hh * 0.05], 0.05);
        c.save(); c.translate(sx, sy); c.rotate(st.dir * (0.4 + s / hh)); fp(c, [[-hh * 0.045, -hh * 0.12], [hh * 0.045, -hh * 0.12], [hh * 0.035, hh * 0.1], [-hh * 0.035, hh * 0.1]], '#d8dce2'); fr(c, -hh * 0.03, -hh * 0.16, hh * 0.06, hh * 0.04, '#b8bcc2'); c.restore(); }
      else { var hx2 = st.tx - hh * 0.14 + ((S.seed % 3)) * hh * 0.14, u = (t / 4000) % 1, lev = u < 0.75 ? u / 0.75 : 1, pull = u < 0.75 ? 0.5 : 0;
        c.save(); c.translate(hx2, y - hh * 0.32); c.rotate(-st.dir * pull); fr(c, -hh * 0.02, -hh * 0.14, hh * 0.04, hh * 0.15, '#2f6db0'); c.restore();
        if (u < 0.75) ln(c, [[hx2, y - hh * 0.22], [hx2, y - hh * 0.04 - lev * hh * 0.18]], '#f2b02a', 1.6);
        glassCup(c, hx2, y - hh * 0.03, hh * 0.12, hh * 0.22, '#f2b02a', lev * 0.85); if (lev > 0.6) fe(c, hx2, y - hh * 0.03 - hh * 0.22 * lev * 0.85, hh * 0.06, hh * 0.02, '#fffaf0');
        cookAt(c, S, st, d, T, [hx2 - st.dir * hh * 0.04, y - hh * 0.44 + pull * hh * 0.05], [st.cx + st.dir * hh * 0.12, y - hh * 0.2], 0.08); } }
  },
  /* the deck oven: loaves behind glowing doors, the peel drawn out with fresh bread */
  bake: { w: 2.0,
    back: function (q, S, L, st) { var hh = S.hh, ox = st.dir > 0 ? st.x0 + hh * 0.55 : st.x1 - hh * 0.55, top = S.deck - hh * 1.15; paper(q, rect(ox - hh * 0.48, top, hh * 0.96, hh * 0.85), '#c8ccd2', 1); for (var k = 0; k < 2; k++) { var wy = top + hh * (0.1 + k * 0.38); fr(q, ox - hh * 0.4, wy, hh * 0.8, hh * 0.3, '#2a1a10'); fr(q, ox - hh * 0.4, wy - hh * 0.04, hh * 0.8, hh * 0.03, '#5a5e64'); for (var i = 0; i < 4; i++) fe(q, ox - hh * 0.3 + i * hh * 0.2, wy + hh * 0.22, hh * 0.08, hh * 0.05, '#d8902a'); }
      ln(q, [[ox - hh * 0.4, S.deck - hh * 0.3], [ox - hh * 0.4, S.deck]], '#5a5e64', 2); ln(q, [[ox + hh * 0.4, S.deck - hh * 0.3], [ox + hh * 0.4, S.deck]], '#5a5e64', 2);
      var rx = st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3; for (var s = 0; s < 4; s++) { var sy = S.deck - hh * (0.2 + s * 0.25); fr(q, rx - hh * 0.25, sy, hh * 0.5, 2, '#9aa0a8'); for (i = 0; i < 3; i++) fe(q, rx - hh * 0.16 + i * hh * 0.16, sy - hh * 0.04, hh * 0.07, hh * 0.04, s % 2 ? '#d8a050' : '#c8822a'); } ln(q, [[rx - hh * 0.25, S.deck], [rx - hh * 0.25, S.deck - hh * 1.0]], '#9aa0a8', 2); ln(q, [[rx + hh * 0.25, S.deck], [rx + hh * 0.25, S.deck - hh * 1.0]], '#9aa0a8', 2); },
    front: function (q, S, L, st) { var hh = S.hh, a = st.dir > 0 ? st.x0 + hh * 1.05 : st.x0 + hh * 0.05, b = st.dir > 0 ? st.x1 : st.x1 - hh * 1.05; pastryCase(q, a, b, st.top + hh * 0.05, S.deck, hh, L.pastry || ['croissant', 'bun', 'tart', 'baguette']); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, ox = st.dir > 0 ? st.x0 + hh * 0.55 : st.x1 - hh * 0.55, top = S.deck - hh * 1.15, wy = top + hh * 0.48;
      c.save(); c.globalCompositeOperation = 'lighter'; glow(c, ox, wy + hh * 0.15, hh * 0.5, '255,140,50', 0.3 + 0.08 * Math.sin(t / 400)); glow(c, ox, top + hh * 0.25, hh * 0.45, '255,140,50', 0.22); c.restore();
      var k = 0.5 + 0.5 * Math.sin(t / 1100), px = ox + st.dir * lerp(hh * 0.05, hh * 0.5, k), py = wy + hh * 0.22;
      var cx = ox + st.dir * hh * 0.85; cookAt(c, S, { cx: cx, dir: -st.dir }, d, T, [px + st.dir * hh * 0.42, py - hh * 0.06], [px + st.dir * hh * 0.25, py - hh * 0.03], 0.12);
      ln(c, [[px, py], [px + st.dir * hh * 0.5, py - hh * 0.04]], '#c8a060', hh * 0.025); fe(c, px, py, hh * 0.1, hh * 0.015, '#c8a060'); if (k > 0.55) { fe(c, px, py - hh * 0.03, hh * 0.08, hh * 0.035, '#c8822a'); steam(c, px, py - hh * 0.06, hh * 0.35, t, 1, 2, 0.5); } }
  },
  /* khanom krok: an iron pan of half-moon cups, coconut batter bubbling, a spoon going cup to cup */
  khanomkrok: { w: 1.5,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh, px = st.tx; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'wood', hh); paper(q, poly([[px - hh * 0.2, st.top], [px + hh * 0.2, st.top], [px + hh * 0.16, st.top - hh * 0.18], [px - hh * 0.16, st.top - hh * 0.18]]), '#a8582a', 0.8);
      paper(q, E(px, st.top - hh * 0.22, hh * 0.3, hh * 0.07), '#2a2a2e', 0.8); for (var i = 0; i < 6; i++) fe(q, px - hh * 0.22 + i * hh * 0.088, st.top - hh * 0.24, hh * 0.035, hh * 0.018, '#f6f0dc');
      DISH.khanom(q, st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3, st.top, hh * 0.4); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, px = st.tx; c.save(); c.globalCompositeOperation = 'lighter'; glow(c, px, st.top - hh * 0.12, hh * 0.25, '255,110,30', 0.35 + 0.1 * Math.sin(t / 200)); c.restore();
      for (var i = 0; i < 6; i++) { var b = (t / 600 + i * 0.37) % 1; if (b < 0.6) fe(c, px - hh * 0.22 + i * hh * 0.088 + Math.sin(i * 5) * 2, st.top - hh * 0.25, b * 2.2, b * 1.4, 'rgba(255,255,255,.8)'); }
      steam(c, px, st.top - hh * 0.28, hh * 0.45, t, 0, 2, 0.5); var k = Math.floor(t / 700) % 6, sp = [px - hh * 0.22 + k * hh * 0.088, st.top - hh * 0.3 - Math.abs(Math.sin(t / 700 * Math.PI)) * hh * 0.05];
      cookAt(c, S, st, d, T, sp, [st.cx + st.dir * hh * 0.1, st.top - hh * 0.15], 0.15); ln(c, [sp, [sp[0], sp[1] + hh * 0.05]], '#c8ccd2', 1.5); }
  },
  /* bingsu: the ice shaved into a growing mountain, flakes falling */
  bingsu: { w: 1.55,
    back: function (q, S, L, st) { var hh = S.hh; shelf(q, st.x0, st.x1, st.top - hh * 0.62, hh, [jar('#d8242a'), jar('#f7d040'), jar('#5aa83a'), jar('#5a2e1a'), jar('#f08aa0')]); },
    front: function (q, S, L, st) { var hh = S.hh, mx = st.tx; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'white', hh); paper(q, rect(mx - hh * 0.14, st.top - hh * 0.55, hh * 0.28, hh * 0.2), '#e8eaee', 0.8); paper(q, rect(mx - hh * 0.1, st.top - hh * 0.68, hh * 0.2, hh * 0.13), 'rgba(220,240,255,.8)', 0.4); fr(q, mx - hh * 0.04, st.top - hh * 0.35, hh * 0.08, hh * 0.35, '#c8ccd2'); fr(q, mx - hh * 0.14, st.top - hh * 0.02, hh * 0.28, 2, '#9aa0a8');
      pastryCase(q, st.dir > 0 ? st.x1 - hh * 0.55 : st.x0 + hh * 0.05, st.dir > 0 ? st.x1 - hh * 0.05 : st.x0 + hh * 0.55, st.top + hh * 0.05, S.deck, hh, ['icecream']); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, mx = st.tx, u = (t / 7000) % 1, by = st.top - hh * 0.02, bx = mx + st.dir * hh * 0.0;
      var b = bowl(c, bx, by, hh * 0.24, '#c8d8e8', '#f6f2ea'); paper(c, function (p) { p.beginPath(); p.moveTo(bx - hh * 0.11, b); p.quadraticCurveTo(bx, b - hh * 0.25 * u - hh * 0.02, bx + hh * 0.11, b); p.closePath(); }, '#fbf6f0', 0.2);
      for (var i = 0; i < 6; i++) { var f = (t / 500 + i / 6) % 1; fe(c, bx + Math.sin(i * 3 + t / 300) * hh * 0.05, st.top - hh * 0.33 + f * hh * 0.18, 1.2, 1.2, 'rgba(255,255,255,.9)'); }
      var a = t / 250, cr = [mx + st.dir * hh * 0.2 + Math.cos(a) * hh * 0.06, st.top - hh * 0.5 + Math.sin(a) * hh * 0.06]; ln(c, [[mx + st.dir * hh * 0.14, st.top - hh * 0.5], cr], '#5a5e64', 1.5);
      cookAt(c, S, { cx: mx - st.dir * hh * 0.4, dir: st.dir }, d, T, [mx - st.dir * hh * 0.15, st.top - hh * 0.25], [mx - st.dir * hh * 0.2, st.top - hh * 0.35], 0.1); }
  },
  /* the cake on its turntable, piped with rosettes as it turns: x = R·sin(θ + ωt) */
  cake: { w: 1.6,
    back: function (q, S, L, st) { ST2.bingsu.back(q, S, L, st); },
    front: function (q, S, L, st) { var hh = S.hh; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'white', hh); fr(q, st.tx - hh * 0.03, st.top - hh * 0.1, hh * 0.06, hh * 0.1, '#c8ccd2'); fe(q, st.tx, st.top - hh * 0.1, hh * 0.24, hh * 0.04, '#d8dce2');
      cakeDome(q, st.dir > 0 ? st.x1 - hh * 0.28 : st.x0 + hh * 0.28, st.top - hh * 0.02, hh, (S.seed >>> 3) % 4); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, x = st.tx, y = st.top - hh * 0.12, R = hh * 0.2, u = (t / 9000) % 1, col = L.icing || '#f8d0dc';
      fr(c, x - R, y - hh * 0.22, R * 2, hh * 0.22, col); fe(c, x, y - hh * 0.22, R, hh * 0.04, mixc(col, '#ffffff', 0.4)); fr(c, x - R, y - hh * 0.12, R * 2, hh * 0.025, '#fbf6f0');
      var n = Math.floor(u * 10); for (var i = 0; i < 10; i++) { var th = i / 10 * TAU + t / 1800, cs = Math.cos(th); if (cs < 0 || i > n) continue; fe(c, x + Math.sin(th) * R * 0.9, y - hh * 0.24, hh * 0.025, hh * 0.022, i % 2 ? '#fbf6f0' : '#d8242a'); }
      for (i = 0; i < 6; i++) { th = i / 6 * TAU + t / 1800; if (Math.cos(th) > 0) fe(c, x + Math.sin(th) * R, y - hh * 0.06, hh * 0.015, hh * 0.015, '#fbf6f0'); }
      var tip = [x + st.dir * R * 0.2, y - hh * 0.27]; cookAt(c, S, st, d, T, [tip[0] - st.dir * hh * 0.08, tip[1] - hh * 0.1], [st.cx + st.dir * hh * 0.18, y - hh * 0.18], 0.15);
      fp(c, [[tip[0], tip[1]], [tip[0] - st.dir * hh * 0.14, tip[1] - hh * 0.1], [tip[0] - st.dir * hh * 0.06, tip[1] - hh * 0.16]], '#f6f2ea'); }
  },
  /* roti on the griddle, the sheet thrown and caught, h = v₀t − ½gt² as it spins */
  roti: { w: 1.55,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'cart', hh); fr(q, st.tx - hh * 0.25, st.top - hh * 0.05, hh * 0.5, hh * 0.05, '#1a1a1e');
      var bx = st.dir > 0 ? st.x1 - hh * 0.25 : st.x0 + hh * 0.25; bowl(q, bx, st.top, hh * 0.24, '#f6f2ea', '#f2e6a8'); fp(q, [[bx + hh * 0.15, st.top], [bx + hh * 0.15, st.top - hh * 0.12], [bx + hh * 0.22, st.top - hh * 0.12], [bx + hh * 0.22, st.top]], '#e8eef2'); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, u = (t / 2200) % 1, rx = st.tx, ry = st.top - hh * 0.06;
      c.save(); c.globalCompositeOperation = 'lighter'; glow(c, rx, ry, hh * 0.25, '255,140,40', 0.2); c.restore();
      if (u < 0.35) { var v = u / 0.35, h = 4 * v * (1 - v) * hh * 0.35; c.save(); c.translate(rx, ry - hh * 0.25 - h); c.scale(1, Math.abs(Math.cos(v * Math.PI * 2)) * 0.35 + 0.08); fe(c, 0, 0, hh * 0.18, hh * 0.18, '#f2dcae'); c.restore(); cookAt(c, S, st, d, T, [rx - st.dir * hh * 0.12, ry - hh * 0.3], [rx + st.dir * hh * 0.1, ry - hh * 0.3], 0.1); }
      else { fe(c, rx, ry - hh * 0.01, hh * 0.2, hh * 0.03, u > 0.7 ? '#e8b862' : '#f2dcae'); if (u > 0.7) { fe(c, rx - hh * 0.05, ry - hh * 0.03, hh * 0.03, hh * 0.012, '#f2e6a8'); ln(c, [[rx - hh * 0.12, ry - hh * 0.04], [rx + hh * 0.1, ry - hh * 0.035]], '#fbf6e8', 1.2); } steam(c, rx, ry - hh * 0.04, hh * 0.3, t, 2, 2, 0.4); cookAt(c, S, st, d, T, [rx - st.dir * hh * 0.1 + Math.sin(t / 200) * hh * 0.03, ry - hh * 0.05], [rx + st.dir * hh * 0.1, ry - hh * 0.06], 0.18); } }
  },
  /* fruit on ice in a glass cart, the knife going through a pineapple */
  fruit: { w: 1.6,
    back: function (q, S, L, st) {},
    front: function (q, S, L, st) { var hh = S.hh; counter(q, st.x0, st.x1, st.top, S.deck, L.ckind || 'cart', hh);
      glassCase(q, st.x0 + hh * 0.05, st.x1 - hh * 0.05, st.top, hh * 0.48, function (a, b, y, h) { fr(q, a + 2, y - h * 0.2, b - a - 4, h * 0.2, '#eef4f8'); var n = Math.round((b - a) / (hh * 0.12));
        for (var i = 0; i < n; i++) { var x = a + (b - a) * (i + 0.5) / n, k = i % 4; ln(q, [[x, y - h * 0.15], [x, y - h * 0.9]], '#e8d8b0', 1);
          if (k === 0) { fp(q, [[x - hh * 0.05, y - h * 0.5], [x + hh * 0.05, y - h * 0.5], [x, y - h * 0.85]], '#e8343a'); fr(q, x - hh * 0.05, y - h * 0.5, hh * 0.1, h * 0.06, '#3f8a3a'); }
          else if (k === 1) fr(q, x - hh * 0.025, y - h * 0.85, hh * 0.05, h * 0.42, '#f7d040'); else if (k === 2) fr(q, x - hh * 0.03, y - h * 0.8, hh * 0.06, h * 0.36, '#f29a3a'); else fr(q, x - hh * 0.03, y - h * 0.8, hh * 0.06, h * 0.36, '#c8e07a'); } }); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, k = Math.abs(Math.sin(t / 260)), bx = st.cx + st.dir * hh * 0.35, by = st.top - hh * 0.48;
      fr(c, bx - hh * 0.12, by - hh * 0.02, hh * 0.24, hh * 0.03, '#a8784a'); paper(c, E(bx, by - hh * 0.1, hh * 0.08, hh * 0.1), '#e8b84a', 0.2); fp(c, [[bx - hh * 0.04, by - hh * 0.2], [bx, by - hh * 0.32], [bx + hh * 0.04, by - hh * 0.2]], '#3f8a3a');
      var kn = [bx - st.dir * hh * 0.02, by - hh * 0.12 - k * hh * 0.1]; cookAt(c, S, st, d, T, kn, [bx + st.dir * hh * 0.06, by - hh * 0.1], 0.12); ln(c, [kn, [kn[0] + st.dir * hh * 0.12, kn[1] + hh * 0.02]], '#e8eef2', 2); }
  },
  /* a fast-food counter: menu boxes lit overhead, the fryer basket rising out of the oil */
  kiosk: { w: 1.9,
    back: function (q, S, L, st) { var hh = S.hh, y = S.deck - hh * 1.22; for (var i = 0; i < 3; i++) { var x = st.x0 + (st.x1 - st.x0) * (i + 0.5) / 3, w = (st.x1 - st.x0) / 3.3; paper(q, rect(x - w / 2, y, w, hh * 0.26), '#2a2a2e', 0.6); fr(q, x - w / 2 + 2, y + 2, w - 4, hh * 0.26 - 4, '#fbf6ea');
      if (i === 0) { fe(q, x, y + hh * 0.13, hh * 0.08, hh * 0.06, '#c8782a'); ln(q, [[x + hh * 0.06, y + hh * 0.17], [x + hh * 0.11, y + hh * 0.2]], '#f2ead8', 3); } else if (i === 1) DISH.burger(q, x, y + hh * 0.24, hh * 0.4); else for (var k = 0; k < 5; k++) fr(q, x - hh * 0.06 + k * hh * 0.03, y + hh * 0.06, hh * 0.02, hh * 0.13, '#f2c24a'); } },
    front: function (q, S, L, st) { var hh = S.hh, fx = st.tx; counter(q, st.x0, st.x1, st.top, S.deck, 'white', hh); fr(q, st.x0, st.top + hh * 0.12, st.x1 - st.x0, hh * 0.08, L.brandCol || '#c8202a');
      paper(q, rect(fx - hh * 0.18, st.top - hh * 0.22, hh * 0.36, hh * 0.22), '#9aa0a8', 0.6); fe(q, fx, st.top - hh * 0.22, hh * 0.17, hh * 0.03, '#c8902a');
      DISH.bucket(q, st.dir > 0 ? st.x1 - hh * 0.3 : st.x0 + hh * 0.3, st.top, hh * 0.38); },
    live: function (c, S, L, st, d, T) { var hh = S.hh, t = S.t, fx = st.tx, u = (t / 3000) % 1, up = u < 0.6 ? 0 : u < 0.75 ? ease((u - 0.6) / 0.15) : u < 0.9 ? 1 : 1 - ease((u - 0.9) / 0.1);
      for (var i = 0; i < 5; i++) { var b = (t / 400 + i * 0.3) % 1; fe(c, fx - hh * 0.12 + i * hh * 0.06, st.top - hh * 0.23, b * 2, b * 1.3, 'rgba(255,240,200,.8)'); }
      var by = st.top - hh * 0.2 - up * hh * 0.2; fp(c, [[fx - hh * 0.1, by], [fx + hh * 0.1, by], [fx + hh * 0.08, by + hh * 0.1], [fx - hh * 0.08, by + hh * 0.1]], 'rgba(150,150,155,.9)'); if (up > 0.2) for (i = 0; i < 4; i++) fe(c, fx - hh * 0.06 + i * hh * 0.04, by + hh * 0.02, hh * 0.025, hh * 0.02, '#e0a040');
      ln(c, [[fx - st.dir * hh * 0.1, by], [fx - st.dir * hh * 0.25, by - hh * 0.08]], '#2a2a2e', 2); cookAt(c, S, st, d, T, [fx - st.dir * hh * 0.25, by - hh * 0.08], [st.cx + st.dir * hh * 0.1, st.top - hh * 0.25], 0.05); }
  }
};
for (var k2 in ST2) ST[k2] = ST2[k2];

DISH.kjeen = function (c, x, y, s) { var t = plate(c, x, y, s); for (var i = 0; i < 3; i++) { c.strokeStyle = '#fbf8ee'; c.lineWidth = s * 0.025; c.beginPath(); for (var a = 0; a < 2.5 * TAU; a += 0.4) { var r = s * 0.01 * a; c.lineTo(x - s * 0.18 + i * s * 0.14 + Math.cos(a) * r, t - s * 0.05 + Math.sin(a) * r * 0.4); } c.stroke(); } fe(c, x + s * 0.02, t - s * 0.07, s * 0.2, s * 0.05, '#c8452a'); herbs(c, x + s * 0.3, t, s, 3); return [x, t - s * 0.1]; };
DISH.boatbowl = function (c, x, y, s) { var t = bowl(c, x, y, s * 0.6, '#f6f2ea', '#5a2a1a', '#2f6db0'); herbs(c, x, t, s * 0.6, 3); for (var k = 0; k < 3; k++) bowl(c, x + s * 0.45, y - k * s * 0.13, s * 0.5, '#f6f2ea', '#e8e2d6', '#2f6db0'); return [x, t]; };

/* ---------------------------------------------------------------- the trades
   st: the kitchen; dishes for the tables and the board; hold: what diners lift */
function TR(st, dishes, hold, o) { var t = { st: st, dishes: dishes, hold: hold, seat: 'stool', table: 'steel' }; for (var k in o || {}) t[k] = o[k]; return t; }
var LANNA = { sin: 0.35, mohom: 0.35, casual: 0.3 };
var TRADES = {
  tamsang: TR('wok', ['krapao', 'friedrice', 'tomyum', 'omelet', 'thaitea'], ['spoon', 'spoon', 'fork'], { hat: 'cap', shingle: 'wok' }),
  curry: TR('curry', ['curryrice', 'redcurry', 'soup', 'water'], ['spoon', 'spoon', 'fork'], {}),
  lanna: TR(['grill', 'noodle'], ['khaosoi', 'saioua', 'namprik', 'kratip'], ['ball', 'spoon', 'ball'], { grill: 'sausage', soup: '#dc8a2c', dish0: 'khaosoi', mix: LANNA, khom: 1, types: { teak: 3, hut: 1.5, garden: 1.5 }, hat: 'kerchief' }),
  isaan: TR('mortar', ['somtam', 'gaiyang', 'larb', 'kratip'], ['ball', 'ball', 'spoon'], { types: { hut: 2, garden: 1.5, tent: 1.5 }, mix: { mohom: 0.3, casual: 0.5, sin: 0.2 }, hat: 'kerchief' }),
  noodle: TR('noodle', ['noodle', 'noodle', 'water'], ['chop', 'spoon', 'chop'], { shingle: 'noodle', caddy: 1 }),
  rice: TR('hang', ['chickenrice', 'redpork', 'soup'], ['spoon', 'spoon', 'fork'], { hang: ['chicken', 'chicken', 'pork'], soupPot: 1 }),
  grill: TR('buffet', ['mookata'], ['tongs', 'chop'], { cookTable: 'dome', types: { garden: 2.5, tent: 2, shop: 1 } }),
  shabu: TR('buffet', ['shabu'], ['chop', 'tongs'], { cookTable: 'pot', types: { modern: 2, mall: 1.5 }, seat: 'chair', table: 'wood' }),
  japanese: TR('sushi', ['sushi', 'ramen', 'matcha'], ['chop', 'chop', 'cup'], { hat: 'band', noren: 1, chochin: 1, types: { modern: 2, shop: 1.5 }, table: 'wood', seat: 'chair' }),
  chinese: TR('hang', ['dimsum', 'duckrice', 'tea'], ['chop', 'chop', 'cup'], { hang: ['duck', 'duck', 'pork'], redLantern: 1, table: 'red' }),
  vietnamese: TR('noodle', ['pho', 'banhmi', 'pho'], ['chop', 'spoon', 'chop'], { soup: '#d8b88a', dish0: 'pho', redLantern: 1, hatDiner: 'cone' }),
  pizza: TR('oven', ['pizza', 'pasta', 'wine'], ['fork', 'fork', 'cup'], { table: 'check', seat: 'chair', hat: 'toque', types: { modern: 2, garden: 1.5 }, mix: { casual: 1 } }),
  western: TR('grill', ['steak', 'burger', 'beer'], ['fork', 'fork', 'beer'], { grill: 'steak', table: 'wood', seat: 'chair', hat: 'toque', mix: { casual: 1 }, types: { modern: 1.5, garden: 1.5 } }),
  indian: TR('tandoor', ['curryb', 'naan', 'chai'], ['spoon', 'cup', 'spoon'], { table: 'cloth', seat: 'chair', marigold: 1, mix: { casual: 1 } }),
  seafood: TR('ice', ['prawns', 'crab', 'tomyum', 'beer'], ['fork', 'spoon', 'beer'], { net: 1, types: { river: 2, garden: 1.5, tent: 1.5 } }),
  vege: TR('curry', ['curryrice', 'tofu', 'soup'], ['spoon', 'spoon', 'fork'], { trays: ['#5d9b3a', '#e8b45a', '#3f8a3a', '#d8c060', '#a8642a', '#f2e6c9'], jflag: 1 }),
  fastfood: TR('kiosk', ['bucket', 'burger', 'cola'], ['leg', 'cup', 'leg'], { seat: 'chair', table: 'white', hat: 'cap', types: { mall: 3, modern: 3 }, mix: { casual: 1 }, apron: '#c8202a' }),
  cafe: TR(['espresso', 'pourover'], ['latte', 'icedlatte', 'cake', 'croissant'], ['mug', 'cup', 'mug'], { table: 'marble', seat: 'chair', shingle: 'cafe', mix: { casual: 0.85, mohom: 0.15 }, apron: '#4a3a2a', hat: 'beanie' }),
  bar: TR('bar', ['beer', 'cocktail', 'beer'], ['beer', 'beer', 'cup'], { table: 'high', seat: 'high', shingle: 'bar', mix: { casual: 1 }, apron: '#1a1a1e' }),
  bread: TR('bake', ['croissant', 'latte', 'cake'], ['cup', 'fork', 'cup'], { table: 'marble', seat: 'chair', hat: 'toque', shingle: 'bakery' }),
  cakes: TR('cake', ['cake', 'latte', 'cake'], ['fork', 'cup', 'fork'], { table: 'marble', seat: 'chair', shingle: 'cake', apron: '#f8d0dc' }),
  icecream: TR('bingsu', ['bingsu', 'bingsu', 'water'], ['spoon', 'spoon'], { table: 'marble', seat: 'chair', shingle: 'cake', apron: '#a8d8f0' }),
  khanom: TR('khanomkrok', ['khanom', 'thaitea', 'khanom'], ['fork', 'cup'], { shingle: 'cake', mix: LANNA, apron: '#e8b84a' }),
  sgrill: TR('grill', ['kratip', 'gaiyang'], ['ball', 'ball'], { grill: 'skewer', table: 'plastic' }),
  schicken: TR('grill', ['gaiyang', 'kratip', 'somtam'], ['ball', 'leg'], { grill: 'chicken', table: 'plastic' }),
  smala: TR('grill', ['beer', 'kratip'], ['beer', 'ball'], { grill: 'mala', table: 'plastic' }),
  sburger: TR('grill', ['burger', 'cola'], ['cup', 'cup'], { grill: 'steak', table: 'plastic', hat: 'cap', mix: { casual: 1 } }),
  swok: TR('wok', ['krapao', 'friedrice', 'thaitea'], ['spoon', 'fork'], { wokFill: '#e8a05a', table: 'plastic', hat: 'cap' }),
  sroti: TR('roti', ['khanom', 'thaitea'], ['fork', 'cup'], { table: 'plastic', hat: 'kopiah' }),
  sfruit: TR('fruit', ['thaitea', 'water'], ['cup', 'cup'], { table: 'plastic' }),
  skrok: TR('khanomkrok', ['khanom', 'thaitea'], ['fork', 'cup'], { table: 'plastic' }),
  snoodle: TR('noodle', ['noodle', 'water'], ['chop', 'spoon'], { table: 'plastic', caddy: 1 }),
  nclear: TR('noodle', ['noodle', 'noodle', 'water'], ['chop', 'spoon', 'chop'], { caddy: 1, soup: '#e8d8a8' }),
  nboat: TR('noodle', ['boatbowl', 'boatbowl', 'water'], ['chop', 'spoon', 'chop'], { caddy: 1, soup: '#5a2a1a', dish0: 'boatbowl', ckind: 'boat', stacks: 1 }),
  nkhaosoi: TR('noodle', ['khaosoi', 'khaosoi', 'water'], ['spoon', 'chop', 'spoon'], { soup: '#dc8a2c', dish0: 'khaosoi', khom: 1, mix: LANNA, types: { teak: 2, hut: 1.5 }, hat: 'kerchief' }),
  nramen: TR('noodle', ['ramen', 'ramen', 'matcha'], ['chop', 'chop', 'cup'], { soup: '#d8b07a', dish0: 'ramen', bowl: '#2a2018', noren: 1, chochin: 1, hat: 'band', table: 'wood', seat: 'chair', types: { modern: 2 } }),
  nkjeen: TR('curry', ['kjeen', 'kjeen', 'water'], ['spoon', 'spoon', 'fork'], { pots: 1, mix: LANNA, trays: ['#c8452a', '#e8c070', '#5d9b3a', '#fbf8ee'] }),
  npho: TR('noodle', ['pho', 'banhmi', 'pho'], ['chop', 'spoon', 'chop'], { soup: '#d8b88a', dish0: 'pho', redLantern: 1, hatDiner: 'cone' }),
  nyentafo: TR('noodle', ['noodle', 'noodle', 'water'], ['chop', 'spoon', 'chop'], { soup: '#e8708a', caddy: 1 })
};
function T0(L) { return TRADES[L.trade]; }
/* first match wins: the name, brand and subs pick the kitchen */
var DETECT = {
  restaurant: [
    ['fastfood', /kfc|mcdonald|burger king|pizza hut|pizza company|subway|dairy queen|five star|5 star chicken|chester|dunkin|texas chicken|bonchon|ไก่ทอด/i],
    ['shabu', /ชาบู|สุกี้|shabu|suki|hot ?pot|หม้อไฟ|\bmk\b|จิ้มจุ่ม|火锅/i],
    ['grill', /หมูกระทะ|moo ?ka?ta|ปิ้งย่าง|yakiniku|korean bbq|เนื้อย่าง|หม่าล่า|mala|เกาหลี|korea/i],
    ['japanese', /sushi|ซูชิ|japan|ญี่ปุ่น|izakaya|ราเม[งน]|ramen|udon|อุด้ง|ทงคัตสึ|tonkatsu|omakase|ข้าวหน้า|japanese/i],
    ['vietnamese', /vietnam|เวียดนาม|\bpho\b|เฝอ|แหนมเนือง|banh ?mi|บั๋นหมี่|ญวน/i],
    ['indian', /india|อินเดีย|bombay|tandoor|masala|biryani|punjab|nepal|เนปาล|curry house/i],
    ['pizza', /pizza|pizzeria|italian|italia|pasta|trattoria|osteria|พิซซ่า|สปาเก/i],
    ['rice', /ข้าวมันไก่|ข้าวขาหมู|ข้าวหมูแดง|หมูกรอบ|khao man gai|chicken rice|โจ๊ก|ข้าวต้ม|ไก่ตอน/i],
    ['chinese', /chinese|(?<!ขนม|หนม)จีน|ติ่มซำ|dim ?sum|เป็ดย่าง|ห่านพะโล้|duck|[一-鿿]/i],
    ['lanna', /ข้าวซอย|khao ?so[iy]|ล้านนา|lanna|ขันโตก|khan ?toke|ไส้อั่ว|น้ำพริกอ่อง|แกงฮังเล|อาหารเหนือ|อาหารพื้นเมือง|northern|น้ำเงี้ยว|แคบหมู|เฮือน|กาดหมั้ว/i],
    ['isaan', /ส้มตำ|ตำ(ปู|ถาด|ซั่ว|ไทย|ลาว|แซ่บ|มั่ว|ป่า)|ตำแซ่บ|som ?tam|isa+n|อีสาน|ไก่ย่าง|ลาบ|larb|laab|น้ำตก|แจ่วฮ้อน|เสือร้องไห้|คอหมูย่าง|แซ่บ/i],
    ['seafood', /ซีฟู้ด|seafood|อาหารทะเล|ทะเล|กุ้งเผา|ปูนึ่ง|หอย|ปลาเผา|ปลาจุ่ม|crab|prawn|shrimp/i],
    ['noodle', /ก๋วยเตี๋ยว|เตี๋ยว|บะหมี่|noodle|ก๋วยจั๊บ|เย็นตาโฟ|ขนมจีน|หนมจีน|เส้น/i],
    ['vege', /อาหารเจ|มังสวิรัติ|vegan|vegetarian|\bveg\b|ร้านเจ|ครัวเจ|^เจ\s|\sเจ$/i],
    ['curry', /ข้าวแกง|ราดแกง|แกง|curry/i],
    ['tamsang', /ตามสั่ง|made-to-order|กะเพรา|ข้าวผัด|ผัดไทย|pad ?thai|ครัว/i],
    ['western', /steak|สเต็ก|สเต๊ก|burger|เบอร์เกอร์|grill|bistro|pub|diner|brunch|breakfast|deli|bbq|smokehouse|mexican|taco|kebab|falafel|greek|french|german|wine|international/i]
  ],
  bakery: [['icecream', /ice ?cream|gelato|bingsu|บิงซู|ไอศกรีม|ไอติม|น้ำแข็งไส|frozen|yogurt|swensen|dairy queen|cold stone|sofuto|softserve/i], ['khanom', /ขนมไทย|ขนมครก|ขนม(ชั้น|เปียกปูน|ถ้วย|ตาล)|ลูกชุบ|ทองหยิบ|thai dessert/i], ['cakes', /cake|เค้ก|cheesecake|brownie|บราวนี่|dessert|ของหวาน|crepe|เครป|macaron|waffle/i], ['bread', /bake|bread|เบเกอรี่|ขนมปัง|croissant|ครัวซองต์|donut|โดนัท|pastry|boulang|patisserie|bun/i]],
  streetfood: [['fastfood', /kfc|mcdonald|burger king|pizza|subway|dairy queen|five star|5 star|chester|dunkin/i], ['rice', /ข้าวมันไก่|ข้าวขาหมู|ข้าวหมูแดง|หมูกรอบ|โจ๊ก/i], ['sburger', /burger|เบอร์เกอร์|hot ?dog|sandwich|แซนด์วิช/i], ['sroti', /roti|โรตี/i], ['smala', /หม่าล่า|mala/i], ['schicken', /ไก่ย่าง|ไก่|chicken/i], ['sgrill', /ปิ้ง|ย่าง|kebab|กะบับ|บาร์บีคิว|bbq|grill|ไส้กรอก/i], ['sfruit', /ผลไม้|fruit|น้ำปั่น|juice|smoothie|มะม่วง/i], ['skrok', /ขนมครก|ขนม/i], ['swok', /ผัด|หอยทอด|ทอด|ข้าว/i], ['snoodle', /ก๋วยเตี๋ยว|เตี๋ยว|noodle|บะหมี่/i]],
  noodle: [['nkhaosoi', /ข้าวซอย|khao ?so[iy]/i], ['nboat', /เรือ|boat/i], ['nramen', /ราเม[งน]|ramen|udon|อุด้ง|japan|ญี่ปุ่น|oishi/i], ['nkjeen', /ขนมจีน|khanom ?jeen|น้ำเงี้ยว/i], ['npho', /เฝอ|\bpho\b|vietnam|เวียดนาม/i], ['nyentafo', /เย็นตาโฟ|yen ?ta ?fo/i]]
};
var FALL = {
  restaurant: function (L, r) { var P = L.P, c = P.cuisine || [], w = { tamsang: 3, curry: 2, noodle: 1.5, isaan: 1.5, lanna: P.province === 'cr' ? 2 : 1.5, rice: 0.8, grill: 0.7, seafood: 0.4 };
    if (P.hills || P.moo) { w.lanna *= 2; w.isaan *= 1.5; }
    if (c.indexOf('international') >= 0) w = { western: 2.5, pizza: 1.2, indian: 0.5, japanese: 0.3, tamsang: 0.4 };
    if (c.indexOf('japanese') >= 0) return 'japanese'; if (c.indexOf('vegetarian') >= 0) return 'vege'; if (c.indexOf('seafood') >= 0) return 'seafood'; if (c.indexOf('northern') >= 0) return 'lanna';
    var F = window.MDDOODLER_FOOD; if (F && F.cuisineOf) { var k = F.cuisineOf(L.text), map = { american: 'western', dutch: 'western', swiss: 'western', swedish: 'western', 'soul-food': 'western', falafel: 'western', burmese: 'curry', 'central-thai': 'tamsang', 'southern-thai': 'curry', isaan: 'isaan', japanese: 'japanese', chinese: 'chinese', vietnamese: 'vietnamese' }; if (map[k]) return map[k]; }
    return wpick(r, w); },
  cafe: function () { return 'cafe'; }, bar: function () { return 'bar'; },
  bakery: function (L, r) { return wpick(r, { bread: 3, cakes: 2, icecream: 1.3, khanom: 1.3 }); },
  streetfood: function (L, r) { return wpick(r, { sgrill: 3, swok: 2, sroti: 1.2, sfruit: 1.2, skrok: 1, snoodle: 1, schicken: 1 }); },
  noodle: function (L, r) { return wpick(r, { nclear: 3, nboat: 1.5, nkhaosoi: L.P.province === 'cr' ? 1 : 1.6, nyentafo: 0.8, nkjeen: 0.6 }); }
};
function tradeOf(kind, L, r) { var D0 = DETECT[kind] || []; for (var i = 0; i < D0.length; i++) if (D0[i][1].test(L.text)) return D0[i][0]; return FALL[kind](L, r); }
var KINDS = {
  restaurant: { shop: 3.2, teak: 1.6, garden: 2, hut: 0.9, modern: 0.8, tent: 0.7 },
  cafe: { modern: 2.5, garden: 2, shop: 2, teak: 1.1, glass: 1.2, cart: 0.6 },
  bar: { shop: 3, garden: 1.5, roof: 1.4, reggae: 1, modern: 1.2, hut: 0.5 },
  bakery: { shop: 3, modern: 2, teak: 0.8, cart: 0.6 },
  streetfood: { cart: 5, tent: 2, hut: 0.6 },
  noodle: { shop: 3, tent: 1.4, hut: 1.2, teak: 1, cart: 0.8 }
};
function typeOf(kind, L, r, T) {
  var P = L.P, w = {}, k;
  if (P.inside) return 'mall';
  if (L.trade === 'fastfood' && kind === 'streetfood') return 'cart';
  if (P.river && P.river.m != null && P.river.m < 150 && kind !== 'streetfood' && r() < 0.85) return 'river';
  for (k in KINDS[kind]) w[k] = KINDS[kind][k];
  if (P.hills) { w.garden = (w.garden || 0.5) * 3; w.hut = (w.hut || 0.3) * 2; w.teak = (w.teak || 0.3) * 1.5; if (kind === 'cafe') w.glass *= 2; }
  if (P.moo && !P.hills) { w.hut = (w.hut || 0.3) * 1.8; w.garden = (w.garden || 0.5) * 1.4; }
  if (T.types) for (k in T.types) w[k] = (w[k] || 0.5) * T.types[k];
  if (/rooftop|sky ?bar|roof/i.test(L.text) && kind === 'bar') return 'roof';
  if (/reggae|เร็กเก้|rasta/i.test(L.text)) return 'reggae';
  if (/garden|สวน|farm|ไร่|ฟาร์ม/i.test(L.text)) w.garden = (w.garden || 0.5) * 3;
  if (/greenhouse|glass ?house|เรือนกระจก/i.test(L.text)) return 'glass';
  if (/amazon|อเมซอน|inthanin|อินทนิล|starbucks|chagee|punthai|พันธุ์ไทย/i.test(L.text)) return r() < 0.7 ? 'modern' : 'shop';
  delete w.mall; delete w.river;
  return wpick(r, w);
}
var SIGNCOL = ['#6a3a1e', '#2f4f6a', '#7a1f1a', '#2a4a3a', '#4a2a5a', '#5a3018'];
function brandCol(s) { if (/amazon|อเมซอน|starbucks|subway|5 star|five star/i.test(s)) return '#2f7a4a'; if (/kfc|mcdonald|pizza|burger king|dairy queen|chester|texas/i.test(s)) return '#b8202a'; if (/dunkin|swensen|s&p/i.test(s)) return '#d8507a'; return null; }

/* ---------------------------------------------------------------- the deal
   the place's facts first (hours, cuisine, river, hills, village, mall, brand, road), then the seed */
function plan(S, kind) {
  var P = S.place || {}, hh = S.hh, r = K.rnd(((S.seed ^ 0x51ed1) >>> 0) || 7), L = { P: P, kind: kind, units: [], props: [], pets: [] };
  L.text = [P.name, P.nameTh, P.nameEn, P.brand, (P.sub || []).join(' ')].filter(Boolean).join(' ');
  var o = K.openNow(P.hours, S.now);
  L.state = o === true ? 'open' : o === false ? 'closed' : kind === 'bar' ? (S.night ? 'open' : 'closed') : S.night ? 'quiet' : 'open';
  L.trade = tradeOf(kind, L, r); var T = TRADES[L.trade];
  L.type = typeOf(kind, L, r, T);
  var Wd = { shop: [4.6, 6], teak: [4.6, 5.8], garden: [5.6, 6.6], river: [5.6, 6.6], hut: [4.2, 5.2], reggae: [4.2, 5.2], modern: [4.6, 5.6], glass: [4.6, 5.4], tent: [4.4, 5.4], mall: [3.8, 4.8], roof: [5, 6.2], cart: [1.7, 2.0] }[L.type];
  var stk = T.st instanceof Array ? pick(r, T.st) : T.st, sw = ST[stk].w * hh;
  if (L.type === 'cart') Wd = [ST[stk].w + 0.1, ST[stk].w + 0.3];
  var bw = Math.min(hh * lerp(Wd[0], Wd[1], r()), S.span * (L.type === 'cart' ? 0.42 : L.type === 'garden' || L.type === 'river' ? 0.74 : 0.68));
  var lo = S.x0 + hh * 0.65, hi = S.x1 - S.span * 0.19 - bw; if (L.type === 'cart') { lo = S.x0 + hh * 1.0; hi = S.x1 - hh * 1.8 - bw; } if (hi < lo) hi = lo;
  L.bx0 = lerp(lo, hi, 0.2 + r() * 0.6); L.bx1 = L.bx0 + bw;
  BLD[L.type].geo(L, S, r);
  L.signCx = L.signCx || (L.bx0 + L.bx1) / 2; L.stairs = r() < 0.5 ? 1 : -1;
  L.brandCol = brandCol(L.text); L.signCol = L.brandCol || (L.type === 'teak' || L.type === 'hut' ? '#5a3018' : L.type === 'modern' ? '#2a2a2e' : pick(r, SIGNCOL));
  L.ckind = T.ckind || (L.type === 'cart' ? 'cart' : L.type === 'teak' ? 'teak' : L.type === 'hut' || L.type === 'reggae' ? 'bamboo' : L.type === 'modern' || L.type === 'roof' ? pick(r, ['concrete', 'wood']) : L.trade === 'chinese' ? 'red' : pick(r, ['steel', 'steel', 'tile', 'wood']));
  L.machine = L.brandCol || pick(r, ['#c8ccd2', '#c0392b', '#2a2a2e', '#e8e0cc', '#2f6a5a']); L.art = pick(r, ['heart', 'rosetta', 'tulip']); L.kettle = pick(r, ['#2a2a2e', '#c8ccd2', '#d8a050']); L.dripper = pick(r, ['#f6f2ea', '#c0392b', '#3a3e44']);
  L.barMode = /cocktail|speakeasy|gin|whisk|mixolog/i.test(L.text) ? 'shake' : /beer|craft|brew|pub|tap|เบียร์/i.test(L.text) ? 'pour' : pick(r, ['shake', 'pour']);
  L.icing = pick(r, ['#f8d0dc', '#fbf2c8', '#c8e8d0', '#5a2e1a', '#f6f2ea']); L.pastry = pick(r, [['croissant', 'bun', 'tart', 'baguette'], ['donut', 'croissant', 'slice', 'bun'], ['slice', 'tart', 'khanom', 'croissant'], ['bun', 'baguette', 'croissant', 'donut']]);
  L.stk = stk; L.T = T;
  /* the kitchen: at one end of the open front, the cook at its outer end facing in */
  var a = L.ox0, b = L.ox1;
  if (L.type === 'garden' || L.type === 'river') { a = L.ox0; b = L.ox1; }
  L.ss = L.type === 'cart' ? -1 : r() < 0.5 ? -1 : 1;
  var st = L.st = {};
  if (L.type === 'cart') { st.x0 = L.bx0; st.x1 = L.bx1; } else { st.x0 = L.ss < 0 ? a + hh * 0.04 : b - hh * 0.04 - sw; st.x1 = st.x0 + sw; }
  st.dir = L.ss < 0 ? 1 : -1; st.cx = L.ss < 0 ? st.x0 + hh * 0.3 : st.x1 - hh * 0.3; st.tx = st.cx + st.dir * hh * 0.5; st.top = S.deck - hh * 0.5;
  if (stk === 'buffet') { st.cx = (st.x0 + st.x1) / 2; }
  /* tables: inside the front first, then the lawn, then the pavement */
  var seat = T.seat, table = T.table;
  if ((L.type === 'teak' || L.type === 'hut' || L.type === 'reggae') && (kind === 'restaurant' || kind === 'noodle')) { if (T.mix === LANNA || L.trade === 'isaan' || r() < 0.4) { seat = 'floor'; table = 'khantok'; } else if (table === 'steel') table = 'wood'; }
  if ((L.type === 'garden' || L.type === 'river') && table === 'steel') table = pick(r, ['wood', 'cloth', 'wood']);
  if (L.type === 'modern' && table === 'steel') { table = 'wood'; seat = 'chair'; }
  L.seat = seat; L.table = table;
  var uw = hh * (seat === 'floor' ? 1.4 : seat === 'high' ? 1.3 : 1.5), free = [];
  if (L.type === 'cart') free = [[L.bx1 + hh * 0.15, S.x1 - hh * 0.8], [S.x0 + hh * 0.7, L.bx0 - hh * 0.15]];
  else if (L.type === 'garden' || L.type === 'river') free = [L.ss < 0 ? [st.x1 + hh * 0.05, L.ox1] : [L.ox0, st.x0 - hh * 0.05], L.sl ? [L.sb + hh * 0.1, L.bx1 + hh * 0.3] : [L.bx0 - hh * 0.3, L.sa - hh * 0.1]];
  else free = [L.ss < 0 ? [st.x1 + hh * 0.05, b] : [a, st.x0 - hh * 0.05]];
  L.music = kind === 'bar' && /live|music|jazz|blues|acoustic|ดนตรี|band|rock|folk|guitar/i.test(L.text);
  L.pool = kind === 'bar' && !L.music && /pool|snooker|สนุ้ก|billiard/i.test(L.text);
  free.forEach(function (f, fi) {
    var room = f[1] - f[0]; if (room < hh * 0.9) return;
    var n = Math.max(0, Math.floor(room / uw)), single = n === 0 || kind === 'cafe' && r() < 0.35;
    if (L.type === 'cart' && n > 1) n = 1;
    if (n === 0) { L.units.push({ x: (f[0] + f[1]) / 2, solo: 1, dir: fi % 2 ? -1 : 1, i: L.units.length }); return; }
    var gap = (room - n * uw) / n;
    for (var i = 0; i < n; i++) { var ux = f[0] + gap / 2 + uw * (i + 0.5) + gap * i, u = { x: ux, i: L.units.length };
      if (i === 0 && L.music && fi === 0) { u.music = 1; L.music = 0; } else if (i === 0 && L.pool && fi === 0 && room >= uw * 1.3) { u.pool = 1; L.pool = 0; }
      else if (kind === 'cafe' && r() < 0.3) { u.solo = 1; u.dir = r() < 0.5 ? 1 : -1; }
      L.units.push(u); }
  });
  if (L.units.length < 2 && L.type !== 'cart' && L.type !== 'garden' && L.type !== 'river' && L.type !== 'mall' && L.type !== 'roof') {
    var yl = L.bx0 - (S.x0 + hh * 0.65), yr = S.x1 - hh * 0.8 - L.bx1, out = yr > yl ? [L.bx1 + hh * 0.15, L.bx1 + hh * 0.15 + uw] : [L.bx0 - hh * 0.15 - uw, L.bx0 - hh * 0.15];
    if (Math.max(yl, yr) > uw + hh * 0.3) { L.units.push({ x: (out[0] + out[1]) / 2, out: 1, i: L.units.length }); if (yr > yl) L.yr0 = out[1]; else L.yl1 = out[0]; }
  }
  L.units.forEach(function (u) { u.items = [T.dishes[(u.i * 2) % T.dishes.length], T.dishes[(u.i * 2 + 1) % T.dishes.length]]; if (kind === 'cafe' && u.solo) u.items = [r() < 0.6 ? 'laptop' : 'book', pick(r, ['latte', 'icedlatte'])]; u.full = L.state === 'open' && (u.i === 0 || r() < 0.82); u.two = !u.solo && r() < 0.8; });
  /* out front, from the building's edge outward */
  var yards = [{ a: S.x0 + hh * 0.62, b: (L.yl1 || L.bx0) - hh * 0.06, s: -1 }, { a: (L.yr0 || L.bx1) + hh * 0.06, b: S.x1 - hh * 0.72, s: 1 }];
  if (L.type === 'cart') { yards = []; var ux = L.units.map(function (u) { return u.x; }); [[S.x0 + hh * 0.62, L.bx0 - hh * 0.06, -1], [L.bx1 + hh * 0.06, S.x1 - hh * 0.72, 1]].forEach(function (y) { var lo2 = y[0], hi2 = y[1]; ux.forEach(function (x) { if (x > lo2 && x < hi2) { if (y[2] > 0) lo2 = Math.max(lo2, x + uw / 2); else hi2 = Math.min(hi2, x - uw / 2); } }); yards.push({ a: lo2, b: hi2, s: y[2] }); }); }
  if (L.type === 'garden' || L.type === 'river') yards.forEach(function (y) { if (y.s < 0) y.b = Math.min(y.b, L.bx0 - hh * 0.4); else y.a = Math.max(y.a, L.bx1 + hh * 0.4); });
  if (L.type === 'mall') yards.forEach(function (y) { y.b = y.a - 1; });
  yards.forEach(function (y) { y.cur = y.s < 0 ? y.b : y.a; });
  function put(k, w, o) { var ys = yards.slice().sort(function (p, q) { return (q.s < 0 ? q.cur - q.a : q.b - q.cur) - (p.s < 0 ? p.cur - p.a : p.b - p.cur); }); if (o && o.side) ys = yards.filter(function (y) { return y.s === o.side; });
    for (var i = 0; i < ys.length; i++) { var y = ys[i], room = y.s < 0 ? y.cur - y.a : y.b - y.cur; if (room >= w * hh) { var x = y.s < 0 ? y.cur - w * hh / 2 : y.cur + w * hh / 2; y.cur += y.s * w * hh; var p = { k: k, x: x, w: w * hh }; for (var f in o || {}) p[f] = o[f]; L.props.push(p); return p; } } return null; }
  var thai = !/fastfood|pizza|western|indian/.test(L.trade) || r() < 0.3;
  if (thai && L.type !== 'mall' && L.type !== 'roof' && r() < 0.72) put('spirit', 0.62);
  if (L.trade === 'vege') put('jflag', 0.4);
  if (P.road && L.type !== 'mall' && L.type !== 'roof') L.plate = put('plate', 0.45, { side: yards[1] && yards[1].b - yards[1].cur > hh * 0.5 ? 1 : -1 });
  var plants = kind === 'cafe' ? ['monstera', 'palm', 'cactus', 'bougain', 'frangipani', 'coffee', 'bamboo'] : ['banana', 'bougain', 'frangipani', 'chilli', 'marigold', 'basil', 'palm', 'bamboo'];
  if (P.hills && kind === 'cafe') plants = ['coffee', 'coffee', 'bamboo', 'banana'];
  if (L.type !== 'roof') { put('plant', 0.55, { pk: pick(r, plants) }); if (r() < 0.6) put('plant', 0.5, { pk: pick(r, plants) }); }
  if (r() < 0.55 && L.state !== 'closed') put('moto', 1.05, { col: pick(r, ['#c0392b', '#2f6db0', '#f2f2ee', '#2a2a2e', '#e8b84a', '#e8408a', '#5a8a4a']), dir: r() < 0.5 ? 1 : -1, helmet: r() < 0.5 ? pick(r, ['#f2f2ee', '#d8242a', '#2a2a2e', '#f7d020']) : null });
  if (kind === 'cafe' && r() < 0.45) put('bike', 0.75, { col: pick(r, ['#2f6a5a', '#c0392b', '#f2e6c9', '#2a2a2e']), basket: r() < 0.6 });
  if ((L.type === 'teak' || L.type === 'hut' || T.mix === LANNA) && r() < 0.5) put('jar', 0.55);
  if (r() < 0.45 && L.type !== 'mall') put('aframe', 0.5);
  if (r() < 0.16 && L.state === 'open') put('song', 2.2, { col: P.province === 'cr' ? '#2f6db0' : '#c0392b' });
  if (r() < 0.5) put('plant', 0.5, { pk: pick(r, plants) });
  L.pole = r() < 0.4 && (L.type === 'shop' || L.type === 'tent' || L.type === 'cart') && L.bx0 - S.x0 > hh * 1.2;
  /* the dog, the cat, the village hens */
  var spots = yards.filter(function (y) { return (y.s < 0 ? y.cur - y.a : y.b - y.cur) > hh * 0.5; });
  if (r() < 0.6) L.pets.push({ k: 'dog', x: spots.length ? (spots[0].s < 0 ? spots[0].cur - hh * 0.3 : spots[0].cur + hh * 0.3) : lerp(L.bx0, L.bx1, r()), col: pick(r, ['#c8a070', '#f2ead8', '#3a2a1a', '#a8582a', '#8a7a6a']), dir: r() < 0.5 ? 1 : -1, sleep: L.state !== 'open' || r() < 0.4 });
  if (r() < (kind === 'cafe' ? 0.55 : 0.3) || /cat|แมว/i.test(L.text)) L.pets.push({ k: 'cat', x: lerp(L.ox0 + hh * 0.3, L.ox1 - hh * 0.3, r()), col: pick(r, ['#f2a04a', '#3a3a3e', '#f2ead8', '#8a8a8a', '#d8b890']), dir: r() < 0.5 ? 1 : -1 });
  if ((P.moo || P.hills) && r() < 0.5 && spots.length > 1) L.pets.push({ k: 'hens', x: spots[spots.length - 1].s < 0 ? spots[spots.length - 1].a + hh * 0.2 : spots[spots.length - 1].b - hh * 0.6 });
  L.shingleK = T.shingle || (kind === 'restaurant' ? 'plate' : kind === 'noodle' ? 'noodle' : kind === 'cafe' ? 'cafe' : kind === 'bar' ? 'bar' : kind === 'bakery' ? 'bakery' : 'plate');
  L.shingleSide = (S.x1 - L.bx1) > (L.bx0 - S.x0) ? 1 : -1;
  L.passer = L.state === 'open' && !S.night && r() < 0.35; L.server = L.state === 'open' && (stk === 'buffet' || r() < 0.3) && L.units.length > 0;
  L.fan = (L.type === 'shop' || L.type === 'tent' || L.type === 'mall' && L.P.inside && /ตลาด|กาด|market/i.test(L.P.inside)) && r() < 0.6;
  L.lights = (L.type === 'garden' || L.type === 'river' || L.type === 'roof' || L.type === 'tent' || kind === 'bar' || kind === 'cafe' && r() < 0.6 || r() < 0.25);
  L.khom = T.khom || L.type === 'teak' || L.type === 'hut' || r() < 0.3;
  L.board = L.ss < 0 ? Math.min(L.ox1 - hh * 0.65, st.x1 + hh * 0.7) : Math.max(L.ox0 + hh * 0.65, st.x0 - hh * 0.7);
  if (kind === 'bar' && L.inner && L.inner !== 'open') L.neon = { x: L.board, y: L.oy + hh * 0.36, k: /cocktail|gin|speakeasy|mixolog/i.test(L.text) ? 'glass' : /beer|craft|brew|pub|เบียร์/i.test(L.text) ? 'mug' : pick(r, ['BAR', 'mug', 'glass']) };
  return L;
}

/* ---------------------------------------------------------------- tables and who sits at them */
var STOOL = ['#d8282a', '#2f6db0', '#2f8f5b', '#e8408a', '#f2b02a'];
function seatX(u, side, L, hh) { return u.x + side * hh * (L.seat === 'floor' ? 0.5 : L.seat === 'high' ? 0.5 : 0.56); }
function tableY(L, S) { return S.deck - S.hh * (L.seat === 'floor' ? 0.17 : L.seat === 'high' ? 0.6 : 0.37); }
function seatDraw(q, S, L, x, dir, k) {
  var hh = S.hh, deck = S.deck, h = SEAT[L.seat].seat * hh * 0.9, col;
  if (L.seat === 'stool') { col = STOOL[(k + S.seed) % STOOL.length]; fp(q, [[x - hh * 0.12, deck - h], [x + hh * 0.12, deck - h], [x + hh * 0.15, deck], [x + hh * 0.1, deck], [x, deck - h * 0.5], [x - hh * 0.1, deck], [x - hh * 0.15, deck]], col); fr(q, x - hh * 0.13, deck - h - 1, hh * 0.26, hh * 0.035, mixc(col, '#ffffff', 0.15)); }
  else if (L.seat === 'chair') { col = L.chairCol || '#6a4424'; fr(q, x - hh * 0.13, deck - h, hh * 0.26, hh * 0.04, col); ln(q, [[x - hh * 0.11, deck - h], [x - hh * 0.12, deck]], col, 2); ln(q, [[x + hh * 0.11, deck - h], [x + hh * 0.12, deck]], col, 2); ln(q, [[x - dir * hh * 0.12, deck - h], [x - dir * hh * 0.14, deck - h - hh * 0.42]], col, 2.2); ln(q, [[x - dir * hh * 0.12, deck - h - hh * 0.2], [x - dir * hh * 0.13, deck - h - hh * 0.38]], col, hh * 0.05); }
  else if (L.seat === 'high') { col = '#2a2a2e'; fe(q, x, deck - h, hh * 0.12, hh * 0.03, '#8a4a2a'); ln(q, [[x - hh * 0.07, deck - h], [x - hh * 0.1, deck]], col, 1.6); ln(q, [[x + hh * 0.07, deck - h], [x + hh * 0.1, deck]], col, 1.6); fr(q, x - hh * 0.09, deck - h * 0.4, hh * 0.18, 1.5, col); }
  else { fe(q, x, deck - hh * 0.03, hh * 0.18, hh * 0.04, pick(K.rnd(k + S.seed), ['#c0392b', '#2f6db0', '#e8b84a', '#2f8f5b'])); }
}
function tableDraw(q, S, L, u, out) {
  var hh = S.hh, deck = S.deck, ty = tableY(L, S), x = u.x, tw = hh * (L.seat === 'high' ? 0.22 : 0.36), k = L.table, T = L.T;
  if (u.music) { fr(q, x + hh * 0.3, deck - hh * 0.95, 2, hh * 0.95, '#2a2a2e'); fe(q, x + hh * 0.3, deck - hh * 0.97, hh * 0.04, hh * 0.05, '#2a2a2e'); paper(q, rect(x + hh * 0.42, deck - hh * 0.4, hh * 0.3, hh * 0.4), '#2a2a2e', 0.6); fe(q, x + hh * 0.57, deck - hh * 0.22, hh * 0.1, hh * 0.1, '#5a5e64'); return; }
  if (u.pool) { var pw = hh * 0.75; paper(q, rect(x - pw, deck - hh * 0.42, pw * 2, hh * 0.08), '#2f7a4a', 0.6); fr(q, x - pw - 3, deck - hh * 0.36, pw * 2 + 6, hh * 0.08, '#6a3a1e'); fr(q, x - pw + hh * 0.05, deck - hh * 0.28, hh * 0.08, hh * 0.28, '#6a3a1e'); fr(q, x + pw - hh * 0.13, deck - hh * 0.28, hh * 0.08, hh * 0.28, '#6a3a1e');
    for (var i = 0; i < 6; i++) fe(q, x - pw * 0.2 + (i % 3) * hh * 0.05, deck - hh * 0.45 - Math.floor(i / 3) * hh * 0.04, hh * 0.025, hh * 0.025, ['#f2c42a', '#2f6db0', '#d8242a', '#7a3a8a', '#e8642a', '#1a1a1a'][i]); return; }
  if (k === 'khantok') { paper(q, poly([[x - tw * 0.4, deck], [x + tw * 0.4, deck], [x + tw * 0.25, ty + hh * 0.03], [x - tw * 0.25, ty + hh * 0.03]]), '#8a1e14', 0.8); paper(q, E(x, ty + hh * 0.02, tw * 1.05, hh * 0.05), S.night ? '#8a2a1e' : '#b0301e', 1); q.strokeStyle = '#e8b84a'; q.lineWidth = 1.2; q.beginPath(); q.ellipse(x, ty + hh * 0.02, tw * 1.05, hh * 0.05, 0, 0, Math.PI); q.stroke(); laiKham(q, x - tw * 0.25, x + tw * 0.25, deck - hh * 0.06, hh * 0.025); }
  else if (k === 'marble' || k === 'high') { ln(q, [[x, ty], [x, deck]], '#2a2a2e', 2.5); fe(q, x, deck - 1, hh * 0.12, hh * 0.02, '#2a2a2e'); paper(q, E(x, ty + 1, tw * (k === 'high' ? 1.2 : 0.9), hh * 0.035), k === 'high' ? '#6a3a1e' : '#f2efe8', 0.6); if (k === 'marble') ln(q, [[x - tw * 0.5, ty + 1], [x + tw * 0.2, ty + 2]], 'rgba(120,120,130,.4)', 0.8); }
  else { var col = { steel: '#d8dce2', wood: '#8a5a32', check: '#f6f2ea', cloth: '#f6f2ea', red: '#a8241c', plastic: pick(K.rnd(S.seed + u.i), ['#f8c8d8', '#c8e0f8', '#f8e8a8', '#d8f0c8']), white: '#f2f2ee' }[k] || '#d8dce2', drape = k === 'check' || k === 'cloth' || k === 'red' || k === 'plastic';
    ln(q, [[x - tw + hh * 0.06, ty], [x - tw + hh * 0.08, deck]], k === 'wood' ? '#5a3a20' : '#8a8e94', 2); ln(q, [[x + tw - hh * 0.06, ty], [x + tw - hh * 0.08, deck]], k === 'wood' ? '#5a3a20' : '#8a8e94', 2);
    paper(q, rect(x - tw, ty, tw * 2, drape ? hh * 0.14 : hh * 0.045), col, 0.7);
    if (k === 'check') { q.fillStyle = 'rgba(200,30,40,.5)'; for (var cx = x - tw; cx < x + tw; cx += hh * 0.07) for (var cy = 0; cy < 2; cy++) if ((Math.round((cx - x) / (hh * 0.07)) + cy) % 2) q.fillRect(cx, ty + cy * hh * 0.07, hh * 0.07, hh * 0.07); }
    if (k === 'plastic') for (i = 0; i < 6; i++) fe(q, x - tw + (i + 0.5) * tw / 3, ty + hh * 0.07, hh * 0.025, hh * 0.025, i % 2 ? '#e8408a' : '#5aa83a');
    if (k === 'red') laiKham(q, x - tw, x + tw, ty + hh * 0.08, hh * 0.03, '#f2c94c');
    if (k === 'steel') fr(q, x - tw, ty + 1, tw * 2, 1, 'rgba(255,255,255,.6)'); }
  if (T.cookTable) { cooker(q, x, ty, hh, T.cookTable); out.push({ cook: T.cookTable, x: x, y: ty }); return; }
  var s = hh * 0.32;
  u.items.forEach(function (it, j) { var dx = u.solo ? x + (j ? -1 : 1) * hh * 0.1 * (u.dir || 1) : x + (j ? 1 : -1) * hh * 0.14, sp = DISH[it] ? DISH[it](q, dx, ty, s * (it === 'laptop' ? 1.1 : 1), S) : null; if (sp) out.push({ x: sp[0], y: sp[1], k: j + u.i }); });
  if (T.caddy && !u.solo) caddy(q, x, ty, hh * 0.8);
  if (T.stacks) for (i = 0; i < 2; i++) bowls(q, x + (i ? 1 : -1) * tw * 0.75, ty, hh * 0.7, 6 + (u.i + i) % 5, '#f6f2ea');
}
/* the grill or pot in the middle of the table: a dome over a charcoal bucket, or a broth pot */
function cooker(q, x, ty, hh, kind) {
  paper(q, poly([[x - hh * 0.13, ty], [x + hh * 0.13, ty], [x + hh * 0.11, ty - hh * 0.12], [x - hh * 0.11, ty - hh * 0.12]]), '#a8582a', 0.6);
  if (kind === 'dome') { fe(q, x, ty - hh * 0.13, hh * 0.21, hh * 0.04, '#c8ccd2'); fe(q, x, ty - hh * 0.14, hh * 0.19, hh * 0.03, '#e8c070'); paper(q, function (p) { p.beginPath(); p.ellipse(x, ty - hh * 0.15, hh * 0.13, hh * 0.1, 0, Math.PI, TAU); p.closePath(); }, '#9aa0a8', 0.4); for (var i = 0; i < 4; i++) fe(q, x - hh * 0.07 + i * hh * 0.045, ty - hh * 0.2 - (i % 2) * hh * 0.03, hh * 0.03, hh * 0.015, '#e89a8a', 0.3); }
  else { paper(q, rect(x - hh * 0.15, ty - hh * 0.24, hh * 0.3, hh * 0.12), '#c8ccd2', 0.5); fe(q, x, ty - hh * 0.24, hh * 0.15, hh * 0.03, '#d8b878'); }
  [-1, 1].forEach(function (sd) { fe(q, x + sd * hh * 0.27, ty - hh * 0.01, hh * 0.08, hh * 0.02, '#f6f2ea'); fe(q, x + sd * hh * 0.27, ty - hh * 0.025, hh * 0.05, hh * 0.015, sd < 0 ? '#e89a8a' : '#5aa83a'); });
}
function seated(c, S, L, u, side, d, k) {
  var hh = S.hh, T = L.T, x = seatX(u, side, L, hh), dir = -side, P0 = SEAT[L.seat], h = hh * 0.9, ty = tableY(L, S), item = u.items[(side + 1) / 2] || '';
  d.dir = dir; d.skirt = 0;
  if (item === 'laptop') { var tp = [u.x - dir * hh * 0.05 + Math.sin(S.t / 90 + k) * hh * 0.01, ty - hh * 0.03]; worker(c, x, S.deck, h, { lean: 0.22, seat: P0.seat, legs: P0.legs }, d, tp, [tp[0] - dir * hh * 0.06, ty - hh * 0.03 + Math.sin(S.t / 110) * hh * 0.01]); return; }
  if (item === 'book') { var bp = [x + dir * hh * 0.24, ty - hh * 0.26], me0 = worker(c, x, S.deck, h, { lean: 0.05, seat: P0.seat, legs: P0.legs }, d, bp, [bp[0] - dir * hh * 0.02, bp[1] + hh * 0.03]); var pg = Math.sin(S.t / 3000) > 0.95 ? 0.4 : 1; fp(c, [[bp[0], bp[1]], [bp[0] + dir * hh * 0.1 * pg, bp[1] - hh * 0.12], [bp[0] - dir * hh * 0.02, bp[1] - hh * 0.14]], '#f6f2ea'); fp(c, [[bp[0], bp[1]], [bp[0] - dir * hh * 0.08, bp[1] - hh * 0.13], [bp[0] - dir * hh * 0.02, bp[1] - hh * 0.14]], '#e8e2d0'); return; }
  var hold = T.hold[k % T.hold.length], per = 3 + (k % 3) * 0.7, ph = ((S.t / 1000) / per + k * 0.37) % 1;
  var lift = ph < 0.35 ? 0 : ph < 0.5 ? ease((ph - 0.35) / 0.15) : ph < 0.8 ? 1 : 1 - ease((ph - 0.8) / 0.2), lean = P0.lean + 0.1 * (1 - lift);
  var sh = shoulder(x, S.deck, h, P0.seat, lean, dir), hd = [sh[0] + dir * Math.sin(lean) * h * 0.14, sh[1] - Math.cos(lean) * h * 0.14];
  var mouth = [hd[0] + dir * h * 0.14, hd[1] + h * 0.06], dish = T.cookTable ? [u.x - dir * hh * 0.02, ty - hh * 0.18] : [u.x - dir * hh * 0.12, ty - hh * 0.05];
  if (T.cookTable && k % 2) { lift = 0.15 * (1 + Math.sin(S.t / 500 + k)); }
  var me = worker(c, x, S.deck, h, { lean: lean, seat: P0.seat, legs: P0.legs }, d, [lerp(dish[0], mouth[0], lift), lerp(dish[1], mouth[1], lift)], [x + dir * h * 0.24, ty - hh * 0.02]);
  held(c, me.hand[0], dir, h, hold, lift, S.t);
  if (T.hatDiner && k === 1) hat(c, me, T.hatDiner);
}
function musician(c, S, L, u, d) {
  var hh = S.hh, x = u.x - hh * 0.05, h = hh * 0.9; d.dir = 1; d.skirt = 0;
  var st = Math.sin(S.t / 140), gx = x + hh * 0.12, gy = S.deck - hh * 0.42;
  paper(c, rect(x - hh * 0.1, S.deck - hh * 0.4, hh * 0.2, hh * 0.04), '#6a3a1e', 0.3); ln(c, [[x - hh * 0.08, S.deck - hh * 0.4], [x - hh * 0.1, S.deck]], '#6a3a1e', 1.5); ln(c, [[x + hh * 0.08, S.deck - hh * 0.4], [x + hh * 0.1, S.deck]], '#6a3a1e', 1.5);
  var me = worker(c, x, S.deck, h, { lean: 0.05, seat: 0.45, legs: [1.3, -1.2, 1.2, -1.1] }, d, [gx + st * hh * 0.03, gy + hh * 0.02], [gx + hh * 0.3, gy - hh * 0.12]);
  c.save(); c.translate(gx, gy); c.rotate(-0.35); fe(c, 0, 0, hh * 0.13, hh * 0.1, '#c8823a'); fe(c, hh * 0.1, 0, hh * 0.09, hh * 0.075, '#c8823a'); fe(c, hh * 0.04, 0, hh * 0.035, hh * 0.035, '#2a1a10'); fr(c, hh * 0.15, -hh * 0.015, hh * 0.3, hh * 0.03, '#5a3a20'); c.restore();
  K.notes(c, gx + hh * 0.1, gy - hh * 0.3, S.t, 3, S.night ? '#ffd27a' : '#fff');
}
function poolPlayer(c, S, L, u, d) {
  var hh = S.hh, pw = hh * 0.75, x = u.x + pw + hh * 0.2, h = hh * 0.92, k = Math.sin(S.t / 600), shot = (S.t / 4000) % 1; d.dir = -1;
  var tip = [u.x + pw * 0.45 - k * hh * 0.06, S.deck - hh * 0.5], butt = [tip[0] + hh * 0.75, tip[1] - hh * 0.12];
  worker(c, x, S.deck, h, { lean: 0.95 }, d, [lerp(tip[0], butt[0], 0.3), lerp(tip[1], butt[1], 0.3)], [lerp(tip[0], butt[0], 0.85), lerp(tip[1], butt[1], 0.85)]);
  ln(c, [tip, butt], '#c8a060', 2); var bx = u.x - pw * 0.6 * (shot < 0.5 ? ease(shot * 2) : 1); fe(c, u.x + pw * 0.35 - (shot < 0.5 ? ease(shot * 2) * pw * 0.9 : pw * 0.9) * 0.0 + (bx - u.x) * 0.2, S.deck - hh * 0.45, hh * 0.026, hh * 0.026, '#f6f2ea');
}

/* ---------------------------------------------------------------- the two still layers */
function ground(q, S, L) {
  var hh = S.hh, n = S.night, y = S.deck, col = L.type === 'garden' ? (n ? '#22301e' : '#6a8a4a') : L.type === 'teak' || L.type === 'hut' || L.type === 'reggae' ? (n ? '#2a2018' : '#9a7a52') : L.type === 'mall' ? (n ? '#4a4844' : '#ddd8ce') : L.type === 'river' ? (n ? '#22301e' : '#6f8a4a') : (n ? '#35322e' : '#b8b0a0');
  K.ground(q, S.x0, S.x1, y, S.H, col);
  if (L.type !== 'garden' && L.type !== 'river' && L.type !== 'mall' && L.type !== 'roof' && !(L.P.river && L.P.river.m < 400)) { var ry = y + (S.H - y) * 0.42; fr(q, S.x0, ry, S.span, S.H - ry, n ? '#26262a' : '#5a5a60'); fr(q, S.x0, ry, S.span, 2.5, n ? '#55524c' : '#d8d2c4'); for (var x = S.x0; x < S.x1; x += hh * 0.6) fr(q, x, ry + (S.H - ry) * 0.5, hh * 0.3, 2, n ? '#8a8060' : '#f2e6a8'); }
}
function back(q, S, L, box) {
  var hh = S.hh, T = L.T, st = L.st, P = L.P, open = L.state === 'open', i;
  if (L.pole) pole(q, S.x0 + hh * 0.8, S.deck, hh, L.bx0 + hh * 0.2, (L.top || S.deck - hh * 2) + hh * 0.15);
  L.glows = [];
  BLD[L.type].back(q, S, L);
  if (L.type === 'cart') { var ux = (L.bx0 + L.bx1) / 2, uy = S.deck - hh * 1.88; ln(q, [[ux, uy], [ux, S.deck - hh * 0.4]], '#9aa0a8', 2.5);
    paper(q, function (p) { p.beginPath(); p.moveTo(ux - hh * 1.05, uy + hh * 0.28); p.quadraticCurveTo(ux, uy - hh * 0.22, ux + hh * 1.05, uy + hh * 0.28); for (var k = 6; k > 0; k--) p.quadraticCurveTo(ux - hh * 1.05 + (k - 0.5) * hh * 0.35, uy + hh * 0.36, ux - hh * 1.05 + (k - 1) * hh * 0.35, uy + hh * 0.28); p.closePath(); }, L.umb[0], 1.2);
    q.save(); q.beginPath(); q.moveTo(ux - hh * 1.05, uy + hh * 0.3); q.quadraticCurveTo(ux, uy - hh * 0.22, ux + hh * 1.05, uy + hh * 0.3); q.closePath(); q.clip(); for (i = 0; i < 6; i += 2) fp(q, [[ux, uy - hh * 0.05], [ux - hh * 1.05 + i * hh * 0.35, uy + hh * 0.32], [ux - hh * 1.05 + (i + 1) * hh * 0.35, uy + hh * 0.32]], L.umb[1]); q.restore(); }
  if (L.inner && L.inner !== 'open' && L.type !== 'cart' && L.state !== 'closed') decor(q, S, L);
  if (L.stk && L.state !== 'closed' || L.type === 'garden' || L.type === 'roof' || L.type === 'river' || L.type === 'cart') ST[L.stk].back(q, S, L, st);
  if (L.state !== 'closed' || L.type === 'garden' || L.type === 'roof' || L.type === 'river' || L.type === 'cart' || L.type === 'tent') L.units.forEach(function (u) { if (u.music || u.pool) return; if (L.state === 'quiet') return; [-1, 1].forEach(function (sd, j) { if (!u.solo || (u.dir || 1) === -sd) seatDraw(q, S, L, seatX(u, sd, L, hh), -sd, u.i * 2 + j); }); });
  if (S.night) {
    var lit = open && L.inner !== 'open' && L.type !== 'garden' && L.type !== 'river';
    q.save(); q.beginPath(); q.rect(box[0], box[1], box[2], box[3]); if (lit) q.rect(L.ox0, L.oy, L.ox1 - L.ox0, S.deck - L.oy); q.clip('evenodd'); dusk(q, S, box, 0.42); q.restore();
    if (lit) { q.save(); q.globalCompositeOperation = 'lighter'; glow(q, (L.ox0 + L.ox1) / 2, S.deck - hh * 0.7, (L.ox1 - L.ox0) * 0.6, '255,200,120', 0.22); q.restore(); }
    else if (L.inner !== 'open' && L.state === 'quiet') { glow(q, (L.ox0 + L.ox1) / 2, L.oy + hh * 0.2, hh * 0.6, '255,220,150', 0.25); fe(q, (L.ox0 + L.ox1) / 2, L.oy + hh * 0.18, 2.5, 3, '#fff2c8'); }
    L.glows.forEach(function (g) { fr(q, g[0], g[1], g[2], g[3], '#ffd88a'); glow(q, g[0] + g[2] / 2, g[1] + g[3] / 2, g[2], '255,210,130', 0.35); });
  }
  q.save(); q.globalCompositeOperation = 'destination-over';
  ground(q, S, L);
  var sp = {}; for (var f in P) if (f !== 'river') sp[f] = P[f]; K.setting(cp(S, { c: q, place: sp, t: 0 }));
  q.restore();
}
function cp(S, o) { var X = {}; for (var f in S) X[f] = S[f]; for (f in o) X[f] = o[f]; return X; }
/* the back wall inside: a board of the trade's dishes, a cooler, a clock, a woven basket */
function decor(q, S, L) {
  var hh = S.hh, T = L.T, st = L.st, a = L.ox0, b = L.ox1, mx = L.board, my = L.oy + hh * 0.14;
  if (L.type !== 'glass' && L.kind !== 'bar') menuBoard(q, mx, my, hh, T.dishes, L.kind === 'cafe' || L.kind === 'bakery' ? 'chalk' : 'board');
  var cx = L.ss < 0 ? b - hh * 0.3 : a + hh * 0.3;
  if (L.kind !== 'bar' && L.kind !== 'cafe' && L.type !== 'glass' && b - a > hh * 3.6 && Math.abs(cx - mx) > hh * 0.9) cooler(q, cx, S.deck, hh, S.night);
  if (L.kind === 'cafe' && L.type !== 'glass') { for (var i = 0; i < 3; i++) { var px = lerp(a + hh * 0.4, b - hh * 0.4, (i + 0.5) / 3); ln(q, [[px, L.oy], [px, L.oy + hh * 0.3]], '#2a2a2e', 1); paper(q, function (p) { p.beginPath(); p.arc(px, L.oy + hh * 0.36, hh * 0.08, Math.PI, TAU); p.closePath(); }, pick(K.rnd(S.seed + i), ['#c8a060', '#2a2a2e', '#f2efe8', '#2f6a5a']), 0.3); if (S.night) L.glows.push([px - 2, L.oy + hh * 0.36, 4, 2]); } }
  if ((T.mix === LANNA || L.trade === 'isaan') && Math.abs(mx - (a + b) / 2) > hh * 0.4) { DISH.kratip(q, (a + b) / 2, L.oy + hh * 0.45, hh * 0.4); }
  if (L.type === 'shop' || L.type === 'tent') { var kx = (a + b) / 2 + hh * 0.9; q.fillStyle = '#f6f2ea'; q.beginPath(); q.arc(kx, L.oy + hh * 0.3, hh * 0.07, 0, TAU); q.fill(); ln(q, [[kx, L.oy + hh * 0.3], [kx, L.oy + hh * 0.25]], '#2a2a2e', 1); ln(q, [[kx, L.oy + hh * 0.3], [kx + hh * 0.04, L.oy + hh * 0.31]], '#2a2a2e', 1); }
  if (L.fan || L.type === 'shop' && S.night) tube(q, (a + b) / 2 - hh * 0.6, L.oy + hh * 0.11, hh, false);
}
function front(q, S, L, box) {
  var hh = S.hh, T = L.T, st = L.st, P = L.P, out = { steam: [], cook: [], sp: null }, closed = L.state === 'closed', quiet = L.state === 'quiet';
  var tablesShown = !closed || L.type === 'garden' || L.type === 'roof' || L.type === 'river' || L.type === 'cart' || L.type === 'tent';
  if (tablesShown) L.units.forEach(function (u) { var o2 = []; if (quiet || closed) { if (!u.music && !u.pool) { tableDraw(q, S, cp(L, { T: cp(T, { cookTable: null }) }), cp(u, { items: [] }), []); stacked(q, S, L, u); } } else { tableDraw(q, S, L, u, o2); o2.forEach(function (p) { (p.cook ? out.cook : out.steam).push(p); }); } });
  if (L.type === 'cart' && closed) { paper(q, poly([[L.bx0 - hh * 0.05, S.deck - hh * 0.18], [L.bx0 + hh * 0.1, S.deck - hh * 1.0], [L.bx1 - hh * 0.1, S.deck - hh * 1.02], [L.bx1 + hh * 0.05, S.deck - hh * 0.18]]), '#2f6db0', 1); for (var i = 1; i < 4; i++) ln(q, [[L.bx0 + (L.bx1 - L.bx0) * i / 4, S.deck - hh * 1.0], [L.bx0 + (L.bx1 - L.bx0) * i / 4 + hh * 0.05, S.deck - hh * 0.2]], 'rgba(255,255,255,.25)', 1); ln(q, [[L.bx0, S.deck - hh * 0.6], [L.bx1, S.deck - hh * 0.62]], '#f2e6a8', 1.5); }
  else if (!closed || L.type === 'garden' || L.type === 'roof' || L.type === 'river' || L.type === 'tent') ST[L.stk].front(q, S, L, st);
  if (T.noren && !closed && L.type !== 'cart') noren(q, S, L);
  BLD[L.type].front(q, S, L);
  if (closed) BLD[L.type].shut(q, S, L);
  L.props.forEach(function (p) {
    if (p.k === 'spirit') out.sp = spiritHouse(q, p.x, S.deck, hh, K.rnd(S.seed + 41));
    else if (p.k === 'plant') plant(q, p.pk, p.x, S.deck, hh, K.rnd(S.seed + Math.round(p.x)));
    else if (p.k === 'moto') moto(q, p.x, S.deck, hh, p.col, p.dir, p.helmet);
    else if (p.k === 'bike') bicycle(q, p.x, S.deck, hh, p.col, p.basket);
    else if (p.k === 'jar') waterJar(q, p.x, S.deck, hh);
    else if (p.k === 'song') songthaew(q, p.x, S.deck, hh, p.col);
    else if (p.k === 'jflag') jFlag(q, p.x, S.deck, hh);
    else if (p.k === 'plate') roadPlate(q, p.x, S.deck, hh, P.road);
    else if (p.k === 'aframe') aframe(q, p.x, S.deck, hh, P.hours && L.state !== 'quiet' ? [closed ? 'ปิด' : 'เปิด'].concat(hoursLines(P.hours)) : null, S.night, T.dishes[0]);
  });
  if (L.type !== 'cart' && L.type !== 'mall') { var sx = L.shingleSide > 0 ? L.bx1 + hh * 0.38 : L.bx0 - hh * 0.38; shingle(q, sx, (L.oy || S.deck - hh * 1.4) - hh * 0.05, hh, L.shingleK === 'cake' ? 'bakery' : L.shingleK, L.shingleSide, S.night, L.shingleK === 'cake'); }
  if (S.night) { var lit = L.state === 'open' && L.inner !== 'open' && L.type !== 'garden' && L.type !== 'river'; q.save(); q.beginPath(); q.rect(box[0], box[1], box[2], box[3]); if (lit) q.rect(L.ox0, L.oy, L.ox1 - L.ox0, S.deck - L.oy); q.clip('evenodd'); dusk(q, S, box, 0.36); q.restore(); }
  var sy = L.type === 'cart' ? S.deck - hh * 1.62 : L.signY, sb = K.sign(q, L.signCx, sy, P, hh, L.signCol, L.state === 'open' ? (S.night ? true : undefined) : false);
  out.sign = sb; return out;
}
/* the place's own hours, cut to two short lines */
function hoursLines(h) { var parts = String(h).split(/;\s*/).slice(0, 2); return parts.map(function (x) { return x.length > 20 ? x.slice(0, 19) + '…' : x; }); }
function stacked(q, S, L, u) { if (L.seat !== 'stool' && L.seat !== 'chair') return; var hh = S.hh, ty = tableY(L, S); for (var i = 0; i < 2; i++) { var x = u.x + (i - 0.5) * hh * 0.3, col = L.seat === 'stool' ? STOOL[(u.i + i + S.seed) % STOOL.length] : '#6a4424'; fp(q, [[x - hh * 0.13, ty], [x + hh * 0.13, ty], [x + hh * 0.1, ty - hh * 0.04], [x - hh * 0.1, ty - hh * 0.04]], col); ln(q, [[x - hh * 0.1, ty - hh * 0.04], [x - hh * 0.14, ty - hh * 0.28]], col, 2); ln(q, [[x + hh * 0.1, ty - hh * 0.04], [x + hh * 0.14, ty - hh * 0.28]], col, 2); } }
/* the noren: a short split curtain over a Japanese door, each panel swinging on its own */
function noren(q, S, L) { var hh = S.hh, a = L.ox0 + hh * 0.05, b = Math.min(L.ox1 - hh * 0.05, a + hh * 1.6), n = 4, w = (b - a) / n; for (var i = 0; i < n; i++) { paper(q, rect(a + i * w + 1, L.oy + hh * 0.02, w - 2, hh * 0.32), '#1f2f5a', 0.4); if (i === 1 || i === 2) { q.strokeStyle = '#f2efe8'; q.lineWidth = 1.5; q.beginPath(); q.arc(a + i * w + (i === 1 ? w : 0), L.oy + hh * 0.18, hh * 0.08, 0, TAU); q.stroke(); } } fr(q, a - 2, L.oy, b - a + 4, 3, '#5a3a20'); }

/* ---------------------------------------------------------------- what moves */
function neon(c, N, hh, t) {
  var on = !(Math.sin(t / 97) * Math.sin(t / 31) > 0.93), col = N.k === 'mug' ? '#ffb02e' : N.k === 'glass' ? '#5af0ff' : '#ff4a9a';
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round';
  for (var pass = 0; pass < 2; pass++) { c.globalAlpha = on ? (pass ? 1 : 0.35) : 0.15; c.strokeStyle = pass ? '#fff' : col; c.fillStyle = pass ? '#fff' : col; c.lineWidth = pass ? 1.2 : 5;
    if (N.k === 'glass') { c.beginPath(); c.moveTo(N.x - hh * 0.2, N.y - hh * 0.2); c.lineTo(N.x + hh * 0.2, N.y - hh * 0.2); c.lineTo(N.x, N.y + hh * 0.02); c.closePath(); c.moveTo(N.x, N.y + hh * 0.02); c.lineTo(N.x, N.y + hh * 0.2); c.moveTo(N.x - hh * 0.1, N.y + hh * 0.2); c.lineTo(N.x + hh * 0.1, N.y + hh * 0.2); c.stroke(); }
    else if (N.k === 'mug') { c.strokeRect(N.x - hh * 0.12, N.y - hh * 0.18, hh * 0.22, hh * 0.32); c.beginPath(); c.arc(N.x + hh * 0.12, N.y - hh * 0.02, hh * 0.08, -1.4, 1.4); c.stroke(); }
    else { c.font = '800 ' + Math.round(hh * 0.2) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.lineWidth = pass ? 0.8 : 3; c.strokeText(N.k, N.x, N.y); } }
  c.restore(); if (on) glow(c, N.x, N.y, hh * 0.5, '255,120,200', 0.12);
}
function eaveKhom(c, S, L) {
  var hh = S.hh, a, b, y, cols = ['#e8402a', '#f29a2a', '#f2c94c'];
  if (L.type === 'garden' || L.type === 'river') { a = L.sa + hh * 0.2; b = L.sb - hh * 0.2; y = S.deck - hh * 1.62; } else { a = L.ox0 + hh * 0.2; b = L.ox1 - hh * 0.2; y = L.oy + hh * 0.02; }
  var n = Math.max(2, Math.round((b - a) / (hh * 0.55))); for (var i = 0; i < n; i++) { var x = lerp(a, b, (i + 0.5) / n); if (Math.abs(x - L.signCx) < hh * 1.3 && y > L.signY - hh * 0.2 && y < L.signY + hh * 0.6) continue; khom(c, x, y, hh, S.t, i, L.T.redLantern ? '#d8242a' : cols[i % 3], S.night); }
}
function live(c, S, L, crew, out, phase) {
  var hh = S.hh, T = L.T, st = L.st, open = L.state === 'open', t = S.t, i;
  if (phase === 0) {
    if (L.P.river && L.P.river.m != null && L.P.river.m < 400 && L.type !== 'roof') K.setting(cp(S, { place: { river: L.P.river } }));
    if (L.neon && S.night && open) neon(c, L.neon, hh, t);
    if (L.fan && L.state !== 'closed') ceilingFan(c, (L.ox0 + L.ox1) / 2 + hh * 0.3, L.oy, hh, open ? t : 0);
    if (open) {
      var cook = crew[0]; if (ST[L.stk].live) ST[L.stk].live(c, S, L, st, cook, T);
      var k = 0; L.units.forEach(function (u) { if (!u.full) return; if (u.music) { musician(c, S, L, u, crew[2 + k++]); return; } if (u.pool) { poolPlayer(c, S, L, u, crew[2 + k++]); return; }
        var sides = u.solo ? [(u.dir || 1) > 0 ? -1 : 1] : u.two ? [-1, 1] : [L.units.length % 2 ? 1 : -1]; sides.forEach(function (sd) { seated(c, S, L, u, sd, crew[2 + k], k); k++; }); });
    }
    return;
  }
  if (open) { out.steam.forEach(function (p) { steam(c, p.x, p.y, hh * 0.45, t, p.k, 2, 0.55); });
    out.cook.forEach(function (p, j) { if (p.cook === 'dome') { smoke(c, p.x, p.y - hh * 0.22, hh * 0.7, t, j * 0.3); } else { steam(c, p.x, p.y - hh * 0.25, hh * 0.55, t, j, 3, 0.7); for (var b = 0; b < 4; b++) { var bb = (t / 500 + b * 0.27 + j) % 1; fe(c, p.x - hh * 0.1 + b * hh * 0.065, p.y - hh * 0.245, bb * 2.5, bb * 1.4, 'rgba(255,255,255,.75)'); } } }); }
  if (L.state !== 'closed' && (L.khom || T.redLantern)) eaveKhom(c, S, L);
  if (T.chochin && L.state !== 'closed') { var cx2 = L.ss < 0 ? L.ox1 - hh * 0.25 : L.ox0 + hh * 0.25, th = 0.12 * Math.cos(t / 700); ln(c, [[cx2, L.oy], [cx2 + Math.sin(th) * hh * 0.08, L.oy + hh * 0.08]], '#2a2a2e', 1); if (S.night) glow(c, cx2, L.oy + hh * 0.22, hh * 0.3, '255,90,60', 0.45); fe(c, cx2 + Math.sin(th) * hh * 0.1, L.oy + hh * 0.22, hh * 0.09, hh * 0.13, '#d8242a'); fr(c, cx2 - hh * 0.07 + Math.sin(th) * hh * 0.1, L.oy + hh * 0.09, hh * 0.14, hh * 0.025, '#1a1a1a'); fr(c, cx2 - hh * 0.07 + Math.sin(th) * hh * 0.1, L.oy + hh * 0.33, hh * 0.14, hh * 0.025, '#1a1a1a'); }
  if (L.lights) { var on = L.state !== 'closed' && (open || S.night), ya, yb, xa, xb;
    if (L.type === 'garden' || L.type === 'river') { xa = L.sl ? L.sb : L.tr ? L.tr.x0 + hh * 0.4 : L.bx0; xb = L.sl ? (L.tr ? L.tr.x1 - hh * 0.4 : L.bx1) : L.sa; ya = S.deck - hh * 1.5; yb = S.deck - hh * 1.6; fairy(c, Math.min(xa, xb), ya, Math.max(xa, xb), yb, hh * 0.25, hh, t, S.night, on); }
    else if (L.type === 'roof') fairy(c, L.bx0, L.top + hh * 0.05, L.bx1, L.top + hh * 0.08, hh * 0.3, hh, t, S.night, on);
    else if (L.type === 'cart') { var ux = (L.bx0 + L.bx1) / 2; if (S.night && on) { glow(c, ux, S.deck - hh * 1.42, hh * 0.9, '255,220,150', 0.4); fe(c, ux, S.deck - hh * 1.42, 3, 4, '#fff6c8'); } ln(c, [[ux, S.deck - hh * 1.6], [ux, S.deck - hh * 1.46]], '#2a2a2e', 1); }
    else if (L.shingleSide) { var e0 = L.shingleSide > 0 ? L.bx1 : L.bx0, e1 = e0 + L.shingleSide * hh * 1.3; fairy(c, Math.min(e0, e1), (L.oy || S.deck - hh * 1.4) + hh * 0.35, Math.max(e0, e1), (L.oy || S.deck - hh * 1.4) + hh * 0.5, hh * 0.15, hh, t, S.night, on); } }
  if (out.sp) incense(c, out.sp, hh, t);
  L.pets.forEach(function (p) { if (p.k === 'dog') dog(c, p.x, S.deck + hh * 0.1, hh, t, p.sleep || !open ? 'sleep' : 'sit', p.col, p.dir); else if (p.k === 'cat') cat(c, p.x, S.deck + hh * 0.06, hh, t, p.col, p.dir); else if (p.k === 'hens') hens(c, p.x, S.deck + hh * 0.08, hh, t); });
  if (L.state === 'closed' && S.night) { var lx = L.type === 'cart' ? (L.bx0 + L.bx1) / 2 : L.bx0 + hh * 0.25; moth(c, lx, (L.oy || S.deck - hh * 1.4) - hh * 0.1, hh, t); }
  if (L.server && L.units.length) { var d = crew[1], a = st.cx, b = L.units[L.units.length - 1].x, u = tri(t / 7000), x = lerp(a, b, ease(u)), dir = Math.cos(t / 7000 * TAU) > 0 ? 1 : -1;
    d.dir = (b > a ? 1 : -1) * (((t / 3500) | 0) % 2 ? -1 : 1); d.skirt = 0; var me = worker(c, x, S.deck + hh * 0.12, hh * 0.95, walkPose(t), d, [x + d.dir * hh * 0.2, S.deck - hh * 0.55], null);
    fe(c, me.hand[0][0], me.hand[0][1] - 2, hh * 0.15, hh * 0.025, '#c8ccd2'); if (T.cookTable) { fe(c, me.hand[0][0], me.hand[0][1] - hh * 0.04, hh * 0.1, hh * 0.025, '#e89a8a'); } else DISH.water(c, me.hand[0][0], me.hand[0][1] - 2, hh * 0.3); }
  if (L.passer) { var d2 = crew[crew.length - 1], sp = S.span + hh * 2, px = S.x1 + hh - ((t / 1000 * hh * 0.35) % sp); d2.dir = -1; K.person(c, px, S.deck + hh * 0.2, hh * 0.95, K.walkP(t / 1000 * TAU * 0.9, false), d2); }
}
function walkPose(t) { var P = K.walkP(t / 1000 * TAU * 0.9, false); return { lean: P.lean, seat: P.seat, legs: P.legs }; }

/* ---------------------------------------------------------------- the scene */
var MIX = { restaurant: { casual: 0.7, sin: 0.15, mohom: 0.15 }, cafe: { casual: 0.9, mohom: 0.1 }, bar: { casual: 1 }, bakery: { casual: 0.8, sin: 0.2 }, streetfood: { casual: 0.75, mohom: 0.15, sin: 0.1 }, noodle: { casual: 0.75, sin: 0.12, mohom: 0.13 } };
function venue(S0, kind) {
  var S = cp(S0, {}); if (S.phone) S.hh *= 1.08;
  var c = S.c, hh = S.hh, L = plan(S, kind), T = L.T;
  var crew = K.town(S, 3 + L.units.length * 2 + 1, T.mix || MIX[kind]);
  var id = [kind, S.W, S.H, Math.round(S.x0), Math.round(S.x1), Math.round(S.deck), Math.round(hh * 10), S.seed, S.night ? 1 : 0, L.state].join('|');
  var box = [S.x0 - 6, S.deck - hh * 2.75, S.span + 12, S.H - S.deck + hh * 2.75];
  layer(S, id + '|b', box, function (q) { back(q, S, L, box); });
  live(c, S, L, crew, null, 0);
  var fr2 = layer(S, id + '|f', box, function (q) { return front(q, S, L, box); }), out = fr2.out || { steam: [], cook: [] };
  live(c, S, L, crew, out, 1);
  S0.hits.push({ k: 'place', x0: Math.min(L.bx0, out.sign ? out.sign.x0 : L.bx0), x1: Math.max(L.bx1, out.sign ? out.sign.x1 : L.bx1), y0: Math.min(L.top || S.deck - hh * 2, out.sign ? out.sign.y0 : S.deck), y1: S.deck + hh * 0.2 });
}
D.addScene('restaurant', function (S) { venue(S, 'restaurant'); }, null, 'h = 4v(1 − v)·h₀<br>rice tossed in the wok');
D.addScene('cafe', function (S) { venue(S, 'cafe'); }, null, 'r = aθ<br>the pour, and the rosetta it leaves');
D.addScene('bar', function (S) { venue(S, 'bar'); }, null, 'y = A·sin 2πft<br>the shaker’s beat');
D.addScene('bakery', function (S) { venue(S, 'bakery'); }, null, 'V = V₀·2<sup>t/τ</sup><br>the dough rising');
D.addScene('streetfood', function (S) { venue(S, 'streetfood'); }, null, 'x = A·sin(ky − ωt)<br>the smoke off the grill');
D.addScene('noodle', function (S) { venue(S, 'noodle'); }, null, 'y = A·|sin ωt|<br>the strainer’s dip');
})();
