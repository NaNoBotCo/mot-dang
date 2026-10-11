/* Arts and crafts of the north, and Saint Expedite's red house, for the auto-doodler
   (Nan, 2026-10-02: "do some for arts and crafts", "one for st expedite"; "be genuinely
   useful, and beautiful because you don't need an explanation to know what it does").
   'handicraft'  eight workshops, one look each, the thing being made large in the middle:
     lacquer   khrueang khoen: a lidded box turns, x = R·sin(θ + ωt); the brush lays red where
               it passes, then gold leaf, motif by motif
     wood      Ban Tawai: mallet on chisel, chips on y = v₀t − ½gt², an elephant out of the block
     silver    Wua Lai: a bowl chased on its stake, the repoussé rising as it turns; the silver
               ubosot behind, glinting
     saa       saa paper: the frame lifted out of the vat, drips falling; sheets with petals in the sun
     celadon   the wheel, r(y) = r₀ + a·sin(ky + φ); a pot out of the kiln, hot to jade,
               c = 1 − e^(−t/τ), its crackle coming in as it cools
     loom      the shuttle across the shed, the beater, the tin jok pattern growing row on row
     candle    a Khao Phansa candle carved band by band, wax curls falling on spirals
     indigo    cloth lifted from the vat goes green to blue as it meets the air, each part by its
               own time out, c = 1 − e^(−t/τ); a batik line drawn in wax beside it
   'expedite'    the red spirit house: HODIE on his cross, the crow under his foot, a live crow
                 on the roof saying cras; thanks stuck on, the light comes, the crow goes.
     soi       a Chiang Mai soi: a devotee sticks a note of thanks on the plinth
     novena    the red house on a mountain bend: nine candles lit one a day, a rider's wai
   Still parts are cut once into an offscreen layer; what moves is drawn off S.t. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU, person = K.person, POSE = K.POSE;
var FONT = '"Sarabun",system-ui,sans-serif', SERIF = '"Cinzel","Trajan Pro",Georgia,"Times New Roman",serif';
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function seg(p, a, b) { return clamp((p - a) / (b - a), 0, 1); }
function hx(s) { return [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)]; }
function mixc(a, b, u) { var A = hx(a), B = hx(b); return 'rgb(' + Math.round(lerp(A[0], B[0], u)) + ',' + Math.round(lerp(A[1], B[1], u)) + ',' + Math.round(lerp(A[2], B[2], u)) + ')'; }

/* ---------------------------------------------------------------- cut once, drawn every frame */
var LAYERS = {};
function mat(c) { return c.getTransform ? c.getTransform() : null; }
function layer(S, name, y0, y1, draw) {
  var c = S.c, m = mat(c);
  if (!m || typeof document === 'undefined') { draw(c); return; }
  var bx = Math.floor(m.a * S.x0 + m.e), by = Math.floor(m.d * y0 + m.f), bw = Math.ceil(m.a * S.span) + 2, bh = Math.ceil(m.d * (y1 - y0)) + 2;
  var key = [S.W, S.H, S.x0, S.x1, S.deck, S.hh, +S.night, S.seed, m.a, m.d, m.e, m.f, y0, y1, S.variant].join(','), L = LAYERS[name];
  if (!L || L.key !== key) {
    var o = document.createElement('canvas'); o.width = Math.max(1, bw); o.height = Math.max(1, bh);
    var q = o.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - bx, m.f - by); draw(q);
    L = LAYERS[name] = { key: key, cv: o, x: bx, y: by };
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(L.cv, L.x, L.y); c.restore();
}
var SPR = {}, nspr = 0;
function sprite(S, name, w, h, draw) {
  var m = mat(S.c), k = m ? Math.abs(m.a) : 1, key = name + '|' + Math.round(w) + '|' + Math.round(h) + '|' + k + '|' + S.seed + '|' + +S.night;
  if (SPR[key]) return SPR[key];
  if (typeof document === 'undefined') return null;
  if (++nspr > 60) { SPR = {}; nspr = 1; }
  var o = document.createElement('canvas'); o.width = Math.max(1, Math.ceil(w * k)); o.height = Math.max(1, Math.ceil(h * k));
  var q = o.getContext('2d'); q.setTransform(k, 0, 0, k, 0, 0); draw(q);
  return (SPR[key] = o);
}
/* a soft round glow of a hue, from a small disc cut once */
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',95%,62%,1)'); g.addColorStop(0.5, 'hsla(' + h + ',95%,60%,.4)'); g.addColorStop(1, 'hsla(' + h + ',95%,60%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o || a <= 0) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
/* a shape filled with the paper's drop shadow, nonzero (paper() fills even-odd) */
function solid(c, path, col, lift) {
  c.save(); c.shadowColor = 'rgba(0,0,0,.38)'; c.shadowBlur = 2 + (lift || 1) * 2; c.shadowOffsetX = 0.8 + (lift || 1) * 0.6; c.shadowOffsetY = 1.2 + (lift || 1);
  c.fillStyle = col; path(c); c.fill(); c.restore();
}
function line(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
function star(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.moveTo(x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.fill(); }
/* the event's banner, slid along so it stays on the stage */
function label(S, cx, y, col) {
  if (!S.label) return;
  var c = S.c; c.font = '800 ' + Math.round(Math.max(12, S.hh * 0.2)) + 'px ' + FONT;
  var bh = Math.max(20, S.hh * 0.32), half = c.measureText(S.label).width / 2 + 10 + bh * 0.6 + 4;
  var lo = S.x0 + S.hh * 0.75 + half, hi = S.x1 - S.hh * 0.95 - half;
  cx = lo > hi ? S.x0 + S.span / 2 : Math.max(lo, Math.min(hi, cx));
  K.banner(c, cx, y, S.label, S.hh, col, S.seed, S.hits);
}
/* the skeleton's joints and an arm that reaches a point (law of cosines), as doodler-craft.js works them */
function joints(x, y, h, P, dir) {
  var seat = P.seat || 0.47, lean = P.lean || 0;
  var hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33];
  return { hip: hip, sh: sh };
}
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
function fig(S, d, x, y, h, P, dir, hA, hB) { d.dir = dir; return person(S.c, x, y, h, hA || hB ? reach(x, y, h, P, dir, hA, hB) : P, d); }
var SIT = { lean: 0.22, seat: 0.12, legs: POSE.lotus.legs, arms: [0.5, 0.9, 0.4, 1.0] };
var STOOL = { lean: 0.18, seat: 0.3, legs: [1.45, -1.35, 1.35, -1.25], arms: [0.5, 0.9, 0.4, 1.0] };
var STAND = { lean: 0.12, legs: [0.1, 0, -0.08, 0], arms: [0.3, 0.4, 0.2, 0.5] };

/* ---------------------------------------------------------------- the workshop's still parts */
/* a teak floor, planks laid along the stage */
function floor(q, S, col, plank) {
  K.ground(q, S.x0, S.x1, S.deck, S.H, col);
  if (!plank) return;
  q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1;
  for (var y = S.deck + 7, i = 0; y < S.H; y += 9 + i * 2, i++) { q.beginPath(); q.moveTo(S.x0, y); q.lineTo(S.x1, y); q.stroke(); }
}
/* a woven bamboo wall (fa khat-tae), twill: strips that cross two, pass two */
function wall(q, x0, x1, y0, y1, N) {
  paper(q, rect(x0, y0, x1 - x0, y1 - y0), N ? '#4e3c28' : '#c9a66b', 1);
  var s = Math.max(4, (y1 - y0) / 9), i, j;
  q.save(); q.beginPath(); q.rect(x0, y0, x1 - x0, y1 - y0); q.clip();
  for (i = 0; (y0 + i * s) < y1; i++) for (j = 0; (x0 + j * s) < x1; j++) {
    var hz = ((i + j) >> 1) % 2 === (i % 2), x = x0 + j * s, y = y0 + i * s;
    q.fillStyle = hz ? (N ? 'rgba(255,220,160,.07)' : 'rgba(255,240,200,.28)') : (N ? 'rgba(0,0,0,.2)' : 'rgba(90,60,20,.18)');
    q.fillRect(x + 0.5, y + 0.5, s - 1, s - 1);
  }
  q.restore();
  q.fillStyle = N ? '#2e2216' : '#7a5530'; q.fillRect(x0, y0 - 2, x1 - x0, 3);
}
function shelf(q, x0, x1, y, N) {
  var wd = N ? '#4a2e1c' : '#6a4426';
  paper(q, rect(x0, y, x1 - x0, 4), wd, 1);
  [x0 + 6, x1 - 8].forEach(function (x) { q.fillStyle = wd; q.beginPath(); q.moveTo(x, y + 4); q.lineTo(x + 2, y + 4); q.lineTo(x + 2, y + 14); q.closePath(); q.fill(); });
}
/* a hanging khom (Lanna lantern) under the eave; lit by night */
function khom(c, x, y, s, N, t, k) {
  if (N) glow(c, x, y + s * 0.5, s * 2.4, 35, 0.6 + 0.1 * Math.sin(t / 300 + k));
  line(c, [[x, y - s * 0.6], [x, y]], 'rgba(40,20,10,.8)', 1);
  solid(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.2, y); q.lineTo(x + s * 0.2, y); q.lineTo(x + s * 0.42, y + s * 0.45); q.lineTo(x + s * 0.2, y + s * 0.9); q.lineTo(x - s * 0.2, y + s * 0.9); q.lineTo(x - s * 0.42, y + s * 0.45); q.closePath(); }, N ? '#ffb347' : '#d9342b', 1);
  c.fillStyle = '#f2c94c'; c.fillRect(x - s * 0.42, y + s * 0.43, s * 0.84, 2);
  line(c, [[x - s * 0.1, y + s * 0.9], [x - s * 0.12, y + s * 1.25]], '#f2c94c', 1); line(c, [[x + s * 0.1, y + s * 0.9], [x + s * 0.12, y + s * 1.25]], '#f2c94c', 1);
}

/* ---------------------------------------------------------------- lacquerware (เครื่องเขิน)
   finished pieces: the khantok tray on its foot, the round betel box, the khan dok
   vessel, a lidded jar; black ground, red cinnabar, gold */
