/* The fleet search end to end, under plain node: the real handler, the real
 * dictionary and thesaurus, and the local twin of the index in place of D1.
 *
 *     node tests/test_fleetsearch_page.js
 *
 * Skips with a stated reason when the twin has not been built
 * (python3 fleetsearch/load.py --sql --local). D1 is a SQLite behind an
 * HTTP binding, so the same MATCH strings and the same SQL run here through
 * node:sqlite; what this cannot see is D1's own latency, which the deploy
 * check in fleetsearch/README.md measures live. */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { gzipSync } from "node:zlib";

/* Page weight is judged gzipped, not raw (client 2026-09-26): ~6 KB over the
 * wire is what a rural reader actually downloads, and Thai text compresses ~5x,
 * so a raw-byte cap punished a text-heavy page. The ceiling still catches a
 * runaway — an uncompressible or unbounded page — with room for the richer
 * curation header (WO-97). */
const gz = (s) => gzipSync(Buffer.from(s)).length;

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const TWIN = join(ROOT, "cache/fleetsearch/fleet.sqlite");
if (!existsSync(TWIN)) {
  console.log(`SKIPPED — no ${TWIN}; run python3 fleetsearch/load.py --sql --local`);
  process.exit(0);
}

const { fleetSearch } = await import(join(ROOT, "publish/fleetsearch.js"));
const SEARCHCORE = (await import(join(ROOT, "publish/searchcore.js"))).default;

const groups = JSON.parse(readFileSync(join(ROOT, "docs/data/search_thesaurus.json"), "utf8")).groups;
const segdict = readFileSync(join(ROOT, "docs/data/search_segdict.txt"), "utf8")
  .split("\n").filter((l) => l && l[0] !== "#");
const core = new SEARCHCORE.SearchCore(groups, segdict);
const coreP = async () => core;

const db = new DatabaseSync(TWIN, { readOnly: true });
const SEARCH = {
  prepare(text) {
    return { text, binds: [],
      bind(...b) { this.binds = b; return this; },
      async all() { return { results: db.prepare(this.text).all(...this.binds) }; } };
  },
  async batch(stmts) { return stmts.map((s) => ({ results: db.prepare(s.text).all(...s.binds) })); },
};
const env = { SEARCH };
const ctx = { waitUntil() {} };

/* The edge attaches cf.latitude/longitude to the request; here it is faked, so
 * the no-permission path can be tested. Chiang Mai, where Cloudflare put a
 * real connection on 2026-09-21. */
const CF = { city: "Chiang Mai", latitude: "18.79038", longitude: "98.98468",
             timezone: "Asia/Bangkok", country: "TH" };

async function get(path, cf) {
  const url = new URL("https://motdang.net" + path);
  const req = new Request(url.toString());
  Object.defineProperty(req, "cf", { value: cf === null ? undefined : (cf || CF) });
  const t = Date.now();
  const res = await fleetSearch(req, env, url, ctx, coreP);
  const ms = Date.now() - t;
  const body = res.status === 302 ? "" : await res.text();
  return { status: res.status, body, ms, h: res.headers };
}

