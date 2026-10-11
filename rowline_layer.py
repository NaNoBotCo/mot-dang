#!/usr/bin/env python3
"""rowline_layer.py — the second line of a result, so the list can be read.

WHY THIS EXISTS
---------------
Michael, 2026-09-08 (via Nan): *"Records that appear in search/map/
discoverability functionality should not require you to click them to see
basic information. You should be able to rank/sort results according to tags
and your own matching criteria, without ever leaving the results page. Most of
the details Motdang has could fit on a line or 2, and would cut down on clicks
for human users (good — accessibility!). You need basic information about
links in order to decide (as a human) whether clicking is worth the extra nav
effort."*

WO-69 made a result a card rather than a link: name, reading, metres, an
open-now lamp, three chips and a 📍. What it did not do is let a reader FINISH
on the list. The record behind that row already held, unread on the row:

    every tag it earned      (`t` — capped at ONE chip; 127 slugs exist)
    its trade tags           (`tt` — never shown at all)
    its street AND district  (`st` and `ar` — the row showed whichever came
                              first and dropped the other)
    its opening schedule     (`hk` — spent on a lamp; the hours themselves,
                              which is what a reader plans around, unread)
    its phone                (61,065 records; not in the index at all)
    its own page on the web  (70,730 records, 52,678 of them a Facebook page,
                              which for a Chiang Mai shop is the first-hand
                              source; not in the index at all)

Four of those six cost NOTHING: they are already ints on the index row, and
they were being thrown away at render time. This module spends them.

WHAT IS ON THE LINE, AND IN WHAT ORDER
--------------------------------------
The order is the order a person scans in — what is it, where is it, when is
it open, how do I reach it:

    what   the sub-shelf
    where  the street, and the tambon/amphoe, both when both are held
    what   every tag and trade tag it carries, glyph first, each one a filter
    when   today's hours in words: "เปิดถึง 18:00", "เปิด 09:00", "ปิดวันนี้"
    reach  ☎ the number, as a tel: link · the shop's own page, as a link

Past the fifth chip they fold behind a +N button that opens IN PLACE. A fold
is not a click-through: no navigation, no page load, nothing lost.

WHAT IS DELIBERATELY NOT ON IT
------------------------------
The address. 49,046 records hold one and it is 2.05 MB of index; almost all of
what it says is the street and the district, which are already two chips, and
the rest is a house number nobody scans a list for. The chip does the work at
a fortieth of the weight.

A completeness score. `ครบที่สุด` sorts on one, and that is the right place
for it — a badge reading "3 of 8 fields" on a row invites a reader to grade a
PLACE by what a directory happens to hold about it, which is exactly backwards
(the disk is a subset of what is true). The ☎ and the link are the honest
version of the same signal: they are there when we can act, absent when we
cannot, and they never say the place is lacking.

An open/closed word where no schedule is held. `hk` absent prints NOTHING —
never "closed", never "hours unknown". Silence is the only true reading.

RANKING, WHICH IS THE OTHER HALF OF THE ASK
-------------------------------------------
`MDROW.tagscore(e, want)` counts how many of the reader's active tag terms a
row carries; refine's sort gains ตรงแท็กมากสุด / most tags matched on top of
its ตรงที่สุด · ก-ฮ · ใกล้ที่สุด · ครบที่สุด. It only ever REORDERS — a row
that carries none of them sorts last and is never dropped, because an OR of
two tags is a wider question than either, not a narrower one.

The chips themselves are the other control: every chip on the line is a
filter, so the reader can narrow by any tag they can SEE, which until now was
one tag per row.

ACCESSIBILITY, WHICH IS WHY IT IS A LINE AND NOT AN ICON ROW
------------------------------------------------------------
* The phone is printed as digits, not as a ☎ alone: a glyph with an
  aria-label is a thing a screen reader announces and a sighted reader with
  low vision has to hover to identify. The digits are the information.
* The hours are words, not a coloured dot. The lamp stays — it is instant —
  but a lamp alone cannot say "closes at six", and colour is never the only
  carrier (WCAG 1.4.1).
* +N is a real <button> with aria-expanded, reachable by keyboard, and its
  label says the number it will reveal.
* Everything is in rem and wraps; at 200% text on a 320 px screen the line
  becomes four lines and loses nothing.
* Outbound links carry rel="noopener nofollow" and are marked with their host
  so a reader knows they are leaving before they tap.

WHAT IT COSTS
-------------
Nothing on the four fields already in the index. `ph` (phone digits, 61,065
rows) and `w` (the page, protocol- and facebook.com-stripped, 70,730 rows) are
new index fields and they are measured in notes/rowline-2026-09-08.txt: about
0.85 MB and 1.85 MB raw on an index that the Overture fold has already taken
past its 10 MB budget on its own. That budget line is not mine to move and I
have not moved it — see §6 of the note.
"""

