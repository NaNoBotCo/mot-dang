/* Wat portraits for the auto-doodler: a wat page with no photograph shows a Lanna viharn, a chedi
   behind it, tung in the wind and the naga stair, in the 5:2 frame under the page's map.
   The viharn, its naga barge boards, hang hong, bai raka, lai kham gable, kong khiu arch, lions and the
   chedi profiles are ported from the Lanna Craft minisite, https://motdang.net/sites/lanna-craft/
   (lanna-craft/tools/js: 10-motifs, 20-viharn, 30-hero, 40-chedi). The place's id (the seed) deals the
   tiers, wings, pitch, roof colour, lacquer, chedi form and side, tung, stair nagas, lions and trees;
   the place's own fields set the old city's wall, the river and the name board.
   The still parts are cut once per size, seed and light into offscreen layers; each frame draws the
   tung, the bells, the light that runs down the gold, the lamps and the fireflies. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.addScene) return;
var K = D.kit, rnd = K.rnd, TAU = K.TAU, PI = Math.PI, sin = Math.sin, cos = Math.cos, abs = Math.abs, sqrt = Math.sqrt, max = Math.max, min = Math.min, rad = PI / 180;
function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
function lerp(a, b, t) { return a + (b - a) * t; }
function sstep(a, b, x) { x = clamp((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); }
function hex(h) { var p = parseInt(h.slice(1), 16); return [(p >> 16) & 255, (p >> 8) & 255, p & 255]; }
function mixc(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
function rgb(c, a) { return a == null ? 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')' : 'rgba(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ',' + (+a).toFixed(3) + ')'; }
var FONT = '"Sarabun",system-ui,sans-serif';

/* the lacquer, tile and plaster colours; assigned per wat before its parts are drawn */
var C = { lac: '#9e1b12', lac2: '#c2281b', lacD: '#5c0d08', black: '#1b0f0b', gold: '#e8b02a', gold2: '#ffd766', tile: '#4a2a22', tile2: '#6b3a2c', lime: '#f5ecdc', lime2: '#d9cbb3', wood: '#7a4a26', jade: '#16917a' };
var ROOFS = [['#4a2a22', '#6b3a2c'], ['#9c3f2a', '#c0613c'], ['#38485a', '#5a6e82'], ['#2f5a4a', '#4a8068']];
var LACS = [['#9e1b12', '#c2281b', '#5c0d08'], ['#7e1a18', '#a52c26', '#3f0b0b'], ['#a6381a', '#d24f26', '#5f1a0c']];

/* ---------------------------------------------------------------- the pen: paths that fill and outline, with a floor under the line width */
function Pen(cx) {
  var P = { cx: cx, p: null, minlw: 0 };
  P.begin = function () { P.p = new Path2D(); return P; };
  P.M = function (x, y) { P.p.moveTo(x, y); return P; };
  P.L = function (x, y) { P.p.lineTo(x, y); return P; };
  P.Q = function (a, b, x, y) { P.p.quadraticCurveTo(a, b, x, y); return P; };
  P.C = function (a, b, c, d, x, y) { P.p.bezierCurveTo(a, b, c, d, x, y); return P; };
  P.Z = function () { P.p.closePath(); return P; };
  P.E = function (x, y, rx, ry, rot, a0, a1, ccw) { P.p.ellipse(x, y, rx, ry, rot || 0, a0 == null ? 0 : a0, a1 == null ? TAU : a1, !!ccw); return P; };
  P.R = function (x, y, w, h) { P.p.rect(x, y, w, h); return P; };
  P.fill = function (s) { cx.fillStyle = s; cx.fill(P.p); return P; };
  P.stroke = function (s, w, cap) { cx.strokeStyle = s; cx.lineWidth = max(w || 1, P.minlw); cx.lineCap = cap || 'round'; cx.lineJoin = 'round'; cx.stroke(P.p); return P; };
  P.fs = function (f, s, w) { P.fill(f); if (s) { cx.strokeStyle = s; cx.lineWidth = max(w || 1, P.minlw); cx.lineJoin = 'round'; cx.stroke(P.p); } return P; };
  return P;
}

