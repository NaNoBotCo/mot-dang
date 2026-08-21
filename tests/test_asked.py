#!/usr/bin/env python3
"""Every reader question leaves the same four things behind, or this fails.

    python3 tests/test_asked.py
    MD_DOCS=/path/to/scratch python3 tests/test_asked.py

Run after build.py. The rule it enforces is the one asked_layer.py's
docstring states: a question in data/asked.json is not answered until it has

  1. records it stands on (or says `gap: true` and means it),
  2. a card on asked.html and a page of its own at asked/<key>.html,
  3. a share card, and the page's og:image pointing at it,
  4. a reply make_post.py can produce with no unfilled placeholder in it.

Each check exists because the thing it guards went wrong by hand at least
once: a hand-built card whose ids no longer matched a record and listed
nothing; a page whose og:image named a card nobody had drawn; a sentence
that still said "{n}" because the placeholder was misspelt.

Two shapes are exempt on purpose: a `draft: true` entry (asked_new.py's stub)
is listed and skipped — it renders nowhere, so nothing can be broken; and a
`gap: true` entry has NO share card by decision (2026-08-19: a poster saying
"nobody does this" travels further than the sentence under it), so its page
must fall back to the brand card and any asked-<key>.png for it is an orphan.

`asked_on` must be a full ISO date. Month-only dates crept in once and made
the field useless for ordering.

`--no-cards` skips check 3 on a fresh clone with an empty assets/og/.
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = pathlib.Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

OG_META = re.compile(
    r"""<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']""", re.I)
UNFILLED = re.compile(r"\{(n|phoned|rest)\}")


def main():
    want_cards = "--no-cards" not in sys.argv
    import asked_layer
    import build
    data = build.load()
    everything = asked_layer.load(include_drafts=True)
    entries = [e for e in everything if not e.get("draft")]
    drafts = [e["key"] for e in everything if e.get("draft")]
    fails = []

    keys = [e["key"] for e in everything]
    if len(keys) != len(set(keys)):
        fails.append(("duplicate key", ", ".join(k for k in keys if keys.count(k) > 1)))
    for e in everything:
        k = e["key"]
        if not re.fullmatch(r"[a-z0-9-]+", k):
            fails.append((k, "key is not a url-safe slug"))
        if not (e.get("q", {}).get("th") and e.get("q", {}).get("en")):
            fails.append((k, "question needs both th and en"))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("asked_on", ""))):
            fails.append((k, f"asked_on must be YYYY-MM-DD, got {e.get('asked_on')!r}"))
    for e in entries:
        k = e["key"]

        # 1 — stands on records, or is a gap on purpose
        shown, counts = asked_layer.select(e, data)
        if e.get("gap"):
            if e.get("find"):
                fails.append((k, "gap: true AND a find selector — pick one"))
        elif not shown:
            fails.append((k, "find selects nothing — a hand-built card used to fail this silently"))

        # 4 — every sentence fills
        for p in e.get("lead", []) + e.get("notes", []):
            for lang in ("th", "en"):
                try:
                    txt = asked_layer._fill(p[lang], counts)
                except (KeyError, IndexError, ValueError) as ex:
                    fails.append((k, f"placeholder in {lang}: {ex}"))
                    continue
                if UNFILLED.search(txt):
                    fails.append((k, f"unfilled placeholder in {lang}"))
            for l in p.get("links", []):
                if not (l.get("href") and l.get("th") and l.get("en")):
                    fails.append((k, "link needs href, th, en"))

        # 2 — the page exists and carries the card
        page = DOCS / "asked" / f"{k}.html"
        if not page.exists():
            fails.append((k, f"no page at asked/{k}.html — run build.py"))
            continue
        html = page.read_text(encoding="utf-8", errors="ignore")
        if f'id="{k}"' not in html:
            fails.append((k, "page does not carry its own qacard"))
        asked_html = (DOCS / "asked.html").read_text(encoding="utf-8", errors="ignore")
        if f'asked/{k}.html' not in asked_html:
            fails.append((k, "asked.html does not link to the question page"))

        # 3 — its own picture (a gap: pointedly NOT its own picture)
        card = ROOT / "assets" / "og" / f"asked-{k}.png"
        m = OG_META.search(html)
        og = m.group(1) if m else ""
        if e.get("gap"):
            if card.exists():
                fails.append((k, "gap entry has a share card — delete assets/og/asked-%s.png" % k))
            if og.endswith(f"/og/asked-{k}.png"):
                fails.append((k, "gap entry's og:image points at a card; should fall back to brand"))
        elif want_cards:
            if not card.exists():
                fails.append((k, "no share card — run make_shelf_cards.py"))
            if not og.endswith(f"/og/asked-{k}.png"):
                fails.append((k, f"og:image is {og or 'missing'}, not its own card"))
            elif not (DOCS / "og" / f"asked-{k}.png").exists():
                fails.append((k, "og:image names a card that is not in docs/og/"))

    print(f"{len(entries)} questions in data/asked.json"
          + (f" · {len(drafts)} DRAFT (unpublished): {', '.join(drafts)}" if drafts else ""))
    for k, why in fails:
        print(f"  FAIL  {k}: {why}")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
