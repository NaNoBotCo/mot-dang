#!/usr/bin/env python3
"""/nam.html — น้ำ, the Ping right now. WO-57 item 5.

WHAT THIS PAGE IS NOT, first, because the proposal it comes from was for
something else. WO-57 offered a flood layer built on the SRTM tiles already
cached here: every pin's ground height, beside its distance from the river.
That was priced and refused in the same paragraph — z12 terrain is ~38 m a
cell with 5–10 m of vertical error, so a page built on it would answer "does
my house flood" with a model that cannot tell one soi from the next. The cost
of being wrong there is somebody staying put.

WHAT IS TRUE INSTEAD, and it turned out to be better. The Royal Irrigation
Department publishes hourly stage and discharge for every gauge on the Ping,
and every row carries THE STATION'S OWN ALERT LEVEL. P.1 at Nawarat Bridge
states 3.70 m. So this page never models anything: it prints the reading, the
register's own limit beside it, the last six hours of arithmetic, and the
river drawn in the order the water passes — Chiang Dao, Cho Lae, Mae Tae,
Nawarat, Pa Khoi Tai — so a reader can see what is upstream of them before it
arrives.

THE ONE COMPUTED NUMBER, and it is computed rather than repeated. Everyone
here says the water takes six to eight hours from Mae Tae to Nawarat.
importers/make_ping.py cross-correlates the two hourly series over thirty days
and prints the lag that fits best WITH its correlation, so a weak answer looks
weak. It is a measurement of the last thirty days, labelled as one, and not a
promise about the next flood.

NO FORECAST, NO ADVICE, NO CREST. Those belong to ปภ. and to the municipality,
and the page says so and gives 1784 rather than an opinion.

Entry point: emit(globals_of_build, data).
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def pct(s):
    if not s.get("limit"):
        return None
    return 100.0 * s["level"] / s["limit"]


def band_colour(p):
    """Four steps, on the station's OWN limit — never a scale of ours.

    Below two thirds, between two thirds and the limit, at or over the limit.
    The colours are the site's, the thresholds are arithmetic on the
    register's number."""
    if p is None:
        return "#8a8a8a"
    if p >= 100:
        return "#d1495b"
    if p >= 80:
        return "#f08a3c"
    if p >= 66:
        return "#f6c445"
    return "#3bb2d0"


def spark(g, st):
    """Seven days of hourly stage, drawn against the station's own limit.

    The limit is a line across the picture, not a colour change: a reader
    should be able to see how much room is left without reading a number."""
    esc = g["esc"]
    pts = st.get("hours") or []
    if len(pts) < 4:
        return ""
    lo = min(v for _t, v in pts)
    hi = max([v for _t, v in pts] + [st.get("limit") or 0])
    span = (hi - lo) or 1.0
    n = len(pts)
    d = " ".join(
        f'{100.0 * i / (n - 1):.2f},{100.0 * (1 - (v - lo) / span):.2f}'
        for i, (_t, v) in enumerate(pts))
    limit_y = (100.0 * (1 - ((st["limit"] - lo) / span))
               if st.get("limit") is not None else None)
    line = ""
    if limit_y is not None and -5 <= limit_y <= 105:
        line = (f'<line x1="0" y1="{limit_y:.2f}" x2="100" y2="{limit_y:.2f}" '
                f'stroke="#d1495b" stroke-width="1" stroke-dasharray="3 2" '
                f'vector-effect="non-scaling-stroke"/>')
    return (f'<svg class="nm-spark" viewBox="0 0 100 100" '
            f'preserveAspectRatio="none" role="img" aria-label="'
            f'{esc(g["bi_text"]("ระดับน้ำ 7 วัน", "seven days of stage"))}">'
            f'{line}<polyline points="{d}" fill="none" stroke="currentColor" '
            f'stroke-width="1.4" vector-effect="non-scaling-stroke"/></svg>')


def station_row(g, st, city=False):
    bi, esc = g["bi"], g["esc"]
    p = pct(st)
    ch = st.get("change6h")
    arrow = "—" if not ch else ("↑" if ch > 0 else "↓")
    chtxt = ("" if ch is None else
             f'<span class="nm-ch">{arrow} {abs(ch):.2f} m'
             f'<small>{bi("/6 ชม.", "/6h", sep="")}</small></span>')
    bar = ("" if p is None else
           f'<span class="nm-bar"><i style="width:{min(p, 100):.1f}%;'
           f'background:{band_colour(p)}"></i></span>')
    lim = ("" if not st.get("limit") else
           f'<span class="nm-lim">{bi("ระดับเตือนภัยของสถานี", "the station’s own limit")} '
           f'<b>{st["limit"]:.2f} m</b></span>')
    return (f'<div class="nm-st{" city" if city else ""}">'
            f'<div class="nm-head"><span class="nm-id">{esc(st["id"])}</span>'
            f'<span class="nm-nm">{bi(st["th"], st["en"])}</span>'
            f'<span class="nm-where">{esc(st.get("river_th", ""))} · '
            f'{esc(st.get("amphoe", ""))} {esc(st.get("province", ""))}</span>'
            f'</div>'
            f'<div class="nm-read"><span class="nm-lv">{st["level"]:.2f}'
            f'<small> m</small></span>'
            + (f'<span class="nm-pct">{p:.0f}%</span>' if p is not None else "")
            + chtxt + '</div>'
            f'{bar}{lim}{spark(g, st)}</div>')


