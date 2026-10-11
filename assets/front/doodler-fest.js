/* Festivals and places of the north for the auto-doodler (doodler.js): the Chiang Rai
   clock tower's light show, the Sunday walking street, Songkran on Loi Kroh, Chinese New
   Year at Warorot, Yi Peng on the Ping, the Flower Festival parade and Bo Sang's umbrellas
   (Nan, 2026-10-02: "make it magically lanna all of it", "animate it"). Still parts are cut
   once into an offscreen layer; what moves is drawn each frame off S.t. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU;
var person = K.person, POSE = K.POSE, walkP = K.walkP, town = K.town, CLOTH = K.CLOTH, lanternGlow = K.lanternGlow;
var FONT = '"Sarabun",system-ui,sans-serif';

/* ---------------------------------------------------------------- cut once, drawn every frame
   layer: the stage between y0 and y1, at the page's own scale; sprite: a w × h piece */
var LAYERS = {}, SPR = {}, nspr = 0;
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
function sprite(S, name, w, h, draw) {
  var m = mat(S.c), k = m ? Math.abs(m.a) : 1, key = name + '|' + Math.round(w) + '|' + Math.round(h) + '|' + k + '|' + S.seed + '|' + +S.night;
  if (SPR[key]) return SPR[key];
  if (typeof document === 'undefined') return null;
  if (++nspr > 80) { SPR = {}; nspr = 1; }
  var o = document.createElement('canvas'); o.width = Math.max(1, Math.ceil(w * k)); o.height = Math.max(1, Math.ceil(h * k));
  var q = o.getContext('2d'); q.setTransform(k, 0, 0, k, 0, 0); draw(q);
  return (SPR[key] = o);
}
function stamp(c, o, x, y, w, h) { if (o) c.drawImage(o, x, y, w, h); }

