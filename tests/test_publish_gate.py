"""The checks that must pass before docs/ is committed and pushed.

This kept being rewritten as a throwaway script and then lost, so it lives
here now. Run it after build.py, before `git add docs/`:

    python3 tests/test_publish_gate.py

Three invariants:

1. No page hyperlinks a URL that check_links.py verified is dead. A dead
   site may be NAMED and DATED on a place page, and the Wayback copy may be
   linked, but the corpse itself never gets an <a href>.
2. No published file carries a /Users/... path (the wichaa privacy rule).
3. docs/CNAME says motdang.net — build.py wipes docs/ every run and re-emits
   it, so a missing CNAME means the domain is about to drop.

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

    print(f"pages scanned         {len(pages)}")
    print(f"broken URLs on file   {len(broken)}")
    print(f"links to broken URLs  {len(hits)}")
    print(f"/Users/ path leaks    {len(leaks)}")
    print(f"CNAME                 {domain or '(missing)'}")

    for where, href in hits[:10]:
        print("  broken link:", where, href)
    for where in leaks[:10]:
        print("  path leak:  ", where)

    ok = not hits and not leaks and domain == "motdang.net"
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
