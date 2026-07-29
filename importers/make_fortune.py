#!/usr/bin/env python3
"""Bake the daily fortune widgets: Thai, Chinese and European, plus a hexagram.

Everything here is *derived*, never improvised. Each tradition has a documented
correspondence table and this file applies it to a date — so two people opening
the page on the same day in Chiang Mai see the same reading, which is what
makes it a shared thing rather than a slot machine.

  Thai      — สีประจำวัน (day colours), พระประจำวันเกิด (the day's Buddha image)
              and กำลังพระเคราะห์, the classical planetary strengths
              (Sun 6, Moon 15, Mars 8, Mercury 17, Jupiter 19, Venus 21,
              Saturn 10, Rahu 12). These are standard Thai almanac material.
  Chinese   — the sexagenary day pillar from ../taoist-oracle's core.ganzhi,
              giving stem, branch, animal and the five-element relation.
  European  — the Moon's zodiac sign for the day, and each sun sign's classical
              aspect to it. Transit-of-the-Moon is the ordinary basis of a
              daily column; the aspect is geometry, not opinion.
  Hexagram  — 梅花易數 time-method (meihua.from_time), which builds the day's
              hexagram from the date itself. Deterministic by design.

Bake a month ahead into data/fortune.json so the tile is right every day
without a rebuild, and so mot-dang's build never imports across repositories.

    python3 importers/make_fortune.py            # 30 days
    python3 importers/make_fortune.py --days 60

If ../taoist-oracle is missing, the Chinese and hexagram sections are skipped
and the rest still writes.
"""
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "fortune.json")
ORACLE = os.path.abspath(os.path.join(ROOT, "..", "taoist-oracle"))

# ---------------------------------------------------------------- Thai
# Monday-indexed to match datetime.weekday().
THAI_DAYS = [
    {"th": "วันจันทร์", "en": "Monday", "colour_th": "สีเหลืองนวล", "colour_en": "cream yellow",
     "hex": "#F2D95C", "planet_th": "พระจันทร์", "planet_en": "the Moon", "strength": 15,
     "buddha_th": "ปางห้ามญาติ", "buddha_en": "the Buddha calming his kinsmen"},
    {"th": "วันอังคาร", "en": "Tuesday", "colour_th": "สีชมพู", "colour_en": "pink",
     "hex": "#EC6A9C", "planet_th": "พระอังคาร", "planet_en": "Mars", "strength": 8,
     "buddha_th": "ปางไสยาสน์", "buddha_en": "the reclining Buddha"},
    {"th": "วันพุธ", "en": "Wednesday", "colour_th": "สีเขียว", "colour_en": "green",
     "hex": "#4FA96B", "planet_th": "พระพุธ", "planet_en": "Mercury", "strength": 17,
     "buddha_th": "ปางอุ้มบาตร", "buddha_en": "the Buddha holding an alms bowl"},
    {"th": "วันพฤหัสบดี", "en": "Thursday", "colour_th": "สีส้ม", "colour_en": "orange",
     "hex": "#EE8B3C", "planet_th": "พระพฤหัสบดี", "planet_en": "Jupiter", "strength": 19,
     "buddha_th": "ปางสมาธิ", "buddha_en": "the Buddha in meditation"},
    {"th": "วันศุกร์", "en": "Friday", "colour_th": "สีฟ้า", "colour_en": "light blue",
     "hex": "#5BB6E0", "planet_th": "พระศุกร์", "planet_en": "Venus", "strength": 21,
     "buddha_th": "ปางรำพึง", "buddha_en": "the Buddha in contemplation"},
    {"th": "วันเสาร์", "en": "Saturday", "colour_th": "สีม่วง", "colour_en": "purple",
     "hex": "#8C63C4", "planet_th": "พระเสาร์", "planet_en": "Saturn", "strength": 10,
     "buddha_th": "ปางนาคปรก", "buddha_en": "the Buddha sheltered by the naga"},
    {"th": "วันอาทิตย์", "en": "Sunday", "colour_th": "สีแดง", "colour_en": "red",
     "hex": "#DC3D3D", "planet_th": "พระอาทิตย์", "planet_en": "the Sun", "strength": 6,
     "buddha_th": "ปางถวายเนตร", "buddha_en": "the Buddha gazing in gratitude"},
]

THAI_ZODIAC = [
    ("ชวด", "Rat"), ("ฉลู", "Ox"), ("ขาล", "Tiger"), ("เถาะ", "Rabbit"),
    ("มะโรง", "Dragon"), ("มะเส็ง", "Snake"), ("มะเมีย", "Horse"), ("มะแม", "Goat"),
    ("วอก", "Monkey"), ("ระกา", "Rooster"), ("จอ", "Dog"), ("กุน", "Pig"),
]

