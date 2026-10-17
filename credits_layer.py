#!/usr/bin/env python3
"""WO-110. Builds the credits page from credits.json. Stdlib only, no network.

    python3 credits_layer.py build --out /tmp/credits.html     # a whole document for review
    python3 credits_layer.py check                             # data/credits.json
    python3 credits_layer.py add --name "…" --kind bug --month 2026-10 --ref ab12cd34

A row is listed when it carries the consent version the form stamped (`consent`), a name that
passes the same test the Worker applies, a kind from KINDS and a month. A row that fails is
named by `check` and left off the page.

build.py calls `rows()` and `body(rows, bi, esc)` and places the body inside page(), which
gives it the site header, footer and language switch. `build` here writes a whole document for review.
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CREDITS_JSON = os.path.join(ROOT, "data", "credits.json")
CONSENT_VERSIONS = {"2026-10-11"}          # the wording versions the form has carried

KINDS = {
    "fix": ("แก้ข้อมูลสถานที่", "Fixed a place"),
    "add": ("เพิ่มสถานที่", "Added a place"),
    "photo": ("ให้รูปสถานที่", "Gave a photo of a place"),
    "bug": ("แจ้งข้อผิดพลาดของเว็บ", "Reported a bug"),
}
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
REF_RE = re.compile(r"^[0-9a-f]{8}$")
# the pattern accept_suggestion.SITE_PATH uses: a path from the site root, ours only
PAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]
MONTHS_TH = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม",
             "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def name_problem(name):
    """Why a name cannot be shown, or None. The Worker's cleanCredit applies the same test."""
    if not isinstance(name, str):
        return "name is not text"
    n = " ".join(name.split())
    if n != name:
        return "name has stray spaces or line breaks"
    if not 2 <= len(n) <= 60:
        return "name is not 2 to 60 characters"
    if re.search(r"[\u0000-\u001f\u007f<>]", n):
        return "name has control characters or angle brackets"
    if re.search(r"@|://|www\.", n, re.I):
        return "name looks like an address"
    if re.search(r"(?:\d[\s().+-]*){6,}", n):
        return "name looks like a phone number"
    return None


def row_problems(r):
    out = []
    if not isinstance(r, dict):
        return ["row is not an object"]
    p = name_problem(r.get("name"))
    if p:
        out.append(p)
    if r.get("kind") not in KINDS:
        out.append("kind %r is not one of %s" % (r.get("kind"), "/".join(KINDS)))
    if not MONTH_RE.match(str(r.get("month", ""))):
        out.append("month is not YYYY-MM")
    if str(r.get("consent", "")) not in CONSENT_VERSIONS:
        out.append("consent %r is not a wording version the form carried" % (r.get("consent"),))
    if "ref" in r and not REF_RE.match(str(r["ref"])):
        out.append("ref is not 8 hex characters")
    if r.get("page") and (not PAGE_RE.match(str(r["page"])) or ".." in str(r["page"])):
        out.append("page is not a path on this site")
    if "fix" in r and not (isinstance(r["fix"], int) and r["fix"] >= 0):
        out.append("fix is not a row number")
    return out


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as err:
        raise SystemExit("%s: %s" % (path, err))
    if not isinstance(doc, dict) or not isinstance(doc.get("credits"), list):
        raise SystemExit("%s: expected an object with a credits list" % path)
    return doc


def listed(doc):
    """(rows that pass, [(index, problems)] for those that do not)."""
    good, bad = [], []
    for i, r in enumerate(doc["credits"]):
        p = row_problems(r)
        (bad.append((i, p)) if p else good.append(r))
    good.sort(key=lambda r: r["name"].casefold())
    good.sort(key=lambda r: r["month"], reverse=True)
    return good, bad


def default_bi(th, en):
    return ('<span class="bi"><span class="th" lang="th">%s</span>'
            '<span class="en" lang="en"><span class="th" lang="th"> · </span>%s</span></span>' % (th, en))


