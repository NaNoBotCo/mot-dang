#!/usr/bin/env python3
"""เมืองหลับนิดหน่อย — The City That Sleeps Nitnoy.

One page, one question: what is this city doing right now? Every place whose
opening hours we hold becomes a lamp on the night map; drag the day through
its 24 hours and watch the morning kads ignite before dawn, the cafés catch
at eight, the bars take over after dark. 2,000-odd lamps, drawn in the
browser from the baked file — no tiles, no library. The which-way panel on
/toilets.html was drawn the same way and has since gained a basemap under it
via map_shell.mount(); this map has not been wired up yet, and the lamps are
the one drawing where cream may still be the right ground — a night map reads
as night. Worth a look, not an assumption.

The lamp rule, stated wherever the map is: a lamp we do not draw is a place
whose hours nobody holds. Unlit is silence, never "closed".

Below the map, two things that fall out of the same bitmaps:
  - what the city eats when — open-fraction curves by food subcategory and
    cuisine tag, with the meal windows each one serves (an inference from
    opening hours, labelled so);
  - the market rhythm — the markets whose hours we hold, sorted into
    morning kad / daytime / evening / night, each with its week-strip.

Entry point: emit(g, data, frame) — g is build.py's globals, frame carries
the shared city-map projection so this page cannot drift from seven/walk.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

GROUPS = [
    ("food", "#f6b73c", "ร้านอาหาร", "food"),
    ("cafe", "#f0e3b0", "คาเฟ่", "cafés"),
    ("night", "#b18cff", "บาร์-ผับ", "bars"),
    ("market", "#ff6b5e", "ตลาด", "markets"),
    ("care", "#ff9fc7", "นวด-ความงาม", "massage & beauty"),
    ("shop", "#7fd8a4", "ของจำเป็น-ช้อป", "essentials & shops"),
    ("other", "#c9d4e0", "อื่น ๆ", "everything else"),
]

CUISINE_TH = {
    "thai": "อาหารไทย", "coffee_shop": "ร้านกาแฟ", "breakfast": "อาหารเช้า",
    "japanese": "ญี่ปุ่น", "chinese": "จีน", "pizza": "พิซซ่า",
    "burger": "เบอร์เกอร์", "italian": "อิตาเลียน", "tea": "ร้านชา",
    "cake": "เค้ก-ขนม", "sandwich": "แซนด์วิช", "international": "นานาชาติ",
    "asian": "เอเชีย", "american": "อเมริกัน", "regional": "อาหารถิ่น",
    "ice_cream": "ไอศกรีม",
}

BAND_TH = {"breakfast": "เช้า", "lunch": "เที่ยง", "dinner": "เย็น",
           "late": "ดึก", "allday": "ทั้งวัน"}
BAND_EN = {"breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
           "late": "late", "allday": "all day"}
KIND_TH = {"morning": "กาดเช้า", "day": "กลางวัน", "evening": "กาดแลง",
           "night": "กลางคืน"}
KIND_EN = {"morning": "morning kad", "day": "daytime", "evening": "evening",
           "night": "night"}
DAY_TH = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]


def _sparkline(curve, color="#b3540f"):
    """A 24-hour open-fraction curve as a small filled SVG."""
    w, h, n = 144, 34, len(curve)
    pts = []
    for i, v in enumerate(curve):
        x = round(i * w / (n - 1), 1)
        y = round(h - 2 - v * (h - 6), 1)
        pts.append("%g,%g" % (x, y))
    poly = " ".join(pts)
    ticks = "".join(
        '<line x1="%g" y1="%d" x2="%g" y2="%d" stroke="#0002"/>'
        % (t * w / 24, h - 4, t * w / 24, h) for t in (6, 12, 18))
    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" '
            'aria-hidden="true"><polygon points="0,%d %s %d,%d" '
            'fill="%s33"/><polyline points="%s" fill="none" stroke="%s" '
            'stroke-width="1.5"/>%s</svg>'
            % (w, h, w, h, h - 2, poly, w, h - 2, color, poly, color, ticks))


def _week_strip(sched):
    """Seven day-rows, one pixel band per open interval."""
    w, rh = 192, 7
    rows = []
    for d in range(7):
        y = d * (rh + 2)
        rows.append('<rect x="0" y="%d" width="%d" height="%d" '
                    'fill="#00000014" rx="2"/>' % (y, w, rh))
        for a, b in sched:
            da, db = a // 1440, (b - 1) // 1440
            for dd in range(da, db + 1):
                if dd != d:
                    continue
                s = max(a - d * 1440, 0)
                e = min(b - d * 1440, 1440)
                if e <= s:
                    continue
                rows.append(
                    '<rect x="%g" y="%d" width="%g" height="%d" '
                    'fill="#b3540f" rx="2"/>'
                    % (round(s * w / 1440, 1), y,
                       max(round((e - s) * w / 1440, 1), 1.5), rh))
    h = 7 * (rh + 2)
    labels = "".join(
        '<text x="-4" y="%d" font-size="6.5" text-anchor="end" '
        'fill="#00000099">%s</text>' % (d * (rh + 2) + rh, DAY_TH[d])
        for d in range(7))
    hours = "".join(
        '<text x="%g" y="%d" font-size="6" text-anchor="middle" '
        'fill="#00000066">%02d</text>' % (t * w / 24, h + 8, t)
        for t in (0, 6, 12, 18, 24))
    return ('<svg viewBox="-16 0 %d %d" width="%d" height="%d" '
            'role="img" aria-label="ช่วงเปิดรายสัปดาห์">%s%s%s</svg>'
            % (w + 20, h + 11, w + 20, h + 11,
               labels, "".join(rows), hours))


_JS = r"""
(function(){
var F=@FRAME@;
var box=document.getElementById('nnbox'),cv=document.getElementById('nncv');
var ctx=cv.getContext('2d');
var still=matchMedia('(prefers-reduced-motion: reduce)').matches;
var D=null,px=null,py=null,on={};
@GROUPS@.forEach(function(g){on[g[0]]=true;});
var GC={};@GROUPS@.forEach(function(g){GC[g[0]]=g[1];});
var sprites={};
function sprite(c){
  if(sprites[c])return sprites[c];
  var s=document.createElement('canvas');s.width=s.height=26;
  var x=s.getContext('2d'),g=x.createRadialGradient(13,13,0,13,13,13);
  g.addColorStop(0,c);g.addColorStop(0.35,c+'aa');g.addColorStop(1,c+'00');
  x.fillStyle=g;x.fillRect(0,0,26,26);return sprites[c]=s;
}
function proj(la,ln){
  return [F.pad+(ln-F.w)/(F.e-F.w)*F.mw,
          F.pad+F.mh-(la-F.s)/(F.n-F.s)*F.mh];
}
var day=0,minute=0,playing=false,timer=null;
function bkkNow(){
  var p=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Bangkok',
    hour:'2-digit',minute:'2-digit',weekday:'short',hour12:false})
    .formatToParts(new Date()),o={};
  p.forEach(function(t){o[t.type]=t.value;});
  var wd={Mon:0,Tue:1,Wed:2,Thu:3,Fri:4,Sat:5,Sun:6}[o.weekday];
  return [wd,(+o.hour)%24*60+(+o.minute)];
}
function openAt(k,t){
  var s=D.schedules[k];
  for(var i=0;i<s.length;i++){if(s[i][0]<=t&&t<s[i][1])return true;}
  return false;
}
var TH=['จันทร์','อังคาร','พุธ','พฤหัสบดี','ศุกร์','เสาร์','อาทิตย์'];
function draw(){
  var t=day*1440+minute,W=cv.width,H=cv.height;
  ctx.clearRect(0,0,W,H);
  var scale=W/F.vw;
  var counts={},total=0;
  for(var i=0;i<D.places.length;i++){
    var p=D.places[i];
    if(!on[p.g])continue;
    if(!openAt(p.k,t))continue;
    counts[p.g]=(counts[p.g]||0)+1;total++;
    var sp=sprite(GC[p.g]);
    ctx.drawImage(sp,px[i]*scale-9,py[i]*scale-9,18,18);
  }
  var hh=('0'+Math.floor(minute/60)).slice(-2),
      mm=('0'+minute%60).slice(-2);
  document.getElementById('nnclock').textContent=
    'วัน'+TH[day]+' '+hh+':'+mm+' น.';
  document.getElementById('nncount').textContent=
    total.toLocaleString('th-TH');
  @GROUPS@.forEach(function(g){
    var el=document.getElementById('nn-n-'+g[0]);
    if(el)el.textContent=counts[g[0]]||0;
  });
}
function setUI(){
  document.getElementById('nnslider').value=minute;
  var chips=document.querySelectorAll('#nndays button');
  chips.forEach(function(b,i){b.classList.toggle('nnon',i===day);});
  draw();
}
function tick(){minute+=4;if(minute>=1440){minute-=1440;day=(day+1)%7;}setUI();}
function play(v){
  playing=v;document.getElementById('nnplay').textContent=v?'⏸':'▶';
  if(timer){clearInterval(timer);timer=null;}
  if(v)timer=setInterval(tick,66);
}
function size(){
  var w=box.clientWidth;
  cv.width=w;cv.height=Math.round(w*F.vh/F.vw);
  if(D)draw();
}
fetch(document.documentElement.dataset.root+'data/open_lamps.json')
 .then(function(r){return r.json();})
 .then(function(d){
   D=d;px=new Float32Array(d.places.length);py=new Float32Array(d.places.length);
   for(var i=0;i<d.places.length;i++){
     var q=proj(d.places[i].la,d.places[i].ln);px[i]=q[0];py[i]=q[1];
   }
   var now=bkkNow();day=now[0];minute=now[1];
   size();setUI();
   if(!still)play(true);
 });
