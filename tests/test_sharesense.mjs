// sharesense: the Worker's rows for the Send sheet (POST /api/share) and for links that land with ?s=.
import { test } from "node:test";
import assert from "node:assert/strict";
import { shareSense, shareLand } from "../publish/sharesense.js";

function env() { const rows = []; return { rows, TRAFFIC: { writeDataPoint: (r) => rows.push(r) } }; }
const classify = (ua) => ({ category: /bot/i.test(ua) ? "social" : "human", agent: /bot/i.test(ua) ? "facebookexternalhit" : "Safari" });
function post(body, ua = "Mozilla/5.0 Safari") {
  return new Request("https://motdang.net/api/share", { method: "POST", body: typeof body === "string" ? body : JSON.stringify(body),
    headers: { "user-agent": ua } });
}

test("each good event is one row; double1 stays 0", async () => {
  const E = env();
  const r = await shareSense(post({ pg: "/cm/p/wat.html", ev: [
    { e: "sheet", s: "abcdefgh", d: "button", k: "cm:wat-phra-singh" },
    { e: "channel", s: "abcdefgh", d: "line", p: "zzzzzzzz", k: "cm:wat-phra-singh" },
    { e: "arrive", s: "qwertyui", d: "whatsapp", k: "ev:coco-bongo-latin-night" }] }), E, classify);
  assert.equal(r.status, 204);
  assert.equal(E.rows.length, 3);
  assert.deepEqual(E.rows[1].blobs, ["motdang.net", "human", "Safari", "/api/share", "XX", "204", "(same site)", "SHARE",
    "channel", "abcdefgh", "line", "/cm/p/wat.html", "zzzzzzzz", "cm:wat-phra-singh"]);
  assert.deepEqual(E.rows[1].doubles, [0, 204, 0, 0, 1]);
  assert.equal(E.rows[2].blobs[13], "ev:coco-bongo-latin-night");
});

test("unknown events, bad codes, odd keys and junk are dropped or blanked", async () => {
  const E = env();
  await shareSense(post({ pg: "javascript:alert(1)", ev: [
    { e: "drop table", s: "abcdefgh" },
    { e: "channel", s: "ABCDEFGH", d: "LINE!", p: "x", k: "../etc" }] }), E, classify);
  assert.equal(E.rows.length, 1);
  assert.deepEqual(E.rows[0].blobs.slice(8), ["channel", "", "", "", "", ""]);
  const F = env();
  await shareSense(post("not json"), F, classify);
  await shareSense(post("x".repeat(9000)), F, classify);
  await shareSense(new Request("https://motdang.net/api/share"), F, classify);
  assert.equal(F.rows.length, 0);
});

test("a request on a shared link writes a land row; others write nothing", () => {
  const E = env();
  const resp = new Response("", { status: 200 });
  shareLand(E, new URL("https://motdang.net/cm/p/wat.html?s=abcdefgh.l"), new Request("https://motdang.net/"), resp, "social", "facebookexternalhit", "(none)");
  shareLand(E, new URL("https://motdang.net/cm/p/wat.html?s=nope"), new Request("https://motdang.net/"), resp, "human", "Safari", "");
  shareLand(E, new URL("https://motdang.net/cm/p/wat.html"), new Request("https://motdang.net/"), resp, "human", "Safari", "");
  assert.equal(E.rows.length, 1);
  assert.deepEqual(E.rows[0].blobs, ["motdang.net", "social", "facebookexternalhit", "/api/share", "XX", "200", "(none)", "SHARE",
    "land", "abcdefgh", "l", "/cm/p/wat.html", "", ""]);
  assert.equal(E.rows[0].doubles[0], 0);
});
