/* Robots and tuk-tuks for the auto-doodler (doodler.js). Nan, 2026-10-02: "some for robotics",
   "some for tuktuks". Robots are paper cut in Lanna colours with gold lai kham trim; tuk-tuks and
   red songthaews go round the old city, Warorot, a parade, a wedding and a nap in the shade.
   Still parts are cut once into offscreen layers and sprites; what moves is drawn off S.t. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU;
var person = K.person, POSE = K.POSE, walkP = K.walkP, town = K.town, CLOTH = K.CLOTH, lanternGlow = K.lanternGlow;
var FONT = '"Sarabun",system-ui,sans-serif', GOLD = '#e8b84a';

/* ---------------------------------------------------------------- cut once, drawn every frame */
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
  var m = mat(S.c), k = m ? Math.abs(m.a) : 1, key = name + '|' + Math.round(w) + '|' + Math.round(h) + '|' + k + '|' + +S.night;
  if (SPR[key]) return SPR[key];
  if (typeof document === 'undefined') return null;
  if (++nspr > 90) { SPR = {}; nspr = 1; }
  var o = document.createElement('canvas'); o.width = Math.max(1, Math.ceil(w * k)); o.height = Math.max(1, Math.ceil(h * k));
  var q = o.getContext('2d'); q.setTransform(k, 0, 0, k, 0, 0); draw(q);
  return (SPR[key] = o);
}
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',95%,62%,1)'); g.addColorStop(0.45, 'hsla(' + h + ',95%,60%,.4)'); g.addColorStop(1, 'hsla(' + h + ',95%,60%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o || a <= 0) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
function label(S, cx, y, col) {
  if (!S.label) return;
  var c = S.c; c.font = '800 ' + Math.round(Math.max(12, S.hh * 0.2)) + 'px ' + FONT;
  var bh = Math.max(20, S.hh * 0.32), half = c.measureText(S.label).width / 2 + 10 + bh * 0.6 + 4;
  cx = half * 2 > S.span ? S.x0 + S.span / 2 : Math.max(S.x0 + half, Math.min(S.x1 - half, cx));
  K.banner(c, cx, y, S.label, S.hh, col, S.seed, S.hits);
}
function X(S, f) { return S.x0 + S.span * f; }
function rr(q, x, y, w, h, r) { r = Math.min(r, w / 2, h / 2); q.moveTo(x + r, y); q.arcTo(x + w, y, x + w, y + h, r); q.arcTo(x + w, y + h, x, y + h, r); q.arcTo(x, y + h, x, y, r); q.arcTo(x, y, x + w, y, r); q.closePath(); }
function rrect(x, y, w, h, r) { return function (q) { q.beginPath(); rr(q, x, y, w, h, r); }; }
function hex(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; }
function mixc(a, b, u) { var A = hex(a), B = hex(b); return 'rgb(' + A.map(function (v, i) { return Math.round(lerp(v, B[i], u)); }).join(',') + ')'; }
function blob(c, x, y, rx, ry, col) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.fill(); }
function line(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }

/* lai kham, the gold stencil on Lanna lacquer: four-petal flowers between dots along a band */
function laiKham(q, x0, x1, y, s, col) {
  q.fillStyle = col || GOLD;
  for (var x = x0 + s; x < x1 - s * 0.4; x += s * 2) {
    for (var k = 0; k < 4; k++) { var a = k * TAU / 4 + TAU / 8; q.beginPath(); q.ellipse(x + Math.cos(a) * s * 0.3, y + Math.sin(a) * s * 0.3, s * 0.3, s * 0.13, a, 0, TAU); q.fill(); }
    if (x + s < x1 - s * 0.4) { q.beginPath(); q.arc(x + s, y, s * 0.13, 0, TAU); q.fill(); }
  }
}
/* the rose r = cos 4θ, eight petals: the gold flower of a lacquer panel */
function rose(q, x, y, R, col) {
  q.fillStyle = col || GOLD; q.beginPath();
  for (var a = 0; a <= TAU + 0.01; a += 0.04) { var r = R * Math.abs(Math.cos(4 * a)); a ? q.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r) : q.moveTo(x + r, y); }
  q.fill(); q.beginPath(); q.arc(x, y, R * 0.16, 0, TAU); q.fill();
}
/* kalae, the crossed horns of a northern gable */
function kalae(q, x, y, s, col) {
  q.save(); q.strokeStyle = col || GOLD; q.lineWidth = Math.max(1.2, s * 0.22); q.lineCap = 'round';
  q.beginPath(); q.moveTo(x, y); q.quadraticCurveTo(x - s * 0.25, y - s * 0.7, x - s * 0.8, y - s * 1.0); q.moveTo(x, y); q.quadraticCurveTo(x + s * 0.25, y - s * 0.7, x + s * 0.8, y - s * 1.0); q.stroke(); q.restore();
}
/* a wheel turned through θ = x / r: tyre, rim, five spokes */
function wheel(c, x, y, r, th, rim) {
  c.fillStyle = '#16141a'; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
  c.fillStyle = rim || '#c9ccd4'; c.beginPath(); c.arc(x, y, r * 0.58, 0, TAU); c.fill();
  c.strokeStyle = '#4a4650'; c.lineWidth = Math.max(1, r * 0.12);
  c.beginPath(); for (var k = 0; k < 5; k++) { var a = th + k * TAU / 5; c.moveTo(x, y); c.lineTo(x + Math.cos(a) * r * 0.55, y + Math.sin(a) * r * 0.55); } c.stroke();
  c.fillStyle = GOLD; c.beginPath(); c.arc(x, y, r * 0.16, 0, TAU); c.fill();
}
/* the elbow of a two-link arm from a to b, bent to side k */
function elbowOf(a, b, l1, l2, k) {
  var dx = b[0] - a[0], dy = b[1] - a[1], d0 = Math.hypot(dx, dy) || 1, d = Math.min(d0, (l1 + l2) * 0.999), ux = dx / d0, uy = dy / d0;
  var x = (l1 * l1 - l2 * l2 + d * d) / (2 * d), h = Math.sqrt(Math.max(0, l1 * l1 - x * x));
  return [a[0] + ux * x - uy * h * k, a[1] + uy * x + ux * h * k];
}
/* long gold fon lep nails fanned from a hand, curling back: bend b */
function nails(c, p, ang, len, b) {
  c.save(); c.strokeStyle = '#ffd36a'; c.lineWidth = Math.max(1, len * 0.12); c.lineCap = 'round';
  for (var k = 0; k < 4; k++) {
    var a = ang + (k - 1.5) * 0.22, ex = p[0] + Math.cos(a) * len, ey = p[1] + Math.sin(a) * len, cx = p[0] + Math.cos(a) * len * 0.6 + Math.cos(a - Math.PI / 2) * len * b, cy = p[1] + Math.sin(a) * len * 0.6 + Math.sin(a - Math.PI / 2) * len * b;
    c.beginPath(); c.moveTo(p[0], p[1]); c.quadraticCurveTo(cx, cy, ex + Math.cos(a - Math.PI / 2) * len * b * 1.2, ey + Math.sin(a - Math.PI / 2) * len * b * 1.2); c.stroke();
  }
  c.restore();
}
/* smoke puffs from a pipe, each u = (t/T + i/n) mod 1 old: drifting back, growing, fading */
function puffs(c, x, y, s, t, dir, n, night) {
  for (var i = 0; i < n; i++) {
    var u = (t / 900 + i / n) % 1, px = x - dir * u * s * 0.9, py = y - u * s * 0.35 - Math.sin(u * 5 + i) * s * 0.03, r = s * (0.03 + u * 0.09);
    c.fillStyle = night ? 'rgba(170,170,200,' + (0.45 * (1 - u)) + ')' : 'rgba(255,255,255,' + (0.7 * (1 - u)) + ')';
    c.beginPath(); c.arc(px, py, r, 0, TAU); c.fill();
  }
}
function zzz(c, x, y, s, t) {
  c.save(); c.textAlign = 'center'; c.textBaseline = 'middle';
  for (var i = 0; i < 3; i++) { var u = (t / 2400 + i / 3) % 1; c.globalAlpha = Math.sin(u * Math.PI);
    c.fillStyle = '#fff6d8'; c.font = '800 ' + Math.round(s * (0.5 + u * 0.7)) + 'px ' + FONT; c.fillText('z', x + u * s * 1.2 + Math.sin(u * 7) * s * 0.2, y - u * s * 2.2); }
  c.restore();
}
function shadowUnder(c, x, y, rx) { c.fillStyle = 'rgba(0,0,0,.22)'; c.beginPath(); c.ellipse(x, y, rx, rx * 0.16, 0, 0, TAU); c.fill(); }

/* ================================================================ the robot
   A friendly robot, front on, cut from paper: a body and a screen head in a Lanna colour with
   gold lai kham trim and kalae horns for an antenna (cut once); eyes, lamp, wheels and arms
   drawn live. o: col, head, legs, tilt, bob, look, happy, hands [[x,y],[x,y]] or arms
   [a1, e1, a2, e2] (from hanging down, + = outward), nails, wa (wheel turn). */
var RCOL = ['#8e2a2a', '#2c3e6b', '#2f7f6b', '#b8621f', '#6b2f6b'];
function robotBody(q, h, o) {
  var B = o.col, L = mixc(B, '#000000', 0.35);
  if (o.legs) {
    [-1, 1].forEach(function (s) { paper(q, rrect(s * 0.1 * h - 0.05 * h, -0.28 * h, 0.1 * h, 0.24 * h, 0.03 * h), L, 0.8);
      paper(q, rrect(s * 0.1 * h - 0.08 * h, -0.06 * h, 0.16 * h, 0.06 * h, 0.03 * h), B, 0.8);
      q.fillStyle = GOLD; q.fillRect(s * 0.1 * h - 0.05 * h, -0.2 * h, 0.1 * h, 0.02 * h); });
  } else {
    paper(q, rrect(-0.25 * h, -0.27 * h, 0.5 * h, 0.1 * h, 0.04 * h), L, 0.8);
    q.fillStyle = GOLD; for (var k = -2; k <= 2; k++) { q.beginPath(); q.arc(k * 0.09 * h, -0.22 * h, 0.012 * h, 0, TAU); q.fill(); }
  }
  paper(q, rrect(-0.06 * h, -0.71 * h, 0.12 * h, 0.09 * h, 0.02 * h), '#3a3440', 0.6);
  paper(q, rrect(-0.22 * h, -0.65 * h, 0.44 * h, 0.4 * h, 0.07 * h), B, 1.4);
  q.strokeStyle = GOLD; q.lineWidth = Math.max(1, h * 0.012); q.beginPath(); rr(q, -0.195 * h, -0.625 * h, 0.39 * h, 0.35 * h, 0.055 * h); q.stroke();
  laiKham(q, -0.19 * h, 0.19 * h, -0.575 * h, 0.032 * h);
  /* lotus petals round the chest lamp */
  q.fillStyle = GOLD; for (var p = 0; p < 8; p++) { var a = p / 8 * TAU; q.beginPath(); q.ellipse(Math.cos(a) * 0.075 * h, -0.4 * h + Math.sin(a) * 0.075 * h, 0.03 * h, 0.012 * h, a, 0, TAU); q.fill(); }
  q.fillStyle = '#2a2230'; q.beginPath(); q.arc(0, -0.4 * h, 0.05 * h, 0, TAU); q.fill();
  /* the head: a cream case, a dark screen */
  paper(q, rrect(-0.2 * h, -0.97 * h, 0.4 * h, 0.28 * h, 0.08 * h), o.head || '#f2e6c9', 1.2);
  q.fillStyle = '#1b2433'; q.beginPath(); rr(q, -0.155 * h, -0.935 * h, 0.31 * h, 0.2 * h, 0.05 * h); q.fill();
  q.strokeStyle = GOLD; q.lineWidth = Math.max(1, h * 0.01); q.beginPath(); rr(q, -0.2 * h + 1, -0.97 * h + 1, 0.4 * h - 2, 0.28 * h - 2, 0.08 * h); q.stroke();
  [-1, 1].forEach(function (s) { q.fillStyle = GOLD; q.beginPath(); q.arc(s * 0.212 * h, -0.83 * h, 0.034 * h, 0, TAU); q.fill(); q.fillStyle = B; q.beginPath(); q.arc(s * 0.212 * h, -0.83 * h, 0.016 * h, 0, TAU); q.fill(); });
  q.strokeStyle = '#3a3440'; q.lineWidth = Math.max(1.2, h * 0.02); q.beginPath(); q.moveTo(0, -0.97 * h); q.lineTo(0, -1.04 * h); q.stroke();
  kalae(q, 0, -1.04 * h, 0.08 * h);
}
function robot(S, x, y, h, o) {
  var c = S.c, t = S.t, w = h * 0.7, hh = h * 1.2, tilt = o.tilt || 0, by = y + (o.bob || 0);
  var spr = sprite(S, 'robot' + o.col + (o.head || '') + (o.legs ? 'L' : 'W'), w, hh, function (q) { q.translate(w / 2, hh - 0.04 * h); robotBody(q, h, o); });
  shadowUnder(c, x, y + 1, h * 0.28);
  c.save(); c.translate(x, by); c.rotate(tilt);
  if (spr) c.drawImage(spr, -w / 2, -hh + 0.04 * h, w, hh); else robotBody(c, h, o);
  if (!o.legs) [-1, 1].forEach(function (s) { wheel(c, s * 0.15 * h, -0.09 * h, 0.09 * h, (o.wa || 0) + s, '#d8d2c0'); });
  /* face */
  var blink = ((t + (o.seed || 0) * 977) % 3900) < 140, lk = (o.look || 0) * 0.03 * h, ey = -0.845 * h, eye = o.night ? '#9ff7ff' : '#7fe8ff';
  if (o.night) { glow(c, -0.07 * h + lk, ey, h * 0.09, 185, 0.7); glow(c, 0.07 * h + lk, ey, h * 0.09, 185, 0.7); }
  c.fillStyle = eye; c.strokeStyle = eye; c.lineWidth = Math.max(1.2, h * 0.018); c.lineCap = 'round';
  [-1, 1].forEach(function (s) {
    var ex = s * 0.07 * h + lk;
    if (o.happy) { c.beginPath(); c.arc(ex, ey + 0.012 * h, 0.03 * h, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); }
    else if (blink) { c.beginPath(); c.moveTo(ex - 0.03 * h, ey); c.lineTo(ex + 0.03 * h, ey); c.stroke(); }
    else { c.beginPath(); c.ellipse(ex, ey, 0.03 * h, 0.04 * h, 0, 0, TAU); c.fill(); c.fillStyle = '#fff'; c.beginPath(); c.arc(ex + 0.01 * h, ey - 0.014 * h, 0.009 * h, 0, TAU); c.fill(); c.fillStyle = eye; }
  });
  c.beginPath(); c.arc(lk * 0.5, -0.79 * h, 0.035 * h, 0.15 * Math.PI, 0.85 * Math.PI); c.stroke();
  c.fillStyle = 'rgba(255,120,150,.55)'; [-1, 1].forEach(function (s) { c.beginPath(); c.arc(s * 0.115 * h, -0.79 * h, 0.018 * h, 0, TAU); c.fill(); });
  /* chest lamp and antenna light, breathing */
  var pl = 0.5 + 0.5 * Math.sin(t / 600 + (o.seed || 0));
  if (o.night) glow(c, 0, -0.4 * h, h * 0.16, 40, 0.4 + 0.4 * pl);
  c.fillStyle = 'hsl(' + (35 + 15 * pl) + ',100%,' + (55 + 20 * pl) + '%)'; c.beginPath(); c.arc(0, -0.4 * h, 0.035 * h, 0, TAU); c.fill();
  var al = (t / 1000 + (o.seed || 0)) % 1.6 < 0.8;
  if (al && o.night) glow(c, 0, -1.0 * h, h * 0.07, 0, 0.8);
  c.fillStyle = al ? '#ff4a3a' : '#7a2a2a'; c.beginPath(); c.arc(0, -1.0 * h, 0.018 * h, 0, TAU); c.fill();
  /* arms */
  var L1 = 0.21 * h, L2 = 0.19 * h, arm = mixc(o.col, '#000000', 0.3), out = [];
  [-1, 1].forEach(function (s, i) {
    var sh = [s * 0.21 * h, -0.6 * h], el, hd;
    if (o.hands) {
      var g = o.hands[i], gx = g[0] - x, gy = g[1] - by, ct = Math.cos(-tilt), st = Math.sin(-tilt);
      hd = [gx * ct - gy * st, gx * st + gy * ct]; el = elbowOf(sh, hd, L1, L2, -s * (o.bend ? o.bend[i] : 1));
      var dd = Math.hypot(hd[0] - sh[0], hd[1] - sh[1]); if (dd > L1 + L2) { hd = [sh[0] + (hd[0] - sh[0]) / dd * (L1 + L2) * 0.999, sh[1] + (hd[1] - sh[1]) / dd * (L1 + L2) * 0.999]; el = elbowOf(sh, hd, L1, L2, -s); }
    } else {
      var A = o.arms || [0.3, 0.3, 0.3, 0.3], a1 = A[i * 2], a2 = A[i * 2 + 1];
      el = [sh[0] + s * Math.sin(a1) * L1, sh[1] + Math.cos(a1) * L1]; hd = [el[0] + s * Math.sin(a1 + a2) * L2, el[1] + Math.cos(a1 + a2) * L2];
    }
    c.lineCap = 'round'; line(c, [sh, el, hd], arm, h * 0.07);
    c.fillStyle = GOLD; c.beginPath(); c.arc(el[0], el[1], h * 0.035, 0, TAU); c.fill();
    c.fillStyle = o.col; c.beginPath(); c.arc(sh[0], sh[1], h * 0.045, 0, TAU); c.fill();
    var fa = Math.atan2(hd[1] - el[1], hd[0] - el[0]);
    if (o.nails) { nails(c, hd, fa - s * 0.5, h * 0.13, s * 0.35); }
    else { c.strokeStyle = arm; c.lineWidth = h * 0.03; c.beginPath(); c.moveTo(hd[0], hd[1]); c.lineTo(hd[0] + Math.cos(fa + 0.5) * h * 0.06, hd[1] + Math.sin(fa + 0.5) * h * 0.06); c.moveTo(hd[0], hd[1]); c.lineTo(hd[0] + Math.cos(fa - 0.5) * h * 0.06, hd[1] + Math.sin(fa - 0.5) * h * 0.06); c.stroke(); }
    c.fillStyle = '#f2e6c9'; c.beginPath(); c.arc(hd[0], hd[1], h * 0.032, 0, TAU); c.fill();
    var ct2 = Math.cos(tilt), st2 = Math.sin(tilt);
    out.push([x + hd[0] * ct2 - hd[1] * st2, by + hd[0] * st2 + hd[1] * ct2, fa + tilt]);
  });
  c.restore();
  return { hand: out, head: [x, by - 0.85 * h] };
}