/* ---------------------------------------------------------------- small things shared */
/* a soft round glow of a given hue, from a small cut-once disc (a gradient this size each frame costs more) */
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',90%,60%,1)'); g.addColorStop(0.5, 'hsla(' + h + ',90%,60%,.45)'); g.addColorStop(1, 'hsla(' + h + ',90%,60%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o) return;
  c.save(); c.globalAlpha = a; c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
/* the event's banner, slid along so it stays on the stage */
function label(S, cx, y, col) {
  if (!S.label) return;
  var c = S.c; c.font = '800 ' + Math.round(Math.max(12, S.hh * 0.2)) + 'px ' + FONT;
  var bh = Math.max(20, S.hh * 0.32), half = c.measureText(S.label).width / 2 + 10 + bh * 0.6 + 4;
  cx = half * 2 > S.span ? S.x0 + S.span / 2 : Math.max(S.x0 + half, Math.min(S.x1 - half, cx));
  K.banner(c, cx, y, S.label, S.hh, col, S.seed, S.hits);
}
function fig(S, d, x, y, h, P, dir) { d.dir = dir; return person(S.c, x, y, h, P, d); }
/* a leg or arm reaching a point: two links, the joint bent forward (k = 1) or back (k = −1) */
function reach(hip, foot, l1, l2, dir, k) {
  var dx = (foot[0] - hip[0]) * dir, dy = foot[1] - hip[1], d = Math.min(Math.hypot(dx, dy), (l1 + l2) * 0.999), a = Math.atan2(dx, dy);
  var b = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))) * (k || 1), t1 = a + b;
  var kx = l1 * Math.sin(t1), ky = l1 * Math.cos(t1), t2 = Math.atan2(dx - kx, dy - ky);
  return [t1, t2 - t1];
}
/* a phone held up, its screen lit */
function phone(c, p, u, col) {
  c.fillStyle = '#15131c'; c.fillRect(p[0] - u * 0.035, p[1] - u * 0.11, u * 0.07, u * 0.12);
  c.fillStyle = col; c.fillRect(p[0] - u * 0.025, p[1] - u * 0.1, u * 0.05, u * 0.095);
}
/* bulbs along a catenary, each breathing on its own phase */
function bulbs(S, xa, xb, y, sag, every, hues, lit) {
  var c = S.c, t = S.t;
  K.strand(c, xa, xb, y, sag, every, function (x, yy, k) {
    var on = lit ? 0.6 + 0.4 * Math.sin(t / 380 + k * 1.7 + xa * 0.01) : 0.15, hue = hues[k % hues.length];
    if (lit) lanternGlow(c, x, yy + 4, 3.2, hue, on);
    c.fillStyle = 'hsla(' + hue + ',100%,' + (lit ? 82 : 92) + '%,' + (0.5 + 0.5 * on) + ')'; c.beginPath(); c.arc(x, yy + 4, 2.2, 0, TAU); c.fill();
  });
}
/* a firework: the shell climbs, then N sparks fly out, r = v·τ, and fall, y += ½gτ² */
function firework(c, x, y, R, a, hue, n) {
  if (a < 0) return;
  if (a < 0.55) { var ry = lerp(y + R * 3.2, y, ease(a / 0.55)); c.fillStyle = 'hsla(' + hue + ',100%,80%,.9)'; c.fillRect(x - 1, ry, 2, R * 0.35); return; }
  var b = (a - 0.55) / 1.6; if (b > 1) return;
  var r = R * (1 - Math.pow(1 - b, 3)), fall = R * 0.45 * b * b, al = 1 - b;
  c.save(); c.globalCompositeOperation = 'lighter'; c.lineCap = 'round'; c.lineWidth = 1.8;
  for (var i = 0; i < n; i++) {
    var th = i / n * TAU, ex = x + Math.cos(th) * r, ey = y + Math.sin(th) * r + fall, tx = x + Math.cos(th) * r * 0.78, ty = y + Math.sin(th) * r * 0.78 + fall * 0.8;
    c.strokeStyle = 'hsla(' + (hue + (i % 3) * 18) + ',100%,70%,' + al + ')'; c.beginPath(); c.moveTo(tx, ty); c.lineTo(ex, ey); c.stroke();
    if (i % 2) { c.fillStyle = 'hsla(' + hue + ',100%,90%,' + al + ')'; c.fillRect(ex - 1, ey - 1, 2, 2); }
  }
  if (b < 0.15) { var g = c.createRadialGradient(x, y, 0, x, y, R * 0.8); g.addColorStop(0, 'hsla(' + hue + ',100%,85%,' + (0.6 * (1 - b / 0.15)) + ')'); g.addColorStop(1, 'hsla(' + hue + ',100%,60%,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, R * 0.8, 0, TAU); c.fill(); }
  c.restore();
}
/* a Lanna roof seen side-on: tiers stepping down, the kalae horns at the ridge ends */
function lannaRoof(c, x, y, w, h, col, tiers) {
  for (var k = 0; k < tiers; k++) {
    var f = k / tiers, ww = w * (1 - f * 0.28), yy = y - h * f * 0.85, hh = h * (1 - f * 0.25) / tiers * 1.6;
    paper(c, poly([[x - ww / 2 - w * 0.05, yy], [x - ww * 0.3, yy - hh], [x + ww * 0.3, yy - hh], [x + ww / 2 + w * 0.05, yy]]), col, 1.2);
  }
  var ty = y - h * 0.85 - h / tiers * 0.35, tw = w * 0.22;
  c.save(); c.strokeStyle = '#e8b84a'; c.lineWidth = Math.max(1.5, w * 0.012); c.lineCap = 'round';
  [-1, 1].forEach(function (s) { var ex = x + s * tw; c.beginPath(); c.moveTo(ex, ty); c.quadraticCurveTo(ex + s * tw * 0.1, ty - h * 0.2, ex - s * tw * 0.25, ty - h * 0.28); c.stroke(); });
  c.restore();
}
function tungs(c, x, y, h, cols, t, n) {   /* little paper flags on sticks, for sand chedis */
  for (var i = 0; i < n; i++) {
    var fx = x + (i - (n - 1) / 2) * h * 0.18, fy = y - h * (0.55 + 0.3 * Math.cos((i - (n - 1) / 2) * 0.9)), sw = Math.sin(t / 500 + i) * h * 0.04;
    c.strokeStyle = '#c9b27a'; c.lineWidth = 1; c.beginPath(); c.moveTo(fx, y - h * 0.2); c.lineTo(fx, fy); c.stroke();
    c.fillStyle = cols[i % cols.length]; c.beginPath(); c.moveTo(fx, fy); c.lineTo(fx + h * 0.09, fy); c.lineTo(fx + h * 0.09 + sw, fy + h * 0.24); c.lineTo(fx + h * 0.045 + sw, fy + h * 0.2); c.lineTo(fx + sw, fy + h * 0.24); c.closePath(); c.fill();
  }
}

/* ================================================================ 1. the clock tower, Chiang Rai
   Chalermchai Kositpipat's golden tower on its roundabout. By night the light-and-sound
   show: colour washes climb it, hue = 360·(y/λ − t/T), beams sweep, θ = θ₀ + a·sin ωt, and
   the crowd holds phones up. By day traffic circles it, x = R·cos ωt, depth = sin ωt. */
var TOWER = [[0, .42], [.05, .42], [.05, .34], [.09, .34], [.12, .28], [.18, .36], [.25, .32], [.31, .23], [.35, .19], [.38, .25], [.56, .25], [.59, .19], [.64, .14], [.66, .18], [.71, .11], [.74, .14], [.79, .075], [.82, .095], [.88, .05], [.93, .028], [1, 0]];
var FLAMES = [.08, .15, .22, .29, .4, .47, .54, .62, .69, .77, .85];
function towerW(f) { for (var i = 1; i < TOWER.length; i++) if (TOWER[i][0] >= f) { var a = TOWER[i - 1], b = TOWER[i]; return lerp(a[1], b[1], b[0] > a[0] ? (f - a[0]) / (b[0] - a[0]) : 1); } return 0; }
function flame(q, x, y, h, s) {
  q.moveTo(x, y + h * 0.12);
  q.quadraticCurveTo(x + s * h * 0.95, y + h * 0.02, x + s * h * 0.78, y - h * 0.62);
  q.quadraticCurveTo(x + s * h * 0.98, y - h * 0.92, x + s * h * 0.58, y - h * 1.08);
  q.quadraticCurveTo(x + s * h * 0.72, y - h * 0.82, x + s * h * 0.5, y - h * 0.62);
  q.quadraticCurveTo(x + s * h * 0.42, y - h * 0.4, x, y - h * 0.35);
  q.closePath();
}
function towerBody(q, cx, by, u, Ht) {
  q.moveTo(cx - TOWER[0][1] * u, by);
  for (var i = 0; i < TOWER.length; i++) q.lineTo(cx - TOWER[i][1] * u, by - TOWER[i][0] * Ht);
  for (i = TOWER.length - 1; i >= 0; i--) q.lineTo(cx + TOWER[i][1] * u, by - TOWER[i][0] * Ht);
  q.closePath();
}
function towerFlames(q, cx, by, u, Ht, s) {
  FLAMES.forEach(function (f, i) { var w = towerW(f) * u, h = u * (0.13 + w / u * 0.42) * (i % 2 ? 0.8 : 1); flame(q, cx + s * w * 0.92, by - f * Ht, h, s); });
}
/* the tower, cut and gilded, standing at (cx, by) */
function drawTower(q, cx, by, u, Ht, night) {
  var g = q.createLinearGradient(cx - u * 0.45, 0, cx + u * 0.45, 0);
  g.addColorStop(0, night ? '#7a4a14' : '#9a6a1e'); g.addColorStop(0.32, night ? '#ffd770' : '#f7d774'); g.addColorStop(0.62, night ? '#e0a032' : '#d9a63a'); g.addColorStop(1, night ? '#6a3a10' : '#8a5a18');
  [-1, 1].forEach(function (s) { paper(q, function (p) { p.beginPath(); towerFlames(p, cx, by, u, Ht, s); }, s < 0 ? (night ? '#f0b648' : '#e9bd4e') : (night ? '#b97a26' : '#c0902f'), 1); });
  paper(q, function (p) { p.beginPath(); towerBody(p, cx, by, u, Ht); }, g, 1.8);
  q.save(); q.strokeStyle = 'rgba(110,60,10,.55)'; q.lineWidth = 1;
  [.05, .09, .31, .38, .56, .64, .71, .79, .88].forEach(function (f) { var w = towerW(f + 0.004) * u; q.beginPath(); q.moveTo(cx - w, by - f * Ht); q.lineTo(cx + w, by - f * Ht); q.stroke(); });
  /* ribs up the body, and the scallops of the bulb */
  [-0.5, 0, 0.5].forEach(function (k) { q.beginPath(); for (var f = 0.09; f <= 0.9; f += 0.02) { var x = cx + k * towerW(f) * u; f === 0.09 ? q.moveTo(x, by - f * Ht) : q.lineTo(x, by - f * Ht); } q.stroke(); });
  q.fillStyle = 'rgba(255,240,190,.55)';
  for (var k = -2; k <= 2; k++) { q.beginPath(); q.arc(cx + k * u * 0.13, by - 0.2 * Ht, u * 0.045, 0, TAU); q.fill(); }
  q.restore();
  /* the arches: the doorway at the foot, a niche above the clock */
  q.fillStyle = night ? 'rgba(40,10,40,.7)' : 'rgba(70,35,8,.6)';
  q.beginPath(); q.moveTo(cx - u * 0.12, by - 0.05 * Ht); q.lineTo(cx - u * 0.12, by - 0.11 * Ht); q.quadraticCurveTo(cx, by - 0.17 * Ht, cx + u * 0.12, by - 0.11 * Ht); q.lineTo(cx + u * 0.12, by - 0.05 * Ht); q.fill();
  q.beginPath(); q.moveTo(cx - u * 0.06, by - 0.645 * Ht); q.lineTo(cx - u * 0.06, by - 0.68 * Ht); q.quadraticCurveTo(cx, by - 0.71 * Ht, cx + u * 0.06, by - 0.68 * Ht); q.lineTo(cx + u * 0.06, by - 0.645 * Ht); q.fill();
  /* the clock's face */
  var fy = by - 0.47 * Ht, fr = u * 0.18;
  paper(q, function (p) { circ(p, cx, fy, fr * 1.18, 5); }, '#b9862a', 0.8);
  paper(q, function (p) { circ(p, cx, fy, fr, 6); }, '#fbf3dc', 0.4);
  q.strokeStyle = '#6a4a1a'; q.lineWidth = 1.2;
  for (k = 0; k < 12; k++) { var a = k / 12 * TAU; q.beginPath(); q.moveTo(cx + Math.cos(a) * fr * 0.78, fy + Math.sin(a) * fr * 0.78); q.lineTo(cx + Math.cos(a) * fr * 0.92, fy + Math.sin(a) * fr * 0.92); q.stroke(); }
  /* the finial */
  paper(q, function (p) { p.beginPath(); p.arc(cx, by - 0.94 * Ht, u * 0.04, 0, TAU); p.moveTo(cx - u * 0.012, by - 0.95 * Ht); p.lineTo(cx, by - 1.06 * Ht); p.lineTo(cx + u * 0.012, by - 0.95 * Ht); }, '#f7d774', 0.5);
}
/* a tuk-tuk, a motorbike or a car, side-on, facing dir; flat fills (paper's grain would scale) */
function flat(c, pts, col) { c.fillStyle = col; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.fill(); }
function vehicle(c, kind, x, y, s, dir, col, night, t) {
  c.save(); c.translate(x, y); c.scale(dir * s, s);
  c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5 * dir; c.shadowOffsetY = 2;
  var wh = '#1b1a20';
  if (kind === 0) {   /* tuk-tuk */
    flat(c, [[-0.42, -0.12], [-0.42, -0.36], [0.06, -0.36], [0.2, -0.24], [0.3, -0.22], [0.32, -0.12]], col);
    flat(c, [[-0.46, -0.36], [-0.44, -0.52], [0.16, -0.52], [0.2, -0.36]], '#2a2f3a');
    c.shadowColor = 'transparent'; c.fillStyle = 'rgba(255,255,255,.5)'; c.fillRect(-0.36, -0.33, 0.3, 0.12);
    c.fillStyle = '#e8b84a'; c.fillRect(-0.42, -0.2, 0.74, 0.025);
    [[-0.3, -0.06], [0.24, -0.06]].forEach(function (w) { c.fillStyle = wh; c.beginPath(); c.arc(w[0], w[1], 0.07, 0, TAU); c.fill(); c.fillStyle = '#888'; c.beginPath(); c.arc(w[0], w[1], 0.03, 0, TAU); c.fill(); });
  } else if (kind === 1) {   /* a motorbike and its rider */
    c.fillStyle = wh; [[-0.2, -0.07], [0.2, -0.07]].forEach(function (w) { c.beginPath(); c.arc(w[0], w[1], 0.075, 0, TAU); c.fill(); });
    flat(c, [[-0.24, -0.12], [-0.05, -0.22], [0.14, -0.2], [0.24, -0.1]], col);
    c.strokeStyle = '#333'; c.lineWidth = 0.025; c.beginPath(); c.moveTo(0.2, -0.07); c.lineTo(0.13, -0.3); c.lineTo(0.08, -0.32); c.stroke();
    flat(c, [[-0.08, -0.22], [-0.02, -0.5], [0.06, -0.5], [0.06, -0.24]], '#3a3550');
    c.strokeStyle = '#3a3550'; c.lineWidth = 0.05; c.lineCap = 'round'; c.beginPath(); c.moveTo(0.03, -0.46); c.lineTo(0.1, -0.33); c.moveTo(-0.05, -0.24); c.lineTo(0.06, -0.2); c.lineTo(0.06, -0.1); c.stroke();
    c.fillStyle = col; c.beginPath(); c.arc(0.02, -0.56, 0.068, Math.PI * 0.9, Math.PI * 2.1); c.fill();
  } else {   /* a small car */
    flat(c, [[-0.5, -0.08], [-0.5, -0.24], [-0.3, -0.26], [-0.18, -0.42], [0.2, -0.42], [0.34, -0.26], [0.5, -0.22], [0.5, -0.08]], col);
    c.shadowColor = 'transparent';
    flat(c, [[-0.15, -0.38], [0.0, -0.38], [0.0, -0.27], [-0.24, -0.27]], 'rgba(200,230,255,.7)'); flat(c, [[0.05, -0.38], [0.18, -0.38], [0.28, -0.27], [0.05, -0.27]], 'rgba(200,230,255,.7)');
    [[-0.3, -0.07], [0.3, -0.07]].forEach(function (w) { c.fillStyle = wh; c.beginPath(); c.arc(w[0], w[1], 0.08, 0, TAU); c.fill(); c.fillStyle = '#999'; c.beginPath(); c.arc(w[0], w[1], 0.035, 0, TAU); c.fill(); });
  }
  c.shadowColor = 'transparent';
  if (night) { var hx = kind === 1 ? 0.15 : kind === 0 ? 0.31 : 0.5, hy = kind === 1 ? -0.26 : -0.17; c.fillStyle = '#fff6c0'; c.beginPath(); c.arc(hx, hy, 0.03, 0, TAU); c.fill();
    var g = c.createLinearGradient(hx, hy, hx + 0.6, hy); g.addColorStop(0, 'rgba(255,240,180,.45)'); g.addColorStop(1, 'rgba(255,240,180,0)'); c.fillStyle = g; c.beginPath(); c.moveTo(hx, hy); c.lineTo(hx + 0.6, hy - 0.08); c.lineTo(hx + 0.6, hy + 0.1); c.fill(); }
  c.restore();
}
var PATHS = {};
function clocktower(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i;
  var cx = S.x0 + S.span * (S.phone ? 0.34 : 0.38), by = deck + u * 0.06, Ht = u * (S.phone ? 4.6 : 3.25);
  layer(S, 'ct-ground', deck - 4, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#24232c' : '#55545e');
    q.fillStyle = nt ? 'rgba(255,230,160,.35)' : 'rgba(255,255,255,.7)';
    for (var x = S.x0 + 6; x < S.x1; x += u * 0.5) q.fillRect(x, deck + u * 0.36, u * 0.26, 2);
    q.fillStyle = nt ? '#2c3a2e' : '#6a8a4a'; q.fillRect(S.x0, deck - 2, S.span, 4);
  });
  /* the traffic round the roundabout: R = 2u; the far half first */
  var cars = nt ? 2 : 4, cols = ['#2f8f5b', '#d9342b', '#4d8fd1', '#e2b33c', '#f2f2f2'], R = u * (S.phone ? 1.85 : 2.15), car = [];
  for (i = 0; i < cars; i++) { var ph = -t * 0.32 + i * TAU / cars + S.seed % 7; car.push({ x: cx + R * Math.cos(ph), z: Math.sin(ph), dir: Math.sin(ph) > 0 ? 1 : -1, k: (i + S.seed) % 3, col: cols[(i + S.seed) % cols.length] }); }
  function drive(front) { car.forEach(function (v) { if ((v.z > 0) === front) vehicle(c, v.k, v.x, deck + u * (0.14 + 0.16 * v.z), u * (0.78 + 0.14 * v.z) * (v.k === 2 ? 1.05 : 1), v.dir, v.col, nt, t); }); }
  drive(false);
  /* the glow behind it at night */
  var hue = (t * 36) % 360;
  if (nt) glow(c, cx, by - Ht * 0.5, Ht * 0.75, hue, 0.35);
  /* the plinth and the tower, cut once */
  var sw = u * 3.4, sh = Ht + u * 0.9, sx = cx - sw / 2, sy = by - Ht - u * 0.35;
  stamp(c, sprite(S, 'ct-tower', sw, sh, function (q) {
    var X = sw / 2, B = by - sy;
    paper(q, function (p) { p.beginPath(); p.ellipse(X, B + u * 0.04, u * 1.45, u * 0.22, 0, 0, TAU); }, nt ? '#3a3a44' : '#b8b0a0', 1.4);
    paper(q, function (p) { p.beginPath(); p.ellipse(X, B - u * 0.02, u * 1.3, u * 0.17, 0, 0, TAU); }, nt ? '#24452e' : '#4f8a4a', 0.6);
    var rr = rnd(77); for (var k = 0; k < 40; k++) { var a = k / 40 * TAU, fx = X + Math.cos(a) * u * 1.2, fy = B - u * 0.02 + Math.sin(a) * u * 0.14; if (Math.sin(a) < -0.2) continue; q.fillStyle = ['#f6a92c', '#ffd65a', '#e5567f', '#f2f2f2'][Math.floor(rr() * 4)]; q.beginPath(); q.arc(fx, fy, u * 0.035, 0, TAU); q.fill(); }
    paper(q, function (p) { p.beginPath(); p.ellipse(X, B, u * 0.62, u * 0.09, 0, 0, TAU); }, nt ? '#8a6a3a' : '#e8dcc0', 0.8);
    drawTower(q, X, B, u, Ht, nt);
    [-1, 1].forEach(function (s) { paper(q, rect(X + s * u * 1.05 - u * 0.06, B - u * 0.2, u * 0.12, u * 0.18), '#2a2630', 0.6); });
  }), sx, sy, sw, sh);
  /* the hands keep Bangkok time */
  var bk = (S.now || Date.now()) / 1000 + 7 * 3600, hr = (bk / 3600) % 12, mn = (bk / 60) % 60, fy = by - 0.47 * Ht, fr = u * 0.18;
  c.strokeStyle = '#3a2410'; c.lineCap = 'round';
  c.lineWidth = 2.2; c.beginPath(); c.moveTo(cx, fy); c.lineTo(cx + Math.sin(hr / 12 * TAU) * fr * 0.5, fy - Math.cos(hr / 12 * TAU) * fr * 0.5); c.stroke();
  c.lineWidth = 1.4; c.beginPath(); c.moveTo(cx, fy); c.lineTo(cx + Math.sin(mn / 60 * TAU) * fr * 0.78, fy - Math.cos(mn / 60 * TAU) * fr * 0.78); c.stroke();
  var key = cx + ',' + by + ',' + u + ',' + Ht, P2 = PATHS[key];
  if (!P2 && typeof Path2D !== 'undefined') { P2 = new Path2D(); towerBody(P2, cx, by, u, Ht); towerFlames(P2, cx, by, u, Ht, -1); towerFlames(P2, cx, by, u, Ht, 1); PATHS = {}; PATHS[key] = P2; }
  if (nt && P2) {
    /* the show: colour washes climbing the gold */
    c.save(); c.clip(P2);
    var wg = c.createLinearGradient(0, by, 0, by - Ht);
    for (i = 0; i <= 6; i++) wg.addColorStop(i / 6, 'hsl(' + ((hue + i * 40) % 360) + ',95%,58%)');
    c.globalCompositeOperation = 'color'; c.fillStyle = wg; c.fillRect(cx - u, by - Ht * 1.1, u * 2, Ht * 1.15);
    var p = (t / 2.6) % 1.4 - 0.2, sg = c.createLinearGradient(0, by - Ht * (p - 0.15), 0, by - Ht * (p + 0.15));
    sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'hsla(' + ((hue + 180) % 360) + ',100%,80%,.55)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
    c.globalCompositeOperation = 'lighter'; c.fillStyle = sg; c.fillRect(cx - u, by - Ht * 1.1, u * 2, Ht * 1.15);
    c.restore();
    /* beams from the plinth */
    c.save(); c.globalCompositeOperation = 'lighter';
    [-1.15, -0.55, 0.55, 1.15].forEach(function (o, k) {
      var bx = cx + o * u, th = o * 0.36 + 0.3 * Math.sin(t * 0.9 + k * 1.7), L = u * 2.5, ex = bx + Math.sin(th) * L, ey = by - Math.cos(th) * L, bh = (hue + 90 * k) % 360;
      var bg = c.createLinearGradient(bx, by, ex, ey); bg.addColorStop(0, 'hsla(' + bh + ',100%,70%,.42)'); bg.addColorStop(1, 'hsla(' + bh + ',100%,70%,0)');
      var nx = Math.cos(th) * u * 0.28, ny = Math.sin(th) * u * 0.28;
      c.fillStyle = bg; c.beginPath(); c.moveTo(bx - 2, by); c.lineTo(ex - nx, ey - ny); c.lineTo(ex + nx, ey + ny); c.lineTo(bx + 2, by); c.fill();
    });
    /* gold glints at the flame tips */
    for (i = 0; i < FLAMES.length * 2; i++) {
      var tw = Math.pow(Math.max(0, Math.sin(t * 2.3 + i * 2.39)), 12); if (tw < 0.05) continue;
      var f = FLAMES[i >> 1], s2 = i % 2 ? 1 : -1, gx = cx + s2 * (towerW(f) * u + u * 0.12), gy = by - f * Ht - u * 0.12, z = u * 0.09 * tw;
      c.fillStyle = 'rgba(255,240,200,' + tw + ')'; c.beginPath(); c.moveTo(gx, gy - z * 2); c.quadraticCurveTo(gx, gy, gx + z * 2, gy); c.quadraticCurveTo(gx, gy, gx, gy + z * 2); c.quadraticCurveTo(gx, gy, gx - z * 2, gy); c.quadraticCurveTo(gx, gy, gx, gy - z * 2); c.fill();
    }
    c.restore();
    K.notes(c, cx - u * 1.05, by - u * 0.3, S.t, 3, 'hsl(' + hue + ',90%,80%)');
    K.notes(c, cx + u * 1.0, by - u * 0.3, S.t + 1300, 3, 'hsl(' + ((hue + 120) % 360) + ',90%,80%)');
  } else if (P2) {
    /* by day the sun runs down the gold */
    c.save(); c.clip(P2); c.globalCompositeOperation = 'lighter';
    var q2 = ((t / 5) % 1.6) - 0.3, dg = c.createLinearGradient(cx - u * 0.6, by - Ht * (q2 + 0.2), cx + u * 0.6, by - Ht * q2);
    dg.addColorStop(0, 'rgba(255,250,220,0)'); dg.addColorStop(0.5, 'rgba(255,250,220,.5)'); dg.addColorStop(1, 'rgba(255,250,220,0)');
    c.fillStyle = dg; c.fillRect(cx - u, by - Ht * 1.1, u * 2, Ht * 1.15); c.restore();
  }
  drive(true);
  /* the crowd: phones up at night, a few visitors by day */
  var n = nt ? (S.phone ? 6 : 8) : (S.phone ? 3 : 4), crew = town(S, n, { casual: 0.6, sin: 0.2, mohom: 0.2 }), beat = t * 1.9;
  for (i = 0; i < n; i++) {
    var fx = S.x0 + S.span * (nt ? (i + 0.5) / n : [0.08, 0.7, 0.86, 0.95][i]), row = i % 2, dir = fx < cx ? 1 : -1;
    if (nt && Math.abs(fx - cx) < u * 0.35) fx += dir * u * 0.4;
    var up = nt ? i % 3 !== 2 : i % 2 === 0, sway = 0.04 * Math.sin(beat + i);
    var P = up ? { lean: sway, legs: [0.06, 0, -0.06, 0], arms: [2.35 + 0.06 * Math.sin(t + i), -0.75, 0.25, 0.3] } : { lean: sway, legs: [0.06, 0, -0.06, 0], arms: [0.2, 0.2, nt ? 2.9 + 0.2 * Math.sin(beat * 2 + i) : 0.1, 0] };
    var me = fig(S, crew[i], fx, deck + u * (0.34 + row * 0.2), u * (0.92 + row * 0.06), P, dir);
    if (up) phone(c, me.hand[0], u, nt ? 'hsl(' + ((hue + i * 25) % 360) + ',90%,78%)' : '#bfe0ff');
  }
  label(S, S.x0 + S.span * (S.phone ? 0.78 : 0.76), deck - u * 1.95, nt ? '#8a3ac0' : '#c0902f');
  S.hits.push({ k: 'event', x0: cx - u * 1.5, x1: cx + u * 1.5, y0: by - Ht, y1: S.H });
}

/* ================================================================ 2. the Sunday walking street
   Ratchadamnoen from Tha Phae Gate toward Wat Phra Singh: stalls of paper umbrellas, soap
   flowers, elephant pants and lanterns under strings of lights, y = a·cosh(x/a); a blind
   band and a salo fiddler busking; the crowd shuffles both ways, x = x₀ ± vt. */
var GOODS = ['umbrella', 'soap', 'food', 'pants', 'lantern', 'bags'];
function stallGoods(q, kind, x0, x1, top, ty, u, nt, r) {
  var w = x1 - x0, i, k, pastel = ['#ffd1e8', '#c3a6ff', '#7fe0a4', '#ffe9a8', '#ffb38a', '#a8e0ff'];
  if (kind === 'umbrella') {
    for (i = 0; i < 3; i++) {
      var ux = x0 + w * (0.22 + i * 0.28), uy = ty - u * (0.38 + (i % 2) * 0.22), ur = u * 0.24, col = ['#e04a3a', '#2f8f5b', '#f2c94c', '#4d8fd1', '#9b6bd6'][Math.floor(r() * 5)];
      paper(q, function (p) { p.beginPath(); for (var j = 0; j < 16; j++) { var a = j / 16 * TAU, rr = j % 2 ? ur : ur * 0.94; p.lineTo(ux + Math.cos(a) * rr, uy + Math.sin(a) * rr); } p.closePath(); }, col, 0.8);
      q.strokeStyle = 'rgba(255,255,255,.35)'; q.lineWidth = 0.8; for (k = 0; k < 8; k++) { var a = k / 8 * TAU; q.beginPath(); q.moveTo(ux, uy); q.lineTo(ux + Math.cos(a) * ur, uy + Math.sin(a) * ur); q.stroke(); }
      for (k = 0; k < 5; k++) { var a2 = k / 5 * TAU + 0.3; q.fillStyle = k % 2 ? '#fff4d0' : '#ffd1e8'; q.beginPath(); q.arc(ux + Math.cos(a2) * ur * 0.55, uy + Math.sin(a2) * ur * 0.55, ur * 0.13, 0, TAU); q.fill(); }
      q.fillStyle = '#5a3a1a'; q.beginPath(); q.arc(ux, uy, ur * 0.08, 0, TAU); q.fill();
    }
  } else if (kind === 'soap') {
    for (i = 0; i < 2; i++) for (k = 0; k < 6; k++) {
      var sx = x0 + w * (0.12 + k * 0.152) + i * w * 0.06, sy = ty - u * (0.06 + i * 0.1), sr = u * 0.055, sc = pastel[Math.floor(r() * pastel.length)];
      q.fillStyle = sc; q.beginPath(); q.arc(sx, sy, sr, 0, TAU); q.fill();
      q.strokeStyle = 'rgba(120,60,90,.35)'; q.lineWidth = 0.8; q.beginPath(); q.arc(sx, sy, sr * 0.6, 0, TAU); q.stroke(); q.beginPath(); q.arc(sx, sy, sr * 0.25, 0, TAU); q.stroke();
    }
    paper(q, rect(x0 + w * 0.68, ty - u * 0.5, w * 0.2, u * 0.28), 'rgba(220,240,255,.55)', 0.5);
    for (k = 0; k < 3; k++) { q.fillStyle = pastel[k + 1]; q.beginPath(); q.arc(x0 + w * (0.73 + k * 0.05), ty - u * (0.3 + (k % 2) * 0.08), u * 0.04, 0, TAU); q.fill(); }
  } else if (kind === 'pants') {
    q.strokeStyle = '#5a4030'; q.lineWidth = 2; q.beginPath(); q.moveTo(x0 + w * 0.06, top + u * 0.28); q.lineTo(x1 - w * 0.06, top + u * 0.28); q.stroke();
    for (i = 0; i < 4; i++) {
      var px = x0 + w * (0.17 + i * 0.22), py = top + u * 0.28, pw = w * 0.17, ph = u * 0.62, pc = ['#2a3a8a', '#7a1f3a', '#1f5a4a', '#5a2a6a', '#c0392b', '#2a6a8a'][Math.floor(r() * 6)];
      paper(q, poly([[px - pw / 2, py], [px + pw / 2, py], [px + pw * 0.55, py + ph], [px + pw * 0.08, py + ph], [px, py + ph * 0.35], [px - pw * 0.08, py + ph], [px - pw * 0.55, py + ph]]), pc, 0.6);
      q.fillStyle = 'rgba(255,230,170,.7)'; for (k = 0; k < 4; k++) { var ey = py + ph * (0.2 + k * 0.2); q.beginPath(); q.ellipse(px - pw * 0.25, ey, pw * 0.12, pw * 0.08, 0, 0, TAU); q.fill(); q.beginPath(); q.ellipse(px + pw * 0.25, ey + ph * 0.1, pw * 0.12, pw * 0.08, 0, 0, TAU); q.fill(); }
      q.fillStyle = 'rgba(255,255,255,.5)'; q.fillRect(px - pw / 2, py + 2, pw, 2);
    }
  } else if (kind === 'lantern') {
    for (i = 0; i < 4; i++) {
      var lx = x0 + w * (0.16 + i * 0.23), ly = top + u * (0.36 + (i % 2) * 0.12), lr = u * 0.12, lc = ['#e04a3a', '#f6a92c', '#e5567f', '#f2c94c', '#9b6bd6'][Math.floor(r() * 5)];
      q.strokeStyle = 'rgba(40,20,30,.8)'; q.lineWidth = 1; q.beginPath(); q.moveTo(lx, top + u * 0.12); q.lineTo(lx, ly - lr); q.stroke();
      paper(q, function (p) { p.beginPath(); p.ellipse(lx, ly, lr * 0.95, lr, 0, 0, TAU); }, lc, 0.6);
      q.strokeStyle = 'rgba(80,20,10,.35)'; q.lineWidth = 0.8; [-0.5, 0, 0.5].forEach(function (f) { q.beginPath(); q.ellipse(lx, ly, Math.abs(f) * lr * 0.95 + 0.5, lr, 0, 0, TAU); q.stroke(); });
      q.fillStyle = '#3a2a1a'; q.fillRect(lx - lr * 0.4, ly - lr - 2, lr * 0.8, 3); q.fillRect(lx - lr * 0.4, ly + lr - 1, lr * 0.8, 3);
      q.fillStyle = '#f2c94c'; q.fillRect(lx - 1, ly + lr + 2, 2, lr * 0.6);
    }
  } else if (kind === 'food') {
    paper(q, rect(x0 + w * 0.12, ty - u * 0.42, w * 0.6, u * 0.32), 'rgba(220,240,255,.5)', 0.6);
    for (k = 0; k < 5; k++) { q.fillStyle = ['#e0773a', '#f7e08a', '#c0392b', '#7fe0a4', '#f08a5d'][k]; q.fillRect(x0 + w * (0.16 + k * 0.11), ty - u * 0.2, w * 0.08, u * 0.08); }
    for (k = 0; k < 6; k++) { q.strokeStyle = '#d9b36a'; q.lineWidth = 1.2; q.beginPath(); q.moveTo(x0 + w * (0.18 + k * 0.08), ty - u * 0.24); q.lineTo(x0 + w * (0.2 + k * 0.08), ty - u * 0.36); q.stroke(); q.fillStyle = '#a8432f'; q.beginPath(); q.arc(x0 + w * (0.195 + k * 0.08), ty - u * 0.3, u * 0.025, 0, TAU); q.fill(); }
    paper(q, function (p) { p.beginPath(); p.ellipse(x1 - w * 0.17, ty - u * 0.06, w * 0.13, u * 0.07, 0, 0, TAU); }, '#3a3a40', 0.6);
    q.fillStyle = '#1b1a20'; [x0 + w * 0.2, x1 - w * 0.25].forEach(function (wx) { q.beginPath(); q.arc(wx, ty + u * 0.36, u * 0.07, 0, TAU); q.fill(); });
  } else {   /* yaam, the woven shoulder bags */
    q.strokeStyle = '#5a4030'; q.lineWidth = 2; q.beginPath(); q.moveTo(x0 + w * 0.06, top + u * 0.24); q.lineTo(x1 - w * 0.06, top + u * 0.24); q.stroke();
    for (i = 0; i < 5; i++) {
      var bx = x0 + w * (0.14 + i * 0.18), bw = w * 0.14, bh = u * 0.3, by2 = top + u * 0.42, bc = CLOTH[Math.floor(r() * CLOTH.length)];
      q.strokeStyle = bc; q.lineWidth = 1.6; q.beginPath(); q.moveTo(bx - bw * 0.35, by2); q.lineTo(bx, top + u * 0.24); q.lineTo(bx + bw * 0.35, by2); q.stroke();
      paper(q, rect(bx - bw / 2, by2, bw, bh), bc, 0.5);
      q.fillStyle = 'rgba(40,20,30,.4)'; for (k = 0; k < 3; k++) q.fillRect(bx - bw / 2, by2 + bh * (0.25 + k * 0.25), bw, 1.5);
      q.fillStyle = '#f2e6c9'; for (k = 0; k < 4; k++) q.fillRect(bx - bw / 2 + k * bw / 4 + 1, by2 + bh, 1.5, bh * 0.25);
    }
  }
}
function walkingStreet(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, X = function (f) { return S.x0 + S.span * f; };
  var ns = 5, s0 = X(0.27), s1 = X(0.995), sw = (s1 - s0) / ns, top = deck - u * 1.32, ty = deck - u * 0.42;
  var order = GOODS.slice((S.seed >>> 3) % GOODS.length).concat(GOODS.slice(0, (S.seed >>> 3) % GOODS.length));
  layer(S, 'ws-back', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#2b2522' : '#9a8670');
    q.fillStyle = nt ? 'rgba(255,220,150,.08)' : 'rgba(255,255,255,.12)'; for (var x = S.x0; x < S.x1; x += u * 0.3) q.fillRect(x, deck + u * 0.02, u * 0.28, S.H - deck);
    /* Wat Phra Singh far down the road, between the stalls' roofs */
    lannaRoof(q, X(0.66), deck - u * 1.2, u * 1.5, u * 0.85, nt ? '#5a2018' : '#a8402f', 3);
    paper(q, function (p) { p.beginPath(); var bx = X(0.84); p.moveTo(bx - u * 0.22, deck - u * 1.2); p.quadraticCurveTo(bx - u * 0.2, deck - u * 1.6, bx, deck - u * 1.75); p.lineTo(bx, deck - u * 2.08); p.lineTo(bx + u * 0.02, deck - u * 1.75); p.quadraticCurveTo(bx + u * 0.2, deck - u * 1.6, bx + u * 0.22, deck - u * 1.2); p.closePath(); }, nt ? '#c9a24a' : '#e8c25a', 1);
    /* Tha Phae Gate: the wall, its merlons, the arch */
    var gx0 = S.x0 - u * 0.4, gx1 = X(0.235), gy = deck - u * 1.5, m = u * 0.14, brick = nt ? '#6d2b20' : '#a8432f';
    paper(q, function (p) {
      p.beginPath(); p.moveTo(gx0, deck); p.lineTo(gx0, gy);
      for (var xm = gx0; xm < gx1 - m; xm += m * 2) { p.lineTo(xm, gy - m); p.lineTo(xm + m, gy - m); p.lineTo(xm + m, gy); p.lineTo(xm + m * 2, gy); }
      p.lineTo(gx1, gy); p.lineTo(gx1, deck); p.closePath();
      var ax = (gx0 + gx1) / 2 + u * 0.2, aw = u * 0.62; p.moveTo(ax - aw / 2, deck); p.lineTo(ax - aw / 2, deck - u * 0.62); p.arc(ax, deck - u * 0.62, aw / 2, Math.PI, 0); p.lineTo(ax + aw / 2, deck); p.closePath();
    }, brick, 1.8);
    q.strokeStyle = 'rgba(60,15,10,.3)'; q.lineWidth = 0.7;
    for (var rw = 1; rw < 9; rw++) { var yy = gy + rw * u * 0.17; q.beginPath(); q.moveTo(gx0, yy); q.lineTo(gx1, yy); q.stroke(); for (var bx = gx0 + (rw % 2) * u * 0.12; bx < gx1; bx += u * 0.24) { q.beginPath(); q.moveTo(bx, yy); q.lineTo(bx, yy - u * 0.17); q.stroke(); } }
    q.fillStyle = nt ? '#3a1a10' : '#e8d8b0'; q.font = '700 ' + Math.round(u * 0.13) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle';
    paper(q, rect((gx0 + gx1) / 2 - u * 0.45 + u * 0.2, gy + u * 0.18, u * 0.9, u * 0.22), nt ? '#e8d8b0' : '#5a1a10', 0.6);
    q.fillText('ประตูท่าแพ', (gx0 + gx1) / 2 + u * 0.2, gy + u * 0.3);
    /* the stalls */
    var r = rnd(S.seed + 5), tops = ['#f2f2f2', '#e8f0e8', '#fff4dc'];
    for (var s = 0; s < ns; s++) {
      var a0 = s0 + s * sw + sw * 0.04, a1 = a0 + sw * 0.92, val = ['#d94b3b', '#2f8f5b', '#4d8fd1', '#e2b33c', '#9b6bd6'][(s + S.seed) % 5];
      paper(q, rect(a0 + 2, top, 3, deck - top), '#5a4030', 0.8); paper(q, rect(a1 - 5, top, 3, deck - top), '#5a4030', 0.8);
      paper(q, poly([[a0 - 4, top + u * 0.06], [a0 + sw * 0.2, top - u * 0.22], [a1 - sw * 0.2, top - u * 0.22], [a1 + 4, top + u * 0.06]]), nt ? '#c8c0b0' : tops[s % 3], 1.4);
      paper(q, function (p) { p.beginPath(); p.moveTo(a0 - 4, top + u * 0.04); p.lineTo(a1 + 4, top + u * 0.04); var sc = (a1 - a0 + 8) / 7; for (var b = 7; b > 0; b--) p.arc(a0 - 4 + (b - 0.5) * sc, top + u * 0.06, sc / 2, 0, Math.PI); p.closePath(); }, val, 0.8);
      paper(q, rect(a0, ty, a1 - a0, u * 0.07), nt ? '#5a4030' : '#9a6a4a', 0.8);
      paper(q, rect(a0 + 3, ty + u * 0.07, a1 - a0 - 6, u * 0.3), ['#7a1f3a', '#2a3a6a', '#1f5a4a', '#8a3a1a'][(s + 1) % 4], 0.6);
      q.fillStyle = '#e8b84a'; q.fillRect(a0 + 3, ty + u * 0.3, a1 - a0 - 6, u * 0.05);
      stallGoods(q, order[s], a0, a1, top, ty, u, nt, r);
    }
    /* the light poles */
    for (s = 0; s <= ns; s++) paper(q, rect(s0 + s * sw - 2, deck - u * 2.02, 4, u * 0.7), '#4a3a2a', 0.6);
  });
  /* strings of lights over the lane, and a bare bulb in each stall */
  for (i = 0; i < ns; i++) bulbs(S, s0 + i * sw, s0 + (i + 1) * sw, deck - u * 2.0, u * 0.22, 15, [42, 50, 30, 55], nt);
  bulbs(S, X(0.02), s0, deck - u * 1.62, u * 0.18, 15, [42, 50, 30, 55], nt);
  for (i = 0; i < ns; i++) {
    var bx = s0 + (i + 0.5) * sw, byy = top + u * 0.14;
    if (nt) lanternGlow(c, bx, byy, u * 0.12, 42, 0.7 + 0.3 * Math.sin(S.t / 300 + i));
    c.fillStyle = nt ? '#fff2c0' : '#f6f0e0'; c.beginPath(); c.arc(bx, byy, u * 0.035, 0, TAU); c.fill();
    if (order[i] === 'lantern' && nt) for (var k = 0; k < 4; k++) lanternGlow(c, s0 + i * sw + sw * 0.04 + sw * 0.92 * (0.16 + k * 0.23), top + u * (0.36 + (k % 2) * 0.12), u * 0.1, 30, 0.8);
    if (order[i] === 'food') { var fx = s0 + i * sw + sw * 0.04 + sw * 0.92 * 0.83; c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 1.4; for (k = 0; k < 2; k++) { c.beginPath(); for (var y = 0; y < u * 0.5; y += 3) { var xx = fx + k * 6 + Math.sin(y * 0.1 - S.t / 300 + k) * (2 + y * 0.06); y ? c.lineTo(xx, ty - u * 0.12 - y) : c.moveTo(xx, ty - u * 0.12); } c.stroke(); } }
  }
  /* the crowd, two lanes, slow */
  var per = S.phone ? 6 : 7, crew = town(S, per * 2 + 4, { casual: 0.62, sin: 0.22, mohom: 0.16 }), Lp = S.span + u * 2;
  for (var lane = 0; lane < 2; lane++) for (i = 0; i < per; i++) {
    var dir = lane ? 1 : -1, v = u * (0.16 + 0.04 * ((i * 7 + lane) % 3)), base = (i / per * Lp + ((i * 37 + S.seed) % 50) / 50 * u * 0.5 + t * v) % Lp;
    var px = dir > 0 ? S.x0 - u + base : S.x1 + u - base, d = crew[lane * per + i];
    var me = fig(S, d, px, deck + u * (lane ? 0.3 : 0.07), u * (lane ? 0.95 : 0.86), walkP(t * TAU * 0.55 + i * 1.3, false), dir);
    var hold = (i + lane * 3 + S.seed) % 5;
    if (hold === 0) paper(c, rect(me.hand[0][0] - 4, me.hand[0][1], 9, 10), '#f2e6c9', 0.4);
    if (hold === 1) { c.strokeStyle = '#5a3a1a'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(me.hand[1][0], me.hand[1][1]); c.lineTo(me.hand[1][0], me.hand[1][1] - u * 0.6); c.stroke();
      c.fillStyle = ['#e04a3a', '#2f8f5b', '#f2c94c'][i % 3]; c.beginPath(); c.moveTo(me.hand[1][0] - u * 0.3, me.hand[1][1] - u * 0.5); c.quadraticCurveTo(me.hand[1][0], me.hand[1][1] - u * 0.78, me.hand[1][0] + u * 0.3, me.hand[1][1] - u * 0.5); c.closePath(); c.fill(); }
    if (hold === 2) { c.strokeStyle = '#d9b36a'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(me.hand[0][0], me.hand[0][1]); c.lineTo(me.hand[0][0] + dir * u * 0.05, me.hand[0][1] - u * 0.16); c.stroke(); c.fillStyle = '#a8432f'; c.beginPath(); c.arc(me.hand[0][0] + dir * u * 0.04, me.hand[0][1] - u * 0.12, u * 0.025, 0, TAU); c.fill(); }
  }
  /* the blind band at the gate's foot, dark glasses, a bowl for coins */
  var bb = per * 2, beat = t * 2.1, by0 = deck + u * 0.62, bxs = [X(0.05), X(0.13), X(0.21)];
  for (i = 0; i < 3; i++) {
    var d2 = crew[bb + i]; d2.garb = 'casual'; d2.col = ['#3a4a6a', '#f2f2f2', '#6a3a3a'][i]; d2.hat = false;
    var arm = i === 0 ? [1.25, 1.2, 1.1, 0.6] : i === 1 ? [0.9, 0.9, 0.55 + 0.3 * Math.sin(beat * Math.PI * 2), 0.7] : [1.2, 0.5 + 0.15 * Math.sin(beat * Math.PI * 2 + 1), 1.2, 0.5 + 0.15 * Math.sin(beat * Math.PI * 2)];
    var M = fig(S, d2, bxs[i], by0, u * 0.9, { lean: 0.04, seat: 0.27, legs: POSE.sit.legs, arms: arm }, 1);
    c.fillStyle = '#111'; c.fillRect(M.head[0] + u * 0.005, M.head[1] - u * 0.04, u * 0.085, u * 0.04);
    if (i === 0) { c.strokeStyle = '#aaa'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(bxs[0] + u * 0.22, by0); c.lineTo(bxs[0] + u * 0.22, M.head[1] + u * 0.06); c.lineTo(bxs[0] + u * 0.13, M.head[1] + u * 0.05); c.stroke(); }
    if (i === 1) paper(c, function (p) { p.save(); p.translate(M.hip[0] + 3, M.hip[1] - u * 0.12); p.rotate(-0.45); p.beginPath(); p.ellipse(0, 0, u * 0.13, u * 0.09, 0, 0, TAU); p.rect(u * 0.09, -u * 0.022, u * 0.34, u * 0.045); p.restore(); }, '#b5652a', 0.8);
    if (i === 2) { paper(c, rect(M.hand[0][0] - u * 0.05, M.hand[0][1] - u * 0.02, u * 0.36, u * 0.08), '#2a2a30', 0.6); c.fillStyle = '#f2f2f2'; for (k = 0; k < 7; k++) c.fillRect(M.hand[0][0] - u * 0.03 + k * u * 0.045, M.hand[0][1] - u * 0.005, u * 0.035, u * 0.03); }
  }
  paper(c, function (p) { p.beginPath(); p.arc(X(0.27), by0 - 2, u * 0.08, 0, Math.PI); p.closePath(); }, '#c0c0c8', 0.5);
  c.fillStyle = '#e8b84a'; c.beginPath(); c.arc(X(0.27) - 3, by0 - 4, 2, 0, TAU); c.arc(X(0.27) + 3, by0 - 5, 2, 0, TAU); c.fill();
  K.notes(c, X(0.13), deck - u * 0.2, S.t, 3, nt ? '#ffe2a0' : '#7a3a8a');
  /* the salo player, the Lanna fiddle on his knee; the bow goes x = A·sin ωt */
  var fxp = X(0.8), bow = Math.sin(t * TAU * 0.9) * u * 0.14, d3 = crew[bb + 3]; d3.garb = 'mohom'; d3.col = '#2c3e6b'; d3.low = '#24335a';
  var F = fig(S, d3, fxp, by0, u * 0.9, { lean: 0.02, seat: 0.1, legs: POSE.lotus.legs, arms: [0.75, 1.1, 1.2 + bow / u * 1.5, 0.5] }, -1);
  var nx = fxp - u * 0.14, ny = by0 - u * 0.2;
  c.strokeStyle = '#3a2410'; c.lineWidth = 2; c.beginPath(); c.moveTo(nx, ny); c.lineTo(nx + u * 0.04, ny - u * 0.55); c.stroke();
  paper(c, function (p) { p.beginPath(); p.arc(nx, ny, u * 0.08, 0, TAU); }, '#7a4a2a', 0.5);
  c.strokeStyle = '#e8d8b0'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(nx - u * 0.2 + bow, ny - u * 0.14); c.lineTo(nx + u * 0.2 + bow, ny - u * 0.17); c.stroke();
  K.notes(c, nx, ny - u * 0.6, S.t + 900, 2, nt ? '#ffe2a0' : '#7a3a8a');
  label(S, X(0.6), deck - u * 2.0 + u * 0.3, '#d94b3b');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2, y1: S.H });
}

