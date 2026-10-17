/* 'ghosts-drawn' for the auto-doodler, taken from the minisite Ghosts, Drawn · ผีเหนือ ผีไทย
   (https://nanobotco.github.io/ghosts-drawn/ , https://motdang.net/sites/ghosts-drawn/), whose
   21 phi are cartoons in a 240 box (tools/art.js). Their own paths are used here, so each keeps its
   look: Mae Nak with her long arm, Nang Tani at the banana tree, tall thin Phi pret with his gold
   belly, Phi pop with her woven creel, the Phi tai hong sheet. Chiang Mai at Halloween, 22 s loop:
   the lights come on along a string of khom (a wisp leads them), the ghosts step out one by one
   and join the street (Mae Nak reaches for a lime, Tani peeks from the banana, a child pours water
   for Pret, children toss sweets to Pop, the sheet says boo to the pumpkin carver), then the carved
   pumpkin flares, every ghost waves and khom loi lift off; all vanish in gold and it starts again.
   By day the ghosts are paler, the bats hang asleep and the pumpkins glow less. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, TAU = K.TAU, ease = K.ease, lerp = K.lerp, LOOP = 22000;
var INK = '#22162e', SKIN = '#f2c9a2', HAIR = '#1a1124', GOLD = '#f0b63c', PUMP = '#f08a1c';

function win(u, a, b) { return ease((u - a) / (b - a)); }                      /* 0 → 1 across [a, b], eased */
function bk(a) { a = Math.max(0, Math.min(1, a)); var q = a - 1; return Math.max(0, 1 + 2.7 * q * q * q + 1.7 * q * q); }   /* ease-out-back, overshoots */
function P(d) { return new Path2D(d); }
function hairLong(cx, top, w, bottom) { return P('M' + (cx - w) + ' ' + (top + 14) + ' C' + (cx - w - 8) + ' ' + (bottom - 30) + ' ' + (cx - w + 2) + ' ' + bottom + ' ' + (cx - w + 12) + ' ' + bottom + ' L' + (cx + w - 12) + ' ' + bottom + ' C' + (cx + w - 2) + ' ' + bottom + ' ' + (cx + w + 8) + ' ' + (bottom - 30) + ' ' + (cx + w) + ' ' + (top + 14) + ' Z'); }
function fringe(cx, cy, w) { return P('M' + (cx - w) + ' ' + (cy + 6) + ' C' + (cx - w + 2) + ' ' + (cy - 26) + ' ' + (cx + w - 2) + ' ' + (cy - 26) + ' ' + (cx + w) + ' ' + (cy + 6) + ' C' + (cx + w - 10) + ' ' + (cy - 6) + ' ' + (cx + 10) + ' ' + (cy + 2) + ' ' + cx + ' ' + (cy - 6) + ' C' + (cx - 12) + ' ' + (cy + 2) + ' ' + (cx - w + 10) + ' ' + (cy - 6) + ' ' + (cx - w) + ' ' + (cy + 6) + 'Z'); }

/* the ghosts' own outlines, copied from the minisite's art.js (box coordinates) */
var G = null;
function paths() { G = {
  nakHair: hairLong(96, 30, 22, 108), nakBody: P('M66 116 q4 -40 30 -46 q26 6 30 46z'), nakSash: P('M78 82 q18 18 40 4'), nakFringe: fringe(96, 42, 21),
  taniHair: hairLong(98, 96, 20, 190), taniDress: P('M70 214 q4 -62 28 -76 q22 10 30 76z'), taniSabai: P('M76 172 q22 -34 46 -30 l-2 22 q-24 0 -44 22z'), taniFringe: fringe(98, 110, 19),
  trunk: P('M138 214 L144 70'), leafA: P('M144 74 C110 40 70 50 40 74 C78 70 112 76 144 80Z'), leafB: P('M144 74 C170 30 214 30 236 50 C206 56 176 66 146 82Z'), leafC: P('M144 72 C140 36 150 14 168 4 C162 30 156 54 148 78Z'),
  stalk: P('M146 84 C170 100 178 120 176 140'), flower: P('M176 138 c-10 4 -12 22 0 30 c12 -8 10 -26 0 -30z'), cloth: P('M124 150 L156 146 L156 166 L124 170Z'),
  pretHair: P('M104 70 C70 88 72 170 88 222 M136 70 C170 88 168 170 152 222'), pretLegs: P('M112 226 L114 170 M128 226 L126 170'), pretNeck: P('M108 126 C110 110 112 98 116 70 H124 C128 98 130 110 132 126'),
  pretCap: P('M98 50 C96 22 144 22 142 50 C134 38 106 38 98 50Z'),
  popBody: P('M56 220 q4 -70 30 -96 h48 q26 26 30 96z'), popBelt: P('M60 196 h100 l4 24 h-108z'), popHair: P('M80 92 C80 58 140 58 140 92 C130 80 120 86 110 76 C100 86 90 80 80 92Z'),
  popArmL: P('M76 140 q-20 10 -16 34'), popArmR: P('M144 140 q22 6 24 26'), teeth: P('M101 112 l3 4 l3 -4 l3 4 l3 -4 l3 4 l3 -4'),
  creel: P('M-22 -40 q22 -14 44 0 q10 40 -4 82 h-36 q-14 -42 -4 -82z'),
  sheet: P('M98 196 C96 140 104 124 120 124 C136 124 144 140 142 196 L134 186 L127 198 L120 186 L113 198 L106 186Z')
}; }

