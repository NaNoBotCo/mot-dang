/* The auto-doodler (Nan, 2026-10-02: "an auto-doodler for the motdang header … a
   new doodle every day"). Any calendar event becomes a paper-cut scene on the
   band's stage, over the north's landscape and sights (skyline.js, MDSKY). The
   event's words pick the scene; the date seeds its colours, crowd and props, so a
   scene drawn twice on two days is two drawings. latin-night keeps its own scene.

   MDDOODLER.setOf(e)                      → the scene an event gets ('run', 'band' …)
   MDDOODLER.pick(cands, day, prev)        → the day's event: sets rotate by date
   MDDOODLER.scene(c, W, H, t, o)          → hit boxes; o.set, o.seed, o.x0, o.x1,
                                             o.deck, o.phone, o.night, o.label
   MDDOODLER.full(c, W, H, t, o)           the whole picture with sky and land, for a still
   MDDOODLER.math(set, seed)               the line of math under the drawing */
(function () {
'use strict';
var SKY = window.MDSKY; if (!SKY || window.MDDOODLER) return;   /* once a page, however many pictures load it */
var paper = SKY.paper, jag = SKY.jag, circ = SKY.circ, TAU = 6.2832;
function rnd(seed) { return function () { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }; }
function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
function poly(pts) { return function (q) { q.beginPath(); pts.forEach(function (p, i) { i ? q.lineTo(p[0], p[1]) : q.moveTo(p[0], p[1]); }); q.closePath(); }; }
function rect(x, y, w, h) { return poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]); }
function lerp(a, b, u) { return a + (b - a) * u; }
function ease(u) { return 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, u))); }

/* ---------------------------------------------------------------- who goes where
   Words first (the calendar's kinds are loose: a running club filed under music),
   then the kind. */
var WORDS = [
  ['latin', /latin|salsa|bachata|kizomba|zouk|merengue|cumbia|reggaeton|tango|milonga|ละติน|ซัลซ่า|บาชาต้า|แทงโก้/i],
  ['run', /\brun|running|marathon|jog|hike|hiking|trail|walk\b|walking|parkrun|cycl|bike|วิ่ง|เดินป่า|ปั่น/i],
  ['calm', /meditat|mindful|breath|sound bath|chant|prayer|worship|church|mass\b|sangha|dhamma|ธรรม|สมาธิ|สวดมนต์|ทำบุญ/i],
  ['yoga', /yoga|pilates|tai ?chi|qi ?gong|stretch|mobility|โยคะ|ไทชิ/i],
  ['ball', /padel|tennis|pickle|badminton|football|futsal|soccer|rugby|volley|basket|frisbee|squash|golf|ping ?pong|cricket|ฟุตบอล|แบด|เทนนิส/i],
  ['dance', /aerobic|zumba|hiit|circuit|boot ?camp|fitness|swing dance|line danc|ballroom|dance|danc|แอโรบิก|เต้น/i],
  ['band', /band|song|singing|live music|jazz|blues|concert|open mic|acoustic|gig|choir|orchestra|recital|rock|folk|karaoke|\bdj\b|ดนตรี|คอนเสิร์ต/i],
  ['film', /film|movie|cinema|screening|documentar|หนัง|ภาพยนตร์/i],
  ['market', /market|bazaar|fair|flea|vintage|craft sale|pop-?up|kad\b|กาด|ตลาด|ถนนคนเดิน/i],
  ['studio', /pottery|ceramic|paint|drawing|sketch|art\b|exhibit|gallery|craft|weav|photo|batik|calligraph|ปั้น|วาด|ศิลป/i],
  ['feast', /brunch|lunch|dinner|dim sum|buffet|bbq|barbecue|food|cook|tasting|wine|beer|coffee|tea\b|supper|feast|kitchen|อาหาร|ทำอาหาร|กาแฟ/i],
  ['learn', /talk|lecture|class|course|workshop|lesson|language|thai for|write|writers|book|read|club|geeks|quiz|chess|bridge|seminar|meetup|toastmaster|เรียน|สัมมนา|อบรม/i]
];
var BYCAT = { music: 'band', dance: 'dance', wellness: 'yoga', sport: 'ball', art: 'studio', learn: 'learn', food: 'feast', market: 'market', social: 'social', faith: 'calm', family: 'social', other: 'social' };
function setOf(e) {
  if (e.dd === 'latin-night') return 'latin';
  var t = (e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 160);
  var s = '';
  for (var i = 0; i < WORDS.length && !s; i++) if (WORDS[i][1].test(t)) s = WORDS[i][0];
  s = s || BYCAT[e.c] || 'social';
  return s === 'feast' && SCENES.food ? 'food' : s;   /* doodler-food.js draws the table by cuisine */
}
var ORDER = ['band', 'market', 'yoga', 'feast', 'run', 'learn', 'latin', 'studio', 'ball', 'social', 'dance', 'film', 'calm'];
/* the day's event: among the ones we know most about, the scene the date's turn
   comes to first; yesterday's scene steps aside when another will do (prev: yesterday's
   candidates), so the band does not draw the same thing two days running */
var NEAR = [];   /* [set, test(e)]: extra groupings by place (doodler-moat.js adds the moat) */
/* A doodle is a scene and its variant (a cuisine, a gate). It airs once per version (Nan,
   2026-10-02: reused "only after significant editing to make it more baller than last time"):
   VERSIONS holds each one's current version, raised by the edit that tops it; aired maps
   'set' or 'set:variant' to the highest version already shown (front/doodle.json). */
var VERSIONS = { 'learn': 2, 'run': 2 }, VARIANTS = {}; // learn v2: hanging lanterns, lai kham blackboard, raising hands, notebooks, fireflies; run v2: water station, cheering spectator, tung banners, lanterns, khom loi, sweat
function version(set, variant) { return VERSIONS[set + ':' + variant] || VERSIONS[set] || 1; }
function variantOf(set, e) { return VARIANTS[set] ? VARIANTS[set](e) || '' : ''; }
function fresh(set, e, aired) { if (!aired) return true; var v = variantOf(set, e), a = aired[v ? set + ':' + v : set] || 0; return version(set, v) > a; }
/* the reader's own choice among the day's doodles (Nan, 2026-10-02: "match the best graphic with the
   customer … by best, I mean be genuinely useful"): first what they can still go to — ahead today and
   soon, or on now — and how near it is to them; then what they open and keep (me.cats, me.venues,
   me.saved, kept in their browser); last, a doodle this browser has already shown them steps back.
   opts: rows {k, set, variant, version}; ev: key → event; here: {lat, lng, how}; seen: {doodle: 1}. */
function forReader(opts, ev, me, here, now, seen) {
  var best = null, bs = -1e9;
  opts.forEach(function (o, i) {
    var e = ev[o.k]; if (!e) return;
    var key = o.set + (o.variant ? ':' + o.variant : '') + '@' + (o.version || 1), sc = -i * 0.3;
    var s0 = Date.parse(String(e.s).replace(' ', 'T') + '+07:00'), e0 = e.e ? Date.parse((e.e.length > 10 ? e.e : e.e + ' 23:59:59').replace(' ', 'T') + '+07:00') : s0 + 2 * 3600e3;
    if (e0 < now) sc -= 8;                                   /* over: nothing to go to */
    else if (s0 <= now) sc += 3;                             /* on now */
    else sc += 4 - Math.min(3, (s0 - now) / 3600e3 / 2);     /* ahead today, sooner first */
    if (here && e.la != null) { var dy = (e.la - here.lat) * 111, dx = (e.lo - here.lng) * 111 * Math.cos(here.lat * Math.PI / 180), km = Math.sqrt(dx * dx + dy * dy);
      sc += (here.how === 'gps' ? 3 : 1.5) * Math.max(0, 1 - km / 12); }
    if (me) sc += Math.min(2, (me.cats && me.cats[e.c] || 0) * 0.4) + (me.venues && e.v && me.venues[e.v] ? 1.5 : 0) + (me.saved && me.saved[e.k] ? 3 : 0);
    if (seen && seen[key]) sc -= 1.5;
    if (sc > bs) { bs = sc; best = o; }
  });
  return best;
}
function pick(cands, day, prev, aired) { var x = choose(cands, day, prev, aired); return x ? x.e : null; }
function choose(cands, day, prev, aired, skip) {
  if (!cands.length) return null;
  function info(e) { return (e.have || []).length + (e.la != null ? 1 : 0); }
  var best = Math.max.apply(null, cands.map(info)), pool = cands.filter(function (e) { return info(e) >= best - 1; });
  var n = Math.floor(Date.parse(day + 'T12:00:00+07:00') / 864e5), by = {};
  function put(s, e) { if (fresh(s, e, aired)) (by[s] = by[s] || []).push(e); }
  pool.forEach(function (e) { var s = setOf(e); put(s, e); NEAR.forEach(function (n) { if (n[0] !== s && n[1](e)) put(n[0], e); }); });
  Object.keys(skip || {}).forEach(function (s) { delete by[s]; });   /* the day's other choices */
  if (!Object.keys(by).length) return null;   /* every doodle today has aired at its version: the band waits for a new one */
  var y = prev && prev.set ? prev : prev && prev.length ? choose(prev, new Date(Date.parse(day + 'T12:00:00+07:00') - 864e5).toISOString().slice(0, 10), null, aired) : null;
  if (y && by[y.set] && Object.keys(by).length > 1) delete by[y.set];
  for (var i = 0; i < ORDER.length; i++) {
    var s = ORDER[(n * 5 + i) % ORDER.length];
    if (by[s]) { var e = by[s].sort(function (a, b) { return info(b) - info(a) || hash(day + a.k) - hash(day + b.k); })[0], v = variantOf(s, e); return { e: e, set: s, variant: v, version: version(s, v) }; }
  }
  var s0 = Object.keys(by)[0], e0 = by[s0][0], v0 = variantOf(s0, e0);
  return { e: e0, set: s0, variant: v0, version: version(s0, v0) };
}

/* ---------------------------------------------------------------- people, cut from paper
   P: lean (torso from upright, + = forward); legs [thigh, knee, thigh, knee] and arms
   [upper, elbow, upper, elbow] — angles from hanging straight down, + = forward;
   the knee and elbow add to the limb above them. seat: hip height (0.47 standing). */
var POSE = {
  stand: { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [0.12, 0.1, -0.1, 0.05] },
  up: { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [2.85, 0, 3.4, 0] },
  tree: { lean: 0, legs: [0, 0, 0.95, -2.3], arms: [3.08, 0, 3.2, 0] },
  warrior: { lean: 0, seat: 0.4, legs: [0.95, -0.95, -0.75, 0], arms: [1.57, 0, -1.57, 0] },
  fold: { lean: 2.3, legs: [0.05, 0, -0.05, 0], arms: [2.3, 0, 2.4, 0] },
  sit: { lean: 0, seat: 0.24, legs: [1.5, -1.5, 1.5, -1.5], arms: [0.3, 0.6, 0.2, 0.7] },
  lotus: { lean: 0, seat: 0.1, legs: [1.45, -2.9, 1.45, -2.9], arms: [0.5, 0.5, 0.45, 0.55] },
  wai: { lean: 0.05, seat: 0.1, legs: [1.45, -2.9, 1.45, -2.9], arms: [0.9, 1.6, 0.8, 1.7] }
};
function mix(A, B, u) {
  var o = { lean: lerp(A.lean || 0, B.lean || 0, u), seat: lerp(A.seat || 0.47, B.seat || 0.47, u), legs: [], arms: [] };
  for (var i = 0; i < 4; i++) { o.legs.push(lerp(A.legs[i], B.legs[i], u)); o.arms.push(lerp(A.arms[i], B.arms[i], u)); }
  return o;
}
function walkP(p, run) {
  var s = Math.sin(p), k = run ? 1 : 0.5;
  return { lean: run ? 0.22 : 0.04, seat: 0.47, lift: run ? Math.abs(Math.cos(p)) * 0.05 : 0,
    legs: [s * 0.5 * (run ? 1.4 : 1), -k * (0.4 + 0.6 * Math.max(0, -Math.cos(p))), -s * 0.5 * (run ? 1.4 : 1), -k * (0.4 + 0.6 * Math.max(0, Math.cos(p)))],
    arms: [-s * (run ? 0.9 : 0.4), run ? 1.5 : 0.3, s * (run ? 0.9 : 0.4), run ? 1.5 : 0.3] };
}
var HAIR = ['none', 'tail', 'bun', 'bob', 'cap'];
function person(c, x, y, h, P, d) {
  if (d.garb) return dressed(c, x, y, h, P, d);
  var dir = d.dir || 1, seat = P.seat || 0.47, lean = P.lean || 0;
  function pt(o, a, l) { return [o[0] + dir * Math.sin(a) * l, o[1] + Math.cos(a) * l]; }
  var hip = [x, y - h * seat - (P.lift || 0) * h];
  var sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33];
  var hd = [sh[0] + dir * Math.sin(lean) * h * 0.14, sh[1] - Math.cos(lean) * h * 0.14];
  var L = P.legs, A = P.arms, k1 = pt(hip, L[0], h * 0.24), f1 = pt(k1, L[0] + L[1], h * 0.23), k2 = pt(hip, L[2], h * 0.24), f2 = pt(k2, L[2] + L[3], h * 0.23);
  var e1 = pt(sh, A[0], h * 0.17), w1 = pt(e1, A[0] + A[1], h * 0.16), e2 = pt(sh, A[2], h * 0.17), w2 = pt(e2, A[2] + A[3], h * 0.16);
  c.save(); c.shadowColor = 'rgba(0,0,0,.45)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2;
  c.strokeStyle = d.col; c.fillStyle = d.col; c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = Math.max(2, h * 0.075);
  c.beginPath();
  c.moveTo(f2[0], f2[1]); c.lineTo(k2[0], k2[1]); c.lineTo(hip[0], hip[1]); c.lineTo(k1[0], k1[1]); c.lineTo(f1[0], f1[1]);
  c.moveTo(hip[0], hip[1]); c.lineTo(sh[0], sh[1]);
  c.moveTo(w2[0], w2[1]); c.lineTo(e2[0], e2[1]); c.lineTo(sh[0], sh[1]); c.lineTo(e1[0], e1[1]); c.lineTo(w1[0], w1[1]);
  c.stroke();
  if (d.skirt) { var sw = h * 0.17; c.beginPath(); c.moveTo(sh[0] * 0.25 + hip[0] * 0.75 + 0, sh[1] * 0.4 + hip[1] * 0.6); c.lineTo(hip[0] - sw, hip[1] + h * 0.17); c.lineTo(hip[0] + sw, hip[1] + h * 0.17); c.closePath(); c.fill(); }
  c.beginPath(); c.arc(hd[0], hd[1], h * 0.105, 0, TAU); c.fill();
  var hr = HAIR[d.hair || 0];
  if (hr === 'tail') { c.beginPath(); c.ellipse(hd[0] - dir * h * 0.12, hd[1] + h * 0.03, h * 0.045, h * 0.11, -dir * 0.5, 0, TAU); c.fill(); }
  if (hr === 'bun') { c.beginPath(); c.arc(hd[0] - dir * h * 0.04, hd[1] - h * 0.12, h * 0.06, 0, TAU); c.fill(); }
  if (hr === 'bob') { c.beginPath(); c.arc(hd[0] - dir * h * 0.02, hd[1] - h * 0.01, h * 0.13, Math.PI * 0.95, Math.PI * 2.05); c.lineTo(hd[0] + h * 0.12, hd[1] + h * 0.07); c.lineTo(hd[0] - h * 0.13, hd[1] + h * 0.07); c.fill(); }
  if (hr === 'cap') { c.beginPath(); c.arc(hd[0], hd[1] - h * 0.02, h * 0.11, Math.PI, TAU); c.lineTo(hd[0] + dir * h * 0.2, hd[1] - h * 0.02); c.fill(); }
  c.restore();
  return { hip: hip, sh: sh, head: hd, hand: [w1, w2], foot: [f1, f2] };
}
/* the skeleton's joints, for the dressed figure */
function joints(x, y, h, P, dir) {
  var seat = P.seat || 0.47, lean = P.lean || 0;
  function pt(o, a, l) { return [o[0] + dir * Math.sin(a) * l, o[1] + Math.cos(a) * l]; }
  var hip = [x, y - h * seat - (P.lift || 0) * h], sh = [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33];
  var hd = [sh[0] + dir * Math.sin(lean) * h * 0.14, sh[1] - Math.cos(lean) * h * 0.14], L = P.legs, A = P.arms;
  var k1 = pt(hip, L[0], h * 0.24), k2 = pt(hip, L[2], h * 0.24), e1 = pt(sh, A[0], h * 0.17), e2 = pt(sh, A[2], h * 0.17);
  return { hip: hip, sh: sh, head: hd, k1: k1, f1: pt(k1, L[0] + L[1], h * 0.23), k2: k2, f2: pt(k2, L[2] + L[3], h * 0.23),
    e1: e1, w1: pt(e1, A[0] + A[1], h * 0.16), e2: e2, w2: pt(e2, A[2] + A[3], h * 0.16), lean: lean };
}
function limb(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke(); }
/* clothes of the north: pha sin (the tube skirt) with its tin jok hem, mo hom (the indigo
   shirt) with a pha khao ma sash, everyday wear, and Akha dress with its headdress */