var LK = '#17110f', LR = '#b3261e', LG = '#e2b33c';
function ware(q, kind, x, y, s) {
  q.save(); q.lineWidth = Math.max(1, s * 0.03); q.strokeStyle = LG;
  if (kind === 'tray') {   /* khantok: a round tray on a flared foot */
    var r = s * 0.95, ty = y - s * 0.55;
    solid(q, poly([[x - r * 0.42, y], [x + r * 0.42, y], [x + r * 0.2, ty + s * 0.12], [x - r * 0.2, ty + s * 0.12]]), LR, 1);
    q.beginPath(); q.moveTo(x - r * 0.42, y - s * 0.06); q.lineTo(x + r * 0.42, y - s * 0.06); q.moveTo(x - r * 0.24, ty + s * 0.2); q.lineTo(x + r * 0.24, ty + s * 0.2); q.stroke();
    for (var i = -3; i <= 3; i++) { q.beginPath(); q.moveTo(x + i * r * 0.09, y - s * 0.08); q.lineTo(x + i * r * 0.05, ty + s * 0.18); q.stroke(); }
    solid(q, function (c) { c.beginPath(); c.ellipse(x, ty, r, s * 0.15, 0, 0, TAU); }, LR, 1);
    q.fillStyle = LK; q.beginPath(); q.ellipse(x, ty - s * 0.01, r * 0.86, s * 0.11, 0, 0, TAU); q.fill();
    q.beginPath(); q.ellipse(x, ty, r, s * 0.15, 0, 0, TAU); q.stroke();
    for (i = 0; i < 6; i++) star(q, x + Math.cos(i / 6 * TAU) * r * 0.55, ty - s * 0.01 + Math.sin(i / 6 * TAU) * s * 0.06, s * 0.05, LG);
  } else if (kind === 'box' || kind === 'jar') {   /* the round betel box; the lidded jar is taller */
    var w = s * (kind === 'jar' ? 0.42 : 0.55), bt = y - s * (kind === 'jar' ? 0.7 : 0.62), ry = w * 0.25;
    solid(q, function (c) { c.beginPath(); c.moveTo(x - w, bt); c.lineTo(x - w * (kind === 'jar' ? 0.75 : 1), y - ry); c.ellipse(x, y - ry, w * (kind === 'jar' ? 0.75 : 1), ry, 0, Math.PI, 0, true); c.lineTo(x + w, bt); c.closePath(); }, kind === 'jar' ? LK : LR, 1);
    q.fillStyle = kind === 'jar' ? LR : LK; q.fillRect(x - w * 0.97, bt + (y - bt) * 0.42, w * 1.94, (y - bt) * 0.2);
    q.beginPath(); q.moveTo(x - w, bt + (y - bt) * 0.4); q.lineTo(x + w, bt + (y - bt) * 0.4); q.moveTo(x - w * 0.96, bt + (y - bt) * 0.64); q.lineTo(x + w * 0.96, bt + (y - bt) * 0.64); q.stroke();
    for (i = -2; i <= 2; i++) star(q, x + i * w * 0.38, bt + (y - bt) * 0.52, s * 0.045, LG);
    solid(q, function (c) { c.beginPath(); c.ellipse(x, bt, w * 1.04, ry, 0, Math.PI, 0); c.quadraticCurveTo(x + w * 0.9, bt - s * 0.22, x, bt - s * 0.24); c.quadraticCurveTo(x - w * 0.9, bt - s * 0.22, x - w * 1.04, bt); c.closePath(); }, kind === 'jar' ? LR : LK, 1);
    q.beginPath(); q.ellipse(x, bt, w * 1.04, ry, 0, 0, TAU); q.stroke();
    q.fillStyle = LG; q.beginPath(); q.arc(x, bt - s * 0.27, s * 0.05, 0, TAU); q.fill();
  } else if (kind === 'vessel') {   /* khan dok: a footed bowl under a tall stepped cone, gold on black */
    var bw = s * 0.32, by2 = y - s * 0.38;
    solid(q, poly([[x - bw * 0.7, y], [x + bw * 0.7, y], [x + bw * 0.25, y - s * 0.12], [x + bw * 0.25, by2 + s * 0.06], [x - bw * 0.25, by2 + s * 0.06], [x - bw * 0.25, y - s * 0.12]]), LK, 1);
    solid(q, function (c) { c.beginPath(); c.moveTo(x - bw, by2); c.quadraticCurveTo(x - bw, by2 + s * 0.12, x, by2 + s * 0.12); c.quadraticCurveTo(x + bw, by2 + s * 0.12, x + bw, by2); c.closePath(); }, LR, 1);
    solid(q, function (c) { c.beginPath(); c.moveTo(x - bw * 0.95, by2); for (var k = 0; k <= 5; k++) { var yy = by2 - k * s * 0.11, ww = bw * (0.95 - k * 0.17); c.lineTo(x - ww, yy); c.lineTo(x - ww * 0.85, yy - s * 0.02); } c.lineTo(x, by2 - s * 0.62); for (k = 5; k >= 0; k--) { var y3 = by2 - k * s * 0.11, w3 = bw * (0.95 - k * 0.17); c.lineTo(x + w3 * 0.85, y3 - s * 0.02); c.lineTo(x + w3, y3); } c.closePath(); }, LK, 1);
    for (i = 0; i < 5; i++) { q.beginPath(); q.moveTo(x - bw * (0.9 - i * 0.17), by2 - i * s * 0.11); q.lineTo(x + bw * (0.9 - i * 0.17), by2 - i * s * 0.11); q.stroke(); }
    q.fillStyle = LG; q.beginPath(); q.arc(x, by2 - s * 0.64, s * 0.035, 0, TAU); q.fill();
  }
  q.restore();
}
function pot(q, x, y, s, col, lip) {
  solid(q, function (c) { c.beginPath(); c.moveTo(x - s * 0.5, y - s * 0.75); c.quadraticCurveTo(x - s * 0.75, y - s * 0.2, x - s * 0.4, y); c.lineTo(x + s * 0.4, y); c.quadraticCurveTo(x + s * 0.75, y - s * 0.2, x + s * 0.5, y - s * 0.75); c.closePath(); }, '#6a4a32', 1);
  q.fillStyle = col; q.beginPath(); q.ellipse(x, y - s * 0.75, s * 0.48, s * 0.12, 0, 0, TAU); q.fill();
  if (lip) { q.strokeStyle = lip; q.lineWidth = 1; q.stroke(); }
}
function lacquer(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var w = Math.min(S.span * 0.68, h * 5.8), a0 = S.x0 + S.span * 0.05, a1 = a0 + w, top = d - h * 2.05;
  var cx = a0 + w * 0.34, base = d - h * 0.2, R = h * 0.44, BH = h * 0.5, ry = R * 0.27, yT = base - BH, ax = cx - R - h * 0.28;
  var bookX = ax + h * 0.2, bookY = d + h * 0.05;
  layer(S, 'lacquer', top - h * 0.7, S.H, function (q) {
    floor(q, S, N ? '#3a2416' : '#8a5a32', true);
    wall(q, a0 + w * 0.05, a1 - w * 0.05, d - h * 1.3, d, N);
    K.sala(q, a0, a1, d, top, N, N ? '#4a1612' : '#8e2a20');
    var sy = d - h * 0.98; shelf(q, a0 + w * 0.6, a1 - w * 0.08, sy, N);
    ware(q, 'tray', a0 + w * 0.66, sy, h * 0.42); ware(q, 'box', a0 + w * 0.775, sy, h * 0.36); ware(q, 'vessel', a0 + w * 0.87, sy, h * 0.62);
    ware(q, 'jar', a0 + w * 0.66, d + h * 0.02, h * 0.58); ware(q, 'tray', a0 + w * 0.8, d + h * 0.03, h * 0.4);
    var ox = a1 + h * 0.7; if (ox < S.x1 - h * 0.9) { ware(q, 'box', ox, d + h * 0.04, h * 0.5); ware(q, 'tray', ox, d - h * 0.5, h * 0.3); }
    pot(q, ax - h * 0.45, d + h * 0.06, h * 0.2, LK, LG); pot(q, ax - h * 0.2, d + h * 0.1, h * 0.17, LR, LG);
    /* the turntable: a post, a disc */
    paper(q, rect(cx - h * 0.04, base, h * 0.08, d - base + h * 0.02), N ? '#3a2416' : '#5a3a20', 1);
    solid(q, function (c2) { c2.beginPath(); c2.ellipse(cx, base + 2, R * 1.12, ry * 1.1, 0, 0, TAU); }, N ? '#4a2e1c' : '#6a4426', 1);
    /* the gold-leaf booklet */
    paper(q, rect(bookX - h * 0.13, bookY - h * 0.04, h * 0.26, h * 0.05), '#f2e6c9', 0.6);
    q.fillStyle = '#e8b84a'; q.fillRect(bookX - h * 0.1, bookY - h * 0.055, h * 0.2, h * 0.02);
  });
  khom(c, a0 + w * 0.55, top + h * 0.5, h * 0.22, N, t, 1);
  /* the box turns three times a cycle: one turn for the red, one for the gold, one to shine */
  var T = 18000, p = (t % T) / T, rot = p * 3 * TAU, Ab = -0.95, Ag = -0.62, n = 32;
  function laid(th, from, to) { var r0 = from * 3 * TAU, r1 = Math.min(rot, to * 3 * TAU); if (rot < r0) return false; return ((((Ab - r0) - th) % TAU) + TAU) % TAU <= r1 - r0; }
  function gilt(th, from, to) { var r0 = from * 3 * TAU, r1 = Math.min(rot, to * 3 * TAU); if (rot < r0) return false; return ((((Ag - r0) - th) % TAU) + TAU) % TAU <= r1 - r0; }
  var bands = [[0, 0.2, 0], [0.2, 0.8, 1], [0.8, 1, 0]];
  for (i = 0; i < n; i++) {
    var th = i / n * TAU, a = th + rot, b = a + TAU / n, m = (a + b) / 2;
    if (Math.cos(m) < -0.02) continue;
    var xa = cx + R * Math.sin(a), xb = cx + R * Math.sin(b), ya = Math.cos(a) * ry, yb = Math.cos(b) * ry, lit = 0.55 + 0.45 * Math.cos(m - 0.35);
    var red = laid(th, 0.1, 0.4333), gold = gilt(th, 0.45, 0.7833);
    bands.forEach(function (B) {
      var y0 = yT + BH * B[0], y1 = yT + BH * B[1];
      c.fillStyle = B[2] && red ? mixc('#4a0c08', '#d8402e', lit) : mixc('#050404', '#3a2e2a', lit);
      c.beginPath(); c.moveTo(xa, y0 + ya); c.lineTo(xb + 0.4, y0 + yb); c.lineTo(xb + 0.4, y1 + yb); c.lineTo(xa, y1 + ya); c.closePath(); c.fill();
    });
    if (gold) {
      var mx = (xa + xb) / 2, sx = Math.max(0.15, Math.cos(m)), my = (ya + yb) / 2;
      c.save(); c.translate(mx, 0); c.scale(sx, 1);
      if (i % 4 === 0) { var fy = yT + BH * 0.5 + my, fr = BH * 0.16; c.fillStyle = LG; for (var k = 0; k < 4; k++) { c.beginPath(); c.ellipse(Math.cos(k * TAU / 4) * fr * 0.55, fy + Math.sin(k * TAU / 4) * fr * 0.55, fr * 0.42, fr * 0.24, k * TAU / 4, 0, TAU); c.fill(); } c.fillStyle = LR; c.beginPath(); c.arc(0, fy, fr * 0.22, 0, TAU); c.fill(); }
      else if (i % 4 === 2) { star(c, 0, yT + BH * 0.5 + my, BH * 0.07, LG); }
      c.fillStyle = LG; var zw = (R * TAU / n) * 0.5;
      c.beginPath(); c.moveTo(-zw, yT + BH * 0.2 + my); c.lineTo(0, yT + BH * 0.06 + my); c.lineTo(zw, yT + BH * 0.2 + my); c.fill();
      c.beginPath(); c.moveTo(-zw, yT + BH * 0.8 + my); c.lineTo(0, yT + BH * 0.94 + my); c.lineTo(zw, yT + BH * 0.8 + my); c.fill();
      c.restore();
    }
  }
  /* the lid; its rosette comes with the last of the gold */
  var gl = seg(p, 0.75, 0.8);
  c.fillStyle = '#0c0807'; c.beginPath(); c.ellipse(cx, yT, R * 1.04, ry * 1.05, 0, 0, TAU); c.fill();
  c.fillStyle = '#1e1714'; c.beginPath(); c.ellipse(cx, yT - BH * 0.06, R * 0.8, ry * 0.8, 0, 0, TAU); c.fill();
  if (gl > 0) { c.save(); c.globalAlpha = gl; c.strokeStyle = LG; c.lineWidth = Math.max(1, h * 0.02); c.beginPath(); c.ellipse(cx, yT, R * 1.0, ry, 0, 0, TAU); c.stroke();
    for (i = 0; i < 8; i++) star(c, cx + Math.cos(i / 8 * TAU) * R * 0.55, yT - BH * 0.06 + Math.sin(i / 8 * TAU) * ry * 0.55, h * 0.03, LG); c.restore(); }
  c.fillStyle = gl > 0.5 ? LG : '#2a201c'; c.beginPath(); c.ellipse(cx, yT - BH * 0.14, R * 0.12, ry * 0.25, 0, 0, TAU); c.fill(); c.beginPath(); c.arc(cx, yT - BH * 0.22, R * 0.08, 0, TAU); c.fill();
  /* finished: a gleam slides across, the lacquer's mirror */
  var sh = seg(p, 0.8, 0.95);
  if (sh > 0 && sh < 1) { c.save(); c.beginPath(); c.rect(cx - R, yT - ry, R * 2, BH + ry * 2); c.clip(); var gx = cx - R * 1.6 + sh * R * 3.2;
    var g = c.createLinearGradient(gx - R * 0.3, 0, gx + R * 0.3, 0); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,250,230,.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = g; c.beginPath(); c.moveTo(gx - R * 0.2, yT - ry); c.lineTo(gx + R * 0.3, yT - ry); c.lineTo(gx + R * 0.0, base + ry); c.lineTo(gx - R * 0.5, base + ry); c.fill(); c.restore();
    star(c, cx + R * 0.5, yT + BH * 0.3, h * 0.06 * Math.sin(sh * Math.PI), '#fff6d0'); }
  /* the lacquerer: the brush in her near hand on the red turn, the leaf in the far hand on the gold */
  var crew = K.town(S, 2, { sin: 0.6, mohom: 0.4 }), dB = [cx + R * Math.sin(Ab) - 1, yT + BH * (0.5 + 0.25 * Math.sin(t / 380))];
  var onRed = p > 0.08 && p < 0.44, onGold = p > 0.44 && p < 0.79, mot = ((rot - 0.45 * 3 * TAU) / (TAU / 8)) % 1;
  var leafT = onGold ? Math.sin(Math.PI * mot) : 0, leafP = [lerp(bookX + h * 0.05, cx + R * Math.sin(Ag) - 1, ease(1 - Math.abs(1 - 2 * mot))), lerp(bookY - h * 0.08, yT + BH * 0.45, ease(1 - Math.abs(1 - 2 * mot))) - leafT * h * 0.12];
  var me = fig(S, crew[0], ax, d, h, SIT, 1, onRed ? dB : [ax + h * 0.22, d - h * 0.2], onGold ? leafP : [ax + h * 0.16, d - h * 0.16]);
  if (onRed) { line(c, [me.hand[0], [dB[0] + 2, dB[1]]], '#6a4426', Math.max(1.4, h * 0.025)); c.fillStyle = LR; c.beginPath(); c.arc(dB[0] + 1, dB[1], h * 0.022, 0, TAU); c.fill(); }
  if (onGold && mot < 0.5) { c.fillStyle = '#ffd65a'; c.save(); c.translate(me.hand[1][0], me.hand[1][1] - h * 0.02); c.rotate(t / 300); c.fillRect(-h * 0.035, -h * 0.035, h * 0.07, h * 0.07); c.restore(); }
  if (onGold && mot > 0.45 && mot < 0.62) star(c, cx + R * Math.sin(Ag), yT + BH * 0.45, h * 0.07, '#fff3b0');
  label(S, (a0 + a1) / 2, top + h * 0.2, '#8e2a20');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* ---------------------------------------------------------------- wood (Ban Tawai)
   an elephant, the north's: body, head, the ear, the trunk curled up, four legs */
function elephant(c, x, y, s, dir, col, line2) {
  c.save(); c.fillStyle = col;
  c.beginPath(); c.ellipse(x, y - s * 0.56, s * 0.5, s * 0.3, 0, 0, TAU); c.fill();
  [-0.36, -0.16, 0.16, 0.34].forEach(function (o, i) { c.fillRect(x + dir * s * o - s * 0.075, y - s * 0.5, s * 0.15, s * (i % 2 ? 0.5 : 0.48)); });
  c.beginPath(); c.arc(x + dir * s * 0.46, y - s * 0.7, s * 0.24, 0, TAU); c.fill();
  c.lineCap = 'round'; c.strokeStyle = col; c.lineWidth = s * 0.13;
  c.beginPath(); c.moveTo(x + dir * s * 0.62, y - s * 0.66); c.quadraticCurveTo(x + dir * s * 0.82, y - s * 0.4, x + dir * s * 0.76, y - s * 0.2); c.quadraticCurveTo(x + dir * s * 0.8, y - s * 0.08, x + dir * s * 0.92, y - s * 0.16); c.stroke();
  c.lineWidth = s * 0.03; c.beginPath(); c.moveTo(x - dir * s * 0.48, y - s * 0.62); c.quadraticCurveTo(x - dir * s * 0.6, y - s * 0.45, x - dir * s * 0.56, y - s * 0.3); c.stroke();
  if (line2) {
    c.strokeStyle = line2; c.lineWidth = Math.max(1, s * 0.025);
    c.beginPath(); c.ellipse(x + dir * s * 0.32, y - s * 0.68, s * 0.13, s * 0.19, 0, 0, TAU); c.stroke();
    c.beginPath(); c.moveTo(x - dir * s * 0.3, y - s * 0.78); c.quadraticCurveTo(x, y - s * 0.88, x + dir * s * 0.2, y - s * 0.8); c.stroke();
    c.fillStyle = line2; c.beginPath(); c.arc(x + dir * s * 0.55, y - s * 0.76, s * 0.025, 0, TAU); c.fill();
    c.strokeStyle = '#f5ecd8'; c.lineWidth = s * 0.04; c.beginPath(); c.moveTo(x + dir * s * 0.6, y - s * 0.56); c.quadraticCurveTo(x + dir * s * 0.7, y - s * 0.5, x + dir * s * 0.74, y - s * 0.56); c.stroke();
  }
  c.restore();
}
/* a kranok scroll: the flame-leaf of Lanna carving, a spiral r = a·e^(−bθ) with a flame off its tip */
function kranok(c, x, y, s, dir, col) {
  c.strokeStyle = col; c.lineWidth = Math.max(1, s * 0.09); c.lineCap = 'round'; c.beginPath();
  for (var a = 0; a <= 5.5; a += 0.25) { var r = s * 0.5 * Math.exp(-0.28 * a); var px = x + dir * Math.cos(a) * r, py = y - Math.sin(a) * r; a ? c.lineTo(px, py) : c.moveTo(px, py); }
  c.stroke();
  c.fillStyle = col; c.beginPath(); c.moveTo(x + dir * s * 0.5, y); c.quadraticCurveTo(x + dir * s * 0.9, y - s * 0.2, x + dir * s * 1.2, y - s * 0.75); c.quadraticCurveTo(x + dir * s * 0.75, y - s * 0.4, x + dir * s * 0.35, y - s * 0.2); c.closePath(); c.fill();
}
function wood(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var w = Math.min(S.span * 0.66, h * 5.6), a0 = S.x0 + S.span * 0.05, a1 = a0 + w, top = d - h * 2.05;
  var bx0 = a0 + w * 0.3, ew = h * 1.15, eh = h * 0.92, sy = d - h * 0.26, bx1 = bx0 + ew, by0 = sy - eh;
  var teak = N ? '#6a4224' : '#a8693a', fresh = N ? '#9a6a3e' : '#e0a468', dark = N ? '#2a1a0e' : '#5a3418';
  layer(S, 'wood', top - h * 0.7, S.H, function (q) {
    floor(q, S, N ? '#2e2218' : '#9a7a52');
    wall(q, a0 + w * 0.05, a1 - w * 0.05, d - h * 1.3, d, N);
    K.sala(q, a0, a1, d, top, N, N ? '#3e2418' : '#7a3a22');
    /* a carved panel on the wall: kranok scrolls in a frame */
    var px0 = a0 + w * 0.55, px1 = a1 - w * 0.08, py0 = d - h * 1.55, py1 = d - h * 1.05;
    paper(q, rect(px0, py0, px1 - px0, py1 - py0), teak, 1.2);
    q.strokeStyle = dark; q.lineWidth = 2; q.strokeRect(px0 + 3, py0 + 3, px1 - px0 - 6, py1 - py0 - 6);
    for (var k = 0; k < 4; k++) kranok(q, px0 + (px1 - px0) * (0.14 + k * 0.24), py1 - (py1 - py0) * 0.25, (py1 - py0) * 0.42, k % 2 ? -1 : 1, dark);
    /* the herd, smallest last, as Ban Tawai lines them up */
    var ex = a0 + w * 0.6, sz = [0.78, 0.6, 0.46, 0.34];
    sz.forEach(function (z) { elephant(q, ex + z * h * 0.45, d + h * 0.04, z * h, 1, teak, dark); ex += z * h * 1.05; });
    if (a1 + h * 1.6 < S.x1 - h * 0.6) { elephant(q, a1 + h * 0.95, d + h * 0.06, h * 1.0, -1, teak, dark); }
    /* the stump, the sawdust */
    solid(q, poly([[bx0 + ew * 0.1, sy], [bx1 - ew * 0.1, sy], [bx1 - ew * 0.05, d + 2], [bx0 + ew * 0.05, d + 2]]), N ? '#4a3020' : '#7a5232', 1);
    q.fillStyle = N ? '#5a4632' : '#e8c48a'; q.beginPath(); q.ellipse(bx0 + ew * 0.5, d + 3, ew * 0.7, h * 0.07, 0, Math.PI, TAU); q.fill();
  });
  khom(c, a0 + w * 0.2, top + h * 0.5, h * 0.22, N, t, 2);
  /* the block gives way from the left: f, the share carved */
  var T = 15000, p = (t % T) / T, f = 0.3 + 0.7 * ease(seg(p, 0.04, 0.8)), edge = bx0 + f * ew, working = p > 0.03 && p < 0.8;
  elephant(c, bx0 + ew * 0.38, sy, ew / 1.5, 1, fresh, dark);
  c.fillStyle = 'rgba(90,50,20,.25)'; c.fillRect(bx0, sy - 2, ew, 2);
  if (f < 1) {
    var r = rnd(7), pts = [[edge, by0]];
    for (i = 1; i < 8; i++) pts.push([edge + (r() - 0.5) * h * 0.06, by0 + eh * i / 8]);
    pts.push([edge, sy], [bx1, sy], [bx1, by0]);
    solid(c, poly(pts), teak, 1);
    c.strokeStyle = dark; c.lineWidth = 1; c.globalAlpha = 0.5;
    for (i = 1; i < 6; i++) { c.beginPath(); c.moveTo(Math.max(edge, bx0) + 3, by0 + eh * i / 6); c.lineTo(bx1 - 2, by0 + eh * i / 6 + Math.sin(i) * 2); c.stroke(); }
    c.globalAlpha = 1;
  }
  /* mallet on chisel: lift = |sin(πt/650)|, a strike at each zero, chips on parabolas */
  var crew = K.town(S, 2, { mohom: 0.6, casual: 0.4 }), cy = by0 + eh * (0.35 + 0.3 * Math.sin(t / 1700)), tip = [edge - 1, cy];
  var butt = [tip[0] - h * 0.24, tip[1] + h * 0.05], lift = working ? Math.pow(Math.abs(Math.sin(Math.PI * t / 650)), 0.7) : 0.6;
  var mh = [butt[0] - h * 0.06 - lift * h * 0.08, butt[1] - h * 0.04 - lift * h * 0.22], cxr = bx0 - h * 0.62;
  var me = fig(S, crew[0], cxr, d, h * 1.02, STAND, 1, mh, [lerp(butt[0], tip[0], 0.3), lerp(butt[1], tip[1], 0.3)]);
  if (working || f < 1) line(c, [butt, tip], '#cfd5de', Math.max(1.5, h * 0.03));
  c.save(); c.translate(me.hand[0][0], me.hand[0][1]); c.rotate(-0.4 - lift * 0.8);
  line(c, [[0, 0], [h * 0.16, 0]], '#7a4a2a', Math.max(1.5, h * 0.03)); solid(c, rect(h * 0.12, -h * 0.07, h * 0.1, h * 0.14), N ? '#5a3418' : '#8a5a32', 0.6); c.restore();
  if (working) {
    var k0 = Math.floor(t / 650);
    for (var kk = k0 - 2; kk <= k0; kk++) {
      var age = (t - kk * 650) / 1000; if (age < 0) continue;
      var rr = rnd(kk * 31 + 5);
      for (i = 0; i < 4; i++) {
        var vx = (rr() - 0.25) * h * 1.6, vy = h * (0.6 + rr() * 1.2), x = tip[0] + vx * age, y = tip[1] - vy * age + h * 3.2 * age * age;
        if (y > d + 4) continue;
        c.save(); c.translate(x, y); c.rotate(age * 9 + i); c.fillStyle = i % 2 ? fresh : '#f2d39a'; c.fillRect(-h * 0.025, -h * 0.012, h * 0.05, h * 0.024); c.restore();
      }
    }
  } else if (p > 0.8) { var u = seg(p, 0.8, 0.98); star(c, bx0 + ew * 0.7, by0 + eh * 0.25, h * 0.08 * Math.sin(u * Math.PI), '#fff3b0'); star(c, bx0 + ew * 0.2, by0 + eh * 0.5, h * 0.05 * Math.sin(u * Math.PI * 2), '#fff3b0'); }
  label(S, (a0 + a1) / 2, top + h * 0.2, '#7a3a22');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* ---------------------------------------------------------------- silver (Wua Lai)
   the silver ubosot of Wat Sri Suphan behind: three tiers of roof, chofa, walls of
   pressed silver; a bowl turning on the smith's stake */
function ubosot(q, x0, x1, d, h, N) {
  var w = x1 - x0, m = (x0 + x1) / 2, sv = N ? '#a8b0c0' : '#dfe4ec', sv2 = N ? '#7a8294' : '#a9b1bf', sv3 = N ? '#c8d0dc' : '#f4f6fa';
  var g = q.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, sv2); g.addColorStop(0.45, sv3); g.addColorStop(1, sv2);
  if (N) { var gg = q.createRadialGradient(m, d - h * 1.1, 0, m, d - h * 1.1, w * 0.9); gg.addColorStop(0, 'rgba(200,220,255,.35)'); gg.addColorStop(1, 'rgba(200,220,255,0)'); q.fillStyle = gg; q.beginPath(); q.arc(m, d - h * 1.1, w * 0.9, 0, TAU); q.fill(); }
  paper(q, rect(x0 - w * 0.04, d - h * 0.2, w * 1.08, h * 0.2), sv2, 1);
  paper(q, rect(x0 + w * 0.06, d - h * 1.0, w * 0.88, h * 0.8), g, 1.2);
  q.strokeStyle = 'rgba(80,90,110,.5)'; q.lineWidth = 1;
  for (var i = 0; i < 4; i++) { var wx = x0 + w * (0.16 + i * 0.2); q.strokeRect(wx, d - h * 0.8, w * 0.1, h * 0.45); q.beginPath(); q.arc(wx + w * 0.05, d - h * 0.8, w * 0.05, Math.PI, TAU); q.stroke(); }
  q.fillStyle = 'rgba(80,90,110,.35)'; for (i = 0; i < 26; i++) { q.beginPath(); q.arc(x0 + w * (0.09 + (i % 13) * 0.065), d - h * (0.92 - Math.floor(i / 13) * 0.62), 1.3, 0, TAU); q.fill(); }
  [[0.0, 1.0, 1.0, 1.42], [0.12, 0.88, 1.36, 1.78], [0.26, 0.74, 1.72, 2.12]].forEach(function (r, k) {
    paper(q, poly([[x0 + w * r[0] - w * 0.04, d - h * r[2]], [x0 + w * (r[0] + 0.12), d - h * r[3]], [x0 + w * (r[1] - 0.12), d - h * r[3]], [x0 + w * r[1] + w * 0.04, d - h * r[2]]]), k % 2 ? sv : sv3, 1.2);
    q.strokeStyle = sv2; q.lineWidth = 1.2; q.beginPath(); q.moveTo(x0 + w * r[0] - w * 0.03, d - h * r[2] - 2); q.lineTo(x0 + w * r[1] + w * 0.03, d - h * r[2] - 2); q.stroke();
    [x0 + w * r[0] - w * 0.04, x0 + w * r[1] + w * 0.04].forEach(function (ex, j) { q.strokeStyle = sv3; q.lineWidth = 2; q.beginPath(); q.moveTo(ex, d - h * r[2]); q.quadraticCurveTo(ex + (j ? 1 : -1) * w * 0.03, d - h * r[2] - h * 0.04, ex + (j ? 1 : -1) * w * 0.02, d - h * r[2] - h * 0.12); q.stroke(); });
  });
  q.strokeStyle = sv3; q.lineWidth = 2.4; q.beginPath(); q.moveTo(m, d - h * 2.12); q.quadraticCurveTo(m + w * 0.05, d - h * 2.25, m + w * 0.02, d - h * 2.3); q.stroke();
  /* the gable's sunburst */
  q.strokeStyle = 'rgba(90,100,120,.45)'; for (i = 0; i < 7; i++) { var a = Math.PI + (i + 0.5) / 7 * Math.PI; q.beginPath(); q.moveTo(m, d - h * 1.76); q.lineTo(m + Math.cos(a) * w * 0.22, d - h * 1.76 + Math.sin(a) * h * 0.3); q.stroke(); }
}
function silver(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var u0 = S.x0 + S.span * 0.05, u1 = u0 + Math.min(S.span * 0.36, h * 3.0), wx = Math.max(u1 + h * 0.9, S.x0 + S.span * 0.52), ex = wx + h * 0.62;
  var bowlY = d - h * 0.62, R = h * 0.42, BH = h * 0.36, ry = R * 0.24, tbl = Math.min(S.x1 - h * 0.8, ex + h * 1.1);
  layer(S, 'silver', d - h * 2.6, S.H, function (q) {
    floor(q, S, N ? '#2a2420' : '#8a7458');
    ubosot(q, u0, u1, d, h, N);
    /* a low wall before the temple, its gate */
    paper(q, rect(u0 - h * 0.1, d - h * 0.3, (u1 - u0) + h * 0.2, h * 0.3), N ? '#6a6e7a' : '#cfd3da', 1);
    /* the stake and its pitch bowl, the brazier, the stool */
    paper(q, rect(ex - h * 0.05, bowlY + BH * 0.2, h * 0.1, d - bowlY - BH * 0.2), N ? '#3a2416' : '#6a4426', 1);
    solid(q, function (c2) { c2.beginPath(); c2.ellipse(ex, bowlY + BH * 0.35, R * 0.75, ry * 0.9, 0, 0, TAU); }, '#2a1a12', 1);
    solid(q, poly([[wx - h * 0.62, d - h * 0.2], [wx - h * 0.3, d - h * 0.2], [wx - h * 0.34, d + 2], [wx - h * 0.58, d + 2]]), '#5a4a42', 1);
    /* the table of finished bowls under a cloth */
    if (tbl + h * 0.7 < S.x1) {
      paper(q, rect(tbl - h * 0.1, d - h * 0.45, h * 1.0, h * 0.45), N ? '#4a1a3a' : '#7a2a5a', 1);
      q.fillStyle = '#e8b84a'; q.fillRect(tbl - h * 0.1, d - h * 0.12, h * 1.0, h * 0.04);
      [[0.15, 0.22], [0.5, 0.3], [0.82, 0.2]].forEach(function (b) { bowl(q, tbl + h * b[0], d - h * 0.45, h * b[1], N, t, 0, 1); });
    }
  });
  /* twinkles run along the temple's eaves and chofa: the silver catching light */
  var tw = [[0.0, 1.0], [1.0, 1.0], [0.12, 1.36], [0.88, 1.36], [0.26, 1.72], [0.74, 1.72], [0.5, 2.22], [0.3, 0.6], [0.7, 0.6]];
  tw.forEach(function (q2, k) { var a = Math.pow(Math.max(0, Math.sin(t / 700 - k * 0.7)), 6); if (a > 0.05) star(c, u0 + (u1 - u0) * q2[0], d - h * q2[1], h * 0.09 * a, 'rgba(255,255,255,' + (0.4 + 0.6 * a) + ')'); });
  /* the bowl turns; each tap raises the next motif where the tool meets it */
  var T = 16000, p = (t % T) / T, rot = -0.6 + p * 1.1 * TAU, At = -1.0;
  var raised = function (th) { var r0 = -0.6 + 0.04 * 1.1 * TAU, r1 = Math.min(rot, -0.6 + 0.9 * 1.1 * TAU); if (rot < r0) return false; return ((((At - r0) - th) % TAU) + TAU) % TAU <= r1 - r0; };
  bowl(c, ex, bowlY, R, N, rot, raised);
  var tap = Math.pow(Math.abs(Math.sin(Math.PI * t / 420)), 0.6), working = p > 0.04 && p < 0.9;
  var tp = [ex + R * Math.sin(At) * 0.96, bowlY - BH * 0.45], butt = [tp[0] - h * 0.14, tp[1] - h * 0.12];
  var crew = K.town(S, 1, { mohom: 1 }), hm = [butt[0] - h * 0.03 - (working ? tap : 0.5) * h * 0.1, butt[1] - h * 0.02 - (working ? tap : 0.5) * h * 0.14];
  var me = fig(S, crew[0], wx - h * 0.46, d, h, STOOL, 1, hm, [lerp(butt[0], tp[0], 0.3), lerp(butt[1], tp[1], 0.3)]);
  line(c, [butt, tp], '#cfd5de', Math.max(1.4, h * 0.028));
  c.save(); c.translate(me.hand[0][0], me.hand[0][1]); c.rotate(-0.7 - (working ? tap : 0.5) * 0.5); line(c, [[0, 0], [h * 0.14, 0]], '#7a4a2a', Math.max(1.4, h * 0.025)); solid(c, rect(h * 0.12, -h * 0.04, h * 0.05, h * 0.08), '#9aa0ac', 0.5); c.restore();
  if (working && tap < 0.25) { var a2 = 1 - tap * 4; star(c, tp[0], tp[1], h * 0.07 * a2, 'rgba(255,255,240,' + a2 + ')');
    c.strokeStyle = 'rgba(255,255,255,' + 0.6 * a2 + ')'; c.lineWidth = 1; for (i = 1; i <= 2; i++) { c.beginPath(); c.arc(tp[0], tp[1], h * 0.06 * i * (1.6 - a2), -2.4, -0.8); c.stroke(); } }
  /* the brazier's coals */
  var cx0 = wx - h * 0.46, fl = 0.7 + 0.3 * Math.sin(t / 130) * Math.sin(t / 317);
  glow(c, cx0, d - h * 0.22, h * (N ? 0.5 : 0.3), 20, 0.6 * fl);
  for (i = 0; i < 5; i++) { c.fillStyle = i % 2 ? '#ff6a2a' : '#ffb347'; c.beginPath(); c.arc(cx0 - h * 0.12 + i * h * 0.06, d - h * 0.22, h * 0.035, 0, TAU); c.fill(); }
  label(S, S.x0 + S.span * 0.62, d - h * 2.05, '#5a6478');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: d - h * 2.3, y1: S.H });
}
/* a silver bowl (salung): a footed round bowl, the rim lit, motifs in repoussé round its
   wall; turning bowls draw only the faces toward us, x = R·sin(θ + rot), width ∝ cos */
