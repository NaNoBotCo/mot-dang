/* /doodles/ — the doodle repository (doodlerepo_layer.py writes the pages and data, tools/doodle_repo.py
   records). Every page is this script: <body data-c="" | front | place | minisite | scene | cover | one,
   data-sub="…">. Lists load 24 at a time; a doodle draws with the engine its latest version was made by
   (/doodles/engines/<hash>.js); the one-doodle page (/doodles/d/?id=…&v=…) replays any version. */
(function () {
  var B = document.body, C = B.dataset.c || '', SUB = B.dataset.sub || '', APP = document.getElementById('app');
  var H = document.documentElement, META = null, NM = { cats: {}, kinds: {} }, RIDGE = null, SHOP = {};
  var REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches, PAGE = 24;
  var Q = new URLSearchParams(location.search);
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function bi(th, en) { return '<span class="th">' + th + '</span><span class="en">' + en + '</span>'; }
  function num(n) { return (+n).toLocaleString('en-US'); }
  function get(u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  var lang = (function () { try { return localStorage.getItem('md-lang'); } catch (e) { return null; } })() || ((navigator.language || '').slice(0, 2) === 'th' ? 'th' : 'en');
  function setLang(l) { lang = l; H.classList.remove('lang-th', 'lang-en'); H.classList.add('lang-' + l); H.lang = l; try { localStorage.setItem('md-lang', l); } catch (e) {} }
  setLang(lang);
  var MTH = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'], MEN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function day(d) { if (!d) return ''; var p = d.split('-'); return bi(+p[2] + ' ' + MTH[p[1] - 1] + ' ' + (+p[0] + 543), +p[2] + ' ' + MEN[p[1] - 1] + ' ' + p[0]); }
  function catName(c) { return NM.cats[c] || { th: c, en: c, path: c }; }
  function kindName(c, s, row) {
    if (c === 'minisite' && row) return { th: row.t[0], en: row.t[1] };
    var k = NM.kinds[s]; return k || { th: s.replace(/-/g, ' '), en: s.replace(/-/g, ' ') };
  }
  function fnv(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function bucket(id) { return ('00' + (fnv(id) % 1024).toString(16)).slice(-3); }
  function engine(h) {
    return new Promise(function (ok) {
      if (engine.have === h) return ok(true);
      var s = document.createElement('script'); s.src = '/doodles/engines/' + h + '.js';
      s.onload = function () { engine.have = h; ok(true); }; s.onerror = function () { ok(false); }; document.head.appendChild(s);
    });
  }
  function rec(id, c, p) { return { id: id, c: c, p: p }; }
  function size(cv) {
    var d = Math.min(2, devicePixelRatio || 1), w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * d) || cv.height !== Math.round(h * d)) { cv.width = Math.round(w * d); cv.height = Math.round(h * d); }
    cv._dpr = d;
  }
  function frame(cv, r, t) { size(cv); try { window.MDREPO.draw(cv, r, t, RIDGE); } catch (e) { console.error(r.id, e); } }
  function shell(inner) {
    APP.innerHTML = '<header><a class="home" href="/"><b>มดแดง</b> Mot Dang</a><nav><button class="btn" id="lang" type="button" aria-label="ภาษา · language">' + bi('EN', 'ไทย') + '</button></nav></header>' + inner +
      '<footer>' + bi('วาดด้วยโค้ด ไม่มีภาพถ่าย', 'Drawn in code, no photographs.') + ' · <a href="/doodles/data/meta.json">data</a> · CC BY 4.0 Mot Dang</footer>';
    $('lang').onclick = function () { setLang(lang === 'th' ? 'en' : 'th'); if (shell.re) shell.re(); };
  }

  /* ================================================================ votes: a thumb up or down on accuracy and on
     aesthetics, and notes, for the latest version (worker.js /doodle-vote; tools/doodle_score.py weighs them,
     tools/doodle_redo.py ranks the low ones for a redraw) */
  function payee() { try { return localStorage.getItem('md-payee') || ''; } catch (e) { return ''; } }
  function payBox() {
    var P = META && META.pay; if (!P) return '';
    return '<p class="pay"><label for="payee">' + bi('ที่อยู่ Lightning สำหรับรับเงิน', 'Lightning address, to be paid') +
      ' <small>' + bi('เลือกภาพ $' + P.pick + ' · บันทึก $' + P.note[0] + '–$' + P.note[1], 'pick $' + P.pick + ' · notes $' + P.note[0] + '–$' + P.note[1]) + '</small></label>' +
      '<input id="payee" type="text" autocomplete="off" spellcheck="false" placeholder="name@wallet.com" value="' + esc(payee()) + '"></p>';
  }
  document.addEventListener('change', function (e) { if (e.target.id === 'payee') try { localStorage.setItem('md-payee', e.target.value.trim()); } catch (x) {} });
  function withPayee(body) { var p = payee(); if (META && META.pay && p) body.payee = p; return body; }
  var VOTE = 'https://mot-dang-claims.nanobotco.workers.dev', AX = [['like', 'ชอบ', 'Like'], ['accuracy', 'ถูกต้อง', 'Accuracy'], ['aesthetics', 'ความงาม', 'Aesthetics']];
  /* what this browser voted on one version (the doodle page and the cards share it), and its favourites list */
  function mineOf(id, v) { try { var st = JSON.parse(localStorage.getItem('md-dv:' + id + '@' + v) || '{}') || {}; return { votes: st.votes || {}, note: st.note || '' }; } catch (e) { return { votes: {}, note: '' }; } }
  function keepMineOf(id, v, m) { try { localStorage.setItem('md-dv:' + id + '@' + v, JSON.stringify(m)); } catch (e) {} }
  function favs() { try { return JSON.parse(localStorage.getItem('md-favs') || '{}') || {}; } catch (e) { return {}; } }
  function keepFav(id, v, on) { var f = favs(); if (on) f[id] = v; else delete f[id]; try { localStorage.setItem('md-favs', JSON.stringify(f)); } catch (e) {} }
  function heart(on) { return '<span class="hrt" aria-hidden="true">' + (on ? '♥' : '♡') + '</span>'; }
  /* every version anyone voted on: {"id@v": [like up, like down, looks up, looks down, favs]} (worker.js /doodle-scores) */
  var SCORES = null;
  function scores() { return SCORES ? Promise.resolve(SCORES) : get(VOTE + '/doodle-scores').then(function (r) { return (SCORES = (r && r.scores) || {}); }); }
  /* a thumb, drawn here (the site's icon sheet has none): the hand, its cuff; down is the same turned over */
  function thumb(n) {
    return '<svg class="ic" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"' + (n === 'down' ? ' style="transform:rotate(180deg)"' : '') + '>' +
      '<path d="M7 10.5v9.5H4v-9.5Z"/><path d="M7 10.5 11 3.5a2 2 0 0 1 2.8 1.9L13 9.5h5.6a2 2 0 0 1 2 2.4l-1.4 6.5a2 2 0 0 1-2 1.6H7"/></svg>';
  }
  function votes(el, id, v) {
    var m0 = mineOf(id, v), mine = m0.votes, T = null, busy = false, sent = m0.note;
    function keep() { keepMineOf(id, v, { votes: mine, note: sent }); keepFav(id, v, mine.fav === 1); }
    function n(a, k) { return T && T[a] ? T[a][k] : 0; }
    el.innerHTML = '<div id="vrows"></div><label class="vn" for="vnote">' + bi('บันทึก: ภาพนี้ถูกตรงไหน ผิดตรงไหน', 'Notes: what is right with the picture, what is wrong') + '</label>' +
      '<textarea id="vnote" maxlength="2000" rows="4"></textarea><div class="vsend"><button class="btn" id="vsend" type="button">' + bi('ส่งบันทึก', 'Send notes') + '</button> <span id="vst" aria-live="polite"></span></div>' + payBox();
    $('vnote').value = sent;
    if (location.hash === '#vnote') setTimeout(function () { $('vnote').scrollIntoView({ block: 'center' }); }, 400);   /* from the front page's Notes link */
    function paint() {
      $('vrows').innerHTML = '<div class="vrow"><span class="vl">' + bi('รายการโปรด', 'Favourite') + '</span><button class="btn vb vf" type="button" data-a="fav" aria-pressed="' + (mine.fav === 1) + '" aria-label="รายการโปรด · Favourite">' +
        heart(mine.fav === 1) + '<i>' + num(n('fav', 0)) + '</i></button></div>' + AX.map(function (a) {
        var m = mine[a[0]] || 0;
        return '<div class="vrow"><span class="vl">' + bi(a[1], a[2]) + '</span>' + [[1, 'up', 0, 'ดี', 'up'], [-1, 'down', 1, 'ไม่ดี', 'down']].map(function (u) {
          return '<button class="btn vb" type="button" data-a="' + a[0] + '" data-x="' + u[0] + '" aria-pressed="' + (m === u[0]) + '" aria-label="' +
            a[1] + ' ' + u[3] + ' · ' + a[2] + ', ' + u[4] + '">' + thumb(u[1]) + '<i>' + num(n(a[0], u[2])) + '</i></button>';
        }).join('') + '</div>';
      }).join('');
    }
    function post(body, done) {
      busy = true; el.classList.add('busy');
      fetch(VOTE + '/doodle-vote', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(withPayee(body)) })
        .then(function (r) { return r.json(); }).then(function (r) {
          if (r && r.ok) { mine = r.mine || mine; T = r.tally; keep(); }
          done(r);
        }).catch(function () { done(null); }).then(function () { busy = false; el.classList.remove('busy'); paint(); });
    }
    $('vrows').onclick = function (e) {
      var b = e.target.closest('.vb'); if (!b || busy) return;
      var a = b.dataset.a, x = a === 'fav' ? (mine.fav === 1 ? 0 : 1) : +b.dataset.x, body = { id: id, v: v }; if (a !== 'fav' && mine[a] === x) x = 0; body[a] = x;
      post(body, function () {});
    };
    $('vsend').onclick = function () {
      var note = $('vnote').value.trim(), body = { id: id, v: v, note: note }, any = false;
      AX.forEach(function (a) { if (mine[a[0]]) { body[a[0]] = mine[a[0]]; any = true; } });   /* a favourite alone carries no note */
      if (busy || !note) return;
      if (!any) { $('vst').innerHTML = bi('กดนิ้วโป้งก่อน', 'Tap a thumb first'); return; }
      post(body, function (r) { if (r && r.ok) { sent = note; keep(); $('vst').innerHTML = bi('ได้รับแล้ว', 'Received'); } else $('vst').innerHTML = bi('ส่งไม่ได้', 'Not sent'); });
    };
    paint();
    get(VOTE + '/doodle-votes?id=' + encodeURIComponent(id) + '&v=' + v).then(function (r) { if (r && r.ok) { T = r.tally; paint(); } });
  }

  /* ================================================================ pick: /doodles/pick/ — the better of two
     (worker.js /doodle-pick; the pairs are data/pairs.json, written by doodlerepo_layer.pairs) */
  function pick() {
    var P = [], n = 0, cur = null;
    shell('<p class="crumb"><a href="/doodles/">' + bi('ดูเดิล', 'Doodles') + '</a></p><h1>' + bi('ภาพไหนดีกว่า', 'Which is better?') + ' <span class="count" id="count"></span></h1>' +
      '<div class="pk2" id="pk2"></div><p class="vsend"><button class="btn" id="psame" type="button">' + bi('บอกไม่ได้', 'Can\'t tell') + '</button> <button class="btn" id="pskip" type="button">' + bi('ข้าม', 'Skip') + '</button> <span id="vst" aria-live="polite"></span></p>' + payBox());
    function title(id) { return get('/doodles/data/v/' + bucket(id) + '.json').then(function (b) { var D = b && b[id]; return D ? D.t : [id, id]; }); }
    function next() {
      if (!P.length) { $('pk2').innerHTML = '<p class="none">' + bi('ยังไม่มีคู่', 'No pairs yet') + '</p>'; return; }
      var r = P[Math.floor(Math.random() * P.length)], sw = Math.random() < 0.5;
      cur = sw ? { a: { id: r[2], v: r[3] }, b: { id: r[0], v: r[1] } } : { a: { id: r[0], v: r[1] }, b: { id: r[2], v: r[3] } };
      Promise.all([title(cur.a.id), title(cur.b.id)]).then(function (t) {
        $('pk2').innerHTML = ['a', 'b'].map(function (k, j) {
          var d = cur[k], same = cur.a.id === cur.b.id;
          return '<button class="pk" type="button" data-s="' + k + '" aria-label="' + esc(bi_t(t[j])) + (same ? ' v' + d.v : '') + '">' +
            '<iframe tabindex="-1" loading="lazy" src="/doodles/d/?id=' + encodeURIComponent(d.id) + '&v=' + d.v + '&frame=1" title="' + esc(t[j][1] || t[j][0]) + '"></iframe>' +
            '<span>' + bi(esc(t[j][0]), esc(t[j][1] || t[j][0])) + (same ? ' · v' + d.v : '') + '</span></button>';
        }).join('');
      });
    }
    function bi_t(t) { return (t[0] || '') + (t[1] && t[1] !== t[0] ? ' · ' + t[1] : ''); }
    function send(s, b) {
      if (!cur) return;
      var body = { a: cur.a, b: cur.b, pick: s }; cur = null; if (b) b.classList.add('won');
      fetch(VOTE + '/doodle-pick', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(withPayee(body)) })
        .then(function (r) { return r.json(); }).then(function (r) { if (r && r.ok) { n++; $('count').textContent = '· ' + num(n); } else $('vst').innerHTML = bi('ส่งไม่ได้', 'Not sent'); })
        .catch(function () { $('vst').innerHTML = bi('ส่งไม่ได้', 'Not sent'); }).then(function () { setTimeout(next, 350); });
    }
    $('pk2').onclick = function (e) { var b = e.target.closest('.pk'); if (b) send(b.dataset.s, b); };
    $('psame').onclick = function () { send('same'); };
    $('pskip').onclick = next;
    get('/doodles/data/pairs.json').then(function (a) { P = a || []; next(); });
  }

  /* ================================================================ one doodle: /doodles/d/?id=…&v=… */
  function one() {
    var id = Q.get('id') || '', want = +Q.get('v') || 0, bare = Q.get('frame') === '1';
    get('/doodles/data/v/' + bucket(id) + '.json').then(function (bk) {
      var D = bk && bk[id];
      if (!D) { shell('<h1>' + bi('ไม่พบดูเดิลนี้', 'No such doodle') + '</h1><p><a href="/doodles/">' + bi('ดูเดิลทั้งหมด', 'All doodles') + '</a></p>'); return; }
      var V = D.vs.filter(function (x) { return x.v === want; })[0] || D.vs[D.vs.length - 1], r = rec(id, D.c, V.p);
      if (bare) { H.classList.add('bare'); APP.innerHTML = '<canvas id="big"></canvas>'; }
      else {
        var cn = catName(D.c), kn = D.s ? kindName(D.c, D.s, { t: D.t }) : null, url = location.origin + '/doodles/d/?id=' + encodeURIComponent(id) + (want ? '&v=' + want : '');
        var p = V.p || {}, extra = '';
        if (D.c === 'front') extra = (p.s ? '<p>' + esc(p.s.slice(11, 16)) + (p.v ? ' · ' + esc(p.v) : '') + '</p>' : '');
        if (D.c === 'place' && p.f) extra = '<p>' + bi(esc(kindName('place', D.s).th), esc(kindName('place', D.s).en)) + (p.f.amphoe ? ' · ' + bi(esc(p.f.amphoe), esc(p.f.amphoeRom || p.f.amphoe)) : '') + '</p>';
        if (p.alt && p.alt[0]) extra += '<p>' + bi(esc(p.alt[0]), esc(p.alt[1])) + '</p>';
        var status = D.pl ? bi('วางแผนไว้', 'planned') : D.g ? bi('ออกไปแล้ว ' , 'left ') + day(D.g) : '';
        shell('<p class="crumb"><a href="/doodles/">' + bi('ดูเดิล', 'Doodles') + '</a> › <a href="/doodles/' + cn.path + '/">' + bi(cn.th, cn.en) + '</a>' +
          (kn ? ' › <a href="/doodles/' + cn.path + '/' + esc(D.s) + '/">' + bi(esc(kn.th), esc(kn.en)) + '</a>' : '') + '</p>' +
          '<h1>' + bi(esc(D.t[0]), esc(D.t[1])) + '</h1>' +
          '<canvas id="big" class="big" role="img" aria-label="' + esc(D.t[1] || D.t[0]) + '"></canvas>' +
          '<div class="meta"><time>' + day(D.d) + '</time>' + (status ? ' · <b class="st">' + status + '</b>' : '') + extra +
          (D.h ? '<a class="go" href="' + esc(D.h) + '">' + bi('ไปที่หน้าของมัน', 'Where it lives') + ' →</a>' : '') + '</div>' +
          (V === D.vs[D.vs.length - 1] && !D.g ? '<div class="vote" id="vote"></div>' : '') +
          '<p><a class="btn" href="/doodles/pick/">' + bi('ภาพไหนดีกว่า', 'Which is better?') + ' →</a></p>' +
          '<h2>' + bi('แชร์', 'Share') + '</h2><div class="share">' +
          '<button class="btn" id="s-copy" type="button">' + bi('คัดลอกลิงก์', 'Copy link') + '</button>' +
          (navigator.share ? '<button class="btn" id="s-share" type="button">' + bi('แชร์…', 'Share…') + '</button>' : '') +
          '<button class="btn" id="s-png" type="button">' + bi('ภาพนิ่ง PNG', 'Picture (PNG)') + '</button>' +
          (window.MediaRecorder && HTMLCanvasElement.prototype.captureStream ? '<button class="btn" id="s-vid" type="button">' + bi('วิดีโอ 4 วินาที', 'Video, 4 s') + '</button>' : '') +
          '<a class="btn" href="https://web.archive.org/save/' + esc(url) + '" rel="noopener">' + bi('เก็บไว้ที่ Internet Archive', 'Save to the Internet Archive') + '</a>' +
          '<a class="btn" href="https://web.archive.org/web/*/' + esc(url) + '" rel="noopener">' + bi('สำเนาที่เก็บไว้', 'Archived copies') + '</a></div>' +
          '<div id="buy"></div>' +
          '<h2>' + bi('รุ่น', 'Versions') + ' <i class="n">' + D.vs.length + '</i></h2><ol class="vers">' + D.vs.map(function (x) {
            return '<li' + (x === V ? ' class="on"' : '') + '><a href="?id=' + encodeURIComponent(id) + '&v=' + x.v + '">v' + x.v + '</a> · ' + day(x.f) + ' – ' + (x.to ? day(x.to) : bi('ปัจจุบัน', 'now')) +
              ' <code>' + esc(x.e) + '</code></li>';
          }).join('') + '</ol>');
        if ($('vote')) votes($('vote'), id, V.v);
        $('s-copy').onclick = function () { (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { $('s-copy').innerHTML = bi('คัดลอกแล้ว', 'Copied'); }).catch(function () { prompt('', url); }); };
        function png() { return new Promise(function (ok) { $('big').toBlob(ok, 'image/png'); }); }
        var fname = id.replace(/[^a-z0-9-]/g, '') + '-v' + V.v;
        function save(blob, ext) { var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fname + '.' + ext; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000); }
        if ($('s-share')) $('s-share').onclick = function () {
          png().then(function (b) {
            var f = new File([b], fname + '.png', { type: 'image/png' }), o = { title: D.t[1] || D.t[0], url: url };
            if (navigator.canShare && navigator.canShare({ files: [f] })) o.files = [f];
            navigator.share(o).catch(function () {});
          });
        };
        $('s-png').onclick = function () { png().then(function (b) { save(b, 'png'); }); };
        if ($('s-vid')) $('s-vid').onclick = function () {
          var btn = $('s-vid'), mt = ['video/mp4', 'video/webm;codecs=vp9', 'video/webm'].filter(function (m) { return MediaRecorder.isTypeSupported(m); })[0];
          if (!mt) return;
          var rec_ = new MediaRecorder($('big').captureStream(30), { mimeType: mt }), parts = [];
          rec_.ondataavailable = function (e) { if (e.data.size) parts.push(e.data); };
          rec_.onstop = function () { save(new Blob(parts, { type: mt }), mt.indexOf('mp4') >= 0 ? 'mp4' : 'webm'); btn.disabled = false; btn.innerHTML = bi('วิดีโอ 4 วินาที', 'Video, 4 s'); };
          btn.disabled = true; btn.innerHTML = bi('กำลังอัด…', 'Recording…'); rec_.start(); setTimeout(function () { rec_.stop(); }, 4000);
        };
        get('/doodles/shop.json').then(function (s) {
          var L = ((s || {}).links || {})[id] || {}, h = '';
          ((s || {}).products || []).forEach(function (pr) { var o = L[pr.id]; if (o && o.url) h += '<a href="' + esc(o.url) + '" rel="noopener">' + bi(esc(pr.th), esc(pr.en)) + (o.price ? ' <small>' + esc(o.price) + '</small>' : '') + '</a>'; });
          if (h) $('buy').innerHTML = '<div class="buy">' + h + '</div>';
        });
      }
      var cv = $('big'); cv.style.aspectRatio = '1';
      engine(V.e).then(function (ok) { return ok ? ok : engine(META.engine); }).then(function () {
        cv.style.aspectRatio = String(window.MDREPO.aspect(r));
        function loop(t) { frame(cv, r, t); if (!REDUCED) requestAnimationFrame(loop); }
        if (REDUCED) frame(cv, r, 4200); else requestAnimationFrame(loop);
        addEventListener('mddoodler', function () { frame(cv, r, REDUCED ? 4200 : performance.now()); });
      });
    });
  }

  /* ================================================================ lists: all, a category, a subcategory */
  var S = { sort: Q.get('sort') || 'new', q: Q.get('q') || '', mine: Q.get('mine') === '1', feat: Q.get('feat') || '' }, POS = null, IDX = null, CH = {}, GEN = 0, VIEW = [], CV = [], ON = {}, AT = 0, LIST = [], LOADING = false;
  function keep() { var u = new URLSearchParams(); if (S.sort !== 'new') u.set('sort', S.sort); if (S.q) u.set('q', S.q); if (S.mine) u.set('mine', '1'); if (S.feat) u.set('feat', S.feat); var q = u.toString(); history.replaceState(null, '', location.pathname + (q ? '?' + q : '')); }
  /* sorts on votes: a Wilson lower bound for liked and looks (a few votes do not outrank many), Reddit's
     (up + down)^(minority / majority) for controversial, a plain count for favourites */
  var VOTED = { liked: 1, contro: 1, looks: 1, favs: 1 };
  function wilson(u, d) { var n = u + d; if (!n) return 0; var z = 1.96, p = u / n; return (p + z * z / (2 * n) - z * Math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / (1 + z * z / n); }
  function rank(sc) {
    if (!sc) return null;
    if (S.sort === 'liked') return sc[0] + sc[1] ? wilson(sc[0], sc[1]) + sc[0] * 1e-6 : null;
    if (S.sort === 'looks') return sc[2] + sc[3] ? wilson(sc[2], sc[3]) + sc[2] * 1e-6 : null;
    if (S.sort === 'contro') return sc[0] && sc[1] ? Math.pow(sc[0] + sc[1], Math.min(sc[0], sc[1]) / Math.max(sc[0], sc[1])) : null;
    if (S.sort === 'favs') return sc[4] || null;
    return 0;
  }
  var CATOF = { s: 'scene', p: 'place', f: 'front', c: 'cover', m: 'minisite' };
  /* a list row from the doodle's own version file, for lists that start from ids (votes, favourites) */
  function rowById(id) {
    return get('/doodles/data/v/' + bucket(id) + '.json').then(function (b) {
      var D = b && b[id]; if (!D) return null; var L = D.vs[D.vs.length - 1];
      var row = { id: id, c: D.c, s: D.s, d: D.d, t: D.t, h: D.h, n: D.vs.length, v: L.v, p: L.p, f: D.vs[0].f, u: L.f };
      if (L.e !== META.engine) row.e = L.e; if (D.g) row.g = D.g; if (D.pl) row.pl = 1;
      return row;
    });
  }
  function byIds() {
    return Promise.all([scores(), S.mine ? favs() : null]).then(function (a) {
      var sc = a[0], ids = {};
      if (S.mine) Object.keys(a[1]).forEach(function (i) { ids[i] = 1; });
      else Object.keys(sc).forEach(function (k) { ids[k.slice(0, k.lastIndexOf('@'))] = 1; });
      var want = Object.keys(ids).filter(function (i) { return !C || CATOF[i[0]] === C; });
      return Promise.all(want.map(rowById));
    }).then(function (rows) {
      rows = rows.filter(function (r) {
        if (!r || (SUB && r.s !== SUB)) return false;
        if (S.feat && (((r.p || {}).f || {}).props || []).indexOf(S.feat) < 0) return false;
        var kn = kindName(r.c, r.s || ''); return !S.q || words(r.t[0] + ' ' + r.t[1] + ' ' + r.d + ' ' + (r.s || '') + ' ' + kn.en + ' ' + kn.th);
      });
      if (VOTED[S.sort]) {
        rows.forEach(function (r) { r._k = rank(SCORES[r.id + '@' + r.v]); });
        rows = rows.filter(function (r) { return r._k != null; }).sort(function (a, b) { return b._k - a._k || (a.d < b.d ? 1 : -1); });
      } else if (S.sort === 'old') rows.sort(function (a, b) { return a.d < b.d ? -1 : a.d > b.d ? 1 : 0; });
      else if (S.sort === 'az') rows.sort(function (a, b) { var k = lang === 'th' ? 0 : 1; return (a.t[k] || a.t[0]).localeCompare(b.t[k] || b.t[0], lang); });
      else rows.sort(function (a, b) { return a.d < b.d ? 1 : a.d > b.d ? -1 : 0; });
      return rows;
    });
  }
  function chunk(n) { return CH[n] || (CH[n] = get('/doodles/data/all/' + n + '.json').then(function (a) { return a || []; })); }
  function rowAt(pos) { return chunk(Math.floor(pos / META.chunk)).then(function (a) { return a[pos % META.chunk]; }); }
  function positions() {
    if (POS) return Promise.resolve(POS);
    if (!C) { POS = []; for (var i = 0; i < META.total; i++) POS.push(i); return Promise.resolve(POS); }
    return get('/doodles/data/list/' + C + (SUB ? '~' + SUB : '') + '.json').then(function (a) { return (POS = a || []); });
  }
  function words(hay) { hay = hay.toLowerCase(); return S.q.toLowerCase().split(/\s+/).every(function (w) { return !w || hay.indexOf(w) >= 0; }); }
  function order() {
    if (VOTED[S.sort] || S.mine) return byIds();
    return (S.feat ? Promise.all([positions(), get('/doodles/data/list/feat~' + S.feat + '.json')]).then(function (a) {
      var inf = {}; (a[1] || []).forEach(function (p) { inf[p] = 1; }); return a[0].filter(function (p) { return inf[p]; });
    }) : positions()).then(function (pos) {
      if (S.sort === 'new' && !S.q) return pos.slice();
      if (S.sort === 'old' && !S.q) return pos.slice().reverse();
      return (IDX ? Promise.resolve(IDX) : get('/doodles/data/idx.json').then(function (a) { return (IDX = a || []); })).then(function (ix) {
        var inl = {}; pos.forEach(function (p) { inl[p] = 1; });
        var rows = ix.filter(function (r) { return inl[r[0]] && (!S.q || words(r[1] + ' ' + r[2] + ' ' + r[3] + ' ' + r[6] + ' ' + kindName(r[5], r[6]).en + ' ' + kindName(r[5], r[6]).th)); });
        var k = lang === 'th' ? 1 : 2;
        if (S.sort === 'old') rows.sort(function (a, b) { return a[3] < b[3] ? -1 : a[3] > b[3] ? 1 : a[0] - b[0]; });
        else if (S.sort === 'az') { var lead = /^[^0-9A-Za-z\u0E00-\u0E7F]+/; rows.sort(function (a, b) { return (a[k] || a[1]).replace(lead, '').localeCompare((b[k] || b[1]).replace(lead, ''), lang); }); }
        else if (S.sort === 'versions') rows.sort(function (a, b) { return b[4] - a[4] || a[0] - b[0]; });
        else if (S.sort === 'changed') rows.sort(function (a, b) { return a[7] < b[7] ? 1 : a[7] > b[7] ? -1 : a[0] - b[0]; });
        else rows.sort(function (a, b) { return a[0] - b[0]; });
        return rows.map(function (r) { return r[0]; });
      });
    });
  }
  function card(row, i) {
    var cn = catName(row.c), kn = row.s ? kindName(row.c, row.s, row) : null, href = '/doodles/d/?id=' + encodeURIComponent(row.id);
    var st = row.pl ? '<b class="st">' + bi('วางแผนไว้', 'planned') + '</b>' : row.g ? '<b class="st">' + bi('ออกไปแล้ว', 'left') + '</b>' : '';
    var media = row.e ? '<iframe loading="lazy" src="' + href + '&frame=1" title="' + esc(row.t[1] || row.t[0]) + '"></iframe>'
      : '<canvas data-i="' + i + '" role="img" aria-label="' + esc(row.t[1] || row.t[0]) + '"></canvas>';
    return '<article class="c-' + row.c + '"><a class="pic" href="' + href + '">' + media + '</a><div class="meta">' +
      '<time>' + day(row.d) + '</time>' + (st ? ' · ' + st : '') + (row.n > 1 ? ' · <span class="nv">' + bi(row.n + ' รุ่น', row.n + ' versions') + '</span>' : '') +
      '<h2><a href="' + href + '">' + bi(esc(row.t[0]), esc(row.t[1] || row.t[0])) + '</a></h2>' +
      '<p>' + (C ? '' : '<a href="/doodles/' + cn.path + '/">' + bi(cn.th, cn.en) + '</a>' + (kn ? ' · ' : '')) +
      (kn && row.c !== 'minisite' ? '<a href="/doodles/' + cn.path + '/' + esc(row.s) + '/">' + bi(esc(kn.th), esc(kn.en)) + '</a>' : '') +
      (row.c === 'place' && row.p && row.p.f && row.p.f.amphoe ? ' · ' + bi(esc(row.p.f.amphoe), esc(row.p.f.amphoeRom || row.p.f.amphoe)) : '') + '</p>' +
      '<p class="acts"><a href="' + href + '">' + bi('เปิด แชร์', 'Open, share') + '</a>' + (row.h ? ' · <a href="' + esc(row.h) + '">' + bi('ไปที่หน้าของมัน', 'Where it lives') + ' →</a>' : '') + '</p>' +
      (row.g ? '' : '<div class="cv" data-id="' + esc(row.id) + '" data-v="' + row.v + '">' + cardVotes(row.id, row.v) + '</div>') + '</div></article>';
  }
  function cardVotes(id, v) {
    var m = mineOf(id, v).votes, sc = (SCORES && SCORES[id + '@' + v]) || [0, 0, 0, 0, 0];
    return '<button class="btn vb" type="button" data-k="like" data-x="1" aria-pressed="' + (m.like === 1) + '" aria-label="ชอบ · Like">' + thumb('up') + '<i>' + num(sc[0]) + '</i></button>' +
      '<button class="btn vb" type="button" data-k="like" data-x="-1" aria-pressed="' + (m.like === -1) + '" aria-label="ไม่ชอบ · Dislike">' + thumb('down') + '<i>' + num(sc[1]) + '</i></button>' +
      '<button class="btn vb vf" type="button" data-k="fav" data-x="1" aria-pressed="' + (m.fav === 1) + '" aria-label="รายการโปรด · Favourite">' + heart(m.fav === 1) + '<i>' + num(sc[4]) + '</i></button>';
  }
  /* one tap on a card: the vote goes to the worker, the counts come back with it */
  function cardVote(b) {
    var box = b.closest('.cv'); if (!box || box.classList.contains('busy')) return;
    var id = box.dataset.id, v = +box.dataset.v, k = b.dataset.k, me = mineOf(id, v), x = +b.dataset.x, body = { id: id, v: v };
    if (k === 'fav') x = me.votes.fav === 1 ? 0 : 1; else if (me.votes[k] === x) x = 0;
    body[k] = x; box.classList.add('busy');
    fetch(VOTE + '/doodle-vote', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(withPayee(body)) })
      .then(function (r) { return r.json(); }).then(function (r) {
        if (!r || !r.ok) return;
        me.votes = r.mine || me.votes; keepMineOf(id, v, me); keepFav(id, v, me.votes.fav === 1);
        var t = r.tally || {}; if (SCORES) SCORES[id + '@' + v] = [(t.like || [0, 0])[0], (t.like || [0, 0])[1], (t.aesthetics || [0, 0])[0], (t.aesthetics || [0, 0])[1], (t.fav || [0, 0])[0]];
      }).catch(function () {}).then(function () { box.classList.remove('busy'); box.innerHTML = cardVotes(id, v); });
  }
  var io = new IntersectionObserver(function (es) { es.forEach(function (e) { ON[e.target.dataset.i] = e.isIntersecting; if (e.isIntersecting && !e.target._d) { e.target._d = 1; draw1(e.target, 4200); } }); });
  var moreIO = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting && e.target.isConnected) page(); }); }, { rootMargin: '700px' });
  function draw1(cv, t) { var row = VIEW[cv.dataset.i]; if (row) frame(cv, rec(row.id, row.c, row.p), t); }
  function paint(t, all) { CV.forEach(function (cv) { if (all || ON[cv.dataset.i]) draw1(cv, t); }); }
  function page() {
    if (LOADING || AT >= LIST.length) return; LOADING = true; var g = GEN, part = LIST.slice(AT, AT + PAGE); AT += part.length;
    Promise.all(part.map(function (x) { return typeof x === 'object' ? x : rowAt(x); })).then(function (rows) {
      LOADING = false; if (g !== GEN) return;
      var list = $('list'), start = VIEW.length, h = '';
      rows.forEach(function (row, j) { if (row) { VIEW[start + j] = row; h += card(row, start + j); } });
      if ($('more')) $('more').remove();
      list.insertAdjacentHTML('beforeend', h);
      Array.prototype.slice.call(list.querySelectorAll('canvas')).forEach(function (cv) { if (!cv._seen) { cv._seen = 1; CV.push(cv); io.observe(cv); cv._d = 1; draw1(cv, 4200); } });   /* a first frame on every card, on screen or not */
      if (AT < LIST.length) { list.insertAdjacentHTML('beforeend', '<button class="btn" id="more" type="button">' + bi('ดูอีก', 'More') + '</button>'); $('more').onclick = page; moreIO.observe($('more')); }
    });
  }
  function show() {
    GEN++; VIEW = []; CV = []; ON = {}; AT = 0; LOADING = false; io.disconnect(); moreIO.disconnect(); keep(); bar();
    $('list').innerHTML = '<p class="none">…</p>';
    order().then(function (l) {
      LIST = l; $('list').innerHTML = l.length ? '' : '<p class="none">' + (S.mine ? bi('ยังไม่มีรายการโปรด แตะ ♡ ใต้ภาพที่ชอบ', 'No favourites yet. Tap ♡ under a picture.') :
        VOTED[S.sort] ? bi('ยังไม่มีใครโหวตดูเดิลในรายการนี้', 'Nobody has voted on a doodle in this list yet.') : bi('ไม่มีดูเดิลที่ตรง', 'No doodle matches')) + '</p>';
      $('count').textContent = '· ' + num(l.length); page();
    });
  }
  function chip(attr, val, on, label, n) { return '<button class="chip" type="button" data-' + attr + '="' + esc(val) + '" aria-pressed="' + on + '">' + label + (n != null ? ' <i>' + num(n) + '</i>' : '') + '</button>'; }
  function link(href, on, label, n) { return '<a class="chip" href="' + href + '"' + (on ? ' aria-current="page"' : '') + '>' + label + (n != null ? ' <i>' + num(n) + '</i>' : '') + '</a>'; }
  function bar() {
    var cats = META.cats, cn = catName(C);
    $('cats').innerHTML = link('/doodles/', !C, bi('ทั้งหมด', 'All'), META.total) + ['front', 'place', 'minisite', 'scene', 'cover'].filter(function (c) { return cats[c]; })
      .map(function (c) { var n = catName(c); return link('/doodles/' + n.path + '/', C === c, bi(n.th, n.en), cats[c].n); }).join('');
    var subs = C && cats[C] ? Object.keys(cats[C].subs).sort(function (a, b) { return cats[C].subs[b] - cats[C].subs[a] || a.localeCompare(b); }) : [];
    $('subs').innerHTML = subs.map(function (s) { var k = C === 'minisite' ? { th: s.replace(/-/g, ' '), en: s.replace(/-/g, ' ') } : kindName(C, s); return link('/doodles/' + cn.path + '/' + esc(s) + '/', SUB === s, bi(esc(k.th), esc(k.en)), cats[C].subs[s]); }).join('');
    $('subs').hidden = !subs.length;
    $('sorts').innerHTML = [['new', 'ใหม่ก่อน', 'Newest'], ['old', 'เก่าก่อน', 'Oldest'], ['liked', 'คนชอบมาก', 'Most liked'], ['contro', 'เห็นต่างกัน', 'Controversial'], ['looks', 'สวยที่สุด', 'Best looking'],
      ['favs', 'เก็บเป็นโปรดมาก', 'Most favourited'], ['az', 'ก–ฮ', 'A–Z'], ['changed', 'เพิ่งเปลี่ยน', 'Recently changed'], ['versions', 'หลายรุ่น', 'Most versions']]
      .map(function (s) { return chip('sort', s[0], S.sort === s[0], bi(s[1], s[2])); }).join('');
    var F = META.feats || {}, nf = Object.keys(favs()).length;
    $('feats').innerHTML = chip('mine', '1', S.mine, heart(true) + ' ' + bi('รายการโปรดของฉัน', 'My favourites'), nf) +
      Object.keys(F).map(function (f) { return chip('feat', f, S.feat === f, bi(esc(F[f].th), esc(F[f].en)), F[f].n); }).join('');
    var q = $('q'); q.placeholder = lang === 'th' ? 'ค้นหา ชื่อ ชนิด วันที่' : 'Search names, kinds, dates'; if (q.value !== S.q) q.value = S.q;
  }
  function list() {
    var cn = C ? catName(C) : null, kn = SUB ? (C === 'minisite' ? null : kindName(C, SUB)) : null;
    shell('<p class="crumb"><a href="/doodles/">' + bi('ดูเดิล', 'Doodles') + '</a>' + (cn ? ' › <a href="/doodles/' + cn.path + '/">' + bi(cn.th, cn.en) + '</a>' : '') + '</p>' +
      '<h1>' + (kn ? bi(esc(kn.th), esc(kn.en)) : SUB ? esc(SUB.replace(/-/g, ' ')) : cn ? bi(cn.th, cn.en) : bi('ดูเดิล', 'Doodles')) + ' <span class="count" id="count"></span></h1>' +
      (C ? '' : '<p class="lede">' + bi('ภาพวาดเคลื่อนไหวทุกภาพของมดแดง ทั้งที่เคยวาด กำลังวาด และวางแผนไว้ ทุกรุ่น เรียงตามวัน แต่ละภาพลิงก์กลับไปหน้าของมันและแชร์ได้',
        'Every moving drawing on Mot Dang, past, present and planned, every version, by date. Each links back to its page and can be shared.') +
        ' <span class="upd">' + bi('ปรับล่าสุด ', 'updated ') + day(META.updated) + ' · ' + bi(num(META.versions) + ' รุ่น', num(META.versions) + ' versions') + '</span></p>') +
      '<p><a class="btn" href="/doodles/pick/">' + bi('ภาพไหนดีกว่า', 'Which is better?') + ' →</a></p>' +
      '<nav class="row wrapr" id="cats" aria-label="หมวด · categories"></nav><nav class="row" id="subs" aria-label="ชนิด · kinds"></nav>' +
      '<div id="tools" role="search"><input id="q" type="search" autocomplete="off" aria-label="ค้นหา · search"><div class="row" id="sorts"></div><div class="row" id="feats" aria-label="รายการโปรด ลักษณะ · favourites, features"></div></div>' +
      '<main id="list" aria-live="polite"></main>');
    shell.re = bar;
    $('sorts').onclick = function (e) { var b = e.target.closest('.chip'); if (b) { S.sort = b.dataset.sort; show(); } };
    $('feats').onclick = function (e) {
      var b = e.target.closest('.chip'); if (!b) return;
      if (b.dataset.mine) S.mine = !S.mine; else S.feat = S.feat === b.dataset.feat ? '' : b.dataset.feat;
      show();
    };
    $('list').addEventListener('click', function (e) { var b = e.target.closest('.cv .vb'); if (b) { e.preventDefault(); cardVote(b); } });
    var qt = 0; $('q').oninput = function (e) { clearTimeout(qt); qt = setTimeout(function () { S.q = e.target.value.trim(); show(); }, 250); };
    engine(META.engine).then(function () {
      show();
      scores().then(function () { Array.prototype.forEach.call(document.querySelectorAll('.cv'), function (box) { box.innerHTML = cardVotes(box.dataset.id, +box.dataset.v); }); });
      addEventListener('mddoodler', function () { paint(REDUCED ? 4200 : performance.now(), true); });
      if (!REDUCED) (function loop(t) { paint(t); requestAnimationFrame(loop); })(0);
    });
  }

  Promise.all([get('/doodles/data/meta.json'), get('/front/ridge.json')]).then(function (a) {
    META = a[0] || { total: 0, cats: {}, chunk: 240 }; NM = META.names || NM; RIDGE = a[1] && a[1].ele ? a[1] : null;
    if (C === 'one') one(); else if (C === 'pick') pick(); else list();
  });
})();
