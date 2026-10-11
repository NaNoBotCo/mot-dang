#!/usr/bin/env python3
"""tap.js — the card any map opens, run against a DOM stub.

It asserts what a reader gets, not what the code contains, and it asserts the
decisions Nan made on 2026-09-07 so that a later session cannot quietly undo
them:

  * a touch on a mark opens the card and names the place;
  * a touch on BARE GROUND opens nothing — silence, her word;
  * a mark the card cannot describe keeps its link instead of swallowing it;
  * hours nobody recorded print NO lamp — never "closed";
  * a tag chip FILTERS the map where the map can filter, says how many are
    left, and says zero out loud rather than showing everything;
  * where the map cannot filter, the chip goes to the same filter on the
    results page, which can;
  * the three nearest MOVE THE CARD, and the reader's own Back button walks
    the trail back and then closes it;
  * the card is a region, not a modal: nothing is trapped, nothing is dimmed,
    every control is a fingertip tall.

    python3 tests/test_tap.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tapcard  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else "  — " + detail))
    if not ok:
        FAIL.append(name)


# --------------------------------------------------------------- the stub
# Deliberately not jsdom: the point is to run the shipped file, and a stub that
# only knows what tap.js actually touches tells us the moment it reaches for
# something new.
HARNESS = r"""'use strict';
const NOW = new Date(2026, 8, 7, 14, 30);      /* Monday 14:30, Chiang Mai */
class FakeDate extends Date {
  constructor(...a){ if(!a.length) super(NOW.getTime()); else super(...a); }
}
Date = FakeDate;

function El(tag, attrs, opts){
  attrs = attrs || {}; opts = opts || {};
  const self = {
    tagName: tag, className: attrs.class || '', _html: '', hidden: false,
    style: {}, children: [], _attrs: attrs, _handlers: {}, _focused: 0,
    _rect: opts.rect || {left:0, top:0, width:0, height:0},
    getAttribute(k){ return k === 'class' ? self.className
                     : (self._attrs[k] === undefined ? null : String(self._attrs[k])); },
    setAttribute(k, v){ if(k === 'class') self.className = String(v);
                        else self._attrs[k] = String(v); },
    removeAttribute(k){ delete self._attrs[k]; },
    appendChild(c){ self.children.push(c); return c; },
    addEventListener(t, fn){ (self._handlers[t] = self._handlers[t] || []).push(fn); },
    dispatch(t, ev){ (self._handlers[t] || []).forEach(fn => fn(ev)); },
    getBoundingClientRect(){ return self._rect; },
    focus(){ self._focused++; },
    closest(sel){ return matches(self, sel) ? self : (self._parent
                   ? self._parent.closest(sel) : null); },
    querySelector(sel){ return self.querySelectorAll(sel)[0] || null; },
    querySelectorAll(sel){ return (self._kids || []).filter(k => matches(k, sel)); },
    classList: {
      add(c){ if(!self.className.split(' ').includes(c)) self.className += ' ' + c; },
      remove(c){ self.className = self.className.split(' ').filter(x => x !== c).join(' '); },
      contains(c){ return self.className.split(' ').includes(c); },
      toggle(c, on){ on ? self.classList.add(c) : self.classList.remove(c); }
    }
  };
  /* Setting innerHTML is how tap.js builds both the shell and every redraw of
     the card, and it reads .firstChild straight back — so the stub gives it
     one, holding whatever was written. */
  self.firstChild = null;
  Object.defineProperty(self, 'innerHTML', {
    get(){ return self._html; },
    set(v){ self._html = String(v);
            if(!self.firstChild) self.firstChild = El('div');
            if(self.firstChild !== self) self.firstChild._html = String(v); }
  });
  return self;
}
/* Selector support: exactly the four shapes tap.js uses. */
function matches(el, sel){
  return sel.split(',').some(one => {
    one = one.trim();
    if(one.startsWith('.')) return el.className.split(' ').includes(one.slice(1));
    if(one.startsWith('[')){
      const m = one.match(/^\[([^\]=]+)(?:="([^"]*)")?\]$/);
      if(!m) return false;
      const v = el.getAttribute(m[1]);
      return m[2] === undefined ? v !== null : v === m[2];
    }
    if(one.includes('[')){
      const m = one.match(/^(\w+)\[([^\]]+)\]$/);
      return m && el.tagName === m[1] && el.getAttribute(m[2]) !== null;
    }
    return el.tagName === one;
  });
}

