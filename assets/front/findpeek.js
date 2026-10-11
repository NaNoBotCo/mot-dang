/* findpeek.js — a look at a place without leaving the list (Nan, 2026-10-04: "Not enough
   preview anywhere. Not enough magic!"). On the search page (publish/findpreview.js marks each
   row) and on shelf, tag and list pages (build.py entry_li):

   · peek: the eye button, a long press on a phone, or a pause of the pointer on a desktop opens
     a card — the place's picture, or the auto-doodler's drawing of it from its own facts when
     it has none; its name in both scripts and the reading; the lamp and its hours; where it
     stands; how to reach it; the page, the map, a ride.
   · drawn thumbnails: a row whose place has no photograph gets the same drawing, painted once
     when it scrolls into view and the browser is idle (not on a data-saver connection).

   Facts come from the place's own .json twin, fetched on demand. Holds still for readers who
   ask for less motion. */
(function () {
'use strict';
if (window.MDPEEK) return;
var d = document, html = d.documentElement;
var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
var HOVER = window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches;
var NET = navigator.connection || {};
var LEAN = !!(NET.saveData || /(^|-)2g$/.test(NET.effectiveType || ''));
var SRC = (d.currentScript && d.currentScript.src) || '';
var BASE = SRC ? SRC.replace(/findpeek\.js(\?.*)?$/, '') : '/front/';
var HOME = /(^|\.)motdang\.net$/.test(location.hostname) ? '' : 'https://motdang.net';
var LANG = (function () {
  var l; try { l = localStorage.getItem('md-lang'); } catch (e) { }
  if (l === 'th' || l === 'en') return l;
  if (html.classList.contains('lang-en')) return 'en';
  if (html.classList.contains('lang-th')) return 'th';
  return /^th/i.test(navigator.language || '') ? 'th' : 'en';
})();
var TH = /[฀-๿]/;
function t(th, en) { return LANG === 'th' ? th : en; }
function el(tag, cls, txt) { var e = d.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

/* ------------------------------------------------------------ the place's twin */
var TWINS = {};
function twinUrl(u) {
  if (!u) return '';
  var a = d.createElement('a'); a.href = u;
  if (!/(^|\.)motdang\.net$/.test(a.hostname) && a.hostname !== location.hostname) return '';
  var m = /^\/((?:cm|cr)\/p\/[^\/?#]+)\.html$/.exec(a.pathname);
  return m ? HOME + '/' + m[1] + '.json' : '';
}
function twin(u) {
  var j = twinUrl(u);
  if (!j) return Promise.resolve(null);
  if (!TWINS[j]) TWINS[j] = fetch(j).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  return TWINS[j];
}
/* what the portrait draws from — the fields doodles_layer.place_facts hands a place page */
function facts(r) {
  var a = r.attrs || {};
  var f = { id: r.id, name: r.name, nameTh: r.nameTh || r.name, nameEn: r.nameEn, cat: (r.cat || [''])[0], sub: r.sub || [],
    brand: a.brand, hours: r.hours, road: a.road, moo: a.moo, tambon: a.tambon, amphoe: a.amphoe, oldCity: !!a.inOldCity,
    inside: a.insideOf, services: Array.isArray(a.services) ? a.services : [], levels: a.levels, facility: a.facilityType,
    province: r.province, lat: r.lat, lng: r.lng, t: 0 };
  f.cuisine = (r.sub || []).filter(function (s) { return s !== 'cafe' && s !== 'bar-pub'; });
  if (a.riverName && a.riverM != null) f.river = { name: a.riverName, m: a.riverM };
  return f;
}

/* ------------------------------------------------------------ the doodler, on demand */
var DOODLER = null;
function script(src) {
  return new Promise(function (ok, no) { var s = d.createElement('script'); s.src = src; s.async = true; s.onload = ok; s.onerror = no; d.head.appendChild(s); });
}
function doodler() {
  if (window.MDDOODLER) return Promise.resolve(window.MDDOODLER);
  if (!DOODLER) DOODLER = (window.SKY ? Promise.resolve() : script(BASE + 'skyline.js'))
    .then(function () { return script(BASE + 'doodler.js'); })
    .then(function () { return window.MDDOODLER; }).catch(function () { return null; });
  return DOODLER;
}
var PAINTED = [];
/* one canvas, one place: sized to its box, painted at time ms; repainted when a scene file lands */
function paint(cv, set, place, ms) {
  var D = window.MDDOODLER; if (!D) return;
  var W = cv.clientWidth, H = cv.clientHeight; if (!W || !H) return;
  var dpr = Math.min(2, window.devicePixelRatio || 1), c = cv.getContext('2d');
  if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
  try { D.portrait(c, W, H, ms, { set: set, place: place }); } catch (e) { }
}
addEventListener('mddoodler', function () {
  PAINTED.forEach(function (p) { if (p.cv.isConnected) paint(p.cv, p.set, p.place, p.ms); });
});
/* what each kind of drawing shows (data/curated/doodle_alt.json, written to front/ by doodles_layer.py) */
var ALT = null;
function alts() {
  if (!ALT) ALT = fetch(BASE + 'doodle_alt.json').then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
  return ALT;
}
function drawInto(box, set, rec, ms) {
  var cv = el('canvas'); cv.setAttribute('role', 'img');
  var nm = rec.nameTh || rec.name || '', en = rec.nameEn || nm;
  cv.setAttribute('aria-label', t('ภาพวาด ' + nm, 'Drawing of ' + en));
  alts().then(function (A) { var a = A[set]; if (a && a[0]) cv.setAttribute('aria-label', t('ภาพวาด ' + nm + ': ' + a[0], 'Drawing of ' + en + ': ' + a[1])); });
  box.appendChild(cv);
  var place = facts(rec), p = { cv: cv, set: set, place: place, ms: ms };
  PAINTED.push(p);
  paint(cv, set, place, ms);
  requestAnimationFrame(function () { cv.classList.add('in'); });
  return p;
}

/* ------------------------------------------------------------ drawn thumbnails */
function idle(f) { (window.requestIdleCallback || function (g) { setTimeout(g, 200); })(f, { timeout: 2500 }); }
function thumbs() {
  if (LEAN || !window.IntersectionObserver) return;
  var boxes = [].slice.call(d.querySelectorAll('.r[data-sc] > a.th, .pvp[data-sc]'))
    .filter(function (b) { var li = b.closest('.r[data-k]'); return !(li && li.dataset.ph && b.matches('a.th')); });
  if (!boxes.length) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      var box = e.target, li = box.closest('.r[data-k], .pvi'), u = urlOf(li) || box.getAttribute('href');
      var set = box.dataset.sc || (li && li.dataset.sc);
      idle(function () {
        Promise.all([twin(u), doodler()]).then(function (v) {
          if (!v[0] || !v[1]) return;
          /* the map moves to a round inset in the corner, so the drawing keeps the place's where */
          var img = box.querySelector('img'), pin = box.querySelector('i');
          if (img) { var ins = el('span', 'mdin'); ins.appendChild(img); if (pin) ins.appendChild(pin); box.appendChild(ins); }
          drawInto(box, set, v[0], 4000 + (u.length * 97) % 9000);
          if (img) box.appendChild(box.querySelector('.mdin'));
        });
      });
    });
  }, { rootMargin: '200px 0px' });
  boxes.forEach(function (b) { io.observe(b); });
}

/* ------------------------------------------------------------ hours, from the week's minutes */
function bkkMinute() { var b = new Date(Date.now() + 7 * 3600e3); return ((b.getUTCDay() + 6) % 7) * 1440 + b.getUTCHours() * 60 + b.getUTCMinutes(); }
function hh(m) { m = ((m % 1440) + 1440) % 1440; return ('0' + Math.floor(m / 60)).slice(-2) + ':' + ('0' + m % 60).slice(-2); }
var DAYS = [['จ.', 'Mon'], ['อ.', 'Tue'], ['พ.', 'Wed'], ['พฤ.', 'Thu'], ['ศ.', 'Fri'], ['ส.', 'Sat'], ['อา.', 'Sun']];
function lamp(iv) {
  if (!iv || !iv.length) return null;
  var m = bkkMinute(), W = 10080, i, a, b;
  for (i = 0; i < iv.length; i++) {
    a = iv[i][0]; b = iv[i][1];
    if ((m >= a && m < b) || (m + W >= a && m + W < b)) {
      if (b - a >= W) return { on: 1, txt: t('เปิด 24 ชม.', 'open 24 h') };
      var left = (m >= a && m < b ? b - m : b - m - W);
      return { on: 1, soon: left <= 60, txt: t('เปิดอยู่ ถึง ' + hh(b), 'open · closes ' + hh(b)) };
    }
  }
  var best = null;
  iv.forEach(function (x) { var ahead = ((x[0] - m) % W + W) % W; if (best === null || ahead < best[0]) best = [ahead, x[0] % W]; });
  var day = Math.floor(best[1] / 1440), today = Math.floor(m / 1440);
  var w = day === today && best[0] < 1440 ? ['', ''] : day === (today + 1) % 7 ? ['พรุ่งนี้ ', 'tomorrow '] : [DAYS[day][0] + ' ', DAYS[day][1] + ' '];
  return { on: 0, txt: t('เปิด ' + w[0] + hh(best[1]), 'opens ' + w[1] + hh(best[1])) };
}

/* ------------------------------------------------------------ the card */
var card = null, scrim = null, openFor = null, back = null, live = null, hideT = 0, showT = 0;
function sheet() { return !HOVER || innerWidth < 640; }
function build() {
  scrim = el('div', 'mdpk-scrim'); scrim.addEventListener('click', close);
  card = el('div', 'mdpk'); card.setAttribute('role', 'dialog'); card.setAttribute('aria-modal', 'false'); card.tabIndex = -1;
  card.addEventListener('mouseenter', function () { clearTimeout(hideT); });
  card.addEventListener('mouseleave', function () { if (!sheet()) hideT = setTimeout(close, 280); });
  var y0 = null;
  card.addEventListener('touchstart', function (e) { y0 = card.scrollTop <= 0 ? e.touches[0].clientY : null; }, { passive: true });
  card.addEventListener('touchmove', function (e) { if (y0 != null && e.touches[0].clientY - y0 > 70) { y0 = null; close(); } }, { passive: true });
  d.body.appendChild(scrim); d.body.appendChild(card);
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && openFor) close(); });
}
function close() {
  clearTimeout(showT); clearTimeout(hideT);
  if (!card || !openFor) return;
  card.classList.remove('on'); scrim.classList.remove('on');
  if (live) { live.stop = 1; live = null; }
  var was = openFor; openFor = null;
  if (back && back.focus && card.contains(d.activeElement)) back.focus();
  setTimeout(function () { if (!openFor) card.hidden = true; }, REDUCED ? 0 : 220);
  return was;
}
function place(rowEl, x, y) {
  if (sheet()) { card.className = 'mdpk sheet'; card.style.left = card.style.top = ''; return; }
  card.className = 'mdpk float';
  var r = rowEl.getBoundingClientRect(), w = Math.min(380, innerWidth - 24), h = card.offsetHeight || 420;
  var left = Math.min(innerWidth - w - 12, Math.max(12, (x || r.left) + 24));
  var top = Math.min(innerHeight - h - 12, Math.max(12, r.top));
  card.style.left = left + 'px'; card.style.top = top + 'px'; card.style.width = w + 'px';
}
function chip(href, label, cls, ext) {
  var a = el('a', 'mdpk-b' + (cls ? ' ' + cls : ''), label); a.href = href;
  if (ext) { a.target = '_blank'; a.rel = 'noopener'; }
  return a;
}
function rowFacts(li) {
  /* what the row itself says: its title, reading, picture, shelf */
  var a = li.tagName === 'A' ? li : li.querySelector('a.t') || li.querySelector('a[href]:not(.mdth):not(.th)');
  var nm = li.classList.contains('pvi') ? li.querySelector('.pvn') : a;
  var o = { url: li.dataset.u || (a && a.href) || '', title: nm ? (nm.firstChild && nm.firstChild.nodeValue || nm.textContent).split(' — ')[0].trim() : '' };
  var rd = li.querySelector('.rd, .pvn small, .rdth, .roman'); o.rd = li.dataset.rd || (rd ? rd.textContent.replace(/^[\s·]*(อ่านว่า|reads)?\s*/, '').trim() : '');
  var img = li.querySelector('a.th img, .pvp img, a.mdth img'); if (img) o.img = img.currentSrc || img.src;
  var pin = li.querySelector('a.th i, .pvp i'); if (pin) o.pin = pin.getAttribute('style');
  var cr = li.querySelector('.cr'); if (cr) o.crumb = cr.textContent.split('›').pop().trim();
  var ab = li.querySelector('.b'); o.abs = '';
  if (ab) { var tx = [].filter.call(ab.childNodes, function (n) { return n.nodeType === 3; }).map(function (n) { return n.nodeValue; }).join(' ').trim(); o.abs = tx; }
  var scEl = li.querySelector('[data-sc]'); o.sc = li.dataset.sc || (scEl && scEl.dataset.sc) || '';
  o.photo = !!li.dataset.ph || li.classList.contains('pvi') && !!li.querySelector('.pvp:not(.map) img') || !!li.querySelector('a.mdth.ph');
  o.kind = li.dataset.k || 'place';
  o.strip = li.querySelector('.pv');
  o.grab = li.querySelector('.ls-grab, .grabride');
  return o;
}
function fill(o, rec) {
  card.textContent = '';
  var x = el('button', 'mdpk-x', '×'); x.type = 'button'; x.setAttribute('aria-label', t('ปิด', 'Close')); x.addEventListener('click', close);
  card.appendChild(x);
  var fig = el('div', 'mdpk-pic');
  var ph = rec && rec.photo && rec.photo.url;
  if (ph) {
    var im = el('img'); im.alt = ''; im.decoding = 'async'; im.src = ph; fig.appendChild(im);
    if (rec.photo.author) fig.appendChild(el('small', 'mdpk-cr', '📷 ' + rec.photo.author + (rec.photo.license ? ' · ' + rec.photo.license : '')));
  } else if (o.photo && o.img) {
    var im2 = el('img'); im2.alt = ''; im2.src = o.img; fig.appendChild(im2);
  } else if (rec && o.sc && !LEAN) {
    fig.classList.add('drawn');
    doodler().then(function (D) {
      if (!D || openFor !== o.url) return;
      var p = drawInto(fig, o.sc, rec, 4000);
      fig.appendChild(el('small', 'mdpk-cr', t('ภาพวาดจากข้อมูลของที่นี่', 'drawn from what the record says')));
      if (!REDUCED) { live = p; (function f(ts) { if (p.stop || !p.cv.isConnected) return; p.ms = ts; paint(p.cv, p.set, p.place, ts); requestAnimationFrame(f); })(performance.now()); }
    });
  } else if (o.img) {
    fig.classList.add('map'); var im3 = el('img'); im3.alt = ''; im3.src = o.img; fig.appendChild(im3);
    if (o.pin) { var i = el('i'); i.setAttribute('style', o.pin); fig.appendChild(i); }
  } else fig = null;
  if (fig) card.appendChild(fig);

  var body = el('div', 'mdpk-in');
  var th = rec ? (rec.nameTh || (TH.test(rec.name || '') ? rec.name : '')) : '', en = rec ? (rec.nameEn || (!TH.test(rec.name || '') ? rec.name : '')) : '';
  var first = LANG === 'th' ? (th || en) : (en || th), second = LANG === 'th' ? (th && en && en !== th ? en : '') : (th && en && en !== th ? th : '');
  var h = el('h3', 'mdpk-h', first || o.title); body.appendChild(h);
  if (second) body.appendChild(el('div', 'mdpk-2', second));
  if (o.rd && (!th || !en) && (TH.test(o.rd) ? LANG === 'th' : LANG === 'en')) body.appendChild(el('div', 'mdpk-rd', t('อ่านว่า ', 'reads ') + o.rd));
  if (o.crumb) body.appendChild(el('div', 'mdpk-k', o.crumb));
  if (rec) {
    var L = lamp(rec.sched);
    if (L) { var lp = el('div', 'mdpk-lamp lamp ' + (L.on ? 'on' : 'off') + (L.soon ? ' soon' : ''), L.txt); body.appendChild(lp); }
    else if (rec.hours) body.appendChild(el('div', 'mdpk-l', '🕘 ' + rec.hours));
    (rec.bearings || []).slice(0, 2).forEach(function (b) { if (b && (b.th || b.en)) body.appendChild(el('div', 'mdpk-l mute', '📍 ' + (LANG === 'th' ? b.th : b.en || b.th))); });
    if (rec.address) body.appendChild(el('div', 'mdpk-l mute', rec.address));
    var pr = (rec.attrs || {}).priceRange; if (pr) body.appendChild(el('div', 'mdpk-l pr', '฿ ' + pr));
    var acts = el('div', 'mdpk-acts');
    acts.appendChild(chip(o.url, t('เปิดหน้า', 'Open page'), 'go'));
    (rec.channels || []).slice(0, 3).forEach(function (c) {
      var lab = { phone: t('โทร', 'Call'), line: 'LINE', facebook: 'Facebook', web: t('เว็บ', 'Website'), instagram: 'Instagram', whatsapp: 'WhatsApp', email: t('อีเมล', 'Email') }[c.kind];
      if (lab && c.href) acts.appendChild(chip(c.href, lab, '', !/^(tel|mailto):/.test(c.href)));
    });
    if (rec.lat != null && rec.province) {
      var slug = (o.url.match(/\/p\/([^\/?#]+)\.html/) || [])[1];
      if (slug) acts.appendChild(chip(HOME + '/map.html#17/' + (+rec.lat).toFixed(5) + '/' + (+rec.lng).toFixed(5) + '/' + rec.province + '-' + ((rec.cat || [''])[0]) + '/pin=' + rec.province + ':' + slug, t('แผนที่', 'Map')));
    }
    if (o.grab) { var g = o.grab.cloneNode(true); g.className = 'mdpk-b ' + g.className; acts.appendChild(g); }
    body.appendChild(acts);
  } else {
    if (o.abs) body.appendChild(el('p', 'mdpk-l', o.abs.slice(0, 220)));
    if (o.strip) { var s2 = o.strip.cloneNode(true); s2.className = 'pv mdpk-strip'; body.appendChild(s2); }
    var a2 = el('div', 'mdpk-acts'); a2.appendChild(chip(o.url, t('เปิดหน้า', 'Open page'), 'go')); body.appendChild(a2);
  }
  card.appendChild(body);
  card.setAttribute('aria-label', first || o.title || '');
}
function show(li, x, y, viaKey) {
  if (!card) build();
  clearTimeout(hideT);
  var o = rowFacts(li);
  if (openFor === o.url) return;
  openFor = o.url; back = viaKey ? d.activeElement : null;
  card.hidden = false; fill(o, null);
  place(li, x, y);
  requestAnimationFrame(function () { card.classList.add('on'); if (sheet()) scrim.classList.add('on'); if (viaKey) card.focus(); });
  twin(o.url).then(function (rec) {
    if (openFor !== o.url) return;
    if (rec || o.kind === 'list') { fill(o, rec); place(li, x, y); card.classList.add('on'); }
  });
}

/* ------------------------------------------------------------ the doors into it */
/* Nan, 2026-10-12: "The links should also contain preview information. Everywhere." Past the rows, any
   link to a place page on any page peeks the same way: the pointer resting on it, or a long press. */
function placeLink(n) {
  var a = n.closest('a[href]'); if (!a || a.closest('.mdpk, nav, header, .crumbs')) return null;
  return twinUrl(a.href) ? a : null;
}
function rowOf(n) {
  if (!n || !n.closest) return null;
  var pv = n.closest('.pvi'); if (pv && !pv.closest('.mdpk')) return pv;
  var li = n.closest('.r[data-k], ul.dir li[data-n]'); if (li && !li.closest('.mdpk')) return li;
  return placeLink(n);
}
function urlOf(li) {
  if (!li) return '';
  if (li.tagName === 'A') { li.dataset.u = li.href; }
  else if (li.classList.contains('pvi')) { li.dataset.u = li.getAttribute('href'); }
  else if (!li.dataset.u) { var a = li.querySelector('a.t') || li.querySelector('a[href*="/p/"]'); if (a) li.dataset.u = a.href; }
  return li.dataset.u;
}
d.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('.pk');
  if (!b) return;
  e.preventDefault();
  var li = b.closest('.r[data-k], li'); if (!li) return;
  urlOf(li);
  if (openFor && openFor === (li.dataset.u)) { close(); return; }
  var r = b.getBoundingClientRect(); show(li, r.left, r.top, e.detail === 0);
});
/* long press: 450 ms still, then the card; the click that follows does not open the link */
var lp = null, eat = false;
d.addEventListener('touchstart', function (e) {
  var li = rowOf(e.target); if (!li || e.touches.length > 1 || e.target.closest('button, .ls-acts, .pk')) return;
  var tch = e.touches[0];
  lp = { li: li, x: tch.clientX, y: tch.clientY, t: setTimeout(function () {
    if (!urlOf(li)) return;
    eat = true; if (navigator.vibrate) try { navigator.vibrate(8); } catch (er) { }
    show(li, lp.x, lp.y);
  }, 450) };
}, { passive: true });
function cancel(e) { if (!lp) return; var tch = e.touches && e.touches[0]; if (!tch || Math.abs(tch.clientX - lp.x) > 10 || Math.abs(tch.clientY - lp.y) > 10) { clearTimeout(lp.t); lp = null; } }
d.addEventListener('touchmove', cancel, { passive: true });
d.addEventListener('touchend', function (e) { if (lp) { clearTimeout(lp.t); lp = null; } if (eat) { e.preventDefault(); } }, { passive: false });
d.addEventListener('click', function (e) { if (eat) { eat = false; e.preventDefault(); e.stopPropagation(); } }, true);
d.addEventListener('contextmenu', function (e) { if (eat || (lp && rowOf(e.target))) e.preventDefault(); });
/* desktop: rest the pointer on a picture or a name */
if (HOVER) {
  d.addEventListener('mouseover', function (e) {
    var tg = e.target.closest && (e.target.closest('a.th, a.t, .pvi, a.mdth, ul.dir li[data-n] > a') || placeLink(e.target));
    if (!tg) return;
    var li = rowOf(tg); if (!li || !urlOf(li)) return;
    clearTimeout(showT); clearTimeout(hideT);
    var x = e.clientX, y = e.clientY;
    showT = setTimeout(function () { show(li, x, y); }, 520);
  });
  d.addEventListener('mouseout', function (e) {
    var tg = e.target.closest && (e.target.closest('a.th, a.t, .pvi, a.mdth, ul.dir li[data-n] > a') || placeLink(e.target));
    if (!tg) return;
    clearTimeout(showT);
    if (openFor && !(e.relatedTarget && card && card.contains(e.relatedTarget))) hideT = setTimeout(close, 380);
  });
}
addEventListener('scroll', function () { if (openFor && !sheet()) close(); }, { passive: true });

var css = el('style');
css.textContent = [
  '.mdpk{position:fixed;z-index:9000;background:#fffdf8;color:#1a1408;border:1px solid #c9b895;box-shadow:0 18px 40px rgba(40,25,5,.28),3px 4px 0 rgba(90,60,20,.18);font:15px/1.45 Georgia,Thonburi,serif;overflow:auto;opacity:0;transition:opacity .2s,transform .22s cubic-bezier(.2,.8,.2,1)}',
  '.mdpk[hidden]{display:none}',
  '.mdpk.float{border-radius:14px;max-height:calc(100vh - 24px);transform:translateY(6px) scale(.98)}',
  '.mdpk.sheet{left:0;right:0;bottom:0;max-height:82vh;border-radius:18px 18px 0 0;transform:translateY(40px);padding-bottom:env(safe-area-inset-bottom)}',
  '.mdpk.sheet::before{content:"";display:block;width:42px;height:5px;border-radius:3px;background:#c9b895;margin:8px auto 0}',
  '.mdpk.on{opacity:1;transform:none}',
  '.mdpk-scrim{position:fixed;inset:0;z-index:8999;background:rgba(26,20,8,.32);opacity:0;pointer-events:none;transition:opacity .2s}',
  '.mdpk-scrim.on{opacity:1;pointer-events:auto}',
  '.mdpk-x{position:absolute;right:8px;top:8px;z-index:2;width:34px;height:34px;border-radius:50%;border:1px solid #c9b895;background:rgba(255,253,248,.92);font-size:20px;line-height:1;cursor:pointer;color:#1a1408;margin:0;padding:0}',
  '.mdpk-pic{position:relative;aspect-ratio:2/1;background:#f2ebdc;overflow:hidden;margin:0}',
  '.mdpk.sheet .mdpk-pic{margin:8px 12px 0;border-radius:12px}',
  '.mdpk.float .mdpk-pic{border-radius:13px 13px 0 0}',
  '.mdpk-pic img{display:block;width:100%;height:100%;object-fit:cover}',
  '.mdpk-pic.map{aspect-ratio:auto;width:112px;height:112px;float:right;margin:12px 12px 6px 10px;border-radius:10px;border:1px solid #c9b895}',
  '.mdpk.sheet .mdpk-pic.map{margin:16px 14px 6px 10px}',
  '.mdpk-pic.map i{position:absolute;width:11px;height:11px;margin:-6px 0 0 -6px;border-radius:50%;background:#b3261e;border:2px solid #fff}',
  '.mdpk-pic canvas{position:absolute;inset:0;width:100%;height:100%;opacity:0;transition:opacity .5s}.mdpk-pic canvas.in{opacity:1}',
  '.mdpk-cr{position:absolute;left:8px;bottom:6px;right:8px;color:#fff;font-size:11px;text-shadow:0 1px 2px rgba(0,0,0,.7)}',
  '.mdpk-in{padding:12px 16px 16px}',
  '.mdpk-h{margin:0 40px 2px 0;font-size:1.25em;line-height:1.25}',
  '.mdpk-2{color:#5c4d38}.mdpk-rd{color:#7a4b12;font-style:italic}.mdpk-k{color:#5c4d38;font-size:.88em;margin:.2em 0 .35em}',
  '.mdpk-l{margin:.2em 0;font-size:.93em}.mdpk-l.mute{color:#5c4d38}.mdpk-l.pr{color:#0b6b3a}',
  '.mdpk-lamp{margin:.3em 0;font-size:.95em}',
  '.mdpk-acts{display:flex;flex-wrap:wrap;gap:.4em;margin-top:.7em;clear:both}',
  '.mdpk-b{display:inline-flex;align-items:center;gap:.3em;padding:.45em .85em;border:1px solid #c9b895;border-radius:1.4em;background:#fff;color:#1a1408;text-decoration:none;font-size:.92em}',
  '.mdpk-b.go{background:#b3261e;border-color:#b3261e;color:#fff}',
  '.mdpk-b svg{width:16px;height:16px}',
  '.mdpk-strip{margin:.6em 0 0}',
  '.pk::before{content:"";display:block;width:18px;height:18px;margin:auto;background:#7a4b12;-webkit-mask:var(--eye) center/contain no-repeat;mask:var(--eye) center/contain no-repeat}',
  ':root{--eye:url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27%3E%3Cpath d=%27M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z%27 fill=%27none%27 stroke=%27%23000%27 stroke-width=%271.8%27/%3E%3Ccircle cx=%2712%27 cy=%2712%27 r=%273.2%27/%3E%3C/svg%3E")}',
  '.pk:hover,.pk:focus-visible{background:#fbf3d9;border-color:#d8b24a}',
  '.lamp.on::before{animation:mdlamp 2.6s ease-in-out infinite}@keyframes mdlamp{50%{box-shadow:0 0 1em #19a64a,0 0 0 .25em rgba(25,166,74,.15)}}',
  '.th canvas,.pvp canvas{position:absolute;inset:0;width:100%;height:100%;opacity:0;transition:opacity .6s}.th canvas.in,.pvp canvas.in{opacity:1}',
  '.pvp{transition:transform .25s}.pvi:hover .pvp{transform:translateY(-2px) rotate(-.6deg)}',
  '.mdin{position:absolute;right:3px;bottom:3px;z-index:2;width:38%;height:38%;border-radius:50%;overflow:hidden;border:2px solid #fffdf8;box-shadow:0 1px 3px rgba(0,0,0,.35);background:#f2ebdc}',
  '.mdin img{display:block;width:100%;height:100%;object-fit:cover}',
  '.mdin i{position:absolute;width:6px!important;height:6px!important;margin:-3px 0 0 -3px!important;border-width:1px!important}',
  'a.mdth{position:relative;display:inline-block;vertical-align:middle;width:44px;height:44px;border-radius:8px;overflow:hidden;background:#f2ebdc;border:1px solid #c9b895;margin-right:.5em;flex:none}',
  'a.mdth img{display:block;width:100%;height:100%;object-fit:cover}',
  'a.mdth i{position:absolute;width:7px;height:7px;margin:-4px 0 0 -4px;border-radius:50%;background:#b3261e;border:1.5px solid #fff}',
  'a.mdth canvas{position:absolute;inset:0;width:100%;height:100%;opacity:0;transition:opacity .6s}a.mdth canvas.in{opacity:1}',
  '@media (prefers-reduced-motion: reduce){.mdpk,.mdpk-scrim,.mdpk-pic canvas,a.mdth canvas,.th canvas,.pvp canvas,.pvp{transition:none}.lamp.on::before{animation:none}.pvi:hover .pvp{transform:none}}'
].join('\n');
d.head.appendChild(css);

window.MDPEEK = { show: show, close: close, twin: twin };
if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', thumbs); else thumbs();
})();
