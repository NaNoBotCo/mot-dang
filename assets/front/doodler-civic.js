/* Civic portraits for the auto-doodler: the schools, halls, markets, clinics, gyms, parks and
   campuses of the north, each drawn from one place's own facts (Nan, 2026-10-02: "utilize the
   doodler to avoid filler"). The seed (a hash of the place id) deals the building, colours,
   people, props, plants, vehicles and animals; the facts steer it (sub, levels, facility,
   specialty, brand, the words in the name); the reader's clock picks what is going on (the
   flag at eight, aerobics at dusk) and the hours say whether the shutters are up.
   'school' 'community' 'freshmarket' 'clinic' 'training' 'gym' 'hospital' 'park' 'university'
   'healthstation' 'dentist' 'tattoo' 'optician' (portraits), 'weights' (portraits and events).
   The still parts are cut once per size, seed and state into an offscreen layer; each frame
   draws what moves. D.civic hands the shopfront frame and the street's things to the craft and
   Akha files, whose massage, muaythai, cooking, elephants and akha scenes draw one place with it. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, jag = K.jag, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU, person = K.person, POSE = K.POSE;
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function pick(r, a) { return a[Math.floor(r() * a.length) % a.length]; }

/* ---------------------------------------------------------------- facts and state */
function placeOf(S) { return S.place || { name: '', nameTh: '', sub: [] }; }
function words(P) {
  return [P.name, P.nameTh, P.nameEn, P.brand, (P.sub || []).join(' '), P.facility, [].concat(P.specialty || []).join(' '), [].concat(P.services || []).join(' '), P.levels].join(' ');
}
function has(P, re) { return re.test(words(P)); }
function subOf(P, s) { return (P.sub || []).indexOf(s) >= 0; }
/* Bangkok hour and weekday from the reader's clock */
function clock(S) { var b = new Date((S.now || Date.now()) + 7 * 3600e3); return { h: b.getUTCHours() + b.getUTCMinutes() / 60, dow: b.getUTCDay() }; }
/* open (people at work, shutters up), lit (lights on at night), shut (shutters down), quiet (unknown hours, night) */
function stateOf(S, P) {
  var o = K.openNow(P.hours, S.now);
  if (o === true) return { open: true, lit: S.night, shut: false, quiet: false, known: true };
  if (o === false) return { open: false, lit: false, shut: true, quiet: true, known: true };
  return { open: !S.night, lit: false, shut: false, quiet: S.night, known: false };
}
/* inside what: a mall, a market, a campus, a hospital, or nothing */
function insideOf(P) {
  var i = P.inside || ''; if (!i) return '';
  if (/เซ็นทรัล|central|plaza|พลาซ่า|mall|ศูนย์การค้า|lotus|โลตัส|big ?c|บิ๊กซี|maya|เมญ่า|กาดสวนแก้ว|airport|สนามบิน|center|เซ็นเตอร์/i.test(i)) return 'mall';
  if (/ตลาด|กาด|market/i.test(i)) return 'market';
  if (/มหาวิทยาลัย|university|วิทยาลัย|college/i.test(i)) return 'campus';
  if (/โรงพยาบาล|hospital/i.test(i)) return 'hospital';
  return 'mall';
}

/* ---------------------------------------------------------------- colour */
function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
/* night: the colour times f, a little bluer */
function shade(h, f) { var v = rgb(h); return 'rgb(' + Math.round(v[0] * f) + ',' + Math.round(v[1] * f) + ',' + Math.round(Math.min(255, v[2] * f * 1.15 + 6)) + ')'; }
function nt(S, h) { return S.night ? shade(h, 0.48) : h; }
function alpha(h, a) { var v = rgb(h); return 'rgba(' + v[0] + ',' + v[1] + ',' + v[2] + ',' + a + ')'; }
var WALL = ['#f2e6c9', '#e9d3a8', '#cfe0d6', '#f0d0b8', '#d8e4ee', '#f4ecd8', '#e6c9a8', '#c9d8b8', '#f2d6d6', '#e0d4ec', '#f6e3a6', '#bcd6d2'];
var ROOF = ['#a8432f', '#b85a2a', '#2f6f6a', '#3a5a8a', '#7a3a5a', '#8a6a3a', '#4a6a3a', '#c06a3a'];
var TRIM = ['#2f6f6a', '#a8432f', '#3a5a8a', '#6a3a1e', '#2a2a30', '#7a3a5a', '#c0392b', '#2f8f5b'];

/* ---------------------------------------------------------------- the still layer, cut once
   keyed by the canvas transform (size and DPR), the stage, the seed and the state */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : { a: 1, d: 1, e: 0, f: 0 }, k = key + '|' + [S.W, S.H, Math.round(S.x0), Math.round(S.x1), Math.round(S.deck), Math.round(S.hh * 10), S.seed, S.night ? 1 : 0, S.phone ? 1 : 0, m.a, m.d, m.e, m.f].join(','), e = null;
  for (var i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    if (typeof document === 'undefined') { draw(c); return { out: null }; }
    var cv = document.createElement('canvas'); cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    var c0 = S.c; S.c = q; var out = draw(q); S.c = c0;
    e = { k: k, cv: cv, ox: ox, oy: oy, out: out };
    CACHE.unshift(e); if (CACHE.length > 28) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
  return e;
}
function stageBox(S) { return [S.x0 - 6, S.deck - S.hh * 2.6, S.span + 12, S.H - S.deck + S.hh * 2.6 + 4]; }

/* ---------------------------------------------------------------- small cuts */
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
function fp(c, pts, col) { c.fillStyle = col; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.fill(); }
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function dot(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
function el(c, x, y, rx, ry, a, col) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), a || 0, 0, TAU); c.fill(); }
function txt(c, s, x, y, px, col, w, al) { c.font = (w || 700) + ' ' + Math.round(px) + 'px "Sarabun",system-ui,sans-serif'; c.fillStyle = col; c.textAlign = al || 'center'; c.textBaseline = 'middle'; c.fillText(s, x, y); }
function glow(c, x, y, r, rgbs, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, 'rgba(' + rgbs + ',' + a + ')'); g.addColorStop(1, 'rgba(' + rgbs + ',0)'); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); }

/* ---------------------------------------------------------------- the ground: a street, a village lane, a lawn */
function street(c, S, kind, r) {
  var hh = S.hh, y = S.deck, H = S.H;
  if (kind === 'lane') {   /* a village lane: packed earth, grass at its edges */
    paper(c, rect(S.x0 - 6, y, S.span + 12, H - y + 6), nt(S, '#a88a5e'), 1.4);
    c.fillStyle = nt(S, '#6f9a4a'); for (var x = S.x0; x < S.x1; x += hh * 0.18) { var g = (x * 7 + S.seed) % 5; if (g < 2) continue; fp(c, [[x, y + 3], [x + 2, y - hh * 0.06], [x + 4, y + 3]], c.fillStyle); }
    return;
  }
  if (kind === 'lawn') {
    paper(c, rect(S.x0 - 6, y, S.span + 12, H - y + 6), nt(S, '#6f9a4a'), 1.4);
    paper(c, rect(S.x0 - 6, y + (H - y) * 0.45, S.span + 12, (H - y) * 0.3), nt(S, '#d8c8a0'), 0.6);
    return;
  }
  /* a city street: the pavement, the kerb painted in bands, the asphalt and its dashes */
  var pv = y + Math.min(hh * 0.26, (H - y) * 0.36);
  paper(c, rect(S.x0 - 6, y, S.span + 12, pv - y + 2), nt(S, kind === 'tile' ? '#d9c9a8' : '#c8bca8'), 1.2);
  c.strokeStyle = S.night ? 'rgba(0,0,0,.25)' : 'rgba(90,70,50,.2)'; c.lineWidth = 1; c.beginPath();
  for (x = S.x0 - (S.seed % 9); x < S.x1; x += hh * 0.22) { c.moveTo(x, y + 1); c.lineTo(x - 3, pv); } c.stroke();
  var kb = ['#f2f2f2', '#d9342b'], kk = (S.seed >>> 3) % 3; if (kk === 1) kb = ['#f2f2f2', '#e8b84a'];
  for (x = S.x0 - 6, i = 0; x < S.x1 + 6; x += hh * 0.24, i++) fr(c, x, pv, hh * 0.24, 3, nt(S, kk === 2 ? '#bdb5a5' : kb[i % 2]));
  fr(c, S.x0 - 6, pv + 3, S.span + 12, H - pv, nt(S, '#5a5a62'));
  var my = pv + 3 + (H - pv) * 0.55; c.fillStyle = nt(S, '#f2f2f2'); for (x = S.x0 + (S.seed % 23); x < S.x1; x += hh * 0.7) c.fillRect(x, my, hh * 0.32, 2);
  var i;
}
/* a plate on a post with the street's name, blue and white as the city's are */
function roadPlate(c, S, x, road) {
  if (!road) return null;
  var hh = S.hh, s = /^(ถนน|ถ\.|ซอย|ซ\.|ทาง|แยก|soi|road|rd|street)/i.test(road) ? road : 'ถ.' + road;
  if (s.length > 22) s = s.slice(0, 21) + '…';
  c.font = '700 ' + Math.round(Math.max(9, hh * 0.12)) + 'px "Sarabun",system-ui,sans-serif';
  var w = c.measureText(s).width + hh * 0.18, h = Math.max(13, hh * 0.19), top = S.deck - hh * 1.25;
  fr(c, x - 1.5, top, 3, S.deck - top + 2, nt(S, '#8a8a92'));
  paper(c, rect(x - w / 2, top - h, w, h), nt(S, '#1f4fa0'), 0.8);
  c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 1; c.strokeRect(x - w / 2 + 2, top - h + 2, w - 4, h - 4);
  txt(c, s, x, top - h / 2 + 0.5, Math.max(9, hh * 0.12), '#fff', 700);
  return [x - w / 2, x + w / 2];
}

/* ---------------------------------------------------------------- the north's touches */
/* a san phra phum on its post: the little house, gilt roof tips, offerings (a red soda with
   its straw, marigolds, figures); returns where the incense stands */
function spiritHouse(c, S, x, s, kind) {
  var y = S.deck + s * 0.04, post = s * 0.82, pw = s * 0.36, gold = S.night ? '#b8872f' : '#e8b84a';
  var body = kind === 1 ? '#f2ece0' : kind === 2 ? '#7a4a2a' : '#c0392b', roof = kind === 2 ? '#6a3a1e' : kind === 1 ? '#c0392b' : '#2f6f6a';
  paper(c, rect(x - s * 0.04, y - post, s * 0.08, post), nt(S, kind === 2 ? '#7a4a2a' : '#f2ece0'), 1);
  paper(c, rect(x - pw / 2, y - post - s * 0.04, pw, s * 0.04), nt(S, gold), 0.8);
  var bw = s * 0.2, bh = s * 0.16, by = y - post - s * 0.04 - bh;
  paper(c, rect(x - bw / 2, by, bw, bh), nt(S, body), 0.8);
  fr(c, x - bw * 0.18, by + bh * 0.3, bw * 0.36, bh * 0.7, nt(S, '#3a2416'));
  [0, 1].forEach(function (k) {
    var ry = by - k * s * 0.08, rw = bw * (0.8 - k * 0.22);
    fp(c, [[x - rw, ry], [x, ry - s * 0.12], [x + rw, ry]], nt(S, roof));
    ln(c, [[x - rw, ry], [x, ry - s * 0.12], [x + rw, ry]], nt(S, gold), 1.2);
    ln(c, [[x - rw, ry], [x - rw - s * 0.03, ry - s * 0.04]], nt(S, gold), 1.2); ln(c, [[x + rw, ry], [x + rw + s * 0.03, ry - s * 0.04]], nt(S, gold), 1.2);
  });
  ln(c, [[x, by - s * 0.2], [x, by - s * 0.27]], nt(S, gold), 1.4);
  /* offerings on the ledge */
  var ly = y - post - s * 0.04;
  fr(c, x - pw * 0.42, ly - s * 0.07, s * 0.025, s * 0.07, '#d9342b'); ln(c, [[x - pw * 0.41, ly - s * 0.07], [x - pw * 0.36, ly - s * 0.11]], '#f2f2f2', 1);
  for (var k = 0; k < 7; k++) dot(c, x - bw * 0.55 + k * bw * 0.18, by + bh * 0.08 + Math.sin(k / 6 * Math.PI) * s * 0.03, Math.max(1, s * 0.016), k % 2 ? '#f29a1f' : '#f7d24a');
  dot(c, x + pw * 0.3, ly - s * 0.025, s * 0.022, nt(S, '#f2ece0')); dot(c, x + pw * 0.38, ly - s * 0.02, s * 0.018, nt(S, '#c9a36a'));
  return [x + pw * 0.15, ly];
}
/* incense: sticks and smoke curling, x = x₀ + A·sin(ky − ωt) */
function smoke(c, x, y, len, t, k) {
  ln(c, [[x, y], [x + 1, y - len * 0.25]], '#b5532f', 1); dot(c, x + 1, y - len * 0.25, 1.1, '#ff7a3a');
  c.strokeStyle = 'rgba(240,236,228,.5)'; c.lineWidth = 1; c.beginPath();
  for (var j = 0; j <= len; j += 3) { var xx = x + 1 + Math.sin(j * 0.12 - t / 650 + k) * (1 + j * 0.08); j ? c.lineTo(xx, y - len * 0.25 - j) : c.moveTo(xx, y - len * 0.25); } c.stroke();
}
/* marigolds strung on a catenary; khom lanterns hung along it */
function marigolds(c, S, xa, xb, y, sag) {
  K.strand(c, xa, xb, y, sag, Math.max(5, S.hh * 0.07), function (x, yy, i) { dot(c, x, yy + 2, Math.max(1.6, S.hh * 0.03), nt(S, i % 3 ? '#f29a1f' : '#f7c52c')); });
}
function khom(c, S, x, y, s, col, lit) {
  ln(c, [[x, y - s * 0.5], [x, y - s * 0.2]], 'rgba(40,20,30,.8)', 1);
  if (lit) glow(c, x, y + s * 0.15, s * 1.4, '255,170,80', 0.45);
  fp(c, [[x - s * 0.36, y - s * 0.2], [x + s * 0.36, y - s * 0.2], [x + s * 0.5, y + s * 0.15], [x + s * 0.36, y + s * 0.5], [x - s * 0.36, y + s * 0.5], [x - s * 0.5, y + s * 0.15]], lit ? '#ffb85a' : nt(S, col));
  ln(c, [[x - s * 0.5, y + s * 0.15], [x + s * 0.5, y + s * 0.15]], nt(S, '#e8b84a'), 1);
  ln(c, [[x, y + s * 0.5], [x, y + s * 0.85]], nt(S, '#e8b84a'), 1);
}
/* the Thai flag, five bands 1:1:2:1:1, its cloth a travelling wave */
function thaiFlag(c, x, top, w, t, k, night) {
  var h = w * 0.66, N = 10, cols = ['#d9342b', '#f4f4f4', '#2a3a8a', '#2a3a8a', '#f4f4f4', '#d9342b'];
  for (var b = 0; b < 6; b++) {
    c.fillStyle = night ? shade(cols[b], 0.6) : cols[b]; c.beginPath();
    for (var i = 0; i <= N; i++) { var u = i / N, dy = Math.sin(u * 4 - t / 300 + k) * u * h * 0.12; c.lineTo(x + u * w, top + dy + h * b / 6); }
    for (i = N; i >= 0; i--) { u = i / N; dy = Math.sin(u * 4 - t / 300 + k) * u * h * 0.12; c.lineTo(x + u * w, top + dy + h * (b + 1) / 6 + 0.4); }
    c.closePath(); c.fill();
  }
}
/* a moth round the lamp on a figure eight, x = a·sin ωt, y = b·sin 2ωt */
function moth(c, x, y, s, t, k) {
  var a = t / 700 + k, mx = x + Math.sin(a) * s * 0.35, my = y + Math.sin(2 * a) * s * 0.14, f = Math.abs(Math.sin(t / 40));
  c.fillStyle = 'rgba(240,230,200,.9)'; c.beginPath(); c.ellipse(mx - 2, my, 2.6, 1 + 1.6 * f, 0.5, 0, TAU); c.ellipse(mx + 2, my, 2.6, 1 + 1.6 * f, -0.5, 0, TAU); c.fill();
}
function bulb(c, S, x, y, s, on) {
  ln(c, [[x, y - s * 0.3], [x, y]], 'rgba(30,20,20,.8)', 1);
  if (on) glow(c, x, y + s * 0.06, s * 0.7, '255,226,150', 0.55);
  el(c, x, y + s * 0.06, s * 0.06, s * 0.08, 0, on ? '#fff3c4' : nt(S, '#d8d0b8'));
}

/* the place's name on its board (K.sign), kept clear of the tung at the stage's ends */
function signW(c, P, sh) {
  var th = P.nameTh || P.name || '', en = P.nameEn && P.nameEn !== th ? P.nameEn : '';
  c.save(); c.font = '800 ' + Math.round(Math.max(11, sh * 0.19)) + 'px "Sarabun",system-ui,sans-serif'; var w1 = c.measureText(th).width;
  c.font = '700 ' + Math.round(Math.max(9, sh * 0.13)) + 'px "Sarabun",system-ui,sans-serif'; var w2 = en ? c.measureText(en).width : 0; c.restore();
  return Math.min(Math.max(w1, w2) + sh * 0.5, sh * 7);
}
function signAt(c, S, cx, y, P, sh, col, lit) {
  if (!(P.nameTh || P.name)) return null;
  sh = Math.min(sh, (S.span - S.hh * 1.7) / 7); var w = signW(c, P, sh), lo = S.x0 + S.hh * 0.75 + w / 2, hi = S.x1 - S.hh * 0.85 - w / 2;
  return K.sign(c, lo > hi ? (S.x0 + S.x1) / 2 : clamp(cx, lo, hi), y, P, sh, col, lit);
}

/* ---------------------------------------------------------------- plants */
function bougainvillea(c, S, x, y, s, k) {
  var cols = [['#e5468f', '#c2307a'], ['#f08a3a', '#e05a2a'], ['#f2f2f2', '#e5c8d8'], ['#b04ac9', '#8a2fa8']][k % 4];
  paper(c, function (q) { circ(q, x, y - s * 0.28, s * 0.3, k + 3); }, nt(S, '#3f6f32'), 0.8);
  for (var i = 0; i < 26; i++) { var a = i * 2.4, rr = s * 0.29 * Math.sqrt(i / 26); dot(c, x + Math.cos(a) * rr, y - s * 0.3 + Math.sin(a) * rr * 0.85, s * 0.04, nt(S, cols[i % 2])); }
}
function banana(c, S, x, y, s, k) {
  var g = nt(S, '#5a9a3a'), g2 = nt(S, '#4a8a32');
  paper(c, rect(x - s * 0.05, y - s * 0.75, s * 0.1, s * 0.75), nt(S, '#8a9a5a'), 0.8);
  for (var i = 0; i < 6; i++) {
    var a = -Math.PI / 2 + (i - 2.5) * 0.48 + (k % 3) * 0.05, L = s * (0.55 + (i % 2) * 0.12), x1 = x + Math.cos(a) * L, y1 = y - s * 0.75 + Math.sin(a) * L * 0.8 + (Math.abs(i - 2.5) > 1.5 ? s * 0.2 : 0);
    c.fillStyle = i % 2 ? g : g2; c.beginPath(); c.moveTo(x, y - s * 0.75);
    c.quadraticCurveTo((x + x1) / 2 - s * 0.12, (y - s * 0.75 + y1) / 2 - s * 0.14, x1, y1); c.quadraticCurveTo((x + x1) / 2 + s * 0.08, (y - s * 0.75 + y1) / 2 + s * 0.06, x, y - s * 0.72); c.fill();
  }
}
function frangipani(c, S, x, y, s, k) {
  c.strokeStyle = nt(S, '#8a8478'); c.lineCap = 'round';
  var tips = [];
  (function br(x0, y0, a, L, d) { var x1 = x0 + Math.cos(a) * L, y1 = y0 + Math.sin(a) * L; c.lineWidth = Math.max(1.5, s * 0.05 * (1 - d * 0.25)); c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
    if (d < 2) { br(x1, y1, a - 0.5, L * 0.72, d + 1); br(x1, y1, a + 0.45, L * 0.7, d + 1); } else tips.push([x1, y1]); })(x, y, -Math.PI / 2 + (k % 3 - 1) * 0.1, s * 0.42, 0);
  tips.forEach(function (p, i) {
    for (var l = 0; l < 5; l++) el(c, p[0] + Math.cos(l * 1.26) * s * 0.07, p[1] + Math.sin(l * 1.26) * s * 0.04, s * 0.06, s * 0.022, l * 1.26, nt(S, '#3f7a32'));
    for (l = 0; l < 3; l++) { var fx = p[0] + (l - 1) * s * 0.035, fy = p[1] - s * 0.03 - (l % 2) * s * 0.02; for (var pt = 0; pt < 5; pt++) el(c, fx + Math.cos(pt * 1.256) * s * 0.014, fy + Math.sin(pt * 1.256) * s * 0.014, s * 0.016, s * 0.008, pt * 1.256, nt(S, k % 2 ? '#fdf6e6' : '#ffd6e0')); dot(c, fx, fy, s * 0.008, '#f7c52c'); }
  });
}
function chilliPots(c, S, x, y, s, n) {
  for (var i = 0; i < n; i++) { var px = x + i * s * 0.2;
    fp(c, [[px - s * 0.07, y - s * 0.12], [px + s * 0.07, y - s * 0.12], [px + s * 0.05, y], [px - s * 0.05, y]], nt(S, '#b8683a'));
    paper(c, function (q) { circ(q, px, y - s * 0.2, s * 0.085, i + 11); }, nt(S, '#4a8a32'), 0.5);
    for (var k = 0; k < 4; k++) el(c, px + (k - 1.5) * s * 0.035, y - s * 0.18 + (k % 2) * s * 0.03, s * 0.01, s * 0.028, 0.3, nt(S, '#d9342b')); }
}
/* a rain tree: the wide umbrella crown of the city's old roads */
function rainTree(c, S, x, y, s, k) {
  paper(c, poly([[x - s * 0.08, y], [x - s * 0.05, y - s * 0.9], [x - s * 0.3, y - s * 1.2], [x - s * 0.24, y - s * 1.24], [x, y - s * 1.0], [x + s * 0.26, y - s * 1.26], [x + s * 0.32, y - s * 1.2], [x + s * 0.06, y - s * 0.9], [x + s * 0.09, y]]), nt(S, '#5a4636'), 1);
  paper(c, function (q) { var pts = []; for (var i = 0; i <= 40; i++) { var a = Math.PI + i / 40 * Math.PI, rr = s * (0.95 + 0.08 * Math.sin(i * 1.7 + k)); pts.push([x + Math.cos(a) * rr * 1.05, y - s * 1.2 + Math.sin(a) * rr * 0.55]); } pts.push([x + s * 0.9, y - s * 1.12], [x - s * 0.9, y - s * 1.12]); jag(q, pts, 40 + k, 3); }, nt(S, k % 2 ? '#3f7a3a' : '#4a8040'), 1.4);
}
function shrub(c, S, x, y, s, k) { paper(c, function (q) { circ(q, x, y - s * 0.16, s * 0.2, k + 21); }, nt(S, ['#3f7a3a', '#4f8a3a', '#2f6a3a'][k % 3]), 0.6); }

/* ---------------------------------------------------------------- vehicles and animals */
function motorbike(c, S, x, y, s, dir, col, side) {
  var w = s * 0.13, b = nt(S, col);
  [[-0.32, 0], [0.3, 0]].forEach(function (p) { dot(c, x + dir * p[0] * s, y - w, w, '#1e1e24'); dot(c, x + dir * p[0] * s, y - w, w * 0.45, nt(S, '#9a9aa2')); });
  fp(c, [[x - dir * s * 0.38, y - s * 0.24], [x - dir * s * 0.05, y - s * 0.22], [x + dir * s * 0.12, y - s * 0.12], [x + dir * s * 0.26, y - s * 0.38], [x + dir * s * 0.33, y - s * 0.36], [x + dir * s * 0.22, y - s * 0.1], [x - dir * s * 0.3, y - s * 0.1]], b);
  fr(c, Math.min(x - dir * s * 0.34, x - dir * s * 0.06), y - s * 0.29, s * 0.28, s * 0.06, '#26262c');
  ln(c, [[x + dir * s * 0.26, y - s * 0.38], [x + dir * s * 0.18, y - s * 0.48], [x + dir * s * 0.3, y - s * 0.5]], '#2a2a30', Math.max(1.4, s * 0.025));
  if (S.night) dot(c, x + dir * s * 0.34, y - s * 0.36, s * 0.025, '#fff3c4');
  if (side) { fp(c, [[x - dir * s * 0.3, y - s * 0.1], [x - dir * s * 1.05, y - s * 0.1], [x - dir * s * 1.08, y - s * 0.34], [x - dir * s * 0.32, y - s * 0.34]], nt(S, '#4a6a8a')); dot(c, x - dir * s * 0.82, y - w, w, '#1e1e24'); }
}
function bicycle(c, S, x, y, s, dir, col) {
  var w = s * 0.15; c.lineWidth = Math.max(1, s * 0.02); c.strokeStyle = '#2a2a30';
  [-0.28, 0.28].forEach(function (p) { c.beginPath(); c.arc(x + dir * p * s, y - w, w, 0, TAU); c.stroke(); });
  ln(c, [[x - dir * s * 0.28, y - w], [x - dir * s * 0.02, y - w], [x + dir * s * 0.18, y - s * 0.34], [x - dir * s * 0.1, y - s * 0.34], [x - dir * s * 0.02, y - w]], nt(S, col), Math.max(1.4, s * 0.03));
  ln(c, [[x + dir * s * 0.28, y - w], [x + dir * s * 0.18, y - s * 0.4], [x + dir * s * 0.26, y - s * 0.42]], nt(S, col), Math.max(1.4, s * 0.03));
  fr(c, x + dir * s * 0.2 - s * 0.06, y - s * 0.46, s * 0.12, s * 0.08, nt(S, '#c9a36a'));
}
function songthaew(c, S, x, y, s, dir, col) {
  var L = s * 1.5, b = nt(S, col);
  paper(c, poly([[x - L / 2, y - s * 0.16], [x + L / 2, y - s * 0.16], [x + L / 2, y - s * 0.42], [x + dir * L * 0.36, y - s * 0.44], [x + dir * L * 0.3, y - s * 0.68], [x - L / 2, y - s * 0.7]]), b, 1);
  fr(c, x - L / 2 + s * 0.06, y - s * 0.62, L * 0.62, s * 0.2, nt(S, '#3a3a44'));
  for (var i = 0; i < 4; i++) fr(c, x - L / 2 + s * 0.08 + i * L * 0.15, y - s * 0.6, 2, s * 0.17, b);
  fp(c, [[x + dir * L * 0.33, y - s * 0.44], [x + dir * L * 0.36, y - s * 0.62], [x + dir * L * 0.44, y - s * 0.44]].map(function (p) { return p; }), nt(S, '#9fc6d8'));
  [[-0.32], [0.3]].forEach(function (p) { dot(c, x + p[0] * L, y - s * 0.12, s * 0.13, '#1e1e24'); dot(c, x + p[0] * L, y - s * 0.12, s * 0.055, nt(S, '#9a9aa2')); });
  if (S.night) dot(c, x + dir * L * 0.5, y - s * 0.3, s * 0.04, '#fff3c4');
}
var DOGS = ['#c99a5a', '#2a2420', '#e8dcc0', '#8a5a3a', '#b88a4a'];
/* a soi dog: asleep and breathing (the curl swells with sin ωt), or sitting with its tail going */
function dog(c, S, x, y, s, k, asleep, t) {
  var col = nt(S, DOGS[k % DOGS.length]), br = 1 + 0.04 * Math.sin(t / 900 + k);
  if (asleep) {
    el(c, x, y - s * 0.1 * br, s * 0.3, s * 0.12 * br, 0, col);
    el(c, x + s * 0.26, y - s * 0.07, s * 0.1, s * 0.075, 0.2, col);
    el(c, x + s * 0.24, y - s * 0.11, s * 0.04, s * 0.06, -0.6, nt(S, '#5a3a2a'));
    ln(c, [[x - s * 0.28, y - s * 0.05], [x - s * 0.1, y - s * 0.01], [x + s * 0.1, y - s * 0.02]], col, Math.max(1.5, s * 0.04));
    var u = (t / 2200 + k * 0.3) % 1; c.globalAlpha = Math.sin(Math.PI * u); txt(c, 'z', x + s * 0.32 + u * s * 0.15, y - s * 0.24 - u * s * 0.3, s * (0.12 + u * 0.08), S.night ? '#e8e0c8' : '#4a3a2a', 700); c.globalAlpha = 1;
    return;
  }
  var wag = Math.sin(t / 120 + k) * 0.5;
  ln(c, [[x - s * 0.18, y - s * 0.16], [x - s * 0.18 - Math.cos(0.9 + wag) * s * 0.18, y - s * 0.16 - Math.sin(0.9 + wag) * s * 0.18]], col, Math.max(1.5, s * 0.04));
  el(c, x - s * 0.05, y - s * 0.16, s * 0.17, s * 0.12, -0.4, col);
  fr(c, x + s * 0.02, y - s * 0.2, s * 0.05, s * 0.2, col); fr(c, x - s * 0.18, y - s * 0.08, s * 0.12, s * 0.08, col);
  el(c, x + s * 0.08, y - s * 0.34, s * 0.09, s * 0.08, 0, col); el(c, x + s * 0.16, y - s * 0.32, s * 0.06, s * 0.04, 0, col);
  fp(c, [[x + s * 0.03, y - s * 0.4], [x + s * 0.06, y - s * 0.5], [x + s * 0.1, y - s * 0.4]], nt(S, '#5a3a2a'));
  dot(c, x + s * 0.12, y - s * 0.35, Math.max(0.8, s * 0.012), '#111');
}
function cat(c, S, x, y, s, k, t) {
  var col = nt(S, ['#e8a050', '#2a2420', '#f2ece0', '#8a8a92'][k % 4]), sw = Math.sin(t / 700 + k);
  c.strokeStyle = col; c.lineWidth = Math.max(1.5, s * 0.035); c.lineCap = 'round'; c.beginPath(); c.moveTo(x - s * 0.1, y - s * 0.04); c.quadraticCurveTo(x - s * 0.3, y - s * 0.05, x - s * 0.28 + sw * s * 0.05, y - s * 0.22); c.stroke();
  el(c, x, y - s * 0.1, s * 0.12, s * 0.1, 0, col); el(c, x + s * 0.06, y - s * 0.24, s * 0.07, s * 0.065, 0, col);
  fp(c, [[x + s * 0.01, y - s * 0.28], [x + s * 0.02, y - s * 0.36], [x + s * 0.06, y - s * 0.3]], col); fp(c, [[x + s * 0.07, y - s * 0.3], [x + s * 0.11, y - s * 0.36], [x + s * 0.12, y - s * 0.27]], col);
}
/* chickens about a village: the head dips to peck, |sin ωt| */
function chicken(c, S, x, y, s, k, t) {
  var pk = Math.pow(Math.max(0, Math.sin(t / 380 + k * 1.9)), 4), dir = k % 2 ? 1 : -1, col = nt(S, ['#c0682a', '#f2ece0', '#2a2420', '#a8432f'][k % 4]);
  fp(c, [[x - dir * s * 0.16, y - s * 0.16], [x - dir * s * 0.24, y - s * 0.32], [x - dir * s * 0.08, y - s * 0.2]], nt(S, '#2a3a2a'));
  el(c, x, y - s * 0.14, s * 0.15, s * 0.1, 0, col);
  var hx = x + dir * s * (0.14 + pk * 0.06), hy = y - s * (0.26 - pk * 0.2);
  ln(c, [[x + dir * s * 0.08, y - s * 0.18], [hx, hy]], col, Math.max(2, s * 0.06)); dot(c, hx, hy, s * 0.05, col);
  dot(c, hx, hy - s * 0.05, s * 0.025, '#d9342b'); fp(c, [[hx + dir * s * 0.04, hy - s * 0.01], [hx + dir * s * 0.09, hy + s * 0.01], [hx + dir * s * 0.04, hy + s * 0.025]], '#e8b84a');
  ln(c, [[x - s * 0.03, y - s * 0.05], [x - s * 0.04, y]], '#e8b84a', 1); ln(c, [[x + s * 0.03, y - s * 0.05], [x + s * 0.04, y]], '#e8b84a', 1);
}

/* ---------------------------------------------------------------- buildings */
/* the roll-up shutter of a Thai shophouse: ribs every few pixels, the box above, a padlock */
function shutter(c, S, x0, x1, y0, y1, col, down) {
  var bx = S.hh * 0.09;
  fr(c, x0 - 2, y0 - bx, x1 - x0 + 4, bx, nt(S, '#8a8a92'));
  if (!down) return;
  fr(c, x0, y0, x1 - x0, y1 - y0, nt(S, col));
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; c.beginPath(); for (var y = y0 + 3; y < y1; y += 4) { c.moveTo(x0, y); c.lineTo(x1, y); } c.stroke();
  fr(c, x0, y1 - 4, x1 - x0, 4, nt(S, '#5a5a62')); dot(c, (x0 + x1) / 2, y1 - 6, 2, '#c9a36a');
}
/* a facade: the trade's front in one of several bodies the seed deals. kind: 'shop' (a concrete
   shophouse of 2–4 storeys), 'teak' (a teak house on posts, the trade beneath it), 'row' (a
   one-storey concrete row under tin), 'glass' (a modern glass box), 'gov' (a government block
   with its veranda and hipped roof). Returns the door (the open front) and where the sign hangs. */
function facade(c, S, f) {
  var hh = S.hh, x0 = f.x0, x1 = f.x1, w = x1 - x0, y = S.deck, wall = nt(S, f.wall), trim = nt(S, f.trim), roof = nt(S, f.roof), out = { x0: x0, x1: x1 };
  var lit = f.lit, win = lit ? '#ffd98a' : S.night ? '#2a2f48' : '#9fc6d8';
  if (f.kind === 'shop') {
    var gf = f.gf || hh * 1.2, fl = clamp((f.floors || 2) - 1, 1, 2), fh = Math.min(hh * 0.6, (hh * 2.22 - gf) / fl), top = y - gf - fl * fh;
    paper(c, rect(x0, top, w, y - top), wall, 1.6);
    fr(c, x0 - hh * 0.04, top - hh * 0.06, w + hh * 0.08, hh * 0.08, trim);
    var nb = Math.max(1, Math.round(w / (hh * 1.25))), bw = w / nb;
    for (var fi = 0; fi < fl; fi++) {
      var fy = top + fi * fh;
      fr(c, x0, fy + fh - 3, w, 3, alpha('#000000', 0.12));
      for (var b = 0; b < nb; b++) {
        var wx = x0 + b * bw + bw * 0.14, ww = bw * 0.72, wy = fy + fh * 0.18, wh = fh * 0.6;
        fr(c, wx - 2, wy - 2, ww + 4, wh + 4, trim); fr(c, wx, wy, ww, wh, (lit && (b + fi + S.seed) % 3) ? '#ffd98a' : win);
        c.strokeStyle = trim; c.lineWidth = 1.2; c.beginPath(); for (var m = 1; m < 3; m++) { c.moveTo(wx + ww * m / 3, wy); c.lineTo(wx + ww * m / 3, wy + wh); } c.stroke();
        if ((b + fi + f.seed) % 3 === 0) { ln(c, [[wx - 4, wy + wh + 2], [wx + ww + 4, wy + wh + 2]], nt(S, '#5a5a62'), 2); for (var rl = 0; rl < 6; rl++) ln(c, [[wx - 2 + rl * (ww + 4) / 5, wy + wh + 2], [wx - 2 + rl * (ww + 4) / 5, wy + wh - fh * 0.18]], nt(S, '#5a5a62'), 1); chilliPots(c, S, wx + ww * 0.15, wy + wh, hh * 0.45, 2); }
        if ((b * 3 + fi + f.seed) % 4 === 1) { fr(c, wx + ww + 3, wy + wh * 0.4, hh * 0.18, hh * 0.13, nt(S, '#e8e8e8')); c.strokeStyle = nt(S, '#9a9aa2'); c.beginPath(); c.arc(wx + ww + 3 + hh * 0.09, wy + wh * 0.4 + hh * 0.065, hh * 0.045, 0, TAU); c.stroke(); }
      }
    }
    fr(c, x0, y - gf, w, hh * 0.16, trim);
    out.top = top; out.signY = y - gf; out.door = { x0: x0 + hh * 0.08, x1: x1 - hh * 0.08, y0: y - gf + hh * 0.16 };
    return out;
  }
  if (f.kind === 'teak') {
    var fl2 = y - hh * 1.14, top2 = y - hh * 2.22, wood = nt(S, '#7a4a2a'), dark = nt(S, '#5a3420');
    for (var p = 0; p < 4; p++) paper(c, rect(x0 + w * (0.04 + p * 0.3) - 3, fl2, 6, y - fl2), dark, 0.8);
    paper(c, rect(x0 - hh * 0.04, fl2 - hh * 0.06, w + hh * 0.08, hh * 0.08), wood, 1);
    paper(c, rect(x0 + w * 0.04, fl2 - hh * 0.5, w * 0.92, hh * 0.44), wood, 1.2);
    c.strokeStyle = 'rgba(0,0,0,.2)'; c.lineWidth = 1; c.beginPath(); for (var px = x0 + w * 0.04; px < x0 + w * 0.96; px += hh * 0.09) { c.moveTo(px, fl2 - hh * 0.5); c.lineTo(px, fl2 - hh * 0.06); } c.stroke();
    for (var wi = 0; wi < 3; wi++) { var wx2 = x0 + w * (0.16 + wi * 0.28); fr(c, wx2, fl2 - hh * 0.4, w * 0.12, hh * 0.24, lit ? '#ffd98a' : nt(S, '#3a2416')); fr(c, wx2 - 2, fl2 - hh * 0.42, w * 0.12 + 4, 3, nt(S, '#e8b84a')); }
    paper(c, poly([[x0 - w * 0.1, fl2 - hh * 0.42], [x0 + w * 0.22, top2 + hh * 0.12], [x0 + w * 0.78, top2 + hh * 0.12], [x0 + w * 1.1, fl2 - hh * 0.42]]), roof, 1.8);
    paper(c, poly([[x0 + w * 0.3, top2 + hh * 0.16], [x0 + w * 0.5, top2 - hh * 0.06], [x0 + w * 0.7, top2 + hh * 0.16]]), roof, 1.4);
    var kx = x0 + w * 0.5, ky = top2 - hh * 0.06, kl = hh * 0.22;
    c.save(); c.strokeStyle = nt(S, '#e8b84a'); c.lineWidth = 2.4; c.lineCap = 'round'; c.beginPath(); c.moveTo(kx, ky); c.quadraticCurveTo(kx - kl * 0.2, ky - kl * 0.8, kx - kl * 0.7, ky - kl * 1.1); c.moveTo(kx, ky); c.quadraticCurveTo(kx + kl * 0.2, ky - kl * 0.8, kx + kl * 0.7, ky - kl * 1.1); c.stroke(); c.restore();
    var sx = f.stairL ? x0 + w * 0.02 : x1 - w * 0.02; ln(c, [[sx, y], [sx + (f.stairL ? 1 : -1) * hh * 0.3, fl2]], wood, 3);
    out.top = top2 - kl; out.signY = fl2 - hh * 0.04; out.door = { x0: x0 + w * 0.06, x1: x1 - w * 0.06, y0: fl2 + hh * 0.04 }; out.under = true;
    return out;
  }
  if (f.kind === 'row') {
    var top3 = y - hh * 1.62;
    paper(c, rect(x0, top3 + hh * 0.12, w, y - top3 - hh * 0.12), wall, 1.4);
    paper(c, poly([[x0 - hh * 0.12, top3 + hh * 0.22], [x0 + hh * 0.05, top3], [x1 - hh * 0.05, top3], [x1 + hh * 0.12, top3 + hh * 0.22]]), roof, 1.4);
    c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; c.beginPath(); for (var rx = x0; rx < x1; rx += 5) { c.moveTo(rx, top3 + 2); c.lineTo(rx - 2, top3 + hh * 0.2); } c.stroke();
    out.top = top3; out.signY = top3 + hh * 0.2; out.door = { x0: x0 + hh * 0.1, x1: x1 - hh * 0.1, y0: top3 + hh * 0.46 };
    return out;
  }
  if (f.kind === 'glass') {
    var top4 = y - hh * (f.floors > 2 ? 2.2 : 1.85), g0 = y - hh * 1.3;
    paper(c, rect(x0, top4, w, y - top4), nt(S, '#e8ecef'), 1.6);
    fr(c, x0 + hh * 0.06, top4 + hh * 0.08, w - hh * 0.12, g0 - top4 - hh * 0.1, lit ? 'rgba(255,220,150,.85)' : S.night ? '#273049' : '#8fb8cc');
    c.strokeStyle = nt(S, '#6a7a86'); c.lineWidth = 1.5; c.beginPath();
    for (var gx = x0 + hh * 0.06; gx <= x1 - hh * 0.05; gx += (w - hh * 0.12) / Math.max(2, Math.round(w / (hh * 0.55)))) { c.moveTo(gx, top4 + hh * 0.08); c.lineTo(gx, g0 - hh * 0.02); }
    for (var gy = top4 + hh * 0.08; gy < g0 - hh * 0.05; gy += hh * 0.3) { c.moveTo(x0 + hh * 0.06, gy); c.lineTo(x1 - hh * 0.06, gy); } c.stroke();
    if (!S.night) fp(c, [[x0 + w * 0.15, top4 + hh * 0.08], [x0 + w * 0.3, top4 + hh * 0.08], [x0 + w * 0.22, g0 - hh * 0.02], [x0 + w * 0.07, g0 - hh * 0.02]], 'rgba(255,255,255,.25)');
    fr(c, x0 - hh * 0.05, g0, w + hh * 0.1, hh * 0.1, trim);
    out.top = top4; out.signY = g0; out.door = { x0: x0 + hh * 0.08, x1: x1 - hh * 0.08, y0: g0 + hh * 0.12 };
    return out;
  }
  /* 'gov': the government block: cream walls, a veranda corridor of square posts, a hipped tile roof */
  var floors = f.floors || 1, fh2 = hh * 0.66, g1 = f.gf || fh2, top5 = y - g1 - fh2 * (floors - 1) - hh * 0.06;
  paper(c, rect(x0, top5, w, y - top5), wall, 1.6);
  for (var fl3 = 0; fl3 < floors; fl3++) {
    var fhh = fl3 ? fh2 : g1, fy3 = fl3 ? y - g1 - fh2 * fl3 : y - g1;
    fr(c, x0, fy3 + fhh - hh * 0.06, w, hh * 0.06, trim);
    var nw = Math.max(2, Math.round(w / (hh * 0.5)));
    for (var k = 0; k < nw; k++) { var wx3 = x0 + (k + 0.2) * w / nw, ww3 = w / nw * 0.6;
      if (fl3 === 0 && f.doorAt != null && Math.abs(k - f.doorAt) < 0.5) { fr(c, wx3 - 2, fy3 + fhh * 0.15, ww3 + 4, fhh * 0.79, nt(S, '#3a2a20')); continue; }
      fr(c, wx3, fy3 + fh2 * 0.22, ww3, fh2 * 0.48, lit && (k + fl3) % 2 ? '#ffd98a' : win);
      c.strokeStyle = trim; c.lineWidth = 1; c.beginPath(); c.moveTo(wx3 + ww3 / 2, fy3 + fh2 * 0.22); c.lineTo(wx3 + ww3 / 2, fy3 + fh2 * 0.7); c.moveTo(wx3, fy3 + fh2 * 0.46); c.lineTo(wx3 + ww3, fy3 + fh2 * 0.46); c.stroke(); }
    if (fl3 > 0) { fr(c, x0, fy3 + fh2 * 0.62, w, 2, nt(S, '#f4f4f4')); for (var bl = x0; bl < x1; bl += hh * 0.1) fr(c, bl, fy3 + fh2 * 0.62, 1.5, fh2 * 0.32, nt(S, '#f4f4f4')); }
  }
  paper(c, poly([[x0 - hh * 0.18, top5 + hh * 0.08], [x0 + hh * 0.35, top5 - hh * 0.42], [x1 - hh * 0.35, top5 - hh * 0.42], [x1 + hh * 0.18, top5 + hh * 0.08]]), roof, 1.8);
  c.strokeStyle = 'rgba(0,0,0,.15)'; c.lineWidth = 1; c.beginPath(); for (var tx = x0; tx < x1; tx += hh * 0.12) { c.moveTo(tx, top5 + hh * 0.06); c.lineTo(lerp(tx, (x0 + x1) / 2, 0.12), top5 - hh * 0.38); } c.stroke();
  if (f.gable) { var gx2 = (x0 + x1) / 2; paper(c, poly([[gx2 - hh * 0.5, top5 - hh * 0.2], [gx2, top5 - hh * 0.62], [gx2 + hh * 0.5, top5 - hh * 0.2]]), roof, 1.4); fp(c, [[gx2 - hh * 0.36, top5 - hh * 0.22], [gx2, top5 - hh * 0.52], [gx2 + hh * 0.36, top5 - hh * 0.22]], wall); ln(c, [[gx2 - hh * 0.5, top5 - hh * 0.2], [gx2, top5 - hh * 0.62], [gx2 + hh * 0.5, top5 - hh * 0.2]], nt(S, '#e8b84a'), 1.4); }
  out.top = top5 - hh * 0.42; out.signY = y - g1 + hh * 0.02; out.door = { x0: x0, x1: x1, y0: y - g1 + hh * 0.1 };
  return out;
}
/* a neighbour cut lower and dimmer at the stage's edge, so the place reads as one of a street */
function neighbour(c, S, x0, x1, k) {
  var hh = S.hh, h = hh * (1.1 + ((S.seed >>> k) % 5) * 0.18), col = WALL[(S.seed + k * 5) % WALL.length];
  paper(c, rect(x0, S.deck - h, x1 - x0, h), nt(S, shade(col, 0.86).replace(/^rgb\((\d+),(\d+),(\d+)\)$/, function (m, a, b, d) { return '#' + [a, b, d].map(function (v) { return ('0' + (+v).toString(16)).slice(-2); }).join(''); })), 1.2);
  shutter(c, S, x0 + hh * 0.1, x1 - hh * 0.1, S.deck - hh * 0.7, S.deck, (k % 2) ? '#9aa6b0' : '#a8b8a0', true);
  for (var x = x0 + hh * 0.2; x < x1 - hh * 0.4; x += hh * 0.6) fr(c, x, S.deck - h + hh * 0.2, hh * 0.32, hh * 0.3, S.night ? ((x + k) % 3 < 1 ? '#ffd98a' : '#2a2f48') : '#9fc6d8');
}
/* the power pole with its tangle of wires running off the stage, every wire a catenary */
function wires(c, S, px, n) {
  var hh = S.hh, top = S.deck - hh * 2.05;
  paper(c, rect(px - hh * 0.04, top, hh * 0.08, S.deck - top), nt(S, '#b8b4aa'), 1);
  fr(c, px - hh * 0.22, top + hh * 0.12, hh * 0.44, 3, nt(S, '#8a867c'));
  c.strokeStyle = S.night ? 'rgba(10,10,20,.7)' : 'rgba(30,30,40,.7)'; c.lineWidth = 1;
  for (var i = 0; i < n; i++) { var y0 = top + hh * (0.13 + i * 0.07), sag = hh * (0.12 + (i % 3) * 0.06);
    c.beginPath(); c.moveTo(S.x0 - 6, y0 + sag * 0.6); c.quadraticCurveTo((S.x0 + px) / 2, y0 + sag * 1.6, px, y0); c.quadraticCurveTo((px + S.x1) / 2, y0 + sag * 2, S.x1 + 6, y0 + sag * 0.9 - hh * 0.4); c.stroke(); }
  fr(c, px + hh * 0.05, top + hh * 0.5, hh * 0.1, hh * 0.14, nt(S, '#6a6a72'));
}

/* ---------------------------------------------------------------- people */
/* an arm that reaches a point: two bones, the elbow by the law of cosines */
function solve(sh, T, l1, l2, dir) {
  var vx = dir * (T[0] - sh[0]), vy = T[1] - sh[1], d = Math.min(Math.sqrt(vx * vx + vy * vy), l1 + l2 - 0.01), at = Math.atan2(vx, vy);
  var al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * Math.max(d, 0.01)), -1, 1)), up = at - al;
  return [up, Math.atan2(vx - Math.sin(up) * l1, vy - Math.cos(up) * l1) - up];
}
function reach(x, y, h, P, dir, hA, hB) {
  var seat = P.seat || 0.47, lean = P.lean || 0, hip = [x, y - h * seat], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33], arms = P.arms.slice(), a;
  if (hA) { a = solve(sh, hA, h * 0.17, h * 0.16, dir); arms[0] = a[0]; arms[1] = a[1]; }
  if (hB) { a = solve(sh, hB, h * 0.17, h * 0.16, dir); arms[2] = a[0]; arms[3] = a[1]; }
  return { lean: lean, seat: seat, lift: P.lift || 0, legs: P.legs, arms: arms };
}
function crowd(S, n, mix) { return K.town(S, n, mix || { casual: 0.6, sin: 0.2, mohom: 0.2 }); }
/* a skirt laid over a dressed figure, from the hip to the knee */
function skirt(c, me, h, col, len) {
  var hx = me.hip[0], hy = me.hip[1], fx = (me.foot[0][0] + me.foot[1][0]) / 2, fy = Math.max(me.foot[0][1], me.foot[1][1]), by = lerp(hy, fy, len || 0.45), sp = h * 0.1 + Math.abs(me.foot[0][0] - me.foot[1][0]) * 0.25;
  fp(c, [[hx - h * 0.075, hy - h * 0.03], [hx + h * 0.075, hy - h * 0.03], [lerp(hx, fx, len || 0.45) + sp, by], [lerp(hx, fx, len || 0.45) - sp, by]], col);
}
function stand(lean) { return { lean: lean || 0, legs: [0.06, 0, -0.06, 0], arms: [0.12, 0.1, -0.1, 0.05] }; }
var SIT = { lean: 0.05, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4, 0.6, 0.3, 0.7] };
/* someone walking along, x = x₀ + vt, wrapping round the stage */
function stroll(S, i, v, off) { var L = S.span + S.hh * 2, u = ((S.t / 1000 * Math.abs(v) * S.hh + off * L) % L + L) % L; return v >= 0 ? S.x0 - S.hh + u : S.x1 + S.hh - u; }
/* a dressed figure in a white coat, scrubs or a uniform: shirt, trousers and skin set here */
function dress(d, top, low, hair) { d.garb = 'casual'; d.col = top; d.low = low; d.long = true; d.skirt = 0; if (hair != null) d.hair = hair; return d; }
/* a white coat over the figure, open at the front; a stethoscope */
function coat(c, me, h, dir) {
  fp(c, [[me.sh[0] - h * 0.09, me.sh[1] - h * 0.01], [me.sh[0] + h * 0.09, me.sh[1] - h * 0.01], [me.hip[0] + h * 0.1, me.hip[1] + h * 0.12], [me.hip[0] - h * 0.1, me.hip[1] + h * 0.12]], '#f8f8f4');
  ln(c, [[me.sh[0] + dir * h * 0.01, me.sh[1]], [me.hip[0] + dir * h * 0.02, me.hip[1] + h * 0.12]], 'rgba(0,0,0,.2)', 1);
  c.strokeStyle = '#3a3a44'; c.lineWidth = 1; c.beginPath(); c.moveTo(me.sh[0] - h * 0.05, me.sh[1]); c.quadraticCurveTo(me.sh[0], me.sh[1] + h * 0.16, me.sh[0] + h * 0.05, me.sh[1]); c.stroke(); dot(c, me.sh[0], me.sh[1] + h * 0.13, Math.max(1, h * 0.018), '#9a9aa2');
}
function mask(c, me, h, dir, col) { el(c, me.head[0] + dir * h * 0.04, me.head[1] + h * 0.035, h * 0.07, h * 0.045, 0, col || '#9fd8e8'); }
function nurseCap(c, me, h) { fp(c, [[me.head[0] - h * 0.07, me.head[1] - h * 0.08], [me.head[0] + h * 0.07, me.head[1] - h * 0.08], [me.head[0] + h * 0.05, me.head[1] - h * 0.14], [me.head[0] - h * 0.05, me.head[1] - h * 0.14]], '#ffffff'); }

/* ---------------------------------------------------------------- the frame every scene shares
   plan: the stage dealt from the seed, so the still layer and the moving parts agree */
function plan(S, salt) {
  var P = placeOf(S), r = rnd((S.seed ^ D.hash(salt)) >>> 0 || 7), st = stateOf(S, P), ck = clock(S);
  return { P: P, r: r, st: st, ck: ck, hh: S.hh, inside: insideOf(P), hits: [] };
}
/* the street side of a portrait: ground, setting, neighbours, power lines, plants, a spirit house,
   the road plate; L.fx0 … L.fx1 is where the place's own front goes */
function streetSide(c, S, L, o) {
  var hh = S.hh, r = L.r;
  street(c, S, o.ground || (L.P.moo && !L.P.road ? 'lane' : 'street'), r);
  K.setting(S);
  if (o.neighbours) { if (L.fx0 - S.x0 > hh * 1.1) neighbour(c, S, S.x0 - 4, L.fx0 - hh * (o.gapL || 0.25), 1); if (S.x1 - L.fx1 > hh * 1.4) neighbour(c, S, L.fx1 + hh * (o.gapR || 0.25), S.x1 + 4, 2); }
  if (o.wires) wires(c, S, L.pole, 4 + (S.seed % 3));
}
function decor(c, S, L, slots) {
  /* plants and the spirit house in the gaps the scene leaves; each slot [x, room] */
  var r = L.r, hh = S.hh, out = {};
  slots.forEach(function (sl, i) {
    var x = sl[0], k = Math.floor(r() * 7);
    if (sl[2] === 'spirit') { out.incense = spiritHouse(c, S, x, hh * 0.95, (S.seed >>> 2) % 3); return; }
    if (k === 0 || k === 1) bougainvillea(c, S, x, S.deck + hh * 0.02, hh * (0.8 + r() * 0.3), S.seed + i);
    else if (k === 2) banana(c, S, x, S.deck + hh * 0.02, hh * (0.9 + r() * 0.3), i);
    else if (k === 3) frangipani(c, S, x, S.deck + hh * 0.02, hh * (1 + r() * 0.3), i + S.seed);
    else if (k === 4) chilliPots(c, S, x - hh * 0.2, S.deck + hh * 0.05, hh * 0.9, 3);
    else shrub(c, S, x, S.deck + hh * 0.04, hh * 0.9, i);
  });
  return out;
}
/* the live bits every street shares: incense, a moth at the lamp when shut at night, the dog */
function streetLife(S, L) {
  var c = S.c, hh = S.hh;
  if (L.incense) smoke(c, L.incense[0], L.incense[1], hh * 0.4, S.t, 1);
  if (L.lamp && S.night) { if (L.st.lit || L.st.quiet) moth(c, L.lamp[0], L.lamp[1] + hh * 0.06, hh, S.t, S.seed % 7); }
  if (L.dog) dog(c, S, L.dog[0], L.dog[1], hh * 0.62, S.seed >>> 4, L.dog[2], S.t);
  if (L.cat) cat(c, S, L.cat[0], L.cat[1], hh * 0.5, S.seed >>> 5, S.t);
}
function pass(S, L, v, kind, k) {
  /* a motorbike or songthaew going by on the road, x = x₀ + vt */
  var hh = S.hh, y = S.H - Math.max(4, (S.H - S.deck) * 0.12), x = stroll(S, k, v, (S.seed % 100) / 100 + k * 0.4), dir = v > 0 ? 1 : -1;
  if (kind === 'songthaew') songthaew(S.c, S, x, y, hh * 0.72, dir, L.P.province === 'cr' ? '#2a7ac0' : '#c0392b');
  else { motorbike(S.c, S, x, y, hh * 0.62, dir, CLOTH2[(S.seed + k) % CLOTH2.length]);
    var d = L.rider || (L.rider = crowd(S, 1, { casual: 1 })[0]); d.dir = dir;
    person(S.c, x - dir * hh * 0.05, y - hh * 0.2, hh * 0.78, { lean: 0.15, seat: 0.3, legs: [1.2, -1.0, 1.1, -1.1], arms: [1.3, 0.3, 1.2, 0.35] }, d);
    if (S.night) { var g = S.c.createLinearGradient(x + dir * hh * 0.2, 0, x + dir * hh * 1.4, 0); g.addColorStop(0, 'rgba(255,240,190,.35)'); g.addColorStop(1, 'rgba(255,240,190,0)'); S.c.fillStyle = g; fp(S.c, [[x + dir * hh * 0.2, y - hh * 0.24], [x + dir * hh * 1.4, y - hh * 0.4], [x + dir * hh * 1.4, y], [x + dir * hh * 0.2, y - hh * 0.2]], g); } }
}
var CLOTH2 = ['#c0392b', '#2a5aa8', '#e2b33c', '#2f8f5b', '#f4f4f4', '#2a2a30', '#9b6bd6', '#e5567f'];

/* ---------------------------------------------------------------- shared games and gear */
/* a football passed between players: the ball on parabolas, y = v₀t − ½gt², the kicker's leg on sin² */
function football(c, S, xs, y, h, crew, k) {
  var n = xs.length, T = 1.6, u = (S.t / 1000 / T + k) % n, i = Math.floor(u), f = u - i, a = xs[i], b = xs[(i + 1) % n];
  xs.forEach(function (x, j) {
    var d = crew[j % crew.length], kick = j === i ? Math.pow(Math.sin(Math.PI * Math.min(1, f * 4)), 2) : 0, run = Math.sin(S.t / 260 + j * 2) * 0.3;
    d.dir = (j === i ? b : a) > x ? 1 : -1; if (j !== i && j !== (i + 1) % n) d.dir = (a + b) / 2 > x ? 1 : -1;
    person(c, x, y + (j % 2) * h * 0.08, h, { lean: 0.12, legs: [0.25 + run - kick * 0.2, -0.3, -0.25 - run + kick * 1.6, -0.2 * (1 - kick)], arms: [-run, 0.5, run, 0.5] }, d);
  });
  var bx = lerp(a, b, f), by = y - h * 0.04 - Math.sin(Math.PI * f) * h * 0.7;
  dot(c, bx, by, Math.max(2.5, h * 0.06), '#f4f4f4'); c.strokeStyle = '#2a2a30'; c.lineWidth = 1; c.beginPath(); c.arc(bx, by, Math.max(2.5, h * 0.06), 0, TAU); c.stroke();
}
function goal(c, S, x, y, s, dir) {
  ln(c, [[x, y], [x, y - s * 0.5], [x + dir * s * 0.7, y - s * 0.5], [x + dir * s * 0.7, y]], nt(S, '#f4f4f4'), Math.max(2, s * 0.03));
  c.strokeStyle = S.night ? 'rgba(200,200,220,.2)' : 'rgba(255,255,255,.35)'; c.lineWidth = 1; c.beginPath();
  for (var i = 1; i < 6; i++) { c.moveTo(x + dir * s * 0.7 * i / 6, y - s * 0.5); c.lineTo(x + dir * s * 0.7 * i / 6 - dir * s * 0.12, y); } for (i = 1; i < 4; i++) { c.moveTo(x, y - s * 0.5 * i / 4); c.lineTo(x + dir * s * 0.7, y - s * 0.5 * i / 4); } c.stroke();
}
/* the skipping rope turned by two, the jumper's hop on |sin ωt| */
function skipping(c, S, x, y, h, crew) {
  var w = 0.9 * h, a = S.t / 1000 * TAU * 1.2, hop = Math.max(0, Math.sin(a)) * h * 0.12;
  var A = crew[0], B = crew[1], J = crew[2]; A.dir = 1; B.dir = -1; J.dir = 1;
  var ha = person(c, x - w, y, h, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.0 + Math.cos(a) * 0.4, 0.4, 0.2, 0.1] }, A).hand[0];
  var hb = person(c, x + w, y, h, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.0 + Math.cos(a) * 0.4, 0.4, 0.2, 0.1] }, B).hand[0];
  var ry = (ha[1] + hb[1]) / 2 + Math.cos(a) * h * 0.55;
  c.strokeStyle = nt(S, '#e5567f'); c.lineWidth = 1.5; c.beginPath(); c.moveTo(ha[0], ha[1]); c.quadraticCurveTo(x, ry + Math.cos(a) * h * 0.4, hb[0], hb[1]); c.stroke();
  person(c, x, y - hop, h * 0.95, { lean: 0, lift: 0, legs: [0.2, -0.4 * (hop > 0 ? 1 : 0), -0.2, -0.4 * (hop > 0 ? 1 : 0)], arms: [0.6, 0.5, -0.4, 0.5] }, J);
}
/* an ice-cream cart on a bicycle with its bell and umbrella */
function iceCart(c, S, x, y, s, k, col) {
  bicycle(c, S, x - s * 0.15, y, s * 0.8, 1, '#4a4a52');
  paper(c, rect(x + s * 0.12, y - s * 0.58, s * 0.5, s * 0.36), nt(S, '#f4f4f4'), 0.8);
  fr(c, x + s * 0.12, y - s * 0.5, s * 0.5, s * 0.06, nt(S, col)); fr(c, x + s * 0.12, y - s * 0.36, s * 0.5, s * 0.06, nt(S, col));
  ln(c, [[x + s * 0.37, y - s * 0.58], [x + s * 0.37, y - s * 1.1]], '#5a5a62', 1.4);
  fp(c, [[x + s * 0.0, y - s * 1.04], [x + s * 0.37, y - s * 1.22], [x + s * 0.74, y - s * 1.04]], nt(S, k % 2 ? '#e5567f' : '#4d8fd1'));
  for (var i = 0; i < 3; i++) { var px = x + s * (0.2 + i * 0.14); fr(c, px, y - s * 0.72, s * 0.05, s * 0.1, ['#f08a5d', '#7fe0a4', '#ffd1e8'][i]); fr(c, px + s * 0.018, y - s * 0.62, s * 0.014, s * 0.05, '#c9a36a'); }
}

/* ---------------------------------------------------------------- school
   A government school by the clock: at eight the flag goes up the pole (h = h₀·ease(t/8)) with
   the school in rows; lessons with heads in the windows and PE on the field; football and the
   skipping rope at noon; at home time the parents' motorbikes at the gate; by night the gate
   shut. Mondays to Thursdays white and navy (scouts one day), Fridays northern dress. The
   building (an old wooden school on posts, a one- or two-storey block, a three-storey private
   school, a bright kindergarten, a glass international school), its colours, the field, the
   tree, the Buddha shrine and the gate are dealt. */
var SCHOOLCOL = [['#e5567f', '#4d8fd1'], ['#c0392b', '#e8b84a'], ['#2f8f5b', '#f4f4f4'], ['#3a5a8a', '#e8b84a'], ['#7a3a5a', '#f2c94c'], ['#e07a2a', '#2a3a8a'], ['#9b6bd6', '#f4f4f4'], ['#2a7ac0', '#d9342b']];
function schoolKind(P) {
  if (subOf(P, 'monastic') || has(P, /ปริยัติ|พระปริยัติธรรม|สามเณร|monastic/i)) return 'novice';
  if (subOf(P, 'international') || has(P, /international|นานาชาติ/i)) return 'intl';
  if (subOf(P, 'kindergarten') && !/[ปม]\./.test(P.levels || '') || has(P, /^(?!.*ประถม).*(อนุบาล|kindergarten|ศูนย์พัฒนาเด็กเล็ก|nursery|pre-?school)/i) && !/[ปม]\./.test(P.levels || '')) return 'kinder';
  if (subOf(P, 'private') || P.facility === 'private') return 'private';
  return 'gov';
}
function school(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'school'), P = L.P, r = L.r, ck = L.ck, kind = schoolKind(P);
  if (kind !== 'novice' && (subOf(P, 'driving') || trainKind(P) === 'drive' && subOf(P, 'training'))) return drive(S);
  if (kind !== 'novice' && (subOf(P, 'language') || subOf(P, 'tutoring') || subOf(P, 'music-art') || subOf(P, 'dance'))) return training(S);
  var cols = SCHOOLCOL[S.seed % SCHOOLCOL.length], wk = ck.dow >= 1 && ck.dow <= 5, h = ck.h;
  var mode = S.night ? 'night' : !wk || h < 6.8 || h > 18 ? 'weekend' : h < 8.4 ? 'flag' : h < 12 ? 'class' : h < 13 ? 'play' : h < 15.5 ? 'class' : 'home';
  if (L.st.known && !L.st.open && !S.night) mode = 'weekend';
  var lv = P.levels || '', sec = /ม\./.test(lv), pri = /ป\./.test(lv) || !lv, kin = /อ\.|อนุบาล/.test(lv) || kind === 'kinder';
  var dress = kind === 'novice' ? 'novice' : kind === 'intl' ? 'polo' : ck.dow === 5 ? 'lanna' : ck.dow === 3 + (S.seed % 2) ? 'scout' : 'white';
  if (kind === 'kinder' && dress === 'white') dress = 'kinder';
  /* where things stand: the block on one side, the gate on the other, the flag between */
  var left = (S.seed >>> 3) % 2 === 0, bw = Math.min(S.span * 0.46, hh * (3.4 + r() * 1.2));
  var bx0 = left ? S.x0 + hh * (0.7 + r() * 0.5) : S.x1 - hh * (1.3 + r() * 0.4) - bw, bx1 = bx0 + bw;
  var gx = left ? Math.min(S.x1 - hh * 1.6, bx1 + hh * (2.6 + r() * 0.8)) : Math.max(S.x0 + hh * 1.5, bx0 - hh * (2.6 + r() * 0.8));
  var fx = (left ? (bx1 + gx) / 2 : (gx + bx0) / 2) + (r() - 0.5) * hh * 0.4, gw = hh * 1.5;
  var bkind = kind === 'intl' ? 'glass' : kind === 'private' ? 'gov3' : kind === 'kinder' ? 'kinder' : pick(r, ['wood', 'gov1', 'gov2', 'gov2', 'gov1']);
  var tree = r() < 0.75, shrine = kind !== 'intl' && r() < 0.6, field = pick(r, ['grass', 'dirt', 'court']), wall = pick(r, ['#f2ece0', '#f6e3a6', '#f2d6d6', '#d8e4ee', '#e9d3a8']), roof = pick(r, ['#c06a3a', '#a8432f', '#2f6f6a', '#3a5a8a', '#b85a2a']);
  var key = 'school|' + mode + '|' + dress;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, field === 'grass' || kind === 'kinder' ? 'lawn' : 'lane', r);
    K.setting(S);
    /* the fence along the back of the yard */
    q.strokeStyle = nt(S, '#d8d0c0'); q.lineWidth = 1.2; q.beginPath(); for (var x = S.x0; x < S.x1; x += hh * 0.12) { q.moveTo(x, S.deck - hh * 0.32); q.lineTo(x, S.deck); } q.moveTo(S.x0, S.deck - hh * 0.28); q.lineTo(S.x1, S.deck - hh * 0.28); q.stroke();
    if (tree) rainTree(q, S, left ? S.x1 - hh * 0.9 : S.x0 + hh * 0.9, S.deck + hh * 0.02, hh * 1.05, S.seed);
    if (r() < 0.7 && mode !== 'night') { var ba = left ? bx1 - hh * 0.2 : fx + 2, bb = left ? fx - 2 : bx0 + hh * 0.2, bunt = [cols[0], cols[1], '#f2c94c', '#2f8f5b', '#4d8fd1'];
      K.strand(q, Math.min(ba, bb), Math.max(ba, bb), S.deck - hh * 1.75, hh * 0.25, Math.max(8, hh * 0.16), function (x, y, i) { fp(q, [[x - hh * 0.06, y], [x + hh * 0.06, y], [x, y + hh * 0.13]], nt(S, bunt[i % bunt.length])); }); }
    /* the building */
    var lit = false, b;
    if (bkind === 'wood') {
      b = facade(q, S, { kind: 'teak', x0: bx0, x1: bx1, wall: '#7a4a2a', trim: '#6a3a1e', roof: roof, lit: lit, stairL: !left });
      for (var w = 0; w < 4; w++) fr(q, bx0 + bw * (0.12 + w * 0.22), b.door.y0 - hh * 0.62, bw * 0.12, hh * 0.08, nt(S, cols[0]));
    } else if (bkind === 'glass') b = facade(q, S, { kind: 'glass', x0: bx0, x1: bx1, wall: '#e8ecef', trim: cols[0], roof: roof, floors: 3, lit: lit });
    else if (bkind === 'kinder') {
      b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: pick(r, ['#ffd1e8', '#d8f0c8', '#fff0b0', '#cfe8ff']), trim: cols[0], roof: cols[1] === '#f4f4f4' ? '#e5567f' : cols[1], floors: 1, gable: true });
      for (var cl = 0; cl < 6; cl++) fr(q, bx0 + cl * bw / 6, S.deck - hh * 0.1, bw / 6, hh * 0.1, nt(S, ['#e5567f', '#f2c94c', '#4d8fd1', '#2f8f5b', '#e07a2a', '#9b6bd6'][cl]));
    } else b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: wall, trim: cols[0], roof: roof, floors: bkind === 'gov1' ? 1 : bkind === 'gov2' ? 2 : 3, gable: r() < 0.5, doorAt: 1 });
    o.top = b.top;
    for (var pt = bx0 + hh * 0.15; pt < bx1 - hh * 0.1; pt += hh * 0.55) { fp(q, [[pt - hh * 0.07, S.deck - hh * 0.1], [pt + hh * 0.07, S.deck - hh * 0.1], [pt + hh * 0.05, S.deck + hh * 0.02], [pt - hh * 0.05, S.deck + hh * 0.02]], nt(S, '#b8683a')); shrub(q, S, pt, S.deck - hh * 0.08, hh * 0.7, Math.round(pt)); }
    /* heads in the windows during lessons */
    if (mode === 'class' || mode === 'flag' || mode === 'home') o.room = classroom(q, S, b, bx0, bx1, left, mode === 'class', r);
    /* the school's colours in a band, and its name in letters on the wall (cut in paper) */
    if (bkind !== 'wood' && bkind !== 'glass') { fr(q, bx0, b.top + hh * 0.42 + (bkind === 'gov1' || bkind === 'kinder' ? hh * 0.06 : 0), bw, hh * 0.04, nt(S, cols[0])); }
    /* the Buddha on his pedestal under a little roof, a garland at his feet */
    if (shrine) { var sx = left ? bx1 + hh * 0.5 : bx0 - hh * 0.5;
      paper(q, rect(sx - hh * 0.2, S.deck - hh * 0.36, hh * 0.4, hh * 0.36), nt(S, '#f2ece0'), 1);
      el(q, sx, S.deck - hh * 0.46, hh * 0.13, hh * 0.08, 0, nt(S, '#d4a23f')); el(q, sx, S.deck - hh * 0.6, hh * 0.07, hh * 0.1, 0, nt(S, '#e0b04a')); dot(q, sx, S.deck - hh * 0.74, hh * 0.05, nt(S, '#e0b04a')); fp(q, [[sx - hh * 0.02, S.deck - hh * 0.78], [sx, S.deck - hh * 0.86], [sx + hh * 0.02, S.deck - hh * 0.78]], nt(S, '#e0b04a'));
      fp(q, [[sx - hh * 0.3, S.deck - hh * 0.92], [sx, S.deck - hh * 1.12], [sx + hh * 0.3, S.deck - hh * 0.92]], nt(S, '#a8432f')); fr(q, sx - hh * 0.22, S.deck - hh * 0.92, 3, hh * 0.56, nt(S, '#f2ece0')); fr(q, sx + hh * 0.2, S.deck - hh * 0.92, 3, hh * 0.56, nt(S, '#f2ece0'));
      for (var m = 0; m < 6; m++) dot(q, sx - hh * 0.12 + m * hh * 0.05, S.deck - hh * 0.36, hh * 0.022, '#f29a1f'); o.shrine = [sx, S.deck - hh * 0.36]; }
    /* the field */
    var fx0 = left ? bx1 + hh * 0.2 : S.x0 + hh * 0.2, fx1 = left ? S.x1 - hh * 0.2 : bx0 - hh * 0.2;
    if (field === 'court') { paper(q, rect(S.x0, S.deck + hh * 0.08, S.span, (S.H - S.deck) * 0.7), nt(S, '#b8604a'), 0.6); q.strokeStyle = nt(S, '#f4f4f4'); q.lineWidth = 1.5; q.strokeRect(S.x0 + hh * 0.3, S.deck + hh * 0.14, S.span - hh * 0.6, (S.H - S.deck) * 0.55); }
    else if (mode !== 'flag') goal(q, S, left ? S.x1 - hh * 0.4 : S.x0 + hh * 0.4, S.deck + hh * 0.18, hh * 0.9, left ? -1 : 1);
    /* the flagpole on its plinth */
    paper(q, rect(fx - hh * 0.22, S.deck - hh * 0.12, hh * 0.44, hh * 0.12), nt(S, '#f2ece0'), 1);
    fr(q, fx - 1.6, S.deck - hh * 2.2, 3.2, hh * 2.1, nt(S, '#d8d8de')); dot(q, fx, S.deck - hh * 2.22, 3, nt(S, '#e8b84a'));
    /* the gate: two pillars in the school's colours and a beam; its leaves shut at night */
    var g0 = gx - gw / 2, g1 = gx + gw / 2, gt = S.deck - hh * 1.5;
    paper(q, rect(g0 - hh * 0.12, gt, hh * 0.24, S.deck - gt), nt(S, cols[0]), 1.2); paper(q, rect(g1 - hh * 0.12, gt, hh * 0.24, S.deck - gt), nt(S, cols[0]), 1.2);
    fr(q, g0 - hh * 0.14, gt - hh * 0.06, hh * 0.28, hh * 0.08, nt(S, cols[1])); fr(q, g1 - hh * 0.14, gt - hh * 0.06, hh * 0.28, hh * 0.08, nt(S, cols[1]));
    paper(q, rect(g0 - hh * 0.2, gt - hh * 0.06, gw + hh * 0.4, hh * 0.1), nt(S, cols[1] === '#f4f4f4' ? '#f2ece0' : cols[1]), 1.2);
    var shut = mode === 'night' || mode === 'weekend' && (S.seed % 3 === 0);
    q.strokeStyle = nt(S, '#5a5a62'); q.lineWidth = 1.5; q.beginPath();
    if (shut) { for (var gb = g0 + hh * 0.14; gb < g1 - hh * 0.12; gb += hh * 0.1) { q.moveTo(gb, S.deck - hh * 0.72); q.lineTo(gb, S.deck); } q.moveTo(g0 + hh * 0.12, S.deck - hh * 0.7); q.lineTo(g1 - hh * 0.12, S.deck - hh * 0.7); q.moveTo(g0 + hh * 0.12, S.deck - hh * 0.06); q.lineTo(g1 - hh * 0.12, S.deck - hh * 0.06); }
    else { [g0 + hh * 0.12, g1 - hh * 0.12].forEach(function (e, i) { var d = i ? -1 : 1; for (var k2 = 0; k2 < 3; k2++) { q.moveTo(e + d * k2 * hh * 0.05, S.deck - hh * 0.7); q.lineTo(e + d * k2 * hh * 0.05, S.deck); } }); }
    q.stroke();
    var sb = signAt(q, S, gx, gt + hh * 0.06, P, hh * 0.8, nt(S, cols[0] === '#f4f4f4' ? '#2f8f5b' : '#5a2e18'), L.st.lit || null);
    o.sign = sb;
    if (S.night) { o.lamp = [g1 + hh * 0.02, gt - hh * 0.3]; bulb(q, S, o.lamp[0], o.lamp[1], hh, true); }
    roadPlate(q, S, left ? S.x1 - hh * 0.25 : S.x0 + hh * 0.25, P.road);
    return o;
  }).out || {};
  /* the flag: up by day, lowered at six; at eight it climbs */
  var pole = S.deck - hh * 2.12, foot = S.deck - hh * 0.5, fh = mode === 'night' ? -1 : mode === 'flag' ? ease(((S.t / 1000) % 14) / 9) : 1;
  if (fh >= 0) thaiFlag(c, fx + 2, lerp(foot, pole, fh), hh * 0.5, S.t, 1, S.night);
  if (still.shrine && !S.night) smoke(c, still.shrine[0] + hh * 0.1, still.shrine[1], hh * 0.35, S.t, 2);
  if (still.lamp) moth(c, still.lamp[0], still.lamp[1] + hh * 0.06, hh, S.t, 3);
  if (still.room && mode === 'class') {   /* the teacher at the board, the chalk going along a line, x = x₀ + vt */
    var R = still.room, cw = (S.t / 1000 * 0.3) % 1, tx = R.bx + R.bw * (0.15 + 0.7 * cw), tc = dressUp(crowd(S, 1, { casual: 1 })[0], '#f2e6c9', '#3a3a44'); tc.dir = -1; tc.hair = 2;
    var me0 = person(c, tx + hh * 0.22, R.y1, hh * 0.7, { lean: 0.05, legs: [0.05, 0, -0.05, 0], arms: [2.2, 0.3, 0.2, 0.2] }, tc);
    ln(c, [[R.bx + R.bw * 0.15, R.by + R.bh * 0.92], [tx, R.by + R.bh * 0.92]], 'rgba(255,255,255,.6)', 1);
  }
  /* the children, dressed for the day */
  var kh = sec && !pri ? hh * 0.88 : kin && !pri ? hh * 0.62 : hh * 0.75;
  function kid(d, i) {
    var girl = (i + S.seed) % 2 === 0; d.garb = 'casual'; d.long = false; d.skirt = 0; d.hair = girl ? (i % 3 ? 3 : 1) : 0;
    if (dress === 'white') { d.col = '#f8f8f4'; d.low = girl ? d.skin : '#24305a'; d.sk = girl ? '#24305a' : null; }
    else if (dress === 'scout') { d.col = girl ? '#3a6a8a' : '#a8925a'; d.low = girl ? d.skin : '#7a6a42'; d.sk = girl ? '#2a3a5a' : null; d.hair = girl ? d.hair : 4; }
    else if (dress === 'lanna') { if (girl) { d.garb = 'sin'; d.col = pick(K.rnd(i + 3), ['#f2e6c9', '#ffd1e8', '#c3a6ff']); d.low = ['#7a1f3a', '#2a3a6a', '#5a2a6a', '#1f5a4a'][i % 4]; d.hem = '#e8b84a'; d.sabai = '#e8b84a'; } else { d.garb = 'mohom'; d.col = '#2c3e6b'; d.low = '#24335a'; } }
    else if (dress === 'polo') { d.col = cols[0]; d.low = girl ? d.skin : '#2a2a30'; d.sk = girl ? '#2a2a30' : null; }
    else if (dress === 'kinder') { d.col = pick(K.rnd(i + 9), ['#f8f8f4', '#ffd1e8', '#cfe8ff', '#fff0b0']); d.low = girl ? d.skin : '#c0392b'; d.sk = girl ? '#c0392b' : null; }
    else { d.garb = 'casual'; d.col = '#d27a32'; d.low = '#d27a32'; d.hair = 0; d.hairCol = '#5a4030'; d.long = true; }
    return d;
  }
  function draw(x, y, hgt, Pz, d) { var me = person(c, x, y, hgt, Pz, d); if (d.sk) skirt(c, me, hgt, d.sk, 0.42); if (dress === 'white' || dress === 'polo') fp(c, [[me.sh[0] - hgt * 0.02, me.sh[1] + hgt * 0.01], [me.sh[0] + hgt * 0.02, me.sh[1] + hgt * 0.01], [me.sh[0], me.sh[1] + hgt * 0.07]], dress === 'polo' ? '#f4f4f4' : '#24305a'); return me; }
  var kids = crowd(S, 18, { casual: 1 }).map(kid);
  if (mode === 'flag') {
    /* the rows stand across the yard on the far side of the pole from the gate, facing it */
    var rows = 3, away = gx > fx ? -1 : 1, room = away < 0 ? fx - S.x0 : S.x1 - fx, per = Math.max(3, Math.min(8, Math.floor(room / (hh * 0.34)) - 2)), dirF = -away, i = 0;
    for (var row = rows - 1; row >= 0; row--) for (var j = 0; j < per; j++, i++) {
      var x = fx + away * hh * (0.6 + j * 0.34 + row * 0.1), y = S.deck + hh * (0.08 + row * 0.13), d = kids[i % kids.length]; d.dir = dirF;
      if (x < S.x0 + hh * 0.3 || x > S.x1 - hh * 0.3) continue;
      draw(x, y, kh * (0.96 + row * 0.04), { lean: 0, legs: [0.03, 0, -0.03, 0], arms: [0.05, 0, -0.05, 0] }, d);
    }
    var tch = dress === 'lanna' ? crowd(S, 1, { sin: 1 })[0] : dress === 'scout' ? dressUp(crowd(S, 1, { casual: 1 })[0], '#a8925a', '#7a6a42') : dressUp(crowd(S, 1, { casual: 1 })[0], '#c8b07a', '#7a6a42');
    tch.dir = -dirF; var pull = Math.sin(S.t / 300) * 0.4;
    person(c, fx - away * hh * 0.28, S.deck + hh * 0.02, hh * 0.95, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [2.6 + pull, 0.2, 2.4 - pull, 0.3] }, tch);
  } else if (mode === 'class' || mode === 'play') {
    var fl0 = left ? Math.max(fx + hh * 0.6, bx1 + hh * 0.6) : S.x0 + hh * 1.2, fl1 = left ? S.x1 - hh * 1.2 : Math.min(fx - hh * 0.6, bx0 - hh * 0.4);
    var np = Math.max(2, Math.min(5, Math.floor((fl1 - fl0) / (hh * 0.55))));
    var xs = []; for (var p = 0; p < np; p++) xs.push(lerp(fl0, fl1, np > 1 ? p / (np - 1) : 0.5) + Math.sin(S.t / 900 + p) * hh * 0.12);
    football(c, S, xs, S.deck + hh * 0.2, kh, kids.slice(0, np), 0);
    if (mode === 'play') { var sxx = left ? bx0 + bw * 0.5 : bx0 + bw * 0.5; skipping(c, S, sxx, S.deck + hh * 0.3, kh * 0.95, kids.slice(8, 11));
      iceCart(c, S, gx + (left ? -1 : 1) * hh * 0.1 - hh * 0.3, S.deck + hh * 0.42, hh * 0.8, S.seed, cols[0]); }
    else { var jn = crowd(S, 1, { casual: 1 })[0]; dressUp(jn, '#6a8a5a', '#3a3a44'); jn.dir = 1; var sw = Math.sin(S.t / 380);
      var jx = (left ? bx0 : bx1) + (left ? 1 : -1) * hh * 0.6, me = person(c, jx, S.deck + hh * 0.1, hh * 0.92, { lean: 0.35, legs: [0.1, 0, -0.1, 0], arms: [0.9 + sw * 0.4, 0.4, 0.8 + sw * 0.4, 0.5] }, jn);
      ln(c, [me.hand[0], [me.hand[0][0] + hh * 0.18 + sw * hh * 0.1, S.deck + hh * 0.1]], '#a8925a', 2); for (var bb = 0; bb < 5; bb++) ln(c, [[me.hand[0][0] + hh * 0.18 + sw * hh * 0.1, S.deck + hh * 0.1], [me.hand[0][0] + hh * (0.12 + bb * 0.03) + sw * hh * 0.1, S.deck + hh * 0.12]], '#c9a36a', 1); }
  } else if (mode === 'home') {
    var dirH = gx > fx ? 1 : -1;
    for (var q2 = 0; q2 < 2; q2++) { var mx = gx + dirH * hh * (0.9 + q2 * 1.15); if (mx > S.x1 - hh * 0.5 || mx < S.x0 + hh * 0.5) continue; motorbike(c, S, mx, S.deck + hh * 0.42, hh * 0.62, -dirH, CLOTH2[(S.seed + q2) % 8]);
      var pa = crowd(S, 1)[0]; pa.dir = -dirH; person(c, mx + dirH * hh * 0.05, S.deck + hh * 0.22, hh * 0.85, { lean: 0.05, seat: 0.3, legs: [1.2, -1.0, 1.1, -1.1], arms: [1.3, 0.3, 1.2, 0.35] }, pa); }
    for (var k3 = 0; k3 < 4; k3++) { var d3 = kids[k3]; d3.dir = dirH; var wx = gx - dirH * hh * (0.3 + k3 * 0.5) + dirH * ((S.t / 1000 * hh * 0.25 + k3 * hh * 0.7) % (hh * 1.2)), m3 = draw(wx, S.deck + hh * 0.12 + (k3 % 2) * hh * 0.08, kh, K.walkP(S.t / 1000 * TAU * 0.9 + k3, false), d3);
      fr(c, m3.sh[0] - dirH * kh * 0.16, m3.sh[1], kh * 0.1, kh * 0.18, nt(S, CLOTH2[(k3 + S.seed) % 8])); }
    /* the meatball man's grill at the gate, smoke rising */
    var gxx = gx - dirH * hh * 1.0; if (gxx > S.x0 + hh * 0.4 && gxx < S.x1 - hh * 0.4) { fr(c, gxx - hh * 0.25, S.deck + hh * 0.08, hh * 0.5, hh * 0.22, nt(S, '#5a5a62')); for (var mb = 0; mb < 5; mb++) { ln(c, [[gxx - hh * 0.2 + mb * hh * 0.1, S.deck + hh * 0.06], [gxx - hh * 0.2 + mb * hh * 0.1, S.deck - hh * 0.12]], '#c9a36a', 1); for (var bl = 0; bl < 3; bl++) dot(c, gxx - hh * 0.2 + mb * hh * 0.1, S.deck - hh * (0.02 + bl * 0.04), hh * 0.022, '#8a4a2a'); }
      for (var sm = 0; sm < 5; sm++) { var su = (S.t / 1800 + sm / 5) % 1; dot(c, gxx + Math.sin(su * 5 + sm) * hh * 0.08, S.deck - hh * 0.2 - su * hh * 0.7, hh * (0.04 + su * 0.08), 'rgba(240,240,240,' + (0.4 * Math.sin(Math.PI * su)).toFixed(2) + ')'); } }
  } else if (mode === 'weekend') {
    var wx0 = left ? bx1 + hh * 0.8 : S.x0 + hh * 1.0, wx1 = left ? S.x1 - hh * 1.0 : bx0 - hh * 0.8, adults = crowd(S, 4, { casual: 1 });
    if (S.seed % 2) football(c, S, [wx0, lerp(wx0, wx1, 0.5), wx1], S.deck + hh * 0.2, hh * 0.9, adults, 0.3);
    else { var bxr = stroll(S, 0, 0.5, 0.2), dk = kids[3]; dk.dir = 1; bicycle(c, S, bxr, S.deck + hh * 0.4, hh * 0.6, 1, '#e5567f'); dk.garb = 'casual'; dk.col = CLOTH2[S.seed % 8]; dk.low = '#3a3a44'; person(c, bxr - hh * 0.02, S.deck + hh * 0.14, kh, { lean: 0.15, seat: 0.4, legs: [1.0 + Math.sin(S.t / 200) * 0.5, -1.2, 1.0 - Math.sin(S.t / 200) * 0.5, -1.2], arms: [1.2, 0.3, 1.1, 0.3] }, dk);
      dog(c, S, gx + hh * 0.2, S.deck + hh * 0.2, hh * 0.6, S.seed, false, S.t); }
  } else dog(c, S, gx - hh * 0.1, S.deck + hh * 0.25, hh * 0.6, S.seed, true, S.t);
  if (still.sign) S.hits.push({ k: 'place', x0: Math.min(bx0, still.sign.x0), x1: Math.max(bx1, still.sign.x1), y0: still.top || S.deck - hh * 2, y1: S.deck });
}
/* a classroom opened up on the ground floor: the green board with its letters, desks, the
   children's heads in rows when a lesson is on */
function classroom(c, S, b, bx0, bx1, left, on, r) {
  var hh = S.hh, w = Math.min(hh * 1.9, (bx1 - bx0) * 0.5), x0 = left ? bx1 - w - hh * 0.25 : bx0 + hh * 0.25, y0 = b.door.y0 + hh * 0.02, y1 = S.deck - hh * 0.04;
  fr(c, x0 - 2, y0 - 2, w + 4, y1 - y0 + 4, nt(S, '#6a5a4a'));
  fr(c, x0, y0, w, y1 - y0, nt(S, '#efe6cf'));
  var bw = w * 0.62, bx = x0 + w * 0.3, by = y0 + (y1 - y0) * 0.1, bh = (y1 - y0) * 0.42;
  fr(c, bx - 2, by - 2, bw + 4, bh + 4, nt(S, '#8a6a3a')); fr(c, bx, by, bw, bh, nt(S, '#2f5a42'));
  var lines = pick(r, [['ก ข ค ง', 'จ ฉ ช'], ['1 + 2 = 3', '2 × 3 = 6'], ['A B C', 'cat · dog'], ['ก ข ค', '๑ ๒ ๓']]);
  txt(c, lines[0], bx + bw * 0.5, by + bh * 0.32, Math.max(8, hh * 0.11), 'rgba(255,255,255,.88)', 700); txt(c, lines[1], bx + bw * 0.5, by + bh * 0.7, Math.max(7, hh * 0.09), 'rgba(255,255,255,.7)', 600);
  fr(c, x0 + w * 0.05, by, w * 0.18, bh * 0.9, nt(S, '#d9c08a'));
  for (var k = 0; k < 4; k++) fr(c, x0 + w * 0.07, by + bh * (0.1 + k * 0.2), w * 0.14, 2, nt(S, '#8a6a3a'));
  if (on) for (var row = 0; row < 2; row++) for (var i = 0; i < 4; i++) {
    var hx = x0 + w * (0.18 + i * 0.22 + row * 0.06), hy = y1 - hh * (0.2 - row * 0.1);
    fr(c, hx - hh * 0.1, hy + hh * 0.05, hh * 0.2, hh * 0.04, nt(S, '#a8784a'));
    fr(c, hx - hh * 0.04, hy - hh * 0.02, hh * 0.08, hh * 0.08, nt(S, '#f8f8f4'));
    dot(c, hx, hy - hh * 0.06, hh * 0.05, nt(S, K.SKIN[(i + row * 2 + S.seed) % 5])); c.fillStyle = '#1c1410'; c.beginPath(); c.arc(hx, hy - hh * 0.075, hh * 0.05, Math.PI * 1.0, Math.PI * 2.0); c.fill();
  }
  c.strokeStyle = nt(S, '#6a5a4a'); c.lineWidth = 2; c.strokeRect(x0, y0, w, y1 - y0);
  return { x0: x0, x1: x0 + w, y0: y0, y1: y1, bx: bx, by: by, bw: bw, bh: bh };
}
function dressUp(d, top, low) { d.garb = 'casual'; d.col = top; d.low = low; d.long = true; d.skirt = 0; return d; }


/* ---------------------------------------------------------------- the shopfront: one frame for the trades of the street
   A shop in a row of shophouses, a one-storey row, a glass box, a teak house; or a unit in a
   mall, or a booth under a market's roof. The front opens on the room where the trade is done
   (cfg.room cuts it once, cfg.work moves in it); a pictogram of the trade hangs out on a bracket
   so the street can read it without its name. Shut: the roll-up shutter is down. */
function shopScene(S, salt, cfg) {
  var hh = S.hh, c = S.c, L = plan(S, salt), r = L.r, P = L.P, st = L.st;
  L.kind = cfg.kind ? cfg.kind(L) : pick(r, cfg.kinds || ['shop', 'shop', 'row', 'glass']);
  if (L.inside === 'mall') L.kind = 'glass';
  if (L.inside === 'market') L.kind = 'row';
  var fw = Math.min(S.span * (S.phone ? 0.62 : 0.5), hh * (3.3 + r() * 1.1));
  L.fx0 = S.x0 + hh * 1.0 + r() * Math.max(0, S.span - fw - hh * 2.3); L.fx1 = L.fx0 + fw;
  L.floors = 2 + Math.floor(r() * 3); L.wall = cfg.wall ? cfg.wall(r) : pick(r, WALL); L.trim = pick(r, TRIM); L.roof = pick(r, ROOF);
  L.awn = r() < 0.6 ? pick(r, [['#c0392b', '#f4f4f4'], ['#2f6f6a', '#f2e6c9'], ['#3a5a8a', '#f4f4f4'], ['#e8b84a', '#7a3a1e'], ['#2f8f5b', '#f4f4f4']]) : null;
  L.neigh = L.inside ? false : r() < 0.55; L.wires = !L.inside && !L.P.moo && r() < 0.6;
  var leftRoom = L.fx0 - S.x0, rightRoom = S.x1 - L.fx1, big = leftRoom > rightRoom ? -1 : 1;
  L.spirit = !L.inside && r() < 0.72 ? (big < 0 ? L.fx0 - hh * 0.45 : L.fx1 + hh * 0.45) : null;
  L.pole = big < 0 ? S.x0 + hh * 0.9 : S.x1 - hh * 1.1;
  L.plantX = big < 0 ? (L.fx1 + hh * 0.5 < S.x1 - hh * 0.8 ? L.fx1 + hh * 0.5 : null) : (L.fx0 - hh * 0.5 > S.x0 + hh * 0.8 ? L.fx0 - hh * 0.5 : null);
  L.bike = r() < 0.7 ? (big < 0 ? Math.max(S.x0 + hh * 1.2, L.fx0 - hh * 1.3) : Math.min(S.x1 - hh * 1.2, L.fx1 + hh * 1.3)) : null; L.bikeCol = pick(r, CLOTH2);
  L.animal = r(); L.blade = cfg.icon ? (L.spirit == null ? (big < 0 ? -1 : 1) : (big < 0 ? 1 : -1)) : 0;
  var key = salt + '|' + (st.shut ? 's' : st.open ? 'o' : 'q') + (st.lit ? 'l' : '') + '|' + (cfg.keyOf ? cfg.keyOf(L) : '');
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    if (L.inside === 'mall') mallBack(q, S, L);
    else {
      street(q, S, L.P.moo && !L.P.road ? 'lane' : 'street', r);
      K.setting(S);
      if (L.inside === 'market') marketRoof(q, S, L);
      if (L.neigh) { if (leftRoom > hh * 1.2) neighbour(q, S, S.x0 - 4, L.fx0 - hh * 0.06, 1); if (rightRoom > hh * 1.2) neighbour(q, S, L.fx1 + hh * 0.06, S.x1 + 4, 2); }
      else if (!L.inside) { var tx = big < 0 ? S.x0 + hh * 0.6 : S.x1 - hh * 0.7; if (r() < 0.5) rainTree(q, S, tx, S.deck + hh * 0.02, hh * 0.85, S.seed); else banana(q, S, tx, S.deck + hh * 0.02, hh * 1.1, S.seed); }
      if (L.wires) wires(q, S, L.pole, 4 + S.seed % 3);
    }
    var f = facade(q, S, { kind: L.kind, x0: L.fx0, x1: L.fx1, wall: L.wall, trim: L.trim, roof: L.roof, floors: L.kind === 'gov' ? 2 : L.floors, gf: L.kind === 'gov' ? hh * 1.2 : null, lit: st.lit, seed: S.seed, stairL: big > 0 });
    L.f = f;
    var R = { x0: f.door.x0, x1: f.door.x1, y0: f.door.y0, y1: S.deck };
    /* the room: its wall, its light, its furniture */
    var bright = st.open || st.lit, dimc = S.night && !st.lit;
    q.save(); q.beginPath(); q.rect(R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0); q.clip();
    fr(q, R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0, dimc ? '#2a2630' : cfg.back || '#f2ece0');
    fr(q, R.x0, R.y1 - hh * 0.12, R.x1 - R.x0, hh * 0.12, dimc ? '#3a3440' : cfg.floor || '#d8cdb8');
    if (cfg.room) { var d0 = S.night; if (dimc) S.night = true; else if (st.lit) S.night = false; o.room = cfg.room(q, S, R, L) || {}; S.night = d0; }
    if (dimc) { q.fillStyle = 'rgba(10,10,30,.45)'; q.fillRect(R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0); }
    q.restore();
    if (bright && S.night) { var g = q.createLinearGradient(0, S.deck, 0, S.deck + hh * 0.6); g.addColorStop(0, 'rgba(255,214,140,.45)'); g.addColorStop(1, 'rgba(255,214,140,0)'); fp(q, [[R.x0, S.deck], [R.x1, S.deck], [R.x1 + hh * 0.4, S.deck + hh * 0.6], [R.x0 - hh * 0.4, S.deck + hh * 0.6]], g); }
    if (st.shut) { if (L.kind === 'glass') { fr(q, R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0, 'rgba(20,24,40,.7)'); closedPlate(q, S, (R.x0 + R.x1) / 2, R.y0 + hh * 0.2); } else shutter(q, S, R.x0, R.x1, R.y0, R.y1, pick(K.rnd(S.seed), ['#9aa6b0', '#a8b8a0', '#b0a8a0', '#8a9ab8']), true); }
    else if (L.kind !== 'teak' && L.kind !== 'glass') shutter(q, S, R.x0, R.x1, R.y0, R.y1, '#9aa6b0', false);
    if (L.kind === 'glass' && !st.shut) { q.strokeStyle = nt(S, '#6a7a86'); q.lineWidth = 2; q.strokeRect(R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0); }
    /* the awning */
    if (L.awn && L.kind !== 'teak') { var ay = R.y0 - hh * 0.02, ad = hh * 0.22, n = Math.max(4, Math.round((R.x1 - R.x0) / (hh * 0.22)));
      for (var k = 0; k < n; k++) { var ax = lerp(R.x0 - hh * 0.06, R.x1 + hh * 0.06, k / n), aw = (R.x1 - R.x0 + hh * 0.12) / n; fp(q, [[ax, ay], [ax + aw, ay], [ax + aw + 1, ay + ad], [ax - 1, ay + ad]], nt(S, L.awn[k % 2])); q.fillStyle = nt(S, L.awn[k % 2]); q.beginPath(); q.arc(ax + aw / 2, ay + ad, aw / 2, 0, Math.PI); q.fill(); } }
    /* Lanna touches dealt to the front: khom lanterns at the eave, or marigolds strung over the door */
    var lt = (S.seed >>> 11) % 4;
    if (lt === 0 && !L.inside) { khom(q, S, R.x0 + hh * 0.12, R.y0 + hh * 0.2, hh * 0.16, '#d9342b', S.night && (st.lit || st.open)); khom(q, S, R.x1 - hh * 0.12, R.y0 + hh * 0.2, hh * 0.16, '#e8b84a', S.night && (st.lit || st.open)); }
    else if (lt === 1) marigolds(q, S, R.x0 + hh * 0.05, R.x1 - hh * 0.05, R.y0 + (L.awn ? hh * 0.3 : hh * 0.04), hh * 0.12);
    /* the board with the name over the front, the trade's pictogram out on its bracket */
    var sy = L.kind === 'shop' ? f.signY - hh * 0.52 : L.kind === 'teak' ? f.signY - hh * 0.5 : L.kind === 'glass' ? f.signY - hh * 0.52 : L.kind === 'gov' ? f.signY - hh * 0.6 : f.signY - hh * 0.12;
    o.sign = signAt(q, S, (L.fx0 + L.fx1) / 2, sy, P, hh * 0.78, nt(S, cfg.signCol ? cfg.signCol(L) : '#5a2e18'), st.lit || (st.shut ? false : null));
    if (cfg.icon) { var bx = L.blade < 0 ? L.fx0 - hh * 0.02 : L.fx1 + hh * 0.02, by = f.signY - hh * 0.32, rr = hh * 0.22, cx = bx + L.blade * (rr + hh * 0.08);
      ln(q, [[bx, by - rr * 0.7], [cx, by - rr * 0.7]], nt(S, '#3a3a44'), 2); ln(q, [[cx - rr * 0.6, by - rr * 0.7], [cx - rr * 0.6, by - rr * 0.55]], nt(S, '#3a3a44'), 1); ln(q, [[cx + rr * 0.6, by - rr * 0.7], [cx + rr * 0.6, by - rr * 0.55]], nt(S, '#3a3a44'), 1);
      if (st.lit || st.open && S.night) glow(q, cx, by + rr * 0.3, rr * 2.4, '255,240,200', 0.4);
      paper(q, function (p) { p.beginPath(); p.arc(cx, by + rr * 0.3, rr, 0, TAU); }, nt(S, cfg.iconBg || '#f8f8f4'), 1); q.strokeStyle = nt(S, L.trim); q.lineWidth = 2; q.beginPath(); q.arc(cx, by + rr * 0.3, rr - 2, 0, TAU); q.stroke();
      cfg.icon(q, S, cx, by + rr * 0.3, rr * 0.75, L); }
    if (L.inside === 'mall' || L.inside === 'market' || L.inside === 'campus' || L.inside === 'hospital') { var iy = (o.sign ? o.sign.y1 : sy) + 3; txt(q, 'ใน ' + (P.inside.length > 26 ? P.inside.slice(0, 25) + '…' : P.inside), (L.fx0 + L.fx1) / 2, iy + hh * 0.07, Math.max(8, hh * 0.1), S.night ? '#e8e0c8' : '#3a2a20', 600); }
    /* the street's things */
    if (!L.inside) {
      if (L.spirit != null) o.incense = spiritHouse(q, S, L.spirit, hh * 0.95, (S.seed >>> 2) % 3);
      if (L.plantX != null) { var pk = (S.seed >>> 6) % 4; if (pk === 0) bougainvillea(q, S, L.plantX, S.deck + hh * 0.04, hh * 0.9, S.seed); else if (pk === 1) chilliPots(q, S, L.plantX - hh * 0.2, S.deck + hh * 0.06, hh * 0.9, 3); else if (pk === 2) frangipani(q, S, L.plantX, S.deck + hh * 0.04, hh * 1.05, S.seed); else banana(q, S, L.plantX, S.deck + hh * 0.04, hh, S.seed); }
      if (L.bike != null) motorbike(q, S, L.bike, S.deck + hh * 0.36, hh * 0.62, L.bike < L.fx0 ? 1 : -1, L.bikeCol, (S.seed >>> 7) % 5 === 0);
      o.plate = roadPlate(q, S, L.plantX != null && Math.abs(L.plantX - (L.fx0 + L.fx1) / 2) > hh ? (L.blade < 0 ? L.fx1 + hh * 0.2 : L.fx0 - hh * 0.2) : (big < 0 ? S.x0 + hh * 0.75 : S.x1 - hh * 0.8), P.road);
    }
    if (S.night && !L.inside) { o.lamp = [L.blade < 0 ? L.fx1 - hh * 0.25 : L.fx0 + hh * 0.25, R.y0 - hh * 0.1]; bulb(q, S, o.lamp[0], o.lamp[1], hh, st.lit || st.quiet); }
    o.R = R; o.top = f.top;
    return o;
  }).out || {};
  var R = still.R;
  L.incense = still.incense; L.lamp = still.lamp;
  if (!L.inside && (st.shut || st.quiet)) L.dog = [Math.min(S.x1 - hh * 0.6, R.x1 - hh * 0.1), S.deck + hh * 0.22, true];
  else if (!L.inside && L.animal < 0.35) L.dog = [L.bike != null ? L.bike + hh * 0.3 : R.x0 - hh * 0.4, S.deck + hh * 0.2, false];
  else if (!L.inside && L.animal < 0.6 && !st.shut) L.cat = [R.x0 + hh * 0.2, S.deck + hh * 0.02];
  if (st.open || st.lit) { c.save(); c.beginPath(); c.rect(R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0); c.clip(); if (cfg.work) cfg.work(c, S, R, L, still.room || {}); c.restore();
    if (L.kind === 'glass') { c.fillStyle = 'rgba(255,255,255,.12)'; fp(c, [[R.x0 + (R.x1 - R.x0) * 0.6, R.y0], [R.x0 + (R.x1 - R.x0) * 0.72, R.y0], [R.x0 + (R.x1 - R.x0) * 0.5, R.y1], [R.x0 + (R.x1 - R.x0) * 0.38, R.y1]], 'rgba(255,255,255,.1)'); } }
  if (cfg.front) cfg.front(c, S, R, L);
  streetLife(S, L);
  if (L.inside === 'mall') mallLife(S, L);
  else if (!S.phone && (S.seed >>> 9) % 3 === 0) pass(S, L, ((S.seed >>> 4) % 2 ? 0.9 : -0.9), (S.seed >>> 5) % 4 === 0 ? 'songthaew' : 'bike', 0);
  S.hits.push({ k: 'place', x0: L.fx0, x1: L.fx1, y0: still.top || S.deck - hh * 2, y1: S.deck });
  return L;
}
function closedPlate(c, S, x, y) {
  var hh = S.hh; ln(c, [[x - hh * 0.15, y - hh * 0.12], [x, y - hh * 0.2], [x + hh * 0.15, y - hh * 0.12]], '#c9a36a', 1);
  paper(c, rect(x - hh * 0.3, y - hh * 0.12, hh * 0.6, hh * 0.24), '#f4ecd8', 0.6); txt(c, 'ปิด · CLOSED', x, y, Math.max(7, hh * 0.085), '#a8342a', 800);
}
/* a mall's inside: the tiled floor, the upper level's glass rail, downlights, an escalator, the
   other units lit either side */
function mallBack(c, S, L) {
  var hh = S.hh, top = S.deck - hh * 2.5;
  fr(c, S.x0 - 6, top, S.span + 12, S.deck - top, '#efe6d6');
  fr(c, S.x0 - 6, top + hh * 0.9, S.span + 12, hh * 0.1, '#d8cdb8');
  c.fillStyle = 'rgba(160,200,220,.35)'; c.fillRect(S.x0 - 6, top + hh * 0.62, S.span + 12, hh * 0.28); ln(c, [[S.x0 - 6, top + hh * 0.62], [S.x1 + 6, top + hh * 0.62]], '#b8c0c8', 2);
  for (var x = S.x0 + hh * 0.3; x < S.x1; x += hh * 0.9) { glow(c, x, top + hh * 1.02, hh * 0.3, '255,240,200', 0.6); dot(c, x, top + hh * 1.01, 2, '#fffbe8'); }
  var ex = L.fx0 < S.x0 + S.span / 2 ? S.x1 - hh * 2.4 : S.x0 + hh * 0.6;
  fp(c, [[ex, S.deck], [ex + hh * 0.35, S.deck], [ex + hh * 1.9, top + hh * 0.9], [ex + hh * 1.55, top + hh * 0.9]], '#b8bcc4'); ln(c, [[ex, S.deck - hh * 0.25], [ex + hh * 1.55, top + hh * 0.66]], '#2a2a30', 2);
  [[S.x0 - 6, L.fx0 - hh * 0.15], [L.fx1 + hh * 0.15, S.x1 + 6]].forEach(function (u, i) { if (u[1] - u[0] < hh * 0.6) return;
    fr(c, u[0], S.deck - hh * 1.45, u[1] - u[0], hh * 1.45, '#fbf6ea'); fr(c, u[0], S.deck - hh * 1.45, u[1] - u[0], hh * 0.18, ['#c0392b', '#2a5aa8', '#2f8f5b', '#9b6bd6'][(S.seed + i) % 4]);
    for (var k = u[0] + hh * 0.2; k < u[1] - hh * 0.2; k += hh * 0.3) { fr(c, k, S.deck - hh * 0.95, hh * 0.18, hh * 0.3, CLOTH2[(Math.round(k) + i) % 8]); fr(c, k - hh * 0.02, S.deck - hh * 0.62, hh * 0.22, 2, '#c8c0b0'); } });
  fr(c, S.x0 - 6, S.deck, S.span + 12, S.H - S.deck, '#e8e0d0'); c.strokeStyle = 'rgba(0,0,0,.08)'; c.lineWidth = 1; c.beginPath();
  for (x = S.x0 - hh; x < S.x1 + hh; x += hh * 0.5) { c.moveTo(x, S.deck); c.lineTo(x + (x - (S.x0 + S.x1) / 2) * 0.3, S.H); } for (var y = S.deck + 6; y < S.H; y += (y - S.deck) * 0.5 + 6) { c.moveTo(S.x0, y); c.lineTo(S.x1, y); } c.stroke();
}
function mallLife(S, L) {
  var c = S.c, hh = S.hh, crew = L.mall || (L.mall = crowd(S, 3, { casual: 1 }));
  for (var i = 0; i < 3; i++) { var v = (i % 2 ? -0.35 : 0.3) * (1 + i * 0.15), x = stroll(S, i, v, i * 0.37 + (S.seed % 50) / 50), d = crew[i]; d.dir = v > 0 ? 1 : -1;
    var me = person(c, x, S.deck + hh * (0.25 + (i % 2) * 0.12), hh * 0.9, K.walkP(S.t / 1000 * TAU * 0.9 + i, false), d);
    if (i !== 1) fr(c, me.hand[0][0] - hh * 0.05, me.hand[0][1], hh * 0.1, hh * 0.12, nt(S, CLOTH2[(i + S.seed) % 8])); }
}
/* a market's roof of tin on steel posts over the booth */
function marketRoof(c, S, L) {
  var hh = S.hh, top = S.deck - hh * 2.1;
  for (var x = S.x0 + hh * 0.4; x < S.x1; x += hh * 2.2) fr(c, x, top + hh * 0.2, 4, S.deck - top - hh * 0.2, nt(S, '#7a8088'));
  paper(c, poly([[S.x0 - 6, top + hh * 0.3], [S.x0 + S.span * 0.5, top], [S.x1 + 6, top + hh * 0.3], [S.x1 + 6, top + hh * 0.38], [S.x0 - 6, top + hh * 0.38]]), nt(S, '#a8b0b8'), 1.2);
  for (x = S.x0 + hh * 0.5; x < S.x1; x += hh * 1.3) { ln(c, [[x, top + hh * 0.38], [x, top + hh * 0.6]], '#3a3a44', 1); fr(c, x - hh * 0.2, top + hh * 0.6, hh * 0.4, 3, S.night ? '#fffbe0' : '#e8e8e8'); }
}
/* pictograms for the bracket: no words, the trade */
var ICON = {
  cross: function (c, S, x, y, s) { var a = s * 0.28, b = s * 0.85; fr(c, x - a, y - b, a * 2, b * 2, nt(S, '#2f9a5b')); fr(c, x - b, y - a, b * 2, a * 2, nt(S, '#2f9a5b')); },
  tooth: function (c, S, x, y, s) { c.fillStyle = '#ffffff'; c.strokeStyle = nt(S, '#3a8ac0'); c.lineWidth = Math.max(1.5, s * 0.1); c.beginPath(); c.moveTo(x - s * 0.7, y - s * 0.45); c.quadraticCurveTo(x - s * 0.75, y - s * 0.95, x - s * 0.3, y - s * 0.85); c.quadraticCurveTo(x, y - s * 0.72, x + s * 0.3, y - s * 0.85); c.quadraticCurveTo(x + s * 0.75, y - s * 0.95, x + s * 0.7, y - s * 0.45);
    c.quadraticCurveTo(x + s * 0.6, y + s * 0.1, x + s * 0.4, y + s * 0.85); c.quadraticCurveTo(x + s * 0.25, y + s * 0.95, x + s * 0.15, y + s * 0.6); c.quadraticCurveTo(x, y + s * 0.2, x - s * 0.15, y + s * 0.6); c.quadraticCurveTo(x - s * 0.25, y + s * 0.95, x - s * 0.4, y + s * 0.85); c.quadraticCurveTo(x - s * 0.6, y + s * 0.1, x - s * 0.7, y - s * 0.45); c.closePath(); c.fill(); c.stroke(); },
  glasses: function (c, S, x, y, s) { c.strokeStyle = nt(S, '#2a2a30'); c.lineWidth = Math.max(2, s * 0.14); c.beginPath(); c.arc(x - s * 0.45, y + s * 0.05, s * 0.36, 0, TAU); c.moveTo(x + s * 0.81, y + s * 0.05); c.arc(x + s * 0.45, y + s * 0.05, s * 0.36, 0, TAU); c.moveTo(x - s * 0.1, y - s * 0.05); c.quadraticCurveTo(x, y - s * 0.18, x + s * 0.1, y - s * 0.05); c.moveTo(x - s * 0.8, y - s * 0.05); c.lineTo(x - s * 0.98, y - s * 0.2); c.moveTo(x + s * 0.8, y - s * 0.05); c.lineTo(x + s * 0.98, y - s * 0.2); c.stroke();
    c.fillStyle = 'rgba(120,190,230,.4)'; c.beginPath(); c.arc(x - s * 0.45, y + s * 0.05, s * 0.3, 0, TAU); c.arc(x + s * 0.45, y + s * 0.05, s * 0.3, 0, TAU); c.fill(); },
  machine: function (c, S, x, y, s) { c.save(); c.translate(x, y); c.rotate(-0.6); fr(c, -s * 0.12, -s * 0.9, s * 0.24, s * 1.1, nt(S, '#2a2a30')); fr(c, -s * 0.3, -s * 0.55, s * 0.6, s * 0.35, nt(S, '#c0392b')); dot(c, 0, -s * 0.38, s * 0.12, nt(S, '#e8b84a')); ln(c, [[0, s * 0.2], [0, s * 0.85]], nt(S, '#8a8a92'), Math.max(1.5, s * 0.08)); c.restore(); },
  book: function (c, S, x, y, s) { fp(c, [[x, y - s * 0.4], [x - s * 0.85, y - s * 0.6], [x - s * 0.85, y + s * 0.5], [x, y + s * 0.7]], nt(S, '#2a5aa8')); fp(c, [[x, y - s * 0.4], [x + s * 0.85, y - s * 0.6], [x + s * 0.85, y + s * 0.5], [x, y + s * 0.7]], nt(S, '#3a6ac0')); for (var k = 0; k < 3; k++) { ln(c, [[x - s * 0.7, y - s * 0.3 + k * s * 0.25], [x - s * 0.15, y - s * 0.18 + k * s * 0.25]], '#f4f4f4', 1); ln(c, [[x + s * 0.7, y - s * 0.3 + k * s * 0.25], [x + s * 0.15, y - s * 0.18 + k * s * 0.25]], '#f4f4f4', 1); } },
  note: function (c, S, x, y, s) { el(c, x - s * 0.35, y + s * 0.5, s * 0.26, s * 0.2, -0.4, nt(S, '#2a2a30')); el(c, x + s * 0.45, y + s * 0.35, s * 0.26, s * 0.2, -0.4, nt(S, '#2a2a30')); ln(c, [[x - s * 0.12, y + s * 0.45], [x - s * 0.12, y - s * 0.7], [x + s * 0.68, y - s * 0.85], [x + s * 0.68, y + s * 0.3]], nt(S, '#2a2a30'), Math.max(2, s * 0.12)); },
  dumbbell: function (c, S, x, y, s) { fr(c, x - s * 0.55, y - s * 0.06, s * 1.1, s * 0.12, nt(S, '#5a5a62')); [-1, 1].forEach(function (d) { fr(c, x + d * s * 0.55 - s * 0.12, y - s * 0.45, s * 0.24, s * 0.9, nt(S, '#2a2a30')); fr(c, x + d * s * 0.82 - s * 0.08, y - s * 0.3, s * 0.16, s * 0.6, nt(S, '#2a2a30')); }); },
  lotus: function (c, S, x, y, s) { for (var k = -2; k <= 2; k++) { c.save(); c.translate(x, y + s * 0.5); c.rotate(k * 0.42); el(c, 0, -s * 0.5, s * 0.2, s * 0.55, 0, nt(S, k % 2 ? '#f08ab0' : '#e5567f')); c.restore(); } fr(c, x - s * 0.8, y + s * 0.55, s * 1.6, s * 0.08, nt(S, '#2f8f5b')); }
};

/* ---------------------------------------------------------------- the room's furniture */
function bench(c, S, x0, x1, y, hh) { fr(c, x0, y - hh * 0.3, x1 - x0, hh * 0.05, nt(S, '#3a6ac0')); fr(c, x0, y - hh * 0.5, x1 - x0, hh * 0.05, nt(S, '#3a6ac0')); fr(c, x0 + 3, y - hh * 0.3, 3, hh * 0.3, nt(S, '#8a8a92')); fr(c, x1 - 6, y - hh * 0.3, 3, hh * 0.3, nt(S, '#8a8a92')); }
function poster(c, S, x, y, w, h, col, draw) { fr(c, x - 1, y - 1, w + 2, h + 2, nt(S, '#8a8a92')); fr(c, x, y, w, h, nt(S, col)); if (draw) draw(c, x, y, w, h); }
/* a wall clock reading the reader's own time: the hands at 2π·h/12 and 2π·m/60 */
function wallClock(c, S, x, y, rr) {
  dot(c, x, y, rr, nt(S, '#f8f8f4')); c.strokeStyle = nt(S, '#3a3a44'); c.lineWidth = 1.2; c.beginPath(); c.arc(x, y, rr, 0, TAU); c.stroke();
  var b = new Date((S.now || 0) + 7 * 3600e3 + S.t * 0), h = b.getUTCHours() % 12 + b.getUTCMinutes() / 60, m = b.getUTCMinutes() + (S.t / 60000) % 60;
  ln(c, [[x, y], [x + Math.sin(h / 12 * TAU) * rr * 0.5, y - Math.cos(h / 12 * TAU) * rr * 0.5]], '#2a2a30', 1.6); ln(c, [[x, y], [x + Math.sin(m / 60 * TAU) * rr * 0.8, y - Math.cos(m / 60 * TAU) * rr * 0.8]], '#2a2a30', 1);
}
function lyingDown(c, x, y, h, d, up) { c.save(); c.translate(x, y); c.rotate(Math.PI / 2 - (up || 0)); d.dir = 1; var me = person(c, 0, 0, h, { lean: 0, legs: [0.03, 0, -0.03, 0], arms: [0.06, 0, -0.04, 0] }, d); c.restore(); return me; }
function sitAt(c, x, y, h, d, dir, arms) { d.dir = dir; return person(c, x, y, h, { lean: 0.05, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: arms || [0.4, 0.6, 0.3, 0.7] }, d); }
function cot(c, S, x0, x1, y, hh, col) { fr(c, x0, y - hh * 0.32, x1 - x0, hh * 0.08, nt(S, col || '#e8e8f0')); fr(c, x0 + 2, y - hh * 0.24, 3, hh * 0.24, nt(S, '#8a8a92')); fr(c, x1 - 5, y - hh * 0.24, 3, hh * 0.24, nt(S, '#8a8a92')); fr(c, x0, y - hh * 0.36, hh * 0.18, hh * 0.05, nt(S, '#f8f8f4')); }

/* ---------------------------------------------------------------- clinic
   A shophouse clinic open to the street: the counter, the bench of people waiting, the doctor
   in his room with the stethoscope, a queue number that steps on n = ⌊t/5⌋; a green cross out
   on the bracket. What the clinic treats changes the room: skin (a bed and a laser that
   blinks), physio (the parallel bars, an elder's slow steps), Thai medicine (herb jars and
   the compress's steam), Chinese medicine (needles), a lab (the centrifuge spinning, θ = ωt),
   long care (wheelchairs), children (toys and a balloon on a string, a pendulum). */
function clinicKind(P) {
  var w = words(P);
  if (/skin|ผิว|ความงาม|beauty|aesthetic|laser|เลเซอร์|ศัลยกรรม|botox|โบท็อก/i.test(w)) return 'skin';
  if (/physio|กายภาพ|rehab|ฟื้นฟู|ortho|กระดูก/i.test(w)) return 'physio';
  if (/chinese|จีน|ฝังเข็ม|acupunct|ครอบแก้ว/i.test(w)) return 'chinese';
  if (/thai-med|thai-medicine|แผนไทย|แพทย์แผน|สมุนไพร|herbal/i.test(w)) return 'thai';
  if (/\blab|laborator|แล็บ|แลบ|ห้องปฏิบัติการ|เทคนิคการแพทย์|x-?ray|เอกซเรย์/i.test(w)) return 'lab';
  if (/long-care|geriatric|nursing|ผู้สูงอายุ|care home|ดูแล|บ้านพัก|elderly/i.test(w)) return 'care';
  if (/paediatric|pediatric|child|kids|เด็ก|กุมาร/i.test(w)) return 'child';
  if (/\bent\b|หู ?คอ ?จมูก|โสต|eye|ตา\b|จักษุ/i.test(w)) return 'ent';
  return 'general';
}
var CLINICBACK = { general: '#e6f2ec', skin: '#f6e2e6', physio: '#e8eef6', chinese: '#f2e2c8', thai: '#f2ead2', lab: '#eef2f6', care: '#f2ecdc', child: '#fff2c8', ent: '#e6f2ec' };
function clinic(S) {
  var kindC = clinicKind(placeOf(S));
  shopScene(S, 'clinic', {
    kinds: kindC === 'care' ? ['row', 'teak', 'glass'] : kindC === 'thai' || kindC === 'chinese' ? ['shop', 'teak', 'row'] : ['shop', 'shop', 'glass', 'row'],
    back: CLINICBACK[kindC], floor: '#dfe6e2', icon: kindC === 'thai' ? ICON.lotus : ICON.cross, keyOf: function () { return kindC; },
    room: function (q, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, o = {};
      wallClock(q, S, R.x0 + w * 0.5, R.y0 + hh * 0.18, hh * 0.08);
      o.clock = [R.x0 + w * 0.5, R.y0 + hh * 0.18];
      /* the queue board */
      fr(q, R.x0 + w * 0.06, R.y0 + hh * 0.1, hh * 0.36, hh * 0.18, '#1a1a22'); o.q = [R.x0 + w * 0.06 + hh * 0.18, R.y0 + hh * 0.19];
      if (kindC === 'skin') { poster(q, S, R.x1 - w * 0.32, R.y0 + hh * 0.08, hh * 0.35, hh * 0.45, '#f8e8ec', function (p, x, y, ww, h) { el(p, x + ww / 2, y + h * 0.45, ww * 0.28, h * 0.32, 0, '#e8b89a'); dot(p, x + ww * 0.4, y + h * 0.4, 1.5, '#2a2a30'); dot(p, x + ww * 0.6, y + h * 0.4, 1.5, '#2a2a30'); for (var k = 0; k < 4; k++) dot(p, x + ww * (0.3 + k * 0.13), y + h * 0.85, 2, '#e5567f'); }); cot(q, S, R.x0 + w * 0.42, R.x0 + w * 0.82, R.y1, hh, '#f8e0e8'); }
      else if (kindC === 'physio') { cot(q, S, R.x0 + w * 0.08, R.x0 + w * 0.42, R.y1, hh, '#dfe8f6'); var pb0 = R.x0 + w * 0.5, pb1 = R.x1 - w * 0.08; ln(q, [[pb0, R.y1 - hh * 0.42], [pb1, R.y1 - hh * 0.42]], '#8a8a92', 3); [pb0, pb1].forEach(function (x) { fr(q, x - 1.5, R.y1 - hh * 0.42, 3, hh * 0.42, '#8a8a92'); }); dot(q, R.x0 + w * 0.46, R.y1 - hh * 0.14, hh * 0.14, '#4d8fd1'); o.bars = [pb0, pb1]; }
      else if (kindC === 'thai' || kindC === 'chinese') { for (var sh = 0; sh < 3; sh++) { fr(q, R.x0 + w * 0.05, R.y0 + hh * (0.35 + sh * 0.18), w * 0.32, 2, '#7a4a2a'); for (var j = 0; j < 5; j++) { var jx = R.x0 + w * (0.08 + j * 0.06); fr(q, jx, R.y0 + hh * (0.24 + sh * 0.18), hh * 0.07, hh * 0.1, ['#c9a36a', '#8a5a3a', '#e8d4a0', '#5a7a3a'][(j + sh) % 4]); fr(q, jx, R.y0 + hh * (0.24 + sh * 0.18), hh * 0.07, hh * 0.025, '#d9342b'); } } cot(q, S, R.x0 + w * 0.45, R.x0 + w * 0.88, R.y1, hh, '#e8d8b8'); }
      else if (kindC === 'lab') { fr(q, R.x0 + w * 0.4, R.y1 - hh * 0.42, w * 0.55, hh * 0.06, '#f4f4f4'); fr(q, R.x0 + w * 0.4, R.y1 - hh * 0.36, w * 0.55, hh * 0.36, '#d8dce4');
        for (var tb = 0; tb < 6; tb++) { fr(q, R.x0 + w * 0.72 + tb * hh * 0.045, R.y1 - hh * 0.56, hh * 0.025, hh * 0.13, ['#d9342b', '#7a1f3a', '#e8b84a', '#4d8fd1', '#7a1f3a', '#2f8f5b'][tb]); } fr(q, R.x0 + w * 0.7, R.y1 - hh * 0.46, hh * 0.3, hh * 0.04, '#8a8a92');
        fr(q, R.x0 + w * 0.48, R.y1 - hh * 0.56, hh * 0.08, hh * 0.14, '#3a3a44'); ln(q, [[R.x0 + w * 0.52, R.y1 - hh * 0.56], [R.x0 + w * 0.56, R.y1 - hh * 0.7]], '#3a3a44', 3); o.cf = [R.x0 + w * 0.9, R.y1 - hh * 0.5]; }
      else if (kindC === 'care') { fr(q, R.x1 - w * 0.3, R.y0 + hh * 0.12, hh * 0.5, hh * 0.3, '#2a2a30'); fr(q, R.x1 - w * 0.3 + 3, R.y0 + hh * 0.12 + 3, hh * 0.5 - 6, hh * 0.3 - 6, S.night ? '#6a8aaa' : '#7ab0d0'); poster(q, S, R.x0 + w * 0.12, R.y0 + hh * 0.36, hh * 0.3, hh * 0.22, '#f8f8f4', function (p, x, y, ww, h) { for (var k = 0; k < 3; k++) dot(p, x + ww * (0.25 + k * 0.25), y + h * 0.55, h * 0.18, ['#e5567f', '#f2c94c', '#4d8fd1'][k]); }); }
      else if (kindC === 'child') { for (var k2 = 0; k2 < 5; k2++) { var ax = R.x0 + w * (0.1 + k2 * 0.18); dot(q, ax, R.y0 + hh * 0.42, hh * 0.07, ['#f2c94c', '#e5567f', '#7fe0a4', '#4d8fd1', '#f08a5d'][k2]); dot(q, ax - hh * 0.05, R.y0 + hh * 0.36, hh * 0.03, ['#f2c94c', '#e5567f', '#7fe0a4', '#4d8fd1', '#f08a5d'][k2]); dot(q, ax + hh * 0.05, R.y0 + hh * 0.36, hh * 0.03, ['#f2c94c', '#e5567f', '#7fe0a4', '#4d8fd1', '#f08a5d'][k2]); }
        fr(q, R.x0 + w * 0.08, R.y1 - hh * 0.12, hh * 0.12, hh * 0.12, '#e5567f'); fr(q, R.x0 + w * 0.08 + hh * 0.13, R.y1 - hh * 0.1, hh * 0.1, hh * 0.1, '#4d8fd1'); fr(q, R.x0 + w * 0.08 + hh * 0.06, R.y1 - hh * 0.22, hh * 0.1, hh * 0.1, '#f2c94c'); }
      else poster(q, S, R.x1 - w * 0.28, R.y0 + hh * 0.08, hh * 0.3, hh * 0.42, '#f8f8f4', function (p, x, y, ww, h) { dot(p, x + ww / 2, y + h * 0.22, ww * 0.12, '#e8b89a'); fr(p, x + ww * 0.36, y + h * 0.32, ww * 0.28, h * 0.4, '#e8b89a'); ln(p, [[x + ww / 2, y + h * 0.36], [x + ww / 2, y + h * 0.66]], '#d9342b', 1); dot(p, x + ww * 0.45, y + h * 0.42, 1.5, '#d9342b'); });
      if (kindC === 'general' || kindC === 'child' || kindC === 'ent') { var dx = R.x1 - w * 0.36; fr(q, dx - 2, R.y0 + hh * 0.06, 3, R.y1 - R.y0, '#b8bcc4'); bench(q, S, R.x0 + w * 0.06, R.x0 + w * 0.42, R.y1, hh); fr(q, R.x1 - w * 0.1, R.y1 - hh * 0.4, hh * 0.18, hh * 0.4, '#c9a36a'); }
      if (kindC === 'skin' || kindC === 'care' || kindC === 'lab') bench(q, S, R.x0 + w * 0.05, R.x0 + w * 0.34, R.y1, hh);
      return o;
    },
    work: function (c, S, R, L, o) {
      var hh = S.hh, w = R.x1 - R.x0, t = S.t, crew = crowd(S, 5, { casual: 0.8, sin: 0.2 }), sw = Math.sin(t / 500);
      if (o.q) { var n = (Math.floor(t / 5000) + S.seed) % 90 + 10; txt(c, ('0' + n).slice(-3), o.q[0], o.q[1], hh * 0.13, '#ff5a3a', 800); }
      var doc = dress(crew[0], '#f8f8f4', '#3a3a44', 0), pat = crew[1], nurse = dress(crew[2], kindC === 'skin' ? '#f2b8c8' : '#f8f8f4', kindC === 'skin' ? '#f2b8c8' : '#f8f8f4', 2);
      function waiting(x0, x1, n2) { for (var i = 0; i < n2; i++) { var x = lerp(x0, x1, n2 > 1 ? i / (n2 - 1) : 0.5), d = crew[3 + i % 2], cough = i === 0 ? Math.max(0, Math.sin(t / 400)) * 0.15 : 0;
        var me = person(c, x, R.y1 - hh * 0.02, hh * 0.86, { lean: 0.05 + cough, seat: 0.36, legs: [1.45, -1.4, 1.4, -1.45], arms: i === 1 ? [1.2, 1.2, 0.3, 0.7] : [0.4, 0.6, 0.3, 0.7] }, d);
        if (i === 1) { fr(c, me.hand[0][0] - 2, me.hand[0][1] - hh * 0.08, hh * 0.05, hh * 0.08, '#2a2a30'); if (S.night) glow(c, me.hand[0][0], me.hand[0][1] - hh * 0.04, hh * 0.15, '180,210,255', 0.5); } } }
      if (kindC === 'general' || kindC === 'child' || kindC === 'ent') {
        waiting(R.x0 + w * 0.12, R.x0 + w * 0.34, w > hh * 2.8 ? 2 : 1);
        if (kindC === 'child') { var bx = R.x0 + w * 0.22 + Math.sin(t / 900) * hh * 0.05; ln(c, [[R.x0 + w * 0.24, R.y1 - hh * 0.5], [bx, R.y0 + hh * 0.5]], '#5a5a62', 1); el(c, bx, R.y0 + hh * 0.42, hh * 0.09, hh * 0.11, 0, '#e5567f'); }
        var px = R.x1 - w * 0.18, me2 = sitAt(c, px, R.y1, hh * (kindC === 'child' ? 0.62 : 0.86), pat, -1);
        var dxx = R.x1 - w * 0.06; doc.dir = -1; var ear = kindC === 'ent' ? [me2.head[0] + hh * 0.06, me2.head[1]] : [me2.sh[0] + hh * 0.05 + sw * hh * 0.02, me2.sh[1] + hh * 0.06];
        var dP = { lean: 0.25, legs: [0.06, 0, -0.06, 0], arms: [1.3 + sw * 0.1, 0.6, 0.3, 0.3] }, me3 = person(c, dxx + hh * 0.18, R.y1, hh * 0.98, dP, doc); coat(c, me3, hh * 0.98, -1);
        ln(c, [me3.hand[0], ear], '#3a3a44', 1); dot(c, ear[0], ear[1], 2, '#9a9aa2');
        if (kindC === 'ent') { c.strokeStyle = '#d8d8de'; c.lineWidth = 1.5; c.beginPath(); c.arc(me3.head[0], me3.head[1] - hh * 0.08, hh * 0.04, 0, TAU); c.stroke(); }
      } else if (kindC === 'skin') {
        waiting(R.x0 + w * 0.12, R.x0 + w * 0.26, 1);
        var cl = crew[4]; cl.garb = 'casual'; cl.col = '#f8f8f4'; lyingDown(c, R.x0 + w * 0.44, R.y1 - hh * 0.36, hh * 0.9, cl);
        var hx = R.x0 + w * 0.47; nurse.dir = -1; var me4 = person(c, hx + hh * 0.05, R.y1, hh * 0.92, { lean: 0.5, legs: [0.06, 0, -0.06, 0], arms: [1.1, 0.5, 0.6, 0.4] }, nurse); mask(c, me4, hh * 0.92, -1);
        var blink = Math.sin(t / 160) > 0.3; ln(c, [me4.hand[0], [me4.hand[0][0] - hh * 0.06, R.y1 - hh * 0.4]], '#3a3a44', 2); if (blink) { glow(c, me4.hand[0][0] - hh * 0.06, R.y1 - hh * 0.4, hh * 0.12, '255,80,80', 0.7); dot(c, me4.hand[0][0] - hh * 0.06, R.y1 - hh * 0.4, 1.6, '#ff3a3a'); }
      } else if (kindC === 'physio') {
        var pp = crew[4]; lyingDown(c, R.x0 + w * 0.1, R.y1 - hh * 0.32, hh * 0.86, pp);
        var th = dress(crew[0], '#4d8fd1', '#2a2a30', 0); th.dir = -1; var pr = 0.5 + 0.5 * Math.sin(t / 700); person(c, R.x0 + w * 0.3, R.y1, hh * 0.95, { lean: 0.6 + pr * 0.15, legs: [0.1, 0, -0.1, 0], arms: [1.6, 0.2, 1.5, 0.3] }, th);
        if (o.bars) { var ph = (t / 1000 * 0.12) % 1, ex = lerp(o.bars[0] + hh * 0.15, o.bars[1] - hh * 0.15, 0.5 - 0.5 * Math.cos(ph * TAU)), el2 = crew[3]; el2.hairCol = '#bdbdbd'; el2.dir = Math.sin(ph * TAU) > 0 ? 1 : -1;
          var Pw = K.walkP(t / 1000 * TAU * 0.35, false); Pw.arms = [0.9, 0.4, 0.9, 0.4]; Pw.lean = 0.12; person(c, ex, R.y1, hh * 0.9, Pw, el2); }
      } else if (kindC === 'thai' || kindC === 'chinese') {
        var lp = crew[4]; lp.garb = 'casual'; lp.col = '#e8b84a'; var ly = R.y1 - hh * 0.36; lyingDown(c, R.x0 + w * 0.47, ly, hh * 0.88, lp);
        var tp = dress(crew[0], kindC === 'thai' ? '#5a2a6a' : '#f8f8f4', '#2a2a30', 2); tp.dir = -1; var press = 0.5 - 0.5 * Math.cos(t / 1000 * TAU * 0.5);
        var me5 = person(c, R.x0 + w * 0.82, R.y1, hh * 0.95, { lean: 0.45 + press * 0.1, legs: [0.06, 0, -0.06, 0], arms: [1.3 + press * 0.2, 0.3, 1.1, 0.4] }, tp);
        if (kindC === 'thai') { dot(c, me5.hand[0][0], me5.hand[0][1] + 2, hh * 0.06, '#e8dcc0'); for (var st2 = 0; st2 < 3; st2++) { var su = (t / 1800 + st2 / 3) % 1; dot(c, me5.hand[0][0] + Math.sin(su * 6) * 3, me5.hand[0][1] - su * hh * 0.4, hh * (0.02 + su * 0.04), 'rgba(255,255,255,' + (0.5 * Math.sin(Math.PI * su)).toFixed(2) + ')'); } }
        else for (var nd = 0; nd < 5; nd++) { var nx = R.x0 + w * 0.5 + nd * hh * 0.1; ln(c, [[nx, ly - hh * 0.06], [nx + 1, ly - hh * 0.16 - (nd % 2) * 3]], '#c9ccd4', 1); dot(c, nx + 1, ly - hh * 0.16 - (nd % 2) * 3, 1.3, '#e8b84a'); }
      } else if (kindC === 'lab') {
        waiting(R.x0 + w * 0.1, R.x0 + w * 0.26, 1);
        var tech = dress(crew[0], '#f8f8f4', '#3a3a44', 2); tech.dir = 1; var bob = Math.sin(t / 1200) * 0.05; var me6 = person(c, R.x0 + w * 0.44, R.y1, hh * 0.92, { lean: 0.35 + bob, seat: 0.36, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.4, 0.4, 1.2, 0.5] }, tech); coat(c, me6, hh * 0.92, 1);
        if (o.cf) { var a = t / 60; dot(c, o.cf[0], o.cf[1], hh * 0.1, '#d8dce4'); c.strokeStyle = '#3a3a44'; c.lineWidth = 1.5; c.beginPath(); for (var k3 = 0; k3 < 3; k3++) { c.moveTo(o.cf[0], o.cf[1]); c.lineTo(o.cf[0] + Math.cos(a + k3 * 2.09) * hh * 0.08, o.cf[1] + Math.sin(a + k3 * 2.09) * hh * 0.08); } c.stroke(); }
      } else {
        waiting(R.x0 + w * 0.12, R.x0 + w * 0.26, 1);
        for (var wc = 0; wc < 2; wc++) { var wx = R.x0 + w * (0.48 + wc * 0.28), e = crew[3 + wc]; e.hairCol = '#cfcfcf';
          c.strokeStyle = '#3a3a44'; c.lineWidth = 2; c.beginPath(); c.arc(wx, R.y1 - hh * 0.12, hh * 0.12, 0, TAU); c.stroke(); sitAt(c, wx, R.y1 - hh * 0.02, hh * 0.84, e, -1);
          if (wc) { var cg = dress(crew[0], '#7fbfd8', '#2a3a5a', 2); cg.dir = -1; person(c, wx + hh * 0.42, R.y1, hh * 0.95, { lean: 0.2, legs: [0.1 + Math.sin(t / 1400) * 0.03, 0, -0.1 - Math.sin(t / 1400) * 0.03, 0], arms: [1.2, 0.4, 1.1, 0.4] }, cg); } }
      }
      if (kindC !== 'care' && kindC !== 'skin' && kindC !== 'thai' && kindC !== 'chinese' && w > hh * 3.2) { nurse.dir = 1; var nm = person(c, R.x0 + w * 0.5, R.y1, hh * 0.9, stand(0.05), nurse); nurseCap(c, nm, hh * 0.9); fr(c, R.x0 + w * 0.44, R.y1 - hh * 0.46, w * 0.13, hh * 0.46, nt(S, '#c9a36a')); fr(c, R.x0 + w * 0.43, R.y1 - hh * 0.48, w * 0.15, hh * 0.04, nt(S, '#f4f4f4')); }
    }
  });
}

/* ---------------------------------------------------------------- dentist
   The chair laid back under its lamp, the dentist and the nurse in masks on either side, the
   drill's hum a jitter of ±1 px at 40 Hz, the rinse cup filling; a big tooth on the bracket */
function dentist(S) {
  shopScene(S, 'dentist', {
    kinds: ['shop', 'glass', 'glass', 'shop', 'row'], back: '#e8f4f8', floor: '#dfe8ec', icon: ICON.tooth, iconBg: '#e8f4fb',
    room: function (q, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, cx = R.x0 + w * 0.56, o = { cx: cx };
      poster(q, S, R.x0 + w * 0.08, R.y0 + hh * 0.08, hh * 0.32, hh * 0.32, '#f8f8f4', function (p, x, y, ww, h) { ICON.tooth(p, S, x + ww / 2, y + h / 2, ww * 0.35); });
      fr(q, R.x1 - w * 0.22, R.y0 + hh * 0.1, hh * 0.42, hh * 0.28, '#f4f8ff'); for (var k = 0; k < 4; k++) fr(q, R.x1 - w * 0.22 + hh * (0.04 + k * 0.095), R.y0 + hh * 0.15, hh * 0.07, hh * 0.18, '#3a4250');
      /* the chair: base, seat, back laid at 30°, the lamp on its arm */
      fr(q, cx - hh * 0.06, R.y1 - hh * 0.22, hh * 0.12, hh * 0.22, '#d8dce4');
      fp(q, [[cx - hh * 0.45, R.y1 - hh * 0.3], [cx + hh * 0.35, R.y1 - hh * 0.3], [cx + hh * 0.35, R.y1 - hh * 0.22], [cx - hh * 0.45, R.y1 - hh * 0.22]], '#3ab0b8');
      fp(q, [[cx - hh * 0.45, R.y1 - hh * 0.3], [cx - hh * 0.85, R.y1 - hh * 0.52], [cx - hh * 0.8, R.y1 - hh * 0.58], [cx - hh * 0.4, R.y1 - hh * 0.36]], '#3ab0b8');
      ln(q, [[cx + hh * 0.42, R.y1], [cx + hh * 0.42, R.y0 + hh * 0.15], [cx - hh * 0.4, R.y0 + hh * 0.22]], '#c8ccd4', 2.5); el(q, cx - hh * 0.45, R.y0 + hh * 0.26, hh * 0.1, hh * 0.05, 0, '#f4f4f4');
      fr(q, cx + hh * 0.45, R.y1 - hh * 0.5, hh * 0.25, hh * 0.04, '#d8dce4'); fr(q, cx + hh * 0.56, R.y1 - hh * 0.5, 3, hh * 0.5, '#9a9aa2');
      bench(q, S, R.x0 + w * 0.04, R.x0 + w * 0.22, R.y1, hh);
      return o;
    },
    work: function (c, S, R, L, o) {
      var hh = S.hh, w = R.x1 - R.x0, t = S.t, crew = crowd(S, 4, { casual: 1 }), cx = o.cx;
      var lamp = [cx - hh * 0.45, R.y0 + hh * 0.3]; c.fillStyle = 'rgba(255,250,220,.22)'; fp(c, [[lamp[0] - hh * 0.06, lamp[1]], [lamp[0] + hh * 0.06, lamp[1]], [cx - hh * 0.45, R.y1 - hh * 0.5], [cx - hh * 0.85, R.y1 - hh * 0.5]], 'rgba(255,250,220,.25)');
      var pt = crew[0]; pt.garb = 'casual'; pt.dir = 1; person(c, cx - hh * 0.36, R.y1 - hh * 0.3 + hh * 0.86 * 0.08, hh * 0.86, { lean: -1.08, seat: 0.08, legs: [1.5, 0.05, 1.42, 0.1], arms: [-0.5, 1.6, -0.4, 1.7] }, pt);
      var jit = Math.sin(t / 25) * 1, dd = dress(crew[1], '#3ab0b8', '#3ab0b8', 0); dd.dir = -1;
      var me = person(c, cx - hh * 0.2, R.y1 - hh * 0.02, hh * 0.9, { lean: 0.6, seat: 0.34, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.6, 0.3, 1.3, 0.5] }, dd); mask(c, me, hh * 0.9, -1);
      ln(c, [[me.hand[0][0] + jit, me.hand[0][1]], [cx - hh * 0.62 + jit, R.y1 - hh * 0.6]], '#c8ccd4', 2);
      if (w > hh * 2.8) { var as = dress(crew[2], '#f2b8c8', '#f2b8c8', 2); as.dir = 1; var me2 = person(c, cx - hh * 1.1, R.y1, hh * 0.88, { lean: 0.35, legs: [0.06, 0, -0.06, 0], arms: [1.4, 0.4, 0.5, 0.4] }, as); mask(c, me2, hh * 0.88, 1); ln(c, [me2.hand[0], [cx - hh * 0.8, R.y1 - hh * 0.6]], '#9a9aa2', 1.5); }
      var fill = (t / 6000) % 1; fr(c, cx + hh * 0.5, R.y1 - hh * 0.6, hh * 0.08, hh * 0.1, 'rgba(255,255,255,.7)'); fr(c, cx + hh * 0.5, R.y1 - hh * 0.6 + hh * 0.1 * (1 - fill), hh * 0.08, hh * 0.1 * fill, 'rgba(120,190,230,.8)');
      var kid = crew[3]; sitAt(c, R.x0 + w * 0.13, R.y1 - hh * 0.02, hh * 0.62, kid, 1, [1.6 + Math.sin(t / 700) * 0.3, 0.6, 0.3, 0.7]);
    }
  });
}

/* ---------------------------------------------------------------- optician
   Frames on the wall in rows, the tumbling-E chart, someone at the mirror trying a pair (the head
   turns every three seconds), the refractor's light blinking; a pair of glasses on the bracket */
function optician(S) {
  var P = placeOf(S), tint = P.brand || /ท็อปเจริญ|top ?charoen/i.test(words(P)) ? '#e07a2a' : null;
  shopScene(S, 'optician', {
    kinds: ['shop', 'glass', 'shop', 'row'], back: '#f4f0e8', icon: ICON.glasses, signCol: function (L) { return tint || '#2a3a5a'; },
    room: function (q, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, o = {}, fx0 = R.x0 + w * 0.05, fx1 = R.x0 + w * 0.58;
      for (var row = 0; row < 3; row++) { var y = R.y0 + hh * (0.12 + row * 0.16); fr(q, fx0, y + hh * 0.07, fx1 - fx0, 2, '#c8b89a');
        for (var x = fx0 + hh * 0.08; x < fx1 - hh * 0.08; x += hh * 0.2) { var col = ['#2a2a30', '#8a3a2a', '#c9a36a', '#3a5a8a', '#e5567f'][Math.round(x * 7 + row) % 5]; q.strokeStyle = col; q.lineWidth = 1.4; q.beginPath(); q.arc(x - hh * 0.035, y + hh * 0.03, hh * 0.03, 0, TAU); q.moveTo(x + hh * 0.065, y + hh * 0.03); q.arc(x + hh * 0.035, y + hh * 0.03, hh * 0.03, 0, TAU); q.stroke(); } }
      /* the chart: E's that shrink by rows, turned by the row */
      var ex = R.x1 - w * 0.22, ey = R.y0 + hh * 0.1; fr(q, ex, ey, hh * 0.38, hh * 0.52, '#fbfbf6'); q.strokeStyle = '#8a8a92'; q.lineWidth = 1; q.strokeRect(ex, ey, hh * 0.38, hh * 0.52);
      for (var r2 = 0; r2 < 5; r2++) { var n = r2 + 1, s2 = hh * (0.11 - r2 * 0.018); for (var k = 0; k < n; k++) { var cx = ex + hh * 0.19 + (k - (n - 1) / 2) * s2 * 1.5, cy = ey + hh * (0.08 + r2 * 0.095); q.save(); q.translate(cx, cy); q.rotate(((k + r2 * 3) % 4) * Math.PI / 2); fr(q, -s2 / 2, -s2 / 2, s2 * 0.25, s2, '#1a1a22'); for (var b = 0; b < 3; b++) fr(q, -s2 / 2, -s2 / 2 + b * s2 * 0.375, s2, s2 * 0.25, '#1a1a22'); q.restore(); } }
      /* the counter and its mirror */
      fr(q, R.x0 + w * 0.08, R.y1 - hh * 0.4, w * 0.4, hh * 0.4, '#c9a36a'); fr(q, R.x0 + w * 0.07, R.y1 - hh * 0.43, w * 0.42, hh * 0.04, '#f4f4f4');
      fr(q, R.x0 + w * 0.36, R.y1 - hh * 0.72, hh * 0.18, hh * 0.28, '#d8e8f0'); q.strokeStyle = '#c9a36a'; q.strokeRect(R.x0 + w * 0.36, R.y1 - hh * 0.72, hh * 0.18, hh * 0.28);
      fr(q, R.x1 - w * 0.3, R.y1 - hh * 0.42, hh * 0.4, hh * 0.04, '#d8dce4'); fr(q, R.x1 - w * 0.3 + hh * 0.18, R.y1 - hh * 0.42, 3, hh * 0.42, '#9a9aa2'); fr(q, R.x1 - w * 0.3 + hh * 0.05, R.y1 - hh * 0.6, hh * 0.22, hh * 0.18, '#e8e8f0');
      o.mirror = R.x0 + w * 0.36; o.ref = [R.x1 - w * 0.3 + hh * 0.05, R.y1 - hh * 0.52];
      return o;
    },
    work: function (c, S, R, L, o) {
      var hh = S.hh, w = R.x1 - R.x0, t = S.t, crew = crowd(S, 3, { casual: 1 });
      var turn = Math.floor(t / 3000) % 2 ? 1 : -1, cu = crew[0]; cu.dir = turn > 0 ? -1 : 1;
      var me = person(c, o.mirror - hh * 0.25, R.y1 + hh * 0.02, hh * 0.92, stand(0.05), cu);
      c.strokeStyle = '#8a3a2a'; c.lineWidth = 1.4; c.beginPath(); c.arc(me.head[0] + cu.dir * hh * 0.045, me.head[1] - hh * 0.005, hh * 0.028, 0, TAU); c.stroke();
      var op = dress(crew[1], '#f8f8f4', '#2a2a30', 2); op.dir = -1; var me2 = person(c, o.ref[0] - hh * 0.25, R.y1, hh * 0.92, { lean: 0.15, seat: 0.36, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.3, 0.5, 0.4, 0.6] }, crew[2]);
      if (Math.sin(t / 300) > 0.6) { glow(c, o.ref[0] + hh * 0.02, o.ref[1], hh * 0.1, '120,255,160', 0.8); }
      var me3 = person(c, o.ref[0] + hh * 0.45, R.y1, hh * 0.95, { lean: 0.1, legs: [0.06, 0, -0.06, 0], arms: [1.2, 0.5, 0.3, 0.3] }, op); coat(c, me3, hh * 0.95, -1);
    }
  });
}

/* ---------------------------------------------------------------- tattoo
   A studio with flash on the wall (a swallow, a rose, a koi, a heart, an anchor, a lotus, a
   star), the client on the bed, the artist's machine buzzing (the needle ±1.5 px at 50 Hz) and
   the line it draws growing along the arm, s = s₀ + vt; brows done lying face up where the
   name says so, a bamboo rod tapping where it says bamboo */
function flash(c, x, y, s, k) {
  var cols = ['#c0392b', '#2a5aa8', '#2f8f5b', '#e8b84a', '#1a1a22'];
  c.save(); c.translate(x, y); c.strokeStyle = '#1a1a22'; c.lineWidth = Math.max(1, s * 0.08); c.fillStyle = cols[k % 5];
  if (k % 7 === 0) { c.beginPath(); c.moveTo(-s, 0); c.quadraticCurveTo(-s * 0.3, -s * 0.5, 0, 0); c.quadraticCurveTo(s * 0.3, -s * 0.5, s, -s * 0.2); c.lineTo(s * 0.3, s * 0.2); c.lineTo(-s * 0.3, s * 0.5); c.closePath(); c.fill(); c.stroke(); }
  else if (k % 7 === 1) { for (var i = 0; i < 5; i++) { c.beginPath(); c.ellipse(Math.cos(i * 1.26) * s * 0.35, Math.sin(i * 1.26) * s * 0.35, s * 0.35, s * 0.25, i * 1.26, 0, TAU); c.fill(); c.stroke(); } c.fillStyle = '#2f8f5b'; c.fillRect(-s * 0.05, s * 0.4, s * 0.1, s * 0.6); }
  else if (k % 7 === 2) { c.beginPath(); c.ellipse(0, 0, s * 0.9, s * 0.4, 0.3, 0, TAU); c.fill(); c.stroke(); c.beginPath(); c.moveTo(-s * 0.8, -s * 0.2); c.lineTo(-s * 1.2, -s * 0.6); c.lineTo(-s * 1.1, s * 0.2); c.closePath(); c.fill(); c.stroke(); }
  else if (k % 7 === 3) { c.fillStyle = '#d9342b'; c.beginPath(); c.moveTo(0, s * 0.8); c.bezierCurveTo(-s * 1.2, -s * 0.1, -s * 0.5, -s * 0.9, 0, -s * 0.3); c.bezierCurveTo(s * 0.5, -s * 0.9, s * 1.2, -s * 0.1, 0, s * 0.8); c.fill(); c.stroke(); }
  else if (k % 7 === 4) { c.beginPath(); c.moveTo(0, -s * 0.9); c.lineTo(0, s * 0.8); c.moveTo(-s * 0.4, -s * 0.5); c.lineTo(s * 0.4, -s * 0.5); c.moveTo(-s * 0.7, s * 0.2); c.quadraticCurveTo(0, s * 1.2, s * 0.7, s * 0.2); c.stroke(); c.beginPath(); c.arc(0, -s * 0.9, s * 0.15, 0, TAU); c.stroke(); }
  else if (k % 7 === 5) { for (i = -2; i <= 2; i++) { c.save(); c.rotate(i * 0.4); c.beginPath(); c.ellipse(0, -s * 0.4, s * 0.18, s * 0.5, 0, 0, TAU); c.fill(); c.stroke(); c.restore(); } }
  else { c.beginPath(); for (i = 0; i < 10; i++) { var a = i / 10 * TAU - Math.PI / 2, rr = i % 2 ? s * 0.4 : s; c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); } c.closePath(); c.fill(); c.stroke(); }
  c.restore();
}
function tattoo(S) {
  var P = placeOf(S), brow = has(P, /คิ้ว|brow|ปาก|lip|permanent make/i), bamboo = has(P, /bamboo|ไม้ไผ่|สักมือ|hand ?poke/i);
  shopScene(S, 'tattoo', {
    kinds: ['shop', 'row', 'shop', 'glass', 'teak'], wall: function (r) { return pick(r, ['#2a2a30', '#5a2a2a', '#3a4a3a', '#f2e6c9', '#8a6a5a', '#3a3a5a']); }, back: '#2a2630', floor: '#3a3440', icon: ICON.machine, signCol: function () { return '#1a1a22'; },
    keyOf: function () { return (brow ? 'b' : '') + (bamboo ? 'm' : ''); },
    room: function (q, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, s = hh * 0.1, k = S.seed % 7;
      fr(q, R.x0, R.y0, w, R.y1 - R.y0, brow ? '#f4e8ec' : S.seed % 3 ? '#2a2630' : '#7a3a2a');
      for (var row = 0; row < 2; row++) for (var x = R.x0 + hh * 0.18; x < R.x1 - hh * 0.15; x += hh * 0.34) { fr(q, x - hh * 0.14, R.y0 + hh * (0.08 + row * 0.32), hh * 0.28, hh * 0.28, '#f4ecd8'); flash(q, x, R.y0 + hh * (0.22 + row * 0.32), s, k++); }
      fr(q, R.x0 + w * 0.3, R.y1 - hh * 0.3, w * 0.42, hh * 0.08, '#1a1a22'); fr(q, R.x0 + w * 0.32, R.y1 - hh * 0.22, 3, hh * 0.22, '#8a8a92'); fr(q, R.x0 + w * 0.69, R.y1 - hh * 0.22, 3, hh * 0.22, '#8a8a92');
      fr(q, R.x1 - w * 0.16, R.y1 - hh * 0.45, hh * 0.25, hh * 0.04, '#8a8a92'); for (var i = 0; i < 5; i++) fr(q, R.x1 - w * 0.16 + i * hh * 0.045, R.y1 - hh * 0.53, hh * 0.03, hh * 0.08, ['#1a1a22', '#c0392b', '#2a5aa8', '#e8b84a', '#2f8f5b'][i]);
      if (!brow && S.seed % 2) { fr(q, R.x0 + w * 0.04, R.y1 - hh * 0.32, w * 0.2, hh * 0.18, '#7a3a2a'); fr(q, R.x0 + w * 0.04, R.y1 - hh * 0.42, hh * 0.06, hh * 0.28, '#7a3a2a'); }
      return {};
    },
    work: function (c, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, t = S.t, crew = crowd(S, 3, { casual: 1 }), cl = crew[0], art = crew[1], by = R.y1 - hh * 0.3;
      cl.garb = 'casual'; cl.long = false;
      var me = lyingDown(c, R.x0 + w * 0.32, by - hh * 0.06, hh * 0.86, cl);
      art.garb = 'casual'; art.col = '#1a1a22'; art.low = '#2a2a30'; art.long = false; art.dir = -1;
      var tx = brow ? R.x0 + w * 0.36 : R.x0 + w * 0.5, ty = by - hh * 0.1, ax = tx + hh * 0.42, jb = Math.sin(t / 20) * 1.2;
      var tip = bamboo ? [tx + hh * 0.06, ty - hh * 0.06 - Math.abs(Math.sin(t / 1000 * Math.PI * 3)) * hh * 0.05] : [tx + hh * 0.07 + jb * 0.3, ty - hh * 0.08 + jb];
      var aP = { lean: 0.5, seat: 0.36, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.45, 0.5, 1.2, 0.6] }, a = person(c, ax, R.y1, hh * 0.9, reach(ax, R.y1, hh * 0.9, aP, -1, tip, [tx - hh * 0.06, ty - hh * 0.02]), art);
      if (bamboo) ln(c, [[tx, ty], [tip[0] + hh * 0.3, tip[1] - hh * 0.22]], '#c9a36a', 2.5);
      else { ln(c, [[tx + jb * 0.2, ty], [tip[0] + hh * 0.1, tip[1] - hh * 0.07]], '#2a2a30', 3.2); fr(c, tip[0] + hh * 0.02, tip[1] - hh * 0.09, hh * 0.07, hh * 0.05, '#c0392b');
        c.strokeStyle = 'rgba(255,255,255,.7)'; c.lineWidth = 1; for (var b = 0; b < 3; b++) { c.beginPath(); c.arc(tx, ty, 3 + b * 3 + (t / 30) % 3, -2.4, -0.8); c.stroke(); } }
      var u = (t / 9000) % 1; ln(c, [[tx - hh * 0.25, ty + 2], [tx - hh * 0.25 + u * hh * 0.25, ty + 2 - Math.sin(u * 6) * 2]], '#1a1a22', 1.5);
      if (S.night) glow(c, tx, ty - hh * 0.3, hh * 0.5, '255,240,200', 0.35);
      if (w > hh * 3) { var fr2 = crew[2]; sitAt(c, R.x0 + w * 0.12, R.y1 - hh * 0.04, hh * 0.86, fr2, 1, [1.2, 1.2, 0.3, 0.7]); }
    }
  });
}

/* ---------------------------------------------------------------- driving school
   The yard as the school runs it (Nan, 2026-10-15: "They teach car and scootering skills. Active
   instruction", with her photo of a class): learners in numbered bibs and helmets ride a loop
   under a steel canopy, slow along the narrow plank (x = p − a(sin 2π(p − ¼) + 1)/2π, slowest
   at its middle) and weaving the cones (y = A·sin πx/g); the instructor turns to whoever is
   nearest and calls to them; the next riders wait at the line. Beside the canopy a learner car
   with its roof sign drives past the striped-pole bay, backs into it, waits, pulls out and backs
   up to go again. The school is two yellow storeys behind its yellow board; golden trumpet
   trees flower over the wall. Shut: the scooters stand in a row and the car sits in the bay. */
var BIB = [['#8ed04a', null], ['#f0622a', '#e8f04a']];   /* the vest, its reflective bands */
var DRIVE_SAY = [['มองไกล ๆ', 'look ahead'], ['ช้า ๆ นิ่ง ๆ', 'slow and steady'], ['ดีมาก!', 'well done!'], ['เลี้ยวกว้าง ๆ', 'turn wide']];
function tabebuia(c, S, x, y, s, k) {
  /* เหลืองปรีดียาธร: a grey trunk, a loose green crown, and the yellow trumpets all over it */
  paper(c, poly([[x - s * 0.06, y], [x - s * 0.04, y - s * 0.7], [x - s * 0.26, y - s * 0.98], [x - s * 0.2, y - s * 1.02], [x, y - s * 0.8], [x + s * 0.22, y - s * 1.04], [x + s * 0.27, y - s * 0.98], [x + s * 0.05, y - s * 0.7], [x + s * 0.07, y]]), nt(S, '#8a8478'), 1);
  paper(c, function (q) { var pts = []; for (var i = 0; i <= 36; i++) { var a = Math.PI + i / 36 * Math.PI, rr = s * (0.72 + 0.1 * Math.sin(i * 2.3 + k)); pts.push([x + Math.cos(a) * rr, y - s * 1.0 + Math.sin(a) * rr * 0.7]); } pts.push([x + s * 0.7, y - s * 0.86], [x - s * 0.7, y - s * 0.86]); jag(q, pts, 30 + k, 3); }, nt(S, '#5a8a3a'), 1.2);
  var r = rnd(k * 31 + 7);
  for (var i = 0; i < 70; i++) { var a = Math.PI + r() * Math.PI, rr = s * 0.68 * Math.sqrt(r()); dot(c, x + Math.cos(a) * rr, y - s * 1.0 + Math.sin(a) * rr * 0.68 + s * 0.08, s * (0.035 + r() * 0.025), nt(S, r() < 0.7 ? '#f6c81e' : '#e8a812')); }
}
function cone(c, S, x, y, s) {
  fp(c, [[x - s * 0.09, y], [x - s * 0.025, y - s * 0.24], [x + s * 0.025, y - s * 0.24], [x + s * 0.09, y]], nt(S, '#f0662a'));
  fr(c, x - s * 0.055, y - s * 0.14, s * 0.11, s * 0.035, nt(S, '#f4f4f4')); fr(c, x - s * 0.12, y - s * 0.02, s * 0.24, s * 0.03, nt(S, '#d9542a'));
}
function stripedPole(c, S, x, y, s) {
  var h = s * 0.62, w = Math.max(2, s * 0.045);
  fr(c, x - w * 1.6, y - w * 0.6, w * 3.2, w * 0.9, nt(S, '#5a5a62'));
  for (var i = 0; i < 6; i++) fr(c, x - w / 2, y - h + i * h / 6, w, h / 6 + 0.5, nt(S, i % 2 ? '#f4f4f4' : '#d9342b'));
}
/* the bib on the learner's back: the vest over the torso, a white square, the number in red */
function bib(c, x, y, s, k, dir, n, kind) {
  var V = BIB[kind], X = function (u) { return x + dir * k * u * s; }, Y = function (v) { return y + k * v * s; };
  c.save(); c.lineCap = 'round';
  ln(c, [[X(-0.155), Y(-0.6)], [X(-0.13), Y(-0.8)]], V[0], Math.max(2.5, s * k * 0.12));
  if (V[1]) { ln(c, [[X(-0.2), Y(-0.66)], [X(-0.09), Y(-0.67)]], V[1], Math.max(1, s * k * 0.018)); ln(c, [[X(-0.19), Y(-0.75)], [X(-0.08), Y(-0.76)]], V[1], Math.max(1, s * k * 0.018)); }
  var b = s * k * 0.085, bx = X(-0.19), by = Y(-0.71);
  fr(c, bx - b / 2, by - b / 2, b, b, '#f4f4f4'); fr(c, bx - b * 0.38, by - b * 0.38, b * 0.76, b * 0.76, '#c62a20');
  if (b > 7) txt(c, String(n), bx, by + 0.5, b * 0.62, '#ffffff', 800);
  c.restore();
}
var SCOOTCOL = ['#c62a20', '#1f1f24', '#f4f2ee', '#2c4e9b', '#e5567f', '#8a9099', '#2f8f5b', '#e8a83a'];
function rideScooter(c, S, x, y, s, k, dir, d, o) {
  if (!K.scooter) {   /* the kit without its step-through: the street's motorbike, the rider astride, a helmet */
    c.save(); c.translate(x, y); if (o.tilt) c.rotate(o.tilt); c.scale(k, k);
    motorbike(c, S, 0, 0, s * 1.2, dir, SCOOTCOL[(o.col || 0) % SCOOTCOL.length]);
    if (d) { d.dir = dir; var me = person(c, -dir * s * 0.06, -s * 0.22, s * 0.8, { lean: 0.15, seat: 0.3, legs: [1.2, -1.0, 1.1, -1.1], arms: [1.3, 0.3, 1.2, 0.35] }, d);
      el(c, me.head[0], me.head[1] - s * 0.02, s * 0.1, s * 0.09, 0, o.helmet || '#f4efe2');
      if (o.n) { ln(c, [me.hip, me.sh], BIB[o.vest || 0][0], Math.max(2.5, s * 0.1)); var b = s * 0.075; fr(c, me.sh[0] - dir * b * 0.6 - b / 2, (me.sh[1] + me.hip[1]) / 2 - b / 2, b, b, '#c62a20'); } }
    c.restore(); return;
  }
  c.save(); c.translate(x, y); if (o.tilt) c.rotate(o.tilt); c.scale(dir * k, k);
  K.scooter(c, s, { k: o.col, auto: true, rider: d, helmets: d ? [o.helmet] : null, th: o.th || 0, night: S.night, t: S.t });
  c.restore();
  if (d && o.n) bib(c, x, y, s, k, dir, o.n, o.vest);
}
function bubble(c, S, x, y, say, px) {
  c.save(); c.font = '800 ' + Math.round(px) + 'px "Sarabun",system-ui,sans-serif'; var w1 = c.measureText(say[0]).width;
  c.font = '700 ' + Math.round(px * 0.72) + 'px "Sarabun",system-ui,sans-serif'; var w2 = c.measureText(say[1]).width;
  var w = Math.max(w1, w2) + px * 1.1, h = px * 2.3, bx = x - w * 0.3, by = y - h - px * 0.6;
  paper(c, function (q) { q.beginPath(); var rr = px * 0.5; q.moveTo(bx + rr, by); q.lineTo(bx + w - rr, by); q.quadraticCurveTo(bx + w, by, bx + w, by + rr); q.lineTo(bx + w, by + h - rr); q.quadraticCurveTo(bx + w, by + h, bx + w - rr, by + h);
    q.lineTo(x + px * 0.5, by + h); q.lineTo(x, y); q.lineTo(x + px * 0.05, by + h); q.lineTo(bx + rr, by + h); q.quadraticCurveTo(bx, by + h, bx, by + h - rr); q.lineTo(bx, by + rr); q.quadraticCurveTo(bx, by, bx + rr, by); q.closePath(); }, '#fffdf4', 1);
  c.restore();
  txt(c, say[0], bx + w / 2, by + h * 0.36, px, '#2a2a30', 800); txt(c, say[1], bx + w / 2, by + h * 0.72, px * 0.72, '#6a5a4a', 700);
}
/* the school's car: a white sedan, its roof sign, the learner at the wheel and the teacher beside */
function learnerCar(c, S, x, y, s, o) {
  var L = 1.05, X = function (u) { return x + u * s; }, gl = S.night ? '#2a3550' : '#9fc4d4', body = nt(S, '#f4f2ec');
  c.save(); c.translate(x, y); if (o.tilt) c.rotate(o.tilt); c.translate(-x, -y);
  c.fillStyle = 'rgba(0,0,0,.18)'; c.beginPath(); c.ellipse(x, y - s * 0.02, L * s * 1.02, s * 0.06, 0, 0, TAU); c.fill();
  /* the roof sign */
  paper(c, rect(X(-0.2), y - s * 0.6, s * 0.4, s * 0.12), nt(S, '#f2c94c'), 0.8); fr(c, X(-0.14), y - s * 0.48, s * 0.03, s * 0.03, '#5a5a62'); fr(c, X(0.11), y - s * 0.48, s * 0.03, s * 0.03, '#5a5a62');
  if (s > 50) txt(c, 'สอนขับรถ', x, y - s * 0.54, s * 0.085, nt(S, '#c62a20'), 800);
  paper(c, poly([[X(-L), y - s * 0.12], [X(-L), y - s * 0.28], [X(-L * 0.55), y - s * 0.3], [X(-L * 0.3), y - s * 0.46], [X(L * 0.25), y - s * 0.46], [X(L * 0.5), y - s * 0.3], [X(L), y - s * 0.26], [X(L), y - s * 0.12]]), body, 1);
  var win = [[X(-L * 0.25), y - s * 0.31], [X(-L * 0.12), y - s * 0.43], [X(L * 0.22), y - s * 0.43], [X(L * 0.4), y - s * 0.31]];
  fp(c, win, gl); fp(c, [[X(-L * 0.5), y - s * 0.31], [X(-L * 0.3), y - s * 0.43], [X(-L * 0.28), y - s * 0.31]], gl);
  /* the two heads in the front window: the learner at the wheel on the far side, the teacher near */
  c.save(); c.beginPath(); win.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.clip();
  dot(c, X(0.1), y - s * 0.37, s * 0.055, nt(S, '#3a2a22')); fr(c, X(0.06), y - s * 0.33, s * 0.08, s * 0.05, nt(S, o.studentCol));
  dot(c, X(-0.03 + (o.point || 0) * 0.02), y - s * 0.355, s * 0.06, nt(S, '#1c1410')); fr(c, X(-0.08), y - s * 0.31, s * 0.1, s * 0.05, nt(S, '#e5567f'));
  c.restore();
  ln(c, [[X(-0.02), y - s * 0.31], [X(-0.02), y - s * 0.14]], 'rgba(0,0,0,.3)', 1);
  fr(c, X(-L * 0.9), y - s * 0.2, L * 1.8 * s, s * 0.02, nt(S, '#d9342b'));   /* the school's stripe */
  /* lamps: the head lamp, the tail lamp bright on the brake, the white reversing lamp */
  el(c, X(L - 0.02), y - s * 0.24, s * 0.035, s * 0.025, 0, S.night ? '#fff2b0' : '#f2f2e8');
  el(c, X(-L + 0.02), y - s * 0.24, s * 0.03, s * 0.03, 0, o.brake ? '#ff3a2a' : '#a8241c');
  if (o.brake) glow(c, X(-L), y - s * 0.24, s * 0.2, '255,60,40', 0.45);
  el(c, X(-L + 0.02), y - s * 0.17, s * 0.025, s * 0.02, 0, o.rev ? '#ffffff' : '#c8c8c8');
  if (o.rev) glow(c, X(-L), y - s * 0.17, s * 0.25, '255,255,235', 0.6);
  [-L * 0.62, L * 0.62].forEach(function (u) { var wx = X(u), wy = y - s * 0.14, rr = s * 0.14; dot(c, wx, wy, rr, '#1e1e24'); dot(c, wx, wy, rr * 0.55, nt(S, '#b8bcc4'));
    c.strokeStyle = '#6a6a72'; c.lineWidth = 1; c.beginPath(); for (var j = 0; j < 3; j++) { var a = (o.th || 0) + j * TAU / 3; c.moveTo(wx, wy); c.lineTo(wx + Math.cos(a) * rr * 0.55, wy + Math.sin(a) * rr * 0.55); } c.stroke(); });
  c.restore();
}
function drive(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'drive'), P = L.P, r = L.r, st = L.st, t = S.t, H = S.H;
  var open = st.open && !S.night;
  var yb = S.deck - hh * 0.5, cx0 = S.x0 + S.span * 0.015, cx1 = S.x0 + S.span * 0.6, yr = yb - hh * 1.2;
  var bw = Math.min(S.span * 0.36, hh * 3.8), bx0 = S.x0 + S.span * 0.06, bx1 = bx0 + bw;
  var yF = S.deck + hh * 0.16, yB = yb + hh * 0.18, ox0 = cx0 + hh * 2.05, ox1 = cx1 - hh * 0.6, R = hh * 0.3;
  var cs = hh * 0.86, Lc = 2.1 * cs, xc = Math.min(S.x1 - Lc * 1.08, Math.max(cx1 + Lc * 0.9, (cx1 + S.x1) / 2)), yC = Math.min(H - hh * 0.06, S.deck + hh * 0.62), yBay = yb + hh * 0.26;
  var plank = [lerp(ox0, ox1, 0.06), lerp(ox0, ox1, 0.38)], cones = [];
  for (var ci = 0; ci < 5; ci++) cones.push(lerp(ox0, ox1, 0.5 + ci * 0.1));
  var gap = cones[1] - cones[0];
  var still = layer(S, 'drive|' + (open ? 1 : 0), stageBox(S), function (q) {
    var o = {};
    /* the school: two yellow storeys, green glass in white frames, a low tiled roof */
    var top = yb - hh * 1.55, fl = (yb - top) / 2;
    paper(q, poly([[bx0 - hh * 0.1, top], [bx0 + hh * 0.2, top - hh * 0.22], [bx1 - hh * 0.2, top - hh * 0.22], [bx1 + hh * 0.1, top]]), nt(S, '#b8604a'), 1);
    paper(q, rect(bx0, top, bw, yb - top), nt(S, '#f4d23e'), 1);
    for (var f = 0; f < 2; f++) for (var w = 0; w < Math.max(2, Math.floor(bw / (hh * 0.55))); w++) {
      var nw = Math.max(2, Math.floor(bw / (hh * 0.55))), wx = bx0 + hh * 0.18 + w * (bw - hh * 0.36) / nw, ww = (bw - hh * 0.36) / nw - hh * 0.1, wy = top + f * fl + fl * 0.22;
      fr(q, wx - 1.5, wy - 1.5, ww + 3, fl * 0.5 + 3, nt(S, '#f8f6ee')); fr(q, wx, wy, ww, fl * 0.5, S.night && open ? '#ffe6a0' : nt(S, '#4f9a6a')); fr(q, wx + ww / 2 - 0.75, wy, 1.5, fl * 0.5, nt(S, '#f8f6ee'));
    }
    for (var pl = 0; pl < 3; pl++) fr(q, bx0 + pl * (bw - hh * 0.08) / 2, top, hh * 0.08, yb - top, nt(S, '#f8e27a'));
    fr(q, bx0, top + fl - 2, bw, 4, nt(S, '#f8e27a'));
    /* trees: golden trumpets over the wall, a banana by the yard */
    tabebuia(q, S, bx1 + hh * 0.75, yb, hh * 1.25, S.seed % 9);
    tabebuia(q, S, S.x1 - hh * 0.7, yb, hh * 1.15, (S.seed >>> 2) % 9 + 3);
    banana(q, S, bx1 + hh * 1.6, yb, hh * 0.95, 1);
    /* the board in front of the school: yellow, a red band along its foot */
    var th = P.nameTh || P.name || '', en = P.nameEn && P.nameEn !== th ? P.nameEn : '', px = Math.max(9, hh * 0.17);
    q.font = '800 ' + Math.round(px) + 'px "Sarabun",system-ui,sans-serif'; var tw = q.measureText(th).width;
    var sw = Math.min(bw * 0.95, Math.max(hh * 1.6, tw + hh * 0.4)), sh = hh * (en ? 0.62 : 0.46), sx = (bx0 + bx1) / 2 - sw / 2, sy = yb - hh * 0.12 - sh;
    fr(q, sx + sw * 0.12, sy + sh, 3, yb - sy - sh, nt(S, '#8a8a92')); fr(q, sx + sw * 0.88 - 3, sy + sh, 3, yb - sy - sh, nt(S, '#8a8a92'));
    paper(q, rect(sx, sy, sw, sh), nt(S, '#f6e24a'), 1.2); fr(q, sx, sy + sh * 0.78, sw, sh * 0.22, nt(S, '#d9342b'));
    txt(q, th.length > 30 ? th.slice(0, 29) + '…' : th, sx + sw / 2, sy + sh * (en ? 0.24 : 0.36), px, '#1e1e24', 800);
    if (en) txt(q, en.length > 36 ? en.slice(0, 35) + '…' : en, sx + sw / 2, sy + sh * 0.56, px * 0.66, '#1e1e24', 700);
    txt(q, 'รถยนต์ · จักรยานยนต์', sx + sw / 2, sy + sh * 0.89, Math.max(7, px * 0.5), '#ffffff', 700);
    o.sign = [sx, sx + sw];
    /* the yard: concrete, the canopy's floor a shade darker, painted lines */
    paper(q, rect(S.x0 - 6, yb, S.span + 12, H - yb + 6), nt(S, '#bdb7aa'), 1.2);
    fr(q, cx0, yb, cx1 - cx0, H - yb, nt(S, '#aaa497'));
    ln(q, [[ox0 - R, yF + hh * 0.04], [ox1 + R, yF + hh * 0.04]], nt(S, '#e8c43a'), Math.max(1.5, hh * 0.025));
    ln(q, [[cx0 + hh * 1.55, yB - hh * 0.04], [cx0 + hh * 1.55, yF + hh * 0.2]], nt(S, '#f4f4f4'), Math.max(2, hh * 0.04));   /* the start line */
    ln(q, [[cx1 + hh * 0.2, yC + hh * 0.03], [S.x1 + 6, yC + hh * 0.03]], nt(S, '#e8c43a'), Math.max(1.5, hh * 0.025));
    /* the bay, painted on the concrete */
    q.strokeStyle = nt(S, '#f4f4f4'); q.lineWidth = Math.max(1.5, hh * 0.025); q.strokeRect(xc - Lc * 0.62, yBay - hh * 0.12, Lc * 1.24, hh * 0.26);
    /* the plank the riders cross, raised on its blocks */
    for (var bk = 0; bk < 4; bk++) fr(q, lerp(plank[0], plank[1], bk / 3) - hh * 0.05, yF - hh * 0.06, hh * 0.1, hh * 0.08, nt(S, '#8a8a8a'));
    paper(q, rect(plank[0] - hh * 0.1, yF - hh * 0.1, plank[1] - plank[0] + hh * 0.2, hh * 0.06), nt(S, '#d8b070'), 0.8); fr(q, plank[0] - hh * 0.1, yF - hh * 0.05, plank[1] - plank[0] + hh * 0.2, hh * 0.012, nt(S, '#a8803a'));
    /* the canopy: white posts, a roof sheet, the truss under it (its diagonals), a camera on the beam */
    var pw = Math.max(2.5, hh * 0.06);
    [cx0 + hh * 0.2, sx - hh * 0.15, sx + sw + hh * 0.15, cx1 - hh * 0.2].forEach(function (px2, k2, A) { if (k2 && px2 - A[k2 - 1] < hh * 0.5) return; fr(q, px2 - pw / 2, yr, pw, yb - yr, nt(S, '#eceef0')); });   /* clear of the board */
    fr(q, cx0 - hh * 0.1, yr - hh * 0.32, cx1 - cx0 + hh * 0.2, hh * 0.08, nt(S, '#dfe3e6'));
    ln(q, [[cx0, yr - hh * 0.24], [cx1, yr - hh * 0.24]], nt(S, '#f4f6f8'), pw * 0.7); ln(q, [[cx0, yr], [cx1, yr]], nt(S, '#f4f6f8'), pw * 0.7);
    q.strokeStyle = nt(S, '#f4f6f8'); q.lineWidth = Math.max(1.2, pw * 0.45); q.beginPath();
    for (var tx = cx0, up = 0; tx < cx1; tx += hh * 0.24, up ^= 1) { q.moveTo(tx, up ? yr - hh * 0.24 : yr); q.lineTo(Math.min(cx1, tx + hh * 0.24), up ? yr : yr - hh * 0.24); } q.stroke();
    fr(q, cx1 - hh * 0.62, yr + 1, hh * 0.1, hh * 0.06, nt(S, '#f4f4f4')); dot(q, cx1 - hh * 0.6, yr + hh * 0.05, hh * 0.025, '#2a2a30');
    if (S.night) for (var lp = 0; lp < 3; lp++) { var lx = lerp(cx0 + hh * 0.6, cx1 - hh * 0.6, lp / 2); fr(q, lx - hh * 0.25, yr + 2, hh * 0.5, 3, '#f8fbff'); glow(q, lx, yr + hh * 0.3, hh * 1.0, '235,245,255', 0.35); }
    if (!open) { /* shut: the school's scooters in a row under the canopy */
      for (var sc = 0; sc < 4; sc++) rideScooter(q, S, lerp(ox0, ox1, 0.1 + sc * 0.26), yB + hh * 0.1, hh * 0.72, 0.9, 1, null, { col: [0, 2, 5, 3][sc] });
    }
    return o;
  }).out || {};
  var K2 = function (y) { return lerp(0.84, 1, clamp((y - yb) / (yC - yb), 0, 1)); };
  var cast = crowd(S, 7, { casual: 1 }), items = [];
  /* the poles of the bay: the far pair under everything, the near pair sorted with the car */
  [-1, 1].forEach(function (sd) { items.push({ y: yBay - hh * 0.12, f: function () { stripedPole(c, S, xc + sd * Lc * 0.62, yBay - hh * 0.12, hh * 0.82); } }); items.push({ y: yBay + hh * 0.14, f: function () { stripedPole(c, S, xc + sd * Lc * 0.62, yBay + hh * 0.14, hh * 0.92); } }); });
  cones.forEach(function (x) { items.push({ y: yF, f: function () { cone(c, S, x, yF, hh); } }); });
  /* the car's drill, T = 14 s: wait, forward past the bay, back into it, wait, out, back to the start */
  var T = 14, u = ((t / 1000) % T + T) % T, xa = xc - Lc * 0.36, xbB = Math.min(S.x1 - Lc * 0.5 + hh * 0.3, xc + Lc * 0.6), cx, cy, rev = false, brake = false, tilt = 0, point = 0;
  function seg(a, b) { return ease(clamp((u - a) / (b - a), 0, 1)); }
  if (u < 1) { cx = xa; cy = yC; brake = true; }
  else if (u < 3.5) { cx = lerp(xa, xbB, seg(1, 3.5)); cy = yC; }
  else if (u < 4.2) { cx = xbB; cy = yC; brake = true; }
  else if (u < 7.7) { var q2 = seg(4.2, 7.7); cx = lerp(xbB, xc, q2); cy = lerp(yC, yBay, q2); rev = true; tilt = -0.05 * Math.sin(Math.PI * q2); }
  else if (u < 9.7) { cx = xc; cy = yBay; brake = true; point = 1; }
  else if (u < 12) { var q3 = seg(9.7, 12); cx = lerp(xc, xbB, q3); cy = lerp(yBay, yC, q3); tilt = 0.05 * Math.sin(Math.PI * q3); }
  else { cx = lerp(xbB, xa, seg(12, 14)); cy = yC; rev = true; }
  if (!open) { cx = xc; cy = yBay; rev = false; brake = false; }
  var ck = K2(cy);
  items.push({ y: cy, f: function () { learnerCar(c, S, cx, cy, cs * ck, { rev: rev, brake: brake && open, tilt: tilt, th: cx / (cs * 0.14), studentCol: CLOTH2[S.seed % CLOTH2.length], point: point }); } });
  if (open && !S.phone && u >= 7.9 && u < 9.6) items.push({ y: H + 1, f: function () { bubble(c, S, cx - cs * 0.1, cy - cs * 0.62 * ck, DRIVE_SAY[2], Math.max(9, hh * 0.13)); } });
  if (open) {
    /* the riders on the loop: u ∈ [0, .42) the front run, plank then cones; a turn; the back run; a turn */
    var n = S.phone ? 2 : 3, Tl = 18, riders = [];
    for (var i = 0; i < n; i++) {
      var v = ((t / 1000 / Tl + i / n + (S.seed % 7) * 0.05) % 1 + 1) % 1, x, y, dir, tl = 0, lift = 0, p;
      if (v < 0.42) { p = v / 0.42; var a = 0.62, f2 = p - a * (Math.sin(TAU * (p - 0.25)) + 1) / TAU; x = lerp(ox0, ox1, f2); dir = 1; y = yF;
        if (x > plank[0] && x < plank[1]) { lift = hh * 0.1; tl = 0.05 * Math.sin(t / 260 + i); }
        if (x > cones[0] - gap / 2 && x < cones[cones.length - 1] + gap / 2) { var ph = Math.PI * (x - cones[0] + gap / 2) / gap; y = yF + hh * 0.13 * Math.sin(ph); tl = 0.06 * Math.cos(ph); } }
      else if (v < 0.5) { p = (v - 0.42) / 0.08; x = ox1 + R * Math.sin(Math.PI * p); y = lerp(yF, yB, (1 - Math.cos(Math.PI * p)) / 2); dir = p < 0.5 ? 1 : -1; tl = -0.08 * Math.sin(Math.PI * p) * dir; }
      else if (v < 0.92) { p = (v - 0.5) / 0.42; x = lerp(ox1, ox0, p); y = yB; dir = -1; }
      else { p = (v - 0.92) / 0.08; x = ox0 - R * Math.sin(Math.PI * p); y = lerp(yB, yF, (1 - Math.cos(Math.PI * p)) / 2); dir = p < 0.5 ? -1 : 1; tl = 0.08 * Math.sin(Math.PI * p) * dir; }
      var d = dress(cast[i], ['#2a2a30', '#3a4a6a', '#f4f4f4'][i % 3], ['#2a2a30', '#5a5a62', '#e8e0d0'][i % 3]);
      riders.push({ x: x, y: y, dir: dir });
      (function (x, y, dir, tl, lift, d, i) { items.push({ y: y, f: function () { rideScooter(c, S, x, y - lift, hh * 0.74, K2(y), dir, d, { col: [0, 2, 5, 3][i % 4], helmet: ['#f4efe2', '#2a2a2a', '#7a2a3a'][i % 3], tilt: tl, th: x / (hh * 0.16) * dir, n: [19, 14, 20, 22][i % 4], vest: i === 1 ? 1 : 0 }); } }); })(x, y, dir, tl, lift, d, i);
    }
    /* waiting at the line, engines idling */
    for (var wq = 0; wq < 2; wq++) { var wy2 = lerp(yB, yF, 0.1 + wq * 0.9), wd = dress(cast[3 + wq], ['#f4f4f4', '#2a2a30'][wq], ['#3a4a6a', '#2a2a30'][wq]);
      (function (wy2, wd, wq) { items.push({ y: wy2, f: function () { rideScooter(c, S, cx0 + hh * (1.0 + wq * 0.12), wy2, hh * 0.74, K2(wy2), 1, wd, { col: [7, 1][wq], helmet: ['#c62a20', '#f4efe2'][wq], n: [1, 22][wq], vest: wq }); } }); })(wy2, wd, wq); }
    /* the instructor: pink, a cap and a whistle, turned to the nearest rider, calling to them */
    var ix = lerp(ox0, ox1, 0.44), iy = Math.min(H - hh * 0.04, yF + hh * 0.42), near = riders.slice().sort(function (a, b) { return Math.abs(a.x - ix) - Math.abs(b.x - ix); })[0];
    var idir = near.x >= ix ? 1 : -1, beat = Math.sin(t / 1000 * TAU * 0.7), pointing = Math.abs(near.x - ix) < hh * 2.5;
    var tdr = dress(cast[5], '#e5567f', '#2a2a30', 4); tdr.dir = idir;
    items.push({ y: iy, f: function () {
      var me = person(c, ix, iy, hh * 0.95, { lean: 0.04, legs: [0.12, 0, -0.1, 0], arms: pointing ? [1.5 + beat * 0.15, 0.1 + beat * 0.2, 0.9, 1.6] : [0.3, 0.3, 1.0, 1.7] }, tdr);
      ln(c, [[me.sh[0] - hh * 0.04, me.sh[1] + 1], [me.sh[0], me.sh[1] + hh * 0.12], [me.sh[0] + hh * 0.04, me.sh[1] + 1]], '#2a2a30', 1);
      dot(c, me.hand[1][0], me.hand[1][1], Math.max(1.5, hh * 0.025), '#c8ccd2');   /* the whistle, to the lips and down */
      fr(c, me.hand[0][0] - (pointing ? 0 : hh * 0.06), me.hand[0][1] - hh * 0.02, pointing ? 0 : hh * 0.12, pointing ? 0 : hh * 0.15, '#e8dcc0');
      var say = DRIVE_SAY[[0, 1, 3, 0][Math.floor(t / 5000) % 4]];
      if ((t / 5000) % 1 < 0.7) bubble(c, S, me.head[0] + idir * hh * 0.1, me.head[1] - hh * 0.12, say, Math.max(9, hh * 0.13));
    } });
  } else dog(c, S, (cx0 + cx1) / 2, S.deck + hh * 0.5, hh * 0.6, S.seed >>> 4, true, t);
  items.sort(function (a, b) { return a.y - b.y; }).forEach(function (it) { it.f(); });
  S.hits.push({ k: 'place', x0: S.x0 + hh * 0.6, x1: S.x1 - hh * 0.6, y0: S.deck - hh * 2.0, y1: S.H });
}

/* ---------------------------------------------------------------- training
   A school for one skill, read from the name: music (the piano's keys going down, a guitar
   strummed), a language (the board's letters), the abacus (beads sliding, x = x₀ + d·ease),
   computers (screens), art (easels), tutoring (sums on the board); hands go up in turn. */
function trainKind(P) {
  var w = words(P);
  if (/music|ดนตรี|piano|เปียโน|guitar|กีตาร์|violin|ไวโอลิน|drum|กลอง|sing|ร้อง/i.test(w)) return 'music';
  if (/abacus|จินตคณิต|ลูกคิด|brain|smart ?brain|math|คณิต|เลข/i.test(w)) return 'abacus';
  if (/computer|คอม|coding|code|robot|หุ่นยนต์|it\b|digital|ดิจิทัล|lab/i.test(w)) return 'computer';
  if (/ballet|บัลเลต์|dance|เต้น|นาฏศิลป์|รำ/i.test(w)) return 'dance';
  if (/cook|ทำอาหาร|ครัว|bak|เบเกอรี่|ขนม/i.test(w)) return 'cook';
  if (/\bart\b|ศิลป|วาด|paint|draw|ceramic|เซรามิก|ปั้น/i.test(w)) return 'art';
  if (/english|ภาษา|language|chinese|japan|korean|thai|french|german|esl|ielts|toefl|เกาหลี|ญี่ปุ่น|จีน|อังกฤษ/i.test(w)) return 'lang';
  if (/driv|ขับรถ|ขับขี่/i.test(w)) return 'drive';
  return 'tutor';
}
function training(S) {
  var P = placeOf(S), kindT = trainKind(P);
  if (kindT === 'drive') return drive(S);
  shopScene(S, 'training', {
    kinds: ['shop', 'glass', 'shop', 'row', 'gov'], back: { music: '#f2ead8', art: '#f4f0e8', computer: '#e8eef6' }[kindT] || '#f4f2e8', keyOf: function () { return kindT; },
    icon: kindT === 'music' ? ICON.note : ICON.book,
    room: function (q, S, R, L) {
      var hh = S.hh, w = R.x1 - R.x0, o = {}, bx = R.x0 + w * 0.12, bw = Math.min(w * 0.5, hh * 1.6), by = R.y0 + hh * 0.1, bh = hh * 0.42;
      if (kindT === 'dance') { for (var mp = 0; mp < 4; mp++) fr(q, R.x0 + w * (0.04 + mp * 0.24), R.y0 + hh * 0.06, w * 0.22, R.y1 - R.y0 - hh * 0.2, '#d8eaf2'); ln(q, [[R.x0, R.y1 - hh * 0.5], [R.x1, R.y1 - hh * 0.5]], '#c9a36a', 3); fr(q, R.x0, R.y1 - hh * 0.12, w, hh * 0.12, '#c9a36a'); return o; }
      if (kindT === 'cook') { fr(q, R.x0 + w * 0.1, R.y1 - hh * 0.4, w * 0.8, hh * 0.4, '#d8dce4'); fr(q, R.x0 + w * 0.08, R.y1 - hh * 0.43, w * 0.84, hh * 0.04, '#f4f4f4'); for (var pn = 0; pn < 5; pn++) fr(q, R.x0 + w * (0.12 + pn * 0.16), R.y0 + hh * 0.14, hh * 0.04, hh * 0.18, '#8a8a92'); o.cook = R.y1 - hh * 0.43; return o; }
      if (kindT === 'music') {
        fr(q, R.x0 + w * 0.08, R.y1 - hh * 0.5, hh * 0.9, hh * 0.5, '#1a1a22'); fr(q, R.x0 + w * 0.08, R.y1 - hh * 0.5, hh * 0.9, hh * 0.08, '#f8f8f4'); for (var k = 0; k < 12; k++) fr(q, R.x0 + w * 0.08 + k * hh * 0.075, R.y1 - hh * 0.5, 1, hh * 0.08, '#8a8a92');
        o.keys = [R.x0 + w * 0.08, R.y1 - hh * 0.5];
        for (var s2 = 0; s2 < 5; s2++) ln(q, [[R.x0 + w * 0.45, R.y0 + hh * (0.12 + s2 * 0.04)], [R.x1 - w * 0.08, R.y0 + hh * (0.12 + s2 * 0.04)]], '#3a3a44', 1);
        for (var n = 0; n < 6; n++) { var nx = R.x0 + w * 0.5 + n * w * 0.07, ny = R.y0 + hh * (0.14 + (n * 3 % 5) * 0.04); el(q, nx, ny + hh * 0.02, hh * 0.022, hh * 0.016, -0.4, '#1a1a22'); ln(q, [[nx + hh * 0.02, ny + hh * 0.02], [nx + hh * 0.02, ny - hh * 0.08]], '#1a1a22', 1); }
        el(q, R.x1 - w * 0.12, R.y1 - hh * 0.4, hh * 0.12, hh * 0.16, 0, '#c9733a'); fr(q, R.x1 - w * 0.12 - 2, R.y0 + hh * 0.3, 4, hh * 0.35, '#5a3420');
        return o;
      }
      fr(q, bx - 2, by - 2, bw + 4, bh + 4, '#9a9aa2'); fr(q, bx, by, bw, bh, kindT === 'art' ? '#f4ecd8' : '#fbfbf6');
      var say = { lang: ['A B C', 'ก ข ค'], abacus: ['7 + 8 = 15', '23 × 4'], computer: ['<html>', 'print("hi")'], tutor: ['x² + 2x + 1', '= (x + 1)²'], drive: ['← ↑ →', ''], art: ['', ''] }[kindT];
      txt(q, say[0], bx + bw / 2, by + bh * 0.3, Math.max(8, hh * 0.13), '#2a5aa8', 800); txt(q, say[1], bx + bw / 2, by + bh * 0.7, Math.max(7, hh * 0.1), '#c0392b', 700);
      if (kindT === 'art') { for (var e = 0; e < 2; e++) { var ex = R.x0 + w * (0.55 + e * 0.25); ln(q, [[ex - hh * 0.15, R.y1], [ex, R.y1 - hh * 0.75], [ex + hh * 0.15, R.y1]], '#8a5a3a', 2); fr(q, ex - hh * 0.16, R.y1 - hh * 0.72, hh * 0.32, hh * 0.26, '#fbfbf6'); dot(q, ex - hh * 0.05, R.y1 - hh * 0.6, hh * 0.06, ['#e8b84a', '#4d8fd1'][e]); fr(q, ex - hh * 0.14, R.y1 - hh * 0.54, hh * 0.28, hh * 0.06, ['#2f8f5b', '#e5567f'][e]); } }
      if (kindT === 'computer') for (var m = 0; m < 3; m++) { var mx = R.x0 + w * (0.2 + m * 0.26); fr(q, mx - hh * 0.14, R.y1 - hh * 0.62, hh * 0.28, hh * 0.18, '#2a2a30'); fr(q, mx - hh * 0.12, R.y1 - hh * 0.6, hh * 0.24, hh * 0.14, S.night ? '#7ab0e0' : '#9fd0f0'); fr(q, mx - 2, R.y1 - hh * 0.44, 4, hh * 0.04, '#2a2a30'); }
      if (kindT === 'abacus') o.abacus = [R.x1 - w * 0.3, R.y0 + hh * 0.14, hh * 0.6, hh * 0.32];
      return o;
    },
    work: function (c, S, R, L, o) {
      var hh = S.hh, w = R.x1 - R.x0, t = S.t, crew = crowd(S, 5, { casual: 1 });
      if (kindT === 'music' && o.keys) {
        var st = crew[0]; sitAt(c, o.keys[0] + hh * 0.45, R.y1, hh * 0.78, st, 1, [1.4 + Math.abs(Math.sin(t / 180)) * 0.1, 0.4, 1.3 + Math.abs(Math.cos(t / 210)) * 0.1, 0.5]);
        var key = Math.floor(t / 180) % 12; fr(c, o.keys[0] + key * hh * 0.075, o.keys[1], hh * 0.07, hh * 0.08, '#d8d0b8'); K.notes(c, o.keys[0] + hh * 0.5, o.keys[1] - hh * 0.1, t, 3, '#c0392b');
        var gt = crew[1]; gt.dir = -1; var g = sitAt(c, R.x1 - w * 0.24, R.y1, hh * 0.86, gt, -1, [1.2, 1.0, 0.9 + Math.sin(t / 120) * 0.25, 0.8]);
        el(c, g.hip[0] - hh * 0.06, g.hip[1] - hh * 0.06, hh * 0.13, hh * 0.09, 0.4, '#c9733a'); ln(c, [[g.hip[0] - hh * 0.06, g.hip[1] - hh * 0.06], [g.hip[0] - hh * 0.4, g.hip[1] - hh * 0.25]], '#5a3420', 2);
        return;
      }
      if (kindT === 'dance') { var bt = t / 1000 * TAU / 3, pl = 0.5 - 0.5 * Math.cos(bt); for (var dn = 0; dn < 4; dn++) { var dd = crew[dn]; dd.garb = 'casual'; dd.col = ['#ffd1e8', '#f2f2f2', '#c3a6ff', '#ffd1e8'][dn]; dd.low = dd.skin; dd.dir = 1; dd.hair = 2;
          var mm = person(c, R.x0 + w * (0.16 + dn * 0.22), R.y1 - hh * 0.04, hh * 0.86, { lean: 0, seat: 0.47 - pl * 0.08, legs: [0.25 + pl * 0.3, -pl * 0.6, -0.25 - pl * 0.3, -pl * 0.6], arms: [1.2 + pl * 1.6, 0.4, -1.2 - pl * 1.6, -0.4] }, dd);
          skirt(c, mm, hh * 0.86, '#ffd1e8', 0.3); } return; }
      if (kindT === 'cook' && o.cook) { for (var ck2 = 0; ck2 < 3; ck2++) { var cx2 = R.x0 + w * (0.22 + ck2 * 0.28), cd = dress(crew[ck2], '#f8f8f4', '#3a3a44', ck2 % 4); cd.dir = 1; var ma = person(c, cx2, R.y1 - hh * 0.02, hh * 0.86, { lean: 0.1, legs: [0.06, 0, -0.06, 0], arms: [1.3 + Math.sin(t / 300 + ck2) * 0.25, 0.5, 0.8, 0.6] }, cd);
          fp(c, [[ma.sh[0] - hh * 0.06, ma.sh[1] + hh * 0.04], [ma.sh[0] + hh * 0.08, ma.sh[1] + hh * 0.04], [ma.hip[0] + hh * 0.1, ma.hip[1] + hh * 0.1], [ma.hip[0] - hh * 0.06, ma.hip[1] + hh * 0.1]], ['#e5567f', '#4d8fd1', '#e2b33c'][ck2]);
          c.fillStyle = '#2a2a30'; c.beginPath(); c.arc(cx2 + hh * 0.3, o.cook - hh * 0.04, hh * 0.12, Math.PI * 0.1, Math.PI * 0.9); c.fill(); for (var sm = 0; sm < 3; sm++) { var su = (t / 2000 + sm / 3 + ck2 * 0.2) % 1; dot(c, cx2 + hh * 0.3 + Math.sin(su * 6) * 3, o.cook - hh * 0.1 - su * hh * 0.4, hh * (0.02 + su * 0.05), 'rgba(255,255,255,' + (0.5 * Math.sin(Math.PI * su)).toFixed(2) + ')'); } } return; }
      var tc = dress(crew[0], '#f2e6c9', '#2a2a30', 2), bx = R.x0 + w * 0.12, bw = Math.min(w * 0.5, hh * 1.6); tc.dir = -1;
      var u = (t / 1000 * 0.4) % 1, me = person(c, bx + bw + hh * 0.18, R.y1, hh * 0.92, { lean: 0.05, legs: [0.05, 0, -0.05, 0], arms: [2.1 + Math.sin(u * TAU) * 0.15, 0.3, 0.2, 0.2] }, tc);
      if (o.abacus) { var A = o.abacus; fr(c, A[0], A[1], A[2], A[3], '#8a5a3a'); for (var rw = 0; rw < 5; rw++) { var yy = A[1] + A[3] * (0.15 + rw * 0.18); ln(c, [[A[0] + 3, yy], [A[0] + A[2] - 3, yy]], '#c9a36a', 1);
        for (var bd = 0; bd < 4; bd++) { var ph = clamp(Math.sin(t / 600 + rw * 1.3 + bd * 0.5) * 1.5, -1, 1), bxx = A[0] + A[2] * (0.15 + bd * 0.12) + (ph > 0 ? A[2] * 0.35 * ease(ph) : 0); el(c, bxx, yy, A[2] * 0.045, A[3] * 0.06, 0, ['#c0392b', '#e8b84a', '#2a5aa8', '#2f8f5b'][bd]); } } }
      var ns = Math.max(2, Math.min(4, Math.floor((R.x1 - bx - bw - hh * 0.5) / (hh * 0.45)) + 2));
      for (var i = 0; i < ns; i++) { var sx = R.x0 + w * (0.14 + i * 0.2), d = crew[1 + i % 4], up = Math.sin(t / 1500 + i * 2.3) > 0.7; d.dir = -1;
        if (sx > R.x1 - hh * 0.3) break;
        person(c, sx, R.y1 + hh * 0.02, hh * 0.72, { lean: 0.05, seat: 0.34, legs: [1.45, -1.4, 1.4, -1.45], arms: up ? [3.0, 0.1, 0.4, 0.7] : [0.9, 1.0, 0.8, 1.1] }, d);
        fr(c, sx - hh * 0.22, R.y1 - hh * 0.3, hh * 0.3, hh * 0.04, nt(S, '#a8784a')); fr(c, sx - hh * 0.2, R.y1 - hh * 0.26, 3, hh * 0.26, nt(S, '#8a8a92')); }
    }
  });
}

/* ---------------------------------------------------------------- community
   The village hall (ศาลาอเนกประสงค์) by the clock: the elders' stick drill at dawn, the news on
   the horn tower at seven and five (sound in rings, r = r₀ + vt), a meeting on plastic chairs
   with the headman at the microphone, lunch on the long table, the weaving group at their
   looms (the batten beats on |sin ωt|), aerobics at dusk to the beat; dark by night but for one
   tube and its moths. A church sings on Sunday morning under its cross; a hall named for a wat
   is a Lanna sala with elders in white. */
function commKind(P) {
  var w = words(P);
  if (/คริสตจักร|church|chapel|christ|คาทอลิก|catholic|มิชชั่?น|mission|นักบุญ|saint|ข่าวประเสริฐ|gospel|คริสเตียน/i.test(w)) return 'church';
  if (/มัสยิด|mosque|masjid|อิสลาม|islam/i.test(w)) return 'mosque';
  if (/วัด|สำนักสงฆ์|ธรรม|พุทธ|สงฆ์|wat\b|temple|buddh|dhamma|meditat/i.test(w)) return 'wat';
  if (/ทอผ้า|ผ้าทอ|weav|หัตถกรรม|craft|จักสาน/i.test(w)) return 'weave';
  if (/ผู้สูงอายุ|elder|senior|ชมรม/i.test(w)) return 'elder';
  if (/สมาคม|association|มูลนิธิ|foundation|club|สโมสร|volunteer|อาสา/i.test(w)) return 'assoc';
  return 'hall';
}
function hornTower(c, S, x, top) {
  var hh = S.hh; fr(c, x - 2, top, 4, S.deck - top, nt(S, '#9a9aa2'));
  [[-1, 0], [1, 0], [-1, 1], [1, 1]].forEach(function (p) { var y = top + p[1] * hh * 0.22, d = p[0]; fp(c, [[x, y - hh * 0.03], [x + d * hh * 0.2, y - hh * 0.09], [x + d * hh * 0.2, y + hh * 0.09], [x, y + hh * 0.03]], nt(S, '#d8d8de')); el(c, x + d * hh * 0.2, y, hh * 0.025, hh * 0.09, 0, nt(S, '#8a8a92')); });
}
function plasticChair(c, S, x, y, s, col) { fr(c, x - s * 0.12, y - s * 0.3, s * 0.24, s * 0.04, nt(S, col)); fr(c, x - s * 0.12, y - s * 0.6, s * 0.04, s * 0.32, nt(S, col)); ln(c, [[x - s * 0.1, y - s * 0.27], [x - s * 0.12, y]], nt(S, col), 2); ln(c, [[x + s * 0.1, y - s * 0.27], [x + s * 0.12, y]], nt(S, col), 2); }
function loom(c, S, x, y, s, t, k) {
  var b = Math.abs(Math.sin(t / 1000 * Math.PI * 1.3 + k));
  ln(c, [[x - s * 0.4, y], [x - s * 0.4, y - s * 0.75], [x + s * 0.35, y - s * 0.75], [x + s * 0.35, y]], nt(S, '#7a4a2a'), 3);
  fr(c, x - s * 0.35, y - s * 0.45, s * 0.65, s * 0.18, nt(S, ['#c0392b', '#2a5aa8', '#7a1f3a', '#2f8f5b'][k % 4])); for (var i = 0; i < 4; i++) fr(c, x - s * 0.35, y - s * 0.43 + i * s * 0.04, s * 0.65, s * 0.012, nt(S, '#e8b84a'));
  c.strokeStyle = 'rgba(240,230,200,.7)'; c.lineWidth = 1; c.beginPath(); for (i = 0; i < 8; i++) { c.moveTo(x - s * 0.33 + i * s * 0.08, y - s * 0.27); c.lineTo(x - s * 0.33 + i * s * 0.08, y - s * 0.7); } c.stroke();
  ln(c, [[x - s * 0.38, y - s * (0.3 + 0.1 * b)], [x + s * 0.33, y - s * (0.3 + 0.1 * b)]], nt(S, '#5a3420'), 3);
  return [x - s * 0.1, y - s * (0.3 + 0.1 * b)];
}
function community(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'community'), P = L.P, r = L.r, ck = L.ck, kind = commKind(P), h = ck.h;
  var mode = S.night ? 'night' : kind === 'mosque' ? 'walk' : kind === 'church' ? (ck.dow === 0 && h < 13 ? 'sing' : h > 16 ? 'sing' : 'sweep')
    : kind === 'weave' ? (h < 17 ? 'weave' : 'aerobic') : h < 8 ? 'stick' : h < 12 ? (kind === 'wat' ? 'merit' : 'meet') : h < 13.5 ? 'lunch' : h < 16.8 ? (kind === 'assoc' ? 'meet' : (S.seed % 2 ? 'weave' : 'meet')) : 'aerobic';
  if (L.st.known && !L.st.open && !S.night) mode = 'sweep';
  var hw = Math.min(S.span * 0.56, hh * (4.2 + r() * 1.0)), left = (S.seed >>> 3) % 2 === 0, hx0 = left ? S.x0 + hh * (0.9 + r() * 0.6) : S.x1 - hh * (1.3 + r() * 0.6) - hw, hx1 = hx0 + hw;
  var tower = kind !== 'church' && r() < 0.75, tx = left ? Math.min(S.x1 - hh * 1.1, hx1 + hh * 0.6) : Math.max(S.x0 + hh * 1.0, hx0 - hh * 0.6);
  var roofK = kind === 'wat' ? 'lanna' : pick(r, ['tin', 'tile', 'lanna', 'tin']), roofC = pick(r, ROOF), post = pick(r, ['#f2ece0', '#c9b8a0', '#7a4a2a']);
  var chairs = pick(r, ['#c0392b', '#2a5aa8', '#2f8f5b', '#e8b84a']);
  var key = 'community|' + kind + '|' + mode;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, P.moo || !P.road ? 'lane' : 'street', r);
    K.setting(S);
    var side = left ? S.x1 - hh * 0.9 : S.x0 + hh * 0.9;
    if (r() < 0.6) rainTree(q, S, side, S.deck + hh * 0.02, hh * 0.95, S.seed); else { banana(q, S, side, S.deck, hh * 1.1, 1); banana(q, S, side + hh * 0.35, S.deck + hh * 0.05, hh * 0.9, 2); }
    var top = S.deck - hh * (kind === 'church' ? 1.55 : 1.45), floor = S.deck - hh * 0.1;
    if (kind === 'mosque') {
      paper(q, rect(hx0, top + hh * 0.2, hw, S.deck - top - hh * 0.2), nt(S, '#f6f2ea'), 1.6);
      var mx0 = (hx0 + hx1) / 2; paper(q, function (p) { p.beginPath(); p.moveTo(mx0 - hh * 0.55, top + hh * 0.22); p.quadraticCurveTo(mx0 - hh * 0.6, top - hh * 0.45, mx0, top - hh * 0.62); p.quadraticCurveTo(mx0 + hh * 0.6, top - hh * 0.45, mx0 + hh * 0.55, top + hh * 0.22); p.closePath(); }, nt(S, '#2f8f5b'), 1.6);
      ln(q, [[mx0, top - hh * 0.62], [mx0, top - hh * 0.78]], nt(S, '#e8b84a'), 2); q.fillStyle = nt(S, '#e8b84a'); q.beginPath(); q.arc(mx0, top - hh * 0.84, hh * 0.06, 0, TAU); q.arc(mx0 + hh * 0.025, top - hh * 0.85, hh * 0.05, 0, TAU, true); q.fill('evenodd');
      var mn = left ? hx1 - hh * 0.25 : hx0 + hh * 0.25; paper(q, rect(mn - hh * 0.1, S.deck - hh * 2.0, hh * 0.2, hh * 2.0), nt(S, '#f6f2ea'), 1.2); fp(q, [[mn - hh * 0.12, S.deck - hh * 2.0], [mn, S.deck - hh * 2.25], [mn + hh * 0.12, S.deck - hh * 2.0]], nt(S, '#2f8f5b'));
      for (var ma = 0; ma < 5; ma++) { var ax2 = hx0 + hw * (0.12 + ma * 0.19); if (Math.abs(ax2 - mn) < hh * 0.25) continue; q.fillStyle = S.night ? '#ffd98a' : '#2f6f5a'; q.beginPath(); q.moveTo(ax2, S.deck - hh * 0.2); q.lineTo(ax2, S.deck - hh * 0.75); q.arc(ax2 + hh * 0.11, S.deck - hh * 0.75, hh * 0.11, Math.PI, 0); q.lineTo(ax2 + hh * 0.22, S.deck - hh * 0.2); q.fill(); }
      o.sign = signAt(q, S, mx0, top + hh * 0.3, P, hh * 0.72, nt(S, '#2f6f5a'), null); o.top = top - hh * 0.9;
    } else if (kind === 'church') {
      paper(q, rect(hx0, top, hw, S.deck - top), nt(S, '#f6f2ea'), 1.6);
      var gx = (hx0 + hx1) / 2; paper(q, poly([[hx0 - hh * 0.15, top + hh * 0.05], [gx, top - hh * 0.6], [hx1 + hh * 0.15, top + hh * 0.05]]), nt(S, roofC), 1.8);
      fp(q, [[gx - hh * 0.6, top + hh * 0.02], [gx, top - hh * 0.42], [gx + hh * 0.6, top + hh * 0.02]], nt(S, '#f6f2ea'));
      fr(q, gx - 2, top - hh * 0.38, 4, hh * 0.3, nt(S, '#c9a36a')); fr(q, gx - hh * 0.08, top - hh * 0.3, hh * 0.16, 4, nt(S, '#c9a36a'));
      for (var w = 0; w < 4; w++) { var wx = hx0 + hw * (0.12 + w * 0.22); if (Math.abs(wx + hw * 0.05 - gx) < hh * 0.35) continue; q.fillStyle = S.night ? '#ffd98a' : '#9fc6d8'; q.beginPath(); q.moveTo(wx, S.deck - hh * 0.35); q.lineTo(wx, S.deck - hh * 0.85); q.arc(wx + hh * 0.1, S.deck - hh * 0.85, hh * 0.1, Math.PI, 0); q.lineTo(wx + hh * 0.2, S.deck - hh * 0.35); q.fill(); }
      o.door = [gx - hh * 0.45, gx + hh * 0.45, S.deck - hh * 1.0];
      fr(q, o.door[0], o.door[2], o.door[1] - o.door[0], S.deck - o.door[2], mode === 'sing' ? (S.night ? '#ffd98a' : '#f2e2b8') : nt(S, '#5a3a2a'));
      if (mode === 'sing') for (var pw = 0; pw < 3; pw++) fr(q, o.door[0] + hh * 0.08, S.deck - hh * (0.2 + pw * 0.12), o.door[1] - o.door[0] - hh * 0.16, hh * 0.04, '#8a5a3a');
      o.sign = signAt(q, S, gx, top + hh * 0.08, P, hh * 0.72, nt(S, '#3a5a8a'), mode === 'sing' && S.night || null);
      o.top = top - hh * 0.6;
    } else {
      /* the hall: a plinth, posts, open sides, the roof */
      paper(q, rect(hx0 - hh * 0.05, floor, hw + hh * 0.1, hh * 0.12), nt(S, '#c8bca8'), 1);
      var np = Math.max(3, Math.round(hw / (hh * 1.1)));
      for (var p = 0; p <= np; p++) paper(q, rect(lerp(hx0, hx1, p / np) - hh * 0.05, top + hh * 0.3, hh * 0.1, floor - top - hh * 0.3), nt(S, post), 0.8);
      if (kind === 'wat' || roofK === 'lanna') {
        paper(q, poly([[hx0 - hh * 0.35, top + hh * 0.42], [hx0 + hw * 0.18, top - hh * 0.05], [hx1 - hw * 0.18, top - hh * 0.05], [hx1 + hh * 0.35, top + hh * 0.42]]), nt(S, roofC), 1.8);
        paper(q, poly([[hx0 + hw * 0.12, top + hh * 0.02], [hx0 + hw * 0.5, top - hh * 0.5], [hx1 - hw * 0.12, top + hh * 0.02]]), nt(S, roofC), 1.6);
        ln(q, [[hx0 - hh * 0.35, top + hh * 0.42], [hx0 + hw * 0.18, top - hh * 0.05], [hx1 - hw * 0.18, top - hh * 0.05], [hx1 + hh * 0.35, top + hh * 0.42]], nt(S, '#e8b84a'), 1.4);
        var kx = hx0 + hw * 0.5, ky = top - hh * 0.5; q.save(); q.strokeStyle = nt(S, '#e8b84a'); q.lineWidth = 2.4; q.lineCap = 'round'; q.beginPath(); q.moveTo(kx, ky); q.quadraticCurveTo(kx - hh * 0.05, ky - hh * 0.2, kx - hh * 0.18, ky - hh * 0.28); q.moveTo(kx, ky); q.quadraticCurveTo(kx + hh * 0.05, ky - hh * 0.2, kx + hh * 0.18, ky - hh * 0.28); q.stroke(); q.restore();
        o.top = top - hh * 0.8;
      } else {
        paper(q, poly([[hx0 - hh * 0.3, top + hh * 0.38], [hx0 + hw * 0.2, top], [hx1 - hw * 0.2, top], [hx1 + hh * 0.3, top + hh * 0.38]]), nt(S, roofK === 'tin' ? '#a8b0b8' : roofC), 1.8);
        if (roofK === 'tin') { q.strokeStyle = 'rgba(0,0,0,.15)'; q.lineWidth = 1; q.beginPath(); for (var rx = hx0 - hh * 0.2; rx < hx1 + hh * 0.2; rx += 5) { q.moveTo(rx, top + hh * 0.36); q.lineTo(lerp(rx, (hx0 + hx1) / 2, 0.2), top + 2); } q.stroke(); }
        o.top = top;
      }
      /* tubes hung from the beam; a notice board on the near post */
      for (var tb = 0; tb < 3; tb++) { var tx2 = lerp(hx0 + hw * 0.2, hx1 - hw * 0.2, tb / 2); ln(q, [[tx2, top + hh * 0.38], [tx2, top + hh * 0.48]], '#3a3a44', 1); fr(q, tx2 - hh * 0.18, top + hh * 0.48, hh * 0.36, 3, S.night && tb === 1 ? '#f4fff8' : nt(S, '#e8e8e8')); }
      if (S.night) glow(q, (hx0 + hx1) / 2, top + hh * 0.5, hh * 0.6, '220,255,240', 0.35);
      var nbx = left ? hx1 + hh * 0.15 : hx0 - hh * 0.75; paper(q, rect(nbx, S.deck - hh * 0.95, hh * 0.6, hh * 0.45), nt(S, '#8a5a3a'), 1); fr(q, nbx + hh * 0.04, S.deck - hh * 0.91, hh * 0.52, hh * 0.37, nt(S, '#c9a36a'));
      for (var pp = 0; pp < 5; pp++) fr(q, nbx + hh * (0.07 + (pp % 3) * 0.16), S.deck - hh * (0.88 - Math.floor(pp / 3) * 0.17), hh * 0.12, hh * 0.14, nt(S, ['#f8f8f4', '#ffe8a0', '#f8f8f4', '#d8f0ff', '#ffd1e8'][pp]));
      fr(q, nbx + hh * 0.27, S.deck - hh * 0.5, 4, hh * 0.5, nt(S, '#8a5a3a')); o.notice = [nbx, S.deck - hh * 0.91];
      if (kind === 'wat') { var bx = (hx0 + hx1) / 2; el(q, bx, floor - hh * 0.2, hh * 0.18, hh * 0.1, 0, nt(S, '#d4a23f')); el(q, bx, floor - hh * 0.38, hh * 0.1, hh * 0.15, 0, nt(S, '#e0b04a')); dot(q, bx, floor - hh * 0.58, hh * 0.07, nt(S, '#e0b04a')); fp(q, [[bx - hh * 0.025, floor - hh * 0.63], [bx, floor - hh * 0.76], [bx + hh * 0.025, floor - hh * 0.63]], nt(S, '#e0b04a')); marigolds(q, S, hx0 + hw * 0.1, hx1 - hw * 0.1, top + hh * 0.42, hh * 0.12); }
      if (mode === 'meet' || mode === 'merit') { o.banner = [hx0 + hw * 0.15, hx1 - hw * 0.15]; fr(q, hx0 + hw * 0.15, top + hh * 0.52, hw * 0.7, hh * 0.2, nt(S, '#f8f4e8')); fr(q, hx0 + hw * 0.15, top + hh * 0.52, hw * 0.7, hh * 0.04, nt(S, chairs)); fr(q, hx0 + hw * 0.15, top + hh * 0.68, hw * 0.7, hh * 0.04, nt(S, chairs)); }
      if (mode === 'weave' && kind !== 'weave') { /* the long work table under the roof */ }
      o.sign = signAt(q, S, (hx0 + hx1) / 2, top + hh * (roofK === 'lanna' || kind === 'wat' ? -0.32 : -0.08), P, hh * 0.72, nt(S, kind === 'wat' ? '#6a2a1a' : '#5a2e18'), null);
      if (kind === 'wat' || kind === 'elder') khom(q, S, hx0 + hh * 0.1, top + hh * 0.5, hh * 0.16, '#d9342b', S.night); 
    }
    if (tower) hornTower(q, S, tx, S.deck - hh * 2.0);
    if (r() < 0.6) o.incense = spiritHouse(q, S, left ? hx0 - hh * 0.5 : hx1 + hh * 0.5, hh * 0.9, (S.seed >>> 2) % 3);
    roadPlate(q, S, left ? S.x1 - hh * 0.3 : S.x0 + hh * 0.3, P.road);
    if (S.night) { o.lamp = [tx, S.deck - hh * 1.5]; bulb(q, S, tx + hh * 0.08, S.deck - hh * 1.5, hh, true); }
    return o;
  }).out || {};
  L.incense = still.incense; L.lamp = still.lamp ? [still.lamp[0] + hh * 0.08, still.lamp[1]] : null;
  var t = S.t, cx = (hx0 + hx1) / 2, crew = crowd(S, 12, kind === 'wat' ? { sin: 0.6, mohom: 0.4 } : { casual: 0.5, sin: 0.25, mohom: 0.25 });
  /* the horn tower speaks at seven and five: rings, r = r₀ + vt */
  if (tower && !S.night && (h < 8.5 || h > 16.5 && h < 18.5)) for (var k = 0; k < 3; k++) { var u = (t / 1400 + k / 3) % 1; c.strokeStyle = 'rgba(255,255,255,' + (0.7 * (1 - u)).toFixed(2) + ')'; c.lineWidth = 1.5; [-1, 1].forEach(function (d) { c.beginPath(); c.arc(tx + d * hh * 0.2, S.deck - hh * 1.89, hh * (0.08 + u * 0.35), d > 0 ? -0.6 : Math.PI - 0.6, d > 0 ? 0.6 : Math.PI + 0.6); c.stroke(); }); }
  var floorY = S.deck - hh * 0.1;
  if (mode === 'stick') {   /* the elders' stick drill: the staff overhead and down on cos ωt */
    var n = Math.max(3, Math.min(6, Math.floor(hw / (hh * 0.7)))), a = 0.5 - 0.5 * Math.cos(t / 1000 * TAU / 2.4);
    for (var i = 0; i < n; i++) { var d = crew[i], x = lerp(hx0 + hh * 0.4, hx1 - hh * 0.4, n > 1 ? i / (n - 1) : 0.5); d.dir = 1; d.hairCol = i % 2 ? '#d8d8d8' : '#9a9a9a'; if (d.garb === 'sin') d.hair = 2;
      var me = person(c, x, S.deck + hh * 0.18, hh * 0.9, { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [1.2 + a * 1.8, 0.2, 1.2 + a * 1.8, 0.2] }, d);
      ln(c, [[me.hand[0][0] - hh * 0.32, me.hand[0][1]], [me.hand[0][0] + hh * 0.32, me.hand[0][1]]], '#c9a36a', 2.5); }
  } else if (mode === 'meet' || mode === 'merit') {
    var rows = 2, per = Math.max(2, Math.min(5, Math.floor(hw / (hh * 0.62)) - 1)), j = 0;
    var head = crew[11]; head.dir = -1; if (kind !== 'wat') { dressUp(head, '#c8b07a', '#5a4a32'); var hm = person(c, hx1 - hh * 0.45, floorY, hh * 0.95, { lean: 0.05, legs: [0.05, 0, -0.05, 0], arms: [1.6 + Math.sin(t / 400) * 0.15, 0.9, 0.4 + Math.sin(t / 900) * 0.3, 0.6] }, head); fr(c, hm.hand[0][0] - 2, hm.hand[0][1] - hh * 0.06, 4, hh * 0.08, '#2a2a30'); fr(c, hx1 - hh * 0.75, floorY - hh * 0.35, hh * 0.3, hh * 0.35, nt(S, '#f8f4e8')); }
    else { var mk = crew[11]; mk.garb = 'casual'; mk.col = '#c8692a'; mk.low = '#c8692a'; mk.hair = 0; mk.hairCol = '#a87a58'; mk.long = true; mk.dir = -1; person(c, hx1 - hh * 0.5, floorY, hh * 0.92, POSE.lotus, mk); }
    for (var row = 0; row < rows; row++) for (var q = 0; q < per; q++, j++) { var px = hx0 + hh * (0.45 + q * 0.62 + row * 0.25), pd = crew[j]; if (px > hx1 - hh * 1.0) continue; pd.dir = 1;
      if (kind === 'wat') { pd.col = '#f6f4ee'; if (pd.garb === 'sin') { pd.low = '#f6f4ee'; pd.sabai = '#f6f4ee'; } person(c, px, floorY + row * hh * 0.08, hh * 0.86, POSE.wai, pd); }
      else { plasticChair(c, S, px - hh * 0.02, floorY + row * hh * 0.08, hh, chairs); person(c, px, floorY + row * hh * 0.08, hh * 0.86, { lean: 0.05, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4 + (q === 1 && Math.sin(t / 1300 + row) > 0.8 ? 2.4 : 0), 0.6, 0.3, 0.7] }, pd); } }
  } else if (mode === 'lunch') {
    var tw = Math.min(hw - hh * 0.8, hh * 3); fr(c, cx - tw / 2, floorY - hh * 0.32, tw, hh * 0.05, nt(S, '#f4f4f4')); fr(c, cx - tw / 2 + 3, floorY - hh * 0.27, 3, hh * 0.27, '#8a8a92'); fr(c, cx + tw / 2 - 6, floorY - hh * 0.27, 3, hh * 0.27, '#8a8a92');
    for (var b2 = 0; b2 < 5; b2++) { var bxx = cx - tw / 2 + tw * (0.12 + b2 * 0.19); dot(c, bxx, floorY - hh * 0.36, hh * 0.06, ['#f2a33a', '#7fbf4a', '#f8f4e8', '#d9342b', '#c9a36a'][b2]); }
    for (var e = 0; e < 4; e++) { var ex = cx - tw / 2 + tw * (0.15 + e * 0.24), ed = crew[e]; ed.dir = e % 2 ? -1 : 1; var lift = Math.max(0, Math.sin(t / 900 + e * 1.7)); person(c, ex, floorY + hh * 0.06, hh * 0.84, { lean: 0.1, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.9 + lift * 0.8, 1.2 + lift * 0.8, 0.6, 0.8] }, ed); }
  } else if (mode === 'weave') {
    for (var l = 0; l < Math.min(3, Math.floor(hw / (hh * 1.2))); l++) { var lx = hx0 + hh * 0.7 + l * hh * 1.25, wd = crew[l]; wd.garb = 'sin'; wd.hair = 2; wd.dir = 1;
      var hand = loom(c, S, lx + hh * 0.35, floorY, hh * 0.9, t, l + S.seed); person(c, lx, floorY, hh * 0.84, reach(lx, floorY, hh * 0.84, { lean: 0.15, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [1, 0.5, 1, 0.5] }, 1, hand, [hand[0] + hh * 0.05, hand[1] + hh * 0.05]), wd); }
  } else if (mode === 'aerobic') {   /* aerobics at dusk: everyone on the beat, |sin ωt| */
    var beat = t / 1000 * TAU * 1.1, s1 = Math.sin(beat), s2 = Math.abs(Math.sin(beat)), ins = crew[0]; dressUp(ins, '#e5567f', '#2a2a30'); ins.dir = left ? -1 : 1;
    var ix = left ? hx1 + hh * 0.2 : hx0 - hh * 0.2; fr(c, ix - hh * 0.4, S.deck - hh * 0.02, hh * 0.8, hh * 0.1, nt(S, '#5a5a62'));
    person(c, ix, S.deck - hh * 0.02 - s2 * hh * 0.04, hh * 0.95, { lean: 0, legs: [0.2 + s1 * 0.3, 0, -0.2 + s1 * 0.3, 0], arms: [2.6 + s1 * 0.5, 0.2, 2.6 - s1 * 0.5, 0.2] }, ins);
    fr(c, ix - hh * 0.55, S.deck - hh * 0.45, hh * 0.16, hh * 0.42, '#2a2a30'); dot(c, ix - hh * 0.47, S.deck - hh * 0.32, hh * 0.05, '#5a5a62');
    var na = Math.max(3, Math.min(7, Math.floor(hw / (hh * 0.6)))); for (var aa = 0; aa < na; aa++) { var ax = lerp(hx0 + hh * 0.3, hx1 - hh * 0.3, aa / Math.max(1, na - 1)), ad = crew[aa + 1]; ad.dir = left ? 1 : -1;
      person(c, ax, S.deck + hh * (0.15 + (aa % 2) * 0.12), hh * 0.88, { lean: 0, lift: s2 * 0.02, legs: [0.2 + s1 * 0.3, 0, -0.2 + s1 * 0.3, 0], arms: [2.6 + s1 * 0.5, 0.2, 2.6 - s1 * 0.5, 0.2] }, ad); }
    K.notes(c, ix - hh * 0.5, S.deck - hh * 0.5, t, 3, '#fff6d6');
  } else if (mode === 'sing') {
    for (var sg = 0; sg < 3; sg++) { var sd = crew[sg], sx = still.door ? lerp(still.door[0] + hh * 0.15, still.door[1] - hh * 0.15, sg / 2) : cx; sd.dir = 1; person(c, sx, S.deck - hh * 0.02, hh * 0.78, { lean: Math.sin(t / 900 + sg) * 0.04, legs: [0.06, 0, -0.06, 0], arms: [0.9, 1.4, 0.8, 1.5] }, sd); }
    K.notes(c, cx, S.deck - hh * 1.0, t, 4, S.night ? '#ffe2a0' : '#fff6d6');
  } else if (mode === 'walk') {   /* men in white caps walking to prayer, x = x₀ + vt */
    for (var wk = 0; wk < 3; wk++) { var wd2 = crew[wk]; dressUp(wd2, '#f6f4ee', wk % 2 ? '#3a3a44' : '#f6f4ee'); var vv = 0.22 + wk * 0.04, wx2 = stroll(S, wk, left ? -vv : vv, wk * 0.3); wd2.dir = left ? -1 : 1;
      var mw = person(c, wx2, S.deck + hh * (0.15 + wk % 2 * 0.1), hh * 0.92, K.walkP(t / 1000 * TAU * 0.8 + wk, false), wd2); c.fillStyle = '#f8f8f4'; c.beginPath(); c.arc(mw.head[0], mw.head[1] - hh * 0.03, hh * 0.085, Math.PI, TAU); c.fill(); }
  } else if (mode === 'sweep') {
    var sw = crew[2]; sw.dir = Math.cos(t / 4000) >= 0 ? 1 : -1; var swing = Math.sin(t / 380); var mx = cx + Math.sin(t / 4000) * hh * 0.8, me2 = person(c, mx, S.deck + hh * 0.15, hh * 0.9, { lean: 0.35, legs: [0.1, 0, -0.1, 0], arms: [0.9 + swing * 0.4, 0.4, 0.8 + swing * 0.4, 0.5] }, sw);
    ln(c, [me2.hand[0], [me2.hand[0][0] + sw.dir * (hh * 0.18 + swing * hh * 0.1), S.deck + hh * 0.15]], '#a8925a', 2);
    L.dog = [left ? hx1 + hh * 0.4 : hx0 - hh * 0.4, S.deck + hh * 0.25, false];
  } else L.dog = [cx, S.deck + hh * 0.3, true];
  if (S.night && !L.lamp) L.lamp = [cx, S.deck - hh * 1.0];
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: hx0, x1: hx1, y0: still.top || S.deck - hh * 2, y1: S.deck });
}

/* ---------------------------------------------------------------- fresh market
   The morning market under its tin roof or its umbrellas: stalls dealt by what the place sells
   (pork, fish on ice, vegetables, fruit, flowers, eggs, the north's sausage coils and sticky-rice
   baskets), the hanging scale's needle swinging θ = θ₀·e^(−λt)·cos ωt after each weighing,
   plastic bags on their hooks as pendulums, the cleaver on |sin ωt|, fish tails flicking; busiest
   at dawn; by night the tarps are down and a cat sleeps on a table. */
function goodsOf(P) {
  var w = words(P), g = [];
  if (/หมู|pork|pig/i.test(w)) g.push('pork');
  if (/ไก่|chicken/i.test(w)) g.push('chicken');
  if (/ปลา|fish|อาหารทะเล|seafood|กุ้ง/i.test(w)) g.push('fish');
  if (/ผลไม้|fruit|ส้ม|มะม่วง|ลำไย|ลิ้นจี่|berry|เบอร์รี่|แบรี/i.test(w)) g.push('fruit');
  if (/ดอกไม้|flower|พวงมาลัย|florist/i.test(w)) g.push('flowers');
  if (/ไข่|egg/i.test(w)) g.push('eggs');
  if (/ผัก|veg|organic|ออร์แกนิก/i.test(w)) g.push('veg');
  if (/น้ำผึ้ง|honey/i.test(w)) g.push('honey');
  return g;
}
var GOODS = ['veg', 'fruit', 'pork', 'fish', 'chillies', 'flowers', 'eggs', 'sausage', 'rice', 'chicken'];
function goods(c, S, kind, x0, x1, y, hh, k) {
  var w = x1 - x0, i, n;
  function heap(cx, cy, rr, cols, m) { for (var j = 0; j < m; j++) { var a = j * 2.4, d = rr * Math.sqrt(j / m); dot(c, cx + Math.cos(a) * d, cy - Math.abs(Math.sin(a)) * d * 0.6, rr * 0.22, nt(S, cols[j % cols.length])); } }
  if (kind === 'veg') { for (i = 0; i < 4; i++) { var vx = x0 + w * (0.12 + i * 0.25); if (i % 2) heap(vx, y - hh * 0.04, hh * 0.13, i === 1 ? ['#d9342b', '#e8402a'] : ['#f2f2e8', '#d8c8a8'], 16); else for (var b = 0; b < 5; b++) el(c, vx + (b - 2) * hh * 0.035, y - hh * 0.08, hh * 0.025, hh * 0.1, (b - 2) * 0.15, nt(S, ['#4f8a3a', '#6faa4a'][b % 2])); } }
  else if (kind === 'fruit') { heap(x0 + w * 0.2, y - hh * 0.04, hh * 0.14, ['#f29a1f', '#f7b52c'], 16); heap(x0 + w * 0.5, y - hh * 0.04, hh * 0.13, ['#e5567f', '#c2307a'], 12); for (i = 0; i < 6; i++) el(c, x0 + w * 0.78 + (i % 3) * hh * 0.06, y - hh * 0.05 - Math.floor(i / 3) * hh * 0.05, hh * 0.035, hh * 0.08, 0.5, nt(S, '#f2d24a')); }
  else if (kind === 'pork') { fr(c, x0 + w * 0.08, y - hh * 0.06, w * 0.84, hh * 0.06, nt(S, '#a86a4a')); for (i = 0; i < 4; i++) el(c, x0 + w * (0.18 + i * 0.22), y - hh * 0.07, hh * 0.1, hh * 0.04, 0, nt(S, '#e89a8a')); }
  else if (kind === 'fish') { for (i = 0; i < 2; i++) { var bx = x0 + w * (0.25 + i * 0.45); el(c, bx, y - hh * 0.05, hh * 0.24, hh * 0.07, 0, nt(S, '#3a6ac0')); el(c, bx, y - hh * 0.09, hh * 0.21, hh * 0.04, 0, nt(S, '#d8eef8')); } }
  else if (kind === 'chillies') { heap(x0 + w * 0.2, y - hh * 0.03, hh * 0.13, ['#d9342b', '#b82a20'], 18); heap(x0 + w * 0.5, y - hh * 0.03, hh * 0.12, ['#f2e6d8', '#e8d0c0'], 14); heap(x0 + w * 0.78, y - hh * 0.03, hh * 0.11, ['#a84a6a', '#8a3a5a'], 12); }
  else if (kind === 'flowers') { for (i = 0; i < 5; i++) { var fx = x0 + w * (0.12 + i * 0.19); for (var m = 0; m < 9; m++) dot(c, fx + Math.sin(m) * hh * 0.04, y - hh * 0.03 - m * hh * 0.025, hh * 0.028, nt(S, m % 2 ? '#f29a1f' : '#f7c52c')); dot(c, fx, y - hh * 0.27, hh * 0.03, nt(S, '#f8f8f4')); } }
  else if (kind === 'eggs') { for (i = 0; i < 3; i++) for (var r2 = 0; r2 < 3; r2++) { fr(c, x0 + w * (0.1 + i * 0.28), y - hh * (0.03 + r2 * 0.05), w * 0.24, hh * 0.04, nt(S, '#c9b88a')); for (var e2 = 0; e2 < 5; e2++) el(c, x0 + w * (0.12 + i * 0.28) + e2 * w * 0.045, y - hh * (0.05 + r2 * 0.05), hh * 0.018, hh * 0.022, 0, nt(S, '#f4e2c8')); } }
  else if (kind === 'sausage') { for (i = 0; i < 3; i++) { var sx = x0 + w * (0.2 + i * 0.3); c.strokeStyle = nt(S, '#a8432f'); c.lineWidth = Math.max(2, hh * 0.035); c.beginPath(); for (var a = 0; a < 14; a += 0.4) c.lineTo(sx + Math.cos(a) * a * hh * 0.008, y - hh * 0.06 + Math.sin(a) * a * hh * 0.004); c.stroke(); } }
  else if (kind === 'rice') { for (i = 0; i < 4; i++) { var rx = x0 + w * (0.14 + i * 0.24); fp(c, [[rx - hh * 0.06, y], [rx + hh * 0.06, y], [rx + hh * 0.05, y - hh * 0.14], [rx - hh * 0.05, y - hh * 0.14]], nt(S, '#c9a36a')); el(c, rx, y - hh * 0.16, hh * 0.05, hh * 0.02, 0, nt(S, '#a8843a')); } }
  else if (kind === 'chicken') { for (i = 0; i < 3; i++) el(c, x0 + w * (0.2 + i * 0.3), y - hh * 0.06, hh * 0.1, hh * 0.06, 0, nt(S, '#f2d0a0')); }
  else if (kind === 'honey') { for (i = 0; i < 6; i++) { var hx = x0 + w * (0.1 + i * 0.15); fr(c, hx, y - hh * 0.14, hh * 0.07, hh * 0.14, nt(S, '#e8a020')); fr(c, hx, y - hh * 0.16, hh * 0.07, hh * 0.03, nt(S, '#f8f4e8')); } }
}
function freshmarket(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'freshmarket'), P = L.P, r = L.r, ck = L.ck, t = S.t;
  var want = goodsOf(P), sup = /lotus|tesco|tops|rimping|ริมปิง|big ?c|makro|แม็คโคร|supermarket|ซูเปอร์|มาร์ท|mart/i.test(words(P));
  var roof = sup ? 'shed' : pick(r, ['shed', 'shed', 'umbrella', 'tarp']), evening = /16:|17:|18:|กาดแลง|evening|night/i.test((P.hours || '') + ' ' + words(P));
  var ns = Math.max(3, Math.min(5, Math.floor((S.span - hh * 1.8) / (hh * 1.45)))), sw = (S.span - hh * 1.8) / ns, stalls = [];
  var deal = GOODS.slice(); for (var i = deal.length - 1; i > 0; i--) { var j = Math.floor(r() * (i + 1)), tmp = deal[i]; deal[i] = deal[j]; deal[j] = tmp; }
  var order = want.concat(deal.filter(function (g) { return want.indexOf(g) < 0; }));
  var mid = Math.floor(ns / 2); for (i = 0; i < ns; i++) stalls.push({ x0: S.x0 + hh * 0.9 + i * sw + hh * 0.08, x1: S.x0 + hh * 0.9 + (i + 1) * sw - hh * 0.08, g: order[(i - mid + ns * 3) % ns === 0 ? 0 : ((i - mid + ns) % ns) % order.length], col: pick(r, ['#c0392b', '#2a5aa8', '#2f8f5b', '#e8b84a', '#e5567f', '#f2f2f2']) });
  var busy = S.night ? 0 : ck.h < 10 ? 3 : ck.h < 15 ? 1 : evening ? 3 : 2, quiet = L.st.shut || L.st.quiet && !(evening && S.night);
  var key = 'freshmarket|' + roof + '|' + (quiet ? 'q' : 'o');
  var ty = S.deck - hh * 0.36;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, P.road ? 'street' : 'lane', r);
    K.setting(S);
    var top = S.deck - hh * 2.05;
    if (roof === 'shed') {
      for (var x = S.x0 + hh * 0.7; x < S.x1 - hh * 0.4; x += hh * 2.2) fr(q, x, top + hh * 0.3, 5, S.deck - top - hh * 0.3, nt(S, '#7a8088'));
      paper(q, poly([[S.x0 + hh * 0.4, top + hh * 0.4], [S.x0 + S.span * 0.5, top], [S.x1 - hh * 0.3, top + hh * 0.4], [S.x1 - hh * 0.3, top + hh * 0.48], [S.x0 + hh * 0.4, top + hh * 0.48]]), nt(S, sup ? '#c8ccd2' : '#a8b0b8'), 1.4);
      q.strokeStyle = 'rgba(0,0,0,.12)'; q.lineWidth = 1; q.beginPath(); for (x = S.x0 + hh * 0.5; x < S.x1 - hh * 0.3; x += 5) { q.moveTo(x, top + hh * 0.46); q.lineTo(lerp(x, S.x0 + S.span * 0.5, 0.25), top + hh * 0.05); } q.stroke();
      for (x = S.x0 + hh * 1.1; x < S.x1 - hh * 0.6; x += hh * 1.3) { ln(q, [[x, top + hh * 0.48], [x, top + hh * 0.66]], '#3a3a44', 1); fr(q, x - hh * 0.2, top + hh * 0.66, hh * 0.4, 3, S.night && !quiet ? '#fffbe0' : nt(S, '#e8e8e8')); if (S.night && !quiet) glow(q, x, top + hh * 0.7, hh * 0.5, '240,255,230', 0.35); }
      o.signY = top + hh * 0.5; o.top = top;
    } else o.top = S.deck - hh * 1.4;
    stalls.forEach(function (s, k) {
      var cx = (s.x0 + s.x1) / 2;
      if (roof === 'umbrella') { var ut = S.deck - hh * 1.45; ln(q, [[cx, ut], [cx, ty]], nt(S, '#d8d8de'), 2); var uw = (s.x1 - s.x0) * 0.62; for (var p = 0; p < 6; p++) fp(q, [[cx, ut - hh * 0.12], [cx - uw + p * uw / 3, ut + hh * 0.1], [cx - uw + (p + 1) * uw / 3, ut + hh * 0.1]], nt(S, p % 2 ? s.col : '#f4f4f4')); }
      if (roof === 'tarp') { var tt = S.deck - hh * 1.3; ln(q, [[s.x0, tt], [s.x0, ty]], nt(S, '#8a8a92'), 2); ln(q, [[s.x1, tt], [s.x1, ty]], nt(S, '#8a8a92'), 2); fp(q, [[s.x0 - hh * 0.05, tt], [s.x1 + hh * 0.05, tt - hh * 0.08], [s.x1 + hh * 0.05, tt + hh * 0.04], [s.x0 - hh * 0.05, tt + hh * 0.12]], nt(S, k % 2 ? '#2a5aa8' : '#e07a2a')); }
      if (s.g === 'pork' || s.g === 'chicken') { var ry = ty - hh * 0.62; ln(q, [[s.x0 + hh * 0.05, ry], [s.x1 - hh * 0.05, ry]], nt(S, '#8a8a92'), 2); }
    });
    var sx = roof === 'shed' ? S.x0 + S.span * 0.5 : (stalls[mid].x0 + stalls[mid].x1) / 2;
    o.sign = signAt(q, S, sx, roof === 'shed' ? o.signY + hh * 0.06 : S.deck - hh * 1.95, P, hh * 0.8, nt(S, '#5a2e18'), S.night && !quiet || null);
    if (r() < 0.65) o.incense = spiritHouse(q, S, S.x0 + hh * 0.55, hh * 0.85, (S.seed >>> 2) % 3);
    roadPlate(q, S, S.x1 - hh * 0.35, P.road);
    if (!quiet && r() < 0.7) motorbike(q, S, S.x1 - hh * 1.0, S.deck + hh * 0.42, hh * 0.62, -1, pick(r, CLOTH2), true);
    if (S.night) { o.lamp = [S.x0 + S.span * 0.5, S.deck - hh * 1.2]; bulb(q, S, o.lamp[0], o.lamp[1], hh, true); }
    return o;
  }).out || {};
  function tables() { layer(S, key + '|front', [S.x0, ty - hh * 0.45, S.span, S.deck - ty + hh * 0.5], function (q) {
    stalls.forEach(function (s, k) {
      paper(q, rect(s.x0, ty, s.x1 - s.x0, hh * 0.06), nt(S, '#c8ccd2'), 0.8);
      fr(q, s.x0 + 2, ty + hh * 0.06, s.x1 - s.x0 - 4, S.deck - ty - hh * 0.06, nt(S, s.col)); fr(q, s.x0 + 2, ty + hh * 0.06, s.x1 - s.x0 - 4, hh * 0.05, nt(S, '#f4f4f4'));
      if (quiet) { paper(q, poly([[s.x0 - 2, ty + hh * 0.1], [s.x0 + hh * 0.1, ty - hh * 0.22], [s.x1 - hh * 0.1, ty - hh * 0.24], [s.x1 + 2, ty + hh * 0.1]]), nt(S, k % 2 ? '#2a5aa8' : '#4a6a8a'), 1); return; }
      goods(q, S, s.g, s.x0, s.x1, ty, hh * 1.3, k);
    });
  }); }
  L.incense = still.incense; L.lamp = still.lamp;
  if (quiet) { tables(); L.cat = [(stalls[mid].x0 + stalls[mid].x1) / 2, ty - hh * 0.12]; L.dog = [stalls[0].x1, S.deck + hh * 0.26, true]; streetLife(S, L); S.hits.push({ k: 'place', x0: S.x0 + hh * 0.8, x1: S.x1 - hh * 0.3, y0: still.top, y1: S.deck }); return; }
  var crew = crowd(S, ns + 4, { casual: 0.55, sin: 0.3, mohom: 0.15 });
  /* the vendors behind their tables, and what moves at each stall */
  stalls.forEach(function (s, k) {
    var cx = (s.x0 + s.x1) / 2, d = crew[k]; d.dir = 1; if (d.garb === 'casual' && k % 2) { d.hat = true; }
    var vx = s.x0 + (s.x1 - s.x0) * 0.3, chop = s.g === 'pork' ? Math.pow(Math.abs(Math.sin(t / 1000 * Math.PI * 1.6 + k)), 3) : 0;
    var me = person(c, vx, ty + hh * 0.1, hh * 0.86, { lean: 0.15, legs: [0.06, 0, -0.06, 0], arms: s.g === 'pork' ? [1.5 + chop * 1.2, 0.5 - chop * 0.4, 1.0, 0.8] : [0.9 + Math.sin(t / 800 + k) * 0.2, 1.1, 0.7, 1.0] }, d);
    if (s.g === 'pork') { var hd = me.hand[0]; fr(c, hd[0] - 2, hd[1] - hh * 0.02, hh * 0.13, hh * 0.08, '#c8ccd2'); fr(c, hd[0] - hh * 0.04, hd[1] - hh * 0.01, hh * 0.05, hh * 0.03, '#5a3420'); }
    if (s.g === 'pork' || s.g === 'chicken') { var ry = ty - hh * 0.62; for (var hk = 0; hk < 3; hk++) { var hx = s.x0 + (s.x1 - s.x0) * (0.4 + hk * 0.22), th = 0.08 * Math.sin(t / 700 + hk * 1.7), L2 = hh * 0.16, ex = hx + Math.sin(th) * L2, ey = ry + Math.cos(th) * L2; ln(c, [[hx, ry], [ex, ey]], '#5a5a62', 1); el(c, ex, ey + hh * 0.1, hh * 0.05, hh * 0.11, th, nt(S, s.g === 'pork' ? '#e08a7a' : '#f2d0a0')); } }
    if (s.g === 'fish') s.fish = true; if (false) for (var f = 0; f < 3; f++) { var fx = s.x0 + (s.x1 - s.x0) * (0.25 + f * 0.25), fl = Math.sin(t / 150 + f * 2) * (Math.sin(t / 2000 + f) > 0.5 ? 0.5 : 0.05); c.save(); c.translate(fx, ty - hh * 0.1); el(c, 0, 0, hh * 0.08, hh * 0.025, 0, '#b8c4d0'); c.rotate(fl); fp(c, [[hh * 0.07, 0], [hh * 0.13, -hh * 0.04], [hh * 0.13, hh * 0.04]], '#9aa6b8'); c.restore(); }
    /* the hanging scale at one stall: θ = θ₀·e^(−λt)·cos ωt after each weighing */
    if (k === mid) { var sxs = s.x1 - hh * 0.25, sys = ty - hh * 0.75, ph = (t / 1000) % 6, th2 = 0.6 * Math.exp(-ph * 1.2) * Math.cos(ph * 7); ln(c, [[sxs, sys - hh * 0.15], [sxs, sys]], '#5a5a62', 1); dot(c, sxs, sys + hh * 0.08, hh * 0.08, '#f4f4f4'); c.strokeStyle = '#3a3a44'; c.lineWidth = 1; c.beginPath(); c.arc(sxs, sys + hh * 0.08, hh * 0.08, 0, TAU); c.stroke(); ln(c, [[sxs, sys + hh * 0.08], [sxs + Math.sin(th2 + 0.4) * hh * 0.06, sys + hh * 0.08 - Math.cos(th2 + 0.4) * hh * 0.06]], '#d9342b', 1.2); ln(c, [[sxs, sys + hh * 0.16], [sxs, sys + hh * 0.26]], '#5a5a62', 1); fr(c, sxs - hh * 0.08, sys + hh * 0.26, hh * 0.16, hh * 0.04, '#c8ccd2'); }
    /* plastic bags on their hook, pendulums */
    if (k % 2 === 0) { var bx = s.x0 + hh * 0.06, by = ty - hh * 0.55; for (var bg = 0; bg < 2; bg++) { var a = 0.12 * Math.sin(t / 650 + bg * 1.3 + k), lx = bx + bg * hh * 0.08 + Math.sin(a) * hh * 0.18, ly = by + Math.cos(a) * hh * 0.18; ln(c, [[bx + bg * hh * 0.08, by], [lx, ly]], '#d8d8de', 1); fp(c, [[lx - hh * 0.05, ly], [lx + hh * 0.05, ly], [lx + hh * 0.06, ly + hh * 0.14], [lx - hh * 0.06, ly + hh * 0.14]], ['rgba(255,255,255,.85)', 'rgba(255,120,150,.8)'][bg]); } }
  });
  tables();
  stalls.forEach(function (s) { if (s.fish) for (var f = 0; f < 3; f++) { var fx = s.x0 + (s.x1 - s.x0) * (0.25 + f * 0.25), fl = Math.sin(t / 150 + f * 2) * (Math.sin(t / 2000 + f) > 0.5 ? 0.5 : 0.05); c.save(); c.translate(fx, ty - hh * 0.12); el(c, 0, 0, hh * 0.1, hh * 0.03, 0, '#b8c4d0'); c.rotate(fl); fp(c, [[hh * 0.09, 0], [hh * 0.16, -hh * 0.05], [hh * 0.16, hh * 0.05]], '#9aa6b8'); c.restore(); } });
  /* the buyers: busiest at dawn; a basket on the arm */
  for (var bu = 0; bu < busy; bu++) { var v = (bu % 2 ? -0.22 : 0.18) * (1 + bu * 0.2), bx2 = stroll(S, bu, v, bu * 0.31 + (S.seed % 40) / 40), bd = crew[ns + bu]; bd.dir = v > 0 ? 1 : -1;
    var near = Math.abs(Math.sin(t / 3000 + bu * 2)) < 0.3, P2 = near ? stand(0.1) : K.walkP(t / 1000 * TAU * 0.8 + bu, false); var mb = person(c, bx2, S.deck + hh * (0.22 + (bu % 2) * 0.12), hh * 0.9, P2, bd);
    fp(c, [[mb.hand[0][0] - hh * 0.07, mb.hand[0][1]], [mb.hand[0][0] + hh * 0.07, mb.hand[0][1]], [mb.hand[0][0] + hh * 0.05, mb.hand[0][1] + hh * 0.1], [mb.hand[0][0] - hh * 0.05, mb.hand[0][1] + hh * 0.1]], nt(S, '#c9a36a')); dot(c, mb.hand[0][0] - hh * 0.02, mb.hand[0][1] - hh * 0.01, hh * 0.025, '#4f8a3a'); }
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: S.x0 + hh * 0.8, x1: S.x1 - hh * 0.3, y0: still.top, y1: S.deck });
}

/* ---------------------------------------------------------------- hospital
   The hospital front: the ward block (a district hospital's three storeys under a hipped roof,
   a city hospital's tall block, a private hospital's glass), the entrance canopy, the
   emergency door in red, and an ambulance coming in on x = x₀ + d·ease(t/T) with its light bar
   turning red and blue; a wheelchair at the door; by night the wards' windows lit. Places
   that are a station, a clinic or a dentist by name get those drawings. */
function ambulance(c, S, x, y, s, dir, t) {
  var L = s * 1.4;
  paper(c, poly([[x - L / 2, y - s * 0.14], [x + L / 2, y - s * 0.14], [x + L / 2, y - s * 0.45], [x + dir * L * 0.32, y - s * 0.5], [x + dir * L * 0.26, y - s * 0.72], [x - L / 2, y - s * 0.72]]), nt(S, '#f8f8f4'), 1);
  fr(c, x - L / 2, y - s * 0.38, L, s * 0.07, '#d9342b'); fr(c, x - L / 2, y - s * 0.3, L, s * 0.03, '#2a5aa8');
  fp(c, [[x + dir * L * 0.3, y - s * 0.48], [x + dir * L * 0.27, y - s * 0.66], [x + dir * L * 0.43, y - s * 0.48]], nt(S, '#9fc6d8'));
  var cx = x - dir * L * 0.12; fr(c, cx - s * 0.03, y - s * 0.66, s * 0.06, s * 0.18, '#d9342b'); fr(c, cx - s * 0.09, y - s * 0.6, s * 0.18, s * 0.06, '#d9342b');
  var on = Math.floor(t / 250) % 2; fr(c, x - s * 0.18, y - s * 0.79, s * 0.16, s * 0.07, on ? '#ff3a3a' : '#7a2a2a'); fr(c, x - s * 0.02, y - s * 0.79, s * 0.16, s * 0.07, on ? '#2a3a7a' : '#4a7aff');
  glow(c, x + (on ? -s * 0.1 : s * 0.06), y - s * 0.76, s * (S.night ? 0.9 : 0.4), on ? '255,60,60' : '80,120,255', S.night ? 0.6 : 0.4);
  [[-0.3], [0.3]].forEach(function (p) { dot(c, x + p[0] * L, y - s * 0.12, s * 0.13, '#1e1e24'); dot(c, x + p[0] * L, y - s * 0.12, s * 0.055, '#9a9aa2'); });
}
function wheelchair(c, S, x, y, s, d, dir) {
  c.strokeStyle = '#3a3a44'; c.lineWidth = 2; c.beginPath(); c.arc(x, y - s * 0.16, s * 0.16, 0, TAU); c.stroke(); dot(c, x + dir * s * 0.25, y - s * 0.04, s * 0.04, '#3a3a44');
  ln(c, [[x - dir * s * 0.1, y - s * 0.62], [x - dir * s * 0.1, y - s * 0.3], [x + dir * s * 0.2, y - s * 0.3]], '#3a3a44', 2);
  d.dir = dir; return person(c, x, y - s * 0.04, s * 0.9, { lean: -0.05, seat: 0.3, legs: [1.45, -1.3, 1.4, -1.35], arms: [0.5, 0.8, 0.4, 0.9] }, d);
}
function hospital(S) {
  var P = placeOf(S), w = words(P), nm = [P.name, P.nameTh, P.nameEn].join(' ');
  if (/ส่งเสริมสุขภาพ|สถานีอนามัย|health promoting|รพ\.?\s*สต/i.test(nm)) return healthstation(S);
  if (/ทันต|dental|dentist|ฟัน/i.test(nm) || [].concat(P.specialty || []).indexOf('dental') >= 0) return dentist(S);
  if (/คลินิก|clinic|กายภาพ|physio|วัคซีน|lab/i.test(nm) && !/โรงพยาบาล|hospital/i.test(nm)) return clinic(S);
  var hh = S.hh, c = S.c, L = plan(S, 'hospital'), r = L.r, t = S.t;
  var big = /มหาราช|นครพิงค์|ประชานุเคราะห์|ศูนย์|ราม|กรุงเทพ|bangkok|lanna|ลานนา|แมคคอร์มิค|mccormick|ดารารัศมี|ราชเวช|เทพปัญญา|ทหาร|ค่าย|university|มหาวิทยาลัย/i.test(w), priv = /hospital|international|private|เอกชน|ราม|กรุงเทพ|bangkok|ลานนา|lanna|absolute|apex/i.test(w) && !/โรงพยาบาล(อำเภอ|ชุมชน)?[ก-๙]+$/.test(P.nameTh || '') ? 1 : 0;
  var kind = big ? (priv ? 'glass' : 'tall') : priv ? 'glass' : 'district';
  var left = (S.seed >>> 3) % 2 === 0, bw = Math.min(S.span * 0.58, hh * (4.4 + r() * 1.2)), bx0 = left ? S.x0 + hh * 0.8 : S.x1 - hh * 0.9 - bw, bx1 = bx0 + bw;
  var cw = hh * 1.7, cx0 = left ? bx1 - cw - hh * 0.3 : bx0 + hh * 0.3, cx1 = cx0 + cw, ctop = S.deck - hh * 0.95, er = left ? cx0 - hh * 0.9 : cx1 + hh * 0.1;
  var roofC = pick(r, ['#2f6f6a', '#3a5a8a', '#a8432f', '#2f8f5b']), wall = pick(r, ['#f6f2ea', '#eef2f4', '#f2ead8', '#e8f0ea']);
  var key = 'hospital|' + kind;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, 'street', r); K.setting(S);
    var b;
    if (kind === 'glass') b = facade(q, S, { kind: 'glass', x0: bx0, x1: bx1, wall: wall, trim: '#2a5aa8', roof: roofC, floors: 3, lit: S.night });
    else if (kind === 'tall') { var top = S.deck - hh * 2.25; paper(q, rect(bx0, top, bw, S.deck - top), nt(S, wall), 1.6); fr(q, bx0, top, bw, hh * 0.08, nt(S, roofC));
      for (var fl = 0; fl < 6; fl++) for (var k = 0; k < Math.floor(bw / (hh * 0.32)); k++) { var lit = S.night && ((k * 7 + fl * 3 + S.seed) % 5) > 1; fr(q, bx0 + hh * 0.14 + k * hh * 0.32, top + hh * (0.18 + fl * 0.3), hh * 0.2, hh * 0.16, lit ? '#ffe9b0' : S.night ? '#2a2f48' : '#9fc6d8'); }
      b = { top: top }; }
    else b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: wall, trim: '#2f8f5b', roof: roofC, floors: 3, lit: S.night, gable: true });
    o.top = b.top;
    /* the cross on the block */
    var crx = left ? bx0 + hh * 0.45 : bx1 - hh * 0.45, cry = (b.top || S.deck - hh * 2) + hh * 0.55; dot(q, crx, cry, hh * 0.24, nt(S, '#f8f8f4')); ICON.cross(q, S, crx, cry, hh * 0.18);
    if (S.night) glow(q, crx, cry, hh * 0.6, '120,255,160', 0.35);
    /* the entrance canopy on its posts */
    fr(q, cx0, ctop - hh * 0.04, cw, S.deck - ctop + hh * 0.04, nt(S, '#d8dce4'));
    fr(q, cx0 + hh * 0.2, ctop + hh * 0.12, cw - hh * 0.4, S.deck - ctop - hh * 0.12, S.night ? '#ffe9b0' : nt(S, '#8fb8cc'));
    paper(q, rect(cx0 - hh * 0.35, ctop - hh * 0.14, cw + hh * 0.7, hh * 0.14), nt(S, '#f4f4f4'), 1.4); fr(q, cx0 - hh * 0.35, ctop - hh * 0.02, cw + hh * 0.7, hh * 0.03, nt(S, roofC));
    [cx0 - hh * 0.3, cx1 + hh * 0.3].forEach(function (x) { fr(q, x - 3, ctop, 6, S.deck - ctop, nt(S, '#c8ccd2')); });
    /* the emergency door, lit red */
    fr(q, er, S.deck - hh * 0.75, hh * 0.8, hh * 0.75, S.night ? '#ffe9b0' : nt(S, '#cfe3ea')); fr(q, er - hh * 0.05, S.deck - hh * 0.98, hh * 0.9, hh * 0.2, '#c0392b');
    fr(q, er + hh * 0.36, S.deck - hh * 0.95, hh * 0.08, hh * 0.14, '#ffffff'); fr(q, er + hh * 0.33, S.deck - hh * 0.92, hh * 0.14, hh * 0.08, '#ffffff');
    if (S.night) glow(q, er + hh * 0.4, S.deck - hh * 0.9, hh * 0.6, '255,80,80', 0.35);
    o.sign = signAt(q, S, (cx0 + cx1) / 2, ctop - hh * 0.66, P, hh * 0.78, nt(S, '#2f6f5a'), S.night || null);
    var tx = left ? S.x1 - hh * 0.8 : S.x0 + hh * 0.8; rainTree(q, S, tx, S.deck + hh * 0.02, hh * 0.9, S.seed);
    for (var m = 0; m < 3; m++) motorbike(q, S, (left ? S.x1 - hh * 1.6 : S.x0 + hh * 1.6) + (left ? -1 : 1) * m * hh * 0.45, S.deck + hh * 0.22, hh * 0.55, 1, CLOTH2[(S.seed + m) % 8]);
    if (r() < 0.6) o.incense = spiritHouse(q, S, left ? bx1 + hh * 0.4 : bx0 - hh * 0.4, hh * 0.9, (S.seed >>> 2) % 3);
    roadPlate(q, S, left ? S.x1 - hh * 0.3 : S.x0 + hh * 0.3, P.road);
    o.er = er; return o;
  }).out || {};
  L.incense = still.incense;
  /* the ambulance: in from the road and under the canopy, every 14 s */
  var u = (t / 1000 + (S.seed % 9)) % 14, dir = left ? -1 : 1, stopX = still.er + hh * 0.4 + (left ? hh * 0.1 : -hh * 0.1), from = left ? S.x1 + hh * 1.5 : S.x0 - hh * 1.5;
  var ax = u < 5 ? lerp(from, stopX, ease(u / 5)) : u < 11 ? stopX : lerp(stopX, from + (left ? -1 : 1) * 0, ease((u - 11) / 3) * 0);
  if (u > 11) ax = lerp(stopX, from - (left ? 1 : -1) * (S.span + hh * 3), ease((u - 11) / 3));
  var crew = crowd(S, 4, { casual: 1 });
  var wc = crew[0]; wc.hairCol = '#cfcfcf'; var wx = (left ? S.x0 + hh * 0.5 : S.x1 - hh * 0.5) + hh * 0.15 * (left ? 1 : -1); wheelchair(c, S, wx + (left ? hh * 0.5 : -hh * 0.5), S.deck + hh * 0.2, hh, wc, left ? 1 : -1);
  var pu = crew[1]; pu.dir = left ? 1 : -1; person(c, wx, S.deck + hh * 0.2, hh * 0.92, { lean: 0.15, legs: [0.1 + Math.sin(t / 1400) * 0.03, 0, -0.1 - Math.sin(t / 1400) * 0.03, 0], arms: [1.2, 0.3, 1.1, 0.3] }, pu);
  if (u > 5.5 && u < 11) { var n1 = dress(crew[2], '#f8f8f4', '#f8f8f4', 2), n2 = dress(crew[3], '#2f8f9a', '#2f8f9a', 0), sx = stopX - dir * hh * (0.9 + Math.min(1, (u - 5.5) / 4) * 0.8);
    n1.dir = -dir; n2.dir = -dir; fr(c, sx - hh * 0.4, S.deck + hh * 0.05, hh * 0.8, hh * 0.05, '#f4f4f4'); fr(c, sx - hh * 0.4, S.deck + hh * 0.1, 3, hh * 0.14, '#8a8a92'); fr(c, sx + hh * 0.37, S.deck + hh * 0.1, 3, hh * 0.14, '#8a8a92');
    person(c, sx - dir * hh * 0.55, S.deck + hh * 0.26, hh * 0.92, K.walkP(t / 200, false), n1); person(c, sx + dir * hh * 0.55, S.deck + hh * 0.26, hh * 0.92, K.walkP(t / 200 + 3, false), n2); }
  ambulance(c, S, ax, S.deck + hh * 0.42, hh * 0.85, dir, t);
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: bx0, x1: bx1, y0: still.top || S.deck - hh * 2.2, y1: S.deck });
}

/* ---------------------------------------------------------------- health station
   The tambon health-promoting station (รพ.สต.): a one-storey government building, its board on
   posts, a veranda of people waiting, the village health volunteers (อสม.) in sky blue taking
   blood pressure at a table (the cuff's bulb squeezed on |sin ωt|) and weighing a baby on the
   hanging scale (θ = θ₀·cos ωt), the herb garden with its tags; home visits by afternoon, a
   fogging run at dusk (the cloud swelling as r = r₀ + vt), chickens about; quiet by night. */
function healthstation(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'healthstation'), P = L.P, r = L.r, ck = L.ck, t = S.t;
  var wk = ck.dow >= 1 && ck.dow <= 5, mode = S.night ? 'night' : !wk ? 'herbs' : ck.h < 12 ? 'check' : ck.h < 16 ? 'visit' : ck.h < 18.5 ? 'fog' : 'herbs';
  var left = (S.seed >>> 3) % 2 === 0, bw = Math.min(S.span * 0.48, hh * (3.6 + r() * 0.8)), bx0 = left ? S.x0 + hh * 0.8 : S.x1 - hh * 0.9 - bw, bx1 = bx0 + bw;
  var gx0 = left ? bx1 + hh * 0.4 : S.x0 + hh * 0.9, gx1 = left ? S.x1 - hh * 0.9 : bx0 - hh * 0.4, roofC = pick(r, ['#2f6f6a', '#3a5a8a', '#2f8f5b', '#a8432f']);
  var key = 'healthstation|' + mode;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, 'lane', r); K.setting(S);
    var b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: pick(r, ['#f6f2ea', '#eef4f0', '#f2ead8']), trim: '#2f8f5b', roof: roofC, floors: 1, gf: hh * 1.0, gable: r() < 0.6, doorAt: 2 });
    o.top = b.top;
    /* the veranda: its bench and posters */
    fr(q, bx0 + hh * 0.2, S.deck - hh * 0.3, bw * 0.4, hh * 0.05, nt(S, '#3a6ac0')); fr(q, bx0 + hh * 0.25, S.deck - hh * 0.25, 3, hh * 0.25, '#8a8a92'); fr(q, bx0 + hh * 0.15 + bw * 0.4, S.deck - hh * 0.25, 3, hh * 0.25, '#8a8a92');
    /* the herb garden: beds and tags */
    var hx0 = lerp(gx0, gx1, 0.45), hx1 = gx1;
    paper(q, rect(hx0, S.deck + hh * 0.06, hx1 - hx0, hh * 0.12), nt(S, '#7a5a3a'), 0.6);
    for (var x = hx0 + hh * 0.15, i = 0; x < hx1 - hh * 0.1; x += hh * 0.32, i++) { if (i % 3 === 0) { c = q; for (var g = -2; g <= 2; g++) ln(q, [[x, S.deck + hh * 0.08], [x + g * hh * 0.04, S.deck - hh * 0.2]], nt(S, '#7aa84a'), 1.4); } else shrub(q, S, x, S.deck + hh * 0.12, hh * 0.55, i);
      fr(q, x + hh * 0.08, S.deck - hh * 0.05, hh * 0.1, hh * 0.06, nt(S, '#f8f8f4')); ln(q, [[x + hh * 0.13, S.deck + hh * 0.01], [x + hh * 0.13, S.deck + hh * 0.1]], nt(S, '#f8f8f4'), 1); }
    c = S.c;
    /* the board on two posts in front */
    var sx = (bx0 + bx1) / 2; o.sign = signAt(q, S, sx, b.top - hh * 0.05, P, hh * 0.72, nt(S, '#2f6f5a'), null);
    o.flag = left ? bx1 + hh * 0.25 : bx0 - hh * 0.25; paper(q, rect(o.flag - hh * 0.15, S.deck - hh * 0.08, hh * 0.3, hh * 0.08), nt(S, '#f2ece0'), 0.8); fr(q, o.flag - 1.5, S.deck - hh * 2.0, 3, hh * 1.95, nt(S, '#d8d8de'));
    if (mode === 'check') { var tx = lerp(gx0, gx1, 0.18); fp(q, [[tx - hh * 0.7, S.deck - hh * 1.15], [tx + hh * 0.7, S.deck - hh * 1.15], [tx + hh * 0.8, S.deck - hh * 0.95], [tx - hh * 0.8, S.deck - hh * 0.95]], nt(S, '#f4f4f4')); for (var tp = 0; tp < 5; tp++) fp(q, [[tx - hh * 0.8 + tp * hh * 0.32, S.deck - hh * 0.95], [tx - hh * 0.64 + tp * hh * 0.32, S.deck - hh * 0.85], [tx - hh * 0.48 + tp * hh * 0.32, S.deck - hh * 0.95]], nt(S, '#2a7ac0'));
      [tx - hh * 0.7, tx + hh * 0.7].forEach(function (px) { fr(q, px - 1.5, S.deck - hh * 1.15, 3, hh * 1.2, nt(S, '#8a8a92')); }); o.tent = tx; }
    var side = left ? S.x1 - hh * 0.6 : S.x0 + hh * 0.6; if (r() < 0.5) banana(q, S, side, S.deck, hh * 1.05, 2); else rainTree(q, S, side, S.deck + hh * 0.02, hh * 0.85, S.seed);
    if (r() < 0.6) o.incense = spiritHouse(q, S, left ? bx0 - hh * 0.35 : bx1 + hh * 0.35, hh * 0.85, (S.seed >>> 2) % 3);
    motorbike(q, S, left ? bx1 - hh * 0.3 : bx0 + hh * 0.3, S.deck + hh * 0.36, hh * 0.6, left ? -1 : 1, '#f4f4f4');
    fr(q, (left ? bx1 - hh * 0.3 : bx0 + hh * 0.3) - (left ? -1 : 1) * hh * 0.2 - hh * 0.1, S.deck + hh * 0.06, hh * 0.2, hh * 0.13, nt(S, '#2a7ac0'));
    if (S.night) { o.lamp = [bx0 + bw * 0.5, b.door.y0 - hh * 0.05]; bulb(q, S, o.lamp[0], o.lamp[1], hh, true); }
    return o;
  }).out || {};
  L.incense = still.incense; L.lamp = still.lamp;
  if (still.flag != null && !S.night) thaiFlag(c, still.flag + 1.5, S.deck - hh * 1.95, hh * 0.42, t, 2, false);
  var crew = crowd(S, 8, { casual: 0.5, sin: 0.3, mohom: 0.2 });
  function vhv(d) { dressUp(d, '#7ec0ea', d.garb === 'sin' ? d.low : '#2a3a5a'); d.garb = 'casual'; return d; }
  if (mode === 'check') {
    /* waiting on the bench */
    for (var i = 0; i < 2; i++) { var e = crew[i]; e.hairCol = '#cfcfcf'; e.dir = 1; person(c, bx0 + hh * (0.45 + i * 0.5), S.deck - hh * 0.02, hh * 0.86, { lean: 0.05, seat: 0.33, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4, 0.6, 0.3, 0.7] }, e); }
    var tx = still.tent, sq = Math.abs(Math.sin(t / 300)); fr(c, tx - hh * 0.35, S.deck - hh * 0.36, hh * 0.7, hh * 0.05, nt(S, '#f4f4f4')); fr(c, tx - hh * 0.3, S.deck - hh * 0.31, 3, hh * 0.31, '#8a8a92'); fr(c, tx + hh * 0.28, S.deck - hh * 0.31, 3, hh * 0.31, '#8a8a92');
    var v1 = vhv(crew[2]); v1.dir = -1; var mv = person(c, tx + hh * 0.5, S.deck + hh * 0.02, hh * 0.88, { lean: 0.05, seat: 0.33, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.2, 0.8, 0.9, 0.9 + sq * 0.2] }, v1);
    dot(c, mv.hand[1][0], mv.hand[1][1], hh * (0.03 + sq * 0.008), '#2a2a30');
    var pt = crew[3]; pt.hairCol = '#bdbdbd'; pt.dir = 1; var mp = person(c, tx - hh * 0.5, S.deck + hh * 0.02, hh * 0.86, { lean: 0.05, seat: 0.33, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.3, 0.2, 0.3, 0.7] }, pt);
    fr(c, mp.hand[0][0] - hh * 0.1, mp.hand[0][1] - hh * 0.03, hh * 0.08, hh * 0.05, '#2a3a5a'); ln(c, [[mp.hand[0][0] - hh * 0.06, mp.hand[0][1]], mv.hand[1]], '#3a3a44', 1);
    /* the baby on the hanging scale */
    var scx = lerp(gx0, gx1, 0.42), scy = S.deck - hh * 1.1, th = 0.15 * Math.cos(t / 1000 * TAU / 1.6); ln(c, [[scx, S.deck - hh * 1.25], [scx, scy]], '#5a5a62', 1); dot(c, scx, scy + hh * 0.06, hh * 0.06, '#f4f4f4'); ln(c, [[scx, scy + hh * 0.06], [scx + Math.sin(th * 3 + 0.5) * hh * 0.05, scy + hh * 0.06 - Math.cos(th * 3 + 0.5) * hh * 0.05]], '#d9342b', 1);
    var bx = scx + Math.sin(th) * hh * 0.3, by = scy + hh * 0.12 + Math.cos(th) * hh * 0.3; ln(c, [[scx, scy + hh * 0.12], [bx - hh * 0.1, by], [bx + hh * 0.1, by], [scx, scy + hh * 0.12]], '#c9a36a', 1); fp(c, [[bx - hh * 0.12, by], [bx + hh * 0.12, by], [bx, by + hh * 0.1]], '#e5567f'); dot(c, bx + hh * 0.05, by - hh * 0.02, hh * 0.04, K.SKIN[1]);
    var mo = crew[4]; mo.dir = -1; person(c, scx + hh * 0.4, S.deck + hh * 0.12, hh * 0.9, { lean: 0.05, legs: [0.06, 0, -0.06, 0], arms: [1.5, 0.3, 0.3, 0.3] }, mo);
  } else if (mode === 'visit') {
    for (var v = 0; v < 2; v++) { var vd = vhv(crew[v + 2]), vv = (left ? 0.2 : -0.2), vx = stroll(S, v, vv, v * 0.3 + 0.2); vd.dir = vv > 0 ? 1 : -1; var mm = person(c, vx, S.deck + hh * (0.2 + v * 0.1), hh * 0.9, K.walkP(t / 1000 * TAU * 0.8 + v, false), vd); fr(c, mm.hand[0][0] - hh * 0.05, mm.hand[0][1], hh * 0.12, hh * 0.1, '#2a7ac0'); }
    var w2 = crew[0]; w2.hairCol = '#cfcfcf'; w2.dir = 1; person(c, bx0 + hh * 0.5, S.deck - hh * 0.02, hh * 0.86, { lean: 0.05, seat: 0.33, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4, 0.6, 0.3, 0.7] }, w2);
  } else if (mode === 'fog') {   /* the fogging run: the machine's cloud swelling and drifting, r = r₀ + vt */
    var fg = vhv(crew[2]), fx = stroll(S, 0, left ? 0.12 : -0.12, 0.4); fg.dir = left ? 1 : -1; var mf = person(c, fx, S.deck + hh * 0.25, hh * 0.92, K.walkP(t / 1000 * TAU * 0.6, false), fg);
    mask(c, mf, hh * 0.92, fg.dir, '#f4f4f4'); var nz = [mf.hand[0][0] + fg.dir * hh * 0.25, mf.hand[0][1] - hh * 0.02]; fr(c, mf.hand[0][0] - hh * 0.08, mf.hand[0][1] - hh * 0.06, hh * 0.18, hh * 0.1, '#c0392b'); ln(c, [mf.hand[0], nz], '#5a5a62', 2);
    for (var p = 0; p < 9; p++) { var u = (t / 3200 + p / 9) % 1; dot(c, nz[0] + fg.dir * u * hh * 1.6 + Math.sin(u * 5 + p) * hh * 0.1, nz[1] - u * hh * 0.4, hh * (0.08 + u * 0.4), 'rgba(245,245,245,' + (0.55 * (1 - u)).toFixed(2) + ')'); }
  } else if (mode === 'herbs') {
    var hd = crew[5]; hd.garb = 'sin'; hd.hair = 2; hd.dir = 1; var hx = lerp(gx0, gx1, 0.55), pour = 0.5 + 0.5 * Math.sin(t / 900);
    var mh = person(c, hx, S.deck + hh * 0.2, hh * 0.9, { lean: 0.3, legs: [0.06, 0, -0.06, 0], arms: [1.3, 0.4 + pour * 0.2, 0.8, 0.5] }, hd);
    fr(c, mh.hand[0][0] - hh * 0.04, mh.hand[0][1] - hh * 0.02, hh * 0.12, hh * 0.1, '#2f8f5b'); for (var dd = 0; dd < 4; dd++) { var du = (t / 600 + dd / 4) % 1; dot(c, mh.hand[0][0] + hh * 0.12 + du * hh * 0.05, mh.hand[0][1] + du * hh * 0.3, 1.4, 'rgba(150,200,255,.9)'); }
  } else L.dog = [bx0 + bw * 0.5, S.deck + hh * 0.25, true];
  if (!S.night) for (var ch = 0; ch < 2 + (S.seed % 2); ch++) chicken(c, S, lerp(gx0, gx1, 0.2 + ch * 0.28) + Math.sin(t / 3000 + ch) * hh * 0.2, S.deck + hh * (0.32 + ch % 2 * 0.1), hh * 0.5, ch + S.seed, t);
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: bx0, x1: bx1, y0: still.top || S.deck - hh * 1.6, y1: S.deck });
}

/* ---------------------------------------------------------------- park
   A park by the clock: joggers and tai chi at dawn (the slow arms on cos ωt), children feeding
   the fish and swan boats on the pond by day (the fountain's drops on parabolas), aerobics at
   dusk, lamps and fireflies by night (each blinks on a sin⁸ pulse). A reservoir gets its raft
   huts and a fisherman's line; a forest park its trail and hikers; a playground its swings
   (θ = θ₀·cos ωt) and slide. */
function parkKind(P) {
  var w = words(P);
  if (subOf(P, 'playground') || /playground|สนามเด็กเล่น|kids|เด็ก|castle|คาสเซิล/i.test(w)) return 'play';
  if (/skate|bmx|pump ?track|extreme|สเก็ต/i.test(w)) return 'skate';
  if (subOf(P, 'water') || /อ่างเก็บน้ำ|ทะเลสาบ|reservoir|lake|หนอง|บึง|สระ|pond|ฝาย|เขื่อน|dam|น้ำตก|waterfall|คลอง/i.test(w)) return 'water';
  if (subOf(P, 'nature') || /อุทยาน|national park|forest|ป่า|ดอย|doi|trail|nature|ธรรมชาติ/i.test(w)) return 'forest';
  return 'park';
}
function swan(c, S, x, y, s, k, t, dir) {
  c.save(); c.translate(x, 0); c.scale(dir || 1, 1); c.translate(-x, 0);
  var b = Math.sin(t / 700 + k) * s * 0.03; el(c, x, y + b, s * 0.4, s * 0.16, 0, nt(S, '#f8f8f4')); fp(c, [[x - s * 0.35, y - s * 0.05 + b], [x - s * 0.5, y - s * 0.3 + b], [x - s * 0.2, y - s * 0.12 + b]], nt(S, '#f0f0ea'));
  c.strokeStyle = nt(S, '#f8f8f4'); c.lineWidth = s * 0.08; c.beginPath(); c.moveTo(x + s * 0.28, y - s * 0.05 + b); c.quadraticCurveTo(x + s * 0.5, y - s * 0.3 + b, x + s * 0.32, y - s * 0.55 + b); c.stroke(); dot(c, x + s * 0.34, y - s * 0.56 + b, s * 0.07, nt(S, '#f8f8f4')); fp(c, [[x + s * 0.39, y - s * 0.58 + b], [x + s * 0.5, y - s * 0.54 + b], [x + s * 0.39, y - s * 0.52 + b]], '#e07a2a');
  fr(c, x - s * 0.15, y - s * 0.28 + b, s * 0.3, s * 0.12, nt(S, ['#e5567f', '#4d8fd1', '#f2c94c'][k % 3]));
  c.restore();
}
function park(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'park'), P = L.P, r = L.r, ck = L.ck, t = S.t, kind = parkKind(P), h = ck.h;
  var mode = S.night ? 'night' : kind === 'water' || kind === 'forest' ? 'wild' : h < 8.5 ? 'dawn' : h < 16.5 ? 'day' : 'dusk';
  var pondL = (S.seed >>> 3) % 2 === 0, px0 = pondL ? S.x0 + hh * 0.9 : S.x0 + S.span * 0.52, px1 = pondL ? S.x0 + S.span * 0.5 : S.x1 - hh * 0.9, py = S.deck + (S.H - S.deck) * 0.45;
  var key = 'park|' + kind + '|' + mode;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, 'lawn', r); K.setting(S);
    /* trees in a row behind, dealt kinds */
    var n = Math.max(3, Math.floor(S.span / (hh * 1.6)));
    for (var i = 0; i < n; i++) { var tx = S.x0 + hh * 0.9 + (i + r() * 0.4) * (S.span - hh * 1.8) / n; if (kind === 'forest' || i % 2 === 0) rainTree(q, S, tx, S.deck - hh * 0.05, hh * (0.7 + r() * 0.35), i + S.seed); else if (r() < 0.5) frangipani(q, S, tx, S.deck - hh * 0.05, hh * 0.95, i); else bougainvillea(q, S, tx, S.deck - hh * 0.04, hh * 0.85, i + S.seed); }
    if (kind === 'water' || kind === 'park') {   /* the pond or the reservoir */
      var wx0 = kind === 'water' ? S.x0 - 4 : px0, wx1 = kind === 'water' ? S.x1 + 4 : px1, wy = kind === 'water' ? S.deck + hh * 0.05 : py - hh * 0.12;
      paper(q, function (p) { p.beginPath(); p.ellipse((wx0 + wx1) / 2, wy + (S.H - wy) * 0.4, (wx1 - wx0) / 2, (S.H - wy) * (kind === 'water' ? 0.9 : 0.55), 0, 0, TAU); }, nt(S, '#4b8fc9'), 0.8);
      if (kind === 'water') { for (var rf = 0; rf < 2; rf++) { var rx = S.x0 + S.span * (0.3 + rf * 0.35); fr(q, rx - hh * 0.5, S.deck + hh * 0.18, hh * 1.0, hh * 0.08, nt(S, '#c9a36a')); for (var bb = 0; bb < 6; bb++) dot(q, rx - hh * 0.45 + bb * hh * 0.18, S.deck + hh * 0.26, hh * 0.04, nt(S, '#a8843a')); fr(q, rx - hh * 0.4, S.deck - hh * 0.4, 3, hh * 0.58, nt(S, '#7a5a3a')); fr(q, rx + hh * 0.38, S.deck - hh * 0.4, 3, hh * 0.58, nt(S, '#7a5a3a')); paper(q, poly([[rx - hh * 0.55, S.deck - hh * 0.36], [rx, S.deck - hh * 0.68], [rx + hh * 0.55, S.deck - hh * 0.36]]), nt(S, '#b89a52'), 1); } o.raft = S.x0 + S.span * 0.3; }
      else { o.pond = [(wx0 + wx1) / 2, wy + (S.H - wy) * 0.4]; paper(q, rect((wx0 + wx1) / 2 - hh * 0.12, wy - hh * 0.05, hh * 0.24, hh * 0.1), nt(S, '#d8d0c0'), 0.6); }
    }
    if (kind === 'forest') { o.tents = [];
      for (var tn = 0; tn < 2; tn++) { var tx3 = S.x0 + S.span * (0.36 + tn * 0.2) + r() * hh * 0.4, tc3 = pick(r, ['#e07a2a', '#2f8f5b', '#2a5aa8', '#e8b84a', '#c0392b']); paper(q, poly([[tx3 - hh * 0.4, S.deck + hh * 0.22], [tx3, S.deck - hh * 0.32], [tx3 + hh * 0.4, S.deck + hh * 0.22]]), nt(S, tc3), 1); fp(q, [[tx3 - hh * 0.08, S.deck + hh * 0.22], [tx3, S.deck - hh * 0.05], [tx3 + hh * 0.08, S.deck + hh * 0.22]], S.night ? '#ffcf7a' : nt(S, '#3a2a20')); o.tents.push(tx3); }
      var tp = S.x0 + S.span * 0.82; fr(q, tp - 2, S.deck - hh * 0.8, 4, hh * 0.9, nt(S, '#7a4a2a')); fp(q, [[tp, S.deck - hh * 0.78], [tp + hh * 0.42, S.deck - hh * 0.78], [tp + hh * 0.52, S.deck - hh * 0.7], [tp + hh * 0.42, S.deck - hh * 0.62], [tp, S.deck - hh * 0.62]], nt(S, '#8a5a3a')); fp(q, [[tp, S.deck - hh * 0.56], [tp - hh * 0.42, S.deck - hh * 0.56], [tp - hh * 0.52, S.deck - hh * 0.48], [tp - hh * 0.42, S.deck - hh * 0.4], [tp, S.deck - hh * 0.4]], nt(S, '#8a5a3a'));
      for (var f = 0; f < 3; f++) bamboo2(q, S, S.x0 + S.span * (0.2 + f * 0.3), S.deck + hh * 0.05, hh, f); paper(q, function (p) { jag(p, [[S.x0 - 4, S.deck + hh * 0.2], [S.x0 + S.span * 0.3, S.deck + hh * 0.14], [S.x0 + S.span * 0.7, S.deck + hh * 0.28], [S.x1 + 4, S.deck + hh * 0.2], [S.x1 + 4, S.deck + hh * 0.36], [S.x0 - 4, S.deck + hh * 0.36]], 9, 2); }, nt(S, '#b89a6a'), 0.6); }
    if (kind === 'play') { var sx = S.x0 + S.span * 0.3; ln(q, [[sx - hh * 0.6, S.deck + hh * 0.2], [sx - hh * 0.45, S.deck - hh * 1.1], [sx + hh * 0.45, S.deck - hh * 1.1], [sx + hh * 0.6, S.deck + hh * 0.2]], nt(S, '#e5567f'), 3); o.swing = [sx, S.deck - hh * 1.1];
      var sl = S.x0 + S.span * 0.66; fr(q, sl - hh * 0.3, S.deck - hh * 0.9, hh * 0.3, hh * 1.1, nt(S, '#f2c94c')); fp(q, [[sl, S.deck - hh * 0.9], [sl + hh * 0.9, S.deck + hh * 0.18], [sl + hh * 0.75, S.deck + hh * 0.2], [sl, S.deck - hh * 0.75]], nt(S, '#4d8fd1')); o.slide = [sl, S.deck - hh * 0.9]; }
    if (kind === 'skate') { var rx2 = S.x0 + S.span * 0.5; paper(q, function (p) { p.beginPath(); p.moveTo(rx2 - hh * 1.6, S.deck + hh * 0.2); p.quadraticCurveTo(rx2 - hh * 1.4, S.deck - hh * 0.7, rx2 - hh * 1.1, S.deck - hh * 0.7); p.lineTo(rx2 - hh * 1.1, S.deck + hh * 0.2); p.closePath(); p.moveTo(rx2 + hh * 1.6, S.deck + hh * 0.2); p.quadraticCurveTo(rx2 + hh * 1.4, S.deck - hh * 0.7, rx2 + hh * 1.1, S.deck - hh * 0.7); p.lineTo(rx2 + hh * 1.1, S.deck + hh * 0.2); p.closePath(); }, nt(S, '#b8bcc4'), 1); fr(q, rx2 - hh * 1.1, S.deck + hh * 0.18, hh * 2.2, hh * 0.06, nt(S, '#a8acb4')); o.ramp = rx2; }
    /* lamp posts and benches along the path */
    for (var lp = 0; lp < 3; lp++) { var lx = S.x0 + S.span * (0.18 + lp * 0.32); fr(q, lx - 1.5, S.deck - hh * 1.1, 3, hh * 1.2, nt(S, '#3a3a44')); el(q, lx, S.deck - hh * 1.12, hh * 0.06, hh * 0.05, 0, S.night ? '#fff3c4' : nt(S, '#e8e8e8')); if (S.night) glow(q, lx, S.deck - hh * 1.1, hh * 0.7, '255,230,160', 0.45); }
    if (kind !== 'water') { var bx = pondL ? S.x1 - hh * 1.6 : S.x0 + hh * 1.2; fr(q, bx, S.deck + hh * 0.05, hh * 0.6, hh * 0.05, nt(S, '#8a5a3a')); fr(q, bx, S.deck - hh * 0.1, hh * 0.6, hh * 0.04, nt(S, '#8a5a3a')); fr(q, bx + 3, S.deck + hh * 0.1, 3, hh * 0.1, '#3a3a44'); fr(q, bx + hh * 0.55, S.deck + hh * 0.1, 3, hh * 0.1, '#3a3a44'); o.bench = bx + hh * 0.3; }
    /* the name on a standing board at the gate */
    var gx = pondL ? S.x1 - hh * 1.4 : S.x0 + hh * 1.5; paper(q, rect(gx - hh * 0.04, S.deck - hh * 1.05, hh * 0.08, hh * 1.05), nt(S, '#7a4a2a'), 0.8);
    o.sign = signAt(q, S, gx, S.deck - hh * 1.6, P, hh * 0.78, nt(S, '#3f6a3a'), null);
    marigolds(q, S, gx - hh * 0.6, gx + hh * 0.6, S.deck - hh * 1.66, hh * 0.08);
    if (r() < 0.5) o.incense = spiritHouse(q, S, pondL ? S.x1 - hh * 0.55 : S.x0 + hh * 0.55, hh * 0.85, (S.seed >>> 2) % 3);
    return o;
  }).out || {};
  L.incense = still.incense;
  var crew = crowd(S, 9, { casual: 0.7, sin: 0.15, mohom: 0.15 }), i2;
  if (still.pond) { /* the fountain: drops on parabolas */ var fx = still.pond[0], fy = still.pond[1] - (S.H - S.deck) * 0.2; for (var d = 0; d < 14; d++) { var u = ((t / 1000) / 1.2 + d / 14) % 1, vx = (d % 7 - 3) * hh * 0.12, yy = fy - hh * 0.9 * u * 2 + hh * 1.8 * u * u * 2 * 0.5 * 2; dot(c, fx + vx * u, Math.min(fy, fy - hh * 1.8 * u + hh * 1.8 * u * u), 1.6, 'rgba(225,245,255,.9)'); }
    if (mode !== 'night') { swan(c, S, still.pond[0] + Math.sin(t / 6000) * (px1 - px0) * 0.28, still.pond[1] + 2, hh * 0.55, S.seed, t, Math.cos(t / 6000) >= 0 ? 1 : -1); swan(c, S, still.pond[0] - Math.sin(t / 7000 + 1) * (px1 - px0) * 0.3, still.pond[1] + hh * 0.08, hh * 0.5, S.seed + 1, t, Math.cos(t / 7000 + 1) > 0 ? -1 : 1); } }
  if (still.raft != null && mode !== 'night') { var fs = crew[0]; fs.dir = 1; var mf = person(c, still.raft + hh * 0.2, S.deck + hh * 0.18, hh * 0.84, { lean: 0.1, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.6, 0.2, 1.4, 0.3] }, fs); var bend = Math.sin(t / 1300) * 0.05; c.strokeStyle = '#a8843a'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(mf.hand[0][0], mf.hand[0][1]); c.quadraticCurveTo(mf.hand[0][0] + hh * 0.6, mf.hand[0][1] - hh * (0.6 + bend), mf.hand[0][0] + hh * 1.0, mf.hand[0][1] - hh * 0.4); c.stroke(); ln(c, [[mf.hand[0][0] + hh * 1.0, mf.hand[0][1] - hh * 0.4], [mf.hand[0][0] + hh * 1.05, S.deck + hh * 0.42]], 'rgba(255,255,255,.6)', 0.8); dot(c, mf.hand[0][0] + hh * 1.05, S.deck + hh * 0.42 + Math.sin(t / 400) * 1.5, 2, '#d9342b'); }
  if (still.swing && mode !== 'night') { var th = 0.6 * Math.cos(t / 1000 * TAU / 2.2), sl = hh * 0.85, kx = still.swing[0] + Math.sin(th) * sl, ky = still.swing[1] + Math.cos(th) * sl; ln(c, [still.swing, [kx, ky]], '#5a5a62', 1.2); fr(c, kx - hh * 0.1, ky, hh * 0.2, 3, '#7a4a2a'); var kd = crew[1]; kd.dir = 1; c.save(); c.translate(kx, ky); c.rotate(-th); person(c, 0, hh * 0.12, hh * 0.6, { lean: 0, seat: 0.24, legs: [1.4 - th, -1.2, 1.3 - th, -1.2], arms: [2.8, 0, 2.9, 0] }, kd); c.restore();
    var su = (t / 3000) % 1, sk = crew[2]; sk.dir = 1; person(c, still.slide[0] + su * hh * 0.85, still.slide[1] + su * hh * 1.05 + hh * 0.05, hh * 0.6, { lean: -0.3, seat: 0.24, legs: [1.4, -0.3, 1.3, -0.3], arms: [2.6, 0, 2.7, 0] }, sk); }
  if (still.ramp != null && mode !== 'night') { var ph = Math.sin(t / 1000 * TAU / 3), rxx = still.ramp + ph * hh * 1.3, ryy = S.deck + hh * 0.18 - Math.pow(Math.abs(ph), 3) * hh * 0.85, sd = crew[3]; sd.dir = Math.cos(t / 1000 * TAU / 3) > 0 ? 1 : -1; fr(c, rxx - hh * 0.18, ryy - 3, hh * 0.36, 3, '#2a2a30'); person(c, rxx, ryy - 3, hh * 0.84, { lean: 0.1, legs: [0.4, -0.5, -0.3, -0.4], arms: [1.6, 0.2, -1.2, 0.2] }, sd); }
  if (mode === 'wild' && kind === 'water') {   /* a kayak paddled across, the blade on sin ωt */
    var kx2 = stroll(S, 2, 0.25, 0.3), kd2 = crew[2]; kd2.dir = 1; var ky2 = S.deck + (S.H - S.deck) * 0.55; fp(c, [[kx2 - hh * 0.5, ky2], [kx2 + hh * 0.5, ky2], [kx2 + hh * 0.35, ky2 + hh * 0.08], [kx2 - hh * 0.35, ky2 + hh * 0.08]], '#e8b84a');
    var pa = Math.sin(t / 500); person(c, kx2, ky2 + hh * 0.02, hh * 0.78, { lean: 0.05, seat: 0.1, legs: [1.5, 0, 1.45, 0], arms: [1.2 + pa * 0.4, 0.6, 1.2 - pa * 0.4, 0.6] }, kd2); ln(c, [[kx2 - hh * 0.35 + pa * hh * 0.1, ky2 - hh * 0.35 + pa * hh * 0.3], [kx2 + hh * 0.35 + pa * hh * 0.1, ky2 - hh * 0.35 - pa * hh * 0.3]], '#3a3a44', 2);
  } else if (mode === 'wild') {   /* hikers along the trail with their packs */
    for (i2 = 0; i2 < 2; i2++) { var hv = 0.3 + i2 * 0.05, hd2 = crew[4 + i2]; hd2.dir = 1; var mh2 = person(c, stroll(S, i2, hv, i2 * 0.12 + 0.3), S.deck + hh * 0.3, hh * 0.9, K.walkP(t / 1000 * TAU * 0.8 + i2, false), hd2); fr(c, mh2.sh[0] - hh * 0.2, mh2.sh[1] - hh * 0.02, hh * 0.13, hh * 0.24, ['#e07a2a', '#2a5aa8'][i2]); }
  } else if (mode === 'dawn') {   /* joggers and the tai chi group */
    for (i2 = 0; i2 < 2; i2++) { var jv = i2 ? -0.75 : 0.65, jd = crew[4 + i2]; jd.dir = jv > 0 ? 1 : -1; person(c, stroll(S, i2, jv, i2 * 0.4), S.deck + hh * (0.3 + i2 * 0.1), hh * 0.9, K.walkP(t / 1000 * TAU * 1.3 + i2, true), jd); }
    var tc = 0.5 - 0.5 * Math.cos(t / 1000 * TAU / 6); for (i2 = 0; i2 < 3; i2++) { var td = crew[6 + i2 % 3]; td.dir = 1; td.hairCol = '#cfcfcf'; person(c, (still.bench || S.x0 + S.span * 0.5) + (i2 - 1) * hh * 0.5, S.deck + hh * 0.12, hh * 0.88, { lean: 0, seat: 0.47 - tc * 0.06, legs: [0.25, -tc * 0.4, -0.25, -tc * 0.4], arms: [0.6 + tc * 1.2, 0.8 - tc * 0.4, 0.4 + tc * 1.4, 0.6] }, td); }
  } else if (mode === 'day') {
    if (still.bench != null) { var rd = crew[4]; rd.hairCol = '#bdbdbd'; rd.dir = 1; var mr = person(c, still.bench, S.deck + hh * 0.06, hh * 0.86, { lean: 0.1, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [1.2, 1.0, 1.1, 1.1] }, rd); fr(c, mr.hand[0][0] - hh * 0.02, mr.hand[0][1] - hh * 0.14, hh * 0.18, hh * 0.13, '#f4f0e0'); }
    if (still.pond) { var fd = crew[5]; fd.dir = pondL ? 1 : -1; var fk = (t / 1500) % 1; var mk = person(c, still.pond[0] + (pondL ? -1 : 1) * hh * 1.1, S.deck + hh * 0.05, hh * 0.62, { lean: 0.2, legs: [0.06, 0, -0.06, 0], arms: [1.4 + fk * 0.6, 0.2, 0.4, 0.3] }, fd); if (fk > 0.4) dot(c, mk.hand[0][0] + fd.dir * fk * hh * 0.5, mk.hand[0][1] + (fk - 0.4) * (fk - 0.4) * hh * 3, 1.5, '#c9a36a'); }
    var pv = 0.35, wd = crew[6]; wd.dir = 1; person(c, stroll(S, 0, pv, 0.6), S.deck + hh * 0.34, hh * 0.9, K.walkP(t / 1000 * TAU * 0.8, false), wd);
  } else if (mode === 'dusk') {   /* aerobics on the lawn, the beat |sin ωt| */
    var beat = t / 1000 * TAU * 1.1, s1 = Math.sin(beat), s2 = Math.abs(s1), na = S.phone ? 4 : 6;
    for (i2 = 0; i2 < na; i2++) { var ax = S.x0 + S.span * (0.2 + i2 * 0.6 / (na - 1)), ad = crew[i2]; ad.dir = 1; person(c, ax, S.deck + hh * (0.18 + (i2 % 2) * 0.12), hh * 0.86, { lean: 0, lift: s2 * 0.02, legs: [0.2 + s1 * 0.3, 0, -0.2 + s1 * 0.3, 0], arms: [2.6 + s1 * 0.5, 0.2, 2.6 - s1 * 0.5, 0.2] }, ad); }
    K.notes(c, S.x0 + S.span * 0.5, S.deck - hh * 0.6, t, 3, '#fff6d6');
  } else {   /* night: a couple on the bench (a campfire in the forest), fireflies on a sin⁸ pulse */
    if (still.tents) { var cfx = still.tents[0] + hh * 0.7; for (var fl2 = 0; fl2 < 3; fl2++) { var fh2 = hh * (0.18 + 0.06 * Math.sin(t / 90 + fl2 * 2)); fp(c, [[cfx - hh * 0.08 + fl2 * hh * 0.06, S.deck + hh * 0.24], [cfx - hh * 0.05 + fl2 * hh * 0.06, S.deck + hh * 0.24 - fh2], [cfx + fl2 * hh * 0.06, S.deck + hh * 0.24]], fl2 % 2 ? '#ffcf4a' : '#ff7a2a'); } glow(c, cfx, S.deck + hh * 0.15, hh * 0.8, '255,160,60', 0.5); }
    if (still.bench != null) { for (i2 = 0; i2 < 2; i2++) { var cd = crew[i2]; cd.dir = i2 ? -1 : 1; person(c, still.bench + (i2 ? hh * 0.12 : -hh * 0.12), S.deck + hh * 0.06, hh * 0.86, { lean: 0.15, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.5, 0.6, 0.3, 0.7] }, cd); } }
    var fr2 = K.rnd(S.seed + 4); for (i2 = 0; i2 < 14; i2++) { var fx2 = S.x0 + fr2() * S.span, fy2 = S.deck - hh * (0.2 + fr2() * 1.2), ph2 = fr2() * TAU, b2 = Math.pow(Math.max(0, Math.sin(t / 700 + ph2)), 8); glow(c, fx2 + Math.sin(t / 1900 + ph2) * hh * 0.2, fy2 + Math.cos(t / 2300 + ph2) * hh * 0.1, hh * 0.1, '220,255,120', b2 * 0.9); }
  }
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: S.x0 + hh * 0.6, x1: S.x1 - hh * 0.6, y0: S.deck - hh * 1.8, y1: S.H });
}
function bamboo2(c, S, x, y, hh, k) {
  for (var i = 0; i < 5; i++) { var bx = x + (i - 2) * hh * 0.07, ht = hh * (1.4 + (i % 3) * 0.2), bend = (i - 2) * 0.12, tx = bx + Math.sin(bend) * ht, ty = y - Math.cos(bend) * ht * 0.98;
    c.strokeStyle = nt(S, '#5a8a3a'); c.lineWidth = Math.max(1.5, hh * 0.035); c.beginPath(); c.moveTo(bx, y); c.quadraticCurveTo(bx + Math.sin(bend) * ht * 0.3, y - ht * 0.6, tx, ty); c.stroke();
    for (var l = 0; l < 4; l++) { var lu = 0.45 + l * 0.17; el(c, lerp(bx, tx, lu * lu) + (l % 2 ? 1 : -1) * hh * 0.08, lerp(y, ty, lu), hh * 0.1, hh * 0.025, (l % 2 ? 0.4 : -0.4), nt(S, '#4f8a3a')); } }
}

/* ---------------------------------------------------------------- university
   A campus: the faculty building (a Lanna-gabled hall, a brick block, glass), the road under its
   rain trees, students in white shirts and black on foot and on bicycles (x = x₀ + vt), the
   university's colour where its name says which (Chiang Mai's purple, with its purple tram;
   Mae Fah Luang's red and gold; Maejo's green), a graduate with garlands and a photographer on
   some days; a polytechnic's workshop throws sparks, an agricultural college has its tractor. */
var UNICOL = [[/เชียงใหม่|chiang ?mai univ|cmu/i, '#6a3a9a'], [/แม่ฟ้าหลวง|mae ?fah ?luang|mfu/i, '#a8232a'], [/แม่โจ้|maejo/i, '#2f7a3a'], [/พายัพ|payap/i, '#2a3a8a'], [/ราชภัฏเชียงใหม่|cmru/i, '#2a5aa8'], [/ราชภัฏเชียงราย|crru/i, '#2a7ac0'], [/ราชมงคล|rmutl/i, '#c0682a'], [/ฟาร์อีสเทอร์น|far ?eastern/i, '#c0392b']];
function university(S) {
  var hh = S.hh, c = S.c, L = plan(S, 'university'), P = L.P, r = L.r, t = S.t, w = words(P) + ' ' + (P.inside || '');
  var col = '#2a5aa8'; UNICOL.forEach(function (u) { if (u[0].test(w)) col = u[1]; });
  var poly2 = /สารพัดช่าง|เทคนิค|polytech|technic|อาชีวะ|ช่าง/i.test(w), agri = /เกษตร|agri|farm/i.test(w), cmu = /เชียงใหม่|cmu/i.test(w) && /มหาวิทยาลัยเชียงใหม่|chiang ?mai univ|cmu/i.test(w);
  var bk = poly2 ? 'shop' : pick(r, ['lanna', 'brick', 'glass', 'lanna']), grad = !S.night && r() < 0.35;
  var bw = Math.min(S.span * 0.5, hh * (4 + r())), left = (S.seed >>> 3) % 2 === 0, bx0 = left ? S.x0 + hh * 0.9 : S.x1 - hh * 1.0 - bw, bx1 = bx0 + bw;
  var key = 'university|' + bk + (grad ? 'g' : '');
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {};
    street(q, S, 'street', r); K.setting(S);
    var b;
    if (bk === 'glass') b = facade(q, S, { kind: 'glass', x0: bx0, x1: bx1, wall: '#e8ecef', trim: col, roof: col, floors: 3, lit: S.night });
    else if (bk === 'brick') { b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: '#b8603a', trim: '#f4ecd8', roof: '#5a3a2a', floors: 3, lit: S.night, doorAt: 3 }); }
    else if (bk === 'shop') { b = facade(q, S, { kind: 'row', x0: bx0, x1: bx1, wall: '#e8e0d0', trim: col, roof: '#8a9098', lit: S.night }); fr(q, b.door.x0, b.door.y0, b.door.x1 - b.door.x0, S.deck - b.door.y0, nt(S, '#3a3a44')); o.shop = b.door; }
    else { b = facade(q, S, { kind: 'gov', x0: bx0, x1: bx1, wall: '#f4ecd8', trim: col, roof: '#7a3a2a', floors: 2, lit: S.night, gable: true, doorAt: 3 }); var gx = (bx0 + bx1) / 2, gt = b.top + hh * 0.2;
      q.save(); q.strokeStyle = nt(S, '#e8b84a'); q.lineWidth = 2.4; q.lineCap = 'round'; q.beginPath(); q.moveTo(gx, gt); q.quadraticCurveTo(gx - hh * 0.05, gt - hh * 0.2, gx - hh * 0.2, gt - hh * 0.28); q.moveTo(gx, gt); q.quadraticCurveTo(gx + hh * 0.05, gt - hh * 0.2, gx + hh * 0.2, gt - hh * 0.28); q.stroke(); q.restore(); }
    fr(q, bx0, S.deck - hh * 0.1, bw, hh * 0.04, nt(S, col)); o.top = b.top - hh * 0.3;
    /* the road's rain trees */
    for (var i = 0; i < 3; i++) { var tx = left ? bx1 + hh * (0.7 + i * 1.3) : bx0 - hh * (0.7 + i * 1.3); if (tx < S.x0 + hh * 0.3 || tx > S.x1 - hh * 0.3) continue; rainTree(q, S, tx, S.deck + hh * 0.04, hh * (0.9 + 0.1 * (i % 2)), i + S.seed); }
    if (agri) { paper(q, rect(S.x0, S.deck - hh * 0.2, S.span, hh * 0.16), nt(S, '#88b05a'), 0.6); }
    /* the name on a long low wall, the university's colour along its top */
    var sx = left ? Math.min(S.x1 - hh * 2, bx1 + hh * 1.8) : Math.max(S.x0 + hh * 2, bx0 - hh * 1.8);
    paper(q, rect(sx - hh * 1.2, S.deck - hh * 0.38, hh * 2.4, hh * 0.38), nt(S, '#d8d0c0'), 1.2); fr(q, sx - hh * 1.2, S.deck - hh * 0.42, hh * 2.4, hh * 0.05, nt(S, col));
    o.sign = signAt(q, S, sx, S.deck - hh * 1.05, P, hh * 0.78, nt(S, col), S.night || null);
    if (grad) { for (var bl = 0; bl < 5; bl++) { var bx = sx + hh * 0.9 + (bl % 3) * hh * 0.08; ln(q, [[sx + hh * 0.9, S.deck - hh * 0.42], [bx, S.deck - hh * (0.9 + bl * 0.07)]], '#5a5a62', 0.8); dot(q, bx, S.deck - hh * (0.95 + bl * 0.07), hh * 0.06, ['#e5567f', '#f2c94c', '#4d8fd1', '#7fe0a4', col][bl]); } }
    roadPlate(q, S, left ? S.x1 - hh * 0.3 : S.x0 + hh * 0.3, P.road);
    if (r() < 0.45) o.incense = spiritHouse(q, S, left ? bx0 - hh * 0.4 : bx1 + hh * 0.4, hh * 0.85, (S.seed >>> 2) % 3);
    o.sx = sx; return o;
  }).out || {};
  L.incense = still.incense;
  var crew = crowd(S, 8, { casual: 1 });
  function student(d, i) { d.garb = 'casual'; d.col = '#f8f8f4'; d.long = false; var girl = (i + S.seed) % 2; d.low = girl ? d.skin : '#1a1a22'; d.sk = girl ? '#1a1a22' : null; d.hair = girl ? 3 : 0; return d; }
  if (still.shop) { var sp = still.shop, wd = dressUp(crew[0], '#2a4a7a', '#2a4a7a'); wd.dir = 1; var mw = person(c, sp.x0 + (sp.x1 - sp.x0) * 0.4, S.deck, hh * 0.9, { lean: 0.4, legs: [0.1, 0, -0.1, 0], arms: [1.3, 0.5, 1.1, 0.6] }, wd);
    fr(c, mw.head[0] - hh * 0.02, mw.head[1] - hh * 0.08, hh * 0.12, hh * 0.12, '#2a2a30'); var sx2 = mw.hand[0][0] + hh * 0.08, sy2 = mw.hand[0][1] + hh * 0.05; fr(c, sx2 - hh * 0.2, sy2, hh * 0.5, hh * 0.04, '#8a8a92');
    for (var k = 0; k < 8; k++) { var u = (t / 500 + k / 8) % 1, a = -Math.PI / 2 + (k - 3.5) * 0.35; dot(c, sx2 + Math.cos(a) * u * hh * 0.4, sy2 + Math.sin(a) * u * hh * 0.35 + u * u * hh * 0.3, 1.3, 'rgba(255,' + (200 + Math.round(55 * (1 - u))) + ',80,' + (1 - u).toFixed(2) + ')'); }
    glow(c, sx2, sy2, hh * 0.25, '255,220,120', 0.5 + 0.3 * Math.sin(t / 50)); }
  /* students walking and cycling */
  for (var i = 0; i < 3; i++) { var v = [0.3, -0.26, 0.6][i], x = stroll(S, i, v, i * 0.33 + (S.seed % 30) / 30), d = student(crew[i + 1], i); d.dir = v > 0 ? 1 : -1;
    if (i === 2) { bicycle(c, S, x, S.deck + hh * 0.42, hh * 0.62, d.dir, col); person(c, x - d.dir * hh * 0.02, S.deck + hh * 0.18, hh * 0.85, { lean: 0.15, seat: 0.4, legs: [1.0 + Math.sin(t / 200) * 0.5, -1.2, 1.0 - Math.sin(t / 200) * 0.5, -1.2], arms: [1.2, 0.3, 1.1, 0.3] }, d); }
    else { var me = person(c, x, S.deck + hh * (0.2 + i * 0.1), hh * 0.9, K.walkP(t / 1000 * TAU * 0.85 + i, false), d); if (d.sk) skirt(c, me, hh * 0.9, d.sk, 0.5); fr(c, me.hand[0][0] - hh * 0.04, me.hand[0][1] - hh * 0.04, hh * 0.1, hh * 0.13, nt(S, CLOTH2[(i + S.seed) % 8])); } }
  if (cmu && !S.night) { var tv = 0.7, tx2 = stroll(S, 5, (S.seed % 2 ? tv : -tv), 0.5); songthaew(c, S, tx2, S.H - Math.max(4, (S.H - S.deck) * 0.12), hh * 0.72, S.seed % 2 ? 1 : -1, '#7a3aaa'); }
  if (grad) { var gd = student(crew[5], 0), gx2 = still.sx + hh * 0.5; gd.dir = -1; gd.col = '#1a1a22'; gd.low = '#1a1a22'; gd.sk = null; var mg = person(c, gx2, S.deck + hh * 0.2, hh * 0.92, { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [1.6, 1.2, 0.3, 0.3] }, gd);
    fp(c, [[mg.sh[0] - hh * 0.06, mg.sh[1]], [mg.sh[0] + hh * 0.06, mg.sh[1]], [mg.hip[0] + hh * 0.05, mg.hip[1] + hh * 0.3], [mg.hip[0] - hh * 0.05, mg.hip[1] + hh * 0.3]], col);
    for (var gl = 0; gl < 7; gl++) dot(c, mg.sh[0] - hh * 0.06 + gl * hh * 0.02, mg.sh[1] + hh * 0.03 + Math.sin(gl / 6 * Math.PI) * hh * 0.08, hh * 0.022, gl % 2 ? '#f8f8f4' : '#e5567f');
    var ph = crew[6]; ph.dir = 1; var mp = person(c, gx2 - hh * 1.1, S.deck + hh * 0.26, hh * 0.9, { lean: 0.2, seat: 0.36, legs: [1.3, -1.6, 0.4, -0.4], arms: [1.6, 1.4, 1.5, 1.5] }, ph); fr(c, mp.head[0] + hh * 0.06, mp.head[1] - hh * 0.04, hh * 0.1, hh * 0.07, '#2a2a30');
    if (Math.sin(t / 900) > 0.97) glow(c, mp.head[0] + hh * 0.12, mp.head[1], hh * 0.4, '255,255,255', 0.9); }
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: bx0, x1: bx1, y0: still.top || S.deck - hh * 2, y1: S.deck });
}

/* ---------------------------------------------------------------- strong figures
   jointsOf: the skeleton as doodler.js works it. brawn: a side-on lifter cut thick (thighs and
   upper arms twice the plain figure's, a V torso, a singlet). poser: a front-on competitor
   whose arms take the stage poses (front double biceps, lat spread, side chest, most muscular)
   with a tan and a sheen. */
function jointsOf(x, y, h, P, dir) {
  var seat = P.seat || 0.47, lean = P.lean || 0, L = P.legs, A = P.arms;
  function pt(o, a, l) { return [o[0] + dir * Math.sin(a) * l, o[1] + Math.cos(a) * l]; }
  var hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33];
  var k1 = pt(hip, L[0], h * 0.24), k2 = pt(hip, L[2], h * 0.24), e1 = pt(sh, A[0], h * 0.17), e2 = pt(sh, A[2], h * 0.17);
  return { hip: hip, sh: sh, head: [sh[0] + dir * Math.sin(lean) * h * 0.15, sh[1] - Math.cos(lean) * h * 0.15], k1: k1, f1: pt(k1, L[0] + L[1], h * 0.23), k2: k2, f2: pt(k2, L[2] + L[3], h * 0.23),
    e1: e1, w1: pt(e1, A[0] + A[1], h * 0.16), e2: e2, w2: pt(e2, A[2] + A[3], h * 0.16), lean: lean };
}
function seg(c, a, b, w, col) { c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); }
function bulge(c, a, b, u, rx, ry, col) { var x = lerp(a[0], b[0], u), y = lerp(a[1], b[1], u), an = Math.atan2(b[1] - a[1], b[0] - a[0]); el(c, x, y, rx, ry, an, col); }
function brawn(c, x, y, h, P, d) {
  var dir = d.dir || 1, J = jointsOf(x, y, h, P, dir), sk = d.skin, low = d.low || '#2a2a30', top = d.col, w = Math.max(2, h * 0.075);
  c.save(); c.shadowColor = 'rgba(0,0,0,.38)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2;
  [[J.k2, J.f2], [J.k1, J.f1]].forEach(function (L, i) { seg(c, J.hip, L[0], w * 1.9, i ? low : shade(low, 0.85)); seg(c, L[0], L[1], w * 1.35, sk); bulge(c, L[0], L[1], 0.35, w * 0.9, w * 0.7, sk); el(c, L[1][0] + dir * h * 0.03, L[1][1], h * 0.055, h * 0.024, 0, '#1a1a22'); });
  var ux = Math.cos(J.lean) * dir, uy = Math.sin(J.lean) * dir, ws = h * 0.12, wh = h * 0.075;
  fp(c, [[J.sh[0] - ux * ws, J.sh[1] - uy * ws], [J.sh[0] + ux * ws, J.sh[1] + uy * ws], [J.hip[0] + ux * wh, J.hip[1] + uy * wh], [J.hip[0] - ux * wh, J.hip[1] - uy * wh]], top || sk);
  c.shadowColor = 'transparent';
  if (top) fp(c, [[J.sh[0] - ux * ws * 0.3, J.sh[1] - uy * ws * 0.3], [J.sh[0] + ux * ws * 0.9, J.sh[1] + uy * ws * 0.9], [J.sh[0] + ux * ws * 0.5 + uy * h * 0.08, J.sh[1] + h * 0.06]], sk);
  else { c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; c.beginPath(); c.moveTo(J.sh[0] + ux * ws * 0.2, J.sh[1] + h * 0.07); c.quadraticCurveTo(J.sh[0] + ux * ws * 0.9, J.sh[1] + h * 0.1, J.sh[0] + ux * ws * 0.9, J.sh[1] + h * 0.04); c.stroke(); }
  c.shadowColor = 'rgba(0,0,0,.38)';
  [[J.e2, J.w2], [J.e1, J.w1]].forEach(function (A) { seg(c, J.sh, A[0], w * 1.55, sk); bulge(c, J.sh, A[0], 0.55, w * 1.0, w * 0.8, sk); seg(c, A[0], A[1], w * 1.15, sk); });
  dot(c, J.sh[0], J.sh[1], w * 1.1, sk);
  c.shadowColor = 'transparent';
  dot(c, J.head[0], J.head[1], h * 0.095, sk); c.fillStyle = d.hairCol || '#1c1410'; c.beginPath(); c.arc(J.head[0] - dir * h * 0.01, J.head[1] - h * 0.02, h * 0.097, Math.PI * 0.95, Math.PI * 2.05); c.fill();
  if (d.band) fr(c, J.head[0] - h * 0.09, J.head[1] - h * 0.05, h * 0.18, h * 0.025, d.band);
  dot(c, J.head[0] + dir * h * 0.045, J.head[1] - h * 0.005, Math.max(0.8, h * 0.011), '#2a1a12');
  c.restore();
  return { hip: J.hip, sh: J.sh, head: J.head, hand: [J.w1, J.w2], foot: [J.f1, J.f2], elbow: [J.e1, J.e2] };
}
var POSES = ['fdb', 'lat', 'side', 'most'];
function poser(c, x, y, h, pose, d, sheen) {
  var sk = d.skin, low = d.low, shY = y - h * 0.8, hipY = y - h * 0.47, hw = h * 0.08, sw = pose === 'lat' ? h * 0.2 : h * 0.16, woman = d.woman;
  c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2;
  [-1, 1].forEach(function (s) { fp(c, [[x + s * h * 0.02, hipY], [x + s * hw * 1.4, hipY], [x + s * h * 0.075, y - h * 0.24], [x + s * h * 0.055, y - h * 0.02], [x + s * h * 0.025, y - h * 0.02], [x + s * h * 0.03, y - h * 0.24]], sk); el(c, x + s * h * 0.045, y, h * 0.05, h * 0.02, 0, '#1a1a22'); });
  fp(c, [[x - sw, shY], [x + sw, shY], [x + (pose === 'lat' ? h * 0.15 : h * 0.12), shY + h * 0.14], [x + hw, hipY], [x - hw, hipY], [x - (pose === 'lat' ? h * 0.15 : h * 0.12), shY + h * 0.14]], sk);
  c.shadowColor = 'transparent';
  fp(c, [[x - hw * 1.05, hipY - h * 0.03], [x + hw * 1.05, hipY - h * 0.03], [x + hw * 0.8, hipY + h * 0.06], [x, hipY + h * 0.09], [x - hw * 0.8, hipY + h * 0.06]], low);
  if (woman) { el(c, x - h * 0.045, shY + h * 0.08, h * 0.04, h * 0.03, 0, low); el(c, x + h * 0.045, shY + h * 0.08, h * 0.04, h * 0.03, 0, low); }
  else { c.strokeStyle = 'rgba(0,0,0,.2)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - h * 0.1, shY + h * 0.1); c.quadraticCurveTo(x, shY + h * 0.13, x + h * 0.1, shY + h * 0.1); for (var a = 0; a < 3; a++) { c.moveTo(x - h * 0.035, shY + h * (0.17 + a * 0.05)); c.lineTo(x + h * 0.035, shY + h * (0.17 + a * 0.05)); } c.moveTo(x, shY + h * 0.14); c.lineTo(x, hipY - h * 0.04); c.stroke(); }
  c.shadowColor = 'rgba(0,0,0,.4)';
  var w = Math.max(2, h * 0.075);
  [-1, 1].forEach(function (s) {
    var S0 = [x + s * sw * 0.92, shY + h * 0.02], E, W;
    if (pose === 'fdb') { E = [x + s * h * 0.34, shY + h * 0.0]; W = [x + s * h * 0.36, shY - h * 0.17]; }
    else if (pose === 'lat') { E = [x + s * h * 0.3, shY + h * 0.12]; W = [x + s * h * 0.1, hipY - h * 0.03]; }
    else if (pose === 'most') { E = [x + s * h * 0.22, shY + h * 0.17]; W = [x + s * h * 0.03, hipY - h * 0.06]; }
    else { E = s < 0 ? [x - h * 0.16, shY + h * 0.17] : [x + h * 0.2, shY + h * 0.16]; W = s < 0 ? [x + h * 0.06, shY + h * 0.22] : [x + h * 0.04, shY + h * 0.23]; }
    seg(c, S0, E, w * 1.6, sk); bulge(c, S0, E, 0.58, w * (pose === 'fdb' ? 1.25 : 1.0), w * (pose === 'fdb' ? 0.95 : 0.75), sk); seg(c, E, W, w * 1.2, sk); dot(c, W[0], W[1], w * 0.7, sk); dot(c, S0[0], S0[1], w * 1.2, sk);
  });
  c.shadowColor = 'transparent';
  fp(c, [[x - h * 0.05, shY - h * 0.01], [x + h * 0.05, shY - h * 0.01], [x + h * 0.035, shY - h * 0.06], [x - h * 0.035, shY - h * 0.06]], sk);
  dot(c, x, shY - h * 0.11, h * 0.075, sk); c.fillStyle = d.hairCol || '#1c1410'; c.beginPath(); c.arc(x, shY - h * 0.125, h * 0.077, Math.PI, TAU); c.fill();
  if (woman) { el(c, x - h * 0.06, shY - h * 0.08, h * 0.03, h * 0.08, 0.2, d.hairCol || '#1c1410'); el(c, x + h * 0.06, shY - h * 0.08, h * 0.03, h * 0.08, -0.2, d.hairCol || '#1c1410'); }
  dot(c, x - h * 0.025, shY - h * 0.11, 1, '#2a1a12'); dot(c, x + h * 0.025, shY - h * 0.11, 1, '#2a1a12');
  if (sheen) { c.strokeStyle = 'rgba(255,240,210,' + (0.35 + 0.25 * sheen).toFixed(2) + ')'; c.lineWidth = 1.2; c.beginPath(); c.arc(x - h * 0.08, shY + h * 0.06, h * 0.05, -2.6, -1.6); c.arc(x + h * 0.08, shY + h * 0.06, h * 0.05, -1.5, -0.5); c.moveTo(x - h * 0.07, y - h * 0.38); c.lineTo(x - h * 0.06, y - h * 0.28); c.moveTo(x + h * 0.07, y - h * 0.38); c.lineTo(x + h * 0.06, y - h * 0.28); c.stroke(); }
  c.restore();
}
var TAN = ['#8a4a2a', '#9a5a32', '#7a3e22', '#a8643a'];
function lifters(S, n, tan) { return crowd(S, n, { casual: 1 }).map(function (d, i) { if (tan) d.skin = TAN[(i + S.seed) % TAN.length]; d.col = i % 3 ? CLOTH2[(i * 3 + S.seed) % 8] : null; d.low = ['#2a2a30', '#2a3a6a', '#3a3a44', '#5a2a2a'][i % 4]; d.band = i % 4 === 1 ? '#d9342b' : null; d.woman = (i + S.seed) % 3 === 1; return d; }); }
/* a barbell seen end-on (plates as discs) or along (plates as slabs), and a dumbbell */
function plates(c, x, y, r, n, cols) { for (var i = n - 1; i >= 0; i--) dot(c, x + i * 1.2, y, r * (1 - i * 0.12), cols[i % cols.length]); dot(c, x, y, r * 0.18, '#c8ccd2'); }
function dumbbell(c, x, y, s, col) { fr(c, x - s * 0.3, y - s * 0.03, s * 0.6, s * 0.06, '#8a8a92'); fr(c, x - s * 0.36, y - s * 0.1, s * 0.12, s * 0.2, col); fr(c, x + s * 0.24, y - s * 0.1, s * 0.12, s * 0.2, col); }

/* ---------------------------------------------------------------- weights
   Five looks, the words pushing which, the seed dealing the rest:
   'iron'   an iron gym: the squat, the bar path a vertical line, knee and hip on ease curves;
            plates on the bar, chalk off the hands, a spotter, the mirror wall's reflection, the
            dumbbell rack, a fan turning (θ = ωt), a tung and a spirit house
   'park'   the free weights corner of a Thai park: concrete-and-pipe barbells, welded benches
            under the rain tree, an uncle's curls, kids swinging off the pull-up bar (θ = θ₀·cos ωt),
            the dog asleep on the warm slab
   'stage'  a bodybuilding contest: posers turning through front double biceps, lat spread, side
            chest and most muscular, the sheen, the judges' cards, the crowd, the trophies, lights
   'meet'   a powerlifting meet: the deadlift to lockout, three white lights coming on, the
            loaders, the bar bending under the load (a sag, y = a·x² across the grip)
   'kb'     a morning class of kettlebells swung as pendulums, the coach counting ๑ to ๑๐ */
var WEIGHTS_WORDS = /body ?build|bodybuilding|weight ?lift|weightlifting|power ?lift|powerlifting|strongman|crossfit|deadlift|เพาะกาย|ยกน้ำหนัก|เพาะเหล็ก/i;
function weightsLook(S) {
  var P = S.place, t = (P ? words(P) : '') + ' ' + (S.title || '') + ' ' + (S.label || '');
  if (/contest|ประกวด|physique|bikini|olympia|championship|ชิงแชมป์|mr\.? ?thai|ms\.? ?thai|bodybuild|เพาะกาย/i.test(t) && !P) return 'stage';
  if (/power ?lift|deadlift|strongman|ยกน้ำหนัก|weight ?lift|\bmeet\b|open\b/i.test(t) && !P) return 'meet';
  if (/kettlebell|crossfit|ครอสฟิต|bootcamp|boot ?camp|hiit|functional/i.test(t)) return 'kb';
  if (/street ?workout|calisthen|outdoor|park|สวน|ลานกีฬา|สนามกีฬา|public/i.test(t)) return 'park';
  var deal = P ? ['iron', 'iron', 'park', 'kb', 'iron'] : ['iron', 'park', 'stage', 'meet', 'kb'];
  return deal[(S.seed >>> 5) % deal.length];
}
/* the iron room, drawn into any room R (a shopfront's or a sala's) */
function ironRoom(q, S, R) {
  var hh = S.hh, w = R.x1 - R.x0, o = {};
  for (var m = 0; m < 4; m++) fr(q, R.x0 + w * (0.02 + m * 0.245), R.y0 + hh * 0.05, w * 0.235, R.y1 - R.y0 - hh * 0.22, nt(S, '#cfe4ee'));
  fr(q, R.x0, R.y1 - hh * 0.14, w, hh * 0.14, nt(S, '#2a2a30')); for (var x = R.x0; x < R.x1; x += hh * 0.25) fr(q, x, R.y1 - hh * 0.14, 1, hh * 0.14, 'rgba(255,255,255,.08)');
  /* the tung on the wall and a khom */
  var tx = R.x0 + w * 0.06; for (var i = 0; i < 6; i++) fr(q, tx, R.y0 + hh * (0.1 + i * 0.07), hh * 0.08, hh * 0.07, ['#d9342b', '#f2c94c', '#f2e6c9', '#2f8f5b'][i % 4]); fp(q, [[tx, R.y0 + hh * 0.52], [tx + hh * 0.04, R.y0 + hh * 0.58], [tx + hh * 0.08, R.y0 + hh * 0.52]], '#d9342b');
  /* the rack */
  var rx = R.x0 + w * 0.42; o.rack = rx; [rx - hh * 0.32, rx + hh * 0.32].forEach(function (px) { fr(q, px - 2.5, R.y1 - hh * 0.95, 5, hh * 0.95, nt(S, '#3a3a44')); for (var k = 0; k < 6; k++) dot(q, px, R.y1 - hh * (0.2 + k * 0.12), 1.2, '#c8ccd2'); });
  fr(q, rx - hh * 0.36, R.y1 - hh * 0.97, hh * 0.72, 4, nt(S, '#3a3a44'));
  /* the dumbbell rack */
  var dx = R.x1 - w * 0.2; fr(q, dx - hh * 0.3, R.y1 - hh * 0.32, hh * 0.6, 3, nt(S, '#5a5a62')); fr(q, dx - hh * 0.3, R.y1 - hh * 0.18, hh * 0.6, 3, nt(S, '#5a5a62')); fr(q, dx - hh * 0.28, R.y1 - hh * 0.32, 3, hh * 0.32, nt(S, '#5a5a62')); fr(q, dx + hh * 0.26, R.y1 - hh * 0.32, 3, hh * 0.32, nt(S, '#5a5a62'));
  for (var k = 0; k < 4; k++) { dumbbell(q, dx - hh * 0.2 + k * hh * 0.14, R.y1 - hh * 0.35, hh * 0.18, nt(S, '#2a2a30')); dumbbell(q, dx - hh * 0.2 + k * hh * 0.14, R.y1 - hh * 0.21, hh * 0.2, nt(S, '#2a2a30')); }
  o.fan = [R.x1 - w * 0.08, R.y0 + hh * 0.22];
  return o;
}
function ironWork(c, S, R, o) {
  var hh = S.hh, t = S.t, crew = lifters(S, 3, false), h = hh * 0.9;
  /* the squat: one rep every 3.2 s, depth on ease; the shoulder stays over the bar's line */
  var ph = (t / 1000 / 3.2) % 1, u = ph < 0.45 ? ease(ph / 0.45) : ph < 0.55 ? 1 : 1 - ease((ph - 0.55) / 0.45), d = crew[0]; d.dir = 1; d.col = '#2a2a30';
  var P = { lean: 0.15 + 0.45 * u, seat: 0.47 - 0.2 * u, legs: [0.05 + 1.25 * u, -0.05 - 1.75 * u, 0.0 + 1.2 * u, -1.7 * u], arms: [2.6, 0.6, 2.5, 0.7] };
  var bx = o.rack || (R.x0 + R.x1) / 2, J = jointsOf(0, R.y1, h, P, 1), x = bx - J.sh[0];
  /* the reflection in the mirror, faint and turned */
  c.save(); c.globalAlpha = 0.22; brawn(c, x + hh * 0.9, R.y1 - hh * 0.12, h * 0.9, P, { dir: -1, skin: d.skin, low: d.low, col: d.col, hairCol: d.hairCol }); c.restore();
  var me = brawn(c, x, R.y1, h, P, d), sy = me.sh[1] - h * 0.02;
  fr(c, bx - 2, sy - 2, 4, 4, '#c8ccd2'); plates(c, bx, sy, hh * 0.15, 3, ['#2a2a30', '#c0392b', '#2a5aa8']);
  /* the spotter behind, hands under the elbows */
  var sp = crew[1]; sp.dir = 1; sp.col = '#c0392b'; var sx = bx - hh * 0.42; brawn(c, sx, R.y1, h * 0.96, reach(sx, R.y1, h * 0.96, { lean: 0.2 + 0.3 * u, seat: 0.47 - 0.12 * u, legs: [0.3 * u, -0.5 * u, 0.2 * u, -0.4 * u], arms: [1, 0.5, 1, 0.5] }, 1, [me.elbow[0][0] - 2, me.elbow[0][1] + 4], [me.elbow[1][0] - 4, me.elbow[1][1] + 6]), sp);
  /* chalk off the hands at the top of each rep */
  if (ph > 0.9 || ph < 0.1) { var cu = ph > 0.9 ? (ph - 0.9) * 5 : 0.5 + ph * 5; for (var k = 0; k < 6; k++) dot(c, me.hand[0][0] + Math.cos(k) * cu * hh * 0.12, me.hand[0][1] - cu * hh * 0.15 + Math.sin(k * 2) * cu * hh * 0.05, hh * 0.03 * (1 + cu), 'rgba(255,255,255,' + (0.6 * (1 - cu)).toFixed(2) + ')'); }
  /* a curl at the dumbbell rack */
  var cd = crew[2]; cd.dir = -1; cd.col = null; var cx = R.x1 - (R.x1 - R.x0) * 0.2 + hh * 0.05, cu2 = 0.5 - 0.5 * Math.cos(t / 1000 * TAU / 1.8);
  if (cx - R.x0 > hh * 1.6) { var mc = brawn(c, cx, R.y1, h * 0.95, { lean: 0.05, legs: [0.08, 0, -0.08, 0], arms: [0.15, 0.2 + cu2 * 2.1, -0.1, 0.1] }, cd); dumbbell(c, mc.hand[0][0], mc.hand[0][1], hh * 0.2, '#2a2a30'); }
  if (o.fan) { var a = t / 90; dot(c, o.fan[0], o.fan[1], hh * 0.13, 'rgba(200,210,220,.35)'); for (var b = 0; b < 3; b++) el(c, o.fan[0] + Math.cos(a + b * 2.09) * hh * 0.07, o.fan[1] + Math.sin(a + b * 2.09) * hh * 0.07, hh * 0.07, hh * 0.03, a + b * 2.09, '#e8e8e8'); dot(c, o.fan[0], o.fan[1], hh * 0.025, '#5a5a62'); ln(c, [o.fan, [o.fan[0], o.fan[1] - hh * 0.18]], '#5a5a62', 2); }
}
/* kettlebells: the swing a pendulum from the hips, θ = θ₀·sin ωt; the coach counts in Thai digits */
function kbWork(c, S, x0, x1, y, n, h) {
  var t = S.t, crew = lifters(S, n + 1, false), w = 1.4;
  for (var i = 0; i < n; i++) { var x = lerp(x0, x1, n > 1 ? i / (n - 1) : 0.5), s = Math.sin(t / 1000 * TAU / w + i * 0.15), up = (s + 1) / 2, d = crew[i]; d.dir = 1;
    var P = { lean: 0.9 - 0.85 * up, seat: 0.42 + 0.04 * up, legs: [0.4 - 0.35 * up, -0.6 + 0.55 * up, 0.35 - 0.3 * up, -0.55 + 0.5 * up], arms: [-0.5 + 2.1 * up + 0.9 * (1 - up) * 0, 0.05, -0.45 + 2.1 * up, 0.05] };
    var me = brawn(c, x, y, h, P, d), hd = [(me.hand[0][0] + me.hand[1][0]) / 2, (me.hand[0][1] + me.hand[1][1]) / 2];
    dot(c, hd[0], hd[1] + h * 0.07, h * 0.075, '#2a2a30'); c.strokeStyle = '#2a2a30'; c.lineWidth = 2; c.beginPath(); c.arc(hd[0], hd[1] + h * 0.01, h * 0.04, Math.PI, TAU); c.stroke(); }
  var co = crew[n]; co.dir = -1; co.col = '#f2c94c'; var cx = x1 + h * 0.75, mc = brawn(c, cx, y, h, { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [1.2, 1.4, 0.2, 0.2] }, co);
  var n10 = Math.floor(t / 1000 / w) % 10, dig = '๑๒๓๔๕๖๗๘๙'.charAt(n10) || '๑๐'; if (n10 === 9) dig = '๑๐';
  var bxx = mc.head[0] - h * 0.2, byy = mc.head[1] - h * 0.3; el(c, bxx, byy, h * 0.14, h * 0.1, 0, 'rgba(255,255,255,.92)'); fp(c, [[bxx + h * 0.04, byy + h * 0.08], [bxx + h * 0.12, byy + h * 0.16], [bxx + h * 0.1, byy + h * 0.06]], 'rgba(255,255,255,.92)'); txt(c, dig, bxx, byy + 1, h * 0.13, '#c0392b', 800);
}
/* the park's free weights: concrete in paint cans on a pipe, a welded bench, the pull-up bar */
function parkGym(q, S, x0, x1) {
  var hh = S.hh, o = {}, y = S.deck;
  paper(q, rect(x0, y - hh * 0.02, x1 - x0, hh * 0.1), nt(S, '#bdb5a5'), 0.8);
  var bx = x0 + (x1 - x0) * 0.62; o.bar = bx; [bx - hh * 0.5, bx + hh * 0.5].forEach(function (px) { fr(q, px - 2.5, y - hh * 1.25, 5, hh * 1.25, nt(S, '#3a6a8a')); }); fr(q, bx - hh * 0.52, y - hh * 1.27, hh * 1.04, 5, nt(S, '#3a6a8a'));
  var be = x0 + (x1 - x0) * 0.22; fr(q, be - hh * 0.35, y - hh * 0.3, hh * 0.7, hh * 0.06, nt(S, '#a84a2a')); ln(q, [[be - hh * 0.3, y], [be - hh * 0.3, y - hh * 0.3]], nt(S, '#a84a2a'), 3); ln(q, [[be + hh * 0.3, y], [be + hh * 0.3, y - hh * 0.3]], nt(S, '#a84a2a'), 3);
  ln(q, [[be - hh * 0.3, y - hh * 0.3], [be - hh * 0.3, y - hh * 0.75]], nt(S, '#a84a2a'), 3); fr(q, be - hh * 0.38, y - hh * 0.77, hh * 0.16, 4, nt(S, '#a84a2a'));
  for (var k = 0; k < 3; k++) { var cx = x0 + (x1 - x0) * (0.38 + k * 0.08); fr(q, cx - hh * 0.25, y - hh * 0.03, hh * 0.5, 3, nt(S, '#8a8a92')); [-1, 1].forEach(function (s) { fr(q, cx + s * hh * 0.25 - hh * 0.06, y - hh * 0.12, hh * 0.12, hh * 0.13, nt(S, '#b8b4aa')); fr(q, cx + s * hh * 0.25 - hh * 0.06, y - hh * 0.12, hh * 0.12, hh * 0.025, nt(S, ['#c0392b', '#2a5aa8', '#e8b84a'][k])); }); }
  o.bench = be; return o;
}
function parkWork(c, S, o, h) {
  var t = S.t, hh = S.hh, crew = lifters(S, 4, false), y = S.deck;
  var un = crew[0]; un.dir = 1; un.col = null; un.hairCol = '#bdbdbd'; var cu = 0.5 - 0.5 * Math.cos(t / 1000 * TAU / 2.2);
  var mu = brawn(c, o.bench + hh * 0.05, y - hh * 0.3 + h * 0.3 * 0.47 - h * 0.14, h, { lean: 0.05, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.25, 0.2 + cu * 2.0, 0.2, 0.2 + cu * 2.0] }, un);
  var hx = (mu.hand[0][0] + mu.hand[1][0]) / 2, hy = (mu.hand[0][1] + mu.hand[1][1]) / 2; fr(c, hx - hh * 0.3, hy - 1.5, hh * 0.6, 3, '#8a8a92'); [-1, 1].forEach(function (s) { fr(c, hx + s * hh * 0.3 - hh * 0.06, hy - hh * 0.07, hh * 0.12, hh * 0.13, '#b8b4aa'); });
  /* kids on the bar, pendulums from their hands */
  for (var k = 0; k < 2; k++) { var px = o.bar + (k ? hh * 0.22 : -hh * 0.22), th = 0.35 * Math.cos(t / 1000 * TAU / 1.6 + k * 1.3), kd = crew[1 + k], kh = hh * 0.62; kd.dir = 1; kd.col = CLOTH2[(k + S.seed) % 8];
    c.save(); c.translate(px, y - hh * 1.25); c.rotate(-th); person(c, 0, kh * 1.0, kh, { lean: 0, legs: [0.2 + th, -0.3, -0.1 + th, -0.2], arms: [3.14, 0, 3.14, 0] }, kd); c.restore(); }
}
function weights(S) {
  var look = weightsLook(S), hh = S.hh, c = S.c, t = S.t;
  if (S.place && (look === 'iron' || look === 'kb')) return shopScene(S, 'weights-' + look, {
    kinds: ['shop', 'glass', 'row', 'shop'], back: '#e8eef2', floor: '#2a2a30', icon: ICON.dumbbell, keyOf: function () { return look; },
    room: function (q, S, R) { return look === 'iron' ? ironRoom(q, S, R) : (fr(q, R.x0, R.y1 - hh * 0.12, R.x1 - R.x0, hh * 0.12, '#2a2a30'), {}); },
    work: function (c, S, R, L, o) { if (look === 'iron') ironWork(c, S, R, o); else kbWork(c, S, R.x0 + hh * 0.45, R.x1 - hh * 1.2, R.y1, Math.max(2, Math.min(4, Math.floor((R.x1 - R.x0 - hh * 1.4) / (hh * 0.6)))), hh * 0.82); }
  });
  var L = plan(S, 'weights'), r = L.r, P = L.P;
  var key = 'weights|' + look + (S.label ? '|b' : '');
  if (look === 'park') {
    var still = layer(S, key, stageBox(S), function (q) {
      var o = {}; street(q, S, 'lawn', r); K.setting(S);
      rainTree(q, S, S.x0 + S.span * 0.3, S.deck + hh * 0.02, hh * 1.05, S.seed);
      var g = parkGym(q, S, S.x0 + S.span * 0.12, S.x1 - S.span * 0.1); o.g = g;
      if (S.place) { var gx = S.x1 - hh * 1.3; fr(q, gx - 2, S.deck - hh * 1.0, 4, hh * 1.0, nt(S, '#7a4a2a')); o.sign = signAt(q, S, gx, S.deck - hh * 1.5, P, hh * 0.75, nt(S, '#2a3a5a'), null); }
      if (r() < 0.6) o.incense = spiritHouse(q, S, S.x0 + hh * 0.55, hh * 0.85, (S.seed >>> 2) % 3);
      return o;
    }).out || {};
    L.incense = still.incense; L.dog = [still.g.bench - hh * 0.7, S.deck + hh * 0.08, true];
    if (!S.night || !S.place) parkWork(c, S, still.g, hh * 0.9);
    streetLife(S, L);
    K.banner(c, S.x0 + S.span * 0.5, S.deck - hh * 2.05, S.label, hh, '#3a6a8a', S.seed, S.hits);
    S.hits.push({ k: S.place ? 'place' : 'event', x0: S.x0, x1: S.x1, y0: S.deck - hh * 1.6, y1: S.H });
    return;
  }
  if (look === 'iron' || look === 'kb') {   /* the band: an open gym under a Lanna sala */
    K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a2620' : '#8a7a62');
    var top = K.under(S, S.night ? '#3a2a40' : '#6a3a5a'), R = { x0: S.x0, x1: S.x1, y0: top + (S.deck - top) * 0.35, y1: S.deck };
    var o2 = layer(S, key, [R.x0, R.y0, R.x1 - R.x0, R.y1 - R.y0 + 2], function (q) { return look === 'iron' ? ironRoom(q, S, R) : {}; }).out || {};
    if (look === 'iron') ironWork(c, S, R, o2); else kbWork(c, S, R.x0 + hh * 0.5, R.x1 - hh * 1.2, R.y1, Math.max(2, Math.min(5, Math.floor((R.x1 - R.x0 - hh * 1.4) / (hh * 0.65)))), hh * 0.85);
    K.banner(c, (S.x0 + S.x1) / 2, top + hh * 0.55, S.label, hh, '#6a3a5a', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
    return;
  }
  var xr = S.avoid ? Math.min(S.x1 - hh * 0.3, S.avoid.cx - S.avoid.r - hh * 0.1) : S.x1 - hh * 0.3;
  if (look === 'stage') {
    var sy = S.deck - hh * 0.3, st = layer(S, key, stageBox(S), function (q) {
      var o = {}; K.ground(q, S.x0, S.x1, S.deck, S.H, S.night ? '#1a1420' : '#3a2a30');
      var cx0 = S.x0 + hh * 0.3, cx1 = xr;
      fr(q, cx0, S.deck - hh * 2.25, cx1 - cx0, hh * 1.95, '#2a1a2a');
      for (var k = 0; k < 2; k++) { var e = k ? cx1 : cx0, d = k ? -1 : 1; fp(q, [[e, S.deck - hh * 2.25], [e + d * hh * 0.7, S.deck - hh * 2.25], [e + d * hh * 0.35, sy], [e, sy]], '#8a1a2a'); for (var f = 0; f < 4; f++) ln(q, [[e + d * hh * (0.1 + f * 0.15), S.deck - hh * 2.2], [e + d * hh * (0.05 + f * 0.08), sy]], 'rgba(0,0,0,.25)', 1); }
      fr(q, cx0, S.deck - hh * 2.3, cx1 - cx0, hh * 0.12, '#e8b84a');
      paper(q, rect(cx0, sy, cx1 - cx0, hh * 0.3), '#5a3a2a', 1.4); fr(q, cx0, sy, cx1 - cx0, 3, '#e8b84a');
      /* trophies */
      var tx = cx1 - hh * 1.0; fr(q, tx - hh * 0.5, sy - hh * 0.22, hh * 1.0, hh * 0.22, '#f4f4f4'); for (var tr = 0; tr < 3; tr++) { var px = tx - hh * 0.32 + tr * hh * 0.32, th = hh * (0.3 + (tr === 1 ? 0.12 : 0)); fr(q, px - hh * 0.06, sy - hh * 0.22 - hh * 0.06, hh * 0.12, hh * 0.06, '#5a3a2a'); fr(q, px - 2, sy - hh * 0.28 - th * 0.5, 4, th * 0.5, '#e0b04a'); el(q, px, sy - hh * 0.28 - th * 0.6, hh * 0.08, hh * 0.1, 0, '#e8b84a'); el(q, px, sy - hh * 0.28 - th * 0.68, hh * 0.08, hh * 0.03, 0, '#f6d27a'); }
      /* the judges' table below the stage */
      var jx0 = S.x0 + S.span * 0.2, jx1 = jx0 + hh * 2.4; fr(q, jx0, S.deck + hh * 0.06, jx1 - jx0, hh * 0.08, '#f4f4f4'); fr(q, jx0, S.deck + hh * 0.14, jx1 - jx0, hh * 0.3, '#2a3a6a'); o.judges = [jx0, jx1];
      return o;
    }).out || {};
    /* stage lights sweeping: cones from above, the angle on sin ωt */
    for (var lgt = 0; lgt < 3; lgt++) { var lx = lerp(S.x0 + hh * 1.0, xr - hh * 1.0, (lgt + 0.5) / 3), a = Math.sin(t / 1800 + lgt * 2) * 0.35, ex = lx + Math.sin(a) * hh * 2.0; c.fillStyle = 'rgba(255,240,200,.12)'; fp(c, [[lx - 4, S.deck - hh * 2.2], [lx + 4, S.deck - hh * 2.2], [ex + hh * 0.5, sy], [ex - hh * 0.5, sy]], ['rgba(255,240,200,.14)', 'rgba(255,170,200,.12)', 'rgba(170,210,255,.12)'][lgt]); }
    var crew = lifters(S, 6, true), np = S.phone ? 3 : 4, pi = Math.floor(t / 3000) % 4;
    for (var i = 0; i < np; i++) { var px2 = lerp(S.x0 + hh * 1.0, xr - hh * 2.0, i / (np - 1)), d2 = crew[i]; d2.low = ['#c0392b', '#2a2a30', '#2a5aa8', '#e8b84a'][i]; poser(c, px2, sy, hh * 1.0, POSES[(pi + (i % 2 ? 0 : 0)) % 4], d2, 0.5 + 0.5 * Math.sin(t / 400 + i)); }
    /* the judges' cards up between poses, the crowd's arms up */
    var cards = Math.floor(t / 3000) % 2;
    if (st.judges) for (var j = 0; j < 3; j++) { var jx = lerp(st.judges[0] + hh * 0.3, st.judges[1] - hh * 0.3, j / 2); dot(c, jx, S.deck + hh * 0.02, hh * 0.09, '#2a2420'); if (cards) { fr(c, jx - hh * 0.08, S.deck - hh * 0.25, hh * 0.16, hh * 0.12, '#f8f8f4'); txt(c, String(7 + (j + S.seed) % 3), jx, S.deck - hh * 0.19, hh * 0.09, '#2a2a30', 800); } }
    for (var cr = 0; cr < 8; cr++) { var hx = S.x0 + S.span * (0.08 + cr * 0.12), hy = S.H - 2; paper(c, function (p) { p.beginPath(); p.ellipse(hx, hy, hh * 0.2, hh * 0.15, 0, Math.PI, TAU); p.moveTo(hx + hh * 0.1, hy - hh * 0.21); p.arc(hx, hy - hh * 0.21, hh * 0.1, 0, TAU); }, '#3a2c26', 0.6); if ((cr + Math.floor(t / 600)) % 3 === 0) ln(c, [[hx + hh * 0.1, hy - hh * 0.12], [hx + hh * 0.2, hy - hh * 0.5]], '#3a2c26', Math.max(2, hh * 0.06)); }
    K.banner(c, S.x0 + S.span * 0.5, S.deck - hh * 2.1, S.label, hh, '#8a1a2a', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - hh * 2.3, y1: S.H });
    return;
  }
  /* 'meet': the platform, the deadlift, the three lights */
  var my = S.deck + hh * 0.05, mt = layer(S, key, stageBox(S), function (q) {
    var o = {}; K.ground(q, S.x0, S.x1, S.deck, S.H, S.night ? '#1e1a22' : '#5a5048'); if (S.place) K.setting(S);
    fr(q, S.x0 + hh * 0.4, S.deck - hh * 2.2, xr - S.x0 - hh * 0.4, hh * 1.9, '#2a2a3a'); for (var k = 0; k < 4; k++) fr(q, S.x0 + hh * 0.4, S.deck - hh * (2.0 - k * 0.45), xr - S.x0 - hh * 0.4, 2, 'rgba(255,255,255,.06)');
    var lb = S.x0 + S.span * 0.5; fr(q, lb - hh * 0.55, S.deck - hh * 2.08, hh * 1.1, hh * 0.32, '#1a1a22'); q.strokeStyle = '#e8b84a'; q.lineWidth = 1; q.strokeRect(lb - hh * 0.55, S.deck - hh * 2.08, hh * 1.1, hh * 0.32);
    var cx = S.x0 + S.span * 0.5; paper(q, rect(cx - hh * 1.6, S.deck - hh * 0.06, hh * 3.2, hh * 0.14), '#a8784a', 1.2); fr(q, cx - hh * 0.9, S.deck - hh * 0.06, hh * 1.8, hh * 0.14, '#2a2a30');
    [-1, 0, 1].forEach(function (s) { var rx = cx + s * hh * 2.3; if (s === 0) rx = cx + hh * 0.0; var ry = s === 0 ? S.H - hh * 0.05 : S.deck + hh * 0.1; if (s !== 0) { fr(q, rx - hh * 0.15, ry - hh * 0.3, hh * 0.3, hh * 0.3, '#3a3a44'); } });
    o.cx = cx; return o;
  }).out || {};
  var cxm = mt.cx, T = 7, ph = (t / 1000 + (S.seed % 5)) % T, lift = ph < 1 ? 0 : ph < 2.6 ? ease((ph - 1) / 1.6) : ph < 5 ? 1 : ph < 6 ? 1 - ease(ph - 5) : 0;
  var crew2 = lifters(S, 4, false), d3 = crew2[0], h3 = hh * 0.98, sk = d3.skin;
  /* the lifter from the front: hips rise, the bar climbs the legs from the shin to the hip */
  var by = lerp(my - h3 * 0.2, my - h3 * 0.44, lift), hipY = lerp(my - h3 * 0.36, my - h3 * 0.5, lift), shY = hipY - h3 * 0.33 * lerp(0.5, 1, lift), kn = (1 - lift) * h3 * 0.09;
  c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 3; c.shadowOffsetY = 2;
  [-1, 1].forEach(function (sd) { seg(c, [cxm + sd * h3 * 0.05, hipY], [cxm + sd * (h3 * 0.08 + kn), lerp(hipY, my, 0.5)], h3 * 0.13, '#2a2a30'); seg(c, [cxm + sd * (h3 * 0.08 + kn), lerp(hipY, my, 0.5)], [cxm + sd * h3 * 0.07, my - h3 * 0.02], h3 * 0.1, sk); el(c, cxm + sd * h3 * 0.08, my, h3 * 0.05, h3 * 0.02, 0, '#1a1a22'); });
  fp(c, [[cxm - h3 * 0.15, shY], [cxm + h3 * 0.15, shY], [cxm + h3 * 0.08, hipY], [cxm - h3 * 0.08, hipY]], '#c0392b');
  [-1, 1].forEach(function (sd) { seg(c, [cxm + sd * h3 * 0.14, shY + h3 * 0.02], [cxm + sd * h3 * 0.15, by], h3 * 0.1, sk); });
  c.shadowColor = 'transparent'; dot(c, cxm, shY - h3 * 0.1, h3 * 0.075, sk); c.fillStyle = '#1c1410'; c.beginPath(); c.arc(cxm, shY - h3 * 0.115, h3 * 0.077, Math.PI, TAU); c.fill(); fr(c, cxm - h3 * 0.075, shY - h3 * 0.14, h3 * 0.15, h3 * 0.02, '#f2f2f2');
  if (lift < 0.5) for (var ch = 0; ch < 4; ch++) { var cu3 = ((t / 900) + ch / 4) % 1; dot(c, cxm + (ch - 1.5) * h3 * 0.12, by - cu3 * h3 * 0.2, h3 * 0.02 * (1 + cu3), 'rgba(255,255,255,' + (0.5 * (1 - cu3)).toFixed(2) + ')'); }
  c.restore();
  /* the bar bends under the load: the ends sag y = a·x² past the grip, deepest at lockout */
  var bend = hh * 0.07 * lift, L3 = hh * 0.95; c.strokeStyle = '#c8ccd2'; c.lineWidth = Math.max(2, hh * 0.028); c.beginPath(); c.moveTo(cxm - L3, by + bend); c.quadraticCurveTo(cxm, by - bend, cxm + L3, by + bend); c.stroke();
  [-1, 1].forEach(function (sd) { ['#c0392b', '#2a5aa8', '#e8b84a'].forEach(function (pc, k) { var px = cxm + sd * (L3 - hh * 0.06 - k * hh * 0.05), py = by + bend * Math.pow((px - cxm) / L3, 2) * 1.0; fr(c, px - hh * 0.022, py - hh * (0.24 - k * 0.04), hh * 0.044, hh * (0.48 - k * 0.08), pc); }); });
  /* three white lights on the referees' stands when the lift is good */
  var good = ph > 3.0 && ph < 5.6;
  [-1, 0, 1].forEach(function (s, k) { var rx = cxm + s * hh * 2.3, ry = s === 0 ? S.deck - hh * 1.9 : S.deck - hh * 0.35, on = good && ph > 3.0 + k * 0.25; if (s !== 0) { var rf = crew2[1 + k]; rf.dir = -s; rf.col = '#f4f4f4'; person(c, rx, S.deck + hh * 0.06, hh * 0.86, { lean: 0.05, seat: 0.33, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4, 0.6, 0.3, 0.7] }, rf); }
    var ly = S.deck - hh * 1.92; if (s === 0) { [-1, 0, 1].forEach(function (q2, kk) { var on2 = good && ph > 3.0 + kk * 0.25; if (on2) glow(c, cxm + q2 * hh * 0.3, ly, hh * 0.28, '255,255,255', 0.7); dot(c, cxm + q2 * hh * 0.3, ly, hh * 0.09, on2 ? '#ffffff' : '#4a4a52'); }); } });
  /* the loaders at the sides */
  [-1, 1].forEach(function (s, k) { var ld = crew2[3 - k]; ld.dir = -s; ld.col = '#2a2a30'; person(c, cxm + s * hh * 1.5, S.deck + hh * 0.12, hh * 0.9, { lean: 0.05, legs: [0.06, 0, -0.06, 0], arms: [0.3, 0.6, 0.2, 0.7] }, ld); });
  for (var cr2 = 0; cr2 < 8; cr2++) { var hx2 = S.x0 + S.span * (0.06 + cr2 * 0.125), hy2 = S.H - 2; paper(c, function (p) { p.beginPath(); p.ellipse(hx2, hy2, hh * 0.2, hh * 0.15, 0, Math.PI, TAU); p.moveTo(hx2 + hh * 0.1, hy2 - hh * 0.21); p.arc(hx2, hy2 - hh * 0.21, hh * 0.1, 0, TAU); }, '#3a2c26', 0.6); if (good && cr2 % 2) ln(c, [[hx2 + hh * 0.1, hy2 - hh * 0.12], [hx2 + hh * 0.2, hy2 - hh * 0.5]], '#3a2c26', Math.max(2, hh * 0.06)); }
  K.banner(c, S.x0 + S.span * 0.24, S.deck - hh * 1.75, S.label, hh, '#2a3a6a', S.seed, S.hits);
  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - hh * 2.2, y1: S.H });
}

/* ---------------------------------------------------------------- gym
   Read from the name and sub: a weights gym (the 'weights' looks), a yoga studio (the class
   through mountain, arms up, tree and warrior), a football pitch in its net cage (floodlit by
   night), a pool (the crawl's arms turning, θ = ωt), badminton (the shuttle on parabolas), a
   driving range (the swing's arc and the ball's flight), a boxing gym (the bag swinging), a
   climbing wall, a Go and chess school (stones going down), a dance room; a sports ground
   with its track by default. */
function gymKind(P) {
  var w = words(P);
  if (/ฟุตบอล|football|soccer|futsal|ฟุตซอล|หญ้าเทียม|arena|อารีน่า/i.test(w)) return 'football';
  if (/สระว่ายน้ำ|swim|pool|aqua|ว่ายน้ำ/i.test(w)) return 'pool';
  if (/แบด|badminton/i.test(w)) return 'badminton';
  if (/golf|กอล์ฟ|driving range/i.test(w) || subOf(P, 'golf')) return 'golf';
  if (/yoga|โยคะ|pilates|พิลาทิส|barre|stretch|meditat/i.test(w)) return 'yoga';
  if (/boxing|มวย|kick|mma|bjj|jiu|judo|ยูโด|karate|คาราเต้|taekwondo|เทควันโด|fight/i.test(w)) return 'boxing';
  if (/climb|ปีนผา|boulder/i.test(w)) return 'climb';
  if (/หมากล้อม|หมากรุก|chess|\bgo\b|board ?game|บอร์ดเกม/i.test(w)) return 'board';
  if (/dance|เต้น|zumba|ซุมบ้า|aerobic|แอโรบิก/i.test(w)) return 'dance';
  if (/skate|สเก็ต|bmx|pump/i.test(w)) return 'skate';
  if (/tennis|เทนนิส|padel|pickle/i.test(w)) return 'tennis';
  if (/gym|fitness|weights?|iron|muscle|ฟิตเนส|ยิม|body|crossfit|strength|power|lift|street ?workout|calisthen/i.test(w)) return 'weights';
  if (subOf(P, 'sport')) return 'ground';
  return 'weights';
}
function gym(S) {
  var P = placeOf(S), kind = gymKind(P), hh = S.hh;
  if (kind === 'weights') return weights(S);
  if (kind === 'skate') return park(S);
  if (kind === 'yoga' || kind === 'boxing' || kind === 'climb' || kind === 'board' || kind === 'dance') return shopScene(S, 'gym-' + kind, {
    kinds: kind === 'yoga' ? ['glass', 'teak', 'shop', 'row'] : ['shop', 'glass', 'row'], back: { yoga: '#f4ece0', boxing: '#e8e0d0', climb: '#d8dce4', board: '#f2ead8', dance: '#e8eef6' }[kind], floor: kind === 'yoga' ? '#c9a36a' : '#8a7a6a',
    icon: kind === 'yoga' ? ICON.lotus : kind === 'board' ? null : ICON.dumbbell, keyOf: function () { return kind; },
    room: function (q, S, R) { var w = R.x1 - R.x0, o = {};
      if (kind === 'climb') { fp(q, [[R.x0 + w * 0.15, R.y1], [R.x0 + w * 0.2, R.y0 + hh * 0.05], [R.x1 - w * 0.1, R.y0 + hh * 0.05], [R.x1 - w * 0.15, R.y1]], '#b8a890'); var hr = K.rnd(S.seed); for (var k = 0; k < 26; k++) dot(q, R.x0 + w * (0.22 + hr() * 0.6), R.y0 + hh * 0.1 + hr() * (R.y1 - R.y0 - hh * 0.2), hh * 0.03, CLOTH2[k % 8]); }
      if (kind === 'boxing') { o.bag = R.x0 + w * 0.7; ln(q, [[R.x0, R.y0 + hh * 0.06], [R.x1, R.y0 + hh * 0.06]], '#3a3a44', 3); }
      if (kind === 'yoga') { for (var m = 0; m < 4; m++) fr(q, R.x0 + w * (0.08 + m * 0.23), R.y1 - hh * 0.04, w * 0.18, hh * 0.04, ['#4fae8c', '#9b6bd6', '#e5567f', '#4d8fd1'][m]); if (S.seed % 2) { dot(q, R.x1 - w * 0.12, R.y0 + hh * 0.3, hh * 0.1, '#e0b04a'); } }
      if (kind === 'dance') for (var mp = 0; mp < 4; mp++) fr(q, R.x0 + w * (0.04 + mp * 0.24), R.y0 + hh * 0.06, w * 0.22, R.y1 - R.y0 - hh * 0.2, '#d8eaf2');
      if (kind === 'board') for (var tb = 0; tb < 2; tb++) { var tx = R.x0 + w * (0.3 + tb * 0.4); fr(q, tx - hh * 0.25, R.y1 - hh * 0.42, hh * 0.5, hh * 0.05, '#c9a36a'); fr(q, tx - 2, R.y1 - hh * 0.37, 4, hh * 0.37, '#8a5a3a'); o['b' + tb] = tx; }
      return o; },
    work: function (c, S, R, L, o) { var w = R.x1 - R.x0, t = S.t, crew = crowd(S, 5, { casual: 1 });
      if (kind === 'yoga' || kind === 'dance') { var seq = kind === 'yoga' ? [POSE.stand, POSE.up, POSE.tree, POSE.up, POSE.warrior, POSE.fold] : [POSE.stand, POSE.up, POSE.stand, POSE.warrior], u = t / 4000, k = Math.floor(u) % seq.length, Pp = K.mix(seq[k], seq[(k + 1) % seq.length], ease((u % 1) * 2.5 - 1.5));
        for (var i = 0; i < 4; i++) { var x = R.x0 + w * (0.17 + i * 0.23); if (x > R.x1 - hh * 0.3) break; crew[i].dir = 1; person(c, x, R.y1 - hh * 0.04, hh * 0.84, Pp, crew[i]); } }
      else if (kind === 'boxing') { var sw = 0.25 * Math.sin(t / 1000 * TAU / 1.4), bx = o.bag + Math.sin(sw) * hh * 0.5, by = R.y0 + hh * 0.06 + Math.cos(sw) * hh * 0.5; ln(c, [[o.bag, R.y0 + hh * 0.06], [bx, by]], '#3a3a44', 1.5); c.save(); c.translate(bx, by); c.rotate(-sw); fr(c, -hh * 0.1, 0, hh * 0.2, hh * 0.45, '#c0392b'); c.restore();
        var bd = lifters(S, 1, false)[0]; bd.dir = 1; var punch = Math.max(0, Math.sin(t / 1000 * TAU / 1.4 + 1.2)); var mb = brawn(c, o.bag - hh * 0.5, R.y1, hh * 0.88, { lean: 0.1, legs: [0.3, -0.1, -0.3, 0.05], arms: [1.0 + punch * 0.6, 2.0 - punch * 1.8, 1.1, 2.0] }, bd); dot(c, mb.hand[0][0], mb.hand[0][1], hh * 0.05, '#c0392b'); dot(c, mb.hand[1][0], mb.hand[1][1], hh * 0.05, '#c0392b'); }
      else if (kind === 'climb') { var cl = crew[0], v = (t / 1000 / 12) % 1, cyy = lerp(R.y1, R.y0 + hh * 0.9, v), sx = R.x0 + w * 0.45 + Math.sin(v * 12) * hh * 0.1; cl.dir = 1; var a = Math.sin(t / 600); person(c, sx, cyy, hh * 0.8, { lean: -0.1, legs: [0.4 + a * 0.4, -0.8, -0.2 - a * 0.4, -0.6], arms: [2.8 - a * 0.4, 0.2, 2.6 + a * 0.4, 0.2] }, cl); ln(c, [[sx, cyy - hh * 0.6], [sx, R.y0]], '#e8b84a', 1); }
      else if (kind === 'board') { ['b0', 'b1'].forEach(function (b, j) { if (o[b] == null) return; var p1 = crew[j * 2], p2 = crew[j * 2 + 1]; p1.dir = 1; p2.dir = -1; sitAt(c, o[b] - hh * 0.4, R.y1, hh * 0.84, p1, 1, [1.3, 0.8, 0.4, 0.7]); sitAt(c, o[b] + hh * 0.4, R.y1, hh * 0.84, p2, -1, [0.6, 1.4, 0.4, 0.7]);
        fr(c, o[b] - hh * 0.16, R.y1 - hh * 0.48, hh * 0.32, hh * 0.06, '#e0b870'); var n = (Math.floor(t / 1500) + j * 3) % 9; for (var s2 = 0; s2 < n; s2++) dot(c, o[b] - hh * 0.13 + (s2 % 5) * hh * 0.065, R.y1 - hh * 0.47 - Math.floor(s2 / 5) * 2, hh * 0.022, s2 % 2 ? '#f8f8f4' : '#1a1a22'); }); } }
  });
  /* the outdoor grounds: a pitch, a pool, a court, a range, a track */
  var c = S.c, L = plan(S, 'gym-' + kind), r = L.r, t = S.t, lit = S.night, key = 'gym|' + kind;
  var still = layer(S, key, stageBox(S), function (q) {
    var o = {}; street(q, S, 'lawn', r); K.setting(S);
    var f0 = S.x0 + hh * 0.9, f1 = S.x1 - hh * 0.9;
    if (kind === 'football' || kind === 'ground' || kind === 'tennis') { paper(q, rect(f0, S.deck - hh * 0.1, f1 - f0, S.H - S.deck + hh * 0.1), nt(S, kind === 'tennis' ? '#3a7a8a' : '#4f9a4a'), 0.8); q.strokeStyle = nt(S, '#f4f4f4'); q.lineWidth = 1.5; q.strokeRect(f0 + hh * 0.2, S.deck, f1 - f0 - hh * 0.4, S.H - S.deck - hh * 0.1); ln(q, [[(f0 + f1) / 2, S.deck], [(f0 + f1) / 2, S.H]], nt(S, '#f4f4f4'), 1.5);
      if (kind === 'ground') { paper(q, rect(f0, S.deck - hh * 0.1, f1 - f0, hh * 0.18), nt(S, '#b8604a'), 0.6); for (var ln2 = 1; ln2 < 4; ln2++) ln(q, [[f0, S.deck - hh * 0.1 + ln2 * hh * 0.045], [f1, S.deck - hh * 0.1 + ln2 * hh * 0.045]], nt(S, '#f4f4f4'), 0.8); }
      if (kind !== 'tennis') { goal(q, S, f0 + hh * 0.25, S.deck + hh * 0.25, hh * 0.9, 1); goal(q, S, f1 - hh * 0.25, S.deck + hh * 0.25, hh * 0.9, -1); }
      else { ln(q, [[(f0 + f1) / 2, S.deck - hh * 0.3], [(f0 + f1) / 2, S.H]], nt(S, '#f4f4f4'), 2); }
      if (kind === 'football') { q.strokeStyle = S.night ? 'rgba(200,200,220,.25)' : 'rgba(40,40,50,.25)'; q.lineWidth = 1; q.beginPath(); for (var nx = f0; nx <= f1; nx += hh * 0.12) { q.moveTo(nx, S.deck - hh * 1.5); q.lineTo(nx, S.deck); } for (var ny = S.deck - hh * 1.5; ny < S.deck; ny += hh * 0.12) { q.moveTo(f0, ny); q.lineTo(f1, ny); } q.stroke(); [f0, f1].forEach(function (px) { fr(q, px - 2, S.deck - hh * 1.55, 4, hh * 1.55, nt(S, '#5a5a62')); }); } }
    if (kind === 'pool') { paper(q, rect(f0, S.deck - hh * 0.05, f1 - f0, S.H - S.deck), nt(S, '#e8e4dc'), 0.8); fr(q, f0 + hh * 0.15, S.deck + hh * 0.05, f1 - f0 - hh * 0.3, S.H - S.deck - hh * 0.05, S.night ? '#2a6a9a' : '#5ab8e0'); for (var lr = 1; lr < 3; lr++) { var ly = S.deck + hh * 0.05 + lr * (S.H - S.deck - hh * 0.05) / 3; for (var bx = f0 + hh * 0.2; bx < f1 - hh * 0.2; bx += 6) dot(q, bx, ly, 1.6, (bx / 6) % 2 < 1 ? '#d9342b' : '#f4f4f4'); }
      fr(q, f1 - hh * 0.9, S.deck - hh * 1.0, 4, hh * 1.0, nt(S, '#f4f4f4')); fr(q, f1 - hh * 1.1, S.deck - hh * 1.0, hh * 0.45, 4, nt(S, '#f4f4f4')); o.chair = f1 - hh * 0.9; var um = f0 + hh * 0.6; ln(q, [[um, S.deck], [um, S.deck - hh * 1.0]], '#d8d8de', 2); for (var p = 0; p < 6; p++) fp(q, [[um, S.deck - hh * 1.12], [um - hh * 0.5 + p * hh * 1 / 6, S.deck - hh * 0.9], [um - hh * 0.5 + (p + 1) * hh / 6, S.deck - hh * 0.9]], nt(S, p % 2 ? '#e5567f' : '#f4f4f4')); }
    if (kind === 'badminton') { var hx0 = f0, hx1 = f1, ht = S.deck - hh * 2.05; for (var x = hx0; x <= hx1; x += (hx1 - hx0) / 4) fr(q, x - 3, ht + hh * 0.3, 6, S.deck - ht - hh * 0.3, nt(S, '#8a8a92')); paper(q, poly([[hx0 - hh * 0.2, ht + hh * 0.35], [(hx0 + hx1) / 2, ht], [hx1 + hh * 0.2, ht + hh * 0.35]]), nt(S, '#a8b0b8'), 1.4);
      paper(q, rect(hx0, S.deck - hh * 0.05, hx1 - hx0, hh * 0.3), nt(S, '#2f7a5a'), 0.6); ln(q, [[(hx0 + hx1) / 2, S.deck - hh * 0.7], [(hx0 + hx1) / 2, S.deck]], nt(S, '#f4f4f4'), 2); fr(q, (hx0 + hx1) / 2 - 1, S.deck - hh * 0.72, 2, hh * 0.3, 'rgba(255,255,255,.4)');
      if (S.night) for (x = hx0 + hh * 0.6; x < hx1; x += hh * 1.2) glow(q, x, ht + hh * 0.45, hh * 0.5, '240,255,230', 0.4); }
    if (kind === 'golf') { for (var b = 0; b < 4; b++) { var bxx = S.x0 + S.span * (0.25 + b * 0.18); ln(q, [[bxx, S.deck - hh * 0.05], [bxx, S.deck - hh * 0.45]], nt(S, '#f4f4f4'), 1.5); fp(q, [[bxx, S.deck - hh * 0.45], [bxx + hh * 0.18, S.deck - hh * 0.4], [bxx, S.deck - hh * 0.35]], nt(S, ['#d9342b', '#e8b84a', '#2a5aa8', '#f4f4f4'][b])); }
      fr(q, f0 - hh * 0.4, S.deck - hh * 1.2, hh * 1.2, hh * 0.08, nt(S, '#3a6a3a')); fr(q, f0 - hh * 0.35, S.deck - hh * 1.12, 4, hh * 1.12, nt(S, '#8a8a92')); fr(q, f0 + hh * 0.7, S.deck - hh * 1.12, 4, hh * 1.12, nt(S, '#8a8a92')); fr(q, f0 - hh * 0.3, S.deck - hh * 0.04, hh * 1.0, hh * 0.08, nt(S, '#2f7a3a')); o.tee = f0 + hh * 0.2; }
    if (lit && (kind === 'football' || kind === 'ground' || kind === 'tennis' || kind === 'golf')) [f0, f1].forEach(function (px) { fr(q, px - 2, S.deck - hh * 2.1, 4, hh * 2.1, nt(S, '#5a5a62')); fr(q, px - hh * 0.2, S.deck - hh * 2.2, hh * 0.4, hh * 0.12, '#fffbe0'); glow(q, px, S.deck - hh * 2.1, hh * 1.2, '255,255,230', 0.5); });
    var sx = S.x0 + S.span * 0.5; o.sign = signAt(q, S, sx, S.deck - hh * (kind === 'badminton' ? 1.82 : 2.0), P, hh * 0.78, nt(S, '#2a3a5a'), lit || null);
    if (kind !== 'badminton') { ln(q, [[sx - hh * 0.5, S.deck - hh * 1.6], [sx - hh * 0.5, S.deck - hh * 2.0]], nt(S, '#5a5a62'), 2); ln(q, [[sx + hh * 0.5, S.deck - hh * 1.6], [sx + hh * 0.5, S.deck - hh * 2.0]], nt(S, '#5a5a62'), 2); }
    if (r() < 0.6) o.incense = spiritHouse(q, S, S.x0 + hh * 0.5, hh * 0.85, (S.seed >>> 2) % 3);
    return o;
  }).out || {};
  L.incense = still.incense;
  var crew = crowd(S, 6, { casual: 1 }), quiet = S.night && !lit;
  if (kind === 'football' || kind === 'ground') football(c, S, [S.x0 + S.span * 0.28, S.x0 + S.span * 0.42, S.x0 + S.span * 0.58, S.x0 + S.span * 0.72], S.deck + hh * 0.25, hh * 0.86, crew, 0);
  if (kind === 'ground' && !S.night) for (var j = 0; j < 2; j++) { var rv = 0.7 + j * 0.1, rd = crew[4 + j]; rd.dir = 1; person(c, stroll(S, j, rv, j * 0.4), S.deck + hh * 0.02, hh * 0.84, K.walkP(t / 1000 * TAU * 1.3 + j, true), rd); }
  if (kind === 'tennis' || kind === 'badminton') { var u = (t / 1000 / 1.3) % 2, f = u % 1, ax = S.x0 + S.span * 0.3, bx2 = S.x1 - S.span * 0.3, xA = u < 1 ? lerp(ax, bx2, f) : lerp(bx2, ax, f), yA = S.deck - hh * (0.6 + Math.sin(Math.PI * f) * (kind === 'badminton' ? 0.9 : 0.5));
    [ax, bx2].forEach(function (x, k) { var d = crew[k]; d.dir = k ? -1 : 1; var hit = (k === 0 ? (u > 1.85 || u < 0.15) : (u > 0.85 && u < 1.15)) ? 1 : 0; var me = person(c, x, S.deck + hh * 0.12, hh * 0.9, { lean: 0.1, legs: [0.25, -0.2, -0.2, 0], arms: [2.0 + hit * 0.8, 0.3, 0.6, 0.6] }, d); ln(c, [me.hand[0], [me.hand[0][0] + d.dir * hh * 0.12, me.hand[0][1] - hh * 0.2]], '#5a5a62', 1.5); el(c, me.hand[0][0] + d.dir * hh * 0.15, me.hand[0][1] - hh * 0.25, hh * 0.06, hh * 0.08, 0, 'rgba(255,255,255,.5)'); });
    if (kind === 'badminton') { fp(c, [[xA, yA], [xA - 3, yA - 5], [xA + 3, yA - 5]], '#f4f4f4'); dot(c, xA, yA, 2, '#f4f4f4'); } else dot(c, xA, yA, 2.5, '#d8f04a'); }
  if (kind === 'pool') { for (var sw = 0; sw < 2; sw++) { var lane = S.deck + hh * 0.05 + (sw + 0.5) * (S.H - S.deck - hh * 0.05) / 3, sxw = stroll(S, sw, sw ? -0.35 : 0.3, sw * 0.4), dir = sw ? -1 : 1, a = t / 1000 * TAU * 0.9 + sw;
      el(c, sxw, lane, hh * 0.35, hh * 0.06, 0, 'rgba(255,255,255,.35)'); dot(c, sxw + dir * hh * 0.32, lane - hh * 0.03, hh * 0.07, ['#e5567f', '#f2c94c'][sw]); ln(c, [[sxw + dir * hh * 0.2, lane - hh * 0.03], [sxw + dir * hh * 0.2 + Math.cos(a) * dir * hh * 0.25, lane - hh * 0.03 - Math.max(0, Math.sin(a)) * hh * 0.25]], K.SKIN[(sw + S.seed) % 5], hh * 0.05); }
    if (still.chair) { var lg = dressUp(crew[2], '#d9342b', '#d9342b'); lg.dir = -1; person(c, still.chair, S.deck - hh * 1.0, hh * 0.8, { lean: 0.05, seat: 0.3, legs: [1.45, -1.4, 1.4, -1.45], arms: [0.4, 0.6, 0.3, 0.7] }, lg); } }
  if (kind === 'golf' && still.tee) { var gp = (t / 1000 / 3.5) % 1, sw2 = gp < 0.4 ? -2.4 * ease(gp / 0.4) : gp < 0.5 ? -2.4 + 5 * ease((gp - 0.4) / 0.1) : 2.6, gd = crew[0]; gd.dir = 1; var mg = person(c, still.tee, S.deck + hh * 0.02, hh * 0.92, { lean: 0.35, legs: [0.15, 0, -0.15, 0], arms: [0.6 + sw2 * 0.5, 0.1, 0.5 + sw2 * 0.5, 0.15] }, gd);
    ln(c, [mg.hand[0], [mg.hand[0][0] + Math.sin(sw2 + 0.3) * hh * 0.45, mg.hand[0][1] + Math.cos(sw2 + 0.3) * hh * 0.45]], '#c8ccd2', 1.5);
    if (gp > 0.45) { var bt = (gp - 0.45) / 0.55; dot(c, still.tee + hh * 0.3 + bt * S.span * 0.55, S.deck - hh * 0.05 - Math.sin(Math.PI * bt) * hh * 1.4, 2, '#f8f8f4'); } }
  streetLife(S, L);
  S.hits.push({ k: 'place', x0: S.x0 + hh * 0.8, x1: S.x1 - hh * 0.8, y0: S.deck - hh * 2.0, y1: S.H });
}

/* the frame and the street's things, for the craft and Akha files' portraits of one place */
D.civic = { shop: shopScene, layer: layer, stageBox: stageBox, plan: plan, stateOf: stateOf, clock: clock, signAt: signAt, spiritHouse: spiritHouse, smoke: smoke, moth: moth, bulb: bulb,
  dog: dog, cat: cat, chicken: chicken, motorbike: motorbike, bicycle: bicycle, songthaew: songthaew, banana: banana, bougainvillea: bougainvillea, frangipani: frangipani, chilliPots: chilliPots,
  rainTree: rainTree, shrub: shrub, khom: khom, marigolds: marigolds, roadPlate: roadPlate, street: street, shutter: shutter, facade: facade, streetLife: streetLife, nt: nt, pick: pick,
  words: words, has: has, subOf: subOf, crowd: crowd, glow: glow, el: el, fr: fr, fp: fp, dot: dot, ln: ln, reach: reach, ICON: ICON, CLOTH2: CLOTH2 };
D.addScene('school', school, null, 'h = h₀·ease(t/8) (the flag)<br>y = v₀t − ½gt² (the ball)');
D.addScene('community', community, null, 'r = r₀ + vt (the horn)<br>y = |sin ωt| (the beat)');
D.addScene('freshmarket', freshmarket, null, 'θ = θ₀·e<sup>−λt</sup>·cos ωt (the scale)');
D.addScene('hospital', hospital, null, 'x = x₀ + d·ease(t/T) (the ambulance)');
D.addScene('healthstation', healthstation, null, 'θ = θ₀·cos ωt (the baby on the scale)');
D.addScene('park', park, null, 'y = v₀t − ½gt² (the fountain)<br>θ = θ₀·cos ωt (the swing)');
D.addScene('university', university, null, 'x = x₀ + vt (the bicycles)');
D.addScene('gym', gym, null, 'θ = ωt (the crawl)<br>y = v₀t − ½gt² (the shuttle)');
D.addScene('weights', weights, WEIGHTS_WORDS, 'the bar path x = x₀ (the squat)<br>θ = θ₀·sin ωt (the kettlebell)', 1);
D.addScene('clinic', clinic, null, 'n = ⌊t/5⌋ (the queue)');
D.addScene('dentist', dentist, null, 'x = x₀ + sin(2π·40t) (the drill)');
D.addScene('optician', optician, null, 'the E at 5′ of arc, row on row');
D.addScene('tattoo', tattoo, null, 's = s₀ + vt (the line)');
D.addScene('training', training, null, 'x = x₀ + d·ease(t) (the beads)');
})();
