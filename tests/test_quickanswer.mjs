/* Quick answers in the search (publish/quickanswer.js):  node --test tests/test_quickanswer.mjs */
import test from "node:test";
import assert from "node:assert/strict";
import { quickMatch, mdCalc, quickHtml, quickJson, convert, mdSpark, trMatch } from "../publish/quickanswer.js";

const near = (a, b, e = 1e-9) => assert.ok(Math.abs(a - b) <= e * Math.max(1, Math.abs(b)), `${a} ≉ ${b}`);

test("the calculator reads sums the way Google does", () => {
  near(mdCalc("15% of 2000"), 300);
  near(mdCalc("2000 + 7%"), 2140);
  near(mdCalc("2000 - 10%"), 1800);
  near(mdCalc("2000*7%"), 140);
  near(mdCalc("(3+4)^2"), 49);
  near(mdCalc("2^3^2"), 512);
  near(mdCalc("-2^2"), -4);
  near(mdCalc("12×(3+4)"), 84);
  near(mdCalc("10 ÷ 4"), 2.5);
  near(mdCalc("√(16)+1"), 5);
  near(mdCalc("2π"), 2 * Math.PI);
  near(mdCalc("5!"), 120);
  near(mdCalc("1,000,000/4"), 250000);
  near(mdCalc("๑๐๐+๒๐๐"), 300);
  near(mdCalc("3 x 4"), 12);
  assert.equal(mdCalc("1/0"), null);
  assert.equal(mdCalc("2+"), null);
  assert.equal(mdCalc("alert(1)"), null);
});

test("searches that look like sums but are not stay with the pages", () => {
  for (const q of ["7-11", "24/7", "869/77", "053-160611", "+66 81 234 5678", "2026-10-14", "4x4", "massage -spa",
                   "dollar", "baht bus", "dollar shop", "foot rub", "5 km", "100 kg", "งานวันนี้", "soi 5", "3.5",
                   "thai massage", "menu in english", "ร้านอาหารจีน", "เรียนภาษาจีน", "โรงเรียนสอนภาษาอังกฤษ",
                   "รับแปลภาษาอังกฤษ", "english to thai", "sabai meaning"]) {
    assert.equal(quickMatch(q), null, q);
  }
});

test("what a reader types reaches the right box", () => {
  const k = (q) => { const m = quickMatch(q); return m && [m.kind, m.amt, m.from, m.to].filter((x) => x !== undefined).join(" "); };
  assert.equal(k("25000 usd to thb"), "fx 25000 USD THB");
  assert.equal(k("dollars to baht"), "fx 1 USD THB");
  assert.equal(k("$100"), "fx 100 USD THB");
  assert.equal(k("100 บาท เป็น ดอลลาร์"), "fx 100 THB USD");
  assert.equal(k("500 บาท เป็น เยน"), "fx 500 THB JPY");
  assert.equal(k("ค่าเงินบาท"), "fx 1 THB USD");
  assert.equal(k("usdthb"), "fx 1 USD THB");
  assert.equal(k("100000 ကျပ် to baht"), "fx 100000 MMK THB");
  assert.equal(k("แลกเงิน"), "fx 1 USD THB");
  assert.equal(k("100 pounds"), "fx 100 GBP THB");
  assert.equal(k("1 pound to kg"), "unit 1 lb kg");
  assert.equal(k("5 miles to km"), "unit 5 mi km");
  assert.equal(k("30c"), "unit 30 c f");
  assert.equal(k("2 ไร่"), "unit 2 rai m2");
  assert.equal(k("1 rai to acre"), "unit 1 rai acre");
  assert.equal(k("1 บาททอง"), "unit 1 bg g");
  assert.equal(k("calculator"), "calc");
  assert.equal(quickMatch("what is 12*12").value, 144);
});

test("conversions", () => {
  const data = { rates: { USD: 1, THB: 33.5, JPY: 158 }, at: 0 };
  near(convert({ kind: "fx", amt: 100, from: "USD", to: "THB" }, data).value, 3350);
  near(convert({ kind: "fx", amt: 33.5, from: "THB", to: "JPY" }, data).value, 158);
  near(convert({ kind: "unit", dim: "temp", amt: 100, from: "c", to: "f" }).value, 212);
  near(convert({ kind: "unit", dim: "temp", amt: -40, from: "f", to: "c" }).value, -40);
  near(convert({ kind: "unit", dim: "area", amt: 1, from: "rai", to: "wa2" }).value, 400);
  near(convert({ kind: "unit", dim: "length", amt: 1, from: "mi", to: "km" }).value, 1.609344);
});

test("the box: no rates, no currency box; the page script carries one calculator", () => {
  assert.equal(quickHtml(quickMatch("25000 usd to thb"), null), "");
  assert.equal(quickJson(quickMatch("25000 usd to thb"), null), undefined);
  const data = { rates: { USD: 1, THB: 33.5 }, at: Date.parse("2026-10-14T00:02:00Z"),
                 hist: [["2026-09-14", 33.2], ["2026-09-30", 33.6], ["2026-10-13", 33.5]] };
  const h = quickHtml(quickMatch("25000 usd to thb"), data);
  assert.match(h, /837,500|837500/);
  assert.match(h, /2026-10-14 07:02/);
  assert.match(h, /exchangerate-api\.com/);
  assert.match(h, /<polyline/);
  assert.ok(!/<\/script>[\s\S]*<\/script>/.test(h.replace(/<script>[\s\S]*?<\/script>/, "")), "one script");
  const c = quickHtml(quickMatch("15% of 2000"));
  assert.match(c, /<output class="qa-out"[^>]*>300</);
  assert.equal(quickJson(quickMatch("15% of 2000")).value, 300);
  assert.equal(mdSpark([["2026-01-01", 1]], ""), "");
});

test("translator: the words and the language, Thai ำ kept whole", () => {
  assert.deepEqual(trMatch("translate toilet to thai"), { kind: "tr", text: "toilet", from: "auto", to: "th" });
  assert.deepEqual(trMatch("ห้องน้ำ ภาษาอังกฤษ"), { kind: "tr", text: "ห้องน้ำ", from: "auto", to: "en" });
  assert.equal(trMatch("แปลห้องน้ำเป็นภาษาอังกฤษ").text, "ห้องน้ำ");
  assert.equal(trMatch("how do you say thank you in burmese").to, "my");
  assert.equal(trMatch("ไก่แปลว่าอะไร").to, "en");
  assert.equal(trMatch("toilet แปลว่า").to, "th");
  assert.equal(trMatch("what does sawasdee mean").to, "en");
  assert.equal(trMatch("Translate Where Is Wat Phra Singh").text, "Where Is Wat Phra Singh");
  assert.deepEqual(trMatch("translator"), { kind: "tr", text: "", from: "auto", to: "" });
  const tr = quickHtml(trMatch("ห้องน้ำ ภาษาอังกฤษ"), { tr: { text: "ห้องน้ำ", from: "th", to: "en", t: "Bathroom", r: "" } });
  assert.match(tr, /<div class="tr-out" lang="en" aria-live="polite">Bathroom<\/div>/);
  assert.doesNotThrow(() => new Function(/<script>([\s\S]*?)<\/script>/.exec(tr)[1]), "page script parses");
});
