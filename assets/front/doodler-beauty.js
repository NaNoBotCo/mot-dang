/* Beauty clinics for the auto-doodler (Nan, 2026-10-02: "do some for beauty clinics").
   'beautyclinic' draws one clinic in one of five looks, dealt by the place's seed and steered
   by its name: the shophouse front, the consultation room, the treatment room, the Lanna villa
   in a garden, and the unit in a mall corridor (a place that stands inside a building). Event
   words (a skincare talk, an aesthetic clinic) bring it to the band as well.
   The motions share one easing, y = ½h(1 − cos 2πt/T): the scan line down the face, the
   sliding doors, the nurse's walk, the LED panel turning red to blue. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, TAU = K.TAU;
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function cyc(t, T) { return 0.5 - 0.5 * Math.cos(t / T * TAU); }

/* ---------------------------------------------------------------- colour and small fills */
function hx(c) { return [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)]; }
function mixc(a, b, u) { var A = hx(a), B = hx(b); return 'rgb(' + A.map(function (v, i) { return Math.round(lerp(v, B[i], u)); }).join(',') + ')'; }
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function fc(c, x, y, r, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
function fe(c, x, y, rx, ry, rot, col) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot, 0, TAU); c.fill(); }
function fp(c, pts, col) { c.fillStyle = col; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.closePath(); c.fill(); }
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
/* a soft round glow from a cut-once disc of the hue */
var GLOW = {};
function glow(c, x, y, r, hue, a) {
  var h = Math.round(hue / 15) * 15 % 360, o = GLOW[h];
  if (!o && typeof document !== 'undefined') { o = GLOW[h] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'hsla(' + h + ',95%,62%,1)'); g.addColorStop(0.45, 'hsla(' + h + ',95%,62%,.4)'); g.addColorStop(1, 'hsla(' + h + ',95%,62%,0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  if (!o || a <= 0) return;
  c.save(); c.globalAlpha = Math.min(1, a); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}

/* ---------------------------------------------------------------- the still parts, cut once
   a layer is the stage between y0 and y1 at the page's own scale, keyed by everything it shows */
var CACHE = [];
function layer(S, key, y0, y1, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : null;
  if (!m || typeof document === 'undefined') return draw(c);
  var k = key + '|' + [m.a, m.d, m.e, m.f].join(','), e = null;
  for (var i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var bx = Math.floor(m.a * (S.x0 - 2) + m.e), by = Math.floor(m.d * y0 + m.f), bw = Math.ceil(m.a * (S.span + 4)) + 2, bh = Math.ceil(m.d * (y1 - y0)) + 2;
    var o = document.createElement('canvas'); o.width = Math.max(1, bw); o.height = Math.max(1, bh);
    var q = o.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - bx, m.f - by);
    e = { k: k, cv: o, x: bx, y: by, out: draw(q) }; CACHE.unshift(e); if (CACHE.length > 14) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.x, e.y); c.restore();
  return e.out;
}
/* what a layer worked out (door, lamps, bed …), kept with it for the moving parts */
function keep(L) { var o = {}; for (var f in L) if (f !== 'r') o[f] = L[f]; return o; }
function take(L, o) { if (o) for (var f in o) L[f] = o[f]; }

/* ---------------------------------------------------------------- the name for the sign
   Map names here carry their treatment lists ("โบท็อกซ์ ฟิลเลอร์ ร้อยไหม …"); the sign keeps the
   clinic's own name: the first Thai run and the first Latin run, cut at the first treatment word */
var STUFF = /โบท|ฟิลเล|ฟิวเล|ร้อยไหม|เมโส|ศัลย|ราคา|ปรับรูป|ยกกระชับ|หน้าใส|หน้าเรียว|ลดหุ่น|ลดสิว|ผิวใส|ไฮฟู|สเตม|คีเล|รักษา|จมูก|หน้าอก|ฉีด|งานผิว|ปลูกผม|ชะลอ|ครบวงจร|สักคิ้ว|สักปาก|จี้ไฝ|ต่อขนตา|โครต|ยืนหนึ่ง|เลเซอร์|^สาขา|^เชียงใหม่|^เชียงราย|^ภาคเหนือ/;
var STUFF_EN = /^(botox|filler|ultherapy|vshape|hifu|by|anti-aging|dermatology\S*|chiang ?mai|cnx)$/i;
var NAMES = {};
function signName(P) {
  var id = P.id || P.name || '';
  if (NAMES[id]) return NAMES[id];
  var raw = String(P.name || P.nameTh || '').replace(/[ᄀ-ᇿ㄰-㆏가-힯]+/g, ' ');
  var parts = raw.split(/\s*[-–]\s+|\s+[-–]\s*|[|:•]|\s+I\s+/), th = [], en = [], thStop = false, enStop = false;
  parts.forEach(function (part) {
    part.split(/\s+/).filter(Boolean).forEach(function (w) {
      if (/[฀-๿]/.test(w)) {
        if (en.length) enStop = true;
        if (thStop) return;
        if (STUFF.test(w)) { if (th.length) thStop = true; return; }
        if (th.join(' ').length + w.length > 26) { if (th.length) thStop = true; return; }
        th.push(w);
      } else {
        if (enStop) return;
        if (STUFF_EN.test(w)) { if (en.length) enStop = true; return; }
        if (en.join(' ').length + w.length > 28) { enStop = true; return; }
        en.push(w);
      }
    });
    if (th.length) thStop = true; if (en.length) enStop = true;
  });
  var e = P.nameEn && P.nameEn !== P.name ? P.nameEn : en.join(' '), t = th.join(' ');
  return (NAMES[id] = t ? { nameTh: t, nameEn: e } : e ? { nameTh: e, nameEn: '' } : { nameTh: 'คลินิกความงาม', nameEn: 'Beauty clinic' });
}
/* the sign, its letters shrunk until the board fits the width it has */
function plate(c, cx, y, P, hh, col, lit, maxW) {
  var N = signName(P), f1 = Math.max(11, hh * 0.19), f2 = Math.max(9, hh * 0.13);
  c.save(); c.font = '800 ' + Math.round(f1) + 'px "Sarabun",system-ui,sans-serif'; var w1 = c.measureText(N.nameTh).width;
  c.font = '700 ' + Math.round(f2) + 'px "Sarabun",system-ui,sans-serif'; var w2 = N.nameEn ? c.measureText(N.nameEn).width : 0; c.restore();
  var w = Math.max(w1, w2) + hh * 0.5, s = w > maxW ? Math.max(0.6, maxW / w) : 1;
  return K.sign(c, cx, y, N, hh * s, col, lit);
}

/* ---------------------------------------------------------------- which clinic
   the name steers: laser and light → the treatment room; skin doctors and consults → the
   consultation; spa, wellness, a home or a massage house → the villa; inside a building → the mall */
var LOOKS = ['front', 'consult', 'treat', 'villa'];
function lookOf(S, r) {
  var P = S.place || {}, nm = (P.name || '') + ' ' + (P.nameEn || '') + ' ' + (S.title || '') + ' ' + (S.label || ''), w = [3, 2, 2, 1.4];
  if (P.inside) return 'mall';
  if (/laser|เลเซอร์|\bled\b|hifu|ไฮฟู|ultherapy|ยกกระชับ|light/i.test(nm)) w[2] += 5;
  if (/skin|ผิวหนัง|derma|consult|ปรึกษา|dr\.|หมอ|แพทย์|เวชกรรม|medical/i.test(nm)) w[1] += 4;
  if (/spa|wellness|สุขภาพ|โคลน|home|บ้าน|natur|เนเจอร์|garden|villa|massage|นวด/i.test(nm) || P.cat === 'massage') w[3] += 5;
  if (/talk|class|workshop|เวิร์กช็อป|สัมมนา/i.test(nm)) w[1] += 3;
  var sum = w.reduce(function (a, b) { return a + b; }, 0), u = r() * sum;
  for (var i = 0; i < 4; i++) { u -= w[i]; if (u < 0) return LOOKS[i]; }
  return 'front';
}
/* façades: white and rose, cream and plum, blush, lilac, mint with a rose door, peach */
var PAL = [
  { wall: '#fbf6f3', rose: '#e7a3b3', deep: '#b85b78', glass: '#f4dfe6', room: '#fbeef0' },
  { wall: '#f7efe6', rose: '#d98ca0', deep: '#8e3b5a', glass: '#efe0e4', room: '#f6e6e4' },
  { wall: '#fdf8f8', rose: '#f2c1cc', deep: '#c76b86', glass: '#f8e8ee', room: '#fdf1f3' },
  { wall: '#f5f2f0', rose: '#c9a0c8', deep: '#7a4a7e', glass: '#ece0ef', room: '#f3ecf4' },
  { wall: '#f8f4ee', rose: '#9fcfc4', deep: '#c76b86', glass: '#e3f0ec', room: '#eef6f2' },
  { wall: '#f3e9e2', rose: '#e2b5a0', deep: '#a0583e', glass: '#f3e3da', room: '#f8ece4' }
];
var BLOOM = [['#fbf7f4', '#e5567f'], ['#f2a7c3', '#b8326a'], ['#b986d6', '#6a2a8a'], ['#f7e08a', '#d0601a'], ['#ffffff', '#d9a441']];

/* ---------------------------------------------------------------- pieces
   a phalaenopsis in a pot: two broad leaves, a stem on a quadratic arch, blooms of five petals */
