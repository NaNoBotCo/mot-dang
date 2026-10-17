/* Burmese and Shan for the interface (WO-112). Loaded by md.js when a reader taps မြန်မာ or တႆး.
   Each .bi pair (Thai span, English span) gets a third span with the translation; CSS shows it
   and hides the English span while html carries lang-my or lang-shn. A pair with no entry keeps
   its English. The dictionary is built by i18n_layer.py from data/i18n/. */
(function () {
  'use strict';
  var H = document.documentElement;
  var ROOT = H.getAttribute('data-root') || '';
  var SEP = '\u001f';
  var DICT = {};
  var PEND = {};

  function cur() { return H.classList.contains('lang-shn') ? 'shn' : H.classList.contains('lang-my') ? 'my' : null; }

  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  /* "{n} pupils" becomes /^(.*?) pupils$/ with the slot names kept in order. */
  function compile(d) {
    if (d.pc) return;
    d.pc = (d.p || []).map(function (row) {
      var names = [], re = '', last = 0, m, rx = /\{([^{}]*)\}/g, src = row[0];
      while ((m = rx.exec(src))) {
        re += esc(src.slice(last, m.index)) + '(.*?)';
        names.push(m[1]);
        last = m.index + m[0].length;
      }
      re += esc(src.slice(last));
      return { re: new RegExp('^' + re + '$'), names: names, tr: row[1] };
    });
  }

  function lookup(d, th, en) {
    var v = d.t[th + SEP + en];
    if (v === undefined) v = d.e[en];
    if (v !== undefined) return v;
    for (var i = 0; i < d.pc.length; i++) {
      var m = d.pc[i].re.exec(en);
      if (!m) continue;
      var out = d.pc[i].tr;
      d.pc[i].names.forEach(function (n, k) { out = out.split('{' + n + '}').join(m[k + 1]); });
      return out;
    }
    return undefined;
  }

  /* The English text of a pair, or null when the span holds markup (a link inside the sentence). */
  function enText(en) {
    var s = '', n = en.firstChild;
    for (; n; n = n.nextSibling) {
      if (n.nodeType === 3) s += n.nodeValue;
      else if (n.nodeType === 1 && n.classList.contains('th')) continue;
      else return null;
    }
    return s.trim();
  }

  function child(b, cls) {
    for (var n = b.firstChild; n; n = n.nextSibling) if (n.nodeType === 1 && n.classList.contains(cls)) return n;
    return null;
  }

  function one(b, lang, d) {
    var th = child(b, 'th'), en = child(b, 'en');
    if (!th || !en) return;
    var e = enText(en);
    if (!e) return;
    var v = lookup(d, th.textContent.trim(), e);
    if (v === undefined) return;
    var old = child(b, 'tr');
    if (old) b.removeChild(old);
    var s = document.createElement('span');
    s.className = 'tr';
    s.lang = lang;
    s.textContent = v;
    b.appendChild(s);
    b.classList.add('hastr');
    b.setAttribute('data-tr', lang);
  }

  function run(root) {
    var lang = cur();
    if (!lang || !DICT[lang]) return;
    var list = (root || document).querySelectorAll('.bi:not([data-tr="' + lang + '"])');
    for (var i = 0; i < list.length; i++) one(list[i], lang, DICT[lang]);
  }

  function load(lang) {
    if (DICT[lang]) return Promise.resolve();
    if (!PEND[lang]) {
      PEND[lang] = fetch(ROOT + 'i18n/' + lang + '.json').then(function (r) { return r.json(); }).then(function (d) {
        compile(d);
        DICT[lang] = d;
      }).catch(function () { PEND[lang] = null; });
    }
    return PEND[lang];
  }

  function apply() {
    var lang = cur();
    if (lang) load(lang).then(function () { run(); });
  }

  var pending = false;
  function watch() {
    if (!window.MutationObserver) return;
    new MutationObserver(function (ms) {
      if (!cur() || pending) return;
      pending = true;
      setTimeout(function () { pending = false; run(); }, 120);
    }).observe(document.body, { childList: true, subtree: true });
  }

  window.MDI18N = { apply: apply };
  watch();
  apply();
})();
