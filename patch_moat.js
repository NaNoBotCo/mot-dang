const fs = require('fs');
let code = fs.readFileSync('assets/front/doodler-moat.js', 'utf8');

// Insert version line at the end
const verLine = "D.versions = D.versions || {};\nD.versions['moat:tha-phae-gate'] = 2; // added Lanna fon lep dancers, tung flags, and a khom loi release\n";
code = code.replace(/window\.MDDOODLER_MOAT = /, verLine + "window.MDDOODLER_MOAT = ");

// Add magic to the end of draw function
const drawEnd = "  S.hits.push({ k: 'event', x0: S.x0, x1: S.x1, y0: E.wall[2], y1: S.H });\n}";
const magicCode = `
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
`;
code = code.replace(drawEnd, magicCode + drawEnd);

fs.writeFileSync('assets/front/doodler-moat.js', code);
