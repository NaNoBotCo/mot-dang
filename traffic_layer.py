#!/usr/bin/env python3
"""/traffic.html — รถติด, rot tit: which hour jams, and which road.

Nan, 2026-09-26: "can you build a TRAFFIC forecasting map for motdang?
Traffic is pretty bad throughout thailand."

THE FORECAST IS ARITHMETIC ON TWO MEASUREMENTS, and the page prints the sum.

  The hour. TomTom's 2025 figures for central Chiang Mai: how much longer a
  drive takes than on an empty road, for every weekday hour (7 × 24), and the
  same by month. The forecast for a day and hour is that weekday-hour figure
  scaled by its month against the year:

        congestion = week[day][hour] × month[m] ÷ year
        minutes for a 10-minute trip = 10 × (1 + congestion ÷ 100)

  Nothing else moves it. Rain, a festival and a walking street are printed
  beside the number, as lines, because nothing on this disk measures what
  they do to it.

  The road. DOH's own counts (vehicles a day, 2025) and DOH's own grade for
  each highway section at its busiest hour, A to F: peak-hour volume against
  the road's capacity. Those lines keep their grade whatever hour is picked;
  the grade is the state's figure for the worst hour and the page says so.

  The cells. TomTom's H3 cells for central Chiang Mai carry a jam score,
  10 to 100, for the morning rush, the evening rush and the whole year. The
  map shows the set for the hour's part of the day, scaled by that hour's
  congestion against the rush it belongs to.

Chiang Rai has DOH's roads and no hour-by-hour figure; the page says that.

Entry point: emit(globals_of_build). Standalone, over a built docs/:
    python3 traffic_layer.py
"""
import datetime
import json
import math
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DAYS_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_TH_S = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
DAYS_EN_S = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.",
             "ต.ค.", "พ.ย.", "ธ.ค."]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
             "Nov", "Dec"]

# Congestion bands for the words beside the number. The number is TomTom's;
# where the words change is this page's reading of it.
BANDS = [  # (from, colour, th, en, ink on that colour)
    (0, "#1f6b57", "โล่ง", "clear", "#ffffff"),
    (15, "#5f9b3a", "คล่อง", "moving", "#1a1208"),
    (35, "#e2b21c", "ช้า", "slow", "#1a1208"),
    (60, "#e0782d", "ติด", "jammed", "#1a1208"),
    (85, "#c13a2e", "ติดหนัก", "heavy jam", "#ffffff"),
]

# DOH's grade: peak-hour volume against the road's capacity.
GRADES = {
    "A": ("#1f6b57", "โล่ง", "free flow"),
    "B": ("#5f9b3a", "คล่อง", "steady"),
    "C": ("#e2b21c", "เริ่มแน่น", "filling up"),
    "D": ("#e0782d", "แน่น", "dense"),
    "E": ("#c13a2e", "เต็มถนน", "at capacity"),
    "F": ("#6e1620", "เกินถนนรับได้", "over capacity"),
}

GRID_HOURS = list(range(5, 24))   # the week grid's columns; the night is flat
CITY_VIEW = (98.99, 18.795, 12.2)
CITY_BOX = (98.93, 18.73, 99.06, 18.87)   # the fallback drawing's frame: about ring road 2


def band(c):
    b = BANDS[0]
    for x in BANDS:
        if c >= x[0]:
            b = x
    return b


def forecast(city, dow, hour, month):
    """(congestion %, minutes for a 10-minute trip, km/h) — the docstring's sum."""
    c0, _v, fv = city["center"]["week"][dow][hour]
    c = c0 * city["center"]["month"][month] / city["center"]["year_c"]
    return c, 10 * (1 + c / 100), fv / (1 + c / 100)


def compact(doc, weather, festivals, markets, translit):
    """The browser's copy: what the page draws, rounded to what it can show."""
    city = doc["city"]
    hexes = city["hex"]
    # H3 cells this size, this far from a pentagon, are one shape: every ring
    # in the city sits within 1.3 m of the first ring's offsets (measured
    # 2026-09-26), so the page gets a template and a centre per cell.
    r0 = hexes[0]["ring"]
    cx0 = sum(p[0] for p in r0) / 6
    cy0 = sum(p[1] for p in r0) / 6
    tpl = [[round(p[0] - cx0, 6), round(p[1] - cy0, 6)] for p in r0]
    cells = []
    for h in hexes:
        cx = sum(p[0] for p in h["ring"]) / 6
        cy = sum(p[1] for p in h["ring"]) / 6
        cells.append([round(cx, 5), round(cy, 5), h["all"], h["am"], h["pm"]])
    roads = []
    for r in doc["roads"]:
        parts = [[v for pt in ln for v in (round(pt[0], 4), round(pt[1], 4))]
                 for ln in r["lines"]]
        en = translit.title(r["name"]) if r["name"] else ""
        roads.append([r["route"], r["section"], r["name"], en, r["motor"], r["moto"],
                      r["heavy"], r["grade"] or "", parts])
    c = city["center"]
    return {
        "g": doc["generated"],
        "w": [[[x[0], x[2]] for x in row] for row in c["week"]],
        "m": c["month"], "yc": c["year_c"],
        "am": [c["am"]["hour"], c["am"]["c"]], "pm": [c["pm"]["hour"], c["pm"]["c"]],
        "hx": {"t": tpl, "c": cells},
        "r": roads,
        "gy": doc["roads_meta"].get("grade_year_be"),
        "ry": doc["roads_meta"].get("year_be"),
        "wx": weather, "fe": festivals, "mk": markets,
    }


