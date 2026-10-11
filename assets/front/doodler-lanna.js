/* Lanna places for the auto-doodler (doodler.js), after Nan (2026-10-02): "some for chaotic
   market alleys", "some for lanna houses perched on top of skyscrapers (real phenomenon)",
   "some for traditional lanna architecture".
   'alley'        market lanes: Kad Luang's back alleys, Muang Mai at dawn, a night-market lane,
                  the Chinatown spice lane, the Chiang Rai night bazaar
   'rooftop'      teak houses and salas on the roofs of towers
   'lanna-house'  the ruen kalae with its granary, water jar, village lane, khantok and raising
   Still parts are cut once into an offscreen layer; what moves is drawn each frame off S.t. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU;
var person = K.person, POSE = K.POSE, walkP = K.walkP, town = K.town, CLOTH = K.CLOTH;
var FONT = '"Sarabun",system-ui,sans-serif';

/* ---------------------------------------------------------------- cut once, drawn every frame */
var LAYERS = {};
function mat(c) { return c.getTransform ? c.getTransform() : null; }
function layer(S, name, y0, y1, draw) {
  var c = S.c, m = mat(c);
  if (!m || typeof document === 'undefined') return draw(c);
  var bx = Math.floor(m.a * S.x0 + m.e), by = Math.floor(m.d * y0 + m.f), bw = Math.ceil(m.a * S.span) + 2, bh = Math.ceil(m.d * (y1 - y0)) + 2;
  var key = [S.W, S.H, S.x0, S.x1, S.deck, S.hh, +S.night, S.seed, m.a, m.d, m.e, m.f, y0, y1, S.variant, S.avoid ? S.avoid.cx + ':' + S.avoid.cy + ':' + S.avoid.r : ''].join(','), L = LAYERS[name];
  if (!L || L.key !== key) {
    var o = document.createElement('canvas'); o.width = Math.max(1, bw); o.height = Math.max(1, bh);
    var q = o.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - bx, m.f - by);
    L = LAYERS[name] = { key: key, cv: o, x: bx, y: by }; L.data = draw(q);
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(L.cv, L.x, L.y); c.restore();
  return L.data;   /* what the cut returned (where its parts stand), kept with it */
}
/* a soft round glow from a small cut-once disc */
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',95%,62%,1)'); g.addColorStop(0.45, 'hsla(' + h + ',95%,60%,.42)'); g.addColorStop(1, 'hsla(' + h + ',95%,60%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o) return;
  c.save(); c.globalAlpha = Math.max(0, Math.min(1, a)); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
/* the event's banner, slid along so it stays on the stage and under the clock */
function label(S, cx, y, col) {
  if (!S.label) return;
  var c = S.c; c.font = '800 ' + Math.round(Math.max(12, S.hh * 0.2)) + 'px ' + FONT;
  var bh = Math.max(20, S.hh * 0.32), half = c.measureText(S.label).width / 2 + 10 + bh * 0.6 + 4;
  var m = S.hh * 0.75;   /* clear of the tung flags at the stage's ends */
  cx = half * 2 + m * 2 > S.span ? S.x0 + S.span / 2 : Math.max(S.x0 + half + m, Math.min(S.x1 - half - m, cx));
  var cy = cap(S, cx - half, cx + half);
  if (S.phone) y = Math.min(y, Math.max(cy, S.H * 0.3));   /* on a phone the sky under the clock is free */
  y = Math.max(y, cy);
  K.banner(c, cx, y, S.label, S.hh, col, S.seed, S.hits);
}
function fig(S, d, x, y, h, P, dir) { d.dir = dir; return person(S.c, x, y, h, P, d); }
function flat(c, pts, col) { c.fillStyle = col; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.fill(); }
function line(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
function dot(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
function frac(v) { return v - Math.floor(v); }
function h2(i, j, s) { return frac(Math.sin(i * 12.9898 + j * 78.233 + s * 0.731) * 43758.5453); }
/* the highest a tall thing between xa and xb may reach: under the clock's circle (S.avoid),
   else under deck − 2.3·hh in the band's right quarter */
function cap(S, xa, xb) {
  var A = S.avoid;
  if (A) { var dx = A.cx < xa ? xa - A.cx : A.cx > xb ? A.cx - xb : 0; return dx >= A.r ? S.H * 0.03 : A.cy + Math.sqrt(A.r * A.r - dx * dx) + 4; }
  return xb > S.W * (S.phone ? 0.6 : 0.77) ? S.deck - S.hh * 2.3 : S.H * 0.03;
}
function look(S, list) { var v = S.variant; return list.indexOf(v) >= 0 ? v : list[(S.seed >>> 4) % list.length]; }
function words(e) { return (e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 160); }
function chooser(rules, list) { return function (e) { var s = words(e); for (var i = 0; i < rules.length; i++) if (rules[i][1].test(s)) return rules[i][0]; return list[K.hash(e.k || s) % list.length]; }; }
/* something hung from a point swings as a pendulum in the breeze, θ = θ₀·sin(√(g/L)·t + φ) */
function swing(t, L, a0, ph) { return a0 * (0.55 + 0.45 * Math.sin(t * 0.37 + ph * 3)) * Math.sin(Math.sqrt(9.8 / L) * t * 0.5 + ph); }
function dim(hex, k, tint) {
  var n = parseInt(hex.slice(1), 16), r = n >> 16, g = n >> 8 & 255, b = n & 255, tt = tint || [30, 30, 60];
  return 'rgb(' + Math.round(r * k + tt[0] * (1 - k)) + ',' + Math.round(g * k + tt[1] * (1 - k)) + ',' + Math.round(b * k + tt[2] * (1 - k)) + ')';
}
/* catenary points, y = y₀ + sag − sag·(cosh((x − m)/a) − 1)/(cosh(h/a) − 1) */
function cat(xa, xb, y, sag, n) {
  var xm = (xa + xb) / 2, half = (xb - xa) / 2, a = half / 1.4, ch = Math.cosh(half / a) - 1, out = [];
  for (var i = 0; i <= n; i++) { var x = lerp(xa, xb, i / n); out.push([x, y + sag - sag * (Math.cosh((x - xm) / a) - 1) / ch]); }
  return out;
}
/* bulbs along a catenary, each breathing on its own phase (bulb·glow at night) */
function bulbs(c, xa, xb, y, sag, every, nt, t, hue) {
  var n = Math.max(2, Math.round((xb - xa) / every)), P = cat(xa, xb, y, sag, n * 2), i;
  line(c, P, 'rgba(30,20,20,.8)', 1);
  for (i = 1; i < P.length - 1; i += 2) {
    var b = 0.75 + 0.25 * Math.sin(t * 2.3 + i * 1.7) * Math.sin(t * 0.7 + i), x = P[i][0], yy = P[i][1] + 3;
    if (nt) glow(c, x, yy, every * 0.75, hue || 40, 0.55 * b);
    dot(c, x, yy, Math.max(1.6, every * 0.13), nt ? 'rgba(255,240,190,' + (0.6 + 0.4 * b) + ')' : '#f4ecd6');
  }
}
/* a soft puff of mist: a white radial disc cut once, stretched to an ellipse */
var PUFF = null;
function puff(c, x, y, rx, ry, a, nt) {
  if (!PUFF && typeof document !== 'undefined') { PUFF = document.createElement('canvas'); PUFF.width = PUFF.height = 64; var q = PUFF.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,.9)'); g.addColorStop(0.5, 'rgba(255,255,255,.45)'); g.addColorStop(1, 'rgba(255,255,255,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!PUFF) return;
  c.save(); c.globalAlpha = nt ? a * 0.6 : a; c.drawImage(PUFF, x - rx, y - ry, rx * 2, ry * 2); c.restore();
}
/* a little paper tag naming a part, its thread pointing at the part; the tag swings a little */
function tag(S, x, y, px, py, txt, u, t, ph) {
  var c = S.c, f = Math.max(10, u * 0.15); c.save(); c.font = '700 ' + Math.round(f) + 'px ' + FONT;
  var w = c.measureText(txt).width + f * 0.9, h = f * 1.5, sw = Math.sin(t * 1.3 + ph) * f * 0.12;
  x = Math.max(S.x0 + w / 2 + 3, Math.min(S.x1 - w / 2 - 3, x)) + sw;
  var ex = Math.max(x - w / 2, Math.min(x + w / 2, px)), ey = py < y ? y - h / 2 : y + h / 2;
  if (Math.abs(px - x) > w / 2 && Math.abs(py - y) < h) { ex = px < x ? x - w / 2 : x + w / 2; ey = y; }
  c.strokeStyle = 'rgba(255,240,200,.95)'; c.lineWidth = 1.4; c.setLineDash([3, 2]); c.beginPath(); c.moveTo(ex, ey); c.lineTo(px, py); c.stroke(); c.setLineDash([]);
  dot(c, px, py, f * 0.22 * (1 + 0.25 * Math.sin(t * 3 + ph)), '#ffd84a'); c.strokeStyle = '#5a2a10'; c.lineWidth = 1; c.beginPath(); c.arc(px, py, f * 0.22, 0, TAU); c.stroke();
  c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 3; c.shadowOffsetY = 2;
  c.fillStyle = '#f6ecd2'; c.beginPath(); c.moveTo(x - w / 2, y - h / 2); c.lineTo(x + w / 2 - h * 0.25, y - h / 2); c.lineTo(x + w / 2, y); c.lineTo(x + w / 2 - h * 0.25, y + h / 2); c.lineTo(x - w / 2, y + h / 2); c.closePath(); c.fill();
  c.shadowColor = 'transparent'; c.strokeStyle = '#b8322a'; c.lineWidth = 1; c.strokeRect(x - w / 2 + 2, y - h / 2 + 2, w - h * 0.25 - 4, h - 4);
  c.fillStyle = '#3a1a0a'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(txt, x - h * 0.1, y + 1);
  c.restore();
}

/* ================================================================ Lanna timber
   The ruen kalae seen gable-on: teak posts on stone feet, the floor, walls that lean out as
   they rise, the gable's boards laid as rays, the roof's two planes edge-on, and the
   bargeboards run on past the ridge and cross into the kalae, a V of carved horns. */
function teak(nt) {
  return { post: nt ? '#3a2416' : '#6e4226', wall: nt ? '#4a2c1a' : '#91572e', board: nt ? '#5a3820' : '#a86a3a', dark: nt ? '#1e120a' : '#3e2414',
    tile: nt ? '#352a28' : '#6a4a3c', horn: nt ? '#d8a84e' : '#f0c060', shade: nt ? 'rgba(0,0,0,.35)' : 'rgba(40,20,10,.25)' };
}
/* a horn of the kalae: a tapering board along a quadratic curve, B(s) = (1−s)²P₀ + 2s(1−s)P₁ + s²P₂,
   with a curl at its tip */
function horn(q, ax, ay, dir, hl, wd, col, edge) {
  var P0 = [ax, ay], P1 = [ax + dir * hl * 0.2, ay - hl * 0.85], P2 = [ax + dir * hl * 0.72, ay - hl * 0.98], L = [], R = [], n = 10, i;
  for (i = 0; i <= n; i++) {
    var s = i / n, a = (1 - s) * (1 - s), b = 2 * s * (1 - s), d = s * s, px = a * P0[0] + b * P1[0] + d * P2[0], py = a * P0[1] + b * P1[1] + d * P2[1];
    var tx = 2 * (1 - s) * (P1[0] - P0[0]) + 2 * s * (P2[0] - P1[0]), ty = 2 * (1 - s) * (P1[1] - P0[1]) + 2 * s * (P2[1] - P1[1]), tl = Math.hypot(tx, ty) || 1, hw = wd * (1 - 0.55 * s) / 2;
    L.push([px - ty / tl * hw, py + tx / tl * hw]); R.unshift([px + ty / tl * hw, py - tx / tl * hw]);
  }
  var pts = L.concat(R);
  q.fillStyle = col; q.beginPath(); pts.forEach(function (p, k) { k ? q.lineTo(p[0], p[1]) : q.moveTo(p[0], p[1]); }); q.closePath(); q.fill();
  var cr = wd * 0.42; q.strokeStyle = col; q.lineWidth = wd * 0.34; q.lineCap = 'round';
  q.beginPath(); q.arc(P2[0], P2[1] + cr, cr, -Math.PI / 2, dir > 0 ? Math.PI * 0.85 : Math.PI * 0.15, dir < 0); q.stroke();
  if (edge) { q.save(); q.shadowColor = 'transparent'; q.strokeStyle = edge; q.lineWidth = Math.max(0.8, wd * 0.12); q.beginPath(); pts.forEach(function (p, k) { k ? q.lineTo(p[0], p[1]) : q.moveTo(p[0], p[1]); }); q.closePath(); q.stroke();
    for (i = 1; i < 4; i++) { var s2 = i / 4.5, a2 = (1 - s2) * (1 - s2), b2 = 2 * s2 * (1 - s2), d2 = s2 * s2; dot(q, a2 * P0[0] + b2 * P1[0] + d2 * P2[0], a2 * P0[1] + b2 * P1[1] + d2 * P2[1], wd * 0.12, edge); } q.restore(); }
}
/* one gable: rays of boards, roof planes with shingle strokes, bargeboards and kalae */
function gable(q, gx, gw, wt, rh, u, P, hs) {
  var ex = gw * 0.64, ey = wt + u * 0.2, ay = wt - rh, th = u * 0.13, g0 = gw * 0.47, k;
  paper(q, poly([[gx - g0, wt + 1], [gx + g0, wt + 1], [gx, ay + th * 1.3]]), P.board, 1);
  q.strokeStyle = P.dark; q.lineWidth = Math.max(0.7, u * 0.016); q.beginPath();
  for (k = 1; k < 10; k++) { var f = k / 10, px = f < 0.5 ? lerp(gx - g0, gx, f * 2) : lerp(gx, gx + g0, f * 2 - 1), py = f < 0.5 ? lerp(wt, ay + th * 1.3, f * 2) : lerp(ay + th * 1.3, wt, f * 2 - 1); q.moveTo(gx, wt - u * 0.02); q.lineTo(px, py); }
  q.stroke();
  q.fillStyle = P.dark; q.beginPath(); q.arc(gx, wt, u * 0.09, Math.PI, TAU); q.fill();
  paper(q, poly([[gx - ex, ey], [gx, ay], [gx + ex, ey], [gx + ex - th, ey + th * 0.35], [gx, ay + th * 1.45], [gx - ex + th, ey + th * 0.35]]), P.tile, 1.6);
  q.strokeStyle = 'rgba(0,0,0,.28)'; q.lineWidth = 0.8; q.beginPath();
  for (k = 1; k < 14; k++) { var f2 = k / 14; [-1, 1].forEach(function (sd) { q.moveTo(gx + sd * ex * f2, lerp(ay, ey, f2)); q.lineTo(gx + sd * (ex - th) * f2, lerp(ay + th * 1.45, ey + th * 0.35, f2)); }); }
  q.stroke();
  q.save(); q.lineCap = 'round'; q.strokeStyle = P.board; q.lineWidth = Math.max(1.6, u * 0.055);
  q.beginPath(); q.moveTo(gx - ex - u * 0.03, ey + u * 0.02); q.lineTo(gx, ay); q.lineTo(gx + ex + u * 0.03, ey + u * 0.02); q.stroke();
  q.strokeStyle = P.horn; q.lineWidth = Math.max(0.7, u * 0.012); q.stroke(); q.restore();
  var hl = u * 0.5 * hs, wd = u * 0.13 * hs;
  q.save(); q.shadowColor = 'rgba(0,0,0,.4)'; q.shadowBlur = 3; q.shadowOffsetX = 1; q.shadowOffsetY = 2;
  horn(q, gx - u * 0.02, ay + u * 0.05, 1, hl, wd, P.board, P.horn); horn(q, gx + u * 0.02, ay + u * 0.05, -1, hl, wd, P.board, P.horn);
  q.restore();
  return { apex: [gx, ay], horn: [gx, ay - hl * 0.45], top: ay - hl * 1.05, eave: ey, ex: ex };
}
/* the ham yon, the carved lintel over the bedroom door: a pointed panel with a lotus and scrolls */
function hamyon(q, x, y, w, h, P) {
  paper(q, poly([[x - w / 2, y], [x + w / 2, y], [x + w / 2, y - h * 0.42], [x + w * 0.22, y - h * 0.62], [x, y - h], [x - w * 0.22, y - h * 0.62], [x - w / 2, y - h * 0.42]]), P.board, 0.8);
  q.strokeStyle = P.horn; q.lineWidth = Math.max(0.7, h * 0.07); q.beginPath();
  q.moveTo(x, y - h * 0.12); q.quadraticCurveTo(x - w * 0.12, y - h * 0.45, x, y - h * 0.78); q.quadraticCurveTo(x + w * 0.12, y - h * 0.45, x, y - h * 0.12);
  [-1, 1].forEach(function (sd) { q.moveTo(x + sd * w * 0.1, y - h * 0.2); q.quadraticCurveTo(x + sd * w * 0.38, y - h * 0.5, x + sd * w * 0.3, y - h * 0.18); q.arc(x + sd * w * 0.25, y - h * 0.2, w * 0.05, 0, TAU); });
  q.stroke();
}
/* the house: o = { nt, post, wall, roof, hs (horn scale), twin, toen (−1 | 1), toenW, door, lit } (multiples of u) */
function ruen(q, x, base, w, u, o) {
  var P = teak(o.nt), ph = u * (o.post == null ? 0.7 : o.post), wh = u * (o.wall || 0.72), rh = u * (o.roof || 1.0), fl = base - ph, wt = fl - wh, i, k;
  var R = { fl: fl, wt: wt, x0: x - w * 0.47, x1: x + w * 0.47, horns: [], wins: [], gables: [] };
  if (o.toen) {
    var tw = w * (o.toenW || 0.7), tx0 = o.toen > 0 ? x + w * 0.4 : x - w * 0.4 - tw, tx1 = tx0 + tw, outer = o.toen > 0 ? tx1 : tx0, inner = o.toen > 0 ? tx0 : tx1;
    var tr = wt + wh * 0.12, tl = fl - wh * 0.95;
    if (ph > 0) { q.fillStyle = P.shade; q.fillRect(tx0, fl, tw, ph); }
    for (k = 0; k < 3; k++) paper(q, rect(lerp(inner, outer, 0.4 + k * 0.28) - u * 0.035, tl + u * 0.1, u * 0.07, base - tl - u * 0.1), P.post, 0.8);
    paper(q, rect(tx0, fl - u * 0.05, tw, u * 0.09), P.dark, 1);
    q.strokeStyle = P.dark; q.lineWidth = Math.max(1, u * 0.022); q.beginPath(); q.moveTo(tx0, fl - u * 0.26); q.lineTo(tx1, fl - u * 0.26);
    for (k = 0; k <= 14; k++) { q.moveTo(lerp(tx0, tx1, k / 14), fl - u * 0.26); q.lineTo(lerp(tx0, tx1, k / 14), fl - u * 0.04); } q.stroke();
    paper(q, poly([[inner, tr], [outer + o.toen * u * 0.16, tl], [outer + o.toen * u * 0.16, tl + u * 0.11], [inner, tr + u * 0.13]]), P.tile, 1.4);
    R.toen = { x0: tx0, x1: tx1, fl: fl, roof: tl + u * 0.11 };
    if (ph > u * 0.3) {   /* the steps up to the terrace */
      var sx = outer - o.toen * u * 0.05, sx2 = outer + o.toen * u * 0.42;
      q.strokeStyle = P.post; q.lineWidth = Math.max(1.2, u * 0.03); q.beginPath(); q.moveTo(sx, fl); q.lineTo(sx2, base);
      for (k = 1; k < 5; k++) { var sy = lerp(fl, base, k / 5); q.moveTo(lerp(sx, sx2, k / 5) - o.toen * u * 0.12, sy); q.lineTo(lerp(sx, sx2, k / 5) + o.toen * u * 0.02, sy); } q.stroke();
      R.steps = [sx, sx2];
    }
  }
  if (ph > 0) { q.fillStyle = P.shade; q.fillRect(x - w * 0.42, fl, w * 0.84, ph); }
  var np = o.posts || 4;
  for (i = 0; i < np; i++) { var px = lerp(x - w * 0.4, x + w * 0.4, i / (np - 1));
    if (ph > 0) { paper(q, rect(px - u * 0.045, fl, u * 0.09, ph), P.post, 0.9); q.fillStyle = o.nt ? '#4a4844' : '#a09a8c'; q.fillRect(px - u * 0.075, base - u * 0.06, u * 0.15, u * 0.06); } }
  paper(q, rect(x - w * 0.47, fl - u * 0.06, w * 0.94, u * 0.1), P.dark, 1.2);
  var b0 = w * 0.4, b1 = w * 0.46;
  paper(q, poly([[x - b0, fl - u * 0.04], [x + b0, fl - u * 0.04], [x + b1, wt], [x - b1, wt]]), P.wall, 1.3);
  q.fillStyle = o.nt ? 'rgba(255,220,170,.05)' : 'rgba(255,225,180,.12)';
  for (k = 0; k < 8; k += 2) { var f0 = k / 8, f1 = (k + 1) / 8; q.beginPath(); q.moveTo(lerp(x - b0, x + b0, f0), fl - u * 0.04); q.lineTo(lerp(x - b0, x + b0, f1), fl - u * 0.04); q.lineTo(lerp(x - b1, x + b1, f1), wt); q.lineTo(lerp(x - b1, x + b1, f0), wt); q.closePath(); q.fill(); }
  q.strokeStyle = P.dark; q.lineWidth = Math.max(1, u * 0.02); q.beginPath();
  for (k = 0; k <= 8; k++) { var f = k / 8; q.moveTo(lerp(x - b0, x + b0, f), fl - u * 0.04); q.lineTo(lerp(x - b1, x + b1, f), wt); }
  var my = lerp(fl, wt, 0.42), mw = lerp(b0, b1, 0.42); q.moveTo(x - mw, my); q.lineTo(x + mw, my); q.stroke();
  /* windows, shutters open */
  [-1, 1].forEach(function (sd) {
    if (o.door === false && sd > 0) return;
    var wx = x + sd * w * 0.27, ww = w * 0.11, wy = wt + wh * 0.18, whh = wh * 0.36;
    q.fillStyle = o.nt ? '#120a06' : '#2a1a10'; q.fillRect(wx - ww / 2, wy, ww, whh);
    paper(q, rect(wx - ww / 2 - ww * 0.48, wy, ww * 0.45, whh), P.board, 0.5); paper(q, rect(wx + ww / 2 + ww * 0.03, wy, ww * 0.45, whh), P.board, 0.5);
    R.wins.push([wx - ww / 2, wy, ww, whh]);
  });
  if (o.door) {
    var dw = w * 0.15, dh = wh * 0.64, dy = fl - u * 0.04 - dh;
    q.fillStyle = o.nt ? '#120a06' : '#2a1a10'; q.fillRect(x - dw / 2, dy, dw, dh);
    paper(q, rect(x - dw / 2 - dw * 0.42, dy, dw * 0.4, dh), P.board, 0.5);
    hamyon(q, x, dy, w * 0.22, wh * 0.26, P); R.door = [x, dy + dh / 2, dw, dh]; R.hamyon = [x, dy - wh * 0.1];
    R.wins.push([x - dw / 2, dy, dw, dh]);
  }
  var gs = o.twin ? [[x - w * 0.235, w * 0.53], [x + w * 0.235, w * 0.53]] : [[x, w]];
  gs.forEach(function (g) { var G = gable(q, g[0], g[1], wt, rh * (o.twin ? 0.78 : 1), u, P, o.hs || 1); R.gables.push(G); R.horns.push(G.horn); });
  if (o.twin) paper(q, rect(x - u * 0.06, wt - u * 0.04, u * 0.12, u * 0.14), P.dark, 0.6);
  R.top = Math.min.apply(null, R.gables.map(function (G) { return G.top; }));
  return R;
}
/* the yung khao, the rice granary: stout posts, walls of plank flaring outward, a small high door, a ladder */
function yung(q, x, base, w, u, o) {
  var P = teak(o.nt), ph = u * 0.6, wh = u * 0.62, fl = base - ph, wt = fl - wh, i, k;
  q.fillStyle = P.shade; q.fillRect(x - w * 0.36, fl, w * 0.72, ph);
  for (i = 0; i < 3; i++) { var px = lerp(x - w * 0.32, x + w * 0.32, i / 2); paper(q, rect(px - u * 0.055, fl, u * 0.11, ph), P.post, 0.9); q.fillStyle = o.nt ? '#4a4844' : '#a09a8c'; q.fillRect(px - u * 0.08, base - u * 0.06, u * 0.16, u * 0.06); }
  paper(q, rect(x - w * 0.42, fl - u * 0.06, w * 0.84, u * 0.1), P.dark, 1.2);
  var b0 = w * 0.34, b1 = w * 0.48;
  paper(q, poly([[x - b0, fl - u * 0.04], [x + b0, fl - u * 0.04], [x + b1, wt], [x - b1, wt]]), P.wall, 1.3);
  q.strokeStyle = P.dark; q.lineWidth = Math.max(0.8, u * 0.016); q.beginPath();
  for (k = 1; k < 7; k++) { var yy = lerp(fl - u * 0.04, wt, k / 7), ww = lerp(b0, b1, k / 7); q.moveTo(x - ww, yy); q.lineTo(x + ww, yy); } q.stroke();
  var dx = x + w * 0.08, dy = wt + wh * 0.12, dw = w * 0.2, dh = wh * 0.42;
  q.fillStyle = o.nt ? '#120a06' : '#2a1a10'; q.fillRect(dx - dw / 2, dy, dw, dh);
  var G = gable(q, x, w * 0.98, wt, u * 0.62, u, P, 0.62);
  var lx0 = x + w * 0.62, lx1 = dx + dw * 0.4, ly1 = dy + dh;
  q.strokeStyle = P.post; q.lineWidth = Math.max(1.4, u * 0.03); q.lineCap = 'round'; q.beginPath();
  q.moveTo(lx0, base); q.lineTo(lx1, ly1); q.moveTo(lx0 + u * 0.12, base); q.lineTo(lx1 + u * 0.12, ly1);
  for (k = 1; k < 6; k++) { var f = k / 6; q.moveTo(lerp(lx0, lx1, f), lerp(base, ly1, f)); q.lineTo(lerp(lx0, lx1, f) + u * 0.12, lerp(base, ly1, f)); } q.stroke();
  return { fl: fl, wt: wt, door: [dx, dy + dh * 0.5], sill: [dx, dy + dh], ladder: [lx0, base, lx1, ly1], horn: G.horn, top: G.top, x0: x - b1, x1: x + b1 };
}
/* the water jar (nam ton) on its little roofed stand by the gate, a coconut-shell dipper hung beside */
function hanNam(q, x, base, u, nt) {
  var P = teak(nt), top = base - u * 0.98, sh = base - u * 0.48;
  [x - u * 0.2, x + u * 0.2].forEach(function (px) { paper(q, rect(px - u * 0.03, top + u * 0.1, u * 0.06, base - top - u * 0.1), P.post, 0.8); });
  paper(q, rect(x - u * 0.26, sh, u * 0.52, u * 0.06), P.dark, 0.8);
  paper(q, poly([[x - u * 0.36, top + u * 0.16], [x, top - u * 0.1], [x + u * 0.36, top + u * 0.16], [x + u * 0.3, top + u * 0.21], [x, top - u * 0.02], [x - u * 0.3, top + u * 0.21]]), P.tile, 1);
  q.strokeStyle = P.board; q.lineWidth = Math.max(1.2, u * 0.035); q.lineCap = 'round'; q.beginPath();
  q.moveTo(x, top - u * 0.08); q.quadraticCurveTo(x + u * 0.04, top - u * 0.22, x + u * 0.13, top - u * 0.24); q.moveTo(x, top - u * 0.08); q.quadraticCurveTo(x - u * 0.04, top - u * 0.22, x - u * 0.13, top - u * 0.24); q.stroke();
  var jc = nt ? '#5a2c20' : '#b05a3a';
  paper(q, function (p) { p.beginPath(); p.ellipse(x, sh - u * 0.14, u * 0.15, u * 0.14, 0, 0, TAU); p.rect(x - u * 0.06, sh - u * 0.32, u * 0.12, u * 0.06); }, jc, 0.8);
  q.fillStyle = nt ? '#3a2a20' : '#7a5a3a'; q.beginPath(); q.ellipse(x, sh - u * 0.33, u * 0.09, u * 0.025, 0, 0, TAU); q.fill();
  q.strokeStyle = 'rgba(255,230,190,.35)'; q.lineWidth = 1; q.beginPath(); q.ellipse(x, sh - u * 0.14, u * 0.15, u * 0.04, 0, 0, Math.PI); q.stroke();
  return { jar: [x, sh - u * 0.15], hook: [x + u * 0.2, top + u * 0.3], top: top - u * 0.24 };
}
/* the coconut-shell dipper: a half shell on a stick */
function dipper(c, x, y, a, u, nt) {
  c.save(); c.translate(x, y); c.rotate(a);
  line(c, [[0, 0], [u * 0.22, 0]], nt ? '#6a4a2a' : '#a07a4a', Math.max(1.2, u * 0.025));
  c.fillStyle = nt ? '#3a2416' : '#5a3a1e'; c.beginPath(); c.arc(u * 0.26, 0, u * 0.055, 0, Math.PI); c.closePath(); c.fill(); c.restore();
}
/* a Lanna temple gate (pratu khong): white stucco stepped in tiers, gilt edges, a dark arch */
function khong(q, x, base, w, h, u, nt) {
  var white = nt ? '#8a8478' : '#f1ebdd', gold = nt ? '#b08a3a' : '#e0b04a', k;
  for (k = 0; k < 4; k++) {
    var tw = w * (1 - k * 0.22), ty = base - h * (0.55 + k * 0.15), th = k ? h * 0.15 : h * 0.55;
    paper(q, poly([[x - tw / 2, ty + th], [x - tw / 2, ty + th * 0.15], [x - tw * 0.42, ty], [x + tw * 0.42, ty], [x + tw / 2, ty + th * 0.15], [x + tw / 2, ty + th]]), white, 1.2);
    q.strokeStyle = gold; q.lineWidth = Math.max(1, u * 0.02); q.beginPath(); q.moveTo(x - tw / 2, ty + th * 0.15); q.lineTo(x - tw * 0.42, ty); q.lineTo(x + tw * 0.42, ty); q.lineTo(x + tw / 2, ty + th * 0.15); q.stroke();
  }
  paper(q, poly([[x - w * 0.06, base - h * 1.0], [x, base - h * 1.18], [x + w * 0.06, base - h * 1.0]]), gold, 0.8);
  var aw = w * 0.32; q.fillStyle = nt ? '#140c10' : '#3a2a26'; q.beginPath(); q.moveTo(x - aw / 2, base); q.lineTo(x - aw / 2, base - h * 0.32); q.quadraticCurveTo(x, base - h * 0.56, x + aw / 2, base - h * 0.32); q.lineTo(x + aw / 2, base); q.closePath(); q.fill();
  q.strokeStyle = gold; q.lineWidth = Math.max(1, u * 0.025); q.stroke();
}
/* a temple's roof seen side-on, tiers stepping down, a chofa at each end */
function wihan(q, x, base, w, h, u, nt) {
  var red = nt ? '#5a2018' : '#a8402f', gold = nt ? '#b08a3a' : '#e0b04a', k;
  paper(q, rect(x - w * 0.36, base - h * 0.42, w * 0.72, h * 0.42), nt ? '#8a8478' : '#efe6d4', 1);
  for (k = 0; k < 3; k++) {
    var tw = w * (1 - k * 0.24), ty = base - h * (0.42 + k * 0.2), tt = h * 0.26;
    paper(q, poly([[x - tw / 2, ty], [x - tw * 0.36, ty - tt], [x + tw * 0.36, ty - tt], [x + tw / 2, ty]]), red, 1.2);
    line(q, [[x - tw / 2, ty], [x - tw * 0.36, ty - tt], [x + tw * 0.36, ty - tt], [x + tw / 2, ty]], gold, Math.max(1, u * 0.02));
    [-1, 1].forEach(function (sd) { line(q, [[x + sd * tw * 0.36, ty - tt], [x + sd * tw * 0.4, ty - tt - u * 0.12]], gold, Math.max(1.2, u * 0.03)); });
  }
}
/* a banana plant and a coconut palm, cut flat */
function banana(q, x, base, h, nt) {
  paper(q, rect(x - h * 0.04, base - h * 0.55, h * 0.08, h * 0.55), nt ? '#2a3a22' : '#6a8a4a', 0.8);
  for (var k = 0; k < 6; k++) { var a = -Math.PI / 2 + (k - 2.5) * 0.45, L = h * (0.45 + (k % 2) * 0.1);
    paper(q, function (p) { p.save(); p.translate(x, base - h * 0.55); p.rotate(a + Math.PI / 2); p.beginPath(); p.ellipse(0, -L / 2, h * 0.07, L / 2, 0, 0, TAU); p.restore(); }, nt ? '#1e3a24' : ['#4f8f4a', '#5fa35a', '#3f7f42'][k % 3], 0.8); }
}
function palm(q, x, base, h, nt) {
  q.strokeStyle = nt ? '#3a3024' : '#8a7050'; q.lineWidth = Math.max(2, h * 0.04); q.lineCap = 'round'; q.beginPath(); q.moveTo(x, base); q.quadraticCurveTo(x + h * 0.12, base - h * 0.5, x + h * 0.06, base - h); q.stroke();
  for (var k = 0; k < 7; k++) { var a = k / 7 * TAU, ex = x + h * 0.06 + Math.cos(a) * h * 0.38, ey = base - h + Math.sin(a) * h * 0.14 + h * 0.12;
    paper(q, function (p) { p.beginPath(); p.moveTo(x + h * 0.06, base - h); p.quadraticCurveTo((x + h * 0.06 + ex) / 2, base - h - h * 0.14, ex, ey); p.quadraticCurveTo((x + h * 0.06 + ex) / 2, base - h - h * 0.04, x + h * 0.06, base - h + h * 0.03); p.closePath(); }, nt ? '#1e3a24' : '#4f8f4a', 0.6); }
}
function bushTree(q, x, base, h, nt, seed, col) {
  var r = rnd(seed);
  paper(q, rect(x - h * 0.05, base - h * 0.55, h * 0.1, h * 0.55), nt ? '#2a2018' : '#6a4a2a', 0.8);
  for (var k = 0; k < 7; k++) { var bx = x + (r() - 0.5) * h * 0.7, by = base - h * (0.6 + r() * 0.4), br = h * (0.18 + r() * 0.12);
    paper(q, function (p) { K.circ(p, bx, by, br, k + 3); }, nt ? '#1c3424' : col || ['#3f7f42', '#4f8f4a', '#5f9a52'][k % 3], 0.8); }
}

/* ================================================================ 1. 'alley' — market lanes
   Shophouses behind, stalls before them, tarps and umbrellas overlapping overhead, the power
   pole's tangle of cable, goods hung from the tarps swinging as pendulums, and the lane full:
   walkers x = x₀ ± vt, a porter's cart, a motorbike squeezing through. */
var ALLEY = ['kadluang', 'muangmai', 'nightlane', 'spice', 'bazaar'];
var ASIGN = { kadluang: ['กาดหลวง', 'ร้านทอง', 'ผ้าเมือง', 'น้ำพริกหนุ่ม', 'ไส้อั่ว', 'แคบหมู'], muangmai: ['ตลาดเมืองใหม่', 'ลำไย', 'ลิ้นจี่', 'ผักสด', 'ขายส่ง', 'พริก'],
  nightlane: ['ตลาดกลางคืน', 'ข้าวซอย', 'ผัดไทย', 'หมูปิ้ง', 'ชาไข่มุก', 'ข้าวเหนียว'], spice: ['เครื่องเทศ', 'ของแห้ง', 'ยาจีน', 'ใบชา', 'โอสถ', 'สมุนไพร'],
  bazaar: ['ไนท์บาซาร์', 'เชียงราย', 'ผ้าทอ', 'เครื่องเงิน', 'ขันโตก', 'กาแฟดอย'] };
var AVERT = { kadluang: ['金行', '福'], muangmai: ['批發', '果'], nightlane: ['夜市', '麵'], spice: ['藥材', '香料', '茶'], bazaar: ['夜市', '銀'] };
var ATARP = { kadluang: ['#2f6fb5', '#e0773a', '#d9342b', '#3f9a6a', '#f2c94c', '#2f6fb5'], muangmai: ['#2f6fb5', '#3a8ac9', '#e8e2d0', '#2f6fb5', '#5aa0d8'],
  nightlane: ['#7a1f3a', '#2a3a6a', '#d9342b', '#e2b33c', '#1f5a4a'], spice: ['#b8322a', '#e8b84a', '#7a1f1a', '#d9342b'], bazaar: ['#5a2a6a', '#1f5a4a', '#b8322a', '#e8b84a', '#2a3a6a'] };
var AHANG = { kadluang: ['garland', 'sausage', 'basket', 'sandals', 'bag', 'chili', 'trap'], muangmai: ['scale', 'banana', 'bagbundle', 'scale', 'banana'],
  nightlane: ['lanternR', 'balloon', 'khom', 'lanternR'], spice: ['lanternR', 'garlic', 'chili', 'kunchiang', 'lanternR'], bazaar: ['tribebag', 'khom', 'tribebag', 'khom', 'garland'] };
var FACADE = ['#e8d8b0', '#cfd8c0', '#e6c8b4', '#c8d4dc', '#ead08e', '#d8bca4', '#b8d0c0'];

function alleyPlan(S, lk) {
  var u = S.hh, r = rnd(S.seed + 17), L = { lk: lk, back: S.deck - u * 0.32, houses: [], stalls: [], hang: [] }, x = S.x0 - u * 0.3;
  while (x < S.x1 + u * 0.2) {
    var w = u * (1.25 + r() * 0.45), top = cap(S, x, x + w), st = Math.max(1, Math.min(r() < 0.4 ? 4 : 3, Math.floor((L.back - top - u * 0.15) / (u * 0.78))));
    L.houses.push({ x0: x, x1: x + w, st: st, col: FACADE[Math.floor(r() * FACADE.length)], sign: ASIGN[lk][L.houses.length % ASIGN[lk].length], vert: r() < 0.45, k: r() });
    x += w;
  }
  var n = Math.max(3, Math.round(S.span / (u * (S.phone ? 1.35 : 1.25)))), sw = S.span / n;
  for (var i = 0; i < n; i++) {
    var a0 = S.x0 + i * sw + sw * 0.03, a1 = a0 + sw * 0.94, ty = S.deck - u * (2.0 + r() * 0.22);
    ty = Math.max(ty, cap(S, a0 - u * 0.3, a1 + u * 0.3) + u * 0.04);
    L.stalls.push({ a0: a0, a1: a1, ty: ty, tilt: (r() - 0.5) * u * 0.25, col: ATARP[lk][(i + S.seed) % ATARP[lk].length], stripe: r() < 0.35, umb: r() < 0.25 && lk !== 'muangmai', k: r() });
    var kinds = AHANG[lk], m = 2 + Math.floor(r() * 2);
    for (var j = 0; j < m; j++) L.hang.push({ x: lerp(a0 + sw * 0.12, a1 - sw * 0.12, m > 1 ? j / (m - 1) : 0.5), y: ty + u * 0.16 + (r() - 0.5) * u * 0.06, kind: kinds[Math.floor(r() * kinds.length)], len: 0.4 + r() * 0.5, ph: r() * TAU, col: CLOTH[Math.floor(r() * CLOTH.length)] });
  }
  L.pole = S.x0 + S.span * (S.phone ? 0.08 : 0.06);
  return L;
}
/* the back: shophouses with shutters, balconies and signs, the stalls' tables and goods, tarps over all */
function alleyBack(q, S, L) {
  var u = S.hh, nt = S.night, lk = L.lk, deck = S.deck, r = rnd(S.seed + 3), k;
  K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#2a2624' : '#8f887a');
  q.fillStyle = nt ? 'rgba(255,210,140,.06)' : 'rgba(255,255,255,.1)'; for (k = 0; k < 9; k++) { var px = S.x0 + r() * S.span; q.beginPath(); q.ellipse(px, deck + u * (0.2 + r() * 0.45), u * (0.2 + r() * 0.4), u * 0.04, 0, 0, TAU); q.fill(); }
  paper(q, rect(S.x0 - 4, L.back, S.span + 8, deck - L.back + 2), nt ? '#3a3430' : '#a8a090', 0.6);
  /* shophouses */
  L.houses.forEach(function (H, hi) {
    var w = H.x1 - H.x0, sh = u * 0.78, top = L.back - u * 0.15 - H.st * sh, col = nt ? dim(H.col, 0.38) : H.col;
    paper(q, rect(H.x0, top, w, L.back - top), col, 1.2);
    paper(q, rect(H.x0 - u * 0.03, top - u * 0.08, w + u * 0.06, u * 0.1), nt ? '#2a2628' : dim(H.col, 0.75, [90, 80, 70]), 0.8);
    q.fillStyle = nt ? '#120c0a' : '#3a2a20'; q.fillRect(H.x0 + w * 0.08, L.back - u * 0.95, w * 0.84, u * 0.95);
    q.strokeStyle = nt ? '#2a201a' : '#6a5038'; q.lineWidth = 1; q.beginPath(); for (k = 1; k < 4; k++) { q.moveTo(H.x0 + w * 0.08, L.back - u * 0.95 * k / 4); q.lineTo(H.x0 + w * 0.92, L.back - u * 0.95 * k / 4); } q.stroke();
    for (k = 0; k < 12; k++) { q.fillStyle = CLOTH[Math.floor(r() * CLOTH.length)]; q.globalAlpha = nt ? 0.35 : 0.7; q.fillRect(H.x0 + w * (0.1 + r() * 0.75), L.back - u * (0.2 + Math.floor(r() * 3) * 0.24), u * 0.06, u * 0.12); } q.globalAlpha = 1;
    for (var s = 1; s < H.st + (H.st > 1 ? 0 : 1); s++) {
      var fy = L.back - u * 0.15 - s * sh;
      if (s === 1 && H.k > 0.5) { q.strokeStyle = nt ? '#1a1a1a' : '#3a3a3a'; q.lineWidth = 1; q.beginPath(); q.moveTo(H.x0 + w * 0.05, fy + sh * 0.62); q.lineTo(H.x1 - w * 0.05, fy + sh * 0.62); for (k = 0; k <= 12; k++) { q.moveTo(H.x0 + w * (0.05 + k * 0.075), fy + sh * 0.62); q.lineTo(H.x0 + w * (0.05 + k * 0.075), fy + sh * 0.9); } q.stroke(); }
      [0.28, 0.72].forEach(function (f, wi) {
        var wx = H.x0 + w * f, ww = w * 0.24, wy = fy + sh * 0.18, wh = sh * 0.5, sc = ['#4f7a5a', '#3a6a8a', '#8a4a3a', '#5a5a7a'][(hi + s) % 4];
        q.fillStyle = nt ? (h2(hi, s * 2 + wi, S.seed) < 0.5 ? '#ffd890' : '#141018') : '#2a2420'; q.fillRect(wx - ww / 2, wy, ww, wh);
        if (!nt) { q.fillStyle = 'rgba(255,255,255,.12)'; q.fillRect(wx - ww / 2, wy, ww * 0.4, wh); }
        q.fillStyle = nt ? dim(sc, 0.4) : sc; q.fillRect(wx - ww / 2 - ww * 0.32, wy, ww * 0.3, wh); q.fillRect(wx + ww / 2 + ww * 0.02, wy, ww * 0.3, wh);
      });
      if ((hi + s) % 3 === 0) { paper(q, rect(H.x0 + w * 0.62, fy + sh * 0.74, u * 0.26, u * 0.16), nt ? '#5a5a60' : '#d8d8d0', 0.6); q.strokeStyle = 'rgba(0,0,0,.35)'; q.beginPath(); q.arc(H.x0 + w * 0.62 + u * 0.13, fy + sh * 0.82, u * 0.05, 0, TAU); q.stroke(); }
      if ((hi + s) % 2 === 1) { q.fillStyle = nt ? '#1e3a24' : '#4f8f4a'; for (k = 0; k < 4; k++) { q.beginPath(); q.arc(H.x0 + w * (0.15 + k * 0.04), fy + sh * 0.6 - (k % 2) * u * 0.05, u * 0.06, 0, TAU); q.fill(); } if (lk === 'kadluang') { q.fillStyle = '#e5567f'; q.beginPath(); q.arc(H.x0 + w * 0.2, fy + sh * 0.55, u * 0.03, 0, TAU); q.fill(); } }
    }
    /* the shop's board over its door, and a tall one hung on the pier */
    var bw = w * 0.84, by = L.back - u * 1.2;
    paper(q, rect(H.x0 + w * 0.08, by, bw, u * 0.24), nt ? '#5a1a14' : ['#b8322a', '#1f5a8a', '#e8b84a', '#2f6a3a'][hi % 4], 0.8);
    q.fillStyle = hi % 4 === 2 ? '#5a1a10' : '#ffe8b0'; q.font = '800 ' + Math.round(u * 0.15) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle';
    q.fillText(H.sign, H.x0 + w * 0.5, by + u * 0.125, bw - 6);
    if (H.vert && H.st > 1) {
      var vx = H.x1 - w * 0.06, vt = AVERT[lk][hi % AVERT[lk].length], vh = Math.min(u * 1.1, vt.length * u * 0.24 + u * 0.12);
      paper(q, rect(vx - u * 0.12, L.back - u * 1.35 - vh, u * 0.24, vh), nt ? '#6a1a14' : '#c0392b', 0.8);
      q.fillStyle = '#f2c94c'; q.font = '700 ' + Math.round(u * 0.17) + 'px "Noto Sans TC","PingFang TC",system-ui,sans-serif';
      for (k = 0; k < vt.length; k++) q.fillText(vt[k], vx, L.back - u * 1.35 - vh + u * 0.16 + k * u * 0.24);
    }
  });
  /* the power pole and its tangle of cable */
  var px = L.pole, ptop = Math.max(cap(S, px - 4, px + 4), deck - u * 3.4);
  paper(q, rect(px - u * 0.06, ptop, u * 0.12, deck - ptop + u * 0.1), nt ? '#5a5a5c' : '#b8b4aa', 1);
  paper(q, rect(px - u * 0.35, ptop + u * 0.15, u * 0.7, u * 0.06), nt ? '#4a4a4c' : '#8a867c', 0.6);
  paper(q, rect(px + u * 0.08, ptop + u * 0.3, u * 0.2, u * 0.32), nt ? '#4a4a50' : '#9a9aa0', 0.8);
  q.strokeStyle = 'rgba(20,18,20,.85)'; q.lineWidth = 1;
  for (k = 0; k < 9; k++) {
    var xl = S.avoid ? S.avoid.cx - S.avoid.r - 6 : S.W * (S.phone ? 0.6 : 0.76), ex = Math.min(xl, S.x0 + S.span * (0.25 + r() * 0.8)), ey = Math.max(cap(S, ex - 2, ex + 2), deck - u * (2.2 + r() * 1.2)), sx = px + (r() - 0.5) * u * 0.6, sy = ptop + u * (0.15 + r() * 0.2);
    var mx = (sx + ex) / 2, sag = u * (0.15 + r() * 0.4); q.beginPath(); q.moveTo(sx, sy); q.quadraticCurveTo(mx, Math.max(sy, ey) + sag, ex, ey); q.stroke();
  }
  for (k = 0; k < 5; k++) { q.beginPath(); q.ellipse(px + u * (0.15 + k * 0.05), ptop + u * (0.75 + k * 0.08), u * (0.12 + k * 0.03), u * 0.06, 0.2 * k, 0, TAU); q.stroke(); }
  /* stalls: a table each, its goods, the tarp over it */
  L.stalls.forEach(function (T, i) {
    var a0 = T.a0, a1 = T.a1, w = a1 - a0, ty = deck - u * 0.48;
    paper(q, rect(a0 + 2, T.ty + u * 0.1, u * 0.05, deck - T.ty), nt ? '#3a3430' : '#6a6050', 0.6); paper(q, rect(a1 - u * 0.07, T.ty + u * 0.1, u * 0.05, deck - T.ty), nt ? '#3a3430' : '#6a6050', 0.6);
    paper(q, rect(a0, ty, w, u * 0.06), nt ? '#4a3a2a' : '#9a7a52', 0.8);
    paper(q, rect(a0 + u * 0.05, ty + u * 0.06, w - u * 0.1, u * 0.34), nt ? '#2a2430' : ['#7a1f3a', '#2a3a6a', '#1f5a4a', '#5a4a3a'][i % 4], 0.6);
    goods(q, S, lk, a0, a1, ty, T, r);
  });
  L.stalls.forEach(function (T, i) {
    var a0 = T.a0 - u * 0.22, a1 = T.a1 + u * 0.22, y0 = T.ty - T.tilt, y1 = T.ty + T.tilt, col = nt ? dim(T.col, 0.42) : T.col;
    if (T.umb) {
      var ux = (T.a0 + T.a1) / 2, R = (a1 - a0) * 0.58, uy = T.ty + u * 0.05;
      paper(q, function (p) { p.beginPath(); p.moveTo(ux - R, uy + u * 0.1); p.quadraticCurveTo(ux, uy - u * 0.42, ux + R, uy + u * 0.1); for (var b = 6; b > 0; b--) p.quadraticCurveTo(ux - R + (b - 0.5) * R / 3, uy + u * 0.2, ux - R + (b - 1) * R / 3, uy + u * 0.1); p.closePath(); }, col, 1.2);
      q.strokeStyle = 'rgba(255,255,255,.25)'; q.lineWidth = 1; for (k = 1; k < 6; k++) { q.beginPath(); q.moveTo(ux, uy - u * 0.16); q.lineTo(ux - R + k * R / 3, uy + u * 0.12); q.stroke(); }
      return;
    }
    paper(q, function (p) { p.beginPath(); p.moveTo(a0, y0); p.lineTo(a1, y1); var n = 6, sc = (a1 - a0) / n; for (var b = n; b > 0; b--) { var bx = a0 + (b - 0.5) * sc; p.quadraticCurveTo(bx, lerp(y0, y1, (b - 0.5) / n) + u * 0.2, a0 + (b - 1) * sc, lerp(y0, y1, (b - 1) / n) + u * 0.12); } p.closePath(); }, col, 1.3);
    if (T.stripe) { q.save(); q.beginPath(); q.moveTo(a0, y0); q.lineTo(a1, y1); q.lineTo(a1, y1 + u * 0.2); q.lineTo(a0, y0 + u * 0.2); q.closePath(); q.clip(); q.fillStyle = 'rgba(255,255,255,.55)'; for (var sx2 = a0; sx2 < a1; sx2 += u * 0.2) q.fillRect(sx2, Math.min(y0, y1) - 2, u * 0.1, u * 0.5); q.restore(); }
    q.strokeStyle = 'rgba(0,0,0,.25)'; q.lineWidth = 1; q.beginPath(); q.moveTo(a0, y0 + u * 0.03); q.lineTo(a1, y1 + u * 0.03); q.stroke();
  });
}
/* goods on a table, by the lane's kind */
function goods(q, S, lk, a0, a1, ty, T, r) {
  var u = S.hh, nt = S.night, w = a1 - a0, k, j, kind = Math.floor(T.k * 4);
  function pile(cx, cy, rr, col, n, sz) { q.fillStyle = nt ? 'rgba(20,20,30,.5)' : 'rgba(0,0,0,.2)'; q.beginPath(); q.ellipse(cx, cy, rr, rr * 0.3, 0, 0, TAU); q.fill();
    for (var m = 0; m < n; m++) { var a = r() * Math.PI, d = Math.sqrt(r()) * rr; dot(q, cx + Math.cos(a) * d, cy - Math.sin(a) * d * 0.55 - sz * 0.3, sz, nt ? dim(col, 0.5) : col); } }
  function basket(cx, cy, rr) { paper(q, function (p) { p.beginPath(); p.moveTo(cx - rr, cy - rr * 0.35); p.lineTo(cx + rr, cy - rr * 0.35); p.lineTo(cx + rr * 0.75, cy); p.lineTo(cx - rr * 0.75, cy); p.closePath(); }, nt ? '#5a4a30' : '#c8a060', 0.5);
    q.strokeStyle = 'rgba(80,50,20,.45)'; q.lineWidth = 0.8; q.beginPath(); for (var m = -3; m <= 3; m++) { q.moveTo(cx + m * rr * 0.25, cy - rr * 0.35); q.lineTo(cx + m * rr * 0.2, cy); } q.stroke(); }
  if (lk === 'muangmai') {
    for (j = 0; j < 2; j++) for (k = 0; k < 3; k++) {
      var cx = a0 + w * (0.2 + k * 0.3), cy = ty - j * u * 0.26, cw = w * 0.27, ch = u * 0.24, fruit = (k + j + kind) % 3;
      paper(q, rect(cx - cw / 2, cy - ch, cw, ch), nt ? '#4a3a24' : '#b8925a', 0.6);
      q.strokeStyle = 'rgba(60,40,20,.5)'; q.lineWidth = 1; q.beginPath(); q.moveTo(cx - cw / 2, cy - ch * 0.5); q.lineTo(cx + cw / 2, cy - ch * 0.5); q.stroke();
      if (j === 1) pile(cx, cy - ch, cw * 0.42, ['#d9342b', '#c9a46a', '#e8c040'][fruit], 18, u * 0.035);
    }
    return;
  }
  if (lk === 'spice') {
    for (k = 0; k < 4; k++) {
      var sx = a0 + w * (0.14 + k * 0.24), sr = w * 0.12, col = ['#c0392b', '#5a3a22', '#8a6a3a', '#e8dcc0', '#e07a3a', '#3a2a1a'][(k + kind) % 6];
      paper(q, function (p) { p.beginPath(); p.moveTo(sx - sr, ty); p.lineTo(sx - sr * 1.05, ty - u * 0.3); p.quadraticCurveTo(sx, ty - u * 0.36, sx + sr * 1.05, ty - u * 0.3); p.lineTo(sx + sr, ty); p.closePath(); }, nt ? '#6a5a40' : '#e0d0a8', 0.6);
      pile(sx, ty - u * 0.3, sr * 0.95, col, 16, u * 0.032);
      if ((k + kind) % 6 === 1) for (j = 0; j < 4; j++) { var stx = sx + (j - 1.5) * sr * 0.4, sty = ty - u * 0.36; q.fillStyle = nt ? '#3a2410' : '#6a3a1a'; q.beginPath(); for (var a = 0; a < 8; a++) { var rr = a % 2 ? u * 0.012 : u * 0.035; q.lineTo(stx + Math.cos(a / 8 * TAU) * rr, sty + Math.sin(a / 8 * TAU) * rr); } q.closePath(); q.fill(); }
    }
    return;
  }
  if (lk === 'nightlane') {
    paper(q, rect(a0 + w * 0.1, ty - u * 0.36, w * 0.5, u * 0.32), nt ? 'rgba(200,230,255,.35)' : 'rgba(220,240,255,.55)', 0.5);
    for (k = 0; k < 5; k++) { q.fillStyle = ['#e0773a', '#f7e08a', '#c0392b', '#7fe0a4', '#f08a5d'][(k + kind) % 5]; q.fillRect(a0 + w * (0.13 + k * 0.09), ty - u * 0.14, w * 0.07, u * 0.08); }
    for (k = 0; k < 5; k++) { line(q, [[a0 + w * (0.15 + k * 0.08), ty - u * 0.2], [a0 + w * (0.17 + k * 0.08), ty - u * 0.32]], '#d9b36a', 1.2); dot(q, a0 + w * (0.165 + k * 0.08), ty - u * 0.27, u * 0.025, '#a8432f'); }
    return;
  }
  if (lk === 'bazaar') {
    paper(q, rect(a0 + w * 0.08, ty - u * 0.05, w * 0.84, u * 0.05), nt ? '#1a1418' : '#2a2026', 0.4);
    for (k = 0; k < 7; k++) { q.strokeStyle = '#d8dce4'; q.lineWidth = 1.2; q.beginPath(); q.arc(a0 + w * (0.14 + k * 0.12), ty - u * 0.1, u * 0.04, 0, TAU); q.stroke(); }
    for (k = 0; k < 3; k++) basket(a0 + w * (0.2 + k * 0.3), ty - u * 0.12, w * 0.1);
    return;
  }
  /* Kad Luang: baskets of chilli, garlic, shallots, limes; sai ua coiled on a tray; cap moo bags */
  for (k = 0; k < 3; k++) { var bx = a0 + w * (0.18 + k * 0.3), br = w * 0.13; basket(bx, ty, br); pile(bx, ty - br * 0.35, br * 0.9, ['#d9342b', '#efe6d0', '#8a3a6a', '#6aa84a', '#e8a040'][(k + kind) % 5], 14, u * 0.035); }
  if (kind % 2) { var cx2 = a0 + w * 0.5, cy2 = ty - u * 0.04; q.strokeStyle = nt ? '#5a2a1a' : '#9a3a22'; q.lineWidth = u * 0.05; q.beginPath(); for (var a2 = 0; a2 < 5 * TAU; a2 += 0.3) { var rr2 = u * 0.02 + a2 * u * 0.006; q.lineTo(cx2 + Math.cos(a2) * rr2 * 1.6, cy2 - u * 0.05 + Math.sin(a2) * rr2 * 0.4); } q.stroke(); }
}
/* a hung thing, drawn about its hook (0, 0) hanging down */
function hangItem(c, it, s, nt) {
  var k, len = it.len * s;
  switch (it.kind) {
    case 'garland': line(c, [[0, 0], [0, len * 0.2]], '#3a2a1a', 1); for (k = 0; k < 9; k++) dot(c, Math.sin(k * 0.7) * s * 0.03, len * 0.2 + k * s * 0.07, s * 0.05, nt ? (k % 2 ? '#a8601a' : '#a88a1a') : (k % 2 ? '#f08a1a' : '#f2c94c')); dot(c, 0, len * 0.2 + s * 0.68, s * 0.035, '#d9342b'); line(c, [[0, len * 0.2 + s * 0.7], [0, len * 0.2 + s * 0.85]], '#d9342b', 2); break;
    case 'sausage': line(c, [[0, 0], [0, len * 0.15]], '#3a2a1a', 1); c.fillStyle = nt ? '#5a2416' : '#9a3a22'; for (k = 0; k < 4; k++) { c.beginPath(); c.ellipse(0, len * 0.15 + s * (0.09 + k * 0.17), s * 0.045, s * 0.085, 0, 0, TAU); c.fill(); } break;
    case 'basket': line(c, [[0, 0], [0, len * 0.3]], '#3a2a1a', 1); c.fillStyle = nt ? '#6a5430' : '#d4aa60'; c.beginPath(); c.ellipse(0, len * 0.3 + s * 0.16, s * 0.12, s * 0.15, 0, 0, TAU); c.fill(); c.fillStyle = nt ? '#4a3a20' : '#a8803a'; c.fillRect(-s * 0.1, len * 0.3, s * 0.2, s * 0.04); c.strokeStyle = 'rgba(80,50,20,.5)'; c.lineWidth = 0.8; for (k = 0; k < 3; k++) { c.beginPath(); c.moveTo(-s * 0.11, len * 0.3 + s * (0.1 + k * 0.07)); c.lineTo(s * 0.11, len * 0.3 + s * (0.1 + k * 0.07)); c.stroke(); } break;
    case 'trap': line(c, [[0, 0], [0, len * 0.2]], '#3a2a1a', 1); flat(c, [[-s * 0.05, len * 0.2], [s * 0.05, len * 0.2], [s * 0.14, len * 0.2 + s * 0.45], [-s * 0.14, len * 0.2 + s * 0.45]], nt ? '#6a5430' : '#d4aa60'); c.strokeStyle = 'rgba(80,50,20,.55)'; c.lineWidth = 0.8; for (k = 1; k < 5; k++) { var yy = len * 0.2 + s * 0.09 * k; c.beginPath(); c.moveTo(-s * (0.05 + k * 0.018), yy); c.lineTo(s * (0.05 + k * 0.018), yy); c.stroke(); } break;
    case 'sandals': line(c, [[0, 0], [0, len * 0.25]], '#3a2a1a', 1); [-1, 1].forEach(function (sd) { c.fillStyle = nt ? dim(it.col, 0.45) : it.col; c.beginPath(); c.ellipse(sd * s * 0.06, len * 0.25 + s * 0.16, s * 0.05, s * 0.15, sd * 0.1, 0, TAU); c.fill(); }); break;
    case 'bag': line(c, [[0, 0], [0, len * 0.15]], '#3a2a1a', 1); c.fillStyle = nt ? 'rgba(200,190,170,.4)' : 'rgba(240,235,220,.75)'; c.fillRect(-s * 0.15, len * 0.15, s * 0.3, s * 0.42); c.fillStyle = nt ? '#8a6a30' : '#e0b05a'; for (k = 0; k < 7; k++) { c.beginPath(); c.arc(-s * 0.09 + (k % 3) * s * 0.09, len * 0.15 + s * (0.1 + Math.floor(k / 3) * 0.12), s * 0.04, 0, TAU); c.fill(); } break;
    case 'chili': line(c, [[0, 0], [0, len * 0.1 + s * 0.6]], '#3a2a1a', 1); c.fillStyle = nt ? '#6a1a12' : '#c8261c'; for (k = 0; k < 7; k++) { var cy = len * 0.1 + k * s * 0.085, sd2 = k % 2 ? 1 : -1; c.beginPath(); c.moveTo(0, cy); c.lineTo(sd2 * s * 0.13, cy + s * 0.05); c.lineTo(0, cy + s * 0.04); c.closePath(); c.fill(); } break;
    case 'garlic': line(c, [[0, 0], [0, len * 0.1]], '#3a2a1a', 1); for (k = 0; k < 6; k++) dot(c, (k % 2 ? 1 : -1) * s * 0.04, len * 0.1 + s * (0.06 + k * 0.08), s * 0.06, nt ? '#8a8478' : '#f2ead8'); break;
    case 'kunchiang': line(c, [[0, 0], [0, len * 0.1]], '#3a2a1a', 1); c.fillStyle = nt ? '#5a1414' : '#a81c1c'; for (k = 0; k < 4; k++) [-1, 1].forEach(function (sd) { c.beginPath(); c.ellipse(sd * s * 0.05, len * 0.1 + s * (0.1 + k * 0.15), s * 0.03, s * 0.07, 0, 0, TAU); c.fill(); }); break;
    case 'lanternR': line(c, [[0, 0], [0, len * 0.2]], '#3a2a1a', 1); c.fillStyle = nt ? '#e04a2a' : '#d9342b'; c.beginPath(); c.ellipse(0, len * 0.2 + s * 0.2, s * 0.18, s * 0.17, 0, 0, TAU); c.fill(); c.fillStyle = '#e8b84a'; c.fillRect(-s * 0.08, len * 0.2 + s * 0.02, s * 0.16, s * 0.03); c.fillRect(-s * 0.08, len * 0.2 + s * 0.35, s * 0.16, s * 0.03); line(c, [[0, len * 0.2 + s * 0.38], [0, len * 0.2 + s * 0.55]], '#e8b84a', 2); break;
    case 'khom': line(c, [[0, 0], [0, len * 0.15]], '#3a2a1a', 1); var ky = len * 0.15 + s * 0.2; c.fillStyle = nt ? '#ffd890' : it.col; c.beginPath(); for (k = 0; k < 10; k++) { var rr = k % 2 ? s * 0.08 : s * 0.19, a = k / 10 * TAU - Math.PI / 2; c.lineTo(Math.cos(a) * rr, ky + Math.sin(a) * rr); } c.closePath(); c.fill(); c.strokeStyle = nt ? '#ffeec0' : '#f2e6c9'; c.lineWidth = 1; for (k = -2; k <= 2; k++) { c.beginPath(); c.moveTo(k * s * 0.04, ky + s * 0.15); c.lineTo(k * s * 0.05, ky + s * 0.42); c.stroke(); } break;
    case 'balloon': line(c, [[0, 0], [0, s * 0.3]], '#ddd', 0.8); dot(c, 0, -s * 0.05, s * 0.12, nt ? dim(it.col, 0.6) : it.col); break;
    case 'tribebag': line(c, [[-s * 0.08, len * 0.2], [0, 0], [s * 0.08, len * 0.2]], it.col, 1.4); c.fillStyle = nt ? '#2a1a26' : '#1d1b2a'; c.fillRect(-s * 0.12, len * 0.2, s * 0.24, s * 0.3); ['#d9342b', '#f2c94c', '#3fb6b0', '#f2f2f2'].forEach(function (cc, i) { c.fillStyle = nt ? dim(cc, 0.5) : cc; c.fillRect(-s * 0.12, len * 0.2 + s * (0.05 + i * 0.06), s * 0.24, s * 0.03); }); c.fillStyle = '#d9342b'; for (k = 0; k < 4; k++) c.fillRect(-s * 0.11 + k * s * 0.07, len * 0.2 + s * 0.3, s * 0.025, s * 0.08); break;
    case 'scale': line(c, [[0, 0], [0, s * 0.2]], '#3a2a1a', 1); c.fillStyle = nt ? '#6a6a70' : '#c8c8cc'; c.beginPath(); c.arc(0, s * 0.3, s * 0.12, 0, TAU); c.fill(); c.fillStyle = '#fff'; c.beginPath(); c.arc(0, s * 0.3, s * 0.08, 0, TAU); c.fill(); line(c, [[0, s * 0.3], [s * 0.05, s * 0.25]], '#c0392b', 1); line(c, [[-s * 0.16, s * 0.65], [0, s * 0.42], [s * 0.16, s * 0.65]], '#5a5a5a', 1); flat(c, [[-s * 0.2, s * 0.65], [s * 0.2, s * 0.65], [s * 0.14, s * 0.73], [-s * 0.14, s * 0.73]], nt ? '#4a4a50' : '#9a9aa4'); break;
    case 'banana': line(c, [[0, 0], [0, s * 0.2]], '#3a2a1a', 1.4); c.fillStyle = nt ? '#6a6a2a' : '#e8d040'; for (k = 0; k < 6; k++) { var by = s * (0.22 + Math.floor(k / 2) * 0.12), sd3 = k % 2 ? 1 : -1; c.beginPath(); c.ellipse(sd3 * s * 0.07, by, s * 0.03, s * 0.1, sd3 * 0.5, 0, TAU); c.fill(); } break;
    case 'bagbundle': line(c, [[0, 0], [0, s * 0.15]], '#3a2a1a', 1); for (k = 0; k < 3; k++) { c.fillStyle = nt ? dim(['#e5567f', '#4d8fd1', '#f2f2f2'][k], 0.5) : ['#e5567f', '#4d8fd1', '#f2f2f2'][k]; c.fillRect(-s * 0.12 + k * s * 0.08, s * 0.15, s * 0.08, s * 0.32); } break;
  }
}
/* a step-through motorbike, side-on; wheels turn with distance, φ = x/r */
function moto(c, x, y, s, dir, col, nt, roll) {
  var r = s * 0.13, i;
  [x - dir * s * 0.3, x + dir * s * 0.3].forEach(function (wx) {
    dot(c, wx, y - r, r, '#1b1a20'); dot(c, wx, y - r, r * 0.5, '#9a9aa4');
    c.strokeStyle = '#1b1a20'; c.lineWidth = 1; c.beginPath(); for (i = 0; i < 3; i++) { var a = roll + i * TAU / 3; c.moveTo(wx, y - r); c.lineTo(wx + Math.cos(a) * r * 0.5, y - r + Math.sin(a) * r * 0.5); } c.stroke();
  });
  var X = function (f) { return x + dir * s * f; };
  flat(c, [[X(-0.42), y - r * 1.5], [X(-0.38), y - s * 0.36], [X(-0.04), y - s * 0.38], [X(0.04), y - r * 1.4], [X(0.18), y - r * 1.4], [X(0.24), y - s * 0.56], [X(0.33), y - s * 0.56], [X(0.37), y - r * 1.5], [X(0.27), y - r * 0.9], [X(-0.3), y - r * 0.9]], nt ? dim(col, 0.5) : col);
  flat(c, [[X(-0.36), y - s * 0.36], [X(-0.06), y - s * 0.38], [X(-0.04), y - s * 0.43], [X(-0.33), y - s * 0.42]], '#1b1a20');
  line(c, [[X(0.3), y - s * 0.56], [X(0.25), y - s * 0.64], [X(0.18), y - s * 0.65]], '#2a2a30', 2);
  dot(c, X(0.36), y - s * 0.5, s * 0.03, nt ? '#fff6c0' : '#f2f2e0');
  if (nt) glow(c, X(0.45), y - s * 0.48, s * 0.3, 50, 0.6);
  return { seat: [X(-0.2), y - s * 0.42], bar: [X(0.18), y - s * 0.65] };
}
/* a hand cart, a big wheel under its bed, sacks or crates on it */
function cart(c, x, y, s, dir, load, nt, roll) {
  var r = s * 0.17, X = function (f) { return x + dir * s * f; };
  if (load === 'crates') for (var k = 0; k < 3; k++) { flat(c, [[X(-0.36 + k * 0.25), y - r * 1.6 - s * 0.24], [X(-0.14 + k * 0.25), y - r * 1.6 - s * 0.24], [X(-0.14 + k * 0.25), y - r * 1.6], [X(-0.36 + k * 0.25), y - r * 1.6]], nt ? '#5a4a30' : '#b8925a'); for (var m = 0; m < 4; m++) dot(c, X(-0.32 + k * 0.25 + m * 0.05), y - r * 1.6 - s * 0.26, s * 0.025, nt ? '#6a1a12' : '#d9342b'); }
  else for (k = 0; k < 4; k++) { c.fillStyle = nt ? '#6a6050' : '#e8dcc0'; c.beginPath(); c.ellipse(X(-0.25 + (k % 3) * 0.2), y - r * 1.6 - s * (0.08 + Math.floor(k / 3) * 0.13), s * 0.12, s * 0.08, 0, 0, TAU); c.fill(); c.strokeStyle = 'rgba(80,60,30,.5)'; c.lineWidth = 0.8; c.stroke(); }
  flat(c, [[X(-0.42), y - r * 1.6], [X(0.42), y - r * 1.6], [X(0.42), y - r * 1.3], [X(-0.42), y - r * 1.3]], nt ? '#3a2a1a' : '#7a5a3a');
  line(c, [[X(-0.42), y - r * 1.45], [X(-0.62), y - s * 0.52]], nt ? '#3a2a1a' : '#7a5a3a', 2);
  dot(c, x, y - r, r, '#1b1a20'); dot(c, x, y - r, r * 0.35, '#8a8a90');
  line(c, [[x, y - r], [x + Math.cos(roll) * r * 0.9, y - r + Math.sin(roll) * r * 0.9]], '#8a8a90', 1.2);
  return { handle: [X(-0.62), y - s * 0.52] };
}
/* steam off a pot: a few strands, x = x₀ + a·sin(ky − ωt), fading as they rise */
function steam(c, x, y, h, t, n, col) {
  c.strokeStyle = col || 'rgba(255,255,255,.45)'; c.lineWidth = 1.4;
  for (var k = 0; k < n; k++) { c.beginPath(); for (var yy = 0; yy < h; yy += 3) { var xx = x + k * 5 - n * 2.5 + Math.sin(yy * 0.12 - t * 3 + k) * (1 + yy * 0.08); yy ? c.lineTo(xx, y - yy) : c.moveTo(xx, y); } c.stroke(); }
}
function alley(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, lk = look(S, ALLEY), X = function (f) { return S.x0 + S.span * f; }, i, k;
  var L = alleyPlan(S, lk);
  if (lk === 'muangmai' && !nt) { var w0 = cap(S, S.x0, S.x1), gd = c.createLinearGradient(0, w0, 0, deck); gd.addColorStop(0, 'rgba(255,170,120,0)'); gd.addColorStop(1, 'rgba(255,170,120,.3)'); c.fillStyle = gd; c.fillRect(S.x0, w0, S.span, deck - w0); }
  L.sh = layer(S, 'alley-' + lk, 0, S.H, function (q) {
    alleyBack(q, S, L);
    if (lk === 'muangmai') truck(q, S, X(S.phone ? 0.72 : 0.78), deck + u * 0.24, u * 1.12, -1);
    if (lk === 'spice') shrine(q, S, L.houses[Math.min(L.houses.length - 1, S.phone ? 1 : 2)]);
    if (lk === 'bazaar') { var cx = X(0.22), ct = Math.max(cap(S, cx - u, cx + u), deck - u * 3.0); clockTower(q, cx, L.back - u * 0.9, (L.back - u * 0.9 - ct), u, nt); }
    return S._sh || null;
  });
  /* the bulbs under the tarps; fluorescent tubes at Muang Mai */
  L.stalls.forEach(function (T, i) {
    var bx = (T.a0 + T.a1) / 2, by = T.ty + u * 0.22;
    if (lk === 'muangmai') { var fl = 0.85 + 0.15 * (Math.sin(t * 37 + i * 5) > 0.97 ? -3 : 1); if (nt) glow(c, bx, by, u * 0.7, 180, 0.35 * fl); c.fillStyle = nt ? 'rgba(235,250,255,' + fl + ')' : '#eef4f2'; c.fillRect(bx - u * 0.25, by - u * 0.02, u * 0.5, u * 0.04); }
    else { if (nt) glow(c, bx, by, u * 0.55, 40, 0.65 + 0.15 * Math.sin(t * 3 + i)); dot(c, bx, by, u * 0.04, nt ? '#fff2c0' : '#f6f0e0'); }
  });
  if (lk === 'nightlane' || lk === 'bazaar') for (i = 0; i < L.stalls.length - 1; i += 1) bulbs(c, (L.stalls[i].a0 + L.stalls[i].a1) / 2, (L.stalls[i + 1].a0 + L.stalls[i + 1].a1) / 2, Math.max(L.stalls[i].ty, L.stalls[i + 1].ty) + u * 0.3, u * 0.12, u * 0.18, nt, t, i % 2 ? 30 : 45);
  /* goods hung from the tarps, each a pendulum */
  L.hang.forEach(function (it) {
    var a = swing(t, it.len * 0.9, 0.12, it.ph);
    c.save(); c.translate(it.x, it.y); c.rotate(a); hangItem(c, it, u, nt); c.restore();
    if (nt && (it.kind === 'khom' || it.kind === 'lanternR')) glow(c, it.x + Math.sin(a) * u * 0.3, it.y + u * 0.35, u * 0.4, it.kind === 'khom' ? 42 : 15, 0.6);
  });
  var crew = town(S, 16, lk === 'bazaar' ? { casual: 0.5, sin: 0.3, mohom: 0.2 } : { casual: 0.6, sin: 0.2, mohom: 0.2 }), ci = 0;
  /* the back row of the crowd, heads and shoulders, shoulder to shoulder */
  if (lk === 'nightlane' || lk === 'bazaar') {
    var nb = Math.round(S.span / (u * 0.3));
    for (i = 0; i < nb; i++) { var hx = S.x0 + (i + 0.5) * S.span / nb + Math.sin(t * 0.6 + i) * u * 0.05, hy = deck + u * 0.02 - Math.abs(Math.sin(t * 3.2 + i * 1.3)) * u * 0.025, col = CLOTH[(i * 7 + S.seed) % CLOTH.length];
      c.fillStyle = nt ? dim(col, 0.4) : dim(col, 0.8, [120, 110, 100]); c.beginPath(); c.ellipse(hx, hy - u * 0.12, u * 0.13, u * 0.14, 0, Math.PI, TAU); c.fill();
      c.fillStyle = nt ? '#2a1c16' : '#3a2418'; c.beginPath(); c.arc(hx, hy - u * 0.36, u * 0.085, 0, TAU); c.fill(); }
  }
  /* the cooks at their woks (night lane), the shrine's smoke (spice), the dancer (bazaar) */
  if (lk === 'nightlane') for (k = 0; k < (S.phone ? 1 : 2); k++) {
    var T2 = L.stalls[1 + k * 2] || L.stalls[0], wx = T2.a0 + (T2.a1 - T2.a0) * 0.75, wy = deck - u * 0.52, toss = Math.max(0, Math.sin(t * 4 + k * 2));
    var dk = crew[ci++]; dk.garb = 'casual'; dk.col = '#f2f2f2';
    fig(S, dk, wx + u * 0.3, deck - u * 0.05, u * 0.85, { lean: 0.1, legs: [0.05, 0, -0.05, 0], arms: [1.3 + toss * 0.4, -0.4, 0.9, 0.6] }, -1);
    var fl2 = 0.6 + 0.4 * Math.abs(Math.sin(t * 9 + k)) + toss * 0.6;
    glow(c, wx, wy + u * 0.05, u * 0.35 * fl2, 25, nt ? 0.8 : 0.45);
    for (i = 0; i < 4; i++) { var fx = wx + (i - 1.5) * u * 0.06; flat(c, [[fx - u * 0.04, wy + u * 0.06], [fx + Math.sin(t * 13 + i) * u * 0.04, wy + u * 0.06 - u * (0.12 + 0.12 * fl2 * (0.5 + 0.5 * Math.sin(t * 11 + i * 2)))], [fx + u * 0.04, wy + u * 0.06]], i % 2 ? '#ffd24a' : '#ff7a2a'); }
    c.save(); c.translate(wx, wy); c.rotate(-toss * 0.35); flat(c, [[-u * 0.2, 0], [u * 0.2, 0], [u * 0.12, u * 0.08], [-u * 0.12, u * 0.08]], '#2a2a30'); line(c, [[u * 0.2, 0], [u * 0.36, -u * 0.04]], '#2a2a30', 2); c.restore();
    for (i = 0; i < 5; i++) { var p = frac(t * 1.2 + i / 5), fx2 = wx - u * 0.1 + i * u * 0.05, fy2 = wy - toss * u * 0.25 - Math.sin(p * Math.PI) * u * 0.18; if (toss > 0.2) dot(c, fx2, fy2, u * 0.022, ['#f2c94c', '#6aa84a', '#e0773a', '#c0392b', '#f2e6c9'][i]); }
    steam(c, wx - u * 0.05, wy - u * 0.15, u * 0.6, t, 3, 'rgba(230,230,230,.35)');
  }
  if (lk === 'spice' && L.sh) {
    var sh = L.sh; for (k = 0; k < 3; k++) steam(c, sh.x + (k - 1) * u * 0.05, sh.y, u * 0.55, t * 0.4 + k, 1, 'rgba(230,225,215,.5)');
    for (k = 0; k < 3; k++) dot(c, sh.x + (k - 1) * u * 0.05, sh.y, u * 0.015 * (1 + 0.4 * Math.sin(t * 5 + k)), '#ff6a2a');
    for (k = 0; k < 2; k++) { glow(c, sh.cx + (k ? 1 : -1) * sh.w * 0.32, sh.cy, u * 0.12, 25, nt ? 0.9 : 0.4); dot(c, sh.cx + (k ? 1 : -1) * sh.w * 0.32, sh.cy - u * 0.02, u * 0.018 * (1 + 0.3 * Math.sin(t * 9 + k)), '#ffd84a'); }
  }
  if (lk === 'bazaar') stage(S, X(S.phone ? 0.68 : 0.62), deck, t, crew[ci++]);
  if (lk === 'kadluang') { var T3 = L.stalls[S.phone ? 1 : 2]; steam(c, T3.a0 + (T3.a1 - T3.a0) * 0.5, deck - u * 0.55, u * 0.7, t, 3); }
  /* the lane: walkers both ways, slow; a porter's cart; a motorbike nosing through */
  var per = S.phone ? 4 : 6, Lp = S.span + u * 2;
  for (var lane = 0; lane < 2; lane++) for (i = 0; i < per; i++) {
    var dir = lane ? 1 : -1, v = u * (0.15 + 0.04 * ((i * 7 + lane) % 3)), base = (i / per * Lp + ((i * 37 + S.seed) % 50) / 50 * u * 0.5 + t * v) % Lp;
    var px = dir > 0 ? S.x0 - u + base : S.x1 + u - base, d = crew[(ci + lane * per + i) % crew.length];
    var M = fig(S, d, px, deck + u * (lane ? 0.36 : 0.12), u * (lane ? 0.92 : 0.84), walkP(t * TAU * 0.5 + i * 1.3, false), dir);
    var hold = (i + lane * 3 + S.seed) % 4;
    if (hold === 0) { c.fillStyle = ['#e5567f', '#f2f2f2', '#4d8fd1'][i % 3]; c.fillRect(M.hand[0][0] - u * 0.05, M.hand[0][1], u * 0.1, u * 0.13); line(c, [[M.hand[0][0] - u * 0.03, M.hand[0][1]], [M.hand[0][0], M.hand[0][1] - u * 0.04], [M.hand[0][0] + u * 0.03, M.hand[0][1]]], '#ddd', 0.8); }
    if (hold === 1 && lk !== 'muangmai') { c.fillStyle = nt ? '#6a5430' : '#c8a060'; c.beginPath(); c.ellipse(M.hand[1][0], M.hand[1][1] + u * 0.06, u * 0.08, u * 0.06, 0, 0, TAU); c.fill(); }
  }
  if (lk !== 'nightlane' && lk !== 'bazaar') {
    var cv = u * 0.22, cl = S.span + u * 3, cpx = S.x0 - u * 1.2 + ((t * cv + S.seed % 100) % cl), roll = cpx / (u * 0.17);
    var CH = cart(c, cpx, deck + u * 0.56, u, 1, lk === 'muangmai' ? 'crates' : 'sacks', nt, roll), dp = crew[ci + 12 % crew.length]; dp.garb = 'mohom'; dp.col = '#2c3e6b'; dp.low = '#24335a';
    fig(S, dp, CH.handle[0] - u * 0.22, deck + u * 0.56, u * 0.92, { lean: 0.32, legs: walkP(t * TAU * 0.45).legs, arms: [1.25, 0.2, 1.15, 0.3] }, 1);
  }
  if (lk === 'kadluang' || lk === 'muangmai') {
    var mv = u * 0.4, ml = S.span + u * 3, mx = S.x1 + u * 1.2 - ((t * mv + 37) % ml), wob = Math.sin(t * 1.7) * u * 0.03, B = moto(c, mx, deck + u * 0.62 + wob, u, -1, lk === 'muangmai' ? '#2f8f5b' : '#c0392b', nt, -mx / (u * 0.13));
    var dr = crew[(ci + 13) % crew.length]; dr.hat = true;
    var hipY = B.seat[1] + u * 0.02, hgt = u * 0.85;
    fig(S, dr, B.seat[0], hipY + hgt * 0.47, hgt, { lean: 0.15, legs: [1.45, -1.55, 1.3, -1.4], arms: [1.2, -0.2, 1.1, -0.1] }, -1);
    c.fillStyle = '#e8e2d0'; c.beginPath(); c.arc(B.seat[0], hipY - hgt * 0.47 - hgt * 0.02, hgt * 0.115, Math.PI, TAU); c.fill();
    if (lk === 'muangmai') { for (k = 0; k < 3; k++) { c.fillStyle = nt ? '#6a6a2a' : '#e8d040'; c.beginPath(); c.ellipse(B.seat[0] + u * (0.3 + k * 0.1), B.seat[1] - u * 0.02, u * 0.05, u * 0.12, 0.6, 0, TAU); c.fill(); } }
    if (frac(t / 5) < 0.3) { var bx2 = mx - u * 0.45, by2 = hipY - hgt * 0.85; c.fillStyle = '#fffaf0'; c.beginPath(); c.ellipse(bx2, by2, u * 0.32, u * 0.12, 0, 0, TAU); c.fill(); c.fillStyle = '#c0392b'; c.font = '800 ' + Math.round(u * 0.14) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ปี๊น ปี๊น', bx2, by2 + 1); }
  }
  if (lk === 'muangmai') {
    /* a porter carries crates from the truck's tail to the stack, back and forth, x = lerp(a, b, ease(u)) */
    var tx = X(S.phone ? 0.72 : 0.78) + u * 0.75, sx = X(S.phone ? 0.38 : 0.5), per2 = 7, ph = (t % per2) / per2, go = ph < 0.5, f = ease(go ? ph * 2 : 2 - ph * 2), ppx = lerp(tx, sx, f);
    var dq = crew[(ci + 14) % crew.length]; dq.garb = 'casual'; dq.col = '#4d8fd1';
    var Q = fig(S, dq, ppx, deck + u * 0.3, u * 0.9, { lean: go ? 0.12 : 0.04, legs: walkP(t * TAU * 0.8).legs, arms: go ? [2.8, 0.2, 2.9, 0.1] : walkP(t * TAU * 0.8).arms }, go ? -1 : 1);
    if (go) { flat(c, [[Q.head[0] - u * 0.18, Q.head[1] - u * 0.12], [Q.head[0] + u * 0.18, Q.head[1] - u * 0.12], [Q.head[0] + u * 0.18, Q.head[1] - u * 0.36], [Q.head[0] - u * 0.18, Q.head[1] - u * 0.36]], nt ? '#5a4a30' : '#b8925a'); for (k = 0; k < 5; k++) dot(c, Q.head[0] - u * 0.14 + k * u * 0.07, Q.head[1] - u * 0.38, u * 0.03, nt ? '#6a1a12' : '#d9342b'); }
  }
  label(S, X(0.55), deck - u * 2.35, { kadluang: '#2f6fb5', muangmai: '#3f9a6a', nightlane: '#7a1f3a', spice: '#b8322a', bazaar: '#5a2a6a' }[lk]);
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2.2, y1: S.H });
}
/* a pickup with a tall wooden rack, tailgate down, crates stacked behind */
function truck(q, S, x, y, u, dir) {
  var nt = S.night, X = function (f) { return x + dir * u * f; }, k;
  paper(q, poly([[X(-0.6), y - u * 0.32], [X(0.75), y - u * 0.32], [X(0.75), y - u * 0.62], [X(0.95), y - u * 0.62], [X(1.05), y - u * 0.92], [X(1.4), y - u * 0.92], [X(1.55), y - u * 0.6], [X(1.62), y - u * 0.55], [X(1.62), y - u * 0.25], [X(-0.6), y - u * 0.25]]), nt ? '#2a3a5a' : '#3a6ab0', 1.4);
  q.fillStyle = nt ? '#9ac0e0' : '#7aa8c8'; q.fillRect(Math.min(X(1.08), X(1.38)), y - u * 0.88, Math.abs(X(1.38) - X(1.08)), u * 0.24);
  paper(q, rect(Math.min(X(-0.6), X(0.72)), y - u * 1.35, Math.abs(X(0.72) - X(-0.6)), u * 0.06), nt ? '#4a3a24' : '#9a7448', 0.8);
  for (k = 0; k < 6; k++) paper(q, rect(X(-0.58 + k * 0.255) - u * 0.03, y - u * 1.35, u * 0.06, u * 1.05), nt ? '#4a3a24' : '#9a7448', 0.6);
  for (var j = 0; j < 3; j++) for (k = 0; k < 4; k++) { var cx = X(-0.45 + k * 0.3), cy = y - u * (0.33 + j * 0.3); paper(q, rect(cx - u * 0.13, cy - u * 0.28, u * 0.26, u * 0.28), j % 2 ? (nt ? '#4a5a7a' : '#3a7ac0') : (nt ? '#4a3a24' : '#b8925a'), 0.6); for (var m = 0; m < 4; m++) dot(q, cx - u * 0.09 + m * u * 0.06, cy - u * 0.3, u * 0.03, [nt ? '#6a1a12' : '#d9342b', nt ? '#6a5a3a' : '#c9a46a'][(j + k) % 2]); }
  [X(-0.2), X(1.25)].forEach(function (wx) { dot(q, wx, y - u * 0.14, u * 0.14, '#1b1a20'); dot(q, wx, y - u * 0.14, u * 0.06, '#8a8a90'); });
  for (j = 0; j < 3; j++) for (k = 0; k < 2; k++) { var sx = X(-1.0 - k * 0.32), sy = y - u * (0.02 + j * 0.24); paper(q, rect(sx - u * 0.14, sy - u * 0.24, u * 0.28, u * 0.24), nt ? '#4a3a24' : '#b8925a', 0.6); for (m = 0; m < 4; m++) dot(q, sx - u * 0.1 + m * u * 0.065, sy - u * 0.26, u * 0.035, j === 2 ? (nt ? '#6a5a3a' : '#c9a46a') : (nt ? '#6a1a12' : '#d9342b')); }
  q.fillStyle = nt ? '#7a1a12' : '#c8261c'; for (k = 0; k < 2; k++) { q.beginPath(); q.ellipse(X(-1.75 - k * 0.32), y - u * 0.16, u * 0.16, u * 0.18, 0, 0, TAU); q.fill(); q.fillStyle = nt ? '#5a4a30' : '#e0d0a8'; q.fillRect(X(-1.75 - k * 0.32) - u * 0.07, y - u * 0.36, u * 0.14, u * 0.06); q.fillStyle = nt ? '#7a1a12' : '#c8261c'; }
  q.fillStyle = '#fff'; q.font = '800 ' + Math.round(u * 0.12) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('ลำไย · ลิ้นจี่', X(-1.25), y - u * 0.82);
}
/* a Chinese shrine against the shophouse: red altar, gold trim, a god's seat, oranges, the incense pot */
function shrine(q, S, H) {
  var u = S.hh, nt = S.night, cx = (H.x0 + H.x1) / 2, w = (H.x1 - H.x0) * 0.62, by = S.deck - u * 0.9, k;
  paper(q, rect(cx - w / 2, by - u * 0.7, w, u * 0.7), nt ? '#6a1410' : '#b8241c', 1.2);
  q.strokeStyle = '#e8b84a'; q.lineWidth = Math.max(1, u * 0.025); q.strokeRect(cx - w / 2 + 3, by - u * 0.7 + 3, w - 6, u * 0.7 - 6);
  paper(q, poly([[cx - w * 0.6, by - u * 0.7], [cx, by - u * 0.98], [cx + w * 0.6, by - u * 0.7]]), nt ? '#2a5a3a' : '#2f8f5b', 1);
  paper(q, function (p) { p.beginPath(); p.arc(cx, by - u * 0.32, u * 0.13, 0, TAU); p.rect(cx - u * 0.17, by - u * 0.2, u * 0.34, u * 0.18); }, nt ? '#a8802a' : '#e0b04a', 0.6);
  for (k = 0; k < 6; k++) dot(q, cx + w * 0.28 + (k % 3 - 1) * u * 0.06, by - u * 0.06 - Math.floor(k / 3) * u * 0.06 - (k === 5 ? u * 0.0 : 0), u * 0.04, '#f08a1a');
  paper(q, rect(cx - w * 0.36, by - u * 0.16, u * 0.06, u * 0.16), '#d9342b', 0.4); paper(q, rect(cx + w * 0.36 - u * 0.06, by - u * 0.16, u * 0.06, u * 0.16), '#d9342b', 0.4);
  paper(q, function (p) { p.beginPath(); p.ellipse(cx - w * 0.15, by - u * 0.04, u * 0.09, u * 0.06, 0, 0, TAU); }, nt ? '#8a6a20' : '#c8a040', 0.5);
  q.strokeStyle = '#c0392b'; q.lineWidth = 1; for (k = -1; k <= 1; k++) { q.beginPath(); q.moveTo(cx - w * 0.15 + k * u * 0.05, by - u * 0.08); q.lineTo(cx - w * 0.15 + k * u * 0.05, by - u * 0.24); q.stroke(); }
  q.fillStyle = '#f2c94c'; q.font = '700 ' + Math.round(u * 0.15) + 'px "Noto Sans TC","PingFang TC",system-ui,sans-serif'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('福', cx, by - u * 0.56);
  S._sh = { x: cx - w * 0.15, y: by - u * 0.24, cx: cx, cy: by - u * 0.18, w: w };
}
/* Chiang Rai's clock tower, gilt, seen far down the lane */
function clockTower(q, x, base, h, u, nt) {
  var gold = nt ? '#c9a24a' : '#e8c25a', w = Math.min(u * 0.7, h * 0.28);
  paper(q, function (p) { p.beginPath(); p.moveTo(x - w * 0.5, base); p.lineTo(x - w * 0.4, base - h * 0.45); p.lineTo(x - w * 0.5, base - h * 0.5); p.lineTo(x - w * 0.32, base - h * 0.72); p.quadraticCurveTo(x - w * 0.2, base - h * 0.9, x, base - h); p.quadraticCurveTo(x + w * 0.2, base - h * 0.9, x + w * 0.32, base - h * 0.72); p.lineTo(x + w * 0.5, base - h * 0.5); p.lineTo(x + w * 0.4, base - h * 0.45); p.lineTo(x + w * 0.5, base); p.closePath(); }, gold, 1.2);
  dot(q, x, base - h * 0.58, w * 0.16, nt ? '#fff2c0' : '#f6f0e0'); q.strokeStyle = '#5a3a10'; q.lineWidth = 1; q.beginPath(); q.moveTo(x, base - h * 0.58); q.lineTo(x, base - h * 0.58 - w * 0.12); q.moveTo(x, base - h * 0.58); q.lineTo(x + w * 0.09, base - h * 0.58); q.stroke();
  q.strokeStyle = 'rgba(120,70,10,.5)'; for (var k = 0; k < 5; k++) { q.beginPath(); q.moveTo(x - w * 0.4, base - h * (0.08 + k * 0.08)); q.lineTo(x + w * 0.4, base - h * (0.08 + k * 0.08)); q.stroke(); }
}
/* the bazaar's stage: a dancer in pha sin with the long brass nails of the fon lep, her hands turning */
function stage(S, x, deck, t, d) {
  var c = S.c, u = S.hh, nt = S.night, w = u * 1.5, sy = deck - u * 0.42;
  flat(c, [[x - w / 2, sy], [x + w / 2, sy], [x + w / 2, deck - u * 0.05], [x - w / 2, deck - u * 0.05]], nt ? '#3a2018' : '#7a4a2a');
  c.fillStyle = '#e8b84a'; c.fillRect(x - w / 2, sy, w, u * 0.03);
  if (nt) glow(c, x, sy - u * 0.5, u * 1.0, 40, 0.4);
  d.garb = 'sin'; d.low = '#7a1f3a'; d.hem = '#e8b84a'; d.sabai = '#e8b84a'; d.hair = 2;
  var a = Math.sin(t * 1.4), M = fig(S, d, x + Math.sin(t * 0.5) * u * 0.2, sy, u * 0.9, { lean: 0.05 * a, legs: [0.15, -0.1, -0.1, 0.05], arms: [1.6 + a * 0.7, 1.2 - a * 0.5, 1.6 - a * 0.7, 1.2 + a * 0.5] }, a > 0 ? 1 : -1);
  M.hand.forEach(function (hd, k) { c.strokeStyle = '#f2c94c'; c.lineWidth = 1.2; c.beginPath(); for (var n = -1; n <= 1; n++) { c.moveTo(hd[0], hd[1]); c.lineTo(hd[0] + Math.cos(t * 1.4 + k + n * 0.3) * u * 0.12, hd[1] - Math.abs(Math.sin(t * 1.4 + k + n * 0.3)) * u * 0.12); } c.stroke(); });
}

/* ================================================================ 2. 'rooftop' — teak houses on towers
   Glass and concrete towers crowned with Lanna houses and salas. The windows play patterns:
   a wave rising floor by floor, a khom-shaped diamond |i − i₀| + ½|j − j₀| = r(t) widening, a
   twinkle; the glass lift rides its shaft, y = lerp(y₀, y₁, ease(u)); on the roof someone waters
   the plants, drops on y = y₀ + vt + ½gt². */
var ROOF = ['dusk', 'salabar', 'crown', 'mist', 'cluster', 'yipeng'];
function towerPlan(S, lk) {
  var u = S.hh, ph = S.phone, X = function (f) { return S.x0 + S.span * f; }, T = [], r = rnd(S.seed + 41);
  function add(cx, w, crownH, kind, crown, minTop) {
    var top = Math.max(cap(S, cx - w * 0.8, cx + w * 0.8) + crownH, minTop || S.H * 0.03 + crownH);
    var o = { x: cx - w / 2, w: w, cx: cx, top: top, kind: kind, crown: crown, seed: T.length * 7 + (S.seed % 97) };
    o.fh = u * (ph ? 0.15 : 0.16); o.cols = Math.max(3, Math.round(w / (u * 0.19))); o.pad = w * 0.07; o.cw = (w - o.pad * 2) / o.cols; o.y0 = top + u * 0.12;
    o.rows = Math.max(2, Math.floor((S.deck - u * 0.62 - o.y0) / o.fh)); T.push(o); return o;
  }
  var mw = u * (ph ? 2.0 : 1.45), hu = mw * 0.34;
  if (lk === 'cluster') {
    add(X(0.12), u * 0.95, u * 0.75, 'concrete', 'sala', S.deck - u * 2.6);
    var m = add(X(ph ? 0.36 : 0.32), mw, hu * 2.5, 'glass', 'ruen'); m.main = 1; m.hu = hu;
    add(X(ph ? 0.62 : 0.53), u * 1.15, u * 0.9, 'hotel', 'twin', S.deck - u * 2.75);
    add(X(ph ? 0.85 : 0.72), u * 1.0, u * 0.8, 'concrete', 'yung', S.deck - u * 2.25);
    if (!ph) add(X(0.9), u * 0.9, u * 0.7, 'glass', 'sala', S.deck - u * 1.75);
  } else {
    if (!ph || lk !== 'mist') add(X(ph ? 0.08 : 0.1), u * 0.9, 0, 'concrete', '', S.deck - u * (1.6 + r() * 0.5));
    var main = add(X(ph ? 0.33 : 0.36), lk === 'crown' ? mw * 1.15 : mw, hu * 2.5, lk === 'crown' ? 'hotel' : 'glass', lk === 'crown' ? 'pool' : 'ruen'); main.main = 1; main.hu = hu;
    if (lk !== 'crown') { main.lift = 1; }
    add(X(ph ? 0.78 : 0.66), u * 1.05, lk === 'mist' ? u * 0.7 : 0, lk === 'mist' ? 'glass' : 'concrete', lk === 'mist' ? 'sala' : '', S.deck - u * (2.0 + r() * 0.3));
    if (!ph) add(X(0.87), u * 0.8, 0, 'hotel', '', S.deck - u * 1.5);
  }
  return T;
}
function towerBody(q, S, T) {
  var nt = S.night, u = S.hh, x = T.x, w = T.w, top = T.top, base = S.deck, k, j;
  var body = T.kind === 'glass' ? (nt ? '#1a2640' : '#5f8fb4') : T.kind === 'hotel' ? (nt ? '#3a3440' : '#e8dcc8') : (nt ? '#34343e' : '#c9c2b4');
  paper(q, rect(x, top, w, base - top), body, 1.8);
  if (T.kind === 'glass') {
    var g = q.createLinearGradient(x, 0, x + w, 0); g.addColorStop(0, nt ? 'rgba(90,120,170,.22)' : 'rgba(255,255,255,.32)'); g.addColorStop(0.5, 'rgba(255,255,255,0)'); g.addColorStop(1, nt ? 'rgba(0,0,0,.28)' : 'rgba(20,40,70,.28)');
    q.fillStyle = g; q.fillRect(x, top, w, base - top);
    q.strokeStyle = nt ? 'rgba(140,170,220,.25)' : 'rgba(225,240,255,.45)'; q.lineWidth = 0.8; q.beginPath();
    for (j = 0; j <= T.rows; j++) { q.moveTo(x, T.y0 + j * T.fh); q.lineTo(x + w, T.y0 + j * T.fh); }
    for (k = 0; k <= T.cols; k++) { q.moveTo(x + T.pad + k * T.cw, T.y0); q.lineTo(x + T.pad + k * T.cw, T.y0 + T.rows * T.fh); } q.stroke();
  } else {
    q.fillStyle = nt ? '#12121a' : T.kind === 'hotel' ? '#5a6a7a' : '#4a4e58';
    for (j = 0; j < T.rows; j++) for (k = 0; k < T.cols; k++) q.fillRect(x + T.pad + k * T.cw + T.cw * 0.14, T.y0 + j * T.fh + T.fh * 0.18, T.cw * 0.72, T.fh * 0.6);
    if (T.kind === 'hotel') { q.strokeStyle = nt ? '#5a5460' : '#f8f2e6'; q.lineWidth = Math.max(1, u * 0.025); q.beginPath(); for (j = 1; j <= T.rows; j++) { q.moveTo(x - u * 0.05, T.y0 + j * T.fh); q.lineTo(x + w + u * 0.05, T.y0 + j * T.fh); } q.stroke(); }
  }
  q.fillStyle = nt ? 'rgba(255,200,120,.7)' : '#2a3038'; q.fillRect(x + w * 0.36, base - u * 0.36, w * 0.28, u * 0.32); q.fillStyle = nt ? '#5a4030' : '#8a8a90'; q.fillRect(x + w * 0.3, base - u * 0.42, w * 0.4, u * 0.05);
  paper(q, rect(x - u * 0.04, top - u * 0.05, w + u * 0.08, u * 0.09), nt ? '#2a2a34' : '#d8d2c4', 1);
  if (T.lift) { q.fillStyle = nt ? 'rgba(120,160,220,.18)' : 'rgba(220,240,255,.35)'; q.fillRect(x - u * 0.16, top + u * 0.1, u * 0.14, base - top - u * 0.1); line(q, [[x - u * 0.16, top + u * 0.1], [x - u * 0.16, base]], nt ? '#4a5060' : '#8a9aa8', 1); line(q, [[x - u * 0.02, top + u * 0.1], [x - u * 0.02, base]], nt ? '#4a5060' : '#8a9aa8', 1); }
}
/* the crowns: a ruen kalae with its terrace, a sala, a granary, a twin-gabled house, a pool */
function crown(q, S, T) {
  var u = S.hh, nt = S.night, cx = T.cx, y = T.top - u * 0.05, hu = T.hu || T.w * 0.36, k, R = null;
  if (!T.crown) return;
  paper(q, rect(T.x - u * 0.02, y - u * 0.04, T.w + u * 0.04, u * 0.05), nt ? '#4a3a2a' : '#9a7a52', 0.6);
  if (T.crown === 'ruen') { R = ruen(q, cx - T.w * 0.04, y, T.w * 0.66, hu, { nt: nt, post: 0.22, wall: 0.62, roof: 0.92, door: true }); }
  else if (T.crown === 'twin') R = ruen(q, cx, y, T.w * 0.8, T.w * 0.3, { nt: nt, post: 0.15, wall: 0.55, roof: 0.85, twin: true });
  else if (T.crown === 'yung') R = yung(q, cx, y, T.w * 0.55, T.w * 0.42, { nt: nt });
  else if (T.crown === 'sala') R = sala(q, cx, y, T.w * 0.8, T.w * 0.42, nt);
  else if (T.crown === 'pool') {
    R = ruen(q, T.x + T.w * 0.3, y, T.w * 0.5, hu * 0.95, { nt: nt, post: 0.2, wall: 0.6, roof: 0.9, door: true, toen: 1, toenW: 0.55 });
    var px0 = T.x + T.w * 0.55, px1 = T.x + T.w + u * 0.5, py = y - u * 0.18;
    paper(q, rect(px0, py, px1 - px0, u * 0.2), nt ? '#d8d2c4' : '#f2ece0', 1);
    q.fillStyle = nt ? '#1e5a8a' : '#4fc0e0'; q.fillRect(px0 + u * 0.04, py + u * 0.02, px1 - px0 - u * 0.08, u * 0.1);
    q.fillStyle = 'rgba(220,240,255,.4)'; q.fillRect(px1 - u * 0.04, py - u * 0.18, u * 0.04, u * 0.36);
    T.pool = [px0 + u * 0.04, px1 - u * 0.08, py + u * 0.02];
  }
  /* pots of bougainvillea along the roof's edge, a rail */
  q.strokeStyle = nt ? '#6a6a70' : '#9a9aa0'; q.lineWidth = 1; q.beginPath(); q.moveTo(T.x, y - u * 0.18); q.lineTo(T.x + T.w, y - u * 0.18); for (k = 0; k <= 6; k++) { q.moveTo(T.x + T.w * k / 6, y - u * 0.18); q.lineTo(T.x + T.w * k / 6, y - u * 0.04); } q.stroke();
  if (T.main && T.crown !== 'pool') [0.05, 0.92].forEach(function (f, i) { var bx = T.x + T.w * f; paper(q, rect(bx - u * 0.05, y - u * 0.13, u * 0.1, u * 0.1), nt ? '#5a2c20' : '#b05a3a', 0.4); for (k = 0; k < 5; k++) dot(q, bx + (k - 2) * u * 0.035, y - u * 0.17 - (k % 2) * u * 0.05, u * 0.045, nt ? '#4a1a3a' : (k % 2 ? '#e5567f' : '#3f7f42')); });
  T.R = R;
}
/* a sala: four posts, a two-tier roof with kalae on the gable */
function sala(q, x, base, w, u, nt) {
  var P = teak(nt), top = base - u * 0.9;
  [x - w * 0.38, x - w * 0.13, x + w * 0.13, x + w * 0.38].forEach(function (px) { paper(q, rect(px - u * 0.04, top, u * 0.08, base - top), P.post, 0.8); });
  paper(q, rect(x - w * 0.45, base - u * 0.1, w * 0.9, u * 0.1), P.dark, 0.8);
  paper(q, poly([[x - w * 0.6, top + u * 0.05], [x - w * 0.42, top - u * 0.18], [x + w * 0.42, top - u * 0.18], [x + w * 0.6, top + u * 0.05]]), P.tile, 1.2);
  var G = gable(q, x, w * 0.75, top - u * 0.16, u * 0.55, u, P, 0.7);
  return { fl: base, wt: top, horns: [G.horn], top: G.top, wins: [] };
}
function liveWindows(c, S, T, t, mode, ph) {
  var nt = S.night, rows = T.rows, cols = T.cols, ci = (cols - 1) / 2, cj = rows * 0.42, dmax = ci + Math.max(cj, rows - cj) * 0.5 + 1, i, j;
  c.fillStyle = nt ? '#ffd88a' : '#fff4d0';
  for (j = 0; j < rows; j++) for (i = 0; i < cols; i++) {
    var h = h2(i, j, T.seed), band;
    if (mode === 0) band = Math.exp(-Math.pow((1 - j / rows) - (ph * 1.4 - 0.2), 2) * 70);
    else if (mode === 1) { var d = Math.abs(i - ci) + Math.abs(j - cj) * 0.5; band = Math.max(0, 1 - Math.abs(d - ph * dmax) * 1.3); }
    else band = Math.pow(Math.max(0, Math.sin(t * (0.4 + h * 1.2) + h * 40)), 8);
    var on = Math.max(nt && h < 0.42 ? 0.5 : 0, band * (nt ? 1 : 0.55));
    if (on < 0.08) continue;
    c.globalAlpha = on; c.fillRect(T.x + T.pad + i * T.cw + T.cw * 0.14, T.y0 + j * T.fh + T.fh * 0.18, T.cw * 0.72, T.fh * 0.6);
  }
  c.globalAlpha = 1;
}
function khomLoi(c, x, y, s, t, k) {
  var fl = 0.85 + 0.15 * Math.sin(t * 9 + k * 3);
  glow(c, x, y, s * 3, 30, 0.55 * fl);
  flat(c, [[x - s * 0.55, y + s * 0.8], [x - s * 0.7, y - s * 0.5], [x - s * 0.3, y - s * 1.1], [x + s * 0.3, y - s * 1.1], [x + s * 0.7, y - s * 0.5], [x + s * 0.55, y + s * 0.8]], '#ffcf80');
  dot(c, x, y + s * 0.8, s * 0.2 * fl, '#fff6c0');
}
/* a little car on the road below: a red songthaew, a tuk-tuk or a car */
function wheels(c, kind, x, y, s, dir, nt) {
  var X = function (f) { return x + dir * s * f; }, col = kind === 'song' ? '#c8261c' : kind === 'tuk' ? '#2f6fb5' : '#e8e2d0';
  if (kind === 'song') { flat(c, [[X(-0.7), y - s * 0.12], [X(0.45), y - s * 0.12], [X(0.45), y - s * 0.42], [X(0.6), y - s * 0.42], [X(0.72), y - s * 0.24], [X(0.72), y - s * 0.12], [X(0.72), y - s * 0.06], [X(-0.7), y - s * 0.06]], nt ? '#7a1a14' : col); flat(c, [[X(-0.7), y - s * 0.42], [X(0.42), y - s * 0.42], [X(0.42), y - s * 0.48], [X(-0.7), y - s * 0.48]], nt ? '#5a1410' : '#a81c14'); c.fillStyle = nt ? '#ffd890' : '#3a3038'; c.fillRect(Math.min(X(-0.6), X(0.3)), y - s * 0.38, Math.abs(X(0.3) - X(-0.6)), s * 0.14); }
  else if (kind === 'tuk') { flat(c, [[X(-0.4), y - s * 0.1], [X(0.4), y - s * 0.1], [X(0.45), y - s * 0.3], [X(0.3), y - s * 0.5], [X(-0.4), y - s * 0.5]], nt ? '#1a3a6a' : col); c.fillStyle = nt ? '#ffd890' : '#f2e6c9'; c.fillRect(Math.min(X(-0.3), X(0.2)), y - s * 0.42, Math.abs(X(0.2) - X(-0.3)), s * 0.14); }
  else { flat(c, [[X(-0.55), y - s * 0.1], [X(0.55), y - s * 0.1], [X(0.55), y - s * 0.22], [X(0.3), y - s * 0.26], [X(0.15), y - s * 0.4], [X(-0.3), y - s * 0.4], [X(-0.45), y - s * 0.26], [X(-0.55), y - s * 0.24]], nt ? '#5a5a64' : col); }
  [X(-0.4), X(0.4)].forEach(function (wx) { dot(c, wx, y - s * 0.08, s * 0.08, '#1b1a20'); });
  if (nt) { glow(c, X(0.72), y - s * 0.2, s * 0.35, 50, 0.7); glow(c, X(-0.7), y - s * 0.2, s * 0.18, 0, 0.7); }
}
function rooftop(S) {
  var lk = look(S, ROOF); if (lk === 'salabar') return skyBar(S);
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, X = function (f) { return S.x0 + S.span * f; }, i, k;
  var TT = towerPlan(S, lk), M = TT.filter(function (T) { return T.main; })[0];
  var CR = layer(S, 'roof-' + lk, 0, S.H, function (q) {
    if (lk === 'mist') {   /* Doi Suthep behind, its gilt chedi near the top */
      var mx = X(S.phone ? 0.25 : 0.2), mt = Math.max(cap(S, mx - u, mx + u), deck - u * 2.9), mw = S.span * (S.phone ? 0.9 : 0.75);
      paper(q, function (p) { p.beginPath(); p.moveTo(mx - mw * 0.5, deck); for (var f = 0; f <= 1.001; f += 0.04) { var xx = mx - mw * 0.5 + f * mw, e = Math.pow(Math.sin(f * Math.PI), 1.3); p.lineTo(xx, deck - (deck - mt) * e * (0.97 + 0.03 * Math.sin(f * 17))); } p.closePath(); }, nt ? '#1e2c36' : '#7a9aa2', 1.4);
      paper(q, function (p) { p.beginPath(); p.moveTo(mx + u * 0.05, mt + u * 0.12); p.lineTo(mx + u * 0.12, mt + u * 0.25); p.lineTo(mx - u * 0.02, mt + u * 0.25); p.closePath(); p.rect(mx - u * 0.05, mt + u * 0.25, u * 0.24, u * 0.06); }, nt ? '#d8a84e' : '#f0c060', 0.6);
    }
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#26242a' : '#7a7670');
    q.fillStyle = nt ? 'rgba(255,230,160,.25)' : 'rgba(255,255,255,.5)'; for (var dx = S.x0; dx < S.x1; dx += u * 0.5) q.fillRect(dx, deck + u * 0.32, u * 0.25, u * 0.03);
    /* the low town around the towers' feet: shophouses, rain trees, a wat's roof */
    var r = rnd(S.seed + 9), xx = S.x0 - u * 0.2;
    while (xx < S.x1) { var bw = u * (0.45 + r() * 0.5), bh = u * (0.35 + r() * 0.5), cl = FACADE[Math.floor(r() * FACADE.length)];
      if (r() < 0.25) bushTree(q, xx + bw / 2, deck - u * 0.02, bh * 1.4, nt, Math.floor(r() * 99));
      else { paper(q, rect(xx, deck - bh, bw, bh), nt ? dim(cl, 0.35) : dim(cl, 0.85, [120, 140, 160]), 0.8); for (k = 0; k < 3; k++) { q.fillStyle = nt ? (r() < 0.5 ? '#ffd890' : '#18141c') : 'rgba(40,50,60,.5)'; q.fillRect(xx + bw * (0.15 + k * 0.27), deck - bh * 0.75, bw * 0.16, bh * 0.22); } }
      xx += bw + u * 0.05; }
    wihan(q, X(S.phone ? 0.62 : 0.52), deck - u * 0.02, u * 1.2, u * 0.95, u, nt);
    TT.forEach(function (T) { towerBody(q, S, T); });
    TT.forEach(function (T) { crown(q, S, T); });
    return TT.map(function (T) { return { R: T.R, pool: T.pool }; });
  });
  TT.forEach(function (T, j) { T.R = CR[j].R; T.pool = CR[j].pool; });
  /* the windows' pattern, shared by every tower so the skyline plays it together */
  var mode = Math.floor(t / 8 + (S.seed % 3)) % 3, ph = frac(t / 8);
  TT.forEach(function (T) { liveWindows(c, S, T, t, mode, ph); });
  if (!nt) TT.forEach(function (T) { if (T.kind !== 'glass') return; c.save(); c.beginPath(); c.rect(T.x, T.top, T.w, deck - T.top); c.clip(); var gx = T.x - T.w + frac(t / 6 + T.seed * 0.1) * T.w * 3; c.fillStyle = 'rgba(255,255,255,.2)'; c.beginPath(); c.moveTo(gx, T.top); c.lineTo(gx + T.w * 0.25, T.top); c.lineTo(gx - T.w * 0.6, deck); c.lineTo(gx - T.w * 0.85, deck); c.fill(); c.restore(); });
  /* the lift */
  TT.forEach(function (T) { if (!T.lift) return; var p = frac(t / 11 + 0.3), e = ease(Math.max(0, Math.min(1, (p < 0.5 ? p : 1 - p) * 2.6 - 0.15))), ch = u * 0.2, ly = lerp(deck - ch - u * 0.08, T.top + u * 0.14, e);
    if (nt) glow(c, T.x - u * 0.09, ly + ch / 2, u * 0.35, 45, 0.6); c.fillStyle = nt ? '#ffe8b0' : '#f2ece0'; c.fillRect(T.x - u * 0.15, ly, u * 0.12, ch); dot(c, T.x - u * 0.09, ly + ch * 0.35, u * 0.025, '#3a2a20'); c.fillStyle = '#3a2a20'; c.fillRect(T.x - u * 0.11, ly + ch * 0.45, u * 0.04, ch * 0.5); });
  /* the crowns glow gold; their windows lit */
  TT.forEach(function (T) {
    if (!T.R) return; var hu = T.hu || T.w * 0.36, gy = (T.R.top + T.top) / 2;
    var br = 1 + 0.1 * Math.sin(t * 1.3 + T.seed); glow(c, T.cx, gy, hu * (T.main ? 1.3 : 1.0), 38, (nt ? 0.15 : 0.05) * br); glow(c, T.cx, gy + hu * 0.25, hu * (T.main ? 0.8 : 0.6), 42, (nt ? 0.32 : 0.1) * br);
    (T.R.wins || []).forEach(function (w, k2) { c.fillStyle = nt ? 'rgba(255,200,110,' + (0.75 + 0.2 * Math.sin(t * 2 + k2)) + ')' : 'rgba(255,214,140,.35)'; c.fillRect(w[0], w[1], w[2], w[3]); });
  });
  /* strings of bulbs from the main crown's eave to the rail */
  if (M && M.R && M.R.gables) { var G = M.R.gables[0]; bulbs(c, M.x + u * 0.02, G.apex[0] - G.ex * 0.6, M.top - u * 0.25, u * 0.06, u * 0.1, nt, t, 40); bulbs(c, G.apex[0] + G.ex * 0.6, M.x + M.w - u * 0.02, M.top - u * 0.25, u * 0.06, u * 0.1, nt, t, 40); }
  /* someone on the roof watering the pots */
  if (M && M.crown !== 'pool') {
    var crew = town(S, 3, { sin: 0.6, mohom: 0.4 }), d = crew[0], gx2 = M.x + M.w * 0.8, hh2 = (M.hu || u * 0.5) * 0.62, tip = Math.sin(t * 1.1) * 0.15;
    var W = fig(S, d, gx2, M.top - u * 0.05, hh2, { lean: 0.1, legs: [0.06, 0, -0.06, 0], arms: [1.15 + tip, 0.2, 0.3, 0.3] }, 1), hx = W.hand[0][0], hy = W.hand[0][1];
    flat(c, [[hx - hh2 * 0.08, hy], [hx + hh2 * 0.08, hy], [hx + hh2 * 0.07, hy + hh2 * 0.12], [hx - hh2 * 0.07, hy + hh2 * 0.12]], '#3f9a6a'); line(c, [[hx + hh2 * 0.07, hy + hh2 * 0.02], [hx + hh2 * 0.22, hy - hh2 * 0.03]], '#3f9a6a', 1.4);
    for (k = 0; k < 6; k++) { var tau = frac(t * 1.5 + k / 6) * 0.35, vx = hh2 * 0.6, ddx = hx + hh2 * 0.22 + vx * tau, ddy = hy - hh2 * 0.03 + 9.8 * tau * tau * hh2 * 0.35; if (ddy < M.top - u * 0.1) dot(c, ddx, ddy, Math.max(0.8, u * 0.015), nt ? 'rgba(170,210,255,.8)' : 'rgba(80,150,220,.85)'); }
  }
  if (M && M.pool) {   /* a swimmer crossing the pool, arms over in turn */
    var P = M.pool, sp = frac(t / 9), sw = P[0] + (P[1] - P[0]) * (sp < 0.5 ? sp * 2 : 2 - sp * 2), sdir = sp < 0.5 ? 1 : -1;
    c.strokeStyle = 'rgba(255,255,255,.6)'; c.lineWidth = 1; c.beginPath(); for (var rx = P[0]; rx < P[1]; rx += u * 0.12) { c.moveTo(rx + Math.sin(t * 2 + rx) * 2, P[2] + u * 0.03); c.lineTo(rx + u * 0.05 + Math.sin(t * 2 + rx) * 2, P[2] + u * 0.03); } c.stroke();
    dot(c, sw, P[2] + u * 0.02, u * 0.035, '#3a2418'); var aa = t * 5; line(c, [[sw, P[2] + u * 0.03], [sw + sdir * Math.cos(aa) * u * 0.08, P[2] + u * 0.03 - Math.abs(Math.sin(aa)) * u * 0.07]], '#d9a27a', 1.6);
    var ld = town(S, 2, { casual: 1 })[1]; fig(S, ld, M.x + M.w * 0.88, M.top - u * 0.22, (M.hu || u * 0.5) * 0.55, { lean: 0, seat: 0.24, legs: POSE.sit.legs, arms: [0.4, 1.2, 0.2, 0.6] }, -1);
  }
  /* mist rolling through the towers' feet at dawn */
  if (lk === 'mist') for (k = 0; k < 5; k++) { var my = deck - u * (0.25 + k * 0.33), drift = (t * u * (0.05 + k * 0.02) + k * 97) % (S.span + u * 4);
    for (i = 0; i < 6; i++) { var ex = S.x0 - u * 2 + ((drift + i * S.span / 6) % (S.span + u * 4)); puff(c, ex, my + Math.sin(i + k) * u * 0.08, u * (1.3 + (i % 3) * 0.35), u * (0.26 + (k % 2) * 0.08), nt ? 0.3 : 0.55, nt); } }
  /* lanterns going up past the roofs at Yi Peng; two on the roof let one go */
  if (lk === 'yipeng') {
    var n = S.phone ? 8 : 14;
    for (k = 0; k < n; k++) { var Pd = 14 + (k % 5) * 3, uu = frac(t / Pd + k * 0.618), lx = S.x0 + S.span * frac(k * 0.37 + 0.11) + Math.sin(uu * TAU * 1.3 + k) * u * 0.4 + uu * u * 0.8, ly2 = deck - u * 0.4 - uu * (deck - S.H * 0.04);
      if (ly2 < cap(S, lx - 4, lx + 4)) continue; khomLoi(c, lx, ly2, u * (0.1 - uu * 0.04), t, k); }
    if (M) { var rp = frac(t / 10), rx2 = M.x + M.w * 0.82, ry = M.top - u * 0.05, hl2 = (M.hu || u * 0.5) * 0.6, cr2 = town(S, 2, { sin: 0.5, mohom: 0.5 });
      fig(S, cr2[0], rx2 - hl2 * 0.25, ry, hl2, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.7, 0, 2.9, 0] }, 1); fig(S, cr2[1], rx2 + hl2 * 0.3, ry, hl2 * 0.95, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.9, 0, 2.7, 0] }, -1);
      khomLoi(c, rx2 + Math.sin(rp * 3) * u * 0.1, ry - hl2 * 1.15 - (rp > 0.3 ? Math.pow((rp - 0.3) / 0.7, 1.4) * (ry - S.H * 0.05) : 0), u * 0.11, t, 99); }
  }
  /* the road: a red songthaew, a tuk-tuk, a car */
  ['song', 'tuk', 'car'].forEach(function (kd, j) { var v = u * (0.6 + j * 0.25), Lr = S.span + u * 3, dir = j % 2 ? -1 : 1, off = ((t * v + j * 211) % Lr), vx2 = dir > 0 ? S.x0 - u * 1.5 + off : S.x1 + u * 1.5 - off; wheels(c, kd, vx2, deck + u * (j % 2 ? 0.5 : 0.3), u * 0.85, dir, nt); });
  label(S, X(0.86), deck - u * 1.35, '#c0392b');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: M ? M.top - u : deck - u * 2, y1: S.H });
}
/* the sala bar on a roof: we stand on the deck; the city lies below the glass rail, Doi Suthep beyond */
function skyBar(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, X = function (f) { return S.x0 + S.span * f; }, i, k;
  var rail = deck - u * 0.62, hz = S.H * 0.62, sx0 = X(S.phone ? 0.03 : 0.05), sx1 = X(S.phone ? 0.62 : 0.5), sw = sx1 - sx0, stop = Math.max(cap(S, sx0 - u * 0.3, sx1 + u * 0.3) + u * 0.75, deck - u * 2.35);
  var nb = X(S.phone ? 0.84 : 0.8), nbTop = Math.max(cap(S, nb - u * 0.6, nb + u * 0.6) + u * 0.6, deck - u * 1.75);
  layer(S, 'skybar', 0, S.H, function (q) {
    /* the city below: blocks in haze, lit windows, a few towers crowned with their own houses */
    var r = rnd(S.seed + 2), xx = S.x0 - u * 0.2;
    for (var row = 0; row < 3; row++) { xx = S.x0 - u * 0.2 - row * u * 0.13;
      while (xx < S.x1) { var bw = u * (0.22 + r() * 0.3), bh = (rail - hz) * (0.25 + row * 0.22) + r() * u * 0.25, by = rail - bh * (0.5 + row * 0.3) + row * u * 0.12;
        q.fillStyle = nt ? dim('#3a4060', 0.6 + row * 0.15) : dim('#9ab0c0', 0.7 + row * 0.1, [200, 210, 220]); q.fillRect(xx, by, bw, rail - by);
        for (k = 0; k < 6; k++) { q.fillStyle = nt ? (r() < 0.55 ? 'rgba(255,214,140,.85)' : 'rgba(0,0,0,0)') : 'rgba(255,255,255,.35)'; q.fillRect(xx + bw * (0.15 + (k % 2) * 0.45), by + (rail - by) * (0.1 + Math.floor(k / 2) * 0.25), bw * 0.25, Math.max(1.5, u * 0.04)); }
        xx += bw + u * 0.03; } }
    /* the neighbour's tower, level with us, a kalae house on its roof */
    paper(q, rect(nb - u * 0.55, nbTop, u * 1.1, deck - nbTop), nt ? '#1a2640' : '#6a92b4', 1.4);
    for (var j = 0; j < 6; j++) for (k = 0; k < 4; k++) { q.fillStyle = nt ? (h2(j, k, 3) < 0.5 ? '#ffd890' : '#0e1426') : 'rgba(255,255,255,.3)'; q.fillRect(nb - u * 0.45 + k * u * 0.24, nbTop + u * (0.15 + j * 0.18), u * 0.16, u * 0.1); }
    ruen(q, nb, nbTop, u * 0.75, u * 0.3, { nt: nt, post: 0.2, wall: 0.6, roof: 0.9 });
    /* the deck, the glass rail, planters */
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#3a2a20' : '#9a7450');
    q.strokeStyle = nt ? 'rgba(0,0,0,.35)' : 'rgba(60,40,20,.3)'; q.lineWidth = 1; for (var px = S.x0; px < S.x1; px += u * 0.4) { q.beginPath(); q.moveTo(px, deck); q.lineTo(px - u * 0.2, S.H); q.stroke(); }
    q.fillStyle = nt ? 'rgba(150,180,220,.14)' : 'rgba(220,240,255,.35)'; q.fillRect(S.x0, rail, S.span, deck - rail);
    q.strokeStyle = nt ? '#8a8a94' : '#c8ccd4'; q.lineWidth = Math.max(1.5, u * 0.03); q.beginPath(); q.moveTo(S.x0, rail); q.lineTo(S.x1, rail); for (px = S.x0; px < S.x1; px += u * 0.8) { q.moveTo(px, rail); q.lineTo(px, deck); } q.stroke();
    for (k = 0; k < 4; k++) { var pxx = X(0.55 + k * 0.13); paper(q, rect(pxx - u * 0.18, deck - u * 0.22, u * 0.36, u * 0.22), nt ? '#3a3a40' : '#8a8a90', 0.6); for (j = 0; j < 6; j++) dot(q, pxx + (j - 2.5) * u * 0.06, deck - u * (0.28 + (j % 2) * 0.08), u * 0.07, nt ? '#1e3a24' : ['#3f7f42', '#e5567f', '#4f8f4a'][j % 3]); }
    /* the sala over the bar */
    var P = teak(nt);
    [sx0 + sw * 0.04, sx0 + sw * 0.36, sx0 + sw * 0.64, sx0 + sw * 0.96].forEach(function (pp) { paper(q, rect(pp - u * 0.045, stop + u * 0.3, u * 0.09, deck - stop - u * 0.3), P.post, 0.9); });
    paper(q, poly([[sx0 - sw * 0.1, stop + u * 0.42], [sx0 + sw * 0.08, stop + u * 0.1], [sx1 - sw * 0.08, stop + u * 0.1], [sx1 + sw * 0.1, stop + u * 0.42]]), P.tile, 1.4);
    gable(q, (sx0 + sx1) / 2, sw * 0.66, stop + u * 0.12, u * 0.62, u, P, 0.9);
    /* the bar: a carved teak front, bottles behind */
    var bx0 = sx0 + sw * 0.12, bx1 = sx1 - sw * 0.12, bt = deck - u * 0.55;
    for (k = 0; k < 9; k++) { var bxx = bx0 + (bx1 - bx0) * (k + 0.5) / 9, bh2 = u * (0.18 + (k % 3) * 0.04); q.fillStyle = ['#2f8f5b', '#c0392b', '#e8b84a', '#4d8fd1', '#8a4a2a'][k % 5]; q.globalAlpha = nt ? 0.75 : 0.9; q.fillRect(bxx - u * 0.025, bt - u * 0.42 - bh2, u * 0.05, bh2); q.fillRect(bxx - u * 0.01, bt - u * 0.48 - bh2, u * 0.02, u * 0.07); }
    q.globalAlpha = 1; paper(q, rect(bx0 - u * 0.1, bt - u * 0.43, bx1 - bx0 + u * 0.2, u * 0.03), P.dark, 0.5);
    paper(q, rect(bx0, bt, bx1 - bx0, deck - bt), P.wall, 1.2);
    paper(q, rect(bx0 - u * 0.06, bt - u * 0.05, bx1 - bx0 + u * 0.12, u * 0.07), P.dark, 0.8);
    q.strokeStyle = P.horn; q.lineWidth = 1; for (k = 0; k < 5; k++) { var cx2 = bx0 + (bx1 - bx0) * (k + 0.5) / 5; q.beginPath(); q.moveTo(cx2, deck - u * 0.08); q.quadraticCurveTo(cx2 - u * 0.1, bt + u * 0.22, cx2, bt + u * 0.08); q.quadraticCurveTo(cx2 + u * 0.1, bt + u * 0.22, cx2, deck - u * 0.08); q.stroke(); }
  });
  /* the city twinkles; cars stream on a road far below */
  for (k = 0; k < 18; k++) { var cxk = S.x0 + S.span * frac(k * 0.618 + 0.1), cyk = rail - u * 0.08 - frac(k * 0.37) * (rail - hz) * 0.6; if (Math.sin(t * (1 + k % 3) + k * 9) > 0.6) dot(c, cxk, cyk, Math.max(1, u * 0.02), nt ? '#fff2c0' : 'rgba(255,255,255,.8)'); }
  for (k = 0; k < 10; k++) { var ry = rail - u * 0.18, rx = S.x0 + frac(t * 0.03 * (k % 2 ? 1 : -1) + k / 10) * S.span; dot(c, rx, ry + (k % 2) * u * 0.04, Math.max(1, u * 0.018), k % 2 ? (nt ? '#ff6a5a' : '#c0392b') : (nt ? '#fff6d0' : '#f2f2f2')); }
  glow(c, nb, nbTop - u * 0.3, u * 0.55, 38, nt ? 0.45 : 0.12);
  /* khom lanterns under the sala's eave, swinging, and a string of bulbs to the rail's end */
  var nk = S.phone ? 3 : 5;
  for (k = 0; k < nk; k++) { var kx = sx0 + sw * (0.1 + 0.8 * k / (nk - 1)), ky = stop + u * 0.42, a = swing(t, 0.6, 0.1, k * 1.3);
    c.save(); c.translate(kx, ky); c.rotate(a); hangItem(c, { kind: k % 2 ? 'khom' : 'lanternR', len: 0.3, col: '#f2c94c' }, u * 0.55, nt); c.restore();
    if (nt) glow(c, kx + Math.sin(a) * u * 0.15, ky + u * 0.22, u * 0.35, k % 2 ? 42 : 15, 0.5); }
  bulbs(c, sx1 + sw * 0.08, X(0.98), Math.max(stop + u * 0.42, cap(S, sx1, X(0.98)) + 4), u * 0.25, u * 0.2, nt, t, 40);
  /* the bartender shakes; three on stools; two at the rail looking out; a waiter with a tray */
  var crew = town(S, 8, { casual: 0.55, sin: 0.25, mohom: 0.2 }), bt2 = deck - u * 0.55, bxm = (sx0 + sx1) / 2 + sw * 0.18, sh = Math.sin(t * 14);
  var bd = crew[0]; bd.garb = 'mohom'; bd.col = '#2c3e6b';
  var B = fig(S, bd, bxm, deck - u * 0.02, u * 0.88, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [2.4 + sh * 0.25, 0.6, 2.3 - sh * 0.25, 0.7] }, -1);
  flat(c, [[B.hand[0][0] - u * 0.03, B.hand[0][1] - u * 0.14], [B.hand[0][0] + u * 0.03, B.hand[0][1] - u * 0.14], [B.hand[0][0] + u * 0.035, B.hand[0][1] + u * 0.02], [B.hand[0][0] - u * 0.035, B.hand[0][1] + u * 0.02]], '#d8dce4');
  paper(c, rect(sx0 + sw * 0.12, bt2, sw * 0.76, deck - bt2), teak(nt).wall, 0.6);
  for (k = 0; k < 3; k++) { var stx = sx0 + sw * (0.22 + k * 0.22), d = crew[1 + k], lift = Math.sin(t * 0.8 + k * 2) > 0.5 ? 1 : 0;
    line(c, [[stx, deck + u * 0.18], [stx, deck - u * 0.28]], '#2a2a30', 2); flat(c, [[stx - u * 0.12, deck - u * 0.3], [stx + u * 0.12, deck - u * 0.3], [stx + u * 0.1, deck - u * 0.26], [stx - u * 0.1, deck - u * 0.26]], '#2a2a30');
    var Sd = fig(S, d, stx, deck - u * 0.28 + u * 0.88 * 0.24, u * 0.88, { lean: 0.1, seat: 0.24, legs: [1.3, -1.2, 1.1, -1.0], arms: [lift ? 2.0 : 1.2, lift ? 1.6 : 0.9, 0.9, 0.9] }, -1);
    var gx = Sd.hand[0][0], gy = Sd.hand[0][1]; flat(c, [[gx - u * 0.04, gy - u * 0.08], [gx + u * 0.04, gy - u * 0.08], [gx, gy - u * 0.02]], ['#ffb38a', '#7fd8ff', '#ff5a8c'][k]); line(c, [[gx, gy - u * 0.02], [gx, gy + u * 0.04]], '#ddd', 1); }
  var rx0 = X(S.phone ? 0.78 : 0.68), d5 = crew[5], d6 = crew[6];
  fig(S, d5, rx0, deck + u * 0.12, u * 0.95, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.9 + 0.1 * Math.sin(t), 0.1, 0.4, 0.8] }, 1);
  var D6 = fig(S, d6, rx0 - u * 0.32, deck + u * 0.16, u * 0.9, { lean: 0.03, legs: [0.06, 0, -0.06, 0], arms: [1.0, 1.4, 0.2, 0.2] }, 1);
  flat(c, [[D6.hand[0][0] - u * 0.03, D6.hand[0][1] - u * 0.1], [D6.hand[0][0] + u * 0.03, D6.hand[0][1] - u * 0.1], [D6.hand[0][0] + u * 0.025, D6.hand[0][1]], [D6.hand[0][0] - u * 0.025, D6.hand[0][1]]], 'rgba(255,200,120,.85)');
  var wp = frac(t / 12), wgo = wp < 0.5, wx = lerp(sx1 + u * 0.2, X(0.97) - u * 0.4, ease(wgo ? wp * 2 : 2 - wp * 2)), d7 = crew[7]; d7.garb = 'mohom'; d7.col = '#2c3e6b';
  var Wt = fig(S, d7, wx, deck + u * 0.4, u * 0.95, { lean: 0.03, legs: walkP(t * TAU * 0.7).legs, arms: [1.6, -1.4, 0.3, 0.3] }, wgo ? 1 : -1);
  flat(c, [[Wt.hand[0][0] - u * 0.18, Wt.hand[0][1] - u * 0.02], [Wt.hand[0][0] + u * 0.18, Wt.hand[0][1] - u * 0.02], [Wt.hand[0][0] + u * 0.18, Wt.hand[0][1] + u * 0.01], [Wt.hand[0][0] - u * 0.18, Wt.hand[0][1] + u * 0.01]], '#c8ccd4');
  for (k = 0; k < 2; k++) flat(c, [[Wt.hand[0][0] - u * 0.1 + k * u * 0.12, Wt.hand[0][1] - u * 0.12], [Wt.hand[0][0] - u * 0.04 + k * u * 0.12, Wt.hand[0][1] - u * 0.12], [Wt.hand[0][0] - u * 0.07 + k * u * 0.12, Wt.hand[0][1] - u * 0.03]], k ? '#7fd8ff' : '#ffb38a');
  label(S, X(0.72), deck - u * 2.05, '#9b6bd6');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: stop, y1: S.H });
}