function bowl(c, x, y, R, N, rot, raised, still) {
  var BH = R * 0.85, ry = R * 0.24, n = 24, i, lo = N ? '#5a6272' : '#7c8494', hi = N ? '#dfe6f0' : '#ffffff';
  var g = c.createLinearGradient(x - R, 0, x + R, 0); g.addColorStop(0, lo); g.addColorStop(0.38, hi); g.addColorStop(0.62, N ? '#b8c0cc' : '#dfe4ec'); g.addColorStop(1, lo);
  solid(c, function (q) { q.beginPath(); q.moveTo(x - R * 0.35, y + BH + R * 0.1); q.lineTo(x + R * 0.35, y + BH + R * 0.1); q.lineTo(x + R * 0.2, y + BH * 0.88); q.lineTo(x - R * 0.2, y + BH * 0.88); q.closePath(); }, lo, 0.8);
  solid(c, function (q) { q.beginPath(); q.moveTo(x - R, y); q.bezierCurveTo(x - R, y + BH * 0.7, x - R * 0.5, y + BH, x, y + BH); q.bezierCurveTo(x + R * 0.5, y + BH, x + R, y + BH * 0.7, x + R, y); q.closePath(); }, g, 1);
  c.fillStyle = N ? '#3a3e48' : '#6a7282'; c.beginPath(); c.ellipse(x, y, R, ry, 0, 0, TAU); c.fill();
  c.strokeStyle = hi; c.lineWidth = Math.max(1, R * 0.05); c.beginPath(); c.ellipse(x, y, R, ry, 0, 0, TAU); c.stroke();
  for (i = 0; i < n; i++) {
    var th = i / n * TAU, a = still ? th : th + rot, ca = Math.cos(a);
    if (ca < 0.12) continue;
    if (!still && !raised(th)) continue;
    var mx = x + R * 0.86 * Math.sin(a), my = y + BH * 0.42 + ca * ry * 0.4, s = R * 0.2;
    c.save(); c.translate(mx, my); c.scale(ca, 1);
    if (i % 3 === 0) { c.fillStyle = 'rgba(40,46,60,.45)'; c.beginPath(); c.ellipse(s * 0.08, s * 0.1, s * 0.6, s * 0.45, 0, 0, TAU); c.fill(); c.fillStyle = hi; c.beginPath(); c.ellipse(0, 0, s * 0.55, s * 0.4, 0, 0, TAU); c.fill(); c.beginPath(); c.arc(s * 0.5, -s * 0.15, s * 0.3, 0, TAU); c.fill(); c.strokeStyle = hi; c.lineWidth = s * 0.16; c.beginPath(); c.moveTo(s * 0.7, -s * 0.1); c.quadraticCurveTo(s * 0.9, s * 0.3, s * 0.75, s * 0.55); c.stroke(); }
    else { for (var k = 0; k < 6; k++) { var px = Math.cos(k / 6 * TAU) * s * 0.42, py = Math.sin(k / 6 * TAU) * s * 0.42; c.fillStyle = 'rgba(40,46,60,.4)'; c.beginPath(); c.arc(px + s * 0.06, py + s * 0.08, s * 0.2, 0, TAU); c.fill(); c.fillStyle = hi; c.beginPath(); c.arc(px, py, s * 0.18, 0, TAU); c.fill(); } }
    c.restore();
  }
}

/* ---------------------------------------------------------------- saa paper (กระดาษสา)
   a drying frame: a wooden frame, the sheet, petals pressed in; wet sheets grey, dry white */
function frame(c, x, y, w, ht, lean, r, wet, N) {
  var tx = lean * ht;
  c.save();
  solid(c, poly([[x, y], [x + w, y], [x + w + tx, y - ht], [x + tx, y - ht]]), N ? '#4a2e1c' : '#8a5a32', 1);
  c.fillStyle = mixc(N ? '#c8c4b8' : '#fbf7ec', N ? '#7a7a78' : '#c9c7c0', wet);
  var b = w * 0.07;
  c.beginPath(); c.moveTo(x + b, y - b); c.lineTo(x + w - b, y - b); c.lineTo(x + w - b + tx * 0.92, y - ht + b); c.lineTo(x + b + tx * 0.92, y - ht + b); c.closePath(); c.fill();
  var cols = ['#e5427f', '#f29a1f', '#ffd23a', '#4fae5a', '#c03a8a', '#ff7a5a'];
  for (var i = 0; i < 9; i++) { var u = 0.15 + r() * 0.7, v = 0.12 + r() * 0.76, px = x + u * w + v * tx, py = y - v * ht;
    c.fillStyle = cols[Math.floor(r() * cols.length)]; c.globalAlpha = 0.85 - wet * 0.3;
    for (var k = 0; k < 5; k++) { c.beginPath(); c.ellipse(px + Math.cos(k * 1.26) * w * 0.03, py + Math.sin(k * 1.26) * w * 0.03, w * 0.03, w * 0.017, k * 1.26, 0, TAU); c.fill(); }
    if (r() < 0.5) { c.fillStyle = '#3f8a4a'; c.beginPath(); c.ellipse(px + w * 0.06, py + w * 0.03, w * 0.04, w * 0.015, 0.6, 0, TAU); c.fill(); } }
  c.restore();
}
function umbrella(q, x, y, r, col, N) {
  solid(q, function (c) { c.beginPath(); c.moveTo(x - r, y); c.quadraticCurveTo(x, y - r * 0.9, x + r, y); c.closePath(); }, col, 1);
  q.strokeStyle = 'rgba(255,255,255,.5)'; q.lineWidth = 1; for (var i = 1; i < 6; i++) { q.beginPath(); q.moveTo(x, y - r * 0.45); q.lineTo(x - r + i * r / 3, y); q.stroke(); }
  q.fillStyle = '#fff4d6'; for (i = 0; i < 4; i++) { q.beginPath(); q.arc(x - r * 0.5 + i * r * 0.33, y - r * 0.15, r * 0.07, 0, TAU); q.fill(); }
  line(q, [[x, y - r * 0.45], [x + r * 0.15, y + r * 0.5]], N ? '#6a4426' : '#8a5a32', 2);
}
function saa(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var vx0 = S.x0 + S.span * 0.2, vw = h * 1.45, vtop = d - h * 0.5, vx1 = vx0 + vw, sx = vx0 + vw * 0.55;
  var rx0 = Math.max(vx1 + h * 1.5, S.x0 + S.span * 0.48), rx1 = S.x1 - h * 0.9;
  var water = N ? '#3a5470' : '#cfe3ea';
  layer(S, 'saa', d - h * 2.4, S.H, function (q) {
    floor(q, S, N ? '#2e2a20' : '#b08a5a');
    /* a bamboo fence behind */
    for (var x = S.x0; x < S.x1; x += h * 0.12) paper(q, rect(x, d - h * 0.95 + Math.sin(x) * 2, h * 0.09, h * 0.95), N ? '#3a3a24' : '#c9b27a', 0.4);
    paper(q, rect(S.x0, d - h * 0.8, S.span, h * 0.05), N ? '#2a2a18' : '#8a7a4a', 0.6);
    /* lanterns of saa paper on a line */
    var lx0 = S.x0 + S.span * 0.05, lx1 = vx1 + h * 0.8;
    q.strokeStyle = 'rgba(40,20,10,.7)'; q.lineWidth = 1; q.beginPath(); q.moveTo(lx0, d - h * 1.9); q.quadraticCurveTo((lx0 + lx1) / 2, d - h * 1.6, lx1, d - h * 1.9); q.stroke();
    /* drying frames in the sun, a row, petals pressed in */
    var r = rnd(S.seed + 3), fw = h * 0.62, n = Math.max(2, Math.floor((rx1 - rx0) / (fw * 1.08)));
    for (i = 0; i < n; i++) frame(q, rx0 + i * (rx1 - rx0 - fw) / Math.max(1, n - 1), d + h * 0.02, fw, h * 0.82, -0.25, r, i === 0 ? 0.6 : 0, N);
    /* umbrellas of the same paper, open, drying */
    umbrella(q, vx1 + h * 0.75, d + h * 0.05, h * 0.42, '#e5427f', N); umbrella(q, vx1 + h * 1.15, d + h * 0.12, h * 0.32, '#f29a1f', N);
    /* the bark beater's stone and the bundle of mulberry bark */
    solid(q, function (c2) { c2.beginPath(); c2.ellipse(vx0 - h * 0.05, d + h * 0.02, h * 0.22, h * 0.07, 0, 0, TAU); }, '#7a7a72', 1);
    for (i = 0; i < 5; i++) line(q, [[vx0 - h * 0.7 + i * 3, d + h * 0.06], [vx0 - h * 0.35 + i * 3, d - h * 0.1]], '#a8865a', 2);
    /* the vat's back wall */
    paper(q, rect(vx0, vtop, vw, h * 0.08), N ? '#5a5a5a' : '#bfbfb8', 1);
  });
  var lx0 = S.x0 + S.span * 0.05, lx1 = vx1 + h * 0.8;
  for (i = 0; i < 4; i++) { var u = (i + 0.5) / 4, lxx = lerp(lx0, lx1, u), lyy = d - h * 1.9 + Math.sin(u * Math.PI) * h * 0.22;
    if (N) glow(c, lxx, lyy + h * 0.16, h * 0.42, 38, 0.7 + 0.1 * Math.sin(t / 300 + i));
    solid(c, function (q) { q.beginPath(); q.ellipse(lxx, lyy + h * 0.16, h * 0.1, h * 0.13, 0, 0, TAU); }, N ? '#ffe2a0' : ['#fbf7ec', '#ffd1e8', '#fff2c8', '#d8f0d0'][i], 0.8);
    c.fillStyle = '#c03a2a'; c.fillRect(lxx - h * 0.05, lyy + h * 0.02, h * 0.1, h * 0.02); c.fillRect(lxx - h * 0.05, lyy + h * 0.28, h * 0.1, h * 0.02); }
  /* the papermaker: dip, lift, hold while it drains, shake to even it, down again (8 s) */
  var T = 8000, p = (t % T) / T, lift = ease(seg(p, 0.15, 0.4)) - ease(seg(p, 0.82, 0.97)), shake = p > 0.45 && p < 0.6 ? Math.sin(t / 60) * h * 0.02 : 0;
  var fy = lerp(vtop + h * 0.12, d - h * 0.78, lift), fw2 = h * 0.8, fxc = sx + shake, crew = K.town(S, 2, { sin: 0.5, casual: 0.5 });
  fig(S, crew[0], sx + h * 0.05, d - h * 0.02, h, { lean: 0.45 - lift * 0.35, legs: [0.05, 0, -0.05, 0], arms: [0.5, 0.5, 0.4, 0.5] }, -1, [fxc - fw2 * 0.45, fy], [fxc + fw2 * 0.4, fy]);
  /* the water, in front of her legs */
  c.fillStyle = water; c.fillRect(vx0 + 3, vtop + h * 0.06, vw - 6, h * 0.12);
  c.fillStyle = N ? 'rgba(220,230,240,.35)' : 'rgba(255,255,255,.75)'; for (i = 0; i < 6; i++) { c.beginPath(); c.ellipse(vx0 + vw * (0.12 + i * 0.15), vtop + h * 0.11, h * 0.07, h * 0.02, 0, 0, TAU); c.fill(); }
  if (p > 0.15 && p < 0.42) { var ru = seg(p, 0.15, 0.42); c.strokeStyle = 'rgba(255,255,255,' + (0.7 * (1 - ru)) + ')'; c.lineWidth = 1; c.beginPath(); c.ellipse(fxc, vtop + h * 0.12, fw2 * (0.5 + ru * 0.4), h * 0.03 * (1 + ru), 0, 0, TAU); c.stroke(); }
  /* the frame, a sheet of pulp on its screen, seen from above */
  if (lift > 0.05) {
    var tilt = h * 0.12;
    solid(c, poly([[fxc - fw2 / 2, fy], [fxc + fw2 / 2, fy], [fxc + fw2 / 2 - h * 0.08, fy - tilt], [fxc - fw2 / 2 + h * 0.08, fy - tilt]]), N ? '#4a2e1c' : '#8a5a32', 1);
    c.fillStyle = N ? '#c8c4b8' : '#f4f1e6'; c.beginPath(); c.moveTo(fxc - fw2 / 2 + 4, fy - 2); c.lineTo(fxc + fw2 / 2 - 4, fy - 2); c.lineTo(fxc + fw2 / 2 - h * 0.08 - 3, fy - tilt + 3); c.lineTo(fxc - fw2 / 2 + h * 0.08 + 3, fy - tilt + 3); c.closePath(); c.fill();
    var pr = rnd(11); c.globalAlpha = 0.9; for (i = 0; i < 7; i++) { c.fillStyle = ['#e5427f', '#f29a1f', '#ffd23a'][i % 3]; c.beginPath(); c.arc(fxc - fw2 * 0.38 + pr() * fw2 * 0.76, fy - tilt * (0.2 + pr() * 0.6), h * 0.022, 0, TAU); c.fill(); } c.globalAlpha = 1;
    /* drips: y = y₀ + ½gt², each on its own clock */
    for (i = 0; i < 7; i++) { var du = ((t / 520) + i * 0.37) % 1, dx = fxc - fw2 * 0.45 + ((i * 0.618) % 1) * fw2 * 0.9, dy = fy + du * du * (vtop + h * 0.08 - fy);
      if (dy < vtop + h * 0.08 && lift > 0.3) { c.fillStyle = N ? 'rgba(180,210,240,.8)' : 'rgba(120,170,210,.85)'; c.beginPath(); c.ellipse(dx, dy, 1.3, 2.4, 0, 0, TAU); c.fill(); } }
  }
  /* the vat's front wall */
  paper(c, rect(vx0, vtop + h * 0.16, vw, d - vtop - h * 0.14), N ? '#6a6a66' : '#d8d6cc', 1.2);
  c.fillStyle = 'rgba(0,0,0,.12)'; c.fillRect(vx0, vtop + h * 0.16, vw, 3);
  /* the bark beater, mallet on |sin|, the bark spreading */
  var bt = Math.abs(Math.sin(Math.PI * t / 480)), bxp = vx0 - h * 0.05;
  var m2 = fig(S, crew[1], bxp - h * 0.4, d + h * 0.04, h * 0.95, SIT, 1, [bxp - h * 0.02, d - h * 0.06 - bt * h * 0.28], [bxp - h * 0.12, d - h * 0.02]);
  c.save(); c.translate(m2.hand[0][0], m2.hand[0][1]); c.rotate(0.3 - bt * 0.6); solid(c, rect(-h * 0.02, -h * 0.02, h * 0.18, h * 0.07), N ? '#5a3a20' : '#8a5a32', 0.6); c.restore();
  c.fillStyle = N ? '#a8a090' : '#efe6cf'; c.beginPath(); c.ellipse(bxp + h * 0.05, d - h * 0.04, h * (0.1 + 0.02 * (1 - bt)), h * 0.025, 0, 0, TAU); c.fill();
  label(S, (rx0 + rx1) / 2, d - h * 1.75, '#e5427f');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: d - h * 2.1, y1: S.H });
}