def _weather(root):
    p = root / "data" / "weather.json"
    try:
        for cty in json.loads(p.read_text())["cities"]:
            if cty["id"] == "chiang-mai":
                return cty.get("hours") or []
    except (OSError, ValueError, KeyError):
        pass
    return []


def _festivals(root, today):
    """Dated festival days from today on, with names, for the context line."""
    try:
        names = {f["id"]: (f.get("name_th"), f.get("name_en"))
                 for f in json.loads((root / "data" / "festivals.json").read_text())["festivals"]}
        rows = json.loads((root / "data" / "festival_calendar.json").read_text())["rows"]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for r in rows:
        if (r.get("date_end") or r.get("date_start") or "") < today:
            continue
        th, en = names.get(r["festival_id"], (None, None))
        if th:
            out.append([r["date_start"], r.get("date_end") or r["date_start"], th, en,
                        r["festival_id"]])
    return sorted(out)


_DAYS = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}


def _markets(root):
    """Walking streets with hours a machine can read: [name, days, from, to, lng, lat]."""
    import re
    try:
        lamps = json.loads((root / "data" / "open_lamps.json").read_text())
    except (OSError, ValueError):
        return []
    places = lamps.get("places") or []
    out = []
    for m in (lamps.get("markets") or {}).get("list") or []:
        if "ถนนคนเดิน" not in m.get("n", "") and "walking street" not in m.get("n", "").lower():
            continue
        mm = re.fullmatch(r"\s*([A-Za-z]{2})(?:-([A-Za-z]{2}))?\s+(\d\d):(\d\d)-(\d\d):(\d\d)\s*",
                          m.get("hours") or "")
        if not mm:
            continue
        a, b = _DAYS.get(mm.group(1).lower()), _DAYS.get((mm.group(2) or mm.group(1)).lower())
        if a is None or b is None:
            continue
        days = list(range(a, b + 1)) if a <= b else list(range(a, 7)) + list(range(0, b + 1))
        k = m.get("k")
        pl = places[k] if isinstance(k, int) and k < len(places) else {}
        if pl.get("id") != m.get("id"):
            pl = next((p for p in places if p.get("id") == m.get("id")), {})
        out.append([m["n"], days, int(mm.group(3)) * 60 + int(mm.group(4)),
                    int(mm.group(5)) * 60 + int(mm.group(6)), pl.get("ln"), pl.get("la")])
    return out


def _svg(doc, bi_text, att):
    """The map with no tiles: DOH's roads over the evening-rush cells, in the
    city frame. Every shape is .mdmap-bg, so the live map replaces it."""
    w0, s0, e0, n0 = CITY_BOX
    kx = math.cos(math.radians((s0 + n0) / 2))
    W = 720
    H = round(W * (n0 - s0) / ((e0 - w0) * kx))

    def xy(lng, lat):
        return (lng - w0) / (e0 - w0) * W, (n0 - lat) / (n0 - s0) * H

    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" class="tdraw" role="img" '
           f'aria-label="{att(bi_text("แผนที่รถติดเย็นวันธรรมดา ในเมืองเชียงใหม่", "Where central Chiang Mai jams in the evening rush"))}">',
           f'<rect class="mdmap-bg" width="{W}" height="{H}" fill="#FBF6EE"/>']
    tpl = doc["city"]["hex"][0]["ring"]
    cx0 = sum(p[0] for p in tpl) / 6
    cy0 = sum(p[1] for p in tpl) / 6
    pts = " ".join("%.1f,%.1f" % ((p[0] - cx0) / (e0 - w0) * W, -(p[1] - cy0) / (n0 - s0) * H)
                   for p in tpl)
    out.append(f'<defs><polygon id="thx" points="{pts}"/></defs><g class="mdmap-bg">')
    for h in doc["city"]["hex"]:
        s = h["pm"]
        if s < 40:
            continue
        cx = sum(p[0] for p in h["ring"]) / 6
        cy = sum(p[1] for p in h["ring"]) / 6
        if not (w0 < cx < e0 and s0 < cy < n0):
            continue
        x, y = xy(cx, cy)
        out.append(f'<use href="#thx" x="{x:.1f}" y="{y:.1f}" fill="{band(s)[1]}" '
                   f'fill-opacity="0.55"/>')
    out.append('</g><g class="mdmap-bg" fill="none" stroke-linecap="round">')
    for r in sorted(doc["roads"], key=lambda r: r["motor"]):
        col = GRADES.get(r["grade"] or "", ("#6d5411",))[0]
        wd = 2 + 6 * min(1, r["motor"] / 120000)
        for ln in r["lines"]:
            if not any(w0 < p[0] < e0 and s0 < p[1] < n0 for p in ln):
                continue
            d = "M" + " L".join("%.1f %.1f" % xy(*p) for p in ln)
            out.append(f'<path d="{d}" stroke="#fff" stroke-width="{wd + 2:.1f}"/>'
                       f'<path d="{d}" stroke="{col}" stroke-width="{wd:.1f}"/>')
    out.append('</g></svg>')
    return "".join(out), (e0 - w0) * kx * 111320 / W   # metres per viewBox unit


