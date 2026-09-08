/* soi_run.js — the ant walks a soi that isn't there.
 *
 * This runs on 404.html and nowhere else. The address came up empty; the page
 * still has to be furniture for an arrival, so the strip at the top of the
 * card is a small side-scroller instead of a warning triangle: one ant, one
 * soi, obstacles a real soi actually has, and a jump.
 *
 * Rules it keeps, in the order they matter:
 *
 * 1. THE SEARCH BOX IS THE PAGE. Nothing here may steal a keystroke from it.
 *    Space and the arrows are only ours while the canvas itself has focus or
 *    the reader has already started the game AND is not typing — see keyOK().
 *    A reader who lands on a miss, types a name and hits space mid-phrase must
 *    get a space, not a jump.
 * 2. NOTHING MOVES UNTIL ASKED. No loop runs on load: the idle frame is drawn
 *    once and the rAF starts on a tap, a click, Space, or the Play button.
 *    That is also what makes prefers-reduced-motion honest here — the motion
 *    is reader-initiated, which is the one kind that setting permits.
 * 3. NO IMAGES, NO DEPENDENCIES. Everything is drawn with canvas paths, so the
 *    whole game is one small file on a page a reader reached by mistake and
 *    may be paying for by the megabyte.
 * 4. IT STOPS WHEN NOBODY IS WATCHING. Blur and tab-hide pause it; a game
 *    running in a background tab on a phone is a battery bill for nothing.
 *
 * The only thing written to disk is one integer, the best distance, under
 * md-soi-best. No coordinates, no counts of anything a person did.
 */
