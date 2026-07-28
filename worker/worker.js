// Cloudflare Worker — Mot Dang's claiming layer. KV, capability tokens, no
// accounts. Mirrors the business-claim design in mueang-map/worker/worker.js,
// adapted for the difference that matters: Mot Dang already has 10,281
// canonical places with stable ids (mostly from OSM), so a "claim" targets an
// EXISTING record rather than creating a new one.
//
// KV layout:
//   claim:<placeId>    → {placeId, phone, lineId, facebook, instagram,
//                          whatsapp, email, website, hours, note,
//                          claimedAt, updatedAt}
//   edit:<token>       → placeId   (capability token, same shape as
//                          mueang-map's bizedit:, one claim each)
//   rlc:<ip>:<hour>    → claim count (1h TTL)
//
// Scope is deliberately narrow: a claim carries CONTACT and PRESENTATIONAL
// facts only (how to reach you, your hours, a note) — never name, address,
// or coordinates. Those describe the place itself and a stranger can get
// them wrong, so they stay on the existing "tell the ants" GitHub-issue path
// that a human reads before it goes live. A claim is a business's own account
// of itself — the same reasoning mueang-map uses for instant, unmoderated
// publish — but bounded so the worst case of a bad-faith claim is a wrong
// phone number, never a hijacked or mislocated listing.
//
// Abuse posture (disclosed honestly, same as mueang-map): no tamper-proof
// log, no verification that the claimant is really the owner — just an IP
// rate limit and the narrow field scope above as the backstop.

const MAX_BODY = 20_000
const CLAIM_PER_HOUR = 5
const PLACE_ID_RE = /^(cm|cr)-[a-z0-9-]+$/

const FIELDS = [
  ['phone', 40], ['lineId', 60], ['facebook', 200], ['instagram', 200],
  ['whatsapp', 40], ['email', 200], ['website', 300], ['hours', 200], ['note', 500],
]

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
  return out
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
      if (!Object.keys(fields).length)
        return json({ error: 'add at least one way to reach you — phone, LINE, a page, a site' }, 400)

      const existing = await env.KV.get(`claim:${placeId}`, 'json')
      if (existing)
        return json({ error: 'already claimed — if this is you, use your edit link; '
          + 'if you think this is wrong, tell us on GitHub' }, 409)

      const token = crypto.randomUUID()
      const now = new Date().toISOString()
      const claim = { placeId, ...fields, claimedAt: now, updatedAt: now }
      await env.KV.put(`claim:${placeId}`, JSON.stringify(claim))
      await env.KV.put(`edit:${token}`, placeId)
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json({ ok: true, placeId, editUrl: `${url.origin}/edit/${token}` })
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
      for (const [key] of FIELDS) {
        if (body?.[key] === '') delete claim[key] // explicit empty string clears a field
        else if (fields[key] !== undefined) claim[key] = fields[key]
      }
      claim.updatedAt = new Date().toISOString()
      await env.KV.put(`claim:${placeId}`, JSON.stringify(claim))
      return json({ ok: true, placeId, claim })
    }

    // GET /claims — public; every live claim, for Mot Dang's static build to
    // fold in (see importers/sync_claims.py). No secrets in here — tokens
    // live only under edit:, never returned by this endpoint.
    if (url.pathname === '/claims' && request.method === 'GET') {
      const all = await listPrefix(env, 'claim:')
      return json({ generated: new Date().toISOString(), claims: all })
    }

    return json({ error: 'not found', endpoints: ['/claim', '/edit/:token', '/claims'] }, 404)
  },
}
