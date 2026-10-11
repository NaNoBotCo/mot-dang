#!/usr/bin/env python3
"""/get.html — the toys, and the file each one actually is.

WO-75. Nan, 2026-09-07: "motdang.net should also be a place to download
widgets and apps. I'm not on the app store or play store... I have a ton of
toys I'd like to make available for download (some paid). We keep them on
motdang.net, and we should be able to find them. But not a lot of words."

So this layer does three things and no more:

  1. copies each toy's FILE into docs/get/ and measures it there — size,
     sha256 and version are read off the bytes that ship, never typed into
     the registry. A registry that carries its own numbers is a registry
     that goes stale silently.
  2. writes a register page whose row is: glyph, name, one line, what it
     runs on, and one button carrying either the size or the price. No
     lede, no explainer, no invitation. The install steps that a sideloaded
     .apk really does need are ONE drawer at the foot of the page, not a
     paragraph on every card.
  3. writes docs/data/downloads.json — the rows search.html adds to its own
     matcher, so a toy is findable by typing its name, and `?cat=dl` shows
     the toys and nothing else.

THE VALVES, and why each is a refusal rather than a warning:

  no file, no link   a row with neither `src` nor `open` names nothing a
                     reader can have. Held.
  priced, unpaid     `price` above zero with no `buy` would print a price
                     with nothing to tap. Held until the rail exists — the
                     rail is Nan's call, and this layer stays ignorant of
                     which one she picks: `buy` is any URL.
  draft: true        the same valve asked_layer uses. A half-packaged toy
                     renders nowhere.

Every held row is printed in the build line, so a toy that quietly stopped
shipping is visible in the log rather than merely absent from the page.

The registry is data/curated/downloads.json, hand-editable. `src` is a path
relative to the projects directory (mot-dang's parent), so a toy built in
its own repo is published from where it is built and never copied into this
one by hand.

Entry point: emit(globals_of_build), same handshake as every layer.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FLEET = ROOT.parent
REG = ROOT / "data" / "curated" / "downloads.json"

# What a row says it runs on, in the reader's two languages. Keys are the
# registry's `on` values; anything else is passed through as itself.
ON = {"android": ("แอนดรอยด์", "Android"),
      "ios": ("ไอโฟน", "iPhone"),
      "web": ("เว็บ", "in a browser"),
      "desktop": ("คอมพิวเตอร์", "desktop"),
      "print": ("พิมพ์", "print")}

CSS = """
.toys{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:12px;
  grid-template-columns:repeat(auto-fill,minmax(268px,1fr))}
.toy{background:var(--card);border:1.5px solid var(--warm-border);border-radius:16px;
  box-shadow:0 2px 0 var(--shadow);padding:14px 14px 12px;display:flex;
  flex-direction:column;gap:6px}
