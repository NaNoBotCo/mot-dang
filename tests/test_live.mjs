/* /api/live (publish/live.js) under plain node, node:sqlite standing in for D1.
 *     node tests/test_live.mjs */
import { DatabaseSync } from "node:sqlite";
import { live, LIVE_SCHEMA } from "../publish/live.js";

const db = new DatabaseSync(":memory:");
db.exec(LIVE_SCHEMA);
const env = { LIVE: { prepare(sql) { let a = []; const st = {
  bind(...x) { a = x; return st; },
  async first() { return db.prepare(sql).get(...a) || null; },
  async run() { return db.prepare(sql).run(...a); } }; return st; } } };
let failed = 0;
const must = (c, m) => { if (!c) throw new Error(m); };
async function t(name, fn) { try { await fn(); console.log("  ok   " + name); } catch (e) { failed++; console.log("  FAIL " + name + "\n       " + e.message); } }
async function call(method, path, body, now) {
  const url = new URL("https://motdang.net" + path);
  const r = await live(new Request(url, { method, body: body ? JSON.stringify(body) : undefined }), env, url, now);
  return { status: r.status, d: await r.json() };
}
const T0 = 1_800_000_000_000;

await t("a share starts, takes a position, and shows it", async () => {
  const s = (await call("POST", "/api/live", null, T0)).d;
  must(/^[a-z2-7]{16}$/.test(s.id) && s.tok && s.until === T0 + 3600e3, JSON.stringify(s));
  must((await call("GET", "/api/live/" + s.id, null, T0)).d.lat === null, "position before any was sent");
  must((await call("POST", "/api/live/" + s.id, { tok: s.tok, lat: 18.7876, lng: 98.9935, acc: 12 }, T0 + 1000)).d.ok, "update");
  const g = (await call("GET", "/api/live/" + s.id, null, T0 + 2000)).d;
  must(g.lat === 18.7876 && g.lng === 98.9935 && g.acc === 12 && g.at === T0 + 1000, JSON.stringify(g));
});

await t("only the sharer's key moves it", async () => {
  const s = (await call("POST", "/api/live", null, T0)).d;
  must((await call("POST", "/api/live/" + s.id, { tok: "x", lat: 1, lng: 1 }, T0 + 1000)).status === 403, "wrong key took");
});

await t("the hour ends it, and the row goes", async () => {
  const s = (await call("POST", "/api/live", null, T0)).d;
  await call("POST", "/api/live/" + s.id, { tok: s.tok, lat: 18.8, lng: 99 }, T0 + 1000);
  must((await call("GET", "/api/live/" + s.id, null, T0 + 3600e3)).d.ended, "still live after the hour");
  must(!db.prepare("SELECT 1 FROM live WHERE id = ?").get(s.id), "row kept");
  must((await call("POST", "/api/live/" + s.id, { tok: s.tok, lat: 18.8, lng: 99 }, T0 + 3601e3)).status === 410, "update after the hour");
});

await t("stop ends it at once", async () => {
  const s = (await call("POST", "/api/live", null, T0)).d;
  must((await call("POST", "/api/live/" + s.id, { tok: s.tok, stop: 1 }, T0 + 5000)).d.ended, "stop");
  must((await call("GET", "/api/live/" + s.id, null, T0 + 6000)).d.ended, "still live after stop");
});

await t("a bad position or a bad id is refused", async () => {
  const s = (await call("POST", "/api/live", null, T0)).d;
  must((await call("POST", "/api/live/" + s.id, { tok: s.tok, lat: 200, lng: 1 }, T0 + 1000)).status === 400, "lat 200");
  must((await call("GET", "/api/live/NOT-AN-ID", null, T0)).status === 404, "bad id");
});

console.log(failed ? `\n${failed} FAILED` : "\nall passed");
process.exit(failed ? 1 : 0);
