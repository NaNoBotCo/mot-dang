#!/usr/bin/env node
/* A soi or street name, typed in Thai or romanised, now finds the way.
 *
 * edge_layer.search_rows() projects data/streets.json into search-index rows
 * in build.py's compact shape. This test runs the SHIPPED engine
 * (publish/searchcore.js) over those rows exactly as emit_edge_index.js and
 * the page do — same fields, same weights — and proves three things:
 *
 *   1. a way's Thai name finds its row, top of the list, and the row carries
 *      the id, the kind, and an actionable target (a map href + a coordinate);
 *   2. the romanised name finds it too;
 *   3. a bare shelf word ("coffee") does NOT surface a way above a real place —
 *      a way stands on no shelf, so it never crowds a shelf query.
 *
 *     node tests/test_edge_soi.mjs
 *
 * The rows come from the real edge_layer, read through python, so this covers
 * the projection and the engine together — one source of truth, no JS twin of
 * the python.
 */
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import SEARCHCORE from "../publish/searchcore.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const D = join(ROOT, "docs", "data");
const PROVWORDS = { cm: "เชียงใหม่ chiang mai chiangmai", cr: "เชียงราย chiang rai chiangrai" };

/* THE TWIN OF emit_edge_index.js addRow and the page's index.add: name from
 * nm|n, em|e, a, r at 1.0; shelf from cat + sub + province + k at 0.45. */
function addRow(index, e) {
  const f = { name: [[e.nm || e.n, e.em || e.e, e.a, e.r].filter(Boolean).join(" "), 1.0] };
  f.shelf = [e.hd ? (PROVWORDS[e.p] || "")
    : ((e.c || []).join(" ") + " " + (e.su || []).map(s => s.replace(/-/g, " ")).join(" ")
       + " " + (PROVWORDS[e.p] || "") + " " + (e.k || "")), 0.45];
  index.add(e, f);
}

let failures = 0;
const ok = (c, m) => { if (c) { console.log("  ok   " + m); } else { failures++; console.log("  FAIL " + m); } };

/* Run edge_layer against a given data ROOT and return JSON. sys.path points at
 * the repo so `import edge_layer` resolves; R is the data root, which lets the
 * junction case below run against a synthetic streets.json. */
const PYHEAD = (root) => `import json,sys;sys.path.insert(0,${JSON.stringify(ROOT)});`
  + `from pathlib import Path;import edge_layer as E;R=Path(${JSON.stringify(root)})`;
const py = (expr, root) => JSON.parse(execFileSync("python3",
  ["-c", `${PYHEAD(root)};print(json.dumps(${expr}))`],
  { cwd: ROOT, maxBuffer: 64 * 1024 * 1024 }).toString());
/* A multi-statement program (ends by printing JSON) — for counts that want a
 * single ways() pass instead of one per number. */
const pyRun = (prog, root) => JSON.parse(execFileSync("python3",
  ["-c", `${PYHEAD(root)}\n${prog}`],
  { cwd: ROOT, maxBuffer: 64 * 1024 * 1024 }).toString());

/* The rows straight from the real projection. */
const rows = py("E.search_rows(R)", ".");
ok(rows.length > 400, `search_rows projected ${rows.length} ways`);

/* One real place, so query 3 has something legitimate to rank ABOVE a way. */
const decoy = { id: "cm-test-cafe-1", s: "test-cafe-1", n: "ร้านกาแฟทดสอบ",
                e: "Test Coffee House", p: "cm", c: ["food"], su: ["coffee"] };

const core = new SEARCHCORE.SearchCore(
  JSON.parse(readFileSync(join(D, "search_thesaurus.json"), "utf8")).groups,
  readFileSync(join(D, "search_segdict.txt"), "utf8").split("\n").filter(l => l && l[0] !== "#"));
const index = new SEARCHCORE.Index(core);
for (const e of rows) addRow(index, e);
addRow(index, decoy);
index.finalize();

const run = (q) => {
  const an = core.analyze(q, index);
  return index.search(an, 0).map(r => ({ id: r.doc.id, doc: r.doc, tier: r.tier }));
};

/* A soi with a Thai name and a romanisation, chosen from the data itself so
 * this does not rot when streets.json changes. */
const soi = rows.find(r => r.r && /ซอย/.test(r.n) && r.u && r.lat != null);
ok(!!soi, `picked a soi to probe: ${soi ? soi.n + " / " + soi.r : "NONE FOUND"}`);

