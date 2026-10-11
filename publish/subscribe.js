/* subscribe.js — the mailing list, collected at the edge with double opt-in.
 *
 * WHAT THIS IS, AND WHAT IT IS NOT YET
 * ------------------------------------
 * A reader gives an email and ticks a consent box; a PENDING row is written and
 * a confirmation link is composed. Following that link flips PENDING → CONFIRMED.
 * That is the whole promise: nobody is on the list until they have clicked a
 * link in their own inbox, and no marketing mail is ever sent from here.
 *
 * SENDING IS GATED OFF (env.MAILING_LIST_LIVE). Default off, off when the var is
 * unset, off unless it reads the exact string "true". While off, the
 * confirmation mail is COMPOSED and then LOGGED, never handed to the mail
 * binding — so a deploy changes nothing a reader can receive until Nan flips the
 * flag. There is no API key here and none is needed: the send path is
 * Cloudflare's own send_email binding (env.MAIL), the same one worker/worker.js
 * uses for the Listing Sheet.
 *
 * WHERE THE DATA LIVES: env.SUBSCRIBERS, a D1 database of its own — never the
 * search index (a reload of that must not touch a person's address) and never
 * the public site bucket. Schema in publish/migrations/0001_subscribers.sql.
 *
 * CONSENT COPY AND THE LIST'S HOME ARE NAN'S TO SETTLE. The strings below are a
 * DRAFT; the wording put to her is _incoming/mailing-list-consent-DRAFT.txt.
 *
 * The pure pieces (validation, token, storage over a bound D1, the gated send)
 * are exported so tests/test_subscribe.mjs can run the flow without a Worker. */

/* ------------------------------------------------------------ consent copy */
/* DRAFT — pending Nan (see _incoming/mailing-list-consent-DRAFT.txt). One place,
 * so a change she makes lands on the page and in the checkbox at once. */
export const CONSENT = {
  th: "ส่งอีเมลถึงฉันเมื่อมีของใหม่บนมดแดง — ยกเลิกได้จากทุกอีเมล",
  en: "Email me when there is something new on Mot Dang — unsubscribe from any message",
};
const INTRO = {
  th: "ข่าวใหม่ทางอีเมล เป็นครั้งคราว ไม่ถี่",
  en: "New posts by email, now and then — not often",
};

const LANGS = new Set(["th", "en", "both"]);
const FROM = "nan@motdang.net";         // Nan's send-as identity (Resend); motdang.net is a verified domain there (beer@ already sends)
const SENDER_NAME = "Mot Dang · มดแดง";
// The Resend API key lives in a Worker secret, never in code:
//   wrangler secret put RESEND_KEY      (the key that sends from motdang.net)
// motdang.net is already verified on the account (beer-mail sends from it), so
// this key can send as nan@motdang.net to any address.
const RESEND_KEY_VAR = "RESEND_KEY";

/* ------------------------------------------------------------ small helpers */
const esc = (x) => String(x == null ? "" : x)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const CORS = { "access-control-allow-origin": "*" };

/* A plain address, lower-cased and length-capped. Deliberately strict-ish and
 * boring: this is a gate, not an RFC 5322 parser. Empty string means "no". */
export function normalizeEmail(raw) {
  const e = String(raw || "").trim().toLowerCase();
  if (e.length < 3 || e.length > 254) return "";
  return /^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+$/.test(e) ? e : "";
}

/* 128 bits of URL-safe randomness. Enough that a confirm link cannot be
 * guessed, and it doubles as the unsubscribe key. */
export function newToken() {
  const b = new Uint8Array(16);
  (globalThis.crypto || crypto).getRandomValues(b);
  return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}

/* The source is a breadcrumb, not a tracker: which page or block sent them, so
 * a later "where did subscribers come from" needs no third party. Capped and
 * stripped to keep an odd referrer from writing a long or ugly string. */
export function clampSource(s) {
  return String(s || "subscribe").replace(/[^\w./:-]/g, "").slice(0, 80) || "subscribe";
}

