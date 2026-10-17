/* The query engine, run under plain node against the index the build wrote.
 *
 * publish/api.js holds every rule about what a query MEANS — which filters AND
 * and which OR, what happens to a place with no pin, what "open now" does with
 * hours nobody holds. None of that involves Cloudflare, so none of it should
 * need a deploy to check. This runs the real engine over the real 13,000 rows
 * and asserts the behaviour a reader was promised on /api/.
 *
 *     node tests/test_api_worker.js
 *
 * Skips with a stated reason if docs/ has not been built, in the same spirit
 * as tests/test_api.py: a green tick over an unbuilt tree would be a lie.
 */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const INDEX = join(process.env.MD_DOCS || join(ROOT, "docs"), "api/v1/index.json");

if (!existsSync(INDEX)) {
  console.log(`SKIPPED — no ${INDEX}; build.py has not run`);
  process.exit(0);
}

const { queryPlaces, findPlace, slugCandidates, RESULT_KEYS, distanceM,
        parseOpenAt, isOpenAt, buildGrid, queryPlacesGrid } = await import(join(ROOT, "publish/api.js"));

const ix = JSON.parse(readFileSync(INDEX, "utf8"));
const q = (s, now) => queryPlaces(ix, new URLSearchParams(s), now);

let failures = 0;
function t(name, fn) {
  try {
    fn();
    console.log("  ok   " + name);
  } catch (e) {
    failures++;
    console.log("  FAIL " + name + "\n       " + e.message);
  }
}
const eq = (a, b, m) => { if (a !== b) throw new Error(`${m || ""} ${a} !== ${b}`); };
const ok = (c, m) => { if (!c) throw new Error(m || "expected true"); };

console.log(`api engine over ${ix.places.length} rows, built ${ix.generated}`);

/* ---------------------------------------------------------- the envelope */

t("the envelope carries every promised key and nothing else", () => {
  const r = q("limit=1");
  eq(JSON.stringify(Object.keys(r)),
     JSON.stringify(["schemaVersion", "generated", "query", "total", "count",
                     "limit", "offset", "results", "attribution", "licence", "terms"]));
});

t("a result carries exactly the frozen keys", () => {
  const r = q("limit=1").results[0];
  const want = RESULT_KEYS.filter((k) => k !== "distanceM");
  eq(JSON.stringify(Object.keys(r)), JSON.stringify(want));
});

t("distanceM appears only when a point was given", () => {
  ok(!("distanceM" in q("limit=1").results[0]), "distance without near=");
  ok("distanceM" in q("near=18.7883,98.9853&limit=1").results[0], "no distance with near=");
});

/* ------------------------------------------------------------- filtering */

t("cat is an OR over acceptable answers", () => {
  const r = q("cat=wat&limit=200");
  ok(r.total > 100, `only ${r.total} wats`);
  for (const x of r.results) ok(x.categories.includes("wat"), x.id);
  const both = q("cat=wat,massage&limit=1");
  ok(both.total > r.total, "two categories returned no more than one");
});

t("has is an AND over requirements", () => {
  const r = q("has=phone,hours&limit=50");
  for (const x of r.results) {
    ok(x.has.includes("phone") && x.has.includes("hours"), x.id);
  }
  ok(r.total < q("has=phone").total, "adding a requirement did not narrow anything");
});

t("a camelCase vocabulary value matches however it is typed", () => {
  // The ant bits are camel ("nameTh") and category keys are lower-kebab. A
  // reader cannot be expected to know which vocabulary is which case, and the
  // first draft silently returned zero for has=nameTh — indistinguishable
  // from "no such places", which is the worst kind of wrong answer.
  const want = q("has=nameTh&limit=1").total;
  ok(want > 0, "has=nameTh matched nothing");
  eq(q("has=nameth&limit=1").total, want, "lowercase spelling disagreed");
  eq(q("has=NAMETH&limit=1").total, want, "uppercase spelling disagreed");
  for (const x of q("has=nameTh&limit=20").results) ok(x.has.includes("nameTh"), x.id);
});

t("province narrows to one province", () => {
  for (const x of q("province=cr&limit=50").results) eq(x.province, "cr", x.id);
});

t("q ANDs its terms and matches Thai as typed", () => {
  const one = q("q=นวด&limit=1").total;
  const two = q("q=นวด แผนไทย&limit=1").total;
  ok(one > 0, "no Thai match at all");
  ok(two <= one, "adding a term widened the result");
});