/* ---------------------------------------------------------------- celadon (ศิลาดล)
   jade green with crackle; a vase, a bowl, a jar */
var JADE = '#8fbf9f', JADE2 = '#5f9a7a';
function jade(q, kind, x, y, s, col) {
  col = col || JADE;
  var g = q.createLinearGradient(x - s * 0.5, 0, x + s * 0.5, 0); g.addColorStop(0, JADE2); g.addColorStop(0.4, col); g.addColorStop(1, JADE2);
  var path = kind === 'vase' ? function (c) { c.beginPath(); c.moveTo(x - s * 0.12, y - s); c.quadraticCurveTo(x - s * 0.1, y - s * 0.72, x - s * 0.34, y - s * 0.45); c.quadraticCurveTo(x - s * 0.42, y - s * 0.1, x - s * 0.18, y); c.lineTo(x + s * 0.18, y); c.quadraticCurveTo(x + s * 0.42, y - s * 0.1, x + s * 0.34, y - s * 0.45); c.quadraticCurveTo(x + s * 0.1, y - s * 0.72, x + s * 0.12, y - s); c.closePath(); }
    : kind === 'bowl' ? function (c) { c.beginPath(); c.moveTo(x - s * 0.6, y - s * 0.5); c.quadraticCurveTo(x - s * 0.55, y - s * 0.05, x - s * 0.2, y); c.lineTo(x + s * 0.2, y); c.quadraticCurveTo(x + s * 0.55, y - s * 0.05, x + s * 0.6, y - s * 0.5); c.closePath(); }
    : function (c) { c.beginPath(); c.moveTo(x - s * 0.2, y - s * 0.8); c.lineTo(x - s * 0.22, y - s * 0.72); c.quadraticCurveTo(x - s * 0.55, y - s * 0.55, x - s * 0.42, y - s * 0.12); c.lineTo(x - s * 0.25, y); c.lineTo(x + s * 0.25, y); c.lineTo(x + s * 0.42, y - s * 0.12); c.quadraticCurveTo(x + s * 0.55, y - s * 0.55, x + s * 0.22, y - s * 0.72); c.lineTo(x + s * 0.2, y - s * 0.8); c.closePath(); };
  solid(q, path, g, 1);
  q.save(); path(q); q.clip(); crackle(q, x, y - s * 0.45, s * 0.6, 1, 13);
  q.fillStyle = 'rgba(255,255,255,.35)'; q.beginPath(); q.ellipse(x - s * 0.15, y - s * 0.5, s * 0.05, s * 0.2, 0.2, 0, TAU); q.fill(); q.restore();
}
/* crackle: a net of short broken lines, as the glaze shrinks off the clay */
function crackle(c, x, y, s, a, seed) {
  var r = rnd(seed); c.strokeStyle = 'rgba(40,70,55,' + (0.5 * a) + ')'; c.lineWidth = 0.7; c.beginPath();
  for (var i = 0; i < 14; i++) { var px = x + (r() - 0.5) * s * 2, py = y + (r() - 0.5) * s * 2; c.moveTo(px, py); for (var k = 0; k < 3; k++) { px += (r() - 0.5) * s * 0.5; py += (r() - 0.5) * s * 0.5; c.lineTo(px, py); } }
  c.stroke();
}
function celadon(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var w = Math.min(S.span * 0.4, h * 3.2), a0 = S.x0 + S.span * 0.04, a1 = a0 + w, top = d - h * 1.95;
  var kx = Math.max(a1 + h * 1.0, S.x0 + S.span * 0.6), kw = h * 1.5, kh = h * 1.15, mouth = [kx, d - h * 0.28];
  var wx = a0 + w * 0.55, wy = d - h * 0.42, slab = [kx - kw * 0.5 - h * 0.55, d - h * 0.3];
  layer(S, 'celadon', d - h * 2.5, S.H, function (q) {
    floor(q, S, N ? '#2e2620' : '#a8845a');
    wall(q, a0 + w * 0.05, a1 - w * 0.05, d - h * 1.2, d, N);
    K.sala(q, a0, a1, d, top, N, N ? '#3a2a20' : '#8a4a2a');
    /* the shelf of jade pieces, under the eave */
    var sy = d - h * 0.98; shelf(q, a0 + w * 0.08, a0 + w * 0.42, sy, N);
    jade(q, 'vase', a0 + w * 0.16, sy, h * 0.42); jade(q, 'bowl', a0 + w * 0.28, sy, h * 0.22); jade(q, 'jar', a0 + w * 0.37, sy, h * 0.3);
    /* the kiln: a brick dome, a chimney behind it */
    var bx = kx + kw * 0.3;
    paper(q, rect(bx - h * 0.13, d - h * 1.95, h * 0.26, h * 1.4), N ? '#5a2a1e' : '#a8492f', 1.2);
    paper(q, function (c2) { c2.beginPath(); c2.moveTo(kx - kw / 2, d); c2.lineTo(kx - kw / 2, d - kh * 0.4); c2.quadraticCurveTo(kx - kw / 2, d - kh, kx, d - kh); c2.quadraticCurveTo(kx + kw / 2, d - kh, kx + kw / 2, d - kh * 0.4); c2.lineTo(kx + kw / 2, d); c2.closePath(); }, N ? '#6a3024' : '#b85a3a', 1.4);
    q.strokeStyle = 'rgba(60,20,10,.35)'; q.lineWidth = 1;
    for (var row = 1; row < 7; row++) { var yy = d - row * kh / 7, half = kw / 2 * Math.sqrt(Math.max(0, 1 - Math.pow(Math.max(0, (row / 7 - 0.4) / 0.6), 2))); q.beginPath(); q.moveTo(kx - half, yy); q.lineTo(kx + half, yy); q.stroke();
      for (var bk = -3; bk <= 3; bk++) { var xx = kx + (bk + (row % 2) * 0.5) * kw / 7; if (Math.abs(xx - kx) < half) { q.beginPath(); q.moveTo(xx, yy); q.lineTo(xx, yy + kh / 7); q.stroke(); } } }
    q.fillStyle = '#1a0a06'; q.beginPath(); q.moveTo(kx - h * 0.25, d); q.lineTo(kx - h * 0.25, d - h * 0.32); q.arc(kx, d - h * 0.32, h * 0.25, Math.PI, TAU); q.lineTo(kx + h * 0.25, d); q.closePath(); q.fill();
    /* the cooling slab, the wheel's stool, a crock of glaze */
    paper(q, rect(slab[0] - h * 0.28, slab[1], h * 0.56, h * 0.3), N ? '#4a4a4a' : '#9a968a', 1);
    if (kx + kw / 2 + h * 1.1 < S.x1) { var tx = kx + kw / 2 + h * 0.55; paper(q, rect(tx - h * 0.4, d - h * 0.42, h * 0.8, h * 0.42), N ? '#3a2416' : '#6a4426', 1); jade(q, 'vase', tx - h * 0.2, d - h * 0.42, h * 0.5); jade(q, 'bowl', tx + h * 0.18, d - h * 0.42, h * 0.26); }
    paper(q, rect(wx - h * 0.08, wy + h * 0.06, h * 0.16, d - wy - h * 0.06), N ? '#3a2416' : '#5a3a20', 1);
    pot(q, a1 - w * 0.12, d + h * 0.04, h * 0.22, N ? '#9aa89a' : '#d8ddd2', '#7a8a7a');
  });
  /* the kiln's fire through the mouth, and its smoke */
  var fl = 0.75 + 0.25 * Math.sin(t / 110) * Math.sin(t / 270 + 1);
  glow(c, mouth[0], mouth[1], h * (N ? 0.75 : 0.5), 25, 0.85 * fl);
  for (i = 0; i < 5; i++) { var fh = h * (0.12 + 0.1 * Math.abs(Math.sin(t / 160 + i * 1.7))); c.fillStyle = i % 2 ? '#ff7a2a' : '#ffc94a'; c.beginPath(); c.moveTo(mouth[0] - h * 0.18 + i * h * 0.09, d); c.quadraticCurveTo(mouth[0] - h * 0.2 + i * h * 0.09, d - fh * 0.6, mouth[0] - h * 0.14 + i * h * 0.09 + Math.sin(t / 200 + i) * 2, d - fh); c.quadraticCurveTo(mouth[0] - h * 0.1 + i * h * 0.09, d - fh * 0.4, mouth[0] - h * 0.1 + i * h * 0.09, d); c.fill(); }
  var chx = kx + kw * 0.3, chy = d - h * 1.95;
  for (i = 0; i < 5; i++) { var su = (t / 3200 + i / 5) % 1; c.fillStyle = 'rgba(' + (N ? '150,140,150' : '235,230,225') + ',' + (0.5 * Math.sin(Math.PI * su)).toFixed(3) + ')'; c.beginPath(); c.arc(chx - su * h * 0.9 + Math.sin(su * 6 + i) * h * 0.05, chy - su * h * 0.5, h * (0.07 + su * 0.16), 0, TAU); c.fill(); }
  /* the wheel: the pot rises, r(y) = r₀(0.55 + 0.6·sin πf + 0.16·sin(kπf + φ)), lines turn on it */
  var crew = K.town(S, 2, { casual: 0.5, mohom: 0.5 }), grow = 0.35 + 0.65 * ease(((t % 12000) / 12000) * 1.3), ph = h * 0.55 * grow, r0 = h * 0.12, kk = 2 + S.r() * 2;
  function rad(f) { return r0 * (0.55 + 0.6 * Math.sin(Math.PI * Math.min(1, f * 1.05)) + 0.16 * Math.sin(kk * Math.PI * f + 1)) + (f > 0.9 ? r0 * (f - 0.9) * 4 : 0); }
  solid(c, function (q) { q.beginPath(); q.ellipse(wx, wy + h * 0.04, h * 0.3, h * 0.06, 0, 0, TAU); }, N ? '#5a5a5a' : '#8a8478', 1);
  c.strokeStyle = 'rgba(0,0,0,.35)'; c.lineWidth = 1.2; for (i = 0; i < 3; i++) { var aa = t / 140 + i * 2.1; c.beginPath(); c.moveTo(wx + Math.cos(aa) * h * 0.26, wy + h * 0.04 + Math.sin(aa) * h * 0.05); c.lineTo(wx + Math.cos(aa) * h * 0.14, wy + h * 0.04 + Math.sin(aa) * h * 0.03); c.stroke(); }
  var clay = N ? '#8a8070' : '#b8ab96';
  solid(c, function (q) { q.beginPath(); var f; for (f = 0; f <= 1; f += 0.05) q.lineTo(wx + rad(f), wy - f * ph); for (f = 1; f >= 0; f -= 0.05) q.lineTo(wx - rad(f), wy - f * ph); q.closePath(); }, clay, 1);
  c.strokeStyle = 'rgba(70,50,30,.35)'; c.lineWidth = 1;
  for (i = 0; i < 4; i++) { var a3 = (t / 300 + i * TAU / 4) % TAU; if (Math.sin(a3) < 0) continue; c.beginPath(); for (var f2 = 0; f2 <= 1; f2 += 0.1) { var xx2 = wx + rad(f2) * Math.cos(a3); f2 ? c.lineTo(xx2, wy - f2 * ph) : c.moveTo(xx2, wy - f2 * ph); } c.stroke(); }
  fig(S, crew[0], wx - h * 0.5, d, h, STOOL, 1, [wx - rad(0.5) - 1, wy - ph * 0.5], [wx - rad(0.8) + 2, wy - ph * 0.85]);
  /* the pot from the kiln: out on the tongs, onto the slab, hot to jade, c = 1 − e^(−t/τ) */
  var T = 10000, p = (t % T) / T, out = ease(seg(p, 0.02, 0.2)), cool = 1 - Math.exp(-Math.max(0, p - 0.2) * T / 1800);
  var px = lerp(mouth[0], slab[0], out), py = lerp(mouth[1] + h * 0.1, slab[1], out), hot = cool < 0.5 ? mixc('#ffd27a', '#e0542a', cool * 2) : mixc('#e0542a', JADE, (cool - 0.5) * 2);
  if (cool < 0.7) glow(c, px, py - h * 0.18, h * 0.45, 25, 0.8 * (1 - cool / 0.7));
  jade(c, 'jar', px, py, h * 0.4, cool > 0.85 ? JADE : hot.replace('rgb', 'rgb'));
  if (cool > 0.6) { c.save(); c.globalAlpha = seg(cool, 0.6, 0.95); crackle(c, px, py - h * 0.18, h * 0.14, 1, 5); c.restore(); }
  if (cool > 0.75 && cool < 0.97) { var tk = (t / 260) % 1; star(c, px + Math.sin(t / 97) * h * 0.1, py - h * 0.2 + Math.cos(t / 131) * h * 0.08, h * 0.04 * (1 - tk), '#fff8d0'); }
  var kwkr = crew[1], tongsOn = p < 0.24, hand = tongsOn ? [px - h * 0.42, py - h * 0.3] : [slab[0] - h * 0.35, d - h * 0.5];
  fig(S, kwkr, slab[0] - h * 0.6 - (tongsOn ? (1 - out) * h * 0.25 : 0), d, h, STAND, 1, hand, [hand[0] - h * 0.05, hand[1] + h * 0.02]);
  if (tongsOn) { line(c, [hand, [px - h * 0.06, py - h * 0.32]], '#3a3a3a', 2); line(c, [[hand[0], hand[1] + 2], [px - h * 0.1, py - h * 0.22]], '#3a3a3a', 2); }
  label(S, (a0 + a1) / 2, top + h * 0.2, '#5f9a7a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* ---------------------------------------------------------------- weaving (ทอผ้า)
   the cloth, cut once: a tin jok diamond lattice, |col mod 8 − 4| + |row mod 8 − 4| < 3 */
function clothSprite(S, w, ht, rows) {
  return sprite(S, 'cloth', w, ht, function (q) {
    var cols = 24, cw = w / cols, rh = ht / rows, pal = ['#7a1f3a', '#e8b84a', '#2f8f5b', '#f2e6c9'];
    for (var r = 0; r < rows; r++) for (var k = 0; k < cols; k++) {
      var rr = rows - 1 - r, dmd = Math.abs((k % 8) - 4) + Math.abs((rr % 8) - 4), band = Math.floor(rr / 8) % 2;
      q.fillStyle = dmd < 2 ? pal[3] : dmd < 3 ? pal[1 + band] : rr % 8 === 0 ? pal[1] : pal[0];
      q.fillRect(k * cw, r * rh, cw + 0.5, rh + 0.5);
    }
  });
}
function loom(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var w = Math.min(S.span * 0.68, h * 5.8), a0 = S.x0 + S.span * 0.05, a1 = a0 + w, top = d - h * 2.05;
  var lx = a0 + w * 0.4, LW = h * 1.45, lt = d - h * 1.62, breast = d - h * 0.52, heddle = d - h * 1.2, x0 = lx - LW / 2, x1 = lx + LW / 2;
  var wood2 = N ? '#4a2e1c' : '#7a4a2a';
  layer(S, 'loom', top - h * 0.7, S.H, function (q) {
    floor(q, S, N ? '#3a2416' : '#8a5a32', true);
    wall(q, a0 + w * 0.05, a1 - w * 0.05, d - h * 1.3, d, N);
    K.sala(q, a0, a1, d, top, N, N ? '#2e3a5a' : '#3a5a8a');
    /* skeins of silk on a bamboo pole */
    var px0 = a0 + w * 0.08, px1 = x0 - h * 0.3; line(q, [[px0, d - h * 1.18], [px1, d - h * 1.18]], N ? '#8a7a4a' : '#c9b27a', 3);
    var sk = ['#d9342b', '#e8b84a', '#2f8f5b', '#9b6bd6', '#f08a5d', '#4d8fd1'];
    for (i = 0; px0 + (i + 0.6) * h * 0.18 < px1; i++) { var sx = px0 + (i + 0.5) * h * 0.18; solid(q, function (c2) { c2.beginPath(); c2.ellipse(sx, d - h * 0.98, h * 0.06, h * 0.22, 0, 0, TAU); }, sk[i % sk.length], 0.6); }
  });
  khom(c, a1 - w * 0.12, top + h * 0.5, h * 0.22, N, t, 3);
  /* the weaver, behind the warp: head, shoulders, a flower in her bun */
  var T = 16000, p = (t % T) / T, rows = 40, ch = h * 0.5 * (0.1 + 0.9 * p), fell = breast - ch, pick = Math.floor(t / 1400), pu = (t % 1400) / 1400, dirp = pick % 2 ? -1 : 1;
  var shx = lerp(x0 - h * 0.05, x1 + h * 0.05, dirp > 0 ? ease(seg(pu, 0.05, 0.65)) : 1 - ease(seg(pu, 0.05, 0.65))), beat = Math.pow(Math.max(0, Math.sin(Math.PI * seg(pu, 0.7, 1))), 2);
  var crew = K.town(S, 2, { sin: 1 }), skin = crew[0].skin, wy = fell - h * 0.25, sabai = crew[0].sabai || '#e8b84a';
  solid(c, function (q) { q.beginPath(); q.moveTo(lx - h * 0.2, d - h * 0.5); q.lineTo(lx - h * 0.17, wy + h * 0.06); q.quadraticCurveTo(lx, wy - h * 0.02, lx + h * 0.17, wy + h * 0.06); q.lineTo(lx + h * 0.2, d - h * 0.5); q.closePath(); }, crew[0].low, 1);
  c.fillStyle = sabai; c.beginPath(); c.moveTo(lx - h * 0.17, wy + h * 0.06); c.lineTo(lx + h * 0.05, wy + h * 0.02); c.lineTo(lx + h * 0.2, d - h * 0.62); c.lineTo(lx + h * 0.1, d - h * 0.6); c.closePath(); c.fill();
  c.fillStyle = skin; c.beginPath(); c.arc(lx, wy - h * 0.06, h * 0.1, 0, TAU); c.fill();
  c.fillStyle = '#1c1410'; c.beginPath(); c.arc(lx, wy - h * 0.09, h * 0.1, Math.PI, TAU); c.fill(); c.beginPath(); c.arc(lx, wy - h * 0.2, h * 0.06, 0, TAU); c.fill();
  c.fillStyle = '#ffd84a'; c.beginPath(); c.arc(lx + h * 0.06, wy - h * 0.22, h * 0.03, 0, TAU); c.fill();
  c.fillStyle = '#2a1a12'; c.fillRect(lx - h * 0.04, wy - h * 0.06, 1.6, 1.6); c.fillRect(lx + h * 0.03, wy - h * 0.06, 1.6, 1.6);
  /* hands: one at the shuttle near its edge, the other on the beater */
  var near = dirp > 0 ? (pu < 0.3 ? 'L' : pu > 0.55 ? 'R' : '') : (pu < 0.3 ? 'R' : pu > 0.55 ? 'L' : '');
  var by = fell - h * 0.06 - h * 0.28 * (1 - beat), hL = near === 'L' ? [shx, fell - h * 0.07] : [lx - LW * 0.32, by], hR = near === 'R' ? [shx, fell - h * 0.07] : [lx + LW * 0.32, by];
  line(c, [[lx - h * 0.15, wy + h * 0.08], [lerp(lx - h * 0.15, hL[0], 0.5) - h * 0.06, (wy + hL[1]) / 2 + h * 0.06], hL], skin, Math.max(2, h * 0.06));
  line(c, [[lx + h * 0.15, wy + h * 0.08], [lerp(lx + h * 0.15, hR[0], 0.5) + h * 0.06, (wy + hR[1]) / 2 + h * 0.06], hR], skin, Math.max(2, h * 0.06));
  /* the frame: posts, top beam, heddle bars rising and falling in turn */
  [x0 - h * 0.08, x1 + h * 0.02].forEach(function (x) { paper(c, rect(x, lt - h * 0.06, h * 0.07, d - lt + h * 0.06), wood2, 1.2); });
  paper(c, rect(x0 - h * 0.12, lt - h * 0.08, LW + h * 0.24, h * 0.07), wood2, 1.2);
  var open = h * 0.05 * (pick % 2 ? 1 : -1) * ease(seg(pu, 0, 0.12) * 1);
  /* the warp: each thread from the fell up through its heddle to the beam; odd ones lifted */
  for (i = 0; i <= 24; i++) { var x = x0 + i / 24 * LW, o = i % 2 ? open : -open;
    c.strokeStyle = N ? 'rgba(240,230,210,.55)' : 'rgba(255,250,236,.85)'; c.lineWidth = 0.9; c.beginPath(); c.moveTo(x, fell); c.lineTo(x, heddle + o); c.lineTo(x, lt); c.stroke(); }
  paper(c, rect(x0 - h * 0.05, heddle + open - h * 0.025, LW + h * 0.1, h * 0.035), N ? '#6a4426' : '#a8693a', 0.6);
  paper(c, rect(x0 - h * 0.05, heddle - open - h * 0.09, LW + h * 0.1, h * 0.035), N ? '#6a4426' : '#a8693a', 0.6);
  /* the cloth so far, from the cut-once sprite, the newest rows at the fell */
  var cs = clothSprite(S, LW, h * 0.5, rows);
  if (cs) { var m = mat(c), k2 = m ? m.a : 1; c.drawImage(cs, 0, cs.height * (1 - ch / (h * 0.5)), cs.width, cs.height * ch / (h * 0.5), x0, fell, LW, ch); }
  c.strokeStyle = 'rgba(0,0,0,.25)'; c.strokeRect(x0, fell, LW, ch);
  /* the weft from the shuttle back to the side it left */
  line(c, [[dirp > 0 ? x0 : x1, fell - h * 0.03], [shx, fell - h * 0.04]], '#e8b84a', 1.4);
  solid(c, function (q) { q.beginPath(); q.moveTo(shx - h * 0.13, fell - h * 0.04); q.quadraticCurveTo(shx, fell - h * 0.09, shx + h * 0.13, fell - h * 0.04); q.quadraticCurveTo(shx, fell + h * 0.01, shx - h * 0.13, fell - h * 0.04); q.closePath(); }, N ? '#8a5a32' : '#c98b4e', 0.8);
  paper(c, rect(x0 - h * 0.06, by - h * 0.02, LW + h * 0.12, h * 0.04), wood2, 1);
  paper(c, rect(x0 - h * 0.12, breast, LW + h * 0.24, h * 0.07), wood2, 1.2);
  /* her bench in front, the finished sin on a line */
  paper(c, rect(lx - h * 0.45, d - h * 0.28, h * 0.9, h * 0.06), wood2, 1);
  var hx0 = x1 + h * 0.55, hx1 = Math.min(a1 - w * 0.06, hx0 + h * 1.5);
  if (hx1 - hx0 > h * 0.6) {
    line(c, [[hx0, d - h * 1.3], [hx1, d - h * 1.3]], N ? '#8a7a4a' : '#c9b27a', 2);
    var sw = Math.sin(t / 1300) * h * 0.02, cl = hx1 - hx0 - h * 0.2;
    if (cs) c.drawImage(cs, 0, 0, cs.width, cs.height * 0.5, hx0 + h * 0.1 + sw, d - h * 1.28, cl, h * 0.75);
    c.fillStyle = '#7a1f3a'; c.fillRect(hx0 + h * 0.1 + sw, d - h * 0.53, cl, h * 0.1);
    c.fillStyle = '#e8b84a'; for (i = 0; i < 8; i++) { c.beginPath(); c.moveTo(hx0 + h * 0.1 + sw + i * cl / 8, d - h * 0.43); c.lineTo(hx0 + h * 0.1 + sw + (i + 0.5) * cl / 8, d - h * 0.5); c.lineTo(hx0 + h * 0.1 + sw + (i + 1) * cl / 8, d - h * 0.43); c.fill(); }
    /* the bobbin winder: a wheel of spokes turning, thread to the bobbin */
    var wx2 = hx0 + h * 0.55, wy2 = d - h * 0.34, wr = h * 0.25, aa = t / 300;
    fig(S, crew[1], wx2 + h * 0.55, d, h * 0.95, SIT, -1, [wx2 + Math.cos(aa) * wr * 0.7, wy2 + Math.sin(aa) * wr * 0.7], null);
    c.strokeStyle = wood2; c.lineWidth = 1.4; c.beginPath(); c.arc(wx2, wy2, wr, 0, TAU); c.stroke();
    for (i = 0; i < 8; i++) { c.beginPath(); c.moveTo(wx2, wy2); c.lineTo(wx2 + Math.cos(aa + i * TAU / 8) * wr, wy2 + Math.sin(aa + i * TAU / 8) * wr); c.stroke(); }
    line(c, [[wx2, wy2], [wx2, d]], wood2, 2); line(c, [[wx2, wy2 - wr], [wx2 - h * 0.45, d - h * 0.2]], '#e8b84a', 1);
  }
  label(S, (a0 + a1) / 2, top + h * 0.2, '#3a5a8a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* ---------------------------------------------------------------- the Khao Phansa candle
   a beeswax pillar, bands carved from the top down: kranok flames, then lotus petals */
function candleBody(c, cx, y0, y1, cw, N) {
  var g = c.createLinearGradient(cx - cw / 2, 0, cx + cw / 2, 0); g.addColorStop(0, N ? '#a8701e' : '#c98a24'); g.addColorStop(0.4, N ? '#e8b84a' : '#ffd36a'); g.addColorStop(1, N ? '#8a5a18' : '#b87a1e');
  solid(c, rect(cx - cw / 2, y0, cw, y1 - y0), g, 1.2);
}
function candleBand(c, cx, y, bh, cw, k, N) {
  var dk = N ? 'rgba(90,50,10,.75)' : 'rgba(140,80,10,.7)', hi = 'rgba(255,240,180,.8)', i;
  c.fillStyle = 'rgba(120,70,10,.18)'; c.fillRect(cx - cw / 2, y, cw, bh);
  if (k % 3 === 2) {   /* lotus petals */
    for (i = 0; i < 5; i++) { var px = cx - cw / 2 + (i + 0.5) * cw / 5; c.fillStyle = dk; c.beginPath(); c.moveTo(px - cw * 0.09, y + bh * 0.9); c.quadraticCurveTo(px - cw * 0.1, y + bh * 0.3, px, y + bh * 0.1); c.quadraticCurveTo(px + cw * 0.1, y + bh * 0.3, px + cw * 0.09, y + bh * 0.9); c.fill();
      c.strokeStyle = hi; c.lineWidth = 0.8; c.beginPath(); c.moveTo(px, y + bh * 0.2); c.lineTo(px, y + bh * 0.8); c.stroke(); }
  } else { for (i = 0; i < 3; i++) kranok(c, cx - cw / 2 + (i + 0.3) * cw / 3, y + bh * 0.8, bh * 0.55, (i + k) % 2 ? 1 : -1, dk); }
  c.strokeStyle = hi; c.lineWidth = 1; c.beginPath(); c.moveTo(cx - cw / 2, y + 0.5); c.lineTo(cx + cw / 2, y + 0.5); c.stroke();
}
function candle(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var cx = S.x0 + S.span * 0.38, cw = h * 0.5, pt = d - h * 0.36, ctop = d - h * 2.15, nb = 6, bh = (pt - ctop) / nb;
  var fx = Math.min(S.x1 - h * 1.3, S.x0 + S.span * 0.78), w = Math.min(S.span * 0.72, h * 6);
  layer(S, 'candle', d - h * 2.5, S.H, function (q) {
    floor(q, S, N ? '#3a3028' : '#b8a888');
    q.strokeStyle = 'rgba(0,0,0,.1)'; for (var x = S.x0; x < S.x1; x += h * 0.3) { q.beginPath(); q.moveTo(x, d); q.lineTo(x - h * 0.2, S.H); q.stroke(); }
    /* the carved pedestal, naga heads at its corners */
    paper(q, rect(cx - h * 0.5, pt, h * 1.0, d - pt), N ? '#6a2a1e' : '#a8432f', 1.2);
    q.fillStyle = '#e8b84a'; q.fillRect(cx - h * 0.5, pt, h * 1.0, h * 0.04); q.fillRect(cx - h * 0.5, d - h * 0.06, h * 1.0, h * 0.04);
    [-1, 1].forEach(function (sd) { naga(q, cx + sd * h * 0.5, pt + h * 0.02, h * 0.38, sd, N); });
    /* the finished candle on its float, flowers round its foot */
    var fpt = d - h * 0.42;
    paper(q, rect(fx - h * 0.62, fpt, h * 1.24, d - fpt), N ? '#2e4a3a' : '#3f7a5a', 1.2);
    for (i = 0; i < 10; i++) { q.fillStyle = i % 2 ? '#f29a1f' : '#fff4d6'; q.beginPath(); q.arc(fx - h * 0.56 + i * h * 0.124, fpt + h * 0.02, h * 0.055, 0, TAU); q.fill(); }
    candleBody(q, fx, d - h * 1.85, fpt, h * 0.38, N);
    for (i = 0; i < 4; i++) candleBand(q, fx, d - h * 1.85 + i * (fpt - d + h * 1.85) / 4, (fpt - d + h * 1.85) / 4, h * 0.38, i, N);
    [-1, 1].forEach(function (sd) { naga(q, fx + sd * h * 0.62, fpt + h * 0.02, h * 0.34, sd, N); });
    /* the ladder */
    var lx = cx - h * 0.62;
    line(q, [[lx - h * 0.12, d], [lx - h * 0.02, d - h * 1.75]], N ? '#5a3a20' : '#8a5a32', 2.5); line(q, [[lx + h * 0.12, d], [lx + h * 0.2, d - h * 1.75]], N ? '#5a3a20' : '#8a5a32', 2.5);
    for (i = 1; i < 7; i++) { var ry = d - i * h * 0.25; line(q, [[lx - h * 0.12 + i * h * 0.014, ry], [lx + h * 0.12 + i * h * 0.014, ry]], N ? '#5a3a20' : '#8a5a32', 2); }
    /* wax strips on a low table */
    var tx = cx + h * 0.95; paper(q, rect(tx, d - h * 0.3, h * 0.8, h * 0.06), N ? '#4a2e1c' : '#7a4a2a', 1);
    for (i = 0; i < 4; i++) { q.fillStyle = N ? '#c99a3a' : '#f2c25a'; q.fillRect(tx + h * 0.05 + i * h * 0.18, d - h * 0.34, h * 0.14, h * 0.04); }
  });
  /* a band takes T/7: carved left to right, then the carver steps down a rung */
  var T = 15000, p = (t % T) / T, nowB = Math.min(nb - 1, Math.floor(p * 7)), bu = p * 7 - Math.floor(p * 7), finished = p * 7 >= nb;
  candleBody(c, cx, ctop, pt, cw, N);
  for (i = 0; i < nb; i++) {
    var by = ctop + i * bh;
    if (i < nowB || finished) candleBand(c, cx, by, bh, cw, i, N);
    else if (i === nowB) { c.save(); c.beginPath(); c.rect(cx - cw / 2, by, cw * ease(bu * 1.15), bh); c.clip(); candleBand(c, cx, by, bh, cw, i, N); c.restore(); }
  }
  /* the wick; lit when the work is done */
  line(c, [[cx, ctop], [cx, ctop - h * 0.06]], '#3a2a1a', 1.5);
  if (finished || N) { var fl = 1 + 0.12 * Math.sin(t / 90); glow(c, cx, ctop - h * 0.14, h * 0.32, 40, 0.8); c.fillStyle = '#ffc94a'; c.beginPath(); c.moveTo(cx, ctop - h * 0.24 * fl); c.quadraticCurveTo(cx + h * 0.05, ctop - h * 0.08, cx, ctop - h * 0.05); c.quadraticCurveTo(cx - h * 0.05, ctop - h * 0.08, cx, ctop - h * 0.24 * fl); c.fill(); }
  glow(c, fx, d - h * 1.95, h * 0.3, 40, N ? 0.8 : 0.5); c.fillStyle = '#ffc94a'; c.beginPath(); c.moveTo(fx, d - h * 2.08 - Math.sin(t / 80) * 1.5); c.quadraticCurveTo(fx + h * 0.045, d - h * 1.94, fx, d - h * 1.9); c.quadraticCurveTo(fx - h * 0.045, d - h * 1.94, fx, d - h * 2.08); c.fill();
  /* the carver on the ladder, the knife at the band; wax curls fall on spirals */
  var tb = ctop + (finished ? nb - 0.5 : nowB + 0.5) * bh, kx = cx - cw / 2 + cw * (finished ? 0.2 : ease(bu * 1.15)) * 0.95, ky = tb + Math.sin(t / 160) * bh * 0.15;
  var footY = Math.min(d, Math.round((tb + h * 0.55 - d) / (h * 0.25)) * h * 0.25 + d), lx = cx - h * 0.62 + (d - footY) / (h * 1.75) * h * 0.08;
  var crew = K.town(S, 1, { mohom: 0.5, casual: 0.5 }), me = fig(S, crew[0], lx - h * 0.02, footY, h, STAND, 1, [Math.min(kx, cx - cw * 0.3), ky], [cx - cw / 2 - 1, ky + h * 0.08]);
  if (!finished) {
    line(c, [me.hand[0], [kx, ky]], '#cfd5de', 1.6);
    for (i = 0; i < 5; i++) { var cu = ((t / 1600) + i / 5) % 1, x2 = kx + Math.sin(cu * 9 + i) * h * 0.08 * cu, y2 = ky + cu * (d - ky);
      c.strokeStyle = N ? '#e8b84a' : '#ffd36a'; c.lineWidth = 1.4; c.beginPath(); for (var a = 0; a < 7; a += 0.6) { var rr = h * 0.03 * (1 - a / 9); a ? c.lineTo(x2 + Math.cos(a + cu * 12) * rr, y2 + Math.sin(a + cu * 12) * rr) : c.moveTo(x2 + rr, y2); } c.stroke(); }
  }
  label(S, S.x0 + S.span * 0.62, d - h * 1.75, '#c98a24');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: ctop, y1: S.H });
}
/* a naga's head rising from a corner: the neck an S, the crest a flame */
function naga(q, x, y, s, dir, N) {
  var g = N ? '#b8872f' : '#e8b84a';
  q.save(); q.strokeStyle = g; q.lineCap = 'round'; q.lineWidth = s * 0.16;
  q.beginPath(); q.moveTo(x, y + s * 0.3); q.quadraticCurveTo(x + dir * s * 0.35, y + s * 0.1, x + dir * s * 0.15, y - s * 0.3); q.quadraticCurveTo(x, y - s * 0.6, x + dir * s * 0.3, y - s * 0.75); q.stroke();
  q.fillStyle = g; q.beginPath(); q.ellipse(x + dir * s * 0.38, y - s * 0.78, s * 0.16, s * 0.1, dir * 0.3, 0, TAU); q.fill();
  q.beginPath(); q.moveTo(x + dir * s * 0.25, y - s * 0.85); q.quadraticCurveTo(x + dir * s * 0.1, y - s * 1.1, x - dir * s * 0.05, y - s * 1.05); q.quadraticCurveTo(x + dir * s * 0.12, y - s * 0.95, x + dir * s * 0.2, y - s * 0.75); q.fill();
  q.fillStyle = '#d9342b'; q.beginPath(); q.arc(x + dir * s * 0.42, y - s * 0.8, s * 0.03, 0, TAU); q.fill();
  q.restore();
}

/* ---------------------------------------------------------------- indigo and batik
   the dye's colour as it oxidises: yellow-green → teal → deep blue over u = 1 − e^(−τ/1.6 s) */
function dye(u) { return u < 0.5 ? mixc('#9aac3a', '#2f8a86', u * 2) : mixc('#2f8a86', '#1c2f78', (u - 0.5) * 2); }
function indigo(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i;
  var bx0 = S.x0 + S.span * 0.05, bw = Math.min(h * 1.6, S.span * 0.22), vx = Math.max(bx0 + bw + h * 1.2, S.x0 + S.span * 0.44), vr = h * 0.5, vtop = d - h * 0.7;
  var lx0 = vx + h * 1.25, lx1 = S.x1 - h * 0.8, ly = d - h * 1.5;
  layer(S, 'indigo', d - h * 2.4, S.H, function (q) {
    floor(q, S, N ? '#2a2620' : '#a8885e');
    /* bamboo poles and the drying line, cloths in every shade the vat gives */
    if (lx1 - lx0 > h * 0.8) {
      [lx0, lx1].forEach(function (x) { paper(q, rect(x - 2, ly - h * 0.1, 4, d - ly + h * 0.1), N ? '#8a7a4a' : '#c9b27a', 1); });
      line(q, [[lx0, ly], [lx1, ly]], 'rgba(40,20,10,.8)', 1);
      var n = Math.max(1, Math.floor((lx1 - lx0) / (h * 0.5))), cw = (lx1 - lx0) / n;
      for (i = 0; i < n; i++) { var x = lx0 + i * cw + cw * 0.08, ww = cw * 0.84, shade = ['#7fb0d8', '#3f78b8', '#24448a', '#16245a', '#2a5aa0'][i % 5], len = h * (0.75 + (i % 3) * 0.12);
        if (i === 2) { mohom(q, x + ww / 2, ly, ww * 1.1, h * 0.7, '#1f2f6a'); continue; }
        paper(q, rect(x, ly, ww, len), shade, 1);
        q.fillStyle = 'rgba(255,255,255,.85)';
        if (i % 2) { for (var k = 0; k < 6; k++) { q.beginPath(); q.arc(x + ww * (0.25 + (k % 2) * 0.5), ly + len * (0.15 + Math.floor(k / 2) * 0.3), ww * 0.12, 0, TAU); q.fill(); q.fillStyle = shade; q.beginPath(); q.arc(x + ww * (0.25 + (k % 2) * 0.5), ly + len * (0.15 + Math.floor(k / 2) * 0.3), ww * 0.06, 0, TAU); q.fill(); q.fillStyle = 'rgba(255,255,255,.85)'; } }
        else { q.strokeStyle = 'rgba(255,255,255,.7)'; q.lineWidth = 1.2; for (k = 0; k < 4; k++) { q.beginPath(); for (var yy = 0; yy <= len; yy += 3) { var xx = x + ww * (0.2 + k * 0.2) + Math.sin(yy * 0.15) * ww * 0.05; yy ? q.lineTo(xx, ly + yy) : q.moveTo(xx, ly); } q.stroke(); } }
        q.fillStyle = 'rgba(0,0,0,.25)'; q.fillRect(x, ly, ww, 2);
      }
    }
    /* two more vats, their lids on; indigo leaves drying in a basket */
    [[vx - h * 0.95, 0.38], [vx + h * 0.8, 0.32]].forEach(function (v) { oong(q, v[0], d + h * 0.04, h * v[1] * 1.5, N); q.fillStyle = N ? '#3a2a1c' : '#7a5230'; q.beginPath(); q.ellipse(v[0], d + h * 0.04 - h * v[1] * 1.5 * 1.35, h * v[1] * 0.8, h * 0.05, 0, 0, TAU); q.fill(); });
    solid(q, function (c2) { c2.beginPath(); c2.ellipse(bx0 + bw + h * 0.55, d + h * 0.05, h * 0.25, h * 0.1, 0, 0, Math.PI); c2.lineTo(bx0 + bw + h * 0.3, d - h * 0.05); c2.lineTo(bx0 + bw + h * 0.8, d - h * 0.05); c2.closePath(); }, '#c9a66b', 1);
    for (i = 0; i < 7; i++) { q.fillStyle = i % 2 ? '#3f7a4a' : '#5a9a5a'; q.beginPath(); q.ellipse(bx0 + bw + h * (0.36 + i * 0.06), d - h * 0.07, h * 0.06, h * 0.025, i, 0, TAU); q.fill(); }
    /* the batik frame on its legs, the wax pot on a little stove */
    line(q, [[bx0 + 3, d], [bx0 + 3, d - h * 0.42]], N ? '#4a2e1c' : '#7a4a2a', 2.5); line(q, [[bx0 + bw - 3, d], [bx0 + bw - 3, d - h * 0.42]], N ? '#4a2e1c' : '#7a4a2a', 2.5);
    paper(q, rect(bx0, d - h * 1.08, bw, h * 0.66), N ? '#4a2e1c' : '#7a4a2a', 1.2);
    q.fillStyle = N ? '#6a8ab0' : '#a9cbea'; q.fillRect(bx0 + 4, d - h * 1.04, bw - 8, h * 0.58);
    q.strokeStyle = 'rgba(255,248,220,.75)'; q.lineWidth = Math.max(1, h * 0.018); for (i = 0; i < 2; i++) { q.beginPath(); for (var bxx = bx0 + 6; bxx < bx0 + bw - 6; bxx += 3) { var byy = d - h * (i ? 0.52 : 0.98) + Math.sin(bxx * 0.25) * h * 0.025; bxx > bx0 + 6 ? q.lineTo(bxx, byy) : q.moveTo(bxx, byy); } q.stroke(); }
    paper(q, rect(bx0 + bw * 0.4, d - h * 0.2, h * 0.24, h * 0.2), '#5a4a42', 1);
  });
  /* batik: the wax line follows r = a·cos 3θ, a rose; θ grows with the cycle */
  var T2 = 14000, pb = (t % T2) / T2, rcx = bx0 + bw / 2, rcy = d - h * 0.75, ra = Math.min(bw * 0.3, h * 0.22), th1 = pb * Math.PI * 1.02, pt = null;
  c.strokeStyle = N ? '#f2e2a8' : '#fff4d0'; c.lineWidth = Math.max(1.4, h * 0.028); c.lineCap = 'round'; c.beginPath();
  for (var a = 0; a <= th1; a += 0.03) { var rr = ra * Math.cos(3 * a), px = rcx + Math.cos(a) * rr, py = rcy + Math.sin(a) * rr; a ? c.lineTo(px, py) : c.moveTo(px, py); pt = [px, py]; }
  c.stroke();
  if (pt) { c.fillStyle = '#ffb347'; c.beginPath(); c.arc(pt[0], pt[1], 1.8, 0, TAU); c.fill(); }
  var crew = K.town(S, 2, { sin: 0.5, mohom: 0.5 }), bat = fig(S, crew[0], (pt ? pt[0] : rcx) + h * 0.3, d + h * 0.04, h, STAND, -1, pt ? [pt[0] + h * 0.06, pt[1] + h * 0.03] : null, [bx0 + bw * 0.42, d - h * 0.24]);
  if (pt) line(c, [bat.hand[0], [pt[0] + 1, pt[1] - 1]], '#7a4a2a', 1.2);
  glow(c, bx0 + bw * 0.52, d - h * 0.2, h * 0.18, 25, 0.5 + 0.2 * Math.sin(t / 150));
  /* the vat: lift the cloth, hold it in the air, dip it again (12 s); each part of the cloth blues by its own time out of the dye */
  var T = 12000, ms = t % T, lift = ease(seg(ms, 600, 5000)) - ease(seg(ms, 10200, 11800)), surf = vtop + h * 0.02, ytop = lerp(surf + h * 0.05, d - h * 1.7, lift);
  var cwid = h * 0.52, len = surf - ytop, nS = 14, vLift = (surf + h * 0.05 - (d - h * 1.7)) / 4400;
  /* the dyer behind, both hands at the cloth's top edge */
  var dyer = fig(S, crew[1], vx + h * 0.45, d, h * 1.02, { lean: 0.15 - lift * 0.1, legs: [0.1, 0, -0.08, 0], arms: [1, 1, 1, 1] }, -1, [vx - cwid * 0.35, ytop], [vx + cwid * 0.3, ytop]);
  oongBack(c, vx, d, vr, N);
  /* the froth on the dye: the "indigo flower", bronze bubbles */
  c.fillStyle = N ? '#0e1a3a' : '#1a2a5a'; c.beginPath(); c.ellipse(vx, surf, vr * 0.82, vr * 0.18, 0, 0, TAU); c.fill();
  for (i = 0; i < 7; i++) { var ba = i * 0.9 + t / 3000, bxp = vx + Math.cos(ba) * vr * 0.45, byp = surf + Math.sin(ba) * vr * 0.08; c.fillStyle = i % 2 ? 'rgba(170,110,160,.8)' : 'rgba(190,140,80,.8)'; c.beginPath(); c.arc(bxp, byp, h * (0.025 + 0.012 * Math.sin(t / 400 + i)), 0, TAU); c.fill(); }
  if (len > 1) {
    for (i = 0; i < nS; i++) {
      var s0 = len * i / nS, s1 = len * (i + 1) / nS, outFor = ms - 600 - (s0 + s1) / 2 / Math.max(1e-6, vLift), u = 1 - Math.exp(-Math.max(0, outFor) / 1600);
      if (ms > 10200) u = Math.max(u, 0.98);
      var sway = Math.sin(t / 900 + i * 0.4) * h * 0.02 * (i / nS);
      c.fillStyle = dye(u); c.fillRect(vx - cwid / 2 + sway, ytop + s0, cwid, s1 - s0 + 0.6);
    }
    c.fillStyle = 'rgba(0,0,0,.15)'; c.fillRect(vx - cwid / 2, ytop, cwid, 2);
    for (i = 0; i < 5; i++) { var du = ((t / 600) + i * 0.29) % 1, dxp = vx - cwid / 2 + ((i * 0.618) % 1) * cwid, dyp = ytop + len * 0.3 + du * du * len * 0.7; c.fillStyle = 'rgba(40,70,140,.8)'; c.beginPath(); c.ellipse(dxp, dyp, 1.2, 2.2, 0, 0, TAU); c.fill(); }
  }
  oong(c, vx, d + h * 0.02, vr * 1.5, N, true);
  label(S, S.x0 + S.span * 0.66, d - h * 2.05, '#1c2f78');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: d - h * 2.1, y1: S.H });
}
/* the oong, a big glazed clay jar for dye; front half drawn after the cloth */
function oong(c, x, y, s, N, front) {
  var r = s * 0.55, ht = s * 1.0, g = c.createLinearGradient(x - r, 0, x + r, 0);
  g.addColorStop(0, N ? '#1e140e' : '#3a2416'); g.addColorStop(0.4, N ? '#4a3220' : '#7a4e2c'); g.addColorStop(1, N ? '#1e140e' : '#3a2416');
  solid(c, function (q) { q.beginPath(); q.moveTo(x - r * 0.8, y - ht * 0.92); q.quadraticCurveTo(x - r * 1.1, y - ht * 0.5, x - r * 0.62, y); q.lineTo(x + r * 0.62, y); q.quadraticCurveTo(x + r * 1.1, y - ht * 0.5, x + r * 0.8, y - ht * 0.92); q.closePath(); }, g, 1.2);
  c.strokeStyle = 'rgba(255,220,170,.25)'; c.lineWidth = 1; c.beginPath(); c.ellipse(x, y - ht * 0.6, r * 0.98, r * 0.12, 0, 0, Math.PI); c.stroke();
  c.fillStyle = N ? '#2e1e14' : '#5a3a20'; c.beginPath(); c.ellipse(x, y - ht * 0.92, r * 0.82, r * 0.16, 0, 0, Math.PI); c.fill();
}
function oongBack(c, x, d, vr, N) { c.fillStyle = N ? '#2e1e14' : '#5a3a20'; c.beginPath(); c.ellipse(x, d + 0.02 * vr - vr * 1.5 * 0.92, vr * 0.84, vr * 0.2, 0, 0, TAU); c.fill(); }
/* a mo hom shirt on the line, its arms out */
function mohom(q, x, y, w, ht, col) {
  paper(q, poly([[x - w * 0.22, y], [x + w * 0.22, y], [x + w * 0.55, y + ht * 0.12], [x + w * 0.5, y + ht * 0.35], [x + w * 0.3, y + ht * 0.3], [x + w * 0.28, y + ht], [x - w * 0.28, y + ht], [x - w * 0.3, y + ht * 0.3], [x - w * 0.5, y + ht * 0.35], [x - w * 0.55, y + ht * 0.12]]), col, 1);
  q.strokeStyle = 'rgba(255,255,255,.35)'; q.lineWidth = 1; q.beginPath(); q.moveTo(x, y); q.lineTo(x, y + ht); q.stroke();
  q.fillStyle = 'rgba(255,255,255,.6)'; for (var i = 0; i < 4; i++) { q.beginPath(); q.arc(x + w * 0.04, y + ht * (0.15 + i * 0.2), 1.3, 0, TAU); q.fill(); }
}