function dressed(c, x, y, h, P, d) {
  var dir = d.dir || 1, J = joints(x, y, h, P, dir), w = Math.max(2, h * 0.075), skin = d.skin || '#d9a27a', g = d.garb;
  var top = d.col, low = d.low || '#2c2f45', bare = g === 'sin' || g === 'akha' && !d.man;
  c.save(); c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 3; c.shadowOffsetX = 1.5; c.shadowOffsetY = 2; c.lineCap = 'round'; c.lineJoin = 'round';
  /* legs: the far one first */
  limb(c, [J.hip, J.k2, J.f2], bare ? skin : low, w * 1.05); limb(c, [J.hip, J.k1, J.f1], bare ? skin : low, w * 1.05);
  if (g === 'akha' && !d.man) {
    [[J.k1, J.f1], [J.k2, J.f2]].forEach(function (p) { limb(c, [[lerp(p[0][0], p[1][0], 0.15), lerp(p[0][1], p[1][1], 0.15)], [lerp(p[0][0], p[1][0], 0.85), lerp(p[0][1], p[1][1], 0.85)]], '#1d1b2a', w * 1.25);
      limb(c, [[lerp(p[0][0], p[1][0], 0.3), lerp(p[0][1], p[1][1], 0.3)], [lerp(p[0][0], p[1][0], 0.36), lerp(p[0][1], p[1][1], 0.36)]], '#d9342b', w * 0.95); });
  }
  c.shadowColor = 'transparent';
  [J.f1, J.f2].forEach(function (f) { c.fillStyle = '#2a1a12'; c.beginPath(); c.ellipse(f[0] + dir * h * 0.03, f[1], h * 0.05, h * 0.022, 0, 0, TAU); c.fill(); });
  c.shadowColor = 'rgba(0,0,0,.4)';
  /* skirts */
  if (g === 'sin' || g === 'akha' && !d.man) {
    var len = g === 'sin' ? 0.86 : 0.42, kx = (J.f1[0] + J.f2[0]) / 2, fy = Math.max(J.f1[1], J.f2[1]), spread = Math.abs(J.f1[0] - J.f2[0]) * 0.55 + h * 0.07;
    var by = lerp(J.hip[1], fy, len), bx = lerp(J.hip[0], kx, len);
    c.fillStyle = low; c.beginPath(); c.moveTo(J.hip[0] - h * 0.075, J.hip[1] - h * 0.04); c.lineTo(J.hip[0] + h * 0.075, J.hip[1] - h * 0.04); c.lineTo(bx + spread, by); c.lineTo(bx - spread, by); c.closePath(); c.fill();
    c.shadowColor = 'transparent';
    if (g === 'sin') {   /* the tin jok: a woven hem band, zigzag */
      var hb = h * 0.07; c.fillStyle = d.hem || '#e8b84a'; c.fillRect(bx - spread, by - hb, spread * 2, hb);
      c.strokeStyle = '#7a1f1a'; c.lineWidth = 1; c.beginPath(); for (var zx = bx - spread, zi = 0; zx <= bx + spread; zx += hb * 0.6, zi++) c.lineTo(zx, by - (zi % 2 ? hb * 0.85 : hb * 0.15)); c.stroke();
    } else { c.fillStyle = '#e8e2d0'; for (var q = 0; q < 4; q++) c.fillRect(bx - spread + q * spread * 0.55, by - 2, spread * 0.3, 2); }
    c.shadowColor = 'rgba(0,0,0,.4)';
  }
  /* the torso */
  var ux = Math.cos(J.lean) * dir, uy = Math.sin(J.lean) * dir, wsh = h * 0.085, wh = h * 0.07;
  c.fillStyle = top; c.beginPath();
  c.moveTo(J.sh[0] - ux * wsh, J.sh[1] - uy * wsh); c.lineTo(J.sh[0] + ux * wsh, J.sh[1] + uy * wsh);
  c.lineTo(J.hip[0] + ux * wh + uy * h * 0.02, J.hip[1] + uy * wh + h * 0.02); c.lineTo(J.hip[0] - ux * wh, J.hip[1] - uy * wh + h * 0.02); c.closePath(); c.fill();
  c.shadowColor = 'transparent';
  if (g === 'mohom') {   /* the pha khao ma, checked, tied at the waist */
    var sy = J.hip[1] - h * 0.02, sw2 = wh * 1.15; for (var k = 0; k < 6; k++) { c.fillStyle = k % 2 ? '#f2e6c9' : '#c0392b'; c.fillRect(J.hip[0] - sw2 + k * sw2 / 3, sy - h * 0.03, sw2 / 3, h * 0.03); }
    c.fillStyle = '#c0392b'; c.beginPath(); c.moveTo(J.hip[0] - dir * sw2, sy); c.lineTo(J.hip[0] - dir * sw2 * 1.4, sy + h * 0.12); c.lineTo(J.hip[0] - dir * sw2 * 0.8, sy + h * 0.1); c.fill();
  }
  if (g === 'sin') { c.fillStyle = d.sabai || '#e8b84a'; c.beginPath(); c.moveTo(J.sh[0] - ux * wsh, J.sh[1] - uy * wsh); c.lineTo(J.sh[0] + ux * wsh * 0.4, J.sh[1]); c.lineTo(J.hip[0] + ux * wh, J.hip[1] - h * 0.06); c.lineTo(J.hip[0] + ux * wh * 0.4, J.hip[1] - h * 0.02); c.closePath(); c.fill(); }
  if (g === 'akha') {    /* red and white trim down the jacket's front; appliqué bands across its foot */
    c.strokeStyle = '#d9342b'; c.lineWidth = Math.max(1, h * 0.014); c.beginPath(); c.moveTo(J.sh[0] + ux * wsh * 0.3, J.sh[1]); c.lineTo(J.hip[0] + ux * wh * 0.5, J.hip[1]); c.stroke();
    c.strokeStyle = '#f2f2f2'; c.beginPath(); c.moveTo(J.sh[0] + ux * wsh * 0.5, J.sh[1]); c.lineTo(J.hip[0] + ux * wh * 0.7, J.hip[1]); c.stroke();
    ['#d9342b', '#f2e6c9', '#e8b84a', '#2f8f5b'].forEach(function (col, i) { c.fillStyle = col; c.fillRect(J.hip[0] - wh, J.hip[1] - h * (0.03 + i * 0.022), wh * 2, h * 0.016); });
  }
  c.shadowColor = 'rgba(0,0,0,.4)';
  /* arms: sleeves, then hands */
  var sleeve = g === 'casual' && !d.long ? 0.45 : 1;
  [[J.e2, J.w2], [J.e1, J.w1]].forEach(function (a) {
    var mid = [lerp(a[0][0], a[1][0], sleeve === 1 ? 0.85 : 0), lerp(a[0][1], a[1][1], sleeve === 1 ? 0.85 : 0)];
    limb(c, [J.sh, a[0]], top, w); if (sleeve === 1) limb(c, [a[0], mid], top, w); limb(c, [sleeve === 1 ? mid : a[0], a[1]], skin, w * 0.85);
    if (g === 'akha') { limb(c, [[lerp(a[0][0], a[1][0], 0.4), lerp(a[0][1], a[1][1], 0.4)], [lerp(a[0][0], a[1][0], 0.55), lerp(a[0][1], a[1][1], 0.55)]], '#d9342b', w * 1.15);
      limb(c, [[lerp(a[0][0], a[1][0], 0.62), lerp(a[0][1], a[1][1], 0.62)], [lerp(a[0][0], a[1][0], 0.72), lerp(a[0][1], a[1][1], 0.72)]], '#3fb6b0', w * 1.05); }
  });
  /* head and hair */
  c.fillStyle = skin; c.beginPath(); c.arc(J.head[0], J.head[1], h * 0.1, 0, TAU); c.fill();
  c.shadowColor = 'transparent';
  var hd = J.head, hr = HAIR[d.hair || 0]; c.fillStyle = d.hairCol || '#1c1410';
  if (g === 'akha' && d.man) {   /* the wrapped black turban, a red tassel at the side */
    c.fillStyle = '#1a1826'; c.beginPath(); c.ellipse(hd[0], hd[1] - h * 0.07, h * 0.125, h * 0.085, 0, Math.PI, TAU); c.ellipse(hd[0], hd[1] - h * 0.05, h * 0.115, h * 0.04, 0, 0, TAU); c.fill();
    c.strokeStyle = 'rgba(255,255,255,.18)'; c.lineWidth = 1; for (var tw = 0; tw < 3; tw++) { c.beginPath(); c.ellipse(hd[0], hd[1] - h * (0.07 + tw * 0.025), h * 0.115, h * 0.03, 0, Math.PI * 1.05, Math.PI * 1.95); c.stroke(); }
    c.fillStyle = '#d9342b'; c.beginPath(); c.arc(hd[0] - dir * h * 0.12, hd[1] - h * 0.03, h * 0.03, 0, TAU); c.fill(); }
  else if (g === 'akha') akhaHat(c, hd, h, dir, d.t || 0, d.ulo, skin);
  else {
    c.beginPath(); c.arc(hd[0] - dir * h * 0.01, hd[1] - h * 0.015, h * 0.102, Math.PI * (dir > 0 ? 0.9 : 1.1) - (dir > 0 ? 0 : 0), Math.PI * 2.05); c.fill();
    if (hr === 'tail') { c.beginPath(); c.ellipse(hd[0] - dir * h * 0.12, hd[1] + h * 0.03, h * 0.04, h * 0.1, -dir * 0.5, 0, TAU); c.fill(); }
    if (hr === 'bun') { c.beginPath(); c.arc(hd[0] - dir * h * 0.06, hd[1] - h * 0.1, h * 0.055, 0, TAU); c.fill(); if (g === 'sin') { c.fillStyle = '#ffd84a'; c.beginPath(); c.arc(hd[0] - dir * h * 0.1, hd[1] - h * 0.12, h * 0.03, 0, TAU); c.fill(); } }
    if (hr === 'bob') { c.beginPath(); c.arc(hd[0] - dir * h * 0.02, hd[1] - h * 0.01, h * 0.125, Math.PI * 0.95, Math.PI * 2.05); c.lineTo(hd[0] + h * 0.12, hd[1] + h * 0.07); c.lineTo(hd[0] - h * 0.13, hd[1] + h * 0.07); c.fill(); }
    if (hr === 'cap' || g === 'mohom' && d.hat) { c.fillStyle = g === 'mohom' ? '#d9b36a' : top; c.beginPath(); c.arc(hd[0], hd[1] - h * 0.03, h * 0.11, Math.PI, TAU); c.lineTo(hd[0] + dir * h * 0.2, hd[1] - h * 0.03); c.fill(); }
  }
  /* an eye and a smile, small */
  c.fillStyle = '#2a1a12'; c.beginPath(); c.arc(hd[0] + dir * h * 0.045, hd[1] - h * 0.01, Math.max(0.8, h * 0.011), 0, TAU); c.fill();
  c.restore();
  return { hip: J.hip, sh: J.sh, head: J.head, hand: [J.w1, J.w2], foot: [J.f1, J.f2] };
}
/* the Akha headdress (Loimi), after the ones in Melodies and Motifs: a cap of silver studs
   edged in red and white beads, big silver balls and coin discs down each side, orange wool
   tassels, and loops of red, white and blue beads under the chin that swing as she moves,
   θ = 0.22·sin(2πt/1.4); ulo = the taller Ulo cone */
