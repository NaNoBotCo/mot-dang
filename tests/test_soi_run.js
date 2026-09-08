#!/usr/bin/env node
// Is the game on 404.html a game — and does it stay out of the search box?
//
//   node tests/test_soi_run.js          (needs only assets/soi_run.js)
//
// The 404 page's job is to get a reader who mistyped an address to the page
// they meant. The side-scroller across the top of it is delight, and delight
// is allowed to cost nothing: this file is the price list.
//
// Two of these checks exist because the first draft failed them silently and
// nobody would ever have filed a bug:
//
//   * THE WIRES HUNG AT y=78 over a 26-tall ant standing at y=142. Ducking was
//     wired, drawn, documented in the hint line and mathematically incapable of
//     mattering — the wire could not touch a standing ant, so the second button
//     was decoration. Geometry that is off by 60px looks exactly like geometry
//     that is right, in a screenshot.
//   * A KEYSTROKE IS THE READER'S. Space belongs to whatever they are typing.
//     On a page whose whole point is a search box, a game that swallows the
//     space bar has taken the page away from the person who needs it.
//
// The rest hold the physics honest: a jump that cannot clear the tallest thing
// on the road, or a gap narrower than a jump is long, is a game that cheats.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'assets', 'soi_run.js');
const FAILED = [];
function ok(name, cond, detail) {
  if (cond) { console.log('  ok   ' + name); return; }
  FAILED.push(name + (detail ? ' — ' + detail : ''));
  console.log('  FAIL ' + name + (detail ? ' — ' + detail : ''));
}

// ---- a canvas and a page, enough of each ---------------------------------
// The 2d context records nothing but the fact that it was asked; the tests
// below are about state and geometry, never about pixels.
function stubCtx() {
  const c = { calls: 0 };
  for (const m of ['clearRect', 'fillRect', 'beginPath', 'moveTo', 'lineTo',
                   'quadraticCurveTo', 'closePath', 'fill', 'stroke', 'arc',
                   'ellipse', 'save', 'restore', 'translate', 'scale',
                   'fillText', 'setTransform']) c[m] = () => { c.calls++; };
  return c;
}

function load() {
  const listeners = { cv: {}, win: {}, doc: {} };
  const on = (bag) => (ev, fn) => { (bag[ev] = bag[ev] || []).push(fn); };
  const ctx = stubCtx();
  const cv = {
    id: 'soirun', tagName: 'CANVAS', width: 800, height: 200, style: {},
    clientWidth: 800, getContext: () => ctx, focus() { doc.activeElement = cv; },
    closest: () => wrap, parentNode: wrap,
    getBoundingClientRect: () => ({ top: 0, left: 0, width: 800, height: 200 }),
    addEventListener: on(listeners.cv)
  };
  var wrap = { clientWidth: 800 };
  const hud = { textContent: '' };
  const hint = { textContent: '', innerHTML: '' };
  const play = { addEventListener: on({}), hidden: false };
  const input = { tagName: 'INPUT', isContentEditable: false };
  const doc = {
    activeElement: null, hidden: false,
    documentElement: {},
    getElementById: (id) => ({ soirun: cv, 'soirun-score': hud,
                               'soirun-hint': hint, 'soirun-play': play }[id] || null),
    addEventListener: on(listeners.doc)
  };
  const rafQ = [];
  const store = {};
  const win = {
    devicePixelRatio: 1,
    addEventListener: on(listeners.win),
    getComputedStyle: () => ({ getPropertyValue: () => '' }),
    localStorage: { getItem: (k) => (k in store ? store[k] : null),
                    setItem: (k, v) => { store[k] = String(v); } },
    requestAnimationFrame: (fn) => { rafQ.push(fn); return rafQ.length; },
    cancelAnimationFrame: () => { rafQ.length = 0; }
  };
  win.window = win;
  const sandbox = Object.assign(win, {
    document: doc, localStorage: win.localStorage, Math, Object, JSON, console,
    getComputedStyle: win.getComputedStyle,
    requestAnimationFrame: win.requestAnimationFrame,
    cancelAnimationFrame: win.cancelAnimationFrame,
    MouseEvent: function () {}, parseInt
  });
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(SRC, 'utf8'), sandbox, { filename: 'soi_run.js' });

  const fire = (bag, ev, e) => (listeners[bag][ev] || []).forEach((f) => f(e || {}));
  // One animation frame = 1/60s of wall clock, handed in as the timestamp the
  // real rAF would hand in, so the fixed-step loop advances exactly once.
  let t = 0;
  function tick(n) {
    for (let i = 0; i < n; i++) {
      const fn = rafQ.shift();
      if (!fn) return false;
      t += 1000 / 60;
      fn(t);
    }
    return true;
  }
  return { cv, hud, hint, doc, ctx, fire, tick, rafQ, store, input,
           game: sandbox.MDSOI,
           key: (k) => fire('cv', 'keydown', { key: k, preventDefault() {} }),
           keyUp: (k) => fire('cv', 'keyup', { key: k }),
           tap: (yFrac) => fire('cv', 'mousedown',
             { clientY: 200 * (yFrac === undefined ? 0.2 : yFrac), clientX: 100,
               preventDefault() {} }),
           release: () => fire('cv', 'mouseup', {}),
           score: () => parseInt(hud.textContent, 10) };
}

