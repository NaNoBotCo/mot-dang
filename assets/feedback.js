/* feedback.js — a thumb up, a thumb down and an optional paragraph on any item (Nan, 2026-10-11).
   Sends to POST /feedback on the claims Worker (worker/worker.js, putFeedback).

     MDFB.html(item, opts)   markup for the control; opts {label: [th, en], counts: true}
     MDFB.scan(root)         fills every empty <div data-fb="item"> under root (default: document)
     MDFB.send(item, o)      o {x: 1|-1|0, note: "…"}; resolves to the Worker's answer
     MDFB.mine(item)         this browser's vote on the item: 1, -1 or 0

   An item is a short id: place:<id>, shelf:<cat/sub>, site:<slug>, event:<key>, festival:<key>.
   One delegated click handler, one submit handler and one input handler sit on document, so markup
   inserted later works without wiring. The vote and a random reader id live in localStorage
   (md-fb:<item>, md-fb-who); a vote replaces this browser's earlier one on the Worker. */
(function () {
  if (window.MDFB) return;
  var API = 'https://mot-dang-claims.nanobotco.workers.dev';
  var ITEM_RE = /^[A-Za-z0-9:_\-.\/]{1,120}$/;
  var de = document.documentElement, who = '';

  function ls(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      localStorage.setItem(k, v);
    } catch (e) {}
    return null;
  }
  function rand() {
    var a = [], i;
    try { var u = new Uint8Array(16); crypto.getRandomValues(u); for (i = 0; i < 16; i++) a.push(('0' + u[i].toString(16)).slice(-2)); }
    catch (e) { for (i = 0; i < 16; i++) a.push(('0' + Math.floor(Math.random() * 256).toString(16)).slice(-2)); }
    return a.join('');
  }
  function me() {
    if (!who) { who = ls('md-fb-who') || ''; }
    if (!/^[A-Za-z0-9_-]{8,64}$/.test(who)) { who = rand(); ls('md-fb-who', who); }
    return who;
  }
  function bi(th, en) { return '<span class="bi"><span class="th" lang="th">' + th + '</span><span class="en" lang="en">' + en + '</span></span>'; }
  function lang() { return de.classList.contains('lang-en') || de.getAttribute('data-lang') === 'en' || de.classList.contains('en') ? 'en' : de.lang === 'en' ? 'en' : 'th'; }
  function state(item) {
    try { var s = JSON.parse(ls('md-fb:' + item) || '{}') || {}; return { x: s.x === 1 || s.x === -1 ? s.x : 0, n: !!s.n }; }
    catch (e) { return { x: 0, n: false }; }
  }
  function keep(item, s) { ls('md-fb:' + item, JSON.stringify(s)); }
  function icon(n) {
    var a = de.getAttribute('data-icons'), href = (a == null ? '/icons.svg' : a).split('#')[0];
    return '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><use href="' + href + '#i-thumb-' + n + '"></use></svg>';
  }

  var CSS = '.mdfb{display:flex;flex-wrap:wrap;align-items:center;gap:.1rem .3rem;margin:1.1rem 0 .4rem;font-size:.85rem;line-height:1.4;color:var(--mute,inherit)}' +
    '.mdfb .bi .th,.mdfb .bi .en{display:inline}' +
    'html.lang-en .mdfb .th,html[data-lang="en"] .mdfb .th,html.en .mdfb .th,html[lang="en"]:not(.lang-both) .mdfb .th{display:none}' +
    'html.lang-th .mdfb .en,html[data-lang="th"] .mdfb .en,html.th .mdfb .en{display:none}' +
    'html.lang-both .mdfb .bi .th+.en:before{content:"\\00a0\\00b7\\00a0"}' +
    '.mdfb-l{margin-right:.2rem}' +
    '.mdfb-b{appearance:none;-webkit-appearance:none;display:inline-flex;align-items:center;justify-content:center;gap:.25rem;min-width:36px;height:36px;padding:0 .45rem;margin:0;background:none;border:1px solid transparent;border-radius:999px;color:inherit;font:inherit;opacity:.55;cursor:pointer}' +
    '.mdfb-b svg{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}' +
    '.mdfb-b:hover,.mdfb-b:focus-visible{opacity:1;border-color:var(--rule,currentColor)}' +
    '.mdfb-b:focus-visible,.mdfb-s:focus-visible,.mdfb-x:focus-visible,.mdfb-f textarea:focus-visible{outline:2px solid var(--link,currentColor);outline-offset:2px}' +
    '.mdfb-b[aria-pressed="true"]{opacity:1;color:var(--ink,currentColor);border-color:var(--rule,currentColor)}' +
    '.mdfb-b[aria-pressed="true"] svg{fill:currentColor;fill-opacity:.2}' +
    '.mdfb-f{flex:1 1 100%;display:flex;flex-wrap:wrap;gap:.4rem;align-items:flex-start;margin:.2rem 0 0}' +
    '.mdfb-f[hidden]{display:none}' +
    '.mdfb-f textarea{flex:1 1 12rem;min-width:0;min-height:2.4rem;max-height:9rem;resize:vertical;margin:0;padding:.4rem .55rem;font:inherit;font-size:16px;line-height:1.4;color:var(--ink,inherit);background:var(--card,transparent);border:1px solid var(--rule,currentColor);border-radius:8px}' +
    '.mdfb-s,.mdfb-x{appearance:none;-webkit-appearance:none;min-height:36px;margin:0;padding:0 .8rem;font:inherit;color:var(--ink,inherit);background:none;border:1px solid var(--rule,currentColor);border-radius:999px;cursor:pointer}' +
    '.mdfb-x{padding:0 .6rem;border-color:transparent;opacity:.6;font-size:1.3rem;line-height:1}' +
    '.mdfb-x:hover{opacity:1}' +
    '.mdfb-t{flex:1 1 100%;min-height:0}' +
    '.mdfb-t:empty{display:none}' +
    '@media(max-width:640px){.mdfb-b{min-width:44px;height:44px}.mdfb-s,.mdfb-x{min-height:44px}}';
  function css() {
    if (document.getElementById('mdfb-css') || !document.head) return;
    var s = document.createElement('style'); s.id = 'mdfb-css'; s.textContent = CSS; document.head.appendChild(s);
  }

  var GOOD = 'ดี · Good', BAD = 'ไม่ดี · Not good';
  function html(item, opts) {
    if (!ITEM_RE.test(item || '')) return '';
    css();
    opts = opts || {};
    var c = opts.counts ? '<span class="mdfb-c"></span>' : '', cur = state(item).x;
    return '<div class="mdfb" data-fb="' + item + '" data-fb-ready="1"' + (opts.counts ? ' data-fb-counts="1"' : '') +
      ' role="group" aria-label="ความเห็นต่อรายการนี้ · Feedback on this item">' +
      (opts.label ? '<span class="mdfb-l">' + bi(opts.label[0], opts.label[1]) + '</span>' : '') +
      '<button type="button" class="mdfb-b" data-fbx="1" aria-pressed="' + (cur === 1) + '" aria-label="' + GOOD + '" title="' + GOOD + '">' + icon('up') + c + '</button>' +
      '<button type="button" class="mdfb-b" data-fbx="-1" aria-pressed="' + (cur === -1) + '" aria-label="' + BAD + '" title="' + BAD + '">' + icon('down') + c + '</button>' +
      '<form class="mdfb-f" hidden>' +
      '<textarea rows="1" maxlength="2000" aria-label="เล่าเพิ่มได้ (ไม่บังคับ) · Add a note (optional)" placeholder="ไม่บังคับ · Optional note"></textarea>' +
      '<button type="submit" class="mdfb-s">' + bi('ส่ง', 'Send') + '</button>' +
      '<button type="button" class="mdfb-x" data-fbclose aria-label="ปิด · Close">×</button>' +
      '</form><span class="mdfb-t" role="status" aria-live="polite"></span></div>';
  }

  function all(item) { return document.querySelectorAll('.mdfb[data-fb="' + item + '"]'); }
  function paint(item, tally) {
    var s = state(item), els = all(item);
    for (var i = 0; i < els.length; i++) {
      var b = els[i].querySelectorAll('.mdfb-b');
      for (var j = 0; j < b.length; j++) {
        b[j].setAttribute('aria-pressed', String(+b[j].getAttribute('data-fbx') === s.x));
        if (tally) { var n = b[j].querySelector('.mdfb-c'); if (n) n.textContent = tally[+b[j].getAttribute('data-fbx') > 0 ? 'up' : 'down'] || ''; }
      }
    }
  }
  function say(root, th, en) { var t = root.querySelector('.mdfb-t'); if (t) t.innerHTML = th ? bi(th, en) : ''; }

  function send(item, o) {
    o = o || {};
    var body = { item: item, who: me(), page: location.pathname.slice(0, 300), lang: lang() };
    if (o.x === 1 || o.x === -1 || o.x === 0) body.x = o.x;
    if (o.note) body.note = o.note;
    return fetch(API + '/feedback', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }); });
  }
  function failed(root, j) {
    if (j && j.status === 429) say(root, 'ลองใหม่ภายหลัง', 'Try again later');
    else say(root, 'ส่งไม่สำเร็จ', 'Not sent');
  }

  /* an empty <div data-fb="item"> becomes the control */
  function hydrate(el) {
    if (el.getAttribute('data-fb-ready')) return;
    var item = el.getAttribute('data-fb');
    if (!ITEM_RE.test(item || '')) return;
    var tmp = document.createElement('div');
    tmp.innerHTML = html(item, { counts: el.getAttribute('data-fb-counts') === '1' });
    var fresh = tmp.firstChild;
    el.setAttribute('data-fb-ready', '1');
    el.className = (el.className ? el.className + ' ' : '') + 'mdfb';
    el.setAttribute('role', 'group');
    el.setAttribute('aria-label', fresh.getAttribute('aria-label'));
    while (fresh.firstChild) el.appendChild(fresh.firstChild);
  }
  /* fills the placeholders under root, and fetches the tallies of controls made with counts */
  function scan(root) {
    css();
    root = root || document;
    var list = root.querySelectorAll('[data-fb]:not([data-fb-ready])'), i;
    for (i = 0; i < list.length; i++) hydrate(list[i]);
    var shown = root.querySelectorAll('.mdfb[data-fb-counts="1"]:not([data-fb-seen])');
    for (i = 0; i < shown.length; i++) {
      (function (el) {
        var item = el.getAttribute('data-fb');
        el.setAttribute('data-fb-seen', '1');
        fetch(API + '/feedback-tally?item=' + encodeURIComponent(item)).then(function (r) { return r.json(); })
          .then(function (j) { if (j && j.ok) paint(item, j); }).catch(function () {});
      })(shown[i]);
    }
  }

  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    var x = t.closest('[data-fbclose]');
    if (x) { var f0 = x.closest('.mdfb').querySelector('.mdfb-f'); if (f0) f0.hidden = true; return; }
    var b = t.closest('.mdfb-b[data-fbx]');
    if (!b) return;
    var root = b.closest('.mdfb'), item = root.getAttribute('data-fb'), s = state(item), v = +b.getAttribute('data-fbx');
    var nx = s.x === v ? 0 : v, was = s;
    keep(item, { x: nx, n: false });
    paint(item); say(root, '', '');
    var f = root.querySelector('.mdfb-f');
    if (f) { f.hidden = nx === 0; if (nx) { var ta = f.querySelector('textarea'); if (ta) ta.focus(); } }
    send(item, { x: nx }).then(function (j) {
      if (j && j.ok) { if (root.getAttribute('data-fb-counts') === '1') paint(item, j.tally); }
      else { keep(item, was); paint(item); if (f) f.hidden = true; failed(root, j); }
    }).catch(function () { keep(item, was); paint(item); if (f) f.hidden = true; failed(root, null); });
  });

  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (!f || !f.classList || !f.classList.contains('mdfb-f')) return;
    ev.preventDefault();
    var root = f.closest('.mdfb'), item = root.getAttribute('data-fb'), ta = f.querySelector('textarea'), note = ta.value.trim();
    if (!note) { f.hidden = true; return; }
    var s = state(item), btn = f.querySelector('.mdfb-s');
    btn.disabled = true;
    send(item, { x: s.x, note: note }).then(function (j) {
      btn.disabled = false;
      if (j && j.ok) { ta.value = ''; ta.style.height = ''; f.hidden = true; keep(item, { x: s.x, n: true }); say(root, 'ขอบคุณ', 'Thanks'); }
      else failed(root, j);
    }).catch(function () { btn.disabled = false; failed(root, null); });
  });

  document.addEventListener('input', function (ev) {
    var ta = ev.target;
    if (!ta || !ta.closest || !ta.closest('.mdfb-f')) return;
    ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight + 2, 144) + 'px';
  });
  document.addEventListener('keydown', function (ev) {
    var ta = ev.target;
    if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey) && ta && ta.closest && ta.closest('.mdfb-f') && ta.form && ta.form.requestSubmit) ta.form.requestSubmit();
  });

  window.MDFB = { html: html, scan: scan, send: send, mine: function (item) { return state(item).x; } };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(); });
  else scan();
})();