let failures = 0;
async function t(name, fn) {
  try { await fn(); console.log("  ok   " + name); }
  catch (e) { failures++; console.log("  FAIL " + name + "\n       " + e.message); }
}
const must = (cond, msg) => { if (!cond) throw new Error(msg); };
const count = (body) => {
  const m = body.match(/พบ ([\d,]+) หน้า/);
  return m ? Number(m[1].replace(/,/g, "")) : 0;
};
const urls = (body) => Array.from(body.matchAll(/<a class="t" href="([^"]+)"/g)).map((m) => m[1]);
const dates = (body) => Array.from(body.matchAll(/· (\d\d-[A-Z][a-z][a-z]-\d{4}) ·/g)).map((m) => m[1]);
const titles = (body) => Array.from(body.matchAll(/<a class="t" href="[^"]+">([^<]*)</g)).map((m) => m[1]);
const iso = (d) => { const [dd, mon, yy] = d.split("-");
  return `${yy}-${String(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].indexOf(mon) + 1).padStart(2, "0")}-${dd}`; };
const dist = (body) => Array.from(body.matchAll(/<span class="d">· ([^<·]+) ·/g)).map((m) => m[1].trim());
/* The scripts a results page may carry, each for one job: the share/LINE/Grab
 * buttons (/locshare.js), the language switch, the place-refine chips, and the
 * position tap when a distance is on offer. Anything else is a stranger. */
const KNOWN_SCRIPT = [/^<script src="\/locshare\.js" defer>/, /^<script>\(function\(\)\{var d=document,r=d\.documentElement,l;/,
                      /^<script>\(function\(\)\{\nvar q=/, /^<script>document\.getElementById\("md-exact"\)/];
const scripts = (body) => Array.from(body.matchAll(/<script[^>]*>[\s\S]{0,60}/g)).map((m) => m[0]);
const strangers = (body) => scripts(body).filter((x) => !KNOWN_SCRIPT.some((re) => re.test(x)));
const bar = (body) => { const m = body.match(/<div class="bar">([\s\S]*?)<\/div>\s*<ol/); return m ? m[1] : ""; };

await t("the front lists every site with a count", async () => {
  const r = await get("/find");
  must(r.status === 200, "status " + r.status);
  must(/pages from \d+ sites/.test(r.body), "site count line missing");
  must(/motdang\.net<\/a> \(/.test(r.body), "motdang row missing");
  // 12,000 for 20 sites; the roster reached 57 on 2026-10-03, a row each.
  must(r.body.length < 17000, `front is ${r.body.length} bytes`);
});

await t("a Thai word: ตอกเส้น finds the tok sen pages", async () => {
  const r = await get("/find?q=ตอกเส้น");
  must(count(r.body) >= 30, `only ${count(r.body)} found`);
  must(/ตอกเส้น|tok sen/i.test(urls(r.body).length ? r.body : ""), "no tok sen title");
  must(r.ms < 400, `${r.ms} ms`);
});

await t("a Thai compound is one phrase: ร้านกาแฟนิมมาน", async () => {
  const r = await get("/find?q=ร้านกาแฟนิมมาน");
  must(count(r.body) >= 1, "nothing found");
  must(/แยกคำ/.test(r.body), "the words-split note is missing");
});

await t("every word first, then any word — and the page says so", async () => {
  const r = await get("/find?q=barbecue+qqxqq");
  must(count(r.body) >= 1, "nothing found");
  must(/ไม่ครบทุกคำ/.test(r.body), "the fallback note is missing");
});

await t("toksen reaches ตอกเส้น through the thesaurus", async () => {
  const r = await get("/find?q=toksen+kru+dao");
  must(count(r.body) >= 1, "nothing found");
});

await t("lucky goes straight to the first page", async () => {
  const r = await get("/find?q=tok+sen+massage&lucky=1");
  must(r.status === 302, "status " + r.status);
  must(/^https:\/\//.test(r.h.get("location")), "location " + r.h.get("location"));
});

await t("upper-case NEAR in the simple box is boolean", async () => {
  const r = await get("/find?q=elephant+NEAR+sanctuary");
  must(count(r.body) >= 1, "nothing found");
  must(/^NEAR\(/.test(r.h.get("x-fleet-match")), "match " + r.h.get("x-fleet-match"));
});

await t("the boolean page refuses a lone NOT, and says why", async () => {
  const r = await get("/find?adv=1&q=NOT+spa");
  must(/NOT needs a word before it/.test(r.body), "no refusal");
});

await t("site: keeps every result on that site", async () => {
  const r = await get("/find?q=massage&site=wichaa.net");
  const u = urls(r.body);
  must(u.length >= 1, "nothing found");
  must(u.every((x) => x.startsWith("https://wichaa.net/")), "a foreign url: " + u.find((x) => !x.startsWith("https://wichaa.net/")));
  must(/ทุกไซต์ · All sites/.test(bar(r.body)), "no way back to all sites");
});

await t("a site the reader typed narrows the same way", async () => {
  const r = await get("/find?q=barbecue+site:carolina-barbecue");
  const u = urls(r.body);
  must(u.length >= 1 && u.every((x) => x.includes("/carolina-barbecue/")), "wrong site in " + u[0]);
});

await t("nothing found says so", async () => {
  const r = await get("/find?q=zzzzqqqxxwww");
  must(/0 pages found/.test(r.body), "no zero line");
});

await t("page two starts at 11", async () => {
  const r = await get("/find?q=barbecue+vinegar&p=2");
  must(/<ol start="11">/.test(r.body), "ol start missing");
  must(/Prev/.test(r.body) && /Next/.test(r.body), "pager missing");
});

await t("json answers with the shape a machine expects", async () => {
  const r = await get("/find?q=ยันต์&fmt=json");
  const d = JSON.parse(r.body);
  must(d.total > 0 && d.results[0].url && d.results[0].title, "shape " + r.body.slice(0, 200));
  must(r.h.get("access-control-allow-origin") === "*", "no CORS");
});

await t("a results page is small", async () => {
  const r = await get("/find?q=เชียงใหม่");
  must(count(r.body) > 10000, `only ${count(r.body)} for เชียงใหม่`);
  /* 9,000 until 2026-10-03; the site's top bar and language switch added
   * ~0.6 KB, and best match now starts with place rows near the reader, which
   * carry their contact, toilet and hours line where list pages did not.
   * 12,000 from 2026-10-04 (publish/findpreview.js, Nan: "not enough preview
   * anywhere"): a reading, a where-line and a list's five pictures per row,
   * measured +1.3 to +2.0 KB gzipped on เชียงใหม่, big bike rental, khao soi,
   * ร้านกาแฟ. */
  must(gz(r.body) < 12000, `${gz(r.body)} bytes gzipped (${r.body.length} raw)`);
  must(!strangers(r.body).length, "a script with no job: " + strangers(r.body).join(" | "));
  must(/first 1,000 shown/.test(r.body), "the cap is not stated");
});

/* The twin is a 660 MB file and the first touch of a row is a disk read, so
 * the timing cases warm the pages they are about to measure. What is being
 * held to a number here is the query work, not this laptop's page cache. */
async function warm(paths) { for (const p of paths) await get(p); }

await t("twelve ordinary queries each answer under 300 ms here", async () => {
  const qs = ["tok sen", "หมอฟัน", "elephant sanctuary", "yant", "muay thai gym", "pil pil",
              "รถมือสอง", "dermatologist", "vegan cafe nimman", "wat phra singh", "ยันต์ห้าแถว", "barbecue"];
  const slow = [];
  await warm(qs.map((q) => "/find?q=" + encodeURIComponent(q)));
  for (const q of qs) {
    const r = await get("/find?q=" + encodeURIComponent(q));
    if (r.ms >= 300) slow.push(`${q} ${r.ms} ms`);
    must(r.status === 200, q + " status " + r.status);
  }
  must(!slow.length, slow.join(", "));
});

await t("the bar offers a sort, a place for the words, a date and a site", async () => {
  const b = bar((await get("/find?q=massage")).body);
  for (const label of ["เรียง · Sort", "คำอยู่ที่ · Words in", "ปรับปรุง · Updated", "ไซต์ · Site"])
    must(b.includes(label), "no row: " + label);
  must(/Best match<\/b>/.test(b), "relevance is not marked as the one in force");
  must(/wichaa\.net<\/a>/.test(b), "no wichaa row in the site facet");
});

await t("the curation header reads as controls: sort in view, narrowers behind Refine, sprites not emoji", async () => {
  const b = (await get("/find?q=massage")).body;
  const bd = bar(b);
  must(/<div class="g srt">/.test(bd), "sort is not its own always-visible row");
  must(/<details class="refine"><summary>/.test(bd), "the narrowers are not behind a Refine control");
  must(/\/icons\.svg#i-sort/.test(bd) && /\/icons\.svg#i-filter/.test(bd), "sort/refine sprites missing");
  must(/\/icons\.svg#i-/.test(bd), "no sprite in the has features");
  must(!/[📷☎🚻🎪🕘🟢☑☐]/u.test(bd), "an emoji survived in the curation header");
});

await t("newest first really is newest first", async () => {
  const r = await get("/find?q=massage&sort=new");
  const d = dates(r.body).map(iso);
  must(d.length >= 5, "too few rows");
  must(d.join() === [...d].sort().reverse().join(), "out of order: " + d.join(" "));
  must(/ใหม่สุด · Newest<\/b>/.test(r.body), "newest is not marked in force");
});

await t("oldest first is the other end of the same answer", async () => {
  const d = dates((await get("/find?q=massage&sort=old")).body).map(iso);
  must(d.join() === [...d].sort().join(), "out of order: " + d.join(" "));
});

await t("A–Z sorts by title, case-blind", async () => {
  const ts = titles((await get("/find?q=massage&sort=az")).body).map((x) => x.toLowerCase());
  must(ts.length >= 5 && ts.join() === [...ts].sort().join(), "out of order: " + ts.slice(0, 3).join(" | "));
});

await t("a sort keeps the same answer, only reordered", async () => {
  const a = await get("/find?q=tok+sen");
  const b = await get("/find?q=tok+sen&sort=az");
  must(count(a.body) === count(b.body), `${count(a.body)} vs ${count(b.body)}`);
});

await t("a sort over more than the window says so", async () => {
  const r = await get("/find?q=เชียงใหม่&sort=new");
  must(/sorted within the 1,000 best matches/.test(r.body), "the window is not stated");
  must(!/sorted within/.test((await get("/find?q=tok+sen&sort=new")).body), "stated on a small answer");
});

await t("title-only narrows, and the count falls", async () => {
  const all = await get("/find?q=massage");
  const ti = await get("/find?q=massage&in=title");
  must(count(ti.body) > 0 && count(ti.body) < count(all.body), `${count(ti.body)} vs ${count(all.body)}`);
  must(titles(ti.body).every((x) => /massage|นวด/i.test(x)), "a title without the word: " + titles(ti.body)[0]);
});

await t("a reader's own title: turns the words-in row off", async () => {
  const b = bar((await get("/find?q=title:massage")).body);
  must(!b.includes("คำอยู่ที่"), "the row is offered over a query that already names a column");
});

await t("updated-within filters by date, and the count matches the bar", async () => {
  const r = await get("/find?q=massage");
  const m = bar(r.body).match(/(7 วัน · 7 days|30 วัน · 30 days|ปีนี้ · A year)<\/a> <span class="n">\(([\d,]+)\)/);
  must(m, "no dated bucket in the bar: " + bar(r.body).slice(0, 300));
  const key = { "7 วัน · 7 days": "7d", "30 วัน · 30 days": "30d", "ปีนี้ · A year": "1y" }[m[1]];
  const got = await get("/find?q=massage&since=" + key);
  must(count(got.body) === Number(m[2].replace(/,/g, "")), `bar ${m[2]} vs answer ${count(got.body)}`);
});

await t("two sites on one host are told apart in the bar", async () => {
  const b = bar((await get("/find?q=wat")).body);
  const labels = Array.from(b.matchAll(/>([a-z0-9.\/-]+)<\/a> <span class="n">/g)).map((m) => m[1]);
  must(labels.length >= 2, "too few site rows: " + labels.join(" "));
  must(new Set(labels).size === labels.length, "two rows read the same: " + labels.join(" "));
  must(labels.some((x) => x.includes("/")), "no host/site label: " + labels.join(" "));
});

await t("a site row over an answer that lives on one site is not offered", async () => {
  /* ร้านซักรีด was one site's answer until a Mae Hong Son loop page named a
   * laundry; ซักรีด still lives on Mot Dang alone (twin of 2026-10-02). */
  const one = await get("/find?q=ซักรีด");
  must(count(one.body) > 0, "ซักรีด found nothing");
  if (count(one.body) > 0 && !/wichaa/.test(bar(one.body))) {
    must(!bar(one.body).includes("ไซต์ · Site"), "one site is offered as a choice");
  }
  must(bar((await get("/find?q=massage")).body).includes("ไซต์ · Site"), "many sites are not offered");
});

await t("a date bucket that narrows nothing is not offered", async () => {
  const b = bar((await get("/find?q=massage")).body);
  const ns = Array.from(b.matchAll(/(?:วัน|ปีนี้)[^<]*<\/a> <span class="n">\(([\d,]+)\)/g)).map((x) => x[1]);
  must(new Set(ns).size === ns.length, "two buckets with the same count: " + ns.join(" "));
});

await t("a site count in the bar is the count you get on clicking it", async () => {
  const r = await get("/find?q=massage");
  const m = bar(r.body).match(/>wichaa\.net<\/a> <span class="n">\(([\d,]+)\)/);
  must(m, "no wichaa count");
  const got = await get("/find?q=massage&site=wichaa");
  must(count(got.body) === Number(m[1].replace(/,/g, "")), `bar ${m[1]} vs answer ${count(got.body)}`);
});

await t("filters ride on the pager and on the box", async () => {
  const r = await get("/find?q=massage&sort=new&site=motdang&n=20");
  const next = r.body.match(/href="([^"]*)">ถัดไป/);
  must(next, "no next link");
  for (const bit of ["sort=new", "site=motdang", "n=20", "p=2"])
    must(next[1].includes(bit), `${bit} missing from ${next[1]}`);
  must(/<input type="hidden" name="sort" value="new">/.test(r.body), "the box drops the sort");
  must(/<input type="hidden" name="site" value="motdang">/.test(r.body), "the box drops the site");
});

await t("a date that is not a date is dropped, not obeyed", async () => {
  const good = await get("/find?q=massage");
  const junk = await get("/find?q=massage&from=yesterday&to=soon");
  must(count(junk.body) === count(good.body), `${count(junk.body)} vs ${count(good.body)}`);
});

await t("a preset travels as the preset, not as the day it worked out to", async () => {
  const r = await get("/find?q=massage&since=1y");
  must(/<input type="hidden" name="since" value="1y">/.test(r.body), "the preset is not kept");
  must(!/name="from"/.test(r.body), "the box carries a fixed date instead of the preset");
});

await t("changing a filter returns to page one", async () => {
  const r = await get("/find?q=massage&p=3");
  const link = r.body.match(/href="([^"]*sort=new[^"]*)"/);
  must(link && !link[1].includes("p=3"), "page three followed the sort: " + (link && link[1]));
});

await t("nothing found names the filters in force", async () => {
  const r = await get("/find?q=massage&site=pink-box&since=7d");
  if (count(r.body) === 0) {
    must(/filters in force/.test(r.body), "no way out offered");
    must(/all sites/.test(r.body) && /any date/.test(r.body), "the filters are not offered off");
  }
});

await t("the boolean form carries sort, words-in and dates", async () => {
  const r = await get("/find?adv=1&q=massage+AND+nimman&sort=az&in=title&from=2026-01-01");
  must(/<select name="sort">[\s\S]*?<option value="az" selected/.test(r.body), "sort not selected");
  must(/<select name="in">[\s\S]*?<option value="title" selected/.test(r.body), "words-in not selected");
  must(/name="from" value="2026-01-01"/.test(r.body), "from not kept");
});

await t("json says how it was sorted and filtered", async () => {
  const d = JSON.parse((await get("/find?q=massage&sort=new&in=title&since=30d&fmt=json")).body);
  must(d.sort === "new" && d.in === "title" && /^\d{4}-\d{2}-\d{2}$/.test(d.from), JSON.stringify(d).slice(0, 200));
  must(d.results.length > 0, "no results");
});

await t("a filtered page is still small, and carries nothing but the position tap", async () => {
  const r = await get("/find?q=เชียงใหม่&sort=new");
  must(!strangers(r.body).length, "a script with no job: " + strangers(r.body).join(" | "));
  /* The pictures beside the rows are the one thing it fetches, lazily, from
   * the bucket's tiles/find/ — no script, no stylesheet, no other host. */
  const srcs = Array.from(r.body.matchAll(/src="([^"]*)"/g)).map((m) => m[1]);
  must(srcs.every((x) => x === "/locshare.js" || (x.startsWith("/tiles/find/") && /\.webp$/.test(x))), "fetches " + srcs.find((x) => !x.startsWith("/tiles/find/")));
  must((r.body.match(/<img /g) || []).length === (r.body.match(/loading="lazy"/g) || []).length, "an eager image");
  must(gz(r.body) < 12500, `${gz(r.body)} bytes gzipped (${r.body.length} raw)`);   // 11,000 before findpreview.js
});

await t("ten filtered and sorted queries answer under 400 ms here", async () => {
  const paths = ["/find?q=massage&sort=new", "/find?q=massage&sort=az", "/find?q=เชียงใหม่&sort=new",
                 "/find?q=cafe&sort=old", "/find?q=wat&site=wichaa", "/find?q=massage&since=30d",
                 "/find?q=massage&in=title", "/find?q=ยันต์&sort=az", "/find?q=barbecue&sort=new",
                 "/find?adv=1&q=massage+NOT+spa&sort=new"];
  const slow = [];
  await warm(paths);
  for (const p of paths) {
    const r = await get(p);
    must(r.status === 200, p + " status " + r.status);
    if (r.ms >= 400) slow.push(`${p} ${r.ms} ms`);
  }
  must(!slow.length, slow.join(", "));
});

await t("the edge's guess puts a distance on every pinned row, and rounds it coarse", async () => {
  const r = await get("/find?q=นวด");
  const d = dist(r.body);
  must(d.length >= 5, "no distances: " + r.body.slice(r.body.indexOf("<ol"), 400));
  must(d.every((x) => /^(ใกล้ๆ|~\d+ กม\.)$/.test(x)), "a coarse guess given a decimal: " + d.join(" "));
  must(/ตำแหน่งโดยประมาณจากเครือข่าย/.test(r.body), "the page does not say the position is a guess");
  must(/Chiang Mai/.test(r.body), "the city is not named");
});

await t("an exact position is drawn as one, and says so", async () => {
  const r = await get("/find?q=นวด&near=18.78900,99.04500");
  const d = dist(r.body);
  must(d.some((x) => /^\d+ ม\.$|^\d+\.\d กม\.$/.test(x)), "no exact distance: " + d.join(" "));
  must(/ตำแหน่งจริงของคุณ/.test(r.body), "the page does not say the position is the reader's");
});

await t("nearest first really is nearest first", async () => {
  const r = await get("/find?q=นวด&sort=near&near=18.78900,99.04500&fmt=json");
  const d = JSON.parse(r.body);
  const ms = d.results.map((x) => x.metres).filter((x) => x !== undefined);
  must(ms.length >= 5, "too few measured rows");
  must(ms.join() === [...ms].sort((a, b) => a - b).join(), "out of order: " + ms.join(" "));
  must(ms[0] < 4000, `the nearest is ${ms[0]} m away`);
  must(d.near.exact === true && d.near.lat === 18.789, JSON.stringify(d.near));
});

await t("nearest is offered only when a position is known", async () => {
  must(/ใกล้ที่สุด · Nearest/.test(bar((await get("/find?q=นวด")).body)), "not offered with a guess");
  const blind = await get("/find?q=นวด", null);
  must(!/ใกล้ที่สุด/.test(bar(blind.body)), "offered with no position at all");
  must(!/<span class="d">/.test(blind.body), "a distance with no position");
  must(count(blind.body) > 0, "the answer itself broke");
});

await t("asking to sort by distance with no position falls back, it does not break", async () => {
  const r = await get("/find?q=นวด&sort=near", null);
  must(count(r.body) > 0, "nothing found");
  must(/ตรงที่สุด · Best match<\/b>/.test(r.body), "did not fall back to relevance");
});

await t("a page with no pin is sorted last, never dropped", async () => {
  const r = await get("/find?q=chiang+mai&sort=near&near=18.78900,99.04500&n=50&fmt=json");
  const d = JSON.parse(r.body);
  const seen = d.results.map((x) => x.metres === undefined);
  must(seen.includes(false), "nothing measured at all");
  must(seen.join() === [...seen].sort().join(), "an unpinned page came before a measured one");
});

await t("the exact position travels with the other filters", async () => {
  const r = await get("/find?q=นวด&sort=near&near=18.78900,99.04500&site=motdang");
  must(/<input type="hidden" name="near" value="18.789,99.045">/.test(r.body), "the box drops it");
  const next = r.body.match(/href="([^"]*)">ถัดไป/);
  must(next && /near=18\.789\d*%2C99\.045/.test(next[1]), "the pager drops it: " + (next && next[1]));
});

await t("the position tap is on the page only when a distance is on offer, beside the known scripts", async () => {
  const withPin = await get("/find?q=นวด");
  must(!strangers(withPin.body).length, "a script with no job: " + strangers(withPin.body).join(" | "));
  must(/md-exact/.test(withPin.body), "no tap offered");
  const blind = (await get("/find?q=นวด", null)).body;
  must(!/getElementById\("md-exact"\)/.test(blind), "a position tap with no position");
  must(!strangers(blind).length, "a script with no job");
});

await t("a busy index is not the reader's fault, and says so", async () => {
  const angry = { prepare() { return { bind() { return this; },
    async all() { throw new Error("D1_ERROR: internal error; reference = e_PVSMDp"); } }; },
    async batch() { throw new Error("D1_ERROR: internal error"); } };
  const url = new URL("https://motdang.net/find?q=massage");
  const res = await fleetSearch(new Request(url.toString()), { SEARCH: angry }, url, ctx, coreP);
  const body = await res.text();
  must(res.status === 503, "status " + res.status);
  must(res.headers.get("cache-control") === "no-store", "a fault was left cacheable");
  must(res.headers.get("retry-after") === "60", "no retry-after");
  must(/the index is being rebuilt/.test(body), "does not say what happened");
  must(/the rest of the site is unaffected/.test(body), "does not say what still works");
  must(!/expression could not be read/.test(body), "blames the reader's query");
});

await t("an expression the engine refuses still blames the expression", async () => {
  const picky = { prepare() { return { bind() { return this; },
    async all() { throw new Error('fts5: syntax error near ""'); } }; },
    async batch() { throw new Error('fts5: syntax error near ""'); } };
  const url = new URL("https://motdang.net/find?adv=1&q=massage+AND");
  const res = await fleetSearch(new Request(url.toString()), { SEARCH: picky }, url, ctx, coreP);
  const body = await res.text();
  must(res.status === 200, "status " + res.status);
  must(/expression could not be read/.test(body), "does not name the expression");
  must(!/being rebuilt/.test(body), "blames the index for a bad query");
});


/* ---- what a row holds besides its words (2026-09-23) ---- */

await t("a place row: its site and breadcrumb, a picture or its map, and what it holds", async () => {
  const r = await get("/find?q=wawee+coffee+wat+ket&kind=place");
  must(count(r.body) >= 1, "nothing found");
  const li = r.body.slice(r.body.indexOf("<li>"), r.body.indexOf("</li>"));
  must(/<div class="cr"><a href="https:\/\/motdang\.net\/">motdang\.net<\/a> › <a href="https:\/\/motdang\.net\/cm\/index\.html">เชียงใหม่ · Chiang Mai<\/a>/.test(li), "no breadcrumb: " + li.slice(0, 300));
  must(/class="th"[^>]*><img src="\/tiles\/find\/(g|p)\//.test(li), "no picture and no map: " + li.slice(0, 300));
  must(/ติดต่อได้ \d ทาง · \d ways to reach|โทร · phone/.test(li), "the ways to reach it are not said");
});

await t("a map thumbnail carries its pin inside the middle half", async () => {
  const r = await get("/find?q=massage&kind=place&n=50");
  const pins = Array.from(r.body.matchAll(/<i style="left:([\d.]+)%;top:([\d.]+)%">/g)).map((m) => [Number(m[1]), Number(m[2])]);
  must(pins.length >= 5, "too few maps: " + pins.length);
  must(pins.every(([x, y]) => x >= 25 && x < 75 && y >= 25 && y < 75), "a pin at the edge: " + JSON.stringify(pins.find(([x, y]) => x < 25 || x >= 75 || y < 25 || y >= 75)));
});

await t("type narrows, and the count in the bar is the count you get", async () => {
  const r = await get("/find?q=coffee");
  const m = bar(r.body).match(/>สถานที่ · Places<\/a> <span class="n">\(([\d,]+)\)/);
  must(m, "no Places option: " + bar(r.body).slice(0, 400));
  const got = await get("/find?q=coffee&kind=place");
  must(count(got.body) === Number(m[1].replace(/,/g, "")), `bar ${m[1]} vs answer ${count(got.body)}`);
  must(!/\/tag\//.test(urls(got.body).join(" ")), "a tag list among the places");
});

await t("each has-switch narrows to what the bar counted, and they add up", async () => {
  const r = await get("/find?q=massage");
  const b = bar(r.body);
  for (const [key, label] of [["contact", "ติดต่อได้ · Contact"], ["hours", "เวลาเปิด · Hours"]]) {
    const m = b.match(new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "</a> <span class=\"n\">\\(([\\d,]+)\\)"));
    must(m, "no " + key + " switch: " + b.slice(0, 500));
    const got = await get("/find?q=massage&has=" + key);
    must(count(got.body) === Number(m[1].replace(/,/g, "")), `${key}: bar ${m[1]} vs answer ${count(got.body)}`);
    /* On-state now reads from the chip: a span marked "on" carrying the label
     * (the ☑ emoji is gone — sprites, ICON-POLICY.md). */
    must(/<span class="on">/.test(bar(got.body)) && bar(got.body).includes(label), key + " is not shown as on");
  }
  const both = await get("/find?q=massage&has=contact,hours");
  const one = await get("/find?q=massage&has=hours");
  must(count(both.body) <= count(one.body), "two switches gave more than one");
  must(/<input type="hidden" name="has" value="contact,hours">/.test(both.body), "the box drops the switches");
});

await t("few results and a filter on: the page offers to uncheck and widen (WO-95)", async () => {
  /* วัด is thousands of pages; asking only for the ones with an event to come
   * drops it under FEW, and then the way back out has to be on the page. */
  const wide = await get("/find?q=" + encodeURIComponent("วัด"));
  must(count(wide.body) > 20, "วัด should be well over FEW: " + count(wide.body));
  must(!/class="loosen"/.test(wide.body), "the widen line showed with no filter on");

  const few = await get("/find?q=" + encodeURIComponent("วัดพระสิงห์") + "&has=events");
  const n = count(few.body);
  must(n > 0 && n <= 20, "expected a few, got " + n);
  const m = few.body.match(/<p class="loosen">([\s\S]*?)<\/p>/);
  must(m, "no widen line on a narrowed few-result page");
  /* The line takes the reader OUT of the filter: a link back to the same
   * query with has=events dropped. */
  must(/<a href="[^"]*\/find\?q=/.test(m[1]) && !/has=events/.test(m[1]),
       "the widen link does not drop the filter: " + m[1]);
});

await t("a toilet is said where the toilet minisite knows one, and links to it", async () => {
  const r = await get("/find?q=วัดพระสิงห์&kind=place");
  must(/<a href="\/toilets\.html"[^>]*>🚻 /.test(r.body), "no toilet line on a wat");
  const t = await get("/find?q=massage&has=toilet");
  if (count(t.body) > 0) {
    const rows = t.body.split("<li>").slice(1);
    must(rows.every((x) => /🚻 (?!ห้องน้ำ \d)/.test(x)), "a row in the toilet filter without its own toilet");
  }
});

await t("section comes from the breadcrumb and narrows to its count", async () => {
  const r = await get("/find?q=massage");
  const m = bar(r.body).match(/href="([^"]*sec=[^"]*)">[^<]*<\/a> <span class="n">\(([\d,]+)\)/);
  must(m, "no section row: " + bar(r.body).slice(0, 500));
  const got = await get(m[1].replace(/&amp;/g, "&"));
  must(count(got.body) === Number(m[2].replace(/,/g, "")), `bar ${m[2]} vs answer ${count(got.body)}`);
});

await t("most detail puts the fuller rows first", async () => {
  const d = JSON.parse((await get("/find?q=massage&sort=rich&fmt=json&n=20")).body);
  const score = (x) => (x.thumb ? 1 : 0) + (x.ways || []).length + (x.toilet && x.toilet.kind !== "nearby" ? 1 : 0) + (x.hours ? 1 : 0);
  const s = d.results.map(score);
  must(s[0] >= s[s.length - 1], "the first row holds less than the last: " + s.join(" "));
  must(/ข้อมูลมากสุด · Most detail/.test(bar((await get("/find?q=massage&sort=rich")).body)), "not offered");
});

await t("json carries the crumbs, the picture and what the row holds", async () => {
  const d = JSON.parse((await get("/find?q=wawee+coffee&kind=place&fmt=json")).body);
  const x = d.results[0];
  must(x && x.kind === "place" && Array.isArray(x.crumbs) && x.crumbs[0].name, JSON.stringify(x).slice(0, 300));
  must(!x.thumb || /^https?:\/\/[^/]+\/tiles\/find\/(p|g)\//.test(x.thumb), "thumb " + x.thumb);
  must(d.kind === "place", "the filter is not reported");
});

await t("the new filters answer under 400 ms here", async () => {
  const paths = ["/find?q=massage&has=contact", "/find?q=coffee&kind=place", "/find?q=เชียงใหม่&has=photo",
                 "/find?q=massage&sort=rich", "/find?q=wat&has=toilet", "/find?q=massage&has=open"];
  await warm(paths);
  const slow = [];
  for (const p of paths) {
    const r = await get(p);
    must(r.status === 200, p + " status " + r.status);
    if (r.ms >= 400) slow.push(`${p} ${r.ms} ms`);
  }
  must(!slow.length, slow.join(", "));
});

/* ---- measured live 2026-10-03, and fixed: one case per item ---- */

/* The site register, as the Worker reads it from the bucket (data/sites.json). */
const REG = JSON.parse(readFileSync(join(ROOT, "docs/data/sites.json"), "utf8"));
const envR = { SEARCH, SITE: { async get(k) { return k === "data/sites.json" ? { json: async () => REG } : null; } } };
async function getR(path, cf) {
  const url = new URL("https://motdang.net" + path);
  const req = new Request(url.toString());
  Object.defineProperty(req, "cf", { value: cf || CF });
  const res = await fleetSearch(req, envR, url, ctx, coreP);
  return { status: res.status, body: res.status === 302 ? "" : await res.text(), h: res.headers };
}
const CR = { city: "Chiang Rai", latitude: "19.9105", longitude: "99.8406", timezone: "Asia/Bangkok", country: "TH" };
const km = (x) => (/nearby|ใกล้ๆ/.test(x) ? 0 : Number((x.match(/~?(\d+)/) || [])[1]));
const placeKm = (body) => Array.from(body.matchAll(/<span class="d">· ([^<]+)<\/span>/g)).map((m) => km(m[1]));

await t("1 a misspelling finds the word it was meant to be, and says so", async () => {
  const r = await get("/find?q=massge");
  must(count(r.body) > 100, "massge found " + count(r.body));
  must(/near spellings — closest first: massge → massage/.test(r.body), "the tier is not said");
  must(!/try another word, another spelling/.test(r.body), "still tells the reader to respell");
  const two = await get("/find?q=massge+cafe");
  must(count(two.body) > 0 && /near spellings/.test(two.body), "a misspelling beside a good word");
});

await t("2 every spelling of khao soi answers with about the same set", async () => {
  const qs = ["khao soi", "kao soi", "khaosoi", "khao soy", "kaosoi", "ข้าวซอย"];
  const ns = [];
  for (const q of qs) ns.push(count((await get("/find?q=" + encodeURIComponent(q))).body));
  const lo = Math.min(...ns), hi = Math.max(...ns);
  must(lo >= 500, "a spelling still finds little: " + qs.map((q, k) => `${q} ${ns[k]}`).join(", "));
  must(hi <= lo * 1.3, "the sets differ: " + qs.map((q, k) => `${q} ${ns[k]}`).join(", "));
});

await t("3 near me sorts by distance; a price is declined out loud; neither is matched as a word", async () => {
  const r = await get("/find?q=khao+soi+near+me");
  must(/near me — nearest first/.test(r.body), "near me not read");
  must(!/"near"|"me"/.test(decodeURIComponent(r.h.get("x-fleet-match"))), "near me still in the match");
  const d = placeKm(r.body).slice(0, 5);
  must(d.length >= 3 && d.every((x) => x <= 3), "not nearest first: " + d.join(" "));
  must(titles(r.body).slice(0, 5).every((x) => /khao ?soi|kao soi|ข้าวซอย|kho soi/i.test(x)), "a loose match sorted in: " + titles(r.body).slice(0, 5).join(" | "));
  const h = await get("/find?q=hospital+near+me");
  must(/hospital|โรงพยาบาล|รพ/i.test(titles(h.body)[0] || ""), "hospital near me starts with " + titles(h.body)[0]);
  const c = await get("/find?q=cheap+massage");
  must(/no prices to filter on/.test(c.body), "the price is not declined");
  must(!/cheap/.test(decodeURIComponent(c.h.get("x-fleet-match"))), "cheap still in the match");
  must(/massage|นวด/i.test(titles(c.body)[0] || ""), "cheap massage starts with " + titles(c.body)[0]);
  const o = await get("/find?q=massage+open+now");
  must(/open now — filtered/.test(o.body) && /class="on"><a[^>]*>[^<]*<svg[^>]*><use href="\/icons\.svg#i-check"/.test(o.body), "open now is not the filter");
});

await t("4 NOT with nothing to subtract from searches nothing, and says so", async () => {
  for (const q of ["NOT khao", "-khao"]) {
    const r = await get("/find?q=" + encodeURIComponent(q));
    must(r.status === 200, q + " status " + r.status);
    must(count(r.body) === 0 && !/<ol/.test(r.body), q + " returned pages");
    must(/nothing to subtract from: −khao/.test(r.body), q + " does not say why");
    must(/pages from \d+ sites/.test(r.body), q + " no sites list");
  }
  must(count((await get("/find?q=NOT+khao+soi")).body) > 0, "NOT khao soi should still find soi");
});

await t("5 a query of signs alone gets the front, and short Thai never fails", async () => {
  for (const q of ['"', "-", "*", "+", "title:", "−"]) {
    const r = await get("/find?q=" + encodeURIComponent(q));
    must(r.status === 200, `${q} status ${r.status}`);
    must(/type a word/.test(r.body) && /pages from \d+ sites/.test(r.body), `${q}: no sites list`);
  }
  for (const q of ["ก", "ม", "ๆ", "่"]) {
    const r = await get("/find?q=" + encodeURIComponent(q));
    must(r.status === 200, `${q} status ${r.status}`);
    must(r.body.length > 500, `${q} blank`);
  }
  const url = new URL("https://motdang.net/find?q=" + encodeURIComponent("ก"));
  const res = await fleetSearch(new Request(url.toString()), env, url, ctx, async () => { throw new Error("no dictionary"); });
  must(res.status === 200, "without the dictionary: " + res.status);
});

await t("6a a query that names a shelf puts the shelf first, and Lucky lands on it", async () => {
  const want = { massage: "/cm/massage/", food: "/cm/food/", wat: "/cm/wat/", map: "/map.html",
                 hotel: "/cm/hotel/", coffee: "/cm/food/cafe/", "นวด": "/cm/massage/", "วัด": "/cm/wat/" };
  for (const [q, path] of Object.entries(want)) {
    const l = await get("/find?q=" + encodeURIComponent(q) + "&lucky=1");
    must((l.h.get("location") || "").startsWith("https://motdang.net" + path), `${q} lucky → ${l.h.get("location")}`);
    const r = await get("/find?q=" + encodeURIComponent(q));
    must((urls(r.body)[0] || "").startsWith("https://motdang.net" + path), `${q} first row ${urls(r.body)[0]}`);
  }
  const cr = await get("/find?q=massage&lucky=1", CR);
  must(cr.h.get("location") === "https://motdang.net/cr/massage/index.html", "Chiang Rai reader → " + cr.h.get("location"));
});

await t("6b record-quality tag pages are out of the answer and out of Lucky", async () => {
  const bad = /\/tag\/(has-[a-z]+|multi-source|stub|no-contact|name-only|no-pin)--/;
  for (const q of ["massage", "sights", "นวด", "cafe"]) {
    const r = await get("/find?q=" + encodeURIComponent(q) + "&n=50");
    const u = urls(r.body).find((x) => bad.test(x));
    must(!u, `${q}: ${u}`);
  }
});

await t("6c best match starts near the reader", async () => {
  const r = await get("/find?q=khao+soi");
  const d = placeKm(r.body).slice(0, 5);
  must(d.length >= 3 && d.every((x) => x <= 20), "Chiang Mai: " + d.join(" "));
  const c = await get("/find?q=khao+soi", CR);
  const u = urls(c.body).filter((x) => /\/c[mr]\/p\//.test(x)).slice(0, 3);
  must(u.length && u.every((x) => x.includes("/cr/")), "Chiang Rai: " + u.join(" "));
});

await t("6d nearest orders the rows that answer the words, not every mention", async () => {
  for (const cf of [CF, CR]) {
    const r = await get("/find?q=khao+soi&sort=near", cf);
    const ts = titles(r.body).slice(0, 6);
    must(ts.every((x) => /khao ?soi|kao soi|ข้าวซอย|kho soi/i.test(x)), cf.city + ": " + ts.join(" | "));
  }
});

await t("7 a register name the dictionary would split is asked for whole", async () => {
  const r = await getR("/find?q=" + encodeURIComponent("รังมด"));
  const m = decodeURIComponent(r.h.get("x-fleet-match") || "");
  must(m.includes('"รังมด"') && !/^"รัง มด"$/.test(m), "match " + m);
  must(count(r.body) < 1000, "รังมด still floods: " + count(r.body));
  must(/motdang\.net\/anthill\//.test(r.body), "the Anthill card is missing");
});

await t("8 Thai queries over huge answers stay fast", async () => {
  const qs = ["ร้าน", "ม", "ข้าวซอย", "เชียงใหม่"];
  await warm(qs.map((q) => "/find?q=" + encodeURIComponent(q)));
  const slow = [];
  for (const q of qs) { const r = await get("/find?q=" + encodeURIComponent(q) + "&n=20"); if (r.ms >= 1200) slow.push(`${q} ${r.ms} ms`); }
  must(!slow.length, slow.join(", "));
});

await t("9 Lucky prefers a Mot Dang answer over an off-site card", async () => {
  for (const q of ["visa", "lucky"]) {
    const l = await getR("/find?q=" + q + "&lucky=1");
    must(/^https:\/\/motdang\.net\//.test(l.h.get("location") || ""), `${q} → ${l.h.get("location")}`);
  }
  const off = await getR("/find?q=" + encodeURIComponent("poplucky") + "&lucky=1");
  must(off.status === 302, "an off-site card still answers when nothing here does");
});

await t("12 the page carries the site's top bar: logo, toilets, map, calendar, every site, language", async () => {
  for (const p of ["/find", "/find?q=massage", "/find?q=zzqqxxyy", "/find?q=-"]) {
    const r = await get(p);
    for (const href of ["/toilets.html", "/map.html", "/calendar.html", "/sites/"]) {
      must(r.body.includes(`<a class="door" href="${href}"`), `${p}: no ${href}`);
    }
    must(/<a class="logo" href="\/">/.test(r.body), p + ": no logo");
    must(/data-lang="th">ไทย<\/button><button type="button" data-lang="en">EN</.test(r.body), p + ": no language switch");
  }
});

await t("a reader's query inside a script is escaped", async () => {
  const r = await get("/find?q=" + encodeURIComponent("massage </script><img src=x onerror=alert(1)>"));
  must(!/<\/script><img src=x/.test(r.body), "the query broke out of the script");
});

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
