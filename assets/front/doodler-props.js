/* Props for place portraits: things a place's tags say it has, drawn over the scene of its trade
   (Nan, 2026-10-03: "lots of places with good descriptions and no good images yet … slowly
   populate visuals"). doodles_layer.place_facts maps the tags to prop ids by
   data/curated/portrait_props.json; each id here draws one. A prop keeps to the frame's edges,
   the sky and the kerb, where the scenes leave room.
   'lights' (open late, open 24 h) · 'parking' · 'rooster' (opens early) · 'aircon' · 'pool' · 'wifi' · 'farm' · 'water' (coin water kiosk) · 'tables' (tables outside) · 'bubbletea' (bubble tea) */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.addProp) return;
var K = D.kit, paper = K.paper, circ = K.circ, poly = K.poly, rect = K.rect, TAU = K.TAU;
function clock(S) { var b = new Date((S.now || Date.now()) + 7 * 3600e3); return b.getUTCHours() + b.getUTCMinutes() / 60; }
function kerb(S) { return S.deck + (S.H - S.deck) * 0.28; }

/* open late: a string of bulbs across the soi, hung from out of frame; lit after dark */
D.addProp('lights', function (S) {
  var c = S.c, y = S.H * 0.035, sag = S.H * 0.09, n = S.phone ? 2 : 3, w = (S.span + 40) / n, lit = S.night || S.alt < 2;
  var cols = ['#ffd27a', '#ff9d6b', '#fff0b8', '#ffb3c7', '#a8e0ff'];
  for (var k = 0; k < n; k++) {
    var xa = S.x0 - 20 + k * w;
    K.strand(c, xa, xa + w, y, sag, S.hh * 0.42, function (x, by, i) {
      var col = cols[(i + k * 2) % cols.length], fl = lit ? 0.75 + 0.25 * Math.sin(S.t / 260 + i * 1.7 + k) : 0;
      if (lit) K.lanternGlow(c, x, by + 6, 4, [44, 18, 50, 340, 200][(i + k * 2) % 5], fl);
      c.fillStyle = '#3a2a20'; c.fillRect(x - 1.6, by, 3.2, 3);
      c.fillStyle = lit ? col : 'rgba(255,255,255,.55)'; c.beginPath(); c.ellipse(x, by + 6.5, 3.4, 4.4, 0, 0, TAU); c.fill();
      if (!lit) { c.strokeStyle = 'rgba(80,60,40,.5)'; c.lineWidth = 0.8; c.stroke(); }
    });
  }
  if (lit) for (var m = 0; m < 2; m++) {   /* moths round the warmest bulb */
    var mx = S.x0 + w * (0.5 + m) - 20, my = y + sag + 8, a = S.t / (430 + m * 90) + m * 2;
    var px = mx + Math.cos(a) * 14, py = my + Math.sin(a * 1.3) * 9, f = Math.abs(Math.sin(S.t / 45 + m)) * 3 + 1;
    c.fillStyle = 'rgba(240,226,200,.85)'; c.beginPath(); c.ellipse(px - 2, py, f, 2.4, -0.5, 0, TAU); c.ellipse(px + 2, py, f, 2.4, 0.5, 0, TAU); c.fill();
  }
});