def build_page(g, doc, pay):
    bi, bi_text, esc, att = g["bi"], g["bi_text"], g["esc"], g["att"]
    page, share_block, BASE = g["page"], g["share_block"], g["BASE"]
    map_shell, glyphs = g["map_shell"], g["glyphs"]
    city = doc["city"]
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    dow, hour, mon = now.weekday(), now.hour, now.month - 1

    # The static answer: what the page says with scripting off, for the hour
    # it was built. The script redraws it from the reader's own clock.
    c, mins, kmh = forecast(city, dow, hour, mon)
    b = band(c)
    head = (f'<div class="tnow" id="tnow" style="--b:{b[1]};--bi:{b[4]}">'
            f'<p class="twhen" id="twhen">{bi(DAYS_TH[dow] + " " + "%02d:00" % hour, DAYS_EN[dow] + " %02d:00" % hour)}</p>'
            f'<p class="tbig"><span class="tword" id="tword">{bi(b[2], b[3])}</span></p>'
            f'<p class="tmin" id="tmin">{bi("ทาง 10 นาที ใช้ %d นาที" % round(mins), "A 10-minute drive takes %d" % round(mins))}</p>'
            f'<p class="tsub" id="tsub">{bi("ในเมืองเชียงใหม่ ช้ากว่าถนนโล่ง %d%% · เฉลี่ย %d กม./ชม." % (round(c), round(kmh)), "Central Chiang Mai, %d%% slower than an empty road · %d km/h" % (round(c), round(kmh)))}</p>'
            f'<p class="tctx" id="tctx" hidden></p>'
            f'</div>')

    days = ('<div class="tdays" id="tdays" role="group" aria-label="%s">' %
            att(bi_text("เลือกวัน", "Pick a day")))
    for k in range(7):
        d = (dow + k) % 7
        th = "วันนี้" if k == 0 else "พรุ่งนี้" if k == 1 else DAYS_TH[d]
        en = "Today" if k == 0 else "Tomorrow" if k == 1 else DAYS_EN[d]
        days += (f'<button type="button" class="tday" data-k="{k}" '
                 f'aria-pressed="{"true" if k == 0 else "false"}">{bi(th, en)}</button>')
    days += "</div>"

    bars = []
    for h in range(24):
        ch, mh, _ = forecast(city, dow, h, mon)
        bars.append(f'<button type="button" class="tbar{" on" if h == hour else ""}" data-h="{h}" '
                    f'style="--h:{min(100, 8 + ch * 0.9):.0f}%;--b:{band(ch)[1]}" '
                    f'aria-label="{att("%02d:00 · %d min" % (h, round(mh)))}"></button>')
    strip = (f'<div class="tstrip" id="tstrip">{"".join(bars)}</div>'
             f'<div class="thours" aria-hidden="true">'
             + "".join(f'<span style="grid-column:{h + 1}">{h}</span>' for h in (0, 6, 12, 18))
             + '</div>'
             f'<div class="tstep">'
             f'<button type="button" id="tprev" class="tbtn">‹ {bi("ชั่วโมงก่อน", "Earlier")}</button>'
             f'<button type="button" id="tnowb" class="tbtn">{glyphs.icon("i-clock", 18)}{bi("ตอนนี้", "Now")}</button>'
             f'<button type="button" id="tnext" class="tbtn">{bi("ชั่วโมงถัดไป", "Later")} ›</button>'
             f'</div>'
             f'<p class="twait" id="twait" hidden></p>')

    fallback, mpu = _svg(doc, bi_text, att)
    box = map_shell.mount("tmap", fallback, prov="cm", zoom=CITY_VIEW[2],
                          lat=CITY_VIEW[1], lng=CITY_VIEW[0], cls="mdmap tmap", mpu=mpu)

    views = (f'<div class="tviews" role="group" aria-label="{att(bi_text("ดูที่ไหน", "Where"))}">'
             f'<button type="button" class="tview" data-v="city" aria-pressed="true">{bi("ในเมืองเชียงใหม่", "Chiang Mai city")}</button>'
             f'<button type="button" class="tview" data-v="cm" aria-pressed="false">{bi("จังหวัดเชียงใหม่", "Chiang Mai province")}</button>'
             f'<button type="button" class="tview" data-v="cr" aria-pressed="false">{bi("เชียงราย", "Chiang Rai")}</button>'
             f'</div>')

    legend_g = "".join(
        f'<li><i style="background:{col}"></i><b>{k}</b> {bi(th, en)}</li>'
        for k, (col, th, en) in GRADES.items())
    legend_b = "".join(
        f'<li><i style="background:{col}"></i>{bi(th, en)}</li>' for _, col, th, en, _ink in BANDS)
    legend = (f'<div class="tlegend">'
              f'<div><h3>{bi("ช่องหกเหลี่ยม: ในเมือง ตามชั่วโมงที่เลือก", "Hexagons: the city, at the hour you picked")}</h3>'
              f'<ul class="tkey">{legend_b}</ul></div>'
              f'<div><h3>{bi("เส้นถนนหลวง: ชั่วโมงที่ติดที่สุดของถนนเส้นนั้น", "Highway lines: that road at its busiest hour")}</h3>'
              f'<ul class="tkey">{legend_g}</ul>'
              f'<p class="quiet">{bi("เส้นหนา = รถมาก แตะเส้นเพื่อดูตัวเลข", "Thicker = more vehicles. Touch a line for its numbers.")}</p></div>'
              f'</div>')

    # The week at a glance, drawn here so it stands with scripting off.
    grid = [f'<table class="tweek" id="tweek"><caption>{bi("ทั้งสัปดาห์: ทาง 10 นาที ใช้กี่นาที", "The week: minutes for a 10-minute drive")} '
            f'<span class="quiet tmon" id="tmon">{bi("เดือน " + MONTHS_TH[mon], "Month: " + MONTHS_EN[mon])}</span></caption>'
            '<thead><tr><th></th>']
    for h in GRID_HOURS:
        grid.append(f'<th scope="col">{h if h % 3 == 0 else ""}</th>')
    grid.append('</tr></thead><tbody>')
    for d in range(7):
        grid.append(f'<tr><th scope="row"><span class="th" lang="th">{DAYS_TH_S[d]}</span>'
                    f'<span class="en" lang="en">{DAYS_EN_S[d]}</span></th>')
        for h in GRID_HOURS:
            ch, mh, _ = forecast(city, d, h, mon)
            grid.append(f'<td><button type="button" class="tcell" data-d="{d}" data-h="{h}" '
                        f'style="--b:{band(ch)[1]}" aria-label="{att("%s %02d:00 · %d นาที/min" % (DAYS_TH[d], h, round(mh)))}">'
                        f'{round(mh)}</button></td>')
        grid.append('</tr>')
    grid.append('</tbody></table>')

    # The worst and the best waking hours of the week, as sentences.
    cells = [(forecast(city, d, h, mon), d, h) for d in range(7) for h in range(6, 23)]
    worst = max(cells, key=lambda x: x[0][0])
    best = min(cells, key=lambda x: x[0][0])
    facts = (f'<ul class="tfacts">'
             f'<li>{bi("ช่วงติดที่สุดของสัปดาห์: %s %02d:00 ทาง 10 นาที ใช้ %d นาที" % (DAYS_TH[worst[1]], worst[2], round(worst[0][1])), "Worst hour of the week: %s %02d:00, a 10-minute drive takes %d" % (DAYS_EN[worst[1]], worst[2], round(worst[0][1])))}</li>'
             f'<li>{bi("ช่วงโล่งที่สุด (06:00–22:00): %s %02d:00 ใช้ %d นาที" % (DAYS_TH[best[1]], best[2], round(best[0][1])), "Clearest hour between 06:00 and 22:00: %s %02d:00, %d minutes" % (DAYS_EN[best[1]], best[2], round(best[0][1])))}</li>'
             f'</ul>')

    top = sorted(doc["roads"], key=lambda r: -r["motor"])[:10]
    rows = "".join(
        f'<tr><td><b>{esc(r["route"])}</b> {bi(r["name"], g["translit"].title(r["name"]))}</td>'
        f'<td class="n">{r["motor"]:,}</td><td class="n">{r["moto"]:,}</td>'
        f'<td><span class="tg" style="--g:{GRADES.get(r["grade"] or "", ("#999",))[0]}">{esc(r["grade"] or "?")}</span></td></tr>'
        for r in top)
    table = (f'<div class="tscroll"><table class="troads"><caption>{bi("ถนนหลวงที่รถมากที่สุด", "The busiest highways")}'
             f'<span class="quiet tcap">{bi("รถต่อวัน: รถยนต์ รถบัส รถบรรทุก มอเตอร์ไซค์แยกช่อง", "Vehicles a day: cars, buses, trucks; motorcycles counted apart")}</span></caption>'
             f'<thead><tr><th>{bi("ทางหลวง", "Route")}</th>'
             f'<th class="n">{bi("รถ/วัน", "Vehicles")}</th>'
             f'<th class="n">{bi("มอเตอร์ไซค์", "Motorcycles")}</th>'
             f'<th>{bi("ระดับ", "Grade")}</th></tr></thead><tbody>{rows}</tbody></table></div>')

    rm = doc["roads_meta"]
    src = city["source"]
    how = (
        f'<section class="thow"><h2>{bi("ตัวเลขมาจากไหน", "Sources")}</h2><ul>'
        f'<li>{bi("ชั่วโมง: " + src["th"] + " ปี 2025 ช่วงกลางเมืองเชียงใหม่ ทุกวันทุกชั่วโมง และรายเดือน", "The hour: " + src["en"] + ", central Chiang Mai, every weekday hour and every month")} '
        f'<a href="{att(src["url"])}">tomtom.com</a> · © TomTom</li>'
        f'<li>{bi("คำนวณ: ระดับรถติด = ค่าของวันและชั่วโมงนั้น × ค่าของเดือน ÷ ค่าทั้งปี แล้ว นาที = 10 × (1 + ระดับรถติด ÷ 100)", "The sum: congestion = that weekday-hour × that month ÷ the year; minutes = 10 × (1 + congestion ÷ 100)")}</li>'
        f'<li>{bi("ตัวเลขนี้เป็นค่าเฉลี่ยของปีที่แล้ว ฝน งานบุญ และถนนคนเดิน ไม่ได้คิดรวม ขึ้นเป็นบรรทัดบอกไว้ข้างตัวเลข", "It is last year averaged. Rain, festivals and walking streets are not in the sum; they show as a line beside it.")}</li>'
        f'<li>{bi("ถนนหลวง: กรมทางหลวง ปริมาณจราจรเฉลี่ยต่อวัน ปี %s (%d ช่วงถนนในเชียงใหม่และเชียงราย) และระดับความติดขัดในชั่วโมงเร่งด่วน ปี %s" % (rm.get("year_be"), len(doc["roads"]), rm.get("grade_year_be")), "Highways: Department of Highways traffic counts, %s BE (%d sections in Chiang Mai and Chiang Rai), and its peak-hour congestion grade, %s BE" % (rm.get("year_be"), len(doc["roads"]), rm.get("grade_year_be")))} '
        + " · ".join(f'<a href="{att(s["url"])}">{esc(s["th"])}</a>' for s in rm.get("sources", []))
        + f' · {bi("ข้อมูลเปิดภาครัฐ", "Open Government Data of Thailand")}</li>'
        f'<li>{bi("ระดับ A–F ของกรมทางหลวง: ปริมาณรถในชั่วโมงที่ติดที่สุด เทียบกับที่ถนนรับได้ E คือเต็มถนน F คือเกิน", "DOH grades A–F: peak-hour vehicles against what the road can carry. E is at capacity, F is over it.")}</li>'
        f'<li>{bi("เชียงราย: มีแต่ตัวเลขถนนหลวงของกรมทางหลวง ยังไม่มีตัวเลขรายชั่วโมง", "Chiang Rai: DOH highway figures only; no hour-by-hour figure on hand.")}</li>'
        f'<li>{bi("ฝน: Open-Meteo 48 ชั่วโมงข้างหน้า · ถนนคนเดิน: เวลาเปิดจาก OpenStreetMap · งานบุญ: ปฏิทินของมดแดง", "Rain: Open-Meteo, the next 48 hours · Walking streets: opening hours from OpenStreetMap · Festivals: the Mot Dang calendar")}</li>'
        f'</ul></section>')

    body = (
        f'<h1>{bi("รถติด", "Traffic")} <span class="trom">rot tit</span></h1>'
        f'{head}{days}{strip}'
        f'{box}{views}{legend}'
        f'{"".join(grid)}{facts}{table}{how}'
        f'{share_block(BASE + "traffic.html", bi_text("รถติด เชียงใหม่ ชั่วโมงไหน ถนนเส้นไหน", "Chiang Mai traffic: which hour, which road"))}'
        f'<script type="application/json" id="tdata-src">{json.dumps({"v": version_data(pay)})}</script>')

    return page("รถติด", body, depth=0, path="traffic.html",
                desc="ชั่วโมงไหนรถติด ถนนเส้นไหนติด ในเชียงใหม่และเชียงราย · Which hour jams and which road, in Chiang Mai and Chiang Rai",
                og="traffic-card.png",
                extra_head=f'<link rel="stylesheet" href="traffic.css?v={version()}">'
                           f'<script src="traffic.js?v={version()}" defer></script>')


