const MD_CATWORDS={"wat": "วัด-สิ่งศักดิ์สิทธิ์ · Wats & Sacred Places", "food": "ร้านอาหาร-ของกิน · Food & Eats", "massage": "นวด-สปา · Massage & Spa", "medical": "หมอ-คลินิก-โรงพยาบาล · Doctors & Hospitals", "cannabis": "กัญชา-กระท่อม · Cannabis & Kratom", "essentials": "ของจำเป็นประจำเมือง · City Essentials", "hotel": "โรงแรม-ที่พัก · Hotels & Stays", "school": "โรงเรียน-สถานศึกษา · Schools & Education", "school-intl": "โรงเรียนนานาชาติ · International Schools", "market": "ตลาด · Markets", "shopping": "ช้อปปิ้ง-ของฝาก · Shopping & Gifts", "realestate": "อสังหาฯ-คอนโด · Real Estate & Condos", "transport": "รถ-เดินทาง · Getting Around", "repair": "ช่าง-ซ่อม · Repairs & Trades", "beauty": "เสริมสวย-ทำผม · Beauty & Hair", "tattoo": "สักยันต์-รอยสัก · Tattoo & Sak Yant", "pets": "สัตว์เลี้ยง · Pets", "sport": "กีฬา-ฟิตเนส · Sport & Fitness", "muaythai": "มวยไทย · Muay Thai", "cooking": "เรียนทำอาหารไทย · Thai Cooking Classes", "chang": "ช้าง · Elephants", "home-services": "แม่บ้าน-ช่างสวน-ดูแลบ้าน · Home Services", "community": "ชมรม-สมาคม · Clubs & Community", "business": "ธุรกิจ-ค้าขาย · Doing Business", "whats-on": "หนัง-คอนเสิร์ต-อีเวนต์ · Movies, Concerts & Events", "museums-galleries": "พิพิธภัณฑ์-หอศิลป์ · Museums & Galleries", "parks": "สวน-ที่พักผ่อน · Parks & Green Space", "sights": "ที่เที่ยว-ของดี · Sights & Good Things"};
const MD_SUBWORDS={"shrine": "ศาลเจ้า-ศาลหลักเมือง Shrines & City Pillars", "spirit-house": "ศาลพระภูมิ Spirit Houses", "thai": "อาหารไทย Thai", "made-to-order": "ตามสั่ง-ผัดกะเพรา Made-to-order", "noodle": "ข้าวซอย-ก๋วยเตี๋ยว Khao Soi & Noodles", "northern": "อาหารเหนือ-ขันโตก Northern Thai & Khantoke", "international": "นานาชาติ International", "seafood": "อาหารทะเล Seafood", "vegetarian": "มังสวิรัติ-เจ Vegetarian & Vegan", "street-food": "สตรีทฟู้ด-ฟาสต์ฟู้ด Street Food & Fast Food", "bakery-dessert": "เบเกอรี่-ของหวาน Bakery & Dessert", "bar-pub": "บาร์-ผับ Bars & Pubs", "cafe": "กาแฟ-คาเฟ่ Coffee & Cafés", "riverside": "ร้านริมน้ำ Riverside", "thai-traditional": "นวดแผนไทย-แผนโบราณ Thai Traditional", "foot": "นวดเท้า-กดจุดฝ่าเท้า Foot", "oil": "นวดน้ำมัน-อโรมา Oil & Aroma", "prakhop": "ประคบสมุนไพร Herbal Compress", "chap-sen": "นวดจับเส้น Deep Sen Work", "tok-sen": "ตอกเส้น Tok Sen (Lanna)", "yam-khang": "ย่ำขาง Yam Khang (Lanna)", "ratchasamnak": "นวดราชสำนัก Royal Court Style", "office-syndrome": "นวดออฟฟิศซินโดรม Office Syndrome", "spa-body": "สปา-ขัดผิว-อบไอน้ำ Spa, Scrub & Steam", "khat-khi-khlai": "ขัดขี้ไคล-ระเบิดขี้ไคล Dead-Skin Scrub", "face": "นวดหน้า-กัวซาหน้า Facial & Face Gua Sha", "cupping": "ครอบแก้ว Cupping", "postpartum": "ทับหม้อเกลือ-อยู่ไฟ Postnatal Care", "prenatal": "นวดคนท้อง Prenatal", "blind-massage": "นวดโดยคนตาบอด Blind Massage", "ap-ob-nuat": "อาบอบนวด Ap Ob Nuat", "hospital": "โรงพยาบาล Hospitals", "clinic": "คลินิก Clinics", "doctors": "หมอเฉพาะทาง Specialists", "dentist": "หมอฟัน Dentists", "pharmacy": "ร้านขายยา Pharmacies", "health-station": "รพ.สต.-สถานีอนามัย Health stations (รพ.สต.)", "laboratory": "แล็บ-ตรวจเลือด Labs & testing", "physio": "กายภาพบำบัด Physiotherapy", "optometrist": "ร้านแว่น-วัดสายตา Eyes & optometry", "long-care": "ดูแลระยะยาว-บ้านพักคนชรา Long-term & residential care", "thai-medicine": "แพทย์แผนไทย-สมุนไพร Traditional Thai Medicine", "dispensary": "ร้านกัญชา Dispensaries", "cannabis-cafe": "คาเฟ่กัญชา Cannabis cafés", "kratom": "ร้านน้ำใบกระท่อม Kratom", "farm": "ฟาร์ม-วิสาหกิจชุมชน Farms & growers", "bank": "ธนาคาร-เอทีเอ็ม Banks & ATMs", "laundry": "ร้านซักรีด-สะดวกซัก Laundry", "utilities": "น้ำดื่ม-แก๊สหุงต้ม Drinking Water & Cooking Gas", "post": "ไปรษณีย์-ขนส่ง Post & Parcels", "gov": "ราชการ-เอกสาร Government Offices", "visa": "วีซ่า-ต่ออายุ Visa & Extensions", "copyshop": "ถ่ายเอกสาร-ปริ้นงาน Copy & Print Shops", "printing": "โรงพิมพ์-ป้าย Print Houses & Signs", "translation": "แปลเอกสาร-รับรอง Translation & Document Services", "photo": "ร้านถ่ายรูป-รูปติดบัตร Photo Studios & ID Photos", "convenience": "ร้านสะดวกซื้อ Convenience Stores", "funeral": "งานศพ-ฌาปนสถาน Funeral Directors & Crematoria", "hotel-full": "โรงแรม Hotels", "guesthouse": "เกสต์เฮาส์ Guesthouses", "hostel": "โฮสเทล Hostels", "government": "โรงเรียนรัฐบาล Government schools", "private": "โรงเรียนเอกชน Private schools", "kindergarten": "อนุบาล-เตรียมอนุบาล Kindergartens & nurseries", "university": "มหาวิทยาลัย Universities", "college": "วิทยาลัย-อาชีวศึกษา Colleges & vocational", "campus": "คณะ-อาคารในมหาวิทยาลัย Faculties & campus buildings", "monastic": "โรงเรียนพระปริยัติธรรม Monastic schools", "religious": "โรงเรียนการกุศล-ศาสนา Faith-founded schools", "special": "การศึกษาพิเศษ Special education", "welfare": "ศึกษาสงเคราะห์ Welfare schools", "language": "โรงเรียนสอนภาษา Language schools", "muaythai": "ค่ายมวย-มวยไทย Muay Thai camps", "cooking": "โรงเรียนสอนทำอาหาร Cooking schools", "massage-school": "โรงเรียนสอนนวด Massage schools", "music-art": "โรงเรียนดนตรี-ศิลปะ Music & art schools", "dance": "โรงเรียนสอนเต้น-รำ Dance schools", "tutoring": "กวดวิชา Tutoring", "driving": "โรงเรียนสอนขับรถ Driving schools", "training": "ศูนย์ฝึกอบรม Training centres", "fresh": "ตลาดสด Fresh Markets", "walking-street": "ถนนคนเดิน Walking Streets", "flea": "ตลาดนัด Flea Markets", "crafts": "ของฝาก-หัตถกรรม Crafts & Gifts", "secondhand": "เสื้อผ้ามือสอง-คัดพิเศษ Consignment & Secondhand", "mall": "ห้าง-มอลล์ Malls", "diy": "DIY-วัสดุก่อสร้าง DIY & Hardware", "clothes": "เสื้อผ้า-เครื่องแต่งกาย Clothes & Apparel", "shoes": "รองเท้า Shoes", "sports-shop": "ชุดกีฬา-อุปกรณ์กีฬา Sports & Outdoor Shops", "dresshire": "ร้านเช่าชุด Dress & Costume Hire", "tailor": "ร้านตัดสูท-ตัดชุด Tailors", "alterations": "ซ่อมแซม-แก้เสื้อผ้า Alterations & Repairs", "fabric": "ผ้าเมตร-ร้านผ้า Fabric by the Metre", "bedding": "เครื่องนอน-ผ้าปูที่นอน Bedding & Sheets", "music": "เครื่องดนตรี-ให้เช่า Instruments — buy & rent", "condo": "อาคารชุด-คอนโด Condominiums", "apartment": "อพาร์ตเมนต์-แมนชั่น-คอร์ท Apartments, Mansions & Courts", "dorm": "หอพัก Dormitories", "moobaan": "หมู่บ้านจัดสรร Moobaan (Housing Estates)", "agent": "นายหน้า-เอเจนต์ Agents & Agencies", "parking": "ที่จอดรถ Parking", "motorcycle-parking": "ที่จอดมอเตอร์ไซค์ Motorcycle Parking", "bicycle-parking": "ที่จอดจักรยาน Bicycle Parking", "parking-entrance": "ทางเข้าอาคารจอดรถ Parking Entrances", "rental": "เช่ารถ-มอเตอร์ไซค์ Car & Bike Rental", "bicycle": "จักรยาน-เช่า-ซ่อม Bicycles — Shops, Rental & Repair", "motorbike": "ร้านมอเตอร์ไซค์-โชว์รูม Motorbike Dealers", "train": "สถานีรถไฟ Train Stations", "bus": "สถานีขนส่ง-ท่ารถ Bus Terminals", "songthaew": "รถแดง-สองแถว Rot Daeng & Songthaew", "taxi": "แท็กซี่-คิวรถ Taxi Ranks", "funicular": "รถรางขึ้นดอย The Doi Suthep Funicular", "pier": "ท่าเรือ Piers & Boat Landings", "airport": "สนามบิน Airports", "fuel": "ปั๊มน้ำมัน Fuel Stations", "auto": "ซ่อมรถ-อู่ Auto & Motorbike", "home": "ช่างบ้าน-ช่างอลูมิเนียม Home Trades", "tech": "มือถือ-คอมพิวเตอร์ Phones & Computers", "mend": "ซ่อมรองเท้า-จักร-เครื่องใช้ไฟฟ้า Cobblers, Sewing-Machine & Appliance Repair", "hair": "ร้านทำผม Hair Salons", "extensions": "ต่อผม-ถักเปีย Extensions & braids", "nails": "ทำเล็บ Nails", "salon": "ร้านเสริมสวย Beauty salons", "beauty-spa": "สปาความงาม Beauty spa", "barber": "ตัดผมชาย Barbers", "sak-yant": "สักยันต์ Sak Yant", "studio": "ร้านสักสมัยใหม่ Modern studios", "cosmetic-tattoo": "สักคิ้ว-สักปาก Cosmetic tattoo", "piercing": "เจาะ Piercing", "tattoo-removal": "ลบรอยสัก Removal", "vet": "หมอสัตว์ Vets", "grooming": "อาบน้ำ-ตัดขน Grooming", "pet-shop": "ร้านสัตว์เลี้ยง-อาหารสัตว์ Pet Shops & Feed", "gym": "มวยไทย-ยิม Muay Thai & Gyms", "stadium": "สนามมวย-ดูมวย Stadiums & Fight Nights", "camp": "ค่ายมวย-ยิมมวยไทย Camps & Gyms", "gear": "ร้านอุปกรณ์มวย Gear Shops", "class": "โรงเรียนสอนทำอาหารไทย Cooking Schools & Classes", "vegan": "อาหารเจ-มังสวิรัติ-วีแกน Vegetarian & Vegan Classes", "dessert": "ขนมไทย Thai Dessert Classes", "carving": "แกะสลักผักผลไม้ Fruit & Vegetable Carving", "hotel": "คลาสในโรงแรม-รีสอร์ต Hotel & Resort Cooking Schools", "vocational": "หลักสูตรอาชีพ-สารพัดช่าง-อาชีวะ Vocational & Professional Courses", "elephant-camp": "ปางช้าง-ศูนย์ช้าง Camps & Sanctuaries", "elephant-care": "คลินิกช้าง-โรงพยาบาลช้าง Elephant Clinics & Hospitals", "elephant-craft": "ของช้าง-กระดาษมูลช้าง-รูปปั้น Of the Elephant — paper, statues, craft", "housekeeper": "แม่บ้าน Housekeepers", "handyman": "ช่างซ่อมบ้าน Handymen", "landscaper": "คนสวน-จัดสวน Landscapers", "pest-control": "กำจัดปลวก-แมลง-หนู Pest Control", "clubs": "ชมรม-สมาคม Clubs & Societies", "centre": "ศาลาประชาคม-ศูนย์ชุมชน Community Centres", "volunteer": "จิตอาสา Volunteering", "cremation": "สุสาน-ฌาปนสถานประจำหมู่บ้าน Village Cremation Grounds", "coworking": "โคเวิร์กกิ้งสเปซ Coworking Spaces", "wholesale": "ค้าส่ง-ซัพพลายเออร์ Wholesale & Suppliers", "online-selling": "ขายออนไลน์-ดรอปชิป Online Selling & Dropshipping", "professional": "ทนาย-บัญชี Lawyers & Accountants", "cinema": "โรงหนัง-รอบฉาย Cinemas & Showtimes", "live-music": "ดนตรีสด Live Music", "events-venue": "ที่จัดงาน-อีเวนต์ Event Venues", "museum": "พิพิธภัณฑ์ Museums", "gallery": "หอศิลป์-แกลเลอรี Art Galleries", "gallery-commercial": "แกลเลอรี-ห้องศิลป์ที่ขายงาน Galleries that sell", "park": "สวนสาธารณะ Public parks", "garden": "สวนพฤกษศาสตร์ Gardens", "nature": "เขตอนุรักษ์-อุทยาน Nature reserves", "water": "อ่างเก็บน้ำ-หนองน้ำ Lakes & reservoirs", "playground": "สนามเด็กเล่น Playgrounds", "library": "ห้องสมุด Libraries", "art-studio": "สตูดิโอศิลป์ Art Studios", "historic": "โบราณสถาน-ที่ประวัติศาสตร์ Historic Places", "viewpoint": "จุดชมวิว Viewpoints", "waterfall": "น้ำตก Waterfalls", "peak": "ดอย-ยอดเขา Peaks & Mountains", "cave": "ถ้ำ Caves", "hot-spring": "น้ำพุร้อน Hot Springs", "community-tourism": "ชุมชนท่องเที่ยว Community Tourism", "culture-site": "แหล่งเรียนรู้-ศิลปวัฒนธรรม Culture & Learning", "outing": "ทริปวันเดียว Outings & Day Trips"};
const MD_TOPCATS=["food", "wat", "medical", "essentials", "massage", "hotel"];
const MD_ASK_HOST="https://ask.motdang.net";
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
  if (!/[^ -]/.test(s)) return s;
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
const TH_DROP = new Set(['่', '้', '๊', '๋', '์', 'ฺ', '๎', 'ๆ', '็']);

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
  let key;
  if (hasThai(tok)) {
    let out = '';
    for (const ch of tok) {
      if (TH_DROP.has(ch)) continue;
      const v = TH_VOWELS[ch] || ch;
      out += (TH_MAP[v] || v);
    }
    key = out;
  } else {
    key = tok;
    for (const [a, b] of LATIN_DIGRAPHS) key = key.split(a).join(b);
    let out = '';
    for (const c of key) out += (c in LATIN_SINGLES ? LATIN_SINGLES[c] : c);
    key = out;
  }
  let dedup = '';
  for (const ch of key) if (dedup[dedup.length - 1] !== ch) dedup += ch;
  return dedup;
}

// Damerau-Levenshtein, abandoned once it passes `cap`. Transposition counts as
// one edit: swapped adjacent letters are the commonest typo there is, and the
// commonest disagreement between two romanisations of one syllable.
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
    // Loose key -> the dictionary words sharing it, bucketed by key length, for
    // repairing a misspelled chunk before anything tries to split it.
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
    if (hay.indexOf(phrase) !== -1) return [hay.split(phrase).join(' '), true];
    return [hay, false];
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
    this.looseIndex = new Map();
    for (const g of groups || []) {
      const members = Array.from(new Set((g || []).map(norm).filter(Boolean))).sort();
      if (members.length < 2) continue;
      const gid = this.groups.length;
      this.groups.push(members);
      for (const mem of members) {
        if (!this.index.has(mem)) this.index.set(mem, new Set());
        this.index.get(mem).add(gid);
        const lk = loose(mem);
        if (lk) {
          if (!this.looseIndex.has(lk)) this.looseIndex.set(lk, new Set());
          this.looseIndex.get(lk).add(gid);
        }
      }
    }
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
      if (lk.length >= 4) gids = new Set(this.looseIndex.get(lk) || []);
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

if (typeof module !== 'undefined' && module.exports) module.exports = SEARCHCORE;
if (typeof globalThis !== 'undefined') globalThis.SEARCHCORE = SEARCHCORE;


// The markup twin of build.py's bi(). Anything the client fills in has to
// join its two languages the same way the server does, or a gloss hydrated by
// JS ends up jammed against the Thai ("สีส้มorange") in both-mode.
function mdBi(th,en){th=th==null?'':th;
if(!en)return '<span class="th" lang="th">'+th+'</span>';
var sep=/[·—–:-]\s*$/.test(th)?'':'<span class="th" lang="th"> · </span>';
return '<span class="bi"><span class="th" lang="th">'+th+'</span>'+
'<span class="en" lang="en">'+sep+en+'</span></span>';}

// ---- location: opt-in, never a gate -----------------------------------
// Every geolocation call on this site goes through here, for one reason: a
// browser permission prompt fired at a reader who has not asked for it is a
// hard stop, and in Thailand it is a hard stop that reads as a risk rather
// than a feature. People who back out of that dialog do not come back to the
// page — they leave, and nothing in our logs would ever tell us.
//
// So: nothing here runs on load. The prompt is reachable only from a tap on
// a control that says what it does, our own plain-language dialog goes in
// front of the browser's, and "no" is answered once and kept. Every caller
// gets a usable coordinate whether or not permission was ever granted,
// because the fallback is a named landmark, not an empty state.
/* Exposed on window so a page-specific layer can use the SAME door to the
   permission prompt rather than opening a second one. There is exactly one
   place on this site that may ask a reader where they are, and this is it. */
const MDLOC=(()=>{
let OFF=false,gate=null;
// Two places people actually give directions from. The site spans two
// provinces, so the caller passes a latitude it already has on the page and
// gets back the right one — no third request to work out where "here" is.
const DEF={cm:{lat:18.7876,lng:98.9931,th:'ประตูท่าแพ',en:'Tha Phae Gate',src:'default'},
           cr:{lat:19.9094,lng:99.8325,th:'หอนาฬิกาเชียงราย',en:'Clock Tower',src:'default'}};
const near=lat=>(typeof lat==='number'&&lat>19.3)?DEF.cr:DEF.cm;
// A remembered origin is a place the reader chose, never a fix we were
// handed: a GPS coordinate is not written to disk anywhere on this site.
function origin(lat){
try{const v=JSON.parse(localStorage.getItem('md-origin'));
if(v&&typeof v.lat==='number'&&v.src!=='gps')return v;}catch(e){}
return near(lat);}
function remember(o){if(o&&o.src!=='gps'){
try{localStorage.setItem('md-origin',JSON.stringify(o));}catch(e){}}return o;}
// Said no once, asked never again — and the doors go with it, because a
// control that reopens a dialog the reader already refused is how a site
// teaches people to distrust it on sight.
function kill(){OFF=true;close();
document.querySelectorAll('[data-gps-door]').forEach(el=>el.remove());}
function close(){if(gate){gate.remove();gate=null;}}
function build(onYes){
gate=document.createElement('div');
gate.className='mdgate';gate.setAttribute('role','dialog');
gate.setAttribute('aria-modal','true');gate.setAttribute('aria-label',
'ใช้ตำแหน่งจริงของคุณไหม / Use your real location?');
gate.innerHTML='<div class="mdgatebox"><b>'+
mdBi('ใช้ตำแหน่งจริงของคุณไหม','Use your real location?')+'</b><p>'+
mdBi('ตำแหน่งของคุณอยู่ในเครื่องคุณเท่านั้น ไม่ถูกส่งออกไปไหน และไม่ถูกเก็บไว้ ใช้เพื่อเรียงลำดับในหน้านี้อย่างเดียว',
'Your location stays on this device. It is not sent anywhere and not stored — it only sorts this page.')+
'</p><div class="mdgateacts"><button type="button" data-g="y">'+
mdBi('📍 ใช้ตำแหน่งของฉัน','Use my location')+'</button>'+
'<button type="button" data-g="n" class="mdgateno">'+mdBi('ไม่ต้อง','Not now')+
'</button></div></div>';
document.body.appendChild(gate);
gate.querySelector('[data-g="y"]').addEventListener('click',()=>{close();onYes();});
gate.querySelector('[data-g="n"]').addEventListener('click',kill);
gate.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
gate.querySelector('[data-g="y"]').focus();}
// ok(point) on a real fix; nope() every other way this can end — refused,
// timed out, unsupported, or already denied at the OS level. Callers use
// nope() to fall back to something that works, never to show an error.
function ask(ok,nope){
if(OFF||!navigator.geolocation){nope&&nope();return;}
build(()=>{navigator.geolocation.getCurrentPosition(
p=>ok({lat:p.coords.latitude,lng:p.coords.longitude,src:'gps'}),
()=>{kill();nope&&nope();},
{enableHighAccuracy:true,timeout:10000,maximumAge:60000});});}
// Ask the browser what it already knows, so a door is never shown for a
// permission the OS has already refused.
if(navigator.permissions&&navigator.permissions.query){
try{navigator.permissions.query({name:'geolocation'}).then(st=>{
if(st.state==='denied')kill();
st.onchange=()=>{if(st.state==='denied')kill();};}).catch(()=>{});}catch(e){}}
return {ask,origin,remember,kill,near,get off(){return OFF;}};
})();
window.MDLOC=MDLOC;

