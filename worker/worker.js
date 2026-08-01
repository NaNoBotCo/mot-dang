// Cloudflare Worker — Mot Dang's claiming layer. KV, capability tokens, no
// accounts. Mirrors the business-claim design in mueang-map/worker/worker.js,
// adapted for the difference that matters: Mot Dang already has 10,281+
// canonical places with stable ids (mostly from OSM), so a "claim" targets an
// EXISTING record rather than creating a new one.
//
// Two entry points write the same claim record: the web form (/claim.html →
// POST /claim, POST /edit/:token) and a LINE Messaging API webhook
// (POST /webhook/line) that lets an owner do the whole thing by chatting with
// the site's LINE Official Account — no browser, no account. Both funnel
// through applyClaim() below so validation/capping can never drift between
// them.
//
// KV layout:
//   claim:<placeId>         → {placeId, phone, lineId, facebook, instagram,
//                               whatsapp, email, website, hours, note, menu,
//                               lineUserId?, claimedAt, updatedAt}
//   edit:<token>            → placeId   (capability token, same shape as
//                               mueang-map's bizedit:, one claim each — used
//                               by the web form)
//   rlc:<ip>:<hour>         → web-form claim count (1h TTL)
//   rll:<lineUserId>:<hour> → LINE claim count (1h TTL)
//   linesess:<lineUserId>   → in-progress LINE chat state (15min TTL)
//   lineowner:<lineUserId>  → durable list of placeIds this LINE user has
//                               claimed/edited, so a return visit can ask
//                               "which of your shops?" instead of starting cold
//
// Scope is deliberately narrow: a claim carries CONTACT and PRESENTATIONAL
// facts only (how to reach you, your hours, your menu, a note) — never name,
// address, or coordinates. Those describe the place itself and a stranger can
// get them wrong, so they stay on the existing "tell the ants" path that a
// human reads before it goes live. A claim is a business's own account of
// itself — the same reasoning mueang-map uses for instant, unmoderated
// publish — but bounded so the worst case of a bad-faith claim is a wrong
// phone number, never a hijacked or mislocated listing. The LINE path adds no
// new field scope — it collects the exact same FIELDS as the web form, just
// one at a time in conversation.
//
// Abuse posture (disclosed honestly, same as mueang-map): no tamper-proof
// log, no verification that the claimant is really the owner — just rate
// limits and the narrow field scope above as the backstop. The LINE path adds
// one more backstop the web form does not have: a returning claimant is
// recognized by their LINE identity (lineUserId), so a second person can
// never silently overwrite an existing claim through chat — they are told
// about the conflict instead (see resolveOwnership below).

const MAX_BODY = 20_000
const MAX_WEBHOOK_BODY = 50_000
const CLAIM_PER_HOUR = 5
const PLACE_ID_RE = /^(cm|cr)-[a-z0-9-]+$/
const SESSION_TTL = 900 // 15 minutes between LINE messages before the flow resets
const OWNER_CAP = 20 // most placeIds remembered per LINE user

const FIELDS = [
  ['phone', 40], ['lineId', 60], ['facebook', 200], ['instagram', 200],
  ['whatsapp', 40], ['email', 200], ['website', 300], ['hours', 200],
  ['note', 500], ['menu', 2000],
]

// Facets — what a branch of a chain actually has (a cash machine, a bake-off
// oven, somewhere to sit). Mirrors data/facets.json; tests/test_facets.py
// fails the build if the two lists drift apart, because a key the worker does
// not recognise is silently dropped and the contributor is never told.
//
// This is a closed vocabulary, which makes it the NARROWEST field a claim can
// carry: unlike `note` or `menu`, nothing a submitter types survives contact
// with it — a value is either one of these thirteen words or it is discarded.
// So it needs no length cap and no escaping, and the worst case of a bad-faith
// submission is a wrong tick, never injected content.
const FACET_KEYS = new Set([
  'atm', 'bakery', 'coffee', 'seating', 'hotfood', 'toilet', 'parking',
  'open24', 'wifi', 'aircon', 'wheelchair', 'evcharge', 'twostorey',
])

