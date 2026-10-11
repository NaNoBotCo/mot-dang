/* The doodle repository's one way to draw any record, bundled with the engine it was drawn by
   (tools/doodle_repo.py → data/doodles/engines/<hash>.js; this file lives in assets/doodles-app/), so an old version replays with its
   own code. A record: { id, c: front|place|minisite|scene|cover, p: params }.

   MDREPO.draw(cv, rec, t, ridge, now)   one frame; cv._dpr is the canvas scale (default 1)
   MDREPO.aspect(rec)                    width / height
   MDREPO.fp(rec, ridge)                 a fingerprint of two small frames: a new value is a new version */
(function () {
  var NOW = Date.parse('2026-01-15T11:00:00+07:00');   /* places and scenes are fingerprinted under one sky */
  function aspect(r) { return r.c === 'place' ? 2 : (r.c === 'cover' || (r.c === 'minisite' && r.p.lib === 'dd')) ? 1200 / 630 : 1000 / 440; }
  function draw(cv, r, t, ridge, now) {
    var DD = window.MDDOODLER, d = cv._dpr || 1, c = cv.getContext('2d'), W = cv.width / d, H = cv.height / d, p = r.p;
    c.setTransform(d, 0, 0, d, 0, 0);
    if (r.c === 'front') return window.MDREPLAY.draw(cv, p, t, ridge);
    if (r.c === 'place') return DD.portrait(c, W, H, t, { set: p.set, place: p.f, ridge: ridge, now: now });
    if (r.c === 'cover' || (r.c === 'minisite' && p.lib === 'dd')) return window.MDDOODLES.draw(p.k, c, W, H, t, null, ridge);
    var set = p.set || p.k;
    return DD.full(c, W, H, t, { set: set, variant: p.variant || '', seed: DD.hash(r.id), ridge: ridge, night: false, now: now || NOW, lat: 18.79, lng: 98.99 });
  }
  function fp(r, ridge) {
    var cv = fp.cv || (fp.cv = document.createElement("canvas")), w = 360, h = Math.round(w / aspect(r)), x = 2166136261, i, k, px;
    cv.width = w; cv.height = h; cv._dpr = 1;
    for (k = 0; k < 2; k++) {
      cv.getContext('2d').clearRect(0, 0, w, h);
      draw(cv, r, k ? 4200 : 1200, ridge, NOW);
      px = cv.getContext('2d').getImageData(0, 0, w, h).data;
      for (i = 0; i < px.length; i += 16) { x ^= px[i] >> 3; x = Math.imul(x, 16777619); x ^= px[i + 1] >> 3; x = Math.imul(x, 16777619); x ^= px[i + 2] >> 3; x = Math.imul(x, 16777619); }
    }
    return ('0000000' + (x >>> 0).toString(16)).slice(-8);
  }
  window.MDREPO = { draw: draw, aspect: aspect, fp: fp, NOW: NOW };
})();
