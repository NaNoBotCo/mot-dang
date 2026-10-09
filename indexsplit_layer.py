#!/usr/bin/env python3
"""indexsplit_layer.py — stop shipping the whole catalogue to answer one question.

WHY THIS EXISTS
---------------
Nan, 2026-09-08: *"1.5 mb before an answer is a problem that needs fixed."*

Measured that morning against the LIVE index, by stripping each field and
re-measuring: 25,582 rows, 1,563,679 bytes gzipped, and no single fat field —
name 17%, keywords 16%, slug 14%, coordinates 17%, id 7%. A reader who types
"ก๋วยเตี๋ยว" sees two hundred rows and has paid for twenty-five thousand.

TWO CHANGES, AND WHAT EACH IS WORTH — measured, not estimated
--------------------------------------------------------------
1. THE CHEAP WINS, 92 KB (6%):
   * coordinates to five decimal places. 17,000 rows ship SEVEN, which is
     1.1 cm, on a directory where thousands of pins are a tambon centroid and
     2,958 rows share a coordinate with another record. Five is 1.1 m.  64 KB
   * `pv` comes off. It is a pure function of `p` — cm -> เชียงใหม่,
     cr -> เชียงราย, zero exceptions in 25,582 rows — and the client can do
     that with a two-entry table.                                        30 KB

2. THE SPLIT, 325 KB (21%): the coordinates and two fields no row renders go
   to data/index2.json, aligned to the first file BY POSITION so they cost no
   keys, and fetched in parallel. The answer is drawn the moment the first
   file lands, complete — see the note on DRAW_FIELDS for why the cut is here
   and not at the 406 KB the obvious cut was worth.

WHAT WAS MEASURED AND REJECTED
------------------------------
* DROPPING `id` (102 KB). Not free, and an earlier draft of this said it was.
  `id` is a join key: events.geojson matches on `placeId`, and the claim flow
  POSTs it to the worker. Replacing it with the array position would silently
  break both.
* MOVING `s` TO THE SECOND FILE (220 KB, the single biggest item left). The
  slug is the row's href. A result that is not yet a link for the first
  half-second is a result you can tap and have nothing happen, which is worse
  than the wait it saves.
* DERIVING `s` from `id` or from a hash stem. Only 1% of slugs have the
  <stem>-<7hex> shape, and only a third of those have a stem the id carries.
  Worth 826 bytes. Measured, so nobody measures it again.

THE HONEST SIZE OF THIS
-----------------------
Today: 1,563,679 -> about 1,238,000 before an answer. After the Overture fold,
which Nan approved and which takes the catalogue to 89,082 rows, it is still
comfortably over four megabytes. **This is a trim, not a fix.** Every client-side move available,
taken together, does not get the folded catalogue back to where the unfolded
one stands today, because the thing being shipped is the catalogue and the
catalogue got bigger. /api/v1/places is deployed, answers in about 120 ms and
has never been called by the search box; that is the fix, and it trades
offline-first for it, which is a decision about what this site is.

NO BUDGET IS SET HERE, AND NONE SHOULD BE
------------------------------------------
The 10 MB ceiling this replaces was a number a session invented on a Sunday
afternoon and every later session inherited. Nan, on being shown its
provenance: *"the 10 mb ceiling is a hallucination that needs nuked."* So this
module measures and reports and does not decide. If a line belongs here it is
hers to draw, and until she draws one there is no line.
"""

# `pv` was a string on every row. It is a function of `p`, and this is the
# whole of that function — emitted into the page rather than hardcoded in the
# JS so a third province is a data change, not a code change.
PROVINCE_WORDS = {"cm": "เชียงใหม่", "cr": "เชียงราย"}

# THE CUT LINE, AND WHY IT IS HERE AND NOT WHERE IT COULD BE.
#
# The obvious cut — every field that only DRAWS a row — is worth 406 KB of
# 1,564 KB. It was built, and then measured in a browser: when the second file
# landed, twenty of twenty-five rows changed height. A list that shifts half a
# second after it draws is a list where a tap lands on the wrong row, and this
# whole piece of work was justified on accessibility. So the cut moved.
#
# What is deferred now is only what CANNOT MOVE ANYTHING: the coordinates
# (whose only mark on a row is the 📍, and .rpin is absolutely positioned, so
# it costs no reflow), and two fields no row renders at all — `f` the facet
# keys, read by the filters, and `fx` the facet set, read by claim.html.
#
# Everything the second line prints — the tags, the street, the district, the
# hours, the phone, the page — stays in the first file and is complete the
# moment the row appears. 325 KB instead of 406 KB, and nothing moves.
DRAW_FIELDS = ("lat", "lng", "f", "fx")

COORD_DP = 5      # 1.1 m. Not a budget — the precision the pins actually have.


