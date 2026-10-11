// GENERATED FILE — do not edit here.
// Source: search-core/searchcore.js. Regenerate with search-core/sync.py.
// Edits made here are silently overwritten and escape parity.py, which is
// the one thing keeping the two runtimes agreeing on what a query means.
// searchcore.js — the JS half of the fleet's forgiving search.
//
// A line-for-line twin of searchcore.py, because the same query has to mean the
// same thing in three places: Mot Dang's client-side search, the wichaa router
// Worker's re-rank, and the Python that builds both indexes. Two
// implementations of one set of rules will drift, so parity.py runs a few
// thousand queries through both and fails the build when they disagree. If you
// change a rule here, change it there, and run parity.
//
// No imports, no build step, no framework. It is pasted into a page by build.py
// and imported by the Worker, and it has to work on a five-year-old phone on a
// satellite connection.

'use strict';

// ---- layer 0: normalization ------------------------------------------------

const SARA_AM = 'ํา';        // ํ + า, the decomposed spelling of ำ
const RE_TONE_NIKHAHIT_AA = /([่-๋])ํา/g;
const RE_NIKHAHIT_AA = /ํา/g;
const RE_ZERO_WIDTH = /[​-‏‪-‮﻿]/g;
const RE_THAI = /[฀-๿]/;
// The Thai block is whitelisted explicitly, and it has to be. Thai vowels and
// tone marks are Unicode category Mn — MARKS, not letters — so \p{L}\p{N} alone
// does not match them and ก๋วยเตี๋ยว came out of normalization as "ก วยเต ยว",
// shredded into fragments that could match nothing. Caught by parity.py against
// the Python side, which had the whitelist from the start.
const RE_NONWORD = /(?:[^\p{L}\p{N}฀-๿]|_)+/gu;

function hasThai(s) { return RE_THAI.test(s || ''); }

// Drop accents from Latin letters; leave every Thai mark alone. "Café de Nimman"
// and "cafe" are the same shop. Thai must be exempt: its vowels and tone marks
// ARE combining characters, so stripping them would delete the word.
function stripLatinMarks(s) {
  // eslint-disable-next-line no-control-regex
  if (!/[^-]/.test(s)) return s;
  const out = [];
  for (const ch of s.normalize('NFD')) {
    if (/\p{M}/u.test(ch)) {
      const base = out.length ? out[out.length - 1] : '';
      if (base && /[a-zA-Z]/.test(base)) continue;
    }
    out.push(ch);
  }
  return out.join('').normalize('NFC');
}

function norm(s) {
  if (!s) return '';
  s = s.normalize('NFC').replace(RE_ZERO_WIDTH, '');
  s = s.replace(RE_TONE_NIKHAHIT_AA, '$1ำ').replace(RE_NIKHAHIT_AA, 'ำ');
  s = stripLatinMarks(s);
  return s.toLowerCase().replace(RE_NONWORD, ' ').trim();
}

// Thai homophone classes: several letters share one sound because they arrived
// from Sanskrit or Pali with their spelling intact, so a reader who knows how a
// word sounds but not which of the four /t/ letters it takes is reporting a real
// ambiguity in the script rather than making a mistake.
const TH_CLASSES = {
  'ก': 'ก', 'ขฃคฅฆ': 'ค', 'ง': 'ง', 'จ': 'จ', 'ฉชฌ': 'ช', 'ซศษส': 'ส',
  'ญย': 'ย', 'ฎด': 'ด', 'ฏต': 'ต', 'ฐฑฒถทธ': 'ท', 'ณน': 'น', 'บ': 'บ',
  'ป': 'ป', 'ผพภ': 'พ', 'ฝฟ': 'ฟ', 'ม': 'ม', 'ร': 'ร', 'ลฬ': 'ล', 'ว': 'ว',
  'หฮ': 'ห', 'อ': 'อ', 'ฤ': 'ร', 'ฦ': 'ล',
};
const TH_MAP = {};
for (const cls in TH_CLASSES) for (const ch of cls) TH_MAP[ch] = TH_CLASSES[cls];

const TH_VOWELS = {
  'ี': 'ิ', 'ิ': 'ิ', 'ื': 'ึ', 'ึ': 'ึ', 'ู': 'ุ', 'ุ': 'ุ',
  'ั': 'ะ', 'ะ': 'ะ', '็': 'ะ', 'ใ': 'ไ', 'ไ': 'ไ', 'ๅ': 'า', 'า': 'า',
};
// ็ (mai taikhu) belongs here, and its absence was a live parity failure: the
// Python side dropped it while JS mapped it to ะ, so เมล็ดกาแฟ produced two
// different phonetic keys and coffee-bean shops were findable from one runtime
// and not the other.
const TH_TO_LATIN_CONS = {
    'ก': 'k', 'ข': 'k', 'ฃ': 'k', 'ค': 'k', 'ฅ': 'k', 'ฆ': 'k',
    'ง': 'g', 
    'จ': 'c', 'ฉ': 'c', 'ช': 'c', 'ฌ': 'c',
    'ซ': 's', 'ศ': 's', 'ษ': 's', 'ส': 's',
    'ญ': 'y', 'ย': 'y',
    'ฎ': 'd', 'ด': 'd', 
    'ฏ': 't', 'ต': 't',
    'ฐ': 't', 'ฑ': 't', 'ฒ': 't', 'ถ': 't', 'ท': 't', 'ธ': 't',
    'ณ': 'n', 'น': 'n',
    'บ': 'b', 'ป': 'p', 
    'ผ': 'p', 'พ': 'p', 'ภ': 'p',
    'ฝ': 'f', 'ฟ': 'f', 
    'ม': 'm',
    'ร': 'r',
    'ล': 'l', 'ฬ': 'l', 
    'ว': 'w',
    'ห': 'h', 'ฮ': 'h', 
    'ฤ': 'ru', 'ฦ': 'lu',
};

