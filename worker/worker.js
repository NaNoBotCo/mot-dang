// Cloudflare Worker — Mot Dang's claiming layer. KV, capability tokens, no
// accounts. Mirrors the business-claim design in mueang-map/worker/worker.js,
// adapted for the difference that matters: Mot Dang already has 10,281+
// canonical places with stable ids (mostly from OSM), so a "claim" targets an
// EXISTING record rather than creating a new one.
//
// Two entry points write the same claim record: the web form (/claim.html →
// POST /claim, POST /edit/:token) and a LINE Messaging API webhook
// (POST /webhook/line) that lets an owner do the whole thing by chatting with
// the site's LINE Official Account — no browser, no sign-in. Both funnel
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
// Abuse posture (disclosed, same as mueang-map): no tamper-proof
// log, no verification that the claimant is really the owner — just rate
// limits and the narrow field scope above as the backstop. The LINE path adds
// one more backstop the web form does not have: a returning claimant is
// recognized by their LINE identity (lineUserId), so a second person can
// never silently overwrite an existing claim through chat — they are told
// about the conflict instead (see resolveOwnership below).

import { EmailMessage } from "cloudflare:email"
import { listerGate, verifyListerBearer, photoName } from './lister_bearer.js'

const MAX_BODY = 20_000
const MAX_WEBHOOK_BODY = 50_000
const CLAIM_PER_HOUR = 5
// Looser than a claim on purpose: a claim edits a listing, a suggestion only
// asks a human to look at something, and the cost of a wasted read is smaller
// than the cost of turning away somebody with three corrections to give.
const SUGGEST_PER_HOUR = 12
const SUGGEST_KINDS = new Set([
  'correction',   // something on a page is wrong
  'missing',      // a place we do not have at all
  'contact',      // a phone, LINE, or page for a listing with none
  'photo',        // somebody is offering a picture
  'crawl',        // a corner of the province worth sending the ants to
  'question',     // a reader question for asked.html — where do I find X
  // 2026-09-10: the three ways a listing stops being true. `detail` on the
  // record carries the specifics — since when, moved where, a duplicate of
  // which page — so the queue reader is not left guessing from `what`.
  'closed',       // ปิดถาวร — shut for good
  'moved',        // ย้ายแล้ว — same shop, new address
  'duplicate',    // ซ้ำ — two records for one place
  'other',
])
const SUGGEST_DETAIL_MAX = 300
// Nan 2026-09-29: coverage is all of northern Thailand (data/coverage.json —
// the 17 provinces; we crawl CM and CR, and take what arrives from the rest).
// Pathum Thani (pth), crawled since 2026-10-12, her word.
const PROVINCE_KEYS = 'cm|cr|pth|lpn|lpg|utt|pre|nan|pyo|mhs|nsn|uti|kpt|tak|sti|plk|pct|pnb'
const NORTH = { south: 14.8, north: 20.5, west: 97.3, east: 101.8 }
const PLACE_ID_RE = new RegExp(`^(${PROVINCE_KEYS})-[a-z0-9-]+$`)
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
//
// The five toilet keys are the sit-down set. `toilet` (convenience stores)
// means "there is one around here" — a 30 m spatial join, evidence about the
// street. `toilethere` means somebody used the one inside. Different claims,
// deliberately different words. `toiletnone` is the only key on this site
// that records an absence, because a person who stood at the door and found
// nothing is giving testimony rather than inferring.
// The massage keys, added 2026-08-17, are the frame and the register: what
// comes off, what you lie on, who else is in the room, whose licence is on the
// wall. `hsscert` is a positive fact only — there is deliberately no
// "no-certificate-seen" key, because unlike a toilet a licence can sit behind
// a counter, so an absence there is one person's afternoon rather than
// testimony, and it would land on a named business.
const FACET_KEYS = new Set([
  'atm', 'bakery', 'coffee', 'seating', 'hotfood', 'toilet', 'parking',
  'open24', 'wifi', 'aircon', 'wheelchair', 'evcharge', 'twostorey',
  // WO-38, the convenience set's evidence keys: cards taken, on/beside a
  // petrol forecourt, and the Slurpee machine (two witnesses and counting).
  'card', 'atstation', 'slurpee',
  // WO-40, the professional set's one new key: a Lawyers Council notarial
  // services attorney on staff. english/booking/card already exist above.
  'notary',
  // 2026-09-05: the sit-down set gained takeaway alongside the seating and
  // delivery keys it already shared with convenience and cannabis. All three
  // tag rules existed in import_fixtures and all three values were already on
  // the records; the set simply never declared them, so 263 restaurants and
  // cafes held an answer nothing could ask for.
  'takeaway',
  // WO-48, the pest-control set. `fdalicence` is the one that decides
  // whether a firm may legally spray at all — permission for type-3
  // hazardous substances under the Hazardous Substances Act B.E. 2535,
  // which the FDA publishes a lookup for. Positive only, on the hsscert
  // rule: a certificate can sit in a drawer, so no absence key.
  // The four animals are asked apart because a bed-bug house and a termite
  // house are not looking for the same firm. bait/pipe are the two ways a
  // termite job is done and the reason two quotes differ. `herbal` records
  // that a firm SAYS it works without chemicals, never that it does.
  // `petsafe` wants a number of hours, not a reassurance.
  'fdalicence', 'termite', 'rodent', 'bedbug', 'mosquito',
  'baitsystem', 'pipesystem', 'herbal', 'warranty', 'petsafe',
  // WO-49, the tailoring set. One English word — tailor — covers four
  // trades that want four different shops, so these keys exist to keep them
  // apart rather than to grade one shop against another. `uniform` and its
  // three specifics (`fulldresswhite`, `policeMilitary`, `insignia`) are the
  // half of the trade the site held nothing of; `insignia` matters because
  // the shop that cuts the cloth and the shop that supplies the shoulder
  // boards are usually two different shops. `eveningwear`, `thaiformal` and
  // `bridal` are the ห้องเสื้อ half, which is nowhere near the suit street.
  // `rental` is the fork a resident takes first — a hired ชุดปกติขาว is 550
  // baht against several thousand to have one made. `copyGarment`,
  // `english` (already above) and `bigsizes` are the three a long-stayer actually
  // filters on, and all three want a person's answer, not a tag.
  // `repairs`, `schoolkit` and `sportskit` complete the four trades.
  'uniform', 'fulldresswhite', 'policemilitary', 'insignia',
  'schoolkit', 'sportskit', 'eveningwear', 'thaiformal', 'bridal',
  'rental', 'repairs', 'copygarment', 'bigsizes',
  // WO-54, the paper set. A copy shop sells a copy; a translator or visa
  // agent prepares a document — two trades that share one counter at the
  // gate of the district office, so the keys keep them apart. `idphoto` is
  // the 4x6 immigration size; `formhelp` is the ร้านหน้าอำเภอ service of
  // filling the form in; `mfarun` and `visaagent` are paid errands and the
  // reader should know which one they are buying.
  'printphone', 'binding', 'laminate', 'scan', 'bigformat', 'idphoto',
  'formhelp', 'certtrans', 'mfarun', 'visaagent',
  'toilethere', 'toiletfree', 'toiletfee5', 'toiletfee10', 'toiletnone',
  'clothed', 'undress', 'scrubglove', 'mat', 'table', 'chair', 'sharedroom',
  'privateroom',
  'priceboard', 'womantherapist', 'mantherapist', 'walkin', 'booking', 'shower',
  'hsscert', 'ttmclinic', 'ttmlicensed', 'blindop', 'exprisoner', 'hospitalttm',
  'hotelspa', 'homeshop', 'school',
  // เสริมสวย-ตัดผม (WO-22). `priceboard`, `walkin`, `booking`, `english`,
  // `parking`, `wheelchair`, `aircon`, `wifi` and `card` are already above and
  // mean the same thing in a hair shop. These are the ones that do not exist
  // anywhere else on the site — and they matter because OpenStreetMap holds
  // NOTHING about what a hair shop can do. `mencut`/`womencut`/`unisex` are
  // the only three it knows, and they arrive from the importer; every other
  // key here can only ever be set by the shop itself or by a person at the
  // door, which is exactly what this endpoint is for.
  'mencut', 'womencut', 'unisex', 'kids',
  'textured', 'braids', 'extensions', 'wigs', 'updo',
  'digiperm', 'rebond', 'colour', 'bleach',
  'fade', 'razorshave', 'beard',
  'scalpcheck', 'treatment', 'keratin',
  'housecall', 'latenight',
  // กัญชา-กระท่อม. `priceboard`, `seating`, `open24`, `wifi`, `parking` and
  // `wheelchair` are already above and mean the same thing on this shelf.
  'openlate', 'smokingok', 'delivery', 'advice', 'english', 'kratomdrink',
  'card', 'crypto',
  // Clinics. `priceboard`, `openlate`, `open24`, `english`, `parking` and
  // `wheelchair` are already above and mean the same thing at a clinic door.
  'bathong', 'sosec', 'foreigninsure', 'weekend', 'walkin', 'chinese',
  'kammuang',
  // Schools. `priceboard` is not reused here — a school's fee is a term's
  // fee and `feeposted` says so in the words a parent uses. `parking` and
  // `wheelchair` are already above and mean the same thing at a school gate.
  'engmedium', 'epmep', 'bilingual', 'chineseprog', 'foreignstudents',
  'edvisa', 'dropin', 'feeposted', 'scholarship', 'busservice', 'boarding',
  'lunch', 'halal',
  // มวยไทย. `dropin`, `edvisa`, `boarding`, `priceboard`, `english`,
  // `shower`, `parking` and `wheelchair` are already above and mean the
  // same thing at a camp door or a stadium gate.
  'beginner', 'womentrain', 'kids', 'privateclass', 'fighters', 'fightnights',
  'gearsold',
  // เรียนทำอาหาร. `kids`, `privateclass`, `english`, `halal`, `edvisa`,
  // `priceboard`, `aircon`, `parking` and `wheelchair` are already above and
  // mean the same thing at a cooking-school door.
  'sameday', 'eveningclass', 'halfday', 'markettour', 'pickupfree',
  'ownstation', 'vegoption', 'allergyok', 'thaitaught', 'recipebook',
  'certgiven', 'multiday', 'opeclicence', 'tourlicence',
  // ช้าง. `priceboard` and `kids` are already above and mean the same thing
  // at a camp gate. Each of these is a statement the camp makes about itself
  // (no riding, a hands-off option, no hook, unchained at night, a vet,
  // papers shown…); nothing here is ever inferred from a name or a shelf.
  'noride', 'ride', 'bathe', 'feed', 'observe', 'noshow', 'nohook',
  'nightfree', 'vet', 'tuaruppaphan', 'mahoutday', 'overnight', 'volunteer',
  'pickup',
  // อสังหาฯ-ที่พัก (WO realestate, 2026-08-21). `aircon`, `wifi`, `parking`,
  // `wheelchair` and `open24` are already above and mean the same thing at a
  // building's desk. These are the ones that decide whether a person takes
  // the room and exist nowhere in OSM — the per-unit electric rate most of
  // all. Each is a policy the building states about itself; nothing here is
  // ever inferred from a name, and the foreign-quota number is deliberately
  // NOT a key (it changes with every transfer — a dated statement in
  // data/curated/realestate.json is the only shape it may take).
  'monthly', 'daily', 'furnished', 'lift', 'pool', 'gym', 'keycard', 'pets',
  'laundry', 'rateboard', 'shortok', 'guard',
])

function readFacets(v) {
  if (!Array.isArray(v)) return null
  const out = [...new Set(v)].filter(k => FACET_KEYS.has(k)).sort()
  return out.length ? out : []
}

