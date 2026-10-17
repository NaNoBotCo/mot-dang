/* 'bag-knots' for the auto-doodler, taken from the minisite Bag Knots
   (https://nanobotco.github.io/bag-knots/).
   We draw a Lanna market scene where a merchant is tying bag knots. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, rect = K.rect, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

var W = 480, H = 400, CX = 240;
var C = {
  curry: ["#E0601F", ["#B3121F", "#2E7D32", "#F4E3B5"]], tomyum: ["#E98A2E", ["#C1272D", "#7CB342", "#F7E7C6"]],
  green: ["#A3B84A", ["#2E5E1E", "#F4E3B5", "#C1272D"]], soup: ["#E8C066", ["#5E8C31", "#F7F0DC", "#B3121F"]],
  tea: ["#E8892B", []], namplaprik: ["#C98A2B", ["#D62828", "#F1E3B4"]], ice: ["#CBEAF6", []],
  fruit: ["#F6C445", []], rice: ["#F4EEDC", ["#E3D9BF"]], soy: ["#5A2E14", []], crackling: ["#E6B771", []]
};
var BAND = "#E07A1F", BAND2 = "#B85B10", PLASTIC = "rgba(255,255,255,.42)", EDGE = "rgba(70,76,84,.6)";

function clamp(t) { return t < 0 ? 0 : t > 1 ? 1 : t; }
function merge(a, b) { var o = {}, k; for (k in a) o[k] = a[k]; for (k in b) if (k !== "reset") o[k] = b[k]; return o; }

function wTied(u, st) {
  var tab = st.tab > 0.5;
  if (u < 38) return tab ? 46 : 18 + (38 - u) * 1.65;
  var nw = tab ? 26 : 18 + (st.straw > 0.5 ? 4 : 0);
  if (u < 88) return nw;
  if (u < 150) { var e = ease((u - 88) / 62); return nw + (182 - (nw - 18)) * e + 14 * st.air * e; }
  return 200 + 14 * st.air * Math.sin(Math.min(1, (u - 150) / 170) * Math.PI * 0.9);
}
function wOpen(u) { return 150 + 50 * Math.min(1, u / 290); }
function wAt(u, st) { return lerp(wOpen(u), wTied(u, st), ease(st.g)); }
function geo(st) { var s = st.size, top = 195 - 165 * s; return {s: s, top: top, y: function (u) { return top + u * s; }}; }

function bodyPath(ctx, st, G, u0) {
  var s = G.s, u, pts = [];
  ctx.beginPath();
  for (u = u0; u <= 290; u += 3) ctx.lineTo(CX - wAt(u, st) / 2 * s, G.y(u));
  var wb = wAt(290, st) / 2 * s;
  for (var i = 0; i <= 24; i++) { var a = Math.PI - Math.PI * i / 24; ctx.lineTo(CX + wb * Math.cos(a), G.y(290) + 34 * s * Math.sin(a)); }
  for (u = 290; u >= u0; u -= 3) ctx.lineTo(CX + wAt(u, st) / 2 * s, G.y(u));
  ctx.closePath();
}
function tipPath(ctx, st, G, u0) {
  var s = G.s, u;
  ctx.beginPath();
  for (u = u0; u <= 40; u += 2) ctx.lineTo(CX - wAt(u, st) / 2 * s, G.y(u));
  for (u = 40; u >= u0; u -= 2) ctx.lineTo(CX + wAt(u, st) / 2 * s, G.y(u));
  if (st.g > 0.6 && st.tab < 0.5) {
    var w0 = wAt(u0, st) * s, n = 8;
    for (var i = n; i >= 0; i--) ctx.lineTo(CX - w0 / 2 + w0 * i / n, G.y(u0) + (i % 2 ? 0 : 5 * s * st.g));
  }
  ctx.closePath();
}
function rr(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function plastic(ctx, s) {
  ctx.fillStyle = PLASTIC; ctx.fill();
  ctx.strokeStyle = EDGE; ctx.lineWidth = Math.max(1.3, 2.2 * s); ctx.lineJoin = "round"; ctx.stroke();
}
function contents(ctx, st, G, seed, clipFn) {
  var c = C[st.contents] || C.curry, s = G.s;
  var lv = st.level;
  ctx.save(); clipFn(); ctx.clip();
  var y0 = G.y(lv);
  ctx.fillStyle = c[0]; ctx.fillRect(0, y0, W, H);
  ctx.strokeStyle = "rgba(255,255,255,.4)"; ctx.lineWidth = 3 * s;
  ctx.beginPath(); ctx.moveTo(0, y0); ctx.quadraticCurveTo(CX, y0 + 8 * s, W, y0); ctx.stroke();
  var r = K.rnd(seed);
  var bits = c[1];
  for (var j = 0; bits.length && j < 22; j++) {
    var bx = CX + (r() - 0.5) * 170 * s, by = G.y(lv + 18 + r() * (300 - lv));
    ctx.fillStyle = bits[j % bits.length];
    ctx.beginPath();
    if (j % 3 === 0) ctx.ellipse(bx, by, 9 * s, 4 * s, r() * 3, 0, Math.PI * 2);
    else ctx.arc(bx, by, (2.5 + r() * 2.5) * s, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}
function ringU(i) { return 82 - i * 7.2; }
function ring(ctx, x, y, rx, ry, frac, lw, part) {
  var a0 = Math.PI, a1 = Math.PI + 2 * Math.PI * frac;
  ctx.lineWidth = lw; ctx.lineCap = "round";
  if (part === "back") {
    var e = Math.min(a1, 2 * Math.PI);
    if (e > a0) { ctx.strokeStyle = BAND2; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, a0, e); ctx.stroke(); }
  } else if (a1 > 2 * Math.PI) {
    ctx.strokeStyle = BAND; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 2 * Math.PI, a1); ctx.stroke();
  }
}
function rings(ctx, st, G, part) {
  var s = G.s, n = Math.ceil(st.wraps - 1e-6);
  if (n <= 0) return;
  for (var i = 0; i < n; i++) {
    var frac = clamp(st.wraps - i), u = ringU(i);
    var rx = (wAt(u, st) / 2 + 2.6) * s, cx = CX;
    var y = G.y(u);
    ring(ctx, cx, y, rx, 3.6 * s, frac, 3.4 * s, part);
  }
}
function lockLoop(ctx, st, G, part) {
  var L = st.lock, s = G.s;
  if (L <= 0.001 || L >= 1.999) return;
  var n = Math.max(1, Math.ceil(st.wraps - 1e-6)), uTop = ringU(n - 1), u, rx, a = 1;
  var rxTip = (wAt(0, st) / 2 + 7) * s, rxN = (wAt(31, st) / 2 + 3) * s;
  if (L < 0.5) { u = lerp(uTop, -10, ease(L / 0.5)); rx = lerp((wAt(uTop, st) / 2 + 3) * s, rxTip, ease(L / 0.5)); }
  else if (L <= 1) { u = lerp(-10, 31, ease((L - 0.5) / 0.5)); rx = lerp(rxTip, rxN, ease((L - 0.5) / 0.5)); }
  else if (L < 1.5) { u = lerp(31, -10, ease((L - 1) / 0.5)); rx = lerp(rxN, rxTip, ease((L - 1) / 0.5)); }
  else { u = lerp(-10, -60, ease((L - 1.5) / 0.5)); rx = rxTip; a = 1 - (L - 1.5) / 0.5; }
  var y = G.y(u), yt = G.y(uTop);
  ctx.globalAlpha = a * (st.wraps > 0.01 ? 1 : 0);
  if (part === "front") {
    ctx.strokeStyle = BAND; ctx.lineWidth = 3 * s; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(CX - (wAt(uTop, st) / 2 + 2.6) * s, yt); ctx.lineTo(CX - rx * 0.9, y);
    ctx.moveTo(CX + (wAt(uTop, st) / 2 + 2.6) * s, yt); ctx.lineTo(CX + rx * 0.9, y); ctx.stroke();
  }
  ring(ctx, CX, y, rx, 3.6 * s, 1, 3.4 * s, part);
  ctx.globalAlpha = 1;
}
function drawBalloon(ctx, st, seed) {
  var G = geo(st), s = G.s, u0 = 0;
  rings(ctx, st, G, "back"); lockLoop(ctx, st, G, "back");
  var clip = function () { bodyPath(ctx, st, G, 38); };
  bodyPath(ctx, st, G, 38); ctx.fillStyle = PLASTIC; ctx.fill();
  contents(ctx, st, G, seed, clip);
  bodyPath(ctx, st, G, 38); ctx.strokeStyle = EDGE; ctx.lineWidth = Math.max(1.3, 2.2 * s); ctx.stroke();
  ctx.save();
  tipPath(ctx, st, G, u0); plastic(ctx, s);
  ctx.restore();
  rings(ctx, st, G, "front"); lockLoop(ctx, st, G, "front");
}

function room(S) {
  var c = S.c, hh = S.hh, t = S.t, u = (t % 6000) / 6000;
  
  var top = S.deck - hh * 2.1;
  K.ground(c, S.x0, S.x1, S.deck, S.H, S.night ? '#2a1d18' : '#7a5a3a');
  K.sala(c, S.x0 + S.span * 0.1, S.x1 - S.span * 0.1, S.deck, top, S.night, S.night ? '#5a241c' : '#8a3a28');

  // Lanna magic
  if (S.night) {
    K.khomLoi(S, 3);
  } else {
    K.motes(S, 6);
  }
  for (var i = 0; i < 3; i++) {
    var kx = S.x0 + S.span * (0.3 + i * 0.2);
    K.lanternGlow(c, kx, top + hh * 0.3, hh * 0.4, 45, S.night ? 1 : 0.4);
  }

  // Merchant table
  var tx = S.x0 + S.span * 0.5, ty = S.deck - hh * 0.4, tw = hh * 1.5;
  c.fillStyle = '#4a2c18'; c.fillRect(tx - tw * 0.5, ty, tw, hh * 0.4);

  // Figure
  var crew = K.town(S, 1, { mohom: 1 }), mer = crew[0];
  mer.dir = -1;
  var WP = K.POSE.stand;
  K.person(c, tx + tw * 0.3, ty, hh * 0.8, K.mix(WP, WP, 0), mer);

  // Animate bag tie process
  // Wraps goes 0 to 4, lock goes 0 to 2 over loop
  var tu = (t % 3000) / 3000;
  var wraps = clamp(tu * 8); if (wraps > 4) wraps = 4;
  var lock = tu > 0.5 ? clamp((tu - 0.5) * 4) * 2 : 0;
  if (tu > 0.9) { wraps = 4; lock = 2; }
  
  var st = { g: 1, air: 0.7, size: 0.4, wraps: wraps, lock: lock, level: 140, contents: 'curry', tab: 0 };
  c.save();
  c.translate(tx - tw * 0.2 - CX * 0.4, ty - 150 * 0.4);
  c.scale(0.8, 0.8);
  drawBalloon(c, st, S.seed);
  c.restore();
  
  var st2 = { g: 1, air: 0.7, size: 0.4, wraps: 4, lock: 2, level: 140, contents: 'tomyum', tab: 0 };
  c.save();
  c.translate(tx - CX * 0.4, ty - 150 * 0.4);
  c.scale(0.8, 0.8);
  drawBalloon(c, st2, S.seed + 1);
  c.restore();

  var st3 = { g: 1, air: 0.7, size: 0.4, wraps: 4, lock: 2, level: 140, contents: 'green', tab: 0 };
  c.save();
  c.translate(tx + tw * 0.2 - CX * 0.4, ty - 150 * 0.4);
  c.scale(0.8, 0.8);
  drawBalloon(c, st3, S.seed + 2);
  c.restore();

  if (S.label) {
    c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif';
    K.banner(c, tx, top + hh * 0.05, S.label, hh, '#c0392b', S.seed, S.hits);
  }
}

D.addScene('bag-knots', room, /\b(?:bags?|knots?|bag ties?|rubber bands?|street food|soups?)\b|แกง|ถุง/i, 'x = r cos θ', 1);
})();
