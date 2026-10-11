#!/usr/bin/env python3
"""rowline.js — the second line of a result, run against a DOM stub.

It asserts what a reader GETS from the list without clicking, and it asserts
the calls made on 2026-09-08 so a later session cannot quietly undo them:

  * every tag a row carries is on the row and every one of them is a filter —
    not one tag, which is what the WO-69 cap allowed;
  * the street AND the district, when both are held;
  * past the fifth chip a +N button that opens IN PLACE — a real button, with
    aria-expanded, and nothing dropped;
  * today's hours in WORDS ("เปิดถึง 18:00"), because a lamp cannot say when;
  * a row with NO schedule prints nothing at all — never "closed", never
    "hours unknown";
  * the phone as digits a reader can read aloud and a tel: link that dials,
    +66 form in the href and the local form on the screen;
  * an outbound link that names its host before the reader taps it;
  * a row holding none of these renders NO line rather than an empty bar —
    63,170 of the records folded in this week are a name and a pin;
  * tagscore only ever REORDERS: a row carrying none of the asked-for tags
    scores nought and is never removed.

    python3 tests/test_rowline.py            (no build needed)
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import rowline_layer  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else "  — " + detail))
    if not ok:
        FAIL.append(name)


# --------------------------------------------------------------- the stub
# Not jsdom. `line()` is a pure string function and only the fold touches the
# document, so the stub knows exactly what rowline.js reaches for — and tells
# us the day it reaches for something else.
HARNESS = r"""'use strict';
const NOW_WMIN = 0*1440 + 14*60 + 30;          /* Monday 14:30, Chiang Mai */
const _docHandlers = {};
global.document = {
  addEventListener(t, fn){ (_docHandlers[t] = _docHandlers[t] || []).push(fn); },
};
global.window = { MDHOURS: { now: () => NOW_WMIN, wmin: () => NOW_WMIN } };
__ROWLINE__
const MDROW = window.MDROW;

/* ---- the tables, in the shape build.py's search_tables() writes them ---- */
const T = {
  tags: [["vegan","เจ","vegan","🌱"], ["wifi","ไวไฟ","wifi",""],
         ["late","เปิดดึก","open late",""], ["halal","ฮาลาล","halal",""],
         ["parking","ที่จอดรถ","parking",""], ["aircon","แอร์","air-con",""],
         ["cash","เงินสด","cash only",""]],
  trade: [["ซ่อมแอร์","air-con repair","som air"], ["ถ่ายเอกสาร","photocopying",""]],
  streets: [["chang-moi","ถนนช้างม่อย","Chang Moi Road"]],
  areas: [["ช้างม่อย","เมืองเชียงใหม่","cm","Chang Moi"]],
  subs: {noodles: ["ก๋วยเตี๋ยว","noodles"]},
  /* Mon 09:00-18:00 and Mon 20:00-23:00, in week-minutes */
  hours: [[[540, 1080], [1200, 1380]], [[0, 10080]]],
};
const rich = {id:"r1", n:"ร้านเจ๊หมวย", su:["noodles"], st:0, ar:0, hk:0,
              t:[0,1,2,3,4,5,6], tt:[0], ph:"0812345678", w:"f/jaemuay"};
const bare = {id:"r2", n:"ที่ไหนสักแห่ง"};
const shut = {id:"r3", n:"ปิดอยู่", hk:0, t:[0]};

