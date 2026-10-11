/* The mailing list, run under plain node — no Worker, no D1, no network.
 *
 * A small in-memory stand-in for the D1 binding answers the four statements
 * publish/subscribe.js issues, so the real code path runs: PENDING → CONFIRMED,
 * a token is required, and with the gate off the confirmation mail is composed
 * while the mail binding stays untouched.
 *
 *     node tests/test_subscribe.mjs
 */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const S = await import(join(ROOT, "publish/subscribe.js"));

let failures = 0;
function t(name, fn) {
  return Promise.resolve()
    .then(fn)
    .then(() => console.log("  ok   " + name))
    .catch((e) => { failures++; console.log("  FAIL " + name + "\n       " + (e && e.stack || e)); });
}
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what || "value"}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const must = (c, m) => { if (!c) throw new Error(m); };

/* The stand-in. Rows keyed by email; each prepared statement is recognised by
 * the shape of its SQL — the same four subscribe.js sends. */
class FakeD1 {
  constructor() { this.rows = new Map(); }
  prepare(sql) { return new Stmt(this, sql.replace(/\s+/g, " ").trim()); }
}
class Stmt {
  constructor(db, sql) { this.db = db; this.sql = sql; this.args = []; }
  bind(...a) { this.args = a; return this; }
  async run() {
    const s = this.sql;
    if (s.startsWith("INSERT INTO subscribers")) {
      const [email, token, source, lang, created_at] = this.args;
      const ex = this.db.rows.get(email);
      if (!ex) {
        this.db.rows.set(email, { email, status: "pending", token, source, lang, created_at, confirmed_at: null, perks: "{}" });
      } else {
        ex.token = token; ex.source = source; ex.lang = lang; ex.created_at = created_at;
        ex.status = ex.status === "confirmed" ? "confirmed" : "pending";
      }
      return { success: true, meta: { changes: 1 } };
    }
    if (s.startsWith("UPDATE subscribers SET status = 'confirmed'")) {
      const [now, token] = this.args;
      let changes = 0;
      for (const r of this.db.rows.values())
        if (r.token === token && r.status === "pending") { r.status = "confirmed"; r.confirmed_at = now; changes++; }
      return { success: true, meta: { changes } };
    }
    return { success: true, meta: { changes: 0 } };
  }
  async first() {
    if (this.sql.includes("WHERE email = ?")) {
      const r = this.db.rows.get(this.args[0]);
      return r ? { status: r.status } : null;
    }
    if (this.sql.includes("WHERE token = ?")) {
      for (const r of this.db.rows.values()) if (r.token === this.args[0]) return { status: r.status };
      return null;
    }
    return null;
  }
}

