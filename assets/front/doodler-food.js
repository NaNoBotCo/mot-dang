/* The food table for the auto-doodler (Nan, 2026-10-02: "There should also be a doodle
   banner for food … Animate it and make it magically lanna all of it"). Fourteen kitchens,
   each under a Lanna sala hung with khom lanterns: a cook at work, a table of that kitchen's
   dishes, diners eating, a hanging sign in Thai and English, and one prop from that kitchen's
   home cut in Lanna paper. The event's words pick the kitchen (o.variant wins); an event
   with no kitchen named gets the khantok.

   MDDOODLER_FOOD.cuisineOf(text) → 'japanese', 'isaan' … ('lanna' when nothing matches)
   MDDOODLER_FOOD.cuisines         the fourteen keys
   MDDOODLER_FOOD.math(key)        that kitchen's line of math
   The still parts are cut once per size and seed into two offscreen layers (behind the
   diners, and the table in front of them); each frame draws what moves. */
(function () {
'use strict';
var TAU = 6.2832;

/* ---------------------------------------------------------------- which kitchen
   first match wins, so the narrow kitchens come before the wide ones */
var DETECT = [
  ['lanna', /lanna|northern thai|northern food|khan ?toke?|khao ?so[iy]|sai ?o?ua|nam ?prik ?(ong|noom|num)|hang ?lay|hinlay|khaep ?mu|nam ?ngiao|ล้านนา|ขันโตก|ข้าวซอย|ไส้อั่ว|น้ำพริก(อ่อง|หนุ่ม)|แกงฮังเล|อาหารเหนือ|อาหารพื้นเมือง|ลาบ(เมือง|คั่ว)|แคบหมู|น้ำเงี้ยว/i],
  ['dutch', /dutch|holland|netherland|stroopwafel|poffert|bitterbal|herring|haring|gouda|\bedam\b|ดัตช์|ฮอลแลนด์|เนเธอร์แลนด์/i],
  ['swiss', /swiss|switzerland|fondue|raclette|r[öo]sti|emmental|gruy[eè]re|สวิส|ฟองดู|ราเคล็ต/i],
  ['swedish', /swed|scandinav|nordic|sm[öo]rg[åa]s|meatball|k[öo]ttbullar|kanelbull|cinnamon bun|\bfika\b|lingonberr|midsommar|สวีเดน|สแกนดิเนเวีย|มีทบอล/i],
  ['japanese', /japan|sushi|sashimi|ramen|izakaya|\budon\b(?!\s*thani)|\bsoba\b|tempura|yakitori|yakiniku|teppan|omakase|matcha|bento|donburi|tonkatsu|ญี่ปุ่น|ซูชิ|ซาชิมิ|ราเม[งน]|ราเม็ง|อิซากายะ|มัทฉะ/i],
  ['chinese', /chin(a|ese)\b|dim ?sum|yum ?cha|peking|pipa duck|roast duck|canton|szechuan|sichuan|dumpling|xiao ?long|hot ?pot|mooncake|จีน|ติ่มซำ|เป็ดย่าง|เป็ดปักกิ่ง|ขนมไหว้พระจันทร์|เกี๊ยว|ซาลาเปา/i],
  ['vietnamese', /vietnam|\bpho\b|phở|banh ?mi|bánh|goi ?cuon|nem ?nuong|bun ?cha|เวียดนาม|เฝอ|บั๋นหมี่|แหนมเนือง|ปากหม้อญวน/i],
  ['burmese', /burm|myanmar|mohinga|lahpet|laphet|tea ?leaf salad|พม่า|เมียนมา|ยำใบชา/i],
  ['soul-food', /soul ?food|fried chicken|collard|cornbread|\bgrits\b|gumbo|jambalaya|cajun|creole|catfish|southern[- ](fried|comfort|cooking|style)|sweet potato pie|โซลฟู้ด/i],
  ['falafel', /falafel|felafel|hummus|houmous|shawarma|shawerma|kebab|kebap|\bpita\b|mezze|\bmeze\b|lebanese|middle[- ]eastern|israeli|levant|ฟาลาเฟล|ฮัมมัส|ชาวาร์มา|เคบับ/i],
  ['isaan', /isaan|\bisan\b|issan|esarn|\besan\b|som ?tam|som ?tum|papaya salad|\blarb\b|\blaab\b|gai ?yang|kai ?yang|อีสาน|ส้มตำ|ตำ(ปู|ถาด|ซั่ว|ไทย|ลาว)|ลาบ|ไก่ย่าง|น้ำตก(หมู|เนื้อ)/i],
  ['southern-thai', /southern thai|south(ern)? (thai|food)|\broti\b|massaman|satay|khao ?yam|kua ?kling|kaeng ?som|gaeng ?som|yellow curry|tai ?pla|seafood|ภาคใต้|ปักษ์ใต้|อาหารใต้|โรตี|มัสมั่น|สะเต๊ะ|ข้าวยำ|คั่วกลิ้ง|แกงส้ม|แกงไตปลา|แกงเหลือง|ซีฟู้ด|อาหารทะเล/i],
  ['central-thai', /central thai|pad ?thai|phat ?thai|tom ?yu?m|green curry|red curry|mango sticky|royal thai|bangkok|\bcurry|ภาคกลาง|ผัดไทย|ต้มยำ|แกงเขียวหวาน|ข้าวเหนียวมะม่วง|ชาววัง|แกง/i],
  ['american', /americ|burger|hot ?dog|\bbbq\b|barbe?cue|smokehouse|brisket|\bribs\b|steak|\bdiner\b|pancake|waffle|brunch|breakfast|\broast\b|carvery|thanksgiving|mac (and|&|n) cheese|milkshake|tex-?mex|อเมริกัน|เบอร์เกอร์|สเต๊ก|บาร์บีคิว|แพนเค้ก/i],
  ['central-thai', /\bthai\b|ไทย/i]
];
/* the words that call the scene at all: dishes and kitchens, a kitchen's adjective only
   when a meal word follows it ("Japanese class" stays a class) */
var WORDS_RE = new RegExp([
  'khan ?toke?', 'khao ?so[iy]', 'sai ?o?ua', 'nam ?prik', 'hang ?lay', 'stroopwafel', 'poffert', 'bitterbal', 'herring', 'fondue', 'raclette', 'r[öo]sti\\b',
  'sm[öo]rg[åa]s', 'meatball', 'kanelbull', 'cinnamon bun', 'sushi', 'sashimi', 'ramen', 'izakaya', 'tempura', 'yakitori', 'yakiniku', 'teppan', 'omakase', 'matcha',
  'dim ?sum', 'yum ?cha', 'peking duck', 'pipa duck', 'roast duck', 'dumpling', 'xiao ?long', 'hot ?pot', 'mooncake', '\\bpho\\b', 'phở', 'banh ?mi', 'goi ?cuon',
  'mohinga', 'tea ?leaf salad', 'soul ?food', 'fried chicken', 'collard', 'cornbread', 'gumbo', 'jambalaya', 'falafel', 'felafel', 'hummus', 'shawarma', 'kebab', 'mezze',
  'som ?ta[mu]', 'papaya salad', '\\blarb\\b', '\\blaab\\b', 'gai ?yang', '\\broti\\b', 'massaman', 'satay', 'khao ?yam', 'seafood', 'pad ?thai', 'tom ?yum', 'green curry',
  '\\bcurry\\b', 'mango sticky', 'burger', 'hot ?dog', 'brisket', 'steak', 'pancake', 'waffle', '\\broast\\b', 'carvery', 'milkshake',
  '(lanna|northern thai|isaan|isan|southern thai|central thai|thai|american|dutch|swiss|swedish|japanese|chinese|vietnamese|burmese|myanmar|lebanese|middle[- ]eastern|israeli|cajun|creole) ' +
    '(food|cuisine|cooking|kitchen|dinner|lunch|brunch|breakfast|buffet|feast|tasting|bbq|barbecue|street food|dishes|menu|supper|banquet|restaurant)',
  'อาหาร(เหนือ|อีสาน|ใต้|ปักษ์ใต้|ภาคกลาง|ญี่ปุ่น|จีน|เวียดนาม|พม่า|อเมริกัน|ดัตช์|สวิส|สวีเดน|ไทย|พื้นเมือง|ล้านนา)',
  'ขันโตก', 'ข้าวซอย', 'ไส้อั่ว', 'น้ำพริกอ่อง', 'แกงฮังเล', 'ส้มตำ', 'ลาบ', 'ไก่ย่าง', 'ผัดไทย', 'ต้มยำ', 'ติ่มซำ', 'ซูชิ', 'ราเม[งน]', 'เฝอ', 'บั๋นหมี่', 'โรตี', 'สะเต๊ะ',
  'มัสมั่น', 'ข้าวยำ', 'ฟาลาเฟล', 'ฮัมมัส', 'ฟองดู', 'โซลฟู้ด'
].join('|'), 'i');
var KEYS = ['lanna', 'american', 'dutch', 'swiss', 'swedish', 'japanese', 'chinese', 'vietnamese', 'burmese', 'central-thai', 'isaan', 'southern-thai', 'soul-food', 'falafel'];
function cuisineOf(text) {
  text = text || '';
  for (var i = 0; i < DETECT.length; i++) if (DETECT[i][1].test(text)) return DETECT[i][0];
  return 'lanna';
}
var MATHS = {
  lanna: 'r = aθ<br>the sai oua coil', american: 'y = v₀t − ½gt²<br>the patty’s flip', dutch: 'θ = ωt<br>the mill’s sails',
  swiss: 'y = a·cosh(x/a)<br>the cheese string', swedish: 'θ = θ₀·sin ωt<br>the Dala horse rocking', japanese: 'x = A·sin(ky − ωt)<br>the ramen’s steam',
  chinese: 'y = A·sin(kx − ωt)<br>the naga’s dance', vietnamese: 'y = ½gt²<br>the phin’s drip', burmese: 'y = y₀ + g(x/v)²/2<br>the pulled tea',
  'central-thai': 'y = A·sin ωt<br>the boat on the khlong', isaan: 'y = |sin ωt|<br>the pestle in the krok', 'southern-thai': 'h = r·|cos θ|<br>the roti turning in the air',
  'soul-food': 'θ = 2π·(33⅓/60)·t<br>the record turning', falafel: 'r = aθ<br>the hummus swirl'
};
window.MDDOODLER_FOOD = { cuisineOf: cuisineOf, cuisines: KEYS.slice(), math: function (k) { return MATHS[k] || MATHS.lanna; }, words: WORDS_RE };

var D = window.MDDOODLER; if (!D || !D.kit || !D.kit.paper) return;
var K = D.kit, paper = K.paper, circ = K.circ, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease;

/* ---------------------------------------------------------------- small cut pieces */
var RR = K.rnd(1);
function E(x, y, rx, ry, rot) { return function (q) { q.beginPath(); q.ellipse(x, y, Math.max(0.3, rx), Math.max(0.3, ry), rot || 0, 0, TAU); }; }
function fe(c, x, y, rx, ry, col, rot) { c.fillStyle = col; c.beginPath(); c.ellipse(x, y, Math.max(0.3, rx), Math.max(0.3, ry), rot || 0, 0, TAU); c.fill(); }
function path(q, pts) { q.beginPath(); for (var i = 0; i < pts.length; i++) i ? q.lineTo(pts[i][0], pts[i][1]) : q.moveTo(pts[i][0], pts[i][1]); }
function fp(c, pts, col) { c.fillStyle = col; path(c, pts); c.closePath(); c.fill(); }
function ln(c, pts, col, w) { c.strokeStyle = col; c.lineWidth = Math.max(0.6, w); c.lineCap = 'round'; c.lineJoin = 'round'; path(c, pts); c.stroke(); }
function sprinkle(c, x, y, rx, ry, n, rad, cols) {
  for (var i = 0; i < n; i++) { var a = RR() * TAU, u = Math.sqrt(RR()); fe(c, x + Math.cos(a) * rx * u, y + Math.sin(a) * ry * u, rad, rad * 0.75, cols[i % cols.length], RR() * 3); }
}
/* the Archimedean spiral, r = aθ, squashed by sq for a coil lying flat */
function spiral(x, y, R, turns, sq, rot) {
  var pts = [], N = Math.ceil(turns * 30), a = R / (turns * TAU);
  for (var i = 0; i <= N; i++) { var th = i / N * turns * TAU; pts.push([x + Math.cos(th + (rot || 0)) * a * th, y + Math.sin(th + (rot || 0)) * a * th * sq]); }
  return pts;
}
function plate(c, x, y, w, col) {
  paper(c, E(x, y - w * 0.05, w * 0.5, w * 0.11), col || '#f6f1e6', 0.7);
  fe(c, x, y - w * 0.06, w * 0.38, w * 0.075, 'rgba(120,90,60,.10)');
  return y - w * 0.07;
}
/* a bowl from the side: body, rim, the surface of what is in it; returns that surface */
function bowl(c, x, y, w, body, soup, band) {
  var h = w * 0.4, ty = y - h;
  paper(c, function (q) {
    q.beginPath(); q.moveTo(x - w / 2, ty); q.bezierCurveTo(x - w / 2, y - w * 0.08, x - w * 0.22, y - w * 0.04, x - w * 0.16, y - w * 0.03);
    q.lineTo(x - w * 0.17, y); q.lineTo(x + w * 0.17, y); q.lineTo(x + w * 0.16, y - w * 0.03);
    q.bezierCurveTo(x + w * 0.22, y - w * 0.04, x + w / 2, y - w * 0.08, x + w / 2, ty); q.ellipse(x, ty, w / 2, w * 0.11, 0, 0, Math.PI, true); q.closePath();
  }, body, 0.9);
  fe(c, x, ty, w * 0.47, w * 0.095, soup);
  c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = Math.max(1, w * 0.025); c.beginPath(); c.ellipse(x, ty, w * 0.495, w * 0.108, 0, 0.1, Math.PI - 0.1); c.stroke();
  if (band) { c.strokeStyle = band; c.lineWidth = Math.max(1, w * 0.035); c.beginPath(); c.ellipse(x, ty + h * 0.22, w * 0.47, w * 0.1, 0, 0.25, Math.PI - 0.25); c.stroke(); }
  return { x: x, y: ty, rx: w * 0.44, ry: w * 0.085 };
}
function glass(c, x, y, w, h, fill, lev) {
  paper(c, poly([[x - w * 0.5, y - h], [x + w * 0.5, y - h], [x + w * 0.38, y], [x - w * 0.38, y]]), 'rgba(225,240,245,.55)', 0.6);
  fp(c, [[x - w * 0.45 + (1 - lev) * w * 0.0, y - h * lev], [x + w * 0.45, y - h * lev], [x + w * 0.36, y - w * 0.05], [x - w * 0.36, y - w * 0.05]], fill);
  ln(c, [[x - w * 0.3, y - h * 0.85], [x - w * 0.22, y - h * 0.15]], 'rgba(255,255,255,.6)', w * 0.06);
}
function leaf(c, x, y, l, w, a, col) {
  c.save(); c.translate(x, y); c.rotate(a); c.fillStyle = col; c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(l * 0.5, -w, l, 0); c.quadraticCurveTo(l * 0.5, w, 0, 0); c.fill();
  c.strokeStyle = 'rgba(255,255,255,.35)'; c.lineWidth = 0.6; c.beginPath(); c.moveTo(0, 0); c.lineTo(l * 0.9, 0); c.stroke(); c.restore();
}
function lime(c, x, y, r) { c.fillStyle = '#5c9e32'; c.beginPath(); c.arc(x, y, r, Math.PI, TAU); c.fill(); c.fillStyle = '#cfe68a'; c.beginPath(); c.arc(x, y, r * 0.78, Math.PI, TAU); c.fill(); c.strokeStyle = '#9fc85a'; c.lineWidth = 0.6; for (var i = 1; i < 4; i++) { c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(Math.PI + i * Math.PI / 4) * r * 0.75, y + Math.sin(Math.PI + i * Math.PI / 4) * r * 0.75); c.stroke(); } }
function chili(c, x, y, l, a) { c.save(); c.translate(x, y); c.rotate(a); c.fillStyle = '#d42a1e'; c.beginPath(); c.moveTo(0, -l * 0.1); c.quadraticCurveTo(l * 0.7, -l * 0.12, l, l * 0.12); c.quadraticCurveTo(l * 0.6, l * 0.1, 0, l * 0.1); c.fill(); c.fillStyle = '#3f8a3a'; c.fillRect(-l * 0.12, -l * 0.07, l * 0.14, l * 0.14); c.restore(); }
/* steam off a dish, each curl x = A·sin(ky − ωt), fading as it rises */
function steam(c, x, y, h, t, k, n, a) {
  n = n || 2; c.save(); c.strokeStyle = '#fff'; c.lineWidth = Math.max(1.1, h * 0.045); c.lineCap = 'round';
  for (var j = 0; j < n; j++) {
    var ph = (t / 2200 + j / n + k * 0.37) % 1, ox = x + (j - (n - 1) / 2) * h * 0.22;
    c.globalAlpha = (a || 0.6) * Math.sin(ph * Math.PI); c.beginPath();
    for (var i = 0; i <= 8; i++) { var f = i / 8, yy = y - (ph * 0.55 + f * 0.45) * h, xx = ox + Math.sin(f * 5 - t / 450 + j * 2 + k) * h * 0.07 * (0.4 + f); i ? c.lineTo(xx, yy) : c.moveTo(xx, yy); }
    c.stroke();
  }
  c.restore();
}
function glow(c, x, y, r, col, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, 'rgba(' + col + ',' + a + ')'); g.addColorStop(1, 'rgba(' + col + ',0)'); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); }
function flames(c, x, y, w, h, t, k) {
  for (var i = 0; i < 5; i++) {
    var fx = x + (i - 2) * w * 0.2, fh = h * (0.55 + 0.45 * Math.abs(Math.sin(t / 130 + i * 1.7 + k))), sw = Math.sin(t / 170 + i) * w * 0.05;
    fp(c, [[fx - w * 0.11, y], [fx + sw, y - fh], [fx + w * 0.11, y]], i % 2 ? '#ffb02e' : '#ff6a1e');
    fp(c, [[fx - w * 0.05, y], [fx + sw * 0.6, y - fh * 0.55], [fx + w * 0.05, y]], '#ffe27a');
  }
}
/* lai kham: gold flowers and scrolls stamped along a band */
function laiKham(c, x0, x1, y, s, col) {
  c.fillStyle = col || '#e8b84a'; c.strokeStyle = col || '#e8b84a'; c.lineWidth = Math.max(0.6, s * 0.12);
  for (var x = x0 + s; x < x1 - s * 0.5; x += s * 2.4) {
    for (var p = 0; p < 4; p++) { var a = p * Math.PI / 2 + 0.785; fe(c, x + Math.cos(a) * s * 0.42, y + Math.sin(a) * s * 0.42, s * 0.3, s * 0.16, col || '#e8b84a', a); }
    c.beginPath(); c.arc(x + s * 1.2, y, s * 0.35, Math.PI * 0.2, Math.PI * 1.6); c.stroke();
  }
}
/* the kalae: crossed gable horns, a little roof's crown */
function kalae(c, x, y, l, col) {
  ln(c, [[x, y], [x - l * 0.25, y - l * 0.7], [x - l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
  ln(c, [[x, y], [x + l * 0.25, y - l * 0.7], [x + l * 0.7, y - l]], col || '#e8b84a', Math.max(1.6, l * 0.12));
}
/* a small Lanna roof in two tiers, for a cart, a sign or a mill */
function lannaRoof(c, x, w, y, h, col, night) {
  paper(c, poly([[x - w * 0.55, y], [x - w * 0.3, y - h * 0.5], [x + w * 0.3, y - h * 0.5], [x + w * 0.55, y]]), col || (night ? '#6d2b20' : '#a8432f'), 1);
  paper(c, poly([[x - w * 0.36, y - h * 0.42], [x, y - h], [x + w * 0.36, y - h * 0.42]]), col || (night ? '#6d2b20' : '#a8432f'), 1.1);
  ln(c, [[x - w * 0.5, y - h * 0.04], [x + w * 0.5, y - h * 0.04]], '#e8b84a', Math.max(1, h * 0.06));
  kalae(c, x, y - h, h * 0.55);
}

/* ---------------------------------------------------------------- people at work
   arms by two-link inverse kinematics: shoulder S, hand target T, upper arm l₁, forearm l₂;
   the elbow from the law of cosines, cos α = (l₁² + d² − l₂²) / 2l₁d */
function ik(sh, T, h, dir) {
  var l1 = h * 0.17, l2 = h * 0.16, dx = T[0] - sh[0], dy = T[1] - sh[1], d = Math.max(Math.abs(l1 - l2) + 0.5, Math.min(Math.hypot(dx, dy), (l1 + l2) * 0.995));
  var phi = Math.atan2(dir * dx, dy), al = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))), up = phi - al;
  var ex = sh[0] + dir * Math.sin(up) * l1, ey = sh[1] + Math.cos(up) * l1, el = Math.atan2(dir * (T[0] - ex), T[1] - ey) - up;
  while (el > Math.PI) el -= TAU; while (el < -Math.PI) el += TAU;
  return [up, el];
}
function shoulder(x, y, h, seat, lean, dir) { var hip = [x, y - h * seat]; return [hip[0] + dir * Math.sin(lean) * h * 0.33, hip[1] - Math.cos(lean) * h * 0.33]; }
/* a figure whose hands go where they are sent: T1 the front hand, T2 the back */
function worker(S, x, h, base, d, T1, T2, y) {
  var dir = d.dir || 1, lean = base.lean || 0, seat = base.seat || 0.47; y = y == null ? S.deck : y;
  var sh = shoulder(x, y, h, seat, lean, dir), A1 = T1 ? ik(sh, T1, h, dir) : [0.15, 0.1], A2 = T2 ? ik(sh, T2, h, dir) : [-0.1, 0.1];
  var me = K.person(S.c, x, y, h, { lean: lean, seat: seat, legs: base.legs || [0.06, 0, -0.06, 0], arms: [A1[0], A1[1], A2[0], A2[1]], lift: base.lift }, d);
  me.A1 = A1; me.dir = dir; me.h = h; return me;
}
/* a cook's apron over the shirt, the front arm drawn back over it */
function apron(c, me, d, col) {
  var h = me.h, dir = me.dir, sh = me.sh, hip = me.hip, w = h * 0.075;
  fp(c, [[sh[0] - w * 0.6, sh[1] + h * 0.06], [sh[0] + w * 0.9, sh[1] + h * 0.06], [hip[0] + w * 1.3 + dir * h * 0.02, hip[1] + h * 0.2], [hip[0] - w * 1.1, hip[1] + h * 0.2]], col);
  c.strokeStyle = 'rgba(0,0,0,.15)'; c.lineWidth = 1; c.beginPath(); c.moveTo(hip[0] - w, hip[1] - h * 0.01); c.lineTo(hip[0] + w * 1.2, hip[1] - h * 0.01); c.stroke();
  var e = [sh[0] + dir * Math.sin(me.A1[0]) * h * 0.17, sh[1] + Math.cos(me.A1[0]) * h * 0.17], aw = Math.max(2, h * 0.075);
  ln(c, [sh, e], d.col, aw); ln(c, [e, me.hand[0]], d.skin || '#d9a27a', aw * 0.85);
}
function hat(c, me, kind, col) {
  var h = me.h, hd = me.head, x = hd[0], y = hd[1], r = h * 0.1, dir = me.dir;
  if (kind === 'toque') { fp(c, [[x - r * 0.9, y - r * 0.5], [x + r * 0.9, y - r * 0.5], [x + r, y - r * 1.5], [x - r, y - r * 1.5]], '#fbfbf7'); [-0.6, 0, 0.6].forEach(function (k) { fe(c, x + k * r, y - r * 1.75, r * 0.6, r * 0.5, '#ffffff'); }); }
  else if (kind === 'cap') { fp(c, [[x - r * 1.05, y - r * 0.35], [x + r * 1.05, y - r * 0.35], [x + r * 0.7, y - r * 1.15], [x - r * 0.7, y - r * 1.15]], col || '#ffffff'); ln(c, [[x - r * 1.05, y - r * 0.4], [x + r * 1.05, y - r * 0.4]], '#c0392b', r * 0.2); }
  else if (kind === 'band') { c.strokeStyle = col || '#fbfbf7'; c.lineWidth = r * 0.42; c.beginPath(); c.ellipse(x, y - r * 0.45, r * 1.02, r * 0.3, 0, 0, TAU); c.stroke(); fp(c, [[x - dir * r, y - r * 0.5], [x - dir * r * 1.7, y - r * 0.2], [x - dir * r * 1.5, y + r * 0.1]], col || '#fbfbf7'); fe(c, x + dir * r * 0.2, y - r * 0.55, r * 0.18, r * 0.12, '#d42a1e'); }
  else if (kind === 'cone') { fp(c, [[x - r * 2.3, y - r * 0.35], [x, y - r * 2.3], [x + r * 2.3, y - r * 0.35]], '#e3c47e'); c.strokeStyle = 'rgba(120,80,30,.45)'; c.lineWidth = 0.7; for (var i = 1; i < 4; i++) { c.beginPath(); c.moveTo(x - r * 2.3 * i / 4, y - r * 0.35 - r * 1.95 * (1 - i / 4)); c.lineTo(x + r * 2.3 * i / 4, y - r * 0.35 - r * 1.95 * (1 - i / 4)); c.stroke(); } }
  else if (kind === 'kopiah') { c.fillStyle = col || '#fbfbf7'; c.beginPath(); c.ellipse(x, y - r * 0.55, r * 1.02, r * 0.62, 0, Math.PI, TAU); c.fill(); }
  else if (kind === 'kerchief') { c.fillStyle = col || '#c0392b'; c.beginPath(); c.arc(x, y - r * 0.15, r * 1.08, Math.PI * 1.02, Math.PI * 1.98); c.closePath(); c.fill(); fp(c, [[x - dir * r, y - r * 0.3], [x - dir * r * 1.6, y + r * 0.2], [x - dir * r * 1.2, y + r * 0.3]], col || '#c0392b'); sprinkle(c, x, y - r * 0.6, r * 0.7, r * 0.3, 5, r * 0.1, ['#fff']); }
}
/* what a diner holds: a morsel on chopsticks, fork or spoon, or the food itself; lift
   runs 0 at the dish to 1 at the mouth */
