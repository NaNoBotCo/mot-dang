#!/usr/bin/env python3
"""derive.py — what it reads out of a string, and what it refuses to.

    python3 tests/test_derive.py

The failure this guards against is not a crash. A parser that quietly starts
writing a plausible-looking อำเภอ that does not exist, or overwrites a
register's fact with a reading, works perfectly and is wrong — and a wrong
administrative field is invisible on the page and poisonous in a search.
So most of what is asserted here is a refusal.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import derive  # noqa: E402
import provenance  # noqa: E402

FAILS = []


def t(name, fn):
    try:
        fn()
        print("  ok   " + name)
    except AssertionError as e:
        FAILS.append(name)
        print(f"  FAIL {name}\n       {e}")


# ------------------------------------------------------------- the reading

def _real_address():
    got = derive.parse_address("150/2 หมู่ที่ 3 ตำบลป่าบง อำเภอสารภี 50140")
    assert got == {"amphoe": "สารภี", "tambon": "ป่าบง", "moo": "3",
                   "postcode": "50140"}, got


def _abbreviated():
    got = derive.parse_address("99 ถ.นิมมานเหมินท์ ซ.5 ต.สุเทพ อ.เมือง จ.เชียงใหม่ 50200")
    assert got["amphoe"].startswith("เมือง"), got
    assert got["tambon"] == "สุเทพ", got
    assert got["road"] == "นิมมานเหมินท์", got
    assert got["soi"] == "5", got
    assert got["postcode"] == "50200", got


def _no_spaces():
    """A Thai address is often written with nothing between the parts."""
    got = derive.parse_address("ตำบลช้างเผือกอำเภอเมืองเชียงใหม่จังหวัดเชียงใหม่")
    assert got["tambon"] == "ช้างเผือก", got
    assert got["amphoe"] == "เมืองเชียงใหม่", got


def _empty():
    assert derive.parse_address("") == {}
    assert derive.parse_address("123 Nimman Road, Chiang Mai") == {}


def _house_number_is_not_a_postcode():
    got = derive.parse_address("12345/6 ถนนช้างคลาน")
    assert "postcode" not in got, got


def _typed_sara_e():
    """เ+เ for แ — a real fault on real records, worth one line of repair."""
    assert derive.normalise("เเม่ริม") == "แม่ริม"


def _typed_sara_am():
    """ํ+า for ำ — 228 roads; ราชดําเนิน read "Ratdanoen" and matched no street."""
    assert derive.normalise("ราชดําเนิน") == "ราชดำเนิน"
    got = derive.parse_address("12 ถ.ราชดําเนิน ต.ศรีภูมิ อ.เมือง 50200")
    assert got["road"] == "ราชดำเนิน", got


# ------------------------------------------------------------- the refusals

def _unknown_amphoe_is_refused():
    known = {"สารภี": [18.69, 99.01, 10925], "เมืองเชียงใหม่": [18.79, 98.98, 9000]}
    name, mode = derive.resolve_amphoe("ทองผาภูมิ", "cm", known)
    assert name is None, f"invented an อำเภอ: {name} ({mode})"


def _muang_resolves_to_this_province():
    known = {"เมืองเชียงราย": [19.9, 99.8, 12000]}
    name, _ = derive.resolve_amphoe("เมือง", "cr", known)
    assert name == "เมืองเชียงราย", name


def _near_match_is_bounded():
    """One transposed letter, yes. A different word, no."""
    known = {"ดอยสะเก็ด": [18.9, 99.2, 25865]}
    assert derive.resolve_amphoe("ดอยสะเก็ต", "cm", known)[0] == "ดอยสะเก็ด"
    assert derive.resolve_amphoe("ดอยหล่อ", "cm", known)[0] is None


# ------------------------------------------------------- the pass on records

def _rec(**kw):
    r = {"id": "x", "province": "cm", "name": "ที่หนึ่ง", "cat": ["food"],
         "sources": [{"type": "osm", "ref": "node/1"}], "attrs": {}}
    r.update(kw)
    r.setdefault("attrs", {})
    return r


def _fills_only_what_is_empty():
    already = _rec(address="ตำบลป่าบง อำเภอสารภี", attrs={"amphoe": "หางดง"})
    derive.apply_address([already], "cm")
    assert already["attrs"]["amphoe"] == "หางดง", \
        "a derivation overwrote a value that was already there"


def _writes_when_empty_and_stamps_a_receipt():
    r = _rec(address="ตำบลป่าบง อำเภอสารภี 50140")
    n = derive.apply_address([r], "cm")
    assert n >= 2, n
    assert r["attrs"]["amphoe"] == "สารภี", r["attrs"]
    assert r["attrs"]["postcode"] == "50140", r["attrs"]
    entry = provenance.of(r, "amphoe")
    assert entry, "no receipt for a field this pass wrote"
    assert entry["how"] == provenance.DERIVED, entry
    assert entry["source"] == derive.SRC, entry


def _a_derived_field_is_never_giveable():
    r = _rec(address="อำเภอสารภี")
    derive.apply_address([r], "cm")
    assert not provenance.giveable(r, "amphoe"), \
        "a reading of ours would be offered to OpenStreetMap as a fact"


def _unconfirmed_tambon_says_so():
    r = _rec(address="ตำบลไม่มีอยู่จริงนะ อำเภอสารภี")
    derive.apply_address([r], "cm")
    assert "tambon" not in r["attrs"], \
        "an unconfirmed reading landed in the same field as a register's fact"
    assert r["attrs"].get("tambonSaid"), r["attrs"]


def _the_pin_is_a_second_witness():
    """A pin in Chiang Mai city against an address claiming Fang, 100 km north."""
    r = _rec(address="อำเภอฝาง", lat=18.7877, lng=98.9931)
    derive.apply_address([r], "cm")
    assert r["attrs"].get("amphoeDisputed"), \
        "the pin and the address disagree and nothing on the record says so"


def _idempotent():
    r = _rec(address="ตำบลป่าบง อำเภอสารภี 50140 หมู่ที่ 3")
    derive.apply_address([r], "cm")
    first = json.dumps(r, ensure_ascii=False, sort_keys=True)
    assert derive.apply_address([r], "cm") == 0, "a second run wrote again"
    assert json.dumps(r, ensure_ascii=False, sort_keys=True) == first, \
        "running twice changed the record"


print("derive")
for name, fn in [
    ("a real address gives up every part of itself", _real_address),
    ("the abbreviated form reads the same", _abbreviated),
    ("no spaces between the parts still parses", _no_spaces),
    ("nothing in, nothing out", _empty),
    ("a five-digit house number is not a postcode", _house_number_is_not_a_postcode),
    ("เ+เ typed for แ is repaired", _typed_sara_e),
    ("ํ+า typed for ำ is repaired", _typed_sara_am),
    ("an อำเภอ this province does not have is refused", _unknown_amphoe_is_refused),
    ("อ.เมือง means THIS province's city district", _muang_resolves_to_this_province),
    ("a near match is one letter, not one guess", _near_match_is_bounded),
    ("a value already on the record is never overwritten", _fills_only_what_is_empty),
    ("an empty field is filled, with a receipt", _writes_when_empty_and_stamps_a_receipt),
    ("nothing derived is ever offered to OpenStreetMap", _a_derived_field_is_never_giveable),
    ("an unconfirmed ตำบล is recorded as what was SAID", _unconfirmed_tambon_says_so),
    ("a pin that contradicts the address is flagged", _the_pin_is_a_second_witness),
    ("running it twice changes nothing", _idempotent),
]:
    t(name, fn)


# ------------------------------------------------------ the other readings

def _script_and_honorific():
    r = _rec(name="แม่ศรี ก๋วยเตี๋ยว", nameEn="Mae Si Noodles")
    derive.apply_name_shape([r], "cm")
    assert r["attrs"]["nameScript"] == "both", r["attrs"]
    assert r["attrs"]["nameHonorific"] == "แม่", r["attrs"]


def _an_honorific_must_open_the_name():
    """แม่ริม is a district and แม่น้ำ is a river; neither is somebody's auntie."""
    r = _rec(name="ร้านกาแฟแม่ริม")
    derive.apply_name_shape([r], "cm")
    assert "nameHonorific" not in r["attrs"], r["attrs"]


