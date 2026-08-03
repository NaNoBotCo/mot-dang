#!/usr/bin/env node
// Does the plan map draw the walk it charges for?
//
// The distances on plan.html were right long before the picture was. The
// router stitched only the junction-to-junction chain, so the piece of road
// from a stop out to the first junction — and back in at the far end — was
// never drawn, and a straight dashed stub covered it. On the ไหว้พระ ๙ วัด
// rounds that left 34 of 80 legs drawing under 60% of their own ground, one
// leg showing 280 m of a 1,846 m walk, and four legs drawing nothing at all
// (both stops on one edge returned path:null and the fallback never fired,
// because the leg WAS routed).
//
// So this runs the shipped md.js — sliced out of docs/, not reimplemented —
// over the real graph and the real rounds, and asks of every leg: is the line
// on the map the journey in the number beside it. It also holds the moat rule:
// water on the page is named, and so is every gate standing on it.
//
//   node tests/test_plan_routes.js          (after build.py, like the others)
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
// MD_DOCS lets this run against a scratch build while somebody else holds
// docs/ — both builds wipe it, so verifying one from the other is not safe.
const DOCS = process.env.MD_DOCS || path.join(ROOT, 'docs');
const MIN_COVER = 0.6;      // of the leg's own metres, drawn as road
const FAILED = [];

function check(label, ok, detail) {
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + '  ' + label + (detail ? '  — ' + detail : ''));
  if (!ok) FAILED.push(label);
}
function need(p, what) {
  if (!fs.existsSync(p)) {
    console.error('no ' + path.relative(ROOT, p) + ' — ' + what);
    process.exit(1);
  }
  return p;
}

const src = fs.readFileSync(need(path.join(DOCS, 'md.js'), 'run build.py first'), 'utf8');
const merit = JSON.parse(fs.readFileSync(need(path.join(ROOT, 'data', 'merit.json'),
  'run importers/build_merit.py first'), 'utf8'));
const graphPath = need(path.join(ROOT, 'data', 'road_graph.json'), 'run build_road_graph.py first');
const recs = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'canonical', 'cm.json'), 'utf8'));
const byId = {};
recs.forEach(r => { byId[r.id] = r; });

// The plan JS, taken out of the file the reader is served. If a marker moves,
// this fails loudly rather than quietly testing nothing.
function slice(from, to, label) {
  const i = src.indexOf(from);
  const j = i < 0 ? -1 : src.indexOf(to, i);
  if (i < 0 || j < 0) {
    console.error('cannot find the ' + label + ' in docs/md.js — marker moved?');
    process.exit(1);
  }
  return src.slice(i, j + to.length);
}
const ROUTER = slice('function km(a,b){', 'out.routed=!!(out.foot||out.ride);\nreturn out;}', 'router');
const MAP = slice('function inRing(p){',
  "function H2(s){return String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));}",
  'map drawing');

// plan.html carries the moat ring and the gates; read them from the built page
// so the test sees exactly what a reader's browser would.
const planHtml = fs.readFileSync(need(path.join(DOCS, 'plan.html'), 'run build.py first'), 'utf8');
const geoMatch = planHtml.match(/id="plan-geo"[^>]*>([\s\S]*?)<\/script>/);
if (!geoMatch) { console.error('no #plan-geo in docs/plan.html'); process.exit(1); }
const GEO = JSON.parse(geoMatch[1]);

const harness = `
'use strict';
const fs=require('fs');
async function mdJSON(p){try{return JSON.parse(fs.readFileSync(${JSON.stringify(graphPath)},'utf8'));}catch(e){return null;}}
async function loadIndex(){return [];}
const GEO=${JSON.stringify(GEO)};
const MOAT=GEO.moat;
const POLY=(GEO.poly||[]).map(p=>({lat:p[0],lng:p[1]}));
const POLY_EDGES=POLY.map((p,i)=>[p,POLY[(i+1)%POLY.length]]);
const GATES=(GEO.gates||[]).map(g=>({lat:g[0],lng:g[1],th:g[2],en:g[3],kind:g[4]}));
let here=null, places=[];
${ROUTER}
${MAP}
module.exports={leg,svgMap,loadGraph,get GRAPH_STATE(){return GRAPH_STATE;}};
`;
const tmp = path.join(os.tmpdir(), 'md-plan-under-test.js');
fs.writeFileSync(tmp, harness);
const R = require(tmp);

