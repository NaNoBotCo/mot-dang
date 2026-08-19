#!/usr/bin/env python3
"""Bake the per-sign horoscope engine: data/horo.json.

Three systems, each divided out by its own signs and each computed, never
improvised — the same date gives the same reading on every machine, and the
arithmetic is stated where a reader can check it.

  Thai     — มหาทักษา (Mahathaksa): the eight day-deities on their wheel
             (อาทิตย์ จันทร์ อังคาร พุธ เสาร์ พฤหัสบดี ราหู ศุกร์). Your birth
             day takes the บริวาร seat and the other seven stations follow in
             order round the wheel, so where TODAY's deity sits in YOUR wheel
             is pure modular arithmetic — and it reproduces the classical
             pairings exactly (a Sunday child's กาลกิณี is Friday, a Monday
             child's is Sunday, and so on for all eight).
             The animal year turns at วันเถลิงศก, computed from the จุลศักราช
             day-count (horakhun): JD = 1954167.5 + (292207·CS + 373)//800.
             That lands 16 Apr for 2025–2027, matching the published almanacs;
             the fixed "13 April" shortcut is wrong for the 13th–15th.
  Chinese  — the sexagenary day pillar (anchored 2000-01-07 = 甲子, same as
             ../taoist-oracle) set against the reader's birth-year branch with
             the classical relations: 沖 ชง, 六合 ฮะ, 三合 สามฮะ, 刑 เฮ้ง,
             害 ไห่, 破 ผั่ว — each one a fixed pairing on the twelve-branch
             circle. Year identity uses ตรุษจีน (Chinese New Year), computed
             from ../taoist-oracle's astronomical lunisolar calendar and baked
             as a table 1920–2030; 立春 is baked beside it because the four-
             pillars page counts years from there and the two differ by days.
  Western  — the Sun, Moon and five classical planets placed on the tropical
             zodiac (Meeus low-precision Sun/Moon, Schlyter elements for the
             planets — within about half a degree, ample for a 30° sign), then
             whole-sign aspects from each transit to each sun sign. Sign
             boundaries are the Sun's actual ingress instants, found by
             iteration, not a fixed date table — so a cusp birthday resolves
             by the year it happened in.

Everything a renderer needs — the bilingual tables, the year boundaries, and
a window of per-day positions — lands in ONE file so the Python page builder
and assets/horo.js read the same words and the same numbers and cannot drift.
tests/test_horo_parity.py holds the two implementations together.

    python3 importers/make_horo.py             # 180 days
    python3 importers/make_horo.py --days 366

If ../taoist-oracle is missing the ตรุษจีน/立春 tables are carried over from
the existing data/horo.json rather than dropped (snapshot-first, like every
other importer here).
"""
import json
import math
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "horo.json")
ORACLE = os.path.abspath(os.path.join(ROOT, "..", "taoist-oracle"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_fortune import (THAI_DAYS, WEDNESDAY_NIGHT, SIGNS,  # noqa: E402
                          moon_longitude, WUXING_REL)

RAD = math.pi / 180.0
YEAR_FROM, YEAR_TO = 1920, 2030


# ---------------------------------------------------------------- shared time
def greg_to_jd(y, m, d, hour=0.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + d + b - 1524.5 + hour / 24.0)


def jd_to_greg(jd):
    jd = jd + 0.5
    z = math.floor(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    dd = math.floor(365.25 * c)
    e = math.floor((b - dd) / 30.6001)
    day = b - dd - math.floor(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return int(year), int(month), int(math.floor(day))


# ---------------------------------------------------------------- Thai system
# Eight day-slots, Sunday-first: 0=Sun … 6=Sat, 7=Wednesday night (ราหู).
# Rows come straight from make_fortune's tables so colour, Buddha image and
# กำลัง can never disagree with the Today tile.
_MF = {  # make_fortune's THAI_DAYS is Monday-indexed
    0: THAI_DAYS[6], 1: THAI_DAYS[0], 2: THAI_DAYS[1], 3: THAI_DAYS[2],
    4: THAI_DAYS[3], 5: THAI_DAYS[4], 6: THAI_DAYS[5], 7: WEDNESDAY_NIGHT,
}
DAY_ABBR = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส", "ราหู"]
DAY_ART_KEY = {2: "pang-saiyat", 4: "pang-samathi", 6: "pang-nak-prok",
               7: "pang-palelai"}

# The wheel order of the eight deities — อาทิตย์ จันทร์ อังคาร พุธ เสาร์
# พฤหัสบดี ราหู ศุกร์ — as day-slot indices. This order IS the ตำรา; every
# classical กาลกิณี pairing falls out of it and the self-check below insists.
WHEEL = [0, 1, 2, 3, 6, 4, 7, 5]

STATIONS = [
    {"th": "บริวาร", "en": "Boriwan", "mean_th": "คนรอบตัว ครอบครัว มิตรสหาย",
     "mean_en": "your people — family, team, friends",
     "line_th": "วันของคนรอบตัว งานที่ทำด้วยกันไปได้ดี ชวนกันทำ อย่าทำคนเดียว",
     "line_en": "A day for your people — shared work goes well; do it together rather than alone.",
     "v": "ดี"},
    {"th": "อายุ", "en": "Ayu", "mean_th": "ชีวิตความเป็นอยู่ สุขภาพ",
     "mean_en": "life and health",
     "line_th": "ดูแลกายใจ กินดี นอนพอ เรื่องสุขภาพที่ค้างไว้เหมาะจัดการวันนี้",
     "line_en": "Tend body and mind — eat well, rest enough; a good day for the health matter you postponed.",
     "v": "กลาง"},
    {"th": "เดช", "en": "Det", "mean_th": "อำนาจ เกียรติ ความน่าเกรงขาม",
     "mean_en": "authority and standing",
     "line_th": "เสียงของคุณมีน้ำหนัก เหมาะเจรจา นำประชุม ขอในสิ่งที่ควรได้",
     "line_en": "Your word carries weight — negotiate, lead, ask for what is due.",
     "v": "ดี"},
    {"th": "ศรี", "en": "Si", "mean_th": "สิริมงคล โชคลาภ เสน่ห์",
     "mean_en": "grace and good fortune",
     "line_th": "วันเปิดทาง เหมาะเริ่มสิ่งใหม่ ออกปากขอ ความเมตตาไหลเข้ามา",
     "line_en": "An opening day — begin things, ask favours; goodwill flows your way.",
     "v": "ดี"},
    {"th": "มูละ", "en": "Mula", "mean_th": "ทรัพย์เดิม บ้าน มรดก",
     "mean_en": "property, home, what you already hold",
     "line_th": "เหมาะดูแลบ้านและทรัพย์ เก็บ ซ่อม ตามของเดิม เงินเก่ากลับมา",
     "line_en": "Tend what you own — save, repair, follow up; old value returns.",
     "v": "ดี"},
    {"th": "อุตสาหะ", "en": "Utsaha", "mean_th": "ความเพียร งานที่ต้องออกแรง",
     "mean_en": "steady effort",
     "line_th": "งานที่ต้องออกแรงคืบหน้าแน่ถ้าลงมือ ค่อยๆ ไปก็ถึง",
     "line_en": "Work that needs elbow grease moves today — steady effort reaches the mark.",
     "v": "กลาง"},
    {"th": "มนตรี", "en": "Montri", "mean_th": "ผู้ใหญ่ ครู ผู้อุปถัมภ์",
     "mean_en": "patrons, teachers, elders",
     "line_th": "เข้าหาผู้ใหญ่ ครู เจ้านาย ได้แรงหนุน เรื่องเอกสารราชการลื่น",
     "line_en": "Approach elders, teachers, officials — support comes down; paperwork moves.",
     "v": "ดี"},
    {"th": "กาลกิณี", "en": "Kalakini", "mean_th": "แรงเสียดทาน เรื่องกวนใจ",
     "mean_en": "friction",
     "line_th": "วันเบาๆ เลี่ยงเริ่มเรื่องใหญ่ ใจเย็นเข้าไว้ ทำบุญสักหน่อยก็ชื่นใจ",
     "line_en": "Keep the day light — hold the big launch, keep cool; a small act of merit settles it.",
     "v": "ระวัง"},
]

THAI_ZODIAC = [
    ("ชวด", "Rat"), ("ฉลู", "Ox"), ("ขาล", "Tiger"), ("เถาะ", "Rabbit"),
    ("มะโรง", "Dragon"), ("มะเส็ง", "Snake"), ("มะเมีย", "Horse"), ("มะแม", "Goat"),
    ("วอก", "Monkey"), ("ระกา", "Rooster"), ("จอ", "Dog"), ("กุน", "Pig"),
]
ZODIAC_EMOJI = ["🐀", "🐂", "🐅", "🐇", "🐉", "🐍", "🐎", "🐐", "🐒", "🐓", "🐕", "🐖"]


def thaloengsok_jd(cs):
    """JD (00:00 UT) of วันเถลิงศก opening จุลศักราช year cs — the horakhun
    day-count from the CS epoch, the piece of the สุริยยาตร์ this needs."""
    return 1954167.5 + (292207 * cs + 373) // 800


def thaloengsok_date(cs):
    return date(*jd_to_greg(thaloengsok_jd(cs)))


def cs_for_date(d):
    """จุลศักราช year the civil date sits in (turns at เถลิงศก)."""
    cs = d.year - 638
    if d < thaloengsok_date(cs):
        cs -= 1
    elif d >= thaloengsok_date(cs + 1):
        cs += 1
    return cs


def thai_animal_index(cs):
    return (cs + 10) % 12          # CS 1388 (from 16 Apr 2026) = มะเมีย, index 6


def wheel_station(birth_slot, today_slot):
    """Station index where today's deity stands in the wheel of someone born
    on birth_slot. 0 = บริวาร … 7 = กาลกิณี."""
    return (WHEEL.index(today_slot) - WHEEL.index(birth_slot)) % 8


# ------------------------------------------------------------- Chinese system
BRANCH_TH = ["ชวด", "ฉลู", "ขาล", "เถาะ", "มะโรง", "มะเส็ง",
             "มะเมีย", "มะแม", "วอก", "ระกา", "จอ", "กุน"]
BRANCH_ZH = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_EN = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
             "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
STEM_ZH = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_ELEMENT = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]      # Wood Wood Fire … Water
ELEM_TH = ["ไม้", "ไฟ", "ดิน", "ทอง", "น้ำ"]
ELEM_EN = ["Wood", "Fire", "Earth", "Metal", "Water"]

DAY_ANCHOR_JD = greg_to_jd(2000, 1, 7) - 8.0 / 24.0    # 甲子, same as the oracle


def day_pillar_index(d):
    return round(greg_to_jd(d.year, d.month, d.day) - 8.0 / 24.0
                 - DAY_ANCHOR_JD) % 60


# The six fixed pairings of each kind on the branch circle, written as rules
# (they are rules): 沖 opposite, 六合 sums to 1, 害 sums to 7 (mod 12).
PO_PAIRS = {(0, 9), (1, 4), (2, 11), (3, 6), (5, 8), (7, 10)}
XING_GROUPS = [{2, 5, 8}, {1, 7, 10}, {0, 3}]
XING_SELF = {4, 6, 9, 11}


def branch_relation(day_b, your_b):
    """Today's branch against your year branch: the strongest single relation,
    checked in the traditional order of weight."""
    if (day_b - your_b) % 12 == 6:
        return "chong"
    if (day_b + your_b) % 12 == 1:
        return "liuhe"
    if day_b != your_b and (day_b - your_b) % 12 in (4, 8):
        return "sanhe"
    if day_b == your_b:
        return "same"
    for g in XING_GROUPS:
        if day_b in g and your_b in g:
            return "xing"
    if (day_b + your_b) % 12 == 7:
        return "hai"
    if (day_b, your_b) in PO_PAIRS or (your_b, day_b) in PO_PAIRS:
        return "po"
    return "plain"


DAY_REL = {
    "chong": {"zh": "沖", "th": "ชง", "en": "clash", "v": "ระวัง",
              "line_th": "วันชงของปีคุณ งดตัดสินใจเรื่องใหญ่ เลื่อนได้ก็เลื่อน ใจเย็นเข้าไว้",
              "line_en": "The day clashes with your year — hold the big decision if you can, and keep your temper."},
    "liuhe": {"zh": "六合", "th": "ฮะ", "en": "harmony", "v": "ดี",
              "line_th": "วันสมพงศ์กับปีคุณ คุยอะไรก็เข้ากัน เหมาะนัดพบ จับมือ ตกลง",
              "line_en": "In harmony with your year — meetings, matches and agreements go smoothly."},
    "sanhe": {"zh": "三合", "th": "สามฮะ", "en": "trine of allies", "v": "ดี",
              "line_th": "สามฮะหนุน มีแรงส่งจากเพื่อนและพันธมิตร งานร่วมไปได้ไกล",
              "line_en": "The triangle supports you — allies push the work along."},
    "same": {"zh": "伏", "th": "ทับปี", "en": "own-year day", "v": "กลาง",
             "line_th": "วันตรงปีคุณพอดี เรื่องเก่าวนกลับมาให้ปิดให้จบ",
             "line_en": "The day mirrors your year — an old matter circles back to be finished."},
    "xing": {"zh": "刑", "th": "เฮ้ง", "en": "testing", "v": "กลาง",
             "line_th": "วันเฮ้ง กติกาและปากเสียงเป็นเรื่องใหญ่ อ่านสัญญาให้ครบ อย่ารับปากลอยๆ",
             "line_en": "A testing day — read the fine print, promise nothing loosely."},
    "hai": {"zh": "害", "th": "ไห่", "en": "scraping", "v": "กลาง",
            "line_th": "วันเสียดสี คำพูดเล็กๆ อาจบาดใจ พูดน้อยลง ฟังมากขึ้น",
            "line_en": "A scraping day — small words can cut; say less, listen more."},
    "po": {"zh": "破", "th": "ผั่ว", "en": "wobble", "v": "กลาง",
           "line_th": "ของเก่าอาจสะดุด อย่าเพิ่งรื้อของดีที่มีอยู่ ซ่อมได้ให้ซ่อม",
           "line_en": "Old arrangements wobble — mend rather than break."},
    "plain": {"zh": "", "th": "ปกติ", "en": "even", "v": "กลาง",
              "line_th": "วันเรียบๆ กับปีคุณ เดินหน้าตามแผนได้",
              "line_en": "An even day for your year — proceed as planned."},
}

# ปีชง, the year-level relations Thai readers know from every มูเตลู column:
# the year branch against yours, in the ชง-เฮ้ง-ไห่-ผั่ว vocabulary.
YEAR_REL = {
    "chong": {"th": "ปีชงตรง", "en": "direct clash year", "v": "ระวัง",
              "line_th": "ปีนี้ชงตรงกับปีคุณ ตามธรรมเนียมนิยมไหว้ไท้ส่วยเอี๊ยรับปี "
                         "ทำบุญใหญ่สักครั้ง แล้วเดินปีอย่างมีสติ",
              "line_en": "A direct-clash year for your sign — tradition favours paying respects to Tai Sui, one solid act of merit, and walking the year mindfully."},
    "same": {"th": "ปีทับ (ชงร่วม)", "en": "own-branch year", "v": "กลาง",
             "line_th": "ปีนักษัตรเดียวกับปีเกิด ตำราจัดเป็นชงร่วม ปีแห่งการทบทวนตัวเอง",
             "line_en": "The year shares your branch — counted a companion clash; a year for taking stock."},
    "xing": {"th": "ปีเฮ้ง (ชงร่วม)", "en": "testing year", "v": "กลาง",
             "line_th": "ปีเฮ้งของคุณ เรื่องกติกา สัญญา ระเบียบ ทำให้เรียบร้อยแต่เนิ่นๆ",
             "line_en": "A testing year — contracts and rules reward early tidiness."},
    "hai": {"th": "ปีไห่ (ชงร่วม)", "en": "scraping year", "v": "กลาง",
            "line_th": "ปีไห่ของคุณ ถนอมน้ำใจคนใกล้ตัวเป็นพิเศษ",
            "line_en": "A scraping year — take particular care of those close to you."},
    "po": {"th": "ปีผั่ว (ชงร่วม)", "en": "wobble year", "v": "กลาง",
           "line_th": "ปีผั่วของคุณ ของเดิมที่ดีอยู่แล้วอย่าเพิ่งรื้อ",
           "line_en": "A wobble year — do not dismantle what already serves you."},
    "liuhe": {"th": "ปีฮะ", "en": "harmonious year", "v": "ดี",
              "line_th": "ปีสมพงศ์ของคุณ จับมือ ร่วมทุน ผูกมิตร ได้จังหวะดี",
              "line_en": "A harmonious year for your sign — partnerships and alliances find their moment."},
    "sanhe": {"th": "ปีสามฮะ", "en": "allied year", "v": "ดี",
              "line_th": "ปีสามฮะหนุนคุณ ขยับขยายได้ มีคนช่วยออกแรง",
              "line_en": "An allied year — room to grow, with hands to help."},
    "plain": {"th": "ปีปกติ", "en": "even year", "v": "กลาง",
              "line_th": "ปีเรียบๆ ของคุณ เดินตามแผนที่วางไว้",
              "line_en": "An even year for your sign — keep to the plan you made."},
}


# ------------------------------------------------------------- Western system
SIGN_GLYPH = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
SIGN_RULER = [4, 3, 2, 1, 0, 2, 3, 4, 5, 6, 6, 5]   # classical rulers, index into PLANETS
ELEMENT_TH = {"fire": "ธาตุไฟ", "earth": "ธาตุดิน", "air": "ธาตุลม", "water": "ธาตุน้ำ"}
ELEMENT_EN = {"fire": "fire", "earth": "earth", "air": "air", "water": "water"}

PLANETS = [
    {"th": "อาทิตย์", "en": "Sun", "glyph": "☉", "kind": "mid",
     "theme_th": "กำลังกายและความมั่นใจ", "theme_en": "vitality and confidence"},
    {"th": "จันทร์", "en": "Moon", "glyph": "☽", "kind": "benefic",
     "theme_th": "อารมณ์และเรื่องใกล้ตัว", "theme_en": "mood and home matters"},
    {"th": "พุธ", "en": "Mercury", "glyph": "☿", "kind": "mid",
     "theme_th": "การพูด เอกสาร การเดินทางสั้น", "theme_en": "words, papers, short trips"},
    {"th": "ศุกร์", "en": "Venus", "glyph": "♀", "kind": "benefic",
     "theme_th": "ความรัก ของสวย เงินทอง", "theme_en": "love, beauty, money"},
    {"th": "อังคาร", "en": "Mars", "glyph": "♂", "kind": "malefic",
     "theme_th": "แรงลุยและความกล้า", "theme_en": "drive and daring"},
    {"th": "พฤหัสบดี", "en": "Jupiter", "glyph": "♃", "kind": "benefic",
     "theme_th": "โชค การขยับขยาย ครูอาจารย์", "theme_en": "luck, growth, teachers"},
    {"th": "เสาร์", "en": "Saturn", "glyph": "♄", "kind": "malefic",
     "theme_th": "หน้าที่ วินัย งานระยะยาว", "theme_en": "duty, discipline, the long haul"},
]

# Whole-sign separations → classical aspect. 0 ร่วมราศี, 2/10 โยคเกณฑ์,
# 3/9 จตุโกณ, 4/8 ตรีโกณ, 6 เล็ง; anything else is no aspect.
ASPECT_OF = {0: "conj", 2: "sextile", 10: "sextile", 3: "square", 9: "square",
             4: "trine", 8: "trine", 6: "opp"}
ASPECTS = {
    "conj": {"th": "ร่วมราศี", "en": "in your sign", "sharp": 3,
             "line_th": "มาอยู่ในราศีคุณ เรื่องนี้เด่นขึ้นมาก",
             "line_en": "stands in your own sign — this theme moves to the front"},
    "sextile": {"th": "โยคเกณฑ์", "en": "sextile", "sharp": 1,
                "line_th": "เปิดโอกาสเล็กๆ ที่ต้องยื่นมือไปรับ",
                "line_en": "opens a small door — it needs you to reach for it"},
    "square": {"th": "จตุโกณ", "en": "square", "sharp": 2,
               "line_th": "มีแรงเสียดทาน แต่เป็นแรงที่ผลักให้ขยับ",
               "line_en": "brings friction, the kind that gets you moving"},
    "trine": {"th": "ตรีโกณ", "en": "trine", "sharp": 2,
              "line_th": "หนุนให้ไหลลื่น เหมาะเดินหน้า",
              "line_en": "carries things along — a theme that flows"},
    "opp": {"th": "เล็ง", "en": "opposition", "sharp": 2,
            "line_th": "อยู่ฝั่งตรงข้าม ต้องหาจุดสมดุล",
            "line_en": "faces you from across the wheel — balance is the work"},
}
PLANET_WEIGHT = [1, 0, 1, 2, 2, 3, 3]   # Moon handled separately; slow = weighty


def aspect_score(pi, akey):
    """ดี/กลาง/ระวัง arithmetic, the classical way round: benefics helping,
    malefics testing, soft aspects easing, hard aspects pressing."""
    kind = PLANETS[pi]["kind"]
    if akey in ("trine", "sextile"):
        return 2 if kind == "benefic" else 1
    if akey == "conj":
        return {"benefic": 2, "mid": 1, "malefic": -2}[kind]
    return -2 if kind == "malefic" else -1


def west_reading(sign, lons):
    """Structured reading for one sun sign from the seven longitudes:
    moon aspect, the strongest other transit, and a verdict tallied openly."""
    psigns = [int(lon // 30) % 12 for lon in lons]
    moon_sep = (sign - psigns[1]) % 12
    moon_a = ASPECT_OF.get(moon_sep)
    best, best_rank = None, -1
    score = 0
    for pi in range(len(lons)):
        if pi == 1:
            continue
        sep = (sign - psigns[pi]) % 12
        akey = ASPECT_OF.get(sep)
        if not akey:
            continue
        score += aspect_score(pi, akey)
        rank = PLANET_WEIGHT[pi] * 10 + ASPECTS[akey]["sharp"]
        if rank > best_rank:
            best_rank, best = rank, (pi, akey)
    if moon_a:
        score += aspect_score(1, moon_a)
    v = "ดี" if score >= 2 else ("ระวัง" if score <= -2 else "กลาง")
    return {"moon_sign": psigns[1], "moon_aspect": moon_a,
            "top": best, "verdict": v}


# ----------------------------------------------- astronomy (Meeus + Schlyter)
def sun_longitude(jd):
    """Apparent solar longitude, Meeus ch. 25 low precision — the same series
    ../taoist-oracle uses, asserted against it below when the repo is here."""
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    mr = m * RAD
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
         + (0.019993 - 0.000101 * t) * math.sin(2 * mr)
         + 0.000289 * math.sin(3 * mr))
    omega = 125.04 - 1934.136 * t
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega * RAD)) % 360.0


def _kepler(m, e):
    m = m % 360.0
    ev = m + (180.0 / math.pi) * e * math.sin(m * RAD) * (1 + e * math.cos(m * RAD))
    for _ in range(8):
        ev = ev - (ev - (180.0 / math.pi) * e * math.sin(ev * RAD) - m) \
             / (1 - e * math.cos(ev * RAD))
    return ev


# Schlyter's mean elements: N, i, w, a, e, M — constant + rate per day from
# the 2000-01-00 epoch. Half-degree class accuracy, which a 30° sign absorbs.
_EL = {
    "mercury": (48.3313, 3.24587e-5, 7.0047, 5.00e-8, 29.1241, 1.01444e-5,
                0.387098, 0.0, 0.205635, 5.59e-10, 168.6562, 4.0923344368),
    "venus": (76.6799, 2.46590e-5, 3.3946, 2.75e-8, 54.8910, 1.38374e-5,
              0.723330, 0.0, 0.006773, -1.302e-9, 48.0052, 1.6021302244),
    "mars": (49.5574, 2.11081e-5, 1.8497, -1.78e-8, 286.5016, 2.92961e-5,
             1.523688, 0.0, 0.093405, 2.516e-9, 18.6021, 0.5240207766),
    "jupiter": (100.4542, 2.76854e-5, 1.3030, -1.557e-7, 273.8777, 1.64505e-5,
                5.20256, 0.0, 0.048498, 4.469e-9, 19.8950, 0.0830853001),
    "saturn": (113.6634, 2.38980e-5, 2.4886, -1.081e-7, 339.3939, 2.97661e-5,
               9.55475, 0.0, 0.055546, -9.499e-9, 316.9670, 0.0334442282),
}


def _helio(name, d):
    n0, nr, i0, ir, w0, wr, a0, ar, e0, er, m0, mr_ = _EL[name]
    n = n0 + nr * d
    i = i0 + ir * d
    w = w0 + wr * d
    a = a0 + ar * d
    e = e0 + er * d
    m = m0 + mr_ * d
    ev = _kepler(m, e)
    xv = a * (math.cos(ev * RAD) - e)
    yv = a * math.sqrt(1 - e * e) * math.sin(ev * RAD)
    v = math.degrees(math.atan2(yv, xv))
    r = math.hypot(xv, yv)
    # Rotate (v+w) through the ascending node onto the ecliptic.
    u = (v + w) * RAD
    xh = r * (math.cos(n * RAD) * math.cos(u)
              - math.sin(n * RAD) * math.sin(u) * math.cos(i * RAD))
    yh = r * (math.sin(n * RAD) * math.cos(u)
              + math.cos(n * RAD) * math.sin(u) * math.cos(i * RAD))
    zh = r * math.sin(u) * math.sin(i * RAD)
    lonecl = math.degrees(math.atan2(yh, xh)) % 360.0
    latecl = math.asin(zh / r)
    # Jupiter and Saturn tug each other visibly; Schlyter's main terms are
    # added to the finished ecliptic longitude.
    if name in ("jupiter", "saturn"):
        mj = (19.8950 + 0.0830853001 * d) * RAD
        ms = (316.9670 + 0.0334442282 * d) * RAD
        if name == "jupiter":
            lonecl += (-0.332 * math.sin(2 * mj - 5 * ms - 67.6 * RAD)
                       - 0.056 * math.sin(2 * mj - 2 * ms + 21 * RAD)
                       + 0.042 * math.sin(3 * mj - 5 * ms + 21 * RAD)
                       - 0.036 * math.sin(mj - 2 * ms)
                       + 0.022 * math.cos(mj - ms)
                       + 0.023 * math.sin(2 * mj - 3 * ms + 52 * RAD)
                       - 0.016 * math.sin(mj - 5 * ms - 69 * RAD))
        else:
            lonecl += (0.812 * math.sin(2 * mj - 5 * ms - 67.6 * RAD)
                       - 0.229 * math.cos(2 * mj - 4 * ms - 2 * RAD)
                       + 0.119 * math.sin(mj - 2 * ms - 3 * RAD)
                       + 0.046 * math.sin(2 * mj - 6 * ms - 69 * RAD)
                       + 0.014 * math.sin(mj - 3 * ms + 32 * RAD))
    return (r * math.cos(lonecl * RAD) * math.cos(latecl),
            r * math.sin(lonecl * RAD) * math.cos(latecl))


def _sun_xy(d):
    w = 282.9404 + 4.70935e-5 * d
    e = 0.016709 - 1.151e-9 * d
    m = 356.0470 + 0.9856002585 * d
    ev = _kepler(m, e)
    xv = math.cos(ev * RAD) - e
    yv = math.sqrt(1 - e * e) * math.sin(ev * RAD)
    v = math.degrees(math.atan2(yv, xv))
    r = math.hypot(xv, yv)
    lon = (v + w) % 360.0
    return r * math.cos(lon * RAD), r * math.sin(lon * RAD)


def planet_longitude(name, jd):
    """Geocentric ecliptic longitude via Schlyter's elements."""
    d = jd - 2451543.5
    xh, yh = _helio(name, d)
    xs, ys = _sun_xy(d)
    return math.degrees(math.atan2(yh + ys, xh + xs)) % 360.0


def longitudes(jd):
    """[Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn] at jd."""
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc)
    return [sun_longitude(jd), moon_longitude(dt.replace(tzinfo=None)),
            planet_longitude("mercury", jd), planet_longitude("venus", jd),
            planet_longitude("mars", jd), planet_longitude("jupiter", jd),
            planet_longitude("saturn", jd)]


def sun_ingress_jd(year, target_deg):
    """Instant the Sun reaches target_deg in the given year, by iteration."""
    approx = greg_to_jd(year, 1, 1) + ((target_deg - 280.0) % 360.0) / 0.98565
    jd = approx
    for _ in range(50):
        diff = (target_deg - sun_longitude(jd) + 180.0) % 360.0 - 180.0
        if abs(diff) < 1e-7:
            break
        jd += diff / 0.98565
    return jd


def sun_sign_index(y, m, d, hour_ict=12.0):
    return int(sun_longitude(greg_to_jd(y, m, d, hour_ict - 7.0)) // 30) % 12


# --------------------------------------------------------------- year tables
def bake_years():
    """ตรุษจีน + 立春 civil dates 1920–2030 from ../taoist-oracle; carried over
    from the previous bake when the sibling repo is not importable."""
    try:
        sys.path.insert(0, ORACLE)
        from core import calendar_cn as cal
    except ImportError:
        if os.path.exists(OUT):
            old = json.load(open(OUT))
            if old.get("years", {}).get("cny"):
                print("⚠  ../taoist-oracle missing — keeping the previous year tables")
                return old["years"]
        raise SystemExit("no ../taoist-oracle and no previous data/horo.json to keep")

    cny, lichun = {}, {}
    for y in range(YEAR_FROM, YEAR_TO + 1):
        ld = cal.lunar_date(y, 2, 1)
        if ld["month"] == 1 and not ld["is_leap"]:
            c = date(y, 2, 1) - timedelta(days=ld["day"] - 1)
        else:
            c = date(y, 2, 2)
            while True:
                ld = cal.lunar_date(c.year, c.month, c.day)
                if ld["month"] == 1 and ld["day"] == 1 and not ld["is_leap"]:
                    break
                c += timedelta(days=1)
                if c > date(y, 3, 5):
                    raise SystemExit(f"no Chinese New Year found for {y}")
        cny[str(y)] = c.isoformat()
        lj = cal.term_jd_for_year(y, 315) + cal.CST
        ly, lm, ld_ = cal.jd_to_gregorian(lj)
        lichun[str(y)] = date(int(ly), int(lm), int(math.floor(ld_))).isoformat()
    return {"cny": cny, "lichun": lichun,
            "from": YEAR_FROM, "to": YEAR_TO}


# -------------------------------------------------------------- self-checks
def self_check(years):
    # The wheel must reproduce every classical กาลกิณี pairing.
    KALAKINI = {0: 5, 1: 0, 2: 1, 3: 2, 4: 6, 5: 7, 6: 3, 7: 4}
    for born, kk in KALAKINI.items():
        got = next(t for t in range(8) if wheel_station(born, t) == 7)
        assert got == kk, f"กาลกิณี of slot {born}: got {got}, ตำรา says {kk}"
    # เถลิงศก lands 16 Apr through 2025–2027, as the published almanacs print.
    for cs, y in ((1387, 2025), (1388, 2026), (1389, 2027)):
        assert thaloengsok_date(cs) == date(y, 4, 16), (cs, thaloengsok_date(cs))
    assert thai_animal_index(cs_for_date(date(2026, 8, 18))) == 6      # มะเมีย
    assert thai_animal_index(cs_for_date(date(2026, 4, 14))) == 5      # ยังมะเส็ง
    # Sexagenary anchor and a couple of published pillars.
    assert day_pillar_index(date(2000, 1, 7)) == 0                     # 甲子
    # ตรุษจีน spot dates every Thai-Chinese family calendar prints.
    for y, iso in ((2024, "2024-02-10"), (2025, "2025-01-29"),
                   (2026, "2026-02-17"), (2000, "2000-02-05"),
                   (1997, "1997-02-07")):
        got = years["cny"].get(str(y))
        assert got == iso, f"CNY {y}: {got} != {iso}"
    # ปีชง arithmetic reproduces the published 2569 list for a มะเมีย year.
    horse = 6
    assert branch_relation(horse, 0) == "chong"
    assert {b for b in range(12)
            if branch_relation(horse, b) in ("chong", "same", "xing", "hai", "po")} \
        == {0, 6, 1, 3}
    # Sun signs at known places: 18 Aug 2026 sits in สิงห์, either side of the
    # March equinox falls either side of เมษ.
    assert sun_sign_index(2026, 8, 18) == 4
    assert sun_sign_index(2026, 3, 21) == 0
    assert sun_sign_index(2026, 3, 19) == 11
    # Venus and Mercury can never wander far from the Sun; a wrong element row
    # or a broken Kepler loop shows up here immediately.
    for probe in (greg_to_jd(2026, 8, 18), greg_to_jd(1990, 1, 1)):
        lons = longitudes(probe)
        for pi, cap in ((2, 32.0), (3, 50.0)):
            sep = abs((lons[pi] - lons[0] + 180.0) % 360.0 - 180.0)
            assert sep < cap, (pi, sep)
    # Jupiter crossed into สิงห์ at the end of June 2026 and stays there
    # through August — a whole-sign anchor the node rotation cannot fake.
    assert int(longitudes(greg_to_jd(2026, 8, 18, 5.0))[5] // 30) == 4, \
        longitudes(greg_to_jd(2026, 8, 18, 5.0))[5]
    # Against the oracle, when it is here: Sun series and day pillars agree.
    try:
        sys.path.insert(0, ORACLE)
        from core import calendar_cn as cal
        from core import ganzhi
        for jd in (greg_to_jd(2026, 8, 18, 5.0), greg_to_jd(1980, 3, 1, 12.0)):
            assert abs(sun_longitude(jd) - cal.solar_longitude(jd)) < 1e-9
        d0 = date(2020, 1, 1)
        for i in range(0, 4000, 37):
            dd = d0 + timedelta(days=i)
            assert day_pillar_index(dd) == ganzhi.day_pillar(dd.year, dd.month, dd.day).index
    except ImportError:
        pass


# --------------------------------------------------------------------- main
def main():
    days = 180
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    years = bake_years()
    self_check(years)

    thai_days = []
    for slot in range(8):
        row = dict(_MF[slot])
        row["abbr"] = DAY_ABBR[slot]
        row["art"] = DAY_ART_KEY.get(slot, "")
        thai_days.append(row)

    tables = {
        "thai": {
            "days": thai_days, "wheel": WHEEL, "stations": STATIONS,
            "zodiac": [{"th": t, "en": e, "emoji": ZODIAC_EMOJI[i]}
                       for i, (t, e) in enumerate(THAI_ZODIAC)],
        },
        "chinese": {
            "branches": [{"zh": BRANCH_ZH[i], "th": BRANCH_TH[i],
                          "en": BRANCH_EN[i], "emoji": ZODIAC_EMOJI[i]}
                         for i in range(12)],
            "stems": STEM_ZH, "stem_element": STEM_ELEMENT,
            "elem_th": ELEM_TH, "elem_en": ELEM_EN,
            "day_rel": DAY_REL, "year_rel": YEAR_REL,
            "wuxing_rel": {k: {"th": v[0], "en": v[1]}
                           for k, v in WUXING_REL.items()},
        },
        "west": {
            "signs": [{"th": s[0], "en": s[1], "element": s[2], "mode": s[3],
                       "glyph": SIGN_GLYPH[i], "ruler": SIGN_RULER[i]}
                      for i, s in enumerate(SIGNS)],
            "planets": PLANETS, "aspects": ASPECTS,
            "element_th": ELEMENT_TH, "element_en": ELEMENT_EN,
        },
        "verdicts": {"ดี": {"en": "good", "cls": "good"},
                     "กลาง": {"en": "middling", "cls": "mid"},
                     "ระวัง": {"en": "take care", "cls": "care"}},
    }

    today = date.today()
    window = {}
    for i in range(days):
        d = today + timedelta(days=i)
        jd_noon_ict = greg_to_jd(d.year, d.month, d.day, 5.0)   # 12:00 ICT
        window[d.isoformat()] = {
            "wd": d.weekday(),
            "dp": day_pillar_index(d),
            "lon": [round(x, 3) for x in longitudes(jd_noon_ict)],
        }

    # This year's twelve solar ingresses, so the page can print the real sign
    # boundaries rather than a date-range folk table.
    ingress = {}
    for yy in (today.year, today.year + 1):
        rows = []
        for k in range(12):
            deg = k * 30
            jd = sun_ingress_jd(yy, deg)
            y2, m2, d2 = jd_to_greg(jd + 7.0 / 24.0)
            frac = ((jd + 7.0 / 24.0) + 0.5) % 1.0
            hh = int(frac * 24)
            mm = int((frac * 24 - hh) * 60)
            rows.append({"sign": k, "date": date(y2, m2, d2).isoformat(),
                         "time_ict": f"{hh:02d}:{mm:02d}"})
        ingress[str(yy)] = rows

    thaloengsok = {str(cs + 638): thaloengsok_date(cs).isoformat()
                   for cs in range(YEAR_FROM - 638, YEAR_TO - 638 + 2)}

    # Today's readings as structured indices, so build.py can render the
    # static page from this file without holding a second copy of the
    # arithmetic. assets/horo.js recomputes live and must agree — the parity
    # test walks both over the whole window.
    t0 = today.isoformat()
    slot = (today.weekday() + 1) % 7            # Sunday-first day slot
    lons0 = window[t0]["lon"]
    dp0 = window[t0]["dp"]
    cny0 = years["cny"].get(str(today.year))
    gy = today.year - 1 if (cny0 and t0 < cny0) else today.year
    yb = (gy - 4) % 12
    cs0 = cs_for_date(today)
    today_block = {
        "date": t0, "slot": slot,
        "thai": {"station": [wheel_station(b, slot) for b in range(8)],
                 "cs": cs0, "animal": thai_animal_index(cs0)},
        "chinese": {"dp": dp0, "year_branch": yb, "gy": gy,
                    "day_rel": [branch_relation(dp0 % 12, b) for b in range(12)],
                    "year_rel": [branch_relation(yb, b) for b in range(12)]},
        "west": {"readings": [west_reading(s, lons0) for s in range(12)]},
    }

    out = {
        "generated": today.isoformat(),
        "from": (today).isoformat(),
        "to": (today + timedelta(days=days - 1)).isoformat(),
        "tables": tables,
        "years": {**years, "thaloengsok": thaloengsok},
        "ingress": ingress,
        "today": today_block,
        "days": window,
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"🐜 horo: {days} day(s), years {years.get('from', YEAR_FROM)}–"
          f"{years.get('to', YEAR_TO)}, ingress {today.year}+{today.year + 1}"
          f" -> {OUT}")


if __name__ == "__main__":
    main()