function akhaHat(c, hd, h, dir, t, ulo, skin) {
  var x = hd[0], y = hd[1], r = h * 0.11, sw = 0.22 * Math.sin(t / 1400 * TAU), i, k;
  c.fillStyle = '#1a1826';
  if (ulo) { c.beginPath(); c.moveTo(x - r * 1.2, y + r * 0.1); c.quadraticCurveTo(x - r * 0.6, y - r * 3.4, x - dir * r * 0.1, y - r * 3.7); c.quadraticCurveTo(x + r * 0.7, y - r * 3.3, x + r * 1.2, y + r * 0.1); c.closePath(); c.fill(); }
  else { c.beginPath(); c.moveTo(x - r * 1.25, y + r * 0.3); c.lineTo(x - r * 1.2, y - r * 1.2); c.quadraticCurveTo(x, y - r * 2.1, x + r * 1.2, y - r * 1.2); c.lineTo(x + r * 1.25, y + r * 0.3); c.closePath(); c.fill(); }
  /* studs, row on row */
  c.fillStyle = '#dfe2ea';
  var rows = ulo ? 6 : 4;
  for (var row = 0; row < rows; row++) { var ry = y - r * (0.75 + row * (ulo ? 0.45 : 0.3)), wdt = (ulo ? 1 - row * 0.13 : 1 - row * 0.12) * r * 1.05;
    for (k = -3; k <= 3; k++) { var sx = x + k * wdt / 3; c.beginPath(); c.arc(sx, ry, r * 0.13, 0, TAU); c.fill(); } }
  c.strokeStyle = '#d9342b'; c.lineWidth = Math.max(1, r * 0.12); c.beginPath(); c.arc(x, y - r * 0.2, r * 1.0, Math.PI * 1.08, Math.PI * 1.92); c.stroke();
  c.strokeStyle = '#f2f2f2'; c.lineWidth = Math.max(0.8, r * 0.08); c.beginPath(); c.arc(x, y - r * 0.2, r * 0.86, Math.PI * 1.1, Math.PI * 1.9); c.stroke();
  /* the face, framed by the cap */
  c.fillStyle = skin || '#d9a27a'; c.beginPath(); c.ellipse(x + dir * r * 0.08, y + r * 0.12, r * 0.66, r * 0.74, 0, 0, TAU); c.fill();
  c.fillStyle = '#1c1410'; c.beginPath(); c.ellipse(x + dir * r * 0.08, y - r * 0.5, r * 0.62, r * 0.16, 0, 0, TAU); c.fill();
  /* silver balls and coins down both sides */
  [-1, 1].forEach(function (sd) {
    for (i = 0; i < 3; i++) { var bx = x + sd * r * (1.12 - i * 0.04), by = y - r * (0.75 - i * 0.55), g = c.createRadialGradient(bx - r * 0.08, by - r * 0.08, 0, bx, by, r * 0.27);
      g.addColorStop(0, '#ffffff'); g.addColorStop(1, '#9aa0ac'); c.fillStyle = g; c.beginPath(); c.arc(bx, by, r * 0.26, 0, TAU); c.fill(); }
    c.fillStyle = '#c9ccd4'; c.beginPath(); c.ellipse(x + sd * r * 0.8, y + r * 0.35, r * 0.18, r * 0.24, 0, 0, TAU); c.fill();
    /* the wool tassel */
    c.strokeStyle = '#f08a3a'; c.lineWidth = Math.max(1, r * 0.08);
    for (k = 0; k < 4; k++) { c.beginPath(); c.moveTo(x + sd * r * 1.3, y - r * 1.2); c.lineTo(x + sd * r * (1.45 + k * 0.08) + Math.sin(sw + k) * r * 0.1, y - r * (0.3 - k * 0.05)); c.stroke(); }
  });
  /* bead loops under the chin, each a hanging arc that swings */
  ['#d9342b', '#f2f2f2', '#2f55c9', '#f2f2f2'].forEach(function (col, j) {
    var dep = r * (0.35 + j * 0.16), off = Math.sin(sw) * dep * 0.6;
    c.fillStyle = col;
    for (var b = 0; b <= 12; b++) { var u = b / 12, bx2 = lerp(x - r * 1.05, x + r * 1.05, u) + off * Math.sin(u * Math.PI), by2 = y + r * 0.95 + Math.sin(u * Math.PI) * dep;
      c.beginPath(); c.arc(bx2, by2, r * 0.075, 0, TAU); c.fill(); }
  });
}
var SKIN = ['#f1c9a5', '#e3b08a', '#d29a6e', '#b97f52', '#9a6440', '#7a4a2e'];
var LOW = ['#2c2f45', '#3a2a22', '#1f3a5a', '#5a4a3a', '#2a2a2a', '#4a3a5a'];
/* a crowd dressed for the north: mix = shares of pha sin, mo hom and everyday wear */
var MIXES = { run: { casual: 0.85, mohom: 0.15 }, yoga: { casual: 1 }, ball: { casual: 1 }, dance: { casual: 0.7, sin: 0.3 },
  band: { casual: 0.6, sin: 0.2, mohom: 0.2 }, calm: { sin: 0.45, mohom: 0.35, casual: 0.2 }, akha: { akha: 1 } };
function town(S, n, mix) {
  var r = S.r; mix = mix || MIXES[S.set] || { sin: 0.35, mohom: 0.25, casual: 0.4 };
  var out = folk(r, n), keys = Object.keys(mix);
  out.forEach(function (d) {
    var u = r(), acc = 0, g = keys[keys.length - 1];
    for (var i = 0; i < keys.length; i++) { acc += mix[keys[i]]; if (u < acc) { g = keys[i]; break; } }
    d.garb = g; d.skin = SKIN[Math.floor(r() * SKIN.length)]; d.low = LOW[Math.floor(r() * LOW.length)]; d.hat = r() < 0.4;
    if (g === 'sin') { d.low = ['#7a1f3a', '#2a3a6a', '#5a2a6a', '#1f5a4a', '#8a3a1a'][Math.floor(r() * 5)]; d.hem = ['#e8b84a', '#d9342b', '#f2e6c9'][Math.floor(r() * 3)]; d.hair = 2; d.sabai = CLOTH[Math.floor(r() * CLOTH.length)]; }
    if (g === 'mohom') { d.col = '#2c3e6b'; d.low = '#24335a'; }
    if (g === 'akha') { d.col = '#1d1b2a'; d.low = '#1d1b2a'; d.ulo = r() < 0.25; d.man = r() < 0.3; }
    d.hairCol = r() < 0.15 ? '#9a9a9a' : r() < 0.1 ? '#8a5a2a' : '#1c1410'; d.t = S.t;
  });
  return out;
}
/* a crowd: colours, hair and skirts dealt from the day's seed */
var CLOTH = ['#ffc266', '#ff5a8c', '#b692ff', '#7fe0a4', '#7fd8ff', '#ff9a5a', '#f2f2f2', '#e5567f', '#ffd1e8', '#4fae8c', '#e2b33c', '#9b6bd6', '#f08a5d', '#6cc3c1', '#f7e08a', '#c3a6ff'];
function folk(r, n) {
  var off = Math.floor(r() * CLOTH.length), out = [];
  for (var i = 0; i < n; i++) out.push({ col: CLOTH[(off + i * 5) % CLOTH.length], hair: Math.floor(r() * HAIR.length), skirt: r() < 0.35 ? 1 : 0, dir: 1 });
  return out;
}

/* ---------------------------------------------------------------- props */
function ground(c, x0, x1, deck, H, col) { paper(c, rect(x0 - 4, deck, x1 - x0 + 8, H - deck + 4), col, 2); }
function banner(c, cx, y, text, hh, col, seed, hits) {
  if (!text) return;
  c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif';
  var bw = c.measureText(text).width + 20, bh = Math.max(20, hh * 0.32);
  c.strokeStyle = 'rgba(40,20,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(cx - bw / 2 + 6, y - 8); c.lineTo(cx - bw / 2 + 6, y); c.moveTo(cx + bw / 2 - 6, y - 8); c.lineTo(cx + bw / 2 - 6, y); c.stroke();
  var tl = bh * 0.55;
  paper(c, function (q) { jag(q, [[cx - bw / 2 - tl, y], [cx + bw / 2 + tl, y], [cx + bw / 2, y + bh / 2], [cx + bw / 2 + tl, y + bh], [cx - bw / 2 - tl, y + bh], [cx - bw / 2, y + bh / 2]], seed % 997, 0.8); }, col, 1.6);
  c.save(); c.strokeStyle = '#f2c94c'; c.lineWidth = 1.2; c.globalAlpha = 0.9; c.strokeRect(cx - bw / 2 + 2, y + 3, bw - 4, bh - 6);
  c.fillStyle = '#f2c94c';
  [-1, 1].forEach(function (sd) { var ex = cx + sd * (bw / 2 - 1); for (var k = 0; k < 3; k++) { var fy = y + bh * (0.22 + k * 0.28); c.beginPath(); c.moveTo(ex, fy - bh * 0.09); c.quadraticCurveTo(ex + sd * bh * 0.2, fy, ex + sd * bh * 0.32, fy - bh * 0.12); c.quadraticCurveTo(ex + sd * bh * 0.18, fy + bh * 0.06, ex, fy + bh * 0.09); c.closePath(); c.fill(); } });
  c.restore();
  c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, cx, y + bh / 2 + 1);
  hits.push({ k: 'event', x0: cx - bw / 2, x1: cx + bw / 2, y0: y - 8, y1: y + bh + 8 });
}
/* a Lanna sala: posts, a two-tier roof and the crossed kalae horns on its gable */
function sala(c, x0, x1, deck, top, night, col) {
  var w = x1 - x0, wood = night ? '#4a2e1c' : '#7a4a2a', roof = col || (night ? '#6d2b20' : '#a8432f');
  [x0 + w * 0.06, x1 - w * 0.06].forEach(function (px) { paper(c, rect(px - 3, top + (deck - top) * 0.3, 6, (deck - top) * 0.7), wood, 1.2); });
  var e1 = top + (deck - top) * 0.32, m = x0 + w / 2;
  paper(c, poly([[x0 - w * 0.04, e1], [x0 + w * 0.2, top + (deck - top) * 0.12], [x1 - w * 0.2, top + (deck - top) * 0.12], [x1 + w * 0.04, e1]]), roof, 1.6);
  paper(c, poly([[x0 + w * 0.14, top + (deck - top) * 0.14], [m, top - (deck - top) * 0.06], [x1 - w * 0.14, top + (deck - top) * 0.14]]), roof, 1.8);
  var ky = top - (deck - top) * 0.06, kl = (deck - top) * 0.14;
  c.save(); c.strokeStyle = '#e8b84a'; c.lineWidth = 2.2; c.lineCap = 'round';
  c.beginPath(); c.moveTo(m, ky); c.quadraticCurveTo(m - kl * 0.2, ky - kl * 0.8, m - kl * 0.7, ky - kl * 1.1); c.moveTo(m, ky); c.quadraticCurveTo(m + kl * 0.2, ky - kl * 0.8, m + kl * 0.7, ky - kl * 1.1); c.stroke(); c.restore();
  return e1;
}
/* the sala over part of the stage, so the sights stay in view; S narrows to it */
function under(S, col) {
  var w = Math.min(S.span * 0.62, S.hh * 6), a0 = S.x0 + (S.span - w) * (0.25 + 0.5 * ((S.seed >>> 8) % 100) / 100), top = S.deck - S.hh * 2.05;
  sala(S.c, a0, a0 + w, S.deck, top, S.night, col);
  S.x0 = a0 + w * 0.02; S.x1 = a0 + w * 0.98; S.span = S.x1 - S.x0;
  return top;
}
function lanternGlow(c, x, y, rad, hue, on) {
  var g = c.createRadialGradient(x, y, 0, x, y, rad * 3); g.addColorStop(0, 'hsla(' + hue + ',100%,70%,' + 0.5 * on + ')'); g.addColorStop(1, 'hsla(' + hue + ',100%,60%,0)');
  c.fillStyle = g; c.beginPath(); c.arc(x, y, rad * 3, 0, TAU); c.fill();
}
/* string between two points as a catenary, y = a·cosh(x/a), with something hung along it */
function strand(c, xa, xb, y, sag, every, hang) {
  var xm = (xa + xb) / 2, half = (xb - xa) / 2, a = half / 1.4, ch = Math.cosh(half / a) - 1, x;
  function cat(q) { return y + sag - sag * (Math.cosh((q - xm) / a) - 1) / ch; }
  c.strokeStyle = 'rgba(40,20,30,.85)'; c.lineWidth = 1.2; c.beginPath();
  for (x = xa; x <= xb; x += 4) x === xa ? c.moveTo(x, cat(x)) : c.lineTo(x, cat(x)); c.stroke();
  for (x = xa + every / 2, i = 0; x < xb - 4; x += every, i++) hang(x, cat(x), i);
  var i;
}
function notes(c, x, y, t, n, col) {
  for (var i = 0; i < n; i++) {
    var u = ((t / 2600 + i / n) % 1), nx = x + i * 9 + Math.sin(u * TAU * 1.5 + i) * 14, ny = y - u * 90, a = Math.sin(u * Math.PI);
    c.save(); c.globalAlpha = a; c.fillStyle = col; c.strokeStyle = col; c.lineWidth = 1.6;
    c.beginPath(); c.ellipse(nx, ny, 4, 3, -0.4, 0, TAU); c.fill(); c.beginPath(); c.moveTo(nx + 3.6, ny - 1); c.lineTo(nx + 3.6, ny - 14); c.lineTo(nx + 9, ny - 11); c.stroke(); c.restore();
  }
}

/* ---------------------------------------------------------------- the scenes
   Each draws on the stage, x0 … x1 along the deck, and pushes its hit boxes.
   S: { c, W, H, t, x0, x1, span, deck, hh, r, night, label, seed, phone, hits } */
