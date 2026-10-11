#!/usr/bin/env python3
"""เช่ารถ — which vehicles a hire shop hires, read off its own words.

Nan, 2026-10-04, after searching motdang for "Big bike rental": "Bikes and
cars should be separate shelves. About 80% of the time in Thailand when
someone says 'bike' they mean scooter. Same with motorcycle." The importers
file every hire shop under one sub, `rental` (Car & Bike Rental), and the
assistant recommended C & P Big Bike For Rent, which sat on the motorbike
dealers' shelf because Overture calls it a motorcycle_dealer.

This pass reads what a record already says — its name, the kind written off
its sign, its trade words, its description, the category its directory gave
it — and writes:

  sub            `rental` becomes car-rental and/or motorbike-rental; a shop
                 that hires bicycles joins the bicycle shelf. A place that
                 hires both lands on both.
  cat            `transport` added to a place whose own NAME says it hires
                 vehicles but whose directory filed it elsewhere (a cafe, a vet,
                 a dispensary — Overture's category, not the shop's).
  attrs.hires    ["bicycle", "car", "motorbike"] — what it hires.
  attrs.hiresVia {vehicle: "field: word"} — the word read.
  attrs.bigBike  true where the record's own words say big bike (บิ๊กไบค์),
                 or the brand on it builds nothing under 250 cc.
  attrs.bigBikeVia the word or brand.

A specific word wins over a generic one: รถเช่า and "rental" mean a car only
when nothing on the record names a motorbike or a bicycle, because the
scooter shops on Kotchasarn write รถเช่า on their signs too. Directory
categories (Overture's car_rental_agency, Facebook's Car Rental) are read
last, for the same reason — Overture files scooter shops as car rental.

Deterministic and idempotent; called from derive.PASSES, so it runs at the
tail of importers/import_all.py and with `python3 derive.py`.
"""
from __future__ import annotations

import re

SRC = "derived:vehicle-words"
SUBS = {"car": "car-rental", "motorbike": "motorbike-rental", "bicycle": "bicycle"}

# Fields read, in the order a reason is quoted from.
_FIELDS = ("name", "nameTh", "nameEn")
_ATTR_FIELDS = ("kind", "kindTh", "signText", "tradeTags", "desc", "description",
                "services")

_MOTO = re.compile(
    r"มอเตอร์ไซ[คต]์?|มอไซ[คต]์?|มอ'ไซ|จักรยานยนต์|สกู[๊]?[ตท]เตอร์|บิ๊?ก\s*ไบ[คกดท]์?|"
    r"\bmotor\s*-?\s*bikes?\b|\bmotorcycles?\b|\bmotor\s*cycles?\b|\bscooters?\b|"
    r"\bmoto\b|\bm/c\b|\bbig\s*-?\s*bikes?\b|\bbigbikes?\b|\bdirt\s*bikes?\b|"
    r"\bvespa\b|\bmopeds?\b|\bmotorbike", re.I)
# "bike" on its own is a scooter here (Nan, 2026-10-04) — unless the same
# record says pedal, bicycle or cycling, which _BICYCLE catches first.
_BIKE = re.compile(r"\bbikes?\b|ไบค์|ไบท์", re.I)
_BICYCLE = re.compile(
    r"จักรยาน(?!ยนต์)|รถถีบ|\bbicycles?\b|\bpedal\s*-?\s*bikes?\b|\bcycling\b|"
    r"\bmountain\s*bikes?\b|\bmtb\b|\be-?bikes?\b|\bpush\s*bikes?\b", re.I)
_CAR = re.compile(
    r"รถยนต์|รถตู้|รถเก๋ง|รถกระบะ|รถบัส|รถอีโคคาร์|คาร์\s*เร[้]?[นล]|คาร์เล้นท์|คาร์เร้นท์|"
    r"เร้นท์\s*อะ\s*คาร์|\bcars?\b|\bvans?\b|\bminivans?\b|\bsuvs?\b|\bpick\s*-?\s*ups?\b|"
    r"\bautos?\b|\bautomobiles?\b|car\s*-?\s*rent|\brent\s*a\s*car\b|\bdrivers?\b|"
    r"พร้อมคนขับ|\bleasing\b|ลีสซิ่ง|\btrucks?\b", re.I)
# Words that say "hire" without saying what.
_HIRE = re.compile(r"เช่า|\brent(?:al|als|ing|s)?\b|\bhire\b|\bfor\s+rent\b|"
                   r"เร้น[ทต]์?|เรนท์|เรนทัล|เร้นทัล|rent\s*a\s*car|carrent", re.I)
