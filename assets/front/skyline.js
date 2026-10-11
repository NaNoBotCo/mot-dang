/* The north, cut from paper: the landscape and the city's sights that run through
   the front page's doodles (Nan, 2026-10-02: "the landscape of chiang mai/chiang rai
   and the urban sights should be a running theme in these doodles"), and the
   rooftop Latin night with its couples. Shared by front.js (the band above the map)
   and doodles.js (each kind's drawing and its still).

   MDSKY.landscape(c, W, H, o) → hit boxes [{k, x0, y0, x1, y1}]
     o.horizon  the y the city stands on        o.x0, o.x1  where the sights may go
     o.cr       Chiang Rai's set, not Chiang Mai's
     o.night, o.pm25, o.ridge (front/ridge.json), o.phone
   MDSKY.latinNight(c, W, H, t, o) → hit boxes for the stage and its banner
     o.x0, o.x1 the stage's span; o.deck the y of the floor; o.label the banner's words
   MDSKY.latinNightScene(c, W, H, t, moon, ridge) the whole picture, for a still */
(function () {
'use strict';
function rnd(seed) { return function () { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }; }
var GRAIN = null;
function grain(c) {
  if (!GRAIN) {
    var g = document.createElement('canvas'), x, i, r = rnd(11); g.width = g.height = 96; x = g.getContext('2d');
    var im = x.createImageData(96, 96);
    for (i = 0; i < im.data.length; i += 4) { var v = r() < 0.5 ? 0 : 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 6 + r() * 16; }
    x.putImageData(im, 0, 0); GRAIN = g;
  }
  return c.createPattern(GRAIN, 'repeat');
}
/* one piece of cut paper: its shadow on what lies under it, its fibres, a cut edge */
function paper(c, path, fill, lift) {
  c.save();
  c.shadowColor = 'rgba(0,0,0,.42)'; c.shadowBlur = 4 + (lift || 1) * 3; c.shadowOffsetX = 1 + (lift || 1); c.shadowOffsetY = 2 + (lift || 1) * 1.5;
  c.fillStyle = fill; path(c); c.fill('evenodd');
  c.restore();
  c.save(); c.fillStyle = grain(c); path(c); c.fill('evenodd');
  c.strokeStyle = 'rgba(255,255,255,.16)'; c.lineWidth = 0.8; path(c); c.stroke(); c.restore();
}
function jag(c, pts, seed, amt) {
  var r = rnd(seed); c.beginPath();
  pts.forEach(function (p, i) { var x = p[0] + (r() - 0.5) * amt, y = p[1] + (r() - 0.5) * amt; i ? c.lineTo(x, y) : c.moveTo(x, y); });
  c.closePath();
}
function circ(c, x, y, r, seed) { var pts = [], n = Math.max(24, Math.round(r * 0.9)); for (var i = 0; i < n; i++) pts.push([x + Math.cos(i / n * 6.2832) * r, y + Math.sin(i / n * 6.2832) * r]); jag(c, pts, seed || 3, Math.min(1.4, r * 0.03)); }
function poly(pts) { return function (q) { q.beginPath(); pts.forEach(function (p, i) { i ? q.lineTo(p[0], p[1]) : q.moveTo(p[0], p[1]); }); q.closePath(); }; }

/* ---------------------------------------------------------------- the sights, west to east
   page: the place page on motdang.net (front_layer matched each landmark to its record) */
var SIGHTS = {
  cm: [
    { k: 'doi-suthep', ridge: true, th: 'วัดพระธาตุดอยสุเทพ', en: 'Wat Phra That Doi Suthep', lat: 18.80492, lng: 98.922103,
      page: 'cm/p/wat-phrathat-doi-suthep-racha-worawihan-114651040.html',
      about: ['ตามตำนาน ช้างเผือกพาพระธาตุขึ้นดอย แล้วหยุดตรงนี้', 'By the chronicle, a white elephant carried the relic up the mountain and stopped here'] },
    { k: 'wat-phra-singh', th: 'วัดพระสิงห์', en: 'Wat Phra Singh', lat: 18.788585, lng: 98.981382,
      page: 'cm/p/wat-phra-singh-93414647.html',
      about: ['วิหารลายคำ และพระพุทธสิหิงค์ที่แห่ออกมาให้สรงน้ำช่วงสงกรานต์', 'The Lai Kham viharn, and the Phra Singh Buddha carried out to be bathed at Songkran'] },
    { k: 'wat-chedi-luang', th: 'วัดเจดีย์หลวง', en: 'Wat Chedi Luang', lat: 18.786973, lng: 98.986857,
      page: 'cm/p/wat-chedi-luang-243018795.html',
      about: ['เจดีย์ใหญ่กลางเมือง ยอดพังลงในแผ่นดินไหว พ.ศ. 2088', 'The great chedi at the city’s heart; its top fell in an earthquake in 1545'] },
    { k: 'three-kings', th: 'อนุสาวรีย์สามกษัตริย์', en: 'Three Kings Monument', lat: 18.79023, lng: 98.987352,
      page: 'cm/p/three-kings-monument-1619287904.html',
      about: ['พญามังราย พญางำเมือง พ่อขุนรามคำแหง ผู้ร่วมกันสร้างเมือง พ.ศ. 1839', 'Mangrai, Ngam Muang and Ramkhamhaeng, who founded the city together in 1296'] },
    { k: 'tha-phae-gate', th: 'ประตูท่าแพ', en: 'Tha Phae Gate', lat: 18.787762, lng: 98.99327,
      page: 'cm/p/thapae-gate-1017379824.html',
      about: ['ประตูเมืองด้านตะวันออก ทางออกไปท่าน้ำปิง', 'The old city’s east gate, the road out to the landing on the Ping'] },
    { k: 'warorot', th: 'กาดหลวง', en: 'Warorot Market', lat: 18.790225, lng: 99.000525,
      page: 'cm/p/warorot-market-89039067.html',
      about: ['ตลาดวโรรส กาดใหญ่ริมน้ำปิง ของกิน ผ้า ของแห้ง', 'Kad Luang, the big market by the Ping: food, cloth, dried goods'] },
    { k: 'iron-bridge', th: 'ขัวเหล็ก', en: 'The Iron Bridge', lat: 18.784074, lng: 99.004137,
      page: 'cm/p/iron-bridge-6388820586.html',
      about: ['สะพานเหล็กข้ามน้ำปิง เดินข้ามได้', 'An iron bridge over the Ping you can walk across'] },
    { k: 'night-bazaar', th: 'ไนท์บาซาร์', en: 'Night Bazaar', lat: 18.784779, lng: 99.000441,
      page: 'cm/p/chiang-mai-night-bazaar-22981272.html',
      about: ['ตลาดกลางคืนถนนช้างคลาน ทุกค่ำ', 'The evening market along Chang Khlan Road, every night'] }
  ],
  cr: [
    { k: 'wat-phra-kaew-cr', th: 'วัดพระแก้ว เชียงราย', en: 'Wat Phra Kaew, Chiang Rai', lat: 19.911662, lng: 99.827016,
      page: 'cr/p/wat-phra-kaew-487642776.html',
      about: ['ที่ที่พบพระแก้วมรกต เมื่อฟ้าผ่าเจดีย์ พ.ศ. 1977', 'Where the Emerald Buddha was found when lightning split the chedi, 1434'] },
    { k: 'clock-tower', th: 'หอนาฬิกาเชียงราย', en: 'Chiang Rai Clock Tower', lat: 19.907163, lng: 99.830989,
      page: 'cr/p/chiang-rai-clock-tower-crcuratedclocktower.html',
      about: ['หอนาฬิกาสีทองของอาจารย์เฉลิมชัย แสงสีเสียงทุกค่ำ 19, 20 และ 21 นาฬิกา', 'Chalermchai Kositpipat’s golden clock tower; a light show at 7, 8 and 9 pm'] },
    { k: 'cr-night-bazaar', th: 'ไนท์บาซาร์เชียงราย', en: 'Chiang Rai Night Bazaar', lat: 19.905315, lng: 99.834066,
      page: 'find?q=' + encodeURIComponent('ไนท์บาซาร์เชียงราย'),
      about: ['ตลาดกลางคืนข้างสถานีขนส่งเก่า', 'The night market beside the old bus station'] }
  ]
};

/* each sight drawn standing on (x, y) at height unit s, from Commons photographs of it
   (Nan, 2026-10-04: "look more like chiang mai"). up() takes points in units of s, y up. */
function up(x, y, s, pts) { return poly(pts.map(function (p) { return [x + p[0] * s, y - p[1] * s]; })); }
/* brick courses and a few weathered patches over a box, in units */
function courses(c, x, y, s, a, b, lo, hi, col, every) {
  var h = every || 0.07; if (h * s < 2.2) return;
  c.save(); c.strokeStyle = col; c.lineWidth = Math.max(0.5, s * 0.006);
  for (var v = lo + h, k = 0; v < hi - h * 0.3; v += h, k++) {
    c.beginPath(); c.moveTo(x + a * s, y - v * s); c.lineTo(x + b * s, y - v * s);
    for (var q = a + (k % 2 ? h : h * 2); q < b; q += h * 3) { c.moveTo(x + q * s, y - v * s); c.lineTo(x + q * s, y - (v + h) * s); }
    c.stroke();
  }
  c.restore();
}
function stains(c, x, y, s, a, b, lo, hi, seed, col) {
  var r = rnd(seed); c.save(); c.fillStyle = col;
  for (var i = 0; i < 7; i++) { var px = a + r() * (b - a), py = lo + r() * (hi - lo), w = 0.05 + r() * 0.12;
    c.beginPath(); c.ellipse(x + px * s, y - py * s, w * s, w * s * 0.45, 0, 0, 6.2832); c.fill(); }
  c.restore();
}
/* a gold hook: the chofa on a gable's peak, the ngao at its eaves (dir ±1) */
function hook(c, x, y, s, dir, col) {
  c.save(); c.strokeStyle = col; c.lineWidth = Math.max(1.2, s * 0.022); c.lineCap = 'round'; c.beginPath();
  c.moveTo(x, y); c.quadraticCurveTo(x + dir * s * 0.02, y - s * 0.09, x + dir * s * 0.07, y - s * 0.1); c.stroke(); c.restore();
}
/* a Lanna gable, front on: red frame, gold pediment, chofa and ngao */
function gable(c, x, y, s, w, b, t, roof, gold, n) {
  paper(c, up(x, y, s, [[-w, b], [0, t], [w, b]]), roof, 1.2);
  var iw = w * 0.74, ib = b + (t - b) * 0.06, it = t - (t - b) * 0.16;
  paper(c, up(x, y, s, [[-iw, ib], [0, it], [iw, ib]]), gold, 0.5);
  c.save(); c.strokeStyle = n ? 'rgba(80,30,10,.6)' : 'rgba(150,50,20,.55)'; c.lineWidth = Math.max(0.6, s * 0.007);
  var cx = x, cy = y - (ib + (it - ib) * 0.34) * s;
  for (var k = 0; k < 9; k++) { var a = Math.PI * (0.06 + k * 0.11); c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx - Math.cos(a) * iw * 0.8 * s, cy - Math.sin(a) * (it - ib) * 0.6 * s); c.stroke(); }
  c.beginPath(); c.arc(cx, cy, (it - ib) * 0.13 * s, 0, 6.2832); c.stroke(); c.restore();
  hook(c, x, y - t * s, s, 1, gold); hook(c, x, y - t * s, s, -1, gold);
  hook(c, x - w * s, y - b * s, s * 0.8, -1, gold); hook(c, x + w * s, y - b * s, s * 0.8, 1, gold);
}
/* a bell chedi: square tiers, the bell, rings, the spire; gold from 'from' up (0..1 of its height) */
function bellChedi(c, x, y, s, h, white, gold, from) {
  var T = function (u) { return u * h; }, cols = function (u) { return u >= from ? gold : white; };
  [[0.3, 0, 0.08], [0.25, 0.08, 0.16], [0.2, 0.16, 0.24]].forEach(function (t) { paper(c, up(x, y, s, [[-t[0], T(t[1])], [-t[0], T(t[2])], [t[0], T(t[2])], [t[0], T(t[1])]]), cols(t[1]), 1); });
  paper(c, function (q) { q.beginPath(); q.moveTo(x - 0.19 * s, y - T(0.26) * s); q.bezierCurveTo(x - 0.2 * s, y - T(0.42) * s, x - 0.1 * s, y - T(0.5) * s, x - 0.07 * s, y - T(0.52) * s);
    q.lineTo(x + 0.07 * s, y - T(0.52) * s); q.bezierCurveTo(x + 0.1 * s, y - T(0.5) * s, x + 0.2 * s, y - T(0.42) * s, x + 0.19 * s, y - T(0.26) * s); q.closePath(); }, cols(0.26), 1);
  paper(c, up(x, y, s, [[-0.06, T(0.52)], [-0.06, T(0.58)], [0.06, T(0.58)], [0.06, T(0.52)]]), cols(0.52), 0.6);
  paper(c, up(x, y, s, [[-0.045, T(0.58)], [0, T(1)], [0.045, T(0.58)]]), gold, 0.6);
  c.save(); c.strokeStyle = 'rgba(120,80,20,.45)'; c.lineWidth = Math.max(0.5, s * 0.006);
  for (var k = 0; k < 5; k++) { var v = T(0.62 + k * 0.07), hw = 0.04 * (1 - (v / T(1) - 0.58) / 0.42); c.beginPath(); c.moveTo(x - hw * s, y - v * s); c.lineTo(x + hw * s, y - v * s); c.stroke(); }
  c.restore();
}
/* the red songthaew, side on, facing dir; L its length in px */
function rotDaeng(c, x, y, L, dir, n, col) {
  var h = L * 0.5, red = col || (n ? '#7d2420' : '#c0392b'), f = function (u, v) { return [x + dir * (u - 0.5) * L, y - v * h]; };
  paper(c, poly([f(0, 0.2), f(0, 0.95), f(0.68, 0.95), f(0.68, 0.2)]), red, 1);
  paper(c, poly([f(0.68, 0.2), f(0.68, 0.78), f(0.8, 0.78), f(0.92, 0.5), f(1, 0.46), f(1, 0.2)]), red, 1);
  c.fillStyle = n ? 'rgba(255,214,140,.55)' : 'rgba(30,30,40,.6)';
  [0.04, 0.24, 0.44].forEach(function (u) { var a = f(u, 0.78), b = f(u + 0.17, 0.5); c.fillRect(Math.min(a[0], b[0]), a[1], Math.abs(b[0] - a[0]), b[1] - a[1]); });
  var wa = f(0.71, 0.74), wb = f(0.83, 0.52); c.fillStyle = 'rgba(40,50,70,.7)'; c.fillRect(Math.min(wa[0], wb[0]), wa[1], Math.abs(wb[0] - wa[0]), wb[1] - wa[1]);
  c.strokeStyle = n ? '#888' : '#d8d8d8'; c.lineWidth = Math.max(0.6, L * 0.02); c.beginPath();
  var r0 = f(0.02, 0.95), r1 = f(0.64, 0.95); c.moveTo(r0[0], r0[1] - h * 0.12); c.lineTo(r1[0], r1[1] - h * 0.12);
  for (var u = 0.06; u < 0.66; u += 0.14) { var p = f(u, 0.95); c.moveTo(p[0], p[1]); c.lineTo(p[0], p[1] - h * 0.12); } c.stroke();
  [0.18, 0.82].forEach(function (u) { var p = f(u, 0.17); c.fillStyle = '#1b1b1f'; c.beginPath(); c.arc(p[0], p[1], h * 0.17, 0, 6.2832); c.fill(); c.fillStyle = '#9a9a9a'; c.beginPath(); c.arc(p[0], p[1], h * 0.07, 0, 6.2832); c.fill(); });
  if (n) { var hl = f(1, 0.36); c.fillStyle = '#ffe9a8'; c.beginPath(); c.arc(hl[0], hl[1], h * 0.06, 0, 6.2832); c.fill(); }
}
function pigeon(c, x, y, s, dir) {
  c.fillStyle = '#7d808a'; c.beginPath(); c.ellipse(x, y - s * 0.4, s * 0.55, s * 0.32, 0, 0, 6.2832); c.fill();
  c.beginPath(); c.arc(x + dir * s * 0.45, y - s * 0.75, s * 0.2, 0, 6.2832); c.fill();
  c.fillStyle = '#5a5d66'; c.beginPath(); c.moveTo(x - dir * s * 0.4, y - s * 0.45); c.lineTo(x - dir * s * 0.95, y - s * 0.6); c.lineTo(x - dir * s * 0.45, y - s * 0.25); c.fill();
}
/* a seated Buddha, a gold glint in a niche */
function seated(c, x, y, s, gold) {
  paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.5, y); q.quadraticCurveTo(x - s * 0.45, y - s * 0.45, x - s * 0.2, y - s * 0.55); q.lineTo(x - s * 0.18, y - s * 0.75);
    q.arc(x, y - s * 0.82, s * 0.17, Math.PI * 0.8, Math.PI * 2.2); q.lineTo(x + s * 0.2, y - s * 0.55); q.quadraticCurveTo(x + s * 0.45, y - s * 0.45, x + s * 0.5, y); q.closePath(); }, gold, 0.4);
  c.fillStyle = gold; c.beginPath(); c.moveTo(x - s * 0.05, y - s * 0.97); c.lineTo(x, y - s * 1.15); c.lineTo(x + s * 0.05, y - s * 0.97); c.fill();
}