// ---- language: Thai, both, or English ---------------------------------
// Default is both. Someone who reads only one of the two should not have to
// find a control before the page makes sense to them. An earlier explicit
// choice — including 'th' or 'en' stored by the old two-way toggle — wins.
const B=document.body;
function mdSetLang(v){B.classList.remove('lang-en','lang-both');
if(v==='en')B.classList.add('lang-en');else if(v==='both')B.classList.add('lang-both');
try{localStorage.setItem('md-lang',v);}catch(e){}
document.querySelectorAll('.langbtn').forEach(b=>
b.setAttribute('aria-pressed',b.dataset.lang===v?'true':'false'));}
mdSetLang((()=>{let v=null;try{v=localStorage.getItem('md-lang');}catch(e){}
return (v==='th'||v==='en'||v==='both')?v:'both';})());
document.querySelectorAll('.langbtn').forEach(b=>
b.addEventListener('click',()=>mdSetLang(b.dataset.lang)));
// ---- hidden bell: the logo ant scurries ------------------------------
const logoAnt=document.querySelector('.logo .ant'),runner=document.getElementById('scurry');
logoAnt&&runner&&logoAnt.closest('.logo').addEventListener('click',()=>{
runner.classList.remove('go');void runner.offsetWidth;runner.classList.add('go');});
// ---- search ----------------------------------------------------------
const RROOT=document.documentElement.getAttribute('data-root')||'';
document.querySelectorAll('form.seek').forEach(f=>{f.addEventListener('submit',e=>{
e.preventDefault();const q=f.querySelector('input').value.trim();
if(q)location.href=RROOT+'search.html?q='+encodeURIComponent(q);});});
const resBox=document.getElementById('results');
async function loadIndex(){const r=await fetch(RROOT+'data/index.json');return r.json();}
if(resBox){(async()=>{
const q=new URLSearchParams(location.search).get('q')||'';
// WO-69 — THE FILTERS. tag= sub= cat= st= ar= narrow; near=lat,lng is a point
// to measure from. Read here, beside q, so the pipeline block below stays
// free of the DOM and the two test harnesses can hand it an F of their own.
const QS=location.search;
const F=(()=>{const u=new URLSearchParams(QS);
const list=k=>(u.get(k)||'').split(',').map(s=>s.trim()).filter(Boolean);
const nr=(u.get('near')||'').split(',').map(Number);
const f={tag:list('tag'),sub:list('sub'),cat:list('cat'),st:list('st'),ar:list('ar'),
near:(nr.length===2&&nr.every(isFinite))?{lat:nr[0],lng:nr[1]}:null};
f.any=!!(f.tag.length||f.sub.length||f.cat.length||f.st.length||f.ar.length||f.near);
return f;})();
document.querySelector('form.seek input').value=q;
// THE GUARD. Everything below this line exists to answer a query, and the
// first thing it does is fetch data/index.json — 6.2 MB, and 6.8 MB with the
// tables beside it, about 36 seconds on a 1.5 Mbps link. It used to run before
// anyone asked whether the reader had typed anything, so opening the search
// page and hesitating cost the whole index to be told nothing. The doors for
// that reader are now baked into search.html itself (search_start_html in
// build.py), so with no query there is nothing to fetch and nothing to draw:
// leave the served page standing and go home.
if(!q&&!F.any)return;
// The two shortcut rows (city map / plan a route, and city · tags · roads ·
// doi) belong to the site, and on a phone they stood between the reader and
// the first result. With a query on the page they file below the list.
{const frag=document.createDocumentFragment();
document.querySelectorAll('header.site .chipbar, header.site .svcbar').forEach(el=>frag.appendChild(el));
resBox.parentNode.insertBefore(frag,resBox.nextSibling);}
// AND THE NOW·NEAR LINE GOES WITH THEM (Nan, 2026-09-07). Today's event
// count, the temperature and the PM2.5 reading are the right first line on
// every page a reader arrives at with no question. This is the one page they
// arrive at WITH one, and the strip sits between them and the answer saying
// nothing about it. Hidden here rather than in nownear_layer, because it is
// this page's circumstance and not a change to the line.
document.querySelectorAll('header.site .nownear').forEach(el=>{el.hidden=true;});
// ---- md:search-pipeline — tests/test_search.py lifts this block ----
// Everything down to the closing marker is cut out by tests/test_search.py and
// run under node against the built index, so its cases exercise the code this
// page actually serves rather than a Python paraphrase of it.
// The test used to find the block by matching a line of the matcher itself.
// The matcher then moved out to search-core/searchcore.js, the anchor stopped
// existing, and the test spent the next three weeks dying on a ValueError
// before it reached a single case. So the anchor is a NAMED MARKER now: move
// it with the block and the test follows; delete it and the test says plainly
// that it can no longer find what it is meant to be testing.
// Keep this stretch free of DOM and network. mdJSON, fetch and loadIndex are
// the only calls out of it, and the test stubs exactly those three.
const idx=await loadIndex();
globalThis.MD_IDX=idx;   // the card panel's "three nearest" reads it (wiring below the render block)
// Searching used to mean typing the name exactly, in order, spelled our way:
// the whole query had to appear as one unbroken substring. "rajavej hospital"
// found nothing, because Rajavej Chiang Mai Hospital keeps two words in the
// middle — and 5,190 listings carry names three words or longer. So the words
// are matched one at a time, and when nothing matches all of them the search
// loosens by steps rather than giving up: most-words-matched first, then near
// spellings. Thai queries carry no spaces, stay a single term, and are matched
// as they always were.
// The matching itself lives in searchcore.js, shared with wichaa's router and
// with the Python that builds both indexes, so one query means one thing across
// the fleet. What used to be here was a substring filter that had grown a
// thesaurus and an edit of slack; what it could never do was read Thai. Thai is
// written without spaces, so ร้านกาแฟนิมมาน arrived as a single token that
// matched nothing at all — and 12,353 listings in this directory are named in it.
//
// The tables are FETCHED, not baked into md.js. Mining them took the thesaurus
// from 76 groups to 2,290 and added a 7,355-word segmentation dictionary, which
// inlined would have put ~60 KB of vocabulary on the ticker, the map and every
// place page to serve a box that only search.html has. Now every other page is
// lighter than it was and the cost falls where the feature is.
const [thesDoc,segText,shelfDoc,panelDoc,lmDoc,tabDoc]=await Promise.all([
mdJSON('data/search_thesaurus.json'),
fetch(RROOT+'data/search_segdict.txt').then(r=>r.ok?r.text():'').catch(()=>''),
mdJSON('data/search_shelves.json'),
mdJSON('data/search_panels.json'),
mdJSON('data/search_landmarks.json'),
mdJSON('data/search_tables.json')]);
// WO-69 — the card's tables: tag / trade / street / area names and the
// opening schedules, each row an int in the index (see search_tables()).
const TAB=Object.assign({tags:[],trade:[],streets:[],areas:[],subs:{},hours:[]},tabDoc||{});
globalThis.MD_TAB=TAB;
const SEG=segText.split('\n').filter(l=>l&&l[0]!=='#');
const SHELVES=(shelfDoc&&shelfDoc.shelves)||{};
const core=new SEARCHCORE.SearchCore((thesDoc&&thesDoc.groups)||[],SEG);
// The name is what a result SHOWS, so it alone should decide the order; the
// shelf, the cuisine, the brand and the road decide only whether a listing is
// findable at all. Kept apart so "coffee" cannot float a shop called Coffee
// Hardware above a cafe. `a` — alt names, old names, the Chinese and Japanese
// names a mapper left in the tags — is matched and never shown.
// The shelf words come from the tables, not from the entry — the entry carries
// only its codes, because twelve thousand copies of "ร้านอาหาร-ของกิน · Food &
// Eats" would cost 1.7 MB on a satellite connection to say twenty-three things.
const sw=e=>((e.c||[]).map(c=>MD_CATWORDS[c]||c).join(' ')+' '+
(e.su||[]).map(s=>(MD_SUBWORDS[s]||'')+' '+s.replace(/-/g,' ')).join(' '));
const index=new SEARCHCORE.Index(core);
// `nm`/`em` where a row has them: the name to MATCH, which is not always the
// name to SHOW. A car park displays "ลานจอดรถ · ใกล้ประตูท่าแพ 100 ม." because
// that is how a reader tells it from the next one, and matches on "ลานจอดรถ"
// because it is not called Tha Phae Gate.
for(const e of idx){index.add(e,{
name:[[e.nm||e.n,e.em||e.e,e.a].filter(Boolean).join(' '),1.0],
shelf:[sw(e)+' '+(e.k||''),0.45]});}
index.finalize();
// The index is the mending dictionary too: ราชเวช is in no Thai dictionary, but
// it is very much a word in a directory that lists the hospital, so a query one
// letter wrong is repaired against what this corpus actually contains.
// ---- NEAR A LANDMARK IS A DISTANCE (WO-68, Nan 2026-09-07) ----------------
// "near tha phae gate" names a POINT. Matched as text it is three ordinary
// words: `gate` scores against every gate in the city, `near` against the
// seventeen places with the word in their name, and a car park 810 m away
// outranks one at 80 m because both merely contain the letters. Nan:
// "Near a landmark should sort by distance."
//
// So the landmark is lifted out of the query before it is analyzed, exactly
// the way searchcore lifts a constraint — its alias and the proximity word in
// front of it are consumed, and what remains is what the reader is looking
// FOR. "parking for motorcycle near taphae gate" becomes: motorbikes, on the
// parking shelf, measured from 18.7877,98.9931.
//
// Longest alias wins, so ประตูช้างเผือก beats ช้างเผือก and Chiang Mai Gate
// beats the bare city name. A query that names a landmark and nothing else
// ("tha phae gate") keeps its words — the reader wants the gate itself, and
// the row for it is a real record.
const LMS=Array.isArray(lmDoc)?lmDoc:[];
const NEARWORD=/(^|\s)(near|nearest|close to|closest to|around|beside|next to|ใกล้ ?ๆ?|แถว ?ๆ?|ข้าง|รอบ ?ๆ?|บริเวณ|แถบ)(\s|$)/gi;
// THE ASPIRATE IS OPTIONAL, AND SO IS THE SPACE. Michael wrote "taphae"; the
// register holds Tha Phae, Thapae, Tha Pae, Thaphae and Tapae, and not that
// one. Chasing spellings into a list one at a time is the mistake the mined
// shelf table already taught us, so this is a rule instead: in Thai
// romanisation the h after t, p and k is written or not written by whoever
// painted the sign, and the space between syllables likewise. `th?a\s*ph?ae`
// covers taphae, thapae, tapae, thaphae and tha phae with one pattern, and
// the register keeps only the spellings that are actually somebody's house
// style. Thai aliases are matched as written — Thai spelling does not drift
// this way.
const lmPat=a=>{let out='';
for(let i=0;i<a.length;i++){const c=a[i].toLowerCase();
if(c===' '||c==='-'){out+='[\\s-]*';continue;}
if(c==='h'&&i>0&&'tpk'.indexOf(a[i-1].toLowerCase())>=0)continue;
out+=c.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
if('tpk'.indexOf(c)>=0)out+='h?';}
return out;};
const LATIN=/^[\x20-\x7e]+$/;
let lm=null,qFor=q;
if(LMS.length){
// Longest alias wins, so ประตูช้างเผือก beats ช้างเผือก and Chiang Mai Gate
// beats the bare city name.
let best=null;
const nq0=SEARCHCORE.norm(q);
for(const l of LMS)for(const a of(l.aliases||[])){
if(a.length<4)continue;
let re=null,hit=null;
if(LATIN.test(a)){re=new RegExp('(^|[^a-z])('+lmPat(a)+')(?![a-z])','i');
const m=re.exec(q);if(m)hit={txt:m[2],idx:m.index+m[1].length};}
else{const i=nq0.indexOf(SEARCHCORE.norm(a));if(i!==-1)hit={txt:a,idx:-1};}
if(hit&&(!best||a.length>best.a.length))best={l:l,a:a,hit:hit};}
if(best){
// Cut the landmark out of the RAW query, then the proximity word that was
// leading up to it. What is left is what the reader is looking FOR.
let left;
if(best.hit.idx>=0)left=q.slice(0,best.hit.idx)+' '+q.slice(best.hit.idx+best.hit.txt.length);
else{const parts=SEARCHCORE.norm(best.a).split(' ').filter(Boolean);
left=q.split(/\s+/).filter(w=>parts.indexOf(SEARCHCORE.norm(w))===-1).join(' ');
if(left===q)left=q.split(SEARCHCORE.norm(best.a)).join(' ');}
left=left.replace(NEARWORD,' ').replace(/\s+/g,' ').trim();
lm=best.l;
// A query that names a landmark AND NOTHING ELSE keeps its words — the gate
// is a record and the reader may want the gate. It is still measured from,
// which is what puts the gate itself (nought metres away) at the top and the
// places carrying its name in order of how near they stand. Typing
// "tha phae gate" used to return the gate fourth, behind three cafés.
if(left)qFor=left;}}
// WO-69 — A TAG IS A FILTER, NOT A WORD (Michael: "discovery should
// EXPLICITLY allow searching/finding by tags"). Three routes, in order:
//   1. tag= in the URL, and #word in the box — always a filter, cut from
//      the words like the landmark above;
//   2. a constraint searchcore already lifted (vegan, wifi, wheelchair,
//      delivery, open late) — mapped onto its tag below, once `an` exists;
//   3. a bare word that IS a tag's name (pizza, japanese, bitcoin, old city,
//      michelin) — a filter only when the filtered set is not empty.
// Routes 2 and 3 are SOFT: never to nothing. Route 1 is what the reader
// asked for by name and may honestly answer zero.
const TAGKEY={};
TAB.tags.forEach((t,i)=>{[t[0],t[1],t[2]].forEach(nm=>{const k=SEARCHCORE.norm(nm||'');if(k&&!TAGKEY[k])TAGKEY[k]={t:i};});});
TAB.trade.forEach((t,i)=>{const k=SEARCHCORE.norm(t[0]||'');if(k&&!TAGKEY[k])TAGKEY[k]={tt:i};});
const resolveTag=v=>{const k=SEARCHCORE.norm(v||'');if(!k)return null;
if(TAGKEY[k])return Object.assign({},TAGKEY[k]);
const ti=TAB.tags.findIndex(t=>t[0]===v);if(ti>=0)return {t:ti};
const si=TAB.trade.findIndex(t=>t[0]===v);if(si>=0)return {tt:si};return null;};
const FT=[];
const pushTag=x=>{if(x&&!FT.some(y=>y.t===x.t&&y.tt===x.tt&&y.none===x.none))FT.push(x);};
// a tag asked for BY NAME that no table knows is a hard filter nothing meets:
// zero rows, the chip struck through — never the whole catalogue
for(const v of F.tag)pushTag(resolveTag(v)||{none:v});
qFor=qFor.replace(/(^|\s)#([^\s#]+)/g,(m,a,w)=>{const r=resolveTag(w);if(r){pushTag(r);return a;}return m;}).replace(/\s+/g,' ').trim();
// No words left and a filter in hand: the filter IS the query. Every row
// stands as an exact hit and the filter step below narrows it.
let an,found;
if(!qFor&&(F.any||FT.length)){an={terms:[],intent:{filters:{},phrases:[]},notes:[]};
found=idx.map(e=>({doc:e,score:0,tier:'exact',coverage:1}));}
else{an=core.analyze(qFor,index);found=an.terms.length?index.search(an,0):[];}
for(const t of an.terms){let hit=null;
for(const v of [t.raw].concat(t.variants||[])){const r=TAGKEY[SEARCHCORE.norm(v)];if(r&&r.t!=null){hit=r;break;}}
if(hit)pushTag({t:hit.t,soft:true,word:t.raw});}
// A BARE SIZE WORD IS A CONSTRAINT THE INDEX CANNOT MEET. "Big women's shoes"
// (Nan, 2026-09-06) matched "big" as text, found a clothing shop with Big in
// its name, and ranked it above every shoe stall. The compound forms (big
// size, ไซส์ใหญ่) are lifted by the shared intent layer; the bare word is
// ambiguous — Big C, big bike — so it is dropped ONLY when keeping it left no
// row matching every word, and the page says so out loud below.
const SIZE_HINT={'big':1,'large':1,'huge':1,'ใหญ่':1,'ไซส์':1};
let sizeDropped=null;
if(found.length&&found[0].coverage<1&&an.terms.length>1){
const kept=an.terms.filter(t=>!SIZE_HINT[t.raw]);
if(kept.length&&kept.length<an.terms.length){
const an2=core.analyze(kept.map(t=>t.raw).join(' '),index);
const f2=an2.terms.length?index.search(an2,0):[];
if(f2.length&&f2[0].coverage>=1){sizeDropped=an.terms.filter(t=>SIZE_HINT[t.raw]).map(t=>t.raw);an=an2;found=f2;}}}
// A word that names a shelf is a reader telling us where to look, not just what
// to match — "coworking" and "ตอกเส้น" each belong to one shelf out of
// twenty-four. Applied as a lift rather than a filter: narrowing hard would
// turn a shelf word that also appears in a shop's name into an empty page.
const wantShelves=new Set();
// shelf_stops: a word the mined table maps to a shelf it does not NAME —
// 'clinic' reached chang through the elephant-hospital child's English name,
// and a reader typing it means people-medicine. Suppressed per word, per
// shelf, so "elephant clinic" still lands: ช้าง lifts chang on its own.
const STOPS=(panelDoc&&panelDoc.shelf_stops)||{};
const lift=w=>{for(const k of(SHELVES[w]||[]))if((STOPS[w]||[]).indexOf(k)===-1)wantShelves.add(k);};
for(const t of an.terms)lift(t.raw);
for(const ph of an.intent.phrases)lift(ph);
// WO-67 — THE PARKING COLUMN, and the reason the word vanished.
//
// searchcore reads "parking" as a CONSTRAINT (access:parking) and eats it out
// of the query, the same way it eats "open now". That is right for "cafe with
// parking" and it was catastrophic on its own: Michael typed "parking for
// motorcycle near taphae gate" and the engine searched for motorcycle + near
// + taphae + gate. The first word he wrote, the whole point of the question,
// was deleted before anything was matched — which is why the page could then
// say "understood 'parking' — this page cannot filter on it yet" and mean it.
// There was no column, because until today there was no parking in the
// catalogue at all: zero records among 22,351.
//
// There are now 1,796. So the constraint is answered the way every other
// shelf word is answered — by lifting the shelf, which raises car parks, files
// everything else behind the namesake header, and leaves the rest of the query
// to do the locating. `parking` is a sub key here, which onShelf() reads
// alongside the category keys.
const IFILT=an.intent.filters||{};
const ivals=k=>[].concat(IFILT[k]||[]);
if(ivals('access').indexOf('parking')!==-1)wantShelves.add('parking');
const TAGOF={diet:{vegetarian:'vegetarian',vegan:'vegan',halal:'halal'},access:{wheelchair:'wheelchair'},
wifi:{yes:'wifi'},delivery:{yes:'delivery'},open:{late:'open-late'}};
for(const k in TAGOF)for(const v of ivals(k)){const slug=TAGOF[k][v];if(!slug)continue;
const ti=TAB.tags.findIndex(t=>t[0]===slug);if(ti>=0)pushTag({t:ti,soft:true,word:v});}
// A topic the site keeps a whole page for answers with that page, not only
// with rows — the rich door, curated in data/curated/search_panels.json.
// Triggered by a word a term expanded to (so จ๊าง arrives through ช้าง) or by
// a phrase of the whole query; first panel to speak wins.
//
// A LIFTED SHELF NO LONGER OPENS A DOOR (2026-09-06, Michael's report). It
// used to, and that is how "parking for motorcycle near taphae gate" was
// answered with elephant camps: the mined table reads the shelf's own English
// TEASER, the chang teaser says "...the gate and the chedis that carry its
// name...", and so gate → chang. Every query naming any gate in this city
// opened the elephant door — full width, glyph, count, lead sentences —
// above the page's own admission that it had matched nothing.
//
// The rule this replaces asked curators to use a shelf trigger "ONLY when
// every term mapping to that key names the topic". That test cannot be made
// by hand: the words are MINED, they change whenever a teaser is reworded,
// and nobody reviewing search_panels.json can see them. It failed twice on
// the same sentence — `clinic` in August, `gate` today — so the kind is
// retired rather than patched a third time. Nine junk words are stopped
// individually in shelf_stops below, and search-core's shelves_motdang()
// stops mining them; this line is what makes those the last of it.
//
// `shelves` KEEPS ITS OTHER JOB. Below, a panel that did open still joins its
// shelf to the lift, which is what raises on-shelf rows and splits namesakes
// out from them. Trigger and lift were one field doing two things; only the
// trigger was leaky.
// MATCHED AGAINST WHAT IS LEFT TO ASK, not the raw query. When a landmark has
// been lifted out, its words have already been answered — with metres — and a
// topic card about them is a second answer to a question nobody asked twice.
// "parking near tha phae gate" opened the MOAT door, nine ways to tell inside
// from outside, a wall of it above the car parks. Same shape as the elephant
// panel, one notch less absurd. A query that is ONLY a landmark keeps its
// words (qFor is the query), so "tha phae gate" still opens the moat door,
// which is exactly where that reader wants to be.
const nq=SEARCHCORE.norm(qFor);
const PANELS=(panelDoc&&panelDoc.panels)||[];
const panel=PANELS.find(p=>
(p.variants||[]).some(v=>an.terms.some(t=>t.variants.indexOf(v)!==-1))||
(p.query||[]).some(s=>nq&&nq.indexOf(SEARCHCORE.norm(s))!==-1))||null;
if(panel)for(const s of(panel.shelves||[]))wantShelves.add(s);
const onShelf=e=>(e.c||[]).some(c=>wantShelves.has(c))||(e.su||[]).some(s=>wantShelves.has(s));
if(wantShelves.size){for(const r of found){
if(onShelf(r.doc))r.score+=0.5;}
found.sort((a,b)=>b.score-a.score);}
// Loosen by STEPS, never all at once. A reader who typed two words meant both,
// so listings matching all of them are the answer and listings matching one are
// a fallback offered only when there is no answer. Keeping them mixed in also
// made the count lie: ร้านกาแฟนิมมาน reported 2,247 finds, which was every cafe
// in the directory plus everything on that road — and the count is the one
// number on this page that has to be true.
// WO-69 — THE FILTER STEP. A filter narrows; a mined shelf word only lifts
// (WO-68's rule). Applied BEFORE the loosen-by-steps below, so the tiers are
// settled over the rows that survive it, not over rows it was about to drop.
const FSUB=new Set(F.sub),FCAT=new Set(F.cat),FST=new Set(F.st),FAR=new Set(F.ar);
const arIdx=new Set();TAB.areas.forEach((a,i)=>{if(FAR.has(a[0])||FAR.has(a[1]))arIdx.add(i);});
const stIdx=new Set();TAB.streets.forEach((s,i)=>{if(FST.has(s[0]))stIdx.add(i);});
const hardTags=FT.filter(x=>!x.soft),softTags=FT.filter(x=>x.soft);
const hasTag=(e,x)=>x.none!=null?false:(x.t!=null?(e.t||[]).indexOf(x.t)!==-1:(e.tt||[]).indexOf(x.tt)!==-1);
const pass=e=>(!FSUB.size||(e.su||[]).some(s=>FSUB.has(s)))&&(!FCAT.size||(e.c||[]).some(c=>FCAT.has(c)))
&&(!stIdx.size||stIdx.has(e.st))&&(!arIdx.size||arIdx.has(e.ar))&&hardTags.every(x=>hasTag(e,x));
const HARD=!!(FSUB.size||FCAT.size||stIdx.size||arIdx.size||hardTags.length);
if(HARD)found=found.filter(r=>pass(r.doc));
for(const x of softTags){const f2=found.filter(r=>hasTag(r.doc,x));if(f2.length)found=f2;else x.dropped=true;}
const whole=found.filter(r=>r.coverage>=1);
if(whole.length)found=whole;
// WO-70 — THE RARE WORD IS THE QUESTION (Michael, "best place to buy a
// Martin guitar": `buy` matched 261 rows, `martin` 4, `guitar` 4; every row
// had matched one word, all tied on coverage, and Guitar House came ~230th
// behind the cafés that matched "buy"). When no row matched every word, a
// word that matches four rows says more about what was wanted than one that
// matches two hundred — so the partial pile is ranked by the rarity of what
// each row matched, Σ log(N/df), and the matcher's own score breaks ties.
// Rows that matched every word are not touched.
if(found.length&&found[0].coverage<1&&an.terms.length>1){
const N=idx.length||1,DID=new Map(index.docs.map((d,i)=>[d,i]));
const DF=an.terms.map(t=>{const ids=new Set();for(const [nm] of index.fields){for(const d of index._resolve(t,nm,0).keys())ids.add(d);}
return {ids:ids,w:Math.log((N+1)/(ids.size+1))};});
for(const r of found){let s=0;const d=DID.get(r.doc);for(const f of DF)if(f.ids.has(d))s+=f.w;r.rare=s;}
found.sort((a,b)=>(b.rare-a.rare)||(b.score-a.score));}
// A STATED CONSTRAINT NARROWS; A SHELF WORD ONLY LIFTS. The difference is
// what the reader said. "motorcycle" HINTS at the transport shelf, and the
// mined table lifts it — but the transport shelf also holds every rental
// counter and repair hut in the city, so with a distance sort the nearest of
// those sat on top of a search whose first word was `parking`. "parking" is
// not a hint: searchcore lifted it as access:parking, which is the reader
// stating a requirement. So it filters.
// Never to nothing, though: a requirement no row can meet leaves the rows we
// have rather than an empty page, and the status line above still says the
// word was understood.
if(ivals('access').indexOf('parking')!==-1){
const onlyPark=found.filter(r=>(r.doc.su||[]).indexOf('parking')!==-1);
if(onlyPark.length)found=onlyPark;}
// THE SORT, when a landmark was named. Relevance has already decided WHICH
// rows answer; the landmark decides their ORDER, because that is the only
// thing the reader asked about them. Nearest first, and a row with no pin
// sorts last rather than nowhere — it is still an answer, it just cannot say
// how far.
//
// Kept inside the tier the matcher settled on: an exact match may not be
// pushed below a near-spelling one for being further away, or a typo would
// win by standing closer. Within a tier, metres decide.
const R2D=Math.PI/180;
const distM=(a,b,c,d)=>{const x=(c-a)*R2D*6371000,y=(d-b)*R2D*6371000*Math.cos((a+c)/2*R2D);
return Math.sqrt(x*x+y*y);};
// The point everything is measured from: the landmark the reader named, or
// the near= the page was opened with. One point, whichever was given.
const P=lm?{lat:lm.lat,lng:lm.lng,id:lm.id,th:lm.th,en:lm.en}:(F.near?{lat:F.near.lat,lng:F.near.lng}:null);
if(P){const TIERS={exact:0,thesaurus:1,loose:2,partial:3};
for(const r of found){const e=r.doc;
r.m=(e.lat==null||e.lng==null)?null:distM(P.lat,P.lng,e.lat,e.lng);}
found.sort((a,b)=>((TIERS[a.tier]||0)-(TIERS[b.tier]||0))
||((a.m==null)-(b.m==null))||((a.m||0)-(b.m||0)));
// THE LANDMARK ITSELF GOES FIRST when it is among the answers. A reader who
// types "tha phae gate" is owed the gate before the cafés beside it, and it
// will not get there on its own: the gate's record is named ประตูท่าแพ
// Thapae Gate and matched that query at a worse tier than two cafés whose
// road field spells it the way the reader did. Nought metres beats every
// argument about spelling.
if(P.id){const i=found.findIndex(r=>r.doc.id===P.id);
if(i>0)found.unshift(found.splice(i,1)[0]);}}
const hits=found.slice(0,200).map(r=>r.doc);
// The metres, by row id, so the renderer can put the one fact the reader
// asked for on the row itself instead of making them open each page to find
// out which is nearest.
const HITM={};if(P)for(const r of found.slice(0,200))HITM[r.doc.id]=r.m;
// ---- md:search-pipeline ends ----
// ---- md:search-render — tests/test_search_page.py lifts from here ----
// Everything from here to the closing marker BUILDS THE PAGE, and until
// 2026-09-07 nothing tested it: tests/test_search.py stops at the line
// above, so a ReferenceError in this half took the entire result list down
// while every search case still passed. Same rule as the pipeline marker —
// move the block and take the marker with it.
// ช้าง answers twice in this city: the camps, and the gates, roads and noodle
// shops that carry the elephant in their NAME — ช้างเผือก, ช้างคลาน, ดอยช้าง.
// Mixed together the second kind buries the first; split, both read true.
// On-shelf rows are the answer; namesakes file behind their own header below.
// The split happens only when the query named a shelf at all — a plain name
// search stays one list, exactly as it was.
const onHits=wantShelves.size?hits.filter(onShelf):hits;
const nameHits=wantShelves.size?hits.filter(e=>!onShelf(e)):[];
// The count says how many were FOUND, not how many fit on the page. Showing the
// capped number told a reader searching "coffee" that the city holds 200 cafes
// when the directory knows 1,976 of them — the one number on this page that has
// to be true.
//
// AND IT SAYS WHAT IT COUNTED. In partial mode this number is the size of the
// loosened pile, not a count of answers: "parking for motorcycle near taphae
// gate" matched no row at all and the heading still read "Search results
// 3,514". A reader reads that as three thousand answers. The word beside it
// is the difference between a count and a boast.
// The loosest tier anything was matched at — 'exact' is silent, everything
// else means the page has to say out loud that it widened. Declared HERE, at
// its first use, and not further down beside the status lines: it was below,
// `partial` read it above, and `const` in the dead zone threw a
// ReferenceError that took the whole result list down. The unit harness never
// saw it — it lifts only the pipeline block, which ends above this line — so
// it took loading the page in a browser to find. Hence tests/test_search_page.py.
const worst=found.length?found[0].tier:null;
const partial=worst==='partial';
document.getElementById('rescount').textContent=(q||F.any)?`${found.length}`:'';
document.getElementById('rescount').className=partial?'count partial':'count';
{const rq=document.getElementById('resqual');
if(rq)rq.innerHTML=(q&&partial)?mdBi('ที่ตรงบางคำ','partial matches'):'';}
// Say plainly how the match was made. A reader shown a near-spelling match
// without being told it was one has been quietly misled about how well the
// search understood them — and a reader who sees ร้านกาแฟนิมมาน reported as
// ร้านกาแฟ + นิมมาน can tell at a glance whether the split was the one they meant.
// Did this query ask after women's health at all? The marker rides on the
// speciality's own vocabulary, so the test is whether any term expanded to it.
const obAsked=an.terms.some(t=>t.variants.some(v=>v==='obgyn'||v==='นรีเวช'||v==='สูตินรีเวช'));
// Status lines print ONCE, in the script the reader typed in. A reader who
// typed Latin is not helped by a Thai sentence above their results, and the
// reverse; .solo survives every language mode, as it does for a lone name.
const qTh=SEARCHCORE.hasThai(q);
const say=(th,en)=>qTh?'<span class="th solo" lang="th">'+th+'</span>':'<span class="en solo" lang="en">'+en+'</span>';
// The count and the cap were printed TWICE — "3,931" in the heading and
// "showing 200 of 3,931" one line below it. The heading is where the number
// belongs; what this line is for is the thing the reader can DO, so that is
// all it says now.
// WO-69: "add a word to narrow it" came off — the count already says.
const more='';
// WO-69 — HOW THE SEARCH READ YOU, AS CHIPS, NOT SENTENCES. A mended or
// loosened spelling is "≈ word"; a Thai query cut into words is the words;
// a search where no row matched everything is each word with its own count;
// a size or a constraint the page could not use is the word struck through;
// the landmark or the point everything is measured from is 📍 and its name.
// (Michael, 2026-09-07: "if you need to explain something using words,
// you're fucking up".) `says` holds chip HTML; `note` renders them in one
// row. The old sentences are gone, not hidden.
const hx=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const says=[];
const words=()=>an.terms.map(t=>t.raw).join(' + ');
// WHICH OF THESE ANSWERS A QUESTION THE READER HAS (Nan, 2026-09-07).
// Kept: the ones that answer "why am I looking at this, and what do I do
// about it" — a repaired spelling, a query read as separate words, a list
// ordered by nearness of spelling, a search that matched nothing whole, a
// word we understood and could not use. Each changes whether the reader
// retypes.
// CUT: "including words that mean the same thing". It fired on the ordinary
// successful case — the thesaurus doing its job — and told nobody anything
// they could act on. A line printed on a good search is a line the reader
// learns to look past, which costs the lines that matter.
if(an.notes.indexOf('mended')>=0||worst==='loose')says.push('≈ '+hx(an.terms.map(t=>t.raw).join(' ')));
if(an.notes.indexOf('segmented')>=0)says.push(an.terms.map(t=>hx(t.raw)).join(' + '));
// The point, and it goes FIRST because it decided the order of everything
// under it.
if(P)says.unshift('📍 '+(lm?mdBi(lm.th,lm.en||lm.th):''));
// NOT EVERY WORD MATCHED — say which. The engine keeps every row that matched
// some of the words only when none matched all of them; the reader is owed the
// count behind each word, not a shrug. Counted against the same index the rows
// came from, so the numbers and the list can never disagree.
if(worst==='partial'){for(const t of an.terms){const ids=new Set();
for(const [nm] of index.fields){for(const d of index._resolve(t,nm,0).keys())ids.add(d);}
says.push(hx(t.raw)+' <span class="count">'+ids.size+'</span>');}}
if(sizeDropped)says.push('<s>'+hx(sizeDropped.join(' '))+'</s>');
// Constraints the box understood but this page has no column to filter on. Said
// out loud and BY NAME, because a filter silently dropped is worse than one
// politely declined, and "cannot filter on that" left the reader guessing what
// "that" was.
// Which constraint this page can actually act on, by KEY and by VALUE. It
// used to be by key alone and empty, so every constraint got the same shrug.
// `access` is the case that proves the pair is needed: access:parking has a
// shelf behind it as of WO-67, access:wheelchair and access:english still
// have nothing, and one word cannot answer for all three.
const CANFILTER={access:['parking','wheelchair'],diet:['vegetarian','vegan','halal'],wifi:['yes'],delivery:['yes'],open:['late']};
const canFilter=k=>{const c=CANFILTER[k];const vs=ivals(k);
return !!c&&vs.length>0&&vs.every(v=>c.indexOf(v)!==-1);};
const FILTER_SAY={size:['ยังไม่มีร้านไหนในนี้บันทึกไซส์ไว้ — ค้นจากคำที่เหลือ','no listing here records sizes yet — the search ran on the other words']};
const asked=Object.keys(IFILT).filter(k=>!canFilter(k));
if(asked.length&&found.length&&Object.keys(IFILT).every(k=>!canFilter(k)))
for(const ph of(an.intent.phrases||[]))says.push('<s>'+hx(ph)+'</s>');
const note=says.length?'<li class="shelf fbar rd">'+says.map(s=>'<span class="rchip">'+s+'</span>').join(' ')+'</li>':'';
// WO-69 — THE ACTIVE FILTERS, each a chip whose tap REMOVES it. No label.
const fbar=(()=>{const items=[];const u0=new URLSearchParams(QS);
const without=(k,v)=>{const u=new URLSearchParams(u0);const rest=(u.get(k)||'').split(',').filter(x=>x&&x!==v);
if(rest.length)u.set(k,rest.join(','));else u.delete(k);const s=u.toString();return RROOT+'search.html'+(s?'?'+s:'');};
for(const x of FT){const tg=x.t!=null?TAB.tags[x.t]:null,tr=x.tt!=null?TAB.trade[x.tt]:null;
const lab=tg?((tg[3]?tg[3]+' ':'')+mdBi(tg[1],tg[2])):hx(tr?tr[0]:(x.none||''));const val=tg?tg[0]:(tr?tr[0]:(x.none||''));
items.push('<a class="rchip on'+((x.dropped||x.none!=null)?' off':'')+'" href="'+without('tag',val)+'">'+lab+'</a>');}
for(const s of F.sub)items.push('<a class="rchip on" href="'+without('sub',s)+'">'+(TAB.subs[s]?mdBi(TAB.subs[s][0],TAB.subs[s][1]):hx(s))+'</a>');
for(const c of F.cat)items.push('<a class="rchip on" href="'+without('cat',c)+'">'+(MD_CATWORDS[c]||hx(c))+'</a>');
for(const s of F.st){const row=TAB.streets.find(x=>x[0]===s);items.push('<a class="rchip on" href="'+without('st',s)+'">'+(row?mdBi(row[1]||row[2],row[2]||row[1]):hx(s))+'</a>');}
for(const a of F.ar)items.push('<a class="rchip on" href="'+without('ar',a)+'">'+hx(a)+'</a>');
return items.length?'<li class="shelf fbar">'+items.join(' ')+'</li>':'';})();
// A place carrying `ob` answered a women's-health query on the strength of
// being a general hospital, which is not the same as anybody having confirmed
// an OB-GYN department there. The cm-womens-health harvester graded it
// `hospital-likely` for exactly that reason, so the row grades it too. Said in
// the row rather than in a footnote: a reader scanning forty-nine names should
// be able to see which five are stated and which forty-four are inferred,
// without reading anything above the list.
// IF IT DOES NOT ANSWER A QUESTION IT IS NOT ON THE ROW (Nan, 2026-09-07:
// "slash and burn. If it doesn't answer a question, it is invisible.")
//
// The province used to print on all two hundred rows. When every row is in
// Chiang Mai — which is most searches, because most of the catalogue is —
// that is two hundred repetitions of one word, and it answers a question
// nobody asked. It prints now only when the results actually SPAN the two
// provinces, which is the only time it tells them apart.
const spanProv=(()=>{let a=null;for(const e of hits){if(a===null)a=e.pv;
else if(e.pv!==a)return true;}return false;})();
// The metres, when the reader named a landmark. This is the whole of what
// they asked about these rows, so it is on the row — not one tap away on
// each of two hundred pages.
// The whole chip through mdBi, not the unit on its own: "80 " + bi("ม.","m")
// rendered as "80 ม. · m" in both-languages mode, which is not a distance in
// either language.
const fmtM=m=>{if(m==null)return '';
const v=m<1000?String(Math.round(m/10)*10):(m/1000).toFixed(1);
return m<1000?mdBi(v+' ม.',v+' m'):mdBi(v+' กม.',v+' km');};
// ONE DISTANCE PER ROW, AND IT IS THE ONE THAT WAS ASKED FOR. A synthesised
// car-park name ends in a bearing to whichever landmark it stands nearest,
// which is what tells it from the next car park — and in a list measured from
// Tha Phae Gate it produced rows reading
//     "ที่จอดรถ · ใกล้แจ่งก๊ะต๊ำ 290 ม. · 430 ม."
// two numbers, neither obviously the one the reader asked about. So under a
// landmark sort the row shows the name WITHOUT its bearing (`nm`/`em`, the
// same base the index matches on) and the chip carries the only distance that
// answers the question. Everywhere else the bearing stays: it is the name.
const dName=e=>(lm&&e.nm)?e.nm:e.n;
const dEn=e=>(lm&&e.em)?e.em:e.e;
// WO-69 — THE CARD (Michael, 2026-09-07). A result is a place, not a link:
// its name, the reading or the English, the metres when a point is known,
// a lamp when we hold a schedule (lit = open now; unlit = closed now; none =
// nobody has recorded hours, which is not "closed"), up to three chips —
// the sub-shelf, the street or the district or the nearest landmark, the
// best tag — every chip a filter, and a 📍. The body opens in place (the
// wiring below the render marker): a mini map, the three nearest places we
// hold, the same kind nearby, what is on here, add to plan.
// THE CLOCK IS THE SHOP'S, NOT THE READER'S. This was new Date().getDay(),
// which is right in Chiang Mai and wrong everywhere else: a reader in London
// saw an unlit lamp on a shop that was open, while /api/v1 answered correctly
// for the same place at the same moment, because it has always gone through
// Intl. Intl does the zone rather than a hardcoded +7, for the reason
// publish/api.js gives: Thailand has not moved its offset since 1920, and an
// offset written into code is a silent bug the day a rule changes.
// hourCycle h23 is the one place this differs from api.js — en-GB with
// hour12:false reports midnight as 24 on some engines, which would put the
// small hours a whole day out. api.js wants the same eight characters.
const MDDAYS=['Mo','Tu','We','Th','Fr','Sa','Su'];
const mdWmin=d=>{try{
const pt=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Bangkok',weekday:'short',
hour:'2-digit',minute:'2-digit',hour12:false,hourCycle:'h23'}).formatToParts(d||new Date());
const g=t=>{const x=pt.find(q=>q.type===t);return x?x.value:'';};
const dy=MDDAYS.indexOf(g('weekday').slice(0,2)),h=parseInt(g('hour'),10),m=parseInt(g('minute'),10);
if(dy<0||isNaN(h)||isNaN(m))return null;return dy*1440+h*60+m;}catch(e){return null;}};
// Recomputed at most twice a minute. A page left open crosses closing time,
// and a lamp that was drawn once at load is a lamp that lies by teatime.
let _wmT=0,_wmV=null;
const WMIN=()=>{const n=Date.now();if(!_wmT||n-_wmT>3e4){_wmV=mdWmin();_wmT=n;}return _wmV;};
// null, NEVER false, when nobody has recorded hours. build_open_lamps.py
// refuses to guess at the strings it cannot parse, and this must not undo that
// by drawing "no one has said" as "shut".
const mdOpen=(sch,w)=>{if(!sch||!sch.length||w==null)return null;
for(const iv of sch)if(w>=iv[0]&&w<iv[1])return true;return false;};
// Minutes until the state changes. The intervals cover one week and they wrap,
// so the edges are searched across three — last week, this one, next — and the
// first one after now wins. A shop open right through to next week has no edge
// ahead of it inside the window and gets null, which prints nothing.
const MDWEEK=10080;
const mdEdge=(sch,w)=>{if(!sch||!sch.length||w==null)return null;let best=null;
for(const iv of sch)for(const k of[-MDWEEK,0,MDWEEK])for(const t of[iv[0]+k,iv[1]+k]){
const d=t-w;if(d>0&&(best===null||d<best))best=d;}
return best;};
// The state between open and closed, which is the one a reader acts on: a lamp
// says whether to go, this says whether to hurry. Only inside the hour — an
// edge nine hours out is not news, it is the opening times, and those are on
// the place's own page.
const MDSOON=60;
const mdWhen=(sch,w)=>{const on=mdOpen(sch,w);if(on===null)return '';
const d=mdEdge(sch,w);if(d===null||d>MDSOON)return '';
return on?mdBi('ปิดใน '+d+' นาที','closes in '+d+' min')
:mdBi('เปิดใน '+d+' นาที','opens in '+d+' min');};
// Handed to the surfaces that are their own files — here.js, near.js — so the
// site has one reading of a schedule rather than one per page.
if(typeof window!=='undefined')window.MDHOURS={open:mdOpen,edge:mdEdge,when:mdWhen,wmin:mdWmin,now:WMIN};
const schOf=e=>(e.hk==null?null:(TAB.hours[e.hk]||null));
const openNow=e=>mdOpen(schOf(e),WMIN());
const nearLm=e=>{let b=null,bd=1500;for(const l of LMS){if(l.lat==null||l.lng==null)continue;
const d=distM(e.lat,e.lng,l.lat,l.lng);if(d<bd){bd=d;b=l;}}return b;};
// WHAT THIS PLACE IS, WHERE IT IS, WHAT ELSE IT IS — in that order, and
// every one of them a filter the reader can tap. The last is the shelf the
// sub-shelf hangs off, so a record with nothing but a name and a shelf still
// carries two: a guitar shop in Chiang Rai with no street, no tambon and no
// landmark within 1.5 km was showing one chip and reading like a bare link.
const chipsOf=e=>{const out=[];
const su=(e.su||[])[0];
if(su&&TAB.subs[su])out.push(['?sub='+encodeURIComponent(su),mdBi(TAB.subs[su][0],TAB.subs[su][1])]);
if(e.st!=null&&TAB.streets[e.st]){const s=TAB.streets[e.st];out.push(['?st='+encodeURIComponent(s[0]),mdBi(s[1]||s[2],s[2]||s[1])]);}
else if(e.ar!=null&&TAB.areas[e.ar]){const a=TAB.areas[e.ar];const nm=a[0]||a[1];out.push(['?ar='+encodeURIComponent(nm),mdBi(nm,a[3]||nm)]);}
else if(e.lat!=null){const nl=nearLm(e);if(nl)out.push(['?q='+encodeURIComponent(q)+'&near='+nl.lat+','+nl.lng,'📍 '+mdBi(nl.th,nl.en||nl.th)]);}
if(e.t&&e.t.length&&TAB.tags[e.t[0]]){const t=TAB.tags[e.t[0]];out.push(['?tag='+encodeURIComponent(t[0]),(t[3]?t[3]+' ':'')+mdBi(t[1],t[2])]);}
else if(e.tt&&e.tt.length&&TAB.trade[e.tt[0]]){const t=TAB.trade[e.tt[0]];out.push(['?tag='+encodeURIComponent(t[0]),hx(t[0])+(t[2]?' <span class="en roman">'+hx(t[2])+'</span>':'')]);}
if(e.c&&e.c[0]&&MD_CATWORDS[e.c[0]]&&!(su&&TAB.subs[su]&&out.length>=3))out.push(['?cat='+encodeURIComponent(e.c[0]),MD_CATWORDS[e.c[0]]]);
return out.slice(0,3);};
const row=e=>{const ch=chipsOf(e),w=WMIN(),sch=schOf(e),on=mdOpen(sch,w),soon=mdWhen(sch,w);
return `<li class="rcard" data-id="${hx(e.id)}"${e.lat!=null?` data-lat="${e.lat}" data-lng="${e.lng}"`:''} data-plan="${hx(e.p+':'+e.s)}">`+
`<a class="rname" href="${RROOT}${e.p}/p/${e.s}.html">${hx(dName(e))}</a>`+
`${dEn(e)&&dEn(e)!==dName(e)?' <span class="count">'+hx(dEn(e))+'</span>':(e.r?' <span class="count roman">'+hx(e.r)+'</span>':'')}`+
`${P&&HITM[e.id]!=null&&e.id!==P.id?' <span class="count dist u">· '+fmtM(HITM[e.id])+'</span>':''}`+
`${on===true?' <span class="lamp on"></span>':(on===false?' <span class="lamp off"></span>':'')}`+
`${soon?' <span class="count soon">'+soon+'</span>':''}`+
`${spanProv?' <span class="count">· '+e.pv+'</span>':''}`+
`${e.ob&&obAsked?' <span class="prov">'+(e.ob===2?mdBi('รพ.สต. — สถานีอนามัยประจำตำบล ฝากครรภ์และวางแผนครอบครัวเป็นงานประจำ','รพ.สต. — the local primary-care station; antenatal care and family planning are routine'):mdBi('โรงพยาบาลทั่วไป — ยังไม่ได้ยืนยันว่ามีแผนกสูตินรีเวช','general hospital — an OB-GYN department is not confirmed'))+'</span>':''}`+
(ch.length?' <span class="rchips">'+ch.map(c=>`<a class="rchip" href="${RROOT}search.html${c[0]}">${c[1]}</a>`).join(' ')+'</span>':'')+
(e.lat!=null?'<button type="button" class="rpin" aria-label="แผนที่ · map">📍</button>':'')+
'<div class="rpanel" hidden></div></li>';};
// Two hundred names in one column is a list nobody reads. Grouped under the
// shelf each one stands on, with its count, the same result becomes a page you
// can steer: thirty-three ข้าวซอย places, four of them in Chiang Rai.
// EXCEPT WHEN DISTANCE IS THE ORDER. Grouping sorts the shelves by size and
// prints them one after another, which quietly re-sorts the rows: a search
// for "tha phae gate" put three cafés above the gate itself because food was
// the bigger group, after the distance sort had correctly placed the gate at
// nought metres. Nearest-first is a single sequence or it is nothing, so a
// landmark search renders one flat list — and the shelf headings, which
// answer "what kinds are these", are not an answer to "which is nearest".
const groupHtml=list=>{if(P)return list.map(row).join('');
const groups=new Map();
for(const e of list){const c=(e.c&&e.c[0])||'other';
if(!groups.has(c))groups.set(c,[]);groups.get(c).push(e);}
return [...groups.entries()].sort((a,b)=>b[1].length-a[1].length)
.map(([c,shelf])=>{const lab=MD_CATWORDS[c];
const head=lab?`<li class="shelf"><a href="${RROOT}${shelf[0].p}/${c}/">${lab}</a> <span class="count">${shelf.length}</span></li>`:'';
return head+shelf.map(row).join('');}).join('');};
// The rich door itself. Its count is taken from the index the page just
// loaded, so it is the directory's own number today, never a baked one.
const pdoor=d=>{const ext=/^https?:/i.test(d.href);
return `<a class="pdoor${d.main?' pdmain':''}" href="${ext?d.href:RROOT+d.href}"${ext?' rel="noopener"':''}>${mdBi(d.label[0],d.label[1])}</a>`;};
const pcodes=(panel&&panel.count&&panel.count.codes)||[];
const pcount=pcodes.length?idx.filter(e=>(e.c||[]).some(c=>pcodes.indexOf(c)!==-1)||(e.su||[]).some(s=>pcodes.indexOf(s)!==-1)).length:0;
// NO DOOR OVER A SEARCH THAT ALREADY FAILED. A rich door is an ANSWER — glyph,
// count, lead sentences, a main door in gold — and in partial mode the page
// has just worked out that nothing matched everything the reader typed. Those
// two things on one screen make the door a wrong answer given confidently,
// which is worse than no answer: Michael read the elephant panel as the reply
// to "parking for motorcycle near taphae gate" and never scrolled as far as
// the sentence saying we could not help.
//
// The panel is suppressed, not the lift. If the query really was about
// elephants, its shelf still raises elephant rows up the list — where a row is
// a row and claims nothing more.
const panelHtml=(panel&&!partial)?`<li class="richdoor">`+
`<p class="rdhead">${panel.glyph?panel.glyph+' ':''}<b>${mdBi(panel.title[0],panel.title[1])}</b>${pcount?` <span class="count">${pcount}</span>`:''}</p>`+
`<p class="rdlead">${mdBi(panel.lead[0],panel.lead[1])}</p>`+
((panel.facts&&panel.facts.length)?`<p class="rdfacts">${panel.facts.map(f=>`<span class="rdfact">${mdBi(f[0],f[1])}</span>`).join(' ')}</p>`:'')+
`<p class="rddoors">${(panel.doors||[]).map(pdoor).join(' ')}</p>`+
(panel.delight?`<p class="rddelight">${mdBi(panel.delight[0],panel.delight[1])}</p>`:'')+
`</li>`:'';
// The namesake shelf reads as its own find, not as noise pushed down: the
// header says WHY these rows answered, and the count beside it stays true.
const divider=(wantShelves.size&&nameHits.length)?`<li class="shelf namesake">${mdBi('ชื่อพ้อง — ที่ซึ่งชื่อมีคำนี้อยู่','namesakes — places carrying the word in their name')} <span class="count">${nameHits.length}</span></li>`:'';
// Nothing found is a fork in the road, not a wall. The shelves are the doors a
// reader can actually walk through, and the ants are the door for a place the
// directory does not hold yet.
const doors=()=>{const top=MD_TOPCATS.map(c=>
`<li class="shelf"><a href="${RROOT}cm/${c}/">${MD_CATWORDS[c]||c}</a></li>`).join('');
return top+
`<li class="shelf"><a href="${RROOT}crawl-request.html">ส่งมดไปสำรวจ · Request a crawl</a></li>`;};
// A reader whose words did not all match is owed a way forward, not only an
// apology. The shelves are no use here — the query named no shelf — so the two
// doors are the ants, who can read a sentence and search the same catalogue
// with more patience than a word index, and the crawl request, which is how a
// thing the directory does not hold gets held. Offered ONLY in partial mode:
// on a search that worked, this would be clutter over a good answer.
const askDoor=MD_ASK_HOST
?' · <a href="'+MD_ASK_HOST+'/?q='+encodeURIComponent(q)+'" rel="noopener">'+mdBi('คุยกับมด','chat with the ants')+'</a>':'';
const stuck=partial?'<li class="shelf stuck">'+askDoor.replace(/^ · /,'')+
(askDoor?' · ':'')+'<a href="'+RROOT+'suggest.html?kind=crawl&t='+encodeURIComponent('crawl request (search): '+q)+'">'+
mdBi('ส่งมดไปเก็บ','send the ants')+'</a></li>':'';
// q is guaranteed non-empty here — the guard above sent the other reader
// home to the served page.
//
// THE ORDER IS THE FIX (2026-09-06). It used to be panel, then note: the
// page's own account of how it had read the query — "nothing matches all of
// motorcycle + near + taphae + gate", "understood 'parking' — this page cannot
// filter on it yet" — printed BELOW a full-width topic card, in the smallest
// type on the page. Every true sentence we had was underneath the wrong one.
// How the search read you now comes first, then what it found.
// `more` — "add a word to narrow it" — sits UNDER the list now. It is advice
// about the list, and advice printed above two hundred answers is one more
// thing between the reader and the first of them.
// P1 — A SHORT ANSWER GETS A SHORT PAGE. Four rows or fewer and the page ends
// at the answer: the shortcut grid, the services bar and the footer's link row
// do not render (CSS, body.mdshort). The OSM credit and the licence line stay,
// because they are a licence condition and not decoration.
// Four is the line because a phone shows about that many rows below the box
// and the heading, so up to four is an answer a reader takes in whole, and
// five is a list they have started scanning. A search that found NOTHING is
// not short in this sense — it needs its shelves and its way forward, which
// is the one time that furniture is the answer.
document.body.classList.toggle('mdshort',hits.length>0&&hits.length<=4);
// WO-69 — THE WHERE-ANSWER (P5). A point and a kind both named: the three
// nearest are the answer and everything past them folds under a number.
// A WHERE-QUESTION: a point, and something asked for beside it. Either the
// landmark was lifted OUT of the query (words were left behind) or the page
// was opened at a point. A query that is ONLY a landmark is not folded — the
// reader asked what stands there, and that is the whole list.
const askedHere=!!(P&&((lm&&qFor!==q)||F.near));
const foldN=(askedHere&&onHits.length>3)?3:0;
const listHtml=foldN
?groupHtml(onHits.slice(0,foldN))+'<li class="shelf fold"><details><summary><span class="count">+'+(onHits.length-foldN+nameHits.length)+'</span></summary><ul class="dir cards">'+groupHtml(onHits.slice(foldN))+divider+groupHtml(nameHits)+'</ul></details></li>'
:groupHtml(onHits)+divider+groupHtml(nameHits);
resBox.className='dir cards';
resBox.innerHTML=(hits.length?fbar+note+stuck+panelHtml+listHtml+more
:fbar+note+stuck+panelHtml+((FT.length||F.any)?'<li class="shelf"><span class="count">0</span></li>':doors()));
if(typeof mdResMap==='function')mdResMap(hits,P,askedHere);
// Feedback at the point of failure (2026-09-06): one line, the query
// carried along, so a wrong list costs the reader one tap to report.
// AT THE POINT OF FAILURE, which is what it was called when it was added
// (2026-09-06) and was not what it did: it printed under every search,
// including the ones that worked. "Wrong results?" under a list of exactly
// the right results is a line that answers nothing and quietly suggests the
// page is unsure of itself. It appears now when the search actually
// struggled — nothing matched everything, the spelling had to be stretched,
// or there were no rows at all.
if(!hits.length||partial||worst==='loose')
resBox.insertAdjacentHTML('beforeend','<li class="shelf tellants"><a href="'+RROOT+'suggest.html?kind=other&t='+encodeURIComponent('search: '+q)+'">'+say('ผลไม่ตรง? บอกมดหน่อย','wrong results? tell the ants')+'</a></li>');
// THE NAME-EXACT ESCAPE HATCH. Held records are out of the ranked index, so
// typing one's name returned five OTHER temples with the same words in them —
// which reads as "we do not have it" about a place we do have. This runs
// whether or not there were hits, because the five-others case is the one that
// misleads. data/held.json is names only and is fetched once, on the first
// search that could match, so a reader who never types a held name never pays
// for it.
// ---- THE BEACON. What was asked, and how well we answered. ---------------
// The box has run entirely in this browser since the site existed and called
// nothing, so every question typed into motdang.net was lost the moment it was
// answered — while the demand loop behind site_gaps ran on chat traffic alone.
// This is the other 99% of the traffic finally reaching it.
//
// IT CAN NEVER COST THE READER ANYTHING. Fired after the list is drawn, with
// sendBeacon so the browser sends it on its own time and nothing awaits it;
// wrapped whole in try/catch; skipped entirely where sendBeacon does not exist
// (which is also how the node harness in tests/test_search_page.py steps over
// it). If it fails, it fails silently and the search is unaffected.
//
// WHAT GOES: the query, how many rows, the tier we matched at, the id ranked
// first, whether a landmark or a filter was in play, and any word that matched
// nothing at all. WHAT NEVER GOES: anything about the reader. No id, no
// position, no stored token. `eid` is minted per search and thrown away — it
// exists only so the click beacon below can find this row, and it must never
// be reused, or it becomes a session identifier.
try{if(MD_ASK_HOST&&typeof navigator!=='undefined'&&navigator.sendBeacon){
// The words that matched NOTHING — the vocabulary gap, which is the whole
// reason this table is worth having. "moto" was in no thesaurus, so "moto
// parking taphae" answered with one shop 4.6 km away and total confidence.
// Computed only when the search actually went wrong, so a good search pays
// nothing for it.
let unk=[];
if(partial||!found.length){for(const t of an.terms){let hit=false;
for(const [nm] of index.fields){try{if(index._resolve(t,nm,0).size){hit=true;break;}}catch(e){}}
if(!hit)unk.push(t.raw);}}
const eid=Array.from(crypto.getRandomValues(new Uint8Array(8))).map(b=>b.toString(16).padStart(2,'0')).join('');
globalThis.MD_BEACON={eid:eid,sent:false};
navigator.sendBeacon(MD_ASK_HOST+'/api/box',new Blob([JSON.stringify({
eid:eid,site:'motdang',source:F.any&&!q?'chip':'box',q:q,
resolved:{lm:(lm&&qFor!==q)?String(lm).slice(0,60):'',near:!!(F.near||P),
filters:['tag','sub','cat','st','ar'].filter(k=>F[k]&&F[k].length)},
unknown:unk.slice(0,12),n:found.length,quality:worst||'',
top:(hits[0]&&hits[0].id)?String(hits[0].id):''})],{type:'text/plain'}));
}}catch(e){}
// ---- md:search-render ends ----
mdHeldRow(q,resBox);})();}
// ---- THE OUTCOME BEACON: did the answer answer? --------------------------
// A count of results says how many rows we drew, not whether any of them was
// the thing. This is the other half: the reader opened one, or refined, or
// left. A row that stays '' forever is the honest reading of "we showed them
// results and they touched none of them" — which is the failure a result count
// cannot see and the one worth ranking work orders by.
//
// Outside the render block for the same reason WO-69 is: the DOM stub that
// tests/test_search_page.py runs the block under has no addEventListener.
// One outcome per search, ever — `sent` latches, so a reader who opens three
// results in three tabs writes one row, not three.
(function(){
if(typeof document==='undefined'||!document.addEventListener)return;
const box=document.getElementById('results');if(!box)return;
function tell(outcome){try{
const B=globalThis.MD_BEACON;
if(!B||B.sent||!MD_ASK_HOST||!navigator.sendBeacon)return;
B.sent=true;
navigator.sendBeacon(MD_ASK_HOST+'/api/box',
new Blob([JSON.stringify({eid:B.eid,outcome:outcome})],{type:'text/plain'}));
}catch(e){}}
box.addEventListener('click',function(e){
const a=e.target.closest&&e.target.closest('a[href]');if(!a)return;
// A tap on a filter chip or a shelf is the reader NARROWING, not arriving.
// Counting that as an answer would score our worst searches as our best.
if(a.classList.contains('pdoor')||a.classList.contains('rchip')){tell('refined');return;}
const m=a.getAttribute('href').match(/\/p\/([^/?#]+)\.html/);
tell(m?'opened:'+m[1].slice(0,100):'opened');},true);
// Left without touching anything. pagehide rather than unload: unload does not
// fire on a phone that switches apps, which is most of this site's traffic.
addEventListener('pagehide',function(){tell('abandoned');});
})();
// ---- WO-69: what a card does when touched -------------------------------
// Outside the render block on purpose: the DOM stub tests/test_search_page.py
// runs the block under has no addEventListener, and the block emits markup
// only. Position from MDLOC lives in memory and never in the URL.
(function(){
const box=document.getElementById('results');if(!box)return;
const RR=document.documentElement.getAttribute('data-root')||'';
let hitsNow=[],pointNow=null,mapOpen=false,mapReady=false,booted=false,cardMapEl=null,evGJ=null,evTried=false,grid=null;
const R2D=Math.PI/180;
const dM=(a,b,c,d)=>{const x=(c-a)*R2D*6371000,y=(d-b)*R2D*6371000*Math.cos((a+c)/2*R2D);return Math.sqrt(x*x+y*y);};
const fm=m=>m<1000?mdBi(Math.round(m/10)*10+' ม.',Math.round(m/10)*10+' m'):mdBi((m/1000).toFixed(1)+' กม.',(m/1000).toFixed(1)+' km');
const hx=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
// the four map files, loaded on the first tap and never before
function mapBoot(then){if(booted){then&&then();return;}booted=true;
let urls=[];try{urls=JSON.parse(document.getElementById('maphead').textContent);}catch(e){}
if(!urls.length){then&&then();return;}
const css=urls.filter(u=>/\.css/.test(u)),js=urls.filter(u=>!/\.css/.test(u));
css.forEach(u=>{const l=document.createElement('link');l.rel='stylesheet';l.href=RR+u;document.head.appendChild(l);});
let i=0;const next=()=>{if(i>=js.length){then&&then();return;}
const s=document.createElement('script');s.src=RR+js[i++];s.async=false;s.onload=next;s.onerror=next;document.head.appendChild(s);};
next();}
// the results map
const rm=document.getElementById('resmap'),rmBtn=document.getElementById('resmapbtn'),nearBtn=document.getElementById('resnear');
const gjOf=list=>({type:'FeatureCollection',features:list.filter(e=>e.lat!=null&&e.lng!=null).slice(0,200).map(e=>({type:'Feature',
geometry:{type:'Point',coordinates:[e.lng,e.lat]},properties:{id:e.id,n:e.n,e:e.e||'',p:e.p,s:e.s,su:(e.su||[])[0]||''}}))});
function drawMap(){if(!rm||!window.MDMAP)return;
const gj=gjOf(hitsNow);
window.MDMAP.ready(rm,map=>{
if(map.getSource('res'))map.getSource('res').setData(gj);
else{map.addSource('res',{type:'geojson',data:gj});
map.addLayer({id:'res-halo',type:'circle',source:'res',paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,3.2,14,5.4,17,8],'circle-color':'#FFFCF6','circle-opacity':.85}});
map.addLayer({id:'res-dot',type:'circle',source:'res',paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,2.4,14,4,17,6],'circle-color':'#C2401C','circle-opacity':.95}});
map.on('click',ev=>{const R=22,pt=ev.point;const f=map.queryRenderedFeatures([[pt.x-R,pt.y-R],[pt.x+R,pt.y+R]],{layers:['res-dot']});
if(!f.length)return;const pr=f[0].properties||{};
if(window.MDCARD)window.MDCARD.show({name:[pr.n,pr.e].filter(Boolean).join(' · '),sub:(window.MD_TAB&&window.MD_TAB.subs[pr.su])?window.MD_TAB.subs[pr.su].join(' · '):'',
href:RR+pr.p+'/p/'+pr.s+'.html',plan:pr.p+':'+pr.s,dist:pointNow?fm(dM(pointNow.lat,pointNow.lng,f[0].geometry.coordinates[1],f[0].geometry.coordinates[0])):''},rm);});
map.on('mousemove',ev=>{const f=map.queryRenderedFeatures(ev.point,{layers:['res-dot']});map.getCanvas().style.cursor=f.length?'pointer':'';});}
const pts=gj.features.map(f=>f.geometry.coordinates);
if(pointNow)map.jumpTo({center:[pointNow.lng,pointNow.lat],zoom:15});
else if(pts.length){const b=[[Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1]))],[Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))]];
try{map.fitBounds(b,{padding:24,maxZoom:16,duration:0});}catch(e){}}
mapReady=true;});}
// A MAP THAT NEVER ARRIVES MUST NOT LEAVE A HOLE. MDMAP.ready() fires only
// when the basemap's style loads, and never when the tiles fail — which is
// correct, and which would otherwise leave 280 px of empty box above the
// answer on exactly the connection this site is for. If it has not drawn in
// eight seconds the box closes again and the reader is left with the list,
// which was the answer all along.
function openMap(){if(!rm)return;mapOpen=true;rm.hidden=false;
const t=setTimeout(()=>{if(!mapReady){rm.hidden=true;mapOpen=false;}},8000);
mapBoot(()=>{rm.setAttribute('data-mdmap','1');if(window.MDMAP&&window.MDMAP.mount)window.MDMAP.mount(rm);
drawMap();const w=setInterval(()=>{if(mapReady){clearTimeout(t);clearInterval(w);}},400);
setTimeout(()=>clearInterval(w),9000);});}
function closeMap(){mapOpen=false;if(rm)rm.hidden=true;}
window.mdResMap=function(hits,P,openNow){hitsNow=hits||[];pointNow=P||pointNow;
if(rmBtn)rmBtn.hidden=!hitsNow.some(e=>e.lat!=null);
if(nearBtn)nearBtn.hidden=!hitsNow.some(e=>e.lat!=null)||!window.MDLOC;
if(openNow&&hitsNow.length)openMap();else if(mapOpen)drawMap();};
rmBtn&&rmBtn.addEventListener('click',()=>{mapOpen?closeMap():openMap();});
// near me: the position sorts the cards on the page and centres the map;
// it is never written to the URL or to storage (MDLOC's own rule)
nearBtn&&nearBtn.addEventListener('click',()=>{if(!window.MDLOC)return;
window.MDLOC.ask(pt=>{pointNow={lat:pt.lat,lng:pt.lng};
const cards=[...box.querySelectorAll('li.rcard')];
for(const c of cards){const la=parseFloat(c.dataset.lat),ln=parseFloat(c.dataset.lng);
let d=isFinite(la)&&isFinite(ln)?dM(pt.lat,pt.lng,la,ln):null;c._m=d;
let sp=c.querySelector('.dist');if(d!=null){if(!sp){sp=document.createElement('span');sp.className='count dist u';c.querySelector('.rname').after(sp);}sp.innerHTML='· '+fm(d);}}
box.querySelectorAll('li.shelf:not(.fbar):not(.stuck):not(.tellants):not(.held):not(.fold):not(.namesake)').forEach(li=>{if(li.querySelector('a[href*="/"]')&&!li.querySelector('.rchip'))li.remove();});
cards.sort((a,b)=>((a._m==null)-(b._m==null))||((a._m||0)-(b._m||0))).forEach(c=>box.appendChild(c));
openMap();});});
// the card body
function nearest3(e){if(!window.MD_IDX)return[];
if(!grid){grid=new Map();for(const x of window.MD_IDX){if(x.lat==null||x.lng==null)continue;
const k=Math.round(x.lat*200)+':'+Math.round(x.lng*200);(grid.get(k)||grid.set(k,[]).get(k)).push(x);}}
const la=Math.round(e.lat*200),ln=Math.round(e.lng*200),out=[];
for(let i=-1;i<=1;i++)for(let j=-1;j<=1;j++)for(const x of(grid.get((la+i)+':'+(ln+j))||[])){if(x.id===e.id)continue;out.push([dM(e.lat,e.lng,x.lat,x.lng),x]);}
return out.sort((a,b)=>a[0]-b[0]).slice(0,3);}
function fill(card){const id=card.dataset.id,e=(window.MD_IDX||[]).find(x=>x.id===id);const pn=card.querySelector('.rpanel');if(!e||!pn)return;
const T=window.MD_TAB||{subs:{}};const su=(e.su||[])[0]||(e.c||[])[0];
let h='';
if(e.lat!=null){h+='<div class="cardmapslot"></div>';
// NO METRES INSIDE THE NOISE OF A PIN. 2,958 rows sit on a coordinate
// shared with another record — a tambon or postcode centroid stacks every
// place it placed on one point, and one Chiang Rai centroid carries 145.
// Three neighbours reading "0 ม." is a false fact stated three times; the
// places are real and the distance between them is not known.
const nb=nearest3(e);if(nb.length)h+='<p class="rnear">'+nb.map(([d,x])=>'<a href="'+RR+x.p+'/p/'+x.s+'.html">'+hx(x.n)+'</a>'+(d>=25?' <span class="count dist u">'+fm(d)+'</span>':'')).join(' · ')+'</p>';
if(su)h+='<p class="rsame"><a href="'+RR+'search.html?'+(e.su&&e.su[0]?'sub=':'cat=')+encodeURIComponent(su)+'&near='+e.lat+','+e.lng+'">'+(T.subs[su]?mdBi(T.subs[su][0],T.subs[su][1]):(MD_CATWORDS[su]||hx(su)))+' 📍</a></p>';}
h+='<p class="rdo"><button type="button" class="planbtn planbtn-lg" data-plan="'+hx(card.dataset.plan)+'"><span class="off-label">'+mdBi('เพิ่มลงแผน','Add to plan')+'</span><span class="on-label">'+mdBi('อยู่ในแผน','In plan')+'</span></button>'+
' <a class="ropen" href="'+RR+e.p+'/p/'+e.s+'.html">'+mdBi('เปิดหน้านี้','Open this page')+'</a></p>';
h+='<p class="revents"></p>';
pn.innerHTML=h;
const pb=pn.querySelector('.planbtn');if(pb&&typeof planGet==='function'){pb.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();
const k=pb.dataset.plan,list=planGet(),i=list.indexOf(k);if(i>-1)list.splice(i,1);else if(list.length<PLAN_MAX)list.push(k);planSet(list);});planPaint();}
if(e.lat!=null){const slot=pn.querySelector('.cardmapslot');
if(!cardMapEl){cardMapEl=document.createElement('div');cardMapEl.id='cardmap';cardMapEl.className='mdmap cardmap';cardMapEl.innerHTML='<div class="mdmap-draw"></div>';}
cardMapEl.dataset.lat=e.lat;cardMapEl.dataset.lng=e.lng;cardMapEl.dataset.zoom='16';slot.appendChild(cardMapEl);
mapBoot(()=>{if(!window.MDMAP)return;const m=window.MDMAP.map(cardMapEl);
if(m){m.resize();m.jumpTo({center:[e.lng,e.lat],zoom:16});}
else{cardMapEl.setAttribute('data-mdmap','1');window.MDMAP.mount&&window.MDMAP.mount(cardMapEl);}});
const ev=pn.querySelector('.revents');const paint=()=>{if(!evGJ)return;const mine=(evGJ.features||[]).filter(f=>(f.properties||{}).placeId===id);
ev.innerHTML=mine.map(f=>'🎪 '+hx(f.properties.title||'')+(f.properties.start?' <span class="count">'+hx(f.properties.start)+'</span>':'')).join('<br>');};
if(evGJ)paint();else if(!evTried){evTried=true;fetch(RR+'data/events.geojson').then(r=>r.ok?r.json():null).then(d=>{evGJ=d;paint();}).catch(()=>{});}}}
box.addEventListener('click',ev=>{const t=ev.target;
const pin=t.closest&&t.closest('.rpin');const card=t.closest&&t.closest('li.rcard');
if(!card)return;
if(pin){ev.preventDefault();const la=parseFloat(card.dataset.lat),ln=parseFloat(card.dataset.lng);
openMap();if(window.MDMAP&&rm){window.MDMAP.ready(rm,map=>{map.jumpTo({center:[ln,la],zoom:16});
if(window.MDCARD){const e=(window.MD_IDX||[]).find(x=>x.id===card.dataset.id)||{};window.MDCARD.show({name:[e.n,e.e].filter(Boolean).join(' · '),sub:'',href:RR+e.p+'/p/'+e.s+'.html',plan:card.dataset.plan},rm);}});}
return;}
if(t.closest('a')||t.closest('button')||t.closest('.rpanel'))return;
const pn=card.querySelector('.rpanel');if(!pn)return;
const open=!pn.hidden;
box.querySelectorAll('li.rcard.open').forEach(c=>{c.classList.remove('open');const p=c.querySelector('.rpanel');if(p)p.hidden=true;});
if(!open){card.classList.add('open');if(!pn.innerHTML)fill(card);else if(cardMapEl&&pn.contains(cardMapEl)===false&&pn.querySelector('.cardmapslot')){pn.querySelector('.cardmapslot').appendChild(cardMapEl);}
pn.hidden=false;
if(cardMapEl&&window.MDMAP){const e=(window.MD_IDX||[]).find(x=>x.id===card.dataset.id);const m=window.MDMAP.map(cardMapEl);if(m&&e&&e.lat!=null){m.resize();m.jumpTo({center:[e.lng,e.lat],zoom:16});}}}});
})();
let MD_HELD=null,MD_HELD_TRIED=false;
async function mdHeldRow(q,box){
 const k=(q||'').replace(/\s+/g,'').toLowerCase();
 if(k.length<4)return;
 if(!MD_HELD&&!MD_HELD_TRIED){MD_HELD_TRIED=true;MD_HELD=await mdJSON('data/held.json');}
 if(!MD_HELD)return;
 // Exact first. Only if nothing is exact does it accept the typed name being
 // the whole of a held name's start — never a loose substring, which would
 // hand back a wrong place with total confidence.
 let hit=MD_HELD[k]||null;
 if(!hit){for(const key in MD_HELD){if(key.startsWith(k)&&k.length>=6){hit=MD_HELD[key];break;}}}
 if(!hit)return;
 const li=document.createElement('li');
 li.className='shelf held';
 li.innerHTML='<a href="'+RROOT+hit[1]+'">'+hit[0]+'</a> <span class="badge pin">'+mdBi('ยังไม่มีพิกัด','no pin')+'</span>'+
  ' · <a href="'+RROOT+'pins.html">'+mdBi('ช่วยเติม','fill it in')+'</a>';
 box.insertBefore(li,box.firstChild);}