/* ---------------------------------------------------------------- motifs */
/* a gilded surface: light at the top, warm in the middle, shadow below (lit 1 → 0 dims it) */
function gold(cx, x0, y0, x1, y1, lit) {
  var g = cx.createLinearGradient(x0, y0, x1, y1), k = lit == null ? 1 : lit;
  g.addColorStop(0, rgb(mixc(hex('#fff0b0'), hex('#7a5410'), 1 - k)));
  g.addColorStop(0.35, rgb(mixc(hex('#f2c040'), hex('#6a4808'), 1 - k)));
  g.addColorStop(0.7, rgb(mixc(hex('#c98a16'), hex('#3e2a05'), 1 - k)));
  g.addColorStop(1, rgb(mixc(hex('#8a5a07'), hex('#2a1b03'), 1 - k)));
  return g;
}
function limeG(cx, lit) {
  var g = cx.createLinearGradient(0, -120, 0, 0), k = lit == null ? 1 : lit;
  g.addColorStop(0, rgb(mixc(hex('#ffffff'), hex('#3a3a44'), 1 - k))); g.addColorStop(1, rgb(mixc(hex('#d9cbb3'), hex('#24242c'), 1 - k))); return g;
}
/* a flame from a base point to a tip, one side swelling, the tip curling by curl·length */
function flame(P, x0, y0, x1, y1, w, curl, side) {
  var dx = x1 - x0, dy = y1 - y0, l = sqrt(dx * dx + dy * dy) || 1, ux = dx / l, uy = dy / l, nx = -uy * (side || 1), ny = ux * (side || 1);
  var tx = x1 + nx * l * (curl || 0.18), ty = y1 + ny * l * (curl || 0.18);
  P.M(x0 + nx * w / 2, y0 + ny * w / 2)
    .Q(x0 + dx * 0.45 + nx * w * 0.95, y0 + dy * 0.45 + ny * w * 0.95, tx, ty)
    .Q(x0 + dx * 0.62 - nx * w * 0.05, y0 + dy * 0.62 - ny * w * 0.05, x0 - nx * w / 2, y0 - ny * w / 2).Z();
  return P;
}
/* a naga head in profile, facing +x when dir = 1; s = head length / 100, open = the jaw 0..1 */
function nagaHead(P, x, y, s, dir, o) {
  o = o || {}; var cx = P.cx, open = o.open == null ? 0.5 : o.open, lit = o.lit == null ? 1 : o.lit, m0 = P.minlw;
  cx.save(); cx.translate(x, y); cx.scale(s * (dir || 1), s); if (o.rot) cx.rotate(o.rot); P.minlw = m0 / s;
  var fill = gold(cx, 0, -120, 0, 0, lit), line = '#4a2400', jo = open * 10, cr = o.crest == null ? 1 : o.crest;
  P.begin(); flame(P, 6, -60, -38 * cr, -112 * cr - 6, 22, 0.22, -1); flame(P, 16, -64, -16 * cr, -124 * cr - 4, 20, 0.22, -1); flame(P, 26, -66, 8 * cr, -118 * cr - 4, 16, 0.2, -1);
  P.fs(fill, line, 2);
  if (o.neck !== false) {
    P.begin().M(-16, 4).C(-14, -20, -12, -36, -10, -46).L(24, -40).C(22, -26, 20, -10, 20, 4).Z().fs(fill, line, 2.2);
    P.begin(); for (var k = 0; k < 4; k++) { var yy = -6 - k * 9; P.M(8, yy).Q(16, yy - 3, 22, yy - 1); } P.stroke(line, 1.4);
  }
  P.begin().M(20, -44).C(34, -40 + jo, 50, -36 + jo * 1.4, 64, -40 + jo * 1.6).C(58, -32 + jo * 1.2, 40, -28 + jo, 22, -30).Z().fs(fill, line, 2);
  if (open > 0.15) { P.begin().M(30, -42 + jo * 0.5).Q(60, -44 + jo, 84, -48 + jo).M(78, -46 + jo).L(90, -52 + jo).M(78, -46 + jo).L(90, -42 + jo).stroke('#d62a2a', 2.4); }
  P.begin().M(-12, -46).C(-14, -60, 0, -70, 28, -71).C(48, -72, 64, -68, 72, -62).C(78, -66, 82, -74, 76, -80).C(84, -78, 88, -66, 78, -58).C(66, -54, 46, -52, 20, -46).Z().fs(fill, line, 2.2);
  P.begin(); flame(P, 22, -66, 48, -84, 9, 0.25, 1); P.fs(fill, line, 1.6);
  P.begin(); flame(P, 30, -32, -4, -14, 10, 0.3, 1); P.fs(fill, line, 1.6);
  P.begin().M(62, -59).L(60, -50).L(57, -58).Z().M(52, -40 + jo * 1.4).L(54, -48 + jo * 1.3).L(48, -40 + jo * 1.3).Z().fill('#fffaf0');
  P.begin().E(30, -60, 7, 5, -0.1).fs('#fff6d8', line, 1.6);
  P.begin().E(32, -60, 3, 3.6).fill('#1b0f0b');
  if (o.glow) { cx.globalAlpha *= o.glow; P.begin().E(32, -60, 9, 9).fill('rgba(255,80,40,.55)'); cx.globalAlpha /= o.glow; }
  P.minlw = m0; cx.restore();
}
/* a tapering scaled body along a centreline pts, width w0 → w1, with scutes, scale arcs and fins */
function tube(P, pts, w0, w1, o) {
  o = o || {}; var n = pts.length, L = [], R = [], i, a, b, dx, dy, l, w, nx, ny;
  for (i = 0; i < n; i++) { a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]; dx = b[0] - a[0]; dy = b[1] - a[1]; l = sqrt(dx * dx + dy * dy) || 1;
    w = lerp(w0, w1, i / (n - 1)) / 2; nx = -dy / l; ny = dx / l; L.push([pts[i][0] + nx * w, pts[i][1] + ny * w]); R.push([pts[i][0] - nx * w, pts[i][1] - ny * w]); }
  P.begin(); P.M(L[0][0], L[0][1]); for (i = 1; i < n; i++) P.L(L[i][0], L[i][1]);
  for (i = n - 1; i >= 0; i--) P.L(R[i][0], R[i][1]); P.Z();
  P.fs(o.fill || C.gold, '#4a2400', o.lw || 2);
  if (o.scales !== false) {
    P.begin(); var step = max(2, Math.round(n / (o.nscale || 26))), m, q, z;
    for (i = step; i < n - 1; i += step) { m = pts[i]; q = R[i]; P.M(lerp(m[0], q[0], 0.15), lerp(m[1], q[1], 0.15)).L(lerp(m[0], q[0], 0.85), lerp(m[1], q[1], 0.85)); }
    P.stroke('rgba(90,40,0,.55)', 1.2);
    P.begin(); for (i = (step >> 1) + 1; i < n - 1; i += step) { m = pts[i]; z = L[i]; var r = lerp(w0, w1, i / (n - 1)) * 0.2;
      P.M(lerp(m[0], z[0], 0.45) - r, lerp(m[1], z[1], 0.45)).Q(lerp(m[0], z[0], 0.45), lerp(m[1], z[1], 0.45) + r, lerp(m[0], z[0], 0.45) + r, lerp(m[1], z[1], 0.45)); }
    P.stroke('rgba(255,240,180,.7)', 1.3);
  }
  return { L: L, R: R };
}
/* bai raka: one fin standing on the board's top edge, leaning toward the apex */
function raka(P, x, y, ux, uy, nx, ny, w, h) {
  var tx = x + nx * h + ux * h * 0.38, ty = y + ny * h + uy * h * 0.38;
  P.M(x - ux * w / 2, y - uy * w / 2)
    .Q(x - ux * w * 0.35 + nx * h * 0.85, y - uy * w * 0.35 + ny * h * 0.85, tx, ty)
    .Q(tx - ux * h * 0.25 - nx * h * 0.1, ty - uy * h * 0.25 - ny * h * 0.1, x + ux * w * 0.05 + nx * h * 0.42, y + uy * w * 0.05 + ny * h * 0.42)
    .Q(x + ux * w * 0.3 + nx * h * 0.2, y + uy * w * 0.3 + ny * h * 0.2, x + ux * w / 2, y + uy * w / 2).Z();
}
/* a rosette of n gold petals, r long, with a glass centre */
function rosette(P, x, y, r, n, o) {
  o = o || {}; P.begin();
  for (var i = 0; i < n; i++) { var q = i * TAU / n, q1 = q - PI / n * 0.8, q2 = q + PI / n * 0.8;
    P.M(x, y).Q(x + cos(q1) * r * 0.9, y + sin(q1) * r * 0.9, x + cos(q) * r, y + sin(q) * r).Q(x + cos(q2) * r * 0.9, y + sin(q2) * r * 0.9, x, y); }
  P.fs(o.fill || C.gold, 'rgba(70,30,0,.6)', 1);
  P.begin().E(x, y, r * 0.28, r * 0.28).fill(o.eye || C.jade);
}
/* a curl (tua ngao): the logarithmic spiral r = r0·e^(−0.2θ/1.4) over turns turns */
function curl(P, x, y, r, a0, turns, dir) {
  var n = 40; P.M(x + cos(a0) * r, y + sin(a0) * r);
  for (var i = 1; i <= n; i++) { var q = a0 + dir * i / n * turns * TAU, rr = r * Math.exp(-0.2 * i / n * turns * TAU / 1.4); P.L(x + cos(q) * rr, y + sin(q) * rr); }
}
/* a temple bell with a bodhi-leaf clapper, swinging by the angle a */
function eaveBell(P, x, y, s, a, lit) {
  var cx = P.cx, m0 = P.minlw; cx.save(); cx.translate(x, y); cx.rotate(a); cx.scale(s, s); P.minlw = m0 / s;
  P.begin().M(0, 0).L(0, 8).stroke('#3a2a10', 1.2);
  P.begin().M(-5, 18).C(-5, 9, -3, 8, 0, 8).C(3, 8, 5, 9, 5, 18).Z().fs(gold(cx, 0, 8, 0, 18, lit), '#4a2400', 0.8);
  cx.rotate(-a * 0.6); P.begin().M(0, 18).L(0, 24).stroke('#3a2a10', 1);
  P.begin().M(0, 24).C(-6, 26, -6, 34, 0, 40).C(6, 34, 6, 26, 0, 24).Z().fs(gold(cx, 0, 24, 0, 40, lit), '#4a2400', 0.8);
  P.minlw = m0; cx.restore();
}
/* a seated lion guardian in profile facing dir: lime body, a mane of stacked flames, a curled tail */
function singha(P, x, y, s, dir, lit) {
  var cx = P.cx, m0 = P.minlw; cx.save(); cx.translate(x, y); cx.scale(s * dir, s); P.minlw = m0 / s;
  var body = limeG(cx, lit), line = '#6a5a44', gd = gold(cx, 0, -140, 0, 0, lit);
  P.begin().R(-34, -18, 76, 18).fs(lit > 0.5 ? '#e9dcc4' : '#4a4650', line, 1.5);
  P.begin().M(-28, -18).C(-30, -50, -20, -74, 2, -82).L(22, -80).C(30, -60, 34, -40, 34, -18).Z().fs(body, line, 1.5);
  P.begin().M(16, -18).L(16, -60).L(30, -60).L(30, -18).Z().fs(body, line, 1.2);
  P.begin().M(26, -18).Q(40, -18, 40, -24).L(26, -24).Z().fs(body, line, 1);
  P.begin(); for (var i = 0; i < 6; i++) flame(P, 4 + i * 2, -84 + i * 10, -22 - i * 3, -98 + i * 14, 14, 0.3, -1); P.fs(gd, '#5a3a08', 1.2);
  P.begin().M(0, -86).C(0, -112, 18, -122, 34, -118).C(52, -114, 58, -100, 52, -88).C(46, -80, 30, -78, 14, -80).Z().fs(body, line, 1.5);
  P.begin().M(40, -96).Q(54, -94, 52, -86).Q(44, -84, 38, -88).fill('#c2281b');
  P.begin().E(36, -106, 4.5, 3.5).fs('#fff', line, 1); P.begin().E(37, -106, 2, 2).fill('#1b0f0b');
  P.begin(); flame(P, 22, -116, 6, -142, 12, 0.3, -1); flame(P, 30, -118, 22, -148, 10, 0.3, -1); P.fs(gd, '#5a3a08', 1.2);
  P.begin(); curl(P, -36, -40, 16, 0, 1.2, -1); P.stroke(gd, 4);
  P.minlw = m0; cx.restore();
}

/* ---------------------------------------------------------------- the viharn, seen from the front
   Origin at the ground, centre front, y up the negative axis. n gables step down toward the viewer, m wing
   roofs step down to each side; every sloping edge carries a barge board, a naga and bai raka. */
