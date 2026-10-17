/* The edge engine answers exactly as the page's engine does.
 *
 * publish/edgesearch.js walks the shards publish/emit_edge_index.js wrote;
 * the page builds searchcore's Index in memory. Same rows, same fields, same
 * rules — so for any query the ranked ids and the tier must be identical.
 * This runs both over the same docs/ and fails on the first disagreement.
 *
 *     node publish/emit_edge_index.js [docs]   # first
 *     MD_DOCS=... node tests/test_edge_search.js
 */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import SEARCHCORE from "../publish/searchcore.js";
import { EdgeIndex } from "../publish/edgesearch.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = process.env.MD_DOCS || join(ROOT, "docs");
const D = join(DOCS, "data");
if (!existsSync(join(DOCS, "api/v1/edge/meta.json"))) { console.log(`SKIPPED — no ${DOCS}/api/v1/edge; run publish/emit_edge_index.js`); process.exit(0); }

const rows = JSON.parse(readFileSync(join(D, "index.json"), "utf8"));
const thes = JSON.parse(readFileSync(join(D, "search_thesaurus.json"), "utf8")).groups;
const seg = readFileSync(join(D, "search_segdict.txt"), "utf8").split("\n").filter(l => l && l[0] !== "#");
const core = new SEARCHCORE.SearchCore(thes, seg);
const PROVWORDS = { cm: "เชียงใหม่ chiang mai chiangmai", cr: "เชียงราย chiang rai chiangrai" };
const mem = new SEARCHCORE.Index(core);
for (const e of rows) {
  const f = { name: [[e.nm || e.n, e.em || e.e, e.a, e.r].filter(Boolean).join(" "), 1.0] };
  f.shelf = [e.hd ? (PROVWORDS[e.p] || "") : ((e.c || []).join(" ") + " " + (e.su || []).map(s => s.replace(/-/g, " ")).join(" ") + " " + (PROVWORDS[e.p] || "") + " " + (e.k || "")), 0.45];
  mem.add(e, f);
}
mem.finalize();
const load = async (rel) => { const p = join(DOCS, rel); return existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null; };
const edge = new EdgeIndex(core, load);
await edge.init();

const Q = ["river tavern", "khao soi", "ข้าวซอย", "coffe nimman", "rajavej hospital", "guitar", "zzzzqqq", "ตอกเส้น", "kow soi",
           "wat phra singh", "วัดพระสิงห์", "ร้านกาแฟนิมมาน", "massage old city", "ราชเวส", "7 eleven", "cheap dentist", "pizza", "โรงพยาบาลราชเวช"];
const pos = new Map(rows.map((r, i) => [r.id, i]));
let failures = 0, totalMs = 0;
for (const q of Q) {
  // The whole ranking from each engine, compared id by id: same ids, same
  // score to four places, same tier. Tie ORDER is not compared — two equal
  // scores may swap between a Map walk and a sort, and neither is wrong.
  const an = core.analyze(q, mem);
  const a = new Map(mem.search(an, 0).map(r => [r.doc.id, [r.score.toFixed(4), r.tier]]));
  const anE = core.analyze(q, edge);
  const t0 = Date.now(); const bl = await edge.search(anE, 0); const ms = Date.now() - t0; totalMs += ms;
  const b = new Map(bl.map(r => [r.id, [r.score.toFixed(4), r.tier]]));
  const why = [];
  if (a.size !== b.size) why.push(`n mem=${a.size} edge=${b.size}`);
  for (const [id, v] of a) { const w = b.get(id); if (!w) { why.push(`edge lacks ${id}`); break; } if (w[0] !== v[0] || w[1] !== v[1]) { why.push(`${id}: mem ${v} edge ${w}`); break; } }
  for (const id of b.keys()) if (!a.has(id)) { why.push(`mem lacks ${id}`); break; }
  // Equal scores keep index.json order (layout 2 carries it in rank.json).
  if (!why.length) for (let i = 1; i < bl.length; i++)
    if (bl[i].score === bl[i - 1].score && pos.get(bl[i].id) < pos.get(bl[i - 1].id)) { why.push(`tie order broken at ${i}: ${bl[i - 1].id} before ${bl[i].id}`); break; }
  const top = bl[0] ? `${bl[0].id} ${bl[0].tier}` : "-";
  if (why.length) failures++;
  console.log(`  ${why.length ? "FAIL" : "ok  "} ${q.padEnd(22)} n=${b.size} top=${top} ${ms} ms ${why.join("; ")}`);
}
console.log(`\n${Q.length} queries · edge ${Math.round(totalMs / Q.length)} ms avg (cold file cache) · ${failures ? failures + " FAILED" : "all green"}`);
process.exit(failures ? 1 : 0);
