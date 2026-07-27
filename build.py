#!/usr/bin/env python3
"""Mot Dang (มดแดง) — static site builder. data/canonical/*.json -> docs/ (GitHub Pages).

Thai-first, 1997 directory genre: Term (count) links, hierarchy in place,
no empty categories shown. EN is a display layer toggled client-side.
Zero external requests on the published pages; OSM attribution in the footer.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
BUILD_DATE = "2026-07-27"

CFG = json.loads((ROOT / "data" / "categories.json").read_text())
CATS = {c["key"]: c for c in CFG["categories"]}
CAT_ORDER = [c["key"] for c in CFG["categories"]]
PROVINCES = CFG["provinces"]

CSS = """
:root{--paper:#FBF6EE;--ink:#2A1E16;--ant:#C2401C;--ant-dark:#8F2E13;
--link:#1F3FBF;--visited:#6B3FA0;--soft:#EADFCE;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:19px/1.65 -apple-system,"Thonburi","Sarabun","Noto Sans Thai",sans-serif;}
main{max-width:880px;margin:0 auto;padding:1rem 1.2rem 4rem}
a{color:var(--link)} a:visited{color:var(--visited)}
a:hover{text-decoration-thickness:3px;text-decoration-color:var(--ant)}
header.site{border-bottom:4px double var(--ant);padding:.8rem 0 .6rem;margin-bottom:1rem;
display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap}
.logo{font-size:2rem;font-weight:800;color:var(--ant);text-decoration:none;letter-spacing:.5px}
.logo:visited{color:var(--ant)} .logo .ant{display:inline-block;transition:transform .35s}
.logo:hover .ant{transform:rotate(-20deg) translateY(-3px)}
.tagline{color:var(--ant-dark);font-size:.95rem}
.langbtn{margin-left:auto;border:2px solid var(--ant);background:none;color:var(--ant);
border-radius:999px;padding:.15rem .8rem;font:inherit;font-size:.9rem;cursor:pointer}
.langbtn:hover{background:var(--ant);color:var(--paper)}
.en{display:none} body.lang-en .en{display:inline} body.lang-en .th{display:none}
h1{font-size:1.6rem;margin:.4rem 0} h2{font-size:1.25rem;border-bottom:2px solid var(--soft);
padding-bottom:.2rem;margin-top:1.6rem}
ul.dir{list-style:none;padding:0;column-width:22rem;column-gap:2.5rem}
ul.dir li{margin:.28rem 0;break-inside:avoid}
.count{color:var(--ant-dark);font-size:.9rem}
.badge{background:var(--soft);border-radius:.5rem;padding:0 .5rem;font-size:.8rem;white-space:nowrap}
.badge.pin{background:#F6D9CE;color:var(--ant-dark)}
.grow{color:var(--ant-dark);font-size:.9rem;font-style:italic}
.featured{border:2px solid var(--ant);border-radius:.8rem;padding:.9rem 1.1rem;margin:1rem 0;
background:#fff;box-shadow:3px 3px 0 var(--soft);transition:transform .18s,box-shadow .18s}
.featured:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--soft)}
.featured .star{color:var(--ant)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1.2rem}
dt{color:var(--ant-dark);font-weight:600} dd{margin:0;overflow-wrap:anywhere}
.prov{color:var(--ant-dark);font-size:.85rem;border-top:1px dashed var(--soft);
margin-top:1.6rem;padding-top:.5rem}
footer{border-top:4px double var(--ant);margin-top:3rem;padding-top:.7rem;font-size:.85rem;
color:var(--ant-dark);position:relative;overflow:hidden}
.crumbs{font-size:.9rem;margin-bottom:.4rem}
#scurry{position:absolute;bottom:2px;left:-2rem;font-size:1.1rem;pointer-events:none}
#scurry.go{animation:scurry 3.5s linear}
@keyframes scurry{from{left:-2rem}to{left:105%}}
@media(max-width:600px){body{font-size:18px} ul.dir{column-width:auto}}
"""

JS = """
const B=document.body,btn=document.querySelector('.langbtn');
if(localStorage.getItem('md-lang')==='en')B.classList.add('lang-en');
btn&&btn.addEventListener('click',()=>{B.classList.toggle('lang-en');
localStorage.setItem('md-lang',B.classList.contains('lang-en')?'en':'th');});
const logo=document.querySelector('.logo .ant'),ant=document.getElementById('scurry');
logo&&ant&&logo.closest('.logo').addEventListener('click',e=>{
if(e.detail&&location.pathname.endsWith('/')&&!location.pathname.match(/\\/(cm|cr)\\//)){}
ant.classList.remove('go');void ant.offsetWidth;ant.classList.add('go');});
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bi(th, en):
    """Bilingual span pair — Thai canonical, English display layer."""
    return f'<span class="th">{esc(th)}</span><span class="en">{esc(en)}</span>'


def page(title, body, depth, crumbs=""):
    r = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · มดแดง</title>
<link rel="stylesheet" href="{r}style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐜</text></svg>">
</head><body>
<main>
<header class="site">
  <a class="logo" href="{r}index.html"><span class="ant">🐜</span> มดแดง</a>
  <span class="tagline">{bi("รู้ทุกซอย เหมือนมดแดง", "knows every soi, like a red ant")}</span>
  <button class="langbtn">TH / EN</button>
</header>
{f'<nav class="crumbs">{crumbs}</nav>' if crumbs else ''}
{body}
<footer>
  {bi("สร้างจากข้อมูลเปิดและการเดินเก็บจริง · ปรับปรุง " + BUILD_DATE,
      "Built from open data and shoe-leather · updated " + BUILD_DATE)}<br>
  © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> (ODbL)
  <span id="scurry">🐜</span>
</footer>
</main>
<script src="{r}md.js"></script>
</body></html>"""


def load():
    data = {}
    for p in PROVINCES:
        data[p["key"]] = json.loads((ROOT / "data" / "canonical" / f"{p['key']}.json").read_text())
    return data


def cat_counts(records):
    counts = {}
    for r in records:
        for c in r["cat"]:
            counts[c] = counts.get(c, 0) + 1
    return counts


def name_of(r):
    return r.get("name") or r.get("nameEn") or r["id"]


def entry_li(r, prov, depth):
    href = "../" * depth + f"{prov}/p/{r['id']}.html"
    star = '<span class="star">★</span> ' if r.get("featured") else ""
    pin = ' <span class="badge pin">' + bi("รอปักหมุด", "pin wanted") + "</span>" \
        if r.get("geoPrecision") == "needs-pin" else ""
    return f'<li>{star}<a href="{href}">{esc(name_of(r))}</a>{pin}</li>'


def geojson(records):
    feats = []
    for r in records:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
            "properties": {"id": r["id"], "name": name_of(r), "cat": r["cat"],
                           "province": r["province"]},
        })
    return {"type": "FeatureCollection", "features": feats}


def detail_page(r, prov_cfg):
    prov, rows = r["province"], []
    cats = " · ".join(
        f'<a href="../{c}/index.html">{bi(CATS[c]["th"], CATS[c]["en"])}</a>' for c in r["cat"])
    rows.append(f"<dt>{bi('หมวด', 'Category')}</dt><dd>{cats}</dd>")
    if r.get("nameEn") and r.get("nameEn") != r.get("name"):
        rows.append(f"<dt>{bi('ชื่ออังกฤษ', 'English name')}</dt><dd>{esc(r['nameEn'])}</dd>")
    if r.get("address"):
        rows.append(f"<dt>{bi('ที่อยู่', 'Address')}</dt><dd>{esc(r['address'])}</dd>")
    if r.get("phone"):
        rows.append(f"<dt>{bi('โทร', 'Phone')}</dt><dd><a href=\"tel:{esc(r['phone'])}\">{esc(r['phone'])}</a></dd>")
    if r.get("website"):
        rows.append(f"<dt>{bi('เว็บ', 'Website')}</dt><dd><a href=\"{esc(r['website'])}\" rel=\"nofollow\">{esc(r['website'])}</a></dd>")
    if r.get("hours"):
        rows.append(f"<dt>{bi('เวลาเปิด', 'Hours')}</dt><dd>{esc(r['hours'])}</dd>")
    if r.get("lat") is not None:
        osm = f"https://www.openstreetmap.org/?mlat={r['lat']}&mlon={r['lng']}#map=18/{r['lat']}/{r['lng']}"
        gmap = f"https://maps.google.com/?q={r['lat']},{r['lng']}"
        approx = " " + bi("(โดยประมาณ)", "(approximate)") if r["geoPrecision"] == "approx" else ""
        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd><a href="{osm}">OpenStreetMap</a> · '
                    f'<a href="{gmap}">Google Maps</a>{approx}</dd>')
    else:
        rows.append(f'<dt>{bi("แผนที่", "Map")}</dt><dd><span class="badge pin">'
                    + bi("รอปักหมุด — ช่วยบอกพิกัดได้", "pin wanted — tell us where!") + "</span></dd>")
    blurb = ""
    if r.get("blurb_th") or r.get("blurb_en"):
        blurb = f'<p class="featured"><span class="star">★</span> {bi(r.get("blurb_th") or "", r.get("blurb_en") or "")}</p>'
    src = (r.get("sources") or [{}])[0]
    prov_line = {"osm": bi("ข้อมูลจาก OpenStreetMap", "Data from OpenStreetMap"),
                 "field": bi("ข้อมูลเก็บภาคสนาม", "Field-collected data"),
                 "curated": bi("ข้อมูลคัดสรรโดยทีมมดแดง", "Curated by the Mot Dang team")}.get(
        src.get("type"), bi("ข้อมูลเปิด", "Open data"))
    fetched = f" · {esc(src['fetched'])}" if src.get("fetched") else ""
    crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
              f'<a href="../index.html">{bi(prov_cfg["th"], prov_cfg["en"])}</a> › {esc(name_of(r))}')
    body = f"""<h1>{esc(name_of(r))}</h1>
{blurb}
<dl>{''.join(rows)}</dl>
<p class="prov">{prov_line}{fetched}</p>"""
    return page(name_of(r), body, depth=2, crumbs=crumbs)


def build():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    (DOCS / ".nojekyll").write_text("")
    (DOCS / "style.css").write_text(CSS)
    (DOCS / "md.js").write_text(JS)
    (DOCS / "data").mkdir()

    data = load()
    home_sections = []

    for p in PROVINCES:
        key, records = p["key"], data[p["key"]]
        counts = cat_counts(records)
        live_cats = [c for c in CAT_ORDER if counts.get(c)]
        pdir = DOCS / key
        (pdir / "p").mkdir(parents=True)

        grow = f' <span class="grow">{bi("— กำลังเติบโต", "— growing")}</span>' \
            if p["mode"] == "wireframe" else ""
        cat_links = "".join(
            f'<li><a href="{key}/{c}/index.html">{bi(CATS[c]["th"], CATS[c]["en"])}</a> '
            f'<span class="count">({counts[c]:,})</span></li>'
            for c in live_cats)
        home_sections.append(
            f'<h2><a href="{key}/index.html">{bi(p["th"], p["en"])}</a> '
            f'<span class="count">({len(records):,})</span>{grow}</h2>'
            f'<ul class="dir">{cat_links}</ul>')

        featured = [r for r in records if r.get("featured")]
        feat_html = ""
        if featured:
            cards = "".join(
                f'<div class="featured"><span class="star">★</span> '
                f'<a href="p/{r["id"]}.html"><strong>{esc(name_of(r))}</strong></a><br>'
                f'{bi(r.get("blurb_th") or "", r.get("blurb_en") or "")}</div>'
                for r in featured)
            feat_html = f'<h2>{bi("ที่น่าไป", "Places to visit")}</h2>{cards}'

        prov_cat_links = "".join(
            f'<li><a href="{c}/index.html">{bi(CATS[c]["th"], CATS[c]["en"])}</a> '
            f'<span class="count">({counts[c]:,})</span></li>'
            for c in live_cats)
        crumbs = f'<a href="../index.html">{bi("หน้าแรก", "Home")}</a> › {bi(p["th"], p["en"])}'
        (pdir / "index.html").write_text(page(
            p["th"],
            f'<h1>{bi(p["th"], p["en"])} <span class="count">({len(records):,})</span>{grow}</h1>'
            f'{feat_html}<h2>{bi("หมวด", "Categories")}</h2><ul class="dir">{prov_cat_links}</ul>',
            depth=1, crumbs=crumbs))

        for c in live_cats:
            in_cat = sorted([r for r in records if c in r["cat"]],
                            key=lambda r: (not r.get("featured"), name_of(r)))
            (pdir / c).mkdir()
            lis = "".join(entry_li(r, key, depth=2).replace(f"{key}/p/", "../p/") for r in in_cat)
            gj = geojson(in_cat)
            gj_name = f"{key}-{c}.geojson"
            (DOCS / "data" / gj_name).write_text(json.dumps(gj, ensure_ascii=False))
            crumbs = (f'<a href="../../index.html">{bi("หน้าแรก", "Home")}</a> › '
                      f'<a href="../index.html">{bi(p["th"], p["en"])}</a> › {bi(CATS[c]["th"], CATS[c]["en"])}')
            (pdir / c / "index.html").write_text(page(
                CATS[c]["th"],
                f'<h1>{bi(CATS[c]["th"], CATS[c]["en"])} '
                f'<span class="count">({len(in_cat):,})</span></h1>'
                f'<ul class="dir">{lis}</ul>'
                f'<p class="prov"><a href="../../data/{gj_name}">⬇ GeoJSON</a> '
                f'({len(gj["features"]):,} {bi("จุด", "points")})</p>',
                depth=2, crumbs=crumbs))

        for r in records:
            (pdir / "p" / f"{r['id']}.html").write_text(detail_page(r, p))

    intro_th = ("สารบัญเมืองเชียงใหม่และเชียงราย — วัด ร้าน หมอ ตลาด และของดีทุกซอย "
                "เรียงเป็นหมวดให้เปิดหาได้เหมือนสมุดหน้าเมือง")
    intro_en = ("A city directory for Chiang Mai and Chiang Rai — wats, shops, doctors, "
                "markets, and the good things down every soi, sorted the old way.")
    intro = f"<p>{bi(intro_th, intro_en)}</p>"
    (DOCS / "index.html").write_text(page("มดแดง", intro + "".join(home_sections), depth=0))

    n_pages = sum(1 for _ in DOCS.rglob("*.html"))
    print(f"built {n_pages:,} pages -> docs/")


if __name__ == "__main__":
    build()