/* parking: the blue P on its post and scooters nosed in at the kerb */
D.addProp('parking', function (S) {
  var c = S.c, u = S.hh, ky = kerb(S), x = S.x0 + u * 1.05, r = K.rnd(S.seed ^ 0x5a17);
  paper(c, rect(x - 1.5, S.deck - u * 1.25, 3, u * 1.25 + (ky - S.deck)), '#8a8f96', 0.6);
  var s = u * 0.36, sy = S.deck - u * 1.25 - s * 0.5;
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - s / 2, sy, s, s, s * 0.14) : q.rect(x - s / 2, sy, s, s); }, '#1f5fb8', 1);
  c.strokeStyle = '#fff'; c.lineWidth = 1.2; c.strokeRect(x - s / 2 + 2.5, sy + 2.5, s - 5, s - 5);
  c.fillStyle = '#fff'; c.font = '900 ' + Math.round(s * 0.72) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('P', x, sy + s * 0.54);
  var cols = ['#c8372d', '#2f6f9f', '#e8e2d0', '#1d1d22', '#e39b2b', '#7aa65a', '#d86aa0'], n = S.phone ? 2 : 3;
  if (S.set === 'busstop') return;   /* the bus has the kerb */
  for (var i = 0; i < n; i++) scooter(c, x + u * 0.55 + i * u * 0.62, ky, u * 0.5, cols[Math.floor(r() * cols.length)], r() < 0.5, S.night);
});
function scooter(c, x, y, s, col, helmet, night) {
  var wr = s * 0.17;
  [x - s * 0.36, x + s * 0.36].forEach(function (wx, i) { paper(c, function (q) { circ(q, wx, y - wr, wr, 7 + i); }, '#1a1a1e', 0.6); c.fillStyle = '#9aa0a8'; c.beginPath(); c.arc(wx, y - wr, wr * 0.38, 0, TAU); c.fill(); });
  paper(c, poly([[x - s * 0.5, y - wr * 1.5], [x - s * 0.42, y - s * 0.5], [x - s * 0.05, y - s * 0.52], [x + s * 0.05, y - s * 0.32], [x + s * 0.24, y - s * 0.34], [x + s * 0.3, y - s * 0.86],
    [x + s * 0.42, y - s * 0.86], [x + s * 0.44, y - s * 0.3], [x + s * 0.5, y - wr * 1.4], [x + s * 0.2, y - wr * 1.2], [x - s * 0.2, y - wr * 1.2]]), col, 0.8);
  paper(c, poly([[x - s * 0.44, y - s * 0.5], [x - s * 0.4, y - s * 0.6], [x - s * 0.04, y - s * 0.6], [x - s * 0.02, y - s * 0.52]]), '#2a2220', 0.5);
  c.strokeStyle = '#2a2a2e'; c.lineWidth = 2; c.beginPath(); c.moveTo(x + s * 0.28, y - s * 0.88); c.lineTo(x + s * 0.48, y - s * 0.9); c.stroke();
  c.fillStyle = night ? '#ffe9a8' : '#f4f0e0'; c.beginPath(); c.arc(x + s * 0.44, y - s * 0.78, s * 0.05, 0, TAU); c.fill();
  if (helmet) { paper(c, function (q) { q.beginPath(); q.arc(x + s * 0.36, y - s * 0.93, s * 0.12, Math.PI, 0); q.closePath(); }, '#f2f2f2', 0.5); }
}

