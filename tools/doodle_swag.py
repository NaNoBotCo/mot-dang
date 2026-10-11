#!/usr/bin/env python3
"""Print files for the doodles the front page aired (data/curated/doodle_aired.json), drawn by
the same engine at print size: assets/sites/doodles/replay.js over assets/front/doodler*.js in
headless Chrome, then laid out with Pillow. Each piece carries a QR code to its moving version,
https://motdang.net/doodles/d/?id=f-<date>-<set>[-<variant>], and its date and event.

    python3 tools/doodle_swag.py                    every aired doodle → cache/swag/
    python3 tools/doodle_swag.py 2026-10-04/market  one doodle (date/set[:variant])
    python3 tools/doodle_swag.py --only mug,tee     some products
    python3 tools/doodle_swag.py --book             the coffee-table book proof of the doodles chosen
    python3 tools/doodle_swag.py --volume 1         the book of aired doodles 1-200 (2: 201-400 …), book only

Per doodle, cache/swag/<date>_<set>[_<variant>]/:
    mug.png      2700×1050   11 oz mug wrap, 9 × 3.5 in at 300 dpi
    tee.png      3600×4800   shirt or tote front, 12 × 16 in at 300 dpi, transparent
    poster.png   4800×1600   24 × 8 in at 200 dpi
    flip.pdf     4.25 × 6.875 in pocket book: title, 48 frames (12 a second) on the right-hand
                 pages, the notes and the QR on the last page
    preview.jpg  the mug, the tee and the poster side by side, small
book.pdf: 11 × 8.5 in landscape; per doodle a full-bleed drawing, and facing it the date, the
event, the venue, the formula that moves it and the QR.

Sizes are the common print-on-demand templates (Printful, Gelato, Printify mugs and tees; Lulu
pocket and US Letter landscape books); the shop that sells them is not chosen yet. Not part
of the site build. Needs Chrome, Pillow and qrcode (pip).
"""
import base64
import io
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import qrcode

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import doodler_sheet  # noqa: E402  (its scripts() inlines skyline.js + doodler*.js)

OUT = ROOT / "cache/swag"
AIRED = ROOT / "data/curated/doodle_aired.json"
SITE = "https://motdang.net/doodles/d/?id="
FONT = "/System/Library/Fonts/Supplemental/SukhumvitSet.ttc"
PAPER, INK, RED = (242, 230, 201), (42, 26, 10), (224, 64, 42)
FLIP_FRAMES, FLIP_FPS = 48, 12


def ident(r):
    return "%s/%s%s" % (r["date"], r["set"], ":" + r["variant"] if r.get("variant") else "")


def doodle_id(r):
    """The doodle's id on /doodles/ (tools/doodle_repo.py): f-<date>-<set>[-<variant>]."""
    return "f-%s-%s%s" % (r["date"], r["set"], "-" + r["variant"] if r.get("variant") else "")


def ridge():
    """The north's skyline the band draws behind every scene (front_layer writes it from terrain_profile.json)."""
    t = json.loads((ROOT / "data/terrain_profile.json").read_text())
    return {k: t[k] for k in ("lat", "lon_a", "lon_b", "step", "tick", "ele", "read")}