/* ------------------------------------------------------------ the storage */

/* A PENDING row, or a refreshed token on one that is still pending. A row that
 * is ALREADY confirmed is left confirmed — re-submitting an address that is on
 * the list must not knock it back to pending and must not trigger another mail.
 * Returns the row's status after the write, so the caller knows which page to
 * show and whether to send. */
export async function storePending(db, rec) {
  await db.prepare(
    `INSERT INTO subscribers (email, status, token, source, lang, created_at, confirmed_at, perks)
     VALUES (?, 'pending', ?, ?, ?, ?, NULL, '{}')
     ON CONFLICT(email) DO UPDATE SET
       token = excluded.token,
       source = excluded.source,
       lang = excluded.lang,
       created_at = excluded.created_at,
       status = CASE WHEN subscribers.status = 'confirmed' THEN 'confirmed' ELSE 'pending' END`
  ).bind(rec.email, rec.token, rec.source, rec.lang, rec.now).run();
  const row = await db.prepare(`SELECT status FROM subscribers WHERE email = ?`)
    .bind(rec.email).first();
  return row ? row.status : "pending";
}

/* PENDING → CONFIRMED, and only ever forward. The token is required — an empty
 * one is refused before a query runs. A token that flips nothing is either
 * already confirmed (fine, say so) or unknown/expired (say that instead, and
 * never reveal whether the address exists). */
export async function confirmToken(db, token, now) {
  const t = String(token || "").trim();
  if (!/^[a-f0-9]{8,64}$/.test(t)) return { ok: false, reason: "missing-or-bad-token" };
  const res = await db.prepare(
    `UPDATE subscribers SET status = 'confirmed', confirmed_at = ? WHERE token = ? AND status = 'pending'`
  ).bind(now, t).run();
  if (res && res.meta && res.meta.changes) return { ok: true, already: false };
  const row = await db.prepare(`SELECT status FROM subscribers WHERE token = ?`).bind(t).first();
  if (row && row.status === "confirmed") return { ok: true, already: true };
  return { ok: false, reason: "invalid-or-expired" };
}

/* ------------------------------------------------------------ the mail */

/* The confirmation message, built as a raw MIME string the same way
 * worker/worker.js builds the Listing Sheet mail. Composed always; SENT only
 * when the gate is open (see sendConfirm). Bilingual, plain text. */
/* One source for the confirm message's words, so the MIME build (below, kept
 * for the plain-node test) and the Resend payload (sendConfirm) never drift. */
export function confirmContent(confirmUrl) {
  return {
    subject: "ยืนยันอีเมล · Confirm your email — Mot Dang",
    text: [
      "ยืนยันการสมัครรับอีเมลจากมดแดง",
      "กดลิงก์นี้เพื่อยืนยัน — ถ้าไม่ได้สมัคร ไม่ต้องทำอะไร ลิงก์จะหมดอายุเอง",
      "",
      confirmUrl,
      "",
      "— — —",
      "",
      "Confirm your Mot Dang email subscription.",
      "Click the link to confirm. If you did not sign up, ignore this — the link expires on its own.",
      "",
      confirmUrl,
    ].join("\r\n"),
  };
}

export function composeConfirm(sub, confirmUrl, id) {
  const { subject, text: body } = confirmContent(confirmUrl);
  return [
    `From: ${SENDER_NAME} <${FROM}>`,
    `To: <${String(sub.email).replace(/[\r\n<>]/g, "")}>`,
    `Message-ID: <${id || newToken()}@motdang.net>`,
    `Date: ${new Date().toUTCString()}`,
    "Subject: =?UTF-8?B?" + b64(utf8(subject)) + "?=",
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: base64",
    "",
    b64(utf8(body)),
  ].join("\r\n");
}

