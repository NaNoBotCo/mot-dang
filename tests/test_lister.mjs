/* The listing-agent gate, run under plain node — no Worker, no network.
 *
 * The SUBSCRIBERS binding is a stand-in over node:sqlite in memory, with both
 * migrations applied, so publish/lister.js runs its own SQL. Resend is a
 * counted fetch stub; MAIL is a recorder. The claims Worker (worker/worker.js)
 * is imported for real, with "cloudflare:email" resolved to a small class, and
 * driven through its fetch handler against in-memory KV and R2.
 *
 *     node tests/test_lister.mjs
 */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { registerHooks } from "node:module";

process.removeAllListeners("warning");           // node:sqlite's experimental notice
const { DatabaseSync } = await import("node:sqlite");

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

/* "cloudflare:email" exists only inside a Worker. */
registerHooks({
  resolve(spec, ctx, next) {
    if (spec === "cloudflare:email")
      return { url: "data:text/javascript,export class EmailMessage{constructor(f,t,r){this.from=f;this.to=t;this.raw=r}}",
               shortCircuit: true };
    return next(spec, ctx);
  },
});

const L = await import(join(ROOT, "publish/lister.js"));
const B = await import(join(ROOT, "worker/lister_bearer.js"));
const CLAIMS = (await import(join(ROOT, "worker/worker.js"))).default;

