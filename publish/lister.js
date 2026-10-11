/* lister.js — the listing-agent gate for motdang.net/listings/add.html.
 *
 * Nan, 2026-09-27: "You should have to sign up and be invited to join
 * newsletter to use this page as a listing agent."
 *
 * THE FLOW
 *   GET  /listings/join                the form (Thai first, English beside it)
 *   POST /listings/join                both boxes re-checked here; a pending
 *                                      subscriber (source "lister") and an
 *                                      'applied' lister row; confirm mail composed,
 *                                      sent only when MAILING_LIST_LIVE is "true"
 *   GET  /listings/join/confirm?token= subscriber confirmed, lister 'confirmed',
 *                                      Nan mailed INVITE / DECLINE links
 *   GET  /listings/invite/<token>      Nan's tap: 'invited', perks.lister set,
 *                                      invite mail (gated) with a sign-in link
 *   GET  /listings/decline/<token>     Nan's tap: 'declined', or 'revoked' once invited
 *   GET|POST /listings/signin          form / mail a 1-hour link (gated); the
 *                                      reply is the same for members and strangers
 *   GET  /listings/signin?token=       sets the md_lister cookie (90 days), → add.html
 *   POST /listings/signout             clears it
 *   GET  /lister/me                    200 {member, bearer} or 401
 *
 * LISTER_INVITE = "auto" (Nan, 2026-09-27: "automatic invite but a bot
 * should sanity check and send digests"): at confirm, sanityCheck() runs;
 * a pass is invited, a fail stays 'confirmed' with its reasons on the row,
 * and Nan gets no per-event mail — listing-sheet/digest.py reports both
 * once a day, with her INVITE / DECLINE links for the held ones.
 * Anything else ("operator") waits for her tap and mails her per applicant.
 *
 * TOKENS. The cookie is v1.<member_key>.<exp>.<sig>; the bearer the form
 * carries to the claims Worker is v1.<member_key>.<office_key>.<exp>.<sig>,
 * 12 hours. Both are HMAC-SHA256 under the LISTER_SECRET secret, which the
 * claims Worker also holds (worker/lister_bearer.js verifies the bearer). The
 * HMAC input is prefixed "cookie|" or "bearer|", so one cannot stand in for
 * the other. /lister/me reads the row on every call, so a revoke stops new
 * bearers at once; a bearer already issued runs out within 12 hours.
 *
 * Stranger mail goes through subscribe.js's gate (MAILING_LIST_LIVE, Resend,
 * RESEND_KEY). Mail to Nan goes through the MAIL send_email binding, which
 * wrangler.toml pins to her address, so it is not behind that gate.
 *
 * Consent copy approved by Nan 2026-09-27:
 * _incoming/lister-consent-APPROVED-2026-09-27.txt. */

import { normalizeEmail, newToken, storePending, confirmToken } from "./subscribe.js";

/* ------------------------------------------------------------ consent copy */
/* Approved by Nan 2026-09-27 ("Agent consent draft looks ok", "cc 4.0 is
 * good"). CONSENT_VERSION is written to each row's consent_version, so a row
 * shows which wording its applicant ticked; a change to the words takes a
 * new version string. */
export const CONSENT_VERSION = "2026-09-27";
export const LISTER_CONSENT = {
  newsletter: {
    th: "รับอีเมลข่าวจากมดแดง — เป็นเงื่อนไขของการลงประกาศ",
    en: "Send me the Mot Dang newsletter — the condition of listing",
  },
  reuse: {
    th: "ข้อมูลและรูปที่ฉันส่ง มดแดงเผยแพร่และนำไปใช้ซ้ำได้ทั่วทั้งเว็บ ภายใต้ CC BY 4.0 โดยให้เครดิตบริษัทของฉัน (CC BY 4.0 คือ ใครก็นำไปใช้ต่อได้ เมื่อให้เครดิต)",
    en: "Mot Dang may publish and reuse what I send, anywhere on the site, under CC BY 4.0 with credit to my agency (CC BY 4.0: anyone may reuse it, with credit)",
  },
};
const CC_BY = "https://creativecommons.org/licenses/by/4.0/deed.th";

/* ------------------------------------------------------------ constants */
const COOKIE = "md_lister";
const COOKIE_TTL = 90 * 24 * 3600;          // seconds
const BEARER_TTL = 12 * 3600;
const SIGNIN_TTL = 3600;                    // a link asked for on /listings/signin
const INVITE_SIGNIN_TTL = 7 * 24 * 3600;    // the link inside the invite mail
const OPERATOR_TTL = 90 * 24 * 3600;        // Nan's INVITE / DECLINE links
const SIGNIN_THROTTLE = 60;                 // one sign-in mail a minute per address
const JOIN_URL = "https://motdang.net/listings/join";
const OPERATOR_TO = "530kings@proton.me";   // the MAIL binding is pinned here too
const OPERATOR_FROM = "listings@motdang.net";
const FROM = "nan@motdang.net";             // Resend send-as, as subscribe.js
const SENDER_NAME = "Mot Dang · มดแดง";
// "north" = anywhere else in northern Thailand (data/coverage.json, Nan 2026-09-29)
const PROVINCES = { cm: "cm", cr: "cr", both: "cm,cr", north: "north" };
const LANGS = new Set(["th", "en", "both"]);

/* ------------------------------------------------------------ small helpers */
const esc = (x) => String(x == null ? "" : x)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const enc = new TextEncoder();
const iso = (ms) => new Date(ms).toISOString();
const nowSec = () => Math.floor(Date.now() / 1000);

/* A typed field, trimmed, control characters out, capped. */
export function clean(v, max) {
  // eslint-disable-next-line no-control-regex
  return String(v == null ? "" : v).replace(/[\u0000-\u001f\u007f]+/g, " ").trim().slice(0, max);
}

