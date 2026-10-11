/* The cover doodles: the drawings above the front page's map, one per kind of
   event (Nan, 2026-10-01). Shared by the front page (front.js), the stills
   (make_doodle_stills.py → assets/doodles/<kind>.png) and anything without a
   picture of its own that one of them fits (data/curated/doodles.json, kinds).
   draw(kind, c, W, H, t, moon, ridge): t in ms; moon and ridge may be null. */
(function () {
'use strict';
function rnd(seed) { return function () { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }; }
var K = {
  /* a rooftop Latin night: string lights hung as catenaries, y = a·cosh(x/a);
     the leader walks a lemniscate of Gerono, x = sin t, y = sin t·cos t; the
     follower turns about the leader at three times the beat; the ridge is Doi
     Suthep's own heights along Tha Phae's latitude; the moon is tonight's. */
  'latin-night': function (c, W, Hh, t, moon, ridge) {
    /* the paper-cut version, with the city's sights and six couples (skyline.js) */
    if (window.MDSKY) return window.MDSKY.latinNightScene(c, W, Hh, t, moon, ridge);
    var g = c.createLinearGradient(0, 0, 0, Hh);
    g.addColorStop(0, '#0d0820'); g.addColorStop(0.62, '#3a1240'); g.addColorStop(1, '#7a2a3a');
    c.fillStyle = g; c.fillRect(0, 0, W, Hh);
    var r = rnd(7), i;
    for (i = 0; i < 90; i++) { var sx = r() * W, sy = r() * Hh * 0.55, tw = 0.35 + 0.35 * Math.sin(t / 700 + i); c.fillStyle = 'rgba(255,255,255,' + tw + ')'; c.fillRect(sx, sy, 1.5, 1.5); }
    if (moon) {
      var mx = W * (W < 560 ? 0.1 : 0.88), my = Hh * (W < 560 ? 0.09 : 0.2), mr = Math.min(22, Hh * 0.08);
      c.fillStyle = '#fff3d0'; c.beginPath(); c.arc(mx, my, mr, 0, 7); c.fill();
      c.save(); c.beginPath(); c.arc(mx, my, mr, 0, 7); c.clip();
      c.fillStyle = '#1a0d2c'; c.beginPath(); c.arc(mx + (moon.waxing ? -1 : 1) * 2 * mr * moon.illum, my, mr * 1.03, 0, 7); c.fill(); c.restore();
    }
    var phone = W < 560, roof = Hh * (phone ? 0.42 : 0.86), R = ridge, base = roof - Hh * (phone ? 0.1 : 0.16);
    c.fillStyle = '#1b0f26'; c.beginPath(); c.moveTo(0, Hh);
    for (var x = 0; x <= W; x += 3) {
      var y;
      if (R && R.ele) { var lng = 98.83 + (x / W) * 0.17, k = Math.max(0, Math.min(R.ele.length - 1, Math.round((lng - R.lon_a) / R.step))); y = base - (R.ele[k] - 300) / 1400 * Hh * (phone ? 0.24 : 0.38); }
      else y = base - (Math.sin(x * 0.004 + 1) * 18 + Math.sin(x * 0.011) * 9);
      c.lineTo(x, y);
    }
    c.lineTo(W, Hh); c.fill();
    c.fillStyle = '#0b0712'; c.fillRect(0, roof, W, Hh - roof);
    c.strokeStyle = 'rgba(255,200,140,.25)'; c.lineWidth = 1; c.beginPath(); c.moveTo(0, roof); c.lineTo(W, roof); c.stroke();
    var poles = [0.03, 0.36, 0.68, 0.99].map(function (p) { return p * W; }), top = roof - Hh * (phone ? 0.32 : 0.58), sag = Hh * (phone ? 0.1 : 0.16);
    c.strokeStyle = 'rgba(255,255,255,.18)'; c.lineWidth = 2;
    poles.forEach(function (px) { c.beginPath(); c.moveTo(px, top - 4); c.lineTo(px, roof); c.stroke(); });
    for (i = 0; i < poles.length - 1; i++) {
      var x0 = poles[i], x1 = poles[i + 1], xm = (x0 + x1) / 2, half = (x1 - x0) / 2, a = half / 1.4, ch = Math.cosh(half / a) - 1;
      var cat = function (x) { return top + sag - sag * (Math.cosh((x - xm) / a) - 1) / ch; };
      c.strokeStyle = 'rgba(40,20,30,.9)'; c.lineWidth = 1.2; c.beginPath();
      for (x = x0; x <= x1; x += 4) x === x0 ? c.moveTo(x, cat(x)) : c.lineTo(x, cat(x)); c.stroke();
      for (x = x0 + 12, k = 0; x < x1 - 6; x += 24, k++) {
        var yb = cat(x) + 5, on = 0.55 + 0.45 * Math.sin(t / 380 + k * 1.7 + i), hue = [42, 340, 190, 55][(k + i) % 4];
        var gb = c.createRadialGradient(x, yb, 0, x, yb, 14); gb.addColorStop(0, 'hsla(' + hue + ',100%,70%,' + 0.55 * on + ')'); gb.addColorStop(1, 'hsla(' + hue + ',100%,60%,0)');
        c.fillStyle = gb; c.beginPath(); c.arc(x, yb, 14, 0, 7); c.fill();
        c.fillStyle = 'hsla(' + hue + ',100%,85%,' + (0.5 + 0.5 * on) + ')'; c.beginPath(); c.arc(x, yb, 2.6, 0, 7); c.fill();
      }
    }
    var cx = W * (phone ? 0.62 : 0.72), cy = roof - 4, A = Math.min(W * 0.12, 130), beat = t / 1000 * Math.PI * 2 / 1.8;
    function lead(T) { return [cx + A * Math.sin(T / 2), cy - 6 + A * 0.18 * Math.sin(T / 2) * Math.cos(T / 2)]; }
    function follow(T) { var L = lead(T); return [L[0] + 26 * Math.cos(T * 1.5), L[1] - 3 + 8 * Math.sin(T * 1.5)]; }
    [[lead, 'rgba(255,194,102,'], [follow, 'rgba(255,90,140,']].forEach(function (d) {
      c.lineWidth = 2; for (var n = 40; n > 0; n--) { var p = d[0](beat - n * 0.05), q = d[0](beat - (n - 1) * 0.05); c.strokeStyle = d[1] + (0.5 * (1 - n / 40)) + ')'; c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); c.stroke(); }
    });
    var L = lead(beat), F = follow(beat), hh = Math.min(58, Hh * (phone ? 0.13 : 0.2));
    function body(p, col, skirt) {
      c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 3; c.lineCap = 'round';
      c.beginPath(); c.moveTo(p[0] - 5, p[1]); c.lineTo(p[0], p[1] - hh * 0.45); c.lineTo(p[0] + 5, p[1]); c.stroke();
      c.beginPath(); c.moveTo(p[0], p[1] - hh * 0.45); c.lineTo(p[0], p[1] - hh * 0.85); c.stroke();
      if (skirt) { var sw = 8 + 7 * Math.abs(Math.sin(beat * 1.5)); c.beginPath(); c.moveTo(p[0], p[1] - hh * 0.62); c.lineTo(p[0] - sw, p[1] - hh * 0.3); c.lineTo(p[0] + sw, p[1] - hh * 0.3); c.fill(); }
      c.beginPath(); c.arc(p[0], p[1] - hh, hh * 0.13, 0, 7); c.fill();
    }
    body(L, '#ffc266', false); body(F, '#ff5a8c', true);
    c.strokeStyle = 'rgba(255,255,255,.6)'; c.lineWidth = 2; c.beginPath(); c.moveTo(L[0], L[1] - hh * 0.75); c.lineTo(F[0], F[1] - hh * 0.75); c.stroke();
  },
  /* the loom from Warp and Weft (nanobotco.github.io/warp-and-weft), set in a Lanna room
     with a weaver at it (WV below) */
  'weaving': function (c, W, Hh, t) { WV.draw(c, W, Hh, t); },
  /* the strands from Melodies and Motifs (motdang.net/sites/melodies-and-motifs), with the
     whole headdress and its singer in front of them (AK below) */
  'akha': function (c, W, Hh, t) { AK(c, W, Hh, t); }
};

/* shared by the two minisite drawings: a 1200 × 630 sheet scaled to cover the frame,
   layers drawn once per size, sprites once per scale */
var SHEET = { k: 1 }, LAYERS = {}, SPRITES = {};
function devScale(c) { try { return Math.abs(c.getTransform().a) || 1; } catch (e) { return 1; } }
function cover(W, H) { var s = Math.max(W / 1200, H / 630); return { s: s, ox: (W / s - 1200) / 2, oy: (H / s - 630) / 2 }; }
function view(c, V) { V.d = devScale(c); SHEET.k = V.d * V.s; c.scale(V.s, V.s); c.translate(V.ox, V.oy); }
function layer(c, key, W, H, V, fn) {
  var id = key + W + 'x' + H + '@' + V.d, L = LAYERS[id];
  if (!L) {
    if (Object.keys(LAYERS).length > 12) LAYERS = {};
    L = LAYERS[id] = document.createElement('canvas'); L.width = Math.round(W * V.d); L.height = Math.round(H * V.d);
    var x = L.getContext('2d'); x.scale(V.d * V.s, V.d * V.s); x.translate(V.ox, V.oy); fn(x);
  }
  c.save(); c.translate(-V.ox, -V.oy); c.scale(1 / V.s, 1 / V.s); c.drawImage(L, 0, 0, W, H); c.restore();
}
function spr(key, w, h, fn) {
  var k = Math.min(4, Math.max(0.25, Math.round(SHEET.k * 8) / 8)), id = key + '@' + k, S = SPRITES[id];
  if (!S) { S = SPRITES[id] = document.createElement('canvas'); S.width = Math.ceil(w * k); S.height = Math.ceil(h * k); var x = S.getContext('2d'); x.scale(k, k); fn(x); }
  return S;
}

/* ---- Warp and Weft's loom: the shawl's plan and the cloth renderer are ported from weave.js;
   the scene around them is motdang's own ---- */
var WV = (function () {
  var HEX = ['#2e1c14', '#e9a53c', '#d8701e', '#9c3a1c', '#17897f', '#df5f9c', '#ece5d6', '#1a100b'];
  var RGB = HEX.map(function (h) { return [1, 3, 5].map(function (i) { return parseInt(h.substr(i, 2), 16); }); });
  var GOLD = 1, OR = 2, RUST = 3, TEAL = 4, PINK = 5, WH = 6, BK = 7;
  var KHMER = '"Noto Sans Khmer","Khmer Sangam MN","Khmer MN","Khmer UI",sans-serif', KOU = 'គោ';
  function hash(a, b) {
    var h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }
  function noise1(x, s) { var i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return hash(i, s) * (1 - u) + hash(i + 1, s) * u; }
  function mod(a, n) { return ((a % n) + n) % n; }
  function nearest(r, g, b) {
    var best = 1, bd = 1e9;
    for (var k = 1; k < 7; k++) { var q = RGB[k], d = (r - q[0]) * (r - q[0]) + (g - q[1]) * (g - q[1]) + (b - q[2]) * (b - q[2]); if (d < bd) { bd = d; best = k; } }
    return best;
  }
  /* draw with canvas paths at 4× then read one colour per cell: a picture becomes a plan for threads */
  function raster(W, H, draw) {
    var S = 4, cv = document.createElement('canvas'); cv.width = W * S; cv.height = H * S;
    var x = cv.getContext('2d'); x.scale(S, S); draw(x);
    var d = x.getImageData(0, 0, W * S, H * S).data, out = new Uint8Array(W * H);
    for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
      var p = ((j * S + 2) * W * S + i * S + 2) * 4;
      out[j * W + i] = d[p + 3] < 110 ? 0 : nearest(d[p], d[p + 1], d[p + 2]);
    }
    return { W: W, H: H, d: out };
  }
  /* motifs, after the shawl */
  function star(x, cx, cy, r, col) {
    x.strokeStyle = HEX[col || TEAL]; x.lineWidth = 1.15; x.lineCap = 'round'; x.beginPath();
    for (var k = 0; k < 8; k++) { var a = k * Math.PI / 4, rr = k % 2 ? r * 0.62 : r; x.moveTo(cx, cy); x.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); }
    x.stroke();
  }
  function flower(x, cx, cy, r) {
    x.fillStyle = HEX[PINK];
    for (var k = 0; k < 4; k++) { var a = k * Math.PI / 2; x.beginPath(); x.arc(cx + Math.cos(a) * r * 0.55, cy + Math.sin(a) * r * 0.55, r * 0.47, 0, 7); x.fill(); }
    x.fillStyle = HEX[TEAL]; x.beginPath(); x.arc(cx, cy, r * 0.3, 0, 7); x.fill();
  }
  function bloom(x, cx, cy, r, col) {
    x.fillStyle = HEX[col || OR]; x.beginPath(); x.arc(cx, cy, r * 0.62, 0, 7); x.fill();
    for (var k = 0; k < 6; k++) { var a = k * Math.PI / 3; x.beginPath(); x.arc(cx + Math.cos(a) * r, cy + Math.sin(a) * r, r * 0.3, 0, 7); x.fill(); }
    x.fillStyle = HEX[RUST]; x.beginPath(); x.arc(cx, cy, r * 0.28, 0, 7); x.fill();
  }
  function sprig(x, cx, cy, r) {
    x.strokeStyle = HEX[WH]; x.lineWidth = 1; x.lineCap = 'round'; x.beginPath();
    x.moveTo(cx, cy - r); x.lineTo(cx, cy + r);
    for (var k = -1; k <= 1; k++) { var y = cy + k * r * 0.6; x.moveTo(cx, y); x.lineTo(cx - r * 0.6, y - r * 0.35); x.moveTo(cx, y); x.lineTo(cx + r * 0.6, y - r * 0.35); }
    x.stroke();
  }
  /* a standing humped cow (zebu) facing left, in a 100 × 70 box, after the shawl */
  function cow(x, ox, oy, s) {
    x.save(); x.translate(ox, oy); x.scale(s, s);
    x.fillStyle = HEX[GOLD]; x.strokeStyle = HEX[GOLD]; x.beginPath();
    x.moveTo(24, 20); x.bezierCurveTo(27, 5, 41, 5, 44, 18); x.lineTo(84, 20); x.bezierCurveTo(91, 22, 92, 35, 86, 43);
    x.lineTo(86, 68); x.lineTo(80, 68); x.lineTo(79, 49); x.lineTo(75, 49); x.lineTo(74, 68); x.lineTo(68, 68); x.lineTo(68, 47);
    x.bezierCurveTo(58, 51, 45, 51, 37, 47); x.lineTo(37, 68); x.lineTo(31, 68); x.lineTo(30, 50); x.lineTo(28, 50); x.lineTo(27, 68); x.lineTo(21, 68); x.lineTo(21, 44);
    x.bezierCurveTo(16, 45, 12, 41, 10, 36); x.lineTo(4, 38); x.lineTo(1, 34); x.lineTo(2, 26); x.lineTo(8, 18);
    x.lineTo(5, 9); x.lineTo(10, 12); x.lineTo(13, 17); x.lineTo(19, 15); x.bezierCurveTo(21, 18, 22, 20, 24, 20);
    x.closePath(); x.fill();
    x.lineWidth = 2.6; x.lineCap = 'round'; x.beginPath(); x.moveTo(88, 24); x.quadraticCurveTo(96, 34, 93, 58); x.stroke();
    x.beginPath(); x.arc(93, 60, 3.2, 0, 7); x.fill();
    x.strokeStyle = HEX[RUST]; x.lineWidth = 3; x.beginPath();
    x.moveTo(28, 12); x.quadraticCurveTo(34, 8, 40, 13);
    x.moveTo(42, 46); x.lineTo(64, 46); x.moveTo(21, 57); x.lineTo(37, 57); x.moveTo(68, 57); x.lineTo(86, 57);
    x.stroke(); x.restore();
  }
  function word(x, text, cx, cy, size, col) {
    x.fillStyle = HEX[col]; x.font = '700 ' + size + 'px ' + KHMER; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillText(text, cx, cy);
  }
  function sprinkle(x, y, flip) {
    var row = flip ? [[4, bloom], [14, star], [25, sprig], [36, flower], [47, sprig], [58, star], [67, bloom]]
                   : [[4, sprig], [13, bloom], [23, star], [35, flower], [47, star], [57, bloom], [66, sprig]];
    row.forEach(function (m) { var cx = m[0], f = m[1]; f === flower ? flower(x, cx, y, 5) : f === star ? star(x, cx, y, 4.2) : f === bloom ? bloom(x, cx, y, 2.4) : sprig(x, cx, y, 3.4); });
  }
  function shawlDesign() {
    return raster(72, 104, function (x) {
      for (var i = 0; i < 8; i++) bloom(x, 4.5 + i * 9, 3, 1.8, i % 2 ? PINK : OR);
      word(x, KOU, 17, 14, 13, TEAL); word(x, KOU, 46, 14, 13, GOLD); bloom(x, 64, 14, 2.6);
      sprinkle(x, 28, false);
      cow(x, 7, 34, 0.56); flower(x, 37, 66, 4); bloom(x, 67, 50, 2.2); star(x, 67, 64, 3.6);
      sprinkle(x, 80, true);
      word(x, KOU, 17, 93, 13, GOLD); word(x, KOU, 46, 93, 13, TEAL); flower(x, 65, 93, 4);
    });
  }
  /* weft-faced cloth, one cell per crossing; Hol cloth is a 1/2 twill: warp shows one in three */
  function HOL(c, q) { return mod(c + q, 3) === 0; }
  function weaveImage(D, cols, rows, cell, o) {
    var img = new ImageData(cols * cell, rows * cell), px = img.data, W = D.W, H = D.H;
    var bleed = o.bleed || 0, slub = o.slub || 0, seed = o.seed || 7, warp = RGB[BK];
    for (var r = 0; r < rows; r++) {
      var q = o.pick ? o.pick(r) : r, qq = o.flip ? H - 1 - mod(q, H) : mod(q, H);
      var sh = bleed ? Math.round((noise1(qq * 0.5, seed) - 0.5) * 2.2 * bleed) : 0;
      for (var c = 0; c < cols; c++) {
        var jit = 0;
        if (bleed) { var hh = hash(c >> 1, qq * 7 + seed); jit = hh < 0.12 * bleed ? -1 : hh > 1 - 0.12 * bleed ? 1 : 0; }
        var k = D.d[qq * W + mod(c + sh + jit, W)], up = HOL(c, q), wf = RGB[k];
        /* shantung: hand-reeled thread runs thick and thin, and a slub catches the light */
        if (slub) {
          var f = 1 + slub * ((noise1(c * 0.07 + qq * 17.3, seed + 3) - 0.5) * 0.3 + (hash(c >> 2, qq * 31 + seed) > 1 - 0.035 * slub ? 0.28 : 0));
          wf = [Math.min(255, wf[0] * f), Math.min(255, wf[1] * f), Math.min(255, wf[2] * f)];
        }
        for (var j = 0; j < cell; j++) {
          var vy = 1.12 - 0.34 * Math.abs((j + 0.5) / cell - 0.5) * 2;
          for (var i = 0; i < cell; i++) {
            var o4 = ((r * cell + j) * cols * cell + c * cell + i) * 4;
            if (up) {
              var vx = 1.25 - 0.45 * Math.abs((i + 0.5) / cell - 0.5) * 2;
              px[o4] = warp[0] * vx + wf[0] * 0.14; px[o4 + 1] = warp[1] * vx + wf[1] * 0.14; px[o4 + 2] = warp[2] * vx + wf[2] * 0.14;
            } else { px[o4] = wf[0] * vy; px[o4 + 1] = wf[1] * vy; px[o4 + 2] = wf[2] * vy; }
            px[o4 + 3] = 255;
          }
        }
      }
    }
    return img;
  }
  /* ---- motdang's edition: the loom in a Lanna room. The scene is laid out on a
     1200 × 630 sheet and scaled to cover the frame. A weaver in pha sin and sabai sits
     at the loom; three shafts lift in turn (shaft −q mod 3 for pick q, the twill), the
     treadle under it goes down, the shuttle flies trailing gold, the beater swings down
     to the fell, and the shawl grows from the breast beam a row at a time: 56 picks,
     a hold while the gold threads catch the light, then the cloth winds on and the next
     length begins. A lai kham frame, khom dao lanterns, glints running down the warp. */
  var D = null, CL = null, GL = null;
  var X0 = 352, CELL = 4, COLS = 184, X1 = X0 + COLS * CELL, NR = 56, BREAST = 548, TOPB = 70;
  var PK = 0.34, HOLD = 3.2, ROLL = 1.1, CYC = NR * PK + HOLD + ROLL, OFF = 13.82;
  var SWL = X0 - 22, SWR = X1 + 22, SHAFT = [150, 176, 202];
  function woven() {
    if (CL) return;
    var img = weaveImage(D, COLS, NR, CELL, { bleed: 1.6, slub: 0.9, seed: 11, pick: function (r) { return NR - 1 - r + 24; }, flip: true });
    CL = document.createElement('canvas'); CL.width = img.width; CL.height = img.height; CL.getContext('2d').putImageData(img, 0, 0);
    /* the gold cells alone, for the light that runs across the finished length */
    var g = new ImageData(img.width, img.height), a = img.data, b = g.data;
    for (var i = 0; i < a.length; i += 4) if (a[i] > 150 && a[i + 1] > a[i] * 0.6 && a[i + 2] < 120) { b[i] = 255; b[i + 1] = 222; b[i + 2] = 120; b[i + 3] = 255; }
    GL = document.createElement('canvas'); GL.width = g.width; GL.height = g.height; GL.getContext('2d').putImageData(g, 0, 0);
  }
  function gold(x, y0, y1) { var g = x.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, '#fff1b0'); g.addColorStop(0.45, '#e9b949'); g.addColorStop(1, '#9a6416'); return g; }
  function wood(x, y0, y1, dark) { var g = x.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, dark ? '#6b4426' : '#a9713d'); g.addColorStop(0.5, dark ? '#4a2c17' : '#7d4f28'); g.addColorStop(1, dark ? '#2a170b' : '#4f2f15'); return g; }
  /* lai kham: gold stencilled on lacquer — a four-petal flower in a diamond, flame tips between */
  function laiKham(x, len, wd) {
    for (var u = 14; u < len - 8; u += 28) {
      x.fillStyle = gold(x, -wd / 2, wd / 2);
      x.beginPath(); x.moveTo(u, -wd * 0.36); x.lineTo(u + wd * 0.36, 0); x.lineTo(u, wd * 0.36); x.lineTo(u - wd * 0.36, 0); x.closePath(); x.fill();
      x.fillStyle = '#4a0c0c'; x.beginPath(); for (var k = 0; k < 4; k++) { var a = k * Math.PI / 2; x.moveTo(u, 0); x.arc(u + Math.cos(a) * wd * 0.13, Math.sin(a) * wd * 0.13, wd * 0.09, 0, 7); } x.fill();
      x.fillStyle = gold(x, -wd / 2, wd / 2);
      [-1, 1].forEach(function (sd) { x.beginPath(); x.moveTo(u + 9, sd * wd * 0.44); x.quadraticCurveTo(u + 14, sd * wd * 0.1, u + 19, sd * wd * 0.44); x.quadraticCurveTo(u + 14, sd * wd * 0.3, u + 9, sd * wd * 0.44); x.fill(); });
    }
  }
  function rosette(x, cx, cy, r) {
    x.fillStyle = gold(x, cy - r, cy + r);
    for (var k = 0; k < 8; k++) { var a = k * Math.PI / 4; x.beginPath(); x.ellipse(cx + Math.cos(a) * r * 0.55, cy + Math.sin(a) * r * 0.55, r * 0.45, r * 0.2, a, 0, 7); x.fill(); }
    x.fillStyle = '#7a1414'; x.beginPath(); x.arc(cx, cy, r * 0.3, 0, 7); x.fill();
    x.fillStyle = '#ffe9a0'; x.beginPath(); x.arc(cx, cy, r * 0.13, 0, 7); x.fill();
  }
  /* the room, the loom's frame and beams: drawn once per size */
  function back(x) {
    var g = x.createRadialGradient(170, 170, 20, 420, 300, 900); g.addColorStop(0, '#5a3418'); g.addColorStop(0.45, '#2a160b'); g.addColorStop(1, '#120905');
    x.fillStyle = g; x.fillRect(0, 0, 1200, 630);
    /* a lai kham wall, faint */
    x.save(); x.globalAlpha = 0.13;
    for (var row = 0; row < 7; row++) { x.save(); x.translate(0, 60 + row * 84); laiKham(x, 1200, 30); x.restore(); }
    x.restore();
    /* floor boards */
    x.fillStyle = wood(x, 596, 630, true); x.fillRect(0, 596, 1200, 34);
    x.strokeStyle = 'rgba(0,0,0,.35)'; x.lineWidth = 1; x.beginPath(); for (var b = 0; b < 1200; b += 90) { x.moveTo(b, 598); x.lineTo(b + 30, 630); } x.stroke();
    /* the warp's dark behind the threads */
    var wg = x.createLinearGradient(0, TOPB, 0, BREAST); wg.addColorStop(0, '#0d0705'); wg.addColorStop(1, '#24160f');
    x.fillStyle = wg; x.fillRect(X0 - 4, TOPB + 18, X1 - X0 + 8, BREAST - TOPB - 18);
    /* posts, the castle beam with kalae horns, the warp beam */
    x.fillStyle = wood(x, 0, 630); x.fillRect(296, 40, 24, 560); x.fillRect(X1 + 34, 40, 24, 560);
    x.fillStyle = wood(x, 40, 70); x.fillRect(280, 40, X1 + 82 - 280, 26);
    x.strokeStyle = '#e9b949'; x.lineWidth = 5; x.lineCap = 'round';
    [[284, -1], [X1 + 78, 1]].forEach(function (e) { x.beginPath(); x.moveTo(e[0], 46); x.quadraticCurveTo(e[0] + e[1] * 26, 36, e[0] + e[1] * 22, 6); x.stroke(); x.beginPath(); x.moveTo(e[0] - e[1] * 8, 46); x.quadraticCurveTo(e[0] + e[1] * 4, 30, e[0] - e[1] * 6, 8); x.stroke(); });
    x.fillStyle = wood(x, 66, 90, true); x.fillRect(X0 - 30, 66, X1 - X0 + 60, 20);
    /* bench */
    x.fillStyle = wood(x, 492, 512); x.fillRect(120, 492, 186, 16);
    x.fillStyle = wood(x, 500, 600, true); x.fillRect(132, 506, 12, 92); x.fillRect(282, 506, 12, 92);
  }
  /* the frame over everything, and the cloth beam */
  function front(x) {
    x.fillStyle = wood(x, BREAST, BREAST + 28); x.fillRect(X0 - 46, BREAST, X1 - X0 + 92, 26);
    x.fillStyle = 'rgba(255,230,180,.25)'; x.fillRect(X0 - 46, BREAST + 2, X1 - X0 + 92, 3);
    var B = 22;
    x.fillStyle = '#5a0c0c'; x.fillRect(0, 0, 1200, B); x.fillRect(0, 630 - B, 1200, B); x.fillRect(0, 0, B, 630); x.fillRect(1200 - B, 0, B, 630);
    x.save(); x.translate(0, B / 2); laiKham(x, 1200, B); x.restore();
    x.save(); x.translate(0, 630 - B / 2); laiKham(x, 1200, B); x.restore();
    x.save(); x.translate(B / 2, 0); x.rotate(Math.PI / 2); laiKham(x, 630, B); x.restore();
    x.save(); x.translate(1200 - B / 2, 0); x.rotate(Math.PI / 2); laiKham(x, 630, B); x.restore();
    x.strokeStyle = gold(x, 0, 630); x.lineWidth = 2; x.strokeRect(B + 3, B + 3, 1200 - 2 * B - 6, 630 - 2 * B - 6);
    x.lineWidth = 1; x.strokeRect(B + 8, B + 8, 1200 - 2 * B - 16, 630 - 2 * B - 16);
    [[B, B], [1200 - B, B], [B, 630 - B], [1200 - B, 630 - B]].forEach(function (p) { rosette(x, p[0], p[1], 20); });
  }
  /* khom dao, the Lanna star lantern: two squares, one turned 45°, turning on its string */
  function khom(x, cx, cy, r, t, k) {
    var fl = 0.85 + 0.15 * Math.sin(t / 130 + k * 2) * Math.sin(t / 370 + k);
    x.strokeStyle = 'rgba(40,20,10,.8)'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(cx, 22); x.lineTo(cx, cy - r); x.stroke();
    var g = x.createRadialGradient(cx, cy, 0, cx, cy, r * 3.4); g.addColorStop(0, 'rgba(255,190,90,' + 0.5 * fl + ')'); g.addColorStop(1, 'rgba(255,140,40,0)');
    x.fillStyle = g; x.beginPath(); x.arc(cx, cy, r * 3.4, 0, 7); x.fill();
    var sq = Math.cos(t / 1900 + k); sq = (sq < 0 ? -1 : 1) * Math.max(0.3, Math.abs(sq));
    x.fillStyle = '#ffcf6a';
    [0, Math.PI / 4].forEach(function (a0, i) {
      x.fillStyle = i ? '#ffd98a' : '#ff9a3a'; x.beginPath();
      for (var j = 0; j < 4; j++) { var a = a0 + j * Math.PI / 2 + t / 2600 + k; x.lineTo(cx + Math.cos(a) * r * sq, cy + Math.sin(a) * r); }
      x.closePath(); x.fill();
    });
    x.fillStyle = 'rgba(255,250,220,' + fl + ')'; x.beginPath(); x.arc(cx, cy, r * 0.28, 0, 7); x.fill();
    /* the tails */
    x.strokeStyle = '#ff6a3a'; x.lineWidth = 2.5;
    for (var j = -1; j <= 1; j++) { x.beginPath(); x.moveTo(cx + j * r * 0.2, cy + r); x.quadraticCurveTo(cx + j * r * 0.3 + Math.sin(t / 700 + j + k) * 8, cy + r * 2, cx + j * r * 0.25 + Math.sin(t / 500 + j) * 10, cy + r * 2.9); x.stroke(); }
  }
  function spark(x, cx, cy, z, a) {
    x.globalAlpha = a; x.beginPath(); x.moveTo(cx, cy - z * 2); x.quadraticCurveTo(cx, cy, cx + z * 2, cy); x.quadraticCurveTo(cx, cy, cx, cy + z * 2); x.quadraticCurveTo(cx, cy, cx - z * 2, cy); x.quadraticCurveTo(cx, cy, cx, cy - z * 2); x.fill();
  }
  function ik(sh, T, L1, L2) {
    var dx = T[0] - sh[0], dy = T[1] - sh[1], d = Math.max(Math.abs(L1 - L2) + 1, Math.min(L1 + L2 - 0.5, Math.sqrt(dx * dx + dy * dy)));
    var base = Math.atan2(dx, dy), al = Math.acos(Math.max(-1, Math.min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))), a1 = base - al;
    var e = [sh[0] + Math.sin(a1) * L1, sh[1] + Math.cos(a1) * L1];
    return [a1, Math.atan2(T[0] - e[0], T[1] - e[1]) - a1];
  }
  function draw(c, W, H, t) {
    if (!D) D = shawlDesign();
    woven();
    var V = cover(W, H), sec = Math.max(0, t) / 1000 + OFF, u = sec % CYC, p, f = 0, roll = 0, hold = -1;
    if (u < NR * PK) { p = Math.floor(u / PK); f = u / PK - p; } else if (u < NR * PK + HOLD) { p = NR; hold = (u - NR * PK) / HOLD; } else { p = NR; roll = (u - NR * PK - HOLD) / ROLL; }
    var weaving = hold < 0 && !roll, dir = p % 2 ? -1 : 1;
    var lift = weaving ? Math.min(1, f / 0.12) : 0, prog = weaving ? Math.max(0, Math.min(1, (f - 0.12) / 0.58)) : 0, bt = weaving && f > 0.7 ? (f - 0.7) / 0.3 : 0;
    prog = prog * prog * (3 - 2 * prog);
    var rows = roll ? NR * (1 - roll * roll) : p, fell = BREAST - rows * CELL, q = p + 24, up = mod(-q, 3), was = mod(-(q - 1), 3);
    c.save(); view(c, V);
    layer(c, 'wv-back', W, H, V, back);
    /* warp: threads from the beam to the fell, through the shafts; the lifted ones, gold */
    var dn = new Path2D(), lf = new Path2D(), cl;
    for (cl = 0; cl < COLS; cl++) {
      var X = X0 + cl * CELL + CELL / 2, sh = mod(-cl, 3) === up;
      var P = sh && weaving ? lf : dn, ey = SHAFT[mod(cl, 3)] - (sh && weaving ? 12 * lift : 0);
      P.moveTo(X, TOPB + 18); P.lineTo(X, ey); P.lineTo(X, fell);
    }
    c.lineWidth = 2.1; c.strokeStyle = 'rgba(120,86,60,.55)'; c.stroke(dn);
    c.strokeStyle = 'rgba(236,196,120,.85)'; c.stroke(lf);
    /* the shafts: bars and heddle eyes; the lifting one rises */
    for (var s = 0; s < 3; s++) {
      var lifted = s === up ? 12 * lift : s === was && weaving ? 12 * (1 - lift) : 0, sy = SHAFT[s] - lifted;
      c.fillStyle = 'rgba(30,16,8,.9)'; c.fillRect(X0 - 14, sy - 12, X1 - X0 + 28, 4); c.fillRect(X0 - 14, sy + 8, X1 - X0 + 28, 4);
      c.strokeStyle = s === up ? 'rgba(255,214,120,.5)' : 'rgba(233,165,60,.22)'; c.lineWidth = 1; c.beginPath();
      for (cl = s; cl < COLS; cl += 3) { var hx = X0 + cl * CELL + CELL / 2; c.moveTo(hx, sy - 10); c.lineTo(hx, sy + 9); }
      c.stroke();
      c.strokeStyle = 'rgba(60,35,20,.9)'; c.beginPath(); c.moveTo(X0 + 40 + s * 30, TOPB + 16); c.lineTo(X0 + 40 + s * 30, sy - 12); c.moveTo(X1 - 40 - s * 30, TOPB + 16); c.lineTo(X1 - 40 - s * 30, sy - 12); c.stroke();
    }
    /* glints running down the warp */
    c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = '#ffd98a';
    for (var gi = 0; gi < 26; gi++) {
      var gx = X0 + (Math.floor(hash(gi, 5) * COLS) + 0.5) * CELL, gp = (sec * (0.18 + 0.2 * hash(gi, 9)) + hash(gi, 3)) % 1, gy = TOPB + 18 + gp * (fell - TOPB - 18);
      var gg = c.createLinearGradient(gx, gy - 36, gx, gy + 4); gg.addColorStop(0, 'rgba(255,220,140,0)'); gg.addColorStop(1, 'rgba(255,236,180,.9)');
      c.fillStyle = gg; c.fillRect(gx - 1.2, gy - 36, 2.4, 40);
    }
    c.restore();
    /* cloth: woven rows rise from the breast beam; winding on, it sinks behind it */
    if (rows > 0) {
      var sy0 = roll ? 0 : NR - p, n = roll ? rows : p;
      c.save(); c.imageSmoothingEnabled = false; c.beginPath(); c.rect(X0, TOPB, X1 - X0, BREAST - TOPB); c.clip();
      c.drawImage(CL, 0, sy0 * CELL, COLS * CELL, n * CELL, X0, fell, COLS * CELL, n * CELL);
      if (hold >= 0) {   /* the gold threads catch a light that crosses the finished length */
        var bx = X0 - 120 + hold * (X1 - X0 + 240);
        c.globalCompositeOperation = 'lighter'; c.globalAlpha = 0.8 * Math.sin(Math.PI * hold);
        var x0 = Math.max(X0, bx - 70), x1 = Math.min(X1, bx + 70);
        if (x1 > x0) c.drawImage(GL, x0 - X0, 0, x1 - x0, NR * CELL, x0, fell, x1 - x0, NR * CELL);
        var sg = c.createLinearGradient(bx - 90, 0, bx + 90, 0); sg.addColorStop(0, 'rgba(255,240,200,0)'); sg.addColorStop(0.5, 'rgba(255,240,200,.22)'); sg.addColorStop(1, 'rgba(255,240,200,0)');
        c.globalAlpha = Math.sin(Math.PI * hold); c.fillStyle = sg; c.fillRect(bx - 90, fell, 180, rows * CELL);
      }
      c.restore();
    }
    /* the pick being laid: the row shows behind the shuttle, a gold thread runs to it */
    var shx = dir > 0 ? X0 - 70 + prog * (X1 - X0 + 140) : X1 + 70 - prog * (X1 - X0 + 140), py = fell - CELL;
    if (weaving && prog > 0 && p < NR) {
      var a0 = dir > 0 ? X0 : Math.max(X0, shx), a1 = dir > 0 ? Math.min(X1, shx) : X1;
      if (a1 > a0) { c.save(); c.imageSmoothingEnabled = false; c.drawImage(CL, a0 - X0, (NR - 1 - p) * CELL, a1 - a0, CELL, a0, py, a1 - a0, CELL); c.restore(); }
      c.save(); c.globalCompositeOperation = 'lighter'; c.strokeStyle = 'rgba(255,214,110,' + (bt ? 0.9 * (1 - bt) : 0.9) + ')'; c.lineWidth = 2;
      c.beginPath(); c.moveTo(dir > 0 ? X0 - 8 : X1 + 8, py + 2); c.lineTo(Math.max(X0 - 70, Math.min(X1 + 70, shx)), py + 2); c.stroke(); c.restore();
    }
    /* the beater: two swords from the castle beam, the reed across */
    var rest = Math.max(fell - 62, 232), ry = rest + (fell - 3 - rest) * Math.sin(Math.PI * bt);
    c.fillStyle = wood(c, 70, ry); c.fillRect(SWL - 6, 66, 12, ry - 66); c.fillRect(SWR - 6, 66, 12, ry - 66);
    c.fillStyle = wood(c, ry - 10, ry + 10); c.fillRect(SWL - 10, ry - 9, SWR - SWL + 20, 18);
    c.strokeStyle = 'rgba(255,225,170,.35)'; c.lineWidth = 1; c.beginPath(); for (cl = 0; cl < COLS; cl += 2) { var rx = X0 + cl * CELL; c.moveTo(rx, ry - 6); c.lineTo(rx, ry + 6); } c.stroke();
    /* the shuttle in flight, with its own blur and a wake of sparks */
    if (weaving && prog > 0 && prog < 1) {
      for (var gh = 3; gh >= 0; gh--) {
        c.save(); c.globalAlpha = gh ? 0.18 / gh : 1; c.translate(shx - dir * gh * 16, py + 1); c.scale(dir * 1.3, 1.3);
        var bg = c.createLinearGradient(0, -9, 0, 9); bg.addColorStop(0, '#e2ad6a'); bg.addColorStop(1, '#6b4020');
        c.fillStyle = bg; c.beginPath(); c.moveTo(42, 0); c.quadraticCurveTo(12, -11, -42, 0); c.quadraticCurveTo(12, 11, 42, 0); c.fill();
        if (!gh) { c.fillStyle = '#ffd36a'; c.fillRect(-14, -3.5, 26, 7); c.fillStyle = '#fff6d0'; c.beginPath(); c.arc(40, 0, 2, 0, 7); c.fill(); }
        c.restore();
      }
      c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = '#ffe28a';
      for (var k = 1; k < 9; k++) { var wx = shx - dir * k * 22, wy = py + Math.sin(k * 2.1 + sec * 9) * 9; spark(c, wx, wy, 3.2 - k * 0.3, 0.9 - k * 0.1); }
      c.restore();
    }
    /* the treadle under the lifted shaft goes down */
    for (s = 0; s < 3; s++) { var td = s === up && weaving ? 8 * lift : 0; c.fillStyle = wood(c, 584, 598, true); c.fillRect(340 + s * 46, 584 + td, 36, 9); }
    /* the weaver, in pha sin and sabai, hands on the beater */
    var KIT = window.MDDOODLER && window.MDDOODLER.kit;
    if (KIT) {
      var hh = 400, lean = 0.32 + 0.16 * Math.sin(Math.PI * bt), hip = [204, 600 - hh * 0.24], sh2 = [hip[0] + Math.sin(lean) * hh * 0.33, hip[1] - Math.cos(lean) * hh * 0.33];
      var gy = Math.max(sh2[1] - 110, Math.min(sh2[1] + 105, ry - 6)), A1 = ik(sh2, [SWL - 2, gy], hh * 0.17, hh * 0.16), A2 = ik(sh2, [SWL - 4, Math.min(ry - 4, gy + 34)], hh * 0.17, hh * 0.16);
      KIT.person(c, 204, 600, hh, { lean: lean, seat: 0.24, legs: [1.45, -1.35, 1.5, -1.45], arms: [A2[0], A2[1], A1[0], A1[1]] },
        { garb: 'sin', col: '#2c3e6b', low: '#7a1f3a', hem: '#e8b84a', sabai: '#e2b33c', hair: 2, skin: '#d29a6e', dir: 1 });
    }
    layer(c, 'wv-front', W, H, V, front);
    /* khom dao over the weaver; gold motes in their light; a shine running round the frame */
    khom(c, 118, 150, 34, t, 0); khom(c, 222, 96, 22, t, 2);
    c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = '#ffd86a';
    for (var m = 0; m < 22; m++) { var mp = (sec * (0.03 + 0.03 * hash(m, 1)) + hash(m, 2)) % 1, mx = 40 + hash(m, 4) * 1120 + Math.sin(sec * 0.7 + m) * 20, my = 600 - mp * 560;
      spark(c, mx, my, 1.6 + 2.2 * Math.pow(Math.abs(Math.sin(sec * 1.7 + m)), 3), 0.25 + 0.6 * Math.sin(Math.PI * mp)); }
    var per = 2 * (1200 + 630), dpos = (sec * 260) % per, fx, fy;
    [dpos, (dpos + per / 2) % per].forEach(function (d) {
      if (d < 1200) { fx = d; fy = 11; } else if (d < 1830) { fx = 1189; fy = d - 1200; } else if (d < 3030) { fx = 3030 - d; fy = 619; } else { fx = 11; fy = per - d; }
      var fg = c.createRadialGradient(fx, fy, 0, fx, fy, 46); fg.addColorStop(0, 'rgba(255,240,190,.75)'); fg.addColorStop(1, 'rgba(255,200,90,0)');
      c.globalAlpha = 1; c.fillStyle = fg; c.fillRect(fx - 46, fy - 46, 92, 92);
    });
    c.restore();
    c.restore();
  }
  return { draw: draw };
})();