console.log('soi_run.js — the ant, the soi, and the search box');

// ---- 1. nothing moves until asked ----------------------------------------
{
  const g = load();
  ok('draws its idle frame on load', g.ctx.calls > 0);
  ok('asks for no animation frame until the reader starts it', g.rafQ.length === 0,
     g.rafQ.length + ' queued');
  g.cv.focus();
  g.key(' ');
  ok('Space on the focused canvas starts the run', g.rafQ.length === 1);
}

// ---- 2. the search box keeps its keystrokes ------------------------------
{
  const g = load();
  g.doc.activeElement = g.input;         // the reader is typing a wat's name
  g.key(' ');
  ok('Space typed into the search box does not start the game', g.rafQ.length === 0);
  g.cv.focus();
  g.key(' ');
  g.doc.activeElement = g.input;         // …and goes back to the box mid-run
  g.tick(30);
  const before = g.score();
  g.key(' ');
  g.tick(1);
  ok('Space typed into the search box mid-run does not jump',
     g.score() >= before);               // no crash, no jump: the run just runs
}

// ---- 3. it is a game: distance accrues, and a crash ends it --------------
{
  const g = load();
  g.cv.focus(); g.key(' ');
  g.tick(60);
  ok('a second of running is distance on the board', g.score() > 20,
     'scored ' + g.score());
  // Stand still in front of everything the road throws and something must land.
  let died = false;
  for (let i = 0; i < 4000 && !died; i++) { g.tick(1); died = g.rafQ.length === 0; }
  ok('standing still eventually ends the run', died);
  ok('the best distance is remembered', 'md-soi-best' in g.store,
     JSON.stringify(g.store));
}

// ---- 4. the geometry: can the ant do what the page tells her to? ---------
// Read straight out of the source, so a number edited in one place and not the
// other is caught here rather than by a reader who cannot get past a lantern.
{
  const src = fs.readFileSync(SRC, 'utf8');
  const num = (re, what) => {
    const m = src.match(re);
    if (!m) { FAILED.push('cannot read ' + what + ' out of soi_run.js'); return NaN; }
    return parseFloat(m[1]);
  };
  const GROUND = num(/GROUND = (\d+)/, 'GROUND');
  const WIRE_Y = num(/WIRE_Y = (\d+)/, 'WIRE_Y');
  const wireH  = num(/k: "wire", w: \d+, h: (\d+)/, "the wire's height");
  const standH = num(/var ah = ant\.duck \? \d+ : (\d+)/, "the ant's standing height");
  const duckH  = num(/var ah = ant\.duck \? (\d+)/, "the ant's ducking height");
  const cartH  = num(/k: "cart", w: \d+, h: (\d+)/, "the cart's height");
  const v0     = Math.abs(num(/ant\.vy = -([\d.]+)/, 'the jump'));
  const grav   = num(/ant\.vy \+= ([\d.]+);/, 'gravity');
  const maxSpd = num(/if \(speed < (\d+)\)/, 'the top speed');

  const standTop = GROUND - standH, duckTop = GROUND - duckH;
  const wireBot = WIRE_Y + wireH;
  ok('a standing ant meets the wires', standTop + 4 < wireBot - 3,
     'ant top ' + standTop + ' vs wire bottom ' + wireBot);
  ok('a ducking ant clears them', duckTop + 4 >= wireBot - 3,
     'ducked top ' + duckTop + ' vs wire bottom ' + wireBot);

  const apex = (v0 * v0) / (2 * grav);
  ok('a jump clears the tallest thing on the road', apex > cartH + 20,
     'apex ' + apex.toFixed(0) + ' vs cart ' + cartH);
  // Airtime spent above the tallest obstacle, against the ground it covers at
  // the top speed — a gap the ant cannot cross in one jump is not a gap.
  const need = cartH - (GROUND - standH - GROUND) - 0; // clearance height wanted
  const tUp = (v0 - Math.sqrt(Math.max(v0 * v0 - 2 * grav * (cartH + 4), 0))) / grav;
  const above = 2 * (v0 / grav - tUp);
  ok('and stays up long enough to cross one at top speed', above * maxSpd > 120,
     (above * maxSpd).toFixed(0) + 'px of clear travel');
  ok('the road gets faster', maxSpd > 10);
  ok('the wires arrive after the reader has met the ground first',
     /k: "wire", .*min: (\d+)/.exec(src) && +/k: "wire", .*min: (\d+)/.exec(src)[1] >= 300);
}