/* ================================================================ 3. Songkran on Loi Kroh Road
   Water guns arc, y = v₀t − ½gt²; a pickup with its barrel drives through and the bucket
   flies; white clay on faces, flower shirts, rainbows in the spray by day; at the road's
   end sand chedis with their tung, and water poured on an elder's hands (rot nam dam hua). */
function flowerShirt(c, me, u, d) {
  var cols = ['#fff4d0', '#ffd84a', '#ffffff', '#ff8ab0'];
  for (var k = 0; k < 6; k++) {
    var f = 0.18 + (k >> 1) * 0.28, sx = lerp(me.sh[0], me.hip[0], f) + (k % 2 ? 1 : -1) * u * 0.035, sy = lerp(me.sh[1], me.hip[1], f) + (k % 2) * u * 0.02;
    c.fillStyle = cols[(k + d) % cols.length];
    for (var p = 0; p < 4; p++) { c.beginPath(); c.arc(sx + Math.cos(p * 1.57) * u * 0.012, sy + Math.sin(p * 1.57) * u * 0.012, u * 0.011, 0, TAU); c.fill(); }
  }
}
function clay(c, me, u, dir) {
  c.fillStyle = 'rgba(250,250,245,.92)';
  c.beginPath(); c.ellipse(me.head[0] + dir * u * 0.035, me.head[1] + u * 0.045, u * 0.04, u * 0.025, 0.3, 0, TAU); c.fill();
  c.beginPath(); c.arc(me.head[0] + dir * u * 0.075, me.head[1] + u * 0.005, u * 0.02, 0, TAU); c.fill();
  c.beginPath(); c.arc(me.head[0] - dir * u * 0.01, me.head[1] + u * 0.07, u * 0.018, 0, TAU); c.fill();
}
function gun(c, h, dir, u, col) {
  c.fillStyle = col; c.beginPath(); c.moveTo(h[0] - dir * u * 0.06, h[1] - u * 0.04); c.lineTo(h[0] + dir * u * 0.2, h[1] - u * 0.04); c.lineTo(h[0] + dir * u * 0.2, h[1] + u * 0.0); c.lineTo(h[0] - dir * u * 0.06, h[1] + u * 0.02); c.fill();
  c.fillStyle = 'rgba(160,220,255,.9)'; c.beginPath(); c.arc(h[0] + dir * u * 0.04, h[1] - u * 0.09, u * 0.05, 0, TAU); c.fill();
  c.fillStyle = '#2a2a30'; c.fillRect(h[0] - u * 0.012, h[1], u * 0.024, u * 0.07);
  return [h[0] + dir * u * 0.21, h[1] - u * 0.025];
}
/* a stream of drops from p with velocity (vx, vy), u/s; g pulls them down; on: 0…1 */
function stream(c, p, vx, vy, g, floor, t, on, u, n, rate) {
  var T = (vy + Math.sqrt(vy * vy + 2 * g * Math.max(0, floor - p[1]))) / g, land = null;
  if (on(t) > 0.5) { c.strokeStyle = 'rgba(200,235,255,.4)'; c.lineWidth = u * 0.03; c.lineCap = 'round'; c.beginPath();
    for (var j = 0; j <= 12; j++) { var aj = j / 12 * T, xj = p[0] + vx * aj, yj = p[1] - vy * aj + 0.5 * g * aj * aj; j ? c.lineTo(xj, yj) : c.moveTo(xj, yj); } c.stroke(); }
  for (var k = 0; k < n; k++) {
    var a = ((t * rate + k / n) % 1) * T, born = t - a; if (on(born) < 0.5) continue;
    var x = p[0] + vx * a, y = p[1] - vy * a + 0.5 * g * a * a;
    c.fillStyle = k % 3 ? 'rgba(170,220,255,.85)' : 'rgba(255,255,255,.9)'; c.beginPath(); c.arc(x, y, u * (0.026 + 0.01 * (k % 2)), 0, TAU); c.fill();
    if (a > T * 0.9) land = [x, floor];
  }
  if (land) { c.strokeStyle = 'rgba(200,235,255,.8)'; c.lineWidth = 1.2; for (var s = -2; s <= 2; s++) { c.beginPath(); c.moveTo(land[0] + s * u * 0.02, land[1]); c.lineTo(land[0] + s * u * 0.05, land[1] - u * (0.07 - Math.abs(s) * 0.015)); c.stroke(); } }
  return land;
}
function pickup(c, x, y, u, col, nt) {
  c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 4; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2;
  flat(c, [[x - 1.2 * u, y - 0.2 * u], [x - 1.2 * u, y - 0.42 * u], [x - 1.0 * u, y - 0.48 * u], [x - 0.85 * u, y - 0.82 * u], [x - 0.42 * u, y - 0.82 * u], [x - 0.4 * u, y - 0.42 * u], [x + 1.1 * u, y - 0.42 * u], [x + 1.12 * u, y - 0.2 * u]], col);
  c.shadowColor = 'transparent';
  flat(c, [[x - 0.82 * u, y - 0.76 * u], [x - 0.5 * u, y - 0.76 * u], [x - 0.48 * u, y - 0.5 * u], [x - 0.98 * u, y - 0.5 * u]], 'rgba(200,230,255,.75)');
  c.fillStyle = 'rgba(0,0,0,.25)'; c.fillRect(x - 0.4 * u, y - 0.42 * u, 1.5 * u, u * 0.03);
  c.fillStyle = nt ? '#fff6c0' : '#f2f2f2'; c.fillRect(x - 1.22 * u, y - 0.4 * u, u * 0.05, u * 0.06);
  [x - 0.8 * u, x + 0.7 * u].forEach(function (wx) { c.fillStyle = '#1b1a20'; c.beginPath(); c.arc(wx, y - 0.16 * u, 0.17 * u, 0, TAU); c.fill(); c.fillStyle = '#aaa'; c.beginPath(); c.arc(wx, y - 0.16 * u, 0.07 * u, 0, TAU); c.fill(); });
  c.restore();
}
function songkran(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, k, X = function (f) { return S.x0 + S.span * f; };
  var floor = deck + u * 0.36, g = u * 5;
  layer(S, 'sk-back', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#26262e' : '#5e626c');
    q.fillStyle = nt ? 'rgba(255,200,230,.12)' : 'rgba(220,240,255,.35)';
    var r = rnd(S.seed + 9); for (k = 0; k < 9; k++) { q.beginPath(); q.ellipse(S.x0 + r() * S.span, deck + u * (0.12 + r() * 0.5), u * (0.25 + r() * 0.3), u * 0.04, 0, 0, TAU); q.fill(); }
    /* Loi Kroh's shophouses */
    var cols = nt ? ['#5a4a5a', '#4a5a5a', '#5a4a40', '#454a60'] : ['#e8d8b0', '#c9e0d0', '#f0c8b0', '#d0d8f0', '#f2e2a0'];
    for (var x = S.x0 - u * 0.3, j = 0; x < S.x1; x += u * 1.05, j++) {
      var hh = u * (1.55 + (j % 3) * 0.18), x1 = x + u * 1.02, top = deck - hh;
      paper(q, rect(x, top, x1 - x, hh), cols[j % cols.length], 1.2);
      paper(q, rect(x - 3, top - 4, x1 - x + 6, 6), nt ? '#3a3040' : '#9a8a7a', 0.6);
      q.fillStyle = nt ? '#1a1418' : '#4a3a30'; q.fillRect(x + u * 0.1, deck - u * 0.62, u * 0.82, u * 0.62);
      q.fillStyle = nt ? 'rgba(255,190,110,.55)' : 'rgba(255,255,255,.15)'; q.fillRect(x + u * 0.14, deck - u * 0.56, u * 0.74, u * 0.5);
      q.strokeStyle = 'rgba(0,0,0,.25)'; q.lineWidth = 1; for (var sl = 1; sl < 7; sl++) { q.beginPath(); q.moveTo(x + u * 0.1, deck - u * 0.62 + sl * u * 0.04); q.lineTo(x + u * 0.92, deck - u * 0.62 + sl * u * 0.04); q.stroke(); }
      for (var w = 0; w < 2; w++) { var wx = x + u * (0.16 + w * 0.46); q.fillStyle = nt ? '#ffd88a' : '#5d7d93'; q.fillRect(wx, top + u * 0.22, u * 0.3, u * 0.42); q.fillStyle = nt ? '#a85a2a' : '#2f8f5b'; q.fillRect(wx - u * 0.05, top + u * 0.22, u * 0.05, u * 0.42); q.fillRect(wx + u * 0.3, top + u * 0.22, u * 0.05, u * 0.42); }
      q.strokeStyle = nt ? '#c9a07a' : '#6a5a4a'; q.lineWidth = 1.2; q.beginPath(); q.moveTo(x + u * 0.05, top + u * 0.72); q.lineTo(x1 - u * 0.05, top + u * 0.72); for (var b = 0; b < 9; b++) { q.moveTo(x + u * (0.08 + b * 0.1), top + u * 0.72); q.lineTo(x + u * (0.08 + b * 0.1), top + u * 0.82); } q.stroke();
      paper(q, rect(x + u * 0.12, top + u * 0.86, u * 0.78, u * 0.16), nt ? ['#ff4fa0', '#4fd8ff', '#ffd84a'][j % 3] : ['#d94b3b', '#4d8fd1', '#e2b33c', '#2f8f5b'][j % 4], 0.5);
    }
    /* the road sign */
    var sx = X(0.3);
    paper(q, rect(sx - 1.5, deck - u * 1.25, 3, u * 1.3), '#8a8a90', 0.6);
    paper(q, rect(sx - u * 0.42, deck - u * 1.38, u * 0.84, u * 0.28), '#1f4a8a', 0.8);
    q.fillStyle = '#fff'; q.font = '700 ' + Math.round(u * 0.12) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('ถ.ลอยเคราะห์', sx, deck - u * 1.29); q.font = '600 ' + Math.round(u * 0.08) + 'px ' + FONT; q.fillText('Loi Kroh Rd', sx, deck - u * 1.18);
    /* blue barrels at the kerb */
    [X(0.46), X(0.71)].forEach(function (bx) { paper(q, rect(bx - u * 0.13, deck - u * 0.36, u * 0.26, u * 0.38), '#2f6fd0', 0.8); q.fillStyle = 'rgba(255,255,255,.25)'; q.fillRect(bx - u * 0.13, deck - u * 0.26, u * 0.26, 2); q.fillRect(bx - u * 0.13, deck - u * 0.12, u * 0.26, 2); });
  });
  if (nt) for (i = 0; i < 4; i++) bulbs(S, X(i / 4), X((i + 1) / 4), deck - u * 2.05, u * 0.2, 14, [330, 190, 50, 120], true);
  /* the rainbow in the spray, by day */
  if (!nt) { c.save(); var ra = 0.2 + 0.1 * Math.sin(t * 0.8), rx = X(0.6), ry = deck + u * 0.2; c.lineWidth = u * 0.045;
    for (k = 0; k < 6; k++) { c.strokeStyle = 'hsla(' + (k * 52) + ',95%,62%,' + ra + ')'; c.beginPath(); c.arc(rx, ry, u * (1.2 - k * 0.045), Math.PI * 1.05, Math.PI * 1.95); c.stroke(); } c.restore(); }
  /* the pickup and its crew, driving left */
  var Lp = S.span + u * 4.5, tx = S.x1 + u * 1.4 - ((t * u * 0.42 + (S.seed % 97) / 97 * Lp) % Lp), ty = deck + u * 0.12 + Math.abs(Math.sin(t * 7)) * 1.2;
  var crew = town(S, 12, { casual: 1 });
  crew.forEach(function (d, j) { d.col = ['#ff5a8c', '#7fd8ff', '#ffc266', '#7fe0a4', '#b692ff', '#f08a5d', '#4fae8c', '#e5567f'][(j + S.seed) % 8]; d.low = ['#2c2f45', '#1f3a5a', '#5a4a3a', '#2a2a2a'][j % 4]; });
  var bed = ty - u * 0.42;
  var B = fig(S, crew[0], tx + u * 0.15, bed, u * 0.88, { lean: 0, legs: [0.15, 0, -0.15, 0], arms: [1.4, 0.2, 0.3, 0.2] }, 1);
  paper(c, function (p) { p.beginPath(); p.ellipse(tx + u * 0.75, bed - u * 0.42, u * 0.2, u * 0.05, 0, 0, TAU); p.rect(tx + u * 0.55, bed - u * 0.42, u * 0.4, u * 0.42); }, '#2f6fd0', 0.6);
  var p3 = (t + 0.7) % 3.2, sw = p3 < 0.6 ? -ease(p3 / 0.6) : p3 < 0.85 ? -1 + 2.6 * ease((p3 - 0.6) / 0.25) : 1.6 - (p3 - 0.85) * 0.5;
  var T2 = fig(S, crew[1], tx - u * 0.25, bed, u * 0.9, { lean: -0.05 + sw * 0.08, legs: [0.25, 0, -0.2, 0], arms: [0.6 + sw * 1.1, 0.4, 0.4 + sw * 1.1, 0.5] }, 1);
  pickup(c, tx, ty, u, ['#f2f2f2', '#c0392b', '#3a4a6a', '#e8e2d0'][S.seed % 4], nt);
  var hb = [(T2.hand[0][0] + T2.hand[1][0]) / 2, (T2.hand[0][1] + T2.hand[1][1]) / 2];
  paper(c, function (p) { p.beginPath(); p.moveTo(hb[0] - u * 0.08, hb[1] - u * 0.06); p.lineTo(hb[0] + u * 0.08, hb[1] - u * 0.06); p.lineTo(hb[0] + u * 0.06, hb[1] + u * 0.08); p.lineTo(hb[0] - u * 0.06, hb[1] + u * 0.08); p.closePath(); }, '#e8b84a', 0.5);
  clay(c, T2, u, 1); clay(c, B, u, 1); flowerShirt(c, T2, u, 1); flowerShirt(c, B, u, 2);
  /* the bucket's water: each drop flies on its own parabola */
  if (p3 > 0.75) { var a = p3 - 0.75, rr = rnd(31);
    for (k = 0; k < 22; k++) { var th = -0.25 - rr() * 0.9, sp = u * (1.6 + rr() * 1.4), x = hb[0] + Math.cos(th) * sp * a, y = hb[1] - u * 0.06 + Math.sin(th) * sp * a + 0.5 * g * a * a; if (y > floor + u * 0.1) continue;
      c.fillStyle = k % 3 ? 'rgba(170,220,255,.8)' : 'rgba(255,255,255,.9)'; c.beginPath(); c.arc(x, y, u * (0.02 + rr() * 0.025), 0, TAU); c.fill(); } }
  var gunMan = fig(S, crew[2], tx + u * 0.42, bed, u * 0.86, { lean: 0.05, legs: [0.15, 0, -0.1, 0], arms: [1.6, -0.1, 1.4, 0.2] }, 1);
  stream(c, gun(c, gunMan.hand[0], 1, u, '#ff5a8c'), u * 1.8, u * 0.9, g, floor, t, function (b) { return Math.sin(b * 1.7) > -0.2 ? 1 : 0; }, u, 12, 1.4);
  flowerShirt(c, gunMan, u, 3); clay(c, gunMan, u, 1);
  /* sand chedis with their tung, and the elder's blessing */
  [[X(0.04), 0.48], [X(0.1), 0.62], [X(0.155), 0.42]].forEach(function (s, j) {
    var cx = s[0], hh = u * s[1], by = deck + u * 0.2;
    paper(c, poly([[cx - hh * 0.42, by], [cx - hh * 0.1, by - hh * 0.8], [cx, by - hh], [cx + hh * 0.1, by - hh * 0.8], [cx + hh * 0.42, by]]), nt ? '#8a7a5a' : '#d8c49a', 0.8);
    c.fillStyle = 'rgba(255,255,255,.8)'; c.fillRect(cx - hh * 0.3, by - hh * 0.3, hh * 0.6, hh * 0.05); c.fillRect(cx - hh * 0.18, by - hh * 0.6, hh * 0.36, hh * 0.04);
    tungs(c, cx, by - hh * 0.45, hh * 1.1, ['#d9342b', '#f2c94c', '#2f8f5b', '#4d8fd1', '#e5567f'], S.t + j * 300, 3);
  });
  var ex = X(0.215), ey = deck + u * 0.56, el = crew[3]; el.garb = 'mohom'; el.col = '#2c3e6b'; el.low = '#24335a'; el.hairCol = '#e8e8e8'; el.hat = false;
  paper(c, rect(ex - u * 0.16, ey - u * 0.28, u * 0.3, u * 0.05), '#7a4a2a', 0.6);
  var E = fig(S, el, ex, ey, u * 0.9, { lean: 0.05, seat: 0.3, legs: POSE.sit.legs, arms: [1.25, 0.35, 1.15, 0.45] }, 1);
  var yo = crew[4]; yo.garb = 'sin'; yo.low = '#7a1f3a'; yo.sabai = '#e8b84a'; yo.hem = '#e8b84a'; yo.hair = 2;
  var Y = fig(S, yo, ex + u * 0.55, ey, u * 0.92, { lean: 0.25, seat: 0.27, legs: [0.05, -1.55, 0.1, -1.6], arms: [1.5, 0.4, 1.3, 0.6] }, -1);
  var sb = [Y.hand[0][0] - u * 0.04, Y.hand[0][1] - u * 0.02], tip = 0.35 + 0.15 * Math.sin(t * 1.3);
  c.save(); c.translate(sb[0], sb[1]); c.rotate(-tip); paper(c, function (p) { p.beginPath(); p.arc(0, 0, u * 0.09, 0, Math.PI); p.closePath(); }, '#d8dce4', 0.5);
  c.fillStyle = '#ffd84a'; c.beginPath(); c.arc(-u * 0.03, -u * 0.01, u * 0.02, 0, TAU); c.arc(u * 0.03, -u * 0.015, u * 0.02, 0, TAU); c.fill(); c.restore();
  var eh = E.hand[0], lip = [sb[0] - u * 0.09, sb[1] - u * 0.01];
  for (k = 0; k < 8; k++) { var a2 = ((t * 1.6 + k / 8) % 1) * 0.3, dx = lerp(lip[0], eh[0] + u * 0.02, a2 / 0.3), dy = lip[1] + 0.5 * g * a2 * a2 * 0.9; if (dy > eh[1] + u * 0.06) continue; c.fillStyle = 'rgba(190,230,255,.9)'; c.beginPath(); c.arc(dx, dy, u * 0.014, 0, TAU); c.fill(); }
  /* the water fight in the street */
  var fx = [0.38, 0.52, 0.66, 0.8], dirs = [1, -1, 1, -1], gcols = ['#ff9a5a', '#4fd0ff', '#b692ff', '#7fe0a4'];
  for (i = 0; i < 4; i++) {
    var d = crew[5 + i], dir = dirs[i], aim = Math.sin(t * 1.1 + i) * 0.12, yy = deck + u * (0.42 + (i % 2) * 0.1);
    var M = fig(S, d, X(fx[i]), yy, u * (0.94 + (i % 2) * 0.04), { lean: 0.05, legs: [0.25, 0, -0.2, 0], arms: [1.55 + aim, -0.15, 1.35 + aim, 0.25] }, dir);
    flowerShirt(c, M, u, i); clay(c, M, u, dir);
    var mz = gun(c, M.hand[0], dir, u, gcols[i]);
    stream(c, mz, dir * u * (1.3 + 0.25 * (i % 2)), u * (0.95 + aim * 3), g, yy - u * 0.02, t + i * 0.37, function (b) { return Math.sin(b * 1.3 + i * 2) > -0.3 ? 1 : 0; }, u, 14, 1.3);
  }
  /* a kid with a bowl, between them */
  var kd = crew[9], kp = (t * 0.9) % 2.4, kx = X(0.59);
  var KD = fig(S, kd, kx, deck + u * 0.6, u * 0.62, { lean: 0.1, legs: [0.2, 0, -0.2, 0], arms: kp < 1.2 ? [0.4, 0.8, 0.5, 0.8] : [2.2, 0.2, 2.1, 0.3] }, -1);
  clay(c, KD, u * 0.62, -1);
  if (kp > 1.2) for (k = 0; k < 10; k++) { var a3 = kp - 1.2, th3 = -2.0 - k * 0.09, sp3 = u * (1.2 + (k % 4) * 0.25), x3 = KD.hand[0][0] + Math.cos(th3) * sp3 * a3, y3 = KD.hand[0][1] + Math.sin(th3) * sp3 * a3 + 0.5 * g * a3 * a3; if (y3 > floor + u * 0.25) continue; c.fillStyle = 'rgba(170,220,255,.85)'; c.beginPath(); c.arc(x3, y3, u * 0.025, 0, TAU); c.fill(); }
  label(S, X(0.55), deck - u * 1.95, '#2f8fd0');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 1.9, y1: S.H });
}