function held(c, p, dir, h, item, lift, t, k, C) {
  var u = h * 0.16, a, tip;
  if (item === 'chop' || item === 'sushi') {
    a = lerp(0.9, -0.35, lift); tip = [p[0] + dir * Math.cos(a) * u * 1.3, p[1] + Math.sin(a) * u * 1.3];
    ln(c, [p, tip], '#c8a060', u * 0.08); ln(c, [[p[0], p[1] + u * 0.08], [tip[0], tip[1] + u * 0.06]], '#b08a50', u * 0.08);
    if (item === 'sushi') { fe(c, tip[0], tip[1] + u * 0.08, u * 0.18, u * 0.1, '#f6f2e8'); fe(c, tip[0], tip[1] + u * 0.01, u * 0.18, u * 0.06, '#f08a5d'); }
    else if (lift > 0.05) { var nl = u * (0.25 + 0.9 * lift); for (var i = -1; i <= 1; i++) { c.strokeStyle = C.noodle || '#f2d58a'; c.lineWidth = Math.max(0.8, u * 0.05); c.beginPath(); for (var j = 0; j <= 6; j++) { var f = j / 6; c.lineTo(tip[0] + i * u * 0.05 + Math.sin(f * 7 + t / 200 + i) * u * 0.04, tip[1] + f * nl); } c.stroke(); } }
  } else if (item === 'fork' || item === 'spoon') {
    a = lerp(1.0, -0.6, lift); tip = [p[0] + dir * Math.cos(a) * u, p[1] + Math.sin(a) * u];
    ln(c, [p, tip], '#c9ccd2', u * 0.1);
    if (item === 'spoon') fe(c, tip[0], tip[1], u * 0.16, u * 0.09, '#c9ccd2', dir * a);
    else { var nx = -Math.sin(a), ny = Math.cos(a) * dir; for (var q = -1; q <= 1; q++) ln(c, [[tip[0] + nx * q * u * 0.06, tip[1] + ny * q * u * 0.06], [tip[0] + dir * Math.cos(a) * u * 0.2 + nx * q * u * 0.06, tip[1] + Math.sin(a) * u * 0.2 + ny * q * u * 0.06]], '#c9ccd2', u * 0.05); }
    fe(c, tip[0] + dir * u * 0.05, tip[1] - u * 0.06, u * 0.1, u * 0.08, C.morsel || '#c8743a');
  } else if (item === 'ball') { fe(c, p[0] + dir * u * 0.1, p[1] - u * 0.05, u * 0.2, u * 0.17, '#f7f3e8'); fe(c, p[0] + dir * u * 0.16, p[1] - u * 0.12, u * 0.06, u * 0.05, '#fffdf6'); }
  else if (item === 'falafel') { fe(c, p[0] + dir * u * 0.1, p[1] - u * 0.05, u * 0.2, u * 0.18, '#6b3f1c'); }
  else if (item === 'leg') { ln(c, [p, [p[0] + dir * u * 0.15, p[1] - u * 0.35]], '#f2ead8', u * 0.12); fe(c, p[0] + dir * u * 0.25, p[1] - u * 0.6, u * 0.24, u * 0.34, '#b8681e', dir * 0.4); sprinkle(c, p[0] + dir * u * 0.25, p[1] - u * 0.6, u * 0.18, u * 0.26, 6, u * 0.05, ['#e0a040', '#8a4a12']); }
  else if (item === 'cup') { var ca = lift * 0.5 * dir; c.save(); c.translate(p[0] + dir * u * 0.1, p[1] - u * 0.1); c.rotate(-ca); fp(c, [[-u * 0.2, -u * 0.25], [u * 0.2, -u * 0.25], [u * 0.15, u * 0.15], [-u * 0.15, u * 0.15]], C.cup || '#f4f1ea'); fe(c, 0, -u * 0.25, u * 0.2, u * 0.05, C.drink || '#8a5a2a'); c.restore(); }
  else if (item === 'wrap' || item === 'banh') {
    c.save(); c.translate(p[0] + dir * u * 0.1, p[1]); c.rotate(dir * (item === 'banh' ? -0.4 - lift * 0.6 : 0.5 - lift * 0.9));
    if (item === 'banh') { fe(c, 0, -u * 0.05, u * 0.6, u * 0.14, '#d99a4e'); fe(c, 0, -u * 0.1, u * 0.5, u * 0.05, '#e8803a'); fe(c, u * 0.1, -u * 0.13, u * 0.3, u * 0.03, '#5aa83a'); }
    else { fp(c, [[-u * 0.18, -u * 0.5], [u * 0.18, -u * 0.5], [0, u * 0.3]], '#efe6d2'); fe(c, 0, -u * 0.5, u * 0.18, u * 0.08, '#5aa83a'); fe(c, u * 0.05, -u * 0.55, u * 0.08, u * 0.07, '#6b3f1c'); fp(c, [[-u * 0.18, -u * 0.25], [u * 0.18, -u * 0.25], [0, u * 0.3]], '#e8e2d2'); }
    c.restore();
  } else if (item === 'fish') {   /* herring held up by the tail */
    var fx = p[0] + dir * u * 0.05, fy = p[1] + u * 0.05, sway = Math.sin(t / 500 + k) * 0.1;
    c.save(); c.translate(fx, fy); c.rotate(sway); fp(c, [[-u * 0.12, 0], [u * 0.12, 0], [0, u * 0.12]], '#7f8c99'); fe(c, 0, u * 0.5, u * 0.11, u * 0.42, '#a8b4c0'); fe(c, u * 0.03, u * 0.5, u * 0.04, u * 0.38, '#d8dee6'); c.restore();
  } else if (item === 'roti') { fp(c, [[p[0], p[1] - u * 0.2], [p[0] + dir * u * 0.45, p[1] - u * 0.1], [p[0] + dir * u * 0.1, p[1] + u * 0.15]], '#e3b062'); }
  else if (item === 'skewer') { a = lerp(0.6, -0.9, lift); tip = [p[0] + dir * Math.cos(a) * u * 1.3, p[1] + Math.sin(a) * u * 1.3]; ln(c, [p, tip], '#d8b878', u * 0.06); for (var s = 0; s < 3; s++) { var f2 = 0.45 + s * 0.2; fe(c, lerp(p[0], tip[0], f2), lerp(p[1], tip[1], f2), u * 0.11, u * 0.09, '#c4782a'); } }
  else if (item === 'bun') { fe(c, p[0] + dir * u * 0.1, p[1] - u * 0.08, u * 0.24, u * 0.18, '#c98a4a'); ln(c, spiral(p[0] + dir * u * 0.1, p[1] - u * 0.08, u * 0.18, 2, 0.75), '#7a4a1e', u * 0.04); }
  else if (item === 'stroop') { fe(c, p[0] + dir * u * 0.12, p[1] - u * 0.08, u * 0.3, u * 0.08, '#c98a3a'); }
  else if (item === 'burger') { fe(c, p[0] + dir * u * 0.15, p[1] - u * 0.18, u * 0.28, u * 0.14, '#e0a050'); fe(c, p[0] + dir * u * 0.15, p[1] - u * 0.06, u * 0.3, u * 0.07, '#5a2e1a'); fe(c, p[0] + dir * u * 0.15, p[1] + u * 0.03, u * 0.27, u * 0.06, '#d99a4e'); }
}

/* ---------------------------------------------------------------- the dishes
   each [still, moving]: the still part is cut once into the front layer; the moving part
   (steam, lids, drips, forks) is drawn each frame. (c, x, y, s): centre, table line, width */
