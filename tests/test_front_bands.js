// The front calendar's three bands (calendar design, 2026-10-11) cut from the baked events with the page's own
// code: MDWHEN.band from when.js says which band an event is in, and bandToday, bandNear, bandAhead from
// front.js put what it keeps in order. Checked at several moments of the day, in the order the reader sees:
//   TODAY: sorted by start, nothing over, no all-day event of tomorrow, runs that began earlier on their own list
//   NEXT 14 DAYS: fourteen days in date order, each event on its own day, each day in start order
//   PLAN AHEAD: by start, from day 15 on; every event inside seven months is in a band or over
//
//   node tests/test_front_bands.js [events.json or when.json]
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const FRONT = fs.readFileSync(process.env.MD_FRONT_JS || path.join(ROOT, 'assets/front/front.js'), 'utf8');
const WHEN = fs.readFileSync(process.env.MD_WHEN_JS || path.join(ROOT, 'assets/front/when.js'), 'utf8');
const SRC = process.argv[2] || path.join(ROOT, 'docs/front/events.json');

function take(name) {
  const i = FRONT.indexOf('\nfunction ' + name + '(');
  if (i < 0) throw new Error('front.js has no function ' + name);
  let j = FRONT.indexOf('{', i), depth = 0, q = null;
  for (let k = j; k < FRONT.length; k++) {
    const ch = FRONT[k];
    if (q) { if (ch === '\\') k++; else if (ch === q) q = null; continue; }
    if (ch === "'" || ch === '"') { q = ch; continue; }
    if (ch === '{') depth++;
    else if (ch === '}' && --depth === 0) return FRONT.slice(i + 1, k + 1);
  }
  throw new Error('unbalanced function ' + name);
}
const win = {}; new Function('window', WHEN)(win);
const MW = win.MDWHEN, at = MW.at, ymd = MW.ymd, bkk = MW.bkk;
const F = new Function('MW', 'at', 'ymd', 'bkk', ['nxByStart', 'bandToday', 'bandNear', 'bandAhead', 'nxPick', 'nxWeek'].map(take).join('\n') +
  '\nreturn { bandToday, bandNear, bandAhead, nxPick, nxWeek, nxByStart };')(MW, at, ymd, bkk);

if (!fs.existsSync(SRC)) { console.log('front bands: no ' + path.relative(ROOT, SRC) + ', nothing to check'); process.exit(0); }
const data = JSON.parse(fs.readFileSync(SRC, 'utf8'));
const evs = (data.events || data.items.filter(x => x.kind === 'ev')).filter(e => e.s);
const bad = [];
const say = (m, w) => { if (bad.length < 40) bad.push(m + ' @ ' + w); };

// the baked day, then a spread of moments around it: small hours, morning, noon, night, 02:59 and 03:01
const day0 = (data.today || ymd(Date.now()));
const moments = ['00:30', '02:59', '03:01', '09:38', '12:00', '15:30', '19:45', '23:50'];
let nToday = 0, nNear = 0, nAhead = 0;
for (let off = 0; off < 3; off++) for (const hm of moments) {
  const d = ymd(at(day0 + ' 12:00:00') + off * 864e5), now = at(d + ' ' + hm + ':00'), w = d + ' ' + hm;
  const td = MW.dayOf(now), T = F.bandToday(evs, now), N = F.bandNear(evs, now), A = F.bandAhead(evs, now);
  nToday += T.rows.length; nNear += N.days.reduce((n, x) => n + N.by[x].length, 0); nAhead += A.length;
  // TODAY
  T.rows.forEach((e, i) => {
    if (MW.over(e, now)) say('TODAY holds an event already over: ' + e.k + ' ' + e.s + ' → ' + e.e, w);
    if (e.ad && e.s.slice(0, 10) > td) say('TODAY holds tomorrow\'s all-day event ' + e.k + ' ' + e.s, w);
    if (MW.band(e, now) !== 'today') say('TODAY holds ' + e.k + ' of band ' + MW.band(e, now), w);
    if (i && at(T.rows[i - 1].s) > at(e.s)) say('TODAY is not in start order at ' + e.k, w);
    if (MW.firstDay(e) < td) say('TODAY rows hold a run begun before today: ' + e.k, w);
  });
  T.run.forEach(e => {
    if (MW.over(e, now) || MW.firstDay(e) >= td) say('TODAY runs holds ' + e.k + ' ' + e.s + ' → ' + e.e, w);
  });
  // NEXT 14 DAYS
  if (N.days.length !== 14) say('NEXT has ' + N.days.length + ' days', w);
  N.days.forEach((x, i) => {
    if (i && !(N.days[i - 1] < x)) say('NEXT days are not in date order at ' + x, w);
    if (x <= td) say('NEXT holds ' + x + ', not after today ' + td, w);
    N.by[x].forEach((e, j) => {
      if (MW.firstDay(e) !== x) say('NEXT day ' + x + ' holds ' + e.k + ' of ' + MW.firstDay(e), w);
      if (MW.band(e, now) !== 'near') say('NEXT holds ' + e.k + ' of band ' + MW.band(e, now), w);
      if (j && at(N.by[x][j - 1].s) > at(e.s)) say('NEXT ' + x + ' is not in start order at ' + e.k, w);
    });
  });
  // PLAN AHEAD
  A.forEach((e, i) => {
    if (MW.band(e, now) !== 'ahead') say('AHEAD holds ' + e.k + ' of band ' + MW.band(e, now), w);
    if (i && at(A[i - 1].s) > at(e.s)) say('AHEAD is not in start order at ' + e.k, w);
  });
  // every event is in one band, or over, or beyond seven months
  const placed = new Set([].concat(T.run, T.rows, A));
  N.days.forEach(x => N.by[x].forEach(e => placed.add(e)));
  evs.forEach(e => {
    const b = MW.band(e, now);
    if (b && !placed.has(e)) say('event in band ' + b + ' is on no list: ' + e.k + ' ' + e.s, w);
    if (!b && placed.has(e)) say('event in no band is on a list: ' + e.k + ' ' + e.s, w);
  });
}
// a fit pick keeps time order and loses nothing
{
  const now = at(day0 + ' 09:38:00'), T = F.bandToday(evs, now);
  T.rows.forEach((e, i) => { e.sc = (i * 7919) % 13; });
  const P = F.nxPick(T.rows, 5);
  if (P.top.length + P.rest.length !== T.rows.length) bad.push('the pick loses rows');
  P.top.forEach((e, i) => { if (i && at(P.top[i - 1].s) > at(e.s)) bad.push('the five picked are not in start order'); });
  P.rest.forEach((e, i) => { if (i && at(P.rest[i - 1].s) > at(e.s)) bad.push('the rest are not in start order'); });
  if (F.nxWeek('2026-10-26') !== '2026-10-26' || F.nxWeek('2026-11-01') !== '2026-10-26') bad.push('a week does not start on Monday');
}
if (bad.length) {
  console.log('front bands: ' + bad.length + ' wrong');
  bad.slice(0, 12).forEach(b => console.log('  ' + b));
  process.exit(1);
}
console.log('front bands: ' + evs.length + ' events, 24 moments; today ' + nToday + ', next 14 days ' + nNear + ', ahead ' + nAhead + ' rows; sorted, none over, one list each');
