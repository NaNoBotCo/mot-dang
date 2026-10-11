#!/usr/bin/env node
// POST /feedback, GET /feedback-tally and GET /feedback-events on the claims Worker
// (worker/worker.js), run against a fake KV.
//
//   node tests/test_feedback_worker.js
import { register } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
register("data:text/javascript," + encodeURIComponent(`
export async function resolve(spec, ctx, next) {
  if (spec === "cloudflare:email") return {
    url: "data:text/javascript," + encodeURIComponent(
      "export class EmailMessage { constructor(f, t, raw) { this.from = f; this.to = t; this.raw = raw } }"),
    shortCircuit: true,
  };
  return next(spec, ctx);
}`));
const worker = (await import(pathToFileURL(join(ROOT, "worker/worker.js")).href)).default;

function makeKV() {
  const m = new Map();
  return {
    m,
    async get(key, type) { const e = m.get(key); if (!e) return null; return type === "json" ? JSON.parse(e.value) : e.value; },
    async put(key, value, opts = {}) { m.set(key, { value: String(value), ttl: opts.expirationTtl ?? null }); },
    async delete(key) { m.delete(key); },
    async list({ prefix = "", cursor, limit = 1000 } = {}) {
      const all = [...m.keys()].filter(k => k.startsWith(prefix)).sort();
      const start = cursor ? Number(cursor) : 0;
      const keys = all.slice(start, start + limit).map(name => ({ name }));
      const done = start + limit >= all.length;
      return { keys, list_complete: done, cursor: done ? undefined : String(start + limit) };
    },
  };
}