function noop() {}
var DISH = {
  /* khao soi in a rooster bowl: the curry, its nest of crisp noodles, chilli oil */
  khaoSoi: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.92, '#f6f2ea', '#dc8a2c', '#3a6db0');
    var ry = y - s * 0.17; fe(c, x - s * 0.06, ry, s * 0.06, s * 0.04, '#c8322a'); ln(c, [[x - s * 0.11, ry - s * 0.01], [x - s * 0.17, ry - s * 0.07]], '#1f1f1f', s * 0.025); ln(c, [[x - s * 0.02, ry - s * 0.03], [x, ry - s * 0.08]], '#c8322a', s * 0.02);
    leaf(c, x + s * 0.06, ry + s * 0.02, s * 0.16, s * 0.04, -0.3, '#3f8a3a');
    sprinkle(c, b.x - s * 0.1, b.y, b.rx * 0.5, b.ry * 0.6, 7, s * 0.02, ['#b0301e', '#f2a23a']);
    paper(c, E(x + s * 0.05, b.y - s * 0.04, s * 0.2, s * 0.08), '#efbd55', 0.5);
    c.strokeStyle = '#c98a26'; c.lineWidth = Math.max(0.7, s * 0.014);
    for (var i = 0; i < 10; i++) { c.beginPath(); c.ellipse(x + s * 0.05 + (RR() - 0.5) * s * 0.28, b.y - s * 0.04 - RR() * s * 0.08, s * 0.06, s * 0.025, RR() * 3, 0, TAU * 0.8); c.stroke(); }
    lime(c, x - s * 0.3, b.y + s * 0.01, s * 0.07);
  }, function (c, x, y, s, S, k) { steam(c, x - s * 0.1, y - s * 0.45, s * 0.75, S.t, k, 2); }],
  /* sai oua coiled on a banana leaf, r = aθ */
  saiOua: [function (c, x, y, s) {
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.5, y - s * 0.04); q.quadraticCurveTo(x, y - s * 0.24, x + s * 0.5, y - s * 0.06); q.quadraticCurveTo(x, y + s * 0.04, x - s * 0.5, y - s * 0.04); }, '#4f9a3c', 0.5);
    ln(c, [[x - s * 0.45, y - s * 0.05], [x + s * 0.45, y - s * 0.07]], '#7cc062', s * 0.012);
    var pts = spiral(x, y - s * 0.1, s * 0.32, 2.6, 0.32, 0.4);
    ln(c, pts.map(function (p) { return [p[0], p[1] + s * 0.012]; }), '#4a1e10', s * 0.11);
    ln(c, pts, '#9a3e22', s * 0.09); ln(c, pts.map(function (p) { return [p[0], p[1] - s * 0.018]; }), '#c4623a', s * 0.03);
    for (var i = 4; i < pts.length; i += 5) fe(c, pts[i][0], pts[i][1], s * 0.012, s * 0.009, i % 2 ? '#4f8a2a' : '#e0b040');
  }, noop],
  /* nam prik ong with cucumber, long beans, cabbage and khaep mu */
  namPrik: [function (c, x, y, s) {
    var py = plate(c, x, y, s, '#e9e2d0');
    leaf(c, x + s * 0.05, py, s * 0.4, s * 0.05, -0.15, '#3f8a3a'); leaf(c, x + s * 0.05, py + s * 0.01, s * 0.38, s * 0.05, 0.08, '#4f9a3c');
    [[-0.3, 0], [-0.22, 0.02], [0.26, -0.01], [0.33, 0.01]].forEach(function (p) { fe(c, x + p[0] * s, py + p[1] * s - s * 0.03, s * 0.06, s * 0.03, '#d6eab0'); fe(c, x + p[0] * s, py + p[1] * s - s * 0.03, s * 0.045, s * 0.02, '#eef6dc'); });
    [[0.18, -0.05], [0.27, -0.08], [-0.16, -0.06]].forEach(function (p) { fe(c, x + p[0] * s, py + p[1] * s, s * 0.07, s * 0.05, '#f2e2b8'); fe(c, x + p[0] * s + s * 0.02, py + p[1] * s - s * 0.01, s * 0.03, s * 0.02, '#fff6dc'); });
    var b = bowl(c, x, py + s * 0.01, s * 0.42, '#7a4a2a', '#c8452a');
    sprinkle(c, b.x, b.y, b.rx * 0.8, b.ry * 0.7, 9, s * 0.012, ['#8a2a14', '#e8703a', '#f2e6c9']);
  }, noop],
  /* sticky rice in a kratip; its lid lifts now and then */
  kratip: [function (c, x, y, s) { kratipBody(c, x, y, s); }, function (c, x, y, s, S, k) { kratipLid(c, x, y, s, S.t, k); }],
  /* a burger: bun, lettuce, tomato, cheese with its drips, patty */
  burger: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95), w = s * 0.62;
    paper(c, E(x, py - s * 0.05, w * 0.5, s * 0.06), '#d99a4e', 0.6);
    paper(c, function (q) { q.beginPath(); q.ellipse(x, py - s * 0.12, w * 0.54, s * 0.07, 0, 0, TAU); }, '#5a2e1a', 0.6);
    sprinkle(c, x, py - s * 0.12, w * 0.45, s * 0.04, 10, s * 0.012, ['#3a1a0a', '#7a4a2a']);
    fp(c, [[x - w * 0.55, py - s * 0.18], [x + w * 0.55, py - s * 0.18], [x + w * 0.4, py - s * 0.08], [x + w * 0.3, py - s * 0.16], [x + w * 0.1, py - s * 0.06], [x - w * 0.05, py - s * 0.16], [x - w * 0.35, py - s * 0.09], [x - w * 0.42, py - s * 0.16]], '#f4c430');
    fe(c, x, py - s * 0.2, w * 0.5, s * 0.03, '#d6402e');
    c.fillStyle = '#5aa83a'; c.beginPath(); c.moveTo(x - w * 0.58, py - s * 0.22); for (var i = 0; i <= 12; i++) c.lineTo(x - w * 0.58 + i * w * 1.16 / 12, py - s * 0.22 + (i % 2 ? s * 0.035 : -s * 0.005)); c.lineTo(x + w * 0.5, py - s * 0.26); c.lineTo(x - w * 0.5, py - s * 0.26); c.fill();
    paper(c, function (q) { q.beginPath(); q.moveTo(x - w * 0.52, py - s * 0.24); q.bezierCurveTo(x - w * 0.5, py - s * 0.52, x + w * 0.5, py - s * 0.52, x + w * 0.52, py - s * 0.24); q.closePath(); }, '#e2a24e', 0.8);
    fe(c, x - w * 0.15, py - s * 0.4, w * 0.18, s * 0.04, 'rgba(255,240,200,.35)');
    for (i = 0; i < 9; i++) fe(c, x + (RR() - 0.5) * w * 0.7, py - s * (0.3 + RR() * 0.12), s * 0.014, s * 0.008, '#fbf1d8', RR());
  }, noop],
  /* fries in a striped carton */
  fries: [function (c, x, y, s) {
    for (var i = 0; i < 9; i++) { var fx = x + (i - 4) * s * 0.045, a = (i - 4) * 0.06; c.save(); c.translate(fx, y - s * 0.35); c.rotate(a); paper(c, rect(-s * 0.022, -s * 0.2 - (i % 3) * s * 0.04, s * 0.044, s * 0.3), i % 2 ? '#f4c84a' : '#eab53a', 0.3); c.restore(); }
    paper(c, poly([[x - s * 0.22, y - s * 0.42], [x + s * 0.22, y - s * 0.42], [x + s * 0.16, y], [x - s * 0.16, y]]), '#d1342b', 0.8);
    for (i = 0; i < 4; i++) fp(c, [[x - s * 0.2 + i * s * 0.12, y - s * 0.42], [x - s * 0.15 + i * s * 0.12, y - s * 0.42], [x - s * 0.12 + i * s * 0.09, y], [x - s * 0.15 + i * s * 0.09, y]], 'rgba(255,255,255,.75)');
  }, noop],
  /* a milkshake: cream, a cherry, a striped straw */
  shake: [function (c, x, y, s) {
    var w = s * 0.3, h = s * 0.62;
    ln(c, [[x + w * 0.1, y - h * 0.6], [x + w * 0.45, y - h * 1.35]], '#ffffff', s * 0.04);
    for (var i = 0; i < 5; i++) { var f = i / 5; ln(c, [[lerp(x + w * 0.1, x + w * 0.45, f), lerp(y - h * 0.6, y - h * 1.35, f)], [lerp(x + w * 0.1, x + w * 0.45, f + 0.1), lerp(y - h * 0.6, y - h * 1.35, f + 0.1)]], '#e04a5a', s * 0.04); }
    glass(c, x, y, w, h, '#f4a6c0', 0.92);
    [[-0.3, 0], [0.3, 0], [0, -0.05], [-0.12, -0.12], [0.12, -0.12], [0, -0.2]].forEach(function (p) { paper(c, E(x + p[0] * w, y - h - s * 0.02 + p[1] * s, w * 0.28, s * 0.06), '#fffaf2', 0.3); });
    paper(c, E(x, y - h - s * 0.27, s * 0.045, s * 0.045), '#c8102e', 0.4); ln(c, [[x, y - h - s * 0.3], [x + s * 0.05, y - h - s * 0.4]], '#3a6a2a', s * 0.012);
  }, noop],
  /* pancakes, butter, syrup that drips, y = ½gt² */
  pancakes: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95);
    for (var i = 0; i < 4; i++) { var yy = py - s * 0.04 - i * s * 0.07; paper(c, E(x, yy, s * 0.32, s * 0.055), '#c98a42', 0.4); fe(c, x, yy - s * 0.015, s * 0.3, s * 0.04, '#e6b066'); }
    var top = py - s * 0.04 - 3 * s * 0.07 - s * 0.02;
    fe(c, x, top, s * 0.26, s * 0.045, '#8a4a12');
    [[-0.2, 0.12], [0.05, 0.2], [0.22, 0.09]].forEach(function (p) { fp(c, [[x + p[0] * s - s * 0.03, top], [x + p[0] * s + s * 0.03, top], [x + p[0] * s + s * 0.015, top + p[1] * s], [x + p[0] * s - s * 0.015, top + p[1] * s]], '#8a4a12'); fe(c, x + p[0] * s, top + p[1] * s, s * 0.018, s * 0.022, '#8a4a12'); });
    paper(c, rect(x - s * 0.06, top - s * 0.06, s * 0.12, s * 0.05), '#f8e08a', 0.3);
  }, function (c, x, y, s, S, k) {
    var T = 1.6, u = ((S.t / 1000) / T + k * 0.3) % 1, top = y - s * 0.07 - s * 0.04 - 3 * s * 0.07 + s * 0.2;
    if (u < 0.5) fe(c, x + s * 0.05, top + s * 0.02 + u * s * 0.05, s * 0.018, s * 0.02 + u * s * 0.02, '#8a4a12');
    else { var g = (u - 0.5) * 2; fe(c, x + s * 0.05, top + s * 0.05 + g * g * s * 0.12, s * 0.016, s * 0.024, '#8a4a12'); }
  }],
  /* apple pie: a slice with its lattice */
  pie: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.9);
    paper(c, poly([[x - s * 0.28, py - s * 0.04], [x + s * 0.22, py - s * 0.02], [x + s * 0.24, py - s * 0.14], [x - s * 0.2, py - s * 0.2]]), '#e8c070', 0.6);
    fp(c, [[x - s * 0.26, py - s * 0.06], [x + s * 0.2, py - s * 0.04], [x + s * 0.21, py - s * 0.1], [x - s * 0.22, py - s * 0.14]], '#e8a64a');
    sprinkle(c, x, py - s * 0.09, s * 0.18, s * 0.025, 6, s * 0.02, ['#f6dca0']);
    paper(c, poly([[x - s * 0.2, py - s * 0.2], [x + s * 0.24, py - s * 0.14], [x + s * 0.18, py - s * 0.24], [x - s * 0.14, py - s * 0.28]]), '#d9a650', 0.4);
    for (var i = 0; i < 4; i++) ln(c, [[x - s * 0.16 + i * s * 0.1, py - s * 0.28 + i * s * 0.01], [x - s * 0.18 + i * s * 0.1 + s * 0.06, py - s * 0.19 + i * s * 0.015]], '#f2d08a', s * 0.03);
    fe(c, x + s * 0.24, py - s * 0.22, s * 0.08, s * 0.06, '#fffaf0');
  }, noop],
  /* stroopwafels, one on a cup of tea to soften */
  stroop: [function (c, x, y, s) {
    var py = plate(c, x - s * 0.15, y, s * 0.6);
    for (var i = 0; i < 3; i++) { var yy = py - s * 0.03 - i * s * 0.05; paper(c, E(x - s * 0.15, yy, s * 0.2, s * 0.045), '#c98a3a', 0.4); fe(c, x - s * 0.15, yy - s * 0.008, s * 0.2, s * 0.008, '#8a4a12'); }
    waffleTop(c, x - s * 0.15, py - s * 0.03 - 2 * s * 0.05 - s * 0.012, s * 0.19, s * 0.04);
    var cx = x + s * 0.22; paper(c, poly([[cx - s * 0.12, y - s * 0.26], [cx + s * 0.12, y - s * 0.26], [cx + s * 0.09, y], [cx - s * 0.09, y]]), '#f4f6fa', 0.6);
    for (i = 0; i < 3; i++) fe(c, cx - s * 0.05 + i * s * 0.05, y - s * 0.12, s * 0.018, s * 0.028, '#2f5fa8');
    ln(c, [[cx + s * 0.12, y - s * 0.22], [cx + s * 0.18, y - s * 0.17], [cx + s * 0.11, y - s * 0.09]], '#f4f6fa', s * 0.03);
    paper(c, E(cx, y - s * 0.28, s * 0.15, s * 0.035), '#c98a3a', 0.4); waffleTop(c, cx, y - s * 0.292, s * 0.14, s * 0.03);
  }, function (c, x, y, s, S, k) { steam(c, x + s * 0.22, y - s * 0.3, s * 0.5, S.t, k, 2, 0.45); }],
  /* poffertjes under powdered sugar, with a butter pat */
  poffertjes: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95);
    for (var i = 0; i < 9; i++) { var px = x + ((i % 5) - 2) * s * 0.11 + (i > 4 ? s * 0.055 : 0), yy = py - s * 0.03 - (i > 4 ? s * 0.05 : 0); paper(c, E(px, yy, s * 0.06, s * 0.04), '#c4823a', 0.3); fe(c, px, yy - s * 0.015, s * 0.045, s * 0.02, '#e0a860'); fe(c, px - s * 0.01, yy - s * 0.03, s * 0.035, s * 0.012, 'rgba(255,255,255,.85)'); }
    paper(c, rect(x - s * 0.05, py - s * 0.15, s * 0.1, s * 0.05), '#f8e08a', 0.3);
    sprinkle(c, x, py - s * 0.08, s * 0.28, s * 0.05, 14, s * 0.01, ['#ffffff']);
  }, noop],
  /* a herring on a paper boat with onions and a flag pick */
  herring: [function (c, x, y, s) {
    paper(c, poly([[x - s * 0.36, y - s * 0.1], [x + s * 0.36, y - s * 0.1], [x + s * 0.3, y], [x - s * 0.3, y]]), '#f6f2ea', 0.5);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.3, y - s * 0.12); q.quadraticCurveTo(x, y - s * 0.22, x + s * 0.24, y - s * 0.12); q.lineTo(x + s * 0.34, y - s * 0.19); q.lineTo(x + s * 0.32, y - s * 0.08); q.lineTo(x + s * 0.24, y - s * 0.11); q.quadraticCurveTo(x, y - s * 0.06, x - s * 0.3, y - s * 0.12); }, '#9aa6b4', 0.4);
    ln(c, [[x - s * 0.25, y - s * 0.13], [x + s * 0.2, y - s * 0.14]], '#d8dee6', s * 0.02); ln(c, [[x - s * 0.22, y - s * 0.16], [x + s * 0.15, y - s * 0.17]], '#5a6a7f', s * 0.015);
    sprinkle(c, x - s * 0.05, y - s * 0.08, s * 0.25, s * 0.03, 14, s * 0.018, ['#ffffff', '#f2eedd']);
    ln(c, [[x + s * 0.05, y - s * 0.12], [x + s * 0.05, y - s * 0.4]], '#d8b878', s * 0.015);
    fp(c, [[x + s * 0.05, y - s * 0.4], [x + s * 0.2, y - s * 0.4], [x + s * 0.2, y - s * 0.367], [x + s * 0.05, y - s * 0.367]], '#ae1c28');
    fp(c, [[x + s * 0.05, y - s * 0.367], [x + s * 0.2, y - s * 0.367], [x + s * 0.2, y - s * 0.334], [x + s * 0.05, y - s * 0.334]], '#ffffff');
    fp(c, [[x + s * 0.05, y - s * 0.334], [x + s * 0.2, y - s * 0.334], [x + s * 0.2, y - s * 0.3], [x + s * 0.05, y - s * 0.3]], '#21468b');
  }, noop],
  /* a Gouda wheel in red wax, a wedge cut out and lying by it */
  gouda: [function (c, x, y, s) {
    var w = s * 0.5, h = s * 0.2, cx = x - s * 0.08;
    paper(c, function (q) { q.beginPath(); q.ellipse(cx, y - h * 0.5, w * 0.5, h * 0.6, 0, 0, TAU); }, '#c0262a', 0.8);
    fe(c, cx, y - h * 0.85, w * 0.46, h * 0.28, '#d8343a');
    fp(c, [[cx, y - h * 0.85], [cx + w * 0.42, y - h * 0.95], [cx + w * 0.48, y - h * 0.4], [cx + w * 0.1, y - h * 0.3]], '#f2c64a');
    ln(c, [[cx, y - h * 0.85], [cx + w * 0.1, y - h * 0.3]], '#e0a830', s * 0.01);
    var wx = x + s * 0.3; paper(c, poly([[wx - s * 0.13, y - s * 0.02], [wx + s * 0.13, y - s * 0.02], [wx + s * 0.02, y - s * 0.16]]), '#f2c64a', 0.4); ln(c, [[wx - s * 0.13, y - s * 0.02], [wx + s * 0.13, y - s * 0.02]], '#c0262a', s * 0.035);
    sprinkle(c, wx, y - s * 0.06, s * 0.05, s * 0.03, 3, s * 0.008, ['#e0a830']);
  }, noop],
  /* fondue: the caquelon over its flame; forks dip bread and draw a string of cheese
     that hangs as a catenary, y = a·cosh(x/a) */
  fondue: [function (c, x, y, s) {
    ln(c, [[x - s * 0.22, y], [x - s * 0.16, y - s * 0.18]], '#3a3a3a', s * 0.03); ln(c, [[x + s * 0.22, y], [x + s * 0.16, y - s * 0.18]], '#3a3a3a', s * 0.03);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.3, y - s * 0.4); q.bezierCurveTo(x - s * 0.3, y - s * 0.15, x - s * 0.18, y - s * 0.12, x, y - s * 0.12); q.bezierCurveTo(x + s * 0.18, y - s * 0.12, x + s * 0.3, y - s * 0.15, x + s * 0.3, y - s * 0.4); q.closePath(); }, '#b8402a', 0.8);
    fe(c, x, y - s * 0.4, s * 0.3, s * 0.06, '#f2d46a'); ln(c, [[x + s * 0.3, y - s * 0.35], [x + s * 0.48, y - s * 0.4]], '#7a2a1a', s * 0.04);
    c.strokeStyle = '#f2e6c9'; c.lineWidth = s * 0.02; c.beginPath(); c.ellipse(x, y - s * 0.26, s * 0.25, s * 0.05, 0, 0.3, Math.PI - 0.3); c.stroke();
  }, function (c, x, y, s, S, k) {
    flames(c, x, y - s * 0.03, s * 0.2, s * 0.09, S.t, k);
    var sy = y - s * 0.4; fe(c, x + Math.sin(S.t / 300) * s * 0.1, sy, s * 0.03, s * 0.012, '#f8e48a');
    [-1, 1].forEach(function (sd, j) {
      var u = ((S.t / 1000) / 3.4 + j * 0.5 + k * 0.2) % 1, dip = u < 0.3 ? 1 - ease(u / 0.3) : u < 0.7 ? 0 : ease((u - 0.7) / 0.3);
      var bx = x + sd * s * 0.1, by = sy + s * 0.02 - (1 - dip) * s * 0.32, hx = x + sd * s * 0.6, hy = sy - s * 0.55;
      ln(c, [[bx, by], [hx, hy]], '#9aa0a8', s * 0.02); fe(c, hx, hy, s * 0.03, s * 0.03, sd > 0 ? '#2f6db0' : '#c0392b');
      if (dip < 0.95) {   /* the cheese string: a catenary between bread and pot */
        var x0 = bx, y0 = by + s * 0.03, x1 = bx + sd * s * 0.02, y1 = sy, sag = s * 0.03;
        c.strokeStyle = '#f2d46a'; c.lineWidth = Math.max(0.8, s * 0.02 * (1 - dip)); c.beginPath(); c.moveTo(x0, y0);
        for (var i = 1; i <= 8; i++) { var f = i / 8, cy = lerp(y0, y1, f) + sag * (Math.cosh((f - 0.5) * 2) - Math.cosh(1)) * -0.6; c.lineTo(lerp(x0, x1, f) + Math.sin(f * 3) * sd * s * 0.02, cy); } c.stroke();
      }
      fe(c, bx, by + s * 0.03, s * 0.045, s * 0.04, dip < 0.95 ? '#f2d46a' : '#e8c27a'); fe(c, bx, by + s * 0.02, s * 0.035, s * 0.03, '#e6b56a');
    });
  }],
  /* rösti in its pan */
  rosti: [function (c, x, y, s) {
    paper(c, E(x, y - s * 0.06, s * 0.36, s * 0.09), '#2c2c2e', 0.7); ln(c, [[x + s * 0.34, y - s * 0.07], [x + s * 0.55, y - s * 0.12]], '#2c2c2e', s * 0.05);
    fe(c, x, y - s * 0.09, s * 0.31, s * 0.07, '#d9952e'); fe(c, x, y - s * 0.1, s * 0.27, s * 0.055, '#eab04a');
    c.strokeStyle = '#b8731e'; c.lineWidth = 0.7; for (var i = 0; i < 18; i++) { var a = RR() * TAU, r = RR() * 0.8; c.beginPath(); c.moveTo(x + Math.cos(a) * s * 0.25 * r, y - s * 0.1 + Math.sin(a) * s * 0.05 * r); c.lineTo(x + Math.cos(a) * s * 0.25 * r + s * 0.04, y - s * 0.1 + Math.sin(a) * s * 0.05 * r + s * 0.004); c.stroke(); }
    leaf(c, x - s * 0.05, y - s * 0.13, s * 0.06, s * 0.02, -0.4, '#3f8a3a');
  }, noop],
  /* a wedge of Emmental, its holes cut through */
  emmental: [function (c, x, y, s) {
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.32, y); q.lineTo(x + s * 0.32, y); q.lineTo(x + s * 0.3, y - s * 0.22); q.lineTo(x - s * 0.32, y - s * 0.08); q.closePath();
      [[-0.15, -0.05, 0.04], [0.05, -0.08, 0.05], [0.2, -0.04, 0.035], [0.22, -0.14, 0.03], [-0.02, -0.02, 0.025]].forEach(function (h) { q.moveTo(x + (h[0] + h[2]) * s, y + h[1] * s); q.ellipse(x + h[0] * s, y + h[1] * s, h[2] * s, h[2] * s * 0.8, 0, 0, TAU); }); }, '#f4d670', 0.7);
    fp(c, [[x - s * 0.32, y - s * 0.08], [x + s * 0.3, y - s * 0.22], [x + s * 0.24, y - s * 0.26], [x - s * 0.34, y - s * 0.11]], '#f8e494');
  }, noop],
  /* chocolate in gold foil, squares broken off */
  choc: [function (c, x, y, s) {
    paper(c, poly([[x - s * 0.3, y - s * 0.02], [x + s * 0.28, y - s * 0.06], [x + s * 0.3, y - s * 0.16], [x - s * 0.28, y - s * 0.12]]), '#5a2e18', 0.6);
    for (var i = 0; i < 5; i++) ln(c, [[x - s * 0.28 + i * s * 0.115, y - s * 0.03 - i * s * 0.008], [x - s * 0.26 + i * s * 0.115, y - s * 0.13 - i * s * 0.008]], '#3a1a0a', s * 0.012);
    paper(c, poly([[x + s * 0.02, y - s * 0.05], [x + s * 0.3, y - s * 0.08], [x + s * 0.32, y - s * 0.17], [x + s * 0.04, y - s * 0.14]]), '#e8b84a', 0.4);
    ln(c, [[x + s * 0.06, y - s * 0.07], [x + s * 0.28, y - s * 0.12]], '#c0262a', s * 0.03);
    paper(c, rect(x - s * 0.42, y - s * 0.07, s * 0.08, s * 0.06), '#5a2e18', 0.3);
  }, noop],
  /* köttbullar with mash, gravy and lingonberries */
  meatballs: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, function (q) { q.beginPath(); q.ellipse(x - s * 0.18, py - s * 0.05, s * 0.16, s * 0.08, 0, 0, TAU); }, '#f4ead0', 0.3);
    c.strokeStyle = '#e0d2a8'; c.lineWidth = 0.8; c.beginPath(); c.ellipse(x - s * 0.18, py - s * 0.07, s * 0.08, s * 0.03, 0, 0, 5); c.stroke();
    fe(c, x + s * 0.08, py - s * 0.02, s * 0.2, s * 0.045, '#8a5228');
    [[0, 0], [0.12, 0.01], [0.24, -0.01], [0.06, -0.06], [0.18, -0.06]].forEach(function (p) { paper(c, E(x + p[0] * s, py - s * 0.06 + p[1] * s, s * 0.06, s * 0.05), '#7a4220', 0.3); fe(c, x + p[0] * s - s * 0.02, py - s * 0.08 + p[1] * s, s * 0.02, s * 0.014, '#b06a3a'); });
    sprinkle(c, x + s * 0.3, py - s * 0.05, s * 0.06, s * 0.03, 9, s * 0.02, ['#c8102e', '#e0283c', '#a00c22']);
    leaf(c, x - s * 0.24, py - s * 0.11, s * 0.06, s * 0.02, -0.5, '#3f8a3a');
  }, function (c, x, y, s, S, k) { steam(c, x - s * 0.15, y - s * 0.15, s * 0.45, S.t, k, 2, 0.45); }],
  /* kanelbullar: each a spiral, r = aθ, under pearl sugar */
  bulle: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95);
    [[-0.17, 0], [0.17, 0], [0, -0.07]].forEach(function (p, i) {
      var bx = x + p[0] * s, by = py - s * 0.08 + p[1] * s;
      paper(c, E(bx, by, s * 0.15, s * 0.09), '#c27a38', 0.5);
      ln(c, spiral(bx, by - s * 0.01, s * 0.13, 2.4, 0.55, i), '#7a3e14', s * 0.022);
      sprinkle(c, bx, by - s * 0.02, s * 0.1, s * 0.05, 6, s * 0.012, ['#ffffff']);
    });
  }, noop],
  /* prinsesstårta: the green dome, its pink rose */
  princess: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.3, py - s * 0.03); q.bezierCurveTo(x - s * 0.3, py - s * 0.48, x + s * 0.3, py - s * 0.48, x + s * 0.3, py - s * 0.03); q.closePath(); }, '#a6d08a', 0.8);
    fe(c, x - s * 0.1, py - s * 0.28, s * 0.08, s * 0.05, 'rgba(255,255,255,.35)');
    sprinkle(c, x, py - s * 0.28, s * 0.22, s * 0.08, 14, s * 0.01, ['#ffffff']);
    var rx = x, ry = py - s * 0.38; fe(c, rx, ry, s * 0.06, s * 0.045, '#f28aa8');
    c.strokeStyle = '#c8507a'; c.lineWidth = 0.8; c.beginPath(); for (var i = 0; i <= 30; i++) { var th = i / 30 * TAU * 2, r = s * 0.05 * th / (TAU * 2); i ? c.lineTo(rx + Math.cos(th) * r, ry + Math.sin(th) * r * 0.7) : c.moveTo(rx, ry); } c.stroke();
    leaf(c, rx + s * 0.04, ry + s * 0.01, s * 0.07, s * 0.02, 0.2, '#3f8a3a'); leaf(c, rx - s * 0.04, ry + s * 0.01, s * 0.07, s * 0.02, Math.PI - 0.2, '#3f8a3a');
  }, noop],
  /* knäckebröd standing in a basket, and a cup for fika */
  crisp: [function (c, x, y, s) {
    for (var i = 0; i < 3; i++) { var cx = x - s * 0.18 + i * s * 0.09; paper(c, E(cx, y - s * 0.24, s * 0.14, s * 0.16, -0.2 + i * 0.2), '#d9b070', 0.4); sprinkle(c, cx, y - s * 0.24, s * 0.1, s * 0.12, 8, s * 0.01, ['#a87838']); fe(c, cx, y - s * 0.24, s * 0.025, s * 0.028, '#8a5a2a'); }
    paper(c, poly([[x - s * 0.3, y - s * 0.14], [x + s * 0.02, y - s * 0.14], [x - s * 0.02, y], [x - s * 0.26, y]]), '#b8864a', 0.5);
    var cx2 = x + s * 0.25; paper(c, poly([[cx2 - s * 0.1, y - s * 0.18], [cx2 + s * 0.1, y - s * 0.18], [cx2 + s * 0.08, y], [cx2 - s * 0.08, y]]), '#2f6db0', 0.5);
    fe(c, cx2, y - s * 0.18, s * 0.1, s * 0.025, '#5a3418'); fp(c, [[cx2 - s * 0.09, y - s * 0.1], [cx2 + s * 0.09, y - s * 0.1], [cx2 + s * 0.085, y - s * 0.07], [cx2 - s * 0.085, y - s * 0.07]], '#f2c94c');
  }, function (c, x, y, s, S, k) { steam(c, x + s * 0.25, y - s * 0.2, s * 0.45, S.t, k, 2, 0.45); }],
  /* nigiri and maki on a geta board, ginger and wasabi */
  nigiri: [function (c, x, y, s) {
    paper(c, rect(x - s * 0.45, y - s * 0.07, s * 0.9, s * 0.05), '#c99a5a', 0.6); paper(c, rect(x - s * 0.38, y - s * 0.02, s * 0.06, s * 0.02), '#a8783a', 0.3); paper(c, rect(x + s * 0.32, y - s * 0.02, s * 0.06, s * 0.02), '#a8783a', 0.3);
    var by = y - s * 0.07, tops = [['#f08a5d', '#ffd9c0'], ['#c8243a', null], ['#f4d03f', 'nori']];
    tops.forEach(function (tp, i) {
      var nx = x - s * 0.3 + i * s * 0.17; paper(c, E(nx, by - s * 0.04, s * 0.07, s * 0.04), '#fbf8f0', 0.3);
      paper(c, function (q) { q.beginPath(); q.ellipse(nx, by - s * 0.075, s * 0.085, s * 0.03, -0.05, 0, TAU); }, tp[0], 0.3);
      if (tp[1] === 'nori') fp(c, [[nx - s * 0.015, by - s * 0.105], [nx + s * 0.015, by - s * 0.105], [nx + s * 0.015, by - s * 0.01], [nx - s * 0.015, by - s * 0.01]], '#1e2a1e');
      else if (tp[1]) for (var j = 0; j < 3; j++) ln(c, [[nx - s * 0.05 + j * s * 0.04, by - s * 0.1], [nx - s * 0.035 + j * s * 0.04, by - s * 0.055]], tp[1], s * 0.008);
    });
    [0, 1].forEach(function (j) { var mx = x + s * 0.2 + j * s * 0.12; paper(c, rect(mx - s * 0.05, by - s * 0.08, s * 0.1, s * 0.08), '#1e2a1e', 0.3); fe(c, mx, by - s * 0.08, s * 0.05, s * 0.022, '#1e2a1e'); fe(c, mx, by - s * 0.08, s * 0.04, s * 0.017, '#fbf8f0'); fe(c, mx, by - s * 0.08, s * 0.015, s * 0.009, j ? '#f08a5d' : '#5aa83a'); });
    fe(c, x - s * 0.42, y - s * 0.1, s * 0.035, s * 0.02, '#f2a6b0'); fe(c, x - s * 0.42, y - s * 0.12, s * 0.025, s * 0.016, '#7ab84a');
  }, noop],
  /* ramen: noodles, chashu, the egg's yolk, a naruto spiral, nori standing up */
  ramen: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.95, '#2a1e1e', '#d8a868', '#c0392b');
    c.strokeStyle = '#f2d58a'; c.lineWidth = Math.max(0.7, s * 0.012); for (var i = 0; i < 5; i++) { c.beginPath(); for (var j = 0; j <= 10; j++) c.lineTo(b.x - b.rx * 0.6 + j * b.rx * 0.12, b.y - b.ry * 0.3 + i * b.ry * 0.18 + Math.sin(j * 1.6 + i) * s * 0.01); c.stroke(); }
    paper(c, rect(b.x + b.rx * 0.45, b.y - s * 0.28, s * 0.11, s * 0.26), '#1e2a1e', 0.4);
    paper(c, E(b.x + b.rx * 0.22, b.y - s * 0.025, s * 0.09, s * 0.045), '#c4825a', 0.3); fe(c, b.x + b.rx * 0.22, b.y - s * 0.03, s * 0.06, s * 0.025, '#e8b896');
    paper(c, E(b.x - b.rx * 0.45, b.y - s * 0.02, s * 0.065, s * 0.04), '#fbf8f0', 0.3); fe(c, b.x - b.rx * 0.45, b.y - s * 0.025, s * 0.035, s * 0.022, '#f29a1e');
    var nx = b.x - b.rx * 0.08, ny = b.y - s * 0.03; fe(c, nx, ny, s * 0.055, s * 0.03, '#fbf8f0');
    ln(c, spiral(nx, ny, s * 0.045, 1.8, 0.55), '#e84a7a', s * 0.01);
    sprinkle(c, b.x + b.rx * 0.05, b.y, b.rx * 0.6, b.ry * 0.5, 8, s * 0.012, ['#5aa83a', '#7ac85a']);
    ln(c, [[x + s * 0.5, y - s * 0.45], [x - s * 0.05, y - s * 0.39]], '#c8a060', s * 0.018); ln(c, [[x + s * 0.5, y - s * 0.43], [x - s * 0.04, y - s * 0.375]], '#b08a50', s * 0.018);
  }, function (c, x, y, s, S, k) { steam(c, x - s * 0.05, y - s * 0.45, s * 0.8, S.t, k, 3); }],
  /* onigiri, the nori band below */
  onigiri: [function (c, x, y, s) {
    leaf(c, x - s * 0.36, y - s * 0.02, s * 0.72, s * 0.06, 0, '#3f8a3a');
    [-0.13, 0.13].forEach(function (dx, i) { var ox = x + dx * s; paper(c, function (q) { q.beginPath(); q.moveTo(ox - s * 0.13, y - s * 0.04); q.quadraticCurveTo(ox - s * 0.15, y - s * 0.12, ox - s * 0.03, y - s * 0.28); q.quadraticCurveTo(ox, y - s * 0.31, ox + s * 0.03, y - s * 0.28); q.quadraticCurveTo(ox + s * 0.15, y - s * 0.12, ox + s * 0.13, y - s * 0.04); q.closePath(); }, '#fbf8f0', 0.6);
      fp(c, [[ox - s * 0.06, y - s * 0.04], [ox + s * 0.06, y - s * 0.04], [ox + s * 0.06, y - s * 0.13], [ox - s * 0.06, y - s * 0.13]], '#1e2a1e'); sprinkle(c, ox, y - s * 0.2, s * 0.05, s * 0.03, 4, s * 0.008, ['#222']); if (i) fe(c, ox, y - s * 0.2, s * 0.025, s * 0.02, '#c8243a'); });
  }, noop],
  /* matcha in a chawan, the whisk beside */
  matcha: [function (c, x, y, s) {
    var b = bowl(c, x - s * 0.08, y, s * 0.5, '#8a5a3a', '#7ab84a');
    sprinkle(c, b.x, b.y, b.rx * 0.7, b.ry * 0.6, 10, s * 0.01, ['#b6e08a']);
    var wx = x + s * 0.28; paper(c, function (q) { q.beginPath(); q.moveTo(wx - s * 0.07, y - s * 0.12); q.quadraticCurveTo(wx, y + s * 0.01, wx + s * 0.07, y - s * 0.12); q.closePath(); }, '#e8d4a0', 0.4);
    for (var i = 0; i < 6; i++) ln(c, [[wx - s * 0.06 + i * s * 0.024, y - s * 0.12], [wx - s * 0.02 + i * s * 0.008, y - s * 0.03]], '#c8a870', s * 0.006);
    paper(c, rect(wx - s * 0.02, y - s * 0.05, s * 0.04, s * 0.05), '#d8bc80', 0.3);
  }, function (c, x, y, s, S, k) { steam(c, x - s * 0.08, y - s * 0.22, s * 0.4, S.t, k, 2, 0.45); }],
  /* dim sum in a bamboo steamer: har gow and siu mai; a second basket's lid lifts */
  dimsum: [function (c, x, y, s) {
    steamer(c, x, y, s * 0.62, s * 0.16);
    var ty = y - s * 0.16;
    [[-0.14, '#f6e6e0'], [0, '#f6e6e0'], [0.14, '#f2c94c']].forEach(function (d, i) {
      var dx = x + d[0] * s;
      if (i < 2) { paper(c, function (q) { q.beginPath(); q.moveTo(dx - s * 0.075, ty); q.quadraticCurveTo(dx - s * 0.07, ty - s * 0.12, dx, ty - s * 0.12); q.quadraticCurveTo(dx + s * 0.07, ty - s * 0.12, dx + s * 0.075, ty); q.closePath(); }, d[1], 0.3); fe(c, dx, ty - s * 0.05, s * 0.035, s * 0.025, 'rgba(240,140,120,.55)'); for (var j = 0; j < 4; j++) ln(c, [[dx - s * 0.04 + j * s * 0.027, ty - s * 0.11], [dx - s * 0.03 + j * s * 0.02, ty - s * 0.07]], '#e8d0c8', s * 0.006); }
      else { paper(c, rect(dx - s * 0.06, ty - s * 0.1, s * 0.12, s * 0.1), d[1], 0.3); fe(c, dx, ty - s * 0.1, s * 0.06, s * 0.02, '#e8a830'); fe(c, dx, ty - s * 0.105, s * 0.02, s * 0.012, '#e8501e'); }
    });
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.32, s * 0.6, S.t, k, 3); }],
  /* roast duck, glossy and sliced, with cucumber and pancakes */
  duck: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    for (var i = 0; i < 6; i++) { var dx = x - s * 0.22 + i * s * 0.07; paper(c, E(dx, py - s * 0.05 - (i % 2) * s * 0.01, s * 0.06, s * 0.035, -0.4), '#8a3214', 0.3); fe(c, dx - s * 0.01, py - s * 0.06, s * 0.03, s * 0.01, 'rgba(255,200,150,.6)', -0.4); fe(c, dx + s * 0.01, py - s * 0.03, s * 0.05, s * 0.01, '#f2e0c8', -0.4); }
    ln(c, [[x + s * 0.22, py - s * 0.03], [x + s * 0.36, py - s * 0.06]], '#6aa83a', s * 0.03); ln(c, [[x + s * 0.24, py - s * 0.06], [x + s * 0.38, py - s * 0.08]], '#e8eed8', s * 0.02);
    paper(c, E(x - s * 0.34, py - s * 0.04, s * 0.1, s * 0.03), '#f4ead6', 0.3);
  }, noop],
  /* noodles in a bowl, chopsticks across */
  noodles: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.8, '#f4f1ea', '#c88a4a', '#2f6db0');
    c.strokeStyle = '#f2d58a'; c.lineWidth = Math.max(0.7, s * 0.014); for (var i = 0; i < 4; i++) { c.beginPath(); for (var j = 0; j <= 8; j++) c.lineTo(b.x - b.rx * 0.6 + j * b.rx * 0.15, b.y - b.ry * 0.2 + i * b.ry * 0.2 + Math.sin(j * 1.7 + i) * s * 0.012); c.stroke(); }
    sprinkle(c, b.x, b.y, b.rx * 0.6, b.ry * 0.5, 6, s * 0.018, ['#5aa83a', '#e8501e']);
    for (i = 0; i < 2; i++) fe(c, b.x + (i ? 0.25 : -0.3) * b.rx, b.y, s * 0.06, s * 0.025, '#3a7a2a');
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.35, s * 0.6, S.t, k, 2); }],
  /* a clay teapot steaming from its spout, two cups */
  teapot: [function (c, x, y, s) {
    var tx = x - s * 0.08;
    ln(c, [[tx + s * 0.13, y - s * 0.14], [tx + s * 0.26, y - s * 0.26]], '#8a4a2a', s * 0.045);
    c.strokeStyle = '#8a4a2a'; c.lineWidth = s * 0.035; c.beginPath(); c.arc(tx - s * 0.17, y - s * 0.15, s * 0.07, Math.PI * 0.5, Math.PI * 1.5); c.stroke();
    paper(c, E(tx, y - s * 0.13, s * 0.17, s * 0.12), '#9a5232', 0.7); fe(c, tx, y - s * 0.24, s * 0.08, s * 0.02, '#7a3a1a'); fe(c, tx, y - s * 0.27, s * 0.025, s * 0.02, '#7a3a1a');
    fe(c, tx - s * 0.06, y - s * 0.17, s * 0.04, s * 0.025, 'rgba(255,220,180,.35)');
    [0.22, 0.36].forEach(function (dx) { paper(c, poly([[x + dx * s - s * 0.05, y - s * 0.08], [x + dx * s + s * 0.05, y - s * 0.08], [x + dx * s + s * 0.035, y], [x + dx * s - s * 0.035, y]]), '#f4f1ea', 0.4); fe(c, x + dx * s, y - s * 0.08, s * 0.045, s * 0.012, '#c8a050'); });
  }, function (c, x, y, s, S, k) { steam(c, x + s * 0.18, y - s * 0.28, s * 0.4, S.t, k, 1, 0.5); }],
  /* a mooncake, fluted, a quarter cut to show the yolk */
  mooncake: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.8);
    paper(c, function (q) { q.beginPath(); for (var i = 0; i <= 48; i++) { var a = i / 48 * TAU, r = s * (0.2 + 0.012 * Math.cos(a * 12)); q.lineTo(x + Math.cos(a) * r, py - s * 0.07 + Math.sin(a) * r * 0.32); } q.closePath(); }, '#c88a3a', 0.6);
    fe(c, x, py - s * 0.09, s * 0.16, s * 0.045, '#d8a050');
    c.strokeStyle = '#a8662a'; c.lineWidth = 0.8; c.beginPath(); c.ellipse(x, py - s * 0.09, s * 0.12, s * 0.032, 0, 0, TAU); c.stroke();
    for (var i = 0; i < 8; i++) { var a = i / 8 * TAU; fe(c, x + Math.cos(a) * s * 0.06, py - s * 0.09 + Math.sin(a) * s * 0.016, s * 0.02, s * 0.008, '#b8762e', a); }
    paper(c, poly([[x + s * 0.24, py - s * 0.01], [x + s * 0.4, py - s * 0.04], [x + s * 0.36, py - s * 0.14]]), '#6a3a22', 0.4); fe(c, x + s * 0.34, py - s * 0.06, s * 0.03, s * 0.025, '#f2a61e');
  }, noop],
  /* phở: broth, rice noodles, beef, herbs, lime */
  pho: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.95, '#f6f2ea', '#d8b070', '#2f6db0');
    c.strokeStyle = '#fbf8ee'; c.lineWidth = Math.max(0.7, s * 0.012); for (var i = 0; i < 4; i++) { c.beginPath(); for (var j = 0; j <= 10; j++) c.lineTo(b.x - b.rx * 0.6 + j * b.rx * 0.12, b.y - b.ry * 0.2 + i * b.ry * 0.2 + Math.sin(j * 1.5 + i) * s * 0.01); c.stroke(); }
    [[-0.3, 0], [-0.1, -0.02], [0.1, 0.01]].forEach(function (p) { fe(c, b.x + p[0] * s, b.y + p[1] * s, s * 0.07, s * 0.025, '#a8604a', 0.2); });
    leaf(c, b.x + s * 0.12, b.y - s * 0.01, s * 0.12, s * 0.035, -0.5, '#2f7a2a'); leaf(c, b.x + s * 0.14, b.y, s * 0.11, s * 0.03, 0.3, '#3f8a3a'); leaf(c, b.x - s * 0.02, b.y - s * 0.02, s * 0.1, s * 0.03, -2.6, '#4f9a3c');
    for (i = 0; i < 4; i++) { c.strokeStyle = '#e8e0f0'; c.lineWidth = 0.8; c.beginPath(); c.ellipse(b.x - s * 0.2 + i * s * 0.08, b.y + s * 0.01, s * 0.02, s * 0.01, 0, 0, TAU); c.stroke(); }
    chili(c, b.x + s * 0.28, b.y - s * 0.01, s * 0.06, 0.3); lime(c, x + s * 0.4, y - s * 0.02, s * 0.06);
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.45, s * 0.8, S.t, k, 3); }],
  /* bánh mì, split to show pickled carrot, daikon, cucumber and coriander */
  banhmi: [function (c, x, y, s) {
    paper(c, rect(x - s * 0.42, y - s * 0.04, s * 0.84, s * 0.03), '#f2e6c9', 0.3);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.42, y - s * 0.08); q.quadraticCurveTo(x - s * 0.44, y - s * 0.2, x - s * 0.3, y - s * 0.2); q.lineTo(x + s * 0.32, y - s * 0.2); q.quadraticCurveTo(x + s * 0.44, y - s * 0.18, x + s * 0.42, y - s * 0.08); q.closePath(); }, '#d99a4e', 0.6);
    fp(c, [[x - s * 0.36, y - s * 0.17], [x + s * 0.36, y - s * 0.17], [x + s * 0.34, y - s * 0.24], [x - s * 0.34, y - s * 0.24]], '#e8a07a');
    for (var i = 0; i < 9; i++) { ln(c, [[x - s * 0.32 + i * s * 0.08, y - s * 0.22], [x - s * 0.28 + i * s * 0.08, y - s * 0.27]], i % 2 ? '#f08a2a' : '#f6f2e6', s * 0.018); }
    for (i = 0; i < 4; i++) leaf(c, x - s * 0.25 + i * s * 0.16, y - s * 0.26, s * 0.08, s * 0.025, -1 - i * 0.3, '#4f9a3c');
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.4, y - s * 0.24); q.quadraticCurveTo(x - s * 0.4, y - s * 0.36, x - s * 0.26, y - s * 0.36); q.lineTo(x + s * 0.3, y - s * 0.36); q.quadraticCurveTo(x + s * 0.42, y - s * 0.34, x + s * 0.4, y - s * 0.28); q.closePath(); }, '#e0a050', 0.6);
    for (i = 0; i < 4; i++) ln(c, [[x - s * 0.24 + i * s * 0.15, y - s * 0.3], [x - s * 0.16 + i * s * 0.15, y - s * 0.35]], '#b8762e', s * 0.014);
  }, noop],
  /* gỏi cuốn: rice paper rolls with shrimp showing through, a dipping sauce */
  goicuon: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    [-0.2, 0, 0.2].forEach(function (dx, i) { var rx = x + dx * s - s * 0.06; paper(c, rect(rx - s * 0.08, py - s * 0.14, s * 0.16, s * 0.1), 'rgba(250,246,236,.92)', 0.4); fe(c, rx - s * 0.03, py - s * 0.1, s * 0.035, s * 0.022, '#f08a6a'); fe(c, rx + s * 0.03, py - s * 0.09, s * 0.035, s * 0.02, '#f49a7a'); fe(c, rx, py - s * 0.06, s * 0.06, s * 0.015, '#6ab84a'); fe(c, rx + s * 0.08, py - s * 0.09, s * 0.02, s * 0.05, 'rgba(250,246,236,.95)'); });
    var b = bowl(c, x + s * 0.32, py, s * 0.2, '#f4f1ea', '#8a4a22'); sprinkle(c, b.x, b.y, b.rx * 0.6, b.ry * 0.5, 4, s * 0.008, ['#e8c890']);
  }, noop],
  /* cà phê phin: the filter drips, y = ½gt², into condensed milk */
  phin: [function (c, x, y, s) {
    var w = s * 0.26, h = s * 0.32;
    paper(c, poly([[x - w * 0.5, y - h], [x + w * 0.5, y - h], [x + w * 0.42, y], [x - w * 0.42, y]]), 'rgba(225,240,245,.55)', 0.5);
    fp(c, [[x - w * 0.42, y - h * 0.28], [x + w * 0.42, y - h * 0.28], [x + w * 0.4, y - s * 0.01], [x - w * 0.4, y - s * 0.01]], '#f4ecd6');
    fp(c, [[x - w * 0.44, y - h * 0.5], [x + w * 0.44, y - h * 0.5], [x + w * 0.42, y - h * 0.28], [x - w * 0.42, y - h * 0.28]], '#5a3418');
    paper(c, E(x, y - h - s * 0.01, w * 0.62, s * 0.022), '#b8bcc4', 0.4);
    paper(c, poly([[x - w * 0.42, y - h - s * 0.2], [x + w * 0.42, y - h - s * 0.2], [x + w * 0.34, y - h - s * 0.01], [x - w * 0.34, y - h - s * 0.01]]), '#c8ccd2', 0.5);
    paper(c, E(x, y - h - s * 0.21, w * 0.44, s * 0.03), '#9aa0a8', 0.3); fe(c, x, y - h - s * 0.24, s * 0.02, s * 0.015, '#9aa0a8');
  }, function (c, x, y, s, S, k) {
    var h = s * 0.32, top = y - h - s * 0.01, bot = y - h * 0.5;
    for (var i = 0; i < 2; i++) { var u = ((S.t / 1000) / 0.9 + i * 0.5 + k * 0.1) % 1; fe(c, x, top + u * u * (bot - top), s * 0.012, s * 0.018, '#3a1e0a'); }
  }],
  /* mohinga: fish broth, rice noodles, fritters, egg, coriander */
  mohinga: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.95, '#f4f1ea', '#c8783a', '#c0392b');
    c.strokeStyle = '#fbf8ee'; c.lineWidth = Math.max(0.7, s * 0.01); for (var i = 0; i < 3; i++) { c.beginPath(); for (var j = 0; j <= 10; j++) c.lineTo(b.x - b.rx * 0.6 + j * b.rx * 0.12, b.y - b.ry * 0.1 + i * b.ry * 0.25 + Math.sin(j * 1.7 + i) * s * 0.01); c.stroke(); }
    [[-0.22, -0.03], [-0.05, -0.04], [0.12, -0.03]].forEach(function (p) { paper(c, poly([[b.x + p[0] * s - s * 0.06, b.y + p[1] * s + s * 0.02], [b.x + p[0] * s + s * 0.06, b.y + p[1] * s + s * 0.01], [b.x + p[0] * s + s * 0.04, b.y + p[1] * s - s * 0.04], [b.x + p[0] * s - s * 0.05, b.y + p[1] * s - s * 0.03]]), '#d8962e', 0.3); });
    paper(c, E(b.x + b.rx * 0.6, b.y - s * 0.02, s * 0.06, s * 0.04), '#fbf8f0', 0.3); fe(c, b.x + b.rx * 0.6, b.y - s * 0.025, s * 0.03, s * 0.02, '#f2b01e');
    sprinkle(c, b.x, b.y - s * 0.02, b.rx * 0.6, b.ry * 0.4, 9, s * 0.014, ['#4f9a3c', '#3f8a3a', '#e8501e']); lime(c, x - s * 0.42, y - s * 0.02, s * 0.06);
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.45, s * 0.75, S.t, k, 2); }],
  /* laphet thoke on a lacquer tray: the tea leaves in the middle, the crunchy things in
     sectors round them, θ_k = 2πk/n */
  laphet: [function (c, x, y, s) {
    paper(c, E(x, y - s * 0.05, s * 0.42, s * 0.11), '#1e1410', 0.8); fe(c, x, y - s * 0.07, s * 0.4, s * 0.095, '#8a1e14');
    var cols = ['#d8a868', '#f2e6c9', '#e8c070', '#e86a3a', '#c8243a', '#a87838'], n = cols.length;
    for (var i = 0; i < n; i++) { var a0 = i / n * TAU, a1 = (i + 1) / n * TAU; c.fillStyle = cols[i]; c.beginPath(); c.moveTo(x, y - s * 0.075); c.ellipse(x, y - s * 0.075, s * 0.36, s * 0.082, 0, a0 + 0.06, a1 - 0.06); c.closePath(); c.fill(); }
    sprinkle(c, x, y - s * 0.075, s * 0.3, s * 0.07, 18, s * 0.012, ['#8a5a2a', '#fff6e0', '#5a3418']);
    paper(c, E(x, y - s * 0.09, s * 0.12, s * 0.04), '#3f5a1e', 0.4); sprinkle(c, x, y - s * 0.09, s * 0.09, s * 0.025, 8, s * 0.012, ['#5a7a2a', '#2a3a14']);
    c.strokeStyle = '#e8b84a'; c.lineWidth = Math.max(0.7, s * 0.012); c.beginPath(); c.ellipse(x, y - s * 0.07, s * 0.4, s * 0.095, 0, 0, TAU); c.stroke();
  }, noop],
  /* lahpet yay, the milk tea, on a saucer */
  milktea: [function (c, x, y, s) {
    paper(c, E(x, y - s * 0.02, s * 0.16, s * 0.035), '#f4f1ea', 0.4);
    glass(c, x, y - s * 0.03, s * 0.2, s * 0.26, '#c8925a', 0.88); fe(c, x, y - s * 0.03 - s * 0.26 * 0.88, s * 0.09, s * 0.015, '#ead2a8');
    var sx = x + s * 0.3; paper(c, poly([[sx - s * 0.13, y - s * 0.02], [sx + s * 0.13, y - s * 0.02], [sx, y - s * 0.2]]), '#d8962e', 0.5); paper(c, poly([[sx - s * 0.02, y - s * 0.02], [sx + s * 0.22, y - s * 0.02], [sx + s * 0.12, y - s * 0.17]]), '#e0a640', 0.5);
    paper(c, poly([[x - s * 0.45, y - s * 0.02], [x - s * 0.19, y - s * 0.02], [x - s * 0.32, y - s * 0.19]]), '#d8962e', 0.5);
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.3, s * 0.4, S.t, k, 2, 0.45); }],
  /* pad thai: noodles, shrimp, sprouts, peanuts, lime */
  padthai: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, function (q) { q.beginPath(); q.ellipse(x, py - s * 0.05, s * 0.3, s * 0.09, 0, Math.PI, TAU); q.closePath(); }, '#d8964a', 0.4);
    c.strokeStyle = '#e8b064'; c.lineWidth = Math.max(0.7, s * 0.014); for (var i = 0; i < 7; i++) { c.beginPath(); for (var j = 0; j <= 8; j++) c.lineTo(x - s * 0.26 + j * s * 0.065, py - s * 0.03 - i * s * 0.011 - Math.sin(j / 8 * Math.PI) * s * 0.06 + Math.sin(j * 2 + i) * s * 0.01); c.stroke(); }
    [[-0.12, -0.1], [0.04, -0.12], [0.16, -0.08]].forEach(function (p) { c.strokeStyle = '#f2784a'; c.lineWidth = s * 0.035; c.beginPath(); c.arc(x + p[0] * s, py + p[1] * s, s * 0.035, 0.3, Math.PI * 1.6); c.stroke(); });
    sprinkle(c, x, py - s * 0.1, s * 0.2, s * 0.04, 12, s * 0.012, ['#e8c890', '#f6eedd', '#5aa83a']);
    lime(c, x + s * 0.33, py - s * 0.01, s * 0.07); for (i = 0; i < 4; i++) ln(c, [[x - s * 0.38, py - s * 0.02 - i * s * 0.01], [x - s * 0.22, py - s * 0.04 - i * s * 0.015]], i % 2 ? '#f6f2e6' : '#5aa83a', s * 0.012);
  }, noop],
  /* tom yum in a mo fai, the chimney pot, charcoal glowing in its chimney */
  tomyum: [function (c, x, y, s) {
    paper(c, poly([[x - s * 0.2, y], [x + s * 0.2, y], [x + s * 0.14, y - s * 0.1], [x - s * 0.14, y - s * 0.1]]), '#7a7e86', 0.5);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.36, y - s * 0.3); q.quadraticCurveTo(x - s * 0.36, y - s * 0.1, x - s * 0.18, y - s * 0.1); q.lineTo(x + s * 0.18, y - s * 0.1); q.quadraticCurveTo(x + s * 0.36, y - s * 0.1, x + s * 0.36, y - s * 0.3); q.closePath(); }, '#b8bcc4', 0.7);
    fe(c, x, y - s * 0.3, s * 0.36, s * 0.07, '#e0602a');
    [[-0.25, 0.01], [0.22, -0.01], [-0.18, -0.03]].forEach(function (p) { c.strokeStyle = '#f2a07a'; c.lineWidth = s * 0.03; c.beginPath(); c.arc(x + p[0] * s, y - s * 0.3 + p[1] * s, s * 0.03, 0.3, Math.PI * 1.6); c.stroke(); });
    chili(c, x + s * 0.12, y - s * 0.31, s * 0.07, -0.3); leaf(c, x - s * 0.12, y - s * 0.31, s * 0.06, s * 0.02, 0.4, '#3f8a3a');
    paper(c, rect(x - s * 0.07, y - s * 0.52, s * 0.14, s * 0.24), '#9aa0a8', 0.6); fe(c, x, y - s * 0.52, s * 0.07, s * 0.02, '#3a2a22');
    ln(c, [[x + s * 0.18, y - s * 0.32], [x + s * 0.3, y - s * 0.5]], '#c8d090', s * 0.02);
  }, function (c, x, y, s, S, k) { fe(c, x, y - s * 0.52, s * 0.05, s * 0.014, 'rgba(255,' + Math.round(120 + 60 * Math.sin(S.t / 150)) + ',40,.95)'); steam(c, x - s * 0.22, y - s * 0.36, s * 0.55, S.t, k, 2); }],
  /* green curry: coconut swirl, Thai eggplant, chilli, basil */
  greencurry: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.82, '#f4f1ea', '#86a84a', '#2f6db0');
    c.strokeStyle = 'rgba(250,246,230,.85)'; c.lineWidth = Math.max(0.7, s * 0.014); c.beginPath(); spiral(b.x, b.y, b.rx * 0.5, 1.5, 0.35).forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke();
    [[-0.2, 0], [0.18, 0.01]].forEach(function (p) { fe(c, b.x + p[0] * s, b.y + p[1] * s, s * 0.04, s * 0.025, '#b8d870'); fe(c, b.x + p[0] * s, b.y + p[1] * s, s * 0.015, s * 0.01, '#5a7a2a'); });
    chili(c, b.x - s * 0.05, b.y - s * 0.01, s * 0.08, 0.4); leaf(c, b.x + s * 0.05, b.y, s * 0.08, s * 0.025, -0.6, '#2f7a2a'); leaf(c, b.x + s * 0.05, b.y, s * 0.08, s * 0.025, -2.2, '#3f8a3a');
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.38, s * 0.6, S.t, k, 2); }],
  /* mango sticky rice: the mango fanned, coconut cream poured */
  mango: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, E(x - s * 0.13, py - s * 0.06, s * 0.15, s * 0.07), '#f8f4e8', 0.4); fe(c, x - s * 0.13, py - s * 0.1, s * 0.11, s * 0.025, '#fffdf6'); sprinkle(c, x - s * 0.13, py - s * 0.1, s * 0.08, s * 0.02, 6, s * 0.01, ['#2a2a2a', '#f2c94c']);
    for (var i = 0; i < 5; i++) paper(c, E(x + s * 0.06 + i * s * 0.05, py - s * 0.05 - i * s * 0.005, s * 0.08, s * 0.04, -0.3), i % 2 ? '#f6b02a' : '#f8c03a', 0.3);
    fe(c, x - s * 0.13, py - s * 0.115, s * 0.07, s * 0.012, 'rgba(255,255,250,.95)');
  }, noop],
  /* som tam: green papaya, tomato, long beans, chillies, peanuts */
  somtam: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, function (q) { q.beginPath(); q.ellipse(x, py - s * 0.04, s * 0.27, s * 0.09, 0, Math.PI, TAU); q.closePath(); }, '#c8e098', 0.4);
    for (var i = 0; i < 16; i++) { var a = RR() * Math.PI, r = RR(); ln(c, [[x + Math.cos(a + Math.PI) * s * 0.22 * r, py - s * 0.04 + Math.sin(a + Math.PI) * s * 0.07 * r], [x + Math.cos(a + Math.PI) * s * 0.22 * r + s * 0.06, py - s * 0.05 + Math.sin(a + Math.PI) * s * 0.07 * r]], i % 3 ? '#e2f0b8' : '#b0d070', s * 0.012); }
    [[-0.12, -0.08], [0.1, -0.09], [0.02, -0.12]].forEach(function (p) { fp(c, [[x + p[0] * s - s * 0.04, py + p[1] * s + s * 0.02], [x + p[0] * s + s * 0.04, py + p[1] * s + s * 0.02], [x + p[0] * s, py + p[1] * s - s * 0.03]], '#e0402a'); });
    chili(c, x - s * 0.04, py - s * 0.1, s * 0.06, 0.6); sprinkle(c, x, py - s * 0.08, s * 0.15, s * 0.03, 6, s * 0.012, ['#e8c890']);
    for (i = 0; i < 3; i++) ln(c, [[x + s * 0.24, py - s * 0.02 - i * s * 0.02], [x + s * 0.44, py - s * 0.06 - i * s * 0.02]], '#4f9a3c', s * 0.02);
    paper(c, E(x - s * 0.35, py - s * 0.03, s * 0.09, s * 0.05), '#d8ecb0', 0.3);
  }, noop],
  /* gai yang clamped in split bamboo, jaew to dip */
  gaiyang: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, function (q) { q.beginPath(); q.moveTo(x - s * 0.25, py - s * 0.06); q.quadraticCurveTo(x - s * 0.22, py - s * 0.25, x, py - s * 0.24); q.quadraticCurveTo(x + s * 0.2, py - s * 0.24, x + s * 0.22, py - s * 0.08); q.quadraticCurveTo(x, py - s * 0.02, x - s * 0.25, py - s * 0.06); }, '#b8601e', 0.5);
    fe(c, x - s * 0.05, py - s * 0.17, s * 0.1, s * 0.04, 'rgba(255,200,120,.4)');
    for (var i = 0; i < 4; i++) ln(c, [[x - s * 0.18 + i * s * 0.1, py - s * 0.2], [x - s * 0.12 + i * s * 0.1, py - s * 0.06]], '#5a2a0a', s * 0.016);
    ln(c, [[x - s * 0.33, py - s * 0.12], [x + s * 0.32, py - s * 0.15]], '#d8b878', s * 0.025); ln(c, [[x - s * 0.33, py - s * 0.18], [x + s * 0.32, py - s * 0.2]], '#d8b878', s * 0.025);
    var b = bowl(c, x + s * 0.34, py, s * 0.18, '#f4f1ea', '#8a2a14'); sprinkle(c, b.x, b.y, b.rx * 0.6, b.ry * 0.5, 4, s * 0.007, ['#e8501e']);
  }, noop],
  /* larb: mince, mint, shallot, toasted rice */
  larb: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    paper(c, function (q) { q.beginPath(); q.ellipse(x - s * 0.05, py - s * 0.04, s * 0.22, s * 0.1, 0, Math.PI, TAU); q.closePath(); }, '#a8684a', 0.4);
    sprinkle(c, x - s * 0.05, py - s * 0.08, s * 0.18, s * 0.05, 18, s * 0.014, ['#7a4a2a', '#c88a6a', '#e8c890', '#d84a3a']);
    for (var i = 0; i < 5; i++) leaf(c, x - s * 0.18 + i * s * 0.07, py - s * 0.1 - (i % 2) * s * 0.03, s * 0.06, s * 0.025, -1 - i * 0.4, '#3f9a4c');
    for (i = 0; i < 3; i++) { ln(c, [[x + s * 0.24, py - s * 0.03 - i * s * 0.02], [x + s * 0.42, py - s * 0.05 - i * s * 0.025]], i === 1 ? '#d8ecb0' : '#4f9a3c', s * 0.02); }
  }, noop],
  /* roti folded in squares under condensed milk */
  roti: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    for (var i = 0; i < 4; i++) { var rx = x - s * 0.21 + i * s * 0.13; paper(c, poly([[rx - s * 0.08, py - s * 0.04], [rx + s * 0.08, py - s * 0.05], [rx + s * 0.06, py - s * 0.12], [rx - s * 0.06, py - s * 0.11]]), '#e3b062', 0.3); sprinkle(c, rx, py - s * 0.08, s * 0.05, s * 0.02, 4, s * 0.01, ['#a8662a']); }
    c.strokeStyle = '#fffaf0'; c.lineWidth = Math.max(0.8, s * 0.015); c.beginPath(); for (i = 0; i <= 14; i++) c.lineTo(x - s * 0.26 + i * s * 0.037, py - s * 0.09 - (i % 2) * s * 0.03); c.stroke();
  }, noop],
  /* massaman: potatoes, peanuts, onion in the red-gold curry */
  massaman: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.82, '#2f6db0', '#c8642a', '#f2c94c');
    [[-0.15, 0], [0.12, -0.01], [0, 0.015]].forEach(function (p) { paper(c, rect(b.x + p[0] * s - s * 0.04, b.y + p[1] * s - s * 0.04, s * 0.08, s * 0.05), '#f2c25a', 0.3); });
    sprinkle(c, b.x, b.y, b.rx * 0.7, b.ry * 0.5, 7, s * 0.016, ['#e8c890', '#f2e6c9']);
    c.strokeStyle = 'rgba(255,200,80,.6)'; c.lineWidth = 1; c.beginPath(); c.ellipse(b.x, b.y, b.rx * 0.8, b.ry * 0.7, 0, 0, TAU); c.stroke();
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.38, s * 0.6, S.t, k, 2); }],
  /* satay on bamboo with peanut sauce and ajad */
  satay: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    for (var i = 0; i < 4; i++) { var a = -0.25 + i * 0.12, sx = x - s * 0.3, sy = py - s * 0.04 - i * s * 0.025; ln(c, [[sx, sy], [sx + Math.cos(a) * s * 0.55, sy + Math.sin(a) * s * 0.12]], '#d8b878', s * 0.014); for (var j = 0; j < 4; j++) { var f = 0.3 + j * 0.16; paper(c, E(sx + Math.cos(a) * s * 0.55 * f, sy + Math.sin(a) * s * 0.12 * f - s * 0.01, s * 0.045, s * 0.025, a), j % 2 ? '#c4782a' : '#d88a32', 0.2); } }
    var b = bowl(c, x + s * 0.32, py, s * 0.22, '#f4f1ea', '#d8742a'); sprinkle(c, b.x, b.y, b.rx * 0.6, b.ry * 0.5, 4, s * 0.008, ['#8a4a12']);
  }, noop],
  /* khao yam: blue butterfly-pea rice ringed by shredded herbs, θ_k = 2πk/n */
  khaoyam: [function (c, x, y, s) {
    var py = plate(c, x, y, s), cols = ['#5aa83a', '#f2d03a', '#f2a6b0', '#fbf8ee', '#e8a64a', '#3f8a3a', '#d84a3a'];
    for (var i = 0; i < cols.length; i++) { var a = Math.PI + (i + 0.5) / cols.length * Math.PI, hx = x + Math.cos(a) * s * 0.28, hy = py - s * 0.05 + Math.sin(a) * s * 0.06; paper(c, E(hx, hy, s * 0.06, s * 0.035), cols[i], 0.2); sprinkle(c, hx, hy, s * 0.045, s * 0.02, 4, s * 0.008, ['rgba(0,0,0,.25)']); }
    paper(c, function (q) { q.beginPath(); q.ellipse(x, py - s * 0.05, s * 0.13, s * 0.11, 0, Math.PI, TAU); q.closePath(); }, '#4a68c8', 0.4); sprinkle(c, x, py - s * 0.1, s * 0.09, s * 0.04, 10, s * 0.01, ['#6a88e0', '#3a50a8']);
    lime(c, x + s * 0.36, py, s * 0.06);
  }, noop],
  /* fried chicken in a basket lined with checked paper */
  chicken: [function (c, x, y, s) {
    paper(c, poly([[x - s * 0.36, y - s * 0.16], [x + s * 0.36, y - s * 0.16], [x + s * 0.3, y], [x - s * 0.3, y]]), '#b8864a', 0.6);
    c.strokeStyle = '#8a5a2a'; c.lineWidth = 0.8; for (var i = 0; i < 6; i++) { c.beginPath(); c.moveTo(x - s * 0.34 + i * s * 0.13, y - s * 0.16); c.lineTo(x - s * 0.29 + i * s * 0.11, y); c.stroke(); }
    for (i = 0; i < 6; i++) fp(c, [[x - s * 0.36 + i * s * 0.12, y - s * 0.16], [x - s * 0.3 + i * s * 0.12, y - s * 0.16], [x - s * 0.33 + i * s * 0.12, y - s * 0.24]], i % 2 ? '#d1342b' : '#fbf8f0');
    [[-0.18, -0.24, -0.5], [0.02, -0.28, 0.2], [0.2, -0.22, 0.7]].forEach(function (p) {
      var cx = x + p[0] * s, cy = y + p[1] * s;
      ln(c, [[cx, cy], [cx + Math.sin(p[2]) * s * 0.16, cy - Math.cos(p[2]) * s * 0.16]], '#f2ead8', s * 0.035); fe(c, cx + Math.sin(p[2]) * s * 0.17, cy - Math.cos(p[2]) * s * 0.17, s * 0.025, s * 0.02, '#f2ead8');
      paper(c, function (q) { var pts = []; for (var j = 0; j < 16; j++) { var a = j / 16 * TAU, r = (j % 2 ? 0.95 : 1.08); pts.push([cx + Math.cos(a) * s * 0.11 * r, cy + Math.sin(a) * s * 0.09 * r]); } path(q, pts); q.closePath(); }, '#b8681e', 0.4);
      sprinkle(c, cx, cy, s * 0.08, s * 0.06, 7, s * 0.016, ['#e0a040', '#8a4a12', '#d88a2a']);
    });
  }, noop],
  /* collard greens, the pot liquor shining */
  collards: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.78, '#f4f1ea', '#4a5a22', '#c0392b');
    for (var i = 0; i < 7; i++) { var lx = b.x - b.rx * 0.7 + i * b.rx * 0.22; paper(c, function (q) { q.beginPath(); q.moveTo(lx - s * 0.05, b.y + s * 0.01); q.quadraticCurveTo(lx - s * 0.03, b.y - s * 0.08 - (i % 2) * s * 0.03, lx + s * 0.04, b.y - s * 0.05); q.quadraticCurveTo(lx + s * 0.03, b.y, lx - s * 0.05, b.y + s * 0.01); }, i % 2 ? '#2f6a2a' : '#3f7a32', 0.2); }
    fe(c, b.x + b.rx * 0.3, b.y - s * 0.02, s * 0.05, s * 0.03, '#d88a7a');
  }, function (c, x, y, s, S, k) { steam(c, x, y - s * 0.4, s * 0.55, S.t, k, 2); }],
  /* cornbread in its cast-iron skillet, cut in wedges, butter melting */
  cornbread: [function (c, x, y, s) {
    paper(c, E(x, y - s * 0.07, s * 0.34, s * 0.1), '#1e1e20', 0.8); ln(c, [[x - s * 0.33, y - s * 0.08], [x - s * 0.52, y - s * 0.12]], '#1e1e20', s * 0.06);
    fe(c, x, y - s * 0.11, s * 0.3, s * 0.075, '#e8b23a'); fe(c, x, y - s * 0.12, s * 0.27, s * 0.06, '#f2c84a');
    for (var i = 0; i < 6; i++) { var a = i / 6 * TAU; ln(c, [[x, y - s * 0.12], [x + Math.cos(a) * s * 0.27, y - s * 0.12 + Math.sin(a) * s * 0.06]], '#c8901e', s * 0.01); }
    sprinkle(c, x, y - s * 0.12, s * 0.22, s * 0.04, 10, s * 0.01, ['#d89a2a']); paper(c, rect(x - s * 0.04, y - s * 0.16, s * 0.08, s * 0.04), '#f8e08a', 0.3);
  }, noop],
  /* mac and cheese in a baking dish, the crust browned */
  mac: [function (c, x, y, s) {
    paper(c, poly([[x - s * 0.36, y - s * 0.16], [x + s * 0.36, y - s * 0.16], [x + s * 0.32, y], [x - s * 0.32, y]]), '#f4f1ea', 0.7);
    ln(c, [[x - s * 0.33, y - s * 0.07], [x + s * 0.33, y - s * 0.07]], '#2f6db0', s * 0.02);
    fe(c, x, y - s * 0.16, s * 0.34, s * 0.05, '#f2a42a'); sprinkle(c, x, y - s * 0.16, s * 0.3, s * 0.04, 22, s * 0.014, ['#c86a1e', '#f8c860', '#a85a1a']);
    ln(c, [[x + s * 0.1, y - s * 0.17], [x + s * 0.32, y - s * 0.36]], '#c9ccd2', s * 0.025);
  }, function (c, x, y, s, S, k) { steam(c, x - s * 0.1, y - s * 0.2, s * 0.5, S.t, k, 2); }],
  /* sweet potato pie, a slice cut, cream on top */
  sweetpie: [function (c, x, y, s) {
    var py = plate(c, x, y, s * 0.95);
    paper(c, E(x - s * 0.04, py - s * 0.06, s * 0.28, s * 0.075), '#c88a42', 0.5); fe(c, x - s * 0.04, py - s * 0.08, s * 0.24, s * 0.06, '#e0782a');
    for (var i = 0; i < 18; i++) { var a = i / 18 * TAU; fe(c, x - s * 0.04 + Math.cos(a) * s * 0.26, py - s * 0.075 + Math.sin(a) * s * 0.068, s * 0.02, s * 0.012, '#d89a52'); }
    fp(c, [[x - s * 0.04, py - s * 0.08], [x + s * 0.2, py - s * 0.06], [x + s * 0.17, py - s * 0.12]], '#f4f1ea');
    paper(c, poly([[x + s * 0.24, py - s * 0.03], [x + s * 0.44, py - s * 0.04], [x + s * 0.4, py - s * 0.11], [x + s * 0.26, py - s * 0.1]]), '#e0782a', 0.3);
    fe(c, x - s * 0.06, py - s * 0.11, s * 0.05, s * 0.03, '#fffaf2');
  }, noop],
  /* falafel: crisp outsides, one broken open green */
  falafel: [function (c, x, y, s) {
    var py = plate(c, x, y, s);
    [[-0.2, 0], [-0.06, 0.01], [0.08, 0], [-0.13, -0.07], [0.01, -0.07]].forEach(function (p) { var fx = x + p[0] * s, fy = py - s * 0.06 + p[1] * s; paper(c, E(fx, fy, s * 0.07, s * 0.06), '#6b3f1c', 0.3); sprinkle(c, fx, fy, s * 0.05, s * 0.04, 5, s * 0.012, ['#8a5a2a', '#4a2a10']); });
    var ox = x + s * 0.24, oy = py - s * 0.05; fe(c, ox, oy, s * 0.07, s * 0.05, '#6b3f1c'); fe(c, ox, oy - s * 0.01, s * 0.055, s * 0.035, '#6aa83a'); sprinkle(c, ox, oy - s * 0.01, s * 0.04, s * 0.025, 5, s * 0.008, ['#4a8a2a', '#9ac85a']);
    c.strokeStyle = '#f6eedd'; c.lineWidth = Math.max(0.8, s * 0.014); c.beginPath(); for (var i = 0; i <= 10; i++) c.lineTo(x - s * 0.25 + i * s * 0.035, py - s * 0.1 - (i % 2) * s * 0.025); c.stroke();
    fp(c, [[x + s * 0.34, py - s * 0.02], [x + s * 0.44, py - s * 0.02], [x + s * 0.4, py - s * 0.07]], '#f2e04a');
  }, noop],
  /* pita wrapped in paper, the filling spilling */
  pita: [function (c, x, y, s) {
    c.save(); c.translate(x, y - s * 0.02); c.rotate(-0.35);
    paper(c, poly([[-s * 0.14, -s * 0.45], [s * 0.14, -s * 0.45], [s * 0.1, 0], [-s * 0.1, 0]]), '#e8d4a8', 0.6);
    fe(c, 0, -s * 0.47, s * 0.14, s * 0.06, '#5aa83a'); fe(c, -s * 0.05, -s * 0.52, s * 0.05, s * 0.045, '#6b3f1c'); fe(c, s * 0.05, -s * 0.5, s * 0.04, s * 0.035, '#d6402e'); fe(c, 0, -s * 0.5, s * 0.05, s * 0.02, '#f6eedd');
    paper(c, poly([[-s * 0.15, -s * 0.28], [s * 0.15, -s * 0.28], [s * 0.11, 0], [-s * 0.11, 0]]), '#f6f2ea', 0.4); ln(c, [[-s * 0.13, -s * 0.24], [s * 0.13, -s * 0.24]], '#2f6db0', s * 0.015);
    c.restore();
  }, noop],
  /* hummus: the spoon's groove a spiral, r = aθ, oil in it, paprika and chickpeas */
  hummus: [function (c, x, y, s) {
    paper(c, E(x, y - s * 0.05, s * 0.36, s * 0.1), '#2f6db0', 0.7); fe(c, x, y - s * 0.08, s * 0.31, s * 0.075, '#e8d6a8');
    ln(c, spiral(x, y - s * 0.08, s * 0.24, 2.2, 0.28), '#c8b080', s * 0.025);
    ln(c, spiral(x, y - s * 0.08, s * 0.14, 1.4, 0.28).slice(10), 'rgba(200,170,40,.75)', s * 0.03);
    sprinkle(c, x, y - s * 0.08, s * 0.2, s * 0.05, 10, s * 0.01, ['#c8301e']);
    [[-0.05, 0], [0.04, -0.01], [0, 0.015]].forEach(function (p) { fe(c, x + p[0] * s, y - s * 0.08 + p[1] * s, s * 0.022, s * 0.018, '#e8c47a'); });
    leaf(c, x + s * 0.12, y - s * 0.09, s * 0.06, s * 0.02, -0.5, '#3f8a3a');
  }, noop],
  /* pickled turnips and cucumbers in a jar */
  pickles: [function (c, x, y, s) {
    var w = s * 0.3, h = s * 0.42;
    paper(c, rect(x - w / 2, y - h, w, h), 'rgba(220,235,240,.55)', 0.6);
    fp(c, [[x - w * 0.45, y - h * 0.8], [x + w * 0.45, y - h * 0.8], [x + w * 0.45, y - s * 0.01], [x - w * 0.45, y - s * 0.01]], 'rgba(240,160,190,.55)');
    for (var i = 0; i < 6; i++) paper(c, rect(x - w * 0.38 + i * w * 0.13, y - h * 0.75 + (i % 2) * s * 0.03, w * 0.09, h * 0.65), i % 3 === 1 ? '#7aa83a' : '#e05a8a', 0.2);
    paper(c, rect(x - w * 0.55, y - h - s * 0.06, w * 1.1, s * 0.07), '#c8a050', 0.4);
    ln(c, [[x - w * 0.35, y - h * 0.9], [x - w * 0.3, y - h * 0.1]], 'rgba(255,255,255,.6)', s * 0.02);
  }, noop],
  /* tabbouleh: parsley, tomato, bulgur */
  tabbouleh: [function (c, x, y, s) {
    var b = bowl(c, x, y, s * 0.7, '#f4f1ea', '#5a9a3a', '#2f6db0');
    sprinkle(c, b.x, b.y - s * 0.01, b.rx * 0.8, b.ry * 0.7, 20, s * 0.014, ['#3f8a3a', '#7ac85a', '#d6402e', '#e8d6a8']);
    lime(c, x + s * 0.32, y - s * 0.02, s * 0.06);
  }, noop]
};
function waffleTop(c, x, y, rx, ry) {
  c.save(); c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.clip(); c.fillStyle = '#d89a4a'; c.fill();
  c.strokeStyle = '#a8662a'; c.lineWidth = 0.7;
  for (var i = -6; i <= 6; i++) { c.beginPath(); c.moveTo(x + i * rx * 0.18 - rx, y - ry * 1.2); c.lineTo(x + i * rx * 0.18 + rx, y + ry * 1.2); c.moveTo(x + i * rx * 0.18 + rx, y - ry * 1.2); c.lineTo(x + i * rx * 0.18 - rx, y + ry * 1.2); c.stroke(); }
  c.restore();
}
function kratipBody(c, x, y, s) {
  var w = s * 0.4, h = s * 0.42;
  ln(c, [[x - w * 0.3, y], [x - w * 0.25, y - h * 0.2]], '#8a6030', s * 0.03); ln(c, [[x + w * 0.3, y], [x + w * 0.25, y - h * 0.2]], '#8a6030', s * 0.03);
  var body = function (q) { q.beginPath(); q.moveTo(x - w / 2, y - h); q.lineTo(x + w / 2, y - h); q.quadraticCurveTo(x + w * 0.58, y - h * 0.25, x + w * 0.32, y - h * 0.08); q.lineTo(x - w * 0.32, y - h * 0.08); q.quadraticCurveTo(x - w * 0.58, y - h * 0.25, x - w / 2, y - h); q.closePath(); };
  paper(c, body, '#cfa055', 0.8);
  c.save(); body(c); c.clip(); c.strokeStyle = 'rgba(120,80,30,.5)'; c.lineWidth = 0.8;
  for (var i = -8; i <= 8; i++) { c.beginPath(); c.moveTo(x + i * w * 0.12, y - h); c.lineTo(x + i * w * 0.12 + h * 0.6, y); c.moveTo(x + i * w * 0.12, y - h); c.lineTo(x + i * w * 0.12 - h * 0.6, y); c.stroke(); }
  c.restore();
  ln(c, [[x - w * 0.5, y - h * 0.55], [x + w * 0.5, y - h * 0.55]], '#8a6030', s * 0.02);
}
function kratipLid(c, x, y, s, t, k) {
  var w = s * 0.4, h = s * 0.42, u = ((t / 1000) / 6.5 + k * 0.31) % 1, lift = u < 0.16 ? Math.sin(u / 0.16 * Math.PI) : 0, ly = y - h - lift * s * 0.14, tilt = lift * 0.25;
  if (lift > 0) { fe(c, x, y - h, w * 0.46, s * 0.04, '#fbf8f0'); steam(c, x, y - h, s * 0.4 * lift, t, k, 2, 0.6 * lift); }
  c.save(); c.translate(x, ly); c.rotate(tilt);
  fp(c, [[-w * 0.55, 0], [w * 0.55, 0], [w * 0.5, -h * 0.32], [-w * 0.5, -h * 0.32]], '#c09048'); fe(c, 0, -h * 0.32, w * 0.5, h * 0.06, '#d8b060');
  c.strokeStyle = 'rgba(120,80,30,.5)'; c.lineWidth = 0.8; for (var i = -3; i <= 3; i++) { c.beginPath(); c.moveTo(i * w * 0.15, 0); c.lineTo(i * w * 0.15 + h * 0.2, -h * 0.3); c.stroke(); }
  c.strokeStyle = '#8a6030'; c.lineWidth = Math.max(0.8, s * 0.015); c.beginPath(); c.arc(0, -h * 0.35, w * 0.35, Math.PI * 1.1, Math.PI * 1.9); c.stroke();
  c.restore();
}
function steamer(c, x, y, w, h) {
  paper(c, rect(x - w / 2, y - h, w, h), '#d2a86a', 0.7);
  ln(c, [[x - w / 2, y - h * 0.25], [x + w / 2, y - h * 0.25]], '#a87838', Math.max(1, h * 0.1)); ln(c, [[x - w / 2, y - h * 0.8], [x + w / 2, y - h * 0.8]], '#a87838', Math.max(1, h * 0.1));
  for (var i = 1; i < 8; i++) ln(c, [[x - w / 2 + i * w / 8, y - h * 0.7], [x - w / 2 + i * w / 8, y - h * 0.35]], 'rgba(140,100,50,.35)', 0.7);
  fe(c, x, y - h, w / 2, h * 0.22, '#e0bc80');
}

