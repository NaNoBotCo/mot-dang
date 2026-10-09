/* The moat, painted (Nan, 2026-10-02: "a monet-ish impression of moat scenes at
   different gates/corners, different times of day … animated and magical"). The old
   city's moat at one of its five gates or four corners, in broken colour: short dabs,
   reflections pulled into level strokes, lilies on the water. The hour sets the palette,
   dawn to night; the sun's azimuth against the way the view looks sets the light, so a
   gate seen against the sunset stands backlit and Doi Suthep shows where it would.

   The still layer (sky, trees, wall, banks, the water's reflections) is painted once per
   quarter hour into its own canvas; each frame lays it down and adds what moves.

   MDDOODLER_MOAT.places               the nine: k, th, en, lat, lng, kind, look (the view's azimuth)
   MDDOODLER_MOAT.nearest(lat, lng)    → { p, m }: the nearest place and the metres to it */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, TAU = K.TAU, RAD = Math.PI / 180;
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

var PLACES = [
  { k: 'tha-phae-gate', th: 'ประตูท่าแพ', en: 'Tha Phae Gate', lat: 18.787762, lng: 98.99327, kind: 'gate', look: 270, ww: 0.66, plaza: 1, doors: 1, pigeons: 1, re: /tha ?phae|ท่าแพ/i },
  { k: 'chiang-mai-gate', th: 'ประตูเชียงใหม่', en: 'Chiang Mai Gate', lat: 18.781355, lng: 98.988981, kind: 'gate', look: 0, ww: 0.46, tiers: 1, stalls: 1, re: /chiang ?mai gate|ประตูเชียงใหม่/i },
  { k: 'saen-pung-gate', th: 'ประตูแสนปุง', en: 'Saen Pung Gate', lat: 18.781545, lng: 98.981597, kind: 'gate', look: 0, ww: 0.3, wh: 0.78, bigTree: 1, re: /saen ?pung|suan ?prung|แสนปุง|สวนปรุง/i },
  { k: 'suan-dok-gate', th: 'ประตูสวนดอก', en: 'Suan Dok Gate', lat: 18.788836, lng: 98.978192, kind: 'gate', look: 90, ww: 0.42, palms: 4, re: /suan ?dok gate|ประตูสวนดอก/i },
  { k: 'chang-phueak-gate', th: 'ประตูช้างเผือก', en: 'Chang Phueak Gate', lat: 18.795433, lng: 98.986594, kind: 'gate', look: 180, ww: 0.42, wh: 0.95, elephant: 1, re: /chang ?ph?(ue|eu)ak|ช้างเผือก/i },
  { k: 'chaeng-si-phum', th: 'แจ่งศรีภูมิ', en: 'Si Phum corner', lat: 18.795, lng: 98.993422, kind: 'corner', look: 225, rain: 2, re: /si ?phum|ศรีภูมิ/i },
  { k: 'chaeng-katam', th: 'แจ่งก๊ะต๊ำ', en: 'Katam corner', lat: 18.781424, lng: 98.99265, kind: 'corner', look: 315, palms: 3, fisher: 1, re: /ka ?tam|ก๊ะต๊ำ|กะต๊ำ/i },
  { k: 'chaeng-ku-hueang', th: 'แจ่งกู่เฮือง', en: 'Ku Hueang corner', lat: 18.781838, lng: 98.978119, kind: 'corner', look: 45, banyan: 1, re: /ku ?hueang|ku ?ruang|กู่เฮือง/i },
  { k: 'chaeng-hua-lin', th: 'แจ่งหัวลิน', en: 'Hua Lin corner', lat: 18.795365, lng: 98.979945, kind: 'corner', look: 135, palms: 4, rain: 1, re: /hua ?lin|หัวลิน/i }
];
var SUTHEP = [18.8049, 98.9216];   /* Doi Suthep's summit, for the views that face it */

/* metres between two points, equirectangular: dx = Δλ·cos φ, dy = Δφ, × R */
function metres(la1, lo1, la2, lo2) { var x = (lo2 - lo1) * Math.cos((la1 + la2) / 2 * RAD), y = la2 - la1; return Math.sqrt(x * x + y * y) * RAD * 6371000; }
function nearest(lat, lng) {
  var best = null, m = Infinity;
  PLACES.forEach(function (p) { var d = metres(lat, lng, p.lat, p.lng); if (d < m) { m = d; best = p; } });
  return { p: best, m: m };
}
/* the azimuth from a place to a point, degrees from north toward east */
function azTo(p, lat, lng) { return (Math.atan2((lng - p.lng) * Math.cos(p.lat * RAD), lat - p.lat) / RAD + 360) % 360; }
function rel(a, look) { return ((a - look + 540) % 360) - 180; }
function placeOf(S) {
  var v = (S.variant || '').toLowerCase(), i;
  if (v) for (i = 0; i < PLACES.length; i++) if (PLACES[i].k === v || PLACES[i].k.indexOf(v) >= 0) return PLACES[i];
  if (S.lat != null && S.lng != null) return nearest(S.lat, S.lng).p;
  for (i = 0; i < PLACES.length; i++) if (PLACES[i].re.test(S.title || '')) return PLACES[i];
  return PLACES[(S.seed >>> 3) % PLACES.length];
}

/* the sun over the old city: the almanac's low-precision formulas, mean anomaly g,
   ecliptic longitude λ, declination δ, hour angle from sidereal time */
function sunPos(ms) {
  var d = ms / 864e5 - 10957.5, g = (357.529 + 0.98560028 * d) * RAD, q = 280.459 + 0.98564736 * d;
  var lam = (q + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * RAD, eps = (23.439 - 3.6e-7 * d) * RAD;
  var dec = Math.asin(Math.sin(eps) * Math.sin(lam)), ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam));
  var gmst = (18.697374558 + 24.06570982441908 * d) % 24, ha = (gmst * 15 + 98.986) * RAD - ra, la = 18.788 * RAD;
  var alt = Math.asin(Math.sin(la) * Math.sin(dec) + Math.cos(la) * Math.cos(dec) * Math.cos(ha));
  var az = Math.atan2(-Math.cos(dec) * Math.sin(ha), Math.sin(dec) * Math.cos(la) - Math.cos(dec) * Math.cos(ha) * Math.sin(la));
  return { alt: alt / RAD, az: (az / RAD + 360) % 360 };
}

/* ---------------------------------------------------------------- the palette by the hour
   Keyframes on the sun's altitude, one set for the morning and one for the evening,
   blended linearly: night blues, dawn pinks and violets, morning, the white noon,
   golden oranges with violet shade, dusk. */
var NAMES = ['sky0', 'sky1', 'glow', 'cloud', 'brick', 'brickS', 'stone', 'leaf', 'leafS', 'water', 'waterL', 'shade', 'mist'];
var NIGHT = '#0e1638 #26306a #4a4c94 #3a3f78 #7a4a44 #3a2a3e #3c3c60 #22404a #102030 #0f2046 #4a5a9a #181440 #46507e';
var NOON = '#96c3e6 #ebf0f0 #fffff0 #ffffff #e17850 #965a64 #f0e6d2 #78b450 #326e5a #46aaa0 #fffff0 #6e78aa #f0f0f0';
var AMF = [[-18, NIGHT],
  [-6, '#4a4890 #d898b4 #fbbcc6 #c896be #a8647a #5a4678 #9682aa #546e7a #323c64 #5a5a96 #e6aac8 #50468c #c8b4dc'],
  [0, '#788cc8 #f8bcaa #ff965a #ffc8be #d2786a #785082 #d2b4b4 #78966e #3c5078 #7882aa #ffbe96 #6e5aa0 #e6c8dc'],
  [8, '#8cb4dc #f5e1be #ffdc96 #fff0dc #d77850 #82506e #e1c8aa #82aa5a #325a64 #508c8c #f0e6b4 #6464a0 #e6dce6'],
  [25, '#78aad7 #d7e6eb #fffadc #fafaf5 #c86446 #78465a #d7c8b4 #64a050 #285a5a #3c8c82 #dcf0e6 #5a64a0 #e6ebf0'],
  [55, NOON]];
var PMF = [[-18, NIGHT],
  [-6, '#323278 #e68278 #ff8c5a #b46e96 #8c505a #3c3264 #6e5a82 #324650 #182240 #283264 #dc8c6e #322864 #8c78a0'],
  [0, '#6464aa #ff965a #ff783c #fa8c78 #c85a3c #643c6e #c88c8c #5a6450 #28325a #505082 #ffa05a #503c8c #c8a0b4'],
  [8, '#8296c8 #ffc882 #ffaa46 #ffd296 #eb7832 #784678 #f0be82 #96a03c #3c466e #466482 #ffbe64 #6450a0 #f0c8b4'],
  [25, '#78a5d2 #e6e4d2 #fff5d2 #fff8ec #d26941 #7d4658 #e1cdb4 #6ea046 #2d5550 #3c827d #faf0c8 #5a5aa0 #ebe6e1'],
  [55, NOON]];
function hex(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; }
[AMF, PMF].forEach(function (F) { F.forEach(function (f) { if (typeof f[1] === 'string') f[1] = f[1].split(' ').map(hex); }); });
function mixc(a, b, u) { return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]; }
function css(c) { return 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')'; }
/* broken colour: a shift in value and a smaller one in hue, per dab */
function jc(c, r, j) { var l = (r() - 0.5) * j; return 'rgb(' + clamp(c[0] + l + (r() - 0.5) * j * 0.6, 0, 255) + ',' + clamp(c[1] + l + (r() - 0.5) * j * 0.6, 0, 255) + ',' + clamp(c[2] + l + (r() - 0.5) * j * 0.6, 0, 255) + ')'; }
function pal(alt, am) {
  var F = am ? AMF : PMF, a = clamp(alt, -18, 55), i = 0, o = {};
  while (i < F.length - 2 && a > F[i + 1][0]) i++;
  var u = clamp((a - F[i][0]) / (F[i + 1][0] - F[i][0]), 0, 1);
  NAMES.forEach(function (k, j) { o[k] = mixc(F[i][1][j], F[i + 1][1][j], u); });
  return o;
}
var FLOOD = hex('#f0b45a'), FLOODS = hex('#9a5a44'), GOLD = hex('#ffd27a');

/* the light: the sun's azimuth against the view's (rel 0 = the sun ahead, the scene
   backlit), how high it stands, the lamps by dusk */
function light(S, p, alt) {
  var sp = sunPos(S.now), o = { alt: alt, az: sp.az, rel: rel(sp.az, p.look) };
  o.up = clamp((alt + 1) / 8, 0, 1);
  o.sx = Math.sin(o.rel * RAD);
  o.lamps = clamp((0.5 - alt) / 5, 0, 1);
  o.am = sp.az < 180;
  o.amb = 0.3 + 0.35 * clamp(alt / 45, 0, 1);
  return o;
}
/* a face's brightness by Lambert's law, cos θ between the sun and the face's normal azimuth n */
function lit(Lt, n) { return Lt.amb + (1 - Lt.amb) * Lt.up * Math.max(0, Math.cos((Lt.az - n) * RAD)) * (1 - 0.5 * clamp(Lt.alt / 70, 0, 1)); }

/* ---------------------------------------------------------------- the brush */
/* one dab: a short stroke, bent a little off its chord */
function dab(q, x, y, len, w, ang, col, a, bend) {
  var dx = Math.cos(ang) * len / 2, dy = Math.sin(ang) * len / 2, b = bend || 0;
  q.globalAlpha = a; q.strokeStyle = col; q.lineWidth = w;
  q.beginPath(); q.moveTo(x - dx, y - dy);
  if (b) q.quadraticCurveTo(x - dy * b, y + dx * b, x + dx, y + dy); else q.lineTo(x + dx, y + dy);
  q.stroke();
}
/* dabs over a region, in two coats: broad thin strokes laid under, then the smaller ones
   scattered at random (one per st₀·st₀ of area); ang may be a field, ang(x, y) */
