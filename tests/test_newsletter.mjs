/* The weekly issue's Worker side (publish/newsletter.js), under plain node.
 * A stand-in D1 and a stubbed fetch: the gate, the per-address unsubscribe link,
 * the no-double-send ledger, and unsubscribe itself.
 *
 *     node tests/test_newsletter.mjs
 */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const N = await import(join(ROOT, "publish/newsletter.js"));

let failures = 0;
async function t(name, fn) {
  try { await fn(); console.log("  ok   " + name); }
  catch (e) { failures++; console.log("  FAIL " + name + "\n       " + (e && e.stack || e)); }
}
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what || "value"}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const must = (c, m) => { if (!c) throw new Error(m); };

class FakeD1 {
  constructor(subs) { this.subs = new Map(subs.map((s) => [s.email, { perks: "{}", ...s }])); this.sends = new Map(); }
  prepare(sql) { return new Stmt(this, sql.replace(/\s+/g, " ").trim()); }
  async batch(stmts) { for (const s of stmts) await s.run(); return []; }
}
class Stmt {
  constructor(db, sql) { this.db = db; this.sql = sql; this.args = []; }
  bind(...a) { this.args = a; return this; }
  async all() {
    if (this.sql.startsWith("SELECT email, token FROM subscribers"))
      return { results: [...this.db.subs.values()].filter((s) => s.status === "confirmed").map(({ email, token }) => ({ email, token })) };
    if (this.sql.startsWith("SELECT email FROM newsletter_sends"))
      return { results: [...this.db.sends.keys()].filter((k) => k.startsWith(this.args[0] + "|")).map((k) => ({ email: k.split("|")[1] })) };
    throw new Error("unexpected all(): " + this.sql);
  }
  async run() {
    const s = this.sql;
    if (s.startsWith("INSERT OR IGNORE INTO newsletter_sends")) { this.db.sends.set(this.args[0] + "|" + this.args[1], this.args[3]); return {}; }
    if (s.startsWith("DELETE FROM newsletter_sends")) { this.db.sends.delete(this.args[0] + "|" + this.args[1]); return {}; }
    if (s.startsWith("UPDATE subscribers SET status = 'unsubscribed'")) {
      let changes = 0;
      for (const r of this.db.subs.values()) if (r.token === this.args[1] && r.status !== "unsubscribed") { r.status = "unsubscribed"; changes++; }
      return { meta: { changes } };
    }
    throw new Error("unexpected run(): " + s);
  }
  async first() {
    for (const r of this.db.subs.values()) if (r.token === this.args[0]) return { status: r.status };
    return null;
  }
}

const SUBS = [
  { email: "a@example.com", token: "aaaaaaaaaaaaaaaa", status: "confirmed" },
  { email: "b@example.com", token: "bbbbbbbbbbbbbbbb", status: "confirmed" },
  { email: "p@example.com", token: "cccccccccccccccc", status: "pending" },
  { email: "events@motdang.net", token: "dddddddddddddddd", status: "pending" },
];
const ISSUE = { issue: "2026-10-19", subject: "s", text: "hi\nUnsubscribe: {{UNSUB}}\n", html: '<a href="{{UNSUB}}">u</a>' };
let calls = [];
globalThis.fetch = async (url, init) => { calls.push(JSON.parse(init.body)); return new Response("{}", { status: 200 }); };
const post = (body, tok = "T") => new Request("https://motdang.net/newsletter/send", {
  method: "POST", headers: { authorization: "Bearer " + tok, "content-type": "application/json" }, body: JSON.stringify(body) });
const U = new URL("https://motdang.net/newsletter/send");

await t("without the token the send path is a 404", async () => {
  const env = { NEWSLETTER_TOKEN: "T", RESEND_KEY: "k", SUBSCRIBERS: new FakeD1(SUBS) };
  eq((await N.newsletter(post(ISSUE, "wrong"), env, U)).status, 404);
});

await t("gate off: only the test address gets it, the confirmed list does not", async () => {
  calls = [];
  const env = { NEWSLETTER_TOKEN: "T", RESEND_KEY: "k", NEWSLETTER_TEST: "events@motdang.net", SUBSCRIBERS: new FakeD1(SUBS) };
  const out = await (await N.newsletter(post(ISSUE), env, U)).json();
  eq(out.live, false); eq(out.sent, 1);
  eq(calls.length, 1); eq(calls[0].length, 1); eq(calls[0][0].to[0], "events@motdang.net");
});

await t("gate on: every confirmed address, each with its own unsubscribe link and header", async () => {
  calls = [];
  const env = { NEWSLETTER_TOKEN: "T", RESEND_KEY: "k", NEWSLETTER_LIVE: "true", SUBSCRIBERS: new FakeD1(SUBS) };
  const out = await (await N.newsletter(post(ISSUE), env, U)).json();
  eq(out.sent, 2);
  const msgs = calls.flat();
  eq(msgs.length, 2);
  const a = msgs.find((m) => m.to[0] === "a@example.com");
  must(a.text.includes("/subscribe/unsubscribe?token=aaaaaaaaaaaaaaaa"), "a's text lacks a's link");
  must(!a.text.includes("bbbb"), "a's mail carries b's token");
  must(a.headers["List-Unsubscribe"].includes("aaaaaaaaaaaaaaaa"), "no List-Unsubscribe header");
  must(!msgs.some((m) => m.to[0] === "p@example.com"), "a pending address was sent to");
});

await t("the same issue twice sends nothing the second time", async () => {
  calls = [];
  const env = { NEWSLETTER_TOKEN: "T", RESEND_KEY: "k", NEWSLETTER_LIVE: "true", SUBSCRIBERS: new FakeD1(SUBS) };
  await N.newsletter(post(ISSUE), env, U);
  const out = await (await N.newsletter(post(ISSUE), env, U)).json();
  eq(out.sent, 0); eq(out.already, 2); eq(calls.length, 1);
});

await t("a refused batch is taken off the ledger, so the next run tries again", async () => {
  const env = { NEWSLETTER_TOKEN: "T", RESEND_KEY: "k", NEWSLETTER_LIVE: "true", SUBSCRIBERS: new FakeD1(SUBS) };
  const ok = globalThis.fetch;
  globalThis.fetch = async () => new Response("nope", { status: 500 });
  const out = await (await N.newsletter(post(ISSUE), env, U)).json();
  globalThis.fetch = ok;
  eq(out.ok, false); eq(out.sent, 0); eq(env.SUBSCRIBERS.sends.size, 0);
});

await t("unsubscribe: GET shows a button and changes nothing; POST takes the address off", async () => {
  const env = { SUBSCRIBERS: new FakeD1(SUBS) };
  const u = new URL("https://motdang.net/subscribe/unsubscribe?token=aaaaaaaaaaaaaaaa");
  const g = await N.newsletter(new Request(u), env, u);
  eq(g.status, 200); must((await g.text()).includes("<form method=\"post\""), "no button");
  eq(env.SUBSCRIBERS.subs.get("a@example.com").status, "confirmed");
  const p = await N.newsletter(new Request(u, { method: "POST" }), env, u);
  eq(p.status, 200);
  eq(env.SUBSCRIBERS.subs.get("a@example.com").status, "unsubscribed");
  const bad = new URL("https://motdang.net/subscribe/unsubscribe?token=zz");
  eq((await N.newsletter(new Request(bad, { method: "POST" }), env, bad)).status, 400);
});

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
