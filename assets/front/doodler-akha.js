/* Akha scenes for the auto-doodler (Nan, 2026-10-02: "Akha cultural events should look
   akha", "do an animation for akha swing festival"). The dress follows the pieces shown in
   Melodies and Motifs: the Loimi headdress of silver studs, balls and coins with bead loops,
   black jackets trimmed red and white with turquoise cuffs.
   'akha'       a village afternoon of songs: a stilt house under its deep thatch, the
                village gate with its wooden birds, singers in a line, a bamboo flute, a
                woman spinning thread on a drop spindle
   'akha-swing' the swing festival: the four-pole swing, a rider in full dress on a pendulum,
                θ = θ₀·cos(√(g/L)·t), the village gathered round */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, rect = K.rect, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

/* a house on posts under a thatch that comes down nearly to the floor; the gable's crossed
   horns; the thatch is a fan of strokes */
function house(c, x, deck, w, hh, night) {
  var fl = deck - hh * 0.55, top = deck - hh * 2.05, wood = night ? '#4a3424' : '#7a5636', thatch = night ? '#6a5a32' : '#b89a52';
  for (var i = 0; i < 5; i++) paper(c, rect(x + w * (0.08 + i * 0.21) - 2, fl, 4, deck - fl), wood, 0.8);
  paper(c, rect(x, fl - 4, w, 6), wood, 1.2);
  paper(c, rect(x + w * 0.12, fl - hh * 0.5, w * 0.76, hh * 0.5), night ? '#3a2a1c' : '#9a7a52', 1);
  if (night) { c.fillStyle = 'rgba(255,190,90,.75)'; c.fillRect(x + w * 0.45, fl - hh * 0.36, w * 0.1, hh * 0.22); }
  paper(c, poly([[x - w * 0.1, fl - hh * 0.2], [x + w * 0.5, top], [x + w * 1.1, fl - hh * 0.2]]), thatch, 1.8);
  c.strokeStyle = night ? 'rgba(30,20,10,.35)' : 'rgba(90,60,20,.35)'; c.lineWidth = 1;
  for (var k = 0; k < 26; k++) { var u = k / 25, bx = lerp(x - w * 0.1, x + w * 1.1, u); c.beginPath(); c.moveTo(x + w * 0.5, top + hh * 0.08); c.lineTo(bx, fl - hh * 0.2); c.stroke(); }
  c.strokeStyle = wood; c.lineWidth = 2.5; c.lineCap = 'round';
  c.beginPath(); c.moveTo(x + w * 0.5, top + 4); c.lineTo(x + w * 0.5 - hh * 0.25, top - hh * 0.25); c.moveTo(x + w * 0.5, top + 4); c.lineTo(x + w * 0.5 + hh * 0.25, top - hh * 0.25); c.stroke();
  /* the ladder */
  c.lineWidth = 2; c.beginPath(); c.moveTo(x + w * 0.9, deck); c.lineTo(x + w * 0.98, fl); c.moveTo(x + w * 0.98, deck); c.lineTo(x + w * 1.06, fl);
  for (k = 1; k < 4; k++) { c.moveTo(lerp(x + w * 0.9, x + w * 0.98, k / 4), lerp(deck, fl, k / 4)); c.lineTo(lerp(x + w * 0.98, x + w * 1.06, k / 4), lerp(deck, fl, k / 4)); } c.stroke();
}
/* the village gate: two posts and a beam, wooden birds along the top, woven bamboo stars hung from it */
function gate(c, x, deck, w, hh, t, night) {
  var top = deck - hh * 1.75, wood = night ? '#5a4430' : '#8a6a44';
  paper(c, rect(x - 3, top, 6, deck - top), wood, 1.2); paper(c, rect(x + w - 3, top, 6, deck - top), wood, 1.2);
  paper(c, rect(x - w * 0.12, top - 4, w * 1.24, 7), wood, 1.4);
  for (var i = 0; i < 4; i++) {
    var bx = x + w * (0.1 + i * 0.27), by = top - 5, bob = Math.sin(t / 900 + i) * 0.04;
    paper(c, function (q) { q.save(); q.translate(bx, by); q.rotate(bob); q.beginPath(); q.moveTo(-hh * 0.12, 0); q.quadraticCurveTo(-hh * 0.02, -hh * 0.14, hh * 0.08, -hh * 0.1); q.lineTo(hh * 0.16, -hh * 0.12); q.lineTo(hh * 0.09, -hh * 0.06); q.quadraticCurveTo(hh * 0.02, 0, -hh * 0.12, 0); q.closePath(); q.restore(); }, wood, 0.8);
  }
  for (i = 0; i < 3; i++) {
    var sx = x + w * (0.25 + i * 0.25), sw = Math.sin(t / 1300 + i * 1.7) * 0.18, L = hh * 0.35, sy = top + 3 + Math.cos(sw) * L, sxx = sx + Math.sin(sw) * L, z = hh * 0.08;
    c.strokeStyle = 'rgba(40,30,20,.7)'; c.lineWidth = 1; c.beginPath(); c.moveTo(sx, top + 3); c.lineTo(sxx, sy); c.stroke();
    c.strokeStyle = night ? '#c9b27a' : '#d9c48a'; c.lineWidth = 1.6; c.beginPath();
    for (var k = 0; k < 6; k++) { var a = k / 6 * TAU + t / 4000; c.moveTo(sxx + Math.cos(a) * z, sy + z + Math.sin(a) * z); c.lineTo(sxx + Math.cos(a + TAU / 3) * z, sy + z + Math.sin(a + TAU / 3) * z); } c.stroke();
  }
}
/* a drop spindle: the whorl spins, the thread runs from the raised hand */
function spindle(c, hand, low, t, hh) {
  c.strokeStyle = 'rgba(240,235,220,.9)'; c.lineWidth = 1; c.beginPath(); c.moveTo(hand[0], hand[1]); c.lineTo(low[0], low[1]); c.stroke();
  var a = t / 60;
  c.fillStyle = '#c9a26a'; c.fillRect(low[0] - 1.2, low[1], 2.4, hh * 0.16);
  c.fillStyle = 'rgba(232,200,150,.75)'; c.beginPath(); c.ellipse(low[0], low[1] + hh * 0.05, hh * 0.09 * Math.abs(Math.cos(a)) + 2, hh * 0.025, 0, 0, TAU); c.fill();
}