function fill(q, r, xa, xb, ya, yb, st, len, w, ang, fn, a) {
  var n = Math.round((xb - xa) * (yb - ya) / (st[0] * st[1])), i, px, py, col, an;
  for (i = 0; i < n * 0.22; i++) {
    px = xa + r() * (xb - xa); py = ya + r() * (yb - ya); col = fn(px, py); an = typeof ang === 'function' ? ang(px, py) : ang;
    if (col) dab(q, px, py, len * (1.6 + r()), w * (2 + r() * 0.8), an + (r() - 0.5) * 0.3, col, a * 0.4, (r() - 0.5) * 0.3);
  }
  for (i = 0; i < n; i++) {
    px = xa + r() * (xb - xa); py = ya + r() * (yb - ya); col = fn(px, py); an = typeof ang === 'function' ? ang(px, py) : ang;
    if (col) dab(q, px, py, len * (0.55 + r() * 0.9), w * (0.65 + r() * 0.6), an + (r() - 0.5) * 0.6, col, a, (r() - 0.5) * 0.5);
  }
}
var SPRITES = {};
/* a soft glow, a radial fade drawn once per colour */
function glow(col) {
  if (SPRITES[col]) return SPRITES[col];
  var g = document.createElement('canvas'); g.width = g.height = 64;
  var x = g.getContext('2d'), rg = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  rg.addColorStop(0, col); rg.addColorStop(0.35, col.replace('1)', '.35)')); rg.addColorStop(1, col.replace('1)', '0)'));
  x.fillStyle = rg; x.fillRect(0, 0, 64, 64);
  return (SPRITES[col] = g);
}

/* ---------------------------------------------------------------- the view's frame
   The far bank's waterline yw; at a corner it falls toward the bastion from both arms,
   yw(x) = yw₀ − k·|x − cx|, and things along the arms shrink with distance. */
function layout(S, p) {
  var H = S.H, ph = !!S.phone, L = { x0: S.x0, x1: S.x1, span: S.span, H: H, ph: ph, deck: S.deck, hh: S.hh };
  L.yw0 = H * (ph ? 0.57 : 0.6);
  L.cx = S.x0 + S.span * (ph ? 0.42 : 0.45);
  L.corner = p.kind === 'corner';
  L.rise = L.corner ? H * 0.06 / (S.span * 0.55) : 0;
  L.wallH = H * 0.18 * (p.wh || 1);
  L.yb = L.yw0 - H * (p.plaza ? 0.07 : 0.036);
  L.yt = L.yb - L.wallH;
  L.ww = Math.min(S.span * (p.ww || 0.4), H * 1.7);
  return L;
}
function ywAt(L, x) { return L.yw0 - L.rise * Math.abs(x - L.cx); }
function scAt(L, x) { return L.corner ? Math.max(0.42, 1 - 0.55 * Math.abs(x - L.cx) / (L.span * 0.55)) : 1; }

/* ---------------------------------------------------------------- the still layer */
/* the sky: a gradient under crossed dabs, warm near the sun, clouds lit from below at the ends of the day */
function sky(q, r, L, P, Lt, E) {
  var g = q.createLinearGradient(0, 0, 0, L.yw0);
  g.addColorStop(0, css(P.sky0)); g.addColorStop(1, css(P.sky1));
  q.globalAlpha = 1; q.fillStyle = g; q.fillRect(L.x0 - 2, 0, L.span + 4, L.yw0 + 4);
  var sun = E.sun, swirl = function (x, y) { return -0.35 + 0.45 * Math.sin(x * 0.009 + y * 0.021) + 0.25 * Math.sin(y * 0.05); };
  fill(q, r, L.x0 - 6, L.x1 + 6, 0, L.yw0 + 2, [11, 5.5], 13, 4.2, swirl, function (x, y) {
    var c = mixc(P.sky0, P.sky1, Math.pow(clamp(y / L.yw0, 0, 1), 1.25));
    if (sun) { var d = Math.sqrt((x - sun.x) * (x - sun.x) + (y - sun.y) * (y - sun.y) * 2) / (L.H * 0.5); c = mixc(c, P.glow, 0.75 * Math.pow(clamp(1 - d, 0, 1), 2)); }
    var u = r(); if (u < 0.1) c = mixc(c, P.glow, 0.45); else if (u < 0.17) c = mixc(c, P.cloud, 0.5); else if (u < 0.22) c = mixc(c, P.shade, 0.3);
    return jc(c, r, 20);
  }, 0.72);
  /* clouds: lobes of pale dabs, the undersides in the shade colour */
  var n = L.ph ? 2 : 3 + Math.floor(r() * 2);
  for (var i = 0; i < n; i++) {
    var cx = L.x0 + L.span * (0.08 + 0.84 * r()), cy = L.H * (0.1 + 0.18 * r()), cw = L.H * (0.12 + 0.16 * r());
    for (var j = 0; j < 5; j++) {
      var lx = cx + (j - 2) * cw * 0.22 + (r() - 0.5) * cw * 0.1, ly = cy - Math.sin((j + 0.5) / 5 * Math.PI) * cw * 0.14, lr = cw * (0.12 + 0.08 * r());
      for (var k = 0; k < 16; k++) {
        var a = r() * TAU, d = Math.sqrt(r()), px = lx + Math.cos(a) * d * lr * 1.4, py = ly + Math.sin(a) * d * lr * 0.7, under = clamp((py - (cy - cw * 0.05)) / (cw * 0.12), 0, 1);
        var c = mixc(mixc(P.cloud, P.glow, 0.3 * (1 - Lt.up * 0.6)), P.shade, 0.15 + 0.45 * under);
        dab(q, px, py, 7 + r() * 7, 3 + r() * 2.4, (r() - 0.5) * 0.7, jc(c, r, 18), 0.6 * (1 - 0.55 * Lt.lamps), 0.2);
      }
    }
  }
  /* stars, by night */
  if (Lt.lamps > 0.6) for (i = 0; i < 26; i++) { q.globalAlpha = 0.4 + 0.5 * r(); q.fillStyle = '#fff4d8'; q.beginPath(); q.arc(L.x0 + r() * L.span, r() * L.yw0 * 0.55, 0.6 + r() * 0.9, 0, TAU); q.fill(); }
  /* the sun's disc, as in Impression, Sunrise: one flat orange coin in the haze */
  if (sun) {
    q.globalAlpha = 0.55; var gz = sun.r * 7; q.drawImage(glow('rgba(' + (P.glow[0] | 0) + ',' + (P.glow[1] | 0) + ',' + (P.glow[2] | 0) + ',1)'), sun.x - gz / 2, sun.y - gz / 2, gz, gz);
    for (k = 0; k < 30; k++) { var a2 = r() * TAU, d2 = sun.r * (1.1 + r() * 1.8); dab(q, sun.x + Math.cos(a2) * d2, sun.y + Math.sin(a2) * d2 * 0.7, 7 + r() * 7, 3.2, (r() - 0.5) * 0.5, jc(mixc(P.glow, P.sky1, 0.3), r, 16), 0.4); }
    q.globalAlpha = 1; q.fillStyle = css(mixc(P.glow, [255, 120, 50], 0.35 * (1 - Lt.up))); q.beginPath(); q.arc(sun.x, sun.y, sun.r, 0, TAU); q.fill();
    for (k = 0; k < 10; k++) dab(q, sun.x + (r() - 0.5) * sun.r, sun.y + (r() - 0.5) * sun.r, sun.r * 0.6, 2.5, (r() - 0.5) * 0.5, jc(mixc(P.glow, [255, 255, 220], 0.4), r, 14), 0.7);
  }
}
/* Doi Suthep, far and blue: a ridge y = y₀ − h·e^(−(x−m)²/s²) under the haze, the wat's gold on its flank */
function mountain(q, r, L, P, Lt, m) {
  var top = function (x) { return L.yw0 - L.H * (0.2 + 0.17 * Math.exp(-Math.pow((x - m) / (L.span * 0.24), 2)) + 0.012 * Math.sin(x * 0.03) + 0.008 * Math.sin(x * 0.083)); };
  var front = Math.max(0, -Math.cos(Lt.rel * RAD)) * Lt.up * clamp(1 - Lt.alt / 30, 0, 1);
  var col = mixc(mixc(mixc(P.shade, P.sky0, 0.35), P.sky1, 0.22), P.glow, 0.35 * front), xa = Math.max(L.x0 - 4, m - L.span * 0.7), xb = Math.min(L.x1 + 4, m + L.span * 0.7);
  q.globalAlpha = 0.85; q.fillStyle = css(col); q.beginPath(); q.moveTo(xa, L.yw0);
  for (var x = xa; x <= xb; x += 6) q.lineTo(x, top(x) + 2); q.lineTo(xb, L.yw0); q.closePath(); q.fill();
  for (x = xa; x < xb; x += 7) for (var y = top(x) + 2; y < L.yw0; y += 5) {
    var f = (y - top(x)) / (L.H * 0.25), c = mixc(col, P.sky1, clamp(f, 0, 1) * 0.35);   /* haze thickens toward its foot */
    c = r() < 0.15 ? mixc(c, P.glow, 0.35 * Lt.up) : r() < 0.15 ? mixc(c, P.shade, 0.3) : c;
    dab(q, x + (r() - 0.5) * 5, y, 8 + r() * 6, 3.2, (r() - 0.5) * 0.6, jc(c, r, 14), 0.6);
  }
  var wx = m + L.span * 0.035, wy = top(wx) + L.H * 0.012;
  if (wx > L.x0 && wx < L.x1) { q.globalAlpha = 0.9; q.fillStyle = Lt.lamps > 0.5 ? '#ffd27a' : css(mixc(GOLD, P.glow, 0.3)); q.beginPath(); q.arc(wx, wy, 1.6, 0, TAU); q.fill(); if (Lt.lamps > 0.5) { q.globalAlpha = 0.5; q.drawImage(glow('rgba(255,210,122,1)'), wx - 8, wy - 8, 16, 16); } }
}
/* a tree's crown: a dome of dabs, lit toward the sun and on top, violet in its shade;
   haze h pulls it toward the sky; some edge dabs are kept to sway in the breeze */
