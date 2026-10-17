/* People's own pages in /find (publish/ownfind.js, joined in publish/fleetsearch.js).
 *
 *     node tests/test_ownfind.js
 *
 * The page maker's /api/find is replaced by a function here; nothing is
 * fetched. The first half reads the module alone. The second runs the real
 * handler over the local twin of the index (python3 fleetsearch/load.py --sql
 * --local) and is skipped with a stated reason when the twin is not there. */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const own = await import(join(ROOT, "publish/ownfind.js"));
const fs = await import(join(ROOT, "publish/fleetsearch.js"));
const feed = JSON.parse(readFileSync(join(ROOT, "tests/fixtures/own_pages_feed.json"), "utf8"));
const PAGE = Object.fromEntries(feed.pages.map((p) => [p.name, p]));

let failures = 0;
async function t(name, fn) {
  try { await fn(); console.log("  ok   " + name); }
  catch (e) { failures++; console.log("  FAIL " + name + "\n       " + e.message); }
}
const must = (c, m) => { if (!c) throw new Error(m); };
const same = (a, b, m) => must(JSON.stringify(a) === JSON.stringify(b), `${m}: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`);
const reply = (body, status = 200) => async () => ({ ok: status === 200, status, json: async () => body });
const HAS = fs.default.HAS;

await t("asked only for plain words on page one of a best-match answer", () => {
  const base = { q: "กาแฟ", adv: false, boolQ: false, lucky: false, page: 1, sort: "rank", site: "", kind: "", sec: "", has: [], from: "", to: "" };
  must(own.ownWanted(base), "plain words");
  must(own.ownWanted({ ...base, sort: "near" }), "nearest");
  for (const [k, v] of Object.entries({ page: 2, sort: "az", site: "wichaa", kind: "list", sec: "x", has: ["photo"], from: "2026-01-01", adv: true, boolQ: true, lucky: true, q: "k" })) {
    must(!own.ownWanted({ ...base, [k]: v }), `not for ${k}=${v}`);
  }
});

await t("the address carries the words, and a position rounded to a kilometre", () => {
  must(own.ownUrl("https://x/api/find", "a b", null) === "https://x/api/find?q=a%20b", "no pin");
  must(own.ownUrl("https://x/api/find", "k", { lat: 18.79038, lon: 98.98468 }).endsWith("&lat=18.79&lng=98.98"), "pin");
});

await t("a good answer is trimmed to pages on the page maker's host", async () => {
  const doc = { results: [PAGE["example-baan-lung-mee"], { ...PAGE["example-tha-sai-shop"], url: "https://evil.example/x" },
                          { ...PAGE["example-plumber-no-pin"], url: "javascript:alert(1)" }, null, "x"] };
  const got = await own.ownPagesSoon({}, "q", null, { fetch: reply(doc) });
  same(got.map((p) => p.name), ["example-baan-lung-mee"], "only the page on the host");
});

await t("any fault is an empty list: status, bad body, throw, nothing to call", async () => {
  same(await own.ownPagesSoon({}, "q", null, { fetch: reply({}, 500) }), [], "500");
  same(await own.ownPagesSoon({}, "q", null, { fetch: reply({ results: "no" }) }), [], "body");
  same(await own.ownPagesSoon({}, "q", null, { fetch: async () => { throw new Error("net"); } }), [], "throw");
  same(await own.ownPagesSoon({}, "q", null, { fetch: async () => ({ ok: true, json: async () => { throw new Error("json"); } }) }), [], "json");
  same(await own.ownPagesSoon({ OWN_FIND_URL: "" }, "q", null, { fetch: () => { throw new Error("called"); } }), [], "switched off");
});

await t("a slow answer is given up on at the budget", async () => {
  let aborted = false;
  const slow = (u, init) => new Promise((_, rej) => { init.signal.addEventListener("abort", () => { aborted = true; rej(new Error("abort")); }); });
  const t0 = Date.now();
  const got = await own.ownPagesSoon({}, "q", null, { fetch: slow, budget: 60 });
  same(got, [], "empty");
  must(Date.now() - t0 < 300, `waited ${Date.now() - t0} ms`);
  must(aborted, "the request was not abandoned");
});

await t("hours become minute-of-week intervals on Chiang Mai's clock, or none", () => {
  const iv = own.schedOf(PAGE["example-baan-lung-mee"].hours);
  same(iv[0], [480, 1020], "Monday 08:00-17:00");
  same(iv[5], [7740, 8040], "Saturday 09:00-14:00");
  same(iv[6], [8160, 8340], "Saturday 16:00-19:00");
  same(own.schedOf({ on: true, always: true }), [[0, 10080]], "always");
  same(own.schedOf({ on: true, tz: "Europe/Lisbon", week: [[["09:00", "17:00"]]] }), null, "another clock gets no lamp");
  same(own.schedOf({ on: false, week: [[["09:00", "17:00"]]] }), null, "switched off");
  same(own.schedOf({ on: true, tz: "Asia/Bangkok", week: [[["22:00", "02:00"]]] }), [[1320, 1560]], "past midnight");
});