/* THE GATE, and the send path is Resend (Nan's send-as identity, nan@motdang.net).
 * Off by default and off unless MAILING_LIST_LIVE is the exact string "true":
 * off → the message is composed (so the path stays exercised and testable) and
 * logged; nothing leaves. On → one POST to Resend, exactly as beer-mail sends,
 * the key read from the RESEND_KEY secret and never written in code. Resend can
 * mail any address (unlike the destination-pinned send_email binding), which is
 * what a stranger's confirm link needs. */
export async function sendConfirm(env, sub, confirmUrl) {
  const { subject, text } = confirmContent(confirmUrl);
  if ((env && env.MAILING_LIST_LIVE) !== "true") {
    console.log(`[mailing-list] confirm mail GATED OFF (MAILING_LIST_LIVE!=="true"); composed for ${sub.email}, not sent`);
    return { sent: false, reason: "gated-off" };
  }
  const key = env && env[RESEND_KEY_VAR];
  if (!key) return { sent: false, reason: "no-resend-key" };
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: "Bearer " + key, "content-type": "application/json" },
      body: JSON.stringify({
        from: `${SENDER_NAME} <${FROM}>`,
        to: String(sub.email).replace(/[\r\n<>]/g, ""),
        subject,
        text,
      }),
    });
    if (!r.ok) {
      const out = await r.json().catch(() => ({}));
      return { sent: false, reason: (out && out.message) || `resend-${r.status}` };
    }
    const out = await r.json().catch(() => ({}));
    return { sent: true, id: out.id };
  } catch (e) {
    console.error("[mailing-list] send failed", e);
    return { sent: false, reason: String((e && e.message) || e) };
  }
}

const utf8 = (s) => new TextEncoder().encode(s);
function b64(bytes) {
  let s = "";
  for (const c of bytes) s += String.fromCharCode(c);
  return btoa(s);
}

/* ------------------------------------------------------------ the pages */

function shell(title, body, robots) {
  return `<!DOCTYPE html><html lang="th" translate="no" class="notranslate"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google" content="notranslate"><meta name="robots" content="${robots || "index,follow"}">
<title>${esc(title)}</title>
<link rel="icon" href="/logo/motdang-favicon.svg" type="image/svg+xml">
<style>
:root{--paper:#fffdf8;--ink:#1a1408;--mute:#5c4d38;--rule:#c9b895;--red:#b3261e;--go:#0b6b3a}
html{background:var(--paper);color:var(--ink);font:17px/1.55 Georgia,"Times New Roman",Thonburi,serif}
body{margin:0;padding:1.2rem 1rem 3rem;max-width:40em}
h1{font-size:1.5em;margin:.2em 0 .1em}.sub{color:var(--mute);margin:.1em 0 1.2em}
a{color:#0000ee}a:visited{color:#551a8b}
form.md-sub{margin:1em 0;padding:1em;border:1px solid var(--rule);background:#fff}
label{display:block;margin:0 0 .8em}
input[type=email]{font:inherit;font-size:1.05em;width:100%;max-width:26em;padding:.4em .5em;border:1px solid var(--mute);box-sizing:border-box;margin-top:.25em}
.consent{display:flex;gap:.55em;align-items:flex-start;font-size:.97em}
.consent input{margin-top:.35em;flex:none}
button{font:inherit;padding:.45em 1.1em;background:#f2ebdc;border:1px solid var(--mute);color:var(--ink);cursor:pointer}
.note{color:var(--mute);font-size:.92em;margin:.8em 0 0}
.ok{color:var(--go)}.bad{color:var(--red)}
footer{margin-top:2.5em;padding-top:.6em;border-top:1px solid var(--rule);color:var(--mute);font-size:.9em}
</style></head><body>
${body}
<footer><a href="/">มดแดง Mot Dang</a> · <a href="/find">ค้นหา · search</a></footer>
</body></html>`;
}

/* THE REUSABLE BLOCK. A dedicated page renders it below; any other page can
 * drop the same markup in (build.py has no hook into the Worker, so a static
 * page includes publish/partials/subscribe-block.html — see the report). No
 * pre-checked box (consent is a choice made here, never a default), one field
 * plus the box, and the consent sentence is the single DRAFT string above. */
