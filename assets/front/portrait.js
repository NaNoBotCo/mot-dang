/* A place page's portrait (Nan, 2026-10-02: "utilize the doodler to avoid filler"): a page
   with no photograph of its own draws the place from its own facts with the auto-doodler.
   build.py writes <canvas class="mdportrait" data-set="…" data-p='{facts}'>; this sizes it,
   animates it while it is on screen, and holds it still for readers who ask for less motion. */
(function () {
'use strict';
var D = window.MDDOODLER; if (!D) return;
var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches, RIDGE = null;
var base = (document.currentScript && document.currentScript.src || '').replace(/portrait\.js(\?.*)?$/, '');
if (base) fetch(base + 'ridge.json').then(function (r) { return r.json(); }).then(function (j) { RIDGE = j; }, function () { });
function mount(cv) {
  if (cv.dataset.on) return; cv.dataset.on = '1';   /* once, however many copies of this script the page holds */
  var place, set = cv.dataset.set, on = false, last = 0;
  try { place = JSON.parse(cv.dataset.p || '{}'); } catch (e) { return; }
  var c = cv.getContext('2d'), W = 0, H = 0;
  function size() { var dpr = Math.min(2, window.devicePixelRatio || 1); W = cv.clientWidth; H = cv.clientHeight; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); c.setTransform(dpr, 0, 0, dpr, 0, 0); }
  function paint(t) { if (!W) size(); c.clearRect(0, 0, W, H); D.portrait(c, W, H, t, { set: set, place: place, ridge: RIDGE }); }
  function f(t) { if (!on) return; if (t - last > 32) { last = t; paint(t); } requestAnimationFrame(f); }
  size(); paint(4000);
  addEventListener('resize', function () { size(); paint(4000); });
  addEventListener('mddoodler', function () { paint(REDUCED ? 4000 : performance.now()); });   /* its scene file arrived */
  if (REDUCED) { setInterval(function () { paint(4000); }, 30e3); return; }
  new IntersectionObserver(function (es) { var was = on; on = es[0].isIntersecting; if (on && !was) requestAnimationFrame(f); }).observe(cv);
}
function all() { [].forEach.call(document.querySelectorAll('canvas.mdportrait'), mount); }
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
