// mapsense: the map beacon (mapsense_layer.py) and the Worker's rows (publish/worker.js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import vm from "node:vm";

const JS = execFileSync("python3", ["-c", "import mapsense_layer;print(mapsense_layer.map_js())"]).toString();

function page(host) {
  const sent = [], L = {}, D = {};
  const ctx = {
    location: { hostname: host, pathname: "/map.html" },
    navigator: { sendBeacon: (u, b) => { sent.push({ u, b }); return true; } },
    Blob: class { constructor(p) { this.t = p.join(""); } },
    addEventListener: (k, f) => { L[k] = f; },
    document: { visibilityState: "visible", addEventListener: (k, f) => { D[k] = f; } },
    setTimeout: (f) => f(), clearTimeout: () => {},
    isFinite, Math, JSON, String,
  };
  ctx.window = ctx;
  vm.runInNewContext(JS, ctx);
  return { ctx, sent, hide: () => L.pagehide() };
}

test("events leave in one beacon on pagehide, rounded to a cell", () => {
  const p = page("motdang.net");
  p.ctx.MDSENSE.tell("open", { k: "cm:wat-phra-singh", lat: 18.78867, lng: 98.98221, z: 15.4 });
  p.ctx.MDSENSE.tell("coord", { d: "Plus Code" });
  p.ctx.MDSENSE.tell("pin", { lat: 18.8, lng: 99.0, k: undefined });
  assert.equal(p.sent.length, 0);
  p.hide();
  assert.equal(p.sent.length, 1);
  assert.equal(p.sent[0].u, "/api/map");
  const d = JSON.parse(p.sent[0].b.t);
  assert.equal(d.pg, "/map.html");
  assert.deepEqual(d.ev[0], { e: "open", c: "18.79,98.98", z: 15, k: "cm:wat-phra-singh" });
  assert.deepEqual(d.ev[1], { e: "coord", d: "pluscode" });
  assert.deepEqual(d.ev[2], { e: "pin", c: "18.80,99.00" });
});

test("a view is sent only after a move the reader made, once per cell and zoom", () => {
  const p = page("motdang.net"), H = {};
  let c = { lat: 18.7, lng: 98.9 }, z = 13;
  const map = { on: (k, f) => { H[k] = f; }, getCenter: () => c, getZoom: () => z };
  p.ctx.MDSENSE.watch(map);
  H.moveend({});                          // a fly the code did
  H.moveend({ originalEvent: {} });       // a drag
  H.moveend({ originalEvent: {} });       // same place again
  c = { lat: 18.75, lng: 98.9 };
  H.movestart({ originalEvent: {} }); H.moveend({});
  p.hide();
  const ev = JSON.parse(p.sent[0].b.t).ev;
  assert.deepEqual(ev.map((e) => e.c), ["18.70,98.90", "18.75,98.90"]);
});

test("a local build sends nothing", () => {
  const p = page("127.0.0.1");
  p.ctx.MDSENSE.tell("open", { lat: 18, lng: 99 });
  p.hide();
  assert.equal(p.sent.length, 0);
});

test("the Worker writes one row per event and keeps them out of SUM(double1)", async () => {
  const src = (await import("node:fs")).readFileSync("publish/worker.js", "utf8");
  assert.match(src, /doubles: \[0, 204, 0, z, 1\]/);
  const mod = await import("../publish/worker.js");
  const rows = [];
  const env = { TRAFFIC: { writeDataPoint: (r) => rows.push(r) } };
  const ctx = { waitUntil: (p) => p };
  const body = JSON.stringify({ pg: "/map.html", ev: [
    { e: "open", c: "18.79,98.98", z: 15, k: "cm:wat-phra-singh" },
    { e: "bogus", c: "1,2" },
    { e: "view", c: "<script>", z: 99 },
  ] });
  const r = await mod.default.fetch(new Request("https://motdang.net/api/map", {
    method: "POST", body, headers: { "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1" } }), env, ctx);
  assert.equal(r.status, 204);
  assert.equal(rows.length, 2);
  assert.deepEqual(rows[0].blobs.slice(3), ["/api/map", "XX", "204", "(same site)", "EVENT", "open", "18.79,98.98", "cm:wat-phra-singh", "/map.html"]);
  assert.equal(rows[0].doubles[0], 0);
  assert.deepEqual(rows[1].blobs.slice(8, 11), ["view", "", ""]);
  assert.equal(rows[1].doubles[3], -1);
});

test("a map search row carries the view's cell, and its words only when it answered nothing", async () => {
  const mod = await import("../publish/worker.js");
  const rows = [], ps = [];
  const env = { TRAFFIC: { writeDataPoint: (r) => rows.push(r) }, SITE: { get: async () => null, head: async () => null } };
  globalThis.caches = { default: { match: async () => null, put: async () => {} } };
  await mod.default.fetch(new Request("https://motdang.net/api/v1/search?q=moto+parking&bbox=98.95,18.77,99.01,18.80"),
    env, { waitUntil: (p) => ps.push(p) });
  await Promise.all(ps);
  // no index in this env: the engine answered 503, so no count and no words
  assert.deepEqual(rows[0].blobs.slice(8), ["search", "18.79,98.98", ""]);
  assert.deepEqual(rows[0].doubles.slice(3), [13, -1]);
});