/* ---------------------------------------------------------------- the kitchens
   cook: the station (still) and the cook at work (moving); prop: the still part and what
   moves. L: the layout, k0/k1 the cook's corner, sy the station's work top, mx the prop */
function stool(c, x, deck, w, h, col) { paper(c, rect(x - w / 2, deck - h, w, h * 0.18), col, 0.6); ln(c, [[x - w * 0.4, deck - h], [x - w * 0.45, deck]], col, Math.max(1.5, w * 0.12)); ln(c, [[x + w * 0.4, deck - h], [x + w * 0.45, deck]], col, Math.max(1.5, w * 0.12)); }
function counter(c, x0, x1, top, deck, col, front) {
  paper(c, rect(x0, top, x1 - x0, deck - top), col, 1.2);
  paper(c, rect(x0 - 3, top - 4, x1 - x0 + 6, 5), front || '#5a4030', 0.6);
}
function sitP(seat, lean) { return { lean: lean || 0.2, seat: seat, legs: [1.55, -1.75, 1.4, -1.55] }; }
var STAND = { lean: 0.05, legs: [0.08, 0, -0.06, 0] };
function smoke(c, x, y, h, t, k) { c.save(); c.strokeStyle = '#d8d4cc'; c.lineWidth = Math.max(2, h * 0.08); c.lineCap = 'round'; for (var j = 0; j < 2; j++) { var ph = (t / 3000 + j / 2 + k) % 1; c.globalAlpha = 0.35 * Math.sin(ph * Math.PI); c.beginPath(); for (var i = 0; i <= 8; i++) { var f = i / 8; c.lineTo(x + Math.sin(f * 4 - t / 700 + j * 2) * h * 0.12 * (0.3 + f), y - (ph * 0.5 + f * 0.5) * h); } c.stroke(); } c.restore(); }
function sparks(c, x, y, h, t, n) { for (var i = 0; i < n; i++) { var u = (t / 1400 + i / n) % 1, sx = x + Math.sin(i * 2.3 + u * 5) * h * 0.15, sy = y - u * h; c.globalAlpha = 1 - u; fe(c, sx, sy, 1.3, 1.3, i % 2 ? '#ffd27a' : '#ff8a3a'); } c.globalAlpha = 1; }

