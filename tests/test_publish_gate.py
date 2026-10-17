"""The checks that must pass before docs/ is committed and pushed.

This kept being rewritten as a throwaway script and then lost, so it lives
here now. Run it after build.py, before `git add docs/`:

    python3 tests/test_publish_gate.py

Three invariants:

1. No page hyperlinks a URL that check_links.py verified is dead. A dead
   site may be NAMED and DATED on a place page, and the Wayback copy may be
   linked, but the corpse itself never gets an <a href>.
2. No published file carries a /Users/... path (the wichaa privacy rule).
3. The site has a front page, the furniture it cannot render without, and
   that front page calls itself by the right domain.
   docs/ held 25,114 files with no docs/index.html at all and this gate said
   PASS: every check above was about what the pages CONTAIN, and a tree with
   no homepage contains nothing wrong. The file floor in standing_walk.sh
   (COUNT < 20000) cleared it too. See ESSENTIAL.
4. Every site under docs/ carries a card in the register
   (data/curated/sites.json, sites_layer.unregistered). Nan, 2026-09-28: all
   new sites carry cards; a publish without one is refused, and the refusal
   is addressed to the bot that posted it.

WHY THERE IS NO CNAME CHECK ANY MORE. There was a fourth invariant here:
docs/CNAME says motdang.net, "so a missing CNAME means the domain is about to
drop". That sentence belonged to GitHub Pages, which has not served this site
since it moved to an R2 bucket behind a Worker (publish/README.md: "GitHub is
not in the publish path at all, and neither is Cloudflare Pages"). motdang.net
is bound in the Cloudflare dashboard. No file in the bucket can hold it,
release it, or drop it. Left as written the note was worse than stale — it
aimed anyone debugging a domain outage at a file with no bearing on one, and
the obvious "fix" of editing it would have done nothing at all.

It was no use as a build sentinel either, which is the other thing it looked
like: build() wrote CNAME second, before a single page existed, so a build
that died at one percent still left a perfect one. ESSENTIAL below is the
check that actually catches that, and it always was.

What the check DID do, by accident, was hold BASE to account: build.py derived
CNAME from BASE, so a typo there failed the gate instead of quietly pointing
22,000 canonical URLs at a host nobody owns. That much is worth keeping, so it
survives as DOMAIN — read off the built front page, which is the thing readers
actually get, rather than off a file that no longer has a reason to exist.

The link scan parses hrefs once per file and tests set membership. Do not
rewrite it as "for each broken url, grep the tree" — that is O(files x urls)
and times out.
"""
import json
import os
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "tools"))
import holdback  # noqa: E402  a page or site held back this round is not checked

# "ok" answers. "social" is a walled garden — unverifiable, not dead, and
# "walled" is any other door shut to the checker (403/406/429) for the
# same reason.
# "redirect-offsite" lands somewhere real. Everything else is broken.
ALIVE = {"ok", "social", "redirect-offsite", "walled"}

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
    "icons.svg": 10_000,   # every icon on every page is drawn from this file
                           # (2026-09-10) — waived below for a tree built
                           # before that, whose pages carry the sprite inline
    "md.js": 10_000,       # the ticker, the map mounts, all 12,353 place pages
    "map.html": 2_000,     # the three doorstep pages, linked from every header
    "my.html": 2_000,
    "plan.html": 2_000,
    "404.html": 2_000,     # the worker serves this on every miss; without it a
                           # mistyped soi gets a bare nine-byte "Not found"
}

# The domain the front page must call itself by, and the tag it lives in.
# build.py writes this from BASE; see the docstring on why it is measured here
# rather than through docs/CNAME.
DOMAIN = "motdang.net"
CANONICAL = re.compile(r'<link rel="canonical" href="https?://([^/"]+)')