var SCENES = {
  /* a trail run: runners at their own speeds, x = x₀ + vt, bounce |sin ωt| */
  // v2 adds: tung banners, khom loi/motes, glowing finish line, dynamic cheering spectator, water station
  run: function (S) {
    var c = S.c, i, n = Math.max(3, Math.min(8, Math.floor(S.span / (S.hh * 0.75)))), crew = town(S, n + 1);
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#1f3326' : '#4f7d4a');
    var path = []; for (var x = S.x0 - 6; x <= S.x1 + 6; x += 10) path.push([x, S.deck + 6 + Math.sin(x * 0.012) * 3]);
    for (x = S.x1 + 6; x >= S.x0 - 6; x -= 10) path.push([x, S.deck + 20 + Math.sin(x * 0.012 + 0.6) * 3]);
    paper(c, function (q) { jag(q, path, 71, 1.5); }, S.night ? '#6b5a44' : '#c9a66b', 1);
    
    var wx = S.x0 + S.span * 0.85, wy = S.deck + 2;
    c.fillStyle = S.night ? '#2d4a63' : '#6495ed';
    c.fillRect(wx - S.hh * 0.4, wy - S.hh * 0.4, S.hh * 0.8, S.hh * 0.4);
    c.fillStyle = '#fff';
    for (i = 0; i < 3; i++) c.fillRect(wx - S.hh * 0.15 + i * S.hh * 0.15, wy - S.hh * 0.55, S.hh * 0.08, S.hh * 0.15);
    var spec = crew[n]; spec.dir = -1;
    var cheer = (S.t / 300) % TAU;
    person(c, wx, wy, S.hh * 0.82, { lean: 0.1, seat: 0, legs: [0.1, 0, -0.1, 0], arms: [2.8 + Math.sin(cheer) * 0.4, 0.2, 3.1 + Math.sin(cheer + 1) * 0.4, 0.2] }, spec);

    var ax = S.x0 + S.span * (0.2 + S.r() * 0.6), top = S.deck - S.hh * 1.75;
    paper(c, rect(ax - S.hh * 0.9, top, 5, S.deck - top + 10), '#e8e2d0', 1.4); paper(c, rect(ax + S.hh * 0.9, top, 5, S.deck - top + 10), '#e8e2d0', 1.4);
    
    tung(S, ax - S.hh * 0.9, top + S.hh * 0.8, 1); tung(S, ax + S.hh * 0.9, top + S.hh * 0.8, 2);
    if (S.night) { lanternGlow(c, ax - S.hh * 0.9, top, S.hh * 0.5, 45, 1); lanternGlow(c, ax + S.hh * 0.9, top, S.hh * 0.5, 45, 1); }
    
    banner(c, ax + 2, top + 2, S.label, S.hh, '#e0773a', S.seed, S.hits);
    
    if (S.night) khomLoi(S, 4); else motes(S, 6);
    
    for (i = 0; i < n; i++) {
      var v = S.hh * (0.9 + 0.5 * ((i * 37 + S.seed) % 7) / 7), span = S.span + S.hh * 2, px = S.x0 - S.hh + ((i / n * span + S.t / 1000 * v) % span);
      var p = S.t / 1000 * TAU * (1.3 + 0.1 * (i % 3)) + i, d = crew[i]; d.skirt = 0;
      person(c, px, S.deck + 12 + (i % 2) * 5, S.hh * (0.92 + (i % 3) * 0.04), walkP(p, true), d);
      
      if (px > ax && px < ax + S.hh * 1.5) {
        c.fillStyle = 'rgba(150, 200, 255, 0.8)';
        c.beginPath(); c.arc(px - S.hh * 0.15, S.deck - S.hh * 0.8 + Math.sin(p * 2) * 4, S.hh * 0.05, 0, TAU); c.fill();
      }
    }
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.2, y1: S.H });
  },
  /* yoga on the grass: the class moves through mountain, arms up, tree and warrior
     together, a breath every six seconds (the sun or moon behind breathes with it) */
  yoga: function (S) {
    var c = S.c, i, n = Math.max(2, Math.min(5, Math.floor(S.span / (S.hh * 1.1)))), crew = town(S, n + 1);
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#1f3326' : '#5b8a5e');
    var br = 1 + 0.08 * Math.sin(S.t / 6000 * TAU), sx = S.x0 + S.span * 0.5, sy = S.deck - S.hh * 1.6, sr = S.hh * 0.38 * br;
    if (!S.night) paper(c, function (q) { q.beginPath(); for (var j = 0; j < 32; j++) { var rr = j % 2 ? sr * 1.15 : sr * 1.5, aa = j / 32 * TAU + S.t / 30000; q.lineTo(sx + Math.cos(aa) * rr, sy + Math.sin(aa) * rr); } q.closePath(); }, '#f6a92c', 1);
    paper(c, function (q) { circ(q, sx, sy, sr, 13); }, S.night ? '#fff2c8' : '#ffd65a', 0.8);
    var seq = [POSE.stand, POSE.up, POSE.tree, POSE.up, POSE.warrior, POSE.fold], u = S.t / 4000, k = Math.floor(u) % seq.length, P = mix(seq[k], seq[(k + 1) % seq.length], ease((u % 1) * 2.5 - 1.5));
    var mats = ['#4fae8c', '#9b6bd6', '#e5567f', '#4d8fd1', '#e2b33c', '#e0773a'];
    for (i = 0; i < n; i++) {
      var mx = S.x0 + S.span * (i + 0.5) / (n + 0.6) + S.hh * 0.3;
      paper(c, rect(mx - S.hh * 0.45, S.deck + 10, S.hh * 0.9, 6), mats[(i + S.seed) % mats.length], 0.6);
      crew[i].dir = 1; person(c, mx, S.deck + 10, S.hh, P, crew[i]);
    }
    var tx = S.x1 - S.hh * 0.6; crew[n].dir = -1;
    paper(c, rect(tx - S.hh * 0.45, S.deck + 10, S.hh * 0.9, 6), '#f2e6c9', 0.6);
    person(c, tx, S.deck + 10, S.hh * 1.05, P, crew[n]);
    banner(c, sx, sy + sr * 1.5 + 6, S.label, S.hh, '#4fae8c', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.2, y1: S.H });
  },
  /* sitting still: a ring of people seated, candles that flicker, a halo that breathes */
  calm: function (S) {
    var c = S.c, i, n = Math.max(3, Math.min(7, Math.floor(S.span / (S.hh * 0.85)))), crew = town(S, n);
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1d18' : '#8a6a4a');
    var cx = S.x0 + S.span * 0.5, br = 1 + 0.1 * Math.sin(S.t / 6000 * TAU);
    var g = c.createRadialGradient(cx, S.deck - S.hh * 0.4, 0, cx, S.deck - S.hh * 0.4, S.hh * 2.2 * br);
    g.addColorStop(0, 'rgba(255,214,120,.45)'); g.addColorStop(1, 'rgba(255,214,120,0)'); c.fillStyle = g; c.fillRect(cx - S.hh * 2.5, S.deck - S.hh * 2.6, S.hh * 5, S.hh * 3);
    for (i = 0; i < 5; i++) {
      var kx = cx + (i - 2) * S.hh * 0.22, ky = S.deck + 8, kh = S.hh * (0.18 + 0.05 * (i % 2)), fl = 1 + 0.15 * Math.sin(S.t / 90 + i * 2);
      paper(c, rect(kx - 3, ky - kh, 6, kh), '#f5ead2', 0.8);
      lanternGlow(c, kx, ky - kh - 6, 4, 45, 0.9);
      paper(c, function (q) { q.beginPath(); q.moveTo(kx, ky - kh - 13 * fl); q.quadraticCurveTo(kx + 4, ky - kh - 4, kx, ky - kh - 1); q.quadraticCurveTo(kx - 4, ky - kh - 4, kx, ky - kh - 13 * fl); q.closePath(); }, '#ffcf5a', 0.4);
    }
    var P = S.r() < 0.5 ? POSE.lotus : POSE.wai;
    for (i = 0; i < n; i++) {
      var side = i < n / 2 ? -1 : 1, j = i < n / 2 ? i : i - Math.ceil(n / 2), px = cx + side * (S.hh * 0.9 + j * S.hh * 0.7);
      crew[i].dir = -side; crew[i].skirt = 0;
      person(c, px, S.deck + 10 + (j % 2) * 4, S.hh * 0.95, i % 2 ? POSE.lotus : P, crew[i]);
    }
    banner(c, cx, S.deck - S.hh * 1.9, S.label, S.hh, '#d9a53c', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.2, y1: S.H });
  },
  /* a market lane: striped awnings, piles of fruit, lanterns that swing as pendulums,
     θ = θ₀·cos(√(g/L)·t), and shoppers walking both ways */
  market: function (S) {
    var c = S.c, i, n = Math.max(2, Math.min(6, Math.floor(S.span / (S.hh * 1.5)))), w = S.span / n;
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2b2522' : '#8d7b66');
    var aw = ['#d94b3b', '#4d8fd1', '#e2b33c', '#4fae8c', '#e5567f', '#9b6bd6'], fruit = ['#f08a5d', '#f7e08a', '#7fe0a4', '#e5567f', '#ffc266', '#9b6bd6'];
    for (i = 0; i < n; i++) {
      var x0 = S.x0 + i * w + w * 0.08, x1 = x0 + w * 0.84, tt = S.deck - S.hh * 0.42, top = S.deck - S.hh * 1.3, col = aw[(i + S.seed) % aw.length];
      paper(c, rect(x0 + 2, top, 4, S.deck - top), '#5a4030', 1); paper(c, rect(x1 - 6, top, 4, S.deck - top), '#5a4030', 1);
      paper(c, rect(x0, tt, x1 - x0, S.hh * 0.12), S.night ? '#5a4030' : '#9a6a4a', 1.2);
      for (var f = 0; f < 7; f++) { var fx = x0 + (x1 - x0) * (f + 0.5) / 7; paper(c, function (q) { circ(q, fx, tt - S.hh * 0.05, S.hh * 0.06, f + i); }, fruit[(f + i * 3 + S.seed) % fruit.length], 0.6); }
      paper(c, function (q) {
        q.beginPath(); q.moveTo(x0 - 6, top + S.hh * 0.2); q.lineTo(x0 + 6, top - S.hh * 0.1); q.lineTo(x1 - 6, top - S.hh * 0.1); q.lineTo(x1 + 6, top + S.hh * 0.2);
        var sc = (x1 - x0 + 12) / 6; for (var b = 6; b > 0; b--) q.arc(x0 - 6 + (b - 0.5) * sc, top + S.hh * 0.2, sc / 2, 0, Math.PI);
        q.closePath();
      }, col, 1.6);
      c.fillStyle = 'rgba(255,255,255,.35)'; for (var st = 0; st < 3; st++) c.fillRect(x0 + (x1 - x0) * (st * 2 + 0.6) / 6, top - S.hh * 0.06, (x1 - x0) / 9, S.hh * 0.24);
      var L = S.hh * 0.32, th = 0.35 * Math.cos(Math.sqrt(9.8 / (L / 40)) * S.t / 1000 + i), lx = x1 - 4 + Math.sin(th) * L, ly = top + S.hh * 0.25 + Math.cos(th) * L;
      c.strokeStyle = 'rgba(40,20,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x1 - 4, top + S.hh * 0.25); c.lineTo(lx, ly); c.stroke();
      if (S.night) lanternGlow(c, lx, ly + 5, 6, 10, 0.9);
      paper(c, function (q) { q.beginPath(); q.ellipse(lx, ly + 6, S.hh * 0.06, S.hh * 0.09, th * -0.5, 0, TAU); }, '#e04a3a', 0.8);
    }
    var crew = town(S, 6);
    for (i = 0; i < 6; i++) {
      var dir = i % 2 ? -1 : 1, v = S.hh * 0.35, sp = S.span + S.hh * 2, base = (i / 6 * sp + S.t / 1000 * v) % sp, px = dir > 0 ? S.x0 - S.hh + base : S.x1 + S.hh - base;
      crew[i].dir = dir; var me = person(c, px, S.deck + S.hh * 0.22 + (i % 2) * 4, S.hh * 0.95, walkP(S.t / 1000 * TAU * 0.9 + i, false), crew[i]);
      paper(c, rect(me.hand[0][0] - 4, me.hand[0][1], 9, 10), '#f2e6c9', 0.6);
    }
    banner(c, S.x0 + S.span * 0.5, S.deck - S.hh * 1.75, S.label, S.hh, '#d94b3b', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.3, y1: S.H });
  },
  /* a long table under a sala: bowls whose steam curls as x = A·sin(ky − ωt), glasses raised in turn */
  feast: function (S) {
    var c = S.c, i, n = 0, crew = town(S, 9);
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a14' : '#9a6a4a');
    var top = under(S), sx0 = S.x0, sx1 = S.x1;
    strand(c, sx0 + S.span * 0.1, sx1 - S.span * 0.1, top + S.hh * 0.72, S.hh * 0.18, 26, function (x, y, k) { var on = 0.6 + 0.4 * Math.sin(S.t / 420 + k); lanternGlow(c, x, y + 4, 3, 40, on); c.fillStyle = '#ffe2a0'; c.beginPath(); c.arc(x, y + 4, 2.2, 0, TAU); c.fill(); });
    n = Math.max(3, Math.min(8, Math.floor(S.span * 0.76 / (S.hh * 0.55))));
    var tx0 = S.x0 + S.span * 0.12, tx1 = S.x1 - S.span * 0.12, ty = S.deck - S.hh * 0.24;
    for (i = 0; i < n; i++) {
      var px = tx0 + (tx1 - tx0) * (i + 0.5) / n, cheer = Math.sin(S.t / 1600 + i * 1.9) > 0.55, P = cheer ? { lean: 0, seat: 0.24, legs: POSE.sit.legs, arms: [2.6, 0.3, 0.3, 0.9] } : POSE.sit;
      crew[i].dir = i % 2 ? -1 : 1; crew[i].skirt = 0;
      var me = person(c, px, S.deck, S.hh * 0.95, P, crew[i]);
      paper(c, rect(me.hand[0][0] - 2.5, me.hand[0][1] - 9, 5, 9), cheer ? '#ffe2a0' : 'rgba(255,240,200,.7)', 0.4);
    }
    paper(c, rect(tx0 - 10, ty, tx1 - tx0 + 20, S.hh * 0.12), '#f2e6c9', 1.6);
    paper(c, rect(tx0 - 10, ty + S.hh * 0.12, tx1 - tx0 + 20, S.hh * 0.14), '#d94b3b', 1.2);
    for (i = 0; i < n; i++) {
      var bx = tx0 + (tx1 - tx0) * (i + 0.5) / n + S.hh * 0.18, by = ty;
      paper(c, function (q) { q.beginPath(); q.arc(bx, by - 1, S.hh * 0.09, 0, Math.PI, false); q.closePath(); }, ['#f7e08a', '#7fd8ff', '#ffffff'][i % 3], 0.6);
      c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 1.5; c.beginPath();
      for (var y = 0; y < S.hh * 0.7; y += 3) { var xx = bx + Math.sin(y * 0.09 - S.t / 300 + i) * (2 + y * 0.08); y ? c.lineTo(xx, by - 6 - y) : c.moveTo(xx, by - 6 - y); } c.stroke();
    }
    banner(c, S.x0 + S.span * 0.5, top + S.hh * 0.95, S.label, S.hh, '#e58f3a', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
  },
  /* a band on a stage: guitar, voice and drums; notes rise on sine paths, the crowd sways
     at the drummer's beat */
  band: function (S) {
    var c = S.c, i, crew = town(S, 12), bpm = 96 + Math.floor(S.r() * 40), beat = S.t / 60000 * bpm, hit = Math.pow(Math.abs(Math.cos(beat * Math.PI)), 6);
    ground(c, S.x0, S.x1, S.deck, S.H, '#1d1420');
    var st0 = S.x0 + S.span * 0.12, st1 = S.x1 - S.span * 0.06, sy = S.deck - S.hh * 0.28, top = S.deck - S.hh * 2.1;
    for (i = 0; i < 3; i++) {
      var lx = st0 + (st1 - st0) * (0.2 + i * 0.3), hue = [300, 190, 45][(i + S.seed) % 3];
      var g = c.createLinearGradient(lx, top, lx, sy); g.addColorStop(0, 'hsla(' + hue + ',100%,70%,.45)'); g.addColorStop(1, 'hsla(' + hue + ',100%,70%,0)');
      c.fillStyle = g; c.beginPath(); c.moveTo(lx - 4, top); c.lineTo(lx + 4, top); c.lineTo(lx + S.hh * 0.6 + Math.sin(S.t / 1400 + i) * 20, sy); c.lineTo(lx - S.hh * 0.6 + Math.sin(S.t / 1400 + i) * 20, sy); c.fill();
    }
    paper(c, rect(st0, sy, st1 - st0, S.hh * 0.28), '#3a2a33', 2);
    paper(c, rect(st0 + 4, sy - S.hh * 0.62, S.hh * 0.3, S.hh * 0.62), '#2a2026', 1.4); paper(c, rect(st1 - 4 - S.hh * 0.3, sy - S.hh * 0.62, S.hh * 0.3, S.hh * 0.62), '#2a2026', 1.4);
    [st0 + 4 + S.hh * 0.15, st1 - 4 - S.hh * 0.15].forEach(function (cx) { [0.2, 0.45].forEach(function (f) { c.fillStyle = '#0d0a0c'; c.beginPath(); c.arc(cx, sy - S.hh * f, S.hh * (0.08 + hit * 0.015), 0, TAU); c.fill(); }); });
    var gx = st0 + (st1 - st0) * 0.3, vx = st0 + (st1 - st0) * 0.52, dx = st0 + (st1 - st0) * 0.74, h = S.hh * 0.95;
    /* drums */
    var dp = { lean: 0.1, seat: 0.3, legs: POSE.sit.legs, arms: [1.6 + hit * 0.8, 0.6, 1.4 + (1 - hit) * 0.8, 0.6] };
    crew[0].dir = -1; person(c, dx + S.hh * 0.25, sy, h, dp, crew[0]);
    paper(c, function (q) { q.beginPath(); q.ellipse(dx - S.hh * 0.05, sy - S.hh * 0.2, S.hh * 0.2, S.hh * 0.2, 0, 0, TAU); }, '#e5567f', 1.2);
    paper(c, rect(dx - S.hh * 0.42, sy - S.hh * 0.42, S.hh * 0.22, S.hh * 0.12), '#d9d0c0', 0.8);
    paper(c, rect(dx - S.hh * 0.62, sy - S.hh * 0.62 - hit * 3, S.hh * 0.28, 3), '#e8b84a', 0.6);
    /* guitar */
    crew[1].dir = 1; var gp = { lean: -0.05, legs: [0.15, 0, -0.15, 0], arms: [0.9, 0.9, 0.5 + 0.35 * Math.sin(beat * Math.PI * 2), 0.7] };
    var G = person(c, gx, sy, h, gp, crew[1]), gb = [G.hip[0] + 4, G.hip[1] - h * 0.06];
    paper(c, function (q) { q.save(); q.translate(gb[0], gb[1]); q.rotate(-0.5); q.beginPath(); q.ellipse(0, 0, h * 0.14, h * 0.1, 0, 0, TAU); q.rect(h * 0.1, -h * 0.025, h * 0.36, h * 0.05); q.restore(); }, '#c0392b', 1.2);
    /* voice */
    crew[2].dir = 1; var up = Math.sin(beat * Math.PI / 4) > 0.3;
    var V = person(c, vx, sy, h * 1.02, { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [1.2, 1.3, up ? 2.8 : 0.3, 0.2] }, crew[2]);
    c.strokeStyle = '#ccc'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(vx + h * 0.22, sy); c.lineTo(vx + h * 0.22, V.head[1] + h * 0.08); c.lineTo(vx + h * 0.12, V.head[1] + h * 0.05); c.stroke();
    notes(c, vx + h * 0.2, V.head[1] - 6, S.t, 4, '#ffe2a0');
    /* the crowd: heads and shoulders at the foot of the stage */
    var nc = Math.max(4, Math.floor(S.span / (S.hh * 0.42)));
    for (i = 0; i < nc; i++) {
      var cx = S.x0 + S.span * (i + 0.5) / nc, bob = Math.abs(Math.sin(beat * Math.PI + i * 0.7)) * 4, cy = S.H - 4 - bob, col = i % 3 ? '#3a2c46' : '#4a3858';
      paper(c, function (q) { q.beginPath(); q.ellipse(cx, cy, S.hh * 0.2, S.hh * 0.16, 0, Math.PI, TAU); q.moveTo(cx + S.hh * 0.1, cy - S.hh * 0.22); q.arc(cx, cy - S.hh * 0.22, S.hh * 0.1, 0, TAU); }, col, 1);
      if ((i * 7 + S.seed) % 5 === 0) { c.strokeStyle = col; c.lineWidth = Math.max(2, S.hh * 0.06); c.lineCap = 'round'; c.beginPath(); c.moveTo(cx + S.hh * 0.12, cy - S.hh * 0.1); c.lineTo(cx + S.hh * 0.22 + Math.sin(beat * Math.PI) * 4, cy - S.hh * 0.5); c.stroke(); }
    }
    banner(c, (st0 + st1) / 2, top + 6, S.label, S.hh, '#9b6bd6', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: st0, x1: st1, y0: top, y1: S.H });
  },
  /* a ball over a net: each shot a parabola, y = v₀t − ½gt²; the hitter swings as it arrives */
  ball: function (S) {
    var c = S.c, crew = town(S, 4), field = /football|soccer|futsal|rugby|frisbee|golf|cricket|ฟุตบอล/i.test(S.title || '');
    ground(c, S.x0, S.x1, S.deck, S.H, field ? (S.night ? '#1f3326' : '#4f8a4a') : (S.night ? '#1d3048' : '#3f78a8'));
    var cx = S.x0 + S.span * 0.5, half = Math.min(S.span * 0.36, S.hh * 2.3), ax = cx - half, bx = cx + half, by = S.deck + 10;
    c.strokeStyle = 'rgba(255,255,255,.75)'; c.lineWidth = 2; c.beginPath(); c.moveTo(ax - S.hh * 0.4, by + 2); c.lineTo(bx + S.hh * 0.4, by + 2); c.stroke();
    if (field) {
      [ax - S.hh * 0.6, bx + S.hh * 0.6].forEach(function (px) { c.strokeStyle = '#f2f2f2'; c.lineWidth = 3; c.beginPath(); c.moveTo(px - S.hh * 0.25, by); c.lineTo(px - S.hh * 0.25, by - S.hh * 1.5); c.moveTo(px + S.hh * 0.25, by); c.lineTo(px + S.hh * 0.25, by - S.hh * 1.5); c.moveTo(px - S.hh * 0.25, by - S.hh * 0.5); c.lineTo(px + S.hh * 0.25, by - S.hh * 0.5); c.stroke(); });
    } else {
      var nw = S.hh * 0.16, nt = by - S.hh * 0.6;
      c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 1; for (var m = 0; m <= 6; m++) { c.beginPath(); c.moveTo(cx - nw, nt + m * S.hh * 0.1); c.lineTo(cx + nw, nt + m * S.hh * 0.1); c.moveTo(cx - nw + m * nw / 3, nt); c.lineTo(cx - nw + m * nw / 3, by); c.stroke(); }
      paper(c, rect(cx - nw - 3, nt - 3, 4, by - nt + 3), '#e8e2d0', 1); paper(c, rect(cx + nw - 1, nt - 3, 4, by - nt + 3), '#e8e2d0', 1);
      paper(c, rect(cx - nw, nt - 3, nw * 2, 5), '#f2f2f2', 0.6);
    }
    var T = 1.7, u = (S.t / 1000 / T) % 1, leg = Math.floor(S.t / 1000 / T) % 2, from = leg ? bx - S.hh * 0.3 : ax + S.hh * 0.3, to = leg ? ax + S.hh * 0.3 : bx - S.hh * 0.3;
    var ballX = lerp(from, to, u), y0 = by - S.hh * 0.65, ballY = y0 - 4 * S.hh * 0.9 * u * (1 - u);
    var swingA = Math.max(0, 1 - Math.abs(u - (leg ? 1 : 0)) * 6), swingB = Math.max(0, 1 - Math.abs(u - (leg ? 0 : 1)) * 6);
    if (u > 0.98 || u < 0.02) swingA = swingB = 0.6;
    function player(px, dir, sw, d) { d.dir = dir; d.skirt = 0; var me = person(c, px, by, S.hh, { lean: 0.15, seat: 0.43, legs: [0.4, -0.5, -0.35, -0.2], arms: [0.6 + sw * 1.8, 0.4, -0.3, 0.6] }, d);
      if (!field) { var hd = me.hand[0]; c.strokeStyle = '#222'; c.lineWidth = 2; c.beginPath(); c.moveTo(hd[0], hd[1]); var rx = hd[0] + dir * Math.sin(0.6 + sw * 1.8) * S.hh * 0.14, ry = hd[1] + Math.cos(0.6 + sw * 1.8) * S.hh * 0.14; c.lineTo(rx, ry); c.stroke(); paper(c, function (q) { q.beginPath(); q.ellipse(rx, ry, S.hh * 0.07, S.hh * 0.055, 0.6, 0, TAU); }, '#e0773a', 0.6); } }
    player(ax, 1, leg ? swingB : swingA, crew[0]); player(bx, -1, leg ? swingA : swingB, crew[1]);
    if (S.span > S.hh * 7) { player(ax - S.hh * 0.9, 1, 0, crew[2]); player(bx + S.hh * 0.9, -1, 0, crew[3]); }
    c.strokeStyle = 'rgba(255,255,255,.25)'; c.lineWidth = 1.5; c.beginPath();
    for (var k = 0; k <= 12; k++) { var uu = Math.max(0, u - k * 0.02); var tx = lerp(from, to, uu), ty = y0 - 4 * S.hh * 0.9 * uu * (1 - uu); k ? c.lineTo(tx, ty) : c.moveTo(tx, ty); } c.stroke();
    paper(c, function (q) { circ(q, ballX, ballY, field ? S.hh * 0.08 : S.hh * 0.05, 5); }, field ? '#f2f2f2' : '#e8f04a', 0.8);
    banner(c, cx, S.deck - S.hh * 1.95, S.label, S.hh, '#e0773a', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.6, y1: S.H });
  },
  /* a class under a sala: the board chalks itself the day's formula, the room listens */
  learn: function (S) {
    var c = S.c, i, crew = town(S, 8), F = FORMULAS[S.seed % FORMULAS.length];
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a14' : '#9a6a4a');
    var top = under(S, S.night ? '#2a4a3a' : '#3f6b52'), sx0 = S.x0, sx1 = S.x1;
    var bw = Math.min(S.span * 0.4, S.hh * 2.4), bh = bw * 0.55, bx = sx1 - S.span * 0.06 - bw, by = S.deck - S.hh * 0.45 - bh;
    
    // Hanging lanna khom from the sala roof
    for (var k = 1; k < 4; k++) {
      var kx = sx0 + S.span * 0.25 * k, ky = top + S.hh * 0.05, s = S.hh * 0.15;
      c.strokeStyle = '#5a4030'; c.lineWidth = 1; c.beginPath(); c.moveTo(kx, ky); c.lineTo(kx, ky + s); c.stroke();
      if (S.night) lanternGlow(c, kx, ky + s, s * 2, 40, 0.6);
      c.fillStyle = S.night ? '#e8a34a' : '#c8342a'; c.beginPath(); c.moveTo(kx, ky + s); c.lineTo(kx - s*0.4, ky + s*0.4); c.lineTo(kx + s*0.4, ky + s*0.4); c.fill();
    }
    
    paper(c, rect(bx + bw * 0.2, by + bh, 3, S.deck - by - bh), '#5a4030', 1); paper(c, rect(bx + bw * 0.8, by + bh, 3, S.deck - by - bh), '#5a4030', 1);
    paper(c, rect(bx - 5, by - 5, bw + 10, bh + 10), '#7a4a2a', 1.6); 
    // lai kham (gold) pattern corners on the blackboard frame
    c.fillStyle = '#d9a83a'; c.fillRect(bx - 5, by - 5, bw * 0.08, 4); c.fillRect(bx - 5, by - 5, 4, bh * 0.15);
    c.fillRect(bx + bw + 5 - bw * 0.08, by - 5, bw * 0.08, 4); c.fillRect(bx + bw + 1, by - 5, 4, bh * 0.15);
    paper(c, rect(bx, by, bw, bh), '#24392f', 0.6);
    
    var u = (S.t / 9000) % 1.2, draw = Math.min(1, u * 1.6);
    c.save(); c.beginPath(); c.rect(bx, by, bw, bh); c.clip();
    c.strokeStyle = 'rgba(240,240,230,.85)'; c.fillStyle = 'rgba(240,240,230,.9)'; c.lineWidth = 1.6; F.draw(c, bx + bw * 0.62, by + bh * 0.5, bh * 0.36, draw);
    var fs = Math.max(11, bh * 0.15); c.font = '700 ' + Math.round(fs) + 'px Georgia,serif';
    fs = Math.max(8, fs * Math.min(1, bw * 0.88 / c.measureText(F.say).width)); c.font = '700 ' + Math.round(fs) + 'px Georgia,serif'; c.textAlign = 'left'; c.textBaseline = 'middle';
    var txt = F.say.slice(0, Math.ceil(F.say.length * Math.min(1, u * 2.2))); c.fillText(txt, bx + bw * 0.06, by + bh * 0.24);
    c.restore();
    
    // The teacher
    var tp = { lean: 0, legs: [0.1, 0, -0.1, 0], arms: [1.5 + 0.3 * Math.sin(S.t / 900), 0.9, 0.2, 0.3] };
    crew[0].dir = 1; person(c, bx - S.hh * 0.35, S.deck, S.hh * 1.02, tp, crew[0]);
    
    // Students
    var n = Math.max(2, Math.min(6, Math.floor((bx - S.hh * 0.9 - sx0) / (S.hh * 0.62))));
    for (i = 0; i < n; i++) {
      var px = sx0 + S.span * 0.08 + i * S.hh * 0.62, d = crew[i + 1]; d.dir = 1; d.skirt = 0;
      var raising = (S.t / 4000 + i) % 7 < 0.8; 
      var arms = raising ? [2.6 + 0.15 * Math.sin(S.t / 200 + i), 0, 0.3, 0.6] : ((S.t / 2500 + i) % 7 < 0.6 ? [2.9, 0, 0.3, 0.6] : [0.7, 0.9, 0.6, 1]);
      var nod = { lean: 0.08 + 0.05 * Math.sin(S.t / 1300 + i), seat: 0.24, legs: POSE.sit.legs, arms: arms };
      paper(c, rect(px - S.hh * 0.18, S.deck - S.hh * 0.24, S.hh * 0.32, 4), '#5a4030', 0.6);
      
      // small notebook prop for each student
      c.fillStyle = '#e8dccc'; c.beginPath(); c.moveTo(px, S.deck - S.hh * 0.24 - 2); c.lineTo(px + S.hh*0.12, S.deck - S.hh * 0.24 - 4); c.lineTo(px + S.hh*0.15, S.deck - S.hh * 0.24); c.fill();
      
      person(c, px, S.deck, S.hh * 0.95, nod, d);
    }
    
    // Fireflies / motes
    if (S.night) {
      for (i = 0; i < 5; i++) {
        var fx = sx0 + S.span * 0.2 + Math.sin(S.t/800 + i) * S.span * 0.15 + i * S.span * 0.1;
        var fy = top + S.hh * 0.4 + Math.sin(S.t/600 + i*2) * S.hh * 0.2;
        lanternGlow(c, fx, fy, 2, 50, 0.7);
        c.fillStyle = '#fff4a0'; c.beginPath(); c.arc(fx, fy, 1.5, 0, TAU); c.fill();
      }
    }
    
    banner(c, (sx0 + sx1) / 2, S.deck + S.hh * 0.14, S.label, S.hh, '#4d8fd1', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
  },
  /* a studio: a pot rising on the wheel, r(y) = r₀ + a·sin(ky + φ), and easels at work */
  studio: function (S) {
    var c = S.c, i, crew = town(S, 4), k = 2 + S.r() * 3, phi = S.r() * TAU;
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a14' : '#9a6a4a');
    var top = under(S, S.night ? '#3a2a5a' : '#6b5aa8'), sx0 = S.x0, sx1 = S.x1;
    var wx = S.x0 + S.span * 0.3, wy = S.deck - S.hh * 0.38;
    paper(c, rect(wx - S.hh * 0.32, wy, S.hh * 0.64, S.hh * 0.38), '#5a4030', 1.2);
    paper(c, rect(wx - S.hh * 0.3, wy - 5, S.hh * 0.6, 5), '#888', 0.8);
    var grow = 0.55 + 0.45 * ((S.t / 12000) % 1), ph = S.hh * 0.55 * grow, r0 = S.hh * 0.11;
    function rad(f) { return r0 * (0.55 + 0.6 * Math.sin(Math.PI * Math.min(1, f * 1.05)) + 0.16 * Math.sin(k * Math.PI * f + phi)) + (f > 0.9 ? r0 * (f - 0.9) * 4 : 0); }
    paper(c, function (q) { q.beginPath(); var f; for (f = 0; f <= 1; f += 0.05) q.lineTo(wx + rad(f), wy - 5 - f * ph); for (f = 1; f >= 0; f -= 0.05) q.lineTo(wx - rad(f), wy - 5 - f * ph); q.closePath(); }, '#c8794a', 1.2);
    c.strokeStyle = 'rgba(80,30,10,.35)'; c.lineWidth = 1;
    for (i = 0; i < 4; i++) { var a = (S.t / 400 + i * TAU / 4) % TAU; if (Math.sin(a) < 0) continue; c.beginPath(); for (var f = 0; f <= 1; f += 0.1) { var xx = wx + rad(f) * Math.cos(a); f ? c.lineTo(xx, wy - 5 - f * ph) : c.moveTo(xx, wy - 5 - f * ph); } c.stroke(); }
    crew[0].dir = 1; crew[0].skirt = 0; person(c, wx - S.hh * 0.5, S.deck, S.hh * 0.95, { lean: 0.35, seat: 0.24, legs: POSE.sit.legs, arms: [1.3, 0.3, 1.2, 0.4] }, crew[0]);
    var ne = Math.max(1, Math.min(3, Math.floor(S.span * 0.5 / (S.hh * 1.15))));
    for (i = 0; i < ne; i++) {
      var ex = S.x0 + S.span * 0.46 + i * S.hh * 1.15, ew = S.hh * 0.62, eh = S.hh * 0.5, ey = S.deck - S.hh * 1.02;
      c.strokeStyle = '#7a4a2a'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(ex, S.deck); c.lineTo(ex + ew * 0.5, ey - 6); c.lineTo(ex + ew, S.deck); c.moveTo(ex + ew * 0.5, ey - 6); c.lineTo(ex + ew * 0.5, S.deck); c.stroke();
      paper(c, rect(ex, ey, ew, eh), '#f5eedc', 1.2);
      var rr = rnd(S.seed + i * 77);
      c.save(); c.beginPath(); c.rect(ex + 3, ey + 3, ew - 6, eh - 6); c.clip();
      for (var b = 0; b < 6; b++) { c.fillStyle = CLOTH[Math.floor(rr() * CLOTH.length)]; c.globalAlpha = 0.85; var shape = rr(); if (shape < 0.4) { c.beginPath(); c.arc(ex + rr() * ew, ey + rr() * eh, eh * (0.1 + rr() * 0.25), 0, TAU); c.fill(); } else c.fillRect(ex + rr() * ew * 0.8, ey + rr() * eh * 0.8, ew * (0.1 + rr() * 0.4), eh * (0.08 + rr() * 0.3)); }
      c.restore();
      var d = crew[i + 1]; d.dir = -1;
      var me = person(c, ex + ew + S.hh * 0.35, S.deck, S.hh, { lean: 0.05, legs: [0.1, 0, -0.1, 0], arms: [1.45 + 0.15 * Math.sin(S.t / 500 + i), 0.3, 0.2, 0.5] }, d);
      c.strokeStyle = '#3b2a14'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(me.hand[0][0], me.hand[0][1]); c.lineTo(me.hand[0][0] - S.hh * 0.1, me.hand[0][1] - 2); c.stroke();
    }
    banner(c, (sx0 + sx1) / 2, top + S.hh * 0.62, S.label, S.hh, '#e2b33c', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
  },
  /* a screening in the open: the beam fans from the projector, the screen plays a
     ball rolling along y = |sin x| over the hills */
  film: function (S) {
    var c = S.c, i;
    ground(c, S.x0, S.x1, S.deck, S.H, '#14121c');
    var sw = Math.min(S.span * 0.44, S.hh * 3), sh = sw * 0.5, sx = S.x0 + S.span * 0.46 - sw / 2, sy = S.deck - S.hh * 0.4 - sh;
    c.strokeStyle = '#d0c8b8'; c.lineWidth = 3; c.beginPath(); c.moveTo(sx + 6, S.deck); c.lineTo(sx + 6, sy - 4); c.moveTo(sx + sw - 6, S.deck); c.lineTo(sx + sw - 6, sy - 4); c.stroke();
    var px = S.x0 + S.span * 0.08, py = S.deck - S.hh * 0.5;
    var g = c.createLinearGradient(px, py, sx, py); g.addColorStop(0, 'rgba(255,250,220,.5)'); g.addColorStop(1, 'rgba(255,250,220,.08)');
    c.fillStyle = g; c.beginPath(); c.moveTo(px, py - 3); c.lineTo(sx, sy); c.lineTo(sx, sy + sh); c.lineTo(px, py + 3); c.fill();
    paper(c, rect(sx, sy, sw, sh), '#f6f2e6', 1.6);
    c.save(); c.beginPath(); c.rect(sx + 4, sy + 4, sw - 8, sh - 8); c.clip();
    c.fillStyle = '#9fc8e0'; c.fillRect(sx, sy, sw, sh);
    c.fillStyle = '#5b8a5e'; c.beginPath(); c.moveTo(sx, sy + sh);
    for (var x = 0; x <= sw; x += 4) c.lineTo(sx + x, sy + sh * 0.7 - Math.abs(Math.sin(x / sw * 3 * Math.PI)) * sh * 0.25); c.lineTo(sx + sw, sy + sh); c.fill();
    var u = (S.t / 5000) % 1, bxx = u * sw; c.fillStyle = '#e04a3a'; c.beginPath(); c.arc(sx + bxx, sy + sh * 0.7 - Math.abs(Math.sin(u * 3 * Math.PI)) * sh * 0.25 - 6, 6, 0, TAU); c.fill();
    c.restore();
    paper(c, rect(px - S.hh * 0.16, py - S.hh * 0.1, S.hh * 0.26, S.hh * 0.2), '#3a3440', 1); c.fillStyle = '#fffbe0'; c.beginPath(); c.arc(px + S.hh * 0.1, py, 3, 0, TAU); c.fill();
    var nc = Math.max(4, Math.floor(S.span / (S.hh * 0.38)));
    for (i = 0; i < nc; i++) {
      var cx = S.x0 + S.span * (i + 0.5) / nc, cy = S.H - 2 - (i % 2) * S.hh * 0.12, col = i % 2 ? '#2e2a3c' : '#3c364e';
      paper(c, function (q) { q.beginPath(); q.ellipse(cx, cy, S.hh * 0.19, S.hh * 0.15, 0, Math.PI, TAU); q.moveTo(cx + S.hh * 0.1, cy - S.hh * 0.21); q.arc(cx, cy - S.hh * 0.21, S.hh * 0.1, 0, TAU); }, col, 1);
    }
    banner(c, sx + sw / 2, sy - S.hh * 0.45, S.label, S.hh, '#4d8fd1', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: sy - S.hh * 0.5, y1: S.H });
  },
  /* a class on its feet: jumping jacks in time, y = |sin ωt|, speakers pulsing rings */
  dance: function (S) {
    var c = S.c, i, rows = 2, per = Math.max(2, Math.min(6, Math.floor(S.span / (S.hh * 0.8)))), crew = town(S, rows * per + 1), bpm = 118 + Math.floor(S.r() * 14), b = S.t / 60000 * bpm * Math.PI;
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a22' : '#a86a7a');
    var s = Math.abs(Math.sin(b));
    var P = { lean: 0, lift: s * 0.06, legs: [0.08 + s * 0.35, 0, -0.08 - s * 0.35, 0], arms: [0.3 + s * 2.6, 0, -0.3 - s * 2.6 + TAU * 0, 0] };
    P.arms = [0.3 + s * 2.5, 0, 0.3 + s * 2.5 + 0.4, 0];
    [S.x0 + S.hh * 0.3, S.x1 - S.hh * 0.6].forEach(function (sx) {
      paper(c, rect(sx, S.deck - S.hh * 0.6, S.hh * 0.32, S.hh * 0.6), '#2a2026', 1.2);
      for (var k = 0; k < 3; k++) { var rr = ((b / Math.PI + k / 3) % 1) * S.hh * 0.8; c.strokeStyle = 'rgba(255,255,255,' + (0.35 * (1 - rr / (S.hh * 0.8))) + ')'; c.lineWidth = 1.5; c.beginPath(); c.arc(sx + S.hh * 0.16, S.deck - S.hh * 0.35, rr, -1.2, 1.2); c.stroke(); }
    });
    for (var row = 0; row < rows; row++) for (i = 0; i < per; i++) {
      var d = crew[row * per + i], px = S.x0 + S.span * (i + 0.5 + row * 0.5) / (per + 0.5);
      person(c, px, S.deck + 8 + row * S.hh * 0.18, S.hh * (0.9 + row * 0.06), P, d);
    }
    banner(c, S.x0 + S.span * 0.5, S.deck - S.hh * 1.9, S.label, S.hh, '#e5567f', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: S.deck - S.hh * 1.2, y1: S.H });
  },
  /* a gathering: bunting hung as catenaries, people in twos and threes, a word now and then */
  social: function (S) {
    var c = S.c, i, groups = Math.max(2, Math.min(4, Math.floor(S.span / (S.hh * 1.6)))), crew = town(S, groups * 3);
    ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#22202c' : '#7a8a6a');
    var poles = []; for (i = 0; i <= groups; i++) poles.push(S.x0 + S.span * (0.02 + 0.96 * i / groups));
    var top = S.deck - S.hh * 1.95, flags = ['#e5567f', '#e2b33c', '#4fae8c', '#4d8fd1', '#9b6bd6', '#f08a5d'];
    poles.forEach(function (px) { paper(c, rect(px - 2, top - 4, 4, S.deck - top + 4), '#e8e2d0', 1); });
    for (i = 0; i < groups; i++) strand(c, poles[i], poles[i + 1], top, S.hh * 0.32, 18, function (x, y, k) {
      var fl = Math.sin(S.t / 700 + x * 0.05) * 0.15;
      paper(c, poly([[x - 6, y], [x + 6, y], [x + Math.sin(fl) * 6, y + 13]]), flags[(k + S.seed) % flags.length], 0.5);
      if (S.night) lanternGlow(c, x, y + 4, 3, 45, 0.5);
    });
    for (i = 0; i < groups; i++) {
      var gx = S.x0 + S.span * (i + 0.5) / groups, m = 2 + (i + S.seed) % 2;
      for (var j = 0; j < m; j++) {
        var d = crew[i * 3 + j], px = gx + (j - (m - 1) / 2) * S.hh * 0.42; d.dir = j < m / 2 ? 1 : -1;
        var talk = Math.sin(S.t / 1100 + i * 2.1 + j * 1.3) > 0.6, drink = (i + j) % 2;
        var me = person(c, px, S.deck + 10 + (j % 2) * 3, S.hh * (0.95 + ((i + j) % 3) * 0.03), { lean: talk ? 0.08 : 0, legs: [0.06, 0, -0.06, 0], arms: [drink ? 1.0 : 0.15, drink ? 1.4 : 0.1, talk ? 1.2 : -0.1, talk ? 0.8 : 0.05] }, d);
        if (drink) paper(c, rect(me.hand[0][0] - 2.5, me.hand[0][1] - 9, 5, 9), '#ffe2a0', 0.4);
        if (talk) { var hx = me.head[0] + d.dir * S.hh * 0.16, hy = me.head[1] - S.hh * 0.22; paper(c, function (q) { q.beginPath(); q.ellipse(hx, hy, S.hh * 0.12, S.hh * 0.08, 0, 0, TAU); q.moveTo(hx - d.dir * S.hh * 0.04, hy + S.hh * 0.06); q.lineTo(hx - d.dir * S.hh * 0.1, hy + S.hh * 0.14); q.lineTo(hx, hy + S.hh * 0.07); }, '#fffaf0', 0.6);
          c.fillStyle = '#555'; for (var dd = -1; dd <= 1; dd++) { c.beginPath(); c.arc(hx + dd * S.hh * 0.05, hy, 1.4, 0, TAU); c.fill(); } }
      }
    }
    banner(c, S.x0 + S.span * 0.5, top + S.hh * 0.42, S.label, S.hh, '#8a76d8', S.seed, S.hits);
    S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: top, y1: S.H });
  }
};
/* the class's board: one result a day, drawn as it is chalked */
var FORMULAS = [
  { say: 'a² + b² = c²', draw: function (c, x, y, s, u) { c.beginPath(); c.moveTo(x - s, y + s * 0.7); c.lineTo(x - s + s * 2 * Math.min(1, u * 3), y + s * 0.7); if (u > 0.33) c.lineTo(x + s, y + s * 0.7 - s * 1.4 * Math.min(1, (u - 0.33) * 3)); if (u > 0.66) c.lineTo(lerp(x + s, x - s, Math.min(1, (u - 0.66) * 3)), lerp(y - s * 0.7, y + s * 0.7, Math.min(1, (u - 0.66) * 3))); c.stroke(); } },
  { say: 'A = πr²', draw: function (c, x, y, s, u) { c.beginPath(); c.arc(x, y, s * 0.8, 0, TAU * u); c.stroke(); if (u > 0.9) { c.beginPath(); c.moveTo(x, y); c.lineTo(x + s * 0.8, y); c.stroke(); } } },
  { say: 'φ = (1 + √5) / 2', draw: function (c, x, y, s, u) { c.beginPath(); for (var a = 0; a < 12 * u; a += 0.05) { var r = s * 0.06 * Math.pow(1.618, a / (Math.PI / 2)); a ? c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r) : c.moveTo(x + r, y); if (r > s * 1.4) break; } c.stroke(); } },
  { say: 'y = sin x', draw: function (c, x, y, s, u) { c.beginPath(); c.moveTo(x - s * 1.2, y); c.lineTo(x + s * 1.2, y); c.stroke(); c.beginPath(); for (var k = 0; k <= 60 * u; k++) { var px = x - s * 1.2 + k / 60 * s * 2.4; k ? c.lineTo(px, y - Math.sin(k / 60 * TAU * 1.5) * s * 0.6) : c.moveTo(px, y); } c.stroke(); } },
  { say: 'V − E + F = 2', draw: function (c, x, y, s, u) { var P = [[0, -1], [0.95, -0.31], [0.59, 0.81], [-0.59, 0.81], [-0.95, -0.31]], n = Math.floor(10 * u); c.beginPath(); for (var i = 0; i < Math.min(5, n); i++) { c.moveTo(x + P[i][0] * s, y + P[i][1] * s); c.lineTo(x + P[(i + 1) % 5][0] * s, y + P[(i + 1) % 5][1] * s); } for (i = 5; i < n; i++) { c.moveTo(x, y); c.lineTo(x + P[i - 5][0] * s, y + P[i - 5][1] * s); } c.stroke(); } },
  { say: '1 + 2 + … + n = n(n + 1) / 2', draw: function (c, x, y, s, u) { var n = 5, q = s * 0.3; for (var i = 0; i < n; i++) for (var j = 0; j <= i; j++) if ((i * 5 + j) / 20 < u) c.fillRect(x - s + j * q, y + s * 0.8 - (n - i) * q, q - 2, q - 2); } },
  { say: 'r = cos 3θ', draw: function (c, x, y, s, u) { c.beginPath(); for (var a = 0; a <= Math.PI * u; a += 0.02) { var r = s * Math.cos(3 * a); a ? c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r) : c.moveTo(x + r, y); } c.stroke(); } }
];
/* ---------------------------------------------------------------- the north's magic, over every scene
   Tung (ตุง, the long Lanna flags) on bamboo at the stage's ends, their cloth a travelling
   wave, x = A·(y/L)·sin(ky − ωt); by night khom loi (sky lanterns) rise from the stage and
   drift, x = x₀ + a·sin(2πu·1.5); by day gold motes twinkle. */
