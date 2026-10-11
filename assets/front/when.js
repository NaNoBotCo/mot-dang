/* The front page's one time model: Bangkok's clock, the day that ends at 03:00, and the band an event
   belongs to (today / near / ahead). front.js, wx.js and tiles.js take their date code from here
   (design: notes/calendar-design-2026-10-11.txt, D). Loaded first; a classic script, no modules. */
(function (W) {
'use strict';
function bkk(t) { return new Date(t + 7 * 3600e3); }
function hhmm(t) { return bkk(t).toISOString().slice(11, 16); }
function ymd(t) { return bkk(t).toISOString().slice(0, 10); }
function at(s) { return Date.parse(s.replace(' ', 'T') + '+07:00'); }
/* an event's end: a bare date (a festival's last day) runs to the end of that day */
function atEnd(s) { return s.length > 10 ? at(s) : at(s + ' 23:59:59'); }
var MON_TH = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
var MON_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
var DAY_TH = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'], DAY_EN = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
function be(year) { return year + 543; }
function span(e) {
  var s = at(e.s), en = e.e ? (e.e.length > 10 ? at(e.e) : at(e.e + ' 23:59:59')) : (e.ad ? s + 864e5 - 1 : s + 2 * 3600e3);
  return [s, Math.max(s, en)];
}
function ics(e) {
  var z = function (ms) { return isNaN(ms) ? '' : new Date(ms).toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z'; };
  var s0 = at(e.s), end = e.e ? atEnd(e.e) : s0 + 7200e3;
  var t = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//motdang.net//front//EN', 'BEGIN:VEVENT', 'UID:' + e.k + '-' + e.s.slice(0, 10) + '@motdang.net',
    'DTSTAMP:' + z(s0), 'DTSTART:' + z(s0), 'DTEND:' + z(end), 'SUMMARY:' + e.t.replace(/[,;]/g, ' '), 'LOCATION:' + (e.v || '').replace(/[,;]/g, ' '),
    'URL:' + (e.url || 'https://motdang.net/'), 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
  return 'data:text/calendar;charset=utf-8,' + encodeURIComponent(t);
}
/* a day ends at 03:00 (calendar design, 2026-10-11): 01:30 tonight is still today's.
   One boundary for the bands, the clock and the gates. */
var DAY_END_H = 3;
var AHEAD_DAYS = 214;                                   /* plan ahead runs to about seven months */
function dayOf(t) { return ymd(t - DAY_END_H * 3600e3); }
function dayGap(a, b) { return Math.round((Date.parse(a + 'T12:00:00Z') - Date.parse(b + 'T12:00:00Z')) / 864e5); }
/* the date an event belongs to on its first day: an all-day event (stored at 00:00) its own date,
   never the night before; any other the day its start moment falls in */
function firstDay(e) { return e.ad ? e.s.slice(0, 10) : dayOf(at(e.s)); }
function over(e, now) {
  var s = span(e);
  return e.ad ? dayOf(now) > ymd(s[1]) : s[1] <= now;
}
/* 'today' (not over, and begun by the end of today's night: a run in progress is today's),
   'near' (days 1-14 after today), 'ahead' (day 15 to about seven months), else null (over or beyond) */
function band(e, now) {
  if (over(e, now)) return null;
  var g = dayGap(firstDay(e), dayOf(now));
  return g <= 0 ? 'today' : g <= 14 ? 'near' : g <= AHEAD_DAYS ? 'ahead' : null;
}
W.MDWHEN = {
  bkk: bkk, hhmm: hhmm, ymd: ymd, at: at, atEnd: atEnd, span: span, ics: ics,
  MON_TH: MON_TH, MON_EN: MON_EN, DAY_TH: DAY_TH, DAY_EN: DAY_EN, be: be,
  DAY_END_H: DAY_END_H, AHEAD_DAYS: AHEAD_DAYS, dayOf: dayOf, firstDay: firstDay, over: over, band: band
};
})(window);