t("min_ants never returns a thinner record than asked for", () => {
  for (const x of q("min_ants=6&limit=50").results) ok(x.antRank >= 6, x.id);
});

/* ------------------------------------------------------------- proximity */

t("near= respects the radius and sorts by it", () => {
  const r = q("near=18.7883,98.9853&radius=1000&limit=100");
  let prev = -1;
  for (const x of r.results) {
    ok(x.distanceM <= 1000, `${x.id} at ${x.distanceM}m is outside a 1 km radius`);
    ok(x.distanceM >= prev, "results are not in distance order");
    prev = x.distanceM;
  }
  ok(r.total > 0, "nothing within 1 km of Tha Phae Gate");
});

t("an unpinned place drops out of a near= query rather than being placed", () => {
  const unpinned = ix.places.filter((p) => p.lat == null).map((p) => p.id);
  ok(unpinned.length > 0, "no unpinned records — check the fixture, not the code");
  const got = new Set(q("near=18.7883,98.9853&radius=50000&limit=200").results.map((x) => x.id));
  for (const id of unpinned.slice(0, 200)) ok(!got.has(id), `${id} was placed`);
});

t("a wider radius never returns fewer places", () => {
  const near = "near=18.7883,98.9853";
  ok(q(`${near}&radius=3000&limit=1`).total >= q(`${near}&radius=500&limit=1`).total);
});

/* ----------------------------------------------------------------- hours */

t("openNow is null — not false — where nobody holds the hours", () => {
  const noHours = q("limit=200").results.filter((x) => x.hours === null);
  ok(noHours.length > 0, "every result had hours — widen the sample");
  for (const x of noHours) eq(x.openNow, null, `${x.id} was judged without hours`);
});

t("open_now excludes the unknown rather than calling it shut", () => {
  const r = q("open_now=1&limit=200");
  for (const x of r.results) {
    eq(x.openNow, true, `${x.id} is in an open_now result and is not open`);
    ok(x.hours !== null, `${x.id} is open with no hours`);
  }
  ok(r.total > 0, "nothing at all is open right now");
  ok(r.total <= ix.hours.withKnownHours, "more open than have hours");
});

t("open_at answers about a stated time, and beats open_now", () => {
  const sun = q("open_at=Su 03:30&limit=5").total;
  const sat = q("open_at=Sa 18:30&limit=5").total;
  ok(sat > sun, `Saturday evening (${sat}) should beat 3.30am Sunday (${sun})`);
  // Both given: the explicit time wins, so the answer must not move with now.
  const a = q("open_at=Sa 18:30&open_now=1&limit=5", new Date("2026-01-01T04:00:00Z")).total;
  const b = q("open_at=Sa 18:30&open_now=1&limit=5", new Date("2026-06-06T19:00:00Z")).total;
  eq(a, b, "an explicit time moved with the clock");
});

t("a malformed open_at is reported, not silently obeyed", () => {
  const r = q("open_at=whenever&limit=1");
  ok(r.query.open_at_ignored, "a bad time was swallowed");
  eq(r.total, q("limit=1").total, "a bad time still filtered");
});

t("the interval test is half-open at both ends of a day", () => {
  eq(isOpenAt([[[540, 1080]]], 0, 540), true, "opening minute");
  eq(isOpenAt([[[540, 1080]]], 0, 1079), true, "last minute");
  eq(isOpenAt([[[540, 1080]]], 0, 1080), false, "closing minute");
  eq(isOpenAt([[[540, 1080]]], null, 600), null, "no schedule is not a closed schedule");
  eq(parseOpenAt("Mo 00:00"), 0);
  eq(parseOpenAt("Su 23:59"), 6 * 1440 + 1439);
});

/* ------------------------------------------------------------ paging etc */

t("limit is capped, not refused", () => {
  const r = q("limit=99999");
  eq(r.limit, 200);
  ok(r.count <= 200);
});

t("offset walks the same ordering without repeating or skipping", () => {
  const a = q("cat=wat&sort=name&limit=10").results.map((x) => x.id);
  const b = q("cat=wat&sort=name&limit=10&offset=5").results.map((x) => x.id);
  eq(JSON.stringify(a.slice(5)), JSON.stringify(b.slice(0, 5)), "pages do not line up");
});