const TH_TO_LATIN_VOWEL = {
    'ี': 'i', 'ิ': 'i',
    'ื': 'u', 'ึ': 'u',
    'ู': 'u', 'ุ': 'u',
    'ั': 'a', 'ะ': 'a', '็': 'a',
    'ใ': 'i', 'ไ': 'i', 'ัย': 'ai',
    'ๅ': 'a', 'า': 'a',
    'ำ': 'am',
    'เ': 'e', 'แ': 'e', 'โ': 'o',
};

const TH_DROP = new Set(['่', '้', '๊', '๋', '์', 'ฺ', '๎', 'ๆ']);

// Thai reaches Latin letters through at least six romanisation habits, so one
// shop is Rajavej, Rachawet and Ratchavej on three different signs.
const LATIN_DIGRAPHS = [
  ['tch', 'c'], ['dch', 'c'],
  ['kh', 'k'], ['ph', 'p'], ['th', 't'], ['ch', 'c'], ['gh', 'k'], ['ng', 'g'],
  ['ee', 'i'], ['ii', 'i'], ['ie', 'i'],
  ['oo', 'u'], ['uu', 'u'], ['ou', 'u'], ['ue', 'u'], ['eu', 'u'],
  ['ae', 'e'], ['oe', 'e'], ['ei', 'i'],
  ['ai', 'i'], ['ay', 'i'],
  ['aw', 'o'], ['au', 'o'], ['or', 'o'], ['ao', 'o'],
  ['ua', 'u'], ['uo', 'u'],
];
const LATIN_SINGLES = {
  g: 'k', j: 'c', q: 'k', x: 's', z: 's', v: 'w',
  b: 'p', d: 't', f: 'p', l: 'r', y: 'i', h: '',
};

// A phonetic key: two spellings of one sound collapse to one string. Compared
// with bounded edit distance rather than instead of it — the key removes the
// systematic differences, the distance absorbs the ordinary slips left over.
function loose(tok) {
  tok = norm(tok);
  if (!tok) return '';
  let key = '';
  if (hasThai(tok)) {
    const chars = Array.from(tok);
    let i = 0;
    while (i < chars.length - 1) {
      if ('เแโใไ'.includes(chars[i]) && !'เแโใไ'.includes(chars[i+1])) {
        const tmp = chars[i];
        chars[i] = chars[i+1];
        chars[i+1] = tmp;
        i += 2;
      } else {
        i += 1;
      }
    }
    const out = [];
    for (let j = 0; j < chars.length; j++) {
      const ch = chars[j];
      if (TH_DROP.has(ch)) continue;
      if (ch === 'อ') {
        if (j === 0) out.push('');
        else out.push('o');
      } else if (TH_TO_LATIN_CONS[ch]) {
        out.push(TH_TO_LATIN_CONS[ch]);
      } else if (TH_TO_LATIN_VOWEL[ch]) {
        out.push(TH_TO_LATIN_VOWEL[ch]);
      } else {
        out.push(ch);
      }
    }
    key = out.join('');
  } else {
    key = tok;
  }
  for (const [a, b] of LATIN_DIGRAPHS) {
    key = key.split(a).join(b);
  }
  let dedupKey = '';
  for (let i = 0; i < key.length; i++) {
    const ch = Object.hasOwn(LATIN_SINGLES, key[i]) ? LATIN_SINGLES[key[i]] : key[i];
    if (!dedupKey || dedupKey[dedupKey.length - 1] !== ch) dedupKey += ch;
  }
  if (!hasThai(tok) && dedupKey.length * 2 < tok.length) return '';
  return dedupKey;
}
function edits(a, b, cap) {
  const la = a.length, lb = b.length;
  if (Math.abs(la - lb) > cap) return cap + 1;
  if (a === b) return 0;
  let prev2 = [], prev = [], cur = [];
  for (let j = 0; j <= lb; j++) prev.push(j);
  for (let i = 1; i <= la; i++) {
    cur = new Array(lb + 1).fill(cap + 1);
    cur[0] = i;
    const lo = Math.max(1, i - cap), hi = Math.min(lb, i + cap);
    for (let j = lo; j <= hi; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      let v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        v = Math.min(v, prev2[j - 2] + 1);
      }
      cur[j] = v;
    }
    let best = cap + 1;
    for (let j = lo; j <= hi; j++) if (cur[j] < best) best = cur[j];
    if (best > cap) return cap + 1;
    prev2 = prev; prev = cur;
  }
  return prev[lb];
}

// How much misspelling a token has earned. One edit turns ยา into ยาย and มา
// into หมา, so short words get no slack at all.
//
// Two edits start at EIGHT characters, and the extra character was bought with a
// real miss: `pharmacy` reduces to the key `parmaci` and `palace` to `parace`,
// two edits apart, so a search for a chemist returned thirteen hotels with
// Palace in the name. Two edits out of seven is a quarter of the word. The ratio
// is what matters, not the count.
function slack(tok) {
  const n = tok.length;
  if (n <= 3) return 0;
  if (n <= 7) return 1;
  return 2;
}

// ---- layer 2: Thai segmentation -------------------------------------------
// Dictionary longest-match. The dictionary is the point: a general wordlist
// segments grammar, a wordlist drawn from the corpus being searched segments the
// things a reader is looking for. NOT character n-grams — boosting the syllable
// ภัย is what once made ยันต์กันภัย return ภัยยะราด.

class Segmenter {
  constructor(words) {
    this.words = new Set();
    this.maxlen = 1;
    for (let w of words || []) {
      w = norm(w);
      if (w.length >= 2 && hasThai(w)) {
        this.words.add(w);
        if (w.length > this.maxlen) this.maxlen = w.length;
      }
    }
    this.maxlen = Math.min(this.maxlen, 30);
    this.byLoose = null;
    this.looseByLen = null;
  }

  // Loose key -> the dictionary words sharing it, bucketed by key length, for
  // repairing a misspelled chunk before anything tries to split it. Built on
  // the first repair, not in the constructor: keying all ~41,000 words is most
  // of what a cold Worker spent before it could answer a correctly spelled
  // query (2026-10-03).
  _looseIndex() {
    if (this.byLoose) return;
    this.byLoose = new Map();
    this.looseByLen = new Map();
    for (const w of this.words) {
      const k = loose(w);
      if (!k) continue;
      if (!this.byLoose.has(k)) {
        this.byLoose.set(k, []);
        if (!this.looseByLen.has(k.length)) this.looseByLen.set(k.length, []);
        this.looseByLen.get(k.length).push(k);
      }
      this.byLoose.get(k).push(w);
    }
    for (const bucket of this.looseByLen.values()) bucket.sort();
  }