function crown(q, r, L, P, Lt, E, cx, cy, rx, ry, h, n) {
  for (var i = 0; i < n; i++) {
    var a = r() * TAU, d = Math.sqrt(r()), x = cx + Math.cos(a) * d * rx, y = cy + Math.sin(a) * d * ry * (Math.sin(a) > 0 ? 0.7 : 1);
    var s = clamp(0.45 - Math.sin(a) * d * 0.4 + Lt.sx * Math.cos(a) * d * 0.45 * Lt.up + (Lt.up - 0.5) * 0.2, 0, 1);
    var c = mixc(P.leafS, P.leaf, s), u = r();
    if (u < 0.1) c = mixc(c, s > 0.5 ? P.glow : P.shade, 0.5); else if (u < 0.14) c = mixc(c, P.sky1, 0.5);
    if (h) c = mixc(c, mixc(P.sky1, P.shade, 0.35), h);
    if (Lt.lamps > 0.3 && E.floodY && y > E.floodY - L.H * 0.1) c = mixc(c, FLOOD, 0.25 * Lt.lamps * clamp((y - E.floodY + L.H * 0.1) / (L.H * 0.1), 0, 1));
    var len = (5 + r() * 6) * (rx > 30 ? 1 : 0.8), col = jc(c, r, 22), ang = (r() - 0.5) * 1.6;
    dab(q, x, y, len, 3 + r() * 2.2, ang, col, 0.85, 0.3);
    if (E.keep && d > 0.8 && E.leaf.length < (L.ph ? 18 : 34) && r() < 0.18) E.leaf.push({ x: x, y: y, len: len, w: 3, ang: ang, col: col, k: r() * TAU });
  }
}
/* a trunk and its limbs, dark strokes with a lit edge toward the sun */
function trunk(q, r, L, P, Lt, x, y0, y1, w) {
  var c = mixc(P.leafS, P.brickS, 0.5);
  dab(q, x, (y0 + y1) / 2, y0 - y1, w, Math.PI / 2 + (r() - 0.5) * 0.08, css(c), 0.95);
  dab(q, x + Lt.sx * w * 0.3, (y0 + y1) / 2, (y0 - y1) * 0.9, w * 0.35, Math.PI / 2, css(mixc(c, P.glow, 0.35 * Lt.up)), 0.7);
  for (var k = 0; k < 3; k++) { var bx = x + (k - 1) * w * 2.2, by = y1 + (y0 - y1) * 0.15; q.globalAlpha = 0.85; q.strokeStyle = css(c); q.lineWidth = w * 0.4; q.beginPath(); q.moveTo(x, y1 + (y0 - y1) * 0.35); q.quadraticCurveTo(x + (bx - x) * 0.3, by, bx, y1); q.stroke(); }
}
/* a rain tree: a broad umbrella crown on a short trunk */
function rainTree(q, r, L, P, Lt, E, x, base, s, haze) {
  var rx = L.H * 0.2 * s, ry = L.H * 0.09 * s;
  trunk(q, r, L, P, Lt, x, base, base - L.H * 0.16 * s, Math.max(2, L.H * 0.018 * s));
  crown(q, r, L, P, Lt, E, x, base - L.H * 0.2 * s, rx, ry, haze || 0, Math.round(rx * ry * 0.09));
}
/* a banyan: a heavy crown, its aerial roots hanging as thin straight strokes */
function banyan(q, r, L, P, Lt, E, x, base, s) {
  var rx = L.H * 0.19 * s, ry = L.H * 0.12 * s, cy = base - L.H * 0.21 * s, c = mixc(P.leafS, P.brickS, 0.45);
  trunk(q, r, L, P, Lt, x, base, cy, L.H * 0.03 * s);
  for (var i = 0; i < 22; i++) { var rx2 = x + (r() - 0.5) * rx * 1.6, ry0 = cy + ry * 0.3, ry1 = base - r() * L.H * 0.05 * s; dab(q, rx2, (ry0 + ry1) / 2, ry1 - ry0, 1 + r() * 1.2, Math.PI / 2 + (r() - 0.5) * 0.05, jc(c, r, 20), 0.75); }
  crown(q, r, L, P, Lt, E, x, cy, rx, ry, 0, Math.round(rx * ry * 0.1));
}
/* a palm: a slim curved trunk, fronds drooping as arcs of dabs, y = y₀ − a·u + b·u² */
function palm(q, r, L, P, Lt, E, x, base, s) {
  var h = L.H * 0.27 * s, lean = (r() - 0.5) * h * 0.25, c = mixc(P.leafS, P.stone, 0.35), tx = x + lean, ty = base - h;
  q.globalAlpha = 0.9; q.strokeStyle = css(c); q.lineWidth = Math.max(1.5, L.H * 0.008 * s);
  q.beginPath(); q.moveTo(x, base); q.quadraticCurveTo(x + lean * 0.2, base - h * 0.5, tx, ty); q.stroke();
  for (var f = 0; f < 9; f++) {
    var a = f / 9 * TAU + r() * 0.4, dx = Math.cos(a), len = h * (0.28 + r() * 0.12);
    for (var k = 1; k <= 6; k++) {
      var u = k / 6, px = tx + dx * len * u, py = ty - Math.abs(Math.sin(a)) * len * 0.25 * u + len * 0.55 * u * u;
      var col = mixc(P.leafS, P.leaf, clamp(0.4 + dx * Lt.sx * 0.5 * Lt.up + 0.2 * (1 - u), 0, 1));
      dab(q, px, py, 5 + r() * 3, 2.2 * s + 0.8, Math.atan2(len * 1.1 * u, dx * len) * (dx < 0 ? -1 : 1) * 0.5 + (dx < 0 ? 0.6 : -0.6), jc(col, r, 18), 0.85);
      if (k === 6 && E.leaf.length < (L.ph ? 18 : 34) && r() < 0.4) E.leaf.push({ x: px, y: py, len: 6, w: 2.4, ang: dx < 0 ? 0.6 : -0.6, col: jc(col, r, 10), k: r() * TAU });
    }
  }
}
/* merlons along a line: points for a crenellated top, teeth of width m·0.55 and height m·0.7 */
function crenel(pts, xa, xb, ya, yb, m) {
  var n = Math.max(1, Math.round((xb - xa) / m)), st = (xb - xa) / n;
  for (var i = 0; i < n; i++) {
    var x = xa + i * st, y = ya + (yb - ya) * (i / n), h = m * 0.7;
    pts.push([x, y], [x + st * 0.22, y], [x + st * 0.22, y - h], [x + st * 0.78, y - h], [x + st * 0.78, y]);
  }
  pts.push([xb, yb]);
}
/* brick under dabs: the face's light by Lambert, level dabs as courses, floodlit from below by night */
function brick(q, r, L, P, Lt, path, bx, by, bw, bh, n, dim) {
  var b = lit(Lt, n) * (1 - (dim || 0)), c0 = mixc(P.brickS, P.brick, b);
  q.save(); q.globalAlpha = 1; q.fillStyle = css(mixc(c0, P.brickS, 0.3)); q.fill(path); q.clip(path);
  fill(q, r, bx - 4, bx + bw + 4, by - 4, by + bh + 2, [7, 3.2], 8, 3.4, 0, function (x, y) {
    var c = c0, f = clamp((y - by) / bh, 0, 1), patch = Math.sin(x * 0.043 + Math.sin(y * 0.07) * 2) * Math.sin(y * 0.031 + x * 0.011);
    c = patch > 0 ? mixc(c, P.brickS, 0.3 * patch) : mixc(c, P.stone, -0.18 * patch);   /* weathered patches, darker and paler */
    if (f > 0.75 && r() < 0.3) c = mixc(c, P.leafS, 0.3);   /* moss at the foot */
    if (Lt.lamps > 0.05) c = mixc(c, FLOOD, Lt.lamps * (0.35 + 0.5 * f));
    c = mixc(c, P.brickS, 0.12 * (1 - f));
    var u = r(); if (u < 0.12) c = mixc(c, Lt.lamps > 0.3 ? mixc(P.brickS, P.shade, 0.3) : P.shade, 0.45 * (1 - 0.5 * Lt.lamps)); else if (u < 0.2) c = mixc(c, P.glow, 0.4 * Lt.up); else if (u < 0.24) c = mixc(c, P.stone, 0.4);
    return jc(c, r, 26);
  }, 0.9);
  q.restore();
  /* the outline broken by dabs across it, so the edge is painted, not cut */
  q.save(); q.setLineDash([2 + r() * 3, 3 + r() * 4]); q.lineDashOffset = r() * 10;
  q.globalAlpha = 0.55; q.strokeStyle = css(mixc(c0, Lt.lamps > 0.3 ? FLOOD : P.sky1, 0.25)); q.lineWidth = 2.6; q.stroke(path);
  q.setLineDash([1.5, 6]); q.globalAlpha = 0.5; q.strokeStyle = css(mixc(c0, P.shade, 0.35)); q.lineWidth = 3.2; q.stroke(path);
  q.restore();
  return c0;
}
/* a gate: the wall, raised over the gateway, ruined at its ends, crenellated, the opening dark with the street's light through it */
function gate(q, r, L, P, Lt, p, E) {
  var wx0 = L.cx - L.ww / 2, wx1 = L.cx + L.ww / 2, m = L.H * 0.032, e = L.ww * 0.05, up = L.H * (p.tiers ? 0.05 : p.doors ? 0.04 : 0.025), cw = L.ww * (p.tiers ? 0.44 : 0.3);
  var pts = [[wx0, L.yb], [wx0, L.yb - L.wallH * 0.5], [wx0 + e * 0.5, L.yb - L.wallH * 0.62], [wx0 + e, L.yb - L.wallH * 0.62]];
  crenel(pts, wx0 + e, L.cx - cw / 2, L.yt, L.yt, m);
  pts.push([L.cx - cw / 2, L.yt - up]);
  crenel(pts, L.cx - cw / 2, L.cx + cw / 2, L.yt - up, L.yt - up, m);
  pts.push([L.cx + cw / 2, L.yt]);
  crenel(pts, L.cx + cw / 2, wx1 - e, L.yt, L.yt, m);
  pts.push([wx1 - e * 0.5, L.yb - L.wallH * 0.55], [wx1, L.yb - L.wallH * 0.45], [wx1, L.yb]);
  var path = new Path2D(); pts.forEach(function (pt, i) { i ? path.lineTo(pt[0], pt[1]) : path.moveTo(pt[0], pt[1]); }); path.closePath();
  brick(q, r, L, P, Lt, path, wx0, L.yt - up - m, L.ww, L.yb - L.yt + up + m, p.look + 180);
  /* the string course under the parapet */
  for (var x = wx0 + e; x < wx1 - e; x += 6) { var top = Math.abs(x - L.cx) < cw / 2 ? L.yt - up : L.yt; dab(q, x, top + 3.5, 7, 1.6, 0, jc(mixc(P.brickS, P.shade, 0.3), r, 16), 0.6); }
  /* the opening */
  var aw = L.H * (p.doors ? 0.085 : 0.065), ah = L.wallH * (p.doors ? 0.74 : 0.7), ay = L.yb, ax = L.cx;
  var arch = new Path2D();
  if (p.doors) { arch.rect(ax - aw / 2, ay - ah, aw, ah); }
  else { arch.moveTo(ax - aw / 2, ay); arch.lineTo(ax - aw / 2, ay - ah + aw / 2); arch.arc(ax, ay - ah + aw / 2, aw / 2, Math.PI, 0); arch.lineTo(ax + aw / 2, ay); arch.closePath(); }
  var dark = mixc(P.brickS, [20, 14, 34], 0.55), beyond = Lt.lamps > 0.4 ? mixc(GOLD, FLOOD, 0.3) : mixc(P.stone, P.glow, 0.3);
  q.save(); q.globalAlpha = 1; q.fillStyle = css(dark); q.fill(arch); q.clip(arch);
  fill(q, r, ax - aw / 2 - 2, ax + aw / 2 + 2, ay - ah - 2, ay + 1, [5, 3], 6, 3, 0, function (x, y) {
    var f = (y - (ay - ah)) / ah; return jc(mixc(dark, beyond, clamp((f - 0.35) * 1.4, 0, 1) * 0.85), r, 18);
  }, 0.9);
  q.restore();
  if (p.doors) [-1, 1].forEach(function (sd) {
    var dx = ax + sd * aw * 0.5, wood = mixc([74, 42, 24], P.glow, 0.25 * Lt.up);
    for (var y = ay - ah + 2; y < ay; y += 3) dab(q, dx - sd * aw * 0.08, y, 3, aw * 0.16, 0, jc(wood, r, 18), 0.9);
  });
  /* the arch's lit rim, on the sun's side */
  var rimc = jc(mixc(P.brick, P.glow, 0.4), r, 10);
  dab(q, ax - Lt.sx * aw * 0.5, ay - ah * 0.45, ah * 0.75, 1.8, Math.PI / 2, rimc, 0.5 * Lt.up + 0.2 * Lt.lamps);
  E.wall = [wx0, wx1, L.yt - up]; E.floodY = L.yb;
  E.gx = ax;
}
/* a corner bastion, seen corner-on: two battered, stepped faces, each lit by its own cos θ;
   the city wall leaves it along both arms of the moat, shrinking with distance */
