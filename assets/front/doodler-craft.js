/* Crafts and customs of the north for the auto-doodler (Nan, 2026-10-02: "Do one for
   bamboo tattooing … Many other topics"; "make it magically lanna all of it").
   'sakyant'    sak yant under a sala: the ajarn taps the yant in with the long needle, a
                dot a tap, d = A·|sin ωt|; a lens shows the back up close; the unalome comes
                last, and the finished yant wakes in gold. The design is a schematic of a
                nine-spire or five-row yant: loops, not letters.
   'muaythai'   a temple-fair ring: the wai khru ram muay, then the bout, kicks on
                θ = θ₀·sin²(πt/T); pi chawa and drum at the ringside
   'takbat'     by day the alms round, monks walking past people kneeling with sticky
                rice; by night wian thian, candles carried around the chedi on an ellipse
   'massage'    tok sen and the herbal compress: the hammer taps the peg, a ring runs along
                the sen line, y = A·e^(−λt)·sin(kx − ωt)
   'elephants'  bath time in the river at a sanctuary: a trunk on a travelling wave, spray
                and buckets on parabolas
   'hotspring'  San Kamphaeng: the geyser on parabolas, eggs in baskets in the boiling pool,
                feet in the warm channel
   'cooking'    a farm cooking class: woks tossed, the pestle in the mortar, |sin ωt| */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU, person = K.person, POSE = K.POSE;
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

/* ---------------------------------------------------------------- shared pieces */
/* the skeleton's joints, worked as doodler.js works them */
function joints(x, y, h, P, dir) {
  var seat = P.seat || 0.47, lean = P.lean || 0;
  function pt(o, a, l) { return [o[0] + dir * Math.sin(a) * l, o[1] + Math.cos(a) * l]; }
  var hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33], L = P.legs, A = P.arms;
  var k1 = pt(hip, L[0], h * 0.24), k2 = pt(hip, L[2], h * 0.24), e1 = pt(sh, A[0], h * 0.17), e2 = pt(sh, A[2], h * 0.17);
  return { hip: hip, sh: sh, head: [sh[0] + dir * Math.sin(lean) * h * 0.14, sh[1] - Math.cos(lean) * h * 0.14], k1: k1, f1: pt(k1, L[0] + L[1], h * 0.23), k2: k2, f2: pt(k2, L[2] + L[3], h * 0.23),
    e1: e1, w1: pt(e1, A[0] + A[1], h * 0.16), e2: e2, w2: pt(e2, A[2] + A[3], h * 0.16) };
}
/* an arm that reaches a point: two bones, the elbow below the line (law of cosines) */
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
/* an arm drawn on its own, over things the body sits behind */
function arm(c, sh, T, h, dir, sleeve, skin) {
  var a = solve(sh, T, h * 0.17, h * 0.16, dir), e = [sh[0] + dir * Math.sin(a[0]) * h * 0.17, sh[1] + Math.cos(a[0]) * h * 0.17];
  var w = [e[0] + dir * Math.sin(a[0] + a[1]) * h * 0.16, e[1] + Math.cos(a[0] + a[1]) * h * 0.16], m = [lerp(e[0], w[0], 0.55), lerp(e[1], w[1], 0.55)];
  c.save(); c.lineCap = 'round';
  c.lineWidth = Math.max(2, h * 0.075); c.strokeStyle = sleeve; c.beginPath(); c.moveTo(sh[0], sh[1]); c.lineTo(e[0], e[1]); c.lineTo(m[0], m[1]); c.stroke();
  c.lineWidth = Math.max(1.8, h * 0.064); c.strokeStyle = skin; c.beginPath(); c.moveTo(m[0], m[1]); c.lineTo(w[0], w[1]); c.stroke();
  c.restore();
  return w;
}
/* a candle; the flame a teardrop, h = h₀(1 + 0.15·sin(t/90 + k)) */
function candle(c, x, y, ht, t, k, wax) {
  var fl = 1 + 0.15 * Math.sin(t / 90 + k * 2.1) + 0.07 * Math.sin(t / 37 + k), fy = y - ht, fh = ht * 0.5 * fl, fw = Math.max(1.6, ht * 0.13);
  c.fillStyle = wax || '#f5ead2'; c.fillRect(x - fw * 0.75, fy, fw * 1.5, ht);
  K.lanternGlow(c, x, fy - fh * 0.45, Math.max(2.5, fh * 0.45), 42, 0.85);
  c.fillStyle = '#ffc94a'; c.beginPath(); c.moveTo(x, fy - fh); c.quadraticCurveTo(x + fw, fy - fh * 0.25, x, fy); c.quadraticCurveTo(x - fw, fy - fh * 0.25, x, fy - fh); c.fill();
  c.fillStyle = '#fff6d0'; c.beginPath(); c.ellipse(x, fy - fh * 0.3, fw * 0.35, fh * 0.22, 0, 0, TAU); c.fill();
}
/* incense: the sticks, and smoke curling as x = A·sin(ky − ωt) */
function incense(c, x, y, len, t, k, n) {
  c.lineWidth = 1; c.lineCap = 'round';
  for (var i = 0; i < n; i++) {
    var sx = x + (i - (n - 1) / 2) * 2.2, tx = sx + (i - (n - 1) / 2) * 1.2, ty = y - len;
    c.strokeStyle = '#b5532f'; c.beginPath(); c.moveTo(sx, y); c.lineTo(tx, ty); c.stroke();
    c.fillStyle = '#ff7a3a'; c.beginPath(); c.arc(tx, ty, 1.1, 0, TAU); c.fill();
    c.strokeStyle = 'rgba(240,236,228,.45)'; c.beginPath();
    for (var j = 0; j <= len * 1.6; j += 3) { var xx = tx + Math.sin(j * 0.11 - t / 650 + k + i) * (1 + j * 0.07); j ? c.lineTo(xx, ty - j) : c.moveTo(xx, ty); } c.stroke();
  }
}
/* the khan tang (ขันตั้ง), the teacher's bowl on its foot: banana-leaf cones, marigold and
   jasmine, two candles, incense; the Lanna word where the centre says khan khru */
function khanTang(c, x, y, s, t, night) {
  var metal = night ? '#b8872f' : '#d4a23f';
  paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.26, y); q.lineTo(x + s * 0.26, y); q.lineTo(x + s * 0.1, y - s * 0.1); q.lineTo(x + s * 0.07, y - s * 0.28); q.lineTo(x + s * 0.42, y - s * 0.3);
    q.quadraticCurveTo(x + s * 0.4, y - s * 0.6, x, y - s * 0.6); q.quadraticCurveTo(x - s * 0.4, y - s * 0.6, x - s * 0.42, y - s * 0.3); q.lineTo(x - s * 0.07, y - s * 0.28); q.lineTo(x - s * 0.1, y - s * 0.1); q.closePath(); }, metal, 1.1);
  c.strokeStyle = 'rgba(255,240,190,.6)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - s * 0.38, y - s * 0.36); c.lineTo(x + s * 0.38, y - s * 0.36); c.stroke();
  var top = y - s * 0.58;
  [-0.27, -0.09, 0.09, 0.27].forEach(function (k, i) { c.fillStyle = i % 2 ? '#3f8a4a' : '#5aa35a'; c.beginPath(); c.moveTo(x + k * s - s * 0.08, top); c.lineTo(x + k * s, top - s * 0.42); c.lineTo(x + k * s + s * 0.08, top); c.fill(); });
  [[-0.32, 0.02], [-0.16, -0.05], [0.18, -0.04], [0.33, 0.02], [0, -0.02]].forEach(function (p, i) {
    c.fillStyle = i % 2 ? '#f29a1f' : '#f7b52c'; c.beginPath(); c.arc(x + p[0] * s, top + p[1] * s, s * 0.08, 0, TAU); c.fill();
    c.fillStyle = '#fffaf0'; c.beginPath(); c.arc(x + p[0] * s + s * 0.05, top + p[1] * s - s * 0.07, s * 0.035, 0, TAU); c.fill();
  });
  candle(c, x - s * 0.12, top - s * 0.1, s * 0.34, t, 1, '#f3e3b0'); candle(c, x + s * 0.12, top - s * 0.1, s * 0.34, t, 2, '#f3e3b0');
  incense(c, x, top - s * 0.05, s * 0.5, t, 3, 3);
}
/* steam: puffs that rise, swell and thin; x = x₀ + A·sin(ky − ωt) */
function steam(c, x, y, hh, t, k, n, rise, a0, wide) {
  for (var i = 0; i < n; i++) {
    var u = (t / 2600 + i / n + k * 0.37) % 1, yy = y - u * rise, xx = x + Math.sin(u * 5 - t / 900 + k) * hh * 0.1 * (0.3 + u) * (wide || 1), r = hh * (0.04 + 0.11 * u) * (wide || 1);
    c.fillStyle = 'rgba(255,255,255,' + ((a0 || 0.45) * Math.sin(Math.PI * u)).toFixed(3) + ')'; c.beginPath(); c.arc(xx, yy, r, 0, TAU); c.fill();
  }
}
/* gold curls rising: a chant, a blessing, a spell in the air */
function curls(c, x, y, hh, t, n, k) {
  c.lineWidth = 1.2; c.lineCap = 'round';
  for (var i = 0; i < n; i++) {
    var u = (t / 2400 + i / n + k) % 1, cx = x + Math.sin(u * 4 + i) * hh * 0.12, cy = y - u * hh * 0.7, r = hh * 0.05 * (0.6 + u * 0.6);
    c.strokeStyle = 'rgba(255,214,90,' + (0.9 * Math.sin(Math.PI * u)).toFixed(3) + ')'; c.beginPath();
    for (var a = 0; a < 9; a += 0.5) { var rr = r * a / 9; a ? c.lineTo(cx + Math.cos(a + t / 400) * rr, cy + Math.sin(a + t / 400) * rr) : c.moveTo(cx, cy); } c.stroke();
  }
}
function bodyBox(S, top) { S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H }); }

/* ---------------------------------------------------------------- sak yant
   The design, in unit space, as strokes the ajarn taps in order: the frame or the rows,
   then the unalome last — the spiral, the zigzag, the straight line (r = aθ for the coil).
   Rows of script are drawn as loops, a prolate trochoid, x = aθ − b·sin θ, y = b·cos θ:
   a script's look, no letters. */
var YANT = {};
function yant(kind) {
  if (YANT[kind]) return YANT[kind];
  var strokes = [], i, th;
  function troch(x0, y0, ang, len, n) {
    var pts = [], a = len / (n * TAU), b = a * 2.3, ca = Math.cos(ang), sa = Math.sin(ang);
    for (th = 0; th <= n * TAU + 0.01; th += 0.32) { var u = a * th - b * Math.sin(th), v = b - b * Math.cos(th); pts.push([x0 + ca * u - sa * v, y0 + sa * u + ca * v]); }
    return pts;
  }
  if (kind === 'nine') {   /* เก้ายอด, nine spires over a frame of three rows */
    var hs = [0.22, 0.32, 0.42, 0.52, 0.68, 0.52, 0.42, 0.32, 0.22], sp = [];
    for (i = 0; i < 9; i++) { var xl = -0.85 + i * 0.189, xm = xl + 0.0945, xr = xl + 0.189;
      for (var f = 0; f <= 1.001; f += 0.25) sp.push([lerp(xl, xm, f), 0.05 - hs[i] * Math.sin(f * Math.PI / 2) * (0.6 + 0.4 * f * f)]);
      for (f = 0.25; f <= 1.001; f += 0.25) sp.push([lerp(xm, xr, f), 0.05 - hs[i] * Math.cos(f * Math.PI / 2) * (0.6 + 0.4 * (1 - f) * (1 - f))]); }
    strokes.push(sp);
    strokes.push([[-0.85, 0.05], [-0.85, 0.85], [0.85, 0.85], [0.85, 0.05], [-0.85, 0.05]]);
    for (i = 0; i < 3; i++) strokes.push(troch(-0.72, 0.13 + i * 0.24, 0, 1.44, 8));
    for (i = 0; i < 9; i++) if (i % 2 === 0) strokes.push([[-0.85 + i * 0.189 + 0.0945, -0.02 - hs[i] * 0.45]]);
  } else {                 /* ห้าแถว, five rows fanned over the shoulder blades */
    for (i = 0; i < 5; i++) { var tilt = (i - 2) * 0.1; strokes.push(troch(-0.62 + i * 0.31 + Math.sin(tilt) * 0.9, 0.85, -Math.PI / 2 + tilt, 1.15 + (i % 2 ? 0 : 0.12) - Math.abs(i - 2) * 0.08, 6)); }
  }
  /* the unalome: the coil, the zigzag, the line, the dots */
  var un = [], cy0 = kind === 'nine' ? -0.78 : -0.42;
  for (th = 0; th <= 2.4 * TAU; th += 0.35) { var r = 0.012 * th; un.push([Math.sin(th) * r, cy0 - Math.cos(th) * r]); }
  var zy = cy0 - 0.012 * 2.4 * TAU;
  for (i = 0; i < 3; i++) { un.push([0.07, zy - 0.06 - i * 0.12]); un.push([-0.07, zy - 0.12 - i * 0.12]); }
  un.push([0, zy - 0.42]); un.push([0, zy - 0.62]);
  strokes.push(un); strokes.push([[0, zy - 0.7]]); strokes.push([[0, zy - 0.77]]);
  /* every stroke cut into taps, about 0.07 apart */
  var dots = [], ends = [];
  strokes.forEach(function (s, si) {
    if (s.length === 1) dots.push([s[0][0], s[0][1], si]);
    for (var j = 1; j < s.length; j++) { var a = s[j - 1], b = s[j], L = Math.hypot(b[0] - a[0], b[1] - a[1]), m = Math.max(1, Math.round(L / 0.07));
      for (var q = j === 1 ? 0 : 1; q <= m; q++) dots.push([lerp(a[0], b[0], q / m), lerp(a[1], b[1], q / m), si]); }
    ends.push(dots.length);
  });
  var y0 = 1, y1 = -1, x0 = 1, x1 = -1; dots.forEach(function (d) { y0 = Math.min(y0, d[1]); y1 = Math.max(y1, d[1]); x0 = Math.min(x0, d[0]); x1 = Math.max(x1, d[0]); });
  return (YANT[kind] = { kind: kind, strokes: strokes, dots: dots, ends: ends, top: y0, bot: y1, x0: x0, x1: x1 });
}
/* the yant at a scale: the traced stencil faint, the tapped dots in lampblack, a finished
   stroke lit gold; wake (0 … 1) lights the whole. What is finished is cut once onto a
   card of its own and laid down each frame. */