def split(rows):
    """(first, second) — the same rows, in two files, aligned by POSITION.

    A row with nothing to draw contributes `0` rather than `{}`: one byte
    instead of two, on the 63,170 records the Overture fold brought in that
    are a name and a pin. The client reads any falsy entry as "nothing here".
    """
    first, second = [], []
    for r in rows:
        head, tail = {}, {}
        for k, v in r.items():
            if k == "pv":
                continue                       # derived from `p` on the client
            if k in DRAW_FIELDS:
                tail[k] = round(v, COORD_DP) if k in ("lat", "lng") else v
            else:
                head[k] = v
        first.append(head)
        second.append(tail or 0)
    return first, second


def report(rows, first, second):
    """What the change is worth, in the bytes a reader actually pays.

    Printed into the build log and asserted by nothing. A number that appears
    in a log is information; the same number in an `if` is a rule nobody
    agreed to.
    """
    import json
    import zlib

    def gz(o):
        return len(zlib.compress(json.dumps(o, ensure_ascii=False).encode(), 6))

    was, now, rest = gz(rows), gz(first), gz(second)
    return (f"  index split: before an answer {now:,} gzipped "
            f"(was {was:,}, −{100 * (was - now) / max(was, 1):.0f}%); "
            f"the rest {rest:,} follows")


def head(root, version):
    """Nothing. The JS rides in md.js beside MDROW; this is here so a caller
    that expects a head() gets one rather than a traceback."""
    return ""


# There is no sheet. An earlier cut of this deferred the whole second line and
# needed a rule to reserve its height; the cut moved instead, and a rule that
# reserves space for something that is never missing is furniture.
CSS = ""

JS = r"""
/* ---- MDIDX — the index arrives in two parts (indexsplit_layer.py) --------
   The first part answers. The second part draws. Nothing here waits on the
   second to show a result, and nothing here treats a field that has not
   ARRIVED as a field the record does not HAVE — an unloaded coordinate read
   as "unpinned" would print a false fact about thousands of places, which is
   the same mistake that made a car park say it had no parking. */
(function(){
'use strict';
var PROV=__PROVINCE_WORDS__;
var full=false, waiting=[];

/* Merge by POSITION. The second file carries no ids and no keys the first
   already has; a row with nothing to draw is the number 0. */
function merge(idx, tail){
  for(var i=0;i<idx.length&&i<tail.length;i++){
    var t=tail[i];
    if(!t)continue;
    for(var k in t)if(Object.prototype.hasOwnProperty.call(t,k))idx[i][k]=t[k];
  }
  full=true;
  for(var j=0;j<waiting.length;j++){try{waiting[j]();}catch(e){}}
  waiting=[];
  repaint();
}

/* The province, which used to be a string on all 25,582 rows. */
function provinces(idx){
  for(var i=0;i<idx.length;i++){var p=PROV[idx[i].p];if(p)idx[i].pv=p;}
}

/* Redraw only what the second file changes: the second line and the 📍. The
   list itself is not re-rendered — the reader's scroll position, any open
   panel and any focus stay exactly where they were. */
function repaint(){
  if(typeof document==='undefined')return;
  var idx=window.MD_IDX;if(!idx)return;
  var by={},i;for(i=0;i<idx.length;i++)by[idx[i].id]=idx[i];
  var cards=document.querySelectorAll('li.rcard[data-id]');
  for(i=0;i<cards.length;i++){
    var card=cards[i],e=by[card.getAttribute('data-id')];
    if(!e)continue;
    if(e.lat!=null){
      card.setAttribute('data-lat',e.lat);card.setAttribute('data-lng',e.lng);
      if(!card.querySelector('.rpin')){
        var b=document.createElement('button');
        b.type='button';b.className='rpin';
        b.setAttribute('aria-label','แผนที่ · map');
        b.innerHTML=typeof mdIcon==='function'?mdIcon('i-pin'):'';
        card.appendChild(b);
      }
    }
    if(window.MDROW){
      var host=card.querySelector('.rline'),
          html=window.MDROW.line(e,window.MD_TAB||{},{root:ROOT()});
      if(!html)continue;
      if(host)host.outerHTML=html;
      else card.insertAdjacentHTML('beforeend',html);
    }
  }
}
function ROOT(){
  return (typeof document!=='undefined'&&document.documentElement.getAttribute('data-root'))||'';
}

/* Called by md.js's loadIndex the moment the first file has parsed. The second
   fetch is not awaited: a slow or failed second file costs the reader the
   detail line, never the answer. */
function fill(idx, root){
  provinces(idx);
  if(typeof fetch!=='function')return idx;
  fetch(root+'data/index2.json')
    .then(function(r){return r.ok?r.json():null;})
    .then(function(t){if(t&&t.length)merge(idx,t);})
    .catch(function(){});
  return idx;
}

/* For code that must not run against a half-filled row — the results map, the
   "three nearest", anything that reads a coordinate across the whole index. */
function whenFull(fn){if(full)fn();else waiting.push(fn);}

window.MDIDX={fill:fill,whenFull:whenFull,repaint:repaint,merge:merge,
  isFull:function(){return full;},PROV:PROV};
})();
"""


def js(indent=0):
    """The JS with the province table baked in."""
    import json
    return JS.replace("__PROVINCE_WORDS__",
                      json.dumps(PROVINCE_WORDS, ensure_ascii=False))