function bastion(q, r, L, P, Lt, p, E) {
  var Bw = Math.min(L.span * 0.34, L.H * 0.86), Bh = L.H * 0.25, y0 = L.yw0 - L.H * 0.024, k = L.rise, m = L.H * 0.03;
  /* the arms' walls first, behind */
  [-1, 1].forEach(function (sd) {
    var xa = L.cx + sd * Bw * 0.42, xb = sd < 0 ? L.x0 - 20 : L.x1 + 20, pts = [], n = sd < 0 ? p.look + 225 : p.look + 135;
    var base = function (x) { return ywAt(L, x) - L.H * 0.022 * scAt(L, x); }, top = function (x) { return base(x) - L.wallH * 0.62 * scAt(L, x); };
    pts.push([xa, base(xa)]);
    var st = m, x = xa;
    while (sd < 0 ? x > xb : x < xb) { var s = scAt(L, x), w = st * s, y = top(x), h = m * 0.7 * s; pts.push([x, y], [x + sd * w * 0.22, y], [x + sd * w * 0.22, y - h], [x + sd * w * 0.78, y - h], [x + sd * w * 0.78, y]); x += sd * w; }
    pts.push([xb, top(xb)], [xb, base(xb)]);
    var path = new Path2D(); pts.forEach(function (pt, i) { i ? path.lineTo(pt[0], pt[1]) : path.moveTo(pt[0], pt[1]); }); path.closePath();
    brick(q, r, L, P, Lt, path, Math.min(xa, xb), top(xa) - m, Math.abs(xb - xa), L.wallH, n);
  });
  /* the bastion's tiers, the far face first */
  var tiers = [[0, 0.5, 1, 0.9], [0.5, 0.72, 0.8, 0.75], [0.72, 0.88, 0.64, 0.6]];
  var faces = Lt.sx > 0 ? [-1, 1] : [1, -1], dimOf = function (sd) { return lit(Lt, p.look + (sd < 0 ? 225 : 135)) < lit(Lt, p.look + (sd < 0 ? 135 : 225)) ? 0.22 : 0; };
  tiers.forEach(function (t) {
    var yB = y0 - t[0] * Bh, yT = y0 - t[1] * Bh, h0 = Bw / 2 * t[2], h1 = Bw / 2 * t[3];
    faces.forEach(function (sd) {
      var path = new Path2D(); path.moveTo(L.cx, yB); path.lineTo(L.cx + sd * h0, yB - k * h0); path.lineTo(L.cx + sd * h1, yT - k * h1); path.lineTo(L.cx, yT); path.closePath();
      brick(q, r, L, P, Lt, path, L.cx - h0, yT - k * h1 - 2, h0 * 2, yB - yT + 4, sd < 0 ? p.look + 225 : p.look + 135, dimOf(sd));
    });
    /* the lit edge along the tier's top */
    for (var x = -h1; x < h1; x += 5) dab(q, L.cx + x, yT - k * Math.abs(x) + 1, 6, 1.6, -k * Math.sign(x), jc(mixc(P.brick, P.glow, 0.5), r, 12), 0.45 * Lt.up + 0.3 * Lt.lamps);
  });
  /* merlons on the top tier, both faces */
  var yT2 = y0 - 0.88 * Bh, hT = Bw / 2 * 0.6;
  [-1, 1].forEach(function (sd) {
    var path = new Path2D(), pts = []; crenel(pts, 0, hT, 0, 0, m * 0.95);
    path.moveTo(L.cx, yT2 + 1);
    pts.forEach(function (pt) { path.lineTo(L.cx + sd * pt[0], yT2 - k * pt[0] + pt[1]); });
    path.lineTo(L.cx + sd * hT, yT2 - k * hT + 1); path.closePath();
    brick(q, r, L, P, Lt, path, L.cx - hT, yT2 - k * hT - m, hT * 2, m * 1.2, sd < 0 ? p.look + 225 : p.look + 135, dimOf(sd));
  });
  /* shrubs that have taken the bastion's top */
  for (var j = 0; j < 3; j++) { var sx = L.cx + (j - 1) * hT * 0.7 + (r() - 0.5) * hT * 0.3; crown(q, r, L, P, Lt, E, sx, yT2 - m * 1.2 - k * Math.abs(sx - L.cx), L.H * 0.035, L.H * 0.02, 0, 22); }
  /* the arris: the corner nearest us */
  dab(q, L.cx, y0 - Bh * 0.42, Bh * 0.8, 1.4, Math.PI / 2, css(mixc(P.brickS, P.shade, 0.3)), 0.5);
  E.wall = [L.cx - Bw / 2, L.cx + Bw / 2, yT2 - m]; E.floodY = y0; E.gx = L.cx; E.Bw = Bw;
}
/* the far bank between the wall and the water: plaza, grass and road as level dabs, the stepped bank edge, shade under the wall */
function farBank(q, r, L, P, Lt, p) {
  var road = mixc(P.stone, P.shade, 0.3), grass = mixc(P.leaf, P.leafS, 0.3);
  var shadow = Lt.up * Math.max(0, Math.cos(Lt.rel * RAD)) * clamp(1.2 - Lt.alt / 40, 0, 1);
  q.globalAlpha = 1; q.fillStyle = css(mixc(road, grass, 0.4)); q.beginPath(); q.moveTo(L.x0 - 4, L.yb - 2);
  for (var x = L.x0 - 4; x <= L.x1 + 8; x += 8) q.lineTo(x, Math.min(L.yb - 2, ywAt(L, x) - L.H * 0.03 * scAt(L, x))); q.lineTo(L.x1 + 8, L.yw0 + 2); q.lineTo(L.x0 - 4, L.yw0 + 2); q.closePath(); q.fill();
  fill(q, r, L.x0 - 4, L.x1 + 4, L.yw0 - L.rise * L.span - L.H * 0.08, L.yw0, [8, 2.6], 9, 2.6, 0, function (x, y) {
    var w = ywAt(L, x), s = scAt(L, x), f = (w - y) / (L.H * (p.plaza ? 0.075 : 0.036) * s);
    if (f < 0 || f > 1.05 || y < (L.corner ? w - L.H * 0.035 * s : L.yb - 1)) return null;
    var c = p.plaza ? mixc(P.stone, P.brick, 0.15) : f > 0.55 ? grass : road;
    if (f < 0.18) c = mixc(P.brick, P.stone, 0.4);   /* the bank's brick lip */
    if (shadow > 0 && f > 0.5) c = mixc(c, P.shade, shadow * 0.5 * clamp((f - 0.5) * 2, 0, 1));
    if (Lt.lamps > 0) c = mixc(c, P.shade, Lt.lamps * 0.25);
    var u = r(); if (u < 0.1) c = mixc(c, P.glow, 0.4 * Lt.up); else if (u < 0.18) c = mixc(c, P.shade, 0.35);
    return jc(c, r, 22);
  }, 0.9);
}
/* a lamp post on the bank: a dark stroke, a lamp that glows by night */
function lampPost(q, r, L, P, Lt, E, x, s) {
  var base = ywAt(L, x) - L.H * 0.012 * s, h = L.H * 0.075 * s, c = css(mixc(mixc(P.leafS, P.shade, 0.5), P.sky1, 0.15));
  dab(q, x, base - h / 2, h, Math.max(1, 1.5 * s), Math.PI / 2, c, 0.6);
  q.globalAlpha = 0.85; q.fillStyle = Lt.lamps > 0.3 ? '#fff2c4' : css(mixc(P.stone, P.sky1, 0.5)); q.beginPath(); q.arc(x, base - h, 2.2 * s, 0, TAU); q.fill();
  if (Lt.lamps > 0.1) { q.globalAlpha = Lt.lamps; var z = 22 * s; q.drawImage(glow('rgba(255,214,130,1)'), x - z / 2, base - h - z / 2, z, z); }
  E.lamps.push({ x: x, y: base - h, w: ywAt(L, x), s: s });
}
/* market umbrellas before the wall, Chiang Mai Gate's evening stalls: domes of colour, bulbs by dusk */
function stalls(q, r, L, P, Lt, E) {
  var cols = [[226, 92, 60], [245, 190, 70], [60, 140, 150], [240, 236, 220], [200, 80, 110]], n = L.ph ? 3 : 5, x0 = L.cx - L.ww * 0.55;
  for (var i = 0; i < n; i++) {
    var x = x0 - i * L.H * 0.07, y = L.yb + L.H * 0.012, w = L.H * 0.034, c = mixc(cols[(i + 2) % 5], P.shade, 0.15 + Lt.lamps * 0.3);
    if (x < L.x0 + 10) break;
    dab(q, x, y - w * 0.45, w * 0.9, 1, Math.PI / 2, '#3a3040', 0.8);
    q.globalAlpha = 0.95; q.fillStyle = css(c); q.beginPath(); q.ellipse(x, y - w, w, w * 0.45, 0, Math.PI, TAU); q.fill();
    for (var k = 0; k < 5; k++) dab(q, x + (r() - 0.5) * w * 1.4, y - w * (1.1 + r() * 0.25), 5, 2.4, (r() - 0.5) * 0.8, jc(mixc(c, P.glow, 0.3), r, 20), 0.7);
    for (k = 0; k < 4; k++) dab(q, x + (k - 1.5) * w * 0.4, y - 1, 4, 2.6, 0, jc(cols[(k + i) % 5], r, 30), 0.85);
    if (Lt.lamps > 0.2) { q.globalAlpha = Lt.lamps * 0.9; q.drawImage(glow('rgba(255,200,110,1)'), x - 10, y - w * 0.7 - 10, 20, 20); E.lamps.push({ x: x, y: y - w * 0.6, w: L.yw0, s: 0.7 }); }
  }
}
/* the white elephant at Chang Phueak: a pale body of dabs on a plinth, gold and red cloth */
function elephant(q, r, L, P, Lt, x) {
  var y = L.yb + L.H * 0.008, s = L.H * 0.05, white = mixc([240, 236, 226], P.shade, 0.18 + 0.2 * (1 - Lt.up)), pl = mixc(P.stone, P.shade, 0.3);
  if (Lt.lamps > 0) white = mixc(white, FLOOD, Lt.lamps * 0.4);
  q.globalAlpha = 0.95; q.fillStyle = css(pl); q.fillRect(x - s * 0.8, y - s * 0.32, s * 1.6, s * 0.32);
  q.fillStyle = css(white); q.beginPath(); q.ellipse(x, y - s * 0.75, s * 0.55, s * 0.32, 0, 0, TAU); q.fill();
  q.beginPath(); q.ellipse(x - s * 0.55, y - s * 0.85, s * 0.24, s * 0.26, 0, 0, TAU); q.fill();
  [-0.35, -0.1, 0.2, 0.4].forEach(function (k) { q.fillRect(x + k * s - s * 0.07, y - s * 0.6, s * 0.14, s * 0.3); });
  q.strokeStyle = css(white); q.lineWidth = s * 0.1; q.beginPath(); q.moveTo(x - s * 0.72, y - s * 0.8); q.quadraticCurveTo(x - s * 0.85, y - s * 0.5, x - s * 0.75, y - s * 0.36); q.stroke();
  q.fillStyle = '#c0392b'; q.fillRect(x - s * 0.15, y - s * 1.02, s * 0.36, s * 0.3); q.fillStyle = '#e8b84a'; q.fillRect(x - s * 0.15, y - s * 0.76, s * 0.36, s * 0.05);
  for (var k = 0; k < 12; k++) dab(q, x + (r() - 0.5) * s, y - s * (0.55 + r() * 0.4), 4, 2, (r() - 0.5), jc(mixc(white, r() < 0.5 ? P.shade : P.glow, 0.3), r, 12), 0.6);
}
/* the water: each dab takes its colour from the scene mirrored in the waterline, y′ = 2·yw − y,
   blended toward the water's own colour with depth and pulled into a level stroke */
