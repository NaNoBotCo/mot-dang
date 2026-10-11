/* Stork scenes, drawn for the stork video (2026-10-05; stork-video/doodles/ holds the originals
   and their renderer). Nan, 2026-10-05: "add the doodles to the doodle page whenever we do
   something like this." No words, so the front page's band never picks them; /doodles/ lists
   them under Scenes. Each block below is one scene file, unchanged. */

/* ---- stork-title ---- */
/* Doodles for stork video — Title card
   'stork-title'  Letters cut out and laid down one by one, then a white stork lands on the S.
                  Subject: "STORKS" with นกกระสา under it, small: "creepy birds, and why we love them"
                  Ground: cream paper · Palette: cream paper, ink black, one red.
   Render stills: node doodles/render.mjs stork-title --still 1 --out work/look-title-1.jpg --bg none
                  node doodles/render.mjs stork-title --still 4 --out work/look-title-4.jpg --bg none
                  node doodles/render.mjs stork-title --still 8 --out work/look-title-8.jpg --bg none */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

var INK = '#181614';
var CREAM = '#faf7ef';
var RED = '#c93826';

/* helper for ellipse path */
function ellPath(x, y, rx, ry, rot) {
  return function (q) {
    q.beginPath();
    q.ellipse(x, y, rx, ry, rot || 0, 0, TAU);
  };
}

/* ---------------------------------------------------------------- letterforms
   Refined cut-paper woodblock typography: bold, stable, with clean perches. */
function pathS(q, x, y, w, h) {
  q.beginPath();
  /* Upper terminal: horizontal cut */
  q.moveTo(x + w * 0.66, y + h * 0.30);
  q.lineTo(x + w * 0.92, y + h * 0.30);

  /* Upper outer curve: around top arch to upper-left shoulder */
  q.bezierCurveTo(x + w * 0.92, y + h * 0.08, x + w * 0.74, y, x + w * 0.50, y);
  q.bezierCurveTo(x + w * 0.26, y, x + w * 0.06, y + h * 0.08, x + w * 0.06, y + h * 0.28);

  /* Left outer shoulder down into lower spine/waist */
  q.bezierCurveTo(x + w * 0.06, y + h * 0.42, x + w * 0.22, y + h * 0.50, x + w * 0.42, y + h * 0.54);

  /* Across diagonal spine into lower inner counter */
  q.bezierCurveTo(x + w * 0.62, y + h * 0.58, x + w * 0.72, y + h * 0.66, x + w * 0.72, y + h * 0.75);
  q.bezierCurveTo(x + w * 0.72, y + h * 0.83, x + w * 0.58, y + h * 0.84, x + w * 0.42, y + h * 0.84);
  q.bezierCurveTo(x + w * 0.30, y + h * 0.84, x + w * 0.25, y + h * 0.78, x + w * 0.34, y + h * 0.70);

  /* Lower terminal: horizontal cut */
  q.lineTo(x + w * 0.08, y + h * 0.70);

  /* Lower outer curve: around bottom arch to lower-right shoulder */
  q.bezierCurveTo(x + w * 0.08, y + h * 0.92, x + w * 0.26, y + h, x + w * 0.50, y + h);
  q.bezierCurveTo(x + w * 0.74, y + h, x + w * 0.94, y + h * 0.92, x + w * 0.94, y + h * 0.72);

  /* Right outer shoulder up into upper spine/waist */
  q.bezierCurveTo(x + w * 0.94, y + h * 0.58, x + w * 0.78, y + h * 0.50, x + w * 0.58, y + h * 0.46);

  /* Across diagonal spine into upper inner counter */
  q.bezierCurveTo(x + w * 0.38, y + h * 0.42, x + w * 0.28, y + h * 0.34, x + w * 0.28, y + h * 0.25);
  q.bezierCurveTo(x + w * 0.28, y + h * 0.17, x + w * 0.42, y + h * 0.16, x + w * 0.58, y + h * 0.16);
  q.bezierCurveTo(x + w * 0.70, y + h * 0.16, x + w * 0.75, y + h * 0.22, x + w * 0.66, y + h * 0.30);

  q.closePath();
}

function pathT(q, x, y, w, h) {
  var bw = h * 0.16, sw = w * 0.27, cx = x + w / 2;
  q.beginPath();
  q.moveTo(x, y);
  q.lineTo(x + w, y);
  q.lineTo(x + w, y + bw);
  q.lineTo(cx + sw / 2, y + bw);
  q.lineTo(cx + sw / 2, y + h);
  q.lineTo(cx - sw / 2, y + h);
  q.lineTo(cx - sw / 2, y + bw);
  q.lineTo(x, y + bw);
  q.closePath();
}

function pathO(q, x, y, w, h) {
  var cx = x + w / 2, cy = y + h / 2, rx = w / 2, ry = h / 2;
  var irx = rx * 0.52, iry = ry * 0.68;
  q.beginPath();
  q.ellipse(cx, cy, rx, ry, 0, 0, TAU);
  q.ellipse(cx, cy, irx, iry, 0, 0, TAU);
}

function pathR(q, x, y, w, h) {
  var sw = w * 0.26, bw = h * 0.16, my = y + h * 0.52;
  q.beginPath();
  q.moveTo(x, y);
  q.lineTo(x + w * 0.68, y);
  q.bezierCurveTo(x + w * 1.02, y, x + w * 1.02, my, x + w * 0.65, my);
  /* diagonal leg kicking down-right */
  q.lineTo(x + w * 0.70, my);
  q.lineTo(x + w * 0.98, y + h);
  q.lineTo(x + w * 0.68, y + h);
  q.lineTo(x + sw + w * 0.10, my + h * 0.02);
  q.lineTo(x + sw, my + h * 0.02);
  q.lineTo(x + sw, y + h);
  q.lineTo(x, y + h);
  q.closePath();
  /* inner counter of R */
  q.moveTo(x + sw, y + bw);
  q.lineTo(x + w * 0.58, y + bw);
  q.bezierCurveTo(x + w * 0.78, y + bw, x + w * 0.78, my - bw * 0.6, x + w * 0.58, my - bw * 0.6);
  q.lineTo(x + sw, my - bw * 0.6);
  q.closePath();
}

function pathK(q, x, y, w, h) {
  var sw = w * 0.26;
  q.beginPath();
  /* vertical stem */
  q.moveTo(x, y);
  q.lineTo(x + sw, y);
  q.lineTo(x + sw, y + h * 0.40);
  /* upper arm */
  q.lineTo(x + w * 0.74, y);
  q.lineTo(x + w, y);
  q.lineTo(x + sw + w * 0.08, y + h * 0.48);
  /* lower leg branching from same waist */
  q.lineTo(x + w, y + h);
  q.lineTo(x + w * 0.70, y + h);
  q.lineTo(x + sw, y + h * 0.58);
  q.lineTo(x + sw, y + h);
  q.lineTo(x, y + h);
  q.closePath();
}

/* ---------------------------------------------------------------- the stork
   White Stork (Ciconia ciconia): pure white plumage, jet black flight
   primaries with emarginated spread fingers in flight, folded over the tail
   when perched; long red stilt legs with gripping toes; long straight red dagger bill. */
function drawStork(c, px, py, u, S) {
  var flare = S.flare || 0;
  var perched = S.perched;
  var clatter = S.clatter || 0;
  var flap = S.wingFlap || 0;
  var turn = S.headTurn || 0;

  c.save();
  c.lineCap = 'round';
  c.lineJoin = 'round';

  /* Stork body center relative to feet */
  var bodyX = perched ? px + u * 0.6 : lerp(px - u * 2.2, px, flare);
  var bodyY = perched ? py - u * 3.6 : lerp(py - u * 4.8, py - u * 4.0, flare);

  /* 1. Legs: bright vermilion red */
  c.strokeStyle = RED;
  c.lineWidth = Math.max(2.6, u * 0.15);

  if (perched) {
    /* Left leg: straight down with slight backward knee bend */
    c.beginPath();
    c.moveTo(px - u * 0.1, py);
    c.lineTo(px - u * 0.24, py - u * 1.8);
    c.lineTo(bodyX - u * 0.25, bodyY + u * 0.5);
    c.stroke();
    /* Left foot gripping perch: forward toes wrapping edge and hind hallux */
    c.beginPath();
    c.moveTo(px - u * 0.35, py);
    c.lineTo(px + u * 0.25, py);
    c.lineTo(px + u * 0.30, py + u * 0.14);
    c.stroke();

    /* Right leg: standing firm beside left leg */
    c.beginPath();
    c.moveTo(px + u * 0.35, py);
    c.lineTo(px + u * 0.22, py - u * 1.7);
    c.lineTo(bodyX + u * 0.05, bodyY + u * 0.5);
    c.stroke();
    /* Right foot gripping perch */
    c.beginPath();
    c.moveTo(px + u * 0.05, py);
    c.lineTo(px + u * 0.65, py);
    c.lineTo(px + u * 0.70, py + u * 0.14);
    c.stroke();
  } else {
    /* Flying/flaring legs trailing and swinging forward */
    var legAngle = lerp(0.85, -0.18, flare);
    c.beginPath();
    c.moveTo(bodyX - u * 0.2, bodyY + u * 0.5);
    c.lineTo(bodyX - u * 1.4 * Math.cos(legAngle), bodyY + u * 0.5 + u * 1.6 * Math.sin(legAngle + 0.4));
    c.lineTo(px - u * 0.1, py);
    c.stroke();
    c.beginPath();
    c.moveTo(bodyX + u * 0.1, bodyY + u * 0.5);
    c.lineTo(bodyX + u * 0.2 - u * 1.4 * Math.cos(legAngle), bodyY + u * 0.5 + u * 1.6 * Math.sin(legAngle + 0.4));
    c.lineTo(px + u * 0.25, py);
    c.stroke();
  }

  /* 2. Tail: black flight feathers extending beyond rump */
  paper(c, poly([
    [bodyX - u * 1.3, bodyY + u * 0.1],
    [bodyX - u * 2.7, bodyY + u * 0.6],
    [bodyX - u * 2.5, bodyY + u * 1.0],
    [bodyX - u * 1.1, bodyY + u * 0.8]
  ]), INK, 1.2);

  /* 3. Main body: pure cream/white paper */
  paper(c, ellPath(bodyX, bodyY, u * 1.7, u * 0.95, -0.18), CREAM, 1.6);

  /* 4. Wings */
  if (perched) {
    /* Folded wing: white coverts over jet-black flight primaries */
    paper(c, poly([
      [bodyX - u * 0.4, bodyY - u * 0.3],
      [bodyX - u * 2.4, bodyY + u * 0.5],
      [bodyX - u * 2.1, bodyY + u * 0.9],
      [bodyX - u * 0.1, bodyY + u * 0.6]
    ]), INK, 1.4);
    /* White wing covert flap over it */
    paper(c, ellPath(bodyX - u * 0.15, bodyY - u * 0.08, u * 1.35, u * 0.65, -0.15), CREAM, 1.8);
  } else {
    /* Open wings during flight/flare: raised high and spread with primary feather fingers */
    var shX = bodyX - u * 0.1, shY = bodyY - u * 0.6;
    var flapOff = flap * u * 0.8;

    /* Left wing (far side): raised high and back */
    var lTipX = shX - u * 2.2, lTipY = shY - u * 3.4 + flapOff;
    paper(c, poly([
      [shX - u * 0.4, shY + u * 0.2],
      [lTipX - u * 0.6, lTipY - u * 0.2],
      [lTipX, lTipY],
      [lTipX + u * 0.5, lTipY + u * 0.4],
      [shX - u * 0.8, shY + u * 0.6]
    ]), INK, 1.1);

    /* Right wing (near side): sweeping up and fanning wide above back */
    var rTipX = shX + u * 0.4, rTipY = shY - u * 3.8 + flapOff;
    paper(c, poly([
      [shX + u * 0.3, shY],
      [rTipX - u * 1.0, rTipY + u * 0.2], /* primary finger 1 */
      [rTipX - u * 0.5, rTipY - u * 0.3], /* primary finger 2 */
      [rTipX, rTipY - u * 0.4],           /* primary finger 3 (apex) */
      [rTipX + u * 0.6, rTipY],           /* primary finger 4 */
      [rTipX + u * 1.0, rTipY + u * 0.6], /* primary finger 5 */
      [shX + u * 1.2, shY + u * 0.4],
      [shX + u * 0.2, shY + u * 0.5]
    ]), INK, 2.2);

    /* White upper wing covert */
    paper(c, poly([
      [shX - u * 0.2, shY + u * 0.2],
      [rTipX - u * 0.4, rTipY + u * 1.2],
      [rTipX + u * 0.4, rTipY + u * 1.4],
      [shX + u * 0.6, shY + u * 0.4]
    ]), CREAM, 2.4);
  }

  /* 5. Neck and Head */
  var neckBaseX = bodyX + u * 1.1;
  var neckBaseY = bodyY - u * 0.2;
  /* During clatter, stork tosses head up/back */
  var headPitch = perched ? lerp(-0.06, 0.44, clatter) : lerp(0.08, -0.22, flare);
  var headX = neckBaseX + u * (perched ? 0.9 : 1.4) + turn * u * 0.3;
  var headY = neckBaseY - u * (perched ? 2.3 : 1.7) - headPitch * u * 0.9;

  /* S-curve neck in white/cream */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(neckBaseX - u * 0.3, neckBaseY);
    q.bezierCurveTo(neckBaseX + u * 0.6, neckBaseY - u * 1.2, headX - u * 0.6, headY + u * 0.9, headX - u * 0.2, headY + u * 0.15);
    q.lineTo(headX + u * 0.2, headY + u * 0.15);
    q.bezierCurveTo(headX - u * 0.1, headY + u * 1.1, neckBaseX + u * 1.1, neckBaseY - u * 0.9, neckBaseX + u * 0.3, neckBaseY + u * 0.15);
    q.closePath();
  }, CREAM, 1.8);

  /* Head */
  paper(c, ellPath(headX, headY, u * 0.55, u * 0.45, headPitch), CREAM, 2.0);

  /* Eye: black with bright white catchlight */
  c.fillStyle = INK;
  c.beginPath();
  c.arc(headX + u * 0.15, headY - u * 0.08, u * 0.09, 0, TAU);
  c.fill();
  c.fillStyle = '#fff';
  c.beginPath();
  c.arc(headX + u * 0.18, headY - u * 0.11, u * 0.03, 0, TAU);
  c.fill();

  /* 6. Long red bill (mandibles part and clatter) */
  var billLen = u * 2.5;
  var billAngle = headPitch - 0.06;
  var billBaseX = headX + u * 0.38;
  var billBaseY = headY + u * 0.04;
  var billTipX = billBaseX + billLen * Math.cos(billAngle);
  var billTipY = billBaseY + billLen * Math.sin(billAngle);

  var clatGap = clatter * u * 0.34;

  /* Upper mandible: straight sharp dagger */
  paper(c, poly([
    [billBaseX, billBaseY - u * 0.16],
    [billTipX, billTipY - clatGap * 0.5],
    [billBaseX + u * 0.25, billBaseY]
  ]), RED, 2.2);

  /* Lower mandible */
  paper(c, poly([
    [billBaseX + u * 0.08, billBaseY + 1],
    [billTipX, billTipY + clatGap * 0.5],
    [billBaseX, billBaseY + u * 0.20]
  ]), RED, 2.2);

  c.restore();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;
  var T = 12000;
  var p = (t % T) / 1000; /* time in seconds 0..12 */

  /* 1. Ground: Cream paper with warm vignette gradient */
  var bg = c.createRadialGradient(W * 0.5, H * 0.5, H * 0.15, W * 0.5, H * 0.5, W * 0.72);
  bg.addColorStop(0, '#fbf7ee');
  bg.addColorStop(0.7, '#f4ece0');
  bg.addColorStop(1, '#ebdcc3');
  c.fillStyle = bg;
  c.fillRect(0, 0, W, H);

  /* Subtle vintage print margin rule */
  c.save();
  c.strokeStyle = 'rgba(24, 22, 20, 0.16)';
  c.lineWidth = 1.5;
  var pad = 44;
  c.strokeRect(pad, pad, W - pad * 2, H - pad * 2);
  c.restore();

  /* 2. Letters layout for "STORKS" */
  var letters = [
    { char: 'S', fn: pathS, w: 128, tilt: 0.008 },
    { char: 'T', fn: pathT, w: 136, tilt: -0.005 },
    { char: 'O', fn: pathO, w: 150, tilt: 0.004 },
    { char: 'R', fn: pathR, w: 144, tilt: -0.006 },
    { char: 'K', fn: pathK, w: 144, tilt: 0.005 },
    { char: 'S', fn: pathS, w: 128, tilt: -0.004 }
  ];

  var gap = 30;
  var LH = 196;
  var totalW = 0;
  letters.forEach(function (L, i) { totalW += L.w + (i ? gap : 0); });

  var startX = (W - totalW) / 2;
  var letterY = H * 0.51; /* top of letters at ~550px, leaving 0..550px clear above for the stork */

  /* Perch location for the stork: top flat bar of the first 'S' */
  var perchX = startX + letters[0].w * 0.48;
  var perchY = letterY;

  /* Letters dropping in one by one:
     Letter 0: 0.05s - 0.35s
     Letter 1: 0.22s - 0.52s
     Letter 2: 0.39s - 0.69s
     Letter 3: 0.56s - 0.86s
     Letter 4: 0.73s - 1.03s
     Letter 5: 0.90s - 1.20s */
  var curX = startX;
  letters.forEach(function (L, i) {
    var dropStart = 0.05 + i * 0.17;
    var dropProgress = Math.max(0, Math.min(1, (p - dropStart) / 0.28));

    if (dropProgress > 0) {
      var e = ease(dropProgress);
      var yOffset = (1 - e) * -320;
      var rot = lerp((i % 2 ? 1 : -1) * 0.12, L.tilt, e);
      var lift = 1 + (1 - e) * 3.5;

      /* When the stork lands at t = 4.5s, the first 'S' gives an elastic bounce */
      var bounceY = 0;
      if (i === 0 && p > 4.4 && p < 6.0) {
        var bt = (p - 4.5);
        bounceY = Math.sin(bt * 16) * Math.exp(-bt * 4.5) * 11;
      }

      c.save();
      var cx = curX + L.w / 2;
      var cy = letterY + LH / 2 + yOffset + bounceY;
      c.translate(cx, cy);
      c.rotate(rot);

      paper(c, function (q) {
        L.fn(q, -L.w / 2, -LH / 2, L.w, LH);
      }, INK, lift);

      c.restore();
    }
    curX += L.w + gap;
  });

  /* 3. Subtitles and Red Accent: appear after letters settle (t > 1.3s) */
  var subProgress = Math.max(0, Math.min(1, (p - 1.3) / 0.6));
  if (subProgress > 0) {
    var subE = ease(subProgress);
    c.save();
    c.globalAlpha = subE;

    /* A fine red horizontal rule under "STORKS" */
    var ruleW = (totalW * 0.82) * subE;
    var ruleY = letterY + LH + 42;
    c.strokeStyle = RED;
    c.lineWidth = 3.2;
    c.beginPath();
    c.moveTo(W / 2 - ruleW / 2, ruleY);
    c.lineTo(W / 2 + ruleW / 2, ruleY);
    c.stroke();

    /* Thai subtitle: นกกระสา */
    c.fillStyle = INK;
    c.textAlign = 'center';
    c.textBaseline = 'middle';
    c.font = '700 50px "Thonburi", "Sukhumvit Set", sans-serif';
    c.fillText('นกกระสา', W / 2, ruleY + 52);

    /* English subtitle: "creepy birds, and why we love them" */
    c.font = '500 27px "Avenir Next", "Helvetica Neue", sans-serif';
    c.letterSpacing = '1.8px';
    c.fillText('creepy birds, and why we love them', W / 2, ruleY + 104);

    /* Traditional red stamp / chop in bottom right corner */
    var sealX = W / 2 + totalW * 0.40;
    var sealY = ruleY + 64;
    paper(c, poly([
      [sealX - 22, sealY - 22],
      [sealX + 22, sealY - 22],
      [sealX + 22, sealY + 22],
      [sealX - 22, sealY + 22]
    ]), RED, 1.2);

    /* Thai seal characters inside the red box: มด */
    c.fillStyle = '#faf7ef';
    c.font = '700 20px "Thonburi", sans-serif';
    c.fillText('มด', sealX, sealY);

    c.restore();
  }

  /* 4. The Stork flight, landing, and perching */
  var storkU = H * 0.046; /* unit of stork height (~50px) */

  if (p < 2.0) {
    /* Stork not yet entered */
  } else if (p >= 2.0 && p < 4.5) {
    /* Stork swoops in from upper left, flaring wings and extending legs */
    var flightP = (p - 2.0) / 2.5;
    var ef = ease(flightP);

    /* Flight trajectory from upper left down to the perch */
    var startFlyX = -100;
    var startFlyY = 40;
    var targetFootX = perchX;
    var targetFootY = perchY;

    var flyX = lerp(startFlyX, targetFootX, ef);
    var flyY = lerp(startFlyY, targetFootY, Math.pow(ef, 0.8));

    var flare = Math.max(0, (flightP - 0.40) / 0.60);
    var flap = Math.sin(p * 13) * (1 - flare * 0.5);

    drawStork(c, flyX, flyY, storkU, {
      flare: flare,
      wingFlap: flap,
      perched: false
    });
  } else if (p >= 4.5 && p < 11.2) {
    /* Stork proudly perched on the S! */
    var clat = 0;
    if (p > 6.2 && p < 9.6) {
      /* Head tossed up and mandibles clattering */
      var clatterCycle = Math.sin((p - 6.2) * 28);
      clat = 0.25 + 0.60 * Math.max(0, clatterCycle);
    }
    var headTurn = Math.sin((p - 4.5) * 1.4) * 0.18;

    drawStork(c, perchX, perchY, storkU, {
      perched: true,
      clatter: clat,
      headTurn: headTurn
    });
  } else {
    /* Smooth exit takeoff to the right */
    var exitP = Math.min(1, (p - 11.2) / 0.8);
    var ee = ease(exitP);
    var exitX = lerp(perchX, W + 140, ee);
    var exitY = lerp(perchY, -80, ee * ee);
    drawStork(c, exitX, exitY, storkU, {
      perched: false,
      flare: 0.1,
      wingFlap: Math.sin(p * 15)
    });
  }
}

D.addScene('stork-title', draw, null, 'letters: y(t) = y₀ + (y₁ − y₀)·ease(t); stork perch landing');
})();

/* ---- stork-openbill ---- */
/* Worked example 1 of 3 — a SCENE: paper-cut figures standing in the engine's own landscape.
   'stork-openbill'  two Asian openbills on vine-wrapped dead palm trunks, as in her footage:
                     one turns its head and clatters its bill, the other preens; leaves sway.
   Render: node doodles/render.mjs stork-openbill --bg full --secs 6 */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

function ell(x, y, rx, ry, rot) { return function (q) { q.beginPath(); q.ellipse(x, y, rx, ry, rot || 0, 0, TAU); }; }
/* a band along a quadratic curve, thick w0 at the start and w1 at the end */
function band(x0, y0, cx, cy, x1, y1, w0, w1) {
  var L = [], R = [];
  for (var i = 0; i <= 12; i++) {
    var u = i / 12, a = 1 - u;
    var x = a * a * x0 + 2 * a * u * cx + u * u * x1, y = a * a * y0 + 2 * a * u * cy + u * u * y1;
    var dx = 2 * a * (cx - x0) + 2 * u * (x1 - cx), dy = 2 * a * (cy - y0) + 2 * u * (y1 - cy), n = Math.hypot(dx, dy) || 1, w = lerp(w0, w1, u) / 2;
    L.push([x - dy / n * w, y + dx / n * w]); R.unshift([x + dy / n * w, y - dx / n * w]);
  }
  return poly(L.concat(R));
}

/* an openbill, facing right, feet at (x, fy); u is a tenth of its height.
   head: 0 looks ahead, 1 tucks back to preen; clap: 0..1 opens the bill's gap a touch more */
