#!/usr/bin/env python3
"""เสริมสวย-ตัดผม — the word for what you want, the shops, and what nobody
has asked them yet.

Four things a person asks about hair in this town, in the order they ask them,
on one page (/beauty.html):

  1. HOW DO I ASK FOR IT — the words. This is the whole reason the page exists.
     A digital perm is ดัดดิจิตอล and a fade is ตัดเฟด and cornrows are ถักเปีย
     and coming to your hotel is ไปทำถึงที่ — and a person who cannot say the
     word does not get the haircut, however many shops the directory lists.
     Thai script, RTGS, tone, and the root where the root explains the word.
  2. WHICH SHOPS — the barber shelf (which held 6 of the city's 62 until this
     build), the salon shelf (which held NONE of 62), the one braiding shop,
     and who each shop states it cuts for.
  3. WHAT NOBODY HAS ASKED THEM — the honest census. Across all 18,686 records
     in both provinces, ZERO shopfronts say perm, updo, afro, textured or house
     call. That is a measurement, not a shrug: those five are door questions,
     they are the `beauty` facet set in data/facets.json, and this page prints
     the count every build so the hole cannot be quietly forgotten.
  4. THE REGISTER — what shops state about their own services, once anybody
     has read them. Empty today and saying so, with the 18-shop read queue the
     records themselves generate.

WHAT THIS PAGE REFUSES TO DO. It does not sort barbers into the hip ones and
the ordinary ones, the farang ones and the Thai ones. Sixty-two shops put
BARBER on the sign — Sweeney Todds and สุเทพบาร์เบอร์ and Rebel House and
ปุ๊ บาร์เบอร์ — and they are listed together, alphabetically, unranked, exactly
as the elephant camps are. A reader can read a sign as well as we can. What a
chair is like is a door question and always was; who a shop is "for" is not
the directory's to say.

And it does not guess at textured hair. Not one shop in either province has
stated it works with tightly coiled hair. The page says that in those words,
gives the sentence to ask in Thai, and leaves the answer blank — because a
wrong yes sends somebody with 4c hair to a chair where nobody has handled it
before, and that is a worse outcome than an honest "we don't know yet".

Entry point: emit(globals_of_build, data) — hooked in build.py after the
cooking layer. Emits beauty.html + beauty.css; prints the counts.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "curated" / "beauty.json"
sys.path.insert(0, str(ROOT / "importers"))
import audit_beauty  # noqa: E402  (zero network; the เปีย stray guard)

CSS = """
.bt-intro{font-size:1.02rem;max-width:46rem}
.bt-rule{margin:.8rem 0 1rem;padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07);font-size:.98rem}
.bt-rule b{display:block;margin-bottom:.15rem}
.bt-words{width:100%;border-collapse:collapse;margin:.6rem 0 1rem;font-size:.95rem}
.bt-words th,.bt-words td{padding:.45rem .4rem;border-bottom:1px solid rgba(0,0,0,.08);
  text-align:left;vertical-align:top}
.bt-words th{font-size:.85rem;color:var(--mute);font-weight:600}
.bt-words .th{font-size:1.12rem;white-space:nowrap}
.bt-words .rtgs{color:var(--mute);font-style:italic;white-space:nowrap;font-size:.88rem}
.bt-words .root{color:var(--mute);font-size:.85rem}
.bt-words tr:hover{background:var(--soft)}
.bt-say{margin:.5rem 0 1.2rem;padding:.7rem .9rem;border-radius:.8rem;
  border:1px dashed rgba(0,0,0,.18);background:var(--soft)}
.bt-say .line{font-size:1.14rem;margin:.15rem 0}
.bt-say .gloss{color:var(--mute);font-size:.9rem;margin:0 0 .5rem}
.bt-gap{margin:.8rem 0 1rem;padding:.75rem .9rem;border-radius:.8rem;
  border:1px solid var(--ant-dark);background:var(--soft)}