/* ================================================================ 3. 'lanna-house' — the ruen kalae
   The kalae house on its posts, a weaver at the loom beneath, the water jar at the gate where a
   passer-by stops to drink; the granary filling at harvest; a village lane under a temple gate;
   khantok on the terrace; a house raised on pegs with no nails; and the parts named. */
var LANNA = ['kalae', 'granary', 'street', 'khantok', 'build', 'parts'];
function yard(q, S, seedBits) {
  var u = S.hh, nt = S.night, r = rnd(S.seed + seedBits), k;
  K.ground(q, S.x0, S.x1, S.deck, S.H, nt ? '#2e2418' : '#b08a5a');
  q.fillStyle = nt ? 'rgba(80,120,70,.35)' : 'rgba(110,150,70,.55)'; for (k = 0; k < 26; k++) { var gx = S.x0 + r() * S.span, gy = S.deck + r() * (S.H - S.deck); q.beginPath(); q.moveTo(gx - 3, gy); q.lineTo(gx, gy - u * 0.1); q.lineTo(gx + 1, gy); q.lineTo(gx + 4, gy - u * 0.08); q.lineTo(gx + 5, gy); q.fill(); }
}
function fence(q, x0, x1, base, u, nt) {
  q.fillStyle = nt ? '#5a4a30' : '#c8a868';
  for (var x = x0; x < x1; x += u * 0.09) { q.fillRect(x, base - u * 0.42 - (Math.round(x) % 3) * u * 0.02, u * 0.05, u * 0.42 + (Math.round(x) % 3) * u * 0.02); }
  line(q, [[x0, base - u * 0.32], [x1, base - u * 0.32]], nt ? '#4a3a24' : '#9a7a40', Math.max(1.2, u * 0.03)); line(q, [[x0, base - u * 0.14], [x1, base - u * 0.14]], nt ? '#4a3a24' : '#9a7a40', Math.max(1.2, u * 0.03));
}
function hen(c, x, y, s, t, ph, col, dir) {
  var peck = Math.pow(Math.max(0, Math.sin(t * 2.2 + ph)), 6);
  c.fillStyle = col; c.beginPath(); c.ellipse(x, y - s * 0.4, s * 0.42, s * 0.3, 0, 0, TAU); c.fill();
  flat(c, [[x - dir * s * 0.3, y - s * 0.5], [x - dir * s * 0.7, y - s * 0.95], [x - dir * s * 0.55, y - s * 0.35]], col);
  var hx = x + dir * s * (0.4 + peck * 0.15), hy = y - s * (0.75 - peck * 0.6);
  dot(c, hx, hy, s * 0.17, col); dot(c, hx - dir * s * 0.02, hy - s * 0.17, s * 0.08, '#d9342b');
  flat(c, [[hx + dir * s * 0.14, hy - s * 0.03], [hx + dir * s * 0.3, hy + s * 0.02], [hx + dir * s * 0.14, hy + s * 0.06]], '#e8b84a');
  line(c, [[x - s * 0.08, y - s * 0.12], [x - s * 0.1, y]], '#c89a3a', 1); line(c, [[x + s * 0.08, y - s * 0.12], [x + s * 0.06, y]], '#c89a3a', 1);
}
/* a shoulder pole (kan haap) with two baskets, bobbing at twice the step, y = a·|sin φ| */
function pole(c, M, u, ph, dir, load, nt) {
  var sx = M.sh[0], sy = M.sh[1] - u * 0.02, bob = Math.abs(Math.sin(ph)) * u * 0.03, L = u * 0.5;
  line(c, [[sx - L, sy + bob], [sx + L, sy - bob]], nt ? '#6a5a3a' : '#b8a060', Math.max(1.5, u * 0.03));
  [-1, 1].forEach(function (sd) { var ex = sx + sd * L * 0.92, ey = sy - sd * bob + u * 0.02, by = ey + u * 0.3;
    line(c, [[ex - u * 0.08, by - u * 0.05], [ex, ey], [ex + u * 0.08, by - u * 0.05]], '#5a4a30', 0.8);
    flat(c, [[ex - u * 0.11, by - u * 0.06], [ex + u * 0.11, by - u * 0.06], [ex + u * 0.08, by + u * 0.12], [ex - u * 0.08, by + u * 0.12]], nt ? '#5a4a30' : '#c8a060');
    if (load) { c.fillStyle = nt ? '#8a7030' : '#e8c050'; c.beginPath(); c.ellipse(ex, by - u * 0.06, u * 0.11, u * 0.05, 0, Math.PI, TAU); c.fill(); } });
}
function buffalo(c, x, y, s, t, nt) {
  var col = nt ? '#2a2a30' : '#4a4850', graze = 0.5 + 0.5 * Math.sin(t * 0.7);
  c.fillStyle = col; c.beginPath(); c.ellipse(x, y - s * 0.55, s * 0.7, s * 0.33, 0, 0, TAU); c.fill();
  [-0.5, -0.3, 0.35, 0.55].forEach(function (f) { c.fillRect(x + f * s - s * 0.05, y - s * 0.4, s * 0.1, s * 0.4); });
  var hx = x + s * 0.8, hy = y - s * (0.55 - graze * 0.35);
  c.beginPath(); c.ellipse(hx, hy, s * 0.22, s * 0.16, 0.6 * graze, 0, TAU); c.fill();
  c.strokeStyle = nt ? '#8a8478' : '#d8d0c0'; c.lineWidth = Math.max(1.5, s * 0.06); c.beginPath(); c.arc(hx - s * 0.05, hy - s * 0.12, s * 0.22, Math.PI * 1.05, Math.PI * 1.95); c.stroke();
  line(c, [[x - s * 0.68, y - s * 0.6], [x - s * 0.78 + Math.sin(t * 2) * s * 0.06, y - s * 0.2]], col, 1.5);
}
function lannaHouse(S) {
  var c = S.c, u0 = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, lk = look(S, LANNA), X = function (f) { return S.x0 + S.span * f; }, i, k;
  var L = {}, ph = S.phone;
  /* the main house fits under the clock: its height is about 2.9·u */
  function fitU(x0, x1, hgt) { return Math.min(u0 * (ph ? 1.15 : 1), (deck - cap(S, x0, x1) - 4) / hgt); }
  L = layer(S, 'lanna-' + lk, 0, S.H, function (q) {
    yard(q, S, 5);
    if (lk === 'kalae' || lk === 'parts') {
      var hx = X(lk === 'parts' ? (ph ? 0.4 : 0.36) : (ph ? 0.5 : 0.45)), w = Math.min(S.span * (ph ? 0.4 : 0.3), u0 * 2.6), u = fitU(hx - w * 0.8, hx + w * 0.8, 2.95), w2 = Math.min(w, u * 2.6);
      bushTree(q, X(0.06), deck, u * 2.2, nt, 3, '#4a8a4a');
      if (!ph) banana(q, X(0.16), deck, u * 1.3, nt);
      L.R = ruen(q, hx, deck, w2, u, { nt: nt, toen: -1, toenW: 0.62, door: true, post: 0.72 });
      L.u = u; L.hx = hx; L.w = w2;
      var gx = lk === 'parts' ? X(ph ? 0.72 : 0.6) : X(ph ? 0.88 : 0.8);
      fence(q, lk === 'parts' ? gx - u * 0.6 : X(ph ? 0.74 : 0.6), S.x1 + 4, deck + u * 0.05, u, nt);
      L.J = hanNam(q, gx, deck + u * 0.08, u * 0.9, nt);
      if (lk === 'parts') { var yx = X(ph ? 0.9 : 0.84), uy = Math.min(u, (deck - cap(S, yx - u * 0.6, yx + u * 0.6) - 4) / 2.1); L.Y = yung(q, yx, deck, u * 1.2 * uy / u, uy, { nt: nt }); }
      else palm(q, X(ph ? 0.96 : 0.95), deck, Math.min(u * 2.0, deck - cap(S, X(0.9), S.x1)), nt);
      /* the loom under the house */
      var lx = hx + w2 * 0.12, fl = L.R.fl, ly = deck;
      line(q, [[lx - u * 0.3, ly], [lx - u * 0.3, fl + u * 0.08]], teak(nt).post, 2); line(q, [[lx + u * 0.35, ly], [lx + u * 0.35, fl + u * 0.08]], teak(nt).post, 2);
      line(q, [[lx - u * 0.35, fl + u * 0.12], [lx + u * 0.4, fl + u * 0.12]], teak(nt).post, 2);
      q.strokeStyle = nt ? 'rgba(220,210,190,.5)' : 'rgba(250,245,230,.85)'; q.lineWidth = 0.6; q.beginPath(); for (k = 0; k < 9; k++) { q.moveTo(lx - u * 0.05 + k * u * 0.035, fl + u * 0.14); q.lineTo(lx - u * 0.12 + k * u * 0.05, ly - u * 0.28); } q.stroke();
      for (k = 0; k < 5; k++) { q.fillStyle = ['#7a1f3a', '#2a3a6a', '#e8b84a', '#7a1f3a', '#1f5a4a'][k]; q.fillRect(lx - u * 0.12, ly - u * 0.28 + k * u * 0.03, u * 0.4, u * 0.03); }
      L.loom = [lx, ly];
    } else if (lk === 'granary') {
      /* the paddy behind, cut and stooked; the granary; the house beside */
      for (k = 0; k < 3; k++) paper(q, rect(S.x0, deck - u * (0.3 - k * 0.08), S.span, u * 0.1), nt ? '#3a3420' : ['#d8b860', '#c8a850', '#e0c070'][k], 0.4);
      for (k = 0; k < 9; k++) { var sx = S.x0 + S.span * (0.05 + k * 0.11), sy = deck - u * 0.2; paper(q, poly([[sx - u * 0.1, sy], [sx, sy - u * 0.28], [sx + u * 0.1, sy]]), nt ? '#5a4a28' : '#e8c060', 0.5); }
      var hx2 = X(ph ? 0.14 : 0.14), u2 = fitU(hx2 - u0, hx2 + u0, 2.95) * 0.82;
      L.H = ruen(q, hx2, deck, u2 * 2.3, u2, { nt: nt, door: true });
      var gx2 = X(ph ? 0.58 : 0.52), ug = Math.min(u0 * (ph ? 1.2 : 1.15), (deck - cap(S, gx2 - u0, gx2 + u0) - 4) / 2.05);
      L.Y = yung(q, gx2, deck, ug * 1.55, ug, { nt: nt }); L.ug = ug; L.gx = gx2;
      if (!ph) bushTree(q, X(0.9), deck, Math.min(u0 * 1.7, deck - cap(S, X(0.84), X(0.96))), nt, 7, '#4f8f4a');
    } else if (lk === 'street') {
      var tg = X(ph ? 0.5 : 0.5), tu = Math.min(u0, (deck - cap(S, tg - u0, tg + u0) - 4) / 3.1);
      wihan(q, tg + tu * 0.2, deck - u0 * 0.55, tu * 2.6, tu * 2.0, tu, nt);
      paper(q, rect(S.x0, deck - u0 * 0.55, S.span, u0 * 0.06), nt ? '#8a8478' : '#f1ebdd', 0.6);
      khong(q, tg, deck - u0 * 0.3, tu * 1.3, tu * 1.7, tu, nt);
      var h1 = X(ph ? 0.14 : 0.16), u3 = fitU(h1 - u0, h1 + u0, 2.9) * (ph ? 0.85 : 0.9);
      L.A = ruen(q, h1, deck + u0 * 0.05, u3 * 2.5, u3, { nt: nt, twin: true, door: true, post: 0.65 });
      var h2x = X(ph ? 0.86 : 0.84), u4 = fitU(h2x - u0 * 1.2, h2x + u0 * 1.2, 2.9) * 0.95;
      L.B = ruen(q, h2x, deck + u0 * 0.05, u4 * 2.2, u4, { nt: nt, door: true, post: 0.6 });
      fence(q, S.x0, h1 - u3 * 1.3, deck + u0 * 0.1, u0, nt); fence(q, h1 + u3 * 1.3, tg - tu * 0.8, deck + u0 * 0.1, u0, nt); fence(q, tg + tu * 0.8, h2x - u4 * 1.2, deck + u0 * 0.1, u0, nt);
      if (!ph) { banana(q, X(0.36), deck + u0 * 0.1, u0 * 1.1, nt); banana(q, X(0.66), deck + u0 * 0.1, u0 * 1.0, nt); }
      L.J = hanNam(q, X(ph ? 0.33 : 0.37), deck + u0 * 0.12, u0 * 0.75, nt);
    } else if (lk === 'khantok') {
      var hx3 = X(ph ? 0.2 : 0.2), u5 = fitU(hx3 - u0, hx3 + u0, 2.95);
      bushTree(q, X(0.03), deck, u5 * 2.4, nt, 11, '#3f7f42');
      L.R = ruen(q, hx3, deck, u5 * 2.2, u5, { nt: nt, toen: 1, toenW: ph ? 1.05 : 1.45, door: true, post: 0.62 });
      L.u = u5;
      if (!ph) palm(q, X(0.93), deck, Math.min(u0 * 1.9, deck - cap(S, X(0.88), S.x1) - 2), nt);
    } else {   /* 'build': the frame on its posts; the old house and its granary behind */
      var bu = fitU(X(0.0), X(0.25), 2.9) * 0.7;
      L.old = ruen(q, X(0.1), deck - u0 * 0.15, bu * 2.2, bu, { nt: nt, door: true });
      var fx0 = X(ph ? 0.3 : 0.36), fx1 = X(ph ? 0.72 : 0.62), ft = deck - u0 * 1.95, P = teak(nt);
      ft = Math.max(ft, cap(S, fx0, fx1) + u0 * 0.2);
      L.f = { x0: fx0, x1: fx1, top: ft };
      paper(q, rect(fx0 - u0 * 0.06, ft, u0 * 0.12, deck - ft), P.post, 1);
      paper(q, rect((fx0 + fx1) / 2 - u0 * 0.06, ft, u0 * 0.12, deck - ft), P.post, 1);
      paper(q, rect(fx0 - u0 * 0.2, ft + u0 * 0.06, (fx1 - fx0) / 2 + u0 * 0.35, u0 * 0.1), P.wall, 1);
      paper(q, rect(fx0 - u0 * 0.2, deck - u0 * 0.72, fx1 - fx0 + u0 * 0.4, u0 * 0.09), P.wall, 1);
      [[fx0, ft + u0 * 0.11], [(fx0 + fx1) / 2, ft + u0 * 0.11], [fx0, deck - u0 * 0.675], [(fx0 + fx1) / 2, deck - u0 * 0.675]].forEach(function (p) { q.fillStyle = nt ? '#c8a050' : '#f0d090'; q.fillRect(p[0] - u0 * 0.03, p[1] - u0 * 0.03, u0 * 0.06, u0 * 0.06); });
      /* over the finished half, the gable's rafters and the kalae already pegged on; shingles going on the near plane */
      var rm = (fx0 + fx1) / 2, rax = (fx0 + rm) / 2, ray = ft - u0 * 0.78, re0 = fx0 - u0 * 0.38, re1 = rm + u0 * 0.38, rey = ft + u0 * 0.12;
      paper(q, poly([[re0, rey], [rax, ray], [rax + u0 * 0.02, ray + u0 * 0.16], [re0 + u0 * 0.14, rey + u0 * 0.04]]), P.tile, 1.2);
      q.strokeStyle = 'rgba(0,0,0,.3)'; q.lineWidth = 0.8; q.beginPath(); for (k = 1; k < 8; k++) { var fk = k / 8; q.moveTo(lerp(re0, rax, fk), lerp(rey, ray, fk)); q.lineTo(lerp(re0 + u0 * 0.14, rax + u0 * 0.02, fk), lerp(rey + u0 * 0.04, ray + u0 * 0.16, fk)); } q.stroke();
      q.save(); q.lineCap = 'round'; q.strokeStyle = P.board; q.lineWidth = Math.max(2, u0 * 0.06);
      q.beginPath(); q.moveTo(re1, rey); q.lineTo(rax, ray); q.moveTo(rax, ray); q.lineTo(rax, ft + u0 * 0.06); for (k = 1; k < 4; k++) { var fr = k / 4; q.moveTo(rax, lerp(ray, ft, fr)); q.lineTo(lerp(rax, re1, fr), lerp(ray, rey, fr)); } q.stroke();
      q.lineWidth = Math.max(1.2, u0 * 0.035); q.beginPath(); q.moveTo(re0 + u0 * 0.2, ft + u0 * 0.06); q.lineTo(re1 - u0 * 0.2, ft + u0 * 0.06); q.stroke(); q.restore();
      q.save(); q.shadowColor = 'rgba(0,0,0,.4)'; q.shadowBlur = 3; q.shadowOffsetX = 1; q.shadowOffsetY = 2;
      horn(q, rax - u0 * 0.02, ray + u0 * 0.05, 1, u0 * 0.42, u0 * 0.11, P.board, P.horn); horn(q, rax + u0 * 0.02, ray + u0 * 0.05, -1, u0 * 0.42, u0 * 0.11, P.board, P.horn); q.restore();
      /* the main post's blessing: cloth of three colours, a banana stem and sugarcane tied on */
      var mp = (fx0 + fx1) / 2; ['#d9342b', '#f2f2f2', '#e8b84a'].forEach(function (cc, j) { q.fillStyle = cc; q.fillRect(mp - u0 * 0.08, ft + u0 * (0.35 + j * 0.06), u0 * 0.16, u0 * 0.06); });
      line(q, [[mp + u0 * 0.09, deck], [mp + u0 * 0.11, ft + u0 * 0.3]], nt ? '#4a5a2a' : '#7a9a3a', Math.max(2, u0 * 0.05));
      for (k = 0; k < 3; k++) paper(q, function (p) { p.save(); p.translate(mp + u0 * 0.11, ft + u0 * 0.32); p.rotate(-0.6 + k * 0.6); p.beginPath(); p.ellipse(0, -u0 * 0.2, u0 * 0.05, u0 * 0.22, 0, 0, TAU); p.restore(); }, nt ? '#1e3a24' : '#5fa35a', 0.5);
      line(q, [[mp - u0 * 0.1, deck], [mp - u0 * 0.12, ft + u0 * 0.25]], nt ? '#5a4a3a' : '#b89a6a', Math.max(1.5, u0 * 0.03));
      /* the stack of timber, the sawhorses */
      for (k = 0; k < 4; k++) paper(q, rect(X(ph ? 0.76 : 0.72) - u0 * 0.1, deck - u0 * (0.09 + k * 0.09), u0 * 1.1 - k * u0 * 0.08, u0 * 0.08), P.board, 0.5);
      [X(ph ? 0.8 : 0.82), X(ph ? 0.95 : 0.93)].forEach(function (sx2) { line(q, [[sx2 - u0 * 0.1, deck + u0 * 0.3], [sx2, deck - u0 * 0.05], [sx2 + u0 * 0.1, deck + u0 * 0.3]], P.post, 2); });
      paper(q, rect(X(ph ? 0.78 : 0.8), deck - u0 * 0.11, X(ph ? 0.97 : 0.95) - X(ph ? 0.78 : 0.8), u0 * 0.08), P.board, 0.6);
    }
    return L;
  });
  var crew = town(S, 10, { sin: 0.45, mohom: 0.35, casual: 0.2 }), ci = 0, u = L.u || u0;
  /* lamplight in the windows after dark */
  [L.R, L.H, L.A, L.B, L.old].forEach(function (R, j) { if (!R || !nt) return; R.wins.forEach(function (w, k2) { glow(c, w[0] + w[2] / 2, w[1] + w[3] / 2, w[3] * 1.4, 35, 0.55 + 0.1 * Math.sin(t * 3 + k2 + j)); c.fillStyle = 'rgba(255,200,110,.85)'; c.fillRect(w[0], w[1], w[2], w[3]); }); });
  /* frangipani flowers fall now and then, x = x₀ + a·sin ωt, y = y₀ + vt */
  for (k = 0; k < (ph ? 3 : 5); k++) { var fp = frac(t / 7 + k * 0.29), fx = S.x0 + S.span * frac(0.13 + k * 0.23) + Math.sin(fp * 9 + k) * u * 0.25, fy = deck - u * 2.2 + fp * u * 2.3;
    if (fy < cap(S, fx - 4, fx + 4) || fp > 0.95) continue; c.fillStyle = nt ? 'rgba(240,235,220,.7)' : '#fffaf0'; for (i = 0; i < 5; i++) { var a = i / 5 * TAU + fp * 6; c.beginPath(); c.ellipse(fx + Math.cos(a) * u * 0.03, fy + Math.sin(a) * u * 0.03, u * 0.03, u * 0.015, a, 0, TAU); c.fill(); } dot(c, fx, fy, u * 0.015, '#f2c94c'); }
  if (lk === 'kalae' || lk === 'parts') {
    var R = L.R, J = L.J;
    /* the weaver: the shuttle runs across, x = A·sin ωt; the beater swings in after each pass */
    var wv = crew[ci++]; wv.garb = 'sin'; wv.hair = 2;
    var sh = Math.sin(t * 1.6), beat = Math.max(0, Math.cos(t * 1.6 * 2)), lx = L.loom[0], ly = L.loom[1];
    fig(S, wv, lx - u * 0.45, ly, u * 0.82, { lean: 0.1 - beat * 0.08, seat: 0.24, legs: POSE.sit.legs, arms: [1.4 + sh * 0.3, 0.3, 1.3 - beat * 0.3, 0.5] }, 1);
    flat(c, [[lx - u * 0.12 + (sh + 1) * u * 0.18, ly - u * 0.32], [lx - u * 0.02 + (sh + 1) * u * 0.18, ly - u * 0.32], [lx - u * 0.04 + (sh + 1) * u * 0.18, ly - u * 0.29], [lx - u * 0.1 + (sh + 1) * u * 0.18, ly - u * 0.29]], '#e8b84a');
    line(c, [[lx - u * 0.15 + beat * u * 0.06, ly - u * 0.5], [lx - u * 0.15 + beat * u * 0.06, ly - u * 0.25]], teak(nt).post, 2);
    /* hens about the yard */
    for (k = 0; k < 3; k++) { var hxk = R.x0 + (R.x1 - R.x0) * (0.2 + k * 0.32) + Math.sin(t * 0.3 + k * 2) * u * 0.25; hen(c, hxk, deck + u * (0.25 + (k % 2) * 0.2), u * 0.2, t, k * 2.1, ['#a8432f', '#f2ead8', '#6a4a2a'][k], Math.cos(t * 0.3 + k * 2) > 0 ? 1 : -1); }
    /* the passer-by: walks in, stops at the jar, dips and drinks, walks on (a 16 s round) */
    var cyc = frac(t / 16), jx = J.jar[0], pxx, act = 0, dir2 = -1, wk = crew[ci++];
    if (cyc < 0.35) pxx = lerp(S.x1 + u * 0.6, jx + u * 0.42, ease(cyc / 0.35)); else if (cyc < 0.6) { pxx = jx + u * 0.42; act = (cyc - 0.35) / 0.25; } else pxx = lerp(jx + u * 0.42, S.x0 + S.span * 0.3, (cyc - 0.6) / 0.4);
    var walking = cyc < 0.35 || cyc >= 0.6, drink = act > 0 ? Math.sin(Math.min(1, act * 1.6) * Math.PI) : 0;
    var Wk = fig(S, wk, pxx, deck + u * 0.32, u * 0.92, walking ? walkP(t * TAU * 0.6) : { lean: 0.05, legs: [0.05, 0, -0.05, 0], arms: [0.4 + drink * 2.1, 0.3 + drink * 1.2, 0.15, 0.1] }, dir2);
    if (!walking && act > 0.05 && act < 0.95) dipper(c, Wk.hand[0][0], Wk.hand[0][1], Math.PI - 0.5 + drink * 1.5, u, nt); else dipper(c, J.hook[0], J.hook[1], Math.PI / 2 - 0.2 + Math.sin(t) * 0.05, u * 0.9, nt);
    /* a lantern on the terrace by night */
    if (R.toen) { var tlx = (R.toen.x0 + R.toen.x1) / 2, tly = R.toen.roof + u * 0.04, sa = swing(t, 0.4, 0.08, 1); c.save(); c.translate(tlx, tly); c.rotate(sa); hangItem(c, { kind: 'khom', len: 0.25, col: '#f2c94c' }, u * 0.7, nt); c.restore(); if (nt) glow(c, tlx, tly + u * 0.25, u * 0.6, 42, 0.75); }
    if (lk === 'parts') {
      var G = R.gables[0];
      tag(S, G.apex[0] - u * 1.35, G.apex[1] - u * 0.3, G.horn[0] - u * 0.06, G.horn[1] + u * 0.05, 'กาแล · kalae', u, t, 0);
      tag(S, G.apex[0] + u * 1.55, G.apex[1] + u * 0.3, R.hamyon[0] + u * 0.08, R.hamyon[1] - u * 0.04, 'หำยนต์ · ham yon', u, t, 1);
      if (R.toen) tag(S, (R.toen.x0 + R.toen.x1) / 2, R.fl + u * 0.42, (R.toen.x0 + R.toen.x1) / 2, R.fl - u * 0.12, 'เติ๋น · toen', u, t, 2);
      if (L.Y) tag(S, Math.min(L.Y.x0 + u * 0.3, S.x1 - u * 0.9), deck + u * 0.45, L.Y.x0 + u * 0.3, L.Y.fl - u * 0.3, 'ยุ้งข้าว · rice granary', u, t, 3);
      tag(S, J.jar[0], J.top - u * 0.4, J.jar[0], J.jar[1] - u * 0.05, 'หม้อน้ำ · water jar', u, t, 4);
    }
    label(S, X(0.12), R.gables[0].apex[1] - u * 1.55, '#a8432f');
  } else if (lk === 'granary') {
    var Y = L.Y, ug = L.ug;
    buffalo(c, X(ph ? 0.85 : 0.8), deck - u0 * 0.1, u0 * 0.55, t, nt);
    /* on the ladder's head someone tips the basket in; grains fall in an arc, y = y₀ + ½gτ² */
    var lad = Y.ladder, tp = frac(t / 4), tip = Math.sin(Math.min(1, tp * 2) * Math.PI), pr = crew[ci++]; pr.garb = 'mohom'; pr.col = '#2c3e6b'; pr.hat = true;
    var lpx = lerp(lad[0], lad[2], 0.72) + ug * 0.15, lpy = lerp(lad[1], lad[3], 0.72);
    var Pr = fig(S, pr, lpx, lpy, ug * 0.85, { lean: -0.3 - tip * 0.25, legs: [0.4, -0.5, -0.2, 0.2], arms: [2.3 + tip * 0.6, 0.6, 2.2 + tip * 0.6, 0.7] }, -1);
    var bh = Pr.hand[0]; c.save(); c.translate(bh[0], bh[1]); c.rotate(-tip * 1.1); flat(c, [[-ug * 0.13, -ug * 0.05], [ug * 0.13, -ug * 0.05], [ug * 0.1, ug * 0.14], [-ug * 0.1, ug * 0.14]], nt ? '#5a4a30' : '#c8a060'); c.restore();
    if (tip > 0.3) for (k = 0; k < 10; k++) { var tau = frac(t * 2.5 + k / 10) * 0.25, gxx = bh[0] - ug * 0.12 - tau * ug * 0.8, gyy = bh[1] + 9.8 * tau * tau * ug * 0.9; if (gyy < Y.sill[1]) dot(c, gxx, gyy, Math.max(0.8, ug * 0.018), nt ? '#a88a3a' : '#f2c94c'); }
    /* two carry paddy in on shoulder poles; one goes back for more */
    for (k = 0; k < (ph ? 2 : 3); k++) { var back = k === 2, v = u0 * 0.3, Lp = Math.max(u0, (lad[0] - S.x0) + u0 * 0.5), off = (t * v + k * Lp * 0.5) % Lp, cx = back ? lad[0] - u0 * 0.3 - off : S.x0 - u0 * 0.5 + off, d = crew[ci++];
      var Mc = fig(S, d, cx, deck + u0 * (0.25 + k * 0.12), u0 * 0.9, { lean: 0.06, legs: walkP(t * TAU * 0.6 + k).legs, arms: [2.6, 0.5, 0.3, 0.2] }, back ? -1 : 1);
      pole(c, Mc, u0, t * TAU * 0.6 + k, back ? -1 : 1, !back, nt); }
    label(S, X(0.86), deck - u0 * 2.2, '#c89a3a');
  } else if (lk === 'street') {
    /* a monk with his bowl, slow; a girl on a bicycle; a woman with a shoulder pole; a dog */
    var mk = crew[ci++]; mk.garb = 'casual'; mk.long = true; mk.col = '#e07a1a'; mk.low = '#e07a1a'; mk.hairCol = mk.skin; mk.hair = 0; mk.hat = false;
    var Lp2 = S.span + u0 * 2, mx = S.x1 + u0 - ((t * u0 * 0.12 + 40) % Lp2);
    var Mk = fig(S, mk, mx, deck + u0 * 0.32, u0 * 0.95, { lean: 0.03, legs: walkP(t * TAU * 0.35).legs, arms: [0.9, 0.9, 0.15, 0.1] }, -1);
    line(c, [[Mk.sh[0] - u0 * 0.06, Mk.sh[1]], [Mk.hip[0] + u0 * 0.06, Mk.hip[1]]], '#b85a10', Math.max(1.5, u0 * 0.04));
    c.fillStyle = '#2a2a30'; c.beginPath(); c.arc(Mk.hand[0][0], Mk.hand[0][1] + u0 * 0.02, u0 * 0.08, 0, Math.PI); c.fill();
    var bv = u0 * 0.9, bxp = S.x0 - u0 + ((t * bv) % (S.span + u0 * 2)), by0 = deck + u0 * 0.6, rr = u0 * 0.17, ang = bxp / rr;
    [bxp - u0 * 0.27, bxp + u0 * 0.27].forEach(function (wx) { c.strokeStyle = '#2a2a30'; c.lineWidth = 1.6; c.beginPath(); c.arc(wx, by0 - rr, rr, 0, TAU); c.stroke(); line(c, [[wx, by0 - rr], [wx + Math.cos(ang) * rr, by0 - rr + Math.sin(ang) * rr]], '#888', 0.8); });
    line(c, [[bxp - u0 * 0.27, by0 - rr], [bxp - u0 * 0.05, by0 - rr * 2.2], [bxp + u0 * 0.2, by0 - rr * 2.2], [bxp + u0 * 0.27, by0 - rr], [bxp, by0 - rr], [bxp - u0 * 0.05, by0 - rr * 2.2]], '#d9342b', 2);
    var kid = crew[ci++]; kid.garb = 'casual'; kid.col = '#f2f2f2';
    fig(S, kid, bxp - u0 * 0.06, by0 - rr * 2.3 + u0 * 0.72 * 0.47, u0 * 0.72, { lean: 0.2, legs: [1.2 + Math.sin(ang) * 0.4, -1.2, 1.2 - Math.sin(ang) * 0.4, -1.2], arms: [1.3, 0.1, 1.2, 0.2] }, 1);
    var wm = crew[ci++], wx2 = S.x0 - u0 + ((t * u0 * 0.22 + S.span * 0.5) % (S.span + u0 * 2));
    var Wm = fig(S, wm, wx2, deck + u0 * 0.18, u0 * 0.88, { lean: 0.05, legs: walkP(t * TAU * 0.55).legs, arms: [2.6, 0.5, 0.3, 0.2] }, 1); pole(c, Wm, u0, t * TAU * 0.55, 1, true, nt);
    var dgx = mx + u0 * 0.9, dgy = deck + u0 * 0.5, trot = Math.sin(t * 8);
    flat(c, [[dgx - u0 * 0.22, dgy - u0 * 0.22], [dgx + u0 * 0.15, dgy - u0 * 0.22], [dgx + u0 * 0.15, dgy - u0 * 0.1], [dgx - u0 * 0.22, dgy - u0 * 0.1]], nt ? '#5a4a3a' : '#c89a5a');
    dot(c, dgx - u0 * 0.26, dgy - u0 * 0.26, u0 * 0.07, nt ? '#5a4a3a' : '#c89a5a');
    line(c, [[dgx - u0 * 0.18, dgy - u0 * 0.1], [dgx - u0 * 0.18 + trot * u0 * 0.04, dgy]], nt ? '#5a4a3a' : '#c89a5a', 2); line(c, [[dgx + u0 * 0.12, dgy - u0 * 0.1], [dgx + u0 * 0.12 - trot * u0 * 0.04, dgy]], nt ? '#5a4a3a' : '#c89a5a', 2);
    line(c, [[dgx + u0 * 0.15, dgy - u0 * 0.2], [dgx + u0 * 0.25, dgy - u0 * 0.3 + Math.sin(t * 10) * u0 * 0.03]], nt ? '#5a4a3a' : '#c89a5a', 2);
    if (nt) [L.A, L.B].forEach(function (R2) { var lx2 = R2.x1, ly2 = R2.wt + u0 * 0.2; glow(c, lx2, ly2, u0 * 0.4, 42, 0.7); dot(c, lx2, ly2, u0 * 0.04, '#fff2c0'); });
    label(S, X(0.2), Math.min(L.A.top, L.B.top) - u0 * 0.5, '#2f6a3a');
  } else if (lk === 'khantok') {
    var R3 = L.R, T = R3.toen, tx = (T.x0 + T.x1) / 2, fy2 = T.fl - u * 0.05, tw = T.x1 - T.x0;
    /* the khantok: a round red lacquer tray on its stand, dishes, sticky rice baskets */
    flat(c, [[tx - u * 0.1, fy2], [tx + u * 0.1, fy2], [tx + u * 0.06, fy2 - u * 0.12], [tx - u * 0.06, fy2 - u * 0.12]], nt ? '#5a1410' : '#a8261c');
    c.fillStyle = nt ? '#6a1a14' : '#c0302a'; c.beginPath(); c.ellipse(tx, fy2 - u * 0.14, u * 0.4, u * 0.07, 0, 0, TAU); c.fill();
    c.strokeStyle = '#e8b84a'; c.lineWidth = 1; c.beginPath(); c.ellipse(tx, fy2 - u * 0.14, u * 0.4, u * 0.07, 0, 0, TAU); c.stroke();
    for (k = 0; k < 5; k++) { var dxk = tx + (k - 2) * u * 0.15; c.fillStyle = '#f2ece0'; c.beginPath(); c.ellipse(dxk, fy2 - u * 0.17, u * 0.065, u * 0.03, 0, 0, TAU); c.fill(); c.fillStyle = ['#c0392b', '#7a4a2a', '#6aa84a', '#e8a040', '#d9342b'][k]; c.beginPath(); c.ellipse(dxk, fy2 - u * 0.18, u * 0.045, u * 0.018, 0, 0, TAU); c.fill(); }
    [-1, 1].forEach(function (sd) { var kx = tx + sd * u * 0.36; flat(c, [[kx - u * 0.04, fy2 - u * 0.15], [kx + u * 0.04, fy2 - u * 0.15], [kx + u * 0.05, fy2 - u * 0.3], [kx, fy2 - u * 0.36], [kx - u * 0.05, fy2 - u * 0.3]], nt ? '#6a5430' : '#d4aa60'); });
    var cand = 0.85 + 0.15 * Math.sin(t * 11); if (nt) glow(c, tx, fy2 - u * 0.3, u * 0.55, 38, 0.45 * cand); line(c, [[tx, fy2 - u * 0.17], [tx, fy2 - u * 0.27]], '#f2ece0', 2); flat(c, [[tx - u * 0.02, fy2 - u * 0.27], [tx + Math.sin(t * 7) * u * 0.01, fy2 - u * 0.36 * cand], [tx + u * 0.02, fy2 - u * 0.27]], '#ffcf4a');
    /* the family round it, eating with their fingers: a hand goes tray → mouth every few seconds */
    var seats = ph ? [-0.85, -0.5, 0.5, 0.85] : [-0.95, -0.62, -0.3, 0.3, 0.62, 0.95];
    seats.forEach(function (sf, j) { var d = crew[ci++], sx = tx + sf * Math.min(tw * 0.45, u * 0.95), dir = sf < 0 ? 1 : -1, eat = Math.max(0, Math.sin(t * 1.3 + j * 1.7)), sc = j % 3 === 2 ? 0.75 : 0.88;
      fig(S, d, sx, fy2 + u * 0.04, u * sc, { lean: 0.1 + eat * 0.1, seat: 0.12, legs: POSE.lotus.legs, arms: [0.7 + eat * 0.9, 1.4 - eat * 0.2, 0.9, 0.5] }, dir); });
    /* khom lanterns along the terrace's eave */
    for (k = 0; k < (ph ? 2 : 4); k++) { var kx2 = T.x0 + tw * (0.15 + k * (ph ? 0.7 : 0.23)), ky2 = T.roof + u * 0.02, sa2 = swing(t, 0.5, 0.08, k);
      c.save(); c.translate(kx2, ky2); c.rotate(sa2); hangItem(c, { kind: k % 2 ? 'khom' : 'lanternR', len: 0.2, col: ['#f2c94c', '#e5567f'][k % 2] }, u * 0.65, nt); c.restore(); if (nt) glow(c, kx2, ky2 + u * 0.22, u * 0.32, k % 2 ? 42 : 15, 0.45); }
    /* below, a woman brings another dish up to the steps */
    var bp = frac(t / 10), bgo = bp < 0.5, bx3 = lerp(S.x1 - u * 0.4, (R3.steps ? R3.steps[1] : T.x1) + u * 0.25, ease(bgo ? bp * 2 : 2 - bp * 2)), dw = crew[ci++]; dw.garb = 'sin';
    var Dw = fig(S, dw, bx3, deck + u * 0.3, u * 0.92, { lean: 0.03, legs: walkP(t * TAU * 0.6).legs, arms: [1.5, -1.3, 0.25, 0.2] }, bgo ? -1 : 1);
    if (bgo) { c.fillStyle = '#f2ece0'; c.beginPath(); c.ellipse(Dw.hand[0][0], Dw.hand[0][1] - u * 0.02, u * 0.12, u * 0.035, 0, 0, TAU); c.fill(); c.fillStyle = '#c0392b'; c.beginPath(); c.ellipse(Dw.hand[0][0], Dw.hand[0][1] - u * 0.04, u * 0.07, u * 0.025, 0, 0, TAU); c.fill(); if (!nt) steam(c, Dw.hand[0][0], Dw.hand[0][1] - u * 0.07, u * 0.3, t, 2, 'rgba(255,255,255,.5)'); }
    var dog = R3.x0 + (R3.x1 - R3.x0) * 0.5, dgy2 = deck - u * 0.02, br = 1 + 0.04 * Math.sin(t * 1.5);
    c.fillStyle = nt ? '#5a4a3a' : '#c89a5a'; c.beginPath(); c.ellipse(dog, dgy2 - u * 0.08, u * 0.24, u * 0.09 * br, 0, 0, TAU); c.fill(); dot(c, dog - u * 0.25, dgy2 - u * 0.08, u * 0.08, nt ? '#5a4a3a' : '#c89a5a');
    label(S, X(0.66), deck - u0 * 2.35, '#a8261c');
  } else {
    /* 'build': a post raised on a rope over an A-frame, θ easing from lying to upright, ⟳ 10 s;
       a carpenter knocks pegs home with a mallet; another saws */
    var F = L.f, px = F.x1, pl = deck - F.top, cy2 = frac(t / 10), up = ease(Math.max(0, Math.min(1, (cy2 - 0.08) / 0.6))), th = (1 - up) * 1.25, fade = cy2 > 0.92 ? 1 - (cy2 - 0.92) / 0.08 : 1;
    var tx2 = px + Math.sin(th) * pl, ty2 = deck - Math.cos(th) * pl, P2 = teak(nt);
    c.save(); c.globalAlpha = fade; c.translate(px, deck); c.rotate(th); flat(c, [[-u0 * 0.06, 0], [u0 * 0.06, 0], [u0 * 0.06, -pl], [-u0 * 0.06, -pl]], P2.post); c.fillStyle = nt ? '#c8a050' : '#f0d090'; c.fillRect(-u0 * 0.03, -pl + u0 * 0.08, u0 * 0.06, u0 * 0.06); c.restore();
    var af = (F.x0 + F.x1) / 2 - u0 * 0.15, at = F.top - u0 * 0.25;
    line(c, [[af - u0 * 0.35, deck], [af, at], [af + u0 * 0.35, deck]], nt ? '#6a6a3a' : '#a8a060', Math.max(1.5, u0 * 0.035));
    var pullX = X(ph ? 0.12 : 0.2) + up * u0 * 0.3;
    line(c, [[tx2, ty2], [af, at], [pullX + u0 * 0.3, deck - u0 * 0.5]], '#d8c8a0', 1.2);
    for (k = 0; k < 2; k++) { var dpu = crew[ci++]; dpu.garb = 'mohom'; dpu.col = '#2c3e6b'; var pxx2 = pullX + k * u0 * 0.35, step = Math.sin(t * 4 + k);
      fig(S, dpu, pxx2, deck + u0 * 0.2, u0 * 0.9, { lean: -0.35, legs: [0.4 + step * 0.15, -0.2, -0.3 - step * 0.15, 0], arms: [1.7, -0.2, 1.6, -0.1] }, 1); }
    var hm = Math.max(0, Math.sin(t * 5)), cp = crew[ci++]; cp.garb = 'casual'; cp.col = '#e8e2d0'; cp.hat = true;
    var lx3 = F.x0 + u0 * 0.35; line(c, [[lx3 + u0 * 0.1, deck], [F.x0 + u0 * 0.05, F.top + u0 * 0.5]], P2.post, 1.6); line(c, [[lx3 + u0 * 0.25, deck], [F.x0 + u0 * 0.2, F.top + u0 * 0.5]], P2.post, 1.6);
    var Cp = fig(S, cp, F.x0 + u0 * 0.3, F.top + u0 * 0.95, u0 * 0.85, { lean: 0.1, legs: [0.3, -0.4, -0.1, 0.1], arms: [2.8 - hm * 1.4, 0.3, 1.9, 0.3] }, -1);
    var mh = Cp.hand[0]; line(c, [[mh[0], mh[1]], [mh[0] - u0 * 0.06, mh[1] - u0 * 0.06]], '#6a4a2a', 2); flat(c, [[mh[0] - u0 * 0.12, mh[1] - u0 * 0.1], [mh[0] - u0 * 0.02, mh[1] - u0 * 0.13], [mh[0] - u0 * 0.0, mh[1] - u0 * 0.06], [mh[0] - u0 * 0.1, mh[1] - u0 * 0.03]], '#8a5a2a');
    if (hm < 0.15) for (k = 0; k < 4; k++) dot(c, F.x0 + Math.cos(k * 1.6) * u0 * 0.1, F.top + u0 * 0.11 + Math.sin(k * 1.6) * u0 * 0.08, u0 * 0.015, '#f0d090');
    var sw2 = Math.sin(t * 6), sy2 = deck - u0 * 0.11, sx3 = X(ph ? 0.88 : 0.88), sd = crew[ci++]; sd.garb = 'mohom'; sd.col = '#2c3e6b';
    fig(S, sd, sx3 + u0 * 0.35, deck + u0 * 0.12, u0 * 0.9, { lean: 0.45, legs: [0.3, -0.3, -0.2, 0.1], arms: [1.6 + sw2 * 0.3, 0.2 - sw2 * 0.2, 1.4, 0.4] }, -1);
    line(c, [[sx3 + sw2 * u0 * 0.12 - u0 * 0.15, sy2 - u0 * 0.1], [sx3 + sw2 * u0 * 0.12 + u0 * 0.12, sy2 + u0 * 0.02]], '#c8ccd4', 2.2);
    for (k = 0; k < 5; k++) { var sp2 = frac(t * 1.7 + k / 5); dot(c, sx3 - u0 * 0.02 + Math.sin(k * 3) * u0 * 0.05, sy2 + sp2 * u0 * 0.35, u0 * 0.012, nt ? '#8a7050' : '#f0d8a0'); }
    if (hm < 0.15) { c.fillStyle = nt ? '#ffe8b0' : '#5a2a10'; c.font = '800 ' + Math.round(u0 * 0.16) + 'px ' + FONT; c.textAlign = 'center'; c.fillText('ป๊อก', F.x0 - u0 * 0.25, F.top - u0 * 0.05); }
    label(S, X(0.86), deck - u0 * 1.95, '#7a4a2a');
  }
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u0 * 2.4, y1: S.H });
}