/* OfficeKey. The same fold as listing-sheet/agencies.py slugify(): NFKC,
 * casefold, the legal tail (Co., Ltd., บริษัท, จำกัด …) out, anything but
 * a-z 0-9 and Thai to a hyphen, 48 characters. The pattern is folded with
 * NFKC as there, since NFKC splits ำ and จำกัด would otherwise not match. A
 * name that folds to nothing gets "office-" and the first eight of the
 * member key. */
const LEGAL_TAIL = new RegExp(
  "(?:\\s|^)(?:co\\.?,?\\s*ltd\\.?|company\\s+limited|ltd\\.?|limited|co\\.?|" +
  "part\\.?,?\\s*ltd\\.?|l\\.?p\\.?|ห้างหุ้นส่วนจำกัด|หจก\\.?|จำกัด|บริษัท)(?=\\s|$)".normalize("NFKC"), "giu");
export function officeKey(name, memberKey) {
  let s = String(name || "").trim().toLowerCase().normalize("NFKC");
  s = s.replace(LEGAL_TAIL, " ");
  s = s.replace(/[^a-z0-9฀-๿]+/gu, "-").replace(/^-+|-+$/g, "").slice(0, 48);
  return s || `office-${String(memberKey || "").slice(0, 8)}`;
}

/* ------------------------------------------------------------ HMAC tokens */
function b64url(bytes) {
  let s = "";
  for (const c of bytes) s += String.fromCharCode(c);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function unb64url(s) {
  if (!/^[A-Za-z0-9_-]+$/.test(s || "")) return null;
  try {
    const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4));
    return Uint8Array.from(bin, (c) => c.charCodeAt(0));
  } catch { return null; }
}
async function hmacKey(secret, usage) {
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" },
    false, [usage]);
}
const MEMBER_RE = /^[a-f0-9]{32}$/;
const OFFICE_RE = /^[a-z0-9฀-๿-]{1,56}$/u;

/* kind is "cookie" or "bearer"; parts are what sits between "v1." and the sig. */
async function sign(secret, kind, parts) {
  const payload = ["v1", ...parts].join(".");
  const key = await hmacKey(secret, "sign");
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(`${kind}|${payload}`));
  return `${payload}.${b64url(new Uint8Array(sig))}`;
}
/* The parts, or null: wrong shape, bad signature, or past its expiry. The
 * signature check is crypto.subtle.verify, which compares in constant time. */
async function verify(secret, kind, token, n, now) {
  if (!secret || typeof token !== "string" || token.length > 400) return null;
  const bits = token.split(".");
  if (bits.length !== n + 2 || bits[0] !== "v1") return null;
  const sig = unb64url(bits[n + 1]);
  if (!sig) return null;
  const payload = bits.slice(0, n + 1).join(".");
  const key = await hmacKey(secret, "verify");
  const ok = await crypto.subtle.verify("HMAC", key, sig, enc.encode(`${kind}|${payload}`));
  if (!ok) return null;
  const exp = Number(bits[n]);
  if (!Number.isInteger(exp) || exp <= (now == null ? nowSec() : now)) return null;
  return bits.slice(1, n + 1);
}

export async function signCookie(secret, memberKey, exp) {
  return sign(secret, "cookie", [memberKey, String(exp)]);
}
export async function verifyCookie(secret, token, now) {
  const p = await verify(secret, "cookie", token, 2, now);
  return p && MEMBER_RE.test(p[0]) ? { member: p[0], exp: Number(p[1]) } : null;
}
export async function signBearer(secret, memberKey, office, exp) {
  return sign(secret, "bearer", [memberKey, office, String(exp)]);
}
/* worker/lister_bearer.js holds the claims Worker's copy of this check;
 * tests/test_lister.mjs signs here and verifies there. */
export async function verifyBearer(secret, token, now) {
  const p = await verify(secret, "bearer", token, 3, now);
  return p && MEMBER_RE.test(p[0]) && OFFICE_RE.test(p[1])
    ? { member: p[0], office: p[1], exp: Number(p[2]) } : null;
}