  // The dictionary word a misspelled chunk was probably meant to be.
  //
  // Segmentation and misspelling fight each other, and segmentation wins by
  // default in the worst way: ราชเวส is in no dictionary, but ราช and เวส both
  // are, so a hospital's name was shredded into two real three-character words —
  // too short to earn any edit slack — and ราชเวช became unreachable. A name
  // misspelled by one letter has to be recognised as a name BEFORE it is split.
  nearest(chunk) {
    chunk = norm(chunk);
    if (!chunk || !hasThai(chunk) || this.words.has(chunk)) return null;
    const key = loose(chunk);
    if (!key) return null;
    this._looseIndex();
    const pick = (words) => words.slice().sort((a, b) =>
      Math.abs(a.length - chunk.length) - Math.abs(b.length - chunk.length)
      || (a < b ? -1 : a > b ? 1 : 0))[0];
    if (this.byLoose.has(key)) return pick(this.byLoose.get(key));
    const cap = slack(key);
    if (!cap) return null;
    let best = null, bestD = cap + 1;
    for (let L = key.length - cap; L <= key.length + cap; L++) {
      for (const k of (this.looseByLen.get(L) || [])) {
        const d = edits(key, k, cap);
        if (d < bestD) { best = k; bestD = d; if (d === 1) break; }
      }
      if (bestD === 1) break;
    }
    return best === null ? null : pick(this.byLoose.get(best));
  }

  // Dynamic programming, minimising token count then preferring the longer
  // split — which beats greedy left-to-right on exactly the compounds that
  // matter, where greedy takes a long wrong prefix and strands the rest.
  split(s) {
    s = norm(s);
    if (!s || !hasThai(s) || !this.words.size) return s ? [s] : [];
    const n = s.length;
    const cost = new Array(n + 1).fill(Infinity);
    const len = new Array(n + 1).fill(0);
    const back = new Array(n + 1).fill(-1);
    const known = new Array(n + 1).fill(false);
    cost[0] = 0; len[0] = 0;
    const better = (i, c, l) => c < cost[i] || (c === cost[i] && l > len[i]);
    for (let i = 0; i < n; i++) {
      if (cost[i] === Infinity) continue;
      let hit = false;
      for (let L = Math.min(this.maxlen, n - i); L > 1; L--) {
        if (this.words.has(s.substr(i, L))) {
          hit = true;
          const c = cost[i] + 1, l = len[i] + L;
          if (better(i + L, c, l)) {
            cost[i + L] = c; len[i + L] = l; back[i + L] = i; known[i + L] = true;
          }
        }
      }
      if (!hit) {
        // An unknown run costs the same as a word, so the segmenter prefers to
        // explain a string with known words but never refuses one it cannot.
        const c = cost[i] + 1, l = len[i];
        if (better(i + 1, c, l)) {
          cost[i + 1] = c; len[i + 1] = l; back[i + 1] = i; known[i + 1] = false;
        }
      }
    }
    if (cost[n] === Infinity) return [s];
    const parts = [];
    let j = n;
    while (j > 0) { const i = back[j]; parts.push([s.slice(i, j), known[j]]); j = i; }
    parts.reverse();
    const out = [];
    for (const [text, isKnown] of parts) {
      if (isKnown || !out.length || out[out.length - 1][1]) out.push([text, isKnown]);
      else out[out.length - 1][0] += text;
    }
    return out.map(x => x[0]).filter(t => t.trim());
  }
}

// ---- layer 1: intent -------------------------------------------------------
// A search box is the only place most readers will ever tell a site what they
// want, and they do not phrase it as keywords. Read as filters, four of the five
// words in "cheap dentist open now" stop competing with the one that matters.

