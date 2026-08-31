#!/usr/bin/env python3
"""Turn a written address into a point, using only this catalogue's own ground.

No geocoding service is called and none should be. Nominatim's terms forbid
bulk use, and paid geocoders would put a third party between a reader and a
Chiang Mai shopfront. Everything here reads two files we already built:

  data/streets.json   — 942 roads and sois, 458 of them with real polyline
                        geometry, each with Thai name, English name, aliases
                        and alternate spellings (2,237 matchable strings).
  data/canonical/*    — 12,353 places, of which 1,288 carry BOTH an address
                        and a surveyed pin. That overlap is a ground-truth set,
                        so this module's accuracy is measured rather than
                        asserted: run `--validate`.

WHAT IT RETURNS, and how sure it is. Never a bare coordinate — always a point
WITH the precision that earned it, because a shop placed on the right road is
useful and a shop placed on the right road while claiming to be a surveyed pin
is a lie the map tells confidently:

  landmark — the address names a place we ALREADY HOLD and could be inside: a
             mall, a market, a campus, a terminal, a hotel. This is the best
             answer available, because it is somebody else's surveyed pin.
             "ชั้น B1 MAYA Lifestyle Shopping Center" lands on Maya, 0 m out.
  street   — the address named a road we hold geometry for. The point is the
             middle of that road and the stated uncertainty is half its length,
             which is the truth: we know the road, not the door.
  postcode — a five-digit Thai postcode names one delivery area and cannot be
             confused the way ตำบล เวียง can. Coarse, and it says so — but it
             is the tier that reaches the Latin-script addresses nothing else
             touches, and it took coverage from 53% to 87%.
  tambon   — the subdistrict, preferably with its อำเภอ.
  none     — nothing matched. Returns None. A record with no pin is honest; an
             invented one is not.

Tried in that order, precise first. Measured over 1,452 surveyed places that
also carry an address: landmark median 234 m, street 201 m, postcode 2,367 m,
tambon 1,817 m, and the stated uncertainty covers the truth 80% of the time.

A soi beats its parent road. "Moon Muang Rd Lane 6" is a much smaller thing
than Moon Muang Road, and streets.json holds sois in their own right, so the
longest matching name wins rather than the first.

THREE THINGS THAT ARE DELIBERATELY NOT LANDMARKS, each learned the hard way:
a ROAD (พหลโยธิน is a highway that things get named after — 52 km out), an
ADMINISTRATIVE NAME (a record literally called "เชียงใหม่" matched nearly every
address in the province), and a LINEAR FEATURE (the irrigation canal runs the
length of the valley). Each was excluded only after it was measured doing harm.
"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Words that say "this is a road" rather than which road. Stripped before
# matching so "Prapokkloa Rd" and "ถนนประปกเกล้า" reach the same key.
ROAD_WORDS = (
    "ถนน", "ซอย", "ตรอก", "แยก", "road", "rd", "soi", "lane", "alley", "street",
    "st", "highway", "hwy",
)
THAI = re.compile(r"[ก-๙]")


def _norm(s):
    """Fold a street name to a comparable key, in either script."""
    s = (s or "").lower().strip()
    s = re.sub(r"[^\w฀-๿]+", " ", s)
    parts = [p for p in s.split() if p and p not in ROAD_WORDS]
    # Thai is written unspaced, so also strip the road words when they are glued
    # to the front: ถนนนิมมานเหมินท์ -> นิมมานเหมินท์
    out = []
    for p in parts:
        for w in ("ถนน", "ซอย", "ตรอก"):
            if p.startswith(w) and len(p) > len(w) + 1:
                p = p[len(w):]
        out.append(p)
    return " ".join(out).strip()


def _haversine(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _run_midpoint(runs):
    """The middle of the longest run, measured along the line, not the average
    of its corners — a hooked road's mean can sit in a field beside it."""
    best = max(runs, key=len)
    if len(best) == 1:
        return tuple(best[0]), 0.0
    segs, total = [], 0.0
    for i in range(len(best) - 1):
        d = _haversine(best[i], best[i + 1])
        segs.append(d)
        total += d
    half, run = total / 2, 0.0
    for i, d in enumerate(segs):
        if run + d >= half:
            f = (half - run) / d if d else 0
            a, b = best[i], best[i + 1]
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), total
        run += d
    return tuple(best[-1]), total