def month_bi(m, bi):
    y, mo = int(m[:4]), int(m[5:7])
    return bi("%s %d" % (MONTHS_TH[mo - 1], y + 543), "%s %d" % (MONTHS_EN[mo - 1], y))


CSS = """
.cr-lede{font-size:1.06rem;line-height:1.65;max-width:64ch}
.cr-table{border-collapse:collapse;width:100%;max-width:46rem;margin:1.2rem 0}
.cr-table th,.cr-table td{text-align:left;padding:.55rem .7rem;border-bottom:1px solid var(--line,#e4d9cd);vertical-align:top}
.cr-table th{font-weight:600;font-size:.88rem;color:var(--muted,#8a7a62)}
.cr-name{font-weight:600}
.cr-empty{padding:1.1rem 1rem;border:1px dashed var(--line,#e4d9cd);border-radius:.85rem;max-width:46rem;color:var(--muted,#8a7a62)}
.cr-note{color:var(--muted,#8a7a62);font-size:.92rem;line-height:1.6;max-width:66ch}
.cr-sample{border:1px solid var(--line,#e4d9cd);border-radius:.6rem;padding:.5rem .8rem;max-width:46rem;background:var(--tint,#fbf6f0)}
@media(max-width:640px){.cr-table th:nth-child(4),.cr-table td:nth-child(4){display:none}}
"""