var LOOKS = { lacquer: lacquer, wood: wood, silver: silver, saa: saa, celadon: celadon, loom: loom, candle: candle, indigo: indigo };
var KEYS = Object.keys(LOOKS);
function handicraft(S) {
  var v = LOOKS[S.variant] ? S.variant : KEYS[(S.seed >>> 5) % KEYS.length];
  LOOKS[v](S);
}
var CRAFT_WORDS = [
  ['lacquer', /lacquer|khrueang ?khoen|เครื่องเขิน|ลงรัก|ขันโตก/i],
  ['silver', /silver|เครื่องเงิน|เงินวัวลาย|repouss/i],
  ['wood', /\bwood|teak|tawai|บ้านถวาย|แกะสลักไม้|ไม้แกะ/i],
  ['saa', /\bsaa\b|mulberry|paper ?making|กระดาษสา|ทำกระดาษ/i],
  ['celadon', /celadon|ceramic|pottery|kiln|ศิลาดล|เซลาดอน|เครื่องปั้น|เตาเผา/i],
  ['candle', /candle|wax|เทียน/i],
  ['indigo', /indigo|batik|dye|คราม|บาติก|มัดย้อม|ย้อม/i],
  ['loom', /weav|loom|textile|silk|ทอผ้า|ผ้าทอ|ผ้าไหม|กี่ทอ/i]
];
D.variants.handicraft = function (e) {
  var s = (e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 200);
  for (var i = 0; i < CRAFT_WORDS.length; i++) if (CRAFT_WORDS[i][1].test(s)) return CRAFT_WORDS[i][0];
  return KEYS[K.hash(e.k || e.t || '') % KEYS.length];
};