function openbill(c, x, fy, u, head, clap, night) {
  var grey = night ? '#9a9890' : '#e9e6dc', black = night ? '#141210' : '#25221f', leg = night ? '#6a5852' : '#c7a79c', horn = night ? '#3a332d' : '#5b5047';
  c.lineCap = 'round';
  /* legs: thigh hidden, the long tarsus, the backward ankle */
  c.strokeStyle = leg; c.lineWidth = u * 0.16;
  [[-0.25, 0.1], [0.3, -0.12]].forEach(function (L) {
    c.beginPath(); c.moveTo(x + L[0] * u, fy); c.lineTo(x + (L[0] + L[1]) * u, fy - 1.7 * u); c.lineTo(x + L[0] * 0.5 * u, fy - 3.1 * u); c.stroke();
    c.beginPath(); c.moveTo(x + L[0] * u - 0.4 * u, fy); c.lineTo(x + L[0] * u + 0.45 * u, fy); c.stroke();
  });
  /* tail and wing are black, the body pale */
  paper(c, poly([[x - 1.4 * u, fy - 4.3 * u], [x - 2.6 * u, fy - 3.5 * u], [x - 2.3 * u, fy - 3.2 * u], [x - 1.2 * u, fy - 3.5 * u]]), black, 1);
  paper(c, ell(x, fy - 4 * u, 1.9 * u, 1.05 * u, -0.12), grey, 1.4);
  paper(c, ell(x - 0.45 * u, fy - 3.85 * u, 1.75 * u, 0.7 * u, -0.05), black, 1);
  /* neck and head: ahead, or swung round to the back */
  var hx = lerp(x + 1.75 * u, x - 0.6 * u, head), hy = lerp(fy - 7.1 * u, fy - 4.9 * u, head), dir = head > 0.5 ? -1 : 1;
  paper(c, band(x + 1.2 * u, fy - 4.5 * u, lerp(x + 2.1 * u, x + 1.6 * u, head), lerp(fy - 5.6 * u, fy - 6.2 * u, head), hx, hy + 0.3 * u, 0.85 * u, 0.55 * u), grey, 1.2);
  paper(c, ell(hx, hy, 0.55 * u, 0.48 * u), grey, 1.2);
  /* the bill: straight upper, lower bowed away from it — the gap the bird is named for */
  var bx = hx + dir * 0.35 * u, by = hy + 0.05 * u, tx = hx + dir * 2.7 * u, ty = hy + (head > 0.5 ? 1.6 : 1.25) * u, g = (0.32 + 0.14 * clap) * u;
  var mx = (bx + tx) / 2, my = (by + ty) / 2, nx = -(ty - by), ny = tx - bx, nn = Math.hypot(nx, ny); nx /= nn; ny /= nn; if (dir < 0) { nx = -nx; ny = -ny; }
  paper(c, poly([[bx, by - 0.2 * u], [tx, ty], [bx + (tx - bx) * 0.5 - nx * 0.04 * u, by + (ty - by) * 0.5 - ny * 0.04 * u], [bx, by + 0.1 * u]]), horn, 1);
  var lo = [], k;
  for (k = 0; k <= 10; k++) { var s = k / 10, bow = Math.sin(Math.PI * Math.min(1, s * 1.15)) * g; lo.push([lerp(bx, tx, s) + nx * (bow + 0.12 * u * (1 - s)), lerp(by + 0.18 * u, ty, s) + ny * (bow + 0.12 * u * (1 - s))]); }
  for (k = 10; k >= 0; k--) { var s2 = k / 10, bow2 = Math.sin(Math.PI * Math.min(1, s2 * 1.15)) * g; lo.push([lerp(bx, tx, s2) + nx * (bow2 + 0.26 * u * (1 - s2) + 0.07 * u), lerp(by + 0.18 * u, ty, s2) + ny * (bow2 + 0.26 * u * (1 - s2) + 0.07 * u)]); }
  paper(c, poly(lo), horn, 1);
  c.fillStyle = '#111'; c.beginPath(); c.arc(hx + dir * 0.18 * u, hy - 0.08 * u, 0.09 * u, 0, TAU); c.fill();
}

/* a dead palm trunk, its top broken off, wrapped in a heart-leaved vine that sways */
function leaf(c, x, y, s, a, col) {
  c.save(); c.translate(x, y); c.rotate(a);
  paper(c, function (q) { q.beginPath(); q.moveTo(0, s * 0.9); q.bezierCurveTo(-s, s * 0.2, -s * 0.7, -s * 0.8, 0, -s * 0.35); q.bezierCurveTo(s * 0.7, -s * 0.8, s, s * 0.2, 0, s * 0.9); }, col, 0.6);
  c.restore();
}
function trunk(c, x, top, deck, w, t, seed, night) {
  var r = K.rnd(seed), bark = night ? '#3c352f' : '#7a6d60';
  var pts = [[x - w / 2, deck], [x - w / 2 + 3, top + 10], [x - w * 0.2, top - 6], [x, top + 4], [x + w * 0.25, top - 12], [x + w / 2 - 2, top + 6], [x + w / 2, deck]];
  paper(c, poly(pts), bark, 2);
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 2;
  for (var y = top + 30; y < deck; y += 26 + r() * 10) { c.beginPath(); c.moveTo(x - w / 2 + 2, y); c.lineTo(x + w / 2 - 2, y + 4); c.stroke(); }
  var greens = night ? ['#1f3a1c', '#2b4a24'] : ['#3d7a32', '#5a9a3e', '#2f6428'];
  for (var i = 0; i < 70; i++) {
    var yy = lerp(top + 4, deck - (deck - top) * 0.15, Math.pow(r(), 0.7)), side = r() - 0.5, sw = Math.sin(t / 900 + i) * 0.12;
    leaf(c, x + side * w * 1.5, yy, 9 + r() * 12, side * 1.8 + sw, greens[i % greens.length]);
  }
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, deck = S.deck, t = S.t, u = H * 0.032;
  var A = { x: S.x0 + S.span * 0.36, top: deck - H * 0.42 }, B = { x: S.x0 + S.span * 0.68, top: deck - H * 0.33 };
  trunk(c, A.x, A.top, deck, H * 0.09, t, S.seed + 1, S.night);
  trunk(c, B.x, B.top, deck, H * 0.08, t + 400, S.seed + 2, S.night);
  /* A looks round every few seconds and clatters; B preens, facing the other way */
  var turn = 0.5 + 0.5 * Math.sin(t / 1400), clap = Math.max(0, Math.sin(t / 90)) * (Math.sin(t / 1400) > 0.6 ? 1 : 0);
  openbill(c, A.x - u * 0.2, A.top + 2, u, 0, clap, S.night);
  c.save(); c.translate(B.x * 2, 0); c.scale(-1, 1);
  openbill(c, B.x + u * 0.1, B.top + 2, u * 0.92, 0.5 + 0.5 * Math.sin(t / 2100 + 1), 0, S.night);
  c.restore();
  void turn;
}
D.addScene('stork-openbill', draw, null, 'gap = g·sin(πs) (the open bill)');
window.STORK_KIT = { openbill: openbill, trunk: trunk, leaf: leaf, band: band, ell: ell };
})();

/* ---- stork-billgap ---- */
/* Worked example 2 of 3 — a DIAGRAM: one thing enormous on flat paper, with a measured callout.
   'stork-billgap'  an openbill's head in close-up, the bill working an apple snail at the tip;
                    a dimension line marks the gap and the shell turns as the bill works it.
   Render: node doodles/render.mjs stork-billgap --bg none --secs 6
   Different on purpose from example 1: no landscape, one subject filling the frame, warm ochre
   paper, a label drawn as part of the picture. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

/* an apple snail's shell: a logarithmic spiral r = a·e^(bθ), filled, its whorls lined */
function shell(c, x, y, R, rot) {
  c.save(); c.translate(x, y); c.rotate(rot);
  var b = 0.18, turns = 3.2, a = R / Math.exp(b * turns * TAU), pts = [];
  for (var th = 0; th <= turns * TAU; th += 0.12) { var r = a * Math.exp(b * th); pts.push([Math.cos(th) * r, Math.sin(th) * r]); }
  paper(c, function (q) { q.beginPath(); q.arc(0, 0, R * 1.02, 0, TAU); }, '#7a5530', 1.6);
  c.strokeStyle = '#3e2a16'; c.lineWidth = R * 0.05; c.lineCap = 'round';
  c.beginPath(); pts.forEach(function (p, i) { i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]); }); c.stroke();
  c.strokeStyle = 'rgba(255,230,180,.35)'; c.lineWidth = R * 0.03;
  for (var k = 0; k < 9; k++) { var t0 = k / 9 * TAU * turns, r0 = a * Math.exp(b * t0); c.beginPath(); c.arc(0, 0, r0 * 1.35, t0, t0 + 0.6); c.stroke(); }
  c.restore();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;
  /* paper: ochre with a darker ring, so the head sits on a stage */
  var g = c.createRadialGradient(W * 0.45, H * 0.5, H * 0.1, W * 0.45, H * 0.5, W * 0.7);
  g.addColorStop(0, '#e8c77e'); g.addColorStop(1, '#b8873e'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  var u = H / 10, hx = W * 0.2, hy = H * 0.42, work = 0.5 + 0.5 * Math.sin(t / 380), gap = u * (0.55 + 0.25 * work);
  /* neck coming in from the left edge, head, eye */
  paper(c, poly([[-20, H * 0.75], [hx - u * 1.2, hy + u * 0.4], [hx + u * 0.3, hy - u * 0.9], [hx + u * 0.6, hy + u * 0.9], [-20, H + 20]]), '#ebe8de', 2);
  paper(c, function (q) { q.beginPath(); q.ellipse(hx, hy, u * 1.25, u * 1.05, 0, 0, TAU); }, '#ebe8de', 2.2);
  c.fillStyle = '#121212'; c.beginPath(); c.arc(hx + u * 0.35, hy - u * 0.25, u * 0.16, 0, TAU); c.fill();
  c.fillStyle = '#fff'; c.beginPath(); c.arc(hx + u * 0.4, hy - u * 0.3, u * 0.05, 0, TAU); c.fill();
  /* the bill: upper straight, lower bowed — the gap opens and closes as it works */
  var bx = hx + u * 0.9, tx = W * 0.8, ty = hy + u * 2.2;
  paper(c, poly([[bx, hy - u * 0.45], [tx, ty], [bx + (tx - bx) * 0.55, hy + (ty - hy) * 0.55 - u * 0.05], [bx, hy + u * 0.15]]), '#5d5147', 2);
  var lo = [], hi = [], k;
  for (k = 0; k <= 20; k++) {
    var s = k / 20, bow = Math.sin(Math.PI * Math.min(1, s * 1.08)) * gap, x = lerp(bx, tx, s), y = lerp(hy + u * 0.35, ty, s);
    hi.push([x, y + bow]); lo.unshift([x, y + bow + u * 0.32 * (1 - s) + u * 0.08]);
  }
  paper(c, poly(hi.concat(lo)), '#4f443b', 2);
  /* the snail, held where the mandibles close, turning as the bill works it */
  shell(c, lerp(bx, tx, 0.86), lerp(hy + u * 0.3, ty, 0.86) + u * 0.12, u * 0.62, t / 900);
  /* the callout: a dimension line across the widest part of the gap */
  var mx = lerp(bx, tx, 0.47), my = lerp(hy + u * 0.35, ty, 0.47), my2 = my + Math.sin(Math.PI * 0.51) * gap;
  c.strokeStyle = '#2b1d10'; c.fillStyle = '#2b1d10'; c.lineWidth = 3;
  c.beginPath(); c.moveTo(mx, my - u * 0.1); c.lineTo(mx, my2 + u * 0.1); c.stroke();
  [[my - u * 0.1, 1], [my2 + u * 0.1, -1]].forEach(function (e) { c.beginPath(); c.moveTo(mx, e[0]); c.lineTo(mx - 9, e[0] + 14 * e[1]); c.lineTo(mx + 9, e[0] + 14 * e[1]); c.closePath(); c.fill(); });
  c.beginPath(); c.moveTo(mx, my2 + u * 0.2); c.lineTo(mx + u * 0.9, H * 0.86); c.stroke();
  c.font = '600 ' + Math.round(u * 0.55) + 'px "Avenir Next", "Helvetica Neue", sans-serif'; c.textBaseline = 'middle';
  c.fillText('the gap · ปากห่าง', mx + u, H * 0.88);
}
D.addScene('stork-billgap', draw, null, 'r = a·e^(bθ) (the shell)');
})();

/* ---- stork-theories ---- */
/* Worked example 3 of 3 — a DATA VISUALIZATION: time as a line you travel along.
   'stork-theories'  where storks go in winter, as people answered it: a paper ribbon across a
                     night-blue sheet, a stork flying along it, and at each stop a card with its
                     own small picture popping up as the bird reaches it.
   Render: node doodles/render.mjs stork-theories --bg none --secs 10
   Different again: dark paper, motion along an axis, text that arrives on cue.
   The stops are data — verify each against sources.md and change them there and here together. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

var STOPS = [
  { when: 'Aristotle', what: 'they hide, or turn into other birds', icon: 'swap' },
  { when: '1555', what: 'Olaus Magnus: under the ice, in the mud', icon: 'lake' },
  { when: 'Charles Morton', what: 'to the moon', icon: 'moon' },
  { when: '1822', what: 'the Pfeilstorch: to Africa', icon: 'spear' }
];

function icon(c, kind, x, y, s, t) {
  c.save(); c.translate(x, y);
  if (kind === 'swap') { c.rotate(Math.sin(t / 500) * 0.3); c.strokeStyle = '#5a4630'; c.lineWidth = s * 0.12; c.beginPath(); c.arc(0, 0, s * 0.6, 0.3, TAU - 0.9); c.stroke(); }
  if (kind === 'lake') { paper(c, function (q) { q.beginPath(); q.ellipse(0, s * 0.2, s, s * 0.4, 0, 0, TAU); }, '#4b7fa0', 1); c.strokeStyle = '#d9eef7'; c.lineWidth = 3; for (var i = -2; i <= 2; i++) { c.beginPath(); c.moveTo(i * s * 0.3, -s * 0.5); c.lineTo(i * s * 0.25, s * 0.3); c.stroke(); } }
  if (kind === 'moon') { paper(c, function (q) { q.beginPath(); q.arc(0, 0, s * 0.7, 0, TAU); q.arc(s * 0.3, -s * 0.15, s * 0.6, 0, TAU, true); }, '#f4e7a8', 1.4); }
  if (kind === 'spear') { c.rotate(-0.5); paper(c, poly([[-s, -3], [s * 0.6, -3], [s * 0.6, -9], [s * 1.1, 0], [s * 0.6, 9], [s * 0.6, 3], [-s, 3]]), '#8a5a2a', 1.2); }
  c.restore();
}
function flyer(c, x, y, s, t) {
  var f = Math.sin(t / 120);
  paper(c, function (q) { q.beginPath(); q.ellipse(x, y, s, s * 0.32, 0, 0, TAU); }, '#efece2', 1.2);
  paper(c, poly([[x - s * 0.3, y], [x + s * 0.1, y], [x - s * 0.1, y - s * (0.9 * f)], [x - s * 0.6, y - s * (0.8 * f)]]), '#1d1b19', 1);
  paper(c, poly([[x + s * 0.9, y - s * 0.08], [x + s * 1.8, y], [x + s * 0.9, y + s * 0.08]]), '#efece2', 1);
  paper(c, poly([[x + s * 1.8, y - s * 0.04], [x + s * 2.4, y + s * 0.05], [x + s * 1.8, y + s * 0.06]]), '#c9472f', 1);
  c.strokeStyle = '#c9472f'; c.lineWidth = s * 0.06; c.beginPath(); c.moveTo(x - s, y); c.lineTo(x - s * 1.9, y + s * 0.1); c.stroke();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t, T = 10000, p = Math.min(1, (t % (T + 1500)) / T);
  var g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#152238'); g.addColorStop(1, '#22365a'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  var r = K.rnd(11); c.fillStyle = 'rgba(255,246,214,.6)'; for (var i = 0; i < 90; i++) c.fillRect(r() * W, r() * H * 0.5, 2, 2);
  /* the ribbon: a gentle wave from left to right */
  var x0 = W * 0.08, x1 = W * 0.92, yAt = function (x) { return H * 0.62 + Math.sin(x / W * TAU * 1.2) * H * 0.04; };
  var top = [], bot = [];
  for (var x = x0; x <= x1; x += 12) { top.push([x, yAt(x) - 9]); bot.unshift([x, yAt(x) + 9]); }
  paper(c, poly(top.concat(bot)), '#c9a35a', 1.4);
  /* stops, and their cards rising as the bird passes */
  c.textAlign = 'center'; c.textBaseline = 'middle';
  STOPS.forEach(function (st, k) {
    var sx = lerp(x0 + W * 0.06, x1 - W * 0.06, k / (STOPS.length - 1)), sy = yAt(sx), on = ease((p - (k + 0.3) / STOPS.length) * 6);
    paper(c, function (q) { q.beginPath(); q.arc(sx, sy, 16, 0, TAU); }, on > 0 ? '#f2e6c9' : '#7a6a48', 1.2);
    if (on <= 0) return;
    var cy = sy - H * 0.22 * on, cw = W * 0.19, ch = H * 0.24;
    c.globalAlpha = Math.min(1, on * 1.4);
    paper(c, poly([[sx - cw / 2, cy - ch / 2], [sx + cw / 2, cy - ch / 2], [sx + cw / 2, cy + ch / 2], [sx - cw / 2, cy + ch / 2]]), '#f2e6c9', 2);
    c.strokeStyle = 'rgba(42,30,16,.4)'; c.lineWidth = 2; c.beginPath(); c.moveTo(sx, cy + ch / 2); c.lineTo(sx, sy - 16); c.stroke();
    icon(c, st.icon, sx, cy - ch * 0.18, H * 0.05, t);  /* 'swap' strokes in paper colour: on a light card use a dark one */
    c.fillStyle = '#2a1e10'; c.font = '700 ' + Math.round(H * 0.03) + 'px "Avenir Next", sans-serif'; c.fillText(st.when, sx, cy + ch * 0.14);
    var fs = Math.round(H * 0.021); c.font = '500 ' + fs + 'px "Avenir Next", sans-serif';
    while (c.measureText(st.what).width > cw * 0.9 && fs > 10) c.font = '500 ' + (--fs) + 'px "Avenir Next", sans-serif';   /* shrink to fit the card */
    c.fillText(st.what, sx, cy + ch * 0.32);
    c.globalAlpha = 1;
  });
  var bx = lerp(x0, x1, p);
  flyer(c, bx, yAt(bx) - H * 0.06, H * 0.035, t);
}
D.addScene('stork-theories', draw, null, 'x = x₀ + (x₁ − x₀)·t/T (the bird along the years)');
})();

/* ---- stork-woodcut ---- */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

/* Woodcut style hatched area */
function hatched(c, pathFn, angle, spacing, thickness, col) {
  c.save();
  c.beginPath(); pathFn(c); c.clip();
  c.strokeStyle = col || '#1a1815';
  c.lineWidth = thickness;
  c.lineCap = 'round';
  c.lineJoin = 'round';
  
  var R = 3000;
  c.rotate(angle);
  c.beginPath();
  for (var y = -R; y < R; y += spacing) {
    c.moveTo(-R, y);
    c.lineTo(R, y);
  }
  c.stroke();
  c.restore();
}

function outlineAndHatch(c, pathFn, angle1, angle2, spacing, thickness, outlineThickness, ink) {
  if (angle1 !== null) hatched(c, pathFn, angle1, spacing, thickness, ink);
  if (angle2 !== null) hatched(c, pathFn, angle2, spacing, thickness, ink);
  c.strokeStyle = ink;
  c.lineWidth = outlineThickness; 
  c.beginPath(); pathFn(c); c.stroke();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t, u = H / 10;
  var ink = '#1a1815';
  
  // Cream paper background
  c.fillStyle = '#f4ebd5';
  c.fillRect(0, 0, W, H);
  
  // Outer printed border (decorated)
  c.strokeStyle = ink;
  c.lineWidth = u * 0.15;
  c.strokeRect(u * 0.5, u * 0.5, W - u, H - u);
  c.lineWidth = u * 0.04;
  c.strokeRect(u * 0.6, u * 0.6, W - u * 1.2, H - u * 1.2);
  c.strokeRect(u * 0.4, u * 0.4, W - u * 0.8, H - u * 0.8);
  
  // Caption plate at the bottom border
  c.fillStyle = '#f4ebd5';
  c.fillRect(W / 2 - u * 2, H - u * 0.9, u * 4, u * 0.8);
  c.strokeRect(W / 2 - u * 2, H - u * 0.9, u * 4, u * 0.8);
  c.fillStyle = ink;
  c.font = 'bold ' + (u * 0.4) + 'px serif';
  c.textAlign = 'center';
  c.textBaseline = 'middle';
  c.fillText('HISTORIA · 1555', W / 2, H - u * 0.5);
  
  // Clip the rest of the scene to the inner border
  c.save();
  c.beginPath();
  c.rect(u * 0.7, u * 0.7, W - u * 1.4, H - u * 1.5); 
  c.clip();
  
  var horizonY = H * 0.35;
  
  // Sky: horizontal lines
  c.lineWidth = u * 0.03;
  c.strokeStyle = ink;
  for (var i = 0; i < 40; i++) {
    var skyY = lerp(u * 0.7, horizonY - u * 0.5, Math.pow(i / 40, 1.5));
    c.beginPath(); c.moveTo(0, skyY); c.lineTo(W, skyY); c.stroke();
  }
  
  // Snowy bank
  var bankPath = function(q) {
    q.moveTo(0, horizonY);
    q.quadraticCurveTo(W * 0.2, horizonY - u, W * 0.5, horizonY - u * 0.2);
    q.quadraticCurveTo(W * 0.8, horizonY - u * 0.8, W, horizonY);
    q.lineTo(W, horizonY + u * 2);
    q.lineTo(0, horizonY + u * 2);
    q.closePath();
  };
  outlineAndHatch(c, bankPath, -TAU/24, null, u*0.2, u*0.03, u*0.06, ink);
  
  // Bare trees
  function drawTree(tx, ty, scale) {
    var s = u * scale;
    c.lineWidth = s * 0.05;
    c.lineCap = 'round';
    c.strokeStyle = ink;
    c.beginPath();
    // Trunk
    c.moveTo(tx, ty); c.lineTo(tx, ty - s * 1.5);
    // Branches
    c.moveTo(tx, ty - s * 0.5); c.lineTo(tx - s * 0.4, ty - s * 1.2);
    c.moveTo(tx - s * 0.2, ty - s * 0.85); c.lineTo(tx - s * 0.5, ty - s * 1.4);
    c.moveTo(tx, ty - s * 0.8); c.lineTo(tx + s * 0.5, ty - s * 1.6);
    c.moveTo(tx + s * 0.2, ty - s * 1.1); c.lineTo(tx + s * 0.4, ty - s * 1.5);
    c.moveTo(tx, ty - s * 1.2); c.lineTo(tx - s * 0.3, ty - s * 1.8);
    c.stroke();
  }
  drawTree(W * 0.1, horizonY, 1.5);
  drawTree(W * 0.25, horizonY - u * 0.5, 1);
  drawTree(W * 0.75, horizonY - u * 0.3, 1.2);
  drawTree(W * 0.9, horizonY + u * 0.2, 1.8);
  
  // Ice surface
  for (var j = 0; j < 60; j++) {
    var iy = lerp(horizonY + u * 0.5, H, Math.pow(S.r(), 1.5));
    var ix = S.r() * W;
    var ilen = S.r() * u * 2;
    c.lineWidth = u * 0.03;
    c.beginPath(); c.moveTo(ix, iy); c.lineTo(ix + ilen, iy); c.stroke();
  }
  
  // Square hole cut in the ice
  var hx = W * 0.5, hy = H * 0.75, hr = u * 2;
  var holePath = function(q) { 
    q.moveTo(hx - hr, hy - hr*0.4); 
    q.lineTo(hx + hr, hy - hr*0.4);
    q.lineTo(hx + hr*1.3, hy + hr*0.5);
    q.lineTo(hx - hr*1.3, hy + hr*0.5);
    q.closePath();
  };
  // Cross hatch water
  outlineAndHatch(c, holePath, 0, TAU / 4, u * 0.08, u * 0.04, u * 0.1, ink);
  
  // The haul motion
  var pullPhase = (t % 3000) / 3000; 
  var pull = 0.5 - 0.5 * Math.cos(pullPhase * TAU); 
  
  var f1x = hx - hr * 1.2, f1y = hy;
  var f2x = hx + hr * 1.2, f2y = hy;
  
  // Fisherman function
  function fisherman(fx, fy, dir, p) {
    c.save();
    c.translate(fx, fy);
    c.rotate(dir * (0.1 + p * 0.15)); 
    
    var outThick = u * 0.08;
    
    // Back leg
    var bleg = function(q) {
      q.moveTo(-u*0.1, -u*0.8); q.lineTo(-dir*u*0.4 - p*dir*u*0.2, 0); 
      q.lineTo(-dir*u*0.2 - p*dir*u*0.2, 0); q.lineTo(u*0.1, -u*0.8); q.closePath();
    };
    outlineAndHatch(c, bleg, -dir * TAU / 8, null, u * 0.08, u * 0.03, outThick, ink);
    
    // Front leg
    var fleg = function(q) {
      q.moveTo(u*0.1, -u*0.8); q.lineTo(dir*u*0.5 + p*dir*u*0.2, u*0.2);
      q.lineTo(dir*u*0.7 + p*dir*u*0.2, u*0.2); q.lineTo(u*0.3, -u*0.8); q.closePath();
    };
    outlineAndHatch(c, fleg, -dir * TAU / 8, null, u * 0.08, u * 0.03, outThick, ink);
    
    // Body (heavy coat, more hunched, denser hatching)
    var bodyPath = function(q) { 
      q.moveTo(-dir*u*0.2, -u*0.6); 
      q.quadraticCurveTo(-dir*u*0.8, -u*1.0, -dir*u*0.4, -u*2.0); // hunched back
      q.lineTo(dir*u*0.4, -u*1.8); // shoulder
      q.quadraticCurveTo(dir*u*0.6, -u*1.0, dir*u*0.3, -u*0.6); // front
      q.closePath(); 
    };
    outlineAndHatch(c, bodyPath, dir * TAU / 6, dir * -TAU / 6, u * 0.07, u * 0.03, outThick, ink);
    
    // Head & hat
    var headPath = function(q) { q.arc(0, -u * 2.2, u * 0.35, 0, TAU); };
    outlineAndHatch(c, headPath, -dir * TAU / 4, dir * TAU / 4, u * 0.08, u * 0.03, outThick, ink);
    
    // Brim of hat
    var brim = function(q) { q.ellipse(dir*u*0.1, -u*2.2, u*0.7, u*0.15, dir*0.15, 0, TAU); };
    outlineAndHatch(c, brim, null, null, u*0.1, u*0.04, outThick, ink);
    
    // Arms pulling
    var handX = dir * (u*1.0 + p*u*0.5), handY = -u*1.0 + p*u*0.2;
    var armPath = function(q) {
      q.moveTo(dir*u*0.2, -u*1.6); q.lineTo(handX, handY - u*0.1); 
      q.lineTo(handX, handY + u*0.1); q.lineTo(dir*u*0.2, -u*1.2); q.closePath();
    };
    outlineAndHatch(c, armPath, dir * TAU / 8, null, u * 0.06, u * 0.03, outThick, ink);
    
    c.restore();
    
    var cosR = Math.cos(dir * (0.1 + p * 0.15)), sinR = Math.sin(dir * (0.1 + p * 0.15));
    return {
      x: fx + handX * cosR - handY * sinR,
      y: fy + handX * sinR + handY * cosR
    };
  }
  
  var hand1 = fisherman(f1x, f1y, 1, pull);
  var hand2 = fisherman(f2x, f2y, -1, pull);
  
  // Net
  var netY = hy - u * 2.5 - pull * u * 0.5;
  var nPath = function(q) { 
    q.moveTo(hx - u*1.2, hy); 
    q.bezierCurveTo(hx - u*1.6, hy - u*0.5, hx - u*0.8, netY, hx, netY);
    q.bezierCurveTo(hx + u*0.8, netY, hx + u*1.6, hy - u*0.5, hx + u*1.2, hy);
    q.closePath();
  };
  // Thick net with cross hatching
  outlineAndHatch(c, nPath, TAU / 8, -TAU / 8, u * 0.12, u * 0.04, u * 0.1, ink);
  
  // Rope from hands to the net top
  c.lineWidth = u * 0.08;
  c.beginPath();
  c.moveTo(hand1.x, hand1.y);
  c.lineTo(hx, netY);
  c.lineTo(hand2.x, hand2.y);
  c.stroke();
  
  function drawSwallow(bx, by, rot, flap, packed) {
    c.save();
    c.translate(bx, by);
    c.rotate(rot);
    
    var birdPath = function(q) {
      // Body
      q.ellipse(0, 0, u*0.35, u*0.15, 0, 0, TAU); 
      // Head
      q.ellipse(-u*0.35, 0, u*0.15, u*0.12, 0, 0, TAU);
      // Beak
      q.moveTo(-u*0.4, -u*0.05); q.lineTo(-u*0.7, 0); q.lineTo(-u*0.4, u*0.05); q.closePath();
      // Forked tail
      q.moveTo(u*0.2, 0); q.lineTo(u*0.8, -u*0.25); q.lineTo(u*0.4, 0); q.lineTo(u*0.8, u*0.25); q.closePath();
      // Flapping wings (swept wings, curved back)
      if (packed) {
        // Folded wings
        q.moveTo(0, -u*0.1); q.quadraticCurveTo(u*0.3, -u*0.3, u*0.6, -u*0.1); q.lineTo(0, 0); q.closePath();
        q.moveTo(0, u*0.1); q.quadraticCurveTo(u*0.3, u*0.3, u*0.6, u*0.1); q.lineTo(0, 0); q.closePath();
      } else {
        q.moveTo(-u*0.1, -u*0.05); 
        q.quadraticCurveTo(-u*0.3, -u*0.4 + flap*u*0.6, -u*0.9, -u*0.7 + flap*u*1.2); 
        q.quadraticCurveTo(-u*0.5, -u*0.4 + flap*u*0.6, -u*0.2, -u*0.1); 
        q.closePath();
        
        q.moveTo(-u*0.1, u*0.05); 
        q.quadraticCurveTo(-u*0.3, u*0.4 - flap*u*0.6, -u*0.9, u*0.7 - flap*u*1.2); 
        q.quadraticCurveTo(-u*0.5, u*0.4 - flap*u*0.6, -u*0.2, u*0.1); 
        q.closePath();
      }
    };
    
    // Fill with cream so they obscure the net and each other
    c.fillStyle = '#f4ebd5';
    c.beginPath(); birdPath(c); c.fill();
    
    // Outline and hatch (thinner outline for birds)
    outlineAndHatch(c, birdPath, TAU/8, null, u*0.08, u*0.02, u*0.04, ink);
    
    c.restore();
  }
  
  // Swallows packed in the net
  var savedT = S.t;
  S.t = 0; 
  for (var p = 0; p < 8; p++) {
    var rx = S.r();
    var ry = S.r();
    var pX = hx + (rx - 0.5) * u * 1.8;
    var pY = netY + u * 1.5 + ry * u * 1.5;
    drawSwallow(pX, pY, rx * TAU, 0, true);
  }
  S.t = savedT;
  
  // Swallows tumbling out
  for (var k = 0; k < 12; k++) {
    var bcycle = (t + k * 1000) % 12000;
    var phase = bcycle / 12000;
    if (phase > 0.6) continue;
    
    var up = phase * 1.66;
    var side = (k % 2 === 0 ? -1 : 1);
    var bx = hx + side * (u * 0.4 + up * u * 4);
    var by = netY + u * 2 - Math.sin(up * TAU / 2) * u * 3 + up * u * 5;
    
    var landed = false;
    if (by > hy + u * 1.0) {
      by = hy + u * 1.0 + (k % 3) * u * 0.3; 
      up = 1; 
      landed = true;
    }
    
    var flap = landed ? 0 : Math.sin(t / 100 + k * 2) * 0.6;
    var rot = side * up * TAU + k;
    if (landed) rot = side * 0.2; 
    
    drawSwallow(bx, by, rot, flap, landed);
  }
  
  c.restore();
}
D.addScene('stork-woodcut', draw, null, 'pull = 0.5 - 0.5·cos(t/3000·2π) (hauling the net)');
})();