.bt-gap b{display:block;margin-bottom:.2rem}
.bt-gap .n{font-size:1.5rem;font-weight:700;color:var(--ant-dark)}
.bt-list{columns:2;column-gap:1.4rem;margin:.5rem 0 1rem;font-size:.95rem}
@media(max-width:640px){.bt-list{columns:1}}
.bt-list div{break-inside:avoid;padding:.16rem 0}
.bt-list a{text-decoration:none;color:inherit}
.bt-list a:hover{text-decoration:underline}
.bt-list small{color:var(--mute);font-size:.82rem}
.bt-count{color:var(--mute);font-weight:400;font-size:.9rem}
.bt-note{color:var(--mute);font-size:.9rem;margin:.3rem 0 1rem}
.bt-q{margin:.4rem 0 1rem;padding-left:1rem;border-left:3px solid var(--ant-dark)}
.bt-q p{margin:.2rem 0}
.bt-queue{font-size:.93rem;margin:.4rem 0 1rem}
.bt-queue li{margin:.18rem 0}
.bt-shops{display:grid;gap:.7rem;margin:.6rem 0 1rem}
.bt-shop{padding:.7rem .9rem;border-radius:.8rem;background:var(--soft);
  border:1px solid rgba(0,0,0,.07)}
.bt-shop h3{margin:0 0 .3rem;font-size:1.05rem}
.bt-shop ul{margin:.2rem 0 .4rem;padding-left:1.1rem}
.bt-shop li{margin:.22rem 0}
.bt-shop .ev{color:var(--mute);font-size:.85rem;font-style:italic}
.bt-sheet{display:inline-block;padding:.45rem .8rem;border-radius:.7rem;
  border:1px solid var(--ant-dark);text-decoration:none;font-weight:600}