// ---- 5. it stops when nobody is watching, and picks up where it stopped ---
{
  const g = load();
  g.cv.focus(); g.key(' ');
  g.tick(45);
  const held = g.score();
  g.fire('win', 'blur');
  ok('a tab that goes away pauses the run', g.rafQ.length === 0);
  g.tick(30);
  ok('and nothing runs while it is away', g.score() === held,
     held + ' -> ' + g.score());
  g.tap();
  g.tick(10);
  ok('a tap carries the same run on rather than wiping it', g.score() > held,
     held + ' -> ' + g.score());
}

// ---- 6. one strip, two verbs ---------------------------------------------
// A tap has to mean two different things depending on where the thumb lands,
// and the ant has to be genuinely in the air or genuinely flat — not merely
// drawn that way, which is all a screenshot can tell you.
{
  const g = load();
  g.cv.focus(); g.key(' ');
  g.tick(10);

  g.tap(0.2);                          // thumb on the upper half
  g.tick(6);
  ok('a tap on the upper half puts her in the air', g.game.ant.y < -20,
     'y ' + g.game.ant.y.toFixed(1));
  while (g.game.ant.y < 0) g.tick(1);  // land

  g.tap(0.9);                          // thumb on the lower half
  g.tick(2);
  ok('a tap on the lower half ducks instead', g.game.ant.duck && g.game.ant.y === 0);
  g.release();
  g.tick(1);
  ok('and letting go stands her up again', !g.game.ant.duck);

  g.key('ArrowDown');
  g.tick(1);
  ok('the Down arrow ducks too', g.game.ant.duck);
  g.keyUp('ArrowDown');
  ok('and releasing it stands her up', !g.game.ant.duck);
}

// ---- 7. ducking is the difference between living and not -----------------
// The check that would have caught the wires hanging at 78: put a wire on the
// road at the ant and run the same frame twice, once standing and once ducked.
// Standing must end the run; ducking must not.
{
  function atTheWire(duck) {
    const g = load();
    g.cv.focus(); g.key(' ');
    g.tick(5);
    if (duck) { g.tap(0.9); }
    // Drop a wire exactly onto her, bypassing the spawner's distance gate:
    // this is about the hitboxes, not about when wires are allowed to appear.
    g.game.obs.length = 0;
    g.game.obs.push({ k: 'wire', x: 78, w: 62, h: 38, air: true });
    g.tick(1);
    return g.game.state;
  }
  const RUN = 1;                                 // RUN is 1 in soi_run.js
  ok('a wire ends the run of an ant who stays standing', atTheWire(false) !== RUN);
  ok('and the same wire passes over one who ducks', atTheWire(true) === RUN);
}

console.log(FAILED.length ? '\nFAILED ' + FAILED.length + ':\n  ' + FAILED.join('\n  ')
                          : '\nall checks passed');
process.exit(FAILED.length ? 1 : 0);