/* ================================================================ Saint Expedite
   The red house: a spirit house on its pillar, painted red, three tiers of roof with gold
   chofa, a malai of marigold and jasmine; in its arched door Expedite in Roman armour, his
   cross raised (HODIE), the palm in his other hand, his helmet set down, his foot on the
   crow (CRAS). Offerings on the porch: red soda with straws, red flowers, pound cake,
   red candles, water, coins, incense. */
var RED = '#c4161f', RED2 = '#8d0b15', RED3 = '#e3242b', GOLD = '#e2b33c', GOLD2 = '#ffe39a';
function goldG(c, x0, x1) { var g = c.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, '#b8841c'); g.addColorStop(0.5, GOLD2); g.addColorStop(1, '#b8841c'); return g; }
/* the house's geometry in hh: pillar, porch, body, three roofs */
function houseAt(x, d, h) {
  var pd = d - h * 0.78, bw = h * 0.92, bt = pd - h * 0.74;
  return { x: x, d: d, h: h, pd: pd, bw: bw, bt: bt, pw: h * 1.95, door: [x, pd - h * 0.03, h * 0.5, h * 0.66], top: bt - h * 1.08 };
}
function houseBack(q, H2, N) {
  var x = H2.x, d = H2.d, h = H2.h, pd = H2.pd, bw = H2.bw, bt = H2.bt;
  /* plinth, pillar */
  paper(q, rect(x - h * 0.34, d - h * 0.22, h * 0.68, h * 0.24), RED2, 1.2);
  q.fillStyle = goldG(q, x - h * 0.34, x + h * 0.34); q.fillRect(x - h * 0.34, d - h * 0.22, h * 0.68, h * 0.03);
  var pg = q.createLinearGradient(x - h * 0.11, 0, x + h * 0.11, 0); pg.addColorStop(0, RED2); pg.addColorStop(0.45, RED3); pg.addColorStop(1, RED2);
  paper(q, rect(x - h * 0.11, pd, h * 0.22, d - h * 0.22 - pd), pg, 1.2);
  q.fillStyle = goldG(q, x - h * 0.11, x + h * 0.11); q.fillRect(x - h * 0.12, pd + h * 0.12, h * 0.24, h * 0.03); q.fillRect(x - h * 0.12, d - h * 0.34, h * 0.24, h * 0.03);
  /* the porch, its rail of little gold posts */
  paper(q, poly([[x - H2.pw / 2, pd], [x + H2.pw / 2, pd], [x + H2.pw / 2 - h * 0.08, pd + h * 0.1], [x - H2.pw / 2 + h * 0.08, pd + h * 0.1]]), RED2, 1.2);
  q.fillStyle = goldG(q, x - H2.pw / 2, x + H2.pw / 2); q.fillRect(x - H2.pw / 2, pd - h * 0.025, H2.pw, h * 0.035);
  /* the body; its arched door glows red inside */
  var bg = q.createLinearGradient(0, bt, 0, pd); bg.addColorStop(0, RED3); bg.addColorStop(1, RED2);
  paper(q, rect(x - bw / 2, bt, bw, pd - bt), bg, 1.2);
  q.fillStyle = goldG(q, x - bw / 2, x + bw / 2); q.fillRect(x - bw / 2, bt, bw, h * 0.035);
  [[-1], [1]].forEach(function (s) { var wx = x + s[0] * bw * 0.36; q.fillStyle = '#5a0a10'; q.fillRect(wx - h * 0.07, bt + h * 0.14, h * 0.14, h * 0.3); q.strokeStyle = GOLD; q.lineWidth = 1.2; q.strokeRect(wx - h * 0.07, bt + h * 0.14, h * 0.14, h * 0.3); });
  var D2 = H2.door, dx = D2[0], dy = D2[1], dw = D2[2], dh = D2[3];
  var ig = q.createRadialGradient(dx, dy - dh * 0.5, 0, dx, dy - dh * 0.5, dh * 0.7); ig.addColorStop(0, N ? '#ff8a5a' : '#ff6a4a'); ig.addColorStop(1, '#4a0508');
  q.fillStyle = ig; q.beginPath(); q.moveTo(dx - dw / 2, dy); q.lineTo(dx - dw / 2, dy - dh + dw / 2); q.arc(dx, dy - dh + dw / 2, dw / 2, Math.PI, TAU); q.lineTo(dx + dw / 2, dy); q.closePath(); q.fill();
}
function houseFront(q, H2, N) {
  var x = H2.x, h = H2.h, bt = H2.bt, D2 = H2.door, dx = D2[0], dy = D2[1], dw = D2[2], dh = D2[3];
  q.strokeStyle = goldG(q, dx - dw / 2, dx + dw / 2); q.lineWidth = Math.max(1.5, h * 0.035);
  q.beginPath(); q.moveTo(dx - dw / 2, dy); q.lineTo(dx - dw / 2, dy - dh + dw / 2); q.arc(dx, dy - dh + dw / 2, dw / 2, Math.PI, TAU); q.lineTo(dx + dw / 2, dy); q.stroke();
  /* roofs: three tiers, each with chofa curling up at the eaves */
  [[1.45, 0, 0.42, '#a10f19'], [1.05, 0.34, 0.38, RED], [0.66, 0.66, 0.34, RED3]].forEach(function (r, k) {
    var w = h * r[0], yb = bt - h * r[1], yt = yb - h * r[2];
    paper(q, poly([[x - w / 2, yb], [x, yt], [x + w / 2, yb]]), r[3], 1.4);
    q.strokeStyle = goldG(q, x - w / 2, x + w / 2); q.lineWidth = Math.max(1.4, h * 0.03); q.beginPath(); q.moveTo(x - w / 2, yb); q.lineTo(x, yt); q.lineTo(x + w / 2, yb); q.stroke();
    [-1, 1].forEach(function (s) { q.beginPath(); q.moveTo(x + s * w / 2, yb); q.quadraticCurveTo(x + s * (w / 2 + h * 0.1), yb - h * 0.02, x + s * (w / 2 + h * 0.07), yb - h * 0.16); q.stroke(); });
    if (k === 0) { q.fillStyle = goldG(q, x - w * 0.3, x + w * 0.3); q.font = '700 ' + Math.max(6, Math.round(h * 0.1)) + 'px ' + SERIF; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('HODIE', x, yb - h * 0.11); }
  });
  q.strokeStyle = goldG(q, x - 3, x + 3); q.lineWidth = Math.max(1.6, h * 0.04); q.beginPath(); q.moveTo(x, bt - h * 1.0); q.lineTo(x, H2.top); q.stroke();
  q.fillStyle = GOLD2; q.beginPath(); q.arc(x, H2.top, h * 0.035, 0, TAU); q.fill();
  /* the malai: marigold and jasmine looped from the eave */
  [-1, 1].forEach(function (s) { var x0 = x + s * h * 0.3, x1 = x + s * h * 0.62, y0 = bt + h * 0.02;
    for (var i = 0; i <= 10; i++) { var u = i / 10, px = lerp(x0, x1, u), py = y0 + Math.sin(u * Math.PI) * h * 0.16; q.fillStyle = i % 3 === 1 ? '#fffaf0' : i % 2 ? '#f29a1f' : '#ffb21f'; q.beginPath(); q.arc(px, py, h * 0.028, 0, TAU); q.fill(); }
    q.fillStyle = RED3; q.beginPath(); q.arc(x1, y0 + h * 0.02, h * 0.035, 0, TAU); q.fill(); });
}
/* Expedite in the door, s his height, facing us: red cloak, gold cuirass, the pteruges,
   the cross up in his right hand, the palm in his left, the helmet by his foot, the crow under it */