var TUNG = [['#d9342b', '#f2c94c', '#f2e6c9', '#2f8f5b'], ['#e5567f', '#f2c94c', '#4d8fd1', '#f2e6c9'], ['#9b6bd6', '#f2c94c', '#d9342b', '#f2e6c9'], ['#f08a5d', '#f2e6c9', '#2f8f5b', '#e8b84a']];
function tung(S, px, ht, k) {
  var c = S.c, top = S.deck - S.hh * ht, L = S.hh * ht * 0.72, w = S.hh * 0.2, N = 14, i, pal = TUNG[(S.seed + k) % TUNG.length];
  c.save(); c.strokeStyle = S.night ? '#8a7a4a' : '#c9b27a'; c.lineWidth = Math.max(2, S.hh * 0.04); c.lineCap = 'round';
  c.beginPath(); c.moveTo(px, S.deck + 6); c.lineTo(px, top - 4); c.moveTo(px - w * 0.2, top); c.lineTo(px + w * 1.1, top); c.stroke();
  for (i = 0; i < 6; i++) { c.beginPath(); c.moveTo(px - 2, S.deck - (S.deck - top) * i / 6); c.lineTo(px + 2, S.deck - (S.deck - top) * i / 6); c.stroke(); }
  c.restore();
  var x0 = px + w * 0.05, L0 = [], R0 = [];
  for (i = 0; i <= N; i++) { var f = i / N, y = top + 2 + f * L, dx = Math.sin(f * 5 - S.t / 520 + k) * f * w * 0.8 + Math.sin(S.t / 1700 + k) * f * w * 0.3; L0.push([x0 + dx, y]); R0.push([x0 + w + dx, y]); }
  for (i = 0; i < N; i++) {
    var a = L0[i], b = R0[i], cc = R0[i + 1], d = L0[i + 1], col = pal[Math.floor(i / 2) % pal.length];
    c.fillStyle = col; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.lineTo(cc[0], cc[1] + 0.6); c.lineTo(d[0], d[1] + 0.6); c.closePath(); c.fill();
    if (i % 2) { var mx = (a[0] + b[0] + cc[0] + d[0]) / 4, my = (a[1] + d[1]) / 2, z = w * 0.16; c.fillStyle = S.night ? 'rgba(10,10,30,.6)' : 'rgba(255,255,255,.55)'; c.beginPath(); c.moveTo(mx, my - z); c.lineTo(mx + z, my); c.lineTo(mx, my + z); c.lineTo(mx - z, my); c.closePath(); c.fill(); }
  }
  /* the swallow tail */
  var e = L0[N], g = R0[N]; c.fillStyle = pal[0]; c.beginPath(); c.moveTo(e[0], e[1]); c.lineTo(e[0] - w * 0.1, e[1] + w * 0.9); c.lineTo((e[0] + g[0]) / 2, e[1] + w * 0.3); c.lineTo(g[0] + w * 0.1, g[1] + w * 0.9); c.lineTo(g[0], g[1]); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(242,201,76,.8)'; c.lineWidth = 1; c.beginPath(); L0.forEach(function (p, j) { j ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke();
}
function khomLoi(S, n) {
  var c = S.c, i;
  for (i = 0; i < n; i++) {
    var P = 26 + i * 7, u = ((S.t / 1000) / P + i / n + (S.seed % 100) / 100) % 1, h0 = S.deck - S.hh * 0.6;
    var x = S.x0 + S.span * (0.12 + 0.76 * ((i * 0.618 + (S.seed % 37) / 37) % 1)) + Math.sin(u * TAU * 1.5 + i) * S.hh * 0.45, y = h0 - u * h0 * 0.95;
    var sz = S.hh * 0.13 * (1 - u * 0.55), a = Math.min(1, u * 8, (1 - u) * 3), fl = 0.85 + 0.15 * Math.sin(S.t / 110 + i * 3);
    c.save(); c.globalAlpha = a;
    var g = c.createRadialGradient(x, y, 0, x, y, sz * 3.2); g.addColorStop(0, 'rgba(255,190,90,' + 0.55 * fl + ')'); g.addColorStop(1, 'rgba(255,150,60,0)');
    c.fillStyle = g; c.beginPath(); c.arc(x, y, sz * 3.2, 0, TAU); c.fill();
    var gb = c.createLinearGradient(x, y - sz, x, y + sz); gb.addColorStop(0, '#ffe2a0'); gb.addColorStop(1, '#ff8a3a');
    c.fillStyle = gb; c.beginPath(); c.moveTo(x - sz * 0.55, y + sz * 0.8); c.lineTo(x - sz * 0.7, y - sz * 0.5); c.quadraticCurveTo(x, y - sz * 1.25, x + sz * 0.7, y - sz * 0.5); c.lineTo(x + sz * 0.55, y + sz * 0.8); c.closePath(); c.fill();
    c.fillStyle = '#fff6c0'; c.beginPath(); c.arc(x, y + sz * 0.85, sz * 0.18 * fl, 0, TAU); c.fill();
    c.restore();
  }
}
function motes(S, n) {
  var c = S.c, r = rnd(S.seed + 91), i;
  for (i = 0; i < n; i++) {
    var bx = S.x0 + r() * S.span, by = S.deck - S.hh * (0.4 + r() * 1.8), ph = r() * TAU, sp = 0.6 + r();
    var x = bx + Math.sin(S.t / 2400 * sp + ph) * S.hh * 0.3, y = by + Math.cos(S.t / 3100 * sp + ph) * S.hh * 0.15, a = Math.pow(Math.abs(Math.sin(S.t / 900 * sp + ph)), 3), z = S.hh * (0.03 + 0.03 * a);
    c.fillStyle = 'rgba(255,214,90,' + (0.25 + 0.75 * a) + ')';
    c.beginPath(); c.moveTo(x, y - z * 2); c.quadraticCurveTo(x, y, x + z * 2, y); c.quadraticCurveTo(x, y, x, y + z * 2); c.quadraticCurveTo(x, y, x - z * 2, y); c.quadraticCurveTo(x, y, x, y - z * 2); c.fill();
  }
}
function magic(S) {
  if (S.noMagic) return;
  tung(S, S.x0 + S.hh * 0.3, 2.15, 0);
  tung(S, S.x1 - S.hh * 0.55, 1.6, 2);
  if (S.night) khomLoi(S, S.phone ? 3 : 5); else motes(S, S.phone ? 8 : 14);
}