var CARDS = {};
function drawYant(c, Y, cx, cy, sc, n, wake, t, big) {
  var s, done = 0, i;
  for (s = 0; s < Y.ends.length; s++) if (Y.ends[s] <= n) done = s + 1;
  var dpr = c.getTransform ? c.getTransform().a : 1, pad = sc * 0.2, ox = Y.x0 * sc - pad, oy = Y.top * sc - pad, w = (Y.x1 - Y.x0) * sc + pad * 2, h = (Y.bot - Y.top) * sc + pad * 2;
  var r = Math.max(big ? 1.1 : 0.7, sc * (big ? 0.034 : 0.04)), lw = Math.max(big ? 1.2 : 0.8, sc * (wake ? 0.04 : 0.025));
  function path(q, a, b) { q.beginPath(); for (var k = a; k < b; k++) Y.strokes[k].forEach(function (p, j) { j ? q.lineTo(p[0] * sc - ox, p[1] * sc - oy) : q.moveTo(p[0] * sc - ox, p[1] * sc - oy); }); }
  function dots(q, a, b, x, y) { q.beginPath(); for (var k = a; k < b && k < Y.dots.length; k++) { var d = Y.dots[k]; q.moveTo(x + d[0] * sc + r, y + d[1] * sc); q.arc(x + d[0] * sc, y + d[1] * sc, r, 0, TAU); } q.fill(); }
  var key = Y.kind + (big ? 'L' : 'B') + Math.round(sc * 10) + ':' + dpr, C = CARDS[key];
  if (!C) { C = CARDS[key] = { a: document.createElement('canvas'), b: document.createElement('canvas'), sig: '' }; [C.a, C.b].forEach(function (k) { k.width = Math.ceil(w * dpr); k.height = Math.ceil(h * dpr); }); }
  var sig = done + '|' + (wake ? 1 : 0);
  if (C.sig !== sig) {
    C.sig = sig; var A = C.a.getContext('2d'), B = C.b.getContext('2d');
    [A, B].forEach(function (q) { q.setTransform(1, 0, 0, 1, 0, 0); q.clearRect(0, 0, C.a.width, C.a.height); q.setTransform(dpr, 0, 0, dpr, 0, 0); q.lineCap = 'round'; q.lineJoin = 'round'; });
    A.strokeStyle = big ? 'rgba(40,70,170,.42)' : 'rgba(40,70,170,.3)'; A.lineWidth = Math.max(big ? 0.9 : 0.6, sc * 0.02); path(A, 0, Y.strokes.length); A.stroke();
    A.fillStyle = '#141a30'; dots(A, 0, done ? Y.ends[done - 1] : 0, -ox, -oy);
    if (done) { path(B, 0, done); if (big) { B.strokeStyle = 'rgba(255,200,60,.35)'; B.lineWidth = lw * 3.5; B.stroke(); } B.strokeStyle = '#ffd65a'; B.lineWidth = lw; B.stroke(); }
  }
  c.drawImage(C.a, cx + ox, cy + oy, w, h);
  c.fillStyle = '#141a30'; dots(c, done ? Y.ends[done - 1] : 0, n, cx, cy);
  if (done) { c.globalAlpha = wake ? 1 : 0.65 + 0.3 * Math.sin(t / 500); c.drawImage(C.b, cx + ox, cy + oy, w, h); c.globalAlpha = 1; }
}
/* the person receiving, seen from behind, sitting forward over the triangle cushion */
function backView(c, x, y, k, d, night) {
  var ys = y - k * 0.5, yw = y - k * 0.14, skin = d.skin;
  paper(c, function (q) { q.beginPath(); q.ellipse(x, y - k * 0.06, k * 0.3, k * 0.09, 0, 0, TAU); }, d.low, 1.2);
  c.fillStyle = '#c0392b'; c.beginPath(); c.moveTo(x - k * 0.3, ys + k * 0.2); c.lineTo(x - k * 0.2, ys + k * 0.08); c.lineTo(x - k * 0.2, ys + k * 0.3); c.fill();
  c.beginPath(); c.moveTo(x + k * 0.3, ys + k * 0.2); c.lineTo(x + k * 0.2, ys + k * 0.08); c.lineTo(x + k * 0.2, ys + k * 0.3); c.fill();
  c.fillStyle = '#f2c94c'; c.fillRect(x - k * 0.3, ys + k * 0.19, k * 0.6, k * 0.02);
  paper(c, function (q) { q.beginPath(); q.moveTo(x - k * 0.13, yw + k * 0.03); q.lineTo(x - k * 0.2, ys + k * 0.07); q.quadraticCurveTo(x - k * 0.22, ys - k * 0.02, x - k * 0.12, ys - k * 0.03);
    q.lineTo(x + k * 0.12, ys - k * 0.03); q.quadraticCurveTo(x + k * 0.22, ys - k * 0.02, x + k * 0.2, ys + k * 0.07); q.lineTo(x + k * 0.13, yw + k * 0.03); q.closePath(); }, skin, 1.4);
  c.strokeStyle = 'rgba(80,40,20,.25)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x, ys + k * 0.02); c.lineTo(x, yw); c.stroke();
  if (d.wrap) { c.fillStyle = d.low; c.fillRect(x - k * 0.14, yw - k * 0.06, k * 0.28, k * 0.09); c.fillStyle = '#f2c94c'; c.fillRect(x - k * 0.14, yw - k * 0.06, k * 0.28, k * 0.015); }
  c.fillStyle = skin; c.fillRect(x - k * 0.04, ys - k * 0.1, k * 0.08, k * 0.09);
  c.beginPath(); c.arc(x, ys - k * 0.15, k * 0.09, 0, TAU); c.fill();
  c.fillStyle = d.hairCol; c.beginPath(); c.arc(x, ys - k * 0.165, k * 0.088, 0, TAU); c.fill();
  if (d.bun) { c.beginPath(); c.arc(x, ys - k * 0.25, k * 0.045, 0, TAU); c.fill(); c.fillStyle = '#ffd84a'; c.beginPath(); c.arc(x + k * 0.04, ys - k * 0.26, k * 0.018, 0, TAU); c.fill(); }
  return { ys: ys, yw: yw };
}
function sakyant(S) {
  var c = S.c, hh = S.hh, r = S.r, X0 = S.x0, X1 = S.x1, kind = (S.seed >> 3) % 2 ? 'nine' : 'rows', Y = yant(kind);
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a14' : '#8a5e3c');
  var top = under(S), sx0 = S.x0, sx1 = S.x1, w = sx1 - sx0, eave = top + (S.deck - top) * 0.32;
  /* the floor mat, woven */
  paper(c, rect(sx0 + w * 0.04, S.deck - 2, w * 0.92, hh * 0.1), S.night ? '#6b4a2a' : '#c9a36a', 0.6);
  c.strokeStyle = 'rgba(90,50,20,.3)'; c.lineWidth = 1; c.beginPath(); for (var mx = sx0 + w * 0.05; mx < sx0 + w * 0.95; mx += 6) { c.moveTo(mx, S.deck - 2); c.lineTo(mx + 3, S.deck + hh * 0.08); } c.stroke();
  /* a pha yant hung from the beam: a cloth with a grid, swaying */
  var px = sx0 + Math.min(w * 0.16, hh * 0.62), sway = Math.sin(S.t / 1600) * 0.04, pw = hh * 0.42, ph = hh * 0.5;
  c.save(); c.translate(px, eave + 2); c.rotate(sway);
  c.strokeStyle = '#3a2416'; c.lineWidth = 1; c.beginPath(); c.moveTo(-pw * 0.3, 0); c.lineTo(0, -4); c.lineTo(pw * 0.3, 0); c.stroke();
  paper(c, rect(-pw / 2, 0, pw, ph), '#f4ecd8', 0.8);
  c.strokeStyle = '#b8342a'; c.lineWidth = 1.4; c.strokeRect(-pw / 2 + 2, 2, pw - 4, ph - 4);
  c.lineWidth = 0.8; c.beginPath(); for (var gi = 1; gi < 4; gi++) { c.moveTo(-pw / 2 + 3 + (pw - 6) * gi / 4, ph * 0.18); c.lineTo(-pw / 2 + 3 + (pw - 6) * gi / 4, ph - 4); c.moveTo(-pw / 2 + 3, ph * 0.18 + (ph * 0.82 - 4) * gi / 4); c.lineTo(pw / 2 - 3, ph * 0.18 + (ph * 0.82 - 4) * gi / 4); } c.stroke();
  c.fillStyle = '#b8342a'; for (gi = 0; gi < 16; gi++) { c.beginPath(); c.arc(-pw / 2 + 3 + (pw - 6) * ((gi % 4) + 0.5) / 4, ph * 0.18 + (ph * 0.82 - 4) * (Math.floor(gi / 4) + 0.5) / 4, 1.3, 0, TAU); c.fill(); }
  c.beginPath(); c.moveTo(-pw * 0.3, ph * 0.14); c.quadraticCurveTo(0, ph * 0.02, pw * 0.3, ph * 0.14); c.stroke();
  c.restore();
  /* the khan tang, on the floor before the teacher */
  khanTang(c, px, S.deck + hh * 0.02, hh * 0.5, S.t, S.night);
  /* where the two sit */
  var xr = Math.min(sx0 + w * 0.6, sx1 - hh * 0.9), xa = xr - hh * 0.5, k = hh * 1.3;
  var monk = (S.seed >> 5) % 3 === 0, aj = K.town(S, 1, { casual: 1 })[0], who = K.town(S, 2, { casual: 1 });
  aj.dir = 1; aj.long = true;
  if (monk) { aj.col = '#c0682a'; aj.low = '#c0682a'; aj.hairCol = '#a87a5a'; aj.hair = 0; aj.skin = '#c08a5e'; }
  else { aj.col = '#f2efe6'; aj.low = '#2c2f45'; aj.hair = 0; }
  paper(c, rect(xa - hh * 0.42, S.deck - hh * 0.14, hh * 0.62, hh * 0.14), S.night ? '#4a2e1c' : '#6e4426', 1);
  paper(c, rect(xa - hh * 0.4, S.deck - hh * 0.2, hh * 0.58, hh * 0.07), '#b8342a', 0.6);
  var aP = { lean: 0.32, seat: 0.1, legs: POSE.lotus.legs, arms: [0.2, 0.3, 0.1, 0.4] }, ah = hh * 1.08, ay = S.deck - hh * 0.2;
  var AJ = person(c, xa, ay, ah, aP, aj);
  if (monk) { c.strokeStyle = '#8a4418'; c.lineWidth = Math.max(1.5, hh * 0.03); c.beginPath(); c.moveTo(AJ.sh[0] - hh * 0.06, AJ.sh[1]); c.lineTo(AJ.hip[0] + hh * 0.06, AJ.hip[1]); c.stroke(); }
  /* the taps: one every 1/f s, the needle's draw d = A·|sin πft|, a dot at each cusp */
  var N = Y.dots.length, f = N / 22, sec = (S.t / 1000 + 27 * (0.3 + 0.55 * (S.seed % 50) / 50)) % 27, P = sec * f, n = Math.min(N, Math.floor(P)), wake = sec > 22 ? (sec - 22) / 5 : 0;
  var rv = who[0]; rv.skin = K.SKIN[(S.seed >> 2) % 5 + 1]; rv.bun = (S.seed >> 4) % 3 === 0; rv.wrap = rv.bun; rv.low = rv.bun ? '#5a2a6a' : '#2c2f45';
  var B = backView(c, xr, S.deck + hh * 0.06, k, rv, S.night), sc = k * 0.15, bcx = xr, bcy = B.ys + k * 0.06 - Y.top * sc;
  if (wake) { var wg = c.createRadialGradient(bcx, bcy, 0, bcx, bcy, k * 0.5); wg.addColorStop(0, 'rgba(255,214,90,' + (0.6 * Math.sin(Math.PI * wake)).toFixed(3) + ')'); wg.addColorStop(1, 'rgba(255,214,90,0)'); c.fillStyle = wg; c.beginPath(); c.arc(bcx, bcy, k * 0.5, 0, TAU); c.fill(); }
  drawYant(c, Y, bcx, bcy, sc, n, wake, S.t, false);
  /* the needle and the two hands: one drives, finger and thumb of the other guide */
  var tgt = Y.dots[Math.min(n, N - 1)], T = [bcx + tgt[0] * sc, bcy + tgt[1] * sc], d = wake ? hh * 0.12 : hh * 0.06 * Math.abs(Math.sin(Math.PI * P));
  var ux = T[0] - AJ.sh[0] - hh * 0.05, uy = T[1] - AJ.sh[1] + hh * 0.06, ul = Math.hypot(ux, uy); ux /= ul; uy /= ul;
  var tip = [T[0] - ux * d, T[1] - uy * d], drive = [tip[0] - ux * hh * 0.24, tip[1] - uy * hh * 0.24], guide = [T[0] - ux * hh * 0.07, T[1] - uy * hh * 0.07];
  var sleeve = monk ? '#c0682a' : '#f2efe6';
  arm(c, AJ.sh, guide, ah, 1, sleeve, aj.skin);
  c.strokeStyle = '#d6b25a'; c.lineWidth = Math.max(1.6, hh * 0.026); c.lineCap = 'round'; c.beginPath(); c.moveTo(drive[0] - ux * hh * 0.18, drive[1] - uy * hh * 0.18); c.lineTo(tip[0], tip[1]); c.stroke();
  c.strokeStyle = '#2a2a30'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(tip[0] - ux * hh * 0.05, tip[1] - uy * hh * 0.05); c.lineTo(tip[0], tip[1]); c.stroke();
  arm(c, [AJ.sh[0] + 1, AJ.sh[1] + 1], drive, ah, 1, sleeve, aj.skin);
  c.fillStyle = aj.skin; c.beginPath(); c.arc(guide[0], guide[1], Math.max(1.5, hh * 0.035), 0, TAU); c.fill(); c.beginPath(); c.arc(drive[0], drive[1], Math.max(1.5, hh * 0.038), 0, TAU); c.fill();
  if (d < hh * 0.012 && !wake) { c.strokeStyle = 'rgba(255,214,90,.9)'; c.lineWidth = 1; c.beginPath(); for (var sp = 0; sp < 6; sp++) { var a = sp / 6 * TAU; c.moveTo(T[0] + Math.cos(a) * 2, T[1] + Math.sin(a) * 2); c.lineTo(T[0] + Math.cos(a) * 5, T[1] + Math.sin(a) * 5); } c.stroke(); }
  curls(c, AJ.head[0] + hh * 0.12, AJ.head[1] - hh * 0.04, hh, S.t, 3, 0);
  /* candles at the far side, and one waiting with an offering, if there is room */
  var cx2 = xr + k * 0.36;
  if (cx2 + hh * 0.2 < sx1) { candle(c, cx2, S.deck + hh * 0.04, hh * 0.3, S.t, 5); candle(c, cx2 + hh * 0.13, S.deck + hh * 0.04, hh * 0.22, S.t, 6); }
  if (xr + k * 0.36 + hh * 0.95 < sx1) { var wt = who[1]; wt.dir = -1; wt.skirt = 0; var me = person(c, sx1 - hh * 0.35, S.deck + hh * 0.04, hh * 0.92, POSE.wai, wt);
    c.fillStyle = '#f7b52c'; c.beginPath(); c.arc(me.hand[0][0], me.hand[0][1] - hh * 0.05, hh * 0.04, 0, TAU); c.fill(); }
  /* the lens: the back up close, in a ring of lotus petals */
  var left = sx0 - X0, right = X1 - sx1, onL = left > right, room = Math.max(left, right), rm = clamp((room - hh * 0.75) / 2, hh * 0.32, hh * 0.68);
  var lx = onL ? sx0 - rm - hh * 0.12 : sx1 + rm + hh * 0.12, ly = S.deck - hh * 0.95;
  if (room < hh * 1.3) { lx = onL ? sx0 + rm * 0.8 : sx1 - rm * 0.8; ly = top + rm * 0.2; }
  if (lx + rm > S.W * 0.76) ly = Math.max(ly, S.H * 0.45 + rm);
  ly = Math.min(ly, S.deck - rm - hh * 0.1);
  c.strokeStyle = 'rgba(242,201,76,.5)'; c.lineWidth = 1; c.setLineDash([2, 3]); c.beginPath(); c.moveTo(lx + (onL ? rm : -rm) * 0.9, ly); c.quadraticCurveTo((lx + T[0]) / 2, ly - hh * 0.2, T[0], T[1]); c.stroke(); c.setLineDash([]);
  function petals(ox, oy) { c.beginPath(); for (var j = 0; j <= 64; j++) { var a = j / 64 * TAU, rr = rm * (1.13 + 0.07 * Math.cos(a * 16)); c.lineTo(lx + ox + Math.cos(a) * rr, ly + oy + Math.sin(a) * rr); } c.closePath(); }
  c.fillStyle = 'rgba(0,0,0,.28)'; petals(3, 4); c.fill(); c.fillStyle = '#d4a23f'; petals(0, 0); c.fill(); c.strokeStyle = 'rgba(255,240,190,.5)'; c.lineWidth = 1; c.stroke();
  c.fillStyle = rv.skin; c.beginPath(); c.arc(lx, ly, rm, 0, TAU); c.fill(); c.fillStyle = 'rgba(255,236,214,.45)'; c.fill();
  c.save(); c.beginPath(); c.arc(lx, ly, rm, 0, TAU); c.clip();
  var ls = rm * 1.7 / (Y.bot - Y.top + 0.25), lcy = ly - (Y.top + Y.bot) / 2 * ls;
  if (wake) { var lg = c.createRadialGradient(lx, ly, 0, lx, ly, rm); lg.addColorStop(0, 'rgba(255,220,110,' + (0.7 * Math.sin(Math.PI * wake)).toFixed(3) + ')'); lg.addColorStop(1, 'rgba(255,220,110,0)'); c.fillStyle = lg; c.fillRect(lx - rm, ly - rm, rm * 2, rm * 2); }
  drawYant(c, Y, lx, lcy, ls, n, wake, S.t, true);
  if (!wake) { var LT = [lx + tgt[0] * ls, lcy + tgt[1] * ls], ld = d / hh * rm * 1.4; c.strokeStyle = '#d6b25a'; c.lineWidth = Math.max(2, rm * 0.06); c.beginPath(); c.moveTo(LT[0] - ux * (ld + rm * 2), LT[1] - uy * (ld + rm * 2)); c.lineTo(LT[0] - ux * ld, LT[1] - uy * ld); c.stroke();
    c.strokeStyle = '#2a2a30'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(LT[0] - ux * (ld + rm * 0.12), LT[1] - uy * (ld + rm * 0.12)); c.lineTo(LT[0] - ux * ld, LT[1] - uy * ld); c.stroke(); }
  c.restore();
  c.strokeStyle = '#f2c94c'; c.lineWidth = 1.5; c.beginPath(); c.arc(lx, ly, rm, 0, TAU); c.stroke();
  if (wake) curls(c, lx, ly - rm * 0.4, hh, S.t, 4, 0.3);
  K.banner(c, (sx0 + sx1) / 2, top + hh * 0.55, S.label, hh, '#8a3a2a', S.seed, S.hits);
  bodyBox(S, top);
}
function under(S, col) { return K.under(S, col); }

/* ---------------------------------------------------------------- muay thai */
/* a fighter: bare back, the shorts, prajiat on the arms, gloves; the mongkhon on the head for the wai khru */
function fighter(c, x, y, h, P, dir, shorts, skin, mong) {
  var d = { garb: 'casual', col: skin, low: skin, skin: skin, hair: 0, hairCol: '#1c1410', dir: dir };
  var me = person(c, x, y, h, P, d), J = joints(x, y, h, P, dir);
  paper(c, function (q) { q.beginPath(); q.moveTo(J.hip[0] - h * 0.085, J.hip[1] - h * 0.05); q.lineTo(J.hip[0] + h * 0.085, J.hip[1] - h * 0.05);
    q.lineTo(lerp(J.hip[0], J.k1[0], 0.7) + h * 0.05, lerp(J.hip[1], J.k1[1], 0.7)); q.lineTo(lerp(J.hip[0], J.k1[0], 0.7) - h * 0.03, lerp(J.hip[1], J.k1[1], 0.7) + h * 0.02);
    q.lineTo(J.hip[0], J.hip[1] + h * 0.03);
    q.lineTo(lerp(J.hip[0], J.k2[0], 0.7) + h * 0.03, lerp(J.hip[1], J.k2[1], 0.7) + h * 0.02); q.lineTo(lerp(J.hip[0], J.k2[0], 0.7) - h * 0.05, lerp(J.hip[1], J.k2[1], 0.7)); q.closePath(); }, shorts, 0.6);
  c.fillStyle = '#f2e6c9'; c.fillRect(J.hip[0] - h * 0.085, J.hip[1] - h * 0.06, h * 0.17, h * 0.025);
  [[J.sh, J.e1], [J.sh, J.e2]].forEach(function (p, i) { c.strokeStyle = i ? '#f2c94c' : '#d9342b'; c.lineWidth = Math.max(2, h * 0.09); c.beginPath(); var a = [lerp(p[0][0], p[1][0], 0.45), lerp(p[0][1], p[1][1], 0.45)], b = [lerp(p[0][0], p[1][0], 0.6), lerp(p[0][1], p[1][1], 0.6)]; c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); });
  me.hand.forEach(function (hd) { c.fillStyle = shorts; c.beginPath(); c.arc(hd[0], hd[1], h * 0.055, 0, TAU); c.fill(); });
  if (mong) { var hd = me.head; c.strokeStyle = '#f4efe2'; c.lineWidth = Math.max(1.6, h * 0.035); c.beginPath(); c.ellipse(hd[0], hd[1] - h * 0.06, h * 0.11, h * 0.035, 0, 0, TAU); c.stroke();
    c.beginPath(); c.moveTo(hd[0] - dir * h * 0.1, hd[1] - h * 0.06); c.quadraticCurveTo(hd[0] - dir * h * 0.2, hd[1] - h * 0.04, hd[0] - dir * h * 0.24, hd[1] + h * 0.05); c.stroke(); }
  return me;
}
/* a muay thai camp, one place: an open shed (D.civic.shop's row or teak front) with heavy bags
   swinging as pendulums (θ = θ₀·sin ωt), a trainer holding pads to a fighter's kicks on sin²,
   the skipping rope turning, tyres stacked; a stadium (sub) keeps the ring with its crowd, its
   name over it and its own ground beneath */
