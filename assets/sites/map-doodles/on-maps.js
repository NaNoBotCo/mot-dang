/* on-maps.js — the landmark drawings of map-doodles on the directory's MapLibre maps.
   Nan, 2026-10-12: put the map doodles on the site's maps, "keep the pics a bit compact".

   A landmark that is in view and has a place in the directory is drawn at that place, 28 to 40 px, and
   the place's own pin steps aside. A tap opens what the pin opened. The 135 'kind' doodles are not
   drawn here.

   Start it from map.js after MDPINS.paint:  MDDOODLEMAP.attach(map, el)
   or load it on a page with maps and it attaches to each [data-mdmap] box by itself.
   map-doodles.js and its manifest load when the first map is at zoom 10.5 or closer and a landmark is
   in view; each drawing is its own small file, fetched once for a landmark that is on screen.

   Skipped: boxes marked data-mdpins-own (the doodle maps' Streets and Terrain views) and /sites/doodle*. */
(function () {
  'use strict';
  if (window.MDDOODLEMAP) return;
  var me = document.currentScript && document.currentScript.src;
  var BASE = me ? me.replace(/[^\/]*$/, '') : 'https://motdang.net/sites/map-doodles/';
  var ORIGIN = (/^https?:\/\/[^\/]+\//.exec(BASE) || ['https://motdang.net/'])[0];
  var MINZ = 10.5;                 // below this nothing is drawn or fetched
  var PX = 48;                     // the raster size; icon-size scales it to 24-40 px
  var CAT = { sights: 1, wat: 1, parks: 1, 'museums-galleries': 1, community: 1, 'whats-on': 1 };
  var STOP = { buddha: 1, temple: 1, chedi: 1, gate: 1, wat: 1, tower: 1, bridge: 1, park: 1 };
  var TH = /[฀-๿]/;
  var EMPTY = { type: 'FeatureCollection', features: [] };
  var LIB = null, ATT = new WeakSet(), MEM = {};

  /* ---- the manifest, read once ---- */
  function norm(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9฀-๿]+/g, ' ').replace(/\s+/g, ' ').trim(); }
  function prep(rows) {
    var seen = {}, city = {};
    rows.forEach(function (r) {
      if (r.city) city[norm(r.city)] = 1;
      (r.words || []).forEach(function (w) { w = norm(w); seen[w] = (seen[w] || 0) + 1; });
    });
    var out = [];
    rows.forEach(function (r) {
      if (r.group !== 'landmark' || r.lat == null) return;
      var ph = [], src = [r.th, r.wiki].concat(String(r.en || '').split(','), r.words || []);
      src.forEach(function (s) {
        s = norm(s);
        if (!s || ph.indexOf(s) > -1 || city[s] || STOP[s] || seen[s] > 2) return;
        if (s.length < (TH.test(s) ? 4 : 5)) return;
        ph.push(s);
      });
      out.push({ id: r.id, en: r.en, th: r.th, lat: r.lat, lng: r.lng, area: !!r.area, ph: ph });
    });
    return out;
  }
  function lib() {
    if (LIB) return LIB;
    LIB = new Promise(function (ok, no) {
      function go() { window.MDDOODLES.ready().then(function (rows) { ok(prep(rows)); }, no); }
      if (window.MDDOODLES) return go();
      var s = document.createElement('script');
      s.src = BASE + 'map-doodles.js'; s.onload = go; s.onerror = no;
      document.head.appendChild(s);
    });
    LIB.catch(function () { LIB = null; });
    return LIB;
  }

  /* ---- a landmark finds its place ---- */
  function metres(aLat, aLng, bLat, bLng) {
    var p = Math.PI / 180, dy = (bLat - aLat) * 111320, dx = (bLng - aLng) * 111320 * Math.cos(aLat * p);
    return Math.sqrt(dx * dx + dy * dy);
  }
  function thin(r) { return / · [\d.,]+ ?(m|km|ม\.|กม\.) /.test((r.nameEn || '') + ' ' + (r.name || '') + ' '); }
  function has(n, p) { return TH.test(p) ? n.indexOf(p) > -1 : (' ' + n + ' ').indexOf(' ' + p + ' ') > -1; }
  /* A place by a landmark's name, inside maxM metres, in a category a landmark can be in. The exact
     name wins, then the better known place, then the nearer. A car park "100 m from" a gate is not it. */
  function pick(lm, rows, maxM) {
    var best = null, bs = -1;
    rows.forEach(function (r) {
      if (r.lat == null || thin(r)) return;
      var cats = r.categories || [];
      if (cats.length && !cats.some(function (c) { return CAT[c]; })) return;
      var d = metres(lm.lat, lm.lng, +r.lat, +r.lng);
      if (d > maxM) return;
      var names = [norm(r.name), norm(r.nameEn)].filter(Boolean), hit = false, exact = false;
      names.forEach(function (n) {
        lm.ph.forEach(function (p) {
          if (has(n, p)) hit = true;
          if (n === p || n === 'the ' + p) exact = true;
        });
      });
      if (!hit) return;
      var s = 3 + (exact ? 5 : 0) + (cats.indexOf('sights') > -1 || cats.indexOf('wat') > -1 ? 1 : 0) + (r.antRank || 0) / 10 - d / maxM;
      if (s > bs) { bs = s; best = r; }
    });
    return best;
  }
  function reach(lm) { return lm.area ? 450 : 200; }
  function api(lm, q) {
    var h = lm.area ? 0.004 : 0.0015, u = ORIGIN + 'api/v1/places?' + (q ? 'q=' + encodeURIComponent(q) + '&' : '') +
      'bbox=' + [lm.lng - h, lm.lat - h, lm.lng + h, lm.lat + h].map(function (v) { return v.toFixed(4); }).join(',') + '&limit=' + (q ? 12 : 100);
    return fetch(u).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) { return d.results || []; });
  }
  function store(k, v) { try { var o = JSON.parse(localStorage.getItem('md-doodle-res') || '{}'); if (v === undefined) return o[k]; o[k] = v; localStorage.setItem('md-doodle-res', JSON.stringify(o)); } catch (e) {} }
  /* [place id, url, lat, lng, saved-at] or 0 for none; a find is kept 3 days, a miss 1 day */
  function resolve(map, lm) {
    if (lm.id in MEM) return Promise.resolve(MEM[lm.id]);
    var c = store(lm.id), now = Date.now();
    if (c && c.length && now - c[4] < 3 * 864e5) return Promise.resolve((MEM[lm.id] = { id: c[0], url: c[1], lat: c[2], lng: c[3] }));
    if (c && c.miss && now - c.miss < 864e5) return Promise.resolve((MEM[lm.id] = null));
    var near = [];
    if (window.MDPINS && MDPINS.row) for (var i = 0; i < 400; i++) { var r = MDPINS.row(map, i); if (!r) break; near.push(r); }
    var m = pick(lm, near, reach(lm));
    /* by its Thai name, its English name, then every place in the box; three calls at most */
    var qs = [lm.th, lm.en, ''];
    function ask(i) {
      if (i >= qs.length) return Promise.resolve(null);
      return api(lm, qs[i]).then(function (rs) { return pick(lm, rs, reach(lm)) || ask(i + 1); });
    }
    var p = m ? Promise.resolve(m) : ask(0);
    return p.then(function (r) {
      var v = r ? { id: r.id, url: String(r.url || '').replace(/^https?:\/\/[^/]+\//, '/'), lat: +r.lat, lng: +r.lng } : null;
      MEM[lm.id] = v;
      store(lm.id, v ? [v.id, v.url, v.lat, v.lng, now] : { miss: now });
      return v;
    }, function () { return undefined; });   // a failed call is tried again at the next move
  }

  /* ---- the drawing as a map image: ink on a cream edge, standing on its point ---- */
  function addImg(map, id) {
    var name = 'mdd-' + id;
    if (map.hasImage(name)) return Promise.resolve(true);
    return new Promise(function (ok) {
      var im = new Image();
      im.crossOrigin = 'anonymous';
      im.onload = function () {
        try {
          var R = Math.min(3, Math.max(2, window.devicePixelRatio || 1)), P = 4;
          var W = Math.round((PX + 2 * P) * R), H = Math.round((PX + P) * R), s = Math.round(PX * R), x0 = Math.round(P * R), y0 = Math.round(P * R);
          var t = document.createElement('canvas'); t.width = s; t.height = s;
          var tx = t.getContext('2d'); tx.drawImage(im, 0, 0, s, s);
          tx.globalCompositeOperation = 'source-in'; tx.fillStyle = '#FFFCF6'; tx.fillRect(0, 0, s, s);
          var c = document.createElement('canvas'); c.width = W; c.height = H;
          var cx = c.getContext('2d'), e = Math.round(1.6 * R);
          [[-e, 0], [e, 0], [0, -e], [0, e], [-e, -e], [e, -e], [-e, e], [e, e]].forEach(function (o) { cx.drawImage(t, x0 + o[0], y0 + o[1]); });
          cx.drawImage(im, x0, y0, s, s);
          if (!map.hasImage(name)) map.addImage(name, cx.getImageData(0, 0, W, H), { pixelRatio: R });
          ok(true);
        } catch (err) { ok(false); }
      };
      im.onerror = function () { ok(false); };
      im.src = window.MDDOODLES.url(id);
    });
  }

  function lang() {
    var h = document.documentElement, c = h.classList, l = h.getAttribute('data-lang') || h.lang || '';
    return c.contains('lang-en') || /^en/.test(l) && !c.contains('lang-th') ? 'en' : c.contains('lang-th') || /^th/.test(l) ? 'th' : '';
  }
  function label(lm) { var L = lang(); return L === 'en' ? lm.en : L === 'th' ? lm.th : lm.th + '\n' + lm.en; }

  /* ---- one map ---- */
  function attach(map, el) {
    if (!map || ATT.has(map)) return;
    if (el && el.hasAttribute && el.hasAttribute('data-mdpins-own')) return;
    if (/^\/sites\/doodle/.test(location.pathname)) return;
    ATT.add(map);
    var own = el && el.id !== 'xmap' && el.querySelector && el.querySelector('.mdmap-draw') && isFinite(parseFloat(el.dataset.lat)) ?
      [parseFloat(el.dataset.lat), parseFloat(el.dataset.lng)] : null;
    var shown = {};            // landmark id → {lm, place}
    var busy = false, again = false, timer = 0, made = false, lastPins = null, orig = null;

    function ensureLayer() {
      if (made) return true;
      if (!map.isStyleLoaded || map.getSource('md-doodles')) { made = !!map.getSource('md-doodles'); return made; }
      var phone = map.getContainer().clientWidth < 640, k = phone ? 0.9 : 1;
      map.addSource('md-doodles', { type: 'geojson', data: EMPTY });
      var lay = { id: 'md-doodles', type: 'symbol', source: 'md-doodles', minzoom: MINZ, layout: {
        'icon-image': ['concat', 'mdd-', ['get', 'd']], 'icon-anchor': 'bottom', 'icon-allow-overlap': true,
        'icon-size': ['interpolate', ['linear'], ['zoom'], 11, 0.5 * k, 13, 0.6 * k, 16, 0.78 * k, 18, 0.84 * k] } };
      if (window.MDMAP_CFG && MDMAP_CFG.glyphs) {
        var font = ['NotoSans'];
        ((MDMAP_CFG.layers) || []).some(function (l) { if (l.type === 'symbol' && l.layout && l.layout['text-font']) { font = l.layout['text-font']; return true; } });
        lay.layout['text-field'] = ['get', 'n']; lay.layout['text-font'] = font; lay.layout['text-size'] = 12;
        lay.layout['text-max-width'] = 9; lay.layout['text-anchor'] = 'top'; lay.layout['text-offset'] = [0, 0.1];
        lay.layout['text-optional'] = true; lay.layout['text-justify'] = 'center';
        lay.paint = { 'text-color': '#2b2118', 'text-halo-color': '#FFFCF6', 'text-halo-width': 1.6 };
      }
      /* just above the pins, under what a page adds after them */
      var ls = map.getStyle().layers || [], at = -1;
      for (var i = 0; i < ls.length; i++) if (ls[i].id === 'md-pins') at = i;
      map.addLayer(lay, at > -1 && ls[at + 1] ? ls[at + 1].id : undefined);
      made = true;
      /* the pin of a place that is drawn gives way */
      var src = map.getSource('md-pins');
      if (src && src.setData && !src.__mdd) {
        orig = src.setData.bind(src);
        src.setData = function (d, w) { lastPins = d; return orig(thinPins(d), w); };
        src.__mdd = 1;
        if (window.MDPINS && MDPINS.mute) MDPINS.mute(map, '_', false);   // the pins redraw through the wrapper
      }
      map.on('click', 'md-doodles', tap);
      map.on('mouseenter', 'md-doodles', function () { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'md-doodles', function () { map.getCanvas().style.cursor = ''; });
      return true;
    }
    function drawn(r) {
      for (var k in shown) {
        var p = shown[k].place, lm = shown[k].lm;
        if (r.id === p.id) return true;
        /* the same place under another record: close by, and named alike */
        if (metres(p.lat, p.lng, +r.lat, +r.lng) < 40 && !thin(r)) {
          var n = [norm(r.name), norm(r.nameEn)];
          if (n.some(function (x) { return x && lm.ph.some(function (q) { return has(x, q); }); })) return true;
        }
      }
      return false;
    }
    function thinPins(d) {
      if (!d || !d.features || !Object.keys(shown).length || !window.MDPINS || !MDPINS.row) return d;
      return { type: 'FeatureCollection', features: d.features.filter(function (f) {
        var r = MDPINS.row(map, f.properties && f.properties.i); return !(r && drawn(r)); }) };
    }
    function paint() {
      var fs = [];
      Object.keys(shown).forEach(function (k) {
        var s = shown[k];
        fs.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [s.place.lng, s.place.lat] }, properties: { d: s.lm.id, n: label(s.lm) } });
      });
      var s = map.getSource('md-doodles'); if (s) s.setData({ type: 'FeatureCollection', features: fs });
      var p = map.getSource('md-pins');
      if (p && orig && lastPins) orig(thinPins(lastPins));
    }
    function tap(e) {
      var f = e.features && e.features[0]; if (!f) return;
      var s = shown[f.properties.d]; if (!s) return;
      var L = lang(), it = { name: (L === 'th' ? s.lm.th : L === 'en' ? s.lm.en : s.lm.th + ' · ' + s.lm.en), sub: '',
        href: s.place.url, json: s.place.url.replace(/\.html$/, '.json'), lat: s.place.lat, lng: s.place.lng };
      if (window.MDX && MDX.el === el && MDX.openItem) { MDX.openItem(it); return; }
      if (window.MDCARD) { MDCARD.show(it, el); return; }
      if (it.href) location.href = it.href;
    }
    function scan() {
      if (map.getZoom() < MINZ) return;
      if (busy) { again = true; return; }
      busy = true;
      var b = map.getBounds(), padLat = (b.getNorth() - b.getSouth()) * 0.08, padLng = (b.getEast() - b.getWest()) * 0.08;
      lib().then(function (lms) {
        var inView = lms.filter(function (m) {
          return m.lat > b.getSouth() - padLat && m.lat < b.getNorth() + padLat && m.lng > b.getWest() - padLng && m.lng < b.getEast() + padLng; });
        var todo = inView.filter(function (m) { return !(m.id in shown) && !(m.id in MEM && !MEM[m.id]); });
        return Promise.all(todo.slice(0, 6).map(function (m) {
          return resolve(map, m).then(function (pl) {
            if (!pl) return;
            if (own && Math.abs(pl.lat - own[0]) < 3e-4 && Math.abs(pl.lng - own[1]) < 3e-4) return;
            return addImg(map, m.id).then(function (ok) { if (ok && ensureLayer()) shown[m.id] = { lm: m, place: pl }; });
          });
        })).then(function () { if (made) paint(); });
      }).catch(function () {}).then(function () { busy = false; if (again) { again = false; later(); } });
    }
    function later() { clearTimeout(timer); timer = setTimeout(scan, 300); }
    map.on('moveend', later);
    new MutationObserver(function () { if (made) paint(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['class', 'data-lang'] });
    later();
  }

  /* a drawn landmark answers a tap before the shelf under it does (explore.js asks MDPINS.hit first) */
  function hookHit() {
    if (!window.MDPINS || MDPINS.__mdd) return;
    var h = MDPINS.hit;
    MDPINS.hit = function (map, pt) {
      if (h && h(map, pt)) return true;
      return map.getLayer('md-doodles') ? map.queryRenderedFeatures([[pt.x - 14, pt.y - 20], [pt.x + 14, pt.y + 4]], { layers: ['md-doodles'] }).length > 0 : false;
    };
    MDPINS.__mdd = 1;
  }

  function all() {
    if (!window.MDMAP) return;
    document.querySelectorAll('[data-mdmap]').forEach(function (el) {
      window.MDMAP.ready(el, function (m) { hookHit(); attach(m, el); });
    });
  }

  window.MDDOODLEMAP = { attach: function (m, el) { hookHit(); attach(m, el); }, pick: pick, prep: prep, norm: norm };
  /* loaded by itself on a page with maps */
  if (window.MDMAP) all();
  else addEventListener('load', all);
})();
