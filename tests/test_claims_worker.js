#!/usr/bin/env node
// The claims Worker (worker/worker.js), run against stubs.
//
//   node tests/test_claims_worker.js
//
// worker/worker.js has one import node cannot resolve — "cloudflare:email" —
// so a module hook hands it a two-line EmailMessage. Everything else it
// touches (env.KV, env.PHOTOS, env.MAIL) is stubbed below, small enough to
// read: KV is a Map that remembers TTLs and lists by prefix in key order, R2
// is a list of {key, uploaded} that pages one object at a time so the
// cursor loop actually runs, and MAIL fails when told to.
//
// What it proves, 2026-09-10: a mail that does not go leaves a mailfail:
// key that GET /health counts; the owner's edit link is a form in a browser
// and the record everywhere else, with every value escaped; a suggestion may
// say closed / moved / duplicate and carry a detail; and the nightly sweep
// deletes only alpha/ objects older than ALPHA_TTL.
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

/* ---- stubs ---------------------------------------------------------- */
function makeKV() {
  const m = new Map();
  return {
    m,
    async get(key, type) {
      const e = m.get(key);
      if (!e) return null;
      return type === "json" ? JSON.parse(e.value) : e.value;
    },
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
function makeR2(objects) {
  const store = new Map(objects.map(o => [o.key, o]));
  return {
    store,
    async put(key, body, meta) { store.set(key, { key, uploaded: new Date(), ...meta }); },
    async delete(keys) { for (const k of Array.isArray(keys) ? keys : [keys]) store.delete(k); },
    async list({ prefix = "", cursor } = {}) {
      const all = [...store.values()].filter(o => o.key.startsWith(prefix)).sort((a, b) => a.key < b.key ? -1 : 1);
      const start = cursor ? Number(cursor) : 0;
      const page = all.slice(start, start + 1);            // one per page, on purpose
      const truncated = start + 1 < all.length;
      return { objects: page, truncated, cursor: truncated ? String(start + 1) : undefined };
    },
  };
}
const makeMail = (fail) => ({ sent: [], async send(msg) { if (fail) throw new Error("no relay"); this.sent.push(msg); } });

const ORIGIN = "https://claims.test";
const call = (env, path, init = {}) => worker.fetch(new Request(ORIGIN + path, init), env);
const post = (env, path, body, headers = {}) =>
  call(env, path, { method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "1.2.3.4", ...headers }, body: JSON.stringify(body) });

/* ---- harness -------------------------------------------------------- */
let pass = 0; const failures = [];
function check(name, ok, why = "") {
  if (ok) { pass++; return; }
  failures.push(name + (why ? ` — ${why}` : ""));
  console.log(`FAIL  ${name}${why ? ` — ${why}` : ""}`);
}
const today = new Date().toISOString().slice(0, 10);

/* ---- /health, empty ------------------------------------------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  const r = await call(env, "/health");
  const j = await r.json();
  check("health: 200", r.status === 200);
  check("health: no-store", r.headers.get("cache-control") === "no-store");
  check("health: empty shape", j.ok === true && j.mailfail.count === 0 && j.mailfail.oldest === null, JSON.stringify(j));
}

/* ---- mail failures leave a mailfail: key ---------------------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(true) };
  const row = { name: "Baan Test", kind: "house", offer: "sale", price: "4.2M", agency: "A", contact: "x" };

  let r = await post(env, "/listing", { listings: [row] });
  let j = await r.json();
  check("listing: still ok when mail fails", r.status === 200 && j.ok === true && j.mailed === false, JSON.stringify(j));
  let keys = [...env.KV.m.keys()].filter(k => k.startsWith("mailfail:"));
  check("listing: one mailfail key", keys.length === 1, keys.join());
  check("listing: key is mailfail:<date>:<id>", keys[0] === `mailfail:${today}:${j.id}`, keys[0]);
  const rec = JSON.parse(env.KV.m.get(keys[0]).value);
  check("listing: record shape", rec.route === "listing" && rec.id === j.id && /no relay/.test(rec.error) && typeof rec.at === "string", JSON.stringify(rec));
  check("listing: 30-day ttl", env.KV.m.get(keys[0]).ttl === 30 * 24 * 3600, String(env.KV.m.get(keys[0]).ttl));

  r = await post(env, "/listing-csv", { csv: "name,kind,offer,price,agency,contact\nB,house,rent,12000,A,x\n", name: "b.csv" });
  j = await r.json();
  check("listing-csv: ok, mailed false", j.ok === true && j.mailed === false, JSON.stringify(j));
  keys = [...env.KV.m.keys()].filter(k => k.startsWith("mailfail:"));
  check("listing-csv: second mailfail key, route named", keys.length === 2
    && JSON.parse(env.KV.m.get(`mailfail:${today}:${j.id}`)?.value || "{}").route === "listing-csv");

  r = await post(env, "/alpha", { v: "up", who: "t", note: "n", ctx: {} });
  j = await r.json();
  check("alpha: ok, mailed false", j.ok === true && j.mailed === false, JSON.stringify(j));
  keys = [...env.KV.m.keys()].filter(k => k.startsWith("mailfail:"));
  check("alpha: third mailfail key, route named", keys.length === 3
    && JSON.parse(env.KV.m.get(`mailfail:${today}:${j.id}`)?.value || "{}").route === "alpha");

  r = await call(env, "/health");
  j = await r.json();
  check("health: counts the three", j.mailfail.count === 3 && j.mailfail.oldest === today, JSON.stringify(j));

  // An older day sorts first, so it is the one reported.
  await env.KV.put("mailfail:2026-01-02:old", "{}", { expirationTtl: 1 });
  j = await (await call(env, "/health")).json();
  check("health: oldest is the earliest date", j.mailfail.count === 4 && j.mailfail.oldest === "2026-01-02", JSON.stringify(j));

  // A mail that goes leaves nothing.
  const env2 = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  j = await (await post(env2, "/listing", { listings: [row] })).json();
  check("listing: mailed true, no key", j.mailed === true && ![...env2.KV.m.keys()].some(k => k.startsWith("mailfail:")));
}

/* ---- /edit/:token — a page in a browser, JSON elsewhere ------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  const HTML = { accept: "text/html,application/xhtml+xml,*/*;q=0.8" };

  let r = await call(env, "/edit/bogus", { headers: HTML });
  let t = await r.text();
  check("edit bogus: 404 html", r.status === 404 && /text\/html/.test(r.headers.get("content-type")), r.status);
  check("edit bogus: bilingual not-valid line", t.includes("ลิงก์นี้ใช้ไม่ได้ · This link is not valid"));
  check("edit bogus: no form", !t.includes("<form"));
  r = await call(env, "/edit/bogus");
  check("edit bogus: json for everyone else", r.status === 404 && /application\/json/.test(r.headers.get("content-type")));

  const nasty = `<b>"x"</b> & 'y'`;
  r = await post(env, "/claim", { placeId: "cm-test-1", phone: "081", note: nasty, hours: "9-5" });
  let j = await r.json();
  check("claim: created", j.ok === true && /\/edit\//.test(j.editUrl), JSON.stringify(j));
  const token = j.editUrl.split("/edit/")[1];

  r = await call(env, `/edit/${token}`, { headers: HTML });
  t = await r.text();
  check("edit: 200 html", r.status === 200 && /text\/html/.test(r.headers.get("content-type")));
  check("edit: no-store, no referrer", r.headers.get("cache-control") === "no-store" && r.headers.get("referrer-policy") === "no-referrer");
  check("edit: value escaped", t.includes("&lt;b&gt;&quot;x&quot;&lt;/b&gt; &amp; &#39;y&#39;") && !t.includes(nasty));
  check("edit: place id shown", t.includes("cm-test-1"));
  for (const k of ["phone", "lineId", "facebook", "instagram", "whatsapp", "email", "website", "hours", "note", "menu"])
    check(`edit: field ${k}`, t.includes(`name="${k}"`));
  check("edit: phone prefilled", t.includes('value="081"'));
  check("edit: save button", t.includes("บันทึก · Save"));
  check("edit: 48 px targets", /min-height:48px/.test(t));
  check("edit: posts to the same url", t.includes("fetch(location.pathname, { method: 'POST'"));
  check("edit: nothing external", !/\b(src|href)=["']?https?:/.test(t) && !/https?:\/\//.test(t.replace(/<!doctype[^>]*>/, "")));
  const nonce = (t.match(/<script nonce="([^"]+)"/) || [])[1];
  const csp = r.headers.get("content-security-policy") || "";
  check("edit: script nonce matches csp", !!nonce && csp.includes(`'nonce-${nonce}'`) && csp.includes("default-src 'none'"), csp);
  check("edit: bilingual title", t.includes("แก้ไขข้อมูลร้าน · Edit your listing"));

  r = await call(env, `/edit/${token}`);
  j = await r.json();
  check("edit: json without accept", r.status === 200 && j.ok === true && j.claim.note === nasty);

  // What the page's Save sends: every field, empty means clear.
  r = await post(env, `/edit/${token}`, { phone: "082", lineId: "", facebook: "", instagram: "", whatsapp: "", email: "", website: "", hours: "", note: "kept", menu: "" });
  j = await r.json();
  check("edit post: updated and cleared", j.ok === true && j.claim.phone === "082" && j.claim.hours === undefined && j.claim.note === "kept", JSON.stringify(j));
}

/* ---- /suggest — closed / moved / duplicate, with detail ------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  const sug = async (body) => {
    const j = await (await post(env, "/suggest", body)).json();
    return JSON.parse(env.KV.m.get(`sug:${j.id}`).value);
  };
  let rec = await sug({ kind: "closed", what: "shut", detail: "since June", placeId: "cm-x" });
  check("suggest: closed + detail", rec.kind === "closed" && rec.detail === "since June", JSON.stringify(rec));
  rec = await sug({ kind: "moved", what: "moved", detail: "  now on Nimman soi 9 " });
  check("suggest: moved, detail trimmed", rec.kind === "moved" && rec.detail === "now on Nimman soi 9");
  rec = await sug({ kind: "duplicate", what: "twice", detail: "x".repeat(400) });
  check("suggest: duplicate, detail capped at 300", rec.kind === "duplicate" && rec.detail.length === 300);
  rec = await sug({ kind: "correction", what: "typo" });
  check("suggest: no detail → null", rec.kind === "correction" && rec.detail === null);
  rec = await sug({ kind: "closed", what: "shut", detail: { a: 1 } });
  check("suggest: non-string detail → null", rec.detail === null);
  rec = await sug({ kind: "nonsense", what: "?" });
  check("suggest: unknown kind → other", rec.kind === "other");
}

/* ---- scheduled(): the alpha sweep ----------------------------------- */
{
  const day = 24 * 3600 * 1000;
  const env = {
    KV: makeKV(), MAIL: makeMail(false),
    PHOTOS: makeR2([
      { key: "alpha/old1/1.jpg", uploaded: new Date(Date.now() - 200 * day) },
      { key: "alpha/old2/1.png", uploaded: new Date(Date.now() - 181 * day) },
      { key: "alpha/new1/1.jpg", uploaded: new Date(Date.now() - 1 * day) },
      { key: "alpha/new2/1.jpg", uploaded: new Date(Date.now() - 179 * day) },
      { key: "inbox/sub/1.jpg", uploaded: new Date(Date.now() - 400 * day) },
    ]),
  };
  check("scheduled: exported", typeof worker.scheduled === "function");
  await worker.scheduled({ cron: "17 3 * * *", scheduledTime: Date.now() }, env, { waitUntil() {} });
  const left = [...env.PHOTOS.store.keys()].sort();
  check("sweep: only old alpha objects gone", JSON.stringify(left) === JSON.stringify(["alpha/new1/1.jpg", "alpha/new2/1.jpg", "inbox/sub/1.jpg"]), left.join());
}

/* ---- a trusted sender is approved on arrival, no mail --------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  await env.KV.put("lsttrust:clarence@example.com", JSON.stringify({ by: "Nan", at: "2026-09-27" }));
  const row = { name: "Baan Trust", kind: "house", offer: "sale", price: "4.2M", agency: "C", contact: "x" };
  let j = await (await post(env, "/listing", { listings: [row], from: "Clarence@Example.com" })).json();
  let sub = JSON.parse(env.KV.m.get(`lst:${j.id}`).value ?? env.KV.m.get(`lst:${j.id}`));
  check("trusted: approved on arrival", sub.status === "approved" && /trusted/.test(sub.approvedBy || ""), JSON.stringify(sub.status));
  check("trusted: no per-submission mail", env.MAIL.sent.length === 0);
  j = await (await post(env, "/listing", { listings: [row], from: "someone@example.com" })).json();
  sub = JSON.parse(env.KV.m.get(`lst:${j.id}`).value ?? env.KV.m.get(`lst:${j.id}`));
  check("untrusted: waits for the tap, and mails", sub.status === "new" && env.MAIL.sent.length === 1);
}

/* ---- the 404 names /health ----------------------------------------- */
{
  const env = { KV: makeKV(), PHOTOS: makeR2([]), MAIL: makeMail(false) };
  const j = await (await call(env, "/nope")).json();
  check("404 lists /health", Array.isArray(j.endpoints) && j.endpoints.includes("/health"));
}

console.log(`${pass} passed, ${failures.length} failed`);
if (failures.length) { console.log("failures:", failures); process.exit(1); }
console.log("all claims-worker checks passed");