// ---- toilet reports --------------------------------------------------------
// A passer-by is not an owner, so a toilet report is not a claim and does not
// live in one. applyClaim() refuses to open a claim from ticks alone, and that
// guard is right: claiming locks a record against everyone else, and a
// stranger reporting "there is a toilet here" must never be able to do that to
// a shop. So reports get their own key, their own endpoint, and no capability
// token — there is nothing here worth capturing.
//
// Worst case of a bad-faith report is one wrong word out of five, on one
// place, overwritten by the next person who looks. The vocabulary is closed
// and nothing typed survives it.
const TOILET_KEYS = ['toilethere', 'toiletfree', 'toiletfee5', 'toiletfee10', 'toiletnone']
const TOILET_PER_HOUR = 20
// /rain and /flood: answers a reader may give, how many an hour, how long kept.
const OBS_PER_HOUR = 12
const OBS_ANSWERS = { rain: ['none', 'light', 'heavy'],
  flood: ['ankle', 'knee', 'waist', 'chest', 'roof', 'dry'],
  // Nan, 2026-09-28: "a 'can you see doi suthep' button for smoke"
  suthep: ['clear', 'hazy', 'gone'] }
const OBS_TTL = { rain: 30 * 86400, flood: 7 * 86400, suthep: 30 * 86400 }

const TOILET_LABEL = {
  toilethere: 'มีห้องน้ำให้ใช้ / there is one you can use',
  toiletfree: 'ใช้ฟรี / free to use',
  toiletfee5: 'เก็บ ๕ บาท / costs 5 baht',
  toiletfee10: 'เก็บ ๑๐ บาท / costs 10 baht',
  toiletnone: 'ที่นี่ไม่มี / none here',
}

async function putToiletReport(env, placeId, report, source) {
  if (!TOILET_KEYS.includes(report)) return { error: 'unknown report', status: 400 }
  if (!PLACE_ID_RE.test(placeId)) return { error: 'bad place id', status: 400 }
  const now = new Date().toISOString()
  const prev = await env.KV.get(`toilet:${placeId}`, 'json')
  const rec = {
    placeId, report, source, at: now,
    firstAt: prev?.firstAt || now,
    // How many people have said something about this spot. A second report
    // agreeing with the first is the cheapest confidence this site can buy.
    seen: (prev?.seen || 0) + 1,
    agrees: prev?.report === report ? (prev?.agrees || 1) + 1 : 1,
  }
  await env.KV.put(`toilet:${placeId}`, JSON.stringify(rec))
  return { ok: true, ...rec }
}

// ---- doodle votes ------------------------------------------------------------
// A thumb up or down on one version of one doodle (/doodles/), on accuracy and
// on aesthetics, with a note. Nan, 2026-10-05: "humans and bots …
// thumbs-up/thumbs-down doodles based on accuracy and aesthetics", then: "not
// discriminating between bots and humans, paying $0.001 dollars per like/dislike
// + brief explanation", and "notes about what's right/wrong with the picture, and
// get paid more for thoroughness, up to 5 cents." Everyone is counted the same way.
// Nan, 2026-10-05, for the lists: a like or dislike on the picture as a whole ("most liked",
// "controversial") and a favourite, both beside the two axes ("why not both?").
//   dvv:<id>@<v>:<voter>   the voter's own votes (one per axis; a second replaces the first)
//   dvt:<id>@<v>           tallies, each axis [up, down]; fav is [count, 0]
//   dve:<at>:<rand>        one event per change, with its note and payout address,
//                          for tools/doodle_score.py (weights, flags, the payout ledger)
const DOODLE_ID_RE = /^[cfmps]-[a-z0-9-]{1,160}$/
const DOODLE_AXES = ['accuracy', 'aesthetics', 'like']
const DOODLE_MARKS = ['fav']   // 1 or 0: there is no down
const DOODLE_PER_HOUR = 120
const PAYEE_RE = /^[A-Za-z0-9@._:+-]{3,120}$/

async function voterId(request) {
  const raw = (request.headers.get('cf-connecting-ip') || '') + '|' + (request.headers.get('user-agent') || '')
  const d = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw)))
  return [...d.slice(0, 8)].map(b => b.toString(16).padStart(2, '0')).join('')
}

function doodleTally(t) {
  return Object.fromEntries([...DOODLE_AXES, ...DOODLE_MARKS].map(a => [a, Array.isArray(t?.[a]) ? t[a] : [0, 0]]))
}

async function putDoodleVote(env, request, body) {
  const id = cap(body?.id, 170), v = Number(body?.v)
  if (!DOODLE_ID_RE.test(id)) return { error: 'bad doodle id', status: 400 }
  if (!Number.isInteger(v) || v < 1 || v > 9999) return { error: 'bad version', status: 400 }
  const votes = {}
  for (const a of DOODLE_AXES) {
    const x = body?.[a]
    if (x === 1 || x === -1 || x === 0) votes[a] = x
  }
  for (const a of DOODLE_MARKS) {
    const x = body?.[a]
    if (x === 1 || x === 0) votes[a] = x
  }
  if (!Object.keys(votes).length) return { error: 'no vote: send accuracy, aesthetics or like as 1, -1 or 0, or fav as 1 or 0', status: 400 }
  // a note: what is right and wrong with the picture; tools/doodle_score.py pays by its thoroughness
  const note = cap(body?.note ?? body?.why, 2000).replace(/[\u0000-\u0008\u000b-\u001f]/g, ' ')
  const payee = cap(body?.payee, 120)
  if (payee && !PAYEE_RE.test(payee)) return { error: 'bad payee', status: 400 }
  const key = `${id}@${v}`, voter = await voterId(request)
  const vk = `dvv:${key}:${voter}`
  const prev = (await env.KV.get(vk, 'json')) || { votes: {} }
  const t = doodleTally(await env.KV.get(`dvt:${key}`, 'json'))
  const at = new Date().toISOString(), changed = {}
  for (const [a, x] of Object.entries(votes)) {
    const old = prev.votes[a] || 0
    if (old !== x) {
      if (old) t[a][old > 0 ? 0 : 1] = Math.max(0, t[a][old > 0 ? 0 : 1] - 1)
      if (x) t[a][x > 0 ? 0 : 1] += 1
      prev.votes[a] = x
    }
    // the same vote again with a note is the note arriving: it is an event, not a new count
    if (old !== x || note) changed[a] = x
  }
  if (!Object.keys(changed).length) return { ok: true, id, v, mine: prev.votes, tally: t }
  prev.at = at
  await env.KV.put(vk, JSON.stringify(prev))
  await env.KV.put(`dvt:${key}`, JSON.stringify({ ...t, id, v, at }))
  await env.KV.put(`dve:${at}:${crypto.randomUUID().slice(0, 8)}`,
    JSON.stringify({ id, v, votes: changed, note, payee, voter, at }))
  return { ok: true, id, v, mine: prev.votes, tally: t }
}

// FEEDBACK — a thumb up, a thumb down and a paragraph, on any item the site shows (Nan, 2026-10-11:
// "You should be able to give feedback on any item on motdang (thumbs up, thumbs down, pgph input
// optional field)"). assets/feedback.js sends it. An item is a short id: place:<id>, shelf:<cat/sub>,
// site:<slug>, event:<key>, festival:<key>.
//   fbv:<item>:<who>      this browser's current vote {x, at}; a new vote replaces it, so a reader
//                         can change their mind. <who> is a random id the browser keeps itself.
//   fbt:<item>            the tally {up, down, at}
//   fb-vote:<iso>:<rand>  one event per change of vote
//   fb-note:<iso>:<rand>  a paragraph, with the vote it came with; private, read with the key only
// CREDITS (WO-110) — a name on /credits.html. A reader is named when the form sent
// credit: {consent: true, name} and the name passes this test; the Worker stamps the wording version
// the form carried. Anything else returns null and the record holds no credit. The name is public once
// a person accepts the report; the note, the contact address and the voter id are not part of it.
const CREDIT_V = '2026-10-11'
function cleanCredit(raw) {
  if (!raw || raw.consent !== true) return null
  const name = cap(raw.name, 60).replace(/\s+/g, ' ')
  if (name.length < 2 || /[\u0000-\u001f\u007f<>]/.test(name)) return null
  if (/@|:\/\/|www\./i.test(name) || /(?:\d[\s().+-]*){6,}/.test(name)) return null
  return { name, v: CREDIT_V }
}

const FB_ITEM_RE = /^[A-Za-z0-9:_\-./]{1,120}$/
const FB_WHO_RE = /^[A-Za-z0-9_-]{8,64}$/
const FB_PER_HOUR = 120
const FB_NOTES_PER_HOUR = 12

async function putFeedback(env, request, body) {
  const item = typeof body?.item === 'string' ? body.item : ''
  if (!FB_ITEM_RE.test(item)) return { error: 'bad item', status: 400 }
  const xs = body?.x
  if (xs !== undefined && xs !== 1 && xs !== -1 && xs !== 0) return { error: 'x is 1, -1 or 0', status: 400 }
  const note = cap(body?.note, 2000).replace(/[\u0000-\u0008\u000b-\u001f]/g, ' ')
  if (xs === undefined && !note) return { error: 'send x as 1, -1 or 0, or a note', status: 400 }
  const whoRaw = typeof body?.who === 'string' ? body.who : ''
  if (whoRaw && !FB_WHO_RE.test(whoRaw)) return { error: 'bad who', status: 400 }
  const who = whoRaw || await voterId(request)
  const vk = `fbv:${item}:${who}`, tk = `fbt:${item}`
  const prev = await env.KV.get(vk, 'json'), old = prev?.x || 0
  const x = xs === undefined ? old : xs
  const t = await env.KV.get(tk, 'json') || {}
  const tally = { up: Number(t.up) || 0, down: Number(t.down) || 0 }
  const at = new Date().toISOString()
  const page = cap(body?.page, 300), lang = body?.lang === 'th' ? 'th' : 'en'
  if (x !== old) {
    if (old) tally[old > 0 ? 'up' : 'down'] = Math.max(0, tally[old > 0 ? 'up' : 'down'] - 1)
    if (x) tally[x > 0 ? 'up' : 'down'] += 1
    await env.KV.put(vk, JSON.stringify({ x, at }))
    await env.KV.put(tk, JSON.stringify({ ...tally, at }))
    await env.KV.put(`fb-vote:${at}:${crypto.randomUUID().slice(0, 8)}`,
      JSON.stringify({ item, x, old, who, page, lang, at }))
  }
  const credit = note ? cleanCredit(body?.credit) : null
  const ref = crypto.randomUUID().slice(0, 8)
  if (note) await env.KV.put(`fb-note:${at}:${ref}`,
    JSON.stringify({ item, x, note, who, page, lang, at, ...(credit ? { credit, ref } : {}) }))
  return { ok: true, item, mine: x, tally, ...(credit ? { ref } : {}) }
}

async function feedbackEvents(env, since) {
  const out = []
  for (const prefix of ['fb-vote:', 'fb-note:']) {
    let cursor
    do {
      const pg = await env.KV.list({ prefix, cursor, limit: 1000 })
      const fresh = pg.keys.filter(k => k.name.slice(prefix.length) > since)
      const vals = await Promise.all(fresh.map(k => env.KV.get(k.name)))
      fresh.forEach((k, i) => { if (vals[i]) try { out.push({ k: k.name, ...JSON.parse(vals[i]) }) } catch {} })
      cursor = pg.list_complete ? null : pg.cursor
    } while (cursor)
  }
  out.sort((a, b) => String(a.at).localeCompare(String(b.at)))
  return out
}


