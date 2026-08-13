#!/usr/bin/env python3
"""รสเมือง — The taste of the town.

Every cuisine-tagged place painted as one dot on the night map: 1,900-odd
dots, six families plus "other", every token kept. Chips filter by family;
a second row lights one cuisine at a time so its belt stands out; every dot
answers with its name on hover. Below the map, the numbers behind the
picture: which cuisines huddle (Indian in 786 m, east of the moat — the
Chang Klan quarter is real), which spread everywhere, and which direction
each one's weight sits from the moat.

House rules as ever: browser-drawn from the baked file over the shared city
frame, no tiles, no library. A place with no cuisine tag is absent — that
is silence, never "no cuisine". Geography numbers are Chiang Mai-only; the
CR dots draw, but a centroid across two provinces is a rice field between
them.

Entry point: emit(g, data, frame) — same contract as nitnoy_layer.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TOKEN_TH = {
    "thai": "อาหารไทย", "coffee_shop": "ร้านกาแฟ", "breakfast": "อาหารเช้า",
    "japanese": "ญี่ปุ่น", "chinese": "จีน", "korean": "เกาหลี",
    "vietnamese": "เวียดนาม", "pizza": "พิซซ่า", "italian": "อิตาเลียน",
    "burger": "เบอร์เกอร์", "american": "อเมริกัน", "french": "ฝรั่งเศส",
    "indian": "อินเดีย", "regional": "อาหารถิ่น", "noodle": "ก๋วยเตี๋ยว",
    "noodles": "ก๋วยเตี๋ยว", "chicken": "ไก่", "seafood": "อาหารทะเล",
    "tea": "ร้านชา", "cake": "เค้ก", "ice_cream": "ไอศกรีม",
    "sandwich": "แซนด์วิช", "international": "นานาชาติ", "asian": "เอเชีย",
    "steak_house": "สเต๊ก", "steak": "สเต๊ก", "pasta": "พาสต้า",
    "local": "พื้นบ้าน", "barbecue": "ปิ้งย่าง", "curry": "แกง",
}

_JS = r"""
(function(){
var F=@FRAME@,T=null,px=null,py=null;
var box=document.getElementById('ttbox'),cv=document.getElementById('ttcv');
var ctx=cv.getContext('2d');
var famOn={},hot=null,FC={};
@FAMS@.forEach(function(f){famOn[f[0]]=true;FC[f[0]]=f[1];});
function proj(la,ln){
  return [F.pad+(ln-F.w)/(F.e-F.w)*F.mw,
          F.pad+F.mh-(la-F.s)/(F.n-F.s)*F.mh];
}
var sprites={};
function sprite(c,dim){
  var k=c+(dim?'d':'');
  if(sprites[k])return sprites[k];
  var s=document.createElement('canvas');s.width=s.height=18;
  var x=s.getContext('2d'),g=x.createRadialGradient(9,9,0,9,9,9);
  var a=dim?'22':'';
  g.addColorStop(0,c+(dim?'55':'ff'));g.addColorStop(0.4,c+(dim?'22':'99'));
  g.addColorStop(1,c+'00');
  x.fillStyle=g;x.fillRect(0,0,18,18);return sprites[k]=s;
}
function draw(){
  if(!T)return;
  var W=cv.width,scale=W/F.vw;
  ctx.clearRect(0,0,W,cv.height);
  var shown=0;
  for(var pass=0;pass<2;pass++){
    for(var i=0;i<T.dots.length;i++){
      var d=T.dots[i];
      if(!famOn[d.f])continue;
      var lit=!hot||d.t===hot;
      if(pass===0&&lit)continue;
      if(pass===1&&!lit)continue;
      if(pass===1)shown++;
      ctx.drawImage(sprite(FC[d.f],!lit),px[i]*scale-6,py[i]*scale-6,12,12);
    }
  }
  document.getElementById('ttcount').textContent=shown.toLocaleString('th-TH');
}
function size(){
  var w=box.clientWidth;
  cv.width=w;cv.height=Math.round(w*F.vh/F.vw);draw();
}
fetch(document.documentElement.dataset.root+'data/taste.json')
 .then(function(r){return r.json();})
 .then(function(d){
   T=d;px=new Float32Array(d.dots.length);py=new Float32Array(d.dots.length);
   for(var i=0;i<d.dots.length;i++){
     var q=proj(d.dots[i].la,d.dots[i].ln);px[i]=q[0];py[i]=q[1];
   }
   size();
 });
addEventListener('resize',size);
document.querySelectorAll('.ttleg button').forEach(function(b){
  b.addEventListener('click',function(){
    var k=this.dataset.f;famOn[k]=!famOn[k];
    this.classList.toggle('ttoff',!famOn[k]);draw();
  });
});
document.querySelectorAll('#ttcui button').forEach(function(b){
  b.addEventListener('click',function(){
    var t=this.dataset.t;
    hot=(hot===t)?null:t;
    document.querySelectorAll('#ttcui button').forEach(function(x){
      x.classList.toggle('tthot',x.dataset.t===hot);});
    draw();
  });
});
cv.addEventListener('mousemove',function(ev){
  if(!T)return;
  var r=cv.getBoundingClientRect(),scale=cv.width/F.vw;
  var mx=(ev.clientX-r.left)*(cv.width/r.width),
      my=(ev.clientY-r.top)*(cv.height/r.height);
  var best=-1,bd=144;
  for(var i=0;i<T.dots.length;i++){
    if(!famOn[T.dots[i].f])continue;
    var dx=px[i]*scale-mx,dy=py[i]*scale-my,dd=dx*dx+dy*dy;
    if(dd<bd){bd=dd;best=i;}
  }
  var el=document.getElementById('ttname');
  if(best>=0){var d=T.dots[best];
    el.textContent=d.n+' · '+d.t.replace(/_/g,' ');}
  else el.textContent=' ';
});
})();
"""

_CSS = """
#ttbox{position:relative;background:#0d1420;border-radius:14px;
  overflow:hidden;box-shadow:0 8px 30px #0006}