function muaythaiPlace(S, C) {
  var hh = S.hh;
  C.shop(S, 'muaythai', {
    kinds: ['row', 'teak', 'row', 'shop'], back: '#e8dcc4', floor: '#4a6aa8', iconBg: '#f8f4e8',
    icon: function (q, S, x, y, s) { q.fillStyle = '#c0392b'; q.beginPath(); q.ellipse(x - s * 0.15, y, s * 0.42, s * 0.5, -0.3, 0, TAU); q.fill(); q.fillStyle = '#f4f4f4'; q.fillRect(x - s * 0.45, y + s * 0.35, s * 0.5, s * 0.2); },
    room: function (q, S, R) {
      var w = R.x1 - R.x0, o = {};
      q.fillStyle = '#2a5aa8'; q.fillRect(R.x0, R.y1 - hh * 0.08, w, hh * 0.08);
      for (var k = 0; k < 3; k++) { q.fillStyle = ['#d9342b', '#f4efe2', '#2a5aa8'][k]; q.fillRect(R.x0, R.y1 - hh * (0.62 - k * 0.15), w * 0.35, 2); }
      q.fillStyle = '#2a2a30'; for (var ty = 0; ty < 3; ty++) { q.beginPath(); q.ellipse(R.x1 - hh * 0.25, R.y1 - hh * (0.05 + ty * 0.08), hh * 0.18, hh * 0.05, 0, 0, TAU); q.fill(); }
      q.strokeStyle = '#5a5a62'; q.lineWidth = 3; q.beginPath(); q.moveTo(R.x0, R.y0 + hh * 0.05); q.lineTo(R.x1, R.y0 + hh * 0.05); q.stroke();
      q.fillStyle = '#f4efe2'; q.strokeStyle = '#f4efe2'; q.lineWidth = 2; q.beginPath(); q.ellipse(R.x0 + w * 0.5, R.y0 + hh * 0.22, hh * 0.1, hh * 0.035, 0, 0, TAU); q.stroke();
      o.bags = [R.x0 + w * 0.22, R.x0 + w * 0.78]; return o;
    },
    work: function (c, S, R, L, o) {
      var t = S.t, w = R.x1 - R.x0, sk = [K.SKIN[(S.seed >>> 1) % 4 + 2], K.SKIN[(S.seed >>> 3) % 4 + 1], K.SKIN[(S.seed >>> 5) % 4 + 1]];
      (o.bags || []).forEach(function (bx, k) { var sw = 0.22 * Math.sin(t / 1000 * TAU / 1.3 + k * 1.7), ex = bx + Math.sin(sw) * hh * 0.4, ey = R.y0 + hh * 0.05 + Math.cos(sw) * hh * 0.4; c.strokeStyle = '#3a3a44'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(bx, R.y0 + hh * 0.05); c.lineTo(ex, ey); c.stroke(); c.save(); c.translate(ex, ey); c.rotate(-sw); paper(c, rect(-hh * 0.09, 0, hh * 0.18, hh * 0.46), k ? '#c0392b' : '#2a2a30', 0.6); c.restore(); });
      /* pad work: the kick on θ₀·sin²(πt/T), the trainer's pads meeting it */
      var T = 1.6, kk = (t / 1000 % T) / T, s = Math.pow(Math.sin(Math.PI * kk), 2), fx = R.x0 + w * 0.42, tx = fx + hh * 0.62;
      fighter(c, fx, R.y1 - hh * 0.06, hh * 0.86, { lean: 0.05 - 0.5 * s, lift: 0, legs: [0.05, 0, -0.32 + 2.2 * s, -0.9 * (1 - s) - 0.05], arms: [1.05 - 1.3 * s, 1.95 - 1.2 * s, 1.25 + 0.3 * s, 1.8] }, 1, '#d9342b', sk[0], false);
      var tr = K.town(S, 1, { casual: 1 })[0]; tr.garb = 'casual'; tr.col = '#2a2a30'; tr.low = '#2a2a30'; tr.dir = -1; var me = person(c, tx, R.y1 - hh * 0.06, hh * 0.9, { lean: 0.1 + 0.08 * s, legs: [0.25, -0.1, -0.25, 0.05], arms: [1.3, 0.5, 1.1, 0.6] }, tr);
      c.fillStyle = '#c0392b'; c.fillRect(me.hand[0][0] - hh * 0.08, me.hand[0][1] - hh * 0.06, hh * 0.08, hh * 0.14);
      if (s > 0.9) { c.strokeStyle = 'rgba(255,240,200,.9)'; c.lineWidth = 1.2; c.beginPath(); for (var b = 0; b < 5; b++) { var a = b / 5 * TAU; c.moveTo(me.hand[0][0] - hh * 0.1 + Math.cos(a) * 3, me.hand[0][1] + Math.sin(a) * 3); c.lineTo(me.hand[0][0] - hh * 0.1 + Math.cos(a) * 8, me.hand[0][1] + Math.sin(a) * 8); } c.stroke(); }
      if (w > hh * 3.2) { var a2 = t / 1000 * TAU * 1.6, hop = Math.max(0, Math.sin(a2)) * hh * 0.06, rx = R.x0 + w * 0.12, d = K.town(S, 2, { casual: 1 })[1]; d.garb = 'casual'; d.col = sk[2]; d.low = '#2a5aa8'; d.skin = sk[2]; d.dir = 1;
        var mr = person(c, rx, R.y1 - hh * 0.06 - hop, hh * 0.84, { lean: 0, legs: [0.1, -0.3, -0.1, -0.3], arms: [0.5, 0.4, 0.5, 0.4] }, d); c.strokeStyle = '#e8b84a'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(mr.hand[0][0], mr.hand[0][1]); c.quadraticCurveTo(rx + Math.cos(a2) * hh * 0.4, mr.hand[0][1] - Math.sin(a2) * hh * 0.9, mr.hand[1][0], mr.hand[1][1]); c.stroke(); }
    }
  });
}
function muaythai(S) {
  var Pl = S.place, Cv = D.civic, st0 = Pl ? K.openNow(Pl.hours, S.now) : null;
  if (Pl && !Cv && D.need) D.need('clinic');
  if (Pl && Cv && (!/stadium|เวที|สนามมวย|arena/i.test(Cv.words(Pl)) || st0 === false)) return muaythaiPlace(S, Cv);
  var c = S.c, hh = S.hh, cx = S.x0 + S.span * 0.54, rw = Math.min(S.span * 0.66, hh * 4.4), rx0 = cx - rw / 2, rx1 = cx + rw / 2, fy = S.deck - hh * 0.38, back = hh * 0.2, inset = hh * 0.3;
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#1e1822' : '#7a6a58');
  if (Pl) K.setting(S);
  var T = 18, u0 = (S.t / 1000 + (S.seed % 7) * 2.3) % T, beat = S.t / 60000 * (u0 < 9 ? 84 : 132);
  /* lights on a catenary over the ring */
  K.strand(c, rx0, rx1, fy - hh * 1.55, hh * 0.22, 22, function (x, y, k) { var on = S.night ? 0.7 + 0.3 * Math.sin(S.t / 300 + k * 1.7) : 0.35; K.lanternGlow(c, x, y + 4, 3, [45, 0, 200][k % 3], on); c.fillStyle = ['#ffe2a0', '#ff8a7a', '#9fd8ff'][k % 3]; c.beginPath(); c.arc(x, y + 4, 2.4, 0, TAU); c.fill(); });
  /* the ring: back posts and ropes, the canvas, the apron */
  var post = function (x, y0, y1, col) { paper(c, rect(x - hh * 0.04, y1, hh * 0.08, y0 - y1), col, 1); c.fillStyle = '#f2e6c9'; c.fillRect(x - hh * 0.05, y1 - 2, hh * 0.1, hh * 0.12); };
  var bl = rx0 + inset, br = rx1 - inset, by = fy - back, pt = hh * 0.82;
  post(bl, by, by - pt * 0.85, '#2a5aa8'); post(br, by, by - pt * 0.85, '#c0392b');
  var ropes = ['#d9342b', '#f4efe2', '#2a5aa8'];
  function ropeRow(xa, ya, xb, yb, hA, hB) { ropes.forEach(function (col, i) { c.strokeStyle = col; c.lineWidth = Math.max(1.4, hh * 0.025); c.beginPath(); c.moveTo(xa, ya - hA * (0.9 - i * 0.28)); c.lineTo(xb, yb - hB * (0.9 - i * 0.28)); c.stroke(); }); }
  ropeRow(bl, by, br, by, pt * 0.85, pt * 0.85);
  paper(c, poly([[bl, by], [br, by], [rx1, fy], [rx0, fy]]), S.night ? '#9aa6c0' : '#dfe3ea', 1);
  paper(c, rect(rx0 - 4, fy, rw + 8, S.deck - fy + hh * 0.04), '#2a5aa8', 1.4);
  c.fillStyle = '#f2c94c'; c.fillRect(rx0 - 4, fy + 2, rw + 8, 2);
  c.fillStyle = 'rgba(255,255,255,.85)'; c.font = '800 ' + Math.round(hh * 0.13) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('มวยไทย', cx, fy + (S.deck - fy) * 0.55);
  ropeRow(bl, by, rx0, fy, pt * 0.85, pt);
  ropeRow(br, by, rx1, fy, pt * 0.85, pt);
  /* the fighters: wai khru (the bow three times, then the ram muay), then the bout */
  var h = hh * 0.98, ax = cx - hh * 0.55, bx = cx + hh * 0.55, fy2 = fy - back * 0.45, sk = [K.SKIN[(S.seed >> 1) % 4 + 2], K.SKIN[(S.seed >> 3) % 4 + 1]];
  var PA, PB, mong = u0 < 9;
  if (u0 < 3) {
    var b = Math.pow(Math.abs(Math.sin(Math.PI * u0)), 1.5), kneel = { lean: 0.25 + 1.0 * b, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0, 0, 0, 0] };
    var Ja = joints(ax, fy2, h, kneel, 1), Jb = joints(bx, fy2, h, kneel, -1);
    function hands(J, dir, x) { return b < 0.3 ? [J.sh[0] + dir * h * 0.13, J.sh[1] + h * 0.1] : [x + dir * h * (0.25 + 0.2 * b), fy2 - h * 0.03]; }
    var ha = hands(Ja, 1, ax), hb = hands(Jb, -1, bx);
    PA = reach(ax, fy2, h, kneel, 1, ha, [ha[0] - 1, ha[1]]); PB = reach(bx, fy2, h, kneel, -1, hb, [hb[0] + 1, hb[1]]);
  } else if (u0 < 9) {
    var w = Math.sin((u0 - 3) / 6 * TAU * 1.5), lift = 0.5 + 0.5 * Math.sin((u0 - 3) * 1.4);
    var ram = { lean: 0.12, legs: [0.15 + 0.9 * lift, -1.3 * lift, -0.2, 0.05], arms: [1.5 + 0.45 * w, 0.4 - 0.3 * w, 1.0 - 0.4 * w, 0.9] };
    ax += Math.sin((u0 - 3) * 0.9) * hh * 0.25; bx -= Math.sin((u0 - 3) * 0.9) * hh * 0.25;
    PA = ram; PB = ram;
  } else {
    var tau = u0 - 9, j = Math.floor(tau / 1.5), kk = (tau % 1.5) / 0.75, s = kk < 1 ? Math.pow(Math.sin(Math.PI * kk), 2) : 0, hop = 0.015 * Math.abs(Math.sin(beat * Math.PI));
    var guard = { lean: 0.05, lift: hop, legs: [0.28, -0.12, -0.32, 0.06], arms: [1.05, 1.95, 1.25, 1.8] };
    var kick = { lean: 0.05 - 0.5 * s, lift: 0, legs: [0.05, 0, -0.32 + 2.2 * s, -0.9 * (1 - s) - 0.05], arms: [1.05 - 1.3 * s, 1.95 - 1.2 * s, 1.25 + 0.3 * s, 1.8] };
    var check = { lean: 0.05 - 0.15 * s, lift: 0, legs: [0.28 + 0.9 * s, -0.12 - 1.4 * s, -0.32, 0.06], arms: [1.05, 1.95, 1.25, 1.8] };
    if (j % 2) { PA = check; PB = kick; } else { PA = kick; PB = check; }
    if (!s) { PA = guard; PB = { lean: guard.lean, lift: 0.015 * Math.abs(Math.cos(beat * Math.PI)), legs: guard.legs, arms: guard.arms }; }
    /* the referee */
    var ref = { garb: 'casual', long: false, col: '#f4f1e8', low: '#22222a', skin: K.SKIN[2], hair: 0, dir: 1 };
    var R = person(c, cx + hh * 1.15 + Math.sin(tau * 0.7) * hh * 0.15, fy - back * 0.85, hh * 0.86, { lean: 0.15, legs: [0.15, 0, -0.15, 0], arms: [0.5, 0.6, 0.3, 0.4] }, ref);
    c.fillStyle = '#111'; c.fillRect(R.sh[0] - 2, R.sh[1] + 1, 4, 2);
  }
  fighter(c, ax, fy2, h, PA, 1, '#d9342b', sk[0], mong);
  fighter(c, bx, fy2, h, PB, -1, '#2a5aa8', sk[1], mong);
  /* the front ropes and posts */
  post(rx0, fy, fy - pt, '#2a5aa8'); post(rx1, fy, fy - pt, '#c0392b');
  ropeRow(rx0, fy, rx1, fy, pt, pt);
  /* the music: pi chawa and klong khaek at the ringside, notes on sine paths */
  var mx = rx0 - hh * 0.45, crew = K.town(S, 3, { mohom: 0.6, casual: 0.4 });
  if (mx - hh * 0.3 > S.x0 + hh * 0.6) {
    crew[0].dir = 1; var pi = person(c, mx, S.deck + hh * 0.08, hh * 0.8, { lean: 0.05, seat: 0.24, legs: POSE.sit.legs, arms: [0.9, 1.6, 1.0, 1.5] }, crew[0]);
    var mouth = [pi.head[0] + hh * 0.07, pi.head[1] + hh * 0.04]; c.strokeStyle = '#6a3a1a'; c.lineWidth = Math.max(2, hh * 0.04); c.beginPath(); c.moveTo(mouth[0], mouth[1]); c.lineTo(mouth[0] + hh * 0.22, mouth[1] + hh * 0.22); c.stroke();
    c.fillStyle = '#c9973f'; c.beginPath(); c.moveTo(mouth[0] + hh * 0.2, mouth[1] + hh * 0.2); c.lineTo(mouth[0] + hh * 0.3, mouth[1] + hh * 0.24); c.lineTo(mouth[0] + hh * 0.24, mouth[1] + hh * 0.3); c.fill();
    K.notes(c, mouth[0] + hh * 0.1, mouth[1] - hh * 0.1, S.t, 3, '#ffe2a0');
    var dx = mx - hh * 0.62; if (dx > S.x0 + hh * 0.55) {
      var hit = Math.abs(Math.sin(beat * Math.PI)); crew[1].dir = 1;
      person(c, dx, S.deck + hh * 0.08, hh * 0.8, { lean: 0.1, seat: 0.24, legs: POSE.sit.legs, arms: [1.0 + hit * 0.5, 0.8, 0.9 + (1 - hit) * 0.5, 0.8] }, crew[1]);
      paper(c, function (q) { q.beginPath(); q.ellipse(dx + hh * 0.2, S.deck - hh * 0.1, hh * 0.18, hh * 0.08, 0, 0, TAU); }, '#8a3a1a', 0.8);
      c.fillStyle = '#f2e6c9'; c.beginPath(); c.ellipse(dx + hh * 0.38, S.deck - hh * 0.1, hh * 0.03, hh * 0.08, 0, 0, TAU); c.fill();
    }
  }
  /* the crowd at the apron: heads, arms up when a kick lands */
  var nc = Math.max(4, Math.floor(rw / (hh * 0.42)));
  for (var i = 0; i < nc; i++) {
    var hx = rx0 + rw * (i + 0.5) / nc, cyy = S.H - 3 - Math.abs(Math.sin(beat * Math.PI + i)) * 2, col = i % 3 ? '#3a2c26' : '#4a3a30';
    paper(c, function (q) { q.beginPath(); q.ellipse(hx, cyy, hh * 0.2, hh * 0.15, 0, Math.PI, TAU); q.moveTo(hx + hh * 0.1, cyy - hh * 0.21); q.arc(hx, cyy - hh * 0.21, hh * 0.1, 0, TAU); }, col, 0.8);
    if (u0 > 9 && (i * 5 + S.seed) % 3 === 0) { c.strokeStyle = col; c.lineWidth = Math.max(2, hh * 0.06); c.lineCap = 'round'; c.beginPath(); c.moveTo(hx + hh * 0.12, cyy - hh * 0.1); c.lineTo(hx + hh * 0.2, cyy - hh * 0.45 - Math.abs(Math.sin(beat * Math.PI)) * 4); c.stroke(); }
  }
  K.banner(c, cx, fy - hh * 1.42, S.label, hh, '#c0392b', S.seed, S.hits);
  if (Pl) { var sb = Cv ? Cv.signAt(c, S, cx, fy - hh * 1.95, Pl, hh * 0.8, '#5a1a1a', S.night || null) : K.sign(c, cx, fy - hh * 1.95, Pl, hh * 0.8, '#5a1a1a', S.night || null); S.hits.push({ k: 'place', x0: rx0, x1: rx1, y0: fy - hh * 1.95, y1: S.deck }); }
  bodyBox(S, fy - hh * 1.5);
}