var DRAW = {
  /* Wat Phra Singh: the Lai Kham viharn's tiered gables, gold pediments, and the white chedi with its gilded spire behind */
  'wat-phra-singh': function (c, x, y, s, n) {
    var roof = n ? '#5e2418' : '#a53a24', low = n ? '#4e1e14' : '#8a2f1d', gold = n ? '#b8862e' : '#e4b23a', wall = n ? '#bdb29a' : '#f4eedf';
    bellChedi(c, x + s * 0.62, y, s * 1.05, 1.32, n ? '#cfc7b4' : '#f6f1e4', gold, 0.5);
    paper(c, up(x, y, s, [[-0.7, 0.04], [-0.7, 0.2], [0.5, 0.2], [0.5, 0.04]]), wall, 1);
    paper(c, up(x, y, s, [[-0.8, 0.2], [-0.42, 0.56], [0.22, 0.56], [0.6, 0.2], [0.54, 0.17], [-0.74, 0.17]]), low, 1.2);
    gable(c, x - s * 0.1, y, s, 0.4, 0.5, 1.08, roof, gold, n);
    paper(c, up(x, y, s, [[-0.62, 0.3], [-0.38, 0.52], [0.18, 0.52], [0.42, 0.3]]), roof, 1.2);
    paper(c, up(x, y, s, [[-0.42, 0], [-0.42, 0.42], [0.22, 0.42], [0.22, 0]]), wall, 1.2);
    gable(c, x - s * 0.1, y, s, 0.34, 0.42, 0.9, roof, gold, n);
    paper(c, up(x, y, s, [[-0.2, 0], [-0.2, 0.25], [-0.1, 0.32], [0, 0.25], [0, 0]]), gold, 0.6);
    paper(c, up(x, y, s, [[-0.175, 0], [-0.175, 0.23], [-0.1, 0.285], [-0.025, 0.23], [-0.025, 0]]), n ? '#3a1410' : '#7a1f1a', 0.3);
    if (n) { c.fillStyle = 'rgba(255,200,110,.35)'; c.fillRect(x - s * 0.17, y - s * 0.22, s * 0.14, s * 0.22); }
    paper(c, up(x, y, s, [[-0.3, 0], [-0.24, 0.06], [0.04, 0.06], [0.1, 0]]), n ? '#8a8270' : '#d9d2c0', 0.5);
    [-0.3, 0.1].forEach(function (u, i) { c.save(); c.strokeStyle = gold; c.lineWidth = Math.max(1, s * 0.02); c.lineCap = 'round'; c.beginPath();
      var bx = x + u * s, d = i ? 1 : -1; c.moveTo(bx - d * s * 0.04, y - s * 0.12); c.quadraticCurveTo(bx + d * s * 0.05, y - s * 0.12, bx + d * s * 0.03, y - s * 0.02); c.stroke(); c.restore(); });
  },
  /* Wat Chedi Luang: the great brick chedi, its top lost in the 1545 earthquake; stucco-framed arched niche,
     naga stair, the elephants round its base, a saffron cloth round its waist */
  'wat-chedi-luang': function (c, x, y, s, n) {
    var brick = n ? '#7a4e34' : '#b06a44', dark = n ? '#5e3a26' : '#93573a', stucco = n ? '#8d877a' : '#c9c3b4', line = 'rgba(60,25,10,.28)';
    if (n) { var g = c.createRadialGradient(x, y - s * 0.6, 0, x, y - s * 0.6, s * 1.2); g.addColorStop(0, 'rgba(255,190,90,.35)'); g.addColorStop(1, 'rgba(255,190,90,0)'); c.fillStyle = g; c.fillRect(x - s * 1.2, y - s * 1.8, s * 2.4, s * 1.8); }
    paper(c, up(x, y, s, [[-0.9, 0], [-0.9, 0.2], [0.9, 0.2], [0.9, 0]]), dark, 1.6);
    paper(c, up(x, y, s, [[-0.72, 0.2], [-0.7, 0.4], [0.7, 0.4], [0.72, 0.2]]), brick, 1.4);
    paper(c, up(x, y, s, [[-0.55, 0.4], [-0.53, 0.6], [0.53, 0.6], [0.55, 0.4]]), dark, 1.3);
    paper(c, up(x, y, s, [[-0.4, 0.6], [-0.38, 0.88], [-0.32, 0.95], [-0.24, 1.02], [-0.16, 1.1], [-0.07, 1.13], [0.0, 1.05], [0.07, 1.12], [0.15, 1.04], [0.24, 0.99], [0.31, 0.93], [0.38, 0.88], [0.4, 0.6]]), brick, 1.4);
    courses(c, x, y, s, -0.9, 0.9, 0, 0.2, line); courses(c, x, y, s, -0.7, 0.7, 0.2, 0.4, line); courses(c, x, y, s, -0.53, 0.53, 0.4, 0.6, line); courses(c, x, y, s, -0.38, 0.38, 0.6, 0.95, line);
    stains(c, x, y, s, -0.8, 0.8, 0.05, 0.95, 1545, n ? 'rgba(20,20,10,.18)' : 'rgba(60,70,40,.2)');
    c.fillStyle = n ? '#2f4a2a' : '#5f8a4a'; [[-0.1, 1.11], [0.08, 1.1], [0.22, 1.0]].forEach(function (p) { c.beginPath(); c.arc(x + p[0] * s, y - p[1] * s, s * 0.035, 0, 6.2832); c.fill(); });
    [-0.36, 0.36].forEach(function (u) { paper(c, up(x, y, s, [[u - 0.05, 0.88], [u - 0.03, 0.98], [u, 1.03], [u + 0.03, 0.98], [u + 0.05, 0.88]]), stucco, 0.6); });
    paper(c, up(x, y, s, [[-0.4, 0.6], [-0.4, 0.66], [0.4, 0.66], [0.4, 0.6]]), n ? '#b8661a' : '#f09a1e', 0.6);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.15, y - s * 0.6); q.lineTo(x - s * 0.15, y - s * 0.8); q.bezierCurveTo(x - s * 0.15, y - s * 0.92, x - s * 0.03, y - s * 0.95, x, y - s * 1.0);
      q.bezierCurveTo(x + s * 0.03, y - s * 0.95, x + s * 0.15, y - s * 0.92, x + s * 0.15, y - s * 0.8); q.lineTo(x + s * 0.15, y - s * 0.6); q.closePath(); }, stucco, 0.9);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.08, y - s * 0.62); q.lineTo(x - s * 0.08, y - s * 0.8); q.arc(x, y - s * 0.8, s * 0.08, Math.PI, 0); q.lineTo(x + s * 0.08, y - s * 0.62); q.closePath(); }, n ? '#2a1a12' : '#3a2418', 0.3);
    seated(c, x, y - s * 0.63, s * 0.12, n ? '#ffcf6a' : '#e4b23a');
    paper(c, up(x, y, s, [[-0.2, 0], [-0.09, 0.6], [0.09, 0.6], [0.2, 0]]), n ? '#5a4030' : '#8a6248', 1);
    c.save(); c.strokeStyle = 'rgba(30,15,5,.35)'; c.lineWidth = Math.max(0.5, s * 0.006);
    for (var v = 0.04; v < 0.6; v += 0.045) { var hw = 0.2 - v / 0.6 * 0.11; c.beginPath(); c.moveTo(x - hw * s, y - v * s); c.lineTo(x + hw * s, y - v * s); c.stroke(); }
    c.restore();
    [-1, 1].forEach(function (d) {
      c.save(); c.strokeStyle = stucco; c.lineWidth = Math.max(1.4, s * 0.04); c.lineCap = 'round'; c.shadowColor = 'rgba(0,0,0,.35)'; c.shadowBlur = 3; c.shadowOffsetY = 1.5;
      c.beginPath(); c.moveTo(x + d * s * 0.1, y - s * 0.6); c.lineTo(x + d * s * 0.22, y - s * 0.06); c.stroke();
      c.beginPath(); c.moveTo(x + d * s * 0.22, y - s * 0.06); c.quadraticCurveTo(x + d * s * 0.3, y - s * 0.12, x + d * s * 0.27, y - s * 0.24); c.stroke(); c.restore();
      paper(c, up(x, y, s, [[d * 0.27 - 0.045, 0.2], [d * 0.27 + d * 0.06, 0.29], [d * 0.27 + 0.045, 0.2]]), stucco, 0.5);
    });
    for (var e = 0; e < 8; e++) {
      var ex = -0.78 + e * 0.2 + (e > 3 ? 0.16 : 0); if (Math.abs(ex) < 0.26) continue;
      var hx = x + ex * s, hy = y - s * 0.14, r = s * 0.055;
      paper(c, function (q) { q.beginPath(); q.arc(hx, hy, r, Math.PI, 0); q.lineTo(hx + r * 0.35, hy + r * 1.6); q.lineTo(hx - r * 0.35, hy + r * 1.6); q.closePath(); }, stucco, 0.6);
      c.fillStyle = 'rgba(0,0,0,.25)'; c.beginPath(); c.ellipse(hx - r * 1.05, hy + r * 0.2, r * 0.45, r * 0.75, 0, 0, 6.2832); c.ellipse(hx + r * 1.05, hy + r * 0.2, r * 0.45, r * 0.75, 0, 0, 6.2832); c.fill();
    }
  },
  /* the Three Kings, bronze, with yellow sashes, before the white Arts and Cultural Centre */
  'three-kings': function (c, x, y, s, n) {
    var wall = n ? '#b9b3a4' : '#f3efe4', roof = n ? '#6e3020' : '#c0583a', bronze = n ? '#2c2c2b' : '#4d4e4c', sash = n ? '#b88c1c' : '#f0b81e';
    paper(c, up(x, y, s, [[-0.88, 0.12], [-0.88, 0.5], [0.88, 0.5], [0.88, 0.12]]), wall, 1.1);
    paper(c, up(x, y, s, [[-0.95, 0.5], [-0.74, 0.66], [0.74, 0.66], [0.95, 0.5]]), roof, 1.1);
    paper(c, up(x, y, s, [[-0.2, 0.62], [0, 0.82], [0.2, 0.62]]), roof, 1);
    paper(c, up(x, y, s, [[-0.15, 0.64], [0, 0.78], [0.15, 0.64]]), wall, 0.4);
    c.fillStyle = '#d9a63a'; c.beginPath(); c.arc(x, y - s * 0.69, s * 0.025, 0, 6.2832); c.fill();
    c.fillStyle = n ? 'rgba(255,214,140,.55)' : 'rgba(60,70,80,.55)';
    for (var i = -6; i <= 6; i++) { if (Math.abs(i) < 2) continue; c.fillRect(x + i * s * 0.12 - s * 0.025, y - s * 0.44, s * 0.05, s * 0.1); c.fillRect(x + i * s * 0.12 - s * 0.025, y - s * 0.28, s * 0.05, s * 0.1); }
    paper(c, up(x, y, s, [[-0.48, 0], [-0.48, 0.12], [0.48, 0.12], [0.48, 0]]), n ? '#8d877a' : '#d6cfbf', 1.2);
    [[-0.27, 0.9, -1], [0, 0.82, 0], [0.27, 0.92, 1]].forEach(function (k) {
      var fx = x + k[0] * s, b = y - s * 0.12, h = k[1] * s, arm = k[2];
      paper(c, function (q) { q.beginPath();
        q.moveTo(fx - h * 0.1, b); q.lineTo(fx - h * 0.09, b - h * 0.4); q.lineTo(fx - h * 0.08, b - h * 0.5); q.lineTo(fx - h * 0.12, b - h * 0.78); q.lineTo(fx - h * 0.04, b - h * 0.8);
        q.lineTo(fx - h * 0.035, b - h * 0.84); q.arc(fx, b - h * 0.88, h * 0.05, Math.PI * 0.7, Math.PI * 2.3); q.lineTo(fx + h * 0.04, b - h * 0.8); q.lineTo(fx + h * 0.12, b - h * 0.78);
        q.lineTo(fx + h * 0.08, b - h * 0.5); q.lineTo(fx + h * 0.09, b - h * 0.4); q.lineTo(fx + h * 0.1, b); q.closePath(); }, bronze, 1.2);
      paper(c, poly([[fx - h * 0.03, b - h * 0.92], [fx, b - h * 1.04], [fx + h * 0.03, b - h * 0.92]]), bronze, 0.5);
      c.save(); c.strokeStyle = bronze; c.lineWidth = Math.max(1.6, h * 0.05); c.lineCap = 'round'; c.lineJoin = 'round';
      [-1, 1].forEach(function (sd) {
        c.beginPath(); c.moveTo(fx + sd * h * 0.11, b - h * 0.76);
        if (arm === sd || (arm === 0 && sd === 1)) { c.lineTo(fx + sd * h * 0.22, b - h * 0.62); c.lineTo(fx + sd * h * 0.09, b - h * 0.5); }
        else c.lineTo(fx + sd * h * 0.15, b - h * 0.48);
        c.stroke(); });
      c.restore();
      paper(c, poly([[fx - h * 0.1, b - h * 0.47], [fx + h * 0.1, b - h * 0.5], [fx + h * 0.1, b - h * 0.44], [fx - h * 0.1, b - h * 0.41]]), sash, 0.5);
      paper(c, poly([[fx + h * 0.01, b - h * 0.44], [fx + h * 0.05, b - h * 0.44], [fx + h * 0.07, b - h * 0.24], [fx + h * 0.02, b - h * 0.26]]), sash, 0.5);
    });
  },
  /* Tha Phae Gate: the orange brick wall, its merlons and slits, the timber doors open, pigeons on the square */
  'tha-phae-gate': function (c, x, y, s, n) {
    var w = 0.82, top = 0.5, m = 0.1, brick = n ? '#9a4e2e' : '#c46a3e', dark = n ? '#7a3b22' : '#a95634';
    if (n) { var g = c.createRadialGradient(x, y, 0, x, y, s * 1.1); g.addColorStop(0, 'rgba(255,170,80,.4)'); g.addColorStop(1, 'rgba(255,170,80,0)'); c.fillStyle = g; c.fillRect(x - s * 1.1, y - s * 1.1, s * 2.2, s * 1.1); }
    var pts = [[-w, 0], [-w, top]];
    for (var u = -w; u < w - 0.01; u += m * 1.7) { var u1 = Math.min(w, u + m); pts.push([u, top + 0.11], [u1, top + 0.11], [u1, top]); if (u1 < w) pts.push([Math.min(w, u + m * 1.7), top]); }
    pts.push([w, top], [w, 0], [0.17, 0], [0.17, 0.34], [-0.17, 0.34], [-0.17, 0]);
    paper(c, up(x, y, s, pts), brick, 1.6);
    paper(c, up(x, y, s, [[-w - 0.02, 0], [-w - 0.02, 0.06], [-0.17, 0.06], [-0.17, 0]]), dark, 0.6);
    paper(c, up(x, y, s, [[0.17, 0], [0.17, 0.06], [w + 0.02, 0.06], [w + 0.02, 0]]), dark, 0.6);
    courses(c, x, y, s, -w, -0.17, 0.06, top, 'rgba(70,25,10,.3)', 0.06); courses(c, x, y, s, 0.17, w, 0.06, top, 'rgba(70,25,10,.3)', 0.06); courses(c, x, y, s, -0.17, 0.17, 0.34, top, 'rgba(70,25,10,.3)', 0.06);
    stains(c, x, y, s, -w, w, 0.08, top, 1296, n ? 'rgba(20,10,5,.2)' : 'rgba(90,40,20,.2)');
    c.fillStyle = 'rgba(40,12,5,.55)';
    for (u = -w; u < w - 0.01; u += m * 1.7) c.fillRect(x + (u + m * 0.42) * s, y - (top + 0.08) * s, Math.max(1, m * 0.16 * s), m * 0.5 * s);
    c.fillStyle = n ? '#2a1610' : '#3d2418'; c.fillRect(x - s * 0.17, y - s * 0.34, s * 0.34, s * 0.34);
    if (n) { c.fillStyle = 'rgba(255,200,120,.25)'; c.fillRect(x - s * 0.17, y - s * 0.34, s * 0.34, s * 0.34); }
    [-1, 1].forEach(function (d) {
      var hx = x + d * s * 0.17; paper(c, poly([[hx, y], [hx, y - s * 0.34], [hx - d * s * 0.1, y - s * 0.31], [hx - d * s * 0.1, y - s * 0.02]]), n ? '#4a3020' : '#7a5232', 0.8);
      c.strokeStyle = 'rgba(30,15,5,.45)'; c.lineWidth = Math.max(0.5, s * 0.006);
      for (var k = 1; k < 4; k++) { c.beginPath(); c.moveTo(hx - d * s * 0.025 * k, y - s * (0.34 - 0.008 * k)); c.lineTo(hx - d * s * 0.025 * k, y - s * 0.01 * k); c.stroke(); }
    });
    paper(c, up(x, y, s, [[-0.6, 0.2], [-0.6, 0.32], [-0.38, 0.32], [-0.38, 0.2]]), n ? '#3a3026' : '#51463a', 0.5);
    c.fillStyle = '#e4b23a'; for (var k2 = 0; k2 < 3; k2++) c.fillRect(x - s * 0.57, y - s * (0.29 - k2 * 0.03), s * 0.16, Math.max(0.6, s * 0.008));
    if (!n) [[-0.5, 0.0, 1], [-0.42, 0.0, -1], [0.36, 0.0, 1], [0.62, 0.0, -1], [0.48, -0.0, 1], [-0.7, top + 0.11, 1], [0.21, top + 0.11, -1]].forEach(function (p) { pigeon(c, x + p[0] * s, y - p[1] * s, s * 0.045, p[2]); });
  },
  /* Kad Luang: the market hall, its sign, red songthaews loading out front, marigolds on the kerb */
  'warorot': function (c, x, y, s, n) {
    var wall = n ? '#8f8670' : '#e6dcc4', band = n ? '#6e6656' : '#c9bea4';
    paper(c, up(x, y, s, [[-0.74, 0], [-0.74, 0.66], [0.74, 0.66], [0.74, 0]]), wall, 1.4);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - 0.8 * s, y - 0.66 * s); q.quadraticCurveTo(x, y - 0.86 * s, x + 0.8 * s, y - 0.66 * s); q.closePath(); }, n ? '#4a5866' : '#7d93a3', 1.2);
    [0.22, 0.44].forEach(function (v) { paper(c, up(x, y, s, [[-0.74, v], [-0.74, v + 0.03], [0.74, v + 0.03], [0.74, v]]), band, 0.4); });
    c.fillStyle = n ? 'rgba(255,214,140,.6)' : 'rgba(55,65,75,.55)';
    for (var i = 0; i < 9; i++) { var wx = x + (-0.66 + i * 0.165) * s; c.fillRect(wx, y - 0.4 * s, s * 0.1, s * 0.12); c.fillRect(wx, y - 0.6 * s, s * 0.1, s * 0.11); }
    c.fillStyle = n ? '#2a2018' : '#4a3a2c'; c.fillRect(x - 0.66 * s, y - 0.2 * s, 1.32 * s, 0.2 * s);
    var aw = ['#e5567f', '#e2b33c', '#4fae8c', '#4d8fd1', '#e86a2a', '#b692ff'];
    for (i = 0; i < 6; i++) paper(c, up(x, y, s, [[-0.66 + i * 0.22, 0.2], [-0.66 + i * 0.22 + 0.22, 0.2], [-0.66 + i * 0.22 + 0.2, 0.14], [-0.66 + i * 0.22 + 0.02, 0.14]]), aw[i], 0.4);
    paper(c, up(x, y, s, [[-0.32, 0.68], [-0.32, 0.8], [0.32, 0.8], [0.32, 0.68]]), n ? '#7a1f1a' : '#b8281f', 0.8);
    var fs = Math.round(s * 0.1); if (fs >= 7) { c.fillStyle = '#fff3d0'; c.font = '700 ' + fs + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('กาดหลวง', x, y - 0.74 * s); }
    rotDaeng(c, x - 0.42 * s, y + s * 0.02, s * 0.62, 1, n);
    rotDaeng(c, x + 0.5 * s, y + s * 0.02, s * 0.58, -1, n);
    var r = rnd(7); c.save();
    for (i = 0; i < 9; i++) { c.fillStyle = r() < 0.6 ? '#f39a1e' : '#f6c531'; c.beginPath(); c.arc(x + (-0.02 + r() * 0.12) * s, y - (0.02 + r() * 0.08) * s, s * 0.028, 0, 6.2832); c.fill(); }
    c.restore();
  },
  /* the Iron Bridge: three camelback truss spans on piers in the Ping */
  'iron-bridge': function (c, x, y, s, n) {
    var w = s * 1.62, iron = n ? '#34424f' : '#4a5d6c', span = w / 3;
    paper(c, poly([[x - w / 2 - s * 0.1, y + s * 0.06], [x + w / 2 + s * 0.1, y + s * 0.06], [x + w / 2 + s * 0.1, y + s * 0.22], [x - w / 2 - s * 0.1, y + s * 0.22]]), n ? '#2a4c7a' : '#6f8f8a', 0.8);
    for (var p = 0; p <= 3; p++) paper(c, up(x - w / 2 + p * span, y, s, [[-0.04, -0.2], [-0.04, 0.02], [0.04, 0.02], [0.04, -0.2]]), n ? '#5a5a58' : '#a9a49a', 0.8);
    c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 4; c.shadowOffsetY = 2; c.strokeStyle = iron; c.lineCap = 'round'; c.lineJoin = 'round';
    for (var k = 0; k < 3; k++) {
      var a = x - w / 2 + k * span, tops = [], j;
      for (j = 0; j <= 6; j++) { var u = j / 6; tops.push([a + u * span, y - s * (0.1 + 0.2 * Math.sin(Math.PI * Math.min(1, Math.max(0, (u - 0.04) / 0.92))))]); }
      c.lineWidth = Math.max(1.6, s * 0.035); c.beginPath(); c.moveTo(a, y); c.lineTo(a + span, y); tops.forEach(function (t, i) { i ? c.lineTo(t[0], t[1]) : c.moveTo(a, y - s * 0.02); }); c.stroke();
      c.lineWidth = Math.max(0.8, s * 0.014); c.beginPath();
      for (j = 1; j < 6; j++) { c.moveTo(tops[j][0], tops[j][1]); c.lineTo(tops[j][0], y); c.moveTo(tops[j][0], tops[j][1]); c.lineTo(tops[j < 3 ? j - 1 : j + 1][0], y); }
      c.stroke();
    }
    c.restore();
    if (n) { c.fillStyle = '#ffd88a'; for (k = 0; k <= 3; k++) { c.beginPath(); c.arc(x - w / 2 + k * span, y - s * 0.06, s * 0.018, 0, 6.2832); c.fill(); } }
  },
  /* the Night Bazaar: the arched hall over the stalls, red lanterns strung across Chang Khlan Road */
  'night-bazaar': function (c, x, y, s, n) {
    paper(c, function (q) { q.beginPath(); q.moveTo(x - 0.7 * s, y - 0.34 * s); q.bezierCurveTo(x - 0.66 * s, y - 0.7 * s, x + 0.66 * s, y - 0.7 * s, x + 0.7 * s, y - 0.34 * s); q.closePath(); }, n ? '#cfc8b6' : '#f1ede3', 1.2);
    c.save(); c.strokeStyle = 'rgba(80,80,90,.35)'; c.lineWidth = Math.max(0.6, s * 0.008);
    for (var k = 1; k < 6; k++) { var u = -0.7 + k * 0.233; c.beginPath(); c.moveTo(x + u * s, y - 0.34 * s); c.lineTo(x + u * 0.6 * s, y - 0.6 * s); c.stroke(); }
    c.restore();
    paper(c, up(x, y, s, [[-0.68, 0], [-0.68, 0.34], [0.68, 0.34], [0.68, 0]]), n ? '#2e2420' : '#5a4a3e', 1);
    var cl = ['#e5567f', '#e2b33c', '#4fae8c', '#4d8fd1', '#b692ff', '#f08a5d', '#f2f2f2'], r = rnd(22);
    for (var i = 0; i < 14; i++) { c.fillStyle = cl[i % cl.length]; c.fillRect(x + (-0.64 + i * 0.093) * s, y - (0.06 + r() * 0.06) * s - 0.16 * s, s * 0.07, (0.14 + r() * 0.06) * s); }
    c.fillStyle = n ? '#fff0b8' : '#fff7da'; for (i = 0; i < 6; i++) { c.beginPath(); c.arc(x + (-0.56 + i * 0.22) * s, y - 0.31 * s, s * (n ? 0.022 : 0.014), 0, 6.2832); c.fill(); }
    [0.62, 0.8].forEach(function (hy, row) {
      var xa = x - 0.86 * s, xb = x + 0.86 * s, top = y - hy * s, sag = s * 0.09;
      c.strokeStyle = 'rgba(30,20,20,.7)'; c.lineWidth = 0.8; c.beginPath();
      for (var j = 0; j <= 20; j++) { var u = j / 20, px = xa + (xb - xa) * u, py = top + sag * 4 * u * (1 - u); j ? c.lineTo(px, py) : c.moveTo(px, py); } c.stroke();
      for (j = 1; j < 10; j++) { var u2 = (j + row * 0.5) / 10.5, lx = xa + (xb - xa) * u2, ly = top + sag * 4 * u2 * (1 - u2) + s * 0.04;
        if (n) { var g = c.createRadialGradient(lx, ly, 0, lx, ly, s * 0.1); g.addColorStop(0, 'rgba(255,90,60,.45)'); g.addColorStop(1, 'rgba(255,90,60,0)'); c.fillStyle = g; c.fillRect(lx - s * 0.1, ly - s * 0.1, s * 0.2, s * 0.2); }
        c.fillStyle = n ? '#ff4a3a' : '#d42a24'; c.beginPath(); c.ellipse(lx, ly, s * 0.03, s * 0.036, 0, 0, 6.2832); c.fill();
        c.fillStyle = '#e8b84a'; c.fillRect(lx - s * 0.012, ly - s * 0.044, s * 0.024, s * 0.012); }
    });
  },
  'wat-phra-kaew-cr': function (c, x, y, s, n) { DRAW['wat-phra-singh'](c, x, y, s, n); },
  /* Chalermchai Kositpipat's clock tower: gilded tiers, flame-cut edges, the clock, the spire; lit purple-gold for the shows */
  'clock-tower': function (c, x, y, s, n) {
    var gold = n ? '#e2a84a' : '#d9a63a', deep = n ? '#a8702a' : '#b0832a';
    if (n) { var g = c.createRadialGradient(x, y - s * 0.6, 0, x, y - s * 0.6, s * 1.1); g.addColorStop(0, 'rgba(220,90,255,.45)'); g.addColorStop(1, 'rgba(220,90,255,0)'); c.fillStyle = g; c.fillRect(x - s * 1.1, y - s * 1.7, s * 2.2, s * 1.7); }
    var flames = function (y0, hw, hgt, k) { var pts = [[-hw, y0]]; for (var i = 0; i <= k; i++) { var u = -hw + i * 2 * hw / k; pts.push([u, y0 + (i % 2 ? hgt : hgt * 0.35)]); } pts.push([hw, y0]); return pts; };
    paper(c, up(x, y, s, flames(0, 0.5, 0.14, 14)), deep, 1);
    paper(c, up(x, y, s, [[-0.42, 0], [-0.34, 0.12], [0.34, 0.12], [0.42, 0]]), gold, 1.2);
    paper(c, up(x, y, s, [[-0.22, 0.12], [-0.2, 0.46], [0.2, 0.46], [0.22, 0.12]]), gold, 1.4);
    c.fillStyle = 'rgba(80,50,10,.35)'; c.beginPath(); c.moveTo(x - s * 0.08, y - s * 0.12); c.lineTo(x - s * 0.08, y - s * 0.3); c.quadraticCurveTo(x, y - s * 0.42, x + s * 0.08, y - s * 0.3); c.lineTo(x + s * 0.08, y - s * 0.12); c.fill();
    paper(c, up(x, y, s, flames(0.44, 0.3, 0.08, 10)), deep, 0.8);
    paper(c, up(x, y, s, [[-0.17, 0.48], [-0.17, 0.74], [0.17, 0.74], [0.17, 0.48]]), gold, 1.3);
    paper(c, function (q) { circ(q, x, y - s * 0.61, s * 0.085, 4); }, '#fff6dc', 0.5);
    c.strokeStyle = '#3a2a10'; c.lineWidth = Math.max(0.8, s * 0.012); c.beginPath(); c.moveTo(x, y - s * 0.61); c.lineTo(x, y - s * 0.67); c.moveTo(x, y - s * 0.61); c.lineTo(x + s * 0.04, y - s * 0.6); c.stroke();
    [[0.74, 0.3, 0.96], [0.9, 0.22, 1.1], [1.04, 0.15, 1.22]].forEach(function (t) {
      paper(c, up(x, y, s, [[-t[1], t[0]], [0, t[2]], [t[1], t[0]]]), gold, 1);
      hook(c, x - t[1] * s, y - t[0] * s, s * 0.9, -1, deep); hook(c, x + t[1] * s, y - t[0] * s, s * 0.9, 1, deep);
    });
    paper(c, up(x, y, s, [[-0.035, 1.18], [0, 1.52], [0.035, 1.18]]), gold, 0.6);
  },
  'cr-night-bazaar': function (c, x, y, s, n) { DRAW['night-bazaar'](c, x, y, s, n); }
};
/* Doi Suthep's gilded chedi on its shoulder of the ridge, its corner parasols, u its height unit */
function suthepChedi(c, sx, sy, u, night) {
  var gold = '#e9b949', deep = '#c8932e';
  paper(c, up(sx, sy, u, [[-1.3, 0], [-1.3, 0.35], [1.3, 0.35], [1.3, 0]]), deep, 0.6);
  paper(c, up(sx, sy, u, [[-1, 0.35], [-1, 0.7], [1, 0.7], [1, 0.35]]), gold, 0.6);
  paper(c, function (q) { q.beginPath(); q.moveTo(sx - u * 0.85, sy - u * 0.7); q.bezierCurveTo(sx - u * 0.9, sy - u * 1.5, sx - u * 0.35, sy - u * 1.75, sx, sy - u * 1.8); q.bezierCurveTo(sx + u * 0.35, sy - u * 1.75, sx + u * 0.9, sy - u * 1.5, sx + u * 0.85, sy - u * 0.7); q.closePath(); }, gold, 0.8);
  paper(c, up(sx, sy, u, [[-0.22, 1.75], [0, 3.6], [0.22, 1.75]]), gold, 0.6);
  c.strokeStyle = deep; c.lineWidth = 0.8; c.beginPath();
  for (var k = 0; k < 4; k++) { var v = 1.95 + k * 0.32, hw = 0.2 * (1 - (v - 1.75) / 1.85); c.moveTo(sx - hw * u, sy - v * u); c.lineTo(sx + hw * u, sy - v * u); }
  c.stroke();
  [-1, 1].forEach(function (d) { var px = sx + d * u * 1.7; c.strokeStyle = deep; c.lineWidth = 0.8; c.beginPath(); c.moveTo(px, sy); c.lineTo(px, sy - u * 2.1); c.stroke();
    [0, 0.3, 0.55].forEach(function (v, i) { var hw = u * (0.45 - i * 0.1); c.fillStyle = gold; c.beginPath(); c.moveTo(px - hw, sy - u * (1.75 + v)); c.lineTo(px, sy - u * (1.95 + v)); c.lineTo(px + hw, sy - u * (1.75 + v)); c.fill(); }); });
}