const nowIso = () => new Date().toISOString();
const formPost = (fields) => new Request("https://motdang.net/subscribe", {
  method: "POST",
  headers: { "content-type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams(fields).toString(),
});

await t("an email is normalised, and rubbish is refused", () => {
  eq(S.normalizeEmail("  Nan@MotDang.NET "), "nan@motdang.net");
  eq(S.normalizeEmail("no-at-sign"), "");
  eq(S.normalizeEmail("a@b"), "");            // no dot in the domain
  eq(S.normalizeEmail(""), "");
  must(S.normalizeEmail("a@b.co"), "a plain address should pass");
});

await t("a token is 128 bits of hex and does not repeat", () => {
  const a = S.newToken(), b = S.newToken();
  must(/^[a-f0-9]{32}$/.test(a), "token shape: " + a);
  must(a !== b, "two tokens collided");
});

await t("PENDING is written, then the token flips it to CONFIRMED", async () => {
  const db = new FakeD1();
  const token = S.newToken();
  const status = await S.storePending(db, { email: "reader@example.com", token, source: "test", lang: "both", now: nowIso() });
  eq(status, "pending", "a fresh sign-up is pending");
  eq(db.rows.get("reader@example.com").status, "pending");

  const res = await S.confirmToken(db, token, nowIso());
  eq(res.ok, true, "confirm should succeed");
  eq(res.already, false);
  eq(db.rows.get("reader@example.com").status, "confirmed", "the row did not flip");
  must(db.rows.get("reader@example.com").confirmed_at, "confirmed_at was not set");
});

await t("a token is required — an empty or malformed one confirms nothing", async () => {
  const db = new FakeD1();
  await S.storePending(db, { email: "x@example.com", token: S.newToken(), source: "t", lang: "both", now: nowIso() });
  eq((await S.confirmToken(db, "", nowIso())).ok, false, "empty token was accepted");
  eq((await S.confirmToken(db, "not-hex!", nowIso())).ok, false, "malformed token was accepted");
  eq((await S.confirmToken(db, "deadbeef", nowIso())).ok, false, "unknown token was accepted");
  eq(db.rows.get("x@example.com").status, "pending", "the row was flipped by a bad token");
});

await t("confirming twice says 'already', not an error", async () => {
  const db = new FakeD1();
  const token = S.newToken();
  await S.storePending(db, { email: "y@example.com", token, source: "t", lang: "both", now: nowIso() });
  eq((await S.confirmToken(db, token, nowIso())).already, false);
  const again = await S.confirmToken(db, token, nowIso());
  eq(again.ok, true); eq(again.already, true, "a second confirm should read as already-confirmed");
});

await t("re-subscribing a confirmed address does not knock it back to pending", async () => {
  const db = new FakeD1();
  const token = S.newToken();
  await S.storePending(db, { email: "z@example.com", token, source: "t", lang: "both", now: nowIso() });
  await S.confirmToken(db, token, nowIso());
  const status = await S.storePending(db, { email: "z@example.com", token: S.newToken(), source: "t2", lang: "en", now: nowIso() });
  eq(status, "confirmed", "a confirmed address must stay confirmed");
});

await t("with the gate OFF the confirm mail is composed but not handed to the binding", async () => {
  const env = { MAILING_LIST_LIVE: "false" };            // MAIL binding deliberately absent
  const r = await S.sendConfirm(env, { email: "reader@example.com", lang: "both" }, "https://motdang.net/subscribe/confirm?token=abc123");
  eq(r.sent, false, "the gate let a send through");
  eq(r.reason, "gated-off");
});

await t("the gate is off when the flag is unset entirely", async () => {
  const r = await S.sendConfirm({}, { email: "a@b.co" }, "https://motdang.net/subscribe/confirm?token=abc123");
  eq(r.sent, false); eq(r.reason, "gated-off");
});

await t("gate OFF never calls Resend (fetch stays untouched)", async () => {
  const realFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; return { ok: true, json: async () => ({}) }; };
  try {
    const r = await S.sendConfirm({ MAILING_LIST_LIVE: "false", RESEND_KEY: "re_test" },
      { email: "a@b.co" }, "https://x/confirm?token=abc123");
    eq(r.sent, false); eq(r.reason, "gated-off");
    eq(calls, 0, "Resend was called while the gate was off");
  } finally { globalThis.fetch = realFetch; }
});

await t("even with the flag on, no RESEND_KEY means no send (and no key in code)", async () => {
  const r = await S.sendConfirm({ MAILING_LIST_LIVE: "true" }, { email: "a@b.co" }, "https://x/confirm?token=abc123");
  eq(r.sent, false, "a send happened with no key");
  eq(r.reason, "no-resend-key");
});

await t("flag ON + RESEND_KEY posts to Resend as nan@motdang.net", async () => {
  const realFetch = globalThis.fetch;
  let seen = null;
  globalThis.fetch = async (url, opts) => {
    seen = { url, opts };
    return { ok: true, json: async () => ({ id: "resend-123" }) };
  };
  try {
    const r = await S.sendConfirm({ MAILING_LIST_LIVE: "true", RESEND_KEY: "re_secret" },
      { email: "reader@example.com", lang: "both" }, "https://motdang.net/subscribe/confirm?token=abc123");
    eq(r.sent, true, "the open gate did not send"); eq(r.id, "resend-123");
    eq(seen.url, "https://api.resend.com/emails");
    eq(seen.opts.headers.authorization, "Bearer re_secret", "the key was not passed as a Bearer");
    const body = JSON.parse(seen.opts.body);
    must(body.from.includes("nan@motdang.net"), "the From is not nan@motdang.net");
    eq(body.to, "reader@example.com");
    must(body.subject.includes("Confirm"), "the subject is missing");
    must(body.text.includes("token=abc123"), "the confirm link is missing from the body");
  } finally { globalThis.fetch = realFetch; }
});

