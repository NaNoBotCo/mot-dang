/* 'all-factored' for the auto-doodler, taken from the minisite All Factored
   (https://nanobotco.github.io/all-factored/, "Flashlight, floodlight": 221 guests in a dark
   room, every 17th in a gold hat; a flashlight sees one at a time, the floodlight shows the
   stripes). Here the room is a Lanna khantok hall under its two-tier roof:
     a letter drops into the lacquer chest's slot (anyone can post one)
     the waiter in mo hom walks the front rows with a torch, one guest at a time
     the owner pulls the cord: the star lantern and the eave khoms light, the whole hall at once
     the 13 gold crowns count off, every 17th guest, a gold line through them
     her naga key turns, the chest opens: 221 = 13 × 17, fireflies, a khom loi, the letter
   One loop is 20 s. Still parts are cut once into an offscreen layer. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, TAU = K.TAU;
var N = 221, STEP = 17, LOOP = 20000, FONT = '"Sarabun",system-ui,sans-serif';
var SHIRT = ['#c0392b', '#2c3e6b', '#1f6a5a', '#8a3a6a', '#d98a2a', '#4a5a8a'];
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function seg(p, a, b) { return clamp((p - a) / (b - a), 0, 1); }
function hx(s) { return [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)]; }
function mixc(a, b, u) { var A = hx(a), B = hx(b); return 'rgb(' + Math.round(lerp(A[0], B[0], u)) + ',' + Math.round(lerp(A[1], B[1], u)) + ',' + Math.round(lerp(A[2], B[2], u)) + ')'; }

/* the still parts cut once into an offscreen canvas, keyed on the stage */
var LAYERS = {};
function layer(S, name, y0, y1, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : null;
  if (!m || typeof document === 'undefined') { draw(c); return; }
  var bx = Math.floor(m.a * S.x0 + m.e), by = Math.floor(m.d * y0 + m.f), bw = Math.ceil(m.a * S.span) + 2, bh = Math.ceil(m.d * (y1 - y0)) + 2;
  var key = [S.W, S.H, S.x0, S.x1, S.deck, S.hh, +S.night, S.seed, m.a, m.d, m.e, m.f, y0, y1].join(','), L = LAYERS[name];
  if (!L || L.key !== key) {
    var o = document.createElement('canvas'); o.width = Math.max(1, bw); o.height = Math.max(1, bh);
    var q = o.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - bx, m.f - by); draw(q);
    L = LAYERS[name] = { key: key, cv: o, x: bx, y: by };
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(L.cv, L.x, L.y); c.restore();
}
/* a soft round glow of a hue, from a small radial disc cut once */
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',95%,66%,1)'); g.addColorStop(0.5, 'hsla(' + h + ',95%,60%,.4)'); g.addColorStop(1, 'hsla(' + h + ',95%,60%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o || a <= 0) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
/* an arm that reaches a point: two segments by the law of cosines */
function solve(s, T, l1, l2, dir) {
  var vx = dir * (T[0] - s[0]), vy = T[1] - s[1], d = Math.min(Math.sqrt(vx * vx + vy * vy), l1 + l2 - 0.01), at = Math.atan2(vx, vy);
  var al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * Math.max(d, 0.01)), -1, 1)), up = at - al;
  return [up, Math.atan2(vx - Math.sin(up) * l1, vy - Math.cos(up) * l1) - up];
}
function reach(x, y, h, P, dir, hA, hB) {
  var seat = P.seat || 0.47, lean = P.lean || 0, hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33], arms = P.arms.slice(), a;
  if (hA) { a = solve(sh, hA, h * 0.17, h * 0.16, dir); arms[0] = a[0]; arms[1] = a[1]; }
  if (hB) { a = solve(sh, hB, h * 0.17, h * 0.16, dir); arms[2] = a[0]; arms[3] = a[1]; }
  return { lean: lean, seat: seat, lift: P.lift || 0, legs: P.legs, arms: arms };
}
function star4(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.moveTo(x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.fill(); }

/* the guests' places: a grid of cols that is neither 13 nor 17 wide, so the 17s fall in slanted stripes */
function seats(gx0, gx1, gy0, gy1) {
  var w = gx1 - gx0, h = gy1 - gy0, cols = Math.max(14, Math.round(Math.sqrt(N * w / h)));
  while (cols % 13 === 0 || cols % 17 === 0) cols++;
  var rows = Math.ceil(N / cols), cell = Math.min(w / cols, h / rows), x0 = gx0 + (w - cell * cols) / 2, y0 = gy0 + (h - cell * rows) / 2, out = [];
  for (var i = 0; i < N; i++) { var r = Math.floor(i / cols), k = i % cols; out.push([x0 + (k + 0.5) * cell, y0 + (r + 0.5) * cell * (0.94 + 0.06 * r / rows), r]); }
  return { at: out, cols: cols, rows: rows, cell: cell };
}
/* busts (head + shoulders) of a list of guests in one path per shirt colour, then heads, then hair */
function busts(c, G, list, a, seed, dark) {
  if (a <= 0.01 || !list.length) return;
  var z = G.cell, i, j, p;
  c.save(); c.globalAlpha = Math.min(1, a);
  for (j = 0; j < (dark ? 1 : SHIRT.length); j++) {
    c.fillStyle = dark ? dark : SHIRT[j]; c.beginPath();
    for (i = 0; i < list.length; i++) { if (!dark && (list[i] * 7 + seed) % SHIRT.length !== j) continue; p = G.at[list[i]]; c.moveTo(p[0] + z * 0.36, p[1] + z * 0.32); c.ellipse(p[0], p[1] + z * 0.32, z * 0.36, z * 0.26, 0, 0, Math.PI, true); }
    c.fill();
  }
  c.fillStyle = dark ? dark : '#d9a27a'; c.beginPath();
  for (i = 0; i < list.length; i++) { p = G.at[list[i]]; c.moveTo(p[0] + z * 0.2, p[1] - z * 0.06); c.arc(p[0], p[1] - z * 0.06, z * 0.2, 0, TAU); }
  c.fill();
  if (!dark) { c.fillStyle = '#1c1410'; c.beginPath(); for (i = 0; i < list.length; i++) { p = G.at[list[i]]; c.moveTo(p[0] + z * 0.21, p[1] - z * 0.08); c.arc(p[0], p[1] - z * 0.08, z * 0.21, 0, Math.PI, true); } c.fill(); }
  c.restore();
}
/* a gold Lanna crown (a little chada spire) on a guest's head; 'on' 0–1 lights it */
function crown(c, p, z, on, t) {
  var x = p[0], y = p[1] - z * 0.22, h = z * (0.55 + 0.15 * on);
  if (on > 0) glow(c, x, y - h * 0.4, z * (1 + 1.4 * on), 45, 0.75 * on);
  c.fillStyle = on > 0 ? mixc('#8a6a2a', '#ffd34d', on) : '#8a6a2a';
  c.beginPath(); c.moveTo(x - z * 0.24, y); c.lineTo(x + z * 0.24, y); c.lineTo(x + z * 0.12, y - h * 0.45); c.lineTo(x, y - h); c.lineTo(x - z * 0.12, y - h * 0.45); c.closePath(); c.fill();
  if (on > 0.5) star4(c, x + z * 0.05, y - h - z * 0.1, z * 0.3 * (0.6 + 0.4 * Math.sin(t / 160 + x)), '#fff4c8');
}
/* a hanging khom (Lanna lantern), dark until 'on' */
function khom(c, x, y, s, on, t, k) {
  if (on > 0) glow(c, x, y + s * 0.45, s * 2.6, 35, on * (0.7 + 0.1 * Math.sin(t / 300 + k)));
  c.strokeStyle = 'rgba(40,20,10,.85)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x, y - s * 0.4); c.lineTo(x, y); c.stroke();
  c.fillStyle = on > 0 ? mixc('#5a2a1e', '#ffb347', on) : '#5a2a1e';
  c.beginPath(); c.moveTo(x - s * 0.2, y); c.lineTo(x + s * 0.2, y); c.lineTo(x + s * 0.42, y + s * 0.45); c.lineTo(x + s * 0.2, y + s * 0.9); c.lineTo(x - s * 0.2, y + s * 0.9); c.lineTo(x - s * 0.42, y + s * 0.45); c.closePath(); c.fill();
  c.fillStyle = '#c9a23a'; c.fillRect(x - s * 0.42, y + s * 0.43, s * 0.84, 1.5);
  c.strokeStyle = '#c9a23a'; c.beginPath(); c.moveTo(x - s * 0.1, y + s * 0.9); c.lineTo(x - s * 0.12, y + s * 1.25); c.moveTo(x + s * 0.1, y + s * 0.9); c.lineTo(x + s * 0.12, y + s * 1.25); c.stroke();
}
/* the star lantern (khom dao): eight points, r alternating R and R·0.5, turning slowly once lit */
function starLamp(c, x, y, R, on, t) {
  if (on > 0) {
    glow(c, x, y, R * 9 * on, 40, 0.55 * on);
    c.save(); c.globalAlpha = 0.16 * on; c.fillStyle = '#ffd98a';   /* rays down into the hall */
    for (var k = 0; k < 7; k++) { var a = Math.PI * (0.18 + k * 0.107) + Math.sin(t / 2400 + k) * 0.03; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a - 0.035) * R * 14, y + Math.sin(a - 0.035) * R * 14); c.lineTo(x + Math.cos(a + 0.035) * R * 14, y + Math.sin(a + 0.035) * R * 14); c.closePath(); c.fill(); }
    c.restore();
  }
  var rot = on * t / 4000;
  c.fillStyle = on > 0 ? mixc('#6a2a1e', '#ffcf5a', on) : '#6a2a1e'; c.beginPath();
  for (var i = 0; i < 16; i++) { var aa = i / 16 * TAU + rot, rr = i % 2 ? R * 0.5 : R; c.lineTo(x + Math.cos(aa) * rr, y + Math.sin(aa) * rr); }
  c.closePath(); c.fill();
  c.strokeStyle = '#e8b84a'; c.lineWidth = 1; c.stroke();
  c.fillStyle = on > 0 ? '#fff6d0' : '#3a1a12'; c.beginPath(); c.arc(x, y, R * 0.28, 0, TAU); c.fill();
  c.strokeStyle = '#d9342b'; c.lineWidth = 1.4;   /* tassels */
  for (i = -1; i <= 1; i++) { c.beginPath(); c.moveTo(x + i * R * 0.35, y + R * 0.7); c.lineTo(x + i * R * 0.42 + Math.sin(t / 700 + i) * 1.5, y + R * 1.5); c.stroke(); }
}
/* the chest (hip) in black lacquer with gold lai kham diamonds, a mail slot in the lid, a brass padlock;
   'open' 0–1 swings the lid back on its hinge */
