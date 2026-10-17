/* The app's home map (motdang.net/appmap/, what the Android app opens on):
   your bike, parking and toilets on one map, search above it.

   Parking, your bike and the walk-back arrow come from ../parking/parking.js
   (window.MDPark). This file adds the toilets from /data/toilets.json — the
   mapped points and the kinds of place anyone may walk into — and the two
   "nearest" buttons. */
(function () {
'use strict';
var P = window.MDPark;
if (!P) return;
var $ = function (s) { return document.querySelector(s); };
var mapEl = document.getElementById('pkmap'), map = null, T = null, PTS = [];

function hoursOpen(w) {
  if (!w) return null;
  var h = new Date().getHours() + new Date().getMinutes() / 60;
  return h >= w[0] && h < w[1];
}
function load() {
  return fetch('../data/toilets.json').then(function (r) { return r.json(); }).then(function (d) {
    T = d;
    var tiers = d.tiers;
    d.verified.forEach(function (v) {
      PTS.push({la: v[0], ln: v[1], th: v[2], en: v[3], fee: v[4], baht: v[5], hours: v[6], k: 'v'});
    });
    d.places.forEach(function (p) {
      var t = tiers[p[0]];
      if (!t || (t.access !== 'public' && t.access !== 'visitor') || p[7] === 'toiletnone') return;
      PTS.push({la: p[1], ln: p[2], th: p[3], en: p[4], hours: p[6], t: t, k: 't'});
    });
  });
}
function name(x) {
  var n = P.L(x.th, x.en) || x.th || x.en;
  return n || P.L('ห้องน้ำ', 'Toilet');
}
function about(x) {
  var bits = [];
  if (x.t) {
    bits.push(P.L(x.t.th, x.t.en));
    var c = T.costs[x.t.cost]; if (c) bits.push(P.L(c.chip_th, c.chip_en));
    var w = T.windows[x.t.window];
    if (w) bits.push(P.L('มักเปิด ', 'usually open ') + w[0] + ':00–' + w[1] + ':00');
  } else {
    bits.push(P.L('ห้องน้ำที่มีคนปักหมุด', 'Mapped toilet'));
    if (x.fee === 'free') bits.push(P.L('ฟรี', 'free'));
    else if (x.baht) bits.push(x.baht + ' ฿');
  }
  if (x.hours) bits.push(x.hours);
  return bits.join(' · ');
}
function openNow(x) { return x.t ? hoursOpen(T.windows[x.t.window]) : null; }
function origin() {
  var h = P.here();
  if (h) return h;
  if (map) { var c = map.getCenter(); return {lat: c.lat, lng: c.lng}; }
  return {lat: 18.7876, lng: 98.9931};
}
function showLoo(x) {
  var o = origin(), d = P.metres(o.lat, o.lng, x.la, x.ln), box = $('#loo');
  var open = openNow(x);
  box.hidden = false;
  box.innerHTML = '<h3>' + P.icon('i-loo') + ' ' + P.esc(name(x)) + '</h3>' +
    '<div class="pk-dir">' + P.fmtD(d) + ' ' + P.dir8(P.bearing(o.lat, o.lng, x.la, x.ln)) +
    (P.here() ? P.L(' จากคุณ', ' from you') : '') + (open === false ? P.L(' · น่าจะปิดอยู่', ' · probably closed now') : '') + '</div>' +
    '<div>' + P.esc(about(x)) + '</div>' +
    '<div class="row"><button type="button" class="pk-btn pk-gold" id="loogo">' + P.icon('i-walk') + P.L('พาไป', 'Walk me there') + '</button>' +
    '<button type="button" class="pk-btn" id="loox">' + P.icon('i-x') + P.L('ปิด', 'Close') + '</button></div>';
  $('#loogo').onclick = function () { P.walkTo(x.la, x.ln, name(x) + ' · ' + about(x)); };
  $('#loox').onclick = function () { box.hidden = true; };
  box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}
function nearestLoo() {
  var o = origin(), best = null;
  PTS.forEach(function (x) {
    if (openNow(x) === false) return;
    var d = P.metres(o.lat, o.lng, x.la, x.ln);
    if (d < 5000 && (!best || d < best.d)) best = {d: d, x: x};
  });
  if (!best) return;
  if (map) map.easeTo({center: [best.x.ln, best.x.la], zoom: Math.max(map.getZoom(), 16)});
  showLoo(best.x);
}
function nearestP() {
  var o = origin();
  P.ensureTiles(o.lat, o.lng).then(function () {
    var b = P.nearest(o.lat, o.lng);
    if (!b) return;
    if (map) map.easeTo({center: [b.lot.ln, b.lot.la], zoom: Math.max(map.getZoom(), 16)});
    P.openLot(b.lot.id);
  });
}
function draw(m) {
  map = m;
  var fc = {type: 'FeatureCollection', features: PTS.map(function (x, i) {
    return {type: 'Feature', geometry: {type: 'Point', coordinates: [x.ln, x.la]}, properties: {i: i}};
  })};
  m.addSource('loo', {type: 'geojson', data: fc});
  m.addLayer({id: 'loo-c', type: 'circle', source: 'loo', minzoom: 12, paint: {
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 12, 3, 16, 7],
    'circle-color': '#0F6E78', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5}});
  m.on('click', 'loo-c', function (e) { var f = e.features && e.features[0]; if (f) showLoo(PTS[f.properties.i]); });
  m.on('mouseenter', 'loo-c', function () { m.getCanvas().style.cursor = 'pointer'; });
  m.on('mouseleave', 'loo-c', function () { m.getCanvas().style.cursor = ''; });
}
var openCard = false;
var mine = $('#mine');
function keep() { var c = mine.querySelector('.pk-card.has'); if (c) c.classList.toggle('open', openCard); }
new MutationObserver(keep).observe(mine, {childList: true});
mine.addEventListener('click', function (e) {
  if (e.target.closest('.pk-card.has h2')) { openCard = !openCard; keep(); }
});
$('#qp').onclick = nearestP;
$('#qt').onclick = function () { if (T) nearestLoo(); };
load().then(function () { if (window.MDMAP) MDMAP.ready(mapEl, draw); });
})();