# Generic vehicle words: a car in Thai shop-speak only when nothing more
# specific stands on the record.
_GENERIC = re.compile(r"รถเช่า|รถให้เช่า|เช่ารถ|\bvehicles?\b", re.I)
# The shop's own web address, read without word edges (osomcarrental.com).
_URL_CAR = re.compile(r"car-?rent|rent-?a-?car|carhire|rentcar", re.I)
_URL_MOTO = re.compile(r"motorbike|motorcycle|scooter|bikerent|bike-rent|bigbike", re.I)
# Hire of these is not a ride: excavators, rollers, cranes, scaffolding.
# A record carrying one joins neither hire shelf.
_NOT_A_RIDE = re.compile(r"แบคโฮ|รถบด|เครน|รถแม็คโคร|รถขุด|backhoe|excavator|crane|"
                         r"forklift|โฟล์คลิฟท์|นั่งร้าน|scaffold", re.I)
# Car-hire companies, read only on a record a directory already filed as hire.
_HIRE_BRANDS = re.compile(r"\b(avis|hertz|budget|europcar|enterprise|alamo|national|"
                          r"thrifty|sixt|dollar|yesaway|thai\s*rent)\b", re.I)

_BIGBIKE = re.compile(r"\bbig\s*-?\s*bikes?\b|\bbigbikes?\b|บิ๊?ก\s*ไบ[คกดท]์?|บิ้ก\s*ไบ[คก]์", re.I)
# Makers whose whole range is over 250 cc. Read only off attrs.brand or a
# transport / repair record's own name — Triumph is also a lingerie brand.
_BIG_BRANDS = re.compile(r"harley|ducati|triumph|royal\s*enfield|bmw\s*motorrad", re.I)
_BIG_BRAND_CATS = {"transport", "repair"}

# Directory categories, read last and only where the name itself says hire —
# Overture files a noodle shop, a car wash and a Nissan dealer as
# car_rental_agency, and a riverside grill as motorcycle_rentals.
_DIR_CAR = {"car_rental_agency", "car_rental", "truck_rentals", "Car Rental",
            "Rental Car", "Car Rental Agency"}
_DIR_MOTO = {"motorcycle_rentals", "Motorcycle Dealership", "Bike Rental",
             "Motorcycle Rental"}
_DIR_BICYCLE = {"bike_rentals", "Bicycle Shop"}
# OpenStreetMap's own tags (importers/import_overpass.py keeps them as
# attrs.hireTag / attrs.hireTypes).
_OSM_TAG = {"car_rental": "car", "motorcycle_rental": "motorbike",
            "bicycle_rental": "bicycle"}


def _texts(r):
    """(label, text) pairs for every field this pass reads."""
    out = [(k, str(r.get(k) or "")) for k in _FIELDS if r.get(k)]
    a = r.get("attrs") or {}
    for k in _ATTR_FIELDS:
        v = a.get(k)
        if not v:
            continue
        if isinstance(v, (list, tuple)):
            v = " · ".join(str(x) for x in v)
        out.append((k, str(v)))
    return out


def _first(rx, texts):
    for k, t in texts:
        m = rx.search(t)
        if m:
            return f"{k}: {m.group(0).strip()}"
    return None


def _dir_cats(r):
    a = r.get("attrs") or {}
    got = []
    if a.get("overtureCategory"):
        got.append(("overtureCategory", a["overtureCategory"]))
    for c in a.get("fbCategories") or []:
        got.append(("fbCategories", c))
    return got


def _own_words(r):
    a = r.get("attrs") or {}
    return " ".join(str(r.get(k) or "") for k in _FIELDS) + " " + str(a.get("kind") or "")


def hire_name(r) -> bool:
    """Whether the record's own name (or the kind read off its sign) says it
    hires vehicles out. A name is the shop's own description of itself here."""
    words = _own_words(r)
    if _NOT_A_RIDE.search(words) or not _HIRE.search(words):
        return False
    return bool(_MOTO.search(words) or _BIKE.search(words) or _BICYCLE.search(words)
                or _CAR.search(words) or _GENERIC.search(words))