/* ---- Melodies and Motifs' strands, grown into a whole headdress (motdang's edition).
   On a 1200 × 630 sheet scaled to cover the frame: the site's band of studs and its 34
   strands behind; in front, a singer in a black jacket with appliqué bands, under a Loimi
   headdress after the photographs on the site — a dome of silver studs that a moving light
   runs across, red, white and blue beads along its edges, red wool at its sides, orange
   tassels, big silver balls and coin discs that spin and flash as they turn face-on, long
   bead strands to the shoulders, and loops of red, white and blue beads under the chin,
   each a pendulum of its own length, θ = θ₀·sin(√(g/L)·t + φ), so they drift in and out
   of step. She sings; the notes rise. */
var AKS = {};
var AK = (function () {
  var COL = ['#d0283a', '#f2b632', '#2f9e6e', '#3a6fd8', '#efeae0'], STR = null, STUDS = null;
  var HX = 600, HY = 322;   /* the face's centre */
  function coinFill(x, cx, cy, rr) {
    var g = x.createRadialGradient(cx - 0.24 * rr, cy - 0.36 * rr, 0, cx - 0.24 * rr, cy - 0.36 * rr, 1.4 * rr);
    g.addColorStop(0, '#ffffff'); g.addColorStop(0.45, '#cfd3da'); g.addColorStop(1, '#7d828c'); return g;
  }
  function ball(x, cx, cy, rr) {
    x.fillStyle = coinFill(x, cx, cy, rr); x.beginPath(); x.arc(cx, cy, rr, 0, 7); x.fill();
    x.strokeStyle = 'rgba(80,84,96,.55)'; x.lineWidth = rr * 0.06; x.beginPath(); x.ellipse(cx, cy, rr * 0.98, rr * 0.3, 0, 0, 7); x.stroke();
    x.beginPath(); x.ellipse(cx, cy, rr * 0.3, rr * 0.98, 0, 0, 7); x.stroke();
  }
  function pomFill(x, cx, cy, rr, a, b) {
    var g = x.createRadialGradient(cx - 0.2 * rr, cy - 0.3 * rr, 0, cx - 0.2 * rr, cy - 0.3 * rr, 1.3 * rr);
    g.addColorStop(0, a || '#ff6272'); g.addColorStop(1, b || '#9e1424'); return g;
  }
  function bead(col) { return spr('bead' + col, 10, 10, function (x) {
    var g = x.createRadialGradient(3.6, 3.4, 0, 5, 5, 5); g.addColorStop(0, col === '#f4f1ea' ? '#ffffff' : '#ffffff'); g.addColorStop(0.25, col); g.addColorStop(1, shade(col));
    x.fillStyle = g; x.beginPath(); x.arc(5, 5, 4.6, 0, 7); x.fill(); }); }
  function shade(col) { return { '#d0283a': '#6e0f1c', '#f4f1ea': '#a7a49c', '#2f55c9': '#16296a', '#f2b632': '#8a5a0a', '#2f9e6e': '#134a32', '#3a6fd8': '#1a3570', '#efeae0': '#9a968c', '#ff8a2a': '#8a3a08' }[col] || '#333'; }
  /* the site's strands, each drawn once into its own strip */
  function strands() {
    if (STR) return STR;
    var r = rnd(29); STR = [];
    for (var i = 0; i < 34; i++) {
      var sx = 1200 / 34 * (i + 0.5) + (r() * 8 - 4), len = 120 + r() * 120, sway = 1.5 + r() * 2.5, ph = r() * 6.28, sp = 0.6 + r() * 0.6, pal = COL[i % 4];
      var cv = document.createElement('canvas'), k = 2; cv.width = 30 * k; cv.height = (len + 20) * k;
      var x = cv.getContext('2d'); x.scale(k, k);
      x.strokeStyle = '#8a8594'; x.lineWidth = 1; x.beginPath(); x.moveTo(15, 0); x.lineTo(15, len); x.stroke();
      for (var y = 6, j = 0; y < len - 18; j++) { x.fillStyle = (j % 5 === 4) ? '#efeae0' : (j % 9 === 0 ? COL[(i + j) % 4] : pal); x.beginPath(); x.arc(15, y, (j % 5 === 4) ? 4.2 : 3.2, 0, 7); x.fill(); y += (j % 5 === 4) ? 9 : 7; }
      if (i % 3 === 0) { x.fillStyle = pomFill(x, 15, len - 4, 13); x.beginPath(); x.arc(15, len - 4, 13, 0, 7); x.fill(); }
      else { x.fillStyle = coinFill(x, 15, len, 12); x.beginPath(); x.arc(15, len, 12, 0, 7); x.fill(); x.fillStyle = '#14131c'; x.beginPath(); x.arc(15, len, 3, 0, 7); x.fill(); }
      STR.push({ cv: cv, x: sx, len: len, sway: sway, ph: ph, sp: sp });
    }
    return STR;
  }
  /* the dome's studs, row on row between the face opening and the crown */
  function studs() {
    if (STUDS) return STUDS;
    STUDS = [];
    for (var i = 0; i < 9; i++) {
      var f = i / 8, rx = 112 + f * 92, ry = 132 + f * 128, rr = 8.5 + f * 2.5, th0 = -0.32 + f * 0.05, len = (Math.PI - 2 * th0) * (rx + ry) / 2, n = Math.floor(len / (rr * 2.25));
      for (var j = 0; j <= n; j++) { var th = th0 + (Math.PI - 2 * th0) * j / n; STUDS.push([HX + rx * Math.cos(th), HY - 8 - ry * Math.sin(th), rr]); }
    }
    return STUDS;
  }
  function dome(x, rx, ry, th0) { x.beginPath(); for (var j = 0; j <= 40; j++) { var th = th0 + (Math.PI - 2 * th0) * j / 40; x.lineTo(HX + rx * Math.cos(th), HY - 8 - ry * Math.sin(th)); } }
  function beadArc(x, rx, ry, th0, col, rr) {
    var len = (Math.PI - 2 * th0) * (rx + ry) / 2, n = Math.floor(len / (rr * 2.1));
    for (var j = 0; j <= n; j++) { var th = th0 + (Math.PI - 2 * th0) * j / n; x.drawImage(bead(col), HX + rx * Math.cos(th) - rr, HY - 8 - ry * Math.sin(th) - rr, rr * 2, rr * 2); }
  }
  /* the static sheet: night cloth, the singer's jacket and face, the headdress's dome */
  function back(x) {
    var g = x.createRadialGradient(HX, 260, 30, HX, 300, 760); g.addColorStop(0, '#3a2c55'); g.addColorStop(0.4, '#1d1a2a'); g.addColorStop(1, '#0b0a10');
    x.fillStyle = g; x.fillRect(0, 0, 1200, 630);
  }
  function mid(x) {
    var i, k;
    /* the site's band across the top */
    x.fillStyle = '#0c0b12'; x.fillRect(0, 0, 1200, 46);
    for (var row = 0; row < 2; row++) for (k = 12 + (row ? 14 : 0); k < 1200; k += 28) { x.fillStyle = coinFill(x, k, 14 + row * 18, 8.5); x.beginPath(); x.arc(k, 14 + row * 18, 8.5, 0, 7); x.fill(); }
    x.fillStyle = '#d0283a'; x.fillRect(0, 44, 1200, 8); x.fillStyle = '#f2b632';
    for (k = 0; k < 1200; k += 16) { x.beginPath(); x.moveTo(k, 52); x.lineTo(k + 8, 59); x.lineTo(k + 16, 52); x.fill(); }
    for (k = 0; k < 1200; k += 150) { x.fillStyle = pomFill(x, k + 60, 54, 15); x.beginPath(); x.arc(k + 60, 54, 15, 0, 7); x.fill(); }
    /* the singer: shoulders in the black jacket, striped sleeves, appliqué bands */
    x.fillStyle = '#16141f'; x.beginPath(); x.moveTo(250, 630); x.bezierCurveTo(260, 520, 360, 470, 520, 452); x.lineTo(680, 452); x.bezierCurveTo(840, 470, 940, 520, 950, 630); x.closePath(); x.fill();
    x.save(); x.clip();
    var stripes = ['#e8457a', '#f4f1ea', '#d0283a', '#3a6fd8', '#f4f1ea', '#e8457a'];
    [-1, 1].forEach(function (sd) { for (k = 0; k < 6; k++) { x.strokeStyle = stripes[k]; x.lineWidth = 9; x.beginPath(); x.moveTo(HX + sd * (300 - k * 3), 480 + k * 22); x.lineTo(HX + sd * (380 - k * 6), 470 + k * 26); x.stroke(); } });
    var bandY = [548, 572, 596], panel = [['#d9542a', '#f2b632', '#2f9e6e', '#3a6fd8', '#d0283a'], ['#f2b632', '#d0283a', '#f4f1ea', '#2f9e6e'], ['#d9542a', '#3a6fd8', '#f2b632', '#e8457a']];
    bandY.forEach(function (by, bi) {
      x.fillStyle = bi === 1 ? '#1d1b2a' : '#c4441c'; x.fillRect(420, by, 360, 20);
      for (k = 0; k < 22; k++) { var dx = 428 + k * 16.5; x.fillStyle = panel[bi][k % panel[bi].length]; x.beginPath(); x.moveTo(dx + 8, by + 2); x.lineTo(dx + 14, by + 10); x.lineTo(dx + 8, by + 18); x.lineTo(dx + 2, by + 10); x.closePath(); x.fill(); }
    });
    x.restore();
    x.strokeStyle = 'rgba(190,170,240,.4)'; x.lineWidth = 3; x.beginPath(); x.moveTo(250, 630); x.bezierCurveTo(260, 520, 360, 470, 520, 452); x.lineTo(680, 452); x.bezierCurveTo(840, 470, 940, 520, 950, 630); x.stroke();
    x.strokeStyle = '#f4f1ea'; x.lineWidth = 3; x.beginPath(); x.moveTo(530, 456); x.lineTo(560, 630); x.moveTo(670, 456); x.lineTo(640, 630); x.stroke();
    x.strokeStyle = '#d0283a'; x.beginPath(); x.moveTo(538, 456); x.lineTo(568, 630); x.moveTo(662, 456); x.lineTo(632, 630); x.stroke();
    /* neck and face */
    x.fillStyle = '#1a1826'; x.beginPath(); x.ellipse(HX, HY - 40, 98, 84, 0, 0, 7); x.fill();
    x.fillStyle = '#b97f52'; x.fillRect(HX - 40, HY + 70, 80, 70);
    x.fillStyle = '#c98e64'; x.beginPath(); x.ellipse(HX, HY + 6, 82, 100, 0, 0, 7); x.fill();
    x.fillStyle = 'rgba(220,90,80,.25)'; x.beginPath(); x.arc(HX - 44, HY + 34, 16, 0, 7); x.arc(HX + 44, HY + 34, 16, 0, 7); x.fill();
    x.strokeStyle = '#3a2216'; x.lineWidth = 3; x.lineCap = 'round';
    x.beginPath(); x.arc(HX - 32, HY + 2, 13, 0.2, Math.PI - 0.2); x.moveTo(HX + 45, HY + 6); x.arc(HX + 32, HY + 2, 13, 0.2, Math.PI - 0.2); x.stroke();
    /* the headdress: red wool at the sides, the black dome, studs, bead edges */
    for (k = 0; k < 24; k++) { var th = -0.3 + (k >> 1) / 11 * 1.25, sd = k % 2 ? -1 : 1, wx = HX + sd * (262 + 8 * Math.sin(k * 1.7)) * Math.cos(th), wy = HY - 8 - 300 * Math.sin(th);
      x.fillStyle = pomFill(x, wx, wy, 26, '#ff4a4a', '#8a0e16'); x.beginPath(); x.ellipse(wx, wy, 26, 20, sd * (0.9 - th), 0, 7); x.fill(); }
    x.fillStyle = '#1a1826'; dome(x, 214, 272, -0.36); for (var j = 40; j >= 0; j--) { var th = -0.36 + (Math.PI + 0.72) * j / 40; x.lineTo(HX + 100 * Math.cos(th), HY - 8 - 116 * Math.sin(th)); } x.closePath(); x.fill();
    var S = studs(), sp = spr('stud', 24, 24, function (q) { q.fillStyle = coinFill(q, 12, 12, 11); q.beginPath(); q.arc(12, 12, 11, 0, 7); q.fill(); });
    S.forEach(function (s) { x.drawImage(sp, s[0] - s[2], s[1] - s[2], s[2] * 2, s[2] * 2); });
    beadArc(x, 222, 280, -0.34, '#d0283a', 5); beadArc(x, 232, 290, -0.3, '#f4f1ea', 4.5); beadArc(x, 241, 299, -0.26, '#2f55c9', 4.5);
    beadArc(x, 100, 116, -0.4, '#f4f1ea', 4); beadArc(x, 92, 107, -0.42, '#d0283a', 4);
    /* a crest of red wool and a silver plate at the crown */
    x.fillStyle = pomFill(x, HX, HY - 300, 30); x.beginPath(); x.arc(HX, HY - 300, 28, 0, 7); x.fill();
    /* the bottom band, embroidered */
    x.fillStyle = '#0c0b12'; x.fillRect(0, 596, 1200, 34); x.fillStyle = COL[0]; x.fillRect(0, 596, 1200, 3); x.fillStyle = COL[1]; x.fillRect(0, 627, 1200, 3);
    for (k = 0; k < 1200; k += 34) {
      x.strokeStyle = COL[(k / 34) % 4]; x.lineWidth = 3; x.beginPath(); x.moveTo(k + 17, 603); x.lineTo(k + 27, 613); x.lineTo(k + 17, 623); x.lineTo(k + 7, 613); x.closePath(); x.stroke();
      x.fillStyle = '#efeae0'; x.fillRect(k + 14.5, 610.5, 5, 5);
      x.strokeStyle = '#efeae0'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(k, 603); x.lineTo(k + 5, 608); x.lineTo(k, 613); x.moveTo(k + 34, 613); x.lineTo(k + 29, 618); x.lineTo(k + 34, 623); x.stroke();
    }
  }
  function star4(x, cx, cy, z) { x.beginPath(); x.moveTo(cx, cy - z * 2); x.quadraticCurveTo(cx, cy, cx + z * 2, cy); x.quadraticCurveTo(cx, cy, cx, cy + z * 2); x.quadraticCurveTo(cx, cy, cx - z * 2, cy); x.quadraticCurveTo(cx, cy, cx, cy - z * 2); x.fill(); }
  function pend(L, t, a0, ph) { return a0 * Math.sin(Math.sqrt(9.8 / (L / 260)) * t + ph); }
  return function (c, W, H, t) {
    var V = cover(W, H), sec = t / 1000, i, k, S;
    c.save(); view(c, V);
    layer(c, 'ak-back', W, H, V, back);
    /* the site's strands, swinging behind */
    strands().forEach(function (s) {
      var a = s.sway * Math.sin(sec * s.sp + s.ph) * Math.PI / 180;
      c.save(); c.translate(s.x, 52); c.rotate(a); c.globalAlpha = 0.85; c.drawImage(s.cv, -15, 0, 30, s.len + 20); c.restore();
    });
    layer(c, 'ak-mid', W, H, V, mid);
    /* she sings */
    var open = Math.max(0, Math.sin(sec * 3.1) * Math.sin(sec * 0.9 + 0.6));
    c.fillStyle = '#5a1f22'; c.beginPath(); c.ellipse(HX, HY + 58, 14, 3 + 11 * open, 0, 0, 7); c.fill();
    c.fillStyle = 'rgba(255,240,210,.85)';
    for (k = 0; k < 4; k++) { var nu = (sec * 0.22 + k / 4) % 1, nx = HX + (k % 2 ? -1 : 1) * (90 + nu * 190) + Math.sin(nu * 9 + k) * 14, ny = HY + 40 - nu * 170;
      c.globalAlpha = Math.sin(Math.PI * nu) * 0.9; c.beginPath(); c.ellipse(nx, ny, 8, 6, -0.4, 0, 7); c.fill(); c.fillRect(nx + 6, ny - 26, 2.4, 26); if (k % 2) c.fillRect(nx + 6, ny - 26, 12, 3); }
    c.globalAlpha = 1;
    /* light runs across the studs */
    var lx = HX + 300 * Math.sin(sec * 0.55), ly = HY - 160 + 60 * Math.cos(sec * 0.37);
    c.save(); c.globalCompositeOperation = 'lighter';
    var hl = spr('hl', 24, 24, function (q) { var g = q.createRadialGradient(9, 8, 0, 12, 12, 12); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.3, 'rgba(220,235,255,.55)'); g.addColorStop(1, 'rgba(200,220,255,0)'); q.fillStyle = g; q.fillRect(0, 0, 24, 24); });
    studs().forEach(function (s) { var d = ((s[0] - lx) * (s[0] - lx) + (s[1] - ly) * (s[1] - ly)) / 9000; if (d < 3) { c.globalAlpha = Math.exp(-d) * 0.95; c.drawImage(hl, s[0] - s[2] * 1.2, s[1] - s[2] * 1.2, s[2] * 2.4, s[2] * 2.4); } });
    c.restore();
    /* orange tassels at the crown's corners */
    c.lineCap = 'round';
    [-1, 1].forEach(function (sd) {
      var tx = HX + sd * 168, ty = HY - 210, sw = pend(150, sec, 0.16, sd);
      for (k = 0; k < 9; k++) { c.strokeStyle = k % 3 ? '#ff8a2a' : '#ffb24a'; c.lineWidth = 3; c.beginPath(); c.moveTo(tx, ty); c.quadraticCurveTo(tx + sd * (20 + k * 3), ty + 40, tx + sd * (26 + k * 4) + Math.sin(sw + k * 0.3) * 60, ty + 120 + k * 6); c.stroke(); }
      c.fillStyle = '#f2b632'; c.beginPath(); c.arc(tx, ty, 8, 0, 7); c.fill();
    });
    /* long strands to the shoulders, white and red, swinging */
    [-1, 1].forEach(function (sd) {
      for (k = 0; k < 7; k++) {
        var ax = HX + sd * (205 + k * 6), ay = HY + 20, L = 190 + k * 18, a = pend(L, sec, 0.07, k * 0.8 + sd), col = k % 3 === 1 ? '#d0283a' : '#f4f1ea';
        var st = spr('str' + col + L, 8, L + 4, function (q) { var b = bead(col); for (var j = 0; j < L; j += 8.5) q.drawImage(b, 0.4, j, 7.2, 7.2); });
        c.save(); c.translate(ax, ay); c.rotate(-a); c.drawImage(st, -4, -3.6, 8, L + 4); c.restore();
        if (k === 3) { var px = ax + Math.sin(a) * L, py = ay + Math.cos(a) * L; c.fillStyle = pomFill(c, px, py, 16, '#ff6a9a', '#a8204a'); c.beginPath(); c.arc(px, py, 16, 0, 7); c.fill();
          c.strokeStyle = '#f4f1ea'; c.lineWidth = 2; c.beginPath(); for (i = -3; i <= 3; i++) { c.moveTo(px + i * 3, py + 12); c.lineTo(px + i * 4 + Math.sin(a * 6) * 4, py + 40); } c.stroke(); }
      }
    });
    /* big silver balls down the cheeks, each on a short pendulum */
    var B = spr('ball', 64, 64, function (q) { ball(q, 32, 32, 30); });
    [-1, 1].forEach(function (sd) {
      for (k = 0; k < 4; k++) {
        var bx = HX + sd * (176 - k * 4), by = HY - 120 + k * 52, a = pend(40, sec, 0.12, k + sd * 1.3), r2 = 27 - k * 1.5;
        var cx = bx + Math.sin(a) * 22, cy = by + Math.cos(a) * 22;
        c.drawImage(B, cx - r2, cy - r2, r2 * 2, r2 * 2);
        var d = Math.abs(cx - lx) / 220; if (d < 1) { c.save(); c.globalCompositeOperation = 'lighter'; c.globalAlpha = 1 - d; c.drawImage(hl, cx - r2 * 0.9, cy - r2 * 0.95, r2 * 1.3, r2 * 1.3); c.restore(); }
      }
    });
    /* coin discs that spin; face-on, they flash */
    var Cn = spr('coin', 60, 60, function (q) { q.fillStyle = coinFill(q, 30, 30, 28); q.beginPath(); q.arc(30, 30, 28, 0, 7); q.fill();
      q.strokeStyle = 'rgba(90,94,104,.8)'; q.lineWidth = 2; q.beginPath(); q.arc(30, 30, 22, 0, 7); q.stroke(); q.beginPath(); q.arc(30, 30, 12, 0, 7); q.stroke();
      for (var e = 0; e < 12; e++) { var ea = e * Math.PI / 6; q.beginPath(); q.moveTo(30 + Math.cos(ea) * 13, 30 + Math.sin(ea) * 13); q.lineTo(30 + Math.cos(ea) * 21, 30 + Math.sin(ea) * 21); q.stroke(); } });
    var flashes = [];
    [-1, 1].forEach(function (sd) {
      for (k = 0; k < 3; k++) {
        var cx = HX + sd * (128 + k * 26), cy = HY + 92 + k * 30, spin = sec * (1.1 + k * 0.37) + k + sd, w2 = Math.abs(Math.cos(spin)), r3 = 22 - k * 2;
        c.strokeStyle = '#efeae0'; c.lineWidth = 2; c.beginPath(); c.moveTo(cx, cy - 34); c.lineTo(cx, cy - r3); c.stroke();
        c.drawImage(Cn, cx - r3 * Math.max(0.08, w2), cy - r3, r3 * 2 * Math.max(0.08, w2), r3 * 2);
        var fl = Math.pow(w2, 30); if (fl > 0.05) flashes.push([cx + r3 * 0.3, cy - r3 * 0.3, fl, r3]);
      }
    });
    /* bead loops under the chin: red, white, blue, white, red, white, each its own pendulum */
    var LOOP = ['#d0283a', '#f4f1ea', '#2f55c9', '#f4f1ea', '#d0283a', '#f4f1ea', '#2f55c9'];
    LOOP.forEach(function (col, j) {
      var x0 = HX - 132 - j * 4, x1 = HX + 132 + j * 4, y0 = HY + 70, dep = 70 + j * 24, a = pend(dep, sec, 0.2, j * 0.9), b = bead(col), n = 26 + j * 3;
      for (var m = 0; m <= n; m++) { var u = m / n, sg = Math.sin(Math.PI * u) * dep;
        c.drawImage(b, x0 + (x1 - x0) * u + Math.sin(a) * sg - 4.2, y0 + Math.cos(a) * sg - 4.2, 8.4, 8.4); }
    });
    /* the chest pendants, slow */
    [-1, 1].forEach(function (sd, k2) {
      var a = pend(120, sec, 0.06, k2 * 2), px = HX + sd * 60 + Math.sin(a) * 120, py = 480 + Math.cos(a) * 30;
      c.strokeStyle = '#cfd3da'; c.lineWidth = 2; c.beginPath(); c.moveTo(HX + sd * 40, 440); c.lineTo(px, py - 30); c.stroke();
      c.drawImage(Cn, px - 32, py - 32, 64, 64);
      var d = Math.abs(px - lx) / 260; if (d < 1) flashes.push([px + 8, py - 10, (1 - d) * 0.8, 30]);
    });
    /* flashes and a ring of sparks where a coin rings */
    c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = '#ffffff';
    flashes.forEach(function (f) {
      c.globalAlpha = f[2]; star4(c, f[0], f[1], f[3] * 0.35 * (0.6 + f[2]));
      for (var e = 0; e < 6; e++) { var ea = e * Math.PI / 3 + sec, rr = f[3] * (1.2 + (1 - f[2]) * 1.4); c.globalAlpha = f[2] * 0.7; star4(c, f[0] + Math.cos(ea) * rr, f[1] + Math.sin(ea) * rr, 2.2); }
    });
    c.restore();
    c.restore();
  };
})();