function chest(c, x0, x1, deck, hh, open, pop, night) {
  var w = x1 - x0, h = hh * 0.5, top = deck - h - hh * 0.08;
  c.fillStyle = '#2a1a12'; c.fillRect(x0 + w * 0.06, deck - hh * 0.1, w * 0.06, hh * 0.1); c.fillRect(x1 - w * 0.12, deck - hh * 0.1, w * 0.06, hh * 0.1);
  paper(c, rect(x0, top, w, h), '#17110f', 1.4);
  c.strokeStyle = '#e2b33c'; c.lineWidth = 1; c.strokeRect(x0 + 3, top + 3, w - 6, h - 6);
  c.fillStyle = '#b3261e'; c.fillRect(x0 + 5, top + h * 0.42, w - 10, h * 0.16);
  c.fillStyle = '#e2b33c';
  for (var k = 0; k < 5; k++) { var dx = x0 + w * (0.14 + k * 0.18), dy = top + h * 0.5, z = h * 0.12; c.beginPath(); c.moveTo(dx, dy - z); c.lineTo(dx + z, dy); c.lineTo(dx, dy + z); c.lineTo(dx - z, dy); c.closePath(); c.fill(); }
  /* the lid, hinged at the back (right) edge */
  c.save(); c.translate(x1, top); c.rotate(open * 1.25);
  paper(c, rect(-w - 2, -h * 0.26, w + 4, h * 0.26), '#1d1512', 1.2);
  c.fillStyle = '#e2b33c'; c.fillRect(-w + 3, -h * 0.26 + 3, w - 6, 1.5);
  c.fillStyle = '#050302'; c.fillRect(-w * 0.62, -h * 0.26 - 1, w * 0.26, 2.5);   /* the slot */
  c.restore();
  /* the padlock on the front: body and shackle; pop lifts the shackle */
  var lx = x0 + w * 0.5, ly = top + h * 0.06, lw = hh * 0.13;
  c.strokeStyle = '#c99a3a'; c.lineWidth = Math.max(1.6, hh * 0.025); c.beginPath(); c.arc(lx + pop * lw * 0.22, ly - pop * lw * 0.55, lw * 0.32, Math.PI, TAU); c.stroke();
  c.fillStyle = '#d9a83a'; c.fillRect(lx - lw * 0.5, ly, lw, lw * 0.85);
  c.fillStyle = '#2a1a0a'; c.beginPath(); c.arc(lx, ly + lw * 0.35, lw * 0.11, 0, TAU); c.fill(); c.fillRect(lx - lw * 0.04, ly + lw * 0.35, lw * 0.08, lw * 0.25);
  return { top: top, lock: [lx, ly + lw * 0.4], slot: [x1 - w * 0.49, top - h * 0.26] };
}
/* a naga-bowed key: gold shaft, the bow a curling naga head, turned by u (0 → 1 is a quarter turn) */
function nagaKey(c, x, y, s, u) {
  c.save(); c.translate(x, y); c.scale(Math.cos(u * Math.PI / 2) * 0.8 + 0.2, 1);
  c.strokeStyle = '#ffd34d'; c.fillStyle = '#ffd34d'; c.lineWidth = Math.max(1.4, s * 0.12); c.lineCap = 'round';
  c.beginPath(); c.moveTo(0, 0); c.lineTo(-s, 0); c.stroke();
  c.beginPath(); c.moveTo(-s, 0); c.bezierCurveTo(-s * 1.5, -s * 0.6, -s * 1.9, s * 0.1, -s * 1.45, s * 0.35); c.stroke();
  c.beginPath(); c.moveTo(-s * 1.45, s * 0.35); c.lineTo(-s * 1.2, s * 0.15); c.lineTo(-s * 1.25, s * 0.5); c.closePath(); c.fill();   /* the naga's jaw */
  c.fillRect(-s * 0.3, 0, s * 0.12, s * 0.3); c.fillRect(-s * 0.55, 0, s * 0.12, s * 0.22);
  c.restore();
}
/* a letter in flight: an envelope with its flap line */
function letter(c, x, y, s, rot) {
  c.save(); c.translate(x, y); c.rotate(rot);
  c.fillStyle = '#f6efdc'; c.fillRect(-s * 0.7, -s * 0.45, s * 1.4, s * 0.9);
  c.strokeStyle = '#a8432f'; c.lineWidth = 1; c.beginPath(); c.moveTo(-s * 0.7, -s * 0.45); c.lineTo(0, s * 0.1); c.lineTo(s * 0.7, -s * 0.45); c.stroke();
  c.fillStyle = '#d9342b'; c.beginPath(); c.arc(0, s * 0.08, s * 0.12, 0, TAU); c.fill();
  c.restore();
}

