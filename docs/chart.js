// Renders the four pillars. Nothing here sends anything anywhere.
(function () {
  'use strict';
  var form = document.getElementById('chartform');
  var out = document.getElementById('chartout');
  if (!form || !out || !window.MDBazi) return;

  function bi(th, en) {
    return '<span class="bi"><span class="th">' + th +
           '</span><span class="en"><span class="th"> · </span>' + en + '</span></span>';
  }
  var ELEM_TH = ['ไม้', 'ไฟ', 'ดิน', 'ทอง', 'น้ำ'];
  var ANIMAL_TH = ['ชวด', 'ฉลู', 'ขาล', 'เถาะ', 'มะโรง', 'มะเส็ง',
                   'มะเมีย', 'มะแม', 'วอก', 'ระกา', 'จอ', 'กุน'];
  var WHO = [['ปี', 'Year'], ['เดือน', 'Month'], ['วัน', 'Day'], ['ชั่วโมง', 'Hour']];

  var TERMS = null, loading = null;
  function terms() {
    if (TERMS) return Promise.resolve(TERMS);
    if (!loading) {
      var root = document.documentElement.getAttribute('data-root') || '';
      loading = fetch(root + 'data/solar_terms.json')
        .then(function (r) { return r.json(); })
        .then(function (j) { TERMS = j; return j; });
    }
    return loading;
  }

  function cell(p, who, extra) {
    if (!p) {
      return '<div class="pillar unknown"><div class="who">' + bi(who[0], who[1]) +
             '</div><div class="zh">—</div><div class="pin">' +
             bi('ไม่ทราบเวลาเกิด', 'birth time unknown') + '</div></div>';
    }
    return '<div class="pillar"><div class="who">' + bi(who[0], who[1]) +
           '</div><div class="zh">' + p.zh + '</div><div class="pin">' + p.pinyin +
           '</div><div class="pin">' + bi('ธาตุ' + ELEM_TH[p.element], p.elementEn) +
           '</div>' + (extra || '') + '</div>';
  }

  function render(c) {
    if (c.error) {
      out.innerHTML = '<p class="chartnote">' +
        bi('ตารางสุริยคติมีเฉพาะปี ' + c.from + '–' + c.to,
           'The solar-term table only covers ' + c.from + '–' + c.to) + '</p>';
      out.hidden = false;
      return;
    }
    var p = c.pillars;
    var animal = '<div class="pin">' +
      bi('นักษัตร' + ANIMAL_TH[p.year.branch], p.year.animal) + '</div>';
    var html = '<div class="pillars">' +
      cell(p.year, WHO[0], animal) + cell(p.month, WHO[1]) +
      cell(p.day, WHO[2]) + cell(p.hour, WHO[3], '') + '</div>';

    html += '<p>' + bi('ธาตุประจำตัว (日主) — ' + c.dayMaster.zh + ' ธาตุ' +
                       ELEM_TH[c.dayMaster.element],
                       'Day master ' + c.dayMaster.pinyin + ', ' + c.dayMaster.elementEn) + '</p>';

    var tally = '<div class="elements">';
    for (var i = 0; i < 5; i++) {
      var n = c.elements[i];
      tally += '<span' + (n ? '' : ' class="none"') + '>' + c.elementNames[i][0] + ' ' +
               bi('ธาตุ' + ELEM_TH[i], c.elementNames[i][1]) + ' × ' + n + '</span>';
    }
    tally += '</div>';
    html += tally;
    html += '<p class="chartnote">' +
      bi(c.hasHour ? 'นับจากทั้งสี่เสา' : 'นับจากสามเสา เพราะไม่ได้ใส่เวลาเกิด',
         c.hasHour ? 'Counted across all four pillars.'
                   : 'Counted across three pillars — no birth time was given.') + '</p>';
    out.innerHTML = html;
    out.hidden = false;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var d = document.getElementById('bdate').value;
    if (!d) return;
    var t = document.getElementById('btime').value;
    var parts = d.split('-').map(Number);
    var hasHour = !!t;
    var hour = hasHour ? Number(t.split(':')[0]) + Number(t.split(':')[1]) / 60 : 0;
    terms().then(function (T) {
      render(window.MDBazi.chart(T, parts[0], parts[1], parts[2], hour, hasHour));
      out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });
})();