def classify(r, filed=True) -> dict:
    """{vehicle: reason} for a hire record. Empty when nothing on it answers."""
    if _NOT_A_RIDE.search(_own_words(r)):
        return {}
    a = r.get("attrs") or {}
    texts = _texts(r)
    if a.get("hireTypes"):
        texts.append(("hireTypes", str(a["hireTypes"])))
    got = {}
    bic = _first(_BICYCLE, texts)
    if bic:
        got["bicycle"] = bic
    moto = _first(_MOTO, texts)
    if moto:
        got["motorbike"] = moto
    elif not bic:
        b = _first(_BIKE, texts)
        if b:
            got["motorbike"] = b
    car = _first(_CAR, texts)
    if car:
        got["car"] = car
    if not got:
        g = _first(_GENERIC, texts)
        if g:
            got["car"] = g
    if not got:
        urls = [(k, str(v)) for k, v in (("website", r.get("website")),
                                         ("facebook", a.get("facebook"))) if v]
        u = _first(_URL_MOTO, urls)
        if u:
            got["motorbike"] = u
        else:
            u = _first(_URL_CAR, urls)
            if u:
                got["car"] = u
    if not got and a.get("hireTag") in _OSM_TAG:
        got[_OSM_TAG[a["hireTag"]]] = f"hireTag: {a['hireTag']} (OpenStreetMap)"
    if not got and filed:
        m = _HIRE_BRANDS.search(_own_words(r))
        if m:
            got["car"] = f"name: {m.group(0)} (car-hire company)"
    if not got and _HIRE.search(_own_words(r)):
        for k, v in _dir_cats(r):
            if v in _DIR_MOTO:
                got["motorbike"] = f"{k}: {v}"
            elif v in _DIR_BICYCLE:
                got["bicycle"] = f"{k}: {v}"
            elif v in _DIR_CAR:
                got["car"] = f"{k}: {v}"
    return got


def big_bike(r):
    """The word or brand that says big bike, or None."""
    texts = _texts(r)
    why = _first(_BIGBIKE, texts)
    if why:
        return why
    a = r.get("attrs") or {}
    if (a.get("facets") or {}).get("bigbike"):
        return "facets: bigbike (trade register)"
    if set(r.get("cat") or []) & _BIG_BRAND_CATS:
        for k in ("brand",):
            m = _BIG_BRANDS.search(str(a.get(k) or ""))
            if m:
                return f"brand: {a[k]}"
        m = _BIG_BRANDS.search(" ".join(str(r.get(k) or "") for k in _FIELDS))
        if m:
            return f"name: {m.group(0)}"
    return None


def apply(records: list, prov: str, counts: dict | None = None, today: str = "") -> int:
    import provenance
    c = counts if counts is not None else {}
    written = 0

    def bump(k):
        c[k] = c.get(k, 0) + 1

    def receipt(r, field):
        if not any(provenance.source_key(s) == SRC for s in r.get("sources") or []):
            r.setdefault("sources", []).append(
                {"type": "derived", "via": "vehicle-words", "fetched": today})
        # hires / bigBike carry their receipt in *Via; only the tracked
        # fields (cat, sub) take a provenance row.
        if field in provenance.TRACKED:
            provenance.stamp(r, field, SRC, provenance.DERIVED, today)

    for r in records:
        cats = list(r.get("cat") or [])
        subs = list(r.get("sub") or [])
        a = r.get("attrs") or {}
        filed = ("transport" in cats and "rental" in subs) or bool(a.get("hireTag"))
        named = not filed and not a.get("hires") and hire_name(r)
        if filed or named:
            got = classify(r, filed)
            new_subs = [s for s in subs if s != "rental"]
            if not got and "rental" in subs:
                # Filed as hire by a directory and nothing on the record names
                # a vehicle (a tent hire, a camera hire, a noodle shop Overture
                # called car_rental_agency): it leaves the hire shelves and
                # stays on the transport shelf it was given.
                bump("vehicleHire/no-vehicle-named")
            for v in sorted(got):
                if SUBS[v] not in new_subs:
                    new_subs.append(SUBS[v])
            if got and "transport" not in cats:
                cats.append("transport")
                r["cat"] = cats
                receipt(r, "cat")
                bump("vehicleHire/joined-from-elsewhere")
            if new_subs != subs:
                r["sub"] = new_subs
                if new_subs:
                    receipt(r, "sub")
                else:
                    # An empty field carries no receipt (provenance.validate).
                    (r.get("provenance") or {}).pop("sub", None)
            if got:
                attrs = r.setdefault("attrs", {})
                hires = sorted(got)
                if attrs.get("hires") != hires:
                    attrs["hires"] = hires
                    attrs["hiresVia"] = {v: got[v] for v in hires}
                    receipt(r, "hires")
                    written += 1
                for v in hires:
                    bump(f"vehicleHire/{v}")
        why = big_bike(r) if (set(cats) & {"transport", "repair", "shopping", "business"}) else None
        if why:
            attrs = r.setdefault("attrs", {})
            if not attrs.get("bigBike"):
                attrs["bigBike"] = True
                attrs["bigBikeVia"] = why
                receipt(r, "bigBike")
                written += 1
            bump("vehicleHire/bigBike")
    return written