function water(q, r, L, P, Lt, E, img, dpr) {
  var D = img.data, IW = img.width, IH = img.height;
  function at(x, y) { var ix = clamp(Math.round((x - L.x0) * dpr), 0, IW - 1), iy = clamp(Math.round(y * dpr), 0, IH - 1), i = (iy * IW + ix) * 4; return [D[i], D[i + 1], D[i + 2]]; }
  var ytop = L.yw0 - L.rise * L.span, g = q.createLinearGradient(0, ytop, 0, L.deck);
  g.addColorStop(0, css(mixc(P.sky1, P.water, 0.5))); g.addColorStop(1, css(P.water));
  q.globalAlpha = 1; q.fillStyle = g; q.beginPath(); q.moveTo(L.x0 - 4, L.deck + 4);
  for (var x = L.x0 - 4; x <= L.x1 + 8; x += 8) q.lineTo(x, ywAt(L, x)); q.lineTo(L.x1 + 8, L.deck + 4); q.closePath(); q.fill();
  var dark = Lt.lamps > 0.5 ? 0.8 : 0.9, N = Math.round(L.span * (L.deck - ytop) / 26), y, w, dd, i;
  for (i = 0; i < N * 1.25; i++) {
    var under = i < N * 0.25;
    x = L.x0 - 6 + r() * (L.span + 12); w = ywAt(L, x); y = w + 0.5 + r() * (L.deck + 3 - w);
    dd = clamp((y - w) / (L.deck - w), 0, 1);
    var sy = 2 * w - y + (r() - 0.5) * (2 + dd * 6), s = at(x + (r() - 0.5) * 6, sy), c = mixc([s[0] * dark, s[1] * dark, s[2] * dark], P.water, 0.18 + 0.3 * dd), u = r();
    if (u < 0.08) c = mixc(c, P.waterL, 0.5); else if (u < 0.14) c = mixc(c, P.shade, 0.4); else if (u < 0.18) c = mixc(c, P.sky0, 0.5); else if (u < 0.2) c = mixc(c, P.glow, 0.4);
    if (under) dab(q, x, y, (24 + r() * 30) * (0.7 + dd), 5 + r() * 3 + dd * 3, (r() - 0.5) * 0.04, jc(c, r, 10), 0.45);
    else dab(q, x, y, (8 + r() * 18) * (0.7 + dd * 0.8), 1.8 + r() * 1.4 + dd * 1.4, (r() - 0.5) * 0.08, jc(c, r, 18), 0.85, (r() - 0.5) * 0.15);
  }
  /* ripples, light and dark, and the bright seam where the bank meets its reflection */
  var n = L.ph ? 70 : 150;
  for (var i = 0; i < n; i++) {
    x = L.x0 + r() * L.span; w = ywAt(L, x); y = w + 3 + Math.pow(r(), 0.8) * (L.deck - w - 3); dd = (y - w) / (L.deck - w);
    dab(q, x, y, 5 + r() * 14 * (0.5 + dd), 1 + r() * 0.9, (r() - 0.5) * 0.05, jc(r() < 0.6 ? mixc(P.waterL, P.sky1, 0.3) : mixc(P.shade, P.water, 0.3), r, 18), 0.35 + r() * 0.3);
  }
  for (x = L.x0 - 4; x < L.x1 + 4; x += 6 + r() * 6) dab(q, x, ywAt(L, x) + 1.2, 8 + r() * 10, 1.4, 0, jc(mixc(P.sky1, P.waterL, 0.5), r, 14), 0.55);
  /* the sun's glitter path */
  if (E.sun) for (i = 0; i < 60; i++) {
    y = L.yw0 + 2 + Math.pow(r(), 0.85) * (L.deck - L.yw0 - 2); var hw = E.sun.r * 0.8 + (y - L.yw0) * 0.22;
    dab(q, E.sun.x + (r() - 0.5) * 2 * hw, y, 6 + r() * 10, 1.6 + r() * 1.6, 0, jc(mixc(P.glow, [255, 250, 220], 0.35), r, 14), 0.6 + 0.3 * r());
  }
  /* the strokes that move: colour of the reflection under them, lightened */
  n = L.ph ? 36 : 64;
  for (i = 0; i < n; i++) {
    x = L.x0 + r() * L.span; w = ywAt(L, x); y = w + 3 + Math.pow(r(), 0.9) * (L.deck - w - 4); dd = (y - w) / (L.deck - w);
    var sc = at(x, 2 * w - y);
    E.shim.push({ x: x, y: y, len: 8 + r() * 12 * (0.6 + dd), w: 1.4 + r() * 1.2 + dd, col: jc(mixc(sc, mixc(P.waterL, P.sky1, 0.4), 0.4), r, 14), amp: 1 + 4 * dd, f: 0.6 + r() * 0.9, k: r() * TAU, a: 0.45 + 0.35 * r() });
  }
}
/* mist on the water at dawn: long translucent strokes */
function mist(q, r, L, P, amt) {
  for (var i = 0; i < (L.ph ? 26 : 50); i++) {
    var y = L.yb - L.H * 0.04 + r() * L.H * 0.14, x = L.x0 + r() * L.span;
    dab(q, x, y, 40 + r() * 110, 5 + r() * 10, (r() - 0.5) * 0.03, jc(P.mist, r, 10), (0.08 + r() * 0.14) * amt);
  }
}
/* the near bank: its stepped stone lip, then grass and path, long violet shadows near sunset */
function nearBank(q, r, L, P, Lt) {
  var e = L.deck, lip = L.H * 0.024;
  q.globalAlpha = 1; q.fillStyle = css(mixc(P.leafS, P.stone, 0.4)); q.fillRect(L.x0 - 4, e, L.span + 8, L.H - e + 4);
  for (var x = L.x0 - 4; x < L.x1 + 4; x += 7 + r() * 5) dab(q, x, e - 1.5, 10 + r() * 8, 2.6, 0, jc(mixc(P.water, [10, 20, 30], 0.35), r, 12), 0.55);
  fill(q, r, L.x0 - 4, L.x1 + 4, e, L.H + 4, [8, 3], 9, 3.2, 0, function (x, y) {
    var f = (y - e) / (L.H - e), c;
    if (y < e + lip * 0.45) c = mixc(P.stone, P.glow, 0.25 * Lt.up);
    else if (y < e + lip) c = mixc(P.brickS, P.stone, 0.35);
    else c = f > 0.62 ? mixc(P.stone, P.brick, 0.18) : mixc(P.leaf, P.leafS, 0.25 + 0.4 * (1 - Lt.up));
    if (Lt.lamps > 0) c = mixc(c, P.shade, 0.4 * Lt.lamps);
    var u = r(); if (u < 0.1) c = mixc(c, P.glow, 0.45 * Lt.up); else if (u < 0.2) c = mixc(c, P.shade, 0.4);
    return jc(c, r, 24);
  }, 0.9);
  if (Lt.up > 0.2 && Lt.alt < 14) {   /* the long shadows of trees out of the picture, falling away from the sun */
    for (var i = 0; i < 3; i++) {
      var sx = L.x0 + L.span * (0.15 + 0.32 * i + r() * 0.1), dx = -Lt.sx * (L.H - e) * 1.6;
      for (var k = 0; k < 18; k++) { var u2 = k / 18, y = e + lip + u2 * (L.H - e - lip); dab(q, sx + dx * u2 + (r() - 0.5) * 8, y, 12 + r() * 10, 3.5, Math.atan2(L.H - e, dx) * 0 + (r() - 0.5) * 0.2, jc(P.shade, r, 14), 0.35 * Lt.up); }
    }
  }
}
/* the plaque: a painted board with the place in Thai and English */
function plaque(q, r, L, P, Lt, p, at) {
  var fs = Math.round(clamp(L.H * 0.032, 11, 15)), text = p.th + ' · ' + p.en;
  q.font = '700 ' + fs + 'px "Sarabun",system-ui,sans-serif';
  var w = q.measureText(text).width + fs * 1.4, h = fs * 1.9, x = at.x, y = at.y;
  var board = mixc([238, 226, 196], P.shade, 0.12 + Lt.lamps * 0.3);
  q.globalAlpha = 0.95; q.fillStyle = css(board); q.fillRect(x, y, w, h);
  for (var k = 0; k < w / 5; k++) { dab(q, x + k * 5 + 2, y + 1, 6, 2, 0, jc(mixc(board, P.brickS, 0.5), r, 14), 0.7); dab(q, x + k * 5 + 2, y + h - 1, 6, 2, 0, jc(mixc(board, P.brickS, 0.5), r, 14), 0.7); }
  for (k = 0; k < 6; k++) dab(q, x + 2 + r() * (w - 4), y + 3 + r() * (h - 6), 8, 2, 0, jc(mixc(board, P.glow, 0.3), r, 12), 0.35);
  q.globalAlpha = 1; q.fillStyle = '#3a2418'; q.textAlign = 'left'; q.textBaseline = 'middle'; q.fillText(text, x + fs * 0.7, y + h / 2 + 1);
  return { w: w, h: h };
}
function plaqueSize(q, L, p) { var fs = Math.round(clamp(L.H * 0.032, 11, 15)); q.font = '700 ' + fs + 'px "Sarabun",system-ui,sans-serif'; return { w: q.measureText(p.th + ' · ' + p.en).width + fs * 1.4, h: fs * 1.9 }; }
/* the edges that melt into the band: the painting's left side and top, and a ring around
   the clock, rubbed out with ragged dabs (destination-out) */
function dissolve(q, r, L, av) {
  q.save(); q.globalCompositeOperation = 'destination-out';
  var ew = L.span * 0.07, eh = L.H * 0.08, g;
  if (L.x0 > 1) {
    g = q.createLinearGradient(L.x0, 0, L.x0 + ew * 0.5, 0); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    q.globalAlpha = 1; q.fillStyle = g; q.fillRect(L.x0, 0, ew, L.H);
    for (var y = 0; y < L.H; y += 3) for (var k = 0; k < 4; k++) { var u = Math.pow(r(), 1.7); dab(q, L.x0 + u * ew, y, 8 + r() * 14, 3 + r() * 4, (r() - 0.5) * 0.6, '#000', 0.9 * (1 - u)); }
  }
  g = q.createLinearGradient(0, 0, 0, eh * 0.5); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  q.globalAlpha = 1; q.fillStyle = g; q.fillRect(L.x0, 0, L.span, eh);
  for (var x = L.x0; x < L.x1; x += 4) for (k = 0; k < 3; k++) { u = Math.pow(r(), 1.7); dab(q, x, u * eh, 8 + r() * 12, 3 + r() * 4, (r() - 0.5) * 0.8, '#000', 0.9 * (1 - u)); }
  if (av) {
    q.globalAlpha = 1; q.fillStyle = '#000'; q.beginPath(); q.arc(av.cx, av.cy, av.r * 0.98, 0, TAU); q.fill();
    var n = Math.round(av.r * 5);
    for (k = 0; k < n; k++) { var a = r() * TAU, u2 = Math.pow(r(), 1.5), rr = av.r * (0.97 + u2 * 0.13); dab(q, av.cx + Math.cos(a) * rr, av.cy + Math.sin(a) * rr, 7 + r() * 9, 3 + r() * 3, a + Math.PI / 2, '#000', 0.9 * (1 - u2)); }
  }
  q.restore();
}