#ttbox svg,#ttbox canvas{display:block;width:100%;height:auto}
#ttcv{position:absolute;inset:0}
.ttleg,#ttcui{display:flex;flex-wrap:wrap;gap:.4rem;margin:.4rem 0}
.ttleg button,#ttcui button{border:1px solid #0003;background:#fff;
  border-radius:999px;padding:.15rem .6rem;cursor:pointer;
  display:flex;gap:.35rem;align-items:center;transition:transform .12s}
.ttleg button:active,#ttcui button:active{transform:scale(.92)}
.ttleg .ttdot{width:.7rem;height:.7rem;border-radius:50%;
  box-shadow:0 0 6px 1px currentColor}
.ttleg .ttoff{opacity:.35}
#ttcui .tthot{background:#b3540f;color:#fff;border-color:#b3540f}
#ttname{min-height:1.4em;font-weight:700}
.tastetable td,.tastetable th{padding:.15rem .6rem;text-align:left}
.tastetable td.num{text-align:right;font-variant-numeric:tabular-nums}
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
            "background-position:center}" % ('ttbox', g))


def emit(g, data, frame):
    page, bi, esc = g["page"], g["bi"], g["esc"]
    share_block, BASE, DOCS = g["share_block"], g["BASE"], g["DOCS"]

    src = ROOT / "data" / "taste.json"
    if not src.exists():
        return "SKIPPED — no data/taste.json (run importers/build_taste.py)"
    taste = json.loads(src.read_text())
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data" / "taste.json").write_bytes(src.read_bytes())

    import shutil
    poster = ROOT / "assets" / "taste_poster.png"
    og = None
    if poster.exists():
        shutil.copyfile(poster, DOCS / "taste_poster.png")
        og = "taste_poster.png"
    # The framed family card (make_answer_cards.py) supersedes the bare
    # poster as the share preview; the poster stays published on the page.
    if (ROOT / "assets" / "og" / "taste.png").exists():
        og = "og/taste.png"

    vw = frame["mw"] + 2 * frame["pad"]
    vh = frame["mh"] + 2 * frame["pad"]
    in_frame = sum(1 for d in taste["dots"]
                   if frame["s"] <= d["la"] <= frame["n"]
                   and frame["w"] <= d["ln"] <= frame["e"])
    outside = len(taste["dots"]) - in_frame

    moat = ""
    ring = g["_moat_ring"]()
    if ring:
        pts = " ".join("%g,%g" % frame["px"](la, ln) for la, ln in ring)
        moat = ('<polygon points="%s" fill="none" stroke="#3d5a80" '
                'stroke-width="2" stroke-dasharray="6 4"/>' % pts)
    underlay = (
        ('<svg viewBox="0 0 %d %d" role="img" aria-label="แผนที่จุดร้านอาหารตามประเภท">' % (vw, vh))
        # The dark rectangle and the traced roads are the fallback, and they
        # step aside when the real ground is behind the box: two street
        # networks drawn a hair apart read as a printing error. What stays is
        # the moat, which is the one landmark worth stating twice.
        + ('' if frame.get("ground_night") else
           ('<rect width="%d" height="%d" fill="#0d1420"/>'
            '<path d="%s" fill="none" stroke="#22334a" stroke-width="1"/>'
            % (vw, vh, frame["road_d"])))
        + moat + '</svg>')

    fams = taste["families"]
    legend = "".join(
        '<button data-f="%s" style="color:%s">'
        '<span class="ttdot" style="background:%s"></span>%s '
        '<b>%d</b></button>'
        % (f["key"], f["color"], f["color"], bi(f["th"], f["en"]), f["n"])
        for f in fams)

    def tok_label(t):
        return TOKEN_TH.get(t, t.replace("_", " "))

    top_tokens = taste["stats"][:14]
    cui_chips = "".join(
        '<button data-t="%s">%s <b>%d</b></button>'
        % (s["t"], esc(tok_label(s["t"])), s["n"]) for s in top_tokens)

    # ---- the findings, served ---------------------------------------------
    st = {s["t"]: s for s in taste["stats"]}
    huddles = sorted(taste["stats"], key=lambda s: s["huddle_m"])[:5]
    spreads = sorted(taste["stats"], key=lambda s: -s["huddle_m"])[:3]

    def km(m):
        return ("%.1f" % (m / 1000)).rstrip("0").rstrip(".")

    story_th = (
        "เมืองนี้ครัวแยกย่าน: ร้านอินเดียกอดกันแน่นที่สุด — รัศมี %s กม. "
        "ทางตะวันออกของคูเมือง (ย่านช้างคลาน) ร้านอาหารเช้าเกาะกลุ่มห่างคูเมือง"
        "ไม่ถึงกิโล ญี่ปุ่นกับเบอร์เกอร์ถ่วงน้ำหนักไปทางตะวันตกเฉียงเหนือ "
        "(ฝั่งนิมมาน) ส่วน%sกระจายทั่วเมืองไม่เกาะใคร"
        % (km(huddles[0]["huddle_m"]),
           TOKEN_TH.get(spreads[0]["t"], spreads[0]["t"])))
    story_en = (
        "The kitchens keep neighborhoods: Indian huddles tightest — a %s km "
        "radius east of the moat (Chang Klan). Breakfast places cluster "
        "within a kilometre of the moat. Japanese and burgers weigh "
        "northwest toward Nimman, while %s spreads everywhere and belongs "
        "to no one street."
        % (km(huddles[0]["huddle_m"]),
           spreads[0]["t"].replace("_", " ")))

    rows = "".join(
        '<tr><td>%s</td><td class="num">%d</td><td class="num">%s</td>'
        '<td class="num">%s</td><td>%s</td></tr>'
        % (bi(esc(tok_label(s["t"])), esc(s["t"].replace("_", " "))), s["n"],
           km(s["huddle_m"]), km(s["moat_m"]), esc(s["dir"]))
        for s in taste["stats"])
    table = (
        '<div style="overflow-x:auto"><table class="tastetable">'
        '<thead><tr><th>%s</th><th>n</th><th>%s</th><th>%s</th>'
        '<th>%s</th></tr></thead><tbody>%s</tbody></table></div>'
        % (bi("ประเภท", "cuisine"),
           bi("รัศมีเกาะกลุ่ม (กม.)", "huddle radius (km)"),
           bi("ห่างคูเมือง (กม.)", "from the moat (km)"),
           bi("ทิศจากคูเมือง", "direction"), rows))

    lede_th = ("ร้านที่บอกประเภทอาหารไว้ %s แห่ง กลายเป็นจุดสีบนแผนที่กลางคืน "
               "— แตะป้ายประเภทแล้วดูว่าย่านไหนรสอะไร"
               % "{:,}".format(len(taste["dots"])))
    lede_en = ("%s places that state their cuisine, painted as colored dots "
               "on the night map — tap a cuisine and watch its belt light up."
               % "{:,}".format(len(taste["dots"])))

    method_th = (
        "วิธีอ่าน: สีคือประเภทอาหารแรกที่ร้านบอกไว้ใน OpenStreetMap "
        "(ร้านที่บอกหลายประเภท นับประเภทแรก) · ร้านที่ไม่บอกประเภท ไม่ถูกวาด "
        "— ไม่ได้แปลว่าไม่มีครัว · ตัวเลขภูมิศาสตร์วัดเฉพาะเชียงใหม่ "
        "(จุดเชียงรายวาดบนแผนที่จังหวัดตัวเอง แต่จุดศูนย์กลางข้ามจังหวัด"
        "คือทุ่งนากลางทาง เลยไม่นับ) · อีก %d จุดอยู่นอกกรอบ นับรวมในตัวเลข "
        "· คำนวณใหม่ทุกครั้งที่สร้างเว็บ" % outside)
    method_en = (
        "How to read it: a dot's color is the first cuisine the place "
        "states in OpenStreetMap (multi-tagged places count their first "
        "tag). A place stating no cuisine is not drawn — that never means "
        "it has no kitchen. Geography numbers are Chiang Mai only: a "
        "centroid computed across two provinces is a rice field between "
        "them. %d more dots sit outside this frame, counted in the totals. "
        "Recomputed every build." % outside)

    js = (_JS
          .replace("@FRAME@", json.dumps({
              "w": frame["w"], "e": frame["e"], "s": frame["s"],
              "n": frame["n"], "mw": frame["mw"], "mh": frame["mh"],
              "pad": frame["pad"], "vw": vw, "vh": vh}))
          .replace("@FAMS@", json.dumps(
              [[f["key"], f["color"]] for f in fams])))

    body = (
        '<h1>🌶️ %s</h1>'
        '<p class="lede">%s</p>'
        '<div class="ttleg">%s</div>'
        '<div id="ttcui">%s</div>'
        '<p id="ttname"> </p>'
        '<div id="ttbox">%s<canvas id="ttcv"></canvas></div>'
        '<p class="tinynote">%s · 🔆 <b id="ttcount"></b></p>'
        '<h2>%s</h2>'
        '<p>%s</p>'
        '%s'
        '<h2>%s</h2>'
        '<p class="tinynote">%s</p>'
        '<p><a href="data/taste.json">data/taste.json</a> · '
        '<a href="nitnoy.html">🏮 %s</a> · '
        '<a href="seven.html">🏪 %s</a></p>'
        '%s<script>%s</script>'
        % (
            bi("รสเมือง", "The taste of the town"),
            bi(lede_th, lede_en),
            legend,
            cui_chips,
            underlay,
            bi("ชี้จุดเพื่อดูชื่อร้าน", "hover a dot for its name"),
            bi("ครัวไหนเกาะย่าน ครัวไหนกระจาย",
               "Which kitchens keep a neighborhood"),
            bi(story_th, story_en),
            table,
            bi("วัดอย่างไร", "How we measured"),
            bi(method_th, method_en),
            bi("เมืองหลับนิดหน่อย", "the city that sleeps nitnoy"),
            bi("ใกล้เซเว่นแค่ไหน", "how near is the nearest 7-Eleven"),
            share_block(BASE + "taste.html", "รสเมือง · มดแดง"),
            js,
        ))

    (DOCS / "taste.html").write_text(page(
        "รสเมือง",
        body, depth=0, path="taste.html", desc=lede_th,
        extra_head="<style>%s%s</style>" % (_CSS, _ground_css(frame)), og=og))
    return ("taste.html — %d dots (%d in frame), %d tokens in stats"
            % (len(taste["dots"]), in_frame, len(taste["stats"])))