// ---- today's sky + fortune, chosen from a month baked at build time ---
// Nothing is fetched: build.py wrote 30 days into these files, so the page is
// right every morning without a rebuild and still makes no outside request.
const MD_TODAY=(()=>{const d=new Date();
return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');})();
async function mdJSON(p){try{const r=await fetch(RROOT+p);return r.ok?await r.json():null;}
catch(e){return null;}}
// Today or nothing. This used to fall back to the earliest baked day, so once
// the window ran out every reader was quietly handed a month-old reading with
// today's date on it. A tile with no entry for today says so instead.
function mdPick(doc){if(!doc||!doc.days)return null;
return doc.days[MD_TODAY]||null;}
function mdStale(sel){document.querySelectorAll(sel).forEach(el=>{
if(el.querySelector('.wstale'))return;
const s=document.createElement('span');s.className='wfoot wstale';
s.innerHTML=mdBi('ยังไม่ได้อัปเดตสำหรับวันนี้','not updated for today');
el.appendChild(s);});}
// --- freshness strip: relative wording computed in the reader's browser,
// so it cannot rot the way a baked "today" would. Stamps are Thai wall time.
(function(){const els=document.querySelectorAll('[data-freshts]');if(!els.length)return;
function mdRel(ts){
const dateOnly=/^\d{4}-\d{2}-\d{2}$/.test(ts);
if(dateOnly){const today=MD_TODAY;
if(ts===today)return ['วันนี้','today'];
const days=Math.round((new Date(today+'T12:00')-new Date(ts+'T12:00'))/864e5);
if(days===1)return ['เมื่อวาน','yesterday'];
if(days>1)return [days+' วันที่แล้ว',days+'d ago'];
return ['วันนี้','today'];}
const d=new Date(ts.replace(' ','T'));if(isNaN(d))return null;
const mins=Math.round((Date.now()-d)/6e4);
if(mins<2)return ['เมื่อกี้','just now'];
if(mins<60)return [mins+' นาทีที่แล้ว',mins+'m ago'];
const h=Math.round(mins/60);
if(h<24)return [h+' ชม.ที่แล้ว',h+'h ago'];
const days=Math.round(h/24);
if(days===1)return ['เมื่อวาน','yesterday'];
return [days+' วันที่แล้ว',days+'d ago'];}
els.forEach(el=>{const ts=el.dataset.freshts||'';const r=mdRel(ts);
const s=el.querySelector('.freshrel');if(!r||!s)return;
s.innerHTML=mdBi(r[0],r[1]);
const age=(Date.now()-new Date(ts.replace(' ','T')+(ts.length===10?'T12:00':'')))/864e5;
if(age>2.2)el.classList.add('quiet');});})();
// --- coming up (WO-41 4d): a static page cannot know what day it is being
// read, so every row carries its own end date and the reader's clock does the
// pruning. The strip stays right even if every walk stops; ISO strings
// compare as strings.
(function(){const cus=document.querySelectorAll('.comingup');if(!cus.length)return;
cus.forEach(cu=>{
cu.querySelectorAll('[data-until]').forEach(el=>{if((el.dataset.until||'')<MD_TODAY)el.remove();});
cu.querySelectorAll('.cuaround').forEach(p=>{if(!p.querySelector('.cuitem'))p.remove();});
const ul=cu.querySelector('ul');if(ul&&!ul.querySelector('li'))ul.remove();
if(!cu.querySelector('li')&&!cu.querySelector('.cuaround')){(cu.closest('.comingupcard')||cu).remove();}});})();
// --- sky tile: moon + jupiter, drawn from baked positions
(async()=>{const host=document.getElementById('w-sky');if(!host)return;
const doc=await mdJSON('data/sky.json');const day=mdPick(doc);
if(!day){mdStale('#w-sky');return;}
const mc=host.querySelector('[data-skycap="moon"]');
// Through mdBi, not hand-built spans: building the pair by hand is what left
// "แรม 4 ค่ำWaning" jammed together with no separator, the same fault the
// Thai horoscope line had.
if(mc&&day.moon)mc.innerHTML=mdBi(
day.moon.phase_th+' · '+day.moon.thai_label_th+(day.moon.wan_phra?' · วันพระ':''),
day.moon.phase_en+' · '+day.moon.thai_label_en+(day.moon.wan_phra?' · wan phra':''));
const slides=[...host.querySelectorAll('.skyslide')];
const dots=[...host.querySelectorAll('[data-skydot]')];let si=0;
const go=i=>{si=(i+slides.length)%slides.length;
slides.forEach((s,n)=>{s.hidden=n!==si;});
dots.forEach((d,n)=>d.classList.toggle('on',n===si));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.skydot);clearInterval(window.__skyT);}));
if(slides.length>1)window.__skyT=setInterval(()=>go(si+1),6000);})();
// --- fortune, horoscope, hexagram, and the day's colour
(async()=>{const doc=await mdJSON('data/fortune.json');const day=mdPick(doc);
if(!day){mdStale('#w-fortune,#w-divination');return;}
const t=day.thai;
// สีประจำวัน: the whole page borrows the day's colour
if(t&&t.hex)document.documentElement.style.setProperty('--day',t.hex);
const setF=(k,v)=>{const el=document.querySelector(`[data-fo="${k}"]`);if(el&&v!=null)el.textContent=v;};
if(t){setF('day_th',t.th);setF('strength',t.strength);setF('zodiac',t.zodiac_year_th);
const sw=document.querySelector('[data-fo="swatch"]');if(sw)sw.style.background=t.hex;
const bl=(sel,a,b)=>{const el=document.querySelector(sel);
if(el)el.innerHTML=mdBi(a,b);};
bl('[data-fo="colour"]',t.colour_th,t.colour_en);
bl('[data-fo="buddha"]',t.buddha_th,t.buddha_en);
bl('[data-fo="planet"]',t.planet_th,t.planet_en);
bl('[data-fo="how"]',t.lucky.how_th,t.lucky.how_en);
setF('nums',t.lucky.two.join(' ')+' · '+t.lucky.three);}
// The horoscope tile is horo.js's now — per-sign, computed live from
// data/horo.json, no baked window to fall off. Only the tab chrome and the
// day colour above still belong to this file.
// hexagram: draw the six lines from the king wen number
const hx=day.hexagram;
if(hx&&hx.number){const box=document.querySelector('[data-hx="lines"]');
const set=(k,v)=>{const e=document.querySelector(`[data-hx="${k}"]`);if(e&&v!=null)e.textContent=v;};
set('zh',hx.zh);set('pinyin',hx.pinyin);set('en',hx.en);set('gloss',hx.gloss);
if(box&&hx.bits){box.innerHTML=hx.bits.slice().reverse().map((b,i)=>
`<span class="hxline ${b?'yang':'yin'} ${hx.moving&&hx.moving.includes(6-i)?'moving':''}"></span>`).join('');}}
// tabs
document.querySelectorAll('.hotab').forEach(b=>{b.addEventListener('click',()=>{
document.querySelectorAll('.hotab').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('.hopane').forEach(p=>{p.hidden=p.dataset.hopane!==b.dataset.hotab;});});});
})();
// --- katha + psalms + 8-ball live in shuffle.js (per-bead cycle, not a carousel)
// --- เซียมซี: shake, a stick falls, read the slip
(()=>{const host=document.getElementById('w-siamsi');if(!host)return;
let sticks=[];try{sticks=JSON.parse(host.dataset.siamsi||'[]');}catch(e){return;}
if(!sticks.length)return;
const tube=host.querySelector('[data-ss="tube"]'),out=host.querySelector('[data-ss="out"]'),
btn=host.querySelector('[data-ss="shake"]');
const V={'ดี':['ดี','good'],'กลาง':['กลาง','middling'],'ระวัง':['ระวัง','take care']};
btn.addEventListener('click',()=>{
if(tube.classList.contains('shaking'))return;
tube.classList.add('shaking');out.hidden=true;
setTimeout(()=>{tube.classList.remove('shaking');
const s=sticks[Math.floor(Math.random()*sticks.length)];
host.querySelector('[data-ss="num"]').textContent='ใบที่ '+s.n;
const v=V[s.verdict]||[s.verdict,s.verdict];
const vd=host.querySelector('[data-ss="verdict"]');
vd.innerHTML=mdBi(v[0],v[1]);
vd.className='ssverdict v-'+(s.verdict==='ดี'?'good':s.verdict==='ระวัง'?'care':'mid');
host.querySelector('[data-ss="text"]').innerHTML=
mdBi(s.th,s.en);
// the slip points somewhere in the directory: unhide the door for this verdict
host.querySelectorAll('.ssdoor').forEach(d=>{d.hidden=d.dataset.ssdoor!==s.verdict;});
out.hidden=false;},900);});})();
// ---- widgets: choices live in localStorage, no account --
function wLoad(k,d){try{const v=JSON.parse(localStorage.getItem(k));
return Array.isArray(v)?v:d;}catch(e){return d;}}
function wSave(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
// gear buttons flip a tile to its picker
document.querySelectorAll('.wcog').forEach(b=>{b.addEventListener('click',()=>{
const p=document.querySelector(`.wpick[data-wpickfor="${b.dataset.wpick}"]`);
if(p)p.hidden=!p.hidden;});});
document.querySelectorAll('.wpick').forEach(p=>{p.addEventListener('click',e=>{
if(e.target===p)p.hidden=true;});});
// --- weather: rotate through the cities the reader picked
const wxPanes=[...document.querySelectorAll('.wxpane')];
if(wxPanes.length){
let wxSel=wLoad('md.wx',['chiang-mai','chiang-rai','reunion']);
const wxBoxes=[...document.querySelectorAll('[data-wxc]')];
const wxDraw=()=>{if(!wxSel.length)wxSel=['chiang-mai'];
wxPanes.forEach(p=>{p.hidden=true;});
let i=0;const show=()=>{const id=wxSel[i%wxSel.length];
wxPanes.forEach(p=>{p.hidden=p.dataset.wxpane!==id;});i++;};
show();clearInterval(window.__wxT);
if(wxSel.length>1)window.__wxT=setInterval(show,4000);};
wxBoxes.forEach(b=>{b.checked=wxSel.includes(b.dataset.wxc);
b.addEventListener('change',()=>{wxSel=wxBoxes.filter(x=>x.checked).map(x=>x.dataset.wxc);
wSave('md.wx',wxSel);wxDraw();});});
wxDraw();}
// --- air: same picker as the weather tile, its own stored choice
const airPanes=[...document.querySelectorAll('.airpane')];
if(airPanes.length){
let airSel=wLoad('md.air',['chiang-mai']);
const airBoxes=[...document.querySelectorAll('[data-airc]')];
const airDraw=()=>{if(!airSel.length)airSel=['chiang-mai'];
airPanes.forEach(p=>{p.hidden=true;});
let i=0;const show=()=>{const id=airSel[i%airSel.length];
airPanes.forEach(p=>{p.hidden=p.dataset.airpane!==id;});i++;};
show();clearInterval(window.__airT);
if(airSel.length>1)window.__airT=setInterval(show,4000);};
airBoxes.forEach(b=>{b.checked=airSel.includes(b.dataset.airc);
b.addEventListener('change',()=>{airSel=airBoxes.filter(x=>x.checked).map(x=>x.dataset.airc);
wSave('md.air',airSel);airDraw();});});
airDraw();}
// --- clocks: Intl does the conversion, so nothing is fetched
const tzRows=[...document.querySelectorAll('.tzrow')];
if(tzRows.length){
let tzSel=wLoad('md.tz',['chiang-mai','london','new-york']);
const tzBoxes=[...document.querySelectorAll('[data-tzc]')];
const shift=document.getElementById('tzshift'),shiftOut=document.getElementById('tzshiftout');
const tzDraw=()=>{const off=shift?parseInt(shift.value,10):0;
if(shiftOut)shiftOut.textContent=(off>0?'+':'')+off+'h';
const base=new Date(Date.now()+off*3600000);
tzRows.forEach(r=>{const on=tzSel.includes(r.dataset.tzrow);r.hidden=!on;
if(!on)return;
try{const f=new Intl.DateTimeFormat('en-GB',{timeZone:r.dataset.tz,hour:'2-digit',
minute:'2-digit',hour12:false});
const d=new Intl.DateTimeFormat('en-GB',{timeZone:r.dataset.tz,weekday:'short'});
r.querySelector('.tztime').textContent=f.format(base);
r.querySelector('.tzday').textContent=d.format(base);}catch(e){}});};
tzBoxes.forEach(b=>{b.checked=tzSel.includes(b.dataset.tzc);
b.addEventListener('change',()=>{tzSel=tzBoxes.filter(x=>x.checked).map(x=>x.dataset.tzc);
wSave('md.tz',tzSel);tzDraw();});});
if(shift)shift.addEventListener('input',tzDraw);
tzDraw();setInterval(tzDraw,15000);}
// --- cinema: one pane per screen
const cnPick=document.querySelector('.cnpick');
if(cnPick){const panes=[...document.querySelectorAll('[data-cnpane]')];
const cnDraw=()=>{panes.forEach(p=>{p.hidden=p.dataset.cnpane!==cnPick.value;});};
const saved=localStorage.getItem('md.cn');
if(saved&&[...cnPick.options].some(o=>o.value===saved))cnPick.value=saved;
cnPick.addEventListener('change',()=>{try{localStorage.setItem('md.cn',cnPick.value);}catch(e){}
cnDraw();});cnDraw();}
// --- showtimes: fade the screenings that have already started. Only when the
// baked sheet really is today's; on any other day the tile stops saying
// "today" — it retitles itself with the day the sheet belongs to and wears
// the same not-updated note the fortune tiles use. A four-day-old Saturday
// sheet presented as tonight is the tile lying.
(()=>{const host=document.getElementById('w-cinema');if(!host)return;
if(host.dataset.cndate!==MD_TODAY){
const h=host.querySelector('h3');
if(h&&host.dataset.cnth)h.innerHTML='🎬 '+mdBi(host.dataset.cnth,host.dataset.cnen||host.dataset.cnth);
mdStale('#w-cinema');return;}
const mark=()=>{const n=new Date(),hm=n.getHours()*60+n.getMinutes();
host.querySelectorAll('.cnt').forEach(el=>{const p=(el.dataset.t||'').split(':');
if(p.length!==2)return;
el.classList.toggle('past',(+p[0])*60+(+p[1])<hm);});};
mark();setInterval(mark,60000);})();
// --- weather: the conditions block is a snapshot. The footer already dates
// it; once the snapshot is not from today, say so where the eye is.
(()=>{const w=document.getElementById('w-weather');if(!w)return;
const g=(w.dataset.wxgen||'').slice(0,10);
if(g&&g!==MD_TODAY)mdStale('#w-weather');})();
// --- events carousel
const carousel=document.querySelector('[data-carousel]');
if(carousel){const slides=[...carousel.querySelectorAll('.evslide')];
const dots=[...document.querySelectorAll('[data-evdot]')];let ci=0;
const go=i=>{ci=(i+slides.length)%slides.length;
slides.forEach((s,n)=>{s.hidden=n!==ci;});
dots.forEach((d,n)=>d.classList.toggle('on',n===ci));};
dots.forEach(d=>d.addEventListener('click',()=>{go(+d.dataset.evdot);
clearInterval(window.__evT);}));
if(slides.length>1)window.__evT=setInterval(()=>go(ci+1),5000);}
// ---- events page filters --------------------------------------------
const evf=document.getElementById('evfilters');
if(evf){const cards=[...document.querySelectorAll('.evcard')];
evf.querySelectorAll('button').forEach(b=>{b.addEventListener('click',()=>{
evf.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
b.classList.add('on');const f=b.dataset.evf;
cards.forEach(c=>{const rec=c.dataset.recurring==='1',map=c.dataset.mapped==='1';
const show=f==='all'||(f==='recurring'&&rec)||(f==='once'&&!rec)||(f==='mapped'&&map);
c.style.display=show?'':'none';});
// hide a day/month heading whose whole grid just went empty
document.querySelectorAll('.evgrid').forEach(g=>{
const any=[...g.children].some(c=>c.style.display!=='none');
g.style.display=any?'':'none';
const h=g.previousElementSibling;
if(h&&h.classList.contains('evday'))h.style.display=any?'':'none';});});});}
// ---- random place (🎲) ----------------------------------------------
document.querySelectorAll('.rand').forEach(a=>{a.addEventListener('click',async e=>{
e.preventDefault();const idx=await loadIndex();
const pick=idx[Math.floor(Math.random()*idx.length)];
location.href=RROOT+pick.p+'/p/'+pick.s+'.html';});});
// ---- sort toolbar: name / distance ----------------------------------
// ก→ฮ sorts by the name the reader can actually see. A row carries both, and
// in English-only mode sorting by the Thai one puts every list in an order
// that reads as no order at all.
function mdSortKey(el){
return (B.classList.contains('lang-en')&&el.dataset.ne)||el.dataset.n||'';}
const dirList=document.querySelector('ul.dir[data-sortable]');
// ---- MDCARD: what a touch on a map is worth ---------------------------
// Every map on this site could be touched and only one of them answered —
// the toilets page, which moves your starting point. Everywhere else a tap
// on the ground reached a listener nobody had written, and a tap on a
// neighbour's dot either did nothing or teleported the reader to another
// page with no warning and no way back but the back button.
//
// So: one card, opened by any map, saying what was touched and offering the
// two things a reader wants next — go there, or keep it for the errand run.
// The rules it is built on:
//   * The first touch NEVER navigates. A finger is 44 px wide and a dot is
//     four; on a shelf of four thousand places the wrong page is one pixel
//     away, and on cell data a wrong page is a real cost. Touch names it,
//     the button opens it.
//   * It is a sheet at the bottom of the SCREEN, not a bubble over the pin.
//     A bubble over a pin covers the neighbours you are comparing it with,
//     and on a 360-wide phone there is nowhere for it to go.
//   * It never invents. Name, shelf and rank are read off the row or the
//     mark that was touched; the distance is only shown when the map knows
//     both ends of it.
// Nothing here is required for a map to work: with scripting off the drawn
// links are still links, and that is still the fallback.
const MDCARD=(()=>{
let el=null,btnClose=null,elName=null,elSub=null,elMeta=null,elOpen=null,elPlan=null;
let lastFocus=null,cur=null;
const build=()=>{
if(el)return el;
el=document.createElement('div');
el.className='mdcard';el.hidden=true;
el.setAttribute('role','dialog');
el.setAttribute('aria-label','จุดที่เลือกบนแผนที่ · the place you touched on the map');
el.innerHTML='<div class="mdcard-in">'+
'<button type="button" class="mdcard-x" aria-label="ปิด · Close">×</button>'+
'<p class="mdcard-name"></p><p class="mdcard-sub"></p><p class="mdcard-meta"></p>'+
'<div class="mdcard-do"><a class="mdcard-open" href="#"></a>'+
'<button type="button" class="mdcard-plan planbtn" aria-pressed="false"></button>'+
'</div></div>';
document.body.appendChild(el);
btnClose=el.querySelector('.mdcard-x');elName=el.querySelector('.mdcard-name');
elSub=el.querySelector('.mdcard-sub');elMeta=el.querySelector('.mdcard-meta');
elOpen=el.querySelector('.mdcard-open');elPlan=el.querySelector('.mdcard-plan');
btnClose.addEventListener('click',()=>hide());
// A tap on the ground outside the card puts it away, the way a sheet should.
// Inside it, nothing closes but the buttons.
document.addEventListener('click',ev=>{
if(el.hidden||el.contains(ev.target))return;
if(ev.target.closest&&ev.target.closest('.mdmap'))return;   // the map speaks for itself
hide();},true);
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&!el.hidden)hide();});
elPlan.addEventListener('click',()=>{
if(!cur||!cur.plan)return;
const list=planGet(),i=list.indexOf(cur.plan);
if(i>-1)list.splice(i,1);
else if(list.length>=PLAN_MAX){
alert('แผนหนึ่งเก็บได้ '+PLAN_MAX+' จุด / a plan holds '+PLAN_MAX+' stops');return;}
else list.push(cur.plan);
planSet(list);          // repaints every ring on the page, this one included
paintPlan();});
return el;};
const paintPlan=()=>{
if(!cur)return;
if(!cur.plan){elPlan.hidden=true;return;}
elPlan.hidden=false;
const on=planGet().indexOf(cur.plan)>-1;
elPlan.classList.toggle('on',on);
elPlan.setAttribute('aria-pressed',on?'true':'false');
elPlan.innerHTML=on?mdBi('เอาออกจากแผน','Remove from plan')
:mdBi('🧭 เพิ่มลงแผน','Add to my plan');};
const hide=()=>{
if(!el||el.hidden)return;
el.hidden=true;cur=null;
if(lastFocus&&lastFocus.focus){try{lastFocus.focus();}catch(e){}}
lastFocus=null;};
// item: {name, nameEn, sub, href, plan, rank, dist}
const show=(item,opener)=>{
if(!item||!item.name)return;
build();cur=item;
lastFocus=opener||document.activeElement;
elName.textContent=item.name;
elSub.textContent=item.sub||'';elSub.hidden=!item.sub;
const bits=[];
if(item.rank)bits.push('🐜'+item.rank);
if(item.dist)bits.push(item.dist);
elMeta.textContent=bits.join('  ·  ');elMeta.hidden=!bits.length;
if(item.href){elOpen.hidden=false;elOpen.href=item.href;
elOpen.innerHTML=mdBi('เปิดหน้านี้','Open this page');}
else elOpen.hidden=true;
paintPlan();
el.hidden=false;
// Focus the card itself, not its first button: a reader arriving here has
// not chosen to leave the page yet, and the name is what they asked for.
elName.setAttribute('tabindex','-1');
try{elName.focus({preventScroll:true});}catch(e){}};
return{show,hide,
// How far apart two coordinates are, in the words this site uses for it.
// Lives here because three different maps needed the same sentence.
gap:(a,b)=>{const R=6371000,dLa=(b.lat-a.lat)*Math.PI/180,dLo=(b.lng-a.lng)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLo/2)**2;
const m=2*R*Math.asin(Math.sqrt(h));
return m<950?Math.round(m/10)*10+' ม./m':(m/1000).toFixed(1)+' กม./km';}};
})();
window.MDCARD=MDCARD;