if (soi) {
  /* 1 — the Thai name finds it, and the row is actionable. */
  const th = run(soi.n);
  const hitTh = th.find(r => r.id === soi.id);
  ok(!!hitTh, `Thai name "${soi.n}" returns the way (${th.length} hits)`);
  ok(th[0] && th[0].id === soi.id, `the way is the top hit for its own Thai name`);
  if (hitTh) {
    const d = hitTh.doc;
    ok(d.id.includes("-way-"), `the hit carries a way id: ${d.id}`);
    ok(Array.isArray(d.kd) && d.kd.includes("way"), `the hit carries kind ["way"]`);
    ok(typeof d.u === "string" && d.u.startsWith("map.html#"), `actionable target u=${d.u}`);
    ok(typeof d.lat === "number" && typeof d.lng === "number",
       `the hit carries a map coordinate ${d.lat},${d.lng}`);
  }

  /* 2 — the romanised name finds it. */
  const rm = run(soi.r);
  ok(rm.some(r => r.id === soi.id), `romanised name "${soi.r}" returns the way (${rm.length} hits)`);
}

/* 3 — a shelf word surfaces the real place, and no way above it. */
for (const q of ["coffee", "กาแฟ"]) {
  const res = run(q);
  const firstWay = res.findIndex(r => r.id.includes("-way-"));
  const decoyAt = res.findIndex(r => r.id === decoy.id);
  ok(decoyAt !== -1, `"${q}" returns the real cafe`);
  ok(firstWay === -1 || (decoyAt !== -1 && decoyAt < firstWay),
     `"${q}" does not rank a way above the real place (cafe@${decoyAt}, way@${firstWay})`);
}

/* 4 — coverage: exact, approximate junction, and in-fence place centroid
 * (Nan approved junction + option-B in-fence centroid, both 2026-09-25). */
const cover = pyRun([
  "w=E.ways(R); rows=E.search_rows(R)",
  "mp=lambda x: x['attrs'].get('mapPoint')",
  "note=lambda x: ((x['provenance'].get('attrs.mapPoint') or {}).get('note') or '')",
  "print(json.dumps({",
  " 'exact':sum(1 for x in w if mp(x) and not mp(x)['approx']),",
  " 'junction':sum(1 for x in w if 'junction of' in note(x)),",
  " 'centroid':sum(1 for x in w if 'place centroid' in note(x)),",
  " 'none':sum(1 for x in w if not mp(x)),",
  " 'rows':len(rows),'total':len(w),",
  " 'outfence':sum(1 for r in rows if not E._in_fence(r['lat'],r['lng']))}))",
].join("\n"), ".");
console.log(`  ..   coverage: ${cover.rows}/${cover.total} rows`
  + ` (exact ${cover.exact}, junction ${cover.junction}, centroid ${cover.centroid},`
  + ` no point ${cover.none})`);
ok(cover.rows === cover.exact + cover.junction + cover.centroid,
   `every located way becomes a search row`);
ok(cover.outfence === 0, `no way pin lands outside the basemap fence`);

/* 5 — the junction pin, proven on a fixture. No real way needs it today (the
 * still-uncovered ways are all offmap with empty crosses), so the mechanism is
 * shown on a synthetic street doc: a geom-less soi that crosses a mapped road. */