function orchid(q, x, y, s, col, dir) {
  dir = dir || 1;
  fe(q, x - s * 0.1, y - s * 0.3, s * 0.2, s * 0.06, -0.35, '#2f6b45'); fe(q, x + s * 0.1, y - s * 0.31, s * 0.2, s * 0.06, 0.35, '#3a7a50');
  fp(q, [[x - s * 0.15, y - s * 0.28], [x + s * 0.15, y - s * 0.28], [x + s * 0.11, y], [x - s * 0.11, y]], '#f4f1ec');
  fr(q, x - s * 0.15, y - s * 0.28, s * 0.3, s * 0.035, '#d4a23f');
  var a = [x, y - s * 0.3], b = [x - dir * s * 0.06, y - s * 1.0], e = [x + dir * s * 0.34, y - s * 0.86];
  q.strokeStyle = '#3d6b3a'; q.lineWidth = Math.max(1, s * 0.022); q.beginPath(); q.moveTo(a[0], a[1]); q.quadraticCurveTo(b[0], b[1], e[0], e[1]); q.stroke();
  for (var k = 0; k < 6; k++) {
    var u = 0.42 + k * 0.115, px = (1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * b[0] + u * u * e[0], py = (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * b[1] + u * u * e[1];
    bloom(q, px, py + s * 0.04, s * 0.085 * (1 - k * 0.07), col);
  }
}
function bloom(q, x, y, r, col) {
  for (var i = 0; i < 5; i++) { var a = i / 5 * TAU - Math.PI / 2; fe(q, x + Math.cos(a) * r * 0.55, y + Math.sin(a) * r * 0.55, r * (i % 2 ? 0.62 : 0.5), r * 0.4, a, col[0]); }
  fc(q, x, y, r * 0.3, col[1]);
}
/* a gold lai kham panel: lacquer ground, a double gold border, a lattice of four-petal flowers */
function laiKham(q, x, y, w, h, base) {
  fr(q, x, y, w, h, base || '#4a1418');
  q.strokeStyle = '#e0b04a'; q.lineWidth = Math.max(1, h * 0.02); q.strokeRect(x + h * 0.04, y + h * 0.04, w - h * 0.08, h - h * 0.08);
  q.lineWidth = Math.max(0.6, h * 0.008); q.strokeRect(x + h * 0.08, y + h * 0.08, w - h * 0.16, h - h * 0.16);
  var n = Math.max(2, Math.round((w - h * 0.16) / (h * 0.3))), m = Math.max(2, Math.round((h - h * 0.16) / (h * 0.3))), cw = (w - h * 0.16) / n, ch = (h - h * 0.16) / m;
  q.fillStyle = '#e8b84a';
  for (var i = 0; i < n; i++) for (var j = 0; j < m; j++) {
    var cx = x + h * 0.08 + (i + 0.5) * cw, cy = y + h * 0.08 + (j + 0.5) * ch, r = Math.min(cw, ch) * 0.32;
    for (var k = 0; k < 4; k++) { var a = k * Math.PI / 2; q.beginPath(); q.arc(cx + Math.cos(a) * r * 0.42, cy + Math.sin(a) * r * 0.42, r * 0.3, 0, TAU); q.fill();
      var b = a + Math.PI / 4; q.beginPath(); q.ellipse(cx + Math.cos(b) * r * 0.82, cy + Math.sin(b) * r * 0.82, r * 0.28, r * 0.1, b, 0, TAU); q.fill(); }
    q.fillStyle = base || '#4a1418'; q.beginPath(); q.arc(cx, cy, r * 0.16, 0, TAU); q.fill(); q.fillStyle = '#e8b84a';
  }
}
/* a gold trim band: little diamonds and dots along a strip */
function laiBand(q, x0, x1, y, h, base) {
  if (base) fr(q, x0, y, x1 - x0, h, base);
  q.fillStyle = '#e0b04a'; fr(q, x0, y, x1 - x0, Math.max(0.8, h * 0.12), '#e0b04a'); fr(q, x0, y + h - Math.max(0.8, h * 0.12), x1 - x0, Math.max(0.8, h * 0.12), '#e0b04a');
  for (var x = x0 + h * 0.5; x < x1 - h * 0.3; x += h * 0.9) { q.fillStyle = '#e8b84a'; q.beginPath(); q.moveTo(x, y + h * 0.2); q.lineTo(x + h * 0.25, y + h * 0.5); q.lineTo(x, y + h * 0.8); q.lineTo(x - h * 0.25, y + h * 0.5); q.closePath(); q.fill(); fc(q, x + h * 0.45, y + h * 0.5, h * 0.07, '#e8b84a'); }
}
/* a woman's face in profile, drawn as a line on the glass: brow, nose, lips, chin, the hair a sweep */
function face(q, x, y, s, col, w) {
  q.save(); q.strokeStyle = col; q.lineWidth = w; q.lineCap = 'round'; q.lineJoin = 'round'; q.beginPath();
  q.moveTo(x - s * 0.05, y - s * 0.5); q.quadraticCurveTo(x + s * 0.12, y - s * 0.46, x + s * 0.14, y - s * 0.22);
  q.lineTo(x + s * 0.24, y - s * 0.04); q.lineTo(x + s * 0.15, y + s * 0.0); q.quadraticCurveTo(x + s * 0.2, y + s * 0.06, x + s * 0.16, y + s * 0.1);
  q.quadraticCurveTo(x + s * 0.2, y + s * 0.14, x + s * 0.14, y + s * 0.18); q.quadraticCurveTo(x + s * 0.12, y + s * 0.3, x + s * 0.0, y + s * 0.3);
  q.quadraticCurveTo(x - s * 0.02, y + s * 0.4, x - s * 0.04, y + s * 0.5); q.stroke();
  q.beginPath(); q.moveTo(x - s * 0.05, y - s * 0.5); q.bezierCurveTo(x - s * 0.4, y - s * 0.5, x - s * 0.45, y - s * 0.05, x - s * 0.3, y + s * 0.25); q.quadraticCurveTo(x - s * 0.2, y + s * 0.42, x - s * 0.34, y + s * 0.55); q.stroke();
  q.beginPath(); q.moveTo(x + s * 0.08, y - s * 0.16); q.quadraticCurveTo(x + s * 0.11, y - s * 0.19, x + s * 0.13, y - s * 0.15); q.stroke();
  q.restore();
}
/* a four-point sparkle, its arms on quadratic curves */
function spark(c, x, y, z, col) {
  c.fillStyle = col; c.beginPath(); c.moveTo(x, y - z * 2); c.quadraticCurveTo(x, y, x + z * 2, y); c.quadraticCurveTo(x, y, x, y + z * 2); c.quadraticCurveTo(x, y, x - z * 2, y); c.quadraticCurveTo(x, y, x, y - z * 2); c.fill();
}
/* the san phra phum on its post: a Lanna house in two red tiers, kalae at the gable, a marigold
   string across the shelf, a red drink with its straw, a garland and a bowl */
function spiritHouse(q, x, y, s, night) {
  var gold = night ? '#b8872f' : '#e0b04a', red = night ? '#7a2420' : '#b8382c';
  fr(q, x - s * 0.04, y - s * 0.75, s * 0.08, s * 0.75, night ? '#bdb6c6' : '#f2ede4'); fr(q, x - s * 0.06, y - s * 0.4, s * 0.12, s * 0.04, gold);
  fp(q, [[x - s * 0.1, y], [x + s * 0.1, y], [x + s * 0.06, y - s * 0.05], [x - s * 0.06, y - s * 0.05]], gold);
  fr(q, x - s * 0.3, y - s * 0.79, s * 0.6, s * 0.05, gold);
  fr(q, x - s * 0.15, y - s * 1.02, s * 0.3, s * 0.23, night ? '#c9b58a' : '#f3e2b0');
  fr(q, x - s * 0.05, y - s * 0.97, s * 0.1, s * 0.18, gold);
  fp(q, [[x - s * 0.24, y - s * 1.0], [x, y - s * 1.2], [x + s * 0.24, y - s * 1.0]], red);
  fp(q, [[x - s * 0.16, y - s * 1.12], [x, y - s * 1.3], [x + s * 0.16, y - s * 1.12]], red);
  fp(q, [[x - s * 0.08, y - s * 1.04], [x, y - s * 1.14], [x + s * 0.08, y - s * 1.04]], gold);
  ln(q, [[x, y - s * 1.3], [x - s * 0.09, y - s * 1.4]], gold, Math.max(1, s * 0.025)); ln(q, [[x, y - s * 1.3], [x + s * 0.09, y - s * 1.4]], gold, Math.max(1, s * 0.025));
  for (var k = 0; k <= 10; k++) { var u = k / 10; fc(q, x - s * 0.28 + u * s * 0.56, y - s * 0.74 + Math.sin(u * Math.PI) * s * 0.07, s * 0.028, k % 2 ? '#f29a2a' : '#f2c94c'); }
  fr(q, x + s * 0.17, y - s * 0.92, s * 0.05, s * 0.13, '#d9342b'); ln(q, [[x + s * 0.2, y - s * 0.92], [x + s * 0.23, y - s * 0.99]], '#f2f2f2', 1);
  fe(q, x - s * 0.21, y - s * 0.82, s * 0.06, s * 0.025, 0, '#f2e6c9'); fc(q, x - s * 0.21, y - s * 0.85, s * 0.03, '#f29a2a');
  return [x - s * 0.08, y - s * 0.8];
}
/* incense: two sticks, the smoke curling as x = A·sin(ky − ωt) */
function incense(c, x, y, len, t) {
  c.lineWidth = 1; c.lineCap = 'round';
  for (var i = 0; i < 2; i++) {
    var tx = x + i * 2.4, ty = y - len;
    ln(c, [[x + i * 2, y], [tx, ty]], '#b5532f', 1); fc(c, tx, ty, 1.1, '#ff7a3a');
    c.strokeStyle = 'rgba(240,236,228,.5)'; c.beginPath();
    for (var j = 0; j <= len * 1.8; j += 3) { var xx = tx + Math.sin(j * 0.11 - t / 650 + i) * (1 + j * 0.07); j ? c.lineTo(xx, ty - j) : c.moveTo(xx, ty); } c.stroke();
  }
}
/* a scooter parked side-on: two wheels, the floorboard, the leg shield, a seat, a helmet on it */
function scooter(q, x, y, s, col, dir, helmet) {
  var d = dir || 1, r = s * 0.11;
  [x - d * s * 0.3, x + d * s * 0.3].forEach(function (wx) { fc(q, wx, y - r, r, '#1f1f24'); fc(q, wx, y - r, r * 0.45, '#b9bcc6'); });
  fp(q, [[x - d * s * 0.44, y - s * 0.22], [x - d * s * 0.42, y - s * 0.36], [x - d * s * 0.1, y - s * 0.38], [x - d * s * 0.06, y - s * 0.2], [x + d * s * 0.2, y - s * 0.2], [x + d * s * 0.24, y - s * 0.5], [x + d * s * 0.33, y - s * 0.52], [x + d * s * 0.36, y - s * 0.2], [x + d * s * 0.3, y - s * 0.12], [x - d * s * 0.38, y - s * 0.12]], col);
  fe(q, x - d * s * 0.25, y - s * 0.4, s * 0.17, s * 0.045, 0, '#2a2226');
  ln(q, [[x + d * s * 0.28, y - s * 0.52], [x + d * s * 0.26, y - s * 0.62], [x + d * s * 0.18, y - s * 0.64]], '#3a3a40', Math.max(1.4, s * 0.03));
  fc(q, x + d * s * 0.36, y - s * 0.46, s * 0.035, '#fff6c0');
  if (helmet) { fe(q, x - d * s * 0.26, y - s * 0.47, s * 0.09, s * 0.075, 0, helmet); fr(q, x - d * s * 0.33, y - s * 0.47, s * 0.14, s * 0.02, '#2a2226'); }
}
/* a hanging khom: a drum of paper with gold rims and a fringe; lit, it glows */
function khom(c, x, y, s, col, lit, th) {
  var a = th || 0, bx = x + Math.sin(a) * s * 0.6, by = y + Math.cos(a) * s * 0.6;
  ln(c, [[x, y], [bx, by]], 'rgba(40,20,30,.8)', 1);
  if (lit) glow(c, bx, by + s * 0.3, s * 1.3, 30, 0.55);
  fe(c, bx, by + s * 0.3, s * 0.26, s * 0.32, 0, lit ? mixc(col, '#fff2c8', 0.45) : col);
  fr(c, bx - s * 0.2, by + s * 0.0, s * 0.4, s * 0.06, '#e0b04a'); fr(c, bx - s * 0.2, by + s * 0.56, s * 0.4, s * 0.06, '#e0b04a');
  c.strokeStyle = '#e0b04a'; c.lineWidth = 1; c.beginPath(); for (var k = -2; k <= 2; k++) { c.moveTo(bx + k * s * 0.07, by + s * 0.62); c.lineTo(bx + k * s * 0.07 + Math.sin(a) * 2, by + s * 0.82); } c.stroke();
}
/* a roll-up shutter, the Thai shophouse kind: slats, a bottom rail, a padlock */
function shutter(q, x0, x1, y0, y1, col, night) {
  fr(q, x0, y0, x1 - x0, y1 - y0, col);
  q.strokeStyle = night ? 'rgba(0,0,0,.35)' : 'rgba(80,80,90,.35)'; q.lineWidth = 1; q.beginPath();
  for (var y = y0 + 4; y < y1; y += 4) { q.moveTo(x0, y); q.lineTo(x1, y); } q.stroke();
  fr(q, x0, y1 - 5, x1 - x0, 5, night ? '#4a4a55' : '#8a8a96'); fr(q, (x0 + x1) / 2 - 3, y1 - 9, 6, 6, '#c9a24a');
}
/* the street's name on a blue plate on a post */
function roadPlate(q, x, y, s, road) {
  var t = /^(ถ\.|ถนน|ซอย|ซ\.)/.test(road) ? road : 'ถ.' + road;
  fr(q, x - 1.5, y - s * 1.25, 3, s * 1.25, '#8a8a96');
  q.font = '700 ' + Math.round(Math.max(9, s * 0.15)) + 'px "Sarabun",system-ui,sans-serif'; var w = q.measureText(t).width + s * 0.2;
  fr(q, x - w / 2, y - s * 1.45, w, s * 0.24, '#1f4f9a'); q.strokeStyle = '#f2f2f2'; q.lineWidth = 1; q.strokeRect(x - w / 2 + 2, y - s * 1.45 + 2, w - 4, s * 0.24 - 4);
  q.fillStyle = '#ffffff'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText(t, x, y - s * 1.33);
}
/* plants: a frangipani on a forked trunk, a bougainvillea spill, a banana's split leaves */
function frangipani(q, x, y, s, night) {
  var bark = night ? '#5a4a40' : '#8a7462';
  ln(q, [[x, y], [x, y - s * 0.6], [x - s * 0.3, y - s * 1.0]], bark, Math.max(2, s * 0.07)); ln(q, [[x, y - s * 0.6], [x + s * 0.28, y - s * 1.05]], bark, Math.max(2, s * 0.06)); ln(q, [[x - s * 0.15, y - s * 0.8], [x - s * 0.05, y - s * 1.15]], bark, Math.max(1.5, s * 0.045));
  [[-0.3, -1.0], [0.28, -1.05], [-0.05, -1.15]].forEach(function (p, i) {
    var cx = x + p[0] * s, cy = y + p[1] * s;
    for (var k = 0; k < 6; k++) { var a = k / 6 * TAU + i; fe(q, cx + Math.cos(a) * s * 0.13, cy + Math.sin(a) * s * 0.06, s * 0.15, s * 0.045, a, night ? '#2c4a34' : '#3f7a48'); }
    for (k = 0; k < 4; k++) { var bx = cx + (k - 1.5) * s * 0.07, by = cy - s * 0.04 + (k % 2) * s * 0.04; for (var j = 0; j < 5; j++) { var b = j / 5 * TAU; fe(q, bx + Math.cos(b) * s * 0.025, by + Math.sin(b) * s * 0.025, s * 0.03, s * 0.016, b, night ? '#d8d2c0' : '#fffaf0'); } fc(q, bx, by, s * 0.014, '#f2c94c'); }
  });
}
function bougainvillea(q, x0, x1, y, s, r, night) {
  for (var i = 0; i < 26; i++) { var u = r(), x = lerp(x0, x1, u), dy = r() * s * (0.15 + 0.35 * Math.sin(u * Math.PI));
    fc(q, x, y + dy, s * (0.04 + r() * 0.03), i % 4 ? (night ? '#8a2a5a' : '#d9348a') : (night ? '#2c4a34' : '#3f7a48')); }
}
function banana(q, x, y, s, night) {
  ln(q, [[x, y], [x, y - s * 0.7]], night ? '#3a5a34' : '#6a9a4a', Math.max(2, s * 0.06));
  [[-1, 0.7], [1, 0.65], [-0.6, 0.95], [0.7, 0.9]].forEach(function (p) {
    var ex = x + p[0] * s * 0.45, ey = y - s * p[1] - s * 0.1;
    q.fillStyle = night ? '#2f5a34' : '#5aa04a'; q.beginPath(); q.moveTo(x, y - s * 0.65); q.quadraticCurveTo((x + ex) / 2, ey - s * 0.25, ex, ey + s * 0.1); q.quadraticCurveTo((x + ex) / 2, ey + s * 0.05, x, y - s * 0.6); q.fill();
  });
}

/* a shelf of skincare: bottles, jars and pumps in soft colours with gold caps, no labels */
function bottles(q, x0, x1, y, s, r) {
  fr(q, x0, y, x1 - x0, s * 0.04, '#b9a37a');
  var cols = ['#f2c1cc', '#fbf7f4', '#cfe0ea', '#e7a3b3', '#f2e6c9', '#c9a0c8', '#9fcfc4'];
  for (var x = x0 + s * 0.05; x < x1 - s * 0.06; x += s * (0.1 + r() * 0.05)) {
    var k = Math.floor(r() * 3), h = s * (0.12 + r() * 0.12), w = s * (0.05 + r() * 0.04), col = cols[Math.floor(r() * cols.length)];
    if (k === 0) { fr(q, x, y - h, w, h, col); fr(q, x + w * 0.25, y - h - s * 0.03, w * 0.5, s * 0.03, '#d4a23f'); }
    else if (k === 1) { fr(q, x, y - h * 0.5, w * 1.3, h * 0.5, col); fr(q, x - 1, y - h * 0.5 - s * 0.025, w * 1.3 + 2, s * 0.025, '#d4a23f'); }
    else { fr(q, x, y - h, w, h, col); fr(q, x + w * 0.4, y - h - s * 0.05, w * 0.2, s * 0.05, '#d4a23f'); fr(q, x + w * 0.4, y - h - s * 0.05, w * 0.6, s * 0.015, '#d4a23f'); }
  }
}

/* ---------------------------------------------------------------- creatures for the quiet hours
   a cat asleep, curled, breathing r = r₀(1 + 0.04·sin 2πt/3.2), the tail tip flicking */
function cat(c, x, y, s, t, col) {
  var b = 1 + 0.04 * Math.sin(t / 3200 * TAU);
  fe(c, x, y - s * 0.09 * b, s * 0.2, s * 0.1 * b, 0, col);
  fc(c, x + s * 0.16, y - s * 0.1, s * 0.075, col);
  fp(c, [[x + s * 0.12, y - s * 0.15], [x + s * 0.14, y - s * 0.22], [x + s * 0.17, y - s * 0.16]], col); fp(c, [[x + s * 0.18, y - s * 0.16], [x + s * 0.22, y - s * 0.22], [x + s * 0.23, y - s * 0.14]], col);
  ln(c, [[x + s * 0.15, y - s * 0.1], [x + s * 0.19, y - s * 0.1]], 'rgba(30,20,20,.7)', 1);
  var fl = Math.sin(t / 900) > 0.6 ? Math.sin(t / 120) * 0.3 : 0;
  c.strokeStyle = col; c.lineWidth = Math.max(2, s * 0.04); c.lineCap = 'round'; c.beginPath(); c.moveTo(x - s * 0.18, y - s * 0.05); c.quadraticCurveTo(x - s * 0.1, y + s * 0.03, x + s * 0.05, y - s * 0.01 + fl * s * 0.1); c.stroke();
}
/* a moth round a lamp on a figure-eight, x = a·sin ωt, y = ½a·sin 2ωt */
function moth(c, x, y, s, t) {
  var w = t / 700, mx = x + Math.sin(w) * s * 0.3, my = y + Math.sin(2 * w) * s * 0.12, f = 0.5 + 0.5 * Math.abs(Math.sin(t / 40));
  fe(c, mx - s * 0.03, my, s * 0.04 * f, s * 0.025, -0.4, 'rgba(240,230,210,.9)'); fe(c, mx + s * 0.03, my, s * 0.04 * f, s * 0.025, 0.4, 'rgba(240,230,210,.9)');
}
/* a jing-jok gecko on the wall by the lamp, its tail swinging θ = 0.3·sin(2πt/2.4) */
function gecko(c, x, y, s, t) {
  var a = 0.3 * Math.sin(t / 2400 * TAU), col = '#c9b48a';
  fe(c, x, y, s * 0.025, s * 0.07, 0, col); fc(c, x, y - s * 0.08, s * 0.025, col);
  ln(c, [[x, y + s * 0.06], [x + Math.sin(a) * s * 0.06, y + s * 0.14]], col, Math.max(1, s * 0.018));
  [[-1, -0.03], [1, -0.03], [-1, 0.04], [1, 0.04]].forEach(function (p) { ln(c, [[x, y + p[1] * s], [x + p[0] * s * 0.04, y + p[1] * s - s * 0.02]], col, 1); });
}

/* ---------------------------------------------------------------- people
   an arm that reaches a point: two bones, the elbow by the law of cosines */
function solve(s, T, l1, l2, dir) {
  var vx = dir * (T[0] - s[0]), vy = T[1] - s[1], d = Math.min(Math.sqrt(vx * vx + vy * vy), l1 + l2 - 0.01), at = Math.atan2(vx, vy);
  var al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * Math.max(d, 0.01)), -1, 1)), up = at - al;
  return [up, Math.atan2(vx - Math.sin(up) * l1, vy - Math.cos(up) * l1) - up];
}
function shoulder(x, y, h, P, dir) { var hip = [x, y - h * (P.seat || 0.47)], l = P.lean || 0; return [hip[0] + dir * Math.sin(l) * h * 0.33, hip[1] - Math.cos(l) * h * 0.33]; }
function reach(x, y, h, P, dir, hA, hB) {
  var sh = shoulder(x, y, h, P, dir), arms = P.arms.slice(), a;
  if (hA) { a = solve(sh, hA, h * 0.17, h * 0.16, dir); arms[0] = a[0]; arms[1] = a[1]; }
  if (hB) { a = solve(sh, hB, h * 0.17, h * 0.16, dir); arms[2] = a[0]; arms[3] = a[1]; }
  return { lean: P.lean || 0, seat: P.seat || 0.47, lift: P.lift || 0, legs: P.legs, arms: arms };
}
var STAND = K.POSE.stand, WAI = { lean: 0.06, legs: [0.04, 0, -0.04, 0], arms: [0.9, 1.6, 0.8, 1.7] };
/* clinic whites with rose accents: the doctor in a long coat with a stethoscope, the nurse in a
   tunic with a rose collar */
