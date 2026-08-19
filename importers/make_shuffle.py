#!/usr/bin/env python3
"""Bake the two scripture shuffles: data/shuffle.json.

Two corpora, one cycle.

  KATHA  — the curated kathas in data/curated/kathas.json (short verses every
           Thai knows, each with what it is FOR and WHEN), plus the canon
           those chant chains are built from: the whole Dhammapada (423
           verses) and the three parittas chanted at every Thai house
           blessing — Maṅgala, Ratana and Karaṇīya Mettā Sutta. Pali root
           (Mahāsaṅgīti edition) and Bhante Sujato's English come from
           SuttaCentral's bilara-data, released CC0; Thai-script Pali is
           derived by rule from the romanised text (a transliteration, not a
           translation, so nothing is invented).
  PSALMS — all 150 psalms, 2,461 verses, in windows of two or three verses
           that never cross a psalm boundary. World English Bible, public
           domain (ebible.org), with its poetic line breaks kept.

Everything is snapshot-first from cache/scripture/ — run the fetch once
(see CACHE_NOTE), and this file never touches the network.

THE CYCLE — home-grown, and stated so anyone can check it.

  A shuffle that is plain random feels like a slot machine; a plain counter
  feels like a spreadsheet. This one is woven from the cycles the site already
  keeps, so the same moment gives the same passage to everyone (a shared
  thing, like the day's hexagram), and a tap moves one bead along a rosary:

     seed = strength(day-deity) · 1000  +  day_pillar · 37  +  kham · 7  +  bead
     index = (seed · STRIDE) mod N,   STRIDE = nearest integer to N/φ coprime
                                              with N (the golden-ratio step)

  The golden-ratio stride is the classical way to walk a circle so that every
  step lands as far as possible from all previous ones — so consecutive beads
  are spread across the whole corpus, nothing clumps, and no passage repeats
  before all N have been seen. The 108 beads of a day are a มาลา; on วันพระ
  the katha draw stays on the merit shelf (refuge, mettā, the blessings).

    python3 importers/make_shuffle.py
"""
import hashlib
import json
import math
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "shuffle.json")
CACHE = os.path.join(ROOT, "cache", "scripture")
KATHAS = os.path.join(ROOT, "data", "curated", "kathas.json")

CACHE_NOTE = """cache/scripture is empty. Fetch once (public-domain / CC0 sources):
  WEB Psalms:  https://ebible.org/Scriptures/eng-web_usfm.zip  -> unzip to cache/scripture/web/
  Dhammapada + Khp 5/6/9: SuttaCentral bilara-data (published branch), root pli-ms +
  translation en-sujato, into cache/scripture/bilara/  (see git log for the exact list)."""

PHI = (1 + 5 ** 0.5) / 2


# ------------------------------------------------------------- Thai-script Pali
# Romanised Pali -> Thai script by the standard Thai Pali orthography (the way
# สวดมนต์ books print it): implicit /a/ carried by the consonant, other vowels
# written, พินทุ (ฺ) under a consonant with no vowel, niggahīta -> ัง.
_CONS = [
    ("kh", "ข"), ("gh", "ฆ"), ("ch", "ฉ"), ("jh", "ฌ"), ("ṭh", "ฐ"), ("ḍh", "ฒ"),
    ("th", "ถ"), ("dh", "ธ"), ("ph", "ผ"), ("bh", "ภ"), ("ñ", "ญ"), ("ṅ", "ง"),
    ("ṇ", "ณ"), ("ṭ", "ฏ"), ("ḍ", "ฑ"), ("ḷ", "ฬ"),
    ("k", "ก"), ("g", "ค"), ("c", "จ"), ("j", "ช"), ("t", "ต"), ("d", "ท"),
    ("n", "น"), ("p", "ป"), ("b", "พ"), ("m", "ม"), ("y", "ย"), ("r", "ร"),
    ("l", "ล"), ("v", "ว"), ("s", "ส"), ("h", "ห"),
]
_VOW = {"a": "", "ā": "า", "i": "ิ", "ī": "ี", "u": "ุ", "ū": "ู", "e": "เ", "o": "โ"}
_VOW_INIT = {"a": "อ", "ā": "อา", "i": "อิ", "ī": "อี", "u": "อุ", "ū": "อู", "e": "เอ", "o": "โอ"}