const fix = mkdtempSync(join(tmpdir(), "edge-soi-"));
mkdirSync(join(fix, "data"));
writeFileSync(join(fix, "data", "streets.json"), JSON.stringify({ streets: [
  { slug: "fix-road-a", name: "ถนนทดสอบ", nameEn: "Fixture Road", province: "cm",
    length: 300, places: [], crosses: [], geom: [[[18.80, 98.97], [18.802, 98.972]]] },
  { slug: "fix-soi-99", name: "ซอยทดสอบเก้าสิบเก้า", nameEn: "Fixture Soi 99", soi: "99",
    province: "cm", length: 0, places: [{ id: "x" }], geom: [], crosses: ["fix-road-a"] },
] }));
try {
  const frows = py("E.search_rows(R)", fix);
  const fways = py("E.ways(R)", fix);
  const fsoi = frows.find(r => /ซอย/.test(r.n));
  const froad = frows.find(r => r.n.startsWith("ถนน"));
  ok(!!fsoi, `a geom-less soi crossing a mapped road becomes a search row`);
  ok(!!fsoi && !!froad && fsoi.lat === froad.lat && fsoi.lng === froad.lng,
     `its junction pin sits on the crossed road (${fsoi ? fsoi.lat + "," + fsoi.lng : "-"})`);
  ok(!!fsoi && typeof fsoi.u === "string" && fsoi.u.startsWith("map.html#"),
     `the junction row carries the same map href format: ${fsoi ? fsoi.u : "-"}`);
  const rec = fways.find(x => /ซอย/.test(x.name));
  ok(!!rec && !!rec.attrs.mapPoint && rec.attrs.mapPoint.approx === true,
     `the record marks the pin approx=true`);
  const note = rec && (rec.provenance["attrs.mapPoint"] || {}).note;
  ok(typeof note === "string" && note.startsWith("junction of"),
     `provenance names the junction: "${note}"`);
  const fi = new SEARCHCORE.Index(core);
  for (const e of frows) addRow(fi, e);
  fi.finalize();
  const fres = fi.search(core.analyze(fsoi.n, fi), 0).map(r => r.doc.id);
  ok(fres.includes(fsoi.id), `the junction-pinned soi is findable by its Thai name`);
} finally {
  rmSync(fix, { recursive: true, force: true });
}

/* 6 — the in-fence place centroid, and the out-of-fence skip. Two offmap ways
 * with no geometry and no crossing: one whose places sit inside the cm-cr fence
 * (pinned) and one whose lone place is in Bangkok (skipped, no row). */
const cfx = mkdtempSync(join(tmpdir(), "edge-cen-"));
mkdirSync(join(cfx, "data"));
mkdirSync(join(cfx, "data", "canonical"));
writeFileSync(join(cfx, "data", "streets.json"), JSON.stringify({ streets: [
  { slug: "cen-in", name: "ซอยในรั้ว", nameEn: "In-Fence Soi", soi: "1", province: "cm",
    length: 0, offmap: true, geom: [], crosses: [], places: [{ id: "p-in-1" }, { id: "p-in-2" }] },
  { slug: "cen-out", name: "ซอยนอกรั้ว", nameEn: "Out-Fence Soi", soi: "2", province: "cm",
    length: 0, offmap: true, geom: [], crosses: [], places: [{ id: "p-out-1" }] },
] }));
writeFileSync(join(cfx, "data", "canonical", "cm.json"), JSON.stringify([
  { id: "p-in-1", lat: 18.79, lng: 98.98, province: "cm" },
  { id: "p-in-2", lat: 18.80, lng: 98.99, province: "cm" },
  { id: "p-out-1", lat: 13.75, lng: 100.50, province: "cm" },   // Bangkok — outside the fence
]));
writeFileSync(join(cfx, "data", "canonical", "cr.json"), JSON.stringify([]));
try {
  const crows = py("E.search_rows(R)", cfx);
  const cways = py("E.ways(R)", cfx);
  const inRow = crows.find(r => r.s === "cen-in");
  const outRow = crows.find(r => r.s === "cen-out");
  ok(!!inRow, `an offmap way with an in-fence place-centroid becomes a search row`);
  ok(!!inRow && typeof inRow.u === "string" && inRow.u.startsWith("map.html#"),
     `the centroid row carries the map href: ${inRow ? inRow.u : "-"}`);
  ok(!outRow, `an offmap way whose centroid falls outside the fence gets NO row`);
  const inRec = cways.find(x => x.attrs.mapPoint && x.name === "ซอยในรั้ว");
  ok(!!inRec && inRec.attrs.mapPoint.approx === true, `the kept record marks approx=true`);
  const cnote = inRec && (inRec.provenance["attrs.mapPoint"] || {}).note;
  ok(typeof cnote === "string" && cnote.startsWith("place centroid"),
     `provenance names it a place centroid: "${cnote}"`);
  const outRec = cways.find(x => x.name === "ซอยนอกรั้ว");
  ok(!!outRec && !outRec.attrs.mapPoint,
     `the out-of-fence way carries no mapPoint (record stays unplaced)`);
} finally {
  rmSync(cfx, { recursive: true, force: true });
}

console.log(failures ? `\n${failures} FAILED` : `\nall green`);
process.exit(failures ? 1 : 0);