function build(S, p, alt) {
  var dpr = (S.c.getTransform ? S.c.getTransform().a : 1) || 1, L = layout(S, p), cv = document.createElement('canvas');
  cv.width = Math.max(1, Math.ceil(L.span * dpr)); cv.height = Math.max(1, Math.ceil(L.H * dpr));
  var q = cv.getContext('2d', { willReadFrequently: true });
  q.setTransform(dpr, 0, 0, dpr, -L.x0 * dpr, 0); q.lineCap = 'round'; q.lineJoin = 'round';
  var r = K.rnd(((S.seed ^ K.hash(p.k)) >>> 0) || 7), Lt = light(S, p, alt), P = pal(alt, Lt.am);
  if (Lt.lamps > 0) { P.brick = mixc(P.brick, FLOOD, Lt.lamps * 0.75); P.brickS = mixc(P.brickS, FLOODS, Lt.lamps * 0.6); }
  var E = { L: L, P: P, Lt: Lt, p: p, shim: [], leaf: [], lamps: [], fount: [], lily: [], cv: cv, dpr: dpr };
  /* the sun on the canvas: across, its azimuth against the view's ±58°; up, its altitude over ~27° from the treeline */
  if (Math.abs(Lt.rel) < 58 && alt > -1.5 && alt < 26) {
    var hz = L.yt - L.H * 0.05, sx = L.x0 + L.span * 0.5 + Lt.rel / 58 * L.span * 0.5, sy = hz - (alt + 1) / 27 * (hz - L.H * 0.1);
    if (sx > L.x0 + L.span * 0.08 && sx < L.x1 - L.span * 0.05) E.sun = { x: sx, y: sy, r: L.H * 0.04 };
    if (E.sun && S.avoid && Math.hypot(sx - S.avoid.cx, sy - S.avoid.cy) < S.avoid.r + E.sun.r * 3) E.sun = null;
  }
  sky(q, r, L, P, Lt, E);
  var ms = rel(azTo(p, SUTHEP[0], SUTHEP[1]), p.look);
  if (Math.abs(ms) < 60) mountain(q, r, L, P, Lt, L.x0 + L.span * 0.5 + ms / 58 * L.span * 0.5);
  /* a row of trees behind the wall, hazier with distance */
  E.floodY = L.yb;
  for (var x = L.x0 - 30; x < L.x1 + 30; x += L.H * (0.13 + r() * 0.1)) {
    var s = scAt(L, x), b = (L.corner ? ywAt(L, x) - L.H * 0.022 * s - L.wallH * 0.62 * s : L.yt) + L.H * 0.035 * s;
    var rx = L.H * (0.08 + r() * 0.07) * s;
    crown(q, r, L, P, Lt, E, x, b - L.H * (0.03 + r() * 0.05) * s, rx, rx * (0.55 + r() * 0.2), 0.2 + 0.25 * (1 - s), Math.round(rx * rx * 0.05));
  }
  if (p.kind === 'gate') gate(q, r, L, P, Lt, p, E); else bastion(q, r, L, P, Lt, p, E);
  farBank(q, r, L, P, Lt, p);
  E.keep = true;   /* from here the trees stand in front: their edge leaves sway */
  /* the place's own: trees beside the wall, palms, lamps, stalls, the elephant */
  var Bw = E.Bw || L.ww, side = function (k) { return L.cx + k * (Bw / 2 + L.H * 0.06); };
  if (p.rain) { rainTree(q, r, L, P, Lt, E, side(-1), ywAt(L, side(-1)) - L.H * 0.026, 1.25 * scAt(L, side(-1))); if (p.rain > 1) rainTree(q, r, L, P, Lt, E, side(1) + L.H * 0.05, ywAt(L, side(1)) - L.H * 0.026, 1.1 * scAt(L, side(1))); }
  if (p.banyan) banyan(q, r, L, P, Lt, E, side(-1) - L.H * 0.05, ywAt(L, side(-1)) - L.H * 0.024, 1.25 * scAt(L, side(-1)));
  if (p.bigTree) rainTree(q, r, L, P, Lt, E, L.cx + L.ww * 0.62, L.yb + L.H * 0.012, 1.35);
  if (p.kind === 'gate' && !p.plaza && !p.bigTree && !p.palms) rainTree(q, r, L, P, Lt, E, L.cx - L.ww * 0.62, L.yb + L.H * 0.012, 0.95);
  if (p.elephant) elephant(q, r, L, P, Lt, L.cx - L.ww * 0.3);
  if (p.stalls) stalls(q, r, L, P, Lt, E);
  var nl = L.ph ? 3 : 5;
  for (var i = 0; i < nl; i++) { x = L.x0 + L.span * (i + 0.5) / nl + (r() - 0.5) * 12; if (Math.abs(x - L.cx) < (p.kind === 'gate' ? L.H * 0.08 : Bw * 0.55)) continue; lampPost(q, r, L, P, Lt, E, x, scAt(L, x)); }
  var np = p.palms || (p.plaza ? 0 : 1);
  for (i = 0; i < np; i++) {
    var k = i % 2 ? 1 : -1, px = L.cx + k * (Bw / 2 + L.H * (0.1 + 0.14 * Math.floor(i / 2)) + r() * L.H * 0.05);
    if (px < L.x0 + 10 || px > L.x1 - 10) continue;
    palm(q, r, L, P, Lt, E, px, ywAt(L, px) - L.H * 0.014 * scAt(L, px), 0.95 * scAt(L, px));
  }
  /* the water, mirrored from what is painted so far */
  var img = q.getImageData(0, 0, cv.width, cv.height);
  water(q, r, L, P, Lt, E, img, dpr);
  var mAmt = Lt.am ? clamp(1 - Math.abs(alt - 1) / 9, 0, 1) : 0.4 * clamp(1 - Math.abs(alt + 2) / 6, 0, 1);
  if (mAmt > 0.05) mist(q, r, L, P, mAmt);
  nearBank(q, r, L, P, Lt);
  /* fountains: one before a corner's bastion and one down the arm; two along a gate's moat */
  var fy = L.yw0 + (L.deck - L.yw0) * 0.32;
  (L.corner ? [L.cx + E.Bw * 0.15, L.cx - L.span * 0.36] : [L.cx - L.span * 0.3, L.cx + L.span * 0.31]).forEach(function (fx, j) {
    if (L.ph && j) return; if (fx < L.x0 + 20 || fx > L.x1 - 20) return;
    var y = fy + (L.corner && j ? -L.rise * Math.abs(fx - L.cx) : 0); E.fount.push({ x: fx, y: y, s: 0.65 + 0.45 * (y - L.yw0) / (L.deck - L.yw0) * (L.corner && j ? 0.6 : 1) });
  });
  /* lily clusters, drifting */
  var nc = L.ph ? 3 : 5;
  for (i = 0; i < nc; i++) {
    var cy = L.yw0 + (L.deck - L.yw0) * (0.45 + 0.5 * r()), ds = 0.6 + 0.6 * (cy - L.yw0) / (L.deck - L.yw0), m = 2 + Math.floor(r() * 3);
    for (k = 0; k < m; k++) E.lily.push({ x: L.x0 + L.span * (i + r() * 0.6) / nc + k * 12 * ds, y: cy + (r() - 0.5) * 6 * ds, s: ds * (0.7 + 0.5 * r()), k: r() * TAU, f: r() < 0.45 ? (r() < 0.5 ? '#f4b6c8' : '#fbf3ea') : null, v: (2 + r() * 2) * (i % 2 ? 1 : -1) });
  }
  /* the plaque and where the banner goes */
  var ps = plaqueSize(q, L, p), pad = 10, bwid = 0;
  if (S.label) { q.font = '800 ' + Math.round(Math.max(12, L.hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif'; bwid = q.measureText(S.label).width + 20 + Math.max(20, L.hh * 0.32) * 1.1; }
  var bh = Math.max(20, L.hh * 0.32);
  E.banner = { cx: L.x1 - bwid / 2 - (L.ph ? 14 : 28), y: L.H - bh - 8 };
  var low = { x: L.x0 + (L.x0 > 1 ? L.span * 0.075 : pad), y: L.H - ps.h - 8 };
  if (L.ph || low.x + ps.w + 16 > E.banner.cx - bwid / 2) {
    low = { x: L.x0 + (L.x0 > 1 ? L.span * 0.075 : pad), y: L.H * 0.09 };
    var av = S.avoid;   /* the clock's circle in the way: the plaque sits over the near bank, above the banner */
    if (av && low.x + ps.w > av.cx - av.r && low.y < av.cy + av.r) low = { x: L.x0 + pad, y: E.banner.y - ps.h - 6 };
  }
  E.plq = low; plaque(q, r, L, P, Lt, p, low);
  dissolve(q, r, L, S.avoid);
  q.globalAlpha = 1;
  return E;
}

/* ---------------------------------------------------------------- what moves */
function fd(c, x, y, len, w, col, a) { c.globalAlpha = a; c.strokeStyle = col; c.lineWidth = w; c.beginPath(); c.moveTo(x - len / 2, y); c.lineTo(x + len / 2, y); c.stroke(); }
/* the reflections tremble: strips of the water's band redrawn, each slid by A(y)·sin(ωt + ky) */
function tremble(c, E, t) {
  var L = E.L, top = Math.floor(L.yw0 - L.rise * L.span) + 2, st = L.ph ? 6 : 5, ed = L.x0 > 1 ? Math.round(L.span * 0.08) : 0;
  for (var y = top; y < L.deck - 2; y += st * 2) {   /* every other strip; the ones between stay still */
    var dd = (y - L.yw0) / (L.deck - L.yw0), dx = (0.5 + 2.2 * clamp(dd, 0, 1)) * Math.sin(t / 1000 * 1.6 + y * 0.21);
    c.drawImage(E.cv, ed * E.dpr, y * E.dpr, E.cv.width - ed * E.dpr, st * E.dpr, L.x0 + ed + dx, y, L.span - ed, st);
  }
}
/* a fountain: a soft plume of spray, jets as parabolas, y = v₀t − ½gt², drawn as quadratic
   curves with the control point at twice the peak; drops ride each arc, foam at the foot */
function fountain(c, f, t, E) {
  var L = E.L, n = L.ph ? 5 : 7, Hp = L.H * 0.1 * f.s, Wf = L.H * 0.1 * f.s, lamp = E.Lt.lamps, sway = Math.sin(t / 1700) * Wf * 0.06, i, j;
  var col = lamp > 0.4 ? '#ffe2a0' : '#f8fbff', T = 1.6;
  c.globalAlpha = 0.32 + 0.04 * Math.sin(t / 400); c.drawImage(glow(lamp > 0.4 ? 'rgba(255,226,160,1)' : 'rgba(248,251,255,1)'), f.x - Wf * 0.75, f.y - Hp * 1.5, Wf * 1.5, Hp * 1.8);
  c.globalAlpha = 0.26; c.strokeStyle = col; c.lineWidth = Math.max(1.4, 2.2 * f.s); c.beginPath();
  for (i = 0; i < n; i++) { var sp = i / (n - 1) * 2 - 1, hk = Hp * (1 - 0.45 * sp * sp), wk = Wf * sp + sway; c.moveTo(f.x, f.y); c.quadraticCurveTo(f.x + wk / 2, f.y - 2 * hk, f.x + wk, f.y); }
  c.stroke();
  c.fillStyle = col;
  for (i = 0; i < n; i++) {
    sp = i / (n - 1) * 2 - 1; hk = Hp * (1 - 0.45 * sp * sp); wk = Wf * sp + sway;
    for (j = 0; j < 3; j++) { var u = (t / 1000 / T + j / 3 + i * 0.137) % 1, x = f.x + wk * u, y = f.y - 4 * hk * u * (1 - u); c.globalAlpha = 0.8; c.fillRect(x - 1, y - 1, 2 * f.s + 0.6, 2 * f.s + 0.6); }
  }
  for (i = 0; i < 3; i++) fd(c, f.x + Math.sin(t / 300 + i * 2) * Wf * 0.25, f.y + 1 + i, Wf * (0.5 - i * 0.1), 2.4, col, 0.55);
  for (i = 0; i < 3; i++) fd(c, f.x + Math.sin(t / 500 + i) * 2, f.y + 5 + i * Hp * 0.25, 4 + i * 2, 1.6, col, 0.3 - i * 0.07);
}
/* a lily pad drifting, x = x₀ + vt wrapped across the moat; a flower by day, shut by night */
function lily(c, l, t, E) {
  var L = E.L, P = E.P, span = L.span + 60, x = L.x0 - 30 + ((((l.x - L.x0 + 30) + t / 1000 * l.v) % span) + span) % span, y = l.y + Math.sin(t / 1300 + l.k) * 0.8, s = l.s * L.H / 440;
  c.globalAlpha = 0.95; c.fillStyle = l.pc || (l.pc = css(mixc(mixc(P.leafS, P.leaf, 0.55), P.water, 0.15)));
  c.beginPath(); c.ellipse(x, y, 9 * s, 3.2 * s, 0, 0.35, TAU - 0.1); c.lineTo(x, y); c.closePath(); c.fill();
  fd(c, x - 2 * s, y - 0.8 * s, 7 * s, 1.4 * s, l.hc || (l.hc = css(mixc(P.leaf, P.glow, 0.45))), 0.8);
  if (l.f) { if (E.Lt.up > 0.2) { fd(c, x + 2 * s, y - 2.2 * s, 4 * s, 2.6 * s, l.f, 0.95); fd(c, x + 2 * s, y - 3.6 * s, 2 * s, 2 * s, '#ffe08a', 0.9); } else fd(c, x + 2 * s, y - 2 * s, 2 * s, 2 * s, l.f, 0.7); }
}
/* the leaves at a crown's edge, swayed by the breeze, dx = a·sin(ωt + φ) */
function sway(c, E, t) {
  for (var i = 0; i < E.leaf.length; i++) {
    var l = E.leaf[i], dx = Math.sin(t / 1000 * 1.3 + l.k) * 1.6 + Math.sin(t / 1000 * 3.1 + l.k * 2) * 0.5, dy = Math.cos(t / 1000 * 1.1 + l.k) * 0.6;
    var ex = Math.cos(l.ang) * l.len / 2, ey = Math.sin(l.ang) * l.len / 2;
    c.globalAlpha = 0.85; c.strokeStyle = l.col; c.lineWidth = l.w; c.beginPath(); c.moveTo(l.x + dx - ex, l.y + dy - ey); c.lineTo(l.x + dx + ex, l.y + dy + ey); c.stroke();
  }
}
/* a bird: two wing arcs, flapping as sin ωt */
function bird(c, x, y, w, flap, col, a) {
  c.globalAlpha = a; c.strokeStyle = col; c.lineWidth = Math.max(1.2, w * 0.25); c.beginPath();
  c.moveTo(x - w, y - flap * w * 0.6); c.quadraticCurveTo(x - w * 0.4, y - w * 0.15, x, y); c.quadraticCurveTo(x + w * 0.4, y - w * 0.15, x + w, y - flap * w * 0.6); c.stroke();
}
/* swallows over the water on figure-eights, x = a·sin u, y = b·sin 2u */
function swallows(c, E, t) {
  var L = E.L, n = L.ph ? 2 : 3, col = css(mixc(E.P.leafS, [20, 20, 30], 0.6));
  for (var i = 0; i < n; i++) {
    var u = t / 1000 * (0.11 + i * 0.02) + i * 2.1, x = L.x0 + L.span * (0.5 + 0.4 * Math.sin(u)), y = L.yw0 - L.H * 0.06 + L.H * 0.07 * Math.sin(2 * u + i);
    bird(c, x, y, L.H * 0.012, Math.sin(t / 70 + i * 3), col, 0.85);
  }
}
/* Tha Phae's pigeons: some pecking on the plaza, head down as |sin|⁴, some wheeling over the gate */
function pigeons(c, E, t, r) {
  var L = E.L, P = E.P, body = css(mixc(mixc(P.stone, P.shade, 0.55), [120, 120, 140], 0.3)), i, n = L.ph ? 6 : 11;
  for (i = 0; i < n; i++) {
    var x = L.cx + (E.pg[i] - 0.5) * L.ww * 1.1, y = L.yb + (L.yw0 - L.yb) * (0.3 + 0.45 * E.pg[i + 11]), pk = Math.pow(Math.abs(Math.sin(t / 650 + i * 1.7)), 4) * 2;
    fd(c, x, y, 4.5, 3, body, 0.9); c.fillStyle = body; c.fillRect(x + 2, y - 2.5 + pk, 2, 2);
  }
  for (i = 0; i < 3; i++) { var u = t / 1000 * 0.5 + i * 2.1; bird(c, L.cx + Math.cos(u) * L.ww * 0.35, E.wall[2] - L.H * 0.05 + Math.sin(u) * L.H * 0.025, L.H * 0.01, Math.sin(t / 90 + i), body, 0.85); }
}
/* a stroller with a paper parasol on the near bank: a column of dabs, a dome, walking x = x₀ + vt */
function stroller(c, E, t) {
  var L = E.L, P = E.P, h = L.hh * 0.55, span = L.span + h * 2, x = L.x0 - h + ((t / 1000 * h * 0.12 + E.walk0 * span) % span), y = L.deck + (L.H - L.deck) * 0.3, bob = Math.abs(Math.sin(t / 420)) * h * 0.02;
  var dress = css(mixc([246, 240, 230], P.shade, 0.15 + 0.35 * E.Lt.lamps)), shade = css(mixc(P.shade, P.water, 0.3));
  fd(c, x - E.Lt.sx * h * 0.25, y + 1, h * 0.5, 2.4, shade, 0.4);
  c.globalAlpha = 0.95; c.strokeStyle = dress; c.lineWidth = h * 0.15; c.beginPath(); c.moveTo(x, y - h * 0.62 - bob); c.lineTo(x + h * 0.03, y - h * 0.04); c.stroke();
  c.strokeStyle = shade; c.lineWidth = h * 0.06; c.globalAlpha = 0.6; c.beginPath(); c.moveTo(x - E.Lt.sx * h * 0.05, y - h * 0.5 - bob); c.lineTo(x - E.Lt.sx * h * 0.05, y - h * 0.08); c.stroke();
  c.globalAlpha = 1; c.fillStyle = '#c99a74'; c.beginPath(); c.arc(x, y - h * 0.72 - bob, h * 0.065, 0, TAU); c.fill();
  if (E.Lt.lamps > 0.6) { c.globalAlpha = 0.9; c.drawImage(glow('rgba(255,200,110,1)'), x + h * 0.1 - 9, y - h * 0.4 - 9 - bob, 18, 18); c.fillStyle = '#ffd27a'; c.fillRect(x + h * 0.08, y - h * 0.42 - bob, 3, 4); return; }
  c.strokeStyle = '#5a4030'; c.lineWidth = 1; c.beginPath(); c.moveTo(x + h * 0.04, y - h * 0.52 - bob); c.lineTo(x + h * 0.12, y - h * 0.98 - bob); c.stroke();
  c.fillStyle = E.parasol; c.beginPath(); c.ellipse(x + h * 0.12, y - h * 0.96 - bob, h * 0.3, h * 0.17, -0.12, Math.PI, TAU); c.fill();
  fd(c, x + h * 0.12 + E.Lt.sx * h * 0.1, y - h * 1.04 - bob, h * 0.2, 2, 'rgba(255,255,240,1)', 0.5);
}
/* a cyclist on the far road, x = x₀ − vt, legs turning with the pedals */
function cyclist(c, E, t) {
  var L = E.L, P = E.P, span = L.span + 40, x = L.x1 + 20 - ((t / 1000 * L.H * 0.03 + E.walk0 * 300) % span), s = scAt(L, x), y = ywAt(L, x) - L.H * (L.corner ? 0.006 : 0.016) * s, h = L.H * 0.035 * s;
  var dark = css(mixc(P.leafS, [20, 20, 30], 0.5)), shirt = E.shirt;
  c.globalAlpha = 0.85; c.strokeStyle = dark; c.lineWidth = 1;
  c.beginPath(); c.arc(x - h * 0.35, y - h * 0.18, h * 0.18, 0, TAU); c.moveTo(x + h * 0.53, y - h * 0.18); c.arc(x + h * 0.35, y - h * 0.18, h * 0.18, 0, TAU); c.stroke();
  var a = t / 160, fx = x + Math.cos(a) * h * 0.12, fy = y - h * 0.2 + Math.sin(a) * h * 0.12;
  c.beginPath(); c.moveTo(x, y - h * 0.6); c.lineTo(fx, fy); c.stroke();
  fd(c, x - h * 0.05, y - h * 0.75, h * 0.35, h * 0.22, shirt, 0.95);
  c.fillStyle = '#c99a74'; c.fillRect(x - h * 0.3, y - h * 1.0, h * 0.18, h * 0.18);
  if (E.Lt.lamps > 0.5) { c.globalAlpha = 0.9; c.fillStyle = '#fff4c8'; c.fillRect(x - h * 0.6, y - h * 0.4, 2, 2); }
}
/* a red songthaew along the far road, its lamps lit after dusk */
function songthaew(c, E, t) {
  var L = E.L, span = L.span + 80, x = L.x0 - 40 + ((t / 1000 * L.H * 0.05 + E.walk0 * 500) % span), y = L.yw0 - L.H * 0.014, w = L.H * 0.06, h = L.H * 0.026;
  var red = css(mixc([200, 40, 36], E.P.shade, 0.15 + 0.4 * E.Lt.lamps));
  fd(c, x, y - h * 0.55, w, h, red, 0.92); fd(c, x - w * 0.05, y - h * 1.05, w * 0.9, h * 0.25, css(mixc([235, 230, 220], E.P.shade, 0.3)), 0.8);
  fd(c, x + w * 0.3, y - h * 0.65, w * 0.18, h * 0.35, css(mixc(E.P.sky1, E.P.shade, 0.3)), 0.8);
  if (E.Lt.lamps > 0.4) { c.globalAlpha = 0.9; c.drawImage(glow('rgba(255,236,170,1)'), x + w * 0.5 - 6, y - h * 0.4 - 6, 12, 12); fd(c, x + w * 0.5, y + 6, 3, 8, '#ffe9a8', 0.3); }
}
/* the fisherman at Katam, sitting on the near bank; his float bobs, rings spread from it, r = r₀ + vt */
function fisher(c, E, t) {
  var L = E.L, P = E.P, h = L.hh * 0.42, x = L.x0 + L.span * 0.22, y = L.deck + (L.H - L.deck) * 0.35, dark = css(mixc(P.leafS, [40, 30, 30], 0.4));
  fd(c, x, y - h * 0.08, h * 0.35, h * 0.14, css(mixc([60, 80, 120], P.shade, 0.3)), 0.95);
  c.globalAlpha = 0.95; c.strokeStyle = css(mixc([200, 120, 60], P.shade, 0.2)); c.lineWidth = h * 0.16; c.beginPath(); c.moveTo(x, y - h * 0.1); c.lineTo(x + h * 0.03, y - h * 0.42); c.stroke();
  c.fillStyle = css(mixc([220, 200, 150], P.shade, 0.2)); c.beginPath(); c.ellipse(x + h * 0.03, y - h * 0.58, h * 0.14, h * 0.06, 0, 0, TAU); c.fill();
  var tx = x + h * 0.9, ty = y - h * 0.95, bob = Math.sin(t / 700) * 1.3, fxx = tx + h * 0.15, fyy = L.deck - (L.deck - L.yw0) * 0.12 + bob;
  c.strokeStyle = dark; c.lineWidth = 1.2; c.beginPath(); c.moveTo(x + h * 0.05, y - h * 0.35); c.lineTo(tx, ty); c.stroke();
  c.globalAlpha = 0.5; c.lineWidth = 0.6; c.beginPath(); c.moveTo(tx, ty); c.quadraticCurveTo(tx + h * 0.1, (ty + fyy) / 2, fxx, fyy); c.stroke();
  c.globalAlpha = 1; c.fillStyle = '#e04a3a'; c.fillRect(fxx - 1, fyy - 2, 2.2, 2.6);
  var u = (t / 3000) % 1; c.globalAlpha = 0.5 * (1 - u); c.strokeStyle = css(P.waterL); c.lineWidth = 0.9; c.beginPath(); c.ellipse(fxx, fyy + 1, 2 + u * 14, 0.8 + u * 3.5, 0, 0, TAU); c.stroke();
}
/* fireflies at dusk: blinks as max(0, sin ωt)³, drifting on Lissajous loops */
function fireflies(c, E, t, n) {
  var L = E.L, spr = glow('rgba(214,255,120,1)');
  for (var i = 0; i < n; i++) {
    var bx = E.ff[i * 2], by = E.ff[i * 2 + 1], x = bx + Math.sin(t / 2300 + i * 1.9) * 12, y = by + Math.sin(t / 1700 + i) * 6, a = Math.pow(Math.max(0, Math.sin(t / 900 * (0.7 + (i % 5) * 0.13) + i * 2.3)), 3);
    if (a < 0.05) continue;
    c.globalAlpha = a; c.drawImage(spr, x - 6, y - 6, 12, 12); c.fillStyle = '#f6ffb0'; c.fillRect(x - 0.8, y - 0.8, 1.6, 1.6);
  }
}
/* sky lanterns rising from behind the wall, x = x₀ + a·sin(2πu·1.3), and their light in the water at y′ = 2·yw − y */
function lanterns(c, E, t, n, seed) {
  var L = E.L, spr = glow('rgba(255,190,90,1)');
  for (var i = 0; i < n; i++) {
    var P = 30 + i * 7, u = ((t / 1000) / P + i / n + (seed % 100) / 100) % 1, y0 = E.wall[2];
    var x = L.x0 + L.span * (0.12 + 0.7 * ((i * 0.618 + (seed % 37) / 37) % 1)) + Math.sin(u * TAU * 1.3 + i) * L.hh * 0.4, y = y0 - u * y0 * 0.95;
    var sz = L.H * 0.016 * (1 - u * 0.5), a = Math.min(1, u * 8, (1 - u) * 3), fl = 0.85 + 0.15 * Math.sin(t / 110 + i * 3);
    c.globalAlpha = a * fl * 0.8; c.drawImage(spr, x - sz * 3, y - sz * 3, sz * 6, sz * 6);
    c.globalAlpha = a; c.fillStyle = '#ffcf80'; c.beginPath(); c.moveTo(x - sz * 0.55, y + sz * 0.8); c.lineTo(x - sz * 0.7, y - sz * 0.5); c.quadraticCurveTo(x, y - sz * 1.2, x + sz * 0.7, y - sz * 0.5); c.lineTo(x + sz * 0.55, y + sz * 0.8); c.closePath(); c.fill();
    c.fillStyle = '#fff6c0'; c.fillRect(x - 1, y + sz * 0.6, 2, 2);
    var ry = 2 * ywAt(L, x) - y;
    if (ry < L.deck - 4) { c.globalAlpha = a * 0.45; c.drawImage(spr, x - sz * 2.5, ry - sz * 2.5, sz * 5, sz * 5); for (var k = 0; k < 3; k++) fd(c, x + Math.sin(t / 400 + k + i) * 2, ry + (k - 1) * sz * 1.1, sz * (1.6 - k * 0.3), 1.6, '#ffcf80', a * (0.6 - k * 0.12)); }
  }
}
/* a krathong on the water, a candle flame flickering 1 ± 0.15·sin ωt, its streak of light below */
function krathong(c, E, t, i) {
  var L = E.L, span = L.span + 60, x = L.x0 - 30 + ((t / 1000 * (3 + i) + E.walk0 * 400 + i * span * 0.5) % span), y = L.yw0 + (L.deck - L.yw0) * (0.55 + 0.3 * i) + Math.sin(t / 900 + i) * 0.8, s = (0.8 + 0.4 * i) * L.H / 440;
  var fl = 1 + 0.15 * Math.sin(t / 90 + i * 2), a = clamp(E.Lt.lamps * 1.4 + 0.3, 0, 1);
  c.globalAlpha = 0.9 * a; c.drawImage(glow('rgba(255,180,80,1)'), x - 14 * s, y - 18 * s, 28 * s, 28 * s);
  for (var k = 0; k < 4; k++) fd(c, x + Math.sin(t / 380 + k) * 1.5, y + 4 * s + k * 4 * s, (6 - k) * s, 1.6, '#ffc070', 0.5 * a - k * 0.08);
  c.globalAlpha = 1; c.fillStyle = '#4f7d3a'; c.beginPath(); c.ellipse(x, y, 7 * s, 2.6 * s, 0, 0, TAU); c.fill();
  fd(c, x - 3 * s, y - 2 * s, 3 * s, 2.4 * s, '#f2a03a', 1); fd(c, x + 3 * s, y - 2 * s, 3 * s, 2.4 * s, '#e5567f', 1); fd(c, x, y - 2.6 * s, 3 * s, 2.4 * s, '#f6e7c8', 1);
  c.fillStyle = '#fff6c0'; c.fillRect(x - 0.6, y - 6 * s, 1.2, 3 * s);
  c.fillStyle = '#ffb347'; c.beginPath(); c.moveTo(x, y - 6 * s - 5 * s * fl); c.quadraticCurveTo(x + 2 * s, y - 6.5 * s, x, y - 5.6 * s); c.quadraticCurveTo(x - 2 * s, y - 6.5 * s, x, y - 6 * s - 5 * s * fl); c.fill();
}
/* the dawn's gold motes and the noon's glints on the water: four-point stars, alpha |sin|³ */
function sparkles(c, E, t, n, gold) {
  var L = E.L;
  c.fillStyle = gold ? 'rgb(255,214,90)' : 'rgb(255,255,245)';
  for (var i = 0; i < n; i++) {
    var bx = E.sp[i * 2], by = E.sp[i * 2 + 1], x = bx + (gold ? Math.sin(t / 2400 + i) * 10 : 0), y = by + (gold ? Math.cos(t / 3100 + i) * 6 : 0);
    var a = Math.pow(Math.abs(Math.sin(t / (gold ? 900 : 420) * (0.6 + (i % 4) * 0.2) + i * 1.3)), gold ? 3 : 8), z = (gold ? 2.6 : 2.2) * (0.5 + a);
    if (a < 0.08) continue;
    c.globalAlpha = a; c.beginPath(); c.moveTo(x, y - z * 2); c.quadraticCurveTo(x, y, x + z * 2, y); c.quadraticCurveTo(x, y, x, y + z * 2); c.quadraticCurveTo(x, y, x - z * 2, y); c.quadraticCurveTo(x, y, x, y - z * 2); c.fill();
  }
}

var CACHE = [];
function cached(S, p, alt) {
  var dpr = (S.c.getTransform ? S.c.getTransform().a : 1) || 1, av = S.avoid;
  var tag = [S.W, S.H, S.x0, S.x1, S.deck, p.k, Math.floor((S.now || Date.now()) / 9e5), S.seed, dpr, S.phone ? 1 : 0, S.label, av ? [Math.round(av.cx), Math.round(av.cy), Math.round(av.r)].join(',') : ''].join('|');
  for (var i = 0; i < CACHE.length; i++) if (CACHE[i].tag === tag) return CACHE[i];
  var E = build(S, p, alt); E.tag = tag;
  var r = K.rnd((S.seed >>> 0) + 17), L = E.L;
  E.walk0 = r(); E.parasol = ['#e88aa8', '#9fd0b4', '#f4efe2', '#9db8e8', '#f2c46a'][Math.floor(r() * 5)]; E.shirt = ['#e5567f', '#4d8fd1', '#f2c94c', '#f4efe2'][Math.floor(r() * 4)];
  E.pg = []; for (i = 0; i < 22; i++) E.pg.push(r());
  E.ff = []; for (i = 0; i < 22; i++) { E.ff.push(L.x0 + L.span * (0.06 + 0.88 * r())); E.ff.push(r() < 0.5 ? L.yt - L.H * 0.05 + r() * L.H * 0.12 : L.deck - L.H * 0.02 + r() * (L.H - L.deck)); }
  E.sp = []; for (i = 0; i < 16; i++) { E.sp.push(L.x0 + L.span * (0.06 + 0.88 * r())); E.sp.push(L.yw0 + 4 + r() * (L.deck - L.yw0 - 8)); }
  CACHE.unshift(E); if (CACHE.length > 8) CACHE.pop();
  return E;
}

/* the moat at a gate or a corner, at this hour; noMagic: its own magic is drawn here */
function draw(S) {
  S.noMagic = true;
  if (S.span < 40 || S.H < 40) return;
  var p = placeOf(S), alt = S.alt != null ? S.alt : sunPos(S.now || Date.now()).alt, E = cached(S, p, alt), L = E.L, Lt = E.Lt, c = S.c, t = S.t, av = S.avoid, i;
  c.save();
  c.beginPath(); c.rect(S.x0, 0, S.span, S.H); if (av) c.arc(av.cx, av.cy, av.r, 0, TAU); c.clip('evenodd');
  c.lineCap = 'round';
  c.globalAlpha = 1; c.drawImage(E.cv, S.x0, 0, S.span, S.H);
  tremble(c, E, t);
  for (i = 0; i < E.shim.length; i++) { var s = E.shim[i]; fd(c, s.x + s.amp * Math.sin(t / 1000 * s.f + s.k), s.y, s.len, s.w, s.col, s.a * (0.65 + 0.35 * Math.sin(t / 1000 * 1.7 * s.f + s.k * 1.7))); }
  if (E.sun) for (i = 0; i < 16; i++) { var y = L.yw0 + 3 + (i / 16) * (L.deck - L.yw0 - 6), hw = E.sun.r * 0.8 + (y - L.yw0) * 0.22, a = Math.pow(Math.abs(Math.sin(t / 260 * (0.7 + (i % 3) * 0.2) + i * 1.9)), 3); fd(c, E.sun.x + Math.sin(i * 7.3 + t / 1400) * hw, y, 6 + (i % 4) * 3, 2, '#fff6d8', a * 0.85); }
  if (Lt.lamps > 0.15) E.lamps.forEach(function (l, j) { for (var k = 0; k < 5; k++) { var yy = l.w + 3 + k * (L.deck - l.w) * 0.11; fd(c, l.x + Math.sin(t / 380 + k * 1.3 + j) * (1 + k * 0.6), yy, (7 - k) * l.s + 2, 2, '#ffd27a', Lt.lamps * (0.75 - k * 0.12)); } });
  E.fount.forEach(function (f) { fountain(c, f, t, E); });
  E.lily.forEach(function (l) { lily(c, l, t, E); });
  sway(c, E, t);
  if (p.pigeons && Lt.up > 0.3) pigeons(c, E, t); else if (Lt.up > 0.2) swallows(c, E, t);
  if (p.kind === 'gate' && Lt.alt > -6) songthaew(c, E, t);
  if (Lt.alt > -7) cyclist(c, E, t);
  if (p.fisher && Lt.alt > -5) fisher(c, E, t);
  stroller(c, E, t);
  /* the magic, by the hour */
  if (Lt.alt < 2) fireflies(c, E, t, Math.round((L.ph ? 10 : 20) * clamp((2 - Lt.alt) / 6, 0.3, 1)));
  if (Lt.alt < 4) { krathong(c, E, t, 0); if (!L.ph) krathong(c, E, t, 1); }
  if (Lt.lamps > 0.6) lanterns(c, E, t, L.ph ? 3 : 4, S.seed >>> 0);
  if (Lt.am && Lt.alt > -6 && Lt.alt < 14) sparkles(c, E, t, L.ph ? 9 : 16, true);
  else if (Lt.alt > 26) sparkles(c, E, t, L.ph ? 7 : 12, false);
  c.globalAlpha = 1;
  K.banner(c, E.banner.cx, E.banner.y, S.label, S.hh, '#2f6f7a', S.seed, S.hits);
  c.restore();

  // Tha Phae Gate v2 set-piece
  if (p.k === 'tha-phae-gate' && (!D.versions || D.versions['moat:tha-phae-gate'] >= 2)) {
    // Tung flags on the plaza
    var tw = L.H * 0.04, th = L.H * 0.5;
    for (var j = 0; j < 2; j++) {
      var k = j === 0 ? -1 : 1;
      var fx = L.cx + k * L.ww * 0.45, fy = L.yb + L.H * 0.05;
      c.strokeStyle = '#c9a05a'; c.lineWidth = 2; c.beginPath(); c.moveTo(fx, fy); c.lineTo(fx, fy - th); c.stroke();
      var fW = L.H * 0.08, fH = L.H * 0.4;
      var fY = fy - th * 0.9;
      // Tung swaying
      var swayF = Math.sin(t / 800 + j) * 5;
      c.fillStyle = '#d35400';
      c.beginPath(); c.moveTo(fx, fY); c.lineTo(fx + fW + swayF, fY);
      c.lineTo(fx + fW + swayF * 0.5, fY + fH * 0.8);
      c.lineTo(fx, fY + fH); c.closePath(); c.fill();
    }
    
    // Fon lep dancers (Lanna fingernail dance)
    if (K.person && K.POSE) {
      var dcrew = K.town(S, 2, { mohom: 0 }); 
      var a1 = Math.sin(t / 600) * 0.5;
      var poseD1 = { lean: 0, arms: [2.5 + a1, 0.4, 2.5 - a1, 0.4], legs: [0.1, 0, -0.1, 0] };
      var poseD2 = { lean: 0, arms: [2.5 - a1, 0.4, 2.5 + a1, 0.4], legs: [-0.1, 0, 0.1, 0] };
      c.save(); c.globalAlpha = Lt.up;
      K.person(c, L.cx - L.ww * 0.2, L.yb + L.H * 0.08, L.H * 0.16, poseD1, dcrew[0]);
      K.person(c, L.cx + L.ww * 0.2, L.yb + L.H * 0.08, L.H * 0.16, poseD2, dcrew[1]);
      c.restore();
    }
    
    // Khom loi release building up over the loop
    if (Lt.alt < 5 && K.khomLoi) {
      var tu = (t % 18000) / 18000;
      var nKhom = Math.floor(tu * 8);
      K.khomLoi(S, nKhom);
    }
  }
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: E.wall[2], y1: S.H });
}

var MATH_LINE = 'y = v₀t − ½gt²<br>y′ = 2y<sub>w</sub> − y';
D.addScene('moat', draw, /\bmoat\b|คูเมือง|แจ่ง|old city corner/i, MATH_LINE);
/* an event by the moat: within ~600 m of a gate or corner, or inside the old city's square */
D.near.push(['moat', function (e) {
  if (e.la == null || e.lo == null) return false;
  if (e.la >= 18.7815 && e.la <= 18.7955 && e.lo >= 98.978 && e.lo <= 98.9935) return true;
  return nearest(e.la, e.lo).m <= 600;
}]);
/* each gate and corner is its own doodle */
D.variants.moat = function (e) { return e.la != null ? nearest(e.la, e.lo).p.k : ''; };
D.versions = D.versions || {};
D.versions['moat:tha-phae-gate'] = 2; // added Lanna fon lep dancers, tung flags, and a khom loi release
window.MDDOODLER_MOAT = { places: PLACES.map(function (p) { return { k: p.k, th: p.th, en: p.en, lat: p.lat, lng: p.lng, kind: p.kind, look: p.look }; }), nearest: nearest };
})();