// A pick: the better of two doodles (Nan, 2026-10-05: "I want the .0001 dollar one to be choosing
// the better of 2 images"). The pair comes from /doodles/data/pairs.json; a second pick of the same
// pair by the same voter replaces the first. dvp:<pair>:<voter> holds it; the event goes in dve: too.
async function putDoodlePick(env, request, body) {
  const side = (o) => ({ id: cap(o?.id, 170), v: Number(o?.v) })
  const a = side(body?.a), b = side(body?.b)
  for (const d of [a, b]) {
    if (!DOODLE_ID_RE.test(d.id)) return { error: 'bad doodle id', status: 400 }
    if (!Number.isInteger(d.v) || d.v < 1 || d.v > 9999) return { error: 'bad version', status: 400 }
  }
  if (a.id === b.id && a.v === b.v) return { error: 'a and b are the same doodle', status: 400 }
  if (!['a', 'b', 'same'].includes(body?.pick)) return { error: 'pick must be "a", "b" or "same"', status: 400 }
  const payee = cap(body?.payee, 120)
  if (payee && !PAYEE_RE.test(payee)) return { error: 'bad payee', status: 400 }
  const [x, y] = [`${a.id}@${a.v}`, `${b.id}@${b.v}`].sort()
  const voter = await voterId(request), at = new Date().toISOString()
  const won = body.pick === 'a' ? `${a.id}@${a.v}` : body.pick === 'b' ? `${b.id}@${b.v}` : ''   // '' is "can't tell"
  const prev = await env.KV.get(`dvp:${x}|${y}:${voter}`, 'json')
  if (prev && prev.won === won) return { ok: true, won }
  await env.KV.put(`dvp:${x}|${y}:${voter}`, JSON.stringify({ won, at }))
  await env.KV.put(`dve:${at}:${crypto.randomUUID().slice(0, 8)}`,
    JSON.stringify({ kind: 'pick', pair: [x, y], won, side: body.pick, payee, voter, at }))
  return { ok: true, won }
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
const ID_MARKER_RE = new RegExp(`\\[id:((?:${PROVINCE_KEYS})-[a-z0-9-]+)\\]`)
// Tells a toilet report apart from a claim; both carry the same id marker.
const TOILET_INTENT_RE = /(ห้องน้ำ|สุขา|ส้วม|toilet|restroom|\bloo\b|\bwc\b)/i

const cap = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '') || ''

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type',
}
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json', ...CORS } })