/* ================================================================ 1. robots
   a. class: a robotics class in a Lanna sala; little rovers roll a figure-8,
      x = a·sin θ, y = b·sin 2θ, heading atan2(ẏ, ẋ); a laptop scrolls their code */
function rover(c, x, y, s, hd, col, t, i, night) {
  shadowUnder(c, x, y + s * 0.18, s * 0.6);
  c.save(); c.translate(x, y); c.scale(1, 0.55); c.rotate(hd);
  c.fillStyle = '#16141a'; c.fillRect(-s * 0.4, -s * 0.42, s * 0.3, s * 0.12); c.fillRect(-s * 0.4, s * 0.3, s * 0.3, s * 0.12); c.fillRect(s * 0.1, -s * 0.42, s * 0.3, s * 0.12); c.fillRect(s * 0.1, s * 0.3, s * 0.3, s * 0.12);
  c.fillStyle = col; c.beginPath(); rr(c, -s * 0.5, -s * 0.32, s, s * 0.64, s * 0.14); c.fill();
  c.fillStyle = GOLD; c.fillRect(-s * 0.42, -s * 0.05, s * 0.84, s * 0.1);
  c.fillStyle = '#7fe8ff'; c.beginPath(); c.arc(s * 0.42, -s * 0.15, s * 0.07, 0, TAU); c.arc(s * 0.42, s * 0.15, s * 0.07, 0, TAU); c.fill();
  c.restore();
  /* the dome and its flag, upright */
  c.fillStyle = '#f2e6c9'; c.beginPath(); c.arc(x, y - s * 0.08, s * 0.2, Math.PI, TAU); c.fill();
  c.strokeStyle = '#3a3440'; c.lineWidth = 1; c.beginPath(); c.moveTo(x, y - s * 0.26); c.lineTo(x, y - s * 0.7); c.stroke();
  var f = Math.sin(t / 220 + i) * s * 0.05;
  c.fillStyle = ['#d9342b', '#f2c94c', '#2f8f5b', '#4d8fd1'][i % 4]; c.beginPath(); c.moveTo(x, y - s * 0.7); c.lineTo(x - s * 0.32, y - s * 0.62 + f); c.lineTo(x - s * 0.22, y - s * 0.56 + f); c.lineTo(x - s * 0.3, y - s * 0.48 + f); c.lineTo(x, y - s * 0.5); c.closePath(); c.fill();
  if (night) glow(c, x + Math.cos(hd) * s * 0.4, y + Math.sin(hd) * s * 0.22, s * 0.3, 185, 0.6);
}
function kid(S, d, x, y, h, P, dir) { d.dir = dir; return person(S.c, x, y, h, P, d); }
function rbClass(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var sx0 = X(S, 0.0), sx1 = X(S, ph ? 0.66 : 0.68), top = d - u * 2.05, e1 = top + (d - top) * 0.32;
  var CX = X(S, ph ? 0.34 : 0.36), CY = d + (S.H - d) * 0.48, A = Math.min(u * 1.25, S.span * 0.17), B = (S.H - d) * 0.3;
  var bx0 = X(S, ph ? 0.38 : 0.4), bw = Math.min(u * 1.5, S.span * 0.2), by0 = e1 + u * 0.12, bh = u * 0.62;
  layer(S, 'rb-class', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#3a2818' : '#8a5e3a');
    q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; for (var y = d + 8; y < S.H; y += 9) { q.beginPath(); q.moveTo(S.x0, y); q.lineTo(S.x1, y); q.stroke(); }
    K.sala(q, sx0, sx1, d, top, N);
    /* the woven mat under the course, checked like a sua */
    var mx0 = CX - A * 1.35, mx1 = CX + A * 1.35, my0 = d + 2, my1 = S.H - 2;
    paper(q, rect(mx0, my0, mx1 - mx0, my1 - my0), N ? '#6b5a3a' : '#d8c08a', 0.6);
    q.fillStyle = N ? 'rgba(0,0,0,.18)' : 'rgba(120,80,30,.22)';
    for (var gx = mx0, k = 0; gx < mx1; gx += 8, k++) for (var gy = my0 + (k % 2) * 4; gy < my1; gy += 8) q.fillRect(gx, gy, 4, 4);
    q.strokeStyle = N ? 'rgba(255,240,200,.75)' : '#fff8e8'; q.lineWidth = Math.max(2, u * 0.04); q.setLineDash([6, 4]); q.beginPath();
    for (var th = 0; th <= TAU + 0.05; th += 0.05) { var px = CX + A * Math.sin(th), py = CY + B * Math.sin(2 * th); th ? q.lineTo(px, py) : q.moveTo(px, py); } q.stroke(); q.setLineDash([]);
    /* the board: gold frame, the curve and its sums */
    paper(q, rect(bx0 - 4, by0 - 4, bw + 8, bh + 8), '#7a4a2a', 1);
    q.fillStyle = N ? '#e8e4d8' : '#fbfaf4'; q.fillRect(bx0, by0, bw, bh);
    q.strokeStyle = GOLD; q.lineWidth = 1.5; q.strokeRect(bx0 - 2, by0 - 2, bw + 4, bh + 4);
    q.strokeStyle = '#4d8fd1'; q.lineWidth = 1.6; q.beginPath();
    for (th = 0; th <= TAU + 0.05; th += 0.08) { px = bx0 + bw * 0.3 + bw * 0.22 * Math.sin(th); py = by0 + bh * 0.45 + bh * 0.25 * Math.sin(2 * th); th ? q.lineTo(px, py) : q.moveTo(px, py); } q.stroke();
    q.fillStyle = '#2a2a3a'; q.font = '700 ' + Math.max(7, Math.round(u * 0.1)) + 'px ' + FONT; q.textAlign = 'left'; q.textBaseline = 'middle';
    q.fillText('x = sin t', bx0 + bw * 0.58, by0 + bh * 0.3); q.fillText('y = sin 2t', bx0 + bw * 0.58, by0 + bh * 0.55);
    q.fillStyle = '#d9342b'; q.fillText('หุ่นยนต์', bx0 + bw * 0.58, by0 + bh * 0.8);
    /* the khantok and the laptop */
    var kx = X(S, 0.17), ky = d - u * 0.2;
    paper(q, function (z) { z.beginPath(); z.ellipse(kx, ky, u * 0.32, u * 0.07, 0, 0, TAU); }, '#8a4a22', 0.8);
    q.fillStyle = '#6a3518'; q.fillRect(kx - u * 0.22, ky, u * 0.44, u * 0.18); q.fillStyle = GOLD; q.fillRect(kx - u * 0.22, ky + u * 0.03, u * 0.44, u * 0.025);
    paper(q, poly([[kx - u * 0.17, ky - u * 0.02], [kx + u * 0.17, ky - u * 0.02], [kx + u * 0.2, ky + u * 0.02], [kx - u * 0.2, ky + u * 0.02]]), '#9aa0ac', 0.4);
    paper(q, rect(kx - u * 0.15, ky - u * 0.3, u * 0.3, u * 0.28), '#2a2a32', 0.6);
    /* spare parts on the mat: a box of wheels, a screwdriver */
    paper(q, rect(X(S, 0.58), d - u * 0.12, u * 0.3, u * 0.14), '#c0392b', 0.5);
    q.fillStyle = '#16141a'; for (k = 0; k < 3; k++) { q.beginPath(); q.arc(X(S, 0.58) + u * (0.06 + k * 0.09), d - u * 0.13, u * 0.035, 0, TAU); q.fill(); }
  });
  /* the lamps under the eave */
  K.strand(c, sx0 + (sx1 - sx0) * 0.08, sx1 - (sx1 - sx0) * 0.08, e1 - 2, u * 0.12, Math.max(22, u * 0.42), function (x, y, k) {
    if (N) glow(c, x, y + 6, u * 0.18, 30 + (k % 3) * 10, 0.6);
    c.fillStyle = ['#ffcf6a', '#ff8a5a', '#f2e6c9'][k % 3]; c.beginPath(); c.ellipse(x, y + 6, u * 0.045, u * 0.06, 0, 0, TAU); c.fill();
  });
  /* the laptop screen: code scrolling, lines of the rovers' program */
  var kx = X(S, 0.17), ky = d - u * 0.2, scx = kx - u * 0.13, scy = ky - u * 0.28, sw = u * 0.26, sh = u * 0.24;
  if (N) glow(c, kx, scy + sh / 2, u * 0.4, 200, 0.5);
  c.save(); c.beginPath(); c.rect(scx, scy, sw, sh); c.clip(); c.fillStyle = '#10202a'; c.fillRect(scx, scy, sw, sh);
  for (var i = 0; i < 9; i++) { var ly = scy + ((i * sh / 6 - t / 140) % (sh * 1.5) + sh * 1.5) % (sh * 1.5); c.fillStyle = ['#7fe8ff', '#f2c94c', '#ff8ab0', '#9be37f'][(i * 3) % 4]; c.fillRect(scx + 2 + (i % 3) * 3, ly, sw * (0.25 + ((i * 37) % 5) / 9), Math.max(1.2, u * 0.018)); }
  c.restore();
  /* the rovers on the figure-8, depth-sorted by y */
  var nb = ph ? 2 : 3, bots = [];
  for (i = 0; i < nb; i++) { var th = t / 1000 * 0.75 + i * TAU / nb; bots.push({ x: CX + A * Math.sin(th), y: CY + B * Math.sin(2 * th), hd: Math.atan2(2 * B * Math.cos(2 * th) / 0.55, A * Math.cos(th)), i: i }); }
  /* the board's tracer follows rover 0 */
  var th0 = t / 1000 * 0.75; c.fillStyle = '#d9342b'; c.beginPath(); c.arc(bx0 + bw * 0.3 + bw * 0.22 * Math.sin(th0), by0 + bh * 0.45 + bh * 0.25 * Math.sin(2 * th0), Math.max(2, u * 0.03), 0, TAU); c.fill();
  /* the class */
  var crew = town(S, 6, { casual: 0.55, sin: 0.25, mohom: 0.2 });
  crew.forEach(function (k, j) { if (j % 2 === 0 && k.garb === 'casual') { k.col = '#f4f4f0'; k.low = '#2c3e6b'; } });
  var kh = u * 0.78, cheer = Math.max(0, Math.sin(t / 700)) * 1.0;
  /* the typing kid */
  var typ = Math.sin(t / 90) * 0.08;
  kid(S, crew[0], kx - u * 0.42, d - 2, kh, { lean: 0.18, seat: 0.24, legs: POSE.sit.legs, arms: [1.25 + typ, 0.25, 1.15 - typ, 0.35] }, 1);
  /* kids round the course: one holds a rover up, two cheer */
  var spots = ph ? [0.6, 0.08] : [0.58, 0.27, 0.45];
  spots.forEach(function (f, j) {
    var dir = f < 0.4 ? 1 : -1, up = j === 0 ? 2.6 + 0.2 * Math.sin(t / 500) : 0.5 + cheer * (j === 1 ? 2.2 : 1.6), P = { lean: 0.05, seat: 0.24, legs: POSE.sit.legs, arms: [up, 0.2, j === 0 ? 2.5 : 0.4 + cheer, 0.3] };
    var me = kid(S, crew[1 + j], X(S, f) + (j === 0 ? u * 0.0 : 0), d + 4 + j * 2, kh, P, dir);
    if (j === 0) { var hp = me.hand[0]; c.fillStyle = '#4d8fd1'; c.beginPath(); rr(c, hp[0] - u * 0.1, hp[1] - u * 0.1, u * 0.2, u * 0.1, u * 0.03); c.fill(); c.fillStyle = '#16141a'; c.beginPath(); c.arc(hp[0] - u * 0.06, hp[1], u * 0.035, 0, TAU); c.arc(hp[0] + u * 0.06, hp[1], u * 0.035, 0, TAU); c.fill(); c.fillStyle = GOLD; c.fillRect(hp[0] - u * 0.08, hp[1] - u * 0.07, u * 0.16, u * 0.02); }
  });
  bots.sort(function (a, b) { return a.y - b.y; }).forEach(function (b) { rover(c, b.x, b.y, u * (ph ? 0.4 : 0.34), b.hd, RCOL[(b.i + S.seed) % RCOL.length], t, b.i, N); });
  /* the teacher points along the curve */
  var tx = X(S, 0.66) - u * 0.45, pa = 1.5 + 0.35 * Math.sin(t / 1300);
  var tc = town(S, 1, { mohom: 0.5, sin: 0.5 })[0];
  if (!ph) kid(S, tc, tx + u * 0.45, d + 6, u * 0.98, { lean: 0.04, legs: [0.06, 0, -0.06, 0], arms: [pa, 0.1, 0.2, 0.4] }, -1);
  /* the class robot waves by the sala */
  var rx = X(S, ph ? 0.8 : 0.8), wv = Math.sin(t / 260);
  robot(S, rx, d + 6, u * (ph ? 1.05 : 1.2), { col: RCOL[(S.seed + 3) % RCOL.length], arms: [2.5 + 0.35 * wv, 0.5 + 0.3 * wv, 0.35, 0.4], look: -0.6, happy: Math.sin(t / 1900) > 0.4, night: N, seed: 3, bob: -Math.abs(Math.sin(t / 520)) * u * 0.03 });
  label(S, (sx0 + sx1) / 2, top + (d - top) * 0.1, '#2c7f7b');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* b. sumo: two wedge bots shove on a ring, the push m = A·sin(2π·5u)·u, then one is
   driven off and falls, y = ½gτ²; the robot referee raises the winner's flag; the board keeps score */