/* the roof geometry: tier i has half-width hw0 + 20i and its apex at yb − hw·tan(pitch); wings step by the pitch less 21° */
function vGeom(o) {
  var E0 = -262, hw0 = 238, tn = Math.tan(o.pitch * rad), tw = Math.tan((o.pitch - 21) * rad), g = { E0: E0, hw0: hw0, tn: tn, tiers: [], wings: [], yP: -30, bells: [], lamps: [] };
  for (var i = 0; i < o.n; i++) { var yb = E0 - 58 * i, hw = hw0 + 20 * i; g.tiers.push({ i: i, yb: yb, hw: hw, ya: yb - hw * tn }); }
  var m = o.m, V = -84 - (E0 + 26), v = m ? (V - 18 * (m - 1)) / m : 0, xi = hw0 - 34, yi = E0 + 26;
  for (var j = 0; j < m; j++) { var h = v / tw, w = { j: j, xi: xi, yi: yi, xo: xi + h, yo: yi + v }; g.wings.push(w); xi = w.xo - 18; yi = w.yo + 18; }
  g.X = m ? g.wings[m - 1].xo + 40 : hw0 + 60;
  return g;
}
/* one sloping edge: tiles, board, the naga riding it, bai raka, the hang hong head; (x0,y0) low outer end, (x1,y1) high inner end */
function edge(P, x0, y0, x1, y1, side, sc, o, apex) {
  var cx = P.cx, dx = x1 - x0, dy = y1 - y0, len = sqrt(dx * dx + dy * dy), ux = dx / len, uy = dy / len, nx = uy, ny = -ux, k, s;
  if (ny > 0) { nx = -nx; ny = -ny; }
  var bt = 24 * sc, tl = 12 * sc, ext = (o.orn.hong ? 30 : 6) * sc, ex = x0 - ux * ext, ey = y0 - uy * ext;
  P.begin().M(ex + nx * bt, ey + ny * bt).L(x1 + nx * bt, y1 + ny * bt).L(x1 + nx * (bt + tl), y1 + ny * (bt + tl)).L(ex + nx * (bt + tl), ey + ny * (bt + tl)).Z().fill(C.tile);
  P.begin(); var nt = Math.round((len + ext) / (9 * sc));
  for (k = 0; k <= nt; k++) { s = k / nt; var px = lerp(ex, x1, s) + nx * (bt + tl), py = lerp(ey, y1, s) + ny * (bt + tl); P.M(px + 3 * sc, py).E(px, py, 3 * sc, 2.4 * sc, 0, 0, PI, true); } P.fill(C.tile2);
  P.begin().M(ex, ey).L(x1, y1).L(x1 + nx * bt, y1 + ny * bt).L(ex + nx * bt, ey + ny * bt).Z().fs(o.orn.naga ? C.lac : C.wood, '#3a0a04', 1.2);
  P.begin().M(ex + nx * 3, ey + ny * 3).L(x1 + nx * 3, y1 + ny * 3).M(ex + nx * (bt - 3), ey + ny * (bt - 3)).L(x1 + nx * (bt - 3), y1 + ny * (bt - 3)).stroke(C.gold, 1.6 * sc);
  if (o.orn.naga) {
    var pts = [], N = 70, A = bt * 0.3, waves = max(3, Math.round(len / (60 * sc)));
    for (k = 0; k <= N; k++) { s = k / N; var w = A * sin(s * waves * TAU - o.t * 1.6 * side + (apex ? 0 : 1.3)) * (0.35 + 0.65 * sin(PI * min(1, s * 1.05)));
      pts.push([lerp(x0 - ux * ext * 0.5, x1 - ux * 6 * sc, s) + nx * (bt / 2 + w), lerp(y0 - uy * ext * 0.5, y1 - uy * 6 * sc, s) + ny * (bt / 2 + w)]); }
    tube(P, pts, bt * 0.62, bt * 0.16, { fill: gold(cx, 0, y1, 0, y0), nscale: 18, fins: 0 });
  }
  if (o.orn.raka) {
    P.begin(); var nf = Math.round(len / (20 * sc));
    for (k = 1; k < nf; k++) { s = k / nf; raka(P, lerp(x0, x1, s) + nx * (bt + tl * 0.4), lerp(y0, y1, s) + ny * (bt + tl * 0.4), ux, uy, nx, ny, 15 * sc, 19 * sc); }
    P.fs(gold(cx, 0, y1 - 40, 0, y0), '#4a2400', 0.9);
  }
  if (o.orn.hong) nagaHead(P, ex + nx * bt * 0.4, ey + ny * bt * 0.4, 0.36 * sc, side, { open: 0.55, rot: -0.15, crest: 1 });
}
/* one gable: the lacquer pediment, its timber grid, a gold flower in every panel, glass points, lotus petals, two edges, the chofa finial */
function gable(P, tr, o, sc) {
  var cx = P.cx, hw = tr.hw, yb = tr.yb, ya = tr.ya, k, x;
  var g = cx.createLinearGradient(0, ya, 0, yb); g.addColorStop(0, C.lac2); g.addColorStop(1, C.lacD);
  P.begin().M(-hw, yb).L(0, ya).L(hw, yb).Z().fill(g);
  cx.save(); var clip = new Path2D(); clip.moveTo(-hw + 8, yb - 2); clip.lineTo(0, ya + 10); clip.lineTo(hw - 8, yb - 2); clip.closePath(); cx.clip(clip);
  var rows = [0.3, 0.6], H = yb - ya, cols = 4; P.begin();
  rows.forEach(function (f) { var y = yb - H * f; P.R(-hw, y - 4 * sc, hw * 2, 8 * sc); });
  for (k = -cols + 1; k < cols; k++) { x = k * hw / cols; P.R(x - 4 * sc, ya, 8 * sc, H); }
  P.fs(C.lacD, C.gold, 1.2);
  var rb = [0, 0.3, 0.6, 1];
  for (var r = 0; r < 3; r++) for (k = -cols; k < cols; k++) {
    var yc = yb - H * (rb[r] + rb[r + 1]) / 2, xc = (k + 0.5) * hw / cols, room = (1 - (yb - yc) / H) * hw - abs(xc);
    if (room < 18 * sc) continue; var rr0 = min(H * 0.3 / 2, hw / cols / 2) * 0.62; rr0 = min(rr0, room * 0.7);
    rosette(P, xc, yc, rr0, r === 2 ? 6 : 8, { eye: o.orn.glass ? C.jade : C.gold, fill: gold(cx, 0, yc - rr0, 0, yc + rr0) });
  }
  if (o.orn.glass) { var R = rnd(tr.i * 31 + 7);
    for (k = 0; k < 70; k++) { var u = R() * 2 - 1, v = R(), gx = u * hw * (1 - v), gy = yb - v * H; cx.globalAlpha = 0.35 + 0.65 * R(); P.begin().R(gx - 1.6 * sc, gy - 1.6 * sc, 3.2 * sc, 3.2 * sc).fill(k % 3 ? '#bff5ff' : '#ffffff'); }
    cx.globalAlpha = 1; }
  P.begin(); var np = Math.round(hw * 2 / (16 * sc));
  for (k = 0; k < np; k++) { x = -hw + (k + 0.5) * hw * 2 / np; P.M(x - 7 * sc, yb).Q(x, yb - 16 * sc, x + 7 * sc, yb).Z(); } P.fs(gold(cx, 0, yb - 16, 0, yb), '#4a2400', 0.6);
  cx.restore();
  edge(P, -hw, yb, 0, ya, -1, sc, o, true);
  edge(P, hw, yb, 0, ya, 1, sc, o, true);
  if (o.orn.chofa) { var top = ya - 30 * sc, sway = 0;
    P.begin().M(-5 * sc, ya - 24 * sc).C(-6 * sc, ya - 60 * sc, -4 * sc + sway, top - 50 * sc, 6 * sc + sway, top - 70 * sc)
      .C(18 * sc + sway, top - 82 * sc, 30 * sc + sway, top - 70 * sc, 22 * sc + sway, top - 60 * sc)
      .C(16 * sc + sway, top - 56 * sc, 10 * sc + sway, top - 62 * sc, 12 * sc + sway, top - 66 * sc)
      .C(4 * sc + sway, top - 54 * sc, 4 * sc, ya - 50 * sc, 5 * sc, ya - 24 * sc).Z().fs(gold(cx, 0, top - 80 * sc, 0, ya), '#4a2400', 1.4);
    P.begin(); for (k = 0; k < 4; k++) { var fy = ya - (34 + k * 16) * sc; flame(P, -5 * sc, fy, -20 * sc, fy - 14 * sc, 7 * sc, 0.3, 1); } P.fs(C.gold, '#4a2400', 0.8);
  }
}
/* the whole hall: platform, stair, door, aisles, columns, roofs rear to front, tie beam, kong khiu, lanterns, stair nagas, lions;
   the bells' and lamps' places go into g.bells and g.lamps, drawn by the frame */
function viharn(P, o) {
  var cx = P.cx, g = vGeom(o), X = g.X, yP = g.yP, E0 = g.E0, hw0 = g.hw0, k, j, side;
  P.begin().M(-X, 0).L(-X + 8, yP).L(X - 8, yP).L(X, 0).Z().fs(C.lime, '#a89a80', 1);
  P.begin().R(-X + 4, yP + 8, 2 * X - 8, 4).R(-X + 2, yP + 18, 2 * X - 4, 3).fill(C.lac);
  if (o.orn.stair) { P.begin().M(-82, 22).L(-70, yP).L(70, yP).L(82, 22).Z().fs('#efe4cf', '#a89a80', 1);
    P.begin(); for (k = 1; k < 6; k++) { var yy = lerp(yP, 22, k / 6), ww = lerp(70, 82, k / 6); P.M(-ww, yy).L(ww, yy); } P.stroke('#b9a888', 1.4); }
  P.begin().R(-hw0 + 18, E0, (hw0 - 18) * 2, yP - E0).fill('#2a140c');
  var dh = 158, dw = 86;
  P.begin().R(-dw / 2 - 8, yP - dh - 8, dw + 16, dh + 8).fill(C.lac);
  P.begin().R(-dw / 2, yP - dh, dw / 2 - 1, dh).R(1, yP - dh, dw / 2 - 1, dh).fs(o.glow > 0.05 ? '#3a1a08' : C.black, C.gold, 1.5);
  if (o.glow > 0.05) { cx.save(); cx.globalAlpha *= o.glow; var dg = cx.createRadialGradient(0, yP - 60, 4, 0, yP - 60, 120); dg.addColorStop(0, 'rgba(255,190,90,.9)'); dg.addColorStop(1, 'rgba(255,140,40,0)'); cx.fillStyle = dg; cx.fillRect(-dw / 2, yP - dh, dw, dh); cx.restore(); }
  P.begin(); [-1, 1].forEach(function (s) { var x0 = s * dw / 4; for (var q = 0; q < 5; q++) flame(P, x0, yP - 20 - q * 26, x0 + s * 10, yP - 40 - q * 26, 12, 0.3, s); }); P.fs(C.gold, '#4a2400', 0.6);
  g.wings.forEach(function (w) { [-1, 1].forEach(function (s) {
    P.begin().M(s * w.xi, w.yi).L(s * w.xo, w.yo).L(s * w.xo, yP).L(s * w.xi, yP).Z().fill('#24110a');
    P.begin().M(s * w.xi, yP - 54).L(s * (w.xo - 6), yP - 54).L(s * (w.xo - 6), yP).L(s * w.xi, yP).Z().fs(C.lime, '#a89a80', 1);
    P.begin().R(min(s * w.xi, s * (w.xo - 6)), yP - 58, abs(w.xo - 6 - w.xi), 6).fill(C.lac); }); });
  var cols = [-(hw0 - 30), -hw0 * 0.42, hw0 * 0.42, hw0 - 30];
  g.wings.forEach(function (w) { cols.push(-(w.xo - 20)); cols.push(w.xo - 20); });
  cols.forEach(function (x) { var top = E0; g.wings.forEach(function (w) { if (abs(x) > w.xi && abs(x) <= w.xo) top = lerp(w.yi, w.yo, (abs(x) - w.xi) / (w.xo - w.xi)) + 10; });
    var cg = cx.createLinearGradient(x - 9, 0, x + 9, 0); cg.addColorStop(0, C.lacD); cg.addColorStop(0.4, C.lac2); cg.addColorStop(1, C.lacD);
    P.begin().R(x - 9, top, 18, yP - top).fill(cg);
    P.begin().M(x - 9, top + 6).L(x + 9, top + 6).L(x, top + 30).Z().M(x - 9, yP - 4).L(x + 9, yP - 4).L(x, yP - 24).Z().fill(C.gold);
    P.begin().R(x - 11, top, 22, 6).R(x - 11, yP - 4, 22, 4).fill(C.gold); });
  for (var i = o.n - 1; i >= 1; i--) gable(P, g.tiers[i], o, 1 - i * 0.04);
  for (j = g.wings.length - 1; j >= 0; j--) { var w = g.wings[j];
    for (side = -1; side <= 1; side += 2) {
      edge(P, side * w.xo, w.yo, side * w.xi, w.yi, side, 0.82, o, false);
      var bx = side * (w.xo - 20), by = w.yo + 12; P.begin().M(bx, by + 34).C(bx + side * 2, by + 14, bx + side * 16, by + 6, bx + side * 30, by - 2).L(bx + side * 30, by + 6).C(bx + side * 18, by + 12, bx + side * 8, by + 22, bx + side * 6, by + 36).Z().fs(C.gold, '#4a2400', 1);
      if (o.orn.bells) g.bells.push({ x: side * (w.xo + 2), y: w.yo + 18, s: 1.3, ph: j * 2 + side });
    } }
  gable(P, g.tiers[0], o, 1);
  P.begin().R(-hw0, E0, hw0 * 2, 18).fs(C.lac, C.gold, 1.4);
  P.begin(); for (k = 0; k < 24; k++) { var bx2 = -hw0 + (k + 0.5) * hw0 * 2 / 24; P.M(bx2, E0 + 3).L(bx2 + 6, E0 + 9).L(bx2, E0 + 15).L(bx2 - 6, E0 + 9).Z(); } P.fill(C.gold);
  if (o.orn.kong) { var L2 = hw0 * 0.42 - 9, yk = E0 + 18; P.begin().M(-L2, yk);
    for (k = 0; k <= 60; k++) { var u = k / 60 * 2 - 1; P.L(u * L2, yk + 14); }
    for (k = 60; k >= 0; k--) { u = k / 60 * 2 - 1; P.L(u * L2, yk + 22 + 58 * u * u + 6 * abs(sin(u * PI * 4.5))); }
    P.Z().fs(gold(cx, 0, yk, 0, yk + 80), '#4a2400', 1.2);
    P.begin(); for (k = -4; k <= 4; k++) { var xr = k * L2 / 5; rosette(P, xr, yk + 26 + 52 * (xr / L2) * (xr / L2) * 0.6, 6, 6, { fill: C.lac2, eye: C.jade }); }
    P.begin().M(-12, yk + 18).Q(0, yk + 54, 12, yk + 18).Z().fs(C.gold, '#4a2400', 1); }
  if (o.orn.hu) { [-(hw0 * 0.42), hw0 * 0.42, -(hw0 - 30), hw0 - 30].forEach(function (x) { [-1, 1].forEach(function (s) {
    if (abs(x) > hw0 * 0.5 && s * x > 0) return; if (abs(x) < hw0 * 0.5 && s * x < 0 && o.orn.kong) return;
    P.begin().M(x + s * 9, E0 + 18).L(x + s * 52, E0 + 18).Q(x + s * 30, E0 + 30, x + s * 9, E0 + 66).Z().fs(gold(cx, 0, E0, 0, E0 + 66), '#4a2400', 1);
    P.begin(); curl(P, x + s * 22, E0 + 32, 8, s > 0 ? PI : 0, 1.3, s); P.stroke(C.lac, 2); }); }); }
  if (o.orn.bells) [-1, 1].forEach(function (s, q) { g.bells.push({ x: s * (hw0 + 6), y: E0 + 14, s: 1.4, ph: 6 + q }); });
  [-0.62, -0.2, 0.2, 0.62].forEach(function (f, q) { var lx = f * hw0, ly = E0 + 70 + 3 * q % 2; g.lamps.push({ x: lx, y: ly });
    if (o.glow < 0.02) return;
    cx.save(); P.begin().M(lx, E0 + 18).L(lx, ly - 18).stroke('#3a2a10', 1);
    var lg = cx.createRadialGradient(lx, ly, 2, lx, ly, 46); lg.addColorStop(0, 'rgba(255,200,110,' + 0.5 * o.glow + ')'); lg.addColorStop(1, 'rgba(255,120,40,0)'); cx.fillStyle = lg; cx.beginPath(); cx.arc(lx, ly, 46, 0, TAU); cx.fill();
    P.begin().M(lx - 12, ly - 16).C(lx - 18, ly - 4, lx - 18, ly + 6, lx - 10, ly + 16).L(lx + 10, ly + 16).C(lx + 18, ly + 6, lx + 18, ly - 4, lx + 12, ly - 16).Z().fs(rgb(mixc(hex('#c2281b'), hex('#ffb35a'), o.glow)), C.gold, 1.2);
    P.begin().M(lx - 6, ly + 16).L(lx - 7, ly + 30).M(lx, ly + 16).L(lx, ly + 34).M(lx + 6, ly + 16).L(lx + 7, ly + 30).stroke(C.gold, 1.2); cx.restore(); });
  if (o.orn.stair) [-1, 1].forEach(function (s) { var pts = [];
    for (var q = 0; q <= 24; q++) { var f = q / 24; pts.push([s * lerp(64, 92, f) + s * 3 * sin(f * 9 - 1), lerp(yP - 6, 14, f)]); }
    tube(P, pts, 9, 16, { fill: gold(cx, 0, yP, 0, 20), nscale: 10 });
    nagaHead(P, s * 100, 18, 0.62, s, { open: 0.6, crest: 1.15, rot: -0.12, glow: o.glow * 0.9 }); });
  if (o.orn.singha) { singha(P, -X + 40, 14, 0.85, -1, 1); singha(P, X - 40, 14, 0.85, 1, 1); }
  return g;
}

