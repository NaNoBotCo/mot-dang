/* What a reader asks for besides the thing itself (Nan, 2026-10-04: "all of
 * them, wire up the 13 too").
 *
 * fleetsearch.js already lifts near me, open now, a price and buy. This file
 * holds the rest, in three kinds:
 *
 *   prefer  the words leave the match and rows that carry the thing rank
 *           first: a facet recorded on the place (data/facets.json keys, as
 *           the crawler copies them into pages.rich), a schedule open at the
 *           asked-for time (keys.sk), a has-bit, the words themselves. The
 *           rest of the answer stays, after them. "halal khao soi" is khao
 *           soi, the halal ones first.
 *   shelf   the word stays in the match, put in the form the thesaurus links
 *           across languages: "fix" and "broken" → repair (ซ่อม), "who buys"
 *           → รับซื้อ.
 *   lead    a line with a link above the results: the emergency numbers,
 *           the weather pages, the listings board, the route planner.
 *
 * The first thirteen take their words from searchcore's INTENT_RULES, the
 * lists the place search reads, so the two boxes hear the same words. */
import { INTENT_RULES } from "./searchcore.js";

const rule = (name, value) => {
  const r = INTENT_RULES.find(([n, v]) => n === name && v === value);
  return r ? r[2].slice() : [];
};

/* Minutes of the week (Monday 00:00 = 0) a schedule must be open at least one
 * of, for each time a reader can ask about. */
const DAY = 1440;
const at = (days, hours) => days.flatMap((d) => hours.map((h) => d * DAY + Math.round(h * 60)));
const ALL = [0, 1, 2, 3, 4, 5, 6];
export const WHEN = {
  late: at(ALL, [22.5, 23.5]),
  early: at(ALL, [6.5]),
  sunday: at([6], [8, 11, 14, 17, 20]),
  weekend: at([5, 6], [8, 11, 14, 17, 20]),
};

