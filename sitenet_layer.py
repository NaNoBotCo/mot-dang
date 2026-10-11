#!/usr/bin/env python3
"""The Mot Dang net — the site's own pages strung like the nets of places.

net_layer.py strings place records; this strings the register. Each card and
page in data/curated/sites.json is a jewel, the register's groups are the strands, and
three more strands hang beside them: the files written for bots
(data/curated/sitenet.json "machines"), the place nets (nets.json), each
pointing at its site or at its first member page, and other people's sites
(sitenet.json "neighbours").

After every page is written, inject(docs) puts the whole net on each card's
page that lives under docs/ and each register page (sites.json "pages"), that
page marked "you are here", and on /sites/.
A Worker-served or external card is a jewel with no page here to carry it.
The block sits between <!--sitenet--> markers, so running again replaces it.

Entry points: inject(docs) → (pages, skipped); net_json(docs) → dict;
llms_section(docs) → text for llms.txt.
"""
import html
import json
import pathlib
import re

import net_layer
import sites_layer

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "curated" / "sitenet.json"
BASE = sites_layer.BASE
MARK = re.compile(r"<!--sitenet-->.*?<!--/sitenet-->", re.S)

# Self-contained: several minisites carry their own stylesheet and none of the
# site's, so the block brings its colours with it.
CSS = """<style>
.sitenet{--mute:#6b6b6b;--muted:#6b6b6b;margin:1.2rem auto;max-width:60rem;padding:.8rem .9rem;background:#fffaf0;color:#2b2b2b;
border:2px solid #c0392b;border-radius:.8rem;box-shadow:3px 3px 0 #f1c40f;
font:inherit;line-height:1.5;text-align:left}
.sitenet h2{margin:0 0 .2rem;font-size:1.05rem;color:inherit}
.sitenet .netname{margin:0 0 .4rem;font-weight:600}
.sitenet .lede{margin:.2rem 0 .6rem}
.sitenet details{margin:.35rem 0;border-top:1px dashed #d8c8a8;padding-top:.35rem}
.sitenet summary{cursor:pointer;font-weight:600;padding:.2rem 0}
.sitenet ul{list-style:none;padding-left:0;margin:.3rem 0}
.sitenet li{padding:.3rem 0}
.sitenet li a,.sitenet li a .en{color:#8e1b12}
.sitenet li .why{display:block;font-size:.9rem;color:#6b6b6b}
.sitenet li.here{background:#fdebd0;border-radius:.5rem;padding:.3rem .45rem}
.sitenet .roman{font-style:italic;color:#6b6b6b;font-size:.85rem}
.sitenet .netsrc{font-size:.8rem;color:#6b6b6b;margin:.5rem 0 0}
.sitenet .netsrc a{color:#8e1b12}
</style>"""

_NET = None


def load():
    global _NET
    if _NET is None:
        _NET = json.loads(DATA.read_text(encoding="utf-8"))
    return _NET


def _e(s):
    return html.escape(str(s or ""), quote=True)


def _bi(th, en):
    if th and en and th != en:
        return (f'<span class="th" lang="th">{_e(th)}</span>'
                f'<span class="th" lang="th"> · </span><span class="en" lang="en">{_e(en)}</span>')
    return _e(th or en)


def _page_of(card, docs):
    """The file under docs/ that carries this card, or None."""
    if card.get("served") != "docs" or card["href"].startswith("http"):
        return None
    h = card["href"]
    f = docs / h / "index.html" if h.endswith("/") else docs / h
    return f if f.exists() else None


_FOUND = {}