def body(rows, bi=default_bi, esc=html.escape, sample=False):
    out = ['<h1>%s</h1>' % bi("เครดิต", "Credits"),
           '<p class="cr-lede">%s</p>' % bi(
               "คนที่แจ้งข้อผิดพลาดหรือช่วยแก้ข้อมูลสถานที่ และติ๊กให้ใส่ชื่อ",
               "People who reported a bug or fixed a place and ticked the box to be named.")]
    if sample:
        out.append('<p class="cr-sample">%s</p>' % bi(
            "ตัวอย่างหน้า รายชื่อด้านล่างเป็นชื่อสมมติ",
            "Sample of the page. The names below are invented."))
    if not rows:
        out.append('<p class="cr-empty">%s</p>' % bi("ยังไม่มีรายชื่อ", "No names yet."))
    else:
        trs = []
        for r in rows:
            kth, ken = KINDS[r["kind"]]
            link = ""
            if r.get("page"):
                link = '<a href="%s">↗</a>' % esc(r["page"], quote=True)
            trs.append('<tr><td class="cr-name">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                esc(r["name"]), bi(kth, ken), month_bi(r["month"], bi), link))
        out.append('<table class="cr-table"><thead><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr></thead>'
                   '<tbody>%s</tbody></table>' % (
                       bi("ชื่อ", "Name"), bi("ช่วยเรื่อง", "Help"), bi("เดือน", "Month"),
                       bi("หน้า", "Page"), "".join(trs)))
    out.append('<h2>%s</h2>' % bi("ชื่อบนหน้านี้", "Names on this page"))
    out.append('<p class="cr-note">%s</p>' % bi(
        "ฟอร์มแจ้งมดมีช่องติ๊ก “ใส่ชื่อฉันในหน้าเครดิต” และช่องพิมพ์ชื่อที่จะแสดง "
        "ชื่อขึ้นหน้านี้เมื่อกรอกทั้งสองช่อง และเรื่องที่แจ้งถูกนำไปใช้แล้ว",
        "The tell-the-ants form has a tick, “Name me on the credits page”, and a box for the name to show. "
        "A name appears here when both are filled and the report has been used."))
    out.append('<p class="cr-note">%s</p>' % bi(
        "แต่ละแถวแสดงชื่อ ประเภทเรื่อง เดือน และลิงก์ไปหน้าที่เกี่ยวข้อง",
        "A row shows the name, the kind of help, the month and a link to the page it concerns."))
    out.append('<p class="cr-note">%s</p>' % bi(
        "เปลี่ยนหรือถอนชื่อได้ทางฟอร์มแจ้งมด พร้อมรหัสอ้างอิงจากข้อความขอบคุณ",
        "A name is changed or taken off through the tell-the-ants form, with the reference code from the thank-you message."))
    out.append('<p class="cr-note"><a href="suggest.html?kind=other">%s</a> · <a href="fixed.html">%s</a></p>' % (
        bi("ฟอร์มแจ้งมด", "Tell the ants"), bi("บันทึกแก้ตามแจ้ง", "The fix log")))
    return "\n".join(out)


def document(rows, css_href="style.css", sample=False):
    robots = "noindex" if sample else "index,follow"
    title = "เครดิต · Credits · มดแดง Mot Dang"
    return """<!DOCTYPE html>
<html lang="th" class="lang-both" translate="no" data-root="" data-icons="icons.svg"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google" content="notranslate">
<title>%(title)s</title>
<meta name="description" content="เครดิต · Credits: people who reported a bug or fixed a place and ticked the box to be named">
<meta name="robots" content="%(robots)s">
<link rel="canonical" href="https://motdang.net/credits.html">
<link rel="stylesheet" href="%(css)s">
<script>try{var _r=document.documentElement,_l=localStorage.getItem('md-lang');if(_l!=='th'&&_l!=='en')_l=/^th/i.test(navigator.language||'')?'th':'en';if(_l==='en'||_l==='th'){_r.classList.remove('lang-both');_r.classList.add('lang-'+_l)}if(_l==='en')_r.lang='en'}catch(e){}</script>
<style>%(cssinline)s</style>
</head><body>
<main>
<p><a href="index.html">%(home)s</a></p>
%(body)s
</main>
</body></html>
""" % {"title": title, "robots": robots, "css": html.escape(css_href, quote=True), "cssinline": CSS,
       "home": default_bi("มดแดง", "Mot Dang"), "body": body(rows, sample=sample)}


def cmd_build(a):
    doc = load(a.inp)
    rows, bad = listed(doc)
    for i, p in bad:
        print("left off: row %d: %s" % (i, "; ".join(p)), file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(document(rows, a.css, a.sample))
    print("%s: %d listed, %d left off" % (a.out, len(rows), len(bad)))
    return 0


def cmd_check(a):
    doc = load(a.inp)
    rows, bad = listed(doc)
    for i, p in bad:
        print("row %d: %s" % (i, "; ".join(p)))
    print("%d listed, %d fail" % (len(rows), len(bad)))
    return 1 if bad else 0


def cmd_add(a):
    row = {"name": a.name, "kind": a.kind, "month": a.month, "consent": a.consent}
    if a.ref:
        row["ref"] = a.ref
    if a.page:
        row["page"] = a.page
    if a.fix is not None:
        row["fix"] = a.fix
    p = row_problems(row)
    if p:
        print("not added: " + "; ".join(p), file=sys.stderr)
        return 1
    doc = load(a.inp)
    doc["credits"].append(row)
    tmp = a.inp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, a.inp)
    print("added row %d" % (len(doc["credits"]) - 1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "check", "add"):
        s = sub.add_parser(name)
        s.add_argument("--in", dest="inp", default=CREDITS_JSON)
    b = sub.choices["build"]
    b.add_argument("--out", default=os.path.join(ROOT, "docs", "credits.html"))
    b.add_argument("--css", default="style.css", help="href of the site stylesheet")
    b.add_argument("--sample", action="store_true", help="mark the page as a sample, noindex")
    d = sub.choices["add"]
    d.add_argument("--name", required=True)
    d.add_argument("--kind", required=True, choices=sorted(KINDS))
    d.add_argument("--month", required=True)
    d.add_argument("--consent", default=sorted(CONSENT_VERSIONS)[-1],
                   help="the wording version the reader ticked (from the queue row's credit.v)")
    d.add_argument("--ref")
    d.add_argument("--page")
    d.add_argument("--fix", type=int)
    a = ap.parse_args(argv)
    return {"build": cmd_build, "check": cmd_check, "add": cmd_add}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
