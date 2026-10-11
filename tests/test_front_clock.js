// The doodle clock on the front page reads like a wall clock: at 09:38 Bangkok time
// the hour hand points between 9 and 10 and the minute hand near 38. Until
// 2026-10-11 the face was a 24-hour dial with midnight at the foot, and at 09:38 its
// hour hand sat where a wall clock says 11; nothing checked. This takes hourOf and
// dialA from front.js as the page runs them.
//
//   node tests/test_front_clock.js
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const SRC = fs.readFileSync(process.env.MD_FRONT_JS || path.join(ROOT, 'assets/front/front.js'), 'utf8');

function take(name) {
  const i = SRC.indexOf('\nfunction ' + name + '(');
  if (i < 0) throw new Error('front.js has no function ' + name);
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
const F = new Function(['bkk', 'hourOf', 'dialA'].map(take).join('\n') + '\nreturn { hourOf, dialA };')();

// a wall clock's hour hand, in canvas radians (0 = 3 o'clock, clockwise), for h hours
const wall = h => -Math.PI / 2 + (h % 12) / 12 * 2 * Math.PI;
const norm = a => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
const bad = [];
for (let m = 0; m < 24 * 60; m += 7) {
  const t = Date.parse('2026-10-11T00:00:00+07:00') + m * 6e4;
  const hh = String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
  const h = F.hourOf(t);
  if (Math.abs(h - m / 60) > 1e-6) { bad.push(hh + ' Bangkok: hourOf gives ' + h.toFixed(3)); continue; }
  const d = Math.abs(norm(F.dialA(h)) - norm(wall(m / 60)));
  if (Math.min(d, 2 * Math.PI - d) > 0.01) bad.push(hh + ' Bangkok: the hour hand points where a wall clock reads ' + (((norm(F.dialA(h)) + Math.PI / 2) / (2 * Math.PI) * 12) % 12).toFixed(1));
}
if (bad.length) {
  console.log('front clock: ' + bad.length + ' times read wrong');
  bad.slice(0, 8).forEach(b => console.log('  ' + b));
  process.exit(1);
}
console.log('front clock: the hour hand reads right at every 7th minute of the day');