class Gazetteer:
    def __init__(self):
        streets = json.load(open(os.path.join(ROOT, "data", "streets.json"),
                                 encoding="utf-8"))["streets"]
        # Province centroids from our own SURVEYED pins, not from any label.
        self._cent = {}
        for prov in ("cm", "cr"):
            f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            if not os.path.exists(f):
                continue
            pts = [(r["lat"], r["lng"])
                   for r in json.load(open(f, encoding="utf-8"))
                   if r.get("lat") and (r.get("geoPrecision") or "exact") == "exact"]
            if pts:
                self._cent[prov] = (sum(p[0] for p in pts) / len(pts),
                                    sum(p[1] for p in pts) / len(pts))
        self.by_name = {}
        self.mislabelled = []
        for s in streets:
            if not s.get("geom"):
                continue
            pt, length = _run_midpoint(s["geom"])
            # A STREET'S PROVINCE COMES FROM ITS GEOMETRY, NEVER ITS LABEL.
            #
            # data/streets.json carries exactly one road whose label and ground
            # disagree: Chiang Mai's ถนนเจ็ดยอด, by Wat Jed Yot, is filed
            # province=cr — 159 km from Chiang Rai and 2 km from the middle of
            # Chiang Mai. Believing the label put five Chiang Rai guesthouses
            # on a Chiang Mai road, 152 km out, and every one of them looked
            # like a confident answer. Chiang Rai has its own ถนนเจ็ดยอด and it
            # is a different road.
            #
            # Deriving from the geometry costs nothing, fixes that road without
            # waiting on build_streets.py, and immunises this against the next
            # mislabel rather than against this one.
            geo_prov = min(self._cent, key=lambda p: _haversine(pt, self._cent[p])) \
                if self._cent else s.get("province")
            if s.get("province") and geo_prov != s.get("province"):
                self.mislabelled.append((s["slug"], s.get("name"),
                                         s["province"], geo_prov))
            entry = {"slug": s["slug"], "name": s.get("name"),
                     "nameEn": s.get("nameEn"), "province": geo_prov,
                     "labelled": s.get("province"), "pt": pt, "length": length}
            names = [s.get("name"), s.get("nameEn"), s.get("key")]
            names += list(s.get("aliases") or []) + list(s.get("alsoSpelled") or [])
            for n in names:
                k = _norm(n)
                # A key holds every road that answers to it, not the first one
                # seen. Both provinces have a ถนนเจ็ดยอด and they are 159 km
                # apart; first-wins made one of them unreachable and answered
                # for the other.
                if k:
                    self.by_name.setdefault(k, []).append(entry)
        # ---- landmarks: the catalogue siting itself --------------------------
        #
        # An address that names a place we ALREADY HOLD needs no inference at
        # all — "ชั้น B1 MAYA Lifestyle Shopping Center" is a surveyed pin we
        # have had all along, and placing that shop on Changpuak Road instead
        # put it 2 km from its own front door while the right answer sat in the
        # same file. This tier is checked before the street for that reason: a
        # building beats a road every time.
        #
        # UNIQUE NAMES ONLY. There are 385 7-Elevens; a name that belongs to
        # more than one place in a province cannot site anything, so it is not
        # indexed at all rather than resolved by a coin flip.
        self.landmarks = {}
        seen_name = {}
        # EVERY road name, including the 484 with no geometry. The first guard
        # only knew roads we could draw, so พหลโยธิน — a highway we hold no
        # line for — stayed indexed as a landmark and answered for every
        # address along it, 52 km out.
        # AN ADMINISTRATIVE NAME IS NOT A LANDMARK EITHER. The catalogue holds
        # OSM place nodes for the province and for subdistricts — a record
        # literally named "เชียงใหม่", another named "Tambon Phra Sing" — and
        # both passed every test above. "เชียงใหม่" then matched almost every
        # address in the province and answered them all with one point, which
        # is how this tier came to have a 3.9 km median while the street tier
        # sat at 195 m. The good matches underneath it were real (a hotel at
        # 7 m, a university faculty at 234 m); the province name was drowning
        # them.
        admin_keys = {"เชียงใหม่", "เชียงราย", "chiang mai", "chiang rai",
                      "เมืองเชียงใหม่", "เมืองเชียงราย", "mueang chiang mai",
                      "mueang chiang rai", "chiangmai", "chiangrai"}
        for prov in ("cm", "cr"):
            f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            if not os.path.exists(f):
                continue
            for r in json.load(open(f, encoding="utf-8")):
                a = r.get("attrs") or {}
                for fld in ("subdistrict", "district", "city", "addrProvince"):
                    k = _norm(a.get(fld))
                    if k:
                        admin_keys.add(k)
        road_keys = set()
        for s in streets:
            for n in ([s.get("name"), s.get("nameEn"), s.get("key")]
                      + list(s.get("aliases") or []) + list(s.get("alsoSpelled") or [])):
                k = _norm(n)
                if k:
                    road_keys.add(k)
        for prov in ("cm", "cr"):
            f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            if not os.path.exists(f):
                continue
            for r in json.load(open(f, encoding="utf-8")):
                if (r.get("geoPrecision") or "exact") != "exact" or not r.get("lat"):
                    continue
                for n in (r.get("name"), r.get("nameEn"), r.get("nameTh")):
                    k = _norm(n)
                    # Long enough to be a name rather than a word. Thai is
                    # unspaced so it is judged on characters; Latin on words.
                    if not k or len(k) < 8:
                        continue
                    if not THAI.search(k) and len(k.split()) < 2:
                        continue
                    # A ROAD IS NOT A LANDMARK. Places get named after the road
                    # they stand on — a bank branch called พหลโยธิน — and
                    # because _norm strips the ถนน prefix, every address on
                    # that highway then matched that one branch. Five of them
                    # landed 49-52 km out, each stating ±150 m. If the name is
                    # in the street index it is a road here, whatever else also
                    # answers to it, and the street tier is the honest handler.
                    if k in self.by_name or k in road_keys or k in admin_keys:
                        continue
                    if re.match(r"^(tambon|amphoe|chang wat|changwat|ตำบล|อำเภอ|จังหวัด)\b", k):
                        continue
                    seen_name.setdefault((prov, k), []).append(r)
        # A LANDMARK IS A CONTAINER, not any place that happens to be unique.
        #
        # An address names another business only when the shop is INSIDE it —
        # a mall, a market, a hospital, a campus, a terminal, a hotel. Letting
        # every unique 8-character name in meant addresses matched noodle shops
        # and bank branches they merely stood near, and the tier's median error
        # was 3 km while the street tier's was 194 m. Restricting it to things
        # you can be inside is what the MAYA case was actually about.
        CONTAINERS = {"shopping", "market", "sport", "medical", "transport",
                      "hotel", "whats-on", "museums-galleries", "parks", "wat"}
        for (prov, k), rs in seen_name.items():
            if len({(round(x["lat"], 4), round(x["lng"], 4)) for x in rs}) != 1:
                continue        # the name belongs to more than one place
            r = rs[0]
            cats = set(r.get("cat") or [])
            if not (cats & CONTAINERS):
                continue
            # A canal is not a container. ถนนเลียบคลองชลประทาน runs the length
            # of the valley, so "somewhere on the irrigation canal" is a 12 km
            # answer dressed as a 250 m one. Linear and areal features you
            # travel ALONG rather than sit inside are no use for siting a door.
            if set(r.get("sub") or []) & {"water", "nature", "viewpoint"}:
                continue
            # How far inside its own grounds the shop could be. A mall or a
            # campus is a big thing to be "at"; a shophouse is not.
            if cats & {"shopping", "sport", "medical", "transport", "market"}:
                unc = 400
            elif cats & {"hotel", "whats-on", "parks"}:
                unc = 250
            else:
                unc = 150
            self.landmarks[(prov, k)] = (r["lat"], r["lng"], r.get("name"), unc)
        self._thai_keys = [k for k in self.landmarks if THAI.search(k[1])]

        self.tambon = {}
        acc, pair = {}, {}
        for prov in ("cm", "cr"):
            f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            if not os.path.exists(f):
                continue
            for r in json.load(open(f, encoding="utf-8")):
                # ONLY SURVEYED PINS FEED THE GAZETTEER.
                #
                # import_all writes data/canonical and this reads it, so on the
                # second run our own INFERRED pins would come back as ground
                # truth and the error would compound quietly, run after run —
                # a centroid built from guesses, siting the next guess. An
                # approximate pin is an output of this module and must never
                # become an input to it.
                if (r.get("geoPrecision") or "exact") != "exact":
                    continue
                a = r.get("attrs") or {}
                t = _norm(a.get("subdistrict"))
                if t and r.get("lat"):
                    acc.setdefault(t, []).append((r["lat"], r["lng"]))
        # A TAMBON CENTROID IS ONLY WORTH ANYTHING IF THE TAMBON IS ONE PLACE.
        #
        # เวียง is the commonest subdistrict name in the north — Mueang Chiang
        # Rai has one, and so do Chiang Khong, Chiang Saen, Phan, Thoeng and
        # Wiang Pa Pao. Averaging every place called ต.เวียง puts the centre in
        # open country between them, and it answered five Chiang Rai addresses
        # 28 km out while sounding as certain as any other row.
        #
        # So each tambon is measured before it is trusted: the spread is the
        # 90th-percentile distance of its own places from their centre. A
        # spread over SPREAD_MAX_M means the name belongs to several places at
        # once and is refused. What survives publishes its own real spread as
        # its uncertainty rather than a flat guess.
        # The temple register is the better gazetteer, and it was already on
        # disk. WO-1 stamped 346 wats with ตำบล and อำเภอ from the ONAB
        # register, and every one of them has a surveyed pin — so 103 distinct
        # (province, tambon, amphoe) centroids fall out of a join we already
        # own, reaching Chiang Khong, Mae Chan and Hot, where the street layer
        # has nothing at all.
        #
        # Thai keys ONLY. The obvious next step — learning ตำบล -> "Tambon"
        # spellings from the same join — was tried and refused: of eight pairs
        # it produced, พระสิงห์ -> "Si Phum" and ท่าสุด -> "Mae Yao" are simply
        # different subdistricts, from boundary wats whose OSM address names
        # the neighbour. Two wrong in eight is not a transliteration table, it
        # is a way to put shops in the wrong ตำบล with total confidence. A
        # Latin-script address that names no road we hold goes unplaced, and
        # that is the correct outcome.
        # ---- postcodes: an unambiguous key we were already carrying ---------
        #
        # A Thai postcode names one district's delivery area and cannot be
        # confused with another the way ตำบล เวียง can. 888 of our surveyed
        # pins carry one, and nearly every address written for a shop ends in
        # one — including the Latin-script addresses that reach no other tier.
        self.postcode = {}
        pc = {}
        for prov in ("cm", "cr"):
            f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            if not os.path.exists(f):
                continue
            for r in json.load(open(f, encoding="utf-8")):
                if (r.get("geoPrecision") or "exact") != "exact" or not r.get("lat"):
                    continue
                code = ((r.get("attrs") or {}).get("postcode") or "").strip()
                if re.fullmatch(r"\d{5}", code):
                    pc.setdefault((prov, code), []).append((r["lat"], r["lng"]))
        for key, pts in pc.items():
            if len(pts) < 3:
                continue
            la = sum(p[0] for p in pts) / len(pts)
            ln = sum(p[1] for p in pts) / len(pts)
            ds = sorted(_haversine((la, ln), p) for p in pts)
            self.postcode[key] = (la, ln, len(pts),
                                  int(max(ds[int(len(ds) * 0.9)], 400)))

        reg = os.path.join(ROOT, "data", "curated", "wat_registry.json")
        if os.path.exists(reg):
            by_id = {}
            for prov in ("cm", "cr"):
                f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
                if os.path.exists(f):
                    for r in json.load(open(f, encoding="utf-8")):
                        by_id[r["id"]] = r
            for wid, w in json.load(open(reg, encoding="utf-8"))["wats"].items():
                r = by_id.get(wid)
                sd, dd = w.get("tambon_th"), w.get("amphoe_th")
                if not (r and r.get("lat") and sd):
                    continue
                if (r.get("geoPrecision") or "exact") != "exact":
                    continue
                acc.setdefault(_norm(sd), []).append((r["lat"], r["lng"]))
                if dd:
                    pair.setdefault(_norm(f"{sd} {dd}"), []).append((r["lat"], r["lng"]))

        # A ตำบล+อำเภอ pair names exactly one place, so two points are enough to
        # site it. A BARE ตำบล does not, and relaxing it to two was a mistake
        # that cost 72 km: two temples in one district's เวียง gave a 250 m
        # spread, and that tiny, confident number then answered for a different
        # district's เวียง entirely. The pair is trusted at two; the bare name
        # has to show three and survive the spread test, because the thing being
        # tested is whether the NAME is unique, not whether the points are tight.
        SPREAD_MAX_M = 6000
        for t, pts in list(pair.items()) + list(acc.items()):
            if len(pts) < (2 if t in pair else 3):
                continue
            la = sum(p[0] for p in pts) / len(pts)
            ln = sum(p[1] for p in pts) / len(pts)
            ds = sorted(_haversine((la, ln), p) for p in pts)
            # With a handful of points the 90th percentile is optimistic — it
            # simply drops the one that would have told the truth. Under four,
            # the widest is the honest number.
            spread = ds[-1] if len(ds) < 4 else ds[int(len(ds) * 0.9)]
            if spread > SPREAD_MAX_M:
                continue
            self.tambon[t] = (la, ln, len(pts), int(max(spread, 250)))

    def street_of(self, address, province=None):
        """Longest street name in the address, preferring the right province.

        Longest wins because a soi is a smaller and therefore better answer
        than the road it hangs off: "Moon Muang Rd Lane 6" should land on the
        lane, not on the 1.6 km road.
        """
        norm_addr = _norm(address)
        if not norm_addr:
            return None
        best = None
        for k, entries in self.by_name.items():
            if len(k) < 4:
                continue
            if not re.search(r"(?:^| )" + re.escape(k) + r"(?:$| )", norm_addr):
                continue
            # Among roads sharing this name, the one in the province we were
            # told about. If none is, the match is refused rather than guessed:
            # a road of the right name in the wrong province is the single
            # worst answer available, because it is confident and 159 km out.
            pool = [e for e in entries if not province or e["province"] == province]
            if not pool:
                continue
            e = max(pool, key=lambda x: x["length"])
            if best is None or len(k) > len(best[0]):
                best = (k, e)
        return best

    def _tambon_of(self, address):
        # ตำบล X อำเภอ Y first, because half the north shares subdistrict names
        # and the pair is the thing that is actually unique.
        m = re.search(r"(?:ตำบล|ต\.)\s*([ก-๙]+).{0,12}?(?:อำเภอ|อ\.)\s*([ก-๙]+)",
                      address)
        if m:
            k = _norm(f"{m.group(1)} {m.group(2)}")
            if k in self.tambon:
                la, ln, n, spread = self.tambon[k]
                return {"lat": round(la, 6), "lng": round(ln, 6),
                        "precision": "tambon", "via": "tambon-amphoe-centroid",
                        "uncertainty_m": spread,
                        "matched": f"{m.group(1)} / {m.group(2)}", "from_places": n}
        for chunk in re.split(r"[,ๆ]| อ\.| อำเภอ|amphoe|tambon|ตำบล|ต\.", address,
                              flags=re.I):
            t = _norm(chunk)
            if t in self.tambon:
                la, ln, n, spread = self.tambon[t]
                return {"lat": round(la, 6), "lng": round(ln, 6),
                        "precision": "tambon", "via": "tambon-centroid",
                        "uncertainty_m": spread, "matched": chunk.strip(),
                        "from_places": n}
        return None

    def landmark_of(self, address, province):
        """The longest place we already hold whose name is written in this
        address. Longest wins so "Maya Lifestyle Shopping Center" beats a
        shorter name sitting inside it."""
        na = _norm(address)
        if not na:
            return None
        # Latin names are looked up as word n-grams rather than scanned for:
        # 10,537 regex passes per address took five and a half minutes over the
        # ground-truth set. Thai has no word gaps, so those keys still need a
        # substring test — but there are far fewer of them.
        toks = na.split()
        cands = set()
        for n in range(1, 7):
            for i in range(len(toks) - n + 1):
                key = (province, " ".join(toks[i:i + n]))
                if key in self.landmarks:
                    cands.add(key)
        for key in self._thai_keys:
            if (not province or key[0] == province) and key[1] in na:
                cands.add(key)
        best = None
        for (prov, k) in cands:
            v = self.landmarks[(prov, k)]
            if province and prov != province:
                continue
            if len(k) > len(na):
                continue
            # Thai runs together, so it is matched as a substring; Latin is
            # matched on whole words, or "Ping Hotel" would match "Camping
            # Hotel".
            if THAI.search(k):
                if k not in na:
                    continue
            elif not re.search(r"(?:^| )" + re.escape(k) + r"(?:$| )", na):
                continue
            # A subdistrict is not a landmark. "ตำบลสุเทพ" names the ตำบล even
            # where a place called Suthep also exists, and reading it as the
            # building would site every address in that ตำบล at one door.
            if re.search(r"(?:ตำบล|ต\.|อำเภอ|อ\.|จังหวัด|จ\.|tambon|amphoe|chang wat)\s*"
                         + re.escape(k[:6]), address, re.I):
                continue
            # ...and reject it where this particular address is plainly
            # using the name as a road: "129 ถนนพหลโยธิน" names a highway even
            # if something in the catalogue is also called that.
            if re.search(r"(?:ถนน|ซอย|ตรอก|\brd\b|\broad\b|\bsoi\b|\blane\b)\s*"
                         + re.escape(k[:6]), address, re.I):
                continue
            if best is None or len(k) > len(best[0]):
                best = (k, v)
        return best

    def locate(self, address, province=None):
        """-> dict(lat, lng, precision, via, uncertainty_m, matched) or None."""
        if not address:
            return None
        lm = self.landmark_of(address, province)
        if lm:
            _, (la, ln, nm, unc) = lm
            return {"lat": round(la, 6), "lng": round(ln, 6),
                    "precision": "landmark", "via": "address-names-a-place-we-hold",
                    "uncertainty_m": unc, "matched": nm}
        hit = self.street_of(address, province)
        tb = self._tambon_of(address)
        if hit:
            _, e = hit
            street = {"lat": round(e["pt"][0], 6), "lng": round(e["pt"][1], 6),
                      "precision": "street", "via": "address-street-match",
                      "uncertainty_m": int(max(e["length"] / 2, 25)),
                      "matched": e.get("nameEn") or e.get("name"),
                      "street_slug": e["slug"]}
            # THE TWO SIGNALS CHECK EACH OTHER.
            #
            # The dangerous failure is not a long road, it is the WRONG road:
            # a short soi with the right name somewhere else in the province,
            # which lands 8 km out while declaring ±194 m. The road name and the
            # subdistrict come from different halves of the same address, so
            # when they disagree by more than both their uncertainties allow,
            # one of them is wrong and we do not know which — so the coarser,
            # harder-to-fool one is used and the disagreement is published
            # rather than hidden.
            if tb:
                apart = _haversine((street["lat"], street["lng"]),
                                   (tb["lat"], tb["lng"]))
                if apart > street["uncertainty_m"] + tb["uncertainty_m"]:
                    tb = dict(tb)
                    tb["via"] = "tambon-centroid (street match disagreed)"
                    tb["rejected_street"] = street["matched"]
                    tb["disagreement_m"] = int(apart)
                    return tb
            return street
        if tb:
            return tb
        # Last real tier. Coarse, and it says so — but a shop the reader can
        # see is in the right corner of the right district beats a shop the map
        # has never heard of, and every address ends in one of these.
        m = re.search(r"\b(\d{5})\b", address)
        if m and province and (province, m.group(1)) in self.postcode:
            la, ln, n, spread = self.postcode[(province, m.group(1))]
            return {"lat": round(la, 6), "lng": round(ln, 6),
                    "precision": "postcode", "via": "postcode-centroid",
                    "uncertainty_m": spread, "matched": m.group(1),
                    "from_places": n}
        return None