function ridgeY(o, W, H, x, scale, off) {
  var R = o.ridge;
  if (!o.cr && R && R.ele) { var lng = 98.8 + (x / W) * 0.26, j = Math.max(0, Math.min(R.ele.length - 1, Math.round((lng - R.lon_a) / R.step))); return o.horizon - off - (R.ele[j] - 300) / 1400 * H * scale; }
  return o.horizon - off - (Math.sin(x * 0.006 + 1) * 0.5 + 0.6) * H * scale * 0.5 - Math.sin(x * 0.019) * 6;
}

function landscape(c, W, H, o) {
  var hits = [], night = o.night, hz = o.horizon, sc = o.phone ? 0.22 : 0.3, xx;
  var far = []; for (xx = -6; xx <= W + 6; xx += 5) far.push([xx, ridgeY(o, W, H, xx, sc, 0)]); far.push([W + 6, H + 6], [-6, H + 6]);
  paper(c, function (q) { jag(q, far, 31, 1.5); }, night ? '#24352f' : '#3f6b52', 1.6);
  var set = SIGHTS[o.cr ? 'cr' : 'cm'];
  /* Doi Suthep's chedi on its own shoulder */
  set.filter(function (s) { return s.ridge; }).forEach(function (s) {
    var sx = (s.lng - 98.8) / 0.26 * W, sy = ridgeY(o, W, H, sx, sc, 0) - 2, u = o.phone ? 4.2 : 5.6;
    suthepChedi(c, sx, sy, u, night);
    if (night) { var g = c.createRadialGradient(sx, sy - u, 0, sx, sy - u, u * 4); g.addColorStop(0, 'rgba(255,214,120,.5)'); g.addColorStop(1, 'rgba(255,214,120,0)'); c.fillStyle = g; c.fillRect(sx - u * 4, sy - u * 5, u * 8, u * 8); }
    hits.push({ k: s.k, x0: sx - 22, x1: sx + 22, y0: sy - u * 4, y1: sy + 10 });
  });
  var haze = Math.min(0.62, Math.max(0.04, ((o.pm25 || 10) - 8) / 120));
  c.fillStyle = (night ? 'rgba(62,64,84,' : 'rgba(236,224,200,') + haze + ')'; c.fillRect(0, 0, W, hz + 4);
  var near = []; for (xx = -6; xx <= W + 6; xx += 8) near.push([xx, hz - (o.phone ? 8 : 14) - Math.sin(xx * 0.013 + 2) * 6 - Math.sin(xx * 0.041) * 3]); near.push([W + 6, H + 6], [-6, H + 6]);
  paper(c, function (q) { jag(q, near, 37, 2); }, night ? '#1d2a24' : '#5b8a5e', 1.8);
  /* the river along the foot of the city: as wide as the Ping stands on its gauge (o.river, front.js) */
  var rw = o.river ? o.river.w : 10, rv = []; for (xx = -6; xx <= W + 6; xx += 10) rv.push([xx, hz + 6 + Math.sin(xx * 0.02) * 3]);
  for (xx = W + 6; xx >= -6; xx -= 10) rv.push([xx, hz + 6 + rw + Math.sin(xx * 0.02 + 0.8) * 3]);
  paper(c, function (q) { jag(q, rv, 41, 1.5); }, o.river ? o.river.col : night ? '#2a4c7a' : '#4b8fc9', 1.2);
  hits.river = [hz + 6, hz + 6 + rw];
  hits.ridgeAt = function (x) { return ridgeY(o, W, H, x, sc, 0); };
  /* the city's sights, west to east, spaced across the room they are given */
  var city = set.filter(function (s) { return !s.ridge; }), x0 = o.x0 == null ? W * 0.04 : o.x0, x1 = o.x1 == null ? W * 0.96 : o.x1;
  var gap = (x1 - x0) / city.length, u2 = Math.min(gap * (o.phone ? 0.62 : 0.54), H * (o.phone ? 0.15 : 0.16));
  city.forEach(function (s, i) {
    var sx = x0 + gap * (i + 0.5), sy = hz + 4;
    DRAW[s.k](c, sx, sy, u2, night);
    hits.push({ k: s.k, x0: sx - gap / 2, x1: sx + gap / 2, y0: sy - u2 * 1.4, y1: sy + 8 });
  });
  return hits;
}