var TEAM = [['#c0392b', 'แดง'], ['#2c6bd1', 'ฟ้า']];
function wedge(c, x, y, s, dir, col, wa, t, sparkle) {
  c.save(); c.translate(x, y); c.scale(dir, 1);
  c.fillStyle = 'rgba(0,0,0,.25)'; c.beginPath(); c.ellipse(0, 0, s * 0.55, s * 0.07, 0, 0, TAU); c.fill();
  wheel(c, -s * 0.22, -s * 0.11, s * 0.11, wa, '#c9ccd4');
  c.fillStyle = col; c.beginPath(); c.moveTo(-s * 0.48, -s * 0.06); c.lineTo(-s * 0.48, -s * 0.36); c.lineTo(-s * 0.05, -s * 0.38); c.lineTo(s * 0.5, -s * 0.02); c.lineTo(s * 0.5, 0); c.lineTo(-s * 0.48, 0); c.closePath(); c.fill();
  c.fillStyle = '#c9ccd4'; c.beginPath(); c.moveTo(s * 0.05, -s * 0.3); c.lineTo(s * 0.52, -s * 0.01); c.lineTo(s * 0.3, -s * 0.01); c.closePath(); c.fill();
  c.strokeStyle = GOLD; c.lineWidth = Math.max(1, s * 0.03); c.beginPath(); c.moveTo(-s * 0.44, -s * 0.2); c.lineTo(s * 0.1, -s * 0.22); c.stroke();
  c.fillStyle = GOLD; for (var k = 0; k < 4; k++) { c.beginPath(); c.arc(-s * 0.38 + k * s * 0.13, -s * 0.1, s * 0.025, 0, TAU); c.fill(); }
  /* the eyes on a dome */
  c.fillStyle = '#f2e6c9'; c.beginPath(); c.arc(-s * 0.2, -s * 0.37, s * 0.13, Math.PI, TAU); c.fill();
  c.fillStyle = '#1b2433'; c.beginPath(); c.arc(-s * 0.15, -s * 0.42, s * 0.035, 0, TAU); c.arc(-s * 0.06, -s * 0.41, s * 0.035, 0, TAU); c.fill();
  /* a little tung on a stick at the back */
  c.strokeStyle = '#3a3440'; c.lineWidth = 1; c.beginPath(); c.moveTo(-s * 0.44, -s * 0.36); c.lineTo(-s * 0.46, -s * 0.8); c.stroke();
  var fl = Math.sin(t / 160) * s * 0.04; c.fillStyle = GOLD; c.beginPath(); c.moveTo(-s * 0.46, -s * 0.8); c.lineTo(-s * 0.62 + fl, -s * 0.78); c.lineTo(-s * 0.6 + fl, -s * 0.55); c.lineTo(-s * 0.54 + fl, -s * 0.6); c.lineTo(-s * 0.46, -s * 0.56); c.closePath(); c.fill();
  if (sparkle) { c.strokeStyle = '#ffe680'; c.lineWidth = 1.5; for (k = 0; k < 5; k++) { var a = -Math.PI / 2 + (k - 2) * 0.45 + Math.sin(t / 37 + k) * 0.2, l = s * (0.12 + 0.1 * Math.abs(Math.sin(t / 53 + k))); c.beginPath(); c.moveTo(s * 0.52, -s * 0.12); c.lineTo(s * 0.52 + Math.cos(a) * l, -s * 0.12 + Math.sin(a) * l); c.stroke(); } }
  c.restore();
}
function rbSumo(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var AX = X(S, ph ? 0.4 : 0.42), tw = Math.min(u * 2.6, S.span * 0.36), TY = d - u * 0.5, R = tw * 0.42, ry = u * 0.16;
  var sb = { x: S.x0 + u * 0.72, y: d - u * 1.95, w: Math.min(u * 1.3, S.span * 0.2), h: u * 0.8 };
  layer(S, 'rb-sumo-a', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#2a2230' : '#9a8a72');
    for (var k = 0; k < 14; k++) { q.fillStyle = k % 2 ? 'rgba(0,0,0,.08)' : 'rgba(255,255,255,.05)'; q.fillRect(S.x0 + k * S.span / 14, d, S.span / 14, S.H - d); }
    /* the scoreboard on its carved stand */
    q.fillStyle = '#5a3418'; q.fillRect(sb.x + sb.w * 0.2, sb.y + sb.h, 4, d - sb.y - sb.h); q.fillRect(sb.x + sb.w * 0.8 - 4, sb.y + sb.h, 4, d - sb.y - sb.h);
    paper(q, rect(sb.x - 5, sb.y - 5, sb.w + 10, sb.h + 10), '#7a4a22', 1.4);
    q.strokeStyle = GOLD; q.lineWidth = 1.4; q.strokeRect(sb.x - 2, sb.y - 2, sb.w + 4, sb.h + 4);
    kalae(q, sb.x + sb.w / 2, sb.y - 5, u * 0.16);
    laiKham(q, sb.x - 3, sb.x + sb.w + 3, sb.y + sb.h + 3, u * 0.035);
  });
  /* the score: rounds of 6.4 s, the winner of round n from a hash of n */
  var T = 6400, n = Math.floor(t / T), p = (t % T) / T, base = n - (n % 9), sc = [0, 0];
  function win(k) { return D.hash('sumo' + k + S.seed) & 1; }
  for (var k = base; k < n; k++) sc[win(k)]++;
  var w = win(n); if (p > 0.8) sc[w]++;
  c.fillStyle = '#12101a'; c.fillRect(sb.x, sb.y, sb.w, sb.h);
  c.textAlign = 'center'; c.textBaseline = 'middle';
  [0, 1].forEach(function (i) {
    var cx = sb.x + sb.w * (0.27 + i * 0.46);
    c.fillStyle = TEAM[i][0]; c.font = '800 ' + Math.round(Math.max(9, u * 0.15)) + 'px ' + FONT; c.fillText(TEAM[i][1], cx, sb.y + sb.h * 0.22);
    var flash = p > 0.8 && i === w && Math.floor(t / 150) % 2;
    if (N || flash) glow(c, cx, sb.y + sb.h * 0.62, u * 0.3, i ? 215 : 5, flash ? 0.9 : 0.35);
    c.fillStyle = flash ? '#ffffff' : '#ffd36a'; c.font = '800 ' + Math.round(Math.max(14, u * 0.36)) + 'px ' + FONT; c.fillText(String(sc[i]), cx, sb.y + sb.h * 0.64);
  });
  c.fillStyle = '#ffd36a'; c.font = '800 ' + Math.round(Math.max(12, u * 0.26)) + 'px ' + FONT; c.fillText(':', sb.x + sb.w / 2, sb.y + sb.h * 0.6);
  /* the operators behind the ring, remotes up */
  var crew = town(S, 9, { casual: 0.8, sin: 0.2 });
  [[-1, 0], [1, 1]].forEach(function (o, i) {
    var ox = AX + o[0] * (tw * 0.5 + u * 0.05), pr = Math.sin(t / 130 + i * 2) * 0.12;
    var me = kid(S, crew[i], ox, TY + u * 0.1, u * 0.72, { lean: 0.15, legs: [0.06, 0, -0.06, 0], arms: [1.3 + pr, 0.4, 1.1 - pr, 0.6] }, -o[0]);
    var hp = me.hand[0]; c.fillStyle = '#2a2a32'; c.fillRect(hp[0] - u * 0.06, hp[1] - u * 0.05, u * 0.12, u * 0.08); c.fillStyle = TEAM[o[1]][0]; c.fillRect(hp[0] - u * 0.04, hp[1] - u * 0.035, u * 0.03, u * 0.03);
    c.strokeStyle = '#2a2a32'; c.lineWidth = 1; c.beginPath(); c.moveTo(hp[0] + u * 0.04, hp[1] - u * 0.05); c.lineTo(hp[0] + u * 0.07, hp[1] - u * 0.22); c.stroke();
  });
  /* the table and its ring */
  layer(S, 'rb-sumo-b', 0, S.H, function (q) {
    paper(q, rect(AX - tw / 2, TY, tw, d - TY + 4), N ? '#5a1f1a' : '#9a3226', 1.6);
    q.fillStyle = GOLD; q.fillRect(AX - tw / 2, TY + u * 0.08, tw, u * 0.03); laiKham(q, AX - tw / 2, AX + tw / 2, TY + u * 0.25, u * 0.06); q.fillRect(AX - tw / 2, TY + u * 0.38, tw, u * 0.02);
    paper(q, function (z) { z.beginPath(); z.ellipse(AX, TY, tw / 2, ry * 1.3, 0, 0, TAU); }, N ? '#3a3440' : '#6a6470', 0.8);
    q.fillStyle = '#16141a'; q.beginPath(); q.ellipse(AX, TY, R, ry, 0, 0, TAU); q.fill();
    q.strokeStyle = '#f4f2ea'; q.lineWidth = Math.max(2, u * 0.04); q.beginPath(); q.ellipse(AX, TY, R, ry, 0, 0, TAU); q.stroke();
    q.fillStyle = '#c0392b'; q.fillRect(AX - R * 0.4, TY - ry * 0.5, 3, ry); q.fillStyle = '#2c6bd1'; q.fillRect(AX + R * 0.4 - 3, TY - ry * 0.5, 3, ry);
  });
  if (N) { c.save(); c.globalCompositeOperation = 'lighter'; var g = c.createLinearGradient(AX, 0, AX, TY); g.addColorStop(0, 'rgba(255,240,200,0)'); g.addColorStop(1, 'rgba(255,240,200,.18)'); c.fillStyle = g; c.beginPath(); c.moveTo(AX - u * 0.15, 0); c.lineTo(AX + u * 0.15, 0); c.lineTo(AX + R, TY); c.lineTo(AX - R, TY); c.fill(); c.restore(); }
  /* the bout */
  var s = Math.min(u * 0.82, R * 0.8), mid = 0, fall = 0, gap = 0, spark = false, xs = R * 0.55;
  if (p < 0.12) gap = xs;
  else if (p < 0.2) gap = xs * (1 - ease((p - 0.12) / 0.08));
  else if (p < 0.62) { mid = R * 0.28 * Math.sin((p - 0.2) * TAU * 5) * ((p - 0.2) / 0.42) * 0.8; spark = true; }
  else if (p < 0.78) { var e0 = R * 0.28 * Math.sin(0.42 * TAU * 5) * 0.8; mid = lerp(e0, (w ? -1 : 1) * (R + s * 0.4), ease((p - 0.62) / 0.16)); spark = true; }
  else { mid = (w ? -1 : 1) * (R + s * 0.4); fall = (p - 0.78) / 0.22; }
  var fade = p > 0.94 ? 1 - (p - 0.94) / 0.06 : p < 0.04 ? p / 0.04 : 1;
  c.save(); c.globalAlpha = fade;
  [0, 1].forEach(function (i) {
    var dir = i ? -1 : 1, x = AX + mid - dir * (s * 0.5 + gap), y = TY + ry * 0.2, rot = 0, lose = i !== w && fall > 0;
    if (lose) { var tau = fall * 0.9; x += -dir * s * 0.4 * fall; y += 0.5 * 9 * u * tau * tau; rot = -dir * fall * 1.5; }
    if (y > d - s * 0.1) y = d - s * 0.1;
    c.save(); c.translate(x, y); c.rotate(rot);
    var won = i === w && fall > 0, hop = won ? -Math.abs(Math.sin(t / 110)) * s * 0.12 : 0;
    wedge(c, 0, hop, s, dir, TEAM[i][0], (mid + gap * dir) / (s * 0.11) * dir + t / (spark ? 60 : 400), t + i * 300, spark && i === 0 && Math.sin(t / 90) > 0);
    c.restore();
  });
  c.restore();
  /* the robot referee with both flags; the winner's goes up */
  var rx = X(S, ph ? 0.82 : 0.78), rh = u * (ph ? 1.0 : 1.15), up = p > 0.66 ? ease((p - 0.66) / 0.08) : 0;
  var rf = robot(S, rx, d + 4, rh, { col: '#2f7f6b', arms: [0.35 + (w === 1 ? up * 2.4 : 0), 0.2, 0.35 + (w === 0 ? up * 2.4 : 0), 0.2], look: -0.8, happy: up > 0.9, night: N, seed: 7 });
  [0, 1].forEach(function (i) {
    var hp = rf.hand[i], col = TEAM[1 - i][0], fl = Math.sin(t / 140 + i) * u * 0.03;
    c.strokeStyle = '#e8e2d0'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(hp[0], hp[1]); c.lineTo(hp[0], hp[1] - u * 0.3); c.stroke();
    c.fillStyle = col; c.beginPath(); c.moveTo(hp[0], hp[1] - u * 0.3); c.lineTo(hp[0] + (i ? 1 : -1) * u * 0.22 + fl, hp[1] - u * 0.26); c.lineTo(hp[0] + (i ? 1 : -1) * u * 0.2 + fl, hp[1] - u * 0.13); c.lineTo(hp[0], hp[1] - u * 0.16); c.closePath(); c.fill();
  });
  /* the crowd in front: heads and shoulders, cheering on the win */
  var nc = ph ? 3 : 5, ch = p > 0.66 ? 1 : 0.3;
  for (var j = 0; j < nc; j++) {
    var cx = X(S, 0.08 + j * (ph ? 0.3 : 0.2)) + (j % 2) * u * 0.2, pump = Math.max(0, Math.sin(t / 180 + j * 1.7)) * ch;
    kid(S, crew[2 + j], cx, S.H + u * 0.35, u * 0.82, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [1.2 + pump * 1.8, 0.3, 0.6 + pump * 2.1, 0.2] }, j % 2 ? -1 : 1);
  }
  label(S, AX, Math.max(4, TY - u * 1.65), '#c0392b');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: TY - u * 1.65, y1: S.H });
}

/* c. drones over the Ping: each drone eases from its place in one figure to the same place
   in the next, p = (1 − e(u))·A + e(u)·B with u staggered per drone, through a khom loi, a
   chedi and the rose r = cos 4θ; their lights double in the river */
function sampler(segs, n) {
  var len = [], tot = 0, out = [];
  segs.forEach(function (s) { var l = 0; for (var i = 1; i < s.length; i++) l += Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]); len.push(l); tot += l; });
  segs.forEach(function (s, j) {
    var m = Math.max(2, Math.round(n * len[j] / tot)), acc = [0];
    for (var i = 1; i < s.length; i++) acc.push(acc[i - 1] + Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]));
    for (var k = 0; k < m; k++) { var target = acc[acc.length - 1] * k / m, q = 1; while (q < acc.length - 1 && acc[q] < target) q++; var f = (target - acc[q - 1]) / ((acc[q] - acc[q - 1]) || 1); out.push([lerp(s[q - 1][0], s[q][0], f), lerp(s[q - 1][1], s[q][1], f)]); }
  });
  while (out.length > n) out.splice(Math.floor(out.length * 0.618) % out.length, 1);
  while (out.length < n) out.push(out[out.length % Math.max(1, out.length)]);
  return out;
}
function arcPts(cx, cy, rx, ry, a0, a1, m) { var o = []; for (var i = 0; i <= m; i++) { var a = lerp(a0, a1, i / m); o.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); } return o; }
var SHAPES = {};
function shapes(n) {
  if (SHAPES[n]) return SHAPES[n];
  /* the khom loi: dome, flared sides, the wire ring, the flame */
  var lantern = sampler([arcPts(0, -0.5, 0.5, 0.32, Math.PI, TAU, 22), [[0.5, -0.5], [0.4, 0.42]], arcPts(0, 0.42, 0.4, 0.07, 0, TAU, 20), [[-0.4, 0.42], [-0.5, -0.5]],
    [[-0.2, -0.78], [-0.16, 0.42]], [[0.2, -0.78], [0.16, 0.42]], [[-0.4, 0.42], [0, 0.6]], [[0.4, 0.42], [0, 0.6]], arcPts(0, 0.66, 0.07, 0.11, 0, TAU, 10)], n);
  /* a Lanna chedi: three square tiers, the bell, the stacked rings, the spire and its umbrella */
  var chedi = sampler([[[-0.62, 0.9], [0.62, 0.9], [0.62, 0.74], [0.5, 0.74], [0.5, 0.58], [0.38, 0.58], [0.38, 0.44]], [[-0.38, 0.44], [-0.38, 0.58], [-0.5, 0.58], [-0.5, 0.74], [-0.62, 0.74], [-0.62, 0.9]],
    arcPts(0, 0.44, 0.34, 0.5, Math.PI, TAU, 20), [[-0.16, -0.14], [0.16, -0.14]], [[-0.12, -0.26], [0.12, -0.26]], [[-0.09, -0.37], [0.09, -0.37]], [[-0.06, -0.47], [0.06, -0.47]], [[0, -0.47], [0, -0.9]], [[-0.12, -0.72], [0.12, -0.72]], [[-0.07, -0.82], [0.07, -0.82]]], n);
  /* the dok kham, eight petals, r = cos 4θ, with a ring */
  var fl = []; for (var a = 0; a <= TAU; a += TAU / 160) { var r = 0.85 * Math.abs(Math.cos(4 * a)); fl.push([Math.cos(a) * r, Math.sin(a) * r]); }
  var flower = sampler([fl, arcPts(0, 0, 0.18, 0.18, 0, TAU, 12)], n);
  return (SHAPES[n] = [lantern, chedi, flower]);
}
function rbDrones(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var ry0 = d - u * 0.32, ry1 = d + (S.H - d) * 0.3, FX = X(S, ph ? 0.38 : 0.38), FY = ph ? S.H * 0.3 : S.H * 0.33, FR = Math.min(ph ? S.H * 0.22 : S.H * 0.24, S.span * 0.2);
  layer(S, 'rb-drone', 0, S.H, function (q) {
    /* the far bank's line of trees, the river, the near bank */
    paper(q, function (z) { var pts = []; for (var x = S.x0 - 6; x <= S.x1 + 6; x += 8) pts.push([x, ry0 - u * (0.12 + 0.08 * Math.abs(Math.sin(x * 0.07)) + 0.06 * Math.sin(x * 0.013))]); pts.push([S.x1 + 6, ry0 + 2], [S.x0 - 6, ry0 + 2]); jag(z, pts, 31, 1.5); }, N ? '#16241e' : '#3d6a46', 1);
    var g = q.createLinearGradient(0, ry0, 0, ry1); g.addColorStop(0, N ? '#1c2a4a' : '#5b9ac0'); g.addColorStop(1, N ? '#0e1630' : '#3f7aa6');
    q.fillStyle = g; q.fillRect(S.x0, ry0, S.span, ry1 - ry0);
    q.strokeStyle = 'rgba(255,255,255,.18)'; q.lineWidth = 1; for (var k = 0; k < 18; k++) { var wx = S.x0 + ((k * 0.381) % 1) * S.span, wy = ry0 + 4 + ((k * 0.617) % 1) * (ry1 - ry0 - 8); q.beginPath(); q.moveTo(wx, wy); q.lineTo(wx + u * 0.25, wy); q.stroke(); }
    paper(q, function (z) { var pts = []; for (var x = S.x0 - 6; x <= S.x1 + 6; x += 10) pts.push([x, ry1 + Math.sin(x * 0.03) * 2]); pts.push([S.x1 + 6, S.H + 4], [S.x0 - 6, S.H + 4]); jag(z, pts, 37, 1.2); }, N ? '#1f2a22' : '#6a8a52', 1);
    /* an iron truss bridge over the Ping, after the Nawarat */
    var bx0 = X(S, ph ? 0.66 : 0.7), bx1 = S.x1 + 4, by = ry0 + (ry1 - ry0) * 0.15, bt = u * 0.42;
    q.fillStyle = N ? '#3a3a4a' : '#6a7078'; q.fillRect(bx0, by, bx1 - bx0, u * 0.06);
    for (var px = bx0 + u * 0.4; px < bx1; px += u * 1.1) q.fillRect(px - 3, by, 6, ry1 - by);
    q.strokeStyle = N ? '#5a5a6e' : '#4a5260'; q.lineWidth = Math.max(1.5, u * 0.025); q.beginPath(); q.moveTo(bx0, by); q.lineTo(bx0 + u * 0.3, by - bt); q.lineTo(bx1, by - bt);
    for (var x2 = bx0 + u * 0.3, j = 0; x2 < bx1; x2 += u * 0.3, j++) { q.moveTo(x2, by - bt); q.lineTo(x2 + u * 0.3 * (j % 2 ? -1 : 1) * 0 + u * 0.15, by); q.lineTo(x2 + u * 0.3, by - bt); }
    q.stroke();
  });
  /* the river carries small krathong-like floats, x = x₀ + vt */
  var nf = ph ? 2 : 4;
  for (var i = 0; i < nf; i++) {
    var fx = S.x0 + ((i / nf * S.span + t / 1000 * u * 0.12) % S.span), fy = ry0 + (ry1 - ry0) * (0.35 + 0.4 * ((i * 0.618) % 1)) + Math.sin(t / 700 + i) * 1.2;
    if (N) glow(c, fx, fy - u * 0.05, u * 0.22, 35, 0.6);
    c.fillStyle = '#4f9a5a'; c.beginPath(); c.ellipse(fx, fy, u * 0.09, u * 0.03, 0, 0, TAU); c.fill();
    c.fillStyle = '#ff9ec0'; for (var k = -1; k <= 1; k++) { c.beginPath(); c.moveTo(fx + k * u * 0.04, fy - u * 0.02); c.lineTo(fx + k * u * 0.05 - u * 0.02, fy - u * 0.09); c.lineTo(fx + k * u * 0.05 + u * 0.02, fy - u * 0.09); c.fill(); }
    c.fillStyle = '#fff6c0'; c.fillRect(fx - 0.6, fy - u * 0.12, 1.2, u * 0.05);
  }
  /* the show: 5.4 s per figure, 3.1 s held, 2.3 s to move */
  var n = ph ? 64 : 100, SH = shapes(n), P = 5400, k = Math.floor(t / P), s = t % P, v = Math.max(0, (s - 3100) / 2300), A0 = SH[k % 3], B0 = SH[(k + 1) % 3];
  var hues = [[28, 48], [45, 55], [320, 280]], r = rnd(91), pts = [];
  for (i = 0; i < n; i++) {
    var dl = r(), ui = ease((v - dl * 0.4) / 0.6), a = A0[i], b = B0[i], sw = Math.sin(ui * Math.PI) * 0.25 * (i % 2 ? 1 : -1);
    var x = FX + (lerp(a[0], b[0], ui) + sw) * FR, y = FY + (lerp(a[1], b[1], ui) - Math.abs(sw) * 0.4) * FR;
    x += Math.sin(t / 900 + i) * 1.2; y += Math.cos(t / 1100 + i * 1.3) * 1.2;
    var ha = hues[k % 3], hb = hues[(k + 1) % 3], hue = lerp(ha[i % 2], hb[i % 2], ui);
    pts.push([x, y, hue, i]);
  }
  if (N) {
    c.save(); c.globalCompositeOperation = 'lighter';
    /* the figure's soft fill: the lantern lit from inside, the chedi gold, the flower pink */
    var fillH = [30, 48, 330], wA = v > 0 ? 1 - ease(v) : 1, wB = v > 0 ? ease(v) : 0;
    glow(c, FX, FY + FR * 0.05, FR * 0.85, fillH[k % 3], 0.22 * wA); glow(c, FX, FY + FR * 0.05, FR * 0.85, fillH[(k + 1) % 3], 0.22 * wB);
    pts.forEach(function (p) { var tw = 0.75 + 0.25 * Math.sin(t / 240 + p[3] * 2.1); if (p[3] % 2 === 0) glow(c, p[0], p[1], u * 0.11, p[2], 0.5 * tw); c.fillStyle = 'hsla(' + p[2] + ',100%,88%,' + tw + ')'; c.fillRect(p[0] - 1.2, p[1] - 1.2, 2.4, 2.4); });
    /* reflections, squeezed into the river: y' = y_r + (y_r − y)·0.12 */
    var yr = ry0 + 2;
    pts.forEach(function (p, j) { if (j % 2) return; var yy = yr + (FY + FR - p[1]) * 0.12 + 2, wob = Math.sin(t / 300 + j) * 2; c.fillStyle = 'hsla(' + p[2] + ',100%,75%,.45)'; c.fillRect(p[0] - 1 + wob, yy, 2.5, 1.2); });
    c.restore();
  } else {
    pts.forEach(function (p) {
      var x = p[0], y = p[1], z = Math.max(2.2, u * 0.035);
      c.strokeStyle = '#3a3a44'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - z, y - z * 0.4); c.lineTo(x + z, y + z * 0.4); c.moveTo(x - z, y + z * 0.4); c.lineTo(x + z, y - z * 0.4); c.stroke();
      c.fillStyle = 'hsl(' + p[2] + ',90%,55%)'; c.beginPath(); c.arc(x, y, z * 0.55, 0, TAU); c.fill();
    });
  }
  /* the watchers on the near bank, phones up, a pilot at his case */
  var crew = town(S, 8), nw = ph ? 4 : 7;
  for (i = 0; i < nw; i++) {
    var wx = X(S, 0.04 + i * 0.9 / nw) + (i % 2) * u * 0.12, up = i % 3 === 0;
    var me = kid(S, crew[i], wx, S.H + u * 0.18, u * 0.86, { lean: -0.05, legs: [0.05, 0, -0.05, 0], arms: up ? [2.7, 0.3, 0.2, 0.3] : [0.2, 0.4, 0.15, 0.2] }, i % 2 ? -1 : 1);
    if (up) { var hp = me.hand[0]; c.fillStyle = '#15131c'; c.fillRect(hp[0] - u * 0.03, hp[1] - u * 0.1, u * 0.06, u * 0.1); c.fillStyle = N ? '#9fe8ff' : '#cfe6f0'; c.fillRect(hp[0] - u * 0.022, hp[1] - u * 0.09, u * 0.044, u * 0.08); if (N) glow(c, hp[0], hp[1] - u * 0.05, u * 0.12, 195, 0.35); }
  }
  /* a robot on the bank conducts, arms tracing the figure */
  var cr = robot(S, X(S, ph ? 0.86 : 0.9), S.H - u * 0.02, u * (ph ? 0.85 : 0.95), { col: RCOL[(S.seed + 1) % RCOL.length], legs: true, arms: [2.4 + 0.4 * Math.sin(t / 700), 0.4, 2.2 + 0.4 * Math.cos(t / 700), 0.5], look: -1, happy: v > 0, night: N, seed: 11 });
  label(S, X(S, ph ? 0.4 : 0.38), ry0 - u * 0.62, '#4b3a8a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: FY - FR, y1: S.H });
}