def _branch_and_company():
    r = _rec(name="บริษัท ยาดี จำกัด สาขา บิ๊กซี เชียงใหม่")
    derive.apply_name_shape([r], "cm")
    assert r["attrs"]["branchName"] == "บิ๊กซี เชียงใหม่", r["attrs"]
    assert r["attrs"]["companyForm"] == "บริษัท", r["attrs"]


def _line_types():
    assert derive.line_type("+66 53 123 456") == "landline-local"
    assert derive.line_type("081-234-5678") == "mobile"
    assert derive.line_type("02 123 4567") == "landline-bangkok"
    assert derive.line_type("+66812345678") == "mobile"
    assert derive.line_type("not a phone") is None


def _front_door():
    fb = _rec(attrs={"facebook": "https://www.facebook.com/x"})
    own = _rec(website="https://example.co.th")
    rented = _rec(website="https://shop.wixsite.com/x")
    derive.apply_contact_shape([fb, own, rented], "cm")
    assert fb["attrs"]["frontDoor"] == "facebook"
    assert own["attrs"]["frontDoor"] == "own-site"
    assert rented["attrs"]["frontDoor"] == "rented"


def _a_chain_needs_three_separate_pins():
    """Three rows at one coordinate are a mess, never a chain of three."""
    same = [_rec(name="ร้านเดียวกัน", lat=18.7, lng=98.9) for _ in range(3)]
    derive.apply_chains(same, "cm")
    assert not any((r["attrs"].get("chainSize")) for r in same), \
        "three records at one pin were branded as a chain"
    spread = [_rec(name="ร้านเดียวกัน", lat=18.7 + i / 10, lng=98.9) for i in range(3)]
    derive.apply_chains(spread, "cm")
    assert all(r["attrs"]["chainSize"] == 3 for r in spread), spread[0]["attrs"]


