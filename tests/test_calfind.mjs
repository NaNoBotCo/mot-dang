/* The calendar inside the search (publish/calfind.js):  node --test tests/test_calfind.mjs */
import test from "node:test";
import assert from "node:assert/strict";
import { readQuery, windowFor, calMatch, calHtml } from "../publish/calfind.js";

const ev = (k, t, s, more = {}) => ({ k, t, s, e: null, ad: false, v: "", c: "other", have: [], n: 0, ...more });
const DATA = {
  cats: [{ k: "dance", th: "เต้นรำ", en: "Dance" }, { k: "music", th: "ดนตรี", en: "Music" }, { k: "faith", th: "วัดและศรัทธา", en: "Faith" }],
  events: [
    ev("tango", "Tango", "2026-10-01 20:00:00", { v: "One Nimman", c: "dance", la: 18.8, lo: 98.97, vu: "cm/p/one-nimman.html" }),
    ev("pub-quiz", "Pub quiz", "2026-10-01 20:00:00", { v: "UN Irish Pub" }),
    ev("morning-yoga", "Morning yoga", "2026-10-01 07:00:00"),
    ev("blues", "The Bottom Blues live", "2026-10-01 00:00:00", { c: "music" }),
    ev("jazz", "Jazz night", "2026-10-02 19:00:00", { c: "music" }),
    ev("market", "Jing Jai market", "2026-10-03 06:30:00"),
    ev("fair", "Temple fair", "2026-10-04 10:00:00", { c: "faith" }),
    ev("tennis", "Tennis, all October", "2026-10-01 00:00:00", { e: "2026-10-31", ad: true }),
  ],
};
const NOW = Date.parse("2026-10-01T18:30:00+07:00");          // a Thursday evening

test("when- and events-words come out of the query, in both scripts", () => {
  assert.deepEqual(readQuery("events"), { when: "", asked: true, toks: [] });
  assert.deepEqual(readQuery("today"), { when: "today", asked: false, toks: [] });
  assert.deepEqual(readQuery("งานวันนี้"), { when: "today", asked: true, toks: [] });
  assert.deepEqual(readQuery("ดนตรีคืนนี้"), { when: "tonight", asked: false, toks: ["ดนตรี"] });
  assert.equal(readQuery("what's on this weekend").when, "weekend");
  assert.equal(readQuery("events saturday").when, "d6");
});

test("งาน counts at the start of a run, not inside ทำงาน or สำนักงาน", () => {
  assert.equal(readQuery("งานดนตรี").asked, true);
  assert.equal(readQuery("สำนักงาน").asked, false);
  assert.equal(calMatch("สำนักงาน", DATA, NOW), null);
  assert.equal(calMatch("ทำงาน", DATA, NOW), null);
});

test("today is what is still ahead today, timed rows first", () => {
  const m = calMatch("today", DATA, NOW);
  assert.deepEqual(m.events.map((e) => e.k), ["tango", "pub-quiz", "blues", "tennis"]);
});

test("the weekend from a Thursday is Saturday and Sunday", () => {
  const [a, b] = windowFor("weekend", NOW);
  assert.equal(new Date(a + 7 * 3600e3).toISOString().slice(0, 16), "2026-10-03T00:00");
  assert.equal(new Date(b + 7 * 3600e3).toISOString().slice(0, 16), "2026-10-05T00:00");
  assert.deepEqual(calMatch("weekend", DATA, NOW).events.map((e) => e.k), ["market", "fair", "tennis"]);
});

test("a title or venue answers without an events-word; a kind needs one", () => {
  assert.deepEqual(calMatch("tango", DATA, NOW).events.map((e) => e.k), ["tango"]);
  assert.deepEqual(calMatch("one nimman", DATA, NOW).events.map((e) => e.k), ["tango"]);
  assert.equal(calMatch("dance", DATA, NOW), null);
  assert.deepEqual(calMatch("dance events", DATA, NOW).events.map((e) => e.k), ["tango"]);
  assert.deepEqual(calMatch("งานวัด", DATA, NOW).events.map((e) => e.k), ["fair"]);
});

test("words the calendar does not hold leave the page alone, unless the calendar was asked for", () => {
  assert.equal(calMatch("khao soi", DATA, NOW), null);
  assert.equal(calMatch("today khao soi", DATA, NOW), null);
  assert.equal(calMatch("khao soi events", DATA, NOW).total, 0);
});

test("rows lead to the calendar and to the venue's pin on the map", () => {
  const h = calHtml(calMatch("tango", DATA, NOW), NOW);
  assert.match(h, /href="\/#ev=tango"/);
  assert.match(h, /href="\/map\.html#16\/18\.8\/98\.97\/\/ev=1&pin=cm:one-nimman"/);
  assert.match(h, /href="\/cm\/p\/one-nimman\.html"/);
  assert.doesNotMatch(h, /<script/);
});