function staff(r, kind) {
  var d = { garb: 'casual', long: true, col: '#f8f6f4', low: kind === 'doc' ? '#3a3f55' : r() < 0.5 ? '#f8f6f4' : '#e7a3b3', dir: 1,
    skin: K.SKIN[Math.floor(r() * K.SKIN.length)], hair: [2, 3, 1, 0][Math.floor(r() * 4)], hairCol: r() < 0.12 ? '#8a8a8a' : '#1c1410', kind: kind };
  return d;
}
function whites(c, J, h, d) {
  var dir = d.dir || 1, hip = J.hip, sh = J.sh;
  if (d.kind === 'doc') {
    fp(c, [[hip[0] - h * 0.085, hip[1] - h * 0.04], [hip[0] + h * 0.085, hip[1] - h * 0.04], [hip[0] + h * 0.1, hip[1] + h * 0.2], [hip[0] - h * 0.1, hip[1] + h * 0.2]], '#f8f6f4');
    ln(c, [[sh[0] - h * 0.03, sh[1]], [sh[0], sh[1] + h * 0.09], [sh[0] + h * 0.03, sh[1]]], '#2a2a35', Math.max(1, h * 0.012));
    fc(c, sh[0] + dir * h * 0.02, sh[1] + h * 0.1, Math.max(1.2, h * 0.016), '#c9ccd4');
  }
  ln(c, [[sh[0] - h * 0.04, sh[1] - h * 0.01], [sh[0], sh[1] + h * 0.05], [sh[0] + h * 0.04, sh[1] - h * 0.01]], '#d9708e', Math.max(1.2, h * 0.02));
  fr(c, sh[0] + dir * h * 0.02 - h * 0.015, sh[1] + h * 0.07, h * 0.03, h * 0.04, '#d9708e');
}
function body(c, x, y, h, P, d) { var J = K.person(c, x, y, h, P, d); if (d.kind) whites(c, J, h, d); return J; }
/* a towel wrapped round the head, the way a facial starts */
function turban(c, hd, h, col) { fe(c, hd[0], hd[1] - h * 0.045, h * 0.115, h * 0.075, 0, col || '#fbf7f4'); ln(c, [[hd[0] - h * 0.08, hd[1] - h * 0.03], [hd[0] + h * 0.06, hd[1] - h * 0.09]], 'rgba(0,0,0,.12)', 1); }

/* ---------------------------------------------------------------- the layout, dealt from the seed */
function lay(S) {
  var r = K.rnd((S.seed ^ 0x5b17c) >>> 0), hh = S.hh, P = S.place, L = { r: r };
  L.look = lookOf(S, r);
  L.pal = PAL[Math.floor(r() * PAL.length)];
  L.wide = L.look === 'consult' || L.look === 'treat' ? 4.5 + r() * 0.5 : L.look === 'villa' ? 3.4 : 3.3 + r() * 0.8;
  if (S.phone) L.wide = Math.min(L.wide, S.span / hh - 2.4);
  var bw = hh * L.wide, lo = S.x0 + hh * 0.9 + bw / 2, hi = S.x1 - hh * 1.1 - bw / 2;
  if (S.avoid) hi = Math.min(hi, S.avoid.cx - S.avoid.r - bw / 2 + hh * 0.4);
  L.bc = hi > lo ? lerp(lo, hi, 0.25 + r() * 0.5) : (S.x0 + S.x1) / 2;
  if (L.look === 'villa') L.bc = hi > lo ? lerp(lo, hi, r() < 0.5 ? 0.15 : 0.85) : L.bc;
  L.bx0 = L.bc - bw / 2; L.bx1 = L.bc + bw / 2; L.bw = bw;
  L.top = S.deck - hh * 2.25;
  if (S.avoid && L.bx1 > S.avoid.cx - S.avoid.r) L.top = Math.max(L.top, S.avoid.cy + S.avoid.r + 4);
  L.gt = S.deck - hh * 1.5;                 /* the ground floor's top */
  L.awning = r() < 0.4; L.arch = r() < 0.4; L.spirit = r() < 0.78; L.spLeft = r() < 0.5;
  L.scoot = r() < 0.7; L.scootCol = ['#e5567f', '#f2f2f2', '#4d8fd1', '#2a2a2a', '#7fd8ff', '#f2c94c'][Math.floor(r() * 6)];
  L.helmet = r() < 0.6 ? ['#f2c94c', '#e5567f', '#f2f2f2', '#2a2a2a'][Math.floor(r() * 4)] : '';
  L.bloomA = BLOOM[Math.floor(r() * BLOOM.length)]; L.bloomB = BLOOM[Math.floor(r() * BLOOM.length)];
  L.plant = ['frangipani', 'banana', 'bougainvillea', 'orchids'][Math.floor(r() * 4)];
  L.door = L.bc + (r() - 0.5) * bw * 0.35;
  L.lacquer = ['#4a1418', '#1d1416', '#5a2026'][Math.floor(r() * 3)];
  L.dev = ['led', 'mist', 'laser'][Math.floor(r() * 3)]; L.mask = r() < 0.5;
  L.flip = r() < 0.5; L.mirrorRoom = r() < 0.5;
  L.khomCol = ['#d9342b', '#f2e6c9', '#e5567f', '#f2c94c'][Math.floor(r() * 4)];
  L.catCol = ['#e8a65a', '#2a2a2a', '#f2ede4', '#8a7a6a'][Math.floor(r() * 4)];
  L.clients = 1 + Math.floor(r() * 2);
  L.facade = FACADES[Math.floor(r() * FACADES.length)];
  if (P && P.oldCity && r() < 0.6) L.facade = 'brick';
  var vw = Math.floor(r() * 4);
  L.villa = { wall: ['#8a5530', '#a0683a', '#6e4226', '#efe6d6'][vw], white: vw === 3, roof: ['#8a3a2a', '#5e3820', '#3f5a4a', '#a8432f'][Math.floor(r() * 4)], shutter: ['#5e3820', '#3f7a58', '#2c3e6b', '#8a3a2a'][Math.floor(r() * 4)] };
  if (P && P.hills && r() < 0.6) L.facade = 'teak';
  if (S.phone && L.look !== 'mall') L.scoot = L.scoot && L.wide < 3.6;
  return L;
}
function stateOf(S) {
  if (!S.place) return 'open';
  var o = K.openNow(S.place.hours, S.now);
  return o === true ? 'open' : o === false ? 'closed' : S.night ? 'quiet' : 'open';
}

/* ---------------------------------------------------------------- the street in front */
function street(q, S, L, green) {
  var hh = S.hh, n = S.night;
  K.ground(q, S.x0, S.x1, S.deck, S.H, green ? (n ? '#1f3326' : '#6a9a5a') : (n ? '#2e2f3c' : '#7a7a82'));
  if (!green) {
    fr(q, S.x0 - 4, S.deck, S.span + 8, hh * 0.16, n ? '#55536a' : '#e6ddd0');
    fr(q, S.x0 - 4, S.deck + hh * 0.16, S.span + 8, 2, n ? '#3a3a48' : '#b9ad9c');
    q.fillStyle = n ? 'rgba(240,240,200,.35)' : 'rgba(255,255,255,.7)';
    for (var x = S.x0 + 10; x < S.x1; x += hh * 0.9) q.fillRect(x, S.deck + (S.H - S.deck) * 0.66, hh * 0.45, 2);
  }
}
/* the things on the pavement: the spirit house, the scooter, the street's plate, a plant */
function pavement(q, S, L) {
  var hh = S.hh, P = S.place || {}, y = S.deck + hh * 0.1, out = {};
  var leftX = L.bx0 - hh * 0.45, rightX = L.bx1 + hh * 0.45;
  if (L.spirit) { var sx = L.spLeft ? leftX : rightX; if (sx > S.x0 + hh * 0.3 && sx < S.x1 - hh * 0.3) out.inc = spiritHouse(q, sx, y, hh * 0.78, S.night); }
  if (L.scoot) { var cx = L.spLeft ? rightX + hh * 0.35 : leftX - hh * 0.35; if (cx > S.x0 + hh * 0.6 && cx < S.x1 - hh * 0.9) scooter(q, cx, y + hh * 0.05, hh * 0.95, L.scootCol, L.spLeft ? -1 : 1, L.helmet); }
  if (P.road) roadPlate(q, L.spLeft ? Math.min(S.x1 - hh * 0.9, rightX + hh * 1.15) : Math.max(S.x0 + hh * 0.9, leftX - hh * 1.15), y, hh, P.road);
  return out;
}

/* ---------------------------------------------------------------- the upper floor, five ways
   plaster with windows, teak boards with lattice under a tile eave, old-city brick with green
   shutters, pastel with a balcony of bougainvillea, glass between gold fins; the name on it */
