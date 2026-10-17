#!/usr/bin/env python3
"""shelfmap_layer.py — a shelf opens on its doodle map, and its chips switch the pins.

Nan, 2026-10-12, over /cm/cannabis/yan-mueang-kao.html: "All these shelves should
include a doodle map front and center, with pins and filter within the category …
for C&K I should be able to isolate 'open in morning' or 'delivers', or 'has line',
just like any other kind of place. Isolation of attributes should toggle descriptive
pins on and off, just like on the motdang homepage. The main driver of all shelf
pages should be a map." Then: "The links should also contain preview information.
Everywhere."

What a list page gets (build.listing_pages, every page of every shelf, sub-shelf,
neighbourhood and tag list):

  block()      under the h1: the doodle map (/sites/doodle-map/ or the Chiang Rai
               one, ?embed=1&shelf=1) and a row of chips counted over the whole
               list. A chip narrows the pins and the rows together; two chips mean
               both. The map gets its marks from the page (postMessage md-shelf).
  row_attrs()  data-f (the chip keys a row carries) and data-s (its week, for
               "open now"), on build.entry_li's <li>
  preview()    the line under a row's name: kind · street · today's hours ·
               phone · LINE · delivery
  write_json() a list longer than one page also writes <page>.map.json beside it,
               so the map and the chips cover the rows on the other pages
  JS / CSS     /shelf.js, and rules appended to style.css

The chips come from what the records already carry: the tags (tags_layer; the
`state` family describes our record, not the place, and is left out), the shelf's
facets, the week from data/open_lamps.json (open at 09:00 on some day = mornings),
and the LINE channel build.channels() finds. A chip that every row or no row
carries is not drawn.
"""
import json
import re

MORNING_MIN = 9 * 60          # open at 09:00 on at least one day
SKIP_FAMILIES = {"state", "area"}
FIRST = ("now", "morning", "open-early", "open-late", "open-24h", "delivery", "line",
         "takeaway", "open-sunday", "open-monday")
EXTRA = {
    "now": ("เปิดอยู่ตอนนี้", "Open now", "i-clock",
            "ตามเวลาเปิด-ปิดที่บันทึกไว้", "by the recorded opening hours"),
    "morning": ("เปิดเช้า", "Open mornings", "i-sun",
                "เปิดตอน 9 โมงเช้าอย่างน้อยหนึ่งวัน", "open at 09:00 on at least one day"),
    "line": ("มี LINE", "LINE", "i-chat",
             "มีบัญชี LINE ให้ทักได้", "a LINE account to message"),
    "photo": ("มีรูป", "Photo", "i-camera", "", ""),
}

_CACHE = {}


def _sched(g, r):
    rows, by_id = g["lamps"]()
    k = by_id.get(r["id"])
    if k is None or not (0 <= k < len(rows)):
        return None
    if g["place_status"](r):
        return None
    return rows[k]


def _morning(iv):
    for a, b in iv or ():
        for d in range(8):
            m = d * 1440 + MORNING_MIN
            if a <= m < b:
                return True
    return False


def _tag_alias(g):
    """facet key -> tag slug, where a tag already counts that facet (or_facet)."""
    t = g.get("TAGS") or {}
    if "_alias" in t:
        return t["_alias"]
    al = {}
    for slug, d in (t.get("defs") or {}).items():
        of = (d.get("rule") or {}).get("or_facet")
        if of:
            al[of] = slug
    for fk, slug in (("delivery", "delivery"), ("takeaway", "takeaway"), ("card", "cards"),
                     ("wifi", "wifi"), ("aircon", "air-con"), ("wheelchair", "wheelchair"),
                     ("openlate", "open-late"), ("open24", "open-24h")):
        if slug in (t.get("defs") or {}):
            al.setdefault(fk, slug)
    t["_alias"] = al
    return al