function hav(a, b) {
  const Rr = 6371000, dla = (b[0] - a[0]) * Math.PI / 180, dlo = (b[1] - a[1]) * Math.PI / 180;
  const h = Math.sin(dla / 2) ** 2 + Math.cos(a[0] * Math.PI / 180) *
    Math.cos(b[0] * Math.PI / 180) * Math.sin(dlo / 2) ** 2;
  return 2 * Rr * Math.asin(Math.sqrt(h));
}
const lineLen = p => !p ? 0 : p.reduce((t, q, i, a) => i ? t + hav(a[i - 1], q) : 0, 0);

(async () => {
  await R.loadGraph();
  check('the road graph loads', R.GRAPH_STATE === 'ready', R.GRAPH_STATE);
  if (R.GRAPH_STATE !== 'ready') process.exit(1);

  let legs = 0, drawnLow = [], noPath = [], unrouted = [], distinctNames = true;
  let mapsWithMoat = 0, unnamedMoat = [], gateLabels = 0, farLegs = [];

  merit.routes.forEach(rt => {
    const stops = rt.stops.map(s => {
      const r = byId[s.id];
      return { key: s.id, n: s.name || s.nameEn || s.id, e: s.nameEn, p: s.province,
        s: s.id, pv: '', c: (r && r.cat) || ['wat'], lat: s.lat, lng: s.lng };
    });
    if (new Set(stops.map(s => s.n)).size !== stops.length) distinctNames = false;
    const ll = [];
    for (let i = 1; i < stops.length; i++) ll.push(R.leg(stops[i - 1], stops[i]));
    ll.forEach((L, i) => {
      legs++;
      const where = rt.slug + ' leg ' + (i + 1) + ' (' + stops[i].n + ' → ' + stops[i + 1].n + ')';
      if (!L.routed) { unrouted.push(where); return; }
      if (L.far >= 100) farLegs.push(where + ' ' + L.far + ' m off the network');
      ['foot', 'ride'].forEach(m => {
        const o = L[m];
        if (!o) return;
        if (!o.path || o.path.length < 2) { noPath.push(where + ' ' + m); return; }
        const cover = lineLen(o.path) / (o.km * 1000);
        // A stop the graph does not reach cannot be drawn to the end: the rest
        // is the straight walk-in, and the page says so in words rather than
        // drawing a road that is not there. Those legs are listed below.
        if (o.km * 1000 > 120 && cover < MIN_COVER && (L.far || 0) < 100)
          drawnLow.push(where + ' ' + m + ' ' + Math.round(cover * 100) + '%');
      });
    });
    const svg = R.svgMap(stops, ll);
    const moatDrawn = svg.indexOf('stroke-dasharray="5 4"') > -1;
    if (moatDrawn) {
      mapsWithMoat++;
      if (svg.indexOf('คูเมือง · the moat') < 0) unnamedMoat.push(rt.slug);
    }
    gateLabels += (svg.match(/>(?:ประตู|แจ่ง)[^<]*</g) || []).length;
    const red = (svg.match(/<path d="[^"]*" fill="none" stroke="#a3231c" stroke-width="2\.5"/g) || []).length;
    const want = ll.filter(l => l.foot && l.foot.path && l.foot.path.length > 1).length;
    if (red !== want)
      check(rt.slug + ': every walked leg is on the map', false, red + ' lines for ' + want + ' legs');
  });

  console.log('\nrouting, over ' + merit.routes.length + ' rounds of nine');
  check('every leg routes', unrouted.length === 0, unrouted.join('; ') || legs + ' legs');
  check('every routed leg draws a line', noPath.length === 0,
    noPath.length ? noPath.join('; ') : 'both modes, all ' + legs + ' legs');
  check('the line covers the walk it charges for', drawnLow.length === 0,
    drawnLow.length ? drawnLow.join('; ') : 'all legs ≥ ' + Math.round(MIN_COVER * 100) + '%');
  check('a round of nine holds nine different temples', distinctNames);

  console.log('\nthe moat and its gates');
  check('the ring reaches these maps at all', mapsWithMoat > 0, mapsWithMoat + ' of ' + merit.routes.length);
  check('water on the page is named', unnamedMoat.length === 0, unnamedMoat.join(', ') || 'every one');
  check('gates are shipped to the page', (GEO.gates || []).length >= 9,
    (GEO.gates || []).length + ' gates and แจ่ง corners in plan.html');
  check('gates standing in frame are named', gateLabels > 0, gateLabels + ' labels across the rounds');
  check('every gate carries both languages',
    (GEO.gates || []).every(g => g[2] && g[3]), (GEO.gates || []).length + ' checked');

  if (farLegs.length) {
    console.log('\nnoted, not failed — stops the graph does not really reach:');
    farLegs.forEach(f => console.log('    ' + f));
  }
  console.log(FAILED.length ? '\n' + FAILED.length + ' failed' : '\nall good');
  process.exit(FAILED.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
