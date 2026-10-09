(function () {
'use strict';
var SKY = window.MDSKY; if (!SKY || window.MDDOODLER) return;
var D = window.MDDOODLER, K = D.kit;

function clamp(t) { return t < 0 ? 0 : t > 1 ? 1 : t; }

function bayeuxTapestry(S) {
  var c = S.c, hh = S.hh, t = S.t, N = S.night;
  
  var top = S.deck - hh * 2.1;
  K.ground(c, S.x0, S.x1, S.deck, S.H, N ? '#1a2228' : '#3a4f3a');

  // Lanna magic: khom lanterns and motes
  if (N) {
    if (K.khomLoi) K.khomLoi(S, 6);
  } else {
    if (K.motes) K.motes(S, 8);
  }
  
  // Halley's comet, Lanna style (from the minisite)
  var cxp = S.x0 + S.span * 0.5, cyp = top - hh * 1.5;
  
  // Comet moving across the sky
  var u = (t % 15000) / 15000;
  var cometX = S.x1 + hh - u * (S.span + hh * 3);
  var cometY = top - Math.sin(u * Math.PI) * hh * 0.5;
  
  var tl = hh * 1.5;
  var ang = Math.PI - 0.2;
  var tg = c.createLinearGradient(cometX, cometY, cometX + Math.cos(ang) * tl, cometY + Math.sin(ang) * tl);
  tg.addColorStop(0, "rgba(255,240,200,.9)"); tg.addColorStop(1, "rgba(255,240,200,0)");
  c.strokeStyle = tg; c.lineWidth = Math.max(3, hh * 0.1); c.lineCap = "round"; 
  c.beginPath(); c.moveTo(cometX, cometY); c.lineTo(cometX + Math.cos(ang) * tl, cometY + Math.sin(ang) * tl); c.stroke();
  c.fillStyle = "#fff"; c.beginPath(); c.arc(cometX, cometY, Math.max(2, hh * 0.08), 0, Math.PI * 2); c.fill();

  // Dressed figures looking at the comet
  var crew = K.town(S, 2, { casual: 0.2, mohom: 0.8 });
  var pose = { lean: -0.15, arms: [0.2, -0.4, 3.5, 3.6], legs: [0, 0, 0, 0] }; // point up
  var WP = K.POSE && K.POSE.stand ? K.POSE.stand : pose;
  var armAnim = Math.sin(t / 800) * 0.1;
  var pose1 = { lean: -0.1, arms: [0.3 + armAnim, 0.4 + armAnim, 3.2, 3.3], legs: [0.1, 0, -0.1, 0] };
  var pose2 = { lean: -0.15, arms: [3.4 + armAnim, 3.5 + armAnim, 0.5, 0.6], legs: [0, 0, 0, 0] };

  var p1 = crew[0]; p1.dir = -1;
  if (K.person) {
    K.person(c, S.x0 + S.span * 0.6, S.deck, hh * 0.75, pose1, p1);
    K.person(c, S.x0 + S.span * 0.75, S.deck, hh * 0.7, pose2, crew[1]);
  }

  // Banner
  if (S.label && K.banner) {
    c.font = '800 ' + Math.round(Math.max(12, hh * 0.2)) + 'px "Sarabun",system-ui,sans-serif';
    K.banner(c, S.x0 + S.span * 0.5, top + hh * 0.2, S.label, hh, '#c0392b', S.seed, S.hits);
  }
}

D.addScene('bayeux-tapestry', bayeuxTapestry, [['bayeux-tapestry', /\b(tapestry|embroidery|stitch|sew|woven|needlework|history|historical|เย็บปัก|ทอผ้า|ประวัติศาสตร์)\b/i]], 'r = a(1-e²)/(1+e cos θ)', 1);
})();