/* opens early: a rooster on the kerb, crowing at first light, pecking the rest of the day */
D.addProp('rooster', function (S) {
  var c = S.c, u = S.hh * 0.48, ky = S.deck + (S.H - S.deck) * 0.5, x = S.x1 - S.span * (S.phone ? 0.22 : 0.17), h = clock(S), t = S.t;
  var dawn = h >= 4.5 && h < 9, crow = dawn && (t % 6000) < 2600, peck = !dawn && Math.sin(t / 700) > 0.55;
  c.save(); c.translate(x, ky); var sc = u / 40; c.scale(-sc, sc);   /* faces the shop */
  [-6, 4].forEach(function (lx, i) { c.strokeStyle = '#d99a2b'; c.lineWidth = 2.2; c.beginPath(); c.moveTo(lx, -14); c.lineTo(lx + (i ? 2 : -1), 0); c.lineTo(lx + (i ? 7 : 4), 0); c.stroke(); });
  var tail = Math.sin(t / 900) * 0.08;   /* the sickle feathers, green-black and copper */
  [['#1e3b2e', 0], ['#0f2420', 0.22], ['#7a2a14', 0.44], ['#1e3b2e', 0.66]].forEach(function (f, i) {
    paper(c, function (q) { q.save(); q.translate(-14, -26); q.rotate(-0.5 + f[1] + tail); q.beginPath(); q.moveTo(0, 0); q.quadraticCurveTo(-26, -24, -30, 6 + i * 2); q.quadraticCurveTo(-20, -10, 0, 6); q.closePath(); q.restore(); }, f[0], 0.6);
  });
  paper(c, function (q) { q.beginPath(); q.ellipse(0, -24, 17, 12, -0.15, 0, TAU); }, '#b8461e', 1);
  paper(c, function (q) { q.beginPath(); q.ellipse(-3, -23, 10, 7, -0.25, 0, TAU); }, '#6a2412', 0.4);   /* the wing */
  var hx = peck ? 18 : 14, hy = peck ? -14 : crow ? -46 : -40, nr = crow ? -0.5 : 0;
  paper(c, poly([[8, -30], [hx - 2, hy + 4], [hx + 6, hy + 2], [14, -24]]), '#e07a24', 0.6);   /* the hackles */
  c.save(); c.translate(hx, hy); c.rotate(nr);
  paper(c, function (q) { circ(q, 0, 0, 6, 5); }, '#c4561f', 0.6);
  paper(c, function (q) { q.beginPath(); q.moveTo(-4, -4); for (var k = 0; k < 4; k++) { q.lineTo(-3 + k * 2.6, -10 - (k % 2) * 2); q.lineTo(-2 + k * 2.6, -5); } q.closePath(); }, '#e22d2d', 0.4);
  c.fillStyle = '#e22d2d'; c.beginPath(); c.ellipse(4, 6, 2, 3.4, 0, 0, TAU); c.fill();
  c.fillStyle = '#e8b13a'; c.beginPath(); c.moveTo(5, -2); c.lineTo(11, crow ? -3 : 0); c.lineTo(5, 1); c.fill();
  if (crow) { c.beginPath(); c.moveTo(5, 1); c.lineTo(10, 4); c.lineTo(5, 2.5); c.fill(); }
  c.fillStyle = '#111'; c.beginPath(); c.arc(1.5, -1.5, 1.3, 0, TAU); c.fill();
  c.restore();
  if (crow) { c.strokeStyle = 'rgba(255,248,220,.9)'; c.lineWidth = 1.6; for (var a = 0; a < 3; a++) { var rr = 10 + a * 7 + (t % 600) / 60; c.beginPath(); c.arc(hx + 10, hy - 4, rr, -0.9, 0.5); c.stroke(); } }
  c.restore();
});

/* air-con: the outdoor unit on the kerb, its fan turning, heat shimmering off it, the drain pipe
   dripping into a puddle */
D.addProp('aircon', function (S) {
  var c = S.c, u = S.hh * 0.62, gy = S.deck + (S.H - S.deck) * 0.42, x = S.x0 + S.span * (S.phone ? 0.2 : 0.16), w = u * 1.1, h = u * 0.78, y = gy - h - u * 0.08;
  paper(c, rect(x - w * 0.42, gy - u * 0.1, u * 0.08, u * 0.1), '#5a5f66', 0.3); paper(c, rect(x + w * 0.34, gy - u * 0.1, u * 0.08, u * 0.1), '#5a5f66', 0.3);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w / 2, y, w, h, u * 0.05) : q.rect(x - w / 2, y, w, h); }, '#ecebe4', 1.1);
  var fx = x - w * 0.14, fy = y + h / 2, fr = h * 0.36;
  c.fillStyle = '#3b3f45'; c.beginPath(); c.arc(fx, fy, fr, 0, TAU); c.fill();
  c.save(); c.translate(fx, fy); c.rotate(S.t / 90); c.fillStyle = '#8a9099';
  for (var b = 0; b < 3; b++) { c.rotate(TAU / 3); c.beginPath(); c.ellipse(fr * 0.45, 0, fr * 0.45, fr * 0.16, 0.4, 0, TAU); c.fill(); }
  c.restore();
  c.strokeStyle = 'rgba(30,30,30,.55)'; c.lineWidth = 1; for (var g = -3; g <= 3; g++) { c.beginPath(); c.moveTo(fx + g * fr * 0.3, fy - fr * Math.sqrt(Math.max(0, 1 - g * g * 0.09))); c.lineTo(fx + g * fr * 0.3, fy + fr * Math.sqrt(Math.max(0, 1 - g * g * 0.09))); c.stroke(); }
  c.beginPath(); c.arc(fx, fy, fr, 0, TAU); c.stroke();
  c.strokeStyle = 'rgba(80,80,80,.45)'; for (var l = 0; l < 5; l++) { c.beginPath(); c.moveTo(x + w * 0.16, y + h * (0.22 + l * 0.13)); c.lineTo(x + w * 0.42, y + h * (0.22 + l * 0.13)); c.stroke(); }
  c.strokeStyle = '#d8d4c8'; c.lineWidth = 2.4; c.beginPath(); c.moveTo(x + w * 0.5, y + h * 0.3); c.quadraticCurveTo(x + w * 0.66, y + h * 0.3, x + w * 0.66, gy - u * 0.04); c.stroke();
  var dp = (S.t % 1400) / 1400, dx = x + w * 0.66;   /* the drip, and its puddle */
  c.fillStyle = 'rgba(120,180,230,.85)'; c.beginPath(); c.ellipse(dx, gy - u * 0.02 + dp * u * 0.12, 1.6, 2.4, 0, 0, TAU); c.fill();
  c.fillStyle = 'rgba(120,170,220,.35)'; c.beginPath(); c.ellipse(dx + 2, gy + u * 0.12, u * 0.22, u * 0.05, 0, 0, TAU); c.fill();
  if (!S.night) { c.strokeStyle = 'rgba(255,255,255,.35)'; c.lineWidth = 1.2;   /* hot air off the back */
    for (var k = 0; k < 3; k++) { var hx = x - w * 0.3 + k * w * 0.22, ph = S.t / 500 + k; c.beginPath();
      for (var j = 0; j <= 10; j++) { var yy = y - 4 - j * u * 0.05; j ? c.lineTo(hx + Math.sin(ph + j * 0.9) * 3, yy) : c.moveTo(hx + Math.sin(ph) * 3, yy); } c.stroke(); } }
});