/* ---------------------------------------------------------------- tak bat, wian thian */
/* a monk for the alms round: the robe over both shoulders, the bowl on its strap */
function monk(c, x, y, h, P, dir, robe, bowl) {
  var d = { garb: 'casual', long: true, col: robe, low: robe, skin: '#c48d62', hair: 0, hairCol: '#a87a58', dir: dir };
  var J = joints(x, y, h, P, dir), me = person(c, x, y, h, P, d), dark = 'rgba(90,30,0,.35)';
  var fx = (J.f1[0] + J.f2[0]) / 2, fyy = Math.max(J.f1[1], J.f2[1]) - h * 0.1, sp = Math.abs(J.f1[0] - J.f2[0]) * 0.45 + h * 0.08;
  c.fillStyle = robe; c.beginPath(); c.moveTo(J.hip[0] - h * 0.09, J.hip[1] - h * 0.05); c.lineTo(J.hip[0] + h * 0.09, J.hip[1] - h * 0.05); c.lineTo(fx + sp, fyy); c.lineTo(fx - sp, fyy); c.closePath(); c.fill();
  c.strokeStyle = dark; c.lineWidth = 1; c.beginPath(); c.moveTo(J.sh[0] - dir * h * 0.06, J.sh[1] - h * 0.01); c.lineTo(J.hip[0] + dir * h * 0.08, J.hip[1] + h * 0.02);
  c.moveTo(J.hip[0], J.hip[1]); c.lineTo(fx - dir * sp * 0.3, fyy); c.stroke();
  if (bowl) { var bx = (me.hand[0][0] + me.hand[1][0]) / 2, byy = (me.hand[0][1] + me.hand[1][1]) / 2 - h * 0.02;
    c.strokeStyle = '#3a2a20'; c.lineWidth = 1; c.beginPath(); c.moveTo(J.sh[0] - dir * h * 0.05, J.sh[1]); c.lineTo(bx, byy - h * 0.04); c.stroke();
    c.fillStyle = '#2a2220'; c.beginPath(); c.ellipse(bx, byy, h * 0.085, h * 0.065, 0, 0, TAU); c.fill();
    c.fillStyle = '#4a3a30'; c.beginPath(); c.ellipse(bx, byy - h * 0.05, h * 0.07, h * 0.02, 0, 0, TAU); c.fill(); return [bx, byy - h * 0.06]; }
  return me.head;
}
/* a Lanna wat gate: whitewashed piers, an arch, a tiered roof with gilt edges */
function watGate(c, x, deck, hh, night) {
  var w = hh * 1.3, top = deck - hh * 1.95, wall = night ? '#8f8aa0' : '#f2ece0', roof = night ? '#6d2b20' : '#a8432f', gold = '#e8b84a';
  paper(c, rect(x - w / 2, deck - hh * 1.2, w * 0.24, hh * 1.2), wall, 1.2); paper(c, rect(x + w / 2 - w * 0.24, deck - hh * 1.2, w * 0.24, hh * 1.2), wall, 1.2);
  paper(c, function (q) { q.beginPath(); q.moveTo(x - w / 2, deck - hh * 1.2); q.lineTo(x + w / 2, deck - hh * 1.2); q.lineTo(x + w / 2, deck - hh * 1.32); q.lineTo(x - w / 2, deck - hh * 1.32); q.closePath(); q.moveTo(x - w * 0.26, deck - hh * 1.2); q.quadraticCurveTo(x, deck - hh * 1.5, x + w * 0.26, deck - hh * 1.2); }, wall, 1.2);
  for (var i = 0; i < 3; i++) { var yb = deck - hh * (1.32 + i * 0.2), ww = w * (0.62 - i * 0.16);
    paper(c, poly([[x - ww, yb], [x - ww * 0.75, yb - hh * 0.2], [x + ww * 0.75, yb - hh * 0.2], [x + ww, yb]]), roof, 1.2);
    c.strokeStyle = gold; c.lineWidth = 1.2; c.beginPath(); c.moveTo(x - ww, yb); c.lineTo(x - ww * 0.75, yb - hh * 0.2); c.moveTo(x + ww, yb); c.lineTo(x + ww * 0.75, yb - hh * 0.2); c.stroke();
    c.beginPath(); c.moveTo(x - ww, yb); c.quadraticCurveTo(x - ww - hh * 0.05, yb - hh * 0.06, x - ww - hh * 0.02, yb - hh * 0.12); c.moveTo(x + ww, yb); c.quadraticCurveTo(x + ww + hh * 0.05, yb - hh * 0.06, x + ww + hh * 0.02, yb - hh * 0.12); c.stroke(); }
  c.fillStyle = gold; c.beginPath(); c.moveTo(x - 2, deck - hh * 1.92); c.lineTo(x, top - hh * 0.06); c.lineTo(x + 2, deck - hh * 1.92); c.fill();
  c.strokeStyle = night ? 'rgba(232,184,74,.5)' : '#c9973f'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - w * 0.26, deck - hh * 1.22); c.quadraticCurveTo(x, deck - hh * 1.46, x + w * 0.26, deck - hh * 1.22); c.stroke();
}
/* a Lanna chedi: the stepped base, the bell, the rings, the gilt umbrella */
function chedi(c, x, deck, hh, night) {
  var g = night ? '#d9a93a' : '#e0b04a', d = night ? '#a8782a' : '#b8872f';
  paper(c, rect(x - hh * 0.8, deck - hh * 0.22, hh * 1.6, hh * 0.22), g, 1.4);
  paper(c, rect(x - hh * 0.6, deck - hh * 0.4, hh * 1.2, hh * 0.18), g, 1.4);
  paper(c, rect(x - hh * 0.44, deck - hh * 0.55, hh * 0.88, hh * 0.15), g, 1.4);
  paper(c, function (q) { q.beginPath(); q.moveTo(x - hh * 0.4, deck - hh * 0.55); q.quadraticCurveTo(x - hh * 0.42, deck - hh * 1.15, x, deck - hh * 1.18); q.quadraticCurveTo(x + hh * 0.42, deck - hh * 1.15, x + hh * 0.4, deck - hh * 0.55); q.closePath(); }, g, 1.6);
  paper(c, rect(x - hh * 0.16, deck - hh * 1.3, hh * 0.32, hh * 0.13), g, 1);
  paper(c, function (q) { q.beginPath(); q.moveTo(x - hh * 0.13, deck - hh * 1.3); for (var i = 0; i < 7; i++) { var yy = deck - hh * (1.3 + i * 0.1), ww = hh * (0.13 - i * 0.016); q.lineTo(x - ww, yy); q.lineTo(x - ww * 0.8, yy - hh * 0.05); } q.lineTo(x, deck - hh * 2.12); for (i = 6; i >= 0; i--) { var y2 = deck - hh * (1.3 + i * 0.1), w2 = hh * (0.13 - i * 0.016); q.lineTo(x + w2 * 0.8, y2 - hh * 0.05); q.lineTo(x + w2, y2); } q.closePath(); }, g, 1.2);
  c.strokeStyle = d; c.lineWidth = 1; c.beginPath(); for (var k = 0; k < 3; k++) { c.moveTo(x - hh * (0.8 - k * 0.18), deck - hh * (0.22 + k * 0.17)); c.lineTo(x + hh * (0.8 - k * 0.18), deck - hh * (0.22 + k * 0.17)); } c.stroke();
  c.fillStyle = '#f2c94c'; [1.62, 1.82, 1.98].forEach(function (f, i) { c.beginPath(); c.ellipse(x, deck - hh * f, hh * (0.1 - i * 0.025), hh * 0.02, 0, 0, TAU); c.fill(); });
}
function takbat(S) {
  var c = S.c, hh = S.hh, i, night = S.night;
  K.ground(c, S.x0, S.x1, S.deck, S.H, night ? '#22202c' : '#a89a86');
  if (!night) {
    /* dawn: a wat gate, mist drifting, x = x₀ + vt */
    var gx = S.x0 + S.span * ((S.seed >> 4) % 2 ? 0.2 : 0.8);
    watGate(c, gx, S.deck, hh, false);
    for (i = 0; i < 3; i++) { var my = S.deck - hh * (0.3 + i * 0.35), mx = S.x0 + ((S.t / 1000 * hh * 0.05 * (1 + i * 0.4) + i * S.span * 0.37) % (S.span + hh * 4)) - hh * 2;
      var mg = c.createLinearGradient(mx - hh * 2, 0, mx + hh * 2, 0); mg.addColorStop(0, 'rgba(255,248,236,0)'); mg.addColorStop(0.5, 'rgba(255,248,236,.32)'); mg.addColorStop(1, 'rgba(255,248,236,0)');
      c.fillStyle = mg; c.fillRect(mx - hh * 2, my - hh * 0.08, hh * 4, hh * 0.16); }
    /* the monks walk right to left; the people kneel with sticky rice */
    var nm = Math.max(3, Math.min(6, Math.floor(S.span / (hh * 1.1)))), v = hh * 0.22, gap = hh * 0.82, loop = S.span + gap * 2 + hh * 2, head = S.t / 1000 * v + (0.35 + 0.3 * (S.seed % 97) / 97) * loop;
    var robes = ['#c8692a', '#b85a22', '#d27a32', '#9a4a1e'], mxs = [];
    for (i = 0; i < nm; i++) { var pq = ((head - i * gap) % loop + loop) % loop; mxs.push(S.x1 + hh - pq); }
    var ng = Math.max(2, Math.min(4, Math.floor(S.span / (hh * 1.6)))), givers = K.town(S, ng, { sin: 0.75, mohom: 0.25 }), gxs = [];
    for (i = 0; i < ng; i++) gxs.push(S.x0 + S.span * (i + 0.6) / (ng + 0.3));
    for (i = 0; i < nm; i++) { var mxx = mxs[i], nov = i === nm - 1, hm = nov ? hh * 0.78 : hh * 0.97;
      var P = K.walkP(S.t / 1000 * TAU * 0.55 + i, false); P.arms = [0.55, 1.0, 0.5, 1.05]; P.legs = P.legs.map(function (a) { return a * 0.6; });
      monk(c, mxx, S.deck + hh * 0.02, hm, P, -1, robes[(i + S.seed) % robes.length], true); }
    for (i = 0; i < ng; i++) {
      var gxx = gxs[i], near = 9; mxs.forEach(function (q) { var dd = q - gxx - hh * 0.35; if (Math.abs(dd) < Math.abs(near)) near = dd; });
      var give = clamp(1 - Math.abs(near) / (hh * 0.45), 0, 1), after = near < -hh * 0.45 && near > -hh * 1.6;
      paper(c, rect(gxx - hh * 0.35, S.deck + hh * 0.16, hh * 0.85, hh * 0.05), '#c0392b', 0.4);
      var d = givers[i]; d.dir = 1; d.skirt = 0;
      var kn = { lean: give * 0.25, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0.3, 0.5, 0.2, 0.6] }, gy = S.deck + hh * 0.2, gh = hh * 0.92;
      var J = joints(gxx, gy, gh, kn, 1), hand = give > 0 ? [lerp(J.sh[0] + gh * 0.12, gxx + gh * 0.42, give), lerp(J.sh[1] + gh * 0.14, J.sh[1] - gh * 0.02, give)] : after ? [J.sh[0] + gh * 0.13, J.sh[1] + gh * 0.08] : [J.sh[0] + gh * 0.1, J.sh[1] + gh * 0.2];
      var me = person(c, gxx, gy, gh, reach(gxx, gy, gh, kn, 1, hand, after ? [hand[0] - 1, hand[1]] : [J.sh[0] + gh * 0.16, J.sh[1] + gh * 0.24]), d);
      paper(c, function (q) { q.beginPath(); q.ellipse(gxx + gh * 0.32, gy - gh * 0.04, gh * 0.12, gh * 0.06, 0, 0, Math.PI); q.closePath(); }, '#cfd3da', 0.6);
      c.fillStyle = '#c9a36a'; c.fillRect(gxx + gh * 0.24, gy - gh * 0.16, gh * 0.1, gh * 0.12);
      if (!after) { c.fillStyle = '#fffaf0'; c.beginPath(); c.arc(me.hand[0][0], me.hand[0][1] - 2, Math.max(2, gh * 0.03), 0, TAU); c.fill(); }
      if (give > 0.85) curls(c, gxx + hh * 0.4, S.deck - hh * 0.75, hh, S.t, 2, i * 0.3);
    }
    K.banner(c, S.x0 + S.span * 0.5, S.deck - hh * 1.95, S.label, hh, '#c8692a', S.seed, S.hits);
  } else {
    /* wian thian: three times around the chedi, keeping it on the right; x = a·cos ωt, y = b·sin ωt */
    var cx = S.x0 + S.span * 0.52, a = Math.min(S.span * 0.4, hh * 2.4), b = hh * 0.2, cy = S.deck + hh * 0.06, n = Math.max(7, Math.min(13, Math.floor(a / (hh * 0.28)))), om = -TAU / 40;
    var walkers = K.town(S, n, { casual: 0.5, sin: 0.5 }), seq = [];
    for (i = 0; i < n; i++) { var th = S.t / 1000 * om + i * TAU * 0.78 / n; seq.push({ i: i, th: th, s: Math.sin(th) }); }
    var g = c.createRadialGradient(cx, S.deck - hh * 0.8, 0, cx, S.deck - hh * 0.8, hh * 2.4); g.addColorStop(0, 'rgba(255,200,110,.35)'); g.addColorStop(1, 'rgba(255,200,110,0)'); c.fillStyle = g; c.fillRect(cx - hh * 2.4, S.deck - hh * 3, hh * 4.8, hh * 3.2);
    function walker(q) {
      var x = cx + a * Math.cos(q.th), y = cy + b * Math.sin(q.th), sc = 0.84 + 0.16 * (q.s + 1) / 2, dir = Math.sin(q.th) * om < 0 ? 1 : -1, h = hh * 0.92 * sc;
      var P = K.walkP(S.t / 1000 * TAU * 0.5 + q.i, false); P.legs = P.legs.map(function (z) { return z * 0.6; });
      var J0 = joints(x, y, h, P, dir), hd = [J0.sh[0] + dir * h * 0.13, J0.sh[1] + h * 0.1]; P = reach(x, y, h, P, dir, hd, [hd[0] - dir, hd[1]]);
      var top;
      if (q.i < 2) top = monk(c, x, y, h, P, dir, '#c0682a', false);
      else { var d = walkers[q.i]; d.dir = dir; d.col = '#f4f1e8'; if (d.garb === 'mohom') d.col = '#f4f1e8'; d.sabai = '#f4f1e8'; d.skirt = 0; person(c, x, y, h, P, d); }
      var fx = hd[0] + dir * h * 0.02, fyy = hd[1] - h * 0.02;
      c.fillStyle = '#f0a0b8'; c.beginPath(); c.ellipse(fx, fyy - h * 0.04, h * 0.025, h * 0.045, 0, 0, TAU); c.fill();
      candle(c, fx + dir * h * 0.05, fyy, h * 0.18, S.t, q.i, '#f3e3b0');
    }
    seq.filter(function (q) { return q.s < 0; }).sort(function (p, q) { return p.s - q.s; }).forEach(walker);
    chedi(c, cx, S.deck - hh * 0.02, hh, true);
    for (i = 0; i < 9; i++) { var kx = cx + (i - 4) * hh * 0.17; candle(c, kx, S.deck - hh * 0.22, hh * 0.08, S.t, i + 20, '#f3e3b0'); }
    seq.filter(function (q) { return q.s >= 0; }).sort(function (p, q) { return p.s - q.s; }).forEach(walker);
    K.banner(c, Math.max(S.x0 + hh * 2.2, cx - a * 0.72), S.deck - hh * 1.85, S.label, hh, '#a8432f', S.seed, S.hits);
  }
  bodyBox(S, S.deck - hh * 1.6);
}

/* ---------------------------------------------------------------- massage */
/* someone lying face down on the mat: the standing figure turned a quarter round */
function lying(c, x, y, h, d) {
  c.save(); c.translate(x, y); c.rotate(Math.PI / 2); d.dir = 1;
  person(c, 0, 0, h, { lean: 0, legs: [0.03, 0, -0.03, 0], arms: [0.06, 0, -0.04, 0] }, d);
  c.restore();
}
/* a massage house, one place (S.place): the shop dealt from its seed through the civic frame
   (D.civic.shop: a shophouse, a teak house with mats beneath, a row, a glass spa), its name on the
   board, its hours as shutters; the stations inside from what it offers (sub: thai-traditional,
   tok-sen, spa-body, foot), the rest dealt: Thai massage on the mat (palms pressing, |sin ωt|),
   tok sen (the ring along the sen line, y = A·e^(−λt)·sin(kx − ωt)), feet in the recliner (thumbs
   on small circles), the compress steaming, oil on the bed by candlelight. */