def render(row, jobs):
    """jobs: [(name, css_w, css_h, scale, t_ms, fmt)] → {name: PIL.Image}, one Chrome run."""
    js = doodler_sheet.scripts() + "\n" + (ROOT / "assets/sites/doodles/replay.js").read_text()
    run = """var OUT = [];
JOBS.forEach(function (j) { var cv = document.createElement('canvas'); cv.width = Math.round(j[1] * j[3]); cv.height = Math.round(j[2] * j[3]); cv._dpr = j[3];
  try { MDREPLAY.draw(cv, ROW, j[4], RIDGE); OUT.push(j[0] + '\\t' + cv.toDataURL(j[5] === 'jpg' ? 'image/jpeg' : 'image/png', 0.9)); } catch (e) { OUT.push(j[0] + '\\tERR ' + e.message); } });
var p = document.createElement('pre'); p.id = 'out'; p.textContent = OUT.join('\\n'); document.body.appendChild(p);"""
    html = ("<!doctype html><meta charset=utf-8><body><script>%s</script><script>var RIDGE=%s,ROW=%s,JOBS=%s;%s</script>"
            % (js, json.dumps(ridge()), json.dumps(row, ensure_ascii=False), json.dumps(jobs), run))
    OUT.mkdir(parents=True, exist_ok=True)
    src = OUT / "_render.html"
    src.write_text(html)
    r = subprocess.run([doodler_sheet.CHROME, "--headless", "--disable-gpu", "--dump-dom", src.resolve().as_uri()],
                       capture_output=True, text=True, timeout=600)
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("chrome drew nothing for %s: %s" % (ident(row), r.stderr[-400:]))
    got = {}
    for line in m.group(1).split("\n"):
        name, _, data = line.partition("\t")
        if data.startswith("ERR"):
            raise SystemExit("%s %s: %s" % (ident(row), name, data))
        got[name] = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGB")
    return got


def font(px, bold=True):
    return ImageFont.truetype(FONT, int(px), index=5 if bold else 2)


def qr(url, px):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=10)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=INK, back_color=PAPER).convert("RGB").resize((px, px), Image.NEAREST)


