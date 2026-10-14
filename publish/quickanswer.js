/* Quick answers in the search (Nan, 2026-10-14: "I want motdang to include a
 * calculator and currency converter like this. simple functions people
 * search for should be searchable on motdang just like google").
 *
 * Three kinds, read from the words alone:
 *   calc  — 25000*33.54, 15% of 2000, sqrt(2), (3+4)^2, "calculator"
 *   fx    — 25000 usd to thb, dollars to baht, 500 บาท เป็น เยน, "exchange rate"
 *   unit  — 5 miles to km, 30 c, 2 ไร่ เป็น ตารางเมตร, 1 บาททอง เป็น กรัม
 * The box stands above the page hits and stays live in the browser: the same
 * calculator source runs on both sides (mdCalc is shipped by toString).
 * Rates: ExchangeRate-API's open endpoint (daily, every currency); the 30-day
 * line: the ECB's reference rates through Frankfurter, for the pairs it has. */

/* ---------- calculator -------------------------------------------------- */

/* Self-contained (no outside names): it is also the page's script. */
export function mdCalc(src) {
  var t = String(src).toLowerCase()
    .replace(/[๐-๙]/g, function (d) { return String(d.charCodeAt(0) - 0x0e50); })
    .replace(/[×✕✖]/g, "*").replace(/÷/g, "/").replace(/[−–—]/g, "-")
    .replace(/(\d),(?=\d{3}(?!\d))/g, "$1").replace(/\*\*/g, "^")
    .replace(/π/g, "pi").replace(/√/g, "sqrt").replace(/ของ/g, " of ").replace(/\s+/g, " ").trim();
  var i = 0, FN = ["sqrt", "sin", "cos", "tan", "log", "ln", "abs", "exp"];
  function sp() { while (t[i] === " ") i++; }
  function at(s) { sp(); return t.slice(i, i + s.length) === s; }
  function word() { sp(); var m = /^[a-z]+/.exec(t.slice(i)); return m ? m[0] : ""; }
  function expr() {
    var a = term();
    for (;;) {
      sp(); var c = t[i];
      if (c !== "+" && c !== "-") return a;
      i++; var b = term(), r = b.p ? a.v * b.v : b.v;
      a = { v: c === "+" ? a.v + r : a.v - r };
    }
  }
  function term() {
    var a = unary();
    for (;;) {
      sp(); var c = t[i], w = word();
      if (c === "*" || c === "/" || c === "x" && w === "x") {
        i++; var b = unary(); a = { v: c === "/" ? a.v / b.v : a.v * b.v };
      } else if (w === "of" && a.p) {
        i += 2; a = { v: a.v * unary().v };
      } else if (c === "(" || w === "pi" || w === "e" || FN.indexOf(w) >= 0) {
        a = { v: a.v * unary().v };
      } else return a;
    }
  }
  function unary() {
    sp();
    if (t[i] === "-") { i++; return { v: -unary().v }; }
    if (t[i] === "+") { i++; return unary(); }
    var b = post();
    sp();
    if (t[i] === "^") { i++; return { v: Math.pow(b.v, unary().v) }; }
    return b;
  }
  function post() {
    var a = prim();
    for (;;) {
      sp();
      if (t[i] === "%") { i++; a = { v: a.v / 100, p: true }; }
      else if (t[i] === "!") {
        i++; var n = a.v, f = 1;
        if (n < 0 || n > 170 || n % 1) throw 0;
        while (n > 1) f *= n--;
        a = { v: f };
      } else return a;
    }
  }
  function prim() {
    sp();
    if (t[i] === "(") {
      i++; var a = expr(); sp();
      if (t[i] === ")") i++; else if (i < t.length) throw 0;
      return { v: a.v };
    }
    var m = /^(\d+\.?\d*|\.\d+)(e[+-]?\d+)?/.exec(t.slice(i));
    if (m) { i += m[0].length; return { v: parseFloat(m[0]) }; }
    var w = word();
    if (w === "pi") { i += 2; return { v: Math.PI }; }
    if (w === "e") { i += 1; return { v: Math.E }; }
    if (FN.indexOf(w) >= 0) {
      i += w.length; var x = unary().v;
      return { v: w === "sqrt" ? Math.sqrt(x) : w === "log" ? Math.log10(x) : w === "ln" ? Math.log(x) : Math[w](x) };
    }
    throw 0;
  }
  try {
    if (!t) return null;
    var r = expr(); sp();
    if (i < t.length || !isFinite(r.v)) return null;
    return r.v;
  } catch (e) { return null; }
}

/* The calculator answers only what reads as a sum, so a search for 7-11,
 * soi 24/7, a phone number, a house number (869/77), a date or a 4x4 still
 * reaches its pages without a box over them. */
