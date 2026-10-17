#!/usr/bin/env node
/* The band's doodle for given days, fixed ahead (front_layer.bake): the auto-doodler's own
   choose() over each day's events, minus every doodle already aired at its current version
   (Nan, 2026-10-02: reused "only after significant editing to make it more baller than last
   time"). Days later in the run count the earlier ones as aired.

     node tools/doodler_pick.mjs <events.json> <aired.json> <day> [day …]  → JSON rows
   aired.json: {"aired": [{date, set, variant, version, k}]} */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FRONT = path.join(ROOT, 'assets/front');
const noop = () => {};
const ctx = { window: { MDSKY: { paper: noop, jag: noop, circ: noop, grain: noop, sights: { cm: [], cr: [] }, landscape: () => [] } }, console, Date, Math };
ctx.window.window = ctx.window;
vm.createContext(ctx);
const files = ['doodler.js', ...fs.readdirSync(FRONT).filter(f => /^doodler-.*\.js$/.test(f)).sort()];
for (const f of files) vm.runInContext(fs.readFileSync(path.join(FRONT, f), 'utf8'), ctx, { filename: f });
const D = ctx.window.MDDOODLER;
/* each file's scenes must be on doodler.js's FILES list, or the page never loads them */
for (const f of files.slice(1)) for (const m of fs.readFileSync(path.join(FRONT, f), 'utf8').matchAll(/addScene\('([a-z-]+)'/g))
  if (D.files[m[1]] !== f) process.stderr.write(`doodler: '${m[1]}' (${f}) is missing from FILES in doodler.js\n`);

const OPTS = 3;
const [evf, airf, ...days] = process.argv.slice(2);
const E = JSON.parse(fs.readFileSync(evf, 'utf8')).events;
const led = fs.existsSync(airf) ? JSON.parse(fs.readFileSync(airf, 'utf8')).aired || [] : [];
const at = s => Date.parse(s.replace(' ', 'T') + '+07:00');
const ymd = t => new Date(t + 7 * 3600e3).toISOString().slice(0, 10);
function span(e) { const s = at(e.s), en = e.e ? (e.e.length > 10 ? at(e.e) : at(e.e + ' 23:59:59')) : (e.ad ? s + 864e5 - 1 : s + 2 * 3600e3); return [s, Math.max(s, en)]; }
/* the day's events: timed, starting that day, shorter than 30 hours */
const of = day => E.filter(e => { const s = span(e); return ymd(s[0]) === day && s[1] - s[0] < 30 * 3600e3; });

const aired = {};
function mark(r) { const key = r.variant ? r.set + ':' + r.variant : r.set; aired[key] = Math.max(aired[key] || 0, r.version || 1); }
led.forEach(r => { if (!days.length || r.date < days[0]) mark(r); });
const out = [];
const byK = {}; for (const e of E) byK[e.k] = byK[e.k] || e;
let last = led.filter(r => days.length && r.date === ymd(at(days[0] + ' 12:00:00') - 864e5))[0] || null;
for (const day of days) {
  const prev = last && last.set ? last : of(ymd(at(day + ' 12:00:00') - 864e5));
  /* the day's choices, up to OPTS, each a different scene; the reader's browser picks among them */
  const opts = [], skip = {};
  for (let i = 0; i < OPTS; i++) {
    const x = D.choose(of(day), day, prev, aired, skip);
    if (!x) break;
    const o = { k: x.e.k, set: x.set, variant: x.variant || '', version: x.version, en: x.e.t };
    opts.push(o); mark(o); skip[x.set] = 1;
  }
  /* a reader in either city has a choice drawn for it: the browser drops options 40 km off or more, and its
     own fallback guesses with only the scene files it has loaded (2026-10-12: three Chiang Rai options left
     Chiang Mai readers a Clock Tower show drawn as a classroom) */
  for (const city of ['cm', 'cr']) {
    if (!opts.length || opts.some(o => (byK[o.k] || {}).city === city)) continue;
    const x = D.choose(of(day).filter(e => e.city === city), day, prev, aired, skip);
    if (!x) continue;
    const o = { k: x.e.k, set: x.set, variant: x.variant || '', version: x.version, en: x.e.t };
    opts.push(o); mark(o); skip[x.set] = 1;
  }
  if (!opts.length) { out.push({ date: day, set: '', k: '' }); last = null; continue; }
  /* every event of the day with the scene it draws as, worked out here with every scene file loaded */
  const sets = {};
  for (const e of of(day)) { const s = D.setOf(e), v = D.variantOf(s, e); sets[e.k] = v ? s + ':' + v : s; }
  const r = Object.assign({ date: day }, opts[0], { opts, sets });
  out.push(r); last = r;
}
process.stdout.write(JSON.stringify(out));
