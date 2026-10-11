"""A place whose name claims the best gets one line under its h1, pointing to
/sites/best-krapow/#sign — why search, signs and stars can't say what is best,
and how to find out at the curb (Nan, 2026-10-04: "link to it by finding
references to 'best x'").

    best_layer.claims(r)   → the phrase in the name that claims it, or ""
    best_layer.line(r, bi) → the <p> for the place page, or ""
"""
import re

HREF_EN = "/sites/best-krapow/#sign"
HREF_TH = "/sites/best-krapow/th/#sign"

# "best" as a word, and the Thai superlatives of taste and quality.
_CLAIM = re.compile(r"\bbest\b|(?:อร่อย|ดี|เด็ด|แซ่บ|สวย|เจ๋ง)ที่สุด", re.I)
# Names where "best" is part of a brand or a phrase rather than a claim.
_NOT = re.compile(r"best\s*express|best\s*friend|best\s*part|u-best", re.I)


def claims(r):
    for k in ("name", "nameTh", "nameEn"):
        v = str(r.get(k) or "")
        if v and not _NOT.search(v):
            m = _CLAIM.search(v)
            if m:
                return m.group(0)
    return ""


def line(r, bi):
    try:
        if not claims(r):
            return ""
        th = f'ป้ายบอกว่าที่สุด ใครเป็นคนตัดสิน <a href="{HREF_TH}">→</a>'
        en = f'The sign says best. Who decides? <a href="{HREF_EN}">→</a>'
        return f'<p class="placestatus bestline">{bi(th, en, raw=True)}</p>'
    except Exception:
        return ""