const ORIGIN = "https://fb.test";
const call = (env, path, init = {}) => worker.fetch(new Request(ORIGIN + path, init), env, { waitUntil() {} });
const post = (env, body, ip = "1.2.3.4") =>
  call(env, "/feedback", { method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": ip }, body: JSON.stringify(body) });
const tally = async (env, item) => (await (await call(env, "/feedback-tally?item=" + encodeURIComponent(item))).json());

let pass = 0; const failures = [];
function check(name, ok, why = "") {
  if (ok) { pass++; return; }
  failures.push(name); console.log(`FAIL  ${name}${why ? " — " + why : ""}`);
}

const env = { KV: makeKV(), FEEDBACK_KEY: "sekrit-key-1234" };
const A = "aaaaaaaa-1111", B = "bbbbbbbb-2222";
const item = "place:cm-test-1";

let r = await post(env, { item, x: 1, who: A, page: "/cm/x/y.html", lang: "th" });
let j = await r.json();
check("vote up: 200", r.status === 200 && j.ok && j.mine === 1, JSON.stringify(j));
check("vote up: tally 1/0", j.tally.up === 1 && j.tally.down === 0, JSON.stringify(j));

r = await post(env, { item, x: 1, who: A });
j = await r.json();
check("same vote again: still 1/0", j.tally.up === 1 && j.tally.down === 0, JSON.stringify(j));
check("same vote again: no second event", [...env.KV.m.keys()].filter(k => k.startsWith("fb-vote:")).length === 1);

j = await (await post(env, { item, x: -1, who: A })).json();
check("change of mind: 0/1", j.tally.up === 0 && j.tally.down === 1 && j.mine === -1, JSON.stringify(j));

j = await (await post(env, { item, x: 1, who: B })).json();
check("second reader: 1/1", j.tally.up === 1 && j.tally.down === 1, JSON.stringify(j));

j = await (await post(env, { item, x: 0, who: A })).json();
check("withdraw: 1/0", j.tally.up === 1 && j.tally.down === 0 && j.mine === 0, JSON.stringify(j));

j = await (await post(env, { item, x: 0, who: A })).json();
check("withdraw twice: tally unchanged", j.tally.up === 1 && j.tally.down === 0, JSON.stringify(j));

// a note arrives with the vote the reader holds; x omitted keeps it
j = await (await post(env, { item, note: "  The hours are wrong.  ", who: B, lang: "en" })).json();
check("note only: keeps vote", j.ok && j.mine === 1 && j.tally.up === 1, JSON.stringify(j));
const notes = [...env.KV.m.keys()].filter(k => k.startsWith("fb-note:"));
check("note: one fb-note key", notes.length === 1, notes.join());
const nrec = JSON.parse(env.KV.m.get(notes[0]).value);
check("note: trimmed, carries item, x, who", nrec.note === "The hours are wrong." && nrec.item === item && nrec.x === 1 && nrec.who === B, JSON.stringify(nrec));

// a note with a vote change: both events
j = await (await post(env, { item, x: -1, note: "Closed on Mondays", who: B })).json();
check("vote + note: tally 0/1", j.tally.up === 0 && j.tally.down === 1, JSON.stringify(j));
check("vote + note: two notes now", [...env.KV.m.keys()].filter(k => k.startsWith("fb-note:")).length === 2);

// validation
for (const [name, body] of [
  ["no item", { x: 1 }],
  ["item too long", { item: "a".repeat(121), x: 1 }],
  ["item bad char", { item: "place:x y", x: 1 }],
  ["item with query chars", { item: "place:x?y=1", x: 1 }],
  ["x out of range", { item, x: 2 }],
  ["x a string", { item, x: "1" }],
  ["nothing to record", { item }],
  ["bad who", { item, x: 1, who: "short" }],
  ["who with slash", { item, x: 1, who: "abcdefgh/../x" }],
]) {
  r = await post(env, body);
  check("rejects: " + name, r.status === 400, String(r.status));
}
r = await post(env, { item: "a".repeat(120), x: 1, who: A });
check("item of 120 chars is accepted", r.status === 200);
check("item with : _ - . / is accepted", (await post(env, { item: "shelf:cm/hair.salon_x-1", x: 1, who: A })).status === 200);
r = await call(env, "/feedback", { method: "POST", headers: { "cf-connecting-ip": "9.9.9.9" }, body: "{nope" });
check("bad json: 400", r.status === 400);
r = await call(env, "/feedback", { method: "POST", headers: { "cf-connecting-ip": "9.9.9.9" }, body: JSON.stringify({ item, x: 1, note: "z".repeat(7000) }) });
check("oversize body: 400", r.status === 400);

// long note is cut to 2000
j = await (await post(env, { item: "site:long", note: "y".repeat(2500), who: A })).json();
const longKey = [...env.KV.m.keys()].filter(k => k.startsWith("fb-note:")).map(k => JSON.parse(env.KV.m.get(k).value)).find(n => n.item === "site:long");
check("note capped at 2000", longKey && longKey.note.length === 2000);

// no who: falls back to a hash of ip+ua, still replaces
let k1 = await post(env, { item: "event:x", x: 1 }, "7.7.7.7");
k1 = await post(env, { item: "event:x", x: -1 }, "7.7.7.7");
j = await k1.json();
check("no who: replaced by ip+ua hash", j.tally.up === 0 && j.tally.down === 1, JSON.stringify(j));

// tally
j = await tally(env, item);
check("tally GET: up/down", j.ok && j.up === 0 && j.down === 1, JSON.stringify(j));
r = await call(env, "/feedback-tally?item=" + encodeURIComponent(item));
check("tally GET: cached a minute", /max-age=60/.test(r.headers.get("cache-control") || ""));
j = await tally(env, "place:never-voted");
check("tally GET: unknown item is 0/0", j.up === 0 && j.down === 0);
r = await call(env, "/feedback-tally?item=bad%20id");
check("tally GET: bad item 400", r.status === 400);
r = await call(env, "/feedback-tally");
check("tally GET: no item 400", r.status === 400);

// events: key-gated
r = await call(env, "/feedback-events");
check("events: 404 without key", r.status === 404);
r = await call(env, "/feedback-events", { headers: { "x-md-key": "wrong-key-123456" } });
check("events: 404 with wrong key", r.status === 404);
const noKeyEnv = { KV: env.KV };
r = await call(noKeyEnv, "/feedback-events", { headers: { "x-md-key": "" } });
check("events: 404 where no secret is set", r.status === 404);
r = await call(env, "/feedback-events", { headers: { "x-md-key": "sekrit-key-1234" } });
j = await r.json();
check("events: 200 with key", r.status === 200 && j.ok && j.count === j.events.length && j.count > 5, JSON.stringify(j).slice(0, 200));
check("events: notes included", j.events.some(e => e.k.startsWith("fb-note:") && e.note === "The hours are wrong."));
check("events: votes included", j.events.some(e => e.k.startsWith("fb-vote:") && e.item === item && e.x === 1));
const mid = j.events[3].at;
j = await (await call(env, "/feedback-events?since=" + encodeURIComponent(mid), { headers: { "x-md-key": "sekrit-key-1234" } })).json();
check("events: since filters", j.events.every(e => e.at >= mid) && j.count < 20);
// no public read of notes anywhere else
for (const path of ["/feedback", "/feedback-notes", "/feedback-note", "/feedbacks"]) {
  r = await call(env, path);
  const t = await r.text();
  check("no public GET: " + path, !t.includes("The hours are wrong"), t.slice(0, 80));
}

// rate limit: 120 an hour per ip, 12 notes
{
  const e2 = { KV: makeKV() };
  let last;
  for (let i = 0; i < 121; i++) last = await post(e2, { item: "place:rl" + (i % 5), x: 1, who: "who-" + String(i).padStart(8, "0") }, "5.5.5.5");
  check("rate limit: 121st vote is 429", last.status === 429, String(last.status));
  check("rate limit: another ip is fine", (await post(e2, { item, x: 1, who: A }, "6.6.6.6")).status === 200);
  const e3 = { KV: makeKV() };
  const rs = [];
  for (let i = 0; i < 13; i++) rs.push((await post(e3, { item, note: "n" + i, who: A }, "4.4.4.4")).status);
  check("note limit: 12 pass, 13th is 429", rs.slice(0, 12).every(s => s === 200) && rs[12] === 429, rs.join());
  check("note limit: votes still pass after", (await post(e3, { item, x: 1, who: A }, "4.4.4.4")).status === 200);
}

// OPTIONS carries CORS
r = await call(env, "/feedback", { method: "OPTIONS" });
check("OPTIONS: cors", r.headers.get("access-control-allow-origin") === "*");
check("404 list names /feedback", JSON.stringify(await (await call(env, "/nope")).json()).includes("/feedback"));

console.log(`${pass} passed, ${failures.length} failed`);
process.exit(failures.length ? 1 : 0);
