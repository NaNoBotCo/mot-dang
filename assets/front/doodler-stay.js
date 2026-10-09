/* Places to stay and live, drawn as portraits of one place for pages with no photograph of
   their own (Nan, 2026-10-02: "utilize the doodler to avoid filler"). A scene reads the place's
   facts (S.place) and deals its look from the hash of its id, so two pages of a kind are two
   drawings. The still parts are cut once into an offscreen canvas; only what moves is drawn
   each frame.
   'hotel'      seven kinds, from the facts and the name: a Lanna resort round its pool, an
                old-city boutique, a mid-rise city hotel with its doorman, a riverside hotel with a
                long-tail going by, a hill resort in the mist, a camp round its fire, a homestay;
                guests arrive by songthaew or tuk-tuk, the bell rings, rooms light one by one
   'guesthouse' a family house: laundry on the balcony, bikes for rent, the auntie sweeping,
                banana pancakes on the garden table, backpackers coming and going
   'hostel'     bunks in the windows, cards in the common room, the chalkboard, bicycles
   'condo'      a tower dealt its floors, balconies, pool deck and rooftop; the barrier lifts for
                a car. Records named for a village are drawn as 'moobaan', firms as 'agent'
   'apartment'  low-rise blocks for monthly rent, scooters under the carport
   'dorm'       a dorm by the university: students, bicycles, a noodle stall
   'moobaan'    a gated estate: the arch, rows of houses, the guard, kids cycling, the lake
   'agent'      an estate agent's office: listings in the window, keys, a house model */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D || !D.kit || !D.kit.sign) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, rnd = K.rnd, TAU = K.TAU;
var FONT = '"Sarabun",system-ui,sans-serif';