/* ---------------------------------------------------------------- 'akha': songs in the village */
function akha(S) {
  var Pl = S.place, Cv = D.civic, ra = K.rnd((S.seed ^ 0xa4a) >>> 0), sta = Pl ? K.openNow(Pl.hours, S.now) : null, quietA = Pl && (sta === false || sta === null && S.night);
  if (Pl && !Cv && D.need) D.need('clinic');
  var c = S.c, i, n = Math.max(2, Math.min(5, Math.floor((S.span - S.hh * 5) / (S.hh * 0.62)))), crew = K.town(S, n + 3, { akha: 1 });
  if (Pl) n = Math.max(1, Math.min(n, 1 + Math.floor(ra() * 5)));
  var hw = Math.min(S.span * 0.34, S.hh * 2.6), hx = S.x0 + S.span * 0.06, up = false, rx = -1;
  if (Pl) {   /* one place: the house's size, a second house up the slope, coffee drying on bamboo racks, dealt */
    hw = Math.min(S.span * 0.34, S.hh * (2.1 + ra() * 0.7)); hx = S.x0 + S.span * (0.05 + ra() * 0.05); up = ra() < 0.5; if (ra() < 0.6) rx = S.x0 + S.span * (0.4 + ra() * 0.12);
  }
  function still(c) {
    K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a2018' : '#8a6a44');
    if (Pl) K.setting(S);
    /* terraces behind: stepped strips of rice in two greens */
    for (var i = 0; i < 4; i++) { var ty = S.deck - S.hh * (0.15 + i * 0.12); paper(c, function (q) { jag(q, [[S.x0 - 4, ty], [S.x1 + 4, ty - S.hh * 0.04], [S.x1 + 4, ty + S.hh * 0.14], [S.x0 - 4, ty + S.hh * 0.14]], 80 + i, 2); }, S.night ? ['#1f3326', '#24402e'][i % 2] : ['#6f9a4a', '#88b05a'][i % 2], 0.6); }
    if (up) house(c, S.x0 + S.span * 0.38, S.deck - S.hh * 0.42, hw * 0.55, S.hh * 0.6, S.night);
    if (rx >= 0) for (var rk = 0; rk < 2; rk++) { var rxx = rx + rk * S.hh * 0.75; c.fillStyle = S.night ? '#5a4a2a' : '#a8843a'; c.fillRect(rxx, S.deck - S.hh * 0.32, S.hh * 0.6, S.hh * 0.04); c.fillRect(rxx + 2, S.deck - S.hh * 0.28, 3, S.hh * 0.28); c.fillRect(rxx + S.hh * 0.56, S.deck - S.hh * 0.28, 3, S.hh * 0.28);
      for (var cb = 0; cb < 12; cb++) { c.fillStyle = cb % 3 ? (S.night ? '#6a2a20' : '#b8342a') : (S.night ? '#4a3020' : '#7a4a2a'); c.beginPath(); c.arc(rxx + S.hh * (0.05 + (cb % 6) * 0.1), S.deck - S.hh * (0.35 + Math.floor(cb / 6) * 0.03), S.hh * 0.025, 0, TAU); c.fill(); } }
    house(c, hx, S.deck, hw, S.hh, S.night);
  }
  /* a place's still parts are cut once (D.civic.layer); the band draws them each frame as before */
  if (Pl && Cv) Cv.layer(S, 'akha', Cv.stageBox(S), still); else still(c);
  gate(c, S.x1 - S.hh * 2.4, S.deck, S.hh * 1.3, S.hh, S.t, S.night);
  /* the singers, side by side, swaying together; the song rises */
  var sx0 = hx + hw + S.hh * 0.6, sx1 = S.x1 - S.hh * 2.7, sway = Math.sin(S.t / 1100);
  for (i = 0; i < (quietA ? 0 : n); i++) {
    var px = lerp(sx0, sx1, n > 1 ? i / (n - 1) : 0.5), d = crew[i]; d.dir = 1;
    var P = { lean: sway * 0.06, legs: [0.06 + sway * 0.05, 0, -0.06 + sway * 0.05, 0], arms: [0.5, 1.2 + 0.2 * Math.sin(S.t / 700 + i), 0.4, 1.3] };
    K.person(c, px, S.deck + 6, S.hh, P, d);
  }
  if (!quietA) K.notes(c, lerp(sx0, sx1, 0.5), S.deck - S.hh * 1.3, S.t, 5, S.night ? '#ffe2a0' : '#fff6d6');
  /* the flute player, seated by the house */
  var f = crew[n]; f.dir = 1; f.ulo = false;
  var fp = K.person(c, hx + hw * 0.55, S.deck + 4, S.hh * 0.95, { lean: 0.1, seat: 0.24, legs: K.POSE.sit.legs, arms: [1.75, 0.5, 1.55, 0.7] }, f);
  c.strokeStyle = '#c9a26a'; c.lineWidth = Math.max(2, S.hh * 0.03); c.beginPath(); c.moveTo(fp.head[0] + S.hh * 0.05, fp.head[1] + S.hh * 0.05); c.lineTo(fp.head[0] + S.hh * 0.42, fp.head[1] + S.hh * 0.2); c.stroke();
  K.notes(c, fp.head[0] + S.hh * 0.4, fp.head[1], S.t + 900, 3, '#ffe2a0');
  /* the spinner on the house's floor */
  var sp = crew[n + 1]; sp.dir = -1;
  var spp = K.person(c, hx + hw * 0.3, S.deck - S.hh * 0.55, S.hh * 0.9, { lean: 0, seat: 0.24, legs: K.POSE.sit.legs, arms: [2.4, 0.4, 0.9, 0.6] }, sp);
  spindle(c, spp.hand[0], [spp.hand[0][0] - S.hh * 0.05, spp.hand[0][1] + S.hh * 0.45], S.t, S.hh);
  K.banner(c, (sx0 + sx1) / 2, S.deck - S.hh * 2.05, S.label, S.hh, '#c0392b', S.seed, S.hits);
  if (Pl) {   /* the place's name hung from the village gate's beam; chickens by day, the dog asleep when quiet */
    var gx = S.x1 - S.hh * 2.4 + S.hh * 0.65, gy = S.deck - S.hh * 1.6;
    if (Cv) Cv.signAt(c, S, gx, gy, Pl, S.hh * 0.75, '#3a2416', S.night && !quietA || null); else K.sign(c, gx, gy, Pl, S.hh * 0.75, '#3a2416', null);
    if (Cv) { if (!S.night) for (var ck = 0; ck < 2 + (S.seed % 2); ck++) Cv.chicken(c, S, lerp(sx0, sx1, 0.15 + ck * 0.35) + Math.sin(S.t / 3000 + ck) * S.hh * 0.2, S.deck + S.hh * (0.25 + ck % 2 * 0.1), S.hh * 0.5, ck + S.seed, S.t);
      if (quietA) Cv.dog(c, S, lerp(sx0, sx1, 0.5), S.deck + S.hh * 0.22, S.hh * 0.6, S.seed >>> 4, true, S.t); }
    S.hits.push({ k: 'place', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 2, y1: S.H });
    return;
  }
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 2, y1: S.H });
}

