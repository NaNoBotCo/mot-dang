/* Ban Sabai Village animation for auto-doodler */
/* https://motdang.net/sites/ban-sabai/ */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit;
var TAU = K.TAU;

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t / 1000;
  var night = S.night;
  
  var tx = (S.x0 + S.x1) / 2;
  var span = (S.x1 - S.x0);
  
  // garden
  K.ground(c, S.x0, S.x1, S.deck, S.H, night ? '#16301f' : '#8dbb7a');

  // the pool
  var cy = S.deck - S.hh * 0.2;
  var prx = Math.min(span * 0.24, 320), pry = S.hh * 0.6;
  
  c.fillStyle = night ? '#cfc3a4' : '#e9dfc6';
  c.beginPath(); c.ellipse(tx, cy, prx + 10, pry + 7, 0, 0, TAU); c.fill();
  
  var pg = c.createRadialGradient(tx, cy - pry * 0.3, 4, tx, cy, prx);
  pg.addColorStop(0, night ? '#3aa8c4' : '#9fe6dc');
  pg.addColorStop(1, night ? '#11526a' : '#2a9d8f');
  c.fillStyle = pg;
  c.beginPath(); c.ellipse(tx, cy, prx, pry, 0, 0, TAU); c.fill();
  
  c.save(); 
  c.beginPath(); c.ellipse(tx, cy, prx, pry, 0, 0, TAU); c.clip();
  c.strokeStyle = night ? 'rgba(255,240,190,.25)' : 'rgba(255,255,255,.55)'; 
  c.lineWidth = 1.2;
  for (var k = 0; k < 9; k++) {
    c.beginPath();
    for (var xx = tx - prx; xx <= tx + prx; xx += 6) {
      var yy = cy - pry + k * pry * 0.24 + Math.sin(xx / 17 + t * 1.6 + k) * 2.2;
      xx === tx - prx ? c.moveTo(xx, yy) : c.lineTo(xx, yy);
    }
    c.stroke();
  }
  c.restore();

  // 21 units around the pool
  var N = 21;
  var rx = Math.min(span * 0.42, 560), ry = S.hh * 1.4;
  var cy2 = S.deck - S.hh * 0.1;
  
  // sort units back to front
  var units = [];
  for (var i = 0; i < N; i++) {
    var frac = i / (N - 1);
    var a = (150 + 240 * frac) * Math.PI / 180;
    var x = tx + rx * Math.cos(a);
    var y = cy2 + ry * Math.sin(a);
    var s = 0.78 + 0.42 * ((y - (cy2 - ry)) / (2 * ry));
    s *= (S.hh / 50); // scale to fit scene
    units.push({x: x, y: y, s: s, i: i, two: (i === 5 || i === 15)});
  }
  units.sort(function(a, b) { return a.y - b.y; });
  
  units.forEach(function(u) {
    var s = u.s, w = 34 * s, hgt = (u.two ? 30 : 18) * s, x = u.x, y = u.y, sway = Math.sin(t * 0.8 + u.i) * 1.5;
    
    if (u.i % 2 === 0) {
      c.fillStyle = night ? '#1f3b29' : '#4f8f55';
      c.beginPath(); c.arc(x + w * 0.72 + sway, y - hgt - 10 * s, 11 * s, 0, TAU); c.fill();
      c.fillStyle = night ? '#2a1f17' : '#6b4a2f';
      c.fillRect(x + w * 0.7, y - hgt - 2 * s, 2.4 * s, hgt);
    }
    
    c.fillStyle = night ? '#cdbf9f' : '#f7efdd';
    c.fillRect(x - w / 2, y - hgt, w, hgt);
    c.strokeStyle = night ? '#6d5b44' : '#8a6a46'; 
    c.lineWidth = Math.max(0.8, s); 
    c.strokeRect(x - w / 2, y - hgt, w, hgt);
    
    c.beginPath(); c.moveTo(x - w * 0.62, y - hgt + 1); c.lineTo(x, y - hgt - 15 * s); c.lineTo(x + w * 0.62, y - hgt + 1); c.closePath();
    c.fillStyle = night ? '#7a3a22' : '#b4532d'; c.fill();
    
    c.strokeStyle = night ? '#4d3320' : '#7a4a28'; c.lineWidth = 1.6 * s; 
    c.beginPath(); c.moveTo(x - 5 * s, y - hgt - 20 * s); c.lineTo(x + 1 * s, y - hgt - 13 * s); 
    c.moveTo(x + 5 * s, y - hgt - 20 * s); c.lineTo(x - 1 * s, y - hgt - 13 * s); c.stroke();
    
    var on = night && (u.i % 3 !== 0);
    c.fillStyle = on ? '#ffd27a' : (night ? '#3b4a55' : '#9fb7bd');
    var ww = 6 * s, wh = 6 * s;
    c.fillRect(x - w * 0.32, y - hgt * 0.62, ww, wh); c.fillRect(x + w * 0.32 - ww, y - hgt * 0.62, ww, wh);
    if (u.two) { c.fillRect(x - w * 0.32, y - hgt * 0.25, ww, wh); c.fillRect(x + w * 0.32 - ww, y - hgt * 0.25, ww, wh); }
    
    c.fillStyle = night ? '#4d3320' : '#7a4a28'; c.fillRect(x - 3 * s, y - 9 * s, 6 * s, 9 * s);
  });

  // Lanna magic
  if (night) {
    if (K.khomLoi) K.khomLoi(S, 4);
    if (K.fireflies) K.fireflies(c, tx, cy, prx, pry, t);
  } else {
    if (K.motes) K.motes(S, 6);
  }

  // Dressed figures using K.town and K.person
  if (K.town && K.person && K.POSE && K.mix) {
    var crew = K.town(S, 2, { casual: 2 });
    crew[0].dir = 1;
    crew[1].dir = -1;
    
    var walkPhase = (t * 0.8) % 1;
    var wPose = K.mix(K.POSE.stand, K.POSE.stand, 0); // we can just use stand or mix something
    // let's animate arms a bit for motion
    var pose = { lean: 0, legs: [0.06, 0, -0.06, 0], arms: [0.12 + Math.sin(t * 2) * 0.1, 0.1, -0.1 + Math.sin(t * 2 + Math.PI) * 0.1, 0.05] };
    
    K.person(c, tx - prx - S.hh * 0.5, S.deck, S.hh * 0.85, pose, crew[0]);
    
    // sitting figure
    K.person(c, tx + prx + S.hh * 0.5, S.deck, S.hh * 0.85, K.POSE.sit || pose, crew[1]);
  }

  if (S.label && K.banner) {
    K.banner(c, tx, S.deck - S.hh * 2.5, S.label, S.hh, '#2a9d8f', S.seed, S.hits);
  }
}

D.addScene('ban-sabai', draw, /\b(?:care ?homes?|aged care|assisted living|nursing|elderly|seniors?|retire\w*)\b|บ้านพัก|ผู้สูงอายุ/i, 'n = 21', 1);

})();