/* ---------------------------------------------------------------- the words, the looks, the math */
D.variants.alley = chooser([
  ['muangmai', /muang ?mai|เมืองใหม่|wholesale|ขายส่ง|ตลาดเช้า|morning market|dawn/i],
  ['spice', /chinatown|ไชน่าทาวน์|ย่านจีน|spice|เครื่องเทศ|เล่าโจ๊ว|herbal|ยาจีน/i],
  ['bazaar', /chiang ?rai|เชียงราย|bazaar|บาซาร์/i],
  ['nightlane', /night|ไนท์|กลางคืน|ตลาดโต้รุ่ง|street food/i],
  ['kadluang', /kad ?luang|กาดหลวง|warorot|วโรรส|ต้นลำไย|ton ?lam ?yai/i]], ALLEY);
D.variants.rooftop = chooser([
  ['yipeng', /yi ?peng|yee ?peng|ยี่เป็ง|lo[iy] ?krathong|ลอยกระทง|lantern/i],
  ['salabar', /sky ?bar|skybar|bar\b|lounge|cocktail|บาร์|sundowner/i],
  ['crown', /pool|hotel|โรงแรม|สระ/i],
  ['mist', /sunrise|dawn|morning|breakfast|yoga|ตอนเช้า|พระอาทิตย์ขึ้น/i],
  ['cluster', /condo|towers|skyline|คอนโด/i]], ROOF);