/* ---------------------------------------------------------------- portraits of one place
   A place page with no photograph of its own draws the place from its own facts (Nan,
   2026-10-02: "utilize the doodler to avoid filler"): S.place carries them (doodles_layer.place_facts):
   id, name, nameTh, nameEn, cat, sub, brand, hours, road, moo, tambon, amphoe, river {name, m},
   oldCity, hills, inside, services, cuisine, levels, facility, province. */
var DAYS = { mo: 1, tu: 2, we: 3, th: 4, fr: 5, sa: 6, su: 0 };
/* open now? OSM opening_hours in its common shapes ('24/7', 'Mo-Fr 08:00-17:00; Sa 09:00-12:00');
   null when the hours are missing or say something else */
function openNow(hours, now) {
  if (!hours) return null;
  var h = String(hours).toLowerCase().trim(); if (h === '24/7') return true;
  var b = new Date((now || Date.now()) + 7 * 3600e3), dow = b.getUTCDay(), mins = b.getUTCHours() * 60 + b.getUTCMinutes(), seen = false, open = false;
  h.split(';').forEach(function (part) {
    var m = /^\s*([a-z]{2})(?:\s*-\s*([a-z]{2}))?\s+(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(part); if (!m || !(m[1] in DAYS)) return;
    seen = true; var d0 = DAYS[m[1]], d1 = m[2] in DAYS ? DAYS[m[2]] : d0, inDay = d0 <= d1 ? dow >= d0 && dow <= d1 : dow >= d0 || dow <= d1;
    var a = +m[3] * 60 + +m[4], z = +m[5] * 60 + +m[6]; if (z <= a) z += 1440;
    if (inDay && (mins >= a && mins < z || mins + 1440 < z)) open = true;
  });
  return seen ? open : null;
}
/* กนก, the flame-leaf of Thai and Lanna carving: one leaf rising from (x, y), size s, curling to
   the side dir (1 right, -1 left), gold cut paper with its vein and three tongues; it sways a little */
function kranok(c, x, y, s, dir, t, col) {
  var sw = Math.sin((t || 0) / 900 + x * 0.013) * 0.05;
  c.save(); c.translate(x, y); c.scale(dir, 1); c.rotate(sw - 0.12);
  var leaf = function (q) { q.beginPath(); q.moveTo(0, 0);
    q.bezierCurveTo(-s * 0.16, -s * 0.42, s * 0.02, -s * 0.86, s * 0.42, -s * 1.02);
    q.quadraticCurveTo(s * 0.74, -s * 1.1, s * 0.7, -s * 0.86); q.quadraticCurveTo(s * 0.62, -s * 0.72, s * 0.5, -s * 0.84);
    q.quadraticCurveTo(s * 0.6, -s * 0.62, s * 0.4, -s * 0.6); q.quadraticCurveTo(s * 0.58, -s * 0.4, s * 0.32, -s * 0.36);
    q.quadraticCurveTo(s * 0.5, -s * 0.14, s * 0.24, -s * 0.06); q.quadraticCurveTo(s * 0.12, s * 0.04, 0, 0); q.closePath(); };
  paper(c, leaf, col || '#d9a23a', 1);
  c.strokeStyle = 'rgba(90,45,10,.75)'; c.lineWidth = Math.max(0.8, s * 0.03); leaf(c); c.stroke();
  c.beginPath(); c.moveTo(s * 0.06, -s * 0.06); c.quadraticCurveTo(s * 0.02, -s * 0.62, s * 0.5, -s * 0.9); c.stroke();
  c.fillStyle = '#fff1c2'; c.beginPath(); c.arc(s * 0.6, -s * 0.88, Math.max(1, s * 0.045), 0, TAU); c.fill();
  c.restore();
}
/* the place's name on a carved Lanna board, Thai over English, hung from two cords; lit when open */
function sign(c, cx, y, place, hh, col, lit) {
  if (!place) return null;
  var th = place.nameTh || place.name || '', en = place.nameEn && place.nameEn !== th ? place.nameEn : '';
  c.save(); c.textAlign = 'center'; c.textBaseline = 'middle';
  var f1 = Math.max(11, hh * 0.19), f2 = Math.max(9, hh * 0.13);
  c.font = '800 ' + Math.round(f1) + 'px "Sarabun",system-ui,sans-serif'; var w1 = c.measureText(th).width;
  c.font = '700 ' + Math.round(f2) + 'px "Sarabun",system-ui,sans-serif'; var w2 = en ? c.measureText(en).width : 0;
  var w = Math.min(Math.max(w1, w2) + hh * 0.5, hh * 7), h = en ? f1 + f2 + hh * 0.18 : f1 + hh * 0.16;
  c.strokeStyle = 'rgba(40,25,10,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(cx - w * 0.35, y - hh * 0.12); c.lineTo(cx - w * 0.35, y); c.moveTo(cx + w * 0.35, y - hh * 0.12); c.lineTo(cx + w * 0.35, y); c.stroke();
  paper(c, function (q) { q.beginPath(); q.moveTo(cx - w / 2, y); q.lineTo(cx + w / 2, y); q.lineTo(cx + w / 2 + h * 0.25, y + h / 2); q.lineTo(cx + w / 2, y + h); q.lineTo(cx - w / 2, y + h); q.lineTo(cx - w / 2 - h * 0.25, y + h / 2); q.closePath(); }, col || '#6a3a1e', 1.6);
  c.strokeStyle = '#e8b84a'; c.lineWidth = 1; c.strokeRect(cx - w / 2 + 3, y + 3, w - 6, h - 6);
  kranok(c, cx - w / 2 - h * 0.22, y + h * 0.62, h * 0.95, -1, place.t);
  kranok(c, cx + w / 2 + h * 0.22, y + h * 0.62, h * 0.95, 1, place.t);
  if (lit) { var g = c.createRadialGradient(cx, y + h / 2, 0, cx, y + h / 2, w * 0.7); g.addColorStop(0, 'rgba(255,214,120,.35)'); g.addColorStop(1, 'rgba(255,214,120,0)'); c.fillStyle = g; c.fillRect(cx - w, y - h, w * 2, h * 3); }
  c.fillStyle = lit === false ? '#cfc3a8' : '#fff4d6';
  c.font = '800 ' + Math.round(f1) + 'px "Sarabun",system-ui,sans-serif'; c.fillText(th.length > 34 ? th.slice(0, 33) + '…' : th, cx, y + hh * 0.08 + f1 / 2, w - 10);
  if (en) { c.font = '700 ' + Math.round(f2) + 'px "Sarabun",system-ui,sans-serif'; c.fillText(en.length > 40 ? en.slice(0, 39) + '…' : en, cx, y + hh * 0.1 + f1 + f2 / 2, w - 10); }
  c.restore();
  return { x0: cx - w / 2, x1: cx + w / 2, y0: y, y1: y + h };
}
/* the ground the place stands on, from its facts: the river by name when it is close, the old
   city's brick wall inside the moat, rice paddies by a village (moo), hills in the mountain districts */
function setting(S) {
  var P = S.place; if (!P) return;
  var c = S.c, hz = S.deck - S.hh * 0.35;
  if (P.hills) { paper(c, function (q) { var pts = []; for (var x = S.x0 - 6; x <= S.x1 + 6; x += 12) pts.push([x, hz - S.hh * (0.9 + 0.5 * Math.sin(x * 0.006 + S.seed % 7) + 0.25 * Math.sin(x * 0.02))]); pts.push([S.x1 + 6, hz + 4], [S.x0 - 6, hz + 4]); jag(q, pts, 61, 2); }, S.night ? '#1d2c26' : '#4d7a52', 1.4); }
  if (P.moo && !P.oldCity) for (var i = 0; i < 3; i++) { var ty = hz - S.hh * 0.05 + i * S.hh * 0.06; paper(c, rect(S.x0, ty, S.span, S.hh * 0.05), S.night ? '#24402e' : ['#88b05a', '#a0c060', '#6f9a4a'][i], 0.4); }
  if (P.oldCity) { var wy = hz - S.hh * 0.55, wx0 = S.x0 + S.span * 0.05, wx1 = S.x0 + S.span * 0.38, m = S.hh * 0.08;
    paper(c, function (q) { q.beginPath(); q.moveTo(wx0, hz); q.lineTo(wx0, wy); for (var x = wx0; x < wx1 - m; x += m * 2) { q.lineTo(x, wy - m); q.lineTo(x + m, wy - m); q.lineTo(x + m, wy); q.lineTo(x + m * 2, wy); } q.lineTo(wx1, wy); q.lineTo(wx1, hz); q.closePath(); }, S.night ? '#6d2b20' : '#a8432f', 1.4); }
  if (P.river && P.river.m != null && P.river.m < 400) {
    var ry = S.deck + (S.H - S.deck) * 0.35, rh = (S.H - S.deck) * 0.45;
    paper(c, function (q) { var pts = []; for (var x = S.x0 - 6; x <= S.x1 + 6; x += 10) pts.push([x, ry + Math.sin(x * 0.02 + S.t / 2000) * 2]); for (x = S.x1 + 6; x >= S.x0 - 6; x -= 10) pts.push([x, ry + rh + Math.sin(x * 0.02 + 1) * 2]); jag(q, pts, 63, 1); }, S.night ? '#2a4c7a' : '#4b8fc9', 0.8);
    c.strokeStyle = 'rgba(255,255,255,.4)'; c.lineWidth = 1.2; for (var k = 0; k < 8; k++) { var sx = S.x0 + ((k * 97 + S.t / 40) % S.span); c.beginPath(); c.moveTo(sx, ry + rh * 0.5); c.lineTo(sx + 10, ry + rh * 0.5); c.stroke(); }
    if (P.river.name) { c.fillStyle = 'rgba(255,255,255,.85)'; c.font = 'italic 600 ' + Math.round(Math.max(9, S.hh * 0.12)) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'right'; c.textBaseline = 'middle'; c.fillText(P.river.name, S.x1 - 8, ry + rh * 0.55); }
  }
}

var MATH = {
  run: 'x = x₀ + vt<br>y = |sin ωt|', yoga: 'r = r₀(1 + 0.08·sin 2πt/6)<br>a breath every six seconds', calm: 'r = r₀(1 + 0.1·sin 2πt/6)',
  market: 'θ = θ₀·cos(√(g/L)·t)', feast: 'x = A·sin(ky − ωt)', band: 'f = 440·2<sup>n/12</sup><br>y = sin 2πft',
  ball: 'y = v₀t − ½gt²', studio: 'r(y) = r₀ + a·sin(ky + φ)', film: 'y = |sin x|', dance: 'y = |sin ωt|', social: 'y = a·cosh(x/a)'
};
function math(set, seed) { return set === 'learn' ? FORMULAS[seed % FORMULAS.length].say : MATH[set] || ''; }
/* props: things a place's tags say it has (doodles_layer.place_facts → place.props), drawn over
   its portrait by doodler-props.js; ids there and in data/curated/portrait_props.json */
var PROPS = {};
function addProp(name, draw) { PROPS[name] = draw; }
function props(S) {
  var P = S.place; if (!P || !P.props || !P.props.length) return;
  if (!PROPS._in) { load('doodler-props.js'); return; }
  P.props.forEach(function (p) { if (PROPS[p]) { S.c.save(); try { PROPS[p](S); } catch (e) { } S.c.restore(); } });
}
/* more scenes from their own files (doodler-food.js, doodler-moat.js): name, draw(S),
   words that call it, where it sits among the turns, its line of math */
function addScene(name, draw, words, math, at) {
  SCENES[name] = draw;
  if (words) WORDS.splice(at == null ? 1 : at, 0, [name, words]);
  if (math) MATH[name] = math;
  if (ORDER.indexOf(name) < 0) ORDER.push(name);
}

/* the scenes kept in their own files load only on the day they are drawn (tools/doodler_pick.mjs
   checks this list against what each file registers) */
var FILES = { 'bayeux-tapestry': 'doodler-site-bayeux-tapestry.js', 'akha': 'doodler-akha.js', 'akha-swing': 'doodler-akha.js', food: 'doodler-food.js', moat: 'doodler-moat.js',
  cooking: 'doodler-craft.js', hotspring: 'doodler-craft.js', elephants: 'doodler-craft.js', massage: 'doodler-craft.js', takbat: 'doodler-craft.js', muaythai: 'doodler-craft.js', sakyant: 'doodler-craft.js',
  songkran: 'doodler-fest.js', cny: 'doodler-fest.js', yipeng: 'doodler-fest.js', umbrella: 'doodler-fest.js', flowers: 'doodler-fest.js', clocktower: 'doodler-fest.js', 'walking-street': 'doodler-fest.js',
  restaurant: 'doodler-eat.js', cafe: 'doodler-eat.js', bar: 'doodler-eat.js', bakery: 'doodler-eat.js', streetfood: 'doodler-eat.js', noodle: 'doodler-eat.js',
  hotel: 'doodler-stay.js', guesthouse: 'doodler-stay.js', hostel: 'doodler-stay.js', condo: 'doodler-stay.js', apartment: 'doodler-stay.js', dorm: 'doodler-stay.js', moobaan: 'doodler-stay.js', agent: 'doodler-stay.js',
  office: 'doodler-shop.js', garage: 'doodler-shop.js', gov: 'doodler-shop.js', salon: 'doodler-shop.js', clothes: 'doodler-shop.js', fixit: 'doodler-shop.js', parking: 'doodler-shop.js', mall: 'doodler-shop.js', pharmacy: 'doodler-shop.js', rental: 'doodler-shop.js', convenience: 'doodler-shop.js', crafts: 'doodler-shop.js', bank: 'doodler-shop.js', laundry: 'doodler-shop.js', fuel: 'doodler-shop.js', tours: 'doodler-shop.js', printing: 'doodler-shop.js', busstop: 'doodler-shop.js', post: 'doodler-shop.js', secondhand: 'doodler-shop.js', pets: 'doodler-shop.js',
  beautyclinic: 'doodler-beauty.js',
  'all-factored': 'doodler-site-all-factored.js', 'bag-knots': 'doodler-site-bag-knots.js', 'ban-sabai': 'doodler-site-ban-sabai.js',
  'stork-title': 'doodler-stork.js', 'stork-openbill': 'doodler-stork.js', 'stork-billgap': 'doodler-stork.js', 'stork-theories': 'doodler-stork.js', 'stork-woodcut': 'doodler-stork.js', 'stork-moon': 'doodler-stork.js',
  'stork-map': 'doodler-stork.js', 'stork-tally': 'doodler-stork.js', 'stork-shadow': 'doodler-stork.js', 'stork-frieze': 'doodler-stork.js', 'stork-popup': 'doodler-stork.js', 'stork-rooftops': 'doodler-stork.js',
  handicraft: 'doodler-arts.js', expedite: 'doodler-arts.js', robots: 'doodler-wheels.js', tuktuk: 'doodler-wheels.js',
  alley: 'doodler-lanna.js', rooftop: 'doodler-lanna.js', 'lanna-house': 'doodler-lanna.js', weights: 'doodler-civic.js',
  school: 'doodler-civic.js', community: 'doodler-civic.js', freshmarket: 'doodler-civic.js', clinic: 'doodler-civic.js', training: 'doodler-civic.js', gym: 'doodler-civic.js', hospital: 'doodler-civic.js', park: 'doodler-civic.js', university: 'doodler-civic.js', healthstation: 'doodler-civic.js', dentist: 'doodler-civic.js', tattoo: 'doodler-civic.js', optician: 'doodler-civic.js' };
var LOADING = {}, BASE = (function () { var sc = typeof document !== 'undefined' && document.currentScript; return sc && sc.src ? sc.src.replace(/doodler\.js(\?.*)?$/, '') : '/front/'; })();
function need(set) { if (!SCENES[set] && FILES[set]) load(FILES[set]); }
function load(f) {
  if (LOADING[f] || typeof document === 'undefined' || !document.createElement) return;
  LOADING[f] = 1; var s = document.createElement('script'); s.src = BASE + f; s.async = true;
  s.onload = function () { window.dispatchEvent(new Event('mddoodler')); };   /* the band repaints with it */
  document.head.appendChild(s);
}
function scene(c, W, H, t, o) {
  if (!SCENES[o.set] && FILES[o.set]) { need(o.set); return []; }   /* drawn from the next frame on, once its file is in */
  var x0 = o.x0 == null ? 0 : o.x0, x1 = o.x1 == null ? W : o.x1, span = x1 - x0, hits = [], set = SCENES[o.set] ? o.set : 'social';
  var S = { c: c, W: W, H: H, t: t, x0: x0, x1: x1, span: span, deck: o.deck, phone: o.phone, night: !!o.night, label: o.label || '', title: o.title || '',
    seed: o.seed >>> 0, r: rnd((o.seed >>> 0) || 1), hh: Math.min(H * (o.phone ? 0.2 : 0.24), span / 8, 90), hits: hits, set: set,
    variant: o.variant || '', alt: o.alt, now: o.now || Date.now(), lat: o.lat, lng: o.lng, avoid: o.avoid, place: o.place || null };
  if (S.place) S.place.t = t;
  c.save(); c.beginPath(); c.rect(x0, 0, span, H); c.clip(); SCENES[set](S); props(S);
  var M = { x0: x0, x1: x1, span: span }; Object.keys(M).forEach(function (k) { S[k] = M[k]; }); magic(S); c.restore();
  return hits;
}
/* the sun's altitude in degrees at a place and moment (the NOAA approximation) */
function sunAlt(t, lat, lng) {
  var d = t / 864e5 - 10957.5, g = (357.529 + 0.98560028 * d) * Math.PI / 180, q = 280.459 + 0.98564736 * d, L = (q + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * Math.PI / 180;
  var e = (23.439 - 0.00000036 * d) * Math.PI / 180, dec = Math.asin(Math.sin(e) * Math.sin(L)), ra = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L));
  var gmst = (18.697374558 + 24.06570982441908 * d) % 24, ha = ((gmst * 15 + lng) * Math.PI / 180) - ra, la = lat * Math.PI / 180;
  return Math.asin(Math.sin(la) * Math.sin(dec) + Math.cos(la) * Math.cos(dec) * Math.cos(ha)) * 180 / Math.PI;
}
/* a place page's portrait: its sky at this moment where it stands, the north's land, the scene of
   what it does drawn from its facts (o.place), no banner (its name is on its own sign) */