def _found_on_disk(docs):
    """Outside a build net_layer is unbound: read each member's page off the
    search index (docs/data/index.json: id, p = province, s = slug)."""
    if not _FOUND:
        want = {}
        for k, n in net_layer.load().items():
            for s in n.get("strands", []):
                for j in s.get("jewels", []):
                    want.setdefault(j["id"], []).append(k)
        try:
            rows = json.loads((docs / "data" / "index.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rows = []
        hit = {r["id"]: "%s/p/%s" % (r["p"], r["s"]) for r in rows if r.get("id") in want}
        for k, n in net_layer.load().items():
            for s in n.get("strands", []):
                for j in s.get("jewels", []):
                    h = hit.get(j["id"])
                    if k not in _FOUND and h and (docs / (h + ".html")).exists():
                        _FOUND[k] = h
    return _FOUND


def _place_nets(docs):
    """[(key, net, href-from-root, site card or None)] — a net with no site of its
    own points at its first member page that the build wrote."""
    out = []
    for key, net in net_layer.load().items():
        card = sites_layer.net_site(key)
        if card:
            out.append((key, net, card["href"], card))
            continue
        first = net_layer.first_href(key) or _found_on_disk(docs).get(key)
        if first:
            out.append((key, net, "%s.html#net-%s" % (first, key), None))
    return out


def strands(docs):
    """The whole net, as data: [{key, th, en, roman, jewels: [{id, href, th, en,
    line_th, line_en}]}]. A docs card whose page is not written yet is left out."""
    net = load()
    cs = [c for c in sites_layer.cards() if sites_layer.on_disk(c, docs)]
    out = []
    pages = sites_layer.page_entries(docs)
    for g in sites_layer.groups():
        js = [{"id": c["id"], "href": c["href"], "th": c["th"], "en": c["en"],
               "line_th": c.get("line_th", ""), "line_en": c.get("line_en", "")}
              for c in cs if c.get("group") == g["key"]]
        js += [{"id": "page:" + p["href"], "href": p["href"], "th": p["th"], "en": p["en"],
                "line_th": p["line_th"], "line_en": p["line_en"]}
               for p in pages if p["group"] == g["key"]]
        if js:
            out.append({"key": g["key"], "th": g["th"], "en": g["en"], "jewels": js})
    m = net["machines"]
    out.append({"key": "bots-files", "th": m["th"], "en": m["en"], "roman": m.get("roman", ""),
                "jewels": [dict(j, id="file:" + j["href"]) for j in m["jewels"]]})
    p = net["places"]
    pj = []
    for key, n, href, card in _place_nets(docs):
        size = sum(len(s.get("jewels", [])) for s in n.get("strands", []))
        pj.append({"id": "net:" + key, "href": href,
                   "th": n["th"], "en": n["en"],
                   "line_th": "%d ที่" % size + (" · เว็บ: " + card["th"] if card else ""),
                   "line_en": "%d places" % size + (" · site: " + card["en"] if card else "")})
    if pj:
        out.append({"key": "place-nets", "th": p["th"], "en": p["en"],
                    "roman": p.get("roman", ""), "jewels": pj})
    nb = net.get("neighbours")
    if nb and nb.get("jewels"):
        out.append({"key": "neighbours", "th": nb["th"], "en": nb["en"], "roman": nb.get("roman", ""),
                    "jewels": [dict(j, id="ext:" + j["href"]) for j in nb["jewels"]]})
    return out


def block(here, prefix, docs, sts=None):
    """here: the card id of the page being written (None on /sites/)."""
    net = load()
    sts = sts if sts is not None else strands(docs)
    parts = ['<!--sitenet-->', CSS, '<section class="sitenet" id="motdang-net">',
             "<h2>%s</h2>" % _bi("ร้อยไว้ในตาข่ายเดียวกัน", "Strung in the same net"),
             '<p class="netname">%s <span class="roman">%s</span></p>' % (
                 _bi(net["th"], net["en"]), _e(net.get("roman", ""))),
             '<p class="lede">%s</p>' % _bi(net["lede_th"], net["lede_en"])]
    for s in sts:
        mine = any(j["id"] == here for j in s["jewels"])
        rows = []
        for j in s["jewels"]:
            why = _bi(j.get("line_th", ""), j.get("line_en", ""))
            if j["id"] == here:
                rows.append('<li class="here"><b>%s</b> — %s<span class="why">%s</span></li>'
                            % (_bi(j["th"], j["en"]), _bi("ที่นี่", "you are here"), why))
            else:
                href = j["href"] if j["href"].startswith("http") else prefix + j["href"]
                rows.append('<li><a href="%s">%s</a><span class="why">%s</span></li>'
                            % (_e(href), _bi(j["th"], j["en"]), why))
        parts.append('<details%s><summary>%s%s (%d)</summary><ul>%s</ul></details>' % (
            " open" if mine else "", _bi(s["th"], s["en"]),
            (' <span class="roman">%s</span>' % _e(s["roman"])) if s.get("roman") else "",
            len(rows), "".join(rows)))
    parts.append('<p class="netsrc"><a href="%snet.json">net.json</a> · <a href="%s" rel="noopener">%s</a></p>' % (
        _e(prefix), _e(net_layer.EXPLAINER),
        _bi("ทำไมเป็นตาข่าย — Indra's Net, Drawn (ภาษาอังกฤษ)", "Why a net — Indra's Net, Drawn")))
    parts.append("</section><!--/sitenet-->")
    return "".join(parts)


def _put(f, blk):
    text = MARK.sub("", f.read_text(encoding="utf-8"))
    i = text.rfind("</main>")
    if i < 0:
        i = text.rfind("</body>")
    if i < 0:
        return False
    f.write_text(text[:i] + blk + text[i:], encoding="utf-8")
    return True


def inject(docs):
    """Put the net on each card's and register page's file under docs/, and on /sites/.
    Returns (pages written, [card ids with no page here])."""
    docs = pathlib.Path(docs)
    sts = strands(docs)
    done, skipped = 0, []
    targets = []
    for c in sites_layer.cards():
        f = _page_of(c, docs)
        if f is None:
            skipped.append(c["id"])
        else:
            targets.append((c["id"], f))
    for p in sites_layer.page_entries(docs):
        f = docs / p["href"]
        targets.append(("page:" + p["href"], f / "index.html" if p["href"].endswith("/") else f))
    hub = docs / "sites" / "index.html"
    if hub.exists():
        targets.append((None, hub))
    for cid, f in targets:
        depth = len(f.relative_to(docs).parts) - 1
        if _put(f, block(cid, "../" * depth, docs, sts)):
            done += 1
    return done, skipped


def net_json(docs):
    net = load()
    sts = strands(docs)
    for s in sts:
        for j in s["jewels"]:
            j["url"] = j["href"] if j["href"].startswith("http") else BASE + j["href"]
    return {"name": {"th": net["th"], "en": net["en"]},
            "about": {"th": net["lede_th"], "en": net["lede_en"]},
            "explainer": net_layer.EXPLAINER, "strands": sts}


def llms_section(docs):
    lines = ["", "## The Mot Dang net", "",
             "The sites of motdang.net strung as one net: each card's page carries the whole",
             "list, that page marked. JSON: " + BASE + "net.json", ""]
    for s in strands(docs):
        lines.append("### %s · %s" % (s["en"], s["th"]))
        for j in s["jewels"]:
            u = j["href"] if j["href"].startswith("http") else BASE + j["href"]
            lines.append("- [%s](%s): %s" % (j["en"], u, j.get("line_en", "")))
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    docs = ROOT / "docs"
    if "--inject" in sys.argv:
        n, skip = inject(docs)
        (docs / "net.json").write_text(json.dumps(net_json(docs), ensure_ascii=False, indent=1),
                                       encoding="utf-8")
        print("sitenet: %d pages carry the net; no page here: %s" % (n, ", ".join(skip)))
    else:
        for s in strands(docs):
            print(s["en"], len(s["jewels"]))