export const INTENTS = [
  /* ---- leads first: their phrases hold words the others would take */
  { id: "urgent", kind: "lead", keep: true,
    pats: ["emergency", "ambulance", "urgent help", "help me", "sos", "call an ambulance",
           "ฉุกเฉิน", "เหตุฉุกเฉิน", "ช่วยด้วย", "รถพยาบาล", "เจ็บป่วยฉุกเฉิน", "เรียกรถพยาบาล"] },
  { id: "route", kind: "lead",
    pats: ["how to get to", "how do i get to", "how can i get to", "directions to", "route to",
           "way to", "get to", "ไปยังไง", "ไปทางไหน", "ไปอย่างไร"],
    front: ["เส้นทางไป", "ทางไป", "วิธีไป"] },
  { id: "weather", kind: "lead", keep: true,
    pats: ["weather", "forecast", "will it rain", "is it raining", "rain today", "raining",
           "air quality", "aqi", "pm2.5", "pm 2.5", "pm25", "haze", "smoke today", "smoky",
           "flood", "flooding", "floods",
           "สภาพอากาศ", "พยากรณ์อากาศ", "อากาศวันนี้", "ฝนตกไหม", "ฝนจะตกไหม", "ฝนตก",
           "ฝุ่น", "ฝุ่นวันนี้", "หมอกควัน", "ค่าฝุ่น", "น้ำท่วม"] },
  { id: "rent", kind: "lead", keep: true,
    pats: [["for rent", "rent"], ["to rent", "rent"], ["for lease", "rent"], ["monthly rent", "rent"],
           "rental", "rentals", "lease", "ให้เช่า", "เช่ารายเดือน", "รายเดือน", "เซ้ง"] },

  /* ---- shelves: the word stays, in the form the thesaurus knows */
  { id: "fix", kind: "shelf", shelf: "repair",
    pats: ["fix", "fixing", "broken", "repairs", "repairing", "mend", "not working",
           "เสีย", "พัง", "ซ่อมแซม"] },
  { id: "sell", kind: "shelf", shelf: "รับซื้อ",
    pats: ["who buys", "where to sell", "where can i sell", "sell my", "selling my", "cash for",
           "we buy", "buyer of", "อยากขาย", "จะขาย", "ขายต่อ"] },

  /* ---- the thirteen searchcore already lists */
  { id: "late", kind: "prefer", pats: rule("open", "late"), when: "late", fac: ["open24", "latenight", "openlate"],
    th: "เปิดดึก — ที่เปิดดึกขึ้นก่อน", en: "open late — places open late first" },
  { id: "early", kind: "prefer", pats: rule("open", "early"), when: "early",
    th: "เปิดเช้า — ที่เปิดเช้าขึ้นก่อน", en: "open early — places open early first" },
  { id: "sunday", kind: "prefer", pats: rule("open", "sunday"), when: "sunday", words: ["sunday", "วันอาทิตย์"],
    th: "วันอาทิตย์ — ที่เปิดวันอาทิตย์ขึ้นก่อน", en: "Sunday — places open on Sunday first" },
  { id: "weekend", kind: "prefer", pats: rule("open", "weekend"), when: "weekend", words: ["weekend", "เสาร์อาทิตย์"],
    th: "สุดสัปดาห์ — ที่เปิดเสาร์-อาทิตย์ขึ้นก่อน", en: "weekend — places open at the weekend first" },
  { id: "best", kind: "prefer", pats: rule("rank", "best"), score: true,
    th: "ดีที่สุด — ที่มีข้อมูลมากขึ้นก่อน", en: "best — the fullest listings first" },
  { id: "vegetarian", kind: "prefer", pats: rule("diet", "vegetarian"), fac: ["vegoption"],
    words: ["vegetarian", "มังสวิรัติ", "vegan", "เจ"],
    th: "มังสวิรัติ — ที่ระบุว่ามีเมนูมังสวิรัติขึ้นก่อน", en: "vegetarian — places that say vegetarian first" },
  { id: "vegan", kind: "prefer", pats: rule("diet", "vegan").concat(["plant based"]), fac: ["vegoption"],
    words: ["vegan", "วีแกน", "เจ", "อาหารเจ", "plant based"],
    th: "เจ · วีแกน — ที่ระบุว่าเจหรือวีแกนขึ้นก่อน", en: "vegan — places that say vegan first" },
  { id: "halal", kind: "prefer", pats: rule("diet", "halal"), fac: ["halal"],
    words: ["halal", "ฮาลาล", "muslim", "มุสลิม"],
    th: "ฮาลาล — ที่ระบุว่าฮาลาลขึ้นก่อน", en: "halal — places that say halal first" },
  { id: "wheelchair", kind: "prefer", pats: rule("access", "wheelchair"), fac: ["wheelchair"],
    words: ["wheelchair", "step free", "รถเข็น", "วีลแชร์", "ทางลาด"],
    th: "รถเข็น — ที่บันทึกว่าเข้าได้ไม่มีขั้นขึ้นก่อน", en: "wheelchair — places recorded step-free first" },
  { id: "parking", kind: "prefer", pats: rule("access", "parking"), fac: ["parking"],
    words: ["parking", "car park", "ที่จอดรถ", "ลานจอดรถ"],
    th: "ที่จอดรถ — ที่มีที่จอดขึ้นก่อน", en: "parking — places with parking first" },
  { id: "english", kind: "prefer", pats: rule("access", "english"), fac: ["english", "engmedium", "epmep"],
    words: ["english spoken", "speaks english", "พูดภาษาอังกฤษ", "พูดอังกฤษ", "คุยอังกฤษได้"],
    th: "พูดอังกฤษ — ที่ระบุว่าพูดอังกฤษได้ขึ้นก่อน", en: "English spoken — places that say so first" },
  { id: "kids", kind: "prefer", pats: rule("kids", "yes"), fac: ["kids"],
    words: ["kids", "children", "family", "เด็ก", "ครอบครัว"],
    th: "พาเด็ก — ที่รับเด็กขึ้นก่อน", en: "kids — places for children first" },
  { id: "pets", kind: "prefer", pats: rule("pets", "yes"), fac: ["pets"],
    words: ["pet friendly", "dog friendly", "pets allowed", "สัตว์เลี้ยง"],
    th: "สัตว์เลี้ยง — ที่ให้พาสัตว์เลี้ยงขึ้นก่อน", en: "pets — places that take pets first" },
  { id: "wifi", kind: "prefer", pats: rule("wifi", "yes"), fac: ["wifi"],
    words: ["wifi", "wi fi", "ไวไฟ"],
    th: "ไวไฟ — ที่มีไวไฟขึ้นก่อน", en: "wifi — places with wifi first" },
  { id: "aircon", kind: "prefer", pats: rule("aircon", "yes"), fac: ["aircon"],
    words: ["air conditioned", "aircon", "แอร์เย็น", "ห้องแอร์", "มีแอร์"],
    th: "มีแอร์ — ที่มีแอร์ขึ้นก่อน", en: "air-con — air-conditioned places first" },
  { id: "delivery", kind: "prefer", pats: rule("delivery", "yes"), fac: ["delivery"],
    words: ["delivery", "เดลิเวอรี", "ส่งถึงบ้าน", "ส่งถึงที่"],
    th: "ส่งถึงที่ — ที่มีส่งขึ้นก่อน", en: "delivery — places that deliver first" },
  { id: "walkin", kind: "prefer", pats: rule("appointment", "walkin"), fac: ["walkin", "sameday", "walkintable"],
    words: ["walk in", "walk ins", "วอล์กอิน", "ไม่ต้องจอง"],
    th: "เดินเข้าได้ — ที่ไม่ต้องนัดขึ้นก่อน", en: "walk-in — places that take walk-ins first" },
  { id: "bigsize", kind: "prefer", pats: rule("size", "big"), fac: ["bigsizes"],
    words: ["big size", "plus size", "ไซส์ใหญ่", "ไซซ์ใหญ่", "บิ๊กไซส์"],
    th: "ไซส์ใหญ่ — ที่ระบุไซส์ใหญ่ขึ้นก่อน", en: "big sizes — places that say so first" },

  /* ---- the new ones that rank rather than lead */
  { id: "book", kind: "prefer", fac: ["booking", "sameday", "privateclass"],
    pats: ["book a table", "book a", "to book", "booking", "bookings", "reserve", "reservation",
           "reservations", "จอง", "จองโต๊ะ", "จองตั๋ว", "สำรองที่นั่ง"],
    front: ["จองโต๊ะ", "จอง"],
    words: ["booking", "reservation", "tickets", "จอง", "ตั๋ว"],
    th: "จอง — ที่รับจองขึ้นก่อน", en: "booking — places that take bookings first" },
  { id: "price", kind: "prefer", fac: ["priceboard"],
    pats: ["how much", "how much is", "how much does", "price of", "prices", "price list", "price",
           "cost", "costs", "fee", "fees", "rates", "entrance fee",
           "เท่าไหร่", "เท่าไร", "ราคาเท่าไหร่", "ค่าเข้า", "ราคา"],
    words: ["price", "baht", "ราคา", "บาท"],
    th: "ราคา — หน้าที่บอกราคาขึ้นก่อน", en: "price — pages that give a price first" },
  { id: "howto", kind: "prefer", page: true,
    pats: ["how to", "how do", "how does", "what is", "what are", "why is", "why do", "guide to", "explain",
           "ทำยังไง", "ทำอย่างไร", "คืออะไร", "ยังไง"],
    front: ["วิธีการ", "วิธี", "อะไรคือ", "ทำไม"],
    th: "วิธี — หน้าอธิบายขึ้นก่อน", en: "how to — explainers and guides first" },
  { id: "free", kind: "prefer", fac: ["toiletfree", "pickupfree"],
    pats: ["free", "for free", "free entry", "free admission", "no charge", "no fee",
           "ฟรี", "เข้าฟรี", "ไม่เสียเงิน", "ไม่มีค่าใช้จ่าย", "ไม่เสียค่าเข้า"],
    words: ["free", "ฟรี"],
    unless: /(gluten|sugar|duty|smoke|alcohol|dairy|lactose|cruelty|tax|nut|hands)[ -]free/i,
    th: "ฟรี — ที่บอกว่าฟรีขึ้นก่อน", en: "free — places that say free first" },
  { id: "learn", kind: "prefer", fac: ["privateclass", "eveningclass", "multiday", "engmedium"],
    pats: ["learn", "learning", "learn to", "learn how to", "เรียน", "อยากเรียน"],
    front: ["อยากเรียน", "เรียน"],
    words: ["class", "course", "lesson", "school", "workshop", "เรียน", "คอร์ส", "สอน", "คลาส", "โรงเรียน"],
    th: "เรียน — ที่สอนขึ้นก่อน", en: "learn — classes and courses first" },
  { id: "work", kind: "lead", keep: true,
    pats: ["jobs", "job", "hiring", "vacancy", "vacancies", "employment",
           "รับสมัครงาน", "รับสมัคร", "หางาน", "สมัครงาน", "ตำแหน่งว่าง"] },
  { id: "contact", kind: "prefer", has: "contact",
    unless: /contact lens/i,
    pats: ["phone number", "phone no", "telephone number", "contact number", "contact", "line id",
           "whatsapp", "เบอร์โทร", "เบอร์", "ติดต่อ", "ไลน์", "ช่องทางติดต่อ"],
    th: "ติดต่อ — ที่มีช่องทางติดต่อขึ้นก่อน", en: "contact — places with a way to reach them first" },
];