/* ---------------------------------------------------------------- the scene */
function room(S) {
  var c = S.c, hh = S.hh, t = S.t, u = (t % LOOP) / LOOP, i, k;
  var hx0 = S.x0 + hh * 0.8, hx1 = S.x1 - hh * (S.phone ? 2.1 : 2.4), w = hx1 - hx0, top = S.deck - hh * 2.05, e1 = top + (S.deck - top) * 0.32;
  var flood = ease(seg(u, 0.42, 0.5)) * (1 - ease(seg(u, 0.93, 1))), trace = seg(u, 0.53, 0.77), turn = seg(u, 0.77, 0.81), open = ease(seg(u, 0.81, 0.87)) * (1 - ease(seg(u, 0.95, 1)));
  var G = seats(hx0 + w * 0.11, hx1 - w * 0.11, e1 + hh * 0.3, S.deck - hh * 0.06), z = G.cell;
  /* the hall's back wall, dark teak, warming as the light comes */
  c.fillStyle = mixc('#120b09', '#6a4a2c', flood * 0.85); c.fillRect(hx0 + w * 0.03, e1 - 2, w * 0.94, S.deck - e1 + 2);
  layer(S, 'af-hall', top - hh * 0.5, S.H, function (q) {
    K.ground(q, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1d18' : '#7a5a3a');
    K.sala(q, hx0, hx1, S.deck, top, S.night, S.night ? '#5a241c' : '#8a3a28');
  });
  /* the low khantok tables, one per row, black to lacquer red */
  c.fillStyle = mixc('#1e1410', '#a8302a', flood);
  for (var r = 0; r < G.rows; r++) { var ry = G.at[Math.min(N - 1, r * G.cols)][1] + z * 0.42; c.fillRect(G.at[r * G.cols][0] - z * 0.5, ry, G.cols * z, Math.max(1.5, z * 0.1)); }
  /* everyone, first as dark shapes, then in colour as the hall lights */
  var all = []; for (i = 0; i < N; i++) all.push(i);
  if (flood < 1) busts(c, G, all, 1, S.seed, '#2c211c');
  busts(c, G, all, flood, S.seed);
  /* the torch's spot: the front row left to right, the next right to left */
  var sweep = seg(u, 0.03, 0.42), row1 = G.rows - 1, row2 = G.rows - 2, gL = G.at[row2 * G.cols][0], gR = G.at[row2 * G.cols + G.cols - 1][0];
  var sx = sweep < 0.5 ? lerp(gL, gR, ease(sweep * 2)) : lerp(gR, gL, ease(sweep * 2 - 1)), sy = G.at[Math.min(N - 1, (sweep < 0.5 ? row1 : row2) * G.cols)][1] - z * 0.05;
  var torch = (1 - flood) * seg(u, 0.03, 0.06) * (1 - seg(u, 0.42, 0.46)), R = z * 1.9, lit = [];
  if (torch > 0) for (i = 0; i < N; i++) { var p = G.at[i], dd = Math.hypot(p[0] - sx, p[1] - sy); if (dd < R) lit.push(i); }
  if (lit.length) {
    busts(c, G, lit, torch, S.seed);
    lit.forEach(function (j) { if (j % STEP === 0) crown(c, G.at[j], z, torch * (1 - Math.hypot(G.at[j][0] - sx, G.at[j][1] - sy) / R), t); });
  }
  /* the crowns: dark until the flood, then counted off 1 … 13, the gold line run through them */
  var hats = []; for (k = 0; k * STEP < N; k++) hats.push(k * STEP);
  if (flood > 0) {
    var shown = trace * hats.length;
    c.save(); c.strokeStyle = '#ffd34d'; c.lineWidth = Math.max(1.5, z * 0.14); c.setLineDash([z * 0.4, z * 0.3]); c.lineDashOffset = -t / 60; c.globalAlpha = 0.85 * flood; c.beginPath();
    for (k = 1; k < hats.length && k < shown; k++) { var a0 = G.at[hats[k - 1]], a1 = G.at[hats[k]], f = Math.min(1, shown - k); c.moveTo(a0[0], a0[1] - z * 0.5); c.lineTo(lerp(a0[0], a1[0], f), lerp(a0[1], a1[1], f) - z * 0.5); }
    c.stroke(); c.restore();
    c.save(); c.font = '800 ' + Math.round(Math.max(8, z * 0.7)) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'bottom';
    hats.forEach(function (j, kk) {
      var on = clamp(shown - kk, 0, 1) * flood; crown(c, G.at[j], z, on, t);
      if (on > 0 && !S.phone) { c.globalAlpha = on; c.fillStyle = '#fff4c8'; c.fillText(String(kk + 1), G.at[j][0] + z * 0.55, G.at[j][1] - z * 0.55); c.globalAlpha = 1; }
    });
    c.restore();
  } else hats.forEach(function (j) { if (lit.indexOf(j) < 0) crown(c, G.at[j], z, 0, t); });
  /* the lanterns: the star lantern at the ridge, four khoms along the eave lighting outward from it */
  var mx = (hx0 + hx1) / 2;
  starLamp(c, mx, e1 + hh * 0.13, hh * 0.12, flood, t);
  for (k = 0; k < 4; k++) { var side = k % 2 ? 1 : -1, far = Math.floor(k / 2), kx = mx + side * w * (0.2 + far * 0.18); khom(c, kx, e1 + 2, hh * 0.14, flood * seg(u, 0.44 + far * 0.03, 0.47 + far * 0.03), t, k); }
  /* the waiter in mo hom with his torch: he follows the spot, waits in the light, walks back */
  var crew = K.town(S, 2, { mohom: 1 }), wt = crew[0], oy = S.deck + hh * 0.14, xs = clamp(gL, hx0 + hh * 0.3, hx1), xe = clamp(sx, hx0 + hh * 0.3, hx1 - hh * 0.2);
  var back = seg(u, 0.88, 1), wx = u >= 0.88 ? lerp(G.at[row2 * G.cols][0], xs, ease(back)) : u < 0.42 ? xe : G.at[row2 * G.cols][0];
  var moving = u < 0.42 && u > 0.03 || u >= 0.88, dir = u >= 0.88 ? -1 : sweep < 0.5 || u >= 0.42 ? 1 : -1;
  if (u >= 0.42 && u < 0.88) dir = 1;
  wt.dir = dir;
  var WP = moving ? K.walkP(t / 1000 * TAU * 0.9, false) : K.POSE.stand;
  if (torch > 0.05) {
    var hand = [wx + dir * hh * 0.24, S.deck - hh * 0.62];
    var me = K.person(c, wx, oy, hh * 0.95, reach(wx, oy, hh * 0.95, WP, dir, hand, null), wt);
    var hp = me.hand[0], bg = c.createRadialGradient(sx, sy, 0, sx, sy, R);
    c.save(); c.globalAlpha = torch;
    bg.addColorStop(0, 'rgba(255,236,170,.32)'); bg.addColorStop(1, 'rgba(255,236,170,0)'); c.fillStyle = bg; c.beginPath(); c.arc(sx, sy, R, 0, TAU); c.fill();
    c.fillStyle = 'rgba(255,236,170,.13)'; c.beginPath(); c.moveTo(hp[0], hp[1]); c.lineTo(sx - R * 0.8, sy - R * 0.4); c.lineTo(sx + R * 0.8, sy + R * 0.3); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(255,230,160,.6)'; c.lineWidth = 1.5; c.beginPath(); c.arc(sx, sy, R, 0, TAU); c.stroke();
    c.restore();
    c.fillStyle = '#3a3a40'; c.save(); c.translate(hp[0], hp[1]); c.rotate(Math.atan2(sy - hp[1], sx - hp[0])); c.fillRect(-hh * 0.02, -hh * 0.025, hh * 0.1, hh * 0.05); c.fillStyle = '#fff2b0'; c.fillRect(hh * 0.08, -hh * 0.03, hh * 0.02, hh * 0.06); c.restore();
  } else {
    var wai = u > 0.5 && u < 0.86, WW = wai ? { lean: 0.05, legs: WP.legs, arms: [0.9, 1.75, 0.8, 1.85] } : WP;
    K.person(c, wx, oy, hh * 0.95, WW, wt);
  }
  /* the owner in pha sin: she pulls the lantern cord, then turns her naga key in the padlock */
  var cx0 = hx1 + hh * (S.phone ? 0.55 : 0.75), cx1 = S.x1 - hh * 0.85, ox = hx1 + hh * 0.3, own = crew[1];
  own.garb = 'sin'; own.dir = 1; own.hair = 2; own.col = '#f2e6c9';
  var cordX = hx1 - w * 0.02, pull = u > 0.35 && u < 0.45 ? Math.abs(Math.sin(seg(u, 0.35, 0.45) * Math.PI * 2)) : 0;
  c.strokeStyle = '#c9a26a'; c.lineWidth = 1; c.beginPath(); c.moveTo(cordX, e1); c.lineTo(cordX, S.deck - hh * (0.95 - pull * 0.12)); c.stroke();
  var Ch = chest(c, cx0, cx1, S.deck, hh, open, ease(seg(u, 0.79, 0.82)) * (1 - seg(u, 0.95, 1)), S.night);
  var keyAt = u > 0.7 && u < 0.92, hA = u > 0.33 && u < 0.47 ? [cordX, S.deck - hh * (0.95 - pull * 0.12)] : null, hB = keyAt ? [Ch.lock[0] - hh * 0.2, Ch.lock[1]] : null;
  own.dir = hA ? -1 : 1;
  K.person(c, ox, S.deck + hh * 0.06, hh, reach(ox, S.deck + hh * 0.06, hh, K.POSE.stand, own.dir, own.dir > 0 ? hB : hA, null), own);
  if (keyAt) nagaKey(c, Ch.lock[0], Ch.lock[1], hh * 0.12, turn);
  /* the letter: posted at the start into the slot, flown out again when the lid opens */
  var fly = seg(u, 0.02, 0.14);
  if (fly > 0 && fly < 1) { var lx = lerp(S.x0 + hh * 0.6, Ch.slot[0], fly), ly = lerp(top - hh * 0.2, Ch.slot[1], fly) - Math.sin(fly * Math.PI) * hh * 0.5; letter(c, lx, ly, hh * 0.1 * (1 - fly * 0.4), fly * 3); }
  var out = seg(u, 0.85, 0.99);
  if (out > 0) {
    var bx = (cx0 + cx1) / 2, by = Ch.top;
    /* fireflies out of the chest, each on its own curl */
    for (k = 0; k < (S.phone ? 9 : 16); k++) {
      var ph = k * 2.39, rise = clamp(out * 1.4 - k * 0.025, 0, 1), fx = bx + Math.sin(ph + rise * 5) * hh * (0.15 + rise * 0.6), fy = by - rise * hh * (1.1 + (k % 4) * 0.25), fa = Math.sin(rise * Math.PI);
      if (fa > 0.02) { glow(c, fx, fy, hh * 0.09, 50, fa); c.fillStyle = 'rgba(255,248,200,' + fa + ')'; c.fillRect(fx - 1, fy - 1, 2, 2); }
    }
    letter(c, bx + Math.sin(out * 4) * hh * 0.15, by - ease(out) * hh * 1.2, hh * 0.1, Math.sin(out * 6) * 0.3);
    /* a small khom loi lifted out after it */
    var kl = seg(u, 0.88, 1), ky = by - ease(kl) * hh * 1.7, ks = hh * 0.12;
    if (kl > 0) { glow(c, bx - hh * 0.2, ky, ks * 3, 30, Math.sin(kl * Math.PI)); c.fillStyle = '#ffd08a'; c.beginPath(); c.moveTo(bx - hh * 0.2 - ks * 0.5, ky + ks * 0.7); c.lineTo(bx - hh * 0.2 - ks * 0.65, ky - ks * 0.4); c.quadraticCurveTo(bx - hh * 0.2, ky - ks * 1.1, bx - hh * 0.2 + ks * 0.65, ky - ks * 0.4); c.lineTo(bx - hh * 0.2 + ks * 0.5, ky + ks * 0.7); c.closePath(); c.fill(); }
    /* the sum, in gold over the open chest */
    var sa = seg(u, 0.84, 0.88) * (1 - seg(u, 0.95, 1));
    if (sa > 0) {
      c.save(); c.globalAlpha = sa; c.font = '800 ' + Math.round(Math.max(11, hh * 0.19)) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle';
      var tw = c.measureText('221 = 13 × 17').width / 2 + 6, tx = clamp(bx, S.x0 + tw, S.x1 - tw), ty = by - hh * 0.75;
      glow(c, tx, ty, hh * 0.8, 45, 0.5); c.lineWidth = 3; c.strokeStyle = 'rgba(40,20,10,.8)'; c.strokeText('221 = 13 × 17', tx, ty); c.fillStyle = '#ffe07a'; c.fillText('221 = 13 × 17', tx, ty);
      c.restore();
    }
  }
  /* the banner hangs from the roof's upper tier */
  if (S.label) {
    c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px ' + FONT;
    var half = c.measureText(S.label).width / 2 + 10 + Math.max(20, hh * 0.32) * 0.6 + 4, lo = S.x0 + hh * 0.75 + half, hi = S.x1 - hh * 0.95 - half;
    K.banner(c, lo > hi ? S.x0 + S.span / 2 : clamp(mx, lo, hi), top + hh * 0.02, S.label, hh, '#7a2a6a', S.seed, S.hits);
  }
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

D.addScene('all-factored', room, /cryptograph|encryption|\bcrypto\b|post-?quantum|quantum comput|cyber ?security|infosec|password|prime numbers?|เข้ารหัส|ควอนตัม|ความปลอดภัยไซเบอร์|รหัสผ่าน/i, '221 = 13 × 17', 1);
})();