var COOK = {
  /* a charcoal stove with sai oua on the grill, fanned with a bamboo fan; sticky rice
     steaming in a huad cone over its pot */
  lanna: [function (c, S, L) {
    var hh = S.hh, gx = L.k0 + hh * 0.95, gy = S.deck - hh * 0.36, hx = L.k0 + hh * 1.45;
    stool(c, L.k0 + hh * 0.42, S.deck, hh * 0.22, hh * 0.18, '#7a4a2a');
    paper(c, poly([[gx - hh * 0.22, gy], [gx + hh * 0.22, gy], [gx + hh * 0.17, S.deck], [gx - hh * 0.17, S.deck]]), '#a65a32', 1);
    fp(c, [[gx - hh * 0.07, S.deck], [gx - hh * 0.07, S.deck - hh * 0.12], [gx + hh * 0.07, S.deck - hh * 0.12], [gx + hh * 0.07, S.deck]], '#2a1208');
    ln(c, [[gx - hh * 0.23, gy], [gx + hh * 0.23, gy]], '#3a3a3a', 2);
    var pts = spiral(gx, gy - hh * 0.03, hh * 0.19, 2.4, 0.3, 0.2); ln(c, pts, '#4a1e10', hh * 0.05); ln(c, pts, '#a8462a', hh * 0.038); ln(c, pts.map(function (p) { return [p[0], p[1] - hh * 0.008]; }), '#d07048', hh * 0.012);
    paper(c, poly([[hx - hh * 0.16, S.deck - hh * 0.22], [hx + hh * 0.16, S.deck - hh * 0.22], [hx + hh * 0.13, S.deck], [hx - hh * 0.13, S.deck]]), '#9a5a32', 1);
    paper(c, rect(hx - hh * 0.15, S.deck - hh * 0.42, hh * 0.3, hh * 0.2), '#c8ccd2', 0.8); fe(c, hx, S.deck - hh * 0.42, hh * 0.15, hh * 0.03, '#a8acb4');
    paper(c, poly([[hx - hh * 0.2, S.deck - hh * 0.72], [hx + hh * 0.2, S.deck - hh * 0.72], [hx + hh * 0.05, S.deck - hh * 0.42], [hx - hh * 0.05, S.deck - hh * 0.42]]), '#d8b060', 0.8);
    c.strokeStyle = 'rgba(120,80,30,.5)'; c.lineWidth = 0.8; for (var i = 0; i < 6; i++) { c.beginPath(); c.moveTo(hx - hh * 0.2 + i * hh * 0.08, S.deck - hh * 0.72); c.lineTo(hx - hh * 0.05 + i * hh * 0.02, S.deck - hh * 0.42); c.stroke(); }
    fe(c, hx, S.deck - hh * 0.72, hh * 0.2, hh * 0.035, '#f8f4e8');
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, gx = L.k0 + hh * 0.95, gy = S.deck - hh * 0.36, hx = L.k0 + hh * 1.45, t = S.t;
    glow(c, gx, S.deck - hh * 0.06, hh * 0.12, '255,120,40', 0.7 + 0.25 * Math.sin(t / 140));
    smoke(c, gx, gy - hh * 0.05, hh * 0.9, t, 0); sparks(c, gx, gy - hh * 0.03, hh * 0.5, t, 5);
    steam(c, hx, S.deck - hh * 0.76, hh * 0.45, t, 1, 2);
    var a = Math.sin(t / 220), T = [gx - hh * 0.2, gy - hh * 0.15 + a * hh * 0.03];
    var me = worker(S, L.k0 + hh * 0.42, hh * 0.95, sitP(0.2, 0.3), d, T, [L.k0 + hh * 0.6, S.deck - hh * 0.25]);
    c.save(); c.translate(me.hand[0][0], me.hand[0][1]); c.rotate(0.9 + a * 0.5); fp(c, [[0, -hh * 0.02], [hh * 0.08, -hh * 0.07], [hh * 0.2, -hh * 0.06], [hh * 0.22, hh * 0.04], [hh * 0.08, hh * 0.06], [0, hh * 0.02]], '#d8b46a'); ln(c, [[hh * 0.06, -hh * 0.05], [hh * 0.06, hh * 0.05]], '#a87838', 1); c.restore();
    hat(c, me, 'kerchief', '#c0392b');
  }],
  /* the griddle: a patty flipped high, y = v₀t − ½gt², turning half over in the air */
  american: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#a8adb4', '#3b3b3b');
    for (var i = 0; i < 3; i++) fe(c, x0 + (i + 0.5) * (x1 - x0) / 3, S.deck - hh * 0.22, hh * 0.035, hh * 0.035, '#c0392b');
    ln(c, [[x0 + 4, S.deck - hh * 0.32], [x1 - 4, S.deck - hh * 0.32]], '#8a9098', 1.5);
    fe(c, x0 + (x1 - x0) * 0.72, sy - hh * 0.02, hh * 0.09, hh * 0.022, '#5a2e1a'); fe(c, x0 + (x1 - x0) * 0.92, sy - hh * 0.02, hh * 0.08, hh * 0.02, '#d9a050');
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, px = L.k0 + hh * 1.05, sy = L.sy - hh * 0.02, T = 2.2, u = (S.t / 1000 / T) % 1, fly = u < 0.45, f = u / 0.45;
    var py = fly ? sy - 4 * hh * 0.42 * f * (1 - f) : sy, rot = fly ? Math.PI * f : 0;
    steam(c, L.k0 + hh * 1.5, sy - hh * 0.03, hh * 0.35, S.t, 2, 2, 0.4); steam(c, px, sy, hh * 0.3, S.t, 3, 1, 0.35);
    var sp = fly && f < 0.2 ? [px - hh * 0.05, sy - hh * 0.04 - f * hh * 0.4] : [px - hh * 0.1, sy - hh * 0.1];
    var me = worker(S, L.k0 + hh * 0.38, hh, STAND, d, sp, [L.k0 + hh * 0.7, sy - hh * 0.05]);
    ln(c, [me.hand[0], [me.hand[0][0] + hh * 0.12, me.hand[0][1] + hh * 0.06]], '#3a3a3a', hh * 0.025); fp(c, [[me.hand[0][0] + hh * 0.1, me.hand[0][1] + hh * 0.04], [me.hand[0][0] + hh * 0.22, me.hand[0][1] + hh * 0.07], [me.hand[0][0] + hh * 0.2, me.hand[0][1] + hh * 0.1], [me.hand[0][0] + hh * 0.09, me.hand[0][1] + hh * 0.07]], '#c9ccd2');
    apron(c, me, d, '#f6f6f2'); hat(c, me, 'cap');
    c.save(); c.translate(px, py); c.rotate(rot); fe(c, 0, 0, hh * 0.1, hh * 0.026, '#5a2e1a'); fe(c, 0, -hh * 0.012, hh * 0.08, hh * 0.012, '#7a4a2a'); c.restore();
    if (!fly) for (var i = 0; i < 4; i++) { var g = (S.t / 300 + i / 4) % 1; fe(c, px + (i - 1.5) * hh * 0.05, sy - g * hh * 0.08, 1, 1, 'rgba(255,230,160,' + (1 - g) + ')'); }
  }],
  /* the poffertjes pan: each ball turned over in its dimple in turn */
  dutch: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#f4f6fa', '#2f5fa8');
    for (var i = 0; i < 6; i++) for (var j = 0; j < 2; j++) { var tx = x0 + (i + 0.5) * (x1 - x0) / 6, ty = sy + hh * 0.08 + j * hh * 0.14; paper(c, rect(tx - hh * 0.05, ty, hh * 0.1, hh * 0.1), '#ffffff', 0.2); fe(c, tx, ty + hh * 0.05, hh * 0.025, hh * 0.025, '#2f5fa8'); }
    paper(c, rect(x0 + 4, sy - hh * 0.06, x1 - x0 - 8, hh * 0.05), '#2a2a2a', 0.6);
    for (i = 0; i < 6; i++) fe(c, x0 + 10 + (i + 0.5) * (x1 - x0 - 20) / 6, sy - hh * 0.06, hh * 0.04, hh * 0.012, '#111');
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62 + 10, x1 = L.k1 - 10, sy = L.sy - hh * 0.06, n = 6, cur = Math.floor(S.t / 500) % n, f = (S.t % 500) / 500;
    for (var i = 0; i < n; i++) {
      var bx = x0 + (i + 0.5) * (x1 - x0) / n, ph = i < cur ? 1 : i === cur ? f : 0, done = (Math.floor(S.t / 500 / n) % 2), a = (done ? 1 - ph : ph) * Math.PI, hop = i === cur ? Math.sin(f * Math.PI) * hh * 0.04 : 0;
      var top = Math.cos(a) > 0 ? '#f2dca0' : '#c4823a'; fe(c, bx, sy - hh * 0.03 - hop, hh * 0.042, hh * 0.03 * Math.max(0.25, Math.abs(Math.cos(a))) + hh * 0.01, top);
    }
    var bx2 = x0 + (cur + 0.5) * (x1 - x0) / n, me = worker(S, L.k0 + hh * 0.36, hh, STAND, d, [bx2 - hh * 0.08, sy - hh * 0.12], [L.k0 + hh * 0.7, sy + hh * 0.02]);
    ln(c, [me.hand[0], [bx2 - hh * 0.01, sy - hh * 0.05]], '#9aa0a8', hh * 0.018);
    apron(c, me, d, '#2f5fa8'); hat(c, me, 'cap', '#ffffff'); steam(c, (x0 + x1) / 2, sy - hh * 0.05, hh * 0.35, S.t, 1, 3, 0.35);
  }],
  /* raclette: the heater melts the cut face, the knife scrapes it down onto potatoes */
  swiss: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, rx = x0 + (x1 - x0) * 0.42;
    counter(c, x0, x1, sy, S.deck, '#8a5a32', '#c0262a');
    paper(c, rect(x0 + 4, sy - hh * 0.06, hh * 0.5, hh * 0.05), '#c99a5a', 0.6);
    paper(c, function (q) { q.beginPath(); q.moveTo(rx, sy - hh * 0.4); q.lineTo(rx, sy - hh * 0.07); q.lineTo(rx - hh * 0.3, sy - hh * 0.07); q.quadraticCurveTo(rx - hh * 0.32, sy - hh * 0.4, rx, sy - hh * 0.4); q.closePath(); }, '#d89a3a', 0.8);
    fp(c, [[rx - hh * 0.035, sy - hh * 0.38], [rx, sy - hh * 0.4], [rx, sy - hh * 0.07], [rx - hh * 0.035, sy - hh * 0.08]], '#f4d670');
    paper(c, rect(rx - hh * 0.06, sy - hh * 0.55, hh * 0.24, hh * 0.08), '#3a3a3a', 0.7); ln(c, [[rx + hh * 0.17, sy - hh * 0.5], [rx + hh * 0.17, sy - hh * 0.07]], '#3a3a3a', 3);
    var px = x1 - hh * 0.2; plate(c, px, sy - hh * 0.005, hh * 0.32); [[-0.06, 0], [0.04, -0.01], [-0.01, -0.03]].forEach(function (p) { fe(c, px + p[0] * hh, sy - hh * 0.04 + p[1] * hh, hh * 0.04, hh * 0.028, '#d8b060'); });
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, rx = x0 + (x1 - x0) * 0.42, u = (S.t / 1000 / 3.2) % 1;
    glow(c, rx + hh * 0.04, sy - hh * 0.46, hh * 0.12, '255,90,30', 0.6 + 0.2 * Math.sin(S.t / 200)); ln(c, [[rx - hh * 0.04, sy - hh * 0.47], [rx + hh * 0.16, sy - hh * 0.47]], '#ff6a2a', 2);
    var sc = ease(Math.min(1, u / 0.6)), ky = lerp(sy - hh * 0.38, sy - hh * 0.1, sc);
    fp(c, [[rx, sy - hh * 0.38], [rx + hh * 0.02 + sc * hh * 0.04, sy - hh * 0.38], [rx + hh * 0.03 + sc * hh * 0.1, ky], [rx, ky]], '#f8d850');
    if (u > 0.55) { var g = (u - 0.55) / 0.45; fe(c, rx + hh * 0.14 + g * hh * 0.1, sy - hh * 0.1 + g * g * hh * 0.07, hh * 0.04, hh * 0.015 + g * hh * 0.01, '#f8d850'); }
    var me = worker(S, L.k0 + hh * 0.36, hh, STAND, d, [rx + hh * 0.06, ky - hh * 0.04], [L.k0 + hh * 0.75, sy - hh * 0.05]);
    ln(c, [me.hand[0], [me.hand[0][0] + hh * 0.02, me.hand[0][1] + hh * 0.08]], '#c9ccd2', hh * 0.03);
    apron(c, me, d, '#c0262a'); hat(c, me, 'toque');
    steam(c, x1 - hh * 0.2, sy - hh * 0.06, hh * 0.3, S.t, 2, 2, 0.4);
  }],
  /* meatballs in the pan, the pan shaken, each ball hopping |sin ωt| */
  swedish: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#f2f2ee', '#2a2a2a');
    paper(c, rect(x0 + hh * 0.1, sy + hh * 0.12, x1 - x0 - hh * 0.2, hh * 0.2), '#2a2a2a', 0.5); fe(c, (x0 + x1) / 2, sy + hh * 0.22, hh * 0.06, hh * 0.04, 'rgba(255,170,60,.4)');
    for (var i = 0; i < 3; i++) fe(c, x0 + hh * 0.15 + i * hh * 0.1, sy + hh * 0.05, hh * 0.02, hh * 0.02, '#2a2a2a');
    var px = x1 - hh * 0.18; paper(c, rect(px - hh * 0.12, sy - hh * 0.2, hh * 0.24, hh * 0.2), '#2f5fa8', 0.7); fe(c, px, sy - hh * 0.2, hh * 0.12, hh * 0.025, '#f4ead0');
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, sy = L.sy, sh = Math.sin(S.t / 160) * hh * 0.025, cx = x0 + hh * 0.42 + sh;
    for (var i = 0; i < 3; i++) fp(c, [[cx - hh * 0.06 + i * hh * 0.05, sy], [cx - hh * 0.03 + i * hh * 0.05, sy - hh * 0.04 - Math.abs(Math.sin(S.t / 110 + i)) * hh * 0.02], [cx + i * hh * 0.05, sy]], '#4a7aff');
    ln(c, [[cx - hh * 0.2, sy - hh * 0.04], [cx + hh * 0.2, sy - hh * 0.04]], '#1e1e20', hh * 0.04); fe(c, cx, sy - hh * 0.05, hh * 0.2, hh * 0.03, '#1e1e20');
    for (i = 0; i < 5; i++) { var hop = Math.abs(Math.sin(S.t / 260 + i * 1.3)) * hh * 0.07; fe(c, cx - hh * 0.13 + i * hh * 0.065, sy - hh * 0.09 - hop, hh * 0.032, hh * 0.03, '#7a4220'); fe(c, cx - hh * 0.14 + i * hh * 0.065, sy - hh * 0.1 - hop, hh * 0.01, hh * 0.008, '#b06a3a'); }
    var me = worker(S, L.k0 + hh * 0.3, hh, STAND, d, [cx - hh * 0.36, sy - hh * 0.08], [L.k0 + hh * 0.62, sy - hh * 0.1]);
    ln(c, [me.hand[0], [cx - hh * 0.2, sy - hh * 0.05]], '#1e1e20', hh * 0.03);
    apron(c, me, d, '#f2c94c'); hat(c, me, 'toque'); steam(c, x0 + hh * 0.42, sy - hh * 0.1, hh * 0.35, S.t, 1, 2, 0.4);
  }],
  /* the sushi counter: the knife draws back through the fish in one pull */
  japanese: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#e0c08a', '#2a1e1e');
    ln(c, [[x0 + 4, sy + hh * 0.1], [x1 - 4, sy + hh * 0.1]], '#c8a06a', 1); paper(c, rect(x0 + 6, sy - hh * 0.04, (x1 - x0) * 0.62, hh * 0.035), '#f2e2c0', 0.5);
    var fx = x0 + (x1 - x0) * 0.3; paper(c, poly([[fx - hh * 0.12, sy - hh * 0.04], [fx + hh * 0.14, sy - hh * 0.04], [fx + hh * 0.12, sy - hh * 0.12], [fx - hh * 0.1, sy - hh * 0.11]]), '#f08a5d', 0.4);
    for (var i = 0; i < 5; i++) ln(c, [[fx - hh * 0.08 + i * hh * 0.05, sy - hh * 0.11], [fx - hh * 0.06 + i * hh * 0.05, sy - hh * 0.05]], '#ffd9c0', 0.9);
    var gx = x1 - hh * 0.18; paper(c, rect(gx - hh * 0.14, sy - hh * 0.04, hh * 0.28, hh * 0.03), '#c99a5a', 0.4);
    [-0.08, 0, 0.08].forEach(function (dx, j) { fe(c, gx + dx * hh, sy - hh * 0.06, hh * 0.035, hh * 0.02, '#fbf8f0'); fe(c, gx + dx * hh, sy - hh * 0.075, hh * 0.04, hh * 0.012, ['#f08a5d', '#c8243a', '#f4d03f'][j]); });
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, fx = x0 + (x1 - x0) * 0.3, u = (S.t / 1000 / 1.8) % 1, pull = u < 0.55 ? ease(u / 0.55) : 1 - ease((u - 0.55) / 0.45);
    var hx = lerp(fx + hh * 0.2, fx - hh * 0.02, pull), hy = lerp(sy - hh * 0.16, sy - hh * 0.08, u < 0.55 ? pull : 0);
    var me = worker(S, L.k0 + hh * 0.34, hh, STAND, d, [hx, hy], [fx - hh * 0.14, sy - hh * 0.1]);
    c.save(); c.translate(me.hand[0][0], me.hand[0][1]); c.rotate(0.15); fp(c, [[0, -hh * 0.012], [hh * 0.06, -hh * 0.012], [hh * 0.06, hh * 0.012], [0, hh * 0.012]], '#2a1e1e'); fp(c, [[hh * 0.06, -hh * 0.014], [hh * 0.3, -hh * 0.008], [hh * 0.32, hh * 0.006], [hh * 0.06, hh * 0.014]], '#d8dee6'); c.restore();
    if (u > 0.45 && u < 0.95) { var g = (u - 0.45) / 0.5; fe(c, fx - hh * 0.16 - g * hh * 0.08, sy - hh * 0.06, hh * 0.05, hh * 0.016, '#f08a5d', -0.2); }
    apron(c, me, d, '#2a3e6b'); hat(c, me, 'band');
  }],
  /* the steamer tower on its wok: the cook lifts the lid, steam bursts out */
  chinese: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, wx = x0 + (x1 - x0) * 0.45;
    paper(c, rect(x0, sy, x1 - x0, S.deck - sy), '#9a4a32', 1.2);
    c.strokeStyle = 'rgba(60,20,10,.4)'; c.lineWidth = 0.8; for (var r = 1; r < 5; r++) { c.beginPath(); c.moveTo(x0, sy + r * (S.deck - sy) / 5); c.lineTo(x1, sy + r * (S.deck - sy) / 5); c.stroke(); }
    paper(c, function (q) { q.beginPath(); q.arc(wx, S.deck - hh * 0.04, hh * 0.1, Math.PI, TAU); q.closePath(); }, '#1e0e08', 0.4);
    paper(c, function (q) { q.beginPath(); q.ellipse(wx, sy, hh * 0.24, hh * 0.08, 0, 0, Math.PI); q.closePath(); }, '#2a2a2a', 0.6);
    steamer(c, wx, sy - hh * 0.02, hh * 0.38, hh * 0.12); steamer(c, wx, sy - hh * 0.14, hh * 0.38, hh * 0.12);
    var dx = x1 - hh * 0.12; ln(c, [[dx - hh * 0.15, sy - hh * 0.62], [dx + hh * 0.1, sy - hh * 0.62]], '#5a4030', 2); ln(c, [[dx, sy - hh * 0.62], [dx, sy - hh * 0.55]], '#888', 1.2);
    paper(c, function (q) { q.beginPath(); q.moveTo(dx, sy - hh * 0.55); q.bezierCurveTo(dx + hh * 0.1, sy - hh * 0.5, dx + hh * 0.09, sy - hh * 0.3, dx, sy - hh * 0.26); q.bezierCurveTo(dx - hh * 0.09, sy - hh * 0.3, dx - hh * 0.1, sy - hh * 0.5, dx, sy - hh * 0.55); }, '#8a2e10', 0.6);
    fe(c, dx - hh * 0.025, sy - hh * 0.44, hh * 0.025, hh * 0.05, 'rgba(255,200,140,.45)');
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, wx = x0 + (x1 - x0) * 0.45, u = (S.t / 1000 / 4.6) % 1, op = u < 0.15 ? ease(u / 0.15) : u < 0.55 ? 1 : 1 - ease((u - 0.55) / 0.2);
    op = Math.max(0, op);
    flames(c, wx, S.deck - hh * 0.04, hh * 0.18, hh * 0.08, S.t, 0);
    var top = sy - hh * 0.26, lx = wx - op * hh * 0.12, ly = top - op * hh * 0.18;
    if (op > 0.1) steam(c, wx, top, hh * 0.6, S.t, 2, 3, 0.75 * op); else steam(c, wx, top, hh * 0.3, S.t, 2, 1, 0.3);
    var me = worker(S, L.k0 + hh * 0.34, hh, STAND, d, [lx - hh * 0.02, ly - hh * 0.06], [L.k0 + hh * 0.66, sy - hh * 0.05]);
    c.save(); c.translate(lx, ly); c.rotate(-op * 0.5); paper(c, function (q) { q.beginPath(); q.ellipse(0, 0, hh * 0.2, hh * 0.05, 0, Math.PI, TAU); q.closePath(); }, '#d2a86a', 0.4); fe(c, 0, -hh * 0.05, hh * 0.03, hh * 0.015, '#a87838'); c.restore();
    apron(c, me, d, '#f6f6f2'); hat(c, me, 'cap', '#ffffff');
  }],
  /* the phở pot: the ladle dips and pours over a bowl of noodles */
  vietnamese: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, px = x0 + hh * 0.25;
    counter(c, x0, x1, sy, S.deck, '#3a7a5a', '#c8ccd2');
    paper(c, rect(px - hh * 0.2, sy - hh * 0.42, hh * 0.4, hh * 0.42), '#b8bcc4', 1); fe(c, px, sy - hh * 0.42, hh * 0.2, hh * 0.04, '#c8a060'); ln(c, [[px - hh * 0.18, sy - hh * 0.32], [px + hh * 0.18, sy - hh * 0.32]], '#9aa0a8', 1.5);
    var bx = x1 - hh * 0.2; bowl(c, bx, sy, hh * 0.28, '#f6f2ea', '#fbf8ee', '#2f6db0');
    for (var i = 0; i < 3; i++) paper(c, E(bx + hh * 0.2, sy - hh * 0.02 - i * hh * 0.03, hh * 0.08, hh * 0.02), '#f6f2ea', 0.2);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, px = x0 + hh * 0.25, bx = x1 - hh * 0.2, u = (S.t / 1000 / 3.4) % 1;
    var m = u < 0.25 ? 0 : u < 0.5 ? ease((u - 0.25) / 0.25) : u < 0.8 ? 1 : 1 - ease((u - 0.8) / 0.2), dip = u < 0.25 ? Math.sin(u / 0.25 * Math.PI) : 0;
    var lx = lerp(px, bx - hh * 0.06, m), ly = lerp(sy - hh * 0.42 + dip * hh * 0.12, sy - hh * 0.2, m);
    steam(c, px, sy - hh * 0.46, hh * 0.6, S.t, 0, 3);
    var me = worker(S, L.k0 + hh * 0.3, hh, STAND, d, [lx - hh * 0.04, ly - hh * 0.22], [L.k0 + hh * 0.6, sy - hh * 0.05]);
    ln(c, [me.hand[0], [lx, ly]], '#9aa0a8', hh * 0.02); fe(c, lx, ly, hh * 0.05, hh * 0.025, '#9aa0a8');
    if (u > 0.55 && u < 0.8) { ln(c, [[lx + hh * 0.04, ly], [lx + hh * 0.06, sy - hh * 0.12]], 'rgba(220,180,110,.85)', hh * 0.015); steam(c, bx, sy - hh * 0.1, hh * 0.3, S.t, 1, 2, 0.5); }
    hat(c, me, 'cone');
  }],
  /* pulled tea: poured from high to low in a long arc, y = y₀ + g(x/v)²/2 */
  burmese: [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#7a4a2a', '#4a2a14');
    var kx = x1 - hh * 0.2; paper(c, E(kx, sy - hh * 0.12, hh * 0.13, hh * 0.11), '#c8ccd2', 0.8); ln(c, [[kx + hh * 0.1, sy - hh * 0.14], [kx + hh * 0.2, sy - hh * 0.24]], '#c8ccd2', hh * 0.03); fe(c, kx, sy - hh * 0.23, hh * 0.03, hh * 0.02, '#2a2a2a');
    for (var i = 0; i < 3; i++) { var gx = x0 + hh * 0.5 + i * hh * 0.09; glass(c, gx, sy, hh * 0.07, hh * 0.1, '#c8925a', 0.8); }
    paper(c, rect(x0 + hh * 0.1, sy - hh * 0.12, hh * 0.08, hh * 0.12), '#e8e2d0', 0.4); ln(c, [[x0 + hh * 0.1, sy - hh * 0.07], [x0 + hh * 0.18, sy - hh * 0.07]], '#2f6db0', hh * 0.03);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, sy = L.sy, up = 0.5 + 0.5 * Math.sin(S.t / 700), hiY = sy - hh * (0.45 + 0.25 * up), loX = x0 + hh * 0.18;
    var lo = [loX, sy - hh * 0.06], hi = [loX - hh * 0.05, hiY];
    var me = worker(S, L.k0 + hh * 0.3, hh, STAND, d, hi, lo);
    paper(c, poly([[lo[0] - hh * 0.05, lo[1] - hh * 0.1], [lo[0] + hh * 0.05, lo[1] - hh * 0.1], [lo[0] + hh * 0.04, lo[1] + hh * 0.04], [lo[0] - hh * 0.04, lo[1] + hh * 0.04]]), '#c8ccd2', 0.3);
    c.save(); c.translate(hi[0] + hh * 0.03, hi[1]); c.rotate(0.9); fp(c, [[-hh * 0.05, -hh * 0.08], [hh * 0.05, -hh * 0.08], [hh * 0.04, hh * 0.06], [-hh * 0.04, hh * 0.06]], '#c8ccd2'); c.restore();
    var sx = hi[0] + hh * 0.09, sY = hi[1] + hh * 0.02, ex = lo[0] + hh * 0.01, eY = lo[1] - hh * 0.1;
    c.strokeStyle = 'rgba(190,130,70,.9)'; c.lineWidth = Math.max(1.2, hh * 0.016); c.beginPath(); for (var i = 0; i <= 12; i++) { var f = i / 12; c.lineTo(lerp(sx, ex, Math.sqrt(f)), lerp(sY, eY, f)); } c.stroke();
    sprinkle(c, lo[0], lo[1] - hh * 0.1, hh * 0.04, hh * 0.01, 4, hh * 0.01, ['#f2e2c0']);
    steam(c, lo[0], lo[1] - hh * 0.12, hh * 0.3, S.t, 1, 1, 0.5);
  }],
  /* the wok tossed: noodles thrown up, flames leaping when it tips */
  'central-thai': [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#5a6a7a', '#2a2a2a');
    var bx = x1 - hh * 0.16; [['#f2ead8', 0], ['#f08a5d', 1], ['#e8d090', 2]].forEach(function (b, i) { bowl(c, bx - (i % 2) * hh * 0.12, sy - (i === 2 ? hh * 0.1 : 0), hh * 0.16, '#f4f1ea', b[0]); });
    paper(c, rect(x0 + hh * 0.06, sy - hh * 0.22, hh * 0.06, hh * 0.22), '#7a3a1a', 0.4);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, sy = L.sy, wx = x0 + hh * 0.42, u = (S.t / 1000 / 1.5) % 1, tip = Math.sin(u * TAU) * 0.18, wy = sy - hh * 0.08;
    flames(c, wx, sy, hh * 0.3, hh * (0.08 + Math.max(0, tip) * 0.6), S.t, 0);
    var hx = wx - hh * 0.38, hy = wy - hh * 0.04 - tip * hh * 0.2;
    var me = worker(S, L.k0 + hh * 0.26, hh, STAND, d, [hx, hy], [wx - hh * 0.05, wy - hh * 0.2]);
    ln(c, [me.hand[1], [wx, wy - hh * 0.05]], '#9aa0a8', hh * 0.02);
    c.save(); c.translate(wx, wy); c.rotate(tip); paper(c, function (q) { q.beginPath(); q.ellipse(0, 0, hh * 0.2, hh * 0.08, 0, 0, Math.PI); q.closePath(); }, '#2a2a2a', 0.4); ln(c, [[-hh * 0.2, 0], [-hh * 0.36, -hh * 0.03]], '#5a4030', hh * 0.03); c.restore();
    var g = (u + 0.75) % 1;
    if (g < 0.5) { var ff = g / 0.5; for (var i = 0; i < 5; i++) { var nx = wx + (i - 2) * hh * 0.04 + ff * hh * 0.05, ny = wy - hh * 0.04 - 4 * hh * 0.22 * ff * (1 - ff) * (0.7 + i * 0.08); c.strokeStyle = i === 2 ? '#f2784a' : '#e0a050'; c.lineWidth = hh * 0.018; c.beginPath(); c.arc(nx, ny, hh * 0.025, 0.4 + i, 2.4 + i); c.stroke(); } }
    hat(c, me, 'kerchief', '#2f6db0');
  }],
  /* the krok and its pestle, pounding y = |sin ωt|; a grill of gai yang smoking behind */
  isaan: [function (c, S, L) {
    var hh = S.hh, kx = L.k0 + hh * 0.9, gx = L.k0 + hh * 1.48;
    stool(c, L.k0 + hh * 0.42, S.deck, hh * 0.22, hh * 0.16, '#7a4a2a');
    paper(c, poly([[gx - hh * 0.22, S.deck - hh * 0.42], [gx + hh * 0.22, S.deck - hh * 0.42], [gx + hh * 0.2, S.deck - hh * 0.36], [gx - hh * 0.2, S.deck - hh * 0.36]]), '#3a3a3a', 0.6);
    ln(c, [[gx - hh * 0.18, S.deck - hh * 0.36], [gx - hh * 0.2, S.deck]], '#3a3a3a', 2); ln(c, [[gx + hh * 0.18, S.deck - hh * 0.36], [gx + hh * 0.2, S.deck]], '#3a3a3a', 2);
    [-0.1, 0.1].forEach(function (dx) { var cx = gx + dx * hh; paper(c, E(cx, S.deck - hh * 0.48, hh * 0.08, hh * 0.06), '#b8601e', 0.4); ln(c, [[cx - hh * 0.02, S.deck - hh * 0.36], [cx - hh * 0.02, S.deck - hh * 0.62]], '#d8b878', 1.5); ln(c, [[cx + hh * 0.02, S.deck - hh * 0.36], [cx + hh * 0.02, S.deck - hh * 0.62]], '#d8b878', 1.5); });
    paper(c, function (q) { q.beginPath(); q.moveTo(kx - hh * 0.16, S.deck - hh * 0.4); q.lineTo(kx + hh * 0.16, S.deck - hh * 0.4); q.quadraticCurveTo(kx + hh * 0.14, S.deck - hh * 0.2, kx + hh * 0.07, S.deck - hh * 0.12); q.lineTo(kx + hh * 0.09, S.deck); q.lineTo(kx - hh * 0.09, S.deck); q.lineTo(kx - hh * 0.07, S.deck - hh * 0.12); q.quadraticCurveTo(kx - hh * 0.14, S.deck - hh * 0.2, kx - hh * 0.16, S.deck - hh * 0.4); q.closePath(); }, '#b8683a', 1);
    fe(c, kx, S.deck - hh * 0.4, hh * 0.16, hh * 0.035, '#7a3a1a'); sprinkle(c, kx, S.deck - hh * 0.41, hh * 0.12, hh * 0.02, 8, hh * 0.012, ['#c8e098', '#e0402a', '#e8c890']);
    paper(c, E(kx - hh * 0.32, S.deck - hh * 0.05, hh * 0.1, hh * 0.05), '#c8e098', 0.4); paper(c, E(kx + hh * 0.26, S.deck - hh * 0.04, hh * 0.06, hh * 0.04), '#4f9a3c', 0.3);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, kx = L.k0 + hh * 0.9, gx = L.k0 + hh * 1.48, top = S.deck - hh * 0.4, w = Math.abs(Math.sin(S.t / 1000 * Math.PI * 1.6)), py = top - hh * 0.06 - w * hh * 0.18;
    smoke(c, gx, S.deck - hh * 0.55, hh * 0.8, S.t, 0.3);
    var me = worker(S, L.k0 + hh * 0.42, hh * 0.95, sitP(0.18, 0.3), d, [kx - hh * 0.02, py - hh * 0.2], [kx - hh * 0.15, top - hh * 0.04]);
    paper(c, rect(kx - hh * 0.025, py - hh * 0.28, hh * 0.05, hh * 0.34), '#8a5a2a', 0.3);
    if (w < 0.25) for (var i = 0; i < 4; i++) { var f = (S.t / 200 + i * 0.25) % 1; fe(c, kx + (i - 1.5) * hh * 0.06 * (1 + f), top - f * hh * 0.1, hh * 0.012, hh * 0.012, i % 2 ? '#c8e098' : '#e0402a'); }
    hat(c, me, 'kerchief', '#c0392b');
  }],
  /* the roti thrown: a disc turning in the air, its height r·|cos θ|, landing on the griddle */
  'southern-thai': [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy;
    counter(c, x0, x1, sy, S.deck, '#c8ccd2', '#2a2a2a');
    paper(c, rect(x0 + hh * 0.06, sy + hh * 0.06, x1 - x0 - hh * 0.12, hh * 0.2), 'rgba(220,240,250,.7)', 0.3);
    [['#f2d03a', 0.15], ['#fffaf0', 0.4], ['#f2e6c9', 0.65]].forEach(function (b) { fe(c, x0 + (x1 - x0) * b[1], sy + hh * 0.18, hh * 0.05, hh * 0.04, b[0]); });
    paper(c, E((x0 + x1) / 2 + hh * 0.1, sy - hh * 0.02, hh * 0.26, hh * 0.035), '#1e1e20', 0.5);
    paper(c, rect(x1 - hh * 0.18, sy - hh * 0.2, hh * 0.08, hh * 0.18), '#e8e2d0', 0.4); ln(c, [[x1 - hh * 0.18, sy - hh * 0.12], [x1 - hh * 0.1, sy - hh * 0.12]], '#c0392b', hh * 0.03);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, gx = (x0 + x1) / 2 + hh * 0.1, u = (S.t / 1000 / 2.4) % 1;
    var fly = u < 0.5, f = u / 0.5, rx = lerp(x0 + hh * 0.05, gx, fly ? f : 1), ry = fly ? sy - hh * 0.2 - 4 * hh * 0.35 * f * (1 - f) : sy - hh * 0.04, th = fly ? f * Math.PI * 3 : Math.PI * 0.5;
    var hands = fly && f < 0.3 ? [rx - hh * 0.02, ry + hh * 0.02] : [x0 + hh * 0.05, sy - hh * 0.25];
    var me = worker(S, L.k0 + hh * 0.3, hh, STAND, d, hands, [hands[0] - hh * 0.05, hands[1] + hh * 0.03]);
    if (!fly) { fe(c, gx, sy - hh * 0.045, hh * 0.18, hh * 0.022, '#e8b660'); sprinkle(c, gx, sy - hh * 0.045, hh * 0.14, hh * 0.012, 5, hh * 0.01, ['#a8662a']); steam(c, gx, sy - hh * 0.06, hh * 0.3, S.t, 1, 2, 0.4); }
    else { fe(c, rx, ry, hh * 0.2, Math.max(1.2, hh * 0.2 * Math.abs(Math.cos(th)) * 0.45), 'rgba(250,240,215,.95)'); }
    apron(c, me, d, '#f6f6f2'); hat(c, me, 'kopiah');
  }],
  /* the iron pot of oil: bubbles rise and burst, tongs lift a drumstick and lower it back */
  'soul-food': [function (c, S, L) {
    var hh = S.hh, x0 = L.k0 + hh * 0.62, x1 = L.k1, sy = L.sy, px = x0 + hh * 0.36;
    counter(c, x0, x1, sy, S.deck, '#2a2a2a', '#5a5a5a');
    paper(c, rect(x0 + hh * 0.08, sy + hh * 0.1, x1 - x0 - hh * 0.16, hh * 0.22), '#3a3a3a', 0.4); fe(c, x0 + hh * 0.3, sy + hh * 0.21, hh * 0.02, hh * 0.02, '#c8a050');
    paper(c, function (q) { q.beginPath(); q.moveTo(px - hh * 0.22, sy - hh * 0.2); q.lineTo(px + hh * 0.22, sy - hh * 0.2); q.lineTo(px + hh * 0.19, sy); q.lineTo(px - hh * 0.19, sy); q.closePath(); }, '#1e1e20', 0.8);
    fe(c, px, sy - hh * 0.2, hh * 0.21, hh * 0.035, '#c88a2a');
    var rx = x1 - hh * 0.2; paper(c, rect(rx - hh * 0.16, sy - hh * 0.03, hh * 0.32, hh * 0.03), '#9aa0a8', 0.3);
    [-0.09, 0.02, 0.11].forEach(function (dx) { paper(c, E(rx + dx * hh, sy - hh * 0.07, hh * 0.05, hh * 0.04, 0.3), '#b8681e', 0.2); });
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.62, sy = L.sy, px = x0 + hh * 0.36, oy = sy - hh * 0.2, u = (S.t / 1000 / 3) % 1, up = u < 0.3 ? 0 : u < 0.5 ? ease((u - 0.3) / 0.2) : u < 0.75 ? 1 : 1 - ease((u - 0.75) / 0.25);
    for (var i = 0; i < 7; i++) { var g = (S.t / 900 + i / 7) % 1; c.strokeStyle = 'rgba(255,230,160,' + (1 - g) + ')'; c.lineWidth = 1; c.beginPath(); c.arc(px + (i - 3) * hh * 0.05, oy - g * hh * 0.02, hh * (0.01 + g * 0.02), 0, TAU); c.stroke(); }
    var dy = oy - up * hh * 0.28, dx = px + hh * 0.02;
    if (up > 0.05) { fe(c, dx, dy, hh * 0.05, hh * 0.07, '#b8681e', 0.4); sprinkle(c, dx, dy, hh * 0.04, hh * 0.05, 5, hh * 0.01, ['#e0a040', '#8a4a12']); for (i = 0; i < 2; i++) fe(c, dx + (i - 0.5) * hh * 0.02, dy + hh * 0.07 + ((S.t / 300 + i * 0.5) % 1) * hh * 0.1, 1, 1.5, '#e8b040'); }
    var me = worker(S, L.k0 + hh * 0.3, hh, STAND, d, [dx - hh * 0.14, dy - hh * 0.1], [L.k0 + hh * 0.6, sy - hh * 0.05]);
    ln(c, [me.hand[0], [dx - hh * 0.02, dy - hh * 0.02]], '#9aa0a8', hh * 0.02); ln(c, [[me.hand[0][0], me.hand[0][1] + hh * 0.02], [dx - hh * 0.02, dy + hh * 0.02]], '#9aa0a8', hh * 0.02);
    steam(c, px, oy, hh * 0.4, S.t, 2, 2, 0.4);
    apron(c, me, d, '#f6f6f2'); hat(c, me, 'kerchief', '#2f6db0');
  }],
  /* the falafel cart under its own Lanna roof: the scoop drops each ball into the oil,
     y = ½gt², and the oil bubbles round it */
  falafel: [function (c, S, L, N) {
    var hh = S.hh, x0 = L.k0 + hh * 0.6, x1 = L.k1 + hh * 0.05, sy = L.sy, fx = x0 + hh * 0.32;
    paper(c, rect(x0, sy, x1 - x0, S.deck - sy - hh * 0.1), '#2f6db0', 1.2);
    for (var i = 0; i < 4; i++) { var tx = x0 + (i + 0.5) * (x1 - x0) / 4; c.strokeStyle = '#f2e6c9'; c.lineWidth = 1; c.beginPath(); for (var p = 0; p < 8; p++) { var a = p / 8 * TAU, r = p % 2 ? hh * 0.04 : hh * 0.08; c.lineTo(tx + Math.cos(a) * r, sy + hh * 0.17 + Math.sin(a) * r); } c.closePath(); c.stroke(); }
    [x0 + hh * 0.15, x1 - hh * 0.15].forEach(function (wx) { paper(c, E(wx, S.deck - hh * 0.1, hh * 0.1, hh * 0.1), '#3a2a1a', 0.6); fe(c, wx, S.deck - hh * 0.1, hh * 0.03, hh * 0.03, '#c8a050'); for (var s = 0; s < 6; s++) ln(c, [[wx, S.deck - hh * 0.1], [wx + Math.cos(s) * hh * 0.08, S.deck - hh * 0.1 + Math.sin(s) * hh * 0.08]], '#c8a050', 0.8); });
    ln(c, [[x0 + 3, sy], [x0 + 3, sy - hh * 0.62]], '#7a4a2a', 3); ln(c, [[x1 - 3, sy], [x1 - 3, sy - hh * 0.62]], '#7a4a2a', 3);
    lannaRoof(c, (x0 + x1) / 2, x1 - x0 + hh * 0.1, sy - hh * 0.6, hh * 0.3, null, S.night);
    paper(c, rect(fx - hh * 0.17, sy - hh * 0.14, hh * 0.34, hh * 0.14), '#3a3a3a', 0.6); fe(c, fx, sy - hh * 0.14, hh * 0.16, hh * 0.03, '#c89a2a');
    var bx = x1 - hh * 0.2; bowl(c, bx, sy, hh * 0.22, '#f4f1ea', '#7aa83a'); paper(c, E(bx - hh * 0.02, sy - hh * 0.2, hh * 0.1, hh * 0.04), '#e8d4a8', 0.3);
  }, function (S, L, d, C) {
    var c = S.c, hh = S.hh, x0 = L.k0 + hh * 0.6, x1 = L.k1 + hh * 0.05, sy = L.sy, fx = x0 + hh * 0.32, oy = sy - hh * 0.14, bx = x1 - hh * 0.2, u = (S.t / 1000 / 2) % 1;
    var m = u < 0.35 ? ease(u / 0.35) : u < 0.55 ? 1 : 1 - ease((u - 0.55) / 0.45), sx = lerp(bx - hh * 0.05, fx + hh * 0.02, m), sY = sy - hh * 0.28 - Math.sin(m * Math.PI) * hh * 0.08;
    var me = worker(S, L.k0 + hh * 0.28, hh, STAND, d, [sx - hh * 0.08, sY], [L.k0 + hh * 0.62, sy - hh * 0.05]);
    ln(c, [me.hand[0], [sx, sY + hh * 0.02]], '#c9ccd2', hh * 0.02); fe(c, sx + hh * 0.02, sY + hh * 0.03, hh * 0.035, hh * 0.025, '#c9ccd2');
    if (u < 0.36) fe(c, sx + hh * 0.02, sY + hh * 0.01, hh * 0.028, hh * 0.026, '#7aa83a');
    else if (u < 0.5) { var g = (u - 0.36) / 0.14; fe(c, fx + hh * 0.04, lerp(sY + hh * 0.03, oy, g * g), hh * 0.028, hh * 0.026, '#7aa83a'); }
    for (var i = 0; i < 6; i++) { var b = (S.t / 700 + i / 6) % 1; c.strokeStyle = 'rgba(255,240,180,' + (1 - b) + ')'; c.lineWidth = 1; c.beginPath(); c.arc(fx + (i - 2.5) * hh * 0.05, oy - b * hh * 0.015, hh * (0.008 + b * 0.015), 0, TAU); c.stroke(); }
    [-0.08, 0.06].forEach(function (dx, j) { fe(c, fx + dx * hh, oy - hh * 0.01 - Math.abs(Math.sin(S.t / 400 + j)) * hh * 0.01, hh * 0.028, hh * 0.022, '#6b3f1c'); });
    steam(c, fx, oy, hh * 0.35, S.t, 1, 2, 0.35); hat(c, me, 'cap', '#f6f6f2');
  }]
};