const out = {};
out.rich   = MDROW.line(rich, T, {root:"/"});
out.bare   = MDROW.line(bare, T, {root:"/"});
out.noSch  = MDROW.line({id:"r4", n:"x", t:[0], ph:"053123456"}, T, {root:"/"});
out.chips  = MDROW.chips(rich, T, "/").length;
out.tel    = MDROW.tel("0812345678");
out.telHref= MDROW.telHref("0812345678");
out.tel9   = MDROW.tel("053123456");
out.web    = MDROW.web("f/jaemuay");
out.webOther = MDROW.web("cmnoodles.co.th/menu");
out.score0 = MDROW.tagscore(bare, ["vegan","halal"], T);
out.score2 = MDROW.tagscore(rich, ["vegan","halal"], T);
out.scoreNone = MDROW.tagscore(rich, [], T);
out.whenOpen = MDROW.when(T.hours[0], 0*1440 + 14*60 + 30);
out.whenBefore = MDROW.when(T.hours[0], 0*1440 + 8*60);
out.whenGap  = MDROW.when(T.hours[0], 0*1440 + 19*60);
out.whenAfter = MDROW.when(T.hours[0], 0*1440 + 23*60 + 30);
out.whenNone = MDROW.when(null, 100);
out.foldBound = !!(_docHandlers.click && _docHandlers.click.length);
/* The fold, driven through the delegated handler the module actually binds. */
(function(){
  var chips=[],i;
  for(i=0;i<11;i++)chips.push({hidden:i>=MDROW.TOP, tagName:'A'});
  var btn={tagName:'BUTTON', _a:{'aria-expanded':'false'}, textContent:'+6',
    getAttribute:function(k){return this._a[k]===undefined?null:this._a[k];},
    setAttribute:function(k,v){this._a[k]=String(v);}};
  btn.parentNode={querySelectorAll:function(){return chips;}};
  var ev={target:{closest:function(sel){return sel==='.rmore'?btn:null;}},
          preventDefault:function(){}, stopPropagation:function(){}};
  var vis=function(){var n=0;for(var j=0;j<chips.length;j++)if(!chips[j].hidden)n++;return n;};
  _docHandlers.click[0](ev);
  var opened=vis(), openAria=btn.getAttribute('aria-label'), openLabel=btn.textContent;
  _docHandlers.click[0](ev);
  out.fold={opened:opened, closed:vis(), openAria:openAria, openLabel:openLabel,
            closedLabel:btn.textContent, expanded:btn.getAttribute('aria-expanded')};
})();
out.TOP = MDROW.TOP;
console.log(JSON.stringify(out));
"""


def run_js():
    src = HARNESS.replace("__ROWLINE__", rowline_layer.JS)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        p = subprocess.run(["node", path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    if p.returncode != 0:
        print(p.stderr.strip()[:2000])
        sys.exit("node refused the file")
    return json.loads(p.stdout.strip().splitlines()[-1])


def main():
    if subprocess.run(["which", "node"], capture_output=True).returncode != 0:
        print("node not found — skipping (the module still imports)")
        return 0
    o = run_js()
    rich, bare = o["rich"], o["bare"]

    print("\nEVERY TAG, AND EVERY ONE OF THEM A FILTER")
    # sub + street + district + seven tags + one trade tag = eleven
    check("all eleven relations become chips, not three", o["chips"] == 11, f"got {o['chips']}")
    for slug in ("vegan", "wifi", "late", "halal", "parking", "aircon", "cash"):
        check(f"tag {slug} is on the row and filters",
              f"tag={slug}" in rich, "missing")
    check("the trade tag is on the row too (WO-69 never showed one)",
          "tag=%E0%B8%8B" in rich or "tag=" + "ซ่อมแอร์" in rich, "no trade chip")

    print("\nWHERE — BOTH, NOT WHICHEVER CAME FIRST")
    check("the street is a chip", "st=chang-moi" in rich, "no street chip")
    check("the district is a chip beside it", "ar=" in rich, "no district chip")
    check("what it is comes first", rich.index("sub=noodles") < rich.index("st=chang-moi"),
          "sub not first")

    print("\nTHE FOLD — IN PLACE, NOTHING DROPPED")
    check("five chips show", rich.count('<a class="rchip"') == rowline_layer_top(o),
          f"{rich.count(chr(60)+'a class=' + chr(34) + 'rchip' + chr(34))} shown")
    check("the rest are hidden, not removed", rich.count("<a hidden") == 11 - o["TOP"],
          f"{rich.count('<a hidden')} hidden")
    check("+N is a real button with aria-expanded",
          '<button type="button" class="rmore" aria-expanded="false"' in rich, "not a button")
    check("+N says how many it will reveal", ">+6</button>" in rich, "wrong count")
    check("the fold is bound from the document, so later rows are covered",
          o["foldBound"], "no delegated handler")
    check("once open the button is announced as collapse, not as '6 more'",
          o["fold"]["openAria"] == "ย่อ · fewer" and o["fold"]["openLabel"] == "\u2212",
          json.dumps(o["fold"], ensure_ascii=False))
    check("the fold opens and closes in place, nothing navigates",
          o["fold"]["opened"] == 11 and o["fold"]["closed"] == rowline_layer_top(o),
          json.dumps(o["fold"], ensure_ascii=False))

    print("\nWHEN — IN WORDS, AND SILENT WHEN NOBODY SAID")
    check("open now says until when", o["whenOpen"]["html"].find("เปิดถึง 18:00") >= 0,
          json.dumps(o["whenOpen"], ensure_ascii=False))
    check("before opening says when it opens", "เปิด 09:00" in o["whenBefore"]["html"],
          json.dumps(o["whenBefore"], ensure_ascii=False))
    check("in the afternoon gap it names the evening session",
          "เปิด 20:00" in o["whenGap"]["html"], json.dumps(o["whenGap"], ensure_ascii=False))
    check("after the last session it says closed FOR TODAY, not closed",
          "วันนี้" in o["whenAfter"]["html"], json.dumps(o["whenAfter"], ensure_ascii=False))
    check("NO SCHEDULE PRINTS NOTHING — never 'closed'", o["whenNone"] is None,
          json.dumps(o["whenNone"], ensure_ascii=False))
    check("a row with no schedule carries no when-text at all",
          "rwhen" not in o["noSch"], o["noSch"][:120])

    print("\nREACH — READABLE, DIALLABLE, AND HONEST ABOUT LEAVING")
    check("the number is printed in its own groups", o["tel"] == "081-234-5678", o["tel"])
    check("a 9-digit landline groups as one", o["tel9"] == "053-123-456", o["tel9"])
    check("the href dials in international form", o["telHref"] == "+66812345678", o["telHref"])
    ip = rowline_layer.index_phone
    check("+66 on an 8-digit landline folds to 0 (053-123-456 on the row)",
          ip({"phone": "+66 53 123 456"}) == "053123456", str(ip({"phone": "+66 53 123 456"})))
    check("+66 on a mobile folds to 0", ip({"phone": "+66 81 234 5678"}) == "0812345678",
          str(ip({"phone": "+66 81 234 5678"})))
    # 36 records keep the trunk 0 after the country code; they indexed as 009…
    for raw in ("+66 091 067 1983", "+66(0)91 067 1983", "0066 091 067 1983"):
        check("%s folds to 091-067-1983's digits" % raw,
              ip({"phone": raw}) == "0910671983", str(ip({"phone": raw})))
    check("the digits are the label, the glyph is decoration",
          'aria-hidden="true">☎ </span>081-234-5678' in rich, "glyph not hidden from AT")
    check("a facebook page resolves to facebook.com",
          o["web"]["href"] == "https://www.facebook.com/jaemuay", json.dumps(o["web"]))
    check("any other page keeps its own host", o["webOther"]["host"] == "cmnoodles.co.th",
          json.dumps(o["webOther"]))
    check("the host is shown before the reader taps", '<span class="rhost">facebook' in rich,
          "host not shown")
    check("outbound links are noopener nofollow", 'rel="noopener nofollow"' in rich, "no rel")

    print("\nA BARE RECORD GETS A BARE ROW")
    check("a name-and-a-pin record renders NO line, not an empty bar", bare == "", repr(bare))

    print("\nRANKING BY TAG ONLY EVER REORDERS")
    check("a row carrying none of them scores nought", o["score0"] == 0, str(o["score0"]))
    check("a row carrying both scores two", o["score2"] == 2, str(o["score2"]))
    check("nothing asked for scores nought for everyone", o["scoreNone"] == 0, str(o["scoreNone"]))

    print("\nTHE SHEET")
    css = rowline_layer.CSS
    check("the hidden chips print anyway on paper", "@media print" in css, "no print rule")
    check("nothing is sized in px that a reader scales",
          not re.search(r"font-size:\s*\d+px", css), "px font-size")
    check("the phone-width rule gives the taps their own line",
          ".rreach{display:block" in css.replace("\n", ""), "no small-screen rule")

    print()
    if FAIL:
        print(f"{len(FAIL)} FAILED: " + "; ".join(FAIL))
        return 1
    print("all green")
    return 0


def rowline_layer_top(o):
    return o["TOP"]


if __name__ == "__main__":
    sys.exit(main())
