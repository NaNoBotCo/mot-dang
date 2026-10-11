// The claims Worker's check of a listing agent's bearer.
//
// publish/lister.js (the site Worker) signs it at GET /lister/me:
//   v1.<member_key>.<office_key>.<exp>.<sig>
// sig = HMAC-SHA256(LISTER_SECRET, "bearer|v1.<member_key>.<office_key>.<exp>"),
// base64url. Both Workers hold LISTER_SECRET as a secret.
// tests/test_lister.mjs signs with that file and verifies with this one.

const enc = new TextEncoder()
const MEMBER_RE = /^[a-f0-9]{32}$/
const OFFICE_RE = /^[a-z0-9฀-๿-]{1,56}$/u

function unb64url(s) {
  if (!/^[A-Za-z0-9_-]+$/.test(s || '')) return null
  try {
    const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4))
    return Uint8Array.from(bin, (c) => c.charCodeAt(0))
  } catch { return null }
}

/* {member, office, exp}, or null: no secret, wrong shape, bad signature,
 * expired. crypto.subtle.verify compares in constant time. */
export async function verifyListerBearer(token, secret, now) {
  if (!secret || typeof token !== 'string' || token.length > 400) return null
  const bits = token.split('.')
  if (bits.length !== 5 || bits[0] !== 'v1') return null
  const [, member, office, expS, sigS] = bits
  if (!MEMBER_RE.test(member) || !OFFICE_RE.test(office)) return null
  const sig = unb64url(sigS)
  if (!sig) return null
  const key = await crypto.subtle.importKey('raw', enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
  const ok = await crypto.subtle.verify('HMAC', key, sig,
    enc.encode(`bearer|v1.${member}.${office}.${expS}`))
  if (!ok) return null
  const exp = Number(expS)
  if (!Number.isInteger(exp) || exp <= (now == null ? Math.floor(Date.now() / 1000) : now)) return null
  return { member, office, exp }
}

/* The gate for POST /listing and /listing-csv. LISTER_REQUIRED "true" makes
 * a valid bearer a condition; otherwise one is recorded when present.
 *   { lister: {member, office} | null }  or  { refuse: <json body> } */
export async function listerGate(body, env) {
  const v = await verifyListerBearer(body && body.lister, env && env.LISTER_SECRET)
  if (v) return { lister: { member: v.member, office: v.office } }
  if ((env && env.LISTER_REQUIRED) === 'true')
    return { refuse: { error: 'sign in as a listing agent to send', join: 'https://motdang.net/listings/join' } }
  return { lister: null }
}

// Photo file names as they land in inbox/<submission>/<name>. The browser's
// own name, so the name the form wrote into the row's `photos` column is the
// file intake.py --photos-pull finds: path parts, control characters and the
// characters a CSV cell or a URL trips on come out; 120 characters.
export function photoName(raw, type) {
  // eslint-disable-next-line no-control-regex
  let s = String(raw || '').split(/[\\/]/).pop().normalize('NFC').replace(/[\u0000-\u001f\u007f"<>|:*?#%,]+/g, '').trim()
  if (s.length > 120) s = s.slice(s.length - 120)
  if (!s || s.startsWith('.')) {
    const ext = type === 'image/png' ? 'png' : type === 'image/webp' ? 'webp'
      : (type === 'image/heic' || type === 'image/heif') ? 'heic' : 'jpg'
    s = `web-${crypto.randomUUID().slice(0, 8)}.${ext}`
  }
  return s
}