/* ================================================================ 4. Chinese New Year, Warorot
   The dragon rides a travelling wave, y = A·sin(kx − ωt), each pole-bearer under his own
   piece of it, chasing the pearl; the lion bobs to the drum, |sin ωt|; red lanterns swing
   as pendulums; the firecracker string burns up from its foot. */
function dragonHead(c, x, y, u, dir, t, nt) {
  c.save(); c.translate(x, y); c.scale(dir, 1);
  var jaw = 0.18 + 0.14 * Math.abs(Math.sin(t * 4));
  c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 4; c.shadowOffsetY = 2;
  /* mane, flames of green and orange behind */
  for (var k = 0; k < 5; k++) { var a = 2.2 + k * 0.35; flat(c, [[-u * 0.05, 0], [Math.cos(a) * u * 0.45, Math.sin(a) * u * 0.45 - u * 0.1], [Math.cos(a + 0.2) * u * 0.25, Math.sin(a + 0.2) * u * 0.25]], k % 2 ? '#2f8f5b' : '#f08a2a'); }
  /* horns */
  c.strokeStyle = '#e8b84a'; c.lineWidth = u * 0.04; c.lineCap = 'round';
  c.beginPath(); c.moveTo(-u * 0.05, -u * 0.16); c.quadraticCurveTo(-u * 0.2, -u * 0.38, -u * 0.38, -u * 0.36); c.moveTo(-u * 0.14, -u * 0.27); c.lineTo(-u * 0.12, -u * 0.38); c.stroke();
  /* the upper head and snout */
  flat(c, [[-u * 0.18, -u * 0.18], [u * 0.12, -u * 0.22], [u * 0.36, -u * 0.12], [u * 0.44, -u * 0.04], [u * 0.4, u * 0.02], [-u * 0.12, u * 0.05]], '#d9342b');
  c.shadowColor = 'transparent';
  /* the lower jaw, hinged */
  c.save(); c.translate(-u * 0.08, u * 0.03); c.rotate(jaw);
  flat(c, [[0, 0], [u * 0.44, -u * 0.02], [u * 0.4, u * 0.08], [0, u * 0.1]], '#c0392b');
  c.fillStyle = '#fff'; for (k = 0; k < 4; k++) { c.beginPath(); c.moveTo(u * (0.12 + k * 0.08), 0); c.lineTo(u * (0.15 + k * 0.08), -u * 0.04); c.lineTo(u * (0.18 + k * 0.08), 0); c.fill(); }
  c.fillStyle = '#ffd84a'; c.fillRect(0, u * 0.08, u * 0.4, u * 0.03); c.restore();
  c.fillStyle = '#7a1010'; c.beginPath(); c.moveTo(-u * 0.05, u * 0.04); c.lineTo(u * 0.38, u * 0.02); c.lineTo(u * 0.3, u * 0.08 + jaw * u * 0.2); c.fill();
  c.fillStyle = '#ffd84a'; c.fillRect(-u * 0.14, -u * 0.06, u * 0.5, u * 0.035);
  /* eye and brow */
  c.fillStyle = '#fff'; c.beginPath(); c.ellipse(u * 0.08, -u * 0.12, u * 0.07, u * 0.055, 0, 0, TAU); c.fill();
  c.fillStyle = '#111'; c.beginPath(); c.arc(u * 0.1, -u * 0.12, u * 0.03, 0, TAU); c.fill();
  c.fillStyle = '#2f8f5b'; c.beginPath(); c.moveTo(-u * 0.02, -u * 0.19); c.quadraticCurveTo(u * 0.1, -u * 0.26, u * 0.2, -u * 0.17); c.lineTo(u * 0.08, -u * 0.19); c.fill();
  /* whiskers, waving */
  c.strokeStyle = '#ffd84a'; c.lineWidth = 1.5;
  [0, 1].forEach(function (j) { var w = Math.sin(t * 3 + j) * u * 0.08; c.beginPath(); c.moveTo(u * 0.38, -u * 0.06 + j * u * 0.04); c.quadraticCurveTo(u * 0.6, -u * 0.14 + w, u * 0.75, u * 0.02 + w * 1.5); c.stroke(); });
  c.restore();
}
function lion(S, x, y, u, t, beat, crew) {
  var c = S.c, hit = Math.abs(Math.sin(beat)), rear = { lean: 1.15, legs: [0.25 + 0.1 * Math.sin(beat), -0.3, -0.15 - 0.1 * Math.sin(beat), -0.2], arms: [1.0, 0.2, 0.8, 0.2] };
  crew[0].low = '#f2c94c'; crew[1].low = '#f2c94c';
  var R = fig(S, crew[1], x - u * 0.6, y, u * 0.95, rear, 1);
  var F = fig(S, crew[0], x, y, u * 0.95, { lean: 0.1, legs: [0.3 * Math.sin(beat * 0.5), -0.1, -0.25, -0.1], arms: [2.7, 0.2, 2.6, 0.3] }, 1);
  var hx = x + u * 0.12, hy = F.head[1] - u * (0.12 + 0.12 * hit), hr = u * 0.3;
  /* the body cloth, from behind the head to the tail, fur along its hem */
  var tail = [R.hip[0] - u * 0.2, R.hip[1] - u * 0.05];
  paper(c, function (p) { p.beginPath(); p.moveTo(hx - hr * 0.6, hy - hr * 0.6); p.quadraticCurveTo(R.sh[0], R.sh[1] - u * 0.35, tail[0], tail[1] - u * 0.1); p.lineTo(tail[0] - u * 0.18, tail[1] + u * 0.05 + Math.sin(t * 5) * u * 0.05); p.lineTo(tail[0] + u * 0.02, tail[1] + u * 0.2); p.lineTo(R.hip[0] + u * 0.1, R.hip[1] + u * 0.12); p.lineTo(hx - hr * 0.2, F.hip[1] + u * 0.02); p.closePath(); }, '#d9342b', 1);
  c.fillStyle = '#f2e6c9'; for (var k = 0; k < 9; k++) { var f = k / 8, fx = lerp(R.hip[0] - u * 0.1, hx - hr * 0.2, f), fy = lerp(R.hip[1] + u * 0.12, F.hip[1] + u * 0.02, f); c.beginPath(); c.arc(fx, fy, u * 0.05, 0, TAU); c.fill(); }
  c.fillStyle = '#ffd84a'; for (k = 0; k < 6; k++) { var gx = lerp(tail[0], hx - hr, k / 6 + 0.08), gy = lerp(tail[1], hy - hr * 0.3, k / 6 + 0.08) + u * 0.12; c.beginPath(); c.arc(gx, gy, u * 0.035, 0, TAU); c.fill(); }
  /* the head: fur ring, face, mirror, horn, eyes that blink, the jaw on the beat */
  paper(c, function (p) { p.beginPath(); for (var j = 0; j < 18; j++) { var a = j / 18 * TAU, rr = j % 2 ? hr * 1.18 : hr * 1.02; p.lineTo(hx + Math.cos(a) * rr, hy + Math.sin(a) * rr); } p.closePath(); }, '#f2e6c9', 1.4);
  paper(c, function (p) { circ(p, hx, hy, hr, 7); }, '#e8b84a', 0.6);
  c.fillStyle = '#d9342b'; c.beginPath(); c.arc(hx, hy - hr * 0.15, hr * 0.78, Math.PI, TAU); c.fill();
  c.fillStyle = '#d8e8f0'; c.beginPath(); c.arc(hx + hr * 0.1, hy - hr * 0.62, hr * 0.13, 0, TAU); c.fill();
  c.fillStyle = '#2f8f5b'; c.beginPath(); c.moveTo(hx - hr * 0.05, hy - hr * 0.8); c.lineTo(hx + hr * 0.05, hy - hr * 1.25); c.lineTo(hx + hr * 0.18, hy - hr * 0.8); c.fill();
  var blink = Math.sin(t * 1.3) > 0.95 ? 0.15 : 1;
  [-0.3, 0.35].forEach(function (o) { c.fillStyle = '#fff'; c.beginPath(); c.ellipse(hx + o * hr, hy - hr * 0.2, hr * 0.2, hr * 0.17 * blink, 0, 0, TAU); c.fill(); c.fillStyle = '#111'; c.beginPath(); c.arc(hx + o * hr + hr * 0.05, hy - hr * 0.2, hr * 0.08 * blink, 0, TAU); c.fill(); });
  c.fillStyle = '#2a1a12'; c.beginPath(); c.ellipse(hx + hr * 0.05, hy + hr * 0.12, hr * 0.14, hr * 0.09, 0, 0, TAU); c.fill();
  var jw = hr * (0.08 + 0.3 * Math.pow(hit, 3));
  c.fillStyle = '#7a1010'; c.fillRect(hx - hr * 0.45, hy + hr * 0.3, hr * 0.9, jw);
  c.fillStyle = '#fff'; c.fillRect(hx - hr * 0.45, hy + hr * 0.3, hr * 0.9, hr * 0.06);
  paper(c, function (p) { p.beginPath(); p.moveTo(hx - hr * 0.55, hy + hr * 0.3 + jw); p.lineTo(hx + hr * 0.55, hy + hr * 0.3 + jw); p.lineTo(hx + hr * 0.4, hy + hr * 0.62 + jw); p.lineTo(hx - hr * 0.4, hy + hr * 0.62 + jw); p.closePath(); }, '#e8b84a', 0.6);
  c.fillStyle = '#f2e6c9'; for (k = 0; k < 5; k++) { c.beginPath(); c.arc(hx - hr * 0.4 + k * hr * 0.2, hy + hr * 0.66 + jw, hr * 0.09, 0, TAU); c.fill(); }
}
function cny(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, k, X = function (f) { return S.x0 + S.span * f; };
  var beat = t * Math.PI * 2.1, hit = Math.pow(Math.abs(Math.cos(beat)), 6);
  layer(S, 'cny-back', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#2a1a1a' : '#8a5a4a');
    /* Warorot market: the long hall, its windows, the sign */
    var w0 = X(0.33), w1 = X(0.8), wt = deck - u * 1.55;
    paper(q, rect(w0, wt, w1 - w0, deck - wt), nt ? '#6a5a4a' : '#e2d2a8', 1.6);
    paper(q, poly([[w0 - u * 0.15, wt + u * 0.02], [w0 + u * 0.25, wt - u * 0.35], [w1 - u * 0.25, wt - u * 0.35], [w1 + u * 0.15, wt + u * 0.02]]), nt ? '#3a4a5a' : '#5d7d93', 1.4);
    q.fillStyle = nt ? 'rgba(255,200,120,.6)' : 'rgba(60,40,30,.45)';
    for (var wx = w0 + u * 0.18; wx < w1 - u * 0.2; wx += u * 0.42) { q.beginPath(); q.moveTo(wx, deck - u * 0.05); q.lineTo(wx, wt + u * 0.62); q.arc(wx + u * 0.13, wt + u * 0.62, u * 0.13, Math.PI, 0); q.lineTo(wx + u * 0.26, deck - u * 0.05); q.fill(); }
    paper(q, rect((w0 + w1) / 2 - u * 0.75, wt + u * 0.1, u * 1.5, u * 0.3), '#c0392b', 0.8);
    q.fillStyle = '#ffd84a'; q.font = '800 ' + Math.round(u * 0.2) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('ตลาดวโรรส', (w0 + w1) / 2, wt + u * 0.26);
    /* shophouses with red doors at the right */
    for (var j = 0; j < 2; j++) { var s0 = X(0.81 + j * 0.1), sh = u * (1.45 + j * 0.12); paper(q, rect(s0, deck - sh, S.span * 0.1, sh), nt ? '#5a4040' : ['#f0d8b0', '#e8c8c0'][j], 1.2); q.fillStyle = '#a82020'; q.fillRect(s0 + S.span * 0.02, deck - u * 0.6, S.span * 0.06, u * 0.6); q.fillStyle = nt ? '#ffd88a' : '#5d7d93'; q.fillRect(s0 + S.span * 0.025, deck - sh + u * 0.2, S.span * 0.05, u * 0.35); }
    /* the Chinese gate: red pillars, green tiles, upturned eaves, a gold plaque */
    var g0 = X(0.02), g1 = X(0.3), gm = (g0 + g1) / 2, gt = deck - u * 1.9;
    [g0 + u * 0.12, g1 - u * 0.12].forEach(function (px) { paper(q, rect(px - u * 0.08, gt, u * 0.16, deck - gt), '#b0221a', 1.2); paper(q, rect(px - u * 0.13, deck - u * 0.16, u * 0.26, u * 0.16), '#8a8a90', 0.8); });
    paper(q, rect(g0 + u * 0.1, gt + u * 0.25, g1 - g0 - u * 0.2, u * 0.1), '#b0221a', 1);
    [[gt, 1, g1 - g0 + u * 0.4], [gt - u * 0.45, 0.62, (g1 - g0) * 0.62]].forEach(function (r) {
      var y = r[0], w = r[2];
      paper(q, function (p) { p.beginPath(); p.moveTo(gm - w / 2 - u * 0.12, y - u * 0.16); p.quadraticCurveTo(gm - w / 2, y, gm - w / 2 + u * 0.2, y); p.lineTo(gm + w / 2 - u * 0.2, y); p.quadraticCurveTo(gm + w / 2, y, gm + w / 2 + u * 0.12, y - u * 0.16); p.lineTo(gm + w * 0.38, y - u * 0.22); p.lineTo(gm - w * 0.38, y - u * 0.22); p.closePath(); }, '#2f7f5b', 1.2);
      q.fillStyle = '#e8b84a'; q.fillRect(gm - w * 0.38, y - u * 0.25, w * 0.76, u * 0.04);
    });
    paper(q, rect(gm - (g1 - g0) * 0.26, gt - u * 0.5, (g1 - g0) * 0.52, u * 0.32), '#b0221a', 1);
    q.fillStyle = '#e8b84a'; for (var dk = 0; dk < 5; dk++) q.fillRect(gm - (g1 - g0) * 0.22 + dk * (g1 - g0) * 0.1, gt - u * 0.42, (g1 - g0) * 0.05, u * 0.16);
    paper(q, rect(gm - u * 0.18, gt - u * 0.2, u * 0.36, u * 0.42), '#e8b84a', 0.8);
    q.fillStyle = '#b0221a'; q.font = '800 ' + Math.round(u * 0.26) + 'px serif'; q.fillText('福', gm, gt + 1);
    /* red paper from the crackers, swept to the kerb */
    var r = rnd(S.seed + 3); q.fillStyle = '#d9342b'; for (k = 0; k < 40; k++) q.fillRect(X(0.83) + (r() - 0.5) * u * 0.9, deck + u * (0.05 + r() * 0.5), 3, 2);
  });
  /* lanterns swing on their strings: θ = θ₀·cos(√(g/L)·t) */
  for (i = 0; i < 3; i++) K.strand(c, X(0.04 + i * 0.32), X(0.36 + i * 0.32), deck - u * 2.08, u * 0.24, u * 0.48, function (x, y, j) {
    var L = u * 0.12, th = 0.22 * Math.cos(Math.sqrt(9.8 / 0.35) * t * 0.5 + j + i), lx = x + Math.sin(th) * L, ly = y + Math.cos(th) * L;
    c.strokeStyle = 'rgba(40,20,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x, y); c.lineTo(lx, ly); c.stroke();
    if (nt) lanternGlow(c, lx, ly + u * 0.1, u * 0.09, 5, 0.9);
    c.fillStyle = '#d9241b'; c.beginPath(); c.ellipse(lx, ly + u * 0.1, u * 0.11, u * 0.09, 0, 0, TAU); c.fill();
    c.fillStyle = '#e8b84a'; c.fillRect(lx - u * 0.05, ly, u * 0.1, u * 0.025); c.fillRect(lx - u * 0.05, ly + u * 0.18, u * 0.1, u * 0.025); c.fillRect(lx - 1, ly + u * 0.2, 2, u * 0.1);
  });
  var crew = town(S, 18, { casual: 1 });
  crew.forEach(function (d, j) { d.col = j < 10 ? '#f2c94c' : ['#d9342b', '#c0392b', '#e5567f', '#b0221a'][j % 4]; d.low = j < 10 ? '#c0392b' : d.low; d.hat = false; });
  /* the dragon, travelling right; poles from each bearer to his piece of the wave */
  var A = u * 0.26, kw = TAU / (u * 3), om = 3.2, yb = deck - u * 1.32, sp = u * 0.62, N = S.phone ? 6 : 7, Ld = sp * (N + 1.5), Lp = S.span + Ld + u * 2;
  var hx = S.x0 - u + ((t * u * 0.55 + (S.seed % 61) / 61 * Lp) % Lp);
  function wy(x) { return yb - A * Math.sin(kw * x - om * t); }
  var bearers = [];
  for (i = 0; i < N; i++) { var bx = hx - (i + 0.8) * sp; bearers.push(bx); }
  bearers.forEach(function (bx, j) { if (bx < S.x0 - u || bx > S.x1 + u) return; var P = walkP(t * TAU * 0.9 + j * 0.8, false); P.arms = [2.9, 0.1, 2.75, 0.2]; var M = fig(S, crew[j], bx, deck + u * 0.12, u * 0.9, P, 1); c.strokeStyle = '#7a4a2a'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(M.hand[0][0], M.hand[0][1] + u * 0.1); c.lineTo(bx, wy(bx)); c.stroke(); });
  var pearlx = hx + u * 0.95, M0 = fig(S, crew[N], pearlx, deck + u * 0.12, u * 0.9, (function () { var P = walkP(t * TAU * 0.9, false); P.arms = [2.6, 0.2, 0.4, 0.3]; return P; })(), 1);
  var ppy = wy(pearlx) - u * 0.15 + Math.sin(t * 5) * u * 0.06;
  c.strokeStyle = '#7a4a2a'; c.lineWidth = 2; c.beginPath(); c.moveTo(M0.hand[0][0], M0.hand[0][1]); c.lineTo(pearlx + u * 0.1, ppy); c.stroke();
  lanternGlow(c, pearlx + u * 0.1, ppy, u * 0.1, 45, nt ? 1 : 0.5);
  paper(c, function (p) { circ(p, pearlx + u * 0.1, ppy, u * 0.1, 3); }, '#ffd84a', 0.6);
  c.strokeStyle = '#d9342b'; c.lineWidth = 1.5; c.beginPath(); c.arc(pearlx + u * 0.1, ppy, u * 0.07, t * 4, t * 4 + 3); c.stroke();
  /* the body: a red tube with a gold belly, green fins along its back */
  var pts = []; for (var x = hx - Ld; x <= hx - u * 0.05; x += u * 0.08) pts.push([x, wy(x)]);
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round'; c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 4; c.shadowOffsetY = 2;
  c.strokeStyle = '#c0221a'; c.lineWidth = u * 0.3; c.beginPath(); pts.forEach(function (p, j) { j ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); c.shadowColor = 'transparent';
  c.strokeStyle = '#ffd84a'; c.lineWidth = u * 0.09; c.beginPath(); pts.forEach(function (p, j) { j ? c.lineTo(p[0], p[1] + u * 0.09) : c.moveTo(p[0], p[1] + u * 0.09); }); c.stroke();
  for (k = 2; k < pts.length - 1; k += 2) { var p0 = pts[k], p1 = pts[k + 1], nx = p1[1] - p0[1], ny = -(p1[0] - p0[0]), nl = Math.hypot(nx, ny) || 1; nx /= nl; ny /= nl;
    flat(c, [[p0[0] + nx * u * 0.12, p0[1] + ny * u * 0.12], [p0[0] + nx * u * 0.27 - u * 0.03, p0[1] + ny * u * 0.27], [p1[0] + nx * u * 0.12, p1[1] + ny * u * 0.12]], k % 4 ? '#2f8f5b' : '#7fe0a4');
    c.strokeStyle = 'rgba(255,216,74,.7)'; c.lineWidth = 1.2; c.beginPath(); c.arc(p0[0], p0[1] - u * 0.02, u * 0.06, 0.2, Math.PI - 0.2); c.stroke(); }
  var tp = pts[0]; flat(c, [[tp[0] + u * 0.05, tp[1] - u * 0.1], [tp[0] - u * 0.35, tp[1] - u * 0.3 + Math.sin(t * 4) * u * 0.1], [tp[0] - u * 0.18, tp[1]], [tp[0] - u * 0.35, tp[1] + u * 0.2 + Math.sin(t * 4) * u * 0.1], [tp[0] + u * 0.05, tp[1] + u * 0.1]], '#2f8f5b');
  c.restore();
  dragonHead(c, hx, wy(hx), u, 1, t, nt);
  /* the drum and the cymbals */
  var dx = X(0.07), dy = deck + u * 0.5;
  paper(c, rect(dx - u * 0.3, dy - u * 0.12, u * 0.6, u * 0.06), '#5a3a1a', 0.8);
  c.fillStyle = '#1b1a20'; [dx - u * 0.22, dx + u * 0.22].forEach(function (wx) { c.beginPath(); c.arc(wx, dy - u * 0.04, u * 0.08, 0, TAU); c.fill(); });
  paper(c, function (p) { p.beginPath(); p.ellipse(dx, dy - u * 0.38, u * 0.28, u * 0.26 * (1 + hit * 0.03), 0, 0, TAU); }, '#b0221a', 1);
  c.fillStyle = '#f2e6c9'; c.beginPath(); c.ellipse(dx, dy - u * 0.62, u * 0.27, u * 0.06, 0, 0, TAU); c.fill();
  c.fillStyle = '#e8b84a'; for (k = 0; k < 7; k++) { c.beginPath(); c.arc(dx - u * 0.24 + k * u * 0.08, dy - u * 0.56, 1.6, 0, TAU); c.fill(); }
  var dm = crew[11]; dm.col = '#d9342b';
  var DR = fig(S, dm, dx + u * 0.42, dy + u * 0.02, u * 0.95, { lean: 0.15, legs: [0.15, 0, -0.15, 0], arms: [2.2 - hit * 0.9, 0.5, 1.4 + hit * 0.9, 0.6] }, -1);
  c.strokeStyle = '#d9b36a'; c.lineWidth = 2; [0, 1].forEach(function (j) { var h = DR.hand[j]; c.beginPath(); c.moveTo(h[0], h[1]); c.lineTo(h[0] - u * 0.18, h[1] + u * 0.06); c.stroke(); });
  var cy = crew[12]; cy.col = '#f2c94c';
  var CY = fig(S, cy, X(0.36), deck + u * 0.55, u * 0.92, { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [1.6 + (1 - hit) * 0.5, 0.2, 1.6 - (1 - hit) * 0.5, 0.2] }, -1);
  [0, 1].forEach(function (j) { var h = CY.hand[j]; c.fillStyle = '#e8c860'; c.beginPath(); c.ellipse(h[0] - u * 0.02, h[1], u * 0.025, u * 0.12, 0, 0, TAU); c.fill(); });
  if (hit > 0.8) { c.strokeStyle = 'rgba(255,240,180,.8)'; c.lineWidth = 1.2; for (k = 0; k < 6; k++) { var a = k / 6 * TAU; c.beginPath(); c.moveTo((CY.hand[0][0] + CY.hand[1][0]) / 2 + Math.cos(a) * u * 0.16, CY.hand[0][1] + Math.sin(a) * u * 0.16); c.lineTo((CY.hand[0][0] + CY.hand[1][0]) / 2 + Math.cos(a) * u * 0.26, CY.hand[0][1] + Math.sin(a) * u * 0.26); c.stroke(); } }
  /* the lion */
  lion(S, X(0.25), deck + u * 0.6, u, t, beat, [crew[13], crew[14]]);
  /* onlookers in red, one with a phone */
  [[0.6, 1], [0.69, -1]].forEach(function (o, j) { var W = fig(S, crew[15 + j], X(o[0]), deck + u * 0.58, u * (0.93 + j * 0.05), { lean: 0, legs: [0.06, 0, -0.06, 0], arms: j ? [2.3, -0.7, 0.2, 0.1] : [0.3, 0.3, 0.6, 1.2] }, o[1]); if (j) phone(c, W.hand[0], u, '#bfe0ff'); });
  /* the firecracker string burns up from its foot; flash, sparks, smoke, red paper */
  var px = X(0.86), top = deck - u * 2.0, Lc = u * 1.6, burn = (t % 6) / 6, bot = top + Lc * (1 - burn * 0.92);
  paper(c, rect(px - 2, top - u * 0.05, 4, deck + u * 0.3 - top), '#c9b27a', 0.8); c.fillStyle = '#c9b27a'; c.fillRect(px - u * 0.35, top - u * 0.05, u * 0.35, 3);
  var sx = px - u * 0.32; c.strokeStyle = '#7a1010'; c.lineWidth = 1; c.beginPath(); c.moveTo(sx, top); c.lineTo(sx, bot); c.stroke();
  for (var cy2 = top + u * 0.05; cy2 < bot; cy2 += u * 0.06) { c.fillStyle = '#d9241b'; c.save(); c.translate(sx, cy2); c.rotate(0.8); c.fillRect(-u * 0.08, -u * 0.015, u * 0.07, u * 0.03); c.rotate(-1.6); c.fillRect(u * 0.01, -u * 0.015, u * 0.07, u * 0.03); c.restore(); }
  var tick = Math.floor(t * 14), rr = rnd(tick * 7 + 3);
  c.save(); c.globalCompositeOperation = 'lighter';
  for (k = 0; k < 3; k++) { var fx = sx + (rr() - 0.5) * u * 0.3, fy = bot + (rr() - 0.3) * u * 0.25, fr = u * (0.06 + rr() * 0.08);
    var fg = c.createRadialGradient(fx, fy, 0, fx, fy, fr * 2); fg.addColorStop(0, 'rgba(255,250,210,.95)'); fg.addColorStop(1, 'rgba(255,160,40,0)'); c.fillStyle = fg; c.beginPath(); c.arc(fx, fy, fr * 2, 0, TAU); c.fill();
    c.strokeStyle = 'rgba(255,220,120,.9)'; c.lineWidth = 1; for (var s2 = 0; s2 < 5; s2++) { var a2 = rr() * TAU; c.beginPath(); c.moveTo(fx + Math.cos(a2) * fr, fy + Math.sin(a2) * fr); c.lineTo(fx + Math.cos(a2) * fr * 2.2, fy + Math.sin(a2) * fr * 2.2); c.stroke(); } }
  c.restore();
  for (k = 0; k < 5; k++) { var sa = ((t * 0.5 + k / 5) % 1), smx = sx + Math.sin(sa * 5 + k) * u * 0.15, smy = Math.max(deck - u * 2.1, bot - sa * u * 1.1); c.fillStyle = 'rgba(220,220,225,' + (0.35 * (1 - sa)) + ')'; c.beginPath(); c.arc(smx, smy, u * (0.08 + sa * 0.15), 0, TAU); c.fill(); }
  for (k = 0; k < 14; k++) { var fa = ((t * 0.6 + k / 14) % 1), bx2 = sx + Math.sin(k * 2.3) * u * 0.5 + Math.sin(t * 3 + k) * u * 0.06, by2 = lerp(bot, deck + u * 0.5, fa); c.fillStyle = k % 3 ? '#d9241b' : '#ffd84a'; c.save(); c.translate(bx2, by2); c.rotate(t * 5 + k); c.fillRect(-2, -1.5, 4 * Math.abs(Math.cos(t * 6 + k)) + 1, 3); c.restore(); }
  label(S, X(0.5), deck - u * 2.5, '#b0221a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2, y1: S.H });
}

/* ================================================================ 5. Yi Peng and Loi Krathong
   On the Ping: krathong drift with their candles, khom loi are held till they fill and
   then let go, y = y₀ − vt, x = a·sin ωt; the Iron Bridge strung with lanterns, a wat lit
   up across the water; fireworks burst, r = v·τ, y += ½gτ². */
function krathong(c, x, y, s, t, k, nt) {
  if (nt) { var rg = c.createRadialGradient(x, y + s * 0.3, 0, x, y + s * 0.3, s * 1.6); rg.addColorStop(0, 'rgba(255,200,100,.45)'); rg.addColorStop(1, 'rgba(255,200,100,0)'); c.fillStyle = rg; c.beginPath(); c.ellipse(x, y + s * 0.3, s * 1.6, s * 0.6, 0, 0, TAU); c.fill(); }
  c.fillStyle = '#c9d8a0'; c.beginPath(); c.ellipse(x, y, s * 0.62, s * 0.16, 0, 0, TAU); c.fill();
  for (var j = 0; j < 7; j++) { var lx = x - s * 0.55 + j * s * 0.18; c.fillStyle = j % 2 ? '#2f7f3b' : '#3f9a4a'; c.beginPath(); c.moveTo(lx - s * 0.1, y); c.lineTo(lx, y - s * 0.32); c.lineTo(lx + s * 0.1, y); c.fill(); }
  ['#f6a92c', '#f2f2f2', '#e5567f', '#ffd84a'].forEach(function (col, j) { c.fillStyle = col; c.beginPath(); c.arc(x - s * 0.24 + j * s * 0.16, y - s * 0.3, s * 0.1, 0, TAU); c.fill(); });
  c.fillStyle = '#f5ead2'; c.fillRect(x - s * 0.03, y - s * 0.72, s * 0.06, s * 0.38);
  c.strokeStyle = '#8a3a1a'; c.lineWidth = 1; c.beginPath(); c.moveTo(x + s * 0.12, y - s * 0.35); c.lineTo(x + s * 0.18, y - s * 0.66); c.moveTo(x + s * 0.17, y - s * 0.35); c.lineTo(x + s * 0.24, y - s * 0.64); c.stroke();
  var fl = 1 + 0.2 * Math.sin(t / 90 + k * 2);
  lanternGlow(c, x, y - s * 0.8, s * 0.12, 42, 0.9);
  c.fillStyle = '#ffcf5a'; c.beginPath(); c.moveTo(x, y - s * (0.82 + 0.2 * fl)); c.quadraticCurveTo(x + s * 0.07, y - s * 0.76, x, y - s * 0.72); c.quadraticCurveTo(x - s * 0.07, y - s * 0.76, x, y - s * (0.82 + 0.2 * fl)); c.fill();
}
function skyLantern(c, x, y, s, lit, t, k) {
  if (lit > 0) { var g = c.createRadialGradient(x, y, 0, x, y, s * 3); g.addColorStop(0, 'rgba(255,190,90,' + 0.55 * lit + ')'); g.addColorStop(1, 'rgba(255,150,60,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, s * 3, 0, TAU); c.fill(); }
  var gb = c.createLinearGradient(x, y - s, x, y + s); gb.addColorStop(0, lit > 0 ? '#ffe9b0' : '#fbf6ea'); gb.addColorStop(1, lit > 0 ? '#ff9a3a' : '#efe3c4');
  c.fillStyle = gb; c.beginPath(); c.moveTo(x - s * 0.55, y + s * 0.8); c.lineTo(x - s * 0.72, y - s * 0.5); c.quadraticCurveTo(x, y - s * 1.3, x + s * 0.72, y - s * 0.5); c.lineTo(x + s * 0.55, y + s * 0.8); c.closePath(); c.fill();
  if (lit > 0) { c.fillStyle = '#fff6c0'; c.beginPath(); c.arc(x, y + s * 0.85, s * 0.18 * (0.85 + 0.15 * Math.sin(t / 100 + k)), 0, TAU); c.fill(); }
}
function yipeng(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, k, X = function (f) { return S.x0 + S.span * f; };
  var r0 = deck - u * 0.72, r1 = deck + u * 0.2;
  /* fireworks over the city, left of the clock */
  if (nt) for (i = 0; i < 3; i++) { var P = 3.6, a = (t + i * 1.25) % P, cyc = Math.floor((t + i * 1.25) / P), rr = rnd(cyc * 13 + i * 7 + 1);
    firework(c, X(0.1 + 0.42 * rr()), deck - u * (S.phone ? 3.6 + rr() * 1.4 : 2.9 + rr() * 0.6), u * (0.5 + rr() * 0.3), a, Math.floor(rr() * 6) * 55, 18); }
  layer(S, 'yp-back', 0, S.H, function (q) {
    /* the far bank and the wat across the water */
    paper(q, rect(S.x0 - 4, r0 - u * 0.12, S.span + 8, u * 0.14), nt ? '#1d2a24' : '#4f7d4a', 1);
    var wx = X(0.12);
    paper(q, rect(wx - u * 0.6, r0 - u * 0.62, u * 1.2, u * 0.52), nt ? '#d8c8a0' : '#f2ead8', 1);
    q.fillStyle = nt ? '#ffcf70' : '#8a5a3a'; for (k = 0; k < 4; k++) q.fillRect(wx - u * 0.48 + k * u * 0.27, r0 - u * 0.48, u * 0.12, u * 0.22);
    lannaRoof(q, wx, r0 - u * 0.6, u * 1.5, u * 0.95, nt ? '#7a2a22' : '#a8402f', 3);
    var cx2 = X(0.3);
    paper(q, function (p) { p.beginPath(); p.moveTo(cx2 - u * 0.4, r0 - u * 0.1); p.lineTo(cx2 - u * 0.36, r0 - u * 0.35); p.lineTo(cx2 - u * 0.26, r0 - u * 0.35); p.quadraticCurveTo(cx2 - u * 0.26, r0 - u * 0.9, cx2 - u * 0.05, r0 - u * 1.15); p.lineTo(cx2, r0 - u * 1.85); p.lineTo(cx2 + u * 0.05, r0 - u * 1.15); p.quadraticCurveTo(cx2 + u * 0.26, r0 - u * 0.9, cx2 + u * 0.26, r0 - u * 0.35); p.lineTo(cx2 + u * 0.36, r0 - u * 0.35); p.lineTo(cx2 + u * 0.4, r0 - u * 0.1); p.closePath(); }, nt ? '#e0b048' : '#e8c25a', 1.2);
    /* the Iron Bridge */
    var b0 = X(0.4), b1 = X(1.02), bt = r0 - u * 0.85, bd = r0 - u * 0.25, iron = nt ? '#3c4b5e' : '#56708c';
    q.save(); q.shadowColor = 'rgba(0,0,0,.4)'; q.shadowBlur = 4; q.shadowOffsetY = 2; q.strokeStyle = iron; q.lineWidth = Math.max(1.5, u * 0.045); q.lineCap = 'round';
    q.beginPath(); q.moveTo(b0, bd); q.lineTo(b1, bd); q.moveTo(b0 + u * 0.2, bt); q.lineTo(b1, bt);
    var nb = 12; for (k = 0; k <= nb; k++) { var bx = b0 + u * 0.2 + k * (b1 - b0 - u * 0.2) / nb; q.moveTo(bx, bd); q.lineTo(bx, bt); if (k < nb) { q.moveTo(bx, bd); q.lineTo(bx + (b1 - b0) / nb, bt); } }
    q.moveTo(b0, bd); q.lineTo(b0 + u * 0.2, bt); q.stroke();
    [0.3, 0.7].forEach(function (f) { var px = lerp(b0, b1, f); q.fillStyle = nt ? '#4a4a55' : '#9a9aa5'; q.fillRect(px - u * 0.08, bd, u * 0.16, r1 - bd); });
    q.restore();
    /* the river */
    paper(q, rect(S.x0 - 4, r0, S.span + 8, r1 - r0), nt ? '#14254a' : '#4b8fc9', 1);
    q.strokeStyle = nt ? 'rgba(160,190,255,.25)' : 'rgba(255,255,255,.35)'; q.lineWidth = 1; var rr2 = rnd(S.seed + 2);
    for (k = 0; k < 24; k++) { var yy = lerp(r0 + 4, r1 - 4, rr2()), xx = S.x0 + rr2() * S.span, w = u * (0.15 + rr2() * 0.3); q.beginPath(); q.moveTo(xx, yy); q.quadraticCurveTo(xx + w / 2, yy - 2, xx + w, yy); q.stroke(); }
    /* the near bank: stone steps down to the water */
    paper(q, rect(S.x0 - 4, r1, S.span + 8, S.H - r1 + 4), nt ? '#3a3540' : '#a89a8a', 1.6);
    q.strokeStyle = 'rgba(0,0,0,.2)'; for (k = 1; k < 4; k++) { q.beginPath(); q.moveTo(S.x0, r1 + k * u * 0.12); q.lineTo(S.x1, r1 + k * u * 0.12); q.stroke(); }
  });
  /* lanterns along the bridge and the wat's eaves, their light on the water */
  var b0 = X(0.4), b1 = X(1.02), bt = r0 - u * 0.85;
  for (k = 0; k < 13; k++) { var lx = lerp(b0 + u * 0.3, b1 - u * 0.1, k / 12), on = nt ? 0.7 + 0.3 * Math.sin(t * 2 + k) : 0;
    if (nt) { lanternGlow(c, lx, bt + u * 0.08, u * 0.06, 40, on); c.fillStyle = 'rgba(255,200,100,' + 0.25 * on + ')'; c.fillRect(lx - 1.5 + Math.sin(t * 3 + k) * 2, r0 + 4, 3, (r1 - r0) * 0.7); }
    c.fillStyle = nt ? '#ffd27a' : '#f2c94c'; c.beginPath(); c.moveTo(lx, bt); c.lineTo(lx + u * 0.05, bt + u * 0.08); c.lineTo(lx, bt + u * 0.16); c.lineTo(lx - u * 0.05, bt + u * 0.08); c.closePath(); c.fill(); }
  var wx = X(0.12); for (k = 0; k < 6; k++) { var ex = wx - u * 0.62 + k * u * 0.25, ey = r0 - u * 0.5; if (nt) lanternGlow(c, ex, ey, u * 0.05, 45, 0.8 + 0.2 * Math.sin(t * 3 + k)); c.fillStyle = nt ? '#ffe08a' : '#f2c94c'; c.fillRect(ex - u * 0.03, ey - u * 0.04, u * 0.06, u * 0.08); }
  /* krathong drift down the Ping */
  var nk = S.phone ? 4 : 6;
  for (k = 0; k < nk; k++) { var z = (k % 3) / 2, Lk = S.span + u * 1.6, kx = S.x0 - u * 0.8 + ((k / nk * Lk + t * u * (0.08 + 0.03 * z)) % Lk), ky = lerp(r0 + u * 0.25, r1 - u * 0.05, z) + Math.sin(t * 1.4 + k) * u * 0.02;
    krathong(c, kx, ky, u * (0.28 + 0.1 * z), S.t, k, true); }
  /* people on the steps: two pairs with khom loi, one setting a krathong down, a sparkler */
  var crew = town(S, 8), bank = deck + u * 0.55;
  [[0.2, 0], [0.5, 4.3]].forEach(function (pr, j) {
    var px = X(pr[0]), T = 11, p = (t + pr[1]) % T, cyc = Math.floor((t + pr[1]) / T), held = !nt || p < 6.5, fill = nt ? Math.min(1, p / 5) : 0;
    var up = { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.75, 0.15, 2.6, 0.2] }, wave = { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.9 + 0.2 * Math.sin(t * 6), 0, 0.2, 0.1] };
    var A1 = fig(S, crew[j * 2], px - u * 0.22, bank, u * 0.94, held ? up : wave, 1);
    var A2 = fig(S, crew[j * 2 + 1], px + u * 0.22, bank + u * 0.04, u * 0.9, held ? up : { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [0.3, 0.2, 0.4, 1.4] }, -1);
    var hy = Math.min(A1.hand[0][1], A2.hand[0][1]);
    if (held) skyLantern(c, px, hy - u * 0.3 + Math.sin(t * 2 + j) * 2, u * 0.26, fill, S.t, j);
    if (nt) for (var m = 0; m < 3; m++) { var tau = p - 6.5 + m * T; if (tau < 0 || tau > 26) continue; var rr3 = rnd(cyc - m + j * 99);
      var ly = hy - u * 0.3 - u * 0.22 * tau - u * 0.004 * tau * tau, lx2 = px + Math.sin(tau * 0.6 + rr3() * 6) * u * 0.35; if (ly < -u) continue;
      skyLantern(c, lx2, ly, u * 0.26 * Math.max(0.35, 1 - tau / 30), Math.min(1, (ly + u) / (u * 2)), S.t, j + m); }
  });
  var kn = crew[4]; kn.garb = 'sin'; kn.low = '#5a2a6a'; kn.sabai = '#f2c94c'; kn.hair = 2;
  var KN = fig(S, kn, X(0.72), bank, u * 0.92, { lean: 0.55, seat: 0.27, legs: [0.05, -1.55, 0.1, -1.6], arms: [1.0, 0.4, 0.9, 0.5] }, -1);
  krathong(c, KN.hand[0][0] - u * 0.06, KN.hand[0][1] + u * 0.02, u * 0.24, S.t, 9, nt);
  var sp = crew[5], SP = fig(S, sp, X(0.85), bank + u * 0.05, u * 0.66, { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [2.2 + 0.4 * Math.sin(t * 3), 0.2, 0.2, 0.2] }, -1);
  var st = [SP.hand[0][0] - u * 0.04, SP.hand[0][1] - u * 0.18];
  c.strokeStyle = '#888'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(SP.hand[0][0], SP.hand[0][1]); c.lineTo(st[0], st[1]); c.stroke();
  if (nt) { c.save(); c.globalCompositeOperation = 'lighter'; var rr4 = rnd(Math.floor(t * 20)); lanternGlow(c, st[0], st[1], u * 0.06, 50, 1);
    c.strokeStyle = 'rgba(255,230,150,.9)'; c.lineWidth = 1; for (k = 0; k < 10; k++) { var a2 = rr4() * TAU, l = u * (0.06 + rr4() * 0.14); c.beginPath(); c.moveTo(st[0], st[1]); c.lineTo(st[0] + Math.cos(a2) * l, st[1] + Math.sin(a2) * l); c.stroke(); } c.restore(); }
  label(S, X(0.62), deck - u * 2.05, nt ? '#d9832a' : '#e2b33c');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2, y1: S.H });
}