.toy h2{margin:0;font-size:1.05rem;line-height:1.35}
.toy .tg{font-size:1.5rem;line-height:1}
.toy .tline{margin:0;line-height:1.5}
.toy .ton{margin:0;font-size:.82rem;color:var(--mute)}
.toy .tgo{margin-top:auto;padding-top:8px}
.toy a.tbtn{display:inline-block;background:linear-gradient(180deg,var(--gold-light),var(--gold));
  color:#3a2c07;font-weight:700;text-decoration:none;padding:9px 16px;border-radius:12px;
  box-shadow:0 3px 0 #8a5f14}
.toy a.tbtn:active{transform:translateY(2px);box-shadow:0 1px 0 #8a5f14}
.toy a.topen{display:inline-block;padding:9px 2px;font-weight:600}
.toy .tsha{display:block;margin-top:6px;font-size:11.5px;color:var(--mute);word-break:break-all}
"""


def _fmt_size(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{max(1, round(n / 1e3))} kB"


def _apk_version(apk):
    """The version an .apk really carries, read from the manifest beside it.

    A version number typed into the registry is a number that goes stale the
    first time somebody rebuilds the app and forgets — and the page would then
    put a wrong version under a right fingerprint, which is worse than putting
    none. Every APK here is built by app/build_apk.py from
    <app>/android/AndroidManifest.xml, so that is where the number is read
    from. Absent, the row simply shows no version.
    """
    man = apk.parent.parent / "android" / "AndroidManifest.xml"
    if not man.exists():
        return None
    m = re.search(r'versionName="([^"]+)"', man.read_text())
    return m.group(1) if m else None


def emit(g):
    docs, page, bi, esc, att = g["DOCS"], g["page"], g["bi"], g["esc"], g["att"]
    mark, BASE = g["mark"], g["BASE"]
    if not REG.exists():
        return "no data/curated/downloads.json — get.html skipped"
    reg = json.loads(REG.read_text())
    toys = reg.get("toys") or []

    (docs / "get").mkdir(exist_ok=True)
    (docs / "data").mkdir(exist_ok=True)
    cards, rows, held, noalt, shipped_bytes = [], [], [], [], 0
    for t in toys:
        tid = t.get("id") or ""
        if not tid or t.get("draft"):
            held.append(f"{tid or '?'}:draft")
            continue
        price = t.get("price") or 0
        if price and not t.get("buy"):
            # A price with nothing to tap is worse than no row. The rail is
            # Nan's to choose; this only refuses to advertise before it exists.
            held.append(f"{tid}:priced-no-rail")
            continue

        src, size, sha = t.get("src"), None, None
        href = None
        if src:
            p = Path(src)
            if not p.is_absolute():
                p = FLEET / src
            if not p.exists():
                held.append(f"{tid}:no-file")
                continue
            blob = p.read_bytes()
            dest = docs / "get" / (tid + p.suffix)
            dest.write_bytes(blob)
            size, sha = len(blob), hashlib.sha256(blob).hexdigest()
            shipped_bytes += size
            href = f"get/{dest.name}"
            # tests/test_alt_text.py cannot see inside get/ — a toy published
            # verbatim is not a page this site wrote, and editing somebody's
            # game to pass a site check is the wrong repair. So the count is
            # made here and said out loud, where the fix is a change in the
            # toy's own repo.
            if p.suffix == ".html":
                n = sum(1 for tag in re.findall(r"<img\b[^>]*>", blob.decode(
                    "utf-8", "replace")) if "alt=" not in tag)
                if n:
                    noalt.append(f"{tid}:{n}")
        elif t.get("open"):
            href = t["open"]
        else:
            held.append(f"{tid}:nothing-to-get")
            continue

        th, en = (list(t.get("name") or []) + ["", ""])[:2]
        lth, len_ = (list(t.get("line") or []) + ["", ""])[:2]
        glyph = t.get("glyph") or "🧩"
        on = " · ".join(bi(*ON.get(k, (k, k))) for k in (t.get("on") or []))

        # A one-file HTML toy is BOTH: it runs at its address on this site, and
        # it is a file you can keep. Making the reader download an .html to
        # play it would be the worse half of that offered as the only half —
        # so the primary is Play, and the size beside it is the keeping.
        playable = bool(src) and href.endswith(".html")
        if price:
            btn = (f'<a class="tbtn" href="{att(t["buy"])}" rel="noopener">'
                   f'฿{price:,}</a>')
        elif playable:
            btn = (f'<a class="tbtn" href="{att(href)}">{bi("เล่น", "Play")}</a>'
                   f' <a class="topen" href="{att(href)}" download>⬇️ '
                   f'{esc(_fmt_size(size))}</a>')
        elif src:
            btn = (f'<a class="tbtn" href="{att(href)}" download>⬇️ '
                   f'{esc(_fmt_size(size))}</a>')
        else:
            btn = f'<a class="topen" href="{att(href)}">{bi("เปิด", "Open")} →</a>'
        more = (f' <a class="topen" href="{att(t["page"])}">{bi("รายละเอียด", "more")}</a>'
                if t.get("page") else "")
        # The version and the fingerprint are for the reader who wants to know
        # what they just took, and they are read off the bytes, so they cannot
        # be wrong. Not a sentence — a line of characters under the button.
        ver = _apk_version(p) if (src and p.suffix == ".apk") else t.get("ver")
        sha_line = (f'<span class="tsha">{esc(ver) + " · " if ver else ""}'
                    f'SHA-256 {sha[:16]}…</span>' if sha else "")
        line_html = f'<p class="tline">{bi(lth, len_)}</p>' if (lth or len_) else ""
        on_html = f'<p class="ton">{on}</p>' if on else ""
        cards.append(
            f'<li class="toy" id="{att(tid)}">'
            f'<span class="tg">{glyph}</span>'
            f'<h2>{bi(th, en)}</h2>'
            f'{line_html}{on_html}'
            f'<p class="tgo">{btn}{more}{sha_line}</p></li>')

        # `u` is the row's own address and `sh` its shelf's — the two fields
        # that let a row which is not a place ride in the same ranked list as
        # 88,000 that are. `g` is the glyph, shown before the name.
        rows.append({"id": "dl:" + tid, "n": th or en, "e": en or None,
                     "c": ["dl"], "u": f"get.html#{tid}", "sh": "get.html",
                     "g": glyph,
                     "k": " ".join(x for x in [lth, len_, t.get("k") or "",
                                               " ".join(t.get("on") or [])] if x)})

    # ONE drawer, once, at the foot — not a paragraph on every Android card.
    # An .apk from outside a store really does need the one nod explained, and
    # /app.html already walks through it for the app that has its own page.
    apk = any((t.get("src") or "").endswith(".apk") for t in toys)
    foot = mark(bi("ติดตั้งไฟล์ .apk", "Installing an .apk"),
                "กดไฟล์ที่โหลดมา เครื่องจะถามครั้งเดียวว่าอนุญาตให้ติดตั้งจากเบราว์เซอร์ไหม "
                "กดอนุญาต แล้วกดติดตั้ง — ที่ถามเพราะไฟล์มาจากมดแดงตรง ๆ ไม่ได้ผ่านสโตร์",
                "Open the file you downloaded. Android asks once whether the browser "
                "may install apps — allow it, then install. It asks because the file "
                "comes straight from Mot Dang rather than through a store.") if apk else ""

    body = (f'<h1>⬇️ {bi("ของเล่น", "Toys")} <span class="count">({len(cards)})</span></h1>'
            f'<ul class="toys">{"".join(cards)}</ul>{foot}')
    (docs / "get.html").write_text(page(
        "ของเล่น", body, 0, path="get.html",
        crumbs=f'<a href="index.html">{bi("หน้าแรก", "Home")}</a> › {bi("ของเล่น", "Toys")}',
        desc="ของเล่นมดแดง — แอปและวิดเจ็ตโหลดไปใช้ได้เลย ไม่ต้องผ่านสโตร์",
        extra_head=f"<style>{CSS}</style>"))
    (docs / "data" / "downloads.json").write_text(
        json.dumps(rows, ensure_ascii=False))
    return (f"get.html · {len(cards)} toys ({_fmt_size(shipped_bytes)} shipped)"
            + (f" · held: {', '.join(held)}" if held else "")
            + (f" · images with no alt: {', '.join(noalt)}" if noalt else ""))


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