const INTENT_RULES = [
  ['open', 'now', ['open now', 'opennow', 'whats open', 'what is open',
    'เปิดอยู่', 'เปิดตอนนี้', 'เปิดไหม', 'ตอนนี้เปิด', 'เปิดยัง']],
  ['open', 'late', ['open late', 'late night', 'after midnight', '24 hours',
    '24hr', '24h', 'all night', 'เปิดดึก', 'ดึก', 'กลางคืน', '24 ชม', '24ชม',
    'ตลอดคืน', 'เปิด 24']],
  ['open', 'early', ['open early', 'breakfast time', 'เปิดเช้า', 'ตอนเช้า', 'เช้ามาก']],
  ['open', 'sunday', ['open sunday', 'on sunday', 'sundays', 'เปิดวันอาทิตย์',
    'วันอาทิตย์']],
  ['open', 'weekend', ['weekend', 'on saturday', 'open saturday', 'สุดสัปดาห์',
    'เสาร์อาทิตย์', 'วันเสาร์']],
  ['near', 'me', ['near me', 'nearby', 'near here', 'close to me', 'around here',
    'walking distance', 'ใกล้ฉัน', 'ใกล้ๆ', 'ใกล้นี่', 'แถวนี้', 'ใกล้เคียง',
    'เดินไปได้']],
  ['price', 'low', ['cheap', 'cheapest', 'budget', 'affordable', 'low price',
    'inexpensive', 'ถูก', 'ถูกๆ', 'ราคาถูก', 'งบน้อย', 'ไม่แพง', 'ประหยัด',
    'ราคาย่อมเยา']],
  ['price', 'high', ['expensive', 'high end', 'luxury', 'premium', 'upscale',
    'แพง', 'หรู', 'ระดับพรีเมียม', 'ไฮเอนด์']],
  ['rank', 'best', ['best', 'top', 'recommended', 'highest rated', 'good',
    'favourite', 'favorite', 'ดีที่สุด', 'แนะนำ', 'ยอดนิยม', 'เด็ด', 'ร้านดัง',
    'ขึ้นชื่อ']],
  ['diet', 'vegetarian', ['vegetarian', 'veggie', 'meatless', 'no meat',
    'มังสวิรัติ', 'ไม่ใส่เนื้อ', 'ไม่กินเนื้อ']],
  ['diet', 'vegan', ['vegan', 'เจ', 'อาหารเจ', 'กินเจ']],
  ['diet', 'halal', ['halal', 'muslim food', 'ฮาลาล', 'อาหารมุสลิม']],
  ['access', 'wheelchair', ['wheelchair', 'wheelchair accessible', 'step free',
    'accessible', 'รถเข็น', 'วีลแชร์', 'ทางลาด', 'ไม่มีบันได']],
  ['access', 'parking', ['parking', 'car park', 'with parking', 'ที่จอดรถ',
    'จอดรถได้', 'ลานจอดรถ']],
  ['access', 'english', ['english speaking', 'speaks english', 'in english',
    'พูดอังกฤษ', 'พูดภาษาอังกฤษ', 'มีภาษาอังกฤษ']],
  ['kids', 'yes', ['with kids', 'for kids', 'child friendly', 'kid friendly',
    'family friendly', 'พาเด็ก', 'เด็กเล่น', 'ครอบครัว', 'เหมาะกับเด็ก']],
  ['pets', 'yes', ['dog friendly', 'pet friendly', 'with my dog',
    'พาสัตว์เลี้ยง', 'พาหมาได้', 'สัตว์เลี้ยงเข้าได้']],
  ['wifi', 'yes', ['wifi', 'wi fi', 'internet', 'work from', 'laptop friendly',
    'ไวไฟ', 'นั่งทำงาน', 'นั่งทำงานได้']],
  // Air-con, in its compound forms only (see searchcore.py).
  ['aircon', 'yes', ['air conditioned', 'air-conditioned', 'airconditioned',
    'with aircon', 'with air con', 'with ac', 'has aircon',
    'aircon room', 'cool inside',
    'มีแอร์', 'ห้องแอร์', 'เปิดแอร์', 'แอร์เย็น']],
  ['delivery', 'yes', ['delivery', 'delivers', 'takeaway', 'take away',
    'ส่งถึงบ้าน', 'เดลิเวอรี', 'สั่งกลับบ้าน', 'ใส่กล่อง']],
  ['appointment', 'walkin', ['walk in', 'walkin', 'no appointment',
    'without appointment', 'วอล์กอิน', 'ไม่ต้องนัด', 'เดินเข้าไปได้']],
  // A size is a constraint, not a word to match — see searchcore.py.
  ['size', 'big', ['big size', 'big sizes', 'bigsize', 'big-size', 'plus size',
    'plus sizes', 'plussize', 'large size', 'large sizes', 'extra large',
    'xxl', '3xl', '4xl', '5xl', 'ไซส์ใหญ่', 'บิ๊กไซส์', 'ไซส์พิเศษ',
    'ไซส์ใหญ่พิเศษ', 'อวบอ้วน', 'สาวอวบ', 'คนอ้วน']],
];

// The words a person wraps a question in. They carry the intent to ASK, which
// the search box already knew.
const QUESTION_SCAFFOLD = [
  'where can i find', 'where can i', 'where do i', 'where is the', 'where is',
  'where are the', 'where are', 'is there a', 'is there any', 'is there',
  'are there any', 'are there', 'how do i find', 'how do i', 'i am looking for',
  'im looking for', 'i need a', 'i need', 'i want a', 'i want', 'looking for',
  'show me the', 'show me', 'find me a', 'find me', 'any good', 'what is the',
  'whats the', 'somewhere to', 'some place to', 'a place to', 'place to',
  'can i get', 'who does', 'who sells', 'does anyone',
  'ที่ไหน', 'อยู่ไหน', 'มีไหม', 'มีที่ไหน', 'หาที่ไหน', 'แนะนำร้าน', 'อยากหา',
  'อยากได้', 'ช่วยหา', 'หา', 'ขอ', 'ที่ใด',
];

// Function words. Left in, each becomes a term in its own right, and a term
// costs coverage: "a restaurant" demanded a match on both words and scored
// every result at half coverage for the privilege.
const STOPWORDS = new Set([
  'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'with',
  'without', 'is', 'are', 'am', 'be', 'was', 'were', 'do', 'does', 'did',
  'my', 'me', 'i', 'we', 'you', 'it', 'its', 'this', 'that', 'these', 'those',
  'there', 'here', 'some', 'any', 'get', 'got', 'go', 'goes', 'can', 'could',
  'would', 'should', 'will', 'shall', 'have', 'has', 'had', 'please', 'thanks',
  'about', 'around', 'from', 'by', 'as', 'so', 'too', 'very', 'just', 'also',
  'ที่', 'ของ', 'และ', 'หรือ', 'ใน', 'กับ', 'แล้ว', 'ครับ', 'ค่ะ', 'คะ', 'นะ',
  'จะ', 'ได้', 'ให้', 'เป็น', 'อยู่', 'มี', 'ไป', 'มา', 'ด้วย', 'ก็', 'แบบ',
  'อะ', 'อ่ะ', 'หน่อย', 'บ้าง', 'ไหน', 'ไหม', 'มั้ย', 'อยาก', 'ช่วย',
  // The English possessive, left behind when norm flattens the apostrophe to a
  // space. It is not a word and it was being treated as a required term: a
  // search for "women's health" asked for women AND s AND health, no listing in
  // the directory answered all three, and the page fell back to
  // most-words-matched — which is every place with "health" or "สุขภาพ" in its
  // name, i.e. all 469 subdistrict health stations. Dropping it lets the pair
  // rule see "women health" and read it as the one thing the reader asked for.
  's',
]);

// The captured word must include the Thai block for the same reason norm does:
// Thai vowels are marks, so \p{L}\p{N} alone captured เน out of ไม่เอาเนื้อ and
// excluded a fragment while leaving the rest of the word in the query.
const RE_NEG = /(?:\bnot\b|\bno\b|\bwithout\b|\bexcept\b|-\s*|ไม่เอา|ไม่ใช่|ยกเว้น|ไม่มี)\s*([\p{L}\p{N}฀-๿]+)/gu;

