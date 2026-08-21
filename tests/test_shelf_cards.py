#!/usr/bin/env python3
"""Every list page's share card exists, and none of them is a card for a shelf
that has gone.

    python3 tests/test_shelf_cards.py

Run after build.py (and after make_shelf_cards.py, which draws them). Four
checks, each guarding a way this goes wrong quietly:

1. **Nothing points at a missing picture.** A page whose og:image 404s unfurls
   in LINE and Facebook as a bare grey rectangle — worse than the brand card
   it would have fallen back to, because the fallback was the thing the
   `shelf_og()` guard existed to keep.
2. **Every list page has a card of its own.** Province, category and
   sub-shelf. This is the check that catches the real regression: somebody
   adds a shelf, nobody re-runs the generator, and the new shelf is the one
   page on the site sharing as a generic ant.
3. **No orphans.** A shelf that was renamed or emptied leaves its card behind
   in assets/og/, where it will be copied into docs/ forever. The failure is
   a stale five names under a shelf name that no longer means them.
4. **The signature index agrees with the pictures on disk.** The index is
   what makes a re-run cheap; an index claiming a card that is not there
   means the next run skips drawing it.

Checks 2-4 are advisory when no shelf card has been drawn at all — a fresh
clone has an empty assets/og/, and the site is designed to build without it.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OG_SRC = ROOT / "assets" / "og"
INDEX = OG_SRC / "_shelf-index.json"

OG_META = re.compile(
    r"""<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']""", re.I)


def list_pages():
    """The province, category and sub-shelf pages, by their card stem.

    Found on disk rather than recomputed from categories.json, so the test
    checks what was actually built and cannot agree with a wrong build for
    the same wrong reason.
    """
    out = {}
    for prov in ("cm", "cr"):
        pdir = DOCS / prov
        if not pdir.is_dir():
            continue
        out[f"shelf-{prov}"] = pdir / "index.html"
        for cat in sorted(p for p in pdir.iterdir() if p.is_dir()):
            if not (cat / "index.html").exists():
                continue
            out[f"shelf-{prov}-{cat.name}"] = cat / "index.html"
            for sub in sorted(p for p in cat.iterdir() if p.is_dir()):
                if (sub / "index.html").exists():
                    out[f"shelf-{prov}-{cat.name}-{sub.name}"] = sub / "index.html"
    return out


def main():
    if not DOCS.exists():
        print("no docs/ — run build.py first")
        return 1
    pages = list_pages()
    drawn = {f.stem for pat in ("shelf-*.png", "asked-*.png")
             for f in OG_SRC.glob(pat)} if OG_SRC.exists() else set()
    shipped = {f.stem for pat in ("shelf-*.png", "asked-*.png")
               for f in (DOCS / "og").glob(pat)} if (DOCS / "og").is_dir() else set()
    # Reader questions draw into the same folder and index (see test_asked.py
    # for their own four checks); here they only need to not be orphans. A
    # `gap: true` question is exempt in both directions — it has no card by
    # decision, so it is neither an orphan nor a page missing one.
    sys.path.insert(0, str(ROOT))
    import asked_layer
    gaps = {e["key"] for e in asked_layer.load(include_drafts=True) if e.get("gap")}
    for q in (DOCS / "asked").glob("*.html") if (DOCS / "asked").is_dir() else []:
        if q.stem not in gaps:
            pages[f"asked-{q.stem}"] = q

    broken, uncarded, orphans, unindexed = [], [], [], []

    # 1 — every og:image on a list page resolves to a file we shipped
    for stem, path in sorted(pages.items()):
        m = OG_META.search(path.read_text(encoding="utf-8", errors="ignore"))
        rel = (m.group(1) if m else "").rsplit("/", 1)[-1]
        if not m:
            broken.append((stem, "no og:image at all"))
        elif not (DOCS / ("og/" + rel if rel.startswith(("shelf-", "asked-")) else rel)).exists():
            broken.append((stem, rel))
        elif not rel.startswith(("shelf-", "asked-")):
            uncarded.append((stem, "falls back to " + rel))

    # 3 — cards for shelves that no longer exist
    orphans = sorted(drawn - set(pages))
    # 4 — the index and the pictures agree
    if INDEX.exists():
        unindexed = sorted(set(json.loads(INDEX.read_text())) - drawn)

    print(f"{len(pages):,} list pages · {len(drawn):,} cards drawn · "
          f"{len(shipped):,} shipped into docs/og/")

    for title, rows in (("BROKEN og:image", broken),
                        ("NO CARD", uncarded),
                        ("ORPHAN card", [(o, "no such shelf") for o in orphans]),
                        ("INDEXED but not drawn", [(u, "") for u in unindexed])):
        if not rows:
            continue
        print(f"{title}: {len(rows)}")
        for stem, detail in rows[:10]:
            print(f"  {stem}  {detail}")
        if len(rows) > 10:
            print(f"  ... and {len(rows) - 10} more")

    if broken or orphans or unindexed:
        print("FAIL")
        return 1
    if uncarded and drawn:
        # Advisory only on a fresh tree with no cards at all; a hard failure
        # once the generator has run, because then a bare shelf is a miss.
        print("FAIL — run: python3 make_shelf_cards.py && python3 build.py")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
