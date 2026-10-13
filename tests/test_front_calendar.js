// The front page's calendar reads every event in docs/front/events.json with the
// page's own date code (front.js at, atEnd, span, ics). On 2026-10-10 one event
// whose end was a bare date threw inside ics(), and the calendar's day drawings
// and day list never rendered on the live page; nothing had checked. This runs
// those functions, taken from assets/front/when.js (where they moved on 2026-10-11) as the
// page runs them, over every event.
//
//   node tests/test_front_calendar.js [events.json]
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const WHEN = process.env.MD_WHEN_JS || path.join(ROOT, 'assets/front/when.js');
if (!fs.existsSync(WHEN)) throw new Error('no ' + path.relative(ROOT, WHEN) + ': the page\'s date code is gone');
const SRC = fs.readFileSync(WHEN, 'utf8');
const EV = process.argv[2] || path.join(ROOT, 'docs/front/events.json');

// a top-level `function name(...) {...}` from when.js, braces counted outside strings
function take(name) {
  const i = SRC.indexOf('\nfunction ' + name + '(');
  if (i < 0) throw new Error('when.js has no function ' + name);
  let j = SRC.indexOf('{', i), depth = 0, q = null;
  for (let k = j; k < SRC.length; k++) {
    const ch = SRC[k];
    if (q) { if (ch === '\\') k++; else if (ch === q) q = null; continue; }
    if (ch === "'" || ch === '"') { q = ch; continue; }
    if (ch === '{') depth++;
    else if (ch === '}' && --depth === 0) return SRC.slice(i + 1, k + 1);
  }
  throw new Error('unbalanced function ' + name);
}
const lib = ['bkk', 'ymd', 'at', 'span', 'ics', 'atEnd'].map(take).join('\n');
const F = new Function(lib + '\nreturn { ymd, at, span, ics };')();

if (!fs.existsSync(EV)) { console.log('front calendar: no ' + path.relative(ROOT, EV) + ', nothing to check'); process.exit(0); }
const data = JSON.parse(fs.readFileSync(EV, 'utf8')), bad = [];
const DT = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/, D = /^\d{4}-\d{2}-\d{2}$/;
for (const e of data.events || []) {
  const who = (e.k || '?') + ' (' + e.s + ' → ' + e.e + ')';
  try {
    if (!DT.test(e.s || '')) { bad.push(who + ': start is not YYYY-MM-DD HH:MM:SS'); continue; }
    if (e.e && !DT.test(e.e) && !D.test(e.e)) { bad.push(who + ': end is neither a date nor a date and time'); continue; }
    const s = F.span(e);
    if (!isFinite(s[0]) || !isFinite(s[1])) { bad.push(who + ': span() is not a number'); continue; }
    if (!e.ad && !/DTSTART:\d{8}T\d{6}Z/.test(decodeURIComponent(F.ics(e)))) bad.push(who + ': ics() wrote no start');
    if (F.ymd(s[0]).length !== 10) bad.push(who + ': ymd() of its start');
    if (e.city && ['cm', 'cr', 'pth', 'pp'].indexOf(e.city) < 0) bad.push(who + ': city ' + e.city);   // the cities front.js cityAt() knows (Nan 2026-10-13: allow city keys)
  } catch (err) { bad.push(who + ': ' + err.message); }
}
if (bad.length) {
  console.log('front calendar: ' + bad.length + ' of ' + data.events.length + ' events break the page\'s date code');
  bad.slice(0, 20).forEach(b => console.log('  ' + b));
  process.exit(1);
}
console.log('front calendar: ' + data.events.length + ' events read by the page\'s own date code');