def pali_to_thai(s):
    """Romanised Pali -> Thai script. Good enough to read aloud; the Thai
    chant-book convention is followed, and the romanised line stays beside
    it so a reader can always check."""
    s = s.replace("ṁ", "ṃ").lower()
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        # consonant (longest match)
        matched = None
        for rom, th in _CONS:
            if s.startswith(rom, i):
                matched = (rom, th)
                break
        if matched:
            rom, th = matched
            i += len(rom)
            # the vowel that follows, or virāma
            v = s[i] if i < n else ""
            if v == "ṃ":
                out.append(th + "ัง")
                i += 1
            elif v in _VOW:
                pre = "เ" if v == "e" else ("โ" if v == "o" else "")
                post = "" if v in ("e", "o") else _VOW[v]
                # niggahīta after an explicit vowel, e.g. "saṃ" handled above; "āṃ"
                out.append(pre + th + post)
                i += 1
                if i < n and s[i] == "ṃ":
                    out.append("ํ")
                    i += 1
            else:
                out.append(th + "ฺ")     # consonant with no vowel: พินทุ
            continue
        if ch in _VOW_INIT:
            out.append(_VOW_INIT[ch])
            i += 1
            if i < n and s[i] == "ṃ":
                out.append("ํ")
                i += 1
            continue
        if ch == "ṃ":
            out.append("ํ")
            i += 1
            continue
        out.append(ch)
        i += 1
    # a final พินทุ on a word's last consonant before space/punct is correct
    # Pali orthography (e.g. "dhammaṁ" -> ธมฺมํ), leave as is.
    return "".join(out)