def _a_name_we_generated_is_not_a_chain():
    made = []
    for i in range(4):
        r = _rec(name="ที่จอดรถ · ย่านแม่ริม", lat=18.9 + i / 10, lng=98.9)
        r["provenance"] = {"name": {"source": "derived:parking-locator", "how": "derived"}}
        made.append(r)
    derive.apply_chains(made, "cm")
    assert not any(r["attrs"].get("brand") for r in made), \
        "a name this repo wrote came back as a brand"


def _a_trade_word_is_not_a_brand():
    shops = [_rec(name="ซักผ้าหยอดเหรียญ", lat=18.7 + i / 10, lng=98.9) for i in range(4)]
    derive.apply_chains(shops, "cm")
    assert not any(r["attrs"].get("brand") for r in shops), \
        "a trade description was branded as a chain"


def _a_host_word_must_be_a_word():
    """Thai has no spaces, so a substring is not a word: วัดสันห้าง is a temple."""
    temple = _rec(name="วัดสันห้าง", lat=18.7, lng=98.9, geoPrecision="exact")
    others = [_rec(name=f"ร้าน {i}", lat=18.7, lng=98.9, geoPrecision="exact")
              for i in range(3)]
    derive.apply_venues([temple] + others, "cm")
    assert not any(r["attrs"].get("insideOf") for r in others), \
        "a temple was made the landlord of three shops"


def _a_real_host_takes_its_tenants():
    mall = _rec(name="ตลาดสดป่าบง", lat=18.7, lng=98.9, geoPrecision="exact")
    tenants = [_rec(name=f"แผง {i}", lat=18.7, lng=98.9, geoPrecision="exact")
               for i in range(3)]
    derive.apply_venues([mall] + tenants, "cm")
    assert all(r["attrs"]["insideOf"] == "ตลาดสดป่าบง" for r in tenants)
    assert "insideOf" not in mall["attrs"], "the host was put inside itself"