def day(r):
    y, m, d = r["date"].split("-")
    return "%d %s %s" % (int(d), "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[int(m) - 1], y)


def hhmm(r):
    s = r.get("s") or ""
    return s[11:16] if s[11:16] not in ("", "00:00") else ""


def tag(r, w, h, scale=1.0):
    """The paper slip a piece carries: QR left, date · time, the event, its venue, motdang.net."""
    im = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(im)
    q = int(h * 0.86)
    im.paste(qr(SITE + doodle_id(r), q), (int(h * 0.07), int(h * 0.07)))
    x, y = q + int(h * 0.2), int(h * 0.1)
    f1, f2, f3 = font(h * 0.17), font(h * 0.2), font(h * 0.13, False)
    d.text((x, y), day(r) + (" · " + hhmm(r) if hhmm(r) else ""), font=f1, fill=RED)
    t = r.get("t") or r["k"]
    while d.textlength(t, font=f2) > w - x - h * 0.1 and len(t) > 8:
        t = t[:-2].rstrip() + "…" if not t.endswith("…") else t[:-3].rstrip() + "…"
    d.text((x, y + h * 0.24), t, font=f2, fill=INK)
    d.text((x, y + h * 0.52), (r.get("v") or "") , font=f3, fill=INK)
    d.text((x, y + h * 0.7), "motdang.net · มดแดง", font=f3, fill=(106, 74, 32))
    return im


def mug(r, art):
    im = art["mug"].copy()
    t = tag(r, 900, 260)
    im.paste(t, (im.width - t.width - 60, 50))   # in the sky, clear of the people
    return im


def tee(r, art):
    W, H = 3600, 4800
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = art["tee"]
    pad = 40
    frame = Image.new("RGBA", (a.width + 2 * pad, a.height + 2 * pad), PAPER + (255,))
    frame.paste(a, (pad, pad))
    mask = Image.new("L", frame.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=90, fill=255)
    im.paste(frame, ((W - frame.width) // 2, 200), mask)
    t = tag(r, 2400, 520).convert("RGBA")
    m2 = Image.new("L", t.size, 0)
    ImageDraw.Draw(m2).rounded_rectangle((0, 0, t.width - 1, t.height - 1), radius=60, fill=255)
    im.paste(t, ((W - t.width) // 2, 200 + frame.height + 120), m2)
    return im


def poster(r, art):
    im = art["poster"].copy()
    t = tag(r, 1300, 340)
    im.paste(t, (im.width - t.width - 80, 70))
    return im


def wrap(d, x, y, text, f, fill, width, lead):
    """Words onto lines no wider than width; returns the y under the last line."""
    line = ""
    for w in text.split():
        if line and d.textlength(line + " " + w, font=f) > width:
            d.text((x, y), line, font=f, fill=fill)
            y, line = y + lead, w
        else:
            line = (line + " " + w).strip()
    if line:
        d.text((x, y), line, font=f, fill=fill)
        y += lead
    return y


def notes(r, how):
    """Plain lines for the book and the flip book's last page: when, what, where, how."""
    out = [day(r) + (" · " + hhmm(r) if hhmm(r) else ""), r.get("t") or r["k"]]
    if r.get("v"):
        out.append(r["v"])
    out.append("drawn for this event on the motdang.net front page that day")
    if how:
        out.append("moves by  " + how)
    out.append("%s%s · version %s" % (r["set"], " · " + r["variant"].replace("-", " ") if r.get("variant") else "", r.get("version", 1)))
    return out


def plain(how):
    h = re.sub(r"<br\s*/?>", "   ", how or "")
    h = re.sub(r"<sup>(.*?)</sup>", r"^\1", h)
    return re.sub(r"<[^>]+>", "", h)


def how_of(row):
    """doodler.js math(set, seed), the formula under the drawing on /sites/doodles/."""
    js = doodler_sheet.scripts() + "\n" + (ROOT / "assets/sites/doodles/replay.js").read_text()
    src = OUT / "_how.html"
    src.write_text("<!doctype html><meta charset=utf-8><body><script>%s</script><script>var p=document.createElement('pre');p.id='o';p.textContent=MDREPLAY.how(%s);document.body.appendChild(p);</script>"
                   % (js, json.dumps(row)))
    r = subprocess.run([doodler_sheet.CHROME, "--headless", "--disable-gpu", "--dump-dom", src.resolve().as_uri()], capture_output=True, text=True, timeout=120)
    m = re.search(r'<pre id="o">(.*?)</pre>', r.stdout, re.S)
    import html as H
    return plain(H.unescape(m.group(1))) if m else ""


def flip(r, frames, how, path):
    """Pocket book 4.25 × 6.875 in at 300 dpi: a frame on each right-hand page near the fore-edge,
    the left-hand pages blank, so the drawing moves under the thumb."""
    W, H = 1275, 2063
    pages = []

    def page():
        return Image.new("RGB", (W, H), PAPER)
    p = page()
    d = ImageDraw.Draw(p)
    d.text((110, 260), "มดแดง · Mot Dang", font=font(70), fill=RED)
    y = 420
    for i, line in enumerate(notes(r, how)[:3]):
        y = wrap(d, 110, y, line, font(64 if i < 2 else 50, i < 2), RED if i == 0 else INK, W - 220, 92 if i < 2 else 74) + 30
    d.text((110, H - 300), "flip from the back, thumb on the corner", font=font(44, False), fill=(106, 74, 32))
    pages += [p, page()]
    for f in frames:
        p = page()
        fw = W - 150
        fr = f.resize((fw, int(f.height * fw / f.width)))
        p.paste(fr, (W - fw - 40, H - fr.height - 160))
        pages += [p, page()]
    p = page()
    d = ImageDraw.Draw(p)
    p.paste(qr(SITE + doodle_id(r), 700), ((W - 700) // 2, 300))
    y = 1100
    for i, line in enumerate(notes(r, how)):
        y = wrap(d, 110, y, line, font(44, i < 2), RED if i == 0 else INK, W - 220, 62) + 14
    pages.append(p)
    pages[0].save(path, "PDF", resolution=300, save_all=True, append_images=pages[1:])
    return len(pages)


def preview(dirp):
    ims = [Image.open(dirp / n).convert("RGBA") for n in ("mug.png", "tee.png", "poster.png")]
    h = 360
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    out = Image.new("RGB", (sum(i.width for i in ims) + 40 * (len(ims) + 1), h + 80), (17, 21, 28))
    x = 40
    for i in ims:
        out.paste(i, (x, 40), i)
        x += i.width + 40
    out.save(dirp / "preview.jpg", quality=82)


def book(rows, hows, arts, path):
    """US Letter landscape at 300 dpi: per doodle the drawing on the right page, notes + QR on the left."""
    W, H = 3300, 2550
    pages = []
    for r in rows:
        left = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(left)
        y = 420
        for i, line in enumerate(notes(r, hows[ident(r)])):
            y = wrap(d, 300, y, line, font(130 if i == 1 else 72, i < 2), RED if i == 0 else INK, W - 600, 160 if i == 1 else 110) + 40
        left.paste(qr(SITE + doodle_id(r), 600), (300, H - 900))
        d.text((300, H - 260), "scan: the drawing moves", font=font(56, False), fill=(106, 74, 32))
        a = arts[ident(r)].resize((W, int(arts[ident(r)].height * W / arts[ident(r)].width)))
        right = Image.new("RGB", (W, H), (18, 19, 48))
        right.paste(a, (0, (H - a.height) // 2))
        pages += [left, right]
    pages[0].save(path, "PDF", resolution=300, save_all=True, append_images=pages[1:])
    return len(pages)


def main(a):
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else {"mug", "tee", "poster", "flip"}
    want = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--only", "--volume"))]
    seen, rows = set(), []
    for r in json.loads(AIRED.read_text())["aired"]:
        if r.get("set") and ident(r) not in seen and (not want or ident(r) in want):
            seen.add(ident(r))
            rows.append(r)
    if "--volume" in a:
        v = int(a[a.index("--volume") + 1])
        rows = rows[200 * (v - 1):200 * v]
        a, only = a + ["--book"], set()
        print("volume %d: %d of 200 doodles" % (v, len(rows)))
    if not rows:
        raise SystemExit("no aired doodle matches %s" % want)
    hows, books = {}, {}
    for r in rows:
        dirp = OUT / ident(r).replace("/", "_").replace(":", "_")
        dirp.mkdir(parents=True, exist_ok=True)
        jobs = []
        if "mug" in only:
            jobs.append(("mug", 900, 350, 3, 4200, "png"))
        if "tee" in only:
            jobs.append(("tee", 1100, 484, 3, 4200, "png"))
        if "poster" in only:
            jobs.append(("poster", 1600, 533.33, 3, 4200, "png"))
        if "--book" in a:
            jobs.append(("book", 1100, 850, 3, 4200, "jpg"))
        if "flip" in only:
            jobs += [("f%02d" % i, 600, 264, 2, 2000 + i * 1000 / FLIP_FPS, "jpg") for i in range(FLIP_FRAMES)]
        art = render(r, jobs)
        hows[ident(r)] = how_of(r)
        made = []
        for name, fn in (("mug", mug), ("tee", tee), ("poster", poster)):
            if name in only:
                fn(r, art).save(dirp / (name + ".png"), optimize=True)
                made.append(name)
        if "flip" in only:
            n = flip(r, [art["f%02d" % i] for i in range(FLIP_FRAMES)], hows[ident(r)], dirp / "flip.pdf")
            made.append("flip(%dpp)" % n)
        if {"mug", "tee", "poster"} <= only:
            preview(dirp)
        if "book" in art:
            books[ident(r)] = art["book"]
        print(ident(r), "→", dirp.relative_to(ROOT), " ".join(made))
    if "--book" in a:
        p = OUT / ("book-v%s.pdf" % a[a.index("--volume") + 1] if "--volume" in a else "book.pdf")
        print("book →", p.relative_to(ROOT), book(rows, hows, books, p), "pages")


if __name__ == "__main__":
    main(sys.argv[1:])