var MST = { 'thai-traditional': 'thai', 'blind-massage': 'thai', 'khat-khi-khlai': 'thai', 'massage-school': 'thai', 'tok-sen': 'toksen', 'chap-sen': 'toksen', 'spa-body': 'oil', spa: 'oil', oil: 'oil', face: 'oil', foot: 'foot' };
function compressIcon(c, S, x, y, s) {
  c.fillStyle = '#e8dcc0'; c.beginPath(); c.arc(x, y + s * 0.2, s * 0.55, 0, TAU); c.fill(); c.strokeStyle = '#7a5a2a'; c.lineWidth = Math.max(1, s * 0.08);
  c.beginPath(); c.moveTo(x - s * 0.3, y - s * 0.25); c.lineTo(x, y - s * 0.05); c.lineTo(x + s * 0.3, y - s * 0.25); c.moveTo(x, y - s * 0.05); c.lineTo(x, y - s * 0.75); c.stroke();
  c.fillStyle = '#5a8a3a'; c.beginPath(); c.ellipse(x - s * 0.15, y + s * 0.15, s * 0.1, s * 0.05, 0.5, 0, TAU); c.ellipse(x + s * 0.18, y + s * 0.3, s * 0.1, s * 0.05, -0.4, 0, TAU); c.fill();
}
function massagePlace(S, C) {
  var P = S.place, want = [], hh = S.hh, r = rnd((S.seed ^ 0x5a17) >>> 0);
  (P.sub || []).forEach(function (x) { var k = MST[x]; if (k && want.indexOf(k) < 0) want.push(k); });
  [[/foot|เท้า|reflex/i, 'foot'], [/spa|สปา|\boil\b|aroma|น้ำมัน/i, 'oil'], [/tok ?sen|ตอกเส้น/i, 'toksen'], [/ประคบ|compress|herbal|สมุนไพร/i, 'compress']].forEach(function (p) { if (C.has(P, p[0]) && want.indexOf(p[1]) < 0) want.push(p[1]); });
  var deal = ['thai', 'foot', 'compress', 'thai'], spa = want.indexOf('oil') >= 0;
  function stations(R) {
    var w = R.x1 - R.x0, n = Math.max(1, Math.min(3, Math.floor(w / (hh * 1.3)))), out = [], k = (S.seed >>> 4) % deal.length;
    for (var i = 0; i < n; i++) out.push(want[i] || (want.length && i >= want.length && (S.seed >>> (6 + i)) % 2 ? want[0] : deal[(k + i) % deal.length]));
    var sw = w / n; return out.map(function (kd, i) { return { k: kd, x0: R.x0 + i * sw, x1: R.x0 + (i + 1) * sw }; });
  }
  var back = spa ? C.pick(r, ['#f2e6d8', '#e8dccc', '#f4ecd8']) : C.pick(r, ['#f2e6c9', '#e8d4b0', '#d8e4d0', '#f0dcc8', '#e6d8ec']);
  C.shop(S, 'massage', {
    kinds: spa ? ['glass', 'teak', 'shop'] : ['shop', 'teak', 'row', 'shop', 'glass', 'teak'], back: back, floor: '#c9a36a', icon: compressIcon, iconBg: '#f8f2e4',
    keyOf: function () { return want.join(',') + '|' + back; },
    room: function (q, S, R) {
      var st = stations(R);
      /* a cloth on the wall, a shelf with a Buddha and flowers on some */
      if ((S.seed >>> 3) % 2) { var cx = (R.x0 + R.x1) / 2; q.fillStyle = '#7a4a2a'; q.fillRect(cx - hh * 0.2, R.y0 + hh * 0.2, hh * 0.4, 3); q.fillStyle = '#d4a23f'; q.beginPath(); q.ellipse(cx, R.y0 + hh * 0.17, hh * 0.06, hh * 0.04, 0, 0, TAU); q.ellipse(cx, R.y0 + hh * 0.1, hh * 0.035, hh * 0.05, 0, 0, TAU); q.fill(); q.fillStyle = '#f29a1f'; q.beginPath(); q.arc(cx + hh * 0.12, R.y0 + hh * 0.17, hh * 0.025, 0, TAU); q.fill(); }
      else { q.fillStyle = C.pick(r, ['#7a1f3a', '#2a3a6a', '#1f5a4a']); q.fillRect(R.x0 + hh * 0.2, R.y0 + hh * 0.08, hh * 0.5, hh * 0.32); q.fillStyle = '#e8b84a'; for (var z = 0; z < 4; z++) q.fillRect(R.x0 + hh * 0.2, R.y0 + hh * (0.12 + z * 0.08), hh * 0.5, 2); }
      st.forEach(function (s2) {
        var cx = (s2.x0 + s2.x1) / 2;
        if (s2.k === 'thai' || s2.k === 'toksen') { paper(q, rect(s2.x0 + hh * 0.1, R.y1 - hh * 0.06, s2.x1 - s2.x0 - hh * 0.2, hh * 0.06), C.pick(r, ['#b8342a', '#2a5aa8', '#7a3a5a', '#2f8f5b']), 0.5); q.fillStyle = '#f2c94c'; q.fillRect(s2.x0 + hh * 0.1, R.y1 - hh * 0.06, s2.x1 - s2.x0 - hh * 0.2, 1.5); q.fillStyle = '#f4f0e8'; q.fillRect(s2.x1 - hh * 0.35, R.y1 - hh * 0.1, hh * 0.22, hh * 0.05); }
        if (s2.k === 'foot') { paper(q, poly([[cx - hh * 0.32, R.y1], [cx - hh * 0.3, R.y1 - hh * 0.3], [cx - hh * 0.52, R.y1 - hh * 0.7], [cx - hh * 0.4, R.y1 - hh * 0.74], [cx - hh * 0.16, R.y1 - hh * 0.34], [cx + hh * 0.3, R.y1 - hh * 0.3], [cx + hh * 0.3, R.y1 - hh * 0.24], [cx + hh * 0.24, R.y1]]), '#7a4a2a', 1); paper(q, rect(cx + hh * 0.36, R.y1 - hh * 0.18, hh * 0.24, hh * 0.18), '#8a5a3a', 0.8); }
        if (s2.k === 'compress') { paper(q, rect(s2.x0 + hh * 0.08, R.y1 - hh * 0.05, hh * 0.7, hh * 0.05), '#c9a36a', 0.4); paper(q, rect(s2.x1 - hh * 0.3, R.y1 - hh * 0.16, hh * 0.24, hh * 0.16), '#8a5a3a', 0.8); q.fillStyle = '#4a4a52'; q.beginPath(); q.ellipse(s2.x1 - hh * 0.18, R.y1 - hh * 0.25, hh * 0.13, hh * 0.09, 0, 0, TAU); q.fill(); }
        if (s2.k === 'oil') { paper(q, rect(s2.x0 + hh * 0.12, R.y1 - hh * 0.42, s2.x1 - s2.x0 - hh * 0.24, hh * 0.08), '#f4ecdc', 0.8); q.fillStyle = '#8a5a3a'; q.fillRect(s2.x0 + hh * 0.16, R.y1 - hh * 0.34, 4, hh * 0.34); q.fillRect(s2.x1 - hh * 0.2, R.y1 - hh * 0.34, 4, hh * 0.34);
          q.fillStyle = '#f4f0f8'; q.beginPath(); q.ellipse(s2.x1 - hh * 0.12, R.y1 - hh * 0.62, hh * 0.08, hh * 0.04, 0, 0, TAU); q.fill(); q.fillStyle = '#c070c0'; for (var o = 0; o < 4; o++) { q.beginPath(); q.arc(s2.x1 - hh * 0.16 + o * hh * 0.03, R.y1 - hh * 0.7 - (o % 2) * 3, hh * 0.022, 0, TAU); q.fill(); } }
      });
      return { st: st };
    },
    work: function (c, S, R, L, o) {
      var crew = K.town(S, 8, { casual: 0.55, sin: 0.45 }), t = S.t, i = 0;
      /* herbs drying on the beam, pendulums */
      for (var hb = 0; hb < 3; hb++) { var hx = lerp(R.x0, R.x1, (hb + 0.5) / 3), th = 0.12 * Math.sin(t / 900 + hb), Lh = hh * 0.18, ex = hx + Math.sin(th) * Lh, ey = R.y0 + hh * 0.05 + Math.cos(th) * Lh; c.strokeStyle = '#3a2416'; c.lineWidth = 1; c.beginPath(); c.moveTo(hx, R.y0 + hh * 0.05); c.lineTo(ex, ey); c.stroke(); for (var l = 0; l < 4; l++) { c.fillStyle = ['#5a8a3a', '#7aa84a'][l % 2]; c.beginPath(); c.ellipse(ex + (l - 1.5) * 2, ey + hh * 0.05, 1.6, hh * 0.06, (l - 1.5) * 0.2, 0, TAU); c.fill(); } }
      (o.st || []).forEach(function (s2) {
        var cx = (s2.x0 + s2.x1) / 2, cl = crew[i++], th2 = crew[i++]; th2.dir = 1; th2.skirt = 0; cl.skirt = 0; if (th2.garb === 'casual') { th2.col = C.pick(K.rnd(S.seed + i), ['#5a2a6a', '#2f6f6a', '#7a3a1e', '#2a3a6a']); th2.long = true; }
        if (s2.k === 'thai' || s2.k === 'toksen') {
          var lh = hh * 0.9, lx = s2.x0 + hh * 0.14, ly = R.y1 - hh * 0.1; cl.garb = 'casual'; cl.col = '#7a3a5a'; cl.low = '#7a3a5a'; cl.long = true;
          var kx = lx + lh * 0.42, kneel = { lean: 0.45, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0, 0, 0, 0] }, kh = hh * 0.86, backY = ly - lh * 0.08;
          if (s2.k === 'thai') { var pr = Math.abs(Math.sin(t / 1000 * Math.PI * 0.9 + i)), along = lx + lh * (0.45 + 0.15 * Math.sin(t / 3000 + i)); person(c, kx - hh * 0.25, R.y1 - hh * 0.02, kh, reach(kx - hh * 0.25, R.y1 - hh * 0.02, kh, kneel, 1, [along, backY - 2 + pr * 2], [along + hh * 0.08, backY - 1 + (1 - pr) * 2]), th2); lying(c, lx, ly, lh, cl); }
          else { var f = 2.2, tau = (t / 1000 * f) % 1 / f, swing = 1.1 * Math.abs(Math.sin(Math.PI * f * t / 1000)), px = lx + lh * 0.62, pegTop = backY - hh * 0.12, pivot = [px - hh * 0.2, pegTop - hh * 0.04];
            person(c, kx - hh * 0.25, R.y1 - hh * 0.02, kh, reach(kx - hh * 0.25, R.y1 - hh * 0.02, kh, kneel, 1, pivot, [px - 2, pegTop + hh * 0.05]), th2); lying(c, lx, ly, lh, cl);
            var amp = hh * 0.05 * Math.exp(-tau * 6); c.save(); c.strokeStyle = 'rgba(255,214,90,.95)'; c.lineWidth = 1.6; c.beginPath(); for (var sx = lx + lh * 0.12; sx <= lx + lh * 0.9; sx += 2) { var dd = Math.abs(sx - px), yy = backY - 2 - amp * Math.exp(-dd / (hh * 0.35)) * Math.sin(dd * 0.35 - tau * 40); sx === lx + lh * 0.12 ? c.moveTo(sx, yy) : c.lineTo(sx, yy); } c.stroke(); c.restore();
            var head = [pivot[0] + Math.cos(swing) * hh * 0.2, pivot[1] - Math.sin(swing) * hh * 0.2]; c.strokeStyle = '#8a5a2a'; c.lineWidth = 2; c.beginPath(); c.moveTo(px, backY - 1); c.lineTo(px, pegTop); c.stroke(); c.strokeStyle = '#6a3a1a'; c.beginPath(); c.moveTo(pivot[0], pivot[1]); c.lineTo(head[0], head[1]); c.stroke(); c.fillStyle = '#9a6a3a'; c.fillRect(head[0] - hh * 0.03, head[1] - hh * 0.04, hh * 0.07, hh * 0.08); }
        } else if (s2.k === 'foot') {
          var rec = { lean: -0.85, seat: 0.36, legs: [1.25, -0.05, 1.32, -0.08], arms: [0.2, 0.4, 0.1, 0.5] }, Jr = joints(cx, R.y1, hh * 0.86, rec, 1); cl.dir = 1; person(c, cx, R.y1, hh * 0.86, rec, cl);
          var cir = [Math.cos(t / 260) * hh * 0.012, Math.sin(t / 260) * hh * 0.012], ft = Jr.f1, sx2 = cx + hh * 0.48, sp2 = { lean: 0.4, seat: 0.3, legs: [1.3, -1.3, 1.2, -1.2], arms: [0, 0, 0, 0] };
          person(c, sx2, R.y1, hh * 0.86, reach(sx2, R.y1, hh * 0.86, sp2, -1, [ft[0] + hh * 0.02 + cir[0], ft[1] - hh * 0.02 + cir[1]], [ft[0] + hh * 0.05 - cir[0], ft[1] + hh * 0.01 - cir[1]]), (th2.dir = -1, th2));
        } else if (s2.k === 'compress') {
          var seated = { lean: 0.15, seat: 0.1, legs: POSE.lotus.legs, arms: [0.4, 0.6, 0.3, 0.7] }, sxp = s2.x0 + hh * 0.55, Js = joints(sxp, R.y1, hh * 0.86, seated, 1), press = 0.5 - 0.5 * Math.cos(t / 1000 * TAU * 0.6), cp = [Js.sh[0] - hh * 0.05, Js.sh[1] - hh * 0.03 - press * hh * 0.05];
          person(c, sxp - hh * 0.4, R.y1, hh * 0.9, reach(sxp - hh * 0.4, R.y1, hh * 0.9, { lean: 0.25, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0, 0, 0, 0] }, 1, [cp[0] - hh * 0.04, cp[1]], [cp[0] - hh * 0.03, cp[1] + hh * 0.04]), th2);
          cl.dir = 1; person(c, sxp, R.y1, hh * 0.86, seated, cl); steam(c, cp[0], cp[1] - hh * 0.05, hh, t, 2, 3, hh * 0.35, 0.55); c.fillStyle = '#e8dcc0'; c.beginPath(); c.arc(cp[0], cp[1], hh * 0.06, 0, TAU); c.fill(); steam(c, s2.x1 - hh * 0.18, R.y1 - hh * 0.32, hh, t, 4, 4, hh * 0.5, 0.45);
        } else {
          var by = R.y1 - hh * 0.42, ox = s2.x0 + hh * 0.18; cl.garb = 'casual'; cl.col = '#f4f0e8'; cl.low = '#f4f0e8'; lying(c, ox, by - hh * 0.04, hh * 0.86, cl); c.fillStyle = '#f4f0e8'; c.fillRect(ox, by - hh * 0.07, hh * 0.45, hh * 0.06);
          var st2 = 0.5 + 0.5 * Math.sin(t / 1000 * TAU * 0.35); th2.dir = -1; person(c, ox + hh * 0.95, R.y1, hh * 0.9, reach(ox + hh * 0.95, R.y1, hh * 0.9, { lean: 0.55, legs: [0.06, 0, -0.06, 0], arms: [1, 0.5, 1, 0.5] }, -1, [ox + hh * (0.35 + 0.25 * st2), by - hh * 0.1], [ox + hh * (0.45 + 0.25 * st2), by - hh * 0.09]), th2);
          candle(c, s2.x0 + hh * 0.14, R.y1 - hh * 0.02, hh * 0.16, t, i, '#f3e3b0');
        }
      });
    },
    front: function (c, S, R, L) {
      /* on some streets two recliners stand out on the pavement, feet being done in the open */
      if (!L.st.open || (S.seed >>> 9) % 3 || L.inside) return;
      var x = R.x0 < S.x0 + S.span / 2 ? R.x1 + hh * 0.5 : R.x0 - hh * 1.1; if (x < S.x0 + hh * 0.9 || x > S.x1 - hh * 1.6) return;
      var cl = K.town(S, 9, { casual: 1 })[8], ms = K.town(S, 10, { sin: 1 })[9]; cl.dir = 1; ms.dir = -1; ms.skirt = 0;
      var y = S.deck + hh * 0.2, rec = { lean: -0.85, seat: 0.36, legs: [1.25, -0.05, 1.32, -0.08], arms: [0.2, 0.4, 0.1, 0.5] };
      paper(c, poly([[x - hh * 0.2, y], [x - hh * 0.18, y - hh * 0.3], [x - hh * 0.4, y - hh * 0.7], [x - hh * 0.28, y - hh * 0.74], [x - hh * 0.04, y - hh * 0.34], [x + hh * 0.42, y - hh * 0.3], [x + hh * 0.42, y - hh * 0.24], [x + hh * 0.36, y]]), '#7a4a2a', 1);
      var Jr = joints(x, y, hh * 0.86, rec, 1); person(c, x, y, hh * 0.86, rec, cl); var ft = Jr.f1, cir = [Math.cos(S.t / 260) * hh * 0.012, Math.sin(S.t / 260) * hh * 0.012], sx2 = x + hh * 0.85;
      person(c, sx2, y, hh * 0.86, reach(sx2, y, hh * 0.86, { lean: 0.4, seat: 0.3, legs: [1.3, -1.3, 1.2, -1.2], arms: [0, 0, 0, 0] }, -1, [ft[0] + hh * 0.02 + cir[0], ft[1] - hh * 0.02 + cir[1]], [ft[0] + hh * 0.05 - cir[0], ft[1] + hh * 0.01 - cir[1]]), ms);
    }
  });
}
function massage(S) {
  if (S.place) { if (D.civic) return massagePlace(S, D.civic); if (D.need) D.need('clinic'); }
  var c = S.c, hh = S.hh;
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1d18' : '#8a6a4a');
  var top = under(S, S.night ? '#22423f' : '#2f6f6a'), sx0 = S.x0, sx1 = S.x1, w = sx1 - sx0, eave = top + (S.deck - top) * 0.32, crew = K.town(S, 4, { casual: 0.6, sin: 0.4 });
  /* herbs hung from the beam to dry, swinging as pendulums */
  for (var i = 0; i < 4; i++) { var hx = sx0 + w * (0.12 + i * 0.25), th = 0.12 * Math.sin(S.t / 900 + i), L = hh * (0.22 + (i % 2) * 0.08), ex = hx + Math.sin(th) * L, ey = eave + Math.cos(th) * L;
    c.strokeStyle = '#3a2416'; c.lineWidth = 1; c.beginPath(); c.moveTo(hx, eave); c.lineTo(ex, ey); c.stroke();
    for (var l = 0; l < 5; l++) { c.fillStyle = ['#5a8a3a', '#7aa84a', '#4a7a32'][l % 3]; c.beginPath(); c.ellipse(ex + (l - 2) * 2.2, ey + hh * 0.06, 1.8, hh * 0.07, (l - 2) * 0.2, 0, TAU); c.fill(); } }
  /* tok sen: the mat, the one lying, the one who taps */
  var need = hh * 4.1, mx0 = sx0 + Math.max(w * 0.03, (w - need) * 0.5), mw = hh * 1.25;
  paper(c, rect(mx0, S.deck - hh * 0.04, mw, hh * 0.06), '#b8342a', 0.6);
  c.fillStyle = '#f2c94c'; c.fillRect(mx0, S.deck - hh * 0.04, mw, 1.5);
  var lh = hh * 1.05, lx = mx0 + hh * 0.06, ly = S.deck - hh * 0.12, c0 = crew[0]; c0.garb = 'casual'; c0.long = true; c0.col = '#7a3a5a'; c0.low = '#7a3a5a';
  var kx = lx + lh * 0.5, kneel = { lean: 0.35, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0, 0, 0, 0] }, kh = hh * 0.95, ky = S.deck - hh * 0.03;
  var px = lx + lh * 0.66, backY = ly - lh * 0.08, pegTop = backY - hh * 0.12;
  var f = 2.2, ph = Math.PI * f * S.t / 1000, swing = 1.1 * Math.abs(Math.sin(ph)), tau = (S.t / 1000 * f) % 1 / f;
  var Jk = joints(kx - hh * 0.22, ky, kh, kneel, 1), pivot = [px - hh * 0.2, pegTop - hh * 0.04];
  var head = [pivot[0] + Math.cos(swing) * hh * 0.2, pivot[1] - Math.sin(swing) * hh * 0.2];
  var c1 = crew[1]; c1.dir = 1; c1.skirt = 0;
  person(c, kx - hh * 0.22, ky, kh, reach(kx - hh * 0.22, ky, kh, kneel, 1, pivot, [px - 2, pegTop + hh * 0.05]), c1);
  lying(c, lx, ly, lh, c0);
  /* the sen line, and the ring that runs along it after each tap: y = A·e^(−λt)·sin(kx − ωt) */
  var s0 = lx + lh * 0.12, s1 = lx + lh * 0.9, amp = hh * 0.05 * Math.exp(-tau * 6);
  c.save(); c.shadowColor = 'rgba(255,200,60,.9)'; c.shadowBlur = 5; c.strokeStyle = 'rgba(255,214,90,.95)'; c.lineWidth = 1.8; c.beginPath();
  for (var sx = s0; sx <= s1; sx += 2) { var dd = Math.abs(sx - px), env = Math.exp(-dd / (hh * 0.35)), yy = backY - 2 - amp * env * Math.sin(dd * 0.35 - tau * 40); sx === s0 ? c.moveTo(sx, yy) : c.lineTo(sx, yy); } c.stroke(); c.restore();
  K.lanternGlow(c, px, backY, hh * 0.05, 45, Math.exp(-tau * 5));
  c.strokeStyle = '#8a5a2a'; c.lineWidth = Math.max(2, hh * 0.035); c.beginPath(); c.moveTo(px, backY - 1); c.lineTo(px, pegTop); c.stroke();
  c.strokeStyle = '#6a3a1a'; c.lineWidth = Math.max(1.5, hh * 0.025); c.beginPath(); c.moveTo(pivot[0], pivot[1]); c.lineTo(head[0], head[1]); c.stroke();
  c.save(); c.translate(head[0], head[1]); c.rotate(-swing); paper(c, rect(-hh * 0.03, -hh * 0.06, hh * 0.08, hh * 0.1), '#9a6a3a', 0.6); c.restore();
  for (var rg = 0; rg < 2; rg++) { var rr = (tau * f + rg * 0.5) % 1; c.strokeStyle = 'rgba(255,214,120,' + (0.6 * (1 - rr)).toFixed(3) + ')'; c.lineWidth = 1; c.beginPath(); c.arc(px, pegTop, hh * 0.05 + rr * hh * 0.18, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); }
  /* the herbal compress, steamed in the pot and pressed to the shoulder */
  var sxp = mx0 + mw + hh * 0.75;
  if (sxp + hh * 0.9 < sx1) {
    var c2 = crew[2], c3 = crew[3]; c2.dir = 1; c2.skirt = 0; c3.dir = 1; c3.skirt = 0; c3.long = true;
    var seated = { lean: 0.15, seat: 0.1, legs: POSE.lotus.legs, arms: [0.4, 0.6, 0.3, 0.7] }, Js = joints(sxp, S.deck, hh * 0.92, seated, 1);
    var press = 0.5 - 0.5 * Math.cos(S.t / 1000 * TAU * 0.6), cp = [Js.sh[0] - hh * 0.05, Js.sh[1] - hh * 0.03 - press * hh * 0.06];
    var mp = { lean: 0.25, seat: 0.22, legs: [0.9, -2.4, 0.9, -2.4], arms: [0, 0, 0, 0] };
    person(c, sxp - hh * 0.42, S.deck, hh * 0.95, reach(sxp - hh * 0.42, S.deck, hh * 0.95, mp, 1, [cp[0] - hh * 0.04, cp[1]], [cp[0] - hh * 0.03, cp[1] + hh * 0.04]), c2);
    person(c, sxp, S.deck, hh * 0.92, seated, c3);
    steam(c, cp[0], cp[1] - hh * 0.06, hh, S.t, 2, 4, hh * 0.45, 0.55);
    paper(c, function (q) { q.beginPath(); q.arc(cp[0], cp[1], hh * 0.07, 0, TAU); }, '#e8dcc0', 0.6);
    c.strokeStyle = '#7a5a2a'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(cp[0] - hh * 0.03, cp[1] - hh * 0.06); c.lineTo(cp[0], cp[1] - hh * 0.12); c.lineTo(cp[0] + hh * 0.03, cp[1] - hh * 0.06); c.stroke();
    /* the pot on its stove, coals glowing */
    var pot = sxp + hh * 0.55;
    if (pot + hh * 0.2 < sx1) {
      paper(c, rect(pot - hh * 0.12, S.deck - hh * 0.16, hh * 0.24, hh * 0.16), '#8a5a3a', 0.8);
      K.lanternGlow(c, pot, S.deck - hh * 0.08, hh * 0.05, 20, 0.7 + 0.3 * Math.sin(S.t / 200));
      paper(c, function (q) { q.beginPath(); q.ellipse(pot, S.deck - hh * 0.26, hh * 0.15, hh * 0.1, 0, 0, TAU); }, '#4a4a52', 1);
      steam(c, pot, S.deck - hh * 0.36, hh, S.t, 4, 5, hh * 0.8, 0.5);
    }
    /* feet: the one reclining, the one on the stool, thumbs pressing in small circles */
    var fx = pot + hh * 0.5;
    if (fx + hh * 1.15 < sx1) {
      var c4 = K.town(S, 6, { casual: 0.5, sin: 0.5 }), cl = c4[4], ms = c4[5]; cl.dir = 1; cl.skirt = 0; ms.dir = -1; ms.skirt = 0;
      paper(c, poly([[fx - hh * 0.2, S.deck], [fx - hh * 0.18, S.deck - hh * 0.3], [fx - hh * 0.42, S.deck - hh * 0.72], [fx - hh * 0.3, S.deck - hh * 0.76], [fx - hh * 0.04, S.deck - hh * 0.36], [fx + hh * 0.42, S.deck - hh * 0.32], [fx + hh * 0.42, S.deck - hh * 0.26], [fx + hh * 0.36, S.deck]]), S.night ? '#4a2e1c' : '#7a4a2a', 1);
      var rec = { lean: -0.85, seat: 0.36, legs: [1.25, -0.05, 1.32, -0.08], arms: [0.2, 0.4, 0.1, 0.5] }, Jr = joints(fx, S.deck, hh * 0.92, rec, 1);
      person(c, fx, S.deck, hh * 0.92, rec, cl);
      var cir = [Math.cos(S.t / 260) * hh * 0.012, Math.sin(S.t / 260) * hh * 0.012], ft = Jr.f1, sx2 = ft[0] + hh * 0.42;
      paper(c, rect(sx2 - hh * 0.12, S.deck - hh * 0.18, hh * 0.24, hh * 0.18), S.night ? '#4a2e1c' : '#8a5a3a', 0.8);
      var sp2 = { lean: 0.4, seat: 0.3, legs: [1.3, -1.3, 1.2, -1.2], arms: [0, 0, 0, 0] };
      person(c, sx2, S.deck, hh * 0.92, reach(sx2, S.deck, hh * 0.92, sp2, -1, [ft[0] + hh * 0.02 + cir[0], ft[1] - hh * 0.02 + cir[1]], [ft[0] + hh * 0.05 - cir[0], ft[1] + hh * 0.01 - cir[1]]), ms);
      c.fillStyle = 'rgba(255,214,90,.8)'; c.beginPath(); c.arc(ft[0], ft[1] - hh * 0.01, hh * 0.018 * (1 + 0.5 * Math.sin(S.t / 260)), 0, TAU); c.fill();
    }
  }
  K.banner(c, (sx0 + sx1) / 2, top + hh * 0.6, S.label, hh, '#2f6f6a', S.seed, S.hits);
  bodyBox(S, top);
}