/* ---------------------------------------------------------------- small tools */
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function pick(r, a) { return a[Math.floor(r() * a.length) % a.length]; }
function frac(v) { return v - Math.floor(v); }
function path(c, pts) { c.beginPath(); for (var i = 0; i < pts.length; i++) i ? c.lineTo(pts[i][0], pts[i][1]) : c.moveTo(pts[i][0], pts[i][1]); }
function fp(c, pts, col) { c.fillStyle = col; path(c, pts); c.closePath(); c.fill(); }
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = Math.max(0.6, w); c.lineCap = 'round'; c.lineJoin = 'round'; path(c, pts); c.stroke(); }
function fe(c, x, y, rx, ry, col, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.3, rx), Math.max(0.3, ry), rot || 0, 0, TAU); c.fill(); }
function fr(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x, y, w, h); }
function pr(c, x, y, w, h, col, lift) { paper(c, rect(x, y, w, h), col, lift == null ? 1 : lift); }
/* colour a toward b by u (hex), kept once worked out */
var MIXC = {};
function mixc(a, b, u) {
  var k = a + b + u; if (MIXC[k]) return MIXC[k];
  var A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16);
  function ch(s) { return Math.round(lerp((A >> s) & 255, (B >> s) & 255, u)); }
  return (MIXC[k] = '#' + ((1 << 24) | (ch(16) << 16) | (ch(8) << 8) | ch(0)).toString(16).slice(1));
}
/* the night's blue over a colour */
function nt(S, col, u) { return S.night ? mixc(col, '#161a34', u == null ? 0.5 : u) : col; }
/* a soft round glow, from a small disc cut once per colour */
var GLOW = {};
function glow(c, x, y, r, rgb, a) {
  var o = GLOW[rgb];
  if (!o) { if (typeof document === 'undefined') return; o = GLOW[rgb] = document.createElement('canvas'); o.width = o.height = 64; var q = o.getContext('2d'), g = q.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(' + rgb + ',1)'); g.addColorStop(0.45, 'rgba(' + rgb + ',.42)'); g.addColorStop(1, 'rgba(' + rgb + ',0)'); q.fillStyle = g; q.fillRect(0, 0, 64, 64); }
  c.save(); c.globalAlpha = clamp(a, 0, 1); c.drawImage(o, x - r, y - r, r * 2, r * 2); c.restore();
}
/* the still layer: drawn once per page size, scale, seed, kind and open state, then stamped */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : null;
  if (!m || typeof document === 'undefined') return draw(c);
  var k = key + '|' + [m.a, m.d, m.e, m.f].join(','), e = null, i;
  for (i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    var cv = document.createElement('canvas'); cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    e = { k: k, cv: cv, ox: ox, oy: oy, out: draw(q) };
    CACHE.unshift(e); if (CACHE.length > 16) CACHE.pop();
  } else if (i) { CACHE.splice(i, 1); CACHE.unshift(e); }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
  return e.out;
}
/* open, closed, or quiet (hours unknown, after dark) */
function stateOf(S) { var o = K.openNow(S.place && S.place.hours, S.now); return o === true ? 'open' : o === false ? 'closed' : S.night ? 'quiet' : 'open'; }
function nameOf(P) { return ((P.name || '') + ' ' + (P.nameEn || '') + ' ' + (P.nameTh || '')).toLowerCase(); }
/* the sign's own size, as K.sign cuts it */
function signSize(c, P, u) {
  var th = P.nameTh || P.name || '', en = P.nameEn && P.nameEn !== th ? P.nameEn : '', f1 = Math.max(11, u * 0.19), f2 = Math.max(9, u * 0.13);
  c.save(); c.font = '800 ' + Math.round(f1) + 'px ' + FONT; var w1 = c.measureText(th.length > 34 ? th.slice(0, 33) + '…' : th).width;
  c.font = '700 ' + Math.round(f2) + 'px ' + FONT; var w2 = en ? c.measureText(en.length > 40 ? en.slice(0, 39) + '…' : en).width : 0; c.restore();
  return { w: Math.min(Math.max(w1, w2) + u * 0.5, u * 7), h: en ? f1 + f2 + u * 0.18 : f1 + u * 0.16 };
}
var SIGNCOL = ['#6a3a1e', '#7a2a24', '#2f4a3a', '#3a2f5a', '#1f3a5a', '#5a3a1a', '#4a2a3a', '#2a4a4a'];
/* the sign hung under a beam on two carved posts, a small Lanna roof on top, marigolds on the beam */
function gateSign(c, S, cx, P, col, lit, roofCol) {
  var u = S.hh, G = S.deck, z = signSize(c, P, u), top = G - u * 1.15 - z.h, x0 = cx - z.w / 2 - u * 0.18, x1 = cx + z.w / 2 + u * 0.18, wood = nt(S, '#6a4026', 0.4);
  pr(c, x0 - u * 0.05, top - u * 0.12, u * 0.1, G - top + u * 0.12, wood, 1.2); pr(c, x1 - u * 0.05, top - u * 0.12, u * 0.1, G - top + u * 0.12, wood, 1.2);
  pr(c, x0 - u * 0.16, top - u * 0.2, x1 - x0 + u * 0.32, u * 0.09, wood, 1.2);
  lannaRoof(c, cx, Math.min(x1 - x0 + u * 0.3, u * 2.2), top - u * 0.19, u * 0.3, roofCol || nt(S, '#a8432f', 0.45));
  marigolds(c, x0, x1, top - u * 0.1, u * 0.12, u);
  return nameSign(c, cx, top + u * 0.02, P, u, col, lit);
}
/* a low board by the gate on two short carved posts, the name hung under the beam */
function lowSign(c, S, cx, P, col, lit) {
  var u = S.hh, G = S.deck, z = signSize(c, P, u), top = G - u * 0.42 - z.h, x0 = cx - z.w / 2 - u * 0.08, x1 = cx + z.w / 2 + u * 0.08, wood = nt(S, '#6a4026', 0.4);
  pr(c, x0 - u * 0.04, top - u * 0.08, u * 0.08, G - top + u * 0.08, wood, 1); pr(c, x1 - u * 0.04, top - u * 0.08, u * 0.08, G - top + u * 0.08, wood, 1);
  pr(c, x0 - u * 0.12, top - u * 0.1, x1 - x0 + u * 0.24, u * 0.07, wood, 1);
  kalae(c, x0, top - u * 0.1, u * 0.16); kalae(c, x1, top - u * 0.1, u * 0.16);
  marigolds(c, x0, x1, top - u * 0.02, u * 0.06, u);
  return nameSign(c, cx, top + u * 0.1, P, u, col, lit);
}
/* the place's own sign (K.sign), drawn when the place has a name */
function nameSign(c, cx, y, P, u, col, lit) { return P && (P.name || P.nameTh) ? K.sign(c, cx, y, P, u, col, lit) : null; }
/* a marigold string between two points, a sagging arc of orange and gold flowers */
function marigolds(c, xa, xb, y, sag, u) {
  var n = Math.max(4, Math.round((xb - xa) / (u * 0.07)));
  for (var i = 0; i <= n; i++) { var f = i / n, x = lerp(xa, xb, f), yy = y + Math.sin(f * Math.PI) * sag; fe(c, x, yy, u * 0.035, u * 0.035, i % 3 ? '#f29a1f' : '#f7c52c'); }
}
/* the street's name on a blue plate on a post, Thai first */
function roadPlate(c, S, x) {
  var P = S.place || {}; if (!P.road) return;
  var road = String(P.road), u = S.hh, txt = /^(ถนน|ถ\.|ซอย|ซ\.)/.test(road) || /[a-z]/i.test(road) ? road : 'ถนน' + road;
  if (txt.length > 26) txt = txt.slice(0, 25) + '…';
  var f = Math.max(9, u * 0.12); c.save(); c.font = '700 ' + Math.round(f) + 'px ' + FONT; var w = c.measureText(txt).width + u * 0.22, h = f + u * 0.1, y = S.deck - u * 1.02;
  ln(c, [[x, S.deck + u * 0.04], [x, y + h]], '#8a8f96', Math.max(1.5, u * 0.035));
  pr(c, x - w / 2, y, w, h, S.night ? '#1d3a6a' : '#1f5aa8', 0.8);
  c.strokeStyle = '#f2f2f2'; c.lineWidth = 1; c.strokeRect(x - w / 2 + 2, y + 2, w - 4, h - 4);
  c.fillStyle = '#ffffff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(txt, x, y + h / 2 + 0.5); c.restore();
}
/* gold lai kham along a band: four-petal flowers and curls in a row */
function laiKham(c, x0, x1, y, s, col) {
  c.strokeStyle = col || '#e8b84a'; c.lineWidth = Math.max(0.6, s * 0.12);
  for (var x = x0 + s; x < x1 - s * 0.5; x += s * 2.4) {
    for (var p = 0; p < 4; p++) { var a = p * Math.PI / 2 + 0.785; fe(c, x + Math.cos(a) * s * 0.42, y + Math.sin(a) * s * 0.42, s * 0.3, s * 0.16, col || '#e8b84a', a); }
    c.beginPath(); c.arc(x + s * 1.2, y, s * 0.35, Math.PI * 0.2, Math.PI * 1.6); c.stroke();
  }
}
/* the kalae: crossed gable horns */
function kalae(c, x, y, l, col) {
  ln(c, [[x, y], [x - l * 0.25, y - l * 0.7], [x - l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
  ln(c, [[x, y], [x + l * 0.25, y - l * 0.7], [x + l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
}
/* a Lanna roof in two tiers with its kalae and a gold eave line */
function lannaRoof(c, x, w, y, h, col) {
  paper(c, poly([[x - w * 0.55, y], [x - w * 0.3, y - h * 0.5], [x + w * 0.3, y - h * 0.5], [x + w * 0.55, y]]), col, 1);
  paper(c, poly([[x - w * 0.36, y - h * 0.42], [x, y - h], [x + w * 0.36, y - h * 0.42]]), col, 1.1);
  ln(c, [[x - w * 0.5, y - h * 0.04], [x + w * 0.5, y - h * 0.04]], '#e8b84a', Math.max(1, h * 0.06));
  kalae(c, x, y - h, h * 0.5);
}
/* a steep teak gable (the ruean kalae's) with its horns */
function gable(c, x, w, y, h, col, horns) {
  paper(c, poly([[x - w * 0.56, y], [x, y - h], [x + w * 0.56, y]]), col, 1.2);
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; for (var k = 1; k < 5; k++) { var f = k / 5; c.beginPath(); c.moveTo(x - w * 0.56 * (1 - f), y - h * f); c.lineTo(x + w * 0.56 * (1 - f), y - h * f); c.stroke(); }
  if (horns !== false) kalae(c, x, y - h + 1, h * 0.45, '#c9873a');
}
function hipRoof(c, x, w, y, h, col) { paper(c, poly([[x - w * 0.56, y], [x - w * 0.3, y - h], [x + w * 0.3, y - h], [x + w * 0.56, y]]), col, 1.1); c.strokeStyle = 'rgba(0,0,0,.14)'; c.lineWidth = 1; for (var k = 1; k < 4; k++) { c.beginPath(); c.moveTo(x - w * (0.56 - 0.26 * k / 4), y - h * k / 4); c.lineTo(x + w * (0.56 - 0.26 * k / 4), y - h * k / 4); c.stroke(); } }
/* a window: glass by day, warm when lit after dark, a curtain to one side */
function pane(c, S, x, y, w, h, lit, frame, curtain, k) {
  fr(c, x - 1, y - 1, w + 2, h + 2, frame);
  if (S.night) { fr(c, x, y, w, h, lit ? '#ffd27a' : '#232a46'); if (lit) fr(c, x, y + h * 0.6, w, h * 0.4, '#f5b85a'); }
  else { fr(c, x, y, w, h, '#a9cfe0'); c.fillStyle = 'rgba(255,255,255,.35)'; c.beginPath(); c.moveTo(x + w * 0.15, y + h); c.lineTo(x + w * 0.55, y); c.lineTo(x + w * 0.75, y); c.lineTo(x + w * 0.35, y + h); c.fill(); }
  if (curtain) fr(c, (k || 0) % 2 ? x + w * 0.66 : x, y, w * 0.34, h, S.night && lit ? mixc(curtain, '#ffd27a', 0.35) : nt(S, curtain, 0.4));
}
/* a roll-up shutter, the Thai shophouse kind, ribbed */
function shutter(c, x, y, w, h, S, col) {
  pr(c, x, y, w, h, nt(S, col || '#9aa0a8', 0.45), 0.6);
  c.strokeStyle = 'rgba(0,0,0,.22)'; c.lineWidth = 1; for (var yy = y + 3; yy < y + h; yy += Math.max(3, h / 16)) { c.beginPath(); c.moveTo(x + 1, yy); c.lineTo(x + w - 1, yy); c.stroke(); }
  fr(c, x + w * 0.45, y + h - 4, w * 0.1, 2, 'rgba(30,30,30,.6)');
}

/* ---------------------------------------------------------------- plants */
function bush(c, x, y, r, cols, n, seed) {
  var R = rnd(seed); for (var i = 0; i < n; i++) { var a = R() * TAU, d = R() * r * 0.7; fe(c, x + Math.cos(a) * d, y + Math.sin(a) * d * 0.6, r * (0.35 + R() * 0.3), r * (0.3 + R() * 0.25), cols[i % cols.length]); }
}
/* bougainvillea: a dark green spill with magenta bracts, falling over a wall or rail */
function bougain(c, x, y, w, h, S, seed) {
  var R = rnd(seed), pink = pick(R, ['#d6337f', '#e5568f', '#c2185b', '#f06aa0', '#e8763a', '#b8336a']);
  for (var i = 0; i < 18; i++) { var px = x + R() * w, py = y + R() * R() * h; fe(c, px, py, w * 0.09 + R() * w * 0.06, w * 0.07, nt(S, i % 3 ? '#2f6b3a' : '#3f7d45', 0.5)); }
  for (i = 0; i < 26; i++) { var qx = x + R() * w, qy = y + R() * R() * h; fe(c, qx, qy, w * 0.05, w * 0.04, nt(S, i % 4 ? pink : '#f7a8c8', 0.45)); }
}
/* frangipani: grey forked limbs, leaf rosettes at the tips, five-petal flowers */
function frangipani(c, x, G, s, S, seed) {
  var R = rnd(seed), bark = nt(S, '#8a7f74', 0.45), tips = [];
  function limb(x0, y0, a, l, d) { var x1 = x0 + Math.sin(a) * l, y1 = y0 - Math.cos(a) * l; ln(c, [[x0, y0], [x1, y1]], bark, Math.max(1.5, s * 0.05 * (3 - d) / 2)); if (d < 2) { limb(x1, y1, a - 0.45 - R() * 0.2, l * 0.7, d + 1); limb(x1, y1, a + 0.45 + R() * 0.2, l * 0.7, d + 1); } else tips.push([x1, y1]); }
  limb(x, G, (R() - 0.5) * 0.2, s * 0.42, 0);
  tips.forEach(function (p, i) {
    for (var k = 0; k < 6; k++) { var a = k / 6 * TAU + i; fe(c, p[0] + Math.cos(a) * s * 0.07, p[1] + Math.sin(a) * s * 0.04 - s * 0.02, s * 0.08, s * 0.025, nt(S, '#3d7a3f', 0.5), a); }
    for (k = 0; k < 2; k++) { var fx = p[0] + (k - 0.5) * s * 0.07, fy = p[1] - s * 0.05 - k * s * 0.02;
      for (var j = 0; j < 5; j++) { var b = j / 5 * TAU; fe(c, fx + Math.cos(b) * s * 0.022, fy + Math.sin(b) * s * 0.022, s * 0.022, s * 0.013, nt(S, '#fbf6ea', 0.3), b); }
      fe(c, fx, fy, s * 0.012, s * 0.012, '#f2c94c'); }
  });
}
/* a banana: a soft trunk and big ragged leaves */
function banana(c, x, G, s, S, seed) {
  var R = rnd(seed); pr(c, x - s * 0.04, G - s * 0.55, s * 0.08, s * 0.55, nt(S, '#7a8a4a', 0.5), 0.8);
  for (var i = 0; i < 6; i++) { var a = -1.2 + i * 0.48 + (R() - 0.5) * 0.2, l = s * (0.38 + R() * 0.12), tx = x + Math.sin(a) * l, ty = G - s * 0.55 - Math.cos(a) * l * 0.6;
    paper(c, function (q) { q.beginPath(); q.moveTo(x, G - s * 0.55); q.quadraticCurveTo((x + tx) / 2 + Math.cos(a) * s * 0.08, (G - s * 0.55 + ty) / 2 - s * 0.1, tx, ty); q.quadraticCurveTo((x + tx) / 2 - Math.cos(a) * s * 0.02, (G - s * 0.55 + ty) / 2 + s * 0.06, x, G - s * 0.55); q.closePath(); }, nt(S, i % 2 ? '#4f9a45' : '#62ad4f', 0.5), 0.7); }
}
/* a coconut palm: a leaning trunk of rings, fronds in arcs */
function palm(c, x, G, s, S, lean) {
  var tx = x + lean * s * 0.25, ty = G - s, trunk = nt(S, '#8a6a4a', 0.45);
  c.strokeStyle = trunk; c.lineWidth = Math.max(2, s * 0.06); c.lineCap = 'round'; c.beginPath(); c.moveTo(x, G); c.quadraticCurveTo(x, G - s * 0.5, tx, ty); c.stroke();
  for (var i = 0; i < 7; i++) { var a = -2.6 + i * 0.75, ex = tx + Math.cos(a) * s * 0.42, ey = ty + Math.sin(a) * s * 0.2 + s * 0.12;
    c.strokeStyle = nt(S, i % 2 ? '#3f8a45' : '#55a04f', 0.5); c.lineWidth = Math.max(2, s * 0.05); c.beginPath(); c.moveTo(tx, ty); c.quadraticCurveTo((tx + ex) / 2, ty - s * 0.14, ex, ey); c.stroke(); }
  fe(c, tx, ty + s * 0.03, s * 0.05, s * 0.04, nt(S, '#6a4a2a', 0.5));
}
/* a pine of the hills, tiers of triangles */
function pine(c, x, G, s, S) { pr(c, x - s * 0.03, G - s * 0.2, s * 0.06, s * 0.2, nt(S, '#5a3a24', 0.5), 0.6); for (var k = 0; k < 3; k++) paper(c, poly([[x - s * (0.3 - k * 0.07), G - s * (0.15 + k * 0.25)], [x, G - s * (0.55 + k * 0.25)], [x + s * (0.3 - k * 0.07), G - s * (0.15 + k * 0.25)]]), nt(S, k % 2 ? '#2f5a3a' : '#3a6a44', 0.55), 0.8); }
/* potted chillies, or a potted fern, on the step */
function pot(c, x, G, s, S, kind, seed) {
  paper(c, poly([[x - s * 0.14, G - s * 0.24], [x + s * 0.14, G - s * 0.24], [x + s * 0.1, G], [x - s * 0.1, G]]), nt(S, kind === 2 ? '#3a6a8a' : '#b5653a', 0.45), 0.6);
  bush(c, x, G - s * 0.34, s * 0.2, [nt(S, '#3f7d45', 0.5), nt(S, '#55a04f', 0.5)], 6, seed);
  if (kind === 0) { var R = rnd(seed + 3); for (var i = 0; i < 6; i++) { var a = R() * TAU; fe(c, x + Math.cos(a) * s * 0.12, G - s * 0.34 + Math.sin(a) * s * 0.07, s * 0.018, s * 0.04, '#d42a1e', a); } }
  if (kind === 1) { for (var j = 0; j < 4; j++) fe(c, x + (j - 1.5) * s * 0.06, G - s * 0.42, s * 0.03, s * 0.03, nt(S, j % 2 ? '#f7c52c' : '#fbf6ea', 0.3)); }
}
function plantAt(c, kind, x, G, u, S, seed) {
  if (kind === 'frangipani') frangipani(c, x, G, u * 1.6, S, seed);
  else if (kind === 'banana') banana(c, x, G, u * 1.25, S, seed);
  else if (kind === 'palm') palm(c, x, G, u * 1.7, S, (seed % 2) ? 1 : -1);
  else if (kind === 'pine') pine(c, x, G, u * 1.5, S);
  else if (kind === 'bougain') { bougain(c, x - u * 0.4, G - u * 0.9, u * 0.8, u * 0.9, S, seed); }
  else pot(c, x, G, u * 0.9, S, kind === 'chilli' ? 0 : kind === 'flower' ? 1 : 2, seed);
}

/* ---------------------------------------------------------------- the spirit house
   san phra phum on its post: the little house, its tiered roof, a marigold garland, the red
   drink with its straw, little dancers and an elephant; incense curls up as x = A·sin(ky − ωt) */
function spiritHouse(c, x, G, s, S, seed) {
  var R = rnd(seed), body = pick(R, ['#e8c25a', '#f2ede0', '#c0392b', '#d9a441']), trim = '#e8b84a', post = pick(R, ['#f2ede0', '#c9a24a', '#8a5a3a']);
  pr(c, x - s * 0.04, G - s * 0.52, s * 0.08, s * 0.52, nt(S, post, 0.4), 1);
  pr(c, x - s * 0.26, G - s * 0.56, s * 0.52, s * 0.05, nt(S, '#8a5a3a', 0.4), 1);
  pr(c, x - s * 0.15, G - s * 0.78, s * 0.3, s * 0.22, nt(S, body, 0.35), 1);
  fr(c, x - s * 0.05, G - s * 0.72, s * 0.1, s * 0.16, nt(S, '#5a2a1a', 0.3));
  paper(c, poly([[x - s * 0.22, G - s * 0.78], [x, G - s * 0.98], [x + s * 0.22, G - s * 0.78]]), nt(S, body === '#c0392b' ? '#d9a441' : '#c0392b', 0.35), 1);
  paper(c, poly([[x - s * 0.15, G - s * 0.9], [x, G - s * 1.08], [x + s * 0.15, G - s * 0.9]]), nt(S, '#d9a441', 0.3), 1);
  ln(c, [[x, G - s * 1.08], [x, G - s * 1.16]], trim, Math.max(1, s * 0.02));
  [-1, 1].forEach(function (k) { ln(c, [[x + k * s * 0.22, G - s * 0.78], [x + k * s * 0.27, G - s * 0.84]], trim, Math.max(1, s * 0.025)); });
  marigolds(c, x - s * 0.16, x + s * 0.16, G - s * 0.76, s * 0.05, s);
  /* the offerings: the red drink, a dancer, an elephant, a flower cup */
  fr(c, x + s * 0.12, G - s * 0.66, s * 0.04, s * 0.1, '#e0302a'); ln(c, [[x + s * 0.14, G - s * 0.66], [x + s * 0.16, G - s * 0.71]], '#f2f2f2', 1);
  fe(c, x - s * 0.2, G - s * 0.6, s * 0.03, s * 0.04, '#f2ede0'); fe(c, x - s * 0.2, G - s * 0.65, s * 0.015, s * 0.015, '#f2ede0');
  fe(c, x + s * 0.21, G - s * 0.59, s * 0.035, s * 0.025, '#9a9aa0');
  fe(c, x - s * 0.1, G - s * 0.6, s * 0.03, s * 0.025, '#f29a1f');
  return { x: x - s * 0.02, y: G - s * 0.6, len: s * 0.14 };
}
function incense(c, I, t, k) {
  if (!I) return;
  var x = I.x, y = I.y, len = I.len; c.lineWidth = 1; c.lineCap = 'round';
  for (var i = 0; i < 3; i++) {
    var sx = x + (i - 1) * 2, tx = sx + (i - 1) * 1.2, ty = y - len;
    c.strokeStyle = '#b5532f'; c.beginPath(); c.moveTo(sx, y); c.lineTo(tx, ty); c.stroke();
    fe(c, tx, ty, 1.1, 1.1, '#ff7a3a');
    c.strokeStyle = 'rgba(240,236,228,.45)'; c.beginPath();
    for (var j = 0; j <= len * 1.8; j += 3) { var xx = tx + Math.sin(j * 0.11 - t / 650 + k + i) * (1 + j * 0.07); j ? c.lineTo(xx, ty - j) : c.moveTo(xx, ty); } c.stroke();
  }
}

/* ---------------------------------------------------------------- lights and cloth
   a khom (the Lanna lantern) on its cord, a pendulum, θ = θ₀·cos(√(g/L)·t + φ) */
function khom(c, x, y, len, r, t, k, col, night) {
  var th = 0.14 * Math.cos(Math.sqrt(9.8 / Math.max(0.3, len / 60)) * t / 1000 + k * 1.7), lx = x + Math.sin(th) * len, ly = y + Math.cos(th) * len;
  ln(c, [[x, y], [lx, ly]], 'rgba(40,20,30,.8)', 1);
  if (night) glow(c, lx, ly + r, r * 3.2, '255,170,80', 0.55 + 0.12 * Math.sin(t / 300 + k));
  fe(c, lx, ly + r, r * 0.9, r, col);
  fr(c, lx - r * 0.7, ly + r * 0.05, r * 1.4, r * 0.18, '#e8b84a'); fr(c, lx - r * 0.7, ly + r * 1.75, r * 1.4, r * 0.18, '#e8b84a');
  ln(c, [[lx, ly + r * 2], [lx + Math.sin(th) * r * 0.5, ly + r * 2.9]], '#e8b84a', Math.max(1, r * 0.25));
}
/* fairy lights on a catenary, y = a·cosh(x/a), each bulb twinkling on its own beat */
function fairy(c, xa, xb, y, sag, gap, t, night, cols) {
  var xm = (xa + xb) / 2, half = (xb - xa) / 2 || 1, a = half / 1.4, ch = Math.cosh(1.4) - 1;
  function cy(x) { return y + sag - sag * (Math.cosh((x - xm) / a) - 1) / ch; }
  c.strokeStyle = 'rgba(40,30,30,.75)'; c.lineWidth = 1; c.beginPath(); for (var x = xa; x <= xb; x += 6) x === xa ? c.moveTo(x, cy(x)) : c.lineTo(x, cy(x)); c.stroke();
  var i = 0; for (x = xa + gap / 2; x < xb; x += gap, i++) {
    var on = 0.55 + 0.45 * Math.sin(t / 380 + i * 2.1), col = cols[i % cols.length];
    if (night) glow(c, x, cy(x) + 2, gap * 0.55, col, 0.35 * on);
    c.fillStyle = 'rgba(' + col + ',' + (night ? 0.6 + 0.4 * on : 0.85) + ')'; c.beginPath(); c.arc(x, cy(x) + 2, 1.8, 0, TAU); c.fill();
  }
}
/* washing on a line, each piece a pendulum in the breeze */
var CLOTHES = ['#e5567f', '#f2f2f2', '#4d8fd1', '#f2c94c', '#7fe0a4', '#e0773a', '#9b6bd6', '#2c3e6b', '#d9342b', '#6cc3c1'];
function laundry(c, xa, xb, y, s, t, seed, S) {
  var R = rnd(seed), n = Math.max(2, Math.floor((xb - xa) / (s * 0.45)));
  ln(c, [[xa, y], [xb, y]], 'rgba(60,50,40,.8)', 1);
  for (var i = 0; i < n; i++) {
    var x = xa + (i + 0.5) * (xb - xa) / n, kind = Math.floor(R() * 3), col = nt(S, pick(R, CLOTHES), 0.45), sw = 0.08 * Math.sin(t / 700 + i * 1.3 + seed % 7);
    c.save(); c.translate(x, y); c.rotate(sw);
    if (kind === 0) fp(c, [[-s * 0.16, 0], [s * 0.16, 0], [s * 0.2, s * 0.08], [s * 0.12, s * 0.1], [s * 0.12, s * 0.34], [-s * 0.12, s * 0.34], [-s * 0.12, s * 0.1], [-s * 0.2, s * 0.08]], col);
    else if (kind === 1) { fr(c, -s * 0.12, 0, s * 0.24, s * 0.42, col); fr(c, -s * 0.12, s * 0.34, s * 0.24, s * 0.04, 'rgba(255,255,255,.4)'); }
    else fp(c, [[-s * 0.12, 0], [s * 0.12, 0], [s * 0.13, s * 0.36], [s * 0.02, s * 0.36], [0, s * 0.12], [-s * 0.02, s * 0.36], [-s * 0.13, s * 0.36]], col);
    fr(c, -1, -2, 2, 3, '#f2f2f2');
    c.restore();
  }
}

/* ---------------------------------------------------------------- wheels and animals
   vehicles side-on in unit space (s = the length), facing dir; wheels turn as θ = x / r */
function wheel(c, x, y, r, rot) {
  fe(c, x, y, r, r, '#1b1a20'); fe(c, x, y, r * 0.55, r * 0.55, '#9aa0a8');
  c.strokeStyle = '#5a5e66'; c.lineWidth = Math.max(0.8, r * 0.12); c.beginPath(); for (var k = 0; k < 3; k++) { var a = rot + k * TAU / 3; c.moveTo(x, y); c.lineTo(x + Math.cos(a) * r * 0.5, y + Math.sin(a) * r * 0.5); } c.stroke();
}
function vehicle(c, kind, x, y, s, dir, col, night, rot) {
  c.save(); c.translate(x, y); c.scale(dir, 1);
  c.shadowColor = 'rgba(0,0,0,.35)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5 * dir; c.shadowOffsetY = 2;
  var r = s * 0.075, hx = 0.5, hy = -0.2;
  if (kind === 'songthaew') {   /* the red truck with benches under its roof */
    fp(c, [[-0.5 * s, -0.1 * s], [-0.5 * s, -0.5 * s], [0.12 * s, -0.5 * s], [0.12 * s, -0.1 * s]], col);
    fp(c, [[-0.52 * s, -0.5 * s], [-0.5 * s, -0.56 * s], [0.14 * s, -0.56 * s], [0.14 * s, -0.5 * s]], mixc(col, '#000000', 0.25));
    fp(c, [[0.12 * s, -0.1 * s], [0.12 * s, -0.42 * s], [0.3 * s, -0.42 * s], [0.4 * s, -0.27 * s], [0.5 * s, -0.25 * s], [0.5 * s, -0.1 * s]], col);
    c.shadowColor = 'transparent';
    fr(c, -0.46 * s, -0.42 * s, 0.54 * s, 0.17 * s, night ? 'rgba(255,214,140,.55)' : 'rgba(40,30,40,.55)');
    for (var k = 0; k < 4; k++) fr(c, (-0.46 + k * 0.135) * s, -0.42 * s, 0.015 * s, 0.17 * s, col);
    fp(c, [[0.15 * s, -0.39 * s], [0.28 * s, -0.39 * s], [0.36 * s, -0.28 * s], [0.15 * s, -0.28 * s]], 'rgba(200,230,255,.7)');
    fr(c, -0.5 * s, -0.22 * s, s, 0.02 * s, '#e8b84a');
    wheel(c, -0.3 * s, -0.08 * s, r, rot); wheel(c, 0.32 * s, -0.08 * s, r, rot); hy = -0.2;
  } else if (kind === 'tuktuk') {
    fp(c, [[-0.42 * s, -0.12 * s], [-0.42 * s, -0.36 * s], [0.06 * s, -0.36 * s], [0.2 * s, -0.24 * s], [0.3 * s, -0.22 * s], [0.32 * s, -0.12 * s]], col);
    fp(c, [[-0.46 * s, -0.36 * s], [-0.44 * s, -0.6 * s], [0.16 * s, -0.6 * s], [0.2 * s, -0.36 * s]], '#2a2f3a');
    fp(c, [[-0.48 * s, -0.6 * s], [-0.46 * s, -0.66 * s], [0.18 * s, -0.66 * s], [0.2 * s, -0.6 * s]], mixc(col, '#ffffff', 0.2));
    c.shadowColor = 'transparent'; fr(c, -0.4 * s, -0.56 * s, 0.5 * s, 0.18 * s, night ? 'rgba(255,214,140,.4)' : 'rgba(255,255,255,.25)');
    fr(c, -0.42 * s, -0.2 * s, 0.74 * s, 0.025 * s, '#e8b84a');
    for (k = 0; k < 5; k++) fe(c, (-0.38 + k * 0.12) * s, -0.63 * s, 0.03 * s, 0.03 * s, k % 2 ? '#e8b84a' : '#f2f2f2');
    wheel(c, -0.3 * s, -0.08 * s, r * 1.05, rot); wheel(c, 0.24 * s, -0.08 * s, r * 1.05, rot); hx = 0.32; hy = -0.17;
  } else if (kind === 'car') {
    fp(c, [[-0.5 * s, -0.08 * s], [-0.5 * s, -0.24 * s], [-0.3 * s, -0.26 * s], [-0.18 * s, -0.42 * s], [0.2 * s, -0.42 * s], [0.34 * s, -0.26 * s], [0.5 * s, -0.22 * s], [0.5 * s, -0.08 * s]], col);
    c.shadowColor = 'transparent';
    fp(c, [[-0.15 * s, -0.38 * s], [0, -0.38 * s], [0, -0.27 * s], [-0.24 * s, -0.27 * s]], 'rgba(200,230,255,.7)'); fp(c, [[0.05 * s, -0.38 * s], [0.18 * s, -0.38 * s], [0.28 * s, -0.27 * s], [0.05 * s, -0.27 * s]], 'rgba(200,230,255,.7)');
    wheel(c, -0.3 * s, -0.07 * s, r * 1.05, rot); wheel(c, 0.3 * s, -0.07 * s, r * 1.05, rot); hy = -0.18;
  } else if (kind === 'scooter') {   /* the step-through: rear cowl and seat, floorboard, leg shield, bars */
    wheel(c, -0.32 * s, -0.14 * s, s * 0.14, rot); wheel(c, 0.36 * s, -0.14 * s, s * 0.14, rot);
    fp(c, [[-0.5 * s, -0.24 * s], [-0.47 * s, -0.36 * s], [-0.36 * s, -0.44 * s], [-0.04 * s, -0.44 * s], [0.02 * s, -0.26 * s], [0.17 * s, -0.24 * s], [0.25 * s, -0.56 * s], [0.31 * s, -0.62 * s], [0.36 * s, -0.6 * s], [0.34 * s, -0.4 * s], [0.46 * s, -0.24 * s], [0.4 * s, -0.17 * s], [0.26 * s, -0.17 * s], [-0.2 * s, -0.17 * s], [-0.46 * s, -0.17 * s]], col);
    c.shadowColor = 'transparent';
    fp(c, [[-0.4 * s, -0.44 * s], [-0.05 * s, -0.44 * s], [-0.07 * s, -0.5 * s], [-0.36 * s, -0.5 * s]], '#1f1a18');
    fr(c, -0.5 * s, -0.3 * s, 0.04 * s, 0.04 * s, '#e0302a');
    ln(c, [[0.31 * s, -0.62 * s], [0.29 * s, -0.72 * s]], '#2a2a2a', Math.max(1.2, s * 0.035)); ln(c, [[0.22 * s, -0.73 * s], [0.36 * s, -0.71 * s]], '#2a2a2a', Math.max(1.4, s * 0.04));
    fe(c, 0.36 * s, -0.6 * s, s * 0.03, s * 0.045, night ? '#fff2b0' : '#e8eef2'); hx = 0.38; hy = -0.6;
  } else if (kind === 'bike') {
    var wr = s * 0.2; wheel(c, -0.3 * s, -wr, wr, rot); wheel(c, 0.3 * s, -wr, wr, rot);
    c.shadowColor = 'transparent';
    ln(c, [[-0.3 * s, -wr], [-0.05 * s, -wr], [0.22 * s, -0.5 * s], [-0.12 * s, -0.5 * s], [-0.3 * s, -wr]], col, Math.max(1.4, s * 0.035));
    ln(c, [[-0.05 * s, -wr], [-0.14 * s, -0.56 * s]], col, Math.max(1.4, s * 0.035)); ln(c, [[0.3 * s, -wr], [0.2 * s, -0.62 * s], [0.12 * s, -0.64 * s]], col, Math.max(1.4, s * 0.035));
    fr(c, -0.2 * s, -0.59 * s, 0.13 * s, 0.035 * s, '#1f1a18');
    if (col === '#e8d9b8' || col === '#7fa8c9') { ln(c, [[0.24 * s, -0.56 * s], [0.4 * s, -0.56 * s], [0.38 * s, -0.44 * s], [0.26 * s, -0.44 * s]], '#8a5a2a', Math.max(1, s * 0.03)); }
    hx = 0.35; hy = -0.5;
  }
  c.shadowColor = 'transparent';
  if (night && kind !== 'bike') { var g = c.createLinearGradient(hx * s, hy * s, hx * s + s * 0.7, hy * s); g.addColorStop(0, 'rgba(255,240,180,.45)'); g.addColorStop(1, 'rgba(255,240,180,0)');
    c.fillStyle = g; c.beginPath(); c.moveTo(hx * s, hy * s); c.lineTo(hx * s + s * 0.7, hy * s - s * 0.1); c.lineTo(hx * s + s * 0.7, hy * s + s * 0.12); c.fill(); fe(c, hx * s, hy * s, s * 0.025, s * 0.025, '#fff6c0'); }
  c.restore();
}
var BODY = { songthaew: 1.75, tuktuk: 1.3, car: 1.7, scooter: 0.9, bike: 0.85 };
/* a soi dog, asleep (breathing, a slow swell) or sitting (tail wagging) */
function dog(c, x, y, s, col, sleep, t, dir) {
  dir = dir || 1;
  if (sleep) { var b = 1 + 0.04 * Math.sin(t / 900); fe(c, x, y - s * 0.12 * b, s * 0.32, s * 0.13 * b, col); fe(c, x + dir * s * 0.3, y - s * 0.09, s * 0.12, s * 0.09, col); fe(c, x + dir * s * 0.27, y - s * 0.14, s * 0.05, s * 0.07, mixc(col, '#000000', 0.25), dir * 0.6);
    ln(c, [[x - dir * s * 0.3, y - s * 0.08], [x - dir * s * 0.36, y - s * 0.02], [x - dir * s * 0.2, y - s * 0.01]], col, s * 0.05);
    if (Math.sin(t / 1800) > 0.3) { c.fillStyle = 'rgba(255,255,255,.7)'; c.font = '700 ' + Math.round(Math.max(8, s * 0.14)) + 'px ' + FONT; c.fillText('z', x + dir * s * 0.4, y - s * 0.3 - frac(t / 1800) * s * 0.1); }
    return; }
  fe(c, x, y - s * 0.2, s * 0.16, s * 0.2, col); fe(c, x + dir * s * 0.1, y - s * 0.44, s * 0.11, s * 0.1, col); fe(c, x + dir * s * 0.2, y - s * 0.42, s * 0.07, s * 0.05, col);
  fp(c, [[x + dir * s * 0.05, y - s * 0.5], [x + dir * s * 0.06, y - s * 0.62], [x + dir * s * 0.13, y - s * 0.52]], mixc(col, '#000000', 0.2));
  ln(c, [[x - dir * s * 0.14, y - s * 0.08], [x - dir * s * (0.28 + 0.05 * Math.sin(t / 140)), y - s * (0.22 + 0.06 * Math.cos(t / 140))]], col, s * 0.05);
  fe(c, x + dir * s * 0.24, y - s * 0.43, s * 0.015, s * 0.015, '#1a1a1a');
}
/* a cat on a step, its tail swishing as θ = 0.4·sin(ωt) */
function cat(c, x, y, s, col, t) {
  fe(c, x, y - s * 0.12, s * 0.13, s * 0.13, col); fe(c, x + s * 0.02, y - s * 0.3, s * 0.08, s * 0.075, col);
  fp(c, [[x - s * 0.05, y - s * 0.34], [x - s * 0.04, y - s * 0.42], [x, y - s * 0.36]], col); fp(c, [[x + s * 0.04, y - s * 0.36], [x + s * 0.09, y - s * 0.42], [x + s * 0.09, y - s * 0.33]], col);
  var a = 0.4 * Math.sin(t / 600); c.strokeStyle = col; c.lineWidth = Math.max(1.4, s * 0.04); c.lineCap = 'round'; c.beginPath(); c.moveTo(x - s * 0.1, y - s * 0.04); c.quadraticCurveTo(x - s * 0.28, y - s * 0.05, x - s * 0.26 + Math.sin(a) * s * 0.1, y - s * 0.22 - Math.cos(a) * s * 0.06); c.stroke();
  fe(c, x + s * 0.05, y - s * 0.31, s * 0.012, s * 0.012, '#c8e86a');
}
/* a hen pecking: her head dips on |sin ωt| */
function hen(c, x, y, s, t, k, col) {
  var p = Math.max(0, Math.sin(t / 400 + k * 2)), d = k % 2 ? 1 : -1;
  fe(c, x, y - s * 0.14, s * 0.14, s * 0.1, col); fp(c, [[x - d * s * 0.1, y - s * 0.16], [x - d * s * 0.24, y - s * 0.3], [x - d * s * 0.16, y - s * 0.12]], mixc(col, '#000000', 0.3));
  var hx = x + d * s * (0.13 + p * 0.06), hy = y - s * (0.26 - p * 0.18); fe(c, hx, hy, s * 0.055, s * 0.055, col); fe(c, hx, hy - s * 0.05, s * 0.025, s * 0.025, '#d9342b'); fp(c, [[hx + d * s * 0.04, hy - s * 0.01], [hx + d * s * 0.09, hy + s * 0.01], [hx + d * s * 0.04, hy + s * 0.02]], '#e8b84a');
  ln(c, [[x, y - s * 0.05], [x, y]], '#e8b84a', 1);
}
/* a moth round the lamp, on a small ellipse */
function moth(c, x, y, r, t) { var a = t / 260; glow(c, x, y, r * 2.4, '255,220,140', 0.5); fe(c, x, y, r * 0.45, r * 0.45, '#fff2c0'); var mx = x + Math.cos(a) * r * 1.3, my = y + Math.sin(a * 1.7) * r * 0.7; fe(c, mx - 1.5, my, 1.6, 1, 'rgba(230,220,200,.9)', 0.4 * Math.sin(t / 40)); fe(c, mx + 1.5, my, 1.6, 1, 'rgba(230,220,200,.9)', -0.4 * Math.sin(t / 40)); }

/* ---------------------------------------------------------------- people of the place */
function crew(S, n, mix, salt) { return K.town({ r: rnd((S.seed ^ salt) >>> 0 || 7), t: S.t, set: 'stay' }, n, mix); }
var GUESTS = { casual: 0.85, sin: 0.08, mohom: 0.07 };
/* a backpack on the back, a rolled mat on top */
function pack(c, me, h, dir, col) {
  var x = me.sh[0] - dir * h * 0.12, y0 = me.sh[1] - h * 0.06, y1 = me.hip[1] + h * 0.03;
  c.fillStyle = col; c.beginPath(); c.moveTo(x - h * 0.08, y0 + h * 0.03); c.quadraticCurveTo(x, y0 - h * 0.03, x + h * 0.08, y0 + h * 0.03); c.lineTo(x + h * 0.08, y1); c.lineTo(x - h * 0.08, y1); c.closePath(); c.fill();
  fe(c, x, y0 - h * 0.02, h * 0.1, h * 0.035, '#5a7a4a'); fr(c, x - h * 0.06, y0 + h * 0.12, h * 0.12, h * 0.02, 'rgba(0,0,0,.25)');
}
/* someone walking between xa and xb, over and over; feet keep to the ground, the stride
   phase p = 2π·x / (0.85h); they fade at the ends */
function walker(S, d, xa, xb, v, ph, y, h, carry, hold) {
  var c = S.c, len = Math.abs(xb - xa), T = len / (v * S.hh) * 1000, u = frac(S.t / T + ph), x = lerp(xa, xb, u), dir = xb > xa ? 1 : -1;
  var a = Math.min(1, u * 7, (1 - u) * 7); if (a <= 0.02) return null;
  d.dir = dir; d.skirt = d.skirt || 0;
  var P = K.walkP(x / (h * 0.85) * TAU * dir, false);
  if (carry === 'case') { P.arms[2] = -0.75; P.arms[3] = 0.05; }
  if (carry === 'bag' || carry === 'keys') { P.arms[0] = 0.25; P.arms[1] = 0.2; }
  c.save(); if (a < 1) c.globalAlpha = a;
  if (carry === 'case') { var hx = x - dir * h * 0.28, cx = hx - dir * h * 0.08; ln(c, [[x - dir * h * 0.16, y - h * 0.47], [cx, y - h * 0.3]], '#3a3a40', Math.max(1, h * 0.02)); pr(c, cx - h * 0.1, y - h * 0.32, h * 0.2, h * 0.3, hold || '#3a5a8a', 0.6); fe(c, cx - h * 0.06, y - h * 0.01, h * 0.025, h * 0.025, '#1b1a20'); fe(c, cx + h * 0.06, y - h * 0.01, h * 0.025, h * 0.025, '#1b1a20'); }
  var me = K.person(c, x, y, h, P, d);
  if (carry === 'pack') pack(c, me, h, dir, hold || '#c0562a');
  if (carry === 'bag') { var b = me.hand[0]; pr(c, b[0] - h * 0.06, b[1], h * 0.12, h * 0.15, hold || '#f2f2f2', 0.4); }
  if (carry === 'books') { var bb = me.hand[0]; fr(c, bb[0] - h * 0.05, bb[1] - h * 0.1, h * 0.09, h * 0.12, hold || '#4d8fd1'); }
  c.restore();
  return me;
}
/* a wai: the palms rise to the chest and the head bows, then back; ease in and out */
function waiP(u) { var k = ease(u); return { lean: 0.22 * k, seat: 0.47, legs: [0.04, 0, -0.04, 0], arms: [lerp(0.12, 0.9, k), lerp(0.1, 1.7, k), lerp(-0.1, 0.8, k), lerp(0.05, 1.8, k)] }; }
var STAND = { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [0.1, 0.12, -0.08, 0.08] };
var SIT = { lean: 0.08, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5], arms: [0.5, 0.9, 0.4, 1.0] };
/* a bell on the counter and its ring, circles growing as r = r₀ + vt */
function bell(c, x, y, s, t, per) {
  fe(c, x, y - s * 0.05, s * 0.12, s * 0.09, '#d9a441'); fr(c, x - s * 0.15, y - s * 0.02, s * 0.3, s * 0.03, '#8a6a3a'); fe(c, x, y - s * 0.15, s * 0.025, s * 0.025, '#f2d27a');
  var u = frac(t / per); if (u < 0.4) { c.strokeStyle = 'rgba(255,230,150,' + (1 - u / 0.4).toFixed(2) + ')'; c.lineWidth = 1.2; for (var k = 0; k < 2; k++) { c.beginPath(); c.arc(x, y - s * 0.08, s * (0.18 + u * 0.8 + k * 0.12), -2.4, -0.7); c.stroke(); } }
}
/* the arrival: a songthaew or tuk-tuk drives in, stops, the guests walk to the door with their
   bags, it drives on; x(t) eases in and out on a cycle of P seconds */
function arrival(S, A) {
  var c = S.c, u = S.hh, t = S.t / 1000, P = A.per, ph = frac(t / P + A.ph) * P, s = BODY[A.kind] * u, dir = A.dir, x, rot;
  var xin = A.stop - dir * (S.span * 0.7 + s), xout = A.stop + dir * (S.span * 0.7 + s);
  if (ph < 3) x = lerp(xin, A.stop, ease(ph / 3)); else if (ph < 10) x = A.stop; else if (ph < 13) x = lerp(A.stop, xout, Math.pow((ph - 10) / 3, 2)); else x = xout;
  rot = x / (s * 0.075);
  /* the guests, out at the back and across to the door */
  A.guests.forEach(function (g, i) {
    var g0 = 3.6 + i * 0.7, g1 = 9.2 + i * 0.3; if (ph < g0 || ph > g1) return;
    var f = (ph - g0) / (g1 - g0), gx = lerp(A.stop - dir * s * 0.45, A.door, f), gy = S.deck + u * (0.05 + i * 0.04);
    g.dir = A.door > gx ? 1 : -1; var al = Math.min(1, f * 6, (1 - f) * 6);
    c.save(); c.globalAlpha = al; var P0 = K.walkP(gx / (u * 0.8) * TAU, false); P0.arms[2] = -0.75; P0.arms[3] = 0.05;
    var cx = gx - g.dir * u * 0.34; ln(c, [[gx - g.dir * u * 0.15, gy - u * 0.47], [cx, gy - u * 0.3]], '#3a3a40', Math.max(1, u * 0.02)); pr(c, cx - u * 0.1, gy - u * 0.31, u * 0.2, u * 0.29, A.cases[i % A.cases.length], 0.6);
    var me = K.person(c, gx, gy, u * 0.94, P0, g); if (g.pack) pack(c, me, u * 0.94, g.dir, g.pack); c.restore();
  });
  if (ph < 13) vehicle(c, A.kind, x, S.deck + u * A.y, s, dir, A.col, S.night, rot);
}
function arrivalDeal(S, R, door, stop, dir, y, kind) {
  var P = S.place || {}, col = kind === 'songthaew' ? P.province === 'cr' ? pick(R, ['#2f6db5', '#f2ede0', '#2f8f5b']) : '#c0392b' : pick(R, ['#2f6db5', '#2f8f5b', '#c0392b', '#e8a23a', '#7a3aa8']);
  var g = crew(S, 2, GUESTS, 0x77); g.forEach(function (d) { d.garb = 'casual'; if (R() < 0.35) d.pack = pick(R, ['#c0562a', '#3a6a4a', '#2c3e6b']); });
  return { kind: kind, col: col, stop: stop, door: door, dir: dir, per: S.night ? 26 : 17, ph: R(), guests: g.slice(0, R() < 0.5 ? 1 : 2), cases: [pick(R, ['#3a5a8a', '#c0392b', '#2a2a2a', '#e8a23a', '#6a4a8a']), pick(R, ['#7a7a80', '#2f8f5b', '#e5567f'])], y: y == null ? 0.42 : y };
}
/* the ground: a street, a lane of red earth or a lawn, and a kerb */
function street(c, S, kind) {
  var u = S.hh, G = S.deck, col = kind === 'lawn' ? '#5f8a4e' : kind === 'earth' ? '#b0805a' : kind === 'brick' ? '#9a6a52' : '#6a6a70';
  K.ground(c, S.x0, S.x1, G, S.H, nt(S, col, 0.5));
  if (kind !== 'lawn') { fr(c, S.x0 - 4, G, S.span + 8, u * 0.12, nt(S, kind === 'earth' ? '#c9a070' : '#b8b2a6', 0.5)); fr(c, S.x0 - 4, G + u * 0.12, S.span + 8, 2, 'rgba(0,0,0,.18)'); }
  if (kind === 'road') { c.strokeStyle = nt(S, '#e8e2d0', 0.5); c.lineWidth = 2; c.setLineDash([u * 0.3, u * 0.3]); c.beginPath(); c.moveTo(S.x0, G + (S.H - G) * 0.62); c.lineTo(S.x1, G + (S.H - G) * 0.62); c.stroke(); c.setLineDash([]); }
}
/* the setting from the facts (K.setting), with the stage's own c; t = 0 so it holds still */
function settingOn(q, S) { var Q = {}; for (var k in S) Q[k] = S[k]; Q.c = q; Q.t = 0; K.setting(Q); }
/* the river, moving: glints along it, x = x₀ + vt, when the place is on its bank */
function riverGlints(S) {
  var P = S.place || {}; if (!P.river || P.river.m == null || P.river.m >= 400) return;
  var c = S.c, ry = S.deck + (S.H - S.deck) * 0.35, rh = (S.H - S.deck) * 0.45;
  c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 1.2; for (var k = 0; k < 7; k++) { var sx = S.x0 + frac(k * 0.37 + S.t / 9000) * S.span; c.beginPath(); c.moveTo(sx, ry + rh * (0.3 + (k % 3) * 0.2)); c.lineTo(sx + 9, ry + rh * (0.3 + (k % 3) * 0.2)); c.stroke(); }
}
function onRiver(P) { return !!(P.river && P.river.m != null && P.river.m < 400); }
/* rooms lighting one by one after dark: each window its own beat, on while sin(2πt/T + φ) > b */
function roomLights(S, L) {
  if (!S.night || !L.wins) return;
  var c = S.c, t = S.t / 1000;
  L.wins.forEach(function (w) { if (!w.anim) return; if (Math.sin(t / w.per * TAU + w.ph) > w.b) { fr(S.c, w.x, w.y, w.w, w.h, '#ffd27a'); fr(c, w.x, w.y + w.h * 0.6, w.w, w.h * 0.4, '#f5b85a'); } });
}
/* a grid of windows over floors; some lit after dark, a few on their own beats */
function windows(c, S, L, R, x, y, w, rows, cols, fh, o) {
  var pitch = w / cols, ww = pitch * (o.ww || 0.62), wh = fh * (o.wh || 0.56), out = L.wins = L.wins || [];
  for (var r0 = 0; r0 < rows; r0++) for (var k = 0; k < cols; k++) {
    var wx = x + k * pitch + (pitch - ww) / 2, wy = y + r0 * fh + fh * (o.top || 0.18), lit = R() < (o.lit || 0.45), anim = !lit && R() < 0.22;
    pane(c, S, wx, wy, ww, wh, lit, nt(S, o.frame || '#f2ede0', 0.5), R() < 0.5 ? pick(R, CLOTHES) : null, k + r0);
    if (anim) out.push({ x: wx, y: wy, w: ww, h: wh, anim: true, per: 6 + R() * 14, ph: R() * TAU, b: 0.1 + R() * 0.5 });
    if (o.ac && R() < 0.3) fr(c, wx + ww + pitch * 0.04, wy + wh * 0.5, pitch * 0.14, wh * 0.4, nt(S, '#c9ccd2', 0.5));
  }
}
/* a room seen through a big window: the bed made up, a pillow, the lamp on (what the place is for) */
function bedRoom(c, S, x, y, w, h, lit, cover, frame) {
  fr(c, x - 2, y - 2, w + 4, h + 4, frame);
  var wall = S.night ? lit ? '#f7c97a' : '#2a2f4a' : '#f3e2c2';
  fr(c, x, y, w, h, wall);
  if (S.night && lit) glow(c, x + w * 0.82, y + h * 0.45, h * 0.6, '255,200,120', 0.6);
  var by = y + h * 0.78, bx = x + w * 0.14, bw = w * 0.6;
  fr(c, bx - w * 0.04, by - h * 0.42, w * 0.06, h * 0.42, nt(S, '#6a4026', 0.3));          /* headboard */
  fr(c, bx, by - h * 0.18, bw, h * 0.18, nt(S, '#fbf6ea', 0.3));                            /* mattress */
  fr(c, bx + bw * 0.3, by - h * 0.2, bw * 0.7, h * 0.12, nt(S, cover, 0.3));                /* blanket */
  fe(c, bx + bw * 0.14, by - h * 0.22, bw * 0.12, h * 0.07, nt(S, '#ffffff', 0.25));        /* pillow */
  fr(c, x + w * 0.8, by - h * 0.12, w * 0.1, h * 0.12, nt(S, '#6a4026', 0.3));
  fp(c, [[x + w * 0.79, by - h * 0.3], [x + w * 0.91, by - h * 0.3], [x + w * 0.88, by - h * 0.42], [x + w * 0.82, by - h * 0.42]], S.night && lit ? '#fff2c0' : '#e8d2a0');
  fr(c, x, y + h - 2, w, 2, frame); fr(c, x + w / 2 - 1, y, 2, h * 0.08, frame);
}
/* bunks through a window: two tiers, a ladder, a curtain, someone asleep up top */
function bunkRoom(c, S, x, y, w, h, lit, cover, frame, k) {
  fr(c, x - 2, y - 2, w + 4, h + 4, frame);
  fr(c, x, y, w, h, S.night ? lit ? '#f2c27a' : '#262b46' : '#ece0c8');
  var wood = nt(S, '#7a4a2a', 0.3), bx = x + w * 0.1, bw = w * 0.72;
  fr(c, bx, y + h * 0.1, w * 0.04, h * 0.9, wood); fr(c, bx + bw, y + h * 0.1, w * 0.04, h * 0.9, wood);
  [0.42, 0.88].forEach(function (f, i) { fr(c, bx, y + h * f - h * 0.08, bw + w * 0.04, h * 0.08, nt(S, '#fbf6ea', 0.3)); fr(c, bx + bw * 0.35, y + h * f - h * 0.1, bw * 0.6, h * 0.06, nt(S, i ? cover : mixc(cover, '#ffffff', 0.4), 0.3)); fe(c, bx + bw * 0.14, y + h * f - h * 0.11, bw * 0.1, h * 0.04, '#ffffff'); });
  fe(c, bx + bw * 0.5, y + h * 0.3, bw * 0.22, h * 0.07, nt(S, cover, 0.25));  /* asleep up top */
  fe(c, bx + bw * 0.22, y + h * 0.29, h * 0.06, h * 0.06, '#d29a6e');
  for (var r = 0; r < 4; r++) fr(c, bx + bw - w * 0.1, y + h * (0.5 + r * 0.1), w * 0.12, 1.5, wood);
  ln(c, [[bx + bw - w * 0.08, y + h * 0.45], [bx + bw - w * 0.08, y + h]], wood, 1.4);
  if (k % 2) fr(c, x + w * 0.72, y, w * 0.28, h, nt(S, pick(rnd(k + 5), CLOTHES), 0.35));
  if (S.night && lit) glow(c, x + w * 0.2, y + h * 0.2, h * 0.4, '255,210,140', 0.5);
}

/* ---------------------------------------------------------------- hotel */
var WALLS = ['#f2ede0', '#efe3c8', '#e8d2b0', '#d9e2dc', '#f0d8c8', '#e2d6ea', '#cfe0e8', '#f5e6b8', '#e9e4da'];
var ACCENT = ['#a8432f', '#2f6b5a', '#2c3e6b', '#7a3a5a', '#c08a3a', '#3a5a7a', '#5a3a2a'];
var COVERS = ['#c0392b', '#2f6b5a', '#e8b84a', '#4d8fd1', '#9b6bd6', '#e5567f', '#f2ede0', '#2c3e6b'];
function hotelKind(P, R) {
  var n = nameOf(P);
  if (/camp|แคมป์|แค้มป์|glamp|tent|เต็นท์/.test(n)) return 'camp';
  if (/homestay|โฮมสเตย์|home stay|โฮมสเตร์/.test(n)) return 'homestay';
  if (onRiver(P) && (P.river.m < 200 || /river|ริมน้ำ|ริมปิง|ริมกก|ริมโขง/.test(n))) return 'river';
  if (/resort|รีสอร์ท|รีสอร์ต|villa|วิลล่า|spa\b|สปา/.test(n)) return P.hills && R() < 0.75 ? 'hill' : 'resort';
  if (/boutique|บูติก/.test(n) || P.oldCity) return 'boutique';
  if (/hotel|โรงแรม|\binn\b|residence|apartment|mansion|แมนชั่น|condo|tower|plaza|grand/.test(n)) return P.hills && R() < 0.4 ? 'hill' : 'city';
  if (P.hills) return R() < 0.75 ? 'hill' : 'resort';
  if (P.moo) return pick(R, ['resort', 'homestay', 'resort', 'city']);
  return pick(R, ['city', 'boutique', 'resort', 'city', 'homestay']);
}
/* the look a hotel page gets: everything dealt here, from the seed, so the still layer and
   the moving parts agree */
var LOOKS = {};
function look(S, scene, deal) {
  var k = [scene, S.seed, S.W, S.H, S.x0, S.x1, S.deck, S.hh, S.night ? 1 : 0].join('|');
  if (!LOOKS[k]) { var n = 0; for (var q in LOOKS) n++; if (n > 40) LOOKS = {}; var R = rnd((S.seed ^ 0x5a17) >>> 0 || 3); LOOKS[k] = deal(S, R, { R: R }); }
  return LOOKS[k];
}
function hotelDeal(S, R, L) {
  var u = S.hh, G = S.deck, sp = S.span, P = S.place || {};
  L.kind = S.variant && /^(city|resort|boutique|river|hill|camp|homestay)$/.test(S.variant) ? S.variant : hotelKind(P, R);
  L.flip = R() < 0.5; L.wall = pick(R, WALLS); L.accent = pick(R, ACCENT); L.signCol = pick(R, SIGNCOL); L.cover = pick(R, COVERS);
  L.dogCol = pick(R, ['#c9a06a', '#3a2a22', '#e8dcc8', '#8a6a4a', '#d9b98a']); L.animal = pick(R, ['dog', 'cat', 'none', 'dog']);
  L.lantern = pick(R, ['#d9342b', '#f29a1f', '#e8b84a', '#c2185b']);
  L.spirit = R() < 0.75; L.plants = [pick(R, ['frangipani', 'banana', 'palm', 'bougain']), pick(R, ['chilli', 'fern', 'flower']), pick(R, ['frangipani', 'palm', 'banana'])];
  var side = L.flip ? -1 : 1;   /* +1: the building to the left, arrivals from the right */
  function X(f) { return side > 0 ? S.x0 + sp * f : S.x1 - sp * f; }
  L.X = X; L.side = side;
  var k = L.kind;
  if (k === 'city') {
    L.bw = u * (2.5 + R() * 1.0); L.bx = side > 0 ? X(0.12) : X(0.12) - L.bw;
    L.top = G - u * (1.95 + R() * 0.33); L.lobby = u * 0.98;
    L.floors = clamp(Math.round((G - L.lobby - L.top) / (u * (0.19 + R() * 0.06))), 3, 7); L.fh = (G - L.lobby - L.top) / L.floors;
    L.style = pick(R, ['slab', 'balc', 'brick', 'fins', 'balc']); L.cols = Math.max(4, Math.floor(L.bw / (u * 0.36))); L.roof = pick(R, ['tank', 'lanna', 'garden', 'bar', 'flags']);
    L.door = L.bx + L.bw * (0.3 + R() * 0.4);
  } else if (k === 'boutique') {
    var oc = P.oldCity; side = L.side = oc ? -1 : side; X = L.X = side > 0 ? function (f) { return S.x0 + sp * f; } : function (f) { return S.x1 - sp * f; };
    L.bw = u * (2.3 + R() * 0.8); L.bx = side > 0 ? X(0.14) : X(0.14) - L.bw; L.storeys = R() < 0.55 ? 2 : 3; L.fh = u * (L.storeys === 2 ? 0.62 : 0.5);
    L.top = G - L.fh * L.storeys; L.roofKind = pick(R, ['hip', 'lanna', 'hip', 'flat']); L.shutters = pick(R, ['#2f6b5a', '#6a4026', '#2c3e6b', '#7a2a24', '#5a7a4a']);
    L.door = L.bx + L.bw * 0.5; L.wall = pick(R, ['#f2ede0', '#efe3c8', '#e8c9a0', '#d9e2dc', '#f5e6b8', '#f0d8c8']);
  } else if (k === 'resort') {
    var gw = signSize(S.c, P, u).w; L.gate = side > 0 ? S.x0 + Math.max(u * 1.2, gw / 2 + u * 0.55) : S.x1 - Math.max(u * 1.2, gw / 2 + u * 0.55);
    L.salaW = u * (1.9 + R() * 0.4); L.sala = side > 0 ? L.gate + gw / 2 + u * 0.35 : L.gate - gw / 2 - u * 0.35 - L.salaW;
    var room = side > 0 ? S.x1 - u * 0.9 - (L.sala + L.salaW + u * 0.5) : L.sala - u * 0.5 - (S.x0 + u * 0.9), pw = clamp(room - u * 1.3, u * 1.6, u * 3.2);
    L.villas = pw > u * 2.4 ? 2 + (R() < 0.5 ? 1 : 0) : 1; L.pool = { x: side > 0 ? L.sala + L.salaW + u * 0.5 : L.sala - u * 0.5 - pw, w: pw };
    L.poolShape = pick(R, ['rect', 'lagoon', 'rect']); L.umb = pick(R, ['#e5567f', '#f2c94c', '#2f8f5b', '#e0773a', '#f2ede0']);
    L.door = L.sala + L.salaW * 0.5; L.noArrive = true;
  } else if (k === 'river') {
    L.bw = u * (3.0 + R() * 0.8); L.bx = side > 0 ? X(0.14) : X(0.14) - L.bw; L.fh = u * 0.6; L.storeys = R() < 0.6 ? 2 : 3; L.top = G - L.fh * L.storeys;
    L.wood = R() < 0.55; L.door = L.bx + L.bw * 0.5; L.noArrive = true; L.boat = pick(R, ['#2f6db5', '#c0392b', '#2f8f5b', '#e8b84a']);
  } else if (k === 'hill') {
    L.slope = side; L.cabins = 3 + (R() < 0.5 ? 1 : 0); L.cabinKind = pick(R, ['aframe', 'teak', 'bamboo', 'glass']); L.lodge = side > 0 ? X(0.1) : X(0.1) - u * 2;
    L.door = L.lodge + u; L.bx = L.lodge; L.bw = u * 2;
  } else if (k === 'camp') {
    L.tentKind = pick(R, ['bell', 'aframe', 'dome']); L.tentCol = pick(R, ['#efe3c8', '#d9c9a0', '#c9a06a', '#e8d2b0', '#9aa86a', '#e0a070']);
    /* along the stage from the open end: the board, the tents, the fire, the hammock if it fits */
    var cw = signSize(S.c, P, u).w, cur = (side > 0 ? S.x0 : S.x1) + side * Math.max(u * 1.1, cw / 2 + u * 0.65), end = side > 0 ? S.x1 - u * 0.9 : S.x0 + u * 0.9;
    L.gate = cur; cur += side * (cw / 2 + u * 0.3);
    var av = (end - cur) * side, nt0 = clamp(Math.floor((av - u * 1.8 - (av > u * 5.2 ? u * 1.6 : 0)) / (u * 1.25)), 1, 3);
    L.tentAt = []; for (var ti = 0; ti < nt0; ti++) L.tentAt.push(cur + side * u * (0.65 + ti * 1.25)); cur += side * u * (0.65 + nt0 * 1.25);
    L.fire = cur + side * u * 0.5; cur += side * u * 1.4;
    L.hammock = (end - cur) * side > u * 1.4 ? [Math.min(cur, cur + side * u * 1.3), Math.max(cur, cur + side * u * 1.3)] : null;
    L.door = L.gate; L.noArrive = true;
  } else {   /* homestay: a teak house on posts */
    L.bw = u * (2.6 + R() * 0.6); L.bx = side > 0 ? X(0.14) : X(0.14) - L.bw; L.door = L.bx + L.bw * 0.5;
    L.posts = u * (0.42 + R() * 0.15); L.noArrive = R() < 0.5;
  }
  L.hit = null;
  /* the arrival stops clear of the building, on the open side */
  if (!L.noArrive) { var vk = R() < 0.5 ? 'songthaew' : 'tuktuk', vs = BODY[vk] * u, edge = side > 0 ? L.bx + L.bw : L.bx;
    L.stop = clamp(edge + side * (vs / 2 + u * 0.45), S.x0 + vs / 2, S.x1 - vs / 2);
    L.A = arrivalDeal(S, R, L.door, L.stop, -side, 0.5, vk); }
  L.staff = crew(S, 4, { sin: 0.5, mohom: 0.3, casual: 0.2 }, 0x3191);
  L.guests = crew(S, 4, GUESTS, 0x88a1);
  return L;
}
/* the city hotel: floors of rooms over a lit lobby, a canopy over the door */
function hotelCityStill(c, S, L, R) {
  var u = S.hh, G = S.deck, x = L.bx, w = L.bw, top = L.top, wall = nt(S, L.wall, 0.45), acc = nt(S, L.accent, 0.4), i;
  if (L.style === 'brick') wall = nt(S, '#b0604a', 0.45);
  pr(c, x, top, w, G - top, wall, 1.8);
  if (L.style === 'brick') { c.strokeStyle = 'rgba(0,0,0,.08)'; c.lineWidth = 1; for (var yy = top + 4; yy < G; yy += 4) { c.beginPath(); c.moveTo(x, yy); c.lineTo(x + w, yy); c.stroke(); } }
  fr(c, x, top, w, u * 0.06, acc); laiKham(c, x, x + w, top + u * 0.03, u * 0.05);
  var fy = G - L.lobby;
  /* a room cutaway on the first floor: the bed says what the building is for */
  var bedK = Math.floor(R() * L.cols);
  windows(c, S, L, R, x, top + u * 0.06, w, L.floors, L.cols, (fy - top - u * 0.06) / L.floors, { frame: L.style === 'fins' ? '#3a3f4a' : '#f2ede0', lit: 0.4, ac: L.style !== 'fins', wh: L.style === 'balc' ? 0.62 : 0.55 });
  var fh = (fy - top - u * 0.06) / L.floors, pitch = w / L.cols;
  if (L.style === 'balc') for (i = 0; i < L.floors; i++) { var by = top + u * 0.06 + (i + 1) * fh - fh * 0.12; fr(c, x - u * 0.04, by, w + u * 0.08, fh * 0.1, nt(S, '#d8d0c0', 0.45)); c.strokeStyle = nt(S, '#5a5a60', 0.4); c.lineWidth = 1; for (var bx = x; bx < x + w; bx += u * 0.05) { c.beginPath(); c.moveTo(bx, by); c.lineTo(bx, by - fh * 0.28); c.stroke(); } fr(c, x - u * 0.04, by - fh * 0.3, w + u * 0.08, 1.5, nt(S, '#5a5a60', 0.4));
    for (var k2 = 0; k2 < L.cols; k2++) if (R() < 0.3) bush(c, x + k2 * pitch + pitch * 0.2, by - fh * 0.1, fh * 0.2, [nt(S, '#3f7d45', 0.5), nt(S, '#d6337f', 0.5)], 4, i * 9 + k2); }
  if (L.style === 'fins') for (i = 0; i <= L.cols; i++) fr(c, x + i * pitch - u * 0.02, top + u * 0.06, u * 0.04, fy - top - u * 0.06, nt(S, L.accent, 0.4));
  bedRoom(c, S, x + bedK * pitch + pitch * 0.08, fy - fh * 0.92, pitch * 0.84, fh * 0.78, true, L.cover, nt(S, '#f2ede0', 0.4));
  /* the lobby, lit; its counter and bell are drawn live */
  var ly = fy, lx0 = x + u * 0.12, lx1 = x + w - u * 0.12;
  fr(c, lx0, ly + u * 0.06, lx1 - lx0, L.lobby - u * 0.06, L.st === 'closed' ? '#2a2c38' : S.night ? '#ffd690' : '#f6e2b8');
  if (L.st !== 'closed') { if (S.night) glow(c, (lx0 + lx1) / 2, G - L.lobby * 0.4, w * 0.6, '255,200,120', 0.55); fr(c, lx0, G - u * 0.08, lx1 - lx0, u * 0.08, '#c99a52'); for (i = 0; i < 3; i++) fe(c, lx0 + (lx1 - lx0) * (0.2 + i * 0.3), ly + u * 0.14, u * 0.05, u * 0.03, '#fff2c0'); }
  else shutter(c, lx0, ly + u * 0.06, lx1 - lx0, L.lobby - u * 0.06, S);
  for (i = 0; i <= 4; i++) fr(c, lx0 + (lx1 - lx0) * i / 4 - 1, ly + u * 0.06, 2, L.lobby - u * 0.06, nt(S, '#3a3f4a', 0.3));
  /* the canopy over the door, gold-edged */
  var cw = u * 1.3; pr(c, L.door - cw / 2, ly - u * 0.02, cw, u * 0.1, acc, 1.4); fr(c, L.door - cw / 2, ly + u * 0.07, cw, 2, '#e8b84a');
  fr(c, L.door - cw / 2 + u * 0.05, ly + u * 0.08, 3, L.lobby - u * 0.08, nt(S, '#d8d0c0', 0.4)); fr(c, L.door + cw / 2 - u * 0.05 - 3, ly + u * 0.08, 3, L.lobby - u * 0.08, nt(S, '#d8d0c0', 0.4));
  /* the roof */
  if (L.roof === 'tank') { [0.2, 0.75].forEach(function (f) { var tx = x + w * f; fr(c, tx - u * 0.12, top - u * 0.08, u * 0.02, u * 0.08, nt(S, '#6a6a70', 0.4)); fr(c, tx + u * 0.1, top - u * 0.08, u * 0.02, u * 0.08, nt(S, '#6a6a70', 0.4)); pr(c, tx - u * 0.14, top - u * 0.26, u * 0.28, u * 0.18, nt(S, '#5a8ab0', 0.4), 0.8); }); }
  if (L.roof === 'lanna') lannaRoof(c, x + w / 2, w * 0.7, top, Math.min(u * 0.5, top - (G - u * 2.3)), nt(S, '#a8432f', 0.45));
  if (L.roof === 'garden') for (i = 0; i < 4; i++) bush(c, x + w * (0.15 + i * 0.23), top - u * 0.06, u * 0.12, [nt(S, '#3f7d45', 0.5), nt(S, '#5aa35a', 0.5)], 5, i + 40);
  if (L.roof === 'bar') { pr(c, x + w * 0.55, top - u * 0.2, w * 0.38, u * 0.2, nt(S, '#6a4026', 0.4), 0.8); paper(c, poly([[x + w * 0.5, top - u * 0.2], [x + w * 0.74, top - u * 0.36], [x + w * 0.98, top - u * 0.2]]), nt(S, '#a8432f', 0.45), 0.8); }
  if (L.roof === 'flags') [0.3, 0.5, 0.7].forEach(function (f) { var fx = x + w * f; ln(c, [[fx, top], [fx, top - u * 0.4]], '#c9ccd2', 1.2); });
  return [{ k: 'place', x0: x, x1: x + w, y0: top, y1: G }];
}
/* the boutique: two or three storeys, teak shutters thrown open, a wooden balcony,
   bougainvillea over the rail, a courtyard step */
function hotelBoutiqueStill(c, S, L, R) {
  var u = S.hh, G = S.deck, x = L.bx, w = L.bw, top = L.top, wall = nt(S, L.wall, 0.45), sh = nt(S, L.shutters, 0.4), i, k;
  pr(c, x, top, w, G - top, wall, 1.6);
  fr(c, x, G - u * 0.12, w, u * 0.12, nt(S, '#b8a888', 0.45));
  var cols = Math.max(3, Math.floor(w / (u * 0.62)));
  for (k = 1; k < L.storeys; k++) {
    var fy = G - k * L.fh;
    fr(c, x - u * 0.03, fy - u * 0.04, w + u * 0.06, u * 0.05, nt(S, '#6a4026', 0.4));
    for (i = 0; i < cols; i++) {
      var wx = x + (i + 0.5) * w / cols - u * 0.13, wy = fy - L.fh * 0.78, ww = u * 0.26, wh = L.fh * 0.56, lit = R() < 0.5;
      if (k === 1 && i === Math.floor(cols / 2)) bedRoom(c, S, wx - u * 0.04, wy, ww + u * 0.08, wh, true, L.cover, nt(S, '#f2ede0', 0.3));
      else pane(c, S, wx, wy, ww, wh, lit, nt(S, '#6a4026', 0.3), R() < 0.4 ? pick(R, CLOTHES) : null, i);
      if (S.night && lit) L.wins = L.wins || [];
      if (!(S.night && L.st === 'closed')) { fr(c, wx - ww * 0.42, wy, ww * 0.38, wh, sh); fr(c, wx + ww * 1.04, wy, ww * 0.38, wh, sh); c.strokeStyle = 'rgba(0,0,0,.25)'; c.lineWidth = 1; for (var s2 = 1; s2 < 5; s2++) { c.beginPath(); c.moveTo(wx - ww * 0.42, wy + wh * s2 / 5); c.lineTo(wx - ww * 0.04, wy + wh * s2 / 5); c.moveTo(wx + ww * 1.04, wy + wh * s2 / 5); c.lineTo(wx + ww * 1.42, wy + wh * s2 / 5); c.stroke(); } }
    }
    if (k === 1) { /* the balcony rail, turned balusters */
      var ry = fy - u * 0.05; fr(c, x + w * 0.08, ry - u * 0.22, w * 0.84, u * 0.03, nt(S, '#6a4026', 0.35));
      for (var bx = x + w * 0.08; bx <= x + w * 0.92; bx += u * 0.07) fr(c, bx, ry - u * 0.2, u * 0.025, u * 0.2, nt(S, '#7a4a2a', 0.35));
      bougain(c, L.side > 0 ? x + w * 0.62 : x + w * 0.05, ry - u * 0.3, w * 0.34, u * 0.75, S, S.seed + 11);
    }
  }
  /* the ground floor: arched teak doors open on a warm room */
  var dw = u * 0.62, dx = L.door - dw / 2, dh = L.fh * 0.86;
  if (L.st === 'closed') shutter(c, dx, G - dh, dw, dh, S, '#8a8f96');
  else { fr(c, dx, G - dh, dw, dh, S.night ? '#ffd690' : '#f3dcb0'); if (S.night) glow(c, L.door, G - dh * 0.5, dw * 1.4, '255,200,120', 0.5); fr(c, dx - dw * 0.3, G - dh, dw * 0.28, dh, sh); fr(c, dx + dw * 1.02, G - dh, dw * 0.28, dh, sh); }
  c.fillStyle = wall; c.beginPath(); c.moveTo(dx - 2, G - dh - 2); c.lineTo(dx + dw + 2, G - dh - 2); c.lineTo(dx + dw + 2, G - dh + dw * 0.2); c.quadraticCurveTo(L.door, G - dh - dw * 0.2, dx - 2, G - dh + dw * 0.2); c.closePath(); c.fill();
  for (i = 0; i < 2; i++) { var gx = i ? x + w * 0.8 : x + w * 0.08; pane(c, S, gx, G - L.fh * 0.75, u * 0.32, L.fh * 0.5, L.st !== 'closed', nt(S, '#6a4026', 0.3), null, i); }
  /* the roof */
  laiKham(c, x, x + w, top - u * 0.02, u * 0.05);
  if (L.roofKind === 'hip') hipRoof(c, x + w / 2, w * 1.02, top, u * 0.42, nt(S, '#b5533a', 0.45));
  else if (L.roofKind === 'lanna') lannaRoof(c, x + w / 2, w * 0.95, top, u * 0.55, nt(S, '#8a3a2a', 0.45));
  else { pr(c, x - u * 0.05, top - u * 0.1, w + u * 0.1, u * 0.1, nt(S, '#d8d0c0', 0.45), 0.8); bush(c, x + w * 0.3, top - u * 0.14, u * 0.12, [nt(S, '#3f7d45', 0.5)], 4, 7); }
  return [{ k: 'place', x0: x, x1: x + w, y0: top - u * 0.4, y1: G }];
}
/* the resort: a reception sala under a Lanna roof, villas behind, the pool in front with loungers */
function hotelResortStill(c, S, L, R) {
  var u = S.hh, G = S.deck, i, roof = nt(S, pick(R, ['#8a3a2a', '#6a4026', '#a8432f', '#5a3a2a']), 0.45), wood = nt(S, '#7a4a2a', 0.4);
  /* the villas behind, smaller, along the back */
  for (i = 0; i < L.villas; i++) {
    var vx = L.pool.x + L.pool.w * (0.15 + i * 0.7 / Math.max(1, L.villas - 1)) - u * 0.4, vw = u * 0.95, vy = G - u * 0.18;
    pr(c, vx, vy - u * 0.42, vw, u * 0.42, nt(S, L.wall, 0.5), 1);
    bedRoom(c, S, vx + vw * 0.2, vy - u * 0.36, vw * 0.6, u * 0.28, R() < 0.7, pick(R, COVERS), nt(S, '#6a4026', 0.4));
    lannaRoof(c, vx + vw / 2, vw * 1.1, vy - u * 0.42, u * 0.42, roof);
  }
  /* the sala */
  var sx = L.sala, sw = L.salaW, top = G - u * 1.55;
  K.sala(c, sx, sx + sw, G, top, S.night, roof);
  fr(c, sx + sw * 0.1, G - u * 0.06, sw * 0.8, u * 0.06, nt(S, '#c99a52', 0.4));
  /* the pool: water, its coping, steps */
  var px = L.pool.x, pw = L.pool.w, py = G + u * 0.1, ph = Math.min(S.H - G - u * 0.12, u * 0.48);
  if (L.poolShape === 'lagoon') paper(c, function (q) { q.beginPath(); q.ellipse(px + pw / 2, py + ph / 2, pw / 2, ph / 2, 0, 0, TAU); }, nt(S, '#e8e2d0', 0.4), 0.6);
  else pr(c, px - u * 0.06, py - u * 0.05, pw + u * 0.12, ph + u * 0.1, nt(S, '#e8e2d0', 0.4), 0.6);
  var g = c.createLinearGradient(0, py, 0, py + ph); g.addColorStop(0, S.night ? '#2a6a9a' : '#5fc6e8'); g.addColorStop(1, S.night ? '#1a4a7a' : '#2f9ac9'); c.fillStyle = g;
  if (L.poolShape === 'lagoon') { c.beginPath(); c.ellipse(px + pw / 2, py + ph / 2, pw / 2 - u * 0.06, ph / 2 - u * 0.05, 0, 0, TAU); c.fill(); } else c.fillRect(px, py, pw, ph);
  if (S.night) glow(c, px + pw / 2, py + ph / 2, pw * 0.5, '120,200,255', 0.35);
  L.water = { x: px, y: py, w: pw, h: ph };
  /* loungers and a parasol at the pool's side */
  var lx = px + pw + u * 0.15;
  if (lx + u * 1.1 > S.x1 - u * 0.8) lx = px - u * 1.2;
  L.lounge = lx;
  for (i = 0; i < 2; i++) { var lo = lx + i * u * 0.55; fp(c, [[lo, G - u * 0.1], [lo + u * 0.4, G - u * 0.1], [lo + u * 0.48, G - u * 0.26], [lo + u * 0.44, G - u * 0.27], [lo + u * 0.38, G - u * 0.13], [lo, G - u * 0.13]], nt(S, '#f2ede0', 0.4)); ln(c, [[lo + u * 0.04, G - u * 0.1], [lo + u * 0.04, G]], wood, 1.5); ln(c, [[lo + u * 0.38, G - u * 0.1], [lo + u * 0.38, G]], wood, 1.5); }
  ln(c, [[lx + u * 0.5, G], [lx + u * 0.5, G - u * 0.95]], wood, 2);
  paper(c, function (q) { q.beginPath(); q.moveTo(lx - u * 0.05, G - u * 0.82); q.quadraticCurveTo(lx + u * 0.5, G - u * 1.18, lx + u * 1.05, G - u * 0.82); q.closePath(); }, nt(S, L.umb, 0.4), 1);
  return [{ k: 'place', x0: Math.min(sx, px), x1: Math.max(sx + sw, px + pw), y0: top - u * 0.4, y1: G + u * 0.5 }];
}
/* the riverside hotel: a long teak house or a white one, a terrace with tables over the bank */
function hotelRiverStill(c, S, L, R) {
  var u = S.hh, G = S.deck, x = L.bx, w = L.bw, top = L.top, wall = nt(S, L.wood ? '#8a5a34' : L.wall, 0.45), i, k;
  pr(c, x, top, w, G - top, wall, 1.6);
  if (L.wood) { c.strokeStyle = 'rgba(0,0,0,.15)'; c.lineWidth = 1; for (var px = x + 5; px < x + w; px += 5) { c.beginPath(); c.moveTo(px, top); c.lineTo(px, G); c.stroke(); } }
  var cols = Math.max(3, Math.floor(w / (u * 0.55)));
  for (k = 1; k < L.storeys; k++) { var fy = G - k * L.fh; fr(c, x - u * 0.05, fy - u * 0.03, w + u * 0.1, u * 0.05, nt(S, '#5a3a24', 0.4));
    for (i = 0; i < cols; i++) { var wx = x + (i + 0.5) * w / cols - u * 0.15; if (k === 1 && i === 1) bedRoom(c, S, wx, fy - L.fh * 0.8, u * 0.34, L.fh * 0.56, true, L.cover, nt(S, '#f2ede0', 0.3)); else pane(c, S, wx, fy - L.fh * 0.8, u * 0.3, L.fh * 0.56, R() < 0.5, nt(S, '#f2ede0', 0.35), R() < 0.4 ? pick(R, CLOTHES) : null, i); }
    var ry = fy - u * 0.04; for (var bx = x; bx <= x + w; bx += u * 0.08) fr(c, bx, ry - u * 0.18, 2, u * 0.18, nt(S, '#5a3a24', 0.35)); fr(c, x, ry - u * 0.2, w, 2.5, nt(S, '#5a3a24', 0.35)); }
  var gy = G - L.fh; fr(c, x + u * 0.1, gy + u * 0.08, w - u * 0.2, L.fh - u * 0.08, L.st === 'closed' ? '#2a2c38' : S.night ? '#ffd690' : '#f3dcb0');
  if (L.st !== 'closed' && S.night) glow(c, x + w / 2, G - L.fh * 0.5, w * 0.5, '255,200,120', 0.45);
  for (i = 0; i <= 5; i++) fr(c, x + u * 0.1 + (w - u * 0.2) * i / 5 - 1.5, gy + u * 0.08, 3, L.fh - u * 0.08, nt(S, '#5a3a24', 0.3));
  if (L.wood) gable(c, x + w / 2, w * 1.05, top, u * 0.5, nt(S, '#6a3a24', 0.45)); else hipRoof(c, x + w / 2, w * 1.04, top, u * 0.4, nt(S, '#a8432f', 0.45));
  /* the terrace deck over the bank, a table and parasol */
  var tx0 = L.side > 0 ? x + w : x - u * 2.1, tx1 = tx0 + u * 2.1;
  fr(c, tx0, G - u * 0.04, tx1 - tx0, u * 0.08, nt(S, '#8a5a34', 0.45)); for (var p2 = tx0; p2 <= tx1; p2 += u * 0.5) fr(c, p2, G, u * 0.05, S.H - G, nt(S, '#5a3a24', 0.5));
  for (i = 0; i < 2; i++) { var tx = tx0 + u * (0.5 + i * 1.0); fr(c, tx - u * 0.18, G - u * 0.3, u * 0.36, u * 0.04, nt(S, '#f2ede0', 0.4)); ln(c, [[tx, G - u * 0.3], [tx, G]], nt(S, '#5a3a24', 0.4), 1.5); }
  L.terrace = [tx0, tx1];
  return [{ k: 'place', x0: Math.min(x, tx0), x1: Math.max(x + w, tx1), y0: top - u * 0.5, y1: G }];
}
/* the hill resort: a slope, cabins up it, a lodge at the foot, pines */
function hotelHillStill(c, S, L, R) {
  var u = S.hh, G = S.deck, s = L.slope, x0 = S.x0, x1 = S.x1, i, h = u * 1.25;
  function sy(x) { var f = (x - x0) / (x1 - x0); f = s > 0 ? f : 1 - f; return G - h * Math.pow(f, 1.3) - u * 0.04; }
  paper(c, function (q) { q.beginPath(); q.moveTo(x0 - 6, G + 2); for (var x = x0 - 6; x <= x1 + 6; x += 10) q.lineTo(x, sy(x) + Math.sin(x * 0.05) * 2); q.lineTo(x1 + 6, G + 2); q.closePath(); }, nt(S, '#5f8a4e', 0.5), 1.4);
  /* the steps up */
  c.strokeStyle = nt(S, '#c9a070', 0.5); c.lineWidth = Math.max(2, u * 0.05); c.beginPath();
  for (var x = L.lodge + u; s > 0 ? x < x1 - u : x > x0 + u; x += s * u * 0.2) { var yy = sy(x) + u * 0.06 + Math.sin(x * 0.03) * u * 0.04; x === L.lodge + u ? c.moveTo(x, yy) : c.lineTo(x, yy); } c.stroke();
  L.cab = [];
  for (i = 0; i < L.cabins; i++) {
    var cx = L.lodge + u + s * u * (1.6 + i * 1.45), cy = sy(cx) + u * 0.04, cw = u * 0.75;
    if (cx < x0 + u * 0.6 || cx > x1 - u * 0.9) continue;
    fr(c, cx - cw * 0.45, cy, u * 0.04, u * 0.12, nt(S, '#5a3a24', 0.5)); fr(c, cx + cw * 0.41, cy, u * 0.04, u * 0.12, nt(S, '#5a3a24', 0.5));
    if (L.cabinKind === 'aframe') { paper(c, poly([[cx - cw * 0.55, cy], [cx, cy - u * 0.75], [cx + cw * 0.55, cy]]), nt(S, '#6a3a24', 0.45), 1); pane(c, S, cx - cw * 0.16, cy - u * 0.36, cw * 0.32, u * 0.3, true, nt(S, '#f2ede0', 0.3), null, i); }
    else { pr(c, cx - cw / 2, cy - u * 0.38, cw, u * 0.38, nt(S, L.cabinKind === 'bamboo' ? '#c9a86a' : L.cabinKind === 'glass' ? '#3a4a5a' : '#8a5a34', 0.45), 1);
      if (L.cabinKind === 'glass') bedRoom(c, S, cx - cw * 0.4, cy - u * 0.33, cw * 0.8, u * 0.28, true, pick(R, COVERS), nt(S, '#2a2a2a', 0.3)); else pane(c, S, cx - cw * 0.2, cy - u * 0.3, cw * 0.4, u * 0.2, R() < 0.8, nt(S, '#f2ede0', 0.3), pick(R, CLOTHES), i);
      if (L.cabinKind === 'bamboo') paper(c, poly([[cx - cw * 0.65, cy - u * 0.36], [cx, cy - u * 0.72], [cx + cw * 0.65, cy - u * 0.36]]), nt(S, '#b8a070', 0.45), 1); else gable(c, cx, cw * 1.15, cy - u * 0.38, u * 0.34, nt(S, '#6a3a24', 0.45)); }
    L.cab.push([cx, cy]);
  }
  for (i = 0; i < 4; i++) { var px = x0 + (x1 - x0) * (0.08 + i * 0.27 + R() * 0.08); pine(c, px, sy(px) + u * 0.05, u * (0.6 + R() * 0.4), S); }
  /* the lodge at the foot */
  var lx = L.lodge, lw = u * 2; pr(c, lx, G - u * 0.62, lw, u * 0.62, nt(S, '#8a5a34', 0.45), 1.4);
  fr(c, lx + u * 0.15, G - u * 0.5, lw - u * 0.3, u * 0.5, L.st === 'closed' ? '#2a2c38' : S.night ? '#ffd690' : '#f3dcb0');
  if (S.night && L.st !== 'closed') glow(c, lx + lw / 2, G - u * 0.3, lw * 0.6, '255,200,120', 0.5);
  for (i = 0; i <= 4; i++) fr(c, lx + u * 0.15 + (lw - u * 0.3) * i / 4 - 1.5, G - u * 0.5, 3, u * 0.5, nt(S, '#5a3a24', 0.3));
  lannaRoof(c, lx + lw / 2, lw * 1.05, G - u * 0.62, u * 0.62, nt(S, '#6a3a24', 0.45));
  return [{ k: 'place', x0: Math.min(lx, x0 + u), x1: Math.max(lx + lw, x1 - u), y0: G - u * 1.9, y1: G }];
}
/* the camp: bell tents or A-frames on a lawn, a fire ring with logs */
function hotelCampStill(c, S, L, R) {
  var u = S.hh, G = S.deck, i, sp = S.span;
  for (i = 0; i < L.tentAt.length; i++) {
    var tx = L.tentAt[i], tw = u * (0.95 + R() * 0.2), col = nt(S, mixc(L.tentCol, '#ffffff', R() * 0.2), 0.45), lit = S.night && R() < 0.8;
    if (L.tentKind === 'bell') { paper(c, function (q) { q.beginPath(); q.moveTo(tx - tw / 2, G); q.lineTo(tx - tw / 2, G - u * 0.3); q.lineTo(tx, G - u * 0.9); q.lineTo(tx + tw / 2, G - u * 0.3); q.lineTo(tx + tw / 2, G); q.closePath(); }, col, 1.2); fp(c, [[tx - tw * 0.14, G], [tx, G - u * 0.5], [tx + tw * 0.14, G]], lit ? '#ffcf7a' : nt(S, '#5a4a3a', 0.4)); ln(c, [[tx, G - u * 0.9], [tx, G - u * 1.0]], nt(S, '#6a4026', 0.4), 2); }
    else if (L.tentKind === 'aframe') { paper(c, poly([[tx - tw / 2, G], [tx, G - u * 0.75], [tx + tw / 2, G]]), col, 1.2); fp(c, [[tx - tw * 0.18, G], [tx, G - u * 0.5], [tx + tw * 0.18, G]], lit ? '#ffcf7a' : nt(S, '#5a4a3a', 0.4)); }
    else { paper(c, function (q) { q.beginPath(); q.ellipse(tx, G, tw / 2, u * 0.6, 0, Math.PI, TAU); q.closePath(); }, col, 1.2); fp(c, [[tx - tw * 0.15, G], [tx - tw * 0.12, G - u * 0.35], [tx + tw * 0.12, G - u * 0.35], [tx + tw * 0.15, G]], lit ? '#ffcf7a' : nt(S, '#5a4a3a', 0.4)); }
    if (lit) glow(c, tx, G - u * 0.2, tw * 0.6, '255,190,100', 0.5);
  }
  var fx = L.fire;
  fe(c, fx, G + u * 0.08, u * 0.32, u * 0.07, nt(S, '#6a6a70', 0.4)); fe(c, fx, G + u * 0.07, u * 0.24, u * 0.05, '#2a1a12');
  [-1, 1].forEach(function (d) { pr(c, fx + d * u * 0.7 - u * 0.25, G - u * 0.05, u * 0.5, u * 0.1, nt(S, '#6a4026', 0.45), 0.6); });
  /* two trees for the hammock */
  if (L.hammock) [L.hammock[0], L.hammock[1]].forEach(function (x) { pr(c, x - u * 0.05, G - u * 1.3, u * 0.1, u * 1.3, nt(S, '#5a3a24', 0.5), 1); bush(c, x, G - u * 1.4, u * 0.4, [nt(S, '#2f5a3a', 0.5), nt(S, '#3f7d45', 0.5)], 7, x | 0); });
  return [{ k: 'place', x0: S.x0 + u * 0.5, x1: S.x1 - u * 0.5, y0: G - u * 1.1, y1: G }];
}
/* the homestay: a teak house on posts (ruean kalae), stairs up, the space below it for living */
function homestayStill(c, S, L, R) {
  var u = S.hh, G = S.deck, x = L.bx, w = L.bw, fl = G - L.posts, top = fl - u * 0.62, teak = nt(S, pick(R, ['#8a5a34', '#7a4a2a', '#9a6a3a', '#6a4026']), 0.45), i;
  for (i = 0; i < 5; i++) pr(c, x + i * (w - u * 0.1) / 4, fl, u * 0.1, L.posts, nt(S, '#5a3a24', 0.5), 0.8);
  pr(c, x - u * 0.15, fl - u * 0.04, w + u * 0.3, u * 0.08, nt(S, '#5a3a24', 0.45), 1);
  pr(c, x, top, w, fl - top, teak, 1.4);
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; for (var px = x + 4; px < x + w; px += 4) { c.beginPath(); c.moveTo(px, top); c.lineTo(px, fl - u * 0.04); c.stroke(); }
  bedRoom(c, S, x + w * 0.12, top + u * 0.14, w * 0.3, u * 0.34, true, L.cover, nt(S, '#5a3a24', 0.3));
  pane(c, S, x + w * 0.58, top + u * 0.14, w * 0.24, u * 0.3, R() < 0.6, nt(S, '#5a3a24', 0.3), pick(R, CLOTHES), 1);
  gable(c, x + w / 2, w * 1.1, top, u * 0.75, nt(S, pick(R, ['#6a3a24', '#5a3a2a', '#8a4a2a']), 0.45));
  /* the stairs */
  var sx = L.side > 0 ? x + w + u * 0.05 : x - u * 0.05, d = L.side > 0 ? 1 : -1;
  for (i = 0; i < 5; i++) fr(c, sx + d * i * u * 0.09 - (d < 0 ? u * 0.15 : 0), fl + i * L.posts / 5, u * 0.15, u * 0.03, nt(S, '#6a4026', 0.4));
  ln(c, [[sx, fl], [sx + d * u * 0.45, G]], nt(S, '#5a3a24', 0.4), 2);
  /* below the floor: a bamboo bench and a water jar */
  pr(c, x + w * 0.2, G - u * 0.2, w * 0.35, u * 0.05, nt(S, '#c9a86a', 0.45), 0.6);
  fe(c, x + w * 0.75, G - u * 0.13, u * 0.12, u * 0.13, nt(S, '#7a4a2a', 0.4));
  return [{ k: 'place', x0: x - u * 0.2, x1: x + w + u * 0.2, y0: top - u * 0.75, y1: G }];
}
var HOTEL_STILL = { city: hotelCityStill, boutique: hotelBoutiqueStill, resort: hotelResortStill, river: hotelRiverStill, hill: hotelHillStill, camp: hotelCampStill, homestay: homestayStill };
var GROUND = { city: 'road', boutique: 'brick', resort: 'lawn', river: 'road', hill: 'lawn', camp: 'lawn', homestay: 'earth' };
/* the still layer of a hotel, with its sign, spirit house and plants placed for its kind */
function hotelStill(c, S, L) {
  var R = rnd((S.seed ^ 0x9e3) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {};
  street(c, S, GROUND[L.kind]); settingOn(c, S);
  var hits = HOTEL_STILL[L.kind](c, S, L, R);
  var lit = L.st === 'closed' ? false : true, z;
  /* the spirit house and the plants, on the open ground */
  var sx = L.side > 0 ? S.x1 - u * 1.25 : S.x0 + u * 1.25;
  if (L.kind === 'city' || L.kind === 'boutique' || L.kind === 'river' || L.kind === 'homestay') sx = L.side > 0 ? Math.max(L.bx - u * 0.35, S.x0 + u * 0.6) : Math.min(L.bx + L.bw + u * 0.35, S.x1 - u * 0.75);
  if (L.spirit && L.kind !== 'camp') L.inc = spiritHouse(c, sx, G + u * 0.02, u * 0.95, S, S.seed);
  var pl = L.plants;
  if (L.kind === 'city') { pot(c, L.door - u * 0.78, G, u * 0.8, S, 2, 3); pot(c, L.door + u * 0.78, G, u * 0.8, S, 2, 4); }
  if (L.kind === 'boutique') { pot(c, L.door - u * 0.5, G, u * 0.7, S, 0, 5); pot(c, L.door + u * 0.5, G, u * 0.7, S, 1, 6); }
  if (L.kind === 'resort' || L.kind === 'homestay') plantAt(c, pl[0], L.side > 0 ? S.x1 - u * 0.5 : S.x0 + u * 0.5, G + u * 0.04, u, S, S.seed + 1);
  if (L.kind === 'resort') plantAt(c, pl[2] === 'palm' ? 'palm' : 'frangipani', L.pool.x - u * 0.2, G, u, S, S.seed + 2);
  if (L.kind === 'homestay' || L.kind === 'boutique') pot(c, L.side > 0 ? L.bx + L.bw + u * 0.95 : L.bx - u * 0.95, G, u * 0.75, S, 0, 9);
  /* the sign, where that kind keeps it */
  if (L.kind === 'city') { var sz = signSize(c, P, u); z = nameSign(c, L.door, G - L.lobby - sz.h - u * 0.04, P, u, L.signCol, lit); }
  else if (L.kind === 'boutique' || L.kind === 'river') z = nameSign(c, L.bx + L.bw / 2, G - (L.fh || u * 0.6) + u * 0.02, P, u, L.signCol, lit);
  else if (L.kind === 'homestay') { var hz = signSize(c, P, u); z = gateSign(c, S, clamp(L.side > 0 ? L.bx + L.bw + hz.w / 2 + u * 0.7 : L.bx - hz.w / 2 - u * 0.7, S.x0 + hz.w / 2 + u * 0.3, S.x1 - hz.w / 2 - u * 0.3), P, L.signCol, lit); }
  else if (L.kind === 'hill') z = nameSign(c, L.lodge + u, G - u * 0.92, P, u, L.signCol, lit);
  else z = lowSign(c, S, L.gate, P, L.signCol, lit);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
/* the moving parts of a hotel: lanterns, the doorman's wai, the bell, swimmers, the boat, mist, fire */
function hotelLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, i, open = L.st !== 'closed';
  roomLights(S, L); riverGlints(S); incense(c, L.inc, t, 1);
  var staff = L.staff, g = L.guests;
  if (L.kind === 'city') {
    /* the counter, the receptionist, the bell */
    if (open) { var rx = L.door - L.side * u * 0.7; staff[0].dir = L.side; K.person(c, rx, G - u * 0.02, u * 0.85, STAND, staff[0]); fr(c, rx - u * 0.35, G - u * 0.36, u * 0.7, u * 0.36, nt(S, '#6a4026', 0.3)); fr(c, rx - u * 0.35, G - u * 0.38, u * 0.7, u * 0.04, '#e8b84a'); bell(c, rx + L.side * u * 0.2, G - u * 0.38, u * 0.6, t / 1000, 4.3); }
    /* the doorman: a wai each time a guest reaches the door */
    var dm = staff[1]; dm.garb = 'casual'; dm.long = true; dm.col = nt(S, L.accent, 0.3); dm.low = '#2a2a30'; dm.hair = 4; dm.dir = L.side;
    if (open) { var ph = L.A ? frac(t / 1000 / L.A.per + L.A.ph) * L.A.per : frac(t / 7000) * 7; K.person(c, L.door + L.side * u * 0.5, G + u * 0.06, u * 0.95, waiP(ph > 8.2 && ph < 10 ? Math.sin((ph - 8.2) / 1.8 * Math.PI) : 0), dm); }
    if (L.roof === 'flags') [0.3, 0.5, 0.7].forEach(function (f, k) { var fx = L.bx + L.bw * f, fy = L.top - u * 0.4; for (var j = 0; j < 5; j++) { var y0 = fy + j * u * 0.04, wv = Math.sin(t / 300 - j * 0.6 + k) * 2; c.fillStyle = ['#d9342b', '#f2f2f2', '#2c3e8a', '#f2f2f2', '#d9342b'][j]; c.beginPath(); c.moveTo(fx, y0); c.quadraticCurveTo(fx + u * 0.15, y0 + wv, fx + u * 0.3, y0 + wv * 1.5); c.lineTo(fx + u * 0.3, y0 + wv * 1.5 + u * 0.04); c.quadraticCurveTo(fx + u * 0.15, y0 + wv + u * 0.04, fx, y0 + u * 0.04); c.fill(); } });
    if (L.roof === 'bar' && S.night) fairy(c, L.bx + L.bw * 0.5, L.bx + L.bw * 0.98, L.top - u * 0.22, u * 0.05, u * 0.12, t, true, ['255,214,120', '255,170,90']);
  }
  if (L.kind === 'boutique') {
    for (i = 0; i < 2; i++) khom(c, L.door + (i ? 1 : -1) * u * 0.42, G - L.fh * 0.95, u * 0.1, u * 0.07, t, i, L.lantern, S.night);
    if (open) { staff[0].dir = -L.side; K.person(c, L.door + L.side * u * 0.15, G + u * 0.02, u * 0.85, STAND, staff[0]); bell(c, L.door - L.side * u * 0.12, G - u * 0.36, u * 0.5, t / 1000, 5.1); fr(c, L.door - u * 0.32, G - u * 0.34, u * 0.4, u * 0.34, nt(S, '#6a4026', 0.3)); }
    if (S.night || L.st === 'closed') moth(c, L.door, G - L.fh * 0.98, u * 0.06, t);
  }
  if (L.kind === 'resort') {
    var W = L.water;
    /* swimmers: crawl along the pool and back, the arm on a circle, θ = ωt */
    for (i = 0; i < (S.night ? 1 : 2); i++) { var per = 9 + i * 3, f = frac(t / 1000 / per + i * 0.4), dir = f < 0.5 ? 1 : -1, ff = f < 0.5 ? f * 2 : 2 - f * 2, sx = W.x + W.w * (0.1 + 0.8 * ease(ff)), sy = W.y + W.h * (0.4 + i * 0.25), d = g[i];
      fe(c, sx, sy, u * 0.16, u * 0.04, 'rgba(255,255,255,.35)'); fe(c, sx + dir * u * 0.1, sy - u * 0.03, u * 0.06, u * 0.06, d.skin); fe(c, sx + dir * u * 0.1, sy - u * 0.06, u * 0.06, u * 0.03, i ? '#d9342b' : '#1c1410');
      var a = t / 400 + i; ln(c, [[sx, sy - u * 0.02], [sx + dir * Math.cos(a) * u * 0.18, sy - u * 0.02 - Math.max(0, Math.sin(a)) * u * 0.14]], d.skin, Math.max(1.5, u * 0.04)); }
    c.strokeStyle = 'rgba(255,255,255,.4)'; c.lineWidth = 1; for (i = 0; i < 5; i++) { var wx = W.x + frac(i * 0.23 + t / 7000) * W.w * 0.9; c.beginPath(); c.moveTo(wx, W.y + W.h * (0.2 + (i % 3) * 0.25)); c.lineTo(wx + u * 0.12, W.y + W.h * (0.2 + (i % 3) * 0.25)); c.stroke(); }
    /* a sunbather on the lounger by day; khom along the sala eave */
    if (!S.night) { var lx = L.lounge, d2 = g[2]; fe(c, lx + u * 0.18, G - u * 0.17, u * 0.17, u * 0.045, d2.col); fe(c, lx + u * 0.4, G - u * 0.22, u * 0.06, u * 0.06, d2.skin); fe(c, lx + u * 0.04, G - u * 0.15, u * 0.06, u * 0.03, d2.skin); }
    for (i = 0; i < 3; i++) khom(c, L.sala + L.salaW * (0.2 + i * 0.3), G - u * 1.1, u * 0.12, u * 0.07, t, i, L.lantern, S.night);
    if (open) { staff[0].dir = L.side; K.person(c, L.sala + L.salaW * 0.5, G + u * 0.02, u * 0.88, STAND, staff[0]); fr(c, L.sala + L.salaW * 0.3, G - u * 0.34, L.salaW * 0.4, u * 0.34, nt(S, '#6a4026', 0.3)); fr(c, L.sala + L.salaW * 0.3, G - u * 0.36, L.salaW * 0.4, u * 0.03, '#e8b84a'); bell(c, L.sala + L.salaW * 0.62, G - u * 0.36, u * 0.55, t / 1000, 4.7); }
  }
  if (L.kind === 'river') {
    if (onRiver(S.place || {})) { var by = G + (S.H - G) * 0.55, bs = u * 1.8, bx = S.x0 - bs + frac(t / 22000 + (S.seed % 10) / 10) * (S.span + bs * 2), bob = Math.sin(t / 500) * 1.2;
      c.save(); c.translate(bx, by + bob); fp(c, [[-bs * 0.5, -u * 0.06], [bs * 0.45, -u * 0.06], [bs * 0.55, -u * 0.22], [bs * 0.4, u * 0.04], [-bs * 0.45, u * 0.04]], nt(S, L.boat, 0.4)); fr(c, -bs * 0.5, -u * 0.07, bs, 2, '#e8b84a');
      ln(c, [[-bs * 0.5, -u * 0.04], [-bs * 0.72, u * 0.06]], '#3a3a3a', 1.5); fe(c, -bs * 0.42, -u * 0.12, u * 0.07, u * 0.06, '#5a5a60'); var bm = g[3]; bm.dir = 1; K.person(c, -bs * 0.32, -u * 0.04, u * 0.6, SIT, bm); c.restore(); }
    fairy(c, L.terrace[0], L.terrace[1], G - u * 0.85, u * 0.12, u * 0.14, t, S.night, ['255,214,120', '255,150,120', '180,220,255']);
    if (open) for (i = 0; i < 2; i++) { var tx = L.terrace[0] + u * (0.5 + i * 1.0); g[i].dir = i ? -1 : 1; K.person(c, tx + (i ? 1 : -1) * u * 0.3, G, u * 0.85, SIT, g[i]); var cupX = tx + (i ? 1 : -1) * u * 0.06; fr(c, cupX - 2, G - u * 0.36, 4, u * 0.06, '#f2f2f2'); }
  }
  if (L.kind === 'hill') {
    /* mist through the valley, drifting as x = x₀ + vt */
    for (i = 0; i < 3; i++) { var mx = S.x0 + frac(t / (40000 + i * 9000) + i * 0.33) * (S.span + u * 4) - u * 2, my = G - u * (0.7 + i * 0.35); c.fillStyle = S.night ? 'rgba(200,210,230,.12)' : 'rgba(255,255,255,.38)'; c.beginPath(); c.ellipse(mx, my, u * 1.4, u * 0.14, 0, 0, TAU); c.fill(); }
    if (L.cab.length) { var cb = L.cab[0], gg = g[0]; gg.dir = -L.slope; K.person(c, cb[0] + L.slope * u * 0.55, cb[1] + u * 0.02, u * 0.75, STAND, gg); }
    for (i = 0; i < 2; i++) khom(c, L.lodge + u * (0.4 + i * 1.2), G - u * 0.62, u * 0.1, u * 0.07, t, i, L.lantern, S.night);
    if (open) bell(c, L.lodge + u * 1.0, G - u * 0.32, u * 0.55, t / 1000, 4.9);
  }
  if (L.kind === 'camp') {
    /* the fire: flames as tongues, h = h₀(1 + 0.25·sin(t/90 + k)), sparks rising */
    var fx = L.fire, fy = G + u * 0.06; glow(c, fx, fy - u * 0.2, u * (S.night ? 1.4 : 0.6), '255,150,60', S.night ? 0.6 : 0.3);
    for (i = 0; i < 5; i++) { var fh = u * (0.3 + 0.1 * Math.sin(t / 90 + i * 1.7)) * (i === 2 ? 1.3 : 1), fx2 = fx + (i - 2) * u * 0.07; fp(c, [[fx2 - u * 0.06, fy], [fx2 + Math.sin(t / 130 + i) * u * 0.04, fy - fh], [fx2 + u * 0.06, fy]], i % 2 ? '#ff8a3a' : '#ffcf5a'); }
    for (i = 0; i < 6; i++) { var su = frac(t / 1600 + i / 6); fe(c, fx + Math.sin(i * 2.3 + su * 5) * u * 0.15, fy - u * 0.3 - su * u * 0.9, 1.3, 1.3, 'rgba(255,200,90,' + (1 - su).toFixed(2) + ')'); }
    [-1, 1].forEach(function (d, k) { var p = g[k]; p.dir = -d; K.person(c, fx + d * u * 0.7, G - u * 0.02, u * 0.85, { lean: 0.15, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5], arms: [1.1 + 0.1 * Math.sin(t / 700 + k), 0.4, 1.0, 0.5] }, p); });
    /* the hammock swinging, a pendulum, a reader in it */
    if (L.hammock) { var h0 = L.hammock[0], h1 = L.hammock[1], hy = G - u * 0.62, sw = Math.sin(t / 1100) * u * 0.05, mid = (h0 + h1) / 2 + sw;
    c.strokeStyle = nt(S, '#e5567f', 0.3); c.lineWidth = Math.max(3, u * 0.08); c.beginPath(); c.moveTo(h0, hy - u * 0.2); c.quadraticCurveTo(mid, hy + u * 0.35, h1, hy - u * 0.2); c.stroke();
    fe(c, mid - u * 0.15, hy + u * 0.06, u * 0.06, u * 0.06, g[2].skin); fe(c, mid + u * 0.05, hy + u * 0.1, u * 0.22, u * 0.06, g[2].col); }
    if (S.night) L.tentAt.forEach(function (x, k) { fairy(c, x - u * 0.45, x + u * 0.45, G - u * 0.42, u * 0.06, u * 0.12, t + k * 300, true, ['255,214,120']); });
  }
  if (L.kind === 'homestay') {
    var hw = L.bx + L.bw, fl = G - L.posts; laundry(c, L.bx + L.bw * 0.15, L.bx + L.bw * 0.85, fl + u * 0.1, u * 0.35, t, S.seed, S);
    var au = staff[0]; au.garb = 'sin'; au.dir = L.side; K.person(c, L.bx + L.bw * 0.4, G, u * 0.85, SIT, au);
    if (S.night) moth(c, hw - u * 0.2, fl - u * 0.68, u * 0.06, t);
  }
  /* an animal of the place */
  var ax = L.side > 0 ? (L.kind === 'city' ? L.bx + L.bw * 0.08 : S.x1 - u * 1.9) : (L.kind === 'city' ? L.bx + L.bw * 0.92 : S.x0 + u * 1.9);
  if (L.animal === 'dog') dog(c, ax, G + u * 0.1, u * 0.55, nt(S, L.dogCol, 0.35), S.night || L.st === 'closed', t, -L.side);
  else if (L.animal === 'cat') cat(c, ax, G + u * 0.08, u * 0.55, nt(S, pick(rnd(S.seed), ['#e8a050', '#3a3a3a', '#f2ede0', '#8a8a90']), 0.3), t);
  if (L.A && (open || !S.night)) arrival(S, L.A);
}
function hotel(S) {
  var L = look(S, 'hotel', hotelDeal), u = S.hh; L.st = stateOf(S);
  var key = ['hotel', L.kind, S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0, L.st, S.phone ? 1 : 0].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { L.wins = []; return hotelStill(q, S, L); });
  hotelLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- shared house pieces */
/* teak planks: vertical lines on a wall */
function planks(c, x, y, w, h, gap) { c.strokeStyle = 'rgba(0,0,0,.16)'; c.lineWidth = 1; c.beginPath(); for (var px = x + gap; px < x + w; px += gap) { c.moveTo(px, y); c.lineTo(px, y + h); } c.stroke(); }
/* bamboo weave: rows of short strokes, alternating */
function weave(c, x, y, w, h, s) { c.strokeStyle = 'rgba(80,50,20,.28)'; c.lineWidth = 1; c.beginPath(); for (var yy = y + s / 2, r = 0; yy < y + h; yy += s, r++) for (var xx = x + (r % 2) * s; xx < x + w; xx += s * 2) { c.moveTo(xx, yy); c.lineTo(Math.min(x + w, xx + s), yy); } c.stroke(); }
/* thatch: a roof of grass, many short strokes hanging from the ridge */
function thatch(c, x, w, y, h, S) { paper(c, poly([[x - w * 0.58, y], [x, y - h], [x + w * 0.58, y]]), nt(S, '#b8955a', 0.45), 1.2); c.strokeStyle = nt(S, '#8a6a3a', 0.4); c.lineWidth = 1; c.beginPath(); for (var k = 0; k < 28; k++) { var f = k / 27, bx = x - w * 0.58 + f * w * 1.16; c.moveTo(bx, y + 2); c.lineTo(lerp(bx, x, 0.4), lerp(y, y - h, 0.4)); } c.stroke(); }
/* a rail of balusters along a balcony */
function rail(c, x0, x1, y, h, col, gap) { fr(c, x0, y - h, x1 - x0, Math.max(2, h * 0.12), col); for (var bx = x0; bx <= x1; bx += gap) fr(c, bx, y - h, Math.max(1.5, gap * 0.28), h, col); }
/* does the place's own name or services say this? */
function said(S, rx) { var P = S.place; return !!P && rx.test((P.name || '') + ' ' + (P.nameEn || '') + ' ' + (P.services || []).join(' ')); }
/* a door: open and warm, or shut */
function doorway(c, S, x, y, w, h, open, col) { if (open) { fr(c, x, y, w, h, S.night ? '#ffd690' : '#f3dcb0'); if (S.night) glow(c, x + w / 2, y + h * 0.5, w * 1.2, '255,200,120', 0.45); fr(c, x - w * 0.18, y, w * 0.16, h, nt(S, col, 0.35)); } else { fr(c, x, y, w, h, nt(S, col, 0.35)); fr(c, x + w * 0.75, y + h * 0.5, 2, 3, '#e8b84a'); } }
/* rental scooters in a row and their board */
function rentRow(c, S, x0, dir, n, R, board) {
  var u = S.hh, G = S.deck, cols = ['#d9342b', '#f2f2f2', '#2c3e6b', '#e8b84a', '#2f8f5b', '#9b6bd6', '#1f1f24', '#e5567f'];
  for (var i = n - 1; i >= 0; i--) vehicle(c, 'scooter', x0 + dir * i * u * 0.72, G + u * 0.1 + (i % 2) * u * 0.03, u * 0.9, -dir, nt(S, pick(R, cols), 0.4), false, R() * 6);
  if (!board || !said(S, /rent|เช่า/i)) return;   /* the board only where the place itself says it rents */
  var bx = x0 + dir * (n * u * 0.72 + u * 0.15), f = Math.max(9, u * 0.12); c.save(); c.font = '800 ' + Math.round(f) + 'px ' + FONT;
  var w = Math.max(c.measureText('รถให้เช่า').width, c.measureText('Bikes for rent').width) + u * 0.16, h = f * 2.3;
  bx = clamp(bx, S.x0 + w / 2 + u * 0.8, S.x1 - w / 2 - u * 0.8);
  ln(c, [[bx - w * 0.3, G + u * 0.12], [bx - w * 0.2, G - u * 0.18]], nt(S, '#6a4026', 0.4), 2); ln(c, [[bx + w * 0.3, G + u * 0.12], [bx + w * 0.2, G - u * 0.18]], nt(S, '#6a4026', 0.4), 2);
  pr(c, bx - w / 2, G - u * 0.18 - h, w, h, nt(S, '#f7f0dc', 0.35), 0.8); c.fillStyle = nt(S, '#c0392b', 0.2); c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillText('รถให้เช่า', bx, G - u * 0.18 - h * 0.7); c.font = '700 ' + Math.round(f * 0.85) + 'px ' + FONT; c.fillStyle = nt(S, '#2a2a30', 0.2); c.fillText('Bikes for rent', bx, G - u * 0.18 - h * 0.28); c.restore();
}
/* a garden table: banana pancakes on a plate, a cup, a stool either side */
function pancakeTable(c, S, x) {
  var u = S.hh, G = S.deck, wood = nt(S, '#7a4a2a', 0.4);
  fr(c, x - u * 0.32, G - u * 0.34, u * 0.64, u * 0.05, wood); ln(c, [[x - u * 0.25, G - u * 0.3], [x - u * 0.28, G]], wood, 2); ln(c, [[x + u * 0.25, G - u * 0.3], [x + u * 0.28, G]], wood, 2);
  fe(c, x - u * 0.06, G - u * 0.36, u * 0.13, u * 0.025, '#f8f8f4');
  fe(c, x - u * 0.06, G - u * 0.385, u * 0.1, u * 0.03, '#e8b860'); c.strokeStyle = '#6a3a1a'; c.lineWidth = 1; c.beginPath(); for (var k = 0; k < 5; k++) { c.moveTo(x - u * (0.14 - k * 0.04), G - u * 0.40); c.lineTo(x - u * (0.12 - k * 0.04), G - u * 0.37); } c.stroke();
  fe(c, x - u * 0.09, G - u * 0.41, u * 0.025, u * 0.012, '#f7e08a'); fe(c, x - u * 0.02, G - u * 0.41, u * 0.025, u * 0.012, '#f7e08a');
  fr(c, x + u * 0.14, G - u * 0.43, u * 0.07, u * 0.07, '#f2ede0'); fr(c, x + u * 0.145, G - u * 0.42, u * 0.06, u * 0.02, '#6a3a1a');
}
/* steam from a cup or a pot: puffs rising, swelling, thinning */
function steam(c, x, y, s, t, n) { for (var i = 0; i < n; i++) { var q = frac(t / 2400 + i / n), yy = y - q * s, xx = x + Math.sin(q * 5 - t / 900 + i) * s * 0.12 * (0.3 + q); c.fillStyle = 'rgba(255,255,255,' + (0.4 * Math.sin(Math.PI * q)).toFixed(3) + ')'; c.beginPath(); c.arc(xx, yy, s * (0.05 + 0.12 * q), 0, TAU); c.fill(); } }
/* the auntie's broom (mai kwad), swept on |sin ωt|, with a puff of dust */
function sweeper(S, d, x, y, h, dir) {
  var c = S.c, t = S.t, sw = Math.sin(t / 380), J = { lean: 0.42, seat: 0.45, legs: [0.25, -0.15, -0.2, 0], arms: [0.9 + sw * 0.35, 0.3, 0.6 + sw * 0.35, 0.5] };
  d.dir = dir; var me = K.person(c, x, y, h, J, d);
  var hx = me.hand[0][0], hy = me.hand[0][1], bx = hx + dir * h * (0.25 + sw * 0.15), by = y;
  ln(c, [[me.hand[1][0], me.hand[1][1]], [bx, by - h * 0.12]], '#c9a06a', Math.max(1.4, h * 0.03));
  fp(c, [[bx - h * 0.09, by], [bx - h * 0.02, by - h * 0.16], [bx + h * 0.04, by - h * 0.16], [bx + h * 0.13, by]], '#d9b36a');
  var q = frac(t / 760); fe(c, bx + dir * h * 0.12 * q, by - h * 0.03 - q * h * 0.08, h * (0.03 + q * 0.05), h * 0.02 * (1 + q), 'rgba(220,200,170,' + (0.5 * (1 - q)).toFixed(2) + ')');
}

/* ---------------------------------------------------------------- guesthouse */
function ghDeal(S, R, L) {
  var u = S.hh, G = S.deck, sp = S.span, P = S.place || {}, n = nameOf(P);
  L.camp = /camp|แคมป์|แค้มป์|glamp|tent|เต็นท์/.test(n);
  L.kind = P.hills || P.moo ? pick(R, ['posts', 'bamboo', 'posts', 'twostorey', 'bamboo']) : P.oldCity ? pick(R, ['shophouse', 'twostorey', 'row']) : pick(R, ['twostorey', 'row', 'shophouse', 'posts', 'twostorey', 'row']);
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.bw = u * (L.kind === 'row' ? 3.3 + R() * 0.5 : L.kind === 'shophouse' ? 2.2 + R() * 0.4 : 2.6 + R() * 0.6);
  L.bx = side > 0 ? S.x0 + sp * 0.11 : S.x1 - sp * 0.11 - L.bw;
  L.wall = pick(R, ['#f2ede0', '#e8d2b0', '#d9e2dc', '#f0d8c8', '#cfe0e8', '#f5e6b8', '#e2d6ea', '#e9c46a']); L.wood = pick(R, ['#8a5a34', '#7a4a2a', '#9a6a3a', '#6a4026']);
  L.roofCol = pick(R, ['#a8432f', '#6a3a24', '#8a4a2a', '#5a6a7a', '#b5653a']); L.cover = pick(R, COVERS); L.signCol = pick(R, SIGNCOL); L.lantern = pick(R, ['#d9342b', '#f29a1f', '#e8b84a', '#c2185b']);
  L.posts = u * (0.42 + R() * 0.15); L.fh = u * (L.kind === 'shophouse' ? 0.6 : 0.95);
  var open0 = side > 0 ? L.bx + L.bw + u * 0.4 : L.bx - u * 0.4;
  L.rent = R() < 0.6; L.nBikes = 2 + Math.floor(R() * 2); L.bikes = open0 + side * u * 0.3;
  L.table = open0 + side * u * (L.rent ? L.nBikes * 0.72 + 1.6 : 0.9); L.hasTable = (S.x1 - u * 0.9 - L.table) * side > 0 && (L.table - S.x0 - u * 0.9) * side > -sp;
  if (side > 0 ? L.table > S.x1 - u * 1.0 : L.table < S.x0 + u * 1.0) L.hasTable = false;
  L.spirit = R() < 0.7; L.plant = pick(R, ['banana', 'frangipani', 'palm', 'bougain', 'banana']); L.animal = P.moo || P.hills ? pick(R, ['hens', 'dog', 'hens', 'cat']) : pick(R, ['dog', 'cat', 'dog', 'none']);
  L.dogCol = pick(R, ['#c9a06a', '#3a2a22', '#e8dcc8', '#8a6a4a']);
  L.folk = crew(S, 5, { sin: 0.4, mohom: 0.2, casual: 0.4 }, 0x61);
  L.trav = crew(S, 4, GUESTS, 0x62); L.trav.forEach(function (d) { d.garb = 'casual'; d.pack = pick(R, ['#c0562a', '#3a6a4a', '#2c3e6b', '#e8a23a', '#7a3a5a']); });
  return L;
}
/* the still guesthouse, by its kind */
function ghStill(c, S, L) {
  var R = rnd((S.seed ^ 0x6a1) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, x = L.bx, w = L.bw, k = L.kind, i, hits = [], open = L.st !== 'closed', z;
  street(c, S, k === 'posts' || k === 'bamboo' ? 'earth' : 'road'); settingOn(c, S);
  var wood = nt(S, L.wood, 0.45), wall = nt(S, L.wall, 0.45), top;
  if (k === 'posts' || k === 'bamboo') {
    var fl = G - L.posts; top = fl - u * 0.62;
    for (i = 0; i < 5; i++) pr(c, x + i * (w - u * 0.1) / 4, fl, u * 0.1, L.posts, nt(S, '#5a3a24', 0.5), 0.8);
    pr(c, x - u * 0.15, fl - u * 0.04, w + u * 0.3, u * 0.08, nt(S, '#5a3a24', 0.45), 1);
    pr(c, x, top, w, fl - top, k === 'bamboo' ? nt(S, '#c9a86a', 0.45) : wood, 1.4);
    if (k === 'bamboo') weave(c, x, top, w, fl - top, Math.max(3, u * 0.06)); else planks(c, x, top, w, fl - top, 4);
    bedRoom(c, S, x + w * 0.1, top + u * 0.14, w * 0.3, u * 0.34, true, L.cover, nt(S, '#5a3a24', 0.3));
    doorway(c, S, x + w * 0.52, top + u * 0.08, w * 0.16, fl - top - u * 0.12, open, L.wood);
    pane(c, S, x + w * 0.75, top + u * 0.14, w * 0.16, u * 0.26, R() < 0.6, nt(S, '#5a3a24', 0.3), pick(R, CLOTHES), 1);
    rail(c, x - u * 0.12, x + w + u * 0.12, fl - u * 0.04, u * 0.18, nt(S, '#5a3a24', 0.4), u * 0.09);
    if (k === 'bamboo') thatch(c, x + w / 2, w * 1.12, top, u * 0.8, S); else gable(c, x + w / 2, w * 1.1, top, u * 0.75, nt(S, L.roofCol, 0.45));
    var d = L.side, sx = d > 0 ? x + w + u * 0.05 : x - u * 0.05;
    for (i = 0; i < 5; i++) fr(c, sx + d * i * u * 0.09 - (d < 0 ? u * 0.15 : 0), fl + i * L.posts / 5, u * 0.15, u * 0.03, nt(S, '#6a4026', 0.4));
    pr(c, x + w * 0.15, G - u * 0.18, w * 0.35, u * 0.05, nt(S, '#c9a86a', 0.45), 0.6);
    L.line = [x + w * 0.05, x + w * 0.95, fl + u * 0.08]; L.sweepY = G; L.door = x + w * 0.6;
    var gz = signSize(c, P, u); z = gateSign(c, S, clamp(L.side > 0 ? x + w + gz.w / 2 + u * 0.7 : x - gz.w / 2 - u * 0.7, S.x0 + gz.w / 2 + u * 0.4, S.x1 - gz.w / 2 - u * 0.4), P, L.signCol, open);
    L.hasTable = false; L.bikes = L.side > 0 ? Math.min(z.x1 + u * 0.5, S.x1 - u * 2) : Math.max(z.x0 - u * 0.5, S.x0 + u * 2);
    if (z.x0 < S.x0 + u * 0.5 || z.x1 > S.x1 - u * 0.5) L.rent = false;
    L.rent = L.rent && (L.side > 0 ? S.x1 - L.bikes > u * 2.2 : L.bikes - S.x0 > u * 2.2);
  } else if (k === 'twostorey') {
    top = G - u * 1.95; var mid = G - L.fh;
    pr(c, x, mid, w, L.fh, wall, 1.4);
    pr(c, x - u * 0.06, top, w + u * 0.12, mid - top, wood, 1.4); planks(c, x - u * 0.06, top, w + u * 0.12, mid - top, 4);
    bedRoom(c, S, x + w * 0.1, top + u * 0.16, w * 0.28, u * 0.4, true, L.cover, nt(S, '#5a3a24', 0.3));
    pane(c, S, x + w * 0.62, top + u * 0.16, w * 0.24, u * 0.36, R() < 0.5, nt(S, '#f2ede0', 0.35), pick(R, CLOTHES), 2);
    fr(c, x - u * 0.2, mid - u * 0.05, w + u * 0.4, u * 0.07, nt(S, '#5a3a24', 0.4));
    rail(c, x - u * 0.2, x + w + u * 0.2, mid - u * 0.04, u * 0.22, nt(S, '#5a3a24', 0.35), u * 0.08);
    doorway(c, S, x + w * 0.38, mid + u * 0.14, w * 0.26, L.fh - u * 0.14, open, '#8a8f96');
    if (!open) shutter(c, x + w * 0.38, mid + u * 0.14, w * 0.26, L.fh - u * 0.14, S);
    pane(c, S, x + w * 0.08, mid + u * 0.25, w * 0.22, u * 0.36, open, nt(S, '#f2ede0', 0.35), null, 0); pane(c, S, x + w * 0.72, mid + u * 0.25, w * 0.2, u * 0.36, open, nt(S, '#f2ede0', 0.35), null, 1);
    hipRoof(c, x + w / 2, w * 1.16, top, u * 0.36, nt(S, L.roofCol, 0.45)); laiKham(c, x, x + w, top + u * 0.04, u * 0.05);
    L.line = [x + w * 0.02, x + w * 0.98, mid - u * 0.34]; L.door = x + w * 0.51;
    z = nameSign(c, L.door, mid + u * 0.01, P, u, L.signCol, open);
  } else if (k === 'row') {
    top = G - u * 1.75; var mid2 = G - L.fh * 0.9, n = Math.max(3, Math.floor(w / (u * 0.8)));
    pr(c, x, top, w, G - top, wall, 1.4);
    for (i = 0; i < n; i++) { var dx = x + (i + 0.5) * w / n; doorway(c, S, dx - u * 0.14, mid2 + u * 0.22, u * 0.24, G - mid2 - u * 0.22, false, L.wood); pane(c, S, dx + u * 0.14, mid2 + u * 0.3, u * 0.16, u * 0.22, R() < 0.5, nt(S, '#f2ede0', 0.35), pick(R, CLOTHES), i);
      if (i === 1) bedRoom(c, S, dx - u * 0.2, top + u * 0.12, u * 0.4, u * 0.36, true, L.cover, nt(S, '#5a3a24', 0.3)); else { doorway(c, S, dx - u * 0.14, top + u * 0.12, u * 0.24, mid2 - top - u * 0.18, false, L.wood); pane(c, S, dx + u * 0.14, top + u * 0.18, u * 0.16, u * 0.22, R() < 0.5, nt(S, '#f2ede0', 0.35), pick(R, CLOTHES), i + 3); }
      c.save(); c.fillStyle = '#e8b84a'; c.font = '700 ' + Math.round(Math.max(8, u * 0.1)) + 'px ' + FONT; c.textAlign = 'center'; c.fillText(String(i + 1), dx - u * 0.02, mid2 + u * 0.2); c.fillText(String(n + i + 1), dx - u * 0.02, top + u * 0.1); c.restore(); }
    fr(c, x - u * 0.1, mid2 - u * 0.05, w + u * 0.2, u * 0.08, nt(S, '#5a3a24', 0.4)); rail(c, x - u * 0.1, x + w + u * 0.1, mid2 - u * 0.04, u * 0.2, nt(S, '#5a3a24', 0.35), u * 0.08);
    gable(c, x + w / 2, w * 1.08, top, u * 0.45, nt(S, L.roofCol, 0.45), true);
    L.line = [x + w * 0.04, x + w * 0.96, mid2 - u * 0.3]; L.door = x + w * 0.5;
    z = nameSign(c, x + w / 2, top - u * 0.4, P, u, L.signCol, open);
  } else {   /* shophouse: three storeys, a café-reception at the street */
    top = G - u * 2.15; var gh = u * 1.0;
    pr(c, x, top, w, G - top, wall, 1.6);
    var fh2 = (G - gh - top) / 2;
    for (var f = 0; f < 2; f++) { var fy = top + f * fh2; for (i = 0; i < 2; i++) { var wx = x + w * (0.12 + i * 0.46); if (f === 1 && i === 0) bedRoom(c, S, wx, fy + fh2 * 0.18, w * 0.32, fh2 * 0.62, true, L.cover, nt(S, '#f2ede0', 0.3)); else pane(c, S, wx, fy + fh2 * 0.18, w * 0.32, fh2 * 0.62, R() < 0.5, nt(S, '#f2ede0', 0.35), pick(R, CLOTHES), i + f); }
      rail(c, x + w * 0.05, x + w * 0.95, fy + fh2 * 0.92, fh2 * 0.22, nt(S, '#3a3f4a', 0.35), u * 0.07); }
    fr(c, x, G - gh, w, u * 0.06, nt(S, L.roofCol, 0.4));
    if (open) { fr(c, x + u * 0.1, G - gh + u * 0.06, w - u * 0.2, gh - u * 0.06, S.night ? '#ffd690' : '#f3dcb0'); if (S.night) glow(c, x + w / 2, G - gh * 0.5, w * 0.6, '255,200,120', 0.5);
      for (i = 0; i < 3; i++) fr(c, x + u * 0.25 + i * u * 0.25, G - gh + u * 0.3, u * 0.12, u * 0.18, pick(R, ['#c0562a', '#2f6b5a', '#e8b84a'])); fr(c, x + u * 0.15, G - gh + u * 0.5, w * 0.5, u * 0.03, nt(S, '#6a4026', 0.3)); }
    else shutter(c, x + u * 0.1, G - gh + u * 0.06, w - u * 0.2, gh - u * 0.06, S);
    fr(c, x - u * 0.05, top - u * 0.08, w + u * 0.1, u * 0.08, nt(S, '#d8d0c0', 0.45)); fr(c, x + w * 0.7, top - u * 0.24, u * 0.24, u * 0.16, nt(S, '#5a8ab0', 0.4));
    L.line = [x + w * 0.05, x + w * 0.95, top + fh2 * 0.9 - fh2 * 0.3]; L.door = x + w * 0.5;
    var sz = signSize(c, P, u); z = nameSign(c, x + w / 2, G - gh - sz.h + u * 0.02, P, u, L.signCol, open);
  }
  /* the open ground: bikes for rent, the pancake table, a plant, the spirit house */
  if (L.rent) rentRow(c, S, L.bikes, L.side, L.nBikes, R, true);
  if (L.hasTable) pancakeTable(c, S, L.table);
  var px = L.side > 0 ? Math.max(x - u * 0.45, S.x0 + u * 0.75) : Math.min(x + w + u * 0.45, S.x1 - u * 0.75);
  if (L.spirit) L.inc = spiritHouse(c, px, G + u * 0.02, u * 0.9, S, S.seed);
  else plantAt(c, L.plant, px, G + u * 0.02, u, S, S.seed + 4);
  if (k === 'twostorey' || k === 'row') bougain(c, L.side > 0 ? x + w * 0.75 : x, (k === 'row' ? G - L.fh * 0.9 : G - L.fh) - u * 0.3, w * 0.25, u * 0.6, S, S.seed + 8);
  pot(c, L.door - u * 0.45, G + u * 0.02, u * 0.6, S, 0, S.seed + 2);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x - u * 0.1, x1: x + w + u * 0.1, y0: G - u * 2.2, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
/* the guesthouse at work: washing in the breeze, the auntie sweeping, pancakes eaten, backpackers */
function ghLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, open = L.st !== 'closed', f = L.folk, tr = L.trav;
  roomLights(S, L); riverGlints(S); incense(c, L.inc, t, 2);
  laundry(c, L.line[0], L.line[1], L.line[2], u * 0.32, t, S.seed, S);
  var ky = (L.kind === 'posts' || L.kind === 'bamboo' ? G - L.posts : L.kind === 'row' ? G - L.fh * 0.9 : G - L.fh) + u * 0.02;
  khom(c, L.bx + L.bw * 0.05, ky, u * 0.08, u * 0.06, t, 0, L.lantern, S.night); khom(c, L.bx + L.bw * 0.95, ky, u * 0.08, u * 0.06, t, 1, L.lantern, S.night);
  if (open && !S.night) { var au = f[0]; au.garb = 'sin'; au.hair = 2; sweeper(S, au, L.door + L.side * u * (0.9 + 0.3 * Math.sin(t / 5000)), G + u * 0.06, u * 0.86, -L.side); }
  if (L.hasTable && open) { var e = tr[2], lift = Math.max(0, Math.sin(t / 900)); e.dir = -L.side; K.person(c, L.table + L.side * u * 0.42, G + u * 0.02, u * 0.88, { lean: 0.15, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5], arms: [1.3 + lift * 0.6, 0.6 + lift * 0.8, 0.9, 1.1] }, e); steam(c, L.table + u * 0.175, G - u * 0.44, u * 0.5, t, 3); }
  /* backpackers: one comes in, one heads out */
  if (!S.night || open) {
    var b0 = L.side > 0 ? S.x1 + u * 0.3 : S.x0 - u * 0.3;
    walker(S, tr[0], b0, L.door, 0.55, 0.1, G + u * 0.1, u * 0.92, 'pack', tr[0].pack);
    if (!S.night) walker(S, tr[1], L.door, b0, 0.6, 0.55, G + u * 0.16, u * 0.95, 'pack', tr[1].pack);
  }
  var ax = L.side > 0 ? L.bx + L.bw * 0.2 : L.bx + L.bw * 0.8;
  if (L.animal === 'dog') dog(c, ax, G + u * 0.12, u * 0.55, nt(S, L.dogCol, 0.35), S.night || !open, t, L.side);
  else if (L.animal === 'cat') cat(c, ax, G + u * 0.08, u * 0.55, nt(S, '#e8a050', 0.3), t);
  else if (L.animal === 'hens') for (var i = 0; i < 3; i++) hen(c, ax + i * u * 0.3, G + u * 0.14 + (i % 2) * u * 0.04, u * 0.5, t, i, nt(S, ['#c0562a', '#f2ede0', '#3a2a22'][i], 0.35));
  if (S.night) moth(c, L.door + u * 0.25, (L.kind === 'posts' || L.kind === 'bamboo' ? G - L.posts - u * 0.5 : G - L.fh) + u * 0.12, u * 0.05, t);
}
function guesthouse(S) {
  var L = look(S, 'guesthouse', ghDeal);
  if (L.camp) { var S2 = {}; for (var q in S) S2[q] = S[q]; S2.variant = 'camp'; return hotel(S2); }
  var u = S.hh; L.st = stateOf(S);
  var key = ['gh', L.kind, S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0, L.st].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { L.wins = []; return ghStill(q, S, L); });
  ghLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- hostel */
var EVENTS = ['Pub quiz 20:00', 'Family dinner 19:00', 'Walking tour 09:00', 'Yoga 07:30', 'Movie night 21:00', 'Muay Thai 18:00', 'Khao soi run 12:00',
  'Night market 18:00', 'Doi Suthep hike 08:00', 'Cooking class 10:00', 'Live music 20:30', 'Waterfall trip 09:30', 'Free pancakes 08:00', 'Thai lesson 16:00'];
function hostelDeal(S, R, L) {
  var u = S.hh, sp = S.span, P = S.place || {};
  L.kind = P.oldCity ? pick(R, ['shophouse', 'house']) : pick(R, ['shophouse', 'house', 'modern', 'shophouse']);
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.bw = u * (2.7 + R() * 0.6); L.bx = side > 0 ? S.x0 + sp * 0.1 : S.x1 - sp * 0.1 - L.bw;
  L.wall = pick(R, ['#f2c94c', '#6cc3c1', '#e5567f', '#4d8fd1', '#7fe0a4', '#f08a5d', '#f2ede0', '#b692ff', '#e9c46a']);
  L.trim = pick(R, ['#2a2a30', '#f2ede0', '#6a4026', '#2c3e6b']); L.mural = pick(R, ['elephant', 'mountains', 'waves', 'dots', 'elephant']);
  L.cover = pick(R, COVERS); L.signCol = pick(R, SIGNCOL); L.roof = pick(R, ['deck', 'gable', 'flat', 'deck']);
  var ev = EVENTS.slice(), out = []; for (var k = 0; k < 3; k++) out.push(ev.splice(Math.floor(R() * ev.length), 1)[0]);
  out.sort(function (a, b) { return a.slice(-5) < b.slice(-5) ? -1 : 1; }); L.events = out;
  L.board = side > 0 ? L.bx + L.bw + u * 0.75 : L.bx - u * 0.75; L.rack = L.board + side * u * 1.0; L.nb = 2 + (R() < 0.5 ? 1 : 0);
  if (side > 0 ? L.rack + u * L.nb * 0.55 > S.x1 - u * 0.8 : L.rack - u * L.nb * 0.55 < S.x0 + u * 0.8) L.nb = 1;
  L.folk = crew(S, 6, GUESTS, 0x71); L.folk.forEach(function (d) { d.garb = 'casual'; });
  L.bikeCol = pick(R, ['#e8d9b8', '#7fa8c9', '#d9342b', '#2f8f5b', '#f2c94c']);
  return L;
}
function hostelStill(c, S, L) {
  var R = rnd((S.seed ^ 0x7b1) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, x = L.bx, w = L.bw, i, open = L.st !== 'closed', hits = [];
  street(c, S, 'road'); settingOn(c, S);
  var top = G - u * 2.12, gh = u * 1.02, wall = nt(S, L.wall, 0.45), trim = nt(S, L.trim, 0.35), fh = (G - gh - top) / 2;
  pr(c, x, top, w, G - top, wall, 1.6);
  if (L.kind === 'modern') { for (var sx = x + w * 0.62; sx < x + w; sx += u * 0.06) fr(c, sx, top, u * 0.03, G - gh - top, nt(S, '#8a5a34', 0.4)); }
  /* the mural on the side panel */
  var mx = L.kind === 'modern' ? x + w * 0.04 : x + w * 0.64, mw = w * 0.32, my = top + u * 0.08, mh = G - gh - top - u * 0.16;
  if (L.kind !== 'modern') { fr(c, mx, my, mw, mh, nt(S, mixc(L.wall, '#ffffff', 0.3), 0.45));
    if (L.mural === 'elephant') { fe(c, mx + mw * 0.5, my + mh * 0.55, mw * 0.3, mh * 0.22, nt(S, '#7a8aa8', 0.4)); fe(c, mx + mw * 0.75, my + mh * 0.45, mw * 0.14, mh * 0.15, nt(S, '#7a8aa8', 0.4)); ln(c, [[mx + mw * 0.85, my + mh * 0.5], [mx + mw * 0.9, my + mh * 0.75], [mx + mw * 0.84, my + mh * 0.82]], nt(S, '#7a8aa8', 0.4), mw * 0.06);
      for (i = 0; i < 4; i++) fr(c, mx + mw * (0.28 + i * 0.12), my + mh * 0.68, mw * 0.06, mh * 0.2, nt(S, '#7a8aa8', 0.4)); fe(c, mx + mw * 0.22, my + mh * 0.2, mw * 0.1, mw * 0.1, nt(S, '#f2c94c', 0.3)); }
    else if (L.mural === 'mountains') { fp(c, [[mx, my + mh], [mx + mw * 0.35, my + mh * 0.3], [mx + mw * 0.6, my + mh * 0.7], [mx + mw * 0.8, my + mh * 0.4], [mx + mw, my + mh]], nt(S, '#2f6b5a', 0.4)); fe(c, mx + mw * 0.7, my + mh * 0.2, mw * 0.1, mw * 0.1, nt(S, '#f08a5d', 0.3)); }
    else if (L.mural === 'waves') { for (i = 0; i < 5; i++) { c.strokeStyle = nt(S, ['#4d8fd1', '#e5567f', '#f2c94c', '#2f8f5b', '#9b6bd6'][i], 0.4); c.lineWidth = Math.max(2, mh * 0.06); c.beginPath(); for (var q = 0; q <= 12; q++) { var qx = mx + q / 12 * mw, qy = my + mh * (0.15 + i * 0.17) + Math.sin(q * 1.2 + i) * mh * 0.05; q ? c.lineTo(qx, qy) : c.moveTo(qx, qy); } c.stroke(); } }
    else for (i = 0; i < 14; i++) fe(c, mx + R() * mw, my + R() * mh, mw * 0.07, mw * 0.07, nt(S, pick(R, CLOTHES), 0.4)); }
  /* the rooms upstairs: bunks behind the glass */
  var wx0 = L.kind === 'modern' ? x + w * 0.4 : x + w * 0.04, ww = L.kind === 'modern' ? w * 0.2 : w * 0.26;
  for (var f = 0; f < 2; f++) for (i = 0; i < 2; i++) { var px = wx0 + i * (ww + w * 0.04), py = top + f * fh + fh * 0.16;
    if ((f + i) % 2 === 0 || R() < 0.4) bunkRoom(c, S, px, py, ww, fh * 0.7, true, pick(R, COVERS), trim, i + f * 2 + S.seed % 3); else pane(c, S, px, py, ww, fh * 0.7, R() < 0.6, trim, pick(R, CLOTHES), i); }
  /* the common room, open to the street */
  var cx0 = x + u * 0.1, cx1 = x + w - u * 0.1;
  if (open) { fr(c, cx0, G - gh + u * 0.06, cx1 - cx0, gh - u * 0.06, S.night ? '#ffcf86' : '#f6e0b6'); if (S.night) glow(c, (cx0 + cx1) / 2, G - gh * 0.5, w * 0.6, '255,190,110', 0.55);
    /* the bar shelf at the back, bottles, a fridge */
    fr(c, cx0 + u * 0.1, G - gh + u * 0.35, (cx1 - cx0) * 0.45, u * 0.03, nt(S, '#6a4026', 0.3)); for (i = 0; i < 7; i++) fr(c, cx0 + u * 0.14 + i * u * 0.13, G - gh + u * 0.22, u * 0.06, u * 0.13, pick(R, ['#2f8f5b', '#8a5a2a', '#c0392b', '#e8b84a', '#4d8fd1']));
    pr(c, cx1 - u * 0.5, G - u * 0.78, u * 0.38, u * 0.78, nt(S, '#d8dde2', 0.3), 0.5); fr(c, cx1 - u * 0.46, G - u * 0.72, u * 0.3, u * 0.3, 'rgba(160,210,240,.7)');
    fe(c, cx0 + u * 0.4, G - u * 0.12, u * 0.26, u * 0.14, nt(S, pick(R, ['#e5567f', '#4d8fd1', '#f2c94c', '#7fe0a4']), 0.35)); }
  else shutter(c, cx0, G - gh + u * 0.06, cx1 - cx0, gh - u * 0.06, S);
  fr(c, x, G - gh, w, u * 0.06, trim);
  /* the roof */
  if (L.roof === 'gable') gable(c, x + w / 2, w * 1.06, top, u * 0.32, nt(S, '#a8432f', 0.45), true);
  else { fr(c, x - u * 0.04, top - u * 0.06, w + u * 0.08, u * 0.06, trim); if (L.roof === 'deck') { rail(c, x, x + w, top - u * 0.06, u * 0.16, trim, u * 0.08); ln(c, [[x + w * 0.7, top - u * 0.06], [x + w * 0.7, top - u * 0.5]], trim, 1.5); paper(c, function (q) { q.beginPath(); q.moveTo(x + w * 0.5, top - u * 0.44); q.quadraticCurveTo(x + w * 0.7, top - u * 0.6, x + w * 0.9, top - u * 0.44); q.closePath(); }, nt(S, pick(R, ['#e5567f', '#f2c94c', '#2f8f5b']), 0.4), 0.8); } }
  /* the chalkboard: today's doings, in chalk */
  var bx = L.board, bw = u * 0.95, bh = u * 0.82, by = G - bh - u * 0.04;
  ln(c, [[bx - bw * 0.45, G + u * 0.04], [bx - bw * 0.35, by]], nt(S, '#6a4026', 0.4), 2.5); ln(c, [[bx + bw * 0.45, G + u * 0.04], [bx + bw * 0.35, by]], nt(S, '#6a4026', 0.4), 2.5);
  pr(c, bx - bw / 2, by, bw, bh, nt(S, '#6a4026', 0.4), 1); fr(c, bx - bw / 2 + 3, by + 3, bw - 6, bh - 6, '#24302a');
  c.save(); c.fillStyle = '#f2f2ea'; c.textAlign = 'left'; c.textBaseline = 'middle'; var fz = Math.max(8, u * 0.105);
  /* chalked on it: the hills and the sun, no words the place has not said */
  c.strokeStyle = '#f2f2ea'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(bx - bw / 2 + 8, by + bh * 0.78);
  [[0.25, 0.42], [0.42, 0.66], [0.6, 0.36], [0.82, 0.7]].forEach(function (p) { c.lineTo(bx - bw / 2 + bw * p[0], by + bh * p[1]); }); c.stroke();
  c.strokeStyle = '#f2c94c'; c.beginPath(); c.arc(bx + bw * 0.22, by + bh * 0.26, bh * 0.1, 0, 6.2832); c.stroke(); c.restore();
  /* the bike rack */
  for (i = 0; i < L.nb; i++) vehicle(c, 'bike', L.rack + L.side * i * u * 0.5, G + u * 0.12, u * 0.85, 1, nt(S, i ? pick(R, ['#d9342b', '#2f8f5b', '#f2c94c', '#2c3e6b']) : L.bikeCol, 0.4), false, R() * 6);
  if (L.nb) ln(c, [[L.rack - u * 0.3 + (L.side < 0 ? -u * (L.nb - 1) * 0.5 : 0), G + u * 0.02], [L.rack + u * 0.3 + (L.side > 0 ? u * (L.nb - 1) * 0.5 : 0), G + u * 0.02]], '#9aa0a8', 2);
  var sz = signSize(c, P, u), z = nameSign(c, x + w / 2, G - gh - sz.h + u * 0.01, P, u, L.signCol, open);
  var spx = L.side > 0 ? Math.max(x - u * 0.45, S.x0 + u * 0.75) : Math.min(x + w + u * 0.45, S.x1 - u * 0.75);
  if ((S.seed >>> 3) % 3) L.inc = spiritHouse(c, spx, G + u * 0.02, u * 0.88, S, S.seed); else plantAt(c, 'banana', spx, G, u, S, S.seed);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x, x1: x + w, y0: top - u * 0.3, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
/* cards in the common room: the dealer's hand goes out, a card flies to each player on a
   parabola, y = y₀ − 4h·u(1 − u); fairy lights; a cyclist rolls by, θ = x / r */
function hostelLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, i, open = L.st !== 'closed', F = L.folk, x = L.bx, w = L.bw, gh = u * 1.02;
  roomLights(S, L); riverGlints(S); incense(c, L.inc, t, 3);
  if (open) {
    fairy(c, x + u * 0.15, x + w - u * 0.15, G - gh + u * 0.1, u * 0.1, u * 0.16, t, S.night, ['255,214,120', '255,120,150', '140,220,255', '180,255,160']);
    var tx = x + w * (L.side > 0 ? 0.55 : 0.45), ty = G - u * 0.3, seats = [tx - u * 0.42, tx + u * 0.42];
    var dealer = F[0]; dealer.dir = 1; var dl = frac(t / 1500), reach = Math.sin(Math.min(1, dl * 3) * Math.PI);
    K.person(c, seats[0], G, u * 0.86, { lean: 0.15, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5], arms: [1.0 + reach * 0.5, 0.7 - reach * 0.5, 0.8, 1.2] }, dealer);
    var p2 = F[1]; p2.dir = -1; K.person(c, seats[1], G, u * 0.86, { lean: 0.12, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5], arms: [1.2, 1.1 + 0.1 * Math.sin(t / 600), 0.9, 1.2] }, p2);
    var p3 = F[2]; p3.dir = 1; K.person(c, tx, G - u * 0.02, u * 0.8, { lean: 0.05, seat: 0.3, legs: [1.4, -1.4, 1.35, -1.4], arms: [1.1, 1.3, 1.0, 1.4] }, p3);
    fr(c, tx - u * 0.36, ty, u * 0.72, u * 0.05, nt(S, '#7a4a2a', 0.3)); ln(c, [[tx - u * 0.3, ty + u * 0.04], [tx - u * 0.3, G]], nt(S, '#5a3a24', 0.3), 2); ln(c, [[tx + u * 0.3, ty + u * 0.04], [tx + u * 0.3, G]], nt(S, '#5a3a24', 0.3), 2);
    for (i = 0; i < 4; i++) fr(c, tx - u * 0.12 + i * u * 0.07, ty - u * 0.025, u * 0.05, u * 0.025, i % 2 ? '#f2f2f2' : '#ffe8e8');
    if (dl > 0.2 && dl < 0.75) { var q = (dl - 0.2) / 0.55, to = Math.floor(t / 1500) % 2 ? seats[1] - u * 0.2 : tx, cx = lerp(seats[0] + u * 0.25, to, q), cy = ty - u * 0.12 - 4 * u * 0.12 * q * (1 - q);
      c.save(); c.translate(cx, cy); c.rotate(q * 6); fr(c, -u * 0.035, -u * 0.05, u * 0.07, u * 0.1, '#ffffff'); fr(c, -u * 0.025, -u * 0.04, u * 0.05, u * 0.08, '#c0392b'); c.restore(); }
  }
  /* a cyclist going by on the road */
  var span = S.span + u * 3, cxp = S.x0 - u * 1.5 + frac(t / 14000 + (S.seed % 7) / 7) * span, dir = (S.seed >>> 5) % 2 ? 1 : -1; if (dir < 0) cxp = S.x1 + S.x0 - cxp;
  var cy2 = G + u * 0.48, rider = F[3]; rider.dir = dir; rider.skirt = 0;
  var pd = cxp / (u * 0.2) * dir, rp = { lean: 0.35, seat: 0.62, legs: [1.1 + 0.5 * Math.sin(pd), -1.4 + 0.5 * Math.sin(pd), 1.1 - 0.5 * Math.sin(pd), -1.4 - 0.5 * Math.sin(pd)], arms: [1.25, 0.2, 1.15, 0.25] };
  K.person(c, cxp - dir * u * 0.1, cy2, u * 0.9, rp, rider);
  vehicle(c, 'bike', cxp, cy2, u * 0.85, dir, nt(S, L.bikeCol, 0.3), S.night, pd);
  /* a backpacker arriving */
  var tr = F[4]; walker(S, tr, L.side > 0 ? S.x1 + u * 0.2 : S.x0 - u * 0.2, x + w / 2, 0.55, 0.3, G + u * 0.14, u * 0.92, 'pack', '#c0562a');
  if (!open) { dog(c, x + w * 0.5, G + u * 0.12, u * 0.55, '#c9a06a', true, t, 1); moth(c, x + w * 0.5, G - gh + u * 0.1, u * 0.05, t); }
}
function hostel(S) {
  var L = look(S, 'hostel', hostelDeal), u = S.hh; L.st = stateOf(S);
  var key = ['hostel', L.kind, S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0, L.st].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { L.wins = []; return hostelStill(q, S, L); });
  hostelLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- homes: shared pieces
   the barrier gate: a booth, a striped arm on a pivot that lifts for a car,
   θ = −(π/2)·ease(u); the car x(t) eases in, waits, passes through and fades at the door */
function gateDeal(S, R, L, pivot, inside, dir) {
  L.gate = { pivot: pivot, inside: inside, dir: dir, per: 14 + R() * 4, ph: R(), col: pick(R, ['#f2f2f2', '#2a2a30', '#c0392b', '#8a9aa8', '#2c3e6b', '#e8b84a', '#5a7a5a']) };
}
function boothStill(c, S, L) {
  var u = S.hh, G = S.deck, g = L.gate, bx = g.pivot - g.dir * u * 0.3;
  pr(c, bx - u * 0.24, G - u * 0.62, u * 0.48, u * 0.62, nt(S, '#e8e2d0', 0.45), 1);
  fr(c, bx - u * 0.18, G - u * 0.52, u * 0.36, u * 0.22, S.night ? '#ffe6a0' : '#a9cfe0');
  if (S.night) glow(c, bx, G - u * 0.42, u * 0.5, '255,220,140', 0.5);
  pr(c, bx - u * 0.3, G - u * 0.7, u * 0.6, u * 0.08, nt(S, '#a8432f', 0.45), 1);
  fr(c, g.pivot - u * 0.05, G - u * 0.42, u * 0.1, u * 0.42, nt(S, '#d8d0c0', 0.4));
}
function gateLive(S, L, guard) {
  var c = S.c, u = S.hh, G = S.deck, g = L.gate, t = S.t / 1000, ph = frac(t / g.per + g.ph) * g.per, d = g.dir, s = BODY.car * u;
  var stop = g.pivot + d * (u * 1.15 + s / 2), x, lift;
  if (ph < 3) x = lerp(stop + d * (S.span * 0.8), stop, ease(ph / 3)); else if (ph < 4.2) x = stop; else if (ph < 8) x = lerp(stop, g.inside, ease((ph - 4.2) / 3.8)); else x = null;
  lift = ph < 3.2 ? 0 : ph < 4.2 ? ease((ph - 3.2) / 1) : ph < 8.5 ? 1 : ph < 9.7 ? 1 - ease((ph - 8.5) / 1.2) : 0;
  /* the guard beside the booth, a hand up while the arm is up */
  if (guard) { guard.dir = d; K.person(c, g.pivot - d * u * 0.72, G + u * 0.04, u * 0.88, { lean: 0, legs: [0.05, 0, -0.05, 0], arms: [lift > 0.3 ? 2.6 : 0.15, lift > 0.3 ? 1.2 : 0.1, -0.08, 0.08] }, guard); }
  var th = -lift * Math.PI / 2 * 0.95, len = u * 1.1, py = G - u * 0.38;
  c.save(); c.translate(g.pivot, py); c.rotate(d * th);
  for (var k = 0; k < 6; k++) fr(c, d > 0 ? k * len / 6 : -(k + 1) * len / 6, -u * 0.025, len / 6, u * 0.05, k % 2 ? '#d9342b' : '#f2f2f2');
  c.restore(); fe(c, g.pivot, py, u * 0.05, u * 0.05, '#5a5a60');
  if (x != null) { var a = Math.min(1, Math.abs(x - g.inside) / (u * 0.6)); c.save(); c.globalAlpha = a; vehicle(c, 'car', x, G + u * 0.16, s, -d, nt(S, g.col, 0.3), S.night, x / (s * 0.08)); c.restore(); }
}
/* breeze blocks (chong lom): a lattice of circles in squares, for stair towers */
function breeze(c, x, y, w, h, s, col) { c.strokeStyle = col; c.lineWidth = 1; for (var yy = y; yy < y + h - s * 0.5; yy += s) for (var xx = x; xx < x + w - s * 0.5; xx += s) { c.strokeRect(xx + 1, yy + 1, s - 2, s - 2); c.beginPath(); c.arc(xx + s / 2, yy + s / 2, s * 0.3, 0, TAU); c.stroke(); } }
/* a resident walking a small dog on a lead */
function dogWalk(S, d, xa, xb, v, ph, y, h, col) {
  var me = walker(S, d, xa, xb, v, ph, y, h, null); if (!me) return;
  var c = S.c, dir = d.dir, dx = me.hand[0][0] + dir * h * 0.35, tr = Math.abs(Math.sin(S.t / 140)) * h * 0.02;
  ln(c, [me.hand[0], [dx, y - h * 0.18]], 'rgba(40,30,30,.7)', 1);
  fe(c, dx, y - h * 0.1 - tr, h * 0.12, h * 0.06, col); fe(c, dx + dir * h * 0.12, y - h * 0.17 - tr, h * 0.055, h * 0.05, col);
  ln(c, [[dx - dir * h * 0.1, y - h * 0.12], [dx - dir * h * 0.16, y - h * 0.2 - Math.sin(S.t / 120) * h * 0.03]], col, Math.max(1, h * 0.025));
  for (var k = 0; k < 2; k++) ln(c, [[dx + (k ? 1 : -1) * h * 0.07, y - h * 0.07], [dx + (k ? 1 : -1) * h * 0.07 + Math.sin(S.t / 140 + k * 3) * h * 0.03, y]], col, Math.max(1, h * 0.025));
}
/* a television's light in a dark room: blue, flickering on two sines */
function tvGlow(S, L) { if (!S.night || !L.tvs) return; var c = S.c; L.tvs.forEach(function (w, k) { var a = 0.45 + 0.25 * Math.sin(S.t / 170 + k * 3) + 0.15 * Math.sin(S.t / 53 + k); c.fillStyle = 'rgba(120,170,255,' + a.toFixed(2) + ')'; c.fillRect(w.x, w.y, w.w, w.h); }); }

/* ---------------------------------------------------------------- condo
   a tower dealt from the seed: its shape, its floors, its balconies and what is on them, a
   pool deck on the podium, a rooftop; residents come and go, the barrier lifts for a car.
   Real-estate records whose names say village or firm are drawn as 'moobaan' or 'agent'. */
var EST_RE = /หมู่บ้าน|village|ville\b|วิลล์|โครงการ|\bhome|โฮม|garden|การ์เด้น|\bpark\b|ปาร์ค|town\b|ทาวน์|บ้าน|land ?& ?house|แลนด์ แอนด์ เฮ้าส์|ชุมชน/;
var FIRM_RE = /บริษัท|บจก|หจก|ห้างหุ้น|จำกัด|co\.|\bltd|\bplc|propert|พร็อพเพอ|พร็อพเพอร์|realty|real ?estate|เรียลเอส|agency|เอเจนซี|ที่ดิน|construction|คอนสตรัค|design|ดีไซน์|เงินติดล้อ|สำนักงาน|office|developer|consult|รับสร้าง|นายหน้า|broker|ประกัน|สินเชื่อ|loan|ผ้าม่าน|โรงงาน/;
var TOWER_RE = /condo|คอนโด|residen|เรสซิเด|tower|ทาวเวอร์|mansion|แมนชั่น|apartment|อพาร์ท|suite|สวีท|\bplace\b|เพลส|court|คอร์ท|\bview\b|วิว|sky|สกาย/;
function condoAs(P) {
  var n = nameOf(P), sub = P.sub || [];
  if (sub.indexOf('condo') >= 0 || TOWER_RE.test(n)) return 'tower';
  if (FIRM_RE.test(n)) return 'agent';
  if (EST_RE.test(n)) return 'moobaan';
  return 'tower';
}
function condoDeal(S, R, L) {
  var u = S.hh, G = S.deck, sp = S.span, P = S.place || {};
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.kind = pick(R, ['slab', 'twin', 'stepped', 'slim', 'slab', 'curve']);
  L.lobby = u * 0.3; L.podium = R() < 0.5 ? u * 0.3 : 0;
  L.top = G - u * (2.0 + R() * 0.2);
  L.n = 6 + Math.floor(R() * 9); L.fh = (G - L.lobby - L.podium - L.top) / L.n;
  L.tw = u * (L.kind === 'slim' ? 1.3 + R() * 0.3 : L.kind === 'twin' ? 1.0 + R() * 0.2 : L.kind === 'curve' ? 1.8 + R() * 0.4 : 1.9 + R() * 0.6);
  L.wide = L.kind === 'twin' ? L.tw * 2 + u * 0.35 : L.tw;
  L.tx = side > 0 ? S.x0 + sp * 0.1 : S.x1 - sp * 0.1 - L.wide;
  L.wall = pick(R, ['#f2ede0', '#e9e4da', '#d9e2dc', '#cfd8e0', '#efe3c8', '#e8d2c0', '#dde6ea', '#f0e6d2']); L.acc = pick(R, ['#2c3e6b', '#2f6b5a', '#a8432f', '#5a5a60', '#c08a3a', '#3a6a8a', '#7a3a5a']);
  L.balc = pick(R, ['glass', 'rail', 'solid', 'glass']); L.roof = pick(R, ['sala', 'pool', 'garden', 'tanks', 'sala', 'crown']);
  L.signCol = pick(R, SIGNCOL); L.cover = pick(R, COVERS);
  var edge = side > 0 ? L.tx + L.wide : L.tx;
  L.door = L.tx + L.wide * (side > 0 ? 0.68 : 0.32);
  gateDeal(S, R, L, edge + side * u * 1.0, edge - side * u * 0.2, side);
  if (side > 0 ? L.gate.pivot + u * 2.3 > S.x1 : L.gate.pivot - u * 2.3 < S.x0) L.gate.pivot = side > 0 ? S.x1 - u * 2.3 : S.x0 + u * 2.3;
  L.folk = crew(S, 5, { casual: 0.75, sin: 0.15, mohom: 0.1 }, 0x91); L.folk[0].garb = 'casual'; L.folk[0].col = '#2c3e6b'; L.folk[0].low = '#2a2a30'; L.folk[0].hair = 4; L.folk[0].long = true;
  L.dogCol = pick(R, ['#f2ede0', '#c9a06a', '#3a2a22', '#e8dcc8']);
  return L;
}
/* one tower: floors of units, each a window and a balcony, something on the balcony */
function towerStill(c, S, L, R, x, w, top, n) {
  var u = S.hh, G = S.deck, base = G - L.lobby - L.podium, fh = (base - top) / n, wall = nt(S, L.wall, 0.45), acc = nt(S, L.acc, 0.4), i, k;
  pr(c, x, top, w, base - top, wall, 1.8);
  var cols = Math.max(2, Math.round(w / (u * 0.45))), pitch = w / cols;
  L.tvs = L.tvs || []; L.wins = L.wins || [];
  for (i = 0; i < n; i++) {
    var fy = top + i * fh;
    for (k = 0; k < cols; k++) {
      var wx = x + k * pitch + pitch * 0.12, ww = pitch * 0.76, wh = fh * 0.62, wy = fy + fh * 0.12, lit = R() < 0.4, tv = !lit && R() < 0.08, an = !lit && !tv && R() < 0.2;
      pane(c, S, wx, wy, ww, wh, lit, nt(S, '#5a6068', 0.4), R() < 0.4 ? pick(R, CLOTHES) : null, k + i);
      if (tv) L.tvs.push({ x: wx, y: wy, w: ww, h: wh });
      if (an) L.wins.push({ x: wx, y: wy, w: ww, h: wh, anim: true, per: 7 + R() * 16, ph: R() * TAU, b: 0.2 + R() * 0.5 });
      /* the balcony front and what stands on it */
      var by = fy + fh * 0.98, bh = fh * 0.34;
      if (L.balc === 'glass') { c.fillStyle = S.night ? 'rgba(120,150,190,.35)' : 'rgba(200,230,245,.55)'; c.fillRect(wx - pitch * 0.06, by - bh, ww + pitch * 0.12, bh); fr(c, wx - pitch * 0.06, by - bh, ww + pitch * 0.12, 1, nt(S, '#f2f2f2', 0.4)); }
      else if (L.balc === 'rail') { fr(c, wx - pitch * 0.06, by - bh, ww + pitch * 0.12, 1.2, nt(S, '#3a3f4a', 0.3)); for (var bx = wx - pitch * 0.06; bx < wx + ww + pitch * 0.06; bx += Math.max(2.5, u * 0.04)) fr(c, bx, by - bh, 1, bh, nt(S, '#3a3f4a', 0.3)); }
      else fr(c, wx - pitch * 0.06, by - bh, ww + pitch * 0.12, bh, acc);
      var thing = R();
      if (thing < 0.22) bush(c, wx + ww * (0.15 + R() * 0.7), by - bh, Math.max(2, fh * 0.28), [nt(S, '#3f7d45', 0.5), nt(S, '#5aa35a', 0.5), nt(S, R() < 0.4 ? '#d6337f' : '#3f7d45', 0.5)], 4, i * 31 + k);
      else if (thing < 0.36) { for (var q = 0; q < 3; q++) fr(c, wx + ww * (0.15 + q * 0.25), by - bh - fh * 0.32, ww * 0.18, fh * 0.3, nt(S, pick(R, CLOTHES), 0.4)); fr(c, wx, by - bh - fh * 0.33, ww, 1, 'rgba(60,60,60,.6)'); }
      else if (thing < 0.5) fr(c, wx + ww * 0.7, by - bh - fh * 0.22, ww * 0.24, fh * 0.22, nt(S, '#c9ccd2', 0.45));
    }
    fr(c, x - u * 0.02, fy + fh * 0.98, w + u * 0.04, Math.max(1.2, fh * 0.06), nt(S, '#d8d0c0', 0.45));
  }
  fr(c, x, top, w, u * 0.05, acc);
  /* the rooftop */
  var rt = top, rw = w;
  if (L.roof === 'sala') { var sw = Math.min(rw * 0.55, u * 1.2), sx = x + rw * 0.5 - sw / 2; fr(c, sx + sw * 0.08, rt - u * 0.13, 2, u * 0.13, nt(S, '#6a4026', 0.4)); fr(c, sx + sw * 0.92 - 2, rt - u * 0.13, 2, u * 0.13, nt(S, '#6a4026', 0.4)); lannaRoof(c, sx + sw / 2, sw, rt - u * 0.12, Math.max(u * 0.12, Math.min(u * 0.3, rt - (G - u * 2.3) - u * 0.12)), nt(S, '#a8432f', 0.45)); }
  else if (L.roof === 'pool') { fr(c, x + rw * 0.1, rt - u * 0.07, rw * 0.8, u * 0.07, S.night ? '#2a6a9a' : '#5fc6e8'); fr(c, x + rw * 0.1, rt - u * 0.12, rw * 0.8, u * 0.05, S.night ? 'rgba(120,150,190,.4)' : 'rgba(200,230,245,.6)'); if (S.night) glow(c, x + rw / 2, rt - u * 0.05, rw * 0.4, '120,200,255', 0.4); }
  else if (L.roof === 'garden') for (i = 0; i < 3; i++) bush(c, x + rw * (0.2 + i * 0.3), rt - u * 0.06, u * 0.1, [nt(S, '#3f7d45', 0.5), nt(S, '#5aa35a', 0.5)], 5, i + 50);
  else if (L.roof === 'tanks') { fr(c, x + rw * 0.2, rt - u * 0.2, u * 0.25, u * 0.2, nt(S, '#8a9aa8', 0.4)); fr(c, x + rw * 0.6, rt - u * 0.15, u * 0.35, u * 0.15, nt(S, '#d8d0c0', 0.4)); ln(c, [[x + rw * 0.85, rt], [x + rw * 0.85, rt - u * 0.22]], '#8a8f96', 1); }
  else { var ch = Math.max(u * 0.06, Math.min(u * 0.18, rt - (G - u * 2.3))); fp(c, [[x - u * 0.04, rt], [x + rw * 0.15, rt - ch], [x + rw * 0.85, rt - ch], [x + rw + u * 0.04, rt]], acc); laiKham(c, x + rw * 0.15, x + rw * 0.85, rt - ch / 2, u * 0.04); }
}
function condoStill(c, S, L) {
  var R = rnd((S.seed ^ 0xc0d) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, x = L.tx, w = L.wide, top = L.top, hits = [], i;
  street(c, S, 'road'); settingOn(c, S);
  L.tvs = []; L.wins = [];
  if (L.kind === 'twin') { towerStill(c, S, L, R, x, L.tw, top + u * 0.18, Math.max(4, L.n - 2)); towerStill(c, S, L, R, x + L.tw + u * 0.35, L.tw, top, L.n); fr(c, x + L.tw, G - L.lobby - L.podium - u * 0.5, u * 0.35, u * 0.5, nt(S, L.wall, 0.5)); }
  else if (L.kind === 'stepped') { var nb = Math.ceil(L.n * 0.45); towerStill(c, S, L, R, x, w, top + (L.n - nb) * L.fh, nb); towerStill(c, S, L, R, L.side > 0 ? x : x + w * 0.35, w * 0.65, top, L.n - nb); }
  else towerStill(c, S, L, R, x, w, top, L.n);
  if (L.kind === 'curve') { c.save(); c.globalAlpha = 0.25; fe(c, x + w * 0.5, top + (G - top) * 0.3, w * 0.1, (G - top) * 0.3, '#ffffff'); c.restore(); }
  /* the podium: car park slats, the pool deck on its roof */
  var base = G - L.lobby;
  if (L.podium) { pr(c, x - u * 0.15, base - L.podium, w + u * 0.3, L.podium, nt(S, mixc(L.wall, '#8a8f96', 0.25), 0.45), 1.4); for (var sy = base - L.podium + u * 0.06; sy < base - u * 0.04; sy += u * 0.07) fr(c, x - u * 0.1, sy, w + u * 0.2, u * 0.03, nt(S, '#5a6068', 0.4));
    var pd = L.side > 0 ? x + w * 0.5 : x - u * 0.15; fr(c, pd, base - L.podium - u * 0.05, w * 0.5 + u * 0.15, u * 0.05, S.night ? '#2a6a9a' : '#5fc6e8'); for (i = 0; i < 2; i++) { var ux = pd + u * (0.25 + i * 0.5); ln(c, [[ux, base - L.podium - u * 0.05], [ux, base - L.podium - u * 0.38]], '#8a8f96', 1); paper(c, function (q) { q.beginPath(); q.moveTo(ux - u * 0.2, base - L.podium - u * 0.32); q.quadraticCurveTo(ux, base - L.podium - u * 0.46, ux + u * 0.2, base - L.podium - u * 0.32); q.closePath(); }, nt(S, i ? '#f2c94c' : '#e5567f', 0.4), 0.6); } }
  /* the glazed ground floor behind a garden wall, and the porch out front with its canopy */
  var lx0 = x + u * 0.04, lx1 = x + w - u * 0.04;
  pr(c, x - u * 0.06, base, w + u * 0.12, L.lobby, nt(S, mixc(L.wall, '#c8bca8', 0.4), 0.45), 1.2);
  fr(c, lx0, base + u * 0.05, lx1 - lx0, L.lobby - u * 0.05, S.night ? '#ffe2a8' : '#cfe6ee');
  for (i = 0; i <= 8; i++) fr(c, lx0 + (lx1 - lx0) * i / 8 - 1, base + u * 0.05, 2, L.lobby - u * 0.05, nt(S, '#5a6068', 0.3));
  pr(c, x - u * 0.1, G - u * 0.2, w + u * 0.2, u * 0.2, nt(S, pick(R, ['#c8bca8', '#b8b2a6', '#9a8a7a', '#e8e2d0']), 0.45), 1);
  for (i = 0; i < Math.floor(w / (u * 0.22)); i++) bush(c, x + u * 0.05 + i * u * 0.22, G - u * 0.22, u * 0.1, [nt(S, '#3f7d45', 0.5), nt(S, '#55a04f', 0.5), nt(S, i % 3 ? '#3f7d45' : '#d6337f', 0.5)], 3, i + 70);
  var pw = u * 1.15, pdx = L.door - pw / 2, ph = u * 0.86;
  fr(c, pdx + u * 0.08, G - ph, pw - u * 0.16, ph, S.night ? '#ffe2a8' : '#dcecf2'); if (S.night) glow(c, L.door, G - ph * 0.45, pw * 0.9, '255,214,150', 0.55);
  for (i = 0; i <= 3; i++) fr(c, pdx + u * 0.08 + (pw - u * 0.16) * i / 3 - 1, G - ph, 2, ph, nt(S, '#5a6068', 0.3));
  pr(c, pdx - u * 0.12, G - ph - u * 0.08, pw + u * 0.24, u * 0.09, nt(S, L.acc, 0.4), 1.4); fr(c, pdx - u * 0.12, G - ph + u * 0.005, pw + u * 0.24, 2, '#e8b84a');
  pot(c, pdx - u * 0.22, G, u * 0.7, S, 2, 11); pot(c, pdx + pw + u * 0.22, G, u * 0.7, S, 2, 12);
  /* the garden strip, the gate and its booth */
  boothStill(c, S, L);
  var px = L.side > 0 ? Math.max(x - u * 0.5, S.x0 + u * 0.75) : Math.min(x + w + u * 0.5, S.x1 - u * 0.75);
  if (R() < 0.6) L.inc = spiritHouse(c, px, G + u * 0.02, u * 0.9, S, S.seed); else plantAt(c, pick(R, ['palm', 'frangipani']), px, G + u * 0.02, u, S, S.seed + 3);
  plantAt(c, pick(R, ['palm', 'frangipani', 'bougain', 'palm']), L.side > 0 ? S.x1 - u * 0.9 : S.x0 + u * 0.9, G + u * 0.02, u * 0.95, S, S.seed + 6);
  var sz = signSize(c, P, u), z = nameSign(c, L.door, G - ph - u * 0.08 - sz.h - u * 0.02, P, u, L.signCol, true);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x - u * 0.15, x1: x + w + u * 0.15, y0: top - u * 0.3, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
function condoLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, F = L.folk, out = L.side > 0 ? S.x1 + u * 0.3 : S.x0 - u * 0.3;
  roomLights(S, L); tvGlow(S, L); riverGlints(S); incense(c, L.inc, t, 4);
  if (L.roof === 'pool' && !S.night) { var ry = L.top - u * 0.05, sx = L.tx + L.wide * (0.2 + 0.6 * (0.5 + 0.5 * Math.sin(t / 3000))); fe(c, sx, ry, u * 0.04, u * 0.04, '#d29a6e'); }
  if (S.night) fairy(c, L.tx + L.wide * 0.05, L.tx + L.wide * 0.95, G - u * 0.24, u * 0.03, u * 0.12, t, true, ['255,214,120']);
  gateLive(S, L, F[0]);
  /* residents: one home with the shopping, one out with the dog, one more by day */
  walker(S, F[1], out, L.door, 0.5, 0.15, G + u * 0.14, u * 0.88, 'bag', '#f2f2f2');
  if (!S.night) { dogWalk(S, F[2], L.door, out, 0.45, 0.6, G + u * 0.2, u * 0.9, nt(S, L.dogCol, 0.3)); walker(S, F[3], L.door, out, 0.62, 0.35, G + u * 0.08, u * 0.86, 'books', '#e5567f'); }
}
function condo(S) {
  var P = S.place || {}, as = condoAs(P);
  if (as === 'moobaan') return moobaan(S);
  if (as === 'agent') return agent(S);
  var L = look(S, 'condo', condoDeal), u = S.hh; L.st = stateOf(S);
  var key = ['condo', L.kind, S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { return condoStill(q, S, L); });
  condoLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- moobaan
   a gated estate: the arch over the road in, the guard and his barrier, rows of the same
   house going back, the lake with its fountain (drops on parabolas, y = v₀t − ½gt²), kids
   on bicycles going round */
function mbDeal(S, R, L) {
  var u = S.hh, G = S.deck, sp = S.span, P = S.place || {};
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.arch = pick(R, ['lanna', 'modern', 'classic', 'lanna']); L.house = pick(R, ['twin', 'hip', 'flat', 'lanna', 'twin']);
  L.cols = [pick(R, ['#f2ede0', '#efe3c8', '#e8d2c0', '#d9e2dc', '#f0d8c8', '#e2d6ea']), pick(R, ['#cfe0e8', '#f5e6b8', '#e9e4da', '#f2ede0'])];
  L.roofCol = pick(R, ['#a8432f', '#5a6a7a', '#8a4a2a', '#2c3e6b', '#b5653a', '#4a4a50']); L.signCol = pick(R, SIGNCOL);
  var gw = signSize(S.c, P, u).w; L.aw = Math.max(gw + u * 0.5, u * 2.0);
  L.ax = side > 0 ? S.x0 + Math.max(u * 1.2, L.aw / 2 + u * 0.75) : S.x1 - Math.max(u * 1.2, L.aw / 2 + u * 0.75);
  L.lake = R() < 0.85; L.lakeSala = R() < 0.5; L.ducks = 1 + Math.floor(R() * 3);
  L.lx = side > 0 ? S.x1 - u * 2.1 : S.x0 + u * 2.1;
  gateDeal(S, R, L, L.ax + side * (L.aw / 2 - u * 0.02), L.ax + side * (L.aw / 2 + u * 2.2), -side);
  L.gate.noCar = true;
  L.folk = crew(S, 5, { casual: 0.8, sin: 0.1, mohom: 0.1 }, 0xa1); L.folk[0].garb = 'casual'; L.folk[0].col = '#2c3e6b'; L.folk[0].low = '#2a2a30'; L.folk[0].hair = 4; L.folk[0].long = true;
  return L;
}
/* one house of the estate, s = its scale */
function estateHouse(c, S, L, x, y, s, col, k) {
  var w = s * 1.1, h = s * 0.62, roof = nt(S, L.roofCol, 0.45), wall = nt(S, col, 0.45);
  pr(c, x - w / 2, y - h, w, h, wall, 0.9);
  pane(c, S, x - w * 0.36, y - h * 0.72, w * 0.26, h * 0.36, (k * 7) % 3 === 0, nt(S, '#f2f2f2', 0.4), null, k);
  fr(c, x + w * 0.12, y - h * 0.62, w * 0.18, h * 0.62, nt(S, '#6a4026', 0.4));
  if (L.house === 'twin') { paper(c, poly([[x - w * 0.58, y - h], [x - w * 0.25, y - h - s * 0.4], [x + w * 0.08, y - h]]), roof, 0.8); paper(c, poly([[x - w * 0.05, y - h], [x + w * 0.28, y - h - s * 0.32], [x + w * 0.6, y - h]]), roof, 0.8); }
  else if (L.house === 'hip') hipRoof(c, x, w * 1.1, y - h, s * 0.3, roof);
  else if (L.house === 'flat') { fr(c, x - w * 0.55, y - h - s * 0.06, w * 1.1, s * 0.08, roof); fr(c, x - w * 0.5, y - h * 0.55, w * 0.3, h * 0.04, roof); }
  else gable(c, x, w * 1.05, y - h, s * 0.42, roof, true);
}
function mbStill(c, S, L) {
  var R = rnd((S.seed ^ 0xb0b) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, i, hits = [];
  street(c, S, 'road'); settingOn(c, S);
  /* the rows of houses going back: the far row small and high, the near row larger */
  var row0 = G - u * 0.5, row1 = G - u * 0.12, sp0 = u * 0.8, sp1 = u * 1.05;
  for (i = 0, x = S.x0 + u * 0.3; x < S.x1; x += sp0, i++) estateHouse(c, S, L, x, row0, u * 0.52, L.cols[i % 2], i);
  for (var j = 0, x = S.x0 + u * 0.6; x < S.x1; x += sp1, j++) { if (Math.abs(x - L.ax) < L.aw / 2 + u * 0.3) continue; estateHouse(c, S, L, x, row1, u * 0.7, L.cols[(j + 1) % 2], j + 20); if (j % 2) palm(c, x + sp1 / 2, G + u * 0.02, u * 1.1, S, j % 4 ? 1 : -1); }
  fr(c, S.x0 - 4, G - u * 0.05, S.span + 8, u * 0.07, nt(S, '#c9c1b0', 0.45));
  /* the lake on the near ground */
  if (L.lake) { var lw = u * 1.8, ly = G + (S.H - G) * 0.55; paper(c, function (q) { q.beginPath(); q.ellipse(L.lx, ly, lw, (S.H - G) * 0.32, 0, 0, TAU); }, nt(S, '#4b8fc9', 0.45), 0.6); L.lakeY = ly; L.lakeW = lw;
    if (L.lakeSala) { var sx = L.lx + lw * 0.45; fr(c, sx - u * 0.35, ly - u * 0.02, u * 0.7, u * 0.04, nt(S, '#6a4026', 0.4)); fr(c, sx - u * 0.3, ly - u * 0.45, 2, u * 0.45, nt(S, '#6a4026', 0.4)); fr(c, sx + u * 0.3 - 2, ly - u * 0.45, 2, u * 0.45, nt(S, '#6a4026', 0.4)); lannaRoof(c, sx, u * 0.8, ly - u * 0.43, u * 0.35, nt(S, '#a8432f', 0.45)); } }
  /* the arch over the road in */
  var ax = L.ax, aw = L.aw, x0 = ax - aw / 2, x1 = ax + aw / 2, at = G - u * 1.55, pc = nt(S, L.arch === 'modern' ? '#5a5a60' : '#e8e2d0', 0.45);
  pr(c, x0 - u * 0.22, at, u * 0.3, G - at, pc, 1.4); pr(c, x1 - u * 0.08, at, u * 0.3, G - at, pc, 1.4);
  if (L.arch === 'classic') { paper(c, function (q) { q.beginPath(); q.moveTo(x0 - u * 0.25, at + u * 0.25); q.quadraticCurveTo(ax, at - u * 0.5, x1 + u * 0.25, at + u * 0.25); q.lineTo(x1 + u * 0.25, at); q.quadraticCurveTo(ax, at - u * 0.68, x0 - u * 0.25, at); q.closePath(); }, pc, 1.2); [x0 - u * 0.07, x1 + u * 0.07].forEach(function (cx) { fe(c, cx, at - u * 0.04, u * 0.12, u * 0.06, pc); }); }
  else if (L.arch === 'modern') { pr(c, x0 - u * 0.3, at - u * 0.16, aw + u * 0.6, u * 0.18, nt(S, '#2a2a30', 0.4), 1.4); fr(c, x0 - u * 0.3, at - u * 0.04, aw + u * 0.6, u * 0.03, nt(S, '#e8b84a', 0.3)); }
  else { pr(c, x0 - u * 0.3, at - u * 0.08, aw + u * 0.6, u * 0.1, nt(S, '#6a4026', 0.4), 1.2); lannaRoof(c, ax, aw * 0.75, at - u * 0.08, u * 0.42, nt(S, '#a8432f', 0.45)); laiKham(c, x0, x1, at - u * 0.03, u * 0.045); }
  var z = nameSign(c, ax, at + u * 0.08, P, u, L.signCol, true);
  boothStill(c, S, L);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x0 - u * 0.3, x1: x1 + u * 0.3, y0: at - u * 0.6, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
function mbLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, F = L.folk, i;
  roomLights(S, L); riverGlints(S);
  if (L.lake) { /* the fountain: drops thrown up and falling, y = v₀t − ½gt² */
    var fx = L.lx - L.lakeW * 0.2, fy = L.lakeY;
    for (i = 0; i < 14; i++) { var q = frac(t / 1300 + i / 14), a = (i % 7 - 3) * 0.12, vx = Math.sin(a) * u * 0.5, hgt = u * 0.55; c.fillStyle = S.night ? 'rgba(200,220,255,.7)' : 'rgba(255,255,255,.85)'; c.beginPath(); c.arc(fx + vx * q, fy - hgt * 4 * q * (1 - q), Math.max(1, u * 0.02), 0, TAU); c.fill(); }
    if (S.night) glow(c, fx, fy - u * 0.2, u * 0.5, '140,200,255', 0.3);
    for (i = 0; i < L.ducks; i++) { var dx = L.lx + Math.sin(t / 6000 + i * 2) * L.lakeW * 0.6, dy = L.lakeY + u * (0.04 + i * 0.05), dd = Math.cos(t / 6000 + i * 2) > 0 ? 1 : -1; fe(c, dx, dy, u * 0.08, u * 0.04, '#f2f2f2'); fe(c, dx + dd * u * 0.07, dy - u * 0.05, u * 0.035, u * 0.035, '#f2f2f2'); fp(c, [[dx + dd * u * 0.1, dy - u * 0.055], [dx + dd * u * 0.14, dy - u * 0.045], [dx + dd * u * 0.1, dy - u * 0.035]], '#e8a23a'); } }
  /* the guard lifts the bar for the kids by day, for a car at night */
  gateLive(S, L, F[0]);
  if (!S.night) for (i = 0; i < 2; i++) {   /* kids cycling round the road */
    var per = 11 + i * 3, f = frac(t / 1000 / per + i * 0.5), dir = f < 0.5 ? 1 : -1, ff = f < 0.5 ? f * 2 : 2 - f * 2, x = lerp(S.x0 + u * 1.0, S.x1 - u * 1.0, ease(ff)), y = G + u * (0.26 + i * 0.12), kid = F[1 + i], h = u * 0.62;
    kid.dir = dir; kid.skirt = 0; var pd = x / (h * 0.25), rp = { lean: 0.3, seat: 0.66, legs: [1.1 + 0.5 * Math.sin(pd), -1.4 + 0.5 * Math.sin(pd), 1.1 - 0.5 * Math.sin(pd), -1.4 - 0.5 * Math.sin(pd)], arms: [1.25, 0.2, 1.15, 0.25] };
    K.person(c, x - dir * h * 0.12, y, h, rp, kid); vehicle(c, 'bike', x, y, u * 0.62, dir, ['#e5567f', '#4d8fd1', '#f2c94c'][i], false, pd);
  }
  else walker(S, F[3], L.side > 0 ? S.x1 + u * 0.3 : S.x0 - u * 0.3, L.ax, 0.5, 0.2, G + u * 0.12, u * 0.88, 'bag', '#f2f2f2');
}
function moobaan(S) {
  var L = look(S, 'moobaan', mbDeal), u = S.hh; L.st = stateOf(S);
  var key = ['moobaan', S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { L.wins = []; return mbStill(q, S, L); });
  mbLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- agent
   an estate agent's shop: house cards in the window marked for sale or rent, and inside,
   the agent jingling the keys over a house model while a couple look on; keys swing on a
   pendulum, θ = θ₀·sin ωt */
function agDeal(S, R, L) {
  var u = S.hh, sp = S.span;
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.kind = pick(R, ['shophouse', 'glass', 'teak', 'shophouse']); L.bw = u * (3.0 + R() * 0.6); L.bx = side > 0 ? S.x0 + sp * 0.14 : S.x1 - sp * 0.14 - L.bw;
  L.wall = pick(R, ['#f2ede0', '#e8d2b0', '#d9e2dc', '#cfe0e8', '#f5e6b8', '#2c3e6b', '#2f6b5a']); L.signCol = pick(R, SIGNCOL); L.awn = pick(R, ['#c0392b', '#2f6b5a', '#2c3e6b', '#e8a23a', '#7a3a5a']);
  L.model = pick(R, ['#f2ede0', '#e8d2b0', '#cfe0e8']); L.modelRoof = pick(R, ['#a8432f', '#5a6a7a', '#6a3a24']);
  L.cards = []; for (var i = 0; i < 8; i++) L.cards.push({ sale: R() < 0.55, col: pick(R, ['#f2ede0', '#e8d2b0', '#cfe0e8', '#f0d8c8']), roof: pick(R, ['#a8432f', '#5a6a7a', '#6a3a24', '#2c3e6b']), kind: Math.floor(R() * 3) });
  L.folk = crew(S, 4, { casual: 0.85, sin: 0.1, mohom: 0.05 }, 0xb1); L.folk[0].garb = 'casual'; L.folk[0].long = true; L.folk[0].col = pick(R, ['#2c3e6b', '#2a2a30', '#f2f2f2', '#7a3a5a']);
  return L;
}
/* a listing card: a little house drawn on it and a tag, ขาย (for sale) red or เช่า (for rent) blue */
function card(c, S, x, y, w, h, C) {
  fr(c, x, y, w, h, '#fbf8f0'); fr(c, x, y, w, 1, 'rgba(0,0,0,.2)');
  var hx = x + w / 2, hy = y + h * 0.62, hw = w * 0.5;
  if (C.kind === 2) { fr(c, hx - hw * 0.35, hy - h * 0.45, hw * 0.7, h * 0.45, C.col); for (var k = 0; k < 3; k++) fr(c, hx - hw * 0.25, hy - h * (0.38 - k * 0.12), hw * 0.5, h * 0.05, '#7aa6c9'); }
  else { fr(c, hx - hw / 2, hy - h * 0.25, hw, h * 0.25, C.col); fp(c, [[hx - hw * 0.62, hy - h * 0.25], [hx, hy - h * 0.48], [hx + hw * 0.62, hy - h * 0.25]], C.roof); if (C.kind) fr(c, hx + hw * 0.1, hy - h * 0.15, hw * 0.2, h * 0.15, '#6a4026'); }
  fr(c, x, y + h * 0.72, w, h * 0.28, C.sale ? '#c0392b' : '#2f6db5');
  c.fillStyle = '#ffffff'; c.font = '800 ' + Math.round(Math.max(7, h * 0.22)) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(C.sale ? 'ขาย' : 'เช่า', hx, y + h * 0.86);
}
function agStill(c, S, L) {
  var R = rnd((S.seed ^ 0xa9e) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, x = L.bx, w = L.bw, open = L.st !== 'closed', hits = [], i;
  street(c, S, 'road'); settingOn(c, S);
  var top = L.kind === 'glass' ? G - u * 1.45 : G - u * 2.0, gh = u * 1.15, wall = nt(S, L.kind === 'teak' ? '#8a5a34' : L.wall, 0.45);
  pr(c, x, top, w, G - top, wall, 1.6);
  if (L.kind === 'teak') planks(c, x, top, w, G - top, 4);
  if (L.kind !== 'glass') { for (i = 0; i < 2; i++) pane(c, S, x + w * (0.15 + i * 0.45), top + u * 0.15, w * 0.3, (G - gh - top) * 0.6, R() < 0.5, nt(S, '#f2ede0', 0.35), pick(R, CLOTHES), i); if (L.kind === 'teak') gable(c, x + w / 2, w * 1.06, top, u * 0.32, nt(S, '#6a3a24', 0.45)); else fr(c, x - u * 0.04, top - u * 0.06, w + u * 0.08, u * 0.06, nt(S, '#d8d0c0', 0.45)); }
  else { fr(c, x - u * 0.06, top - u * 0.08, w + u * 0.12, u * 0.1, nt(S, '#2a2a30', 0.4)); }
  /* the shop window full of listings, and the open door on the office */
  var wx = x + u * 0.12, ww = w * 0.48, wy = G - gh + u * 0.12, wh = gh - u * 0.3;
  fr(c, wx - 2, wy - 2, ww + 4, wh + 4, nt(S, '#3a3f4a', 0.3)); fr(c, wx, wy, ww, wh, open ? (S.night ? '#ffe6b0' : '#eef4f6') : '#2a2c38');
  if (open || !S.night) { var cw = ww / 4.4, ch = wh / 2.3; for (i = 0; i < 8; i++) card(c, S, wx + cw * 0.2 + (i % 4) * cw * 1.07, wy + ch * 0.12 + Math.floor(i / 4) * ch * 1.1, cw * 0.9, ch * 0.95, L.cards[i]); }
  if (S.night && open) glow(c, wx + ww / 2, wy + wh / 2, ww * 0.6, '255,220,150', 0.4);
  var ox = wx + ww + u * 0.12, ow = x + w - u * 0.12 - ox;
  if (open) { fr(c, ox, wy - u * 0.06, ow, gh - u * 0.06, S.night ? '#ffd690' : '#f3e2c2'); if (S.night) glow(c, ox + ow / 2, G - gh * 0.45, ow * 0.7, '255,200,120', 0.45);
    /* a framed plan on the back wall, the table */
    fr(c, ox + ow * 0.6, wy + u * 0.05, ow * 0.3, u * 0.24, '#fbf8f0'); c.strokeStyle = '#2f6db5'; c.lineWidth = 1; c.strokeRect(ox + ow * 0.63, wy + u * 0.08, ow * 0.24, u * 0.18); c.beginPath(); c.moveTo(ox + ow * 0.75, wy + u * 0.08); c.lineTo(ox + ow * 0.75, wy + u * 0.26); c.moveTo(ox + ow * 0.63, wy + u * 0.17); c.lineTo(ox + ow * 0.75, wy + u * 0.17); c.stroke(); }
  else shutter(c, ox, wy - u * 0.06, ow, gh - u * 0.06, S);
  L.ox = ox; L.ow = ow;
  /* the awning, scalloped, over both */
  var ay = G - gh - u * 0.02; paper(c, function (q) { q.beginPath(); q.moveTo(x - u * 0.1, ay - u * 0.12); q.lineTo(x + w + u * 0.1, ay - u * 0.12); q.lineTo(x + w + u * 0.2, ay + u * 0.08); for (var k = 0, n = Math.round((w + u * 0.4) / (u * 0.25)); k <= n; k++) { var sx = x + w + u * 0.2 - k * (w + u * 0.4) / n; q.quadraticCurveTo(sx + (w + u * 0.4) / n / 2, ay + u * 0.16, sx, ay + u * 0.08); } q.closePath(); }, nt(S, L.awn, 0.4), 1);
  var sz = signSize(c, P, u), z = nameSign(c, x + w / 2, Math.max(top + u * 0.02, ay - u * 0.14 - sz.h), P, u, L.signCol, open);
  /* a for-sale board in the yard */
  var bx = L.side > 0 ? x + w + u * 0.75 : x - u * 0.75; ln(c, [[bx, G + u * 0.04], [bx, G - u * 0.6]], nt(S, '#6a4026', 0.4), 2.5); fr(c, bx - u * 0.35, G - u * 0.62, u * 0.7, u * 0.04, nt(S, '#6a4026', 0.4));
  pr(c, bx - u * 0.32, G - u * 0.56, u * 0.64, u * 0.34, '#fbf8f0', 0.7); fr(c, bx - u * 0.32, G - u * 0.56, u * 0.64, u * 0.12, '#c0392b');
  c.save(); c.fillStyle = '#ffffff'; c.font = '800 ' + Math.round(Math.max(8, u * 0.1)) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ขาย · FOR SALE', bx, G - u * 0.5, u * 0.6);
  fp(c, [[bx - u * 0.12, G - u * 0.3], [bx, G - u * 0.42], [bx + u * 0.12, G - u * 0.3]], '#a8432f'); fr(c, bx - u * 0.09, G - u * 0.3, u * 0.18, u * 0.07, '#e8d2b0'); c.restore();
  var px = L.side > 0 ? Math.max(x - u * 0.45, S.x0 + u * 0.75) : Math.min(x + w + u * 0.45, S.x1 - u * 0.75);
  if (R() < 0.65) L.inc = spiritHouse(c, px, G + u * 0.02, u * 0.9, S, S.seed); else pot(c, px, G, u * 0.8, S, 1, S.seed);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x, x1: x + w, y0: top - u * 0.3, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
function agLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, F = L.folk, open = L.st !== 'closed';
  incense(c, L.inc, t, 5); riverGlints(S);
  if (open) {
    var tx = L.ox + L.ow * 0.5, ty = G - u * 0.36;
    /* the couple, one pointing at the model */
    var a = F[1], b = F[2]; a.dir = -1; b.dir = -1; var pt = 0.5 + 0.5 * Math.sin(t / 1400);
    K.person(c, tx + u * 0.42, G + u * 0.02, u * 0.88, { lean: 0.12, legs: [0.05, 0, -0.05, 0], arms: [1.2 + pt * 0.5, 0.2, 0.15, 0.1] }, a);
    K.person(c, tx + u * 0.7, G + u * 0.03, u * 0.84, STAND, b);
    /* the agent with the keys */
    var ag = F[0]; ag.dir = 1; var me = K.person(c, tx - u * 0.42, G + u * 0.02, u * 0.9, { lean: 0.05, legs: [0.05, 0, -0.05, 0], arms: [1.6, 0.3, 0.2, 0.2] }, ag);
    var kh = me.hand[0], th = 0.5 * Math.sin(t / 220); c.save(); c.translate(kh[0], kh[1]); c.rotate(th); ln(c, [[0, 0], [0, u * 0.06]], '#c9ccd2', 1); fe(c, 0, u * 0.08, u * 0.025, u * 0.025, '#e8b84a'); fr(c, -1, u * 0.1, 2, u * 0.06, '#e8b84a'); fr(c, u * 0.02, u * 0.07, u * 0.03, u * 0.05, '#c0392b'); c.restore();
    /* the table and the house model on it */
    fr(c, tx - u * 0.28, ty, u * 0.56, u * 0.05, nt(S, '#6a4026', 0.3)); ln(c, [[tx - u * 0.22, ty], [tx - u * 0.22, G]], nt(S, '#5a3a24', 0.3), 2); ln(c, [[tx + u * 0.22, ty], [tx + u * 0.22, G]], nt(S, '#5a3a24', 0.3), 2);
    fr(c, tx - u * 0.14, ty - u * 0.14, u * 0.28, u * 0.14, nt(S, L.model, 0.25)); fp(c, [[tx - u * 0.19, ty - u * 0.14], [tx, ty - u * 0.28], [tx + u * 0.19, ty - u * 0.14]], nt(S, L.modelRoof, 0.25)); fr(c, tx - u * 0.1, ty - u * 0.1, u * 0.06, u * 0.05, '#7aa6c9'); fr(c, tx + u * 0.03, ty - u * 0.09, u * 0.05, u * 0.09, '#6a4026');
  } else { dog(c, L.bx + L.bw * 0.4, G + u * 0.12, u * 0.55, '#c9a06a', true, t, 1); moth(c, L.bx + L.bw * 0.5, G - u * 1.15, u * 0.05, t); }
  /* someone stopping to read the window by day */
  if (!S.night) walker(S, F[3], L.side > 0 ? S.x1 + u * 0.3 : S.x0 - u * 0.3, L.bx + L.bw * 0.3, 0.45, 0.25, G + u * 0.12, u * 0.88, null);
}
function agent(S) {
  var L = look(S, 'agent', agDeal), u = S.hh; L.st = stateOf(S); if (L.st === 'quiet') L.st = 'closed';
  var key = ['agent', L.kind, S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0, L.st].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { return agStill(q, S, L); });
  agLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- apartment
   low-rise blocks let by the month: open walkways with doors along them, washing on the
   rails, a stair tower of breeze blocks, scooters under the carport, the board for rooms */
function apDeal(S, R, L) {
  var u = S.hh, sp = S.span, P = S.place || {}, n = nameOf(P);
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.storeys = 3 + Math.floor(R() * 3); L.fh = u * (L.storeys > 4 ? 0.36 : 0.42); L.style = pick(R, ['corridor', 'balcony', 'corridor', 'shop']);
  L.blocks = R() < 0.35 ? 2 : 1; L.bw = u * (L.blocks === 2 ? 1.6 + R() * 0.3 : 2.7 + R() * 0.6);
  L.wide = L.blocks === 2 ? L.bw * 2 + u * 0.35 : L.bw;
  L.bx = side > 0 ? S.x0 + sp * 0.1 : S.x1 - sp * 0.1 - L.wide;
  L.wall = pick(R, ['#f2ede0', '#f0d8c8', '#d9e2dc', '#f5e6b8', '#e2d6ea', '#cfe0e8', '#f2c9a8', '#e9e4da']); L.acc = pick(R, ['#2f6b5a', '#a8432f', '#2c3e6b', '#c08a3a', '#7a3a5a', '#5a7a4a']);
  L.board = !/hotel|โรงแรม|resort|รีสอร์ท|รายวัน|daily/.test(n);
  L.port = side > 0 ? L.bx + L.wide + u * 0.3 : L.bx - u * 0.3; L.portW = u * 2.2;
  if (side > 0 ? L.port + L.portW > S.x1 - u * 0.8 : L.port - L.portW < S.x0 + u * 0.8) L.portW = Math.max(u * 1.2, (side > 0 ? S.x1 - u * 0.8 - L.port : L.port - S.x0 - u * 0.8));
  L.signCol = pick(R, SIGNCOL);
  L.folk = crew(S, 5, { casual: 0.7, sin: 0.2, mohom: 0.1 }, 0xc1);
  return L;
}
function apBlock(c, S, L, R, x, w) {
  var u = S.hh, G = S.deck, fh = L.fh, n = L.storeys, top = G - n * fh, wall = nt(S, L.wall, 0.45), acc = nt(S, L.acc, 0.4), i, k;
  pr(c, x, top, w, G - top, wall, 1.6);
  var units = Math.max(2, Math.floor(w / (u * 0.62))), pitch = w / units;
  L.wins = L.wins || []; L.tvs = L.tvs || []; L.tubes = L.tubes || [];
  for (i = 0; i < n; i++) {
    var fy = top + i * fh, ground = i === n - 1;
    for (k = 0; k < units; k++) {
      var ux = x + k * pitch;
      if (ground && L.style === 'shop' && k < 2) { var open = L.st !== 'closed' && !(S.night && L.st === 'quiet'); if (open) { fr(c, ux + pitch * 0.08, fy + fh * 0.12, pitch * 0.84, fh * 0.88, S.night ? '#ffd690' : '#f3dcb0'); for (var b = 0; b < 4; b++) fr(c, ux + pitch * (0.15 + b * 0.18), fy + fh * 0.3, pitch * 0.12, fh * 0.2, pick(R, ['#c0562a', '#2f6b5a', '#e8b84a', '#4d8fd1'])); } else shutter(c, ux + pitch * 0.08, fy + fh * 0.12, pitch * 0.84, fh * 0.88, S); continue; }
      var lit = R() < 0.45, tv = !lit && R() < 0.1;
      fr(c, ux + pitch * 0.1, fy + fh * 0.18, pitch * 0.26, fh * 0.78, nt(S, pick(R, ['#6a4026', '#8a8f96', '#2f6b5a', '#a8432f', '#e8e2d0']), 0.4));
      pane(c, S, ux + pitch * 0.48, fy + fh * 0.22, pitch * 0.38, fh * 0.4, lit, nt(S, '#f2ede0', 0.35), R() < 0.6 ? pick(R, CLOTHES) : null, k + i);
      if (tv) L.tvs.push({ x: ux + pitch * 0.48, y: fy + fh * 0.22, w: pitch * 0.38, h: fh * 0.4 });
      else if (!lit && R() < 0.2) L.wins.push({ x: ux + pitch * 0.48, y: fy + fh * 0.22, w: pitch * 0.38, h: fh * 0.4, anim: true, per: 6 + R() * 12, ph: R() * TAU, b: 0.2 + R() * 0.5 });
      if (R() < 0.35) fr(c, ux + pitch * 0.12, fy + fh * 0.9, pitch * 0.1, fh * 0.06, pick(R, CLOTHES));   /* shoes by the door */
    }
    if (!ground || L.style !== 'shop') {
      var ry = fy + fh;
      if (L.style === 'balcony') for (k = 0; k < units; k++) { var bx = x + k * pitch + pitch * 0.42; fr(c, bx, ry - fh * 0.34, pitch * 0.5, fh * 0.34, acc); }
      else if (!ground) { fr(c, x - u * 0.06, ry - fh * 0.36, w + u * 0.12, fh * 0.36, nt(S, mixc(L.wall, '#8a8f96', 0.2), 0.45)); for (k = 0; k < units * 3; k++) { var hx = x + (k + 0.5) * w / (units * 3); fe(c, hx, ry - fh * 0.2, fh * 0.05, fh * 0.07, nt(S, '#5a6068', 0.4)); } }
      fr(c, x - u * 0.06, ry - 2, w + u * 0.12, 3, acc);
      if (!ground) { L.tubes.push({ x: x + w * 0.3, y: fy + fh * 0.06, w: u * 0.18 }); L.tubes.push({ x: x + w * 0.72, y: fy + fh * 0.06, w: u * 0.18 }); }
      /* washing over the rail */
      if (!ground) for (k = 0; k < units; k++) if (R() < 0.45) for (var q = 0; q < 2 + Math.floor(R() * 2); q++) fr(c, x + k * pitch + pitch * (0.2 + q * 0.2), ry - fh * 0.42, pitch * 0.14, fh * 0.3, nt(S, pick(R, CLOTHES), 0.4));
    }
  }
  /* the stair tower in breeze blocks, at the outer end */
  var sx = L.side > 0 ? x - u * 0.38 : x + w; pr(c, sx, top - u * 0.12, u * 0.38, G - top + u * 0.12, nt(S, mixc(L.wall, '#ffffff', 0.25), 0.45), 1.2); breeze(c, sx + u * 0.04, top, u * 0.3, G - top - u * 0.3, Math.max(5, u * 0.1), nt(S, '#9a8f80', 0.4));
  fr(c, x - u * 0.06, top - u * 0.07, w + u * 0.12, u * 0.07, acc);
  if (R() < 0.5) { fr(c, x + w * 0.65, top - u * 0.22, u * 0.24, u * 0.15, nt(S, '#5a8ab0', 0.4)); ln(c, [[x + w * 0.2, top - u * 0.07], [x + w * 0.2, top - u * 0.3]], '#8a8f96', 1); }
  return top;
}
function apStill(c, S, L) {
  var R = rnd((S.seed ^ 0xa9a) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, hits = [], i, x = L.bx;
  street(c, S, 'road'); settingOn(c, S);
  L.wins = []; L.tvs = []; L.tubes = [];
  var top = apBlock(c, S, L, R, x, L.bw); if (L.blocks === 2) top = Math.min(top, apBlock(c, S, L, R, x + L.bw + u * 0.35, L.bw));
  /* the carport: a tin roof on posts, scooters under it */
  var p0 = L.side > 0 ? L.port : L.port - L.portW, p1 = p0 + L.portW, py = G - u * 0.78;
  [p0 + u * 0.08, p1 - u * 0.08].forEach(function (px) { fr(c, px - 1.5, py, 3, G - py, nt(S, '#8a8f96', 0.4)); });
  paper(c, poly([[p0 - u * 0.1, py], [p1 + u * 0.1, py - u * 0.08], [p1 + u * 0.1, py - u * 0.02], [p0 - u * 0.1, py + u * 0.06]]), nt(S, pick(R, ['#2f6b8a', '#a8432f', '#8a9aa8', '#2f6b5a']), 0.4), 1);
  var nS = Math.max(1, Math.floor((L.portW - u * 0.2) / (u * 0.55))), scols = ['#d9342b', '#f2f2f2', '#2c3e6b', '#e8b84a', '#1f1f24', '#e5567f', '#2f8f5b'];
  for (i = nS - 1; i >= 0; i--) vehicle(c, 'scooter', p0 + u * 0.4 + i * (L.portW - u * 0.6) / Math.max(1, nS - 1 || 1), G + u * 0.04 + (i % 2) * u * 0.04, u * 0.85, -L.side, nt(S, pick(R, scols), 0.4), false, R() * 6);
  if (S.night) glow(c, (p0 + p1) / 2, py + u * 0.1, L.portW * 0.4, '220,240,255', 0.35);
  /* the board: a room free, by the month */
  if (L.board && said(S, /เช่า|rent|ห้องว่าง|monthly|รายเดือน/i)) { var f = Math.max(9, u * 0.13);   /* only where the place says so */ c.save(); c.font = '800 ' + Math.round(f) + 'px ' + FONT;
    var bw = Math.max(c.measureText('ห้องว่าง').width, c.measureText('Room for rent').width * 0.85) + u * 0.18, bh = f * 3.1, by = py + u * 0.06;
    /* hung from the carport's outer beam */
    var bx = clamp(L.side > 0 ? p1 - bw * 0.3 : p0 + bw * 0.3, S.x0 + bw / 2 + u * 0.7, S.x1 - bw / 2 - u * 0.7);
    ln(c, [[bx - bw * 0.3, py + u * 0.02], [bx - bw * 0.3, by]], '#8a8f96', 1.2); ln(c, [[bx + bw * 0.3, py + u * 0.02], [bx + bw * 0.3, by]], '#8a8f96', 1.2);
    pr(c, bx - bw / 2, by, bw, bh, '#fbf8f0', 0.8); c.strokeStyle = '#c0392b'; c.lineWidth = 1.2; c.strokeRect(bx - bw / 2 + 2, by + 2, bw - 4, bh - 4);
    c.fillStyle = '#c0392b'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ห้องว่าง', bx, by + bh * 0.25);
    c.font = '700 ' + Math.round(f * 0.78) + 'px ' + FONT; c.fillStyle = '#2a2a30'; c.fillText('Room for rent', bx, by + bh * 0.53); c.fillText('รายเดือน · Monthly', bx, by + bh * 0.79); c.restore(); }
  var sz = signSize(c, P, u), z = nameSign(c, L.bx + L.wide / 2, Math.max(top + u * 0.02, G - L.fh * 1.0 - sz.h * 0.5), P, u, L.signCol, true);
  if ((S.seed >>> 4) % 3) L.inc = spiritHouse(c, L.side > 0 ? S.x1 - u * 0.95 : S.x0 + u * 0.95, G + u * 0.02, u * 0.85, S, S.seed);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: L.bx - u * 0.4, x1: L.bx + L.wide + u * 0.4, y0: top - u * 0.3, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
function apLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, F = L.folk, i;
  roomLights(S, L); tvGlow(S, L); riverGlints(S); incense(c, L.inc, t, 6);
  if (S.night) L.tubes.forEach(function (b, k) { var fl = k === 2 && Math.sin(t / 90) > 0.6 ? 0.3 : 1; glow(c, b.x + b.w / 2, b.y + 2, b.w * 0.9, '220,240,255', 0.35 * fl); fr(c, b.x, b.y, b.w, 2.5, 'rgba(240,250,255,' + (0.95 * fl).toFixed(2) + ')'); });
  /* someone along the walkway, up on the second floor */
  var fy = G - L.fh * 2, wd = F[0]; if (L.storeys > 2) { var me = walker(S, wd, L.bx + L.bw * 0.1, L.bx + L.bw * 0.9, 0.35, 0.2, fy + L.fh * 0.98, L.fh * 0.95, 'bag', '#f2f2f2'); }
  /* a scooter coming home along the road, θ = x / r for its wheels */
  var span = S.span + u * 3, sx = S.x0 - u * 1.5 + frac(t / 11000 + (S.seed % 9) / 9) * span, dir = L.side; if (dir < 0) sx = S.x1 + S.x0 - sx;
  var rd = F[1]; rd.dir = dir; rd.skirt = 0; var rme = K.person(c, sx - dir * u * 0.08, G + u * 0.5, u * 0.88, { lean: 0.1, seat: 0.62, legs: [1.2, -1.3, 1.1, -1.2], arms: [1.3, 0.3, 1.2, 0.3] }, rd);
  vehicle(c, 'scooter', sx, G + u * 0.52, u * 0.88, dir, nt(S, '#d9342b', 0.3), S.night, sx / (u * 0.12));
  c.fillStyle = nt(S, '#f2f2f2', 0.3); c.beginPath(); c.arc(rme.head[0], rme.head[1] - u * 0.01, u * 0.1, Math.PI, TAU); c.fill();
  if (!S.night) { var sit = F[2]; sit.dir = -L.side; K.person(c, L.side > 0 ? L.bx + L.wide - u * 0.35 : L.bx + u * 0.35, G + u * 0.04, u * 0.82, SIT, sit); }
  cat(c, L.side > 0 ? L.bx + L.bw * 0.5 : L.bx + L.wide - L.bw * 0.5, G + u * 0.06, u * 0.5, nt(S, '#e8a050', 0.3), t);
}
function apartment(S) {
  var L = look(S, 'apartment', apDeal), u = S.hh; L.st = stateOf(S);
  var key = ['apartment', S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0, L.st].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { return apStill(q, S, L); });
  apLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}

/* ---------------------------------------------------------------- dorm
   a student dorm by the university: rows of small rooms each with its towel on the rail,
   the gate, bicycles, a noodle cart out front with its pot steaming; students in uniform
   (white shirt, dark skirt or trousers) with their bags. A name with หญิง or ชาย says who lives there. */
function dmDeal(S, R, L) {
  var u = S.hh, sp = S.span, P = S.place || {}, n = nameOf(P);
  L.who = /หญิง|women|female|girl|lady|ladies/.test(n) ? 'f' : /ชาย|\bmen\b|\bmale\b|\bboys?\b/.test(n) ? 'm' : '';
  L.side = R() < 0.5 ? 1 : -1; var side = L.side;
  L.storeys = 4 + Math.floor(R() * 3); L.fh = (u * 2.05) / L.storeys; L.bw = u * (2.5 + R() * 0.6);
  L.bx = side > 0 ? S.x0 + sp * 0.1 : S.x1 - sp * 0.1 - L.bw;
  L.wall = pick(R, ['#f2ede0', '#e8d2c0', '#d9e2dc', '#f5e6b8', '#cfe0e8', '#f0d8c8', '#e2d6ea']); L.acc = pick(R, ['#7a3a5a', '#2c3e6b', '#2f6b5a', '#a8432f', '#c08a3a', '#5a4a8a']);
  L.cart = side > 0 ? L.bx + L.bw + u * 1.15 : L.bx - u * 1.15; L.rack = L.cart + side * u * 1.25; L.signCol = pick(R, SIGNCOL);
  L.nb = clamp(Math.floor(((side > 0 ? S.x1 - u * 0.8 - L.rack : L.rack - S.x0 - u * 0.8)) / (u * 0.45)), 0, 4);
  L.stall = pick(R, ['#c0392b', '#2f6db5', '#e8a23a', '#2f8f5b']);
  L.folk = crew(S, 6, { casual: 1 }, 0xd1);
  L.folk.forEach(function (d, k) { var f = L.who ? L.who === 'f' : (k + (S.seed >>> 2)) % 2 === 0; d.uni = f ? 'f' : 'm'; d.garb = 'casual'; d.col = '#f4f4f0'; d.low = f ? '#f4f4f0' : '#1f2433'; d.long = !f && k % 3 === 0; d.hair = f ? pick(R, [1, 2, 3]) : pick(R, [0, 0, 4]); d.bag = pick(R, ['#2c3e6b', '#c0392b', '#2f6b5a', '#3a3a3a', '#e5567f', '#e8a23a']); });
  L.vendor = crew(S, 1, { sin: 1 }, 0xd2)[0];
  return L;
}
/* the uniform skirt, dark and pleated, from the hip to the knee */
function uniSkirt(c, me, h) { var hp = me.hip, k = [(me.foot[0][0] + me.foot[1][0]) / 2, hp[1] + h * 0.26]; fp(c, [[hp[0] - h * 0.075, hp[1] - h * 0.03], [hp[0] + h * 0.075, hp[1] - h * 0.03], [k[0] + h * 0.12, k[1]], [k[0] - h * 0.12, k[1]]], '#1f2433'); fr(c, hp[0] - h * 0.075, hp[1] - h * 0.04, h * 0.15, h * 0.02, '#3a3a3a'); }
function student(S, d, xa, xb, v, ph, y, h) {
  var me = walker(S, d, xa, xb, v, ph, y, h, 'pack', d.bag); if (!me) return;
  var c = S.c, a = Math.min(1, frac(S.t / (Math.abs(xb - xa) / (v * S.hh) * 1000) + ph) * 7, (1 - frac(S.t / (Math.abs(xb - xa) / (v * S.hh) * 1000) + ph)) * 7);
  c.save(); c.globalAlpha = a; if (d.uni === 'f') uniSkirt(c, me, h); else fr(c, me.hip[0] - h * 0.07, me.hip[1] - h * 0.04, h * 0.14, h * 0.025, '#2a2a2a'); c.restore();
}
function dmStill(c, S, L) {
  var R = rnd((S.seed ^ 0xd0d) >>> 0 || 5), u = S.hh, G = S.deck, P = S.place || {}, x = L.bx, w = L.bw, hits = [], i, k;
  street(c, S, 'road'); settingOn(c, S);
  L.wins = [];
  var top = G - L.storeys * L.fh, wall = nt(S, L.wall, 0.45), acc = nt(S, L.acc, 0.4);
  pr(c, x, top, w, G - top, wall, 1.6);
  var cols = Math.max(4, Math.floor(w / (u * 0.36))), pitch = w / cols;
  for (i = 0; i < L.storeys - 1; i++) { var fy = top + i * L.fh;
    for (k = 0; k < cols; k++) { var wx = x + k * pitch + pitch * 0.14, lit = R() < 0.6;
      pane(c, S, wx, fy + L.fh * 0.14, pitch * 0.72, L.fh * 0.5, lit, nt(S, '#f2ede0', 0.35), R() < 0.7 ? pick(R, CLOTHES) : null, k + i);
      if (!lit && R() < 0.25) L.wins.push({ x: wx, y: fy + L.fh * 0.14, w: pitch * 0.72, h: L.fh * 0.5, anim: true, per: 8 + R() * 14, ph: R() * TAU, b: 0.2 + R() * 0.5 });
      fr(c, wx - pitch * 0.04, fy + L.fh * 0.7, pitch * 0.8, Math.max(1.5, L.fh * 0.05), nt(S, '#5a6068', 0.4));
      if (R() < 0.55) fr(c, wx + pitch * (0.1 + R() * 0.4), fy + L.fh * 0.72, pitch * 0.22, L.fh * 0.22, nt(S, pick(R, ['#f2f2f2', '#e5567f', '#4d8fd1', '#f2c94c', '#7fe0a4']), 0.35)); }
    fr(c, x, fy + L.fh - 2, w, 2, acc); }
  /* the ground floor: the lobby, a notice board, the mailboxes */
  var gy = G - L.fh; fr(c, x, gy, w, 3, acc);
  fr(c, x + w * 0.38, gy + L.fh * 0.15, w * 0.24, L.fh * 0.85, S.night ? '#ffe2a8' : '#cfe6ee'); for (k = 0; k < 3; k++) fr(c, x + w * (0.38 + k * 0.12) - 1, gy + L.fh * 0.15, 2, L.fh * 0.85, nt(S, '#5a6068', 0.3));
  fr(c, x + w * 0.08, gy + L.fh * 0.2, w * 0.22, L.fh * 0.45, nt(S, '#c9a06a', 0.35)); for (k = 0; k < 6; k++) fr(c, x + w * (0.1 + (k % 3) * 0.065), gy + L.fh * (0.25 + Math.floor(k / 3) * 0.18), w * 0.05, L.fh * 0.13, pick(R, ['#fbf8f0', '#f7e08a', '#ffd1e8', '#cfe6ee']));
  for (k = 0; k < 8; k++) fr(c, x + w * (0.7 + (k % 4) * 0.06), gy + L.fh * (0.25 + Math.floor(k / 4) * 0.2), w * 0.05, L.fh * 0.16, nt(S, '#9aa0a8', 0.35));
  fr(c, x - u * 0.05, top - u * 0.06, w + u * 0.1, u * 0.06, acc);
  if (S.night) glow(c, x + w * 0.5, G - L.fh * 0.5, w * 0.3, '255,214,150', 0.45);
  /* the noodle cart: glass case, the pot, a stool */
  var cx = L.cart, cw = u * 0.95;
  [cx - cw * 0.42, cx + cw * 0.42].forEach(function (wx2) { fe(c, wx2, G + u * 0.04, u * 0.07, u * 0.07, '#2a2a2a'); });
  pr(c, cx - cw / 2, G - u * 0.42, cw, u * 0.38, nt(S, '#d8dde2', 0.35), 1);
  fr(c, cx - cw * 0.45, G - u * 0.72, cw * 0.55, u * 0.3, 'rgba(200,230,245,.65)'); fr(c, cx - cw * 0.45, G - u * 0.72, cw * 0.55, 2, '#9aa0a8');
  for (k = 0; k < 4; k++) fe(c, cx - cw * 0.38 + k * cw * 0.13, G - u * 0.5, cw * 0.05, u * 0.03, pick(R, ['#f2e6c9', '#e8c070', '#c0562a', '#5aa35a']));
  pr(c, cx + cw * 0.15, G - u * 0.66, cw * 0.3, u * 0.24, nt(S, '#b8bcc4', 0.3), 0.6);
  c.save(); c.fillStyle = nt(S, L.stall, 0.2); c.font = '800 ' + Math.round(Math.max(8, u * 0.12)) + 'px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ก๋วยเตี๋ยว', cx, G - u * 0.24, cw * 0.9); c.restore();
  paper(c, poly([[cx - cw * 0.65, G - u * 0.98], [cx + cw * 0.65, G - u * 0.98], [cx + cw * 0.55, G - u * 0.86], [cx - cw * 0.55, G - u * 0.86]]), nt(S, L.stall, 0.4), 1);
  ln(c, [[cx - cw * 0.5, G - u * 0.86], [cx - cw * 0.5, G - u * 0.42]], '#9aa0a8', 1.5); ln(c, [[cx + cw * 0.5, G - u * 0.86], [cx + cw * 0.5, G - u * 0.42]], '#9aa0a8', 1.5);
  var st = cx - L.side * cw * 0.95; fr(c, st - u * 0.1, G - u * 0.24, u * 0.2, u * 0.04, nt(S, '#d9342b', 0.35)); ln(c, [[st - u * 0.08, G - u * 0.2], [st - u * 0.1, G]], nt(S, '#d9342b', 0.35), 1.5); ln(c, [[st + u * 0.08, G - u * 0.2], [st + u * 0.1, G]], nt(S, '#d9342b', 0.35), 1.5);
  L.stool = st;
  for (i = 0; i < L.nb; i++) vehicle(c, 'bike', L.rack + L.side * i * u * 0.45, G + u * 0.1, u * 0.8, 1, nt(S, pick(R, ['#e8d9b8', '#7fa8c9', '#d9342b', '#2f8f5b', '#f2c94c', '#2c3e6b']), 0.4), false, R() * 6);
  var sz = signSize(c, P, u), z = nameSign(c, x + w / 2, gy - sz.h * 0.55, P, u, L.signCol, true);
  var px = L.side > 0 ? Math.max(x - u * 0.45, S.x0 + u * 0.75) : Math.min(x + w + u * 0.45, S.x1 - u * 0.75);
  if ((S.seed >>> 6) % 3) L.inc = spiritHouse(c, px, G + u * 0.02, u * 0.85, S, S.seed); else plantAt(c, 'frangipani', px, G, u, S, S.seed);
  roadPlate(c, S, L.side > 0 ? S.x1 - u * 0.35 : S.x0 + u * 0.35);
  hits.push({ k: 'place', x0: x, x1: x + w, y0: top - u * 0.2, y1: G });
  if (z) hits.push({ k: 'place', x0: z.x0, x1: z.x1, y0: z.y0, y1: z.y1 });
  return hits;
}
function dmLive(S, L) {
  var c = S.c, u = S.hh, G = S.deck, t = S.t, F = L.folk, cx = L.cart;
  roomLights(S, L); riverGlints(S); incense(c, L.inc, t, 7);
  /* the noodle seller ladling, the pot's steam, a student eating at the stool */
  var v = L.vendor, sw = Math.sin(t / 500); v.dir = -L.side; var vx = cx + L.side * u * 0.75;
  K.person(c, vx, G + u * 0.04, u * 0.86, { lean: 0.15, legs: [0.05, 0, -0.05, 0], arms: [1.4 + sw * 0.3, 0.6, 1.0, 0.8] }, v);
  steam(c, cx + L.side * u * 0.3, G - u * 0.68, u * 0.7, t, 4);
  var e = F[5], lift = Math.max(0, Math.sin(t / 800)); e.dir = L.side; var me = K.person(c, L.stool, G + u * 0.02, u * 0.86, { lean: 0.2, seat: 0.26, legs: [1.5, -1.5, 1.45, -1.5], arms: [1.0 + lift * 0.7, 0.8 + lift * 0.7, 0.8, 1.2] }, e);
  if (e.uni === 'f') uniSkirt(c, me, u * 0.86);
  fe(c, L.stool + L.side * u * 0.25, G - u * 0.42, u * 0.1, u * 0.05, '#f2f2f2');
  /* students to and from class, and one wheeling out on a bicycle */
  var away = L.side > 0 ? S.x1 + u * 0.3 : S.x0 - u * 0.3, door = L.bx + L.bw * 0.5;
  student(S, F[0], door, away, 0.6, 0.1, G + u * 0.14, u * 0.88);
  student(S, F[1], away, door, 0.5, 0.45, G + u * 0.2, u * 0.86);
  if (!S.night) student(S, F[2], door, away, 0.55, 0.75, G + u * 0.1, u * 0.9);
  var span = S.span + u * 3, bx = S.x0 - u * 1.5 + frac(t / 12000 + (S.seed % 5) / 5) * span, dir = -L.side; if (dir < 0) bx = S.x1 + S.x0 - bx;
  var rd = F[3]; rd.dir = dir; var pd = bx / (u * 0.2) * dir, rp = { lean: 0.3, seat: 0.62, legs: [1.1 + 0.5 * Math.sin(pd), -1.4 + 0.5 * Math.sin(pd), 1.1 - 0.5 * Math.sin(pd), -1.4 - 0.5 * Math.sin(pd)], arms: [1.25, 0.2, 1.15, 0.25] };
  var rme = K.person(c, bx - dir * u * 0.1, G + u * 0.5, u * 0.88, rp, rd); pack(c, rme, u * 0.88, dir, rd.bag);
  vehicle(c, 'bike', bx, G + u * 0.5, u * 0.85, dir, nt(S, '#7fa8c9', 0.3), S.night, pd);
}
function dorm(S) {
  var L = look(S, 'dorm', dmDeal), u = S.hh; L.st = stateOf(S);
  var key = ['dorm', S.W, S.H, S.x0, S.x1, S.deck, u, S.seed, S.night ? 1 : 0].join(',');
  var hits = layer(S, key, [S.x0 - 6, S.deck - u * 2.75, S.span + 12, S.H - S.deck + u * 2.75], function (q) { return dmStill(q, S, L); });
  dmLive(S, L);
  (hits || []).forEach(function (h) { S.hits.push(h); });
}
/* the scenes, by name (doodles_layer.PORTRAIT maps a place to one) */
D.addScene('hotel', hotel, null, 'θ = θ₀·cos(√(g/L)·t) (the lanterns)<br>rooms lit on sin(2πt/T + φ) > b');
D.addScene('condo', condo, null, 'θ = −(π/2)·ease(t) (the barrier)<br>rooms lit on sin(2πt/T + φ) > b');
D.addScene('moobaan', moobaan, null, 'y = v₀t − ½gt² (the fountain)');
D.addScene('agent', agent, null, 'θ = θ₀·sin ωt (the keys)');
D.addScene('apartment', apartment, null, 'θ = x / r (the scooter wheels)<br>rooms lit on sin(2πt/T + φ) > b');
D.addScene('dorm', dorm, null, 'x = x₀ + A·sin(ky − ωt) (the noodle steam)');
D.addScene('hostel', hostel, null, 'y = y₀ − 4h·u(1 − u) (the dealt card)<br>θ = x / r (the wheels)');
D.addScene('guesthouse', guesthouse, null, 'θ = θ₀·sin ωt (the washing)<br>y = |sin ωt| (the broom)');
})();