const CARDS = [];
const document = {
  readyState: 'complete',
  documentElement: { getAttribute: () => '' },
  body: El('body'),
  _all: [],
  createElement(tag){ const e = El(tag); CARDS.push(e); return e; },
  querySelectorAll(sel){ return document._all.filter(k => matches(k, sel)); },
  querySelector(sel){ return document.querySelectorAll(sel)[0] || null; },
  addEventListener(t, fn){ (document._h = document._h || {}); (document._h[t] = document._h[t] || []).push(fn); },
  dispatch(t, ev){ ((document._h || {})[t] || []).forEach(fn => fn(ev)); }
};
const HIST = { entries: [], back: 0, go: [] };
const window = {
  addEventListener(t, fn){ (window._h = window._h || {}); (window._h[t] = window._h[t] || []).push(fn); },
  dispatch(t, ev){ ((window._h || {})[t] || []).forEach(fn => fn(ev)); }
};
const history = {
  pushState(s){ HIST.entries.push(s); },
  back(){ HIST.back++; const s = HIST.entries.pop();
          window.dispatch('popstate', { state: HIST.entries.length ? HIST.entries[HIST.entries.length-1] : null }); },
  go(n){ HIST.go.push(n); }
};
const localStorage = { _v: {}, getItem(k){ return this._v[k] || null; },
                       setItem(k, v){ this._v[k] = v; } };
const TABLES = JSON.parse(process.argv[3]);
function XMLHttpRequest(){
  return { open(){}, send(){ this.status = 200;
    this.responseText = JSON.stringify(TABLES); this.onload && this.onload(); } };
}
const alerts = [];
function alert(m){ alerts.push(m); }
globalThis.window = window; globalThis.document = document;
globalThis.history = history; globalThis.localStorage = localStorage;
globalThis.XMLHttpRequest = XMLHttpRequest; globalThis.alert = alert;

/* ---- the fixture: one map holder, three marks ------------------------- */
function mark(attrs, x){
  const m = El('a', attrs, { rect: { left: x, top: 100, width: 8, height: 8 } });
  return m;
}
const marks = JSON.parse(process.argv[2]).map((a, i) => mark(a, 100 + i * 200));
const holder = El('div', { class: 'mdmap' });
holder.className = 'mdmap';
holder._kids = marks;
marks.forEach(m => { m._parent = holder; });
document._all = [holder];

/* ---- the shipped file — it scans for maps as it loads ---------------- */
%TAPJS%