/* ---------------------------------------------------------------- elephants */
/* an Asian elephant: twin domes, a small ear that fans, the trunk a chain of joints on a
   travelling wave, θₖ = a·sin(ωt − kφ); curl (0 … 1) lifts it to spray */
function elephant(c, x, y, s, dir, t, o) {
  var skin = o.skin, far = o.far, sw = Math.sin(t / 650 + o.k), cyb = y - s * 0.6;
  function leg(lx, col) { paper(c, function (q) { q.beginPath(); q.moveTo(lx - s * 0.1, cyb); q.lineTo(lx - s * 0.11, y); q.quadraticCurveTo(lx, y + s * 0.03, lx + s * 0.11, y); q.lineTo(lx + s * 0.1, cyb); q.closePath(); }, col, 0.8); }
  leg(x + dir * s * 0.4, far); leg(x - dir * s * 0.28, far);
  /* the tail */
  var tx = x - dir * s * 0.58, ty = y - s * 0.78; c.strokeStyle = skin; c.lineWidth = Math.max(1.5, s * 0.03); c.beginPath(); c.moveTo(tx, ty); c.quadraticCurveTo(tx - dir * s * 0.06, ty + s * 0.2, tx - dir * s * 0.04 + sw * s * 0.05, ty + s * 0.38); c.stroke();
  paper(c, function (q) { q.beginPath(); q.ellipse(x - dir * s * 0.04, cyb - s * 0.08, s * 0.58, s * 0.34, 0, 0, TAU); q.moveTo(x - dir * s * 0.3, cyb - s * 0.3); q.ellipse(x - dir * s * 0.12, cyb - s * 0.28, s * 0.3, s * 0.2, 0, 0, TAU); }, skin, 1.6);
  leg(x + dir * s * 0.3, skin); leg(x - dir * s * 0.38, skin);
  if (o.mud) { c.save(); c.beginPath(); c.ellipse(x - dir * s * 0.04, cyb - s * 0.08, s * 0.58, s * 0.34, 0, 0, TAU); c.clip(); c.fillStyle = o.mud;
    [[-0.2, -0.3, 0.2], [0.1, -0.35, 0.16], [-0.35, -0.1, 0.14], [0.25, -0.05, 0.1]].forEach(function (m) { c.beginPath(); c.ellipse(x + dir * m[0] * s, cyb + m[1] * s, m[2] * s * 1.3, m[2] * s, 0.4, 0, TAU); c.fill(); }); c.restore(); }
  /* head, domes, ear */
  var hx = x + dir * s * 0.5, hy = y - s * 0.86;
  paper(c, function (q) { q.beginPath(); q.arc(hx, hy, s * 0.26, 0, TAU); q.moveTo(hx - dir * s * 0.02 + s * 0.13, hy - s * 0.2); q.arc(hx - dir * s * 0.02, hy - s * 0.2, s * 0.13, 0, TAU); q.moveTo(hx + dir * s * 0.12 + s * 0.12, hy - s * 0.17); q.arc(hx + dir * s * 0.12, hy - s * 0.17, s * 0.12, 0, TAU); }, skin, 1.4);
  var ef = 1 + 0.15 * Math.sin(t / 420 + o.k);
  c.fillStyle = o.ear; c.beginPath(); c.moveTo(hx - dir * s * 0.08, hy - s * 0.12); c.quadraticCurveTo(hx - dir * s * 0.32 * ef, hy - s * 0.1, hx - dir * s * 0.26 * ef, hy + s * 0.14); c.quadraticCurveTo(hx - dir * s * 0.15, hy + s * 0.24, hx - dir * s * 0.04, hy + s * 0.08); c.closePath(); c.fill();
  c.fillStyle = '#1c1410'; c.beginPath(); c.arc(hx + dir * s * 0.12, hy - s * 0.04, Math.max(1.2, s * 0.022), 0, TAU); c.fill();
  /* the trunk */
  var N = 10, sl = s * 0.075, p = [hx + dir * s * 0.2, hy + s * 0.08], th = 0.15, pts = [p.slice()], cur = o.curl || 0;
  for (var k = 0; k < N; k++) { th += cur * 0.36 + 0.06 * Math.sin(t / 520 - k * 0.55 + o.k) + (cur ? 0 : 0.02); p = [p[0] + dir * Math.sin(th) * sl, p[1] + Math.cos(th) * sl]; pts.push(p.slice()); }
  c.lineCap = 'round'; c.strokeStyle = skin;
  for (k = 0; k < N; k++) { c.lineWidth = s * (0.13 - k * 0.008); c.beginPath(); c.moveTo(pts[k][0], pts[k][1]); c.lineTo(pts[k + 1][0], pts[k + 1][1]); c.stroke(); }
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; c.beginPath(); for (k = 1; k < N; k += 2) { var a = pts[k], b2 = pts[k + 1], nx = -(b2[1] - a[1]), ny = b2[0] - a[0], nl = Math.hypot(nx, ny) || 1, wd = s * (0.06 - k * 0.004); c.moveTo(a[0] + nx / nl * wd, a[1] + ny / nl * wd); c.lineTo(a[0] - nx / nl * wd, a[1] - ny / nl * wd); } c.stroke();
  return { tip: pts[N], dir2: [pts[N][0] - pts[N - 1][0], pts[N][1] - pts[N - 1][1]], head: [hx, hy] };
}
/* water thrown or sprayed: drops on parabolas, y = v₀t − ½gt² */
function spray(c, x, y, vx, vy, g, life, n, t, k, col) {
  c.fillStyle = col;
  for (var i = 0; i < n; i++) { var u = ((t / 1000) / life + i / n + k) % 1, tt = u * life, j = 0.85 + 0.3 * ((i * 37) % 11) / 11, px = x + vx * j * tt, py = y - vy * j * tt + 0.5 * g * tt * tt;
    c.globalAlpha = 1 - u * 0.5; c.beginPath(); c.arc(px, py, 2 + (i % 3) * 0.8, 0, TAU); c.fill(); }
  c.globalAlpha = 1;
}
function bamboo(c, x, y, hh, t, k, night) {
  var col = night ? '#2f4a32' : '#5a8a3a', leaf = night ? '#24402a' : '#4f8a3a';
  for (var i = 0; i < 5; i++) { var bx = x + (i - 2) * hh * 0.07, ht = hh * (1.5 + (i % 3) * 0.22), bend = (i - 2) * 0.12 + Math.sin(t / 1800 + i + k) * 0.04, tx = bx + Math.sin(bend) * ht, ty = y - Math.cos(bend) * ht * 0.98;
    c.strokeStyle = col; c.lineWidth = Math.max(1.5, hh * 0.035); c.beginPath(); c.moveTo(bx, y); c.quadraticCurveTo(bx + Math.sin(bend) * ht * 0.3, y - ht * 0.6, tx, ty); c.stroke();
    c.fillStyle = leaf; for (var l = 0; l < 4; l++) { var lu = 0.45 + l * 0.17, lx = lerp(bx, tx, lu * lu), ly = lerp(y, ty, lu); c.beginPath(); c.ellipse(lx + (l % 2 ? 1 : -1) * hh * 0.08, ly, hh * 0.1, hh * 0.025, (l % 2 ? 0.4 : -0.4), 0, TAU); c.fill(); } }
}
function elephants(S) {
  var c = S.c, hh = S.hh, i, night = S.night, ws = S.deck - hh * 0.1, Pl = S.place, Cv = D.civic, ste = Pl ? K.openNow(Pl.hours, S.now) : null, quietE = Pl && (ste === false || ste === null && night), re = rnd((S.seed ^ 0xe1e) >>> 0);
  if (Pl && !Cv && D.need) D.need('clinic');
  if (Pl) K.setting(S);
  /* the far bank, bamboo and bananas */
  paper(c, function (q) { jag(q, [[S.x0 - 4, ws - hh * 0.28], [S.x0 + S.span * 0.3, ws - hh * 0.34], [S.x0 + S.span * 0.7, ws - hh * 0.3], [S.x1 + 4, ws - hh * 0.36], [S.x1 + 4, ws + 6], [S.x0 - 4, ws + 6]], 17, 2); }, night ? '#2a3a26' : '#6a8a44', 1);
  var r = rnd(S.seed + 5);
  for (i = 0; i < 3; i++) bamboo(c, S.x0 + S.span * (0.12 + i * 0.36 + r() * 0.1), ws - hh * 0.3, hh, S.t, i, night);
  paper(c, rect(S.x0 - 4, ws, S.span + 8, S.H - ws + 4), night ? '#1f3a44' : '#3f7f8a', 1);
  /* who is in the river */
  var big = Math.min(hh * 1.35, S.span * 0.2), ex = S.x0 + S.span * ((S.seed >> 3) % 2 ? 0.36 : 0.6), dir = (S.seed >> 4) % 2 ? 1 : -1;
  var skin = night ? '#5c5a62' : '#7e7a82', ear = night ? '#4c4a52' : '#6c6870', far = night ? '#4a484f' : '#68646c', mud = night ? '#4a3a2c' : '#7a5e44';
  var T = 7, u = (S.t / 1000 % T) / T, curl = clamp(Math.sin((u - 0.3) / 0.45 * Math.PI), 0, 1) * (u > 0.3 && u < 0.75 ? 1 : 0);
  var cx = ex - dir * big * 1.15, cs = big * 0.55, bob = Math.abs(Math.sin(S.t / 600)) * hh * 0.04;
  var crew = K.town(S, 3, { mohom: 1 }); crew[2].garb = 'casual'; crew[2].col = '#b0302a'; crew[2].long = false;
  var Cf = elephant(c, cx, S.deck + hh * 0.14 - bob, cs, dir, S.t, { skin: skin, ear: ear, far: far, k: 2, curl: 0.3 + 0.25 * Math.sin(S.t / 800) });
  var E = elephant(c, ex, S.deck + hh * 0.16, big, dir, S.t, { skin: skin, ear: ear, far: far, mud: mud, k: 0, curl: curl * 1.25 });
  if (curl > 0.5) { var dl = Math.hypot(E.dir2[0], E.dir2[1]) || 1; spray(c, E.tip[0], E.tip[1], -dir * hh * 0.9, hh * 1.5, hh * 3.4, 0.85, 22, S.t, 0, 'rgba(225,245,255,.95)'); }
  /* people with buckets, throwing on the beat of the swing */
  var nP = quietE ? 0 : Math.max(1, Math.min(2, Math.floor(S.span / (hh * 2.6))));
  for (i = 0; i < nP; i++) {
    var side = i ? dir : -dir, px = ex + side * big * (i ? 1.05 : 0.95) + (i ? dir * hh * 0.1 : 0), pd = -side, d = crew[i]; d.dir = pd;
    var ph = (S.t / 1000 / 2.4 + i * 0.5) % 1, up = ph < 0.35 ? -0.4 + ph / 0.35 * 0.2 : ph < 0.5 ? -0.2 + (ph - 0.35) / 0.15 * 2.4 : 2.2 - (ph - 0.5) / 0.5 * 2.6;
    var me = person(c, px, S.deck + hh * 0.22, hh * 0.92, { lean: 0.1, legs: [0.2, -0.1, -0.15, 0], arms: [up, 0.3, up + 0.2, 0.25] }, d);
    var bk = me.hand[0]; paper(c, poly([[bk[0] - hh * 0.06, bk[1]], [bk[0] + hh * 0.06, bk[1]], [bk[0] + hh * 0.05, bk[1] + hh * 0.1], [bk[0] - hh * 0.05, bk[1] + hh * 0.1]]), ['#e2b33c', '#4d8fd1'][i], 0.5);
    if (ph > 0.45 && ph < 0.8) { var tt = (ph - 0.45) * 2.4; c.fillStyle = 'rgba(210,240,255,.85)'; for (var q = 0; q < 14; q++) { var ja = ((q * 7) % 13) / 13, jb = ((q * 5) % 11) / 11, xx = bk[0] + pd * hh * (0.6 + 0.7 * ja) * tt, yy = bk[1] - hh * (0.9 + 0.9 * jb) * tt + 0.5 * hh * 5 * tt * tt; c.beginPath(); c.arc(xx, yy, 1.3 + (q % 3) * 0.8, 0, TAU); c.fill(); } }
  }
  /* the mahout in a Karen shirt, a hand on the trunk */
  if (S.span > hh * 5.5 && !quietE) { var mx = E.head[0] + dir * big * 0.55, md = crew[2]; md.dir = -dir; person(c, mx, S.deck + hh * 0.24, hh * 0.9, { lean: 0.05, legs: [0.1, 0, -0.1, 0], arms: [1.3, 0.4, 0.2, 0.2] }, md);
    c.strokeStyle = '#f2e6c9'; c.lineWidth = 1; c.beginPath(); c.moveTo(mx - hh * 0.07, S.deck - hh * 0.2); c.lineTo(mx + hh * 0.07, S.deck - hh * 0.2); c.stroke(); }
  /* the water's face over the legs: a travelling wave, rings spreading where drops fall */
  c.fillStyle = night ? 'rgba(30,64,76,.88)' : 'rgba(70,140,152,.86)'; c.beginPath(); c.moveTo(S.x0 - 4, S.H + 4);
  for (var x = S.x0 - 4; x <= S.x1 + 4; x += 8) c.lineTo(x, S.deck + hh * 0.04 + Math.sin(x * 0.05 - S.t / 500) * 1.6); c.lineTo(S.x1 + 4, S.H + 4); c.fill();
  c.strokeStyle = 'rgba(255,255,255,.45)'; c.lineWidth = 1;
  [[ex, big * 0.6], [cx, cs * 0.6], [ex - dir * big * 0.4, big * 0.5]].forEach(function (p, k) { for (var j = 0; j < 2; j++) { var rr = ((S.t / 1800 + j * 0.5 + k * 0.3) % 1); c.globalAlpha = 1 - rr; c.beginPath(); c.ellipse(p[0], S.deck + hh * 0.06, p[1] * (0.6 + rr), hh * 0.05 * (0.6 + rr), 0, 0, TAU); c.stroke(); } });
  c.globalAlpha = 1;
  for (i = 0; i < 6; i++) { var gx = S.x0 + ((i * 0.17 * S.span + S.t / 1000 * hh * 0.15) % S.span); c.beginPath(); c.moveTo(gx, S.deck + hh * (0.25 + (i % 3) * 0.12)); c.lineTo(gx + hh * 0.25, S.deck + hh * (0.25 + (i % 3) * 0.12)); c.stroke(); }
  K.banner(c, ex - dir * big * 0.2, S.deck - hh * 2.02, S.label, hh, '#4f7d4a', S.seed, S.hits);
  if (Pl) {   /* on the far bank: a bamboo sala, a basket of bananas, the board with the name on its posts */
    var bxs = dir > 0 ? S.x1 - hh * 1.3 : S.x0 + hh * 1.3, sy = ws - hh * 0.3;
    if (re() < 0.7) { K.sala(c, bxs - hh * 0.7, bxs + hh * 0.7, sy, sy - hh * 1.0, night, re() < 0.5 ? (night ? '#5a4a2a' : '#b89a52') : null); }
    c.fillStyle = night ? '#6a5a32' : '#c9a36a'; c.beginPath(); c.moveTo(bxs - hh * 0.2, sy); c.lineTo(bxs + hh * 0.2, sy); c.lineTo(bxs + hh * 0.15, sy - hh * 0.18); c.lineTo(bxs - hh * 0.15, sy - hh * 0.18); c.fill();
    c.fillStyle = night ? '#a89a3a' : '#f2d24a'; for (var bn = 0; bn < 5; bn++) { c.beginPath(); c.ellipse(bxs - hh * 0.12 + bn * hh * 0.06, sy - hh * 0.2, hh * 0.025, hh * 0.08, 0.5, 0, TAU); c.fill(); }
    var sxe = dir > 0 ? S.x0 + hh * 2.0 : S.x1 - hh * 2.0, sye = S.deck - hh * 1.75;
    c.fillStyle = night ? '#4a2e1c' : '#7a4a2a'; c.fillRect(sxe - hh * 0.6, sye, 4, ws - sye); c.fillRect(sxe + hh * 0.6 - 4, sye, 4, ws - sye);
    if (Cv) Cv.signAt(c, S, sxe, sye, Pl, hh * 0.8, '#3f5a2a', null); else K.sign(c, sxe, sye, Pl, hh * 0.8, '#3f5a2a', null);
    if (Pl.river && Pl.river.name) { c.fillStyle = 'rgba(255,255,255,.85)'; c.font = 'italic 600 ' + Math.round(Math.max(9, hh * 0.12)) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'right'; c.textBaseline = 'middle'; c.fillText(Pl.river.name, S.x1 - 8, S.H - hh * 0.1); }
    S.hits.push({ k: 'place', x0: S.x0, x1: S.x1, y0: S.deck - big * 1.2, y1: S.H });
  }
  bodyBox(S, S.deck - big * 1.2);
}