/* wi-fi: a standing sign with the wifi symbol */
D.addProp('wifi', function (S) {
  var c = S.c, u = S.hh * 0.6, ky = S.deck + (S.H - S.deck) * 0.35, x = S.x1 - S.span * (S.phone ? 0.08 : 0.08), y = ky - u * 1.5;
  paper(c, rect(x - 2, y, 4, ky - y), '#8c7362', 0.5);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - u*0.6, y - u*0.8, u*1.2, u*0.9, 4) : q.rect(x - u*0.6, y - u*0.8, u*1.2, u*0.9); }, '#3a3a40', 0.8);
  c.strokeStyle = '#fff'; c.lineCap = 'round'; c.lineWidth = 3;
  for (var i = 1; i <= 3; i++) {
    c.beginPath(); c.arc(x, y - u*0.2, i * u * 0.18, -Math.PI*0.75, -Math.PI*0.25); c.stroke();
  }
  c.fillStyle = '#fff'; c.beginPath(); c.arc(x, y - u*0.2, 3, 0, TAU); c.fill();
});

/* pool: a small pool of water on the kerb with a life ring */
D.addProp('pool', function (S) {
  var c = S.c, u = S.hh * 0.8, ky = S.deck + (S.H - S.deck) * 0.35, x = S.x0 + S.span * (S.phone ? 0.28 : 0.26);
  c.fillStyle = S.night ? 'rgba(40, 100, 150, 0.7)' : 'rgba(70, 160, 210, 0.7)';
  c.beginPath(); c.ellipse(x, ky, u * 1.2, u * 0.4, 0, 0, TAU); c.fill();
  c.strokeStyle = 'rgba(255, 255, 255, 0.4)'; c.lineWidth = 1.5;
  c.beginPath(); c.ellipse(x, ky, u * 1.1, u * 0.3, 0, 0, Math.PI); c.stroke();
  c.save(); c.translate(x - u * 0.6, ky + u * 0.1); c.scale(1, 0.4); c.rotate(-0.2);
  c.strokeStyle = '#e64539'; c.lineWidth = 6;
  c.beginPath(); c.arc(0, 0, u * 0.4, 0, Math.PI / 2); c.stroke();
  c.beginPath(); c.arc(0, 0, u * 0.4, Math.PI, Math.PI * 1.5); c.stroke();
  c.strokeStyle = '#f2f2f2';
  c.beginPath(); c.arc(0, 0, u * 0.4, Math.PI / 2, Math.PI); c.stroke();
  c.beginPath(); c.arc(0, 0, u * 0.4, Math.PI * 1.5, TAU); c.stroke();
  c.restore();
});