def emit(g, data):
    DOCS, ROOT_ = g["DOCS"], g["ROOT"]
    src_f = ROOT_ / "data" / "ping.json"
    if not src_f.exists():
        return "SKIPPED — no data/ping.json (importers/make_ping.py)"
    bi, esc, att = g["bi"], g["esc"], g["att"]
    doc = json.loads(src_f.read_text(encoding="utf-8"))
    sts = doc["stations"]
    city = next((s for s in sts if s["id"] == doc["city_station"]), None)
    chain = [s for s in sts if s.get("chain")]
    tribs = [s for s in sts if not s.get("chain")]
    src = doc["source"]
    lag = doc.get("lag") or {}

    (DOCS / "nam.css").write_text(CSS)

    p = pct(city) if city else None
    head = ""
    if city:
        head = (
            f'<div class="nm-city" style="--band:{band_colour(p)}">'
            f'<span class="nm-cnum">{city["level"]:.2f}<small> m</small></span>'
            f'<span class="nm-cof">{bi("จากระดับเตือนภัย", "of the alert level")} '
            f'<b>{city["limit"]:.2f} m</b> '
            f'({p:.0f}%)</span>'
            f'<span class="nm-cwhen">{esc(city["id"])} {bi(city["th"], city["en"])} · '
            f'{esc(city["observed"].replace("T", " "))} · '
            f'{esc(str(city["dischg"]))} {bi("ลบ.ม./วิ", "m³/s")}</span></div>')

    lagline = ""
    if lag.get("hours") is not None:
        lagline = (
            f'<p class="nm-lag">'
            + bi(f"วัดจากข้อมูลจริง {lag['window_days']} วันหลังสุด: ระดับน้ำที่ {lag['from']} "
                 f"มาถึง {lag['to']} ช้ากว่าราว {lag['hours']} ชั่วโมง "
                 f"(ค่าสหสัมพันธ์ {lag['r']} จาก {lag['hours_compared']:,} ชั่วโมงที่เทียบได้) "
                 f"— เป็นการวัดของช่วงที่ผ่านมา ไม่ใช่คำทำนายของครั้งหน้า",
                 f"Measured from the last {lag['window_days']} days of the register's own "
                 f"readings: the stage at {lag['from']} shows up at {lag['to']} about "
                 f"{lag['hours']} hours later (r={lag['r']} across "
                 f"{lag['hours_compared']:,} compared hours). That is a measurement of "
                 f"the days behind us, not a promise about the next flood.")
            + '</p>')

    body = (
        f'<h1>🌊 {bi("น้ำ — แม่น้ำปิง ตอนนี้", "Water — the Ping right now")}</h1>'
        f'<p class="lede">'
        + bi("ระดับน้ำรายชั่วโมงจากสถานีของกรมชลประทาน พร้อมระดับเตือนภัยที่สถานีนั้นประกาศเอง "
             "เรียงตามลำน้ำจากต้นน้ำลงมาถึงในเมือง",
             "Hourly stage from the Irrigation Department's own gauges, each shown "
             "against the alert level that station itself publishes, in the order "
             "the water passes on its way into the city.")
        + '</p>'
        + head + lagline +
        f'<h2>{bi("ตามลำน้ำปิง", "Down the Ping")}</h2>'
        f'<p class="tinynote">'
        + bi("บนลงล่างคือทิศทางที่น้ำไหล เส้นประแดงในกราฟคือระดับเตือนภัยของสถานีนั้น",
             "Top to bottom is the way the water goes. The dashed red line in each "
             "chart is that station's own alert level.")
        + '</p>'
        f'<div class="nm-chain">'
        + "".join(station_row(g, s, s["id"] == doc["city_station"]) for s in chain)
        + '</div>'
        f'<h2>{bi("ลำน้ำสาขา", "The tributaries")}</h2>'
        f'<div class="nm-grid">'
        + "".join(station_row(g, s) for s in tribs) + '</div>'
        f'<h2>{bi("มาตรวัด", "Gauge readings")}</h2>'
        f'<p class="nm-not">'
        + bi("หน้านี้บอกว่ามาตรวัดอ่านได้เท่าไร ระดับเตือนภัยของแต่ละสถานีเป็นเท่าไร และหกชั่วโมงที่ผ่านมาขึ้นหรือลงเท่าไร "
             "การเตือนภัยเป็นของกรมป้องกันและบรรเทาสาธารณภัยและเทศบาล — สายด่วน 1784",
             "This page says what the gauges read, what each station's own alert level "
             "is, and which way the last six hours went. It does not say when the river "
             "crests, who should move what, or whose house floods. Warnings belong to "
             "ปภ. and the municipality — the hotline is 1784.")
        + f' <a class="nm-sos" href="tel:1784">☎ 1784</a> '
        f'<a href="chuai.html">🆘 '
        + bi("เบอร์ฉุกเฉินและที่ใกล้ที่สุด", "Emergency numbers and what is nearest")
        + '</a></p>'
        f'<p class="tinynote">'
        + bi(f"ที่มา: {src['name']} · อ่านเมื่อ {doc['generated'][:16].replace('T', ' ')} · "
             f"{src['note_th']}",
             f"Source: {src['en']}, read {doc['generated'][:16].replace('T', ' ')}. "
             f"{src['note_en']}")
        + f' <a href="{att(src["url"])}" rel="noopener">hydro-1.net</a>'
        f' · <a href="data/ping.json">ping.json</a></p>'
        + g["share_block"](g["BASE"] + "nam.html",
                           "น้ำ · แม่น้ำปิงตอนนี้ — มดแดง"))

    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "ping.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    html = g["page"](
        "น้ำ — ระดับน้ำแม่น้ำปิง สะพานนวรัฐ P.1 ตอนนี้ เทียบระดับเตือนภัย",
        body, depth=0, path="nam.html",
        desc="ระดับน้ำแม่น้ำปิงรายชั่วโมงที่สะพานนวรัฐ (P.1) และสถานีต้นน้ำ "
             "เทียบกับระดับเตือนภัยที่กรมชลประทานประกาศเอง · Hourly Ping River "
             "levels at Nawarat Bridge and upstream, against the Irrigation "
             "Department's own alert levels.",
        extra_head='<link rel="stylesheet" href="nam.css">',
        crumbs='<a href="index.html">มดแดง</a> › ' + bi("น้ำ", "The river"))
    (DOCS / "nam.html").write_text(html)

    return (f'{len(sts)} gauges, {doc["city_station"]} at '
            f'{city["level"]:.2f}/{city["limit"]:.2f} m ({p:.0f}%), '
            f'lag {lag.get("hours")} h r={lag.get("r")}, '
            f'page {len(html.encode()) / 1024:.0f} kB')


