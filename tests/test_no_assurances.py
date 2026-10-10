#!/usr/bin/env python3
"""Reader-visible text on the built site, run through stylecheck's assurance forms.

Run as a script: python3 tests/test_no_assurances.py  (skips on an unbuilt site)

Why: on 2026-09-25 the toilets page, the location gate on every page, /here,
/chuai, /draw and /app all told readers their position was "not sent anywhere,  # stylecheck: allow
not stored" — assurance forms ~/.claude/STYLE.md §1 bans. stylecheck.py missed
them in the source because it read every string literal as somebody else's
quotation. This reads what a reader reads: the built pages, tags and scripts
stripped, every root page plus a sample of each province's place pages.
"""
import html
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
STYLECHECK = Path.home() / ".claude" / "bin" / "stylecheck.py"
SAMPLE_PER_PROVINCE = 40
# (page, words) that match a pattern and are not the site promising anything.
# Each carries why; add to this only with a reason a reader would accept.
# stylecheck: allow-start — the list names the words it excuses
NOT_A_PROMISE = [
    ("events.html", "We will"),          # organisers' own event descriptions, quoted
    ("asked.html", "never leaves"),      # "Some American paperwork never leaves the house" — remote notarization
    ("who.html", "no account"),          # "Mot Dang has no account on —" the impersonation list
    ("add.html", "no account"),          # the same list, under the ways to reach the ants
]
# stylecheck: allow-end


def visible_text(page):
    s = page.read_text(errors="ignore")
    s = re.sub(r"<(script|style|noscript|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<(br|p|li|h\d|div|tr)\b", "\n<", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s)


def main():
    if not (DOCS / "index.html").exists():
        print("skip: docs/ not built")
        return 0
    if not STYLECHECK.exists():
        print("skip: %s not on this machine" % STYLECHECK)
        return 0
    spec = importlib.util.spec_from_file_location("stylecheck", STYLECHECK)
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)

    pages = sorted(DOCS.glob("*.html"))
    for pv in ("cm", "cr"):
        pages += sorted((DOCS / pv / "p").glob("*.html"))[:SAMPLE_PER_PROVINCE]
    hits = []
    for p in pages:
        text = visible_text(p)
        for line in sc.scan(text, str(p.relative_to(DOCS)), False, code=False):
            if " ASSURANCE " in line and not any(
                    line.startswith(pg + ":") and ("'%s'" % w) in line for pg, w in NOT_A_PROMISE):
                hits.append(line)
    for h in hits[:40]:
        print("  " + h[:220])
    print("\n%d page(s) read, %d assurance form(s) in reader-visible text" % (len(pages), len(hits)))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