function saint(c, x, y, s, N, glowA) {
  var sk = '#e3b08a';
  if (glowA > 0) glow(c, x, y - s * 0.6, s * 1.1, 45, glowA);
  /* halo */
  c.strokeStyle = 'rgba(255,227,154,.9)'; c.lineWidth = Math.max(1, s * 0.03); c.beginPath(); c.arc(x, y - s * 0.86, s * 0.13, 0, TAU); c.stroke();
  /* cloak behind */
  c.fillStyle = '#9c0d17'; c.beginPath(); c.moveTo(x - s * 0.15, y - s * 0.72); c.quadraticCurveTo(x - s * 0.36, y - s * 0.3, x - s * 0.3, y - s * 0.02); c.lineTo(x + s * 0.24, y - s * 0.04); c.quadraticCurveTo(x + s * 0.3, y - s * 0.4, x + s * 0.15, y - s * 0.72); c.closePath(); c.fill();
  /* legs, sandals */
  line(c, [[x - s * 0.06, y - s * 0.32], [x - s * 0.08, y - s * 0.02]], sk, s * 0.08); line(c, [[x + s * 0.06, y - s * 0.32], [x + s * 0.1, y - s * 0.1]], sk, s * 0.08);
  /* pteruges: strips round the hips */
  for (var i = 0; i < 6; i++) { c.fillStyle = i % 2 ? '#c4161f' : '#e8b84a'; c.fillRect(x - s * 0.15 + i * s * 0.05, y - s * 0.44, s * 0.045, s * 0.14); }
  /* cuirass */
  var g = c.createLinearGradient(x - s * 0.15, 0, x + s * 0.15, 0); g.addColorStop(0, '#a8741c'); g.addColorStop(0.5, '#ffe39a'); g.addColorStop(1, '#a8741c');
  c.fillStyle = g; c.beginPath(); c.moveTo(x - s * 0.15, y - s * 0.72); c.lineTo(x + s * 0.15, y - s * 0.72); c.lineTo(x + s * 0.13, y - s * 0.43); c.lineTo(x - s * 0.13, y - s * 0.43); c.closePath(); c.fill();
  /* arms: right up with the cross, left down with the palm */
  line(c, [[x + s * 0.14, y - s * 0.68], [x + s * 0.26, y - s * 0.6], [x + s * 0.28, y - s * 0.8]], sk, s * 0.065);
  line(c, [[x - s * 0.14, y - s * 0.68], [x - s * 0.22, y - s * 0.5], [x - s * 0.2, y - s * 0.38]], sk, s * 0.065);
  /* the cross, HODIE along its beam */
  var cx = x + s * 0.28; line(c, [[cx, y - s * 0.35], [cx, y - s * 1.08]], '#f5d27a', s * 0.05); line(c, [[cx - s * 0.2, y - s * 0.93], [cx + s * 0.2, y - s * 0.93]], '#f5d27a', s * 0.1);
  c.fillStyle = '#7d0a13'; c.font = '700 ' + Math.max(4, s * 0.075) + 'px ' + SERIF; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('HODIE', cx, y - s * 0.93);
  /* the palm frond */
  c.strokeStyle = '#2f7a45'; c.lineWidth = Math.max(1, s * 0.025); c.beginPath(); c.moveTo(x - s * 0.2, y - s * 0.38); c.quadraticCurveTo(x - s * 0.34, y - s * 0.6, x - s * 0.28, y - s * 0.85); c.stroke();
  for (i = 1; i < 7; i++) { var u = i / 7, px = lerp(x - s * 0.24, x - s * 0.3, u), py = lerp(y - s * 0.45, y - s * 0.84, u); c.beginPath(); c.moveTo(px, py); c.lineTo(px - s * 0.09, py + s * 0.03); c.moveTo(px, py); c.lineTo(px + s * 0.07, py + s * 0.04); c.stroke(); }
  /* head: youthful, dark hair */
  c.fillStyle = sk; c.beginPath(); c.arc(x, y - s * 0.84, s * 0.085, 0, TAU); c.fill();
  c.fillStyle = '#2a1a12'; c.beginPath(); c.arc(x, y - s * 0.87, s * 0.087, Math.PI * 1.05, Math.PI * 1.95); c.fill();
  /* the helmet set down */
  c.fillStyle = '#d4a23f'; c.beginPath(); c.arc(x + s * 0.24, y - s * 0.02, s * 0.08, Math.PI, TAU); c.fill(); c.fillStyle = '#c4161f'; c.beginPath(); c.ellipse(x + s * 0.24, y - s * 0.11, s * 0.09, s * 0.03, 0, 0, TAU); c.fill();
  /* the crow underfoot, CRAS on its ribbon */
  crow(c, x - s * 0.1, y - s * 0.03, s * 0.2, -1, 0, N);
  c.fillStyle = '#ffe39a'; c.fillRect(x - s * 0.34, y - s * 0.02, s * 0.24, s * 0.07); c.fillStyle = '#5a0a10'; c.font = '700 ' + Math.max(4, s * 0.06) + 'px ' + SERIF; c.fillText('CRAS', x - s * 0.22, y + s * 0.015);
}
/* a crow: body, head, beak, tail, a wing that beats as flap ∈ [−1, 1] */
function crow(c, x, y, s, dir, flap, N) {
  c.save(); c.translate(x, y); c.scale(dir, 1);
  c.fillStyle = '#0d0a12';
  c.beginPath(); c.ellipse(0, -s * 0.35, s * 0.42, s * 0.24, -0.15, 0, TAU); c.fill();
  c.beginPath(); c.arc(s * 0.38, -s * 0.55, s * 0.17, 0, TAU); c.fill();
  c.beginPath(); c.moveTo(s * 0.5, -s * 0.6); c.lineTo(s * 0.78, -s * 0.52); c.lineTo(s * 0.5, -s * 0.48); c.fill();
  c.beginPath(); c.moveTo(-s * 0.35, -s * 0.36); c.lineTo(-s * 0.85, -s * 0.22); c.lineTo(-s * 0.8, -s * 0.38); c.closePath(); c.fill();
  c.fillStyle = '#1b1624'; c.beginPath(); c.moveTo(-s * 0.1, -s * 0.42); c.quadraticCurveTo(-s * 0.2, -s * 0.42 - flap * s * 0.7, -s * 0.6, -s * 0.42 - flap * s * 0.55); c.quadraticCurveTo(-s * 0.3, -s * 0.36, s * 0.2, -s * 0.36); c.closePath(); c.fill();
  c.strokeStyle = '#2a2430'; c.lineWidth = Math.max(1, s * 0.05); c.beginPath(); c.moveTo(0, -s * 0.14); c.lineTo(-s * 0.04, 0); c.moveTo(s * 0.12, -s * 0.14); c.lineTo(s * 0.14, 0); c.stroke();
  c.fillStyle = '#f5d27a'; c.beginPath(); c.arc(s * 0.43, -s * 0.58, Math.max(0.8, s * 0.035), 0, TAU); c.fill();
  c.restore();
}
/* her red ribbon with the crow's word, gold edged */
function cras(c, x, y, s, a) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a; c.font = 'italic 700 ' + Math.round(Math.max(9, s)) + 'px ' + SERIF;
  var w = c.measureText('cras!').width + s * 0.9, hh = s * 1.4;
  c.fillStyle = '#b3121f'; c.strokeStyle = '#f5d27a'; c.lineWidth = 1;
  c.beginPath(); c.moveTo(x + hh / 2, y); c.lineTo(x + w - hh / 2, y); c.arc(x + w - hh / 2, y + hh / 2, hh / 2, -Math.PI / 2, Math.PI / 2); c.lineTo(x + hh / 2, y + hh); c.arc(x + hh / 2, y + hh / 2, hh / 2, Math.PI / 2, Math.PI * 1.5); c.fill(); c.stroke();
  c.fillStyle = '#fff4dc'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('cras!', x + w / 2, y + hh / 2 + 1);
  c.restore();
}
/* offerings, set on a line y */
function soda(c, x, y, s) { var g = c.createLinearGradient(x - s * 0.12, 0, x + s * 0.12, 0); g.addColorStop(0, '#b3001b'); g.addColorStop(0.45, '#ff3b3b'); g.addColorStop(1, '#a1001a');
  solid(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.12, y); q.lineTo(x - s * 0.12, y - s * 0.6); q.quadraticCurveTo(x - s * 0.12, y - s * 0.72, x - s * 0.05, y - s * 0.8); q.lineTo(x - s * 0.05, y - s * 0.95); q.lineTo(x + s * 0.05, y - s * 0.95); q.lineTo(x + s * 0.05, y - s * 0.8); q.quadraticCurveTo(x + s * 0.12, y - s * 0.72, x + s * 0.12, y - s * 0.6); q.lineTo(x + s * 0.12, y); q.closePath(); }, g, 0.6);
  line(c, [[x, y - s * 0.9], [x + s * 0.22, y - s * 1.3]], '#ffffff', Math.max(1, s * 0.06)); c.fillStyle = 'rgba(255,255,255,.4)'; c.fillRect(x - s * 0.08, y - s * 0.55, s * 0.03, s * 0.4); }
function flowers(c, x, y, s) { solid(c, poly([[x - s * 0.14, y], [x + s * 0.14, y], [x + s * 0.18, y - s * 0.32], [x - s * 0.18, y - s * 0.32]]), RED3, 0.6);
  line(c, [[x, y - s * 0.3], [x - s * 0.2, y - s * 0.7]], '#2f7a45', 1.2); line(c, [[x, y - s * 0.3], [x + s * 0.18, y - s * 0.75]], '#2f7a45', 1.2); line(c, [[x, y - s * 0.3], [x, y - s * 0.82]], '#2f7a45', 1.2);
  [[-0.2, 0.72], [0.18, 0.77], [0, 0.85], [-0.08, 0.6], [0.1, 0.62]].forEach(function (p) { c.fillStyle = '#d8102a'; c.beginPath(); c.arc(x + p[0] * s, y - p[1] * s, s * 0.11, 0, TAU); c.fill(); c.fillStyle = '#ff6a7a'; c.beginPath(); c.arc(x + p[0] * s - s * 0.02, y - p[1] * s - s * 0.02, s * 0.04, 0, TAU); c.fill(); }); }
function cake(c, x, y, s) { c.fillStyle = '#f2f2f2'; c.beginPath(); c.ellipse(x, y - s * 0.02, s * 0.32, s * 0.06, 0, 0, TAU); c.fill();
  solid(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.24, y - s * 0.04); q.lineTo(x - s * 0.24, y - s * 0.3); q.quadraticCurveTo(x, y - s * 0.42, x + s * 0.24, y - s * 0.3); q.lineTo(x + s * 0.24, y - s * 0.04); q.closePath(); }, '#e7b760', 0.6);
  c.strokeStyle = '#9b5a1c'; c.lineWidth = Math.max(1, s * 0.05); c.beginPath(); c.moveTo(x - s * 0.24, y - s * 0.3); c.quadraticCurveTo(x, y - s * 0.42, x + s * 0.24, y - s * 0.3); c.stroke(); }
function redCandle(c, x, y, s, t, k) { solid(c, rect(x - s * 0.07, y - s * 0.5, s * 0.14, s * 0.5), RED, 0.5); c.fillStyle = GOLD2; c.fillRect(x - s * 0.1, y - s * 0.03, s * 0.2, s * 0.03);
  var fl = 1 + 0.15 * Math.sin(t / 90 + k * 2.1) + 0.07 * Math.sin(t / 37 + k), fh = s * 0.24 * fl, fy = y - s * 0.52;
  glow(c, x, fy - fh * 0.4, s * 0.35, 40, 0.8); c.fillStyle = '#ffc23a'; c.beginPath(); c.moveTo(x, fy - fh); c.quadraticCurveTo(x + s * 0.07, fy - fh * 0.3, x, fy); c.quadraticCurveTo(x - s * 0.07, fy - fh * 0.3, x, fy - fh); c.fill();
  c.fillStyle = '#fff4c2'; c.beginPath(); c.ellipse(x, fy - fh * 0.3, s * 0.025, fh * 0.2, 0, 0, TAU); c.fill(); }
function water(c, x, y, s) { c.fillStyle = 'rgba(207,233,255,.55)'; c.strokeStyle = '#e8f4ff'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - s * 0.1, y - s * 0.34); c.lineTo(x + s * 0.1, y - s * 0.34); c.lineTo(x + s * 0.08, y); c.lineTo(x - s * 0.08, y); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = 'rgba(124,196,255,.6)'; c.fillRect(x - s * 0.085, y - s * 0.22, s * 0.17, s * 0.21); }
function coins(c, x, y, s) { [[-0.1, 0, '#b8841c', '#ffe39a'], [0.1, 0, '#9aa3ad', '#e3e8ee'], [0, -0.05, '#b8841c', '#ffe39a']].forEach(function (k) { c.fillStyle = k[3]; c.strokeStyle = k[2]; c.lineWidth = 1; c.beginPath(); c.ellipse(x + k[0] * s, y - s * 0.04 + k[1] * s, s * 0.09, s * 0.035, 0, 0, TAU); c.fill(); c.stroke(); }); }
function joss(c, x, y, s, t) { solid(c, poly([[x - s * 0.13, y], [x + s * 0.13, y], [x + s * 0.11, y - s * 0.12], [x - s * 0.11, y - s * 0.12]]), '#b8841c', 0.5);
  for (var i = 0; i < 3; i++) { var sx = x + (i - 1) * s * 0.06, tx = sx + (i - 1) * s * 0.04, ty = y - s * 0.6; line(c, [[sx, y - s * 0.12], [tx, ty]], '#8d0b15', 1);
    c.fillStyle = '#ff7a3a'; c.beginPath(); c.arc(tx, ty, 1.2, 0, TAU); c.fill();
    c.strokeStyle = 'rgba(240,236,228,.5)'; c.lineWidth = 1; c.beginPath(); for (var j = 0; j <= s * 0.9; j += 3) { var xx = tx + Math.sin(j * 0.12 - t / 650 + i) * (1 + j * 0.06); j ? c.lineTo(xx, ty - j) : c.moveTo(xx, ty); } c.stroke(); } }