function readFacets(v) {
  if (!Array.isArray(v)) return null
  const out = [...new Set(v)].filter(k => FACET_KEYS.has(k)).sort()
  return out.length ? out : []
}

// Order the LINE chat asks fields in — likeliest-to-matter-to-a-food-cart
// first. Purely a prompt-ordering list; storage/validation still goes
// through FIELDS above so the two entry points can never disagree on shape.
const CHAT_FIELD_ORDER = ['hours', 'phone', 'lineId', 'facebook', 'menu',
  'instagram', 'whatsapp', 'email', 'website', 'note']

const CHAT_PROMPTS = {
  hours: "เปิด-ปิดกี่โมงคะ? / What are your hours?",
  phone: "เบอร์โทรร้านคืออะไร? / What is the shop's phone number?",
  lineId: "LINE ร้าน (ถ้ามี) คืออะไร? / The shop's own LINE ID, if different from yours?",
  facebook: "มีเพจ Facebook ไหม? ส่งลิงก์มาได้เลย / A Facebook page link, if you have one?",
  menu: "มีเมนู/ของขายอะไรบ้าง? พิมพ์มาได้เลย / What do you sell? (menu items, free text)",
  instagram: "Instagram ร้าน (ถ้ามี)? / Instagram, if you have one?",
  whatsapp: "WhatsApp (ถ้ามี)? / WhatsApp, if you have one?",
  email: "อีเมลร้าน (ถ้ามี)? / An email, if you have one?",
  website: "เว็บไซต์ร้าน (ถ้ามี)? / A website, if you have one?",
  note: "มีอะไรอยากบอกเพิ่มไหม? / Anything else you want to add?",
}

const SKIP_RE = /^(ไม่มี|ข้าม|skip|-)$/i
const FINISH_RE = /^(จบ|เสร็จ|done|บันทึก|save)$/i
const CANCEL_RE = /^(ยกเลิก|cancel|เริ่มใหม่|restart)$/i
const ID_MARKER_RE = /\[id:((?:cm|cr)-[a-z0-9-]+)\]/

const cap = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '') || ''

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type',
}
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', ...CORS } })

async function listPrefix(env, prefix) {
  const out = []
  let cursor
  do {
    const page = await env.KV.list({ prefix, cursor })
    for (const k of page.keys) {
      const v = await env.KV.get(k.name, 'json')
      if (v) out.push(v)
    }
    cursor = page.list_complete ? null : page.cursor
  } while (cursor)
  return out
}

function readFields(body) {
  const out = {}
  for (const [key, max] of FIELDS) {
    const v = cap(body?.[key], max)
    if (v) out[key] = v
  }
  // An empty array is a real answer — "I looked, and it has none of these" —
  // so it is kept, while an absent key means the submitter never saw the
  // question. Only null (not an array at all) is treated as "not asked".
  const f = readFacets(body?.facets)
  if (f !== null) out.facets = f
  return out
}

