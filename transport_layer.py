#!/usr/bin/env python3
"""รถ-เดินทาง — /transport.html: how the city actually moves. WO-13.

THE GAP THIS FILLS (measured 2026-08-19, notes/transport-proposal-2026-08-19.md).
The transport shelf held 536 records of which 435 were petrol pumps, and the
one thing on the site that could answer a journey — the flights board — was
reachable from nowhere. Worse, the shelf could not tell a train from a bus:
`import_overpass.classify()` folded bus terminal, railway station and public-
transport station into ONE sub called "station" and dropped `amenity=taxi`
entirely, so the Chiang Mai railway station sat under ช among the songthaew
stops and five taxi ranks — one with a phone — never reached the catalogue at
all. The tags had been on disk since the first crawl. WO-13 split them
(train · bus · songthaew · taxi · funicular · pier) and this page is where the
split becomes an answer.

WHAT THIS PAGE WILL NOT DO. It states no fare, no departure time and no
journey duration, because this catalogue holds none of those and a directory
that guesses at a bus time strands somebody at a bus stop. The provincial
register lists ROUTES — where a bus is licensed to go — and that is exactly
what is printed, in the register's own words, with its year. Where a reader
needs a timetable the page says who has one and links them.

Entry points:
    band(g, cat_key)   the porch on the transport shelf (build.py calls it)
    emit(g, data)      /transport.html, before the sitemap
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUS = ROOT / "data" / "bus_routes.json"

SUB_TH = {"train": "สถานีรถไฟ", "bus": "สถานีขนส่ง-ท่ารถ", "songthaew": "รถแดง-สองแถว",
          "taxi": "แท็กซี่-คิวรถ", "funicular": "รถรางขึ้นดอย", "pier": "ท่าเรือ",
          "airport": "สนามบิน", "rental": "เช่ารถ-มอเตอร์ไซค์"}
SUB_EN = {"train": "Train stations", "bus": "Bus terminals", "songthaew": "Rot daeng & songthaew",
          "taxi": "Taxi ranks", "funicular": "The Doi Suthep funicular", "pier": "Piers",
          "airport": "Airports", "rental": "Car & bike rental"}
GLYPH = {"train": "🚉", "bus": "🚌", "songthaew": "🚐", "taxi": "🚕",
         "funicular": "🚡", "pier": "⛴", "airport": "✈️", "rental": "🛵"}
# A songthaew stop's whole content is its name: mappers wrote the destination
# there because OSM has no field for it. This pulls the destination out for
# the board, and prints the name as written when it cannot.
DEST = re.compile(r"(?:to|ไป|go to|for)\s+([A-Za-z฀-๿][^,()]{2,32})", re.I)


def _by_sub(data, prov):
    out = {}
    for r in data[prov]:
        if "transport" not in (r.get("cat") or []):
            continue
        for s in (r.get("sub") or []):
            out.setdefault(s, []).append(r)
    return out


def band(g, cat_key):
    """One line on the transport shelf pointing at the board — the same porch
    the muay thai and cooking shelves have."""
    if cat_key != "transport":
        return ""
    bi = g["bi"]
    return ('<p class="bandline">🚌 '
            + bi("เส้นทางรถเมล์ รถไฟ รถแดง แท็กซี่ และเที่ยวบิน รวมไว้ที่เดียว",
                 "Bus routes, trains, red trucks, taxi ranks and who flies here — one page")
            + ' <a href="../../transport.html">'
            + bi("เปิดหน้ารถ-เดินทาง", "Open the transport board") + "</a></p>")


def _routes():
    if not BUS.exists():
        return {}, {}
    doc = json.loads(BUS.read_text())
    rs = doc.get("routes") or []
    # The provincial register writes one row per (route, tambon it passes), so
    # 642 rows are ~200 routes seen many times over. Fold them back into
    # routes and keep the districts each one is licensed through.
    prov = {}
    for r in rs:
        if r.get("kind") != "provincial":
            continue
        e = prov.setdefault(r["name"], {"name": r["name"], "year_be": r.get("year_be"),
                                        "amphoe": set(), "tambon": set()})
        if r.get("amphoe"):
            e["amphoe"].add(r["amphoe"])
        if r.get("tambon"):
            e["tambon"].add(r["tambon"])
    numbered = [r for r in rs if r.get("kind") == "category-1-4"]
    city = [r for r in rs if r.get("kind") == "city"]
    return {"provincial": prov, "numbered": numbered, "city": city}, doc.get("sources") or {}


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    DOCS, BASE = g["DOCS"], g["BASE"]
    share_block, place_slug = g["share_block"], g["place_slug"]
    name_bi, name_of = g["name_bi"], g["name_of"]
    PROVINCES = g["PROVINCES"]
    routes, bus_src = _routes()
    subs = {p["key"]: _by_sub(data, p["key"]) for p in PROVINCES}

    def rows(prov, sub, limit=None):
        rs = sorted(subs[prov].get(sub) or [], key=name_of)
        out = []
        for r in rs[:limit] if limit else rs:
            line = f'<li><a href="{prov}/p/{place_slug(r)}.html">{name_bi(r)}</a>'
            bits = []
            if r.get("phone"):
                bits.append(f'<a href="tel:{att(re.sub(r"[^0-9+]", "", r["phone"]))}">'
                            f'☎️ {esc(r["phone"])}</a>')
            a = r.get("attrs") or {}
            if a.get("operator"):
                bits.append(esc(a["operator"]))
            if bits:
                line += ' <span class="count">· ' + " · ".join(bits) + "</span>"
            out.append(line + "</li>")
        return "".join(out), len(rs)

    def section(sub, note_th="", note_en=""):
        blocks = []
        total = 0
        for p in PROVINCES:
            html, n = rows(p["key"], sub)
            total += n
            if not n:
                continue
            blocks.append(f'<h3>{bi(p["th"], p["en"])} <span class="count">({n})</span> '
                          f'· <a href="{p["key"]}/transport/{sub}/index.html">'
                          + bi("ดูในสารบัญ", "on the shelf") + "</a></h3>"
                          f'<ul class="dir">{html}</ul>')
        if not total:
            return ""
        note = (f'<p class="tinynote">{bi(note_th, note_en)}</p>'
                if note_th or note_en else "")
        return (f'<section id="{sub}"><h2>{GLYPH[sub]} {bi(SUB_TH[sub], SUB_EN[sub])} '
                f'<span class="count">({total})</span></h2>{note}'
                + "".join(blocks) + "</section>")

    body = [f'<h1>🚌 {bi("รถ-เดินทาง", "Getting around")}</h1>']
    lede_th = ("เมืองนี้เดินทางด้วยอะไรบ้าง — รถแดง รถเมล์ รถไฟ แท็กซี่ เรือ และเครื่องบิน "
               "หน้านี้รวมทุกอย่างที่สารบัญถืออยู่จริงไว้ที่เดียว")
    lede_en = ("What this city actually moves on — red trucks, buses, the train, taxis, "
               "boats and flights — everything the catalogue holds, on one page.")
    body.append(f'<p>{bi(lede_th, lede_en)}</p>')
    # The honest frame, first and unmissable.
    warn_th = ("มดแดงไม่มีตารางเวลาและไม่มีค่าโดยสาร และจะไม่เดาให้ — ทะเบียนของทางราชการ "
               "บอกว่ารถสายไหนวิ่งไปไหน ไม่ได้บอกว่าออกกี่โมง คนที่รู้เวลาจริงคือผู้ประกอบการ "
               "ที่ท่ารถ ลิงก์อยู่ข้างล่างนี้")
    warn_en = ("This page has no timetables and no fares, and will not invent them. The "
               "government register says which routes run where, not when they leave — the "
               "people who know that are at the terminal, linked below.")
    body.append(f'<p class="myhint">⚠️ {bi(warn_th, warn_en)}</p>')

    # ---- the bus board ---------------------------------------------------
    if routes:
        city, numbered, prov_r = routes["city"], routes["numbered"], routes["provincial"]
        src = (bus_src.get("cm-bus-routes") or {})
        cred = (f'<a href="{att(src.get("dataset_url") or "https://data.go.th/")}" '
                f'rel="noopener">{esc(src.get("publisher") or "data.go.th")}</a>')
        city_html = "".join(
            f'<li><b>{esc(r.get("route_no") or "?")}</b> {esc(r["name"])}'
            + (f' <span class="count">· {r["vehicles"]} '
               + g["bi_text"]("คัน", "vehicles") + "</span>" if r.get("vehicles") else "")
            + "</li>" for r in sorted(city, key=lambda x: (x.get("route_no") or "")))
        num_html = "".join(
            f'<li><b>{esc(r.get("route_no") or "?")}</b> {esc(r["name"])}</li>'
            for r in sorted(numbered, key=lambda x: (x.get("route_no") or "")))
        prov_rows = sorted(prov_r.values(), key=lambda e: e["name"])
        prov_html = "".join(
            f'<li>{esc(e["name"])}'
            + (f' <span class="count">· {g["bi_text"]("ผ่าน", "through")} '
               + esc(", ".join(sorted(e["amphoe"])[:6])) + "</span>" if e["amphoe"] else "")
            + "</li>" for e in prov_rows)
        yr = next((e["year_be"] for e in prov_rows if e.get("year_be")), None)
        body.append(
            f'<section id="bus-routes"><h2>🚌 {bi("สายรถโดยสารประจำทาง", "Licensed bus routes")} '
            f'<span class="count">({len(prov_rows) + len(numbered) + len(city)})</span></h2>'
            f'<p class="tinynote">'
            + bi(f"จากทะเบียนเส้นทางของทางราชการ{f' พ.ศ. {yr}' if yr else ''} — "
                 "บอกว่าสายไหนได้รับอนุญาตให้วิ่งไปไหน ไม่มีเวลาออกรถอยู่ในทะเบียน",
                 f"From the province's own route register{f', B.E. {yr}' if yr else ''} — "
                 "which routes are licensed to run where. The register carries no departure times.")
            + f" · {cred}</p>"
            + (f'<h3>{bi("ในเขตเมืองเชียงใหม่", "Chiang Mai city routes")} '
               f'<span class="count">({len(city)})</span></h3><ul class="dir">{city_html}</ul>'
               if city else "")
            + (f'<h3>{bi("สายมีหมายเลข (หมวด 1 และ 4)", "Numbered routes (categories 1 and 4)")} '
               f'<span class="count">({len(numbered)})</span></h3>'
               f'<ul class="dir">{num_html}</ul>' if numbered else "")
            + (f'<h3>{bi("สายในจังหวัด", "Routes across the province")} '
               f'<span class="count">({len(prov_rows)})</span></h3>'
               f'<ul class="dir">{prov_html}</ul>' if prov_rows else "")
            + f'<p class="prov"><a href="data/bus_routes.json">⬇ '
            + bi("ไฟล์เส้นทางทั้งหมด", "the whole route file") + "</a></p></section>")

    # ---- the shelf sections, each pointing at its own child ---------------
    body.append(section(
        "bus",
        "ท่ารถและสถานีขนส่งที่อยู่บนแผนที่ กดชื่อเพื่อดูหน้าของแต่ละที่ เบอร์โทรถ้ามี",
        "The terminals and stops on the map. Open one for whatever we hold — a phone, if there is one."))
    body.append(section(
        "train",
        "สถานีรถไฟที่อยู่บนแผนที่ ตารางเวลาที่แน่นอนอยู่ที่การรถไฟฯ เอง · เชียงรายยังไม่มีสถานีรถไฟในสารบัญ",
        "The railway stations on the map. The timetable that matters is SRT's own. "
        "Chiang Rai has no railway station in this catalogue."))
    body.append(section(
        "songthaew",
        "OSM ไม่มีช่องสำหรับรถสองแถว คนทำแผนที่จึงเขียนปลายทางไว้ในชื่อ — ชื่อที่เห็นคือสิ่งที่เขาเขียนไว้จริง",
        "OSM has no field for a songthaew route, so mappers wrote the destination into the "
        "name. What you see is what they wrote — read it as a mapper's note, not a timetable."))
    body.append(section(
        "taxi", "คิวรถและจุดจอดแท็กซี่ที่บันทึกไว้",
        "The taxi ranks and stands on record."))
    body.append(section(
        "funicular", "รถรางขึ้นพระธาตุดอยสุเทพ — สถานีล่างและสถานีบน",
        "The cable car up to Wat Phra That Doi Suthep — its bottom and top stations."))
    body.append(section("pier", "ท่าเรือและท่าแพ", "Boat landings."))
    body.append(section("airport", "", ""))

    # ---- flights: the board that existed and nothing pointed at ----------
    if (DOCS / "flights.html").exists():
        body.append(
            f'<section id="flights"><h2>✈️ {bi("ใครบินมาที่นี่", "Who flies here")}</h2>'
            f'<p>{bi("กระดานเส้นทางบิน — สายการบิน ปลายทาง และฤดูกาลของแต่ละเส้นทาง จาก CNX และ CEI", "The route board — airlines, destinations and the season each route runs, out of CNX and CEI.")}'
            f' <a href="flights.html">{bi("เปิดกระดานเที่ยวบิน", "Open the flight board")}</a></p></section>')

    body.append(f'<p class="tinynote">'
                + bi("ขาดสายไหน ท่ารถไหน หรือรู้เวลาเดินรถจริง บอกมดได้ที่หน้าเพิ่มข้อมูล",
                     "A route missing, a stop we don't have, or a departure time you actually know? "
                     "Tell the ants on the add-a-place page.")
                + f' <a href="add.html">{bi("เพิ่มข้อมูล", "Add a place")}</a> · '
                f'<a href="plan.html">{bi("วางแผนเดินทางในเมือง", "Plan a route on foot or by bike")}</a></p>')
    body.append(share_block(BASE + "transport.html", "รถ-เดินทาง · มดแดง"))

    (DOCS / "transport.html").write_text(page(
        "รถ-เดินทาง", "".join(body), depth=0, path="transport.html",
        desc="รถ-เดินทางเชียงใหม่-เชียงราย — สายรถโดยสาร สถานีรถไฟ รถแดง แท็กซี่ ท่าเรือ และเที่ยวบิน",
        crumbs=f'<a href="index.html">มดแดง</a> › {bi("รถ-เดินทาง", "Getting around")}'))
    counts = {s: sum(len(subs[p["key"]].get(s) or []) for p in PROVINCES)
              for s in ("train", "bus", "songthaew", "taxi", "funicular", "pier")}
    return {"page": 1, "routes": sum(len(v) for v in routes.values()) if routes else 0, **counts}


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. Run: python3 build.py")