/* ---- stork-moon ---- */
/* DOODLES.md: id 'moon'
   Form: night sky
   Ground · palette: --bg none; deep violet to black, a huge pale moon with craters
   Motion: one stork flapping steadily up and away, getting smaller; stars wheel slowly
   Subject: Charles Morton's moon migration (1703)
   Species: White Stork (Ciconia ciconia) — white body, black flight feathers, red bill and legs
*/
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

/* helper: circle path function */
function circ(x, y, r) {
  return function (q) { q.beginPath(); q.arc(x, y, r, 0, TAU); };
}

/* helper: ellipse path function */
function ell(x, y, rx, ry, rot) {
  return function (q) { q.beginPath(); q.ellipse(x, y, rx, ry, rot || 0, 0, TAU); };
}

/* 4-pointed paper star */
function star4(c, x, y, r, fill, lift) {
  var d = r * 0.22;
  var pts = [
    [x, y - r],
    [x + d, y - d],
    [x + r, y],
    [x + d, y + d],
    [x, y + r],
    [x - d, y + d],
    [x - r, y],
    [x - d, y - d]
  ];
  paper(c, poly(pts), fill, lift || 0.4);
}

/* Smooth organic cut-paper patch for lunar maria */
function maria(c, pts, col) {
  paper(c, function (q) {
    q.beginPath();
    var n = pts.length;
    q.moveTo((pts[n - 1][0] + pts[0][0]) / 2, (pts[n - 1][1] + pts[0][1]) / 2);
    for (var i = 0; i < n; i++) {
      var next = pts[(i + 1) % n];
      var midX = (pts[i][0] + next[0]) / 2;
      var midY = (pts[i][1] + next[1]) / 2;
      q.quadraticCurveTo(pts[i][0], pts[i][1], midX, midY);
    }
    q.closePath();
  }, col, 0.35);
}

/* Full moon crater: bright rayed impact spot with soft paper depth */
function lunarCrater(c, x, y, r, rays) {
  c.save();
  if (rays) {
    c.strokeStyle = 'rgba(255, 253, 245, 0.22)';
    c.lineWidth = 1.0;
    for (var i = 0; i < rays.length; i++) {
      var a = rays[i][0], len = rays[i][1];
      c.beginPath();
      c.moveTo(x, y);
      c.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
      c.stroke();
    }
  }

  /* Ejecta blanket */
  var ejecta = c.createRadialGradient(x, y, r * 0.1, x, y, r * 2.2);
  ejecta.addColorStop(0, 'rgba(255, 254, 248, 0.45)');
  ejecta.addColorStop(0.5, 'rgba(255, 252, 240, 0.15)');
  ejecta.addColorStop(1, 'rgba(255, 250, 235, 0)');
  c.fillStyle = ejecta;
  c.beginPath();
  c.arc(x, y, r * 2.2, 0, TAU);
  c.fill();

  /* Crater floor */
  c.fillStyle = 'rgba(185, 172, 148, 0.35)';
  c.beginPath();
  c.arc(x, y, r, 0, TAU);
  c.fill();

  /* Delicate sunlit rim */
  c.strokeStyle = 'rgba(255, 255, 250, 0.75)';
  c.lineWidth = Math.max(1, r * 0.2);
  c.beginPath();
  c.arc(x, y, r * 0.85, 0, TAU);
  c.stroke();
  c.restore();
}

/* Draw the Moon with lunar geography and craters */
function drawMoon(c, mx, my, R) {
  /* 1. Luminous celestial aura */
  var halo = c.createRadialGradient(mx, my, R * 0.85, mx, my, R * 1.8);
  halo.addColorStop(0, 'rgba(240, 234, 255, 0.24)');
  halo.addColorStop(0.35, 'rgba(185, 165, 230, 0.09)');
  halo.addColorStop(0.7, 'rgba(100, 80, 160, 0.025)');
  halo.addColorStop(1, 'rgba(10, 5, 20, 0)');
  c.fillStyle = halo;
  c.beginPath();
  c.arc(mx, my, R * 1.8, 0, TAU);
  c.fill();

  /* 2. Base pale paper disc */
  paper(c, circ(mx, my, R), '#f6f1df', 3.0);

  c.save();
  c.beginPath();
  c.arc(mx, my, R - 0.5, 0, TAU);
  c.clip();

  /* 3. Lunar Maria: large continuous dark plains */
  var mColLight = '#ded4be';
  var mColMid = '#cdbe9f';
  var mColDeep = '#b8a682';

  /* The Western Sea complex: Oceanus Procellarum & Mare Imbrium */
  maria(c, [
    [mx - R * 0.76, my - R * 0.12],
    [mx - R * 0.65, my - R * 0.48],
    [mx - R * 0.38, my - R * 0.62],
    [mx - R * 0.12, my - R * 0.45],
    [mx - R * 0.18, my - R * 0.18],
    [mx - R * 0.35, my + R * 0.08],
    [mx - R * 0.58, my + R * 0.16],
    [mx - R * 0.76, my + R * 0.02]
  ], mColLight);

  /* Mare Imbrium basin center */
  maria(c, [
    [mx - R * 0.52, my - R * 0.45],
    [mx - R * 0.25, my - R * 0.52],
    [mx - R * 0.15, my - R * 0.35],
    [mx - R * 0.30, my - R * 0.24],
    [mx - R * 0.50, my - R * 0.30]
  ], mColMid);

  /* Mare Serenitatis (center-north) */
  maria(c, [
    [mx - R * 0.05, my - R * 0.42],
    [mx + R * 0.22, my - R * 0.45],
    [mx + R * 0.32, my - R * 0.25],
    [mx + R * 0.14, my - R * 0.15],
    [mx - R * 0.08, my - R * 0.28]
  ], mColMid);

  /* Mare Tranquillitatis (center-east) */
  maria(c, [
    [mx + R * 0.12, my - R * 0.20],
    [mx + R * 0.42, my - R * 0.12],
    [mx + R * 0.48, my + R * 0.08],
    [mx + R * 0.25, my + R * 0.15],
    [mx + R * 0.06, my - R * 0.02]
  ], mColDeep);

  /* Mare Crisium (isolated oval in the east) */
  maria(c, [
    [mx + R * 0.55, my - R * 0.22],
    [mx + R * 0.72, my - R * 0.18],
    [mx + R * 0.74, my - R * 0.06],
    [mx + R * 0.56, my - R * 0.08]
  ], mColDeep);

  /* Mare Fecunditatis & Nectaris (south-east) */
  maria(c, [
    [mx + R * 0.20, my + R * 0.12],
    [mx + R * 0.46, my + R * 0.18],
    [mx + R * 0.40, my + R * 0.42],
    [mx + R * 0.16, my + R * 0.36],
    [mx + R * 0.10, my + R * 0.22]
  ], mColLight);

  /* Mare Nubium & Humorum (south-west) */
  maria(c, [
    [mx - R * 0.42, my + R * 0.16],
    [mx - R * 0.12, my + R * 0.18],
    [mx - R * 0.18, my + R * 0.46],
    [mx - R * 0.38, my + R * 0.44],
    [mx - R * 0.52, my + R * 0.28]
  ], mColMid);

  /* 4. Craters: bright full-moon ray centers and features */
  var tyX = mx + R * 0.06, tyY = my + R * 0.65;
  var tyRays = [];
  var tyAngles = [-2.5, -2.1, -1.8, -1.5, -1.2, -0.9, -0.6, -0.3, 0.1, 0.5, 0.8, 1.2];
  for (var rIdx = 0; rIdx < tyAngles.length; rIdx++) {
    tyRays.push([tyAngles[rIdx], R * (0.55 + ((rIdx * 7) % 5) * 0.18)]);
  }
  lunarCrater(c, tyX, tyY, R * 0.048, tyRays);

  /* Copernicus with bright halo rays */
  var copRays = [
    [-2.8, R * 0.3], [-2.0, R * 0.35], [-1.2, R * 0.32],
    [-0.4, R * 0.38], [0.5, R * 0.28], [1.5, R * 0.3]
  ];
  lunarCrater(c, mx - R * 0.32, my - R * 0.14, R * 0.042, copRays);

  /* Kepler */
  lunarCrater(c, mx - R * 0.52, my - R * 0.08, R * 0.026, [
    [-2.2, R * 0.2], [-1.0, R * 0.22], [0.2, R * 0.2], [1.4, R * 0.18]
  ]);

  /* Plato (distinct dark volcanic floor in north) */
  paper(c, circ(mx - R * 0.16, my - R * 0.56, R * 0.038), '#9c8e73', 0.2);
  c.strokeStyle = 'rgba(255, 255, 245, 0.7)';
  c.lineWidth = 1.2;
  c.beginPath();
  c.arc(mx - R * 0.16, my - R * 0.56, R * 0.038, 0, TAU);
  c.stroke();

  /* 5. Spherical limb shading */
  var limb = c.createRadialGradient(mx - R * 0.25, my - R * 0.2, R * 0.55, mx, my, R);
  limb.addColorStop(0, 'rgba(255, 255, 255, 0.05)');
  limb.addColorStop(0.75, 'rgba(0, 0, 0, 0)');
  limb.addColorStop(1, 'rgba(25, 15, 45, 0.38)');
  c.fillStyle = limb;
  c.beginPath();
  c.arc(mx, my, R, 0, TAU);
  c.fill();

  c.restore();
}

/* Wing generator for White Stork:
   Leading edge is pure white coverts.
   Trailing edge and wingtip are jet-black flight feathers with 5 separated primary fingers.
   isFar: if true, drawn slightly smaller and offset in perspective.
*/
function storkWing(c, u, flap, isFar) {
  c.save();
  var white = '#fefcf8';
  var black = '#141312';

  /* Wing flaps up and down around shoulder:
     When flap = -1 (upstroke peak): wing rises high above back.
     When flap = +1 (downstroke peak): wing sweeps down to body level.
  */
  var rot = (isFar ? -0.38 : -0.10) - flap * 0.65;
  c.rotate(rot);
  if (isFar) c.scale(0.86, 0.86);

  /* 1. BLACK FLIGHT FEATHERS (trailing edge and separated primary tips) */
  var blackPts = [
    /* covert seam line (starting from inner wing) */
    [-u * 0.25, -u * 0.10],
    [-u * 0.10, -u * 0.85],
    [u * 0.25, -u * 1.55],
    /* Wingtip: 5 separated primary feather fingers fanning outward */
    [u * 0.45, -u * 2.25], /* finger 1 (outermost) */
    [u * 0.20, -u * 2.45], /* finger 2 */
    [-u * 0.15, -u * 2.40], /* finger 3 */
    [-u * 0.45, -u * 2.20], /* finger 4 */
    [-u * 0.70, -u * 1.85], /* finger 5 (innermost primary) */
    /* Trailing edge of secondaries running down to inner body */
    [-u * 0.75, -u * 1.15],
    [-u * 0.65, -u * 0.45],
    [-u * 0.45, -u * 0.05]
  ];
  paper(c, poly(blackPts), black, isFar ? 0.8 : 1.7);

  /* 2. WHITE LEADING EDGE COVERTS (smooth, rounded forward leading edge) */
  var whitePts = [
    [0, 0],
    [u * 0.25, -u * 0.35], /* elbow */
    [u * 0.50, -u * 0.95], /* carpal / wrist */
    [u * 0.55, -u * 1.60], /* outer coverts */
    [u * 0.25, -u * 1.55], /* meeting the flight feathers */
    [-u * 0.10, -u * 0.85],
    [-u * 0.25, -u * 0.10]
  ];
  paper(c, poly(whitePts), white, isFar ? 1.0 : 1.9);

  c.restore();
}

/* White Stork (Ciconia ciconia) in flight */
function drawStork(c, x, y, scale, angle, wingPhase, alpha) {
  c.save();
  c.translate(x, y);
  c.rotate(angle);
  c.scale(scale, scale);
  if (alpha != null && alpha < 1) c.globalAlpha = Math.max(0, Math.min(1, alpha));

  var white = '#fefcf8';
  var red = '#cf3924';
  var u = 68;

  var flap = Math.sin(wingPhase);

  /* FAR WING (behind body) */
  c.save();
  c.translate(-u * 0.05, -u * 0.14);
  storkWing(c, u, flap, true);
  c.restore();

  /* LEGS: long coral-red legs trailing straight behind tail */
  c.strokeStyle = red;
  c.lineWidth = u * 0.042;
  c.lineCap = 'round';
  c.lineJoin = 'round';

  /* Far leg */
  c.beginPath();
  c.moveTo(-u * 0.45, u * 0.05);
  c.lineTo(-u * 1.55, u * 0.12);
  c.lineTo(-u * 2.35, u * 0.16);
  c.lineTo(-u * 2.65, u * 0.19);
  c.stroke();

  /* Near leg */
  c.beginPath();
  c.moveTo(-u * 0.35, u * 0.10);
  c.lineTo(-u * 1.50, u * 0.20);
  c.lineTo(-u * 2.30, u * 0.24);
  c.lineTo(-u * 2.60, u * 0.28);
  c.stroke();

  /* TAIL: short clean white fan */
  var tailPts = [
    [-u * 0.45, -u * 0.05],
    [-u * 1.05, -u * 0.08],
    [-u * 1.10, u * 0.09],
    [-u * 0.45, u * 0.11]
  ];
  paper(c, poly(tailPts), white, 1.2);

  /* BODY: sleek white torso */
  paper(c, ell(-u * 0.05, u * 0.02, u * 0.65, u * 0.24, -0.04), white, 1.4);

  /* NECK: outstretched long white neck */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(u * 0.30, -u * 0.08);
    q.quadraticCurveTo(u * 0.90, -u * 0.15, u * 1.55, -u * 0.13);
    q.lineTo(u * 1.55, 0);
    q.quadraticCurveTo(u * 0.90, 0, u * 0.30, u * 0.12);
    q.closePath();
  }, white, 1.4);

  /* HEAD: sleek white oval */
  var hx = u * 1.62, hy = -u * 0.08;
  paper(c, ell(hx, hy, u * 0.18, u * 0.12, 0.04), white, 1.5);

  /* EYE: dark eye with white catchlight */
  c.fillStyle = '#111';
  c.beginPath();
  c.arc(hx + u * 0.04, hy - u * 0.02, u * 0.034, 0, TAU);
  c.fill();
  c.fillStyle = '#fff';
  c.beginPath();
  c.arc(hx + u * 0.05, hy - u * 0.03, u * 0.012, 0, TAU);
  c.fill();

  /* BILL: long, sharp, straight coral-red spear */
  var billPts = [
    [hx + u * 0.11, hy - u * 0.05],
    [hx + u * 1.25, hy - u * 0.015],
    [hx + u * 0.11, hy + u * 0.04]
  ];
  paper(c, poly(billPts), red, 1.5);
  c.strokeStyle = '#9a2010';
  c.lineWidth = u * 0.018;
  c.beginPath();
  c.moveTo(hx + u * 0.15, hy - u * 0.005);
  c.lineTo(hx + u * 1.15, hy - u * 0.012);
  c.stroke();

  /* NEAR WING (in front of body) */
  c.save();
  c.translate(u * 0.06, -u * 0.04);
  storkWing(c, u, flap, false);
  c.restore();

  c.restore();
}

/* Star catalog: distributed evenly across the sky dome */
var STARS = null;
function getStars(seed, W, H) {
  if (STARS) return STARS;
  var r = K.rnd(seed || 1703);
  var list = [];
  var n = 220;
  for (var i = 0; i < n; i++) {
    var x = r() * W;
    var y = r() * H;
    var sz = 0.7 + r() * 1.5;
    var bright = 0.25 + r() * 0.75;
    var hero = (i % 16 === 0);
    list.push({ x: x, y: y, sz: sz, bright: bright, hero: hero, tw: r() * TAU });
  }
  STARS = list;
  return list;
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;

  /* 1. DEEP VIOLET TO BLACK NIGHT SKY GRADIENT */
  var mx = W * 0.73, my = H * 0.34, mR = Math.min(W, H) * 0.29;
  var sky = c.createLinearGradient(W * 0.5, 0, W * 0.2, H);
  sky.addColorStop(0, '#1c1033'); /* rich deep violet near top and moon */
  sky.addColorStop(0.45, '#0e081e'); /* midnight indigo */
  sky.addColorStop(0.85, '#05030a'); /* deep obsidian velvet */
  sky.addColorStop(1, '#020104');
  c.fillStyle = sky;
  c.fillRect(0, 0, W, H);

  /* 2. STARS WHEELING SLOWLY around Polaris (upper left) */
  var px = W * 0.18, py = H * 0.12;
  var stars = getStars(S.seed || 1703, W, H);
  var wheelAngle = (t / 12000) * (TAU * 0.05);
  var cosW = Math.cos(wheelAngle), sinW = Math.sin(wheelAngle);

  for (var i = 0; i < stars.length; i++) {
    var st = stars[i];
    var dx = st.x - px, dy = st.y - py;
    var sx = px + dx * cosW - dy * sinW;
    var sy = py + dx * sinW + dy * cosW;

    if (sx < -20 || sx > W + 20 || sy < -20 || sy > H + 20) continue;

    var tw = st.bright * (0.75 + 0.25 * Math.sin(t / 700 + st.tw));
    if (st.hero) {
      star4(c, sx, sy, st.sz * 3.0, 'rgba(255, 246, 218, ' + tw.toFixed(2) + ')', 0.4);
    } else {
      c.fillStyle = 'rgba(238, 232, 255, ' + tw.toFixed(2) + ')';
      c.beginPath();
      c.arc(sx, sy, st.sz, 0, TAU);
      c.fill();
    }
  }

  /* 3. EARTH ATMOSPHERE LIMB at bottom-left */
  var earthGrad = c.createRadialGradient(W * 0.05, H * 1.45, H * 0.55, W * 0.05, H * 1.45, H * 0.85);
  earthGrad.addColorStop(0, 'rgba(40, 70, 135, 0.35)');
  earthGrad.addColorStop(0.65, 'rgba(20, 30, 70, 0.14)');
  earthGrad.addColorStop(1, 'rgba(5, 3, 10, 0)');
  c.fillStyle = earthGrad;
  c.beginPath();
  c.arc(W * 0.05, H * 1.45, H * 0.85, 0, TAU);
  c.fill();

  /* 4. THE HUGE PALE MOON WITH CRATERS */
  drawMoon(c, mx, my, mR);

  /* 5. CELESTIAL FLIGHT PATH: sweeping arc from Earth toward the Moon */
  var T = 12000;
  var u = (t % T) / T; /* 0..1 loop progress */

  var p0x = W * 0.08, p0y = H * 0.82;
  var cpx = W * 0.42, cpy = H * 0.44;
  var p1x = mx - mR * 0.10, p1y = my + mR * 0.10;

  /* Delicate celestial flight path */
  c.save();
  c.strokeStyle = 'rgba(235, 215, 160, 0.20)';
  c.lineWidth = 1.6;
  c.setLineDash([4, 10]);
  c.beginPath();
  c.moveTo(p0x, p0y);
  c.quadraticCurveTo(cpx, cpy, p1x, p1y);
  c.stroke();
  c.restore();

  /* 6. ONE WHITE STORK FLAPPING STEADILY UP AND AWAY, GETTING SMALLER */
  var travelU = Math.min(1, u * 1.08); /* reaches moon around u = 0.92 */
  var a = 1 - travelU;
  var bx = a * a * p0x + 2 * a * travelU * cpx + travelU * travelU * p1x;
  var by = a * a * p0y + 2 * a * travelU * cpy + travelU * travelU * p1y;

  var dx = 2 * a * (cpx - p0x) + 2 * travelU * (p1x - cpx);
  var dy = 2 * a * (cpy - p0y) + 2 * travelU * (p1y - cpy);
  var pathAngle = Math.atan2(dy, dx);

  /* Flap cycle: 400 ms per beat (30 beats per 12 s loop) */
  var flapPhase = (t / 400) * TAU;

  /* Scale: starts large in foreground, shrinks to distant silhouette at moon */
  var startScale = (H / 1080) * 1.25;
  var endScale = (H / 1080) * 0.15;
  var storkScale = lerp(startScale, endScale, travelU);

  /* Subtle bobbing of body during flap */
  var bob = Math.cos(flapPhase) * 4 * storkScale;

  /* Loop boundary fade */
  var alpha = 1;
  if (u < 0.04) alpha = u / 0.04;
  else if (u > 0.94) alpha = Math.max(0, (1 - u) / 0.06);

  drawStork(c, bx, by + bob, storkScale, pathAngle, flapPhase, alpha);

  /* 7. CAPTION: bottom under the moon disc, clear of flight path and tung banners */
  var dim = Math.min(W, H);
  var labelX = (W < H) ? W * 0.5 : mx;
  var labelY = H * 0.90;
  c.save();
  c.textAlign = 'center';
  c.textBaseline = 'alphabetic';
  c.fillStyle = 'rgba(240, 234, 218, 0.92)';
  c.font = '600 ' + Math.round(dim * 0.024) + 'px "Avenir Next", "Thonburi", "Helvetica Neue", sans-serif';
  c.fillText('Charles Morton · to the moon', labelX, labelY);

  c.fillStyle = 'rgba(215, 205, 185, 0.80)';
  c.font = '400 ' + Math.round(dim * 0.019) + 'px "Avenir Next", "Thonburi", "Helvetica Neue", sans-serif';
  c.fillText('สู่ดวงจันทร์', labelX, labelY + dim * 0.034);
  c.restore();
}