def facts(g, r):
    """{keys, sched, line, tel, area, kind} for one record, once a build."""
    rid = r["id"]
    hit = _CACHE.get(rid)
    if hit is not None:
        return hit
    T = g.get("TAGS") or {}
    defs = T.get("defs") or {}
    keys = []
    for s in (T.get("by_id") or {}).get(rid) or []:
        d = defs.get(s) or {}
        if d.get("family") in SKIP_FAMILIES:
            continue
        keys.append(s)
    al = _tag_alias(g)
    for fk in g["facet_bits"](r):
        k = al.get(fk) or "f-" + fk
        if k not in keys:
            keys.append(k)
    sch = _sched(g, r)
    if _morning(sch):
        keys.append("morning")
    line = tel = None
    try:
        live, _ = g["channels"](r)
    except Exception:                          # noqa: BLE001
        live = []
    for c in live:
        if c.get("kind") == "line" and not line:
            line = c.get("href")
        elif c.get("kind") == "phone" and not tel:
            tel = (c.get("href"), c.get("text"))
    if line:
        keys.append("line")
    area = None
    stg = g["STREET_OF"].get(rid)
    if stg:
        area = stg[0].get("name") or stg[0].get("nameEn")
    elif (r.get("attrs") or {}).get("tambon"):
        area = "ต." + r["attrs"]["tambon"]
    kind = None
    subs = r.get("sub") or []
    for s in subs:
        lab = g["SUB_LABELS"].get(s)
        if lab:
            kind = (lab.get("th") or "", lab.get("en") or "")
            break
    if not kind:
        for c in r.get("cat") or []:
            cc = g["CATS"].get(c)
            if cc:
                kind = (cc.get("th") or "", cc.get("en") or "")
                break
    out = {"keys": keys, "sched": sch, "line": line, "tel": tel, "area": area, "kind": kind}
    if T.get("by_id") is not None and g["STREET_OF"]:     # not before tags and streets are known
        _CACHE[rid] = out
    return out


def _sched_attr(iv):
    return ",".join("%d-%d" % (a, b) for a, b in iv) if iv else ""


def row_attrs(g, r):
    """data-f and data-s for a list row's <li>."""
    f = facts(g, r)
    att = g["att"]
    out = ""
    if f["keys"]:
        out += ' data-f="%s"' % att(" ".join(f["keys"]))
    if f["sched"]:
        out += ' data-s="%s"' % _sched_attr(f["sched"])
    return out


def _short_hours(h):
    h = re.sub(r"\s+", " ", str(h or "")).strip()
    return h if len(h) <= 44 else h[:43].rstrip(" ;,") + "…"


def _local_phone(t):
    """+66926232326 -> 092 623 2326, the way a number is written and said here."""
    d = re.sub(r"\D", "", str(t or ""))
    if d.startswith("66") and len(d) in (10, 11):
        d = "0" + d[2:]
    if len(d) == 10 and d.startswith("0"):
        return "%s %s %s" % (d[:3], d[3:6], d[6:])
    if len(d) == 9 and d.startswith("02"):
        return "%s %s %s" % (d[:2], d[2:5], d[5:])
    if len(d) == 9 and d.startswith("0"):
        return "%s %s %s" % (d[:3], d[3:6], d[6:])
    return str(t or "")


def preview(g, r):
    """The line under a row's name: what, where, when, how to reach it."""
    f = facts(g, r)
    bi, esc, att, icon = g["bi"], g["esc"], g["att"], g["svg_icon"]
    bits = []
    if f["kind"]:
        bits.append('<span class="rpk">%s</span>' % bi(*f["kind"]))
    if f["area"]:
        bits.append('<span class="rpa">%s</span>' % esc(f["area"]))
    hrs = r.get("hours")
    if f["sched"] or hrs:
        bits.append('<span class="rph"%s>%s</span>' % (
            (' data-s="%s"' % _sched_attr(f["sched"])) if f["sched"] else "",
            esc(_short_hours(hrs)) if hrs else ""))
    if f["tel"] and f["tel"][0]:
        bits.append('<a class="rpt" href="%s">%s%s</a>' % (
            att(f["tel"][0]), icon("i-phone", 14), esc(_local_phone(f["tel"][1] or f["tel"][0]))))
    if f["line"]:
        bits.append('<a class="rpl" href="%s" rel="nofollow noopener">%sLINE</a>' % (
            att(f["line"]), icon("i-chat", 14)))
    if "delivery" in f["keys"]:
        bits.append('<span class="rpd">%s</span>' % bi("ส่งถึงที่", "delivers"))
    if not bits:
        return ""
    return '<span class="rpv">%s</span>' % " ".join(bits)