/* ---------------------------------------------------------------- the chedi: each form is a stack of segments, bottom to top,
   sampled into a width profile at 180 heights */
var CHEDI = {
  kukut: { seg: [['box', .06, .72, 0, 'brick'], ['box', .12, .62, 0, 'brick'], ['box', .02, .66, 0, 'brick'], ['box', .12, .54, 0, 'brick'], ['box', .02, .58, 0, 'brick'],
    ['box', .12, .46, 0, 'brick'], ['box', .02, .5, 0, 'brick'], ['box', .12, .38, 0, 'brick'], ['box', .02, .42, 0, 'brick'], ['box', .12, .3, 0, 'brick'], ['box', .02, .33, 0, 'brick'], ['taper', .14, .14, .02, 'brick']] },
  bell: { seg: [['box', .04, .62, 0, 'gold'], ['box', .035, .56, 0, 'gold'], ['box', .035, .5, 0, 'gold'], ['taper', .05, .44, .38, 'gold'], ['box', .03, .4, 0, 'gold'],
    ['taper', .04, .36, .33, 'gold'], ['bell', .2, .36, .14, 'gold', .035], ['box', .03, .16, 0, 'gold'], ['box', .02, .13, 0, 'gold'], ['rings', .2, .1, .035, 'gold', 7], ['bulb', .14, .04, .006, 'gold'], ['taper', .06, .01, .004, 'gold']] },
  chiangman: { seg: [['box', .21, .74, 0, 'lime'], ['box', .03, .62, 0, 'lime'], ['taper', .04, .52, .46, 'lime'], ['bell', .17, .44, .16, 'gold', .03], ['box', .03, .16, 0, 'gold'],
    ['rings', .17, .11, .035, 'gold', 6], ['bulb', .12, .04, .006, 'gold'], ['taper', .05, .01, .004, 'gold']] },
  kutao: { seg: [['box', .06, .64, 0, 'lime'], ['box', .04, .56, 0, 'lime'], ['ball', .14, .52, 0, 'kutao'], ['ball', .125, .44, 0, 'kutao'], ['ball', .11, .36, 0, 'kutao'],
    ['ball', .1, .29, 0, 'kutao'], ['ball', .09, .22, 0, 'kutao'], ['taper', .12, .06, .005, 'gold']] },
  shan: { seg: [['box', .05, .72, 0, 'white'], ['box', .04, .62, 0, 'white'], ['box', .04, .52, 0, 'white'], ['taper', .03, .46, .44, 'white'], ['bell', .16, .44, .22, 'gold', .02],
    ['concave', .44, .22, .012, 'gold'], ['taper', .05, .012, .004, 'gold']] },
  lao: { seg: [['box', .07, .54, 0, 'white'], ['box', .26, .44, 0, 'white'], ['taper', .05, .44, .38, 'gold'], ['concave', .5, .36, .012, 'gold'], ['taper', .05, .012, .004, 'gold']] }
};
var CHEDI_COL = { gold: '#e8b02a', lime: '#f1ead9', brick: '#a8613a', white: '#f7f3ec', kutao: '#efe6d2' };
/* width at 180 heights: box = w, taper = lerp, bell = lerp + a·sin, ball = √(1 − (2f − 1)²), rings = lerp·(1 + 0.16|sin|³), bulb, concave = (1 − f)^2.4 */
function profile(form) {
  if (form._p) return form._p; var segs = form.seg, tot = 0; segs.forEach(function (s) { tot += s[1]; });
  var N = 180, out = [], acc = 0, si = 0;
  for (var i = 0; i < N; i++) { var u = (i + 0.5) / N * tot; while (si < segs.length - 1 && u > acc + segs[si][1]) { acc += segs[si][1]; si++; }
    var s = segs[si], f = clamp((u - acc) / s[1], 0, 1), w;
    switch (s[0]) {
      case 'taper': w = lerp(s[2], s[3], f); break;
      case 'bell': w = lerp(s[2], s[3], Math.pow(f, 1.6)) + (s[5] || 0.03) * sin(PI * min(1, f * 1.2)); break;
      case 'ball': w = s[2] * max(0.28, sqrt(max(0, 1 - Math.pow(2 * f - 1, 2)))); break;
      case 'rings': w = lerp(s[2], s[3], f) * (1 + 0.16 * Math.pow(abs(sin(f * PI * (s[5] || 6))), 3)); break;
      case 'bulb': w = s[2] * Math.pow(1 - f, 0.7) * (1 + 0.6 * sin(PI * f)) + s[3]; break;
      case 'concave': w = s[3] + (s[2] - s[3]) * Math.pow(1 - f, 2.4); break;
      default: w = s[2];
    }
    out.push({ w: w, c: hex(CHEDI_COL[s[4]] || '#e8b02a'), s: si, k: s[4] }); }
  form._p = out; return out;
}
/* a chedi standing on (x, y), H tall: colour bands, round shading, mouldings, ceramic bowls, niches, elephants, the umbrella or hti */
function chedi(P, x, y, H, form, name) {
  var cx = P.cx, pr = profile(form), N = pr.length, dy = H / N, i, k, q, hw;
  P.begin(); P.M(x - pr[0].w * H / 2, y);
  for (i = 0; i < N; i++) P.L(x - pr[i].w * H / 2, y - (i + 1) * dy);
  P.L(x, y - H - 2);
  for (i = N - 1; i >= 0; i--) P.L(x + pr[i].w * H / 2, y - (i + 1) * dy);
  P.L(x + pr[0].w * H / 2, y); P.Z(); var path = P.p;
  P.fill('#000');
  for (i = 0; i < N; i++) { hw = pr[i].w * H / 2; cx.fillStyle = rgb(pr[i].c); cx.fillRect(x - hw - 0.5, y - (i + 1) * dy - 0.6, hw * 2 + 1, dy + 1.2); }
  cx.save(); cx.clip(path);
  var maxw = 0; pr.forEach(function (p) { if (p.w > maxw) maxw = p.w; }); var Wd = maxw * H / 2;
  var sg = cx.createLinearGradient(x - Wd, 0, x + Wd, 0); sg.addColorStop(0, 'rgba(40,20,0,.42)'); sg.addColorStop(0.32, 'rgba(255,255,255,.22)'); sg.addColorStop(0.5, 'rgba(255,255,255,0)'); sg.addColorStop(1, 'rgba(30,10,0,.5)');
  cx.fillStyle = sg; cx.fillRect(x - Wd, y - H - 4, Wd * 2, H + 6);
  cx.strokeStyle = 'rgba(60,30,0,.45)'; cx.lineWidth = max(1, H * 0.003);
  for (i = 1; i < N; i++) if (pr[i].s !== pr[i - 1].s) { var yy = y - i * dy; cx.beginPath(); cx.moveTo(x - Wd, yy); cx.lineTo(x + Wd, yy); cx.stroke(); }
  if (name === 'kutao') { var R = rnd(5); for (i = 0; i < N; i++) if (pr[i].k === 'kutao' && i % 3 === 0) { hw = pr[i].w * H / 2;
      for (q = 0; q < 6; q++) { var u = R() * 2 - 1; cx.fillStyle = ['#2e86de', '#16917a', '#e84d8a', '#e8b02a'][q % 4]; cx.beginPath(); cx.arc(x + u * hw * 0.9, y - i * dy, max(1, H * 0.006), 0, TAU); cx.fill(); } } }
  if (name === 'kukut') {
    [0.62, 0.54, 0.46, 0.38, 0.3].forEach(function (wd, k) { var u0 = (0.06 + k * 0.14) / 0.9, h = 0.12 / 0.9 * H, y0 = y - u0 * H, wdt = wd * H / 2;
      for (var j = -1; j <= 1; j++) { var nx = x + j * wdt * 0.62, nw = h * 0.42, ny = y0 - h * 0.1;
        cx.fillStyle = '#5a2a14'; cx.beginPath(); cx.moveTo(nx - nw / 2, ny); cx.lineTo(nx - nw / 2, ny - h * 0.5); cx.quadraticCurveTo(nx, ny - h * 0.95, nx + nw / 2, ny - h * 0.5); cx.lineTo(nx + nw / 2, ny); cx.fill();
        cx.fillStyle = '#e8b02a'; cx.beginPath(); cx.ellipse(nx, ny - h * 0.58, nw * 0.14, h * 0.08, 0, 0, TAU); cx.fill(); cx.fillRect(nx - nw * 0.12, ny - h * 0.5, nw * 0.24, h * 0.42); } }); }
  cx.restore();
  if (name === 'chiangman') { cx.save(); var bw = 0.74 * H / 2, by = y - 0.06 * H, es = H * 0.0011;
    [-0.66, 0, 0.66].forEach(function (f) { var ex = x + f * bw; cx.save(); cx.translate(ex, by); cx.scale(es, es);
      cx.fillStyle = '#e9e1cf'; cx.strokeStyle = '#8a7a5a'; cx.lineWidth = 3;
      cx.beginPath(); cx.ellipse(-46, -60, 34, 40, 0.2, 0, TAU); cx.ellipse(46, -60, 34, 40, -0.2, 0, TAU); cx.fill(); cx.stroke();
      cx.beginPath(); cx.ellipse(0, -70, 38, 44, 0, 0, TAU); cx.fill(); cx.stroke();
      cx.beginPath(); cx.moveTo(-12, -40); cx.quadraticCurveTo(-14, 10, 4, 30); cx.lineTo(16, 26); cx.quadraticCurveTo(10, 0, 12, -40); cx.closePath(); cx.fill(); cx.stroke();
      cx.fillStyle = '#fffaf0'; cx.beginPath(); cx.moveTo(-18, -38); cx.lineTo(-30, -14); cx.lineTo(-22, -36); cx.fill(); cx.beginPath(); cx.moveTo(18, -38); cx.lineTo(30, -14); cx.lineTo(22, -36); cx.fill();
      cx.fillStyle = '#1b0f0b'; cx.beginPath(); cx.arc(-15, -78, 4, 0, TAU); cx.arc(15, -78, 4, 0, TAU); cx.fill();
      cx.fillStyle = '#e8b02a'; cx.beginPath(); cx.moveTo(-26, -108); cx.lineTo(0, -122); cx.lineTo(26, -108); cx.lineTo(0, -98); cx.fill();
      cx.restore(); }); cx.restore(); }
  var ty = y - H, tu = name === 'bell' || name === 'chiangman', th = name === 'shan' || name === 'lao';
  if (tu) { for (k = 0; k < 4; k++) { var r = H * (0.05 - k * 0.01), yk = ty + H * 0.02 - k * H * 0.022;
      cx.fillStyle = '#ffd766'; cx.strokeStyle = '#8a5a07'; cx.lineWidth = 1; cx.beginPath(); cx.ellipse(x, yk, r, r * 0.28, 0, 0, TAU); cx.fill(); cx.stroke();
      for (q = -2; q <= 2; q++) { var bx = x + q * r * 0.42; cx.fillStyle = '#e8b02a'; cx.fillRect(bx - 1, yk + r * 0.2, 2, H * 0.012); cx.beginPath(); cx.arc(bx, yk + r * 0.2 + H * 0.014, H * 0.004, 0, TAU); cx.fill(); } }
    cx.fillStyle = '#fff3c0'; cx.beginPath(); cx.arc(x, ty - H * 0.075, H * 0.007, 0, TAU); cx.fill(); }
  if (th) { cx.strokeStyle = '#c98a16'; cx.lineWidth = max(1, H * 0.003);
    for (k = 0; k < 6; k++) { r = H * (0.06 - k * 0.009); yk = ty + H * 0.03 - k * H * 0.016; cx.beginPath(); cx.ellipse(x, yk, r, r * 0.25, 0, 0, TAU); cx.stroke();
      for (q = -3; q <= 3; q++) { bx = x + q * r * 0.3; cx.fillStyle = '#e8b02a'; cx.fillRect(bx - 0.7, yk + r * 0.2, 1.4, H * 0.01); cx.beginPath(); cx.arc(bx, yk + r * 0.2 + H * 0.011, H * 0.0035, 0, TAU); cx.fill(); } }
    cx.beginPath(); cx.moveTo(x, ty - H * 0.07); cx.lineTo(x, ty - H * 0.11); cx.stroke();
    cx.fillStyle = '#fff'; cx.beginPath(); cx.arc(x, ty - H * 0.115, H * 0.008, 0, TAU); cx.fill(); }
}