let failures = 0;
function t(name, fn) {
  return Promise.resolve().then(fn)
    .then(() => console.log("  ok   " + name))
    .catch((e) => { failures++; console.log("  FAIL " + name + "\n       " + (e && e.stack || e)); });
}
const eq = (a, b, what) => { if (a !== b) throw new Error(`${what || "value"}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const must = (c, m) => { if (!c) throw new Error(m); };

/* ---------------------------------------------------------------- stand-ins */
class D1 {
  constructor() {
    this.db = new DatabaseSync(":memory:");
    for (const f of ["0001_subscribers.sql", "0002_listers.sql", "0003_lister_checks.sql"])
      this.db.exec(readFileSync(join(ROOT, "publish/migrations", f), "utf8"));
  }
  prepare(sql) { return new Stmt(this.db, sql); }
  row(sql, ...a) { const r = this.db.prepare(sql).get(...a); return r ? { ...r } : null; }
}
class Stmt {
  constructor(db, sql) { this.db = db; this.sql = sql; this.args = []; }
  bind(...a) { this.args = a; return this; }
  async run() { const r = this.db.prepare(this.sql).run(...this.args); return { success: true, meta: { changes: Number(r.changes) } }; }
  async first() { const r = this.db.prepare(this.sql).get(...this.args); return r ? { ...r } : null; }
  async all() { return { results: this.db.prepare(this.sql).all(...this.args).map((r) => ({ ...r })) }; }
}
const mailBox = () => ({ sent: [], async send(m) { this.sent.push(m); } });
const decode = (raw) => Buffer.from(raw.split("\r\n\r\n")[1].replace(/\r\n/g, ""), "base64").toString("utf8");

/* Resend, counted. */
let resendCalls = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opts) => {
  resendCalls.push({ url, body: JSON.parse(opts.body) });
  return { ok: true, status: 200, json: async () => ({ id: "resend-x" }) };
};

const SECRET = "test-secret-" + "a".repeat(20);
const ORIGIN = "https://motdang.net";
const env = (over) => ({ SUBSCRIBERS: new D1(), MAIL: mailBox(), MAILING_LIST_LIVE: "false",
                         LISTER_SECRET: SECRET, LISTER_INVITE: "operator", ...(over || {}) });
const go = (e, method, path, fields, headers) => {
  const init = { method, headers: { ...(headers || {}) } };
  if (fields) {
    init.headers["content-type"] = "application/x-www-form-urlencoded";
    init.body = new URLSearchParams(fields).toString();
  }
  const req = new Request(ORIGIN + path, init);
  return L.lister(req, e, new URL(req.url));
};
const APPLY = { email: "Agent@Example.com", name: "Somchai P.", office: "Ping Valley Property Co., Ltd.",
                phone: "081 234 5678", province: "cm", newsletter: "yes", reuse: "yes" };
const countRows = (e) => [e.SUBSCRIBERS.row("SELECT COUNT(*) n FROM subscribers").n,
                          e.SUBSCRIBERS.row("SELECT COUNT(*) n FROM listers").n];

/* join → confirm, returning the env and the lister row. */
async function joined(over, apply, e0) {
  const e = e0 || env(over);
  await go(e, "POST", "/listings/join", apply || APPLY);
  const email = String((apply || APPLY).email).toLowerCase();
  const tok = e.SUBSCRIBERS.row("SELECT token FROM subscribers WHERE email = ?", email).token;
  const page = await (await go(e, "GET", "/listings/join/confirm?token=" + tok)).text();
  return { e, page, row: e.SUBSCRIBERS.row("SELECT * FROM listers WHERE email = ?", email) };
}
async function invited(over) {
  const { e, row } = await joined(over);
  await go(e, "GET", "/listings/invite/" + row.invite_token);
  return { e, row: e.SUBSCRIBERS.row("SELECT * FROM listers") };
}
async function signedIn(over) {
  const { e, row } = await invited(over);
  const res = await go(e, "GET", "/listings/signin?token=" + row.signin_token);
  const cookie = res.headers.get("set-cookie").split(";")[0];
  return { e, row, cookie, res };
}

/* ---------------------------------------------------------------- join */
await t("join refuses without the newsletter box — no rows", async () => {
  const e = env();
  const { newsletter, ...rest } = APPLY;
  const res = await go(e, "POST", "/listings/join", rest);
  eq(res.status, 400);
  must((await res.text()).includes("Newsletter box not ticked"), "wrong refusal");
  eq(countRows(e).join(), "0,0", "a row was written");
});

await t("join refuses without the reuse box — no rows", async () => {
  const e = env();
  const { reuse, ...rest } = APPLY;
  const res = await go(e, "POST", "/listings/join", rest);
  eq(res.status, 400);
  must((await res.text()).includes("CC BY 4.0"), "wrong refusal");
  eq(countRows(e).join(), "0,0", "a row was written");
});

await t("join refuses with neither phone nor LINE, and with a bad email", async () => {
  const e = env();
  eq((await go(e, "POST", "/listings/join", { ...APPLY, phone: "" })).status, 400);
  eq((await go(e, "POST", "/listings/join", { ...APPLY, email: "nope" })).status, 400);
  eq(countRows(e).join(), "0,0");
});

await t("the join page: Thai first, both boxes required and unticked", async () => {
  const res = await go(env(), "GET", "/listings/join");
  eq(res.status, 200);
  const html = await res.text();
  must(html.indexOf("สมัครลงประกาศ") < html.indexOf("Join as a listing agent"), "Thai is not first");
  must(/name="newsletter"[^>]*required/.test(html) && /name="reuse"[^>]*required/.test(html), "a box is not required");
  must(!/checked/.test(html), "a box is pre-ticked");
  must(!/[\u{1F300}-\u{1FAFF}✅✋⚠]/u.test(html), "emoji on the page");
});

await t("join writes a pending subscriber (source lister) and an applied lister; gate off sends nothing", async () => {
  const e = env(); resendCalls = [];
  const res = await go(e, "POST", "/listings/join", APPLY);
  eq(res.status, 200);
  must((await res.text()).includes("Application saved"), "gate-off page should say saved");
  const s = e.SUBSCRIBERS.row("SELECT * FROM subscribers");
  eq(s.email, "agent@example.com"); eq(s.status, "pending"); eq(s.source, "lister");
  const l = e.SUBSCRIBERS.row("SELECT * FROM listers");
  eq(l.status, "applied"); eq(l.reuse_consent, 1); eq(l.provinces, "cm");
  eq(l.office_key, "ping-valley-property");
  must(/^[a-f0-9]{32}$/.test(l.member_key), "member_key shape");
  eq(resendCalls.length, 0, "Resend was called with the gate off");
  eq(e.MAIL.sent.length, 0, "Nan was mailed before a confirm");
});

await t("gate ON: the confirm mail goes to the applicant through Resend", async () => {
  const e = env({ MAILING_LIST_LIVE: "true", RESEND_KEY: "re_x" }); resendCalls = [];
  const res = await go(e, "POST", "/listings/join", APPLY);
  must((await res.text()).includes("Check your email"), "gate-on page");
  eq(resendCalls.length, 1);
  eq(resendCalls[0].body.to, "agent@example.com");
  must(resendCalls[0].body.text.includes("/listings/join/confirm?token="), "confirm link missing");
});

await t("confirm → subscriber confirmed, lister confirmed, operator mail to Nan with both links", async () => {
  const { e, row } = await joined();
  eq(e.SUBSCRIBERS.row("SELECT status FROM subscribers").status, "confirmed");
  eq(row.status, "confirmed");
  must(row.invite_token && row.decline_token, "operator tokens missing");
  eq(e.MAIL.sent.length, 1, "operator mail count");
  const m = e.MAIL.sent[0];
  eq(m.to, "530kings@proton.me"); eq(m.from, "listings@motdang.net");
  const body = decode(m.raw);
  must(body.includes(`/listings/invite/${row.invite_token}`), "INVITE link missing");
  must(body.includes(`/listings/decline/${row.decline_token}`), "DECLINE link missing");
  must(body.includes("Somchai P.") && body.includes("CC BY 4.0: yes"), "details missing");
});

await t("a bad confirm token moves nothing", async () => {
  const e = env();
  await go(e, "POST", "/listings/join", APPLY);
  eq((await go(e, "GET", "/listings/join/confirm?token=deadbeef")).status, 400);
  eq(e.SUBSCRIBERS.row("SELECT status FROM listers").status, "applied");
});

/* ---------------------------------------------------------------- invite */
await t("invite → status invited, perks.lister set, invite mail composed (gate off: not sent)", async () => {
  resendCalls = [];
  const { e, row } = await invited();
  eq(row.status, "invited");
  must(row.signin_token, "no sign-in token after invite");
  const perks = JSON.parse(e.SUBSCRIBERS.row("SELECT perks FROM subscribers").perks);
  eq(perks.lister.member, row.member_key); eq(perks.lister.office, row.office_key);
  eq(resendCalls.length, 0, "Resend called with the gate off");
  const again = await go(e, "GET", "/listings/invite/" + row.invite_token);
  must((await again.text()).includes("Already invited"), "second tap");
});

/* ---------------------------------------------------------------- sanity check */
await t("auto + checks pass → invited automatically, invited_by auto, Nan mailed nothing", async () => {
  resendCalls = [];
  const { e, row, page } = await joined({ LISTER_INVITE: "auto" });
  eq(row.status, "invited"); eq(row.invited_by, "auto"); eq(row.held_reasons, null);
  must(page.includes("Confirmed and invited"), "applicant page");
  eq(e.MAIL.sent.length, 0, "auto mode sent Nan a per-event mail");
  eq(resendCalls.length, 0, "invite mail left the gate while it is off");
  must(JSON.parse(e.SUBSCRIBERS.row("SELECT perks FROM subscribers").perks).lister, "perks.lister");
});

await t("auto + gate ON: the invite mail goes to the applicant, still nothing to Nan", async () => {
  resendCalls = [];
  const { e } = await joined({ LISTER_INVITE: "auto", MAILING_LIST_LIVE: "true", RESEND_KEY: "re_x" });
  eq(resendCalls.map((c) => c.body.subject.includes("Invited")).filter(Boolean).length, 1, "invite mail");
  eq(e.MAIL.sent.length, 0);
});

const HOLDS = [
  ["disposable email domain", { email: "x@mailinator.com" }],
  ["disposable email domain", { email: "x@eu.yopmail.com" }],
  ["name is too short", { name: "A" }],
  ["office is the email address", { office: "agent@example.com" }],
  ["name is the email address", { name: "agent" }],
  ["office contains a URL", { office: "Best Homes https://spam.example" }],
  ["office contains a URL", { office: "cheapvillas.xyz" }],
  ["phone is not a Thai number and no plausible LINE ID", { phone: "+1 415 555 0100", line_id: "" }],
  ["phone is not a Thai number and no plausible LINE ID", { phone: "12", line_id: "x" }],
  ["name looks like keyboard noise", { name: "sdfghjkl" }],
  ["name looks like keyboard noise", { name: "asdf qwer" }],
  ["office looks like keyboard noise", { office: "ฟหกดเ" }],
  ["office looks like keyboard noise", { office: "abcกขค" }],
  ["name looks like keyboard noise", { name: "aaaaa" }],
];
for (const [reason, over] of HOLDS) {
  await t(`held: ${reason} (${JSON.stringify(over)})`, async () => {
    const apply = { ...APPLY, ...over };
    const { e, row, page } = await joined({ LISTER_INVITE: "auto" }, apply);
    eq(row.status, "confirmed", "a failing applicant was invited");
    must(JSON.parse(row.held_reasons || "[]").includes(reason), `reasons ${row.held_reasons}`);
    must(page.includes("Email confirmed") && !page.includes("invited"), "applicant page gives the hold away");
    eq(e.MAIL.sent.length, 0, "auto mode mailed Nan");
    // her links still work on a held row
    const inv = await go(e, "GET", "/listings/invite/" + row.invite_token);
    must((await inv.text()).includes("Invited"), "INVITE on a held row");
    eq(e.SUBSCRIBERS.row("SELECT invited_by FROM listers WHERE member_key = ?", row.member_key).invited_by, "operator");
  });
}

await t("a Thai name, a Thai office, LINE only, a +66 number: all pass", async () => {
  for (const over of [
    { name: "สมชาย ใจดี", office: "บริษัท บ้านสวน เชียงใหม่ จำกัด" },
    { office: "ร้าน ABC Home", phone: "", line_id: "@pingvalley" },
    { phone: "+66 81 234 5678" }, { phone: "053-123-456" },
    { name: "Nguyen Thi Mai", office: "Chiang Rai Land" },
  ]) {
    const { row } = await joined({ LISTER_INVITE: "auto" }, { ...APPLY, ...over });
    eq(row.held_reasons, null, JSON.stringify(over));
    eq(row.status, "invited", JSON.stringify(over));
  }
});

await t("more than IP_DAY_MAX applications from one IP in a day: the next is held", async () => {
  const e = env({ LISTER_INVITE: "auto" });
  for (let i = 0; i <= L.IP_DAY_MAX; i++) {
    const init = { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded", "cf-connecting-ip": "203.0.113.9" },
                   body: new URLSearchParams({ ...APPLY, email: `a${i}@example.com` }).toString() };
    const req = new Request(ORIGIN + "/listings/join", init);
    await L.lister(req, e, new URL(req.url));
    const tok = e.SUBSCRIBERS.row("SELECT token FROM subscribers WHERE email = ?", `a${i}@example.com`).token;
    await go(e, "GET", "/listings/join/confirm?token=" + tok);
  }
  const rows = e.SUBSCRIBERS.db.prepare("SELECT email, status, held_reasons, ip_hash FROM listers ORDER BY created_at, email").all();
  must(rows.every((r) => r.ip_hash && r.ip_hash !== "203.0.113.9"), "the IP was written, or not hashed");
  eq(rows.filter((r) => r.status === "invited").length, L.IP_DAY_MAX, "first four invited");
  const held = rows.find((r) => r.status === "confirmed");
  must(held && held.held_reasons.includes("applications from one IP"), "fifth not held: " + JSON.stringify(rows));
});

await t("operator mode: Nan's per-applicant mail lists the failed checks", async () => {
  const { e } = await joined({ LISTER_INVITE: "operator" }, { ...APPLY, email: "x@mailinator.com" });
  const body = decode(e.MAIL.sent[0].raw);
  must(body.includes("checks failed: disposable email domain"), body);
});

await t("rows record the approved wording version", async () => {
  const { row } = await joined();
  eq(row.consent_version, "2026-09-27");
});

await t("decline before invite → declined; the invite link then refuses", async () => {
  const { e, row } = await joined();
  await go(e, "GET", "/listings/decline/" + row.decline_token);
  eq(e.SUBSCRIBERS.row("SELECT status FROM listers").status, "declined");
  eq((await go(e, "GET", "/listings/invite/" + row.invite_token)).status, 409);
});

await t("re-joining an invited address: same reply, state kept", async () => {
  const { e } = await invited();
  const fresh = env();
  const a = await (await go(fresh, "POST", "/listings/join", { ...APPLY, email: "new@example.com" })).text();
  const b = await (await go(e, "POST", "/listings/join", { ...APPLY, name: "Someone Else" })).text();
  eq(a, b, "the reply differs for a known address");
  const l = e.SUBSCRIBERS.row("SELECT * FROM listers");
  eq(l.status, "invited"); eq(l.full_name, "Somchai P.");
});

/* ---------------------------------------------------------------- sign-in */
await t("sign-in POST: the same reply for invited, applied and unknown addresses", async () => {
  for (const live of ["false", "true"]) {
    const over = { MAILING_LIST_LIVE: live, RESEND_KEY: "re_x" };
    const { e } = await invited(over);
    const p = await joined(over);
    resendCalls = [];
    const r1 = await go(e, "POST", "/listings/signin", { email: "agent@example.com" });
    const r2 = await go(e, "POST", "/listings/signin", { email: "stranger@example.com" });
    const r3 = await go(p.e, "POST", "/listings/signin", { email: "agent@example.com" });
    const [b1, b2, b3] = [await r1.text(), await r2.text(), await r3.text()];
    eq(r1.status, r2.status); eq(r1.status, r3.status);
    eq(b1, b2, `invited vs unknown differ (live=${live})`);
    eq(b1, b3, `invited vs applied differ (live=${live})`);
    eq(resendCalls.length, live === "true" ? 1 : 0, `Resend calls (live=${live})`);
    if (live === "true") eq(resendCalls[0].body.to, "agent@example.com");
  }
});

await t("sign-in mail is throttled to one a minute", async () => {
  const { e } = await invited({ MAILING_LIST_LIVE: "true", RESEND_KEY: "re_x" });
  resendCalls = [];
  await go(e, "POST", "/listings/signin", { email: "agent@example.com" });
  await go(e, "POST", "/listings/signin", { email: "agent@example.com" });
  eq(resendCalls.length, 1);
});

await t("sign-in link → 303 to add.html with an HttpOnly Secure Lax cookie; single use", async () => {
  const { e, row, res } = await signedIn();
  eq(res.status, 303); eq(res.headers.get("location"), "/listings/add.html");
  const sc = res.headers.get("set-cookie");
  must(/^md_lister=v1\.[a-f0-9]{32}\.\d+\.[A-Za-z0-9_-]+;/.test(sc), "cookie shape: " + sc);
  must(/HttpOnly/.test(sc) && /Secure/.test(sc) && /SameSite=Lax/.test(sc) && /Max-Age=7776000/.test(sc), "cookie flags");
  eq((await go(e, "GET", "/listings/signin?token=" + row.signin_token)).status, 400, "token reused");
});

await t("/lister/me: 200 with a bearer the claims Worker accepts; no CORS header", async () => {
  const { e, row, cookie } = await signedIn();
  const res = await go(e, "GET", "/lister/me", null, { cookie });
  eq(res.status, 200);
  eq(res.headers.get("access-control-allow-origin"), null, "credentialed JSON must not be origin-open");
  const d = await res.json();
  eq(d.member.name, "Somchai P."); eq(d.member.office, "Ping Valley Property Co., Ltd.");
  eq(d.member.email, "agent@example.com");
  const v = await B.verifyListerBearer(d.bearer, SECRET);
  must(v, "claims Worker refused the bearer");
  eq(v.member, row.member_key); eq(v.office, row.office_key);
  must(v.exp - Date.now() / 1000 > 11.9 * 3600 && v.exp - Date.now() / 1000 <= 12 * 3600, "bearer life is not 12 h");
});

await t("/lister/me: 401 with no cookie, a tampered cookie, or an expired one", async () => {
  const { e, row, cookie } = await signedIn();
  const r0 = await go(e, "GET", "/lister/me");
  eq(r0.status, 401); eq((await r0.json()).join, "https://motdang.net/listings/join");
  const bad = cookie.slice(0, -2) + (cookie.endsWith("AA") ? "BB" : "AA");
  eq((await go(e, "GET", "/lister/me", null, { cookie: bad })).status, 401, "tampered");
  const old = await L.signCookie(SECRET, row.member_key, Math.floor(Date.now() / 1000) - 5);
  eq((await go(e, "GET", "/lister/me", null, { cookie: "md_lister=" + old })).status, 401, "expired");
  const other = await L.signCookie("another-secret", row.member_key, Math.floor(Date.now() / 1000) + 99);
  eq((await go(e, "GET", "/lister/me", null, { cookie: "md_lister=" + other })).status, 401, "wrong secret");
});

await t("revocation: DECLINE after invite → revoked, perks cleared, the same cookie gets 401", async () => {
  const { e, row, cookie } = await signedIn();
  eq((await go(e, "GET", "/lister/me", null, { cookie })).status, 200);
  await go(e, "GET", "/listings/decline/" + row.decline_token);
  eq(e.SUBSCRIBERS.row("SELECT status FROM listers").status, "revoked");
  eq(JSON.parse(e.SUBSCRIBERS.row("SELECT perks FROM subscribers").perks).lister, undefined);
  eq((await go(e, "GET", "/lister/me", null, { cookie })).status, 401);
});

await t("sign-out clears the cookie", async () => {
  const res = await go(env(), "POST", "/listings/signout");
  eq(res.status, 303);
  must(/^md_lister=;.*Max-Age=0/.test(res.headers.get("set-cookie")), "not cleared");
});

/* ---------------------------------------------------------------- tokens */
await t("bearer: tamper, expiry, wrong secret, cookie-as-bearer all refused", async () => {
  const m = "0123456789abcdef0123456789abcdef";
  const exp = Math.floor(Date.now() / 1000) + 600;
  const good = await L.signBearer(SECRET, m, "ping-valley", exp);
  must(await B.verifyListerBearer(good, SECRET), "good bearer refused");
  must(await L.verifyBearer(SECRET, good), "site-side verify refused");
  const parts = good.split(".");
  eq(await B.verifyListerBearer([parts[0], m, "other-office", parts[3], parts[4]].join("."), SECRET), null, "office swapped");
  eq(await B.verifyListerBearer([parts[0], m, parts[2], String(exp + 999), parts[4]].join("."), SECRET), null, "exp extended");
  eq(await B.verifyListerBearer(good, "wrong-secret"), null, "wrong secret");
  eq(await B.verifyListerBearer(good, ""), null, "no secret");
  eq(await B.verifyListerBearer(await L.signBearer(SECRET, m, "x", exp - 700), SECRET), null, "expired");
  const cookie = await L.signCookie(SECRET, m, exp);
  eq(await B.verifyListerBearer(cookie, SECRET), null, "a cookie passed as a bearer");
  eq(await L.verifyCookie(SECRET, good), null, "a bearer passed as a cookie");
  must(await B.verifyListerBearer(await L.signBearer(SECRET, m, "บ้านสวน", exp), SECRET), "Thai office key");
});

await t("officeKey folds the way listing-sheet/agencies.py slugify does", () => {
  const names = ["Ping Valley Property Co., Ltd.", "บริษัท บ้านสวน เชียงใหม่ จำกัด", "Northern Homes", "!!!"];
  const py = JSON.parse(execFileSync("python3", ["-c",
    "import sys,json;sys.path.insert(0,sys.argv[1]);import agencies as A;print(json.dumps([A.slugify(n) for n in json.loads(sys.argv[2])]))",
    join(ROOT, "..", "listing-sheet"), JSON.stringify(names)], { encoding: "utf8" }));
  for (let i = 0; i < 3; i++) eq(L.officeKey(names[i], "abcdef0123"), py[i], names[i]);
  eq(L.officeKey("!!!", "abcdef0123"), "office-abcdef01");
});

await t("the router claims its paths and leaves the sheet's files alone", () => {
  for (const p of ["/listings/join", "/listings/join/confirm", "/listings/signin", "/listings/signout",
                   "/lister/me", "/listings/invite/x", "/listings/decline/x"])
    must(L.ownsLister(p), "should own " + p);
  for (const p of ["/listings/join.json", "/listings/add.html", "/listings/", "/listing"])
    must(!L.ownsLister(p), "should not own " + p);
  const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");
  const mount = src.indexOf("if (ownsLister(url.pathname))");
  must(mount > 0 && mount < src.indexOf('headers: { allow: "GET, HEAD, OPTIONS", ...CORS }'),
    "publish/worker.js does not mount lister ahead of the GET/HEAD guard");
});

/* ---------------------------------------------------------------- claims Worker */
class KV {
  constructor() { this.m = new Map(); }
  async get(k, type) { const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k, v) { this.m.set(k, String(v)); }
  async delete(k) { this.m.delete(k); }
  async list({ prefix } = {}) { return { keys: [...this.m.keys()].filter((k) => k.startsWith(prefix || "")).map((name) => ({ name })), list_complete: true }; }
}
class R2 {
  constructor() { this.m = new Map(); }
  async put(k, v, o) { this.m.set(k, { v, o }); }
  async list({ prefix } = {}) { return { objects: [...this.m.keys()].filter((k) => k.startsWith(prefix || "")).map((key) => ({ key })), truncated: false }; }
  async delete(k) { this.m.delete(k); }
}
const claimsEnv = (over) => ({ KV: new KV(), PHOTOS: new R2(), MAIL: mailBox(), LISTER_SECRET: SECRET, ...(over || {}) });
const ROW = { name: "Baan Suan Ping", kind: "house", offer: "rent", price: "32000", agency: "Ping Valley", contact: "081 234 5678" };
const postListing = (ce, body, path) => CLAIMS.fetch(new Request("https://claims.example" + (path || "/listing"), {
  method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "1.2.3.4" },
  body: JSON.stringify(body) }), ce);
const bearerFor = (m, o, s) => L.signBearer(s || SECRET, m || "0123456789abcdef0123456789abcdef", o || "ping-valley",
  Math.floor(Date.now() / 1000) + 3600);

await t("claims gate OFF (LISTER_REQUIRED unset): a send without a bearer is taken, as today", async () => {
  const ce = claimsEnv();
  const res = await postListing(ce, { listings: [ROW], attest: true });
  eq(res.status, 200);
  const d = await res.json();
  eq((await ce.KV.get(`lst:${d.id}`, "json")).lister, undefined);
  must(decode(ce.MAIL.sent[0].raw).includes("Listing agent: not signed in"), "mail line");
});

await t("claims gate ON: no bearer, a bad one, or no secret → 401 with the join address", async () => {
  for (const [label, body, over] of [
    ["none", { listings: [ROW] }, {}],
    ["garbage", { listings: [ROW], lister: "v1.x.y.z.w" }, {}],
    ["wrong secret", { listings: [ROW], lister: await bearerFor(null, null, "other") }, {}],
    ["no secret set", { listings: [ROW], lister: await bearerFor() }, { LISTER_SECRET: undefined }],
  ]) {
    const ce = claimsEnv({ LISTER_REQUIRED: "true", ...over });
    const res = await postListing(ce, body);
    eq(res.status, 401, label);
    eq((await res.json()).join, "https://motdang.net/listings/join", label);
    eq(ce.KV.m.size, 0, `${label}: something was stored`);
  }
  const ce = claimsEnv({ LISTER_REQUIRED: "true" });
  eq((await postListing(ce, { csv: "name,kind,offer,price,agency,contact\nX,house,rent,1,A,c\n" }, "/listing-csv")).status, 401, "csv");
});

await t("claims gate ON: a valid bearer is stamped on the submission and named in Nan's mail", async () => {
  const ce = claimsEnv({ LISTER_REQUIRED: "true" });
  const res = await postListing(ce, { listings: [ROW], attest: true, lister: await bearerFor() });
  eq(res.status, 200);
  const d = await res.json();
  const sub = await ce.KV.get(`lst:${d.id}`, "json");
  eq(sub.lister.member, "0123456789abcdef0123456789abcdef"); eq(sub.lister.office, "ping-valley");
  must(decode(ce.MAIL.sent[0].raw).includes("Listing agent: ping-valley (member 0123456789abcdef0123456789abcdef)"), "mail line");
  const one = await (await postListing(ce, { ...ROW, lister: await bearerFor() })).json();
  const oneSub = await ce.KV.get(`lst:${one.id}`, "json");
  eq(oneSub.rows[0].lister, undefined, "a one-row body kept the bearer as a column");
  eq(oneSub.lister.office, "ping-valley");
  const csv = await postListing(ce, { csv: "name,kind,offer,price,agency,contact\nX,house,rent,1,A,c\n", lister: await bearerFor() }, "/listing-csv");
  eq(csv.status, 200);
  eq((await ce.KV.get(`lst:${(await csv.json()).id}`, "json")).lister.office, "ping-valley");
});

const photoPost = (ce, fields, files) => {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  for (const f of files) fd.append("photo", f);
  return CLAIMS.fetch(new Request("https://claims.example/listing-photo", { method: "POST", body: fd }), ce);
};
const jpeg = (name, bytes) => new File([new Uint8Array(bytes || 10)], name, { type: "image/jpeg" });

await t("/listing-photo: stored at inbox/<id>/<name> with the LINE path's counter", async () => {
  const ce = claimsEnv({ LISTER_REQUIRED: "true" });
  const bearer = await bearerFor();
  const { id } = await (await postListing(ce, { listings: [{ ...ROW, photos: "IMG_1.jpg" }], lister: bearer })).json();
  const res = await photoPost(ce, { lister: bearer, sub: id }, [jpeg("IMG_1.jpg"), jpeg("../../etc/รูป 2.jpg")]);
  eq(res.status, 200);
  const d = await res.json();
  eq(d.n, 2);
  must(ce.PHOTOS.m.has(`inbox/${id}/IMG_1.jpg`), "IMG_1 not at inbox/<id>/");
  must(ce.PHOTOS.m.has(`inbox/${id}/รูป 2.jpg`), "path parts not stripped: " + [...ce.PHOTOS.m.keys()]);
  eq(await ce.KV.get(`lstphotos:${id}`), "2");
});

await t("/listing-photo: refuses no bearer, another agent, a non-image, an oversize file, the 13th", async () => {
  const ce = claimsEnv();
  const bearer = await bearerFor();
  const { id } = await (await postListing(ce, { listings: [ROW], lister: bearer })).json();
  eq((await photoPost(ce, { sub: id }, [jpeg("a.jpg")])).status, 401, "no bearer");
  const other = await bearerFor("fedcba9876543210fedcba9876543210");
  eq((await photoPost(ce, { lister: other, sub: id }, [jpeg("a.jpg")])).status, 403, "another agent");
  const svg = new File(["<svg/>"], "x.svg", { type: "image/svg+xml" });
  eq((await photoPost(ce, { lister: bearer, sub: id }, [svg])).status, 415, "svg");
  eq((await photoPost(ce, { lister: bearer, sub: id }, [jpeg("big.jpg", 5 * 1024 * 1024 + 1)])).status, 413, "over 5 MB");
  const twelve = Array.from({ length: 12 }, (_, i) => jpeg(`p${i}.jpg`));
  eq((await photoPost(ce, { lister: bearer, sub: id }, twelve)).status, 200, "twelve");
  eq((await photoPost(ce, { lister: bearer, sub: id }, [jpeg("p12.jpg")])).status, 400, "thirteenth");
  const { id: anon } = await (await postListing(ce, { listings: [ROW] })).json();
  eq((await photoPost(ce, { lister: bearer, sub: anon }, [jpeg("a.jpg")])).status, 403, "a submission with no lister");
});

await t("listerGate: off passes a missing bearer through; on returns a refusal", async () => {
  eq((await B.listerGate({}, { LISTER_SECRET: SECRET })).lister, null);
  must((await B.listerGate({}, { LISTER_SECRET: SECRET, LISTER_REQUIRED: "true" })).refuse, "on + none");
  eq((await B.listerGate({}, { LISTER_REQUIRED: "false" })).refuse, undefined);
});

globalThis.fetch = realFetch;
console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