// The single writer /claim, /edit/:token, and the LINE webhook all call —
// keeps validation/capping identical across every entry point.
async function applyClaim(env, placeId, fields, opts = {}) {
  const key = `claim:${placeId}`
  const existing = await env.KV.get(key, 'json')

  if (opts.mode === 'create') {
    if (existing) return { error: 'already claimed — if this is you, use your edit link; '
      + 'if you think this is wrong, tell us on GitHub', status: 409 }
    // Facets alone can never open a claim. Claiming locks the record against
    // everyone else, so letting a passer-by do it by ticking "has an ATM"
    // would let a stranger lock a shop out of its own listing — a much worse
    // outcome than the missing tick. Contributing facets without claiming is
    // a different door (see the facet checklist on the place page).
    if (!FIELDS.some(([k]) => fields[k] !== undefined))
      return { error: 'add at least one way to reach you — phone, LINE, a page, a site', status: 400 }
    const token = crypto.randomUUID()
    const now = new Date().toISOString()
    const claim = { placeId, ...fields, claimedAt: now, updatedAt: now }
    if (opts.lineUserId) claim.lineUserId = opts.lineUserId
    await env.KV.put(key, JSON.stringify(claim))
    await env.KV.put(`edit:${token}`, placeId)
    return { ok: true, placeId, editToken: token, claim }
  }

  // edit
  if (!existing) return { error: 'no such claim record', status: 404 }
  for (const [k] of [...FIELDS, ['facets']]) {
    if (opts.clears?.includes(k)) delete existing[k]
    else if (fields[k] !== undefined) existing[k] = fields[k]
  }
  existing.updatedAt = new Date().toISOString()
  await env.KV.put(key, JSON.stringify(existing))
  return { ok: true, placeId, claim: existing }
}

// ---- LINE Messaging API helpers -------------------------------------------

async function verifyLineSignature(body, signature, secret) {
  if (!signature) return false
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const mac = new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(body)))
  let sigBytes
  try { sigBytes = Uint8Array.from(atob(signature), c => c.charCodeAt(0)) } catch { return false }
  if (sigBytes.length !== mac.length) return false
  let diff = 0
  for (let i = 0; i < mac.length; i++) diff |= mac[i] ^ sigBytes[i] // constant-time compare
  return diff === 0
}

