/* map-doodles.js — drawn marks for places anywhere on earth, for any map on motdang.net or a minisite.
   Nan, 2026-10-12: "attribute doodles suitable for worldwide mapping functionality in motdang and its
   mini sites … eifel tower and easter island heads ready to go, not emojis."

   Load it from its folder (it finds svg/ and map-doodles.json beside itself), or copy the folder into a
   minisite and load it from there:
     <script src="/sites/map-doodles/map-doodles.js"></script>

   MDDOODLES.ready()                 Promise of the manifest rows
   MDDOODLES.get(id)                 one row: id, en, th, group (landmark|kind), region|set, osm, wd, lat, lng
   MDDOODLES.url(id)                 the drawing as its own file, for <img src>
   MDDOODLES.html(id, px, lang)      an <img> string with its name as alt text
   MDDOODLES.image(id, px)           Promise of an Image, cached, for a canvas
   MDDOODLES.draw(ctx, id, x, y, px) draws it standing on (x, y); false until loaded, then onload(id) fires
   MDDOODLES.match(tags, kind)       the best id for a place: OSM tags {amenity:'place_of_worship', …},
                                     a wikidata id (tags.wikidata), or a motdang category (kind)
   MDDOODLES.near(lat, lng, km)      landmarks within km, nearest first
   MDDOODLES.maplibre(map, ids, px)  adds each as image 'md-doodle-<id>' for a symbol layer
                                     (icon-anchor 'bottom' puts it on its point)
   Every drawing: viewBox 0 0 64 64, standing on the bottom centre (32, 60). */
(function () {
  'use strict';
  var me = document.currentScript && document.currentScript.src;
  var BASE = me ? me.replace(/[^\/]*$/, '') : '/sites/map-doodles/';
  /* motdang's place categories (mappins_layer.KINDS) → a doodle */
  var MD = {
    wat: 'buddhist-temple', food: 'restaurant', massage: 'spa', medical: 'hospital', cannabis: 'cannabis',
    essentials: 'bank', hotel: 'hotel', school: 'school', 'school-intl': 'school', market: 'fresh-market',
    shopping: 'mall', transport: 'songthaew', sport: 'gym', muaythai: 'muay-thai', cooking: 'street-food',
    chang: 'elephant', 'museums-galleries': 'museum', parks: 'park', sights: 'viewpoint', 'whats-on': 'live-music'
  };
  var rows = null, byId = {}, wd = {}, rules = [], wait = null, imgs = {};
  var api = { base: BASE, onload: null, MD: MD };

  api.ready = function () {
    if (wait) return wait;
    wait = fetch(BASE + 'map-doodles.json').then(function (r) { return r.json(); }).then(function (list) {
      rows = list;
      list.forEach(function (r) {
        byId[r.id] = r;
        if (r.wd) wd[r.wd] = r.id;
        (r.osm || []).forEach(function (rule) {
          var need = rule.split('+').map(function (kv) { var i = kv.indexOf('='); return [kv.slice(0, i), kv.slice(i + 1)]; });
          rules.push({ id: r.id, need: need });
        });
      });
      rules.sort(function (a, b) { return b.need.length - a.need.length; });   // the most specific rule wins
      return list;
    });
    return wait;
  };
  api.list = function () { return rows || []; };
  api.get = function (id) { return byId[id] || null; };
  api.url = function (id) { return BASE + 'svg/' + id + '.svg'; };
  api.name = function (id, lang) { var r = byId[id]; return r ? (lang === 'th' ? r.th : r.en) : id; };
  api.html = function (id, px, lang) {
    px = px || 40;
    var alt = String(api.name(id, lang)).replace(/[&<>"]/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]; });
    return '<img class="md-doodle" src="' + api.url(id) + '" width="' + px + '" height="' + px + '" alt="' + alt + '" loading="lazy" decoding="async">';
  };
  api.image = function (id, px) {
    var key = id + '@' + (px || 0);
    if (imgs[key]) return imgs[key].p;
    var im = new Image(), slot = { im: im, ok: false };
    if (px) { im.width = px; im.height = px; }
    slot.p = new Promise(function (res, rej) {
      im.onload = function () { slot.ok = true; res(im); if (api.onload) api.onload(id); };
      im.onerror = rej;
    });
    im.src = api.url(id);
    imgs[key] = slot;
    return slot.p;
  };
  api.draw = function (ctx, id, x, y, px) {
    var slot = imgs[id + '@0'];
    if (!slot) { api.image(id); return false; }
    if (!slot.ok) return false;
    ctx.drawImage(slot.im, x - px / 2, y - px * 60 / 64, px, px);
    return true;
  };
  api.match = function (tags, kind) {
    tags = tags || {};
    if (tags.wikidata && wd[tags.wikidata]) return wd[tags.wikidata];
    for (var i = 0; i < rules.length; i++) {
      var ok = rules[i].need.every(function (kv) { return kv[1] === '*' ? tags[kv[0]] != null : String(tags[kv[0]]) === kv[1]; });
      if (ok) return rules[i].id;
    }
    return (kind && MD[kind]) || null;
  };
  api.near = function (lat, lng, km) {
    var out = [];
    (rows || []).forEach(function (r) {
      if (r.lat == null) return;
      var p = Math.PI / 180, a = Math.sin((r.lat - lat) * p / 2), b = Math.sin((r.lng - lng) * p / 2);
      var d = 12742 * Math.asin(Math.sqrt(a * a + Math.cos(lat * p) * Math.cos(r.lat * p) * b * b));
      if (d <= km) out.push({ id: r.id, km: d });
    });
    return out.sort(function (a, b) { return a.km - b.km; });
  };
  api.maplibre = function (map, ids, px) {
    px = px || 48;
    var ratio = Math.min(3, window.devicePixelRatio || 1);
    return Promise.all(ids.map(function (id) {
      var name = 'md-doodle-' + id;
      if (map.hasImage(name)) return name;
      return new Promise(function (res) {
        var im = new Image(px * ratio, px * ratio);
        im.onload = function () { if (!map.hasImage(name)) map.addImage(name, im, { pixelRatio: ratio }); res(name); };
        im.onerror = function () { res(null); };
        im.src = api.url(id);
      });
    }));
  };
  window.MDDOODLES = api;
})();