/* d. the Sunday market: a robot ladles khao soi at a Lanna stall; the ladle follows the
   path pot → up → bowl, eased, and the steam rises as x = a·sin(ky − ωt) */
function bowl(c, x, y, s, full) {
  c.fillStyle = '#f4f0e6'; c.beginPath(); c.moveTo(x - s, y - s * 0.3); c.quadraticCurveTo(x, y + s * 0.9, x + s, y - s * 0.3); c.closePath(); c.fill();
  c.strokeStyle = '#2c6bd1'; c.lineWidth = Math.max(1, s * 0.12); c.beginPath(); c.moveTo(x - s * 0.8, y); c.quadraticCurveTo(x, y + s * 0.45, x + s * 0.8, y); c.stroke();
  if (full) { c.fillStyle = '#e8902a'; c.beginPath(); c.ellipse(x, y - s * 0.3, s * 0.95, s * 0.2, 0, 0, TAU); c.fill();
    c.strokeStyle = '#f2c94c'; c.lineWidth = Math.max(1, s * 0.12); c.beginPath(); for (var a = 0; a < 5; a++) c.arc(x - s * 0.3 + a * s * 0.15, y - s * 0.45, s * 0.12, 0, Math.PI * 1.6); c.stroke(); }
}
function rbMarket(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var cx0 = X(S, ph ? 0.06 : 0.16), cx1 = X(S, ph ? 0.6 : 0.58), ct = d - u * 0.55, at = d - u * 2.15, potX = cx0 + (cx1 - cx0) * 0.18, potT = ct - u * 0.32;
  var bX = cx0 + (cx1 - cx0) * 0.78, rbX = cx0 + (cx1 - cx0) * 0.5;
  layer(S, 'rb-mkt-a', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#2a2420' : '#a89880');
    q.strokeStyle = 'rgba(0,0,0,.12)'; q.lineWidth = 1; for (var x = S.x0; x < S.x1; x += u * 0.3) { q.beginPath(); q.moveTo(x, d); q.lineTo(x - u * 0.1, S.H); q.stroke(); }
    /* the neighbours: Bo Sang umbrellas and stalls behind */
    var r = rnd(S.seed + 3), j;
    for (var k = 0; k < 4; k++) {
      var ux = X(S, 0.62 + k * 0.1), uy = d - u * (0.9 + r() * 0.3), ur = u * 0.38, col = ['#d9342b', '#e8b84a', '#2f8f5b', '#9b6bd6', '#e5567f'][Math.floor(r() * 5)];
      q.strokeStyle = '#5a3a1a'; q.lineWidth = 2; q.beginPath(); q.moveTo(ux, uy); q.lineTo(ux, d); q.stroke();
      paper(q, function (z) { z.beginPath(); z.moveTo(ux - ur, uy + ur * 0.15); z.quadraticCurveTo(ux, uy - ur * 0.75, ux + ur, uy + ur * 0.15); for (var j = 6; j >= 0; j--) z.lineTo(ux - ur + j * ur / 3, uy + ur * (j % 2 ? 0.22 : 0.15)); z.closePath(); }, col, 1);
      q.strokeStyle = 'rgba(255,255,255,.5)'; q.lineWidth = 0.8; for (j = -2; j <= 2; j++) { q.beginPath(); q.moveTo(ux, uy - ur * 0.3); q.lineTo(ux + j * ur * 0.45, uy + ur * 0.15); q.stroke(); }
      paper(q, rect(ux - u * 0.3, d - u * 0.42, u * 0.6, u * 0.42), N ? '#4a3020' : '#8a5a32', 0.6);
    }
    /* the stall's posts and awning, scalloped, red with gold */
    q.fillStyle = '#5a3418'; q.fillRect(cx0 + 2, at, 5, d - at); q.fillRect(cx1 - 7, at, 5, d - at);
    paper(q, poly([[cx0 - u * 0.15, at + u * 0.28], [cx0 + u * 0.1, at], [cx1 - u * 0.1, at], [cx1 + u * 0.15, at + u * 0.28]]), N ? '#7a2420' : '#b8382a', 1.4);
    q.fillStyle = GOLD; q.fillRect(cx0 - u * 0.12, at + u * 0.25, cx1 - cx0 + u * 0.24, u * 0.04);
    for (x = cx0 - u * 0.12; x < cx1 + u * 0.12; x += u * 0.16) { q.fillStyle = Math.round((x - cx0) / (u * 0.16)) % 2 ? '#f2e6c9' : '#b8382a'; q.beginPath(); q.arc(x + u * 0.08, at + u * 0.29, u * 0.08, 0, Math.PI); q.fill(); }
    kalae(q, (cx0 + cx1) / 2, at, u * 0.2);
    /* the hanging sign */
    var sw = Math.min(u * 1.1, (cx1 - cx0) * 0.36), sx = cx0 + (cx1 - cx0) * 0.8 - sw / 2, sy = at + u * 0.42;
    q.strokeStyle = '#3a2410'; q.lineWidth = 1; q.beginPath(); q.moveTo(sx + sw * 0.2, at + u * 0.3); q.lineTo(sx + sw * 0.2, sy); q.moveTo(sx + sw * 0.8, at + u * 0.3); q.lineTo(sx + sw * 0.8, sy); q.stroke();
    paper(q, rect(sx, sy, sw, u * 0.36), '#6a3a1e', 1); q.strokeStyle = GOLD; q.strokeRect(sx + 2, sy + 2, sw - 4, u * 0.36 - 4);
    q.fillStyle = '#fff4d6'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.font = '800 ' + Math.round(Math.max(10, u * 0.17)) + 'px ' + FONT; q.fillText('ข้าวซอย', sx + sw / 2, sy + u * 0.13);
    q.font = '700 ' + Math.round(Math.max(7, u * 0.1)) + 'px ' + FONT; q.fillText('khao soi', sx + sw / 2, sy + u * 0.28);
  });
  /* the cook */
  var T = 3600, p = (t % T) / T, pot = [potX, potT + u * 0.04], upP = [potX + u * 0.2, potT - u * 0.42], over = [bX - u * 0.05, ct - u * 0.42], hand;
  if (p < 0.2) hand = [lerp(over[0], pot[0], ease(p / 0.2)), lerp(over[1], pot[1], ease(p / 0.2)) - Math.sin(p / 0.2 * Math.PI) * u * 0.25];
  else if (p < 0.32) hand = [pot[0] + Math.sin((p - 0.2) / 0.12 * TAU) * u * 0.06, pot[1] + u * 0.03];
  else if (p < 0.5) hand = [lerp(pot[0], upP[0], ease((p - 0.32) / 0.18)), lerp(pot[1], upP[1], ease((p - 0.32) / 0.18))];
  else if (p < 0.68) hand = [lerp(upP[0], over[0], ease((p - 0.5) / 0.18)), lerp(upP[1], over[1], ease((p - 0.5) / 0.18))];
  else hand = over;
  var tilt = p > 0.68 && p < 0.86 ? ease((p - 0.68) / 0.08) * 1.3 : 0, full = p > 0.74 && p < 0.97;
  var hand2 = p > 0.86 ? [lerp(bX, cx1 + u * 0.15, ease((p - 0.86) / 0.1)), ct - u * 0.12] : [bX, ct - u * 0.12];
  var rb = robot(S, rbX, d - u * 0.05, u * 1.4, { col: RCOL[(S.seed + 2) % RCOL.length], legs: true, hands: [hand, hand2], bend: [1, -1], look: p < 0.5 ? -1 : 0.6, happy: full, night: N, seed: 5 });
  /* the counter, the stove and pot, the bowls */
  layer(S, 'rb-mkt-b', 0, S.H, function (q) {
    paper(q, rect(cx0 - u * 0.05, ct, cx1 - cx0 + u * 0.1, d - ct + 2), N ? '#4a2a16' : '#7a4a22', 1.6);
    q.fillStyle = GOLD; q.fillRect(cx0 - u * 0.05, ct + u * 0.05, cx1 - cx0 + u * 0.1, u * 0.025); laiKham(q, cx0, cx1, ct + u * 0.2, u * 0.05); q.fillRect(cx0 - u * 0.05, ct + u * 0.33, cx1 - cx0 + u * 0.1, u * 0.02);
    q.fillStyle = '#c0392b'; q.fillRect(cx0 + u * 0.1, ct + u * 0.4, cx1 - cx0 - u * 0.2, d - ct - u * 0.45);
    for (var k = 0; k < 6; k++) { q.fillStyle = k % 2 ? '#f2e6c9' : GOLD; q.fillRect(cx0 + u * 0.1, ct + u * (0.44 + k * 0.035), cx1 - cx0 - u * 0.2, u * 0.012); }
    paper(q, rect(potX - u * 0.26, ct - u * 0.14, u * 0.52, u * 0.14), '#3a3440', 0.8);
    paper(q, function (z) { z.beginPath(); z.moveTo(potX - u * 0.24, potT); z.lineTo(potX + u * 0.24, potT); z.lineTo(potX + u * 0.21, ct - u * 0.14); z.lineTo(potX - u * 0.21, ct - u * 0.14); z.closePath(); }, '#c9a050', 1);
    q.fillStyle = '#e8902a'; q.beginPath(); q.ellipse(potX, potT, u * 0.24, u * 0.04, 0, 0, TAU); q.fill();
    q.fillStyle = 'rgba(255,255,255,.35)'; q.fillRect(potX - u * 0.18, potT + u * 0.05, u * 0.05, u * 0.12);
    for (k = 0; k < 4; k++) bowl(q, bX + u * 0.32, ct - u * 0.03 - k * u * 0.05, u * 0.12, false);
    var dishes = [['#9be37f', 0.45], ['#d97aa0', 0.55], ['#f2e64c', 0.62]];
    dishes.forEach(function (dd) { var x = cx0 + (cx1 - cx0) * dd[1]; q.fillStyle = '#f4f0e6'; q.beginPath(); q.ellipse(x, ct - u * 0.02, u * 0.08, u * 0.025, 0, 0, TAU); q.fill(); q.fillStyle = dd[0]; for (var j = 0; j < 4; j++) { q.beginPath(); q.arc(x - u * 0.04 + j * u * 0.027, ct - u * 0.04, u * 0.02, 0, TAU); q.fill(); } });
  });
  /* the stove's glow, the steam */
  var fl = 0.7 + 0.3 * Math.sin(t / 90) * Math.sin(t / 37);
  glow(c, potX, ct - u * 0.06, u * 0.3, 20, (N ? 0.7 : 0.35) * fl);
  c.strokeStyle = N ? 'rgba(255,240,220,.3)' : 'rgba(255,255,255,.55)'; c.lineWidth = Math.max(1.5, u * 0.03); c.lineCap = 'round';
  for (var i = 0; i < 3; i++) { c.beginPath(); for (var f = 0; f <= 1; f += 0.08) { var yy = potT - f * u * 0.5, xx = potX + (i - 1) * u * 0.1 + Math.sin(f * 7 - t / 300 + i * 2) * u * 0.05 * (0.4 + f); f ? c.lineTo(xx, yy) : c.moveTo(xx, yy); } c.globalAlpha = 0.9; c.stroke(); c.globalAlpha = 1; }
  /* the ladle, tipping over the bowl; the soup pours */
  var h1 = rb.hand[0], la = -0.4 - tilt;
  c.strokeStyle = '#9aa0ac'; c.lineWidth = Math.max(1.5, u * 0.025); c.beginPath(); c.moveTo(h1[0], h1[1]); c.lineTo(h1[0] + Math.cos(la + Math.PI / 2) * u * 0.28, h1[1] + Math.sin(la + Math.PI / 2) * u * 0.28); c.stroke();
  var lx = h1[0] + Math.cos(la + Math.PI / 2) * u * 0.28, ly = h1[1] + Math.sin(la + Math.PI / 2) * u * 0.28;
  c.fillStyle = '#b8bcc4'; c.beginPath(); c.arc(lx, ly, u * 0.06, la, la + Math.PI); c.fill();
  if (tilt > 0.8 && p < 0.84) { c.strokeStyle = '#e8902a'; c.lineWidth = Math.max(2, u * 0.04); c.beginPath(); c.moveTo(lx, ly); c.lineTo(lx + Math.sin(t / 50) * 1.5, ct - u * 0.2); c.stroke(); }
  bowl(c, rb.hand[1][0], rb.hand[1][1] + u * 0.04, u * 0.13, full);
  /* the queue */
  var crew = town(S, 4, { casual: 0.55, sin: 0.3, mohom: 0.15 }), nq = ph ? 2 : 3;
  for (i = 0; i < nq; i++) {
    var qx = cx1 + u * (0.45 + i * 0.55), reach = i === 0 && p > 0.88 ? 1.4 : 0.15 + 0.1 * Math.sin(t / 900 + i);
    kid(S, crew[i], qx, d + 6 + (i % 2) * 3, u * (0.95 + (i % 2) * 0.05), { lean: 0.04, legs: [0.06, 0, -0.06, 0], arms: [reach, 0.2, 0.15, 0.2] }, -1);
  }
  /* lamps along the awning */
  K.strand(c, cx0 - u * 0.1, cx1 + u * 0.1, at + u * 0.33, u * 0.1, Math.max(16, u * 0.3), function (x, y, k) {
    if (N) glow(c, x, y + 3, u * 0.14, 40 + (k % 2) * 10, 0.7);
    c.fillStyle = N ? '#fff2b0' : '#f7e8c0'; c.beginPath(); c.arc(x, y + 3, Math.max(1.6, u * 0.025), 0, TAU); c.fill();
  });
  label(S, X(S, 0.5), Math.max(4, at - u * 0.42), '#b8382a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: at - u * 0.4, y1: S.H });
}

/* e. fon lep: a dancer in gold nails and a robot copying her a beat late; the arms follow
   θ(t) = θ₀ + a·sin(2πt/T), and the robot's are θ(t − 0.6 s) rounded to steps of 0.15 */
