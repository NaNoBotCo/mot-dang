// The front page's time model (assets/front/when.js): the day that ends at 03:00 and the band an
// event belongs to. Until 2026-10-11 each part of the page kept its own idea of "today": the list
// dropped an all-day event two hours after it started, the fortnight kept it to midnight, and the
// 59 all-day events stored at 00:00 showed on the night before. This runs when.js over a baked
// when.json (front_layer.bake_when) and over the edges by hand.
//
//   node tests/test_when.js [when.json]        (default docs/front/when.json; events.json beside it)
//   MD_WHEN_JS=<a copy of when.js> node tests/test_when.js   to try a changed copy
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const WHEN = process.env.MD_WHEN_JS || path.join(ROOT, 'assets/front/when.js');
const win = {};
new Function('window', fs.readFileSync(WHEN, 'utf8'))(win);
const M = win.MDWHEN;
const bad = [];
const eq = (what, got, want) => { if (got !== want) bad.push(what + ': ' + got + ', wanted ' + want); };
const T = s => Date.parse(s + '+07:00');

// --- the edges, by hand. Now is Sunday 11 Oct 2026, 09:38 in Bangkok.
const now = T('2026-10-11T09:38:00');
const ev = (s, e, ad) => ({ k: 'x', t: 'x', s, e: e || null, ad: !!ad });
eq('all-day tomorrow, stored 00:00', M.band(ev('2026-10-12 00:00:00', null, true), now), 'near');
eq('all-day today', M.band(ev('2026-10-11 00:00:00', null, true), now), 'today');
eq('all-day yesterday', M.band(ev('2026-10-10 00:00:00', null, true), now), null);
eq('all-day today, seen at 01:30 the next night', M.band(ev('2026-10-11 00:00:00', null, true), T('2026-10-12T01:30:00')), 'today');
eq('all-day today, seen at 02:59:59 the next night', M.band(ev('2026-10-11 00:00:00', null, true), T('2026-10-12T02:59:59')), 'today');
eq('all-day today, seen at 03:00:00 the next night', M.band(ev('2026-10-11 00:00:00', null, true), T('2026-10-12T03:00:00')), null);
eq('01:30 tonight', M.band(ev('2026-10-12 01:30:00', '2026-10-12 03:30:00'), now), 'today');
eq('02:59:59 tonight', M.band(ev('2026-10-12 02:59:59', '2026-10-12 04:00:00'), now), 'today');
eq('03:00:00 tomorrow', M.band(ev('2026-10-12 03:00:00', '2026-10-12 05:00:00'), now), 'near');
eq('dayOf 02:59:59', M.dayOf(T('2026-10-12T02:59:59')), '2026-10-11');
eq('dayOf 03:00:00', M.dayOf(T('2026-10-12T03:00:00')), '2026-10-12');
eq('dayOf 00:00', M.dayOf(T('2026-10-12T00:00:00')), '2026-10-11');
eq('timed, over', M.band(ev('2026-10-11 07:00:00', '2026-10-11 08:00:00'), now), null);
eq('timed, begun and not over', M.band(ev('2026-10-11 09:00:00', '2026-10-11 12:00:00'), now), 'today');
eq('timed, later today', M.band(ev('2026-10-11 19:30:00', null), now), 'today');
eq('no end: two hours', M.band(ev('2026-10-11 07:30:00', null), now), null);
eq('a run in progress (bare-date end)', M.band(ev('2026-10-09 00:00:00', '2026-10-13', true), now), 'today');
eq('a run that ended yesterday', M.band(ev('2026-10-08 00:00:00', '2026-10-10', true), now), null);
eq('day 14', M.band(ev('2026-10-25 19:00:00', null), now), 'near');
eq('day 15', M.band(ev('2026-10-26 19:00:00', null), now), 'ahead');
eq('day 15, all-day', M.band(ev('2026-10-26 00:00:00', null, true), now), 'ahead');
eq('day 214', M.band(ev('2027-05-13 19:00:00', null), now), 'ahead');
eq('day 215', M.band(ev('2027-05-14 19:00:00', null), now), null);
eq('be(2026)', M.be(2026), 2569);