function fillP(c, p, col, w) { c.fillStyle = col; c.fill(p); c.lineWidth = w || 3; c.strokeStyle = INK; c.lineJoin = 'round'; c.lineCap = 'round'; c.stroke(p); }
function limbP(c, p, col, w) { c.lineCap = 'round'; c.strokeStyle = INK; c.lineWidth = w + 3; c.stroke(p); c.strokeStyle = col; c.lineWidth = w; c.stroke(p); }
function disc(c, x, y, r, col, w) { c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); if (w) { c.lineWidth = w; c.strokeStyle = INK; c.stroke(); } }
function oval(c, x, y, rx, ry, col, w, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, rx, ry, rot || 0, 0, TAU); c.fill(); if (w) { c.lineWidth = w; c.strokeStyle = INK; c.stroke(); } }
/* a pair of cartoon eyes: whites, ink pupils shifted by look, lids shut by bl (0 open … 1 shut) */
function eyes(c, x, y, g, r, bl, look, fill) {
  [-1, 1].forEach(function (s) {
    oval(c, x + s * g, y, r * 0.82, Math.max(0.5, r * (1 - 0.9 * bl)), fill || '#fff', 2);
    if (bl < 0.6) disc(c, x + s * g + 1 + look, y + 1, r * 0.42, INK);
  });
}
function blink(t, ph) { var m = (t + ph) % 3600; return m < 140 ? Math.sin(m / 140 * Math.PI) : 0; }
function cheeks(c, x, y, g) { c.fillStyle = 'rgba(255,143,158,.55)'; [-1, 1].forEach(function (s) { c.beginPath(); c.arc(x + s * g, y, 5, 0, TAU); c.fill(); }); }
function spark(c, x, y, z, a) {                                                       /* a four-point gold lai kham spark */
  c.fillStyle = 'rgba(255,214,90,' + a + ')';
  c.beginPath(); c.moveTo(x, y - z * 2); c.quadraticCurveTo(x, y, x + z * 2, y); c.quadraticCurveTo(x, y, x, y + z * 2); c.quadraticCurveTo(x, y, x - z * 2, y); c.quadraticCurveTo(x, y, x, y - z * 2); c.fill();
}
function glow(c, x, y, r, rgb, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, 'rgba(' + rgb + ',' + a + ')'); g.addColorStop(1, 'rgba(' + rgb + ',0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
function poof(c, x, y, r, p) {                                                        /* eight sparks leaving a point, r·p out, fading as 1 − p */
  if (p <= 0 || p >= 1) return;
  for (var k = 0; k < 8; k++) { var a = k / 8 * TAU + 0.3; spark(c, x + Math.cos(a) * r * p, y + Math.sin(a) * r * p * 0.8, r * 0.07 * (1 - p * 0.5), 0.9 * (1 - p)); }
}
function shadow(c, x, y, rx, a) { c.fillStyle = 'rgba(0,0,0,' + (a || 0.28) + ')'; c.beginPath(); c.ellipse(x, y, rx, Math.max(1.5, rx * 0.16), 0, 0, TAU); c.fill(); }

/* a carved pumpkin: ribbed ellipse, the face cut by prog (eyes, then nose, then teeth), a candle glow inside by lit */
function pumpkin(c, x, y, r, face, prog, lit, fl, night, glowK) {
  c.save(); c.translate(x, y);
  oval(c, -r * 0.42, -r * 0.8, r * 0.58, r * 0.78, '#e07414', 1.6); oval(c, r * 0.42, -r * 0.8, r * 0.58, r * 0.78, '#e07414', 1.6);
  oval(c, 0, -r * 0.8, r * 0.62, r * 0.82, PUMP, 1.8);
  c.strokeStyle = 'rgba(120,50,0,.35)'; c.lineWidth = 1; c.beginPath(); c.ellipse(0, -r * 0.8, r * 0.3, r * 0.8, 0, 0, TAU); c.stroke();
  c.fillStyle = '#4a7a2a'; c.fillRect(-r * 0.08, -r * 1.75, r * 0.16, r * 0.3);
  if (prog > 0) {
    var inner = lit ? 'rgba(255,' + Math.round(200 + 30 * fl) + ',80,1)' : '#3a1608', e = Math.min(1, prog * 2), m = Math.max(0, prog * 2 - 1), ey = -r * 0.98, es = r * 0.2 * e;
    c.fillStyle = inner;
    if (e > 0) {
      if (face === 2) { c.beginPath(); c.arc(-r * 0.3, ey, es, 0, TAU); c.arc(r * 0.3, ey, es, 0, TAU); c.fill(); }
      else if (face === 3) { c.lineWidth = 2; c.strokeStyle = inner; c.beginPath(); c.arc(-r * 0.3, ey, es * 0.9, 0.2, Math.PI - 0.2); c.arc(r * 0.3, ey, es * 0.9, 0.2, Math.PI - 0.2); c.stroke(); }
      else { c.beginPath(); c.moveTo(-r * 0.5, ey + es); c.lineTo(-r * 0.3, ey - es * 1.3); c.lineTo(-r * 0.1, ey + es); c.moveTo(r * 0.5, ey + es); c.lineTo(r * 0.3, ey - es * 1.3); c.lineTo(r * 0.1, ey + es); c.closePath(); c.fill(); }
      c.beginPath(); c.moveTo(0, ey + es * 1.2); c.lineTo(-es * 0.6, ey + es * 2.3); c.lineTo(es * 0.6, ey + es * 2.3); c.closePath(); c.fill();
    }
    if (m > 0) {
      var my = -r * 0.55, mw = r * 0.5 * m;
      c.beginPath(); c.moveTo(-mw, my);
      if (face === 1) { for (var k = 0; k <= 6; k++) c.lineTo(-mw + mw * 2 * k / 6, my + (k % 2 ? r * 0.2 : 0) * m); c.lineTo(mw, my + r * 0.1); c.quadraticCurveTo(0, my + r * 0.4 * m, -mw, my + r * 0.1); }
      else if (face === 3) { c.quadraticCurveTo(0, my + r * 0.2 * m, mw, my); c.quadraticCurveTo(0, my + r * 0.08, -mw, my); }
      else { c.quadraticCurveTo(0, my + r * 0.5 * m, mw, my); c.lineTo(mw * 0.7, my + r * 0.05); c.quadraticCurveTo(0, my + r * 0.3 * m, -mw * 0.7, my + r * 0.05); }
      c.closePath(); c.fill();
    }
  }
  c.restore();
  if (lit && prog > 0.3) glow(c, x, y - r * 0.8, r * 2.4, '255,170,60', (0.15 + 0.35 * glowK) * (0.8 + 0.2 * fl));
}

/* a khom lantern: a paper hexagon with a gold cap and tassel, lit by a (0…1) */
function khom(c, x, y, sz, a, fl, tail) {
  if (a <= 0.01) { c.fillStyle = '#7a5a3a'; c.fillRect(x - sz * 0.5, y - sz * 0.8, sz, sz * 1.5); return; }
  glow(c, x, y, sz * 3.2, '255,170,70', 0.5 * a * fl);
  var g = c.createLinearGradient(x, y - sz, x, y + sz); g.addColorStop(0, '#ffe9a8'); g.addColorStop(1, '#ff8a3a');
  c.fillStyle = g; c.beginPath(); c.moveTo(x - sz * 0.5, y + sz * 0.8); c.lineTo(x - sz * 0.7, y - sz * 0.45); c.quadraticCurveTo(x, y - sz * 1.2, x + sz * 0.7, y - sz * 0.45); c.lineTo(x + sz * 0.5, y + sz * 0.8); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(120,40,0,.5)'; c.lineWidth = 0.8; c.beginPath(); c.moveTo(x, y - sz * 1.0); c.lineTo(x, y + sz * 0.8); c.moveTo(x - sz * 0.5, y - sz * 0.3); c.quadraticCurveTo(x, y - sz * 0.05, x + sz * 0.5, y - sz * 0.3); c.stroke();
  if (tail) { c.fillStyle = '#fff6c0'; c.beginPath(); c.arc(x, y + sz * 0.9, sz * 0.18 * fl, 0, TAU); c.fill(); }
}

/* a wrapped sweet: a body and two twisted ends */
function sweet(c, x, y, z, col, rot) {
  c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = col; c.beginPath(); c.ellipse(0, 0, z, z * 0.62, 0, 0, TAU); c.fill();
  c.beginPath(); c.moveTo(z * 0.8, 0); c.lineTo(z * 1.7, -z * 0.6); c.lineTo(z * 1.7, z * 0.6); c.moveTo(-z * 0.8, 0); c.lineTo(-z * 1.7, -z * 0.6); c.lineTo(-z * 1.7, z * 0.6); c.fill();
  c.strokeStyle = 'rgba(255,255,255,.6)'; c.lineWidth = Math.max(0.6, z * 0.18); c.beginPath(); c.moveTo(-z * 0.3, -z * 0.5); c.lineTo(z * 0.3, z * 0.5); c.stroke(); c.restore();
}

/* a witch hat on a head point: cone leaning with lean, gold buckle band */
function witchHat(c, hd, h, lean, col) {
  var r = h * 0.15, x = hd[0], y = hd[1] - h * 0.07;
  c.fillStyle = col; c.beginPath(); c.ellipse(x, y, r * 1.35, r * 0.3, 0, 0, TAU); c.fill();
  c.beginPath(); c.moveTo(x - r * 0.8, y); c.quadraticCurveTo(x - r * 0.2 + lean * r, y - r * 1.8, x + lean * r * 2.4, y - r * 2.6); c.quadraticCurveTo(x + r * 0.5 + lean * r, y - r * 1.5, x + r * 0.8, y); c.closePath(); c.fill();
  c.fillStyle = GOLD; c.fillRect(x - r * 0.62, y - r * 0.5, r * 1.24, r * 0.2);
}
function catEars(c, hd, h, col) { var r = h * 0.1, x = hd[0], y = hd[1] - h * 0.08; c.fillStyle = col; [-1, 1].forEach(function (s) { c.beginPath(); c.moveTo(x + s * r * 0.2, y); c.lineTo(x + s * r * 0.55, y - r * 1.2); c.lineTo(x + s * r * 1.05, y + r * 0.1); c.closePath(); c.fill(); }); }

/* Mae Nak (box 240, floor at y 116): head, pink blouse, gold sash, jasmine garland; hands off, the arm is drawn in the world */
function maeNak(c, x, y, hh, o) {
  var sc = hh / 105; c.save(); c.translate(x, y); c.scale(sc, sc); c.translate(-96, -116);
  fillP(c, G.nakHair, HAIR, 2.5); fillP(c, G.nakBody, '#b2557a', 3);
  c.strokeStyle = '#f2c14e'; c.lineWidth = 4; c.lineCap = 'round'; c.stroke(G.nakSash);
  for (var k = 0; k <= 8; k++) { var s = k / 8, gx = lerp(76, 118, s), gy = 86 + Math.sin(s * Math.PI) * 17; disc(c, gx, gy, 3.6, k % 2 ? '#fff8e0' : '#ffd84a', 1); }
  oval(c, 96, 50, 20, 22, SKIN, 3); fillP(c, G.nakFringe, HAIR, 2.5);
  disc(c, 112, 38, 4.5, '#fff8e0', 1); disc(c, 116, 43, 4, '#ffd84a', 1);
  eyes(c, 96, 52, 8, 4.5, o.bl, o.look); cheeks(c, 96, 60, 13);
  c.strokeStyle = INK; c.lineWidth = 2; c.beginPath(); c.moveTo(90, 64); c.quadraticCurveTo(96, 64 + 4 + 3 * o.smile, 102, 64); c.stroke();
  c.restore();
}
/* the long arm: a chain of points from shoulder to hand, p(s) = (1−s)A + sB + n·a·sin(πs)·sin(ωt), blouse sleeve over the first fifth */
function longArm(c, sx, sy, hx, hy, w, t) {
  var N = 18, d = Math.hypot(hx - sx, hy - sy) || 1, nx = -(hy - sy) / d, ny = (hx - sx) / d, amp = Math.min(d * 0.09, w * 2.4), pts = [], i;
  for (i = 0; i <= N; i++) { var s = i / N, b = Math.sin(s * Math.PI) * (amp * Math.sin(t / 240 + s * 3) + d * 0.05); pts.push([lerp(sx, hx, s) + nx * b, lerp(sy, hy, s) + ny * b]); }
  c.lineCap = 'round'; c.lineJoin = 'round';
  function trace(a, b) { c.beginPath(); for (var j = a; j <= b; j++) j === a ? c.moveTo(pts[j][0], pts[j][1]) : c.lineTo(pts[j][0], pts[j][1]); }
  trace(0, N); c.strokeStyle = INK; c.lineWidth = w + 3; c.stroke(); c.strokeStyle = SKIN; c.lineWidth = w; c.stroke();
  trace(0, 3); c.strokeStyle = '#b2557a'; c.lineWidth = w + 1; c.stroke();
  disc(c, hx, hy, w * 0.95, SKIN, 2);
  c.strokeStyle = INK; c.lineWidth = 1.6; c.beginPath(); c.moveTo(hx + w * 0.5, hy - w * 0.5); c.lineTo(hx + w * 1.15, hy - w * 0.9); c.stroke();
}
function lime(c, x, y, r) { disc(c, x, y, r, '#9ccc3c', 1.6); c.fillStyle = 'rgba(255,255,255,.5)'; c.beginPath(); c.arc(x - r * 0.3, y - r * 0.3, r * 0.28, 0, TAU); c.fill(); }

/* Nang Tani: the banana tree (trunk, three leaves swaying, red cloth with gold stripes, a flower) and she peeking from behind it;
   peek 0 = hidden behind the trunk … 1 = out; box 240, trunk foot at (138, 214) */
function taniTree(c, x, y, hh, o) {
  var sc = hh / 100; c.save(); c.translate(x, y); c.scale(sc, sc); c.translate(-138, -214);
  var off = lerp(34, -12, o.peek), tilt = Math.sin(o.t / 900) * 0.04 + o.wave * Math.sin(o.t / 160) * 0.05;
  c.save(); c.translate(off, 0); c.translate(98, 214); c.rotate(tilt); c.translate(-98, -214);
  fillP(c, G.taniHair, HAIR, 2.5); fillP(c, G.taniDress, '#2f6a34', 3); fillP(c, G.taniSabai, '#c6e59a', 2.5);
  oval(c, 98, 118, 18, 20, SKIN, 3); fillP(c, G.taniFringe, HAIR, 2.5);
  disc(c, 112, 106, 4.5, '#ff7aa8', 1); disc(c, 106, 103, 3.4, '#fff4c0', 1);
  eyes(c, 98, 120, 7, 4.5, o.bl, 2 * o.peek); cheeks(c, 98, 128, 12);
  c.strokeStyle = '#b5304a'; c.lineWidth = 2.5; c.lineCap = 'round'; c.beginPath(); c.moveTo(92, 132); c.quadraticCurveTo(98, 132 + 4 + 2 * o.peek, 104, 132); c.stroke();
  if (o.wave > 0) { c.save(); c.translate(126, 172); c.rotate(-0.5 + Math.sin(o.t / 170) * 0.4); limbP(c, P('M0 0 q6 -16 2 -34'), '#c6e59a', 6); disc(c, 2, -36, 6, SKIN, 2); c.restore(); }
  c.restore();
  c.lineCap = 'round'; c.strokeStyle = INK; c.lineWidth = 30; c.stroke(G.trunk); c.strokeStyle = '#a9c97a'; c.lineWidth = 24; c.stroke(G.trunk);
  c.strokeStyle = '#86a95a'; c.lineWidth = 2; c.beginPath(); c.moveTo(132, 190); c.lineTo(140, 80); c.moveTo(146, 196); c.lineTo(150, 80); c.stroke();
  c.save(); c.translate(144, 76); c.rotate(Math.sin(o.t / 1500) * 0.035); c.translate(-144, -76);
  fillP(c, G.leafA, '#5f9a46', 3); fillP(c, G.leafB, '#6aaa4c', 3); fillP(c, G.leafC, '#78b956', 3);
  c.strokeStyle = INK; c.lineWidth = 3; c.stroke(G.stalk); fillP(c, G.flower, '#8f2f55', 2.5);
  for (var b = 0; b < 4; b++) { c.save(); c.translate(172 + b * 3, 150 + b * 8); c.rotate(-0.35); oval(c, 0, 0, 11, 3.6, b % 2 ? '#e8d84a' : '#c9e04a', 1.4); c.restore(); }
  c.restore();
  c.save(); c.translate(140, 150); c.rotate(Math.sin(o.t / 700) * 0.03); c.translate(-140, -150); fillP(c, G.cloth, '#d23b3b', 2.5);
  c.strokeStyle = '#f0c04a'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(128, 150); c.lineTo(130, 168); c.moveTo(140, 148); c.lineTo(142, 168); c.moveTo(150, 147); c.lineTo(152, 166); c.stroke(); c.restore();
  c.restore();
}

/* Phi pret (box 240, feet at y 226): neck long, belly gold by gold (0…1); hands big as palm leaves, cubic arms from the shoulder easing from hanging to raised by ha (0…1) */
function pret(c, x, y, sx, sy, o) {
  var BODY = '#7d6c88', HEAD = '#8f7d9a';
  c.save(); c.translate(x, y); c.scale(sx, sy); c.translate(-120, -226);
  c.lineCap = 'round'; c.strokeStyle = HAIR; c.lineWidth = 7; c.stroke(G.pretHair);
  limbP(c, G.pretLegs, BODY, 3);
  disc(c, 120, 150, 28, BODY, 3);
  if (o.gold > 0.02) glow(c, 120, 150, 40, '255,214,90', Math.min(1, 1.1 * o.gold) * (0.85 + 0.15 * Math.sin(o.t / 230)));
  fillP(c, G.pretNeck, BODY, 3);
  [-1, 1].forEach(function (s) {
    var a = o.ha, hx = 120 + s * lerp(54, 74, a), hy = lerp(176, 52, a), p = new Path2D();
    p.moveTo(120 + s * 10, 106); p.bezierCurveTo(120 + s * lerp(28, 34, a), lerp(130, 100, a), 120 + s * lerp(40, 64, a), lerp(150, 84, a), hx, hy);
    limbP(c, p, BODY, 3);
    c.save(); c.translate(hx, hy); c.rotate(-s * 0.245 * (1 - a)); oval(c, -s * 6 * (1 - a), lerp(18, -12, a), 11.5, 22, BODY, 3); c.restore();
  });
  oval(c, 120, 50, 22, 22, HEAD, 3);
  fillP(c, G.pretCap, HAIR, 2.5);
  eyes(c, 120, 52, 9, 6, blink(o.t, 400), 0);
  if (o.gold > 0.5) { c.strokeStyle = INK; c.lineWidth = 1.8; c.beginPath(); c.moveTo(115, 63); c.quadraticCurveTo(120, 68, 125, 63); c.stroke(); }
  else { disc(c, 120, 64, 1.8, INK); oval(c, 110, 62 + (o.t / 300) % 8, 1.6, 2.6, '#9fd8ff', 0); }
  if (o.hat) {                                                                         /* a witch hat, tall as the rest of him */
    c.save(); c.translate(120, 34); c.rotate(Math.sin(o.t / 700) * 0.05);
    c.fillStyle = '#2a1a3e'; c.beginPath(); c.ellipse(0, 0, 30, 6, 0, 0, TAU); c.fill(); c.lineWidth = 2; c.strokeStyle = INK; c.stroke();
    c.beginPath(); c.moveTo(-18, -2); c.quadraticCurveTo(-4, -34, 14, -62); c.quadraticCurveTo(10, -30, 18, -2); c.closePath(); c.fill(); c.stroke();
    c.fillStyle = GOLD; c.fillRect(-16, -12, 33, 5); c.restore();
  }
  c.restore();
}

/* Phi pop (box 240, feet at y 220): purple dress, red-glow face on the belly, a mouth that chomps by open (0…1), the woven creel at her side */
function pop(c, x, y, hh, o) {
  var sc = hh / 120; c.save(); c.translate(x, y); c.scale(sc, sc); c.translate(-110, -220);
  c.translate(0, -Math.abs(Math.sin(o.t / 640)) * 3);
  fillP(c, G.popBody, '#6c4a8c', 3); fillP(c, G.popBelt, '#2f5d62', 2.5);
  oval(c, 110, 170, 22, 26, '#120a1c', 0);
  var pl = 0.6 + 0.4 * Math.sin(o.t / 260); if (o.night) { glow(c, 103, 166, 11, '255,51,72', 0.8 * pl); glow(c, 117, 166, 11, '255,51,72', 0.8 * pl); }
  disc(c, 103, 166, 3.5, '#ff3348'); disc(c, 117, 166, 3.5, '#ff3348');
  c.strokeStyle = '#ff3348'; c.lineWidth = 2; c.lineCap = 'round'; c.beginPath(); c.moveTo(100, 182); c.quadraticCurveTo(110, 188, 120, 182); c.stroke();
  disc(c, 110, 96, 30, SKIN, 3);
  fillP(c, G.popHair, HAIR, 2.5);
  eyes(c, 110, 98, 11, 6, blink(o.t, 1100), o.look * 2);
  var mo = 7 + 10 * o.open; c.fillStyle = '#4a1030'; c.beginPath(); c.ellipse(110, 114 + o.open * 3, 10 + 3 * o.open, mo, 0, 0, TAU); c.fill(); c.lineWidth = 2.5; c.strokeStyle = INK; c.stroke();
  c.strokeStyle = '#fff'; c.lineWidth = 1.6; c.stroke(G.teeth);
  limbP(c, G.popArmL, '#6c4a8c', 4);
  var p = new Path2D(); p.moveTo(144, 140); p.quadraticCurveTo(168 + o.reach * 6, 146, 172 + o.reach * 6, 170 - o.reach * 4); limbP(c, p, '#6c4a8c', 4);
  disc(c, 172 + o.reach * 6, 172 - o.reach * 4, 6, SKIN, 2);
  c.restore();
}
/* the woven creel: a belly of cane with crossed strokes clipped to it, a dark mouth on top; wobbles by w */
function creel(c, x, y, s, w) {
  c.save(); c.translate(x, y); c.rotate(w); c.scale(s, s);
  c.fillStyle = '#c99a55'; c.fill(G.creel); c.save(); c.clip(G.creel); c.strokeStyle = 'rgba(110,60,20,.55)'; c.lineWidth = 1.4; c.beginPath();
  for (var k = -50; k < 50; k += 8) { c.moveTo(k, -50); c.lineTo(k + 40, 50); c.moveTo(k + 40, -50); c.lineTo(k, 50); } c.stroke(); c.restore();
  c.lineWidth = 3; c.strokeStyle = INK; c.stroke(G.creel); oval(c, 0, -42, 16, 6, '#3b2a1a', 2.5); c.restore();
}

/* the Phi tai hong sheet (box 240, hem at y 198): hem sways, a happy shut-eye face that goes wide for boo (0…1), an arm holding a pumpkin pail */
function sheet(c, x, y, hh, o) {
  var sc = hh / 150; c.save(); c.translate(x, y); c.scale(sc, sc); c.translate(-120, -198); c.translate(120, 198); c.rotate(Math.sin(o.t / 800) * 0.05); c.translate(-120, -198);
  c.globalAlpha *= 0.93; fillP(c, G.sheet, '#eef2ff', 3); disc(c, 120, 124, 20, '#eef2ff', 3);
  c.globalAlpha = 1;
  if (o.boo > 0.1) { oval(c, 111, 122, 4.5, 6 + 3 * o.boo, INK, 0); oval(c, 129, 122, 4.5, 6 + 3 * o.boo, INK, 0); oval(c, 120, 138, 5 + 2 * o.boo, 3 + 6 * o.boo, INK, 0); }
  else { c.strokeStyle = INK; c.lineWidth = 2.2; c.lineCap = 'round'; c.beginPath(); c.moveTo(110, 126); c.quadraticCurveTo(114, 123, 118, 126); c.moveTo(122, 126); c.quadraticCurveTo(126, 123, 130, 126); c.moveTo(112, 138); c.quadraticCurveTo(120, 133, 128, 138); c.stroke(); }
  var arm = lerp(0, -1, o.boo), p = new Path2D(); p.moveTo(138, 150); p.quadraticCurveTo(156 + arm * 10, 150 + arm * 20, 160, 168 + arm * 50); limbP(c, p, '#eef2ff', 6);
  c.save(); c.translate(160, 172 + arm * 50); c.rotate(Math.sin(o.t / 500) * 0.15); oval(c, 0, 12, 13, 10, PUMP, 2.4); c.strokeStyle = INK; c.lineWidth = 2; c.beginPath(); c.arc(0, 4, 11, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); c.restore();
  c.restore();
}

/* a wisp: a pale orb with two eyes and a trail of fading dots */
function wisp(c, x, y, r, trail, t, night, ph) {
  trail.forEach(function (p, i) { var a = (1 - i / trail.length); glow(c, p[0], p[1], r * (0.9 - i * 0.07), night ? '190,240,255' : '255,250,230', 0.5 * a); });
  glow(c, x, y, r * 2.8, night ? '184,255,240' : '255,248,220', night ? 0.55 : 0.4);
  disc(c, x, y, r, '#f4fffb'); c.fillStyle = INK; var b = blink(t, ph * 700) < 0.5; if (b) { disc(c, x - r * 0.3, y - r * 0.05, r * 0.14, INK); disc(c, x + r * 0.3, y - r * 0.05, r * 0.14, INK); }
  c.strokeStyle = INK; c.lineWidth = 1; c.beginPath(); c.arc(x, y + r * 0.2, r * 0.22, 0.2, Math.PI - 0.2); c.stroke();
}

/* a bat: two wings beating with sin(ωt) around a small body, eyes lit; asleep it hangs wrapped */
function bat(c, x, y, s, t, ph, asleep) {
  c.save(); c.translate(x, y); c.scale(s, s);
  if (asleep) { c.fillStyle = '#2a1a3e'; c.beginPath(); c.ellipse(0, 0.9, 0.8, 1.3, Math.sin(t / 1200 + ph) * 0.1, 0, TAU); c.fill(); c.beginPath(); c.moveTo(-0.5, -0.4); c.lineTo(-0.7, -1.6); c.lineTo(0, -0.7); c.lineTo(0.7, -1.6); c.lineTo(0.5, -0.4); c.fill(); c.restore(); return; }
  var w = Math.sin(t / 90 + ph); c.fillStyle = '#2a1a3e';
  [-1, 1].forEach(function (d) { c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(d * 1.6, -1.8 - w * 1.6, d * 3.4, -0.6 - w * 1.8); c.quadraticCurveTo(d * 2.7, 0.2 - w * 0.4, d * 2.1, 0.9); c.quadraticCurveTo(d * 1.4, 0.2, d * 0.9, 1.1); c.quadraticCurveTo(d * 0.4, 0.4, 0, 1.2); c.closePath(); c.fill(); });
  c.beginPath(); c.ellipse(0, 0.2, 0.8, 1.1, 0, 0, TAU); c.fill(); c.beginPath(); c.moveTo(-0.6, -0.7); c.lineTo(-0.5, -1.5); c.lineTo(-0.1, -0.9); c.lineTo(0.1, -0.9); c.lineTo(0.5, -1.5); c.lineTo(0.6, -0.7); c.fill();
  c.fillStyle = '#ffe27a'; c.fillRect(-0.45, -0.3, 0.3, 0.3); c.fillRect(0.15, -0.3, 0.3, 0.3);
  c.restore();
}

/* a dressed child from the crowd, with a costume on top */
function kid(c, d, x, y, h, P, costume, dir) {
  d.dir = dir || 1; var j = K.person(c, x, y, h, P, d);
  if (costume === 'witch') witchHat(c, j.head, h, 0.15 * d.dir, '#2a1a3e');
  else if (costume === 'cat') catEars(c, j.head, h, '#2a1a3e');
  else if (costume === 'crown') { var r = h * 0.1; c.fillStyle = GOLD; c.beginPath(); c.moveTo(j.head[0] - r, j.head[1] - h * 0.07); c.lineTo(j.head[0] - r, j.head[1] - h * 0.17); c.lineTo(j.head[0] - r * 0.4, j.head[1] - h * 0.12); c.lineTo(j.head[0], j.head[1] - h * 0.2); c.lineTo(j.head[0] + r * 0.4, j.head[1] - h * 0.12); c.lineTo(j.head[0] + r, j.head[1] - h * 0.17); c.lineTo(j.head[0] + r, j.head[1] - h * 0.07); c.fill(); }
  return j;
}
/* a pumpkin pail on a child's wrist */
function pail(c, x, y, r) { oval(c, x, y, r, r * 0.8, PUMP, 1.4); c.strokeStyle = INK; c.lineWidth = 1.2; c.beginPath(); c.arc(x, y - r * 0.2, r * 0.9, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); }

/* a speech burst: a spiked star that holds a word */
function burst(c, x, y, r, txt, a, rot) {
  c.save(); c.translate(x, y); c.rotate(rot); c.globalAlpha = a; c.fillStyle = '#ffe27a'; c.strokeStyle = INK; c.lineWidth = 1.6; c.beginPath();
  for (var i = 0; i < 16; i++) { var an = i / 16 * TAU, rr = i % 2 ? r * 0.7 : r; i ? c.lineTo(Math.cos(an) * rr, Math.sin(an) * rr) : c.moveTo(rr, 0); }
  c.closePath(); c.fill(); c.stroke(); c.rotate(-rot); c.fillStyle = INK; c.font = '800 ' + Math.round(r * 0.8) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(txt, 0, 1); c.restore();
}

function draw(S) {
  if (!G) paths();
  var c = S.c, t = S.t, hh = S.hh, deck = S.deck, night = S.night, span = S.span;
  var u = (t % LOOP) / LOOP, alt = S.alt == null ? (night ? -20 : 40) : S.alt;
  var lights = night ? 1 : alt < 8 ? 0.6 : 0.18;                                       /* how far the lamps are on: dusk half, day a little */
  var wu = Math.min(span / 8, hh * 1.5), mid = S.x0 + span / 2;
  function X(k) { return mid + (k - 4) * wu; }
  var gy = deck + hh * 0.17, vanish = 1 - win(u, 0.955, 0.995);
  function appear(at, len) { return bk((u - at) / (len || 0.05)) * vanish; }
  var fl = 0.85 + 0.15 * Math.sin(t / 110);

  /* the moon behind the house roof, bats crossing it; by day nothing here */
  if (night || alt < 8) {
    var mx = X(1.55), my = deck - hh * 3.3, mr = hh * 0.36;
    glow(c, mx, my, mr * 3.2, '255,240,200', 0.32); disc(c, mx, my, mr, '#fff3cf'); c.fillStyle = 'rgba(214,190,140,.5)';
    [[-0.3, -0.2, 0.2], [0.25, 0.15, 0.14], [-0.05, 0.4, 0.1]].forEach(function (k) { c.beginPath(); c.arc(mx + k[0] * mr, my + k[1] * mr, k[2] * mr, 0, TAU); c.fill(); });
  }

  /* ground, and the lane the party walks on */
  K.ground(c, S.x0, S.x1, deck, S.H, night ? '#1f2a1e' : '#86ad63');
  K.paper(c, K.rect(S.x0 - 4, deck + hh * 0.04, span + 8, hh * 0.34), night ? '#3b2c3d' : '#d8bf8a', 0.6);

  /* the Lanna house: sala roof and posts, a raised floor, steps; pumpkins and khom hang from the eave */
  var hx0 = X(0.75), hx1 = X(2.75), roofTop = deck - hh * 2.5, fh = hh * 0.62;
  K.sala(c, hx0, hx1, deck + hh * 0.04, roofTop, night, night ? '#5a2a2a' : '#9a3a2a');
  var wall = hx0 + (hx1 - hx0) * 0.07;
  K.paper(c, K.rect(wall, deck - fh - hh * 0.04, (hx1 - hx0) * 0.86, hh * 0.1), night ? '#4a2e1c' : '#8a5a32', 1);
  /* a window glow inside and the back wall, so the ghost has a room behind her */
  c.fillStyle = night ? 'rgba(255,180,90,.2)' : 'rgba(255,230,170,.18)'; c.fillRect(wall + 2, deck - fh - hh * 1.2, (hx1 - hx0) * 0.86 - 4, hh * 1.16);

  /* the lime, Mae Nak's cycle (11 s): drop it, reach, grab, bring it back, hold it up */
  var nakX = X(2.0), nakFloor = deck - fh - hh * 0.04, aN = appear(0.09, 0.05), nsc = hh * 1.2 / 105, sh = [nakX + 24 * nsc, nakFloor - 26 * nsc];
  var v = (u * 2) % 1, rest = [sh[0] + hh * 0.3, sh[1] + hh * 0.22], tgt = [X(2.85), gy - hh * 0.07];
  var q = v < 0.5 ? win(v, 0.14, 0.46) : 1 - win(v, 0.52, 0.86), hp = [lerp(rest[0], tgt[0], q), lerp(rest[1], tgt[1], q) - Math.sin(q * Math.PI) * hh * 0.12 * 0];
  var lp = v < 0.12 ? [lerp(rest[0], tgt[0], v / 0.12), lerp(rest[1], tgt[1], Math.pow(v / 0.12, 2)) - Math.sin(v / 0.12 * Math.PI) * hh * 0.18] : v < 0.5 ? tgt : hp;
  if (aN > 0.02) {
    c.save(); c.globalAlpha = night ? 1 : 0.94;
    maeNak(c, nakX, nakFloor, hh * 1.2 * aN, { bl: blink(t, 0), look: Math.sin(t / 900), smile: q });
    c.restore();
  }
  K.paper(c, K.rect(hx0 + (hx1 - hx0) * 0.06, nakFloor, (hx1 - hx0) * 0.88, hh * 0.1), night ? '#6a4226' : '#9a6a3a', 1.2);
  [0.1, 0.36, 0.62, 0.9].forEach(function (f) { c.strokeStyle = night ? '#35200f' : '#6a4a2a'; c.lineWidth = 1; c.beginPath(); c.moveTo(hx0 + (hx1 - hx0) * f, nakFloor + 1); c.lineTo(hx0 + (hx1 - hx0) * f, nakFloor + hh * 0.08); c.stroke(); });
  for (var st = 0; st < 3; st++) K.paper(c, K.rect(X(2.45) + st * hh * 0.04, nakFloor + hh * 0.1 + st * hh * 0.17, hh * 0.46 - st * hh * 0.08, hh * 0.12), night ? '#5a3a20' : '#a9794a', 0.5);
  if (aN > 0.02) {
    c.save(); c.globalAlpha = night ? 1 : 0.94; longArm(c, sh[0], sh[1], hp[0], hp[1], hh * 0.055 * aN, t);
    c.restore(); lime(c, lp[0], lp[1], hh * 0.07 * aN);
    if (aN < 1) poof(c, nakX, nakFloor - hh * 0.5, hh * 0.8, (u - 0.09) / 0.07);
  }
  if (vanish < 1) poof(c, nakX, nakFloor - hh * 0.5, hh * 0.8, (u - 0.955) / 0.04);

  /* pumpkins on the eave, lit one by one from the left as the wisp passes */
  var pumpU = [0.04, 0.07, 0.1, 0.13];
  for (var pi = 0; pi < 3; pi++) {
    var px = hx0 + (hx1 - hx0) * (0.1 + pi * 0.19), py = roofTop + hh * 1.72, pl = u > pumpU[pi] && vanish > 0.5 ? 1 : 0, sw = Math.sin(t / 900 + pi) * hh * 0.03;
    c.strokeStyle = 'rgba(40,20,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(px, roofTop + hh * 0.9); c.lineTo(px + sw, py - hh * 0.26); c.stroke();
    pumpkin(c, px + sw, py, hh * 0.15, pi % 4, 1, pl, 0.85 + 0.15 * Math.sin(t / 130 + pi * 2), night, lights);
  }
  /* the bats: asleep from the eave by day, flapping across the sky by night */
  if (night || alt < 8) { for (var bi = 0; bi < 3; bi++) { var bu = t / (5200 + bi * 1300) + bi * 0.37; bat(c, mid + Math.cos(bu * TAU) * span * 0.34, deck - hh * (3.0 + 0.3 * Math.sin(bu * TAU * 2 + bi)) , hh * 0.1, t, bi * 2, false); } }
  else { bat(c, hx0 + (hx1 - hx0) * 0.3, roofTop + hh * 0.9, hh * 0.1, t, 0, true); bat(c, hx0 + (hx1 - hx0) * 0.38, roofTop + hh * 0.92, hh * 0.09, t, 2, true); }

  /* a string of khom across the lane; the wisp that leads lights them left of itself */
  var sxa = hx1 + hh * 0.05, sxb = X(7.35), sy0 = deck - hh * 2.35, wpts = [[7.1, 2.1, 0], [3.1, 2.15, 0.22], [5.3, 3.3, 0.45], [6.6, 2.7, 0.7], [4.2, 3.15, 0.9], [7.1, 2.1, 1]], wx, wy;
  for (var wi = 0; wi < wpts.length - 1; wi++) if (u >= wpts[wi][2] && u <= wpts[wi + 1][2]) { var wq = ease((u - wpts[wi][2]) / (wpts[wi + 1][2] - wpts[wi][2])); wx = X(lerp(wpts[wi][0], wpts[wi + 1][0], wq)); wy = deck - hh * lerp(wpts[wi][1], wpts[wi + 1][1], wq) + Math.sin(t / 420) * hh * 0.05; }
  K.strand(c, sxa, sxb, sy0, hh * 0.25, hh * 0.46, function (lx, ly, i) {
    var la = (u < 0.22 ? Math.max(0, Math.min(1, (lx - wx) / (hh * 0.3) + 0.5)) : 1) * vanish * lights;
    khom(c, lx, ly + hh * 0.1, hh * 0.1, la, 0.85 + 0.15 * Math.sin(t / 120 + i * 2), false);
  });
  var wtrail = []; for (var tr = 1; tr <= 6; tr++) wtrail.push([wx - tr * hh * 0.09 * (u < 0.22 ? -1 : 0.4) + Math.sin(t / 300 + tr) * 2, wy + tr * hh * 0.02 + Math.sin(t / 250 + tr) * 2]);
  wisp(c, wx, wy, hh * 0.11, wtrail, t, night, 1);
  [[0.5, 0.0, 6100, 1.9], [0.62, 0.3, 4700, 1.7]].forEach(function (o, k) {              /* two more wisps drift in after the first has lit the string */
    var wa = win(u, 0.2 + k * 0.1, 0.28 + k * 0.1) * vanish; if (wa < 0.02) return;
    var ph = t / o[2] * TAU + o[1] * 9, xx = X(4.4 + k * 1.5) + Math.sin(ph) * hh * 1.8, yy = deck - hh * (o[3] + 0.4 * Math.sin(ph * 1.7 + k));
    var tl = []; for (var q2 = 1; q2 <= 5; q2++) { var pp = ph - q2 * 0.07; tl.push([X(4.4 + k * 1.5) + Math.sin(pp) * hh * 1.8, deck - hh * (o[3] + 0.4 * Math.sin(pp * 1.7 + k))]); }
    c.save(); c.globalAlpha = wa; wisp(c, xx, yy, hh * 0.09, tl, t, night, 2 + k); c.restore();
  });

  /* Nang Tani and her banana tree, the red cloth tied round the trunk, a tray of sweets at its foot */
  var bx = X(7.4), aT = appear(0.04, 0.06), peek = (win(u, 0.17, 0.24) - win(u, 0.46, 0.52) + win(u, 0.6, 0.66) - win(u, 0.9, 0.95)) * 1, wv = win(u, 0.8, 0.84) * (1 - win(u, 0.93, 0.96));
  taniTree(c, bx, gy - hh * 0.05, hh * Math.min(1, 0.4 + aT * 0.6), { t: t, peek: Math.max(0, Math.min(1, peek)), bl: blink(t, 900), wave: wv });
  c.save(); c.translate(bx - hh * 0.5, gy - hh * 0.02);
  oval(c, 0, 0, hh * 0.2, hh * 0.05, '#c9a24a', 1.4); [['#d23b3b', -0.1], ['#fff4d8', 0.02], ['#d23b3b', 0.12]].forEach(function (k, i) { disc(c, hh * k[1], -hh * 0.04 - (i === 1 ? 0.02 * hh : 0), hh * 0.06, k[0], 1); });
  var cf = 0.85 + 0.15 * Math.sin(t / 95); c.fillStyle = '#fff6d0'; c.fillRect(-hh * 0.015, -hh * 0.2, hh * 0.03, hh * 0.1); c.fillStyle = 'rgba(255,170,50,' + cf + ')'; c.beginPath(); c.ellipse(0, -hh * 0.23, hh * 0.022, hh * 0.04 * cf, 0, 0, TAU); c.fill(); glow(c, 0, -hh * 0.23, hh * 0.3, '255,190,80', 0.35 * lights); c.restore();

  /* Phi pret rises from a stub to full height (u 0.24 – 0.32); a child pours water into his bowl, his belly turns gold */
  var pX = X(3.3), aP = win(u, 0.24, 0.32) * vanish, gold = win(u, 0.36, 0.5) * vanish, hands = win(u, 0.78, 0.82) * (1 - win(u, 0.93, 0.955));
  shadow(c, pX, gy, hh * 0.5 * aP);
  if (aP > 0.02) {
    if (night) glow(c, pX, gy - hh * 1.2, hh * 1.5, '150,130,220', 0.22 * aP);
    c.save(); c.globalAlpha = night ? 1 : 0.92; pret(c, pX, gy, hh / 85 * (0.7 + 0.3 * aP), hh / 85 * aP, { t: t, gold: gold, ha: hands, hat: 1 }); c.restore();
  }
  var bowlX = pX + hh * 0.72, bowlY = gy - hh * 0.04;
  if (aP > 0.4) {
    oval(c, bowlX, bowlY, hh * 0.17, hh * 0.05, '#c9a24a', 1.4); c.fillStyle = 'rgba(143,212,255,' + (0.4 + 0.5 * win(u, 0.3, 0.45)) + ')'; c.beginPath(); c.ellipse(bowlX, bowlY - hh * 0.008, hh * 0.13, hh * 0.028, 0, 0, TAU); c.fill();
  }
  var kidH = hh * 0.8, crew = K.town(S, 5, { casual: 0.35, mohom: 0.3, sin: 0.35 });
  var pouring = u > 0.3 && u < 0.88 ? 1 : 0, kx = pX + hh * 1.05;
  if (aP > 0.4 || u > 0.3) {
    var tilt = pouring ? 0.5 + 0.35 * Math.sin(t / 800) : 0.1, kj = kid(c, crew[0], kx, gy, kidH, { lean: 0.08, legs: [0.06, 0, -0.06, 0], arms: [1.15, 0.3, 1.0, 0.4] }, 'crown', -1);
    var wv0 = kj.hand[0]; c.save(); c.translate(wv0[0], wv0[1]); c.rotate(-tilt * 0.9); oval(c, -hh * 0.04, -hh * 0.04, hh * 0.07, hh * 0.09, '#c0c8d4', 1.4); c.restore();
    if (pouring) { c.strokeStyle = 'rgba(143,212,255,.9)'; c.lineWidth = Math.max(1.4, hh * 0.022); c.setLineDash([hh * 0.05, hh * 0.04]); c.lineDashOffset = -t / 22; c.beginPath(); c.moveTo(wv0[0] - hh * 0.12, wv0[1] + hh * 0.02); c.quadraticCurveTo(wv0[0] - hh * 0.2, wv0[1] + hh * 0.1, bowlX + hh * 0.03, bowlY - hh * 0.01); c.stroke(); c.setLineDash([]); }
  }
  if (gold > 0.4) for (var gs = 0; gs < 5; gs++) { var gu = (t / 2200 + gs / 5) % 1; spark(c, pX + Math.sin(gu * 9 + gs) * hh * 0.3, gy - hh * (0.9 + gu * 1.1), hh * 0.025, Math.sin(gu * Math.PI) * 0.9 * gold); }
  if (aP > 0 && aP < 1) poof(c, pX, gy - hh * 0.8, hh * 0.9, (u - 0.24) / 0.1);

  /* the carving stall: cloth with lai kham trim, the big pumpkin cut by prog; the sheet says boo from behind it */
  var tX = X(5.0), tw = hh * 1.2, ty = gy - hh * 0.5, prog = win(u, 0.04, 0.3) * vanish, sUp = win(u, 0.55, 0.6) * (1 - win(u, 0.63, 0.67)) + win(u, 0.66, 0.7) * (1 - win(u, 0.93, 0.955)) * 0.35;
  var boo = win(u, 0.59, 0.61) * (1 - win(u, 0.66, 0.7));
  if (u > 0.5 && u < 0.955) {
    c.save(); c.beginPath(); c.rect(S.x0, 0, span, ty + hh * 0.03); c.clip(); c.globalAlpha = night ? 1 : 0.92; if (night) glow(c, tX + hh * 0.46, ty - hh * 0.3, hh * 0.9, '230,235,255', 0.25 * sUp);
    sheet(c, tX + hh * 0.46, ty + hh * 0.75 - sUp * hh * 0.8 - boo * hh * 0.08, hh * 1.1, { t: t, boo: boo }); c.restore();
  }
  /* the carver stands behind the stall, sawing at the pumpkin; she jumps at the boo and laughs after */
  var jump = boo * Math.sin(Math.min(1, (u - 0.59) / 0.07) * Math.PI), carveA = Math.sin(t / 160), laugh = u > 0.64 && u < 0.78 ? Math.sin(t / 90) * 0.04 : 0;
  var cd1 = crew[1]; cd1.garb = 'mohom'; cd1.col = '#2c3e6b'; cd1.low = '#24335a'; cd1.hat = 1;
  kid(c, cd1, tX - hh * 0.36, gy - jump * hh * 0.2, hh * 1.0, { lean: 0.08 + laugh - boo * 0.2, legs: [0.06, 0, -0.06, 0], arms: boo > 0.2 ? [2.6, 0.2, 2.8, 0.1] : [1.3 + carveA * 0.15, 0.2, 1.2 + carveA * 0.2, 0.4] }, 'witch', 1);
  K.paper(c, K.rect(tX - tw / 2, ty, tw, hh * 0.5), night ? '#7a2a2a' : '#c0392b', 1.4);
  c.fillStyle = GOLD; c.fillRect(tX - tw / 2, ty + hh * 0.07, tw, hh * 0.035); for (var zi = 0; zi < 9; zi++) { c.beginPath(); c.moveTo(tX - tw / 2 + zi * tw / 9, ty + hh * 0.2); c.lineTo(tX - tw / 2 + (zi + 0.5) * tw / 9, ty + hh * 0.28); c.lineTo(tX - tw / 2 + (zi + 1) * tw / 9, ty + hh * 0.2); c.closePath(); c.fill(); }
  K.paper(c, K.rect(tX - tw / 2 - hh * 0.03, ty - hh * 0.04, tw + hh * 0.06, hh * 0.06), night ? '#6a4226' : '#9a6a3a', 1);
  var pS = bk(u / 0.04) * vanish; pumpkin(c, tX + hh * 0.12, ty - hh * 0.03, hh * 0.3 * pS, 1, prog, prog > 0.8, fl, night, lights);
  if (prog > 0.05 && prog < 0.95) for (var ch = 0; ch < 4; ch++) { var cu = (t / 700 + ch * 0.27) % 1; c.fillStyle = 'rgba(255,170,40,' + (1 - cu) + ')'; c.fillRect(tX + hh * 0.12 + (ch - 1.5) * hh * 0.1 + cu * hh * 0.12 * (ch % 2 ? 1 : -1), ty - hh * 0.5 + cu * hh * 0.3, hh * 0.025, hh * 0.015); }
  var flare = win(u, 0.8, 0.83) * (1 - win(u, 0.83, 0.9));
  if (flare > 0.01) { glow(c, tX + hh * 0.12, ty - hh * 0.35, hh * (1.2 + 2 * flare), '255,214,110', 0.7 * flare); for (var fs = 0; fs < 10; fs++) { var fa = fs / 10 * TAU + 0.2; spark(c, tX + hh * 0.07 + Math.cos(fa) * hh * 1.8 * (0.2 + flare), ty - hh * 0.35 + Math.sin(fa) * hh * 1.2 * (0.2 + flare), hh * 0.04, flare); } }
  if (boo > 0.3) burst(c, tX - hh * 0.55, ty - hh * 1.15, hh * 0.26, 'บู!', Math.min(1, boo * 1.3), -0.2);

  /* Phi pop and her creel; two children toss sweets, to the creel and to her mouth by turns */
  var ppX = X(6.0), aPop = appear(0.4, 0.05), cX = ppX + hh * 0.5, cYtop = gy - hh * 0.36;
  var kA = [X(6.85), X(7.18)], tossU = (u > 0.46 && u < 0.84), PER = 1500, mouthOpen = 0, reachC = 0;
  [0, 1].forEach(function (k) {
    var enter = 1 - win(u, 0.28 + k * 0.03, 0.44 + k * 0.03), leave = win(u, 0.88 + k * 0.02, 0.99), kxx = kA[k] + enter * hh * 3.2 + leave * hh * 3.2;
    var walking = enter > 0.01 || leave > 0.01, ph = t / 300 + k * 2, hop = u > 0.8 && u < 0.88 ? Math.abs(Math.sin(t / 150 + k)) * 0.06 : 0;
    var arms = tossU && !walking ? [1.2 + 0.7 * Math.max(0, Math.sin((t + k * 700) / PER * TAU)), 0.2, 0.2, 0.2] : [0.1, 0.1, 1.0, 0.8];
    var pose = walking ? K.walkP(ph, false) : { lean: 0.05, lift: hop, legs: [0.06, 0, -0.06, 0], arms: u > 0.8 && u < 0.88 ? [2.8, 0.1, 2.9, 0.1] : arms };
    var cd = crew[2 + k]; if (u < 0.28 || u > 0.99) return;
    var jj = kid(c, cd, kxx, gy + hh * 0.14, kidH * (k ? 0.88 : 1), pose, k ? 'cat' : 'witch', -1);
    pail(c, jj.hand[0][0] - hh * 0.02, jj.hand[0][1] + hh * 0.04, hh * 0.06);
    if (!walking && tossU && vanish > 0.9) {
      var tt = (t + k * 700) % PER, pr = tt / (PER * 0.55), idx = Math.floor((t + k * 700) / PER);
      if (pr < 1) { var toMouth = (idx + k) % 2, tx = toMouth ? ppX + hh * 0.05 : cX, ty2 = toMouth ? gy - hh * 0.84 : cYtop, x0 = jj.hand[1][0], y0 = jj.hand[1][1];
        sweet(c, lerp(x0, tx, pr), lerp(y0, ty2, pr) - Math.sin(pr * Math.PI) * hh * 0.7, hh * 0.035, ['#ff5a8c', '#7fd8ff', '#ffd84a', '#7fe0a4'][(idx + k) % 4], pr * 9);
        if (toMouth && pr > 0.7) mouthOpen = Math.max(mouthOpen, (pr - 0.7) / 0.3); }
      else if (pr < 1.5 && ((idx + k) % 2) === 0) reachC = 1; else if (pr < 1.5) mouthOpen = Math.max(mouthOpen, 1 - (pr - 1) / 0.5);
    }
  });
  shadow(c, ppX, gy, hh * 0.55 * aPop);
  if (aPop > 0.02) {
    c.save(); c.globalAlpha = night ? 1 : 0.92; if (night) glow(c, ppX, gy - hh * 0.7, hh * 1.1, '120,60,170', 0.22 * aPop);
    pop(c, ppX, gy, hh * 0.95 * aPop, { t: t, open: mouthOpen, reach: reachC, look: Math.sin(t / 700), night: night }); c.restore();
    creel(c, cX, gy - hh * 0.02, hh / 170 * aPop, reachC * Math.sin(t / 70) * 0.06);
    if (aPop < 1) poof(c, ppX, gy - hh * 0.6, hh * 0.9, (u - 0.4) / 0.08);
  }

  /* khom loi lift off from the lane (u 0.8 – 0.96), gold sparks in their wake */
  for (var kl = 0; kl < 8; kl++) {
    var ku = (u - 0.8 - kl * 0.012) / 0.15; if (ku <= 0 || ku >= 1) continue;
    var kxl = X(1.5 + kl * 0.75) + Math.sin(ku * 6 + kl) * hh * 0.35, kyl = gy - hh * 0.6 - ku * (deck - hh * 0.4), ka = Math.min(1, ku * 6) * (1 - win(ku, 0.7, 1));
    c.save(); c.globalAlpha = ka; khom(c, kxl, kyl, hh * 0.12 * (1 - ku * 0.4), 1, 0.85 + 0.15 * Math.sin(t / 100 + kl), true); c.restore();
    if (ku < 0.8) spark(c, kxl + Math.sin(t / 200 + kl) * 3, kyl + hh * 0.25, hh * 0.025, 0.7 * ka);
  }
  /* by day four gold motes drift (K.motes); by night the band lays its own khom loi */
  if (!night) K.motes(S, 4);

  K.banner(c, S.x0 + span * 0.5, Math.max(8, deck - hh * (S.phone ? 3.9 : 3.65)), S.label, hh, '#c0561b', S.seed, S.hits);
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - hh * 3.3, y1: S.H });
}

D.addScene('ghosts-drawn', draw, /\bhallowe'?en\b|\bhaunted\b|\bghosts?\b|\bspooky\b|ฮาโลวีน|ผีสิง/i, 'p(s) = (1 − s)A + sB + n·a·sin πs·sin ωt<br>y = y₀ + v₀t − ½gt²', 1);
})();