function rbFonlep(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var px0 = X(S, ph ? 0.04 : 0.06), px1 = X(S, ph ? 0.74 : 0.72), pt = d - u * 0.22, bk0 = X(S, ph ? 0.1 : 0.14), bk1 = X(S, ph ? 0.68 : 0.62), bkt = d - u * 2.0;
  layer(S, 'rb-fon', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#241a1a' : '#7a6a52');
    /* the lacquer backdrop: red, gold rose in the middle, a lattice of lai kham */
    paper(q, rect(bk0, bkt, bk1 - bk0, pt - bkt), N ? '#4a1414' : '#8e1f1a', 1.6);
    q.strokeStyle = GOLD; q.lineWidth = 2; q.strokeRect(bk0 + 4, bkt + 4, bk1 - bk0 - 8, pt - bkt - 8);
    q.save(); q.beginPath(); q.rect(bk0 + 6, bkt + 6, bk1 - bk0 - 12, pt - bkt - 12); q.clip();
    for (var y = bkt + u * 0.25, row = 0; y < pt; y += u * 0.3, row++) laiKham(q, bk0 + (row % 2) * u * 0.15, bk1, y, u * 0.07, N ? 'rgba(232,184,74,.55)' : 'rgba(232,184,74,.7)');
    q.restore();
    var mx = (bk0 + bk1) / 2, my = bkt + (pt - bkt) * 0.3;
    q.fillStyle = N ? '#4a1414' : '#8e1f1a'; q.beginPath(); q.arc(mx, my, u * 0.4, 0, TAU); q.fill();
    rose(q, mx, my, u * 0.34, GOLD); q.strokeStyle = GOLD; q.lineWidth = 1.5; q.beginPath(); q.arc(mx, my, u * 0.39, 0, TAU); q.stroke();
    kalae(q, mx, bkt, u * 0.25);
    /* the teak dais */
    paper(q, rect(px0, pt, px1 - px0, d - pt + 3), N ? '#3a2214' : '#6a3a1c', 1.4);
    q.fillStyle = GOLD; q.fillRect(px0, pt + 2, px1 - px0, 2); laiKham(q, px0, px1, pt + (d - pt) * 0.6, u * 0.05);
    /* the drum and the seung by the dais */
    var dx = X(S, ph ? 0.86 : 0.82);
    paper(q, function (z) { z.beginPath(); z.ellipse(dx, d - u * 0.18, u * 0.17, u * 0.22, 0, 0, TAU); }, '#a8432f', 1);
    q.fillStyle = '#f2e6c9'; q.beginPath(); q.ellipse(dx, d - u * 0.4, u * 0.14, u * 0.04, 0, 0, TAU); q.fill();
    q.strokeStyle = GOLD; q.lineWidth = 1; for (var k = -2; k <= 2; k++) { q.beginPath(); q.moveTo(dx + k * u * 0.06, d - u * 0.38); q.lineTo(dx + k * u * 0.07, d); q.stroke(); }
  });
  /* candles at the dais' edge */
  for (var i = 0; i < (ph ? 3 : 5); i++) {
    var cx = lerp(px0 + u * 0.2, px1 - u * 0.2, i / ((ph ? 3 : 5) - 1)), fl = 0.8 + 0.2 * Math.sin(t / 70 + i * 3) * Math.sin(t / 41 + i);
    c.fillStyle = '#f2e6c9'; c.fillRect(cx - 2, pt - u * 0.12, 4, u * 0.12);
    glow(c, cx, pt - u * 0.16, u * (N ? 0.22 : 0.12), 35, (N ? 0.8 : 0.5) * fl);
    c.fillStyle = '#ffd36a'; c.beginPath(); c.ellipse(cx, pt - u * 0.16, 2, 4 * fl, 0, 0, TAU); c.fill();
  }
  /* the dance */
  var T = 5200;
  function arms(tt) { var f = tt / T * TAU; return [1.7 + 0.9 * Math.sin(f), 0.9 + 0.5 * Math.sin(f + 1.2), 0.9 - 0.7 * Math.sin(f), 0.9 + 0.5 * Math.sin(f + 2.6)]; }
  var Ad = arms(t), dip = 0.5 + 0.5 * Math.sin(t / T * TAU * 2);
  var dancer = town(S, 1, { sin: 1 })[0]; dancer.dir = 1; dancer.low = '#5a2a6a'; dancer.hem = GOLD; dancer.sabai = GOLD; dancer.hair = 2;
  var dx = X(S, ph ? 0.26 : 0.29), dh = u * 1.4;
  var me = person(c, dx, pt, dh, { lean: 0.06 * Math.sin(t / T * TAU), seat: 0.47 - dip * 0.03, legs: [0.18 + dip * 0.1, -0.3 * dip, -0.08, -0.05], arms: Ad }, dancer);
  /* her gold headpiece and nails */
  c.fillStyle = GOLD; c.beginPath(); c.moveTo(me.head[0] - dh * 0.06, me.head[1] - dh * 0.1); c.lineTo(me.head[0] - dh * 0.03, me.head[1] - dh * 0.24); c.lineTo(me.head[0], me.head[1] - dh * 0.1); c.closePath(); c.fill();
  me.hand.forEach(function (hp, j) { var a = Math.atan2(hp[1] - me.sh[1], hp[0] - me.sh[0]); nails(c, hp, a - 0.9, dh * 0.12, -0.45); });
  /* the robot, a beat late and in steps */
  var Ar = arms(t - 600).map(function (a) { return Math.round(a / 0.15) * 0.15; }), rx = X(S, ph ? 0.52 : 0.52);
  var inSync = Math.abs(Math.sin((t - 300) / T * TAU)) > 0.92;
  robot(S, rx, pt, u * 1.28, { col: RCOL[(S.seed + 4) % RCOL.length], legs: true, arms: [Ar[2] * 0.9 + 0.2, Ar[3] * 0.6, Ar[0] * 0.9, Ar[1] * 0.6], nails: true, look: -1, happy: inSync, tilt: Math.round(0.05 * Math.sin(t / T * TAU) / 0.025) * 0.025, bob: dip * u * 0.02, night: N, seed: 9 });
  if (inSync) { for (i = 0; i < 4; i++) { var a = t / 300 + i * TAU / 4, sx = rx + Math.cos(a) * u * 0.55, sy = pt - u * 1.25 + Math.sin(a) * u * 0.15; c.fillStyle = '#ffe680'; c.beginPath(); c.moveTo(sx, sy - 4); c.lineTo(sx + 1.2, sy - 1.2); c.lineTo(sx + 4, sy); c.lineTo(sx + 1.2, sy + 1.2); c.lineTo(sx, sy + 4); c.lineTo(sx - 1.2, sy + 1.2); c.lineTo(sx - 4, sy); c.lineTo(sx - 1.2, sy - 1.2); c.closePath(); c.fill(); } }
  /* the drummer beats, |sin ωt|, and the music rises */
  var dr = town(S, 2, { mohom: 1 }), drx = X(S, ph ? 0.86 : 0.82), beat = Math.abs(Math.sin(t / 260));
  person(c, drx + u * 0.32, d + 4, u * 0.9, { lean: 0.15, seat: 0.24, legs: POSE.sit.legs, arms: [1.2 + beat * 0.6, 0.6, 1.0 + (1 - beat) * 0.6, 0.6] }, (dr[0].dir = -1, dr[0]));
  K.notes(c, drx - u * 0.1, d - u * 0.6, t, ph ? 2 : 3, N ? '#ffe2a0' : '#fff4d6');
  label(S, (bk0 + bk1) / 2, bkt - u * 0.42, '#8e1f1a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: bkt - u * 0.4, y1: S.H });
}

var RLOOKS = ['class', 'sumo', 'drones', 'market', 'fonlep'];
function robots(S) {
  var v = RLOOKS.indexOf(S.variant) >= 0 ? S.variant : RLOOKS[S.seed % RLOOKS.length];
  ({ class: rbClass, sumo: rbSumo, drones: rbDrones, market: rbMarket, fonlep: rbFonlep })[v](S);
}

/* ================================================================ the tuk-tuk
   Side on, facing +x, s its length. The body is cut once; wheels turn θ = x / r, the body
   rides the bumps, y = A·|sin kx|, the driver's hand twists the throttle. */
var TUKC = [{ b: '#2f8f5b', r: '#1d4a3a', s: '#f2c94c' }, { b: '#2c4e9b', r: '#1a2a5a', s: '#f2c94c' }, { b: '#c0392b', r: '#5a1a14', s: '#f2e6c9' }, { b: '#e8a83a', r: '#2c3e6b', s: '#c0392b' }, { b: '#7a3a8a', r: '#2a1a3a', s: '#e8b84a' }, { b: '#2a9a9a', r: '#1a3a4a', s: '#f2c94c' }];
function tukBody(q, s, k, deco) {
  var C = TUKC[k % TUKC.length], z = function (x, y) { return [x * s, y * s]; };
  /* the bench back */
  paper(q, rrect(-0.53 * s, -0.66 * s, 0.11 * s, 0.26 * s, 0.03 * s), '#7a1f1a', 0.6);
  /* the rear tub */
  paper(q, function (z2) { z2.beginPath(); z2.moveTo(-0.5 * s, -0.17 * s); z2.lineTo(-0.56 * s, -0.24 * s); z2.lineTo(-0.56 * s, -0.4 * s); z2.quadraticCurveTo(-0.55 * s, -0.45 * s, -0.5 * s, -0.45 * s); z2.lineTo(-0.04 * s, -0.43 * s); z2.lineTo(-0.02 * s, -0.17 * s); z2.closePath(); }, C.b, 1.2);
  q.fillStyle = C.s; q.fillRect(-0.55 * s, -0.33 * s, 0.52 * s, 0.035 * s);
  q.fillStyle = '#d8dce4'; q.fillRect(-0.55 * s, -0.27 * s, 0.52 * s, 0.015 * s);
  q.fillStyle = '#ff3a2a'; q.fillRect(-0.57 * s, -0.4 * s, 0.025 * s, 0.06 * s);
  /* floor and running board */
  q.fillStyle = '#2a2830'; q.fillRect(-0.04 * s, -0.2 * s, 0.32 * s, 0.035 * s); q.fillStyle = '#c9ccd4'; q.fillRect(-0.04 * s, -0.2 * s, 0.32 * s, 0.01 * s);
  /* driver's seat */
  paper(q, rrect(0.02 * s, -0.4 * s, 0.17 * s, 0.05 * s, 0.02 * s), '#2a2026', 0.5);
  q.fillStyle = '#2a2026'; q.fillRect(0.08 * s, -0.36 * s, 0.05 * s, 0.17 * s);
  /* the nose fairing and front mudguard */
  paper(q, function (z2) { z2.beginPath(); z2.moveTo(0.24 * s, -0.17 * s); z2.lineTo(0.3 * s, -0.42 * s); z2.quadraticCurveTo(0.36 * s, -0.52 * s, 0.44 * s, -0.48 * s); z2.quadraticCurveTo(0.5 * s, -0.36 * s, 0.49 * s, -0.2 * s); z2.lineTo(0.46 * s, -0.17 * s); z2.closePath(); }, C.b, 1.2);
  q.fillStyle = C.s; q.beginPath(); q.moveTo(0.29 * s, -0.36 * s); q.lineTo(0.48 * s, -0.33 * s); q.lineTo(0.48 * s, -0.3 * s); q.lineTo(0.28 * s, -0.33 * s); q.closePath(); q.fill();
  q.fillStyle = '#d8dce4'; q.beginPath(); q.arc(0.36 * s, -0.12 * s, 0.13 * s, Math.PI * 1.05, Math.PI * 1.95); q.lineTo(0.36 * s + 0.11 * s, -0.12 * s); q.arc(0.36 * s, -0.12 * s, 0.11 * s, Math.PI * 1.95, Math.PI * 1.05, true); q.closePath(); q.fill();
  /* the headlamp ring, the plate */
  q.fillStyle = '#c9ccd4'; q.beginPath(); q.arc(0.47 * s, -0.41 * s, 0.035 * s, 0, TAU); q.fill(); q.fillStyle = '#fff8d8'; q.beginPath(); q.arc(0.47 * s, -0.41 * s, 0.024 * s, 0, TAU); q.fill();
  q.fillStyle = '#f2e6c9'; q.fillRect(-0.55 * s, -0.24 * s, 0.08 * s, 0.04 * s);
  /* windscreen and posts */
  q.fillStyle = 'rgba(200,230,255,.28)'; q.beginPath(); q.moveTo(0.4 * s, -0.5 * s); q.lineTo(0.35 * s, -0.83 * s); q.lineTo(0.31 * s, -0.83 * s); q.lineTo(0.33 * s, -0.5 * s); q.closePath(); q.fill();
  q.strokeStyle = '#2a2830'; q.lineWidth = Math.max(1.4, s * 0.016); q.lineCap = 'round';
  q.beginPath(); q.moveTo(0.4 * s, -0.5 * s); q.lineTo(0.35 * s, -0.84 * s); q.moveTo(-0.03 * s, -0.43 * s); q.lineTo(-0.04 * s, -0.84 * s); q.moveTo(-0.53 * s, -0.45 * s); q.lineTo(-0.52 * s, -0.84 * s); q.stroke();
  /* handlebar */
  q.beginPath(); q.moveTo(0.3 * s, -0.45 * s); q.lineTo(0.27 * s, -0.5 * s); q.stroke();
  /* the roof, sweeping up at the back */
  paper(q, function (z2) { z2.beginPath(); z2.moveTo(0.42 * s, -0.82 * s); z2.quadraticCurveTo(0.4 * s, -0.89 * s, 0.3 * s, -0.9 * s); z2.lineTo(-0.48 * s, -0.9 * s); z2.quadraticCurveTo(-0.6 * s, -0.92 * s, -0.66 * s, -1.02 * s); z2.quadraticCurveTo(-0.6 * s, -0.86 * s, -0.54 * s, -0.83 * s); z2.closePath(); }, C.r, 1.4);
  q.fillStyle = GOLD; for (var x = -0.5; x < 0.38; x += 0.06) { q.beginPath(); q.arc(x * s, -0.845 * s, 0.009 * s, 0, TAU); q.fill(); }
  q.fillStyle = C.s; q.fillRect(-0.5 * s, -0.875 * s, 0.82 * s, 0.012 * s);
}
/* t: the clock; o: { k colour, x (for the wheel turn), dir, bob, driver, pax [{d, P}], night, glow hue, beam, puff, deco(c, s) } */
function tuk(S, x, y, s, o) {
  var c = S.c, t = S.t, dir = o.dir || 1, w = s * 1.4, h = s * 1.15;
  var spr = sprite(S, 'tuk' + (o.k % TUKC.length), w, h, function (q) { q.translate(w * 0.52, h - s * 0.06); tukBody(q, s, o.k); });
  if (o.under != null && S.night) { c.save(); c.translate(x, y); c.scale(1, 0.16); glow(c, 0, 0, s * 0.75, o.under, 0.9); c.restore(); }
  shadowUnder(c, x, y + 1, s * 0.52);
  if (o.beam && S.night) { c.save(); c.globalCompositeOperation = 'lighter'; var bx = x + dir * 0.47 * s, by = y - 0.41 * s + (o.bob || 0), g = c.createLinearGradient(bx, by, bx + dir * s * 1.2, by); g.addColorStop(0, 'rgba(255,240,190,.5)'); g.addColorStop(1, 'rgba(255,240,190,0)'); c.fillStyle = g; c.beginPath(); c.moveTo(bx, by - 2); c.lineTo(bx + dir * s * 1.2, by - s * 0.18); c.lineTo(bx + dir * s * 1.2, by + s * 0.3); c.lineTo(bx, by + 2); c.fill(); c.restore(); glow(c, bx, by, s * 0.12, 50, 0.9); }
  if (o.puff) puffs(c, x - dir * 0.55 * s, y - 0.12 * s, s, t, dir, 4, S.night);
  var th = (o.x != null ? o.x : x) / (s * 0.1) * dir;
  c.save(); c.translate(x, y); c.scale(dir, 1);
  wheel(c, -0.3 * s, -0.1 * s, 0.1 * s, th); wheel(c, 0.36 * s, -0.1 * s, 0.1 * s, th + 1);
  c.translate(0, o.bob || 0);
  /* the people inside, then the body over their legs */
  var drv = null;
  (o.pax || []).forEach(function (p, i) { var hx = -0.32 * s + i * 0.17 * s; person(c, hx, -0.42 * s + s * 0.55 * 0.24, s * 0.55, p.P, (p.d.dir = 1, p.d)); });
  if (o.driver) {
    var tw = Math.sin(t / 140) * 0.05;
    drv = person(c, 0.1 * s, -0.4 * s + s * 0.56 * 0.24, s * 0.56, { lean: 0.22 + (o.lean || 0), seat: 0.24, legs: [1.45, -1.2, 1.4, -1.25], arms: [1.45 + tw, -0.15, 1.35 - tw, -0.05] }, (o.driver.dir = 1, o.driver));
  }
  if (o.lie) o.lie(c, s);
  if (spr) c.drawImage(spr, -w * 0.52, -h + s * 0.06, w, h); else tukBody(c, s, o.k);
  if (drv) { var hp = drv.hand[0]; c.fillStyle = '#16141a'; c.save(); c.translate(hp[0], hp[1]); c.rotate(Math.sin(t / 140) * 0.4); c.fillRect(-s * 0.02, -s * 0.012, s * 0.04, s * 0.024); c.restore(); }
  if (S.night) glow(c, 0.47 * s, -0.41 * s, s * 0.08, 50, 0.9);
  if (S.night) glow(c, -0.56 * s, -0.37 * s, s * 0.06, 0, 0.8);
  if (o.deco) o.deco(c, s);
  c.restore();
}
/* the red songthaew, side on, facing +x, s its length; baskets on the rack */
function songBody(q, s, sign) {
  var R = '#c62a20', Rd = '#8a1a14';
  paper(q, function (z) { z.beginPath(); z.moveTo(-0.5 * s, -0.16 * s); z.lineTo(-0.5 * s, -0.66 * s); z.lineTo(0.18 * s, -0.66 * s); z.lineTo(0.18 * s, -0.16 * s); z.closePath(); z.moveTo(-0.46 * s, -0.56 * s); z.lineTo(0.14 * s, -0.56 * s); z.lineTo(0.14 * s, -0.4 * s); z.lineTo(-0.46 * s, -0.4 * s); z.closePath(); }, R, 1.4);
  q.fillStyle = Rd; q.fillRect(-0.5 * s, -0.66 * s, 0.68 * s, 0.03 * s);
  q.strokeStyle = Rd; q.lineWidth = Math.max(1, s * 0.01); for (var x = -0.38; x < 0.14; x += 0.12) { q.beginPath(); q.moveTo(x * s, -0.56 * s); q.lineTo(x * s, -0.4 * s); q.stroke(); }
  q.fillStyle = '#f2e6c9'; q.fillRect(-0.48 * s, -0.33 * s, 0.64 * s, 0.025 * s);
  q.fillStyle = '#d8dce4'; q.fillRect(-0.56 * s, -0.2 * s, 0.08 * s, 0.025 * s);
  /* the cab and bonnet */
  paper(q, function (z) { z.beginPath(); z.moveTo(0.18 * s, -0.16 * s); z.lineTo(0.18 * s, -0.6 * s); z.lineTo(0.32 * s, -0.6 * s); z.lineTo(0.4 * s, -0.4 * s); z.lineTo(0.52 * s, -0.37 * s); z.lineTo(0.54 * s, -0.2 * s); z.lineTo(0.5 * s, -0.16 * s); z.closePath(); }, R, 1.4);
  q.fillStyle = 'rgba(200,230,255,.55)'; q.beginPath(); q.moveTo(0.21 * s, -0.57 * s); q.lineTo(0.31 * s, -0.57 * s); q.lineTo(0.37 * s, -0.42 * s); q.lineTo(0.21 * s, -0.42 * s); q.closePath(); q.fill();
  q.fillStyle = '#d8dce4'; q.fillRect(0.5 * s, -0.24 * s, 0.05 * s, 0.05 * s); q.fillStyle = '#fff8d8'; q.fillRect(0.51 * s, -0.33 * s, 0.03 * s, 0.03 * s);
  [-0.3, 0.32].forEach(function (wx) { q.fillStyle = '#2a1a18'; q.beginPath(); q.arc(wx * s, -0.12 * s, 0.11 * s, Math.PI, TAU); q.fill(); });
  /* the rack and the sign */
  q.strokeStyle = '#3a3440'; q.lineWidth = Math.max(1, s * 0.01); q.beginPath(); q.moveTo(-0.48 * s, -0.72 * s); q.lineTo(0.16 * s, -0.72 * s); for (x = -0.46; x < 0.18; x += 0.1) { q.moveTo(x * s, -0.66 * s); q.lineTo(x * s, -0.72 * s); } q.stroke();
  if (sign) { paper(q, rect(0.19 * s, -0.7 * s, 0.14 * s, 0.07 * s), '#f4f0e6', 0.6); q.fillStyle = '#c62a20'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.font = '800 ' + Math.max(6, Math.round(s * 0.045)) + 'px ' + FONT; q.fillText(sign, 0.26 * s, -0.665 * s); }
}
function songthaew(S, x, y, s, o) {
  var c = S.c, t = S.t, dir = o.dir || 1, w = s * 1.25, h = s * 0.95;
  var spr = sprite(S, 'song' + (o.sign || ''), w, h, function (q) { q.translate(w * 0.5, h - s * 0.05); songBody(q, s, o.sign); });
  shadowUnder(c, x, y + 1, s * 0.55);
  if (o.puff) puffs(c, x - dir * 0.52 * s, y - 0.12 * s, s * 0.7, t, dir, 4, S.night);
  c.save(); c.translate(x, y); c.scale(dir, 1);
  wheel(c, -0.3 * s, -0.09 * s, 0.09 * s, (o.x || 0) / (s * 0.09)); wheel(c, 0.32 * s, -0.09 * s, 0.09 * s, (o.x || 0) / (s * 0.09) + 1);
  c.translate(0, o.bob || 0);
  /* heads in the windows */
  (o.pax || []).forEach(function (p, i) { var hx = -0.4 * s + i * 0.12 * s; c.fillStyle = p.col; c.fillRect(hx - s * 0.035, -0.46 * s, s * 0.07, s * 0.06); c.fillStyle = p.skin; c.beginPath(); c.arc(hx, -0.49 * s + Math.sin(t / 300 + i) * s * 0.004, s * 0.03, 0, TAU); c.fill(); c.fillStyle = '#1c1410'; c.beginPath(); c.arc(hx, -0.5 * s, s * 0.031, Math.PI, TAU); c.fill(); });
  if (spr) c.drawImage(spr, -w * 0.5, -h + s * 0.05, w, h); else songBody(c, s, o.sign);
  if (o.rack) o.rack(c, s);
  if (S.night) { glow(c, 0.53 * s, -0.32 * s, s * 0.07, 50, 0.9); glow(c, -0.5 * s, -0.3 * s, s * 0.05, 0, 0.7); }
  c.restore();
}
function basket(c, x, y, s, fill) {
  c.fillStyle = '#b88a4a'; c.beginPath(); c.moveTo(x - s, y - s * 0.9); c.lineTo(x + s, y - s * 0.9); c.lineTo(x + s * 0.75, y); c.lineTo(x - s * 0.75, y); c.closePath(); c.fill();
  c.strokeStyle = '#7a5a2a'; c.lineWidth = 0.8; for (var k = 1; k < 4; k++) { c.beginPath(); c.moveTo(x - s * (1 - k * 0.06), y - s * 0.9 + k * s * 0.22); c.lineTo(x + s * (1 - k * 0.06), y - s * 0.9 + k * s * 0.22); c.stroke(); }
  if (fill) { c.fillStyle = fill; for (k = 0; k < 5; k++) { c.beginPath(); c.arc(x - s * 0.6 + k * s * 0.3, y - s * 0.95, s * 0.2, 0, TAU); c.fill(); } }
}
function pax(S, n, mix) { return town(S, n, mix).map(function (d, i) { return { d: d, P: { lean: -0.05, seat: 0.24, legs: [1.45, -1.3, 1.4, -1.35], arms: [0.5, 0.8, 0.4, 0.9] } }; }); }