import re


# The JS is APPENDED TO md.js and the CSS folded into style.css rather than
# shipped as their own files: both are read by search.html's row renderer and
# by tap.js's map card, both of which already wait on md.js, and two more
# requests on a satellite connection to deliver 9 KB is a cost with nothing on
# the other side of it.


# ---------------------------------------------------------------- the index
# Two new fields on an index row, and the only two on this line that are not
# already there. Both are written in their SHORTEST true form, because the
# index is fetched whole before a reader sees an answer:
#
#   ph  the phone as digits, nothing else — 61,065 records, ~0.85 MB
#   w   the shop's own page, protocol-stripped, and "f/<slug>" where it is a
#       Facebook page (52,678 of the 70,730 are) — ~1.85 MB
#
# NOT the address: 49,046 records hold one, it is 2.05 MB, and what it says is
# the street and the district, which the row already carries as two chips at a
# fortieth of the weight.


def index_phone(r):
    """The digits of the first number on the record, or None.

    Thai records carry numbers written every way there is — 053-123456,
    +66 81 234 5678, 081 234 5678 / 089 111 2222. The separators are noise in
    an index and the row re-groups them for display, so only digits are kept,
    and a +66 is folded back to the 0 the number is written and spoken with
    here. A second number on a record does not go on a LIST row; it is on the
    place's own page, where there is room to say which is which.
    """
    v = str(r.get("phone") or "").strip()
    if not v:
        return None
    v = re.split(r"[,;/]|\s{2,}", v)[0]
    d = re.sub(r"\D", "", v)
    if d.startswith("0066"):
        d = d[2:]                      # the 00 international prefix
    if d.startswith("660"):
        d = d[2:]                      # +66 (0)91…: the trunk 0 kept after the code
    # 10 as well as 11: after the 66 a landline is 8 digits, a mobile 9.
    elif d.startswith("66") and len(d) >= 10:
        d = "0" + d[2:]
    return d if 8 <= len(d) <= 11 else None


def index_web(r):
    """The place's own page on the web, stripped to what is not boilerplate.

    A Facebook page becomes "f/<slug>" — thirteen bytes of "facebook.com/"
    saved on 52,678 records, and the row puts it back. For a Chiang Mai shop
    that page is very often the FIRST-HAND source (a place's own Facebook page
    IS first-hand, 2026-09-06), which is why it is preferred over a website
    field that is frequently the same URL typed twice.
    """
    al = r.get("attrs") or {}
    for u in (str(al.get("facebook") or "").strip(), str(r.get("website") or "").strip()):
        if not u:
            continue
        u = re.sub(r"^https?://", "", u, flags=re.I)
        u = re.sub(r"^www\.", "", u, flags=re.I)
        u = u.rstrip("/")
        if not u:
            continue
        m = re.match(r"^(?:[a-z-]+\.)?facebook\.com/(.+)$", u, flags=re.I)
        if m:
            return "f/" + m.group(1)
        return u
    return None


