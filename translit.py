"""RTGS — the Royal Thai General System of Transcription, in this repo.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
This produces a *reading*: how a Thai name sounds, written in Latin letters by
the published rules of the Royal Society of Thailand (ราชบัณฑิตยสภา, RTGS 1999).
It is not a name and must never be stored as one.

/what.html tells readers the site keeps the Thai name as the real record, and
`nameEn` is a sourced field holding what a place calls itself. Both still hold,
because a reading is a different object from a name. CLAUDE.md used to go
further and forbid machine transliteration outright, on the grounds that an
absent English name is a smaller error than an invented one — which was a real
sourcing rule with a false dichotomy stapled to it. A labelled reading beside
the Thai is neither absent nor invented, and while nobody had priced it, 24,023
listing rows rendered as a clickable blank in English-only mode.

Two places where writing a reading has a cost worth knowing:

  * `nameEn` and `data/canonical/` hold sourced facts. A reading is computed,
    so writing it there loses the distinction between what a shop calls itself
    and what a program worked out — which is the whole basis of the per-field
    provenance the site publishes.
  * `place_slug()` reads `name_of()`, and a slug that moves is a 404 after
    deploy. Changing what `name_of()` returns costs redirects.

Everywhere else is a judgement about what reads well, not a boundary. `.roman`
after the Thai is one good answer for a listing row. A tag chip, a filter label
or a heading may want a different one, and that is a call to make on the page,
not a rule this file gets to make for it.

RTGS is transcription, not transliteration: it follows the SOUND, so it is
lossy on purpose (no tones, no vowel length, ข and ค both `kh`). Two different
Thai names can read the same. That is the standard behaving correctly, and it
is why the reading is an aid beside the name rather than a replacement for it.

HOW IT WORKS
------------
`romanize()` walks a Thai string left to right, matching the longest syllable
pattern it can at each step from RTGS's own vowel table, then spells the
syllable as initial + vowel + final. Word boundaries come from the site's own
corpus dictionary (data/search_segdict.txt) so that syllables join into the
words a reader would say, rather than one hyphen-free run.

`gloss()` goes one step further for the generic head word a Thai place name
almost always opens with — วัด, โรงเรียน, โรงพยาบาล, ร้าน. Those are
dictionary words, not names, and translating them is what makes a roll of
2,136 temples usable by somebody who does not read Thai. The rest of the name
is read, never translated.

No third-party dependency, by choice: PyThaiNLP would pull a model download
into a build that runs offline, and RTGS is a published rule set that fits in
one file.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# The alphabet, as SOUNDS. RTGS transcribes what is said, so every consonant
# has two values: one as the head of a syllable and one at the end of it, where
# Thai allows only eight stops and nasals. ข and ค are both `kh` because they
# differ in tone class, not in sound, and RTGS does not write tone.
# ---------------------------------------------------------------------------
INITIAL = {
    "ก": "k",  "ข": "kh", "ฃ": "kh", "ค": "kh", "ฅ": "kh", "ฆ": "kh",
    "ง": "ng", "จ": "ch", "ฉ": "ch", "ช": "ch", "ซ": "s",  "ฌ": "ch",
    "ญ": "y",  "ฎ": "d",  "ฏ": "t",  "ฐ": "th", "ฑ": "th", "ฒ": "th",
    "ณ": "n",  "ด": "d",  "ต": "t",  "ถ": "th", "ท": "th", "ธ": "th",
    "น": "n",  "บ": "b",  "ป": "p",  "ผ": "ph", "ฝ": "f",  "พ": "ph",
    "ฟ": "f",  "ภ": "ph", "ม": "m",  "ย": "y",  "ร": "r",  "ล": "l",
    "ว": "w",  "ศ": "s",  "ษ": "s",  "ส": "s",  "ห": "h",  "ฬ": "l",
    "อ": "",   "ฮ": "h",
}

FINAL = {
    "ก": "k",  "ข": "k",  "ค": "k",  "ฆ": "k",  "ง": "ng",
    "จ": "t",  "ฉ": "t",  "ช": "t",  "ซ": "t",  "ฌ": "t",
    "ญ": "n",  "ฎ": "t",  "ฏ": "t",  "ฐ": "t",  "ฑ": "t",  "ฒ": "t",
    "ณ": "n",  "ด": "t",  "ต": "t",  "ถ": "t",  "ท": "t",  "ธ": "t",
    "น": "n",  "บ": "p",  "ป": "p",  "ผ": "p",  "ฝ": "p",  "พ": "p",
    "ฟ": "p",  "ภ": "p",  "ม": "m",  "ย": "i",  "ร": "n",  "ล": "n",
    "ว": "o",  "ศ": "t",  "ษ": "t",  "ส": "t",  "ฬ": "n",
}
# อ and ฮ are missing on purpose: Thai closes no syllable with either. While
# they sat here with an empty value they were consumed as silent finals, and
# แม่ฮ่องสอน read "maeangason" — the ฮ eaten by แม่, the name falling apart
# behind it.

CONS = "".join(INITIAL)
TONE = "่้๊๋"          # mai ek/tho/tri/chattawa — RTGS writes no tone
THANTHAKHAT = "์"  # ์  the killer: what it sits on is not said
PHINTHU = "ฺ"      # ฺ  rare, also silences

# True initial clusters. Anything else that looks like two consonants is two
# syllables with an unwritten vowel between them (สบาย = sa-bai), which the
# fallback below handles.
CLUSTERS = (
    "กร", "กล", "กว", "ขร", "ขล", "ขว", "คร", "คล", "คว",
    "ตร", "ปร", "ปล", "ผล", "พร", "พล", "ฟร", "ฟล", "บร", "บล",
    "ดร", "ทร",
)

# The native ones. Thai's own cluster inventory is the first three rows above;
# ดร, บร, บล, ฟร and ฟล only ever appear where a foreign word was written in
# Thai letters, and they behave differently after a leading vowel. See the
# exception in _initial(): ไดร- is not a shape Thai builds, so ได้รับ must be
# read ได้ + รับ and not as a "dr" cluster — it read "Draiba" until 2026-09-08.
NATIVE_CLUSTERS = frozenset((
    "กร", "กล", "กว", "ขร", "ขล", "ขว", "คร", "คล", "คว",
    "ตร", "ปร", "ปล", "ผล", "พร", "พล",
))

# ห and อ as silent leaders: they carry tone class for a following sonorant and
# are not themselves said — หมา is `ma`, not `hma`.
# หฤ is NOT here: ห before ฤ is said — หฤทัย is ha-rue-thai, หฤหรรษ์ ha-rue-han.
# It sat in this tuple until 2026-09-07 and พระหฤทัย read "Phraathai".
HO_NAM = ("หง", "หญ", "หน", "หม", "หย", "หร", "หล", "หว")
O_NAM = ("อย",)

# ทร is /s/ (ทราย = sai), the one cluster that is not the sum of its letters.
SPECIAL_INITIAL = {"ทร": "s", "ศร": "s", "สร": "s"}


def _initial(s, i):
    """The consonant sound that opens a syllable at s[i:], and how far it ran.

    Two orthographic tells do the work here.

    ห as a silent leader vs ห as a real initial: in หมา the mark of tone class
    is ห itself and any tone mark sits over the ม (หม้อ = mo). In ห้วย the tone
    mark sits immediately after the ห, which can only happen when ห IS the
    initial — so ห้วย is huai, not wai. One character of lookahead separates
    them; before this rule ห้วยแก้ว read as "wayakwae".

    A cluster vs two syllables: กร in กรม is a cluster because a consonant
    follows it to be the final (krom); คร at the end of นคร cannot be, so the
    ค is an initial and the ร its final (na-khon).
    """
    two = s[i:i + 2]
    _nx = s[i + 1:i + 2]
    tone_on_first = bool(_nx) and _nx in TONE
    if two in SPECIAL_INITIAL and not tone_on_first:
        return SPECIAL_INITIAL[two], 2
    if two in HO_NAM and not tone_on_first:
        return INITIAL.get(two[1], ""), 2
    if two in O_NAM and not tone_on_first:
        return INITIAL.get(two[1], ""), 2
    if two in CLUSTERS and not tone_on_first and not _wo_is_vowel(s, i) and (
            _cluster_has_rime(s, i + 2)
            # แพร่, โปร, ไตร: the leading vowel written BEFORE the pair belongs
            # to the cluster as a whole, so the pair is a cluster with nothing
            # after it. Read as initial + final instead, น้ำแพร่ was "Namphaen".
            # NATIVE clusters only. The loan pairs — ดร, บร, บล, ฟร, ฟล — are
            # shapes Thai does not build, so a leading vowel in front of one is
            # a coincidence of two words meeting: ได้รับ is ได้ + รับ, and this
            # exception read it "Draiba".
            or (i > 0 and s[i - 1] in LEAD_VOWELS and two in NATIVE_CLUSTERS)):
        return INITIAL.get(two[0], "") + INITIAL.get(two[1], ""), 2
    c = s[i:i + 1]
    if c in INITIAL:
        return INITIAL[c], 1
    return None, 0


def _cluster_has_rime(s, k):
    """True when what follows a would-be cluster can actually finish the
    syllable: a written vowel, or a consonant free to be the final."""
    nxt = s[k:k + 1]
    if not nxt:
        return False
    if nxt in VOWEL_SIGNS or nxt in LEAD_VOWELS:
        return True
    return nxt in FINAL


def _wo_is_vowel(s, i):
    """True when the ว of a would-be กว/ขว/คว cluster is really the vowel.

    `-วย` is the rime /uai/, so the ว belongs to the vowel and not to the
    cluster: ก๋วยเตี๋ยว is kuai tiao, and it read `kwo tiao` until 2026-09-08.
    Every other initial already gets this right because สว, ด้ว and ช่ว are
    not clusters at all — only ก, ข and ค have a ว partner to be confused
    with, which is why the test is this narrow.

    The same confusion with no ย after it is what put แก้ว in the lexicon as
    Kaeo; there the ว is the final /o/. One letter of lookahead separates the
    two, so the rule is written here rather than word by word.
    """
    return s[i:i + 2] in ("กว", "ขว", "คว") and s[i + 2:i + 3] == "ย"


# ---------------------------------------------------------------------------
# The vowel table. Each entry is (pattern, vowel, needs_final).
#
# `pattern` is matched AFTER the initial consonant has been taken, except for
# the four leading vowels เ แ โ ใ ไ, which are written before their consonant
# and so are handled by `lead`. Order matters: the longest shape that can match
# has to be tried first, or เ-ือ would be read as เ- plus a stray ื.
# ---------------------------------------------------------------------------
# (leading char or "", trailing pattern, roman vowel, final-consonant slot)
# F  = a final consonant is consumed from the string
# -  = no final; the pattern is the whole rime
VOWELS = [
    # --- diphthongs written around the consonant, longest first -------------
    ("เ", "ียะ", "ia", "-"),
    ("เ", "ือะ", "uea", "-"),
    ("เ", "ียว", "iao", "-"),
    ("เ", "ือย", "ueai", "-"),
    ("เ", "ีย", "ia", "F"),
    ("เ", "ือ", "uea", "F"),
    ("เ", "าะ", "o", "-"),
    ("เ", "อะ", "oe", "-"),
    ("เ", "ิ", "oe", "F"),
    ("เ", "อ", "oe", "F"),
    ("เ", "ย", "oei", "-"),
    ("เ", "ะ", "e", "-"),
    ("เ", "า", "ao", "-"),
    ("เ", "ว", "eo", "-"),
    ("เ", "็", "e", "F"),
    ("เ", "", "e", "F"),
    ("แ", "ะ", "ae", "-"),
    ("แ", "ว", "aeo", "-"),
    ("แ", "็", "ae", "F"),
    ("แ", "", "ae", "F"),
    ("โ", "ะ", "o", "-"),
    ("โ", "ย", "oi", "-"),
    ("โ", "", "o", "F"),
    ("ใ", "", "ai", "-"),
    ("ไ", "ย", "ai", "-"),
    ("ไ", "", "ai", "-"),
    # --- vowels written after or above the consonant ------------------------
    ("", "ัวะ", "ua", "-"),
    ("", "ัว", "ua", "F"),
    ("", "ำ", "am", "-"),
    ("", "ัย", "ai", "-"),
    ("", "าย", "ai", "-"),
    ("", "าว", "ao", "-"),
    ("", "าะ", "o", "-"),
    ("", "า", "a", "F"),
    ("", "ิว", "io", "-"),
    ("", "ิ", "i", "F"),
    ("", "ี", "i", "F"),
    ("", "ึ", "ue", "F"),
    ("", "ือ", "ue", "F"),
    ("", "ื", "ue", "F"),
    ("", "ุย", "ui", "-"),
    ("", "ุ", "u", "F"),
    ("", "ู", "u", "F"),
    ("", "อย", "oi", "-"),
    ("", "อ", "o", "F"),
    ("", "วย", "uai", "-"),
    ("", "ว", "ua", "f"),
    ("", "ะ", "a", "-"),
    ("", "รร", "a", "R"),      # รร: `an` bare, `a` + the final that follows
    ("", "ั", "a", "F"),
    ("", "็", "o", "F"),
]

# ฤ ฦ: vowel-consonants with three readings. `rue` is the ordinary one; `ri`
# before a few stems (ฤทธิ์ = rit) and `roe` in ฤกษ์. Only the common two are
# worth the rule — the third would be a lookup table of four words.
RU = {"ฤ": "rue", "ฦ": "lue"}
RU_RI = ("ฤทธิ", "ฤษี", "ฤษ")


VOWEL_SIGNS = "\u0e30\u0e31\u0e32\u0e33\u0e34\u0e35\u0e36\u0e37\u0e38\u0e39\u0e47\u0e4d"
LEAD_VOWELS = "\u0e40\u0e41\u0e42\u0e43\u0e44"


def _strip_silent(w):
    """Drop what the killer mark kills, and the tone marks RTGS does not write.

    ์ silences the letter it sits on. Three shapes, all common in names:

      สิงห์    kill the ห            -> sing
      จันทร์   kill the ร AND the ท   -> chan   (a final cluster dies whole)
      พันธุ์   kill the ุ then the ธ   -> phan   (the mark rides a vowel sign)

    The middle case is the one worth naming: when the killed letter is ร ล ว
    or ย it is the tail of a cluster, so the consonant in front of it is silent
    too. ศาสตร์ is `sat`, not `satta`. When it is anything else — ห in สิงห์ —
    only that one letter goes and the ง before it is still the final.

    A word-final ร after a stop is silent for the same reason without needing a
    mark at all: จักร is `chak`, บัตร is `bat`, สมัคร is `samak`.
    """
    # ห้วย vs หมา: a tone mark directly after the ห can only happen when the ห
    # is the initial. ฮ is the same sound and is in no ho-nam pair, so the
    # decision survives the tone marks being dropped on the next line.
    w = re.sub("\u0e2b([" + TONE + "])", lambda m: "\u0e2e" + m.group(1), w)
    out, i = [], 0
    while i < len(w):
        c = w[i]
        if c in TONE or c == PHINTHU:
            i += 1
            continue
        if c == THANTHAKHAT:
            # walk back over any vowel sign, then take the consonant with it
            while out and out[-1] in VOWEL_SIGNS:
                out.pop()
            killed = out.pop() if out else ""
            # the letter in front dies with it only when the two were a
            # cluster — ทร in จันทร์, ตร in ศาสตร์. In มอร์ the อ is the vowel of
            # มอ and stays: "Mo", not "Ma".
            if (killed == "\u0e23" and out
                    and (out[-1] + killed) in CLUSTERS + tuple(SPECIAL_INITIAL)):
                out.pop()
            i += 1
            continue
        out.append(c)
        i += 1
    w = "".join(out)
    # ...ก ร / ...ต ร at the end of a word: the ร is not said — จักร is chak,
    # บัตร is bat. Only where the syllable already carries a written vowel,
    # though: นคร has none, and dropping its ร turned na-khon into "nok".
    if (len(w) > 2 and w[-1] == "\u0e23" and w[-2] in "\u0e01\u0e15\u0e17\u0e04"
            and any(c in VOWEL_SIGNS or c in LEAD_VOWELS for c in w[:-1])):
        w = w[:-1]
    return w


def _syllable(s, i):
    """Read one syllable out of s at i. Returns (roman, next_index) or None."""
    lead = ""
    if s[i] in "เแโใไ":
        lead = s[i]
        j = i + 1
    else:
        j = i
    ini, took = _initial(s, j)
    if ini is None:
        return None
    j += took
    rest = s[j:]

    for vlead, pat, vow, slot in VOWELS:
        if vlead != lead:
            continue
        if pat and not rest.startswith(pat):
            continue
        k = j + len(pat)
        if slot == "-":
            return ini + vow, k
        if slot == "R":                    # รร
            nxt = s[k:k + 1]
            if nxt and nxt in FINAL and not _opens_next(s, k):
                return ini + vow + FINAL[nxt], k + 1
            return ini + "an", k
        # slot == "F": take a final consonant if one is really final here
        nxt = s[k:k + 1]
        if nxt and nxt in FINAL and not _opens_next(s, k):
            f = FINAL[nxt]
            # ย and ว as finals are the tail of a diphthong, not consonants
            if f == "i":
                return ini + vow + "i", k + 1
            if f == "o":
                return ini + vow + "o", k + 1
            return ini + vow + f, k + 1
        if slot == "f":
            continue      # ว is only the vowel `ua` when a final follows it
        if pat == "" and lead == "":
            continue                       # a bare consonant is not a syllable yet
        return ini + vow, k

    # No written vowel. Two ways this happens, and they sound different:
    #   closed  — คน is khon, ลม is lom: one consonant left, so it is the
    #             final and the unwritten vowel is `o`
    #   open    — นคร is na-khon, ขนม is kha-nom: two consonants left, so this
    #             one heads an open syllable with an unwritten `a` and the pair
    #             behind it forms the next syllable
    if lead:
        return None
    a, b = s[j:j + 1], s[j + 1:j + 2]
    if a and a in FINAL:
        # ง almost never heads a syllable inside a word, so where it CAN close
        # one it does: มงคล is mong-khon, not ma-ngo-khon; สงกรานต์ songkran.
        if a == "\u0e07" and not _opens_next(s, j):
            return ini + "ong", j + 1
        if b and b in INITIAL and not _opens_next(s, j + 1):
            return ini + "a", j              # two consonants left: open
        if not _opens_next(s, j):
            f = FINAL[a]
            return ini + ("o" + f if f not in ("i", "o") else "o"), j + 1
    return ini + "a", j


def _opens_next(s, k):
    """True when s[k] is really the head of the NEXT syllable, not a final.

    A consonant carrying its own written vowel is starting something. A
    consonant followed by a LEADING vowel is not — the leading vowel belongs to
    whatever comes after it, so this letter is free to close the syllable
    behind it. Reading เชียงใหม่ the other way produced "chiangamai".
    """
    if k >= len(s):
        return False
    nxt = s[k + 1:k + 2]
    while nxt and nxt in TONE:
        k += 1
        nxt = s[k + 1:k + 2]
    if not nxt:
        return False
    if nxt in VOWEL_SIGNS:
        return True
    if nxt == "\u0e27" and s[k + 2:k + 3] in "\u0e22\u0e23\u0e25\u0e19\u0e21\u0e07\u0e01\u0e14\u0e1a":
        return True                        # -วย / -วน: the ว is this letter's vowel
    # The letter leads a PAIR that heads a syllable of its own: หม in ต้นหมื้อ,
    # ทร in แก้ทรง. Read as a final instead, they gave "Santanamue" (the น
    # left open) and "Kaetrong" (the ท taken as a final, the ทร cluster lost).
    two = s[k:k + 2]
    if two in HO_NAM or two in SPECIAL_INITIAL or two in CLUSTERS:
        after = s[k + 2:k + 3]
        if after and (after in VOWEL_SIGNS or after in FINAL):
            return True
    return False


THAI_RE = re.compile(r"[฀-๿]+")

# The elements a place name is built from, on which a compound is cut and a
# space written: RTGS writes Pratu Tha Phae, Pa Cha, Nong Hoi, Mae Rim. Every
# entry is a generic Thai noun for a kind of place or ground — nothing here is
# itself a name. The lexicon's own keys and the head words join the set at
# load, so a curated word cuts the same way.
TOPONYM_ELEMENTS = (
    "ประตู", "แจ่ง", "ท่า", "ป่า", "หนอง", "ห้วย", "แม่", "ดอย", "สัน", "บ้าน",
    "วัด", "ถนน", "ตลาด", "คลอง", "สะพาน", "ทุ่ง", "โป่ง", "ปาง", "ผา", "เวียง",
    "ขัว", "กาด", "บ่อ", "เกาะ", "ม่อน", "ต้น", "สวน", "ศาล", "พระ", "เจดีย์",
    "น้ำตก", "ถ้ำ", "อ่าง", "ซอย", "ลาน", "อาคาร", "หมู่บ้าน", "ชุมชน", "ที่",
    "หอ", "น้ำ",
)
_ELEMENTS = None

# Words that OPEN with an element and are one word all the same. The cut
# rule cannot tell สันติ (peace, one word) from สันทราย (San Sai, two), so the
# few common ones are named. A place called สันติสุข reads Santisuk.
_ONE_WORD = {"สันติ", "สันติสุข", "สันติภาพ", "สันต์", "ป่าน", "ท่าน", "แม่น",
             "บ่อน", "ที่ดิน", "ที่สุด", "ต้นทุน", "ลานนา", "ล้านนา",
             "น้ำมัน", "น้ำแข็ง", "น้ำตาล", "น้ำหอม", "น้ำใจ"}


def _elements():
    global _ELEMENTS
    if _ELEMENTS is None:
        _ELEMENTS = set(TOPONYM_ELEMENTS) | set(HEADWORDS) | set(_lexicon())
    return _ELEMENTS


def _cuts_clean(tail):
    """True when the dictionary accounts for every character of `tail`."""
    d = _load_dict()
    return all(t in d for t in _segment(tail))


def _rom_word(w, syl_sep=""):
    """One dictionary word, read syllable by syllable — unless the lexicon
    already knows it, in which case the published reading wins over the rules."""
    hit = _lexicon().get(w)
    if hit:
        return hit
    # A compound the dictionary swallowed whole: บ้านสันทราย is one entry, but
    # the reading a person wants is Ban San Sai, not Bansansai; ประตูท่าแพ is
    # one entry and read "Pratuthaphae" until 2026-09-07. If the word opens
    # with an element a Thai place name is built from — a lexicon word, a
    # generic head, a toponym like ประตู/ท่า/ป่า/หนอง — and what is left is a
    # word we know, or cuts cleanly into words we know, read the parts with a
    # space between them, the way RTGS writes a place name.
    #
    # THE PART IN FRONT IS READ, NEVER TRANSLATED. HEADWORDS carry an English
    # gloss for head_split(), which puts it at the head or the tail of the whole
    # name. Inside a name the same table used to leak that gloss into the
    # middle of the reading: วัดถ้ำพระ came out "Wat Cave Phra". A word that is
    # not the head is a word in the name, and it is read.
    lex = _lexicon()
    if w in _ONE_WORD:
        return _rom_word_rules(w, syl_sep)
    for k in sorted((x for x in _elements() if w.startswith(x) and x != w),
                    key=len, reverse=True):
        tail = w[len(k):]
        if not tail or len(tail) < 2:
            continue
        if (tail in lex or tail in _load_dict() or _cuts_clean(tail)
                or tail.startswith(tuple(TOPONYM_ELEMENTS))):
            head = lex.get(k) or _rom_word(k, syl_sep)
            parts = [head] + [_rom_word(t, syl_sep) for t in _segment(tail)]
            return " ".join(x for x in parts if x)
    return _rom_word_rules(w, syl_sep)


def _rom_word_rules(w, syl_sep=""):
    """One word read by the letter rules alone — no lexicon, no cutting."""
    w = _strip_silent(w)
    if not w:
        return ""
    out, i, guard = [], 0, 0
    while i < len(w) and guard < 64:
        guard += 1
        c = w[i]
        if c in RU:
            nxt = w[i:i + 4]
            out.append("ri" if any(nxt.startswith(p) for p in RU_RI) else RU[c])
            i += 1
            continue
        if c == "ๆ":                        # mai yamok: say it again
            if out:
                out.append(out[-1])
            i += 1
            continue
        if not ("ก" <= c <= "๛"):
            out.append(c)
            i += 1
            continue
        syl = _syllable(w, i)
        if syl is None:
            i += 1
            continue
        r, nxt_i = syl
        if nxt_i <= i:
            i += 1
            continue
        out.append(r)
        i = nxt_i
    return syl_sep.join(x for x in out if x)


# ---------------------------------------------------------------------------
# Word boundaries. Longest match against the site's own corpus dictionary, so
# the reading breaks where a reader would break it. Words the corpus has never
# seen still get read — they are just read as one run.
# ---------------------------------------------------------------------------
_LEX = None


def _lexicon():
    """The curated table of words the letter rules cannot reach.

    Two kinds, kept apart because they are different claims. `irregular` is
    Pali/Sanskrit and other readings where RTGS's own published form differs
    from what the letters alone would give — ธาตุ is `That`, not `Thatu`.
    `loanword` is English written in Thai script, where the reading IS the
    English: บิ้วตี้ read letter by letter gives `Bioti`, which helps nobody,
    and the sign in the street says Beauty.

    Both are facts with a source (see the file's own `_source`), not guesses,
    and neither is a NAME — the reading they build is still labelled a reading.
    """
    global _LEX
    if _LEX is not None:
        return _LEX
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "curated", "rtgs_lexicon.json")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        raw = {}
    _LEX = dict(raw.get("irregular") or {})
    _LEX.update(raw.get("loanword") or {})
    _LEX.update(raw.get("place") or {})
    # `brand` is the third kind and the newest (WO-56): a name's own Latin
    # spelling, read off a record in this catalogue that carries it. It exists
    # because every state register writes Thai only while 58% of the mapped
    # records carry Latin only, so one place stands in the directory twice and
    # the reading is the only thing that can introduce the halves. Last in, so
    # a building's own sign outranks the letter rules — ปันนา is Punna, which
    # is what is painted on it, not Panna.
    _LEX.update(raw.get("brand") or {})
    return _LEX


_DICT = None


def _load_dict(path=None):
    global _DICT
    if _DICT is not None:
        return _DICT
    import os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "data", "search_segdict.txt")
    words = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and THAI_RE.fullmatch(line):
                    words.add(line)
    except OSError:
        pass
    words.update(HEADWORDS)
    words.update(_lexicon())
    _DICT = words
    return _DICT


# A Thai word cannot begin on a mark or on a vowel written after its consonant,
# cannot end on a vowel written before its consonant, and cannot begin on a
# letter a killer is about to silence. Cuts at those points are not unlikely,
# they are impossible — and greedy matching made them: บุ่น came out as
# บุ + ่น and read "Bu Na".
_ILLEGAL_START = set("ัาิีึืุูำะ่้๊๋์็ฺํ๎ๆฯ")
_MAX_WORD = 20
_MAX_UNKNOWN = 12


def _segment(text):
    """Split a Thai run into dictionary words.

    Dynamic programming over the corpus dictionary, choosing the cut that
    leaves the fewest unaccounted RUNS, then the fewest unaccounted
    CHARACTERS, then the fewest words. Greedy longest-match was the first
    version and it strands the tail of a word it took too much of: คำอูน became
    คำ + อู + น and read "Kham U Na". (The objective and the legality rules are
    thapsap's segmenter, ported so both projects cut the same way.)

    A run the dictionary does not know is kept whole and read by rule — that
    is where every name lives.
    """
    d = _load_dict()
    n = len(text)
    if n == 0:
        return []
    INF = (10 ** 9, 10 ** 9, 10 ** 9)
    best = [INF] * (n + 1)
    back = [(-1, False)] * (n + 1)
    best[0] = (0, 0, 0)

    def legal(pos):
        if pos < n and text[pos] in _ILLEGAL_START:
            return False
        if 0 < pos <= n and text[pos - 1] in LEAD_VOWELS:
            return False
        if pos + 1 < n and text[pos + 1] == THANTHAKHAT:
            return False
        # ...and not between a silent leader and the letter it leads: ห|มื้อ
        # is not two words, it is หมื้อ with its ห cut off (ต้นหมื้อ read
        # "Tanaha Mue" while มื้อ, a dictionary word, was cheaper than หมื้อ).
        if 0 < pos < n and text[pos - 1:pos + 1] in HO_NAM + O_NAM:
            return False
        return True

    for i in range(n):
        if best[i] == INF or not legal(i):
            continue
        unk_i, chr_i, cnt_i = best[i]
        # Cost = (unknown runs, 2·unknown chars + 5·words, words). Charging
        # unknown characters alone shreds a NAME into dictionary syllables —
        # อนาคามี became อ + นา + คา + มี, "A Na Kha Mi" — because three
        # two-letter words cost less than eight unknown letters. Five per word
        # against two per letter keeps that name whole and still cuts หมูบุ่น
        # into หมู + บุ่น. The tuple's third term breaks ties toward fewer words.
        for ln in range(min(_MAX_WORD, n - i), 1, -1):
            if text[i:i + ln] in d and legal(i + ln):
                cand = (unk_i, chr_i + 5, cnt_i + 1)
                if cand < best[i + ln]:
                    best[i + ln], back[i + ln] = cand, (i, True)
        for ln in range(1, min(_MAX_UNKNOWN, n - i) + 1):
            if not legal(i + ln):
                continue
            cand = (unk_i + 1, chr_i + 2 * ln + 5, cnt_i + 1)
            if cand < best[i + ln]:
                best[i + ln], back[i + ln] = cand, (i, False)

    segs = []
    j = n
    while j > 0:
        i, known = back[j]
        if i < 0:                      # no legal path (all marks): keep whole
            segs.append((text[:j], False))
            break
        segs.append((text[i:j], known))
        j = i
    segs.reverse()

    out = []
    for t, known in segs:
        # adjacent unknowns are one run; and a stray consonant — one letter,
        # or one letter and the marks on it (นท์) — is never a word of its
        # own: it is the tail of the word before it (คำอู + น, ปริ + นท์)
        stray = not known and len(_strip_silent(t)) <= 1
        if out and (not known and not out[-1][1] or len(t) == 1 or stray):
            out[-1] = (out[-1][0] + t, out[-1][1] and known)
        else:
            out.append((t, known))
    return [t for t, _ in out]


ABBREV = {"ม": "m", "กม": "km", "ตร": "sq", "ชม": "hr"}


def romanize(text, sep=" ", syl_sep=""):
    """A Thai string, read aloud in Latin letters by RTGS.

    Latin already in the string is left exactly as it is — a name like
    "ร้าน 7-Eleven" keeps its Latin half untouched.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    out, last = [], 0
    for m in THAI_RE.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        run = m.group(0)
        # a unit abbreviation — "930 ม." is 930 m, not "930 ma."
        if text[m.end():m.end() + 1] == "." and run in ABBREV:
            out.append(ABBREV[run])
            last = m.end()
            continue
        parts = [_rom_word(w, syl_sep) for w in _segment(run)]
        out.append(sep.join(p for p in parts if p))
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    s = "".join(out)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title(text, syl_sep=""):
    """The reading, capitalised the way a name is written in Latin script.

    A word the lexicon spelt is left exactly as the lexicon spelt it — eXta
    and Café keep their shape; only the rule-built words get a capital.
    """
    spelt = set(_lexicon().values()) | set(ABBREV.values())
    out = []
    for w in romanize(text, syl_sep=syl_sep).split(" "):
        out.append(w if (w.rstrip(".") in spelt or not w) else w[:1].upper() + w[1:])
    return " ".join(out)


# ---------------------------------------------------------------------------
# The generic head word. A Thai place name almost always opens with the kind
# of thing it is — วัด, โรงเรียน, โรงพยาบาล — and those are dictionary words,
# not names. Translating the head and reading the rest is what turns a roll of
# 2,136 temples into something a reader who has no Thai can actually use.
#
# Every entry here is a common noun with a settled English equivalent. Nothing
# that is part of a name goes in this table.
# ---------------------------------------------------------------------------
HEADWORDS = {
    # places of worship
    "วัด": "Wat",
    "สำนักสงฆ์": "Monastic residence",
    "ที่พักสงฆ์": "Monastic retreat",
    "ศาลเจ้า": "Shrine",
    "มัสยิด": "Mosque",
    "โบสถ์": "Church",
    "คริสตจักร": "Church",
    # schooling
    "โรงเรียน": "School",
    "มหาวิทยาลัย": "University",
    "วิทยาลัย": "College",
    "ศูนย์พัฒนาเด็กเล็ก": "Childcare centre",
    "สถาบัน": "Institute",
    # health
    "โรงพยาบาล": "Hospital",
    "โรงพยาบาลส่งเสริมสุขภาพตำบล": "Sub-district health promoting hospital",
    "คลินิก": "Clinic",
    "สถานีอนามัย": "Health station",
    "ร้านขายยา": "Pharmacy",
    "ร้านยา": "Pharmacy",
    "ฟาร์มาซี": "Pharmacy",
    "เภสัช": "Pharmacy",
    "ทันตกรรม": "Dental",
    "การแพทย์": "Medical",
    # commerce
    "ร้าน": "Ran",                    # a bare "shop" — see NOTE below
    "ร้านขายของชำ": "Grocery shop",
    "ร้านอาหาร": "Restaurant",
    "ร้านกาแฟ": "Coffee shop",
    "ร้านตัดผม": "Barber",
    "ร้านเสริมสวย": "Beauty salon",
    "ตลาด": "Market",
    "ตลาดสด": "Fresh market",
    "ห้างสรรพสินค้า": "Department store",
    "ธนาคาร": "Bank",
    "ปั๊ม": "Filling station",
    "ปั๊มน้ำมัน": "Filling station",
    "สหกรณ์": "Cooperative",
    "บริษัท": "Company",
    "หจก": "Partnership",
    "ห้างหุ้นส่วนจำกัด": "Partnership",
    # staying
    "โรงแรม": "Hotel",
    "รีสอร์ท": "Resort",
    "รีสอร์ต": "Resort",
    "เกสต์เฮ้าส์": "Guest house",
    "เกสต์เฮาส์": "Guest house",
    "บ้านพัก": "Guest house",
    "หอพัก": "Dormitory",
    # civic and ground
    "ชุมชน": "Community",
    "หมู่บ้าน": "Village",
    "บ้าน": "Ban",                    # a place-name element, not "house"
    "เทศบาล": "Municipality",
    "องค์การบริหารส่วนตำบล": "Sub-district administrative organisation",
    "อบต": "Sub-district administrative organisation",
    "ที่ว่าการอำเภอ": "District office",
    "สถานีตำรวจ": "Police station",
    "สถานีตำรวจภูธร": "Provincial police station",
    "สภ": "Police station",
    "ไปรษณีย์": "Post office",
    "สวนสาธารณะ": "Public park",
    "สวน": "Garden",
    "อุทยานแห่งชาติ": "National park",
    "น้ำตก": "Waterfall",
    "ดอย": "Doi",                     # mountain, and part of the name itself
    "ถ้ำ": "Cave",
    "อ่างเก็บน้ำ": "Reservoir",
    "สนามกีฬา": "Sports ground",
    "สนามบิน": "Airport",
    "สถานีขนส่ง": "Bus terminal",
    "สถานีรถไฟ": "Railway station",
    "พิพิธภัณฑ์": "Museum",
    "หอศิลป์": "Art gallery",
    "ห้องสมุด": "Library",
    "ศูนย์": "Centre",
    "สาขา": "branch",
}

# NOTE on ร้าน and บ้าน: both are common nouns AND name elements. "ร้านสมพร"
# is Somphon's shop, but "บ้านถวาย" is a village called Ban Thawai and calling
# it "House Thawai" would be wrong. Where the head word is inseparable from the
# name it is romanised, not translated — that is why those two map to `Ran` and
# `Ban` rather than to English words.

# Where the English word goes. `Wat`, `Doi` and `Ban` are borrowed into
# English WITH the name and lead it — Wat Phra Singh, Doi Suthep. A translated
# generic noun trails instead, because that is how English says it: Huai Kaeo
# Waterfall, not Waterfall Huai Kaeo. Getting this backwards was the loudest
# wrongness in the first pass over the waterfall shelf.
LEADING_HEADS = {"Wat", "Doi", "Ban", "Ran", "Phra"}

_HEADS = sorted(HEADWORDS, key=len, reverse=True)


def head_split(text):
    """(english head, remainder) if the name opens with a known common noun."""
    t = unicodedata.normalize("NFC", (text or "").strip())
    for h in _HEADS:
        if t.startswith(h):
            return HEADWORDS[h], t[len(h):].strip()
    return None, t


def reading(text, syl_sep=""):
    """What a reader is shown beside a Thai-only name.

    The generic head word in English, the rest of the name read by RTGS. Both
    halves are honest about what they are: `Wat Phra Singh` translates วัด and
    reads พระสิงห์ — it does not claim to be the temple's own English sign.
    """
    if not text:
        return ""
    head, rest = head_split(text)
    body = title(rest, syl_sep=syl_sep)
    if not head:
        return body
    if not body:
        return head
    if head in LEADING_HEADS:
        return head + " " + body
    return body + " " + head


__all__ = ["romanize", "title", "reading", "head_split", "HEADWORDS"]