def version_data(pay):
    return "%08x" % (zlib.crc32(json.dumps(pay, sort_keys=True).encode()) & 0xFFFFFFFF)


def version():
    return "%08x" % (zlib.crc32((JS + CSS).encode()) & 0xFFFFFFFF)


def emit(g):
    DOCS, ROOT_ = g["DOCS"], g["ROOT"]
    src = ROOT_ / "data" / "traffic.json"
    if not src.exists():
        return "SKIPPED — no data/traffic.json (importers/make_traffic.py)"
    doc = json.loads(src.read_text(encoding="utf-8"))
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).date().isoformat()
    pay = compact(doc, _weather(ROOT_), _festivals(ROOT_, today), _markets(ROOT_),
                  g["translit"])
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "traffic.json").write_text(
        json.dumps(pay, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DOCS / "traffic.css").write_text(CSS)
    (DOCS / "traffic.js").write_text(JS.replace("__GRADES__", json.dumps(
        {k: [v[0], v[1], v[2]] for k, v in GRADES.items()}, ensure_ascii=False)).replace(
        "__BANDS__", json.dumps([list(b) for b in BANDS], ensure_ascii=False)))
    (DOCS / "traffic.html").write_text(build_page(g, doc, pay))
    card = ROOT_ / "assets" / "og" / "traffic-card.png"
    if card.exists():
        (DOCS / "traffic-card.png").write_bytes(card.read_bytes())
    return "%d roads, %d cells, %s" % (len(pay["r"]), len(pay["hx"]["c"]),
                                       "card" if card.exists() else "NO CARD (make_traffic_card.py)")


CSS = """/* /traffic.html — รถติด */
.trom{font-size:.5em;font-weight:400;color:var(--mute);letter-spacing:.02em}
.tnow{border:3px solid var(--b);border-radius:16px;padding:14px 16px;margin:10px 0 14px;
 background:linear-gradient(180deg,color-mix(in srgb,var(--b) 14%,#fff) 0%,var(--card,#fffdf7) 70%);
 box-shadow:4px 4px 0 var(--b)}
.tnow p{margin:0}
.twhen{font-size:1rem;color:var(--ink-soft)}
.tbig{font-size:2rem;font-weight:700;line-height:1.2;margin:4px 0!important}
.tword{display:inline-block;background:var(--b);color:var(--bi);border-radius:12px;padding:2px 14px}
.tmin{font-size:1.35rem;font-weight:700;margin-top:2px!important}
.tsub{font-size:1rem;color:var(--ink-soft);margin-top:4px!important}
.tctx{margin-top:10px!important;font-size:1rem}
.tctx span.tline{display:block;padding:6px 10px;margin-top:6px;border-radius:10px;background:var(--card-alt,#f8f0dd)}
.tctx .rowicon{vertical-align:-4px;margin-right:4px}
.tdays{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px;scrollbar-width:none}
.tday{flex:0 0 auto;border:2px solid var(--ink);background:var(--paper);border-radius:999px;
 padding:8px 14px;font:inherit;font-size:1rem;min-height:44px;cursor:pointer}
.tday[aria-pressed=true]{background:var(--ink);color:var(--paper)}
.tstrip{display:grid;grid-template-columns:repeat(24,1fr);gap:2px;align-items:end;height:92px;
 padding:4px 0;border-bottom:2px solid var(--rule)}
.tbar{height:var(--h);min-height:6px;background:var(--b);border:0;border-radius:4px 4px 0 0;padding:0;
 cursor:pointer;opacity:.8}
.tbar.on{opacity:1;outline:3px solid var(--ink);outline-offset:1px}
.tbar.now{box-shadow:inset 0 3px 0 var(--ink)}
.thours{display:grid;grid-template-columns:repeat(24,1fr);font-size:.8rem;color:var(--mute)}
.tstep{display:flex;gap:8px;justify-content:space-between;margin:8px 0}
.tbtn{flex:1;border:2px solid var(--ink);background:var(--paper);border-radius:12px;min-height:44px;
 font:inherit;font-size:1rem;cursor:pointer;padding:6px 8px}
.tbtn .rowicon{vertical-align:-4px;margin-right:4px}
.twait{font-size:1.05rem;padding:8px 12px;border-left:5px solid var(--jade,#1f6b57);background:var(--card-alt,#f8f0dd);
 border-radius:0 10px 10px 0;margin:4px 0 12px}
.tmap{margin-top:8px;aspect-ratio:4/5;max-height:78vh}
@media (min-width:760px){.tmap{aspect-ratio:4/3}}
.tviews{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.tview{border:2px solid var(--ink);background:var(--paper);border-radius:999px;padding:6px 12px;
 min-height:44px;font:inherit;font-size:.95rem;cursor:pointer}
.tview[aria-pressed=true]{background:var(--ink);color:var(--paper)}
.tlegend{display:grid;gap:10px;margin:10px 0 18px}
@media (min-width:760px){.tlegend{grid-template-columns:1fr 1fr}}
.tlegend>div{min-width:0}
.tlegend .bi,.tkey .bi,.tnow .bi,.twait .bi,.tbtn .bi{white-space:normal}
.tlegend h3{font-size:1rem;margin:0 0 4px}
.tkey{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 12px}
.tkey li{display:flex;align-items:center;gap:6px;font-size:.95rem}
.tkey i{display:inline-block;width:22px;height:12px;border-radius:3px}
.tweek{border-collapse:separate;border-spacing:2px;width:100%;margin:18px 0 6px;table-layout:fixed}
.tweek caption{text-align:left;font-weight:700;font-size:1.05rem;padding-bottom:6px}
.tweek th{font-weight:400;font-size:.8rem;color:var(--mute);padding:0}
.tweek tbody th{text-align:left;width:34px;font-size:.72rem;line-height:1.1;color:var(--ink)}
.tweek tbody th span{display:block}
.tweek tr>th:first-child{width:34px}
.tweek .tmon{display:block;font-weight:400;font-size:.95rem}
.tweek td{padding:0}
.tcell{width:100%;aspect-ratio:1;min-height:18px;border:0;border-radius:4px;background:var(--b);
 color:#fff;font:inherit;font-size:.7rem;font-weight:700;padding:0;cursor:pointer;text-shadow:0 0 2px rgba(0,0,0,.6)}
.tcell.on{outline:3px solid var(--ink);outline-offset:1px}
@media (max-width:420px){.tcell{font-size:0}}
.tfacts{padding-left:1.1em;font-size:1.05rem}
.tscroll{overflow-x:auto;margin:14px 0}
.troads{width:100%;min-width:320px;border-collapse:collapse;margin:14px 0;font-size:.95rem}
.troads caption{text-align:left;font-weight:700;font-size:1.05rem;padding-bottom:6px}
.troads .tcap{display:block;font-weight:400;font-size:.9rem}
.troads th,.troads td{padding:6px 4px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
.troads .n{text-align:right;font-variant-numeric:tabular-nums}
.tg{display:inline-block;min-width:1.6em;text-align:center;border-radius:6px;background:var(--g);color:#fff;font-weight:700}
.thow ul{padding-left:1.1em}
.thow li{margin-bottom:6px}
"""

JS = r"""/* traffic.js — /traffic.html. Reads data/traffic.json; the sum is in
   traffic_layer.py's docstring and on the page under Sources. */
(function(){
'use strict';
var G=__GRADES__,BANDS=__BANDS__;
var DTH=['จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์','อาทิตย์'];
var DEN=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
var MTH=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'];
var MEN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function B(th,en){return '<span class="bi"><span class="th" lang="th">'+esc(th)+'</span><span class="en" lang="en"><span class="th" lang="th"> · </span>'+esc(en)+'</span></span>';}
function icon(n){return window.mdIcon?window.mdIcon(n,20):'';}
function pad(h){return (h<10?'0':'')+h+':00';}
function band(c){var b=BANDS[0];for(var i=0;i<BANDS.length;i++)if(c>=BANDS[i][0])b=BANDS[i];return b;}
/* Bangkok keeps one offset all year, so +7 h and the UTC fields are its clock. */
function bkk(ms){var t=new Date(ms+7*3600e3);
 return{dow:(t.getUTCDay()+6)%7,h:t.getUTCHours(),mon:t.getUTCMonth(),
  iso:t.toISOString().slice(0,10),mins:t.getUTCHours()*60+t.getUTCMinutes()};}

var D=null,sel={k:0,h:0},map=null,el=document.getElementById('tmap');
function dayOf(k){return bkk(Date.now()+k*864e5);}
function fc(dow,h,mon){var x=D.w[dow][h],c=x[0]*D.m[mon]/D.yc;
 return{c:c,min:10*(1+c/100),kmh:x[1]/(1+c/100)};}

function context(day,h){
 var out=[];
 var key=day.iso+'T'+pad(h);
 (D.wx||[]).forEach(function(r){
  if(r[0]===key&&(r[1]>=50||r[2]>=0.5))
   out.push(icon('i-rain')+B('ฝนน่าจะตก '+r[1]+'%'+(r[2]>=0.1?' · '+r[2]+' มม.':''),
    'Rain likely, '+r[1]+'%'+(r[2]>=0.1?', '+r[2]+' mm':'')));});
 (D.mk||[]).forEach(function(m){
  var t=h*60;
  if(m[1].indexOf(day.dow)>-1&&t+59>=m[2]&&t<m[3])
   out.push(icon('i-walk')+B(m[0]+' '+Math.floor(m[2]/60)+':'+('0'+m[2]%60).slice(-2)+'–'+Math.floor(m[3]/60)+':'+('0'+m[3]%60).slice(-2),
    'Walking street, '+Math.floor(m[2]/60)+':'+('0'+m[2]%60).slice(-2)+'–'+Math.floor(m[3]/60)+':'+('0'+m[3]%60).slice(-2)));});
 (D.fe||[]).forEach(function(f){
  if(day.iso>=f[0]&&day.iso<=f[1])
   out.push(icon('i-lantern')+'<a href="festivals/'+esc(f[4])+'.html">'+B(f[2],f[3])+'</a>');});
 return out;}

function paintHead(){
 var day=dayOf(sel.k),x=fc(day.dow,sel.h,day.mon),b=band(x.c);
 var box=document.getElementById('tnow');box.style.setProperty('--b',b[1]);box.style.setProperty('--bi',b[4]);
 var wth=(sel.k===0?'วันนี้ ':sel.k===1?'พรุ่งนี้ ':'')+DTH[day.dow]+' '+pad(sel.h);
 var wen=(sel.k===0?'Today, ':sel.k===1?'Tomorrow, ':'')+DEN[day.dow]+' '+pad(sel.h);
 document.getElementById('twhen').innerHTML=B(wth,wen);
 document.getElementById('tword').innerHTML=B(b[2],b[3]);
 document.getElementById('tmin').innerHTML=B('ทาง 10 นาที ใช้ '+Math.round(x.min)+' นาที','A 10-minute drive takes '+Math.round(x.min));
 document.getElementById('tsub').innerHTML=B('ในเมืองเชียงใหม่ ช้ากว่าถนนโล่ง '+Math.round(x.c)+'% · เฉลี่ย '+Math.round(x.kmh)+' กม./ชม.',
  'Central Chiang Mai, '+Math.round(x.c)+'% slower than an empty road · '+Math.round(x.kmh)+' km/h');
 var ctx=context(day,sel.h),cx=document.getElementById('tctx');
 cx.innerHTML=ctx.map(function(s){return '<span class="tline">'+s+'</span>';}).join('');cx.hidden=!ctx.length;
 paintWait(day);}

/* Leave now or wait: only for the reader's own hour. The first hour in the
   next three that saves a whole minute on a 10-minute trip. */
function paintWait(day){
 var w=document.getElementById('twait'),now=bkk(Date.now());
 if(sel.k!==0||sel.h!==now.h){w.hidden=true;return;}
 var here=fc(day.dow,sel.h,day.mon).min,best=null;
 for(var i=1;i<=3&&!best;i++){var t=bkk(Date.now()+i*3600e3),m=fc(t.dow,t.h,t.mon).min;
  if(m<=here-1)best={h:t.h,m:m};}
 if(best)w.innerHTML=B('รอถึง '+pad(best.h)+' ทาง 10 นาที จะใช้ '+Math.round(best.m)+' นาที แทน '+Math.round(here),
  'Wait until '+pad(best.h)+' and a 10-minute drive takes '+Math.round(best.m)+' instead of '+Math.round(here));
 else w.innerHTML=B('ตอนนี้ไม่แย่กว่า 3 ชั่วโมงข้างหน้า','The next three hours are no clearer than now');
 w.hidden=false;}

function paintStrip(){
 var day=dayOf(sel.k),now=bkk(Date.now());
 document.querySelectorAll('.tbar').forEach(function(b){
  var h=+b.dataset.h,x=fc(day.dow,h,day.mon);
  b.style.setProperty('--h',Math.min(100,8+x.c*0.9)+'%');
  b.style.setProperty('--b',band(x.c)[1]);
  b.classList.toggle('on',h===sel.h);
  b.classList.toggle('now',sel.k===0&&h===now.h);
  b.setAttribute('aria-label',pad(h)+' · '+Math.round(x.min)+' นาที/min');
  b.setAttribute('aria-pressed',h===sel.h?'true':'false');});
 document.querySelectorAll('.tday').forEach(function(b){b.setAttribute('aria-pressed',+b.dataset.k===sel.k?'true':'false');});}

function paintWeek(){
 var mon=dayOf(sel.k).mon,dsel=dayOf(sel.k).dow;
 document.getElementById('tmon').innerHTML=B('เดือน '+MTH[mon],'Month: '+MEN[mon]);
 document.querySelectorAll('.tcell').forEach(function(b){
  var d=+b.dataset.d,h=+b.dataset.h,x=fc(d,h,mon);
  b.style.setProperty('--b',band(x.c)[1]);b.textContent=Math.round(x.min);
  b.classList.toggle('on',d===dsel&&h===sel.h);});}

/* ---- the map ------------------------------------------------------------ */
function cellSet(h){return h>=6&&h<=10?3:h>=15&&h<=20?4:2;}
function hexData(){
 var day=dayOf(sel.k),x=fc(day.dow,sel.h,day.mon),col=cellSet(sel.h);
 var ref=col===3?D.am[1]:col===4?D.pm[1]:D.yc,r=x.c/ref,T=D.hx.t,f=[];
 D.hx.c.forEach(function(c){
  var s=c[col]*r;if(s<15)return;
  var ring=T.map(function(o){return[c[0]+o[0],c[1]+o[1]];});ring.push(ring[0]);
  f.push({type:'Feature',properties:{s:Math.round(s)},geometry:{type:'Polygon',coordinates:[ring]}});});
 return{type:'FeatureCollection',features:f};}
function roadData(){
 var f=[];
 D.r.forEach(function(r,i){
  var lines=r[8].map(function(fl){var l=[];for(var j=0;j<fl.length;j+=2)l.push([fl[j],fl[j+1]]);return l;});
  f.push({type:'Feature',id:i,properties:{i:i,g:r[7]||'?',v:r[4]},
   geometry:{type:'MultiLineString',coordinates:lines}});});
 return{type:'FeatureCollection',features:f};}
function firstSymbol(m){var ls=m.getStyle().layers||[];
 for(var i=0;i<ls.length;i++)if(ls[i].type==='symbol')return ls[i].id;return undefined;}
function mountMap(m){
 map=m;var before=firstSymbol(m);
 var steps=['step',['get','s']];BANDS.forEach(function(b,i){if(i===0)steps.push(b[1]);else steps.push(b[0],b[1]);});
 m.addSource('thex',{type:'geojson',data:hexData()});
 m.addLayer({id:'thex',type:'fill',source:'thex',paint:{'fill-color':steps,
  'fill-opacity':['interpolate',['linear'],['get','s'],15,0.25,60,0.5,100,0.62]}},before);
 var gc=['match',['get','g']];Object.keys(G).forEach(function(k){gc.push(k,G[k][0]);});gc.push('#6d5411');
 var wd=['interpolate',['linear'],['get','v'],2000,1.5,40000,4,120000,8];
 m.addSource('troad',{type:'geojson',data:roadData()});
 m.addLayer({id:'troad-case',type:'line',source:'troad',layout:{'line-cap':'round','line-join':'round'},
  paint:{'line-color':'#ffffff','line-width':['+',wd,2.5]}},before);
 m.addLayer({id:'troad',type:'line',source:'troad',layout:{'line-cap':'round','line-join':'round'},
  paint:{'line-color':gc,'line-width':wd}},before);
 m.on('click',function(e){
  var p=e.point,hit=m.queryRenderedFeatures([[p.x-14,p.y-14],[p.x+14,p.y+14]],{layers:['troad']});
  if(!hit.length)return;
  var r=D.r[hit[0].properties.i],g=G[r[7]];
  var n=r[4].toLocaleString('en-US'),mc=r[5].toLocaleString('en-US');
  /* Both cards read these: md.js prints name/sub/dist, tap.js name/nameEn/
     subWords/where/dist. */
  if(window.MDCARD)window.MDCARD.show({
   name:'ทางหลวง '+r[0]+' · '+r[2],nameEn:'Highway '+r[0]+' · '+r[3],
   sub:'รถยนต์ รถบัส รถบรรทุก '+n+' คัน/วัน · '+n+' cars, buses and trucks a day',
   subWords:['รถยนต์ รถบัส รถบรรทุก '+n+' คัน/วัน',n+' cars, buses and trucks a day'],
   where:'มอเตอร์ไซค์ '+mc+' คัน/วัน · '+mc+' motorcycles a day',
   dist:(g?'ชั่วโมงที่ติดที่สุด ระดับ '+r[7]+' '+g[1]+' · busiest hour, grade '+r[7]+', '+g[2]+' · ':'')+
    'กรมทางหลวง '+D.ry+' · DOH'},el);});
 m.on('mousemove',function(e){var p=e.point;
  m.getCanvas().style.cursor=m.queryRenderedFeatures([[p.x-8,p.y-8],[p.x+8,p.y+8]],{layers:['troad']}).length?'pointer':'';});}
function paintMap(){if(map&&map.getSource('thex'))map.getSource('thex').setData(hexData());}
var VIEWS={city:[[98.93,18.72],[99.06,18.87]],cm:[[98.0,17.8],[99.6,20.1]],cr:[[99.3,19.4],[100.6,20.5]]};

function paint(){paintHead();paintStrip();paintWeek();paintMap();}
function wire(){
 document.getElementById('tdays').addEventListener('click',function(e){
  var b=e.target.closest('.tday');if(!b)return;sel.k=+b.dataset.k;paint();});
 document.getElementById('tstrip').addEventListener('click',function(e){
  var b=e.target.closest('.tbar');if(!b)return;sel.h=+b.dataset.h;paint();});
 document.getElementById('tweek').addEventListener('click',function(e){
  var b=e.target.closest('.tcell');if(!b)return;
  var d=+b.dataset.d,today=bkk(Date.now()).dow;sel.k=(d-today+7)%7;sel.h=+b.dataset.h;paint();
  document.getElementById('tnow').scrollIntoView({behavior:'smooth',block:'start'});});
 function step(n){sel.h+=n;if(sel.h>23){if(sel.k<6){sel.k++;sel.h=0;}else sel.h=23;}
  if(sel.h<0){if(sel.k>0){sel.k--;sel.h=23;}else sel.h=0;}paint();}
 document.getElementById('tprev').addEventListener('click',function(){step(-1);});
 document.getElementById('tnext').addEventListener('click',function(){step(1);});
 document.getElementById('tnowb').addEventListener('click',function(){sel={k:0,h:bkk(Date.now()).h};paint();});
 document.querySelectorAll('.tview').forEach(function(b){b.addEventListener('click',function(){
  document.querySelectorAll('.tview').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
  if(map)map.fitBounds(VIEWS[b.dataset.v],{padding:20,duration:900});});});}

function start(json){D=json;sel={k:0,h:bkk(Date.now()).h};wire();paint();
 if(window.MDMAP&&el)window.MDMAP.ready(el,mountMap);}
var v='';try{v=JSON.parse(document.getElementById('tdata-src').textContent).v;}catch(e){}
fetch('data/traffic.json?v='+v).then(function(r){return r.json();}).then(start)
 .catch(function(){/* the page as built stands: the grid, the table and the drawn map */});
})();
"""


def main():
    import build  # importing does not build: build() runs under __main__ only
    if not (build.DOCS / "index.html").exists():
        raise SystemExit("docs/ is not built yet — run python3 build.py first")
    g = vars(build)
    if "translit" not in g:
        import translit
        g = dict(g, translit=translit)
    print(emit(g))


if __name__ == "__main__":
    main()
