// share_layer.py KIT_JS: share codes, tagged links, the calendar file, countdowns.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import vm from "node:vm";

const KIT = execFileSync("python3", ["-c", "import share_layer;print(share_layer.KIT_JS)"]).toString();
const ctx = { Math, Date, JSON, String, Number, Uint8Array, encodeURIComponent, decodeURIComponent, isFinite,
  crypto: { getRandomValues: (a) => { for (let i = 0; i < a.length; i++) a[i] = (i * 37 + 11) & 255; return a; } } };
ctx.window = ctx;
vm.runInNewContext(KIT, ctx);
const K = ctx.MDSHAREKIT;

test("a code is eight letters from the 32, and parses back with its channel", () => {
  const c = K.code();
  assert.match(c, /^[a-km-np-z2-9]{8}$/);
  assert.equal(K.code([0, 1, 2, 3, 31, 32, 255, 64]), "abcd9a9a");
  assert.deepEqual({ ...K.parse(c + ".l") }, { code: c, ch: "l" });
  assert.deepEqual({ ...K.parse(c) }, { code: c, ch: "" });
  assert.equal(K.parse("ABCDEFGH"), null);
  assert.equal(K.parse("abcdefg1"), null);     // 1 is not in the alphabet
  assert.equal(K.parse("abcdefgh.toolong"), null);
});

test("our links get ?s=, the hash survives, other hosts are left alone", () => {
  assert.equal(K.tagUrl("https://motdang.net/cm/p/x.html", "abcdefgh", "l"), "https://motdang.net/cm/p/x.html?s=abcdefgh.l");
  assert.equal(K.tagUrl("https://motdang.net/#ev=latin-night", "abcdefgh", "w"), "https://motdang.net/?s=abcdefgh.w#ev=latin-night");
  assert.equal(K.tagUrl("https://motdang.net/map.html?go=18.7,98.9&s=zzzzzzzz.c#16/1/2", "abcdefgh", "n"),
    "https://motdang.net/map.html?go=18.7,98.9&s=abcdefgh.n#16/1/2");
  assert.equal(K.tagUrl("https://www.motdang.net", "abcdefgh", ""), "https://www.motdang.net/?s=abcdefgh");
  assert.equal(K.tagUrl("https://maps.google.com/?q=1,2", "abcdefgh", "l"), "https://maps.google.com/?q=1,2");
  assert.equal(K.tagUrl("http://localhost:8765/cm/p/x.html", "abcdefgh", "c", "localhost"), "http://localhost:8765/cm/p/x.html?s=abcdefgh.c");
  assert.equal(K.tagUrl("http://localhost:8765/x", "abcdefgh", "c"), "http://localhost:8765/x");
});

test("a message has each of our links tagged, punctuation kept outside", () => {
  const t = "Wat Phra Singh\nhttps://motdang.net/cm/p/wat.html.\nGoogle: https://maps.google.com/?q=1,2\n(https://motdang.net/)";
  assert.equal(K.tagText(t, "abcdefgh", "m"),
    "Wat Phra Singh\nhttps://motdang.net/cm/p/wat.html?s=abcdefgh.m.\nGoogle: https://maps.google.com/?q=1,2\n(https://motdang.net/?s=abcdefgh.m)");
});

test("another app's share link has the link inside it tagged for that app", () => {
  const u = "https://motdang.net/cm/p/x.html";
  const line = K.retag(K.lineHref("ร้านนี้ " + u), "abcdefgh");
  assert.equal(decodeURIComponent(line.split("text=")[1]), "ร้านนี้ " + u + "?s=abcdefgh.l");
  const lineit = K.retag("https://social-plugins.line.me/lineit/share?url=" + encodeURIComponent(u), "abcdefgh");
  assert.equal(decodeURIComponent(lineit.split("url=")[1]), u + "?s=abcdefgh.l");
  const wa = K.retag("https://wa.me/?text=Hi%20" + encodeURIComponent(u), "abcdefgh");
  assert.equal(decodeURIComponent(wa.split("text=")[1]), "Hi " + u + "?s=abcdefgh.w");
  const fb = K.retag(K.fbHref(u), "abcdefgh");
  assert.equal(decodeURIComponent(fb.split("u=")[1]), u + "?s=abcdefgh.f");
  const tg = K.retag(K.tgHref(u, "Name"), "abcdefgh");
  assert.match(decodeURIComponent(tg), /x\.html\?s=abcdefgh\.t&text=Name$/);
  const mail = K.retag(K.mailHref("Look " + u), "abcdefgh");
  assert.ok(mail.startsWith("mailto:?subject="));
  assert.equal(decodeURIComponent(mail.split("body=")[1]), "Look " + u + "?s=abcdefgh.m");
  assert.equal(K.appOf("fb-messenger://share/?link=x"), "messenger");
  assert.equal(K.retag("https://example.com/?text=" + encodeURIComponent(u), "abcdefgh"), "https://example.com/?text=" + encodeURIComponent(u));
});