function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

function stripPhrase(hay, phrase) {
  if (!phrase) return [hay, false];
  if (hasThai(phrase)) {
    // A THAI PHRASE IS STRIPPED ONLY AT A BOUNDARY. Thai has no spaces, and
    // "substring is the boundary" mutilated the words the phrase sat inside:
    // หา ("find") cut อาหาร (food) into อา + ร, ขอ ("may I") cut ของกิน into
    // งกิน, and เจ (vegan) cut เจดีย์ (chedi) out of every temple named for
    // one — while setting diet:vegan on the search. Found 2026-09-10 by the
    // first miss report (อาหาร answered with two loose rows). A match now
    // needs a non-Thai character or the string's edge on BOTH sides; a
    // phrase typed inside an unspaced run is left to the segmenter and the
    // stopword list, which is where "หาร้านอาหาร" already ends up right.
    let hit = false, out = '', i = 0;
    while (i < hay.length) {
      const j = hay.indexOf(phrase, i);
      if (j === -1) { out += hay.slice(i); break; }
      const before = j === 0 ? '' : hay[j - 1];
      const after = hay[j + phrase.length] || '';
      if (!RE_THAI.test(before) && !RE_THAI.test(after)) { out += hay.slice(i, j) + ' '; hit = true; }
      else out += hay.slice(i, j + phrase.length);
      i = j + phrase.length;
    }
    return [out, hit];
  }
  // No lookbehind: Safari shipped it late and these pages run on old phones.
  const re = new RegExp('(^|[^\\p{L}\\p{N}])' + escapeRe(phrase) +
                        '(?![\\p{L}\\p{N}])', 'gu');
  let hit = false;
  const out = hay.replace(re, (m, p1) => { hit = true; return p1 + ' '; });
  return [out, hit];
}

function parseIntent(q, rules) {
  rules = rules || INTENT_RULES;
  const filters = {}, exclude = [], phrases = [];
  let hay = ' ' + norm(q) + ' ';

  RE_NEG.lastIndex = 0;
  let m;
  while ((m = RE_NEG.exec(hay)) !== null) {
    const w = m[1];
    if (w && w !== 'open' && w !== 'near' && w !== 'เปิด') exclude.push(w);
  }
  if (exclude.length) hay = hay.replace(RE_NEG, ' ');

  // Longest patterns first, so "open late" is not eaten by "open".
  const flat = [];
  for (const [name, value, pats] of rules) {
    for (const p of pats) flat.push([p.length, name, value, norm(p)]);
  }
  flat.sort((a, b) => b[0] - a[0]);
  for (const [, name, value, p] of flat) {
    const [next, hit] = stripPhrase(hay, p);
    hay = next;
    if (hit) {
      (filters[name] = filters[name] || new Set()).add(value);
      phrases.push(p);
    }
  }
  const scaffold = QUESTION_SCAFFOLD.slice().sort((a, b) => b.length - a.length);
  for (const p of scaffold) hay = stripPhrase(hay, norm(p))[0];

  const out = {};
  for (const k in filters) out[k] = Array.from(filters[k]).sort();
  return { filters: out, exclude, phrases,
           residual: hay.replace(/\s+/g, ' ').trim() };
}

// ---- layer 3: thesaurus ----------------------------------------------------
// Synonymy across languages, and nothing else. Spelling variants are pointedly
// absent — those are the phonetic key's job — which keeps this table small
// enough that a wrong entry is visible rather than buried.

class Thesaurus {
  constructor(groups) {
    this.groups = [];
    this.index = new Map();
    this.looseIndex = null;
    for (const g of groups || []) {
      const members = Array.from(new Set((g || []).map(norm).filter(Boolean))).sort();
      if (members.length < 2) continue;
      const gid = this.groups.length;
      this.groups.push(members);
      for (const mem of members) {
        if (!this.index.has(mem)) this.index.set(mem, new Set());
        this.index.get(mem).add(gid);
      }
    }
  }

  // Loose key -> groups, built on the first loose lookup rather than for
  // every member up front (see Segmenter._looseIndex).
  _looseIdx() {
    if (this.looseIndex) return this.looseIndex;
    this.looseIndex = new Map();
    this.groups.forEach((members, gid) => {
      for (const mem of members) {
        const lk = loose(mem);
        if (!lk) continue;
        if (!this.looseIndex.has(lk)) this.looseIndex.set(lk, new Set());
        this.looseIndex.get(lk).add(gid);
      }
    });
    return this.looseIndex;
  }

  // The key must be long enough to be about a word rather than a syllable:
  // "with" reduces to `wit`, which collided with a real group and handed a
  // stopword seventeen synonyms.
  expand(tok, useLoose) {
    tok = norm(tok);
    if (!tok) return [];
    let gids = new Set(this.index.get(tok) || []);
    if ((useLoose !== false) && !gids.size) {
      const lk = loose(tok);
      if (lk.length >= 4) gids = new Set(this._looseIdx().get(lk) || []);
    }
    const out = [tok], seen = new Set([tok]);
    for (const gid of Array.from(gids).sort((a, b) => a - b)) {
      for (const mem of this.groups[gid]) {
        if (!seen.has(mem)) { seen.add(mem); out.push(mem); }
      }
    }
    return out;
  }
}

// ---- putting it together ---------------------------------------------------

const TIER_EXACT = 'exact', TIER_THESAURUS = 'thesaurus',
      TIER_LOOSE = 'loose', TIER_PARTIAL = 'partial';
const TIER_WEIGHT = { exact: 1.0, thesaurus: 0.8, loose: 0.55, partial: 0.3 };
const TIER_ORDER = [TIER_EXACT, TIER_THESAURUS, TIER_LOOSE, TIER_PARTIAL];