t("total counts matches, not the page", () => {
  const r = q("cat=wat&limit=3");
  eq(r.count, 3);
  ok(r.total > 3);
});

t("an impossible query is an empty answer, not an error", () => {
  const r = q("cat=wat&q=zzzzqqqnothing");
  eq(r.total, 0);
  eq(r.results.length, 0);
});

/* -------------------------------------------------------------- lookup */

t("a place is findable by id and by the slug in its own URL", () => {
  const counts = new Map();
  for (const p of ix.places) counts.set(p.slug, (counts.get(p.slug) || 0) + 1);
  const row = ix.places.find((p) => counts.get(p.slug) === 1);
  ok(findPlace(ix, row.id) === row, "id lookup failed");
  ok(findPlace(ix, row.slug) === row, "slug lookup failed");
  eq(findPlace(ix, "no-such-place"), null);
  eq(slugCandidates(ix, row.slug).length, 0, "a unique slug reported as shared");
});

t("a shared slug resolves to nothing, and offers both ids instead", () => {
  // 75 slugs are shared, every one of them the same shop entered in two
  // curated registers. Returning the first would be right nearly always,
  // which is what makes it the wrong habit: the day a shared slug is two
  // different places, a guessing lookup serves the wrong one in silence.
  const counts = new Map();
  for (const p of ix.places) counts.set(p.slug, (counts.get(p.slug) || 0) + 1);
  const shared = ix.places.find((p) => counts.get(p.slug) > 1);
  if (!shared) { console.log("       (no shared slugs in this build — nothing to check)"); return; }
  eq(findPlace(ix, shared.slug), null, "a shared slug was silently resolved");
  const cands = slugCandidates(ix, shared.slug);
  ok(cands.length > 1, "no candidates offered");
  for (const c of cands) ok(findPlace(ix, c.id) === c, "a candidate id does not resolve");
});

t("the lookup cache never leaks into the descriptor", () => {
  findPlace(ix, "warm the cache");
  const { places, schedules, ...head } = ix;
  ok(!("_byId" in head), "an internal Map rode along into the served descriptor");
  JSON.stringify(head);   // throws if anything unserialisable got attached
});

/* ------------------------------------------------------------ the city */

t("a city name in q is the province filter, never two more words (2026-09-10)", () => {
  // Nan, from River Tavern in Chiang Rai: "river tavern chiang rai" returned
  // nothing while "river tavern" returned the record. No row carried its own
  // province, so the city was two words no name contained.
  const r = q("q=river tavern chiang rai&limit=5");
  ok(r.total >= 1, "River Tavern not found with its city attached");
  eq(r.results[0].id, "cr-curated-river-tavern", "River Tavern is not the first row");
  for (const x of q("q=chiang rai&limit=50").results) eq(x.province, "cr", x.id);
  for (const x of q("q=ร้าน เชียงใหม่&limit=50").results) eq(x.province, "cm", x.id);
  // an explicit province= still wins over the words
  for (const x of q("q=khao soi chiang rai&province=cm&limit=20").results) eq(x.province, "cm", x.id);
  // both cities named: nothing lifted, and nothing thrown
  q("q=chiang mai chiang rai&limit=5");
});

t("the edge row carries its province words", () => {
  const cr = ix.places.find((p) => p.province === "cr");
  ok(cr.q.includes("เชียงราย") && cr.q.includes("chiang rai"), cr.id);
});

/* ------------------------------------------------------------ distances */

t("haversine agrees with a known city distance", () => {
  // Tha Phae Gate → Wat Phra Singh, ~1.4 km along the moat road.
  const d = distanceM(18.7883, 98.9930, 18.7889, 98.9817);
  ok(d > 1100 && d < 1400, `${Math.round(d)}m`);
});

/* ------------------------------------------------------------ the grid */