/* ---------------------------------------------------------------- what each wat is: the seed deals it */
function plan(S) {
  var r = rnd((S.seed ^ 0x9e3779b9) >>> 0), P = {}, a; r(); r(); r();
  P.dir = r() < 0.5 ? 1 : -1;
  a = r(); P.n = a < 0.25 ? 1 : a < 0.78 ? 2 : 3;
  a = r(); P.m = a < 0.1 ? 0 : a < 0.45 ? 1 : 2;
  P.pitch = 46 + r() * 8;
  P.roof = Math.floor(r() * ROOFS.length); P.lac = Math.floor(r() * LACS.length);
  a = r(); P.form = a < 0.3 ? 'bell' : a < 0.5 ? 'chiangman' : a < 0.65 ? 'kukut' : a < 0.78 ? 'kutao' : a < 0.9 ? 'shan' : 'lao';
  P.stair = r() < 0.72; P.singha = r() < 0.6; P.kong = r() < 0.82; P.naga = r() < 0.9; P.hu = r() < 0.7;
  P.tung = 1 + Math.floor(r() * 3); P.tree = r() < 0.8; P.treeSeed = Math.floor(r() * 9999); P.sand = r(); P.cs = 0.74 + r() * 0.12;
  P.phase = r() * 7;
  return P;
}
/* the light of the hour from the sun's altitude, in steps of 1.5° so a layer is cut once per step: the tint runs orange (2°) → rose-violet (−3°) → navy (−8°), its weight 0 → 0.14 → 0.3 → 0.52 */
function light(S) {
  var alt = S.alt != null ? S.alt : S.night ? -10 : 30, a = Math.round(clamp(alt, -12, 12) / 1.5) * 1.5, tint, ta;
  if (a >= 2) { tint = hex('#ff8a40'); ta = 0.14 * (1 - sstep(2, 12, a)); }
  else if (a >= -3) { tint = mixc(hex('#ff8a40'), hex('#9a4a80'), sstep(2, -3, a)); ta = lerp(0.14, 0.3, sstep(2, -3, a)); }
  else { tint = mixc(hex('#9a4a80'), hex('#262e6a'), sstep(-3, -8, a)); ta = lerp(0.3, 0.52, sstep(-3, -8, a)); }
  var night = 1 - sstep(-7, -1, a), dusk = sstep(-8, 0, a) * (1 - sstep(4, 14, a));
  return { night: night, dusk: dusk, day: sstep(-2, 10, alt), tint: tint, ta: ta, key: a };
}
/* a colour as the tint leaves it (what source-atop does to the cut layers, for the parts drawn each frame) */
function lit(L, h) { return L.ta > 0.01 ? rgb(mixc(hex(h), L.tint, L.ta)) : h; }
/* where everything stands: the viharn's scale and centre, the chedi's, the sign's side */
function layout(S, Q) {
  var W = S.W, H = S.H, deck = S.deck, ph = S.phone, strip = H - deck, g = vGeom({ n: Q.n, m: Q.m, pitch: Q.pitch }), top = g.tiers[Q.n - 1].ya - 130;
  var by = deck + strip * 0.18, sc = min((by - H * (ph ? 0.05 : 0.07)) / -top, W * (ph ? 0.5 : 0.52) / (2 * (g.X + 70)));
  var half = (g.X + 70) * sc, vx = W * (0.5 - Q.dir * (ph ? 0.05 : 0.07)), Hv = -top * sc;
  var Hc = min(Hv * Q.cs, W * 0.4), cx = vx + Q.dir * min(W * 0.5 - 0.06 * W, half + Hc * 0.34 + (ph ? 18 : 26));
  return { sc: sc, by: by, vx: vx, half: half, Hv: Hv, Hc: Hc, cx: cx, cy: deck - H * 0.012 };
}