# ------------------------------------------------------------------- corpora
def load_json(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def read_dhp():
    """423 verses: (ref, pali lines, english lines, chapter title)."""
    bdir = os.path.join(CACHE, "bilara")
    files = sorted(f for f in os.listdir(bdir) if f.startswith("dhp") and f.endswith("_root-pli-ms.json"))
    verses = {}
    chapters = {}
    for f in files:
        root = load_json(os.path.join(bdir, f))
        tr = load_json(os.path.join(bdir, f.replace("_root-pli-ms.json", "_translation-en-sujato.json")))
        for key, txt in root.items():
            m = re.match(r"dhp(\d+):(\d+)(?:\.(\d+))?$", key)
            if not m:
                continue
            v = int(m.group(1))
            seg = m.group(2)
            if seg == "0":
                # headings: 0.3 is the vagga name
                if m.group(3) == "3":
                    chapters[v] = txt.strip()
                continue
            verses.setdefault(v, {"pli": [], "en": []})
            verses[v]["pli"].append(txt.strip())
            verses[v]["en"].append((tr.get(key) or "").strip())
    # chapter name carried forward to verses without their own heading
    cur = ""
    out = []
    for v in sorted(verses):
        if v in chapters:
            cur = chapters[v]
        pli = [x for x in verses[v]["pli"] if x]
        en = [x for x in verses[v]["en"] if x]
        out.append({"id": f"dhp{v}", "ref": f"Dhp {v}", "vagga": cur,
                    "pli": pli, "th": [pali_to_thai(x) for x in pli], "en": en})
    return out


KHP = {5: ("Maṅgala Sutta", "มงคลสูตร", "the thirty-eight blessings"),
       6: ("Ratana Sutta", "รตนสูตร", "the Jewel discourse"),
       9: ("Karaṇīya Mettā Sutta", "กรณียเมตตสูตร", "loving-kindness")}


def read_kp():
    """The three parittas, one passage per stanza."""
    bdir = os.path.join(CACHE, "bilara")
    out = []
    for k, (en_t, th_t, about) in KHP.items():
        root = load_json(os.path.join(bdir, f"kp{k}_root-pli-ms.json"))
        tr = load_json(os.path.join(bdir, f"kp{k}_translation-en-sujato.json"))
        # segments "kp5:3.1" .. group by the integer part = stanza
        stanzas = {}
        for key, txt in root.items():
            m = re.match(rf"kp{k}:(\d+)\.(\d+)$", key)
            if not m:
                continue
            st = int(m.group(1))
            if st == 0:
                continue
            stanzas.setdefault(st, {"pli": [], "en": []})
            stanzas[st]["pli"].append(txt.strip())
            stanzas[st]["en"].append((tr.get(key) or "").strip())
        for st in sorted(stanzas):
            pli = [x for x in stanzas[st]["pli"] if x]
            en = [x for x in stanzas[st]["en"] if x]
            if not pli:
                continue
            out.append({"id": f"kp{k}-{st}", "ref": f"{en_t} {st}", "vagga": f"{th_t} · {en_t}",
                        "pli": pli, "th": [pali_to_thai(x) for x in pli], "en": en,
                        "merit": True})
    return out


def read_curated():
    d = load_json(KATHAS)
    out = []
    for k in d["kathas"]:
        out.append({"id": "k-" + k["id"], "ref": k.get("for_th", ""), "vagga": "คาถา",
                    "th": [k["th"]], "pli": [k.get("rom", "")],
                    "en": [k.get("gloss_en", "")], "gloss_th": k.get("gloss_th", ""),
                    "when_th": k.get("when_th", ""), "when_en": k.get("when_en", ""),
                    "for_th": k.get("for_th", ""), "for_en": k.get("for_en", ""),
                    "curated": True, "merit": True})
    return out


USFM_STRIP = [
    (re.compile(r"\\f \+.*?\\f\*", re.S), ""),          # footnotes
    (re.compile(r"\\w ([^|\\]*)\|[^\\]*\\w\*"), r"\1"),   # strong's wrappers
    (re.compile(r"\\w ([^\\]*)\\w\*"), r"\1"),
    (re.compile(r"\\x .*?\\x\*", re.S), ""),              # cross refs
    (re.compile(r"\\(?:wj|nd|add|qs|sc|it|bd|em)\*?\s?"), ""),
    (re.compile(r"\\[a-z]+\d?\*?"), ""),                  # any other marker
]


def clean_usfm(s):
    for rx, rep in USFM_STRIP:
        s = rx.sub(rep, s)
    return re.sub(r"[ \t]+", " ", s).strip()


def read_psalms():
    """All 2,461 verses with their poetic line breaks, then windows of two or
    three verses that never cross a psalm."""
    path = os.path.join(CACHE, "web", "20-PSAeng-web.usfm")
    raw = open(path, encoding="utf-8").read()
    chap = 0
    verses = []          # (psalm, verse, [lines])
    cur = None
    for line in raw.splitlines():
        line = line.rstrip()
        if line.startswith("\\c "):
            chap = int(line.split()[1])
            cur = None
            continue
        m = re.match(r"\\v (\d+)\s*(.*)$", line)
        if m:
            cur = [chap, int(m.group(1)), []]
            verses.append(cur)
            txt = clean_usfm(m.group(2))
            if txt:
                cur[2].append(txt)
            continue
        if cur is not None and re.match(r"\\q\d?\s", line + " "):
            txt = clean_usfm(line)
            if txt:
                cur[2].append(txt)
    assert len(verses) == 2461, len(verses)
    # windows: walk each psalm, cut into runs of 3,2,3,2… using a pattern that
    # leaves no orphan single verse where it can be helped.
    by_ps = {}
    for p, v, ls in verses:
        by_ps.setdefault(p, []).append((v, ls))
    windows = []
    for p in sorted(by_ps):
        vs = by_ps[p]
        n = len(vs)
        sizes = []
        rem = n
        alt = 3
        while rem > 0:
            if rem in (1, 2, 3):
                sizes.append(rem)
                rem = 0
            elif rem == 4:
                sizes += [2, 2]
                rem = 0
            else:
                sizes.append(alt)
                rem -= alt
                alt = 2 if alt == 3 else 3
        i = 0
        for sz in sizes:
            chunk = vs[i:i + sz]
            i += sz
            windows.append({"id": f"ps{p}:{chunk[0][0]}-{chunk[-1][0]}" if sz > 1 else f"ps{p}:{chunk[0][0]}",
                            "ref": f"Psalm {p}:{chunk[0][0]}" + (f"–{chunk[-1][0]}" if sz > 1 else ""),
                            "ref_th": f"สดุดี {p}:{chunk[0][0]}" + (f"–{chunk[-1][0]}" if sz > 1 else ""),
                            "psalm": p,
                            "verses": [{"v": v, "lines": ls} for v, ls in chunk]})
    return windows


# -------------------------------------------------------------------- cycle
STRENGTH = [6, 15, 8, 17, 19, 21, 10, 12]        # Sun-first slots; 7 = Wed night
SYNODIC, EPOCH = 29.530588853, 2451550.09766     # shared with make_sky / coucal


def greg_to_jd(y, m, d, hour=0.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + d + b - 1524.5 + hour / 24.0)


_DAY_ANCHOR = greg_to_jd(2000, 1, 7) - 8.0 / 24.0


def day_pillar(y, m, d):
    return round(greg_to_jd(y, m, d) - 8.0 / 24.0 - _DAY_ANCHOR) % 60


def kham(y, m, d):
    """ค่ำ day 1..15 at 12:00 ICT from mean Moon age, and whether it is a
    วันพระ (ขึ้น/แรม 8 and 15 — the short-month 14 cannot be told apart by a
    mean-age count, so 15 stands for both)."""
    age = (greg_to_jd(y, m, d, 5.0) - EPOCH) % SYNODIC
    day = int(math.floor(age)) + 1
    waning = day > 15
    k = min(day - 15 if waning else day, 15)
    return {"day": k, "waning": waning, "wan_phra": k in (8, 15)}


_SKY = None


def sky_kham(d):
    """The anchored Thai lunar day from data/sky.json when the date is inside
    its baked window — that table is the site's calendar of record for
    วันพระ. None outside it, and kham() carries on from the mean Moon."""
    global _SKY
    if _SKY is None:
        p = os.path.join(ROOT, "data", "sky.json")
        _SKY = json.load(open(p)).get("days", {}) if os.path.exists(p) else {}
    m = (_SKY.get(d.isoformat()) or {}).get("moon")
    if not m or "thai_day" not in m:
        return None
    return {"day": int(m["thai_day"]), "waning": not m.get("waxing", True),
            "wan_phra": bool(m.get("wan_phra"))}


def seed_for(d, bead, slot=None):
    """The cycle's seed for a civil date and a bead (1..108). `slot` is the
    Sun-first day slot (7 = Wednesday night); daytime weekday by default."""
    if slot is None:
        slot = (d.weekday() + 1) % 7
    kk = sky_kham(d) or kham(d.year, d.month, d.day)
    return {"seed": STRENGTH[slot] * 1000 + day_pillar(d.year, d.month, d.day) * 37 + kk["day"] * 7 + bead,
            "slot": slot, "kham": kk, "dp": day_pillar(d.year, d.month, d.day)}


def index_for(seed, n, stride):
    return (seed * stride) % n


def pick(cycle, corpus, d, bead, merit_only=False):
    c = cycle[corpus]
    s = seed_for(d, bead)
    idx = index_for(s["seed"], c["n"], c["stride"])
    if merit_only and c.get("merit_shelf"):
        shelf = c["merit_shelf"]
        idx = shelf[index_for(s["seed"], len(shelf), golden_stride(len(shelf)))]
    return idx, s


def golden_stride(n):
    """Nearest integer to n/φ that is coprime with n — the step that walks a
    ring of n seats as evenly as a ring can be walked."""
    s = max(1, round(n / PHI))
    d = 0
    while True:
        for cand in (s + d, s - d):
            if 1 <= cand < n and math.gcd(cand, n) == 1:
                return cand
        d += 1


def main():
    if not os.path.isdir(os.path.join(CACHE, "bilara")) or not os.path.exists(
            os.path.join(CACHE, "web", "20-PSAeng-web.usfm")):
        raise SystemExit(CACHE_NOTE)

    curated = read_curated()
    kp = read_kp()
    dhp = read_dhp()
    katha = curated + kp + dhp
    psalms = read_psalms()

    # a stable order, then the stride over it
    nk, np_ = len(katha), len(psalms)
    merit_idx = [i for i, k in enumerate(katha) if k.get("merit")]

    def sha(obj):
        return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

    out = {
        "generated": date.today().isoformat(),
        "cycle": {
            "rule": "seed = strength*1000 + day_pillar*37 + kham*7 + bead; index = (seed*stride) mod n",
            "katha": {"n": nk, "stride": golden_stride(nk), "merit_shelf": merit_idx},
            "psalms": {"n": np_, "stride": golden_stride(np_)},
            "beads": 108,
        },
        "licence": {
            "katha_canon": "Pali root: Mahāsaṅgīti Tipiṭaka; English: Bhante Sujato — both via SuttaCentral bilara-data, CC0 1.0. Thai script derived by rule from the romanised Pali.",
            "katha_curated": "data/curated/kathas.json — verses published everywhere in Thailand, set down as tradition.",
            "psalms": "World English Bible (WEB), public domain — ebible.org.",
        },
        "counts": {"curated": len(curated), "paritta": len(kp), "dhammapada": len(dhp),
                   "katha_total": nk, "psalm_windows": np_, "psalm_verses": 2461},
        "katha": katha,
        "psalms": psalms,
        "sha": {"katha": sha(katha), "psalms": sha(psalms)},
    }
    # Three files, not one: the homepage fetches the small cycle file and
    # whichever corpus a tile needs; a 700 KB blob on every front-page load
    # would be the one heavy thing on a site that is otherwise light.
    katha_out = os.path.join(ROOT, "data", "katha.json")
    psalms_out = os.path.join(ROOT, "data", "psalms.json")
    with open(katha_out, "w", encoding="utf-8") as fh:
        json.dump({"generated": out["generated"], "licence": out["licence"]["katha_canon"],
                   "curated_licence": out["licence"]["katha_curated"],
                   "n": nk, "items": katha}, fh, ensure_ascii=False, separators=(",", ":"))
    with open(psalms_out, "w", encoding="utf-8") as fh:
        json.dump({"generated": out["generated"], "licence": out["licence"]["psalms"],
                   "n": np_, "items": psalms}, fh, ensure_ascii=False, separators=(",", ":"))
    today = date.today()
    s1 = seed_for(today, 1)
    ki, _ = pick(out["cycle"], "katha", today, 1, merit_only=s1["kham"]["wan_phra"])
    pi, _ = pick(out["cycle"], "psalms", today, 1)
    out["today"] = {"date": today.isoformat(), "seed": s1["seed"], "kham": s1["kham"],
                    "katha_idx": ki, "psalm_idx": pi}
    out.pop("katha")
    out.pop("psalms")
    out["files"] = {"katha": "data/katha.json", "psalms": "data/psalms.json"}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    kb = (os.path.getsize(katha_out) + os.path.getsize(psalms_out)) // 1024
    print(f"🐜 shuffle: {len(curated)} kathas + {len(kp)} paritta stanzas + {len(dhp)} Dhammapada "
          f"= {nk} (stride {golden_stride(nk)}); {np_} psalm windows over 2461 verses "
          f"(stride {golden_stride(np_)}) -> {OUT} ({kb} KB)")


if __name__ == "__main__":
    main()