/* ---------------------------------------------------------------- the props, Lanna-fied */
function pendulum(t, L, k) { return 0.22 * Math.cos(Math.sqrt(9.8 / Math.max(0.3, L)) * t / 1000 + k); }
function postArm(c, S, x, top, reach, night) {
  var hh = S.hh, wood = night ? '#5a3a24' : '#7a4a2a';
  paper(c, rect(x - hh * 0.035, top, hh * 0.07, S.deck - top), wood, 1);
  paper(c, rect(x - hh * 0.04, top, reach + hh * 0.08, hh * 0.05), wood, 0.8);
  ln(c, [[x, top + hh * 0.32], [x + hh * 0.28, top + hh * 0.04]], wood, Math.max(1.5, hh * 0.03));
  var ex = x + reach + hh * 0.04; c.strokeStyle = '#e8b84a'; c.lineWidth = Math.max(1.2, hh * 0.025); c.beginPath(); c.arc(ex, top - hh * 0.05, hh * 0.07, Math.PI * 0.5, Math.PI * 2.2); c.stroke();
  kalae(c, x, top, hh * 0.2);
  laiKham(c, x - hh * 0.03, x + hh * 0.03, S.deck - hh * 0.6, hh * 0.05);
}
function hangLantern(c, x, y, len, th, draw) { var lx = x + Math.sin(th) * len, ly = y + Math.cos(th) * len; ln(c, [[x, y], [lx, ly]], 'rgba(40,20,30,.8)', 1); draw(lx, ly, th); }
function khomDao(c, x, y, r, rot, night) {   /* the Lanna star lantern, turning: x' = x·cos ωt */
  if (night) glow(c, x, y, r * 2.6, '255,170,80', 0.55);
  var cs = Math.cos(rot), pts = [];
  for (var i = 0; i < 10; i++) { var a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr * (0.35 + 0.65 * Math.abs(cs)), y + Math.sin(a) * rr]); }
  fp(c, pts, cs > 0 ? '#e8402a' : '#c8302a'); fp(c, pts.map(function (p) { return [x + (p[0] - x) * 0.6, y + (p[1] - y) * 0.6]; }), night ? '#ffd27a' : '#f2c94c');
  for (i = 0; i < 5; i++) ln(c, [[x + (i - 2) * r * 0.12, y + r * 0.5], [x + (i - 2) * r * 0.14, y + r * 1.2]], i % 2 ? '#f2c94c' : '#e8402a', 1);
}
var PROP = {
  /* a bamboo post with khom dao, the star lanterns, turning */
  lanna: [function (c, S, L) { postArm(c, S, L.mx - S.hh * 0.45, S.deck - S.hh * 1.75, S.hh * 0.9, S.night); },
    function (S, L) {
      var c = S.c, hh = S.hh, x = L.mx - hh * 0.45, top = S.deck - hh * 1.72;
      [[0.3, 0.42, 0.24], [0.62, 0.2, 0.15], [0.86, 0.5, 0.13]].forEach(function (p, i) { hangLantern(c, x + hh * p[0], top, hh * p[1], pendulum(S.t, 1.2, i * 2) * 0.4, function (lx, ly) { khomDao(c, lx, ly + hh * p[2], hh * p[2], S.t / 1800 + i, S.night); }); });
    }],
  /* a roadside EAT sign, its bulbs chasing round, under a Lanna roof */
  american: [function (c, S, L) {
    var hh = S.hh, x = L.mx, top = S.deck - hh * 1.12, w = hh * 1.1, h = hh * 0.42;
    paper(c, rect(x - hh * 0.04, top, hh * 0.08, S.deck - top), '#8a9098', 1);
    paper(c, rect(x - w / 2, top - h, w, h), '#c0392b', 1.2); paper(c, rect(x - w / 2 + 4, top - h + 4, w - 8, h - 8), '#a8242a', 0.3);
    lannaRoof(c, x, w * 1.05, top - h, hh * 0.3, '#2f6db0', S.night);
    c.font = '900 ' + Math.round(h * 0.55) + 'px Georgia,serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fff6d8'; c.fillText('EAT', x - w * 0.12, top - h * 0.5 + 1);
    c.font = '800 ' + Math.round(h * 0.34) + 'px "Sarabun",system-ui,sans-serif'; c.fillStyle = '#f2c94c'; c.fillText('กิน', x + w * 0.3, top - h * 0.48);
    paper(c, poly([[x - hh * 0.04, top + hh * 0.3], [x - hh * 0.5, top + hh * 0.3], [x - hh * 0.5, top + hh * 0.22], [x - hh * 0.68, top + hh * 0.38], [x - hh * 0.5, top + hh * 0.54], [x - hh * 0.5, top + hh * 0.46], [x - hh * 0.04, top + hh * 0.46]]), '#f2c94c', 0.8);
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, top = S.deck - hh * 1.12, w = hh * 1.1, h = hh * 0.42, n = 18, step = Math.floor(S.t / 160);
    for (var i = 0; i < n; i++) { var f = i / n, px, py; if (f < 0.35) { px = x - w / 2 + f / 0.35 * w; py = top - h; } else if (f < 0.5) { px = x + w / 2; py = top - h + (f - 0.35) / 0.15 * h; } else if (f < 0.85) { px = x + w / 2 - (f - 0.5) / 0.35 * w; py = top; } else { px = x - w / 2; py = top - (f - 0.85) / 0.15 * h; }
      var on = (i + step) % 3 === 0; if (on && S.night) glow(c, px, py, 6, '255,220,120', 0.6); fe(c, px, py, 1.8, 1.8, on ? '#fff6c0' : '#8a6a3a'); }
    for (i = 0; i < 6; i++) { var on2 = (step + i) % 6 < 2, ax = x - hh * 0.08 - i * hh * 0.08; if (on2 && S.night) glow(c, ax, top + hh * 0.38, 6, '255,220,120', 0.6); fe(c, ax, top + hh * 0.38, 1.8, 1.8, on2 ? '#fff6c0' : '#a8862a'); }
  }],
  /* a windmill under a Lanna roof, its sails turning θ = ωt; tulips at its foot */
  dutch: [function (c, S, L) {
    var hh = S.hh, x = L.mx, base = S.deck, top = S.deck - hh * 1.15;
    paper(c, poly([[x - hh * 0.3, base], [x + hh * 0.3, base], [x + hh * 0.18, top], [x - hh * 0.18, top]]), S.night ? '#4a4a52' : '#6a6a72', 1.4);
    fp(c, [[x - hh * 0.06, base], [x - hh * 0.06, base - hh * 0.2], [x + hh * 0.06, base - hh * 0.2], [x + hh * 0.06, base]], '#3a2a1a');
    fe(c, x, top + hh * 0.35, hh * 0.04, hh * 0.05, S.night ? '#ffd27a' : '#cfe3e8');
    paper(c, rect(x - hh * 0.32, base - hh * 0.5, hh * 0.64, hh * 0.04), '#7a4a2a', 0.6);
    lannaRoof(c, x, hh * 0.5, top, hh * 0.32, null, S.night);
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, hub = [x, S.deck - hh * 1.05], th = S.t / 1000 * 0.9, R = hh * 0.55;
    for (var i = 0; i < 4; i++) {
      var a = th + i * Math.PI / 2, ux = Math.cos(a), uy = Math.sin(a), nx = -uy, ny = ux, w = hh * 0.1;
      ln(c, [hub, [hub[0] + ux * R, hub[1] + uy * R]], '#5a4030', 2.2);
      var p0 = [hub[0] + ux * R * 0.25, hub[1] + uy * R * 0.25], p1 = [hub[0] + ux * R, hub[1] + uy * R];
      fp(c, [p0, p1, [p1[0] + nx * w, p1[1] + ny * w], [p0[0] + nx * w, p0[1] + ny * w]], 'rgba(242,230,201,.8)');
      for (var k = 1; k < 5; k++) { var f = 0.25 + k * 0.15; ln(c, [[hub[0] + ux * R * f, hub[1] + uy * R * f], [hub[0] + ux * R * f + nx * w, hub[1] + uy * R * f + ny * w]], '#8a6a4a', 0.8); }
    }
    fe(c, hub[0], hub[1], hh * 0.04, hh * 0.04, '#e8b84a');
    for (i = 0; i < 7; i++) { var tx = x - hh * 0.6 + i * hh * 0.2, sw = Math.sin(S.t / 900 + i) * 0.15, ty = S.deck + hh * 0.06; ln(c, [[tx, ty], [tx + sw * hh * 0.3, ty - hh * 0.2]], '#3f8a3a', 1.4); fp(c, [[tx + sw * hh * 0.3 - hh * 0.035, ty - hh * 0.2], [tx + sw * hh * 0.3 - hh * 0.04, ty - hh * 0.27], [tx + sw * hh * 0.3, ty - hh * 0.24], [tx + sw * hh * 0.3 + hh * 0.04, ty - hh * 0.27], [tx + sw * hh * 0.3 + hh * 0.035, ty - hh * 0.2]], ['#e0283c', '#f2c94c', '#ff7aa8', '#ff8a2a'][i % 4]); }
  }],
  /* the Alps cut from paper, a cowbell on a woven Lanna strap swinging, θ = θ₀·cos(√(g/L)·t) */
  swiss: [function (c, S, L) {
    var hh = S.hh, x = L.mx, b = S.deck;
    paper(c, poly([[x - hh * 0.75, b], [x - hh * 0.35, b - hh * 1.05], [x - hh * 0.22, b - hh * 0.9], [x - hh * 0.05, b - hh * 1.5], [x + hh * 0.15, b - hh * 1.1], [x + hh * 0.3, b - hh * 1.2], [x + hh * 0.7, b]]), S.night ? '#3a4a6a' : '#7a8aa8', 1.6);
    fp(c, [[x - hh * 0.46, b - hh * 0.85], [x - hh * 0.35, b - hh * 1.05], [x - hh * 0.25, b - hh * 0.88], [x - hh * 0.32, b - hh * 0.92], [x - hh * 0.38, b - hh * 0.86]], '#f6f8fc');
    fp(c, [[x - hh * 0.16, b - hh * 1.25], [x - hh * 0.05, b - hh * 1.5], [x + hh * 0.08, b - hh * 1.22], [x, b - hh * 1.28], [x - hh * 0.06, b - hh * 1.2]], '#f6f8fc');
    paper(c, poly([[x - hh * 0.75, b], [x - hh * 0.3, b - hh * 0.35], [x + hh * 0.1, b - hh * 0.2], [x + hh * 0.7, b]]), S.night ? '#1d3a26' : '#4f8a4a', 1.2);
    postArm(c, S, x + hh * 0.3, b - hh * 1.0, hh * 0.35, S.night);
  }, function (S, L) {
    var c = S.c, hh = S.hh, px = L.mx + hh * 0.55, py = S.deck - hh * 0.97, Ls = hh * 0.35, th = pendulum(S.t, 0.6, 0) * 1.3;
    var bx = px + Math.sin(th) * Ls, by = py + Math.cos(th) * Ls;
    ln(c, [[px, py], [bx, by]], '#c0262a', hh * 0.06); for (var i = 1; i < 4; i++) fe(c, lerp(px, bx, i / 4), lerp(py, by, i / 4), hh * 0.015, hh * 0.015, '#f2c94c');
    c.save(); c.translate(bx, by); c.rotate(-th); paper(c, poly([[-hh * 0.08, 0], [hh * 0.08, 0], [hh * 0.12, hh * 0.22], [-hh * 0.12, hh * 0.22]]), '#c8a040', 0.6); fe(c, 0, hh * 0.24, hh * 0.03, hh * 0.03, '#5a4020'); ln(c, [[-hh * 0.1, hh * 0.1], [hh * 0.1, hh * 0.1]], '#e8d070', 1); c.restore();
    if (Math.abs(th) > 0.24) { c.strokeStyle = 'rgba(255,240,180,.7)'; c.lineWidth = 1.2; for (i = 1; i < 3; i++) { c.beginPath(); c.arc(bx, by + hh * 0.15, hh * 0.1 * i, th > 0 ? -0.6 : Math.PI - 0.6, th > 0 ? 0.6 : Math.PI + 0.6); c.stroke(); } }
  }],
  /* a Dala horse painted in gold lai kham, rocking θ = θ₀·sin ωt */
  swedish: [function (c, S, L) {
    var hh = S.hh, x = L.mx, b = S.deck;
    paper(c, poly([[x - hh * 0.5, b], [x + hh * 0.5, b], [x + hh * 0.42, b - hh * 0.12], [x - hh * 0.42, b - hh * 0.12]]), '#e8b84a', 1);
    laiKham(c, x - hh * 0.42, x + hh * 0.42, b - hh * 0.06, hh * 0.035, '#a8242a');
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, b = S.deck - hh * 0.12, th = 0.07 * Math.sin(S.t / 900), u = hh * 0.9;
    c.save(); c.translate(x, b); c.rotate(th);
    var horse = [[-0.38, 0], [-0.38, -0.32], [-0.42, -0.4], [-0.4, -0.5], [-0.3, -0.5], [-0.2, -0.46], [0.18, -0.46], [0.22, -0.62], [0.2, -0.8], [0.26, -0.86], [0.3, -0.82], [0.34, -0.86], [0.38, -0.8], [0.48, -0.66], [0.46, -0.6], [0.36, -0.62], [0.32, -0.5], [0.3, -0.32], [0.3, 0], [0.12, 0], [0.12, -0.2], [-0.2, -0.2], [-0.2, 0]];
    paper(c, poly(horse.map(function (p) { return [p[0] * u, p[1] * u]; })), '#c8202a', 1.2);
    ln(c, [[0.22 * u, -0.8 * u], [0.12 * u, -0.6 * u], [0.18 * u, -0.46 * u]], '#1e2a5a', u * 0.04);
    fe(c, 0.33 * u, -0.74 * u, u * 0.018, u * 0.018, '#1e1e20');
    fp(c, [[-0.1 * u, -0.46 * u], [0.12 * u, -0.46 * u], [0.08 * u, -0.3 * u], [-0.06 * u, -0.3 * u]], '#2f6db0'); ln(c, [[-0.1 * u, -0.46 * u], [0.12 * u, -0.46 * u]], '#f2e6c9', u * 0.02);
    c.strokeStyle = '#f2c94c'; c.lineWidth = Math.max(1, u * 0.018);
    [[-0.28, -0.38, 0.06], [0.2, -0.36, 0.05], [-0.25, -0.25, 0.04], [0.24, -0.6, 0.04]].forEach(function (p) { c.beginPath(); c.arc(p[0] * u, p[1] * u, p[2] * u, 0.5, 5.5); c.stroke(); fe(c, p[0] * u, p[1] * u, u * 0.015, u * 0.015, '#f2c94c'); });
    for (var i = 0; i < 5; i++) fe(c, (-0.05 + i * 0.03) * u, -0.38 * u, u * 0.012, u * 0.02, i % 2 ? '#f2e6c9' : '#7fd8a4');
    c.restore();
  }],
  /* chōchin and Lanna khom hung side by side, swinging as pendulums */
  japanese: [function (c, S, L) {
    var hh = S.hh, x = L.mx, top = S.deck - hh * 1.6, wood = S.night ? '#3a1e1e' : '#5a2a22';
    paper(c, rect(x - hh * 0.55, top, hh * 0.07, S.deck - top), wood, 1); paper(c, rect(x + hh * 0.48, top, hh * 0.07, S.deck - top), wood, 1);
    paper(c, rect(x - hh * 0.66, top - hh * 0.04, hh * 1.32, hh * 0.07), '#c0262a', 0.9); kalae(c, x, top - hh * 0.04, hh * 0.22);
    paper(c, rect(x - hh * 0.5, S.deck - hh * 0.62, hh * 1.0, hh * 0.24), S.night ? '#2a3a5a' : '#2f4a7a', 0.8);
    c.font = '700 ' + Math.round(hh * 0.13) + 'px "Sarabun",system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#f2e6c9'; c.fillText('ร้านอาหาร', x, S.deck - hh * 0.5);
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, top = S.deck - hh * 1.56;
    [[-0.32, 'cho'], [0, 'khom'], [0.32, 'cho']].forEach(function (p, i) {
      hangLantern(c, x + p[0] * hh, top, hh * 0.12, pendulum(S.t, 0.8, i * 1.7) * 0.5, function (lx, ly, th) {
        if (p[1] === 'cho') { if (S.night) glow(c, lx, ly + hh * 0.17, hh * 0.4, '255,120,60', 0.6); c.save(); c.translate(lx, ly); c.rotate(-th);
          fp(c, [[-hh * 0.07, 0], [hh * 0.07, 0], [hh * 0.07, hh * 0.04], [-hh * 0.07, hh * 0.04]], '#1e1e20'); fe(c, 0, hh * 0.17, hh * 0.11, hh * 0.14, S.night ? '#ff5a3a' : '#d8282a');
          c.strokeStyle = 'rgba(0,0,0,.3)'; c.lineWidth = 0.7; for (var k = -2; k <= 2; k++) { c.beginPath(); c.ellipse(0, hh * 0.17 + k * hh * 0.05, hh * 0.11 * Math.sqrt(1 - Math.pow(k * 0.05 / 0.14, 2)), hh * 0.012, 0, 0, Math.PI); c.stroke(); }
          fp(c, [[-hh * 0.07, hh * 0.3], [hh * 0.07, hh * 0.3], [hh * 0.07, hh * 0.34], [-hh * 0.07, hh * 0.34]], '#1e1e20'); c.restore(); }
        else khomDao(c, lx, ly + hh * 0.13, hh * 0.13, S.t / 1600, S.night);
      });
    });
  }],
  /* a naga on sticks, dancing: its body y = A·sin(kx − ωt), a Lanna crest on its head */
  chinese: [function (c, S, L) {}, function (S, L) {
    var c = S.c, hh = S.hh, x0 = L.mx - hh * 0.62, x1 = L.mx + hh * 0.62, base = S.deck - hh * 0.95, n = 8, segs = [];
    for (var i = 0; i <= n; i++) { var f = i / n, x = lerp(x0, x1, f); segs.push([x, base + Math.sin(f * 5 - S.t / 300) * hh * 0.13]); }
    for (i = 1; i < n; i += 2) ln(c, [[segs[i][0], segs[i][1]], [segs[i][0] + Math.sin(i) * hh * 0.05, S.deck]], '#7a4a2a', 1.6);
    c.lineCap = 'round'; c.lineJoin = 'round'; c.strokeStyle = '#a8141a'; c.lineWidth = hh * 0.2; path(c, segs); c.stroke();
    c.strokeStyle = '#e02a2a'; c.lineWidth = hh * 0.16; path(c, segs); c.stroke();
    c.strokeStyle = '#f2c94c'; c.lineWidth = hh * 0.04; path(c, segs.map(function (p) { return [p[0], p[1] + hh * 0.04]; })); c.stroke();
    for (i = 0; i < n; i++) { var mx2 = (segs[i][0] + segs[i + 1][0]) / 2, my2 = (segs[i][1] + segs[i + 1][1]) / 2; fp(c, [[mx2 - hh * 0.05, my2 - hh * 0.07], [mx2, my2 - hh * 0.17], [mx2 + hh * 0.05, my2 - hh * 0.07]], '#2f8f5b'); c.strokeStyle = '#f2c94c'; c.lineWidth = 1; c.beginPath(); c.arc(mx2, my2 - hh * 0.01, hh * 0.04, 0, Math.PI); c.stroke(); }
    var tx = segs[n][0], ty = segs[n][1]; fp(c, [[tx, ty - hh * 0.05], [tx + hh * 0.18, ty - hh * 0.12 + Math.sin(S.t / 200) * hh * 0.04], [tx + hh * 0.12, ty], [tx + hh * 0.2, ty + hh * 0.08], [tx, ty + hh * 0.05]], '#f2c94c');
    var hx = segs[0][0] - hh * 0.06, hy = segs[0][1];
    fp(c, [[hx + hh * 0.08, hy - hh * 0.1], [hx - hh * 0.2, hy - hh * 0.06], [hx - hh * 0.24, hy + hh * 0.02], [hx - hh * 0.12, hy + hh * 0.06], [hx + hh * 0.08, hy + hh * 0.1]], '#d8282a');
    fp(c, [[hx - hh * 0.22, hy + hh * 0.02], [hx - hh * 0.06, hy + hh * 0.04], [hx - hh * 0.12, hy + hh * 0.1]], '#f2e6c9');
    fe(c, hx - hh * 0.1, hy - hh * 0.03, hh * 0.025, hh * 0.025, '#fff'); fe(c, hx - hh * 0.105, hy - hh * 0.03, hh * 0.012, hh * 0.012, '#111');
    ln(c, [[hx - hh * 0.04, hy - hh * 0.08], [hx + hh * 0.02, hy - hh * 0.26], [hx + hh * 0.12, hy - hh * 0.3]], '#f2c94c', hh * 0.035); ln(c, [[hx, hy - hh * 0.09], [hx + hh * 0.1, hy - hh * 0.2], [hx + hh * 0.2, hy - hh * 0.2]], '#f2c94c', hh * 0.03);
    ln(c, [[hx - hh * 0.22, hy], [hx - hh * 0.32, hy - hh * 0.05 + Math.sin(S.t / 250) * hh * 0.03]], '#f2c94c', 1.2);
  }],
  /* Hội An silk lanterns from a carved Lanna bracket, swaying */
  vietnamese: [function (c, S, L) { postArm(c, S, L.mx - S.hh * 0.5, S.deck - S.hh * 1.65, S.hh * 1.0, S.night); },
    function (S, L) {
      var c = S.c, hh = S.hh, x = L.mx - hh * 0.5, top = S.deck - hh * 1.6, cols = [['#e8402a', '255,110,70'], ['#f2c94c', '255,210,90'], ['#9b4bd6', '200,120,255']];
      [0.3, 0.6, 0.9].forEach(function (dx, i) {
        hangLantern(c, x + dx * hh, top, hh * (0.12 + (i % 2) * 0.1), pendulum(S.t, 0.9, i * 2.1) * 0.6, function (lx, ly, th) {
          if (S.night) glow(c, lx, ly + hh * 0.14, hh * 0.35, cols[i][1], 0.6);
          c.save(); c.translate(lx, ly); c.rotate(-th);
          c.fillStyle = cols[i][0]; c.beginPath(); c.moveTo(0, 0); c.bezierCurveTo(hh * 0.16, hh * 0.04, hh * 0.16, hh * 0.24, 0, hh * 0.28); c.bezierCurveTo(-hh * 0.16, hh * 0.24, -hh * 0.16, hh * 0.04, 0, 0); c.fill();
          c.strokeStyle = 'rgba(80,30,10,.45)'; c.lineWidth = 0.8; [-0.6, -0.25, 0.25, 0.6].forEach(function (k) { c.beginPath(); c.moveTo(0, 0); c.quadraticCurveTo(k * hh * 0.2, hh * 0.14, 0, hh * 0.28); c.stroke(); });
          fp(c, [[-hh * 0.03, -hh * 0.01], [hh * 0.03, -hh * 0.01], [hh * 0.03, hh * 0.03], [-hh * 0.03, hh * 0.03]], '#e8b84a'); fp(c, [[-hh * 0.03, hh * 0.26], [hh * 0.03, hh * 0.26], [hh * 0.02, hh * 0.3], [-hh * 0.02, hh * 0.3]], '#e8b84a');
          ln(c, [[0, hh * 0.3], [Math.sin(S.t / 400 + i) * hh * 0.02, hh * 0.42]], '#e8402a', 1.2); c.restore();
        });
      });
    }],
  /* a Pathein parasol by a tea-shop stool, its spokes turning */
  burmese: [function (c, S, L) {
    var hh = S.hh, x = L.mx; stool(c, x + hh * 0.3, S.deck, hh * 0.24, hh * 0.18, '#7a4a2a');
    ln(c, [[x - hh * 0.2, S.deck], [x - hh * 0.05, S.deck - hh * 1.35]], '#5a3a20', hh * 0.04);
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx - hh * 0.05, y = S.deck - hh * 1.35, R = hh * 0.62, rot = S.t / 4000;
    paper(c, function (q) { q.beginPath(); q.ellipse(x, y, R, R * 0.42, -0.12, Math.PI, TAU); q.ellipse(x, y, R, R * 0.12, -0.12, 0, Math.PI); q.closePath(); }, '#e8702a', 1.2);
    c.save(); c.beginPath(); c.ellipse(x, y, R, R * 0.42, -0.12, Math.PI, TAU); c.closePath(); c.clip();
    for (var i = 0; i < 12; i++) { var a = rot + i / 12 * TAU, cx = Math.cos(a); if (Math.sin(a) > 0.1) continue; ln(c, [[x, y - R * 0.42], [x + cx * R, y + Math.sin(-0.12) * cx * R]], '#a8441a', 1); var fx = x + cx * R * 0.7, fy = y - R * 0.42 * 0.35 + Math.sin(-0.12) * cx * R * 0.7; fe(c, fx, fy, R * 0.07, R * 0.05, i % 2 ? '#f2c94c' : '#f6e6d0'); }
    c.restore();
    fe(c, x, y - R * 0.43, hh * 0.035, hh * 0.035, '#e8b84a'); fp(c, [[x - hh * 0.02, y - R * 0.43], [x, y - R * 0.43 - hh * 0.12], [x + hh * 0.02, y - R * 0.43]], '#e8b84a');
    c.strokeStyle = '#f2c94c'; c.lineWidth = 1.2; c.beginPath(); c.ellipse(x, y, R, R * 0.12, -0.12, 0, Math.PI); c.stroke();
  }],
  /* a floating-market boat on the khlong, bobbing y = A·sin ωt, its paddler in a ngob hat */
  'central-thai': [function (c, S, L) {
    var hh = S.hh, x0 = L.mx - hh * 0.72, x1 = L.mx + hh * 0.72;
    paper(c, rect(x0, S.deck - hh * 0.04, x1 - x0, hh * 0.2), S.night ? '#2a4c7a' : '#4b8fc9', 0.8);
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, bob = Math.sin(S.t / 700) * hh * 0.025, tilt = Math.sin(S.t / 700 + 1) * 0.04, wy = S.deck - hh * 0.02;
    c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 1; for (var i = 0; i < 4; i++) { c.beginPath(); for (var k = 0; k <= 10; k++) { var wx = x - hh * 0.7 + k * hh * 0.14; c.lineTo(wx, wy + hh * 0.05 + i * hh * 0.035 + Math.sin(wx * 0.08 - S.t / 400 + i) * 1.5); } c.stroke(); }
    c.save(); c.translate(x, wy + bob); c.rotate(tilt);
    var crew = { dir: -1, garb: 'casual', col: '#2c3e6b', low: '#24335a', skin: '#c8905a', hair: 0 };
    var P = { lean: 0.25, seat: 0.12, legs: [1.5, -2.7, 1.5, -2.7], arms: [] }, row = Math.sin(S.t / 600);
    var me = worker({ c: c, deck: 0 }, hh * 0.3, hh * 0.85, P, crew, [hh * 0.1 - row * hh * 0.1, -hh * 0.3], [hh * 0.05 - row * hh * 0.08, -hh * 0.12], -hh * 0.06);
    ln(c, [[hh * 0.16 - row * hh * 0.12, -hh * 0.42], [-hh * 0.1 - row * hh * 0.14, hh * 0.18]], '#7a4a2a', hh * 0.025); fe(c, -hh * 0.12 - row * hh * 0.14, hh * 0.2, hh * 0.04, hh * 0.07, '#7a4a2a', 0.4);
    hat(c, me, 'cone');
    paper(c, function (q) { q.beginPath(); q.moveTo(-hh * 0.7, -hh * 0.12); q.quadraticCurveTo(-hh * 0.4, hh * 0.08, 0, hh * 0.08); q.quadraticCurveTo(hh * 0.4, hh * 0.08, hh * 0.7, -hh * 0.12); q.lineTo(hh * 0.6, -hh * 0.06); q.lineTo(-hh * 0.6, -hh * 0.06); q.closePath(); }, '#4a2e1c', 0.6);
    ln(c, [[-hh * 0.62, -hh * 0.07], [hh * 0.62, -hh * 0.07]], '#e8b84a', 1);
    [['#f6b02a', -0.4], ['#5aa83a', -0.28], ['#e0283c', -0.16], ['#f6b02a', -0.05], ['#9b4bd6', -0.34]].forEach(function (f, j) { fe(c, f[1] * hh, -hh * (0.1 + (j > 3 ? 0.06 : 0)), hh * 0.05, hh * 0.045, f[0]); });
    c.restore();
  }],
  /* a khaen player: the bamboo mouth organ held up, notes rising */
  isaan: [function (c, S, L) {}, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx + hh * 0.1, d = L.crew[1]; d.dir = -1; d.garb = 'mohom'; d.col = '#2c3e6b'; d.low = '#24335a';
    var lean = 0.05 + 0.06 * Math.sin(S.t / 500), sh = shoulder(x, S.deck, hh, 0.47, lean, -1), mouth = [sh[0] - hh * 0.1, sh[1] - hh * 0.1];
    var me = worker(S, x, hh, { lean: lean, legs: [0.1, 0, -0.08, 0] }, d, [mouth[0] - hh * 0.02, mouth[1] + hh * 0.05], [mouth[0] + hh * 0.02, mouth[1] + hh * 0.1]);
    var kx = mouth[0] - hh * 0.03, ky = mouth[1] + hh * 0.04;
    for (var i = 0; i < 7; i++) { var px = kx - hh * 0.04 + i * hh * 0.013, l = hh * (0.55 + Math.abs(i - 3) * 0.04); ln(c, [[px, ky + hh * 0.12], [px, ky + hh * 0.12 - l]], i % 2 ? '#d8b070' : '#c8a060', Math.max(1, hh * 0.012)); }
    paper(c, E(kx, ky + hh * 0.04, hh * 0.04, hh * 0.05), '#6a3a1a', 0.3);
    ln(c, [[kx - hh * 0.05, ky - hh * 0.25], [kx + hh * 0.05, ky - hh * 0.25]], '#c0392b', 1.5);
    hat(c, me, 'kerchief', '#c0392b');
    K.notes(c, kx - hh * 0.25, ky - hh * 0.05, S.t, 3, S.night ? '#ffe2a0' : '#7a3a1a');
  }],
  /* a Nora dancer: the tall gold crown, the beaded netting, long curved nails */
  'southern-thai': [function (c, S, L) {}, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx + hh * 0.05, d = L.crew[1], u = S.t / 1000; d.dir = -1; d.garb = 'casual'; d.long = true; d.col = '#c0262a'; d.low = '#2a3a6a';
    var lean = 0.1 + 0.05 * Math.sin(u * 1.2), base = { lean: lean, seat: 0.4, legs: [0.5, -0.8, -0.2, -0.4] }, sh = shoulder(x, S.deck, hh, 0.4, lean, -1);
    var T1 = [sh[0] - hh * (0.25 + 0.06 * Math.sin(u * 1.3)), sh[1] - hh * (0.05 + 0.12 * Math.sin(u * 1.3))], T2 = [sh[0] + hh * (0.22 + 0.05 * Math.cos(u * 1.3)), sh[1] + hh * (0.05 - 0.1 * Math.cos(u * 1.3))];
    var me = worker(S, x, hh, base, d, T1, T2);
    for (var i = 0; i < 12; i++) fe(c, me.sh[0] + ((i % 4) - 1.5) * hh * 0.035, me.sh[1] + hh * 0.03 + Math.floor(i / 4) * hh * 0.07, hh * 0.012, hh * 0.012, i % 2 ? '#f2c94c' : '#f2e6c9');
    fp(c, [[me.hip[0] + hh * 0.05, me.hip[1] - hh * 0.06], [me.hip[0] + hh * 0.28, me.hip[1] - hh * 0.22], [me.hip[0] + hh * 0.2, me.hip[1] - hh * 0.02]], '#e8b84a');
    var hd = me.head; fp(c, [[hd[0] - hh * 0.09, hd[1] - hh * 0.06], [hd[0] - hh * 0.05, hd[1] - hh * 0.2], [hd[0], hd[1] - hh * 0.42], [hd[0] + hh * 0.05, hd[1] - hh * 0.2], [hd[0] + hh * 0.09, hd[1] - hh * 0.06]], '#e8b84a');
    for (i = 1; i < 4; i++) ln(c, [[hd[0] - hh * 0.07 + i * hh * 0.01, hd[1] - hh * 0.06 - i * hh * 0.08], [hd[0] + hh * 0.07 - i * hh * 0.01, hd[1] - hh * 0.06 - i * hh * 0.08]], '#c0262a', 1);
    me.hand.forEach(function (p, j) { for (var k = 0; k < 3; k++) { c.strokeStyle = '#f2c94c'; c.lineWidth = 1; c.beginPath(); c.moveTo(p[0], p[1]); c.quadraticCurveTo(p[0] - hh * 0.06, p[1] - hh * 0.02 - k * hh * 0.02, p[0] - hh * 0.05, p[1] - hh * 0.1 - k * hh * 0.01); c.stroke(); } });
  }],
  /* a gramophone on a lacquer cabinet: the record turns, θ = 2π·(33⅓/60)·t, notes rise */
  'soul-food': [function (c, S, L) {
    var hh = S.hh, x = L.mx, top = S.deck - hh * 0.6;
    paper(c, rect(x - hh * 0.4, top, hh * 0.8, hh * 0.5), '#2a1410', 1.2); laiKham(c, x - hh * 0.38, x + hh * 0.38, top + hh * 0.25, hh * 0.05);
    ln(c, [[x - hh * 0.34, top + hh * 0.5], [x - hh * 0.36, S.deck]], '#2a1410', 3); ln(c, [[x + hh * 0.34, top + hh * 0.5], [x + hh * 0.36, S.deck]], '#2a1410', 3);
    ln(c, [[x + hh * 0.22, top - hh * 0.05], [x + hh * 0.2, top - hh * 0.5], [x + hh * 0.05, top - hh * 0.68]], '#c8a040', hh * 0.04);
    paper(c, function (q) { q.beginPath(); q.moveTo(x + hh * 0.05, top - hh * 0.66); q.quadraticCurveTo(x - hh * 0.1, top - hh * 0.72, x - hh * 0.38, top - hh * 1.05); q.quadraticCurveTo(x - hh * 0.5, top - hh * 0.8, x - hh * 0.3, top - hh * 0.52); q.quadraticCurveTo(x - hh * 0.1, top - hh * 0.58, x + hh * 0.05, top - hh * 0.62); q.closePath(); }, '#e8b84a', 1);
    c.strokeStyle = '#c0882a'; c.lineWidth = 0.8; for (var i = 1; i < 4; i++) { c.beginPath(); c.moveTo(x + hh * 0.03, top - hh * 0.64); c.quadraticCurveTo(x - hh * 0.12, top - hh * 0.65 - i * hh * 0.03, x - hh * 0.32 - i * hh * 0.03, top - hh * 0.62 - i * hh * 0.12); c.stroke(); }
  }, function (S, L) {
    var c = S.c, hh = S.hh, x = L.mx, top = S.deck - hh * 0.6, th = S.t / 1000 * TAU * (100 / 3 / 60);
    fe(c, x - hh * 0.05, top - hh * 0.02, hh * 0.3, hh * 0.07, '#111'); fe(c, x - hh * 0.05, top - hh * 0.02, hh * 0.1, hh * 0.024, '#c0262a');
    c.strokeStyle = 'rgba(255,255,255,.35)'; c.lineWidth = 1; c.beginPath(); c.ellipse(x - hh * 0.05, top - hh * 0.02, hh * 0.22, hh * 0.05, 0, th, th + 0.8); c.stroke();
    fe(c, x - hh * 0.05 + Math.cos(th) * hh * 0.07, top - hh * 0.02 + Math.sin(th) * hh * 0.017, hh * 0.015, hh * 0.008, '#f2c94c');
    ln(c, [[x + hh * 0.3, top - hh * 0.06], [x + hh * 0.1, top - hh * 0.04]], '#c9ccd2', 1.6);
    K.notes(c, x - hh * 0.62, top - hh * 0.3, S.t, 3, S.night ? '#ffe2a0' : '#3a1e10');
  }],
  /* pierced brass lanterns from a Lanna bracket, their stars of light drifting */
  falafel: [function (c, S, L) { postArm(c, S, L.mx - S.hh * 0.45, S.deck - S.hh * 1.6, S.hh * 0.9, S.night); },
    function (S, L) {
      var c = S.c, hh = S.hh, x = L.mx - hh * 0.45, top = S.deck - hh * 1.55;
      [[0.35, 0.18], [0.75, 0.3]].forEach(function (p, i) {
        hangLantern(c, x + p[0] * hh, top, hh * p[1], pendulum(S.t, 1, i * 2) * 0.35, function (lx, ly, th) {
          var w = hh * 0.17, h = hh * 0.3; glow(c, lx, ly + h * 0.6, hh * (S.night ? 0.45 : 0.2), '255,190,90', S.night ? 0.6 : 0.25);
          c.save(); c.translate(lx, ly); c.rotate(-th);
          fp(c, [[-w * 0.15, 0], [w * 0.15, 0], [w * 0.6, h * 0.22], [-w * 0.6, h * 0.22]], '#b8862a');
          fp(c, [[-w * 0.5, h * 0.22], [w * 0.5, h * 0.22], [w * 0.4, h * 0.95], [-w * 0.4, h * 0.95]], '#e0aa3a');
          [['#2f9fa8', -0.22], ['#c8302a', 0.02], ['#2f9fa8', 0.26]].forEach(function (g) { fp(c, [[g[1] * w * 1.4 - w * 0.12, h * 0.32], [g[1] * w * 1.4 + w * 0.12, h * 0.32], [g[1] * w * 1.4 + w * 0.1, h * 0.86], [g[1] * w * 1.4 - w * 0.1, h * 0.86]], S.night ? '#ffd27a' : g[0]); });
          fp(c, [[-w * 0.3, h * 0.95], [w * 0.3, h * 0.95], [0, h * 1.15]], '#b8862a');
          for (var k = 0; k < 6; k++) { var a = S.t / 2500 + k * 1.05, sx = Math.sin(a) * w * 0.35; if (Math.cos(a) < 0) continue; fe(c, sx, h * (0.38 + (k % 3) * 0.18), 1.4, 1.4, S.night ? '#fff2b0' : '#5a3a10'); }
          c.restore();
        });
      });
    }]
};