await t("the composed mail carries the confirm link and is base64 text", () => {
  const msg = S.composeConfirm({ email: "reader@example.com" }, "https://motdang.net/subscribe/confirm?token=TOK", "id1");
  must(/Content-Transfer-Encoding: base64/.test(msg), "not base64");
  must(/To: <reader@example.com>/.test(msg), "recipient missing");
  const body = msg.split("\r\n\r\n")[1];
  must(Buffer.from(body, "base64").toString("utf8").includes("subscribe/confirm?token=TOK"), "the confirm link is not in the body");
});

await t("POST /subscribe with consent stores a pending row; gate off → 'saved'", async () => {
  const env = { SUBSCRIBERS: new FakeD1(), MAILING_LIST_LIVE: "false" };
  const res = await S.handleSubscribe(formPost({ email: "new@example.com", consent: "yes", source: "test" }),
    env, new URL("https://motdang.net/subscribe"));
  eq(res.status, 200, "subscribe did not accept a valid sign-up");
  const html = await res.text();
  must(html.includes("Request saved"), "the gated-off page should say the request is saved");
  const row = env.SUBSCRIBERS.rows.get("new@example.com");
  must(row && row.status === "pending", "no pending row was written");
});

await t("POST /subscribe with the box unticked is refused — no row", async () => {
  const env = { SUBSCRIBERS: new FakeD1(), MAILING_LIST_LIVE: "false" };
  const res = await S.handleSubscribe(formPost({ email: "nope@example.com", source: "test" }),
    env, new URL("https://motdang.net/subscribe"));
  eq(res.status, 400, "an unticked consent box was accepted");
  must((await res.text()).includes("Consent needed"), "wrong refusal");
  eq(env.SUBSCRIBERS.rows.size, 0, "a row was written without consent");
});

await t("POST /subscribe with a bad email is refused", async () => {
  const env = { SUBSCRIBERS: new FakeD1(), MAILING_LIST_LIVE: "false" };
  const res = await S.handleSubscribe(formPost({ email: "not-an-email", consent: "yes" }),
    env, new URL("https://motdang.net/subscribe"));
  eq(res.status, 400);
  eq(env.SUBSCRIBERS.rows.size, 0);
});

await t("GET /subscribe/confirm?token=… confirms the pending row", async () => {
  const env = { SUBSCRIBERS: new FakeD1(), MAILING_LIST_LIVE: "false" };
  await S.handleSubscribe(formPost({ email: "flow@example.com", consent: "yes" }),
    env, new URL("https://motdang.net/subscribe"));
  const token = env.SUBSCRIBERS.rows.get("flow@example.com").token;
  const res = await S.handleConfirm(new Request("https://motdang.net/subscribe/confirm?token=" + token),
    env, new URL("https://motdang.net/subscribe/confirm?token=" + token));
  eq(res.status, 200);
  must((await res.text()).includes("Confirmed"), "the confirm page did not confirm");
  eq(env.SUBSCRIBERS.rows.get("flow@example.com").status, "confirmed");
});

await t("the sign-up block has no pre-checked consent and posts to /subscribe", () => {
  const block = S.signupBlock({ source: "home" });
  must(/action="\/subscribe" method="post"/.test(block), "the block does not post to /subscribe");
  must(/name="consent"/.test(block) && /required/.test(block), "no required consent box");
  must(!/checked/.test(block), "consent must never be pre-checked");
  must(block.includes("home"), "the source breadcrumb is missing");
});

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