const ctx = { HAS, today: "2026-10-13" };
await t("a live page becomes a row the one renderer can draw", () => {
  const r = own.ownRow({ ...PAGE["example-baan-lung-mee"], score: 4 }, ctx);
  must(r.site === "sites" && r.host === "sites.motdang.net" && r.own, "site");
  must(r.kind === "place" && r.lat === 18.7885, "kind and pin");
  must(JSON.parse(r.rich).ways.includes("line"), "ways");
  must((r.has & HAS.contact) && (r.has & HAS.hours) && (r.has & HAS.photo), "has bits " + r.has);
  must(r.thumbUrl.startsWith("https://sites.motdang.net/img/"), "cover");
  const e = own.ownRow(PAGE["example-night-market"], ctx);
  must(e.kind === "page" && JSON.parse(e.rich).ev[0].d === "2026-10-20" && (e.has & HAS.events), "event");
  const n = own.ownRow(PAGE["example-plumber-no-pin"], ctx);
  must(n.lat === null && n.lon === null, "no pin stays no pin");
});

await t("the merge skips what the index holds, adds at most three after the first two, and brings its lamps", () => {
  const rows = [1, 2, 3, 4].map((i) => ({ id: i, url: `https://motdang.net/p${i}`, site: "motdang" }));
  rows.push({ id: 5, url: PAGE["example-baan-lung-mee"].url, site: "sites" });
  const aux = { scheds: new Map([[7, [[0, 10]]]]), secEn: {} };
  const live = Object.values(PAGE).map((p, i) => ({ ...p, score: 10 - i }));
  const m = own.mergeOwn(rows, live, ctx, aux);
  must(m.added === 3, "added " + m.added);
  must(m.rows.length === rows.length + 3, "length");
  must(m.rows.filter((r) => r.url === PAGE["example-baan-lung-mee"].url).length === 1, "the indexed copy is not shown twice");
  same(m.rows.slice(0, 2).map((r) => r.id), [1, 2], "the index keeps its first two");
  must(m.rows[2].own && m.rows[3].own && m.rows[4].own, "live pages follow");
  const lamp = m.rows.find((r) => r.sk != null && r.sk < 0);
  must(lamp && m.aux.scheds.get(lamp.sk).length > 0, "lamp for a live page");
  must(m.aux.scheds.get(7)[0][1] === 10, "the index's own lamps still answer");
  must(!aux.scheds.has(lamp.sk), "the shared lamp table is not touched");
  const none = own.mergeOwn(rows, [PAGE["example-baan-lung-mee"]], ctx, aux);
  must(none.added === 0 && none.rows === rows, "nothing new, nothing changed");
});

await t("the row mark is on the page maker's site and nowhere else", () => {
  must(/class="own"[^>]*>.*own page/.test(fs.ownMark({ site: "sites" })), "mark");
  must(fs.ownMark({ site: "motdang" }) === "", "no mark");
  const th = fs.thumbHtml({ thumb: "", thumbUrl: "https://sites.motdang.net/img/a.webp", url: "https://sites.motdang.net/a", rich: "{}" });
  must(th.includes('src="https://sites.motdang.net/img/a.webp"'), "live cover as the picture");
});