D.addScene('stork-moon', draw, null, 's = s₀(1 − 0.85u), θ = ωt (Morton\'s moon flight)');
})();

/* ---- stork-map ---- */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

var afroEurasiaCoords = [
  [-5, 36.2],
  [-9, 37], [-9, 43], [-4, 43], [-2, 43], [-1, 44], [-4, 48], [-1, 49], [2, 51],
  [4, 52], [8, 54], [8, 57], [10, 57], [10, 54], [12, 54],
  [14, 54], [19, 54], [24, 57], [24, 60], [30, 60],
  [28, 65], [20, 64], [18, 60], [16, 56], [12, 58], [11, 59], [5, 59], [5, 62], [10, 64], [15, 68], [25, 71],
  [35, 69], [40, 65], [50, 60], [50, 45], [45, 40],
  [45, 30], [45, 20], [51, 10], [40, -4], [40, -10], [35, -20], [27, -33], [20, -35], [18, -34],
  [14, -22], [12, -15], [13, -6], [9, -1], [9, 4], [0, 5], [-8, 4], [-14, 10], [-17, 15], [-17, 21], [-10, 30], [-6, 34],
  [-5, 35.8],
  [0, 35.8], [5, 37], [10, 33], [20, 32], [25, 31], [30, 31],
  [34, 31], [35, 33], [36, 36], [33, 36], [28, 37], [26, 39],
  [26, 41], [23, 40], [24, 38], [21, 37], [19, 40], [19, 42], [14, 45],
  [12, 45], [14, 41], [18, 40], [16, 38], [15, 41], [12, 42], [9, 44],
  [5, 43], [3, 42], [0, 40], [-2, 36],
  [-5, 36.2]
];
var gbCoords = [
  [1,51],[2,52],[0,54],[-2,57],[-3,59],[-5,58],[-5,55],[-3,54],[-5,50],[-1,50],[1,51]
];
var sicilyCoords = [
  [13,37],[15,37],[15,38],[12,38],[13,37]
];

function proj(lon, lat, W, H) {
  var scale = H * 0.009;
  return [W * 0.5 + (lon - 15) * scale, H * 0.5 - (lat - 15) * scale];
}

function drawStork(c, x, y, s, t, angle) {
  c.save();
  c.translate(x, y);
  c.rotate(angle);
  
  var wflap = Math.sin(t/120);
  var wy = s * 1.8 + wflap * s * 0.8;
  var wtx = -s * 0.2;
  
  // Black flight feathers (underneath)
  paper(c, poly([[-s*0.2, s*0.1], [wtx - s*0.7, wy], [-s*0.8, s*0.1]]), '#25221f', 1);
  paper(c, poly([[-s*0.2, -s*0.1], [wtx - s*0.7, -wy], [-s*0.8, -s*0.1]]), '#25221f', 1);
  
  // White wing coverts (on top)
  paper(c, poly([[s*0.4, s*0.1], [wtx, wy], [-s*0.4, s*0.1]]), '#fff', 1);
  paper(c, poly([[s*0.4, -s*0.1], [wtx, -wy], [-s*0.4, -s*0.1]]), '#fff', 1);
  
  // Tail (black)
  paper(c, poly([[-s*0.6, s*0.15], [-s*1.2, s*0.08], [-s*1.2, -s*0.08], [-s*0.6, -s*0.15]]), '#25221f', 1);
  
  // Legs trailing
  c.strokeStyle = '#c9472f'; c.lineWidth = s*0.15; c.lineCap = 'round';
  c.beginPath(); c.moveTo(-s*0.8, s*0.08); c.lineTo(-s*1.6, s*0.12); c.stroke();
  c.beginPath(); c.moveTo(-s*0.8, -s*0.08); c.lineTo(-s*1.6, -s*0.12); c.stroke();

  // Body
  paper(c, function(q) { q.beginPath(); q.ellipse(0, 0, s*0.8, s*0.35, 0, 0, TAU); }, '#fff', 1);
  
  // Neck and head
  paper(c, poly([[s*0.6, -s*0.1], [s*1.2, -s*0.08], [s*1.2, s*0.08], [s*0.6, s*0.1]]), '#fff', 1);
  paper(c, function(q) { q.beginPath(); q.arc(s*1.3, 0, s*0.2, 0, TAU); }, '#fff', 1);
  
  // Red bill
  paper(c, poly([[s*1.4, -s*0.06], [s*2.2, 0], [s*1.4, s*0.06]]), '#c9472f', 1);
  
  // Spear through neck
  c.strokeStyle = '#5c4033'; c.lineWidth = s*0.1;
  c.beginPath(); c.moveTo(s*1.0, -s*1.2); c.lineTo(s*1.2, s*1.2); c.stroke();
  paper(c, poly([[s*1.2, s*1.2], [s*1.05, s*1.0], [s*1.35, s*1.0]]), '#4a332a', 1); // spearhead
  
  c.restore();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;
  
  // Sea wash (old atlas style)
  var g = c.createRadialGradient(W*0.5, H*0.5, H*0.1, W*0.5, H*0.5, W*0.8);
  g.addColorStop(0, '#c3d5d8'); g.addColorStop(1, '#a1babc');
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  
  // Draw continents
  function drawCont(coords) {
    var pts = coords.map(function(pt) { return proj(pt[0], pt[1], W, H); });
    paper(c, poly(pts), '#eadeca', 1.5);
  }
  drawCont(afroEurasiaCoords);
  drawCont(gbCoords);
  drawCont(sicilyCoords);
  
  // Route
  var routeLonLat = [
    [24, -2],   // Congo basin
    [22, 5],    // CAR
    [20, 15],   // Chad / Sahel
    [18, 25],   // Libya
    [15, 34],   // Med Sea
    [14, 37.5], // Sicily
    [13, 42],   // Italy
    [12, 47],   // Alps
    [11.5, 50], // Germany
    [11.17, 53.97] // Klütz
  ];
  
  var routePts = routeLonLat.map(function(pt) { return proj(pt[0], pt[1], W, H); });
  
  var loopT = t % 12000;
  var T = 12000;
  var p = Math.min(1, Math.max(0, (loopT - 1000) / 8000)); // route takes 8s
  
  // Dashed route line up to p
  c.save();
  c.beginPath();
  c.moveTo(routePts[0][0], routePts[0][1]);
  for (var i=1; i<routePts.length; i++) c.lineTo(routePts[i][0], routePts[i][1]);
  
  var totalLen = 0;
  var segLens = [];
  for (var i=0; i<routePts.length-1; i++) {
    var d = Math.hypot(routePts[i+1][0] - routePts[i][0], routePts[i+1][1] - routePts[i][1]);
    segLens.push(d);
    totalLen += d;
  }
  
  var targetLen = p * totalLen;
  c.beginPath();
  c.moveTo(routePts[0][0], routePts[0][1]);
  var drawLen = 0;
  var birdPt = routePts[0];
  var birdAngle = 0;
  
  for (var i=0; i<routePts.length-1; i++) {
    if (drawLen + segLens[i] < targetLen) {
      c.lineTo(routePts[i+1][0], routePts[i+1][1]);
      drawLen += segLens[i];
    } else {
      var frac = (targetLen - drawLen) / segLens[i];
      var bx = lerp(routePts[i][0], routePts[i+1][0], frac);
      var by = lerp(routePts[i][1], routePts[i+1][1], frac);
      c.lineTo(bx, by);
      birdPt = [bx, by];
      birdAngle = Math.atan2(routePts[i+1][1] - routePts[i][1], routePts[i+1][0] - routePts[i][0]);
      break;
    }
  }
  
  c.strokeStyle = '#4a3f35';
  c.lineWidth = H*0.006;
  c.setLineDash([H*0.015, H*0.012]);
  c.stroke();
  c.restore();
  
  // Klütz Pin and label (appears at the end)
  var klutz = routePts[routePts.length-1];
  if (p > 0.95) {
    var pinAlpha = Math.min(1, (p - 0.95) * 20);
    c.globalAlpha = pinAlpha;
    paper(c, function(q) { q.beginPath(); q.arc(klutz[0], klutz[1]-H*0.03, H*0.015, 0, TAU); }, '#c9472f', 1);
    c.beginPath(); c.moveTo(klutz[0], klutz[1]-H*0.03); c.lineTo(klutz[0], klutz[1]); c.strokeStyle='#2a1e10'; c.lineWidth=2; c.stroke();
    c.fillStyle = 'rgba(255,255,255,0.4)'; c.beginPath(); c.arc(klutz[0]-H*0.005, klutz[1]-H*0.035, H*0.004, 0, TAU); c.fill();
    
    c.fillStyle = '#2a1e10';
    c.font = '700 ' + Math.round(H * 0.025) + 'px "Avenir Next", sans-serif';
    c.textAlign = 'center';
    c.textBaseline = 'bottom';
    c.fillText('1822', klutz[0], klutz[1] - H*0.045);
    c.globalAlpha = 1;
  }
  
  // Bird flying
  if (p > 0 && p < 1) {
    if (p > 0.95) c.globalAlpha = (1 - p) * 20;
    drawStork(c, birdPt[0], birdPt[1], H*0.025, t, birdAngle);
    c.globalAlpha = 1;
  }
}

D.addScene('stork-map', draw, null, 'p = min(1, t/T) (the route)');

})();

/* ---- stork-tally ---- */
/* 'stork-tally'  arrow-storks recorded in Germany: chalk tally marks drawn in
   fives up to 25 on a slate board, an African spear icon above each group,
   and 'about 25, as of 2003'.
   Render: node doodles/render.mjs stork-tally --bg none --secs 12 */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

/* deterministic hash for hand-drawn chalk variation */
function hash2(i, j) {
  var h = (i * 374761393 + j * 668265263) ^ 0x5bf03635;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/* fit text font size to ensure it never clips at frame edge */
function setChalkFont(c, text, maxW, targetSz, weight) {
  var sz = targetSz;
  c.font = weight + ' ' + Math.round(sz) + 'px "Avenir Next", "Helvetica Neue", sans-serif';
  while (c.measureText(text).width > maxW && sz > 12) {
    sz -= 1;
    c.font = weight + ' ' + Math.round(sz) + 'px "Avenir Next", "Helvetica Neue", sans-serif';
  }
}

/* a natural chalk stroke with organic hand curve, chalk tooth, and powdery halo */
function chalkStroke(c, x0, y0, x1, y1, p, w, seed) {
  if (p <= 0) return;
  var curX = lerp(x0, x1, p), curY = lerp(y0, y1, p);
  var dx = curX - x0, dy = curY - y0, dist = Math.hypot(dx, dy);
  if (dist < 0.5) return;
  var nx = -dy / dist, ny = dx / dist;

  /* organic hand curvature: slight arc plus subtle micro-texture */
  var handCurve = (hash2(seed, 3) - 0.5) * dist * 0.03;
  var steps = Math.max(5, Math.floor(dist / 5));
  var pts = [[x0, y0]];
  for (var i = 1; i <= steps; i++) {
    var u = i / steps;
    var arc = Math.sin(u * Math.PI) * handCurve;
    var tooth = (hash2(seed, i * 11 + 5) - 0.5) * w * 0.18;
    var off = arc + tooth;
    pts.push([lerp(x0, curX, u) + nx * off, lerp(y0, curY, u) + ny * off]);
  }

  c.save();
  c.lineCap = 'round';
  c.lineJoin = 'round';

  /* 1. powdery chalk dust halo */
  c.strokeStyle = 'rgba(235, 238, 245, 0.25)';
  c.lineWidth = w * 1.75;
  c.beginPath();
  pts.forEach(function (pt, idx) { idx ? c.lineTo(pt[0], pt[1]) : c.moveTo(pt[0], pt[1]); });
  c.stroke();

  /* 2. textured chalk core */
  c.strokeStyle = 'rgba(252, 250, 244, 0.9)';
  c.lineWidth = w;
  c.beginPath();
  pts.forEach(function (pt, idx) { idx ? c.lineTo(pt[0], pt[1]) : c.moveTo(pt[0], pt[1]); });
  c.stroke();

  /* 3. bright chalk ridge */
  c.strokeStyle = 'rgba(255, 255, 255, 0.98)';
  c.lineWidth = w * 0.42;
  c.beginPath();
  pts.forEach(function (pt, idx) { idx ? c.lineTo(pt[0], pt[1]) : c.moveTo(pt[0], pt[1]); });
  c.stroke();

  /* 4. active chalk tip contact and dust flecks while drawing */
  if (p < 0.98) {
    c.fillStyle = '#ffffff';
    c.beginPath();
    c.arc(curX, curY, w * 0.85, 0, TAU);
    c.fill();
    for (var k = 0; k < 4; k++) {
      var rx = curX + (hash2(seed, k * 17 + 3) - 0.5) * w * 4;
      var ry = curY + (hash2(seed, k * 23 + 7) - 0.1) * w * 4;
      c.fillStyle = 'rgba(255, 255, 255, 0.48)';
      c.fillRect(rx, ry, 2, 2);
    }
  }
  c.restore();
}

/* African hunting spear in chalk (the Pfeilstorch spear):
   slender leaf-iron blade with sharp basal barbs,
   criss-cross sinew socket wrap, long tapered hardwood shaft */
function spearIcon(c, cx, cy, s, p, seed) {
  if (p <= 0) return;
  c.save();
  c.translate(cx, cy);

  var ang = -0.3 + (hash2(seed, 2) - 0.5) * 0.08;
  c.rotate(ang);

  var totalLen = s * 1.85;
  var shaftLen = totalLen * 0.65;
  var headLen = totalLen * 0.35;
  var w = s * 0.054;

  /* shaft draws down first */
  var pShaft = Math.min(1, p * 1.45);
  chalkStroke(c, 0, shaftLen * 0.5, 0, -shaftLen * 0.5, pShaft, w, seed);

  /* spearhead forms */
  var pHead = Math.max(0, Math.min(1, (p - 0.28) / 0.72));
  if (pHead > 0) {
    var topY = -shaftLen * 0.5 - headLen;
    var baseY = -shaftLen * 0.5;
    var midY = topY + headLen * 0.48;
    var hw = s * 0.145 * pHead;

    /* slender leaf iron blade with basal barbs */
    c.strokeStyle = 'rgba(252, 250, 245, 0.95)';
    c.fillStyle = 'rgba(240, 235, 220, 0.38)';
    c.lineWidth = w * 0.85;
    c.lineJoin = 'round';
    c.beginPath();
    c.moveTo(0, topY);
    c.quadraticCurveTo(-hw * 1.1, midY, -hw * 0.65, baseY + headLen * 0.14);
    c.lineTo(-hw * 0.88, baseY + headLen * 0.2); /* barb */
    c.lineTo(0, baseY);
    c.lineTo(hw * 0.88, baseY + headLen * 0.2);  /* barb */
    c.lineTo(hw * 0.65, baseY + headLen * 0.14);
    c.quadraticCurveTo(hw * 1.1, midY, 0, topY);
    c.closePath();
    c.fill();
    c.stroke();

    /* central blade ridge */
    chalkStroke(c, 0, baseY, 0, topY, pHead, w * 0.72, seed + 1);

    /* cross-hatched sinew wrapping on socket */
    c.strokeStyle = 'rgba(255, 255, 255, 0.88)';
    c.lineWidth = w * 0.7;
    for (var b = 0; b < 4; b++) {
      var by = baseY + b * (s * 0.038);
      c.beginPath();
      c.moveTo(-w * 2.2, by);
      c.lineTo(w * 2.2, by);
      c.stroke();
    }
  }

  /* chalk impact dust puff when spear first lands */
  if (p > 0.15 && p < 0.65) {
    var puffP = (p - 0.15) / 0.5;
    c.fillStyle = 'rgba(255, 255, 255,' + (0.35 * (1 - puffP)) + ')';
    for (var d = 0; d < 6; d++) {
      var dth = d / 6 * TAU;
      var dr = puffP * s * 0.18;
      c.fillRect(Math.cos(dth) * dr - 1.5, shaftLen * 0.5 + Math.sin(dth) * dr - 1.5, 3, 3);
    }
  }

  c.restore();
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;
  var phone = W < 600 || W < H;
  var dim = Math.min(W, H);

  /* 1. Wood frame & slate board */
  var fw = Math.round(dim * 0.048);
  c.fillStyle = '#422610';
  c.fillRect(0, 0, W, H);

  /* outer bevel and wood grain tones */
  c.fillStyle = '#55341a';
  c.fillRect(fw * 0.25, fw * 0.25, W - fw * 0.5, H - fw * 0.5);
  c.fillStyle = '#341c0a';
  c.fillRect(fw * 0.7, fw * 0.7, W - fw * 1.4, H - fw * 1.4);

  /* 45-degree corner mitre cuts */
  c.strokeStyle = 'rgba(0, 0, 0, 0.45)';
  c.lineWidth = 2.5;
  c.beginPath();
  c.moveTo(0, 0); c.lineTo(fw, fw);
  c.moveTo(W, 0); c.lineTo(W - fw, fw);
  c.moveTo(0, H); c.lineTo(fw, H - fw);
  c.moveTo(W, H); c.lineTo(W - fw, H - fw);
  c.stroke();

  /* slate slab */
  var sx = fw, sy = fw, sw = W - 2 * fw, sh = H - 2 * fw;
  var slateGrad = c.createRadialGradient(W * 0.5, H * 0.46, dim * 0.15, W * 0.5, H * 0.5, dim * 0.85);
  slateGrad.addColorStop(0, '#262d35');
  slateGrad.addColorStop(0.7, '#1d2228');
  slateGrad.addColorStop(1, '#15181b');
  c.fillStyle = slateGrad;
  c.fillRect(sx, sy, sw, sh);

  /* inner bevel shadow around slate */
  c.strokeStyle = 'rgba(0, 0, 0, 0.65)';
  c.lineWidth = 7;
  c.strokeRect(sx + 3.5, sy + 3.5, sw - 7, sh - 7);

  /* faint slate natural cleavage lines */
  c.strokeStyle = 'rgba(255, 255, 255, 0.018)';
  c.lineWidth = 1;
  for (var sl = 0; sl < 12; sl++) {
    var sly = sy + sh * (0.08 + sl * 0.075);
    c.beginPath();
    c.moveTo(sx + 10, sly);
    c.lineTo(sx + sw - 10, sly + (hash2(sl, 5) - 0.5) * 8);
    c.stroke();
  }

  /* chalk eraser wipe streaks */
  c.save();
  c.lineCap = 'round';
  c.strokeStyle = 'rgba(235, 240, 248, 0.028)';
  for (var wIdx = 0; wIdx < 10; wIdx++) {
    c.lineWidth = dim * (0.06 + 0.03 * (wIdx % 3));
    c.beginPath();
    var ax = sx + sw * (0.12 + 0.76 * (wIdx / 9));
    var ay = sy + sh * (0.22 + 0.55 * ((wIdx * 5) % 9 / 9));
    c.arc(ax, ay, dim * 0.22, 0.3 + wIdx * 0.35, 2.7 + wIdx * 0.35);
    c.stroke();
  }
  c.restore();

  /* bottom chalk tray */
  var trayH = fw * 0.75;
  var trayY = H - fw - trayH;
  c.fillStyle = '#2c1607';
  c.fillRect(sx, trayY, sw, trayH);
  c.fillStyle = 'rgba(255, 255, 255, 0.1)';
  c.fillRect(sx, trayY, sw, 2.5);

  /* chalk dust in tray */
  var dustGrad = c.createLinearGradient(0, trayY + trayH - 6, 0, trayY + trayH);
  dustGrad.addColorStop(0, 'rgba(255, 255, 255, 0)');
  dustGrad.addColorStop(1, 'rgba(255, 255, 255, 0.18)');
  c.fillStyle = dustGrad;
  c.fillRect(sx, trayY + trayH - 6, sw, 6);

  /* chalk stick */
  var chkX = sx + sw * 0.76, chkY = trayY + trayH * 0.32, chkW = dim * 0.065, chkH = dim * 0.016;
  c.fillStyle = 'rgba(0, 0, 0, 0.45)';
  c.fillRect(chkX + 2, chkY + chkH, chkW, 2.5);
  c.fillStyle = '#f3f0e8';
  c.fillRect(chkX, chkY, chkW, chkH);
  c.fillStyle = '#dbd6c8';
  c.fillRect(chkX + chkW - 4, chkY, 4, chkH);

  /* felt eraser */
  var erX = sx + sw * 0.84, erY = trayY + trayH * 0.16, erW = dim * 0.09, erH = dim * 0.026;
  c.fillStyle = '#4c321e';
  c.fillRect(erX, erY, erW, erH * 0.58);
  c.fillStyle = '#6f737a';
  c.fillRect(erX, erY + erH * 0.58, erW, erH * 0.42);

  /* 2. Board Header */
  c.textAlign = 'center';
  c.textBaseline = 'middle';

  var titleY = sy + sh * 0.088;
  c.fillStyle = 'rgba(252, 250, 244, 0.95)';
  setChalkFont(c, 'PFEILSTÖRCHE · ARROW-STORKS', sw * 0.88, dim * 0.046, '700');
  c.fillText('PFEILSTÖRCHE · ARROW-STORKS', W * 0.5, titleY);

  var subY = titleY + (phone ? dim * 0.048 : H * 0.042);
  c.fillStyle = 'rgba(228, 232, 240, 0.76)';
  setChalkFont(c, 'Recorded in Germany with African spears · นกกระสาลูกศร', sw * 0.88, dim * 0.026, '500');
  c.fillText('Recorded in Germany with African spears · นกกระสาลูกศร', W * 0.5, subY);

  /* chalk divider line with comfortable margin above spears */
  var divY = subY + (phone ? dim * 0.038 : H * 0.032);
  chalkStroke(c, sx + sw * 0.08, divY, sx + sw * 0.92, divY, 1, 2.2, 999);

  /* 3. Tally Groups & Spear Icons
     5 groups of 5 tallies = 25 marks.
     T_START = 500ms, STRIDE = 265ms, MARK_DUR = 160ms.
     Mark 0: 500ms -> Mark 24: 6860ms. */
  var T_START = 500;
  var STRIDE = 265;
  var MARK_DUR = 160;

  var groups = 5;
  var marksPerGroup = 5;
  var totalMarks = 25;

  var rowY = phone ? (sy + sh * 0.36) : (sy + sh * 0.42);
  var tallyH = phone ? (dim * 0.22) : (H * 0.185);
  var groupW = sw * (phone ? 0.16 : 0.128);
  var groupGap = sw * (phone ? 0.03 : 0.046);
  var totalGroupsW = groups * groupW + (groups - 1) * groupGap;
  var groupsX0 = sx + (sw - totalGroupsW) * 0.5;

  var completedCount = 0;

  /* faint chalk baseline for the tallies */
  c.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  c.lineWidth = 1.5;
  c.beginPath();
  c.moveTo(groupsX0 - groupGap * 0.5, rowY + tallyH + 7);
  c.lineTo(groupsX0 + totalGroupsW + groupGap * 0.5, rowY + tallyH + 7);
  c.stroke();

  /* historical labels: only 1822 · Klütz under the first mark and 2003 at the end */
  var labelY = rowY + tallyH + (phone ? dim * 0.04 : H * 0.034);
  c.fillStyle = 'rgba(240, 242, 248, 0.68)';

  /* 1822 · Klütz under the first mark */
  var firstMarkX = groupsX0 + groupW * 0.18;
  setChalkFont(c, '1822 · Klütz', groupW * 1.2, dim * 0.02, '600');
  c.fillText('1822 · Klütz', firstMarkX, labelY);

  /* 2003 at the end */
  var lastGroupX = groupsX0 + 4 * (groupW + groupGap);
  var endMarkX = lastGroupX + groupW * 0.5;
  setChalkFont(c, '2003', groupW * 0.8, dim * 0.02, '600');
  c.fillText('2003', endMarkX, labelY);

  for (var g = 0; g < groups; g++) {
    var gx = groupsX0 + g * (groupW + groupGap);
    var gy = rowY;

    /* tallies 1..5 in this group */
    for (var m = 0; m < marksPerGroup; m++) {
      var globalIdx = g * marksPerGroup + m;
      var markStart = T_START + globalIdx * STRIDE;
      var pMark = Math.max(0, Math.min(1, (t - markStart) / MARK_DUR));
      if (pMark >= 0.95) completedCount++;

      var strokeW = Math.max(3.5, dim * 0.007);
      var markSeed = 100 + globalIdx * 19;

      if (m < 4) {
        /* vertical tally: organic tilt and slight fanning */
        var mx = gx + groupW * (0.18 + m * 0.21);
        var tilt = (m - 1.5) * 0.026;
        var topX = mx - tilt * tallyH * 0.5 + (hash2(markSeed, 1) - 0.5) * groupW * 0.04;
        var topY = gy + (hash2(markSeed, 2) - 0.5) * tallyH * 0.05;
        var botX = mx + tilt * tallyH * 0.5 + (hash2(markSeed, 3) - 0.5) * groupW * 0.04;
        var botY = gy + tallyH + (hash2(markSeed, 4) - 0.5) * tallyH * 0.05;
        chalkStroke(c, topX, topY, botX, botY, pMark, strokeW, markSeed);
      } else {
        /* 5th tally: energetic diagonal slash across all four verticals */
        var slashX0 = gx + groupW * 0.04;
        var slashY0 = gy + tallyH * 0.85;
        var slashX1 = gx + groupW * 0.96;
        var slashY1 = gy + tallyH * 0.15;
        chalkStroke(c, slashX0, slashY0, slashX1, slashY1, pMark, strokeW * 1.25, markSeed);
      }
    }

    /* African spear icon above this group: positioned with clear headroom below divider */
    var fifthMarkEnd = T_START + (g * marksPerGroup + 4) * STRIDE + MARK_DUR;
    var pSpear = Math.max(0, Math.min(1, (t - fifthMarkEnd) / 340));
    var spearCx = gx + groupW * 0.5;
    var spearCy = gy - (phone ? dim * 0.075 : H * 0.058);
    var spearSize = phone ? (dim * 0.105) : (H * 0.082);
    spearIcon(c, spearCx, spearCy, spearSize, pSpear, 500 + g * 37);
  }

  /* 4. Chalk Tally Count Indicator & Final Summary */
  var allMarksEnd = T_START + (totalMarks - 1) * STRIDE + MARK_DUR;
  var pSummary = Math.max(0, Math.min(1, (t - (allMarksEnd + 150)) / 600));

  var centerTextY = rowY + tallyH + (phone ? dim * 0.13 : H * 0.108);

  /* Chalk count indicator during counting phase */
  if (pSummary < 1) {
    c.fillStyle = 'rgba(255, 255, 255,' + (0.95 * (1 - pSummary)) + ')';
    setChalkFont(c, 'RECORDED: ' + completedCount + ' / 25', sw * 0.88, dim * 0.05, '700');
    c.fillText('RECORDED: ' + completedCount + ' / 25', W * 0.5, centerTextY);
  }

  /* Climax headline: "about 25, as of 2003" */
  if (pSummary > 0) {
    c.save();
    c.globalAlpha = ease(pSummary);

    c.fillStyle = '#ffffff';
    setChalkFont(c, 'about 25, as of 2003', sw * 0.88, dim * 0.06, '700');
    c.fillText('about 25, as of 2003', W * 0.5, centerTextY);

    var noteY = centerTextY + (phone ? dim * 0.06 : H * 0.048);
    c.fillStyle = 'rgba(235, 240, 248, 0.82)';
    var noteText = 'documented arrow-storks in Germany · นกกระสาลูกศรที่พบบันทึก';
    setChalkFont(c, noteText, sw * 0.9, dim * 0.028, '500');
    c.fillText(noteText, W * 0.5, noteY);

    c.restore();
  }
}

D.addScene('stork-tally', draw, null, 'tally = 5·g + m, spear = 1(m == 4) (chalk tallies in fives)');
})();

