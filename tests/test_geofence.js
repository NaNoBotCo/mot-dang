/* What the page says about where you are, run under plain node.
 *
 * publish/worker.js fills meta[name=md-where] on every page and, on a page
 * that publishes its own coordinates, writes a line under the heading saying
 * how far away it is. The streaming rewrite itself needs Cloudflare's
 * HTMLRewriter and is checked live after a deploy; what is checked here is
 * every rule that decides WHAT that line says — the arithmetic, the compass,
 * the rounding, and the one that keeps a directory page from claiming to
 * stand somewhere.
 *
 *     node tests/test_geofence.js
 */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const { hereLine, collectGeo, whereLine } = await import(join(ROOT, "publish/worker.js"));

let failures = 0;
function t(name, fn) {
  try { fn(); console.log("  ok   " + name); }
  catch (e) { failures++; console.log("  FAIL " + name + "\n       " + e.message); }
}
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what || "value"}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const must = (c, m) => { if (!c) throw new Error(m); };

/* Cloudflare's guess for a real connection on 2026-09-21, and the house it was
 * actually sent from: 6.4 km apart, which is why a coarse position is never
 * given a decimal. */
const EDGE = { lat: 18.79038, lon: 98.98468 };
const HOUSE = { lat: 18.789, lon: 99.045 };
const THAPHAE = { lat: 18.78787, lon: 98.99329 };

t("the arithmetic agrees with the map", () => {
  const d = hereLine(EDGE, HOUSE).m;
  must(Math.abs(d - 6370) < 120, `${Math.round(d)} m, expected about 6,370`);
  must(Math.abs(hereLine(EDGE, THAPHAE).m - 949) < 20, Math.round(hereLine(EDGE, THAPHAE).m));
});

t("a degree of longitude is not a degree of latitude", () => {
  const north = hereLine(EDGE, { lat: EDGE.lat + 0.01, lon: EDGE.lon }).m;
  const east = hereLine(EDGE, { lat: EDGE.lat, lon: EDGE.lon + 0.01 }).m;
  must(north > east, `north ${Math.round(north)} should exceed east ${Math.round(east)}`);
  must(Math.abs(north - 1113) < 5 && Math.abs(east - 1054) < 5, `${north} ${east}`);
});

t("the compass names the direction", () => {
  eq(hereLine(EDGE, HOUSE).dir[1], "E");
  eq(hereLine(EDGE, { lat: 19.9, lon: EDGE.lon }).dir[1], "N");
  eq(hereLine(EDGE, { lat: 17.9, lon: EDGE.lon }).dir[1], "S");
  eq(hereLine(EDGE, { lat: EDGE.lat, lon: 97.9 }).dir[1], "W");
  eq(hereLine(EDGE, { lat: EDGE.lat + 0.09, lon: EDGE.lon + 0.09 }).dir[1], "NE");
});

t("a coarse position is never given a decimal", () => {
  for (const to of [HOUSE, THAPHAE, { lat: 19.9, lon: 99.8 }, { lat: 13.75, lon: 100.5 }]) {
    const [th, en] = hereLine(EDGE, to).far;
    must(/^(ใกล้ๆ|~\d+ กม\.)$/.test(th), "thai: " + th);
    must(/^(nearby|~\d+ km)$/.test(en), "english: " + en);
  }
});

t("under a kilometre and a half is 'nearby', not a number", () => {
  eq(hereLine(EDGE, THAPHAE).far[1], "nearby");
  eq(hereLine(EDGE, HOUSE).far[1], "~6 km");
  /* Bangkok. The flat approximation is within half a percent of the
     great circle over this distance (583 km against 585), and the label is
     rounded to the kilometre anyway. */
  eq(hereLine(EDGE, { lat: 13.75, lon: 100.5 }).far[1], "~583 km");
});

t("standing on the spot has no direction and does not divide by zero", () => {
  const line = hereLine(EDGE, { ...EDGE });
  eq(line.m, 0);
  eq(line.dir, null);
  eq(line.far[1], "nearby");
});

t("a place page's own coordinate is found", () => {
  const out = [];
  collectGeo({ "@type": "Restaurant", name: "Aroy Garden",
               geo: { "@type": "GeoCoordinates", latitude: 18.737294, longitude: 99.1264296 } }, out);
  eq(out.length, 1);
  eq(out[0].lat, 18.737294);
  eq(out[0].lon, 99.12643);
});

t("a directory page carrying many coordinates claims none of them", () => {
  const out = [];
  collectGeo({ "@type": "ItemList", itemListElement: [
    { item: { geo: { latitude: 18.1, longitude: 99.1 } } },
    { item: { geo: { latitude: 18.2, longitude: 99.2 } } }] }, out);
  const uniq = new Set(out.map((g) => `${g.lat},${g.lon}`));
  must(uniq.size === 2, "the page would have picked one of " + uniq.size);
});

t("the same coordinate repeated is still one place", () => {
  const out = [];
  collectGeo([{ geo: { latitude: 18.1, longitude: 99.1 } },
              { geo: { latitude: 18.1, longitude: 99.1 } }], out);
  eq(new Set(out.map((g) => `${g.lat},${g.lon}`)).size, 1);
});