/* ---------------------------------------------------------------- hot spring */
function hotspring(S) {
  var c = S.c, hh = S.hh, i, night = S.night, r = rnd(S.seed + 3);
  K.ground(c, S.x0, S.x1, S.deck, S.H, night ? '#2a2622' : '#b4a48a');
  /* the geyser: every 7 s a column of drops, y = v₀t − ½gt²; steam all the while */
  var gx = S.x0 + S.span * ((S.seed >> 3) % 2 ? 0.7 : 0.32), gy = S.deck - hh * 0.32, T = 7, u = (S.t / 1000 + 5 + (S.seed % 5) * 0.3) % T, g = hh * 9, v0 = Math.sqrt(2 * g * hh * 1.65);
  paper(c, function (q) { jag(q, [[gx - hh * 0.75, S.deck - hh * 0.05], [gx - hh * 0.35, gy - hh * 0.05], [gx - hh * 0.08, gy - hh * 0.15], [gx + hh * 0.1, gy - hh * 0.14], [gx + hh * 0.4, gy], [gx + hh * 0.8, S.deck - hh * 0.05]], 23, 3); }, night ? '#5a5248' : '#8a7e6e', 1.4);
  c.fillStyle = night ? '#d8e6e0' : '#e8f0ea'; c.beginPath(); c.ellipse(gx, gy - hh * 0.14, hh * 0.12, hh * 0.03, 0, 0, TAU); c.fill();
  steam(c, gx, gy - hh * 0.2, hh, S.t, 0, 6, hh * 1.5, 0.4, 1.6);
  if (u < 4.2) {
    var col = c.createLinearGradient(0, gy - hh * 1.8, 0, gy); col.addColorStop(0, 'rgba(240,250,255,0)'); col.addColorStop(1, 'rgba(240,250,255,.75)');
    var hmax = Math.min(1, u / 0.4) * Math.min(1, (4.2 - u) / 0.8) * v0 * v0 / (2 * g);
    c.fillStyle = col; c.beginPath(); c.moveTo(gx - hh * 0.06, gy - hh * 0.12); c.quadraticCurveTo(gx - hh * 0.03, gy - hmax * 0.6, gx, gy - hmax); c.quadraticCurveTo(gx + hh * 0.03, gy - hmax * 0.6, gx + hh * 0.06, gy - hh * 0.12); c.fill();
    c.fillStyle = 'rgba(235,248,255,.9)';
    for (i = 0; i < 26; i++) { var life = 2 * v0 / g * (0.6 + 0.4 * ((i * 7) % 10) / 10), launch = (i / 26) * 4.2, tt = (u - launch + 4.2) % 4.2;
      if (tt > life) continue; var vx = (((i * 13) % 9) - 4) * hh * 0.07, vy = v0 * (0.6 + 0.4 * ((i * 7) % 10) / 10);
      c.beginPath(); c.arc(gx + vx * tt, gy - hh * 0.14 - vy * tt + 0.5 * g * tt * tt, 1.4 + (i % 3) * 0.6, 0, TAU); c.fill(); }
  }
  /* bougainvillea along the back */
  for (i = 0; i < 4; i++) { var bgx = S.x0 + S.span * (0.08 + i * 0.27 + r() * 0.06); if (Math.abs(bgx - gx) < hh * 0.9) continue;
    paper(c, function (q) { circ(q, bgx, S.deck - hh * 0.22, hh * 0.24, i + 7); }, night ? '#24402a' : '#4f7d3a', 0.8);
    c.fillStyle = night ? '#a03a78' : '#e5468f'; for (var bl = 0; bl < 16; bl++) { var ba = bl * 2.4, br2 = hh * 0.2 * Math.sqrt(bl / 16); c.beginPath(); c.arc(bgx + Math.cos(ba) * br2, S.deck - hh * 0.24 + Math.sin(ba) * br2 * 0.8, hh * 0.035, 0, TAU); c.fill(); } }
  /* the boiling pool, the rack, eggs in baskets */
  var ex = gx > S.x0 + S.span * 0.5 ? S.x0 + S.span * 0.28 : S.x0 + S.span * 0.72, ey = S.deck + hh * 0.02, erx = Math.min(hh * 0.95, S.span * 0.18), ery = hh * 0.16;
  paper(c, function (q) { q.beginPath(); q.ellipse(ex, ey, erx + hh * 0.07, ery + hh * 0.05, 0, 0, TAU); }, night ? '#5a5248' : '#9a8e7a', 1.2);
  c.fillStyle = night ? '#4a7a78' : '#8fd0c4'; c.beginPath(); c.ellipse(ex, ey, erx, ery, 0, 0, TAU); c.fill();
  c.fillStyle = 'rgba(255,255,255,.7)'; for (i = 0; i < 14; i++) { var bu = (S.t / 700 + i * 0.37) % 1, bx = ex + (((i * 29) % 17) / 17 - 0.5) * erx * 1.6, by = ey + (((i * 11) % 7) / 7 - 0.5) * ery * 1.2; c.beginPath(); c.arc(bx, by - bu * 2, 0.8 + bu * 1.6, 0, TAU); c.fill(); }
  var rk = ey - hh * 0.95; c.strokeStyle = night ? '#6a5a3a' : '#a88a4a'; c.lineWidth = Math.max(2, hh * 0.04); c.beginPath(); c.moveTo(ex - erx * 0.9, ey); c.lineTo(ex - erx * 0.8, rk); c.lineTo(ex + erx * 0.8, rk); c.lineTo(ex + erx * 0.9, ey); c.stroke();
  for (i = 0; i < 4; i++) { var kx = ex + erx * (-0.6 + i * 0.4), dip = Math.sin(S.t / 1100 + i * 1.7) * hh * 0.04, ky = ey - hh * 0.06 + dip;
    c.strokeStyle = 'rgba(60,40,20,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(kx, rk); c.lineTo(kx, ky - hh * 0.12); c.stroke();
    paper(c, function (q) { q.beginPath(); q.moveTo(kx - hh * 0.09, ky - hh * 0.1); q.lineTo(kx + hh * 0.09, ky - hh * 0.1); q.lineTo(kx + hh * 0.07, ky); q.lineTo(kx - hh * 0.07, ky); q.closePath(); }, '#c9a36a', 0.5);
    c.fillStyle = '#fff6e6'; for (var e = 0; e < 3; e++) { c.beginPath(); c.ellipse(kx + (e - 1) * hh * 0.05, ky - hh * 0.12, hh * 0.028, hh * 0.035, 0, 0, TAU); c.fill(); }
    c.strokeStyle = 'rgba(90,60,20,.4)'; c.beginPath(); for (var wv = 0; wv < 3; wv++) { c.moveTo(kx - hh * 0.08, ky - hh * 0.08 + wv * hh * 0.03); c.lineTo(kx + hh * 0.08, ky - hh * 0.08 + wv * hh * 0.03); } c.stroke(); }
  var dpx = ex + (gx > ex ? -1 : 1) * (erx + hh * 0.3), dd2 = gx > ex ? 1 : -1, dk = K.town(S, 5)[4]; dk.dir = dd2; dk.skirt = 0;
  var dip2 = Math.sin(S.t / 1300) * 0.08, DP = person(c, dpx, ey + hh * 0.04, hh * 0.9, { lean: 0.45, seat: 0.22, legs: [1.6, -2.5, 1.5, -2.6], arms: [1.3 + dip2, 0.2, 1.1 + dip2, 0.3] }, dk);
  var stk = [DP.hand[0][0] + dd2 * hh * 0.42, DP.hand[0][1] + hh * 0.12 + dip2 * hh];
  c.strokeStyle = '#a88a4a'; c.lineWidth = 2; c.beginPath(); c.moveTo(DP.hand[0][0], DP.hand[0][1]); c.lineTo(stk[0], stk[1]); c.stroke();
  paper(c, rect(stk[0] - hh * 0.06, stk[1], hh * 0.12, hh * 0.08), '#c9a36a', 0.4); c.fillStyle = '#fff6e6'; c.beginPath(); c.ellipse(stk[0], stk[1] - 1, hh * 0.03, hh * 0.035, 0, 0, TAU); c.fill();
  c.fillStyle = 'rgba(143,208,196,.6)'; c.beginPath(); c.ellipse(ex, ey + ery * 0.3, erx * 0.9, ery * 0.6, 0, 0, Math.PI); c.fill();
  steam(c, ex - erx * 0.4, ey - hh * 0.1, hh, S.t, 1, 4, hh * 0.9, 0.4); steam(c, ex + erx * 0.4, ey - hh * 0.1, hh, S.t, 3, 4, hh * 0.9, 0.4);
  /* the sign on the rack */
  c.fillStyle = '#7a4a2a'; c.fillRect(ex - hh * 0.22, rk - hh * 0.2, hh * 0.44, hh * 0.17); c.fillStyle = '#f7e9c8'; c.font = '700 ' + Math.round(hh * 0.11) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ต้มไข่', ex, rk - hh * 0.115);
  /* feet in the warm channel */
  var cy0 = S.deck + hh * 0.14, crew = K.town(S, 6), n = Math.max(2, Math.min(6, Math.floor(S.span / (hh * 1.1))));
  for (i = 0; i < n; i++) { var px = S.x0 + S.span * (i + 0.5) / n + (i % 2 ? hh * 0.2 : -hh * 0.1), d = crew[i]; d.dir = i % 2 ? -1 : 1; d.skirt = 0;
    var kick = Math.sin(S.t / 700 + i * 2) * 0.25; if (Math.abs(px - ex) < erx + hh * 0.3) continue;
    person(c, px, cy0 + hh * 0.18, hh * 0.9, { lean: -0.05, seat: 0.42, legs: [1.45, -1.2 + kick, 1.45, -1.35 - kick], arms: [-0.5, 0.2, -0.4, 0.2] }, d); }
  paper(c, rect(S.x0 - 4, cy0, S.span + 8, hh * 0.05), night ? '#6a6258' : '#d8cdb8', 1);
  c.fillStyle = night ? 'rgba(60,110,110,.9)' : 'rgba(120,196,186,.9)'; c.fillRect(S.x0 - 4, cy0 + hh * 0.05, S.span + 8, hh * 0.2);
  c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 1; c.beginPath(); for (var x = S.x0; x < S.x1; x += 14) { var yy = cy0 + hh * 0.1 + Math.sin(x * 0.08 - S.t / 400) * 1.5; c.moveTo(x, yy); c.lineTo(x + 7, yy); } c.stroke();
  paper(c, rect(S.x0 - 4, cy0 + hh * 0.25, S.span + 8, S.H - cy0), night ? '#5a5248' : '#c4b8a2', 1);
  for (i = 0; i < 4; i++) steam(c, S.x0 + S.span * (0.15 + i * 0.24), cy0 + hh * 0.06, hh, S.t, 5 + i, 3, hh * 0.5, 0.3);
  if (night) for (i = 0; i < 3; i++) { var lx = S.x0 + S.span * (0.2 + i * 0.3); K.lanternGlow(c, lx, S.deck - hh * 0.9, 5, 40, 0.8); c.fillStyle = '#ffb347'; c.beginPath(); c.ellipse(lx, S.deck - hh * 0.9, 4, 6, 0, 0, TAU); c.fill(); c.strokeStyle = '#3a2416'; c.beginPath(); c.moveTo(lx, S.deck - hh * 0.9 + 6); c.lineTo(lx, S.deck); c.stroke(); }
  K.banner(c, gx + (gx > S.x0 + S.span * 0.5 ? -1 : 1) * hh * 1.5, S.deck - hh * 1.85, S.label, hh, '#4a8f9a', S.seed, S.hits);
  bodyBox(S, S.deck - hh * 1.8);
}

/* ---------------------------------------------------------------- cooking class */
function plants(c, x0, x1, y, hh, t, night, k) {
  for (var x = x0 + hh * 0.15, i = 0; x < x1 - hh * 0.1; x += hh * 0.34, i++) {
    var kind = (i + k) % 3, sw = Math.sin(t / 1500 + i) * 0.06;
    if (kind === 0) { c.strokeStyle = night ? '#3a5a2a' : '#7aa84a'; c.lineWidth = 1.5; c.beginPath(); for (var b = -3; b <= 3; b++) { c.moveTo(x, y); c.quadraticCurveTo(x + b * hh * 0.03, y - hh * 0.2, x + b * hh * 0.06 + sw * hh, y - hh * (0.38 - Math.abs(b) * 0.04)); } c.stroke(); }
    else { c.fillStyle = night ? '#2f4a2a' : '#4f8a3a'; for (var l = 0; l < 5; l++) { c.beginPath(); c.ellipse(x + (l - 2) * hh * 0.05 + sw * hh * 0.3, y - hh * (0.08 + (l % 3) * 0.06), hh * 0.05, hh * 0.03, (l - 2) * 0.5, 0, TAU); c.fill(); }
      if (kind === 1) { c.fillStyle = '#d9342b'; for (l = 0; l < 3; l++) { c.beginPath(); c.ellipse(x + (l - 1) * hh * 0.06, y - hh * 0.06, hh * 0.012, hh * 0.035, 0.3, 0, TAU); c.fill(); } } }
  }
}
/* a cooking school, one place, behind a front dealt by D.civic.shop (a teak house, a row, a
   shophouse, glass) when it is not a farm under a sala: the bench of woks (the toss on parabolas,
   y = v₀t − ½gt²), aprons, the teacher's ladle, steam; shut when its hours say so */