// ---- neighbours on a place map answer with a card ---------------------
// They are real links and they stay real links — this only steps in front of
// a plain left click. Middle-click, ctrl/cmd-click and "open in new tab" all
// pass through untouched, and with scripting off the link is the whole
// feature. What it buys: the wrong dot costs a glance instead of a page load,
// and the right dot can go straight into the errand run without opening it.
(function(){
const holder=document.querySelector('.mdmap[data-lat]');if(!holder)return;
const nbs=[...holder.querySelectorAll('.nbs a[data-n]')];
if(!nbs.length)return;
const here={lat:parseFloat(holder.dataset.lat),lng:parseFloat(holder.dataset.lng)};
const open=(a,by)=>{
const la=parseFloat(a.dataset.lat),ln=parseFloat(a.dataset.lng);
MDCARD.show({name:a.dataset.n,sub:a.dataset.sub||'',href:a.getAttribute('href'),
plan:a.dataset.plan||'',rank:a.dataset.rank||'',
dist:isFinite(la)&&isFinite(ln)&&isFinite(here.lat)
?MDCARD.gap(here,{lat:la,lng:ln})+' จากที่นี่ · from here':''},by);};
nbs.forEach(a=>{a.addEventListener('click',ev=>{
if(ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey||ev.button)return;
ev.preventDefault();open(a,a);});});
// The near miss, and the tap on bare ground. The disc drawn round each dot
// is a margin, not a fingertip — the rest of the tolerance is here, where
// the reader's real pixels can be measured: whatever was touched, the
// nearest dot within about a fingertip answers. Below that it was a tap on
// the city, and the city is allowed to say nothing.
const nearest=(cx,cy)=>{
let best=null,bd=34*34;                    // ~a fingertip's radius, in CSS px
for(const a of nbs){
const r=a.getBoundingClientRect();
if(!r.width&&!r.height)continue;           // omitted or off-frame
const dx=r.left+r.width/2-cx,dy=r.top+r.height/2-cy,d=dx*dx+dy*dy;
if(d<bd){bd=d;best=a;}}
return best;};
holder.addEventListener('click',ev=>{
if(ev.target.closest&&ev.target.closest('.nbs a'))return;   // already answered
const a=nearest(ev.clientX,ev.clientY);
if(a)open(a,holder);});
// And the same question asked by the basemap itself, which reports taps in
// coordinates rather than pixels — the event that had one listener on this
// whole site until now.
holder.addEventListener('mdmap:click',ev=>{
const p=ev.detail;if(!p)return;
let best=null,bd=Infinity;
for(const a of nbs){
const la=parseFloat(a.dataset.lat),ln=parseFloat(a.dataset.lng);
if(!isFinite(la)||!isFinite(ln))continue;
const d=(la-p.lat)*(la-p.lat)+(ln-p.lng)*(ln-p.lng);
if(d<bd){bd=d;best=a;}}
// About 60 m at this latitude, in squared degrees — a tap has to land on
// something, not merely nearer one dot than another across a whole frame.
if(best&&bd<3e-7)open(best,holder);});
})();

