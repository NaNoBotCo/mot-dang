/* Spirit house portraits for the auto-doodler: a spirit house on its post (san phra phum) in the 5:2 frame
   on the page of the place it stands at. The five models, the morning tray and the garlands are ported from
   the Spirit House Manual minisite, https://motdang.net/sites/spirit-house/ (spirit-house/docs/assets/house.js,
   sky.js, app.js). The place's own name picks the model (deva, ta-yai, Brahma, Lanna wood, Chinese shrine),
   its colour and size, and a hint of where it stands (a showroom, a garage, a bar, a gate, greenery);
   the place's id deals the rest. The reader's Bangkok clock sets the tray: water, food and incense in the
   morning, water and a garland through the day, a lamp after dark. The still parts are cut once per size, seed
   and light into offscreen layers; each frame draws the smoke, the garlands, the flames, the dancers and the glints. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.addScene) return;
var K = D.kit, rnd = K.rnd, TAU = K.TAU, sin = Math.sin, cos = Math.cos, abs = Math.abs, max = Math.max, min = Math.min, sqrt = Math.sqrt, PI = Math.PI;
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function lerp(a, b, u) { return a + (b - a) * u; }
function pick(r, a) { return a[Math.floor(r() * a.length) % a.length]; }

/* ---------------------------------------------------------------- small cuts */
function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function hex(v) { return '#' + v.map(function (x) { x = Math.round(clamp(x, 0, 255)); return (x < 16 ? '0' : '') + x.toString(16); }).join(''); }
function mixc(a, b, u) { var p = rgb(a), q = rgb(b); return hex([lerp(p[0], q[0], u), lerp(p[1], q[1], u), lerp(p[2], q[2], u)]); }
function lum(h) { var v = rgb(h); return 0.3 * v[0] + 0.59 * v[1] + 0.11 * v[2]; }
function rgba(h, a) { var v = rgb(h); return 'rgba(' + v[0] + ',' + v[1] + ',' + v[2] + ',' + (+a).toFixed(3) + ')'; }
/* a polygon from a flat list, filled and outlined */
function pg(c, pts, fill, stroke, lw) {
  c.beginPath(); c.moveTo(pts[0], pts[1]); for (var i = 2; i < pts.length; i += 2) c.lineTo(pts[i], pts[i + 1]); c.closePath();
  if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw || 1; c.stroke(); }
}
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function dot(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, max(0.1, r), 0, TAU); c.fill(); }
function ov(c, x, y, rx, ry, col, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, max(0.1, rx), max(0.1, ry), rot || 0, 0, TAU); c.fill(); }
function ln(c, x0, y0, x1, y1, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); }
function rr(c, x, y, w, h, r, col) { r = min(r, w / 2, h / 2); c.fillStyle = col; c.beginPath(); c.moveTo(x + r, y); c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r); c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h); c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r); c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y); c.closePath(); c.fill(); }
function grad(c, x0, y0, x1, y1, stops) { var g = c.createLinearGradient(x0, y0, x1, y1); for (var i = 0; i < stops.length; i += 2) g.addColorStop(stops[i], stops[i + 1]); return g; }
function vgrad(c, y0, y1, a, b) { return grad(c, 0, y0, 0, y1, [0, a, 1, b]); }
function glowAt(c, x, y, r, col, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0)); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); }

