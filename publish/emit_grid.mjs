#!/usr/bin/env node
/* emit_grid.mjs — api/v1/grid/, the box index the Worker answers
 * /api/v1/places?bbox= from without reading index.json. What it holds and
 * why: publish/api.js, "the grid".
 *
 *   docs/api/v1/grid/meta.json      v, the envelope's fields, one column per
 *                                   field a box query reads, in /places order
 *   docs/api/v1/grid/c0000.json …   { v, rows } — GRID_CHUNK whole rows each
 *
 * `v` is a hash of everything written. The Worker keeps a chunk only when its
 * v matches meta's, so a deploy caught halfway (new meta, old chunk) falls
 * back to the index instead of answering with the wrong row.
 *
 *   node publish/emit_grid.mjs [docs-dir]
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, unlinkSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { buildGrid } from "./api.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = resolve(process.argv[2] || join(HERE, "..", "docs"));
const V1 = join(DOCS, "api", "v1");
const OUT = join(V1, "grid");

const t0 = Date.now();
const index = JSON.parse(readFileSync(join(V1, "index.json"), "utf8"));
const { meta, chunks } = buildGrid(index);

const bodies = chunks.map((rows) => JSON.stringify(rows));
const h = createHash("sha1");
h.update(JSON.stringify(meta));
for (const b of bodies) h.update(b);
const v = h.digest("hex").slice(0, 12);

mkdirSync(OUT, { recursive: true });
const name = (c) => "c" + String(c).padStart(4, "0") + ".json";
const keep = new Set(["meta.json", ...chunks.map((_, c) => name(c))]);
for (const f of readdirSync(OUT)) if (!keep.has(f)) unlinkSync(join(OUT, f));
bodies.forEach((b, c) => writeFileSync(join(OUT, name(c)), `{"v":"${v}","rows":${b}}`));
writeFileSync(join(OUT, "meta.json"), JSON.stringify({ v, ...meta }));

const mb = (JSON.stringify(meta).length / 1e6).toFixed(1);
console.log(`  grid: ${meta.lat.length.toLocaleString()} pinned rows · ${chunks.length} chunks · ` +
            `meta ${mb} MB · v ${v} · ${((Date.now() - t0) / 1000).toFixed(1)} s`);