/* pages other than the front: a still marked data-dd="<kind>" plays its drawing in place,
   on a canvas laid over it while it is on screen; the still stays under it */
function play() {
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  [].forEach.call(document.querySelectorAll('img[data-dd]'), function (im) {
    var k = im.getAttribute('data-dd'); if (!K[k] || im.getAttribute('data-ddon')) return;
    im.setAttribute('data-ddon', '1');
    var box = im.parentNode, cv = document.createElement('canvas'), ctx = cv.getContext('2d'), on = false, raf = 0, t0 = 0;
    if (getComputedStyle(box).position === 'static') box.style.position = 'relative';
    cv.setAttribute('aria-hidden', 'true');
    cv.style.cssText = 'position:absolute;pointer-events:none;border-radius:' + getComputedStyle(im).borderRadius;
    box.insertBefore(cv, im.nextSibling);
    function tick(now) {
      var w = im.offsetWidth, h = im.offsetHeight, dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (w && h) {
        cv.style.left = im.offsetLeft + 'px'; cv.style.top = im.offsetTop + 'px'; cv.style.width = w + 'px'; cv.style.height = h + 'px';
        if (cv.width !== Math.round(w * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        K[k](ctx, w, h, 4000 + now - t0, null, null);
      }
      if (on) raf = requestAnimationFrame(tick);
    }
    if (!('IntersectionObserver' in window)) { on = true; raf = requestAnimationFrame(tick); return; }
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && !on) { on = true; if (!t0) t0 = performance.now(); raf = requestAnimationFrame(tick); }
        else if (!e.isIntersecting) { on = false; cancelAnimationFrame(raf); }
      });
    }, { rootMargin: '80px' }).observe(im);
  });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', play); else play();
window.MDDOODLES = {
  has: function (k) { return !!K[k]; },
  draw: function (k, c, W, H, t, moon, ridge) { K[k](c, W, H, t, moon, ridge); }
};
})();