// --- the baked file
const wf = path.resolve(process.argv[2] || path.join(ROOT, 'docs/front/when.json'));
if (!fs.existsSync(wf)) {
  if (process.argv[2]) { console.log('when: no ' + wf); process.exit(1); }
  if (bad.length) { console.log('when: ' + bad.length + ' edges wrong'); bad.forEach(b => console.log('  ' + b)); process.exit(1); }
  console.log('when: no ' + path.relative(ROOT, wf) + ', the edges only'); process.exit(0);
}
const W = JSON.parse(fs.readFileSync(wf, 'utf8'));
const items = W.items || [];
const evs = items.filter(i => i.kind === 'ev');
eq('built is an ISO time', /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$/.test(W.built || ''), true);
eq('today is the Bangkok date of built', W.today, M.ymd(Date.parse(W.built)));
for (const i of items) {
  if (['ev', 'fest', 'sky'].indexOf(i.kind) < 0) bad.push('kind ' + i.kind);
  if (i.kind === 'fest' && !(/^\d{4}-\d{2}-\d{2}$/.test(i.d0) && /^\d{4}-\d{2}-\d{2}$/.test(i.d1) && i.d0 <= i.d1 && i.id)) bad.push('festival ' + i.id + ': ' + i.d0 + ' to ' + i.d1);
  if (i.kind === 'sky' && !/^\d{4}-\d{2}-\d{2}$/.test(i.d)) bad.push('sky row ' + i.d);
}
const evf = path.join(path.dirname(wf), 'events.json');
if (fs.existsSync(evf)) {
  const E = JSON.parse(fs.readFileSync(evf, 'utf8')).events;
  eq('events in when.json and events.json', evs.length, E.length);
  const diff = E.filter((e, n) => !evs[n] || evs[n].k !== e.k || JSON.stringify(Object.assign({}, evs[n], { kind: undefined })) !== JSON.stringify(Object.assign({}, e, { kind: undefined })));
  eq('events whose id or fields differ from events.json', diff.length, 0);
} else bad.push('no events.json beside when.json to hold the ids to');

// every event is in exactly one band, or is over, at the moments a reader could look
const base = T(W.today + 'T00:00:00'), DAY = 864e5;
const looks = [];
for (let d = 0; d <= 3; d++) for (const h of ['00:30:00', '02:59:59', '03:00:00', '09:38:00', '23:59:59']) looks.push(base + d * DAY + (Date.parse('1970-01-01T' + h + 'Z')));
function digest() {
  const out = [];
  for (const t of looks) {
    const c = { today: 0, near: 0, ahead: 0, over: 0, none: 0 };
    for (const e of evs) {
      const b = M.band(e, t), o = M.over(e, t);
      if (o) { c.over++; if (b !== null) bad.push(e.k + ' is over and still in ' + b); continue; }
      if (b === null) { c.none++; bad.push(e.k + ' (' + e.s + ' → ' + e.e + ') is in no band at ' + M.hhmm(t) + ' ' + M.ymd(t)); continue; }
      c[b]++;
      // an all-day event is its own date's, never the night before's
      if (e.ad && b === 'today' && !(e.s.slice(0, 10) <= M.dayOf(t))) bad.push(e.k + ' all-day ' + e.s + ' is in today at ' + M.hhmm(t) + ' ' + M.ymd(t));
      if (!e.ad && b === 'today' && M.dayOf(M.at(e.s)) > M.dayOf(t)) bad.push(e.k + ' ' + e.s + ' is in today before its day');
    }
    eq('bands and over add up at ' + t, c.today + c.near + c.ahead + c.over + c.none, evs.length);
    out.push([t, c.today, c.near, c.ahead, c.over, evs.map(e => M.band(e, t) || '-').join('')].join(','));
  }
  return out.join('\n') + '\n' + evs.map(e => M.dayOf(M.at(e.s)) + M.hhmm(M.at(e.s))).join(',');
}
// the phone's time zone must change nothing
const tz0 = process.env.TZ;
process.env.TZ = 'America/Los_Angeles'; const off = new Date(base).getTimezoneOffset(); const la = digest();
process.env.TZ = 'Asia/Bangkok'; const off2 = new Date(base).getTimezoneOffset(); const bk = digest();
if (tz0 === undefined) delete process.env.TZ; else process.env.TZ = tz0;
if (off === off2) bad.push('this node did not change its time zone, so the zone check proves nothing');
eq('Los Angeles and Bangkok give the same bands', la === bk, true);

if (bad.length) {
  console.log('when: ' + bad.length + ' wrong');
  bad.slice(0, 20).forEach(b => console.log('  ' + b));
  process.exit(1);
}
const first = bk.split('\n')[3].split(',');
console.log('when: ' + evs.length + ' events, ' + items.length + ' items, one band each (or over) at ' + looks.length + ' moments; today ' + first[1] + ', near ' + first[2] + ', ahead ' + first[3] + ', over ' + first[4] + ' at 09:38; same in Los Angeles and Bangkok');