D.variants['lanna-house'] = chooser([
  ['parts', /architecture|สถาปัตย|tour|museum|พิพิธภัณฑ์|เรือนโบราณ/i],
  ['granary', /granary|ยุ้ง|harvest|rice|ข้าว/i],
  ['khantok', /khantok|kantoke|ขันโตก|dinner|supper/i],
  ['build', /build|carpent|restor|craftsm|ช่างไม้|ยกเสา|บูรณะ/i],
  ['street', /village|street|lane|walk|หมู่บ้าน|ซอย/i]], LANNA);

D.addScene('alley', alley,
  /^(?![\s\S]*(chinese new year|lunar new year|ตรุษจีน|lion dance|dragon dance|เชิดสิงโต|vegetarian|kin ?je|กินเจ|walking street|ถนนคนเดิน))[\s\S]*(alley|ตรอก|soi market|kad ?luang|กาดหลวง|warorot|วโรรส|ต้นลำไย|ton ?lam ?yai|muang ?mai market|ตลาดเมืองใหม่|กาดเมืองใหม่|wholesale market|ตลาดเช้า|chinatown|ไชน่าทาวน์|ย่านจีน|night bazaar|ไนท์บาซาร์)/i,
  'θ = θ₀·sin(√(g/L)·t), the goods swing<br>x = x₀ ± vt, the lane', 1);
D.addScene('rooftop', rooftop,
  /^(?![\s\S]*(yoga|meditat|kirtan|โยคะ|สมาธิ|latin|salsa|bachata|ละติน))[\s\S]*(rooftop|roof ?top|sky ?bar|skybar|ดาดฟ้า|penthouse|(?<!clock |water )\btower\b)/i,
  '|i − i₀| + ½|j − j₀| = r(t), the windows<br>y = lerp(y₀, y₁, ease(u)), the lift', 1);
D.addScene('lanna-house', lannaHouse,
  /lanna (house|home|architecture|heritage|style|teak)|kalae|กาแล|เรือนล้านนา|เรือนกาแล|เรือนโบราณ|ยุ้งข้าว|rice granary|heritage house|teak house|บ้านไม้สัก|architecture tour|สถาปัตย/i,
  'B(s) = (1−s)²P₀ + 2s(1−s)P₁ + s²P₂, the kalae<br>y = y₀ + ½gτ², the grain', 1);
})();