var FACADES = ['render', 'teak', 'brick', 'pastel', 'glass'];
function upper(q, S, L, st) {
  var hh = S.hh, n = S.night, pal = L.pal, x0 = L.bx0, x1 = L.bx1, y0 = L.top + hh * 0.09, y1 = L.gt - hh * 0.12, k = L.facade, lit = n && st !== 'closed';
  var wy = y0 + hh * 0.08, wh = y1 - wy - hh * 0.08, ww = hh * 0.4, xs = [x0 + hh * 0.18, x1 - hh * 0.18 - ww];
  function pane(x, col) { fr(q, x, wy, ww, wh, col); if (lit) glow(q, x + ww / 2, wy + wh / 2, ww, 38, 0.35); }
  if (k === 'teak') {
    fr(q, x0, y0, x1 - x0, y1 - y0, n ? '#4a2e1c' : '#8a5530');
    q.strokeStyle = 'rgba(0,0,0,.2)'; q.lineWidth = 1; q.beginPath(); for (var x = x0 + hh * 0.08; x < x1; x += hh * 0.09) { q.moveTo(x, y0); q.lineTo(x, y1); } q.stroke();
    xs.forEach(function (x) { pane(x, n ? '#ffd9a0' : '#f2dcb0'); q.strokeStyle = n ? '#33201a' : '#5e3820'; q.lineWidth = 1.2; q.beginPath();
      for (var a = 1; a < 4; a++) { q.moveTo(x + ww * a / 4, wy); q.lineTo(x + ww * a / 4, wy + wh); q.moveTo(x, wy + wh * a / 4); q.lineTo(x + ww, wy + wh * a / 4); } q.stroke(); q.strokeStyle = '#e0b04a'; q.strokeRect(x, wy, ww, wh); });
    var ry = L.top - hh * 0.03; fp(q, [[x0 - hh * 0.12, ry + hh * 0.16], [x0 + hh * 0.05, ry], [x1 - hh * 0.05, ry], [x1 + hh * 0.12, ry + hh * 0.16]], n ? '#4a2420' : '#9a3a2a');
    q.fillStyle = n ? '#3a1a18' : '#7a2a20'; for (x = x0 - hh * 0.08; x < x1 + hh * 0.1; x += hh * 0.12) { q.beginPath(); q.arc(x, ry + hh * 0.16, hh * 0.05, 0, Math.PI); q.fill(); }
    fr(q, x0 - hh * 0.12, ry + hh * 0.15, x1 - x0 + hh * 0.24, 1.6, '#e0b04a');
  } else if (k === 'brick') {
    fr(q, x0, y0, x1 - x0, y1 - y0, n ? '#5a2a20' : '#a8503a');
    q.strokeStyle = n ? 'rgba(0,0,0,.25)' : 'rgba(255,230,210,.35)'; q.lineWidth = 1; q.beginPath();
    for (var r = 0, y = y0 + hh * 0.06; y < y1; y += hh * 0.06, r++) { q.moveTo(x0, y); q.lineTo(x1, y); for (x = x0 + (r % 2 ? hh * 0.07 : 0); x < x1; x += hh * 0.14) { q.moveTo(x, y); q.lineTo(x, y - hh * 0.06); } } q.stroke();
    xs.forEach(function (x) { fr(q, x - 2, wy - 2, ww + 4, wh + 4, '#f2ede4'); pane(x, n ? '#ffd9a0' : '#cfe3ea'); fr(q, x - hh * 0.12, wy, hh * 0.1, wh, n ? '#24402e' : '#3f7a58'); fr(q, x + ww + hh * 0.02, wy, hh * 0.1, wh, n ? '#24402e' : '#3f7a58'); });
  } else if (k === 'pastel') {
    fr(q, x0, y0, x1 - x0, y1 - y0, n ? mixc(pal.rose, '#22234a', 0.5) : mixc(pal.rose, '#ffffff', 0.45));
    xs.forEach(function (x) { fr(q, x - 2, wy - 2, ww + 4, wh + 4, '#fbf7f4'); pane(x, n ? '#ffd9a0' : '#cfe3ea'); ln(q, [[x + ww / 2, wy], [x + ww / 2, wy + wh]], '#fbf7f4', 1.4); });
    fr(q, x0 + hh * 0.08, y1 - hh * 0.2, x1 - x0 - hh * 0.16, hh * 0.03, '#fbf7f4'); for (x = x0 + hh * 0.1; x < x1 - hh * 0.08; x += hh * 0.08) fr(q, x, y1 - hh * 0.2, 1.4, hh * 0.2, '#fbf7f4');
    bougainvillea(q, x0 + hh * 0.05, x0 + hh * 0.7, y1 - hh * 0.2, hh * 0.45, K.rnd(S.seed + 4), n); bougainvillea(q, x1 - hh * 0.7, x1 - hh * 0.05, y1 - hh * 0.2, hh * 0.45, K.rnd(S.seed + 6), n);
  } else if (k === 'glass') {
    var g = q.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, n ? '#2a3a5a' : '#a9cde0'); g.addColorStop(0.5, n ? '#3a4a6a' : '#d8ecf4'); g.addColorStop(1, n ? '#22304a' : '#8ab8d0');
    q.fillStyle = g; q.fillRect(x0, y0, x1 - x0, y1 - y0);
    if (lit) for (x = x0 + hh * 0.12; x < x1 - hh * 0.2; x += hh * 0.5) fr(q, x, y0 + hh * 0.1, hh * 0.3, y1 - y0 - hh * 0.2, 'rgba(255,214,150,.45)');
    q.fillStyle = 'rgba(255,255,255,.25)'; for (x = x0 + hh * 0.2; x < x1; x += hh * 0.9) fp(q, [[x, y0], [x + hh * 0.18, y0], [x - hh * 0.1, y1], [x - hh * 0.28, y1]], 'rgba(255,255,255,.22)');
    for (x = x0 + hh * 0.06; x < x1; x += hh * 0.25) fr(q, x, y0, 2, y1 - y0, '#d4a23f');
  } else {
    xs.forEach(function (x) {
      var cw = n ? '#f2d9a0' : '#cfe3ea';
      if (L.arch) { q.fillStyle = cw; q.beginPath(); q.moveTo(x, wy + wh); q.lineTo(x, wy + ww * 0.5); q.quadraticCurveTo(x + ww / 2, wy - ww * 0.2, x + ww, wy + ww * 0.5); q.lineTo(x + ww, wy + wh); q.closePath(); q.fill(); if (lit) glow(q, x + ww / 2, wy + wh / 2, ww, 38, 0.35); }
      else pane(x, cw);
      q.strokeStyle = '#d4a23f'; q.lineWidth = 1.4; q.strokeRect(x, wy + (L.arch ? ww * 0.5 : 0), ww, wh - (L.arch ? ww * 0.5 : 0));
      ln(q, [[x + ww / 2, wy + (L.arch ? ww * 0.1 : 0)], [x + ww / 2, wy + wh]], '#d4a23f', 1);
    });
  }
  if (S.place) plate(q, L.bc, L.top + hh * 0.2, S.place, hh, n ? '#5a2a3a' : pal.deep, st === 'open' || n, L.bw - hh * 0.95);
  else K.banner(q, L.bc, L.top + hh * 0.18, S.label, hh, pal.deep, S.seed, []);
}

/* the treatment chair, a client reclined in it, a towel round her head, the light on its arm
   above her face (its glow is drawn each frame); returns where the light is */
function recliner(q, mid, fy, hh, on, pal, cl) {
  fp(q, [[mid - hh * 0.4, fy - hh * 0.36], [mid + hh * 0.1, fy - hh * 0.36], [mid + hh * 0.36, fy - hh * 0.62], [mid + hh * 0.42, fy - hh * 0.58], [mid + hh * 0.16, fy - hh * 0.28], [mid - hh * 0.4, fy - hh * 0.28]], on ? pal.deep : '#5a4a6a');
  fr(q, mid - hh * 0.05, fy - hh * 0.28, hh * 0.08, hh * 0.24, '#b9bcc6'); fr(q, mid - hh * 0.2, fy - hh * 0.06, hh * 0.38, hh * 0.04, '#b9bcc6');
  if (on) { cl = cl || {};
    q.lineCap = 'round'; ln(q, [[mid + hh * 0.06, fy - hh * 0.42], [mid - hh * 0.36, fy - hh * 0.42]], cl.low || '#2c2f45', hh * 0.08);
    ln(q, [[mid + hh * 0.06, fy - hh * 0.42], [mid + hh * 0.28, fy - hh * 0.6]], cl.col || '#f2c1cc', hh * 0.13);
    fc(q, mid + hh * 0.37, fy - hh * 0.69, hh * 0.085, cl.skin || '#e3b08a'); fe(q, mid + hh * 0.42, fy - hh * 0.74, hh * 0.08, hh * 0.06, 0.5, '#fbf7f4');
    fe(q, mid + hh * 0.33, fy - hh * 0.72, hh * 0.05, hh * 0.035, -0.6, 'rgba(255,255,255,.95)'); }
  ln(q, [[mid + hh * 0.5, fy - hh * 1.25], [mid + hh * 0.5, fy - hh * 1.0], [mid + hh * 0.3, fy - hh * 0.9]], '#9a9aa6', Math.max(1.4, hh * 0.025));
  fe(q, mid + hh * 0.3, fy - hh * 0.88, hh * 0.14, hh * 0.05, -0.5, '#e8e4ee');
  return on ? [mid + hh * 0.33, fy - hh * 0.8] : null;
}

/* ---------------------------------------------------------------- look 1: the shophouse front
   white and rose, the name on the upper façade, frosted glass with a face drawn on it, the
   treatment chair seen through the clear pane, orchids at the door */
function frontBack(q, S, L, st) {
  var hh = S.hh, n = S.night, pal = L.pal, wall = n ? mixc(pal.wall, '#22234a', 0.55) : pal.wall, rose = n ? mixc(pal.rose, '#22234a', 0.45) : pal.rose;
  var lit = st === 'open' && n, on = st === 'open';
  paper(q, rect(L.bx0, L.top, L.bw, S.deck - L.top), wall, 1.6);
  laiBand(q, L.bx0, L.bx1, L.top, hh * 0.09, n ? '#5a3a2a' : pal.deep);
  upper(q, S, L, st);
  /* the fascia, and an awning on some */
  fr(q, L.bx0, L.gt - hh * 0.12, L.bw, hh * 0.12, rose);
  laiBand(q, L.bx0 + hh * 0.05, L.bx1 - hh * 0.05, L.gt - hh * 0.1, hh * 0.08, null);
  /* the ground floor: pilasters, glass, the doorway */
  var gx0 = L.bx0 + hh * 0.12, gx1 = L.bx1 - hh * 0.12, dw = hh * 0.62, dx0 = clamp(L.door - dw / 2, gx0 + hh * 0.5, gx1 - hh * 0.5 - dw), dx1 = dx0 + dw;
  L.dx0 = dx0; L.dx1 = dx1; L.dtop = S.deck - hh * 1.12;
  fr(q, L.bx0, L.gt, hh * 0.12, S.deck - L.gt, rose); fr(q, L.bx1 - hh * 0.12, L.gt, hh * 0.12, S.deck - L.gt, rose);
  if (st === 'open' || st === 'quiet') {
    var glassTop = L.gt + hh * (L.awning ? 0.24 : 0.02);
    /* the room behind the glass: warm wall, a treatment chair under its lamp */
    fr(q, gx0, L.gt, gx1 - gx0, S.deck - L.gt, on ? (n ? '#ffe6c8' : pal.room) : '#3a3550');
    var wide = dx0 - gx0 > gx1 - dx1, cx0 = wide ? gx0 : dx1, cx1 = wide ? dx0 : gx1, mid = (cx0 + cx1) / 2, fy = S.deck;
    L.pane = [cx0, cx1];
    if (cx1 - cx0 > hh * 0.8) {
      /* the treatment chair seen through the clear pane, a client reclined in it under the light */
      if (on) glow(q, mid, fy - hh * 0.75, hh * 0.9, 35, n ? 0.6 : 0.3);
      bottles(q, cx0 + hh * 0.12, cx1 - hh * 0.12, L.gt + hh * 0.42, hh, K.rnd(S.seed + 23));
      L.led = recliner(q, mid, fy, hh, on, pal, L.cl);
      orchid(q, wide ? cx0 + hh * 0.22 : cx1 - hh * 0.22, fy - hh * 0.04, hh * 0.5, L.bloomB, wide ? 1 : -1);
    }
    /* the frosted side, a face drawn on it */
    var fx0 = wide ? dx1 : gx0, fx1 = wide ? gx1 : dx0, fw = fx1 - fx0;
    q.fillStyle = on ? 'rgba(255,250,252,.72)' : 'rgba(40,40,70,.5)'; q.fillRect(fx0, glassTop, fw, S.deck - glassTop);
    q.fillStyle = on ? 'rgba(255,250,252,.18)' : 'rgba(40,40,70,.25)'; q.fillRect(cx0, glassTop, cx1 - cx0, S.deck - glassTop);
    if (fw > hh * 0.45) face(q, (fx0 + fx1) / 2 + fw * 0.06, S.deck - hh * 0.74, Math.min(hh * 0.62, fw * 1.1), on ? pal.deep : '#9a8ab0', Math.max(1.4, hh * 0.03));
    fr(q, gx0, S.deck - hh * 0.3, gx1 - gx0, 1.4, '#d4a23f');
    q.strokeStyle = '#d4a23f'; q.lineWidth = 1.6; q.strokeRect(gx0, glassTop, gx1 - gx0, S.deck - glassTop);
    /* the doorway behind its doors */
    fr(q, dx0, L.dtop, dw, S.deck - L.dtop, on ? (n ? '#ffd9a0' : '#fff2e0') : '#2a2840');
    if (on) glow(q, (dx0 + dx1) / 2, S.deck - hh * 0.6, hh * 0.8, 38, n ? 0.7 : 0.35);
  }
  if (st !== 'open') shutter(q, gx0, gx1, L.gt + hh * 0.02, S.deck, n ? '#6a6878' : '#b8b4bc', n);
  if (L.awning) {
    var ay = L.gt + hh * 0.02, ah = hh * 0.22, k = Math.max(4, Math.round(L.bw / (hh * 0.3)));
    fr(q, L.bx0 - hh * 0.06, ay, L.bw + hh * 0.12, ah * 0.6, rose);
    for (var i = 0; i < k; i++) { var x0 = L.bx0 - hh * 0.06 + i * (L.bw + hh * 0.12) / k, w = (L.bw + hh * 0.12) / k; q.fillStyle = i % 2 ? rose : (n ? '#c9c2d0' : '#fdfafa'); q.fillRect(x0, ay, w, ah * 0.6); q.beginPath(); q.arc(x0 + w / 2, ay + ah * 0.6, w / 2, 0, Math.PI); q.fill(); }
  }
  /* orchids at the door; a wall lamp */
  if (st === 'open') { orchid(q, L.dx0 - hh * 0.2, S.deck + hh * 0.06, hh * 0.62, L.bloomA, -1); orchid(q, L.dx1 + hh * 0.2, S.deck + hh * 0.06, hh * 0.62, L.bloomA, 1); }
  L.lamp = [L.dx1 + hh * 0.12, L.gt + hh * 0.35];
  fr(q, L.lamp[0] - 2, L.lamp[1] - hh * 0.06, 4, hh * 0.08, '#d4a23f'); fe(q, L.lamp[0], L.lamp[1] + hh * 0.03, hh * 0.05, hh * 0.04, 0, n ? '#fff2c0' : '#f2e6c9');
  if (n) glow(q, L.lamp[0], L.lamp[1] + hh * 0.03, hh * 0.35, 42, 0.6);
}
/* the moving parts: a client walks to the door, the glass doors part as y = ½h(1 − cos), a
   nurse inside gives a wai, a light sweeps the glass */
function frontLive(S, L, st, crew) {
  var c = S.c, hh = S.hh, t = S.t, dw = L.dx1 - L.dx0, dc = (L.dx0 + L.dx1) / 2;
  if (st !== 'open') return;
  var T = 15000, u = (t % T) / T, fromL = L.flip, xs = fromL ? S.x0 - hh * 0.6 : S.x1 + hh * 0.6, walkEnd = 0.62;
  var open = u < 0.5 ? 0 : u < 0.58 ? cyc((u - 0.5) / 0.08 * 0.5, 1) : u < 0.74 ? 1 : u < 0.82 ? 1 - cyc((u - 0.74) / 0.08 * 0.5, 1) : 0;
  /* inside: the nurse at the door */
  c.save(); c.beginPath(); c.rect(L.dx0, L.dtop, dw, S.deck - L.dtop); c.clip();
  var ns = staff(K.rnd(S.seed + 7), 'nurse'); ns.dir = fromL ? -1 : 1;
  if (open > 0.05) body(c, dc + (fromL ? 1 : -1) * hh * 0.08, S.deck, hh * 0.92, open > 0.6 ? WAI : STAND, ns);
  c.restore();
  /* the doors: two glass leaves sliding apart */
  var lw = dw / 2, off = open * lw * 0.92;
  c.fillStyle = 'rgba(235,245,250,.55)'; c.fillRect(L.dx0 - off, L.dtop, lw, S.deck - L.dtop); c.fillRect(dc + off, L.dtop, lw, S.deck - L.dtop);
  c.strokeStyle = '#d4a23f'; c.lineWidth = 1.2; c.strokeRect(L.dx0 - off, L.dtop, lw, S.deck - L.dtop); c.strokeRect(dc + off, L.dtop, lw, S.deck - L.dtop);
  fr(c, dc - off - 3, S.deck - hh * 0.6, 2, hh * 0.18, '#d4a23f'); fr(c, dc + off + 1, S.deck - hh * 0.6, 2, hh * 0.18, '#d4a23f');
  /* the light over the client's face, red then blue */
  if (L.led) { var m = cyc(t, 10000), bl = clamp((m - 0.35) * 3.3, 0, 1); glow(c, L.led[0], L.led[1] + hh * 0.06, hh * 0.3, 0, 0.8 * (1 - bl)); glow(c, L.led[0], L.led[1] + hh * 0.06, hh * 0.3, 225, 0.8 * bl); }
  /* the light across the glass */
  var sw = ((t / 9000) % 1) * 1.6 - 0.3, gx0 = L.bx0 + hh * 0.12, gx1 = L.bx1 - hh * 0.12, sx = lerp(gx0, gx1, sw);
  c.save(); c.beginPath(); c.rect(gx0, L.gt, gx1 - gx0, S.deck - L.gt); c.clip(); c.fillStyle = 'rgba(255,255,255,.22)';
  c.beginPath(); c.moveTo(sx, L.gt); c.lineTo(sx + hh * 0.25, L.gt); c.lineTo(sx - hh * 0.35, S.deck); c.lineTo(sx - hh * 0.6, S.deck); c.closePath(); c.fill(); c.restore();
  /* the client, walking in; a friend a step behind on some */
  for (var i = 0; i < L.clients; i++) {
    var lag = i * 0.05, v = u - lag, d = crew[i];
    if (v < 0 || v > walkEnd + 0.06) continue;
    var w = Math.min(1, v / walkEnd), x = lerp(xs, dc, w), a = v > walkEnd - 0.02 ? clamp(1 - (v - walkEnd + 0.02) / 0.06, 0, 1) : 1;
    if (a <= 0) continue;
    d.dir = fromL ? 1 : -1;
    c.save(); c.globalAlpha = a; var J = body(c, x, S.deck + hh * 0.08 + i * 3, hh * 0.95, K.walkP(Math.abs(x - xs) / (hh * 0.3), false), d);
    if (i === 0) { var hd = J.hand[1]; fr(c, hd[0] - hh * 0.05, hd[1], hh * 0.1, hh * 0.12, '#f2c1cc'); ln(c, [[hd[0] - hh * 0.03, hd[1]], [hd[0], hd[1] - hh * 0.04], [hd[0] + hh * 0.03, hd[1]]], '#b85b78', 1); }
    c.restore();
  }
}

