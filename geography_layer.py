#!/usr/bin/env python3
"""ดอย — the land the directory sits on, in three dimensions (/doi.html). WO-37.

Three things a reader asks about the ground, in the order they ask them:

  1. WHAT DOES IT LOOK LIKE — the basemap with real relief under it: hillshade
     over the same self-hosted tiles every other map uses, and a 3D mode that
     tilts the camera and raises the ranges. Opt-in, always — the button acts,
     the page never performs. The third dimension arrives the way the second
     did: one .pmtiles file in our own bucket (importers/build_terrain.py is
     the fetch and the bind), ranges only, no key, nobody's logs but ours.
  2. WHAT THE NUMBERS ARE — heights as an instrument's readings, dated, with
     the instrument named: the highest cell the model holds in the frame, the
     basin floor at ประตูท่าแพ, and a west–east cut through the gate drawn
     from the same file the map reads. No view is ranked; the doi do not
     compete. The summit sign keeps its own number; ours carries a read date.
  3. WHAT THE NAMES MEAN — ดอย ม่อน ขุน แม่ ห้วย ผา โป่ง แอ่ง น้ำตก: nine
     words that turn a bus timetable into a relief map. Place-names are the
     oldest elevation data this valley has.

The fallback story is the site's usual one, run in reverse: the drawn
cross-section is the no-script, no-tiles, on-paper picture, and it is not a
lesser copy of the live map — it is the one artefact here the live map cannot
show. With tiles it moves below the mount and keeps its own section.

Entry point: emit(globals_of_build, data) — hooked in build.py after the
hot-springs layer. Reads data/terrain_meta.json + data/terrain_profile.json
(written by importers/build_terrain.py --read-back half, Pillow optional
there); with neither on disk this page is skipped and says so, the same
supported absence as every other instrument on this site.
"""
import json
import math
import zlib
from pathlib import Path

import map_shell

ROOT = Path(__file__).resolve().parent
META = ROOT / "data" / "terrain_meta.json"
PROFILE = ROOT / "data" / "terrain_profile.json"

CSS = """/* /doi.html — the land under the directory. */
.doimap{height:min(70vh,600px);margin:.5rem 0 .2rem}
@media (min-width:760px){.doimap{height:min(74vh,680px)}}
.doimap .mdmap-draw{height:100%}
.doi-fallback{height:100%;display:grid;align-content:center;gap:.4rem;
  background:var(--soft,#F6EFE3);border-radius:14px;padding:1rem}
.doimap.mdmap-on .doi-fallback{display:none}
#doibar{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.6rem 0 .2rem}
/* Size and squish only. The colours — resting, pressed, after dark — belong
   to the design layer at the end of build.py's CSS, which already dresses
   buttons and their aria-pressed state sitewide; a second palette here
   fought it and lost, half-inverted. Retune the variables, not the rules. */
.doibtn{min-height:46px;padding:.5rem .95rem;border-radius:.7rem;font:inherit;
  font-size:.98rem;cursor:pointer;transition:transform .12s ease}
.doibtn:active{transform:scale(.96)}
.doiseg{display:inline-flex;gap:.35rem;flex-wrap:wrap}
.doi-rule{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;
  background:var(--soft);border:1px solid rgba(0,0,0,.07);font-size:.98rem}
.doi-rule b{display:block;margin-bottom:.15rem}
.doi-facts{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));
  margin:.6rem 0}
.doi-fact{padding:.8rem .95rem;border:1px solid rgba(0,0,0,.08);border-radius:.8rem;
  background:var(--card,#fff)}
.doi-fact .big{font-size:1.9rem;font-weight:700;line-height:1.15;display:block}
.doi-fact small{color:var(--mute)}
.doi-sect{border:1px solid rgba(0,0,0,.08);border-radius:.8rem;
  background:var(--card,#fff);padding:.7rem .8rem .4rem;margin:.6rem 0 .2rem}
.doi-sect svg{display:block;width:100%;height:auto}
.doi-method{color:var(--mute);font-size:.85rem;margin:.3rem 0 .9rem}
.doi-words{margin:.2rem 0;padding-left:1.1rem}
.doi-words li{margin:.26rem 0}
.doi-note{color:var(--mute);font-size:.9rem}
/* One ink set, no dark fork: the site's paper stays cream in every mode, so
   a media-query palette here painted half the drawing for a night that never
   comes. Fixed inks, like every other drawn map on this site. */
.doi-grid{stroke:rgba(42,30,22,.14);stroke-width:1}
.doi-area{fill:#E2D2AC}
.doi-line{stroke:#4A3A28;stroke-width:2;fill:none}
.doi-lab{font-size:12px;fill:#5a4f42}
.doi-lab2{font-size:12.5px;font-weight:600;fill:#3d3428}
.doi-axis{font-size:10.5px;fill:#8a7a62}
.doi-tick{stroke:#8a7a62;stroke-width:1.4}
@media (prefers-reduced-motion:reduce){.doibtn{transition:none}}
"""