/* ---- stork-shadow ---- */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, TAU = K.TAU;

// Helper: circular punched hole through hide
function punchDot(q, x, y, r) {
  q.moveTo(x + r, y);
  q.arc(x, y, r, 0, TAU);
}

// Helper: row of punched bead dots along a straight line
function punchDotRow(q, x1, y1, x2, y2, count, r) {
  for (var i = 0; i < count; i++) {
    var f = count > 1 ? i / (count - 1) : 0.5;
    punchDot(q, x1 + (x2 - x1) * f, y1 + (y2 - y1) * f, r);
  }
}

// Helper: curved row of punched bead dots along quadratic bezier
function punchQuadDots(q, x1, y1, cx, cy, x2, y2, count, r) {
  for (var i = 0; i < count; i++) {
    var t = count > 1 ? i / (count - 1) : 0.5;
    var it = 1 - t;
    var x = it * it * x1 + 2 * it * t * cx + t * t * x2;
    var y = it * it * y1 + 2 * it * t * cy + t * t * y2;
    punchDot(q, x, y, r);
  }
}

// Helper: tapered curved slit (feather vane, fur rib, flame curve)
function punchCurvedSlit(q, x1, y1, cx, cy, x2, y2, w) {
  var steps = 8;
  var ptsUp = [], ptsDn = [];
  for (var i = 0; i <= steps; i++) {
    var t = i / steps;
    var it = 1 - t;
    var x = it * it * x1 + 2 * it * t * cx + t * t * x2;
    var y = it * it * y1 + 2 * it * t * cy + t * t * y2;
    var tx = 2 * (1 - t) * (cx - x1) + 2 * t * (x2 - cx);
    var ty = 2 * (1 - t) * (cy - y1) + 2 * t * (y2 - cy);
    var tlen = Math.sqrt(tx * tx + ty * ty) || 1;
    var nx = -ty / tlen, ny = tx / tlen;
    var taper = Math.sin(t * Math.PI) * w * 0.5;
    ptsUp.push([x + nx * taper, y + ny * taper]);
    ptsDn.push([x - nx * taper, y - ny * taper]);
  }
  q.moveTo(ptsUp[0][0], ptsUp[0][1]);
  for (var j = 1; j <= steps; j++) q.lineTo(ptsUp[j][0], ptsUp[j][1]);
  for (var k = steps; k >= 0; k--) q.lineTo(ptsDn[k][0], ptsDn[k][1]);
  q.closePath();
}

// Helper: Thai traditional diamond punch (lai pracham yam motif)
function punchDiamond(q, cx, cy, rw, rh) {
  q.moveTo(cx, cy - rh);
  q.lineTo(cx + rw, cy);
  q.lineTo(cx, cy + rh);
  q.lineTo(cx - rw, cy);
  q.closePath();
}

// Helper: Thai floral rosette (lai dok loi)
function punchRosette(q, cx, cy, rad, petals, dotR) {
  punchDot(q, cx, cy, dotR * 1.4);
  for (var i = 0; i < petals; i++) {
    var a = (i / petals) * TAU;
    punchDot(q, cx + Math.cos(a) * rad, cy + Math.sin(a) * rad, dotR);
  }
}

// Draw a Nang Yai bamboo control pole with joints and bindings
function drawBambooStick(c, H, baseY, xOffset, topY) {
  c.save();
  var stickW = H * 0.013;
  var bottomY = H - baseY + 80;
  var x = xOffset || 0;
  var top = topY != null ? topY : -20;

  // Bamboo shaft
  c.fillStyle = '#1e1309';
  c.fillRect(x - stickW * 0.5, top, stickW, bottomY - top);

  // Bamboo nodes
  c.fillStyle = '#3a2412';
  c.strokeStyle = '#0e0804';
  c.lineWidth = 1.5;
  var nodeStep = H * 0.11;
  for (var ny = top + 35; ny < bottomY; ny += nodeStep) {
    c.beginPath();
    c.ellipse(x, ny, stickW * 0.75, stickW * 0.35, 0, 0, TAU);
    c.fill();
    c.stroke();
  }

  // Cord bindings at attachment point
  c.strokeStyle = '#614320';
  c.lineWidth = 2;
  for (var cy0 = top + 5; cy0 <= top + 30; cy0 += 6) {
    c.beginPath();
    c.moveTo(x - stickW * 0.7, cy0);
    c.lineTo(x + stickW * 0.7, cy0);
    c.stroke();
  }
  c.restore();
}

// =========================================================================
// STORK PUPPET (นกกระสา หนังใหญ่)
// =========================================================================
function drawStorkPuppet(q, u) {
  // Outer silhouette with carved kranok crest, scalloped wings and tail
  q.beginPath();
  // Beak tip
  q.moveTo(-4.0 * u, -4.6 * u);
  // Upper bill culmen up to forehead
  q.lineTo(-2.2 * u, -5.0 * u);
  q.quadraticCurveTo(-1.8 * u, -5.2 * u, -1.6 * u, -5.5 * u);
  // Triple-plumed kranok flame crest (หางหงส์)
  q.quadraticCurveTo(-1.85 * u, -5.85 * u, -1.7 * u, -6.25 * u); // plume 1 tip
  q.lineTo(-1.45 * u, -5.9 * u);
  q.quadraticCurveTo(-1.38 * u, -6.3 * u, -1.15 * u, -6.55 * u); // plume 2 tip
  q.lineTo(-0.98 * u, -6.15 * u);
  q.quadraticCurveTo(-0.82 * u, -6.45 * u, -0.62 * u, -6.65 * u); // plume 3 tip
  q.lineTo(-0.58 * u, -6.1 * u);
  // Back of neck curving gracefully down to mantle
  q.quadraticCurveTo(-0.35 * u, -5.3 * u, -0.2 * u, -4.6 * u);
  q.quadraticCurveTo(-0.1 * u, -4.2 * u, 0.5 * u, -4.2 * u);
  // Back & upper wing: carved scalloped feather contour
  q.lineTo(1.1 * u, -4.15 * u);
  q.lineTo(1.6 * u, -4.05 * u);
  q.lineTo(2.2 * u, -3.85 * u);
  q.lineTo(2.8 * u, -3.55 * u);
  // Layered tail feathers
  q.lineTo(3.5 * u, -3.1 * u); // feather 1 tip
  q.lineTo(3.1 * u, -3.0 * u);
  q.lineTo(3.4 * u, -2.8 * u); // feather 2 tip
  q.lineTo(3.0 * u, -2.7 * u);
  q.lineTo(3.2 * u, -2.5 * u); // feather 3 tip
  q.lineTo(2.5 * u, -2.55 * u);
  // Undertail & belly
  q.quadraticCurveTo(1.7 * u, -2.6 * u, 1.1 * u, -2.7 * u);
  // Rear leg & mounting bracket
  q.lineTo(1.0 * u, -2.7 * u);
  q.lineTo(1.0 * u, -1.5 * u);
  q.lineTo(1.2 * u, -1.45 * u); // knee spur
  q.lineTo(1.0 * u, -1.4 * u);
  q.lineTo(1.0 * u, 0); // foot
  q.lineTo(0.75 * u, 0);
  q.lineTo(0.75 * u, -1.4 * u);
  q.lineTo(0.75 * u, -2.7 * u);
  // Belly between legs
  q.lineTo(0.35 * u, -2.8 * u);
  // Front leg & mounting bracket
  q.lineTo(0.15 * u, -2.8 * u);
  q.lineTo(0.15 * u, -1.5 * u);
  q.lineTo(0.35 * u, -1.45 * u); // knee spur
  q.lineTo(0.15 * u, -1.4 * u);
  q.lineTo(0.15 * u, 0); // foot
  q.lineTo(-0.1 * u, 0);
  q.lineTo(-0.1 * u, -1.4 * u);
  q.lineTo(-0.1 * u, -2.9 * u);
  // Breast / chest: proud swelling curve with carved feather serrations
  q.quadraticCurveTo(-0.7 * u, -3.1 * u, -1.3 * u, -3.6 * u);
  q.lineTo(-1.15 * u, -3.8 * u); // breast scallop notch
  q.quadraticCurveTo(-1.5 * u, -4.1 * u, -1.35 * u, -4.5 * u);
  // Throat to lower bill
  q.quadraticCurveTo(-1.7 * u, -4.75 * u, -2.0 * u, -4.8 * u);
  // Lower bill to tip
  q.lineTo(-4.0 * u, -4.6 * u);
  q.closePath();

  // --- PUNCHED LIGHT PATTERNS (Nang Yai Openwork) ---
  var dotR = u * 0.030; // crisp legible punch size

  // 1. Bill: open mouth slit, serrations & nostril
  punchCurvedSlit(q, -3.8 * u, -4.62 * u, -3.0 * u, -4.72 * u, -2.1 * u, -4.82 * u, u * 0.065);
  punchCurvedSlit(q, -2.7 * u, -4.92 * u, -2.4 * u, -4.98 * u, -2.1 * u, -4.94 * u, u * 0.04);
  punchDotRow(q, -3.5 * u, -4.72 * u, -2.2 * u, -4.9 * u, 6, dotR * 0.8);

  // 2. Eye: glowing radiant eye with concentric rings & brow
  punchDot(q, -1.75 * u, -5.05 * u, dotR * 1.8);
  for (var a = 0; a < 8; a++) {
    var ea = (a / 8) * TAU;
    punchDot(q, -1.75 * u + Math.cos(ea) * u * 0.14, -5.05 * u + Math.sin(ea) * u * 0.14, dotR * 0.7);
  }
  punchCurvedSlit(q, -2.0 * u, -5.25 * u, -1.75 * u, -5.35 * u, -1.5 * u, -5.28 * u, u * 0.045);

  // 3. Crest: openwork flame cutouts
  punchCurvedSlit(q, -1.45 * u, -5.6 * u, -1.58 * u, -5.85 * u, -1.52 * u, -6.15 * u, u * 0.05);
  punchCurvedSlit(q, -1.15 * u, -5.7 * u, -1.22 * u, -6.05 * u, -1.1 * u, -6.35 * u, u * 0.055);
  punchCurvedSlit(q, -0.8 * u, -5.8 * u, -0.8 * u, -6.15 * u, -0.7 * u, -6.45 * u, u * 0.05);
  punchDot(q, -0.95 * u, -5.7 * u, dotR * 0.9);

  // 4. CARVED BORDER ALONG NECK:
  // Continuous bead border (kai pla) running parallel to front and back contours
  punchQuadDots(q, -1.35 * u, -4.7 * u, -1.1 * u, -4.2 * u, -1.0 * u, -3.6 * u, 9, dotR);
  punchQuadDots(q, -0.75 * u, -5.6 * u, -0.4 * u, -4.9 * u, -0.2 * u, -4.3 * u, 9, dotR);
  punchCurvedSlit(q, -1.45 * u, -4.65 * u, -1.2 * u, -4.15 * u, -1.1 * u, -3.65 * u, u * 0.035);
  punchCurvedSlit(q, -0.6 * u, -5.5 * u, -0.3 * u, -4.8 * u, -0.1 * u, -4.25 * u, u * 0.035);

  // Neck jewelry / collars (lai prajam yam)
  punchDiamond(q, -1.05 * u, -4.9 * u, u * 0.07, u * 0.09);
  punchDiamond(q, -0.75 * u, -4.4 * u, u * 0.08, u * 0.10);
  punchCurvedSlit(q, -1.2 * u, -4.6 * u, -0.95 * u, -4.65 * u, -0.7 * u, -4.6 * u, u * 0.045);

  // 5. CARVED BORDER ALONG BREAST & BELLY:
  punchQuadDots(q, -1.1 * u, -3.7 * u, -0.6 * u, -3.2 * u, 0.2 * u, -3.0 * u, 10, dotR * 1.15);
  punchCurvedSlit(q, -1.2 * u, -3.65 * u, -0.7 * u, -3.1 * u, 0.1 * u, -2.9 * u, u * 0.035);

  // Pectoral starburst medallion (lai dok loi)
  punchRosette(q, -0.55 * u, -3.7 * u, u * 0.21, 6, dotR * 1.2);
  punchDiamond(q, -0.55 * u, -3.7 * u, u * 0.08, u * 0.08);

  // 6. WINGS: CARVED BORDER & FEATHER OPENWORK
  // Upper back / wing ridge carved border
  punchDotRow(q, 0.4 * u, -4.0 * u, 2.5 * u, -3.6 * u, 12, dotR);
  punchCurvedSlit(q, 0.3 * u, -4.1 * u, 1.4 * u, -3.9 * u, 2.6 * u, -3.5 * u, u * 0.035);

  // Shoulder rosette
  punchRosette(q, 0.55 * u, -3.65 * u, u * 0.21, 6, dotR * 1.2);

  // 5 sweeping flight feathers (remiges) with long light slits
  punchCurvedSlit(q, 0.2 * u, -3.35 * u, 1.3 * u, -3.65 * u, 2.5 * u, -3.25 * u, u * 0.075);
  punchCurvedSlit(q, 0.4 * u, -3.05 * u, 1.5 * u, -3.35 * u, 2.8 * u, -2.95 * u, u * 0.075);
  punchCurvedSlit(q, 0.7 * u, -2.85 * u, 1.7 * u, -3.1 * u, 3.0 * u, -2.65 * u, u * 0.07);
  punchCurvedSlit(q, 1.0 * u, -2.7 * u, 1.9 * u, -2.9 * u, 3.1 * u, -2.4 * u, u * 0.065);

  // Graduated pinhole rows inside feather blades
  punchDotRow(q, 0.7 * u, -3.5 * u, 2.3 * u, -3.4 * u, 6, dotR * 0.85);
  punchDotRow(q, 0.9 * u, -3.2 * u, 2.5 * u, -3.1 * u, 6, dotR * 0.85);
  punchDotRow(q, 1.2 * u, -2.9 * u, 2.7 * u, -2.8 * u, 5, dotR * 0.85);

  // 7. TAIL CUTOUTS & CARVED BORDER
  punchCurvedSlit(q, 2.6 * u, -2.95 * u, 3.0 * u, -3.05 * u, 3.35 * u, -3.0 * u, u * 0.05);
  punchCurvedSlit(q, 2.4 * u, -2.7 * u, 2.8 * u, -2.8 * u, 3.15 * u, -2.75 * u, u * 0.05);
  punchDot(q, 3.3 * u, -2.9 * u, dotR * 0.95);
  punchDot(q, 3.1 * u, -2.6 * u, dotR * 0.95);

  // 8. Leg joints & carved brackets
  punchDiamond(q, 0.87 * u, -1.45 * u, u * 0.05, u * 0.08);
  punchCurvedSlit(q, 0.87 * u, -2.3 * u, 0.87 * u, -1.9 * u, 0.87 * u, -1.6 * u, u * 0.04);
  punchDiamond(q, 0.02 * u, -1.45 * u, u * 0.05, u * 0.08);
  punchCurvedSlit(q, 0.02 * u, -2.3 * u, 0.02 * u, -1.9 * u, 0.02 * u, -1.6 * u, u * 0.04);
}