# ------------------------------------------------------------------ the chips
def _label(g, k):
    """(th, en, glyph-or-icon html, note)"""
    icon = g["svg_icon"]
    if k in EXTRA:
        th, en, ic, nth, nen = EXTRA[k]
        return th, en, icon(ic, 16), (nth, nen)
    if k.startswith("f-"):
        fk = k[2:]
        for fs in g["FACET_SETS"]:
            for x in fs["facets"]:
                if x["key"] == fk:
                    return x["th"], x["en"], x.get("icon") or "", ("", "")
        return fk, fk, "", ("", "")
    if k.startswith("s-"):
        lab = g["SUB_LABELS"].get(k[2:]) or {}
        return lab.get("th") or k[2:], lab.get("en") or k[2:], "", ("", "")
    d = ((g.get("TAGS") or {}).get("defs") or {}).get(k) or {}
    return d.get("th") or k, d.get("en") or k, d.get("glyph") or "", ("", "")


def _glyph(gl):
    """A tag's or facet's mark, only where the site's icon set draws it (no stray emoji)."""
    if not gl:
        return ""
    try:
        import glyphs
        out = glyphs.emoji_to_icon(gl)
    except Exception:                          # noqa: BLE001
        return ""
    return out if out != gl and "<svg" in out else ""


def chip_keys(g, records):
    """[(key, count)] for a list, in the order the chips are drawn."""
    n = len(records)
    cnt = {}
    has_s = 0
    subs = {}
    for r in records:
        f = facts(g, r)
        for k in f["keys"]:
            cnt[k] = cnt.get(k, 0) + 1
        if f["sched"]:
            has_s += 1
        for s in r.get("sub") or []:
            if s in g["SUB_LABELS"]:
                subs[s] = subs.get(s, 0) + 1
    out = []
    if has_s >= 2:
        out.append(("now", has_s))
    rest = sorted(cnt.items(), key=lambda kv: (
        FIRST.index(kv[0]) if kv[0] in FIRST else len(FIRST),
        -kv[1], kv[0]))
    for k, c in rest:
        if c == 0 or (c >= n and n > 3):
            continue
        out.append((k, c))
    # the shelves inside this one, where the list holds more than one of them; the
    # Overture kind words then say the same thing twice ("dispensaries"), so they go
    if len([s for s, c in subs.items() if c < n]) >= 2:
        defs = (g.get("TAGS") or {}).get("defs") or {}
        out = [(k, c) for k, c in out if (defs.get(k) or {}).get("family") != "kind"]
        for s, c in sorted(subs.items(), key=lambda kv: -kv[1]):
            if c < n:
                out.append(("s-" + s, c))
    return out


def _doodle_src(prov):
    return "/sites/doodle-chiang-rai/" if prov == "cr" else "/sites/doodle-map/"