/* The box path must answer what the index walk answers, byte for byte: the
 * same total, the same rows in the same order, the same envelope. */
{
  const { meta, chunks } = buildGrid(ix);
  let reads = 0;
  const viaGrid = (s) => queryPlacesGrid(meta, async (c) => { reads++; return chunks[c]; },
                                         new URLSearchParams(s));
  const boxes = [
    "bbox=98.95,18.77,99.02,18.80&limit=120",           // the box measured slow 2026-10-11
    "bbox=98.9800,18.7850,98.9950,18.7950&limit=23",    // one ninth of an old-city view
    "bbox=98.95,18.77,99.02,18.80&limit=200&offset=150",
    "bbox=98.95,18.77,99.02,18.80&min_ants=3&limit=50",
    "bbox=98.95,18.77,99.02,18.80&province=cm",
    "bbox=98.95,18.77,99.02,18.80&province=cr",
    "bbox=98.95,18.77,99.02,18.80&province=zz",
    "bbox=99.70,19.80,99.95,20.05&limit=200",            // Chiang Rai town
    "bbox=97.0,17.0,101.0,21.0&limit=200",               // both provinces
    "bbox=97.0,17.0,101.0,21.0&offset=84000&limit=200",  // past the end
    "bbox=100.5,13.7,100.6,13.8",                        // Bangkok: nothing here
    "bbox=98.95,18.77,99.02,18.80&sort=relevance&limit=40",
    "bbox=98.95,18.77,99.02,18.80&q=chiang mai&limit=40",
  ];
  for (const s of boxes) {
    const want = JSON.stringify(q(s));
    const got = JSON.stringify(await viaGrid(s));
    t("grid = index walk: " + s, () => eq(got, want, `${got.length} vs ${want.length} bytes`));
  }
  /* 2026-10-13: the grid put ground truth first and the index walk did not, so
   * a Chiang Mai box gave different rows on each path. The built index above
   * only catches that when it carries groundTruth, so this one is made to:
   * ground truth against ant rank, ties on both, Thai names that sort
   * differently from their code points, and a row with no groundTruth. */
  {
    const names = ["ไก่ย่าง", "กาแฟ", "เกาะ", "ข้าวซอย", "ก้อน", "Zebra", "กา", "ฃ", "ไข่", "ก"];
    const places = names.map((name, k) => ({
      id: "cm-t-" + k, province: "cm", slug: "t-" + k, name, cat: [], sub: [],
      lat: 18.79 + k * 1e-4, lng: 98.99 + k * 1e-4, antRank: [7, 3, 3, 6, 3, 9, 3, 6, 3, 5][k],
      ...(k === 9 ? {} : { groundTruth: [1, 22, 22, 21, 0, 1, 22, 21, 22, 0][k] }),
    }));
    const tix = { ...ix, places };
    const { meta: tm, chunks: tc } = buildGrid(tix);
    for (const s of ["bbox=98.98,18.78,99.01,18.80", "bbox=98.98,18.78,99.01,18.80&limit=3&offset=2"]) {
      const want = queryPlaces(tix, new URLSearchParams(s));
      const got = await queryPlacesGrid(tm, async (c) => tc[c], new URLSearchParams(s));
      const ids = (r) => r.results.map((x) => x.id).join(" ");
      t("grid = index walk with ground truth and Thai ties: " + s, () => {
        eq(ids(got), ids(want), "rows:");
        eq(JSON.stringify(got), JSON.stringify(want), "envelope:");
      });
    }
    t("the default order is ground truth, then ant rank, then Thai name", () => eq(
      queryPlaces(tix, new URLSearchParams("bbox=98.98,18.78,99.01,18.80")).results.map((r) => r.name).join(" "),
      "กา กาแฟ เกาะ ไข่ ข้าวซอย ฃ Zebra ไก่ย่าง ก ก้อน"));
  }
  reads = 0;
  await viaGrid("bbox=98.9800,18.7850,98.9950,18.7950&limit=23");
  t(`one ninth of a view reads ${reads} of ${chunks.length} chunks`, () => ok(reads <= 23 && reads < chunks.length / 10));
  for (const s of ["bbox=98.95,18.77,99.02,18.80&cat=food", "bbox=98.95,18.77,99.02,18.80&q=coffee",
                   "bbox=98.95,18.77,99.02,18.80&near=18.79,98.99", "bbox=98.95,18.77,99.02,18.80&open_now=1",
                   "bbox=98.95,18.77,99.02,18.80&sort=name", "q=coffee", "bbox=1,2"]) {
    const got = await viaGrid(s);
    t("not a grid question, left to the index: " + s, () => eq(got, null));
  }
}

console.log(failures ? `\n${failures} FAILED` : "\nall green");
process.exit(failures ? 1 : 0);