CSS = """/* rowline.css — the second line of a result row.

   It is one flowing line that wraps, not a grid: a grid would hold columns
   open for fields most records do not have, and 63,170 of the records folded
   in this week hold a name and a pin and nothing else. What is held prints;
   what is not held takes no space. */
.rline{display:block;margin-top:.12rem;line-height:1.7}
.rline > *{vertical-align:middle}
/* The chips past the fifth. Hidden by attribute, not by a class, so a row
   rendered before rowline.js parses is not briefly a wall of tags. */
.rline .rchip[hidden]{display:none}
.rmore{font-size:.78rem;line-height:1.5;border:1px dashed var(--warm-border);border-radius:999px;
padding:0 .55rem;margin:.1rem .15rem 0 0;color:var(--mute);background:transparent;cursor:pointer;
min-height:1.6rem;white-space:nowrap}
.rmore:hover,.rmore:focus{border-color:var(--ant);color:var(--ink)}
.rmore[aria-expanded="true"]{border-style:solid}
/* When it is open, and until when. Not a colour on its own — the words carry
   it, and the colour only doubles them. */
.rwhen{font-size:.82rem;color:var(--ink);white-space:nowrap;margin-right:.5rem}
.rwhen.shut{color:#9A3412}
/* Reach. The number is the label; the glyph is decoration and is hidden from
   the accessibility tree, because "telephone 081 234 5678" read twice is
   worse than once. */
.rtel,.rweb{font-size:.82rem;text-decoration:none;white-space:nowrap;margin-right:.5rem;
border-bottom:1px solid var(--warm-border)}
.rtel:hover,.rweb:hover,.rtel:focus,.rweb:focus{border-bottom-color:var(--ant)}
.rtel{font-variant-numeric:tabular-nums}
.rweb .rhost{color:var(--mute)}
@media (max-width:30rem){
/* On a phone the reach moves to its own line so the tap targets do not sit
   shoulder to shoulder with the chips (WCAG 2.5.8). */
.rline .rreach{display:block;margin-top:.15rem}
.rtel,.rweb{display:inline-block;min-height:1.9rem;line-height:1.9rem}
}
@media print{.rmore{display:none}.rline .rchip[hidden]{display:inline-block}}
"""