export function readCookie(request, name) {
  const raw = request.headers.get("cookie") || "";
  for (const part of raw.split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return null;
}

/* ------------------------------------------------------------ storage */

/* An 'applied' row, or fresh details on one still 'applied' or 'confirmed'.
 * An invited, declined or revoked row keeps its state and its details. */
export async function upsertLister(db, r) {
  await db.prepare(
    `INSERT INTO listers (member_key, email, full_name, office_name, office_key, phone, line_id,
       provinces, status, lang, reuse_consent, consent_version, created_at, modified_at, ip_hash)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, 1, ?, ?, ?, ?)
     ON CONFLICT(email) DO UPDATE SET
       full_name = excluded.full_name, office_name = excluded.office_name,
       office_key = excluded.office_key, phone = excluded.phone, line_id = excluded.line_id,
       provinces = excluded.provinces, lang = excluded.lang, reuse_consent = 1,
       consent_version = excluded.consent_version, modified_at = excluded.modified_at,
       ip_hash = excluded.ip_hash
     WHERE listers.status IN ('applied', 'confirmed')`
  ).bind(r.member_key, r.email, r.full_name, r.office_name, r.office_key, r.phone || null,
         r.line_id || null, r.provinces, r.lang, CONSENT_VERSION, r.now, r.now, r.ip_hash || null).run();
  return db.prepare(`SELECT * FROM listers WHERE email = ?`).bind(r.email).first();
}

const byColumn = (db, col, v) =>
  db.prepare(`SELECT * FROM listers WHERE ${col} = ?`).bind(v).first();

/* perks.lister on the subscriber row: set on invite, removed on revoke. */
export async function setPerk(db, email, value) {
  const row = await db.prepare(`SELECT perks FROM subscribers WHERE email = ?`).bind(email).first();
  if (!row) return false;
  let perks = {};
  try { perks = JSON.parse(row.perks || "{}") || {}; } catch { perks = {}; }
  if (value) perks.lister = value; else delete perks.lister;
  await db.prepare(`UPDATE subscribers SET perks = ? WHERE email = ?`)
    .bind(JSON.stringify(perks), email).run();
  return true;
}

/* ------------------------------------------------------------ mail */
const utf8 = (s) => enc.encode(s);
function b64(bytes) {
  let s = "";
  for (const c of bytes) s += String.fromCharCode(c);
  return btoa(s).replace(/(.{76})/g, "$1\r\n");
}

export function confirmMail(url) {
  return {
    subject: "ยืนยันอีเมล · Confirm your email — Mot Dang listings",
    text: [
      "ยืนยันอีเมลเพื่อสมัครลงประกาศกับมดแดง และรับอีเมลข่าว",
      "ถ้าไม่ได้สมัคร ไม่ต้องทำอะไร",
      "", url, "", "— — —", "",
      "Confirm your email to join Mot Dang as a listing agent and receive the newsletter.",
      "If you did not apply, ignore this.",
      "", url,
    ].join("\r\n"),
  };
}
export function inviteMail(url) {
  return {
    subject: "ได้รับเชิญลงประกาศ · Invited to list — Mot Dang",
    text: [
      "คุณได้รับเชิญลงประกาศบนมดแดงแล้ว กดลิงก์เพื่อเข้าสู่ระบบ (ใช้ได้ 7 วัน ครั้งเดียว)",
      "", url, "",
      "เข้าสู่ระบบครั้งต่อไป: https://motdang.net/listings/signin",
      "", "— — —", "",
      "You are invited to list on Mot Dang. Open the link to sign in (one use, 7 days).",
      "", url, "",
      "To sign in again later: https://motdang.net/listings/signin",
    ].join("\r\n"),
  };
}
export function signinMail(url) {
  return {
    subject: "ลิงก์เข้าสู่ระบบ · Sign-in link — Mot Dang",
    text: [
      "ลิงก์เข้าสู่ระบบ ใช้ได้ 1 ชั่วโมง ครั้งเดียว", "", url, "",
      "ถ้าไม่ได้ขอ ไม่ต้องทำอะไร", "", "— — —", "",
      "Your sign-in link, one use, one hour.", "", url, "",
      "If you did not ask for it, ignore this.",
    ].join("\r\n"),
  };
}

/* The gate subscribe.js uses, for any message to a lister: off unless
 * MAILING_LIST_LIVE is exactly "true", and then one POST to Resend with the
 * RESEND_KEY secret. Off → composed, logged, returned. */
export async function sendGated(env, to, content) {
  if ((env && env.MAILING_LIST_LIVE) !== "true") {
    console.log(`[lister] mail GATED OFF (MAILING_LIST_LIVE!=="true"); composed "${content.subject}", not sent`);
    return { sent: false, reason: "gated-off", content };
  }
  const key = env && env.RESEND_KEY;
  if (!key) return { sent: false, reason: "no-resend-key", content };
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: "Bearer " + key, "content-type": "application/json" },
      body: JSON.stringify({ from: `${SENDER_NAME} <${FROM}>`,
                             to: String(to).replace(/[\r\n<>]/g, ""),
                             subject: content.subject, text: content.text }),
    });
    const out = await r.json().catch(() => ({}));
    if (!r.ok) return { sent: false, reason: (out && out.message) || `resend-${r.status}`, content };
    return { sent: true, id: out.id, content };
  } catch (e) {
    console.error("[lister] send failed", e);
    return { sent: false, reason: String((e && e.message) || e), content };
  }
}

/* What Nan reads on her phone when someone confirms (LISTER_INVITE
 * "operator" only; in "auto" the digest carries it). */
export function operatorMail(L, origin) {
  const prov = { cm: "Chiang Mai", cr: "Chiang Rai", "cm,cr": "Chiang Mai + Chiang Rai", north: "elsewhere in the north" }[L.provinces] || L.provinces;
  const lines = [
    "A listing agent confirmed their email and asks to list.",
    "",
    `  ${L.full_name}`,
    `  ${L.office_name}  (office key ${L.office_key})`,
    `  ${L.email}`,
    `  phone: ${L.phone || "-"}   LINE: ${L.line_id || "-"}`,
    `  provinces: ${prov}`,
    `  newsletter: yes   reuse under CC BY 4.0: ${L.reuse_consent ? "yes" : "NO"}   (${L.consent_version || "?"})`,
    `  applied ${L.created_at}`,
    ...(L.held_reasons ? [`  checks failed: ${JSON.parse(L.held_reasons).join("; ")}`] : []),
    "",
    "INVITE — they get a sign-in link:", `  ${origin}/listings/invite/${L.invite_token}`, "",
    "DECLINE — marks them declined, with no mail to them:", `  ${origin}/listings/decline/${L.decline_token}`,
    "", `Member ${L.member_key}`,
  ];
  return { subject: `Listing agent — ${L.full_name} (${L.office_name})`, text: lines.join("\r\n") };
}