// =========================================================================
// FOX PUPPET (สุนัขจิ้งจอก หนังใหญ่)
// =========================================================================
function drawFoxPuppet(q, u) {
  // Outer silhouette with carved flame fur, ears, mane, and brush tail
  q.beginPath();
  // Snout tip
  q.moveTo(2.7 * u, -1.2 * u);
  // Upper muzzle slope
  q.lineTo(1.8 * u, -1.55 * u);
  q.lineTo(1.35 * u, -2.0 * u);
  // Front ear with carved flame kranok tufts
  q.lineTo(1.45 * u, -2.4 * u);
  q.lineTo(1.55 * u, -2.95 * u); // front ear tip
  q.lineTo(1.25 * u, -2.7 * u); // inner notch
  q.lineTo(1.05 * u, -2.15 * u);
  // Crown between ears
  q.lineTo(0.9 * u, -2.2 * u);
  // Back ear with carved flame kranok tufts
  q.lineTo(0.95 * u, -2.6 * u);
  q.lineTo(0.95 * u, -3.05 * u); // back ear tip
  q.lineTo(0.7 * u, -2.8 * u);
  q.lineTo(0.55 * u, -2.15 * u);
  // Mane / back of neck
  q.lineTo(0.2 * u, -2.2 * u);
  // Spine: carved serrated flame-fur border along the entire back
  q.lineTo(-0.15 * u, -2.3 * u);
  q.lineTo(-0.1 * u, -2.45 * u); // fur notch 1
  q.lineTo(-0.45 * u, -2.35 * u);
  q.lineTo(-0.4 * u, -2.5 * u); // fur notch 2
  q.lineTo(-0.85 * u, -2.28 * u);
  q.lineTo(-0.8 * u, -2.42 * u); // fur notch 3
  q.lineTo(-1.25 * u, -2.15 * u);
  q.lineTo(-1.2 * u, -2.28 * u); // fur notch 4
  q.lineTo(-1.65 * u, -1.85 * u); // rump
  // Magnificent bushy tail with carved flame-fur scallops
  q.quadraticCurveTo(-2.3 * u, -2.3 * u, -3.0 * u, -2.75 * u);
  q.lineTo(-2.85 * u, -2.55 * u); // tail wave notch 1
  q.quadraticCurveTo(-3.3 * u, -2.85 * u, -3.9 * u, -2.6 * u); // plume tip 1
  q.lineTo(-3.6 * u, -2.35 * u);
  q.quadraticCurveTo(-4.1 * u, -2.45 * u, -4.3 * u, -2.0 * u); // main tail plume tip
  q.lineTo(-3.9 * u, -1.8 * u);
  q.quadraticCurveTo(-3.6 * u, -1.1 * u, -2.7 * u, -0.9 * u); // lower tail sweep
  q.lineTo(-2.85 * u, -1.1 * u); // tail notch 2
  q.quadraticCurveTo(-2.3 * u, -1.05 * u, -1.8 * u, -1.25 * u); // tail base
  // Hind leg (rear)
  q.lineTo(-1.6 * u, -1.3 * u);
  q.lineTo(-1.7 * u, 0); // back hind paw
  q.lineTo(-1.45 * u, 0);
  q.lineTo(-1.35 * u, -0.9 * u);
  // Hind leg (front)
  q.lineTo(-1.1 * u, -1.0 * u);
  q.lineTo(-1.15 * u, 0); // front hind paw
  q.lineTo(-0.9 * u, 0);
  q.lineTo(-0.8 * u, -1.0 * u);
  // Belly contour
  q.quadraticCurveTo(-0.1 * u, -1.05 * u, 0.4 * u, -1.0 * u);
  // Foreleg (back)
  q.lineTo(0.55 * u, -1.0 * u);
  q.lineTo(0.55 * u, 0); // back fore paw
  q.lineTo(0.75 * u, 0);
  q.lineTo(0.75 * u, -1.05 * u);
  // Foreleg (front)
  q.lineTo(1.05 * u, -1.1 * u);
  q.lineTo(1.05 * u, 0); // front fore paw
  q.lineTo(1.3 * u, 0);
  q.lineTo(1.3 * u, -1.2 * u);
  // Chest ruff with carved fur scallops
  q.quadraticCurveTo(1.6 * u, -1.15 * u, 1.8 * u, -0.85 * u);
  q.lineTo(1.65 * u, -0.75 * u); // ruff notch
  q.quadraticCurveTo(2.15 * u, -0.7 * u, 2.15 * u, -1.1 * u);
  // Lower jaw to snout tip
  q.lineTo(2.45 * u, -1.1 * u);
  q.lineTo(2.7 * u, -1.2 * u);
  q.closePath();

  // --- PUNCHED LIGHT PATTERNS (Nang Yai Openwork) ---
  var dotR = u * 0.030; // crisp legible punch size

  // 1. Muzzle, Whisker dots & Mouth slit
  punchCurvedSlit(q, 2.65 * u, -1.18 * u, 2.3 * u, -1.15 * u, 1.9 * u, -1.1 * u, u * 0.04);
  punchDotRow(q, 2.4 * u, -1.32 * u, 2.0 * u, -1.35 * u, 3, dotR * 0.7);
  punchDotRow(q, 2.3 * u, -1.42 * u, 1.9 * u, -1.45 * u, 3, dotR * 0.7);

  // 2. Glowing Eye & Arching Brow
  punchDot(q, 1.65 * u, -1.72 * u, dotR * 1.6);
  for (var fa = 0; fa < 6; fa++) {
    var fea = (fa / 6) * TAU;
    punchDot(q, 1.65 * u + Math.cos(fea) * u * 0.11, -1.72 * u + Math.sin(fea) * u * 0.11, dotR * 0.6);
  }
  punchCurvedSlit(q, 1.88 * u, -1.88 * u, 1.65 * u, -1.98 * u, 1.42 * u, -1.9 * u, u * 0.045);

  // 3. Ears: carved inner kranok flame cutouts
  punchCurvedSlit(q, 1.42 * u, -2.15 * u, 1.45 * u, -2.5 * u, 1.42 * u, -2.8 * u, u * 0.07);
  punchCurvedSlit(q, 0.88 * u, -2.2 * u, 0.9 * u, -2.55 * u, 0.9 * u, -2.9 * u, u * 0.07);

  // 4. CARVED BORDER ALONG MANE & CHEST
  punchQuadDots(q, 1.8 * u, -1.25 * u, 1.7 * u, -0.75 * u, 1.2 * u, -1.0 * u, 8, dotR);
  punchCurvedSlit(q, 1.9 * u, -1.2 * u, 1.8 * u, -0.7 * u, 1.3 * u, -0.95 * u, u * 0.035);

  // 5. CARVED BORDER ALONG SPINE
  punchQuadDots(q, 0.25 * u, -2.0 * u, -0.65 * u, -2.18 * u, -1.55 * u, -1.7 * u, 13, dotR);
  punchCurvedSlit(q, 0.2 * u, -2.12 * u, -0.65 * u, -2.28 * u, -1.5 * u, -1.8 * u, u * 0.035);

  // Ribcage / flank fur slits
  punchCurvedSlit(q, 0.5 * u, -1.7 * u, 0.3 * u, -1.4 * u, 0.1 * u, -1.15 * u, u * 0.05);
  punchCurvedSlit(q, 0.1 * u, -1.75 * u, -0.1 * u, -1.45 * u, -0.3 * u, -1.2 * u, u * 0.05);
  punchCurvedSlit(q, -0.3 * u, -1.75 * u, -0.5 * u, -1.5 * u, -0.7 * u, -1.25 * u, u * 0.05);

  // Shoulder & Hip medallions (Thai floral rosettes)
  punchRosette(q, 0.8 * u, -1.4 * u, u * 0.17, 5, dotR * 1.15);
  punchRosette(q, -1.1 * u, -1.45 * u, u * 0.19, 6, dotR * 1.2);

  // 6. BUSHY TAIL: MAGNIFICENT OPENWORK & CARVED BORDERS
  punchQuadDots(q, -1.9 * u, -1.8 * u, -2.7 * u, -2.35 * u, -3.8 * u, -2.45 * u, 10, dotR);
  punchCurvedSlit(q, -1.85 * u, -1.95 * u, -2.7 * u, -2.5 * u, -3.7 * u, -2.58 * u, u * 0.035);

  punchQuadDots(q, -1.9 * u, -1.3 * u, -2.7 * u, -1.2 * u, -3.6 * u, -1.8 * u, 10, dotR);
  punchCurvedSlit(q, -1.85 * u, -1.18 * u, -2.7 * u, -1.08 * u, -3.5 * u, -1.7 * u, u * 0.035);

  punchCurvedSlit(q, -1.85 * u, -1.45 * u, -2.85 * u, -1.95 * u, -3.95 * u, -2.2 * u, u * 0.075);
  punchCurvedSlit(q, -2.35 * u, -1.65 * u, -2.85 * u, -1.65 * u, -3.4 * u, -1.35 * u, u * 0.055);
  punchCurvedSlit(q, -2.55 * u, -2.05 * u, -3.1 * u, -2.25 * u, -3.6 * u, -2.35 * u, u * 0.055);

  punchDot(q, -4.05 * u, -2.35 * u, dotR * 1.25);
  punchDot(q, -4.15 * u, -2.05 * u, dotR * 1.2);
  punchDiamond(q, -3.9 * u, -2.0 * u, u * 0.06, u * 0.06);

  // 7. Leg joints
  punchDiamond(q, 1.15 * u, -0.5 * u, u * 0.045, u * 0.07);
  punchDiamond(q, -1.0 * u, -0.5 * u, u * 0.045, u * 0.07);
}

// =========================================================================
// DINNER PROPS
// =========================================================================
// Dinner 1: Flat shallow pedestal tray (พาน)
function drawPlatePuppet(q, u) {
  q.beginPath();
  // Pedestal base with carved foot
  q.moveTo(-1.2 * u, 0);
  q.lineTo(1.2 * u, 0);
  q.lineTo(0.9 * u, -0.18 * u);
  q.lineTo(0.35 * u, -0.38 * u);
  // Wide shallow tray with carved rim lip
  q.lineTo(2.0 * u, -0.55 * u);
  q.lineTo(2.1 * u, -0.72 * u); // rim outer corner
  q.lineTo(-2.1 * u, -0.72 * u);
  q.lineTo(-2.0 * u, -0.55 * u);
  q.lineTo(-0.35 * u, -0.38 * u);
  q.lineTo(-0.9 * u, -0.18 * u);
  q.closePath();

  // Punched light patterns
  var dotR = u * 0.026;
  // Rim carved bead border
  punchDotRow(q, -1.8 * u, -0.64 * u, 1.8 * u, -0.64 * u, 15, dotR);
  // Shallow soup surface slit
  punchCurvedSlit(q, -1.6 * u, -0.68 * u, 0, -0.69 * u, 1.6 * u, -0.68 * u, u * 0.035);
  // Lotus petal fretwork on pedestal
  punchDiamond(q, 0, -0.24 * u, u * 0.1, u * 0.12);
  punchDot(q, -0.6 * u, -0.09 * u, dotR * 1.2);
  punchDot(q, 0.6 * u, -0.09 * u, dotR * 1.2);
  punchCurvedSlit(q, -0.6 * u, -0.28 * u, -0.4 * u, -0.38 * u, -0.2 * u, -0.32 * u, u * 0.035);
  punchCurvedSlit(q, 0.2 * u, -0.32 * u, 0.4 * u, -0.38 * u, 0.6 * u, -0.28 * u, u * 0.035);
}

// Dinner 2: Tall narrow jar (คนโฑ / โถคอคอด)
function drawJarPuppet(q, u) {
  q.beginPath();
  // Pedestal base
  q.moveTo(-0.9 * u, 0);
  q.lineTo(0.9 * u, 0);
  q.lineTo(0.75 * u, -0.35 * u);
  // Bulbous lower vessel
  q.quadraticCurveTo(1.15 * u, -1.4 * u, 0.55 * u, -2.6 * u);
  // Tall, very narrow neck
  q.lineTo(0.25 * u, -4.3 * u);
  // Flared lip at mouth
  q.lineTo(0.48 * u, -4.55 * u);
  q.lineTo(0.42 * u, -4.75 * u);
  q.lineTo(-0.42 * u, -4.75 * u);
  q.lineTo(-0.48 * u, -4.55 * u);
  // Left neck & body
  q.lineTo(-0.25 * u, -4.3 * u);
  q.quadraticCurveTo(-1.15 * u, -1.4 * u, -0.75 * u, -0.35 * u);
  q.closePath();

  // Punched light patterns
  var dotR = u * 0.028;
  // Deep interior neck slit (stork's bill enters here)
  punchCurvedSlit(q, 0, -4.65 * u, 0, -3.6 * u, 0, -2.5 * u, u * 0.16);
  // Lip carved bead border
  punchDotRow(q, -0.3 * u, -4.68 * u, 0.3 * u, -4.68 * u, 5, dotR * 0.8);
  // Neck ornamental rings
  punchDotRow(q, -0.2 * u, -4.1 * u, 0.2 * u, -4.1 * u, 4, dotR * 0.85);
  punchDotRow(q, -0.22 * u, -3.4 * u, 0.22 * u, -3.4 * u, 4, dotR * 0.85);
  punchDiamond(q, 0, -2.85 * u, u * 0.09, u * 0.11);
  // Belly medallion (Thai floral rosette)
  punchRosette(q, 0, -1.5 * u, u * 0.24, 6, dotR * 1.2);
  punchDiamond(q, 0, -1.5 * u, u * 0.09, u * 0.09);
  // Lotus petal flank slits
  punchCurvedSlit(q, -0.55 * u, -2.0 * u, -0.75 * u, -1.5 * u, -0.55 * u, -0.95 * u, u * 0.05);
  punchCurvedSlit(q, 0.55 * u, -2.0 * u, 0.75 * u, -1.5 * u, 0.55 * u, -0.95 * u, u * 0.05);
  // Pedestal base bead row
  punchDotRow(q, -0.65 * u, -0.18 * u, 0.65 * u, -0.18 * u, 7, dotR);
}

// =========================================================================
// MAIN SCENE RENDER
// =========================================================================
function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t, u = H * 0.1;
  var tLoop = t % 12000;
  var phase = tLoop < 6000 ? 0 : 1;
  var pTime = (tLoop % 6000) / 6000;

  // --- LIT CLOTH SCREEN BACKGROUND (Nang Yai shadow play) ---
  // Warm oil-lamp glow behind white cotton screen with subtle organic flicker
  var flick = Math.sin(t * 0.0037) * 0.025 + Math.sin(t * 0.0083) * 0.012;
  var cx = W * 0.5, cy = H * 0.56;
  var glowR1 = H * (0.16 + flick);
  var glowR2 = W * (0.70 + flick);
  var glow = c.createRadialGradient(cx, cy, glowR1, cx, cy, glowR2);
  glow.addColorStop(0, '#fff0a5');
  glow.addColorStop(0.22, '#f5bc4f');
  glow.addColorStop(0.52, '#c76e20');
  glow.addColorStop(0.80, '#5f2405');
  glow.addColorStop(1.0, '#1a0b02');
  c.fillStyle = glow;
  c.fillRect(0, 0, W, H);

  // Woven screen fabric texture
  c.save();
  c.strokeStyle = 'rgba(0,0,0,0.035)';
  c.lineWidth = 1;
  for (var i = 0; i < W; i += 7) {
    c.beginPath(); c.moveTo(i, 0); c.lineTo(i, H); c.stroke();
  }
  for (var j = 0; j < H; j += 7) {
    c.beginPath(); c.moveTo(0, j); c.lineTo(W, j); c.stroke();
  }
  c.restore();

  // --- TIMING & STAGE TRANSITION ---
  // Dip puppets down behind screen edge during dinner change (around 6s mark)
  var moveY = 0;
  if (pTime < 0.08) {
    moveY = (0.08 - pTime) / 0.08 * H * 0.85;
  } else if (pTime > 0.92) {
    moveY = (pTime - 0.92) / 0.08 * H * 0.85;
  }
  var baseY = H * 0.78 + moveY;

  // DINNER PROP (Center)
  c.save();
  c.translate(W * 0.5, baseY);
  drawBambooStick(c, H, baseY, 0, -0.6 * u);
  paper(c, function (q) {
    if (phase === 0) drawPlatePuppet(q, u);
    else drawJarPuppet(q, u);
  }, '#150d06', 1);
  c.restore();

  // STORK PUPPET (Right side)
  c.save();
  if (phase === 0) {
    // DINNER 1 (Flat Plate):
    // Stork bends down on the right side of the plate and taps the rim: clack-clack-clack!
    var tapCycle = Math.sin(tLoop / 85);
    var isTapping = Math.max(0, tapCycle);
    var storkAngle = -0.32 - isTapping * 0.07; // tilt forward toward plate
    var storkDip = isTapping * 0.16 * u;
    var storkX0 = W * 0.81;
    var storkY0 = baseY + 2.1 * u + storkDip;
    c.translate(storkX0, storkY0);
    c.rotate(storkAngle);
    // Control sticks clamp the hide firmly:
    drawBambooStick(c, H, storkY0, 0, -2.8 * u);
    drawBambooStick(c, H, storkY0, 0.88 * u, -2.7 * u);
  } else {
    // DINNER 2 (Tall Narrow Jar):
    // Stork stands tall, reaches slender bill right down into mouth of tall jar, drinking easily
    var storkX1 = W * 0.74;
    var storkAngle1 = -0.05 + Math.sin(tLoop / 260) * 0.015;
    var storkY1 = baseY;
    c.translate(storkX1, storkY1);
    c.rotate(storkAngle1);
    drawBambooStick(c, H, storkY1, 0, -2.8 * u);
    drawBambooStick(c, H, storkY1, 0.88 * u, -2.7 * u);
  }
  paper(c, function (q) { drawStorkPuppet(q, u); }, '#150d06', 1);
  c.restore();

  // FOX PUPPET (Left side)
  c.save();
  if (phase === 0) {
    // DINNER 1 (Flat Plate):
    // Fox sits close on the left side of the plate, happily lapping up the soup
    var foxX0 = W * 0.28;
    var foxLap = Math.max(0, Math.sin(tLoop / 100)) * 0.08;
    var foxAngle0 = 0.18 + foxLap;
    c.translate(foxX0, baseY);
    c.rotate(foxAngle0);
    drawBambooStick(c, H, baseY, 0.9 * u, -1.0 * u);
    drawBambooStick(c, H, baseY, -1.2 * u, -1.2 * u);
  } else {
    // DINNER 2 (Tall Narrow Jar):
    // Fox circles in frustration: pacing back and forth, jumping / tilting head up at jar
    var foxPace = Math.sin(tLoop / 240) * u * 0.5;
    var foxX1 = W * 0.30 + foxPace;
    var foxAngle1 = -0.32 + Math.sin(tLoop / 150) * 0.08; // head tilted up helplessly
    c.translate(foxX1, baseY);
    c.rotate(foxAngle1);
    drawBambooStick(c, H, baseY, 0.9 * u, -1.0 * u);
    drawBambooStick(c, H, baseY, -1.2 * u, -1.2 * u);
  }
  paper(c, function (q) { drawFoxPuppet(q, u); }, '#150d06', 1);
  c.restore();
}

D.addScene('stork-shadow', draw, null, 'scene = Math.floor(t / 6000) (two dinners)');
})();

/* ---- stork-frieze ---- */
/* 'stork-frieze'  an ancient Egyptian temple frieze on carved limestone:
   a band of repeated saddle-billed stork signs (Gardiner G29, the 'ba' soul)
   and hieroglyphic glyphs (ankh, djed, was, wedjat, brazier) scrolls sideways
   like a procession along a temple wall.
   Render: node doodles/render.mjs stork-frieze --bg none --secs 12 */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

/* geometric path helpers */
function ell(x, y, rx, ry, rot) {
  return function (q) { q.beginPath(); q.ellipse(x, y, rx, ry, rot || 0, 0, TAU); };
}
function rect(x, y, w, h) {
  return poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]);
}
function star(x, y, rOut, rIn, pts) {
  return function (q) {
    q.beginPath();
    var n = pts || 5;
    for (var i = 0; i < n * 2; i++) {
      var r = (i % 2 === 0) ? rOut : rIn;
      var a = i / (n * 2) * TAU - Math.PI / 2;
      var px = x + Math.cos(a) * r, py = y + Math.sin(a) * r;
      i === 0 ? q.moveTo(px, py) : q.lineTo(px, py);
    }
    q.closePath();
  };
}

/* Palette: limestone stone, lapis lazuli, malachite green, red ochre, yellow gold, carbon black */
var PAL = {
  stone: '#ece3d2',
  stoneDark: '#ded3be',
  stoneJoint: 'rgba(90, 72, 50, 0.22)',
  lapis: '#1b3b6f',
  lapisDeep: '#122544',
  lapisBright: '#26549a',
  malachite: '#226343',
  malachiteDeep: '#16452e',
  malachiteLight: '#328c60',
  red: '#ab3222',
  redBright: '#c63d2c',
  ochre: '#cf982b',
  gold: '#f5c338',
  black: '#1a1816',
  white: '#f9f7f2'
};

/* Egyptian Hieroglyphs */

/* The Ankh (life): loop at top, crossbar, vertical stem */
function ankh(c, x, y, s) {
  var w = s * 0.44, h = s * 0.95;
  paper(c, function (q) {
    q.beginPath();
    q.ellipse(x, y - h * 0.26, w * 0.42, h * 0.26, 0, 0, TAU);
    q.ellipse(x, y - h * 0.26, w * 0.2, h * 0.14, 0, 0, TAU);
  }, PAL.malachite, 1.2);
  paper(c, rect(x - w * 0.48, y - h * 0.03, w * 0.96, h * 0.09), PAL.malachite, 1.2);
  paper(c, rect(x - w * 0.13, y + h * 0.05, w * 0.26, h * 0.45), PAL.malachite, 1.2);
  paper(c, rect(x - w * 0.18, y - h * 0.02, w * 0.36, h * 0.07), PAL.ochre, 1.3);
}

/* The Djed pillar (stability): column with 4 horizontal capitals */
function djed(c, x, y, s) {
  var w = s * 0.5, h = s * 0.95;
  paper(c, rect(x - w * 0.15, y - h * 0.05, w * 0.3, h * 0.55), PAL.lapis, 1.2);
  for (var i = 0; i < 4; i++) {
    var yy = y - h * (0.12 + i * 0.095);
    var bw = w * (0.86 - i * 0.06);
    paper(c, rect(x - bw * 0.5, yy, bw, h * 0.07), i % 2 === 0 ? PAL.lapis : PAL.malachite, 1.3);
  }
  paper(c, rect(x - w * 0.22, y + h * 0.45, w * 0.44, h * 0.06), PAL.ochre, 1.2);
}

/* The Was scepter (power): Seth head at top, straight shaft, forked base */
function was(c, x, y, s) {
  var w = s * 0.36, h = s * 1.05;
  paper(c, poly([
    [x - w * 0.45, y - h * 0.38],
    [x - w * 0.12, y - h * 0.52],
    [x + w * 0.04, y - h * 0.42],
    [x + w * 0.4, y - h * 0.5],
    [x + w * 0.18, y - h * 0.36],
    [x - w * 0.08, y - h * 0.32]
  ]), PAL.ochre, 1.3);
  paper(c, rect(x - w * 0.08, y - h * 0.32, w * 0.16, h * 0.72), PAL.ochre, 1.2);
  paper(c, poly([
    [x - w * 0.08, y + h * 0.4],
    [x - w * 0.35, y + h * 0.5],
    [x - w * 0.22, y + h * 0.5],
    [x, y + h * 0.43],
    [x + w * 0.22, y + h * 0.5],
    [x + w * 0.35, y + h * 0.5],
    [x + w * 0.08, y + h * 0.4]
  ]), PAL.ochre, 1.2);
}

/* The Eye of Horus (wedjat): protection and wholeness */
function wedjat(c, x, y, s) {
  var w = s * 0.75, h = s * 0.48;
  paper(c, poly([
    [x - w * 0.48, y - h * 0.16],
    [x, y - h * 0.44],
    [x + w * 0.48, y - h * 0.2],
    [x + w * 0.44, y - h * 0.12],
    [x, y - h * 0.34],
    [x - w * 0.44, y - h * 0.1]
  ]), PAL.lapis, 1.3);
  paper(c, ell(x, y - h * 0.05, w * 0.35, h * 0.19), PAL.white, 1.1);
  paper(c, ell(x + w * 0.02, y - h * 0.05, w * 0.15, h * 0.15), PAL.black, 1.4);
  paper(c, poly([
    [x + w * 0.32, y - h * 0.06],
    [x + w * 0.55, y - h * 0.06],
    [x + w * 0.55, y - h * 0.01],
    [x + w * 0.32, y + h * 0.02]
  ]), PAL.lapis, 1.2);
  paper(c, poly([
    [x - w * 0.1, y + h * 0.1],
    [x - w * 0.04, y + h * 0.45],
    [x + w * 0.04, y + h * 0.45],
    [x + w * 0.06, y + h * 0.1]
  ]), PAL.lapis, 1.2);
  paper(c, function (q) {
    q.beginPath();
    q.arc(x + w * 0.18, y + h * 0.22, w * 0.12, 0, Math.PI, false);
    q.lineWidth = s * 0.07;
  }, PAL.lapis, 1.2);
}

/* The Shen ring (eternity): knotted rope loop */
function shen(c, x, y, s) {
  var r = s * 0.26;
  paper(c, function (q) {
    q.beginPath();
    q.arc(x, y - r * 0.3, r, 0, TAU);
    q.arc(x, y - r * 0.3, r * 0.58, 0, TAU, true);
  }, PAL.gold, 1.3);
  paper(c, rect(x - r * 1.1, y + r * 0.7, r * 2.2, r * 0.28), PAL.gold, 1.3);
  paper(c, rect(x - r * 0.3, y + r * 0.5, r * 0.6, r * 0.25), PAL.red, 1.4);
}

/* The Foot (Gardiner D58, phonetic 'b'): knee, calf, heel, toes */
function foot(c, x, y, s) {
  var w = s * 0.52, h = s * 0.78;
  paper(c, poly([
    [x - w * 0.35, y - h * 0.5],
    [x - w * 0.08, y - h * 0.5],
    [x - w * 0.04, y - h * 0.12],
    [x + w * 0.45, y + h * 0.38],
    [x + w * 0.45, y + h * 0.5],
    [x - w * 0.42, y + h * 0.5],
    [x - w * 0.44, y + h * 0.28],
    [x - w * 0.3, y + h * 0.04],
    [x - w * 0.38, y - h * 0.3]
  ]), PAL.red, 1.3);
}

/* The Brazier with flame (Q7 / ba offering): cup and rising flame */
function brazier(c, x, y, s) {
  var w = s * 0.5, h = s * 0.7;
  paper(c, poly([
    [x - w * 0.42, y + h * 0.05],
    [x + w * 0.42, y + h * 0.05],
    [x + w * 0.3, y + h * 0.32],
    [x + w * 0.15, y + h * 0.36],
    [x + w * 0.2, y + h * 0.48],
    [x - w * 0.2, y + h * 0.48],
    [x - w * 0.15, y + h * 0.36],
    [x - w * 0.3, y + h * 0.32]
  ]), PAL.red, 1.2);
  paper(c, poly([
    [x, y - h * 0.48],
    [x + w * 0.18, y - h * 0.2],
    [x + w * 0.12, y],
    [x - w * 0.12, y],
    [x - w * 0.18, y - h * 0.24]
  ]), PAL.gold, 1.4);
}

/* Water ripple (Gardiner N35, 'n'): zig-zag */
function water(c, x, y, w, s) {
  var h = s * 0.18, pts = [], n = 7;
  for (var i = 0; i <= n; i++) {
    var px = x - w * 0.5 + i / n * w;
    var py = y + ((i % 2 === 0) ? -h : h);
    pts.push([px, py]);
  }
  for (var j = n; j >= 0; j--) {
    var qx = x - w * 0.5 + j / n * w;
    var qy = y + ((j % 2 === 0) ? -h : h) + s * 0.1;
    pts.push([qx, qy]);
  }
  paper(c, poly(pts), PAL.lapis, 1.2);
}

/* Lotus bloom (seshen): stem, red sepals, white/lapis petals */
function lotus(c, x, y, s) {
  var w = s * 0.48, h = s * 0.78;
  paper(c, rect(x - w * 0.07, y + h * 0.1, w * 0.14, h * 0.4), PAL.malachite, 1.1);
  paper(c, poly([
    [x - w * 0.36, y + h * 0.14],
    [x + w * 0.36, y + h * 0.14],
    [x + w * 0.24, y + h * 0.3],
    [x - w * 0.24, y + h * 0.3]
  ]), PAL.red, 1.2);
  paper(c, poly([
    [x, y - h * 0.4],
    [x + w * 0.44, y - h * 0.1],
    [x + w * 0.22, y + h * 0.14],
    [x - w * 0.22, y + h * 0.14],
    [x - w * 0.44, y - h * 0.1]
  ]), PAL.lapisBright, 1.3);
  paper(c, poly([
    [x, y - h * 0.44],
    [x + w * 0.2, y - h * 0.05],
    [x, y + h * 0.14],
    [x - w * 0.2, y - h * 0.05]
  ]), PAL.white, 1.4);
}