# ------------------------------------------------------------ European
SIGNS = [
    ("ราศีเมษ", "Aries", "fire", "cardinal"), ("ราศีพฤษภ", "Taurus", "earth", "fixed"),
    ("ราศีเมถุน", "Gemini", "air", "mutable"), ("ราศีกรกฎ", "Cancer", "water", "cardinal"),
    ("ราศีสิงห์", "Leo", "fire", "fixed"), ("ราศีกันย์", "Virgo", "earth", "mutable"),
    ("ราศีตุลย์", "Libra", "air", "cardinal"), ("ราศีพิจิก", "Scorpio", "water", "fixed"),
    ("ราศีธนู", "Sagittarius", "fire", "mutable"), ("ราศีมังกร", "Capricorn", "earth", "cardinal"),
    ("ราศีกุมภ์", "Aquarius", "air", "fixed"), ("ราศีมีน", "Pisces", "water", "mutable"),
]
ASPECTS = {
    0: ("ดวงจันทร์ทับราศี", "the Moon is in your own sign", "รู้สึกไวเป็นพิเศษ เชื่อสัญชาตญาณได้",
        "Feelings run close to the surface; instinct is worth trusting."),
    4: ("ตรีโกณ", "trine", "ราบรื่น เหมาะเริ่มสิ่งที่ค้างไว้",
        "Things move without friction — a good day to restart what stalled."),
    8: ("ตรีโกณ", "trine", "ราบรื่น เหมาะเริ่มสิ่งที่ค้างไว้",
        "Things move without friction — a good day to restart what stalled."),
    3: ("จตุโกณ", "square", "มีแรงเสียดทาน แต่เป็นแรงที่ผลักให้ขยับ",
        "Some friction, but the kind that gets you moving."),
    9: ("จตุโกณ", "square", "มีแรงเสียดทาน แต่เป็นแรงที่ผลักให้ขยับ",
        "Some friction, but the kind that gets you moving."),
    6: ("เล็งกัน", "opposition", "มองจากอีกฝั่ง คนอื่นสะท้อนเรากลับมา",
        "The view from the other side; other people mirror you today."),
    2: ("โยคเกณฑ์", "sextile", "โอกาสเล็กๆ ที่ต้องยื่นมือไปรับ",
        "A small opening — it needs you to reach for it."),
    10: ("โยคเกณฑ์", "sextile", "โอกาสเล็กๆ ที่ต้องยื่นมือไปรับ",
        "A small opening — it needs you to reach for it."),
}
ASPECT_QUIET = ("ห่างกัน", "no close aspect", "วันสงบ เหมาะทำงานที่ต้องใช้สมาธิ",
                "A quiet day — good for work that needs concentration.")


def moon_longitude(dt):
    """Low-precision lunar ecliptic longitude, good to about a degree.

    Meeus's abridged terms. A degree is far finer than the 30° a zodiac sign
    spans, so this is ample for naming the sign the Moon sits in.
    """
    jd = 2440587.5 + dt.replace(tzinfo=timezone.utc).timestamp() / 86400.0
    t = (jd - 2451545.0) / 36525.0
    lp = 218.316 + 481267.8813 * t                      # mean longitude
    m = 134.963 + 477198.8676 * t                       # mean anomaly
    f = 93.272 + 483202.0175 * t                        # argument of latitude
    d = 297.850 + 445267.1115 * t                       # mean elongation
    ms = 357.529 + 35999.0503 * t                       # sun's mean anomaly
    r = math.radians
    lon = (lp + 6.289 * math.sin(r(m)) - 1.274 * math.sin(r(m - 2 * d))
           + 0.658 * math.sin(r(2 * d)) - 0.186 * math.sin(r(ms))
           - 0.059 * math.sin(r(2 * m - 2 * d)) - 0.057 * math.sin(r(m - 2 * d + ms))
           + 0.053 * math.sin(r(m + 2 * d)) + 0.046 * math.sin(r(2 * d - ms))
           + 0.041 * math.sin(r(m - ms)) - 0.035 * math.sin(r(d))
           - 0.031 * math.sin(r(m + ms)) + 0.015 * math.sin(r(2 * f - 2 * d)))
    return lon % 360.0


def lucky_numbers(d, strength):
    """Traditional-style เลขเด็ด, derived openly from the date.

    Thai almanac numerology works from the day's planetary strength and the
    figures of the date itself, so that is exactly what this does — no hidden
    randomness. Anyone can check the arithmetic, which is the point: these are
    a custom to enjoy, not a prediction to bet the rent on.
    """
    be = d.year + 543
    digits = f"{d.day:02d}{d.month:02d}{be % 100:02d}"
    two = (strength * d.day + d.month) % 100
    two_b = (int(digits[:2]) + int(digits[2:4]) + strength) % 100
    three = (strength * 100 + d.day * d.month + be) % 1000
    return {"two": [f"{two:02d}", f"{two_b:02d}"], "three": f"{three:03d}",
            "how_th": f"จากกำลังพระเคราะห์ {strength} กับวันที่ {d.day}/{d.month}/{be}",
            "how_en": f"from the day's planetary strength ({strength}) and the date {d.day}/{d.month}/{be}"}