/* ---------------------------------------------------------------- the kitchens' cards */
function C(th, en, seat, cloth, dishes, hold, extra) {
  var o = { th: th, en: en, seat: seat, cloth: cloth, dishes: dishes, hold: hold, mix: { casual: 0.6, sin: 0.2, mohom: 0.2 } };
  for (var k in extra || {}) o[k] = extra[k];
  return o;
}
var CUIS = {
  lanna: C('อาหารเหนือ', 'Lanna', 'floor', 'khantok', ['khaoSoi', 'saiOua', 'namPrik', 'kratip'], ['ball', 'ball', 'spoon'], { mix: { sin: 0.45, mohom: 0.4, casual: 0.15 }, morsel: '#c8452a' }),
  american: C('อาหารอเมริกัน', 'American', 'table', 'diner', ['burger', 'fries', 'pancakes', 'shake', 'pie'], ['burger', 'fork', 'fork'], { morsel: '#e8a64a', mix: { casual: 0.8, sin: 0.1, mohom: 0.1 } }),
  dutch: C('อาหารดัตช์', 'Dutch', 'table', 'delft', ['stroop', 'poffertjes', 'herring', 'gouda'], ['fish', 'fork', 'stroop'], { morsel: '#c4823a' }),
  swiss: C('อาหารสวิส', 'Swiss', 'table', 'swiss', ['fondue', 'rosti', 'emmental', 'choc'], ['fork', 'cup', 'fork'], { morsel: '#f2d46a', drink: '#c8102e', cup: '#f4f1ea' }),
  swedish: C('อาหารสวีเดน', 'Swedish', 'table', 'swede', ['meatballs', 'bulle', 'princess', 'crisp'], ['fork', 'bun', 'cup'], { morsel: '#7a4220' }),
  japanese: C('อาหารญี่ปุ่น', 'Japanese', 'table', 'hinoki', ['ramen', 'nigiri', 'onigiri', 'matcha'], ['chop', 'sushi', 'cup'], { noodle: '#f2d58a', cup: '#8a5a3a', drink: '#7ab84a' }),
  chinese: C('อาหารจีน', 'Chinese', 'table', 'red', ['dimsum', 'duck', 'noodles', 'teapot', 'mooncake'], ['chop', 'chop', 'cup'], { cup: '#f4f1ea', drink: '#a8783a' }),
  vietnamese: C('อาหารเวียดนาม', 'Vietnamese', 'low', 'steel', ['pho', 'banhmi', 'goicuon', 'phin'], ['chop', 'banh', 'spoon'], { noodle: '#fbf8ee', morsel: '#a8604a', stools: ['#d8282a', '#2f6db0'] }),
  burmese: C('อาหารพม่า', 'Burmese', 'low', 'teak', ['mohinga', 'laphet', 'milktea'], ['spoon', 'cup', 'chop'], { noodle: '#fbf8ee', cup: '#f4f1ea', drink: '#c8925a', stools: ['#7a4a2a', '#8a5a32'] }),
  'central-thai': C('อาหารภาคกลาง', 'Central Thai', 'table', 'thai', ['padthai', 'tomyum', 'greencurry', 'mango'], ['spoon', 'fork', 'spoon'], { morsel: '#d8964a' }),
  isaan: C('อาหารอีสาน', 'Isan', 'floor', 'mat', ['somtam', 'gaiyang', 'larb', 'kratip'], ['ball', 'ball', 'leg'], { mix: { mohom: 0.45, sin: 0.3, casual: 0.25 } }),
  'southern-thai': C('อาหารใต้', 'Southern Thai', 'table', 'batik', ['roti', 'massaman', 'satay', 'khaoyam'], ['roti', 'skewer', 'spoon'], { morsel: '#c8642a' }),
  'soul-food': C('โซลฟู้ด', 'Soul food', 'table', 'gingham', ['chicken', 'collards', 'cornbread', 'mac', 'sweetpie'], ['leg', 'fork', 'leg'], { morsel: '#f2a42a', mix: { casual: 0.8, sin: 0.1, mohom: 0.1 } }),
  falafel: C('ฟาลาเฟล', 'Falafel', 'table', 'zellige', ['falafel', 'pita', 'hummus', 'pickles', 'tabbouleh'], ['wrap', 'falafel', 'wrap'], { morsel: '#6b3f1c' })
};