/* ---------------------------------------------------------------- looks 2 and 3: the room inside
   the front wall cut away: the name above, the room below, the street before it */
function roomShell(q, S, L, st) {
  var hh = S.hh, n = S.night, pal = L.pal, wall = n ? mixc(pal.wall, '#22234a', 0.55) : pal.wall, on = st === 'open';
  paper(q, rect(L.bx0, L.top, L.bw, S.deck - L.top), wall, 1.6);
  laiBand(q, L.bx0, L.bx1, L.top, hh * 0.09, n ? '#5a3a2a' : pal.deep);
  var rx0 = L.bx0 + hh * 0.14, rx1 = L.bx1 - hh * 0.14, ry0 = L.gt;
  L.rx0 = rx0; L.rx1 = rx1; L.ry0 = ry0; L.floor = S.deck - hh * 0.05;
  var back = on ? (n ? mixc(pal.room, '#ffd9a0', 0.35) : pal.room) : (n ? '#2c2a44' : mixc(pal.room, '#9a98a8', 0.4));
  fr(q, rx0, ry0, rx1 - rx0, S.deck - ry0, back);
  fp(q, [[rx0, S.deck - hh * 0.2], [rx1, S.deck - hh * 0.2], [rx1, S.deck], [rx0, S.deck]], on ? (n ? '#e8c9a0' : '#efe3d6') : (n ? '#3a3650' : '#c8bfb6'));
  q.strokeStyle = 'rgba(0,0,0,.08)'; q.lineWidth = 1; q.beginPath(); for (var x = rx0; x < rx1; x += hh * 0.3) { q.moveTo(x, S.deck - hh * 0.2); q.lineTo(x - hh * 0.06, S.deck); } q.stroke();
  fr(q, rx0, S.deck - hh * 0.22, rx1 - rx0, 2, '#d4a23f');
  /* pendant lamps */
  var nl = Math.max(2, Math.round((rx1 - rx0) / (hh * 1.3)));
  L.lamps = [];
  for (var i = 0; i < nl; i++) { var lx = lerp(rx0, rx1, (i + 0.5) / nl); ln(q, [[lx, ry0], [lx, ry0 + hh * 0.18]], '#9a8a7a', 1); fp(q, [[lx - hh * 0.09, ry0 + hh * 0.26], [lx + hh * 0.09, ry0 + hh * 0.26], [lx + hh * 0.04, ry0 + hh * 0.18], [lx - hh * 0.04, ry0 + hh * 0.18]], '#e0b04a');
    if (on) glow(q, lx, ry0 + hh * 0.3, hh * 0.45, 40, n ? 0.6 : 0.35); L.lamps.push([lx, ry0 + hh * 0.26]); }
  return back;
}
function roomFrame(q, S, L, st) {
  var hh = S.hh, n = S.night, pal = L.pal, rose = n ? mixc(pal.rose, '#22234a', 0.45) : pal.rose;
  fr(q, L.bx0, L.gt - hh * 0.12, L.bw, hh * 0.12, rose);
  laiBand(q, L.bx0 + hh * 0.05, L.bx1 - hh * 0.05, L.gt - hh * 0.1, hh * 0.08, null);
  fr(q, L.bx0, L.gt, hh * 0.14, S.deck - L.gt, rose); fr(q, L.bx1 - hh * 0.14, L.gt, hh * 0.14, S.deck - L.gt, rose);
  fr(q, L.bx0 + hh * 0.1, L.gt, 2, S.deck - L.gt, '#d4a23f'); fr(q, L.bx1 - hh * 0.12, L.gt, 2, S.deck - L.gt, '#d4a23f');
  if (st !== 'open') { q.fillStyle = n ? 'rgba(20,20,50,.38)' : 'rgba(60,60,80,.18)'; q.fillRect(L.rx0, L.ry0, L.rx1 - L.rx0, S.deck - L.ry0); }
  if (st === 'closed') shutter(q, L.rx0, L.rx1, L.ry0, L.ry0 + (S.deck - L.ry0) * 0.62, n ? '#6a6878' : '#b8b4bc', n);
  upper(q, S, L, st);
}
/* the room's contents face either way, x → 2·x_c − x */
function mirror(c, L) { if (L.mirrorRoom) { c.translate(2 * L.bc, 0); c.scale(-1, 1); } }
/* consultation: reception and its orchid, the gold panel, the doctor with a tablet, the client
   in the chair before the mirror, the skin-analysis screen */
function consultBack(q, S, L, st) {
  var hh = S.hh, n = S.night, on = st === 'open', W = L.rx1 - L.rx0, X = function (u) { return L.rx0 + W * u; }, fl = L.floor;
  laiKham(q, X(0.03), L.ry0 + hh * 0.34, W * 0.21, hh * 0.56, L.lacquer);
  bottles(q, X(0.4), X(0.58), L.ry0 + hh * 0.62, hh, K.rnd(S.seed + 21));
  /* the mirror: a Lanna arch in a gold frame */
  var mx = X(0.67), mw = hh * 0.5, my0 = fl - hh * 1.12, my1 = fl - hh * 0.42; L.mirror = [mx, my0, mw, my1];
  q.fillStyle = '#d4a23f'; q.beginPath(); q.moveTo(mx - mw / 2 - 3, my1 + 3); q.lineTo(mx - mw / 2 - 3, my0 + mw * 0.4); q.quadraticCurveTo(mx, my0 - mw * 0.45, mx + mw / 2 + 3, my0 + mw * 0.4); q.lineTo(mx + mw / 2 + 3, my1 + 3); q.closePath(); q.fill();
  q.fillStyle = n ? '#5a6a8a' : '#cfe0ea'; q.beginPath(); q.moveTo(mx - mw / 2, my1); q.lineTo(mx - mw / 2, my0 + mw * 0.4); q.quadraticCurveTo(mx, my0 - mw * 0.35, mx + mw / 2, my0 + mw * 0.4); q.lineTo(mx + mw / 2, my1); q.closePath(); q.fill();
  ln(q, [[mx - mw * 0.3, my0 + mw * 0.2], [mx - mw * 0.1, my0 + mw * 0.05]], 'rgba(255,255,255,.6)', 1.4);
  fr(q, mx - mw * 0.7, my1 + 3, mw * 1.4, hh * 0.05, '#d4a23f'); fr(q, mx - mw * 0.6, my1 + 3 + hh * 0.05, hh * 0.04, fl - my1 - hh * 0.06, '#b9a37a'); fr(q, mx + mw * 0.6 - hh * 0.04, my1 + 3 + hh * 0.05, hh * 0.04, fl - my1 - hh * 0.06, '#b9a37a');
  /* the chair before it */
  var cx = X(0.5); L.chair = cx;
  fp(q, [[cx - hh * 0.2, fl - hh * 0.27], [cx + hh * 0.16, fl - hh * 0.27], [cx + hh * 0.16, fl - hh * 0.2], [cx - hh * 0.2, fl - hh * 0.2]], L.pal.deep);
  fp(q, [[cx - hh * 0.26, fl - hh * 0.62], [cx - hh * 0.18, fl - hh * 0.62], [cx - hh * 0.12, fl - hh * 0.25], [cx - hh * 0.22, fl - hh * 0.25]], L.pal.deep);
  fr(q, cx - hh * 0.03, fl - hh * 0.2, hh * 0.05, hh * 0.18, '#b9bcc6'); fr(q, cx - hh * 0.16, fl - hh * 0.03, hh * 0.3, hh * 0.03, '#b9bcc6');
  /* the screen on its arm: a face drawn in light, a grid behind it */
  var sx = X(0.87), sy = L.ry0 + hh * 0.34, sw = Math.min(hh * 0.62, W * 0.2), sh = hh * 0.46; L.screen = [sx - sw / 2, sy, sw, sh];
  ln(q, [[L.rx1, sy + sh * 0.6], [sx + sw * 0.3, sy + sh * 0.6]], '#9a9aa6', 2);
  fr(q, sx - sw / 2 - 3, sy - 3, sw + 6, sh + 6, '#2a2a35'); fr(q, sx - sw / 2, sy, sw, sh, on ? '#10243a' : '#14141c');
  if (on) {
    q.strokeStyle = 'rgba(120,220,255,.18)'; q.lineWidth = 1; q.beginPath();
    for (var gx = sx - sw / 2 + sw / 8; gx < sx + sw / 2; gx += sw / 8) { q.moveTo(gx, sy); q.lineTo(gx, sy + sh); }
    for (var gy = sy + sh / 6; gy < sy + sh; gy += sh / 6) { q.moveTo(sx - sw / 2, gy); q.lineTo(sx + sw / 2, gy); } q.stroke();
    q.strokeStyle = '#7fd8ff'; q.lineWidth = 1.2; q.beginPath(); q.ellipse(sx, sy + sh * 0.5, sw * 0.18, sh * 0.36, 0, 0, TAU); q.stroke();
    q.beginPath(); q.arc(sx - sw * 0.07, sy + sh * 0.42, 1.6, 0, TAU); q.arc(sx + sw * 0.07, sy + sh * 0.42, 1.6, 0, TAU); q.stroke();
    q.beginPath(); q.moveTo(sx - sw * 0.06, sy + sh * 0.68); q.quadraticCurveTo(sx, sy + sh * 0.73, sx + sw * 0.06, sy + sh * 0.68); q.stroke();
    q.beginPath(); q.moveTo(sx, sy + sh * 0.46); q.lineTo(sx - sw * 0.02, sy + sh * 0.58); q.lineTo(sx + sw * 0.02, sy + sh * 0.59); q.stroke();
  }
  /* reception: the counter behind which the receptionist stands, an orchid on top */
  L.desk = [X(0.03), X(0.23)]; L.docX = X(0.35);
  if (on) orchid(q, X(0.2), fl - hh * 0.52, hh * 0.45, L.bloomA, -1);
  orchid(q, X(0.97), fl, hh * 0.6, L.bloomB, -1);
}
function consultLive(S, L, st, crew) {
  var c = S.c, hh = S.hh, t = S.t, fl = L.floor, on = st === 'open';
  var sc = L.screen, sx = sc[0], sy = sc[1], sw = sc[2], sh = sc[3];
  if (!on) { gecko(c, L.rx1 - hh * 0.3, L.ry0 + hh * 0.6 + Math.sin(t / 5000) * hh * 0.05, hh, t); moth(c, L.lamps[0][0], L.lamps[0][1] + hh * 0.1, hh, t); return; }
  /* the receptionist behind the counter, typing */
  var rc = staff(K.rnd(S.seed + 3), 'nurse'); rc.dir = 1;
  var rx = lerp(L.desk[0], L.desk[1], 0.45), tp = Math.sin(t / 160) * 0.12;
  body(c, rx, fl - hh * 0.02, hh * 0.9, { lean: 0.15, legs: STAND.legs, arms: [1.1 + tp, 0.6, 1.0 - tp, 0.7] }, rc);
  fr(c, L.desk[0], fl - hh * 0.5, L.desk[1] - L.desk[0], hh * 0.5, L.pal.deep); fr(c, L.desk[0] - hh * 0.03, fl - hh * 0.53, L.desk[1] - L.desk[0] + hh * 0.06, hh * 0.04, '#e0b04a');
  laiBand(c, L.desk[0] + 2, L.desk[1] - 2, fl - hh * 0.36, hh * 0.08, null);
  /* the scan: a line down the face and back, y = ½h(1 − cos 2πt/T), the cells it passes lit */
  var u = cyc(t, 4200), ly = sy + sh * (0.1 + 0.8 * u);
  glow(c, sx + sw / 2, ly, sw * 0.4, 195, 0.35);
  c.fillStyle = 'rgba(127,216,255,.9)'; c.fillRect(sx + 2, ly - 1, sw - 4, 2);
  for (var k = 0; k < 9; k++) { var px = sx + sw * (0.35 + 0.3 * ((k * 0.618) % 1)), py = sy + sh * (0.2 + 0.6 * ((k * 0.382 + 0.1) % 1)); if (Math.abs(py - ly) < sh * 0.25) fc(c, px, py, 1.6, 'rgba(255,170,200,' + (1 - Math.abs(py - ly) / (sh * 0.25)) + ')'); }
  /* the client in the chair, facing the mirror; her face in it */
  var d = crew[0]; d.dir = 1;
  var bob = Math.sin(t / 3000) * 0.03, J = body(c, L.chair, fl - hh * 0.04, hh * 0.92, { lean: -0.05 + bob, seat: 0.27, legs: [1.5, -1.45, 1.4, -1.5], arms: [0.5, 0.9, 0.4, 1.0] }, d);
  if (S.seed % 3 === 0) turban(c, J.head, hh * 0.92, '#fbf7f4');
  var m = L.mirror; c.save(); c.globalAlpha = 0.5; fc(c, m[0] + m[2] * 0.08, J.head[1] - Math.sin(bob) * 2, hh * 0.085, d.skin); fe(c, m[0] + m[2] * 0.08, J.head[1] + hh * 0.2, hh * 0.11, hh * 0.08, 0, d.col); c.restore();
  /* the doctor behind her, a tablet in one hand, the other showing the mirror: the hand moves on ½(1 − cos 2πt/7) */
  var doc = staff(K.rnd(S.seed + 11), 'doc'), dx = L.docX; doc.dir = 1;
  var pt = cyc(t, 7000), hand = [lerp(dx + hh * 0.22, m[0] - m[2] * 0.3, pt), lerp(fl - hh * 0.5, fl - hh * 0.78, pt)];
  var P = reach(dx, fl, hh * 1.0, STAND, 1, hand, [dx + hh * 0.16, fl - hh * 0.55]);
  var Jd = body(c, dx, fl, hh * 1.0, P, doc);
  fr(c, Jd.hand[1][0] - hh * 0.02, Jd.hand[1][1] - hh * 0.12, hh * 0.1, hh * 0.13, '#2a2a35'); fr(c, Jd.hand[1][0] - hh * 0.01, Jd.hand[1][1] - hh * 0.11, hh * 0.08, hh * 0.11, '#7fd8ff');
}
/* treatment: a bed, a client under a blanket, a nurse at her head with the tool of the day:
   an LED panel turning red to blue, a wand misting, or a laser handpiece and its soft spark */