addEventListener('resize',size);
document.getElementById('nnslider').addEventListener('input',function(){
  minute=+this.value;play(false);draw();
  var hh=('0'+Math.floor(minute/60)).slice(-2),
      mm=('0'+minute%60).slice(-2);
  document.getElementById('nnclock').textContent=
    'วัน'+TH[day]+' '+hh+':'+mm+' น.';
});
document.querySelectorAll('#nndays button').forEach(function(b,i){
  b.addEventListener('click',function(){day=i;setUI();});
});
document.getElementById('nnplay').addEventListener('click',
  function(){play(!playing);});
document.getElementById('nnnow').addEventListener('click',function(){
  var now=bkkNow();day=now[0];minute=now[1];play(false);setUI();
});
document.querySelectorAll('.nnleg button').forEach(function(b){
  b.addEventListener('click',function(){
    var k=this.dataset.g;on[k]=!on[k];
    this.classList.toggle('nnoff',!on[k]);draw();
  });
});
})();
"""

_CSS = """
#nnbox{position:relative;background:#0d1420;border-radius:14px;
  overflow:hidden;box-shadow:0 8px 30px #0006}
#nnbox svg,#nnbox canvas{display:block;width:100%;height:auto}
#nncv{position:absolute;inset:0}
.nnbar{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;
  margin:.6rem 0}