def building_now():
    """(pid, age_seconds) if another build.py owns docs/ right now, else None.

    build.py wipes docs/ at the start of every run and refills it over several
    minutes, so a gate that lands in that window sees a tree with no index.html
    and reports "not a site: index.html (absent)" — which reads as the site
    having been destroyed, when it is a rebuild caught mid-stride. The two
    readings call for opposite responses, and the alarming one is the wrong one.

    build.py holds cache/build.lock for exactly the window in which docs/ is
    legitimately incomplete, so it can be asked. A lock whose process is gone is
    stale (build.take_build_lock() clears those rather than obeying them) and is
    NOT a running build, so liveness is checked and not merely the file.

    Imported lazily and only on the failure path: build.py is 17,000 lines, and
    a gate on its way to PASS should not pay to import it. Anything going wrong
    in here degrades to None — a build.py that will not import is a problem to
    report as itself, never a reason for the gate to crash instead of FAIL.
    """
    try:
        sys.path.insert(0, str(ROOT))
        import build
        # Two lines, pid first, written by take_build_lock(), which owns this
        # format. Only the pid is parsed here; mtime gives the age.
        pid = int(build.LOCK.read_text().split()[0])
        age = time.time() - build.LOCK.stat().st_mtime
        try:
            os.kill(pid, 0)      # signal 0 asks without sending anything
        except ProcessLookupError:
            return None          # stale lock, not a running build
        except PermissionError:
            pass                 # it exists, it is just not ours to signal
    except Exception:
        return None
    return pid, age


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
    essential = dict(ESSENTIAL)
    home = DOCS / "index.html"
    if "icons.svg" not in (home.read_text(errors="ignore") if home.is_file() else ""):
        essential.pop("icons.svg", None)      # pages that never point at it
    for rel, floor in essential.items():
        f = DOCS / rel
        size = f.stat().st_size if f.is_file() else -1
        if size < floor:
            thin.append((rel, size))

    # WO-75 — get/ is the toys themselves, published verbatim from the repos that
    # build them. This suite is a check on the pages this site WRITES; making a
    # third-party game pass it would mean editing the game. downloads_layer.py
    # names any image without alt text in its own build line instead.
    #
    # WIDENED 2026-09-21 (Nan's call) to loop/, which is the same case: the Mae
    # Hong Son loop is built by its own repo and installed here verbatim. Four
    # of the places it lists have lost their websites — anusarnmarket.com,
    # baanjangnak.com, 99thegalleryhotel.com and the BOT museum are all
    # DNS-dead — and they are OSM `website` tags that minisite renders, not
    # links this build writes. Holding them here stopped the WHOLE site
    # publishing from 15:28 that day: ten hits of thirteen were under loop/.
    # The right repair is link-health retirement inside mhs-loop, the way
    # build.py already retires a dead link into a note with its archived copy.
    # Until that exists, this suite does not police a site it does not build.
    #
    # ADD A PREFIX HERE ONLY FOR A DIRECTORY THIS BUILD DOES NOT WRITE. Every
    # other installed minisite (ghost/, muay-thai/, roads/) passes today and
    # stays policed; carving them out pre-emptively would be turning the gate
    # down rather than telling the truth about who owns a page.
    FOREIGN = ("get/", "loop/")
    pages = [p for p in DOCS.rglob("*.html")
             if not p.relative_to(DOCS).as_posix().startswith(FOREIGN)
             and not holdback.held(p.relative_to(DOCS).as_posix())]
    hits, leaks = [], []
    for p in pages:
        text = p.read_text(errors="ignore")
        if "/Users/" in text:
            leaks.append(str(p.relative_to(DOCS)))
        for href in HREF.findall(text):
            if href.rstrip("/") in broken:
                hits.append((str(p.relative_to(DOCS)), href))

    # Read off the built page, not off BASE — BASE agreeing with itself proves
    # nothing. An absent index.html is already named by `thin`; it lands here
    # as an empty domain, which fails too and says so in its own words.
    home = DOCS / "index.html"
    found = CANONICAL.search(home.read_text(errors="ignore")) if home.is_file() else None
    domain = found.group(1) if found else ""

    print(f"essential files       {len(essential) - len(thin)}/{len(essential)} present and filled")
    print(f"pages scanned         {len(pages)}")
    print(f"broken URLs on file   {len(broken)}")
    print(f"links to broken URLs  {len(hits)}")
    print(f"/Users/ path leaks    {len(leaks)}")
    print(f"front page domain     {domain or '(no canonical link)'}")
    sys.path.insert(0, str(DOCS.parent))
    import sites_layer
    uncarded = [m for m in (sites_layer.unregistered(DOCS) if not thin else [])
                if not holdback.held(m)]
    print(f"sites without a card  {len(uncarded)}")

    for where, href in hits[:10]:
        print("  broken link:", where, href)
    for where in leaks[:10]:
        print("  path leak:  ", where)
    for rel, size in thin:
        print("  not a site: ", rel,
              "(absent)" if size < 0 else f"({size} bytes, floor {ESSENTIAL[rel]})")

    # A half-built docs/ is still a FAIL and must stay one: publishing it is the
    # thing deploy.py's floor exists to stop, and the walk's answer to a FAIL —
    # ship nothing, come back in twenty minutes — is already the right answer to
    # a race. Only the diagnosis changes, from "the site is gone" to "somebody
    # is building it", because those send a reader looking in opposite places.
    if thin:
        held = building_now()
        if held:
            pid, age = held
            print(f"\n  NOT A BROKEN SITE: pid {pid} is building this repo right "
                  f"now\n  (lock taken {int(age // 60)}m {int(age % 60)}s ago). "
                  f"docs/ is wiped at the start of\n  every build and refills "
                  f"over minutes, so the files above are missing\n  because they "
                  f"have not been written yet. Nothing is lost and nothing\n  "
                  f"needs fixing — wait for that build to finish and run this "
                  f"again.")

    if uncarded:
        print(sites_layer.refusal(uncarded))

    ok = not hits and not leaks and not thin and not uncarded and domain == DOMAIN
    # A page or site that failed is named for tools/holdback.py, which holds it
    # back and runs this gate again; the rest publishes (Nan, 2026-10-11).
    if not ok:
        holdback.propose({w for w, _ in hits}, "broken link")
        holdback.propose(leaks, "path leak")
        holdback.propose(uncarded, "no card")
        if thin:
            holdback.cannot("essential files missing or thin")
        if domain != DOMAIN:
            holdback.cannot("front page domain %r" % domain)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