def validate(limit=0):
    """Measure it against places that carry BOTH an address and a real pin."""
    g = Gazetteer()
    errs, by_prec = [], {}
    tested = 0
    for prov in ("cm", "cr"):
        f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        for r in json.load(open(f, encoding="utf-8")):
            # SURVEYED PINS ONLY. Once the weed.th records landed, the
            # catalogue held 243 pins this module had itself inferred, and
            # scoring against those is marking your own homework — it reported
            # a "median 0 m" tambon tier, which is exactly what you get when
            # the answer key was copied from the candidate.
            if (r.get("geoPrecision") or "exact") != "exact":
                continue
            if not r.get("lat") or not r.get("address"):
                continue
            got = g.locate(r["address"], prov)
            tested += 1
            if not got:
                by_prec.setdefault("none", []).append(None)
                continue
            d = _haversine((r["lat"], r["lng"]), (got["lat"], got["lng"]))
            errs.append((d, got["precision"], r.get("name"), r["address"][:60],
                         got["uncertainty_m"]))
            by_prec.setdefault(got["precision"], []).append(d)
            if limit and len(errs) >= limit:
                break
    print(f"ground truth: {tested} places carry an address AND a surveyed pin")
    for prec in ("landmark", "street", "postcode", "tambon", "none"):
        v = by_prec.get(prec) or []
        if prec == "none":
            print(f"  {prec:8s} {len(v):5d}  (no match — returns None, nothing invented)")
            continue
        if not v:
            continue
        v2 = sorted(v)
        med = v2[len(v2) // 2]
        p90 = v2[int(len(v2) * 0.9)]
        print(f"  {prec:8s} {len(v):5d}  median {med:7.0f} m   90th {p90:7.0f} m"
              f"   worst {v2[-1]:7.0f} m")
    # THE METRIC THAT DECIDES WHETHER THIS MAY SHIP.
    #
    # A median is not the point. This site publishes a pin WITH the distance it
    # might be wrong by, so the question a reader's trust rests on is whether
    # that stated distance actually covers the truth. A 13 km miss on a road
    # 27 km long, declared as ±13.5 km, is an honest answer. A 300 m miss
    # declared as ±25 m is not, however much better it looks in a median.
    if errs:
        covered = sum(1 for d, _, _, _, u in errs if d <= u)
        print(f"\ncalibration: the true pin falls inside the stated uncertainty "
              f"for {covered} of {len(errs)} ({100 * covered / len(errs):.0f}%)")
    if errs:
        print("\nworst five (the ones to look at before trusting this):")
        for d, prec, name, addr, unc in sorted(errs, reverse=True)[:5]:
            mark = "within" if d <= unc else "OUTSIDE"
            print(f"  {d:8.0f} m  [{prec}] stated \u00b1{unc:6d} m {mark:7s} "
                  f"{str(name)[:24]:24} {addr}")


if __name__ == "__main__":
    if "--validate" in sys.argv:
        validate()
    else:
        g = Gazetteer()
        print(f"gazetteer: {len(g.by_name)} street names with geometry, "
              f"{len(g.tambon)} tambon centroids")
        for a in ("24/1 Moon Muang Rd Lane 6, Tambon Si Phum, Amphoe Mueang Chiang Mai, 50200",
                  "264 Prapokkloa Rd, Tambon Si Phum, Chiang Mai 50200",
                  "3 ถนนนิมมานเหมินท์ ตำบลสุเทพ อำเภอเมืองเชียงใหม่ เชียงใหม่ 50200"):
            print("\n", a)
            print("  ->", json.dumps(g.locate(a, "cm"), ensure_ascii=False))
