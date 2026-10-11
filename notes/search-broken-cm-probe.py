#!/usr/bin/env python3
"""Is general search broken for Chiang Mai? Measure it rather than assert it.

For each query: ask Brave for the web results a person would get, classify what
comes back, check whether the links resolve, and ask Mot Dang the same question.
Writes results.json. Every number in the write-up comes from this file.
"""
import json, urllib.request, urllib.parse, urllib.error, time, sys, re, ssl

K=json.load(open('/Users/annikapeacock/.config/nanobotco/keys.json'))['brave_search']
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
CTX=ssl.create_default_context()

QUERIES = [
 # A — home-ground Thai trade terms: Chiang Mai is the world capital of these
 ("A","ตอกเส้น เชียงใหม่","tok sen"),
 ("A","ย่ำขาง เชียงใหม่","yam khang"),
 ("A","จับเส้น เชียงใหม่","chap sen"),
 ("A","ประคบสมุนไพร เชียงใหม่","herbal compress"),
 ("A","ร้านตีมีด เชียงใหม่","knife smith"),
 ("A","ช่างกุญแจ เชียงใหม่","locksmith"),
 ("A","ร้านซ่อมนาฬิกา เชียงใหม่","watch repair"),
 ("A","ร้านผ้าฝ้ายทอมือ เชียงใหม่","hand-woven cotton"),
 ("A","ร้านซ่อมจักรยาน เชียงใหม่","bicycle repair"),
 ("A","ทำฟันปลอม เชียงใหม่","dentures"),
 ("A","ร้านขายเครื่องดนตรีไทย เชียงใหม่","Thai instruments"),
 ("A","ตู้น้ำดื่มหยอดเหรียญ เชียงใหม่","coin-op water"),
 # B — ordinary needs in English, from the gaps the demand corpus named
 ("B","locksmith chiang mai","locksmith"),
 ("B","watch repair chiang mai","watch repair"),
 ("B","self storage chiang mai","self storage"),
 ("B","compounding pharmacy chiang mai","compounding pharmacy"),
 ("B","poker club chiang mai","poker club"),
 ("B","electrolysis hair removal chiang mai","electrolysis"),
 ("B","colon hydrotherapy chiang mai","colon hydrotherapy"),
 ("B","korean grocery store chiang mai","korean grocery"),
 ("B","large size shoes chiang mai","large size shoes"),
 ("B","brass band instruments chiang mai","band instruments"),
 ("B","bridge club chiang mai","bridge club"),
 ("B","indoor climbing gym chiang mai","climbing gym"),
 # C — answer-shaped: what + where + when, the shape people actually need
 ("C","tok sen massage old city chiang mai open after 9pm","tok sen late"),
 ("C","24 hour pharmacy chiang mai","24h pharmacy"),
 ("C","dentist open sunday chiang mai","dentist sunday"),
 ("C","vet open now chiang mai","vet now"),
 ("C","motorcycle parking near tha phae gate","moto parking"),
 ("C","public toilet near chiang mai gate","toilet"),
 ("C","nursing home chiang mai english speaking","nursing home"),
 ("C","laundry open late chiang mai","laundry late"),
 # D — Chiang Rai: the thin-city case
 ("D","ตอกเส้น เชียงราย","tok sen CR"),
 ("D","ช่างกุญแจ เชียงราย","locksmith CR"),
 ("D","ร้านซ่อมนาฬิกา เชียงราย","watch repair CR"),
 ("D","dentist chiang rai","dentist CR"),
 ("D","veterinarian chiang rai","vet CR"),
 ("D","hardware store chiang rai","hardware CR"),
]

AGGREGATOR = ("tripadvisor.","agoda.","booking.com","klook.","getyourguide","expedia.",
              "yelp.","trip.com","viator.","lonelyplanet","timeout.","thrillist")
SOCIAL     = ("tiktok.com","youtube.com","youtu.be","instagram.com","pinterest.")
MARKET     = ("shopee.","lazada.","aliexpress","amazon.","etsy.")
FORUM      = ("reddit.com","quora.com","thaivisa","aseannow","pantip.com","tripadvisor.com/ShowTopic")
DIRECTORY  = ("thdata.co","wongnai.com","longdo.com","dbd.go.th","yellowpages","bedandbreakfast",
              "foursquare.com","maps.google","google.com/maps","citysearch","openrice")
SOCIALBIZ  = ("facebook.com","line.me","fb.me")
MOTDANG    = ("motdang.net",)

def kind(url):
    u=url.lower()
    if any(s in u for s in MOTDANG): return "motdang"
    if any(s in u for s in AGGREGATOR): return "aggregator"
    if any(s in u for s in FORUM): return "forum"
    if any(s in u for s in SOCIAL): return "social-video"
    if any(s in u for s in MARKET): return "marketplace"
    if any(s in u for s in DIRECTORY): return "directory"
    if any(s in u for s in SOCIALBIZ): return "business-social"
    return "other"

def brave(q):
    url=K['base']+"?"+urllib.parse.urlencode({"q":q,"count":10})
    req=urllib.request.Request(url, headers={K['header']:K['key'],"Accept":"application/json"})
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req,timeout=40))
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(4+attempt*4); continue
            return {"_error":f"HTTP {e.code}"}
        except Exception as e:
            return {"_error":type(e).__name__}
    return {"_error":"rate-limited"}

def link_ok(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA}, method="GET")
    try:
        r=urllib.request.urlopen(req,timeout=20,context=CTX)
        return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def motdang(q):
    url="https://motdang.net/api/v1/places?"+urllib.parse.urlencode({"q":q,"limit":5})
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        d=json.load(urllib.request.urlopen(req,timeout=30,context=CTX))
        items=d.get("places") or d.get("results") or d.get("items") or []
        return {"n": d.get("total", len(items)), "top":[ (i.get("name") or i.get("title") or "")[:60] for i in items[:3]]}
    except Exception as e:
        return {"error":type(e).__name__}

out=[]
for i,(stratum,q,label) in enumerate(QUERIES,1):
    d=brave(q)
    res=d.get("web",{}).get("results",[]) if "_error" not in d else []
    rows=[]
    for r in res[:10]:
        rows.append({"title":r.get("title","")[:120],"url":r.get("url",""),"kind":kind(r.get("url",""))})
    for r in rows[:5]:
        r["status"]=link_ok(r["url"]); time.sleep(0.2)
    md=motdang(q.replace(" เชียงใหม่","").replace(" เชียงราย","").replace(" chiang mai","").replace(" chiang rai",""))
    out.append({"stratum":stratum,"query":q,"label":label,
                "error":d.get("_error"),"n_results":len(res),"results":rows,"motdang":md})
    print(f"{i:>2}/{len(QUERIES)} {stratum} {label:<24} brave {len(res):>2} · motdang {md.get('n','?')}", flush=True)
    time.sleep(1.2)

json.dump({"run":time.strftime("%Y-%m-%d %H:%M"),"queries":len(QUERIES),"rows":out},
          open(sys.argv[1] if len(sys.argv)>1 else "results.json","w"), ensure_ascii=False, indent=1)
print("written")
