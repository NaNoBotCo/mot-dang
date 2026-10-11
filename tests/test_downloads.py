#!/usr/bin/env python3
"""WO-75 — the toys, and the three ways this shelf can lie.

Run:  python3 tests/test_downloads.py     (needs a built docs/)

What is checked, and why each one is here rather than trusted:

  1. EVERY BUTTON LANDS ON A FILE THAT EXISTS. A download shelf whose button
     404s is worse than no shelf: the reader tried, and the site failed in
     the one place it was making a promise it could keep.
  2. A PRICE ALWAYS HAS A RAIL. `price` with no `buy` is refused by the
     layer; this asserts the refusal, because the failure mode is a printed
     baht figure with nothing behind it.
  3. THE SEARCH ROWS MATCH THE PAGE. Every card on /get.html has a row in
     data/downloads.json and every row's `u` anchors to a card — the whole
     point of the shelf is that the box finds it, and a row pointing at an
     anchor that is not there fails silently in the browser.
  4. THE MEASUREMENTS ARE THE FILE'S. The size on the button and the sha256
     under it are re-derived here from the bytes in docs/get/ and compared,
     so a registry that grew a typed number is caught.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
REG = ROOT / "data" / "curated" / "downloads.json"

fails = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def main():
    page = DOCS / "get.html"
    if not page.exists():
        print("docs/get.html is not built — run build.py first")
        return 1
    html = page.read_text()
    reg = json.loads(REG.read_text())
    toys = reg.get("toys") or []
    rows = json.loads((DOCS / "data" / "downloads.json").read_text())

    print("the buttons")
    hrefs = re.findall(r'<a class="(?:tbtn|topen)" href="([^"]+)"', html)
    local = [h for h in hrefs if not h.startswith(("http://", "https://", "#"))]
    missing = [h for h in local if not (DOCS / h.split("#")[0]).exists()]
    check(f"every local button points at a file that exists ({len(local)} checked)",
          not missing, str(missing[:3]))

    print("the prices")
    priced = [t for t in toys if (t.get("price") or 0) and not t.get("buy")]
    ids_on_page = set(re.findall(r'<li class="toy" id="([^"]+)"', html))
    check("a price with no rail is held off the page",
          not (ids_on_page & {t.get("id") for t in priced}),
          str(sorted(ids_on_page & {t.get("id") for t in priced})))
    # And the other way: a row that IS priced must carry the baht figure, not
    # a size — a paid toy advertised by its weight is a free toy.
    for t in toys:
        if (t.get("price") or 0) and t.get("buy") and t.get("id") in ids_on_page:
            card = html.split(f'id="{t["id"]}"', 1)[1].split("</li>", 1)[0]
            check(f'{t["id"]} shows its price', f'฿{t["price"]:,}' in card)

    print("the search rows")
    check("a row for every card, a card for every row",
          {r["u"].split("#")[1] for r in rows} == ids_on_page,
          str(ids_on_page ^ {r["u"].split("#")[1] for r in rows}))
    check("every row is in the toys category and carries its shelf",
          all(r.get("c") == ["dl"] and r.get("sh") == "get.html" for r in rows))
    check("every row has a name to match on", all((r.get("n") or "").strip() for r in rows))
    # The row ids must not collide with a place id, or the card panel would
    # find a toy where it expected a shop.
    check("row ids are namespaced", all(r["id"].startswith("dl:") for r in rows))

    print("the measurements")
    for m in re.finditer(r'<li class="toy" id="([^"]+)".*?</li>', html, re.S):
        tid, card = m.group(1), m.group(0)
        f = next((DOCS / "get").glob(tid + ".*"), None)
        if f is None:
            continue                      # an `open`-only toy ships no file
        blob = f.read_bytes()
        sha = re.search(r"SHA-256 ([0-9a-f]{16})", card)
        if sha:
            check(f"{tid} sha is the file's",
                  hashlib.sha256(blob).hexdigest().startswith(sha.group(1)))
        size = re.search(r"⬇️ ([\d.]+) (MB|kB)", card)
        if size:
            got = float(size.group(1))
            want = len(blob) / (1e6 if size.group(2) == "MB" else 1e3)
            check(f"{tid} size is the file's",
                  abs(got - want) <= (0.05 if size.group(2) == "MB" else 1))

    print()
    if fails:
        print(f"{len(fails)} FAILED: " + "; ".join(fails))
        return 1
    print("all good")
    return 0


if __name__ == "__main__":
    sys.exit(main())