# doi.js — everything below runs only on /doi.html, and only once map.js has
# mounted the shared basemap. It draws INTO the map through MDMAP.ready(),
# the same door explore.js uses; this file never constructs a map and never
# names a tile URL of its own — the elevation source rides in MDMAP_CFG,
# placed there by map_shell.emit() from data/basemap.json, which stays the
# one place on this site tiles are configured.
JS = r"""/* doi.js — /doi.html only. The third dimension, opt-in. */
(function(){
var box=document.getElementById('doimap');
if(!box||!window.MDMAP||!window.MDMAP_CFG)return;
var T=window.MDMAP_CFG.terrain;
if(!T||!T.url)return;
MDMAP.ready(box,function(map){
  /* Resolved against the SITE root, exactly as map.js resolves the basemap —
     the same two traps, the same cure. */
  var ROOT=document.documentElement.getAttribute('data-root')||'';
  var ABS=new URL(T.url,new URL(ROOT||'./',location.href)).href;
  if(!map.getSource('doidem')){
    map.addSource('doidem',{type:'raster-dem',url:'pmtiles://'+ABS,
      encoding:T.encoding||'terrarium',tileSize:256,maxzoom:T.maxzoom||12,
      attribution:'ความสูง · elevation: Mapzen terrain tiles / SRTM (NASA, USGS)'});
    /* Hillshade sits under the water, so rivers and the moat keep their ink
       over the relief. The first of these ids present wins; a retuned style
       that renames them all leaves the shading on top of fills, which is
       visible and shippable rather than silently absent. */
    var before=null;
    ['water','water-line','buildings','roads-casing','roads-minor']
      .some(function(id){if(map.getLayer(id)){before=id;return true}return false;});
    map.addLayer({id:'doi-hills',type:'hillshade',source:'doidem',paint:{
      'hillshade-exaggeration':0.58,
      'hillshade-illumination-anchor':'map',
      'hillshade-illumination-direction':335,
      'hillshade-shadow-color':'#59452F',
      'hillshade-highlight-color':'#FFFDF4',
      'hillshade-accent-color':'#6E5A40'}},before||undefined);
  }
  /* The controls appear only now — a button that cannot act yet is worse
     than no button, and with no basemap none of these can act. */
  var bar=document.getElementById('doibar');
  if(bar)bar.hidden=false;
  function rm(){return matchMedia('(prefers-reduced-motion:reduce)').matches;}

  var b3=document.getElementById('doi3d'),on=false;
  function set3d(want){
    on=want;
    if(on){
      map.setTerrain({source:'doidem',exaggeration:1.35});
      map[rm()?'jumpTo':'easeTo']({pitch:60,duration:rm()?0:900});
    }else{
      map[rm()?'jumpTo':'easeTo']({pitch:0,duration:rm()?0:700});
      map.setTerrain(null);
    }
    if(b3)b3.setAttribute('aria-pressed',on?'true':'false');
    box.classList.toggle('doi-3d',on);
  }
  if(b3)b3.addEventListener('click',function(){set3d(!on);});

  var seg=[].slice.call(document.querySelectorAll('#doibar .doilight'));
  seg.forEach(function(b){b.addEventListener('click',function(){
    if(map.getLayer('doi-hills'))
      map.setPaintProperty('doi-hills','hillshade-illumination-direction',
        parseFloat(b.dataset.az)||335);
    seg.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false');});
  });});

  /* The one flight on the page, and the reader books it. The coordinate is
     the instrument's own — data-lat/lng come from terrain_meta.json through
     the page, so the button and the facts card can never disagree. */
  var fly=document.getElementById('doitop');
  if(fly)fly.addEventListener('click',function(){
    var la=parseFloat(fly.dataset.lat),ln=parseFloat(fly.dataset.lng);
    if(!isFinite(la)||!isFinite(ln))return;
    if(!on)set3d(true);
    map[rm()?'jumpTo':'flyTo']({center:[ln,la],zoom:11.6,
      duration:rm()?0:2600});
  });
});
})();
"""