export function signupBlock(opts) {
  const o = opts || {};
  const source = clampSource(o.source || "subscribe");
  const lang = LANGS.has(o.lang) ? o.lang : "both";
  return `<form class="md-sub" action="/subscribe" method="post">
<input type="hidden" name="source" value="${esc(source)}">
<input type="hidden" name="lang" value="${esc(lang)}">
<label>อีเมล · Email
<input type="email" name="email" required autocomplete="email" inputmode="email" placeholder="you@example.com"></label>
<label class="consent"><input type="checkbox" name="consent" value="yes" required>
<span>${esc(CONSENT.th)}<br>${esc(CONSENT.en)}</span></label>
<button type="submit">สมัคร · Subscribe</button>
</form>`;
}

function subscribePage(url) {
  const source = clampSource(url.searchParams.get("src") || "subscribe");
  const body = `<h1>รับข่าวมดแดง · Mot Dang by email</h1>
<p class="sub">${esc(INTRO.th)} · ${esc(INTRO.en)}</p>
${signupBlock({ source })}
<p class="note">ยืนยันสองชั้น — จะมีอีเมลขอให้กดยืนยันก่อนถึงจะเข้ารายชื่อ · Double opt-in: we email you a link to confirm before you are on the list.</p>`;
  return html(200, shell("รับข่าว · Subscribe · มดแดง", body, "index,follow"));
}

const RESULTS = {
  "check-inbox": ["✅ เกือบเสร็จแล้ว", "เปิดอีเมลแล้วกดลิงก์ยืนยัน",
                  "Almost there", "Open your email and click the link to confirm.", "ok"],
  saved: ["✅ บันทึกคำขอแล้ว", "การยืนยันทางอีเมลยังไม่เปิดใช้งาน — คำขอถูกเก็บไว้แล้ว",
          "Request saved", "Email confirmation is not switched on yet — your request is held.", "ok"],
  already: ["✅ อยู่ในรายชื่อแล้ว", "อีเมลนี้ยืนยันไว้แล้ว ไม่ต้องทำอะไรเพิ่ม",
            "Already subscribed", "This address is already confirmed — nothing to do.", "ok"],
  "bad-email": ["✋ อีเมลไม่ถูกต้อง", "ลองพิมพ์อีเมลอีกครั้ง",
                "Check the email", "That did not look like an email address — try again.", "bad"],  // stylecheck: allow — UI status message
  "no-consent": ["✋ ยังไม่ได้ติ๊กยินยอม", "ต้องติ๊กช่องยินยอมก่อนถึงจะสมัครได้",
                 "Consent needed", "Please tick the consent box to subscribe.", "bad"],
  error: ["⚠️ ขัดข้อง", "ลองอีกครั้งในอีกสักครู่",
          "Something went wrong", "Please try again shortly.", "bad"],
  confirmed: ["✅ ยืนยันแล้ว", "คุณอยู่ในรายชื่อแล้ว — ยกเลิกได้จากทุกอีเมล",
              "Confirmed", "You are on the list — unsubscribe from any message.", "ok"],
  "confirm-already": ["✅ ยืนยันไว้แล้ว", "ลิงก์นี้ใช้ยืนยันไปแล้ว",
                      "Already confirmed", "This link was already used to confirm.", "ok"],
  "confirm-bad": ["✋ ลิงก์ใช้ไม่ได้", "ลิงก์ยืนยันไม่ถูกต้องหรือหมดอายุ — สมัครใหม่ได้",
                  "Link not valid", "This confirm link is not valid or has expired — you can subscribe again.", "bad"],
  "not-ready": ["⚠️ ยังไม่พร้อม", "รายชื่ออีเมลยังไม่ได้ตั้งค่า",
                "Not ready", "The mailing list is not configured yet.", "bad"],
};