/* ---------------------------------------------------------------- 'akha-swing': the swing festival
   Four tall poles lashed at the top; the rope hangs L from the lashing and the rider swings
   on it, θ = θ₀·cos(√(g/L)·t) with θ₀ near 50°; she stands in the loop holding the rope. */
function swing(S) {
  var c = S.c, i, crew = K.town(S, 9, { akha: 1 });
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a2018' : '#8a6a44');
  var cx = S.x0 + S.span * 0.52, apex = S.deck - S.hh * 2.25, spread = S.hh * 1.25, wood = S.night ? '#6a5236' : '#a07a4a';
  /* the poles: two near, two far, crossing just above the lashing */
  c.save(); c.lineCap = 'round';
  [[-1, 0.8, 'rgba(0,0,0,.25)'], [1, 0.8, 'rgba(0,0,0,.25)']].forEach(function (p) { c.strokeStyle = S.night ? '#4a3a26' : '#7a5a36'; c.lineWidth = Math.max(3, S.hh * 0.06); c.beginPath(); c.moveTo(cx + p[0] * spread * 0.7, S.deck - S.hh * 0.1); c.lineTo(cx - p[0] * S.hh * 0.12, apex - S.hh * 0.18); c.stroke(); });
  [-1, 1].forEach(function (sd) { c.strokeStyle = wood; c.lineWidth = Math.max(3.5, S.hh * 0.07); c.beginPath(); c.moveTo(cx + sd * spread, S.deck + 6); c.lineTo(cx - sd * S.hh * 0.16, apex - S.hh * 0.22); c.stroke(); });
  c.restore();
  K.paper(c, function (q) { K.circ(q, cx, apex, S.hh * 0.07, 5); }, '#d9c48a', 0.8);
  /* the rider on her pendulum */
  var L = S.hh * 1.45, w0 = Math.sqrt(9.8 / 3.2), th = 0.9 * Math.cos(w0 * S.t / 1000), fx = cx + Math.sin(th) * L, fy = apex + Math.cos(th) * L;
  c.strokeStyle = '#d9c48a'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(cx - 2, apex); c.lineTo(fx - 3, fy - S.hh * 0.02); c.moveTo(cx + 2, apex); c.lineTo(fx + 3, fy - S.hh * 0.02); c.stroke();
  for (var k = 1; k <= 8; k++) { var tt = S.t - k * 45, th2 = 0.9 * Math.cos(w0 * tt / 1000); c.fillStyle = 'rgba(255,230,160,' + (0.2 * (1 - k / 8)) + ')'; c.beginPath(); c.arc(cx + Math.sin(th2) * L, apex + Math.cos(th2) * L - S.hh * 0.5, S.hh * 0.18, 0, TAU); c.fill(); }
  var rd = crew[0]; rd.man = false; rd.dir = Math.sin(w0 * S.t / 1000) > 0 ? -1 : 1;
  c.save(); c.translate(fx, fy); c.rotate(-th);
  K.person(c, 0, 0, S.hh * 0.95, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [3.05, 0, 3.2, 0] }, rd);
  c.restore();
  /* the village round it: clapping, a drum, a gong */
  var beat = S.t / 1000 * 2.2;
  for (i = 1; i < 9; i++) {
    var side = i % 2 ? -1 : 1, j = Math.ceil(i / 2), px = cx + side * (spread + S.hh * 0.25 + j * S.hh * 0.5), d = crew[i]; d.dir = -side;
    if (px < S.x0 + S.hh * 0.4 || px > S.x1 - S.hh * 0.9) continue;
    var clap = Math.abs(Math.sin(beat * Math.PI + i));
    K.person(c, px, S.deck + 6 + (j % 2) * 4, S.hh * (0.92 + (i % 3) * 0.03), { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.2 + clap * 0.3, 0.8 - clap * 0.4, 1.1 + clap * 0.3, 0.9 - clap * 0.4] }, d);
  }
  gate(c, S.x0 + S.hh * 0.9, S.deck, S.hh * 1.2, S.hh, S.t, S.night);
  K.banner(c, cx, S.deck + S.hh * 0.12, S.label, S.hh, '#c0392b', S.seed, S.hits);
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: apex, y1: S.H });
}

D.addScene('akha-swing', swing, /swing festival|โล้ชิงช้า|ชิงช้าอาข่า|yeh ?ku ?ja|yae ?khu ?(ja|za)|แยะขู่จ่ะ/i, 'θ = θ₀·cos(√(g/L)·t)', 1);
D.addScene('akha', akha, /\bakha\b|อาข่า|อ่าข่า/i, 'y = sin x (the song)', 2);
})();