/* ---------------------------------------------------------------- the rooftop Latin night
   String lights hung as catenaries, y = a·cosh(x/a). In each couple the leader walks a
   lemniscate of Gerono, x = sin t, y = sin t·cos t, and the partner turns about the
   leader at three times the beat. Six couples, partners of every kind. */
var COUPLES = [
  [{ skirt: 0, hair: 0, col: '#ffc266' }, { skirt: 1, hair: 1, col: '#ff5a8c' }],
  [{ skirt: 1, hair: 1, col: '#b692ff' }, { skirt: 1, hair: 2, col: '#7fe0a4' }],
  [{ skirt: 0, hair: 0, col: '#7fd8ff' }, { skirt: 0, hair: 0, col: '#ff9a5a' }],
  [{ skirt: 0, hair: 0, col: '#f2f2f2' }, { skirt: 1, hair: 1, col: '#e5567f' }],
  [{ skirt: 1, hair: 2, col: '#ffd1e8' }, { skirt: 0, hair: 1, col: '#4fae8c' }],
  [{ skirt: 0, hair: 0, col: '#e2b33c' }, { skirt: 1, hair: 1, col: '#9b6bd6' }]
];
function figure(c, p, h, d, hand, beat, k) {
  var hip = [p[0], p[1] - h * 0.45], sh = [p[0], p[1] - h * 0.8], step = Math.sin(beat * 2 + k) * h * 0.08;
  c.save(); c.shadowColor = 'rgba(0,0,0,.45)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2;
  c.strokeStyle = d.col; c.fillStyle = d.col; c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = Math.max(2, h * 0.075);
  c.beginPath(); c.moveTo(p[0] - h * 0.1 + step, p[1]); c.lineTo(hip[0], hip[1]); c.lineTo(p[0] + h * 0.1 - step, p[1]);
  c.moveTo(hip[0], hip[1]); c.lineTo(sh[0], sh[1]); c.lineTo(hand[0], hand[1]);
  var up = Math.sin(beat + k) > 0;
  c.moveTo(sh[0], sh[1]); c.lineTo(sh[0] + (hand[0] > sh[0] ? -1 : 1) * h * 0.2, sh[1] - (up ? h * 0.25 : -h * 0.05)); c.stroke();
  if (d.skirt) { var sw = h * (0.16 + 0.12 * Math.abs(Math.sin(beat * 1.5 + k))); c.beginPath(); c.moveTo(p[0], p[1] - h * 0.66); c.lineTo(p[0] - sw, p[1] - h * 0.26); c.lineTo(p[0] + sw, p[1] - h * 0.26); c.closePath(); c.fill(); }
  c.beginPath(); c.arc(p[0], p[1] - h * 0.93, h * 0.11, 0, 6.2832); c.fill();
  if (d.hair === 1) { c.beginPath(); c.ellipse(p[0] + (hand[0] > p[0] ? -1 : 1) * h * 0.12, p[1] - h * 0.9, h * 0.05, h * 0.12, 0.5, 0, 6.2832); c.fill(); }
  if (d.hair === 2) { c.beginPath(); c.arc(p[0], p[1] - h * 1.06, h * 0.07, 0, 6.2832); c.fill(); }
  c.restore();
}
function latinNight(c, W, H, t, o) {
  var x0 = o.x0 == null ? 0 : o.x0, x1 = o.x1 == null ? W : o.x1, deck = o.deck, span = x1 - x0, hits = [];
  var hh = Math.min(H * (o.phone ? 0.2 : 0.24), span / 8, 90);
  /* the deck and its rail */
  paper(c, poly([[x0 - 4, deck], [x1 + 4, deck], [x1 + 4, H + 4], [x0 - 4, H + 4]]), '#2a1a22', 2);
  c.strokeStyle = 'rgba(255,200,140,.28)'; c.lineWidth = 1;
  c.beginPath(); c.moveTo(x0, deck); c.lineTo(x1, deck); c.stroke();
  /* poles and lights */
  var np = Math.max(3, Math.round(span / 220) + 1), top = deck - hh * 2.3, sag = hh * 0.45, i, x;
  var poles = []; for (i = 0; i < np; i++) poles.push(x0 + span * (0.02 + 0.96 * i / (np - 1)));
  c.strokeStyle = 'rgba(255,255,255,.22)'; c.lineWidth = 2;
  poles.forEach(function (px) { c.beginPath(); c.moveTo(px, top - 4); c.lineTo(px, deck); c.stroke(); });
  for (i = 0; i < poles.length - 1; i++) {
    var a0 = poles[i], a1 = poles[i + 1], xm = (a0 + a1) / 2, half = (a1 - a0) / 2, a = half / 1.4, ch = Math.cosh(half / a) - 1;
    var cat = function (xq) { return top + sag - sag * (Math.cosh((xq - xm) / a) - 1) / ch; };
    c.strokeStyle = 'rgba(40,20,30,.9)'; c.lineWidth = 1.2; c.beginPath();
    for (x = a0; x <= a1; x += 4) x === a0 ? c.moveTo(x, cat(x)) : c.lineTo(x, cat(x)); c.stroke();
    for (x = a0 + 12, k = 0; x < a1 - 6; x += 22, k++) {
      var yb = cat(x) + 5, on = 0.55 + 0.45 * Math.sin(t / 380 + k * 1.7 + i), hue = [42, 340, 190, 55][(k + i) % 4];
      var gb = c.createRadialGradient(x, yb, 0, x, yb, 13); gb.addColorStop(0, 'hsla(' + hue + ',100%,70%,' + 0.55 * on + ')'); gb.addColorStop(1, 'hsla(' + hue + ',100%,60%,0)');
      c.fillStyle = gb; c.beginPath(); c.arc(x, yb, 13, 0, 6.2832); c.fill();
      c.fillStyle = 'hsla(' + hue + ',100%,85%,' + (0.5 + 0.5 * on) + ')'; c.beginPath(); c.arc(x, yb, 2.4, 0, 6.2832); c.fill();
    }
  }
  var k;
  /* the banner, hung from the middle span */
  if (o.label) {
    var bx = (poles[Math.floor((np - 1) / 2)] + poles[Math.floor((np - 1) / 2) + 1]) / 2, by = top + sag + 8;
    c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif';
    var bw = c.measureText(o.label).width + 20, bh = Math.max(20, hh * 0.32);
    c.strokeStyle = 'rgba(40,20,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(bx - bw / 2 + 6, by - 8); c.lineTo(bx - bw / 2 + 6, by); c.moveTo(bx + bw / 2 - 6, by - 8); c.lineTo(bx + bw / 2 - 6, by); c.stroke();
    paper(c, function (q) { jag(q, [[bx - bw / 2, by], [bx + bw / 2, by], [bx + bw / 2, by + bh], [bx, by + bh + 6], [bx - bw / 2, by + bh]], 51, 1); }, '#e5567f', 1.6);
    c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(o.label, bx, by + bh / 2 + 1);
    hits.push({ k: 'event', x0: bx - bw / 2, x1: bx + bw / 2, y0: by - 8, y1: by + bh + 8 });
  }
  /* the couples */
  var beat = t / 1000 * Math.PI * 2 / 1.8, n = Math.max(2, Math.min(COUPLES.length, Math.floor(span / (hh * 1.35))));
  for (i = 0; i < n; i++) {
    var cx = x0 + span * (i + 0.5) / n, cy = deck + 4 + (i % 2) * hh * 0.05, A = hh * 0.32, T = beat + i * 1.3, pair = COUPLES[i];
    var L = [cx + A * Math.sin(T / 2), cy - 2 + A * 0.18 * Math.sin(T / 2) * Math.cos(T / 2)];
    var F = [L[0] + hh * 0.42 * Math.cos(T * 1.5), L[1] - 1 + hh * 0.08 * Math.sin(T * 1.5)];
    var hand = [(L[0] + F[0]) / 2, Math.min(L[1], F[1]) - hh * 0.72];
    c.strokeStyle = 'rgba(255,255,255,.12)'; c.lineWidth = 1.5; c.beginPath();
    for (var m = 30; m > 0; m--) { var q0 = cx + A * Math.sin((T - m * 0.05) / 2); m === 30 ? c.moveTo(q0, cy) : c.lineTo(q0, cy + 1); } c.stroke();
    figure(c, L, hh, pair[0], hand, T, 0);
    figure(c, F, hh * (pair[1].skirt ? 0.94 : 0.98), pair[1], hand, T, 1.1);
  }
  hits.push({ k: 'event', x0: x0, x1: x1, y0: deck - hh * 1.2, y1: H });
  return hits;
}