"""

# --- the words -------------------------------------------------------------
# Thai, RTGS, tone, and the root ONLY where the root explains the word. A gloss
# that just re-states the English is left off: "ดัด = perm" teaches nothing,
# "ดัด = to bend" teaches why a Thai speaker calls it that. Tones are on the
# spoken syllables as a learner needs them, not as a dictionary lists them.
WORDS = [
    ("ตัดผม", "tat phom", "tàt phǒm", "cut hair", "ตัด to cut + ผม head-hair",
     "The plain haircut. Every shop understands it."),
    ("ตัดผมชาย", "tat phom chai", "tàt phǒm chaai", "men's haircut", "+ ชาย male",
     "What sixteen shopfronts in this catalogue say instead of BARBER."),
    ("บาร์เบอร์", "baboe", "baa-bêu", "barber", "English, borrowed whole",
     "On 46 signs here. A shop using this word is usually clippers, a razor and a mirror."),
    ("ตัดเฟด", "tat fet", "tàt fèet", "fade", "English fade, borrowed",
     "Ask for สกินเฟด sa-kin-fèet if you want it to skin."),
    ("โกนหนวด", "kon nuat", "koon nùat", "shave (the moustache/beard)", "โกน to shave",
     "โกนหน้า koon nâa is a face shave — the hot towel and the folding razor."),
    ("กันขอบ", "kan khop", "gan khɔ̀ɔp", "line up / edge up", "กัน to fence off + ขอบ edge",
     "The tidy-up between cuts. Cheap, quick, and the thing to ask for at two weeks."),
    ("สระไดร์", "sa dai", "sà dai", "wash and blow-dry", "สระ to wash hair + English dry",
     "The commonest transaction in a Thai salon. Often under ฿150."),
    ("ดัดผม", "dat phom", "dàt phǒm", "perm", "ดัด to bend",
     "The general word. On its own it may get you a cold perm."),
    ("ดัดดิจิตอล", "dat dichithan", "dàt dì-jì-tôn", "digital perm", "+ English digital",
     "The heated-rod perm. Say this exact word — ดัดผม alone will not get it."),
    ("ดัดวอลลุ่ม", "dat wonlum", "dàt wɔn-lûm", "volume perm (roots only)", "+ English volume",
     "Roots lifted, lengths left. A different price and a different machine."),
    ("ยืดผม", "yuet phom", "yʉ̂ʉt phǒm", "straighten", "ยืด to stretch",
     "รีบอนดิ้ง rii-bɔɔn-dîng is the rebonding system by name."),
    ("ทำสี", "tham si", "tham sǐi", "colour", "ทำ to do + สี colour",
     "ไฮไลท์ hai-lái for highlights; ฟอกผม fɔ̂ɔk phǒm is to bleach."),
    ("เกล้าผม", "klao phom", "glâo phǒm", "put hair up / updo", "เกล้า to bind up on the head",
     "The word for a wedding, a งาน, a graduation. An old word, not a salon coinage."),
    ("ต่อผม", "to phom", "tɔ̀ɔ phǒm", "hair extensions", "ต่อ to join on, to extend",
     "Ask ผมแท้หรือผมเทียม phǒm-thɛ́ɛ rʉ̌ʉ phǒm-thiam — real hair or synthetic."),
    ("ถักเปีย", "thak pia", "thàk pia", "braid / plait", "ถัก to plait + เปีย a braid",
     "ถักเปียแถว thàk pia thɛ̌ɛo is cornrows — literally 'braided in rows'."),
    ("เดรดล็อค", "dret lok", "drèet-lɔ́k", "dreadlocks / locs", "English, borrowed",
     "Also just เดรด. The one shop in this catalogue that says it is in Chiang Mai."),
    ("ผมหยิก", "phom yik", "phǒm yìk", "curly hair", "หยิก to curl, to pinch",
     "ผมหยิกฝอย phǒm yìk fɔ̌ɔi — tightly coiled hair. ฝอย = fine strands, as of a scouring pad."),
    ("ทรีตเมนต์", "tritmen", "trìit-men", "treatment", "English, borrowed",
     "สปาผม sa-paa phǒm is a hair spa; อบไอน้ำ òp ai-náam is the steam cap."),
    ("ต่อขนตา", "to khon ta", "tɔ̀ɔ khǒn taa", "eyelash extensions", "ต่อ to join + ขนตา lash",
     "Its own trade here, often in the same room as nails."),
    ("ทำเล็บ", "tham lep", "tham lép", "nails", "ทำ to do + เล็บ nail",
     "ต่อเล็บ tɔ̀ɔ lép to extend; เพ้นท์เล็บ pén lép to paint."),
    ("ไปทำถึงที่", "pai tham thueng thi", "bpai tham thʉ̌ng thîi", "come and do it on site",
     "ไป to go + ทำ to do + ถึงที่ right to the place",
     "The house-call phrase. นอกสถานที่ nɔ̂ɔk sà-thǎan-thîi — 'off premises' — is the shop's own word for it."),
    ("ช่างผม", "chang phom", "châang phǒm", "hairdresser (the person)", "ช่าง a skilled tradesperson",
     "ช่าง is the same word as in ช่างไม้ carpenter. A stylist here is a tradesperson, not an artist."),
]

# The sentences somebody actually needs, whole. A vocabulary list is not a
# sentence, and at the door it is the sentence that is needed.
SAYINGS = [
    ("ช่างเคยทำผมหยิกฝอยไหมคะ / ครับ",
     "châang khəəi tham phǒm yìk fɔ̌ɔi mǎi ká / kráp",
     "Has the stylist ever worked with tightly coiled hair?",
     "The single most useful sentence on this page. คะ if you are a woman, ครับ if a man."),
    ("ถักเปียแถวได้ไหม คิดราคายังไง",
     "thàk pia thɛ̌ɛo dâi mǎi · khít raa-khaa yang-ngai",
     "Can you do cornrows? How is it priced?",
     "Braiding is usually by the hour or by the head, and the two differ a lot."),
    ("ที่นี่ดัดดิจิตอลได้ไหม ใช้เวลากี่ชั่วโมง",
     "thîi-nîi dàt dì-jì-tôn dâi mǎi · chái wee-laa gìi chûa-moong",
     "Do you do digital perms here? How many hours does it take?",
     "Three to four hours is normal. Ask before you sit down, not after."),
    ("ช่างไปทำถึงที่พักได้ไหม ค่าเดินทางเท่าไร",
     "châang bpai tham thʉ̌ng thîi-phák dâi mǎi · khâa dəən-thaang thâo-rài",
     "Can the stylist come to where I'm staying? What's the travel charge?",
     "Many Thai stylists will; almost none advertise it. You have to ask."),
    ("มีป้ายราคาไหมคะ / ครับ",
     "mii bpâai raa-khaa mǎi ká / kráp",
     "Is there a price list?",
     "Asking for the board is normal and nobody minds. Asking after is where it goes wrong."),
]


def load_reg():
    if REG.exists():
        return json.loads(REG.read_text())
    return {"shops": [], "verified_on": None}




def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    place_slug, name_bi = g["place_slug"], g["name_bi"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    PROVINCES = g["PROVINCES"]
    shelf_og = g.get("shelf_og")

    reg = load_reg()
    (DOCS / "beauty.css").write_text(CSS)

    prov_of, all_recs = {}, []
    for p in PROVINCES:
        for r in data[p["key"]]:
            prov_of[r["id"]] = p["key"]
            all_recs.append(r)

    by_id = {r["id"]: r for r in all_recs}

    def href(r):
        return prov_of[r["id"]] + "/p/" + place_slug(r) + ".html"

    beauty = [r for r in all_recs if "beauty" in (r.get("cat") or [])]

    def on(sub):
        out = [r for r in beauty if sub in (r.get("sub") or [])]
        return sorted(out, key=lambda r: (r.get("name") or "").lower())

    barbers, salons, exts = on("barber"), on("salon"), on("extensions")
    nails, spas, hairs = on("nails"), on("beauty-spa"), on("hair")

    def listing(recs):
        """Alphabetical, unranked, with the reach the directory holds.

        The same shape the elephant camps get, for the same reason: a list
        that ranks is a list with an opinion about somebody's livelihood.
        """
        rows = []
        for r in recs:
            a = r.get("attrs") or {}
            marks = []
            if r.get("phone"):
                marks.append("&#9742;")
            if a.get("lineId"):
                marks.append("LINE")
            if r.get("website") or a.get("facebook"):
                marks.append("&#127760;")
            if r.get("hours"):
                marks.append("&#128340;")
            ch = " <small>" + " ".join(marks) + "</small>" if marks else ""
            cr = "" if prov_of[r["id"]] == "cm" else " <small>&middot;&#3594;&#3619;</small>"
            rows.append("<div><a href=\"" + href(r) + "\">" + name_bi(r) + "</a>" + ch + cr + "</div>")
        return "<div class=\"bt-list\">" + "".join(rows) + "</div>"

    def note(th, en):
        return "<p class=\"bt-note\">" + bi(th, en) + "</p>"

    def h2(th, en, n=None):
        c = "" if n is None else " <span class=\"bt-count\">(" + str(n) + ")</span>"
        return "<h2>" + bi(th, en) + c + "</h2>"

    # ---- the words --------------------------------------------------------
    wrows = "".join(
        "<tr><td class=\"th\">" + esc(t) + "</td><td class=\"rtgs\">" + esc(rt)
        + "<br>" + esc(tone) + "</td><td>" + esc(en) + "<br><span class=\"root\">"
        + esc(root) + "</span></td><td>" + esc(nt) + "</td></tr>"
        for t, rt, tone, en, root, nt in WORDS)
    words_html = (
        "<table class=\"bt-words\"><thead><tr><th>" + bi("คำ", "Word")
        + "</th><th>RTGS / " + bi("เสียง", "tone") + "</th><th>"
        + bi("แปล-ราก", "Meaning & root") + "</th><th>"
        + bi("ใช้ยังไง", "How it is used") + "</th></tr></thead><tbody>"
        + wrows + "</tbody></table>")

    say_html = "".join(
        "<div class=\"bt-say\"><p class=\"line\">" + esc(th) + "</p><p class=\"gloss\">"
        + esc(rt) + "</p><p>" + esc(en) + "</p><p class=\"gloss\">" + esc(nt) + "</p></div>"
        for th, rt, en, nt in SAYINGS)

    # ---- the census of what nobody has been asked -------------------------
    # Recomputed every build from audit_beauty's own rules, so the number on
    # the page can never drift from the number the audit reports.
    zero = {}
    for key in ("perm", "textured", "mobile"):
        zero[key] = len(audit_beauty.scan(key)[2])
    total = len(all_recs)

    stated = [r for r in beauty
              if any(k in ((r.get("attrs") or {}).get("facets") or {})
                     for k in ("mencut", "womencut", "unisex"))]
    # A LINK IS NOT A READABLE SOURCE, and counting them together overstated
    # this queue as 18 when only 8 were ever eligible. enrich_sites' first-hand
    # rule excludes Facebook, Instagram and LINE — a login wall is not a
    # statement about a shop — so the two are counted apart. Same class of
    # error as the barber shelf: a number that flatters itself.
    import enrich_sites as _es
    linked = sorted(
        [r for r in beauty
         if r.get("website") or (r.get("attrs") or {}).get("facebook")
         or (r.get("attrs") or {}).get("instagram")],
        key=lambda r: (r.get("name") or "").lower())

    def _url_of(r):
        a = r.get("attrs") or {}
        return r.get("website") or a.get("facebook") or a.get("instagram") or ""

    queue = [r for r in linked if _es.first_hand(_url_of(r))]
    social = [r for r in linked if not _es.first_hand(_url_of(r))]

    gap_th = ("จาก {:,} ระเบียนในสองจังหวัด ไม่มีร้านไหนบอกเลยว่าทำผมหยิกฝอยแบบผมแอฟริกันได้ "
              "— ไม่ใช่ว่าไม่มีร้านทำได้ แต่ไม่มีร้านไหนเคยพูด และหน้านี้จะไม่เดาแทน "
              "เพราะการเดาว่า “ได้” หนึ่งครั้ง คือการส่งคนหนึ่งคนไปนั่งเก้าอี้ที่ไม่มีใครเคยจับผมแบบนั้นมาก่อน").format(total)
    gap_en = ("of {:,} records across both provinces state that they work with tightly coiled or "
              "Afro-textured hair. That is not the same as no shop being able to — it means no shop "
              "has said so, and this page will not guess on their behalf. One wrong yes puts somebody "
              "in a chair where nobody has handled their hair before.").format(total)
    gap_html = (
        "<div class=\"bt-gap\"><b>&#127744; "
        + bi("ผมหยิกฝอย-ผมแอฟโฟร — สิ่งที่สารบัญนี้ยังตอบไม่ได้",
             "Tightly coiled and Afro-textured hair — what this directory cannot yet tell you")
        + "</b><p><span class=\"n\">" + str(zero["textured"]) + "</span> " + bi(gap_th, gap_en)
        + "</p><p>"
        + bi("สิ่งที่ทำได้ตอนนี้: ถามด้วยประโยคข้างบน แล้วบอกมดว่าร้านตอบว่าอะไร — คำตอบจะขึ้นเป็นป้าย 🌀 บนหน้าร้านนั้น และเป็นของสาธารณะตลอดไป",
             "What can be done today: ask the sentence above, then tell the ants what the shop answered. It becomes a 🌀 mark on that shop’s page, and it stays public for good.")
        + "</p></div>")

    def li(th, en, val):
        return "<li>" + bi(th, en) + ": <b>" + str(val) + "</b></li>"

    census_html = (
        note("นับใหม่ทุกครั้งที่สร้างหน้า จากกฎเดียวกับ importers/audit_beauty.py",
             "Recounted on every build, from the same rules as importers/audit_beauty.py")
        + "<ul class=\"bt-queue\">"
        + li("ชื่อร้านที่บอกว่าดัดผม-ดัดดิจิตอล-ยืดผม-เกล้าผม",
             "shopfronts naming a perm, a digital perm, straightening or an updo", zero["perm"])
        + li("ชื่อร้านที่บอกว่าทำผมหยิกฝอย-ผมแอฟโฟร",
             "shopfronts naming textured or Afro hair", zero["textured"])
        + li("ชื่อร้านที่บอกว่าไปทำถึงที่",
             "shopfronts naming a house call", zero["mobile"])
        + li("ร้านที่บอกเองว่าตัดให้ใคร (ชาย-หญิง-ทั้งสอง จาก OpenStreetMap)",
             "shops that state who they cut for (male / female / unisex, from OpenStreetMap)",
             str(len(stated)) + " / " + str(len(beauty)))
        + li("ร้านที่มีเว็บของตัวเองให้อ่าน (อ่านแล้ว)",
             "shops with a site of their own to read (read)", len(queue))
        + li("ร้านที่มีแต่ลิงก์เฟซบุ๊ก-ไลน์ — ไม่นับเป็นแหล่งข้อมูลชั้นต้น",
             "shops carrying only a Facebook or LINE link — not a first-hand source", len(social))
        + li("บริการที่ร้านบอกเองบนเว็บของตัวเอง",
             "services a shop states on its own site",
             sum(len(x.get("stated") or {}) for x in (reg.get("shops") or [])))
        + "</ul>"
        + note("สามบรรทัดแรกเป็นศูนย์ และตั้งใจพิมพ์ไว้ให้เห็น: ไม่มีกฎชื่อร้านไหนที่รอเขียนอยู่ ทั้งสามข้อตอบได้ทางเดียวคือร้านบอกเอง หรือมีคนไปยืนถามหน้าร้าน",
               "The first three lines are zero, and are printed rather than hidden: there is no name rule waiting to be written. Those three are answered by the shop stating it, or by somebody asking at the shop — and by nothing else."))

    # ---- the register (empty, and saying so) ------------------------------
    stated_shops = [x for x in (reg.get("shops") or []) if x.get("stated")]
    if stated_shops:
        FLABEL = {k: (f["th"], f["en"], f.get("icon", ""))
                  for k, f in (g.get("FACET_DEF") or {}).get("beauty", {}).items()}
        cards = []
        for x in stated_shops:
            r = by_id.get(x["place"])
            title = ('<a href="' + href(r) + '">' + name_bi(r) + "</a>") if r else esc(x.get("name") or "")
            lines = []
            for k in x["stated"]:
                th, en, ic = FLABEL.get(k, (k, k, ""))
                ev = (x.get("evidence") or {}).get(k, "")
                lines.append("<li>" + esc(ic) + " " + bi(th, en)
                             + ('<br><span class="ev">“…' + esc(ev) + '…”</span>' if ev else "")
                             + "</li>")
            src = esc(x.get("source", ""))
            cards.append(
                '<div class="bt-shop"><h3>' + title + "</h3><ul>" + "".join(lines) + "</ul>"
                + '<p class="bt-note">' + bi("อ่านจากเว็บของร้านเอง", "read from the shop’s own site")
                + ' · <a href="' + att(src) + '" rel="noopener nofollow">'
                + esc(src.replace("https://", "").replace("http://", "").rstrip("/"))
                + "</a> · " + bi("เมื่อ", "on") + " " + esc(x.get("fetched", "")) + "</p></div>")
        unread = reg.get("could_not_read") or []
        why = {}
        for u in unread:
            key = ("social" if "social or messaging" in u.get("why", "")
                   else "robots" if "robots" in u.get("why", "") else "dead")
            why[key] = why.get(key, 0) + 1
        reg_html = (
            note("ทุกบรรทัดคือคำที่ร้านเขียนไว้เอง พร้อมประโยคที่อ่านเจอ ไม่มีบรรทัดไหนที่ตรวจย้อนไม่ได้ ช่องว่างแปลว่าหน้าเว็บไม่ได้พูดถึง ไม่ได้แปลว่าไม่มี",
                 "Every line is the shop’s own wording, with the sentence it was read from — nothing here is unauditable. A blank means the page did not mention it, never that the shop cannot.")
            + '<div class="bt-shops">' + "".join(cards) + "</div>"
            + note("อ่านไม่ได้ " + str(len(unread)) + " ร้าน: " + str(why.get("social", 0))
                   + " ร้านมีแต่ลิงก์เฟซบุ๊ก-ไลน์ (กำแพงล็อกอินไม่ใช่คำบอกของร้าน) · "
                   + str(why.get("dead", 0)) + " ร้านโดเมนตายแล้ว · "
                   + str(why.get("robots", 0)) + " ร้าน robots.txt ไม่อนุญาต",
                   str(len(unread)) + " could not be read: " + str(why.get("social", 0))
                   + " carry only a Facebook or LINE link (a login wall is not a statement by the shop) · "
                   + str(why.get("dead", 0)) + " have a domain that no longer resolves · "
                   + str(why.get("robots", 0)) + " are refused by robots.txt"))
    else:
        qrows = "".join("<li><a href=\"" + href(r) + "\">" + name_bi(r) + "</a></li>"
                        for r in queue)
        reg_html = (
            "<p>"
            + bi("ยังไม่มีร้านไหนถูกอ่าน — และนั่นคือสถานะจริง ไม่ใช่การลืม การอ่านหน้าเว็บของร้านคืองานที่ต้องต่อเน็ต ส่วน WO-22 สร้างแบบไม่ต่อเน็ตทั้งชุด คิวพร้อมแล้ว",
                 "No shop has been read yet, and that is the true state rather than an omission: reading a shop’s own pages is network work, and this build was zero-network throughout. The queue is ready.")
            + "</p>"
            + note("ร้านที่มีหน้าให้อ่านแล้ว", "Shops that already have a page to read")
            + "<ul class=\"bt-queue\">" + qrows + "</ul>"
            + "<p class=\"bt-note\">"
            + bi("โครงของทะเบียนอยู่ใน", "The register’s shape is in")
            + " <code>data/curated/beauty.json</code> &middot; "
            + bi("ขั้นตอนที่รอไฟเขียว", "the steps awaiting a go")
            + " <code>notes/beauty-proposal-2026-08-20.md</code></p>")

    # ---- assemble ---------------------------------------------------------
    intro = bi(
        "หน้านี้มีสี่อย่าง: คำที่ต้องพูดเพื่อให้ได้ทรงที่อยากได้ (ภาษาไทย เสียงอ่าน และรากคำ) · ชั้นร้านตัดผมชายและร้านเสริมสวยที่สารบัญมี · สิ่งที่ยังไม่มีใครถามร้านเลย พร้อมตัวเลขจริง · และทะเบียนบริการที่ร้านบอกเอง เรียงตามตัวอักษร ไม่จัดอันดับ ไม่แยกว่าร้านไหนของใคร",
        "Four things on one page: the words to say to get the haircut you want, in Thai, with the sounds and the roots · the barber and salon shelves the directory holds · what nobody has asked the shops yet, with the real counts · and the register of services the shops state for themselves. Alphabetical, unranked, and never sorted by whose shop it is thought to be.")
    rule_html = (
        "<div class=\"bt-rule\"><b>&#128136; " + bi("กติกาของหน้านี้", "The rule of this page")
        + "</b>"
        + bi("ร้านบอกเองว่าทำอะไรได้ — หรือหน้านี้บอกว่ายังไม่มีใครถาม · ช่องว่างแปลว่าเงียบ ไม่ได้แปลว่าไม่มี · หน้านี้ไม่แยกร้านเป็นร้านฮิปกับร้านธรรมดา ร้านฝรั่งกับร้านไทย ป้ายหน้าร้านอ่านเองได้ และร้านทุกร้านที่เขียนว่า BARBER อยู่ในรายการเดียวกันทั้งหมด",
             "The shop states what it can do — or this page says nobody has asked · a blank means silence, never a no · this page does not sort shops into the hip ones and the ordinary ones, the farang ones and the Thai ones. A reader can read a shopfront, and every shop that put BARBER on the sign is in one list.")
        + "</div>")

    og = shelf_og("cm", "beauty") if shelf_og else None
    body = (
        "<h1>&#128136; "
        + bi("เสริมสวย-ตัดผม — คำที่ต้องพูด ร้านที่มี และสิ่งที่ยังไม่มีใครถาม",
             "Hair — the word to ask for, the shops, and what nobody has asked them")
        + "</h1><p class=\"bt-intro\">" + intro + "</p>" + rule_html

        + h2("คำที่ต้องพูด", "The word to ask for")
        + note("ทรงที่อยากได้ ต้องมีคำเรียก ร้านที่ดัดดิจิตอลได้มีอยู่ทั่วเมือง แต่ถ้าพูดว่า “ดัดผม” เฉย ๆ อาจได้ดัดเย็นกลับบ้าน",
               "A haircut you cannot name is a haircut you do not get. Shops all over this city do digital perms — but ask for ดัดผม alone and you may go home with a cold perm.")
        + words_html

        + h2("ประโยคที่ใช้ได้จริงหน้าร้าน", "Sentences that work at the counter")
        + say_html

        + note("พกไปด้วยได้ — แผ่น A4 พิมพ์ขาวดำ ตัวไทยใหญ่พอที่จะชี้ให้ช่างดูหน้าร้าน ถ่ายเอกสารแจกต่อได้เลย",
               "Take it with you — a black-and-white A4 sheet with the Thai set large enough to point at across a counter. Photocopy and hand it on freely.")
        + '<p><a class="bt-sheet" href="reader/hair-words.pdf">📄 '
        + bi("ดาวน์โหลดแผ่นคำศัพท์ตัดผม-ทำผม (PDF สองหน้า)",
             "Download the hair words sheet (2-page PDF)") + "</a></p>"
        + h2("สิ่งที่สารบัญนี้ยังตอบไม่ได้", "What this directory cannot yet tell you")
        + gap_html
        + "<h3>" + bi("สำมะโนความเงียบ", "A census of the silence") + "</h3>"
        + census_html

        + h2("ร้านตัดผมชาย", "Barbers", len(barbers))
        + note("เรียงตามตัวอักษร ไม่จัดอันดับ · ☎ LINE 🌐 🕒 คือสิ่งที่สารบัญมี · ก่อนหน้านี้ชั้นนี้มีอยู่ ๖ ร้าน เพราะ OpenStreetMap ติดป้าย hairdresser=barber ไว้แค่ ๖ จุด ที่เหลือเขียนคำว่า บาร์เบอร์ ไว้บนป้ายร้านตัวเอง",
               "Alphabetical, unranked · ☎ LINE 🌐 🕒 mark what the directory holds · this shelf held six until this build, because OpenStreetMap tags hairdresser=barber on six points. The rest wrote BARBER on their own shopfront.")
        + listing(barbers)

        + h2("ร้านเสริมสวย", "Salons", len(salons))
        + note("ชั้นนี้เคยว่างเปล่า และถูกบันทึกไว้ว่า “ไม่มีสัญญาณใดแยกร้านเสริมสวยออกจากร้านทำผม” ซึ่งจริงกับป้ายข้อมูล และไม่จริงกับร้าน — คำว่า เสริมสวย อยู่ในชื่อร้านหกสิบสองร้าน สัญญาณไม่เคยอยู่ในแท็ก มันอยู่บนป้าย เป็นภาษาไทย มาตลอด",
               "This shelf was empty, recorded as “no OSM signal separates a salon from a hairdresser”. True of the tags and false of the shops: เสริมสวย is in sixty-two names. The signal was never in the tag — it was on the sign, in Thai, all along.")
        + listing(salons)

        + h2("ต่อผม-ถักเปีย", "Extensions & braids", len(exts))
        + note("ร้านเดียว และหน้านี้บอกว่าร้านเดียว การถักเปียแถวและการต่อผมทำกันในร้านทั่วเมือง แต่แทบไม่มีร้านไหนเขียนไว้บนป้าย — จึงเป็นคำถามหน้าร้าน ไม่ใช่กฎชื่อร้าน",
               "One shop, and this page says one shop. Cornrowing and extensions are done in salons all over this city; almost none writes it on the sign — so it is a question for the shopfront, not a name rule.")
        + listing(exts)

        + h2("ร้านบอกเองว่าตัดให้ใคร", "Who the shops state they cut for", len(stated))
        + note("สามป้ายเดียวที่ OpenStreetMap รู้เรื่องร้านผม — male, female, unisex — และการนำเข้าเคยทิ้งทั้งสามไปทุกครั้ง ตอนนี้ขึ้นเป็นป้ายบนหน้าร้าน ร้านที่ตอบไปแล้วไม่ควรถูกถามซ้ำหน้าร้าน",
               "The only three things OpenStreetMap knows about a hair shop — male, female, unisex — and the import threw all three away on every run until now. They are facet marks on the shop’s own page now: a shop that has already answered should not be asked again in person.")
        + listing(stated)

        + h2("ทะเบียนบริการ — ร้านบอกเองว่าอะไร", "The services register — what each shop states")
        + reg_html

        + h2("ชั้นอื่นในหมวดนี้", "The rest of the shelf")
        + "<ul class=\"bt-queue\">"
        + "<li><a href=\"cm/beauty/hair/\">" + bi("ร้านทำผม", "Hair salons") + "</a> (" + str(len(hairs)) + ")</li>"
        + "<li><a href=\"cm/beauty/nails/\">" + bi("ทำเล็บ", "Nails") + "</a> (" + str(len(nails)) + ")</li>"
        + "<li><a href=\"cm/beauty/spa-beauty/\">" + bi("สปาความงาม", "Beauty spa") + "</a> (" + str(len(spas)) + ")</li>"
        + "<li><a href=\"cm/massage/\">" + bi("นวด-สปา", "Massage & spa") + "</a></li>"
        + "<li><a href=\"cm/tattoo/\">" + bi("สักยันต์-รอยสัก", "Tattoo & sak yant") + "</a> — "
        + bi("สักคิ้วอยู่ที่นั่น ไม่ได้อยู่ชั้นนี้", "cosmetic brow tattooing is filed there, not here") + "</li>"
        + "</ul>"
        + share_block(BASE + "beauty.html", "เสริมสวย-ตัดผม คำที่ต้องพูด · มดแดง", card=og))

    title = ("เสริมสวย-ตัดผม เชียงใหม่ — คำที่ต้องพูด ร้านตัดผมชาย ร้านเสริมสวย"
             " · Hair in Chiang Mai — the word to ask for")
    desc = ("คำภาษาไทยสำหรับตัดผม ดัดดิจิตอล ต่อผม ถักเปีย เกล้าผม ยืดผม และไปทำถึงที่ "
            "พร้อมเสียงอ่านและรากคำ · ชั้นร้านตัดผมชายและร้านเสริมสวยของเชียงใหม่-เชียงราย "
            "· และสิ่งที่ยังไม่มีใครถามร้านเลย · Thai words for a haircut, a digital perm, "
            "extensions, braids, an updo and a house call, with sounds and roots; the barber "
            "and salon shelves of Chiang Mai and Chiang Rai; and an honest census of what "
            "nobody has asked them")
    crumbs = ("<a href=\"index.html\">" + bi("หน้าแรก", "Home") + "</a> › "
              + bi("เสริมสวย-ตัดผม", "Hair"))
    (DOCS / "beauty.html").write_text(page(
        title, body, depth=0, path="beauty.html", desc=desc,
        extra_head="<link rel=\"stylesheet\" href=\"beauty.css\">", og=og, crumbs=crumbs))
    return {"page": 1, "words": len(WORDS), "sentences": len(SAYINGS),
            "barbers": len(barbers), "salons": len(salons), "extensions": len(exts),
            "who_stated": len(stated), "read_queue": len(queue),
            "silent_perm": zero["perm"], "silent_textured": zero["textured"],
            "silent_mobile": zero["mobile"]}