def _a_crowded_pin_is_a_geocoder_shrug():
    mall = _rec(name="ตลาดใหญ่", lat=18.7, lng=98.9, geoPrecision="exact")
    crowd = [_rec(name=f"ร้าน {i}", lat=18.7, lng=98.9, geoPrecision="exact")
             for i in range(40)]
    derive.apply_venues([mall] + crowd, "cm")
    assert not any(r["attrs"].get("insideOf") for r in crowd), \
        "forty records on one coordinate were read as a building's tenants"


def _category_agreement_only_reports():
    agree = _rec(sub=["cafe"], attrs={"overtureCategory": "cafe"})
    differ = _rec(sub=["cafe"], attrs={"overtureCategory": "car_wash"})
    derive.apply_category_agreement([agree, differ], "cm")
    assert agree["attrs"]["catAgreement"] == "agree"
    assert differ["attrs"]["catAgreement"] == "differ"
    assert differ["sub"] == ["cafe"], "a disagreement rewrote the shelf"


# ------------------------------------------------------------ pins in doubt

def _ovt(**kw):
    kw.setdefault("confidence", "third-party")
    kw.setdefault("geoPrecision", "exact")
    return _rec(**kw)


def _a_stack_of_strangers_needs_pins():
    shops = [_ovt(id=f"s{i}", name=f"ร้าน {i}", lat=18.767, lng=99.02614,
                  address=f"{i} ถนน สุเทพ") for i in range(6)]
    hand = _rec(id="h", lat=18.767, lng=99.02614, confidence="curated", geoPrecision="exact")
    alone = _ovt(id="a", lat=18.8, lng=98.95)
    n = derive.apply_pin_doubt(shops + [hand, alone], "cm")
    assert n == 6, n
    for r in shops:
        assert r["geoPrecision"] == "needs-pin" and r["lat"] is None, r
        assert r["attrs"]["pinDoubt"] == "stacked:7", r["attrs"]
        assert r["attrs"]["pinWas"] == [18.767, 99.02614], r["attrs"]
    assert hand["lat"] == 18.767, "a pin a person placed was moved"
    assert alone["geoPrecision"] == "exact", "a pin on its own was flagged"
    assert derive.apply_pin_doubt(shops + [hand, alone], "cm") == 0, "a second run wrote again"


def _four_at_one_pin_is_not_a_stack():
    four = [_ovt(id=f"f{i}", lat=18.7, lng=98.9) for i in range(4)]
    assert derive.apply_pin_doubt(four, "cm") == 0


def _one_buildings_address_leaves_the_stack():
    mall = [_ovt(id=f"m{i}", name=f"ร้าน {i}", lat=19.88628, lng=99.83303,
                 address="ชั้น 2 ศูนย์การค้าเซ็นทรัล เชียงราย") for i in range(6)]
    assert derive.apply_pin_doubt(mall, "cr") == 0
    assert all(r["geoPrecision"] == "exact" for r in mall)


def _approx_tenants_do_not_make_a_stack():
    """Tenants pinned to their building are approx; the host's own pin stands."""
    host = _rec(id="host", name="Antique Market", lat=18.80936, lng=98.9958,
                confidence="crawled", geoPrecision="exact")
    tenants = [_ovt(id=f"t{i}", lat=18.80936, lng=98.9958, geoPrecision="approx")
               for i in range(20)]
    assert derive.apply_pin_doubt([host] + tenants, "cm") == 0