/* farm: a patch of rice stalks or crops */
D.addProp('farm', function (S) {
  var c = S.c, u = S.hh * 0.5, ky = S.deck + (S.H - S.deck) * 0.4, x = S.x1 - S.span * (S.phone ? 0.28 : 0.28);
  c.fillStyle = S.night ? '#3a2e20' : '#6e5a40';
  c.beginPath(); c.ellipse(x, ky, u * 1.5, u * 0.5, 0, 0, TAU); c.fill();
  c.strokeStyle = S.night ? '#4a702a' : '#76a845'; c.lineWidth = 2; c.lineCap = 'round';
  var r = K.rnd(S.seed ^ 0x1234);
  for (var i = 0; i < 15; i++) {
    var px = x - u * 1.2 + r() * u * 2.4;
    var py = ky - u * 0.2 + r() * u * 0.4;
    var th = r() * 0.4 - 0.2 + Math.sin(S.t / 800 + i) * 0.1;
    var h = u * (0.8 + r() * 0.5);
    c.beginPath(); c.moveTo(px, py); c.quadraticCurveTo(px + Math.sin(th)*h, py - h, px + Math.sin(th)*h*1.2, py - h*1.1); c.stroke();
  }
});

/* coin water kiosk: a tall white/blue dispenser with a nozzle and a coin slot */
D.addProp('water', function (S) {
  var c = S.c, u = S.hh * 0.7, gy = S.deck + (S.H - S.deck) * 0.35, x = S.x0 + S.span * (S.phone ? 0.12 : 0.10), w = u * 0.8, h = u * 1.6, y = gy - h;
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w / 2, y, w, h, u * 0.1) : q.rect(x - w / 2, y, w, h); }, '#f4f6f8', 1);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w / 2, y, w, h * 0.25, u * 0.1) : q.rect(x - w / 2, y, w, h * 0.25); }, '#1c6ab8', 1);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w * 0.35, y + h * 0.3, w * 0.7, h * 0.45, u * 0.05) : q.rect(x - w * 0.35, y + h * 0.3, w * 0.7, h * 0.45); }, '#c8d4e0', 1);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w * 0.25, y + h * 0.35, w * 0.5, h * 0.3, u * 0.05) : q.rect(x - w * 0.25, y + h * 0.35, w * 0.5, h * 0.3); }, '#a6b8c9', 0.8);
  c.fillStyle = '#687582'; c.beginPath(); c.arc(x, y + h * 0.45, u * 0.08, 0, TAU); c.fill(); /* nozzle */
  c.strokeStyle = '#4b5561'; c.lineWidth = u * 0.04; c.beginPath(); c.moveTo(x + w * 0.2, y + h * 0.35); c.lineTo(x + w * 0.2, y + h * 0.45); c.stroke(); /* coin slot */
});

/* tables: a simple table with two stools, street food style */
D.addProp('tables', function (S) {
  var c = S.c, u = S.hh * 0.6, gy = S.deck + (S.H - S.deck) * 0.45, x = S.x1 - S.span * (S.phone ? 0.24 : 0.22), w = u * 1.2, h = u * 0.6, y = gy - h;
  /* stools */
  var cols = ['#c74b4b', '#487ab8', '#cf8729'];
  var r = K.rnd(S.seed ^ 0x6291), c1 = cols[Math.floor(r() * cols.length)], c2 = cols[Math.floor(r() * cols.length)];
  paper(c, poly([[x - w * 0.7, gy], [x - w * 0.5, gy], [x - w * 0.55, gy - h * 0.6], [x - w * 0.65, gy - h * 0.6]]), c1, 0.9);
  paper(c, poly([[x + w * 0.5, gy], [x + w * 0.7, gy], [x + w * 0.65, gy - h * 0.6], [x + w * 0.55, gy - h * 0.6]]), c2, 0.9);
  /* table legs */
  paper(c, rect(x - w * 0.4, gy - h, u * 0.08, h), '#a4a8ab', 1);
  paper(c, rect(x + w * 0.32, gy - h, u * 0.08, h), '#a4a8ab', 1);
  /* table top */
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w / 2, y, w, u * 0.15, u * 0.05) : q.rect(x - w / 2, y, w, u * 0.15); }, '#dedbcf', 1);
  /* bowl/plate on table */
  c.fillStyle = '#f4f6f8'; c.beginPath(); c.ellipse(x, y - u * 0.05, u * 0.2, u * 0.1, 0, 0, TAU); c.fill();
});