/* the whole picture, for a still or a kind with no scene of its own */
function latinNightScene(c, W, H, t, moon, ridge) {
  var g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0d0820'); g.addColorStop(0.62, '#3a1240'); g.addColorStop(1, '#7a2a3a');
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  var r = rnd(7), i; for (i = 0; i < 60; i++) { c.fillStyle = 'rgba(255,255,255,' + (0.3 + 0.3 * Math.sin(t / 700 + i)) + ')'; c.fillRect(r() * W, r() * H * 0.5, 1.5, 1.5); }
  if (moon) {
    var mx = W * 0.86, my = H * 0.16, mr = Math.min(18, H * 0.07), side = moon.waxing ? 1 : -1, kk = 2 * moon.illum - 1;
    paper(c, function (q) { circ(q, mx, my, mr, 9); }, '#3a3f78', 1);
    paper(c, function (q) { q.beginPath(); q.arc(mx, my, mr, -Math.PI / 2, Math.PI / 2, side < 0); q.ellipse(mx, my, mr * Math.abs(kk), mr, 0, Math.PI / 2, -Math.PI / 2, side > 0 ? kk < 0 : kk >= 0); q.closePath(); }, '#fff2c8', 0.6);
  }
  var phone = W < 560;
  landscape(c, W, H, { horizon: H * 0.66, night: true, pm25: 12, ridge: ridge, phone: phone });
  latinNight(c, W, H, t, { deck: H * 0.84, phone: phone });
}

window.MDSKY = { paper: paper, jag: jag, circ: circ, grain: grain, sights: SIGHTS, draw: DRAW, landscape: landscape, latinNight: latinNight, latinNightScene: latinNightScene };
})();