JS = r"""
/* ---- MDROW — the second line of a result (rowline_layer.py) -------------
   Self-contained on purpose. md.js calls it while rendering a result row and
   tap.js calls it while drawing a map card; neither can be relied on to have
   loaded the other's helpers first, so this brings its own escaping, its own
   bilingual join (the exact markup mdBi writes, or both languages show at
   once) and reads a schedule through window.MDHOURS when it is there. */
(function(){
'use strict';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
/* The markup twin of md.js's mdBi. Kept identical rather than imported: a
   chip written any other way jams the two languages together in both-mode. */
function bi(th,en){th=th==null?'':th;
  if(!en||en===th)return '<span class="th" lang="th">'+esc(th)+'</span>';
  return '<span class="bi"><span class="th" lang="th">'+esc(th)+'</span>'+
    '<span class="en" lang="en"><span class="th" lang="th"> · </span>'+esc(en)+'</span></span>';}
function href(root,qs){return esc(root)+'search.html?'+qs;}
function chip(root,qs,label,extra){
  return '<a class="rchip'+(extra?' '+extra:'')+'" href="'+href(root,qs)+'">'+label+'</a>';}

/* ---- what it is, where it is, what else it is -------------------------
   Every one of these is a filter the reader can tap, which is the whole of
   "discovery should EXPLICITLY allow finding by tags": you cannot filter by a
   tag you were never shown. The cap that used to sit here — three chips, one
   of them a tag — meant a record carrying nine tags advertised one. */
function chipsOf(e,T,root){
  var out=[],i,su,s,a,t;
  T=T||{};
  su=(e.su||[])[0];
  if(su&&T.subs&&T.subs[su])out.push(chip(root,'sub='+encodeURIComponent(su),bi(T.subs[su][0],T.subs[su][1])));
  /* BOTH, not whichever came first. A street tells you the block and a
     district tells you the side of town; a reader deciding whether to cross
     the river needs the second even when we have the first. */
  if(e.st!=null&&T.streets&&T.streets[e.st]){s=T.streets[e.st];
    out.push(chip(root,'st='+encodeURIComponent(s[0]),bi(s[1]||s[2],s[2]||s[1])));}
  if(e.ar!=null&&T.areas&&T.areas[e.ar]){a=T.areas[e.ar];
    var an=a[0]||a[1];if(an)out.push(chip(root,'ar='+encodeURIComponent(an),bi(an,a[3]||'')));}
  /* open-<day> is left off: the lamp and the hours line already say it. */
  for(i=0;i<((e.t&&e.t.length)||0);i++){t=T.tags&&T.tags[e.t[i]];if(!t)continue;
    if(/^open-(mon|tues|wednes|thurs|fri|satur|sun)day$/.test(t[0]||''))continue;
    out.push(chip(root,'tag='+encodeURIComponent(t[0]),(t[3]?esc(t[3])+' ':'')+bi(t[1],t[2])));}
  for(i=0;i<((e.tt&&e.tt.length)||0);i++){t=T.trade&&T.trade[e.tt[i]];if(!t)continue;
    out.push(chip(root,'tag='+encodeURIComponent(t[0]),bi(t[0],t[1]||'')));}
  return out;}

/* ---- when, in words --------------------------------------------------
   The lamp says whether to go now. This says whether to go after lunch, and
   that is the question a list is scanned with. Read off `hk`, the schedule
   already on the row; a row without one prints NOTHING — not "closed", not
   "hours unknown". Nobody has said, so we do not either. */
var DAY=1440,WEEK=10080;
function hhmm(m){m=((m%DAY)+DAY)%DAY;var h=Math.floor(m/60),n=m%60;
  return (h<10?'0':'')+h+':'+(n<10?'0':'')+n;}
function wmin(){if(window.MDHOURS&&window.MDHOURS.now)return window.MDHOURS.now();
  if(window.MDHOURS&&window.MDHOURS.wmin)return window.MDHOURS.wmin();return null;}
function whenText(sch,w){
  if(!sch||!sch.length||w==null)return null;
  var d0=Math.floor(w/DAY)*DAY,i,iv,open=null,next=null;
  for(i=0;i<sch.length;i++){iv=sch[i];
    if(w>=iv[0]&&w<iv[1]){open=iv;break;}}
  if(open)return {shut:false,html:bi('เปิดถึง '+hhmm(open[1]),'open until '+hhmm(open[1]))};
  /* Not open. The next opening TODAY is news a reader can act on; one three
     days out is the opening times, and those are on the place's own page. */
  for(i=0;i<sch.length;i++){iv=sch[i];
    if(iv[0]>=w&&iv[0]<d0+DAY&&(next===null||iv[0]<next))next=iv[0];}
  if(next!==null)return {shut:true,html:bi('เปิด '+hhmm(next),'opens '+hhmm(next))};
  return {shut:true,html:bi('ปิดแล้ววันนี้','closed for today')};}

/* ---- reach -----------------------------------------------------------
   A Thai number is dialled as it is written. It is printed in its own groups
   and dialled from the digits, so a tap works and a reader can also just read
   it off the screen to somebody else, which is what actually happens. */
function telText(d){d=String(d||'').replace(/\D/g,'');
  if(!d)return null;
  if(d.length===10&&d.charAt(0)==='0')return d.slice(0,3)+'-'+d.slice(3,6)+'-'+d.slice(6);
  if(d.length===9&&d.charAt(0)==='0')return d.slice(0,3)+'-'+d.slice(3,6)+'-'+d.slice(6);
  return d;}
function telHref(d){d=String(d||'').replace(/\D/g,'');
  return d.charAt(0)==='0'?'+66'+d.slice(1):d;}
/* `w` is stored stripped: "f/<slug>" is a Facebook page, anything else is a
   host and path. The host is SHOWN — a reader is about to leave the site and
   is entitled to know where to. */
function webOf(u){if(!u)return null;u=String(u);
  /* No glyph on a Facebook link: the host IS the word, and "f facebook" said
     the same thing twice on 52,678 rows. */
  if(u.slice(0,2)==='f/')return {href:'https://www.facebook.com/'+u.slice(2),host:'facebook',glyph:''};
  return {href:'https://'+u,host:u.split('/')[0].replace(/^www\./,''),glyph:'🌐'};}

/* ---- the line --------------------------------------------------------
   TOP is 5 because five chips is about what the eye takes without counting,
   and because the fifth is where a food row stops saying what it is and
   starts saying what else it is. The rest fold; nothing is dropped. */
var TOP=5;
function line(e,T,o){
  o=o||{};
  var root=o.root||'',out='',i,ch=chipsOf(e,T,root),hid=0;
  if(ch.length){
    out+='<span class="rchips">';
    for(i=0;i<ch.length;i++){
      if(i<TOP)out+=ch[i]+' ';
      else{hid++;out+=ch[i].replace('<a class="rchip','<a hidden class="rchip')+' ';}}
    if(hid)out+='<button type="button" class="rmore" aria-expanded="false" '+
      'aria-label="'+esc('อีก '+hid+' · '+hid+' more')+'">+'+hid+'</button>';
    out+='</span>';}
  var sch=(e.hk!=null&&T&&T.hours)?T.hours[e.hk]:null;
  var wt=whenText(sch,wmin());
  var reach='';
  if(e.ph){var tt=telText(e.ph);
    if(tt)reach+='<a class="rtel" href="tel:'+esc(telHref(e.ph))+'">'+
      '<span aria-hidden="true">☎ </span>'+esc(tt)+'</a>';}
  var wb=webOf(e.w);
  if(wb)reach+='<a class="rweb" href="'+esc(wb.href)+'" rel="noopener nofollow" target="_blank">'+
    (wb.glyph?'<span aria-hidden="true">'+esc(wb.glyph)+' </span>':'')+
    '<span class="rhost">'+esc(wb.host)+'</span></a>';
  if(wt||reach){out+='<span class="rreach">';
    if(wt)out+='<span class="rwhen'+(wt.shut?' shut':'')+'">'+wt.html+'</span>';
    out+=reach+'</span>';}
  out=out?'<span class="rline">'+out+'</span>':'';
  /* Written at run time, so glyphs.sweep_html never sees it: md.js's
     mdGlyphs draws the tag marks, the ☎ and the 🌐. A bare name, not
     window.*: md.js is one classic script. Twice over is harmless. */
  return typeof mdGlyphs==='function'?mdGlyphs(out):out;}

/* ---- ranking by tag ---------------------------------------------------
   How many of the terms the reader is actually asking about this row
   carries. Used as a SORT and never as a filter: a row scoring nought sorts
   last and is never removed, because an OR of two tags is a wider question
   than either of them, not a narrower one, and because a row that has never
   been tagged is untagged, not disqualified. */
function tagscore(e,want,T){
  if(!want||!want.length)return 0;
  var have={},i,t;T=T||{};
  for(i=0;i<((e.t&&e.t.length)||0);i++){t=T.tags&&T.tags[e.t[i]];if(t)have[t[0]]=1;}
  for(i=0;i<((e.tt&&e.tt.length)||0);i++){t=T.trade&&T.trade[e.tt[i]];if(t)have[t[0]]=1;}
  for(i=0;i<((e.su&&e.su.length)||0);i++)have[e.su[i]]=1;
  var n=0;for(i=0;i<want.length;i++)if(have[want[i]])n++;
  return n;}

/* The fold, delegated from the document so a row drawn at any later moment —
   a second search, a filter applied in place — is covered without rebinding.
   Capture is off; md.js's own row handler already steps aside for a button. */
function bindFold(){
  document.addEventListener('click',function(ev){
    var b=ev.target&&ev.target.closest&&ev.target.closest('.rmore');
    if(!b)return;
    ev.preventDefault();ev.stopPropagation();
    var wrap=b.parentNode,open=b.getAttribute('aria-expanded')==='true',
        chips=wrap.querySelectorAll('.rchip'),i,n=0;
    for(i=0;i<chips.length;i++){if(i<TOP)continue;chips[i].hidden=open;n++;}
    b.setAttribute('aria-expanded',open?'false':'true');
    /* The label changes with the state, and so does what it is ANNOUNCED as:
       a button reading "−" whose aria-label still says "10 more" tells a
       screen-reader user the opposite of what the page is doing. */
    b.setAttribute('aria-label',open?('อีก '+n+' · '+n+' more'):'ย่อ · fewer');
    b.textContent=open?('+'+n):'\u2212';});}
if(typeof document!=='undefined'&&document.addEventListener)bindFold();

window.MDROW={line:line,chips:chipsOf,when:whenText,tagscore:tagscore,
  tel:telText,telHref:telHref,web:webOf,TOP:TOP,_bi:bi};
})();
"""