/* ================================================================ 6. the Flower Festival
   A parade down the road: the marching band in step, floats of marigolds and
   chrysanthemums, the Flower Queen waving from the first. Each flower head is set by
   phyllotaxis, r = c·√n, θ = n·137.5°; petals drift down. */
function bloom(q, x, y, R, n, a, b) {
  for (var k = n; k > 0; k--) { var r = R * Math.sqrt(k / n), th = k * 2.39996; q.fillStyle = k > n * 0.35 ? a : b; q.beginPath(); q.arc(x + Math.cos(th) * r, y + Math.sin(th) * r, R * 0.16, 0, TAU); q.fill(); }
}
var FLOWERS = [['#f6a92c', '#c8650c'], ['#ffd84a', '#d99a1a'], ['#f2f2f2', '#e8d870'], ['#e5567f', '#a8204a'], ['#b692ff', '#6a3ab0'], ['#ff8a5a', '#d0401a']];
function floatSprite(S, kind, w, h, u) {
  return sprite(S, 'fl-float' + kind, w, h, function (q) {
    var base = h - u * 0.12, top = base - u * 0.8, r = rnd(S.seed + kind * 17), m = u * 0.12;
    paper(q, function (p) { p.beginPath(); p.moveTo(m, base); p.lineTo(m + u * 0.1, top); p.lineTo(w - m - u * 0.1, top); p.lineTo(w - m, base); p.closePath(); }, '#3f7a3a', 1.6);
    var band = kind ? [FLOWERS[3], FLOWERS[2], FLOWERS[4], FLOWERS[1], FLOWERS[3], FLOWERS[0]] : [FLOWERS[1], FLOWERS[0], FLOWERS[2], FLOWERS[0], FLOWERS[1], FLOWERS[5]];
    for (var y = top + u * 0.08, row = 0; y < base; y += u * 0.12, row++) for (var x = m + u * 0.12 + (row % 2) * u * 0.06; x < w - m - u * 0.05; x += u * 0.12) { var f = band[row % band.length]; bloom(q, x + (r() - 0.5) * 2, y, u * 0.075, 14, f[0], f[1]); }
    q.strokeStyle = '#2f7f3b'; q.lineWidth = 2; for (x = m + u * 0.1; x < w - m - u * 0.3; x += u * 0.42) { q.beginPath(); q.moveTo(x, top + u * 0.05); q.quadraticCurveTo(x + u * 0.21, top + u * 0.3, x + u * 0.42, top + u * 0.05); q.stroke(); }
    q.fillStyle = '#e8b84a'; q.fillRect(m + u * 0.08, top - 2, w - m * 2 - u * 0.16, u * 0.05);
    if (!kind) {   /* an elephant of white and pink chrysanthemums */
      var ex = w * 0.62, ey = top, ew = u * 1.2, eh = u * 0.85;
      paper(q, function (p) { p.beginPath(); p.ellipse(ex, ey - eh * 0.5, ew * 0.5, eh * 0.38, 0, 0, TAU); p.moveTo(ex + ew * 0.62, ey - eh * 0.62); p.arc(ex + ew * 0.45, ey - eh * 0.66, eh * 0.24, 0, TAU);
        p.moveTo(ex + ew * 0.62, ey - eh * 0.6); p.quadraticCurveTo(ex + ew * 0.8, ey - eh * 0.3, ex + ew * 0.7, ey - eh * 0.05); p.lineTo(ex + ew * 0.62, ey - eh * 0.08); p.quadraticCurveTo(ex + ew * 0.68, ey - eh * 0.3, ex + ew * 0.55, ey - eh * 0.5); p.closePath();
        [-0.32, -0.1, 0.14, 0.32].forEach(function (lx) { p.rect(ex + lx * ew - ew * 0.07, ey - eh * 0.3, ew * 0.14, eh * 0.3); }); }, '#f2e6f0', 1.2);
      for (var k = 0; k < 40; k++) { var a = r() * TAU, rr = Math.sqrt(r()); bloom(q, ex + Math.cos(a) * rr * ew * 0.42, ey - eh * 0.5 + Math.sin(a) * rr * eh * 0.3, u * 0.05, 8, k % 3 ? '#ffffff' : '#ffb6d0', '#f0d0a0'); }
      paper(q, function (p) { p.beginPath(); p.ellipse(ex + ew * 0.32, ey - eh * 0.6, ew * 0.14, eh * 0.22, 0.2, 0, TAU); }, '#ffb6d0', 0.6);
      q.fillStyle = '#c0392b'; q.fillRect(ex - ew * 0.25, ey - eh * 0.88, ew * 0.4, eh * 0.06); q.fillStyle = '#e8b84a'; q.fillRect(ex - ew * 0.25, ey - eh * 0.82, ew * 0.4, eh * 0.15);
      q.fillStyle = '#2a1a12'; q.beginPath(); q.arc(ex + ew * 0.52, ey - eh * 0.72, u * 0.025, 0, TAU); q.fill();
    } else {   /* a khan dok: the stemmed offering bowl with its cone of marigolds */
      var kx = w * 0.6, ky = top, kh = u * 1.05;
      paper(q, poly([[kx - u * 0.18, ky], [kx - u * 0.08, ky - kh * 0.22], [kx + u * 0.08, ky - kh * 0.22], [kx + u * 0.18, ky]]), '#e8b84a', 1);
      paper(q, function (p) { p.beginPath(); p.moveTo(kx - u * 0.5, ky - kh * 0.22); p.quadraticCurveTo(kx, ky - kh * 0.02, kx + u * 0.5, ky - kh * 0.22); p.lineTo(kx + u * 0.45, ky - kh * 0.32); p.lineTo(kx - u * 0.45, ky - kh * 0.32); p.closePath(); }, '#d9a63a', 1);
      paper(q, poly([[kx - u * 0.42, ky - kh * 0.32], [kx, ky - kh * 1.08], [kx + u * 0.42, ky - kh * 0.32]]), '#f6a92c', 1.2);
      for (k = 0; k < 9; k++) { var f2 = k / 9, rw = u * 0.4 * (1 - f2); for (var j = -2; j <= 2; j++) bloom(q, kx + j * rw * 0.42, ky - kh * (0.36 + f2 * 0.68), u * 0.05 * (1 - f2 * 0.4), 8, k % 2 ? '#ffd84a' : '#f6a92c', '#c8650c'); }
      [-1, 1].forEach(function (s) { for (k = 0; k < 4; k++) bloom(q, kx + s * u * (0.68 + k * 0.05), ky - u * (0.12 + k * 0.18), u * 0.09, 14, '#e5567f', '#a8204a'); });
    }
  });
}
function flowers(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, k, X = function (f) { return S.x0 + S.span * f; };
  layer(S, 'fl-back', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#2a2a30' : '#8a8478');
    q.fillStyle = nt ? 'rgba(255,255,255,.2)' : 'rgba(255,255,255,.6)'; for (var x = S.x0; x < S.x1; x += u * 0.6) q.fillRect(x, deck + u * 0.4, u * 0.3, 2);
    /* the beds along the road and an arch of flowers */
    paper(q, rect(S.x0 - 4, deck - u * 0.22, S.span + 8, u * 0.24), nt ? '#1f3326' : '#4f8a4a', 1);
    var r = rnd(S.seed + 4); for (x = S.x0 + 4; x < S.x1; x += u * 0.11) { var f = FLOWERS[Math.floor(r() * 6)]; bloom(q, x, deck - u * (0.15 + r() * 0.1), u * 0.055, 10, f[0], f[1]); }
    var a0 = X(0.06), a1 = X(0.3), am = (a0 + a1) / 2, aw = (a1 - a0) / 2, ah = u * 1.7;
    for (k = 0; k <= 44; k++) { var th = Math.PI * k / 44, ax = am - Math.cos(th) * aw, ay = deck - u * 0.1 - Math.sin(th) * ah; var f3 = FLOWERS[k % 6]; bloom(q, ax, ay, u * 0.1, 16, f3[0], f3[1]); }
    paper(q, rect(am - u * 0.62, deck - ah - u * 0.32, u * 1.24, u * 0.3), '#2f7f3b', 1);
    q.fillStyle = '#ffd84a'; q.font = '800 ' + Math.round(u * 0.15) + 'px ' + FONT; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText('เทศกาลไม้ดอก', am, deck - ah - u * 0.17);
  });
  /* the parade, moving left; offsets along it in u */
  var v = u * 0.3, fw = u * 2.7, fh = u * 2.15;
  var Lp = Math.max(S.span + u * 3.2, u * 11.6), base = t * v + (S.seed % 89) / 89 * Lp;
  function at(o) { return S.x1 + u * 1.5 - ((base + o * u) % Lp); }
  var crew = town(S, 12, { sin: 1 }), step = t * TAU * 0.95;
  /* the khan dok float, girls with garlands, the elephant float with the queen, the band */
  var f2x = at(0), sp2 = floatSprite(S, 1, fw, fh, u); stamp(c, sp2, f2x - fw / 2, deck + u * 0.18 - fh, fw, fh);
  var pr = crew[0]; pr.sabai = '#ffd84a'; fig(S, pr, f2x - fw * 0.25, deck + u * 0.18 - u * 0.92, u * 0.78, { lean: 0, seat: 0.24, legs: POSE.sit.legs, arms: [0.5, 1.2, 2.6 + 0.3 * Math.sin(t * 3), 0.2] }, -1);
  [1.95, 2.55].forEach(function (o, j) { var gx = at(o), d = crew[1 + j]; var M = fig(S, d, gx, deck + u * 0.2, u * 0.92, walkP(step + j * Math.PI, false), -1);
    c.strokeStyle = j ? '#f2f2f2' : '#f6a92c'; c.lineWidth = 3; c.beginPath(); c.arc(M.sh[0], M.sh[1] + u * 0.03, u * 0.07, 0.2, Math.PI - 0.2); c.stroke();
    paper(c, function (p) { p.beginPath(); p.arc(M.hand[0][0], M.hand[0][1], u * 0.09, 0, Math.PI); p.closePath(); }, '#d9a63a', 0.4); bloom(c, M.hand[0][0], M.hand[0][1] - u * 0.02, u * 0.06, 8, '#e5567f', '#a8204a'); });
  /* the elephant float is cut facing right; mirrored here so its head leads the parade left */
  var f1x = at(4.6), sp1 = floatSprite(S, 0, fw, fh, u); c.save(); c.translate(f1x, 0); c.scale(-1, 1); stamp(c, sp1, -fw / 2, deck + u * 0.18 - fh, fw, fh); c.restore();
  var qn = crew[3]; qn.sabai = '#e8b84a'; qn.low = '#7a1f3a'; qn.hem = '#e8b84a';
  var Q = fig(S, qn, f1x + fw * 0.28, deck + u * 0.18 - u * 0.92, u * 0.92, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [0.3, 0.3, 2.6 + 0.35 * Math.sin(t * 3.2), 0.3 * Math.sin(t * 3.2)] }, -1);
  c.fillStyle = '#ffd84a'; c.beginPath(); c.moveTo(Q.head[0] - u * 0.08, Q.head[1] - u * 0.08); c.lineTo(Q.head[0] - u * 0.05, Q.head[1] - u * 0.2); c.lineTo(Q.head[0], Q.head[1] - u * 0.12); c.lineTo(Q.head[0] + u * 0.05, Q.head[1] - u * 0.2); c.lineTo(Q.head[0] + u * 0.08, Q.head[1] - u * 0.08); c.fill();
  c.strokeStyle = '#ffd1e8'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(Q.sh[0] + u * 0.06, Q.sh[1]); c.lineTo(Q.hip[0] - u * 0.06, Q.hip[1]); c.stroke();
  /* the band in step: drum major, drums, a trumpet */
  var band = [6.8, 7.4, 8.0, 8.6];
  band.forEach(function (o, j) {
    var bx = at(o), d = crew[4 + j]; d.garb = 'casual'; d.col = j ? '#c0392b' : '#f2f2f2'; d.low = '#1f2a4a'; d.long = 1; d.hat = false;
    var P = walkP(step, false);
    if (j === 0) P.arms = [2.8, 0.1, -0.2, 0.3]; else if (j < 3) { var hs = Math.pow(Math.abs(Math.sin(step)), 4); P.arms = [1.1 + hs * 0.6, 0.9, 1.1 + (1 - hs) * 0.6, 0.9]; } else P.arms = [1.45, 0.5, 1.4, 0.6];
    var M = fig(S, d, bx, deck + u * 0.24, u * 0.95, P, -1);
    c.fillStyle = '#1f2a4a'; c.fillRect(M.head[0] - u * 0.075, M.head[1] - u * 0.26, u * 0.15, u * 0.2); c.fillStyle = '#ffd84a'; c.fillRect(M.head[0] - u * 0.08, M.head[1] - u * 0.09, u * 0.16, u * 0.03);
    c.fillStyle = j ? '#f2f2f2' : '#e5567f'; c.beginPath(); c.ellipse(M.head[0], M.head[1] - u * 0.3, u * 0.03, u * 0.07, 0, 0, TAU); c.fill();
    if (j === 0) { var ba = t * 5, h = M.hand[0]; c.strokeStyle = '#e8e2d0'; c.lineWidth = 2; c.beginPath(); c.moveTo(h[0] - Math.cos(ba) * u * 0.18, h[1] - Math.sin(ba) * u * 0.18); c.lineTo(h[0] + Math.cos(ba) * u * 0.18, h[1] + Math.sin(ba) * u * 0.18); c.stroke(); c.fillStyle = '#ffd84a'; c.beginPath(); c.arc(h[0] + Math.cos(ba) * u * 0.18, h[1] + Math.sin(ba) * u * 0.18, 2.5, 0, TAU); c.fill(); }
    else if (j < 3) { paper(c, rect(M.hip[0] - u * 0.18, M.hip[1] - u * 0.06, u * 0.2, u * 0.13), '#f2f2f2', 0.5); c.fillStyle = '#c0392b'; c.fillRect(M.hip[0] - u * 0.18, M.hip[1] - u * 0.06, u * 0.2, u * 0.025); }
    else { var h2 = M.hand[0]; c.fillStyle = '#e8c860'; c.fillRect(h2[0] - u * 0.22, h2[1] - u * 0.02, u * 0.24, u * 0.03); c.beginPath(); c.moveTo(h2[0] - u * 0.22, h2[1] - u * 0.005); c.lineTo(h2[0] - u * 0.32, h2[1] - u * 0.07); c.lineTo(h2[0] - u * 0.32, h2[1] + u * 0.06); c.fill(); }
  });
  K.notes(c, at(8.6) - u * 0.4, deck - u * 0.8, S.t, 3, nt ? '#ffe2a0' : '#7a3a8a');
  /* petals drift down: x = x₀ + a·sin ωt */
  var rr = rnd(S.seed + 8);
  for (k = 0; k < (S.phone ? 12 : 20); k++) { var px = S.x0 + rr() * S.span, sp = 0.3 + rr() * 0.3, yy = ((t * sp * u + rr() * (deck + u)) % (deck + u * 0.6)) - u * 0.2, xx = px + Math.sin(t * 1.3 + k) * u * 0.3, rot = t * 3 + k, col = FLOWERS[k % 6][0];
    if (xx > S.x1 - S.span * 0.24 && yy < deck - u * 2.3) continue;
    c.fillStyle = col; c.beginPath(); c.ellipse(xx, yy, u * 0.04 * Math.abs(Math.cos(rot)) + 1, u * 0.025, rot * 0.3, 0, TAU); c.fill(); }
  /* pots of marigolds and chrysanthemums along the kerb, in front */
  layer(S, 'fl-front', deck + u * 0.2, S.H, function (q) {
    var r2 = rnd(S.seed + 6);
    for (var x = S.x0 + u * 0.2; x < S.x1; x += u * 0.42) { var py = S.H - u * 0.02, f = FLOWERS[Math.floor(r2() * 6)];
      paper(q, poly([[x - u * 0.1, py - u * 0.16], [x + u * 0.1, py - u * 0.16], [x + u * 0.07, py], [x - u * 0.07, py]]), '#b5652a', 0.6);
      bloom(q, x - u * 0.06, py - u * 0.22, u * 0.07, 12, f[0], f[1]); bloom(q, x + u * 0.06, py - u * 0.24, u * 0.07, 12, f[0], f[1]); bloom(q, x, py - u * 0.3, u * 0.075, 12, f[0], f[1]); }
  });
  label(S, X(0.62), deck - u * 2.05, '#e5567f');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2, y1: S.H });
}