(function () {
  "use strict";

  var cv = document.getElementById("soirun");
  if (!cv || !cv.getContext) return;
  var ctx = cv.getContext("2d");
  /* build.py ships the strip hidden. Reaching this line is the proof that
     there is a game to show, so this is where it is shown — a reader with no
     JavaScript, or with this file blocked, gets the page without it rather
     than an empty box and a Play button that does nothing. */
  var strip = document.getElementById("soirun-strip");
  if (strip) strip.hidden = false;
  var sayline = document.getElementById("soirun-say");
  if (sayline) sayline.hidden = false;
  var wrap = cv.closest(".soirun") || cv.parentNode;
  var hud = document.getElementById("soirun-score");
  var hint = document.getElementById("soirun-hint");
  var playBtn = document.getElementById("soirun-play");

  /* ---- palette ---------------------------------------------------------
     Read off :root so a retune of the site's colours carries into the game
     instead of leaving one strip on the old paper. Fallbacks are the values
     as of 2026-09-05, so the game still draws if the stylesheet is late. */
  function v(name, fallback) {
    try {
      var got = getComputedStyle(document.documentElement)
        .getPropertyValue(name).trim();
      return got || fallback;
    } catch (e) { return fallback; }
  }
  /* Chosen for the horizon, not for the swatch. The first pairing was
     --card-alt sky over --paper road with --soft shophouses: three creams
     within a few points of each other, so the road edge disappeared and the
     skyline read as a smudge. The road stays paper — the game should look
     like the page it is on — and the buildings and the kerb line carry the
     contrast instead. */
  var DAY = {
    sky: v("--card-alt", "#f8f0dd"),
    far: v("--dashed", "#c4b28d"),
    road: v("--paper", "#faf5ea"),
    line: v("--ink-soft", "#544636"),
    ink: v("--ink", "#2a1e16"),
    ant: v("--ant", "#c13a2e"),
    antDark: v("--ant-dark", "#8f2a21"),
    gold: v("--gold-light", "#f3c34b"),
    goldInk: v("--gold-ink", "#8e6621"),
    dust: v("--gloss", "#685845")
  };
  var NIGHT = {
    sky: v("--night-b", "#1e0f30"),
    far: v("--night-a", "#3a1b4f"),
    road: v("--night-c", "#160a24"),
    line: v("--night-mute", "#d8c7ee"),
    ink: v("--on-dark", "#f7eeda"),
    ant: v("--neon", "#ff6ec7"),
    antDark: v("--neon", "#ff6ec7"),
    gold: v("--neon-gold", "#ffd24a"),
    goldInk: v("--neon-gold", "#ffd24a"),
    dust: v("--night-mute", "#d8c7ee")
  };

  /* ---- the field -------------------------------------------------------
     One logical coordinate system, 800x200, scaled to whatever width the card
     gives us and to the device pixel ratio. Every number below is in logical
     units, so the game plays identically on a 360px phone and a desktop. */
  /* The whole world is drawn against these four numbers and the ant's two
     heights below. The first draft put the ant at 30 of 200 — 15% of the
     strip, against the 31% Chrome's dinosaur fills — and the strip read as a
     lot of empty sky with a smudge in it. Scaling the ANT and the obstacles
     up, rather than cropping the frame down, keeps the 4:1 shape that stops
     this thing pushing the search box off a phone screen. */
  var W = 800, H = 200, GROUND = 168, WIRE_Y = 104;
  function fit() {
    var css = wrap.clientWidth || cv.clientWidth || 800;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var h = Math.round(css * H / W);
    cv.style.height = h + "px";
    cv.width = Math.round(css * dpr);
    cv.height = Math.round(h * dpr);
    ctx.setTransform(cv.width / W, 0, 0, cv.width / W, 0, 0);
    draw();
  }

  /* ---- state ----------------------------------------------------------- */
  var IDLE = 0, RUN = 1, OVER = 2, PAUSED = 3;
  var state = IDLE;
  var ant, obs, sugar, dist, sugarCount, speed, spawnIn, raf = 0, last = 0, acc = 0;
  var best = 0;
  try { best = parseInt(localStorage.getItem("md-soi-best"), 10) || 0; } catch (e) {}

  function reset() {
    ant = { y: 0, vy: 0, duck: false, step: 0, dead: false };
    obs = [];
    sugar = [];
    dist = 0;
    sugarCount = 0;
    speed = 5.6;
    spawnIn = 60;
  }
  reset();

  function night() { return Math.floor(dist / 500) % 2 === 1; }
  function pal() { return night() ? NIGHT : DAY; }

  /* ---- obstacles -------------------------------------------------------
     Four things that are actually in the way of an ant on a Chiang Mai soi.
     Three sit on the ground and are jumped; the wires hang and are ducked
     under, which is what stops the game being one button. */
  var KINDS = [
    { k: "cone", w: 28, h: 48, air: false, min: 0 },
    { k: "cones", w: 64, h: 48, air: false, min: 220 },
    { k: "dog", w: 76, h: 32, air: false, min: 120 },
    { k: "cart", w: 66, h: 64, air: false, min: 380 },
    { k: "wire", w: 84, h: 40, air: true, min: 600 }
  ];

  function spawn() {
    var pool = KINDS.filter(function (k) { return dist >= k.min; });
    var k = pool[(Math.random() * pool.length) | 0];
    obs.push({ k: k.k, x: W + 20, w: k.w, h: k.h, air: k.air });
    /* Gap scales with speed so the jump stays possible at 14 as it was at 6.
       Below this the game stops being hard and starts being unfair. */
    spawnIn = Math.round((58 + Math.random() * 46) * (7.2 / speed));
    /* A sugar arc rides in the space between obstacles, at a height only a
       jump reaches. Ants are why this site is called Mot Dang. */
    if (Math.random() < 0.55) {
      var n = 3 + ((Math.random() * 3) | 0);
      var x0 = W + 20 + 130 + Math.random() * 90;
      for (var i = 0; i < n; i++) {
        sugar.push({ x: x0 + i * 30, y: 104 - Math.sin(i / (n - 1) * Math.PI) * 44, got: false });
      }
    }
  }

  /* ---- one 60Hz step --------------------------------------------------- */
  function step() {
    dist += speed / 11;                 /* logical px -> a readable metre */
    if (speed < 14) speed += 0.0022;

    ant.vy += 0.62;
    ant.y += ant.vy;
    if (ant.y > 0) { ant.y = 0; ant.vy = 0; }
    /* Ducking in the air drops you faster — the same trick the dino has, and
       the only way to make a low wire after a badly timed jump. */
    if (ant.duck && ant.y < 0) ant.vy += 0.55;
    ant.step += speed * 0.09;

    if (--spawnIn <= 0) spawn();

    var i;
    for (i = obs.length - 1; i >= 0; i--) {
      obs[i].x -= speed;
      if (obs[i].x + obs[i].w < -10) obs.splice(i, 1);
    }
    for (i = sugar.length - 1; i >= 0; i--) {
      sugar[i].x -= speed;
      if (sugar[i].x < -20) sugar.splice(i, 1);
    }

    /* Hitboxes, and the three numbers that decide whether this is a game.
       The ant standing is 40 tall (top at 128) and ducking is 20 (top at 148);
       WIRE_Y..WIRE_Y+40 is 104..144. So a wire catches a standing ant with 9px
       to spare and misses a ducking one by 11 — the first draft hung the wires
       at 78, entirely above a 26-tall ant, and ducking did nothing at all on a
       page nobody would have reported it from. tests/test_soi_run.js pins all
       three. Boxes sit a little inside the art on purpose: a pixel-tight
       collision on a hand-drawn ant reads as a cheat. */
    var aw = 62;
    var ah = ant.duck ? 20 : 40;
    var ax = 60, ay = GROUND + ant.y - ah;

    for (i = 0; i < obs.length; i++) {
      var o = obs[i];
      var oy = o.air ? WIRE_Y : GROUND - o.h;
      if (ax + aw - 6 > o.x + 3 && ax + 6 < o.x + o.w - 3 &&
          ay + ah - 4 > oy + 3 && ay + 4 < oy + o.h - 3) {
        return over();
      }
    }
    for (i = 0; i < sugar.length; i++) {
      var s = sugar[i];
      if (s.got) continue;
      if (Math.abs(s.x - (ax + aw / 2)) < 22 && Math.abs(s.y - (ay + ah / 2)) < 24) {
        s.got = true;
        sugarCount++;
        dist += 12;
      }
    }
  }

  /* ---- drawing --------------------------------------------------------- */
  function draw() {
    var p = pal();
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = p.sky;
    ctx.fillRect(0, 0, W, H);

    /* Far side of the soi: shophouse roofline, parallax at a third speed.
       It is two tones and no detail, because at 14px/frame detail is mud. */
    var off = (dist * 3.2) % 160;
    ctx.fillStyle = p.far;
    for (var b = -1; b < 7; b++) {
      var bx = b * 160 - off;
      ctx.fillRect(bx, 62, 96, 42);
      ctx.fillRect(bx + 104, 76, 44, 28);
      ctx.beginPath();
      ctx.moveTo(bx - 6, 62); ctx.lineTo(bx + 48, 38); ctx.lineTo(bx + 102, 62);
      ctx.closePath(); ctx.fill();
    }

    ctx.fillStyle = p.road;
    ctx.fillRect(0, GROUND, W, H - GROUND);
    ctx.strokeStyle = p.line;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, GROUND + 0.5); ctx.lineTo(W, GROUND + 0.5);
    ctx.stroke();

    /* Grit on the tarmac, so standing still still reads as a road. */
    ctx.fillStyle = p.line;
    var g = (dist * 11) % 40;
    for (var x = -g; x < W; x += 40) {
      ctx.fillRect(x, GROUND + 9, 13, 2);
      ctx.fillRect(x + 21, GROUND + 19, 7, 2);
    }

    for (var i = 0; i < obs.length; i++) drawObs(obs[i], p);
    for (var j = 0; j < sugar.length; j++) {
      var s = sugar[j];
      if (s.got) continue;
      ctx.fillStyle = p.gold;
      ctx.fillRect(s.x - 4, s.y - 4, 8, 8);
      ctx.fillStyle = p.goldInk;
      ctx.fillRect(s.x - 4, s.y - 4, 3, 3);
    }

    drawAnt(p);

    if (state !== RUN) {
      ctx.fillStyle = p.sky;
      ctx.globalAlpha = 0.82;
      ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = 1;
      ctx.fillStyle = p.ink;
      ctx.textAlign = "center";
      ctx.font = "700 30px -apple-system,Thonburi,Sarabun,sans-serif";
      if (state === OVER) {
        ctx.fillText("ชนเข้าให้แล้ว · Bumped into it", W / 2, 72);
        ctx.font = "500 21px -apple-system,Thonburi,Sarabun,sans-serif";
        ctx.fillText("เดินได้ " + Math.floor(dist) + " ม. · you walked " +
                     Math.floor(dist) + " m", W / 2, 106);
        ctx.fillText("แตะอีกครั้งเพื่อเดินใหม่ · tap to walk it again", W / 2, 136);
      } else if (state === PAUSED) {
        ctx.fillText("พักไว้ก่อน · Paused", W / 2, 82);
        ctx.font = "500 21px -apple-system,Thonburi,Sarabun,sans-serif";
        ctx.fillText("แตะเพื่อเดินต่อ · tap to carry on", W / 2, 118);
      } else {
        ctx.fillText("ซอยนี้ยังว่าง · This soi is empty", W / 2, 72);
        ctx.font = "500 21px -apple-system,Thonburi,Sarabun,sans-serif";
        ctx.fillText("แตะหรือกด Space เพื่อออกเดิน · tap or press Space to walk",
                     W / 2, 106);
        if (best) {
          ctx.fillStyle = p.goldInk;
          ctx.fillText("ไกลสุดที่เคยเดิน " + best + " ม. · your best is " + best + " m",
                       W / 2, 136);
        }
      }
      ctx.textAlign = "left";
    }
  }

  function drawObs(o, p) {
    var y = o.air ? WIRE_Y : GROUND - o.h;
    if (o.k === "cone" || o.k === "cones") {
      var n = o.k === "cones" ? 2 : 1;
      for (var c = 0; c < n; c++) {
        var cx = o.x + c * 36;
        ctx.fillStyle = night() ? p.gold : "#d9622a";
        ctx.beginPath();
        ctx.moveTo(cx + 14, y);
        ctx.lineTo(cx + 26, GROUND);
        ctx.lineTo(cx + 2, GROUND);
        ctx.closePath(); ctx.fill();
        ctx.fillRect(cx - 1, GROUND - 5, 30, 5);
        ctx.fillStyle = p.sky;                 /* the reflective band */
        ctx.fillRect(cx + 7, y + 19, 15, 7);
      }
    } else if (o.k === "dog") {
      /* หมาซอย, asleep across the lane, entirely unbothered. */
      ctx.fillStyle = night() ? p.line : "#8a6a44";
      ctx.beginPath();
      ctx.ellipse(o.x + 40, GROUND - 13, 34, 13, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(o.x + 11, GROUND - 19, 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();                          /* one ear up */
      ctx.moveTo(o.x + 5, GROUND - 28);
      ctx.lineTo(o.x + 2, GROUND - 40);
      ctx.lineTo(o.x + 14, GROUND - 29);
      ctx.closePath(); ctx.fill();
      ctx.fillRect(o.x + 68, GROUND - 30, 5, 17); /* tail, flat out */
    } else if (o.k === "cart") {
      /* แผงลอย — a cart with its umbrella up. */
      ctx.fillStyle = night() ? p.far : "#9a8a6a";
      ctx.fillRect(o.x + 8, GROUND - 34, 50, 26);
      ctx.fillStyle = p.ant;
      ctx.beginPath();
      ctx.moveTo(o.x, GROUND - 42);
      ctx.quadraticCurveTo(o.x + 33, GROUND - 72, o.x + 66, GROUND - 42);
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = p.ink;
      ctx.fillRect(o.x + 31, GROUND - 44, 4, 12);
      ctx.beginPath(); ctx.arc(o.x + 19, GROUND - 5, 6, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(o.x + 47, GROUND - 5, 6, 0, Math.PI * 2); ctx.fill();
    } else {
      /* สายไฟ — the tangle every soi has overhead, with a lantern in it. The
         art is drawn TO the hitbox rather than near it: the wires sag across
         the top of the box and the lantern hangs to its bottom edge, so what
         the reader ducks under is what is actually there. */
      ctx.strokeStyle = p.ink;
      ctx.lineWidth = 3;
      for (var k = 0; k < 3; k++) {
        ctx.beginPath();
        ctx.moveTo(o.x - 10, y + 2 + k * 5);
        ctx.quadraticCurveTo(o.x + 42, y + 16 + k * 6, o.x + 94, y + 2 + k * 5);
        ctx.stroke();
      }
      ctx.strokeStyle = p.goldInk;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(o.x + 42, y + 16); ctx.lineTo(o.x + 42, y + 22);
      ctx.stroke();
      ctx.fillStyle = p.gold;
      ctx.beginPath();
      ctx.ellipse(o.x + 42, y + 30, 12, 10, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawAnt(p) {
    /* Three segments, six legs, two antennae — มดแดง, drawn the way the
       masthead ant is drawn, facing the way she is walking.
       lift is the body centre above the road and sq flattens her when she
       ducks; the legs are drawn to lift/sq, which is where the road is in
       this transformed frame, so they land on it in both postures instead of
       through it. */
    var base = GROUND + ant.y;
    var duck = ant.duck && ant.y === 0;
    var lift = duck ? 12 : 26;
    var sq = duck ? 0.55 : 1;
    var foot = lift / sq;
    var swing = Math.sin(ant.step);
    var run = ant.y === 0;

    ctx.save();
    ctx.translate(98, base - lift);
    ctx.scale(1, sq);

    ctx.strokeStyle = p.antDark;
    ctx.lineWidth = 3.5;
    ctx.lineCap = "round";
    for (var i = 0; i < 3; i++) {
      var lx = -17 + i * 18;
      var ph = run ? Math.sin(ant.step + i * 2.1) : 0.6;
      ctx.beginPath();
      ctx.moveTo(lx, 3);
      ctx.lineTo(lx - 9 + ph * 10, foot);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(lx, 3);
      ctx.lineTo(lx + 10 - ph * 10, foot);
      ctx.stroke();
    }

    ctx.fillStyle = p.ant;
    ctx.beginPath(); ctx.ellipse(-27, 0, 17, 14, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(-3, 0, 11, 10, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(20, -3, 13, 11, 0, 0, Math.PI * 2); ctx.fill();

    ctx.strokeStyle = p.antDark;
    ctx.lineWidth = 3;
    var aw = run ? swing * 4 : 0;
    ctx.beginPath();
    ctx.moveTo(27, -9); ctx.quadraticCurveTo(38, -23, 46 + aw, -28);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(27, -3); ctx.quadraticCurveTo(41, -14, 50 - aw, -17);
    ctx.stroke();

    ctx.fillStyle = p.sky;
    ctx.beginPath(); ctx.arc(24, -6, 3.2, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    /* A little dust where the feet are, so speed is visible standing still. */
    if (run && state === RUN) {
      ctx.fillStyle = p.dust;
      ctx.globalAlpha = 0.5;
      var d = (ant.step * 6) % 20;
      ctx.fillRect(58 - d, GROUND - 4, 11, 3);
      ctx.fillRect(44 - d, GROUND - 9, 7, 2);
      ctx.globalAlpha = 1;
    }
  }

  /* The running score, and ONLY while running. Sitting over the idle card it
     covered the "This soi is empty" line — the one sentence that tells a
     reader the strip is a thing they can start. The overlay carries the best
     distance itself, so nothing is lost by taking the pill away. */
  function hudText() {
    if (!hud) return;
    hud.hidden = state !== RUN;
    var line = Math.floor(dist) + " ม. / m";
    if (sugarCount) line += "  ·  🍯 " + sugarCount;
    if (best) line += "  ·  ไกลสุด best " + best;
    hud.textContent = line;
  }

  /* ---- loop ------------------------------------------------------------ */
  function frame(t) {
    raf = requestAnimationFrame(frame);
    if (!last) last = t;
    acc += Math.min(t - last, 120);       /* a backgrounded tab must not
                                             fast-forward the ant into a cone */
    last = t;
    while (acc >= 1000 / 60) {
      acc -= 1000 / 60;
      if (state !== RUN) break;
      step();
    }
    draw();
    hudText();
  }

  function start() {
    if (state === RUN) return;
    reset();
    state = RUN;
    last = 0; acc = 0;
    say("กระโดด: แตะ หรือ Space · มุด: แตะค้างครึ่งล่าง หรือลูกศรลง",
        "Jump: tap or Space · Duck: hold the lower half, or Down arrow");
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(frame);
  }

  function over() {
    state = OVER;
    ant.dead = true;
    var m = Math.floor(dist);
    if (m > best) {
      best = m;
      try { localStorage.setItem("md-soi-best", String(best)); } catch (e) {}
    }
    cancelAnimationFrame(raf);
    raf = 0;
    say("ชนแล้ว — แตะที่ซอยเพื่อเดินใหม่", "Bumped into it — tap the soi to walk it again");
    draw();
    hudText();
  }

  /* An interruption is not a crash. The tab went away; the run is held where
     it stood and the next tap carries on, because ending somebody's best run
     because they took a phone call is a way to lose them twice. */
  function pause() {
    if (state !== RUN) return;
    state = PAUSED;
    cancelAnimationFrame(raf); raf = 0;
    say("พักไว้ก่อน — แตะเพื่อเดินต่อ", "Paused — tap to carry on");
    draw();
  }

  function resume() {
    if (state !== PAUSED) return;
    state = RUN;
    last = 0; acc = 0;
    say("กระโดด: แตะ หรือ Space · มุด: แตะค้างครึ่งล่าง หรือลูกศรลง",
        "Jump: tap or Space · Duck: hold the lower half, or Down arrow");
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(frame);
  }

  /* The hint is bilingual markup, not a string: md.js's language toggle shows
     and hides .th/.en inside it, so writing textContent here would leave one
     line on the page that ignores the reader's choice of language. mdBi() is
     md.js's own joiner; if md.js has not loaded, the hint simply stays as
     build.py rendered it. */
  function say(th, en) {
    if (!hint || typeof window.mdBi !== "function") return;
    hint.innerHTML = window.mdBi(th, en);
  }

  /* ---- input -----------------------------------------------------------
     keyOK is the whole of rule 1. Keys are ours only when the canvas has
     focus, and never when the reader is in a field — which on this page is
     the search box, the reason anybody is here. */
  function typing(el) {
    if (!el) return false;
    var t = (el.tagName || "").toLowerCase();
    return t === "input" || t === "textarea" || t === "select" || el.isContentEditable;
  }
  function keyOK() {
    return document.activeElement === cv && !typing(document.activeElement);
  }

  cv.addEventListener("keydown", function (e) {
    if (!keyOK()) return;
    if (e.key === " " || e.key === "Spacebar" || e.key === "ArrowUp" || e.key === "Enter") {
      e.preventDefault();
      if (state === PAUSED) return resume();
      if (state !== RUN) return start();
      if (ant.y === 0) { ant.vy = -13.2; ant.duck = false; }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      ant.duck = true;
    }
  });
  cv.addEventListener("keyup", function (e) {
    if (e.key === "ArrowDown") ant.duck = false;
  });

  function pointerDown(e) {
    e.preventDefault();
    cv.focus();
    if (state === PAUSED) return resume();
    if (state !== RUN) return start();
    var r = cv.getBoundingClientRect();
    var y = ((e.touches ? e.touches[0].clientY : e.clientY) - r.top) / r.height;
    if (y > 0.62) { ant.duck = true; return; }      /* lower half ducks */
    if (ant.y === 0) { ant.vy = -13.2; ant.duck = false; }
  }
  function pointerUp() { ant.duck = false; }

  cv.addEventListener("mousedown", pointerDown);
  cv.addEventListener("mouseup", pointerUp);
  cv.addEventListener("touchstart", pointerDown, { passive: false });
  cv.addEventListener("touchend", pointerUp);
  cv.addEventListener("touchcancel", pointerUp);
  if (playBtn) playBtn.addEventListener("click", function () {
    cv.focus();
    /* Held mid-run, the button carries on rather than wiping the run —
       the same thing a tap on the soi does. */
    if (state === PAUSED) return resume();
    start();
  });

  window.addEventListener("blur", pause);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) pause();
  });
  window.addEventListener("resize", fit);

  /* The test seam. tests/test_soi_run.js runs this file against a stub canvas
     and needs to see whether the ant is actually ducking, actually airborne,
     and what is on the road — none of which a stub context can be asked. Read
     only, and getters rather than a copy, so nothing here is a second source
     of truth about the game's state. */
  window.MDSOI = {
    get state() { return state; },
    get ant() { return ant; },
    get obs() { return obs; },
    get dist() { return dist; },
    get ground() { return GROUND; },
    get wireY() { return WIRE_Y; }
  };

  fit();
  hudText();
})();