if(dirList){
// Place rows carry data-n; the brand shelves and road headings around them do
// not. Asking for the rows themselves rather than for the list's children is
// what lets a row live inside a folded <details> and still be sorted, filtered
// and counted with all the others.
const items=[...dirList.querySelectorAll('li[data-n]')];
// Any explicit sort or filter abandons the fold: the reader has asked for one
// order across everything, and rows still tucked behind a closed triangle
// would be an answer they cannot see. Rows come up to the top level and the
// empty shelves go.
const unfold=()=>{items.forEach(li=>dirList.appendChild(li));
dirList.querySelectorAll('li.brandshelf,li.areahead').forEach(h=>h.remove());};
const byName=document.getElementById('sort-name'),byDist=document.getElementById('sort-dist');
byName&&byName.addEventListener('click',()=>{
items.sort((a,b)=>mdSortKey(a).localeCompare(mdSortKey(b),'th'));
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
dirList.classList.remove('ranked');
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byName.classList.add('on');});
// Sorting by distance from a point the reader granted us. The old version
// called getCurrentPosition straight off the tap and, when that was refused,
// raised an alert() — a dead end whose only cause was "no location", which
// is precisely the screen this site must never show.
const sortByDist=pt=>{const R=6371;
items.forEach(li=>{const lat=parseFloat(li.dataset.lat),lng=parseFloat(li.dataset.lng);
if(isNaN(lat)){li.dataset.km=1e9;return;}
const dLa=(lat-pt.lat)*Math.PI/180,dLo=(lng-pt.lng)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(pt.lat*Math.PI/180)*Math.cos(lat*Math.PI/180)*Math.sin(dLo/2)**2;
li.dataset.km=2*R*Math.asin(Math.sqrt(h));});
items.sort((a,b)=>a.dataset.km-b.dataset.km);
items.forEach(li=>{let d=li.querySelector('.dist');const km=parseFloat(li.dataset.km);
if(km<1e8){if(!d){d=document.createElement('span');d.className='dist';li.appendChild(d);}
d.textContent=' · '+(km<1?Math.round(km*1000)+' ม.':km.toFixed(1)+' กม.');}
dirList.appendChild(li);});
dirList.classList.remove('ranked');
document.querySelectorAll('.toolbar button').forEach(x=>x.classList.remove('on'));
byDist&&byDist.classList.add('on');};
// Refused, or already denied at the OS level. The list still sorts — by name,
// which is the order it was in — and the distance door removes itself rather
// than sitting there waiting to ask again.
const distDeclined=()=>{byName&&byName.click();};
byDist&&byDist.addEventListener('click',()=>{MDLOC.ask(sortByDist,distDeclined);});
// ---- ant rank sorts: most complete / recently walked / needs love ----
// The two completeness sorts also reveal the per-row 🐜N chips (.ranked on
// the list): once the reader has asked "which listings are filled in", the
// score is the subject and hiding it makes the sort look broken. Every other
// order puts the chips away again.
const btns=[...document.querySelectorAll('.toolbar button')];
const reorder=(btn,cmp,ants)=>{if(!btn)return;btn.addEventListener('click',()=>{
items.sort(cmp);
items.forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});
dirList.classList.toggle('ranked',!!ants);
btns.forEach(x=>x&&x.classList.remove('on'));btn.classList.add('on');});};
const nm=(a,b)=>mdSortKey(a).localeCompare(mdSortKey(b),'th');
const rk=li=>parseInt(li.dataset.rank||'0',10);
reorder(document.getElementById('sort-rank'),(a,b)=>rk(b)-rk(a)||nm(a,b),true);
reorder(document.getElementById('sort-love'),(a,b)=>rk(a)-rk(b)||nm(a,b),true);
const rw=li=>parseInt(li.dataset.royal||'0',10);
reorder(document.getElementById('sort-royal'),(a,b)=>rw(b)-rw(a)||nm(a,b));
reorder(document.getElementById('sort-hon'),
(a,b)=>(parseInt(b.dataset.hon||'0',10)-parseInt(a.dataset.hon||'0',10))||rk(b)-rk(a)||nm(a,b));
// ---- the shelf map, made answerable ----------------------------------
// The dots are one <path>, so there is nothing to hover. Instead the points
// are held as plain numbers and the nearest one to the pointer is found on
// each move — a few thousand comparisons, which is nothing, and it means a
// four-thousand-place shelf answers as fast as a forty-place one. Everything
// below degrades to the drawn map if scripting is off, which is the state the
// page was already in.
(function(){const box=document.querySelector('.mdmap .shelfmap');if(!box)return;
const holder=box.closest('.mdmap');
const tag=holder&&holder.querySelector('.sm-pts');if(!tag)return;
let RAW=[];try{RAW=JSON.parse(tag.textContent||'[]');}catch(e){return;}
if(!RAW.length)return;
// Each point is [x, y, rowIndex]. The row itself holds the name, the link, the
// facets and the ant rank — read from the DOM at hover time rather than
// shipped twice.
const rows=[...dirList.querySelectorAll('li')].filter(li=>li.dataset.n!==undefined);
const PTS=RAW.map(a=>({x:a[0],y:a[1],li:rows[a[2]]})).filter(p=>p.li);
const hi=box.querySelector('.sm-hi'),base=box.querySelector('.sm-base');
const hov=box.querySelector('.sm-hover');
const hc=hov&&hov.querySelector('circle'),ht=hov&&hov.querySelector('text');
const vb=(box.getAttribute('viewBox')||'0 0 720 400').split(/\s+/).map(Number);
let live=PTS,near=null;
const draw=list=>{if(!hi)return;
hi.setAttribute('d',list.length===PTS.length?'':list.map(p=>'M'+p.x+' '+p.y+'h0').join(''));
base&&base.setAttribute('opacity',list.length===PTS.length?'.5':'.16');};
// Pointer position in the drawing's own coordinates, so it keeps agreeing with
// the dots after the box is resized or the tiles under it are zoomed.
const at=ev=>{const r=box.getBoundingClientRect();
return[(ev.clientX-r.left)/r.width*vb[2],(ev.clientY-r.top)/r.height*vb[3]];};
// How many drawing units a CSS pixel is worth, right now. The drawing is laid
// out at whatever width the column gives it and then scaled again by the
// basemap under it, so a radius written as a constant in viewBox units is a
// different size in the reader's hand on every page. A finger is about the
// same 44 px everywhere; the arithmetic goes the other way instead.
const perPx=()=>{const r=box.getBoundingClientRect();
return r.width?vb[2]/r.width:1;};
const pick=(ev,cssR)=>{const[mx,my]=at(ev),lim=cssR*perPx();
let best=null,bd=lim*lim;
for(const p of live){const dx=p.x-mx,dy=p.y-my,d=dx*dx+dy*dy;
if(d<bd){bd=d;best=p;}}
return best;};
const rowName=li=>(li.dataset.n||li.dataset.ne||'').split(' · ')[0];
// The listeners go on the HOLDER, not on the drawing. Once a basemap mounts,
// the drawing is handed pointer-events:none so the map underneath can be
// panned — which also took every one of these events away, so the hover names
// and the clicks on this map worked only until the tiles arrived. The holder
// is above both and hears everything; the coordinates are still read from the
// drawing's own rectangle, which is what keeps the dots agreeing with the
// ground after a pan or a zoom.
holder.addEventListener('mousemove',ev=>{
const best=pick(ev,18);
near=best;
if(!hov)return;
if(!best){hov.style.display='none';holder.style.cursor='';return;}
hov.style.display='';holder.style.cursor='pointer';
hc.setAttribute('cx',best.x);hc.setAttribute('cy',best.y);
const right=best.x<vb[2]*0.62;
ht.setAttribute('x',best.x+(right?11:-11));ht.setAttribute('y',best.y-10);
ht.setAttribute('text-anchor',right?'start':'end');
const rank=best.li.dataset.rank;
ht.textContent=(best.li.dataset.ne||best.li.dataset.n||'').split(' · ')[0]
+(rank&&rank!=='0'?'  🐜'+rank:'');});
holder.addEventListener('mouseleave',()=>{near=null;if(hov)hov.style.display='none';});
// A tap names the place; the card's own button opens it. The radius is a
// fingertip rather than the pointer's 18 px, because this is the gesture a
// phone makes and a near-miss used to open a stranger's page.
holder.addEventListener('click',ev=>{
const best=pick(ev,30)||near;
if(!best)return;
const li=best.li,a=li.querySelector('a[href]'),btn=li.querySelector('.planbtn[data-plan]');
const rank=li.dataset.rank;
MDCARD.show({name:rowName(li),sub:li.dataset.area||'',
href:a?a.getAttribute('href'):'',plan:btn?btn.dataset.plan:'',
rank:(rank&&rank!=='0')?rank:''},holder);});
// A filter chip or a search box narrows the LIST; the map follows it, so the
// two are one view of one thing rather than two things that disagree.
window.MDSHELFMAP={filter(pred){live=pred?PTS.filter(pred):PTS;draw(live);},
byFacet(set){this.filter(set&&set.length?p=>{
const f=(p.li.dataset.facets||'').split(' ');
return set.every(x=>f.indexOf(x)>=0);}:null);}};
draw(PTS);})();
// ---- ancient first ---------------------------------------------------
// The founding years the temple register gave us. A place with no year is not
// young — it is undated, so it keeps its alphabetical place BELOW the dated
// ones rather than being sorted as though it were founded in year zero.
// Temples are never ranked against each other here: this is a date, and the
// page says so.
const yr=li=>{const v=parseInt(li.dataset.founded||'',10);return isNaN(v)?null:v;};
reorder(document.getElementById('sort-age'),(a,b)=>{const x=yr(a),y=yr(b);
if(x===null&&y===null)return nm(a,b);if(x===null)return 1;if(y===null)return -1;
return x-y||nm(a,b);});
// ---- by neighbourhood ------------------------------------------------
// The road graph already knows which places share a road. Grouped under it,
// a shelf of four thousand names becomes a walk down one soi at a time. The
// heading links to that road's own page; places the graph never reached keep
// their names and gather under one plain heading at the end, because "we do
// not know which road this is on" is a fact and not a failure.
const areaBtn=document.getElementById('group-area');
areaBtn&&areaBtn.addEventListener('click',()=>{
unfold();
const groups=new Map();
for(const li of items){const a=li.dataset.area||'';
if(!groups.has(a))groups.set(a,[]);groups.get(a).push(li);}
const named=[...groups.entries()].filter(([a])=>a).sort((x,y)=>y[1].length-x[1].length);
const rest=groups.get('')||[];
for(const [area,list] of named){const h=document.createElement('li');
h.className='shelf areahead';const slug=list[0].dataset.areaHref;
// A listing page always sits one level under its province, and the soi pages
// are its sibling directory — the same relative step the row links already use.
h.innerHTML=(slug?`<a href="../soi/${slug}.html">${area}</a>`:area)+
` <span class="count">${list.length}</span>`;
dirList.appendChild(h);
list.sort(nm).forEach(li=>{const d=li.querySelector('.dist');d&&d.remove();dirList.appendChild(li);});}
if(rest.length){const h=document.createElement('li');h.className='shelf areahead';
h.innerHTML=mdBi('ยังไม่รู้ว่าอยู่ถนนไหน','road not known yet')+
` <span class="count">${rest.length}</span>`;
dirList.appendChild(h);
rest.sort(nm).forEach(li=>dirList.appendChild(li));}
dirList.classList.remove('ranked');
btns.forEach(x=>x&&x.classList.remove('on'));areaBtn.classList.add('on');});
// Any other sort clears the neighbourhood headings and the brand shelves, or
// they would sit above rows that no longer belong to them.
btns.forEach(b=>b&&b!==areaBtn&&b.addEventListener('click',()=>unfold()));
reorder(document.getElementById('sort-fresh'),
(a,b)=>(b.dataset.upd||'').localeCompare(a.dataset.upd||'')||rk(b)-rk(a)||nm(a,b));
// ---- facet chips: keep only rows that have ALL the picked things ------
// AND, not OR, because the question is always "somewhere with a cash machine
// AND somewhere to sit", never "either one". The heading count follows the
// filter so it never contradicts what is on screen.
const fbar=document.querySelector('[data-facetbar]');
if(fbar){const on=new Set();const h1c=document.querySelector('h1 .count');
const total=items.length;
const paint=()=>{let shown=0;
items.forEach(li=>{const has=new Set((li.dataset.facets||'').split(' ').filter(Boolean));
const ok=[...on].every(f=>has.has(f));li.classList.toggle('fhide',!ok);if(ok)shown++;});
fbar.querySelectorAll('.fchip').forEach(b=>b.classList.toggle('on',on.has(b.dataset.f)));
if(h1c)h1c.textContent='('+shown.toLocaleString()+(shown<total?' / '+total.toLocaleString():'')+')';
// The map is the same view as the list, so it thins out with it. A reader
// filtering to "has a toilet" should watch the city thin, not scroll down to
// find out where the survivors are.
window.MDSHELFMAP&&window.MDSHELFMAP.byFacet([...on]);};
fbar.querySelectorAll('.fchip').forEach(b=>b.addEventListener('click',()=>{
const f=b.dataset.f;if(!f){on.clear();}else if(on.has(f)){on.delete(f);}else{on.add(f);}
// Narrowing to "has a cash machine" has to reach inside the shelves too. Rows
// that survive the filter while still folded away behind a shut triangle are
// an answer the reader cannot see, and the count above would promise places
// the page appears not to hold.
if(on.size)unfold();
paint();}));}}
// ---- copy link --------------------------------------------------------
document.querySelectorAll('.copylink').forEach(b=>{b.addEventListener('click',async()=>{
await navigator.clipboard.writeText(b.dataset.url);
b.textContent=b.dataset.done;setTimeout(()=>b.textContent=b.dataset.label,1500);});});
// ---- native share (Web Share API where supported) ---------------------
if(navigator.share){document.querySelectorAll('[data-native]').forEach(b=>{
b.style.display='';b.addEventListener('click',()=>{
navigator.share({title:b.dataset.title,url:b.dataset.url}).catch(()=>{});});});}
// ---- currency converter: recompute on input, baked rates, no live call --
// Stands on its own. It used to sit inside the day-colour block below, which
// is guarded on #daycolor — an element the home page does not carry — so on
// the one page that has the converter the listener was never attached and the
// figures sat frozen at whatever build.py baked for 100 baht.
const fxamount=document.getElementById('fxamount');
if(fxamount){const recalc=()=>{const amt=parseFloat(fxamount.value)||0;
document.querySelectorAll('.fxout').forEach(el=>{
el.textContent=(amt*parseFloat(el.dataset.rate)).toLocaleString(undefined,
{minimumFractionDigits:2,maximumFractionDigits:2});});};
fxamount.addEventListener('input',recalc);
fxamount.addEventListener('change',recalc);recalc();}
// ---- home modules: day colour + ticker + personalize ------------------
const day=document.getElementById('daycolor');
if(day){const names=['อาทิตย์','จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์'];
const ens=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const cols=[['แดง','red','#C22'],['เหลือง','yellow','#E7B10A'],['ชมพู','pink','#E77'],
['เขียว','green','#2A7'],['ส้ม','orange','#E80'],['ฟ้า','light blue','#59F'],['ม่วง','purple','#96C']];
const d=new Date().getDay(),c=cols[d],be=new Date().getFullYear()+543;
day.innerHTML=`<span class="swatch" style="background:${c[2]}"></span>`+
`<span class="th">วัน${names[d]} — สีมงคลวันนี้: ${c[0]} · พ.ศ. ${be}</span>`+
`<span class="en">${ens[d]} — today's auspicious colour: ${c[1]} · B.E. ${be}</span>`;}
// ---- my page: pins + updates + daily pick + bookmarks + notes ---------
const H=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pinpick=document.getElementById('pinpick');
if(pinpick){
const PULSE=JSON.parse(document.getElementById('pulse').textContent);
const DEFAULT_PINS=['cm/wat','cm/food','cr/wat'];
const rawPins=localStorage.getItem('md-pins');
const pins=new Set(rawPins===null?DEFAULT_PINS:JSON.parse(rawPins));
if(rawPins===null)localStorage.setItem('md-pins',JSON.stringify([...pins]));
const seen=JSON.parse(localStorage.getItem('md-seen')||'{}');
const shelf=document.getElementById('myshelf');
function unpin(pc){pins.delete(pc);localStorage.setItem('md-pins',JSON.stringify([...pins]));
const cb=pinpick.querySelector(`input[data-pc="${pc}"]`);if(cb)cb.checked=false;renderPins();}
async function renderPins(){
if(!pins.size){shelf.innerHTML='<p class="shelf">ยังไม่ได้ปักหมวด — เลือกด้านล่าง / no shelves pinned yet — pick below</p>';return;}
const idx=await loadIndex();
shelf.innerHTML=[...pins].map(pc=>{
const[pv,cat]=pc.split('/');const m=PULSE[pv]&&PULSE[pv][cat];if(!m)return'';
const fresh=seen[pc]!=null&&m.n>seen[pc]?` <span class="badge">+${m.n-seen[pc]} ใหม่/new</span>`:'';
const sample=idx.filter(e=>e.p===pv&&e.c&&e.c.includes(cat)).slice(0,3);
const preview=sample.map(e=>`<li><a href="${pv}/p/${e.s}.html">${H(e.n)}</a></li>`).join('')
||'<li class="shelf">🐜</li>';
return `<div class="topicwidget"><button class="unpin" data-pc="${pc}" title="ถอดปัก / unpin">✕</button>`+
`<h4><a href="${pv}/${cat}/index.html">${H(m.t)}</a> `+
`<span class="count">(${m.n.toLocaleString()}) · ${H(m.v)}</span>${fresh}</h4>`+
`<ul class="preview">${preview}</ul></div>`;}).join('');
shelf.querySelectorAll('.unpin').forEach(b=>b.addEventListener('click',()=>unpin(b.dataset.pc)));
myMapLink();}
// ---- my shelves, as my map -------------------------------------------
// The explore map takes its entire view from the address bar, so "my map" is
// that page opened at the shelves this reader pinned — no second map, no
// second filter, nothing stored anywhere but their own browser. Six is the
// cap the map itself keeps (a reader cannot hold more colours apart than
// that), so a heavily-pinned page sends the first six and says so rather
// than quietly dropping the rest.
function myMapLink(){
const go=document.getElementById('mymapgo'),note=document.getElementById('mymapnote');
if(!go)return;
const keys=[...pins].map(pc=>pc.replace('/','-'));
const six=keys.slice(0,6);
go.href='map.html'+(six.length?'#12.4/18.78760/98.99310/'+six.join(','):'');
if(!note)return;
note.textContent=!keys.length?'ปักหมวดไว้ก่อน แล้วหมวดนั้นจะขึ้นบนแผนที่ · pin a shelf and it appears on the map'
:(keys.length>6?'แผนที่แสดงได้ทีละ ๖ หมวด · the map shows six shelves at a time':'');}
pinpick.querySelectorAll('input').forEach(cb=>{cb.checked=pins.has(cb.dataset.pc);
cb.addEventListener('change',()=>{cb.checked?pins.add(cb.dataset.pc):pins.delete(cb.dataset.pc);
localStorage.setItem('md-pins',JSON.stringify([...pins]));renderPins();});});
renderPins();
[...pins].forEach(pc=>{const[pv,cat]=pc.split('/');
if(PULSE[pv]&&PULSE[pv][cat])seen[pc]=PULSE[pv][cat].n;});
localStorage.setItem('md-seen',JSON.stringify(seen));
(async()=>{const el=document.getElementById('dailypick');if(!el)return;
const idx=await loadIndex();const pc=[...pins];
let pool=idx.filter(e=>e.c&&pc.some(p=>{const[pv,cat]=p.split('/');
return e.p===pv&&e.c.includes(cat);}));
if(!pool.length)pool=idx;
const t=new Date(),seed=t.getFullYear()*372+(t.getMonth()+1)*31+t.getDate();
const pick=pool[seed%pool.length];
el.innerHTML=`<a href="${pick.p}/p/${pick.s}.html">${H(pick.n)}</a> <span class="count">· ${H(pick.pv)}</span>`;})();
// ---- widget gallery: her other projects, opt-in iframes ----------------
const wgal=document.getElementById('widgetgallery');
if(wgal){const STARTERS=JSON.parse(document.getElementById('widgets-data').textContent);
const added=document.getElementById('widgetboxes');
function myWidgets(){return JSON.parse(localStorage.getItem('md-widgets')||'[]');}
function renderWidgets(){const list=myWidgets();
added.innerHTML=list.map((w,i)=>`<div class="widgetbox"><div class="wtitle">`+
`<span>${H(w.n)}</span><button data-i="${i}" title="เอาออก / remove">✕</button></div>`+
`<iframe src="${H(w.u)}" loading="lazy" sandbox="allow-scripts allow-same-origin allow-popups"></iframe></div>`).join('');
added.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
const list=myWidgets();list.splice(+b.dataset.i,1);
localStorage.setItem('md-widgets',JSON.stringify(list));renderWidgets();renderGallery();}));}
function addWidget(n,u){if(!u)return;const list=myWidgets();
if(list.some(w=>w.u===u))return;list.push({n,u});
localStorage.setItem('md-widgets',JSON.stringify(list));renderWidgets();renderGallery();}
function renderGallery(){const have=new Set(myWidgets().map(w=>w.u));
wgal.innerHTML=STARTERS.map(w=>`<button data-u="${H(w.url)}" data-n="${H(w.th)}"`+
`${have.has(w.url)?' disabled':''}>+ ${H(w.th)}</button>`).join('');
wgal.querySelectorAll('button:not(:disabled)').forEach(b=>b.addEventListener('click',()=>
addWidget(b.dataset.n,b.dataset.u)));}
renderWidgets();renderGallery();
const awf=document.getElementById('addwidgetform');
awf.addEventListener('submit',e=>{e.preventDefault();
const n=awf.querySelector('[name=n]').value.trim(),u=awf.querySelector('[name=u]').value.trim();
if(!n||!u)return;addWidget(n,u);awf.reset();});}
const bmList=document.getElementById('bmlist'),bmForm=document.getElementById('bmform');
function renderBm(){const bm=JSON.parse(localStorage.getItem('md-bm')||'[]');
bmList.innerHTML=bm.map((b,i)=>`<li><a href="${H(b.u)}" rel="noopener">${H(b.n)}</a> `+
`<button class="bmdel" data-i="${i}" title="ลบ">✕</button></li>`).join('')||
'<li class="shelf">ยังไม่มีลิงก์ / no links yet</li>';
bmList.querySelectorAll('.bmdel').forEach(btn=>btn.addEventListener('click',()=>{
const b=JSON.parse(localStorage.getItem('md-bm')||'[]');b.splice(+btn.dataset.i,1);
localStorage.setItem('md-bm',JSON.stringify(b));renderBm();}));}
renderBm();
bmForm.addEventListener('submit',e=>{e.preventDefault();
const n=bmForm.querySelector('[name=n]').value.trim(),u=bmForm.querySelector('[name=u]').value.trim();
if(!n||!u)return;const b=JSON.parse(localStorage.getItem('md-bm')||'[]');
b.push({n,u});localStorage.setItem('md-bm',JSON.stringify(b));bmForm.reset();renderBm();});
const notes=document.getElementById('mynotes');
notes.value=localStorage.getItem('md-notes')||'';
notes.addEventListener('input',()=>localStorage.setItem('md-notes',notes.value));
}
const persona=document.getElementById('persona');
if(persona){const mods=['m-day','m-rand','m-fx','m-gold','m-moon'];
const hidden=JSON.parse(localStorage.getItem('md-mods')||'[]');
mods.forEach(id=>{const el=document.getElementById(id);if(!el)return;
if(hidden.includes(id))el.style.display='none';
const cb=persona.querySelector(`input[data-mod="${id}"]`);if(!cb)return;
cb.checked=!hidden.includes(id);
cb.addEventListener('change',()=>{const h=JSON.parse(localStorage.getItem('md-mods')||'[]');
const i=h.indexOf(id);if(cb.checked&&i>-1)h.splice(i,1);if(!cb.checked&&i===-1)h.push(id);
localStorage.setItem('md-mods',JSON.stringify(h));el.style.display=cb.checked?'':'none';});});}
// ---- sortable tables (stats page) --------------------------------------
document.querySelectorAll('table.sortable').forEach(tbl=>{
const tbody=tbl.querySelector('tbody');
tbl.querySelectorAll('th').forEach((th,idx)=>{let asc=true;
th.addEventListener('click',()=>{
const rows=[...tbody.querySelectorAll('tr')],numeric=th.dataset.sort==='num';
rows.sort((a,b)=>{const av=a.children[idx],bv=b.children[idx];
const A=numeric?parseFloat(av.dataset.v??av.textContent):av.textContent;
const Bv=numeric?parseFloat(bv.dataset.v??bv.textContent):bv.textContent;
if(numeric)return asc?A-Bv:Bv-A;
return asc?String(A).localeCompare(String(Bv),'th'):String(Bv).localeCompare(String(A),'th');});
rows.forEach(r=>tbody.appendChild(r));
tbl.querySelectorAll('th').forEach(h=>h.classList.remove('sorted','asc'));
th.classList.add('sorted');if(asc)th.classList.add('asc');asc=!asc;});});});
// ---- crawl-request form: hand the request to suggest.html, prefilled ---
const crawlForm=document.getElementById('crawlform');
if(crawlForm){crawlForm.addEventListener('submit',e=>{
e.preventDefault();
const area=crawlForm.area.value.trim(),cat=crawlForm.cat.value.trim(),
kind=crawlForm.kind.value,note=crawlForm.note.value.trim();
const title=`crawl request (${kind}): ${area||'?'} — ${cat||'?'}`;
const body=title+'\n\n'+(note?note+'\n\n':'');
// Hands the request to suggest.html with the box already filled, rather than
// opening a GitHub issue the reader may have no account for — and which, once
// the account was hidden, was a 404.
location.href=RROOT+'suggest.html?kind=crawl&t='+encodeURIComponent(body);});}
// ---- claim.html: find-or-paste an existing place, claim it, or edit it -
const claimFind=document.getElementById('claim-find');
if(claimFind){
const cfg=JSON.parse(document.getElementById('claim-cfg').textContent);
const WORKER=cfg.workerUrl,SITE='https://motdang.net/';
const FIELDS=['phone','lineId','facebook','instagram','whatsapp','email','website','hours','menu','note'];
// Facet ticks travel as an array, not as FIELDS entries — an empty array is a
// real answer ("I looked; it has none of these"), which a blank text input
// cannot express.
// Only the shown fieldset is read. Every set is in the page, so reading them
// all would let a hidden 7-Eleven question ride along on a massage shop.
const getTicks=form=>[...form.querySelectorAll('fieldset[data-facetticks]:not([hidden]) input[name="facet"]:checked')].map(c=>c.value);
const setTicks=(form,vals)=>{const on=new Set(vals||[]);
form.querySelectorAll('input[name="facet"]').forEach(c=>{c.checked=on.has(c.value);});};
// Which tick-list this place answers to. `fx` comes from the search index; a
// place with no set shows no fieldset at all, which is the right answer for
// the 6,249 records nobody has written questions for yet.
const showTicks=(form,fx)=>{let shown=null;
form.querySelectorAll('fieldset[data-facetticks]').forEach(fs=>{
const on=!!fx&&fs.dataset.facetticks===fx;fs.hidden=!on;if(on)shown=fs;});
return shown;};
const params=new URLSearchParams(location.search);
const stepFind=claimFind,stepConfirm=document.getElementById('claim-confirm'),
stepSuccess=document.getElementById('claim-success'),stepEdit=document.getElementById('claim-edit');
function showStep(el){[stepFind,stepConfirm,stepSuccess,stepEdit].forEach(s=>{s.style.display=s===el?'':'none';});}
const editToken=params.get('edit');
if(editToken){
showStep(stepEdit);
const editForm=document.getElementById('editform'),editErr=document.getElementById('editerror');
(async()=>{try{
const res=await fetch(WORKER+'/edit/'+encodeURIComponent(editToken));
const data=await res.json();
if(!res.ok)throw new Error(data.error||'ลิงก์ใช้ไม่ได้ / invalid link');
FIELDS.forEach(f=>{if(data.claim[f])editForm[f].value=data.claim[f];});
// The worker returns placeId at the top level; the stored claim carries a
// copy of it, so fall back to that rather than to nothing.
const pid=data.placeId||(data.claim&&data.claim.placeId);
const idx=await loadIndex();
const me=pid&&idx.find(x=>x.id===pid);
showTicks(editForm,me&&me.fx);
setTicks(editForm,data.claim.facets);
}catch(err){editErr.textContent=err.message;}})();
editForm.addEventListener('submit',async e=>{
e.preventDefault();
const btn=editForm.querySelector('button.submit');
btn.disabled=true;editErr.style.color='';editErr.textContent='';
const body={};FIELDS.forEach(f=>{body[f]=editForm[f].value.trim();});
body.facets=getTicks(editForm);
try{
const res=await fetch(WORKER+'/edit/'+encodeURIComponent(editToken),{method:'POST',
headers:{'content-type':'application/json'},body:JSON.stringify(body)});
const data=await res.json();
if(!res.ok)throw new Error(data.error||'บันทึกไม่สำเร็จ / save failed');
editErr.style.color='#1a6b4a';editErr.textContent='✓ บันทึกแล้ว / saved';
}catch(err){editErr.textContent=err.message;}
btn.disabled=false;});
}else{
let picked=null;
const results=document.getElementById('claimresults'),search=document.getElementById('claimsearch'),
urlPaste=document.getElementById('claimurlpaste'),findErr=document.getElementById('claimfinderror');
function slugFromUrl(v){const m=v.trim().match(/\/(cm|cr)\/p\/([a-z0-9-]+)\.html/i);return m?m[2]:null;}
function pick(e){picked=e;
showTicks(document.getElementById('claimform'),e.fx);
document.getElementById('claimwhoname').textContent=e.n;
document.getElementById('claimwhoprov').textContent='· '+e.pv;
document.getElementById('claimwholink').href=SITE+e.p+'/p/'+e.s+'.html';
showStep(stepConfirm);}
search&&search.addEventListener('input',async()=>{
const q=search.value.trim().toLowerCase();
if(!q){results.innerHTML='';return;}
const idx=await loadIndex();
const hits=idx.filter(e=>(e.n+' '+(e.e||'')).toLowerCase().includes(q)).slice(0,12);
results.innerHTML=hits.map(e=>`<li><button>${H(e.n)} <span class="count">· ${H(e.pv)}</span></button></li>`).join('');
results.querySelectorAll('button').forEach((b,i)=>b.addEventListener('click',()=>pick(hits[i])));});
urlPaste&&urlPaste.addEventListener('change',async()=>{
const slug=slugFromUrl(urlPaste.value);
findErr.textContent='';
if(!slug){findErr.textContent='หาไอดีจากลิงก์ไม่เจอ / could not read an id from that link';return;}
const idx=await loadIndex();const e=idx.find(x=>x.s===slug);
if(!e){findErr.textContent='ไม่พบที่นี่ในสารบัญ / not found in the directory';return;}
pick(e);});
document.getElementById('claimagain').addEventListener('click',()=>{picked=null;showStep(stepFind);});
const wantId=params.get('id');
if(wantId){(async()=>{const idx=await loadIndex();const e=idx.find(x=>x.id===wantId);if(e)pick(e);})();}
const claimForm=document.getElementById('claimform'),claimErr=document.getElementById('claimerror');
claimForm.addEventListener('submit',async e=>{
e.preventDefault();
if(!picked){claimErr.textContent='เลือกที่ตั้งก่อน / pick a place first';return;}
const body={placeId:picked.id};let any=false;
FIELDS.forEach(f=>{const v=claimForm[f].value.trim();if(v){body[f]=v;any=true;}});
// Ticks ride along but never satisfy `any` — a claim still needs a real way
// to reach the shop, or a passer-by could lock an owner out with one tick.
body.facets=getTicks(claimForm);
if(!any){claimErr.textContent='ใส่อย่างน้อยหนึ่งช่องทาง / fill in at least one channel';return;}
const btn=claimForm.querySelector('button.submit');
btn.disabled=true;btn.textContent='กำลังบันทึก… / saving…';claimErr.textContent='';
try{
const res=await fetch(WORKER+'/claim',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
const data=await res.json();
if(!res.ok)throw new Error(data.error||'บันทึกไม่สำเร็จ / something went wrong');
const viewUrl=SITE+picked.p+'/p/'+picked.s+'.html';
const vlink=document.getElementById('successviewlink');
vlink.href=viewUrl;vlink.textContent=viewUrl;
document.getElementById('successediturl').textContent=data.editUrl;
document.getElementById('successcopybtn').dataset.url=data.editUrl;
showStep(stepSuccess);
}catch(err){
claimErr.textContent=err.message;
btn.disabled=false;btn.textContent='🏪 ยืนยันฟรี · Claim it free';}});
}}
// ---- route plan: pick stops anywhere, see them together on plan.html --
// A plan is an ordered list of "province:slug" keys in localStorage. That is
// the whole state — the same string is what travels in a ?stops= share link,
// so a plan someone sends you and a plan you built yourself are the same
// object by the time either is drawn.
const PLAN_KEY='md-plan',PLAN_MAX=9;   // ไหว้พระ ๙ วัด is nine by definition
const WALK_KMH=4.6,RIDE_KMH=18;
function planGet(){try{const v=JSON.parse(localStorage.getItem(PLAN_KEY));
return Array.isArray(v)?v.slice(0,PLAN_MAX):[];}catch(e){return[];}}
function planSet(list){try{localStorage.setItem(PLAN_KEY,JSON.stringify(list.slice(0,PLAN_MAX)));}
catch(e){}planPaint();}
function planPaint(){const list=planGet(),have=new Set(list);
document.querySelectorAll('.planbtn[data-plan]').forEach(b=>{
const on=have.has(b.dataset.plan);b.classList.toggle('on',on);
b.setAttribute('aria-pressed',on?'true':'false');});
document.querySelectorAll('.plancount').forEach(el=>{
el.textContent=list.length||'';el.style.display=list.length?'':'none';});}
document.querySelectorAll('.planbtn[data-plan]').forEach(b=>{
b.addEventListener('click',e=>{e.preventDefault();
const k=b.dataset.plan,list=planGet(),i=list.indexOf(k);
if(i>-1)list.splice(i,1);
else if(list.length>=PLAN_MAX){alert('แผนหนึ่งเก็บได้ '+PLAN_MAX+' จุด / a plan holds '+PLAN_MAX+' stops');return;}
else list.push(k);
planSet(list);});});
planPaint();
// ---- plan.html itself --------------------------------------------------
const planSteps=document.getElementById('plansteps');
if(planSteps){(async()=>{
const CATL=JSON.parse(document.getElementById('cat-labels').textContent);
const SITE='https://motdang.net/';
const GEO=JSON.parse(document.getElementById('plan-geo').textContent);
const MOAT=GEO.moat;
// The moat ring as its four แจ่ง corners, in order. Slightly out of square,
// which is the point: an axis-aligned box puts Suan Dok Gate on the wrong
// side of the water it stands on.
const POLY=(GEO.poly||[]).map(p=>({lat:p[0],lng:p[1]}));
const POLY_EDGES=POLY.map((p,i)=>[p,POLY[(i+1)%POLY.length]]);
// The five gates and the four แจ่ง corners, as the catalogue pins them — the
// same records build.py routes a moat crossing by. Where a person gets over
// the water is the thing anybody here gives directions by, so any map showing
// a stretch of moat names the ways across it that stand on that map.
const GATES=(GEO.gates||[]).map(g=>({lat:g[0],lng:g[1],th:g[2],en:g[3],kind:g[4]}));
const elEmpty=document.getElementById('planempty'),elHas=document.getElementById('planhasstops'),
elTotal=document.getElementById('plantotal'),elMap=document.getElementById('planmap'),
elBanner=document.getElementById('planbanner');
let here=null; // the reader's own position, once they offer it
// What the last drawing framed: centre and reach, in the drawing's own units.
// svgMap fills it, render() hands it to the basemap. Null until the first
// plan is drawn, which is also when there is nothing to point a map at.
let PLANFRAME=null;
// A shared link wins over whatever is in this browser, but never silently:
// the banner says a plan arrived and offers to keep it before it overwrites.
const shared=new URLSearchParams(location.search).get('stops');
let stops=planGet(),incoming=null;
if(shared){const inc=shared.split(',').map(s=>s.trim()).filter(Boolean).slice(0,PLAN_MAX);
if(inc.length){incoming=inc;stops=inc;}}
function km(a,b){const R=6371,dLa=(b.lat-a.lat)*Math.PI/180,dLo=(b.lng-a.lng)*Math.PI/180;
const h=Math.sin(dLa/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLo/2)**2;
return 2*R*Math.asin(Math.sqrt(h));}
function dist(d){return d<1?Math.round(d*1000)+' ม./m':d.toFixed(1)+' กม./km';}
function mins(d,kmh){const m=Math.round(d/kmh*60);return m<1?'<1':m;}
function segX(a,b,c,d){
const side=(p,q,r)=>(q.lng-p.lng)*(r.lat-p.lat)-(q.lat-p.lat)*(r.lng-p.lng);
const d1=side(c,d,a),d2=side(c,d,b),d3=side(a,b,c),d4=side(a,b,d);
return ((d1>0&&d2<0)||(d1<0&&d2>0))&&((d3>0&&d4<0)||(d3<0&&d4>0));}
// ---- the road graph: nobody can fly ----------------------------------
// Straight-line distance is wrong in a city and most wrong for the two people
// this page is for. There are buildings in the way, sois that do not join up,
// a one-way ring around the moat, and water you cross at a footbridge or a
// U-turn and nowhere else — and a footbridge is a road to a walker and a wall
// to a scooter. So we route on the real network, with a mode.
//
// The asymmetry that does most of the work: **oneway binds ride and not foot.**
// On a one-way ring road the shop thirty metres behind you is a lap away.
let GRAPH=null,GRAPH_STATE='cold';
const MODES={foot:{kmh:4.6,fwd:1,bwd:2,osrm:'foot'},
             ride:{kmh:18,fwd:4,bwd:8,osrm:'car'}};
async function loadGraph(){
if(GRAPH_STATE!=='cold')return GRAPH;
GRAPH_STATE='loading';
const g=await mdJSON('data/road_graph.json');
if(!g||!g.nodes||!g.edges){GRAPH_STATE='absent';return null;}
const S=g.scale;
const nodes=g.nodes.map(p=>[p[0]/S,p[1]/S]);
// Rebuild each edge's full polyline: its two junction ends with the road's
// bends, which arrive delta-encoded, threaded back between them.
const adj=nodes.map(()=>[]);
const geom=[];
g.edges.forEach((e,i)=>{
const a=e[0],b=e[1],len=e[2],flags=e[3],d=e[4]||[];
const pts=[nodes[a]];
let la=0,ln=0;
for(let k=0;k<d.length;k+=2){
if(k===0){la=d[0];ln=d[1];}else{la+=d[k];ln+=d[k+1];}
pts.push([la/S,ln/S]);}
pts.push(nodes[b]);
geom.push(pts);
adj[a].push([b,len,flags,i,1]);
adj[b].push([a,len,flags,i,0]);});
GRAPH={area:g.area,nodes:nodes,adj:adj,edges:g.edges,geom:geom};
GRAPH_STATE='ready';
return GRAPH;}
function inArea(p){const a=GRAPH&&GRAPH.area;
return !!a&&p.lat>a.s&&p.lat<a.n&&p.lng>a.w&&p.lng<a.e;}
function passable(flags,mode,fwd){const m=MODES[mode];
return (flags&(fwd?m.fwd:m.bwd))!==0;}
// Metres from p to the segment ab, and how far along ab the foot of that
// perpendicular falls. Local flat projection: over one road segment the
// curvature of the earth is not the error that matters.
function toSeg(p,a,b){
const kx=Math.cos(p.lat*Math.PI/180)*111320,ky=110540;
const px=0,py=0;
const ax=(a[1]-p.lng)*kx,ay=(a[0]-p.lat)*ky;
const bx=(b[1]-p.lng)*kx,by=(b[0]-p.lat)*ky;
const dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy;
let t=L?((px-ax)*dx+(py-ay)*dy)/L:0;
t=Math.max(0,Math.min(1,t));
const cx=ax+t*dx,cy=ay+t*dy;
return {d:Math.hypot(cx-px,cy-py),t:t,seg:Math.sqrt(L)};}
// Snap a stop onto the network: nearest point on the nearest edge this mode may
// use, with the walk-in distance to each end of it. Snapping to junctions alone
// would throw away up to a block of accuracy on every stop.
function snap(p,mode){
if(!GRAPH)return null;
let best=null;
for(let i=0;i<GRAPH.geom.length;i++){
const flags=GRAPH.edges[i][3];
if(!passable(flags,mode,true)&&!passable(flags,mode,false))continue;
const pts=GRAPH.geom[i];
let run=0;
for(let k=0;k<pts.length-1;k++){
const r=toSeg(p,pts[k],pts[k+1]);
if(!best||r.d<best.d){
best={d:r.d,edge:i,fromA:run+r.t*r.seg,total:0};}
run+=r.seg;}
if(best&&best.edge===i){
let tot=0;
for(let k=0;k<pts.length-1;k++)tot+=toSeg(p,pts[k],pts[k+1]).seg;
best.total=tot;}}
if(!best)return null;
const e=GRAPH.edges[best.edge];
best.a=e[0];best.b=e[1];
best.toA=best.fromA;best.toB=Math.max(0,best.total-best.fromA);
return best;}
// A tiny binary heap — Dijkstra on ~10k junctions wants one, and an array sort
// per pop turns a millisecond into a second.
function Heap(){this.a=[];}
Heap.prototype.push=function(k,v){const a=this.a;a.push([k,v]);let i=a.length-1;
while(i>0){const p=(i-1)>>1;if(a[p][0]<=a[i][0])break;const t=a[p];a[p]=a[i];a[i]=t;i=p;}};
Heap.prototype.pop=function(){const a=this.a;if(!a.length)return null;
const top=a[0],last=a.pop();
if(a.length){a[0]=last;let i=0;
for(;;){const l=2*i+1,r=l+1;let m=i;
if(l<a.length&&a[l][0]<a[m][0])m=l;
if(r<a.length&&a[r][0]<a[m][0])m=r;
if(m===i)break;const t=a[m];a[m]=a[i];a[i]=t;i=m;}}
return top;};
// ---- cutting a road at a point ----------------------------------------
// A snapped stop stands part of the way along an edge, not at a junction, so
// the first and the last stretch of every journey is a PIECE of a road. The
// junction chain alone leaves those pieces out, and the straight stub then
// covers them — claiming a hundred metres of real street is "the walk in from
// the pin". Cut the edge instead and draw the ground that is actually walked.
function segLen(p,q){const kx=Math.cos((p[0]+q[0])/2*Math.PI/180)*111320,ky=110540;
return Math.hypot((q[1]-p[1])*kx,(q[0]-p[0])*ky);}
function edgeLen(pts){let t=0;for(let k=0;k<pts.length-1;k++)t+=segLen(pts[k],pts[k+1]);return t;}
function atAlong(pts,d){
let run=0;
for(let k=0;k<pts.length-1;k++){const L=segLen(pts[k],pts[k+1]);
if(run+L>=d){const t=L?(d-run)/L:0;
return [pts[k][0]+(pts[k+1][0]-pts[k][0])*t,pts[k][1]+(pts[k+1][1]-pts[k][1])*t];}
run+=L;}
return pts[pts.length-1];}
// The part of one edge between two distances along it, given in travel order.
function cutEdge(ei,d0,d1){
const pts=GRAPH.geom[ei],L=edgeLen(pts);
const a=Math.max(0,Math.min(L,Math.min(d0,d1))),b=Math.max(0,Math.min(L,Math.max(d0,d1)));
const out=[atAlong(pts,a)];
let run=0;
for(let k=0;k<pts.length-1;k++){run+=segLen(pts[k],pts[k+1]);
if(run>a+0.01&&run<b-0.01)out.push(pts[k+1]);}
out.push(atAlong(pts,b));
return d1<d0?out.reverse():out;}
function joinLine(line,pts){pts.forEach(pt=>{const last=line[line.length-1];
if(!last||Math.abs(last[0]-pt[0])>1e-9||Math.abs(last[1]-pt[1])>1e-9)line.push(pt);});
return line;}
// Dijkstra from both ends of the start edge to both ends of the goal edge.
// Directed: an edge is only traversable the way this mode is allowed to take
// it, which is where oneway earns its keep.
function route(from,to,mode){
if(!GRAPH||!from||!to)return null;
// Both stops on one stretch of road is only a straight answer if this mode may
// travel that way down it. On a one-way soi the shop thirty metres behind you
// is a lap away, so that case falls through to the search like any other.
if(from.edge===to.edge){
const fwd=to.fromA>=from.fromA;
if(passable(GRAPH.edges[from.edge][3],mode,fwd))
return {m:Math.abs(to.fromA-from.fromA),
path:cutEdge(from.edge,from.fromA,to.fromA),sameEdge:true};}
const N=GRAPH.nodes.length;
const cost=new Float64Array(N).fill(Infinity);
const prevN=new Int32Array(N).fill(-1),prevE=new Int32Array(N).fill(-1);
const h=new Heap();
// Leaving the start edge is only possible towards an end this mode may reach.
if(passable(GRAPH.edges[from.edge][3],mode,false)||from.a===from.b){
cost[from.a]=from.toA;h.push(from.toA,from.a);}
if(passable(GRAPH.edges[from.edge][3],mode,true)){
if(from.toB<cost[from.b]){cost[from.b]=from.toB;h.push(from.toB,from.b);}}
const goals={};
if(passable(GRAPH.edges[to.edge][3],mode,true))goals[to.a]=to.toA;
if(passable(GRAPH.edges[to.edge][3],mode,false))goals[to.b]=to.toB;
if(!Object.keys(goals).length)return null;
let bestGoal=null,bestCost=Infinity;
while(true){
const top=h.pop();
if(!top)break;
const c=top[0],n=top[1];
if(c>cost[n])continue;
if(c>=bestCost)break;
if(goals[n]!==undefined&&c+goals[n]<bestCost){bestCost=c+goals[n];bestGoal=n;}
const list=GRAPH.adj[n];
for(let i=0;i<list.length;i++){
const to2=list[i][0],len=list[i][1],flags=list[i][2],ei=list[i][3],fwd=list[i][4];
if(!passable(flags,mode,fwd===1))continue;
const nc=c+len;
if(nc<cost[to2]){cost[to2]=nc;prevN[to2]=n;prevE[to2]=ei;h.push(nc,to2);}}}
if(bestGoal===null)return null;
// Stitch the whole journey into one polyline: the piece of the first road from
// the stop out to the junction it leaves by, then the junction chain, then the
// piece of the last road in to the second stop. Leaving the two end pieces out
// drew a 1.8 km walk as 280 m of road and a straight line across the rest.
const chain=[];
let cur=bestGoal;
while(cur!==-1&&prevE[cur]!==-1){chain.push([prevE[cur],cur]);cur=prevN[cur];}
chain.reverse();
const line=[];
joinLine(line,cutEdge(from.edge,from.fromA,
(cur===from.a)?0:edgeLen(GRAPH.geom[from.edge])));
chain.forEach(([ei,into])=>{
const e=GRAPH.edges[ei],pts=GRAPH.geom[ei];
joinLine(line,(e[1]===into)?pts:pts.slice().reverse());});
joinLine(line,cutEdge(to.edge,
(bestGoal===to.a)?0:edgeLen(GRAPH.geom[to.edge]),to.fromA));
return {m:bestCost,path:line};}
// ---- the errand solver -------------------------------------------------
// Pick a pharmacy, an ATM and som tam by NAME and any tool will route between
// them. The question people actually have is the other way round: I need those
// three things, which ones make the shortest single trip? Choosing the nearest
// of each independently is not the same answer and is often a worse one — the
// nearest pharmacy can sit the wrong side of a one-way ring from everything
// else you need.
//
// Done in three parts. One Dijkstra per candidate fills a cost matrix (n
// searches, not n squared pairs). Then every combination of one-candidate-per
// errand is scored against that matrix, which is arithmetic. Then the order
// within the winning combination: exact for a small round, 2-opt beyond, since
// the cost of an approximation here is a slightly longer walk.
function costsFrom(s,mode){
if(!GRAPH||!s)return null;
const N=GRAPH.nodes.length,cost=new Float64Array(N).fill(Infinity),h=new Heap();
if(passable(GRAPH.edges[s.edge][3],mode,false)||s.a===s.b){cost[s.a]=s.toA;h.push(s.toA,s.a);}
if(passable(GRAPH.edges[s.edge][3],mode,true)&&s.toB<cost[s.b]){cost[s.b]=s.toB;h.push(s.toB,s.b);}
for(;;){const top=h.pop();if(!top)break;
const c=top[0],n=top[1];
if(c>cost[n])continue;
const list=GRAPH.adj[n];
for(let i=0;i<list.length;i++){
const to=list[i][0],len=list[i][1],flags=list[i][2],fwd=list[i][4];
if(!passable(flags,mode,fwd===1))continue;
const nc=c+len;
if(nc<cost[to]){cost[to]=nc;h.push(nc,to);}}}
return cost;}
function costTo(cost,t,mode){
if(!cost||!t)return null;
let best=Infinity;
if(passable(GRAPH.edges[t.edge][3],mode,true))best=Math.min(best,cost[t.a]+t.toA);
if(passable(GRAPH.edges[t.edge][3],mode,false))best=Math.min(best,cost[t.b]+t.toB);
return best===Infinity?null:best;}
// Unreachable is not free. Charged high enough that the search avoids it and
// low enough that sums stay comparable.
const NOWAY=1e7;
function matrixFor(points,mode){
const snaps=points.map(p=>snap(p,mode));
const n=points.length,M=[];
for(let i=0;i<n;i++){
const row=new Array(n).fill(null);
if(snaps[i]){const cost=costsFrom(snaps[i],mode);
for(let j=0;j<n;j++){
if(!snaps[j])continue;
if(i===j){row[j]=0;continue;}
const c=costTo(cost,snaps[j],mode);
if(c!==null)row[j]=c+snaps[i].d+snaps[j].d;}}
M.push(row);}
return M;}
function tourLen(M,order){let t=0;
for(let i=0;i<order.length-1;i++){const v=M[order[i]][order[i+1]];t+=(v===null?NOWAY:v);}
return t;}
// An open path, not a loop: an errand run ends where it ends. Start is pinned
// (where the reader is, or the first stop they chose); the rest is free.
function bestOrder(M,idx){
const rest=idx.slice(1);
if(rest.length<=6){
let best=null,bestLen=Infinity;
const perm=(arr,cur)=>{
if(!arr.length){const o=[idx[0]].concat(cur),L=tourLen(M,o);
if(L<bestLen){bestLen=L;best=o;}return;}
for(let i=0;i<arr.length;i++)perm(arr.slice(0,i).concat(arr.slice(i+1)),cur.concat([arr[i]]));};
perm(rest,[]);
return {order:best,len:bestLen};}
let order=[idx[0]],left=rest.slice();
while(left.length){const cur=order[order.length-1];
let bi=0,bd=Infinity;
left.forEach((j,i)=>{const v=M[cur][j],d=(v===null?NOWAY:v);if(d<bd){bd=d;bi=i;}});
order.push(left[bi]);left.splice(bi,1);}
let improved=true;
while(improved){improved=false;
for(let i=1;i<order.length-1;i++)for(let k=i+1;k<order.length;k++){
const cand=order.slice(0,i).concat(order.slice(i,k+1).reverse(),order.slice(k+1));
if(tourLen(M,cand)+1e-9<tourLen(M,order)){order=cand;improved=true;}}}
return {order:order,len:tourLen(M,order)};}
async function solveErrands(kinds,mode){
const idx=await loadIndex();
const area=GRAPH&&GRAPH.area;
if(!area)return null;
// Anchor the search: where the reader is, else the stops already chosen, else
// the middle of the area we can route in.
const anchor=here||(places.length?{lat:places[0].lat,lng:places[0].lng}
:{lat:(area.n+area.s)/2,lng:(area.w+area.e)/2});
const CAND=6;
const slots=[];
for(const k of kinds){
const pool=idx.filter(e=>e.lat!=null&&(e.c||[]).indexOf(k)>-1
&&e.lat>area.s&&e.lat<area.n&&e.lng>area.w&&e.lng<area.e);
pool.sort((a,b)=>km(anchor,a)-km(anchor,b));
if(!pool.length)return {missing:k};
slots.push(pool.slice(0,CAND));}
// Points: the fixed part of the round first, then every candidate.
const fixed=[anchor].concat(places.map(p=>({lat:p.lat,lng:p.lng})));
const pts=fixed.slice(),meta=[];
slots.forEach((pool,si)=>pool.forEach(e=>{meta.push({slot:si,e:e,i:pts.length});
pts.push({lat:e.lat,lng:e.lng});}));
const M=matrixFor(pts,mode);
// Every way of taking one candidate per errand. Six candidates over three
// errands is 216 combinations — small, and each is only a table lookup away
// from a score.
let best=null;
const walk=(si,chosen)=>{
if(si===slots.length){
const r=bestOrder(M,fixed.map((_,i)=>i).concat(chosen.map(m=>m.i)));
if(!best||r.len<best.len)best={len:r.len,order:r.order,chosen:chosen.slice()};
return;}
meta.filter(m=>m.slot===si).forEach(m=>{chosen.push(m);walk(si+1,chosen);chosen.pop();});};
walk(0,[]);
if(!best)return null;
// What the naive answer would have been, so the page can say whether asking
// the question this way actually bought anything.
const naive=slots.map((pool,si)=>meta.find(m=>m.slot===si&&m.e===pool[0]));
const nOrder=bestOrder(M,fixed.map((_,i)=>i).concat(naive.map(m=>m.i)));
return {best:best,naive:{len:nOrder.len},meta:meta,fixedCount:fixed.length};}
function osmDirections(a,b,mode){
return 'https://www.openstreetmap.org/directions?engine=fossgis_osrm_'+MODES[mode].osrm+
'&route='+a.lat.toFixed(5)+'%2C'+a.lng.toFixed(5)+'%3B'+b.lat.toFixed(5)+'%2C'+b.lng.toFixed(5);}
// One leg, both ways of travelling it. The two modes get different distances
// because they are genuinely different journeys — that is the whole point.
// A stop this far from any road we hold is not really on the network, and the
// straight walk-in charged for it is a guess. วัดเมืองลัง sits 450 m from the
// nearest junction in the graph while OSM has a footpath 10 m away, and the
// leg came out 916 m against a real walk of 4.3 km. One stop of the ninety on
// the merit rounds is in that state — rare enough to name on the page rather
// than hide, and never to pass off as a measured distance.
const FAR_FROM_ROAD=100;
function leg(a,b){
const out={crow:km(a,b),foot:null,ride:null,routed:false,far:0};
if(GRAPH_STATE!=='ready'||!inArea(a)||!inArea(b))return out;
for(const mode of ['foot','ride']){
const s=snap(a,mode),t=snap(b,mode);
if(!s||!t)continue;
const r=route(s,t,mode);
if(!r)continue;
// Add the walk-in from each stop to the road it was snapped to; otherwise a
// shop set back from the street reads as being on it.
out[mode]={km:(r.m+s.d+t.d)/1000,path:r.path,snap:Math.round(s.d+t.d)};
out.far=Math.max(out.far,Math.round(Math.max(s.d,t.d)));}
out.routed=!!(out.foot||out.ride);
return out;}
async function resolve(keys){
const idx=await loadIndex();
const bySlug={};idx.forEach(e=>{bySlug[e.p+':'+e.s]=e;});
const out=[];
for(const k of keys){const e=bySlug[k];
if(!e||e.lat==null)continue;
const rec={key:k,n:e.n,en:e.e,p:e.p,s:e.s,pv:e.pv,c:e.c||[],lat:e.lat,lng:e.lng};
// The slim index carries no address or phone. The per-place .json beside
// every page does, and eight of those is a cheap price for stop cards that
// are actually useful standing in the street.
const j=await mdJSON(e.p+'/p/'+e.s+'.json');
if(j){rec.addr=j.address||'';rec.chan=(j.channels||[]).slice(0,4);rec.sched=j.sched||null;}
out.push(rec);}
return out;}
// Which network the reader is on. It decides what "nearest" means when the
// stops are reordered, and which of the two lines the page leads with.
let planMode=(()=>{try{return localStorage.getItem('md-planmode')==='ride'?'ride':'foot';}
catch(e){return 'foot';}})();
// The graph is half a megabyte, so it loads here and nowhere else on the site.
await loadGraph();
let places=await resolve(stops);
// Drop anything the index no longer knows, rather than leaving a hole.
if(places.length!==stops.length&&!incoming){stops=places.map(p=>p.key);planSet(stops);}
// Is a point inside the moat ring? Ray casting, because the ring is a little
// out of square and its bounding box puts Suan Dok Gate on the wrong bank.
function inRing(p){
if(POLY.length<3)return false;
let hit=false;
for(let i=0,j=POLY.length-1;i<POLY.length;j=i++){
const yi=POLY[i].lat,xi=POLY[i].lng,yj=POLY[j].lat,xj=POLY[j].lng;
if((xi>p.lng)!==(xj>p.lng)){
const ty=(yj-yi)*(p.lng-xi)/((xj-xi)||1e-12)+yi;
if(p.lat<ty)hit=!hit;}}
return hit;}
// Liang–Barsky, enough of it to keep a label on the canvas.
function clipToBox(p,q,W,H){
let t0=0,t1=1;const dx=q.x-p.x,dy=q.y-p.y;
const tests=[[-dx,p.x],[dx,W-p.x],[-dy,p.y],[dy,H-p.y]];
for(let i=0;i<tests.length;i++){
const pp=tests[i][0],qq=tests[i][1];
if(pp===0){if(qq<0)return null;continue;}
const r=qq/pp;
if(pp<0){if(r>t1)return null;if(r>t0)t0=r;}
else{if(r<t0)return null;if(r<t1)t1=r;}}
return [{x:p.x+t0*dx,y:p.y+t0*dy},{x:p.x+t1*dx,y:p.y+t1*dy}];}
// Where to write "the moat" so the words land on water that is on the page and
// not on top of a gate that is also naming itself. Pinning the label to the
// ring's northernmost corner dropped it off the top of the picture on five of
// the ten merit rounds — drawn water, no name — and putting it at the middle
// of the longest visible side then landed it on Chang Phueak Gate.
function moatLabelPoint(X,Y,W,H,taken){
let best=null,fallback=null;
POLY_EDGES.forEach(me=>{
const p={x:X(me[0].lng),y:Y(me[0].lat)},q={x:X(me[1].lng),y:Y(me[1].lat)};
const c=clipToBox(p,q,W,H);
if(!c)return;
const L=Math.hypot(c[1].x-c[0].x,c[1].y-c[0].y);
if(L<12)return;
const upright=Math.abs(c[1].y-c[0].y)>Math.abs(c[1].x-c[0].x);
if(!fallback||L>fallback.L)fallback={L:L,x:(c[0].x+c[1].x)/2,y:(c[0].y+c[1].y)/2,upright:upright};
[0.5,0.3,0.7,0.15,0.85].forEach(t=>{
const x=c[0].x+(c[1].x-c[0].x)*t,y=c[0].y+(c[1].y-c[0].y)*t;
if(x<40||x>W-40||y<18||y>H-14)return;
let clear=999;
(taken||[]).forEach(g=>{clear=Math.min(clear,Math.hypot(g[0]-x,g[1]-y));});
// Long side, well clear of any gate already naming itself.
const score=L+Math.min(clear,150)*3;
if(!best||score>best.score)best={score:score,x:x,y:y,upright:upright};});});
// Water on the page always gets its name, even when only a sliver of one side
// shows: a clamped label at the edge beats an unnamed blue dashed line.
const pick=best||fallback;
if(!pick)return null;
const py=Math.min(Math.max(pick.y,18),H-14);
if(pick.upright){const right=pick.x<W/2;   // the words go on whichever side has room
return [Math.min(Math.max(right?pick.x+8:pick.x-8,6),W-6),py,right?'start':'end'];}
return [Math.min(Math.max(pick.x,60),W-60),Math.max(py-7,16),'middle'];}
function svgMap(list,legs){
if(!list.length)return'';
// The stops set the frame — never the moat. Framing to the moat as well
// squeezes four stops 400m apart into a knot in the middle of a 1.6km
// square. The moat is drawn afterwards, clipped by the viewBox, so it is a
// landmark you recognise at the edge of the picture rather than the subject.
const pts=list.map(p=>({lat:p.lat,lng:p.lng}));
if(here)pts.push(here);
// Frame the roads the route actually uses, not just its stops: a leg that has
// to go round three blocks leaves the box drawn around its endpoints.
(legs||[]).forEach(l=>{if(!l)return;
['foot','ride'].forEach(m=>{if(l[m]&&l[m].path)l[m].path.forEach(
q=>pts.push({lat:q[0],lng:q[1]}));});});
let n=Math.max(...pts.map(p=>p.lat)),s=Math.min(...pts.map(p=>p.lat)),
w=Math.min(...pts.map(p=>p.lng)),e=Math.max(...pts.map(p=>p.lng));
// A single stop has no extent at all; give every plan a floor so one pin
// does not divide by zero and eight clustered pins are not a smudge.
const padLat=Math.max((n-s)*0.22,0.0022),padLng=Math.max((e-w)*0.22,0.0022);
n+=padLat;s-=padLat;w-=padLng;e+=padLng;
const kx=Math.cos((n+s)/2*Math.PI/180),W=760;
const H=Math.max(240,Math.min(520,W*((n-s)/((e-w)*kx||1e-9))));
const X=lng=>(lng-w)/(e-w)*W,Y=lat=>(n-lat)/(n-s)*H;
// The moat and its gates, worked out before the picture opens so the map can
// say in its own label what it is showing. The rule does not depend on where
// the route happens to sit: if a side of the moat crosses this frame it is
// drawn AND named, and every gate or แจ่ง corner standing inside the frame is
// drawn AND named. A frame wholly within the walls has no side to draw, so it
// gets the one fact in words instead.
const inFrame=p=>p.lat<n&&p.lat>s&&p.lng>w&&p.lng<e;
const cmHere=POLY.length&&list.some(p=>p.p==='cm');
const frame=[{lat:n,lng:w},{lat:n,lng:e},{lat:s,lng:e},{lat:s,lng:w}];
const frameEdges=frame.map((p,i)=>[p,frame[(i+1)%4]]);
const moatShows=!!cmHere&&(POLY.some(inFrame)
||POLY_EDGES.some(me=>frameEdges.some(fe=>segX(me[0],me[1],fe[0],fe[1]))));
// Only claim "inside the old city" when the frame really does sit in the ring.
// A plan out in Hang Dong also fails to show a side of the moat, and telling
// its reader they are inside the walls would simply be untrue.
const insideWalls=!!cmHere&&!moatShows&&frame.every(inRing);
const gatesHere=cmHere?GATES.filter(inFrame):[];
let aria='แผนที่ทริปของคุณ '+list.length+' จุด · map of your route, '+list.length+' stops';
if(moatShows)aria+=' — คูเมืองอยู่ในภาพ · the old city moat runs across it';
else if(insideWalls)aria+=' — ทั้งหมดอยู่ในเวียงเก่า · all of it inside the old city';
if(gatesHere.length)aria+=' — '+gatesHere.map(g=>g.th+' '+g.en).join(', ');
// Hand the frame out so render() can point the basemap at exactly what was
// drawn. Everything below is in these units; nothing else knows them.
PLANFRAME={n:n,s:s,e:e,w:w,kx:kx,W:W,H:H};
const GROUND=!!(window.MDMAP&&elMap&&MDMAP.live(elMap));
let o=['<svg viewBox="0 0 '+W+' '+Math.round(H)+'" width="100%" class="planmap" role="img" '+
'aria-label="'+H2(aria)+'">'];
// The cream rectangle IS the map when there is nothing underneath, and it is
// a sheet thrown over the map when there is.
if(!GROUND)o.push('<rect width="'+W+'" height="'+Math.round(H)+'" fill="#FBF6EE"/>');
// The traced moat is four corner pins joined by straight lines. Over a real
// basemap that is a wrong shape sitting on a right one — the actual moat is
// there in the tiles, rounded corners and all — so the tracing gives way and
// only its name stays.
if(moatShows&&!GROUND){
o.push('<path d="'+POLY.map((p,i)=>(i?'L':'M')+X(p.lng).toFixed(1)+' '+Y(p.lat).toFixed(1)).join(' ')+
'Z" fill="none" stroke="#2a78d6" stroke-width="2" stroke-dasharray="5 4" opacity=".55">'+
'<title>คูเมืองเชียงใหม่ (เส้นโดยประมาณ จากหมุดแจ่งทั้งสี่) · the old city moat, '+
'traced from the four แจ่ง corner pins</title></path>');
const lab=moatLabelPoint(X,Y,W,H,gatesHere.map(g=>[X(g.lng),Y(g.lat)]));
if(lab)o.push('<text x="'+lab[0].toFixed(1)+'" y="'+lab[1].toFixed(1)+'" text-anchor="'+lab[2]+
'" font-size="11" fill="#2a78d6" opacity=".9">คูเมือง · the moat</text>');}
else if(insideWalls)o.push('<text x="'+(W-12)+'" y="20" text-anchor="end" font-size="11" '+
'fill="#2a78d6" opacity=".8">ในเวียงเก่า · inside the old city</text>');
// A gate is a diamond on the water, named in both languages. Cream-filled so
// the route line reads through it, and drawn before the legs so a red walking
// line lies over the landmark rather than under it.
gatesHere.forEach(g=>{
const gx=X(g.lng),gy=Y(g.lat);
// A gate is a symbol standing over one spot, so it keeps its size when the
// reader zooms; the moat it stands on is ground and grows.
o.push('<g data-mdpin="'+gx.toFixed(1)+','+gy.toFixed(1)+'">');
o.push('<path d="M'+gx.toFixed(1)+' '+(gy-6).toFixed(1)+'l6 6l-6 6l-6-6Z" fill="#FBF6EE" '+
'stroke="#2a78d6" stroke-width="2" opacity=".95"><title>'+H2(g.th+' · '+g.en)+
'</title></path>');
const gl=g.th+' · '+g.en,half=gl.length*3.1;
let ga='middle',gxl=gx;
if(gx-half<4){ga='start';gxl=4;}else if(gx+half>W-4){ga='end';gxl=W-4;}
// Under the gate normally; over it when a stop is standing where the words
// would go, since two names in one place is neither name.
const crowded=list.some(p=>Math.hypot(X(p.lng)-gx,Y(p.lat)-(gy+20))<46);
const gyl=crowded?Math.max(14,gy-12):Math.min(H-5,gy+20);
o.push('<text x="'+gxl.toFixed(1)+'" y="'+gyl.toFixed(1)+'" text-anchor="'+ga+
'" font-size="10" fill="#2a78d6" opacity=".9">'+H2(gl)+'</text>');
o.push('</g>');});
// Draw the roads the route really follows. Both modes, because they diverge:
// where the walk and the ride part company is exactly the thing worth seeing.
// The scooter line goes down first and solid, the walking line over it dashed,
// so where they agree you read one road and where they differ you read two.
const drawPath=(pth,stroke,w,dash)=>{
if(!pth||pth.length<2)return;
const d=pth.map((q,i)=>(i?'L':'M')+X(q[1]).toFixed(1)+' '+Y(q[0]).toFixed(1)).join(' ');
o.push('<path d="'+d+'" fill="none" stroke="'+stroke+'" stroke-width="'+w+
'" stroke-linejoin="round" stroke-linecap="round"'+
(dash?' stroke-dasharray="'+dash+'"':'')+' opacity=".85"/>');};
let anyRouted=false,anyStraight=false;
(legs||[]).forEach(l=>{if(!l)return;
if(l.ride&&l.ride.path){drawPath(l.ride.path,'#1c5aa8',4,'');anyRouted=true;}
if(l.foot&&l.foot.path){drawPath(l.foot.path,'#a3231c',2.5,'6 4');anyRouted=true;}});
// The stub from a pin to the road it sits back from. Its length is already in
// the leg distance; without it drawn, a shop down a lane looks unreachable —
// the route line simply stops short of its own pin.
(legs||[]).forEach((l,i)=>{if(!l)return;
const pth=(l.foot&&l.foot.path)||(l.ride&&l.ride.path);
if(!pth||pth.length<2)return;
[[list[i],pth[0]],[list[i+1],pth[pth.length-1]]].forEach(([stop,end])=>{
if(!stop)return;
const dx=X(end[1])-X(stop.lng),dy=Y(end[0])-Y(stop.lat);
if(Math.hypot(dx,dy)<3)return;
o.push('<line x1="'+X(stop.lng).toFixed(1)+'" y1="'+Y(stop.lat).toFixed(1)+'" x2="'+
X(end[1]).toFixed(1)+'" y2="'+Y(end[0]).toFixed(1)+'" stroke="#8a7a62" stroke-width="1.5" '+
'stroke-dasharray="2 3" opacity=".7"><title>'+
'จากหมุดถึงถนน / from the pin out to the road</title></line>');});});
// A leg the graph could not route still needs a line, but a faint dotted one
// that does not pretend to be a road.
list.forEach((p,i)=>{const L=(legs||[])[i-1];
if(i&&L&&!L.routed){anyStraight=true;
const a=list[i-1];
o.push('<path d="M'+X(a.lng).toFixed(1)+' '+Y(a.lat).toFixed(1)+'L'+X(p.lng).toFixed(1)+
' '+Y(p.lat).toFixed(1)+'" fill="none" stroke="#8a7a62" stroke-width="2" '+
'stroke-dasharray="2 5" opacity=".8"><title>'+
'เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed</title></path>');}});
if(here){o.push('<g data-mdpin="'+X(here.lng).toFixed(1)+','+Y(here.lat).toFixed(1)+
'"><circle cx="'+X(here.lng).toFixed(1)+'" cy="'+Y(here.lat).toFixed(1)+
'" r="7" fill="#2a78d6" fill-opacity=".25" stroke="#2a78d6" stroke-width="2">'+
'<title>ตำแหน่งของคุณ · you are here</title></circle></g>');}
list.forEach((p,i)=>{const cx=X(p.lng),cy=Y(p.lat);
// The pin, its number and its name are one symbol over one doorway. Grown
// with the ground they would be four times the size two zooms in.
o.push('<g data-mdpin="'+cx.toFixed(1)+','+cy.toFixed(1)+'">');
if(GROUND)o.push('<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+
'" r="16" fill="#FFFCF6"/>');
o.push('<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="13" fill="#a3231c" '+
'stroke="#7d1712" stroke-width="2"><title>'+H2(p.n)+'</title></circle>');
o.push('<text x="'+cx.toFixed(1)+'" y="'+(cy+5).toFixed(1)+'" text-anchor="middle" '+
'font-size="14" font-weight="700" fill="#fff">'+(i+1)+'</text>');
const label=p.n.length>24?p.n.slice(0,23)+'…':p.n;
let anchor='middle',lx=cx;const half=label.length*3.6;
if(cx-half<4){anchor='start';lx=4;}else if(cx+half>W-4){anchor='end';lx=W-4;}
o.push('<text x="'+lx.toFixed(1)+'" y="'+(cy-18).toFixed(1)+'" text-anchor="'+anchor+
'" font-size="12" fill="#2A1E16" stroke="#FFFCF6" stroke-width="3" '+
'paint-order="stroke">'+H2(label)+'</text>');
o.push('</g>');});
const kmDeg=111.32*kx,barKm=(e-w)*kx*111.32>6?2:0.5,barPx=barKm/kmDeg/(e-w)*W;
if(barPx<W*0.6){const by=Math.round(H-16);
// Frame furniture: it keeps its corner, and the shell takes the bar away
// once the reader has zoomed off the scale it was measured at.
o.push('<g class="mdmap-scale" data-mdfix="1">');
o.push('<line x1="16" y1="'+by+'" x2="'+(16+barPx).toFixed(1)+'" y2="'+by+
'" stroke="#2A1E16" stroke-width="2"/>');
o.push('<text x="16" y="'+(by-5)+'" font-size="10" fill="#2A1E16">'+barKm+' กม./km</text>');
o.push('</g>');}
// Two lines on one map need saying which is which.
if(anyRouted||anyStraight){let lx=W-14,ly=H-34;
o.push('<g data-mdfix="1">');
const key=(stroke,wd,dash,label)=>{
o.push('<line x1="'+(lx-26)+'" y1="'+ly+'" x2="'+(lx-6)+'" y2="'+ly+'" stroke="'+stroke+
'" stroke-width="'+wd+'"'+(dash?' stroke-dasharray="'+dash+'"':'')+' stroke-linecap="round"/>');
o.push('<text x="'+(lx-32)+'" y="'+(ly+4)+'" text-anchor="end" font-size="10" fill="#2A1E16">'+
label+'</text>');ly+=14;};
if(anyRouted){key('#a3231c',2.5,'6 4','🚶 เดิน/walk');key('#1c5aa8',4,'','🛵 มอไซค์/scooter');}
if(anyStraight)key('#8a7a62',2,'2 5','เส้นตรง/straight');
o.push('</g>');}
o.push('</svg>');return o.join('');}
function H2(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function planUrl(){return SITE+'plan.html?stops='+encodeURIComponent(places.map(p=>p.key).join(','));}
// share_block bakes the bare plan.html URL into each pill's query string. Swap
// that placeholder for the real ?stops= link — percent-encoded, since it now
// carries a ? of its own and would otherwise truncate the outer share URL.
function repointShare(){const box=document.getElementById('planshare');if(!box)return;
const u=planUrl(),t='แผนเดินทาง '+places.length+' จุด · มดแดง';
box.querySelectorAll('a.pill').forEach(a=>{
if(!a.dataset.tpl)a.dataset.tpl=a.getAttribute('href');
a.setAttribute('href',a.dataset.tpl.split(SITE+'plan.html').join(encodeURIComponent(u)));});
box.querySelectorAll('[data-url]').forEach(b=>{b.dataset.url=u;
if(b.dataset.title!=null)b.dataset.title=t;});}
function textPlan(){
const lines=['แผนเดินทาง / My route — มดแดง motdang.net',''];
places.forEach((p,i)=>{lines.push((i+1)+'. '+p.n+(p.en&&p.en!==p.n?' ('+p.en+')':''));
if(p.addr)lines.push('   '+p.addr);
(p.chan||[]).forEach(c=>lines.push('   '+c.text));
lines.push('   '+SITE+p.p+'/p/'+p.s+'.html');
const nx=places[i+1];
if(nx){const L=leg(p,nx);
if(L.routed){
if(L.foot)lines.push('   ↓ เดิน/walk '+dist(L.foot.km)+' — '+mins(L.foot.km,MODES.foot.kmh)+' นาที/min');
else lines.push('   ↓ เดินไปไม่ได้ / not walkable');
if(L.ride)lines.push('     ขี่/scooter '+dist(L.ride.km)+' — '+mins(L.ride.km,MODES.ride.kmh)+' นาที/min');
else lines.push('     ขี่ไปไม่ได้ / no road for a scooter');
if(L.far>=FAR_FROM_ROAD){
lines.push('     จุดหนึ่งห่างถนนที่บันทึกไว้ '+L.far+' ม. ระยะจริงน่าจะไกลกว่านี้ / one stop is '+
L.far+' m from the nearest road on record, so the real distance is probably longer');
lines.push('     '+osmDirections(p,nx,'foot'));}
}else{
lines.push('   ↓ '+dist(L.crow)+' เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed');
lines.push('     '+osmDirections(p,nx,'foot'));}}
lines.push('');});
lines.push('ลิงก์ทริปนี้ / this route: '+planUrl());
return lines.join('\n');}
// The demo teaches an empty page. Once there are real stops on the map it is
// just a second animated map competing with the true one, so it steps aside.
const elDemo=document.getElementById('plandemo');
// The basemap mounts lazily — map.js waits until the box is on screen, because
// MapLibre is a megabyte. So the first drawing is made before there is any
// ground, keeps its cream sheet (which is right: it is what fills the box
// while the tiles are in flight), and would then sit ON TOP of the streets
// when they arrive. map.js announces the moment it is ready by dispatching
// mdmap:sync, so listen once and draw again — this second drawing knows the
// ground is there, drops the sheet and the traced moat, and points the camera
// at the plan's own frame.
if(elMap)elMap.addEventListener('mdmap:sync',function ready(){
elMap.removeEventListener('mdmap:sync',ready);render();});
function render(){
if(elDemo)elDemo.style.display=places.length?'none':'';
if(!places.length){elEmpty.style.display='';elHas.style.display='none';
if(incoming)elBanner.style.display='none';return;}
elEmpty.style.display='none';elHas.style.display='';
const legs=[];for(let i=1;i<places.length;i++)legs.push(leg(places[i-1],places[i]));
// With a basemap live the drawing belongs in its own layer under the tiles;
// writing straight into the container would tear the live map out with it.
(elMap.querySelector('.mdmap-draw')||elMap).innerHTML=svgMap(places,legs);
if(window.MDMAP&&MDMAP.live(elMap)&&PLANFRAME){
const F=PLANFRAME;
// Measure the SVG, not its container. The wrapper scrolls sideways and the
// drawing carries a min-width, so on a narrow phone the box is 300 px wide
// while the picture inside it is 352 — and a scale taken from the box would
// put the streets at one zoom and the pins at another.
const svgEl=elMap.querySelector('.mdmap-draw svg');
const shown=(svgEl&&svgEl.getBoundingClientRect().width)||elMap.clientWidth||F.W;
// The SVG is F.W viewBox units across, shown at whatever width the column
// gave it. Metres-per-CSS-pixel has to account for both, or the streets end
// up at one zoom and the pins at another.
MDMAP.retarget(elMap,(F.n+F.s)/2,(F.w+F.e)/2,
 (F.e-F.w)*F.kx*111320/shown);}
// Totals per mode, and only over the legs that mode could actually route.
// Summing a routed leg with a crow-flies one would produce a number that is
// neither, so an unrouted leg is counted and named separately.
const sum=m=>legs.reduce((t,l)=>t+(l[m]?l[m].km:0),0);
const unrouted=legs.filter(l=>!l.routed).length;
const footTot=sum('foot'),rideTot=sum('ride');
const legIn=here&&places.length?leg(here,places[0]):null;
let tot='<b>'+places.length+' จุด / stops</b>';
if(places.length>1){
if(GRAPH_STATE==='ready'&&(footTot||rideTot)){
tot+=' · <span class="pmode foot">🚶 '+dist(footTot)+' · '+mins(footTot,MODES.foot.kmh)+' นาที/min</span>'+
' · <span class="pmode ride">🛵 '+dist(rideTot)+' · '+mins(rideTot,MODES.ride.kmh)+' นาที/min</span>';
if(rideTot>footTot*1.15)tot+=' <span class="tinynote">'+
'(มอไซค์ไกลกว่าเพราะถนนเดินรถทางเดียว / longer by scooter — one-way streets)</span>';
}else{
tot+=' · '+dist(footTot||rideTot||0);}}
else tot+=' · จุดเดียว / a single stop';
if(legIn&&legIn.foot)tot+=' · จากตำแหน่งคุณถึงจุดแรก '+dist(legIn.foot.km);
if(unrouted)tot+=' · <b>'+unrouted+' ช่วงอยู่นอกเขตคิดเส้นทาง</b> / '+unrouted+
' leg'+(unrouted>1?'s':'')+' outside the routed area';
elTotal.innerHTML=tot;
// WHEN YOU GET THERE, IS IT STILL OPEN? Everything above this line is
// metres; this is the other half of the same question, and the reason the
// stops carry their week in `sched`. Travel time only — nothing is assumed
// about how long an errand takes, because that is the reader's business and
// not something this page can know — so it says "about", and an arrival that
// lands after closing is worth saying out loud even approximately. No
// schedule means no line at all: unknown is not shut.
const MDW=10080;
const NOWW=(window.MDHOURS&&MDHOURS.now)?MDHOURS.now():null;
const legMin=L=>{if(!L)return 0;const m=L[planMode]||L.foot||L.ride;
return m?Math.round(m.km/MODES[planMode].kmh*60):0;};
const cumMin=[];{let t=(legIn&&legIn[planMode])?Math.round(legIn[planMode].km/MODES[planMode].kmh*60):0;
for(let i=0;i<places.length;i++){cumMin.push(t);t+=legMin(legs[i]);}}
function arrivalHtml(p,i){
if(NOWW===null||!p.sched||!window.MDHOURS)return '';
const at=((NOWW+cumMin[i])%MDW+MDW)%MDW;
const on=MDHOURS.open(p.sched,at);
if(on===null)return '';
const clock=('0'+Math.floor((at%1440)/60)).slice(-2)+':'+('0'+(at%60)).slice(-2);
if(!on)return '<p class="planwhen shut">⚠ '+mdBi('ถึงประมาณ '+clock+' — ตอนนั้นปิดแล้ว',
'arrive about '+clock+' — closed by then')+'</p>';
const d=MDHOURS.edge(p.sched,at);
const tail=(d!==null&&d<=60)?' · '+mdBi('อีก '+d+' นาทีปิด','closes '+d+' min later'):'';
return '<p class="planwhen">'+mdBi('ถึงประมาณ '+clock+' — เปิดอยู่',
'arrive about '+clock+' — open')+tail+'</p>';}
planSteps.innerHTML=places.map((p,i)=>{
const cats=(p.c||[]).map(c=>CATL[c]?CATL[c][0]:c).join(' · ');
const chan=(p.chan||[]).map(c=>'<a href="'+H2(c.href)+'" rel="noopener">'+H2(c.text)+'</a>').join('');
const L=legs[i];
let legHtml='';
if(L){
if(L.routed){
const f=L.foot,r=L.ride;
let rows='';
if(f)rows+='<span class="pleg foot">🚶 '+dist(f.km)+' · '+mins(f.km,MODES.foot.kmh)+' นาที/min</span>';
if(r)rows+='<span class="pleg ride">🛵 '+dist(r.km)+' · '+mins(r.km,MODES.ride.kmh)+' นาที/min</span>';
if(!f)rows+='<span class="pleg none">🚶 เดินไปไม่ได้ / not walkable</span>';
if(!r)rows+='<span class="pleg none">🛵 ขี่ไปไม่ได้ / no road for a scooter</span>';
let note='';
if(f&&r&&r.km>f.km*1.25)note='<span class="planvia">↳ '+
'ขี่ไกลกว่าเดิน '+dist(r.km-f.km)+' — ถนนทางเดียวหรือต้องกลับรถ / '+
'the ride is '+dist(r.km-f.km)+' longer: one-way, or a U-turn to get across</span>';
if(L.far>=FAR_FROM_ROAD){const A=places[i],B=places[i+1];
note+='<span class="planvia">↳ จุดหนึ่งในช่วงนี้อยู่ห่างถนนที่มดบันทึกไว้ '+L.far+
' ม. ระยะจริงน่าจะไกลกว่านี้ / one stop on this leg is '+L.far+
' m from the nearest road on record, so the real distance is probably longer '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'foot'))+'" rel="noopener">'+
'🚶 ดูเส้นทางจริง/check it ↗</a></span>';}
legHtml='<li class="planleg">'+rows+note+'</li>';
}else{
const A=places[i],B=places[i+1];
legHtml='<li class="planleg out">↓ '+dist(L.crow)+' '+
'<span class="tinynote">เส้นตรง ยังไม่ได้คิดตามถนน / straight line, not routed</span> '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'foot'))+'" rel="noopener">🚶 ดูเส้นทาง/directions ↗</a> '+
'<a class="planosm" href="'+H2(osmDirections(A,B,'ride'))+'" rel="noopener">🛵 ดูเส้นทาง/directions ↗</a></li>';}}
return '<li class="planstop"><span class="plannum">'+(i+1)+'</span>'+
'<div class="planbody"><h3><a href="'+RROOT+p.p+'/p/'+p.s+'.html">'+H2(p.n)+'</a></h3>'+
'<span class="plancat">'+H2(cats)+' · '+H2(p.pv)+'</span>'+
(p.addr?'<p class="planaddr">'+H2(p.addr)+'</p>':'')+
arrivalHtml(p,i)+
(chan?'<div class="planchan">'+chan+'</div>':'')+
'</div><div class="planacts">'+
'<button type="button" data-up="'+i+'" title="เลื่อนขึ้น / move up"'+(i?'':' disabled')+'>▲</button>'+
'<button type="button" data-down="'+i+'" title="เลื่อนลง / move down"'+(i<places.length-1?'':' disabled')+'>▼</button>'+
'<button type="button" class="plandel" data-del="'+i+'" title="เอาออก / remove">✕</button>'+
'</div></li>'+legHtml;}).join('');
planSteps.querySelectorAll('[data-up]').forEach(b=>b.addEventListener('click',()=>{
const i=+b.dataset.up;[places[i-1],places[i]]=[places[i],places[i-1]];commit();}));
planSteps.querySelectorAll('[data-down]').forEach(b=>b.addEventListener('click',()=>{
const i=+b.dataset.down;[places[i+1],places[i]]=[places[i],places[i+1]];commit();}));
planSteps.querySelectorAll('[data-del]').forEach(b=>b.addEventListener('click',()=>{
places.splice(+b.dataset.del,1);commit();}));
const dl=document.getElementById('plandlbtn');
if(dl){if(dl.dataset.blob)URL.revokeObjectURL(dl.dataset.blob);
const url=URL.createObjectURL(new Blob([textPlan()],{type:'text/plain;charset=utf-8'}));
dl.dataset.blob=url;dl.href=url;}
repointShare();}
// commit = the plan changed for real: remember it, redraw, and stop treating
// it as somebody else's shared link.
function commit(){incoming=null;elBanner.style.display='none';
planSet(places.map(p=>p.key));render();}
if(incoming){const mine=planGet();
elBanner.className='planbanner';elBanner.style.display='';
elBanner.innerHTML='<span>📩 <b>แผนที่มีคนแชร์มา '+incoming.length+' จุด</b> · '+
'A route someone shared with you'+(mine.length?' — แผนเดิมของคุณยังอยู่ / your own plan is untouched':'')+
'</span><button type="button" id="plankeep">💾 เก็บเป็นแผนของฉัน / Keep as mine</button>';
document.getElementById('plankeep').addEventListener('click',commit);}
document.querySelectorAll('.pmbtn').forEach(b=>b.addEventListener('click',()=>{
planMode=b.dataset.mode;
try{localStorage.setItem('md-planmode',planMode);}catch(e){}
document.querySelectorAll('.pmbtn').forEach(x=>{const on=x===b;
x.classList.toggle('on',on);x.setAttribute('aria-pressed',on?'true':'false');});
document.body.classList.toggle('mode-ride',planMode==='ride');
render();}));
document.body.classList.toggle('mode-ride',planMode==='ride');
document.querySelectorAll('.pmbtn').forEach(x=>{const on=x.dataset.mode===planMode;
x.classList.toggle('on',on);x.setAttribute('aria-pressed',on?'true':'false');});
document.getElementById('planclearbtn').addEventListener('click',()=>{
places=[];planSet([]);incoming=null;elBanner.style.display='none';render();});
// Where the run starts. With nothing granted the route simply begins at the
// first stop, which is a complete answer — so this button adds precision, it
// does not unlock the feature. Declining used to raise an alert() and leave
// the reader exactly where they were; it now starts the run from the landmark
// nearest the plan instead, and says which one.
const planLoc=document.getElementById('planlocbtn');
planLoc&&planLoc.addEventListener('click',()=>{MDLOC.ask(pt=>{
here=pt;planLoc.classList.add('on');render();},
()=>{const o=MDLOC.origin(places.length?places[0].lat:null);
here={lat:o.lat,lng:o.lng};MDLOC.remember(o);
planLoc.classList.add('on');
planLoc.innerHTML='📍 '+mdBi('เริ่มจาก'+o.th,'Starting from '+o.en);
render();});});
// Nearest-neighbour from wherever the run starts. Not the optimal tour, and
// it does not pretend to be — with eight stops it is close enough to save
// real riding, and it stays legible: "always go to the nearest one next".
// ---- errands: the UI over solveErrands ---------------------------------
const errSel=document.getElementById('planerrsel'),errAdd=document.getElementById('planerradd'),
errList=document.getElementById('planerrlist'),errSolve=document.getElementById('planerrsolve'),
errOut=document.getElementById('planerrout');
if(errSel&&errAdd){
let kinds=(()=>{try{const v=JSON.parse(localStorage.getItem('md-plan-kinds'));
return Array.isArray(v)?v.slice(0,4):[];}catch(e){return[];}})();
const labelOf=k=>{const o=[...errSel.options].find(o=>o.value===k);
return o?o.textContent.replace(/\s*\(\d+\)$/,''):k;};
function paintKinds(){
errList.innerHTML=kinds.map((k,i)=>'<li>'+H2(labelOf(k))+
' <button type="button" class="errdel" data-i="'+i+'" aria-label="'+
H2('เอาออก / remove')+'">✕</button></li>').join('');
errSolve.style.display=kinds.length?'':'none';
try{localStorage.setItem('md-plan-kinds',JSON.stringify(kinds));}catch(e){}
errList.querySelectorAll('.errdel').forEach(b=>b.addEventListener('click',()=>{
kinds.splice(+b.dataset.i,1);paintKinds();errOut.innerHTML='';}));}
errAdd.addEventListener('click',()=>{
const k=errSel.value;
// Four errands over six candidates each is already 1,296 combinations; past
// that the wait stops being worth the better answer.
if(!k||kinds.indexOf(k)>-1||kinds.length>=4)return;
kinds.push(k);paintKinds();errOut.innerHTML='';});
errSolve.addEventListener('click',async()=>{
errOut.innerHTML='<p class="tinynote">🐜 '+H2('มดกำลังลองทุกทาง…')+'</p>';
// Yield once so the message paints before the search blocks the thread.
await new Promise(r=>setTimeout(r,30));
const res=await solveErrands(kinds,planMode);
if(!res||res.missing){errOut.innerHTML='<p class="tinynote">'+
H2('ยังไม่มีข้อมูลพอในเขตที่มดเดินถนนไว้ / not enough of that kind inside the area we hold roads for')+
'</p>';return;}
const chosen=res.best.chosen;
const saved=res.naive.len-res.best.len;
const rows=chosen.map(m=>'<li><a href="'+m.e.p+'/p/'+m.e.s+'.html">'+H2(m.e.n)+'</a> '+
'<span class="tinynote">'+H2(labelOf(kinds[m.slot]))+'</span></li>').join('');
// Say plainly whether asking the question this way helped. Sometimes the
// nearest of each IS the best round, and claiming otherwise would be a lie
// dressed as a feature.
const verdict=saved>50
?'<p class="errsaved">'+H2('สั้นกว่าการเลือกที่ใกล้ที่สุดทีละอย่าง '+Math.round(saved)+' เมตร')+
' · '+H2('shorter than picking the nearest of each, by '+Math.round(saved)+' m')+'</p>'
:'<p class="tinynote">'+H2('รอบนี้ การเลือกที่ใกล้ที่สุดทีละอย่างก็สั้นพอ ๆ กัน')+
' · '+H2('here, picking the nearest of each is just as good')+'</p>';
errOut.innerHTML='<p class="errtotal"><b>'+H2(dist(res.best.len/1000))+'</b> '+
H2(planMode==='foot'?'เดินทั้งรอบ / walking the whole round':'ขี่รถทั้งรอบ / riding the whole round')+
'</p>'+verdict+'<ol class="errpicks">'+rows+'</ol>'+
'<button type="button" id="erradd2plan" class="pill dark">'+
H2('ใส่ทั้งหมดลงในแผน')+' · '+H2('Add them all to the plan')+'</button>';
document.getElementById('erradd2plan').addEventListener('click',()=>{
const add=chosen.map(m=>m.e.p+':'+m.e.s).filter(k=>stops.indexOf(k)<0);
stops=stops.concat(add).slice(0,PLAN_MAX);
planSet(stops);location.href='plan.html?stops='+encodeURIComponent(stops.join(','));});});
paintKinds();}
document.getElementById('planreorderbtn').addEventListener('click',()=>{
if(places.length<3)return;
const rest=places.slice();const out=[];
let cur=here||rest[0];
if(!here)out.push(rest.shift());
// Nearest by the network the reader is actually travelling on. Ordering by
// crow-flies would happily send a scooter the wrong way up a one-way soi.
const nearBy=(a,b)=>{const L=leg(a,b);
const r=L[planMode]||L.foot||L.ride;return r?r.km:L.crow;};
while(rest.length){let bi=0,bd=Infinity;
rest.forEach((p,i)=>{const d=nearBy(cur,p);if(d<bd){bd=d;bi=i;}});
cur=rest[bi];out.push(rest.splice(bi,1)[0]);}
places=out;commit();});
render();
})();}