class SearchCore {
  constructor(thesaurus, segdict, rules) {
    this.thes = thesaurus instanceof Thesaurus ? thesaurus
      : new Thesaurus(thesaurus || []);
    this.seg = segdict instanceof Segmenter ? segdict
      : new Segmenter(segdict || []);
    this.rules = rules || INTENT_RULES;
    // A corpus of 12,353 listings holds only ~15,000 distinct words, and both
    // expensive operations — the phonetic key and Thai segmentation — depend on
    // nothing but the word. Memoised per word rather than per occurrence, which
    // is what makes building this index in a phone browser reasonable at all.
    this.looseMemo = new Map();
    this.segMemo = new Map();
  }

  _loose(w) {
    let v = this.looseMemo.get(w);
    if (v === undefined) { v = loose(w); this.looseMemo.set(w, v); }
    return v;
  }

  _split(w) {
    let v = this.segMemo.get(w);
    if (v === undefined) { v = this.seg.split(w); this.segMemo.set(w, v); }
    return v;
  }

  // `oracle` is anything with .nearest(chunk) — pass an index when you have one,
  // since the corpus knows words the language dictionary does not.
  analyze(q, oracle) {
    oracle = oracle || this.seg;
    const intent = parseIntent(q, this.rules);
    // A CONSTRAINT IS ONLY A CONSTRAINT WHEN THERE IS SOMETHING TO CONSTRAIN.
    // parseIntent eats the phrase it recognises and leaves the rest as
    // `residual`, which is right for "cafe with parking" and leaves NOTHING
    // for "parking". Every constraint word typed on its own — parking, wifi,
    // open now, wheelchair, ที่จอดรถ — analyzed to zero terms and so found
    // zero rows, in a directory holding thousands of places that answer each
    // of them. It read as "we have none of that".
    //
    // Found 2026-09-06 chasing a reader's report about parking, which is the
    // one where it did the most damage: he typed "parking for motorcycle near
    // taphae gate", the engine searched for *motorcycle + near + taphae +
    // gate*, and the first word of his question never reached the index.
    //
    // So when eating the phrase would leave nothing, the words are put back
    // and matched as words. The filters stay set either way. Twin of the same
    // block in searchcore.py — parity.py fails the build if they drift.
    let text = intent.residual;
    if (!text.trim()) text = intent.phrases.join(' ') || q;
    const notes = new Set();
    let rawTokens = [];
    for (const chunk of text.split(/\s+/)) {
      if (!chunk) continue;
      if (hasThai(chunk)) {
        // A word the THESAURUS knows is never split. ร้านยา is a pharmacy, and
        // it is also ร้าน + ยา — two perfectly good words the dictionary is
        // delighted to find — so the segmenter took the Thai for "chemist" apart
        // into "shop" and "medicine", neither of which expands to anything, and
        // a search for ร้านยา returned none of the directory's thirty-five
        // pharmacies. The thesaurus lists terms that mean something WHOLE.
        if (this.thes.index.has(norm(chunk))) { rawTokens.push(norm(chunk)); continue; }
        // Repair before splitting: a name one letter wrong is still a name, and
        // splitting it destroys the only thing that could have matched it.
        const mend = oracle.nearest ? oracle.nearest(chunk) : null;
        if (mend) { notes.add('mended'); rawTokens.push(mend); continue; }
        const pieces = this.seg.split(chunk);
        if (pieces.length > 1) notes.add('segmented');
        rawTokens = rawTokens.concat(pieces);
      } else rawTokens.push(chunk);
    }
    const kept = rawTokens.filter(t => !STOPWORDS.has(t));
    if (kept.length && kept.length !== rawTokens.length) {
      rawTokens = kept; notes.add('stopwords');
    }
    const terms = [];
    let i = 0;
    while (i < rawTokens.length) {
      // A two-word phrase can itself be a thesaurus entry ("khao soi", "love
      // charm"), so pairs get a look-up before the words are taken separately.
      let pair = null;
      if (i + 1 < rawTokens.length) {
        const cand = rawTokens[i] + ' ' + rawTokens[i + 1];
        if (this.thes.index.has(cand)) pair = cand;
      }
      const raw = pair || rawTokens[i];
      const variants = this.thes.expand(raw);
      if (variants.length > 1) notes.add('widened');
      terms.push({
        raw,
        variants,
        looseVariants: Array.from(new Set(variants.map(loose).filter(Boolean))).sort(),
        // The key for what the reader actually TYPED, kept apart from its
        // synonyms' keys: only this one is worth hunting misspellings for, since
        // the synonyms come from a table and are spelled right by construction.
        looseOwn: loose(raw),
      });
      i += pair ? 2 : 1;
    }
    if (Object.keys(intent.filters).length) notes.add('intent');
    return { query: q, terms, intent, notes: Array.from(notes).sort() };
  }

  termTier(term, hay, words, hayLoose, wordsLoose) {
    const first = term.variants.length ? term.variants[0] : '';
    if (first && (hay.indexOf(first) !== -1 || words.indexOf(first) !== -1)) {
      return TIER_EXACT;
    }
    for (let k = 1; k < term.variants.length; k++) {
      const v = term.variants[k];
      if (v && (hay.indexOf(v) !== -1 || words.indexOf(v) !== -1)) {
        return TIER_THESAURUS;
      }
    }
    for (const lv of term.looseVariants) {
      if (!lv) continue;
      if (hayLoose.indexOf(lv) !== -1 || wordsLoose.indexOf(lv) !== -1) {
        return TIER_LOOSE;
      }
      const cap = slack(lv);
      if (cap) {
        for (const w of wordsLoose) {
          if (w && Math.abs(w.length - lv.length) <= cap
              && edits(lv, w, cap) <= cap) return TIER_LOOSE;
        }
      }
    }
    // A prefix is what a reader still typing has given you.
    if (first && first.length >= 3) {
      for (const w of words) if (w.indexOf(first) === 0) return TIER_PARTIAL;
      const fl = loose(first);
      if (fl.length >= 3) {
        for (const w of wordsLoose) if (w.indexOf(fl) === 0) return TIER_PARTIAL;
      }
    }
    return null;
  }