/* The Sun disk (Ra) with golden rim */
function sun(c, x, y, r) {
  paper(c, ell(x, y, r, r), PAL.gold, 1.3);
  paper(c, ell(x, y, r * 0.82, r * 0.82), PAL.red, 1.4);
}

/* The Saddle-Billed Stork sign (Gardiner G29):
   Facing right, feet on baseline fy, height scale u */
function storkSign(c, x, fy, u) {
  var bx = x, by = fy;
  c.lineCap = 'round';

  /* 1. Long legs: tarsus and tibia, standing in noble Egyptian stance */
  /* Back leg (slightly behind, tilted back) */
  c.strokeStyle = PAL.black; c.lineWidth = u * 0.16;
  c.beginPath();
  c.moveTo(bx - u * 0.3, by);
  c.lineTo(bx - u * 0.25, by - u * 2.3);
  c.lineTo(bx - u * 0.45, by - u * 4.6);
  c.stroke();

  /* Front leg (standing firmly upright) */
  c.beginPath();
  c.moveTo(bx + u * 0.4, by);
  c.lineTo(bx + u * 0.35, by - u * 2.3);
  c.lineTo(bx + u * 0.15, by - u * 4.6);
  c.stroke();

  /* Red knees (intertarsal joints) - key diagnostic of saddle-billed stork */
  paper(c, ell(bx - u * 0.25, by - u * 2.3, u * 0.22, u * 0.24), PAL.redBright, 1.4);
  paper(c, ell(bx + u * 0.35, by - u * 2.3, u * 0.22, u * 0.24), PAL.redBright, 1.4);

  /* Red feet flat on baseline: three forward toes with claws, rear spur */
  [[-0.3, by], [0.4, by]].forEach(function (f) {
    var fx = bx + f[0] * u, fy0 = f[1];
    paper(c, poly([
      [fx - u * 0.25, fy0],
      [fx + u * 0.55, fy0],
      [fx + u * 0.5, fy0 - u * 0.08],
      [fx + u * 0.1, fy0 - u * 0.1],
      [fx - u * 0.2, fy0 - u * 0.06]
    ]), PAL.redBright, 1.3);
  });

  /* 2. Tail feathers (black, angled down behind legs) */
  paper(c, poly([
    [bx - u * 1.5, by - u * 4.5],
    [bx - u * 2.8, by - u * 3.4],
    [bx - u * 2.5, by - u * 3.1],
    [bx - u * 1.3, by - u * 3.8]
  ]), PAL.black, 1.1);

  /* 3. Pure white breast and underbelly */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(bx - u * 1.6, by - u * 4.3);
    q.bezierCurveTo(bx - u * 1.4, by - u * 3.3, bx + u * 0.7, by - u * 3.3, bx + u * 1.5, by - u * 4.2);
    q.bezierCurveTo(bx + u * 2.1, by - u * 5.0, bx + u * 1.9, by - u * 6.1, bx + u * 1.1, by - u * 6.4);
    q.bezierCurveTo(bx + u * 0.3, by - u * 6.5, bx - u * 0.8, by - u * 5.8, bx - u * 1.6, by - u * 4.3);
    q.closePath();
  }, PAL.white, 1.3);

  /* 4. Wing: curved back contour with tiered lapis, malachite, and black feathers */
  /* Primary flight feathers (black) */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(bx + u * 0.9, by - u * 6.1);
    q.bezierCurveTo(bx + u * 1.3, by - u * 5.2, bx + u * 0.5, by - u * 4.2, bx - u * 1.4, by - u * 4.2);
    q.lineTo(bx - u * 2.6, by - u * 4.4);
    q.bezierCurveTo(bx - u * 2.2, by - u * 5.3, bx - u * 1.2, by - u * 5.8, bx + u * 0.9, by - u * 6.1);
    q.closePath();
  }, PAL.black, 1.2);

  /* Secondary coverts (lapis blue) */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(bx + u * 0.7, by - u * 5.9);
    q.bezierCurveTo(bx + u * 1.0, by - u * 5.1, bx + u * 0.3, by - u * 4.4, bx - u * 1.1, by - u * 4.4);
    q.lineTo(bx - u * 2.1, by - u * 4.7);
    q.bezierCurveTo(bx - u * 1.7, by - u * 5.4, bx - u * 0.9, by - u * 5.7, bx + u * 0.7, by - u * 5.9);
    q.closePath();
  }, PAL.lapis, 1.3);

  /* Greater coverts band (malachite green) */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(bx + u * 0.5, by - u * 5.7);
    q.bezierCurveTo(bx + u * 0.8, by - u * 5.0, bx + u * 0.2, by - u * 4.6, bx - u * 0.8, by - u * 4.6);
    q.lineTo(bx - u * 1.5, by - u * 4.9);
    q.bezierCurveTo(bx - u * 1.1, by - u * 5.3, bx - u * 0.5, by - u * 5.5, bx + u * 0.5, by - u * 5.7);
    q.closePath();
  }, PAL.malachite, 1.4);

  /* Scalloped feather crescents in yellow ochre */
  c.strokeStyle = PAL.ochre; c.lineWidth = u * 0.08;
  for (var k = 0; k < 4; k++) {
    c.beginPath();
    c.arc(bx - u * 0.4 + k * u * 0.38, by - u * 5.1, u * 0.42, 0.4, 2.2, false);
    c.stroke();
  }

  /* 5. Neck: long, elegant S-curve up from breast, deep lapis-tinted black */
  paper(c, function (q) {
    q.beginPath();
    q.moveTo(bx + u * 0.8, by - u * 6.1);
    q.bezierCurveTo(bx + u * 1.9, by - u * 6.6, bx + u * 2.3, by - u * 7.5, bx + u * 1.9, by - u * 8.6);
    q.lineTo(bx + u * 1.2, by - u * 8.5);
    q.bezierCurveTo(bx + u * 1.6, by - u * 7.6, bx + u * 1.3, by - u * 6.8, bx + u * 0.2, by - u * 6.3);
    q.closePath();
  }, PAL.lapisDeep, 1.4);

  /* 6. Head: sleek oval held high */
  var hx = bx + u * 1.7, hy = by - u * 8.7;
  paper(c, ell(hx, hy, u * 0.65, u * 0.54, 0.1), PAL.lapisDeep, 1.4);

  /* Eye: golden yellow with black pupil & Egyptian cosmetic kohl line */
  paper(c, ell(hx + u * 0.15, hy - u * 0.08, u * 0.18, u * 0.14), PAL.gold, 1.5);
  c.fillStyle = PAL.black;
  c.beginPath();
  c.arc(hx + u * 0.18, hy - u * 0.08, u * 0.08, 0, TAU);
  c.fill();
  c.strokeStyle = PAL.black; c.lineWidth = u * 0.06;
  c.beginPath();
  c.moveTo(hx + u * 0.28, hy - u * 0.08);
  c.lineTo(hx + u * 0.52, hy - u * 0.05);
  c.stroke();

  /* 7. Red throat wattle beneath the chin */
  paper(c, poly([
    [hx + u * 0.12, hy + u * 0.42],
    [hx + u * 0.26, hy + u * 0.88],
    [hx + u * 0.06, hy + u * 0.96],
    [hx - u * 0.04, hy + u * 0.46]
  ]), PAL.redBright, 1.3);

  /* 8. The Massive Tricolor Bill:
     Base = red, Middle = black, Tip = red.
     Curving culmen and wedge profile */
  var tx = hx + u * 3.4, ty = hy + u * 0.48;

  /* Slanted segment boundaries */
  var x1Top = hx + u * 1.3, x1Bot = hx + u * 1.15;
  var x2Top = hx + u * 2.3, x2Bot = hx + u * 2.15;

  /* Base third: red */
  paper(c, poly([
    [hx + u * 0.4, hy - u * 0.24],
    [x1Top, lerp(hy - u * 0.24, ty, 0.35)],
    [x1Bot, lerp(hy + u * 0.38, ty + u * 0.22, 0.35)],
    [hx + u * 0.35, hy + u * 0.38]
  ]), PAL.red, 1.4);

  /* Middle third: carbon black band */
  paper(c, poly([
    [x1Top, lerp(hy - u * 0.24, ty, 0.35)],
    [x2Top, lerp(hy - u * 0.24, ty, 0.68)],
    [x2Bot, lerp(hy + u * 0.38, ty + u * 0.22, 0.68)],
    [x1Bot, lerp(hy + u * 0.38, ty + u * 0.22, 0.35)]
  ]), PAL.black, 1.4);

  /* Tip third: red */
  paper(c, poly([
    [x2Top, lerp(hy - u * 0.24, ty, 0.68)],
    [tx, ty],
    [tx - u * 0.2, ty + u * 0.22],
    [x2Bot, lerp(hy + u * 0.38, ty + u * 0.22, 0.68)]
  ]), PAL.red, 1.4);

  /* Central bill cutting line */
  c.strokeStyle = 'rgba(0,0,0,0.35)'; c.lineWidth = u * 0.05;
  c.beginPath();
  c.moveTo(hx + u * 0.4, hy + u * 0.12);
  c.lineTo(tx - u * 0.1, ty + u * 0.15);
  c.stroke();

  /* 9. The Frontal Saddle (shield):
     Golden-yellow frontal plate on top of upper bill at base */
  paper(c, poly([
    [hx + u * 0.25, hy - u * 0.32],
    [hx + u * 0.9, hy - u * 0.36],
    [hx + u * 1.35, hy - u * 0.14],
    [hx + u * 0.65, hy - u * 0.05],
    [hx + u * 0.25, hy - u * 0.1]
  ]), PAL.gold, 1.6);
}

/* Vertical Papyrus Column separating frieze panels */
function papyrusColumn(c, x, yTop, yBase, s) {
  var colW = s * 0.24;
  /* column shaft with vertical reed flutes */
  paper(c, rect(x - colW * 0.5, yTop + s * 0.6, colW, yBase - yTop - s * 0.6), PAL.ochre, 1.1);
  c.strokeStyle = 'rgba(0,0,0,0.18)'; c.lineWidth = 1.2;
  [-0.25, 0, 0.25].forEach(function (off) {
    c.beginPath();
    c.moveTo(x + colW * off, yTop + s * 0.6);
    c.lineTo(x + colW * off, yBase - s * 0.14);
    c.stroke();
  });

  /* reed binding ties */
  [0.2, 0.4, 0.6, 0.8].forEach(function (frac) {
    var yy = lerp(yTop + s * 0.6, yBase, frac);
    paper(c, rect(x - colW * 0.55, yy, colW * 1.1, s * 0.06), PAL.red, 1.2);
  });
  /* papyrus campaniform capital */
  paper(c, poly([
    [x - colW * 0.5, yTop + s * 0.6],
    [x - colW * 1.25, yTop + s * 0.15],
    [x + colW * 1.25, yTop + s * 0.15],
    [x + colW * 0.5, yTop + s * 0.6]
  ]), PAL.malachite, 1.3);
  /* abacus block at top */
  paper(c, rect(x - colW * 1.35, yTop, colW * 2.7, s * 0.15), PAL.lapis, 1.3);
  /* base plinth */
  paper(c, rect(x - colW * 1.15, yBase - s * 0.14, colW * 2.3, s * 0.14), PAL.stoneDark, 1.2);
}

/* Upper / Lower Egyptian Block Frieze band */
function blockFrieze(c, x0, x1, y, h) {
  var blockW = h * 0.72;
  var colors = [PAL.red, PAL.lapis, PAL.malachite, PAL.ochre];
  var startK = Math.floor(x0 / blockW);
  var endK = Math.ceil(x1 / blockW);

  /* Torus roll cord above and below */
  paper(c, rect(x0, y, x1 - x0, h * 0.12), PAL.ochre, 1.1);
  paper(c, rect(x0, y + h * 0.88, x1 - x0, h * 0.12), PAL.ochre, 1.1);

  /* repeating colored blocks */
  for (var k = startK; k <= endK; k++) {
    var bx = k * blockW;
    var col = colors[((k % 4) + 4) % 4];
    paper(c, rect(bx + blockW * 0.08, y + h * 0.14, blockW * 0.84, h * 0.72), col, 1.2);
    /* white and black separator pinstripes */
    paper(c, rect(bx + blockW * 0.94, y + h * 0.14, blockW * 0.06, h * 0.72), PAL.white, 1.1);
    paper(c, rect(bx + blockW * 0.02, y + h * 0.14, blockW * 0.06, h * 0.72), PAL.black, 1.1);
  }
}

/* Dado Lotus Band (connected alternating open lotus blooms and closed buds) */
function dadoLotusBand(c, x0, x1, y, h) {
  var step = h * 0.85;
  var startK = Math.floor(x0 / step);
  var endK = Math.ceil(x1 / step);

  /* Lower limestone backing */
  paper(c, rect(x0, y, x1 - x0, h), PAL.stoneDark, 1.0);

  /* Horizontal stem line */
  c.strokeStyle = PAL.malachiteDeep; c.lineWidth = h * 0.06;
  c.beginPath();
  c.moveTo(x0, y + h * 0.75);
  c.lineTo(x1, y + h * 0.75);
  c.stroke();

  for (var k = startK; k <= endK; k++) {
    var lx = k * step;
    var isBloom = (k % 2 === 0);
    if (isBloom) {
      /* Open lotus bloom */
      paper(c, poly([
        [lx, y + h * 0.15],
        [lx + step * 0.25, y + h * 0.45],
        [lx + step * 0.12, y + h * 0.72],
        [lx - step * 0.12, y + h * 0.72],
        [lx - step * 0.25, y + h * 0.45]
      ]), PAL.lapisBright, 1.2);
      paper(c, poly([
        [lx, y + h * 0.2],
        [lx + step * 0.12, y + h * 0.5],
        [lx, y + h * 0.72],
        [lx - step * 0.12, y + h * 0.5]
      ]), PAL.white, 1.3);
      paper(c, poly([
        [lx - step * 0.14, y + h * 0.65],
        [lx + step * 0.14, y + h * 0.65],
        [lx + step * 0.08, y + h * 0.75],
        [lx - step * 0.08, y + h * 0.75]
      ]), PAL.red, 1.2);
    } else {
      /* Closed lotus bud */
      paper(c, poly([
        [lx, y + h * 0.28],
        [lx + step * 0.14, y + h * 0.55],
        [lx, y + h * 0.72],
        [lx - step * 0.14, y + h * 0.55]
      ]), PAL.malachite, 1.2);
      paper(c, poly([
        [lx, y + h * 0.34],
        [lx + step * 0.07, y + h * 0.54],
        [lx, y + h * 0.7],
        [lx - step * 0.07, y + h * 0.54]
      ]), PAL.white, 1.3);
    }
  }
}

/* Master Draw Routine */
function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t;
  var T = 12000; /* 12 s loop period */

  /* Dimensions */
  var ySky = H * 0.07;
  var yFriezeTop = H * 0.155;
  var yBase = H * 0.81;
  var yFriezeBot = H * 0.895;

  /* 1. Paint Limestone Wall Background */
  var grad = c.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, '#f2ece0');
  grad.addColorStop(0.5, '#ede3d0');
  grad.addColorStop(1, '#e3d7c1');
  c.fillStyle = grad;
  c.fillRect(0, 0, W, H);

  /* 2. Horizontal Scroll Math:
     Cycle through 3 distinct metope units.
     Unit width U = H * 0.76.
     In 12 seconds, scroll exactly 3 units so the loop closes cleanly. */
  var U = H * 0.76;
  var totalDistance = 3 * U;
  var p = (t % T) / T;
  var scrollOffset = p * totalDistance;

  /* Ashlar stone block seams (scrolling with the wall) */
  c.strokeStyle = PAL.stoneJoint; c.lineWidth = 2;
  c.beginPath();
  c.moveTo(0, H * 0.36); c.lineTo(W, H * 0.36);
  c.moveTo(0, H * 0.58); c.lineTo(W, H * 0.58);
  c.stroke();

  var blockSeamStep = U * 0.5;
  var seamStart = Math.floor((scrollOffset - U) / blockSeamStep);
  var seamEnd = Math.ceil((scrollOffset + W + U) / blockSeamStep);
  for (var sIdx = seamStart; sIdx <= seamEnd; sIdx++) {
    var sx = sIdx * blockSeamStep - scrollOffset;
    var y0 = (sIdx % 2 === 0) ? yFriezeTop : H * 0.36;
    var y1 = (sIdx % 2 === 0) ? H * 0.58 : yBase;
    c.beginPath(); c.moveTo(sx, y0); c.lineTo(sx, y1); c.stroke();
  }

  /* 3. Render Visible Metope Units */
  var kStart = Math.floor((scrollOffset - U) / U);
  var kEnd = Math.ceil((scrollOffset + W + U) / U);

  for (var k = kStart; k <= kEnd; k++) {
    var unitX = k * U - scrollOffset;
    var variant = ((k % 3) + 3) % 3;

    /* A. Papyrus column divider at the left edge of each unit */
    papyrusColumn(c, unitX + U * 0.05, yFriezeTop, yBase, H * 0.16);

    /* B. Hieroglyph Column (flanked by red painter guide lines) */
    var colX = unitX + U * 0.19;
    c.strokeStyle = 'rgba(171, 50, 34, 0.35)'; c.lineWidth = 1.5;
    c.beginPath();
    c.moveTo(colX - U * 0.08, yFriezeTop + H * 0.03);
    c.lineTo(colX - U * 0.08, yBase - H * 0.02);
    c.moveTo(colX + U * 0.08, yFriezeTop + H * 0.03);
    c.lineTo(colX + U * 0.08, yBase - H * 0.02);
    c.stroke();

    var gSize = H * 0.09;
    if (variant === 0) {
      /* Variant 0: Sun, Ankh, Djed, Was, Shen */
      sun(c, colX, yFriezeTop + H * 0.08, gSize * 0.38);
      ankh(c, colX, yFriezeTop + H * 0.20, gSize * 0.95);
      djed(c, colX, yFriezeTop + H * 0.34, gSize * 0.95);
      was(c, colX, yFriezeTop + H * 0.48, gSize * 0.95);
      shen(c, colX, yFriezeTop + H * 0.60, gSize * 0.9);
    } else if (variant === 1) {
      /* Variant 1: Wedjat (Eye of Horus), Was scepter, Water ripple, Ankh, Shen */
      wedjat(c, colX, yFriezeTop + H * 0.08, gSize * 1.05);
      was(c, colX, yFriezeTop + H * 0.22, gSize * 1.0);
      water(c, colX, yFriezeTop + H * 0.35, U * 0.13, gSize * 0.7);
      ankh(c, colX, yFriezeTop + H * 0.48, gSize * 0.95);
      shen(c, colX, yFriezeTop + H * 0.60, gSize * 0.9);
    } else {
      /* Variant 2: Lotus, Ankh, Djed, Water, Was */
      lotus(c, colX, yFriezeTop + H * 0.08, gSize * 0.9);
      ankh(c, colX, yFriezeTop + H * 0.22, gSize * 0.95);
      djed(c, colX, yFriezeTop + H * 0.35, gSize * 0.95);
      water(c, colX, yFriezeTop + H * 0.48, U * 0.13, gSize * 0.7);
      was(c, colX, yFriezeTop + H * 0.60, gSize * 0.95);
    }

    /* C. The Majestic Saddle-Billed Stork Sign (Gardiner G29, the 'ba') */
    var storkX = unitX + U * 0.58;
    var storkScale = H * 0.052;
    storkSign(c, storkX, yBase, storkScale);

    /* D. Inscription for 'ba' placed in front of the stork's chest and legs */
    var baX = storkX + storkScale * 1.9;
    foot(c, baX, yBase - H * 0.16, H * 0.08);
    brazier(c, baX, yBase - H * 0.065, H * 0.07);
  }

  /* 4. Ground Baseline */
  paper(c, rect(0, yBase, W, H * 0.012), PAL.black, 1.4);
  paper(c, rect(0, yBase + H * 0.012, W, H * 0.01), PAL.red, 1.2);

  /* 5. Lower Egyptian Block Frieze & Dado Lotus Band */
  blockFrieze(c, 0, W, yBase + H * 0.024, H * 0.06);
  dadoLotusBand(c, 0, W, yFriezeBot, H - yFriezeBot);

  /* 6. Upper Celestial Sky (*Pet*) Bar with Gold Stars */
  paper(c, rect(0, 0, W, ySky), PAL.lapisDeep, 1.2);
  var starDist = H * 0.08;
  for (var stx = starDist * 0.5; stx < W + starDist; stx += starDist) {
    paper(c, star(stx, ySky * 0.5, H * 0.018, H * 0.008, 5), PAL.gold, 1.4);
  }

  /* 7. Upper Egyptian Block Frieze */
  blockFrieze(c, 0, W, ySky, yFriezeTop - ySky);

  /* Subtle raking sunlight across the limestone wall */
  var raking = c.createLinearGradient(0, 0, W, 0);
  raking.addColorStop(0, 'rgba(255,255,255,0.08)');
  raking.addColorStop(0.5, 'rgba(0,0,0,0.0)');
  raking.addColorStop(1, 'rgba(40,25,10,0.06)');
  c.fillStyle = raking;
  c.fillRect(0, yFriezeTop, W, yBase - yFriezeTop);
}

D.addScene('stork-frieze', draw, null, 'x(t) = (x₀ − v·t) mod 3U (scrolling temple frieze)');
})();

/* ---- stork-popup ---- */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, ease = K.ease, TAU = K.TAU;

function ell(x, y, rx, ry, rot) { return function (q) { q.beginPath(); q.ellipse(x, y, rx, ry, rot || 0, 0, TAU); }; }
function band(x0, y0, cx, cy, x1, y1, w0, w1) {
  var L = [], R = [];
  for (var i = 0; i <= 12; i++) {
    var u = i / 12, a = 1 - u;
    var x = a * a * x0 + 2 * a * u * cx + u * u * x1, y = a * a * y0 + 2 * a * u * cy + u * u * y1;
    var dx = 2 * a * (cx - x0) + 2 * u * (x1 - cx), dy = 2 * a * (cy - y0) + 2 * u * (y1 - cy), n = Math.hypot(dx, dy) || 1, w = lerp(w0, w1, u) / 2;
    L.push([x - dy / n * w, y + dx / n * w]); R.unshift([x + dy / n * w, y - dx / n * w]);
  }
  return poly(L.concat(R));
}

function whiteStork(c, x, y, s, clap, t, alpha) {
  if (alpha <= 0) return;
  c.globalAlpha = alpha;
  var white = '#f4f4f4', black = '#1a1a1a', red = '#c83727';
  c.lineCap = 'round';
  
  /* legs */
  c.strokeStyle = red; c.lineWidth = s * 0.18;
  [[-s*0.3, 0], [s * 0.3, 0]].forEach(function(L, i) {
    var ox = L[0], oy = L[1];
    var step = Math.max(0, Math.sin(t/150 + i * Math.PI)) * s * 0.6; 
    var lx = x + ox + step * 0.5, ly = y - step;
    c.beginPath(); 
    c.moveTo(lx, ly); 
    c.lineTo(x + ox + s*0.2, y - s * 2.0); 
    c.lineTo(x + ox + s*0.4, y - s * 3.5); 
    c.stroke();
    /* feet */
    c.beginPath();
    c.moveTo(lx, ly);
    c.lineTo(lx + s*0.6, ly);
    c.stroke();
  });

  /* flight feathers (black tail/wing back) */
  paper(c, poly([[x - s*1.8, y - s*4.2], [x - s*3.4, y - s*3.3], [x - s*1.6, y - s*2.7]]), black, 1.5);
  
  /* body */
  paper(c, ell(x, y - s * 4.0, s * 2.1, s * 1.3, -0.15), white, 1.5);
  
  /* neck */
  paper(c, band(x + s*1.2, y - s*4.4, x + s*0.8, y - s*6.0, x + s*1.6, y - s*7.4, s*1.0, s*0.6), white, 1.2);
  
  /* head */
  paper(c, ell(x + s*1.8, y - s*7.5, s*0.7, s*0.6, 0), white, 1.2);
  c.fillStyle = '#000'; c.beginPath(); c.arc(x + s*2.0, y - s*7.6, s*0.09, 0, TAU); c.fill();
  
  /* bill */
  var gap = clap * s * 0.4;
  var bx = x + s*2.4, by = y - s*7.4;
  var tx = x + s*4.8, ty = y - s*7.1;
  /* upper */
  paper(c, poly([[bx, by - s*0.3], [tx, ty - gap/2], [bx, by]]), red, 1);
  /* lower */
  paper(c, poly([[bx, by], [tx, ty + gap/2], [bx, by + s*0.3]]), red, 1);
  c.globalAlpha = 1;
}

function drawSliderBase(c, x, y, s, w) {
  var bh = s * 0.2;
  paper(c, poly([
    [x - w, y], [x + w, y], 
    [x + w - s*0.2, y + bh], [x - w + s*0.2, y + bh]
  ]), '#8c7762', 1);
}