/* ================================================================ 2. tuk-tuks
   a. race: round the old city at night, past the wall and the moat's fountains; each
      tuk-tuk at its own speed, x = x₀ + vt (mod the stage), neon underglow, speed lines */
function ttRace(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var wy = d - u * 0.62, wt = d - u * 1.55, my0 = d - u * 0.6, my1 = d - u * 0.08;
  layer(S, 'tt-race', 0, S.H, function (q) {
    /* the brick wall, crenellated, and a gate */
    var x0 = S.x0 - 4, x1 = X(S, ph ? 0.62 : 0.66), m = u * 0.12;
    paper(q, function (z) { z.beginPath(); z.moveTo(x0, my0); z.lineTo(x0, wt); for (var x = x0; x < x1 - m * 2; x += m * 2) { z.lineTo(x, wt - m); z.lineTo(x + m, wt - m); z.lineTo(x + m, wt); z.lineTo(x + m * 2, wt); } z.lineTo(x1, wt); z.lineTo(x1, my0); z.closePath(); }, N ? '#5e2a20' : '#a8432f', 1.6);
    q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; for (var y = wt + 6; y < my0; y += 7) { q.beginPath(); q.moveTo(x0, y); q.lineTo(x1, y); q.stroke(); }
    var gx = (x0 + x1) * 0.48; q.fillStyle = N ? '#1a0e10' : '#3a1a14'; q.beginPath(); q.moveTo(gx - u * 0.28, my0); q.lineTo(gx - u * 0.28, wt + u * 0.4); q.arc(gx, wt + u * 0.4, u * 0.28, Math.PI, TAU); q.lineTo(gx + u * 0.28, my0); q.closePath(); q.fill();
    /* trees past the wall */
    for (var k = 0; k < 4; k++) { var tx = X(S, 0.7 + k * 0.09), tr = u * (0.35 + (k % 2) * 0.1); paper(q, function (z) { circ(z, tx, my0 - tr * 1.2, tr, 7 + k); }, N ? '#1a2c22' : '#3d6a46', 1); q.fillStyle = '#4a3020'; q.fillRect(tx - 2, my0 - tr * 0.4, 4, tr * 0.4); }
    /* the moat */
    var g = q.createLinearGradient(0, my0, 0, my1); g.addColorStop(0, N ? '#14203e' : '#4f8fb8'); g.addColorStop(1, N ? '#0c1428' : '#3a7aa0'); q.fillStyle = g; q.fillRect(S.x0, my0, S.span, my1 - my0);
    /* the road */
    paper(q, rect(S.x0 - 4, my1, S.span + 8, S.H - my1 + 4), N ? '#26242c' : '#5a5860', 0.8);
    q.fillStyle = 'rgba(255,255,255,.55)'; for (var x = S.x0; x < S.x1; x += u * 0.5) q.fillRect(x, (my1 + S.H) / 2, u * 0.25, 2);
  });
  /* lamp posts, their light in the water; the fountains, y = v₀t − ½gt² */
  var nl = ph ? 3 : 5;
  for (var i = 0; i < nl; i++) {
    var lx = X(S, 0.08 + i * 0.9 / nl), hue = [45, 320, 190, 45, 120][i % 5];
    c.fillStyle = '#2a2830'; c.fillRect(lx - 1.5, my1 - u * 0.95, 3, u * 0.95);
    if (N) { glow(c, lx, my1 - u * 0.98, u * 0.22, hue, 0.8); c.globalAlpha = 0.5; for (var k = 0; k < 4; k++) { c.fillStyle = 'hsla(' + hue + ',100%,70%,.6)'; c.fillRect(lx - 3 + Math.sin(t / 300 + k + i) * 3, my0 + 3 + k * 5, 6, 2); } c.globalAlpha = 1; }
    c.fillStyle = N ? 'hsl(' + hue + ',100%,80%)' : '#f2e6c9'; c.beginPath(); c.arc(lx, my1 - u * 0.98, u * 0.05, 0, TAU); c.fill();
  }
  var nf = ph ? 2 : 3;
  for (i = 0; i < nf; i++) {
    var fx = X(S, 0.17 + i * 0.27), hue2 = N ? [190, 300, 45][i % 3] : 200;
    for (k = 0; k < 9; k++) {
      var a = ((t / 1200 + k / 9) % 1), vx = (k - 4) * u * 0.1, vy = u * 1.0, xx = fx + vx * a, yy = my0 + u * 0.2 - (vy * a - 0.5 * vy * 2 * a * a);
      c.fillStyle = N ? 'hsla(' + hue2 + ',100%,80%,' + (1 - a) + ')' : 'rgba(240,250,255,' + (0.9 - a * 0.6) + ')'; c.beginPath(); c.arc(xx, yy, Math.max(1, u * 0.022), 0, TAU); c.fill();
    }
    if (N) glow(c, fx, my0 + u * 0.15, u * 0.4, hue2, 0.35);
  }
  /* the race */
  var n = ph ? 2 : 3, s = u * 1.55, crew = town(S, n * 3, { casual: 0.7, mohom: 0.15, sin: 0.15 }), lanes = [my1 + (S.H - my1) * 0.25, S.H - u * 0.08], order = [];
  for (i = 0; i < n; i++) {
    var v = u * (2.2 + 0.7 * ((i * 7 + S.seed) % 5) / 5), L = S.span + s * 2, x = S.x0 - s + ((i / n * L + t / 1000 * v) % L), lane = i % 2;
    order.push({ i: i, x: x, y: lanes[lane], sc: lane ? 1 : 0.82 });
  }
  order.sort(function (a, b) { return a.y - b.y; }).forEach(function (o) {
    var ss = s * o.sc, i = o.i, bob = -Math.abs(Math.sin(o.x * 0.06 + i)) * ss * 0.02 - Math.abs(Math.sin(t / 70 + i)) * ss * 0.006;
    for (var k = 0; k < 4; k++) { var sy = o.y - ss * (0.25 + k * 0.12), sl = ss * (0.3 + ((k + i) % 3) * 0.15); c.strokeStyle = N ? 'hsla(' + [300, 190, 90][i % 3] + ',100%,75%,.5)' : 'rgba(255,255,255,.7)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(o.x - ss * 0.6 - sl, sy); c.lineTo(o.x - ss * 0.62, sy); c.stroke(); }
    var woo = Math.sin(t / 200 + i * 2) > 0;
    tuk(S, o.x, o.y, ss, { k: (S.seed + i * 2) % TUKC.length, x: o.x, bob: bob, driver: crew[i * 3], lean: 0.12, under: [300, 190, 90][i % 3], beam: true, puff: true,
      deco: function (c2, s2) {   /* the race number on the tub, a checked flag on the roof */
        c2.fillStyle = '#f8f4ec'; c2.beginPath(); c2.arc(-0.3 * s2, -0.33 * s2, s2 * 0.07, 0, TAU); c2.fill(); c2.strokeStyle = '#16141a'; c2.lineWidth = 1; c2.stroke();
        c2.save(); c2.scale(1, 1); c2.fillStyle = '#16141a'; c2.textAlign = 'center'; c2.textBaseline = 'middle'; c2.font = '800 ' + Math.round(s2 * 0.09) + 'px ' + FONT; c2.fillText(String(i + 1), -0.3 * s2, -0.325 * s2); c2.restore();
        c2.strokeStyle = '#2a2830'; c2.lineWidth = 1.2; c2.beginPath(); c2.moveTo(-0.5 * s2, -0.9 * s2); c2.lineTo(-0.52 * s2, -1.18 * s2); c2.stroke();
        var fw = Math.sin(t / 90 + i) * s2 * 0.015;
        for (var a2 = 0; a2 < 3; a2++) for (var b2 = 0; b2 < 2; b2++) { c2.fillStyle = (a2 + b2) % 2 ? '#16141a' : '#f8f4ec'; c2.fillRect(-0.52 * s2 - (a2 + 1) * s2 * 0.045, -1.18 * s2 + b2 * s2 * 0.045 + fw * (a2 + 1) / 3, s2 * 0.045, s2 * 0.045); }
      },
      pax: [{ d: crew[i * 3 + 1], P: { lean: -0.1, seat: 0.24, legs: [1.45, -1.3, 1.4, -1.35], arms: woo ? [2.9, 0.1, 2.7, 0.2] : [0.6, 0.8, 2.8, 0.1] } }] });
  });
  label(S, X(S, 0.36), wt - u * 0.55, '#c0392b');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: wt - u * 0.55, y1: S.H });
}

/* b. parade: tuk-tuks dressed in marigold garlands, ribbons and tung roll by slowly, dancers
   between them; ribbons wave x = A·sin(ky − ωt), petals fall */