CSS = """/* nam.css — generated by nam_layer.py */
.nm-city{display:grid;gap:.1rem .8rem;background:var(--card);
border-left:8px solid var(--band);border-radius:.6rem;padding:.8rem 1rem;
margin:1rem 0}
.nm-cnum{font-size:3rem;font-weight:700;line-height:1}
.nm-cnum small{font-size:1rem;font-weight:400;color:var(--ink-soft)}
.nm-cof b{font-size:1.1rem}
.nm-cwhen{font-size:.82rem;color:var(--ink-soft)}
.nm-lag{max-width:62ch;border-left:3px solid var(--gloss);padding-left:.7rem}
.nm-chain{display:flex;flex-direction:column;gap:.5rem;margin:.6rem 0 1.4rem;
position:relative}
.nm-chain:before{content:"";position:absolute;left:.9rem;top:.6rem;bottom:.6rem;
width:3px;background:var(--card-alt);border-radius:2px}
.nm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));
gap:.6rem;margin:.6rem 0 1.2rem}
.nm-st{background:var(--card);border:2px solid var(--card-alt);
border-radius:.6rem;padding:.5rem .8rem;position:relative}
.nm-chain .nm-st{margin-left:2.1rem}
.nm-chain .nm-st:before{content:"";position:absolute;left:-1.35rem;top:1rem;
width:.7rem;height:.7rem;border-radius:50%;background:var(--ink);
box-shadow:0 0 0 3px var(--paper)}
.nm-st.city{border-color:var(--ant-dark);border-width:3px}
.nm-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.2rem .5rem}
.nm-id{font-weight:700;font-size:.78rem;letter-spacing:.05em;
border:1.5px solid var(--ink);border-radius:.3rem;padding:0 .3em}
.nm-nm{font-weight:700}
.nm-where{font-size:.78rem;color:var(--ink-soft)}
.nm-read{display:flex;flex-wrap:wrap;align-items:baseline;gap:.15rem .7rem;
margin:.15rem 0}
.nm-lv{font-size:1.6rem;font-weight:700;line-height:1;
font-variant-numeric:tabular-nums}
.nm-lv small{font-size:.75rem;font-weight:400;color:var(--ink-soft)}
.nm-pct{font-weight:700;font-variant-numeric:tabular-nums}
.nm-ch{color:var(--ink-soft);font-variant-numeric:tabular-nums}
.nm-ch small{font-size:.78em}
.nm-bar{display:block;height:.55rem;background:var(--card-alt);
border-radius:.3rem;overflow:hidden;margin:.25rem 0 .2rem}
.nm-bar i{display:block;height:100%}
.nm-lim{display:block;font-size:.78rem;color:var(--ink-soft)}
.nm-spark{display:block;width:100%;height:2.6rem;margin-top:.3rem;
color:var(--ink-soft)}
.nm-not{max-width:62ch}
.nm-sos{font-weight:700;text-decoration:none;color:var(--ant-dark);
border:2px solid var(--ant-dark);border-radius:2rem;padding:.05rem .6rem;
white-space:nowrap}
"""


if __name__ == "__main__":
    print("This layer runs from build.py — it needs its helpers. "
          "Run: python3 build.py")