  prepare(text) {
    const h = norm(text);
    const base = h.split(/\s+/).filter(Boolean);
    // The DOCUMENT is segmented too, not just the query, and that is why Thai
    // misspellings work at all: โรงพยาบาลราชเวช is one 15-character token, so
    // ราชเวส — six characters, one letter wrong — failed the length guard and
    // matched nothing. Pieces are added ALONGSIDE the whole word so an exact
    // match on the full name still out-ranks a match on one piece of it.
    let words = base;
    const pieces = [];
    for (const w of base) {
      if (hasThai(w) && w.length > 4) {
        const parts = this._split(w);
        if (parts.length > 1) for (const p of parts) pieces.push(p);
      }
    }
    if (pieces.length) words = base.concat(pieces);
    const hl = words.map(w => this._loose(w)).join(' ');
    const wl = hl.split(/\s+/).filter(Boolean);
    return [h, words, hl, wl];
  }

  // Prepared once when the index loads, never per keystroke: these pages are
  // read on old phones on satellite connections, and the document side is by far
  // the expensive half.
  prepareDoc(fields) {
    const out = {};
    for (const name in fields) {
      out[name] = { prep: this.prepare(fields[name][0]), weight: fields[name][1] };
    }
    return out;
  }

  scoreDoc(an, preparedDoc) {
    if (!an.terms.length) return null;
    let total = 0, matched = 0, worst = TIER_EXACT;
    for (const term of an.terms) {
      let bestTier = null, bestWeight = 0;
      for (const name in preparedDoc) {
        const { prep, weight } = preparedDoc[name];
        const tier = this.termTier(term, prep[0], prep[1], prep[2], prep[3]);
        if (tier === null) continue;
        const value = TIER_WEIGHT[tier] * weight;
        if (value > bestWeight) { bestTier = tier; bestWeight = value; }
      }
      if (bestTier === null) continue;
      matched++;
      total += bestWeight;
      if (TIER_ORDER.indexOf(bestTier) > TIER_ORDER.indexOf(worst)) worst = bestTier;
    }
    if (!matched) return null;
    // Every term matching is worth far more than one term matching well — a
    // reader who typed three words meant all three.
    const coverage = matched / an.terms.length;
    if (coverage < 1) worst = TIER_PARTIAL;
    return { score: total * coverage * coverage, tier: worst, matched,
             terms: an.terms.length, coverage };
  }

  score(an, fields) { return this.scoreDoc(an, this.prepareDoc(fields)); }
}

// ---- an index, for corpora too big to compare one document at a time -------
// Fuzzy matching is a question about the VOCABULARY, not about the documents.
// There are ~14,000 distinct words in this directory and two or three in a
// query; resolve the query against the vocabulary once and every document
// holding a surviving word is a dictionary look-up away. The first version
// compared each term against every word of every document and took six seconds
// for ร้านกาแฟนิมมาน, which is not a search anybody waits for — least of all on
// the connections these pages are read on.

class Index {
  constructor(core) {
    this.core = core;
    this.fields = new Map();
    this.postings = new Map();       // field -> Map(word -> Set(docid))
    this.loosePostings = new Map();  // field -> Map(looseWord -> Set(docid))
    this.docs = [];
  }

  add(doc, fields) {
    const did = this.docs.length;
    this.docs.push(doc);
    for (const name in fields) {
      const [text, weight] = fields[name];
      if (!this.fields.has(name)) this.fields.set(name, weight);
      if (!this.postings.has(name)) this.postings.set(name, new Map());
      if (!this.loosePostings.has(name)) this.loosePostings.set(name, new Map());
      const prep = this.core.prepare(text);
      const post = this.postings.get(name), lpost = this.loosePostings.get(name);
      for (const w of new Set(prep[1])) {
        if (!post.has(w)) post.set(w, new Set());
        post.get(w).add(did);
      }
      for (const w of new Set(prep[3])) {
        if (!lpost.has(w)) lpost.set(w, new Set());
        lpost.get(w).add(did);
      }
    }
    return did;
  }

  finalize() {
    // Loose keys bucketed by length: a string more than `cap` characters longer
    // or shorter cannot be `cap` edits away, so only these bands are ever walked.
    this.looseByLen = new Map();
    for (const [name, lpost] of this.loosePostings) {
      const buckets = new Map();
      for (const w of lpost.keys()) {
        if (!buckets.has(w.length)) buckets.set(w.length, []);
        buckets.get(w.length).push(w);
      }
      for (const bucket of buckets.values()) bucket.sort();
      this.looseByLen.set(name, buckets);
    }
    // A mending dictionary drawn from the corpus itself. Names are what readers
    // misspell, so only the name field contributes, and only Thai words — Latin
    // slips are already handled by the phonetic key, which does not need the
    // query kept whole to work.
    this.mend = new Map();
    this.mendByLen = new Map();
    for (const w of (this.postings.get('name') || new Map()).keys()) {
      if (!hasThai(w) || w.length < 3) continue;
      const k = this.core._loose(w);
      if (!k) continue;
      if (!this.mend.has(k)) {
        this.mend.set(k, []);
        if (!this.mendByLen.has(k.length)) this.mendByLen.set(k.length, []);
        this.mendByLen.get(k.length).push(k);
      }
      this.mend.get(k).push(w);
    }
    for (const bucket of this.mendByLen.values()) bucket.sort();
    return this;
  }

  // The corpus word a misspelled chunk was probably meant to be. Consulted
  // before segmentation, because splitting a misspelled name into two correctly
  // spelled short words destroys it.
  nearest(chunk) {
    chunk = norm(chunk);
    if (!chunk || !hasThai(chunk)) return this.core.seg.nearest(chunk);
    if ((this.postings.get('name') || new Map()).has(chunk)) return null;
    const key = this.core._loose(chunk);
    if (!key) return null;
    const pick = (words) => words.slice().sort((a, b) =>
      Math.abs(a.length - chunk.length) - Math.abs(b.length - chunk.length)
      || (a < b ? -1 : a > b ? 1 : 0))[0];
    if (this.mend.has(key)) return pick(this.mend.get(key));
    const cap = slack(key);
    let best = null, bestD = cap + 1;
    if (cap) {
      for (let L = key.length - cap; L <= key.length + cap; L++) {
        for (const k of (this.mendByLen.get(L) || [])) {
          const d = edits(key, k, cap);
          if (d < bestD) { best = k; bestD = d; if (d === 1) break; }
        }
        if (bestD === 1) break;
      }
    }
    if (best !== null) return pick(this.mend.get(best));
    return this.core.seg.nearest(chunk);
  }