function ttParade(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  layer(S, 'tt-par', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#2a2230' : '#9a8670');
    q.fillStyle = N ? 'rgba(255,255,255,.06)' : 'rgba(255,255,255,.18)'; q.fillRect(S.x0, d + (S.H - d) * 0.45, S.span, 3);
    /* the bunting poles */
    [X(S, 0.03), X(S, ph ? 0.6 : 0.66)].forEach(function (px) { q.fillStyle = '#e8e2d0'; q.fillRect(px - 2, d - u * 2.1, 4, u * 2.1); });
  });
  var top = d - u * 2.05;
  K.strand(c, X(S, 0.03), X(S, ph ? 0.6 : 0.66), top, u * 0.35, Math.max(14, u * 0.22), function (x, y, k) {
    var fl = Math.sin(t / 600 + x * 0.05) * 0.15;
    c.fillStyle = ['#ff9a1a', '#ffd34a', '#d9342b', '#f2e6c9', '#2f8f5b'][k % 5]; c.beginPath(); c.moveTo(x - 5, y); c.lineTo(x + 5, y); c.lineTo(x + Math.sin(fl) * 6, y + 11); c.closePath(); c.fill();
    if (N && k % 2) glow(c, x, y + 4, u * 0.12, 40, 0.5);
  });
  /* the procession: tuk-tuks and dancers, x = x₀ + vt round the stage */
  var v = u * 0.42, s = u * 1.45, n = ph ? 2 : 3, gap = (S.span + s * 1.6) / n, crew = town(S, n * 3 + 4, { sin: 0.5, mohom: 0.3, casual: 0.2 }), yy = d + (S.H - d) * 0.62;
  for (var i = 0; i < n; i++) {
    var L = S.span + s * 1.6, x = S.x0 - s * 0.8 + ((i * gap + t / 1000 * v) % L), k = (S.seed + i * 3) % TUKC.length;
    /* a dancer walking ahead, arms in fon */
    var dx = x + s * 0.85, wp = walkP(t / 1000 * TAU * 0.5 + i, false), f = t / 3000 * TAU + i;
    wp.arms = [1.6 + 0.6 * Math.sin(f), 0.9, 0.8 - 0.4 * Math.sin(f), 0.9];
    var dd = crew[n * 2 + i]; dd.dir = 1; var me = person(c, dx, yy + 2, u * 0.95, wp, dd);
    if (dd.garb === 'sin') me.hand.forEach(function (hp) { nails(c, hp, -1.2, u * 0.1, -0.4); });
    tuk(S, x, yy, s, { k: k, x: x, bob: -Math.abs(Math.sin(x * 0.04 + i)) * s * 0.012, driver: crew[i * 2], puff: true,
      pax: [{ d: crew[i * 2 + 1], P: { lean: 0, seat: 0.24, legs: [1.45, -1.3, 1.4, -1.35], arms: [2.6 + 0.3 * Math.sin(t / 250 + i), 0.3, 0.4, 0.8] } }],
      deco: function (c2, s2) {
        /* marigold garland along the roof, a catenary of flowers */
        K.strand(c2, -0.5 * s2, 0.38 * s2, -0.86 * s2, s2 * 0.1, s2 * 0.045, function (gx, gy, j) { c2.fillStyle = j % 3 ? '#ff9a1a' : '#ffd34a'; c2.beginPath(); c2.arc(gx, gy, s2 * 0.028, 0, TAU); c2.fill(); });
        /* the flower cone on the nose */
        c2.fillStyle = '#ffd34a'; c2.beginPath(); c2.moveTo(0.36 * s2, -0.5 * s2); c2.lineTo(0.46 * s2, -0.5 * s2); c2.lineTo(0.41 * s2, -0.68 * s2); c2.closePath(); c2.fill();
        for (var j = 0; j < 6; j++) { c2.fillStyle = j % 2 ? '#ff6a8a' : '#ff9a1a'; c2.beginPath(); c2.arc(0.37 * s2 + (j % 3) * 0.03 * s2, -0.52 * s2 - Math.floor(j / 3) * 0.06 * s2, s2 * 0.022, 0, TAU); c2.fill(); }
        /* two tung on poles from the roof, their cloth waving */
        [-0.46, 0.22].forEach(function (px, m) {
          c2.strokeStyle = '#c9b27a'; c2.lineWidth = 1.5; c2.beginPath(); c2.moveTo(px * s2, -0.9 * s2); c2.lineTo(px * s2, -1.5 * s2); c2.stroke();
          for (var q2 = 0; q2 < 8; q2++) { var f0 = q2 / 8, ox = Math.sin(f0 * 4 - t / 400 + m + i) * f0 * s2 * 0.06; c2.fillStyle = ['#d9342b', '#f2c94c', '#f2e6c9', '#2f8f5b'][q2 % 4]; c2.fillRect(px * s2 + 1 + ox, -1.5 * s2 + f0 * s2 * 0.5, s2 * 0.07, s2 * 0.065); }
        });
        /* ribbons from the back, x = A·sin(ky − ωt) */
        ['#ff6a8a', '#ffd34a', '#7fd8ff'].forEach(function (col, m) {
          c2.strokeStyle = col; c2.lineWidth = Math.max(1.5, s2 * 0.02); c2.beginPath();
          for (var f2 = 0; f2 <= 1; f2 += 0.1) { var rx = -0.56 * s2 - f2 * s2 * 0.4, ry = -0.85 * s2 + m * s2 * 0.05 + Math.sin(f2 * 6 - t / 180 + m) * s2 * 0.05 * f2 + f2 * s2 * 0.15; f2 ? c2.lineTo(rx, ry) : c2.moveTo(rx, ry); } c2.stroke();
        });
        if (N) for (j = 0; j < 7; j++) { var bx = lerp(-0.5, 0.36, j / 6) * s2; glow(c2, bx, -0.82 * s2, s2 * 0.07, 45, 0.5 + 0.4 * Math.sin(t / 300 + j)); }
      } });
  }
  /* falling marigold petals */
  var r = rnd(S.seed + 17);
  for (i = 0; i < (ph ? 10 : 18); i++) { var px = S.x0 + r() * S.span, sp = 0.5 + r(), u2 = ((t / 6000) * sp + r()) % 1, py = top + u2 * (S.H - top), sx = px + Math.sin(u2 * 9 + i) * u * 0.2;
    c.fillStyle = i % 2 ? '#ff9a1a' : '#ffd34a'; c.save(); c.translate(sx, py); c.rotate(t / 400 + i); c.fillRect(-2, -1, 4, 2.5); c.restore(); }
  /* watchers at the front edge */
  for (i = 0; i < (ph ? 2 : 4); i++) { var wx = X(S, 0.1 + i * 0.25), wv = Math.sin(t / 300 + i * 2); var me2 = kid(S, crew[crew.length - 1 - i], wx, S.H + u * 0.4, u * 0.85, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [2.3 + wv * 0.4, 0.3, 0.3, 0.3] }, i % 2 ? 1 : -1);
    var hp = me2.hand[0]; c.strokeStyle = '#e8e2d0'; c.lineWidth = 1; c.beginPath(); c.moveTo(hp[0], hp[1]); c.lineTo(hp[0], hp[1] - u * 0.25); c.stroke(); c.fillStyle = ['#d9342b', '#f2c94c', '#2f8f5b', '#e5567f'][i % 4]; c.fillRect(hp[0], hp[1] - u * 0.25, u * 0.14 + wv * 2, u * 0.09); }
  label(S, X(S, 0.33), top + u * 0.45, '#e07a1a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

/* c. nap: a driver asleep in his back seat under a rain tree, hat on his face, the soi dog
   asleep by the wheel; breath r = r₀(1 + 0.04·sin 2πt/4), z's rising, dappled light drifting */
function ttNap(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var TX = X(S, ph ? 0.38 : 0.32), cr = Math.min(u * 1.9, S.span * 0.34), cy = d - u * 2.2;
  layer(S, 'tt-nap', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#24222a' : '#8a8272');
    paper(q, rect(S.x0 - 4, d + (S.H - d) * 0.15, S.span + 8, (S.H - d) * 0.12), N ? '#4a4652' : '#c4bca8', 0.4);
    /* the rain tree: a short trunk, limbs fanning out, a wide flat dome of leaf (clumps along
       the dome y = cy − h·sin a, a darker underside first) */
    var bark = N ? '#2a1e18' : '#5a3a22', r = rnd(S.seed + 9), k;
    q.fillStyle = bark; q.beginPath(); q.moveTo(TX - u * 0.16, d + 2); q.quadraticCurveTo(TX - u * 0.08, d - u * 0.6, TX - u * 0.1, d - u * 0.95); q.lineTo(TX + u * 0.1, d - u * 0.95); q.quadraticCurveTo(TX + u * 0.08, d - u * 0.6, TX + u * 0.18, d + 2); q.closePath(); q.fill();
    q.strokeStyle = bark; q.lineCap = 'round';
    [-0.75, -0.4, 0, 0.35, 0.7].forEach(function (f, j) { q.lineWidth = u * (0.13 - Math.abs(f) * 0.06); q.beginPath(); q.moveTo(TX, d - u * 0.9); q.quadraticCurveTo(TX + f * cr * 0.3, d - u * 1.3, TX + f * cr * 0.85, cy + u * 0.3 - (j % 2) * u * 0.15); q.stroke(); });
    paper(q, function (z) { z.beginPath(); z.ellipse(TX, cy + u * 0.32, cr * 1.02, u * 0.24, 0, 0, TAU); }, N ? '#0f1c15' : '#2f5a38', 1);
    for (k = 0; k < 22; k++) { var a = (k + 0.5) / 22 * Math.PI, bx = TX - Math.cos(a) * cr * (0.95 - 0.1 * r()), by = cy + u * 0.25 - Math.sin(a) * cr * 0.42 + r() * u * 0.08, br = u * (0.26 + r() * 0.16);
      paper(q, function (z) { circ(z, bx, by, br, 11 + k); }, N ? ['#14261c', '#1a2e22'][k % 2] : ['#3d6a46', '#4f7d4a', '#5a8a52'][k % 3], 1); }
    for (k = 0; k < 9; k++) { var bx2 = TX + (r() - 0.5) * cr * 1.2, by2 = cy - u * 0.05 + r() * u * 0.25;
      paper(q, function (z) { circ(z, bx2, by2, u * (0.24 + r() * 0.12), 41 + k); }, N ? '#1a3024' : ['#5a8a52', '#6a9a5a'][k % 2], 0.8); }
    /* pink rain-tree puffs */
    for (k = 0; k < 14; k++) { q.fillStyle = N ? 'rgba(220,140,170,.4)' : 'rgba(255,170,200,.85)'; q.beginPath(); q.arc(TX + (r() - 0.5) * cr * 1.8, cy + u * 0.2 - r() * cr * 0.4, u * 0.03, 0, TAU); q.fill(); }
    /* a spirit house on its post by the tree, garlands on it */
    var sx = X(S, ph ? 0.9 : 0.66), sy = d - u * 1.05;
    q.fillStyle = N ? '#5a5048' : '#cfc3a8'; q.fillRect(sx - 3, sy, 6, d - sy);
    paper(q, rect(sx - u * 0.17, sy - u * 0.24, u * 0.34, u * 0.24), N ? '#8a7040' : '#e8d8a8', 0.8);
    paper(q, poly([[sx - u * 0.24, sy - u * 0.22], [sx, sy - u * 0.5], [sx + u * 0.24, sy - u * 0.22]]), N ? '#7a2a20' : '#b8382a', 0.8);
    kalae(q, sx, sy - u * 0.5, u * 0.1);
    q.fillStyle = '#ff9a1a'; for (k = 0; k < 6; k++) { q.beginPath(); q.arc(sx - u * 0.15 + k * u * 0.06, sy - u * 0.02 + Math.sin(k / 5 * Math.PI) * u * 0.05, u * 0.022, 0, TAU); q.fill(); }
    q.fillStyle = '#d9342b'; q.fillRect(sx - u * 0.05, sy - u * 0.18, u * 0.1, u * 0.12);
    if (N) { /* a street lamp */ var lx = X(S, ph ? 0.8 : 0.84); q.fillStyle = '#3a3840'; q.fillRect(lx - 2, d - u * 1.9, 4, u * 1.9); q.fillRect(lx - u * 0.25, d - u * 1.9, u * 0.27, 3); }
  });
  /* shade and dappled light */
  c.fillStyle = 'rgba(0,0,0,.22)'; c.beginPath(); c.ellipse(TX + u * 0.2, d + (S.H - d) * 0.45, cr * 0.95, (S.H - d) * 0.4, 0, 0, TAU); c.fill();
  if (!N) { var r = rnd(S.seed + 13); for (var i = 0; i < 12; i++) { var lx0 = TX + (r() - 0.5) * cr * 1.6, ly0 = d + r() * (S.H - d) * 0.75 + 3, a = 0.25 + 0.2 * Math.sin(t / 900 + i * 1.7); c.fillStyle = 'rgba(255,240,170,' + a + ')'; c.beginPath(); c.ellipse(lx0 + Math.sin(t / 1500 + i) * u * 0.05, ly0, u * 0.05, u * 0.018, 0, 0, TAU); c.fill(); } }
  else { var lx = X(S, ph ? 0.8 : 0.84) - u * 0.23; glow(c, lx, d - u * 1.84, u * 0.35, 45, 0.9); c.fillStyle = '#fff2c0'; c.beginPath(); c.arc(lx, d - u * 1.84, u * 0.04, 0, TAU); c.fill();
    for (i = 0; i < 4; i++) { var a2 = t / (300 + i * 70) + i * 2; c.fillStyle = 'rgba(255,250,220,.8)'; c.fillRect(lx + Math.cos(a2) * u * 0.18, d - u * 1.84 + Math.sin(a2 * 1.3) * u * 0.12, 2, 2); }
    /* fireflies under the tree */
    var rf = rnd(S.seed + 21); for (i = 0; i < 8; i++) { var fx = TX + (rf() - 0.5) * cr * 1.6 + Math.sin(t / 1300 + i) * u * 0.2, fy = d - u * (0.2 + rf() * 1.2) + Math.cos(t / 1700 + i) * u * 0.1, on = Math.max(0, Math.sin(t / 500 + i * 2.3)); glow(c, fx, fy, u * 0.08, 70, on); } }
  /* the tuk-tuk, parked; the driver lies across the bench, feet over the side */
  var s = u * (ph ? 1.9 : 2.1), kx = TX + u * 0.1, breathe = Math.sin(t / 4000 * TAU), drv = town(S, 1, { casual: 1 })[0];
  drv.col = '#2c3e6b';
  tuk(S, kx, d + (S.H - d) * 0.5, s, { k: (S.seed + 1) % TUKC.length, x: 0,
    lie: function (c2, s2) {
      /* lying on the bench: legs up on the back rail, the head on the near side, a hat */
      var hx = -0.06 * s2, hy = -0.5 * s2;
      c2.lineCap = 'round'; line(c2, [[-0.2 * s2, -0.47 * s2], [-0.42 * s2, -0.6 * s2], [-0.6 * s2, -0.58 * s2]], '#3a3040', s2 * 0.045);
      c2.fillStyle = '#2a1a12'; c2.beginPath(); c2.ellipse(-0.62 * s2, -0.6 * s2, s2 * 0.035, s2 * 0.02, 0.4, 0, TAU); c2.fill();
      c2.fillStyle = drv.col; c2.beginPath(); c2.ellipse(-0.13 * s2, -0.48 * s2 - breathe * s2 * 0.006, s2 * 0.1, s2 * (0.045 + breathe * 0.004), -0.1, 0, TAU); c2.fill();
      c2.fillStyle = drv.skin; c2.beginPath(); c2.arc(hx, hy, s2 * 0.045, 0, TAU); c2.fill();
      line(c2, [[-0.1 * s2, -0.5 * s2], [-0.05 * s2, -0.43 * s2], [-0.12 * s2, -0.45 * s2]], drv.skin, s2 * 0.025);
      c2.fillStyle = '#d9b36a'; c2.beginPath(); c2.ellipse(hx + 0.01 * s2, hy - 0.03 * s2, s2 * 0.07, s2 * 0.02, -0.3, 0, TAU); c2.fill(); c2.beginPath(); c2.arc(hx + 0.01 * s2, hy - 0.04 * s2, s2 * 0.035, Math.PI * 1.1, Math.PI * 2.1); c2.fill();
    },
    deco: function (c2, s2) {
      /* an iced coffee in a bag, hung from the handlebar, swinging */
      var sw = Math.sin(t / 1600) * 0.1, bx = 0.27 * s2, by = -0.5 * s2;
      c2.save(); c2.translate(bx, by); c2.rotate(sw); c2.strokeStyle = '#e8e2d0'; c2.lineWidth = 0.8; c2.beginPath(); c2.moveTo(0, 0); c2.lineTo(0, s2 * 0.06); c2.stroke();
      c2.fillStyle = 'rgba(190,120,60,.85)'; c2.beginPath(); c2.ellipse(0, s2 * 0.11, s2 * 0.035, s2 * 0.055, 0, 0, TAU); c2.fill(); c2.strokeStyle = '#e5567f'; c2.lineWidth = 1.2; c2.beginPath(); c2.moveTo(0, s2 * 0.08); c2.lineTo(s2 * 0.02, s2 * 0.03); c2.stroke(); c2.restore();
    } });
  zzz(c, kx - s * 0.08, d + (S.H - d) * 0.5 - s * 0.58, u * 0.3, t);
  /* the soi dog, curled; a tail thump now and then, an ear flick */
  var gx = kx + s * 0.66, gy = d + (S.H - d) * 0.66, ds = u * 0.8, br = 1 + 0.05 * breathe, thump = Math.max(0, Math.sin(t / 180)) * (Math.sin(t / 3100) > 0.7 ? 1 : 0);
  var fur = ['#c98a4a', '#e8d8b8', '#d9a066', '#b87a3a'][S.seed % 4];
  shadowUnder(c, gx, gy + 1, ds * 0.6);
  c.strokeStyle = fur; c.lineWidth = ds * 0.1; c.lineCap = 'round'; c.beginPath(); c.moveTo(gx + ds * 0.4, gy - ds * 0.08); c.quadraticCurveTo(gx + ds * 0.7, gy - ds * (0.1 + thump * 0.3), gx + ds * 0.62, gy + ds * (0.02 - thump * 0.2)); c.stroke();
  blob(c, gx, gy - ds * 0.15 * br, ds * 0.48, ds * 0.2 * br, fur);
  blob(c, gx - ds * 0.38, gy - ds * 0.1, ds * 0.17, ds * 0.13, fur);
  c.fillStyle = fur; c.beginPath(); c.moveTo(gx - ds * 0.44, gy - ds * 0.18); c.lineTo(gx - ds * (0.5 + (Math.sin(t / 2700) > 0.95 ? 0.06 : 0)), gy - ds * 0.38); c.lineTo(gx - ds * 0.34, gy - ds * 0.22); c.closePath(); c.fill();
  blob(c, gx - ds * 0.53, gy - ds * 0.06, ds * 0.09, ds * 0.06, fur);
  c.fillStyle = '#1a1414'; c.beginPath(); c.arc(gx - ds * 0.61, gy - ds * 0.07, ds * 0.025, 0, TAU); c.fill();
  c.strokeStyle = '#1a1414'; c.lineWidth = 1; c.beginPath(); c.arc(gx - ds * 0.42, gy - ds * 0.12, ds * 0.035, 0.2, Math.PI - 0.2); c.stroke();
  /* sparrows pecking by day */
  if (!N) for (i = 0; i < (ph ? 2 : 3); i++) { var bx = X(S, 0.62 + i * 0.08), pk = Math.max(0, Math.sin(t / 240 + i * 2)) * u * 0.04, by = S.H - u * 0.15;
    blob(c, bx, by - u * 0.05, u * 0.06, u * 0.04, '#8a6a4a'); blob(c, bx + u * 0.05, by - u * 0.08 + pk, u * 0.032, u * 0.03, '#6a4a32'); c.fillStyle = GOLD; c.fillRect(bx + u * 0.08, by - u * 0.08 + pk, u * 0.03, u * 0.012); }
  label(S, TX, cy - cr * 0.48, '#4f7d4a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: cy - cr * 0.5, y1: S.H });
}

/* d. Warorot: a red songthaew loads baskets at Kad Luang, tuk-tuks wait in a row, a carrier
   jogs past with a shoulder pole, its baskets swinging θ = θ₀·sin ωt; the engine idles */
function ttWarorot(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var b0 = X(S, 0.0), b1 = X(S, ph ? 0.6 : 0.62), bt = d - u * 2.3;
  layer(S, 'tt-war', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#28262e' : '#6a6870');
    paper(q, rect(S.x0 - 4, d - 2, S.span + 8, (S.H - d) * 0.18), N ? '#4a4652' : '#bcb4a4', 0.5);
    /* Kad Luang: three floors, a sign band, shutters, awnings */
    paper(q, rect(b0, bt, b1 - b0, d - bt), N ? '#5a5048' : '#e8dcc4', 1.6);
    q.fillStyle = N ? '#3a2a20' : '#c9b48a'; q.fillRect(b0, bt, b1 - b0, u * 0.08);
    var sh = u * 0.34, sy = bt + u * 0.16;
    paper(q, rect(b0 + u * 0.15, sy, b1 - b0 - u * 0.3, sh), '#b8221a', 1);
    q.strokeStyle = GOLD; q.lineWidth = 1.5; q.strokeRect(b0 + u * 0.15 + 3, sy + 3, b1 - b0 - u * 0.3 - 6, sh - 6);
    q.fillStyle = '#ffe9a8'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.font = '800 ' + Math.round(Math.max(10, u * 0.2)) + 'px ' + FONT; q.fillText('กาดหลวง · ตลาดวโรรส', (b0 + b1) / 2, sy + sh / 2 + 1, b1 - b0 - u * 0.5);
    for (var row = 0; row < 2; row++) for (var x = b0 + u * 0.2; x < b1 - u * 0.3; x += u * 0.42) { var wy = bt + u * (0.62 + row * 0.42); q.fillStyle = N ? (((x * 7 + row) | 0) % 3 ? '#ffd88a' : '#2a2a3a') : '#7a9aaa'; q.fillRect(x, wy, u * 0.26, u * 0.26); q.fillStyle = N ? '#3a2a20' : '#c9b48a'; q.fillRect(x - 2, wy + u * 0.26, u * 0.3, 3); }
    /* the shop-front awnings, striped */
    var ay = d - u * 0.95;
    for (x = b0; x < b1; x += u * 0.7) { var col = ['#2f8f5b', '#c0392b', '#2c6bd1', '#e8a83a'][Math.round((x - b0) / (u * 0.7)) % 4]; paper(q, poly([[x, ay], [x + u * 0.66, ay], [x + u * 0.72, ay + u * 0.22], [x - u * 0.06, ay + u * 0.22]]), col, 0.8);
      q.fillStyle = 'rgba(255,255,255,.55)'; for (var k = 0; k < 3; k++) q.fillRect(x + k * u * 0.24, ay + 2, u * 0.08, u * 0.2); }
    q.fillStyle = N ? '#2a2026' : '#5a4a3a'; q.fillRect(b0, ay + u * 0.22, b1 - b0, d - ay - u * 0.22);
    /* the flower stalls past the market: buckets of marigold, rose, orchid */
    for (k = 0; k < (ph ? 3 : 5); k++) { var fx = X(S, 0.66 + k * 0.07), fcol = ['#ff9a1a', '#e5567f', '#b692ff', '#ffd34a', '#f2f2f2'][k % 5]; paper(q, rect(fx - u * 0.1, d - u * 0.22, u * 0.2, u * 0.22), '#3a6a8a', 0.5);
      for (var j = 0; j < 7; j++) { q.fillStyle = fcol; q.beginPath(); q.arc(fx - u * 0.1 + j * u * 0.033, d - u * (0.27 + (j % 3) * 0.04), u * 0.04, 0, TAU); q.fill(); } }
  });
  /* the red lanterns on the façade */
  for (var i = 0; i < (ph ? 3 : 5); i++) { var lx = lerp(b0 + u * 0.3, b1 - u * 0.3, i / ((ph ? 3 : 5) - 1)), ly = d - u * 1.05, sw = Math.sin(t / 900 + i) * 0.06;
    c.save(); c.translate(lx, ly - u * 0.12); c.rotate(sw); if (N) glow(c, 0, u * 0.12, u * 0.24, 5, 0.6); c.fillStyle = '#d9241a'; c.beginPath(); c.ellipse(0, u * 0.12, u * 0.08, u * 0.1, 0, 0, TAU); c.fill(); c.fillStyle = GOLD; c.fillRect(-u * 0.04, u * 0.01, u * 0.08, u * 0.02); c.fillRect(-u * 0.04, u * 0.21, u * 0.08, u * 0.02); c.restore(); }
  /* the songthaew, idling: a fast small shake */
  var crew = town(S, 10), ss = u * 2.4, sx = X(S, ph ? 0.36 : 0.32), sy = d + (S.H - d) * 0.55, idle = Math.sin(t / 45) * u * 0.008;
  var pax2 = crew.slice(0, 4).map(function (p) { return { col: p.col, skin: p.skin }; });
  var lift = (t % 4000) / 4000, up = lift < 0.5 ? ease(lift / 0.5) : 1;
  songthaew(S, sx, sy, ss, { x: 0, bob: idle, puff: true, pax: pax2, sign: 'กาดหลวง', rack: function (c2, s2) {
    basket(c2, -0.36 * s2, -0.72 * s2, s2 * 0.05, '#c98a2a'); basket(c2, -0.22 * s2, -0.72 * s2, s2 * 0.05, '#9be37f'); basket(c2, -0.08 * s2, -0.72 * s2, s2 * 0.05, '#e5567f');
    if (up >= 1) basket(c2, 0.06 * s2, -0.72 * s2, s2 * 0.05, '#ffd34a');
  } });
  /* the loader hands a basket up to the rack */
  var lx2 = sx + ss * 0.0 + ss * 0.06, me = kid(S, crew[5], lx2, sy + 6, u * 0.95, { lean: -0.1, legs: [0.1, 0, -0.1, 0], arms: [lerp(0.6, 2.9, up), 0.2, lerp(0.5, 2.8, up), 0.3] }, -1);
  if (up < 1) { var hp = me.hand[0]; basket(c, hp[0], hp[1] + u * 0.05, ss * 0.05, '#ffd34a'); }
  /* a passenger climbs aboard at the back step */
  var cl = (t % 5200) / 5200, clx = sx - ss * 0.56, cly = sy - ss * 0.04 * ease(Math.min(1, cl * 3));
  if (cl < 0.7) kid(S, crew[6], clx, cly + 4, u * 0.92, walkP(cl * TAU * 2, false), 1);
  /* the tuk-tuks waiting */
  var nt = ph ? 1 : 2;
  for (i = 0; i < nt; i++) {
    var tx = X(S, ph ? 0.84 : 0.72 + i * 0.17), wave = i === 0 ? Math.sin(t / 260) : 0;
    tuk(S, tx, d + (S.H - d) * 0.75, u * 1.4, { k: (S.seed + i * 2 + 1) % TUKC.length, x: 0, dir: -1, bob: Math.sin(t / 50 + i) * u * 0.004, driver: crew[7 + i], puff: i === 0,
      pax: [] });
    if (i === 0) { c.save(); c.strokeStyle = crew[7].skin; c.lineWidth = Math.max(2, u * 0.05); c.lineCap = 'round'; var ax = tx - u * 0.17, ay = d + (S.H - d) * 0.75 - u * 0.85; c.beginPath(); c.moveTo(ax, ay + u * 0.15); c.lineTo(ax - u * 0.1 + wave * u * 0.06, ay - u * 0.08); c.stroke(); c.restore(); }
  }
  /* the carrier with the shoulder pole, jogging along the front */
  var v = u * 0.55, L = S.span + u * 2, cx = S.x0 - u + ((t / 1000 * v + S.seed % 100) % L), wp = walkP(t / 1000 * TAU * 1.2, false), cd = crew[9]; cd.dir = 1; cd.hat = true; cd.garb = 'mohom'; cd.col = '#2c3e6b';
  wp.arms = [2.6, 0.9, 0.2, 0.3];
  var cm = person(c, cx, S.H - 2, u * 0.95, wp, cd), bob = Math.abs(Math.sin(t / 1000 * TAU * 1.2)) * u * 0.04, py = cm.sh[1] - u * 0.03 + bob;
  c.strokeStyle = '#c9a050'; c.lineWidth = Math.max(2, u * 0.03); c.beginPath(); c.moveTo(cx - u * 0.55, py + u * 0.04); c.quadraticCurveTo(cx, py - u * 0.04, cx + u * 0.55, py + u * 0.04); c.stroke();
  [-1, 1].forEach(function (sd) { var th = 0.15 * Math.sin(t / 1000 * TAU * 1.2 + sd), ex = cx + sd * u * 0.52, ey = py + u * 0.04, by2 = ey + u * 0.42; var bx = ex + Math.sin(th) * u * 0.42;
    c.strokeStyle = '#7a5a2a'; c.lineWidth = 1; c.beginPath(); c.moveTo(ex, ey); c.lineTo(bx - u * 0.1, by2 - u * 0.1); c.moveTo(ex, ey); c.lineTo(bx + u * 0.1, by2 - u * 0.1); c.stroke(); basket(c, bx, by2 + u * 0.06, u * 0.14, sd > 0 ? '#9be37f' : '#ff9a1a'); });
  label(S, (b0 + b1) / 2, bt - u * 0.42, '#b8221a');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: bt - u * 0.4, y1: S.H });
}