def _a_name_from_the_other_province():
    white = _ovt(name="Chiang Rai White Temple", cat=["wat"], lat=18.78646, lng=98.99251)
    tri = _ovt(name="The Golden Triangle- Tri Border of Thailand, Burma and Laos",
               cat=["sights"], lat=18.78646, lng=98.99252)
    sriphat = _ovt(name="รพ.ศรีพัฒน์  เชียงใหม่", cat=["medical"], lat=19.9, lng=99.83)
    derive.apply_pin_doubt([white, tri], "cm")
    derive.apply_pin_doubt([sriphat], "cr")
    for r in (white, tri, sriphat):
        assert r["attrs"].get("pinDoubt") == "name-other-province", (r["name"], r["attrs"])


def _a_borrowed_name_keeps_its_pin():
    kept = [
        _ovt(name="สุกี้ สาขาเซ็นทรัลเชียงราย"),                       # a branch
        _ovt(name="ถนนเชียงใหม่-เชียงราย"),                            # both provinces
        _ovt(name="ร้านน้ำเงี้ยวบุษบา เจ้าเก่าเชียงราย หน้ากองบิน 41"),   # a dish style
        _ovt(name="Golden Triangle Motorcycle Club", cat=["whats-on"]),  # a landmark, off a sight shelf
        _ovt(name="Ratchiangsaen Flora House", cat=["sights"]),          # a road
        _rec(name="Khao Soy Mae Sai Chiang Rai", confidence="crawled"),  # an OSM node
    ]
    for i, r in enumerate(kept):   # apart, so they are not read as a stack
        r.update(lat=18.79 + i / 1000, lng=98.99, geoPrecision=r.get("geoPrecision") or "exact")
    derive.apply_pin_doubt(kept, "cm")
    flagged = [r["name"] for r in kept if r["attrs"].get("pinDoubt")]
    assert not flagged, flagged
    village = _ovt(name="วัดสันเชียงใหม่", lat=19.9, lng=99.83)
    derive.apply_pin_doubt([village], "cr")
    assert not village["attrs"].get("pinDoubt"), village["attrs"]


def _a_pin_in_the_other_province():
    """Filed cm, pinned at Wat Rong Khun in Chiang Rai (COD-AB polygons on disk)."""
    r = _ovt(name="ร้านหนึ่ง", lat=19.8243, lng=99.7633)
    derive.apply_pin_doubt([r], "cm")
    assert r["attrs"].get("pinDoubt") == "other-province", r["attrs"]


EXTRA = [
    ("a stack of strangers at one pin needs pins", _a_stack_of_strangers_needs_pins),
    ("four at one pin is not a stack", _four_at_one_pin_is_not_a_stack),
    ("one building's address leaves the stack standing", _one_buildings_address_leaves_the_stack),
    ("approx tenants on a host's pin do not make a stack", _approx_tenants_do_not_make_a_stack),
    ("a name from the other province needs a pin", _a_name_from_the_other_province),
    ("a borrowed name keeps its pin", _a_borrowed_name_keeps_its_pin),
    ("a pin in the other province needs a pin", _a_pin_in_the_other_province),
    ("the script of a name, and an honorific in front of it", _script_and_honorific),
    ("an honorific must open the name, not sit inside it", _an_honorific_must_open_the_name),
    ("สาขา gives up the branch, and the company form", _branch_and_company),
    ("a phone prefix says what kind of line it is", _line_types),
    ("the front door is the one a reader would land on", _front_door),
    ("a chain needs three separate pins, not three rows", _a_chain_needs_three_separate_pins),
    ("a name this repo generated is never a brand", _a_name_we_generated_is_not_a_chain),
    ("a trade word shared by fifty shops is not a brand", _a_trade_word_is_not_a_brand),
    ("a host word must be a word — วัดสันห้าง is not a mall", _a_host_word_must_be_a_word),
    ("a real host takes its tenants, and is not inside itself", _a_real_host_takes_its_tenants),
    ("forty records on one coordinate is a geocoder, not a venue", _a_crowded_pin_is_a_geocoder_shrug),
    ("a category disagreement is reported, never acted on", _category_agreement_only_reports),
]
for name, fn in EXTRA:
    t(name, fn)

print(f"\n{len(FAILS)} failed" if FAILS else "\nall green")
sys.exit(1 if FAILS else 0)