/* bubble tea: a large cup of boba with a big straw */
D.addProp('bubbletea', function (S) {
  var c = S.c, u = S.hh * 0.5, gy = S.deck + (S.H - S.deck) * 0.4, x = S.x1 - S.span * (S.phone ? 0.12 : 0.12), w = u * 0.6, h = u * 1.2, y = gy - h;
  /* shadow */
  c.fillStyle = 'rgba(0,0,0,0.2)'; c.beginPath(); c.ellipse(x, gy, w * 0.8, u * 0.15, 0, 0, TAU); c.fill();
  /* cup */
  c.fillStyle = '#fce4be'; c.beginPath(); c.moveTo(x - w * 0.4, gy); c.lineTo(x + w * 0.4, gy); c.lineTo(x + w * 0.5, y); c.lineTo(x - w * 0.5, y); c.fill();
  /* pearls */
  c.fillStyle = '#2c1e16';
  var r = K.rnd(S.seed ^ 0xb0ba);
  for (var i = 0; i < 15; i++) {
    c.beginPath(); c.arc(x - w * 0.3 + r() * w * 0.6, gy - u * 0.1 - r() * u * 0.25, u * 0.08, 0, TAU); c.fill();
  }
  /* lid */
  c.fillStyle = '#ffffff'; c.beginPath(); c.ellipse(x, y, w * 0.5, u * 0.1, 0, 0, TAU); c.fill();
  c.beginPath(); c.ellipse(x, y - u * 0.1, w * 0.45, u * 0.08, 0, 0, TAU); c.fill();
  /* straw */
  paper(c, poly([[x - u * 0.08, gy - u * 0.2], [x + u * 0.08, gy - u * 0.2], [x + u * 0.1, y - u * 0.6], [x - u * 0.1, y - u * 0.6]]), '#222', 1);
});

/* camp: a couple of tents on the kerb */
D.addProp('camp', function (S) {
  var c = S.c, u = S.hh * 0.7, gy = S.deck + (S.H - S.deck) * 0.35, x = S.x1 - S.span * (S.phone ? 0.25 : 0.25);
  c.fillStyle = 'rgba(0,0,0,0.15)'; c.beginPath(); c.ellipse(x, gy, u * 1.5, u * 0.3, 0, 0, TAU); c.fill();
  paper(c, poly([[x - u * 0.6, gy], [x + u * 0.4, gy], [x - u * 0.1, gy - u]]), '#4a7050', 0.8);
  paper(c, poly([[x - u * 1.2, gy + u * 0.1], [x + u * 0.2, gy + u * 0.1], [x - u * 0.5, gy - u * 1.1]]), '#8c9c64', 0.9);
  paper(c, poly([[x - u * 0.5, gy - u * 1.1], [x - u * 0.8, gy + u * 0.1], [x - u * 0.2, gy + u * 0.1]]), '#2a3a2a', 0.6);
  if (S.night) {
    c.fillStyle = 'rgba(255, 220, 150, 0.6)';
    c.beginPath(); c.moveTo(x - u * 0.5, gy - u * 0.8); c.lineTo(x - u * 0.7, gy + u * 0.1); c.lineTo(x - u * 0.3, gy + u * 0.1); c.fill();
  }
  c.strokeStyle = '#d0d0c0'; c.lineWidth = 1;
  c.beginPath(); c.moveTo(x - u * 0.5, gy - u * 1.1); c.lineTo(x - u * 1.4, gy + u * 0.2); c.stroke();
  c.beginPath(); c.moveTo(x - u * 0.5, gy - u * 1.1); c.lineTo(x + u * 0.4, gy + u * 0.2); c.stroke();
});