/* Lines and links for the lead kinds. Numbers as Safety First prints them
 * (motdang.net/sites/safety/, read 2026-10-04). */
const SAFETY = "/sites/safety/";
export const LEADS = {
  urgent: {
    th: "ฉุกเฉิน", en: "emergency",
    links: [["tel:1669", "1669 รถพยาบาล · ambulance"], ["tel:191", "191 ตำรวจ · police"],
            ["tel:199", "199 ดับเพลิง · fire"], ["tel:1155", "1155 ตำรวจท่องเที่ยว · police, English spoken"],
            ["tel:1784", "1784 สาธารณภัย · disaster"], [SAFETY, "ความปลอดภัย · Safety First"]],
  },
  weather: {
    th: "อากาศ", en: "weather",
    links: [["/", "ฟ้าและพยากรณ์ · sky and forecast"],
            ["https://nanobotco.github.io/rain-chiang-mai/", "ฝนตอนนี้ · rain radar"],
            ["/sites/smoky-season/", "ฝุ่นและควัน · smoke and haze"],
            [SAFETY + "#river", "ระดับน้ำปิง · Ping river level"]],
  },
  rent: {
    th: "เช่า", en: "rent",
    links: [["/listings/", "ประกาศเช่า-ขาย · listings"]],
  },
  work: {
    th: "งาน", en: "work",
    links: [["/home-help/", "แม่บ้านและช่างลงชื่อ · home help board"]],
  },
};
/* rent's listings line shows when the reader named a home, or nothing else. */
const HOME_WORDS = /(^|\s)(house|home|condo|condominium|room|rooms|apartment|flat|studio|villa|land|townhouse|shophouse|office|บ้าน|คอนโด|ห้อง|ห้องพัก|อพาร์ทเมนท์|อพาร์ตเมนต์|ที่ดิน|ทาวน์เฮาส์|ตึกแถว|อาคาร|หอพัก)(\s|$)/;