/* ---------------------------------------------------------------- layers cut once, then laid each frame */
var CACHE = [];
function tintLayer(q, cv, L) {
  if (L.ta < 0.01) return;
  q.save(); q.setTransform(1, 0, 0, 1, 0, 0); q.globalCompositeOperation = 'source-atop'; q.fillStyle = rgb(L.tint, L.ta); q.fillRect(0, 0, cv.width, cv.height); q.restore();
}
/* the gold of a layer as a soft white mask, one pixel per CSS pixel, and a few glints on it: a pixel is gold where g/r ≈ 0.6..0.8 and b/g < 0.8 */
function goldMask(cv, gw, gh, ma, seed) {
  var d, w = cv.width, h = cv.height;
  try { d = cv.getContext('2d').getImageData(0, 0, w, h); } catch (e) { return null; }
  var a = d.data, o = document.createElement('canvas'); o.width = w; o.height = h;
  var oq = o.getContext('2d'), im = oq.createImageData(w, h), b = im.data, cand = [];
  for (var i = 0, p = 0; i < a.length; i += 4, p++) {
    var r = a[i], g = a[i + 1], bl = a[i + 2];
    if (a[i + 3] < 200 || r < 140) continue;
    var k = sstep(0.55, 0.7, g / r) * (1 - sstep(0.7, 0.9, bl / (g + 1)));
    if (k <= 0.02) continue;
    b[i] = b[i + 1] = b[i + 2] = 255; b[i + 3] = k * 255;
    if (k > 0.9 && g > 150 && (p % 5) === 0 && ((p / w | 0) % 5) === 0) cand.push([(p % w) / ma, ((p / w) | 0) / ma]);
  }
  oq.putImageData(im, 0, 0);
  var m = document.createElement('canvas'); m.width = gw; m.height = gh; m.getContext('2d').drawImage(o, 0, 0, gw, gh);
  var r2 = rnd(seed), pts = [], n = min(9, cand.length); for (var j = 0; j < n; j++) pts.push(cand[Math.floor(r2() * cand.length)]);
  return { m: m, pts: pts };
}
/* cut a layer: draw(q) runs once on its own canvas laid out like the stage; the tint is laid over it; mask = also cut its gold */
function cut(S, key, box, draw, L, mask, hide) {
  var c = S.c, m = c.getTransform ? c.getTransform() : { a: 1, d: 1, e: 0, f: 0 };
  var k = key + '|' + [S.W, S.H, Math.round(S.deck), S.seed, S.phone ? 1 : 0, L.key, m.a, m.d, m.e, m.f, typeof document !== 'undefined' && document.fonts ? document.fonts.status : ''].join(','), e = null, i;
  for (i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    if (typeof document === 'undefined') { draw(c); return null; }
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.max(1, Math.ceil(box[2] * m.a) + 2), h = Math.max(1, Math.ceil(box[3] * m.d) + 2);
    var cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    e = { k: k, cv: cv, ox: ox, oy: oy, box: box, out: draw(q) };
    if (mask) { e.gm = goldMask(cv, Math.max(1, Math.ceil(box[2])), Math.max(1, Math.ceil(box[3])), m.a, S.seed + key.length); if (e.gm) { e.tc = document.createElement('canvas'); e.tc.width = e.gm.m.width; e.tc.height = e.gm.m.height; e.tq = e.tc.getContext('2d'); } }
    tintLayer(q, cv, L);
    CACHE.unshift(e); if (CACHE.length > 12) CACHE.pop();
  } else if (i) { CACHE.splice(i, 1); CACHE.unshift(e); }
  if (!hide) { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore(); }
  return e;
}
/* a soft round glow, cut once, laid with 'lighter' */
var GLOW = null;
function glow() {
  if (GLOW || typeof document === 'undefined') return GLOW;
  var g = document.createElement('canvas'); g.width = g.height = 64; var q = g.getContext('2d'), rg = q.createRadialGradient(32, 32, 0, 32, 32, 32);
  rg.addColorStop(0, 'rgba(255,255,255,1)'); rg.addColorStop(0.25, 'rgba(255,255,255,.45)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); q.fillStyle = rg; q.fillRect(0, 0, 64, 64);
  var t = document.createElement('canvas'); t.width = t.height = 64; var tq = t.getContext('2d'); tq.fillStyle = 'rgb(255,176,86)'; tq.fillRect(0, 0, 64, 64); tq.globalCompositeOperation = 'destination-in'; tq.drawImage(g, 0, 0);
  GLOW = t; return t;
}

/* ---------------------------------------------------------------- the ground, the trees, the chedi behind */
/* a tree: trunk and a canopy of overlapping discs in two greens over a darker underside, r the canopy's radius */
function tree(q, x, y, r, greens, seed) {
  var R = rnd(seed), i, cy = y - r * 1.15, dk = rgb(mixc(hex(greens[0]), [10, 30, 20], 0.45));
  q.fillStyle = '#4a3220'; q.fillRect(x - r * 0.07, y - r * 1.1, r * 0.14, r * 1.1);
  var ds = [];
  for (i = 0; i < 9; i++) { var a = i / 9 * TAU + R(); ds.push([x + cos(a) * r * 0.62, cy + sin(a) * r * 0.4, r * (0.5 + R() * 0.18)]); }
  q.fillStyle = dk; ds.forEach(function (d) { q.beginPath(); q.arc(d[0], d[1] + r * 0.09, d[2], 0, TAU); q.fill(); });
  ds.forEach(function (d, k) { q.fillStyle = greens[k % 2]; q.beginPath(); q.arc(d[0], d[1], d[2], 0, TAU); q.fill(); });
  q.fillStyle = greens[2]; q.beginPath(); q.arc(x, cy - r * 0.12, r * 0.6, 0, TAU); q.fill();
  q.fillStyle = 'rgba(255,255,220,.14)'; q.beginPath(); q.arc(x - r * 0.2, cy - r * 0.32, r * 0.34, 0, TAU); q.fill();
  q.fillStyle = 'rgba(255,255,220,.1)'; for (i = 0; i < 7; i++) { q.beginPath(); q.arc(x + (R() - 0.5) * r * 1.3, cy + (R() - 0.6) * r * 0.8, max(1, r * 0.06), 0, TAU); q.fill(); }
}
/* the layer behind the hall: the old city's wall, the tree line, the courtyard wall and sand, the river, a big tree at the far edge */
function drawBack(q, S, Q, Y, P) {
  var W = S.W, H = S.H, deck = S.deck, ph = S.phone, r = rnd(S.seed + 11), sandTop = deck - H * 0.085, i, x;
  if (P.oldCity) { var wy = sandTop - H * 0.2, m = max(4, H * 0.035), x0 = Q.dir > 0 ? W * 0.02 : W * 0.55, x1 = x0 + W * 0.43;
    q.fillStyle = '#a8432f'; q.beginPath(); q.moveTo(x0, sandTop); q.lineTo(x0, wy); for (x = x0; x < x1 - m; x += m * 2) { q.lineTo(x, wy - m * 0.8); q.lineTo(x + m, wy - m * 0.8); q.lineTo(x + m, wy); q.lineTo(x + m * 2, wy); } q.lineTo(x1, wy); q.lineTo(x1, sandTop); q.fill();
    q.strokeStyle = 'rgba(70,24,12,.35)'; q.lineWidth = 1; q.beginPath(); for (var yy = wy + m * 0.9; yy < sandTop; yy += m * 0.9) { q.moveTo(x0, yy); q.lineTo(x1, yy); } q.stroke(); }
  var far = ['#5b8a55', '#4d7d4a', '#6a9760'], near = ['#2f6b3a', '#3f8a4a', '#4a9a55'];
  for (x = -H * 0.1; x < W + H * 0.1; x += H * (0.1 + r() * 0.06)) tree(q, x, sandTop - H * 0.07, H * (0.1 + r() * 0.05), far, Math.floor(r() * 1e6));
  q.fillStyle = '#35603a'; q.fillRect(0, sandTop - H * 0.07, W, H * 0.07 + 1);
  for (x = -H * 0.05; x < W + H * 0.1; x += H * (0.13 + r() * 0.08)) tree(q, x, sandTop - H * 0.01, H * (0.09 + r() * 0.05), near, Math.floor(r() * 1e6));
  var wl = H * 0.045;
  q.fillStyle = '#efe4cf'; q.fillRect(0, sandTop - wl, W, wl); q.fillStyle = Y.lacw; q.fillRect(0, sandTop - wl, W, max(1.5, wl * 0.22));
  q.fillStyle = 'rgba(70,50,30,.2)'; q.fillRect(0, sandTop - wl * 0.1, W, wl * 0.1 + 1);
  for (x = W * 0.03; x < W; x += W * 0.07) { q.fillStyle = 'rgba(120,100,70,.28)'; q.fillRect(x, sandTop - wl * 0.78, max(1, wl * 0.08), wl * 0.78); }
  var gg = q.createLinearGradient(0, sandTop, 0, H); gg.addColorStop(0, '#dcc79e'); gg.addColorStop(1, '#c7a777'); q.fillStyle = gg; q.fillRect(0, sandTop, W, H - sandTop);
  q.fillStyle = 'rgba(120,90,50,.22)'; for (i = 0; i < (ph ? 22 : 60); i++) { var sx = r() * W, sy = sandTop + (H - sandTop) * (0.15 + 0.8 * r()); q.fillRect(sx, sy, 1 + r() * 3, 1); }
  q.fillStyle = 'rgba(70,45,25,.2)'; q.beginPath(); q.ellipse(Y.vx, Y.by + 3 * Y.sc, Y.half * 0.98, max(3, 11 * Y.sc), 0, 0, TAU); q.fill();
  var y0 = Y.by + 22 * Y.sc, hw0 = 82 * Y.sc, hw1 = hw0 + (H - y0) * 0.45;
  q.fillStyle = '#ebdfc4'; q.beginPath(); q.moveTo(Y.vx - hw0, y0); q.lineTo(Y.vx + hw0, y0); q.lineTo(Y.vx + hw1, H); q.lineTo(Y.vx - hw1, H); q.fill();
  q.strokeStyle = 'rgba(120,90,50,.28)'; q.lineWidth = 1; q.beginPath(); for (i = 1; i < 4; i++) { var py = lerp(y0, H, i / 4), pw = lerp(hw0, hw1, i / 4); q.moveTo(Y.vx - pw, py); q.lineTo(Y.vx + pw, py); } q.stroke();
  if (P.river && P.river.m != null && P.river.m < 400) { var ry = deck + (H - deck) * 0.62, rh = (H - deck) * 0.36;
    q.fillStyle = '#4b8fc9'; q.beginPath(); q.moveTo(0, ry + 1); for (x = 0; x <= W; x += 10) q.lineTo(x, ry + sin(x * 0.02) * 1.2); q.lineTo(W, ry + rh); q.lineTo(0, ry + rh); q.fill();
    q.fillStyle = 'rgba(255,255,255,.35)'; for (i = 0; i < 9; i++) q.fillRect(r() * W, ry + rh * (0.3 + 0.5 * r()), 10 + r() * 14, 1.2); }
  if (Q.tree) { var tx = Q.dir > 0 ? W * 0.045 : W * 0.955, tr = H * 0.2; tree(q, tx, sandTop + H * 0.05, tr, near, Q.treeSeed); }
}
/* the chedi alone, on its own layer so its gold can glint */
function drawChedi(q, S, Q, Y) {
  q.fillStyle = 'rgba(70,45,25,.22)'; q.beginPath(); q.ellipse(Y.chx, Y.chy + 1, profile(CHEDI[Q.form])[0].w * Y.Hc * 0.56, max(2, Y.Hc * 0.022), 0, 0, TAU); q.fill();
  var Pn = Pen(q); Pn.minlw = 0.6; chedi(Pn, Y.chx, Y.chy, Y.Hc, CHEDI[Q.form], Q.form); }
/* the name board on two posts, Thai over English, the sign's own width measured first */
function signSize(c, P, u) {
  var th = P.nameTh || P.name || '', en = P.nameEn && P.nameEn !== th ? P.nameEn : '', f1 = Math.max(11, u * 0.19), f2 = Math.max(9, u * 0.13);
  c.save(); c.font = '800 ' + Math.round(f1) + 'px ' + FONT; var w1 = c.measureText(th.length > 34 ? th.slice(0, 33) + '…' : th).width;
  c.font = '700 ' + Math.round(f2) + 'px ' + FONT; var w2 = en ? c.measureText(en.length > 40 ? en.slice(0, 39) + '…' : en).width : 0; c.restore();
  return { w: Math.min(Math.max(w1, w2) + u * 0.5, u * 7), h: en ? f1 + f2 + u * 0.18 : f1 + u * 0.16 };
}

/* a line cut with … to fit a width, backed off past a leading vowel, space or hyphen at the end */
function fit(c, str, font, w, maxc) {
  c.save(); c.font = font; var n = Math.min(str.length, maxc);
  if (str.length > maxc || c.measureText(str).width > w) {
    if (str.length > maxc) n = maxc - 1;
    while (n > 3 && c.measureText(str.slice(0, n) + '…').width > w) n--;
    while (n > 3 && /[เแโใไ\s\-,(]$/.test(str.charAt(n - 1))) n--;
    str = str.slice(0, n) + '…';
  }
  c.restore(); return str;
}
/* ---------------------------------------------------------------- parts drawn each frame */
var TUNGC = [['#c2281b', '#ffd766', '#ffffff', '#16917a', '#e8b02a', '#ff5c8a'], ['#16917a', '#ffd766', '#ffffff', '#c2281b', '#e8b02a', '#2f6fd8']];
/* a tung (ตุง) on bamboo: 22 cloth bands, x = (6 + 26w)v² + (5 + 10w)v·sin(7v − (2.4 + 2w)t + φ) down the length v */
function tungPole(c, x, yG, h, t, wind, seed, L, minlw) {
  var pole = lit(L, '#c9a46a'), len = h * 0.62, wd = 26, bands = 22, top = yG - h + 4, cols = TUNGC[seed % 2].map(function (h2) { return lit(L, h2); }), k, edge = lit(L, '#c9a46a');
  c.save(); c.lineCap = 'round'; c.strokeStyle = pole; c.lineWidth = max(4, minlw * 3);
  c.beginPath(); c.moveTo(x, yG); c.lineTo(x, yG - h); c.stroke();
  c.lineWidth = max(3, minlw * 2.4); c.beginPath(); c.moveTo(x - 2, yG - h); c.quadraticCurveTo(x + 18, yG - h - 22, x + 46, yG - h - 18); c.stroke();
  function dx(v) { return (wind * 26 + 6) * v * v + (5 + wind * 10) * v * sin(v * 7 - t * (2.4 + wind * 2) + seed); }
  for (k = 0; k < bands; k++) { var v0 = k / bands, v1 = (k + 1) / bands, y0 = top + v0 * len, y1 = top + v1 * len, a = dx(v0), b = dx(v1), w0 = wd * (1 - v0 * 0.15), w1 = wd * (1 - v1 * 0.15);
    c.fillStyle = k % 4 === 3 ? lit(L, '#1b0f0b') : cols[(k + seed) % cols.length];
    c.beginPath(); c.moveTo(x + 40 - w0 / 2 + a, y0); c.lineTo(x + 40 + w0 / 2 + a, y0); c.lineTo(x + 40 + w1 / 2 + b, y1 + 0.6); c.lineTo(x + 40 - w1 / 2 + b, y1 + 0.6); c.closePath(); c.fill();
    if (k % 4 === 3) { c.strokeStyle = edge; c.lineWidth = max(2, minlw); c.beginPath(); c.moveTo(x + 40 - w0 / 2 - 3 + a, y0); c.lineTo(x + 40 + w0 / 2 + 3 + a, y0); c.stroke(); } }
  var tail = dx(1); c.fillStyle = lit(L, '#c2281b'); c.beginPath(); c.moveTo(x + 30 + tail, top + len); c.lineTo(x + 40 + tail, top + len + 30); c.lineTo(x + 50 + tail, top + len); c.closePath(); c.fill();
  c.restore();
}
/* a four-point star, long arm r */
function twinkle(c, x, y, r) {
  c.beginPath(); c.moveTo(x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.fill();
}
/* a band of light running across a layer's gold: centre x = (1.5u − 0.25)·width with u = t/period + phase, tilted 20°, drawn only where
   the band is (its box), clipped to the gold with the mask */
function band(S, e, t, phase, bw, c0, c1, amp, period) {
  var c = S.c, q = e.tq, w = e.tc.width, h = e.tc.height, u = (t / period + phase) % 1, cxp = lerp(-0.25, 1.25, u) * w, hb = w * bw, reach = hb + h * 0.37 + 2;
  var x0 = clamp(Math.floor(cxp - reach), 0, w), x1 = clamp(Math.ceil(cxp + reach), 0, w), bwid = x1 - x0; if (bwid < 2) return;
  q.globalCompositeOperation = 'source-over'; q.clearRect(x0, 0, bwid, h);
  q.save(); q.beginPath(); q.rect(x0, 0, bwid, h); q.clip(); q.translate(cxp, h * 0.4); q.rotate(-0.35);
  var g = q.createLinearGradient(-hb, 0, hb, 0); g.addColorStop(0, 'rgba(' + c0 + ',0)'); g.addColorStop(0.5, 'rgba(' + c1 + ',' + amp.toFixed(3) + ')'); g.addColorStop(1, 'rgba(' + c0 + ',0)');
  q.fillStyle = g; q.fillRect(-hb, -h * 1.2, hb * 2, h * 2.4); q.restore();
  q.globalCompositeOperation = 'destination-in'; q.drawImage(e.gm.m, x0, 0, bwid, h, x0, 0, bwid, h);
  c.drawImage(e.tc, x0, 0, bwid, h, e.box[0] + x0, e.box[1], bwid, h);
}
/* the lamps' glow on the gold: baked once into e.lg (glows clipped to the gold), laid at a flickering alpha */
function lampLight(S, e, lamps, t, k) {
  var w = e.tc.width, h = e.tc.height, gl = glow(); if (!gl) return;
  if (!e.lg) {
    var lg = document.createElement('canvas'); lg.width = w; lg.height = h; var q = lg.getContext('2d'), x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    lamps.forEach(function (l) { var lx = l.x - e.box[0], ly = l.y - e.box[1]; q.drawImage(gl, lx - l.r, ly - l.r, l.r * 2, l.r * 2); x0 = min(x0, lx - l.r); y0 = min(y0, ly - l.r); x1 = max(x1, lx + l.r); y1 = max(y1, ly + l.r); });
    q.globalCompositeOperation = 'destination-in'; q.drawImage(e.gm.m, 0, 0);
    e.lg = lg; e.lb = [clamp(Math.floor(x0), 0, w), clamp(Math.floor(y0), 0, h), 0, 0]; e.lb[2] = clamp(Math.ceil(x1), 0, w) - e.lb[0]; e.lb[3] = clamp(Math.ceil(y1), 0, h) - e.lb[1];
  }
  var b = e.lb; if (b[2] < 2 || b[3] < 2) return;
  var c = S.c; c.save(); c.globalAlpha = clamp(k * (0.88 + 0.12 * sin(t * 6) * sin(t * 2.1 + 1)) * 1.15, 0, 1);
  c.drawImage(e.lg, b[0], b[1], b[2], b[3], e.box[0] + b[0], e.box[1] + b[1], b[2], b[3]); c.restore();
}
/* the light on a layer's gold: by day a warm band, after dark a pale moonlit band and the lamps' glow */
function shine(S, e, L, t, lamps, phase, bw, amp) {
  if (!e || !e.gm) return;
  var sun = L.day * (1 - L.night);
  if (sun > 0.08) band(S, e, t, phase, bw, '255,238,170', '255,248,214', amp * sun, 7);
  if (L.night > 0.2) band(S, e, t, (phase + 0.5) % 1, bw * 1.2, '170,196,255', '190,212,255', 0.3 * amp * L.night, 9);
  if (lamps.length && (L.night > 0.05 || L.dusk > 0.05)) lampLight(S, e, lamps, t, max(L.night, L.dusk * 0.6));
}

/* ---------------------------------------------------------------- the scene */
function wat(S) {
  var c = S.c, P = S.place || {}, t = S.t / 1000, W = S.W, H = S.H, deck = S.deck, ph = S.phone, Q = plan(S), L = light(S), Y = layout(S, Q), sc = Y.sc, vx = Y.vx, by = Y.by, i, k;
  S.noMagic = true;
  var pal = ROOFS[Q.roof], lac = LACS[Q.lac]; C.tile = pal[0]; C.tile2 = pal[1]; C.lac = lac[0]; C.lac2 = lac[1]; C.lacD = lac[2];
  var minlw = (ph ? 0.85 : 0.7) / sc, Yb = { chx: Y.cx, chy: Y.cy, Hc: Y.Hc, lacw: lac[0], vx: vx, by: by, sc: sc, half: Y.half };
  var o = { n: Q.n, m: Q.m, pitch: Q.pitch, t: 1, glow: L.night, orn: { chofa: 1, naga: Q.naga ? 1 : 0, raka: 1, hong: 1, kong: Q.kong ? 1 : 0, hu: Q.hu ? 1 : 0, glass: 1, stair: Q.stair ? 1 : 0, singha: Q.singha ? 1 : 0, bells: 1 } };
  var hb = [vx - Y.half - 14 * sc, by + (-Y.Hv - 40 * sc), Y.half * 2 + 28 * sc, Y.Hv + 40 * sc + 40 * sc], g;
  /* behind: the compound, the chedi */
  cut(S, 'wb', [0, H * 0.3, W, H * 0.7], function (q) { drawBack(q, S, Q, Yb, P); }, L, false);
  var ec = cut(S, 'wc', [Y.cx - Y.Hc * 0.42, Y.cy - Y.Hc * 1.15, Y.Hc * 0.84, Y.Hc * 1.2], function (q) { drawChedi(q, S, Q, Yb); }, L, true);
  /* tung on bamboo between the hall and the chedi, and beyond */
  var wind = 0.35 + 0.15 * sin(t * 0.4 + Q.phase), ts = Y.Hv * 0.7 / 560, tx = [vx + Q.dir * (Y.half + (ph ? 6 : 12)), Q.dir > 0 ? W * 0.97 - 46 * ts : W * 0.03, vx - Q.dir * (Y.half + 10)];
  for (i = min(Q.tung, ph ? 2 : 3) - 1; i >= 0; i--) {
    c.save(); c.translate(tx[i], deck + (H - deck) * 0.1); c.scale(ts, ts); tungPole(c, 0, 0, i === 0 ? 560 : i === 1 ? 470 : 380, t + i * 1.7, wind, i * 2 + 1 + (Q.treeSeed % 3), L, 0.8 / ts); c.restore(); }
  /* the hall */
  var ev = cut(S, 'wv', hb, function (q) {
    q.save(); q.translate(vx, by); q.scale(sc, sc);
    var Pn = Pen(q); Pn.minlw = minlw; g = viharn(Pn, o); q.restore(); return g;
  }, L, true);
  g = ev && ev.out || vGeom(o); if (!ev || !ev.out) { g.bells = []; g.lamps = []; }
  /* bells swing */
  var Pb = Pen(c), bl = 1 - 0.6 * L.night * 0.8;
  for (i = 0; i < g.bells.length; i++) { var b = g.bells[i]; c.save(); c.translate(vx, by); c.scale(sc, sc); Pb.minlw = minlw; eaveBell(Pb, b.x, b.y, b.s, 0.09 * sin(t * 1.7 + b.ph) + 0.04 * sin(t * 3.1 + b.ph * 2), bl); c.restore(); }
  /* the light on the gold */
  var lamps = []; if (L.night > 0.05 || L.dusk > 0.05) for (i = 0; i < g.lamps.length; i++) lamps.push({ x: vx + g.lamps[i].x * sc, y: by + g.lamps[i].y * sc, r: 105 * sc });
  if (lamps.length) lamps.push({ x: vx, y: by - 90 * sc, r: 150 * sc });
  shine(S, ev, L, t, lamps, Q.phase / 7, 0.07, 0.8);
  var cl = []; if (L.night > 0.05) cl.push({ x: Y.cx, y: Y.cy - Y.Hc * 0.42, r: Y.Hc * 0.55 });
  shine(S, ec, L, t + 3, cl, (Q.phase / 7 + 0.37) % 1, 0.1, 0.4);
  /* twinkles on the gold */
  c.save(); c.globalCompositeOperation = 'lighter'; var tw = max(L.day * (1 - L.night), L.night * 0.7);
  [ev, ec].forEach(function (e, j) { if (!e || !e.gm) return; e.gm.pts.forEach(function (p, n) { if (ph && n > 4) return; var a = Math.pow(max(0, sin(t * (1.6 + 0.3 * (n % 3)) + n * 2.1 + j)), 8) * tw; if (a < 0.05) return;
    c.fillStyle = 'rgba(255,246,206,' + a.toFixed(3) + ')'; twinkle(c, e.box[0] + p[0], e.box[1] + p[1], (ph ? 2.2 : 5) * (0.6 + a * 0.6)); }); });
  /* lamps and the door glow after dark; fireflies */
  var gl = glow();
  if (L.night > 0.05 && gl) {
    var fl = 0.82 + 0.18 * sin(t * 5) * sin(t * 1.7 + 1);
    c.globalAlpha = L.night * 0.5 * fl; c.drawImage(gl, vx - 230 * sc, by - 315 * sc, 460 * sc, 250 * sc);
    c.globalAlpha = L.night * 0.4; c.drawImage(gl, vx - 130 * sc, by - 170 * sc, 260 * sc, 200 * sc);
    c.globalAlpha = L.night * 0.34; c.drawImage(gl, vx - 260 * sc, by - 30 * sc, 520 * sc, 120 * sc);
    var rf = rnd(S.seed + 5), nf = ph ? 6 : 12;
    for (i = 0; i < nf; i++) { var fx = (rf() + 0.03 * sin(t * (0.5 + rf()) + i)) * W, fy = deck - H * (0.02 + 0.3 * rf()) + 0.03 * H * sin(t * 0.7 + i * 2), fa = L.night * (0.4 + 0.6 * Math.pow(max(0, sin(t * (1.2 + rf()) + i * 3)), 2));
      c.globalAlpha = fa; c.fillStyle = 'rgb(210,255,140)'; c.beginPath(); c.arc(fx, fy, ph ? 1.2 : 1.7, 0, TAU); c.fill(); if (i % 2) { c.globalAlpha = fa * 0.4; c.drawImage(gl, fx - 6, fy - 6, 12, 12); } }
    c.globalAlpha = 1;
  }
  c.restore();
  if (L.night > 0.5 && K.khomLoi) K.khomLoi(S, ph ? 2 : 3);
  /* swallows by day */
  if (L.day * (1 - L.night) > 0.2) { c.strokeStyle = 'rgba(27,15,11,' + (0.75 * L.day).toFixed(2) + ')'; c.lineWidth = ph ? 1 : 1.4; c.lineCap = 'round';
    for (i = 0; i < 3; i++) { var a0 = t * (0.25 + 0.07 * i) + i * 2 + Q.phase, bx = W * (0.25 + 0.25 * i) + cos(a0) * W * 0.13, byy = H * (0.14 + 0.07 * i) + sin(a0 * 2) * H * 0.04, f = sin(t * 12 + i) * 3, z = ph ? 0.6 : 1;
      c.beginPath(); c.moveTo(bx - 7 * z, byy - f * z); c.quadraticCurveTo(bx - 3 * z, byy - 2 * z, bx, byy); c.quadraticCurveTo(bx + 3 * z, byy - 2 * z, bx + 7 * z, byy - f * z); c.stroke(); } }
  /* the name board in front, on the side away from the chedi, its words cut to the room beside the hall */
  if (P.nameTh || P.name) {
    var u = S.hh * (ph ? 0.78 : 1), free = Q.dir > 0 ? vx - Y.half : W - vx - Y.half, G = by + (ph ? 1 : 2);
    var th = P.nameTh || P.name, en = P.nameEn && P.nameEn !== th ? P.nameEn : '', f1 = Math.max(11, u * 0.19), f2 = Math.max(9, u * 0.13), kr = (f1 + f2 + u * 0.18) * 0.9;
    var cap = min(W * 0.44, free + Y.half * (ph ? 0.5 : 0.3)) - u * 0.5 - 2 * kr;
    th = fit(c, th, '800 ' + Math.round(f1) + 'px ' + FONT, cap, 34); en = en ? fit(c, en, '700 ' + Math.round(f2) + 'px ' + FONT, cap, 40) : '';
    var P2 = { nameTh: th, nameEn: en, name: th, t: P.t }, z = signSize(c, P2, u), pad = z.w / 2 + kr + 2, sx = Q.dir > 0 ? max(pad, free / 2) : W - max(pad, free / 2);
    sx = clamp(sx, pad, W - pad);
    var top = G - u * 0.36 - z.h, bx0 = sx - z.w / 2 - u * 0.18, bx1 = sx + z.w / 2 + u * 0.18, sb = [bx0 - kr - 4, top - u * 0.3, bx1 - bx0 + 2 * kr + 8, G - top + u * 0.34];
    var es = cut(S, 'ws' + th + en, sb, function (q) {
      var wood = lit(L, '#6a4026'), pw = max(2, u * 0.09);
      q.fillStyle = wood; q.fillRect(bx0 - pw / 2, top - u * 0.1, pw, G - top + u * 0.1); q.fillRect(bx1 - pw / 2, top - u * 0.1, pw, G - top + u * 0.1);
      q.fillRect(bx0 - u * 0.1, top - u * 0.14, bx1 - bx0 + u * 0.2, max(2, u * 0.07));
      return K.sign(q, sx, top + u * 0.02, P2, u, lit(L, '#6a3a1e'), null);
    }, { key: L.key, ta: 0, tint: L.tint }, false);
    var z2 = es && es.out; if (z2) S.hits.push({ k: 'place', x0: z2.x0, x1: z2.x1, y0: z2.y0, y1: z2.y1 });
  }
}
D.addScene('wat', wat, null, 'x = A·(y/L)·sin(ky − ωt)');
})();
