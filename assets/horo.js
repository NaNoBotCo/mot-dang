// Per-sign horoscopes, computed in the reader's browser — Thai มหาทักษา,
// Chinese branch relations over the sexagenary day, Western whole-sign
// transits. The arithmetic mirrors importers/make_horo.py line for line and
// tests/test_horo_parity.py holds the two together; edit both or neither.
//
// Words and tables come from data/horo.json so this file and the Python page
// builder can never say different things. Nothing here transmits anything:
// a birth date typed into the finder is arithmetic on this machine and then
// a localStorage note, exactly like /chart.html.
(function (global) {
  'use strict';

  var RAD = Math.PI / 180;

  function mod(n, k) { return ((n % k) + k) % k; }

  function gregToJD(y, m, d, hour) {
    hour = hour || 0;
    if (m <= 2) { y -= 1; m += 12; }
    var a = Math.floor(y / 100), b = 2 - a + Math.floor(a / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1))
         + d + b - 1524.5 + hour / 24;
  }

  // ---- Chinese: sexagenary day, anchored 2000-01-07 (CST) = 甲子 ----------
  var DAY_ANCHOR = gregToJD(2000, 1, 7) - 8 / 24;
  function dayPillarIndex(y, m, d) {
    return mod(Math.round(gregToJD(y, m, d) - 8 / 24 - DAY_ANCHOR), 60);
  }

  var PO = {'0,9': 1, '1,4': 1, '2,11': 1, '3,6': 1, '5,8': 1, '7,10': 1};
  var XING = [[2, 5, 8], [1, 7, 10], [0, 3]];
  function branchRelation(dayB, yourB) {
    if (mod(dayB - yourB, 12) === 6) return 'chong';
    if (mod(dayB + yourB, 12) === 1) return 'liuhe';
    var s = mod(dayB - yourB, 12);
    if (dayB !== yourB && (s === 4 || s === 8)) return 'sanhe';
    if (dayB === yourB) return 'same';
    for (var g = 0; g < XING.length; g++) {
      if (XING[g].indexOf(dayB) > -1 && XING[g].indexOf(yourB) > -1) return 'xing';
    }
    if (mod(dayB + yourB, 12) === 7) return 'hai';
    if (PO[dayB + ',' + yourB] || PO[yourB + ',' + dayB]) return 'po';
    return 'plain';
  }

  // ---- Thai: เถลิงศก from the จุลศักราช day-count, and the ทักษา wheel ----
  function thaloengsokJD(cs) {
    return 1954167.5 + Math.floor((292207 * cs + 373) / 800);
  }
  function jdToParts(jd) {
    jd += 0.5;
    var z = Math.floor(jd), a = z;
    if (z >= 2299161) {
      var al = Math.floor((z - 1867216.25) / 36524.25);
      a = z + 1 + al - Math.floor(al / 4);
    }
    var b = a + 1524, c = Math.floor((b - 122.1) / 365.25),
        dd = Math.floor(365.25 * c), e = Math.floor((b - dd) / 30.6001);
    var day = b - dd - Math.floor(30.6001 * e);
    var month = e < 14 ? e - 1 : e - 13;
    var year = month > 2 ? c - 4716 : c - 4715;
    return { y: year, m: month, d: day };
  }
  function csForDate(y, m, d) {
    var jd = gregToJD(y, m, d), cs = y - 638;
    if (jd < thaloengsokJD(cs)) cs -= 1;
    else if (jd >= thaloengsokJD(cs + 1)) cs += 1;
    return cs;
  }
  function thaiAnimalIndex(cs) { return mod(cs + 10, 12); }

  var WHEEL = [0, 1, 2, 3, 6, 4, 7, 5];
  function wheelStation(birthSlot, todaySlot) {
    return mod(WHEEL.indexOf(todaySlot) - WHEEL.indexOf(birthSlot), 8);
  }

  // ---- Western: Meeus Sun/Moon, Schlyter planets --------------------------
  function sunLongitude(jd) {
    var t = (jd - 2451545.0) / 36525.0;
    var l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t;
    var m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t;
    var mr = m * RAD;
    var c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * Math.sin(mr)
          + (0.019993 - 0.000101 * t) * Math.sin(2 * mr)
          + 0.000289 * Math.sin(3 * mr);
    var omega = 125.04 - 1934.136 * t;
    return mod(l0 + c - 0.00569 - 0.00478 * Math.sin(omega * RAD), 360);
  }

  function moonLongitude(jd) {
    var t = (jd - 2451545.0) / 36525.0;
    var lp = 218.316 + 481267.8813 * t;
    var m = 134.963 + 477198.8676 * t;
    var f = 93.272 + 483202.0175 * t;
    var d = 297.850 + 445267.1115 * t;
    var ms = 357.529 + 35999.0503 * t;
    var lon = lp + 6.289 * Math.sin(m * RAD) - 1.274 * Math.sin((m - 2 * d) * RAD)
      + 0.658 * Math.sin(2 * d * RAD) - 0.186 * Math.sin(ms * RAD)
      - 0.059 * Math.sin((2 * m - 2 * d) * RAD) - 0.057 * Math.sin((m - 2 * d + ms) * RAD)
      + 0.053 * Math.sin((m + 2 * d) * RAD) + 0.046 * Math.sin((2 * d - ms) * RAD)
      + 0.041 * Math.sin((m - ms) * RAD) - 0.035 * Math.sin(d * RAD)
      - 0.031 * Math.sin((m + ms) * RAD) + 0.015 * Math.sin((2 * f - 2 * d) * RAD);
    return mod(lon, 360);
  }

  function kepler(m, e) {
    m = mod(m, 360);
    var ev = m + (180 / Math.PI) * e * Math.sin(m * RAD) * (1 + e * Math.cos(m * RAD));
    for (var i = 0; i < 8; i++) {
      ev = ev - (ev - (180 / Math.PI) * e * Math.sin(ev * RAD) - m)
             / (1 - e * Math.cos(ev * RAD));
    }
    return ev;
  }

  var EL = {
    mercury: [48.3313, 3.24587e-5, 7.0047, 5.00e-8, 29.1241, 1.01444e-5,
              0.387098, 0.0, 0.205635, 5.59e-10, 168.6562, 4.0923344368],
    venus: [76.6799, 2.46590e-5, 3.3946, 2.75e-8, 54.8910, 1.38374e-5,
            0.723330, 0.0, 0.006773, -1.302e-9, 48.0052, 1.6021302244],
    mars: [49.5574, 2.11081e-5, 1.8497, -1.78e-8, 286.5016, 2.92961e-5,
           1.523688, 0.0, 0.093405, 2.516e-9, 18.6021, 0.5240207766],
    jupiter: [100.4542, 2.76854e-5, 1.3030, -1.557e-7, 273.8777, 1.64505e-5,
              5.20256, 0.0, 0.048498, 4.469e-9, 19.8950, 0.0830853001],
    saturn: [113.6634, 2.38980e-5, 2.4886, -1.081e-7, 339.3939, 2.97661e-5,
             9.55475, 0.0, 0.055546, -9.499e-9, 316.9670, 0.0334442282]
  };

  function helio(name, d) {
    var q = EL[name];
    var n = q[0] + q[1] * d, i = q[2] + q[3] * d, w = q[4] + q[5] * d,
        a = q[6] + q[7] * d, e = q[8] + q[9] * d, m = q[10] + q[11] * d;
    var ev = kepler(m, e);
    var xv = a * (Math.cos(ev * RAD) - e);
    var yv = a * Math.sqrt(1 - e * e) * Math.sin(ev * RAD);
    var v = Math.atan2(yv, xv) / RAD;
    var r = Math.sqrt(xv * xv + yv * yv);
    var u = (v + w) * RAD;
    var xh = r * (Math.cos(n * RAD) * Math.cos(u)
                  - Math.sin(n * RAD) * Math.sin(u) * Math.cos(i * RAD));
    var yh = r * (Math.sin(n * RAD) * Math.cos(u)
                  + Math.cos(n * RAD) * Math.sin(u) * Math.cos(i * RAD));
    var zh = r * Math.sin(u) * Math.sin(i * RAD);
    var lonecl = mod(Math.atan2(yh, xh) / RAD, 360);
    var latecl = Math.asin(zh / r);
    if (name === 'jupiter' || name === 'saturn') {
      var mj = (19.8950 + 0.0830853001 * d) * RAD;
      var ms = (316.9670 + 0.0334442282 * d) * RAD;
      if (name === 'jupiter') {
        lonecl += -0.332 * Math.sin(2 * mj - 5 * ms - 67.6 * RAD)
                - 0.056 * Math.sin(2 * mj - 2 * ms + 21 * RAD)
                + 0.042 * Math.sin(3 * mj - 5 * ms + 21 * RAD)
                - 0.036 * Math.sin(mj - 2 * ms)
                + 0.022 * Math.cos(mj - ms)
                + 0.023 * Math.sin(2 * mj - 3 * ms + 52 * RAD)
                - 0.016 * Math.sin(mj - 5 * ms - 69 * RAD);
      } else {
        lonecl += 0.812 * Math.sin(2 * mj - 5 * ms - 67.6 * RAD)
                - 0.229 * Math.cos(2 * mj - 4 * ms - 2 * RAD)
                + 0.119 * Math.sin(mj - 2 * ms - 3 * RAD)
                + 0.046 * Math.sin(2 * mj - 6 * ms - 69 * RAD)
                + 0.014 * Math.sin(mj - 3 * ms + 32 * RAD);
      }
    }
    return [r * Math.cos(lonecl * RAD) * Math.cos(latecl),
            r * Math.sin(lonecl * RAD) * Math.cos(latecl)];
  }

  function sunXY(d) {
    var w = 282.9404 + 4.70935e-5 * d;
    var e = 0.016709 - 1.151e-9 * d;
    var m = 356.0470 + 0.9856002585 * d;
    var ev = kepler(m, e);
    var xv = Math.cos(ev * RAD) - e;
    var yv = Math.sqrt(1 - e * e) * Math.sin(ev * RAD);
    var v = Math.atan2(yv, xv) / RAD;
    var r = Math.sqrt(xv * xv + yv * yv);
    var lon = mod(v + w, 360);
    return [r * Math.cos(lon * RAD), r * Math.sin(lon * RAD)];
  }

  function planetLongitude(name, jd) {
    var d = jd - 2451543.5;
    var h = helio(name, d), s = sunXY(d);
    return mod(Math.atan2(h[1] + s[1], h[0] + s[0]) / RAD, 360);
  }

  function longitudes(jd) {
    return [sunLongitude(jd), moonLongitude(jd),
            planetLongitude('mercury', jd), planetLongitude('venus', jd),
            planetLongitude('mars', jd), planetLongitude('jupiter', jd),
            planetLongitude('saturn', jd)];
  }

  // ---- the reading composers (same arithmetic as make_horo.py) -----------
  var ASPECT_OF = {0: 'conj', 2: 'sextile', 10: 'sextile', 3: 'square',
                   9: 'square', 4: 'trine', 8: 'trine', 6: 'opp'};
  var PLANET_WEIGHT = [1, 0, 1, 2, 2, 3, 3];

  function aspectScore(T, pi, akey) {
    var kind = T.west.planets[pi].kind;
    if (akey === 'trine' || akey === 'sextile') return kind === 'benefic' ? 2 : 1;
    if (akey === 'conj') return { benefic: 2, mid: 1, malefic: -2 }[kind];
    return kind === 'malefic' ? -2 : -1;
  }

  function westReading(T, sign, lons) {
    var psigns = lons.map(function (x) { return mod(Math.floor(x / 30), 12); });
    var moonA = ASPECT_OF[mod(sign - psigns[1], 12)] || null;
    var best = null, bestRank = -1, score = 0;
    for (var pi = 0; pi < lons.length; pi++) {
      if (pi === 1) continue;
      var akey = ASPECT_OF[mod(sign - psigns[pi], 12)];
      if (!akey) continue;
      score += aspectScore(T, pi, akey);
      var rank = PLANET_WEIGHT[pi] * 10 + T.west.aspects[akey].sharp;
      if (rank > bestRank) { bestRank = rank; best = [pi, akey]; }
    }
    if (moonA) score += aspectScore(T, 1, moonA);
    var v = score >= 2 ? 'ดี' : (score <= -2 ? 'ระวัง' : 'กลาง');
    return { moon_sign: psigns[1], moon_aspect: moonA, top: best, verdict: v };
  }

  // ------------------------------------------------------------ rendering
  var DATA = null;

  function bi(th, en) {
    return '<span class="bi"><span class="th">' + th +
           '</span><span class="en"><span class="th"> · </span>' + en + '</span></span>';
  }
  function verdictPill(T, v) {
    var meta = T.verdicts[v];
    return '<span class="ssverdict v-' + meta.cls + '">' + bi(v, meta.en) + '</span>';
  }
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function recall(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  // Today in the reader's own clock. The readings are day-granular on
  // purpose — a daily column speaks for the day, so positions are taken at
  // 12:00 เวลาไทย and stay put from midnight to midnight.
  function todayParts() {
    var n = new Date();
    return { y: n.getFullYear(), m: n.getMonth() + 1, d: n.getDate(),
             jsDay: n.getDay(), hour: n.getHours() };
  }
  function noonJD(p) { return gregToJD(p.y, p.m, p.d, 5.0); }  // 12:00 ICT in UT

  function thaiTodaySlot(p) {
    return (p.jsDay === 3 && p.hour >= 18) ? 7 : p.jsDay;
  }

  function currentYearBranch(p) {
    // Popular reckoning: the animal changes at ตรุษจีน.
    var cny = DATA.years.cny[String(p.y)];
    var iso = p.y + '-' + String(p.m).padStart(2, '0') + '-' + String(p.d).padStart(2, '0');
    var gy = (cny && iso < cny) ? p.y - 1 : p.y;
    return { year: gy, branch: mod(gy - 4, 12) };
  }

  function thaiReading(T, birthSlot) {
    var p = todayParts();
    var t = thaiTodaySlot(p);
    var st = T.thai.stations[wheelStation(birthSlot, t)];
    var me = T.thai.days[birthSlot];
    var today = T.thai.days[t];
    var kk = T.thai.days[WHEEL[mod(WHEEL.indexOf(birthSlot) + 7, 8)]];
    return { station: st, me: me, today: today, todaySlot: t, kalakini: kk,
             cs: csForDate(p.y, p.m, p.d) };
  }

  function chineseReading(T, yourB) {
    var p = todayParts();
    var dp = dayPillarIndex(p.y, p.m, p.d);
    var yb = currentYearBranch(p);
    var dayRel = T.chinese.day_rel[branchRelation(mod(dp, 12), yourB)];
    var yearRel = T.chinese.year_rel[branchRelation(yb.branch, yourB)];
    return { dp: dp, dayBranch: mod(dp, 12), dayStem: mod(dp, 10),
             yearBranch: yb.branch, dayRel: dayRel, yearRel: yearRel };
  }

  // ---- the finder: one birth date -> all three signs, locally ------------
  function findSigns(y, m, d) {
    var out = {};
    var jsDay = new Date(y, m - 1, d).getDay();
    out.thaiSlot = jsDay;                      // Wednesday resolves by chip
    out.wednesday = jsDay === 3;
    var cs = csForDate(y, m, d);
    out.thaiAnimal = thaiAnimalIndex(cs);
    out.cs = cs;
    var iso = y + '-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0');
    var cny = DATA.years.cny[String(y)];
    var cnYear = (cny && iso < cny) ? y - 1 : y;
    out.cnBranch = mod(cnYear - 4, 12);
    out.cnStem = mod(cnYear - 4, 10);
    out.cnYear = cnYear;
    out.cnyKnown = !!cny;
    // Sun sign from the actual longitude at noon ICT of the birth day; a
    // birthday ON an ingress day gets a note rather than a silent guess.
    var lon = sunLongitude(gregToJD(y, m, d, 5.0));
    out.sunSign = mod(Math.floor(lon / 30), 12);
    var lonAM = sunLongitude(gregToJD(y, m, d, -7.0));   // 00:00 ICT
    var lonPM = sunLongitude(gregToJD(y, m, d, 17.0));   // 24:00 ICT
    out.cusp = Math.floor(lonAM / 30) !== Math.floor(lonPM / 30);
    return out;
  }

  // ---- DOM wiring --------------------------------------------------------
  function chipsOf(sys) {
    return Array.prototype.slice.call(
      document.querySelectorAll('[data-hchips="' + sys + '"] .hochip'));
  }
  function markChips(sys, idx) {
    chipsOf(sys).forEach(function (c) {
      c.classList.toggle('on', +c.dataset.hchip === idx);
      c.setAttribute('aria-pressed', +c.dataset.hchip === idx ? 'true' : 'false');
    });
  }
  function fill(sys, html) {
    Array.prototype.slice.call(
      document.querySelectorAll('[data-hread="' + sys + '"]')
    ).forEach(function (el) { el.innerHTML = html; });
  }

  function renderThai(T, slot) {
    var r = thaiReading(T, slot);
    var lines = ['<p class="horeadline">' + verdictPill(T, r.station.v) + ' ' +
      '<b>' + bi(r.station.th, r.station.en) + '</b> — ' +
      bi(r.station.mean_th, r.station.mean_en) + '</p>',
      '<p>' + bi(r.station.line_th, r.station.line_en) + '</p>',
      '<p class="tinynote">' +
      bi('วันนี้' + r.today.th + ' อยู่ตำแหน่ง' + r.station.th + 'ของคนเกิด' + r.me.th,
         'Today, ' + r.today.en + ', stands at ' + r.station.en +
         ' on the wheel of a ' + r.me.en + ' child') + '</p>',
      '<p class="hocolours"><span class="hocol"><span class="hoswatch" style="background:' + r.me.hex +
      '"></span>' + bi('สีของคุณ ' + r.me.colour_th, 'your colour: ' + r.me.colour_en) + '</span>' +
      '<span class="hocol"><span class="hoswatch hoavoid" style="background:' + r.kalakini.hex + '"></span>' +
      bi('เลี่ยง' + r.kalakini.colour_th + ' (สีกาลกิณี)',
         'ease off ' + r.kalakini.colour_en + ' (the กาลกิณี colour)') + '</span>' +
      '<span class="hocol">' + bi('กำลังวัน ' + r.me.strength, 'day strength ' + r.me.strength) + '</span></p>'];
    fill('th', lines.join(''));
    markChips('th', slot);
    var wheelBox = document.getElementById('howheel-th');
    if (wheelBox) pointThaiWheel(T, slot, r.todaySlot);
  }

  function renderChinese(T, yourB) {
    var r = chineseReading(T, yourB);
    var br = T.chinese.branches;
    var pillarZh = T.chinese.stems[r.dayStem] + br[r.dayBranch].zh;
    var relTag = r.dayRel.zh ? r.dayRel.zh + ' ' + r.dayRel.th : r.dayRel.th;
    var html = ['<p class="horeadline">' + verdictPill(T, r.dayRel.v) + ' ' +
      '<b>' + bi('วันนี้' + relTag + 'กับปี' + br[yourB].th,
                 'today is ' + r.dayRel.en + ' for the ' + br[yourB].en + ' year') +
      '</b></p>',
      '<p>' + bi(r.dayRel.line_th, r.dayRel.line_en) + '</p>',
      '<p class="tinynote">' + bi('เสาวันนี้ ' + pillarZh + ' (วัน' + br[r.dayBranch].th + ')',
        'day pillar ' + pillarZh + ' — a ' + br[r.dayBranch].en + ' day') + '</p>',
      '<p class="hoyearrel">' + verdictPill(T, r.yearRel.v) + ' ' +
      bi(r.yearRel.th + ' — ' + r.yearRel.line_th,
         r.yearRel.en + ' — ' + r.yearRel.line_en) + '</p>'];
    // With a full birth year from the finder the five elements join in.
    var by = recall('md.horo.cnyear');
    if (by && DATA.years.cny[by]) {
      var stem = mod(+by - 4, 10);
      var se = T.chinese.stem_element[stem];
      var de = T.chinese.stem_element[r.dayStem];
      var rel = se === de ? 'same'
        : (mod(se + 1, 5) === de ? 'i_generate'
        : (mod(de + 1, 5) === se ? 'generates_me'
        : (mod(se + 2, 5) === de ? 'i_overcome' : 'overcomes_me')));
      var wr = T.chinese.wuxing_rel[rel];
      html.push('<p class="tinynote">' +
        bi('ธาตุปีคุณ' + T.chinese.elem_th[se] + ' พบธาตุวัน' + T.chinese.elem_th[de] +
           ' — ' + wr.th,
           'your year element ' + T.chinese.elem_en[se] + ' meets the day’s ' +
           T.chinese.elem_en[de] + ' — ' + wr.en) + '</p>');
    }
    fill('cn', html.join(''));
    markChips('cn', yourB);
    if (document.getElementById('howheel-cn')) pointBranchWheel(T, yourB, r);
  }

  function renderWest(T, sign) {
    var p = todayParts();
    var lons = longitudes(noonJD(p));
    var r = westReading(T, sign, lons);
    var s = T.west.signs[sign];
    var html = ['<p class="horeadline">' + verdictPill(T, r.verdict) + ' ' +
      '<b>' + bi('ราศี' + s.th.replace('ราศี', ''), s.en) + '</b> ' +
      '<span class="hoglyph">' + s.glyph + '</span></p>'];
    if (r.moon_aspect) {
      var ma = T.west.aspects[r.moon_aspect];
      html.push('<p>' + bi('ดวงจันทร์' + ma.th + ' — อารมณ์และเรื่องใกล้ตัว' +
        (r.moon_aspect === 'conj' ? 'เด่นชัดมาก' : 'ขยับตาม'),
        'the Moon ' + ma.line_en) + '</p>');
    } else {
      html.push('<p>' + bi('ดวงจันทร์ไม่ทำมุมวันนี้ ใจนิ่งดี เหมาะงานต้องสมาธิ',
        'no Moon aspect today — a settled mind, good for quiet work') + '</p>');
    }
    if (r.top) {
      var pl = T.west.planets[r.top[0]], ak = T.west.aspects[r.top[1]];
      html.push('<p>' + bi('ดาว' + pl.th + ak.th + ' — ' + pl.theme_th + ' ' + ak.line_th,
        pl.en + ' ' + ak.line_en + ' — the theme is ' + pl.theme_en) + '</p>');
    }
    html.push('<p class="tinynote">' +
      bi('ดวงจันทร์อยู่ราศี' + T.west.signs[r.moon_sign].th.replace('ราศี', ''),
         'the Moon is in ' + T.west.signs[r.moon_sign].en) + '</p>');
    fill('eu', html.join(''));
    markChips('eu', sign);
    if (document.getElementById('howheel-eu')) pointZodiacWheel(T, sign, lons);
  }

  // ---- wheels: the structure is drawn at build time; this only re-points --
  function polar(cx, cy, r, deg) {
    return [cx + r * Math.cos(deg * RAD), cy - r * Math.sin(deg * RAD)];
  }

  function pointThaiWheel(T, birthSlot, todaySlot) {
    // Station names travel round the octagon so that บริวาร sits on the
    // reader's own day; the rim highlight rests on today's deity.
    var bp = WHEEL.indexOf(birthSlot);
    for (var k = 0; k < 8; k++) {
      var el = document.getElementById('hwst-' + k);
      if (el) el.textContent = T.thai.stations[mod(k - bp, 8)].th;
    }
    // Seats are laid out clockwise from the top, so stepping the highlight
    // round by k seats is a positive SVG rotation of 45° each.
    var hi = document.getElementById('hw-today');
    if (hi) hi.setAttribute('transform',
      'rotate(' + (45 * WHEEL.indexOf(todaySlot)) + ' 110 110)');
    var kkEl = document.getElementById('hw-kk');
    if (kkEl) kkEl.setAttribute('transform',
      'rotate(' + (45 * mod(bp + 7, 8)) + ' 110 110)');
  }

  function pointBranchWheel(T, yourB, r) {
    // Twelve fixed branch seats; the chord shows today against you.
    var seat = function (b) { return polar(110, 110, 86, 90 - 30 * b); };
    var you = document.getElementById('cw-you'), day = document.getElementById('cw-day');
    var pu = seat(yourB), pd = seat(r.dayBranch);
    if (you) { you.setAttribute('cx', pu[0]); you.setAttribute('cy', pu[1]); }
    if (day) { day.setAttribute('cx', pd[0]); day.setAttribute('cy', pd[1]); }
    var chord = document.getElementById('cw-rel');
    if (chord) {
      chord.setAttribute('x1', pd[0]); chord.setAttribute('y1', pd[1]);
      chord.setAttribute('x2', pu[0]); chord.setAttribute('y2', pu[1]);
      chord.setAttribute('class', 'cwrel cwrel-' +
        branchRelation(r.dayBranch, yourB));
      chord.style.display = r.dayBranch === yourB ? 'none' : '';
    }
    var tri = document.getElementById('cw-sanhe');
    if (tri) {
      var pts = [yourB, mod(yourB + 4, 12), mod(yourB + 8, 12)].map(seat)
        .map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); });
      tri.setAttribute('points', pts.join(' '));
    }
  }

  function pointZodiacWheel(T, sign, lons) {
    // Planet glyphs at their real longitudes, 0° เมษ at the left, wheeling
    // counterclockwise — the chart convention.
    for (var pi = 0; pi < lons.length; pi++) {
      var g = document.getElementById('zw-p' + pi);
      if (!g) continue;
      var pos = polar(110, 110, 74, 180 + lons[pi]);
      g.setAttribute('x', pos[0]);
      g.setAttribute('y', pos[1] + 4);
    }
    var arc = document.getElementById('zw-you');
    if (arc) arc.setAttribute('transform',
      'rotate(' + (-30 * sign) + ' 110 110)');
  }

  // ---- boot ---------------------------------------------------------------
  function chosen(sys, fallback) {
    var v = recall('md.horo.' + sys);
    if (v === null && sys === 'eu') v = recall('md.sign');   // the old key
    var n = v === null ? NaN : +v;
    return isNaN(n) ? fallback : n;
  }

  function renderAll(T) {
    var p = todayParts();
    renderThai(T, chosen('th', thaiTodaySlot(p)));
    renderChinese(T, chosen('cn', currentYearBranch(p).branch));
    renderWest(T, chosen('eu', Math.floor(sunLongitude(noonJD(p)) / 30) % 12));
  }

  function wireFinder(T) {
    var form = document.getElementById('horofind');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = form.querySelector('input[type=date]').value;
      if (!v) return;
      var ymd = v.split('-').map(Number);
      var f = findSigns(ymd[0], ymd[1], ymd[2]);
      store('md.horo.th', f.thaiSlot); store('md.horo.cn', f.cnBranch);
      store('md.horo.eu', f.sunSign); store('md.horo.cnyear', String(f.cnYear));
      var T2 = DATA.tables;
      var bits = [
        bi('เกิด' + T2.thai.days[f.thaiSlot].th, 'born on a ' + T2.thai.days[f.thaiSlot].en),
        bi('ปี' + T2.thai.zodiac[f.thaiAnimal].th + ' (จ.ศ. ' + f.cs + ')',
           'year of the ' + T2.thai.zodiac[f.thaiAnimal].en),
        bi('นักษัตรจีน ' + T2.chinese.branches[f.cnBranch].th +
           ' ธาตุ' + T2.chinese.elem_th[T2.chinese.stem_element[f.cnStem]],
           T2.chinese.elem_en[T2.chinese.stem_element[f.cnStem]] + ' ' +
           T2.chinese.branches[f.cnBranch].en),
        bi('ราศี' + T2.west.signs[f.sunSign].th.replace('ราศี', '') + ' ' +
           T2.west.signs[f.sunSign].glyph,
           T2.west.signs[f.sunSign].en)];
      var notes = [];
      if (f.wednesday) {
        notes.push(bi('เกิดวันพุธหลังราว 18:00 นับเป็นพุธกลางคืน (ราหู) — แตะเม็ดราหูได้เลย',
          'born on a Wednesday after ~18:00 counts as Wednesday night (ราหู) — tap the ราหู chip'));
      }
      if (f.cusp) {
        notes.push(bi('วันเกิดคุณเป็นวันที่อาทิตย์ย้ายราศีพอดี เวลาเกิดชี้ขาด',
          'the Sun changed signs on your birthday — the birth hour decides'));
      }
      if (!f.cnyKnown) {
        notes.push(bi('ปีนอกตาราง (' + DATA.years.from + '–' + DATA.years.to +
          ') นักษัตรจีนนับจากปีสากล', 'outside the table (' + DATA.years.from +
          '–' + DATA.years.to + ') the Chinese year is counted from the civil year'));
      }
      var out = document.querySelector('[data-hfound]');
      if (out) {
        out.innerHTML = '<p class="hofoundrow">' + bits.join(' · ') + '</p>' +
          (notes.length ? '<p class="tinynote">' + notes.join(' · ') + '</p>' : '');
        out.hidden = false;
      }
      renderAll(T);
    });
  }

  function init() {
    var need = document.querySelector('[data-hread]');
    if (!need) return;
    var root = document.documentElement.getAttribute('data-root') || '';
    fetch(root + 'data/horo.json')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        DATA = j;
        var T = j.tables;
        ['th', 'cn', 'eu'].forEach(function (sys) {
          chipsOf(sys).forEach(function (c) {
            c.addEventListener('click', function () {
              store('md.horo.' + sys, c.dataset.hchip);
              if (sys === 'th') renderThai(T, +c.dataset.hchip);
              if (sys === 'cn') renderChinese(T, +c.dataset.hchip);
              if (sys === 'eu') renderWest(T, +c.dataset.hchip);
            });
          });
        });
        wireFinder(T);
        renderAll(T);
      })
      .catch(function () { /* the page keeps its baked reading */ });
  }

  global.MDHoro = {
    gregToJD: gregToJD, dayPillarIndex: dayPillarIndex,
    branchRelation: branchRelation, thaloengsokJD: thaloengsokJD,
    csForDate: csForDate, thaiAnimalIndex: thaiAnimalIndex,
    wheelStation: wheelStation, sunLongitude: sunLongitude,
    moonLongitude: moonLongitude, planetLongitude: planetLongitude,
    longitudes: longitudes, westReading: westReading, findSigns: findSigns,
    _setData: function (d) { DATA = d; }
  };

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
}(typeof window !== 'undefined' ? window : this));