const NIGHT = { k: "coco-bongo-latin-night", t: "Coco Bongo Latin night, salsa; bachata", s: "2026-10-02 20:00:00", e: null,
  v: "Copacabana Rooftop", la: 18.7876, lo: 98.9931, d: "Salsa and bachata on the roof", cost: "200 THB" };

test("a timed event: Bangkok times with their zone, a stable UID, an alarm, folded lines", () => {
  const t = K.ics(NIGHT, { now: Date.UTC(2026, 9, 1, 3, 4, 5) });
  const L = t.split("\r\n");
  assert.ok(t.endsWith("\r\n"));
  assert.ok(L.includes("TZID:Asia/Bangkok"));
  assert.ok(L.includes("UID:coco-bongo-latin-night-2026-10-02@motdang.net"));
  assert.ok(L.includes("DTSTAMP:20261001T030405Z"));
  assert.ok(L.includes("DTSTART;TZID=Asia/Bangkok:20261002T200000"));
  assert.ok(L.includes("DTEND;TZID=Asia/Bangkok:20261002T220000"));
  assert.ok(L.includes("SUMMARY:Coco Bongo Latin night\\, salsa\\; bachata"));
  assert.ok(L.includes("GEO:18.787600;98.993100"));
  assert.ok(L.includes("URL:https://motdang.net/#ev=coco-bongo-latin-night"));
  assert.ok(L.includes("TRIGGER:-PT1H"));
  for (const l of L) assert.ok(Buffer.byteLength(l, "utf8") <= 75, "line over 75 octets: " + l);
  const thai = K.ics({ ...NIGHT, t: "งานวัด".repeat(20) });
  for (const l of thai.split("\r\n")) assert.ok(Buffer.byteLength(l, "utf8") <= 75);
  const summary = thai.split("\r\n").reduce((acc, l) => (acc.on && l.startsWith(" ") ? { on: 1, s: acc.s + l.slice(1) } : l.startsWith("SUMMARY:") ? { on: 1, s: l } : { on: 0, s: acc.s }), { on: 0, s: "" }).s;
  assert.equal(summary, "SUMMARY:" + "งานวัด".repeat(20));
});

test("an all-day run of days: DATE values, the end the day after the last", () => {
  const e = { k: "tennis", t: "Tennis classes", s: "2026-10-01 00:00:00", e: "2026-10-31", ad: true };
  const L = K.ics(e, { now: 0 }).split("\r\n");
  assert.ok(L.includes("DTSTART;VALUE=DATE:20261001"));
  assert.ok(L.includes("DTEND;VALUE=DATE:20261101"));
  assert.ok(!L.includes("TZID:Asia/Bangkok"));
  assert.ok(!L.includes("BEGIN:VALARM"));
  assert.equal(K.when(e).en, "1 Oct – 31 Oct");
});

test("Google Calendar link and the words that go with a link", () => {
  const g = K.gcal(NIGHT, { url: "https://motdang.net/?s=abcdefgh.l#ev=coco-bongo-latin-night" });
  assert.match(g, /dates=20261002T200000\/20261002T220000&ctz=Asia%2FBangkok/);
  assert.match(g, /location=Copacabana%20Rooftop/);
  assert.equal(K.when(NIGHT).th, "ศ. 2 ต.ค. 20:00");
  assert.equal(K.when(NIGHT).en, "Fri 2 Oct 20:00");
  assert.equal(K.evText(NIGHT, "U"), "Coco Bongo Latin night, salsa; bachata\nศ. 2 ต.ค. 20:00 · Fri 2 Oct 20:00\nCopacabana Rooftop\nU");
});

test("the countdown: days, then hours, then the clock, then on, then past", () => {
  const s = K.at(NIGHT.s);
  assert.equal(s, Date.UTC(2026, 9, 2, 13, 0, 0));
  assert.equal(K.countText(NIGHT, s - 3 * 864e5).en, "in 3 days");
  assert.equal(K.countText(NIGHT, s - 864e5 - 5 * 3600e3).en, "in 1 day 5 h");
  assert.equal(K.countText(NIGHT, s - 2 * 3600e3 - 125e3).en, "in 2 h 2 min");
  assert.equal(K.countText(NIGHT, s - 2 * 3600e3 - 125e3, true).th, "อีก 2:02:05");
  assert.equal(K.countText(NIGHT, s + 60e3).en, "On now");
  assert.equal(K.countText(NIGHT, s + 3 * 3600e3).th, "จบไปแล้ว");
  assert.deepEqual({ ...K.until(NIGHT, s - 90061e3) }, { state: "soon", ms: 90061e3, d: 1, h: 1, m: 1, s: 1 });
});