  // {docid: tier} for one term in one field — each document's OWN tier.
  // Returning one tier for the whole set was wrong: it stopped at the cheapest
  // tier that produced anything, so "coffe" reached `coffee` by key and stopped,
  // and Café de Nimman never appeared for "nimman coffe" while thirteen cafés
  // merely ON Nimman road ranked above it.
  _resolve(term, name, extraSlack) {
    const post = this.postings.get(name) || new Map();
    const lpost = this.loosePostings.get(name) || new Map();
    const tiers = new Map();
    const mark = (ids, tier) => {
      const rank = TIER_ORDER.indexOf(tier);
      for (const did of ids) {
        const prev = tiers.get(did);
        if (prev === undefined || rank < TIER_ORDER.indexOf(prev)) {
          tiers.set(did, tier);
        }
      }
    };
    const first = term.variants.length ? term.variants[0] : '';
    if (first && post.has(first)) mark(post.get(first), TIER_EXACT);
    for (let k = 1; k < term.variants.length; k++) {
      const v = term.variants[k];
      if (post.has(v)) mark(post.get(v), TIER_THESAURUS);
    }
    for (const lv of term.looseVariants) {
      if (lpost.has(lv)) mark(lpost.get(lv), TIER_LOOSE);
    }
    // UNGATED, and every attempt to gate it was a bug — first skipping it when
    // any cheaper tier matched, then when the term matched exactly, which one
    // listing literally named "Coffe" was enough to trigger for everybody. This
    // tier ranks below exact and thesaurus by construction, so scanning can only
    // ADD candidates underneath the good ones.
    const lv = term.looseOwn;
    const cap = lv ? slack(lv) + (extraSlack || 0) : 0;
    if (cap) {
      const byLen = this.looseByLen.get(name) || new Map();
      for (let L = lv.length - cap; L <= lv.length + cap; L++) {
        for (const w of (byLen.get(L) || [])) {
          if (edits(lv, w, cap) <= cap) mark(lpost.get(w), TIER_LOOSE);
        }
      }
    }
    if (!tiers.size && first && first.length >= 3) {
      for (const [w, ids] of post) {
        if (w.indexOf(first) === 0 || w.indexOf(first) !== -1) mark(ids, TIER_PARTIAL);
      }
    }
    return tiers;
  }

  search(an, limit) {
    if (!an.terms.length) return [];
    const resolveAll = (term, extra) => {
      const best = new Map();
      for (const [name, weight] of this.fields) {
        for (const [did, tier] of this._resolve(term, name, extra)) {
          const value = TIER_WEIGHT[tier] * weight;
          const prev = best.get(did);
          if (prev === undefined || value > prev[0]) best.set(did, [value, tier]);
        }
      }
      return best;
    };
    const resolved = an.terms.map(t => resolveAll(t, 0));

    // CONTEXTUAL SLACK. A three-character Thai token earns no edit slack,
    // because one edit turns ยา into ยาย — and that rule, right on its own, kept
    // ราชเวส from reaching ราชเวช: the corpus splits the hospital's name into
    // โรงพยาบาล + ราช + เวช, so the query's เวส had three characters and no
    // licence to be wrong. But its neighbour ราช matched exactly, and a term
    // beside an exact match is not a wild guess. So a term that found nothing is
    // retried with one more edit — and ONLY when some other term landed exactly.
    let anchored = false;
    for (const r of resolved) {
      for (const [, tier] of r) {
        if (tier === TIER_EXACT || tier === TIER_THESAURUS) { anchored = true; break; }
      }
      if (anchored) break;
    }
    if (anchored) {
      for (let i = 0; i < an.terms.length; i++) {
        if (!resolved[i].size) resolved[i] = resolveAll(an.terms[i], 1);
      }
    }

    const acc = new Map();
    for (const best of resolved) {
      for (const [did, [value, tier]] of best) {
        let row = acc.get(did);
        if (!row) { row = [0, TIER_EXACT, 0]; acc.set(did, row); }
        row[0] += value;
        row[2] += 1;
        if (TIER_ORDER.indexOf(tier) > TIER_ORDER.indexOf(row[1])) row[1] = tier;
      }
    }
    const n = an.terms.length;
    const out = [];
    for (const [did, [total, worst, matched]] of acc) {
      const coverage = matched / n;
      out.push({
        doc: this.docs[did],
        score: total * coverage * coverage,
        tier: coverage < 1 ? TIER_PARTIAL : worst,
        coverage,
      });
    }
    out.sort((a, b) => b.score - a.score);
    // LOOSEN BY STEPS, never all at once. A reader who typed two words meant
    // both, so documents matching all the terms are the answer and documents
    // matching some are a fallback, offered only when there is no answer.
    // Mixing them also made the count lie: ร้านกาแฟนิมมาน reported 2,247 finds —
    // every café in the directory plus everything else on that road.
    const whole = out.filter(r => r.coverage >= 1);
    const kept = whole.length ? whole : out;
    return limit ? kept.slice(0, limit) : kept;
  }
}

const SEARCHCORE = {
  norm, loose, edits, slack, hasThai, Segmenter, Thesaurus, SearchCore,
  Index, parseIntent, INTENT_RULES, QUESTION_SCAFFOLD, STOPWORDS,
  TIER_EXACT, TIER_THESAURUS, TIER_LOOSE, TIER_PARTIAL, TIER_ORDER, TIER_WEIGHT,
};

if (typeof globalThis !== 'undefined') globalThis.SEARCHCORE = SEARCHCORE;

export default SEARCHCORE;
export { norm, loose, edits, slack, hasThai, Segmenter, Thesaurus,
         SearchCore, Index, parseIntent, INTENT_RULES };