def _fmt(n):
    return "{:,.0f}".format(float(n))


def _profile_svg(prof, meta, bi_text, esc):
    """The basin, cut west to east through ประตูท่าแพ and drawn to be read:
    a metres axis, the ridge and the rim named, the gate marked, the vertical
    stretch stated. This is the page's on-paper, no-script picture — the one
    frame here the live map cannot draw."""
    ele = prof["ele"]
    lon_a, lon_b, step = prof["lon_a"], prof["lon_b"], prof["step"]
    lat0 = prof["lat"]
    n = len(ele)
    lons = [lon_a + i * step for i in range(n)]

    W, H = 760, 320
    PADL, PADR, PADT, PADB = 56, 16, 26, 36
    top = 1800.0
    plot_w, plot_h = W - PADL - PADR, H - PADT - PADB

    def X(lon):
        return PADL + (lon - lon_a) / (lon_b - lon_a) * plot_w

    def Y(e):
        return PADT + (top - max(0.0, min(top, e))) / top * plot_h

    pts = " ".join("%.1f,%.1f" % (X(lons[i]), Y(ele[i])) for i in range(n))
    base = PADT + plot_h
    area = ("M%.1f,%.1f L" % (PADL, base)) + pts.replace(" ", " L") + \
           (" L%.1f,%.1f Z" % (X(lons[-1]), base))

    grid, axis = [], []
    for m in (0, 500, 1000, 1500):
        y = Y(m)
        grid.append('<line class="doi-grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>'
                    % (PADL, y, W - PADR, y))
        axis.append('<text class="doi-axis" x="%d" y="%.1f" text-anchor="end">%s</text>'
                    % (PADL - 6, y + 3.5, _fmt(m)))
    axis.append('<text class="doi-axis" x="%d" y="%.1f">ม. · m</text>'
                % (PADL - 44, PADT - 8))

    # The two heights the drawing names are found in the data, never typed.
    iw = max((i for i in range(n) if lons[i] < 98.95),
             key=lambda i: ele[i])
    ie = max((i for i in range(n) if lons[i] > 99.18),
             key=lambda i: ele[i])
    marks = []
    marks.append('<text class="doi-lab2" x="%.1f" y="%.1f" text-anchor="middle">'
                 'ดอยปุย–ดอยสุเทพ</text>' % (X(lons[iw]) + 26, Y(ele[iw]) - 18))
    marks.append('<text class="doi-lab" x="%.1f" y="%.1f" text-anchor="middle">'
                 '%s ม.</text>' % (X(lons[iw]) + 26, Y(ele[iw]) - 5, _fmt(ele[iw])))
    marks.append('<text class="doi-lab2" x="%.1f" y="%.1f" text-anchor="middle">'
                 'ขอบตะวันออก</text>' % (X(lons[ie]), Y(ele[ie]) - 18))
    marks.append('<text class="doi-lab" x="%.1f" y="%.1f" text-anchor="middle">'
                 '%s ม.</text>' % (X(lons[ie]), Y(ele[ie]) - 5, _fmt(ele[ie])))

    tp = meta.get("tha_phae") or {}
    xg = X(float(tp.get("lng", 98.9931)))
    marks.append('<line class="doi-tick" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (xg, base, xg, base - 16))
    marks.append('<text class="doi-lab" x="%.1f" y="%.1f" text-anchor="middle">'
                 'ประตูท่าแพ %s ม.</text>'
                 % (xg, base - 21, _fmt(tp.get("ele", 0))))
    marks.append('<text class="doi-lab" x="%.1f" y="%.1f" text-anchor="middle" '
                 'opacity=".75">แอ่งเชียงใหม่</text>'
                 % ((X(98.99) + X(99.16)) / 2, Y(0) - 46))

    # A bar that is true at this drawing's own scale, and the stretch printed
    # beside it rather than hidden: the picture says how it was made.
    m_per_px_x = (lon_b - lon_a) * 111.32 * math.cos(math.radians(lat0)) * 1000 / plot_w
    m_per_px_y = top / plot_h
    vx = m_per_px_x / m_per_px_y
    km10 = 10000 / m_per_px_x
    bar = ('<g><line x1="%d" y1="%d" x2="%.1f" y2="%d" class="doi-tick"/>'
           '<text class="doi-axis" x="%d" y="%d">10 กม. · km</text></g>'
           % (PADL, H - 10, PADL + km10, H - 10, PADL, H - 16))

    label = bi_text(
        "ภาพตัดความสูงตะวันตก–ตะวันออกผ่านประตูท่าแพ: สันดอยปุย–ดอยสุเทพ "
        "แอ่งเมืองเชียงใหม่ และขอบดอยด้านตะวันออก",
        "West to east height profile through Tha Phae Gate: the Doi Pui and "
        "Doi Suthep ridge, the Chiang Mai basin, and the eastern rim")
    return ('<svg role="img" aria-label="%s" viewBox="0 0 %d %d" '
            'xmlns="http://www.w3.org/2000/svg">%s%s'
            '<path class="doi-area" d="%s"/>'
            '<polyline class="doi-line" points="%s"/>%s%s</svg>'
            % (esc(label), W, H, "".join(grid), "".join(axis),
               area, pts, "".join(marks), bar)), vx


def emit(g, data):
    page, bi, esc = g["page"], g["bi"], g["esc"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: th + " · " + en)

    if not (META.exists() and PROFILE.exists()):
        return {"page": 0,
                "skipped": "no terrain readings — run importers/build_terrain.py"}
    meta = json.loads(META.read_text())
    prof = json.loads(PROFILE.read_text())

    (DOCS / "doi.css").write_text(CSS)
    terrain_cfg = map_shell.config().get("terrain") or {}
    v = "%08x" % (zlib.crc32((JS + CSS + json.dumps(terrain_cfg, sort_keys=True)
                              ).encode("utf-8")) & 0xFFFFFFFF)
    (DOCS / "doi.js").write_text(JS)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "terrain_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1))
    (DOCS / "data" / "terrain_profile.json").write_text(
        json.dumps(prof, ensure_ascii=False, separators=(",", ":")))

    hi = meta["highest_cell"]
    tp = meta["tha_phae"]
    read = meta.get("read", "")
    src = meta.get("source", {})
    drop = float(hi["ele"]) - float(tp["ele"])

    svg, vx = _profile_svg(prof, meta, bi_text, esc)

    intro = bi(
        "เมืองนี้ตั้งอยู่ก้นแอ่ง — พื้นราว %s เมตรเหนือระดับน้ำทะเล มีสันดอยล้อมทุกด้าน "
        "หน้านี้วางพื้นดินจริงไว้ใต้แผนที่: แสงเงาตามความสูงบนแผนที่ทุกซูม กดดู 3 มิติได้ "
        "และภาพตัดขวางของแอ่งที่วาดจากไฟล์เดียวกับที่แผนที่อ่าน" % _fmt(tp["ele"]),
        "The city sits on a basin floor about %s metres above the sea, ringed by "
        "ranges on every side. This page puts the real ground under the map — "
        "relief shading at every zoom, a 3D mode one tap away, and a cross-section "
        "of the basin drawn from the same file the map reads." % _fmt(tp["ele"]))

    rule = ('<div class="doi-rule"><b>⛰ ' + bi("กติกาของหน้านี้", "The rule of this page") + "</b>"
            + bi("ความสูงทุกตัวเป็นตัวเลขของเครื่องอ่าน — แบบจำลองความสูงที่หน้านี้ถือ พร้อมวันที่อ่านและแหล่ง · "
                 "ป้ายบนยอดถือเลขของป้ายเอง · ไม่มีวิวไหนถูกจัดอันดับ ไม่มีดอยไหน “ชนะ” · "
                 "โหมด 3 มิติเป็นทางเลือก กดเองเสมอ หน้าไม่เล่นเอง",
                 "Every height here is an instrument's reading — the elevation model this page "
                 "holds, with its read date and its source · the sign on a summit keeps its own "
                 "number · no view is ranked and no doi wins · 3D is opt-in, always — the page "
                 "never performs on its own") + "</div>")

    bar = (
        '<div id="doibar" hidden>'
        '<button type="button" id="doi3d" class="doibtn" aria-pressed="false">⛰ '
        + bi("ดู 3 มิติ", "view in 3D") + "</button>"
        '<span class="doiseg" role="group" aria-label="'
        + esc(bi_text("ทิศของแสงบนเงาเขา", "hillshade light direction")) + '">'
        '<button type="button" class="doibtn doilight" data-az="90" aria-pressed="false">'
        + bi("แสงเช้า", "morning light") + "</button>"
        '<button type="button" class="doibtn doilight" data-az="335" aria-pressed="true">'
        + bi("แสงแผนที่", "map light") + "</button>"
        '<button type="button" class="doibtn doilight" data-az="270" aria-pressed="false">'
        + bi("แสงเย็น", "evening light") + "</button></span>"
        '<button type="button" id="doitop" class="doibtn" data-lat="%s" data-lng="%s">'
        % (hi["lat"], hi["lng"])
        + bi("ไปยอดสูงสุด", "to the highest cell") + "</button></div>")

    fallback = ('<div class="doi-fallback">' + svg
                + '<p class="doi-note">'
                + bi("ภาพตัดขวางคือแผนที่ของหน้านี้เมื่อไม่มีไทล์ — พื้นจริงขึ้นเองเมื่อโหลดได้",
                     "The cross-section is this page's map when tiles cannot load — "
                     "the live ground mounts by itself when it can")
                + "</p></div>")
    box = map_shell.mount("doimap", fallback, prov="cm", zoom=9.6,
                          lat=18.80, lng=98.92, cls="mdmap doimap", full=True)

    # The summit is named only when the verified cell actually sits on it —
    # the coordinate decides, not the expectation. Anywhere else, the number
    # stands alone with its position, which is already the whole claim.
    near_inthanon = (abs(float(hi["lat"]) - 18.5885) < 0.03
                     and abs(float(hi["lng"]) - 98.4867) < 0.03)
    hi_name_th = " (ยอดดอยอินทนนท์)" if near_inthanon else ""
    hi_name_en = " (the summit of Doi Inthanon)" if near_inthanon else ""
    facts = (
        '<div class="doi-facts">'
        '<div class="doi-fact"><span class="big">%s ม.</span>' % _fmt(hi["ele"])
        + bi("เซลล์ที่สูงที่สุดที่แบบจำลองถือในกรอบสองจังหวัด%s — พิกัด %s, %s"
             % (hi_name_th, hi["lat"], hi["lng"]),
             "the highest cell the model holds in the two-province frame%s — at %s, %s"
             % (hi_name_en, hi["lat"], hi["lng"]))
        + "</div>"
        '<div class="doi-fact"><span class="big">%s ม.</span>' % _fmt(tp["ele"])
        + bi("พื้นแอ่งที่ประตูท่าแพ — ยอดสูงสุดอยู่สูงกว่าหน้าประตูราว %s เมตร" % _fmt(drop),
             "the basin floor at Tha Phae Gate — the highest cell stands about %s "
             "metres above it" % _fmt(drop))
        + "</div>"
        '<div class="doi-fact"><span class="big">%s</span>' % esc(read)
        + bi("วันที่อ่าน · แหล่ง: ", "read on this date · source: ")
        + '<a href="%s">%s</a>' % (esc(src.get("url", "")), esc(src.get("name", "")))
        + "</div></div>")

    method = ('<p class="doi-method">'
              + bi("เส้นตัดที่ละติจูดของประตูท่าแพ (%.4f°N) จาก %.2f° ถึง %.2f° ตะวันออก — "
                   "แกนตั้งยืดราว %d เท่าเพื่อให้อ่านได้ ภาพจึงชันกว่าดอยจริง · อ่านเมื่อ %s"
                   % (prof["lat"], prof["lon_a"], prof["lon_b"], round(vx), read),
                   "Cut at Tha Phae Gate latitude (%.4f°N), %.2f° to %.2f°E — the vertical "
                   "axis is stretched about %d× to be readable, so the picture is steeper "
                   "than the doi · read %s"
                   % (prof["lat"], prof["lon_a"], prof["lon_b"], round(vx), read))
              + "</p>")

    words = "".join("<li>%s</li>" % bi(th, en) for th, en in [
        ("ดอย (doi) — ภูเขา ในคำเมือง: ดอยสุเทพ ดอยอินทนนท์ · ไทยกลางว่า ภูเขา · ร่วมเชื้อกับ “loi” ของไทใหญ่",
         "doi (ดอย) — mountain, in the northern tongue: Doi Suthep, Doi Inthanon; standard Thai says phukhao; kin to Shan loi"),
        ("ม่อน (mɔ̂n) — เนินยอดมน: ม่อนแจ่ม",
         "mon (ม่อน) — a rounded knoll: Mon Cham"),
        ("ขุน (khǔn) — ต้นน้ำ “หัวหน้า” ของลำน้ำ: ขุนช่างเคี่ยน ขุนวาง",
         "khun (ขุน) — a river's headwaters, its chief: Khun Chang Khian, Khun Wang"),
        ("แม่ (mɛ̂ɛ) — แม่น้ำ นำหน้าชื่อบ้านริมน้ำทั่วเหนือ: แม่ริม แม่แตง แม่ปิง",
         "mae (แม่) — mother, the river word that fronts half the north's town names: Mae Rim, Mae Taeng, the Mae Ping"),
        ("ห้วย (hûai) — ลำห้วย: ห้วยตึงเฒ่า ห้วยแก้ว",
         "huai (ห้วย) — a creek: Huai Tueng Thao, Huai Kaeo"),
        ("ผา (phǎa) — หน้าผา: ผาช่อ ผาลาด",
         "pha (ผา) — a cliff: Pha Chor, Pha Lat"),
        ("โป่ง (pòong) — แอ่งแร่ที่ซึมจากดิน: โป่งเดือด — ต่อที่หน้าน้ำพุร้อน",
         "pong (โป่ง) — a mineral seep: Pong Duet — the hot-springs page carries the rest"),
        ("แอ่ง (ɛ̀ng) — ที่ลุ่มระหว่างดอย: แอ่งเชียงใหม่ ที่ภาพตัดบนหน้านี้วาดไว้",
         "aeng (แอ่ง) — the basin between the doi: the Chiang Mai basin this page's cross-section draws"),
        ("น้ำตก (nám-tòk) — น้ำตก: แม่สา บัวตอง · ส่วน “ลาบ-น้ำตก” ในเมนูคือมื้อเที่ยง คนละเรื่อง",
         "namtok (น้ำตก) — a waterfall: Mae Sa, Bua Tong · the menu's nam tok is lunch, a different story"),
    ])
    roots = ('<p class="doi-note">'
             + bi("ตามรากศัพท์ต่อได้ที่ wichaa.net/thairoots — ดอย ม่อน ขุน แม่ ห้วย ผา โป่ง ล้วนเป็นคำไทแท้",
                  "follow the roots at wichaa.net/thairoots — doi, mon, khun, mae, huai, pha and pong are all old Tai stock")
             + "</p>")

    ld = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "ดอย — ความสูงภูมิประเทศเชียงใหม่·เชียงราย · Chiang Mai & Chiang Rai elevation readings",
        "url": BASE + "doi.html",
        "description": "Elevation readings for the Chiang Mai and Chiang Rai frame: "
                       "the model's highest cell, the basin floor at Tha Phae Gate, and "
                       "a west-east height profile. Terrarium-encoded tiles, read "
                       + read + ".",
        "dateModified": read,
        "isBasedOn": src.get("url", ""),
        "distribution": [
            {"@type": "DataDownload", "contentUrl": BASE + "data/terrain_meta.json",
             "encodingFormat": "application/json"},
            {"@type": "DataDownload", "contentUrl": BASE + "data/terrain_profile.json",
             "encodingFormat": "application/json"},
        ],
    }

    og = shelf_og("cm", "sights") if shelf_og else None
    body = (
        '<h1>⛰ ' + bi("ดอย — แผ่นดินเชียงใหม่ · เชียงราย",
                      "The doi — the shape of the land") + "</h1>"
        '<p class="doi-intro">' + intro + "</p>"
        + rule
        + "<h2>" + bi("แผนที่พื้นดิน", "The ground map") + "</h2>"
        + bar + box
        + '<p class="doi-note">'
        + bi("ลากด้วยนิ้วเดียวได้เลย หน้านี้แผนที่คือหน้า · ปุ่มขึ้นเองเมื่อพื้นพร้อม",
             "One finger pans — on this page the map is the page · the buttons appear "
             "when the ground is ready") + "</p>"
        + "<h2>" + bi("ตัวเลขที่เครื่องอ่านได้", "What the instrument read") + "</h2>"
        + facts
        + "<h2>" + bi("แอ่งเชียงใหม่ — ภาพตัดขวาง", "The basin, in cross-section") + "</h2>"
        + '<div class="doi-sect">' + svg + "</div>" + method
        + "<h2>" + bi("อ่านแผ่นดินจากชื่อบ้าน", "Reading the land through its names") + "</h2>"
        + '<ul class="doi-words">' + words + "</ul>" + roots
        + '<p class="doi-note">'
        + bi("ไปต่อ: ", "Onward: ")
        + '<a href="namphuron.html">♨️ ' + bi("น้ำพุร้อน — โป่งทั้งภาคเหนือ", "hot springs — the north's pong") + "</a> · "
        + '<a href="soi.html">' + bi("ถนนและซอยที่ปีนดอยพวกนี้", "the roads and sois that climb these doi") + "</a></p>"
        + '<p class="doi-note">'
        + bi("ทะเบียนดิบ", "Raw readings") + ': <a href="data/terrain_meta.json">data/terrain_meta.json</a> · '
        + '<a href="data/terrain_profile.json">data/terrain_profile.json</a> · '
        + bi("เห็นเลขที่ควรอ่านใหม่ — ", "a reading that needs re-reading — ")
        + '<a href="suggest.html">' + bi("บอกมด", "tell the ants") + "</a></p>"
        + share_block(BASE + "doi.html",
                      "ดอย — แผ่นดินเชียงใหม่·เชียงราย · มดแดง", card=og))

    (DOCS / "doi.html").write_text(page(
        "ดอย — แผ่นดินเชียงใหม่ · เชียงราย · The doi — the shape of the land",
        body, depth=0, path="doi.html",
        desc="แผนที่ภูมิประเทศเชียงใหม่-เชียงราย: แสงเงาตามความสูงจริง โหมดสามมิติ ภาพตัดขวางแอ่งเชียงใหม่ "
             "ยอดสูงสุดที่แบบจำลองอ่านได้ และคำเรียกแผ่นดินในชื่อบ้านนามเมือง — ทุกตัวเลขมีวันที่อ่านและแหล่ง · "
             "The terrain of Chiang Mai and Chiang Rai: real relief shading, an opt-in 3D mode, "
             "a cross-section of the basin, the model's highest cell, and the landscape words "
             "inside northern place-names — every number dated and sourced.",
        extra_head='<link rel="stylesheet" href="doi.css?v=%s">' % v
                   + '<script src="doi.js?v=%s" defer></script>' % v
                   + '<script type="application/ld+json">'
                   + json.dumps(ld, ensure_ascii=False) + "</script>",
        og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("ดอย", "The doi")))
    return {"page": 1, "highest": hi["ele"], "tha_phae": tp["ele"],
            "profile_points": len(prof["ele"]), "terrain_cfg": bool(terrain_cfg)}