/* ---------------------------------------------------------------- the table and its cloth */
function cloth(c, kind, x0, x1, y, h, night) {
  var w = x1 - x0, i, j;
  var base = { diner: '#c0392b', delft: '#f6f8fc', swiss: '#c8202a', swede: '#e6f0fa', hinoki: '#3a2218', red: '#a8241c', steel: '#b8bcc4', teak: '#6a3e22', thai: '#f4ecd8', batik: '#2a3a6a', gingham: '#fbf6f0', zellige: '#f6f2ea' }[kind] || '#f2e6c9';
  paper(c, rect(x0, y, w, h), base, 1.2);
  c.save(); c.beginPath(); c.rect(x0, y, w, h); c.clip();
  if (kind === 'diner') { ln(c, [[x0, y + h * 0.3], [x1, y + h * 0.3]], '#e8eaee', h * 0.12); ln(c, [[x0, y + h * 0.7], [x1, y + h * 0.7]], '#e8eaee', h * 0.12); }
  else if (kind === 'delft') { for (i = 0; x0 + i * h * 0.5 < x1; i++) { var tx = x0 + i * h * 0.5 + h * 0.25; c.strokeStyle = '#2f5fa8'; c.lineWidth = 0.8; c.strokeRect(tx - h * 0.23, y + h * 0.1, h * 0.46, h * 0.46); fe(c, tx, y + h * 0.33, h * 0.07, h * 0.07, '#2f5fa8'); for (j = 0; j < 4; j++) fe(c, tx + Math.cos(j * 1.57) * h * 0.13, y + h * 0.33 + Math.sin(j * 1.57) * h * 0.13, h * 0.05, h * 0.025, '#4a7ac8', j * 1.57); } ln(c, [[x0, y + h * 0.8], [x1, y + h * 0.8]], '#2f5fa8', h * 0.06); }
  else if (kind === 'swiss') { for (i = 0; x0 + i * h * 0.6 < x1; i++) { var cx = x0 + i * h * 0.6 + h * 0.3, cy = y + h * (i % 2 ? 0.62 : 0.32); fp(c, [[cx - h * 0.04, cy - h * 0.12], [cx + h * 0.04, cy - h * 0.12], [cx + h * 0.04, cy - h * 0.04], [cx + h * 0.12, cy - h * 0.04], [cx + h * 0.12, cy + h * 0.04], [cx + h * 0.04, cy + h * 0.04], [cx + h * 0.04, cy + h * 0.12], [cx - h * 0.04, cy + h * 0.12], [cx - h * 0.04, cy + h * 0.04], [cx - h * 0.12, cy + h * 0.04], [cx - h * 0.12, cy - h * 0.04], [cx - h * 0.04, cy - h * 0.04]], '#ffffff'); } }
  else if (kind === 'swede') { ln(c, [[x0, y + h * 0.5], [x1, y + h * 0.5]], '#2f6db0', h * 0.22); ln(c, [[x0, y + h * 0.5], [x1, y + h * 0.5]], '#f2c94c', h * 0.08); }
  else if (kind === 'hinoki') { for (i = 0; i < 3; i++) ln(c, [[x0, y + h * (0.25 + i * 0.25)], [x1, y + h * (0.25 + i * 0.25)]], 'rgba(255,220,180,.12)', 1); ln(c, [[x0, y + h * 0.05], [x1, y + h * 0.05]], '#c0262a', h * 0.08); }
  else if (kind === 'red') { laiKham(c, x0, x1, y + h * 0.5, h * 0.14, '#f2c94c'); ln(c, [[x0, y + h * 0.12], [x1, y + h * 0.12]], '#f2c94c', 1); ln(c, [[x0, y + h * 0.88], [x1, y + h * 0.88]], '#f2c94c', 1); }
  else if (kind === 'steel') { for (i = 0; i < 4; i++) ln(c, [[x0, y + h * (0.2 + i * 0.2)], [x1, y + h * (0.2 + i * 0.2)]], 'rgba(255,255,255,.25)', 1); }
  else if (kind === 'teak') { for (i = 0; i < 4; i++) ln(c, [[x0, y + h * (0.2 + i * 0.2)], [x1, y + h * (0.22 + i * 0.2)]], 'rgba(0,0,0,.15)', 1); }
  else if (kind === 'thai') { for (i = 0; x0 + i * h * 0.3 < x1; i++) fp(c, [[x0 + i * h * 0.3, y + h * 0.75], [x0 + i * h * 0.3 + h * 0.15, y + h * 0.3], [x0 + i * h * 0.3 + h * 0.3, y + h * 0.75]], i % 2 ? '#e8b84a' : '#c0262a'); ln(c, [[x0, y + h * 0.85], [x1, y + h * 0.85]], '#e8b84a', h * 0.08); }
  else if (kind === 'batik') { for (i = 0; x0 + i * h * 0.4 < x1; i++) { var bx = x0 + i * h * 0.4 + h * 0.2; c.strokeStyle = '#e8b84a'; c.lineWidth = 1; c.beginPath(); c.arc(bx, y + h * 0.5, h * 0.16, 0, TAU); c.stroke(); fe(c, bx, y + h * 0.5, h * 0.05, h * 0.05, '#f2e6c9'); for (j = 0; j < 6; j++) fe(c, bx + Math.cos(j) * h * 0.26, y + h * 0.5 + Math.sin(j) * h * 0.26, 1, 1, '#c86a2a'); } }
  else if (kind === 'gingham') { c.fillStyle = 'rgba(200,30,40,.45)'; for (i = 0; x0 + i * h * 0.25 < x1; i += 2) c.fillRect(x0 + i * h * 0.25, y, h * 0.25, h); for (j = 0; j < 4; j += 2) c.fillRect(x0, y + j * h * 0.25, w, h * 0.25); }
  else if (kind === 'zellige') { for (i = 0; x0 + i * h * 0.45 < x1; i++) { var zx = x0 + i * h * 0.45 + h * 0.22, pts = []; for (j = 0; j < 16; j++) { var a = j / 16 * TAU, r = j % 2 ? h * 0.1 : h * 0.2; pts.push([zx + Math.cos(a) * r, y + h * 0.45 + Math.sin(a) * r]); } fp(c, pts, j % 2 ? '#2f6db0' : '#2f8f8a'); fe(c, zx, y + h * 0.45, h * 0.05, h * 0.05, '#f2c94c'); } }
  c.restore();
  if (night) { c.fillStyle = 'rgba(10,5,20,.18)'; c.fillRect(x0, y, w, h); }
}
function table(c, S, L, Cu) {
  var hh = S.hh, x0 = L.tx0 - hh * 0.08, x1 = L.tx1 + hh * 0.08, y = L.ty, wood = S.night ? '#4a2e1c' : '#6a3e22';
  if (Cu.seat === 'floor') {   /* the khantok: a low round lacquer tray on its pedestal */
    var cx = (x0 + x1) / 2, rx = (x1 - x0) / 2;
    var mat = Cu.cloth === 'mat', lac = mat ? '#b8864a' : S.night ? '#7a2018' : '#a8241c', top = mat ? '#d8b070' : S.night ? '#8a2a1e' : '#c03424', foot = mat ? '#9a6a34' : S.night ? '#5a1810' : '#8a1e14';
    paper(c, poly([[cx - rx * 0.35, L.foot], [cx + rx * 0.35, L.foot], [cx + rx * 0.22, y + hh * 0.08], [cx - rx * 0.22, y + hh * 0.08]]), foot, 1);
    if (mat) { c.save(); c.beginPath(); c.rect(cx - rx * 0.35, y, rx * 0.7, L.foot - y); c.clip(); for (var i = -12; i < 12; i++) ln(c, [[cx + i * hh * 0.06, y], [cx + i * hh * 0.06 + hh * 0.3, L.foot]], 'rgba(60,30,10,.35)', 0.8); c.restore(); }
    laiKham(c, cx - rx * 0.28, cx + rx * 0.28, L.foot - (L.foot - y) * 0.4, hh * 0.035);
    paper(c, function (q) { q.beginPath(); q.ellipse(cx, y + hh * 0.04, rx, hh * 0.07, 0, 0, TAU); }, lac, 1.2);
    fe(c, cx, y + hh * 0.02, rx * 0.97, hh * 0.05, top);
    c.strokeStyle = '#e8b84a'; c.lineWidth = 1.5; c.beginPath(); c.ellipse(cx, y + hh * 0.04, rx, hh * 0.07, 0, 0, Math.PI); c.stroke();
    if (mat) for (i = 0; i < 30; i++) ln(c, [[cx - rx * 0.95 + i * rx * 0.065, y + hh * 0.04], [cx - rx * 0.92 + i * rx * 0.065, y + hh * 0.1]], 'rgba(90,50,20,.4)', 0.8); else laiKham(c, cx - rx * 0.85, cx + rx * 0.85, y + hh * 0.085, hh * 0.03);
    return;
  }
  var th = Cu.seat === 'low' ? hh * 0.06 : hh * 0.16;
  ln(c, [[x0 + hh * 0.08, y], [x0 + hh * 0.1, L.foot]], wood, Math.max(2, hh * 0.045)); ln(c, [[x1 - hh * 0.08, y], [x1 - hh * 0.1, L.foot]], wood, Math.max(2, hh * 0.045));
  paper(c, poly([[x0 + hh * 0.04, y - hh * 0.04], [x1 - hh * 0.04, y - hh * 0.04], [x1, y], [x0, y]]), Cu.cloth === 'hinoki' ? '#5a3424' : Cu.cloth === 'steel' ? '#d8dce2' : '#f6f0e2', 0.8);
  cloth(c, Cu.cloth, x0, x1, y, th, S.night);
}

/* ---------------------------------------------------------------- the setting */
function sign(c, S, L, Cu) {
  var hh = S.hh, fs = Math.round(Math.max(11, hh * 0.16)), txt = Cu.th + ' · ' + Cu.en;
  c.font = '700 ' + fs + 'px "Sarabun",system-ui,sans-serif';
  var w = c.measureText(txt).width + fs * 1.6, h = fs * 1.55, cx = L.m, y = S.deck - hh * 1.5 - h / 2, hy = S.deck - hh * 1.66;
  ln(c, [[cx - w * 0.36, hy], [cx - w * 0.36, y]], 'rgba(40,20,10,.85)', 1); ln(c, [[cx + w * 0.36, hy], [cx + w * 0.36, y]], 'rgba(40,20,10,.85)', 1);
  paper(c, function (q) { q.beginPath(); q.moveTo(cx - w / 2, y); q.lineTo(cx + w / 2, y); q.quadraticCurveTo(cx + w / 2 + h * 0.4, y + h / 2, cx + w / 2, y + h); q.lineTo(cx - w / 2, y + h); q.quadraticCurveTo(cx - w / 2 - h * 0.4, y + h / 2, cx - w / 2, y); q.closePath(); }, S.night ? '#3a2214' : '#5a3418', 1.4);
  c.strokeStyle = '#e8b84a'; c.lineWidth = 1; c.strokeRect(cx - w / 2 + 3, y + 3, w - 6, h - 6);
  [-1, 1].forEach(function (sd) { var ex = cx + sd * (w / 2 + h * 0.18); c.strokeStyle = '#e8b84a'; c.lineWidth = 1.2; c.beginPath(); c.arc(ex, y + h / 2, h * 0.16, 0, TAU); c.stroke(); });
  c.fillStyle = '#f6e2a8'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(txt, cx, y + h / 2 + 1);
}
function lay(S, Cu) {
  var hh = S.hh, ph = S.phone, a = S.x0 + hh * (ph ? 0.6 : 0.8), b = S.x1 - hh * (ph ? 0.6 : 0.85), M = ph ? 0 : hh * 1.45, room = b - a - M - (ph ? 0 : hh * 0.15), sw = Math.min(room, hh * 6.8), extra = room - sw;
  var sa = a + extra * 0.35, sb = sa + sw, L = { sa: sa, sb: sb, m: (sa + sb) / 2, mx: Math.min(b - M / 2, sb + hh * 0.15 + M / 2 + extra * 0.25), top: S.deck - hh * 1.8, eave: S.deck - hh * 1.224 };
  L.k0 = sa + hh * 0.12; L.k1 = sa + hh * 1.8; L.sy = S.deck - hh * 0.52;
  L.tx0 = sa + hh * 2.05; L.tx1 = sb - hh * 0.25; L.ty = S.deck - hh * (Cu.seat === 'table' ? 0.2 : Cu.seat === 'low' ? 0.07 : 0.0); L.foot = S.deck + hh * 0.36;
  var tw = L.tx1 - L.tx0, small = S.span < 560;
  L.nd = Math.max(2, Math.min(small ? 3 : 4, Cu.dishes.length, Math.floor(tw / (hh * 0.68))));
  var dw = tw / L.nd; L.ds = Math.min(dw * 0.98, hh * 0.85);
  L.dish = []; var off = S.seed % Cu.dishes.length;
  for (var i = 0; i < L.nd; i++) L.dish.push({ k: Cu.dishes[(i + off) % Cu.dishes.length], x: L.tx0 + dw * (i + 0.5) });
  /* diners sit at the table's ends and in the gaps between dishes */
  L.diner = []; for (i = 0; i <= L.nd; i++) L.diner.push(L.tx0 + dw * i + (i === 0 ? hh * 0.02 : i === L.nd ? -hh * 0.02 : 0));
  L.ne = L.diner.length;
  /* the prop steps left until it is clear of the clock */
  if (S.avoid) for (var g = 0; g < 12 && Math.hypot(L.mx - S.avoid.cx, S.deck - hh * 2 - S.avoid.cy) < S.avoid.r + hh * 0.5 && L.mx - hh * 0.1 > sb + hh * 0.75; g++) L.mx -= hh * 0.1;
  return L;
}
var SEATP = { table: { lean: 0.12, seat: 0.27, legs: [1.5, -1.5, 1.45, -1.5] }, low: { lean: 0.22, seat: 0.17, legs: [1.85, -2.0, 1.75, -2.0] }, floor: { lean: 0.15, seat: 0.1, legs: [1.45, -2.9, 1.45, -2.9] } };
function back(c, S, L, Cu) {
  var hh = S.hh;
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1a14' : '#9a6a4a');
  paper(c, rect(L.sa - hh * 0.1, S.deck - 3, L.sb - L.sa + hh * 0.2, hh * 0.1), S.night ? '#3a2416' : '#6a4026', 1);
  for (var x = L.sa; x < L.sb; x += hh * 0.3) ln(c, [[x, S.deck - 2], [x, S.deck + hh * 0.07]], 'rgba(0,0,0,.18)', 1);
  if (S.night) glow(c, (L.tx0 + L.tx1) / 2, S.deck - hh * 0.6, hh * 2.2, '255,190,110', 0.28);
  K.sala(c, L.sa, L.sb, S.deck, L.top, S.night);
  sign(c, S, L, Cu);
  if (!S.phone) PROP[Cu.key][0](c, S, L);
  COOK[Cu.key][0](c, S, L);
  var P = SEATP[Cu.seat];
  if (Cu.seat === 'table') paper(c, rect(L.tx0 - hh * 0.1, S.deck - hh * 0.27, L.tx1 - L.tx0 + hh * 0.2, hh * 0.05), S.night ? '#4a2e1c' : '#7a4a2a', 0.8);
  if (Cu.seat === 'low') L.diner.forEach(function (x, i) { stool(c, x, S.deck, hh * 0.2, hh * P.seat * 0.98, Cu.stools[i % 2]); });
  if (Cu.seat === 'floor') paper(c, E((L.tx0 + L.tx1) / 2, S.deck + hh * 0.02, (L.tx1 - L.tx0) * 0.6, hh * 0.05), '#c99a52', 0.5);
}
function front(c, S, L, Cu, hits) {
  table(c, S, L, Cu);
  RR = K.rnd(S.seed ^ 0x5eed);
  L.dish.forEach(function (d) { DISH[d.k][0](c, d.x, L.ty + S.hh * 0.01, L.ds, S); });
  K.banner(c, (L.tx0 + L.tx1) / 2, L.eave + S.hh * 0.03, S.label, S.hh, '#c0562a', S.seed, hits);
}
/* khom along the eave, each a pendulum on its cord */
function eaveLanterns(S, L, skip) {
  var c = S.c, hh = S.hh;
  K.strand(c, L.sa + (L.sb - L.sa) * 0.05, L.sb - (L.sb - L.sa) * 0.05, L.eave + 2, hh * 0.08, hh * 0.42, function (x, y, k) {
    if (x > skip[0] && x < skip[1]) return;
    var th = 0.18 * Math.cos(S.t / 520 + k * 1.3), len = hh * 0.08, lx = x + Math.sin(th) * len, ly = y + Math.cos(th) * len, r = hh * 0.055;
    ln(c, [[x, y], [lx, ly]], 'rgba(40,20,30,.8)', 1);
    if (S.night) glow(c, lx, ly + r, r * 3.2, '255,160,70', 0.45 + 0.15 * Math.sin(S.t / 300 + k));
    fe(c, lx, ly + r, r * 0.85, r, ['#e8402a', '#f29a2a', '#f2c94c'][k % 3]); fp(c, [[lx - r * 0.5, ly + r * 0.15], [lx + r * 0.5, ly + r * 0.15], [lx, ly - r * 0.15]], '#e8b84a');
    ln(c, [[lx, ly + r * 1.9], [lx + Math.sin(th) * r * 0.6, ly + r * 2.8]], '#e8b84a', 1);
  });
}

/* ---------------------------------------------------------------- the still layers, cut once */
var CACHE = [];
function layer(S, key, box, draw) {
  var c = S.c, m = c.getTransform ? c.getTransform() : { a: 1, d: 1, e: 0, f: 0 }, k = key + '|' + [m.a, m.d, m.e, m.f].join(','), e = null;
  for (var i = 0; i < CACHE.length; i++) if (CACHE[i].k === k) { e = CACHE[i]; break; }
  if (!e) {
    var ox = Math.floor(box[0] * m.a + m.e), oy = Math.floor(box[1] * m.d + m.f), w = Math.ceil(box[2] * m.a) + 2, h = Math.ceil(box[3] * m.d) + 2;
    var cv = document.createElement('canvas'); cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var q = cv.getContext('2d'); q.setTransform(m.a, 0, 0, m.d, m.e - ox, m.f - oy);
    e = { k: k, cv: cv, ox: ox, oy: oy, out: draw(q) };
    CACHE.unshift(e); if (CACHE.length > 24) CACHE.pop();
  }
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(e.cv, e.ox, e.oy); c.restore();
  return e;
}

/* ---------------------------------------------------------------- the scene */
function draw(S0) {
  /* on a phone the stage is eight people wide: the prop stays home and the rest is cut 1.3 times larger */
  var S = {}; for (var f in S0) S[f] = S0[f]; if (S.phone) S.hh *= 1.3;
  var key = KEYS.indexOf(S.variant) >= 0 ? S.variant : cuisineOf(S.title), Cu = CUIS[key], c = S.c, hh = S.hh;
  Cu.key = key;
  var L = lay(S, Cu), crew = K.town(S, L.ne + 2, Cu.mix); L.crew = crew;
  var id = [key, S.W, S.H, Math.round(S.x0), Math.round(S.x1), Math.round(S.deck), Math.round(hh * 10), S.seed, S.night ? 1 : 0, S.phone ? 1 : 0, S.label].join('|');
  layer(S, id + '|back', [S.x0 - 4, S.deck - hh * 2.4, S.span + 8, S.H - S.deck + hh * 2.4], function (q) { RR = K.rnd(S.seed); back(q, S, L, Cu); });
  /* the banner's room on the eave, so the lanterns hang either side of it */
  c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif';
  var bw = S.label ? c.measureText(S.label).width / 2 + hh * 0.45 : 0, bc = (L.tx0 + L.tx1) / 2;
  eaveLanterns(S, L, [bc - bw, bc + bw]);
  if (!S.phone) PROP[key][1](S, L);
  /* the cook */
  var cook = crew[0]; cook.dir = 1; cook.garb = 'casual'; cook.long = true; cook.skirt = 0;
  COOK[key][1](S, L, cook, Cu);
  /* the diners, eating: the hand goes from dish to mouth and back */
  var P0 = SEATP[Cu.seat];
  L.diner.forEach(function (x, i) {
    var d = crew[i + 2], dir = i % 2 ? -1 : 1, near = null, best = 1e9;
    L.dish.forEach(function (ds) { var dd = (ds.x - x) * dir; if (dd > -hh * 0.05 && dd < best) { best = dd; near = ds; } });
    if (!near) { dir = -dir; L.dish.forEach(function (ds) { var dd = (ds.x - x) * dir; if (dd > -hh * 0.05 && dd < best) { best = dd; near = ds; } }); }
    d.dir = dir; d.skirt = 0;
    var item = Cu.hold[i % Cu.hold.length], per = 3 + (i % 3) * 0.7, ph = ((S.t / 1000) / per + i * 0.37) % 1;
    var lift = ph < 0.35 ? 0 : ph < 0.5 ? ease((ph - 0.35) / 0.15) : ph < 0.8 ? 1 : 1 - ease((ph - 0.8) / 0.2), lean = P0.lean + 0.1 * (1 - lift);
    var h = hh * 0.92, sh = shoulder(x, S.deck, h, P0.seat, lean, dir), hd = [sh[0] + dir * Math.sin(lean) * h * 0.14, sh[1] - Math.cos(lean) * h * 0.14];
    var mouth = [hd[0] + dir * h * 0.14, hd[1] + h * (item === 'fish' ? -0.12 : 0.06)], dish = near ? [lerp(x + dir * h * 0.3, near.x, 0.5), L.ty - hh * 0.06] : [x + dir * h * 0.3, L.ty - hh * 0.05];
    var me = worker(S, x, h, { lean: lean, seat: P0.seat, legs: P0.legs }, d, [lerp(dish[0], mouth[0], lift), lerp(dish[1], mouth[1], lift)], [x + dir * h * 0.22, L.ty - hh * 0.02]);
    held(c, me.hand[0], dir, h, item, lift, S.t, i, Cu);
    if (key === 'vietnamese' && i === 1) hat(c, me, 'cone');
  });
  var fr = layer(S, id + '|front', [L.tx0 - hh * 0.6, L.eave - hh * 0.2, L.tx1 - L.tx0 + hh * 1.2, S.H - L.eave + hh * 0.2], function (q) { var h2 = []; front(q, S, L, Cu, h2); return h2; });
  (fr.out || []).forEach(function (h) { S.hits.push(h); });
  L.dish.forEach(function (d, i) { DISH[d.k][1](c, d.x, L.ty + hh * 0.01, L.ds, S, i); });
  S.hits.push({ k: 'event', x0: L.sa, x1: S.x1, y0: S.deck - hh * 2, y1: S.H });
}

D.addScene('food', draw, WORDS_RE, 'x = A·sin(ky − ωt)<br>the steam off the table');
/* each kitchen is its own doodle, aired and topped on its own */
D.variants.food = function (e) { return cuisineOf((e.t || '') + ' ' + (e.v || '') + ' ' + (e.d || '').slice(0, 160)); };
})();