// ---- reveal on scroll, and a little parallax -------------------------
// The two motions carried over from the design study. Both are decoration, so
// both are built to fail into "everything visible, nothing moving".
//
// The reveal rule lives behind .js-reveal on <html>, added here. If this file
// never runs — blocked, cached badly, thrown by an earlier error — the class
// is never added, the rule never matches, and the page is simply already
// there. A reveal effect that hides content by default and shows it from JS
// is the commonest way a pretty page ships blank; this cannot do that.
(function(){
if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
const items=[].slice.call(document.querySelectorAll('[data-reveal]'));
const pxs=[].slice.call(document.querySelectorAll('[data-parallax]'));
if(!items.length&&!pxs.length)return;
document.documentElement.classList.add('js-reveal');
const show=el=>el.classList.add('shown');
// Belt and braces: whatever happens to the observer or the scroll handler,
// nothing stays hidden past six seconds.
setTimeout(()=>items.forEach(show),6000);
if('IntersectionObserver' in window){
const io=new IntersectionObserver((es,o)=>{es.forEach(e=>{
if(e.isIntersecting){show(e.target);o.unobserve(e.target);}});},
{rootMargin:'0px 0px -8% 0px'});
items.forEach(el=>io.observe(el));
}else items.forEach(show);
if(!pxs.length)return;
// Offset each element against its own container's distance from the middle of
// the screen, so the drift is symmetrical and nothing runs away down the page.
pxs.forEach(el=>{el.dataset.mdBase=el.style.transform||'';});
let ticking=false;
const onScroll=()=>{if(ticking)return;ticking=true;
requestAnimationFrame(()=>{ticking=false;const vh=window.innerHeight;
pxs.forEach(el=>{const p=(el.parentElement||el).getBoundingClientRect();
const mid=p.top+p.height/2-vh/2;
const y=-mid*parseFloat(el.dataset.parallax||'0.1');
el.style.transform='translateY('+y.toFixed(1)+'px) '+(el.dataset.mdBase||'');});});};
window.addEventListener('scroll',onScroll,{passive:true});
window.addEventListener('resize',onScroll,{passive:true});
onScroll();
})();