WUXING_REL = {
    "same": ("ธาตุเดียวกัน เสมอกัน", "same element — evenly matched"),
    "i_generate": ("เราส่งเสริมเขา ให้ออกไป", "you nourish it — a day of giving out"),
    "generates_me": ("เขาส่งเสริมเรา มีคนหนุน", "it nourishes you — support arrives"),
    "i_overcome": ("เราชนะเขา คุมสถานการณ์ได้", "you overcome it — the day yields to you"),
    "overcomes_me": ("เขาชนะเรา ควรถ่อมและระวัง", "it overcomes you — go gently and watch your step"),
}


def thai_zodiac_year(d):
    """The Thai animal year turns at Songkran, not on 1 January.

    Counting straight from the Gregorian year makes January to mid-April wrong
    by one animal — the kind of quiet off-by-one that makes an almanac useless.
    """
    y = d.year if (d.month, d.day) >= (4, 13) else d.year - 1
    return THAI_ZODIAC[(y - 4) % 12]


def build_day(d, oracle_ok):
    wd = d.weekday()
    td = THAI_DAYS[wd]
    zth, zen = thai_zodiac_year(d)
    entry = {
        "date": d.isoformat(),
        "thai": {**td, "zodiac_year_th": zth, "zodiac_year_en": zen,
                 "lucky": lucky_numbers(d, td["strength"])},
    }
    # European: the Moon's sign, then every sun sign's aspect to it.
    lon = moon_longitude(datetime(d.year, d.month, d.day, 12))
    mi = int(lon // 30) % 12
    signs = []
    for i, (sth, sen, elem, mode) in enumerate(SIGNS):
        sep = (i - mi) % 12
        a = ASPECTS.get(sep, ASPECT_QUIET)
        signs.append({"th": sth, "en": sen, "element": elem, "mode": mode,
                      "aspect_th": a[0], "aspect_en": a[1],
                      "line_th": a[2], "line_en": a[3]})
    entry["european"] = {"moon_sign_th": SIGNS[mi][0], "moon_sign_en": SIGNS[mi][1],
                         "moon_lon": round(lon, 2), "signs": signs}
    if oracle_ok:
        from core import ganzhi, wuxing
        from methods import meihua
        # Pillar exposes name/animal as METHODS, not properties — call them, or
        # a bound method ends up in the JSON and the dump fails.
        p = ganzhi.day_pillar(d.year, d.month, d.day)
        entry["chinese"] = {
            "pillar": p.name(),
            "animal": p.animal(),
            "stem_element_en": wuxing.name(p.element, "en"),
            "stem_element_zh": wuxing.name(p.element, "zh"),
            "branch_element_en": wuxing.name(p.branch_element, "en"),
            "relation": str(wuxing.relation(p.element, p.branch_element)),
            "relation_th": WUXING_REL.get(str(wuxing.relation(p.element, p.branch_element)), ("", ""))[0],
            "relation_en": WUXING_REL.get(str(wuxing.relation(p.element, p.branch_element)), ("", ""))[1],
        }
        r = meihua.from_time(d.year, d.month, d.day, 12)
        prim, chg = r["primary"], r.get("changed")
        entry["hexagram"] = {
            "number": prim.number, "zh": prim.hanzi, "pinyin": prim.pinyin,
            "bits": list(prim.bits),
            "en": prim.english, "gloss": prim.gloss,
            "changed_number": getattr(chg, "number", None),
            "changed_en": getattr(chg, "english", None),
            "verdict": r.get("verdict", ""),
            "moving": r.get("moving", []),
            "lunar": r.get("lunar", {}),
        }
    return entry


def main():
    days = 30
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    oracle_ok = os.path.isdir(ORACLE)
    if oracle_ok and ORACLE not in sys.path:
        sys.path.insert(0, ORACLE)
    try:
        if oracle_ok:
            import core.ganzhi  # noqa: F401
    except ImportError:
        oracle_ok = False

    today = date.today()
    out = {}
    for i in range(days):
        d = today + timedelta(days=i)
        out[d.isoformat()] = build_day(d, oracle_ok)

    with open(OUT, "w") as fh:
        json.dump({"generated": today.isoformat(),
                   "has_chinese": oracle_ok, "days": out}, fh,
                  ensure_ascii=False, indent=1)
    print(f"🐜 fortune for {len(out)} day(s)"
          f"{' incl. Chinese + hexagram' if oracle_ok else ' (Thai + European only)'} -> {OUT}")
    if not oracle_ok:
        print("⚠  ../taoist-oracle not importable — Chinese and hexagram skipped")


if __name__ == "__main__":
    main()