const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const THAI = /[฀-๿]/;

/* Lifts every intent above from a padded query (" ... "). Returns the query
 * left over, what was heard, and the words taken out (put back by the caller
 * when nothing else is left). A Thai pattern counts standing alone or at the
 * end of a run, the rule fleetsearch.js uses for its own four; a `front`
 * pattern at the start of one (วิธีทำข้าวซอย). A pattern given as [words, form]
 * is rewritten to that form; a `keep` intent is heard and left in place; a
 * shelf word is put back in its thesaurus form. */
export function liftMore(s) {
  const heard = [];
  const removed = [];
  const hear = (it, p) => { if (!heard.find((h) => h.id === it.id)) heard.push({ id: it.id, said: p }); };
  const take = (p, rep) => {
    const re = THAI.test(p)
      ? new RegExp(`${reEsc(p)}(?=[^\\u0e00-\\u0e7f]|$)`)
      : new RegExp(`(?<=\\s)${reEsc(p)}(?=\\s)`, "i");
    if (!re.test(s)) return false;
    if (rep !== p) s = s.replace(re, ` ${rep} `);
    return true;
  };
  /* Thai puts the route around the place: ไปวัดเจดีย์หลวงยังไง. Read before
   * the loop, or how-to would take the ยังไง. */
  const thRoute = /(^|\s)ไป([฀-๿]+?)(ยังไง|อย่างไร|ทางไหน)(?=\s|$)/;
  if (thRoute.test(s)) {
    s = s.replace(thRoute, "$1$2");
    hear(INTENTS.find((x) => x.id === "route"), "ไป…ยังไง");
  }
  for (const it of INTENTS) {
    if (it.unless && it.unless.test(s)) continue;
    const pats = (it.pats || []).map((p) => (Array.isArray(p) ? p : [p, null]))
      .sort((a, b) => b[0].length - a[0].length);
    for (const [p, form] of pats) {
      const rep = form || (it.keep ? p : it.kind === "shelf" ? it.shelf : "");
      if (take(p, rep)) {
        hear(it, p);
        if (!rep) removed.push(p);
      }
    }
    for (const p of it.front || []) {
      const re = new RegExp(`(^|\\s)${reEsc(p)}(?=[\\u0e00-\\u0e7f])`);
      if (!re.test(s)) continue;
      s = s.replace(re, "$1");
      hear(it, p);
      removed.push(p);
    }
  }
  return { s, heard, removed };
}