function treatBack(q, S, L, st) {
  var hh = S.hh, n = S.night, on = st === 'open', W = L.rx1 - L.rx0, X = function (u) { return L.rx0 + W * u; }, fl = L.floor;
  laiKham(q, X(0.36), L.ry0 + hh * 0.3, W * 0.26, hh * 0.42, L.lacquer);
  bottles(q, X(0.7), X(0.94), L.ry0 + hh * 0.55, hh, K.rnd(S.seed + 21));
  /* the shelf of rolled towels */
  var s0 = X(0.03), s1 = X(0.2);
  fr(q, s0, fl - hh * 0.75, s1 - s0, hh * 0.04, '#b9a37a'); fr(q, s0, fl - hh * 0.4, s1 - s0, hh * 0.04, '#b9a37a');
  for (var i = 0; i < 4; i++) { fc(q, s0 + (i + 0.5) * (s1 - s0) / 4, fl - hh * 0.81, hh * 0.055, i % 2 ? '#fbf7f4' : L.pal.rose); fc(q, s0 + (i + 0.5) * (s1 - s0) / 4, fl - hh * 0.46, hh * 0.055, i % 2 ? L.pal.rose : '#fbf7f4'); }
  orchid(q, lerp(s0, s1, 0.5), fl - hh * 0.79, hh * 0.38, L.bloomA, 1);
  /* the bed: head at the right */
  var b1 = X(0.64), b0 = b1 - hh * 1.35, by = fl - hh * 0.46; L.bed = [b0, b1, by];
  fr(q, b0 + hh * 0.06, by + hh * 0.08, hh * 0.05, fl - by - hh * 0.08, '#b9bcc6'); fr(q, b1 - hh * 0.11, by + hh * 0.08, hh * 0.05, fl - by - hh * 0.08, '#b9bcc6');
  fr(q, b0, by, b1 - b0, hh * 0.1, on ? '#f6f2f4' : '#c9c4d0'); fr(q, b0, by + hh * 0.1, b1 - b0, hh * 0.04, L.pal.deep);
  fe(q, b1 - hh * 0.16, by - hh * 0.02, hh * 0.16, hh * 0.05, 0, '#ffffff');
  /* the tool: an LED arm, a laser cart, or the mist bottle on a trolley */
  var tx = X(0.9); L.tool = tx;
  if (L.dev === 'led') {
    fr(q, tx - hh * 0.03, fl - hh * 1.0, hh * 0.06, hh * 1.0, '#b9bcc6'); fr(q, tx - hh * 0.16, fl - hh * 0.04, hh * 0.32, hh * 0.04, '#9a9aa6');
    ln(q, [[tx, fl - hh * 1.0], [b1 - hh * 0.16, by - hh * 0.62]], '#b9bcc6', Math.max(2, hh * 0.04));
  } else if (L.dev === 'laser') {
    fr(q, tx - hh * 0.2, fl - hh * 0.72, hh * 0.4, hh * 0.68, '#f2f0f4'); fr(q, tx - hh * 0.16, fl - hh * 0.68, hh * 0.32, hh * 0.2, on ? '#10243a' : '#14141c');
    if (on) { q.strokeStyle = '#7fd8ff'; q.lineWidth = 1; q.beginPath(); for (var k = 0; k <= 20; k++) { var gx = tx - hh * 0.14 + k * hh * 0.014; k ? q.lineTo(gx, fl - hh * 0.58 - Math.sin(k * 0.8) * hh * 0.04) : q.moveTo(gx, fl - hh * 0.58); } q.stroke(); }
    fc(q, tx - hh * 0.12, fl - hh * 0.06, hh * 0.035, '#2a2a35'); fc(q, tx + hh * 0.12, fl - hh * 0.06, hh * 0.035, '#2a2a35');
  } else {
    fr(q, tx - hh * 0.18, fl - hh * 0.5, hh * 0.36, hh * 0.04, '#d4a23f'); fr(q, tx - hh * 0.02, fl - hh * 0.5, hh * 0.04, hh * 0.46, '#b9a37a');
    fr(q, tx - hh * 0.12, fl - hh * 0.64, hh * 0.08, hh * 0.14, '#cfe0ea'); fr(q, tx + hh * 0.02, fl - hh * 0.6, hh * 0.1, hh * 0.1, '#f2c1cc');
  }
  orchid(q, X(0.98), fl, hh * 0.52, L.bloomB, -1);
}
function treatLive(S, L, st, crew) {
  var c = S.c, hh = S.hh, t = S.t, fl = L.floor, on = st === 'open', b = L.bed, by = b[2];
  var hx0 = b[1] - hh * 0.2, hy = by - hh * 0.07;
  if (on || L.dev === 'led') { /* the LED panel over the face: an arc of cells */
    var px = hx0, py = by - hh * 0.62, m = on ? cyc(t, 10000) : 0, red = on ? 1 - clamp((m - 0.35) * 3.3, 0, 1) : 0, blue = on ? clamp((m - 0.35) * 3.3, 0, 1) : 0;
    if (L.dev === 'led') {
      if (on) { glow(c, px, hy - hh * 0.1, hh * 0.75, 0, 0.7 * red); glow(c, px, hy - hh * 0.1, hh * 0.75, 225, 0.7 * blue); }
      c.fillStyle = '#e8e6ee'; c.beginPath(); c.ellipse(px, py + hh * 0.18, hh * 0.32, hh * 0.22, 0, Math.PI * 1.05, Math.PI * 1.95); c.lineTo(px + hh * 0.26, py + hh * 0.12); c.ellipse(px, py + hh * 0.2, hh * 0.24, hh * 0.14, 0, Math.PI * 1.9, Math.PI * 1.1, true); c.closePath(); c.fill();
      var col = on ? 'rgb(' + Math.round(255 * red + 90 * blue) + ',' + Math.round(70 * red + 120 * blue) + ',' + Math.round(80 * red + 255 * blue) + ')' : '#8a8898';
      for (var k = 0; k < 9; k++) { var a = Math.PI * (1.12 + k * 0.095); fc(c, px + Math.cos(a) * hh * 0.28, py + hh * 0.18 + Math.sin(a) * hh * 0.18, Math.max(1.2, hh * 0.018), col); }
    }
  }
  if (!on) { gecko(c, L.rx0 + hh * 0.3, L.ry0 + hh * 0.5 + Math.sin(t / 5000) * hh * 0.05, hh, t); moth(c, L.lamps[L.lamps.length - 1][0], L.lamps[L.lamps.length - 1][1] + hh * 0.1, hh, t); return; }
  /* the client lying down, face up, the blanket rising with her breath */
  var d = crew[0], br = Math.sin(t / 4200 * TAU) * hh * 0.012, hr = hh * 0.1, fx = b[0] + hh * 0.1;
  fe(c, hx0 + hr * 0.6, hy + hr * 0.2, hr * 1.1, hr * 0.7, 0, '#fbf7f4');
  fc(c, hx0, hy, hr, d.skin);
  fp(c, [[hx0 - hr * 0.35, hy - hr * 0.85], [hx0 - hr * 0.2, hy - hr * 1.3], [hx0 + hr * 0.05, hy - hr * 0.9]], d.skin);
  if (L.mask || L.dev === 'led') { c.fillStyle = 'rgba(255,255,255,.95)'; c.beginPath(); c.arc(hx0, hy, hr * 1.02, Math.PI * 1.02, Math.PI * 1.98); c.closePath(); c.fill(); ln(c, [[hx0 - hr * 0.1, hy - hr * 0.55], [hx0 + hr * 0.3, hy - hr * 0.55]], '#c9b4bc', 1); }
  else ln(c, [[hx0 - hr * 0.05, hy - hr * 0.5], [hx0 + hr * 0.3, hy - hr * 0.45]], '#2a1a12', 1);
  c.fillStyle = L.pal.rose; c.beginPath(); c.moveTo(hx0 - hr * 0.9, by); c.lineTo(hx0 - hr * 0.9, hy - hr * 0.2);
  c.quadraticCurveTo(lerp(fx, hx0, 0.7), hy - hr * 1.1 - br, lerp(fx, hx0, 0.45), hy - hr * 0.5); c.quadraticCurveTo(lerp(fx, hx0, 0.25), hy - hr * 0.9, fx + hr * 0.4, hy - hr * 0.6);
  c.quadraticCurveTo(fx, hy - hr * 1.5, fx - hr * 0.3, hy - hr * 0.3); c.lineTo(fx - hr * 0.3, by); c.closePath(); c.fill();
  ln(c, [[hx0 - hr * 0.9, hy - hr * 0.2], [lerp(fx, hx0, 0.55), hy - hr * 0.75 - br * 0.6]], '#fbf7f4', Math.max(1.5, hh * 0.03));
  /* the nurse at her head */
  var ns = staff(K.rnd(S.seed + 5), 'nurse'), nx = b[1] + hh * 0.28; ns.dir = -1;
  var tip = [hx0 + hh * 0.12, hy - hh * 0.18], wob = Math.sin(t / 900) * hh * 0.04;
  if (L.dev === 'led') { var P0 = reach(nx, fl, hh * 0.95, STAND, -1, [hx0 + hh * 0.14, hy - hh * 0.02], null); body(c, nx, fl, hh * 0.95, P0, ns); return; }
  var hand = [tip[0] + wob, tip[1] + Math.cos(t / 900) * hh * 0.02];
  var P1 = reach(nx, fl, hh * 0.95, { lean: 0.25, legs: STAND.legs, arms: STAND.arms }, -1, hand, [hx0 + hh * 0.12, hy - hh * 0.06]);
  body(c, nx, fl, hh * 0.95, P1, ns);
  var tl = [hand[0] - hh * 0.1, hand[1] + hh * 0.08];
  ln(c, [hand, tl], L.dev === 'laser' ? '#e8e6ee' : '#f2c1cc', Math.max(2.5, hh * 0.05)); fc(c, tl[0], tl[1], Math.max(1.5, hh * 0.022), '#d4a23f');
  if (L.dev === 'laser') {
    c.strokeStyle = '#9a9aa6'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(hand[0], hand[1]); c.quadraticCurveTo(nx + hh * 0.1, fl - hh * 0.2, L.tool - hh * 0.1, fl - hh * 0.5); c.stroke();
    var tw = 0.5 + 0.5 * Math.sin(t / 130);
    glow(c, tl[0], tl[1], hh * 0.12, 330, 0.5 + 0.3 * tw);
    for (var s = 0; s < 4; s++) { var a2 = s / 4 * TAU + t / 700; spark(c, tl[0] + Math.cos(a2) * hh * 0.06, tl[1] + Math.sin(a2) * hh * 0.04, hh * 0.012 * (0.6 + tw), 'rgba(255,240,250,.9)'); }
  } else {
    /* the mist: drops on x = x₀ + vt, fading as 1 − u */
    glow(c, tl[0] - hh * 0.1, tl[1] + hh * 0.05, hh * 0.16, 200, 0.35);
    for (var i = 0; i < 22; i++) { var u = ((t / 1100) + i / 22) % 1, sp = ((i * 0.618) % 1 - 0.5) * 1.1;
      c.fillStyle = 'rgba(230,246,255,' + (0.95 * (1 - u)) + ')'; c.beginPath(); c.arc(tl[0] - u * hh * 0.28, tl[1] + u * hh * 0.12 + sp * u * hh * 0.2, Math.max(1, hh * 0.014 * (1 + u)), 0, TAU); c.fill(); }
  }
}

/* ---------------------------------------------------------------- look 4: the Lanna villa in a garden
   a teak house on posts, a kalae gable, a lotus pond, khom along the eave, the nurse with towels */