// ---- แจ้งมด / tell the ants: the suggestion form -----------------------
// Every "tell us" link on this site used to open a GitHub issue, which asked
// a Chiang Mai shopkeeper to hold a GitHub account in order to correct their
// own phone number — and which, from 2026-08-07, answered 404 to everyone.
// The form posts to the same Worker the claim flow uses. Nothing here
// publishes itself; it joins a queue a person reads.
(function(){
const form=document.getElementById('suggestform');
if(!form)return;
const cfg=JSON.parse(document.getElementById('suggest-cfg').textContent);
const qs=new URLSearchParams(location.search);
// A link can arrive carrying what it was about — which place, what kind of
// thing — so the reader is not asked to retype what they just clicked past.
if(qs.get('kind'))form.kind.value=qs.get('kind');
if(qs.get('t')&&!form.what.value)form.what.value=qs.get('t');
const pid=qs.get('id')||'';
// TYPED FACTS (facts.py, 2026-09-06). With a place known, the form offers a
// field and a value; the drawer on a place page arrives with the field set.
// The fact travels as "fact:" + JSON in `what`, so the Worker and the queue
// need no new kind — importers/apply_facts.py reads it out by number.
const fbox=document.getElementById('factbox'),ff=form.querySelector('[name=factfield]'),fv=form.querySelector('[name=factvalue]');
if(pid&&fbox){fbox.hidden=false;if(qs.get('field')&&ff)ff.value=qs.get('field');}
const where=document.getElementById('suggestwhere');
if(pid&&where){where.textContent=pid;where.parentElement.hidden=false;}
const say=document.getElementById('suggestsay');
form.addEventListener('submit',async e=>{
e.preventDefault();
let what=form.what.value.trim();
if(ff&&ff.value&&fv&&fv.value.trim())what='fact:'+JSON.stringify({field:ff.value,value:fv.value.trim(),note:what});
else if(ff&&ff.value&&!what){say.textContent='ใส่ค่าในช่องด้วยเจ้า / Put the value in the box';return;}
if(!what){say.textContent='บอกเราหน่อยว่าเรื่องอะไร / Tell us what to look at';return;}
const btn=form.querySelector('button');btn.disabled=true;
say.textContent='กำลังส่ง… / sending…';
try{
const res=await fetch(cfg.workerUrl+'/suggest',{method:'POST',
headers:{'content-type':'application/json'},
body:JSON.stringify({kind:form.kind.value,what:what,
placeId:pid||null,from:form.from.value.trim()||null,
page:qs.get('p')||document.referrer||location.href,
lang:document.documentElement.lang==='th'?'th':'en'})});
const out=await res.json();
if(out.ok){form.hidden=true;
say.textContent='ขอบคุณเจ้า — มดรับเรื่องแล้ว จะมีคนอ่านทุกข้อ / '
+'Thank you — the ants have it. A person reads every one.';}
else{say.textContent=(out.error||'ส่งไม่สำเร็จ / could not send')+
' — ลองใหม่อีกครั้ง / please try again';btn.disabled=false;}
}catch(err){
// A failure here must not swallow what they wrote: the text stays in the
// box, and the fallback address is one they can use without an account.
say.textContent='ส่งไม่ได้ตอนนี้ / could not send just now — '
+'อีเมลมาก็ได้ / email works too: '+cfg.email;btn.disabled=false;}
});
})();

