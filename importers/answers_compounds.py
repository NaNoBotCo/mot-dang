#!/usr/bin/env python3
"""answers_compounds.py — a ready answer for every compound a reader might type into motdang.net/find.

Nan, 2026-10-04: "retatrutide" found nothing and "retatrutide buy" found Power Buy. Systemic and
planned: a lexicon of listed medicines and popular compounds (data/curated/compounds.json), each
looked up on Thailand's drug register (importers/fda_register.py → data/curated/fda_register.json),
turned here into one answer card in the shape publish/fleetsearch.js reads:

    what it is · whether Thailand registers it, and the legal class that decides who may sell it ·
    how people get it here in practice (by class) · cost where a page states it · the registered
    alternative when it is unregistered · Mot Dang pages · a quiet Defiant line.

Writes data/curated/answers_compounds.json. Publish with the care answers (on her word):
    cp data/curated/answers_compounds.json docs/data/answers-compounds.json
    python3 publish/deploy.py --files data/answers-compounds.json --yes
New compounds: add a row to compounds.json (notes/compound-gaps.txt lists the searches that missed),
run fda_register.py <id>, then this.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEX = ROOT / "data" / "curated" / "compounds.json"
REG = ROOT / "data" / "curated" / "fda_register.json"
ADHD = ROOT / "data" / "curated" / "adhd.json"
HEALTH = ROOT / "data" / "curated" / "answers_health.json"
OUT = ROOT / "data" / "curated" / "answers_compounds.json"
MD = "https://motdang.net"
D = "https://defiant.to"
FDA_SEARCH = ["https://pertento.fda.moph.go.th/FDA_SEARCH_DRUG/SEARCH_DRUG/FRM_SEARCH_DRUG.aspx", "Thai FDA drug register search"]
FDA_TRAVEL = ["https://permitfortraveler.fda.moph.go.th/nct_permit_main/Main/FRM_checkdrug_index", "Thai FDA traveller drug check"]
CHECKMD = ["https://checkmd.tmc.or.th", "Medical Council doctor licence check"]

PAGE = {
    "care": {"th": "ดูแลต่อเนื่อง", "en": "Ongoing care", "u": MD + "/care.html"},
    "medical": {"th": "หมวดการแพทย์", "en": "Medical shelf", "u": MD + "/cm/medical/"},
    "women": {"th": "สุขภาพผู้หญิง", "en": "Women's health", "u": MD + "/womens-health.html"},
    "trans": {"th": "สุขภาพคนข้ามเพศ", "en": "Trans health", "u": MD + "/trans-health.html"},
    "skin": {"th": "ผิวหนัง", "en": "Skin", "u": MD + "/skin.html"},
    "adhd": {"th": "สมาธิสั้น", "en": "ADHD", "u": MD + "/adhd.html"},
    "airport": {"th": "ยาที่สนามบิน", "en": "Medicine at the airport", "u": MD + "/medicine-airport.html"},
    "counsel": {"th": "ปรึกษาจิตใจ", "en": "Counselling", "u": MD + "/counselling.html"},
}

# class → the pages, the Defiant page, and how a compound of this kind is got and checked here
CLASS = {
    "glp1": dict(go=["care"], d="/biologics/", dl=("Biologics, priced", "ราคายาชีววัตถุ"),
        how=("Weight-loss and endocrine clinics in Chiang Mai prescribe the registered ones and set the dose; prices differ clinic to clinic.",
             "คลินิกลดน้ำหนักและคลินิกต่อมไร้ท่อในเชียงใหม่สั่งจ่ายตัวที่ขึ้นทะเบียนและกำหนดขนาด ราคาแต่ละที่ต่างกัน"),
        vet=None,
        unreg=("What sells here under this name comes as research vials, through clinics and online. Tirzepatide (Mounjaro) and semaglutide (Ozempic, Wegovy) are registered.",
               "ที่ขายในชื่อนี้คือขวดสำหรับงานวิจัย ผ่านคลินิกและออนไลน์ เทอร์เซพาไทด์ (Mounjaro) และเซมากลูไทด์ (Ozempic, Wegovy) ขึ้นทะเบียนแล้ว"),
        src=[]),
    "peptide": dict(go=["care"], d="/procedures/peptide-injections/", dl=("Peptides, priced", "ราคาเปปไทด์"),
        how=("Longevity and aesthetic clinics in Chiang Mai, and some pharmacies, sell it; a physician-started cycle runs about $100–500.",
             "คลินิกชะลอวัยและคลินิกความงามในเชียงใหม่ และร้านขายยาบางร้าน มีขาย คอร์สที่หมอเริ่มให้ราว 100–500 ดอลลาร์"),
        vet=None, src=[[D + "/procedures/peptide-injections/", "defiant.to, peptide injections"]]),
    "gh": dict(go=["care"], d="/longevity/", dl=("Longevity in Thailand", "ชะลอวัยในไทย"),
        how=("Endocrinologists prescribe the registered pens; longevity clinics offer it too.",
             "แพทย์ต่อมไร้ท่อสั่งจ่ายปากกาที่ขึ้นทะเบียน คลินิกชะลอวัยก็มี"), vet=None, src=[]),
    "sarm": dict(go=["care"], d="/longevity/", dl=("Longevity in Thailand", "ชะลอวัยในไทย"),
        how=("Sold as research chemicals online and around gyms; no country registers it as a medicine.",
             "ขายเป็นสารเคมีเพื่อการวิจัย ทางออนไลน์และตามยิม ไม่มีประเทศใดขึ้นทะเบียนเป็นยา"),
        vet=None, src=[]),
    "aas": dict(go=["care"], d="/longevity/", dl=("Longevity in Thailand", "ชะลอวัยในไทย"),
        how=("Many Thai pharmacies sell it behind the counter, by generic name, and small shops order what they lack. Hospital urology and endocrine clinics and men's-health clinics prescribe it with blood work.",
             "ร้านขายยาหลายร้านขายหลังเคาน์เตอร์ตามชื่อสามัญ ร้านเล็กสั่งของที่ไม่มีให้ได้ คลินิกระบบปัสสาวะและต่อมไร้ท่อของโรงพยาบาล และคลินิกสุขภาพชาย สั่งจ่ายพร้อมตรวจเลือด"),
        vet=None, src=[["field", "Chiang Mai field report, 2026"]]),
    "ancillary": dict(go=["care"], d="/longevity/", dl=("Longevity in Thailand", "ชะลอวัยในไทย"),
        how=("Pharmacies carry the registered ones.", "ร้านขายยามีตัวที่ขึ้นทะเบียน"), vet=None, src=[]),
    "hrt": dict(go=["women"], d="/estradiol/", dl=("Estradiol: what to ask for", "เอสตราไดออล: ขออะไรดี"),
        how=("The Thai brands: vaginal estrogen cream is Ovestin (estriol), whole-body estradiol gel is Oestrogel. OB-GYNs (สูตินรีแพทย์) at hospital women's centres and evening clinics prescribe and monitor.",
             "ชื่อยี่ห้อในไทย ครีมเอสโตรเจนช่องคลอดคือ Ovestin (เอสไตรออล) เจลเอสตราไดออลทั้งตัวคือ Oestrogel สูตินรีแพทย์ที่ศูนย์สุขภาพสตรีและคลินิกเย็นสั่งจ่ายและติดตามผล"),
        vet=None, src=[[D + "/estradiol/", "defiant.to, estradiol in Thailand"]]),
    "trans": dict(go=["trans"], d="/estradiol/", dl=("Hormones on Thai shelves", "ฮอร์โมนบนชั้นยาไทย"),
        how=("Sriphat (Chiang Mai University) runs a clinic for gender-diverse people; Mplus in Chiang Mai and Chiang Rai test hormone levels.",
             "ศรีพัฒน์ (มช.) มีคลินิกสำหรับผู้มีความหลากหลายทางเพศ เอ็มพลัสเชียงใหม่และเชียงรายตรวจระดับฮอร์โมน"),
        vet=None, src=[["https://sriphat.med.cmu.ac.th/th/knowledge-381", "Sriphat, gender-diverse clinic"]]),
    "ed": dict(go=["care"], d="/pelvic/", dl=("Pelvic health", "อุ้งเชิงกราน"),
        how=("Generic sildenafil is the cheap local standard; branded tadalafil costs far more here than in India.",
             "ซิลเดนาฟิลชื่อสามัญราคาถูกที่สุด ทาดาลาฟิลยี่ห้อดังที่นี่แพงกว่าอินเดียมาก"), vet=None, src=[["field", "Chiang Mai field report, Feb 2026"]]),
    "hair": dict(go=["skin"], d="/glowup/", dl=("The glow-up menu", "เมนูความงาม"),
        how=("Dermatology clinics prescribe it and pharmacies stock the registered forms.",
             "คลินิกผิวหนังสั่งจ่าย ร้านขายยามีรูปแบบที่ขึ้นทะเบียน"), vet=None, src=[]),
    "longevity": dict(go=["care"], d="/longevity/", dl=("Longevity in Thailand", "ชะลอวัยในไทย"),
        how=("Longevity clinics in Chiang Mai offer it; registered drugs among these are also at pharmacies.",
             "คลินิกชะลอวัยในเชียงใหม่มีให้ ตัวที่เป็นยาขึ้นทะเบียนก็มีที่ร้านขายยา"),
        vet=None, src=[]),
    "nootropic": dict(go=["counsel"], d="/brain/", dl=("Brain treatments", "รักษาด้วยการกระตุ้นสมอง"), how=None, vet=None, src=[]),
    "stimulant": dict(go=["adhd", "airport"], d="/flying-with-meds/", dl=("Flying with meds", "พกยาบิน"), how=None, vet=None, src=[FDA_TRAVEL]),
    "sleep": dict(go=["airport", "counsel"], d="/flying-with-meds/", dl=("Flying with meds", "พกยาบิน"),
        how=("Many of these are controlled in Thailand: a doctor prescribes them, and bringing them in can need an FDA permit; the FDA traveller list gives each substance's category.",
             "ยาหลายตัวในกลุ่มนี้เป็นยาควบคุมในไทย หมอเป็นผู้สั่ง และการนำเข้าอาจต้องขอใบอนุญาต อย. รายการของ อย. สำหรับผู้เดินทางบอกประเภทของแต่ละสาร"),
        vet=None, src=[FDA_TRAVEL]),
    "biologic": dict(go=["skin"], d="/biologics/", dl=("Biologics, priced", "ราคายาชีววัตถุ"),
        how=("A dermatologist or specialist confirms the diagnosis and gives the injection; clinics publish per-injection prices far below US cash prices.",
             "แพทย์ผิวหนังหรือแพทย์เฉพาะทางยืนยันการวินิจฉัยและฉีดให้ คลินิกติดราคาต่อเข็มต่ำกว่าราคาเงินสดอเมริกามาก"),
        vet=None, src=[[D + "/biologics/", "defiant.to, biologics"]]),
    "derm": dict(go=["skin"], d="/glowup/", dl=("The glow-up menu", "เมนูความงาม"),
        how=("Dermatology and aesthetic clinics offer it.", "คลินิกผิวหนังและคลินิกความงามมีให้"), vet=None, src=[]),
    "common": dict(go=["medical"], d="/articles/pharmacies-chiang-mai/", dl=("Pharmacies in Chiang Mai", "ร้านขายยาในเชียงใหม่"),
        how=("Thai boxes carry the generic name or a Thai brand rather than the US brand; the 24-hour counters are inside the private hospitals.",
             "กล่องยาไทยใช้ชื่อสามัญหรือชื่อยี่ห้อไทย ไม่ใช่ชื่อยี่ห้ออเมริกา ห้องยา 24 ชั่วโมงอยู่ในโรงพยาบาลเอกชน"), vet=None,
        src=[[D + "/articles/pharmacies-chiang-mai/", "defiant.to, pharmacies"]]),
    "herb": dict(go=["medical"], d="/articles/pharmacies-chiang-mai/", dl=("Pharmacies in Chiang Mai", "ร้านขายยาในเชียงใหม่"), how=None, vet=None, src=[]),
}

# one-off facts a template cannot know, each with its source
NOTE = {
    "retatrutide": ("No country has approved it; Eli Lilly plans to file with the US FDA in early 2027 after phase 3 trials.",
                    "ยังไม่มีประเทศใดอนุมัติ Eli Lilly วางแผนยื่นต่อ FDA สหรัฐฯ ต้นปี 2570 หลังงานวิจัยระยะที่ 3",
                    ["https://www.drugs.com/history/retatrutide", "drugs.com, retatrutide status"]),
    "tirzepatide": ("Mounjaro launched in Thailand at the end of May 2025, in 2.5 to 10 mg pens.",
                    "Mounjaro เปิดตัวในไทยปลายพฤษภาคม 2568 มีปากกา 2.5 ถึง 10 มก.",
                    ["https://zuelligpharma.com/news-insights/Zuellig-Pharma-Launches-Lillys-Innovative-Obesity-and-Diabetes-Medicine-in-Thailand", "Zuellig Pharma, Mounjaro launch"]),
    "tildrakizumab": ("A Chiang Mai dermatology clinic publishes Ilumya at ฿42,000 an injection, against about $17,552 at the US cash price.",
                      "คลินิกผิวหนังในเชียงใหม่ติดราคา Ilumya เข็มละ 42,000 บาท ที่อเมริการาว 17,552 ดอลลาร์",
                      ["https://www.crystalclinic.net/service/psoriasis/", "Crystal Clinic price list"]),
    "kratom": ("Thailand took kratom off the narcotics list in August 2021; leaves and brewed drinks sell openly, though not to anyone under 18 or to pregnant or nursing women.",
               "ไทยถอดกระท่อมออกจากยาเสพติดเมื่อสิงหาคม 2564 ใบและน้ำต้มขายได้อย่างเปิดเผย แต่ห้ามขายให้ผู้อายุต่ำกว่า 18 ปี หญิงตั้งครรภ์ และหญิงให้นมบุตร",
               ["https://en.wikipedia.org/wiki/Mitragyna_speciosa", "Wikipedia: Mitragyna speciosa (legal status)"]),
    "pseudoephedrine": ("Thai pharmacies refuse it over the counter and offer loratadine instead.",
                        "ร้านขายยาไทยไม่ขายหน้าร้าน จะได้ลอราทาดีนแทน", ["field", "Chiang Mai field report, Feb 2026"]),
}

# aliases too short or too common to stand alone as a search word
WEAK = {"test", "var", "eq", "gw", "fin", "nr", "t3", "mast", "primo", "diane", "depo", "prep", "nad", "ta1",
        "sema", "tirz", "reta", "cagri", "spiro", "caber", "adex", "nolva", "deca", "tren", "trt", "txa", "gluta",
        "z-pack", "plan b", "dbol"}
EXTRA = {"emtricitabine/tenofovir": ["prep hiv", "prep clinic", "prep pill", "เพร็พ"],
         "testosterone": ["testosterone injection", "test e", "test c", "trt clinic"],
         "trenbolone": ["tren ace"], "nandrolone": ["deca durabolin"], "retatrutide": ["reta peptide"],
         "semaglutide": ["sema peptide"], "tirzepatide": ["tirz peptide"]}


DISPLAY = {"ghk-cu": "GHK-Cu", "nad+": "NAD+", "nmn": "NMN", "hcg": "hCG", "dhea": "DHEA", "mots-c": "MOTS-c",
           "5-amino-1mq": "5-Amino-1MQ", "emtricitabine/tenofovir": "Emtricitabine/tenofovir (PrEP)",
           "melanotan ii": "Melanotan II", "kpv": "KPV", "sr9009": "SR9009"}


def title(cid):
    if cid in DISPLAY:
        return DISPLAY[cid]
    return cid.upper() if re.search(r"\d", cid) else cid[:1].upper() + cid[1:]


def register_lines(cid, r, adhd):
    """(en, th) sentences from the register row and, for stimulants, the narcotics schedule."""
    en, th = [], []
    mol = adhd.get(cid)
    if mol:
        en.append(f"Thai law: {mol['class_en']}. {mol['carry_en']}")
        th.append(f"กฎหมายไทย: {mol['class_th']} {mol['carry_th']}")
        return en, th
    if not r or r.get("total") is None:
        return en, th
    n = r["total"]
    if n == 0 and cls_of.get(cid) in ("sleep", "stimulant", "biologic", "nootropic"):
        # the public search leaves out psychotropics and some new biologics: no hit there is not "unregistered"
        return en, th
    if n == 0:
        en.append(f"It is not on Thailand's drug register (Thai FDA search, {REG_DATE}).")
        th.append(f"ไม่มีในทะเบียนยาของไทย (ค้นที่ อย. {REG_DATE})")
        return en, th
    brands = ", ".join([x.upper() for x in (brand_word(b) for b in r.get("brands_en", [])) if x][:3])
    en.append(f"Thailand's drug register lists {n} product{'s' if n != 1 else ''}" + (f", among them {brands}." if brands else "."))
    th.append(f"ทะเบียนยาไทยมี {n} รายการ" + (f" เช่น {brands}" if brands else ""))
    cls = set(r.get("class", []))
    if "special" in cls and "dangerous" in cls:  # stylecheck: allow — register class keys
        en.append("Some are pharmacist-dispensed (ยาอันตราย), sold without a prescription; others are specially controlled (ยาควบคุมพิเศษ) and need a doctor's.")
        th.append("บางรายการเป็นยาอันตราย เภสัชกรขายได้โดยไม่ต้องมีใบสั่งแพทย์ บางรายการเป็นยาควบคุมพิเศษ ต้องมีใบสั่งแพทย์")
    elif "special" in cls:
        en.append("Legal class: specially controlled (ยาควบคุมพิเศษ), sold on a doctor's prescription at hospital and clinic pharmacies.")
        th.append("ประเภทยาควบคุมพิเศษ ต้องมีใบสั่งแพทย์ ห้องยาโรงพยาบาลและคลินิกจ่ายให้")
    elif "dangerous" in cls:  # stylecheck: allow — register class keys
        en.append("Legal class: pharmacist-dispensed (ยาอันตราย), sold without a prescription.")
        th.append("ประเภทยาอันตราย เภสัชกรขายให้ได้โดยไม่ต้องมีใบสั่งแพทย์")
    elif cls & {"household", "packaged"}:
        en.append("It sits on open shelves.")
        th.append("วางขายบนชั้นทั่วไป")
    return en, th


REG_DATE = ""
cls_of = {}


# a brand as a search word: no strength, form or pack words; long enough not to be a name
_FORM = re.compile(r"\(.*?\)|\[.*?\]|\b\d[\d.,/]*\s*(mg|mcg|ug|g|ml|iu|units?|%)?\b|\b(tablets?|tab|capsules?|cap|"
                   r"injection|inj|syrup|suspension|solution|cream|soft|dry|oral|film-coated|extended-release|usp|"
                   r"forte|plus|xr|sr|pr|tm|r)\b\.?|[™®\"]|ชนิดเม็ด|มิลลิกรัม", re.I)
NAMES = {"sasha", "anzac", "zonia", "rita", "zoric", "trazen", "modil", "tadol", "nestol", "lozol", "puride", "sertra",
         "uroka", "zetron", "startec", "keratyl", "suplac", "donhon", "maforan", "silatio", "persa tina"}


def brand_word(b):
    w = re.sub(r"\s+", " ", _FORM.sub(" ", b)).strip(" -.,(").lower()
    if len(w.replace(" ", "")) < 6 or w in NAMES or len(w.split()) > 2:
        return ""
    return w


def fold_name(s):
    return re.sub(r"[^a-z0-9\u0e00-\u0e7f]+", "", (s or "").lower())


def main():
    global REG_DATE
    lex = json.loads(LEX.read_text(encoding="utf-8"))["compounds"]
    regd = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {"rows": {}, "fetched": ""}
    REG_DATE = regd.get("fetched", "")
    reg = regd.get("rows", {})
    adhd = {}
    if ADHD.exists():
        for m in json.loads(ADHD.read_text(encoding="utf-8")).get("molecules", []):
            for k in [m["key"]] + [x.strip().lower() for x in m["generic_en"].split("·")]:
                adhd[k] = m
    desk = json.loads(HEALTH.read_text(encoding="utf-8"))["desk"]
    cls_of.update({c["id"]: c["class"] for c in lex})
    out = []
    for c in lex:
        cid, k = c["id"], CLASS[c["class"]]
        r = reg.get(cid)
        # a research compound the register "finds" only inside other products' names is a
        # substring collision (bpc → Fisherman's Friend): read it as unregistered
        if r and r.get("total") and c["class"] in ("peptide", "sarm"):
            keys = [fold_name(x) for x in [cid] + c["aliases"]]
            brands = [fold_name(x) for x in r.get("brands_en", []) + r.get("brands_th", [])]
            if not any(k and k in b for k in keys for b in brands):
                r = {**r, "total": 0, "brands_en": [], "brands_th": [], "class": [], "collided": True}
        name = title(cid)
        en = [f"{name}: {c['what_en']}."]
        th = [f"{name}: {c['what_th']}"]
        ren, rth = register_lines(cid, r, adhd)
        en += ren
        th += rth
        if cid in NOTE:
            en.append(NOTE[cid][0])
            th.append(NOTE[cid][1])
        unreg = r is not None and r.get("total") == 0 and c["class"] not in ("sleep", "stimulant", "biologic", "nootropic")
        if unreg and k.get("unreg"):
            en.append(k["unreg"][0])
            th.append(k["unreg"][1])
        elif k.get("how"):
            en.append(k["how"][0])
            th.append(k["how"][1])
        if k.get("vet"):
            en.append(k["vet"][0])
            th.append(k["vet"][1])
        src = []
        if cid in NOTE and NOTE[cid][2]:
            src.append(NOTE[cid][2])
        if r and r.get("total") is not None:
            src.append(FDA_SEARCH)
        src += k.get("src", [])
        names = [cid] + [a for a in c["aliases"] if a.lower() not in WEAK] + EXTRA.get(cid, [])
        if "-" in cid:
            names.append(cid.replace("-", " "))
            names.append(cid.replace("-", ""))
        if r:
            names += [x for x in (brand_word(b) for b in r.get("brands_en", [])) if x]
            names += [x for x in (brand_word(b) for b in r.get("brands_th", [])) if x]
        seen, w = set(), []
        for x in names:
            x = x.strip().lower()
            if x and x not in seen:
                seen.add(x)
                w.append(x)
        out.append({"id": "c-" + re.sub(r"[^a-z0-9]+", "-", cid), "en": name, "th": name,
                    "a_en": " ".join(en), "a_th": " ".join(th), "src": src,
                    "go": [PAGE[g] for g in k["go"]], "desk": True,
                    "d": D + k["d"], "d_th": D + k["d"], "d_label_en": k["dl"][0], "d_label_th": k["dl"][1],
                    "w": w, "cls": c["class"]})
    doc = {"read": REG_DATE, "general": None, "cls": "health", "fuzzy": True, "desk": desk,
           "source_note": "data/curated/compounds.json + Thai FDA drug register (importers/fda_register.py)",
           "answers": out}
    head = json.dumps({x: v for x, v in doc.items() if x != "answers"}, ensure_ascii=False)[:-1]
    for a in out:
        a["_"] = "stylecheck: allow — w is the readers' search words"
    body = ",\n".join(json.dumps(a, ensure_ascii=False) for a in out)
    OUT.write_text(f'{head}, "answers": [\n{body}\n]}}\n', encoding="utf-8")
    print(f"answers_compounds: {len(out)} -> {OUT.relative_to(ROOT)}  (register read {REG_DATE})")


if __name__ == "__main__":
    main()