// For the one page here that shows what a stranger typed (the owner's own
// claim, back to the owner). Every value passes through this first.
const escHtml = (s) => String(s ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
const wantsHtml = (request) => (request.headers.get('accept') || '').includes('text/html')

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

/* A picture someone sent the OA, filed against the listing they are bound to.
 *
 * WHY THIS IS THE SAFE DOOR. There is no upload endpoint here — no URL a
 * stranger can POST a file to. A photo can only arrive from a LINE account
 * that has already sent us its listing's code, it lands in a bucket nothing
 * serves, and it stays there until Nan taps Publish. So the worst case is
 * that one identifiable account makes one held submission unpleasant, and the
 * public never sees it. Held submissions have their photos deleted with them.
 */
async function takePhoto(env, userId, messageId) {
  const subId = await env.KV.get(`lstlineuser:${userId}`)
  if (!subId) return { error: 'unbound' }
  const sub = await env.KV.get(`lst:${subId}`, 'json')
  if (!sub) return { error: 'gone' }

  const countKey = `lstphotos:${subId}`
  const n = Number((await env.KV.get(countKey)) || 0)
  if (n >= PHOTO_MAX) return { error: 'full', n }

  const r = await fetch(`https://api-data.line.me/v2/bot/message/${encodeURIComponent(messageId)}/content`,
    { headers: { authorization: `Bearer ${env.LINE_CHANNEL_TOKEN}` } })
  if (!r.ok) return { error: 'fetch', status: r.status }

  const type = (r.headers.get('content-type') || '').split(';')[0].trim().toLowerCase()
  if (!PHOTO_TYPES.has(type)) return { error: 'type', type }
  const buf = await r.arrayBuffer()
  if (buf.byteLength > PHOTO_MAX_BYTES) return { error: 'big', bytes: buf.byteLength }

  // The name is what ends up in the listing's `photos` list, so it is derived
  // from the message id — stable, unguessable, and it cannot collide.
  const ext = type === 'image/png' ? 'png' : type === 'image/webp' ? 'webp'
    : (type === 'image/heic' || type === 'image/heif') ? 'heic' : 'jpg'
  const name = `line-${messageId}.${ext}`
  await env.PHOTOS.put(`inbox/${subId}/${name}`, buf, {
    httpMetadata: { contentType: type },
    customMetadata: { submission: subId, lineUser: userId, at: new Date().toISOString() },
  })
  await env.KV.put(countKey, String(n + 1))
  return { ok: true, n: n + 1, name }
}

/* Push — a message the account starts, to a user who has messaged it before.
 * Used for exactly one thing: telling a lister their price is about to lapse
 * (listing-sheet/notify.py → POST /notify). The channel token lives here and
 * nowhere else, which is why the sheet asks the Worker rather than LINE. */
async function linePush(env, userId, text) {
  const r = await fetch('https://api.line.me/v2/bot/message/push', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${env.LINE_CHANNEL_TOKEN}` },
    body: JSON.stringify({ to: userId, messages: [{ type: 'text', text }] }),
  })
  return r.ok
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

// One number, one fact, then done — the whole exchange is two messages. A
// passer-by with a phone in one hand does not get an interview.
async function handleToilet(env, userId, session, text, replyToken) {
  const n = parseInt((text.match(/\d+/) || [])[0], 10)
  const key = TOILET_KEYS[n - 1]
  if (!key) {
    await lineReply(env, replyToken,
      "ขอเป็นตัวเลข ๑–๕ นะคะ / A number from 1 to 5, please\n\n"
      + TOILET_KEYS.map((k, i) => `${i + 1}. ${TOILET_LABEL[k]}`).join('\n'))
    return
  }
  const res = await putToiletReport(env, session.placeId, key, 'line')
  await clearSession(env, userId)
  if (res.error) {
    await lineReply(env, replyToken, "บันทึกไม่สำเร็จค่ะ ลองใหม่อีกครั้ง / Could not save that — please try again.")
    return
  }
  await lineReply(env, replyToken,
    `บันทึกแล้วเจ้า ขอบคุณมาก 🐜 — ${TOILET_LABEL[key]}\n`
    + "Saved, thank you. It will show on motdang.net at the next build.\n\n"
    + "เจอที่อื่นอีก ส่งมาได้เรื่อย ๆ นะคะ / Found another? Keep them coming.")
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

  // A picture, from someone who has bound this chat to a listing with its
  // code. Anyone else is told what to send first — the code is the whole
  // permission, and without it a photo has no listing to belong to.
  if (ev.message.type === 'image') {
    const r = await takePhoto(env, userId, ev.message.id)
    if (!replyToken) return
    const say = {
      unbound: 'ส่งรหัสประกาศก่อนนะคะ เช่น #a1b2c3d4 (อยู่ในหน้าหลังกดส่งประกาศ)\n'
        + 'Send your listing code first — like #a1b2c3d4, shown after you sent the listing.',
      gone: 'ไม่พบประกาศนั้นแล้วค่ะ / That listing is no longer in the queue.',
      full: `รับรูปได้สูงสุด ${PHOTO_MAX} รูปต่อประกาศค่ะ / ${PHOTO_MAX} photos per listing is the limit.`,
      type: 'ไฟล์นี้ไม่ใช่รูปภาพค่ะ / That is not an image file.',
      big: 'รูปใหญ่เกิน 5 MB ค่ะ ลองส่งขนาดปกติ / Over 5 MB — send it at normal size.',
      fetch: 'โหลดรูปไม่สำเร็จ ลองส่งใหม่อีกครั้ง / Could not fetch that one — send it again.',
    }
    await lineReply(env, replyToken, r.ok
      ? `ได้รับรูปแล้ว ${r.n} รูป 🐜 แนบกับประกาศให้แล้ว จะขึ้นพร้อมประกาศ\n`
        + `Got it — ${r.n} photo(s) on this listing. They go up with it.`
      : (say[r.error] || 'ลองใหม่อีกครั้งนะคะ / Please try again.'))
    return
  }

  if (ev.message.type !== 'text') {
    if (replyToken) await lineReply(env, replyToken,
      "ตอนนี้บอทอ่านข้อความและรูปค่ะ ส่งอย่างอื่นยังไม่ได้ แต่พิมพ์บอกได้เลย มีคนอ่านแชทนี้ด้วย\n"
      + "The bot reads text and photos — anything else, just type it; a person also checks this chat.")
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
  //
  // The toilet door is checked FIRST, because both arrive carrying the same
  // [id:...] marker and only the leading word tells them apart. Without this
  // branch someone who tapped "tell the ants about the toilet" would be asked
  // for their opening hours and their Facebook page — the claim interview,
  // aimed at an owner, run at a stranger who wanted to answer one question.
  // "#a1b2c3d4" — the code the Listing Sheet shows after Send. Sending it
  // here ties this LINE user to that submission, so the lapse warning can
  // reach them on LINE as well as by email. Nothing else is stored.
  const tag = text.match(/^#([0-9a-f]{8})$/i)
  if (tag) {
    const code = tag[1].toLowerCase()
    // Both directions: the code finds the user (for a lapse push), and the
    // user finds the submission (for a photo they send next). Without the
    // reverse we would have to scan every binding on every picture.
    const match = await env.KV.list({ prefix: 'lst:' })
    const subId = (match.keys.find(k => k.name.slice(4).startsWith(code)) || {}).name?.slice(4)
    if (subId) await env.KV.put(`lstlineuser:${userId}`, subId)
    await env.KV.put(`lstline:${code}`, userId)
    await lineReply(env, replyToken, subId
      ? ('รับทราบค่ะ 🐜 จะแจ้งทางไลน์นี้เมื่อประกาศใกล้หมดอายุ\n'
         + 'ส่งรูปมาที่แชทนี้ได้เลย แนบกับประกาศให้อัตโนมัติ\n\n'
         + 'Noted — we will message here before your price lapses.\n'
         + 'Send photos to this chat and they attach to that listing.')
      : ('ไม่พบรหัสนี้ค่ะ ตรวจรหัสจากหน้าลงประกาศอีกครั้ง\n'
         + 'We do not have that code — check it on the page where you sent the listing.'))
    return
  }

  const marker = text.match(ID_MARKER_RE)
  if (marker && PLACE_ID_RE.test(marker[1]) && TOILET_INTENT_RE.test(text)) {
    await putSession(env, userId, { step: 'toilet', placeId: marker[1] })
    await lineReply(env, replyToken,
      "ขอบคุณเจ้า 🐜 ที่นี่เป็นยังไงคะ? ตอบเป็นตัวเลขได้เลย\n"
      + "Thank you! What is it like there? Just send the number.\n\n"
      + TOILET_KEYS.map((k, i) => `${i + 1}. ${TOILET_LABEL[k]}`).join('\n')
      + "\n\n(พิมพ์ ยกเลิก เพื่อออก / send \"cancel\" to stop)")
    return
  }
  if (marker && PLACE_ID_RE.test(marker[1])) {
    await startCollecting(env, userId, marker[1], replyToken)
    return
  }

  const session = await getSession(env, userId)
  if (session) {
    if (session.step === 'toilet') { await handleToilet(env, userId, session, text, replyToken); return }
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

// ---------------------------------------------------------------------------
// THE LISTING SHEET'S FRONT DOOR
//
// motdang.net/listings/add.html is the Listing Sheet's entry form. Until now
// it ended at "Download CSV" and a shell command, which is a developer's
// console instruction shown to an estate agent: everyone who filled the form
// in reached a dead end, and nothing they typed ever arrived.
//
// This is the arrival. One POST, one email, one tap.
//
//   POST /listing            the form sends its batch here. Rate-limited,
//                            size-capped, the required six validated at the
//                            edge so a submitter is told immediately rather
//                            than silently held.
//   GET  /listing/ok/:token  the operator's one-tap publish
//   GET  /listing/no/:token  the operator's one-tap hold
//   GET  /listings-inbox     403, deliberately — see /suggestions below.
//
// WHY THE WORKER DOES NOT KNOW THE SCHEMA. The sheet's listing schema is 56
// fields wide and lives in listing-sheet/{intake,facets}.py, which already
// reports unknown words rather than guessing at them. Teaching it to this
// worker too would create a second copy to drift, and a key the worker does
// not recognise is silently dropped with the contributor never told — the
// exact failure the facet list's comment warns about. So this validates the
// SIX that make a listing a listing, caps everything else, and passes the
// rest through untouched for intake.py to read.
//
// WHY A HUMAN STILL TAPS. Nothing here publishes itself. A submission is a
// stranger's dated price with a named seller and a reachable contact, and the
// sheet already holds a row proving why that needs a look: it arrived
// unsolicited from a private individual's gmail, and publishing it would have
// put their personal address on a live page. So the operator gets an email
// with two links and the rest of the chain is machinery. One tap is the whole
// of the human part, and it is the tap that stops that.
const LISTING_PER_HOUR = 6
const LISTING_MAX_BODY = 250_000     // a 25-row batch with every field filled
const LISTING_MAX_ROWS = 25
// The form has 66 columns today. This is headroom, not a truncation point:
// a row over the cap is REFUSED rather than quietly trimmed, because a field
// silently dropped is the one failure nobody finds out about.
const LISTING_MAX_KEYS = 200
const LISTING_KINDS = new Set(['house', 'condo', 'apartment', 'townhouse',
  'land', 'room', 'commercial', 'compound'])
const LISTING_OFFERS = new Set(['sale', 'rent'])
// Long enough that a link mailed on a Friday still works after a holiday.
const LISTING_TOKEN_TTL = 90 * 24 * 3600

// Photos, per submission. Twelve is more than any listing needs and few
// enough that the bucket cannot become someone's file host; 5 MB is a phone
// photo with room to spare. Both are refused politely, in the chat, rather
// than silently dropped.
const PHOTO_MAX = 12
const PHOTO_MAX_BYTES = 5 * 1024 * 1024
const PHOTO_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'])

const LISTING_TO = '530kings@proton.me'
const LISTING_FROM = 'listings@motdang.net'

/* A submitted row, cleaned. Keys are lowercased and must look like column
 * names; values become strings. Nothing is interpreted here — see above. */
function cleanRow(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  const out = {}
  if (Object.keys(raw).length > LISTING_MAX_KEYS) return null
  for (const [k, v] of Object.entries(raw)) {
    const key = String(k).toLowerCase().trim()
    if (!/^[a-z][a-z0-9_]{0,39}$/.test(key)) continue
    if (v === null || v === undefined || v === '') continue
    const val = Array.isArray(v) ? v.map(x => String(x)).join(', ') : String(v)
    const s = val.trim().slice(0, 600)
    if (s) out[key] = s
  }
  return out
}

/* The six that make a listing a listing. Returns a complaint or null.
 * Deliberately the same six intake.py calls REQUIRED — a submitter who gets
 * past this has given a page that can stand on its own. */
function listingFault(r, i) {
  const where = `row ${i + 1}`
  for (const k of ['name', 'kind', 'offer', 'price', 'agency', 'contact'])
    if (!r[k]) return `${where}: ${k} is required`
  if (!LISTING_KINDS.has(r.kind.toLowerCase()))
    return `${where}: kind must be one of ${[...LISTING_KINDS].join(', ')}`
  if (!LISTING_OFFERS.has(r.offer.toLowerCase()))
    return `${where}: offer must be sale or rent`
  // "4.2M", "4,200,000" and "4200000" all mean the same thing to intake.py,
  // so this only asks that a digit is in there somewhere and the number is
  // not nonsense. Parsing properly is intake.py's job, in one place.
  const digits = r.price.replace(/[^0-9]/g, '')
  if (!digits || Number(digits) <= 0) return `${where}: price needs a number`
  return null
}

/* A CSV reader that is small on purpose. It exists to COUNT rows and read
 * the header, so the email can say "41 rows from Northern Homes" and the
 * form can be told at once that a required column is missing. It does not
 * interpret a single value — that is intake.py's job, in one place, with the
 * forgiving vocabulary (บ้าน/house, 4.2M/4,200,000) the Worker deliberately
 * does not carry. Quotes, embedded commas and embedded newlines are handled
 * because Excel and Google Sheets emit all three. */
function csvRows(text) {
  const rows = []; let row = [], cell = '', q = false
  const t = text.replace(/^﻿/, '')
  for (let i = 0; i < t.length; i++) {
    const c = t[i]
    if (q) {
      if (c === '"') { if (t[i + 1] === '"') { cell += '"'; i++ } else q = false }
      else cell += c
    } else if (c === '"') q = true
    else if (c === ',' || c === '\t') { row.push(cell); cell = '' }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && t[i + 1] === '\n') i++
      row.push(cell); rows.push(row); row = []; cell = ''
    } else cell += c
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row) }
  return rows.filter(r => r.some(x => x.trim() !== ''))
}
// The same fold intake.norm() applies to a header: NFC, trim, lowercase.
const foldHead = (s) => String(s || '').normalize('NFC').trim().toLowerCase()
const CSV_REQUIRED = ['name', 'kind', 'offer', 'price', 'agency', 'contact']
const CSV_MAX_BYTES = 2_000_000
const LISTING_COLUMNS = new Set(["name", "kind", "offer", "price", "agency", "contact", "photos", "terms", "pets", "unit", "province", "tambon", "amphoe", "address", "lat", "lng", "building_ref", "as_of", "status", "closed_on", "until", "source", "agency_ref", "bedrooms", "bathrooms", "interior_sqm", "land_wah", "land_sqm", "floors", "floor_level", "furnished", "use", "term", "ac_units", "water_heaters", "parking_spaces", "year_built", "owned_since", "min_months", "deposit_months", "hoa_thb_month", "hoa_thb_sqm_month", "electric_thb_unit", "water_thb_unit", "electric_meter", "water_source", "tenure", "title_grade", "road_access", "road_frontage_m", "tabien_baan", "zoning", "flood", "flood_since", "permitted", "faces", "services", "juristic", "juristic_name", "juristic_contact", "debt_free", "sinking_fund_thb", "foreign_quota", "short_lets", "rate_1w", "rate_2w", "rate_1m", "rate_3m", "rate_6m", "rate_1y", "rate_2y"])

/* RFC 2047 for a subject line that may be in Thai. */
function mimeWord(s) {
  // eslint-disable-next-line no-control-regex
  if (/^[\x20-\x7E]*$/.test(s)) return s
  const b = btoa(String.fromCharCode(...new TextEncoder().encode(s)))
  return `=?UTF-8?B?${b}?=`
}

function b64(s) {
  return btoa(String.fromCharCode(...new TextEncoder().encode(s)))
    .replace(/(.{76})/g, '$1\r\n')
}

/* A mail that did not go. The record it announced is already in KV, so the
 * send is best-effort at every site — but best-effort was also silent: a
 * console.log and a mailed:false in a reply nothing reads. This leaves a
 * dated key instead, which GET /health counts, so the nightly pull can see
 * that mail has been failing and read the queue itself. 30 days, then gone.
 *   mailfail:<YYYY-MM-DD>:<id> → {route, id, error, at} */
const MAILFAIL_TTL = 30 * 24 * 3600
async function mailFailed(env, route, id, err) {
  const at = new Date().toISOString()
  console.log(`${route} mail failed`, String(err))
  try {
    await env.KV.put(`mailfail:${at.slice(0, 10)}:${id}`,
      JSON.stringify({ route, id, error: String(err).slice(0, 300), at }),
      { expirationTtl: MAILFAIL_TTL })
  } catch (e) { console.log('mailfail record failed', String(e)) } // never fail the reply over the log
}

/* What the operator reads on her phone. Plain text on purpose: it has to be
 * legible in a notification preview, and the only thing she has to do with it
 * is tap one of two links. */
function listingEmail(sub, origin) {
  const L = []
  if (sub.kind === 'csv') {
    L.push(`A spreadsheet sent through motdang.net/listings/add.html: ${sub.file || 'listings.csv'}`)
    L.push(`${sub.rowsN} row(s) · agency in the first row: ${sub.agency || '(blank)'}`)
    L.push(`Columns it uses: ${sub.columns.known.join(', ')}`)
    if (sub.columns.unknown.length)
      L.push(`Columns intake.py will ignore, with a note: ${sub.columns.unknown.join(', ')}`)
    L.push(`Sent by: ${sub.from || 'no reply address given'}`)
    L.push(sub.lister ? `Listing agent: ${sub.lister.office} (member ${sub.lister.member})` : 'Listing agent: not signed in')
    L.push(sub.attest
      ? 'They ticked: authorised to publish these listings and the contacts in them.'
      : 'THEY DID NOT tick the authorisation box.')
    L.push('')
    L.push('PUBLISH — the nightly pull runs intake.py over the file and rebuilds:')
    L.push(`  ${origin}/listing/ok/${sub.okToken}`)
    L.push('')
    L.push('HOLD — keep it back; nothing is deleted, it waits:')
    L.push(`  ${origin}/listing/no/${sub.noToken}`)
    L.push('')
    L.push(`Reference ${sub.id}`)
    return L.join('\r\n')
  }
  L.push(`${sub.rows.length} listing(s) sent through motdang.net/listings/add.html`)
  L.push(`Sent by: ${sub.from || 'no reply address given'}`)
  L.push(sub.lister ? `Listing agent: ${sub.lister.office} (member ${sub.lister.member})` : 'Listing agent: not signed in')
  L.push(sub.attest
    ? 'They ticked: authorised to publish this listing and this contact.'
    : 'THEY DID NOT tick the authorisation box.')
  L.push('')
  for (const r of sub.rows) {
    L.push(`  ${r.name}`)
    L.push(`    ${r.offer} · ${r.kind} · ${r.price} baht`)
    L.push(`    ${r.agency} — ${r.contact}`)
    const extra = Object.keys(r).filter(k =>
      !['name', 'kind', 'offer', 'price', 'agency', 'contact'].includes(k))
    if (extra.length) L.push(`    also filled: ${extra.join(', ')}`)
    L.push('')
  }
  L.push('PUBLISH — the nightly pull writes it to the sheet and rebuilds:')
  L.push(`  ${origin}/listing/ok/${sub.okToken}`)
  L.push('')
  L.push('HOLD — keep it back; nothing is deleted, it waits:')
  L.push(`  ${origin}/listing/no/${sub.noToken}`)
  L.push('')
  L.push(`Reference ${sub.id}`)
  return L.join('\r\n')
}

/* A decision page, for the browser the tap lands in. */
function listingPage(title, line) {
  return new Response(`<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title} — The Listing Sheet</title>
<style>body{margin:0;background:#faf8f4;color:#1a1a19;display:grid;
place-items:center;min-height:100vh;font:16px/1.6 -apple-system,
BlinkMacSystemFont,"Segoe UI",sans-serif;padding:1.5rem}
div{max-width:26rem}h1{font-size:1.4rem;margin:0 0 .4rem}
p{color:#57574f;margin:0}a{color:#a33d21}</style>
<div><h1>${title}</h1><p>${line}</p></div>`,
    { headers: { 'content-type': 'text/html; charset=utf-8', ...CORS } })
}

/* The owner's edit link, opened in a browser. listingPage() above is a
 * one-line decision page for the Listing Sheet and cannot carry a form, so
 * this is its own page: the claim's fields, a Save that POSTs the same JSON
 * the API takes to the same URL, and nothing fetched from anywhere else.
 * The URL is the capability, so the page is never cached and sends no
 * referrer. A null claim renders the not-valid line, status 404. */
const EDIT_LABELS = {
  phone: 'โทร · Phone', lineId: 'LINE ID', facebook: 'Facebook', instagram: 'Instagram',
  whatsapp: 'WhatsApp', email: 'อีเมล · Email', website: 'เว็บไซต์ · Website',
  hours: 'เวลาเปิด-ปิด · Hours', menu: 'เมนู · Menu', note: 'หมายเหตุ · Note',
}
function claimEditPage(placeId, claim) {
  const nonce = crypto.randomUUID()
  const rows = claim ? FIELDS.map(([k, max]) => {
    const v = escHtml(claim[k] || '')
    const box = (k === 'menu' || k === 'note')
      ? `<textarea name="${k}" maxlength="${max}" rows="4">${v}</textarea>`
      : `<input name="${k}" type="text" maxlength="${max}" autocomplete="off" value="${v}">`
    return `<label>${EDIT_LABELS[k]}<br>${box}</label>`
  }).join('\n') : ''
  const body = claim
    ? `<p class="id">${escHtml(placeId)}</p>
<form id="f" method="post">
${rows}
<button type="submit">บันทึก · Save</button>
</form>
<p id="say" role="status" aria-live="polite"></p>
<script nonce="${nonce}">
var f = document.getElementById('f'), say = document.getElementById('say')
f.addEventListener('submit', function (e) {
  e.preventDefault()
  var body = {}
  for (var i = 0; i < f.elements.length; i++) {
    var el = f.elements[i]
    if (el.name) body[el.name] = el.value.trim()
  }
  say.textContent = 'กำลังบันทึก · Saving'
  fetch(location.pathname, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
    .then(function (r) { return r.json() })
    .then(function (j) { say.textContent = j.ok ? 'บันทึกแล้ว · Saved' : 'บันทึกไม่สำเร็จ · Not saved' + (j.error ? ' — ' + j.error : '') })
    .catch(function () { say.textContent = 'บันทึกไม่สำเร็จ · Not saved' })
})
</script>`
    : '<p>ลิงก์นี้ใช้ไม่ได้ · This link is not valid</p>'
  return new Response(`<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>แก้ไขข้อมูลร้าน · Edit your listing</title>
<style>body{margin:0;background:#faf8f4;color:#1a1a19;padding:1.5rem;
font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:30rem;margin:0 auto}h1{font-size:1.4rem;margin:0 0 .3rem}
.id{color:#57574f;margin:0 0 1rem;font-family:ui-monospace,monospace}
label{display:block;margin:0 0 .9rem;color:#57574f}
input,textarea{display:block;width:100%;box-sizing:border-box;min-height:48px;
margin-top:.2rem;padding:.6rem .7rem;font:inherit;color:#1a1a19;background:#fff;
border:1px solid #c9c5bc;border-radius:6px}textarea{min-height:6rem}
button{min-height:48px;min-width:8rem;padding:0 1.2rem;font:inherit;font-weight:600;
color:#fff;background:#a33d21;border:0;border-radius:6px}
#say{margin:.8rem 0 0;min-height:1.5rem}</style>
<main><h1>แก้ไขข้อมูลร้าน · Edit your listing</h1>
${body}
</main>`, {
    status: claim ? 200 : 404,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'no-store',
      'referrer-policy': 'no-referrer',
      'content-security-policy': `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src 'self'; form-action 'none'`,
    },
  })
}

/* ===================== ALPHA — DELETE THIS BLOCK AT BETA =====================
 * Nan, 2026-09-09: a thumbs up / thumbs down for the alpha testers, with a
 * screenshot and a box to say what went wrong — "I want this to go away
 * completely for beta." So the whole of it is between these two markers and
 * one route block below, and beta is deleting both.
 *
 * KV:  alpha:<id> → the report, 180-day TTL
 * R2:  alpha/<id>/<n>.<ext> in the PHOTOS bucket — private, same bucket the
 *      listing photos use, and nothing serves it.
 * Mail: one message per report to the verified destination, with the pictures
 *      attached when they are small enough to attach. The mail is the
 *      notification; KV is the record, so a mail failure loses nothing.
 */
const ALPHA_PER_HOUR = 60
const ALPHA_TTL = 180 * 24 * 3600
const ALPHA_MAX_SHOTS = 3
const ALPHA_MAX_BYTES = 6 * 1024 * 1024
const ALPHA_MAIL_BYTES = 2_500_000        // above this the mail names the key instead
const ALPHA_TO = '530kings@proton.me'
const ALPHA_FROM = 'listings@motdang.net' // the one verified sender on this account

function b64bytes(buf) {
  const b = new Uint8Array(buf)
  let s = ''
  for (let i = 0; i < b.length; i += 8192)
    s += String.fromCharCode.apply(null, b.subarray(i, i + 8192))
  return btoa(s).replace(/(.{76})/g, '$1\r\n')
}

/* Plain text, and ordered so the first three lines answer "who, where, what"
 * in a phone notification without opening anything. */
function alphaEmail(rec, shots) {
  const c = rec.ctx || {}
  const L = []
  L.push(`${rec.v === 'up' ? 'WORKED' : 'WENT WRONG'} — ${rec.who || 'unnamed tester'}`)
  L.push(c.url || '')
  if (c.q) L.push(`searched: ${c.q}`)
  L.push('')
  if (rec.note) { L.push(rec.note); L.push('') }
  if (c.counts) {
    const k = Object.entries(c.counts).filter(([, v]) => v !== undefined)
      .map(([a, b]) => `${a} ${b}`).join(' · ')
    if (k) L.push(`on the page: ${k}`)
  }
  if (c.map) L.push('map: ' + c.map.map(m => m.live
    ? `${m.lat},${m.lng} z${m.z}` : `no tiles (drawn: ${m.drawn})`).join(' | '))
  if (c.h1) L.push(`heading: ${c.h1}`)
  L.push('')
  if (c.errs && c.errs.length) {
    L.push(`JS errors (${c.errs.length}):`)
    for (const e of c.errs) L.push(`  ${e.at}ms  ${e.m}  ${e.f || ''}`)
  }
  if (c.nets && c.nets.length) {
    L.push(`requests that did not come back (${c.nets.length}):`)
    for (const n of c.nets) L.push(`  ${n.s}  ${n.u}  ${n.ms}ms`)
  }
  if (c.trail && c.trail.length) {
    L.push('last taps:')
    for (const t of c.trail) L.push(`  ${t.at}ms  ${t.t} ${t.x || ''} ${t.h || ''} ${t.d || ''}`.trimEnd())
  }
  L.push('')
  L.push(`build ${rec.build || '?'} · ${c.view || ''} · ${c.lang || ''} · ${c.net || 'connection unknown'}`
    + ` · service worker ${c.sw ? 'on' : 'off'} · ${c.ms}ms into the visit`)
  if (c.ua) L.push(c.ua)
  if (c.ref) L.push(`came from ${c.ref}`)
  L.push('')
  L.push(shots.length ? `pictures: ${shots.map(s => s.key).join(', ')}` : 'no picture')
  L.push(`report ${rec.id}`)
  return L.join('\r\n')
}

/* TRUSTED SENDERS (Nan, 2026-09-27: "approve from clarence, and all future
 * listings from clarence"). KV `lsttrust:<email>` = {"by", "at", "who"}; a
 * submission whose sender address is on it is approved on arrival, the same
 * state her publish tap sets, and the next pull publishes it. The address is
 * the one the form sends; LISTER_REQUIRED still asks the sender to be a
 * signed-in agent first. */
async function trustedSender(env, sub) {
  const from = String(sub.from || '').trim().toLowerCase()
  if (!from) return false
  const rec = await env.KV.get(`lsttrust:${from}`, 'json')
  if (!rec) return false
  sub.status = 'approved'
  sub.decidedAt = new Date().toISOString()
  sub.approvedBy = `trusted sender (${rec.by || 'Nan'}, ${rec.at || ''})`
  return true
}


/* The nightly cron ([triggers] in wrangler.toml) runs this. KV forgets an
 * alpha record after ALPHA_TTL on its own; R2 forgets nothing, so the
 * screenshots under alpha/<id>/ would outlive the reports that named them.
 * Walks the whole prefix first and deletes after, so the cursor never runs
 * over a listing that is being shortened under it; a thousand keys per
 * delete is R2's cap. */
async function alphaSweep(env) {
  const cutoff = Date.now() - ALPHA_TTL * 1000
  const old = []
  let cursor, seen = 0
  do {
    const page = await env.PHOTOS.list({ prefix: 'alpha/', cursor })
    seen += page.objects.length
    for (const o of page.objects) if (new Date(o.uploaded).getTime() < cutoff) old.push(o.key)
    cursor = page.truncated ? page.cursor : null
  } while (cursor)
  for (let i = 0; i < old.length; i += 1000) await env.PHOTOS.delete(old.slice(i, i + 1000))
  console.log(`alpha sweep: ${seen} seen, ${old.length} deleted`)
  return { seen, gone: old.length }
}
/* =================== end ALPHA — DELETE THIS BLOCK AT BETA =================== */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url)
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS })

    // GET /health — public, no key, counts only: whether mail has been
    // failing (see mailFailed). The nightly pull_inbox.sh curls it; a count
    // above zero is its cue to read the queue with wrangler rather than wait
    // for a message that did not come. Keys sort by date, so the first one
    // listed is the oldest.
    if (url.pathname === '/health' && request.method === 'GET') {
      const page = await env.KV.list({ prefix: 'mailfail:', limit: 1000 })
      const keys = page.keys.map(k => k.name)
      return new Response(JSON.stringify({
        ok: true,
        mailfail: { count: keys.length, oldest: keys.length ? keys[0].split(':')[1] : null },
      }), { headers: { 'content-type': 'application/json', 'cache-control': 'no-store', ...CORS } })
    }

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

    // POST /toilet — a passer-by's answer to one question, at one place. No
    // token, no claim, nothing locked; see putToiletReport for why this is a
    // separate door from /claim rather than a facet on one.
    if (url.pathname === '/toilet' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rlt:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= TOILET_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)

      const text = await request.text()
      if (text.length > MAX_BODY) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }

      const result = await putToiletReport(env, cap(body?.placeId, 60),
        cap(body?.report, 20), 'web')
      if (result.error) return json({ error: result.error }, result.status)
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json(result)
    }

    // POST /rain · POST /flood — Nan 2026-09-28: "an 'is it raining now'
    // button to feed the weather machine, a 'how deep is your flooding'
    // question for emergencies". One answer and one point per tap. The
    // point is the reader's own (MDLOC) when they gave one, else the edge's
    // city-grade guess, and says which. GET returns what is still live, for
    // the site and for weather-north's hourly archive.
    if (Object.hasOwn(OBS_ANSWERS, url.pathname.slice(1)) && request.method === 'POST') {
      const kind = url.pathname.slice(1)
      // motdang-line forwards every LINE reader from one address; with the
      // shared relay secret it names the reader (a hash), and the limit is per
      // reader instead of per address.
      const relayed = env.RELAY_SECRET && request.headers.get('x-md-relay') === env.RELAY_SECRET
      const who = relayed ? 'line:' + String(request.headers.get('x-md-user') || '').replace(/[^0-9a-f]/g, '').slice(0, 32)
        : (request.headers.get('cf-connecting-ip') || 'unknown')
      const bucket = `rl${kind}:${who}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= OBS_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)
      const text = await request.text()
      if (text.length > 400) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      const answer = String(body?.answer || '')
      if (!OBS_ANSWERS[kind].includes(answer)) return json({ error: 'unknown answer' }, 400)
      let lat = Number(body?.lat), lng = Number(body?.lng), from = 'reader'
      if (!isFinite(lat) || !isFinite(lng) || body?.lat == null) {
        lat = Number(request.cf?.latitude); lng = Number(request.cf?.longitude); from = 'edge'
      }
      if (!isFinite(lat) || !isFinite(lng) || lat < NORTH.south || lat > NORTH.north
          || lng < NORTH.west || lng > NORTH.east)
        return json({ error: 'outside northern Thailand' }, 400)
      // Rain to ~1 km, flood to ~200 m: a flood report is only worth anything
      // if a boat can find the street.
      const q = kind === 'flood' ? 500 : 100
      const rec = { kind, answer, lat: Math.round(lat * q) / q, lng: Math.round(lng * q) / q,
        from, via: relayed ? 'line' : 'web', at: new Date().toISOString() }
      const key = `obs:${kind}:${rec.at}:${crypto.randomUUID().slice(0, 8)}`
      await env.KV.put(key, JSON.stringify(rec), { expirationTtl: OBS_TTL[kind] })
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json({ ok: true, ...rec })
    }
    if (Object.hasOwn(OBS_ANSWERS, url.pathname.slice(1)) && request.method === 'GET') {
      const kind = url.pathname.slice(1)
      const hours = Math.min(Math.max(Number(url.searchParams.get('hours')) || 6, 1), 24 * 30)
      const since = new Date(Date.now() - hours * 3600_000).toISOString()
      const out = []
      let cursor
      do {
        const page = await env.KV.list({ prefix: `obs:${kind}:`, cursor, limit: 1000 })
        const fresh = page.keys.filter(k => k.name.split(':').slice(2, -1).join(':') >= since)
        const vals = await Promise.all(fresh.map(k => env.KV.get(k.name)))
        for (const v of vals) if (v) try { out.push(JSON.parse(v)) } catch {}
        cursor = page.list_complete ? null : page.cursor
      } while (cursor)
      return new Response(JSON.stringify({ ok: true, kind, hours, count: out.length, reports: out }),
        { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=60', ...CORS } })
    }

    // POST /feedback — {item, x?: 1|-1|0, note?: string<=2000, page?, lang?, who?}. A vote replaces
    // this browser's (who's) earlier vote on the item. Returns {ok, item, mine, tally: {up, down}}.
    // GET /feedback-tally?item=<id> — {ok, item, up, down}, cached a minute.
    // GET /feedback-events?since=<iso> — every vote change and note; only with the FEEDBACK_KEY
    // secret in x-md-key (importers/sync_feedback.py). Notes have no public GET: they can carry
    // contact details.
    if (url.pathname === '/feedback' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const hour = Math.floor(Date.now() / 3600_000)
      const bucket = `rlfb:${ip}:${hour}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= FB_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)
      const text = await request.text()
      if (text.length > 6000) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      let nbucket = null, ncount = 0
      if (cap(body?.note, 2000)) {
        nbucket = `rlfn:${ip}:${hour}`
        ncount = Number((await env.KV.get(nbucket)) || 0)
        if (ncount >= FB_NOTES_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)
      }
      const result = await putFeedback(env, request, body)
      if (result.error) return json({ error: result.error }, result.status)
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      if (nbucket) await env.KV.put(nbucket, String(ncount + 1), { expirationTtl: 3600 })
      return json(result)
    }
    if (url.pathname === '/feedback-tally' && request.method === 'GET') {
      const item = url.searchParams.get('item') || ''
      if (!FB_ITEM_RE.test(item)) return json({ error: 'bad item' }, 400)
      const ck = new Request('https://cache.mot-dang/feedback-tally/' + encodeURIComponent(item))
      const cached = typeof caches !== 'undefined' ? caches.default : null
      const hit = cached ? await cached.match(ck) : null
      if (hit) return hit
      const t = await env.KV.get(`fbt:${item}`, 'json') || {}
      const res = new Response(JSON.stringify({ ok: true, item, up: Number(t.up) || 0, down: Number(t.down) || 0 }),
        { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=60', ...CORS } })
      if (cached && ctx?.waitUntil) ctx.waitUntil(cached.put(ck, res.clone()))
      return res
    }
    if (url.pathname === '/feedback-events' && request.method === 'GET') {
      const want = env.FEEDBACK_KEY, got = request.headers.get('x-md-key') || ''
      if (!want || got.length !== want.length || got !== want) return json({ error: 'not found' }, 404)
      const events = await feedbackEvents(env, url.searchParams.get('since') || '')
      return json({ ok: true, count: events.length, events })
    }
    // POST /doodle-vote — {id, v, accuracy?: 1|-1|0, aesthetics?: 1|-1|0, like?: 1|-1|0, fav?: 1|0, by?: "bot"}.
    // GET /doodle-votes — every tally, for importers/sync_doodle_votes.py;
    // ?id=<id>&v=<v> for one version's, which the doodle page reads.
    if (url.pathname === '/doodle-vote' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rldv:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= DOODLE_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)
      const text = await request.text()
      if (text.length > 9000) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      const result = await putDoodleVote(env, request, body)
      if (result.error) return json({ error: result.error }, result.status)
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json(result)
    }
    // GET /doodle-vote-events?since=<iso> — the event log, with notes and payout
    // addresses; only with the DOODLE_EVENTS_KEY secret (importers/sync_doodle_votes.py).
    if (url.pathname === '/doodle-vote-events' && request.method === 'GET') {
      const want = env.DOODLE_EVENTS_KEY, got = request.headers.get('x-md-key') || ''
      if (!want || got.length !== want.length || got !== want) return json({ error: 'not found' }, 404)
      const since = url.searchParams.get('since') || ''
      const out = []
      let cursor
      do {
        const page = await env.KV.list({ prefix: 'dve:', cursor, limit: 1000 })
        const fresh = page.keys.filter(k => k.name.slice(4) > since)
        const vals = await Promise.all(fresh.map(k => env.KV.get(k.name)))
        fresh.forEach((k, i) => { if (vals[i]) try { out.push({ k: k.name, ...JSON.parse(vals[i]) }) } catch {} })
        cursor = page.list_complete ? null : page.cursor
      } while (cursor)
      return json({ ok: true, count: out.length, events: out })
    }
    // POST /doodle-pick — {a: {id, v}, b: {id, v}, pick: "a"|"b"|"same", payee?}
    if (url.pathname === '/doodle-pick' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rldp:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= 600) return json({ error: 'rate limit — try again later' }, 429)
      const text = await request.text()
      if (text.length > 1000) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      const result = await putDoodlePick(env, request, body)
      if (result.error) return json({ error: result.error }, result.status)
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json(result)
    }
    // GET /doodle-scores — every version anyone has voted on, compact, for the lists' sorts:
    // {"<id>@<v>": [like up, like down, looks up, looks down, favs]}; cached a minute at the edge.
    if (url.pathname === '/doodle-scores' && request.method === 'GET') {
      const ck = new Request('https://cache.mot-dang/doodle-scores')
      const hit = await caches.default.match(ck)
      if (hit) return hit
      const all = await listPrefix(env, 'dvt:'), out = {}
      for (const raw of all) {
        if (!raw.id) continue
        const t = doodleTally(raw)
        out[`${raw.id}@${raw.v}`] = [t.like[0], t.like[1], t.aesthetics[0], t.aesthetics[1], t.fav[0]]
      }
      const res = new Response(JSON.stringify({ ok: true, generated: new Date().toISOString(), scores: out }),
        { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=60', ...CORS } })
      ctx.waitUntil(caches.default.put(ck, res.clone()))
      return res
    }
    if (url.pathname === '/doodle-votes' && request.method === 'GET') {
      const id = url.searchParams.get('id'), v = url.searchParams.get('v')
      if (id) {
        if (!DOODLE_ID_RE.test(id) || !/^\d{1,4}$/.test(v || '')) return json({ error: 'bad id or v' }, 400)
        const t = doodleTally(await env.KV.get(`dvt:${id}@${v}`, 'json'))
        return new Response(JSON.stringify({ ok: true, id, v: Number(v), tally: t }),
          { headers: { 'content-type': 'application/json', 'cache-control': 'no-store', ...CORS } })
      }
      const all = await listPrefix(env, 'dvt:')
      const out = {}
      for (const t of all) if (t.id) out[`${t.id}@${t.v}`] = t
      return json({ ok: true, count: all.length, generated: new Date().toISOString(), tallies: out })
    }

    // GET /toilets — public; every report, for importers/sync_toilets.py to
    // snapshot into the repo before a build. Same two-step pattern as /claims:
    // the build itself never calls the network.
    if (url.pathname === '/toilets' && request.method === 'GET') {
      const all = await listPrefix(env, 'toilet:')
      const out = {}
      for (const r of all) out[r.placeId] = r
      return json({ ok: true, count: all.length, reports: out })
    }

    // GET/POST /edit/:token — the owner's private capability link.
    if (url.pathname.startsWith('/edit/')) {
      const token = url.pathname.slice('/edit/'.length)
      // The link is what the owner saved. Opened in a browser it is a form;
      // fetched by a script it is the record, as before.
      const page = request.method === 'GET' && wantsHtml(request)
      const placeId = token && await env.KV.get(`edit:${token}`)
      if (!placeId) return page ? claimEditPage(null, null) : json({ error: 'invalid or revoked edit link' }, 404)
      const claim = await env.KV.get(`claim:${placeId}`, 'json')
      if (!claim) return page ? claimEditPage(null, null) : json({ error: 'no such claim record' }, 404) // orphaned token; shouldn't happen

      if (request.method === 'GET') return page ? claimEditPage(placeId, claim) : json({ ok: true, placeId, claim })
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

    // POST /suggest — the "tell the ants" door, brought in-house.
    //
    // Everything a claim deliberately refuses — a name that is wrong, an
    // address that moved, a place missing entirely, a photo somebody is
    // offering, a corner of the province worth crawling — used to route to a
    // GitHub issue. When the account was hidden on 2026-08-07 that link began
    // returning 404 to every reader, on 5,784 pages, for ten days: the site
    // went on asking for help through a door that had been locked.
    //
    // Unlike a claim, nothing here publishes itself. A claim is a business's
    // own account of its own contact details, bounded so the worst case is a
    // wrong phone number. This takes free text about SOMEBODY ELSE'S place
    // from a stranger, so it can only ever be a queue that a person reads.
    if (url.pathname === '/suggest' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rls:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= SUGGEST_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)

      const text = await request.text()
      if (text.length > MAX_BODY) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }

      // A closed vocabulary, for the same reason the facet list is closed:
      // nothing a submitter types survives contact with it.
      const kind = SUGGEST_KINDS.has(body?.kind) ? body.kind : 'other'
      const what = cap(body?.what, 4000)
      if (!what) return json({ error: 'tell us what to look at' }, 400)
      // Optional; the form asks for it on closed/moved/duplicate — since
      // when, moved where, a duplicate of which page. Plain text, capped,
      // and like `what` it is never rendered anywhere unescaped.
      const detail = cap(body?.detail, SUGGEST_DETAIL_MAX) || null

      // placeId is optional — a suggestion may be about a place we do not have
      // yet — but if given it must be one of ours, so the queue can be sorted
      // by place rather than by guesswork.
      const placeId = cap(body?.placeId, 60)
      if (placeId && !PLACE_ID_RE.test(placeId))
        return json({ error: 'placeId not a recognized Mot Dang id' }, 400)

      const id = crypto.randomUUID()
      const credit = cleanCredit(body?.credit)   // null unless the box was ticked and the name passes
      await env.KV.put(`sug:${id}`, JSON.stringify({
        id,
        kind,
        what,
        detail,
        placeId: placeId || null,
        // Optional and clearly optional on the form: how to reach the person
        // if we need to ask. Their own contact detail, which does not reach the site — see
        // the note on /suggestions below.
        from: cap(body?.from, 200) || null,
        page: cap(body?.page, 300) || null,   // where they were standing when they told us
        lang: body?.lang === 'th' ? 'th' : 'en',
        credit,
        status: 'new',
        createdAt: new Date().toISOString(),
      }))
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })
      return json({ ok: true, id, ...(credit ? { ref: id.slice(0, 8) } : {}) })
    }

    // There is deliberately NO public GET for the suggestion queue.
    //
    // /claims is public because a claim is meant to be published — it becomes
    // the shop's listing. A suggestion is the opposite: unmoderated text from
    // a stranger, often carrying the sender's own phone or email so we can ask
    // a follow-up question. Serving that openly would publish contributors'
    // contact details and hand anyone a free anonymous text host on this
    // domain. The queue is read from the operator's own machine with wrangler
    // (importers/sync_suggestions.py), which is already authenticated, and
    // lands in _incoming/ — gitignored, so it can never ride into a commit.
    if (url.pathname === '/suggestions') {
      return json({ error: 'the suggestion queue is not public — it carries '
        + 'contributors\' own contact details. Read it with wrangler.' }, 403)
    }

    // POST /listing — the Listing Sheet's add form, arriving. See the block
    // above the export for why this holds rather than publishes.
    if (url.pathname === '/listing' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rlst:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= LISTING_PER_HOUR)
        return json({ error: 'that is a lot of listings in an hour — send the rest later, or email them to hello@motdang.net' }, 429)

      const text = await request.text()
      if (text.length > LISTING_MAX_BODY) return json({ error: 'too much at once — send it in smaller batches' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }

      // The listing-agent bearer from motdang.net/lister/me (lister_bearer.js).
      const gate = await listerGate(body, env)
      if (gate.refuse) return json(gate.refuse, 401)
      if (body && typeof body === 'object') delete body.lister   // a one-row body would keep it as a column

      const raw = Array.isArray(body?.listings) ? body.listings
        : (body && typeof body === 'object' ? [body] : [])
      if (!raw.length) return json({ error: 'nothing to add' }, 400)
      if (raw.length > LISTING_MAX_ROWS)
        return json({ error: `${LISTING_MAX_ROWS} listings at a time is the limit; send the rest in a second batch` }, 400)

      const rows = []
      for (let i = 0; i < raw.length; i++) {
        const r = cleanRow(raw[i])
        if (!r) return json({ error: `row ${i + 1} is not a listing` }, 400)
        const fault = listingFault(r, i)
        if (fault) return json({ error: fault }, 400)
        rows.push(r)
      }

      const id = crypto.randomUUID()
      const sub = {
        id,
        rows,
        // Their own address, so we can answer them. Not published — the
        // same reason the suggestion queue below is not public.
        from: cap(body?.from, 200) || null,
        // Their word that this may go on a page. Recorded, dated, and shown
        // in the email either way; a missing tick is not a silent refusal,
        // it is a thing the operator gets to see.
        attest: body?.attest === true,
        lang: body?.lang === 'th' ? 'th' : 'en',
        page: cap(body?.page, 300) || null,
        status: 'new',
        createdAt: new Date().toISOString(),
        okToken: crypto.randomUUID().replace(/-/g, ''),
        noToken: crypto.randomUUID().replace(/-/g, ''),
      }
      if (gate.lister) sub.lister = gate.lister
      await trustedSender(env, sub)
      await env.KV.put(`lst:${id}`, JSON.stringify(sub))
      await env.KV.put(`lstok:${sub.okToken}`, JSON.stringify({ id, act: 'approved' }), { expirationTtl: LISTING_TOKEN_TTL })
      await env.KV.put(`lstok:${sub.noToken}`, JSON.stringify({ id, act: 'held' }), { expirationTtl: LISTING_TOKEN_TTL })
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })

      // The email is the notification, not the record: the record is already
      // in KV above. So a mail failure must not lose the submission or tell
      // the sender it failed — it is counted (mailFailed, GET /health) and
      // the row waits to be pulled.
      // A trusted sender's submission is approved already; the daily digest
      // reports it, so Nan gets no per-submission mail for it.
      let mailed = !sub.approvedBy
      if (mailed) try {
        const subject = `Listing Sheet — ${rows.length > 1 ? `${rows.length} listings` : rows[0].name} (${rows[0].agency})`
        const msg = [
          `From: Mot Dang Listings <${LISTING_FROM}>`,
          `To: <${LISTING_TO}>`,
          sub.from ? `Reply-To: <${sub.from.replace(/[\r\n<>]/g, '')}>` : null,
          `Message-ID: <${id}@motdang.net>`,
          `Date: ${new Date().toUTCString()}`,
          `Subject: ${mimeWord(subject)}`,
          'MIME-Version: 1.0',
          'Content-Type: text/plain; charset=utf-8',
          'Content-Transfer-Encoding: base64',
          '',
          b64(listingEmail(sub, url.origin)),
        ].filter(x => x !== null).join('\r\n')
        await env.MAIL.send(new EmailMessage(LISTING_FROM, LISTING_TO, msg))
      } catch (err) {
        mailed = false
        await mailFailed(env, 'listing', id, err)
      }

      return json({
        ok: true,
        id,
        n: rows.length,
        mailed,
        // What the form shows the person who just pressed the button. Says
        // what happens next and does not promise a speed we do not keep.
        message: sub.from
          ? 'Got it. Someone checks it, then it goes up. We will write to you.'
          : 'Got it. Someone checks it, then it goes up.',
      })
    }

    // POST /listing-csv — a whole spreadsheet, as the agency exported it.
    //
    // WHY RAW, NOT PARSED IN THE BROWSER. An agency with forty properties has
    // them in a sheet already, and the importer on Nan's machine already
    // forgives บ้าน and house, 4.2M and 4,200,000, ครบ and furnished. Teaching
    // the browser that vocabulary would be a second copy to drift. So the
    // file goes up as it is, the Worker checks only that the six required
    // columns exist and counts the rows, and intake.py --pull does the rest
    // where the vocabulary lives. The browser shows a preview of the column
    // mapping from the same header rule, so a missing column is caught
    // before Send, not in an email a day later.
    if (url.pathname === '/listing-csv' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rlst:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= LISTING_PER_HOUR)
        return json({ error: 'that is a lot in an hour — send the rest later, or email the file to hello@motdang.net' }, 429)

      const text = await request.text()
      if (text.length > CSV_MAX_BYTES + 2000) return json({ error: 'file too large — 2 MB is the limit; split it' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      const gate = await listerGate(body, env)
      if (gate.refuse) return json(gate.refuse, 401)
      const csv = typeof body?.csv === 'string' ? body.csv : ''
      if (!csv.trim()) return json({ error: 'the file is empty' }, 400)
      if (csv.length > CSV_MAX_BYTES) return json({ error: 'file too large — 2 MB is the limit; split it' }, 400)

      const rows = csvRows(csv)
      if (rows.length < 2) return json({ error: 'a header row and at least one listing, please' }, 400)
      const head = rows[0].map(foldHead)
      const missing = CSV_REQUIRED.filter(c => !head.includes(c))
      if (missing.length)
        return json({ error: `missing column${missing.length > 1 ? 's' : ''}: ${missing.join(', ')} — the header row needs name, kind, offer, price, agency, contact` }, 400)
      const known = head.filter(h => h && LISTING_COLUMNS.has(h))
      const unknown = head.filter(h => h && !LISTING_COLUMNS.has(h))
      const agencyAt = head.indexOf('agency')

      const id = crypto.randomUUID()
      const sub = {
        id, kind: 'csv', csv,
        file: cap(body?.name, 120) || 'listings.csv',
        rowsN: rows.length - 1,
        agency: cap(rows[1][agencyAt], 120) || null,
        columns: { known, unknown: unknown.slice(0, 40) },
        from: cap(body?.from, 200) || null,
        attest: body?.attest === true,
        lang: body?.lang === 'th' ? 'th' : 'en',
        page: cap(body?.page, 300) || null,
        status: 'new',
        createdAt: new Date().toISOString(),
        okToken: crypto.randomUUID().replace(/-/g, ''),
        noToken: crypto.randomUUID().replace(/-/g, ''),
      }
      if (gate.lister) sub.lister = gate.lister
      await trustedSender(env, sub)
      await env.KV.put(`lst:${id}`, JSON.stringify(sub))
      await env.KV.put(`lstok:${sub.okToken}`, JSON.stringify({ id, act: 'approved' }), { expirationTtl: LISTING_TOKEN_TTL })
      await env.KV.put(`lstok:${sub.noToken}`, JSON.stringify({ id, act: 'held' }), { expirationTtl: LISTING_TOKEN_TTL })
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })

      // A trusted sender's submission is approved already; the daily digest
      // reports it, so Nan gets no per-submission mail for it.
      let mailed = !sub.approvedBy
      if (mailed) try {
        const subject = `Listing Sheet — spreadsheet, ${sub.rowsN} row${sub.rowsN === 1 ? '' : 's'}${sub.agency ? ` (${sub.agency})` : ''}`
        const msg = [
          `From: Mot Dang Listings <${LISTING_FROM}>`,
          `To: <${LISTING_TO}>`,
          sub.from ? `Reply-To: <${sub.from.replace(/[\r\n<>]/g, '')}>` : null,
          `Message-ID: <${id}@motdang.net>`,
          `Date: ${new Date().toUTCString()}`,
          `Subject: ${mimeWord(subject)}`,
          'MIME-Version: 1.0',
          'Content-Type: text/plain; charset=utf-8',
          'Content-Transfer-Encoding: base64',
          '',
          b64(listingEmail(sub, url.origin)),
        ].filter(x => x !== null).join('\r\n')
        await env.MAIL.send(new EmailMessage(LISTING_FROM, LISTING_TO, msg))
      } catch (err) {
        mailed = false
        await mailFailed(env, 'listing-csv', id, err)
      }
      return json({
        ok: true, id, rows: sub.rowsN, mailed, columns: sub.columns,
        message: sub.from
          ? 'Got it. Someone checks it, then it goes up. We will write to you.'
          : 'Got it. Someone checks it, then it goes up.',
      })
    }

    // POST /listing-photo — the add form's pictures, after its /listing send
    // came back with an id. Multipart: `lister` (the bearer), `sub` (the id),
    // and the files. Only the signed-in agent whose bearer the submission
    // carries may add to it. Same caps, same place and same counter as the
    // LINE path (takePhoto), so intake.py --photos-pull reads both alike.
    if (url.pathname === '/listing-photo' && request.method === 'POST') {
      if (Number(request.headers.get('content-length') || 0) > PHOTO_MAX * PHOTO_MAX_BYTES + 100_000)
        return json({ error: 'too much at once' }, 413)
      let form
      try { form = await request.formData() } catch { return json({ error: 'expected multipart form data' }, 400) }
      const who = await verifyListerBearer(form.get('lister'), env.LISTER_SECRET)
      if (!who) return json({ error: 'sign in as a listing agent to send photos', join: 'https://motdang.net/listings/join' }, 401)
      const subId = String(form.get('sub') || '')
      if (!/^[0-9a-f-]{36}$/.test(subId)) return json({ error: 'which submission?' }, 400)
      const sub = await env.KV.get(`lst:${subId}`, 'json')
      if (!sub) return json({ error: 'no such submission' }, 404)
      if (!sub.lister || sub.lister.member !== who.member) return json({ error: 'not your submission' }, 403)
      if (sub.status === 'held') return json({ error: 'that submission is held' }, 409)
      const files = [...form.values()].filter(v => v && typeof v === 'object' && typeof v.arrayBuffer === 'function')
      if (!files.length) return json({ error: 'no photos' }, 400)
      const countKey = `lstphotos:${subId}`
      const n = Number((await env.KV.get(countKey)) || 0)
      if (n + files.length > PHOTO_MAX) return json({ error: `${PHOTO_MAX} photos per listing is the limit`, n }, 400)
      for (const f of files) {
        const type = String(f.type || '').split(';')[0].trim().toLowerCase()
        if (!PHOTO_TYPES.has(type)) return json({ error: `not a photo: ${cap(f.name, 80)}` }, 415)
        if (f.size > PHOTO_MAX_BYTES) return json({ error: `over 5 MB: ${cap(f.name, 80)}` }, 413)
      }
      const names = []
      for (const f of files) {
        const type = String(f.type).split(';')[0].trim().toLowerCase()
        const name = photoName(f.name, type)
        await env.PHOTOS.put(`inbox/${subId}/${name}`, await f.arrayBuffer(), {
          httpMetadata: { contentType: type },
          customMetadata: { submission: subId, lister: who.member, at: new Date().toISOString() },
        })
        names.push(name)
      }
      await env.KV.put(countKey, String(n + files.length))
      return json({ ok: true, n: n + files.length, names })
    }

    // POST /notify — the sheet's nightly asks for a LINE push. Shared key,
    // set as a secret on both sides; email never comes through here (the
    // Mac sends that itself).
    if (url.pathname === '/notify' && request.method === 'POST') {
      const text = await request.text()
      if (text.length > MAX_BODY) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(text) } catch { return json({ error: 'invalid json' }, 400) }
      if (!env.NOTIFY_KEY || body?.key !== env.NOTIFY_KEY) return json({ error: 'no' }, 403)
      const to = cap(body?.to, 60), msg = cap(body?.text, 1500)
      if (!to || !msg) return json({ error: 'to and text' }, 400)
      const ok = await linePush(env, to, msg)
      return json({ ok })
    }

    // GET /listing/confirm/:token — the lister's one tap from the lapse
    // email or LINE message: "still current". Records the day; the next pull
    // moves as_of forward and the row stays live. Same capability-token
    // shape as everything else here.
    if (url.pathname.startsWith('/listing/confirm/')) {
      const token = url.pathname.slice('/listing/confirm/'.length)
      const rec = token && await env.KV.get(`lstcf:${token}`, 'json')
      if (!rec) return listingPage('That link has expired', 'Send the listing again from motdang.net/listings/add.html and it will be current from today.')
      await env.KV.put(`lstconfirmed:${rec.file}`, JSON.stringify({ at: new Date().toISOString().slice(0, 10), key: rec.key, token }))
      return listingPage('ยืนยันแล้ว · Confirmed',
        `${rec.name || rec.key} — current as of today. The sheet updates at the next build.`)
    }

    // GET /listing/ok/:token · /listing/no/:token — the operator's one tap,
    // from the email, on a phone. A capability token, the same shape as
    // /edit/:token: no sign-in, and it names one submission only.
    if (url.pathname.startsWith('/listing/ok/') || url.pathname.startsWith('/listing/no/')) {
      const token = url.pathname.slice('/listing/ok/'.length)
      const rec = token && await env.KV.get(`lstok:${token}`, 'json')
      if (!rec) return listingPage('That link has expired',
        'Nothing is lost — the listing is still in the queue. Pull it by hand with <code>intake.py --pull --all</code>.')
      const sub = await env.KV.get(`lst:${rec.id}`, 'json')
      if (!sub) return listingPage('Already gone', 'That submission is no longer in the queue.')
      if (sub.status === 'pulled') return listingPage('Already on the sheet',
        'This one was published and written to the sheet already.')

      const was = sub.status
      sub.status = rec.act
      sub.decidedAt = new Date().toISOString()
      await env.KV.put(`lst:${rec.id}`, JSON.stringify(sub))
      const what = sub.kind === 'csv' ? `${sub.rowsN} row(s) from ${sub.file}`
        : sub.rows.length > 1 ? `${sub.rows.length} listings` : sub.rows[0].name
      // Held means held, pictures included. Leaving them in the bucket would
      // keep a stranger's images on our storage indefinitely for a listing
      // nobody will publish.
      if (rec.act === 'held') {
        try {
          const listed = await env.PHOTOS.list({ prefix: `inbox/${rec.id}/` })
          for (const o of listed.objects) await env.PHOTOS.delete(o.key)
          await env.KV.delete(`lstphotos:${rec.id}`)
        } catch (err) { console.log('photo cleanup failed', String(err)) }
      }

      return rec.act === 'approved'
        ? listingPage('Publishing', `${what} — the next pull writes it to the sheet and rebuilds. Tap the other link if you change your mind before then.`)
        : listingPage('Held', `${what} — kept back${was === 'approved' ? ', and the earlier approval is cancelled' : ''}. Nothing is deleted.`)
    }

    // No public GET for the listing queue, for exactly the reason given under
    // /suggestions: it carries the sender's own email address, given so we
    // could write back. intake.py --pull reads KV with wrangler.
    if (url.pathname === '/listings-inbox') {
      return json({ error: 'the listing queue is not public — it carries '
        + 'senders\' own contact details. Read it with intake.py --pull.' }, 403)
    }

    /* ============== ALPHA — DELETE THIS BLOCK AT BETA ==================== */

    // POST /alpha — one tester, one thumb, one request. The note, the context
    // the page collected, and up to three screenshots arrive together as
    // multipart, so there is no half-arrived report to reconcile.
    if (url.pathname === '/alpha' && request.method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown'
      const bucket = `rlal:${ip}:${Math.floor(Date.now() / 3600_000)}`
      const count = Number((await env.KV.get(bucket)) || 0)
      if (count >= ALPHA_PER_HOUR) return json({ error: 'rate limit — try again later' }, 429)

      const ct = (request.headers.get('content-type') || '').toLowerCase()
      let raw = '', files = []
      if (ct.includes('multipart/form-data')) {
        let form
        try { form = await request.formData() } catch { return json({ error: 'bad form' }, 400) }
        raw = String(form.get('report') || '')
        for (const [k, v] of form.entries()) {
          if (!k.startsWith('shot') || typeof v === 'string') continue
          if (files.length >= ALPHA_MAX_SHOTS) break
          files.push(v)
        }
      } else {
        raw = await request.text()
      }
      if (raw.length > MAX_BODY) return json({ error: 'body too large' }, 400)
      let body
      try { body = JSON.parse(raw) } catch { return json({ error: 'invalid json' }, 400) }

      const v = body?.v === 'up' ? 'up' : body?.v === 'down' ? 'down' : ''
      if (!v) return json({ error: 'v must be up or down' }, 400)

      const id = `a${Date.now().toString(36)}-${crypto.randomUUID().slice(0, 6)}`
      const rec = {
        id, v,
        who: cap(body?.who, 40),
        note: cap(body?.note, 4000),
        at: cap(body?.at, 40) || new Date().toISOString(),
        build: cap(body?.build, 20),
        ctx: body?.ctx && typeof body.ctx === 'object' ? body.ctx : {},
        ip: null,               // deliberately not kept; the tester has a name
      }

      // The pictures. A file that is the wrong type or too big is dropped and
      // SAID SO in the record rather than failing the report — a tester who
      // attached a 20 MB screenshot still has a bug worth reading.
      const shots = [], dropped = []
      for (const f of files) {
        const type = String(f.type || '').split(';')[0].trim().toLowerCase()
        const buf = await f.arrayBuffer()
        if (!PHOTO_TYPES.has(type)) { dropped.push({ name: cap(f.name, 80), why: `type ${type || '?'}` }); continue }
        if (buf.byteLength > ALPHA_MAX_BYTES) { dropped.push({ name: cap(f.name, 80), why: `${Math.round(buf.byteLength / 1e6)} MB` }); continue }
        const ext = type === 'image/png' ? 'png' : type === 'image/webp' ? 'webp'
          : (type === 'image/heic' || type === 'image/heif') ? 'heic' : 'jpg'
        const key = `alpha/${id}/${shots.length + 1}.${ext}`
        await env.PHOTOS.put(key, buf, {
          httpMetadata: { contentType: type },
          customMetadata: { report: id, tester: rec.who, at: rec.at },
        })
        shots.push({ key, type, bytes: buf.byteLength, buf })
      }
      rec.shots = shots.map(s => ({ key: s.key, type: s.type, bytes: s.bytes }))
      if (dropped.length) rec.dropped = dropped

      await env.KV.put(`alpha:${id}`, JSON.stringify(rec), { expirationTtl: ALPHA_TTL })
      await env.KV.put(bucket, String(count + 1), { expirationTtl: 3600 })

      // The record is already safe above, so the mail is best-effort and its
      // failure is counted (mailFailed, GET /health) rather than raised.
      let mailed = true
      try {
        const subject = `Mot Dang alpha — ${rec.v === 'up' ? 'worked' : 'went wrong'}`
          + ` — ${rec.who || 'tester'} — ${(rec.ctx.url || '').replace(/^https?:\/\/[^/]+/, '') || '/'}`
        const text = alphaEmail(rec, shots)
        const small = shots.filter(s => s.bytes < ALPHA_MAIL_BYTES)
        const head = [
          `From: Mot Dang Alpha <${ALPHA_FROM}>`,
          `To: <${ALPHA_TO}>`,
          `Message-ID: <${id}@motdang.net>`,
          `Date: ${new Date().toUTCString()}`,
          `Subject: ${mimeWord(subject)}`,
          'MIME-Version: 1.0',
        ]
        let msg
        if (small.length) {
          const b = `mdalpha${id}`
          const parts = [
            `Content-Type: multipart/mixed; boundary="${b}"`, '',
            `--${b}`,
            'Content-Type: text/plain; charset=utf-8',
            'Content-Transfer-Encoding: base64', '',
            b64(text),
          ]
          for (const s of small) {
            const name = s.key.split('/').pop()
            parts.push(`--${b}`,
              `Content-Type: ${s.type}; name="${name}"`,
              `Content-Disposition: attachment; filename="${id}-${name}"`,
              'Content-Transfer-Encoding: base64', '',
              b64bytes(s.buf))
          }
          parts.push(`--${b}--`)
          msg = head.concat(parts).join('\r\n')
        } else {
          msg = head.concat([
            'Content-Type: text/plain; charset=utf-8',
            'Content-Transfer-Encoding: base64', '',
            b64(text),
          ]).join('\r\n')
        }
        await env.MAIL.send(new EmailMessage(ALPHA_FROM, ALPHA_TO, msg))
      } catch (err) {
        mailed = false
        await mailFailed(env, 'alpha', id, err)
      }

      return json({ ok: true, id, shots: shots.length, dropped: dropped.length, mailed })
    }

    // GET /alpha-reports?key=… — the whole queue, for importers/sync_alpha.py.
    // Free text written by named testers, so unlike /toilets this one is not
    // public: it answers only to the ALPHA_KEY secret, and 404s where no key
    // is configured so an unset secret can never read as an open door.
    if (url.pathname === '/alpha-reports' && request.method === 'GET') {
      const want = env.ALPHA_KEY || ''
      const got = url.searchParams.get('key') || ''
      if (!want || got.length !== want.length || got !== want)
        return json({ error: 'not found' }, 404)
      const all = await listPrefix(env, 'alpha:')
      all.sort((a, b) => String(a.at).localeCompare(String(b.at)))
      return json({ ok: true, count: all.length, reports: all })
    }

    /* ============ end ALPHA — DELETE THIS BLOCK AT BETA ================== */

    return json({ error: 'not found', endpoints: ['/claim', '/edit/:token', '/claims',
      '/toilet', '/toilets', '/feedback', '/feedback-tally', '/doodle-vote', '/doodle-votes', '/doodle-scores', '/doodle-pick', '/suggest', '/listing', '/listing-csv', '/listing/confirm/:token', '/webhook/line', '/alpha', '/health'] }, 404)
  },

  /* ============== ALPHA — DELETE THIS BLOCK AT BETA ==================== */
  // [triggers] crons in wrangler.toml lands here nightly. Only the alpha
  // sweep hangs off it; when this block goes, that toml line goes with it.
  async scheduled(event, env) {
    await alphaSweep(env)
  },
  /* ============ end ALPHA — DELETE THIS BLOCK AT BETA ================== */
}