export function operatorRaw(content, id) {
  const subj = /^[\x20-\x7E]*$/.test(content.subject)
    ? content.subject : "=?UTF-8?B?" + b64(utf8(content.subject)).replace(/\r\n/g, "") + "?=";
  return [
    `From: Mot Dang Listings <${OPERATOR_FROM}>`,
    `To: <${OPERATOR_TO}>`,
    `Message-ID: <${id || newToken()}@motdang.net>`,
    `Date: ${new Date().toUTCString()}`,
    `Subject: ${subj}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: base64",
    "",
    b64(utf8(content.text)),
  ].join("\r\n");
}

/* EmailMessage lives in "cloudflare:email", which exists only inside a
 * Worker; loaded on first use so node can import this file. Tests hand in a
 * stand-in with setEmailMessage(). */
let EmailMessageCls = null;
export function setEmailMessage(cls) { EmailMessageCls = cls; }
export async function sendOperator(env, content, id) {
  if (!env.MAIL) {
    console.log(`[lister] operator mail: no MAIL binding; composed "${content.subject}"`);
    return { sent: false, reason: "no-mail-binding", content };
  }
  try {
    if (!EmailMessageCls) EmailMessageCls = (await import("cloudflare:email")).EmailMessage;
    await env.MAIL.send(new EmailMessageCls(OPERATOR_FROM, OPERATOR_TO, operatorRaw(content, id)));
    return { sent: true, content };
  } catch (e) {
    console.error("[lister] operator mail failed", e);
    return { sent: false, reason: String((e && e.message) || e), content };
  }
}

/* ------------------------------------------------------------ sanity check */

/* Throwaway inboxes. A listing agent's address is how buyers and Nan reach
 * them for months; an inbox that self-destructs in ten minutes says the
 * applicant does not mean to be reached. Small on purpose — the well-known
 * services — and a subdomain of one counts. */
export const DISPOSABLE = new Set([
  "mailinator.com", "guerrillamail.com", "guerrillamail.info", "guerrillamail.net",
  "sharklasers.com", "grr.la", "10minutemail.com", "10minutemail.net", "temp-mail.org",
  "tempmail.com", "tempmail.net", "tempmailo.com", "tmpmail.org", "yopmail.com", "yopmail.net",
  "trashmail.com", "getnada.com", "dispostable.com", "maildrop.cc", "throwawaymail.com",
  "fakeinbox.com", "mintemail.com", "mohmal.com", "emailondeck.com", "moakt.com",
  "mailnesia.com", "burnermail.io", "spamgourmet.com", "mytemp.email", "mailpoof.com",
]);
/* More applications than this from one IP in 24 hours is held: one office
 * signing up its agents is normal, a script working through a list is not. */
export const IP_DAY_MAX = 4;

const fold = (s) => String(s || "").normalize("NFKC").toLowerCase().replace(/[\s._\-()'",]+/g, "");
const letters = (s) => (String(s || "").match(/\p{L}/gu) || []).length;

/* Keyboard noise: what a hand dragged across the keys, or Thai typed with the
 * layout switched to English (and the reverse), tends to leave. Each test is
 * narrow so that a real Thai or English name passes. */
export function looksLikeNoise(s) {
  const t = String(s || "").toLowerCase();
  // Thai and Latin letters inside ONE word ("abcกข"): names mix scripts
  // across words ("ร้าน ABC Home"), a layout slip mixes them within one.
  if (t.split(/\s+/).some((w) => /[a-z]/.test(w) && /[ก-๏]/.test(w))) return true;
  // Six Latin consonants in a row with no vowel ("sdfghj"): no English word
  // or Thai romanisation does that.
  if (/[bcdfghjklmnpqrstvwxz]{6,}/.test(t)) return true;
  // One character four times over ("aaaa", "กกกก").
  if (/(\p{L})\1{3,}/u.test(t)) return true;
  // Home-row and top-row runs, English and Thai Kedmanee.
  if (/qwer|asdf|sdfg|zxcv|hjkl|ฟหกด|หกดเ|ๆไำพ/.test(t)) return true;
  return false;
}

export function thaiPhone(p) {
  const d = String(p || "").replace(/[\s\-().]/g, "");
  // 0 + 8 digits (landline, e.g. 053 xxx xxx) or 0 + 9 (mobile, 08x/09x/06x);
  // +66 or 66 drops the leading 0.
  return /^0\d{8,9}$/.test(d) || /^\+?66\d{8,9}$/.test(d);
}
export function plausibleLineId(s) {
  // LINE's own rule for an ID: 4–20 of a-z 0-9 . _ -; an official account
  // starts with @.
  return /^@?[a-z0-9._-]{4,20}$/.test(String(s || "").trim().toLowerCase());
}
const URL_RE = /(https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|org|info|biz|io|xyz|ru|top|co|th|me)(\/|\b))/i;

/* The reasons a confirmed applicant is held for Nan, [] for none.
 * `ipCount` is how many applications share this row's ip_hash in the 24
 * hours before it, this one included. */
export function sanityCheck(L, ipCount) {
  const why = [];
  const email = String(L.email || "").toLowerCase();
  const local = email.split("@")[0];
  const domain = email.split("@")[1] || "";
  if ([...DISPOSABLE].some((d) => domain === d || domain.endsWith("." + d)))
    why.push("disposable email domain");
  for (const [label, v] of [["name", L.full_name], ["office", L.office_name]]) {
    const s = String(v || "").trim();
    if (!s) { why.push(`${label} is empty`); continue; }
    // One letter is not a name or an agency.
    if (letters(s) < 2) why.push(`${label} is too short`);
    // The email pasted into the name box, or its local part.
    if (fold(s) === fold(email) || fold(s) === fold(local)) why.push(`${label} is the email address`);
    // A link in a name box is how spam carries its payload.
    if (URL_RE.test(s)) why.push(`${label} contains a URL`);
    if (looksLikeNoise(s)) why.push(`${label} looks like keyboard noise`);
  }
  // A buyer has to be able to reach them: a Thai number or a LINE ID.
  if (!thaiPhone(L.phone) && !plausibleLineId(L.line_id))
    why.push("phone is not a Thai number and no plausible LINE ID");
  if (ipCount > IP_DAY_MAX) why.push(`${ipCount} applications from one IP in 24 hours`);
  return why;
}

/* A keyed hash of the IP, so rows can be counted per address without the
 * address being written. */
export async function ipHash(ip, secret) {
  if (!ip) return null;
  const d = await crypto.subtle.digest("SHA-256", enc.encode(`${secret || ""}|${ip}`));
  return Array.from(new Uint8Array(d).slice(0, 8), (x) => x.toString(16).padStart(2, "0")).join("");
}

async function ipCountFor(db, L) {
  if (!L.ip_hash) return 1;
  const since = iso(Date.parse(L.created_at) - 24 * 3600 * 1000);
  const r = await db.prepare(`SELECT COUNT(*) AS n FROM listers WHERE ip_hash = ? AND created_at > ?
      AND created_at <= ?`).bind(L.ip_hash, since, L.created_at).first();
  return r ? Number(r.n) : 1;
}

/* ------------------------------------------------------------ state moves */

/* confirmed → invited. perks.lister set, a 7-day single-use sign-in link
 * mailed through the gate. Returns the send result, or null if the row was
 * not 'confirmed'. */
export async function inviteLister(env, L, origin, by) {
  const db = env.SUBSCRIBERS;
  const now = Date.now();
  const tok = newToken();
  const res = await db.prepare(
    `UPDATE listers SET status = 'invited', invited_at = ?, invited_by = ?, signin_token = ?,
       signin_expires = ?, modified_at = ? WHERE member_key = ? AND status = 'confirmed'`
  ).bind(iso(now), by || "operator", tok, iso(now + INVITE_SIGNIN_TTL * 1000), iso(now), L.member_key).run();
  if (!(res && res.meta && res.meta.changes)) return null;
  await setPerk(db, L.email, { member: L.member_key, office: L.office_key, since: iso(now) });
  return sendGated(env, L.email, inviteMail(`${origin}/listings/signin?token=${tok}`));
}

/* ------------------------------------------------------------ pages */

function shell(title, body) {
  return `<!DOCTYPE html><html lang="th" translate="no" class="notranslate"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google" content="notranslate"><meta name="robots" content="noindex">
<title>${esc(title)}</title>
<link rel="icon" href="/logo/motdang-favicon.svg" type="image/svg+xml">
<style>
:root{--paper:#fffdf8;--ink:#1a1408;--mute:#5c4d38;--rule:#c9b895;--red:#b3261e;--go:#0b6b3a}
html{background:var(--paper);color:var(--ink);font:17px/1.55 Georgia,"Times New Roman",Thonburi,serif}
body{margin:0;padding:1.2rem 1rem 3rem;max-width:40em}
h1{font-size:1.5em;margin:.2em 0 .1em}h2{font-size:1.15em;margin:1.6em 0 .2em}
.sub{color:var(--mute);margin:.1em 0 1.2em}
a{color:#0000ee}a:visited{color:#551a8b}
form.md-sub{margin:1em 0;padding:1em;border:1px solid var(--rule);background:#fff}
label{display:block;margin:0 0 .8em}
input[type=email],input[type=text],input[type=tel]{font:inherit;font-size:1.05em;width:100%;max-width:26em;padding:.4em .5em;border:1px solid var(--mute);box-sizing:border-box;margin-top:.25em}
fieldset{border:0;padding:0;margin:0 0 .8em}legend{padding:0;margin-bottom:.2em}
fieldset label{display:inline-flex;gap:.35em;margin:0 1.2em .3em 0}
.consent{display:flex;gap:.55em;align-items:flex-start;font-size:.97em}
.consent input{margin-top:.35em;flex:none}
.hint{color:var(--mute);font-size:.9em;margin:-.5em 0 .8em}
button{font:inherit;padding:.45em 1.1em;background:#f2ebdc;border:1px solid var(--mute);color:var(--ink);cursor:pointer}
.ok{color:var(--go)}.bad{color:var(--red)}
footer{margin-top:2.5em;padding-top:.6em;border-top:1px solid var(--rule);color:var(--mute);font-size:.9em}
</style></head><body>
${body}
<footer><a href="/listings/">กระดานประกาศ · The Listing Sheet</a> · <a href="/">มดแดง Mot Dang</a></footer>
</body></html>`;
}

function htmlResponse(status, body, extra) {
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store",
               "x-robots-tag": "noindex", ...(extra || {}) },
  });
}

export function signinForm() {
  return `<form class="md-sub" action="/listings/signin" method="post">
<label>อีเมล · Email
<input type="email" name="email" required autocomplete="email" inputmode="email"></label>
<button type="submit">เข้าสู่ระบบ · Sign in</button>
</form>`;
}

export function joinForm() {
  const c = LISTER_CONSENT;
  return `<form class="md-sub" action="/listings/join" method="post">
<label>อีเมล · Email
<input type="email" name="email" required autocomplete="email" inputmode="email"></label>
<label>ชื่อ-นามสกุล · Your name
<input type="text" name="name" required autocomplete="name" maxlength="120"></label>
<label>บริษัท / สำนักงาน · Agency or office
<input type="text" name="office" required autocomplete="organization" maxlength="120"></label>
<label>เบอร์โทร · Phone
<input type="tel" name="phone" autocomplete="tel" maxlength="40"></label>
<label>LINE ID
<input type="text" name="line_id" maxlength="60"></label>
<p class="hint">เบอร์โทรหรือ LINE อย่างใดอย่างหนึ่ง · Phone or LINE, one is enough</p>
<fieldset><legend>จังหวัด · Province</legend>
<label><input type="radio" name="province" value="cm" required> เชียงใหม่ · Chiang Mai</label>
<label><input type="radio" name="province" value="cr"> เชียงราย · Chiang Rai</label>
<label><input type="radio" name="province" value="both"> ทั้งสองจังหวัด · Both</label>
<label><input type="radio" name="province" value="north"> จังหวัดอื่นในภาคเหนือ · Elsewhere in the north</label>
</fieldset>
<label class="consent"><input type="checkbox" name="newsletter" value="yes" required>
<span>${esc(c.newsletter.th)}<br>${esc(c.newsletter.en)}</span></label>
<label class="consent"><input type="checkbox" name="reuse" value="yes" required>
<span>${esc(c.reuse.th)}<br>${esc(c.reuse.en)} · <a href="${CC_BY}" rel="license">CC BY 4.0</a></span></label>
<button type="submit">สมัคร · Apply</button>
</form>`;
}

function joinPage() {
  return htmlResponse(200, shell("สมัครลงประกาศ · Join as a listing agent · มดแดง",
    `<h1>สมัครลงประกาศ · Join as a listing agent</h1>
<p class="sub">นายหน้าและบริษัทอสังหาฯ ภาคเหนือ · Agents and agencies, northern Thailand<br>
สมัคร → ยืนยันอีเมล → รับคำเชิญ · Apply → confirm your email → invitation</p>
${joinForm()}
<h2>ได้รับเชิญแล้ว · Invited already</h2>
${signinForm()}`));
}

/* [Thai heading, Thai line, English heading, English line, class, extra] */
const RESULTS = {
  "check-inbox": ["ส่งลิงก์ยืนยันแล้ว", "เปิดอีเมลแล้วกดลิงก์ยืนยัน",
                  "Check your email", "Open the link in it to confirm.", "ok"],  // stylecheck: allow — UI status message
  saved: ["บันทึกใบสมัครแล้ว", "ระบบส่งอีเมลยังไม่เปิดใช้ ใบสมัครเก็บไว้แล้ว",
          "Application saved", "Email is not switched on yet. The application is held.", "ok"],
  "bad-email": ["อีเมลไม่ถูกต้อง", "ลองพิมพ์อีกครั้ง",
                "Check the email", "That did not look like an email address.", "bad", "join"],  // stylecheck: allow — UI status message
  missing: ["ข้อมูลยังไม่ครบ", "ต้องมีชื่อ บริษัท จังหวัด และเบอร์โทรหรือ LINE",
            "Something is missing", "Name, agency, province, and a phone or LINE ID.", "bad", "join"],
  "no-newsletter": ["ยังไม่ได้ติ๊กรับอีเมลข่าว", "การรับอีเมลข่าวเป็นเงื่อนไขของการลงประกาศ",
                    "Newsletter box not ticked", "The newsletter is the condition of listing.", "bad", "join"],
  "no-reuse": ["ยังไม่ได้ติ๊กช่อง CC BY 4.0", "ต้องติ๊กช่องการเผยแพร่ก่อนสมัคร",
               "Reuse box not ticked", "Tick the CC BY 4.0 box to apply.", "bad", "join"],
  error: ["ขัดข้อง", "ลองอีกครั้งในอีกสักครู่", "Something went wrong", "Try again shortly.", "bad"],
  "not-ready": ["ยังไม่พร้อม", "ระบบสมัครยังไม่ได้ตั้งค่า", "Not ready", "Joining is not configured yet.", "bad"],
  confirmed: ["ยืนยันอีเมลแล้ว", "ขั้นต่อไปคือคำเชิญทางอีเมล",
              "Email confirmed", "The next step is an invitation by email.", "ok"],
  "confirmed-invited": ["ยืนยันแล้ว ได้รับเชิญแล้ว", "เข้าสู่ระบบด้วยอีเมลของคุณ",
                        "Confirmed and invited", "Sign in with your email.", "ok", "signin"],
  "confirm-bad": ["ลิงก์ใช้ไม่ได้", "ลิงก์ไม่ถูกต้องหรือหมดอายุ สมัครใหม่ได้",
                  "Link not valid", "This link is not valid or has expired. You can apply again.", "bad", "join"],
  "signin-sent": ["ตรวจอีเมล", "อีเมลที่ได้รับเชิญแล้วจะได้ลิงก์เข้าสู่ระบบ ใช้ได้ 1 ชั่วโมง",
                  "Check your email", "An invited address receives a sign-in link, good for one hour.", "ok"],  // stylecheck: allow — UI status message
  "signin-off": ["ระบบส่งอีเมลยังไม่เปิดใช้", "ยังส่งลิงก์เข้าสู่ระบบไม่ได้",
                 "Email is not switched on yet", "Sign-in links cannot go out yet.", "bad"],
  "signin-bad": ["ลิงก์ใช้ไม่ได้", "ลิงก์หมดอายุหรือใช้ไปแล้ว ขอลิงก์ใหม่ด้านล่าง",
                 "Link not valid", "This sign-in link has expired or was used. Ask for a new one below.", "bad", "signin"],  // stylecheck: allow — UI status message
  "signin-form": ["เข้าสู่ระบบ", "สำหรับผู้ลงประกาศที่ได้รับเชิญ",
                  "Sign in", "For invited listing agents.", "ok", "signin"],
  "signed-out": ["ออกจากระบบแล้ว", "", "Signed out", "", "ok"],
};

function resultPage(key, status, extra) {
  const r = RESULTS[key] || RESULTS.error;
  const tail = r[5] === "join" ? `<p><a href="/listings/join">สมัครลงประกาศ · Join as a listing agent</a></p>`
    : r[5] === "signin" ? signinForm() : "";
  const lines = [r[1], r[3]].filter(Boolean).map(esc).join("<br>");
  return htmlResponse(status, shell(`${r[2]} · มดแดง`,
    `<h1 class="${r[4]}">${esc(r[0])} · ${esc(r[2])}</h1>
${lines ? `<p class="sub">${lines}</p>` : ""}${tail}
<p><a href="/listings/add.html">ลงประกาศ · Add a listing</a></p>`), extra);
}

/* Nan's pages, after a tap. */
function operatorPage(status, th, en, line) {
  return htmlResponse(status, shell(`${en} · มดแดง`,
    `<h1>${esc(th)} · ${esc(en)}</h1>${line ? `<p class="sub">${esc(line)}</p>` : ""}`));
}

function json(status, obj, extra) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store",
               vary: "cookie", ...(extra || {}) },
  });
}

/* ------------------------------------------------------------ form reading */
async function readForm(request) {
  const ct = (request.headers.get("content-type") || "").toLowerCase();
  if (ct.includes("application/json")) {
    let o = {};
    try { o = await request.json(); } catch { /* empty */ }
    return { get: (k) => (o && o[k] != null ? String(o[k]) : null) };
  }
  try { return await request.formData(); }
  catch { return { get: () => null }; }
}

/* ------------------------------------------------------------ handlers */

export async function handleJoin(request, env, url) {
  const f = await readForm(request);
  const email = normalizeEmail(f.get("email"));
  if (!email) return resultPage("bad-email", 400);
  /* Both boxes, here on the server: a stripped checkbox or a JSON caller
   * that left one out writes nothing. */
  if (!f.get("newsletter")) return resultPage("no-newsletter", 400);
  if (!f.get("reuse")) return resultPage("no-reuse", 400);
  const full_name = clean(f.get("name"), 120);
  const office_name = clean(f.get("office"), 120);
  const phone = clean(f.get("phone"), 40);
  const line_id = clean(f.get("line_id"), 60);
  const provinces = PROVINCES[f.get("province")];
  if (!full_name || !office_name || !(phone || line_id) || !provinces) return resultPage("missing", 400);
  if (!env.SUBSCRIBERS) return resultPage("not-ready", 503);
  const lang = LANGS.has(f.get("lang")) ? f.get("lang") : "both";

  const db = env.SUBSCRIBERS;
  const token = newToken();
  const member_key = newToken();
  const now = iso(Date.now());
  try {
    const ip_hash = await ipHash(request.headers.get("cf-connecting-ip"), env.LISTER_SECRET);
    await storePending(db, { email, token, source: "lister", lang, now });
    await upsertLister(db, { member_key, email, full_name, office_name,
      office_key: officeKey(office_name, member_key), phone, line_id, provinces, lang, now, ip_hash });
  } catch (e) {
    console.error("[lister] join store failed", e);
    return resultPage("error", 500);
  }
  /* Every applicant gets a confirm link, whatever state their row is in, so
   * the reply says nothing about whether the address was already known. */
  const sent = await sendGated(env, email, confirmMail(`${url.origin}/listings/join/confirm?token=${token}`));
  return resultPage(sent.sent ? "check-inbox" : "saved", 200);
}

export async function handleJoinConfirm(request, env, url) {
  if (!env.SUBSCRIBERS) return resultPage("not-ready", 503);
  const db = env.SUBSCRIBERS;
  const token = url.searchParams.get("token");
  let res;
  try { res = await confirmToken(db, token, iso(Date.now())); }
  catch (e) { console.error("[lister] confirm failed", e); return resultPage("error", 500); }
  if (!res.ok) return resultPage("confirm-bad", 400);

  const sub = await db.prepare(`SELECT email FROM subscribers WHERE token = ?`).bind(token).first();
  const L = sub && await byColumn(db, "email", sub.email);
  if (!L) return resultPage("confirmed", 200);
  if (L.status === "invited") return resultPage("confirmed-invited", 200);
  if (L.status !== "applied") return resultPage("confirmed", 200);

  const now = Date.now();
  const inv = newToken(), dec = newToken();
  const moved = await db.prepare(
    `UPDATE listers SET status = 'confirmed', confirmed_at = ?, invite_token = ?, invite_expires = ?,
       decline_token = ?, decline_expires = ?, modified_at = ? WHERE member_key = ? AND status = 'applied'`
  ).bind(iso(now), inv, iso(now + OPERATOR_TTL * 1000), dec, iso(now + OPERATOR_TTL * 1000),
         iso(now), L.member_key).run();
  if (!(moved && moved.meta && moved.meta.changes)) return resultPage("confirmed", 200);
  const C = { ...L, status: "confirmed", invite_token: inv, decline_token: dec };

  const why = sanityCheck(C, await ipCountFor(db, C));
  if (why.length) {
    C.held_reasons = JSON.stringify(why);
    await db.prepare(`UPDATE listers SET held_reasons = ? WHERE member_key = ?`)
      .bind(C.held_reasons, C.member_key).run();
  }
  /* Auto mode: a pass is invited, a fail waits; either way Nan hears from
   * the daily digest, not from here. */
  if (env.LISTER_INVITE === "auto") {
    if (why.length) return resultPage("confirmed", 200);
    await inviteLister(env, C, url.origin, "auto");
    return resultPage("confirmed-invited", 200);
  }
  await sendOperator(env, operatorMail(C, url.origin), C.member_key);
  return resultPage("confirmed", 200);
}

const expired = (at) => !at || Date.parse(at) <= Date.now();
const HEX32 = /^[a-f0-9]{32}$/;

export async function handleInvite(request, env, url, token) {
  if (!env.SUBSCRIBERS) return operatorPage(503, "ยังไม่พร้อม", "Not ready", "SUBSCRIBERS is not bound.");
  const L = HEX32.test(token) ? await byColumn(env.SUBSCRIBERS, "invite_token", token) : null;
  if (!L || expired(L.invite_expires))
    return operatorPage(404, "ลิงก์หมดอายุ", "That link has expired", "");
  const who = `${L.full_name} · ${L.office_name} · ${L.email}`;
  if (L.status === "invited") return operatorPage(200, "เชิญไว้แล้ว", "Already invited", who);
  if (L.status !== "confirmed") return operatorPage(409, "เชิญไม่ได้", `Not invited: status is ${L.status}`, who);
  const sent = await inviteLister(env, L, url.origin, "operator");
  return operatorPage(200, "เชิญแล้ว", "Invited", who +
    (sent && sent.sent ? " — sign-in link mailed." : ` — invite mail not sent (${sent ? sent.reason : "?"}).`));
}

export async function handleDecline(request, env, url, token) {
  if (!env.SUBSCRIBERS) return operatorPage(503, "ยังไม่พร้อม", "Not ready", "SUBSCRIBERS is not bound.");
  const db = env.SUBSCRIBERS;
  const L = HEX32.test(token) ? await byColumn(db, "decline_token", token) : null;
  if (!L || expired(L.decline_expires))
    return operatorPage(404, "ลิงก์หมดอายุ", "That link has expired", "");
  const who = `${L.full_name} · ${L.office_name} · ${L.email}`;
  const now = iso(Date.now());
  if (L.status === "invited") {
    await db.prepare(`UPDATE listers SET status = 'revoked', revoked_at = ?, signin_token = NULL,
        signin_expires = NULL, modified_at = ? WHERE member_key = ?`).bind(now, now, L.member_key).run();
    await setPerk(db, L.email, null);
    return operatorPage(200, "ยกเลิกสิทธิ์แล้ว", "Revoked", who);
  }
  if (L.status === "applied" || L.status === "confirmed") {
    await db.prepare(`UPDATE listers SET status = 'declined', declined_at = ?, modified_at = ?
        WHERE member_key = ?`).bind(now, now, L.member_key).run();
    return operatorPage(200, "ปฏิเสธแล้ว", "Declined", who);
  }
  return operatorPage(200, "ทำไปแล้ว", `Already ${L.status}`, who);
}

/* POST: the reply depends on the send gate only, never on the address. */
export async function handleSigninPost(request, env, url) {
  const f = await readForm(request);
  const email = normalizeEmail(f.get("email"));
  if (!email) return resultPage("bad-email", 400);
  if (!env.SUBSCRIBERS) return resultPage("not-ready", 503);
  const db = env.SUBSCRIBERS;
  try {
    const L = await byColumn(db, "email", email);
    const now = Date.now();
    const recent = L && L.signin_sent_at && now - Date.parse(L.signin_sent_at) < SIGNIN_THROTTLE * 1000;
    if (L && L.status === "invited" && !recent) {
      const tok = newToken();
      await db.prepare(`UPDATE listers SET signin_token = ?, signin_expires = ?, signin_sent_at = ?,
          modified_at = ? WHERE member_key = ?`)
        .bind(tok, iso(now + SIGNIN_TTL * 1000), iso(now), iso(now), L.member_key).run();
      await sendGated(env, email, signinMail(`${url.origin}/listings/signin?token=${tok}`));
    }
  } catch (e) {
    console.error("[lister] signin failed", e);
  }
  return resultPage(env.MAILING_LIST_LIVE === "true" ? "signin-sent" : "signin-off", 200);
}

export function cookieHeader(value, maxAge) {
  return `${COOKIE}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`;
}

export async function handleSigninGet(request, env, url) {
  const token = url.searchParams.get("token");
  if (!token) return resultPage("signin-form", 200);
  if (!env.SUBSCRIBERS || !env.LISTER_SECRET) return resultPage("not-ready", 503);
  const db = env.SUBSCRIBERS;
  const L = HEX32.test(token) ? await byColumn(db, "signin_token", token) : null;
  if (!L || L.status !== "invited" || expired(L.signin_expires)) return resultPage("signin-bad", 400);
  const now = iso(Date.now());
  /* Single use: the token is cleared before the cookie is handed over. */
  const res = await db.prepare(`UPDATE listers SET signin_token = NULL, signin_expires = NULL,
      last_signin_at = ?, modified_at = ? WHERE member_key = ? AND signin_token = ?`)
    .bind(now, now, L.member_key, token).run();
  if (!(res && res.meta && res.meta.changes)) return resultPage("signin-bad", 400);
  const cookie = await signCookie(env.LISTER_SECRET, L.member_key, nowSec() + COOKIE_TTL);
  return new Response(null, {
    status: 303,
    headers: { location: "/listings/add.html", "set-cookie": cookieHeader(cookie, COOKIE_TTL),
               "cache-control": "no-store" },
  });
}

export function handleSignout() {
  return new Response(null, {
    status: 303,
    headers: { location: "/listings/add.html", "set-cookie": cookieHeader("", 0),
               "cache-control": "no-store" },
  });
}

/* The signed-in lister, or null: a good cookie AND a row still 'invited'. */
export async function currentLister(request, env) {
  if (!env.SUBSCRIBERS || !env.LISTER_SECRET) return null;
  const c = await verifyCookie(env.LISTER_SECRET, readCookie(request, COOKIE));
  if (!c) return null;
  const L = await byColumn(env.SUBSCRIBERS, "member_key", c.member);
  return L && L.status === "invited" ? L : null;
}

export async function handleMe(request, env) {
  if (!env.SUBSCRIBERS || !env.LISTER_SECRET) return json(503, { ok: false, error: "not configured" });
  let L;
  try { L = await currentLister(request, env); }
  catch (e) { console.error("[lister] me failed", e); return json(500, { ok: false }); }
  if (!L) {
    const had = readCookie(request, COOKIE);
    return json(401, { ok: false, join: JOIN_URL },
      had ? { "set-cookie": cookieHeader("", 0) } : undefined);
  }
  const exp = nowSec() + BEARER_TTL;
  return json(200, {
    ok: true,
    member: { name: L.full_name, office: L.office_name, email: L.email },
    bearer: await signBearer(env.LISTER_SECRET, L.member_key, L.office_key, exp),
    expires: exp,
  });
}

/* ------------------------------------------------------------ the router */

export function ownsLister(p) {
  return p === "/listings/join" || p === "/listings/join/" || p === "/listings/join/confirm" ||
    p === "/listings/signin" || p === "/listings/signout" || p === "/lister/me" ||
    p.startsWith("/listings/invite/") || p.startsWith("/listings/decline/");
}

const notAllowed = (allow) => new Response("Method not allowed", { status: 405, headers: { allow } });

export async function lister(request, env, url) {
  const p = url.pathname;
  const m = request.method;
  const read = m === "GET" || m === "HEAD";
  if (p === "/listings/join" || p === "/listings/join/") {
    if (m === "POST") return handleJoin(request, env, url);
    return read ? joinPage() : notAllowed("GET, POST, HEAD");
  }
  if (p === "/listings/join/confirm")
    return read ? handleJoinConfirm(request, env, url) : notAllowed("GET, HEAD");
  if (p.startsWith("/listings/invite/"))
    return read ? handleInvite(request, env, url, p.slice(17)) : notAllowed("GET, HEAD");
  if (p.startsWith("/listings/decline/"))
    return read ? handleDecline(request, env, url, p.slice(18)) : notAllowed("GET, HEAD");
  if (p === "/listings/signin") {
    if (m === "POST") return handleSigninPost(request, env, url);
    return read ? handleSigninGet(request, env, url) : notAllowed("GET, POST, HEAD");
  }
  if (p === "/listings/signout")
    return m === "POST" ? handleSignout() : notAllowed("POST");
  if (p === "/lister/me") return read ? handleMe(request, env) : notAllowed("GET, HEAD");
  return new Response("Not found", { status: 404 });
}

export default { lister, ownsLister };
