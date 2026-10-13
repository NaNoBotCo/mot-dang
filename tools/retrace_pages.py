#!/usr/bin/env python3
"""Writes assets/sites/retrace/index.html and th/index.html (one template, two languages).

    python3 tools/retrace_pages.py

The map itself is assets/sites/retrace/rt.js; data/*.json come from tools/retrace_data.py.
Counts on the page are read from those files.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "assets" / "sites" / "retrace"
URL = "https://motdang.net/sites/retrace/"


def counts():
    pl = json.loads((SITE / "data" / "places.json").read_text())
    ph = json.loads((SITE / "data" / "photos.json").read_text())
    k = {}
    for r in pl:
        k[r[1]] = k.get(r[1], 0) + 1
    new = sum(1 for r in ph if r[6][:4] in ("2025", "2026"))
    return {"w": k.get("w", 0), "s": k.get("s", 0), "ph": len(ph), "h": k.get("h", 0), "new": new,
            "old": sum(1 for r in ph if r[6][:4] <= "2019")}


C = counts()

STR = {
    "en": dict(
        lang="en", title="Retrace · find the street you remember",
        desc="Tap the wats you passed in the order you passed them. Retrace draws the walk, the sun on it and the street photos along it, on the old city of Chiang Mai.",
        kicker="ย้อนรอย · Chiang Mai old city", h1="Retrace",
        lead="Tap the wats you passed, in the order you passed them. Retrace draws the walk between them, the sun on it at the hour you set, and the street photos along it.",
        start="Start a board", how_btn="How it works", nav=["Map", "How it works", "Numbers", "Say"],
        lang_link="/sites/retrace/th/", lang_name="ไทย",
        map_h="The board", map_p="A map of the old city on your screen. Touch it and it fills the screen; the strip at the bottom holds the tools.",
        how_h="How it works", how=[
            ("Tap the wats", "Each wat you tap gets a marigold number, 1, 2, 3, in the order you walked. The walk between them is drawn along the footpaths and roads."),
            ("Add clues", "A hotel close by, a café, the shrine, the shape of a spirit house. Tap them, or type a scrap of what you remember, and the places that fit light up."),
            ("Set the hour", "Pick the day and the time. The sun's direction is drawn, and the stretches where it was in your eyes or at your back turn gold."),
            ("Walk it", "Street photos along the route, in walking order. Swipe through them like walking, and say where a spirit house stands.")],
        slab_h="What is on the map", slab=[
            (C["w"], "wats"), (C["s"], "shrines, spirit houses and big trees"), (C["ph"], "street photos"), (C["h"], "places to stay")],
        age=f"{C['old']:,} of the photos were taken in 2019 or before; {C['new']:,} in 2025 or 2026. The year shows on every photo.",
        say_h="This is a test", say_p="Retrace is new, and the way to improve it is to watch it used. Use it for a real memory, then tell us what worked and what did not.",
        say_fb="Does Retrace work for you",
        say_log="Retrace sends a short log of your taps (tabs used, wats and clues counted, the sun time you set) along with thumbs and notes. The people who make it read the log to fix what trips testers up.",
        src_h="Where it comes from",
        src="Roads, water and place names: OpenStreetMap contributors (ODbL) and Mot Dang's own records. Street photos: Mapillary contributors, CC BY-SA 4.0, credited on each photo. Sun: NOAA solar equations for Chiang Mai. Spirit house drawings: The Spirit House Manual.",
        home="Mot Dang · มดแดง", home_link="/", manual="The Spirit House Manual", pop="Tap me",
        g1="Wat Phra Singh", g2="Wat Chedi Luang", g3="Wat Phan Tao",
    ),
    "th": dict(
        lang="th", title="ย้อนรอย · ตามหาถนนที่จำได้",
        desc="แตะวัดที่เดินผ่านตามลำดับ ย้อนรอยจะวาดเส้นทางเดิน แดดตามเวลา และรูปถนนตลอดทาง ในเมืองเก่าเชียงใหม่",
        kicker="Retrace · เมืองเก่าเชียงใหม่", h1="ย้อนรอย",
        lead="แตะวัดที่คุณเดินผ่านตามลำดับ ย้อนรอยจะวาดทางเดินระหว่างวัด แดดในเวลาที่ตั้ง และรูปถนนตลอดทาง",
        start="เริ่มกระดาน", how_btn="ใช้อย่างไร", nav=["แผนที่", "ใช้อย่างไร", "ตัวเลข", "บอกเรา"],
        lang_link="/sites/retrace/", lang_name="English",
        map_h="กระดาน", map_p="แผนที่เมืองเก่าบนหน้าจอ แตะแล้วแผนที่เต็มจอ แถบด้านล่างคือเครื่องมือ",
        how_h="ใช้อย่างไร", how=[
            ("แตะวัด", "วัดที่แตะจะได้เลขสีดอกบวบ 1 2 3 ตามลำดับที่เดิน ทางเดินระหว่างวัดวาดตามทางเท้าและถนน"),
            ("เพิ่มเบาะแส", "โรงแรมใกล้ ๆ คาเฟ่ ศาล รูปทรงศาลพระภูมิ แตะเลือก หรือพิมพ์เศษความจำ สถานที่ที่เข้ากันจะสว่างขึ้น"),
            ("ตั้งเวลา", "เลือกวันและเวลา ทิศของแดดถูกวาดไว้ ช่วงที่แดดเข้าตาหรืออยู่ข้างหลังจะเป็นสีทอง"),
            ("เดินดู", "รูปถนนตลอดเส้นทางเรียงตามที่เดิน ปัดดูเหมือนเดิน แล้วบอกว่าศาลพระภูมิอยู่ตรงไหน")],
        slab_h="ในแผนที่มีอะไรบ้าง", slab=[
            (C["w"], "วัด"), (C["s"], "ศาล ศาลพระภูมิ และต้นไม้ใหญ่"), (C["ph"], "รูปถนน"), (C["h"], "ที่พัก")],
        age=f"รูปถ่ายปี 2019 หรือก่อนนั้น {C['old']:,} รูป ปี 2025–2026 {C['new']:,} รูป ปีที่ถ่ายแสดงบนทุกรูป",
        say_h="นี่คือการทดลอง", say_p="ย้อนรอยเพิ่งเริ่ม วิธีที่ดีที่สุดคือดูคนใช้จริง ลองใช้กับความทรงจำจริง แล้วบอกเราว่าอะไรใช้ได้ อะไรไม่ได้",
        say_fb="ย้อนรอยใช้ได้ไหม",
        say_log="ย้อนรอยส่งบันทึกสั้น ๆ ว่าคุณแตะอะไร (แท็บที่ใช้ จำนวนวัดและเบาะแส เวลาแดดที่ตั้ง) มาพร้อมนิ้วโป้งและข้อความ ผู้ทำอ่านบันทึกนี้เพื่อแก้จุดที่ผู้ทดลองสะดุด",
        src_h="ที่มา",
        src="ถนน น้ำ และชื่อสถานที่: ผู้ร่วมสร้าง OpenStreetMap (ODbL) และข้อมูลของมดแดง รูปถนน: ผู้ร่วมสร้าง Mapillary, CC BY-SA 4.0 ระบุชื่อบนทุกรูป แดด: สมการสุริยะ NOAA สำหรับเชียงใหม่ ภาพศาลพระภูมิ: คู่มือศาลพระภูมิ",
        home="Mot Dang · มดแดง", home_link="/", manual="คู่มือศาลพระภูมิ", pop="แตะดู",
        g1="วัดพระสิงห์", g2="วัดเจดีย์หลวง", g3="วัดพันเถา",
    ),
}

CSS = """
@font-face{font-family:'Prompt';font-weight:600;font-display:swap;src:url(/sites/retrace/fonts/prompt-600-thai.woff2) format('woff2');unicode-range:U+0E01-0E5B,U+200C-200D,U+25CC}
@font-face{font-family:'Prompt';font-weight:600;font-display:swap;src:url(/sites/retrace/fonts/prompt-600-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2212,U+0E3F}
@font-face{font-family:'Sarabun';font-weight:400;font-display:swap;src:url(/sites/retrace/fonts/sarabun-400-thai.woff2) format('woff2');unicode-range:U+0E01-0E5B,U+200C-200D,U+25CC}
@font-face{font-family:'Sarabun';font-weight:400;font-display:swap;src:url(/sites/retrace/fonts/sarabun-400-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2212,U+0E3F}
@font-face{font-family:'Sarabun';font-weight:600;font-display:swap;src:url(/sites/retrace/fonts/sarabun-600-thai.woff2) format('woff2');unicode-range:U+0E01-0E5B,U+200C-200D,U+25CC}
@font-face{font-family:'Sarabun';font-weight:600;font-display:swap;src:url(/sites/retrace/fonts/sarabun-600-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2212,U+0E3F}
:root{--paper:#f6efe2;--ink:#1d1712;--mute:#645a4c;--gold:#f2a900;--rust:#c8431e;--dark:#17120d;--cream:#f3ecd8;--line:#d9ccb0;--rule:#b9a98a;--link:#8a3a10}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--paper:#17120d;--ink:#f3ecd8;--mute:#b8ab95;--line:#3a2f23;--rule:#6b5b45;--link:#f2b968;--dark:#0e0a07}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:3.4rem}
body{margin:0;background:var(--paper);color:var(--ink);font:400 18px/1.6 'Sarabun',system-ui,sans-serif;-webkit-text-size-adjust:100%}
body.rt-lock{overflow:hidden;overscroll-behavior:none}
a{color:var(--link);text-underline-offset:3px}
h1,h2,h3,.kicker,nav.top,.slab b,.gold,.strip,.chip,.big{font-family:'Prompt','Sarabun',system-ui,sans-serif;font-weight:600}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px}
nav.top{position:sticky;top:0;z-index:30;display:flex;gap:.2rem;align-items:center;overflow-x:auto;background:var(--dark);padding:.35rem 10px;scrollbar-width:none}
nav.top::-webkit-scrollbar{display:none}
nav.top a{color:var(--cream);text-decoration:none;padding:.4rem .75rem;border-radius:99px;white-space:nowrap;font-size:.85rem;letter-spacing:.05em;text-transform:uppercase}
nav.top a:hover,nav.top a:focus-visible{background:#33281c}
nav.top .home{color:var(--gold)}
nav.top .lang{margin-left:auto;background:var(--gold);color:#000}
.gold,button.gold,a.gold{background:var(--gold);color:#000;border:2px solid #000;border-radius:10px;padding:.65rem 1.1rem;font-size:1rem;text-decoration:none;cursor:pointer;display:inline-block;min-height:44px}
.gold:hover{filter:brightness(1.07)}
.hero{background:var(--dark);color:var(--cream);overflow:hidden}
.hero .wrap{display:grid;gap:1.2rem;padding-top:2.4rem;padding-bottom:2.4rem;align-items:center}
@media(min-width:820px){.hero .wrap{grid-template-columns:1.1fr .9fr}}
.kicker{font-size:.78rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin:0 0 .5rem}
h1{font-size:clamp(3.2rem,12vw,7.4rem);line-height:.9;margin:0 0 .6rem;letter-spacing:-.02em;text-transform:uppercase}
.lead{font-size:clamp(1.05rem,2.4vw,1.35rem);max-width:34ch;margin:0 0 1.3rem;color:#eadfc8}
.hero .row{display:flex;flex-wrap:wrap;gap:.7rem}
.hero a.alt{color:var(--cream);border:2px solid var(--cream);border-radius:10px;padding:.65rem 1.1rem;text-decoration:none;min-height:44px;font-family:'Prompt',sans-serif}
.art{width:100%;max-width:440px;justify-self:center;cursor:pointer;display:block}
.art svg{width:100%;height:auto;display:block}
.tapfx{-webkit-tap-highlight-color:transparent}
.tapfx:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.art .d{transform-box:fill-box;transform-origin:center;animation:none}
.art.go .d{animation:pop .5s cubic-bezier(.3,1.6,.5,1) both}
.art.go .d2{animation-delay:.25s}.art.go .d3{animation-delay:.5s}
@keyframes pop{0%{transform:scale(0)}100%{transform:scale(1)}}
.art .sun{transform-box:view-box;transform-origin:200px 200px;transition:transform 1.2s cubic-bezier(.3,.7,.3,1)}
.art.go .sun{transform:rotate(120deg)}
.art .band{stroke-dasharray:420;stroke-dashoffset:0}
.art.go .band{animation:draw 1.1s ease both}
@keyframes draw{from{stroke-dashoffset:420}to{stroke-dashoffset:0}}
section{padding:2.6rem 0}
h2{font-size:clamp(1.7rem,5vw,2.6rem);line-height:1.05;margin:0 0 .7rem;text-transform:uppercase;letter-spacing:-.01em}
.sub{color:var(--mute);max-width:56ch;margin:0 0 1.2rem}
#tool{margin:0}
.stage{position:relative;height:clamp(420px,72svh,720px);background:#efe5cf;border-top:3px solid var(--ink);border-bottom:3px solid var(--ink);overflow:hidden}
.stage #rt{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:pan-y;cursor:pointer}
#tool.full{position:fixed;inset:0;z-index:1000}
#tool.full .stage{height:100%;height:100dvh;border:0}
#tool.full #rt{touch-action:none;cursor:grab}
.veil{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:.6rem;padding:1rem 1rem 1.6rem;pointer-events:none;background:linear-gradient(180deg,rgba(23,18,13,0) 40%,rgba(23,18,13,.5))}
.veil span{background:rgba(239,229,207,.9);color:var(--ink);padding:.2rem .6rem;border-radius:6px;font-size:.9rem}
.veil span:empty{display:none}
.veil button{pointer-events:auto}
#tool.full .veil{display:none}
.top,.strip,.sheet,.card{display:none}
#tool.full .top{display:flex}
#tool.full .strip{display:flex}
.top{position:absolute;top:0;left:0;right:0;align-items:flex-start;gap:.6rem;padding:.5rem .6rem;padding-top:max(.5rem,env(safe-area-inset-top));pointer-events:none;color:#000}
.top *{pointer-events:auto}
.top b{font-size:1.05rem;text-shadow:0 0 6px #efe5cf,0 0 6px #efe5cf;letter-spacing:.04em;text-transform:uppercase}
.top .x,.top #rt-zoom button{width:44px;height:44px;border-radius:50%;border:2px solid #000;background:var(--gold);color:#000;font:600 22px/1 'Prompt',sans-serif;cursor:pointer;padding:0}
#rt-zoom{position:absolute;right:.6rem;top:calc(max(.5rem,env(safe-area-inset-top)) + 118px);display:flex;flex-direction:column;gap:6px}
.top b{align-self:center}
.strip{position:absolute;left:0;right:0;bottom:0;background:var(--dark);padding:.3rem .3rem max(.3rem,env(safe-area-inset-bottom));gap:.25rem;z-index:3}
.strip button{flex:1;min-width:0;min-height:50px;border:0;border-radius:10px;background:transparent;color:var(--cream);font-size:.7rem;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;cursor:pointer;letter-spacing:.03em}
.strip svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.strip button.on{background:var(--gold);color:#000}
.strip button:focus-visible{outline:3px solid var(--gold);outline-offset:-2px}
.sheet{position:absolute;left:0;right:0;bottom:var(--strip,58px);max-height:42dvh;overflow:auto;background:var(--dark);color:var(--cream);padding:.8rem 1rem 1rem;border-top:3px solid var(--gold);z-index:2;overscroll-behavior:contain;font-size:.95rem}
#tool.full .sheet:not([hidden]){display:block}
.sheet .hint{margin:.1rem 0 .6rem;font-size:1rem}
.sheet .sub{margin:.8rem 0 .3rem;color:#cdbf9f;font-family:'Prompt',sans-serif;font-weight:600;font-size:.8rem;letter-spacing:.12em;text-transform:uppercase}
.sheet .note{color:#cdbf9f;margin:.5rem 0;font-size:.9rem}
.sheet button,.card button{font:600 .88rem 'Prompt','Sarabun',sans-serif;min-height:40px;padding:.35rem .8rem;border-radius:9px;border:2px solid var(--cream);background:transparent;color:var(--cream);cursor:pointer}
.sheet button.gold,.card button.gold{background:var(--gold);color:#000;border-color:#000}
.sheet .row{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.55rem 0}
.sheet .chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.4rem 0}
.sheet .chip.on{background:var(--gold);color:#000;border-color:#000}
.sheet .big{font-size:1.4rem}
.sheet input[type=search],.sheet input[type=date]{flex:1;min-height:42px;border-radius:9px;border:2px solid var(--cream);background:#241b13;color:var(--cream);padding:.3rem .6rem;font:400 1rem 'Sarabun',sans-serif;min-width:0}
.sheet input[type=range]{width:100%;accent-color:var(--gold);height:34px}
.sheet .find{display:flex;gap:.5rem;margin:.5rem 0}
.sheet ol.order,.sheet ul.clist{list-style:none;margin:.4rem 0;padding:0;display:grid;gap:.35rem}
.sheet li{display:flex;gap:.45rem;align-items:center}
.sheet li .nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sheet li button{min-width:40px;padding:.2rem .5rem}
.no{width:30px;height:30px;border-radius:50%;background:var(--gold);color:#000;display:grid;place-items:center;font-family:'Prompt',sans-serif;font-weight:600;flex:none}
.houses{display:grid;grid-template-columns:repeat(5,1fr);gap:.35rem}
.houses .hs{display:flex;flex-direction:column;align-items:center;gap:2px;padding:.2rem;font-size:.66rem;border-width:2px;min-height:0;background:#efe5cf;color:#000;border-color:#efe5cf}
.houses .hs.on{border-color:var(--gold);outline:3px solid var(--gold)}
.houses canvas{width:100%;height:auto;display:block;pointer-events:none}
.tag{display:inline-block;background:#33281c;border:1px solid var(--rule);border-radius:99px;padding:.15rem .7rem;font-size:.85rem;margin:2px 0}
.tag b{color:var(--gold)}.tag.maybe{border-style:dashed}
.viewer img{width:100%;max-height:30dvh;object-fit:cover;border-radius:8px;background:#000;display:block}
.vcap{font-size:.8rem;color:#cdbf9f;margin-top:.3rem}
.vcap a{color:#f2c779}
.fb{margin-top:.6rem;border-top:1px solid #33281c;padding-top:.2rem}
.sheet .mdfb{margin:.5rem 0 .2rem;color:#cdbf9f}
.card{position:absolute;left:10px;right:10px;bottom:calc(var(--cover,58px) + 8px);z-index:4;background:var(--paper);color:var(--ink);border:3px solid #000;border-radius:12px;padding:.5rem;gap:.6rem}
#tool.full .card:not([hidden]){display:flex}
.card img{width:92px;height:92px;object-fit:cover;border-radius:8px;flex:none}
.card .ct{flex:1;min-width:0;display:flex;flex-direction:column;gap:.15rem}
.card .ct b{font-family:'Prompt',sans-serif;font-size:1.02rem;line-height:1.2}
.card .ct span{font-size:.82rem;color:var(--mute)}
.card .cb{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.3rem}
.card .cb a{align-self:center;font-size:.85rem}
.card button{color:var(--ink);border-color:var(--ink);min-height:38px}
.card .x{position:absolute;right:4px;top:2px;border:0;font-size:1.4rem;min-height:36px;padding:0 .5rem}
.card.pop{animation:cardin .25s ease}
@keyframes cardin{from{transform:translateY(14px);opacity:0}to{transform:none;opacity:1}}
.toast{position:absolute;left:50%;top:70px;transform:translateX(-50%) scale(.9);background:#000;color:#fff;padding:.5rem 1rem;border-radius:99px;opacity:0;transition:all .25s;pointer-events:none;z-index:6;font-size:.9rem}
.toast.on{opacity:1;transform:translateX(-50%) scale(1)}
.cards{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.hc{background:#fffaf0;color:#1d1712;border:2px solid var(--ink);border-radius:14px;padding:1rem;cursor:pointer}
.hc h3{margin:.4rem 0 .3rem;font-size:1.15rem}
.hc p{margin:0;font-size:.95rem;line-height:1.5}
.hc svg{width:100%;height:92px;display:block}
.hc .gg{transform-box:fill-box;transform-origin:center}
.hc.go .p1{animation:pop .5s cubic-bezier(.3,1.6,.5,1) both}.hc.go .p2{animation:pop .5s .2s cubic-bezier(.3,1.6,.5,1) both}.hc.go .p3{animation:pop .5s .4s cubic-bezier(.3,1.6,.5,1) both}
.hc.go .ring{animation:ringin .8s ease both}
@keyframes ringin{from{stroke-dashoffset:90}to{stroke-dashoffset:0}}
.hc .sunball{transition:transform 1s cubic-bezier(.3,.7,.3,1);transform-box:view-box}
.hc.go .sunball{transform:translate(120px,-28px)}
.hc.go .fr{animation:slide .6s ease both}.hc.go .fr2{animation-delay:.15s}.hc.go .fr3{animation-delay:.3s}
@keyframes slide{from{transform:translateX(40px);opacity:0}to{transform:none;opacity:1}}
.slabs{background:var(--dark);color:var(--cream)}
.slab{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-top:1rem}
.slab div{border-top:4px solid var(--gold);padding-top:.5rem;cursor:pointer}
.slab b{display:block;font-size:clamp(2.2rem,8vw,3.6rem);line-height:1;color:var(--gold)}
.slab span{font-size:.95rem;color:#e6dac2}
.slabs .age{margin-top:1.2rem;color:#cdbf9f;max-width:60ch}
.fbbox{background:#fffaf0;color:#1d1712;border:2px solid var(--ink);border-radius:14px;padding:1rem;max-width:60ch}
.fbbox .mdfb{color:#645a4c;margin:.4rem 0}
footer{padding:2rem 0 3rem;border-top:3px solid var(--ink);color:var(--mute);font-size:.88rem}
footer a{color:var(--link)}
html[lang=th] .kicker,html[lang=th] nav.top a,html[lang=th] .sheet .sub,html[lang=th] h1,html[lang=th] h2,html[lang=th] .strip button{letter-spacing:0;text-transform:none}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}
"""


def hero_svg(s):
    return f"""<svg viewBox="0 0 400 400" role="img" aria-label="{s['g1']} · {s['g2']} · {s['g3']}">
<rect width="400" height="400" rx="18" fill="#efe5cf"/>
<rect x="46" y="46" width="308" height="308" rx="16" fill="none" stroke="#a9d3cc" stroke-width="16"/>
<rect x="60" y="60" width="280" height="280" rx="10" fill="none" stroke="#86b9b0" stroke-width="2"/>
<g stroke="#fffaf0" stroke-width="9" fill="none" stroke-linecap="round"><path d="M60 200H340M200 60V340M110 110L290 290"/></g>
<g stroke="#c9b88f" stroke-width="1.5" fill="none" stroke-dasharray="4 4"><path d="M90 150H200M200 250H320M140 200V300"/></g>
<g fill="#2b2118"><path d="M200 38l9 9-9 9-9-9z"/><path d="M200 344l9 9-9 9-9-9z"/><path d="M38 200l9 9-9 9-9-9z" transform="translate(0 -9)"/><path d="M344 200l9 9-9 9-9-9z" transform="translate(0 -9)"/></g>
<path class="band" d="M120 140L200 200L270 260" stroke="rgba(242,169,0,.45)" stroke-width="36" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<path class="band" d="M120 140L200 200L270 260" stroke="#7a3b00" stroke-width="3" fill="none" stroke-dasharray="8 5" stroke-linecap="round"/>
<g font-family="Prompt,sans-serif" font-weight="600" font-size="18" text-anchor="middle">
<g class="d d1"><circle cx="120" cy="140" r="16" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="120" y="146" fill="#000">1</text></g>
<g class="d d2"><circle cx="200" cy="200" r="16" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="200" y="206" fill="#000">2</text></g>
<g class="d d3"><circle cx="270" cy="260" r="16" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="270" y="266" fill="#000">3</text></g></g>
<g class="sun"><circle cx="200" cy="-8" r="0" fill="none"/><g transform="translate(200 24)"><circle r="13" fill="#f2a900" stroke="#fff6dc" stroke-width="3"/></g></g>
</svg>"""


def card_svgs():
    return [
        """<svg viewBox="0 0 220 92" aria-hidden="true"><path d="M30 60L110 30L190 62" stroke="#c9b88f" stroke-width="3" fill="none" stroke-dasharray="6 5"/>
<g font-family="Prompt,sans-serif" font-weight="600" font-size="15" text-anchor="middle"><g class="gg p1"><circle cx="30" cy="60" r="14" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="30" y="65.5" fill="#000">1</text></g>
<g class="gg p2"><circle cx="110" cy="30" r="14" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="110" y="35.5" fill="#000">2</text></g>
<g class="gg p3"><circle cx="190" cy="62" r="14" fill="#f2a900" stroke="#2b1a00" stroke-width="3"/><text x="190" y="67.5" fill="#000">3</text></g></g></svg>""",
        """<svg viewBox="0 0 220 92" aria-hidden="true"><g fill="none" stroke="#2b2118" stroke-width="3"><circle class="ring" cx="45" cy="46" r="24" stroke-dasharray="90 90"/><circle class="ring" cx="110" cy="46" r="24" stroke-dasharray="6 5"/><circle class="ring" cx="175" cy="46" r="24" stroke-dasharray="90 90"/></g>
<g class="gg p1"><rect x="35" y="38" width="20" height="16" fill="#2f6fbf"/><path d="M32 38L45 26L58 38z" fill="#2f6fbf"/></g>
<g class="gg p2"><path d="M98 36h24v16a12 12 0 0 1-24 0z" fill="#7a4a22"/><path d="M122 40h6a6 6 0 0 1 0 12h-6" fill="none" stroke="#7a4a22" stroke-width="3"/></g>
<g class="gg p3"><rect x="173" y="36" width="4" height="22" fill="#b8860b"/><path d="M162 38L175 26L188 38z" fill="#b8860b"/><rect x="167" y="38" width="16" height="10" fill="#e0ac2a"/></g></svg>""",
        """<svg viewBox="0 0 220 92" aria-hidden="true"><path d="M20 80Q110 -30 200 80" fill="none" stroke="#c9b88f" stroke-width="3" stroke-dasharray="5 5"/><g class="sunball"><circle cx="40" cy="64" r="13" fill="#f2a900" stroke="#fff6dc" stroke-width="3"/></g><path d="M20 82H200" stroke="#2b2118" stroke-width="3"/></svg>""",
        """<svg viewBox="0 0 220 92" aria-hidden="true"><g stroke="#2b2118" stroke-width="3"><rect class="fr fr1" x="14" y="22" width="56" height="46" rx="5" fill="#a9d3cc"/><rect class="fr fr2" x="82" y="22" width="56" height="46" rx="5" fill="#efe5cf"/><rect class="fr fr3" x="150" y="22" width="56" height="46" rx="5" fill="#f2c779"/></g>
<path d="M26 58l12-14 10 10 8-6 8 10z" fill="#2f6b2a" opacity=".6"/><path d="M164 58l14-16 10 12 10-8 6 12z" fill="#b8860b" opacity=".6"/></svg>""",
    ]


def page(lang):
    s = STR[lang]
    other = "en" if lang == "th" else "th"
    here = URL if lang == "en" else URL + "th/"
    alt = STR[other]
    cards = card_svgs()
    how = "".join(
        f'<div class="hc tapfx" tabindex="0" role="button" aria-label="{h}">{cards[i]}<h3>{i + 1}. {h}</h3><p>{p}</p></div>'
        for i, (h, p) in enumerate(s["how"]))
    slab = "".join(f'<div class="tapfx" tabindex="0" role="button"><b data-n="{n}">{n:,}</b><span>{lbl}</span></div>' for n, lbl in s["slab"])
    nav = s["nav"]
    return f"""<!doctype html><html lang="{s['lang']}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{s['title']}</title>
<meta name="description" content="{s['desc']}">
<meta name="theme-color" content="#17120d">
<link rel="canonical" href="{here}">
<link rel="alternate" hreflang="en" href="{URL}"><link rel="alternate" hreflang="th" href="{URL}th/"><link rel="alternate" hreflang="x-default" href="{URL}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Mot Dang · มดแดง">
<meta property="og:title" content="{s['title']}"><meta property="og:description" content="{s['desc']}"><meta property="og:url" content="{here}">
<meta property="og:image" content="{URL}card.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="A map of the old city of Chiang Mai with three numbered wats joined by a marigold band, beside the word Retrace.">
<meta property="og:locale" content="{'th_TH' if lang == 'th' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{URL}card.jpg">
<link rel="icon" href="/sites/retrace/icon.svg" type="image/svg+xml">
<style>{CSS}</style></head><body>
<nav class="top" aria-label="Retrace"><a class="home" href="/">Mot Dang</a><a href="#map">{nav[0]}</a><a href="#how">{nav[1]}</a><a href="#numbers">{nav[2]}</a><a href="#say">{nav[3]}</a><a class="lang" href="{s['lang_link']}" hreflang="{other}">{s['lang_name']}</a></nav>
<header class="hero"><div class="wrap"><div>
<p class="kicker">{s['kicker']}</p><h1>{s['h1']}</h1><p class="lead">{s['lead']}</p>
<div class="row"><a class="gold" href="#map" data-open>{s['start']}</a><a class="alt" href="#how">{s['how_btn']}</a></div></div>
<div class="art tapfx" tabindex="0" role="button" aria-label="{s['pop']}">{hero_svg(s)}</div></div></header>
<section id="map" style="padding:0"><div class="wrap" style="padding-top:2rem;padding-bottom:1rem"><h2>{s['map_h']}</h2><p class="sub">{s['map_p']}</p></div><div id="tool"></div></section>
<section id="how"><div class="wrap"><h2>{s['how_h']}</h2><div class="cards">{how}</div></div></section>
<section id="numbers" class="slabs"><div class="wrap"><h2>{s['slab_h']}</h2><div class="slab">{slab}</div><p class="age">{s['age']}</p></div></section>
<section id="say"><div class="wrap"><h2>{s['say_h']}</h2><div class="fbbox"><p style="margin-top:0">{s['say_p']}</p><div data-fb="retrace:site"></div><p style="margin-bottom:0;font-size:.9rem;color:#645a4c">{s['say_log']}</p></div></div></section>
<footer><div class="wrap"><p><b>{s['src_h']}</b><br>{s['src']}</p><p><a href="/">{s['home']}</a> · <a href="/sites/spirit-house/">{s['manual']}</a></p></div></footer>
<script src="/sites/retrace/rt.js" defer></script>
<script src="/feedback.js" defer></script>
</body></html>"""


def main():
    (SITE / "th").mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(page("en"), encoding="utf-8")
    (SITE / "th" / "index.html").write_text(page("th"), encoding="utf-8")
    print("pages written", C)


if __name__ == "__main__":
    main()
