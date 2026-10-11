import re

with open('assets/front/doodler.js', 'r') as f:
    content = f.read()

learn_code = """  learn: function (S) {
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
  },"""

old_code = re.search(r"  learn: function \(S\) \{.*?\},\n", content, re.DOTALL).group(0)
content = content.replace(old_code, learn_code + '\n')
content = content.replace("var VERSIONS = {}, VARIANTS = {};", "var VERSIONS = { 'learn': 2 }, VARIANTS = {}; // version 2: hanging lanterns, lai kham blackboard, raising hands, notebooks, fireflies")

with open('assets/front/doodler.js', 'w') as f:
    f.write(content)