/* the porch, offerings both sides of the body */
function porch(c, H2, t, N) {
  var x = H2.x, h = H2.h, y = H2.pd - h * 0.01, s = h * 0.36, L = x - H2.bw / 2, R = x + H2.bw / 2;
  redCandle(c, L - h * 0.08, y, s * 0.9, t, 1); flowers(c, L - h * 0.24, y, s); water(c, L - h * 0.4, y, s * 0.8); soda(c, L - h * 0.51, y, s * 0.85);
  cake(c, R + h * 0.14, y, s); soda(c, R + h * 0.34, y, s * 0.85); soda(c, R + h * 0.44, y, s * 0.85); redCandle(c, R + h * 0.06, y, s * 0.75, t, 2);
  coins(c, x - h * 0.08, y + h * 0.005, s * 0.7); joss(c, x + h * 0.12, y, s, t);
}
/* rays from the door when today wins: 12 wedges, r = r₀·(0.6 + 0.4·sin 3φ), turning */
function rays(c, x, y, r, a, t) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a * 0.5; c.fillStyle = '#ffe9a8';
  for (var i = 0; i < 12; i++) { var ang = i / 12 * TAU + t / 4000, rr = r * (0.7 + 0.3 * Math.sin(i * 3 + t / 500)); c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(ang - 0.08) * rr, y + Math.sin(ang - 0.08) * rr); c.lineTo(x + Math.cos(ang + 0.08) * rr, y + Math.sin(ang + 0.08) * rr); c.closePath(); c.fill(); }
  c.restore(); glow(c, x, y, r * 0.6, 45, a);
}
/* HODIE, letter by letter on an arc above the roof, as her page bursts it from a crow */
function hodie(c, x, y, s, u, y0) {
  if (u <= 0 || u >= 1) return;
  var L = 'HODIE', a = Math.min(1, u * 6, (1 - u) * 4);
  c.save(); c.font = '700 ' + Math.round(s) + 'px ' + SERIF; c.textAlign = 'center'; c.textBaseline = 'middle';
  for (var i = 0; i < 5; i++) { var k = ease(clamp(u * 2.6 - i * 0.07, 0, 1)), fx = x + (i - 2) * s * 0.92, fy = y - Math.cos((i - 2) * 0.35) * s * 0.3;
    var px = lerp(x, fx, k), py = lerp(y0, fy, k) - Math.sin(k * Math.PI) * s * 0.4, sc = 0.4 + 0.6 * k;
    glow(c, px, py, s * 0.9, 45, a * 0.6); c.globalAlpha = a; c.save(); c.translate(px, py); c.scale(sc, sc);
    c.fillStyle = '#fff3c4'; c.strokeStyle = '#9a6a0e'; c.lineWidth = Math.max(1, s * 0.07); c.strokeText(L[i], 0, 0); c.fillText(L[i], 0, 0); c.restore(); }
  c.restore();
}
/* sticky notes of thanks on the plinth, a scribble each */
function notes(c, x0, x1, y0, y1, n, seed, extra) {
  var r = rnd(seed), cols = ['#fff27a', '#ffb0d0', '#a8f0c0', '#ffd27a', '#a8d8ff'], w = (y1 - y0) * 0.42;
  for (var i = 0; i < n + (extra ? 1 : 0); i++) {
    var last = i === n, px = last ? extra[0] : x0 + r() * (x1 - x0 - w), py = last ? extra[1] : y0 + r() * (y1 - y0 - w), rot = (r() - 0.5) * 0.4;
    c.save(); c.translate(px + w / 2, py + w / 2); c.rotate(rot); c.globalAlpha = last ? extra[2] : 1;
    c.shadowColor = 'rgba(0,0,0,.3)'; c.shadowBlur = 2; c.shadowOffsetY = 1; c.fillStyle = cols[i % cols.length]; c.fillRect(-w / 2, -w / 2, w, w); c.shadowColor = 'transparent';
    c.strokeStyle = 'rgba(60,40,80,.6)'; c.lineWidth = 0.7; c.beginPath(); for (var k = 0; k < 3; k++) { c.moveTo(-w * 0.35, -w * 0.25 + k * w * 0.22); c.lineTo(w * (0.1 + 0.2 * ((k + i) % 2)), -w * 0.25 + k * w * 0.22); } c.stroke();
    if (i % 3 === 0) { c.fillStyle = '#d8102a'; c.beginPath(); c.arc(w * 0.25, w * 0.25, w * 0.08, 0, TAU); c.fill(); }
    c.restore();
  }
}
/* the soi: a shophouse with green shutters, a power pole and its tangle, bougainvillea on a wall */
function soi(q, S, hx, N) {
  var h = S.hh, d = S.deck, x0 = S.x0, wall2 = N ? '#5a4a3e' : '#e8d8b8', i;
  floor(q, S, N ? '#2e2e30' : '#9a968e');
  q.fillStyle = N ? '#3a3a3c' : '#b8b4aa'; q.fillRect(S.x0, d + h * 0.18, S.span, 3);
  /* shophouse, two storeys, left */
  var sx1 = Math.min(hx - h * 1.25, x0 + S.span * 0.34);
  if (sx1 - x0 > h * 0.8) {
    paper(q, rect(x0 - 4, d - h * 2.2, sx1 - x0 + 4, h * 2.2), wall2, 1.4);
    q.fillStyle = N ? '#3a2a20' : '#a8432f'; q.fillRect(x0 - 4, d - h * 2.24, sx1 - x0 + 4, h * 0.08);
    for (var wx = x0 + h * 0.15; wx + h * 0.45 < sx1; wx += h * 0.65) {
      q.fillStyle = N ? '#ffcf7a' : '#2a4a3a'; q.fillRect(wx, d - h * 1.85, h * 0.45, h * 0.55);
      q.fillStyle = N ? 'rgba(80,50,20,.5)' : '#3f7a5a'; for (i = 0; i < 6; i++) q.fillRect(wx + 2, d - h * 1.82 + i * h * 0.09, h * 0.45 - 4, h * 0.04);
      q.fillStyle = N ? '#7a7670' : '#c9c4b8'; q.fillRect(wx, d - h * 0.95, h * 0.45, h * 0.95);
      q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; for (i = 1; i < 12; i++) { q.beginPath(); q.moveTo(wx, d - h * 0.95 + i * h * 0.08); q.lineTo(wx + h * 0.45, d - h * 0.95 + i * h * 0.08); q.stroke(); }
    }
    q.fillStyle = N ? '#2e4a3a' : '#3f8a5a'; q.fillRect(x0 - 4, d - h * 1.12, sx1 - x0 + 4, h * 0.1);
  }
  /* a low wall right of the house, bougainvillea over it */
  var wl = hx + h * 1.15, wr = S.x1;
  if (wr - wl > h * 0.6) {
    paper(q, rect(wl, d - h * 0.9, wr - wl + 4, h * 0.9), wall2, 1.2);
    var r = rnd(S.seed + 5);
    for (i = 0; i < (wr - wl) / (h * 0.06); i++) { var bx = wl + r() * (wr - wl), by = d - h * 0.9 + (r() - 0.6) * h * 0.35; q.fillStyle = r() < 0.25 ? '#3f7a3a' : r() < 0.5 ? '#c0307a' : '#e5427f'; q.beginPath(); q.arc(bx, by, h * (0.04 + r() * 0.04), 0, TAU); q.fill(); }
    for (i = 0; i < 6; i++) { var vx = wl + (i + 0.5) * (wr - wl) / 6; line(q, [[vx, d - h * 0.9], [vx + Math.sin(i) * h * 0.08, d - h * (0.5 + 0.25 * ((i * 7) % 3) / 3)]], '#3f7a3a', 1.5); q.fillStyle = '#e5427f'; q.beginPath(); q.arc(vx + Math.sin(i) * h * 0.08, d - h * (0.5 + 0.25 * ((i * 7) % 3) / 3), h * 0.05, 0, TAU); q.fill(); }
  }
  /* the power pole and its wires */
  var px = hx - h * 1.05; paper(q, rect(px - h * 0.05, d - h * 2.4, h * 0.1, h * 2.4 + 2), N ? '#5a5a5a' : '#b8b4aa', 1);
  q.strokeStyle = 'rgba(20,20,25,.75)'; q.lineWidth = 1;
  for (i = 0; i < 5; i++) { q.beginPath(); q.moveTo(S.x0, d - h * (2.1 + i * 0.04)); q.quadraticCurveTo((S.x0 + px) / 2, d - h * (1.85 + i * 0.05), px, d - h * (2.25 - i * 0.03)); q.quadraticCurveTo(px + h * 1.5, d - h * (1.9 + i * 0.07), S.x1, d - h * (2.0 + i * 0.06)); q.stroke(); }
  q.beginPath(); q.ellipse(px + h * 0.15, d - h * 1.95, h * 0.18, h * 0.08, 0.3, 0, TAU); q.stroke();
}
/* a mountain bend: the road sweeping round, chevron boards on its outside */
function bend(q, S, hx, N) {
  var h = S.hh, d = S.deck, i;
  floor(q, S, N ? '#1f3326' : '#5b8a5e');
  var r0 = d + h * 0.08;
  paper(q, function (c) { c.beginPath(); c.moveTo(S.x0 - 4, S.H + 4); c.lineTo(S.x0 - 4, r0 + h * 0.05); c.quadraticCurveTo(hx - h * 0.4, r0 - h * 0.05, S.x1 + 4, r0 + h * 0.12); c.lineTo(S.x1 + 4, S.H + 4); c.closePath(); }, N ? '#2a2a2e' : '#5a5a60', 1);
  q.strokeStyle = '#f2c94c'; q.lineWidth = 2; q.setLineDash([h * 0.18, h * 0.14]); q.beginPath(); q.moveTo(S.x0, r0 + h * 0.28); q.quadraticCurveTo(hx, r0 + h * 0.15, S.x1, r0 + h * 0.32); q.stroke(); q.setLineDash([]);
  /* chevrons, yellow and black, along the outside of the bend */
  for (var x = S.x0 + h * 0.3; x < S.x1 - h * 0.2; x += h * 0.75) {
    if (Math.abs(x - hx) < h * 1.15) continue;
    line(q, [[x, d + h * 0.05], [x, d - h * 0.42]], N ? '#6a6a6a' : '#9a9a9a', 2);
    paper(q, rect(x - h * 0.17, d - h * 0.62, h * 0.34, h * 0.24), '#f2c94c', 0.8);
    q.fillStyle = '#1a1a1a'; for (i = 0; i < 2; i++) { var cx = x - h * 0.08 + i * h * 0.13; q.beginPath(); q.moveTo(cx - h * 0.04, d - h * 0.6); q.lineTo(cx + h * 0.04, d - h * 0.5); q.lineTo(cx - h * 0.04, d - h * 0.4); q.lineTo(cx - h * 0.0, d - h * 0.4); q.lineTo(cx + h * 0.08, d - h * 0.5); q.lineTo(cx - h * 0.0, d - h * 0.6); q.closePath(); q.fill(); }
  }
  /* the hill the road cuts round, a tree */
  paper(q, function (c) { c.beginPath(); c.moveTo(hx + h * 1.1, d); c.quadraticCurveTo(hx + h * 2.0, d - h * 1.3, S.x1 + 4, d - h * 0.9); c.lineTo(S.x1 + 4, d); c.closePath(); }, N ? '#1d2c26' : '#4d7a52', 1.2);
  /* zebras at the shrine's foot, for the crossing */
  [[-0.75, 0.32], [0.72, 0.28]].forEach(function (z, k) { zebra(q, hx + z[0] * h, d + h * 0.02, h * z[1], k ? -1 : 1); });
}
function zebra(q, x, y, s, dir) {
  q.save(); q.translate(x, y); q.scale(dir, 1);
  q.fillStyle = '#f5f5f0'; q.beginPath(); q.ellipse(0, -s * 0.6, s * 0.4, s * 0.2, 0, 0, TAU); q.fill();
  q.fillRect(-s * 0.32, -s * 0.6, s * 0.08, s * 0.6); q.fillRect(s * 0.24, -s * 0.6, s * 0.08, s * 0.6);
  q.beginPath(); q.moveTo(s * 0.25, -s * 0.7); q.lineTo(s * 0.45, -s * 1.1); q.lineTo(s * 0.6, -s * 1.0); q.lineTo(s * 0.38, -s * 0.6); q.fill();
  q.fillStyle = '#1a1a1a'; for (var i = 0; i < 5; i++) q.fillRect(-s * 0.3 + i * s * 0.14, -s * 0.78, s * 0.05, s * 0.32);
  q.fillRect(s * 0.38, -s * 1.12, s * 0.04, s * 0.2);
  q.restore();
}
function motorbike(c, x, y, s, t, N, d2, wai) {
  var wr = s * 0.2, spin = t / 80;
  [-0.4, 0.4].forEach(function (o) { c.strokeStyle = '#1a1a1a'; c.lineWidth = s * 0.07; c.beginPath(); c.arc(x + o * s, y - wr, wr, 0, TAU); c.stroke(); c.strokeStyle = '#9a9a9a'; c.lineWidth = 1; c.beginPath(); c.moveTo(x + o * s + Math.cos(spin) * wr, y - wr + Math.sin(spin) * wr); c.lineTo(x + o * s - Math.cos(spin) * wr, y - wr - Math.sin(spin) * wr); c.stroke(); });
  solid(c, poly([[x - s * 0.42, y - wr * 1.6], [x + s * 0.1, y - wr * 1.4], [x + s * 0.32, y - wr * 2.4], [x + s * 0.4, y - wr * 1.2], [x - s * 0.1, y - wr * 1.0]]), d2.col || '#d9342b', 0.8);
  c.fillStyle = '#2a2a2a'; c.fillRect(x - s * 0.35, y - wr * 1.95, s * 0.35, wr * 0.35);
  if (N) glow(c, x + s * 0.45, y - wr * 2.1, s * 0.35, 50, 0.7);
  fig({ c: c }, d2, x - s * 0.15, y - wr * 0.6, s * 0.95, { lean: 0.2, seat: 0.55, legs: [1.2, -1.3, 1.1, -1.2], arms: [1.2, 0.4, 1.3, 0.3] }, 1, [x + s * 0.3, y - wr * 2.3], wai ? [x + s * 0.1, y - wr * 3.3] : [x + s * 0.28, y - wr * 2.25]);
  c.fillStyle = '#f2f2f2'; var hd = [x - s * 0.15 + s * 0.95 * 0.2 * 0.5, y - wr * 0.6 - s * 0.95 * 0.55 - s * 0.95 * 0.45]; c.beginPath(); c.arc(hd[0] + s * 0.06, hd[1] + s * 0.02, s * 0.11, Math.PI, TAU); c.fill();
}
function expedite(S) {
  var c = S.c, h = S.hh, d = S.deck, N = S.night, t = S.t, i, look = S.variant === 'novena' || S.variant === 'soi' ? S.variant : ((S.seed >>> 4) % 2 ? 'novena' : 'soi');
  S.noMagic = true;
  var hx = S.x0 + S.span * (S.phone ? 0.46 : 0.42), H2 = houseAt(hx, d, h);
  layer(S, 'exp-' + look, d - h * 2.6, S.H, function (q) {
    if (look === 'soi') soi(q, S, hx, N); else bend(q, S, hx, N);
    houseBack(q, H2, N);
    if (look === 'soi') notes(q, hx - h * 0.33, hx + h * 0.33, d - h * 0.2, d - h * 0.01, 7, 3, null);
    /* rows of red soda at the pillar's foot, a malai of red roses */
    for (i = 0; i < 4; i++) { soda(q, hx - h * 0.62 - i * h * 0.1, d + h * 0.05 + (i % 2) * 2, h * 0.3); }
    cake(q, hx + h * 0.55, d + h * 0.06, h * 0.32); flowers(q, hx + h * 0.82, d + h * 0.06, h * 0.36);
  });
  /* the cycle, 16 s: walk up, stick the thanks on, wai; the light, HODIE; the crow goes, comes back */
  var T = 16000, ms = t % T, glowA = 0.25 + 0.15 * Math.sin(t / 700);
  var burst = look === 'soi' ? seg(ms, 6600, 11000) : seg(ms, 10200, 14600), shine = burst > 0 && burst < 1 ? Math.sin(Math.PI * Math.min(1, burst * 1.4)) : 0;
  rays(c, H2.door[0], H2.door[1] - H2.door[3] * 0.45, h * 1.5, shine, t);
  saint(c, H2.door[0], H2.door[1] - h * 0.01, h * 0.56, N, glowA + shine * 0.6);
  houseFront(c, H2, N);
  porch(c, H2, t, N);
  /* the live crow: on the top roof's eave, croaking; startled when today wins, it beats away up-left and glides back */
  var perch = [hx + h * 0.42, H2.bt - h * 0.36], b0 = look === 'soi' ? 6800 : 10400, gone = ms - b0, back = T - 2600, cr = [perch[0], perch[1]], flap = 0, cdir = -1, show = true;
  if (gone > 0 && ms < back) { var u = gone / 1000; cr = [perch[0] - u * h * 1.6, perch[1] - u * h * 1.1 - Math.sin(u * 3) * h * 0.1]; flap = Math.sin(t / 70); if (cr[1] < -h) show = false; }
  else if (ms >= back) { var v = ease(seg(ms, back, T - 300)); cr = [lerp(S.x0 - h * 0.5, perch[0], v), lerp(perch[1] - h * 1.4, perch[1], v) - Math.sin(v * Math.PI) * h * 0.2]; cdir = 1; flap = v > 0.85 ? 0 : Math.sin(t / 110) * 0.6; }
  if (show) crow(c, cr[0], cr[1], h * 0.32, cdir, flap, N);
  var croak = gone < 0 && (ms % 2400) < 1000 ? Math.min(1, (ms % 2400) / 150, (1000 - (ms % 2400)) / 150) : 0;
  cras(c, perch[0] + h * 0.08, perch[1] - h * 0.62, h * 0.16, croak);
  hodie(c, H2.x, H2.top - h * 0.3, Math.max(11, h * 0.3), look === 'soi' ? seg(ms, 6700, 11500) : seg(ms, 10300, 14800), H2.door[1] - H2.door[3] * 0.6);
  if (look === 'soi') {
    /* the devotee: walks up, the note goes on the plinth, a wai, walks off */
    var crew = K.town(S, 1, { casual: 0.5, sin: 0.5 }), dvx = hx - h * 0.62, wx, P, hA = null, hB = null, dir = 1, nx = hx - h * 0.18, ny = d - h * 0.16, noteA = clamp((ms - 5200) / 200, 0, 1) * (1 - seg(ms, 15000, 15800));
    if (ms < 4000) { wx = lerp(S.x0 - h * 0.6, dvx, ms / 4000); P = K.walkP(ms / 1000 * TAU * 0.9, false); }
    else if (ms < 6000) { wx = dvx; P = { lean: 0.35, legs: [0.15, 0, -0.1, 0], arms: [0.5, 0.3, 0.4, 0.3] }; var r2 = ease(seg(ms, 4200, 5100)) - ease(seg(ms, 5400, 5900)); hA = [lerp(wx + h * 0.12, nx + h * 0.02, r2), lerp(d - h * 0.5, ny + h * 0.03, r2)]; }
    else if (ms < 11000) { wx = dvx; P = { lean: 0.12 + 0.08 * Math.sin(seg(ms, 6200, 7600) * Math.PI), legs: [0.06, 0, -0.06, 0], arms: [0.5, 0.3, 0.4, 0.3] }; hA = [wx + h * 0.16, d - h * 0.78]; hB = [wx + h * 0.15, d - h * 0.8]; }
    else { wx = lerp(dvx, S.x0 - h * 0.8, seg(ms, 11000, 15000)); P = K.walkP(ms / 1000 * TAU * 0.9, false); dir = -1; }
    var me = fig(S, crew[0], wx, d + h * 0.1, h, P, dir, hA, hB);
    if (ms > 4000 && ms < 5300) { c.fillStyle = '#fff27a'; c.fillRect(me.hand[0][0] - h * 0.04, me.hand[0][1] - h * 0.04, h * 0.08, h * 0.08); }
    if (noteA > 0) notes(c, 0, 0, 0, h * 0.19, 0, 9, [nx - h * 0.04, ny - h * 0.03, noteA]);
    /* the soi dog asleep under the shutter, breathing */
    var dgx = S.x0 + S.span * 0.1, br = 1 + 0.05 * Math.sin(t / 900);
    if (dgx < hx - h * 1.6) { c.fillStyle = N ? '#8a6a4a' : '#c9a06a'; c.beginPath(); c.ellipse(dgx, d + h * 0.12, h * 0.26, h * 0.09 * br, 0, 0, TAU); c.fill(); c.beginPath(); c.arc(dgx + h * 0.24, d + h * 0.1, h * 0.08, 0, TAU); c.fill(); c.beginPath(); c.moveTo(dgx + h * 0.2, d + h * 0.04); c.lineTo(dgx + h * 0.26, d - h * 0.02); c.lineTo(dgx + h * 0.29, d + h * 0.05); c.fill(); }
  } else {
    /* the novena: nine red candles on the ledge, lit one a day (one each 1.1 s), a kneeling devotee with the light */
    var cy0 = d + h * 0.1, k9 = Math.min(9, Math.floor((ms - 300) / 1100) + 1), out = seg(ms, 14600, 15600);
    for (i = 0; i < 9; i++) { var cxp = hx - h * 0.8 + i * h * 0.2; if (i < k9 && ms > 300 && out < 1) { c.save(); c.globalAlpha = 1 - out; redCandle(c, cxp, cy0, h * 0.34, t, i); c.restore(); } else { solid(c, rect(cxp - h * 0.024, cy0 - h * 0.17, h * 0.048, h * 0.17), RED, 0.5); } }
    c.fillStyle = GOLD2; c.font = '700 ' + Math.round(Math.max(9, h * 0.14)) + 'px ' + SERIF; c.textAlign = 'center'; c.textBaseline = 'middle';
    var lighting = ms > 300 && ms < 300 + 9 * 1100, li = clamp(Math.floor((ms - 300) / 1100), 0, 8), crew2 = K.town(S, 2, { sin: 0.6, casual: 0.4 });
    var kx = hx - h * 1.3, hand = lighting ? [hx - h * 0.8 + li * h * 0.2, cy0 - h * 0.22] : [kx + h * 0.2, d - h * 0.42];
    var kn = fig(S, crew2[0], kx - (lighting ? 0 : 0), d + h * 0.14, h, { lean: lighting ? 0.35 : 0.05, seat: 0.24, legs: [1.5, -2.6, 1.5, -2.6], arms: [0.9, 1.6, 0.8, 1.7] }, 1, hand, lighting ? null : [kx + h * 0.2, d - h * 0.44]);
    if (lighting) { c.fillStyle = '#ffc23a'; c.beginPath(); c.arc(kn.hand[0][0] + 2, kn.hand[0][1] - 3, 2, 0, TAU); c.fill(); }
    /* nine beads above the candles, gold as each day is kept */
    for (i = 0; i < 9; i++) { c.fillStyle = i < k9 && ms > 300 && out < 1 ? '#ffd65a' : 'rgba(255,255,255,.35)'; c.beginPath(); c.arc(hx - h * 0.8 + i * h * 0.2, cy0 + h * 0.1, h * 0.03, 0, TAU); c.fill(); }
    /* a rider rounds the bend and lifts a hand in a wai to the house */
    var rp = ((t + 4000) % 9000) / 9000, rx = lerp(S.x0 - h, S.x1 + h, rp), ry = Math.min(S.H - 2, d + h * 0.62 + Math.pow((rx - hx) / S.span, 2) * h * 0.3), waiNow = Math.abs(rx - hx) < h * 0.9;
    motorbike(c, rx, ry, h * 0.66, t, N, crew2[1], waiNow);
  }
  S.hits.push({ k: 'event', x0: hx - h * 1.2, x1: hx + h * 1.2, y0: H2.top, y1: S.H });
  if (S.label) { if (S.phone) label(S, S.x0 + S.span * 0.4, d - h * 4.1, RED2); else label(S, hx + h * 2.4, look === 'soi' ? d - h * 2.05 : d - h * 1.75, RED2); }
  K.motes(S, S.phone ? 8 : 14);
}
D.variants.expedite = function (e) {
  var s = (e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 200);
  if (/novena|โนวีนา|19 ?april|19 เมษา|nineteenth|feast/i.test(s)) return 'novena';
  return K.hash(e.k || e.t || '') % 2 ? 'novena' : 'soi';
};

D.addScene('handicraft', handicraft,
  /handicraft|arts? (and|&) crafts?|\bcraft(?!s? ?(space|beer|brew|market|fair|sale|bazaar|cocktail|coffee|gin))|lacquer|wood ?carv|silversmith|silver ?(work|ware|craft)|repouss|celadon|saa paper|mulberry paper|paper ?making|batik|indigo|\bweav|candle carv|หัตถกรรม|งานฝีมือ|เครื่องเขิน|แกะสลัก(?!ผัก|ผลไม้)|เครื่องเงิน|เงินวัวลาย|กระดาษสา|ผ้าทอ|ทอผ้า|ย้อมคราม|ผ้าคราม|บาติก|ศิลาดล|เซลาดอน/i,
  'x = R·sin(θ + ωt) (the turning piece)<br>c = 1 − e<sup>−t/τ</sup> (indigo, celadon)', 1);
D.addScene('expedite', expedite,
  /(saint|st\.?|san|santo) ?exp[eé]dit|expeditus|\bexpedite\b(?! (your|the|visa|processing|service|delivery|shipping|it|this))|เอ็กซ์เปดิต|เซนต์เอ็กซ์|\bhodie\b/i,
  'r = r₀(0.7 + 0.3·sin 3φ) (the light)<br>x = x₀ − vt, y = y₀ − ut (the crow, away)', 1);
})();