// ---- WO-65 NOW · NEAR: the plan cell, and a ☰ that never opens on nothing --
(function(){
function nnPlan(){var el=document.querySelector('.nnplan');if(!el)return;
var n=0;try{var v=JSON.parse(localStorage.getItem('md-plan'));n=Array.isArray(v)?v.length:0;}catch(e){}
el.hidden=!n;el.innerHTML=n?'<span class="nnsep"> · </span>🗺 '+mdBi('แผนของคุณ '+n+' จุด','your plan, '+n+(n>1?' stops':' stop')):'';}
nnPlan();
document.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('.planbtn'))setTimeout(nnPlan,0);});
window.addEventListener('storage',function(e){if(!e.key||e.key==='md-plan')nnPlan();});
// The count of what is on TODAY, where today is the reader's own date. It was
// baked from BUILD_DATE, a hand-typed string, and on 2026-09-07 that string
// said the 5th on every page of the site. data/today.json carries three weeks
// forward; mdPick hands back today's entry or nothing at all.
function nnSep(el){var n=el.nextElementSibling;
while(n){if(!n.hidden&&!n.classList.contains('nnsep'))return true;n=n.nextElementSibling;}
return false;}
(async function(){var wrap=document.querySelector('.nnevwrap');if(!wrap)return;
var a=wrap.querySelector('.nnev'),sep=wrap.querySelector('.nnevsep');
var day=mdPick(await mdJSON('data/today.json'));
var n=day&&day.events;
// Nothing on today is a true answer and not an error: the cell goes rather
// than printing a nought, exactly as an empty plan does.
if(!n){nnEmpty();return;}
a.innerHTML='🎪 '+mdBi(n+' งานวันนี้',n+' on today');
wrap.hidden=false;sep.hidden=!nnSep(wrap);nnEmpty();})();
// 📍 ตรงนี้ — shown only where the browser already says granted. It is a link,
// never a redirect and never a prompt: Nan's call, 2026-09-07. Where
// navigator.permissions is missing the cell simply stays down and the reader
// still has the chip in ☰.
(function(){var el=document.querySelector('.nnhere');if(!el)return;
if(!navigator.permissions||!navigator.permissions.query)return;
navigator.permissions.query({name:'geolocation'}).then(function(st){
function paint(){var on=st.state==='granted';
el.innerHTML=on?'<span class="nnsep"> · </span>📍 '+mdBi('ตรงนี้','where I am'):'';
el.hidden=!on;nnEmpty();}
paint();st.onchange=paint;}).catch(function(){});})();
// A line with nothing true left to say is not a line. Same cleanup nnDrawer
// does for the ☰ over an empty drawer.
function nnEmpty(){document.querySelectorAll('p.nownear').forEach(function(p){
var live=Array.prototype.some.call(p.children,function(c){
return !c.hidden&&!c.classList.contains('nnsep')&&(c.textContent||'').trim();});
p.hidden=!live;});}
nnEmpty();
// search.html files the chip rows under its results; the drawer they left is
// then a glyph over nothing, so it goes too.
function nnDrawer(){document.querySelectorAll('details.morenav').forEach(function(d){
d.hidden=!d.querySelector('a');});}
window.addEventListener('load',function(){setTimeout(nnDrawer,0);});
})();