/* ================================================================ 7. Bo Sang's umbrellas
   Saa-paper umbrellas dry in rows; a painter puts a flower on one petal by petal; another
   opens and shuts hers, each rib at x = R·sin α, y = R·cos α; the bicycle parade rolls
   by under open umbrellas, wheels turning φ = x/r. */
var UCOL = ['#e04a3a', '#f2c94c', '#2f8f5b', '#4d8fd1', '#e5567f', '#9b6bd6', '#f08a2a', '#f2f2f2'];
function canopy(c, top, R, al, col, u) {   /* side-on, ribs at ±α from the shaft */
  var lx = top[0] - R * Math.sin(al), rx = top[0] + R * Math.sin(al), y = top[1] + R * Math.cos(al);
  paper(c, function (p) { p.beginPath(); p.moveTo(lx, y); p.quadraticCurveTo(top[0] - R * Math.sin(al) * 0.6, top[1] - R * 0.15 * Math.sin(al), top[0], top[1] - 2); p.quadraticCurveTo(top[0] + R * Math.sin(al) * 0.6, top[1] - R * 0.15 * Math.sin(al), rx, y);
    var n = 6; for (var k = n; k > 0; k--) { var x0 = lerp(lx, rx, k / n), x1 = lerp(lx, rx, (k - 1) / n); p.quadraticCurveTo((x0 + x1) / 2, y - R * 0.06 * Math.sin(al), x1, y); } p.closePath(); }, col, 0.8);
  c.strokeStyle = 'rgba(80,40,10,.35)'; c.lineWidth = 0.8; for (var k = -2; k <= 2; k++) { c.beginPath(); c.moveTo(top[0], top[1]); c.lineTo(top[0] + k / 2 * R * Math.sin(al), y); c.stroke(); }
  if (al > 0.6) { c.fillStyle = 'rgba(255,245,220,.85)'; [-0.45, 0.1, 0.55].forEach(function (f) { c.beginPath(); c.arc(top[0] + f * R * Math.sin(al), top[1] + R * Math.cos(al) * 0.6 + Math.abs(f) * R * 0.1, u * 0.03, 0, TAU); c.fill(); }); }
}
function frontUmbrella(q, x, y, R, col, n) {   /* face-on: the painted disc and its ribs */
  paper(q, function (p) { p.beginPath(); for (var j = 0; j < 24; j++) { var a = j / 24 * TAU, rr = j % 2 ? R : R * 0.95; p.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } p.closePath(); }, col, 1);
  q.strokeStyle = 'rgba(80,40,10,.3)'; q.lineWidth = 0.8; for (var k = 0; k < n; k++) { var a = k / n * TAU; q.beginPath(); q.moveTo(x, y); q.lineTo(x + Math.cos(a) * R, y + Math.sin(a) * R); q.stroke(); }
  q.strokeStyle = 'rgba(80,40,10,.25)'; q.beginPath(); q.arc(x, y, R * 0.25, 0, TAU); q.stroke();
}
function petal(c, x, y, a, s, col) { c.fillStyle = col; c.beginPath(); c.ellipse(x + Math.cos(a) * s, y + Math.sin(a) * s, s, s * 0.55, a, 0, TAU); c.fill(); }
function bicycle(c, x, y, u, phi, col) {
  var r = u * 0.2, w0 = [x - u * 0.33, y - r], w1 = [x + u * 0.33, y - r];
  c.strokeStyle = '#2a2a30'; c.lineWidth = 1.6;
  [w0, w1].forEach(function (w) { c.beginPath(); c.arc(w[0], w[1], r, 0, TAU); c.stroke(); c.lineWidth = 0.7; for (var k = 0; k < 6; k++) { var a = phi + k * Math.PI / 6; c.beginPath(); c.moveTo(w[0] - Math.cos(a) * r, w[1] - Math.sin(a) * r); c.lineTo(w[0] + Math.cos(a) * r, w[1] + Math.sin(a) * r); c.stroke(); } c.lineWidth = 1.6; });
  var cr = [x, y - r], seat = [x + u * 0.06, y - u * 0.55], bar = [x - u * 0.24, y - u * 0.6];
  c.strokeStyle = col; c.lineWidth = 2.2; c.beginPath(); c.moveTo(w1[0], w1[1]); c.lineTo(cr[0], cr[1]); c.lineTo(seat[0], seat[1] + u * 0.04); c.lineTo(w1[0], w1[1]); c.moveTo(cr[0], cr[1]); c.lineTo(bar[0] + u * 0.04, bar[1] + u * 0.1); c.lineTo(seat[0], seat[1] + u * 0.08); c.moveTo(w0[0], w0[1]); c.lineTo(bar[0], bar[1]); c.stroke();
  c.fillStyle = '#2a2a30'; c.fillRect(seat[0] - u * 0.06, seat[1], u * 0.12, u * 0.035);
  c.strokeStyle = '#2a2a30'; c.beginPath(); c.moveTo(bar[0], bar[1]); c.lineTo(bar[0] + u * 0.08, bar[1] - u * 0.02); c.stroke();
  paper(c, function (p) { p.beginPath(); p.moveTo(w0[0] - u * 0.05, bar[1] + u * 0.12); p.lineTo(w0[0] + u * 0.12, bar[1] + u * 0.12); p.lineTo(w0[0] + u * 0.09, bar[1] + u * 0.26); p.lineTo(w0[0] - u * 0.03, bar[1] + u * 0.26); p.closePath(); }, '#c9a66b', 0.4);
  return { seat: seat, bar: bar, crank: cr };
}
function umbrella(S) {
  var c = S.c, u = S.hh, t = S.t / 1000, nt = S.night, deck = S.deck, i, k, X = function (f) { return S.x0 + S.span * f; };
  layer(S, 'bs-back', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, deck, S.H, nt ? '#2a2018' : '#b89a6a');
    /* the workshop: a Lanna house, umbrellas hung under its eaves */
    var h0 = X(0.0), h1 = X(0.28), hm = (h0 + h1) / 2;
    paper(q, rect(h0, deck - u * 1.25, h1 - h0, u * 1.25), nt ? '#4a2e1c' : '#8a5a34', 1.4);
    q.strokeStyle = 'rgba(40,20,10,.35)'; q.lineWidth = 1; for (var y = deck - u * 1.2; y < deck; y += u * 0.1) { q.beginPath(); q.moveTo(h0, y); q.lineTo(h1, y); q.stroke(); }
    q.fillStyle = nt ? '#ffcf70' : '#2a1a10'; q.fillRect(hm - u * 0.3, deck - u * 0.95, u * 0.6, u * 0.5);
    lannaRoof(q, hm, deck - u * 1.2, h1 - h0 + u * 0.3, u * 1.0, nt ? '#5a2a1a' : '#7a3a22', 2);
    for (k = 0; k < 5; k++) { var ux = h0 + (h1 - h0) * (0.12 + k * 0.19), uy = deck - u * 1.12; q.strokeStyle = '#5a3a1a'; q.lineWidth = 1; q.beginPath(); q.moveTo(ux, uy); q.lineTo(ux, uy + u * 0.12); q.stroke();
      paper(q, function (p) { p.beginPath(); p.moveTo(ux, uy + u * 0.1); p.quadraticCurveTo(ux - u * 0.2, uy + u * 0.14, ux - u * 0.2, uy + u * 0.24); p.lineTo(ux + u * 0.2, uy + u * 0.24); p.quadraticCurveTo(ux + u * 0.2, uy + u * 0.14, ux, uy + u * 0.1); p.closePath(); }, UCOL[(k + S.seed) % UCOL.length], 0.6); }
    /* saa paper drying on its frames */
    for (k = 0; k < 4; k++) { var fx = X(0.31 + k * 0.045), fy = deck - u * 0.85; q.save(); q.translate(fx, deck); q.rotate(-0.12);
      paper(q, rect(0, -u * 0.85, u * 0.36, u * 0.85), nt ? '#8a7a5a' : '#6a4a2a', 0.8); paper(q, rect(u * 0.03, -u * 0.82, u * 0.3, u * 0.79), nt ? '#c8c0a8' : '#f6f0e0', 0.4);
      q.strokeStyle = 'rgba(160,140,100,.35)'; var rf = rnd(k + 40); for (var j = 0; j < 8; j++) { q.beginPath(); q.moveTo(u * 0.05 + rf() * u * 0.25, -u * (0.1 + rf() * 0.7)); q.lineTo(u * 0.05 + rf() * u * 0.25, -u * (0.1 + rf() * 0.7)); q.stroke(); } q.restore(); }
    /* rows of umbrellas drying, open, on the ground */
    var r = rnd(S.seed + 12);
    [[deck - u * 0.12, 0.3, 0.54], [deck + u * 0.04, 0.36, 0.52]].forEach(function (row, ri) {
      for (var x = X(row[2]) + ri * u * 0.2; x < S.x1 - u * 0.1; x += u * row[1] * 2.1) { var R = u * row[1], col = UCOL[Math.floor(r() * UCOL.length)];
        q.strokeStyle = '#5a3a1a'; q.lineWidth = 1.2; q.beginPath(); q.moveTo(x, row[0] - R * 0.5); q.lineTo(x + R * 0.3, row[0]); q.stroke();
        paper(q, function (p) { p.beginPath(); p.ellipse(x, row[0] - R * 0.55, R, R * 0.62, -0.25, Math.PI * 1.02, Math.PI * 2.02); p.closePath(); }, col, 0.8);
        q.strokeStyle = 'rgba(80,40,10,.3)'; q.lineWidth = 0.7; for (var j = 1; j < 6; j++) { var a = Math.PI + j / 6 * Math.PI; q.beginPath(); q.moveTo(x, row[0] - R * 0.55 - R * 0.62 * 0.95); q.lineTo(x + Math.cos(a - 0.25) * R, row[0] - R * 0.55 + Math.sin(a - 0.25) * R * 0.62); q.stroke(); }
        q.fillStyle = 'rgba(255,245,220,.8)'; q.beginPath(); q.arc(x - R * 0.3, row[0] - R * 0.85, R * 0.1, 0, TAU); q.arc(x + R * 0.25, row[0] - R * 0.95, R * 0.08, 0, TAU); q.fill(); }
    });
  });
  if (nt) for (i = 0; i < 3; i++) bulbs(S, X(0.28 + i * 0.24), X(0.52 + i * 0.24), deck - u * 1.95, u * 0.2, 16, [42, 30, 50], true);
  /* the painter: a flower goes on, petal by petal */
  var crew = town(S, 8, { sin: 0.6, mohom: 0.25, casual: 0.15 }), ux = X(0.36), uy = deck - u * 0.5, UR = u * 0.4, cyc = 16, p = (t % cyc) / cyc * 5, done = Math.floor(p);
  paper(c, rect(ux - 2, uy, 4, deck + u * 0.4 - uy), '#5a3a1a', 0.6);
  paper(c, poly([[ux - u * 0.2, deck + u * 0.42], [ux, deck + u * 0.28], [ux + u * 0.2, deck + u * 0.42]]), '#5a3a1a', 0.6);
  stamp(c, sprite(S, 'bs-disc', UR * 2 + 12, UR * 2 + 12, function (q) { frontUmbrella(q, UR + 6, UR + 6, UR, UCOL[(S.seed >>> 4) % 6], 20); }), ux - UR - 6, uy - UR - 6, UR * 2 + 12, UR * 2 + 12);
  var spots = [[-0.45, -0.35], [0.4, -0.4], [0.05, 0.45], [-0.5, 0.3], [0.55, 0.2]], pc = ['#fff4d0', '#ffd1e8', '#ffffff', '#ffe08a', '#c3f0d0'], brush = null;
  for (k = 0; k <= Math.min(done, 4); k++) { var sx = ux + spots[k][0] * UR, sy = uy + spots[k][1] * UR, np = k < done ? 5 : Math.floor((p % 1) * 6);
    for (var j = 0; j < np; j++) petal(c, sx, sy, j / 5 * TAU - 1.57, u * 0.05, pc[k]);
    if (np > 0) { c.fillStyle = '#e8a020'; c.beginPath(); c.arc(sx, sy, u * 0.025, 0, TAU); c.fill(); }
    if (k === done) brush = [sx + Math.cos(np / 5 * TAU - 1.57) * u * 0.08, sy + Math.sin(np / 5 * TAU - 1.57) * u * 0.08]; }
  var pd = crew[0], px = ux - u * 0.62, py = deck + u * 0.4, ph = u * 0.92, lean = 0.12, hip = [px, py - ph * 0.27], sh = [hip[0] + Math.sin(lean) * ph * 0.33, hip[1] - Math.cos(lean) * ph * 0.33];
  var A = brush ? reach(sh, [brush[0] - u * 0.06, brush[1] + u * 0.03], ph * 0.17, ph * 0.16, 1, -1) : [0.9, 0.6];
  paper(c, rect(px - u * 0.14, py - ph * 0.27, u * 0.26, u * 0.05), '#7a4a2a', 0.5);
  var PD = fig(S, pd, px, py, ph, { lean: lean, seat: 0.27, legs: POSE.sit.legs, arms: [A[0], A[1], 0.9, 0.9] }, 1);
  c.strokeStyle = '#3b2a14'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(PD.hand[0][0], PD.hand[0][1]); c.lineTo(PD.hand[0][0] + u * 0.07, PD.hand[0][1] - u * 0.03); c.stroke();
  paper(c, rect(px - u * 0.3, py - u * 0.08, u * 0.18, u * 0.08), '#f2f2f2', 0.4); ['#e04a3a', '#ffd84a', '#4d8fd1'].forEach(function (col, j) { c.fillStyle = col; c.beginPath(); c.arc(px - u * 0.26 + j * u * 0.05, py - u * 0.08, u * 0.018, 0, TAU); c.fill(); });
  /* she opens and shuts hers: α eases between shut and open */
  var oc = (t % 5) / 5, al = 0.08 + 1.12 * (oc < 0.3 ? ease(oc / 0.3) : oc < 0.6 ? 1 : oc < 0.9 ? 1 - ease((oc - 0.6) / 0.3) : 0);
  var od = crew[1], O = fig(S, od, X(0.56), deck + u * 0.3, u * 0.94, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.75, 0.2, 0.3, 0.2] }, -1);
  var otop = [O.hand[0][0], O.hand[0][1] - u * 0.42];
  c.strokeStyle = '#5a3a1a'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(O.hand[0][0], O.hand[0][1] + u * 0.06); c.lineTo(otop[0], otop[1]); c.stroke();
  canopy(c, otop, u * 0.48, al, UCOL[(S.seed + 3) % UCOL.length], u);
  /* the bicycle parade, rolling left */
  var nb = 3, Lp = S.span + u * 3, sp = u * 0.62;
  for (i = 0; i < nb; i++) {
    var bx = S.x1 + u * 1.2 - ((t * sp + i * Lp / nb + (S.seed % 53) / 53 * Lp) % Lp), by = deck + u * 0.62, ph2 = bx / (u * 0.2), d = crew[2 + i];
    d.garb = 'sin'; d.hair = 2; d.low = ['#7a1f3a', '#2a3a6a', '#1f5a4a'][i]; d.sabai = UCOL[(i + 1) % 6];
    /* the bicycle is cut basket-first to the left, the way it rolls; the rider is posed facing right and mirrored onto it */
    var B0 = bicycle(c, bx, by, u, ph2, ['#c0392b', '#2f8f5b', '#4d8fd1'][i]), B = { seat: [2 * bx - B0.seat[0], B0.seat[1]], bar: [2 * bx - B0.bar[0], B0.bar[1]], crank: B0.crank };
    c.save(); c.translate(bx, 0); c.scale(-1, 1); c.translate(-bx, 0);
    var crank = -ph2, h = u * 0.9, hipP = [B.seat[0], B.seat[1] - u * 0.02], seat = (by - hipP[1]) / h, shP = [hipP[0] + Math.sin(0.15) * h * 0.33, hipP[1] - Math.cos(0.15) * h * 0.33];
    var p1 = [B.crank[0] + Math.cos(crank) * u * 0.08, B.crank[1] + Math.sin(crank) * u * 0.08], p2 = [B.crank[0] - Math.cos(crank) * u * 0.08, B.crank[1] - Math.sin(crank) * u * 0.08];
    var L1 = reach(hipP, p1, h * 0.24, h * 0.23, 1, 1), L2 = reach(hipP, p2, h * 0.24, h * 0.23, 1, 1), AR = reach(shP, B.bar, h * 0.17, h * 0.16, 1, -1);
    var R2 = fig(S, d, hipP[0], by, h, { lean: 0.15, seat: seat, legs: [L1[0], L1[1], L2[0], L2[1]], arms: [AR[0], AR[1], 2.85, 0.1] }, 1);
    c.restore();
    var hand = [2 * bx - R2.hand[1][0], R2.hand[1][1]], top2 = [hand[0], hand[1] - u * 0.4];
    c.strokeStyle = '#5a3a1a'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(hand[0], hand[1] + u * 0.05); c.lineTo(top2[0], top2[1]); c.stroke();
    canopy(c, top2, u * 0.46, 1.05 + 0.04 * Math.sin(t * 2 + i), UCOL[(i * 3 + S.seed) % UCOL.length], u);
  }
  label(S, X(0.66), deck - u * 2.0, '#d9832a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: deck - u * 2, y1: S.H });
}

