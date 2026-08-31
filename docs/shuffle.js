// The scripture shuffles — katha (Dhammapada + parittas + the curated
// kathas) and Psalms — and the 8-ball oracle. One cycle drives both
// shuffles; it mirrors importers/make_shuffle.py's seed rule and
// tests/test_shuffle_parity.py holds the two together.
//
// The cycle, so anyone can check it:
//   seed  = strength(day-deity) * 1000 + day_pillar * 37 + kham * 7 + bead
//   index = (seed * stride) mod n             (stride = golden-ratio step)
// Same moment, same passage, for everyone. A tap moves one bead (1..108) and
// the walk is remembered per day on this device only.
(function (global) {
  'use strict';

  // ---- time cycles (same constants as make_fortune / make_sky / coucal) ---
  var STRENGTH = [6, 15, 8, 17, 19, 21, 10, 12];   // Sun-first slots; 7 = Wed night
  var SYNODIC = 29.530588853, EPOCH = 2451550.09766;

  function gregToJD(y, m, d, hour) {
    hour = hour || 0;
    if (m <= 2) { y -= 1; m += 12; }
    var a = Math.floor(y / 100), b = 2 - a + Math.floor(a / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1))
         + d + b - 1524.5 + hour / 24;
  }
  function mod(n, k) { return ((n % k) + k) % k; }
  var DAY_ANCHOR = gregToJD(2000, 1, 7) - 8 / 24;
  function dayPillar(y, m, d) { return mod(Math.round(gregToJD(y, m, d) - 8 / 24 - DAY_ANCHOR), 60); }
  // Moon age at 12:00 ICT -> ค่ำ day 1..15 and whether it is a วันพระ
  function kham(y, m, d) {
    var jd = gregToJD(y, m, d, 5.0);
    var age = mod(jd - EPOCH, SYNODIC);
    var day = Math.floor(age) + 1;               // 1..30
    var waning = day > 15;
    var k = waning ? day - 15 : day;
    if (k > 15) k = 15;
    // วันพระ: ขึ้น 8, ขึ้น 15, แรม 8, แรม 14/15 — the 14 only in a short month,
    // which this simple count cannot know, so the 15 is used for both.
    var wanPhra = (k === 8) || (k === 15);
    return { day: k, waning: waning, wanPhra: wanPhra };
  }
  function slotOf(date) {
    var s = date.getDay();
    return (s === 3 && date.getHours() >= 18) ? 7 : s;
  }

  // data/sky.json carries the anchored Thai lunar day (the site's calendar of
  // record for วันพระ); inside its window that wins, beyond it the mean Moon.
  var SKY = null;
  function skyKham(y, m, d) {
    if (!SKY) return null;
    var iso = y + '-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0');
    var mo = (SKY[iso] || {}).moon;
    if (!mo || mo.thai_day == null) return null;
    return { day: +mo.thai_day, waning: !mo.waxing, wanPhra: !!mo.wan_phra };
  }
  function seedFor(date, bead) {
    var y = date.getFullYear(), m = date.getMonth() + 1, d = date.getDate();
    var slot = slotOf(date);
    var kk = skyKham(y, m, d) || kham(y, m, d);
    return { seed: STRENGTH[slot] * 1000 + dayPillar(y, m, d) * 37 + kk.day * 7 + bead,
             slot: slot, kham: kk, dp: dayPillar(y, m, d) };
  }
  function indexFor(seed, n, stride) { return mod(seed * stride, n); }

  // ---- DOM ---------------------------------------------------------------
  function bi(th, en) {
    return '<span class="bi"><span class="th">' + th +
           '</span><span class="en"><span class="th"> · </span>' + en + '</span></span>';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function recall(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function todayKey() {
    var n = new Date();
    return n.getFullYear() + '-' + String(n.getMonth() + 1).padStart(2, '0') + '-' + String(n.getDate()).padStart(2, '0');
  }
  // The bead walk is per day: tomorrow starts at bead 1 again.
  function beadOf(corpus) {
    var raw = recall('md.bead.' + corpus);
    if (!raw) return 1;
    var parts = raw.split('|');
    return parts[0] === todayKey() ? Math.max(1, Math.min(108, +parts[1] || 1)) : 1;
  }
  function setBead(corpus, b) { store('md.bead.' + corpus, todayKey() + '|' + b); }

  var CYCLE = null, CORPUS = {};
  function root() { return document.documentElement.getAttribute('data-root') || ''; }
  function getJSON(path) { return fetch(root() + path).then(function (r) { return r.json(); }); }

  function pick(corpus, bead, meritOnly) {
    var c = CYCLE[corpus];
    var s = seedFor(new Date(), bead);
    var idx = indexFor(s.seed, c.n, c.stride);
    if (meritOnly && c.merit_shelf && c.merit_shelf.length) {
      // On วันพระ the katha walk stays on the merit shelf: the same stride,
      // over the shelf's own ring.
      var shelf = c.merit_shelf;
      idx = shelf[indexFor(s.seed, shelf.length, goldenStride(shelf.length))];
    }
    return { idx: idx, seed: s };
  }
  function goldenStride(n) {
    var s = Math.max(1, Math.round(n / 1.618033988749895)), d = 0;
    while (true) {
      var cands = [s + d, s - d];
      for (var i = 0; i < 2; i++) {
        var c = cands[i];
        if (c >= 1 && c < n && gcd(c, n) === 1) return c;
      }
      d++;
    }
  }
  function gcd(a, b) { while (b) { var t = b; b = a % b; a = t; } return a; }

  // ---- katha tile --------------------------------------------------------
  function renderKatha(pane, bead) {
    var host = pane;
    var s = seedFor(new Date(), bead);
    var res = pick('katha', bead, s.kham.wanPhra);
    var k = CORPUS.katha.items[res.idx];
    var body = '';
    if (k.curated) {
      body = '<p class="kath">' + esc(k.th[0]) + '</p>' +
             '<p class="karom">' + esc(k.pli[0]) + '</p>' +
             '<p class="kagloss">' + bi(esc(k.gloss_th || ''), esc(k.en[0] || '')) + '</p>' +
             (k.when_th ? '<p class="kawhen">' + bi('ใช้เมื่อ ' + esc(k.when_th), esc(k.when_en || '')) + '</p>' : '');
    } else {
      body = '<p class="kath small">' + k.th.map(esc).join('<br>') + '</p>' +
             '<p class="karom">' + k.pli.map(esc).join('<br>') + '</p>' +
             '<p class="kagloss en-only">' + k.en.map(esc).join('<br>') + '</p>';
    }
    var refth = k.curated ? (k.for_th || 'คาถา') : (k.vagga ? k.vagga : '');
    host.querySelector('[data-sh="body"]').innerHTML = body;
    host.querySelector('[data-sh="ref"]').innerHTML =
      '<span class="sharef">' + esc(refth ? refth + ' · ' : '') + esc(k.ref) + '</span>';
    host.querySelector('[data-sh="bead"]').textContent = bead + '/108';
    var wp = host.querySelector('[data-sh="wanphra"]');
    if (wp) wp.hidden = !s.kham.wanPhra;
  }

  // ---- psalms tile -------------------------------------------------------
  function renderPsalms(pane, bead) {
    var host = pane;
    var res = pick('psalms', bead, false);
    var w = CORPUS.psalms.items[res.idx];
    var html = w.verses.map(function (v) {
      return '<p class="psv"><sup>' + v.v + '</sup>' + v.lines.map(esc).join('<br>') + '</p>';
    }).join('');
    host.querySelector('[data-sh="body"]').innerHTML = html;
    host.querySelector('[data-sh="ref"]').innerHTML = bi(esc(w.ref_th), esc(w.ref));
    host.querySelector('[data-sh="bead"]').textContent = bead + '/108';
  }

  // One tile, one pane per shelf. Each shelf keeps its own bead on the same
  // cycle, and its corpus is fetched the first time its tab is opened — so a
  // reader who never opens the Psalms never downloads them.
  function wireShelf(pane, corpus, file, render) {
    if (!pane || pane.dataset.wired) return;
    pane.dataset.wired = '1';
    var btn = pane.querySelector('[data-sh="next"]');
    var go = function () {
      var bead = beadOf(corpus);
      render(pane, bead);
      pane.classList.remove('turning');
    };
    getJSON(file).then(function (j) {
      CORPUS[corpus] = j;
      go();
      if (btn) btn.addEventListener('click', function () {
        var b = beadOf(corpus) % 108 + 1;
        setBead(corpus, b);
        pane.classList.add('turning');
        setTimeout(go, 260);
      });
    }).catch(function () { /* the baked passage stays */ });
  }

  var SHELVES = {
    katha: { file: 'data/katha.json', render: renderKatha },
    psalms: { file: 'data/psalms.json', render: renderPsalms }
  };

  function wireTile() {
    var host = document.getElementById('w-katha');
    if (!host) return;
    var open = function (key) {
      var pane = host.querySelector('[data-shpane="' + key + '"]');
      if (!pane) return;
      var sh = SHELVES[key];
      if (sh) wireShelf(pane, key, sh.file, sh.render);
    };
    // the shelf on top when the page opens
    var first = host.querySelector('.shpane:not([hidden])');
    if (first) open(first.dataset.shpane);
    var tabs = [].slice.call(host.querySelectorAll('[data-shtab]'));
    tabs.forEach(function (b) {
      b.addEventListener('click', function () {
        tabs.forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        [].slice.call(host.querySelectorAll('.shpane')).forEach(function (p) {
          p.hidden = p.dataset.shpane !== b.dataset.shtab;
        });
        open(b.dataset.shtab);
      });
    });
  }

  // ---- 8-ball ------------------------------------------------------------
  // The mechanic is the toy everybody knows; the twenty answers are this
  // site's own words. Which face rises is the same cycle as the shuffles,
  // keyed by the second, so it is a shake and not a coin flip.
  function wireEightBall() {
    var host = document.getElementById('w-eightball');
    if (!host) return;
    var answers;
    try { answers = JSON.parse(host.dataset.answers || '[]'); } catch (e) { return; }
    if (!answers.length) return;
    var ball = host.querySelector('[data-eb="ball"]'), face = host.querySelector('[data-eb="face"]'),
        tri = host.querySelector('[data-eb="tri"]'), out = host.querySelector('[data-eb="out"]'),
        btn = host.querySelector('[data-eb="shake"]');
    var V = { 'ดี': 'good', 'กลาง': 'mid', 'ระวัง': 'care' };
    btn.addEventListener('click', function () {
      if (ball.classList.contains('shaking')) return;
      ball.classList.add('shaking');
      tri.classList.remove('up');
      out.hidden = true;
      setTimeout(function () {
        ball.classList.remove('shaking');
        var n = new Date();
        var s = seedFor(n, n.getSeconds() + 60 * n.getMinutes());
        var a = answers[indexFor(s.seed, answers.length, goldenStride(answers.length))];
        face.innerHTML = '<span class="ebth">' + esc(a.th) + '</span><span class="eben">' + esc(a.en) + '</span>';
        tri.className = 'ebtri up v-' + (V[a.v] || 'mid');
        out.innerHTML = bi(esc(a.th), esc(a.en));
        out.className = 'ebout v-' + (V[a.v] || 'mid');
        out.hidden = false;
        host.classList.add('answered');
      }, 900);
    });
  }

  function init() {
    wireEightBall();
    if (!document.getElementById('w-katha')) return;
    getJSON('data/sky.json').then(function (j) { SKY = j.days || null; }).catch(function () {})
    .then(function () { return getJSON('data/shuffle.json'); }).then(function (j) {
      CYCLE = j.cycle;
      wireTile();
    }).catch(function () {});
  }

  global.MDShuffle = { seedFor: seedFor, indexFor: indexFor, kham: kham,
                       dayPillar: dayPillar, goldenStride: goldenStride, gregToJD: gregToJD };

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }
}(typeof window !== 'undefined' ? window : this));
