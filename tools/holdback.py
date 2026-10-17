#!/usr/bin/env python3
"""Hold back the failing part of a build; publish the rest (Nan, 2026-10-11, "A").

Until 2026-10-11 one bad page stopped the whole publish: 26 rounds in a row
published nothing because sites/bum-gun/ drew a pin off its frame, two pages
had no card, and so on — each the work of one session, each blocking the
other 270,000 files. Now a gate that fails on a page or a site names it here,
the gate runs again without it, and the deploy leaves that path in the bucket
as it is: its last published version stays live, and a page that was never
published stays unpublished.

A unit is a site directory (sites/<slug>/, or a top-level folder installed
from assets/<name>/) or one .html page. A failure anywhere else — a record's
pin, a shared script, the front page and the other essential files — is not
held: the gate fails as before. More than MAX units in one round fails too;
that many is a systemic fault, not one session's page.

    python3 tools/holdback.py reset                 # start of a round's gates
    python3 tools/holdback.py accept <proposals>    # a gate's proposals → held
    python3 tools/holdback.py take <reason> < paths # docs-relative paths → held
    python3 tools/holdback.py list                  # held this round

The list lives at $MD_HOLD_BACK (the server: /srv/state/held-back.txt), else
cache/held-back.txt; one "<unit>\\t<reason>" per line. A gate run with
$MD_HOLD_PROPOSE set writes there what it would hold, "!\\t<why>" for a
failure it cannot.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
PATH = Path(os.environ.get("MD_HOLD_BACK") or (ROOT / "cache" / "held-back.txt"))
MAX = int(os.environ.get("MD_HOLD_MAX") or 20)

# Pages every other page leans on (tests/test_publish_gate.py ESSENTIAL, the
# offline page, search): an old copy of one beside new pages is a broken site.
PROTECTED = {"index.html", "map.html", "my.html", "plan.html", "404.html",
             "chuai.html", "search.html"}


def _installed(name):
    """A top-level folder copied whole from assets/<name>/ (the loop, muay-thai, …)."""
    a = ROOT / "assets" / name
    return a.is_dir() and any(a.rglob("*.html"))


def unit_of(rel):
    """The unit a docs-relative path belongs to, or None when it cannot be held."""
    rel = rel.strip().lstrip("/")
    if rel.startswith("docs/"):
        rel = rel[5:]
    parts = rel.split("/")
    if parts[0] == "sites" and len(parts) >= 2 and parts[1]:
        return "sites/%s/" % parts[1]
    if len(parts) >= 2 and parts[0] and _installed(parts[0]):
        return parts[0] + "/"
    if rel.endswith(".html") and rel not in PROTECTED:
        return rel
    return None


def load():
    """{unit: reason} held this round."""
    out = {}
    try:
        for line in PATH.read_text().splitlines():
            u, _, why = line.partition("\t")
            if u and u != "!":
                out[u] = why
    except OSError:
        pass
    return out


_HELD = None


def held(rel):
    """True when rel is inside a unit held this round."""
    global _HELD
    if _HELD is None:
        _HELD = load()
    rel = rel.lstrip("/")
    if rel.startswith("docs/"):
        rel = rel[5:]
    return any(rel == u or (u.endswith("/") and rel.startswith(u)) for u in _HELD)


def propose(rels, why):
    """For a gate: name what it would hold. False when $MD_HOLD_PROPOSE is unset
    or a path cannot be held (that is written as "!", so the round fails)."""
    out = os.environ.get("MD_HOLD_PROPOSE")
    if not out:
        return False
    ok, lines = True, []
    for r in rels:
        u = unit_of(r)
        if u is None:
            ok = False
            lines.append("!\t%s: %s cannot be held" % (why, r))
        else:
            lines.append("%s\t%s" % (u, why))
    with open(out, "a") as fh:
        fh.write("".join(l + "\n" for l in lines))
    return ok


def cannot(why):
    """For a gate: a failure no unit explains."""
    out = os.environ.get("MD_HOLD_PROPOSE")
    if out:
        with open(out, "a") as fh:
            fh.write("!\t%s\n" % why)


def excludes():
    """rclone --exclude-from globs for the held units, escaped like deploy.py's."""
    esc = lambda s: re.sub(r"([*?\[\]{}\\])", r"\\\1", s)
    return ["/" + esc(u) + ("**" if u.endswith("/") else "") for u in load()]


def _merge(new):
    cur = load()
    for u, why in new.items():
        if u in cur and why not in cur[u].split("; "):
            cur[u] += "; " + why
        else:
            cur.setdefault(u, why)
    if len(cur) > MAX:
        print("holdback: %d units, over %d — not one session's page; nothing held" % (len(cur), MAX))
        return False
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text("".join("%s\t%s\n" % kv for kv in sorted(cur.items())))
    for u, why in sorted(new.items()):
        print("held back: %s  (%s)" % (u, why))
    return True


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "list"
    if cmd == "reset":
        PATH.unlink(missing_ok=True)
        return 0
    if cmd == "list":
        for u, why in sorted(load().items()):
            print("%s\t%s" % (u, why))
        return 0
    if cmd == "accept":
        try:
            lines = Path(argv[2]).read_text().splitlines()
        except (IndexError, OSError):
            print("holdback: the gate named nothing to hold")
            return 1
        bad = [l.partition("\t")[2] for l in lines if l.startswith("!\t")]
        if bad or not lines:
            for b in bad[:10]:
                print("not holdable: " + b)
            return 1
        new = {}
        for l in lines:
            u, _, why = l.partition("\t")
            new.setdefault(u, why)
        return 0 if _merge(new) else 1
    if cmd == "take":
        why = argv[2] if len(argv) > 2 else "held"
        new = {}
        for r in sys.stdin.read().split():
            u = unit_of(r)
            if u is None:
                print("not holdable: %s: %s" % (why, r))
                return 1
            new.setdefault(u, why)
        return 0 if new and _merge(new) else 1
    if cmd == "line":
        # One line for the walk's ledger: "sites/bum-gun/ (map sanity); …"
        print("; ".join("%s (%s)" % kv for kv in sorted(load().items())))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