def block(g, records, prov, json_url=""):
    """The map and its chips, for the top of a list page."""
    bi, bi_text, att = g["bi"], g["bi_text"], g["att"]
    pinned = sum(1 for r in records if r.get("lat") is not None
                 and (r.get("geoPrecision") or "exact") != "needs-pin")
    if not pinned:
        return ""
    keys = chip_keys(g, records)
    chips = []
    for k, c in keys:
        th, en, gl, note = _label(g, k)
        if gl and "<svg" not in gl:
            gl = _glyph(gl)
        tip = bi_text(*note) if note[0] else ""
        chips.append('<button type="button" class="shc" data-k="%s" aria-pressed="false"%s>%s%s'
                     ' <span class="n">%s</span></button>' % (
                         att(k), (' title="%s"' % att(tip)) if tip else "",
                         (gl + " ") if gl else "", bi(th, en),
                         "" if k == "now" else "%d" % c))
    cc = {}
    for r in records:
        c0 = (r.get("cat") or [""])[0]
        cc[c0] = cc.get(c0, 0) + 1
    cat = max(cc, key=cc.get) if cc else ""
    title = bi_text("แผนที่วาดมือของรายการนี้", "a hand-drawn map of this list")
    src = _doodle_src(prov) + "?embed=1&shelf=1"
    return (
        '<section class="shmap" data-prov="%s" data-cat="%s" data-json="%s" data-n="%d" aria-label="%s">'
        '<div class="shframe"><iframe src="%s" allow="geolocation" title="%s"></iframe></div>'
        '%s<p class="shsay" aria-live="polite"></p></section>'
        '<script src="/shelf.js?v=%s" defer></script>' % (
            prov, att(cat), att(json_url), len(records), att(title), att(src), att(title),
            ('<div class="shchips" role="group" aria-label="%s">%s'
             '<button type="button" class="shc shx" data-k="" hidden>%s</button></div>' % (
                 att(bi_text("แสดงเฉพาะ", "Show only")), "".join(chips), bi("ล้าง", "Clear")))
            if chips else "",
            version()))


def json_doc(g, records, href_of):
    """The whole list for the map and the chips: {k: chip keys, r: rows}.

    A row: [lat, lng, th, en, href, cat, photo, hours, [chip indexes], sched, kind, area].
    """
    keys = [k for k, _ in chip_keys(g, records)]
    idx = {k: i for i, k in enumerate(keys)}
    rows = []
    for r in records:
        f = facts(g, r)
        th, en = g["name_pair"](r)
        if not th and not en:
            th = g["name_text"](r)
        ok = r.get("lat") is not None and (r.get("geoPrecision") or "exact") != "needs-pin"
        ph = ""
        try:
            import commons_layer
            pp = commons_layer.place_picture(r["id"])
            if pp and pp.get("src"):
                ph = "/" + pp["src"]
        except Exception:                      # noqa: BLE001
            ph = ""
        fl = [idx[k] for k in f["keys"] if k in idx]
        for s in r.get("sub") or []:
            if "s-" + s in idx:
                fl.append(idx["s-" + s])
        rows.append([round(r["lat"], 5) if ok else None, round(r["lng"], 5) if ok else None,
                     th or "", en or "", href_of(r), (r.get("cat") or [""])[0], ph,
                     _short_hours(r.get("hours")), fl, f["sched"] or 0,
                     list(f["kind"]) if f["kind"] else 0, f["area"] or 0])
    return {"k": keys, "r": rows}


def write_json(g, path, records):
    """docs/<page>.map.json beside a list page; returns its root-absolute url."""
    href_of = lambda r: "/%s/p/%s.html" % (r.get("province") or "cm", g["place_slug"](r))
    rel = re.sub(r"\.html$", "", path) + ".map.json"
    out = g["DOCS"] / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(json_doc(g, records, href_of), ensure_ascii=False, separators=(",", ":")))
    return "/" + rel


_V = None


def version():
    global _V
    if _V is None:
        import zlib
        _V = "%08x" % (zlib.crc32((JS + CSS).encode("utf-8")) & 0xFFFFFFFF)
    return _V


def emit(docs):
    (docs / "shelf.js").write_text(JS)