t("nonsense coordinates are not coordinates", () => {
  const out = [];
  collectGeo({ geo: { latitude: "", longitude: "" } }, out);
  collectGeo({ geo: { latitude: 0, longitude: 0 } }, out);
  collectGeo({ geo: { latitude: 91, longitude: 10 } }, out);
  collectGeo({ geo: { latitude: "x", longitude: "y" } }, out);
  eq(out.length, 0);
});

t("a coordinate written as a string still counts", () => {
  const out = [];
  collectGeo({ geo: { latitude: "18.7373", longitude: "99.1264" } }, out);
  eq(out.length, 1);
});

t("the Worker draws the line from the same rules the search does", async () => {
  const fs = await import(join(ROOT, "publish/fleetsearch.js"));
  const a = hereLine(EDGE, HOUSE);
  must(Math.abs(a.m - fs.metres(EDGE, { lat: HOUSE.lat, lon: HOUSE.lon })) < 1, "the distances differ");
  eq(a.dir[1], fs.bearing(EDGE, HOUSE)[1]);
  eq(a.far[1], fs.farLabel(a.m, false)[1]);
});

t("the big hub pages are not walked for geo, but still learn they are lists", () => {
  const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");
  must(/GEO_MAX_BYTES = 2_000_000/.test(src), "no size guard");
  /* The geo PARSE is still gated on size; the cheap ItemList scan is not, so a
     shelf too big to walk (cm/food is 2.4 MB) still draws its city line. */
  must(/parseGeo = !\(size > GEO_MAX_BYTES\)/.test(src), "the size guard is gone");
  must(/if \(!parseGeo \|\| pin === false\) return/.test(src), "the guard is not applied to the parse");
  must(/t\.text\.includes\("ItemList"\)/.test(src), "the ItemList scan is missing");
  must(/withWhere\(res, request, obj\.size\)/.test(src), "the size is not passed in");
  must(/LD_MAX_CHARS/.test(src), "no cap on the JSON-LD a page may hold open");
});

/* The line the reader gets, decided without HTMLRewriter. Cloudflare's guess
   on 2026-09-21 stood at this city; the house is the page's own coordinate. */
const CF = { city: "Chiang Mai", latitude: 18.79038, longitude: 98.98468 };
const FROM = { lat: CF.latitude, lon: CF.longitude };

t("a shelf now draws the reader's city — the newly-covered surface", () => {
  const line = whereLine({ known: true, pin: null, isList: true, from: FROM, cf: CF });
  must(line, "the ItemList surface drew no line");
  must(/data-md-where-city/.test(line), "the shelf line is not marked");
  must(line.includes("Chiang Mai"), "the city is not named");
  must(/network's rough position/.test(line), "the guess is not named as a guess");
  must(!/\d+\.\d/.test(line.replace(/font-size:[^;"]*/g, "")), "a coarse guess must carry no decimal");
  must(/href="\/find"/.test(line), "the precise-fix opt-in is not reachable");
});

t("no line anywhere when Cloudflare handed over no position", () => {
  eq(whereLine({ known: false, pin: null, isList: true, from: {}, cf: {} }), "", "shelf, cf absent");
  eq(whereLine({ known: false, pin: { lat: 18.7, lon: 99 }, isList: false, from: {}, cf: {} }), "", "place, cf absent");
});

t("a single place still draws its distance, not a city", () => {
  const line = whereLine({ known: true, pin: { lat: 18.789, lon: 99.045 }, isList: false, from: FROM, cf: CF });
  must(/md-here/.test(line) && !/data-md-where-city/.test(line), "a place drew the shelf line");
  must(/~6 km/.test(line), "the distance to the place is not drawn");
});

t("a page that is neither a place nor a list keeps silence", () => {
  eq(whereLine({ known: true, pin: null, isList: false, from: FROM, cf: CF }), "",
     "the front page or an article got a line it should not");
});

t("every page gets the meta, not only the front one", () => {
  const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");
  must(/ext\(key\) === "html" \? withWhere/.test(src), "the rewrite is still keyed to one file");
  must(!/key === "index\.html" \? withWhere/.test(src), "the old front-page-only rule is still there");
});

t("the meta is written when the page has none", () => {
  const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");
  must(/metaSeen = true/.test(src), "nothing notices whether the page carried one");
  must(/onEndTag/.test(src) && /end\.before\(`<meta name="md-where"/.test(src),
       "a page without the tag gets nothing");
  /* The front page rebuilt on 2026-09-21 dropped the tag the 2026-09-19 page
     had; filling only would have left the geofence with no position. */
  const live = join(ROOT, "docs/index.html");
  if (existsSync(live)) {
    const html = readFileSync(live, "utf8");
    if (!/md-where/.test(html)) {
      must(/end\.before/.test(src), "the live front page carries no tag and none is written");
    }
  }
});

t("a page carrying a reader's city is not left cacheable by a shared cache", () => {
  const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");
  must(/out\.headers\.set\("cache-control", "private/.test(src), "no private marking");
});

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