/* What rent's lead needs to know about the words left. */
export const namesHome = (q) => HOME_WORDS.test(" " + q + " ");

/* The prefer groups for what was heard: each is one multiplier in the rank
 * and one key in the nearest order. `phrase` and `seg` are fleetsearch's, so
 * a Thai word is split the way the index split it; `scheds` is the lamp
 * schedules (id → week intervals), `openAt` the test that reads them. */
export function preferOf(heard, { phrase, seg, scheds, openAt }) {
  const out = [];
  for (const h of heard) {
    const it = INTENTS.find((x) => x.id === h.id);
    if (!it || it.kind !== "prefer") continue;
    const g = { id: it.id, fac: (it.fac || []).slice(), has: it.has || "", page: !!it.page, score: !!it.score, sk: [] };
    const words = Array.from(new Set([h.said].concat(it.words || []).filter((w) => w && !/…/.test(w))));
    const ph = words.map((w) => phrase(w, seg, false)).filter(Boolean);
    g.match = ph.length ? ph.join(" OR ") : "";
    if (it.when && scheds) {
      const mins = WHEN[it.when] || [];
      for (const [k, iv] of scheds) if (mins.some((m) => openAt(iv, m))) g.sk.push(k);
    }
    out.push(g);
  }
  return out;
}

/* One line per intent heard: what the box did with it. A prefer line only
 * while the order is best match or nearest, the two orders it moves. */
export function saidOf(heard, ranked) {
  const out = [];
  for (const h of heard) {
    const it = INTENTS.find((x) => x.id === h.id);
    if (!it) continue;
    if (it.th) { if (ranked !== false) out.push(`${it.th} · ${it.en}`); }
    else if (it.kind === "shelf") out.push(it.id === "fix" ? "ซ่อม · repair" : "รับซื้อ · who buys");
  }
  return out;
}

/* The lead lines, as HTML. `top` is the first place result (for the route
 * planner), `q` the words left, `esc` fleetsearch's escaper. */
export function leadHtml(heard, { top, q, esc }) {
  const out = [];
  const line = (lead, extra) => {
    const links = lead.links.concat(extra || [])
      .map(([u, t]) => `<a href="${esc(u)}">${esc(t)}</a>`).join(" · ");
    out.push(`<p class="note lead">${esc(lead.th)} · ${esc(lead.en)} — ${links}</p>`);
  };
  for (const h of heard) {
    if (h.id === "rent" && (!q || namesHome(q))) line(LEADS.rent);
    else if (h.id === "work") line(LEADS.work);
    else if (LEADS[h.id] && h.id !== "rent") line(LEADS[h.id]);
    else if (h.id === "route") {
      const m = top && /^https:\/\/motdang\.net\/(cm|cr)\/p\/([^/]+)\.html$/.exec(top.url || "");
      out.push(m
        ? `<p class="note lead">เส้นทาง · route — <a href="/plan.html?stops=${esc(encodeURIComponent(m[1] + ":" + m[2]))}&amp;go=1">นำทางไป · Guide me to ${esc(String(top.title || "").split(/ · | — /)[0])}</a></p>`
        : `<p class="note lead">เส้นทาง · route — <a href="/plan.html">วางแผนเส้นทาง · plan a route</a></p>`);
    }
  }
  return out.join("");
}

/* The lead links as data, for ?fmt=json. */
export function leadJson(heard, { top, q, origin }) {
  const abs = (u) => (/^https?:|^tel:/.test(u) ? u : origin + u);
  const out = [];
  for (const h of heard) {
    if (h.id === "rent" && q && !namesHome(q)) continue;
    if (LEADS[h.id]) out.push({ intent: h.id, links: LEADS[h.id].links.map(([u, t]) => ({ url: abs(u), label: t })) });
    else if (h.id === "route") {
      const m = top && /^https:\/\/motdang\.net\/(cm|cr)\/p\/([^/]+)\.html$/.exec(top.url || "");
      out.push({ intent: "route", links: [{ url: abs(m ? `/plan.html?stops=${encodeURIComponent(m[1] + ":" + m[2])}&go=1` : "/plan.html"),
                                            label: m ? "Guide me" : "plan a route" }] });
    }
  }
  return out;
}