var BACK = {};
function portrait(c, W, H, t, o) {
  var P = o.place || {}, now = o.now || Date.now(), alt = o.alt != null ? o.alt : sunAlt(now, P.lat || 18.79, P.lng || 98.99), night = alt < -4;
  var band = alt > 6 ? 0 : alt > -1 ? 1 : alt > -8 ? 2 : 3, phone = W < 560, dpr = c.getTransform ? c.getTransform().a : 1;
  /* sky and land change with the light's band, not the frame: cut once, laid each frame */
  var key = [W, H, dpr, band, P.province, !!o.ridge].join('|'), B = BACK[key];
  if (!B) {
    B = document.createElement('canvas'); B.width = Math.round(W * dpr); B.height = Math.round(H * dpr);
    var k = B.getContext('2d'); k.setTransform(dpr, 0, 0, dpr, 0, 0);
    var g = k.createLinearGradient(0, 0, 0, H); g.addColorStop(0, ['#5f9fc2', '#b9617a', '#2a2650', '#121330'][band]); g.addColorStop(1, ['#8fbfd6', '#e39a7a', '#4b3a6b', '#1d1f3f'][band]);
    k.fillStyle = g; k.fillRect(0, 0, W, H);
    if (night) { var r = rnd(9); for (var i = 0; i < 40; i++) { k.fillStyle = 'rgba(255,246,214,' + (0.4 + 0.4 * r()) + ')'; k.fillRect(r() * W, r() * H * 0.45, 1.6, 1.6); } }
    SKY.landscape(k, W, H, { horizon: H * 0.6, night: night, pm25: 15, ridge: o.ridge, phone: phone, cr: P.province === 'cr', x0: W * 0.04, x1: W * 0.96 });
    var ks = Object.keys(BACK); if (ks.length > 6) delete BACK[ks[0]];
    BACK[key] = B;
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(B, 0, 0); c.restore();
  return scene(c, W, H, t, { set: o.set, seed: o.seed != null ? o.seed : hash(String(P.id || P.name || '')), label: '', title: (P.name || '') + ' ' + (P.nameEn || ''), night: night, phone: phone,
    deck: H * 0.84, x0: 0, x1: W, variant: o.variant, alt: alt, now: now, lat: P.lat, lng: P.lng, place: P });
}
/* the whole picture: sky, the north's land and sights, the scene */
function full(c, W, H, t, o) {
  var night = !!o.night, g = c.createLinearGradient(0, 0, 0, H);
  if (night) { g.addColorStop(0, '#0d0820'); g.addColorStop(0.62, '#2a1a4a'); g.addColorStop(1, '#4a2a4a'); }
  else { g.addColorStop(0, '#8fbfd6'); g.addColorStop(0.7, '#cfe3e8'); g.addColorStop(1, '#f2e6c9'); }
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  var phone = W < 560;
  SKY.landscape(c, W, H, { horizon: H * 0.66, night: night, pm25: 12, ridge: o.ridge, phone: phone, cr: o.cr });
  return scene(c, W, H, t, { set: o.set, seed: o.seed, label: o.label, title: o.title, night: night, phone: phone, deck: H * 0.84, x0: 0, x1: W,
    variant: o.variant, alt: o.alt, now: o.now, lat: o.lat, lng: o.lng });
}

window.MDDOODLER = { portrait: portrait, addProp: addProp, props: PROPS, sunAlt: sunAlt, setOf: setOf, pick: pick, choose: choose, scene: scene, full: full, math: math, sets: function () { return Object.keys(SCENES); }, order: ORDER, hash: hash, addScene: addScene,
  near: NEAR, forReader: forReader, files: FILES, need: need, versions: VERSIONS, variants: VARIANTS, version: version, variantOf: variantOf, kit: { paper: paper, jag: jag, circ: circ, poly: poly, rect: rect, lerp: lerp, ease: ease, rnd: rnd, hash: hash, TAU: TAU, person: person, POSE: POSE, mix: mix,
    walkP: walkP, folk: folk, town: town, SKIN: SKIN, CLOTH: CLOTH, ground: ground, banner: banner, sala: sala, under: under, lanternGlow: lanternGlow, strand: strand, notes: notes,
    tung: tung, khomLoi: khomLoi, motes: motes, akhaHat: akhaHat, openNow: openNow, sign: sign, setting: setting, kranok: kranok } };
})();
