#!/usr/bin/env node
// WO-110. The credit field on POST /suggest and POST /feedback, against a fake KV.
// Runs against the Worker under MD_ROOT (default: the repo root).
//
//   node tests/test_credits_worker.mjs
import { register } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.MD_ROOT ? resolve(process.env.MD_ROOT) : resolve(HERE, "..");
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

const call = (env, path, body, ip) => worker.fetch(new Request("https://cr.test" + path, {
  method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": ip },
  body: JSON.stringify(body) }), env, { waitUntil() {} });
let pass = 0; const failures = [];
function check(name, ok, why = "") {
  if (ok) { pass++; return; }
  failures.push(name); console.log(`FAIL  ${name}${why ? " — " + why : ""}`);
}
const env = { KV: makeKV(), FEEDBACK_KEY: "sekrit-key-1234" };
let n = 0;
const ip = () => `10.0.0.${++n}`;
const sug = () => [...env.KV.m.keys()].filter(k => k.startsWith("sug:")).map(k => JSON.parse(env.KV.m.get(k).value));
const notes = () => [...env.KV.m.keys()].filter(k => k.startsWith("fb-note:")).map(k => JSON.parse(env.KV.m.get(k).value));

// /suggest: ticked and named
let r = await call(env, "/suggest", { kind: "correction", what: "wrong phone", from: "reader@example.org",
  credit: { consent: true, name: "  Example   Reader " } }, ip());
let j = await r.json();
let rec = sug().find(s => s.id === j.id);
check("suggest: 200 with a ref", r.status === 200 && j.ok && j.ref === j.id.slice(0, 8), JSON.stringify(j));
check("suggest: credit holds the name and the wording version",
  rec.credit && rec.credit.name === "Example Reader" && rec.credit.v === "2026-10-11", JSON.stringify(rec.credit));
check("suggest: the contact address stays a separate field", rec.from === "reader@example.org" && !JSON.stringify(rec.credit ?? null).includes("example.org"));

// /suggest: no credit, or not ticked
r = await call(env, "/suggest", { kind: "correction", what: "wrong hours" }, ip());
j = await r.json();
rec = sug().find(s => s.id === j.id);
check("suggest: no credit field, no credit, no ref", rec.credit === null && j.ref === undefined, JSON.stringify(rec.credit));
r = await call(env, "/suggest", { kind: "correction", what: "x", credit: { consent: false, name: "Example Reader" } }, ip());
j = await r.json();
check("suggest: consent false drops the name", sug().find(s => s.id === j.id).credit === null && j.ref === undefined);
r = await call(env, "/suggest", { kind: "correction", what: "x", credit: { name: "Example Reader" } }, ip());
j = await r.json();
check("suggest: a name with no consent field is dropped", sug().find(s => s.id === j.id).credit === null);
r = await call(env, "/suggest", { kind: "correction", what: "x", credit: { consent: "true", name: "Example Reader" } }, ip());
j = await r.json();
check("suggest: consent must be the boolean true", sug().find(s => s.id === j.id).credit === null);

// the name test
for (const [label, name] of [
  ["empty", ""], ["one character", "x"], ["an email", "reader@example.org"], ["a link", "see https://example.org"],
  ["www", "www.example.org"], ["a phone number", "081 234 5678"], ["a phone with plus", "+66 81-234-5678"],
  ["angle brackets", "<b>Example</b>"], ["a control character", "Example\u0007Reader"],
]) {
  r = await call(env, "/suggest", { kind: "other", what: label, credit: { consent: true, name } }, ip());
  j = await r.json();
  check("name test: " + label + " is dropped", r.status === 200 && sug().find(s => s.id === j.id).credit === null && j.ref === undefined);
}
for (const [label, name] of [["Thai", "ตัวอย่าง ผู้อ่าน"], ["short digits", "Example 7"], ["nickname", "sample_nickname"]]) {
  r = await call(env, "/suggest", { kind: "other", what: label, credit: { consent: true, name } }, ip());
  j = await r.json();
  check("name test: " + label + " is kept", sug().find(s => s.id === j.id).credit?.name === name, JSON.stringify(sug().find(s => s.id === j.id).credit));
}
r = await call(env, "/suggest", { kind: "other", what: "long", credit: { consent: true, name: "N".repeat(90) } }, ip());
j = await r.json();
check("name test: 90 characters is cut to 60", sug().find(s => s.id === j.id).credit?.name.length === 60);

// /feedback: a note with a credit
r = await call(env, "/feedback", { item: "site:test", x: -1, note: "the map covers the button", who: "aaaaaaaa-1111",
  credit: { consent: true, name: "Example Reader" } }, ip());
j = await r.json();
const nr = notes().find(x => x.note === "the map covers the button");
check("feedback note: ref returned and stored", j.ok && /^[0-9a-f]{8}$/.test(j.ref) && nr.ref === j.ref, JSON.stringify(j));
check("feedback note: credit stored with the version", nr.credit?.name === "Example Reader" && nr.credit?.v === "2026-10-11");
const ev = await (await worker.fetch(new Request("https://cr.test/feedback-events", { headers: { "x-md-key": "sekrit-key-1234" } }), env, { waitUntil() {} })).json();
check("feedback-events carries the credit to the sync", ev.events.some(e => e.credit?.name === "Example Reader" && e.ref === nr.ref));

// /feedback: a vote with a credit and no note names nobody
r = await call(env, "/feedback", { item: "site:test2", x: 1, who: "bbbbbbbb-2222", credit: { consent: true, name: "Example Reader" } }, ip());
j = await r.json();
check("feedback vote only: no ref, no note record", j.ok && j.ref === undefined && notes().length === 1);

// /feedback: a note without a credit
r = await call(env, "/feedback", { item: "site:test3", note: "typo in the footer", who: "cccccccc-3333" }, ip());
j = await r.json();
const nr2 = notes().find(x => x.note === "typo in the footer");
check("feedback note without credit: no credit, no ref", j.ok && j.ref === undefined && nr2.credit === undefined && nr2.ref === undefined);

console.log(`${pass} passed, ${failures.length} failed`);
process.exit(failures.length ? 1 : 0);