CSS = r"""
/* ---- shelfmap_layer: the doodle map at the head of a list, and its chips ---- */
.shmap{margin:.4rem 0 1rem}
.shframe{position:relative;height:min(62vh,540px);min-height:320px;border:2px solid var(--ink,#2a1e16);
  border-radius:14px 10px 16px 12px;overflow:hidden;background:#f5ecd7;box-shadow:3px 3px 0 rgba(43,33,24,.18)}
.shframe iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:block}
.shmap.tool .shframe iframe{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;z-index:2147483000}
html.shtool,html.shtool body{overflow:hidden;overscroll-behavior:none}
.shchips{display:flex;flex-wrap:wrap;gap:6px;margin:.6rem 0 .2rem}
.shc{font:inherit;font-size:.9rem;min-height:40px;padding:4px 12px;border:1.5px solid #b9a888;
  border-radius:14px 9px 13px 10px;background:#fffaf0;color:#2b2118;cursor:pointer;display:inline-flex;align-items:center;gap:4px}
.shc .n{font-size:.8em;color:#6d5d4b}
.shc svg{width:16px;height:16px;flex:none}
.shc[aria-pressed=true]{background:#2b2118;border-color:#2b2118;color:#fffaf0;font-weight:700}
.shc[aria-pressed=true] .n{color:#f5ecd7}
.shc[aria-pressed=true] svg{color:#fffaf0}
.shc.more{border-style:dashed}
.shchips.fold .shc.late{display:none}
.shsay{margin:.2rem 0 .4rem;min-height:1.3em;font-size:.92rem;color:#5c4d38}
.shmap.tool .shchips{position:fixed;z-index:2147483001;left:64px;right:12px;top:12px;flex-wrap:nowrap;overflow-x:auto;
  margin:0;padding:2px 0;scrollbar-width:none}
.shmap.tool .shchips .shc{flex:none;box-shadow:2px 2px 0 rgba(43,33,24,.22)}
@media (min-width:700px){.shmap.tool .shchips{right:280px}}
ul.dir li[hidden]{display:none!important}
.rpv{flex:1 1 100%;display:block;box-sizing:border-box;max-width:100%;padding-left:52px;margin-top:-.1rem;font-size:.84rem;line-height:1.6;color:#5c4d38}
ul.dir li:not(:has(>a.mdth)) .rpv{padding-left:0}
.rpv>*{display:inline-block;margin-right:.35em;white-space:nowrap}
.rpv>*+*::before{content:"· ";color:#b9a888}
.rpv .rpk{color:#2b2118}
.rph.on{color:#0b6b3a;font-weight:600}.rph.off{color:#9A3412}
.rpt,.rpl{color:inherit;text-decoration:none;border-bottom:1px solid #d8c9a8}
.rpt svg,.rpl svg{vertical-align:-2px;margin-right:2px}
ul.dir.shfound{margin-top:.3rem}
"""