/* takeaway: a cluster of plastic carrier bags with food boxes */
D.addProp('takeaway', function (S) {
  var c = S.c, u = S.hh * 0.5, gy = S.deck + (S.H - S.deck) * 0.35, x = S.x0 + S.span * (S.phone ? 0.24 : 0.20);
  c.fillStyle = 'rgba(0,0,0,0.15)'; c.beginPath(); c.ellipse(x, gy, u * 0.8, u * 0.2, 0, 0, TAU); c.fill();
  var r = K.rnd(S.seed ^ 0x6a95);
  for (var i = 0; i < 3; i++) {
    var px = x - u * 0.3 + r() * u * 0.6, py = gy - r() * u * 0.1;
    paper(c, function(q) { q.beginPath(); q.roundRect ? q.roundRect(px - u * 0.3, py - u * 0.25, u * 0.6, u * 0.25, 2) : q.rect(px - u * 0.3, py - u * 0.25, u * 0.6, u * 0.25); }, '#f0f0f0', 0.8);
    c.fillStyle = 'rgba(255, 255, 255, 0.7)';
    c.beginPath(); c.moveTo(px - u * 0.4, py); c.quadraticCurveTo(px, py - u * 0.8, px + u * 0.4, py); c.fill();
    c.strokeStyle = 'rgba(255, 255, 255, 0.8)'; c.lineWidth = 2;
    c.beginPath(); c.moveTo(px - u * 0.2, py - u * 0.6); c.quadraticCurveTo(px - u * 0.1, py - u * 0.9, px, py - u * 0.6); c.stroke();
    c.beginPath(); c.moveTo(px + u * 0.2, py - u * 0.6); c.quadraticCurveTo(px + u * 0.1, py - u * 0.9, px, py - u * 0.6); c.stroke();
  }
});

/* noodles: a kerb table with a steaming bowl of noodles */
D.addProp('noodles', function (S) {
  var c = S.c, u = S.hh * 0.6, gy = S.deck + (S.H - S.deck) * 0.4, x = S.x0 + S.span * (S.phone ? 0.30 : 0.28), w = u * 1.0, h = u * 0.5, y = gy - h;
  c.fillStyle = 'rgba(0,0,0,0.15)'; c.beginPath(); c.ellipse(x, gy, w * 0.6, u * 0.2, 0, 0, TAU); c.fill();
  paper(c, rect(x - w * 0.35, gy - h, u * 0.08, h), '#a4a8ab', 1);
  paper(c, rect(x + w * 0.27, gy - h, u * 0.08, h), '#a4a8ab', 1);
  paper(c, function (q) { q.beginPath(); q.roundRect ? q.roundRect(x - w / 2, y, w, u * 0.1, u * 0.03) : q.rect(x - w / 2, y, w, u * 0.1); }, '#b83a3a', 1);
  var bx = x, by = y - u * 0.05, br = u * 0.3;
  c.fillStyle = '#fdfdfd'; c.beginPath(); c.arc(bx, by, br, 0, Math.PI); c.fill();
  c.strokeStyle = '#4a90e2'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(bx - br * 0.8, by + br * 0.4); c.lineTo(bx + br * 0.8, by + br * 0.4); c.stroke();
  c.fillStyle = '#dcb464'; c.beginPath(); c.ellipse(bx, by, br * 0.9, br * 0.2, 0, 0, TAU); c.fill();
  c.strokeStyle = '#c49a6c'; c.lineWidth = 2; c.beginPath(); c.moveTo(bx - br * 0.6, by + br * 0.1); c.lineTo(bx + br * 1.2, by - br * 0.8); c.stroke(); c.beginPath(); c.moveTo(bx - br * 0.4, by + br * 0.1); c.lineTo(bx + br * 1.1, by - br * 0.9); c.stroke();
  c.strokeStyle = 'rgba(255,255,255,0.6)'; c.lineWidth = 1.5; c.lineCap = 'round';
  for (var k = 0; k < 2; k++) {
    var sx = bx - br * 0.3 + k * br * 0.6, sy = by - br * 0.3;
    c.beginPath();
    for (var j = 0; j < 5; j++) {
      var ssy = sy - j * u * 0.15;
      var ssx = sx + Math.sin(S.t / 300 + j + k * 2) * u * 0.1;
      j ? c.lineTo(ssx, ssy) : c.moveTo(ssx, ssy);
    }
    c.stroke();
  }
});

D.props._in = 1;
})();