/* ------------------------------------------------------ the handler, over the twin */
const TWIN = join(ROOT, "cache/fleetsearch/fleet.sqlite");
const dataFile = (n) => [join(ROOT, "docs/data", n), join(ROOT, "data", n)].find(existsSync);
if (!existsSync(TWIN) || !dataFile("search_thesaurus.json") || !dataFile("search_segdict.txt")) {
  console.log("  skip the handler tests - no local twin (python3 fleetsearch/load.py --sql --local) or dictionary");
} else {
  const { DatabaseSync } = await import("node:sqlite");
  const SEARCHCORE = (await import(join(ROOT, "publish/searchcore.js"))).default;
  const groups = JSON.parse(readFileSync(dataFile("search_thesaurus.json"), "utf8")).groups;
  const segdict = readFileSync(dataFile("search_segdict.txt"), "utf8").split("\n").filter((l) => l && l[0] !== "#");
  const core = new SEARCHCORE.SearchCore(groups, segdict);
  const db = new DatabaseSync(TWIN, { readOnly: true });
  const SEARCH = {
    prepare(text) { return { text, binds: [], bind(...b) { this.binds = b; return this; }, async all() { return { results: db.prepare(this.text).all(...this.binds) }; } }; },
    async batch(stmts) { return stmts.map((s) => ({ results: db.prepare(s.text).all(...s.binds) })); },
  };
  const CF = { city: "Chiang Mai", latitude: "18.79038", longitude: "98.98468", timezone: "Asia/Bangkok", country: "TH" };
  const realFetch = globalThis.fetch;
  let calls = [];
  const stub = (fn) => { globalThis.fetch = async (u, init) => { calls.push(String(u)); return fn(u, init); }; };
  async function get(path, env) {
    const url = new URL("https://motdang.net" + path);
    const req = new Request(url.toString());
    Object.defineProperty(req, "cf", { value: CF });
    const res = await fs.fleetSearch(req, { SEARCH, ...(env || {}) }, url, { waitUntil() {} }, async () => core);
    return { status: res.status, body: res.status === 302 ? "" : await res.text() };
  }
  const urls = (b) => Array.from(b.matchAll(/<a class="t" href="([^"]+)"/g)).map((m) => m[1]);
  const LIVE = { results: [{ ...PAGE["example-baan-lung-mee"], score: 5 }, { ...PAGE["example-tha-sai-shop"], score: 3 }] };

  await t("a live page joins page one, marked, after the index's first two", async () => {
    calls = []; stub(reply(LIVE));
    const quiet = await get("/find?q=coffee&sort=rank", { OWN_FIND_URL: "" });
    const r = await get("/find?q=coffee");
    globalThis.fetch = realFetch;
    must(calls.length === 1 && calls[0].startsWith("https://sites.motdang.net/api/find?q=coffee&lat=18.79&lng=98.98"), "call " + calls);
    const u = urls(r.body), q = urls(quiet.body);
    must(u.includes(PAGE["example-baan-lung-mee"].url), "live page missing");
    same(u.slice(0, 2), q.slice(0, 2), "the first two are the index's");
    must(/class="own"/.test(r.body), "no own-page mark");
    must(u.length === q.length + 2, `${u.length} vs ${q.length}`);
    must(/พบ [\d,]+ หน้า/.test(r.body), "count line");
  });

  await t("the same words as JSON carry own_page on those rows", async () => {
    stub(reply(LIVE));
    const r = await get("/find?q=coffee&fmt=json");
    globalThis.fetch = realFetch;
    const doc = JSON.parse(r.body);
    const hit = doc.results.find((x) => x.url === PAGE["example-baan-lung-mee"].url);
    must(hit && hit.own_page === true && hit.site === "sites", "row");
    must(hit.open_now === true || hit.open_now === false, "a lamp for a page with hours");
    must(hit.thumb === PAGE["example-baan-lung-mee"].cover, "cover as thumb");
    must(doc.results.filter((x) => x.own_page).length === 2, "two live pages");
  });

  await t("a page maker that fails leaves the answer exactly as it was", async () => {
    const quiet = await get("/find?q=coffee", { OWN_FIND_URL: "" });
    for (const fn of [reply({}, 503), async () => { throw new Error("down"); }, reply({ results: [] }), () => new Promise(() => {})]) {
      stub(fn);
      const t0 = Date.now();
      const r = await get("/find?q=coffee");
      globalThis.fetch = realFetch;
      must(Date.now() - t0 < 2500, "waited " + (Date.now() - t0));
      same(urls(r.body), urls(quiet.body), "same results");
      must(!/class="own"/.test(r.body), "mark without a page");
    }
  });

  await t("it is not asked on page two, a sort, a site filter or the boolean door", async () => {
    calls = []; stub(reply(LIVE));
    for (const path of ["/find?q=coffee&p=2", "/find?q=coffee&sort=az", "/find?q=coffee&site=motdang", "/find?q=coffee&kind=place",
                        "/find?adv=1&q=coffee", "/find?q=coffee&lucky=1", "/find?q=coffee+AND+shop", "/find?q=coffee&has=photo"]) {
      await get(path);
    }
    globalThis.fetch = realFetch;
    same(calls, [], "calls made");
  });

  await t("a page maker that answers alone still gives a page for words the index lacks", async () => {
    stub(reply({ results: [{ ...PAGE["example-baan-lung-mee"], title: "บ้านลุงหมี · Uncle Bear's Home", score: 9 }] }));
    const r = await get("/find?q=qqxqqzz");
    globalThis.fetch = realFetch;
    must(r.status === 200, "status " + r.status);
    must(urls(r.body).includes(PAGE["example-baan-lung-mee"].url), "live page missing from an answer of nothing else");
  });
}

console.log(failures ? `${failures} FAILED` : "all passed");
process.exit(failures ? 1 : 0);