/* the words that call each scene, ahead of the engine's own; the first to match wins */
D.addScene('songkran', songkran, /songkran|สงกรานต์|loi ?kroh water|water festival|ปี๋ใหม่เมือง|ปีใหม่เมือง/i,
  'y = v₀t − ½gt²<br>the water arcs', 1);
D.addScene('cny', cny, /^(?![\s\S]*(lisu|hmong|lahu|ลีซู|ม้ง|ลาหู่))[\s\S]*(chinese new year|lunar new year|ตรุษจีน|spring festival.*(chin|warorot)|dragon dance|lion dance|เชิดสิงโต)/i,
  'y = A·sin(kx − ωt)<br>the dragon', 2);
D.addScene('yipeng', yipeng, /yi ?peng|yee ?peng|ยี่เป็ง|lo[iy] ?krathong|ลอยกระทง|(?<!chinese )lantern festival/i,
  'y = y₀ − vt, x = a·sin ωt<br>the khom loi', 3);
D.addScene('umbrella', umbrella, /bo ?sang|bor ?sang|บ่อสร้าง|umbrella festival/i,
  'x = R·sin α, y = R·cos α<br>the ribs open', 4);
D.versions['umbrella'] = 2;   /* v2: the parade bicycles lead with the basket, the way they roll */
D.addScene('flowers', flowers, /flower festival|flower parade|มหกรรมไม้ดอก|ไม้ดอกไม้ประดับ|เทศกาลดอกไม้/i,
  'r = c·√n, θ = n·137.5°<br>each flower head', 5);
D.versions['flowers'] = 2;   /* v2: the elephant float's head leads the parade */
D.addScene('clocktower', clocktower, /clock ?tower|หอนาฬิกา|light (and |& )?sound show.*chiang ?rai|light show.*chiang ?rai/i,
  'hue = 360·(y/λ − t/T)<br>x = R·cos ωt, the roundabout', 6);
D.addScene('walking-street', walkingStreet, /walking street|ถนนคนเดิน|sunday market|wua ?lai|วัวลาย|saturday (night )?market/i,
  'y = a·cosh(x/a), the lights<br>x = x₀ ± vt, the crowd', 7);
})();