function resultPage(key, status) {
  const r = RESULTS[key] || RESULTS.error;
  const cls = r[4];
  const again = (cls === "bad" && key !== "not-ready")
    ? `<p class="note"><a href="/subscribe">← กลับไปสมัคร · back to sign up</a></p>` : "";
  return html(status, shell(`${r[2]} · มดแดง`,
    `<h1 class="${cls}">${esc(r[0])} · ${esc(r[2])}</h1>
<p class="sub">${esc(r[1])}<br>${esc(r[3])}</p>${again}`, "noindex"));
}

function html(status, body) {
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8",
               "cache-control": "no-store", ...CORS },
  });
}

/* ------------------------------------------------------------ form reading */
/* A POST arrives as a form (the page) or as JSON (a caller). Both come back as
 * something with .get(name), so the handler reads one shape. */
async function readForm(request) {
  const ct = (request.headers.get("content-type") || "").toLowerCase();
  if (ct.includes("application/json")) {
    let o = {};
    try { o = await request.json(); } catch { /* an empty map answers every get */ }
    return { get: (k) => (o && o[k] != null ? String(o[k]) : null) };
  }
  try { return await request.formData(); }
  catch { return { get: () => null }; }
}

/* ------------------------------------------------------------ the handlers */

export async function handleSubscribe(request, env, url) {
  if (!env.SUBSCRIBERS) return resultPage("not-ready", 503);
  const form = await readForm(request);
  const email = normalizeEmail(form.get("email"));
  const consent = form.get("consent");
  const lang = LANGS.has(form.get("lang")) ? form.get("lang") : "both";
  const source = clampSource(form.get("source") || url.searchParams.get("src"));
  if (!email) return resultPage("bad-email", 400);
  /* Server-side consent gate: a form with a stripped checkbox, or a JSON caller
   * that never set it, does not get onto the list. No box, no row. */
  if (!consent) return resultPage("no-consent", 400);

  const token = newToken();
  const now = new Date().toISOString();
  let status;
  try { status = await storePending(env.SUBSCRIBERS, { email, token, source, lang, now }); }
  catch (e) { console.error("[mailing-list] store failed", e); return resultPage("error", 500); }

  if (status === "confirmed") return resultPage("already", 200);

  const confirmUrl = `${url.origin}/subscribe/confirm?token=${token}`;
  const sent = await sendConfirm(env, { email, lang }, confirmUrl);
  return resultPage(sent.sent ? "check-inbox" : "saved", 200);
}

export async function handleConfirm(request, env, url) {
  if (!env.SUBSCRIBERS) return resultPage("not-ready", 503);
  const token = url.searchParams.get("token");
  let res;
  try { res = await confirmToken(env.SUBSCRIBERS, token, new Date().toISOString()); }
  catch (e) { console.error("[mailing-list] confirm failed", e); return resultPage("error", 500); }
  if (res.ok) return resultPage(res.already ? "confirm-already" : "confirmed", 200);
  return resultPage("confirm-bad", 400);
}

/* One entry from worker.js. GET /subscribe renders the page; POST /subscribe
 * collects; GET /subscribe/confirm confirms. A method that fits nowhere is a
 * 405 with the ones that do. */
export async function subscribe(request, env, url) {
  const p = url.pathname;
  if (p === "/subscribe" || p === "/subscribe/") {
    if (request.method === "POST") return handleSubscribe(request, env, url);
    if (request.method === "GET" || request.method === "HEAD") return subscribePage(url);
    return new Response("Method not allowed", { status: 405, headers: { allow: "GET, POST, HEAD", ...CORS } });
  }
  if (p === "/subscribe/confirm") {
    if (request.method === "GET" || request.method === "HEAD") return handleConfirm(request, env, url);
    return new Response("Method not allowed", { status: 405, headers: { allow: "GET, HEAD", ...CORS } });
  }
  return new Response("Not found", { status: 404, headers: CORS });
}

export default { subscribe, handleSubscribe, handleConfirm, storePending, confirmToken,
                 sendConfirm, composeConfirm, signupBlock, normalizeEmail, newToken, clampSource };