/* ---------------------------------------------------------------- the still layers, cut once
   keyed by the canvas transform (size and DPR), the seed and the state; each hands back what it drew
   (the closures that move). A soft-shadowed paper lift for the house sits in lift(). */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : { a: 1, d: 1, e: 0, f: 0 }, k = key + '|' + [S.W, S.H, S.seed, S.phone ? 1 : 0, m.a, m.d, m.e, m.f].join(','), e = null, i;
  for (i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    if (typeof document === 'undefined') return { out: draw(c) };
    var cv = document.createElement('canvas'); cv.width = max(1, w); cv.height = max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    e = { k: k, cv: cv, ox: ox, oy: oy, out: draw(q) };
    CACHE.unshift(e); if (CACHE.length > 14) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
  return e;
}
/* draw fn on a scratch sheet and lay it down with one soft shadow under the whole cut-out */
function lift(q, dx, fn) {
  var m = q.getTransform(), cv = q.canvas, t = document.createElement('canvas'); t.width = cv.width; t.height = cv.height;
  var tq = t.getContext('2d'); tq.setTransform(m); var out = fn(tq);
  if (window.MDSKY && MDSKY.grain) { tq.save(); tq.setTransform(1, 0, 0, 1, 0, 0); tq.globalCompositeOperation = 'source-atop'; tq.globalAlpha = 0.5; tq.fillStyle = MDSKY.grain(tq); tq.fillRect(0, 0, t.width, t.height); tq.restore(); }
  q.save(); q.setTransform(1, 0, 0, 1, 0, 0); q.shadowColor = 'rgba(20,10,30,.34)'; q.shadowBlur = 5 * m.a; q.shadowOffsetX = dx * m.a; q.shadowOffsetY = 2.5 * m.a; q.drawImage(t, 0, 0); q.restore();
  return out;
}
/* the light's colour multiplied into what a layer holds (only where it holds something): warm at dawn and dusk, violet at twilight, navy by night; k = 1 full, less for the lit house */
var MULT = [null, [255, 208, 172], [152, 142, 208], [80, 92, 150]];
function tint(q, band, k) {
  var m = MULT[band]; if (!m || typeof document === 'undefined') return;
  k = k == null ? 1 : k;
  var cv = q.canvas, t = document.createElement('canvas'); t.width = cv.width; t.height = cv.height; var tq = t.getContext('2d');
  tq.drawImage(cv, 0, 0); tq.globalCompositeOperation = 'multiply'; tq.fillStyle = 'rgb(' + m.map(function (v) { return Math.round(255 - (255 - v) * k); }).join(',') + ')'; tq.fillRect(0, 0, t.width, t.height);
  tq.globalCompositeOperation = 'destination-in'; tq.drawImage(cv, 0, 0);
  q.save(); q.setTransform(1, 0, 0, 1, 0, 0); q.globalCompositeOperation = 'copy'; q.drawImage(t, 0, 0); q.restore();
}
var GLOW = null;   /* a white soft disc, tinted as it is laid */
function glowSprite() {
  if (GLOW || typeof document === 'undefined') return GLOW;
  var g = document.createElement('canvas'); g.width = g.height = 64; var q = g.getContext('2d'), rg = q.createRadialGradient(32, 32, 0, 32, 32, 32);
  rg.addColorStop(0, 'rgba(255,255,255,1)'); rg.addColorStop(0.3, 'rgba(255,255,255,.4)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); q.fillStyle = rg; q.fillRect(0, 0, 64, 64);
  GLOW = g; return g;
}
var GCACHE = {};
function glowTinted(col) {   /* the disc in one colour, cut once */
  if (GCACHE[col]) return GCACHE[col];
  var g = glowSprite(); if (!g) return null;
  var t = document.createElement('canvas'); t.width = t.height = 64; var q = t.getContext('2d'); q.fillStyle = col; q.fillRect(0, 0, 64, 64); q.globalCompositeOperation = 'destination-in'; q.drawImage(g, 0, 0);
  GCACHE[col] = t; return t;
}
/* a soft light laid on the frame, additive */
function lamp(c, x, y, r, col, a) { var g = glowTinted(col); if (!g) return; c.globalAlpha = clamp(a, 0, 1); c.drawImage(g, x - r, y - r, r * 2, r * 2); c.globalAlpha = 1; }
/* a four-point glint */
function twinkle(c, x, y, r) { c.beginPath(); c.moveTo(x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.fill(); }

/* ---------------------------------------------------------------- colours of the houses
   (the minisite's palettes, and a black and gold) */
var PAL = {
  gold: { body: '#e0ac2a', hi: '#ffe48a', lo: '#9a6b0c', trim: '#fff2b8', roof: '#d99a1c', dark: '#5a3606' },
  red: { body: '#c0392b', hi: '#ff7a5c', lo: '#7d1a12', trim: '#f2c14e', roof: '#a52a1f', dark: '#3f0b06' },
  white: { body: '#f6f2e8', hi: '#ffffff', lo: '#c9bfa8', trim: '#e0ac2a', roof: '#efe6d2', dark: '#6b5a3a' },
  blue: { body: '#3a78c2', hi: '#8cc2ff', lo: '#1f4a80', trim: '#ffffff', roof: '#2f63a3', dark: '#0e2442' },
  green: { body: '#3c9b6b', hi: '#9be3b9', lo: '#1f5e3d', trim: '#f2c14e', roof: '#2f7d55', dark: '#0d2b1b' },
  wood: { body: '#9a6236', hi: '#d29a62', lo: '#5c3418', trim: '#e9c58f', roof: '#6e4123', dark: '#2a160a' },
  clay: { body: '#c4673a', hi: '#ee9a6c', lo: '#7c3816', trim: '#f6d29a', roof: '#a9532b', dark: '#3a1806' },
  black: { body: '#33292a', hi: '#6a5a58', lo: '#171112', trim: '#e0ac2a', roof: '#241c1d', dark: '#0a0708' }
};

/* ---------------------------------------------------------------- the pieces of the houses (ported) */
/* an eave end: a log-spiral hook, the curvature κ(s) = a/(s+ε) integrated along the line */
function curl(c, x, y, len, dir, col, lw) {
  var th = -PI / 2 + dir * 0.9, px = x, py = y, n = 22, ds = len / n;
  c.beginPath(); c.moveTo(px, py);
  for (var i = 0; i < n; i++) { var s = i / n, kk = 0.4 + 6.5 * s * s; th += dir * kk * ds / len * 2.2; px += cos(th) * ds * dir; py += sin(th) * ds; c.lineTo(px, py); }
  c.strokeStyle = col; c.lineWidth = lw; c.lineCap = 'round'; c.stroke();
}
/* one roof tier from the front: a flared trapezoid, a sawtooth of bai raka under the eave, a gable, curled ends */
function tier(c, cx, y, w, h, p, s) {
  var f = w * 0.08, lw = max(1, s * 0.06);
  pg(c, [cx - w / 2 - f, y, cx + w / 2 + f, y, cx + w * 0.34, y - h, cx - w * 0.34, y - h], grad(c, 0, y - h, 0, y, [0, mixc(p.roof, p.hi, 0.35), 1, p.roof]));
  pg(c, [cx - w / 2 - f, y, cx + w / 2 + f, y, cx + w / 2 + f * 0.5, y + h * 0.16, cx - w / 2 - f * 0.5, y + h * 0.16], p.lo);
  c.beginPath(); var n = max(6, Math.round(w / (s * 0.22)));
  for (var i = 0; i <= n; i++) c.lineTo(cx - w / 2 - f + (w + 2 * f) * i / n, y + h * 0.16 + abs(sin(i * PI / 2)) * h * 0.18);
  c.strokeStyle = p.trim; c.lineWidth = max(1, s * 0.05); c.stroke();
  pg(c, [cx - w * 0.22, y - h * 0.15, cx + w * 0.22, y - h * 0.15, cx, y - h * 1.05], p.body, p.trim, lw);
  pg(c, [cx - w * 0.09, y - h * 0.18, cx + w * 0.09, y - h * 0.18, cx, y - h * 0.62], p.hi);
  curl(c, cx - w / 2 - f, y, s * 0.55, -1, p.trim, max(1.2, s * 0.09));
  curl(c, cx + w / 2 + f, y, s * 0.55, 1, p.trim, max(1.2, s * 0.09));
  curl(c, cx, y - h * 1.05, s * 0.5, 1, p.trim, max(1.2, s * 0.08));
}
/* Phra Chai Mongkhon at the door, gilded, sword up, bag down (the glow is drawn live) */
function figureDeva(c, x, y, s) {
  var g = '#f5c542';
  pg(c, [x - s * 0.22, y, x + s * 0.22, y, x + s * 0.14, y - s * 0.62, x - s * 0.14, y - s * 0.62], g);
  dot(c, x, y - s * 0.74, s * 0.13, '#f7d36a');
  pg(c, [x - s * 0.08, y - s * 0.86, x + s * 0.08, y - s * 0.86, x, y - s * 1.12], g);
  ln(c, x + s * 0.16, y - s * 0.45, x + s * 0.3, y - s * 0.98, '#fff6c8', max(1, s * 0.04));
  dot(c, x - s * 0.24, y - s * 0.3, s * 0.08, '#c98a1c');
}
/* the old couple, ta-yai, in the doorway of their house */
function couple(c, x, y, s) {
  [[-0.17, '#e8e0d0'], [0.17, '#c96b6b']].forEach(function (f) {
    var fx = x + f[0] * s;
    pg(c, [fx - s * 0.12, y, fx + s * 0.12, y, fx + s * 0.07, y - s * 0.38, fx - s * 0.07, y - s * 0.38], f[1]);
    dot(c, fx, y - s * 0.47, s * 0.09, '#e9c49a'); dot(c, fx, y - s * 0.52, s * 0.07, '#d9d9d9');
  });
}
/* a dancer on the porch (drawn live, she sways) */
function dancer(c, x, y, h, col, t, ph) {
  var sw = sin(t * 2 + ph) * h * 0.05;
  pg(c, [x - h * 0.2, y, x + h * 0.2, y, x + h * 0.06 + sw, y - h * 0.62, x - h * 0.06 + sw, y - h * 0.62], col);
  dot(c, x + sw, y - h * 0.72, h * 0.1, '#f0c9a0');
  pg(c, [x - h * 0.06 + sw, y - h * 0.8, x + h * 0.06 + sw, y - h * 0.8, x + sw, y - h], '#f2c14e');
  c.strokeStyle = '#f0c9a0'; c.lineWidth = max(1, h * 0.05); c.lineCap = 'round';
  c.beginPath(); c.moveTo(x - h * 0.05 + sw, y - h * 0.55); c.quadraticCurveTo(x - h * 0.3, y - h * 0.55, x - h * 0.28 + sw, y - h * 0.8); c.stroke();
  c.beginPath(); c.moveTo(x + h * 0.05 + sw, y - h * 0.55); c.quadraticCurveTo(x + h * 0.3, y - h * 0.5, x + h * 0.32, y - h * 0.38); c.stroke();
}
/* a small white elephant, trunk down */
function elephant(c, x, y, h, col) {
  col = col || '#eae6dc';
  ov(c, x, y - h * 0.55, h * 0.5, h * 0.32, col);
  [-0.32, -0.12, 0.14, 0.32].forEach(function (k) { fr(c, x + k * h - h * 0.07, y - h * 0.4, h * 0.14, h * 0.4, col); });
  dot(c, x + h * 0.5, y - h * 0.72, h * 0.22, col);
  c.strokeStyle = col; c.lineWidth = h * 0.1; c.lineCap = 'round';
  c.beginPath(); c.moveTo(x + h * 0.66, y - h * 0.66); c.quadraticCurveTo(x + h * 0.82, y - h * 0.3, x + h * 0.7, y - h * 0.12); c.stroke();
  ov(c, x + h * 0.42, y - h * 0.7, h * 0.13, h * 0.17, 'rgba(0,0,0,.12)');
  dot(c, x + h * 0.56, y - h * 0.78, h * 0.03, '#222');
}
/* an elephant statue: the same, larger, in a gold-edged red cloth, on its own plinth */
function statue(c, x, y, h, col, dir) {
  c.save(); c.translate(x, y); c.scale(dir || 1, 1);
  fr(c, -h * 0.72, -h * 0.16, h * 1.44, h * 0.16, '#d8d2c4'); fr(c, -h * 0.72, -h * 0.18, h * 1.44, h * 0.04, '#efe9da');
  elephant(c, -h * 0.08, -h * 0.16, h * 0.9, col);
  pg(c, [-h * 0.34, -h * 0.78, h * 0.2, -h * 0.78, h * 0.26, -h * 0.5, -h * 0.4, -h * 0.5], '#c0262d', '#f2c14e', max(1, h * 0.025));
  dot(c, h * 0.52, -h * 0.84, h * 0.05, '#f2c14e');
  pg(c, [h * 0.46, -h * 0.76, h * 0.52, -h * 0.5, h * 0.6, -h * 0.68], '#fffaf0');
  c.restore();
}
/* a garland on a catenary through two hooks: y = a·cosh((x−m)/a) − a·cosh(span/a), a solved for the sag; beads of jasmine and marigold */
function garland(c, x0, y0, x1, y1, sag, s, t) {
  var m = (x0 + x1) / 2, span = abs(x1 - x0) / 2, a = span * span / (2 * sag) + sag / 3, n = 24, base = max(y0, y1), sw = sin(t * 0.9) * s * 0.03, rb = max(0.95, s * 0.075);
  for (var i = 0; i <= n; i++) {
    var x = x0 + (x1 - x0) * i / n, dy = a * (Math.cosh((x - m) / a) - Math.cosh(span / a)), y = base - dy + sw * sin(PI * i / n);
    dot(c, x, y, rb, i % 4 === 2 ? '#ff9f1c' : '#fffdf4');
  }
  var tx = m + sw * 2, ty = base + sag;
  c.strokeStyle = '#2e7d32'; c.lineWidth = max(1, s * 0.03); c.beginPath(); c.moveTo(tx, ty); c.lineTo(tx + sw, ty + s * 0.35); c.stroke();
  dot(c, tx + sw, ty + s * 0.4, max(1, s * 0.1), '#e63946'); dot(c, tx + sw, ty + s * 0.55, max(0.9, s * 0.08), '#ff9f1c');
}
/* a hanging phuang malai strand from an eave end */
function strand(c, x, y, len, s, t, ph) {
  var sw = sin(t * 1.1 + ph) * s * 0.05;
  for (var i = 0; i < 6; i++) { var u = i / 5; dot(c, x + sw * u, y + u * len, max(0.9, s * 0.07), i % 2 ? '#ff9f1c' : '#fffdf4'); }
  dot(c, x + sw, y + len + s * 0.1, max(1, s * 0.09), '#e63946');
}
/* the three-colour cloth tied on the post: bands and a tail that moves */
function ribbonBand(c, x, y, w, s) { ['#e63946', '#f1c40f', '#2e86de'].forEach(function (col, i) { fr(c, x - w / 2, y + i * s * 0.09, w, s * 0.09, col); }); }
function ribbonTail(c, x, y, w, s, t) {
  var sw = sin(t * 1.7) * s * 0.06;
  c.strokeStyle = '#e63946'; c.lineWidth = max(1, s * 0.06); c.lineCap = 'round'; c.beginPath(); c.moveTo(x + w / 2, y + s * 0.1); c.quadraticCurveTo(x + w / 2 + s * 0.3 + sw, y + s * 0.4, x + w / 2 + s * 0.15 + sw * 1.6, y + s * 0.8); c.stroke();
}
/* a naga rising beside a plinth, a sine body and a hood of heads */
function naga(c, x, y, s, dir, col) {
  var top = y - 1.35 * s, i;
  c.strokeStyle = col; c.lineWidth = 0.24 * s; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath();
  for (i = 0; i <= 20; i++) { var u = i / 20, px = x + dir * sin(u * 7.5) * 0.17 * s, py = y - u * 1.35 * s; i ? c.lineTo(px, py) : c.moveTo(px, py); }
  c.stroke();
  c.strokeStyle = 'rgba(255,240,170,.55)'; c.lineWidth = 0.06 * s; c.beginPath();
  for (i = 0; i <= 20; i++) { var u2 = i / 20; i ? c.lineTo(x + dir * sin(u2 * 7.5) * 0.17 * s - 0.05 * s, y - u2 * 1.35 * s) : c.moveTo(x - 0.05 * s, y); } c.stroke();
  var hx = x + dir * sin(7.5) * 0.17 * s;
  for (var k = -1; k <= 1; k++) ov(c, hx + k * 0.13 * s, top - 0.12 * s + abs(k) * 0.05 * s, 0.1 * s, 0.2 * s, col, k * 0.4);
  dot(c, hx + dir * 0.03 * s, top - 0.05 * s, 0.035 * s, '#7d1a12');
}

/* ---------------------------------------------------------------- the five models.
   Each draws its still parts on c and pushes what moves to L as function (c, t); it returns its extent. */
function deva(c, o, L) {
  var s = o.s, x = o.x, y = o.y, p = o.p, ped = o.ped ? s * 1.15 : 0;
  if (ped) {
    var pw = s * 0.95; pg(c, [x - pw, y, x + pw, y, x + pw * 0.86, y - ped, x - pw * 0.86, y - ped], grad(c, x - pw, 0, x + pw, 0, [0, '#cfc7b4', 0.5, '#efe9da', 1, '#bfb7a3']));
    fr(c, x - pw * 0.98, y - ped - s * 0.07, pw * 1.96, s * 0.1, '#efe9da'); fr(c, x - pw * 0.9, y - s * 0.12, pw * 1.8, s * 0.12, '#bdb5a0');
    if (o.naga) { naga(c, x - pw - s * 0.18, y, s * 0.82, -1, '#d8a62a'); naga(c, x + pw + s * 0.18, y, s * 0.82, 1, '#d8a62a'); }
    y -= ped + s * 0.05;
  }
  pg(c, [x - s * 0.8, y, x + s * 0.8, y, x + s * 0.65, y - s * 0.35, x - s * 0.65, y - s * 0.35], '#d8d2c4');
  var py0 = y - s * 0.35, py1 = y - s * (o.pillar || 3.7);
  pg(c, [x - s * 0.36, py0, x + s * 0.36, py0, x + s * 0.27, py1, x - s * 0.27, py1], grad(c, x - s * 0.35, 0, x + s * 0.35, 0, [0, p.lo, 0.45, p.body, 0.7, p.hi, 1, p.lo]));
  if (o.cloth) { var cy = y - s * (o.pillar ? min(1.7, o.pillar * 0.46) : 1.7); ribbonBand(c, x, cy, s * 0.66, s); L.push(function (q, t) { ribbonTail(q, x, cy, s * 0.66, s, t); }); }
  c.beginPath();
  for (var i = 0; i <= 40; i++) { var th = PI + PI * i / 40, r = s * 0.95 * (1 + 0.22 * abs(cos(4 * th))); c.lineTo(x + cos(th) * r, py1 - s * 0.05 - sin(th + PI) * r * 0.55); }
  c.closePath(); c.fillStyle = grad(c, 0, py1 - s, 0, py1, [0, p.hi, 1, p.body]); c.fill(); c.strokeStyle = p.trim; c.lineWidth = max(1, s * 0.05); c.stroke();
  var dk = py1 - s * 0.55;
  fr(c, x - s * 1.9, dk, s * 3.8, s * 0.28, p.lo); fr(c, x - s * 1.9, dk - s * 0.06, s * 3.8, s * 0.08, p.trim);
  for (var b = 0; b <= 14; b++) { var bx = x - s * 1.8 + s * 3.6 * b / 14; if (abs(bx - x) < s * 0.42) continue; fr(c, bx - s * 0.035, dk - s * 0.42, s * 0.07, s * 0.42, p.trim); }
  fr(c, x - s * 1.85, dk - s * 0.46, s * 1.45, s * 0.06, p.trim); fr(c, x + s * 0.4, dk - s * 0.46, s * 1.45, s * 0.06, p.trim);
  var hb = dk, ht = dk - s * 1.75, hw = s * 2.3;
  c.fillStyle = grad(c, x - hw / 2, 0, x + hw / 2, 0, [0, p.lo, 0.3, p.body, 0.6, p.hi, 1, p.lo]); c.fillRect(x - hw / 2, ht, hw, hb - ht);
  [-0.5, -0.32, 0.32, 0.5].forEach(function (k) { fr(c, x + k * hw - s * 0.06, ht, s * 0.12, hb - ht, p.trim); });
  c.beginPath(); c.moveTo(x - s * 0.42, hb); c.lineTo(x - s * 0.42, ht + s * 0.65);
  c.quadraticCurveTo(x - s * 0.42, ht + s * 0.2, x, ht + s * 0.08); c.quadraticCurveTo(x + s * 0.42, ht + s * 0.2, x + s * 0.42, ht + s * 0.65);
  c.lineTo(x + s * 0.42, hb); c.closePath(); c.fillStyle = p.dark; c.fill(); c.strokeStyle = p.trim; c.lineWidth = max(1, s * 0.07); c.stroke();
  figureDeva(c, x, hb - s * 0.05, s * 1.25);
  if (o.glass) {   /* glass sides: panes over the walls, thin frames */
    c.fillStyle = 'rgba(205,232,245,.42)'; c.fillRect(x - hw / 2, ht, hw * 0.5 - s * 0.45, hb - ht); c.fillRect(x + s * 0.45, ht, hw * 0.5 - s * 0.45, hb - ht);
    ln(c, x - hw / 2 + s * 0.2, ht, x - hw / 2 + s * 0.6, hb, 'rgba(255,255,255,.55)', max(1, s * 0.07)); ln(c, x + hw / 2 - s * 0.6, ht, x + hw / 2 - s * 0.2, hb, 'rgba(255,255,255,.45)', max(1, s * 0.07));
  }
  var gx = x, gy = hb - s * 0.8;
  L.push(function (q, t) { var a = 0.25 + 0.15 * sin(t * 1.3); dot(q, gx, gy, s * 0.62, 'rgba(255,240,170,' + a.toFixed(3) + ')'); });
  /* the porch: dancers sway, elephant and zebra stand */
  if (o.retinue) {
    L.push(function (q, t) { dancer(q, x - s * 1.25, dk - s * 0.02, s * 0.62, '#d23f6b', t, 0); dancer(q, x + s * 1.2, dk - s * 0.02, s * 0.62, '#7b4bd1', t, 1.7); });
    elephant(c, x - s * 0.72, dk - s * 0.02, s * 0.42, '#f2efe6');
    zebra(c, x + s * 0.78, dk - s * 0.02, s * 0.45);
  }
  var ry = ht, w = s * 3.3, h = s * 0.75, eave = [];
  for (var k = 0; k < 3; k++) { tier(c, x, ry, w, h, p, s); eave.push([x - w / 2, x + w / 2, ry + h * 0.34, w]); ry -= h * 0.82; w *= 0.78; h *= 0.86; }
  var sy = ry, sr = s * 0.55, glints = [[x - s * 1.55, ht - s * 0.3], [x + s * 1.5, ht - s * 0.62]];
  for (var j = 0; j < 7; j++) {
    c.beginPath(); c.moveTo(x - sr, sy); c.quadraticCurveTo(x - sr * 0.95, sy - sr * 0.9, x, sy - sr * 1.15); c.quadraticCurveTo(x + sr * 0.95, sy - sr * 0.9, x + sr, sy); c.closePath();
    c.fillStyle = j % 2 ? p.body : p.hi; c.fill(); sy -= sr * 0.85; sr *= 0.72;
  }
  ln(c, x, sy, x, sy - s * 0.7, p.hi, max(1, s * 0.05)); dot(c, x, sy - s * 0.72, max(0.8, s * 0.06), '#fff8d0');
  glints.push([x, sy - s * 0.74], [x + s * 0.12, ry - s * 0.25]);
  /* hanging garland across the eave, strands from its ends */
  L.push(function (q, t) { garland(q, x - s * 1.55, ht + s * 0.05, x + s * 1.55, ht + s * 0.05, s * 0.7, s, t); });
  L.push(function (q, t) { var w1 = s * 3.3 / 2 + s * 0.26; strand(q, x - w1, ht + s * 0.12, s * 1.1, s, t, 0); strand(q, x + w1, ht + s * 0.12, s * 1.1, s, t, 2); });
  return { top: sy - s * 0.8, deck: dk, hb: hb, ht: ht, w: s * 3.8, door: [x, hb - s * 0.7], eave: eave[0], glints: glints, py: y };
}
/* a zebra, in the minisite's retinue, standing */
function zebra(c, x, y, h) {
  c.save(); c.translate(x, y); c.scale(-1, 1);
  c.fillStyle = '#fbfbf7'; c.strokeStyle = '#1b1b1b'; c.lineWidth = max(0.6, h * 0.03);
  [[-0.3, 0], [-0.18, 0], [0.2, 0], [0.32, 0]].forEach(function (L) { c.fillRect(L[0] * h - h * 0.04, -h * 0.42, h * 0.08, h * 0.42); c.strokeRect(L[0] * h - h * 0.04, -h * 0.42, h * 0.08, h * 0.42); });
  c.beginPath(); c.ellipse(0, -h * 0.55, h * 0.42, h * 0.2, 0, 0, TAU); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(h * 0.28, -h * 0.62); c.lineTo(h * 0.5, -h * 0.98); c.lineTo(h * 0.66, -h * 0.9); c.lineTo(h * 0.44, -h * 0.55); c.closePath(); c.fill(); c.stroke();
  c.save(); c.beginPath(); c.ellipse(0, -h * 0.55, h * 0.42, h * 0.2, 0, 0, TAU); c.clip(); c.fillStyle = '#1b1b1b';
  for (var i = 0; i < 9; i++) { var u = -0.42 + 0.84 * (0.5 - 0.5 * cos(PI * i / 8)); c.fillRect(u * h, -h * 0.8, h * 0.035, h * 0.5); }
  c.restore(); c.fillStyle = '#1b1b1b'; c.fillRect(h * 0.36, -h * 0.98, h * 0.06, h * 0.2); dot(c, h * 0.6, -h * 0.9, h * 0.025, '#1b1b1b');
  c.restore();
}
/* San Ta-yai: a house on four legs, the old couple at the door, a steep curved gable */
function tayai(c, o, L) {
  var s = o.s, x = o.x, y = o.y, p = o.p, dk = y - s * 3.1;
  [[-1.05, 0.15, p.lo], [1.05, 0.15, p.lo], [-1.3, 0, p.body], [1.3, 0, p.body]].forEach(function (a) { fr(c, x + a[0] * s - s * 0.1, dk, s * 0.2, y - a[1] * s - dk, a[2]); });
  fr(c, x - s * 1.6, dk - s * 0.22, s * 3.2, s * 0.26, p.lo); fr(c, x - s * 1.6, dk - s * 0.28, s * 3.2, s * 0.07, p.trim);
  var ht = dk - s * 1.55, hw = s * 2.3;
  fr(c, x - hw / 2, ht, hw, dk - s * 0.22 - ht, p.body);
  c.strokeStyle = p.lo; c.lineWidth = max(0.6, s * 0.03);
  for (var i = 1; i < 9; i++) { var bx = x - hw / 2 + hw * i / 9; c.beginPath(); c.moveTo(bx, ht); c.lineTo(bx, dk - s * 0.22); c.stroke(); }
  fr(c, x - s * 0.42, ht + s * 0.35, s * 0.84, dk - s * 0.22 - ht - s * 0.35, p.dark);
  couple(c, x, dk - s * 0.24, s * 1.25);
  var rb = ht + s * 0.05, apex = ht - s * 1.85, ew = s * 1.75;
  c.beginPath(); c.moveTo(x - ew, rb); c.quadraticCurveTo(x - ew * 0.35, rb - s * 0.4, x, apex); c.quadraticCurveTo(x + ew * 0.35, rb - s * 0.4, x + ew, rb); c.closePath();
  c.fillStyle = grad(c, 0, apex, 0, rb, [0, mixc(p.roof, p.hi, 0.3), 1, p.roof]); c.fill();
  c.beginPath(); c.moveTo(x - ew * 0.62, rb - s * 0.05); c.quadraticCurveTo(x - ew * 0.22, rb - s * 0.4, x, apex + s * 0.35); c.quadraticCurveTo(x + ew * 0.22, rb - s * 0.4, x + ew * 0.62, rb - s * 0.05); c.closePath();
  c.fillStyle = p.body; c.fill(); c.strokeStyle = p.trim; c.lineWidth = max(1, s * 0.07); c.stroke();
  curl(c, x - ew, rb, s * 0.5, -1, p.trim, max(1.2, s * 0.08)); curl(c, x + ew, rb, s * 0.5, 1, p.trim, max(1.2, s * 0.08)); curl(c, x, apex, s * 0.55, 1, p.trim, max(1.2, s * 0.08));
  L.push(function (q, t) { garland(q, x - s * 1.2, ht + s * 0.1, x + s * 1.2, ht + s * 0.1, s * 0.5, s * 0.85, t + 1); });
  return { top: apex - s * 0.6, deck: dk, hb: dk - s * 0.22, ht: ht, w: s * 3.2, door: [x, dk - s * 0.7], eave: [x - ew, x + ew, rb, ew * 2], glints: [[x, apex - s * 0.3], [x + ew, rb - s * 0.55]], py: y };
}
/* San Phra Phrom: a stepped plinth, four columns, the four-faced god seated, a tiered roof and a prang spire */
function brahma(c, o, L) {
  var s = o.s, x = o.x, y = o.y, p = o.p;
  for (var k = 0; k < 3; k++) fr(c, x - s * (2.1 - k * 0.35), y - s * (k + 1) * 0.55, s * 2 * (2.1 - k * 0.35), s * 0.55, k % 2 ? '#e9e2d2' : '#d8cfbc');
  var fl = y - s * 1.65, ht = fl - s * 2.2;
  [[-1.0, p.lo], [1.0, p.lo], [-1.35, p.body], [1.35, p.body]].forEach(function (a) { fr(c, x + a[0] * s - s * 0.1, ht, s * 0.2, fl - ht, a[1]); });
  fr(c, x - s * 1.6, fl - s * 0.12, s * 3.2, s * 0.12, p.trim);
  var by = fl - s * 0.12;
  c.fillStyle = '#f2c14e'; c.beginPath(); c.ellipse(x, by - s * 0.35, s * 0.6, s * 0.35, 0, PI, 0); c.fill();
  pg(c, [x - s * 0.3, by - s * 0.3, x + s * 0.3, by - s * 0.3, x + s * 0.2, by - s * 1.05, x - s * 0.2, by - s * 1.05], '#f2c14e');
  [-0.22, 0, 0.22].forEach(function (a, i) { dot(c, x + a * s, by - s * 1.18 + (i === 1 ? -s * 0.04 : 0), s * 0.13, i === 1 ? '#f7d36a' : '#e7b73c'); });
  pg(c, [x - s * 0.16, by - s * 1.32, x + s * 0.16, by - s * 1.32, x, by - s * 1.75], '#f2c14e');
  c.strokeStyle = '#f2c14e'; c.lineWidth = max(1, s * 0.07); c.lineCap = 'round';
  [[-1, 0.7], [1, 0.7], [-1, 0.95], [1, 0.95]].forEach(function (a, i) { c.beginPath(); c.moveTo(x + a[0] * s * 0.2, by - s * a[1]); c.lineTo(x + a[0] * s * (0.55 + 0.1 * i), by - s * (a[1] + 0.25 + 0.05 * sin(i))); c.stroke(); });
  var gx = x, gy = by - s * 1.0;
  L.push(function (q, t) { var a = 0.22 + 0.12 * sin(t * 1.1); dot(q, gx, gy, s * 0.85, 'rgba(255,236,160,' + a.toFixed(3) + ')'); });
  var ry = ht, w = s * 3.6, h = s * 0.7;
  for (var j = 0; j < 2; j++) { tier(c, x, ry, w, h, p, s); ry -= h * 0.82; w *= 0.72; h *= 0.85; }
  c.beginPath(); c.moveTo(x - s * 0.55, ry); c.quadraticCurveTo(x - s * 0.5, ry - s * 1.4, x, ry - s * 2.1); c.quadraticCurveTo(x + s * 0.5, ry - s * 1.4, x + s * 0.55, ry); c.closePath();
  c.fillStyle = grad(c, x - s * 0.55, 0, x + s * 0.55, 0, [0, p.body, 0.5, p.hi, 1, p.body]); c.fill(); c.strokeStyle = p.trim; c.lineWidth = max(1, s * 0.05); c.stroke();
  for (var q = 1; q < 6; q++) { var yy = ry - s * 2.1 * q / 6, hw = s * 0.55 * sqrt(1 - q / 6); c.beginPath(); c.moveTo(x - hw, yy); c.lineTo(x + hw, yy); c.stroke(); }
  if (o.retinue) { elephant(c, x - s * 1.75, y - s * 1.65, s * 0.55, '#f7f4ec'); elephant(c, x + s * 1.2, y - s * 1.65, s * 0.55, '#f7f4ec'); }
  L.push(function (q, t) { garland(q, x - s * 1.4, ht + s * 0.15, x + s * 1.4, ht + s * 0.15, s * 0.55, s * 0.9, t + 2); });
  return { top: ry - s * 2.3, deck: fl, hb: fl, ht: ht, w: s * 4.2, door: [x, by - s * 0.8], eave: [x - s * 1.8, x + s * 1.8, ht + s * 0.25, s * 3.6], glints: [[x, ry - s * 2.1], [x + s * 1.9, ht - s * 0.1]], py: y };
}
/* Lanna wood: a house of planks on four posts, a low gable and crossed kalae */
function puya(c, o, L) {
  var s = o.s, x = o.x, y = o.y, p = o.p, dk = y - s * 3.4;
  [[-0.95, 0.12, p.lo], [0.95, 0.12, p.lo], [-1.15, 0, p.body], [1.15, 0, p.body]].forEach(function (a) { fr(c, x + a[0] * s - s * 0.12, dk, s * 0.24, y - a[1] * s - dk, a[2]); });
  fr(c, x - s * 1.45, dk - s * 0.18, s * 2.9, s * 0.2, p.lo);
  var ht = dk - s * 1.2, hw = s * 2.1;
  fr(c, x - hw / 2, ht, hw, dk - s * 0.18 - ht, p.body);
  c.strokeStyle = p.lo; c.lineWidth = max(0.6, s * 0.03);
  for (var i = 1; i < 7; i++) { var by = ht + (dk - s * 0.18 - ht) * i / 7; c.beginPath(); c.moveTo(x - hw / 2, by); c.lineTo(x + hw / 2, by); c.stroke(); }
  fr(c, x - s * 0.35, ht + s * 0.3, s * 0.7, dk - s * 0.18 - ht - s * 0.3, p.dark);
  fr(c, x - s * 0.28, dk - s * 0.55, s * 0.56, s * 0.18, '#fffaf0'); dot(c, x, dk - s * 0.62, s * 0.1, '#ffd166');
  var rb = ht + s * 0.05, apex = ht - s * 1.15, ew = s * 1.7;
  pg(c, [x - ew, rb, x, apex, x + ew, rb], p.roof);
  pg(c, [x - ew * 0.55, rb - s * 0.06, x, apex + s * 0.3, x + ew * 0.55, rb - s * 0.06], p.body, p.trim, max(1, s * 0.05));
  c.strokeStyle = p.roof; c.lineWidth = max(1.5, s * 0.16); c.lineCap = 'round';
  c.beginPath(); c.moveTo(x - s * 0.15, apex + s * 0.12); c.quadraticCurveTo(x + s * 0.25, apex - s * 0.3, x + s * 0.55, apex - s * 0.6); c.stroke();
  c.beginPath(); c.moveTo(x + s * 0.15, apex + s * 0.12); c.quadraticCurveTo(x - s * 0.25, apex - s * 0.3, x - s * 0.55, apex - s * 0.6); c.stroke();
  L.push(function (q, t) { fr(q, x + ew * 0.75, rb - s * 0.05, s * 0.1, s * 0.9 + sin(t * 2) * s * 0.05, '#e63946'); });
  return { top: apex - s * 0.8, deck: dk, hb: dk - s * 0.18, ht: ht, w: s * 3.0, door: [x, dk - s * 0.55], eave: [x - ew, x + ew, rb, ew * 2], glints: [[x - s * 0.55, apex - s * 0.55], [x + ew * 0.8, rb - s * 0.3]], py: y };
}
/* the Chinese earth-god shrine: a red box on a plinth, a swallow-tail roof, lanterns, incense in a burner */
function chinese(c, o, L) {
  var s = o.s, x = o.x, y = o.y, red = '#c0262d', gold = '#f2c14e';
  fr(c, x - s * 1.7, y - s * 1.8, s * 3.4, s * 1.8, '#8c1c1c'); fr(c, x - s * 1.7, y - s * 1.9, s * 3.4, s * 0.12, gold);
  var ht = y - s * 4.1;
  fr(c, x - s * 1.45, ht, s * 2.9, y - s * 1.9 - ht, red); fr(c, x - s * 0.7, ht + s * 0.4, s * 1.4, s * 1.6, '#3a0a0a');
  for (var i = 0; i < 4; i++) fr(c, x - s * 1.25, ht + s * (0.35 + i * 0.45), s * 0.3, s * 0.3, gold);
  for (var j = 0; j < 4; j++) fr(c, x + s * 0.95, ht + s * (0.35 + j * 0.45), s * 0.3, s * 0.3, gold);
  fr(c, x - s * 0.45, y - s * 2.35, s * 0.9, s * 0.45, '#b8862a');
  var tips = [];
  c.strokeStyle = '#7a1010'; c.lineWidth = max(1, s * 0.05);
  [-0.15, 0, 0.15].forEach(function (k) { c.beginPath(); c.moveTo(x + k * s, y - s * 2.35); c.lineTo(x + k * s * 1.4, y - s * 3.05); c.stroke(); tips.push([x + k * s * 1.4, y - s * 3.05]); });
  var rb = ht - s * 0.05, ew = s * 2.2;
  c.beginPath();
  for (var u = -1; u <= 1.0001; u += 0.05) c.lineTo(x + u * ew, rb - s * 0.9 - Math.pow(abs(u), 4) * s * 0.75);
  for (var v = 1; v >= -1.0001; v -= 0.05) c.lineTo(x + v * ew * 0.92, rb - Math.pow(abs(v), 4) * s * 0.35);
  c.closePath(); c.fillStyle = '#1f6f50'; c.fill(); c.strokeStyle = gold; c.lineWidth = max(1, s * 0.06); c.stroke();
  dot(c, x, rb - s * 1.15, s * 0.22, gold);
  [-1, 1].forEach(function (d, i) {
    L.push(function (q, t) {
      var ang = sin(t * 1.6 + i) * 0.12, lx = x + d * s * 1.75 + sin(ang) * s * 0.6, ly = rb + cos(ang) * s * 0.6;
      q.strokeStyle = '#333'; q.lineWidth = 1; q.beginPath(); q.moveTo(x + d * s * 1.75, rb); q.lineTo(lx, ly); q.stroke();
      ov(q, lx, ly + s * 0.25, s * 0.22, s * 0.28, '#e0262d'); fr(q, lx - s * 0.12, ly - s * 0.03, s * 0.24, s * 0.06, gold);
    });
  });
  return { top: rb - s * 1.6, deck: y - s * 1.9, hb: y - s * 1.9, ht: ht, w: s * 4.4, door: [x, ht + s * 1.2], eave: [x - ew, x + ew, rb, ew * 2], glints: [[x, rb - s * 1.2]], tips: tips, py: y };
}
var MODEL = { deva: deva, tayai: tayai, brahma: brahma, puya: puya, chinese: chinese };
/* each model's height and half-width in its own unit s (top of the finial to its post's foot, half the porch) */
var NOM = { deva: [9.4, 1.95], tayai: [6.8, 1.75], brahma: [6.9, 2.1], puya: [6.3, 1.55], chinese: [5.6, 2.2] };

/* ---------------------------------------------------------------- the offering table and its tray
   At one baseline ty: the incense pot and sticks, a candle each side, and the day's offerings. */
function tray(c, o, L) {
  var s = o.s, x = o.x, ty = o.ty, it = o.items, n = o.sticks, burn = o.burn, px = x, pr = s * 0.42, tips = [];
  c.fillStyle = '#c79a3a'; c.beginPath(); c.moveTo(px - pr, ty - s * 0.5); c.quadraticCurveTo(px - pr * 1.05, ty, px - pr * 0.6, ty); c.lineTo(px + pr * 0.6, ty); c.quadraticCurveTo(px + pr * 1.05, ty, px + pr, ty - s * 0.5); c.closePath(); c.fill();
  fr(c, px - pr * 1.05, ty - s * 0.56, pr * 2.1, s * 0.1, '#8e6310'); fr(c, px - pr * 0.9, ty - s * 0.6, pr * 1.8, s * 0.06, '#b9b2a6');
  for (var i = 0; i < n; i++) {
    var a = (i - (n - 1) / 2) * 0.09, len = s * (burn > 0 ? 0.35 + 1.0 * burn : 0.16), bx = px + (i - (n - 1) / 2) * s * 0.07, tx = bx + sin(a) * len, tyy = ty - s * 0.6 - cos(a) * len;
    ln(c, bx, ty - s * 0.6, tx, tyy, burn > 0 ? '#b5422b' : '#6a5a52', max(1, s * 0.035));
    if (o.lit && burn > 0.02) tips.push([tx, tyy]);
  }
  [-1, 1].forEach(function (d) {
    var cx = x + d * s * 0.85; fr(c, cx - s * 0.07, ty - s * 0.55, s * 0.14, s * 0.55, '#fff6e0'); fr(c, cx - s * 0.07, ty - s * 0.55, s * 0.04, s * 0.55, 'rgba(255,255,255,.7)');
    if (o.flame) L.push(function (q, t) {
      var fl = 1 + 0.12 * sin(t * 13 + d) + 0.08 * sin(t * 21.7 + d * 2);
      q.fillStyle = '#ffcf4a'; q.beginPath(); q.ellipse(cx, ty - s * 0.66, s * 0.06, s * 0.13 * fl, 0, 0, TAU); q.fill();
      q.save(); q.globalCompositeOperation = 'lighter'; lamp(q, cx, ty - s * 0.66, s * 0.62, '#ffb347', 0.5 * fl); q.restore();
    });
  });
  var sl = { water: -1.55, red: -1.25, sweet: -0.55, rice: 0.55, banana: 1.2, coconut: 1.6 };
  if (it.water) { fr(c, x + sl.water * s - s * 0.12, ty - s * 0.42, s * 0.24, s * 0.42, 'rgba(170,215,255,.9)'); fr(c, x + sl.water * s - s * 0.12, ty - s * 0.42, s * 0.24, s * 0.06, '#e8f6ff'); fr(c, x + sl.water * s - s * 0.08, ty - s * 0.4, s * 0.04, s * 0.34, 'rgba(255,255,255,.55)'); }
  if (it.red) {
    var rx = x + sl.red * s; fr(c, rx - s * 0.1, ty - s * 0.62, s * 0.2, s * 0.62, '#e0262d'); fr(c, rx - s * 0.06, ty - s * 0.74, s * 0.12, s * 0.12, '#e0262d'); fr(c, rx - s * 0.1, ty - s * 0.4, s * 0.2, s * 0.1, '#f7f2e6');
    ln(c, rx, ty - s * 0.74, rx + s * 0.12, ty - s * 1.05, '#ffffff', max(1, s * 0.03));
  }
  if (it.sweet) { ov(c, x + sl.sweet * s, ty - s * 0.1, s * 0.26, s * 0.1, '#6ccf9c'); [-0.12, 0, 0.12].forEach(function (k, i) { dot(c, x + sl.sweet * s + k * s, ty - s * 0.2, s * 0.07, ['#ff7aa2', '#ffd166', '#7bd389'][i]); }); }
  if (it.rice) { ov(c, x + sl.rice * s, ty - s * 0.08, s * 0.3, s * 0.1, '#ffffff'); c.fillStyle = '#ffffff'; c.beginPath(); c.arc(x + sl.rice * s, ty - s * 0.12, s * 0.2, PI, 0); c.fill(); }
  if (it.banana) { c.strokeStyle = '#f6d23a'; c.lineWidth = s * 0.09; c.lineCap = 'round'; for (var b = 0; b < 4; b++) { c.beginPath(); c.arc(x + sl.banana * s, ty - s * 0.5, s * 0.36, PI * (0.62 + b * 0.06), PI * (0.98 + b * 0.04)); c.stroke(); } }
  if (it.coconut) { dot(c, x + sl.coconut * s, ty - s * 0.24, s * 0.24, '#7a5232'); dot(c, x + sl.coconut * s, ty - s * 0.4, s * 0.12, '#e9f5d0'); }
  if (it.garland) { for (var g = 0; g < 14; g++) { var th = TAU * g / 14; dot(c, x - s * 0.95 + cos(th) * s * 0.2, ty - s * 0.04 + sin(th) * s * 0.07, max(0.9, s * 0.06), g % 4 ? '#fffdf4' : '#ff9f1c'); } }
  if (it.bowl) { ov(c, x + 1.1 * s, ty - s * 0.1, s * 0.34, s * 0.12, '#c79a3a'); c.fillStyle = '#c79a3a'; c.beginPath(); c.arc(x + 1.1 * s, ty - s * 0.12, s * 0.3, 0, PI); c.fill(); ov(c, x + 1.1 * s, ty - s * 0.14, s * 0.26, s * 0.07, '#fff6e0'); dot(c, x + 1.1 * s, ty - s * 0.2, s * 0.08, '#ff9f1c'); }
  return tips;
}
/* the table: two legs, a top in red cloth with a gold fringe, the tray on it */
function table(c, o, L) {
  var s = o.s, x = o.x, y = o.y, top = y - s * 1.5, w = s * 3.6;
  [-0.42, 0.42].forEach(function (k) { fr(c, x + k * w - s * 0.08, top, s * 0.16, y - top, '#7a4a24'); });
  fr(c, x - w / 2 - s * 0.1, top - s * 0.14, w + s * 0.2, s * 0.16, '#9a6236'); fr(c, x - w / 2 - s * 0.1, top + s * 0.02, w + s * 0.2, s * 0.32, '#e63946');
  fr(c, x - w / 2 - s * 0.1, top + s * 0.02, w + s * 0.2, s * 0.06, 'rgba(255,255,255,.25)');
  for (var f = 0; f < 18; f++) fr(c, x - w / 2 + w * f / 18, top + s * 0.34, s * 0.06, s * 0.12, '#f2c14e');
  o.ty = top - s * 0.14; return tray(c, o, L);
}

/* ---------------------------------------------------------------- smoke: stateless, a pure function of time */
function smokeAt(c, t, x, y, s, k, wind, band) {
  var col = band === 0 ? '188,196,216' : band === 1 ? '224,196,212' : '234,238,255', amp = band === 0 ? 0.6 : 0.5;
  for (var j = 0; j < 14; j++) {
    var u = (t * 0.26 + j / 14 + k * 0.137) % 1, yy = y - u * s * 5.2, xx = x + sin(u * 6.5 + k * 2.1 + t * 0.6) * s * 0.26 * u + u * u * s * 0.55 * wind;
    var a = amp * (1 - u) * (u < 0.08 ? u / 0.08 : 1);
    c.fillStyle = 'rgba(' + col + ',' + a.toFixed(3) + ')'; c.beginPath(); c.arc(xx, yy, s * (0.14 + 0.46 * u), 0, TAU); c.fill();
  }
}

/* ---------------------------------------------------------------- what the name says
   The model, colour and size from the English and Thai names, the place around it from the words after the preposition. */
var SPECS = {};
function specOf(P) {
  var id = String(P.id || P.name || ''); if (SPECS[id]) return SPECS[id];
  var en = String(P.nameEn || ''), th = String(P.nameTh || '') + ' ' + String(P.name || ''), cut = /\s(?:at|by|in|on|behind|beside|outside|among|through|under|near|with|tied)\s/i.exec(en);
  var head = (cut ? en.slice(0, cut.index) : en).toLowerCase(), tail = ((cut ? en.slice(cut.index) : '') + ' ' + th).toLowerCase(), all = head + ' ' + tail;
  var slug = id.replace(/^cm-(?:curated|osm)-/, '').replace(/^spirit-house-?/, '').replace(/-/g, ' ').toLowerCase();
  var sp = { model: 'deva', col: null, small: false, n: 1, naga: false, glass: false, cloth: null, ped: false, shelf: false, eleph: null, bowl: false, extra: null, build: null, gate: null, green: null, canal: false, island: false, poles: false, wall: false, fence: false, houseNo: null, tractor: false, hospital: false, road: false };
  var hs = head + ' ' + (head.trim() === 'spirit house' || head.trim() === 'spirit houses' ? slug : '');
  if (/brahma|พระพรหม/.test(all)) { sp.model = 'brahma'; sp.col = 'white'; }
  else if (/ta-?yai|ตายาย/.test(all)) { sp.model = 'tayai'; sp.col = 'red'; }
  else if (/chinese|earth god|ศาลเจ้าจีน/.test(all)) { sp.model = 'chinese'; sp.col = 'red'; }
  else if (/wooden|\bwood\b|ไม้/.test(hs)) { sp.model = 'puya'; sp.col = /red/.test(hs) ? 'red' : 'wood'; }
  if (!sp.col) sp.col = /black/.test(hs) ? 'black' : /white|ขาว/.test(hs) ? 'white' : /terracotta|clay/.test(hs) ? 'clay' : /blue|น้ำเงิน/.test(hs) ? 'blue' : /green|เขียว/.test(hs) ? 'green' : /gold|ทอง/.test(hs) ? 'gold' : /red|แดง/.test(hs) ? 'red' : null;
  sp.small = /\bsmall\b|เล็ก/.test(hs) || /\bsmall\b/.test(slug);
  sp.n = /spirit houses|twin|\btwo\b|สอง/.test(hs) ? 2 : 1;
  sp.naga = /naga|นาค/.test(all); sp.glass = /glass-sided|glass sided/.test(head);
  sp.ped = /pedestal/.test(all) || /pillar/.test(tail); sp.shelf = /shelf/.test(all);
  if (/three-colour|tricolour|ribbon|cloth/.test(all)) sp.cloth = true;
  if (/elephant/.test(all)) sp.eleph = /statue/.test(all) ? 'statue' : 'small';
  sp.bowl = /offering bowl/.test(all); sp.table = /offering table/.test(all);
  if (/house shrine|ศาลเจ้าที่/.test(all)) sp.extra = 'chinese';
  var B = [['showroom', /showroom|dealership|dealer|ดีลเลอร์/], ['parts', /auto parts|อะไหล่/], ['machinery', /machinery/], ['garage', /garage|tyre|tire|service cent|diesel|machinery|ยานยนต์|ยาง|อู่/],
    ['bar', /\bbar\b|karaoke|\bclub\b|บาร์|คาราโอเกะ/], ['gym', /\bgym\b|fitness|treadmill|ยิม|ฟิตเนส/], ['dental', /dental|ทันต/], ['clinic', /clinic|hospital|คลินิก|โรงพยาบาล/],
    ['furniture', /furniture|เฟอร์นิเจอร์/], ['glassshop', /premium glass|glass shop|กระจก/], ['carpets', /carpet|พรม/], ['framing', /framing|frame\b|กรอบ/], ['sound', /\bsound\b|เสียง/],
    ['materials', /building materials|วัสดุก่อสร้าง/], ['office', /office|leasing|loan|insurance|\baia\b|srisawad|bank|ธนาคาร/], ['hotel', /hotel|resort|โรงแรม|รีสอร์ท/],
    ['restaurant', /restaurant|cafe|café|courtyard|garden restaurant|khao soi|ข้าวซอย|ร้านอาหาร|ร้านกาแฟ|การ์เด้น|tables|seating/], ['carpark', /car park|parking|ที่จอด/], ['market', /market|ตลาด|กาด/],
    ['station', /\bptt\b|petrol|ปั๊ม|gas station|fuel/], ['temple', /temple|วัด|compound/], ['shophouse', /shophouse|arcade|\bshop\b|store|ร้าน/]];
  for (var i = 0; i < B.length; i++) if (B[i][1].test(tail)) { sp.build = B[i][0]; break; }
  if (sp.build === 'garage' && /tractor|แทรกเตอร์/.test(all)) sp.build = 'showroom';
  sp.tractor = /tractor|แทรกเตอร์/.test(all);
  if (!sp.build && /house (\d+)/.test(tail)) { sp.build = 'home'; sp.houseNo = /house (\d+)/.exec(tail)[1]; }
  if (/gate|driveway|ประตู/.test(tail)) sp.gate = /behind (?:a |the )?(?:\w+ )?gate|behind the shrine fence/.test(' ' + tail.trim()) ? 'front' : 'side';
  if (/fence/.test(tail)) { sp.fence = true; }
  if (/banyan/.test(tail)) sp.green = 'banyan'; else if (/purple flower|flowers/.test(tail)) sp.green = 'flowers'; else if (/\btrees?\b/.test(tail)) sp.green = 'trees';
  else if (/greenery|hedge|bush/.test(tail)) sp.green = /behind/.test(tail) ? 'hedgefront' : 'hedge'; else if (/garden|yard/.test(tail) && !/machinery|yard wall/.test(tail)) sp.green = 'yard';
  sp.canal = /canal|river|คลอง/.test(all); sp.island = /traffic island/.test(tail); sp.poles = /pole/.test(tail); sp.hospital = /hospital|โรงพยาบาล/.test(tail);
  sp.road = /roadside|corner|island/.test(all);
  return (SPECS[id] = sp);
}

/* ---------------------------------------------------------------- the day: Bangkok hour, the light's band, what is on the table */
function stateOf(S) {
  var b = new Date((S.now || Date.now()) + 7 * 3600e3), h = b.getUTCHours() + b.getUTCMinutes() / 60, alt = S.alt != null ? S.alt : (S.night ? -20 : 40);
  var band = alt > 6 ? 0 : alt > -1 ? 1 : alt > -8 ? 2 : 3, stage, burn = 0, lit = false, items = { water: 1, garland: 1 };
  if (h >= 5 && h < 10.5) { stage = 'morning'; lit = true; burn = clamp(1 - (h - 5.5) / 4.6, 0.08, 1); items = { water: 1, red: 1, rice: 1, banana: 1, sweet: 1, garland: 1 }; }
  else if (h >= 10.5 && h < 11) { stage = 'morning'; items = { water: 1, red: 1, rice: 1, banana: 1, sweet: 1, garland: 1 }; }
  else if (h >= 11 && h < 17.5) stage = 'day'; else if (h >= 17.5 && h < 19.5) stage = 'evening'; else stage = 'night';
  return { h: h, alt: alt, band: band, stage: stage, burn: Math.round(burn * 8) / 8, lit: lit, items: items, lamp: alt < 5, candles: alt < 5 || stage === 'evening' };
}

/* ---------------------------------------------------------------- the plan: where the house, its table and the setting stand */
function plan(S, sp) {
  var W = S.W, H = S.H, deck = S.deck, r = rnd((S.seed ^ 0x2545f491) >>> 0 || 1), Q = { r: r, W: W, H: H, deck: deck, ph: S.phone, seed: S.seed >>> 0, by: deck - H * 0.04 };
  var model = sp.model, nom = NOM[model], pillar = null, nh = nom[0], hwn = nom[1];
  if (model === 'deva') { if (sp.small) { pillar = 2.6; nh -= 1.1; } if (sp.shelf) { pillar = 1.0; nh -= 2.7; } if (sp.ped) nh += 1.2; }
  if (sp.shelf) nh += 3.0;
  Q.dir = r() < 0.5 ? 1 : -1;
  var s = (deck - H * 0.055) / nh, n = sp.n, gapw = hwn * 2 * 1.12;
  var spanN = n === 2 ? gapw + hwn * 2 : hwn * 2;
  s = min(s, W * 0.5 / (spanN + 1.2));
  Q.s = s; Q.pillar = pillar; Q.nh = nh; Q.hwn = hwn; Q.gapw = gapw;
  Q.hx = Q.dir > 0 ? W * (0.29 + 0.05 * r()) : W * (0.71 - 0.05 * r());
  Q.hw = (n === 2 ? gapw / 2 + hwn : hwn) * s;
  var bwid = W * (S.phone ? 0.5 : 0.42);   /* the setting shows at the side, the frame cuts it */
  Q.bx0 = Q.dir > 0 ? max(W - bwid, Q.hx + Q.hw + s * 0.7) : -20; Q.bx1 = Q.dir > 0 ? W + 20 : min(bwid, Q.hx - Q.hw - s * 0.7);
  Q.ox0 = Q.dir > 0 ? -20 : Q.hx + Q.hw; Q.ox1 = Q.dir > 0 ? Q.hx - Q.hw : W + 20;
  return Q;
}

/* ---------------------------------------------------------------- plants */
/* a clump of leaf: discs in three greens, base at y */
function bush(q, x, y, r, cols, seed) {
  var rg = rnd(seed), i, n = 7;
  for (i = 0; i < n; i++) { var a = i / (n - 1) * PI, bx = x + cos(PI + a) * r * 0.9 + (rg() - 0.5) * r * 0.25, by = y - sin(a) * r * 0.5 - r * 0.3; dot(q, bx, by, r * (0.5 + rg() * 0.2), cols[i % 2]); }
  dot(q, x, y - r * 0.62, r * 0.72, cols[2]); dot(q, x - r * 0.22, y - r * 0.9, r * 0.32, 'rgba(255,255,215,.16)');
}
/* a tree: trunk and a canopy of overlapping discs */
function treeAt(q, x, y, h, cols, seed) {
  var rg = rnd(seed), r = h * 0.34, i;
  q.fillStyle = '#5a3d28'; q.beginPath(); q.moveTo(x - r * 0.1, y); q.lineTo(x - r * 0.06, y - h * 0.62); q.lineTo(x + r * 0.06, y - h * 0.62); q.lineTo(x + r * 0.1, y); q.closePath(); q.fill();
  var cy = y - h * 0.68;
  for (i = 0; i < 10; i++) { var a = i / 10 * TAU + rg(); dot(q, x + cos(a) * r * 0.7, cy + sin(a) * r * 0.45, r * (0.5 + rg() * 0.2), cols[i % 2]); }
  dot(q, x, cy - r * 0.12, r * 0.62, cols[2]); dot(q, x - r * 0.2, cy - r * 0.34, r * 0.34, 'rgba(255,255,215,.14)');
}
/* a banyan: a wide low canopy and aerial roots hanging to the ground */
function banyanAt(q, x, y, s, seed) {
  var rg = rnd(seed), i, cols = ['#2f6b3a', '#3f8a48', '#5aa253'];
  for (i = 0; i < 70; i++) { var a = i * 2.39996, r = sqrt(i / 70) * s * 3.1; dot(q, x + cos(a) * r * 1.35, y - s * 4.5 + sin(a) * r * 0.55, s * (0.58 - 0.2 * i / 70), cols[i % 3]); }
  q.fillStyle = '#6b4a32'; q.beginPath(); q.moveTo(x - s * 0.7, y); q.quadraticCurveTo(x - s * 0.4, y - s * 2.2, x - s * 0.55, y - s * 4.1); q.lineTo(x + s * 0.55, y - s * 4.1); q.quadraticCurveTo(x + s * 0.4, y - s * 2.2, x + s * 0.7, y); q.closePath(); q.fill();
  q.strokeStyle = '#5a3d28'; q.lineWidth = max(0.8, s * 0.07);
  for (i = 0; i < 12; i++) { var rx = x - s * 2.4 + s * 4.8 * i / 11, ry = y - s * 3.9 + abs(rx - x) * 0.05; q.beginPath(); q.moveTo(rx, ry); q.quadraticCurveTo(rx + (rg() - 0.5) * s * 0.3, y - s * 2, rx + (rg() - 0.5) * s * 0.2, y - s * (i % 3 ? 1.2 : 0)); q.stroke(); }
}
/* a clipped hedge: a run of rounded boxes with leaf-light on top, flowers if given */
function hedge(q, x0, x1, y, h, cols, seed, flower) {
  var rg = rnd(seed), x, i;
  for (x = x0; x < x1; x += h * 0.9) { rr(q, x, y - h * (0.85 + rg() * 0.15), h * 0.95, h * 1.2, h * 0.38, cols[(x / h | 0) % 2]); }
  for (x = x0; x < x1; x += h * 0.9) { rr(q, x + h * 0.08, y - h * 0.85, h * 0.8, h * 0.22, h * 0.1, 'rgba(255,255,215,.13)'); }
  if (flower) for (i = 0; i < (x1 - x0) / (h * 0.34); i++) dot(q, x0 + rg() * (x1 - x0), y - h * (0.15 + rg() * 0.7), max(1, h * 0.09), flower[i % flower.length]);
}
var GREEN = [['#2f6b3a', '#3f8a48', '#4f9a52'], ['#3a7a3f', '#4a9a4a', '#62ae58'], ['#2c5f3f', '#3a7a50', '#4c9064']];

/* ---------------------------------------------------------------- things in the shop windows and yards */
/* a car in side view, left edge x, wheels on y, length w */
function car(q, x, y, w, col) {
  var h = w * 0.4;
  function U(u, v) { return [x + u * w, y - v * h]; }
  var body = [[0.02, 0.24], [0.02, 0.5], [0.08, 0.56], [0.24, 0.6], [0.32, 0.92], [0.68, 0.95], [0.8, 0.63], [0.95, 0.58], [0.99, 0.46], [0.99, 0.24]], f = [];
  body.forEach(function (b) { var p = U(b[0], b[1]); f.push(p[0], p[1]); });
  ov(q, x + w * 0.5, y, w * 0.48, h * 0.05, 'rgba(0,0,0,.2)');
  pg(q, f, grad(q, 0, y - h, 0, y, [0, mixc(col, '#ffffff', 0.25), 0.5, col, 1, mixc(col, '#000000', 0.25)]));
  var wa = U(0.34, 0.64), wb = U(0.37, 0.87), wc = U(0.49, 0.89), wd = U(0.49, 0.64), we = U(0.53, 0.64), wf = U(0.53, 0.89), wg = U(0.66, 0.89), wh = U(0.76, 0.64);
  pg(q, [wa[0], wa[1], wb[0], wb[1], wc[0], wc[1], wd[0], wd[1]], '#bfe3f2'); pg(q, [we[0], we[1], wf[0], wf[1], wg[0], wg[1], wh[0], wh[1]], '#bfe3f2');
  ln(q, U(0.02, 0.4)[0], U(0.02, 0.4)[1], U(0.99, 0.4)[0], U(0.99, 0.4)[1], 'rgba(0,0,0,.18)', max(0.6, h * 0.025));
  [0.23, 0.78].forEach(function (u) { var p = U(u, 0.18); dot(q, p[0], p[1], h * 0.2, '#1d1d22'); dot(q, p[0], p[1], h * 0.1, '#b9bcc4'); });
  var hl = U(0.97, 0.5); dot(q, hl[0], hl[1], max(0.8, h * 0.05), '#fff3b0');
}
/* a tractor, left edge x, wheels on y, length w */
function tractor(q, x, y, w, col) {
  var h = w * 0.62;
  ov(q, x + w * 0.5, y, w * 0.5, h * 0.04, 'rgba(0,0,0,.2)');
  pg(q, [x + w * 0.46, y - h * 0.3, x + w * 0.96, y - h * 0.3, x + w * 0.96, y - h * 0.55, x + w * 0.6, y - h * 0.6, x + w * 0.46, y - h * 0.55], col);
  pg(q, [x + w * 0.12, y - h * 0.28, x + w * 0.52, y - h * 0.28, x + w * 0.52, y - h * 0.58, x + w * 0.46, y - h * 0.98, x + w * 0.16, y - h * 0.98, x + w * 0.12, y - h * 0.6], mixc(col, '#ffffff', 0.12));
  pg(q, [x + w * 0.19, y - h * 0.62, x + w * 0.19, y - h * 0.92, x + w * 0.42, y - h * 0.92, x + w * 0.44, y - h * 0.62], '#bfe3f2');
  fr(q, x + w * 0.1, y - h * 1.02, w * 0.42, h * 0.05, mixc(col, '#000000', 0.3));
  fr(q, x + w * 0.82, y - h * 0.82, w * 0.03, h * 0.28, '#2a2a2e');
  dot(q, x + w * 0.27, y - h * 0.27, h * 0.27, '#202024'); dot(q, x + w * 0.27, y - h * 0.27, h * 0.13, '#d8d8de');
  q.strokeStyle = '#3a3a40'; q.lineWidth = max(1, h * 0.04); for (var i = 0; i < 12; i++) { var a = i / 12 * TAU; q.beginPath(); q.moveTo(x + w * 0.27 + cos(a) * h * 0.27, y - h * 0.27 + sin(a) * h * 0.27); q.lineTo(x + w * 0.27 + cos(a) * h * 0.31, y - h * 0.27 + sin(a) * h * 0.31); q.stroke(); }
  dot(q, x + w * 0.84, y - h * 0.14, h * 0.14, '#202024'); dot(q, x + w * 0.84, y - h * 0.14, h * 0.07, '#d8d8de');
}
/* a standing tyre, and a pyramid of them */
function tyre(q, x, y, r) { dot(q, x, y - r, r, '#1b1b1f'); dot(q, x, y - r, r * 0.62, '#34343a'); dot(q, x, y - r, r * 0.34, '#aeb0b8'); dot(q, x - r * 0.3, y - r * 1.3, r * 0.2, 'rgba(255,255,255,.08)'); }
function tyres(q, x, y, r, rows) { for (var j = 0; j < rows; j++) for (var i = 0; i < rows - j; i++) tyre(q, x + (i - (rows - j - 1) / 2) * r * 2, y - j * r * 1.75, r); }
/* an armchair-and-sofa pair, a lamp */
function sofa(q, x, y, w) {
  var h = w * 0.36; rr(q, x, y - h * 0.62, w, h * 0.62, h * 0.12, '#b5503a'); rr(q, x + w * 0.04, y - h, w * 0.92, h * 0.5, h * 0.16, '#c9644a');
  rr(q, x - w * 0.04, y - h * 0.72, w * 0.12, h * 0.72, h * 0.1, '#a54632'); rr(q, x + w * 0.92, y - h * 0.72, w * 0.12, h * 0.72, h * 0.1, '#a54632');
  fr(q, x + w * 0.12, y - h * 0.1, w * 0.04, h * 0.1, '#5a3a2a'); fr(q, x + w * 0.84, y - h * 0.1, w * 0.04, h * 0.1, '#5a3a2a');
  fr(q, x + w * 1.2, y - h * 1.9, w * 0.02, h * 1.9, '#4a3a2a'); pg(q, [x + w * 1.08, y - h * 1.9, x + w * 1.34, y - h * 1.9, x + w * 1.28, y - h * 2.3, x + w * 1.14, y - h * 2.3], '#fff0c8');
}
/* a treadmill, side view */
function treadmill(q, x, y, w) {
  var h = w * 0.62; pg(q, [x, y - h * 0.18, x + w * 0.8, y - h * 0.3, x + w * 0.8, y - h * 0.18, x, y - h * 0.06], '#2a2d34'); pg(q, [x + w * 0.04, y - h * 0.16, x + w * 0.78, y - h * 0.28, x + w * 0.78, y - h * 0.25, x + w * 0.04, y - h * 0.13], '#6a6e78');
  ln(q, x + w * 0.74, y - h * 0.26, x + w * 0.9, y - h * 0.98, '#2a2d34', max(1.4, w * 0.04)); rr(q, x + w * 0.8, y - h * 1.06, w * 0.22, h * 0.2, h * 0.04, '#34a8c8');
  ln(q, x + w * 0.84, y - h * 0.8, x + w * 0.5, y - h * 0.62, '#2a2d34', max(1, w * 0.03)); fr(q, x + w * 0.04, y - h * 0.06, w * 0.04, h * 0.06, '#2a2d34'); fr(q, x + w * 0.74, y - h * 0.18, w * 0.04, h * 0.18, '#2a2d34');
}
/* framed pictures on a wall */
function frames(q, x0, x1, y0, y1, rg) {
  var x = x0 + (x1 - x0) * 0.04, cols = ['#c9a050', '#7a4a2a', '#2f4a6a', '#c9c0b0', '#8a2a2a'], pics = ['#9ec9a0', '#e8c070', '#7fa8d0', '#e08a7a', '#c7b3e0'];
  while (x < x1 - (x1 - x0) * 0.1) { var w = (y1 - y0) * (0.3 + rg() * 0.3), h = w * (0.8 + rg() * 0.5), yy = y0 + (y1 - y0) * (0.12 + rg() * 0.3); fr(q, x, yy, w, h, pick(rg, cols)); fr(q, x + w * 0.1, yy + w * 0.1, w * 0.8, h - w * 0.2, pick(rg, pics)); x += w * 1.25; }
}
/* speaker cabinets */
function speakers(q, x, y, w, n) {
  for (var i = 0; i < n; i++) { var bw = w * 0.5, bh = bw * 1.5, bx = x + i * bw * 1.2, by = y - (i % 2) * bh * 0.2; rr(q, bx, by - bh, bw, bh, bw * 0.06, '#232328'); dot(q, bx + bw / 2, by - bh * 0.7, bw * 0.3, '#3a3a42'); dot(q, bx + bw / 2, by - bh * 0.7, bw * 0.12, '#15151a'); dot(q, bx + bw / 2, by - bh * 0.25, bw * 0.18, '#3a3a42'); }
}
/* carpet rolls standing in a rack */
function rolls(q, x, y, w, rg) {
  var n = max(3, Math.round(w / (w * 0.16))), cols = ['#a83a3a', '#2f5a8a', '#c98a2a', '#3a7a5a', '#7a3a7a'];
  for (var i = 0; i < n; i++) { var rw = w / n * 0.84, rh = w * 0.34 * (0.8 + rg() * 0.3), rx = x + i * w / n, c0 = cols[i % 5]; rr(q, rx, y - rh, rw, rh, rw * 0.46, c0); ov(q, rx + rw / 2, y - rh, rw / 2, rw * 0.18, mixc(c0, '#ffffff', 0.3)); ln(q, rx + rw * 0.2, y - rh * 0.7, rx + rw * 0.2, y - rh * 0.1, 'rgba(255,255,255,.3)', max(0.8, rw * 0.1)); }
}
/* glass sheets leaning in an A-frame rack */
function panes(q, x, y, w, h) {
  for (var i = 0; i < 5; i++) { var bx = x + i * w * 0.18; pg(q, [bx, y, bx + w * 0.26, y, bx + w * 0.3, y - h, bx + w * 0.04, y - h], 'rgba(170,215,235,.55)', 'rgba(255,255,255,.6)', 1); }
  fr(q, x - w * 0.02, y - h * 0.04, w * 1.1, h * 0.05, '#4a4a52');
}
/* cement sacks stacked, a bundle of pipes */
function sacks(q, x, y, w, h) {
  for (var j = 0; j < 3; j++) for (var i = 0; i < 4 - j; i++) { var sw = w * 0.2, sx = x + (i + j * 0.5) * sw * 1.05; rr(q, sx, y - (j + 1) * h * 0.2, sw, h * 0.2, h * 0.04, j % 2 ? '#c9c4b8' : '#b9b4a8'); fr(q, sx + sw * 0.2, y - (j + 1) * h * 0.2 + h * 0.06, sw * 0.6, h * 0.05, '#2f5a8a'); }
  for (var k = 0; k < 6; k++) dot(q, x + w * 0.82 + (k % 3) * w * 0.07, y - h * 0.08 - Math.floor(k / 3) * h * 0.14, h * 0.07, k % 2 ? '#9aa0a8' : '#7a8088');
}
/* shelves of boxes and cans (auto parts) */
function shelves(q, x0, x1, y0, y1, rg) {
  var rows = 3, cols = ['#f2c94c', '#2c5aa0', '#c62a20', '#f4f1ea', '#e8692a'], i, j;
  for (j = 0; j < rows; j++) {
    var yy = y0 + (y1 - y0) * (j + 1) / rows; fr(q, x0, yy - 2, x1 - x0, 2.4, '#5a5048');
    for (var x = x0 + 3; x < x1 - 8; x += 6 + rg() * 10) { var bw = 5 + rg() * 9, bh = (y1 - y0) / rows * (0.35 + rg() * 0.4); rr(q, x, yy - 2 - bh, bw, bh, 1, pick(rg, cols)); x += bw; }
  }
}
/* a desk, screen and chair */
function desk(q, x, y, w) {
  var h = w * 0.34; fr(q, x, y - h * 0.5, w, h * 0.08, '#8a6a48'); fr(q, x + w * 0.05, y - h * 0.42, w * 0.04, h * 0.42, '#6a4a2e'); fr(q, x + w * 0.9, y - h * 0.42, w * 0.04, h * 0.42, '#6a4a2e');
  rr(q, x + w * 0.3, y - h * 1.15, w * 0.3, h * 0.55, h * 0.04, '#2a2d34'); rr(q, x + w * 0.32, y - h * 1.12, w * 0.26, h * 0.4, h * 0.03, '#7ec8e8'); fr(q, x + w * 0.44, y - h * 0.6, w * 0.02, h * 0.1, '#2a2d34');
  rr(q, x + w * 0.7, y - h * 0.34, w * 0.26, h * 0.1, h * 0.04, '#3a3a42'); fr(q, x + w * 0.82, y - h * 0.24, w * 0.02, h * 0.24, '#3a3a42');
}
/* a bottle shelf, lit */
function bottles(q, x0, x1, y0, y1, rg) {
  var cols = ['#c9a050', '#6aa87a', '#c0392b', '#4a7ab8', '#e8d8a0'];
  fr(q, x0, y0, x1 - x0, y1 - y0, '#2a2030');
  for (var j = 1; j <= 2; j++) { var yy = y0 + (y1 - y0) * j / 2.4; fr(q, x0, yy, x1 - x0, 1.6, '#6a5a48'); for (var x = x0 + 2; x < x1 - 4; x += 4 + rg() * 3) { var bh = (y1 - y0) * 0.3 * (0.8 + rg() * 0.4); rr(q, x, yy - bh, 2.8, bh, 1, pick(rg, cols)); } }
}
/* an excavator, left edge x, tracks on y, length w */
function excavator(q, x, y, w) {
  var h = w * 0.62, col = '#e8b22a';
  rr(q, x, y - h * 0.16, w * 0.62, h * 0.16, h * 0.08, '#2a2a2e');
  rr(q, x + w * 0.04, y - h * 0.4, w * 0.48, h * 0.26, h * 0.04, col); pg(q, [x + w * 0.04, y - h * 0.66, x + w * 0.3, y - h * 0.66, x + w * 0.36, y - h * 0.4, x + w * 0.04, y - h * 0.4], col); pg(q, [x + w * 0.1, y - h * 0.62, x + w * 0.28, y - h * 0.62, x + w * 0.32, y - h * 0.44, x + w * 0.1, y - h * 0.44], '#bfe3f2');
  q.strokeStyle = col; q.lineWidth = max(2, h * 0.09); q.lineCap = 'round'; q.lineJoin = 'round'; q.beginPath(); q.moveTo(x + w * 0.4, y - h * 0.5); q.lineTo(x + w * 0.72, y - h * 1.08); q.lineTo(x + w * 0.98, y - h * 0.7); q.stroke();
  pg(q, [x + w * 0.94, y - h * 0.72, x + w * 1.04, y - h * 0.74, x + w * 1.02, y - h * 0.48, x + w * 0.9, y - h * 0.46], '#6a6e78');
}
/* an awning of alternating stripes with a scalloped lower edge */
function awning(q, x0, x1, y, h, c1, c2, n) {
  var w = (x1 - x0) / n, i;
  for (i = 0; i < n; i++) { var ax = x0 + i * w; pg(q, [ax, y, ax + w, y, ax + w * 1.04, y + h * 0.78, ax - w * 0.04, y + h * 0.78], i % 2 ? c2 : c1); q.fillStyle = i % 2 ? c2 : c1; q.beginPath(); q.arc(ax + w / 2, y + h * 0.78, w / 2, 0, PI); q.fill(); }
  fr(q, x0 - 1, y - 1.5, x1 - x0 + 2, 2.5, 'rgba(0,0,0,.2)');
}
/* a string of small bulbs on a catenary */
function bulbs(q, x0, x1, y, sag, n, cols, L, st) {
  var pts = [], a = (x1 - x0) / 2 / 1.4, xm = (x0 + x1) / 2, ch = Math.cosh((x1 - x0) / 2 / a) - 1;
  q.strokeStyle = 'rgba(30,20,20,.7)'; q.lineWidth = 0.9; q.beginPath();
  for (var i = 0; i <= n; i++) { var x = x0 + (x1 - x0) * i / n, yy = y + sag - sag * (Math.cosh((x - xm) / a) - 1) / ch; i ? q.lineTo(x, yy) : q.moveTo(x, yy); pts.push([x, yy]); } q.stroke();
  pts.forEach(function (p, i) { dot(q, p[0], p[1] + 1.4, 1.5, cols[i % cols.length]); });
  if (st && st.lamp) L.push(function (c, t) { c.save(); c.globalCompositeOperation = 'lighter'; for (var j = 0; j < pts.length; j += 2) lamp(c, pts[j][0], pts[j][1] + 1.4, 7, cols[j % cols.length], 0.55 + 0.25 * sin(t * 2 + j)); c.restore(); });
}
/* the shop's sign board: a roundel with an icon, two bars for the name */
function signBoard(q, x, y, w, h, bg, fg, icon) {
  rr(q, x, y, w, h, h * 0.14, bg); q.strokeStyle = rgba(fg, 0.55); q.lineWidth = max(0.8, h * 0.05); q.strokeRect(x + h * 0.08, y + h * 0.08, w - h * 0.16, h * 0.84);
  var tx = x + h * 0.2;
  if (icon) {
    var cx = x + h * 0.62, cy = y + h * 0.5, r = h * 0.34; dot(q, cx, cy, r, rgba(fg, 0.95));
    if (icon === 'car') car(q, cx - r * 0.78, cy + r * 0.34, r * 1.56, bg);
    else if (icon === 'tyre') { dot(q, cx, cy, r * 0.72, bg); dot(q, cx, cy, r * 0.28, rgba(fg, 0.95)); }
    else if (icon === 'cross') { fr(q, cx - r * 0.18, cy - r * 0.62, r * 0.36, r * 1.24, '#2f8f5b'); fr(q, cx - r * 0.62, cy - r * 0.18, r * 1.24, r * 0.36, '#2f8f5b'); }
    else if (icon === 'redcross') { fr(q, cx - r * 0.18, cy - r * 0.62, r * 0.36, r * 1.24, '#c62a20'); fr(q, cx - r * 0.62, cy - r * 0.18, r * 1.24, r * 0.36, '#c62a20'); }
    else if (icon === 'tooth') { q.fillStyle = '#2c7aa8'; q.beginPath(); q.moveTo(cx - r * 0.5, cy - r * 0.5); q.quadraticCurveTo(cx, cy - r * 0.8, cx + r * 0.5, cy - r * 0.5); q.quadraticCurveTo(cx + r * 0.55, cy + r * 0.2, cx + r * 0.25, cy + r * 0.72); q.quadraticCurveTo(cx + r * 0.1, cy + r * 0.2, cx, cy + r * 0.2); q.quadraticCurveTo(cx - r * 0.1, cy + r * 0.2, cx - r * 0.25, cy + r * 0.72); q.quadraticCurveTo(cx - r * 0.55, cy + r * 0.2, cx - r * 0.5, cy - r * 0.5); q.fill(); }
    else if (icon === 'dumbbell') { ln(q, cx - r * 0.6, cy, cx + r * 0.6, cy, bg, max(1.2, r * 0.18)); fr(q, cx - r * 0.7, cy - r * 0.38, r * 0.26, r * 0.76, bg); fr(q, cx + r * 0.44, cy - r * 0.38, r * 0.26, r * 0.76, bg); }
    tx = x + h * 1.08;
  }
  var bw = w - (tx - x) - h * 0.24; if (bw > h * 0.6) { rr(q, tx, y + h * 0.28, bw * 0.86, h * 0.17, h * 0.07, rgba(fg, 0.95)); rr(q, tx, y + h * 0.56, bw * 0.55, h * 0.13, h * 0.06, rgba(fg, 0.7)); }
}
/* a lit lamp at night, drawn live: additive glow with a slow flicker */
function nightLamp(L, st, x, y, r, col, a, flick) {
  if (!st.lamp) return;
  L.push(function (c, t) { c.save(); c.globalCompositeOperation = 'lighter'; lamp(c, x, y, r, col, a * (1 - (flick || 0) + (flick || 0) * (0.6 + 0.4 * sin(t * 9 + x) * sin(t * 2.3))) * (st.band === 1 ? 0.5 : 1)); c.restore(); });
}

/* a thin haze over a building, to set it back from the house */
function veil(q, x0, ty, x1, by) { q.save(); q.globalCompositeOperation = 'source-atop'; q.fillStyle = 'rgba(214,228,236,.2)'; q.fillRect(x0, ty - 5, x1 - x0, by - ty + 5); q.restore(); }

/* ---------------------------------------------------------------- the ground */
function ground(q, Q, sp, st) {
  var W = Q.W, H = Q.H, deck = Q.deck, gy = Q.by, kind = sp.island || sp.road ? 'road' : sp.canal ? 'canal' : (sp.green === 'yard' || sp.green === 'trees' || sp.green === 'flowers' || sp.green === 'hedge' || sp.green === 'hedgefront' || sp.green === 'banyan') ? 'lawn' : 'paved';
  Q.groundKind = kind;
  var pav = ['#d9cfb9', '#c5b99f'], lawn = ['#8fb46a', '#74a055'];
  K.paper(q, K.rect(-6, gy, W + 12, H - gy + 6), '#d2c7ad', 0.6);
  var g = q.createLinearGradient(0, gy, 0, H); g.addColorStop(0, kind === 'lawn' ? lawn[0] : pav[0]); g.addColorStop(1, kind === 'lawn' ? lawn[1] : pav[1]); q.fillStyle = g; q.fillRect(-6, gy, W + 12, H - gy + 6);
  var rg = rnd(Q.seed || 5), i;
  q.fillStyle = vgrad(q, gy, H, 'rgba(70,50,30,.1)', 'rgba(70,50,30,0)'); q.fillRect(-6, gy, W + 12, (H - gy) * 0.4);
  if (kind === 'paved' || kind === 'road') {   /* paving joints */
    q.strokeStyle = 'rgba(80,70,55,.16)'; q.lineWidth = 1;
    for (var yy = gy + (H - gy) * 0.34; yy < deck + (H - deck) * 0.7; yy += (H - gy) * 0.34) { q.beginPath(); q.moveTo(0, yy); q.lineTo(W, yy); q.stroke(); }
    for (var xx = rg() * 40; xx < W; xx += 46 + rg() * 20) { q.beginPath(); q.moveTo(xx, gy); q.lineTo(xx - 14, deck + (H - deck) * 0.7); q.stroke(); }
  }
  if (kind === 'lawn') { q.strokeStyle = 'rgba(60,110,50,.5)'; q.lineWidth = 1.1; for (i = 0; i < W / 3; i++) { var bx = rg() * W, by2 = gy + 4 + rg() * (H - gy - 4); q.beginPath(); q.moveTo(bx, by2); q.lineTo(bx + (rg() - 0.5) * 3, by2 - 3 - rg() * 3); q.stroke(); } }
  if (kind === 'road') {   /* a kerb in bands, the road below */
    var ky = deck + (H - deck) * 0.5, rh = H - ky;
    for (var kx = 0; kx < W; kx += 14) fr(q, kx, ky, 14, max(2, rh * 0.18), (kx / 14 | 0) % 2 ? '#2a2a2e' : '#f4f1ea');
    q.fillStyle = vgrad(q, ky, H, '#5c5a60', '#46444a'); q.fillRect(0, ky + max(2, rh * 0.18), W, H - ky);
    q.fillStyle = 'rgba(245,240,220,.65)'; for (var dx = 0; dx < W; dx += 46) q.fillRect(dx, ky + rh * 0.66, 24, max(1, rh * 0.06));
  }
  if (kind === 'canal') {   /* a canal in the foreground: a concrete lip, a railing, the water below */
    var ky = deck + (H - deck) * 0.4, lip = max(3, (H - deck) * 0.12);
    K.paper(q, K.rect(-6, ky + lip, W + 12, H - ky - lip + 6), '#4b8fc9', 0.5);
    q.fillStyle = vgrad(q, ky + lip, H, '#5aa0d4', '#3a78ae'); q.fillRect(-6, ky + lip, W + 12, H - ky - lip + 6);
    q.fillStyle = 'rgba(255,255,255,.35)'; for (i = 0; i < 14; i++) q.fillRect(rg() * W, ky + lip + (H - ky - lip) * (0.15 + rg() * 0.7), 8 + rg() * 14, 1.2);
    fr(q, -6, ky, W + 12, lip, '#cfc6b2'); fr(q, -6, ky, W + 12, 2, '#efe9da'); fr(q, -6, ky + lip - 1.5, W + 12, 1.5, 'rgba(60,50,40,.3)');
    var rh2 = H * 0.05; for (var rx = 4; rx < W; rx += 16) fr(q, rx, ky - rh2, 1.8, rh2, '#7a7e86'); fr(q, -6, ky - rh2, W + 12, 2, '#7a7e86'); fr(q, -6, ky - rh2 * 0.5, W + 12, 1.4, '#7a7e86');
  }
}

/* ---------------------------------------------------------------- buildings and the places they stand for */
var DARKW = ['#5d6f84', '#76675a', '#4c6a5c', '#7d5648', '#4f5878'];
/* the wall of a building: paper, a cap, a shaded side, a stained top, a plinth */
function wallOf(q, x0, x1, ty, by, col) {
  K.paper(q, K.rect(x0, ty, x1 - x0, by - ty), col, 1.2);
  q.fillStyle = vgrad(q, ty, by, rgba('#ffffff', 0.14), rgba('#000000', 0.1)); q.fillRect(x0, ty, x1 - x0, by - ty);
  fr(q, x0 - 2, ty - 3, x1 - x0 + 4, 4, mixc(col, '#000000', 0.28)); fr(q, x0 - 2, ty - 3, x1 - x0 + 4, 1.4, mixc(col, '#ffffff', 0.4));
  fr(q, x0, by - 3, x1 - x0, 3, mixc(col, '#000000', 0.32));
  q.fillStyle = 'rgba(60,50,40,.07)'; for (var x = x0 + 14; x < x1; x += 31) fr(q, x, ty, 3, (by - ty) * 0.4, 'rgba(60,50,40,.07)');
}
var BK = {
  showroom: { front: 'glass', item: 'car', sign: ['#1f4a80', '#ffffff'], icon: 'car', h: 0.5, wall: '#e9eef2' },
  parts: { front: 'open', item: 'parts', sign: ['#c62a20', '#f2c94c'], icon: 'tyre', h: 0.46, wall: '#efe6d2' },
  garage: { front: 'shutter', item: 'tyres', sign: ['#f2c94c', '#1f2a44'], icon: 'tyre', h: 0.46, wall: '#dfe9ee' },
  bar: { front: 'door', sign: ['#1c1624', '#ff5ca8'], h: 0.5, wall: '#3b3248' },
  gym: { front: 'glass', item: 'treadmill', sign: ['#1f2a44', '#f2c94c'], icon: 'dumbbell', h: 0.5, wall: '#e4ecd9' },
  dental: { front: 'glass', item: 'chair', sign: ['#ffffff', '#2c7aa8'], icon: 'tooth', h: 0.5, wall: '#f4f7f8' },
  clinic: { front: 'glass', item: 'desk', sign: ['#ffffff', '#2f8f5b'], icon: 'cross', h: 0.5, wall: '#f4f7f8' },
  furniture: { front: 'glass', item: 'sofa', sign: ['#6a3a1e', '#f2c94c'], h: 0.48, wall: '#f1dcc8' },
  glassshop: { front: 'open', item: 'panes', sign: ['#2c5aa0', '#f4f1ea'], h: 0.46, wall: '#dfe9ee' },
  carpets: { front: 'open', item: 'rolls', sign: ['#7a2a2a', '#f2c94c'], h: 0.46, wall: '#f3e9b8' },
  framing: { front: 'glass', item: 'frames', sign: ['#1f2a44', '#f4f1ea'], h: 0.48, wall: '#e9dde8' },
  sound: { front: 'glass', item: 'speakers', sign: ['#1c1c22', '#e8692a'], h: 0.48, wall: '#dcd7cd' },
  materials: { front: 'open', item: 'sacks', sign: ['#2f8f5b', '#f4f1ea'], h: 0.46, wall: '#e8d4b0' },
  office: { front: 'glass', item: 'desk', sign: ['#2c5aa0', '#f4f1ea'], h: 0.52, wall: '#dfe6ee' },
  shophouse: { front: 'shutter', item: null, sign: ['#c62a20', '#f2c94c'], h: 0.56, wall: '#efe3c8', floors: 2 }
};
/* a building along the side of the frame: its box, its signboard, its shop floor */
function shop(q, Q, sp, st, L, kind) {
  var B = BK[kind], icon = kind === 'clinic' && sp.hospital ? 'redcross' : B.icon, W = Q.W, H = Q.H, by = Q.by, rg = rnd(Q.seed + 3), bh = H * (B.h || 0.48) * 0.74, ty = by - bh;
  var x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, wall = B.wall;
  if (Q.col === 'white' && lum(wall) > 190) wall = pick(rg, DARKW);   /* a white house stands against a darker wall */
  wallOf(q, x0, x1, ty, by, wall);
  var fl2 = B.floors === 2;
  if (fl2) {   /* upper storey windows with grilles and plants, a floor line */
    var ux0 = vx0 + vw * 0.08, uw = vw * 0.84, n = max(2, Math.round(uw / (H * 0.2))), ww = uw / n * 0.62;
    fr(q, x0, ty + bh * 0.46, x1 - x0, 3, mixc(wall, '#000000', 0.2));
    for (var i = 0; i < n; i++) { var wx = ux0 + uw / n * (i + 0.19); fr(q, wx, ty + bh * 0.12, ww, bh * 0.26, '#3a4a5a'); fr(q, wx, ty + bh * 0.12, ww, bh * 0.07, 'rgba(255,255,255,.18)'); for (var gx = 1; gx < 4; gx++) fr(q, wx + ww * gx / 4, ty + bh * 0.12, 1, bh * 0.26, 'rgba(20,20,24,.7)'); fr(q, wx - 2, ty + bh * 0.39, ww + 4, bh * 0.04, '#7a7e86'); if (i % 2) { bush(q, wx + ww * 0.5, ty + bh * 0.39, ww * 0.34, GREEN[i % 3], Q.seed + i); } }
  }
  var sy = ty + bh * (fl2 ? 0.5 : 0.12), sh = bh * (fl2 ? 0.13 : 0.2), sx0 = vx0 + vw * 0.06, sw = vw * 0.88;
  signBoard(q, sx0, sy, sw, sh, B.sign[0], B.sign[1], icon);
  var oy0 = sy + sh + bh * 0.04, oy1 = by - 3, ox0 = sx0, ox1 = sx0 + sw;
  if (B.front === 'glass') {
    fr(q, ox0 - 3, oy0 - 3, ox1 - ox0 + 6, oy1 - oy0 + 3, mixc(wall, '#000000', 0.35));
    q.fillStyle = vgrad(q, oy0, oy1, '#9fc7d8', '#d6e9ee'); q.fillRect(ox0, oy0, ox1 - ox0, oy1 - oy0);
    q.fillStyle = vgrad(q, oy1 - (oy1 - oy0) * 0.22, oy1, rgba('#e9e2d0', 0), '#e9e2d0'); q.fillRect(ox0, oy1 - (oy1 - oy0) * 0.22, ox1 - ox0, (oy1 - oy0) * 0.22);
    var ih = oy1 - oy0;
    if (B.item === 'car' && sp.tractor) { var tw0 = min(ih * 1.7, (ox1 - ox0) * 0.34); tractor(q, ox0 + (ox1 - ox0) * 0.12, oy1 - ih * 0.04, tw0, '#e8692a'); tractor(q, ox0 + (ox1 - ox0) * 0.55, oy1 - ih * 0.04, tw0 * 0.9, '#2f8f5b'); }
    else if (B.item === 'car') { var cw = min(ih * 1.9, (ox1 - ox0) * 0.4), nc = max(1, Math.floor((ox1 - ox0) / (cw * 1.1))); for (var c1 = 0; c1 < nc; c1++) car(q, ox0 + (ox1 - ox0 - nc * cw * 1.1) / 2 + c1 * cw * 1.1 + cw * 0.05, oy1 - ih * 0.04, cw, pick(rg, ['#c62a20', '#f4f1ea', '#2c5aa0', '#2a2d34', '#e8b22a'])); }
    else if (B.item === 'treadmill') { var tw = min(ih * 1.5, (ox1 - ox0) * 0.3), nt = max(1, Math.floor((ox1 - ox0) / (tw * 1.3))); for (var t1 = 0; t1 < nt; t1++) treadmill(q, ox0 + ((ox1 - ox0) - nt * tw * 1.3) / 2 + t1 * tw * 1.3 + tw * 0.15, oy1 - ih * 0.05, tw); }
    else if (B.item === 'sofa') { var sw2 = min(ih * 1.6, (ox1 - ox0) * 0.36); sofa(q, ox0 + (ox1 - ox0) * 0.12, oy1 - ih * 0.05, sw2); sofa(q, ox0 + (ox1 - ox0) * 0.58, oy1 - ih * 0.05, sw2 * 0.8); }
    else if (B.item === 'frames') frames(q, ox0, ox1, oy0, oy1, rg);
    else if (B.item === 'speakers') speakers(q, ox0 + (ox1 - ox0) * 0.1, oy1 - ih * 0.05, min(ih * 0.9, (ox1 - ox0) * 0.12), 6);
    else if (B.item === 'desk') { var dw = min(ih * 1.4, (ox1 - ox0) * 0.3); desk(q, ox0 + (ox1 - ox0) * 0.14, oy1 - ih * 0.05, dw); desk(q, ox0 + (ox1 - ox0) * 0.55, oy1 - ih * 0.05, dw); }
    else if (B.item === 'chair') { var dw2 = min(ih * 1.2, (ox1 - ox0) * 0.3); rr(q, ox0 + (ox1 - ox0) * 0.3, oy1 - ih * 0.5, dw2 * 0.3, ih * 0.45, 3, '#2c7aa8'); fr(q, ox0 + (ox1 - ox0) * 0.3 + dw2 * 0.12, oy1 - ih * 0.06, dw2 * 0.06, ih * 0.06, '#7a7e86'); rr(q, ox0 + (ox1 - ox0) * 0.3 - dw2 * 0.2, oy1 - ih * 0.62, dw2 * 0.4, ih * 0.14, 3, '#2c7aa8'); }
    q.fillStyle = 'rgba(255,255,255,.2)'; q.beginPath(); q.moveTo(ox0 + (ox1 - ox0) * 0.1, oy0); q.lineTo(ox0 + (ox1 - ox0) * 0.2, oy0); q.lineTo(ox0 + (ox1 - ox0) * 0.1, oy1); q.lineTo(ox0, oy1); q.closePath(); q.fill();
    q.beginPath(); q.moveTo(ox0 + (ox1 - ox0) * 0.55, oy0); q.lineTo(ox0 + (ox1 - ox0) * 0.62, oy0); q.lineTo(ox0 + (ox1 - ox0) * 0.52, oy1); q.lineTo(ox0 + (ox1 - ox0) * 0.45, oy1); q.closePath(); q.fill();
    var mn = max(3, Math.round((ox1 - ox0) / (H * 0.55))); for (var mi = 1; mi < mn; mi++) fr(q, ox0 + (ox1 - ox0) * mi / mn - 1, oy0, 2, ih, mixc(wall, '#000000', 0.4));
    if (kind === 'showroom' && !Q.ph) { bulbs(q, ox0, ox1, ty - 2, -4, 22, ['#c62a20', '#f2c94c', '#ffffff', '#2c5aa0'], L, st); }
    nightLamp(L, st, (ox0 + ox1) / 2, (oy0 + oy1) / 2, (ox1 - ox0) * 0.5, '#ffe6a8', 0.35, 0);
  } else if (B.front === 'shutter') {
    var up = 0.58; fr(q, ox0 - 3, oy0 - 3, ox1 - ox0 + 6, oy1 - oy0 + 3, mixc(wall, '#000000', 0.35)); fr(q, ox0, oy0, ox1 - ox0, oy1 - oy0, '#2b2b30');
    var sh2 = (oy1 - oy0) * (1 - up); q.fillStyle = '#8f98a2'; q.fillRect(ox0, oy0, ox1 - ox0, sh2); q.strokeStyle = 'rgba(40,50,60,.45)'; q.lineWidth = 1; for (var yy = oy0 + 3; yy < oy0 + sh2; yy += 3.4) { q.beginPath(); q.moveTo(ox0, yy); q.lineTo(ox1, yy); q.stroke(); }
    fr(q, ox0, oy0 + sh2 - 2, ox1 - ox0, 2.6, '#5a626c');
    if (B.item === 'tyres') { var tr = (oy1 - oy0) * 0.16; for (var k2 = 0; k2 < 5; k2++) tyre(q, ox0 + (ox1 - ox0) * (0.14 + k2 * 0.18), oy1, tr); }
    nightLamp(L, st, (ox0 + ox1) / 2, oy1 - (oy1 - oy0) * 0.25, (ox1 - ox0) * 0.35, '#ffe6a8', 0.4, 0);
    if (kind === 'garage') { tyres(q, Q.bx0 + (ox1 - ox0) * 0.06, by + H * 0.012, H * 0.034, 3); }
  } else if (B.front === 'open') {
    fr(q, ox0 - 3, oy0 - 3, ox1 - ox0 + 6, oy1 - oy0 + 3, mixc(wall, '#000000', 0.35)); fr(q, ox0, oy0, ox1 - ox0, oy1 - oy0, '#3a3430');
    var ih2 = oy1 - oy0;
    if (B.item === 'parts') shelves(q, ox0 + 3, ox1 - 3, oy0 + 3, oy1, rg);
    else if (B.item === 'panes') panes(q, ox0 + (ox1 - ox0) * 0.1, oy1, (ox1 - ox0) * 0.4, ih2 * 0.9);
    else if (B.item === 'rolls') rolls(q, ox0 + (ox1 - ox0) * 0.06, oy1, (ox1 - ox0) * 0.6, rg);
    else if (B.item === 'sacks') sacks(q, ox0 + (ox1 - ox0) * 0.06, oy1, (ox1 - ox0) * 0.7, ih2 * 0.9);
    nightLamp(L, st, (ox0 + ox1) / 2, (oy0 + oy1) / 2, (ox1 - ox0) * 0.4, '#ffe6a8', 0.3, 0);
    if (kind === 'parts') { tyres(q, ox1 - (ox1 - ox0) * 0.12, by + H * 0.012, H * 0.03, 3); }
  } else if (B.front === 'door') {   /* bar: a dark door, bottle shelf, neon */
    fr(q, ox0 - 3, oy0 - 3, ox1 - ox0 + 6, oy1 - oy0 + 3, '#1a1420'); fr(q, ox0, oy0, ox1 - ox0, oy1 - oy0, '#241c2c');
    var dw3 = (ox1 - ox0) * 0.3, dx3 = ox0 + (ox1 - ox0) * 0.35; fr(q, dx3, oy0 + (oy1 - oy0) * 0.12, dw3, (oy1 - oy0) * 0.88, '#4a3a2e'); fr(q, dx3 + dw3 * 0.1, oy0 + (oy1 - oy0) * 0.2, dw3 * 0.8, (oy1 - oy0) * 0.5, '#e9b25a');
    bottles(q, ox0 + (ox1 - ox0) * 0.06, ox0 + (ox1 - ox0) * 0.3, oy0 + (oy1 - oy0) * 0.2, oy0 + (oy1 - oy0) * 0.7, rg); bottles(q, ox0 + (ox1 - ox0) * 0.7, ox0 + (ox1 - ox0) * 0.94, oy0 + (oy1 - oy0) * 0.2, oy0 + (oy1 - oy0) * 0.7, rg);
    q.strokeStyle = '#ff5ca8'; q.lineWidth = max(1.6, H * 0.01); q.lineCap = 'round'; q.beginPath(); q.moveTo(sx0 + sw * 0.1, sy + sh * 0.5); q.quadraticCurveTo(sx0 + sw * 0.2, sy + sh * 0.1, sx0 + sw * 0.3, sy + sh * 0.5); q.quadraticCurveTo(sx0 + sw * 0.4, sy + sh * 0.9, sx0 + sw * 0.5, sy + sh * 0.5); q.stroke();
    bulbs(q, ox0, ox1, oy0 - 3, 5, 14, ['#ff5ca8', '#ffd166', '#7fe0ff'], L, st);
    nightLamp(L, st, sx0 + sw * 0.5, sy + sh * 0.5, min(sw * 0.3, H * 0.2), '#ff4fa3', 0.35, 0.35); nightLamp(L, st, dx3 + dw3 / 2, oy0 + (oy1 - oy0) * 0.45, dw3 * 1.4, '#ffb347', 0.45, 0.2);
  }
  /* an awning over the front of the shophouse and the garage's roll box */
  if (kind === 'shophouse') awning(q, ox0, ox1, oy0 - 2, bh * 0.1, '#c62a20', '#f4f1ea', max(6, Math.round((ox1 - ox0) / 22)));
  Q.bldTop = ty;
  return { x0: vx0, x1: vx1 };
}
/* a hotel: two floors of blue glass, a gilt portico, flags */
function hotel(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, bh = H * 0.5, ty = by - bh, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, rg = rnd(Q.seed + 9), wall = Q.col === 'white' ? '#9a8a74' : '#efe3c8';
  wallOf(q, x0, x1, ty, by, wall);
  var rows = 3, n = max(3, Math.round(vw / (H * 0.17))), i, j;
  for (j = 0; j < rows; j++) for (i = 0; i < n; i++) { var wx = vx0 + vw * 0.06 + (vw * 0.88) / n * (i + 0.15), ww = (vw * 0.88) / n * 0.7, wy = ty + bh * (0.08 + j * 0.22); fr(q, wx, wy, ww, bh * 0.14, '#4b6a8a'); fr(q, wx, wy, ww, bh * 0.04, 'rgba(255,255,255,.28)'); fr(q, wx - 2, wy + bh * 0.145, ww + 4, 2.4, '#bdb5a0'); if (st.lamp && (i * 3 + j * 5 + Q.seed) % 4 === 0) { fr(q, wx, wy, ww, bh * 0.14, '#ffd98a'); } }
  var px = vx0 + vw * 0.5, pw = min(vw * 0.5, H * 0.9), py = by - bh * 0.4, pt = ty + bh * 0.62;
  fr(q, px - pw / 2, pt, pw, py - pt + bh * 0.4 - 3, '#3a4a5a');
  fr(q, px - pw * 0.34, pt + (by - pt) * 0.18, pw * 0.68, (by - pt) * 0.8 - 3, '#bfe3f2'); fr(q, px - 1, pt + (by - pt) * 0.18, 2, (by - pt) * 0.8 - 3, '#4a5a6a');
  pg(q, [px - pw * 0.58, pt, px + pw * 0.58, pt, px + pw * 0.54, pt - bh * 0.1, px - pw * 0.54, pt - bh * 0.1], '#e0ac2a', '#fff2b8', 1); fr(q, px - pw * 0.58, pt - 1, pw * 1.16, 3, '#9a6b0c');
  [-0.52, 0.52].forEach(function (k) { q.fillStyle = grad(q, px + k * pw - 4, 0, px + k * pw + 4, 0, [0, '#9a6b0c', 0.5, '#ffe48a', 1, '#9a6b0c']); q.fillRect(px + k * pw - 4, pt, 8, by - pt - 3); });
  signBoard(q, px - pw * 0.3, pt - bh * 0.34, pw * 0.6, bh * 0.2, '#3a2a1a', '#e0ac2a', null);
  for (i = 0; i < 3; i++) { var fx = vx0 + vw * (i === 0 ? 0.08 : i === 1 ? 0.18 : 0.92); if (Q.ph && i === 2) continue; ln(q, fx, ty - 2, fx, ty - bh * 0.3, '#9a9aa2', 1.4); pg(q, [fx, ty - bh * 0.3, fx + H * 0.07, ty - bh * 0.27, fx, ty - bh * 0.23], ['#c62a20', '#2c5aa0', '#2f8f5b'][i]); }
  nightLamp(L, st, px, pt + (by - pt) * 0.5, pw * 0.6, '#ffe6a8', 0.5, 0);
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
/* a restaurant courtyard: a pergola with lights, tables under parasols, pots */
function restaurant(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, deck = Q.deck, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, rg = rnd(Q.seed + 5), ty = by - H * 0.38;
  wallOf(q, x0, x1, ty, by, Q.col === 'white' ? '#6a5a48' : '#e9d3a8');
  var pw = vw * 0.9, px0 = vx0 + vw * 0.05, top = ty + H * 0.02, i;
  fr(q, px0, top, pw, H * 0.03, '#6a4126'); for (i = 0; i <= 3; i++) fr(q, px0 + pw * i / 3 - 2, top, 4, by - top, '#7a4a2a');
  for (var rx = px0; rx < px0 + pw; rx += 9) fr(q, rx, top - 3, 3, H * 0.05, '#7a4a2a');
  bulbs(q, px0 + 4, px0 + pw - 4, top + H * 0.05, 6, 16, ['#ffd98a', '#fff3c4'], L, st);
  var nt = Q.ph ? 1 : 2;
  for (i = 0; i < nt; i++) {
    var tx = px0 + pw * (0.22 + i * 0.5), ty2 = by + H * 0.012, tw = H * 0.17;
    fr(q, tx - tw * 0.48, ty2 - H * 0.07, tw * 0.96, H * 0.012, '#8a6a48'); fr(q, tx - 1.2, ty2 - H * 0.07, 2.4, H * 0.07, '#5a3a22');
    [-0.65, 0.65].forEach(function (k) { fr(q, tx + k * tw - H * 0.02, ty2 - H * 0.05, H * 0.04, H * 0.05, '#a05a32'); fr(q, tx + k * tw - H * 0.02, ty2 - H * 0.075, H * 0.04, H * 0.015, '#8a4a28'); });
    ln(q, tx, ty2 - H * 0.07, tx, ty2 - H * 0.19, '#5a3a22', 1.6); pg(q, [tx - tw * 0.8, ty2 - H * 0.14, tx + tw * 0.8, ty2 - H * 0.14, tx, ty2 - H * 0.22], i % 2 ? '#2f8f5b' : '#c62a20'); pg(q, [tx - tw * 0.3, ty2 - H * 0.14, tx - tw * 0.1, ty2 - H * 0.14, tx - tw * 0.02, ty2 - H * 0.22, tx - tw * 0.1, ty2 - H * 0.2], 'rgba(255,255,255,.55)');
  }
  bush(q, px0 + pw * 0.04, by + H * 0.012, H * 0.07, GREEN[0], Q.seed + 2); bush(q, px0 + pw * 0.97, by + H * 0.012, H * 0.07, GREEN[1], Q.seed + 3);
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
/* a market: striped stalls, crates, a string of bulbs */
function market(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, rg = rnd(Q.seed + 11), ty = by - H * 0.42;
  K.paper(q, K.rect(x0, ty, x1 - x0, by - ty), Q.col === 'white' ? '#5a6a58' : '#d8c9a4', 1);
  q.fillStyle = vgrad(q, ty, by, 'rgba(255,255,255,.12)', 'rgba(0,0,0,.14)'); q.fillRect(x0, ty, x1 - x0, by - ty);
  var ns = Q.ph ? 2 : 3, sw = vw / ns, i, cols = [['#c62a20', '#f4f1ea'], ['#2f8f5b', '#f4f1ea'], ['#e8692a', '#f4f1ea']];
  for (i = 0; i < ns; i++) {
    var sx = vx0 + sw * i + sw * 0.06, w = sw * 0.88, ay = ty + H * 0.1, cy = by - H * 0.1;
    fr(q, sx + 2, ay, 2, cy - ay + H * 0.1, '#6a4126'); fr(q, sx + w - 4, ay, 2, cy - ay + H * 0.1, '#6a4126');
    fr(q, sx, cy, w, H * 0.1, '#7a5a3a'); fr(q, sx, cy, w, 2, '#9a7a52');
    var pc = ['#e8692a', '#c62a20', '#9ad06a', '#f2c94c', '#8a3a6a'];
    for (var k = 0; k < Math.floor(w / 6); k++) dot(q, sx + 5 + k * 6, cy - 2.4 - ((k % 2) * 2.4), 3.2, pc[(k + i) % 5]);
    awning(q, sx, sx + w, ay, H * 0.12, cols[i % 3][0], cols[i % 3][1], max(4, Math.round(w / 18)));
    for (var lx = sx + w * 0.2; lx < sx + w * 0.9; lx += w * 0.3) { ln(q, lx, ay + H * 0.1, lx, ay + H * 0.14, '#333', 1); ov(q, lx, ay + H * 0.17, 3, 4, '#e0262d'); nightLamp(L, st, lx, ay + H * 0.17, 12, '#ff9a5a', 0.7, 0.1); }
  }
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
/* a car park: bays on the ground and cars in them, a low wall behind */
function carpark(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, rg = rnd(Q.seed + 13), ty = by - H * 0.2;
  K.paper(q, K.rect(x0, ty, x1 - x0, by - ty), Q.col === 'white' ? '#5a5048' : '#d8cfb8', 0.8); fr(q, x0, ty - 2, x1 - x0, 3, '#8a8478');
  var cw = H * 0.34, n = max(1, Math.floor(vw / (cw * 1.18))), cols = ['#c62a20', '#f4f1ea', '#2c5aa0', '#2a2d34', '#e8b22a', '#7a8088'];
  for (var i = 0; i < n; i++) { var cx = vx0 + (vw - n * cw * 1.18) / 2 + i * cw * 1.18; car(q, cx, by + H * 0.025, cw, pick(rg, cols)); }
  q.fillStyle = 'rgba(245,240,220,.6)'; for (var j = 0; j <= n; j++) { var lx = vx0 + (vw - n * cw * 1.18) / 2 + j * cw * 1.18 - cw * 0.09; q.beginPath(); q.moveTo(lx, by + H * 0.012); q.lineTo(lx + 2, by + H * 0.012); q.lineTo(lx - 5, by + H * 0.095); q.lineTo(lx - 7, by + H * 0.095); q.fill(); }
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
/* a fuel station: a canopy on two columns, two pumps, a kiosk */
function station(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, ty = by - H * 0.5, bh = H * 0.5;
  var cx0 = vx0 + vw * 0.02, cx1 = vx1 - vw * 0.02;
  K.paper(q, K.rect(vx0 + vw * 0.55, ty + bh * 0.32, vw * 0.45, by - ty - bh * 0.32), '#e9eef2', 1); fr(q, vx0 + vw * 0.58, ty + bh * 0.5, vw * 0.38, bh * 0.4, '#9fc7d8');
  [0.12, 0.88].forEach(function (k) { fr(q, vx0 + vw * k - 4, ty + bh * 0.16, 8, by - ty - bh * 0.16, '#d6d6dc'); });
  K.paper(q, K.rect(cx0, ty, cx1 - cx0, bh * 0.16), '#2c5aa0', 1.4); fr(q, cx0, ty + bh * 0.1, cx1 - cx0, bh * 0.04, '#f2c94c'); fr(q, cx0, ty + bh * 0.16, cx1 - cx0, 2.4, '#e9eef2');
  [0.3, 0.46].forEach(function (k, i) { var px = vx0 + vw * k, ph = bh * 0.34; rr(q, px - 6, by - ph, 12, ph, 2, i ? '#2c5aa0' : '#c62a20'); fr(q, px - 4, by - ph + 4, 8, 7, '#bfe3f2'); fr(q, px - 6, by - 4, 12, 4, '#4a4a52'); q.strokeStyle = '#222'; q.lineWidth = 1.4; q.beginPath(); q.moveTo(px + 6, by - ph * 0.6); q.quadraticCurveTo(px + 12, by - ph * 0.3, px + 8, by - 5); q.stroke(); });
  nightLamp(L, st, (cx0 + cx1) / 2, ty + bh * 0.3, (cx1 - cx0) * 0.5, '#fff3c4', 0.4, 0);
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
/* a temple compound: a white wall with a gold cap, a gateway with a stacked roof, a tree behind */
function temple(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, wy = by - H * 0.2;
  treeAt(q, vx0 + vw * 0.8, by - H * 0.12, H * 0.62, GREEN[0], Q.seed + 4);
  K.paper(q, K.rect(x0, wy, x1 - x0, by - wy), '#f4efe2', 1); fr(q, x0, wy - 3, x1 - x0, 5, '#e0ac2a'); fr(q, x0, wy + 2, x1 - x0, 2, '#c9a050');
  var gx = vx0 + vw * 0.42, gw = H * 0.34, gh = H * 0.46;
  K.paper(q, K.rect(gx - gw / 2, by - gh, gw, gh), '#f4efe2', 1.2); fr(q, gx - gw * 0.3, by - gh * 0.72, gw * 0.6, gh * 0.72, '#5a2a1a'); fr(q, gx - gw * 0.3, by - gh * 0.72, gw * 0.6, 3, '#e0ac2a');
  var ry = by - gh;
  for (var k = 0; k < 2; k++) { var rw = gw * (1.5 - k * 0.45), rh = H * 0.09; pg(q, [gx - rw / 2, ry, gx + rw / 2, ry, gx + rw * 0.36, ry - rh, gx - rw * 0.36, ry - rh], k ? '#8a3a28' : '#6a2a1a', '#e0ac2a', 1.2); ry -= rh * 0.8; }
  ln(q, gx, ry, gx, ry - H * 0.07, '#e0ac2a', 1.6);
  Q.bldTop = by - gh; return { x0: vx0, x1: vx1 };
}
/* a house with its gate pillar and number plate */
function home(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, ty = by - H * 0.4, wy = ty + H * 0.1;
  wallOf(q, vx0 + vw * 0.04, x1, wy, by, Q.col === 'white' ? '#8a6a5a' : '#f1dcc8');
  pg(q, [vx0 - 2, wy, x1 + 2, wy, x1 - H * 0.1, ty, vx0 + H * 0.12, ty], '#a9532b', '#7c3816', 1.2); for (var rx = vx0 + 6; rx < x1; rx += 9) ln(q, rx, wy - 1, rx + 3, ty + 2, 'rgba(60,20,8,.25)', 1);
  var dw = vw * 0.18; fr(q, vx0 + vw * 0.22, wy + H * 0.06, dw, by - wy - H * 0.06 - 3, '#6a3a1e'); fr(q, vx0 + vw * 0.22 + dw * 0.1, wy + H * 0.09, dw * 0.8, H * 0.1, '#bfe3f2');
  [0.55, 0.78].forEach(function (k) { fr(q, vx0 + vw * k, wy + H * 0.08, vw * 0.13, H * 0.14, '#4b6a8a'); fr(q, vx0 + vw * k - 2, wy + H * 0.22, vw * 0.13 + 4, 3, '#bdb5a0'); });
  nightLamp(L, st, vx0 + vw * 0.28, wy + H * 0.16, H * 0.18, '#ffe6a8', 0.4, 0);
  if (sp.houseNo) { var px = vx0 + vw * 0.22 + dw * 1.25, pw = H * 0.075; rr(q, px, wy + H * 0.075, pw, pw * 0.62, 2, '#1f4a80'); q.fillStyle = '#ffffff'; q.font = '700 ' + Math.round(pw * 0.42) + 'px "Sarabun",system-ui,sans-serif'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText(sp.houseNo, px + pw / 2, wy + H * 0.075 + pw * 0.33); }
  bush(q, vx0 + vw * 0.5, by + H * 0.01, H * 0.06, GREEN[1], Q.seed + 7);
  Q.bldTop = ty; return { x0: vx0, x1: vx1 };
}
var BUILD = { hotel: hotel, restaurant: restaurant, market: market, carpark: carpark, station: station, temple: temple, home: home };

/* ---------------------------------------------------------------- the rest of the setting */
/* a gate: two pillars with lamps, bars between them (front: bars across the house) */
function gate(q, Q, x0, x1, h, L, st, bars) {
  var pw = h * 0.16, by = Q.deck + Q.H * 0.012, i;
  if (bars) { q.strokeStyle = '#3a3a42'; q.lineWidth = max(1.2, h * 0.02); for (var bx = x0 + pw; bx < x1 - pw; bx += h * 0.1) { q.beginPath(); q.moveTo(bx, by); q.lineTo(bx, by - h * 0.82); q.stroke(); } fr(q, x0 + pw, by - h * 0.82, x1 - x0 - pw * 2, h * 0.03, '#3a3a42'); fr(q, x0 + pw, by - h * 0.3, x1 - x0 - pw * 2, h * 0.025, '#3a3a42'); fr(q, x0 + pw, by - h * 0.04, x1 - x0 - pw * 2, h * 0.03, '#3a3a42'); for (var sx = x0 + pw; sx < x1 - pw; sx += h * 0.1) pg(q, [sx - 2, by - h * 0.82, sx + 2, by - h * 0.82, sx, by - h * 0.9], '#3a3a42'); }
  [x0, x1 - pw].forEach(function (px) { K.paper(q, K.rect(px, by - h, pw, h), '#e6dec9', 1); fr(q, px - pw * 0.1, by - h - pw * 0.18, pw * 1.2, pw * 0.22, '#c9bfa5'); dot(q, px + pw / 2, by - h - pw * 0.42, pw * 0.34, '#fff0c8'); nightLamp(L, st, px + pw / 2, by - h - pw * 0.42, pw * 2.4, '#ffd98a', 0.7, 0.1); });
}
/* utility poles and their wires across the top of the frame */
function poles(q, Q, xs, L) {
  var H = Q.H, W = Q.W, by = Q.deck + H * 0.02, top = H * 0.08;
  q.strokeStyle = 'rgba(30,26,30,.7)'; q.lineWidth = 1;
  for (var w = 0; w < 4; w++) { q.beginPath(); q.moveTo(-4, top + w * 5 + 6); for (var i = 0; i < xs.length; i++) { var x1 = xs[i]; q.quadraticCurveTo((i ? xs[i - 1] + x1 : x1 - 40) / 2, top + w * 5 + 14 + i * 2, x1, top + w * 5 + 2 + (w % 2) * 4); } q.quadraticCurveTo((xs[xs.length - 1] + W) / 2, top + w * 5 + 14, W + 4, top + w * 5 + 8); q.stroke(); }
  xs.forEach(function (x) { fr(q, x - 3, top, 6, by - top, '#6a6258'); fr(q, x - 3, top, 1.6, by - top, 'rgba(255,255,255,.2)'); fr(q, x - 14, top + 3, 28, 3, '#4a443c'); fr(q, x - 12, top + 14, 24, 3, '#4a443c'); });
}
/* the plants: far side trees, the banyan, flowering shrubs */
function greenery(q, Q, sp) {
  var W = Q.W, H = Q.H, by = Q.by, g = sp.green, rg = rnd(Q.seed + 17), x, ox0 = max(Q.ox0, 0), ox1 = min(Q.ox1, W);
  if (g === 'banyan') { banyanAt(q, Q.hx + Q.dir * -Q.s * 4.5, by + H * 0.01, H * 0.1, Q.seed); return; }
  if (g === 'trees') { for (x = ox0 + H * 0.06; x < ox1; x += H * (0.22 + rg() * 0.1)) treeAt(q, x, by + H * 0.01, H * (0.5 + rg() * 0.2), GREEN[(x / 10 | 0) % 3], Math.floor(rg() * 1e6)); return; }
  if (g === 'flowers') { for (x = ox0 + H * 0.05; x < ox1; x += H * (0.1 + rg() * 0.05)) bush(q, x, by + H * 0.02, H * (0.06 + rg() * 0.03), GREEN[(x / 10 | 0) % 3], Math.floor(rg() * 1e6)); for (var i = 0; i < 60; i++) dot(q, ox0 + rg() * (ox1 - ox0), by - H * (0.01 + rg() * 0.09), max(1, H * 0.009), ['#b05ac8', '#d070e0', '#e08af0'][i % 3]); return; }
  if (g === 'hedge' || g === 'hedgefront') { hedge(q, -6, W + 6, by + H * 0.01, H * 0.09, GREEN[0].slice(0, 2), Q.seed + 2); }
  if (g === 'yard') { for (x = ox0 + H * 0.05; x < ox1; x += H * (0.13 + rg() * 0.06)) bush(q, x, by + H * 0.02, H * (0.05 + rg() * 0.03), GREEN[(x / 10 | 0) % 3], Math.floor(rg() * 1e6)); }
}
/* the layer in front of the house: the near hedge, the gate bars, the fence, the poles, the island's near edge */
function drawFront(q, S, Q, sp, st, L) {
  var H = Q.H, W = Q.W, s = Q.s, deck = Q.deck, by2 = deck + H * 0.012;
  if (sp.green === 'hedgefront') { var hr = H * 0.075, hrg = rnd(Q.seed + 8); for (var hxx = Q.hx - Q.hw - s * 1.2; hxx < Q.hx + Q.hw + s * 1.2; hxx += hr * 1.15) bush(q, hxx, by2 + H * 0.03, hr * (0.9 + hrg() * 0.25), GREEN[(hxx / 7 | 0) % 3], Math.floor(hrg() * 1e6)); for (var fi = 0; fi < 26; fi++) dot(q, Q.hx - Q.hw - s + hrg() * (Q.hw * 2 + s * 2), by2 - H * (0.0 + hrg() * 0.07), max(1, H * 0.008), ['#ffd166', '#ff7aa2', '#ffffff'][fi % 3]); }
  if (sp.gate === 'front') gate(q, Q, Q.hx - Q.hw - s * 0.6, Q.hx + Q.hw + s * 0.6, s * 4.3, L, st, true);
  if (sp.fence) { var fx0 = Q.hx - Q.hw - s * 0.4, fx1 = Q.hx + Q.hw + s * 0.4, fh = s * 1.7; fr(q, fx0, by2 - fh * 0.1, fx1 - fx0, fh * 0.1, '#e6dec9'); for (var bx = fx0; bx < fx1; bx += s * 0.34) { fr(q, bx, by2 - fh, max(1.2, s * 0.08), fh * 0.9, '#f4efe2'); pg(q, [bx - 1, by2 - fh, bx + s * 0.08 + 1, by2 - fh, bx + s * 0.04, by2 - fh - s * 0.16], '#e0ac2a'); } fr(q, fx0, by2 - fh * 0.82, fx1 - fx0, max(1.2, s * 0.07), '#f4efe2'); fr(q, fx0, by2 - fh * 0.2, fx1 - fx0, max(1.2, s * 0.07), '#f4efe2'); }
  if (sp.poles) poles(q, Q, [Q.hx - Q.hw - s * 1.4, Q.hx + Q.hw + s * 2.6], L);
}

/* a plastered wall behind the house, and the shelf the house stands on with its two brackets */
function shelfWall(q, Q, sp) {
  var s = Q.s, deck = Q.deck, hx = Q.hx, d = Q.dir, W = Q.W, H = Q.H, wa = hx - d * s * 2.8, wb = hx + d * s * 7.2, x0 = min(wa, wb), x1 = max(wa, wb), ty = deck - s * 6.6, by = Q.by + H * 0.012, col = Q.col === 'white' ? '#7a6a5a' : '#e4d6b8';
  wallOf(q, x0, x1, ty, by, col);
  var a = hx - d * s * 2.3, b = hx + d * s * 4.0, sa = min(a, b), sb = max(a, b), sy = deck - s * 3.0;
  fr(q, sa, sy, sb - sa, s * 0.34, '#8a6a48'); fr(q, sa, sy, sb - sa, s * 0.08, '#b08a5a'); fr(q, sa, sy + s * 0.3, sb - sa, s * 0.05, 'rgba(0,0,0,.25)');
  [sa + s * 0.4, sb - s * 0.4].forEach(function (bx) { var dir2 = bx < hx ? -1 : 1; pg(q, [bx - s * 0.1, sy + s * 0.34, bx + s * 0.1, sy + s * 0.34, bx + s * 0.1, sy + s * 1.5, bx - s * 0.1, sy + s * 1.5], '#6a4a30'); pg(q, [bx, sy + s * 0.34, bx + dir2 * -s * 0.0, sy + s * 1.5, bx + dir2 * s * 0.9, sy + s * 0.34], '#6a4a30'); });
}
/* a machinery yard: a sheet-metal fence, an excavator behind it */
function machinery(q, Q, sp, st, L) {
  var W = Q.W, H = Q.H, by = Q.by, x0 = Q.bx0, x1 = Q.bx1, vx0 = max(x0, 0), vx1 = min(x1, W), vw = vx1 - vx0, fy = by - H * 0.17;
  excavator(q, vx0 + vw * 0.3, fy + H * 0.045, min(vw * 0.5, H * 0.56));
  K.paper(q, K.rect(x0, fy, x1 - x0, by - fy), '#8fa0b0', 1); q.strokeStyle = 'rgba(40,55,70,.4)'; q.lineWidth = 1; for (var x = x0; x < x1; x += 5) { q.beginPath(); q.moveTo(x, fy); q.lineTo(x, by); q.stroke(); }
  fr(q, x0, fy - 3, x1 - x0, 4, '#5a6a78'); for (var px = x0 + 8; px < x1; px += 60) fr(q, px, fy - 3, 4, by - fy + 3, '#5a6a78');
  Q.bldTop = by - H * 0.4; return { x0: vx0, x1: vx1 };
}
BUILD.machinery = machinery;

/* ---------------------------------------------------------------- the house with its tray, the part that stands in front of the setting */
function houseLayer(q, S, Q, sp, st, lives) {
  var s = Q.s, deck = Q.deck, p = PAL[Q.col], out = { x0: Q.hx - Q.hw, x1: Q.hx + Q.hw, y0: deck - Q.nh * s, y1: deck }, houses = [], n = sp.n, i, tips = [], to;
  var xs = n === 2 ? [Q.hx - Q.gapw * s / 2, Q.hx + Q.gapw * s / 2] : [Q.hx], scs = n === 2 ? (Q.dir < 0 ? [0.84, 1] : [1, 0.84]) : [1];
  var items = {}; for (var k in st.items) items[k] = st.items[k]; if (sp.bowl) items.bowl = 1; if (sp.table) items.coconut = 1;
  lift(q, Q.sunSign * -2.2, function (g) {
    for (i = 0; i < n; i++) {
      var o = { s: s * scs[i], x: xs[i], y: deck, p: p, pillar: Q.pillar, cloth: i === 0 ? Q.cloth : false, retinue: true, ped: sp.ped, naga: sp.naga, glass: sp.glass };
      if (sp.shelf) o.y = deck - s * 3.0;
      houses.push(MODEL[sp.model](g, o, lives));
    }
    to = { s: s * (sp.model === 'deva' ? 0.85 : sp.model === 'brahma' ? 0.75 : 0.62), x: Q.hx + s * 0.1, y: deck + s * 0.2, items: items, sticks: sp.small ? 3 : 5, burn: st.lit ? st.burn : st.stage === 'morning' ? 0.12 : 0, lit: st.lit, flame: st.candles };
    if (n === 2) { to.s = s * 0.8; to.x = Q.hx; }
    if (sp.model === 'chinese') tips = houses[0].tips.slice();
    else if (sp.shelf) { to.ty = deck - s * 2.9; to.x = xs[0] + Q.dir * s * 2.4; to.s = s * 0.6; tips = tray(g, to, lives); }
    else tips = table(g, to, lives);
    if (st.lit && sp.model !== 'chinese' && !sp.shelf && K.town && K.person) {   /* a woman kneeling in wai while the incense burns */
      var pd = K.town({ r: rnd(Q.seed + 77), set: 'calm', t: 0 }, 1, { sin: 0.5, casual: 0.35, mohom: 0.15 })[0]; pd.dir = 1;
      K.person(g, max(to.s * 1.5, to.x - to.s * 1.85 - to.s * 1.3), deck + to.s * 0.4, to.s * 3.1, K.POSE.wai, pd);
    }
    var bd = Q.dir;   /* the building's side */
    if (sp.eleph === 'statue') statue(g, Q.hx + bd * (Q.hw + s * 1.3), deck + s * 0.1, s * 2.6, '#f2efe6', -bd);
    else if (sp.eleph === 'small') elephant(g, Q.hx + bd * (Q.hw + s * 0.2), deck + s * 0.1, s * 1.15, '#f2efe6');
    if (sp.extra === 'chinese') chinese(g, { s: s * 0.5, x: Q.hx - bd * (Q.hw + s * 1.4), y: deck + s * 0.1 }, lives);
  });
  Q.top = min.apply(null, houses.map(function (m) { return m.top; }));
  if (st.lit && tips.length) lives.push(function (c, t) {
    for (var j = 0; j < tips.length; j += 2) smokeAt(c, t, tips[j][0], tips[j][1], to.s * 0.62, j, Q.dir * 0.25, st.band);
    c.save(); c.globalCompositeOperation = 'lighter'; for (var j2 = 0; j2 < tips.length; j2++) lamp(c, tips[j2][0], tips[j2][1], to.s * 0.2, '#ff7a2a', 0.8 + 0.2 * sin(t * 7 + j2)); c.restore();
  });
  var gl = [];
  houses.forEach(function (m, hi) { m.glints.forEach(function (g2, j) { gl.push([g2[0], g2[1]]); }); });
  lives.push(function (c, t) {
    if (st.band > 1 && !st.lamp) return;
    c.save(); c.globalCompositeOperation = 'lighter';
    for (var j = 0; j < gl.length; j++) { var a = Math.pow(max(0, sin(t * (1.5 + 0.3 * (j % 3)) + j * 2.1)), 8) * (st.band === 3 ? 0.55 : 0.9); if (a < 0.05) continue; c.fillStyle = 'rgba(255,246,206,' + a.toFixed(3) + ')'; twinkle(c, gl[j][0], gl[j][1], max(2, s * 0.32) * (0.6 + a * 0.5)); }
    c.restore();
  });
  /* marigold petals let go of the garland and drift down; fireflies over the ground after dark */
  var m0 = houses[0], pz = max(1.2, s * 0.09);
  lives.push(function (c, t) {
    var dim = st.band === 3 ? 0.5 : 1;
    for (var j = 0; j < 4; j++) {
      var u = (t * 0.07 + j * 0.25) % 1, px = m0.door[0] + (j - 1.5) * s * 0.7 + sin(u * 8 + j * 1.7) * s * 0.35, py = m0.ht + s * 0.1 + u * s * 4.6, a = (u < 0.1 ? u / 0.1 : 1 - (u - 0.1) / 0.9) * 0.9 * dim;
      c.fillStyle = (j % 2 ? 'rgba(255,159,28,' : 'rgba(255,253,244,') + a.toFixed(3) + ')'; c.beginPath(); c.ellipse(px, py, pz, pz * 0.55, sin(u * 9 + j) * 1.2, 0, TAU); c.fill();
    }
  });
  if (st.band >= 2) lives.push(function (c, t) {
    var rf = rnd(Q.seed + 5), n = Q.ph ? 5 : 9;
    c.save(); c.globalCompositeOperation = 'lighter';
    for (var j = 0; j < n; j++) {
      var fx = Q.hx + (rf() - 0.5) * Q.W * 0.7 + 0.03 * Q.W * sin(t * (0.5 + rf()) + j), fy = Q.deck - Q.H * (0.02 + 0.2 * rf()) - Q.H * 0.03 * (0.5 + 0.5 * sin(t * 0.7 + j * 2)), fa = 0.4 + 0.6 * Math.pow(max(0, sin(t * (1.2 + rf()) + j * 3)), 2);
      lamp(c, fx, fy, 5, '#d2ff8c', fa * 0.9); lamp(c, fx, fy, 1.6, '#f4ffd0', fa);
    }
    c.restore();
  });
  if (st.lamp) lives.push(function (c, t) {
    var fl = 0.86 + 0.14 * sin(t * 5.3) * sin(t * 1.7);
    c.save(); c.globalCompositeOperation = 'lighter';
    houses.forEach(function (m) { lamp(c, m.door[0], m.door[1], s * 2.3, '#ffb347', 0.55 * fl * (st.band === 1 ? 0.6 : 1)); lamp(c, m.door[0], m.door[1] - s * 0.2, s * 0.9, '#ffe9a8', 0.5 * fl); });
    c.save(); c.translate(Q.hx, deck + Q.H * 0.02); c.scale(1, 0.22); lamp(c, 0, 0, Q.hw * 1.6, '#ffb347', 0.34 * fl * (st.band === 1 ? 0.5 : 1)); c.restore();
    c.restore();
  });
  return out;
}

/* ---------------------------------------------------------------- the scene */
function draw(S) {
  S.noMagic = true;
  if (!(S.W > 30 && S.H > 30)) return;   /* a canvas not yet laid out */
  var P = S.place || {}, c = S.c, sp = specOf(P), Q = plan(S, sp), st = stateOf(S), t = S.t / 1000, r = Q.r;
  Q.col = sp.col || pick(r, ['gold', 'gold', 'gold', 'white', 'gold', 'red']); if (sp.model === 'puya' && !PAL[Q.col]) Q.col = 'wood';
  Q.cloth = sp.cloth != null ? sp.cloth : r() < 0.4;
  Q.sunSign = st.h < 12 ? -1 : 1;
  var kb = [P.id || '', st.band, st.lamp ? 1 : 0, st.alt > 2 ? Math.round(st.h * 2) : -1].join('|'), key = [kb, st.stage, st.burn, st.candles ? 1 : 0].join('|');
  var back = layer(S, 'b' + kb, [0, 0, Q.W, Q.H], function (q) { var L = []; drawBack(q, S, Q, sp, st, L); tint(q, st.band, 1); return L; });
  (back.out || []).forEach(function (f) { f(c, t); });
  var my = Q.deck - Q.nh * Q.s - Q.s * 2, bx = Q.hx - Q.hw - Q.s * 4, bw = Q.hw * 2 + Q.s * 8;
  var mid = layer(S, 'm' + key, [bx, my, bw, Q.H - my], function (q) { var L = []; var o = houseLayer(q, S, Q, sp, st, L); tint(q, st.band, 0.5); return { L: L, o: o }; });
  if (mid.out) { mid.out.L.forEach(function (f) { f(c, t); }); var o = mid.out.o; S.hits.push({ k: 'place', x0: o.x0, x1: o.x1, y0: o.y0, y1: o.y1 }); }
  if (sp.green === 'hedgefront' || sp.gate === 'front' || sp.fence || sp.poles) {
    var fr2 = layer(S, 'f' + key, sp.poles ? [0, 0, Q.W, Q.H] : [bx, my, bw, Q.H - my], function (q) { var L = []; drawFront(q, S, Q, sp, st, L); tint(q, st.band); return L; });
    (fr2.out || []).forEach(function (f) { f(c, t); });
  }
  if ((sp.island || sp.road) && K.traffic) K.traffic(S, { y: Q.H - 2, u: Q.H * 0.1, density: 0.22, k: 0.84, only: 'near' });   /* the scooters of the road in front */
}
/* the layer behind the house: the ground and the setting */
function drawBack(q, S, Q, sp, st, L) {
  var W = Q.W, H = Q.H, deck = Q.deck, kind = sp.build;
  ground(q, Q, sp, st);
  if (sp.green === 'banyan' || sp.green === 'trees' || sp.green === 'flowers') greenery(q, Q, sp);
  var bld = null;
  if (kind && BK[kind]) bld = shop(q, Q, sp, st, L, kind); else if (kind && BUILD[kind]) bld = BUILD[kind](q, Q, sp, st, L);
  if (bld) veil(q, bld.x0, Q.bldTop, bld.x1, Q.by);
  if (sp.green === 'hedge' || sp.green === 'yard') greenery(q, Q, sp);
  if (sp.gate === 'side') { var gw = H * 0.5, gx0 = Q.dir > 0 ? Q.ox0 + (Q.ox1 - Q.ox0) * 0.1 : Q.ox1 - (Q.ox1 - Q.ox0) * 0.1 - gw; gx0 = clamp(gx0, 6, W - gw - 6); gate(q, Q, gx0, gx0 + gw, H * 0.4, L, st, true); }
  if (sp.shelf) shelfWall(q, Q, sp);
  if (st.alt > 2 && !sp.shelf) { var len = clamp(1 / Math.tan(st.alt * PI / 180), 0.5, 3.5) * Q.s * 1.2, sx = Q.hx + Q.sunSign * len * 0.5; ov(q, sx, deck + H * 0.014, len * 0.5 + Q.s * 1.0, Q.s * 0.3, 'rgba(60,40,50,.2)'); }
  if (st.band <= 1) glowAt(q, Q.hx, deck - Q.s * 5, Q.s * 7, '#fff6d8', st.band === 0 ? 0.2 : 0.28);
}
D.addScene('spirithouse', draw, null, 'y = a·cosh(x/a) (the garland)<br>wₙ₊₁ = 0.78·wₙ (the roof tiers)');
})();