const scenario = process.argv[4];
const out = { steps: [] };
function card(){ return CARDS.find(c => (c.className || '').includes('mdtap')); }
function shot(label){
  const c = card();
  out.steps.push({ label, hidden: !c || c.hidden,
                   html: c && c.firstChild ? c.firstChild.innerHTML : '',
                   role: c ? c.getAttribute('role') : null,
                   pushed: HIST.entries.length, went: HIST.go.slice(),
                   backs: HIST.back });
}
function tapAt(x, y, target){
  let prevented = false;
  holder.dispatch('click', {
    clientX: x, clientY: y, button: 0,
    target: target || { closest: () => null },
    preventDefault(){ prevented = true; }
  });
  out.steps.push({ label: 'tap:' + x, prevented });
}
function press(act, extra){
  const c = card();
  const btn = { getAttribute: k => (k === 'data-act' ? act : (extra || {})[k]) };
  c.dispatch('click', { target: { closest: () => btn }, preventDefault(){} });
}
MDTAP_SCENARIOS[scenario]();
console.log(JSON.stringify(out));
"""

SCENARIOS = r"""
const MDTAP_SCENARIOS = {
  /* a touch on a dot, and a touch on nothing */
  basic(){
    tapAt(104, 104); shot('on a mark');
    window.MDTAP.hide();
    tapAt(700, 600); shot('on bare ground');
  },
  /* hours: none at all, open now, shut now */
  lamp(){
    tapAt(104, 104); shot('no hours');
    window.MDTAP.hide();
    tapAt(304, 104); shot('open now');
    window.MDTAP.hide();
    tapAt(504, 104); shot('shut now');
  },
  /* the chips, with a map that can filter and one that cannot */
  filter(){
    let asked = [];
    window.MDTAP.show({ name: 'ร้านหนึ่ง', t: [0], lat: 18.78, lng: 98.99 }, null,
      { surface: { filter(tag){ asked.push(tag); return tag === null ? 9 : 0; } } });
    shot('chips as buttons');
    press('filter', { 'data-tag': '0' });
    shot('filtered to zero');
    out.asked = asked;
  },
  chiplink(){
    window.MDTAP.show({ name: 'ร้านสอง', t: [0], lat: 18.78, lng: 98.99 });
    shot('chips as links');
  },
  /* walking, and the Back button */
  walk(){
    tapAt(104, 104); shot('first card');
    press('walk', { 'data-i': '0' }); shot('walked');
    history.back(); shot('after Back');
    press('close'); shot('after close');
  }
};
"""

MARKS = [
    # name, no hours: the lamp must not appear
    {"data-mdtap": "1", "data-n": "ร้านไม่มีเวลา · No Hours Shop", "data-lat": "18.7876",
     "data-lng": "98.9933", "data-plan": "cm:a", "href": "../../cm/p/a.html",
     "data-t": "0", "data-st": "0"},
    {"data-mdtap": "1", "data-n": "ร้านเปิดอยู่ · Open Shop", "data-lat": "18.7880",
     "data-lng": "98.9940", "data-plan": "cm:b", "href": "../../cm/p/b.html",
     "data-hk": "0"},
    {"data-mdtap": "1", "data-n": "ร้านปิดแล้ว · Shut Shop", "data-lat": "18.7890",
     "data-lng": "98.9950", "data-plan": "cm:c", "href": "../../cm/p/c.html",
     "data-hk": "1"},
]

# Monday 14:30 is inside 08:00–18:00 and outside 20:00–23:00.
TABLES = {
    "tags": [["chicken", "ไก่", "Chicken", "🍗"]],
    "streets": [["moon-muang", "ถนนมูลเมือง", "Moon Muang Road"]],
    "areas": [["ศรีภูมิ", "เมืองเชียงใหม่", "cm", ""]],
    "subs": {"thai": ["อาหารไทย", "Thai"]},
    "hours": [[[480, 1080]], [[1200, 1380]]],
}


def run(scenario):
    js = HARNESS.replace("%TAPJS%", tapcard.JS + SCENARIOS)
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(js)
        path = fh.name
    try:
        proc = subprocess.run(
            ["node", path, json.dumps(MARKS, ensure_ascii=False),
             json.dumps(TABLES, ensure_ascii=False), scenario],
            capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(path)
    if proc.returncode:
        print("✗ tap.js failed to run under node:\n"
              + (proc.stderr or proc.stdout)[-2000:])
        FAIL.append("tap.js runs at all")
        return None
    return json.loads(proc.stdout)


def main():
    print("tap.js — what a touch on a map is worth")

    print(" a touch, and the silence")
    r = run("basic")
    if r:
        on, ground = r["steps"][1], r["steps"][3]
        check("a touch on a mark opens the card", not on["hidden"])
        check("and the card names the place", "ร้านไม่มีเวลา" in on["html"],
              on["html"][:120])
        check("the card is a region, never a dialog", on["role"] == "region",
              str(on["role"]))
        check("a touch on bare ground opens nothing", ground["hidden"])
        check("a mark's own click is only taken once it has answered",
              r["steps"][0]["prevented"] and not r["steps"][2]["prevented"])

    print(" the lamp, which never guesses")
    r = run("lamp")
    if r:
        none_, open_, shut = r["steps"][1], r["steps"][3], r["steps"][5]
        check("no hours recorded → no lamp at all",
              "mdtap-lamp" not in none_["html"])
        # Not a search for the word: a NEIGHBOUR called ร้านเปิดอยู่ contains
        # those letters honestly. The claim is that no lamp was drawn for this
        # place and no closed-now sentence was written about it.
        check("no hours recorded → nothing about being closed",
              "mdtap-shut" not in none_["html"]
              and "closed now" not in none_["html"])
        check("open now → the lamp says open", "เปิดอยู่" in open_["html"])
        check("shut now → the lamp says closed", "ปิดอยู่" in shut["html"])

    print(" the chips filter the map")
    r = run("filter")
    if r:
        chips, zero = r["steps"][0], r["steps"][1]
        check("a tag is a button when the map can filter",
              'data-act="filter"' in chips["html"], chips["html"][:200])
        check("pressing it narrows the map", r["asked"] == [0], str(r.get("asked")))
        check("a tag nobody has says zero out loud",
              "ไม่มีที่ไหนในกรอบนี้" in zero["html"], zero["html"][:300])
        check("and offers the same filter, sorted, on the results page",
              "search.html?tag=chicken" in zero["html"])
    r = run("chiplink")
    if r:
        h = r["steps"][0]["html"]
        check("where the map cannot filter, the chip is a link to one that can",
              'href="search.html?tag=chicken' in h and 'near=18.78,98.99' in h,
              h[:300])

    print(" walking the card, and the reader's own Back button")
    r = run("walk")
    if r:
        first, walked, backed, closed = (r["steps"][1], r["steps"][2],
                                         r["steps"][3], r["steps"][4])
        check("the nearest are offered", 'data-act="walk"' in first["html"],
              first["html"][:300])
        name = lambda h: (re.search(r'class="mdtap-name"[^>]*>([^<]*)', h)
                          or [None, ""])[1]
        check("touching one moves the card without leaving the page",
              name(walked["html"]) == "ร้านเปิดอยู่", name(walked["html"]))
        check("every card is one history entry", walked["pushed"] == 2,
              str(walked["pushed"]))
        check("Back walks the trail back",
              name(backed["html"]) == "ร้านไม่มีเวลา", name(backed["html"]))
        check("closing hands back every entry the walk took",
              closed["hidden"] and closed["went"] == [-1], str(closed["went"]))

    print(" the shape Nan asked for, in the stylesheet")
    css = tapcard.CSS
    check("no scrim: the map is never dimmed or covered",
          "inset:0" not in css and "rgba(42,30,22,.34)" not in css)
    check("no centred modal", "translate(-50%,-50%)" not in css)
    check("the sheet is a maximum height, so it grows with the reader's type",
          "max-height:58vh" in css
          and not re.search(r"(?<!max-)height:\d+vh", css))
    check("a wide screen docks it beside the map",
          "@media (min-width:900px)" in css)
    check("every control is a fingertip",
          len(re.findall(r"min-height:44px", css)) >= 4)
    check("the card is drawn in the site's own tokens, not in literals",
          len(re.findall(r"#[0-9a-fA-F]{6}", css)) <= 2)
    check("it does not print", "@media print" in css)

    print(" every map already calls it")
    check("MDCARD keeps its name and gets this card",
          "window.MDCARD=MDTAP;" in tapcard.JS)
    check("and md.js's own card stays as the fallback",
          "tap.js has not arrived" in tapcard.__doc__)

    if FAIL:
        print(f"\n✗ {len(FAIL)} failed: " + " · ".join(FAIL))
        sys.exit(1)
    print("\n✓ tap.js answers a touch the way she asked")


if __name__ == "__main__":
    main()