async function lineReply(env, replyToken, text) {
  try {
    await fetch('https://api.line.me/v2/bot/message/reply', {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${env.LINE_CHANNEL_TOKEN}` },
      body: JSON.stringify({ replyToken, messages: [{ type: 'text', text }] }),
    })
  } catch (err) { console.error('line reply failed', err) } // never let a reply failure break the webhook ack
}

// The same published file the web form's loadIndex() searches — cached
// briefly so a burst of chat messages does not refetch a ~1MB file per
// message. No separate data pipeline: this repo has exactly one source of
// truth for the catalog, and the worker reads it the same way a browser does.
async function fetchIndex() {
  const req = new Request('https://motdang.net/data/index.json')
  const cache = caches.default
  let res = await cache.match(req)
  if (!res) {
    const live = await fetch(req)
    res = new Response(live.body, live)
    res.headers.set('cache-control', 'public, max-age=600')
    await cache.put(req, res.clone())
  }
  return res.json()
}

function searchPlaces(idx, q) {
  const needle = q.trim().toLowerCase()
  if (!needle) return []
  return idx.filter(e => (e.n + ' ' + (e.e || '')).toLowerCase().includes(needle)).slice(0, 5)
}

function candidateList(candidates) {
  return candidates.map((e, i) => `${i + 1}. ${e.n} · ${e.pv}`).join('\n')
}

async function getSession(env, userId) {
  return (await env.KV.get(`linesess:${userId}`, 'json')) || null
}
async function putSession(env, userId, session) {
  await env.KV.put(`linesess:${userId}`, JSON.stringify(session), { expirationTtl: SESSION_TTL })
}
async function clearSession(env, userId) {
  await env.KV.delete(`linesess:${userId}`)
}
async function pushLineOwner(env, userId, placeId) {
  const key = `lineowner:${userId}`
  const list = (await env.KV.get(key, 'json')) || []
  const next = [placeId, ...list.filter(id => id !== placeId)].slice(0, OWNER_CAP)
  await env.KV.put(key, JSON.stringify(next))
}

// Same conflict posture as the existing /claim 409: a claim is never
// silently overwritten by someone the record does not already recognize.
async function resolveOwnership(env, placeId, lineUserId) {
  const existing = await env.KV.get(`claim:${placeId}`, 'json')
  if (!existing) return { mode: 'create' }
  if (existing.lineUserId && existing.lineUserId === lineUserId) return { mode: 'edit', claim: existing }
  return { mode: 'conflict' }
}

async function startSearch(env, userId, query, replyToken) {
  const idx = await fetchIndex().catch(() => [])
  const hits = searchPlaces(idx, query)
  if (!hits.length) {
    await lineReply(env, replyToken,
      "ยังไม่เจอร้านนี้ในสารบัญค่ะ ลองพิมพ์ชื่อร้านอีกครั้ง หรือขอให้ทีมงานเพิ่มร้านได้ที่ motdang.net/crawl-request.html\n"
      + "Not found yet — try a different spelling, or ask us to add it at motdang.net/crawl-request.html")
    return
  }
  await putSession(env, userId, { step: 'awaiting_pick', candidates: hits })
  await lineReply(env, replyToken,
    `เจอร้านเหล่านี้ค่ะ:\n${candidateList(hits)}\n\nตอบเลขได้เลยค่ะ / Reply with a number.`)
}

async function handlePick(env, userId, session, text, replyToken) {
  const n = Number(text.trim())
  if (session.allowNew && n === 0) {
    await clearSession(env, userId)
    await lineReply(env, replyToken, "พิมพ์ชื่อร้านที่ต้องการยืนยันได้เลยค่ะ / Type the name of the shop you want to claim.")
    return
  }
  const picked = Number.isInteger(n) && n >= 1 ? session.candidates[n - 1] : null
  if (!picked) {
    await lineReply(env, replyToken, "ตอบเป็นเลขในรายการนะคะ (เช่น 1) / Please reply with one of the listed numbers.")
    return
  }
  await startCollecting(env, userId, picked.id, replyToken)
}

async function startCollecting(env, userId, placeId, replyToken) {
  if (!PLACE_ID_RE.test(placeId)) return // defensive; should never happen from our own candidate lists
  const own = await resolveOwnership(env, placeId, userId)
  if (own.mode === 'conflict') {
    await clearSession(env, userId)
    await lineReply(env, replyToken,
      "ร้านนี้มีคนยืนยันไว้แล้วค่ะ ถ้าเป็นร้านของคุณจริง แก้ไขผ่านลิงก์ส่วนตัวที่เคยได้รับ หรือแจ้งได้ที่ motdang.net/claim.html\n"
      + "This place is already claimed. If it is really your shop, use your private edit link, or tell us at motdang.net/claim.html.")
    return
  }
  const session = { step: 'collecting', placeId, mode: own.mode, fieldIdx: 0, draft: {} }
  await putSession(env, userId, session)
  await promptField(env, userId, session, replyToken, true)
}

async function promptField(env, userId, session, replyToken, isFirst) {
  const field = CHAT_FIELD_ORDER[session.fieldIdx]
  if (!field) return finalizeSession(env, userId, session, replyToken)
  const lead = isFirst
    ? "ได้เลยค่ะ! ตอบทีละข้อ พิมพ์ \"ข้าม\" เพื่อข้าม หรือ \"จบ\" เพื่อบันทึกตอนนี้เลย\n"
    : ""
  await lineReply(env, replyToken, lead + CHAT_PROMPTS[field])
}

async function handleCollect(env, userId, session, text, replyToken) {
  if (FINISH_RE.test(text)) return finalizeSession(env, userId, session, replyToken)
  const field = CHAT_FIELD_ORDER[session.fieldIdx]
  if (field && !SKIP_RE.test(text)) {
    const max = FIELDS.find(([k]) => k === field)?.[1] || 500
    session.draft[field] = cap(text, max)
  }
  session.fieldIdx += 1
  await putSession(env, userId, session)
  await promptField(env, userId, session, replyToken, false)
}

async function finalizeSession(env, userId, session, replyToken) {
  await clearSession(env, userId)
  if (!Object.keys(session.draft).length) {
    await lineReply(env, replyToken,
      "ยังไม่ได้บันทึกอะไรเลยค่ะ (ไม่มีข้อมูล) พิมพ์ชื่อร้านใหม่เพื่อเริ่มอีกครั้ง\n"
      + "Nothing saved (no fields given) — type a shop name to start again.")
    return
  }

  if (session.mode === 'create') {
    const bucket = `rll:${userId}:${Math.floor(Date.now() / 3600_000)}`
    const count = Number((await env.KV.get(bucket)) || 0)
    if (count >= CLAIM_PER_HOUR) {
      await lineReply(env, replyToken,
        "ขอโทษค่ะ ยืนยันได้หลายร้านเกินไปในชั่วโมงนี้ ลองใหม่อีกครั้งภายหลังนะคะ\n"
        + "Too many claims this hour — please try again later.")
      return
    }
    const result = await applyClaim(env, session.placeId, session.draft, { mode: 'create', lineUserId: userId })
    await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
    if (result.error) { await lineReply(env, replyToken, result.error); return }
    await pushLineOwner(env, userId, session.placeId)
    await lineReply(env, replyToken,
      "บันทึกแล้วค่ะ! ✅ ขึ้นในเว็บทันที ขอบคุณที่ช่วยให้ข้อมูลถูกต้องนะคะ 🐜\n"
      + "Saved! It is live on the site now. Thank you for helping keep the information accurate.")
    return
  }

  const result = await applyClaim(env, session.placeId, session.draft, { mode: 'edit' })
  if (result.error) { await lineReply(env, replyToken, result.error); return }
  await pushLineOwner(env, userId, session.placeId)
  await lineReply(env, replyToken, "อัปเดตแล้วค่ะ! ✅ / Updated!")
}

async function handleLineEvent(env, ev) {
  const userId = ev.source?.userId
  const replyToken = ev.replyToken
  if (!userId) return // group/room events with no linkable user identity; nothing we can key state on

  if (ev.type === 'follow') {
    if (replyToken) await lineReply(env, replyToken,
      "สวัสดีค่ะ 🐜 อยากยืนยันร้านไหม? พิมพ์ชื่อร้านมาได้เลย หรือกดปุ่ม \"ยืนยันร้านของฉัน\" จากหน้าร้านใน motdang.net\n"
      + "Hi! Want to claim your shop? Type its name, or tap \"This is my place\" from your motdang.net page.")
    return
  }

  if (ev.type !== 'message') return // postbacks, unfollow, etc — nothing to do in v1

  if (ev.message.type !== 'text') {
    if (replyToken) await lineReply(env, replyToken,
      "ตอนนี้บอทอ่านได้แค่ข้อความตัวหนังสือค่ะ (ยังไม่รับรูป) แต่พิมพ์บอกได้เลย มีคนอ่านแชทนี้ด้วย\n"
      + "The bot only reads text for now (no photos yet) — go ahead and type; a person also checks this chat.")
    return
  }

  if (!replyToken) return // nothing meaningful to do without one
  const text = (ev.message.text || '').trim()

  if (CANCEL_RE.test(text)) {
    await clearSession(env, userId)
    await lineReply(env, replyToken,
      "ยกเลิกแล้วค่ะ พิมพ์ชื่อร้านใหม่ได้เลยเมื่อพร้อม / Cancelled — type a shop name whenever you are ready.")
    return
  }

  // Deep-link marker always wins, even mid-session — e.g. she tapped a
  // different place's claim button while already mid-chat about another one.
  const marker = text.match(ID_MARKER_RE)
  if (marker && PLACE_ID_RE.test(marker[1])) {
    await startCollecting(env, userId, marker[1], replyToken)
    return
  }

  const session = await getSession(env, userId)
  if (session) {
    if (session.step === 'awaiting_pick') { await handlePick(env, userId, session, text, replyToken); return }
    if (session.step === 'collecting') { await handleCollect(env, userId, session, text, replyToken); return }
  }

  // Cold start, known user — offer her own places before treating free text
  // as a fresh name search.
  const owned = await env.KV.get(`lineowner:${userId}`, 'json')
  if (owned?.length) {
    const idx = await fetchIndex().catch(() => [])
    const named = owned.slice(0, 5).map(id => idx.find(e => e.id === id)).filter(Boolean)
    if (named.length) {
      await putSession(env, userId, { step: 'awaiting_pick', candidates: named, allowNew: true })
      await lineReply(env, replyToken,
        `ร้านของคุณ:\n${candidateList(named)}\n0. ร้านอื่น (พิมพ์ชื่อร้าน)\n\nตอบเลขได้เลยค่ะ / Reply with a number, or 0 for a different shop.`)
      return
    }
  }

  await startSearch(env, userId, text, replyToken)
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS })

    // POST /claim — anyone; claims one existing place, once. Publishes instantly.
    if (url.pathname === '/claim' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rlc:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= CLAIM_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)

      const text = await request.text()
      if (text.length > MAX_BODY) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }

      const placeId = cap(body?.placeId, 60)
      if (!placeId || !PLACE_ID_RE.test(placeId))
        return json({ error: 'placeId missing or not a recognized Mot Dang id' }, 400)

      const fields = readFields(body)
      const result = await applyClaim(env, placeId, fields, { mode: 'create' })
      if (result.error) return json({ error: result.error }, result.status)

      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json({ ok: true, placeId: result.placeId, editUrl: `${url.origin}/edit/${result.editToken}` })
    }

    // GET/POST /edit/:token — the owner's private capability link.
    if (url.pathname.startsWith('/edit/')) {
      const token = url.pathname.slice('/edit/'.length)
      const placeId = token && await env.KV.get(`edit:${token}`)
      if (!placeId) return json({ error: 'invalid or revoked edit link' }, 404)
      const claim = await env.KV.get(`claim:${placeId}`, 'json')
      if (!claim) return json({ error: 'no such claim record' }, 404) // orphaned token; shouldn't happen

      if (request.method === 'GET') return json({ ok: true, placeId, claim })
      if (request.method !== 'POST') return json({ error: 'method not allowed' }, 405)

      let body
      try { body = await request.json() } catch { return json({ error: 'invalid json' }, 400) }
      const fields = readFields(body)
      const clears = FIELDS.filter(([k]) => body?.[k] === '').map(([k]) => k)
      const result = await applyClaim(env, placeId, fields, { mode: 'edit', clears })
      if (result.error) return json({ error: result.error }, result.status)
      return json({ ok: true, placeId: result.placeId, claim: result.claim })
    }

    // GET /claims — public; every live claim, for Mot Dang's static build to
    // fold in (see importers/sync_claims.py). No secrets in here — tokens
    // live only under edit:, never returned by this endpoint.
    if (url.pathname === '/claims' && request.method === 'GET') {
      const all = await listPrefix(env, 'claim:')
      return json({ generated: new Date().toISOString(), claims: all })
    }

    // POST /webhook/line — LINE Messaging API callback. Lets an owner run the
    // whole claim/edit flow by chatting with the site's LINE Official
    // Account instead of using the web form; writes through the exact same
    // applyClaim() the routes above use.
    if (url.pathname === '/webhook/line' && request.method === 'POST') {
      const raw = await request.text()
      if (raw.length > MAX_WEBHOOK_BODY) return new Response('too large', { status: 400 })
      const sig = request.headers.get('x-line-signature')
      if (!env.LINE_CHANNEL_SECRET || !(await verifyLineSignature(raw, sig, env.LINE_CHANNEL_SECRET)))
        return new Response('bad signature', { status: 401 })
      let body
      try { body = JSON.parse(raw) } catch { return new Response('bad json', { status: 400 }) }
      for (const ev of body.events || []) {
        try { await handleLineEvent(env, ev) }
        catch (err) { console.error('line event failed', err) } // one bad event never breaks the ack
      }
      return new Response('ok', { status: 200 }) // LINE's console "Verify" sends events:[] and expects 200
    }

    return json({ error: 'not found', endpoints: ['/claim', '/edit/:token', '/claims', '/webhook/line'] }, 404)
  },
}
