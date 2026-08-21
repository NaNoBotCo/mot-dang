"""The checks that must pass before docs/ is committed and pushed.

This kept being rewritten as a throwaway script and then lost, so it lives
here now. Run it after build.py, before `git add docs/`:

    python3 tests/test_publish_gate.py

Four invariants:

1. No page hyperlinks a URL that check_links.py verified is dead. A dead
   site may be NAMED and DATED on a place page, and the Wayback copy may be
   linked, but the corpse itself never gets an <a href>.
2. No published file carries a /Users/... path (the wichaa privacy rule).
3. docs/CNAME says motdang.net — build.py wipes docs/ every run and re-emits
   it, so a missing CNAME means the domain is about to drop.
4. The site has a front page, and the furniture it cannot render without.
   docs/ held 25,114 files with no docs/index.html at all and this gate said
   PASS: every check above was about what the pages CONTAIN, and a tree with
   no homepage contains nothing wrong. The file floor in standing_walk.sh
   (COUNT < 20000) cleared it too. See ESSENTIAL.

The link scan parses hrefs once per file and tests set membership. Do not
rewrite it as "for each broken url, grep the tree" — that is O(files x urls)
and times out.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# "ok" answers. "social" is a walled garden — unverifiable, not dead.
# "redirect-offsite" lands somewhere real. Everything else is broken.
ALIVE = {"ok", "social", "redirect-offsite"}

HREF = re.compile(r'href="([^"]+)"')

# What a site cannot be a site without. build.py wipes docs/ and re-emits all
# of these unconditionally, so any one of them missing means the build stopped
# part-way, and a tiny one means it stopped mid-write.
#
# The number beside each is a floor under "did this get written at all", NOT an
# assertion about size: every one sits an order of magnitude below what the
# file actually weighs (index.html ~190 KB, md.js ~180 KB, style.css ~130 KB).
# A false FAIL here stops the walk publishing anything, so the floors stay
# loose enough that a legitimately lighter build still ships — while an empty
# or truncated file, which is the failure actually seen, still fails.
ESSENTIAL = {
    "index.html": 10_000,  # the front page — there is no other way in
    "style.css": 10_000,   # unstyled and broken look identical to a reader
    "md.js": 10_000,       # the ticker, the map mounts, all 12,353 place pages
    "map.html": 2_000,     # the three doorstep pages, linked from every header
    "my.html": 2_000,
    "plan.html": 2_000,
    "CNAME": 5,            # present here, and its contents checked below
}


def main():
    if not DOCS.exists():
        print("docs/ is not built — run build.py first")
        return 1

    links = json.loads((ROOT / "data" / "linkhealth.json").read_text())["links"]
    broken = {u.rstrip("/") for u, v in links.items() if v.get("status") not in ALIVE}
    if not broken:
        # A gate that checks nothing passes every time. This happened once.
        print("FAIL: linkhealth.json yielded no broken URLs — check its shape")
        return 1

    # Cheap (seven stats), and it runs before the scan so that a build which
    # stopped part-way is named as that, rather than as a clean-looking report
    # over whatever pages did get written.
    thin = []
    for rel, floor in ESSENTIAL.items():
        f = DOCS / rel
        size = f.stat().st_size if f.is_file() else -1
        if size < floor:
            thin.append((rel, size))

    pages = list(DOCS.rglob("*.html"))
    hits, leaks = [], []
    for p in pages:
        text = p.read_text(errors="ignore")
        if "/Users/" in text:
            leaks.append(str(p.relative_to(DOCS)))
        for href in HREF.findall(text):
            if href.rstrip("/") in broken:
                hits.append((str(p.relative_to(DOCS)), href))

    cname = (DOCS / "CNAME")
    domain = cname.read_text().strip() if cname.exists() else ""

    print(f"essential files       {len(ESSENTIAL) - len(thin)}/{len(ESSENTIAL)} present and filled")
    print(f"pages scanned         {len(pages)}")
    print(f"broken URLs on file   {len(broken)}")
    print(f"links to broken URLs  {len(hits)}")
    print(f"/Users/ path leaks    {len(leaks)}")
    print(f"CNAME                 {domain or '(missing)'}")

    for where, href in hits[:10]:
        print("  broken link:", where, href)
    for where in leaks[:10]:
        print("  path leak:  ", where)
    for rel, size in thin:
        print("  not a site: ", rel,
              "(absent)" if size < 0 else f"({size} bytes, floor {ESSENTIAL[rel]})")

    ok = not hits and not leaks and not thin and domain == "motdang.net"
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