.nnbar input[type=range]{flex:1;min-width:10rem}
#nnclock{font-variant-numeric:tabular-nums;font-weight:700;
  min-width:11ch}
#nndays button,.nnleg button,#nnplay,#nnnow{border:1px solid #0003;
  background:#fff;border-radius:999px;padding:.15rem .6rem;
  cursor:pointer;transition:transform .12s}
#nndays button:active,.nnleg button:active{transform:scale(.92)}
#nndays .nnon{background:#b3540f;color:#fff;border-color:#b3540f}
.nnleg{display:flex;flex-wrap:wrap;gap:.4rem;margin:.4rem 0}
.nnleg button{display:flex;gap:.35rem;align-items:center}
.nnleg .nndot{width:.7rem;height:.7rem;border-radius:50%;
  box-shadow:0 0 6px 1px currentColor}
.nnleg .nnoff{opacity:.35}
.mealgrid{display:grid;gap:.8rem;
  grid-template-columns:repeat(auto-fill,minmax(11rem,1fr))}
.mealcard{border:1px solid #0002;border-radius:10px;padding:.5rem .6rem}
.mealcard b{display:block}
.bandchip{display:inline-block;border-radius:999px;padding:0 .5rem;
  font-size:.8em;background:#b3540f22;margin-right:.25rem}
.kadgrid{display:grid;gap:.8rem;
  grid-template-columns:repeat(auto-fill,minmax(13rem,1fr))}
.kadcard{border:1px solid #0002;border-radius:10px;padding:.5rem .6rem}
"""


def _ground_css(frame):
    """The real city, behind the lamps.

    The box was a flat dark rectangle: it showed the SHAPE of the scatter and
    nothing about where any of it is. build.py renders the shared city frame
    once, at this exact projection, so the background lines up with the drawing
    by construction rather than by a number kept in sync by hand. No archive on
    the machine and this is "" — the flat rectangle stands, as it always did.
    """
    g = (frame or {}).get("ground_night")
    if not g:
        return ""
    return ("#%s{background-image:url(%s);background-size:100%% 100%%;"
            "background-position:center}" % ('nnbox', g))


def emit(g, data, frame):
    page, bi, esc = g["page"], g["bi"], g["esc"]
    share_block, BASE, DOCS = g["share_block"], g["BASE"], g["DOCS"]
    place_slug = g["place_slug"]

    src = ROOT / "data" / "open_lamps.json"
    if not src.exists():
        return ("SKIPPED — no data/open_lamps.json "
                "(run importers/build_open_lamps.py)")
    lamps = json.loads(src.read_text())
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data" / "open_lamps.json").write_bytes(src.read_bytes())

    # the stop-motion + its poster are optional assets (make_nitnoy_gif.py,
    # needs Pillow) — without them the page simply has no film strip
    import shutil
    gif = ROOT / "assets" / "nitnoy.gif"
    poster = ROOT / "assets" / "nitnoy_poster.png"
    has_gif = gif.exists()
    og = None
    if has_gif:
        shutil.copyfile(gif, DOCS / "nitnoy.gif")
    if poster.exists():
        shutil.copyfile(poster, DOCS / "nitnoy_poster.png")
        og = "nitnoy_poster.png"
    # The framed family card (make_answer_cards.py) supersedes the bare
    # poster as the share preview; the poster stays the on-page film still.
    if (ROOT / "assets" / "og" / "nitnoy.png").exists():
        og = "og/nitnoy.png"

    vw = frame["mw"] + 2 * frame["pad"]
    vh = frame["mh"] + 2 * frame["pad"]

    in_frame = sum(1 for p in lamps["places"]
                   if frame["s"] <= p["la"] <= frame["n"]
                   and frame["w"] <= p["ln"] <= frame["e"])
    outside = len(lamps["places"]) - in_frame

    moat = ""
    ring = g["_moat_ring"]()
    if ring:
        pts = " ".join("%g,%g" % frame["px"](la, ln) for la, ln in ring)
        moat = ('<polygon points="%s" fill="none" stroke="#3d5a80" '
                'stroke-width="2" stroke-dasharray="6 4"/>' % pts)

    underlay = (
        ('<svg viewBox="0 0 %d %d" role="img" aria-label="แผนที่โคมไฟกลางเมืองเชียงใหม่">' % (vw, vh))
        # The dark rectangle and the traced roads are the fallback, and they
        # step aside when the real ground is behind the box: two street
        # networks drawn a hair apart read as a printing error. What stays is
        # the moat, which is the one landmark worth stating twice.
        + ('' if frame.get("ground_night") else
           ('<rect width="%d" height="%d" fill="#0d1420"/>'
            '<path d="%s" fill="none" stroke="#22334a" stroke-width="1"/>'
            % (vw, vh, frame["road_d"])))
        + moat + '</svg>')

    # ---- category labels for the meal section -----------------------------
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    sub_names = {}
    for c in cats.get("categories", cats if isinstance(cats, list) else []):
        for ch in c.get("children", []):
            sub_names[ch.get("key", "")] = (ch.get("th", ch.get("key", "")),
                                            ch.get("en", ch.get("key", "")))

    def band_chips(bands):
        return "".join('<span class="bandchip">%s · %s</span>'
                       % (BAND_TH[b], BAND_EN[b]) for b in bands) or \
               '<span class="bandchip">—</span>'

    meal_cards = []
    for m in sorted(lamps["meals"]["subs"], key=lambda m: -m["n"]):
        th, en = sub_names.get(m["sub"], (m["sub"], m["sub"]))
        meal_cards.append(
            '<div class="mealcard"><b>%s</b>%s<br>%s'
            '<span class="tinynote">n=%d</span></div>'
            % (bi(esc(th), esc(en)), _sparkline(m["curve"]),
               band_chips(m["bands"]), m["n"]))
    cuisine_cards = []
    for m in sorted(lamps["meals"]["cuisines"], key=lambda m: -m["n"]):
        th = CUISINE_TH.get(m["cuisine"], m["cuisine"])
        cuisine_cards.append(
            '<div class="mealcard"><b>%s</b>%s<br>%s'
            '<span class="tinynote">n=%d</span></div>'
            % (bi(esc(th), esc(m["cuisine"])), _sparkline(m["curve"]),
               band_chips(m["bands"]), m["n"]))

    # who serves breakfast — the direct answer, ranked
    bfast = sorted((m for m in lamps["meals"]["cuisines"]
                    if m["scores"].get("breakfast", 0) >= 0.4),
                   key=lambda m: -m["scores"]["breakfast"])
    bfast_line = " · ".join(
        "%s (%.0f%%)" % (CUISINE_TH.get(m["cuisine"], m["cuisine"]),
                         m["scores"]["breakfast"] * 100) for m in bfast[:6])

    # ---- markets ----------------------------------------------------------
    by_id = {}
    for prov in ("cm", "cr"):
        for r in data.get(prov, []):
            by_id[r["id"]] = r
    kad_cards = {k: [] for k in ("morning", "day", "evening", "night")}
    for m in lamps["markets"]["list"]:
        sched = lamps["schedules"][m["k"]]
        r = by_id.get(m["id"])
        name = esc(m["n"])
        if r is not None:
            name = ('<a href="%s/p/%s.html">%s</a>'
                    % (r["province"], place_slug(r), name))
        kad_cards[m["kind"]].append(
            '<div class="kadcard"><b>%s</b>%s'
            '<span class="tinynote">%s</span></div>'
            % (name, _week_strip(sched), esc(m["hours"])))
    kad_html = []
    for kind in ("morning", "day", "evening", "night"):
        if not kad_cards[kind]:
            continue
        kad_html.append('<h3>%s</h3><div class="kadgrid">%s</div>'
                        % (bi(KIND_TH[kind], KIND_EN[kind]),
                           "".join(kad_cards[kind])))

    parse = lamps["parse"]
    lede_th = ("ลากเข็มนาฬิกาแล้วดูเมืองตื่น — ทุกดวงคือร้านที่เรารู้เวลาเปิด "
               "%s ดวงจากทั้งหมด %s แห่งในสารบัญ กาดเช้าติดก่อนฟ้าสาง "
               "คาเฟ่ตามมาแปดโมง บาร์รับช่วงหลังมืด"
               % ("{:,}".format(parse["parsed"]),
                  "{:,}".format(parse["records"])))
    lede_en = ("Drag the clock and watch the city wake — every lamp is a "
               "place whose opening hours we hold: %s lamps of %s places "
               "in the catalog. The morning kads catch before dawn, the "
               "cafés at eight, the bars take over after dark."
               % ("{:,}".format(parse["parsed"]),
                  "{:,}".format(parse["records"])))

    legend = "".join(
        '<button data-g="%s" style="color:%s">'
        '<span class="nndot" style="background:%s"></span>%s '
        '<span id="nn-n-%s">0</span></button>'
        % (k, c, c, bi(th, en), k) for k, c, th, en in GROUPS)

    days = "".join('<button type="button">%s</button>' % d for d in DAY_TH)

    js = (_JS
          .replace("@FRAME@", json.dumps({
              "w": frame["w"], "e": frame["e"], "s": frame["s"],
              "n": frame["n"], "mw": frame["mw"], "mh": frame["mh"],
              "pad": frame["pad"], "vw": vw, "vh": vh}))
          .replace("@GROUPS@", json.dumps(
              [[k, c] for k, c, _t, _e in GROUPS])))

    method_th = (
        "วิธีอ่าน: โคมวาดเฉพาะร้านที่สารบัญมีเวลาเปิด (opening_hours จาก "
        "OpenStreetMap และเจ้าของร้านยืนยัน) — โคมที่ไม่วาด แปลว่าเราไม่รู้เวลา "
        "ไม่ได้แปลว่าปิด · อ่านเวลาไม่ออก %d ป้าย (นับและเก็บตัวอย่างไว้ใน "
        "ไฟล์ข้อมูล ไม่เดา) · กรอบแผนที่คือเขตเมืองที่ถนนถูกเก็บ อีก %d "
        "ดวงอยู่นอกกรอบ นับรวมในตัวเลขแต่ไม่ได้วาด · เวลาเป็นเวลาไทยเสมอ "
        "· คำนวณใหม่ทุกครั้งที่สร้างเว็บ" % (parse["excluded"], outside))
    method_en = (
        "How to read it: a lamp is drawn only for a place whose opening "
        "hours the catalog holds (OpenStreetMap opening_hours plus "
        "owner-confirmed claims) — an undrawn lamp means we do not know "
        "the hours, never that a place is closed. %d hour strings could "
        "not be read (counted and sampled in the data file, not guessed). "
        "The frame is the road-crawl area; %d more lamps burn outside it, "
        "counted in the totals but not drawn. All times are Thai time. "
        "Recomputed every build." % (parse["excluded"], outside))

    meal_note_th = ("เส้นโค้งคือสัดส่วนร้านที่เปิด ณ แต่ละครึ่งชั่วโมง "
                    "เฉลี่ยทั้งสัปดาห์ — เป็นการอนุมานจากเวลาเปิดของทั้งหมวด "
                    "ไม่ใช่คำสัญญาของร้านใดร้านหนึ่ง")
    meal_note_en = ("Each curve is the share of a category open at each "
                    "half-hour, averaged over the week — an inference about "
                    "the category's habit, never a promise about one shop.")

    kad_gap_th = ("มีเวลาเปิดแค่ %d จาก %d ตลาด และจังหวะรายแผงข้างในกาด "
                  "ไม่มีในข้อมูลเปิดที่ไหนเลย — ต้องเดินเก็บเอง "
                  "รู้เวลากาดไหนช่วยบอกได้เลย"
                  % (lamps["markets"]["with_hours"],
                     lamps["markets"]["total"]))
    kad_gap_en = ("We hold hours for only %d of %d markets, and stall-level "
                  "rhythm inside a kad exists in no open dataset at all — "
                  "it has to be walked. If you know a market's hours, tell "
                  "the ants."
                  % (lamps["markets"]["with_hours"],
                     lamps["markets"]["total"]))

    body = (
        '<h1>🏮 %s</h1>'
        '<p class="lede">%s</p>'
        '<div class="nnbar"><button id="nnplay" type="button">▶</button>'
        '<button id="nnnow" type="button">%s</button>'
        '<span id="nndays">%s</span>'
        '<input id="nnslider" type="range" min="0" max="1439" step="5" '
        'value="720" aria-label="เวลา">'
        '<span id="nnclock"></span>'
        '<span>💡 <b id="nncount">0</b></span></div>'
        '<div class="nnleg">%s</div>'
        '<div id="nnbox">%s<canvas id="nncv"></canvas></div>'
        '<p class="tinynote">%s</p>'
        '%s'
        '<h2>%s</h2>'
        '<p>%s <b>%s</b></p>'
        '<div class="mealgrid">%s</div>'
        '<h3>%s</h3>'
        '<div class="mealgrid">%s</div>'
        '<p class="tinynote">%s</p>'
        '<h2>%s</h2>%s'
        '<p>%s <a href="crawl-request.html">🐜 %s</a></p>'
        '<p><a href="data/open_lamps.json">data/open_lamps.json</a> · '
        '<a href="walk.html">🚶 %s</a> · '
        '<a href="seven.html">🏪 %s</a></p>'
        '%s<script>%s</script>'
        % (
            bi("เมืองหลับนิดหน่อย", "The City That Sleeps Nitnoy"),
            bi(lede_th, lede_en),
            bi("ตอนนี้", "now"),
            days,
            legend,
            underlay,
            bi(method_th, method_en),
            ('<h2>%s</h2><figure style="margin:0">'
             '<img src="nitnoy.gif" alt="%s" loading="lazy" '
             'style="width:100%%;max-width:36rem;border-radius:14px;'
             'box-shadow:0 8px 30px #0004">'
             '<figcaption class="tinynote">%s</figcaption></figure>'
             % (bi("หนึ่งวันเสาร์ในหกวินาที", "One Saturday in six seconds"),
                "แผนที่โคมไฟของเมืองเชียงใหม่ ขยับทีละครึ่งชั่วโมงครบ 24 ชั่วโมง",
                bi("วาดจากไฟล์ข้อมูลเดียวกับแผนที่ข้างบน ทีละครึ่งชั่วโมง "
                   "— เซฟไปแชร์ได้เลย",
                   "Drawn from the same data file as the map above, one "
                   "frame per half hour — save and share freely."))
             ) if has_gif else "",
            bi("เมืองกินอะไรตอนไหน", "What the city eats when"),
            bi("หมวดที่เปิดรับข้าวเช้า:", "Serving breakfast:"),
            esc(bfast_line or "—"),
            "".join(meal_cards),
            bi("แยกตามประเภทอาหาร", "By cuisine tag"),
            "".join(cuisine_cards),
            bi(meal_note_th, meal_note_en),
            bi("จังหวะกาด", "The market rhythm"),
            "".join(kad_html),
            bi(kad_gap_th, kad_gap_en),
            bi("ขอให้มดไปเก็บ", "ask the ants to collect"),
            bi("แผนที่ระยะเดิน", "the city at walking pace"),
            bi("ใกล้เซเว่นแค่ไหน", "how near is the nearest 7-Eleven"),
            share_block(BASE + "nitnoy.html",
                        "เมืองหลับนิดหน่อย · มดแดง"),
            js,
        ))

    (DOCS / "nitnoy.html").write_text(page(
        "เมืองหลับนิดหน่อย",
        body, depth=0, path="nitnoy.html", desc=lede_th,
        extra_head="<style>%s%s</style>" % (_CSS, _ground_css(frame)), og=og))
    return ("nitnoy.html — %d lamps (%d in frame), %d meal curves, "
            "%d markets" % (parse["parsed"], in_frame,
                            len(lamps["meals"]["subs"])
                            + len(lamps["meals"]["cuisines"]),
                            lamps["markets"]["with_hours"]))