JS = r"""/* shelf.js — the doodle map at the head of a list, and the chips that switch its pins
   (shelfmap_layer.py, Nan 2026-10-12). The page hands the map its places (md-shelf); a chip
   narrows the pins and the rows together; two chips mean both. The address keeps the chips
   (#f=morning,delivery), so a narrowed list is a link. */
(function () {
'use strict';
var d = document, sec = d.querySelector('section.shmap'); if (!sec || sec.dataset.on) return; sec.dataset.on = 1;
var fr = sec.querySelector('iframe'), say = sec.querySelector('.shsay'), box = sec.querySelector('.shchips');
var html = d.documentElement, list = d.querySelector('ul.dir[data-sortable]');
var LANG = function () { return html.classList.contains('lang-en') ? 'en' : html.classList.contains('lang-th') ? 'th' : (/^th/i.test(navigator.language || '') ? 'th' : 'en'); };
function t(th, en) { return LANG() === 'en' ? en : th; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
function bi(th, en) { th = th || en || ''; if (!en || en === th) return '<span class="th" lang="th">' + esc(th) + '</span>';
  return '<span class="bi"><span class="th" lang="th">' + esc(th) + '</span><span class="en" lang="en"><span class="th" lang="th"> · </span>' + esc(en) + '</span></span>'; }

/* ---- the week, as minutes from Monday 00:00 in Bangkok ---- */
function bkk() { var b = new Date(Date.now() + 7 * 3600e3); return ((b.getUTCDay() + 6) % 7) * 1440 + b.getUTCHours() * 60 + b.getUTCMinutes(); }
function hh(m) { m = ((m % 1440) + 1440) % 1440; return ('0' + Math.floor(m / 60)).slice(-2) + ':' + ('0' + m % 60).slice(-2); }
function parseS(s) { if (!s) return null; if (typeof s !== 'string') return s; return s.split(',').map(function (x) { var p = x.split('-'); return [+p[0], +p[1]]; }); }
function openNow(iv) { if (!iv) return false; var m = bkk(); for (var i = 0; i < iv.length; i++) { var a = iv[i][0], b = iv[i][1]; if ((m >= a && m < b) || (m + 10080 >= a && m + 10080 < b)) return true; } return false; }
var DAYS = [['จ.', 'Mon'], ['อ.', 'Tue'], ['พ.', 'Wed'], ['พฤ.', 'Thu'], ['ศ.', 'Fri'], ['ส.', 'Sat'], ['อา.', 'Sun']];
function words(iv) {
  if (!iv || !iv.length) return null;
  var m = bkk(), W = 10080;
  for (var i = 0; i < iv.length; i++) { var a = iv[i][0], b = iv[i][1];
    if ((m >= a && m < b) || (m + W >= a && m + W < b)) { if (b - a >= W) return [1, t('เปิด 24 ชม.', 'open 24 h')]; return [1, t('เปิดอยู่ ถึง ' + hh(b), 'open · closes ' + hh(b))]; } }
  var best = null; iv.forEach(function (x) { var ah = ((x[0] - m) % W + W) % W; if (best === null || ah < best[0]) best = [ah, x[0] % W]; });
  var day = Math.floor(best[1] / 1440), today = Math.floor(m / 1440);
  var w = day === today && best[0] < 1440 ? ['', ''] : day === (today + 1) % 7 ? ['พรุ่งนี้ ', 'tomorrow '] : [DAYS[day][0] + ' ', DAYS[day][1] + ' '];
  return [0, t('ปิดอยู่ เปิด ' + w[0] + hh(best[1]), 'closed · opens ' + w[1] + hh(best[1]))];
}
function hoursWords(root) {
  [].forEach.call((root || d).querySelectorAll('.rph[data-s]'), function (el) {
    var w = words(parseS(el.dataset.s)); if (!w) return;
    if (!el.dataset.raw) el.dataset.raw = el.textContent;
    el.textContent = w[1]; el.className = 'rph ' + (w[0] ? 'on' : 'off'); if (el.dataset.raw) el.title = el.dataset.raw;
  });
}

/* ---- the places: this page's rows, or the whole list when it runs to more pages ---- */
var ROWS = [], KEYS = [], whole = false;
function fromDom() {
  KEYS = [].map.call(box ? box.querySelectorAll('.shc[data-k]:not(.shx)') : [], function (b) { return b.dataset.k; });
  var ix = {}; KEYS.forEach(function (k, i) { ix[k] = i; });
  ROWS = [].map.call(list ? list.querySelectorAll('li[data-n]') : [], function (li) {
    var a = li.querySelector('a[href]:not(.mdth)') || li.querySelector('a[href]'), f = (li.dataset.f || '').split(' ').filter(Boolean);
    var sub = (li.dataset.sub || '').split(' ').filter(Boolean).map(function (s) { return 's-' + s; });
    var pic = li.querySelector('a.mdth.ph img'), nm = pairOf(li);
    return { li: li, lat: li.dataset.lat ? +li.dataset.lat : null, lng: li.dataset.lng ? +li.dataset.lng : null, th: nm[0], en: nm[1],
      u: a ? a.getAttribute('href') : '', abs: a ? a.href : '', ph: pic ? pic.src : '', hrs: '', c: sec.dataset.cat || '',
      f: f.concat(sub).map(function (k) { return ix[k]; }).filter(function (x) { return x != null; }), s: parseS(li.dataset.s) };
  });
}
function pairOf(li) {
  var th = li.querySelector('a:not(.mdth) .th, a:not(.mdth) [lang=th]'), en = li.querySelector('a:not(.mdth) .en[lang=en], a:not(.mdth) [lang=en]');
  var n = li.dataset.n || '';
  return [th ? th.textContent.trim() : (/[฀-๿]/.test(n) ? n : ''), en ? en.textContent.replace(/^\s*·\s*/, '').trim() : (li.dataset.ne || (!/[฀-๿]/.test(n) ? n : ''))];
}
function fromJson(doc) {
  whole = true; KEYS = doc.k || [];
  ROWS = (doc.r || []).map(function (x) { return { lat: x[0], lng: x[1], th: x[2], en: x[3], u: x[4], abs: x[4], c: x[5], ph: x[6], hrs: x[7], f: x[8] || [], s: x[9] || null, kind: x[10] || null, area: x[11] || '' }; });
}

/* ---- the chips ---- */
var ON = [];
function want() { return ON.map(function (k) { return KEYS.indexOf(k); }); }
function match(r) {
  for (var i = 0; i < ON.length; i++) {
    var k = ON[i];
    if (k === 'now') { if (!openNow(r.s)) return false; continue; }
    if (r.f.indexOf(KEYS.indexOf(k)) < 0) return false;
  }
  return true;
}
function marks() {
  return ROWS.map(function (r, i) { return r.lat == null ? null : { i: i, lat: r.lat, lng: r.lng, th: r.th, en: r.en, u: r.abs || r.u, c: r.c, ph: r.ph, h: r.hrs }; }).filter(Boolean);
}
function shown() { var o = []; ROWS.forEach(function (r, i) { if (r.lat != null && (!ON.length || match(r))) o.push(i); }); return o; }
var READY = false;
function post(type, extra) {
  if (!fr || !fr.contentWindow) return;
  var m = Object.assign({ type: type }, extra || {});
  try { fr.contentWindow.postMessage(m, location.origin); } catch (e) { }
}
function sendAll(fit) { post('md-shelf', { marks: marks(), show: ON.length ? shown() : null, fit: fit !== false, label: [d.title.split(' · ')[0], ''] }); }
function render() {
  var n = 0, all = ROWS.length;
  ROWS.forEach(function (r) { r.ok = !ON.length || match(r); if (r.ok) n++; });
  if (!whole) ROWS.forEach(function (r) { if (r.li) r.li.hidden = !r.ok; });
  else foundList();
  if (box) {
    [].forEach.call(box.querySelectorAll('.shc[data-k]:not(.shx)'), function (b) { b.setAttribute('aria-pressed', String(ON.indexOf(b.dataset.k) >= 0)); });
    var x = box.querySelector('.shx'); if (x) x.hidden = !ON.length;
  }
  if (say) say.textContent = ON.length ? (n.toLocaleString() + t(' จาก ' + all.toLocaleString() + ' แห่ง', ' of ' + all.toLocaleString() + ' places')) +
    (n ? '' : t(' — ไม่มีที่ไหนตรงทุกข้อ ลองเอาบางข้อออก', ' — none has all of these; take one off')) : '';
  try { history.replaceState(history.state, '', location.pathname + location.search + (ON.length ? '#f=' + ON.join(',') : '')); } catch (e) { }
  post('md-shelf-show', { show: ON.length ? shown() : null, fit: true });
}
/* a list on more pages than this one: the matches from all of them, in place of this page's rows */
var FOUND = null;
function foundList() {
  if (!list) return;
  var pagers = d.querySelectorAll('nav.pager');
  if (!ON.length) { if (FOUND) FOUND.hidden = true; list.hidden = false; [].forEach.call(pagers, function (p) { p.hidden = false; }); return; }
  if (!FOUND) { FOUND = d.createElement('ul'); FOUND.className = 'dir shfound'; list.parentNode.insertBefore(FOUND, list); }
  list.hidden = true; [].forEach.call(pagers, function (p) { p.hidden = true; });
  var out = [];
  ROWS.forEach(function (r) {
    if (!r.ok || out.length >= 600) return;
    var bits = [];
    if (r.kind) bits.push('<span class="rpk">' + bi(r.kind[0], r.kind[1]) + '</span>');
    if (r.area) bits.push('<span class="rpa">' + esc(r.area) + '</span>');
    if (r.s || r.hrs) bits.push('<span class="rph"' + (r.s ? ' data-s="' + r.s.map(function (x) { return x[0] + '-' + x[1]; }).join(',') + '"' : '') + '>' + esc(r.hrs || '') + '</span>');
    var pic = r.ph ? '<a class="mdth ph" href="' + esc(r.u) + '" tabindex="-1" aria-hidden="true"><img src="' + esc(r.ph) + '" alt="" loading="lazy" width="44" height="44"></a>' : '';
    out.push('<li data-n="' + esc(r.th || r.en) + '">' + pic + '<a href="' + esc(r.u) + '">' + nameHtml(r) + '</a>' + (bits.length ? '<span class="rpv">' + bits.join(' ') + '</span>' : '') + '</li>');
  });
  FOUND.innerHTML = out.join(''); FOUND.hidden = false; hoursWords(FOUND);
}
/* a sole name shows in every language mode (.solo, as build.name_bi writes it) */
function nameHtml(r) {
  var th = r.th || '', en = r.en || '';
  if (th && en && th !== en) return bi(th, en);
  var one = th || en, thai = /[\u0E00-\u0E7F]/.test(one);
  return '<span class="' + (thai ? 'th' : 'en') + ' solo" lang="' + (thai ? 'th' : 'en') + '">' + esc(one) + '</span>';
}
function toggle(k) {
  if (!k) ON = []; else { var i = ON.indexOf(k); if (i >= 0) ON.splice(i, 1); else ON.push(k); }
  render();
}
if (box) {
  box.addEventListener('click', function (e) { var b = e.target.closest('.shc'); if (!b) return; toggle(b.dataset.k); });
  /* past the first row of chips, the rest wait behind "more" */
  var cs = box.querySelectorAll('.shc[data-k]:not(.shx)');
  if (cs.length > 12) {
    [].forEach.call(cs, function (b, i) { if (i >= 10) b.classList.add('late'); });
    box.classList.add('fold');
    var mb = d.createElement('button'); mb.type = 'button'; mb.className = 'shc more';
    mb.innerHTML = bi('อีก ' + (cs.length - 10), (cs.length - 10) + ' more');
    mb.addEventListener('click', function (e) { e.stopPropagation(); box.classList.remove('fold'); mb.remove(); });
    box.insertBefore(mb, box.querySelector('.shx'));
  }
}

/* ---- the map's whole-screen mode, as on the front page: a touch makes it the tool; ✕, Esc or Back return ---- */
function off() { sec.classList.remove('tool'); html.classList.remove('shtool'); post('md-map', { tool: false }); }
addEventListener('message', function (e) {
  if (e.origin !== location.origin || !fr || e.source !== fr.contentWindow || !e.data) return;
  var m = e.data;
  if (m.type === 'md-shelf-ready') { READY = true; sendAll(true); return; }
  if (m.type !== 'md-map') return;
  if (m.tool) { if (sec.classList.contains('tool')) return; sec.classList.add('tool'); html.classList.add('shtool'); try { history.pushState({ mdshelf: 1 }, ''); } catch (x) { } }
  else if (sec.classList.contains('tool')) { if (history.state && history.state.mdshelf) history.back(); else off(); }
});
addEventListener('popstate', function () { if (sec.classList.contains('tool') && !(history.state && history.state.mdshelf)) off(); });
addEventListener('keydown', function (e) { if (e.key === 'Escape' && sec.classList.contains('tool')) off(); });

function start() {
  var h = /#f=([^&]+)/.exec(location.hash);
  if (h) ON = decodeURIComponent(h[1]).split(',').filter(function (k) { return KEYS.indexOf(k) >= 0; });
  render(); sendAll(true);
  fr && fr.addEventListener('load', function () { sendAll(true); });
}
hoursWords();
addEventListener('mdlang', function () { hoursWords(); if (FOUND && !FOUND.hidden) foundList(); });
setInterval(function () { hoursWords(); if (ON.indexOf('now') >= 0) render(); }, 300e3);
fromDom();
if (sec.dataset.json) {
  fetch(sec.dataset.json).then(function (r) { return r.ok ? r.json() : null; }).then(function (doc) { if (doc) fromJson(doc); start(); }, function () { start(); });
} else start();
})();
"""