function villaBack(q, S, L, st) {
  var hh = S.hh, n = S.night, on = st === 'open', V = L.villa, x0 = L.bx0, x1 = L.bx1, fy = S.deck - hh * 0.62, wy = S.deck - hh * 1.42, w = x1 - x0;
  var teak = n ? mixc(V.wall, '#1c1d3a', 0.5) : V.wall, dark = n ? '#33201a' : '#5e3820', roofC = n ? mixc(V.roof, '#1c1d3a', 0.45) : V.roof;
  /* posts and the floor */
  for (var i = 0; i < 5; i++) fr(q, lerp(x0 + hh * 0.08, x1 - hh * 0.14, i / 4), fy, hh * 0.07, S.deck - fy, dark);
  fr(q, x0 - hh * 0.05, fy - hh * 0.06, w + hh * 0.1, hh * 0.08, dark);
  /* the walls: boards (or whitewash with teak frames), two lit windows with shutters */
  var wx0 = L.flip ? x0 + w * 0.3 : x0 + hh * 0.05, wx1 = L.flip ? x1 - hh * 0.05 : x0 + w * 0.7, ww = wx1 - wx0;
  paper(q, rect(wx0, wy, ww, fy - wy), teak, 1.4);
  if (V.white) { fr(q, wx0, wy, ww, hh * 0.05, dark); fr(q, wx0, fy - hh * 0.05, ww, hh * 0.05, dark); for (var x = wx0; x <= wx1; x += ww / 3) fr(q, x - 1.5, wy, 3, fy - wy, dark); }
  else { q.strokeStyle = 'rgba(0,0,0,.18)'; q.lineWidth = 1; q.beginPath(); for (x = wx0 + hh * 0.07; x < wx1; x += hh * 0.09) { q.moveTo(x, wy); q.lineTo(x, fy); } q.stroke(); }
  [0.2, 0.62].forEach(function (u) { var wx = wx0 + ww * u; fr(q, wx, wy + hh * 0.18, hh * 0.32, hh * 0.38, on || n ? '#ffd9a0' : '#3a2a20'); if (on || n) glow(q, wx + hh * 0.16, wy + hh * 0.37, hh * 0.4, 38, n ? 0.6 : 0.25);
    fr(q, wx - hh * 0.12, wy + hh * 0.18, hh * 0.12, hh * 0.38, V.shutter); fr(q, wx + hh * 0.32, wy + hh * 0.18, hh * 0.12, hh * 0.38, V.shutter); q.strokeStyle = '#e0b04a'; q.lineWidth = 1; q.strokeRect(wx, wy + hh * 0.18, hh * 0.32, hh * 0.38); });
  /* the veranda: rail, steps down from its open end */
  var vx0 = L.flip ? x0 : x0 + w * 0.72, vx1 = L.flip ? x0 + w * 0.28 : x1, sd = L.flip ? -1 : 1, se = L.flip ? vx0 : vx1;
  L.ver = [vx0, vx1, fy]; L.steps = se + sd * hh * 0.3;
  fr(q, vx0, fy - hh * 0.3, vx1 - vx0, hh * 0.04, dark); for (x = vx0; x <= vx1; x += hh * 0.1) fr(q, x, fy - hh * 0.3, 2, hh * 0.3, dark);
  ln(q, [[se, fy], [se + sd * hh * 0.5, S.deck]], dark, Math.max(2, hh * 0.04));
  for (i = 0; i < 4; i++) fr(q, se + sd * (hh * 0.02 + i * hh * 0.11) - (sd < 0 ? hh * 0.24 : 0), fy + i * hh * 0.155, hh * 0.24, hh * 0.05, dark);
  /* the roof in two tiers, kalae crossed at the gable */
  var r0 = wy - hh * 0.04, peak = L.top + hh * 0.12;
  paper(q, poly([[x0 - hh * 0.3, r0 + hh * 0.08], [x0 + w * 0.15, lerp(r0, peak, 0.5)], [x1 - w * 0.15, lerp(r0, peak, 0.5)], [x1 + hh * 0.3, r0 + hh * 0.08]]), roofC, 1.6);
  paper(q, poly([[x0 + w * 0.08, lerp(r0, peak, 0.52)], [(x0 + x1) / 2, peak], [x1 - w * 0.08, lerp(r0, peak, 0.52)]]), roofC, 1.8);
  fp(q, [[x0 + w * 0.3, lerp(r0, peak, 0.55)], [(x0 + x1) / 2, peak + hh * 0.12], [x1 - w * 0.3, lerp(r0, peak, 0.55)]], '#c9973f');
  laiBand(q, x0 - hh * 0.2, x1 + hh * 0.2, r0 + hh * 0.02, hh * 0.08, null);
  var m = (x0 + x1) / 2; q.save(); q.strokeStyle = '#e8b84a'; q.lineWidth = Math.max(2, hh * 0.035); q.lineCap = 'round';
  q.beginPath(); q.moveTo(m, peak); q.quadraticCurveTo(m - hh * 0.04, peak - hh * 0.12, m - hh * 0.16, peak - hh * 0.18); q.moveTo(m, peak); q.quadraticCurveTo(m + hh * 0.04, peak - hh * 0.12, m + hh * 0.16, peak - hh * 0.18); q.stroke(); q.restore();
  L.eave = [x0 - hh * 0.2, x1 + hh * 0.2, r0 + hh * 0.12];
  /* the pond on the open side; a frangipani on the other */
  var pl = L.bc < (S.x0 + S.x1) / 2, pcx = pl ? x1 + hh * 1.5 : x0 - hh * 1.5;
  pcx = clamp(pcx, S.x0 + hh * 1.3, S.x1 - hh * 1.3); L.pond = [pcx, S.deck + hh * 0.02, hh * 1.05, hh * 0.15];
  fe(q, pcx, S.deck + hh * 0.02, hh * 1.12, hh * 0.19, 0, n ? '#5a5466' : '#b9ad9c');
  fe(q, pcx, S.deck + hh * 0.02, hh * 1.05, hh * 0.15, 0, n ? '#1f3a5a' : '#5a9ac0');
  for (i = 0; i < 7; i++) { var px = pcx + (i - 3) * hh * 0.27, py = S.deck + hh * (0.03 + ((i * 37) % 5) * 0.012); q.fillStyle = n ? '#2c5a3a' : '#4f9a5a'; q.beginPath(); q.ellipse(px, py, hh * 0.1, hh * 0.032, 0, 0.3, TAU - 0.1); q.lineTo(px, py); q.fill(); }
  var fx = pl ? Math.max(S.x0 + hh * 0.7, x0 - hh * 0.6) : Math.min(S.x1 - hh * 0.9, x1 + hh * 0.6);
  if (L.plant === 'banana') banana(q, fx, S.deck + hh * 0.05, hh * 1.1, n); else frangipani(q, fx, S.deck + hh * 0.05, hh * 1.25, n);
  L.tree = [fx, S.deck - hh * 1.2];
  bougainvillea(q, vx0, vx1, fy - hh * 0.32, hh * 0.5, K.rnd(S.seed + 2), n);
  if (L.spirit) L.inc = spiritHouse(q, pl ? Math.min(x1 + hh * 0.35, pcx - hh * 1.25) : Math.max(x0 - hh * 0.35, pcx + hh * 1.25), S.deck + hh * 0.1, hh * 0.72, n);
  /* the name on a carved board hung from the floor beam */
  if (S.place) plate(q, (wx0 + wx1) / 2, fy + hh * 0.12, S.place, hh * 0.9, n ? '#3a2014' : '#6a3a1e', on || n, w * 0.75);
  else K.banner(q, (wx0 + wx1) / 2, fy + hh * 0.12, S.label, hh, L.pal.deep, S.seed, []);
}
function villaLive(S, L, st, crew) {
  var c = S.c, hh = S.hh, t = S.t, n = S.night, on = st === 'open', p = L.pond;
  /* the pond: rings spreading, r = r₀ + vt, and lotus flowers bobbing */
  for (var i = 0; i < 2; i++) { var u = ((t / 3800) + i * 0.5) % 1, rx = p[0] + (i ? 0.4 : -0.35) * p[2]; c.strokeStyle = 'rgba(255,255,255,' + 0.5 * (1 - u) + ')'; c.lineWidth = 1; c.beginPath(); c.ellipse(rx, p[1] + hh * 0.02, hh * 0.05 + u * hh * 0.3, hh * 0.015 + u * hh * 0.06, 0, 0, TAU); c.stroke(); }
  for (i = 0; i < 3; i++) { var lx = p[0] + (i - 1) * p[2] * 0.55, ly = p[1] - hh * 0.06 + Math.sin(t / 1500 + i * 2) * hh * 0.01, s = hh * 0.07;
    ln(c, [[lx, p[1] + hh * 0.03], [lx, ly]], '#4f8a4a', 1.2);
    fe(c, lx - s * 0.5, ly - s * 0.4, s * 0.28, s * 0.6, -0.5, n ? '#c97a9a' : '#f29ac0'); fe(c, lx + s * 0.5, ly - s * 0.4, s * 0.28, s * 0.6, 0.5, n ? '#c97a9a' : '#f29ac0'); fe(c, lx, ly - s * 0.6, s * 0.3, s * 0.7, 0, n ? '#e0a0b8' : '#ffc0d8'); }
  /* khom along the eave, swaying θ = 0.12·cos(t/600 + k), lit after dark */
  var e = L.eave, nk = Math.max(3, Math.round((e[1] - e[0]) / (hh * 0.7)));
  for (i = 0; i < nk; i++) khom(c, lerp(e[0] + hh * 0.2, e[1] - hh * 0.2, i / (nk - 1)), e[2], hh * 0.3, i % 2 ? L.khomCol : '#f2e6c9', n, 0.12 * Math.cos(t / 600 + i * 1.3));
  /* frangipani petals falling, y = vt, x = A·sin ωt */
  for (i = 0; i < 3; i++) { var fu = ((t / 6000) + i / 3) % 1, fx = L.tree[0] + (i - 1) * hh * 0.3 + Math.sin(fu * TAU * 1.5 + i) * hh * 0.15, fy = L.tree[1] + fu * hh * 1.25; spark(c, fx, fy, hh * 0.018, 'rgba(255,250,235,' + (1 - fu) + ')'); }
  if (L.inc) incense(c, L.inc[0], L.inc[1], hh * 0.12, t);
  if (!on) { cat(c, L.steps, S.deck + hh * 0.06, hh * 0.8, t, L.catCol); return; }
  /* a client on the veranda with tea, its steam curling */
  var d = crew[0]; d.dir = L.flip ? -1 : 1;
  var vx = lerp(L.ver[0], L.ver[1], L.flip ? 0.6 : 0.4), J = body(c, vx, L.ver[2] - hh * 0.02, hh * 0.85, { lean: 0, seat: 0.24, legs: [1.5, -1.5, 1.5, -1.5], arms: [0.6, 1.3, 0.4, 1.2] }, d);
  turban(c, J.head, hh * 0.85, '#fbf7f4');
  var cup = J.hand[0]; fr(c, cup[0] - hh * 0.03, cup[1] - hh * 0.04, hh * 0.06, hh * 0.05, '#f2e6c9');
  c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 1; c.beginPath(); for (var j = 0; j < hh * 0.2; j += 2) { var sx = cup[0] + Math.sin(j * 0.25 - t / 400) * 2; j ? c.lineTo(sx, cup[1] - hh * 0.05 - j) : c.moveTo(sx, cup[1] - hh * 0.05); } c.stroke();
  /* the nurse with folded towels, walking the path and back: x = a + b·½(1 − cos 2πt/T) */
  var ns = staff(K.rnd(S.seed + 9), 'nurse'), T = 16000, t2 = t + 4000 + (S.seed % 3000) - 1500, wv = cyc(t2, T), xa = L.steps, xb = clamp(p[0] + (p[0] < xa ? hh * 0.4 : -hh * 0.4), S.x0 + hh * 0.5, S.x1 - hh * 0.5);
  var x = lerp(xa, xb, wv), dir = Math.sin(t2 / T * TAU) >= 0 ? (xb > xa ? 1 : -1) : (xb > xa ? -1 : 1); ns.dir = dir;
  var P = K.walkP(Math.abs(x - xa) / (hh * 0.28), false); P.arms = [1.25, 0.85, 1.15, 0.9];
  var Jn = body(c, x, S.deck + hh * 0.12, hh * 0.92, P, ns), hx = (Jn.hand[0][0] + Jn.hand[1][0]) / 2, hy = Math.min(Jn.hand[0][1], Jn.hand[1][1]);
  for (var k = 0; k < 3; k++) fr(c, hx - hh * 0.12, hy - hh * (0.05 + k * 0.045), hh * 0.24, hh * 0.04, k % 2 ? L.pal.rose : '#fbf7f4');
}

/* a neighbouring shop in the corridor, told by its goods: handbags on shelves, a tea counter
   with its cups, a wall of books, buckets of flowers */
function neighbour(q, x, w, y0, deck, hh, kind, col, n) {
  fr(q, x, y0 + hh * 0.42, w, deck - y0 - hh * 0.42, n ? mixc(col, '#2a2838', 0.35) : col);
  fr(q, x, y0 + hh * 0.1, w, hh * 0.24, n ? '#4a4658' : ['#2a3a4a', '#8a3a2a', '#3f6a4a', '#5a3a6a'][kind]);
  fr(q, x + hh * 0.2, y0 + hh * 0.19, w - hh * 0.4, hh * 0.05, 'rgba(255,255,255,.55)');
  var fl = deck - hh * 0.04, i;
  if (kind === 0) { for (var r = 0; r < 2; r++) { fr(q, x + hh * 0.15, fl - hh * (0.45 + r * 0.45), w - hh * 0.3, hh * 0.03, '#b9a37a');
      for (i = 0; i < 4; i++) { var bx = x + hh * (0.3 + i * 0.42), by = fl - hh * (0.45 + r * 0.45), cc = ['#c0392b', '#2c2f45', '#e2b33c', '#9b6bd6'][(i + r) % 4];
        fr(q, bx - hh * 0.12, by - hh * 0.18, hh * 0.24, hh * 0.18, cc); q.strokeStyle = cc; q.lineWidth = 1.5; q.beginPath(); q.arc(bx, by - hh * 0.18, hh * 0.08, Math.PI, TAU); q.stroke(); } } }
  else if (kind === 1) { fr(q, x + hh * 0.15, fl - hh * 0.45, w - hh * 0.3, hh * 0.45, '#8a5530'); for (i = 0; i < 5; i++) { var cx = x + hh * (0.35 + i * 0.3); fp(q, [[cx - hh * 0.06, fl - hh * 0.72], [cx + hh * 0.06, fl - hh * 0.72], [cx + hh * 0.045, fl - hh * 0.5], [cx - hh * 0.045, fl - hh * 0.5]], 'rgba(255,255,255,.8)'); fr(q, cx - hh * 0.045, fl - hh * 0.62, hh * 0.09, hh * 0.12, ['#c98a5a', '#f2c94c', '#7fe0a4', '#ff9a9a', '#c3a6ff'][i]); ln(q, [[cx + hh * 0.01, fl - hh * 0.72], [cx + hh * 0.03, fl - hh * 0.8]], '#2a2a2a', 1.5); } }
  else if (kind === 2) { for (r = 0; r < 3; r++) { fr(q, x + hh * 0.15, fl - hh * (0.3 + r * 0.35), w - hh * 0.3, hh * 0.03, '#8a5530'); for (var bx2 = x + hh * 0.18; bx2 < x + w - hh * 0.2; bx2 += hh * 0.07) fr(q, bx2, fl - hh * (0.3 + r * 0.35) - hh * (0.2 + ((bx2 * 7) % 5) * 0.02), hh * 0.055, hh * (0.2 + ((bx2 * 7) % 5) * 0.02), ['#c0392b', '#2c3e6b', '#e2b33c', '#4fae8c', '#f2e6c9'][Math.floor(bx2) % 5]); } }
  else { for (i = 0; i < 4; i++) { var fx = x + hh * (0.35 + i * 0.42); fp(q, [[fx - hh * 0.12, fl], [fx + hh * 0.12, fl], [fx + hh * 0.15, fl - hh * 0.25], [fx - hh * 0.15, fl - hh * 0.25]], '#5a6a7a');
      for (var j = 0; j < 7; j++) { var a = j / 7 * Math.PI; ln(q, [[fx, fl - hh * 0.25], [fx + Math.cos(a) * hh * 0.18, fl - hh * 0.25 - Math.sin(a) * hh * 0.3]], '#3f7a48', 1); fc(q, fx + Math.cos(a) * hh * 0.18, fl - hh * 0.25 - Math.sin(a) * hh * 0.3, hh * 0.05, ['#e5567f', '#f2c94c', '#fbf7f4', '#ff9a5a'][(i + j) % 4]); } } }
  q.fillStyle = 'rgba(230,240,250,.22)'; q.fillRect(x, y0 + hh * 0.42, w, deck - y0 - hh * 0.42);
  fr(q, x, y0 + hh * 0.42, 2, deck - y0 - hh * 0.42, '#c9ccd4'); fr(q, x + w - 2, y0 + hh * 0.42, 2, deck - y0 - hh * 0.42, '#c9ccd4');
}