const CALC_WORDS = /^(calculator|calc|เครื่องคิดเลข|คิดเลข|เครื่องคำนวณ|คำนวณ)$/;
const CALC_LEAD = /^(what is|whats|what's|calculate|calc|compute|คำนวณ|คิด)\s*/;
const CALC_TAIL = /\s*(=|เท่ากับ|เท่าไหร่|เท่าไร|ได้เท่าไหร่|\?)+\s*$/;
export function calcMatch(q) {
  let s = String(q || "").toLowerCase().normalize("NFKC").trim();
  if (CALC_WORDS.test(s)) return { kind: "calc", expr: "", value: null };
  const led = CALC_LEAD.test(s) || CALC_TAIL.test(s);
  s = s.replace(CALC_LEAD, "").replace(CALC_TAIL, "").trim();
  if (!s || s.length > 120) return null;
  if (!/[\d๐-๙]/.test(s)) return null;
  if (!/[+\-*/^%!×÷√π−]|\b(sqrt|sin|cos|tan|log|ln|abs|exp)\b|\d\s+x\s+\d/.test(s)) return null;
  if (!led) {
    const c = s.replace(/\s+/g, "");
    if (/^\+?\d+([-/.]\d+)*$/.test(c) && !/[*^%]/.test(c) && s === c) return null;  // 7-11, 24/7, 053-160611, 869/77
    if (/^\+\d[\d\s-]{6,}$/.test(s)) return null;                                      // +66 81 234 5678
    if (/^\d+x\d+$/.test(c)) return null;                                             // 4x4
  }
  const v = mdCalc(s);
  return v === null ? null : { kind: "calc", expr: s, value: v };
}

/* ---------- currencies and units ---------------------------------------- */

/* code, Thai, English, aliases (lower case; Thai, Burmese, Khmer and Lao
 * spellings match anywhere, Latin ones as whole words). */
export const CUR = [
  ["THB", "บาท", "Thai Baht", ["thb", "baht", "bht", "thai baht", "฿", "บาท", "เงินบาท", "ဘတ်", "បាត", "ບາດ"]],
  ["USD", "ดอลลาร์สหรัฐ", "US Dollar", ["usd", "us dollar", "us dollars", "u.s. dollar", "u.s. dollars", "american dollar", "american dollars", "dollar", "dollars", "buck", "bucks", "us$", "$", "ดอลลาร์สหรัฐ", "ดอลลาร์อเมริกา", "ดอลลาร์", "ดอลล่าร์", "ดอลล่า", "เหรียญสหรัฐ", "ဒေါ်လာ", "ដុល្លារ", "ໂດລາ"]],
  ["EUR", "ยูโร", "Euro", ["eur", "euro", "euros", "€", "ยูโร"]],
  ["GBP", "ปอนด์", "British Pound", ["gbp", "pound sterling", "pounds sterling", "british pound", "british pounds", "pound", "pounds", "quid", "£", "ปอนด์สเตอร์ลิง", "ปอนด์"]],
  ["JPY", "เยน", "Japanese Yen", ["jpy", "japanese yen", "yen", "¥", "円", "เยน"]],
  ["CNY", "หยวน", "Chinese Yuan", ["cny", "rmb", "yuan", "renminbi", "chinese yuan", "元", "หยวน"]],
  ["KRW", "วอน", "South Korean Won", ["krw", "korean won", "won", "₩", "วอน"]],
  ["MMK", "จ๊าด", "Myanmar Kyat", ["mmk", "kyat", "kyats", "จ๊าด", "ကျပ်"]],
  ["LAK", "กีบ", "Lao Kip", ["lak", "kip", "₭", "กีบ", "ກີບ"]],
  ["KHR", "เรียล", "Cambodian Riel", ["khr", "riel", "riels", "៛", "เรียล", "រៀល"]],
  ["VND", "ด่ง", "Vietnamese Dong", ["vnd", "dong", "₫", "ด่ง", "ดอง"]],
  ["MYR", "ริงกิต", "Malaysian Ringgit", ["myr", "ringgit", "ริงกิต"]],
  ["SGD", "ดอลลาร์สิงคโปร์", "Singapore Dollar", ["sgd", "singapore dollar", "singapore dollars", "s$", "ดอลลาร์สิงคโปร์"]],
  ["IDR", "รูเปียห์", "Indonesian Rupiah", ["idr", "rupiah", "รูเปียห์"]],
  ["PHP", "เปโซ", "Philippine Peso", ["php", "philippine peso", "philippine pesos", "peso", "pesos", "₱", "เปโซ"]],
  ["INR", "รูปี", "Indian Rupee", ["inr", "indian rupee", "indian rupees", "rupee", "rupees", "₹", "รูปีอินเดีย", "รูปี"]],
  ["HKD", "ดอลลาร์ฮ่องกง", "Hong Kong Dollar", ["hkd", "hong kong dollar", "hong kong dollars", "hk$", "ดอลลาร์ฮ่องกง"]],
  ["TWD", "ดอลลาร์ไต้หวัน", "Taiwan Dollar", ["twd", "taiwan dollar", "taiwan dollars", "nt$", "ดอลลาร์ไต้หวัน"]],
  ["AUD", "ดอลลาร์ออสเตรเลีย", "Australian Dollar", ["aud", "australian dollar", "australian dollars", "aussie dollar", "a$", "au$", "ดอลลาร์ออสเตรเลีย", "ดอลลาร์ออส"]],
  ["NZD", "ดอลลาร์นิวซีแลนด์", "New Zealand Dollar", ["nzd", "new zealand dollar", "new zealand dollars", "nz$", "ดอลลาร์นิวซีแลนด์"]],
  ["CAD", "ดอลลาร์แคนาดา", "Canadian Dollar", ["cad", "canadian dollar", "canadian dollars", "c$", "ca$", "ดอลลาร์แคนาดา"]],
  ["CHF", "ฟรังก์สวิส", "Swiss Franc", ["chf", "swiss franc", "swiss francs", "franc", "francs", "ฟรังก์สวิส", "ฟรังก์"]],
  ["SEK", "โครนาสวีเดน", "Swedish Krona", ["sek", "swedish krona", "kronor", "โครนาสวีเดน"]],
  ["NOK", "โครนนอร์เวย์", "Norwegian Krone", ["nok", "norwegian krone", "โครนนอร์เวย์"]],
  ["DKK", "โครนเดนมาร์ก", "Danish Krone", ["dkk", "danish krone", "โครนเดนมาร์ก"]],
  ["RUB", "รูเบิล", "Russian Ruble", ["rub", "ruble", "rubles", "rouble", "roubles", "₽", "รูเบิล"]],
  ["AED", "ดีแรห์ม", "UAE Dirham", ["aed", "dirham", "dirhams", "ดีแรห์ม", "ดิรฮัม"]],
  ["SAR", "ริยาล", "Saudi Riyal", ["sar", "riyal", "riyals", "ริยาล"]],
  ["ILS", "เชเกล", "Israeli Shekel", ["ils", "shekel", "shekels", "₪", "เชเกล"]],
  ["ZAR", "แรนด์", "South African Rand", ["zar", "rand", "แรนด์"]],
  ["BRL", "เรอัล", "Brazilian Real", ["brl", "reais", "brazilian real", "เรอัล"]],
  ["MXN", "เปโซเม็กซิโก", "Mexican Peso", ["mxn", "mexican peso", "mexican pesos", "เปโซเม็กซิโก"]],
  ["TRY", "ลีรา", "Turkish Lira", ["turkish lira", "lira", "₺", "ลีรา"]],
  ["PLN", "ซวอตี", "Polish Zloty", ["pln", "zloty", "ซวอตี"]],
  ["CZK", "โครูนา", "Czech Koruna", ["czk", "koruna", "โครูนา"]],
  ["BDT", "ตากา", "Bangladeshi Taka", ["bdt", "taka", "ตากา"]],
  ["NPR", "รูปีเนปาล", "Nepalese Rupee", ["npr", "nepalese rupee", "nepali rupee", "รูปีเนปาล"]],
  ["LKR", "รูปีศรีลังกา", "Sri Lankan Rupee", ["lkr", "sri lankan rupee", "รูปีศรีลังกา"]],
  ["PKR", "รูปีปากีสถาน", "Pakistani Rupee", ["pkr", "pakistani rupee", "รูปีปากีสถาน"]],
  ["BND", "ดอลลาร์บรูไน", "Brunei Dollar", ["bnd", "brunei dollar", "ดอลลาร์บรูไน"]],
];
const CUR_BY = Object.fromEntries(CUR.map((c) => [c[0], c]));
/* The ECB publishes these; a pair of two of them gets the 30-day line. */
const ECB = new Set(["AUD", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP", "HKD", "IDR", "ILS", "INR",
  "JPY", "KRW", "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "SEK", "SGD", "THB", "TRY", "USD", "ZAR"]);

/* dimension → [code, Thai, English, m, o, aliases]; base = (v + o) * m. */
export const UNITS = {
  length: [
    ["m", "เมตร", "metre", 1, 0, ["m", "meter", "meters", "metre", "metres", "เมตร"]],
    ["km", "กิโลเมตร", "kilometre", 1000, 0, ["km", "kms", "kilometer", "kilometers", "kilometre", "kilometres", "กิโลเมตร", "กม.", "กม"]],
    ["cm", "เซนติเมตร", "centimetre", 0.01, 0, ["cm", "centimeter", "centimeters", "centimetre", "centimetres", "เซนติเมตร", "ซม.", "ซม", "เซน"]],
    ["mm", "มิลลิเมตร", "millimetre", 0.001, 0, ["mm", "millimeter", "millimeters", "millimetre", "millimetres", "มิลลิเมตร", "มม.", "มม"]],
    ["mi", "ไมล์", "mile", 1609.344, 0, ["mi", "mile", "miles", "ไมล์"]],
    ["yd", "หลา", "yard", 0.9144, 0, ["yd", "yds", "yard", "yards", "หลา"]],
    ["ft", "ฟุต", "foot", 0.3048, 0, ["ft", "foot", "feet", "ฟุต"]],
    ["in", "นิ้ว", "inch", 0.0254, 0, ["inch", "inches", "นิ้ว", "\""]],
    ["wa", "วา", "wa (2 m)", 2, 0, ["wa", "วา"]],
    ["sok", "ศอก", "sok (50 cm)", 0.5, 0, ["sok", "ศอก"]],
  ],
  area: [
    ["m2", "ตารางเมตร", "square metre", 1, 0, ["m2", "m²", "sqm", "sq m", "sq.m.", "square meter", "square meters", "square metre", "square metres", "ตารางเมตร", "ตร.ม.", "ตร.ม", "ตรม"]],
    ["wa2", "ตารางวา", "square wa", 4, 0, ["sq wa", "square wa", "square wah", "talang wa", "ตารางวา", "ตร.ว.", "ตร.วา", "ตรว"]],
    ["ngan", "งาน", "ngan", 400, 0, ["ngan", "งาน"]],
    ["rai", "ไร่", "rai", 1600, 0, ["rai", "ไร่"]],
    ["acre", "เอเคอร์", "acre", 4046.8564224, 0, ["acre", "acres", "เอเคอร์"]],
    ["ha", "เฮกตาร์", "hectare", 10000, 0, ["ha", "hectare", "hectares", "เฮกตาร์", "เฮกแตร์"]],
    ["ft2", "ตารางฟุต", "square foot", 0.09290304, 0, ["ft2", "ft²", "sqft", "sq ft", "square foot", "square feet", "ตารางฟุต"]],
    ["km2", "ตารางกิโลเมตร", "square kilometre", 1e6, 0, ["km2", "km²", "sq km", "square kilometer", "square kilometers", "square kilometre", "square kilometres", "ตารางกิโลเมตร", "ตร.กม."]],
  ],
  mass: [
    ["kg", "กิโลกรัม", "kilogram", 1, 0, ["kg", "kgs", "kilo", "kilos", "kilogram", "kilograms", "กิโลกรัม", "กก.", "กก", "กิโล"]],
    ["g", "กรัม", "gram", 0.001, 0, ["g", "gram", "grams", "gramme", "grammes", "กรัม"]],
    ["lb", "ปอนด์", "pound", 0.45359237, 0, ["lb", "lbs", "pound", "pounds", "ปอนด์"]],
    ["oz", "ออนซ์", "ounce", 0.028349523125, 0, ["oz", "ounce", "ounces", "ออนซ์"]],
    ["st", "สโตน", "stone", 6.35029318, 0, ["stone", "stones", "สโตน"]],
    ["bg", "บาททองคำแท่ง", "baht of gold bar", 0.015244, 0, ["บาททองคำแท่ง", "ทองคำแท่ง", "baht gold", "gold baht", "บาททอง", "ทองบาท"]],
    ["bo", "บาททองรูปพรรณ", "baht of gold jewellery", 0.01516, 0, ["บาททองรูปพรรณ", "ทองรูปพรรณ"]],
    ["sl", "สลึง", "salueng (¼ baht gold bar)", 0.003811, 0, ["salueng", "สลึง"]],
  ],
  volume: [
    ["l", "ลิตร", "litre", 1, 0, ["l", "liter", "liters", "litre", "litres", "ลิตร"]],
    ["ml", "มิลลิลิตร", "millilitre", 0.001, 0, ["ml", "milliliter", "milliliters", "millilitre", "millilitres", "มิลลิลิตร", "มล.", "มล", "ซีซี", "cc"]],
    ["gal", "แกลลอน (สหรัฐ)", "US gallon", 3.785411784, 0, ["gal", "gallon", "gallons", "แกลลอน", "แกลอน"]],
    ["floz", "ออนซ์ของเหลว", "US fluid ounce", 0.0295735295625, 0, ["fl oz", "floz", "fluid ounce", "fluid ounces"]],
    ["cup", "ถ้วยตวง", "US cup", 0.2365882365, 0, ["cup", "cups", "ถ้วยตวง"]],
  ],
  speed: [
    ["kmh", "กิโลเมตร/ชั่วโมง", "km/h", 1 / 3.6, 0, ["km/h", "kmh", "kph", "kmph", "กม./ชม.", "กม/ชม", "กิโลเมตรต่อชั่วโมง"]],
    ["mph", "ไมล์/ชั่วโมง", "mph", 0.44704, 0, ["mph", "miles per hour", "ไมล์ต่อชั่วโมง"]],
    ["ms", "เมตร/วินาที", "m/s", 1, 0, ["m/s", "mps", "meters per second", "metres per second", "เมตรต่อวินาที"]],
    ["kn", "นอต", "knot", 0.514444, 0, ["knot", "knots", "kt", "นอต"]],
  ],
  temp: [
    ["c", "องศาเซลเซียส", "°C", 1, 273.15, ["°c", "c", "celsius", "centigrade", "degrees c", "degree c", "deg c", "องศาเซลเซียส", "เซลเซียส", "องศา"]],
    ["f", "องศาฟาเรนไฮต์", "°F", 5 / 9, 459.67, ["°f", "f", "fahrenheit", "degrees f", "degree f", "deg f", "องศาฟาเรนไฮต์", "ฟาเรนไฮต์"]],
    ["k", "เคลวิน", "kelvin", 1, 0, ["kelvin", "เคลวิน"]],
  ],
};
const DIM_LABEL = { length: ["ความยาว", "length"], area: ["พื้นที่", "area"], mass: ["น้ำหนัก", "weight"],
  volume: ["ปริมาตร", "volume"], speed: ["ความเร็ว", "speed"], temp: ["อุณหภูมิ", "temperature"] };
/* What a bare amount turns into when the reader names only one unit. */
const ALONE = { c: "f", f: "c", rai: "m2", ngan: "m2", wa2: "m2", bg: "g", bo: "g", sl: "g" };
const DEFAULT_TO = { length: { km: "mi", mi: "km", m: "ft", ft: "m", cm: "in", in: "cm" },
  mass: { kg: "lb", lb: "kg", g: "oz", oz: "g" }, volume: { l: "gal", gal: "l" },
  area: { m2: "wa2", acre: "rai", ha: "rai", ft2: "m2" }, speed: { kmh: "mph", mph: "kmh" }, temp: { k: "c" } };

/* Words the converter reads past; anything else on the line means the reader
 * wants pages, not a sum (a dollar shop, a baht bus, the Euro pub). */
const GLUE = ["how many", "how much", "what is", "whats", "what's", "convert", "conversion", "converter", "calculator",
  "into", "to", "in", "as", "is", "are", "=", "->", "→", "equals", "equal", "of", "a", "the", "one", "per",
  "today", "now", "rate", "rates", "exchange", "currency", "currencies", "money", "price", "unit", "units",
  "เป็น", "แปลง", "แลก", "เท่ากับ", "กี่", "เท่าไหร่", "เท่าไร", "ได้", "คือ", "วันนี้", "ตอนนี้", "ค่า", "เงิน",
  "อัตรา", "แลกเปลี่ยน", "สกุล", "หน่วย", "ราคา", "ต่อ", "ละ", "ไหม", "ครับ", "ค่ะ", "คะ", "ประมาณ", "ใน"];
const RATE_WORDS = new Set(["rate", "rates", "exchange", "currency", "currencies", "converter", "convert", "conversion",
  "แลก", "แปลง", "อัตรา", "แลกเปลี่ยน", "สกุล", "ค่า", "to", "in", "into", "เป็น", "=", "->", "→", "today", "วันนี้"]);
const CONVERTER_ONLY = [/^(currency|money) (converter|exchange|conversion)$/, /^exchange rates?$/, /^currency$/,
  /^อัตราแลกเปลี่ยน(วันนี้)?$/, /^แปลงสกุลเงิน$/, /^แลกเงิน$/, /^ค่าเงิน$/, /^แลกเปลี่ยนเงิน$/, /^fx$/];
const UNIT_ONLY = [/^unit convert(er|or)?$/, /^units? conversion$/, /^แปลงหน่วย$/];

let LEX = null;
function lexicon() {
  if (LEX) return LEX;
  const L = [];
  for (const [code, , , al] of CUR) for (const a of al) L.push([a, { cur: code }]);
  for (const [dim, rows] of Object.entries(UNITS)) {
    for (const [code, , , , , al] of rows) for (const a of al) L.push([a, { unit: code, dim }]);
  }
  for (const g of GLUE) L.push([g, { glue: g }]);
  /* one entry per spelling, its meanings joined (pound = GBP and lb) */
  const by = new Map();
  for (const [a, m] of L) {
    const o = by.get(a) || {};
    if (m.cur) o.cur = m.cur;
    if (m.unit) (o.units = o.units || []).push({ unit: m.unit, dim: m.dim });
    if (m.glue) o.glue = m.glue;
    by.set(a, o);
  }
  LEX = [...by.entries()].sort((a, b) => b[0].length - a[0].length);
  return LEX;
}
const LATIN = /[a-z]/;
const isLetter = (ch) => !!ch && /[\p{L}\p{M}]/u.test(ch) && !/[฀-๿]/.test(ch);

/* The line as numbers, currencies, units and glue — or null at the first
 * word that is none of them. */
export function scan(q) {
  let s = String(q || "").toLowerCase().normalize("NFKC")
    .replace(/[๐-๙]/g, (d) => String(d.charCodeAt(0) - 0x0e50))
    .replace(/(\d),(?=\d{3}(?!\d))/g, "$1").replace(/[?!¿]/g, " ")
    .replace(/(\d)\s*k\b/g, "$1000").replace(/\s+/g, " ").trim();
  if (!s || s.length > 80) return null;
  const out = [];
  let i = 0;
  const lex = lexicon();
  outer: while (i < s.length) {
    const ch = s[i];
    if (ch === " " || ch === "," || ch === "/" && out.length && out[out.length - 1].cur) { i++; continue; }
    const m = /^-?\d+(\.\d+)?|^\.\d+/.exec(s.slice(i));
    if (m && !(m[0][0] === "-" && out.length && out[out.length - 1].num !== undefined)) {
      out.push({ num: parseFloat(m[0]) }); i += m[0].length; continue;
    }
    for (const [a, o] of lex) {
      if (s.startsWith(a, i)) {
        if (LATIN.test(a[0]) && isLetter(s[i - 1])) continue;
        if (LATIN.test(a[a.length - 1]) && isLetter(s[i + a.length])) continue;
        out.push(o); i += a.length; continue outer;
      }
    }
    return null;
  }
  return out;
}

export function convMatch(q) {
  const raw = String(q || "").toLowerCase().normalize("NFKC").replace(/\s+/g, " ").trim();
  if (CONVERTER_ONLY.some((r) => r.test(raw))) return { kind: "fx", amt: 1, from: "USD", to: "THB", bare: true };
  if (UNIT_ONLY.some((r) => r.test(raw))) return { kind: "unit", dim: "length", amt: 1, from: "km", to: "mi", bare: true };
  const pair = /^([a-z]{3})([a-z]{3})$/.exec(raw);
  const tk = scan(pair && CUR_BY[pair[1].toUpperCase()] && CUR_BY[pair[2].toUpperCase()] ? pair[1] + " " + pair[2] : raw);
  if (!tk || !tk.length) return null;
  const nums = tk.filter((t) => t.num !== undefined);
  if (nums.length > 1) return null;
  const amt = nums.length ? nums[0].num : null;
  const named = tk.filter((t) => t.cur || t.units);
  const glue = tk.filter((t) => t.glue).map((t) => t.glue);
  const asked = glue.some((g) => RATE_WORDS.has(g));
  if (!named.length || named.length > 2) return null;
  /* units first: both named things share a dimension (1 pound to kg) */
  const dims = (t) => (t.units || []).map((u) => u.dim);
  if (named.every((t) => t.units)) {
    if (named.length === 2) {
      const d = dims(named[0]).find((x) => dims(named[1]).includes(x));
      if (d) {
        const a = named[0].units.find((u) => u.dim === d).unit, b = named[1].units.find((u) => u.dim === d).unit;
        if (a !== b) return { kind: "unit", dim: d, amt: amt === null ? 1 : amt, from: a, to: b };
      }
    } else if (amt !== null && !named[0].cur) {
      /* one unit and an amount: only the ones with a natural other side
       * (30 c, 2 ไร่), or any common one when the reader asked to convert */
      const u = named[0].units.find((x) => ALONE[x.unit]) ||
                (asked ? named[0].units.find((x) => DEFAULT_TO[x.dim] && DEFAULT_TO[x.dim][x.unit]) : null);
      if (u) return { kind: "unit", dim: u.dim, amt, from: u.unit, to: ALONE[u.unit] || DEFAULT_TO[u.dim][u.unit] };
    }
  }
  if (named.every((t) => t.cur)) {
    const from = named[0].cur;
    if (named.length === 2) {
      return named[1].cur === from ? null : { kind: "fx", amt: amt === null ? 1 : amt, from, to: named[1].cur };
    }
    if (amt !== null || asked) return { kind: "fx", amt: amt === null ? 1 : amt, from, to: from === "THB" ? "USD" : "THB" };
  }
  return null;
}

/* One reading of the line: a sum first (25000*33.54), then a conversion. */
export function quickMatch(q) {
  return calcMatch(q) || convMatch(q);
}

/* ---------- data -------------------------------------------------------- */

const HOUR = 3600e3;
let FX = null, FX_AT = 0;
export async function fxRates() {
  if (FX && Date.now() - FX_AT < HOUR) return FX;
  try {
    const r = await fetch("https://open.er-api.com/v6/latest/USD", { cf: { cacheTtl: 3600, cacheEverything: true } });
    const j = await r.json();
    if (j && j.result === "success" && j.rates && j.rates.THB) {
      FX = { rates: j.rates, at: j.time_last_update_unix * 1000 };
      FX_AT = Date.now();
    }
  } catch { /* the last copy, or none: the box stands down */ }
  return FX;
}

const HIST = new Map();
export async function fxHistory(from, to, now = Date.now()) {
  if (!ECB.has(from) || !ECB.has(to) || from === to) return null;
  const k = from + to, got = HIST.get(k);
  if (got && now - got.at < 6 * HOUR) return got.pts;
  try {
    const start = new Date(now - 31 * 86400e3).toISOString().slice(0, 10);
    const r = await fetch(`https://api.frankfurter.dev/v1/${start}..?from=${from}&to=${to}`,
      { cf: { cacheTtl: 21600, cacheEverything: true } });
    const j = await r.json();
    const pts = Object.entries(j.rates || {}).map(([d, o]) => [d, o[to]]).filter((p) => typeof p[1] === "number");
    if (pts.length > 2) { HIST.set(k, { at: now, pts }); return pts; }
  } catch { /* no line, the numbers still answer */ }
  return got ? got.pts : null;
}

export async function quickData(m) {
  if (!m || m.kind !== "fx") return null;
  const [fx, hist] = await Promise.all([fxRates(), fxHistory(m.from, m.to)]);
  return fx ? { ...fx, hist } : null;
}

/* ---------- numbers ------------------------------------------------------ */

export function fmtNum(v, money) {
  if (!isFinite(v)) return "—";
  const a = Math.abs(v);
  if (money) {
    const d = a >= 1 || a === 0 ? 2 : Math.min(8, 1 - Math.floor(Math.log10(a)) + 2);
    return v.toLocaleString("en-US", { minimumFractionDigits: a >= 1 || a === 0 ? 2 : 0, maximumFractionDigits: d });
  }
  if (a !== 0 && (a >= 1e15 || a < 1e-6)) return v.toPrecision(10).replace(/\.?0+e/, "e");
  return Number(v.toPrecision(12)).toLocaleString("en-US", { maximumFractionDigits: 10 });
}

function unitRow(dim, code) { return UNITS[dim].find((u) => u[0] === code); }
export function convert(m, data) {
  if (m.kind === "fx") {
    const R = data.rates;
    if (!R[m.from] || !R[m.to]) return null;
    return { value: m.amt * R[m.to] / R[m.from], unit: R[m.to] / R[m.from] };
  }
  const a = unitRow(m.dim, m.from), b = unitRow(m.dim, m.to);
  const base = (m.amt + a[4]) * a[3];
  return { value: base / b[3] - b[4], unit: (1 + a[4]) * a[3] / b[3] - b[4] };
}

/* ---------- page -------------------------------------------------------- */

const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const ymdhm = (t) => new Date(t + 7 * HOUR).toISOString().slice(0, 16).replace("T", " ");

/* The 30-day line. Self-contained like mdCalc: the page redraws it when the
 * reader picks two other currencies. L is "th", "en" or "" (both). */
export function mdSpark(pts, L) {
  if (!pts || pts.length < 3) return "";
  function say(th, en) { return L == "th" ? th : L == "en" ? en : th + " · " + en; }
  function f(v) { var a = Math.abs(v), d = a >= 1 ? 2 : Math.min(8, 1 - Math.floor(Math.log10(a)) + 2);
    return v.toLocaleString("en-US", { minimumFractionDigits: a >= 1 ? 2 : 0, maximumFractionDigits: d }); }
  var W = 320, H = 96, P = 4, vs = pts.map(function (p) { return p[1]; });
  var lo = Math.min.apply(null, vs), hi = Math.max.apply(null, vs), sp = hi - lo || 1;
  var line = pts.map(function (p, i) {
    return (P + i * (W - 2 * P) / (pts.length - 1)).toFixed(1) + "," + (P + (H - 2 * P) * (1 - (p[1] - lo) / sp)).toFixed(1);
  }).join(" ");
  var up = vs[vs.length - 1] >= vs[0] ? "up" : "dn", ch = (vs[vs.length - 1] / vs[0] - 1) * 100;
  function d(s) { return s.slice(8, 10) + "/" + s.slice(5, 7); }
  return '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="30 days">'
    + '<polygon points="' + P + "," + (H - P) + " " + line + " " + (W - P) + "," + (H - P) + '" class="qa-fill ' + up + '"/>'
    + '<polyline points="' + line + '" class="qa-line ' + up + '"/></svg>'
    + "<figcaption><span>" + d(pts[0][0]) + " – " + d(pts[pts.length - 1][0]) + "</span>"
    + "<span><span>" + say("ต่ำสุด", "low") + "</span> " + f(lo) + " · <span>" + say("สูงสุด", "high") + "</span> " + f(hi) + "</span>"
    + '<b class="' + up + '">' + (ch >= 0 ? "+" : "") + ch.toFixed(2) + "% · <span>" + say("30 วัน", "30 days") + "</span></b></figcaption>";
}

function opts(list, sel) {
  return list.map((o) => `<option value="${esc(o.k)}"${o.k === sel ? " selected" : ""}>${esc(o.th)} · ${esc(o.en)}${o.code ? " (" + o.code + ")" : ""}</option>`).join("");
}

/* The page's script: one function per kind, reading the box's own data. */
const QA_JS = `(function(){function run(){var b=document.querySelector(".qa");if(!b)return;var D=JSON.parse(b.dataset.qa),r=document.documentElement,
L=r.classList.contains("lang-th")?"th":r.classList.contains("lang-en")?"en":"";function nm(o){return L=="th"?o.th:L=="en"?o.en:o.th+" · "+o.en}
function f(v,m){if(!isFinite(v))return"—";var a=Math.abs(v);if(m){var d=a>=1||a===0?2:Math.min(8,1-Math.floor(Math.log10(a))+2);return v.toLocaleString("en-US",{minimumFractionDigits:a>=1||a===0?2:0,maximumFractionDigits:d})}
if(a!==0&&(a>=1e15||a<1e-6))return v.toPrecision(10).replace(/\\.?0+e/,"e");return Number(v.toPrecision(12)).toLocaleString("en-US",{maximumFractionDigits:10})}
var calc=${mdCalc.toString()};
if(D.kind=="calc"){var x=b.querySelector(".qa-x"),o=b.querySelector(".qa-out"),h=b.querySelector(".qa-was");
function show(){var v=calc(x.value);o.textContent=x.value.trim()?(v===null?"…":f(v)):"0"}
x.addEventListener("input",show);b.querySelector(".qa-keys").addEventListener("click",function(e){var k=e.target.closest("button");if(!k)return;e.preventDefault();var c=k.dataset.k;
if(c=="AC")x.value="";else if(c=="del")x.value=x.value.slice(0,-1);else if(c=="="){var v=calc(x.value);if(v!==null){h.textContent=x.value+" =";x.value=String(Number(v.toPrecision(12)))}}else x.value+=c;show();x.focus()});
b.querySelector("form").addEventListener("submit",function(e){e.preventDefault();var v=calc(x.value);if(v!==null){h.textContent=x.value+" =";x.value=String(Number(v.toPrecision(12)));show()}});return}
var A=b.querySelector(".qa-a"),B=b.querySelector(".qa-b"),SA=b.querySelector(".qa-sa"),SB=b.querySelector(".qa-sb"),H1=b.querySelector(".qa-h1"),H2=b.querySelector(".qa-h2"),M=D.kind=="fx";
function by(k){for(var i=0;i<D.list.length;i++)if(D.list[i].k==k)return D.list[i]}
function cv(v,a,c){return((v+a.o)*a.m)/c.m-c.o}
function num(s){return parseFloat(String(s).replace(/[,\\s]/g,"").replace(/[\\u0e50-\\u0e59]/g,function(d){return d.charCodeAt(0)-0x0e50}))}
function head(){var a=by(SA.value),c=by(SB.value);H1.textContent="1 "+nm(a)+" "+(L=="th"?"เท่ากับ":L=="en"?"equals":"เท่ากับ · equals");H2.textContent=f(cv(1,a,c),M)+" "+nm(c)}head();
function go(fromB){var a=by(SA.value),c=by(SB.value);if(fromB){var w=num(B.value);A.value=isFinite(w)?f(cv(w,c,a),M).replace(/,/g,""):""}else{var v=num(A.value);B.value=isFinite(v)?f(cv(v,a,c),M).replace(/,/g,""):""}head()}
var spark=${mdSpark.toString()},seen={},tk=0;seen[D.from+D.to]=D.hist;
function draw(p){var ch=b.querySelector(".qa-chart");if(!ch)return;ch.innerHTML=spark(p,L);ch.hidden=!p;ch.style.opacity=1}
function line(){if(!M)return;var k=SA.value+SB.value,ch=b.querySelector(".qa-chart"),me=++tk;if(k in seen)return draw(seen[k]);if(ch)ch.style.opacity=.3;
fetch("/find?fmt=json&q="+encodeURIComponent("1 "+SA.value+" to "+SB.value)).then(function(r){return r.json()}).then(function(j){seen[k]=j.quick&&j.quick.history||null;if(me==tk)draw(seen[k])}).catch(function(){if(me==tk)draw(null)})}
if(M)draw(D.hist);
A.addEventListener("input",function(){go(0)});B.addEventListener("input",function(){go(1)});
SA.addEventListener("change",function(){go(0);line()});SB.addEventListener("change",function(){go(0);line()});
b.querySelector(".qa-swap").addEventListener("click",function(e){e.preventDefault();var t=SA.value;SA.value=SB.value;SB.value=t;go(0);line()})}
/* after the page's language script, so the headline speaks the reader's language */
if(document.readyState=="loading")document.addEventListener("DOMContentLoaded",run);else run()})()`;

export function quickHtml(m, data) {
  if (!m) return "";
  if (m.kind === "calc") {
    const keys = [["(", ")", "%", "AC"], ["7", "8", "9", "÷"], ["4", "5", "6", "×"], ["1", "2", "3", "−"],
      ["0", ".", "=", "+"], ["√", "^", "π", "⌫"]];
    const k = (c) => `<button type="button" data-k="${{ "AC": "AC", "⌫": "del", "√": "√(" }[c] || esc(c)}"${/[÷×−+=^%]/.test(c) ? ' class="op"' : c === "AC" || c === "⌫" ? ' class="fn"' : ""}>${esc(c)}</button>`;
    const out = m.value === null ? "0" : fmtNum(m.value);
    return `<section class="qa qa-calc" aria-label="เครื่องคิดเลข · Calculator" data-qa='${esc(JSON.stringify({ kind: "calc" }))}'>`
      + `<h2>เครื่องคิดเลข · Calculator</h2>`
      + `<form action="/find" method="get"><p class="qa-was">${m.expr ? esc(m.expr) + " =" : ""}</p>`
      + `<input class="qa-x" name="q" value="${esc(m.expr)}" inputmode="decimal" autocomplete="off" aria-label="นิพจน์ · expression">`
      + `<output class="qa-out" aria-live="polite">${out}</output></form>`
      + `<div class="qa-keys">${keys.map((r) => r.map(k).join("")).join("")}</div>`
      + `<script>${QA_JS}</script></section>`;
  }
  let list, srcLine = "", chart = "", title;
  if (m.kind === "fx") {
    if (!data || !data.rates[m.from] || !data.rates[m.to]) return "";
    const R = data.rates;
    list = CUR.filter((c) => R[c[0]]).map((c) => ({ k: c[0], code: c[0], th: c[1], en: c[2], m: 1 / R[c[0]], o: 0 }));
    title = "แปลงสกุลเงิน · Currency converter";
    srcLine = `<span>อัตรากลางตลาด · mid-market rate</span>, <span>ปรับเมื่อ · updated</span> ${ymdhm(data.at)} (UTC+7) · `
      + `<a href="https://www.exchangerate-api.com" rel="noopener">Rates By Exchange Rate API</a>`
      + (data.hist ? ` · กราฟ · chart: <a href="https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html" rel="noopener">ECB</a> via <a href="https://frankfurter.dev" rel="noopener">Frankfurter</a>` : "");
    chart = `<figure class="qa-chart"${data.hist ? "" : " hidden"}>${mdSpark(data.hist, "")}</figure>`;
  } else {
    list = UNITS[m.dim].map((u) => ({ k: u[0], th: u[1], en: u[2], m: u[3], o: u[4] }));
    title = `แปลงหน่วย${DIM_LABEL[m.dim][0]} · ${DIM_LABEL[m.dim][1]} converter`;
  }
  const money = m.kind === "fx";
  const a = list.find((x) => x.k === m.from), b = list.find((x) => x.k === m.to);
  const r = convert(m, data);
  if (!r) return "";
  const h1 = `1 <span>${esc(a.th)} · ${esc(a.en)}</span> <span>เท่ากับ · equals</span>`;
  const h2 = `${fmtNum(r.unit, money)} <span>${esc(b.th)} · ${esc(b.en)}</span>`;
  const box = { kind: m.kind, from: m.from, to: m.to, list, hist: m.kind === "fx" ? data.hist || null : undefined };
  return `<section class="qa qa-conv" aria-label="${esc(title)}" data-qa='${esc(JSON.stringify(box))}'>`
    + `<h2>${esc(title)}</h2>`
    + `<p class="qa-h1">${h1}</p><p class="qa-h2">${h2}</p>`
    + `<div class="qa-io"><div class="qa-rows">`
    + `<label class="qa-row"><input class="qa-a" value="${esc(String(m.amt))}" inputmode="decimal" aria-label="จำนวน · amount"><select class="qa-sa" aria-label="จาก · from">${opts(list, m.from)}</select></label>`
    + `<label class="qa-row"><input class="qa-b" value="${esc(fmtNum(r.value, money).replace(/,/g, ""))}" inputmode="decimal" aria-label="ผล · result"><select class="qa-sb" aria-label="เป็น · to">${opts(list, m.to)}</select></label>`
    + `</div><button class="qa-swap" type="button" aria-label="สลับ · swap">⇅</button></div>`
    + chart
    + (srcLine ? `<p class="qa-src">${srcLine}</p>` : "")
    + `<script>${QA_JS}</script></section>`;
}

export function quickJson(m, data) {
  if (!m) return undefined;
  if (m.kind === "calc") return { kind: "calc", expression: m.expr || undefined, value: m.value === null ? undefined : m.value };
  if (m.kind === "fx" && !data) return undefined;
  const r = convert(m, data);
  if (!r) return undefined;
  return { kind: m.kind, dimension: m.dim, amount: m.amt, from: m.from, to: m.to, value: r.value, per_unit: r.unit,
    rate_time: m.kind === "fx" ? new Date(data.at).toISOString() : undefined,
    source: m.kind === "fx" ? "https://www.exchangerate-api.com" : undefined,
    history: m.kind === "fx" && data.hist ? data.hist : undefined };
}

export const QA_CSS = `
.qa{margin:.9em 0 1em;padding:.7em 1em .8em;border:2px solid var(--ink);border-radius:.7em;background:#fff;max-width:36em;box-shadow:3px 3px 0 #f1c40f}
.qa h2{margin:0 0 .3em;font-size:.95em;color:var(--mute);font-weight:normal}
.qa-h1{margin:0;color:var(--mute)}.qa-h2{margin:.05em 0 .5em;font-size:2em;line-height:1.15;font-weight:bold;color:var(--ink)}
.qa-io{display:flex;gap:.5em;align-items:center}.qa-rows{flex:1;min-width:0}
.qa-row{display:flex;margin:0 0 .45em;border:1.5px solid var(--rule);border-radius:.5em;overflow:hidden;background:#fff}
.qa-row:focus-within{border-color:#24406E;box-shadow:0 0 0 1px #24406E}
.qa-row input{flex:1 1 40%;min-width:0;border:0;padding:.55em .7em;font:inherit;font-size:1.2em;background:transparent;color:var(--ink)}
.qa-row select{flex:1 1 60%;min-width:0;border:0;border-left:1px solid var(--rule);padding:.5em;font:inherit;background:#fffaf0;color:var(--ink)}
.qa-swap{border:1.5px solid var(--rule);background:#fffaf0;border-radius:99px;width:2.4em;height:2.4em;font-size:1.1em;cursor:pointer;color:var(--ink)}
.qa-chart{margin:.4em 0 0;transition:opacity .2s}.qa-chart svg{display:block;width:100%;height:6em}
.qa-line{fill:none;stroke-width:2;vector-effect:non-scaling-stroke}.qa-line.up{stroke:#1e7a3c}.qa-line.dn{stroke:#b3261e}
.qa-fill.up{fill:#1e7a3c18}.qa-fill.dn{fill:#b3261e18}
.qa-chart figcaption{display:flex;flex-wrap:wrap;gap:.2em 1em;justify-content:space-between;font-size:.82em;color:var(--mute)}
.qa-chart b.up{color:#1e7a3c}.qa-chart b.dn{color:#b3261e}
.qa-src{margin:.5em 0 0;font-size:.78em;color:var(--mute);line-height:1.45}.qa-src a{color:var(--mute)}
.qa-calc form{margin:0 0 .5em;padding:.4em .6em;border:1.5px solid var(--rule);border-radius:.5em;text-align:right}
.qa-was{margin:0;min-height:1.2em;font-size:.85em;color:var(--mute);overflow-wrap:anywhere}
.qa-x{width:100%;box-sizing:border-box;border:0;text-align:right;font:inherit;font-size:1.05em;color:var(--mute);background:transparent;padding:0}
.qa-out{display:block;font-size:2em;font-weight:bold;overflow-wrap:anywhere;color:var(--ink)}
.qa-keys{display:grid;grid-template-columns:repeat(4,1fr);gap:.35em}
.qa-keys button{font:inherit;font-size:1.15em;padding:.5em 0;border:1px solid var(--rule);border-radius:.45em;background:#fffaf0;color:var(--ink);cursor:pointer}
.qa-keys button.op{background:#f1e6cc}.qa-keys button.fn{background:#eee6d6}
.qa-keys button[data-k="="]{background:#24406E;color:#fff;border-color:#24406E}
`;
