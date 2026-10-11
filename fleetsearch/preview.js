/* The fleet search on this machine: the real handler over the local twin of
 * the index, with the thumbnails served from cache/fleetsearch/thumbs/.
 *
 *     node fleetsearch/preview.js [port]        # then open http://localhost:8841/find?q=…
 *
 * Needs the twin (python3 fleetsearch/load.py --sql --local). The same
 * stand-in for D1 as tests/test_fleetsearch_page.js; the edge's guess at a
 * reader's position is faked as Chiang Mai, as it is there. */
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, normalize } from "node:path";
import { DatabaseSync } from "node:sqlite";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const TWIN = process.env.FLEET_TWIN || join(ROOT, "cache/fleetsearch/fleet.sqlite");
const DOCS = join(ROOT, "docs");
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp" };
const THUMBS = join(ROOT, "cache/fleetsearch/thumbs");
const PORT = Number(process.argv[2] || 8841);
if (!existsSync(TWIN)) { console.error(`no ${TWIN}; run python3 fleetsearch/load.py --sql --local`); process.exit(1); }

const { fleetSearch } = await import(join(ROOT, "publish/fleetsearch.js"));
const SEARCHCORE = (await import(join(ROOT, "publish/searchcore.js"))).default;
const groups = JSON.parse(readFileSync(join(ROOT, "docs/data/search_thesaurus.json"), "utf8")).groups;
const segdict = readFileSync(join(ROOT, "docs/data/search_segdict.txt"), "utf8").split("\n").filter((l) => l && l[0] !== "#");
const core = new SEARCHCORE.SearchCore(groups, segdict);

const db = new DatabaseSync(TWIN, { readOnly: true });
const SEARCH = {
  prepare(text) {
    return { text, binds: [], bind(...b) { this.binds = b; return this; },
             async all() { return { results: db.prepare(this.text).all(...this.binds) }; } };
  },
  async batch(stmts) { return stmts.map((s) => ({ results: db.prepare(s.text).all(...s.binds) })); },
};
const CF = { city: "Chiang Mai", latitude: "18.79038", longitude: "98.98468" };

createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (url.pathname.startsWith("/tiles/find/")) {
    const f = normalize(join(THUMBS, url.pathname.slice("/tiles/find/".length)));
    if (!f.startsWith(THUMBS) || !existsSync(f)) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "content-type": "image/webp" });
    res.end(readFileSync(f));
    return;
  }
  /* the site's own files beside the page (the peek script, the doodler, a place's .json twin) */
  const ext = (url.pathname.match(/\.[a-z]+$/) || [""])[0];
  if (TYPES[ext]) {
    const OVER = process.env.PREVIEW_OVERLAY;     // a scratch tree that stands in front of docs/
    const o = OVER ? normalize(join(OVER, decodeURIComponent(url.pathname))) : "";
    const f = o && o.startsWith(OVER) && existsSync(o) ? o
      : ext === ".html" ? "" : normalize(join(DOCS, decodeURIComponent(url.pathname)));
    if (f && (f.startsWith(DOCS) || (OVER && f.startsWith(OVER))) && existsSync(f)) {
      res.writeHead(200, { "content-type": TYPES[ext] });
      res.end(readFileSync(f));
      return;
    }
  }
  const r = new Request(url.toString());
  Object.defineProperty(r, "cf", { value: CF });
  const out = await fleetSearch(r, { SEARCH }, url, { waitUntil() {} }, async () => core);
  const headers = Object.fromEntries(out.headers.entries());
  res.writeHead(out.status, headers);
  res.end(out.status === 302 ? "" : Buffer.from(await out.arrayBuffer()));
}).listen(PORT, () => console.log(`fleet search preview on http://localhost:${PORT}/find`));