function princessWithMirror(c, x, y, s, alpha) {
  if (alpha <= 0) return;
  c.globalAlpha = alpha;
  
  drawSliderBase(c, x, y, s, s*2.2);

  /* gown */
  paper(c, function(q) {
    q.beginPath();
    q.moveTo(x - s*0.5, y - s*4.5);
    q.bezierCurveTo(x - s*3, y - s*0.5, x - s*3.5, y, x - s*2, y);
    q.lineTo(x + s*2, y);
    q.bezierCurveTo(x + s*3.5, y, x + s*3, y - s*0.5, x + s*0.5, y - s*4.5);
  }, '#c68453', 1.5);
  
  /* sash */
  paper(c, poly([[x - s*0.6, y - s*4.5], [x + s*0.6, y - s*4.5], [x + s*0.7, y - s*4.0], [x - s*0.7, y - s*4.0]]), '#cfb352', 1);
  
  /* torso */
  paper(c, poly([[x - s*0.6, y - s*4.5], [x + s*0.6, y - s*4.5], [x + s*0.8, y - s*6.5], [x - s*0.8, y - s*6.5]]), '#e8d2c1', 1);
  
  /* right arm holding mirror */
  paper(c, band(x + s*0.7, y - s*6.0, x + s*2.5, y - s*6.0, x + s*2.0, y - s*7.5, s*0.8, s*0.5), '#e8d2c1', 1);
  paper(c, poly([[x + s*1.8, y - s*6.6], [x + s*2.4, y - s*7.2], [x + s*2.2, y - s*7.4], [x + s*1.6, y - s*6.8]]), '#8c6239', 1);
  paper(c, ell(x + s*2.4, y - s*7.7, s*0.6, s*0.8, 0.3), '#d4af37', 1);
  paper(c, ell(x + s*2.4, y - s*7.7, s*0.4, s*0.6, 0.3), '#e0f7fa', 1);
  
  /* left arm */
  paper(c, band(x - s*0.7, y - s*6.0, x - s*1.5, y - s*5.0, x - s*1.0, y - s*3.5, s*0.8, s*0.5), '#e8d2c1', 1);

  /* hair back */
  paper(c, ell(x, y - s*7.5, s*1.2, s*1.5, 0), '#3a2d28', 1);
  
  /* head */
  paper(c, ell(x, y - s*7.2, s*0.6, s*0.8, 0), '#f4d0b5', 1);
  
  /* crown */
  paper(c, poly([
    [x - s*0.6, y - s*7.8], [x + s*0.6, y - s*7.8], 
    [x + s*0.8, y - s*9.2], [x + s*0.4, y - s*8.5], 
    [x, y - s*9.3], 
    [x - s*0.4, y - s*8.5], [x - s*0.8, y - s*9.2]
  ]), '#d4af37', 1);
  c.globalAlpha = 1;
}

function trojanBackdrop(c, W, H) {
  paper(c, function(q){
    q.beginPath(); 
    q.moveTo(0, H*0.82);
    q.lineTo(0, H*0.3);
    q.lineTo(W*0.3, H*0.3); q.lineTo(W*0.3, H*0.2); q.lineTo(W*0.4, H*0.2); q.lineTo(W*0.4, H*0.3);
    q.lineTo(W*0.6, H*0.3); q.lineTo(W*0.6, H*0.15); q.lineTo(W*0.7, H*0.15); q.lineTo(W*0.7, H*0.3);
    q.lineTo(W, H*0.3);
    q.lineTo(W, H*0.82);
  }, '#c2b591', 1.5);
  
  paper(c, function(q){
    q.beginPath(); 
    q.moveTo(0, H*0.82);
    q.lineTo(0, H*0.4); 
    q.lineTo(W*0.15, H*0.4); q.lineTo(W*0.15, H*0.25); q.lineTo(W*0.25, H*0.25); q.lineTo(W*0.25, H*0.4);
    q.lineTo(W*0.75, H*0.4); 
    q.lineTo(W*0.75, H*0.25); q.lineTo(W*0.85, H*0.25); q.lineTo(W*0.85, H*0.4);
    q.lineTo(W, H*0.4);
    q.lineTo(W, H*0.82);
  }, '#d9cca6', 2);
  
  paper(c, function(q){
    q.beginPath();
    for (var x = W*0.25; x <= W*0.7; x += W*0.05) {
      q.moveTo(x, H*0.4); q.lineTo(x, H*0.35); q.lineTo(x + W*0.025, H*0.35); q.lineTo(x + W*0.025, H*0.4);
    }
  }, '#d9cca6', 2);

  c.fillStyle = '#a69975';
  c.beginPath(); c.arc(W*0.25, H*0.82, W*0.06, Math.PI, 0); c.fill();
  c.beginPath(); c.arc(W*0.75, H*0.82, W*0.06, Math.PI, 0); c.fill();
  c.fillRect(W*0.18, H*0.3, W*0.04, H*0.08);
  c.fillRect(W*0.78, H*0.3, W*0.04, H*0.08);
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t % 12000;
  var s = H * 0.055;
  var cx = W / 2, cy = H * 0.82;
  
  /* Paper theatre background */
  c.fillStyle = '#f4ecd8'; c.fillRect(0, 0, W, H);
  
  /* Backdrop (Trojan walls) slides in 0-2s */
  var bgP = Math.min(1, Math.max(0, t / 2000));
  var bgSlide = ease(bgP);
  var bgX = (bgSlide - 1) * W;
  
  c.save();
  c.translate(bgX, 0);
  trojanBackdrop(c, W, H);
  c.restore();

  /* Stage floor */
  paper(c, poly([[0, cy], [W, cy], [W, H], [0, H]]), '#9c7b60', 2);
  
  /* Grooves on floor */
  c.strokeStyle = '#634b35'; c.lineWidth = H*0.005;
  [0.85, 0.89, 0.93].forEach(function(gy) {
    c.beginPath(); c.moveTo(0, H*gy); c.lineTo(W, H*gy); c.stroke();
  });

  /* Princess slides in 2-5s */
  var prP = Math.min(1, Math.max(0, (t - 2000) / 1500));
  var prSlide = ease(prP);
  var prX = W * 0.85 - W * 0.35 * prSlide;
  
  if (t < 6000) {
    c.save();
    c.translate(prX - cx, 0);
    princessWithMirror(c, cx, cy, s, 1);
    c.restore();
  }

  /* Flash 5-6s */
  if (t > 5000 && t < 6000) {
    var flPIn = Math.min(1, (t - 5000) / 200);
    var flPOut = Math.max(0, (t - 5800) / 200);
    var flX = W*0.85 - W*0.35 * ease(flPIn) + W*0.5 * ease(flPOut); 
    
    c.save();
    c.translate(flX - cx, 0);
    paper(c, poly([[cx - s*0.5, cy], [cx + s, cy], [cx, cy - s*2], [cx + s*1.5, cy - s*3], [cx - s*0.5, cy - s*8], [cx - s*1.5, cy - s*2.5], [cx - s*0.5, cy - s*1.5]]), '#ffea00', 1.5);
    drawSliderBase(c, cx, cy, s, s*1.5);
    c.restore();
  }

  /* Stork (6-12s) */
  if (t >= 6000) {
    var clap = Math.max(0, Math.sin(t / 40)); 
    drawSliderBase(c, cx, cy, s, s*2.2);
    whiteStork(c, cx, cy, s, clap, 0, 1); // t=0 so it stands still
  }

  /* Feathers (6-8s) */
  if (t >= 6000 && t < 8000) {
    var fP = (t - 6000) / 2000;
    var r = K.rnd(42);
    for (var i = 0; i < 80; i++) {
      var ox = (r() - 0.5) * s * 6;
      var oy = -r() * s * 8; 
      var speedX = (r() - 0.5) * W * 0.4;
      var speedY = (r() - 0.2) * H * 0.4;
      var fx = cx + ox + speedX * fP;
      var fy = cy + oy + speedY * fP + fP * fP * H * 0.4;
      var fAlpha = 1 - fP;
      if (fAlpha > 0 && fy < cy + s) {
        c.globalAlpha = fAlpha;
        paper(c, ell(fx, fy, s*0.4, s*0.15, r()*TAU + t/200), '#fff', 1);
      }
    }
    c.globalAlpha = 1;
  }

  /* Curtains part 0-2s */
  var curP = Math.min(1, Math.max(0, t / 2000));
  var curSlide = ease(curP);
  
  var lcW = W * 0.5 * (1 - curSlide);
  if (lcW > 0) {
    paper(c, poly([[0, 0], [lcW, 0], [lcW, cy], [0, cy]]), '#b83b3b', 2);
    paper(c, poly([[lcW - s*0.2, 0], [lcW, 0], [lcW, cy], [lcW - s*0.2, cy]]), '#d4af37', 1);
  }
  var rcW = W * 0.5 * (1 - curSlide);
  if (rcW > 0) {
    paper(c, poly([[W, 0], [W - rcW, 0], [W - rcW, cy], [W, cy]]), '#b83b3b', 2);
    paper(c, poly([[W - rcW, 0], [W - rcW + s*0.2, 0], [W - rcW + s*0.2, cy], [W - rcW, cy]]), '#d4af37', 1);
  }

  /* Proscenium arch */
  paper(c, poly([[0, 0], [W*0.1, 0], [W*0.1, H], [0, H]]), '#5a1f1f', 2);
  paper(c, poly([[W*0.9, 0], [W, 0], [W, H], [W*0.9, H]]), '#5a1f1f', 2);
  paper(c, poly([[0, 0], [W, 0], [W, H*0.15], [0, H*0.15]]), '#7a2929', 2);
  for (var i = 0; i < 10; i++) {
    paper(c, ell(W * (i+0.5)/10, H*0.15, W*0.06, H*0.04, 0), '#7a2929', 2);
    paper(c, ell(W * (i+0.5)/10, H*0.12, s*0.15, s*0.15, 0), '#d4af37', 1);
  }
}
D.addScene('stork-popup', draw, null, 'feathers out (the princess breaks), stork steps out');
})();

/* ---- stork-rooftops ---- */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var K = D.kit, paper = K.paper, poly = K.poly, lerp = K.lerp, TAU = K.TAU;

function ell(x, y, rx, ry, rot) { return function (q) { q.beginPath(); q.ellipse(x, y, rx, ry, rot || 0, 0, TAU); }; }

function band(x0, y0, cx, cy, x1, y1, w0, w1) {
  var L = [], R = [];
  for (var i = 0; i <= 12; i++) {
    var u = i / 12, a = 1 - u;
    var x = a * a * x0 + 2 * a * u * cx + u * u * x1, y = a * a * y0 + 2 * a * u * cy + u * u * y1;
    var dx = 2 * a * (cx - x0) + 2 * u * (x1 - cx), dy = 2 * a * (cy - y0) + 2 * u * (y1 - cy), n = Math.hypot(dx, dy) || 1, w = lerp(w0, w1, u) / 2;
    L.push([x - dy / n * w, y + dx / n * w]); R.unshift([x + dy / n * w, y - dx / n * w]);
  }
  return poly(L.concat(R));
}

function whiteStork(c, x, fy, u, head, night) {
  var white = night ? '#dcdadd' : '#ffffff', black = night ? '#1a1a1c' : '#222222', leg = night ? '#9a3333' : '#d24040', billCol = night ? '#a84040' : '#e65050';
  c.lineCap = 'round';
  // legs
  c.strokeStyle = leg; c.lineWidth = u * 0.16;
  [[-0.25, 0.1], [0.3, -0.12]].forEach(function (L) {
    c.beginPath(); c.moveTo(x + L[0] * u, fy); c.lineTo(x + (L[0] + L[1]) * u, fy - 1.7 * u); c.lineTo(x + L[0] * 0.5 * u, fy - 3.1 * u); c.stroke();
    c.beginPath(); c.moveTo(x + L[0] * u - 0.4 * u, fy); c.lineTo(x + L[0] * u + 0.45 * u, fy); c.stroke();
  });
  // body
  paper(c, poly([[x - 1.0 * u, fy - 4.3 * u], [x - 2.8 * u, fy - 3.3 * u], [x - 2.5 * u, fy - 2.8 * u], [x - 1.2 * u, fy - 3.2 * u]]), black, 1);
  paper(c, ell(x, fy - 4 * u, 1.9 * u, 1.1 * u, -0.12), white, 1.4);
  paper(c, ell(x - 0.45 * u, fy - 3.85 * u, 1.75 * u, 0.7 * u, -0.05), black, 1);
  // neck and head
  var hx = lerp(x + 1.75 * u, x - 0.2 * u, head), hy = lerp(fy - 7.1 * u, fy - 5.1 * u, head), dir = head > 0.5 ? -1 : 1;
  paper(c, band(x + 1.2 * u, fy - 4.5 * u, lerp(x + 2.1 * u, x + 1.2 * u, head), lerp(fy - 5.6 * u, fy - 6.2 * u, head), hx, hy + 0.2 * u, 0.8 * u, 0.5 * u), white, 1.2);
  paper(c, ell(hx, hy, 0.55 * u, 0.45 * u), white, 1.2);
  // bill (straight, closed)
  var bx = hx + dir * 0.3 * u, by = hy + 0.05 * u, tx = hx + dir * 3.0 * u, ty = hy + (head > 0.5 ? 1.4 : 1.1) * u;
  paper(c, poly([[bx, by - 0.15 * u], [tx, ty], [bx, by + 0.15 * u]]), billCol, 1);
  c.fillStyle = '#111'; c.beginPath(); c.arc(hx + dir * 0.15 * u, hy - 0.08 * u, 0.09 * u, 0, TAU); c.fill();
}

function flyingStork(c, x, y, u, phase, night) {
  var white = night ? '#dcdadd' : '#ffffff', black = night ? '#1a1a1c' : '#222222', leg = night ? '#9a3333' : '#d24040', billCol = night ? '#a84040' : '#e65050';
  var flap = Math.sin(phase * TAU);
  var fflap = Math.max(0, flap);
  var dflap = Math.min(0, flap);
  
  // far wing
  paper(c, poly([[x + 1 * u, y - u * 0.2], [x - 1 * u + flap * 1 * u, y - 2.5 * u * flap], [x - 3 * u + flap * 1.5 * u, y - 3 * u * flap], [x - 1 * u, y - u * 0.2]]), black, 1);
  paper(c, poly([[x + 1 * u, y - u * 0.2], [x + flap * 1 * u, y - 1 * u * flap], [x - 1.5 * u + flap * 0.5 * u, y - 1.5 * u * flap], [x - 0.5 * u, y - u * 0.2]]), white, 1);
  
  // legs
  c.strokeStyle = leg; c.lineWidth = u * 0.16;
  c.beginPath(); c.moveTo(x - u, y + u * 0.1); c.lineTo(x - 3.5 * u, y - u * 0.2); c.stroke();
  c.beginPath(); c.moveTo(x - u, y + u * 0.2); c.lineTo(x - 3.5 * u, y - u * 0.1); c.stroke();
  
  // body
  paper(c, ell(x, y, 2.2 * u, 0.9 * u, 0), white, 1.4);
  
  // near wing
  paper(c, poly([[x + 1 * u, y + u * 0.2], [x - 1 * u - flap * 1 * u, y + 3 * u * flap], [x - 3.5 * u - flap * 1.5 * u, y + 3.5 * u * flap], [x - 1 * u, y + u * 0.2]]), black, 1);
  paper(c, poly([[x + 1 * u, y + u * 0.2], [x - flap * 1 * u, y + 1.2 * u * flap], [x - 2 * u - flap * 0.5 * u, y + 1.5 * u * flap], [x - 0.5 * u, y + u * 0.2]]), white, 1);
  
  // neck and head
  paper(c, band(x + 1.4 * u, y - 0.1 * u, x + 2.8 * u, y + 0.2 * u, x + 4 * u, y, 0.8 * u, 0.45 * u), white, 1.2);
  paper(c, ell(x + 4.2 * u, y - 0.05 * u, 0.6 * u, 0.45 * u), white, 1);
  
  // bill
  paper(c, poly([[x + 4.5 * u, y - 0.2 * u], [x + 6.5 * u, y + 0.05 * u], [x + 4.5 * u, y + 0.1 * u]]), billCol, 1);
  c.fillStyle = '#111'; c.beginPath(); c.arc(x + 4.3 * u, y - 0.15 * u, 0.08 * u, 0, TAU); c.fill();
  
  // bundle
  var cloth = night ? '#d0d5e0' : '#ffffff';
  var bx = x + 5.5 * u, by = y + 0.05 * u;
  paper(c, ell(bx, by - 0.1 * u, 0.15 * u, 0.1 * u, 0), cloth, 1);
  paper(c, poly([[bx, by], [bx - 0.6 * u, by + 1.6 * u], [bx + 0.6 * u, by + 1.6 * u]]), cloth, 1);
  paper(c, ell(bx, by + 1.7 * u, 0.9 * u, 0.7 * u, 0), cloth, 1);
  
  // folds/strings
  c.strokeStyle = '#a8b0c0'; c.lineWidth = u*0.1;
  c.beginPath(); c.moveTo(bx, by); c.lineTo(bx, by + 1.8 * u); c.stroke();
  c.beginPath(); c.moveTo(bx, by); c.lineTo(bx - 0.3*u, by + 1.7 * u); c.stroke();
  c.beginPath(); c.moveTo(bx, by); c.lineTo(bx + 0.3*u, by + 1.7 * u); c.stroke();
  // string hanging from bill to knot
  c.beginPath(); c.moveTo(x + 5.5 * u, y + 0.05 * u); c.lineTo(bx, by - 0.1 * u); c.stroke();
}

function drawHouse(c, x, y, w, h, roofCol, wallCol, night, isStepped, r) {
  var wallH = h * 0.4;
  var roofH = h * 0.6;
  var rBase = y - wallH;
  
  // Wall
  paper(c, poly([[x - w/2, y], [x - w/2, rBase], [x + w/2, rBase], [x + w/2, y]]), wallCol, 1);
  
  // Windows
  var winW = w * 0.18, winH = wallH * 0.25;
  for (var wx = -1; wx <= 1; wx += 2) {
    for (var wy = 0.2; wy <= 0.7; wy += 0.45) {
      var isLit = r() > 0.4;
      var wCol = isLit ? (night ? '#ffd275' : '#ffeeaa') : (night ? '#3a3a40' : '#454550');
      var cx = x + wx * w * 0.22;
      var cy = y - wallH + wallH * wy;
      paper(c, poly([
        [cx - winW/2, cy - winH/2], [cx + winW/2, cy - winH/2],
        [cx + winW/2, cy + winH/2], [cx - winW/2, cy + winH/2]
      ]), wCol, 1);
      
      c.strokeStyle = isLit ? (night ? '#953' : '#a85') : (night ? '#222' : '#333'); 
      c.lineWidth = 1;
      c.beginPath(); c.moveTo(cx, cy - winH/2); c.lineTo(cx, cy + winH/2); c.stroke();
      c.beginPath(); c.moveTo(cx - winW/2, cy); c.lineTo(cx + winW/2, cy); c.stroke();
    }
  }

  // Roof / Gable
  if (isStepped) {
    var steps = 4;
    var pts = [];
    pts.push([x - w/2, rBase]);
    for(var i=0; i<steps; i++) {
      var sx1 = x - w/2 + (w/2) * (i/steps);
      var sy1 = rBase - roofH * (i/steps);
      var sx2 = x - w/2 + (w/2) * ((i+1)/steps);
      pts.push([sx1, sy1], [sx2, sy1]);
      if (i < steps - 1) pts.push([sx2, sy1 - roofH/steps]);
    }
    pts.push([x, rBase - roofH]);
    for(var i=steps-1; i>=0; i--) {
      var sx1 = x + w/2 - (w/2) * (i/steps);
      var sy1 = rBase - roofH * (i/steps);
      var sx2 = x + w/2 - (w/2) * ((i+1)/steps);
      if (i < steps - 1) pts.push([sx1, sy1 + roofH/steps]);
      pts.push([sx1, sy1], [sx2, sy1]);
    }
    pts.push([x + w/2, rBase]);
    paper(c, poly(pts), wallCol, 1);
  } else {
    paper(c, poly([[x - w/2 - w*0.05, rBase], [x, rBase - roofH], [x + w/2 + w*0.05, rBase]]), roofCol, 1);
    
    // scallops
    c.strokeStyle = 'rgba(0,0,0,0.5)'; c.lineWidth = 1.5;
    for (var ty = rBase - 5; ty > rBase - roofH + 10; ty -= 8) {
      var fw = w * (ty - (rBase - roofH)) / roofH + w*0.1;
      var startX = x - fw/2;
      c.beginPath();
      for(var sx = startX; sx < x + fw/2 - 4; sx += 8) {
        c.moveTo(sx, ty);
        c.quadraticCurveTo(sx + 4, ty + 4, sx + 8, ty);
      }
      c.stroke();
    }
  }
}

function draw(S) {
  var c = S.c, W = S.W, H = S.H, t = S.t, span = S.span;
  var r = K.rnd(S.seed);
  
  var roofCols = S.night ? ['#602520', '#703025', '#55221b', '#6b3630'] : ['#8c3525', '#702a1d', '#9c4535', '#a03b30'];
  // European dusk walls: ochre, terracotta, dull blue, slate, warm brown
  var wallCols = S.night ? ['#524636', '#4a3b3b', '#3a4a50', '#554433', '#403530', '#5a4a40', '#30404a'] : ['#a09070', '#b08a8a', '#809aa0', '#c09a70', '#a0857a', '#c0a080', '#7a9aa0'];
  var chimCol = S.night ? '#40302b' : '#a66b56';
  
  var baseY = H;
  var maxHouseH = H * 0.45;
  var numHouses = 8;
  var hW = span * 0.18;
  
  var nestChimneyX = 0;
  var nestChimneyY = 0;
  var nestHouseIdx = 4;
  
  // Draw all chimneys first so they sit behind the houses
  var houses = [];
  for (var i = 0; i < numHouses; i++) {
    var isStepped = r() > 0.4;
    var hH = maxHouseH * (0.65 + r() * 0.35);
    var hX = S.x0 + span * -0.05 + span * 1.1 * (i / (numHouses - 1));
    var rCol = roofCols[Math.floor(r() * roofCols.length)];
    var wCol = wallCols[Math.floor(r() * wallCols.length)];
    houses.push({x: hX, w: hW, h: hH, isStepped: isStepped, rCol: rCol, wCol: wCol});
    
    var roofTipY = baseY - hH;
    var chX = hX + hW * (r() > 0.5 ? 0.25 : -0.25);
    var chTop = roofTipY - hH * 0.15;
    var chBottom = baseY - hH * 0.4; // Base of the roof
    paper(c, poly([[chX - H * 0.02, chBottom], [chX + H * 0.02, chBottom], [chX + H * 0.02, chTop], [chX - H * 0.02, chTop]]), chimCol, 1);
    
    if (i === nestHouseIdx) {
      nestChimneyX = chX;
      nestChimneyY = chTop;
    }
  }
  
  // Now draw the houses
  for (var i = 0; i < numHouses; i++) {
    var h = houses[i];
    drawHouse(c, h.x, baseY, h.w, h.h, h.rCol, h.wCol, S.night, h.isStepped, r);
  }
  
  // Nest on chimney
  var nestCol = S.night ? '#2a221f' : '#4a3225';
  var nY = nestChimneyY - H * 0.01;
  
  var bu = H * 0.025;
  whiteStork(c, nestChimneyX, nY, bu, 0.5 + 0.5 * Math.sin(t / 2000), S.night);
  
  c.save(); c.beginPath(); c.ellipse(nestChimneyX, nY, H * 0.09, H * 0.03, 0, 0, TAU); c.clip();
  paper(c, ell(nestChimneyX, nY, H * 0.09, H * 0.03, 0), nestCol, 1);
  c.restore();
  
  c.strokeStyle = '#111'; c.lineWidth = 2;
  var sr = K.rnd(S.seed);
  for(var i=0; i<30; i++) {
    c.beginPath(); 
    var sx = nestChimneyX - H * 0.08 + sr()*H*0.16, sy = nY - H * 0.015 + sr()*H*0.03;
    c.moveTo(sx, sy); c.lineTo(sx + (sr()-0.5)*H*0.06, sy + (sr()-0.5)*H*0.02);
    c.stroke();
  }

  // flying stork with bundle
  var loopTime = 12000;
  var pt = (t % loopTime) / loopTime;
  var flyX = S.x0 - span * 0.2 + (span * 1.4) * pt;
  var flyY = H * 0.25 + Math.sin(t / 800) * H * 0.05;
  
  flyingStork(c, flyX, flyY, bu * 1.3, t / 400, S.night);
}

D.addScene('stork-rooftops', draw, null, 'x = t/12s (glide)');
})();

/* addScene() also appends to the band's rotation order, and the front page's daily pick is
   ORDER[(day·5 + i) mod ORDER.length]: twelve more names would reshuffle which doodle airs on
   which day. These scenes are for /doodles/ only, so they leave the order as they found it. */
(function () {
var D = window.MDDOODLER; if (!D || !D.order) return;
for (var i = D.order.length - 1; i >= 0; i--) if (/^stork-/.test(D.order[i])) D.order.splice(i, 1);
})();