function cookingPlace(S, C) {
  var hh = S.hh;
  C.shop(S, 'cooking', {
    kinds: ['teak', 'row', 'shop', 'glass', 'teak'], back: C.pick(K.rnd(S.seed + 3), ['#f2e6c9', '#e8d8c0', '#f4ecd8', '#dfe8d8']), floor: '#b89a6a', iconBg: '#f8f4e8',
    icon: function (q, S, x, y, s) { q.fillStyle = '#2a2a30'; q.beginPath(); q.arc(x, y - s * 0.1, s * 0.6, Math.PI * 0.1, Math.PI * 0.9); q.closePath(); q.fill(); q.strokeStyle = '#7a7a82'; q.lineWidth = Math.max(1.5, s * 0.1); q.beginPath(); q.moveTo(x + s * 0.5, y); q.lineTo(x + s * 0.95, y - s * 0.3); q.stroke(); q.fillStyle = '#d9342b'; q.beginPath(); q.arc(x - s * 0.2, y - s * 0.6, s * 0.1, 0, TAU); q.arc(x + s * 0.15, y - s * 0.75, s * 0.08, 0, TAU); q.fill(); },
    room: function (q, S, R) { var w = R.x1 - R.x0; q.fillStyle = '#7a5232'; q.fillRect(R.x0 + w * 0.08, R.y1 - hh * 0.4, w * 0.84, hh * 0.4); q.fillStyle = '#a8784a'; q.fillRect(R.x0 + w * 0.06, R.y1 - hh * 0.44, w * 0.88, hh * 0.05);
      for (var p = 0; p < 5; p++) { q.fillStyle = '#8a8a92'; q.fillRect(R.x0 + w * (0.12 + p * 0.17), R.y0 + hh * 0.12, 2, hh * 0.14); q.beginPath(); q.arc(R.x0 + w * (0.12 + p * 0.17) + 1, R.y0 + hh * 0.3, hh * 0.04, 0, TAU); q.fill(); }
      plants(q, R.x0 + w * 0.05, R.x1 - w * 0.05, R.y1 - hh * 0.44, hh * 0.7, 0, S.night, S.seed % 3); return { top: R.y1 - hh * 0.44 }; },
    work: function (c, S, R, L, o) {
      var w = R.x1 - R.x0, t = S.t, n = Math.max(2, Math.min(4, Math.floor(w / (hh * 0.85)))), crew = K.town(S, n, { casual: 0.7, sin: 0.3 }), bt = o.top, aprons = ['#e5567f', '#4d8fd1', '#e2b33c', '#4fae8c'];
      for (var i = 0; i < n; i++) { var px = R.x0 + w * (i + 0.4) / n, d = crew[i]; d.dir = 1; d.garb = 'casual'; d.skirt = 0; var wk = [px + hh * 0.28, bt - hh * 0.04], a = t / 1000 * TAU * 0.8 + i * 1.3, hand = [wk[0] - hh * 0.06 + Math.cos(a) * hh * 0.05, wk[1] - hh * 0.12 + Math.sin(a) * hh * 0.03];
        var me = person(c, px, R.y1 - hh * 0.02, hh * 0.88, reach(px, R.y1 - hh * 0.02, hh * 0.88, { lean: 0.1, legs: [0.06, 0, -0.06, 0], arms: [0.5, 0.6, 0.4, 0.8] }, 1, hand, [wk[0] - hh * 0.2, wk[1] - hh * 0.02]), d);
        paper(c, function (q) { q.beginPath(); q.moveTo(me.sh[0] - hh * 0.06, me.sh[1] + hh * 0.04); q.lineTo(me.sh[0] + hh * 0.08, me.sh[1] + hh * 0.04); q.lineTo(me.hip[0] + hh * 0.1, me.hip[1] + hh * 0.1); q.lineTo(me.hip[0] - hh * 0.06, me.hip[1] + hh * 0.1); q.closePath(); }, aprons[(i + S.seed) % 4], 0.4);
        c.fillStyle = '#2a2a30'; c.beginPath(); c.arc(wk[0], wk[1] - hh * 0.06, hh * 0.14, Math.PI * 0.15, Math.PI * 0.85); c.closePath(); c.fill(); c.strokeStyle = '#7a7a82'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(me.hand[0][0], me.hand[0][1]); c.lineTo(wk[0], wk[1] - hh * 0.03); c.stroke();
        var u = (t / 1000 / 1.8 + i * 0.4) % 1, tt = u * 0.7; if (u < 0.55) for (var p = 0; p < 3; p++) { var yy = wk[1] - hh * 0.05 - hh * (1.2 + p * 0.15) * tt + 0.5 * hh * 9 * tt * tt; if (yy > wk[1] - hh * 0.04) continue; c.fillStyle = ['#7fbf4a', '#d9342b', '#f2c94c'][p]; c.beginPath(); c.arc(wk[0] + (p - 1) * hh * 0.08 * tt, yy, Math.max(1.5, hh * 0.02), 0, TAU); c.fill(); }
        steam(c, wk[0], wk[1] - hh * 0.1, hh, t, i, 3, hh * 0.5, 0.4); }
    }
  });
}
function cooking(S) {
  var Pl = S.place, Cv = D.civic, stc = Pl ? K.openNow(Pl.hours, S.now) : null;
  if (Pl && !Cv && D.need) D.need('clinic');
  if (Pl && Cv && (stc === false || stc === null && S.night || !/farm|ฟาร์ม|garden|สวน|organic/i.test(Cv.words(Pl)) && (S.seed >>> 4) % 2)) return cookingPlace(S, Cv);
  var c = S.c, hh = S.hh, i, night = S.night, X0 = S.x0, X1 = S.x1;
  K.ground(c, S.x0, S.x1, S.deck, S.H, night ? '#2a2018' : '#8a7a50');
  if (Pl) K.setting(S);
  var top = under(S, night ? '#5a2a20' : '#b0502f'), sx0 = S.x0, sx1 = S.x1, w = sx1 - sx0;
  plants(c, X0 + hh * 0.7, sx0 - hh * 0.1, S.deck + hh * 0.2, hh, S.t, night, 0); plants(c, sx1 + hh * 0.1, X1 - hh * 0.8, S.deck + hh * 0.2, hh, S.t, night, 1);
  /* the teacher at the end of the bench, a ladle raised */
  var tx = sx0 + hh * 0.4, crew = K.town(S, 5, { casual: 0.7, sin: 0.3 }), tt = crew[0]; tt.dir = 1; tt.col = '#f4f1e8'; tt.garb = 'casual'; tt.long = false;
  var wave = 0.25 * Math.sin(S.t / 700), T = person(c, tx, S.deck, hh, { lean: 0, legs: [0.08, 0, -0.08, 0], arms: [2.5 + wave, 0.3, 0.6, 0.9] }, tt);
  paper(c, function (q) { var hx = T.head[0], hy = T.head[1] - hh * 0.08; q.beginPath(); q.rect(hx - hh * 0.08, hy - hh * 0.08, hh * 0.16, hh * 0.08); q.moveTo(hx + hh * 0.13, hy - hh * 0.12); q.arc(hx, hy - hh * 0.12, hh * 0.13, 0, TAU); }, '#ffffff', 0.6);
  c.strokeStyle = '#7a7a82'; c.lineWidth = 2; c.beginPath(); c.moveTo(T.hand[0][0], T.hand[0][1]); c.lineTo(T.hand[0][0] + hh * 0.05, T.hand[0][1] - hh * 0.2); c.stroke();
  c.fillStyle = '#7a7a82'; c.beginPath(); c.arc(T.hand[0][0] + hh * 0.06, T.hand[0][1] - hh * 0.22, hh * 0.04, 0, Math.PI); c.fill();
  /* the students behind the bench, woks on the fire */
  var bx0 = tx + hh * 0.38, bx1 = sx1 - w * 0.03, bt = S.deck - hh * 0.42, ns = Math.max(1, Math.min(4, Math.floor((bx1 - bx0) / (hh * 0.85)))), aprons = ['#e5567f', '#4d8fd1', '#e2b33c', '#4fae8c'];
  var woks = [];
  for (i = 0; i < ns; i++) {
    var px = bx0 + (bx1 - bx0) * (i + 0.5) / ns, d = crew[i + 1]; d.dir = 1; d.garb = 'casual'; d.skirt = 0;
    var wk = [px + hh * 0.3, bt - hh * 0.05], pound = i === ns - 1 && ns > 1, a = S.t / 1000 * TAU * 0.8 + i * 1.3;
    var hand = pound ? [wk[0] - hh * 0.04, bt - hh * 0.2 - hh * 0.12 * Math.abs(Math.sin(S.t / 1000 * Math.PI * 2.4))] : [wk[0] - hh * 0.06 + Math.cos(a) * hh * 0.05, wk[1] - hh * 0.12 + Math.sin(a) * hh * 0.03];
    var P = reach(px, S.deck - hh * 0.04, hh * 0.98, { lean: 0.1, legs: [0.06, 0, -0.06, 0], arms: [0.5, 0.6, 0.4, 0.8] }, 1, hand, [wk[0] - hh * 0.2, wk[1] - hh * 0.02]);
    var me = person(c, px, S.deck - hh * 0.04, hh * 0.98, P, d);
    paper(c, function (q) { q.beginPath(); q.moveTo(me.sh[0] - hh * 0.06, me.sh[1] + hh * 0.04); q.lineTo(me.sh[0] + hh * 0.08, me.sh[1] + hh * 0.04); q.lineTo(me.hip[0] + hh * 0.1, me.hip[1] + hh * 0.12); q.lineTo(me.hip[0] - hh * 0.06, me.hip[1] + hh * 0.12); q.closePath(); }, aprons[(i + S.seed) % 4], 0.4);
    woks.push({ x: wk[0], y: wk[1], hand: me.hand[0], pound: pound, i: i });
  }
  paper(c, rect(bx0 - hh * 0.05, bt, bx1 - bx0 + hh * 0.1, hh * 0.06), night ? '#6a4a2a' : '#a8784a', 1.2);
  paper(c, rect(bx0, bt + hh * 0.06, bx1 - bx0, S.deck - bt - hh * 0.06), night ? '#4a3220' : '#7a5232', 1.2);
  c.fillStyle = 'rgba(0,0,0,.18)'; for (var pl = bx0 + hh * 0.2; pl < bx1; pl += hh * 0.3) c.fillRect(pl, bt + hh * 0.1, 2, S.deck - bt - hh * 0.14);
  woks.forEach(function (k) {
    if (k.pound) {
      /* the mortar and pestle: y = A·|sin ωt|, chili flecks at each strike */
      paper(c, function (q) { q.beginPath(); q.moveTo(k.x - hh * 0.12, bt - hh * 0.12); q.lineTo(k.x + hh * 0.12, bt - hh * 0.12); q.lineTo(k.x + hh * 0.08, bt); q.lineTo(k.x - hh * 0.08, bt); q.closePath(); }, '#b8683a', 0.8);
      c.strokeStyle = '#8a5a2a'; c.lineWidth = Math.max(2.5, hh * 0.05); c.lineCap = 'round'; c.beginPath(); c.moveTo(k.hand[0], k.hand[1]); c.lineTo(k.x, k.hand[1] + hh * 0.18); c.stroke();
      var ps = (S.t / 1000 * 2.4) % 1; if (ps < 0.35) { c.fillStyle = '#d9342b'; for (var q = 0; q < 5; q++) { var ft = ps, vx = (q - 2) * hh * 0.5, xx = k.x + vx * ft, yy = bt - hh * 0.14 - hh * 1.4 * ft + 0.5 * hh * 9 * ft * ft; c.fillRect(xx, yy, 2, 2); } }
      return;
    }
    var fl = 1 + 0.2 * Math.sin(S.t / 80 + k.i * 3);
    c.fillStyle = '#4d8fd1'; for (var f = -2; f <= 2; f++) { c.beginPath(); c.moveTo(k.x + f * hh * 0.05 - 2, k.y + hh * 0.04); c.lineTo(k.x + f * hh * 0.05, k.y + hh * 0.04 - hh * 0.06 * fl * (1 - Math.abs(f) * 0.2)); c.lineTo(k.x + f * hh * 0.05 + 2, k.y + hh * 0.04); c.fill(); }
    K.lanternGlow(c, k.x, k.y + hh * 0.02, hh * 0.04, 25, 0.6);
    paper(c, function (q) { q.beginPath(); q.arc(k.x, k.y - hh * 0.08, hh * 0.16, Math.PI * 0.15, Math.PI * 0.85); q.closePath(); }, '#2a2a30', 0.8);
    c.strokeStyle = '#7a7a82'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(k.hand[0], k.hand[1]); c.lineTo(k.x + hh * 0.02, k.y - hh * 0.03); c.stroke();
    /* the toss, y = v₀t − ½gt² */
    var u = (S.t / 1000 / 1.8 + k.i * 0.4) % 1, tt2 = u * 0.7; if (u < 0.55) { var cols = ['#7fbf4a', '#d9342b', '#f2c94c', '#f08a5d'];
      for (var p = 0; p < 4; p++) { var vy = hh * (1.5 + p * 0.15), vx2 = (p - 1.5) * hh * 0.1, yy2 = k.y - hh * 0.06 - vy * tt2 + 0.5 * hh * 9 * tt2 * tt2; if (yy2 > k.y - hh * 0.04) continue; c.fillStyle = cols[p]; c.beginPath(); c.arc(k.x + vx2 * tt2, yy2, Math.max(1.5, hh * 0.022), 0, TAU); c.fill(); } }
    steam(c, k.x, k.y - hh * 0.12, hh, S.t, k.i, 3, hh * 0.6, 0.4);
  });
  /* bowls of what goes in */
  var cols2 = ['#d9342b', '#7fbf4a', '#f7f2e0', '#f2a33a', '#9b6bd6'];
  for (i = 0; i < Math.min(6, Math.floor((bx1 - bx0) / (hh * 0.22))); i++) { var bxx = bx0 + hh * 0.12 + i * hh * 0.22; if (woks.some(function (k) { return Math.abs(k.x - bxx) < hh * 0.2; })) continue;
    c.fillStyle = '#f4f1e8'; c.beginPath(); c.arc(bxx, bt, hh * 0.06, 0, Math.PI, true); c.fill(); c.fillStyle = cols2[(i + S.seed) % 5]; c.beginPath(); c.ellipse(bxx, bt - hh * 0.05, hh * 0.05, hh * 0.02, 0, 0, TAU); c.fill(); }
  K.banner(c, (sx0 + sx1) / 2, top + hh * 0.6, S.label, hh, '#b0502f', S.seed, S.hits);
  if (Pl) { var sgn = Cv ? Cv.signAt(c, S, (sx0 + sx1) / 2, top + hh * 0.05, Pl, hh * 0.78, '#5a2e18', null) : K.sign(c, (sx0 + sx1) / 2, top + hh * 0.05, Pl, hh * 0.78, '#5a2e18', null); if (Cv) { var inc = Cv.spiritHouse(c, S, Math.max(X0 + hh * 0.6, sx0 - hh * 0.5), hh * 0.85, (S.seed >>> 2) % 3); Cv.smoke(c, inc[0], inc[1], hh * 0.4, S.t, 1); } S.hits.push({ k: 'place', x0: sx0, x1: sx1, y0: top, y1: S.deck }); }
  bodyBox(S, top);
}

/* ---------------------------------------------------------------- words, math, order
   Titles and venues in English and Thai; checked against the calendar and the festivals */
/* cooking classes sit first in line, ahead of the table scenes, which take a cuisine's own words */
D.addScene('cooking', cooking, /\b(cook(ing)?|cookery) (class|school|course|lesson|workshop|demo)|cookery|เรียนทำอาหาร|สอนทำอาหาร|คลาสทำอาหาร/i, 'y = A·|sin ωt| (the pestle)<br>y = v₀t − ½gt² (the toss)', 0);
D.addScene('hotspring', hotspring, /hot ?springs?|น้ำพุร้อน|บ่อน้ำร้อน|บ่อน้ำแร่|\bonsen\b|ออนเซ็น|geyser/i, 'y = v₀t − ½gt² (the geyser)', 1);
D.addScene('elephants', elephants, /elephant|mahout|ปางช้าง|วันช้าง|ช้างไทย|ศูนย์อนุรักษ์ช้าง|อาบน้ำช้าง|เลี้ยงช้าง|ดูแลช้าง|ควาญช้าง/i, 'θₖ = a·sin(ωt − kφ) (the trunk)<br>y = v₀t − ½gt² (the spray)', 1);
D.addScene('massage', massage, /massage|นวด|tok ?sen|ตอกเส้น|prakhop|ประคบ|reflexolog|yam ?khang|ย่ำขาง/i, 'y = A·e<sup>−λt</sup>·sin(kx − ωt)', 1);
D.addScene('takbat', takbat, /tak ?bat|ตักบาตร|\balms\b|บิณฑบาต|wian ?th?ian|เวียนเทียน|candle procession|makha ?bucha|มาฆบูชา|visakha|วิสาขบูชา|asalha|asanha|อาสาฬหบูชา|khao ?phansa|เข้าพรรษา|ok ?phansa|ออกพรรษา|เทโว|salak|สลากภัต|ก๋วยสลาก/i, 'x = x₀ − vt (the alms round)<br>x = a·cos ωt, y = b·sin ωt (wian thian)', 1);
D.addScene('muaythai', muaythai, /muay ?thai|muaythai|มวยไทย|ค่ายมวย|เวทีมวย|ชกมวย|kick ?boxing|\bboxing\b(?! day)|ram muay|รำมวย|wai kh?ru muay|ไหว้ครูมวย|nai khanom tom|นายขนมต้ม/i, 'θ = θ₀·sin²(πt/T) (the kick)', 1);
D.addScene('sakyant', sakyant, /sak ?yant|sakyant|sak ?mai|bamboo tattoo|hand.?poke|สักยันต์|สักไม้|สักขาลาย|ยันต์|\byant\b/i, 'd = A·|sin ωt| (the tap)<br>x = aθ − b·sin θ (the rows) · r = aθ (the unalome)', 1);
})();