/* e. wedding: the bride and groom ride a tuk-tuk dressed in white and gold, the guests' one
   behind with the khan maak trays; the road and the flower arches slide past, x = x₀ − vt
   (mod L), balloons swing on their strings as pendulums, θ = θ₀·sin(√(g/L)·t), petals fall */
function archSprite(S, aw, ah) {
  var u = S.hh;
  return sprite(S, 'arch' + S.seed, aw + u * 0.3, ah + u * 0.2, function (q) {
    var ax = aw / 2 + u * 0.15, at = u * 0.12, r = rnd(S.seed + 7), k;
    q.fillStyle = '#e8e2d0'; q.fillRect(ax - aw / 2 - 2, at + aw * 0.5, 4, ah - aw * 0.5); q.fillRect(ax + aw / 2 - 2, at + aw * 0.5, 4, ah - aw * 0.5);
    for (var a = 0; a <= Math.PI; a += 0.07) for (k = 0; k < 2; k++) { var px = ax - Math.cos(a) * aw / 2 + (r() - 0.5) * 4, py = at + aw * 0.5 - Math.sin(a) * aw * 0.5 + (r() - 0.5) * 4 + k * 5;
      q.fillStyle = ['#f8f4ec', '#ffc0d0', '#f2e6c9', '#ff8fb0', '#e8b84a'][Math.floor(r() * 5)]; q.beginPath(); q.arc(px, py, u * (0.05 + r() * 0.03), 0, TAU); q.fill(); }
    for (k = 0; k < 10; k++) { var yy = at + aw * 0.55 + k * (ah - aw * 0.55) / 10; q.fillStyle = ['#f8f4ec', '#ffc0d0', '#9be37f'][k % 3]; q.beginPath(); q.arc(ax - aw / 2 + (k % 2) * 3, yy, u * 0.04, 0, TAU); q.arc(ax + aw / 2 - (k % 2) * 3, yy, u * 0.04, 0, TAU); q.fill(); }
    paper(q, rect(ax - u * 0.38, at + aw * 0.42, u * 0.76, u * 0.24), '#f8f4ec', 0.6);
    q.fillStyle = '#b8382a'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.font = '800 ' + Math.round(Math.max(10, u * 0.16)) + 'px ' + FONT; q.fillText('วิวาห์', ax, at + aw * 0.42 + u * 0.12);
  });
}
function ttWedding(S) {
  var c = S.c, u = S.hh, d = S.deck, t = S.t, N = S.night, ph = S.phone;
  var v = u * 0.6, run = t / 1000 * v, yy = d + (S.H - d) * 0.55;
  layer(S, 'tt-wed', 0, S.H, function (q) {
    K.ground(q, S.x0, S.x1, d, S.H, N ? '#2a2632' : '#8a9a72');
    paper(q, rect(S.x0 - 4, d + (S.H - d) * 0.2, S.span + 8, (S.H - d) * 0.6), N ? '#3a3640' : '#b8b0a0', 0.6);
  });
  /* the road's dashes and the roadside slide by */
  c.fillStyle = 'rgba(255,255,255,.6)'; var gp = u * 0.6;
  for (var x = S.x0 - ((run % gp) + gp) % gp; x < S.x1; x += gp) c.fillRect(x, d + (S.H - d) * 0.52, u * 0.3, 2);
  var aw = u * 1.4, ah = u * 2.0, arch = archSprite(S, aw, ah), L = S.span + aw * 2.6, crew = town(S, 10, { sin: 0.5, mohom: 0.4, casual: 0.1 });
  for (var j = 0; j < 2; j++) {
    var axx = S.x0 - aw + ((j * L / 2 - run) % L + L) % L;
    if (arch) c.drawImage(arch, axx - aw / 2 - u * 0.15, d - ah - u * 0.12 + 2, aw + u * 0.3, ah + u * 0.2);
    /* guests at the arch, cheering the couple past */
    for (var g = 0; g < 2; g++) { var ch = Math.max(0, Math.sin(t / 220 + g * 2 + j)); kid(S, crew[6 + j * 2 + g], axx + (g ? 1 : -1) * aw * 0.25, d + 4, u * 0.95, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.4 + ch * 1.4, 0.4, 0.3 + ch * 0.6, 0.4] }, 1); }
  }
  /* the two tuk-tuks ride mid-stage, easing a little forward and back */
  var s = u * 1.55, x1 = X(S, ph ? 0.68 : 0.55) + Math.sin(t / 3100) * u * 0.2, x2 = x1 - s * 1.45 + Math.sin(t / 2300) * u * 0.12;
  var bride = crew[0], groom = crew[1]; bride.garb = 'sin'; bride.low = '#f2e6c9'; bride.hem = GOLD; bride.sabai = GOLD; bride.col = '#f8f4ec'; bride.hair = 2;
  groom.garb = 'mohom'; groom.col = '#f8f4ec'; groom.low = '#e8dcc4';
  var wv = Math.sin(t / 280), sit = [1.45, -1.3, 1.4, -1.35];
  [[x2, 1], [x1, 0]].forEach(function (pp) {
    var x = pp[0], main = pp[1] === 0;
    tuk(S, x, yy, s, { k: main ? 3 : (S.seed + 2) % TUKC.length, x: run + x, bob: -Math.abs(Math.sin(run * 0.05 + pp[1])) * s * 0.012, driver: crew[main ? 2 : 3], puff: true, beam: main,
      pax: main ? [{ d: groom, P: { lean: -0.05, seat: 0.24, legs: sit, arms: [0.5, 0.8, 0.4, 0.9] } }, { d: bride, P: { lean: -0.05, seat: 0.24, legs: sit, arms: [2.6 + 0.3 * wv, 0.3, 0.4, 0.9] } }]
        : [{ d: crew[4], P: { lean: 0, seat: 0.24, legs: sit, arms: [1.3, 1.2, 1.2, 1.3] } }, { d: crew[5], P: { lean: 0, seat: 0.24, legs: sit, arms: [2.4 - 0.3 * wv, 0.4, 0.4, 0.9] } }],
      deco: function (c2, s2) {
        if (main) {
          /* white ribbon bows and a garland on the roof */
          c2.fillStyle = '#f8f4ec'; [[0.42, -0.42], [-0.3, -0.36]].forEach(function (b) { c2.beginPath(); c2.moveTo(b[0] * s2, b[1] * s2); c2.lineTo(b[0] * s2 - s2 * 0.05, b[1] * s2 - s2 * 0.035); c2.lineTo(b[0] * s2 - s2 * 0.05, b[1] * s2 + s2 * 0.035); c2.closePath(); c2.moveTo(b[0] * s2, b[1] * s2); c2.lineTo(b[0] * s2 + s2 * 0.05, b[1] * s2 - s2 * 0.035); c2.lineTo(b[0] * s2 + s2 * 0.05, b[1] * s2 + s2 * 0.035); c2.closePath(); c2.fill(); });
          K.strand(c2, -0.5 * s2, 0.38 * s2, -0.86 * s2, s2 * 0.08, s2 * 0.04, function (gx, gy, m) { c2.fillStyle = m % 2 ? '#f8f4ec' : '#ffc0d0'; c2.beginPath(); c2.arc(gx, gy, s2 * 0.022, 0, TAU); c2.fill(); });
          /* balloons on strings from the roof's tail, each a pendulum trailing the ride */
          var cols = ['#ff8fb0', '#f8f4ec', '#ffd34a', '#ff6a8a', '#c3a6ff'];
          for (var m = 0; m < 5; m++) { var Ls = s2 * (0.38 + (m % 3) * 0.08), th = 0.2 * Math.sin(t / 1000 * Math.sqrt(9.8 / (Ls / s2 * 2)) + m) - 0.3, ox = -0.62 * s2, oy = -0.98 * s2, bx = ox + Math.sin(th) * Ls - (m - 2) * s2 * 0.05, by = oy - Math.cos(th) * Ls;
            c2.strokeStyle = 'rgba(255,255,255,.8)'; c2.lineWidth = 0.8; c2.beginPath(); c2.moveTo(ox, oy); c2.quadraticCurveTo((ox + bx) / 2 + 3, (oy + by) / 2, bx, by + s2 * 0.06); c2.stroke();
            if (N) glow(c2, bx, by, s2 * 0.12, [330, 45, 50, 340, 270][m], 0.4);
            c2.fillStyle = cols[m]; c2.beginPath(); c2.ellipse(bx, by, s2 * 0.05, s2 * 0.062, th, 0, TAU); c2.fill(); c2.fillStyle = 'rgba(255,255,255,.6)'; c2.beginPath(); c2.arc(bx - s2 * 0.015, by - s2 * 0.022, s2 * 0.012, 0, TAU); c2.fill(); }
          /* a heart on the back of the tub */
          var z = s2 * 0.05; c2.fillStyle = '#ff6a8a'; c2.beginPath(); c2.moveTo(-0.3 * s2, -0.22 * s2); c2.bezierCurveTo(-0.3 * s2 - z * 1.6, -0.22 * s2 - z * 1.2, -0.3 * s2 - z * 0.6, -0.22 * s2 - z * 2.2, -0.3 * s2, -0.22 * s2 - z * 1.3); c2.bezierCurveTo(-0.3 * s2 + z * 0.6, -0.22 * s2 - z * 2.2, -0.3 * s2 + z * 1.6, -0.22 * s2 - z * 1.2, -0.3 * s2, -0.22 * s2); c2.fill();
          if (N) for (m = 0; m < 7; m++) glow(c2, lerp(-0.5, 0.36, m / 6) * s2, -0.84 * s2, s2 * 0.06, 45, 0.6 + 0.3 * Math.sin(t / 250 + m));
        } else {
          /* the khan maak: a gold tray of banana-leaf cones, held up */
          c2.fillStyle = GOLD; c2.fillRect(-0.4 * s2, -0.58 * s2, s2 * 0.16, s2 * 0.025);
          c2.fillStyle = '#4f9a5a'; for (var n2 = 0; n2 < 3; n2++) { c2.beginPath(); c2.moveTo(-0.38 * s2 + n2 * 0.05 * s2, -0.58 * s2); c2.lineTo(-0.355 * s2 + n2 * 0.05 * s2, -0.68 * s2); c2.lineTo(-0.33 * s2 + n2 * 0.05 * s2, -0.58 * s2); c2.fill(); }
          c2.fillStyle = '#ff6a8a'; c2.beginPath(); c2.arc(-0.355 * s2, -0.69 * s2, s2 * 0.015, 0, TAU); c2.fill();
        }
      } });
  });
  /* petals and paper hearts falling */
  var r = rnd(S.seed + 29), top = d - u * 2.1;
  for (var i = 0; i < (ph ? 10 : 18); i++) { var px = S.x0 + r() * S.span, sp = 0.4 + r(), u2 = ((t / 7000) * sp + r()) % 1, py = top + u2 * (S.H - top), sx = px + Math.sin(u2 * 8 + i) * u * 0.25, heart = i % 3 === 0;
    c.save(); c.translate(sx, py); c.rotate(Math.sin(t / 500 + i) * 0.6); c.fillStyle = heart ? '#ff6a8a' : ['#f8f4ec', '#ffc0d0'][i % 2];
    if (heart) { var hz = u * 0.04; c.beginPath(); c.moveTo(0, hz); c.bezierCurveTo(-hz * 1.6, -hz * 0.3, -hz * 0.6, -hz * 1.4, 0, -hz * 0.4); c.bezierCurveTo(hz * 0.6, -hz * 1.4, hz * 1.6, -hz * 0.3, 0, hz); c.fill(); } else c.fillRect(-2, -1.2, 4, 2.4);
    c.restore(); }
  label(S, X(S, 0.45), Math.max(4, d - u * 2.55), '#e5567f');
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
}

var TLOOKS = ['race', 'parade', 'nap', 'warorot', 'wedding'];
function tuktuk(S) {
  var v = TLOOKS.indexOf(S.variant) >= 0 ? S.variant : TLOOKS[S.seed % TLOOKS.length];
  ({ race: ttRace, parade: ttParade, nap: ttNap, warorot: ttWarorot, wedding: ttWedding })[v](S);
}

/* the words that call each scene; the look follows the event's own words, else its key */
function text(e) { return (e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 160); }
D.addScene('robots', robots, /\brobot|drone ?show|\bdrones?\b|arduino|maker ?space|\bstem (camp|class)|\bcoding (class|club|camp)|หุ่นยนต์|โดรน/i,
  'x = a·sin t, y = a·sin 2t (the figure-8)<br>p = (1 − u)·A + u·B (the drones)', 1);
D.addScene('tuktuk', tuktuk, /tuk.?tuks?\b|tuktuk|ตุ๊กตุ๊ก|ตุ๊ก ๆ|สามล้อ|songthaew|song ?taew|สองแถว|rot ?daeng|รถแดง/i,
  'θ = x / r (the wheels)<br>y = A·|sin kx| (the bumps)', 1);
D.variants.robots = function (e) {
  var s = text(e);
  if (/drone|โดรน/i.test(s)) return 'drones';
  if (/sumo|battle|compet|contest|championship|olympiad|tournament|แข่ง|ประกวด/i.test(s)) return 'sumo';
  if (/fon|ฟ้อน|danc|รำ/i.test(s)) return 'fonlep';
  if (/market|bazaar|fair|kad\b|กาด|ตลาด|food/i.test(s)) return 'market';
  if (/class|camp|club|workshop|kids|school|course|เรียน|ค่าย|อบรม/i.test(s)) return 'class';
  return RLOOKS[D.hash(e.k || s) % RLOOKS.length];
};
D.variants.tuktuk = function (e) {
  var s = text(e);
  if (/wedding|bride|วิวาห์|แต่งงาน|มงคลสมรส/i.test(s)) return 'wedding';
  if (/race|rally|grand prix|แข่ง/i.test(s)) return 'race';
  if (/parade|procession|festival|ขบวน|แห่|เทศกาล/i.test(s)) return 'parade';
  if (/songthaew|song ?taew|สองแถว|rot ?daeng|รถแดง|warorot|วโรรส|กาดหลวง|kad luang/i.test(s)) return 'warorot';
  if (/nap|driver|คนขับ|rest/i.test(s)) return 'nap';
  return TLOOKS[D.hash(e.k || s) % TLOOKS.length];
};
})();