/* a tung hung from a ceiling: bands of cloth, the cloth a travelling wave x = A·(y/L)·sin(ky − ωt) */
var TUNGC = [['#d9342b', '#f2c94c', '#f2e6c9', '#2f8f5b'], ['#e5567f', '#f2c94c', '#4d8fd1', '#f2e6c9']];
function tungHang(c, x, y, len, w, t, k) {
  var N = 12, pal = TUNGC[k % 2], prev = null;
  ln(c, [[x - w * 0.2, y], [x + w * 1.2, y]], '#c9b27a', 2);
  for (var i = 0; i <= N; i++) {
    var f = i / N, yy = y + 2 + f * len, dx = Math.sin(f * 5 - t / 520 + k) * f * w * 0.7, cur = [x + dx, yy];
    if (prev) fp(c, [[prev[0], prev[1]], [prev[0] + w, prev[1]], [cur[0] + w, cur[1] + 0.6], [cur[0], cur[1] + 0.6]], pal[Math.floor(i / 2) % pal.length]);
    prev = cur;
  }
  fp(c, [[prev[0], prev[1]], [prev[0] - w * 0.1, prev[1] + w * 0.9], [prev[0] + w / 2, prev[1] + w * 0.3], [prev[0] + w * 1.1, prev[1] + w * 0.9], [prev[0] + w, prev[1]]], pal[0]);
}

/* ---------------------------------------------------------------- look 5: a unit in a mall
   the corridor: a skylight letting the real sky in, the floor above behind glass rails,
   neighbours' fronts either side, the clinic's glass front and its name, shoppers passing */
function mallBack(q, S, L, st) {
  var hh = S.hh, n = S.night, on = st === 'open', pal = L.pal, ceil = S.deck - hh * 2.55;
  /* the ceiling: a slab with skylight panes cut through it */
  q.save(); q.fillStyle = n ? '#2a2838' : '#e8e4e0'; q.beginPath(); q.rect(S.x0 - 4, 0, S.span + 8, ceil);
  var nP = Math.max(3, Math.round(S.span / (hh * 1.6)));
  for (var i = 0; i < nP; i++) { var px = S.x0 + (i + 0.5) * S.span / nP, pw = S.span / nP * 0.7; q.moveTo(px - pw / 2, ceil * 0.15); q.lineTo(px + pw / 2, ceil * 0.15); q.lineTo(px + pw / 2 - hh * 0.2, ceil * 0.75); q.lineTo(px - pw / 2 + hh * 0.2, ceil * 0.75); q.closePath(); }
  q.fill('evenodd'); q.restore();
  q.fillStyle = n ? 'rgba(255,220,160,.5)' : 'rgba(255,255,255,.7)'; for (i = 0; i < nP * 2; i++) q.fillRect(S.x0 + (i + 0.5) * S.span / (nP * 2) - 3, ceil - 4, 6, 3);
  /* the floor above: a band and its glass rail */
  fr(q, S.x0 - 4, ceil, S.span + 8, hh * 0.18, n ? '#3a3848' : '#d8d2cc');
  fr(q, S.x0 - 4, ceil - hh * 0.22, S.span + 8, hh * 0.22, n ? 'rgba(160,190,220,.25)' : 'rgba(200,225,240,.45)'); fr(q, S.x0 - 4, ceil - hh * 0.23, S.span + 8, 2, '#c9ccd4');
  /* the back: neighbours and the clinic */
  var by0 = ceil + hh * 0.18;
  fr(q, S.x0 - 4, by0, S.span + 8, S.deck - by0, n ? '#3a3648' : '#f2eee8');
  var nb = ['#d9e4ea', '#efe6d8', '#e0e8dc', '#ece0e8', '#e2e2e8'];
  for (var x = S.x0 + hh * 0.1, k = 0; x < S.x1; x += hh * 2.2, k++) {
    if (x + hh * 2.0 > L.bx0 - hh * 0.1 && x < L.bx1 + hh * 0.1) continue;
    neighbour(q, x, hh * 2.0, by0, S.deck, hh, (k + S.seed) % 4, nb[(k + S.seed) % nb.length], n);
  }
  /* the clinic's front: a rose frame, glass, a reception desk, a gold panel, orchids */
  var x0 = L.bx0, x1 = L.bx1;
  fr(q, x0, by0, x1 - x0, S.deck - by0, on ? (n ? '#ffe6c8' : pal.room) : '#3a3550');
  laiKham(q, (x0 + x1) / 2 - hh * 0.5, S.deck - hh * 1.4, hh * 1.0, hh * 0.55, L.lacquer);
  if (on) glow(q, (x0 + x1) / 2, S.deck - hh * 1.1, hh * 1.3, 38, n ? 0.5 : 0.3);
  fr(q, (x0 + x1) / 2 - hh * 0.6, S.deck - hh * 0.48, hh * 1.2, hh * 0.46, pal.deep); fr(q, (x0 + x1) / 2 - hh * 0.63, S.deck - hh * 0.5, hh * 1.26, hh * 0.04, '#e0b04a');
  face(q, (x0 + x1) / 2, S.deck - hh * 0.26, hh * 0.3, '#f2d9a0', Math.max(1, hh * 0.02));
  bottles(q, x0 + hh * 0.2, (x0 + x1) / 2 - hh * 0.6, S.deck - hh * 0.95, hh, K.rnd(S.seed + 23)); L.led = x1 - x0 > hh * 3.4 ? recliner(q, x1 - hh * 0.85, S.deck - hh * 0.02, hh * 0.9, on, pal, L.cl) : null;
  orchid(q, x0 + hh * 0.35, S.deck, hh * 0.6, L.bloomA, 1); orchid(q, x1 - hh * 0.35, S.deck, hh * 0.6, L.bloomB, -1);
  q.fillStyle = 'rgba(230,240,250,.25)'; q.fillRect(x0, by0 + hh * 0.42, x1 - x0, S.deck - by0 - hh * 0.42);
  fr(q, x0 - hh * 0.08, by0, hh * 0.1, S.deck - by0, pal.rose); fr(q, x1 - hh * 0.02, by0, hh * 0.1, S.deck - by0, pal.rose);
  fr(q, x0, by0 + hh * 0.36, x1 - x0, hh * 0.06, '#d4a23f');
  if (!on) shutter(q, x0, x1, by0 + hh * 0.42, S.deck, n ? '#6a6878' : '#c8c4cc', n);
  /* the floor: polished, the lights in it */
  fr(q, S.x0 - 4, S.deck, S.span + 8, S.H - S.deck, n ? '#4a4658' : '#ddd6cc');
  q.fillStyle = n ? 'rgba(255,220,160,.15)' : 'rgba(255,255,255,.4)'; for (i = 0; i < nP * 2; i++) q.fillRect(S.x0 + (i + 0.5) * S.span / (nP * 2) - 2, S.deck + hh * 0.1, 4, S.H - S.deck - hh * 0.12);
  q.strokeStyle = 'rgba(0,0,0,.06)'; q.lineWidth = 1; q.beginPath(); for (x = S.x0; x < S.x1; x += hh * 0.5) { q.moveTo(x, S.deck); q.lineTo(x - hh * 0.3, S.H); } q.stroke();
  /* where it is: the building's name on a hanging board */
  var P = S.place || {};
  if (P.inside) { q.font = '700 ' + Math.round(Math.max(9, hh * 0.13)) + 'px "Sarabun",system-ui,sans-serif'; var tw = q.measureText(P.inside).width + hh * 0.3, hx = L.bx1 + hh * 0.3 + tw / 2 < S.x1 - 10 ? L.bx1 + hh * 0.3 + tw / 2 : L.bx0 - hh * 0.3 - tw / 2;
    ln(q, [[hx - tw * 0.3, ceil + hh * 0.18], [hx - tw * 0.3, ceil + hh * 0.3]], '#9a9aa6', 1); ln(q, [[hx + tw * 0.3, ceil + hh * 0.18], [hx + tw * 0.3, ceil + hh * 0.3]], '#9a9aa6', 1);
    fr(q, hx - tw / 2, ceil + hh * 0.3, tw, hh * 0.22, '#2a3a4a'); L.board = [hx - tw / 2, hx + tw / 2]; q.fillStyle = '#ffffff'; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText(P.inside, hx, ceil + hh * 0.41); }
  return S.place ? plate(q, (x0 + x1) / 2, by0 + hh * 0.0, S.place, hh * 0.85, n ? '#5a2a3a' : pal.deep, on, x1 - x0) : null;
}
function mallLive(S, L, st, crew) {
  var c = S.c, hh = S.hh, t = S.t, on = st === 'open', ceil = S.deck - hh * 2.55, i;
  /* the corridor dressed for the north: tung hung from the ceiling, khom between them */
  for (i = 0; i < 2; i++) tungHang(c, i ? S.x1 - hh * 0.4 : S.x0 + hh * 0.2, ceil + hh * 0.18, hh * 1.25, hh * 0.2, t, i * 2);
  var nk = Math.max(3, Math.round(S.span / (hh * 1.6)));
  for (i = 0; i < nk; i++) { var kx = S.x0 + (i + 0.5) * S.span / nk; if (kx > L.bx0 - hh * 0.3 && kx < L.bx1 + hh * 0.3 || L.board && kx > L.board[0] - hh * 0.2 && kx < L.board[1] + hh * 0.2) continue;
    khom(c, kx, ceil + hh * 0.18, hh * 0.24, i % 2 ? L.khomCol : '#f2e6c9', true, 0.08 * Math.cos(t / 700 + i)); }
  if (L.led) { var m = cyc(t, 10000), bl = clamp((m - 0.35) * 3.3, 0, 1); glow(c, L.led[0], L.led[1] + hh * 0.05, hh * 0.28, 0, 0.8 * (1 - bl)); glow(c, L.led[0], L.led[1] + hh * 0.05, hh * 0.28, 225, 0.8 * bl); }
  if (on) { var ns = staff(K.rnd(S.seed + 13), 'nurse'); ns.dir = 1; body(c, L.bx0 + hh * 0.75, S.deck + hh * 0.02, hh * 0.9, Math.sin(t / 5000) > 0.3 ? WAI : STAND, ns); }
  /* shoppers along the corridor at their own speeds, x = x₀ + vt */
  for (var i = 0; i < 3; i++) {
    var d = crew[i], v = hh * (0.5 + 0.15 * i), span = S.span + hh * 2, dir = i % 2 ? -1 : 1, s = ((t / 1000) * v + i * span / 3) % span, x = dir > 0 ? S.x0 - hh + s : S.x1 + hh - s;
    d.dir = dir; var J = body(c, x, S.deck + hh * (0.18 + i * 0.07), hh * 0.95, K.walkP(s / (hh * 0.3), false), d);
    if (i !== 1) fr(c, J.hand[1][0] - hh * 0.05, J.hand[1][1], hh * 0.1, hh * 0.12, ['#f2c1cc', '#f2e6c9', '#9fcfc4'][i]);
  }
}

/* ---------------------------------------------------------------- the scene */
function draw(S0) {
  var S = Object.create(S0), c = S.c, hh;
  if (S.phone) S.hh = S0.hh * 1.12; hh = S.hh;
  var L = lay(S), st = stateOf(S), P = S.place, look = L.look;
  var river = P && P.river && P.river.m != null && P.river.m < 400 && look !== 'mall';
  var key = ['bc', look, S.W, S.H, Math.round(S.x0), Math.round(S.x1), Math.round(S.deck), Math.round(hh * 10), S.seed, S.night ? 1 : 0, st, S.label].join('|');
  var crew = K.town(S, 4, { casual: 0.7, sin: 0.18, mohom: 0.12 }); L.cl = crew[3];
  crew.forEach(function (d) { d.skirt = 0; });
  if (look === 'mall') {
    take(L, layer(S, key + '|m', 0, S.H, function (q) { mallBack(q, S, L, st); return keep(L); }));
    mallLive(S, L, st, crew); S0.noMagic = true;
  } else {
    var green = look === 'villa', y0 = L.top - hh * 0.5;
    layer(S, key + '|g', y0, S.H, function (q) { street(q, S, L, green); var Q = Object.create(S); Q.c = q; Q.t = 0; K.setting(Q); });
    if (river) {   /* the river is cut once with the ground; its ripples run, x = x₀ + t/40 */
      var ry = S.deck + (S.H - S.deck) * 0.575; c.strokeStyle = 'rgba(255,255,255,.4)'; c.lineWidth = 1.2; c.beginPath();
      for (var k = 0; k < 8; k++) { var rx = S.x0 + ((k * 97 + S.t / 40) % S.span); c.moveTo(rx, ry); c.lineTo(rx + 10, ry); } c.stroke();
    }
    take(L, layer(S, key + '|b', y0, S.H, function (q) {
      if (look === 'villa') villaBack(q, S, L, st);
      else {
        L.inc = pavement(q, S, L).inc;
        if (look === 'front') frontBack(q, S, L, st);
        else { roomShell(q, S, L, st); q.save(); mirror(q, L); if (look === 'consult') consultBack(q, S, L, st); else treatBack(q, S, L, st); q.restore(); roomFrame(q, S, L, st); }
      }
      return keep(L);
    }));
    if (look === 'front') frontLive(S, L, st, crew);
    else if (look === 'consult' || look === 'treat') { c.save(); mirror(c, L); (look === 'consult' ? consultLive : treatLive)(S, L, st, crew); c.restore(); }
    else villaLive(S, L, st, crew);
    if (look !== 'villa') {
      if (L.inc) incense(c, L.inc[0], L.inc[1], hh * 0.12, S.t);
      if (st !== 'open') { cat(c, (L.dx0 || L.bc) + hh * 0.3, S.deck + hh * 0.1, hh * 0.85, S.t, L.catCol); if (L.lamp) moth(c, L.lamp[0], L.lamp[1], hh, S.t); }
      /* khom along the fascia after dark */
      if (S.night) { var nk = Math.max(2, Math.round(L.bw / (hh * 1.1))); for (var i = 0; i < nk; i++) khom(c, lerp(L.bx0 + hh * 0.3, L.bx1 - hh * 0.3, nk > 1 ? i / (nk - 1) : 0.5), L.gt + (L.awning && look === 'front' ? hh * 0.15 : 0), hh * 0.24, i % 2 ? L.khomCol : '#f2e6c9', true, 0.1 * Math.cos(S.t / 650 + i)); }
    }
  }
  S0.hits.push({ k: P ? 'place' : 'event', x0: L.bx0, x1: L.bx1, y0: L.top, y1: S.deck });
  if (!P && S.label) S0.hits.push({ k: 'event', x0: L.bc - hh * 1.5, x1: L.bc + hh * 1.5, y0: L.top, y1: L.top + hh * 0.5 });
}

D.addScene('beautyclinic', draw, /beauty clinic|aesthetic clinic|คลินิกความงาม|skin ?care (workshop|class|talk)|skincare|dermatolog/i, 'y = ½h(1 − cos 2πt/T)<br>the scan line, the doors, the light turning red to blue', 1);
})();
