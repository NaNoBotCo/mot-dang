#!/usr/bin/env python3
"""ยาข้ามพรมแดน — medicine through the airport (/medicine-airport.html).

WHO THIS IS FOR. Two people at the same carousel. The person arriving with a
bag of their own prescriptions, wondering which channel to walk; and the
person who lives here, was prescribed medicine by a Thai doctor, and is about
to fly home to see family with it. Both questions have official, published
answers, in English, from Thailand's own FDA — and almost nobody has read
them, so the group chat answers instead.

WHAT THIS PAGE IS. The Thai FDA's two traveler-guidance documents (inbound,
version 5, dated 21 September 2024; outbound, version 4, dated 29 January
2021), read on 2026-08-26 and printed here with the source on every claim.
Where the FDA is silent, this page says so instead of guessing — writing
border rules from memory is the failure this repo has a rule against.

WHAT THIS PAGE IS NOT. Not medical advice, not legal advice. It names no
dose, holds no view on what anyone should take, and the ADHD-stimulant
special case stays on /adhd.html, which owns it. The authority's checker
outranks this page, and the page says so.
"""

FDA_IN = ("https://permitfortraveler.fda.moph.go.th/nct_permit_main/Upload/"
          "Guidance%20for%20Travelers%20who%20travel%20into%20Thailand_21092024.pdf")
FDA_OUT = ("https://permitfortraveler.fda.moph.go.th/nct_permit_main/Upload/"
           "Guidance_for_Travelers_who_travel_out_of_Thailand.pdf")
FDA_TOOL = ("https://permitfortraveler.fda.moph.go.th/nct_permit_main/"
            "Main/FRM_checkdrug_index")
FDA_PORTAL = "https://permitfortraveler.fda.moph.go.th/nct_permit_main/"
READ_DATE = "2026-08-26"

CSS = """
:root{--mv-ink:#33302a;--mv-line:#e2dacc;--mv-tint:#faf6ee;
--mv-go:#2f6b46;--mv-stop:#a63a2a;--mv-quiet:#8a7d64}
.mv-intro{font-size:1.05rem;line-height:1.65;max-width:62ch}
.mv-note{color:var(--mv-quiet);font-size:.92rem;line-height:1.6;max-width:64ch}
.mv-h{margin:1.9rem 0 .35rem}
.mv-lane{border:1px solid var(--mv-line);border-radius:.85rem;
padding:.85rem 1rem 1rem;margin:.9rem 0;background:var(--mv-tint)}
.mv-lane h3{margin:.1rem 0 .3rem;font-size:1.1rem}
.mv-lane p{margin:.35rem 0;line-height:1.6}
.mv-badge{display:inline-block;font-size:.76rem;letter-spacing:.03em;
text-transform:uppercase;border-radius:.6rem;padding:.08rem .5rem;
margin-left:.4rem;color:#fff}
.mv-badge.go{background:var(--mv-go)}
.mv-badge.paper{background:#7a6a2f}
.mv-badge.stop{background:var(--mv-stop)}
.mv-src{display:block;color:var(--mv-quiet);font-size:.84rem;margin-top:.4rem}
.mv-src a{color:inherit}
.mv-list{line-height:1.7}
.mv-gloss{display:grid;gap:.3rem;margin:.6rem 0}
.mv-gloss .row{display:grid;grid-template-columns:minmax(8rem,12rem) minmax(7rem,10rem) 1fr;
gap:.2rem .8rem;padding:.35rem 0;border-top:1px dashed var(--mv-line)}
.mv-gloss .row:first-child{border-top:0}
.mv-gloss .th{font-weight:600}
.mv-gloss .rtgs{color:var(--mv-quiet);font-style:italic}
@media(max-width:640px){.mv-gloss .row{grid-template-columns:1fr}}
"""


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS = g["BASE"], g["DOCS"]
    share_block = g["share_block"]
    shelf_og = g.get("shelf_og")
    bi_text = g.get("bi_text") or (lambda th, en: th + " · " + en)

    (DOCS / "medtravel.css").write_text(CSS)

    def src(th, en, url, label):
        return ('<span class="mv-src">' + bi(th, en) + ' — <a href="'
                + att(url) + '" rel="noopener">' + esc(label) + "</a>, "
                + bi("อ่านเมื่อ " + READ_DATE, "read " + READ_DATE) + "</span>")

    src_in = src("ที่มา: เอกสารแนะนำขาเข้าของ อย. (ฉบับที่ 5, 21 ก.ย. 2567)",
                 "Source: Thai FDA inbound guidance (version 5, 21 Sep 2024)",
                 FDA_IN, "permitfortraveler.fda.moph.go.th")
    src_out = src("ที่มา: เอกสารแนะนำขาออกของ อย. (ฉบับที่ 4, 29 ม.ค. 2564)",
                  "Source: Thai FDA outbound guidance (version 4, 29 Jan 2021)",
                  FDA_OUT, "permitfortraveler.fda.moph.go.th")

    gloss = [
        ("ใบสั่งยา", "bai sang ya", "prescription — the paper a doctor writes"),
        ("ใบรับรองแพทย์", "bai raprong phaet",
         "medical certificate — the doctor's letter customs wants; ask for it in English"),
        ("ยาประจำตัว", "ya prajam tua",
         "your own regular medicine — the phrase to use at any desk"),
        ("ยาเสพติดให้โทษ", "ya sep tit hai thot",
         "narcotic drug — the legal class of opioid-type medicine (lane 3)"),
        ("วัตถุออกฤทธิ์ต่อจิตและประสาท", "watthu ok rit to chit lae prasat",
         "psychotropic substance — the legal class of sleep and anxiety medicine (lane 2)"),
        ("ช่องเขียว / ช่องแดง", "chong khiao / chong daeng",
         "green channel / red channel at customs — nothing to declare / goods to declare"),
        ("ใบอนุญาต", "bai anuyat", "permit — Form IC-2 inbound, Form OC-2 outbound"),
        ("ด่านอาหารและยา", "dan ahan lae ya",
         "the FDA checkpoint at the airport — where medicine questions are answered"),
    ]
    gloss_html = ('<div class="mv-gloss">'
                  + "".join('<div class="row"><span class="th">' + esc(t)
                            + '</span><span class="rtgs">' + esc(r)
                            + '</span><span>' + esc(m) + "</span></div>"
                            for t, r, m in gloss)
                  + "</div>")

    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "name": "ยาข้ามพรมแดน — พกยาผ่านสนามบินไทย · Medicine through Thai airports",
          "url": BASE + "medicine-airport.html",
          "inLanguage": ["th", "en"],
          "citation": [FDA_IN, FDA_OUT, FDA_PORTAL]}
    import json as _json
    head = ('<link rel="stylesheet" href="medtravel.css">'
            '<script type="application/ld+json">'
            + _json.dumps(ld, ensure_ascii=False) + "</script>")
    og = shelf_og("cm", "medical") if shelf_og else None

    body = (
        "<h1>" + bi("ยาข้ามพรมแดน — พกยาผ่านสนามบิน",
                    "Medicine through the airport — both directions") + "</h1>"

        + '<p class="mv-intro">' + bi(
            "คนสองคนยืนอยู่ที่สายพานเดียวกัน คนหนึ่งเพิ่งลงเครื่อง พกยาประจำตัวมาจากบ้าน "
            "ไม่แน่ใจว่าต้องเดินช่องไหน อีกคนอยู่ที่นี่ หมอไทยสั่งยาให้ และกำลังจะบินกลับไปเยี่ยมบ้านพร้อมยา "
            "ทั้งสองคำถามมีคำตอบทางการที่ตีพิมพ์แล้ว — หน้านี้คือคำตอบนั้น อ่านจากเอกสารของ อย. เอง "
            "พร้อมลิงก์ต้นทางและวันที่กำกับทุกข้อ",
            "Two people stand at the same carousel. One just landed with their own "
            "prescriptions and isn't sure which channel to walk. The other lives here, "
            "was prescribed medicine by a Thai doctor, and is flying home to visit family "
            "with it. Both questions have official, published answers — this page is those "
            "answers, read from the Thai FDA's own guidance, with the source and date on "
            "every claim.")
        + "</p>"

        + '<p class="mv-note">' + bi(
            "หน้านี้ไม่ใช่คำแนะนำทางการแพทย์หรือกฎหมาย ไม่มีขนาดยา "
            "เป็นเรื่องของเอกสารกับด่านเท่านั้น กฎเปลี่ยนได้ — ต้นทางที่ลิงก์ไว้ชนะหน้านี้เสมอ",
            "This page is not medical or legal advice. It names no dose and holds no view "
            "on what anyone should take — it is about paperwork and checkpoints only. "
            "Rules change; the linked source always outranks this page.")
        + "</p>"

        + "<h2 class=\"mv-h\">" + bi("เช็กยาของคุณกับเครื่องมือ อย.",
                                     "Check your medicine — the FDA tool") + "</h2>"
        + "<p>" + bi(
            "พิมพ์ชื่อสามัญ (ชื่อโมเลกุล ไม่ใช่ยี่ห้อ) ลงใน "
            "<a href=\"" + att(FDA_TOOL) + "\" rel=\"noopener\">เครื่องมือตรวจสอบยาของ อย.</a> "
            "จะได้คำตอบของหน่วยงานเองว่ายาของคุณอยู่ในบัญชีไหนและพกเข้ามาได้อย่างไร "
            "คำตอบนั้นใหญ่กว่าหน้านี้ ใหญ่กว่าเภสัชกรที่บ้าน และใหญ่กว่ากรุ๊ปแชท",
            "Type the generic (molecule) name — not the brand name — into the "
            "<a href=\"" + att(FDA_TOOL) + "\" rel=\"noopener\">FDA's check-the-drug tool</a>. "
            "It returns the authority's own answer about which list your medicine sits on "
            "and how it may be carried. That answer outranks this page, your pharmacist at "
            "home, and the group chat.", raw=True)
        + "</p>"

        + "<h2 class=\"mv-h\">" + bi("ขาเข้า — สามช่องทาง", "Arriving — the three lanes") + "</h2>"

        + '<div class="mv-lane"><h3>' + bi("ยาทั่วไป", "Ordinary prescription medicine")
        + '<span class="mv-badge go">' + bi("ช่องเขียว", "green channel") + "</span></h3>"
        + "<p>" + bi(
            "ยาส่วนใหญ่อยู่ช่องนี้ — ยาความดัน ไทรอยด์ เบาหวาน ฮอร์โมน อินซูลิน "
            "อย. ระบุว่ายาที่ไม่ใช่ยาเสพติดหรือวัตถุออกฤทธิ์ ถือเป็นของใช้ส่วนตัวเมื่อ "
            "ไม่เกินปริมาณใช้ 30 วัน อยู่ในบรรจุภัณฑ์เดิมที่มีฉลาก และมีใบสั่งยาหรือใบรับรองแพทย์ระบุชื่อคุณ "
            "เดินช่องเขียวได้ ไม่ต้องสำแดง เก็บใบสั่งยาติดตัวตลอดการเดินทาง",
            "Most medicine is in this lane — blood pressure, thyroid, diabetes, hormones, "
            "insulin. The FDA states that medicine outside the controlled classes counts as "
            "personal belongings when it is no more than a 30-day supply, in its original "
            "labeled packaging, with a prescription or medical certificate in your name. "
            "Green channel, nothing to declare; keep the prescription with you for the "
            "whole stay.") + "</p>" + src_in + "</div>"

        + '<div class="mv-lane"><h3>' + bi("วัตถุออกฤทธิ์ (ประเภท 2, 3, 4)",
                                           "Psychotropics (Schedule II, III, IV)")
        + '<span class="mv-badge paper">' + bi("เอกสาร หรือใบอนุญาต", "papers, or a permit") + "</span></h3>"
        + "<p>" + bi(
            "ยานอนหลับและยาคลายกังวลหลายตัวอยู่ช่องนี้โดยที่คนพกไม่รู้ตัว — alprazolam, diazepam, "
            "clonazepam, lorazepam, zolpidem, zopiclone, phenobarbital รวมถึง pseudoephedrine "
            "กติกาของ อย. มีสองขั้น: ไม่เกิน 30 วัน — ไม่ต้องขอใบอนุญาต แค่มีใบรับรองแพทย์หรือใบสั่งยา "
            "ครบตามหัวข้อด้านล่าง · 31–90 วัน — ต้องขอใบอนุญาต IC-2 ล่วงหน้าอย่างน้อย 15 วัน",
            "Many sleep and anxiety medicines sit in this lane without their carriers "
            "knowing — alprazolam, diazepam, clonazepam, lorazepam, zolpidem, zopiclone, "
            "phenobarbital, even pseudoephedrine. The FDA's stated rule has two tiers: up "
            "to a 30-day supply needs no permit, only a certificate or prescription with "
            "the details listed below; a 31-to-90-day supply needs a Form IC-2 permit "
            "applied for at least 15 days ahead.") + "</p>" + src_in + "</div>"

        + '<div class="mv-lane"><h3>' + bi("ยาเสพติดให้โทษ (ประเภท 2, 3)",
                                           "Narcotic-class medicine (Schedule II, III)")
        + '<span class="mv-badge paper">' + bi("ใบอนุญาตเสมอ · ช่องแดง", "permit always · red channel") + "</span></h3>"
        + "<p>" + bi(
            "ยาแก้ปวดกลุ่มโอปิออยด์ — codeine, morphine, oxycodone, fentanyl, methadone, "
            "tapentadol และญาติ ๆ — ต้องมีใบอนุญาต IC-2 ทุกกรณี พกได้ไม่เกินปริมาณใช้ 90 วัน "
            "ตามกฎกระทรวงที่มีผล 21 ก.ย. 2567 เมื่อถึงไทยให้เดินช่องแดง แสดงยา ใบอนุญาต "
            "และเอกสารแพทย์พร้อมกัน",
            "Opioid-class painkillers — codeine, morphine, oxycodone, fentanyl, methadone, "
            "tapentadol and their relatives — need the Form IC-2 permit in every case, up "
            "to a 90-day supply, under the ministerial regulation in force since 21 Sep "
            "2024. On arrival, walk the red channel and present medicine, permit, and "
            "medical documents together.") + "</p>" + src_in + "</div>"

        + '<div class="mv-lane"><h3>' + bi("ที่นำเข้าไม่ได้เลย", "What cannot enter at all")
        + '<span class="mv-badge stop">' + bi("ไม่มีใบอนุญาตชนิดใดช่วยได้", "no permit exists") + "</span></h3>"
        + "<p>" + bi(
            "อย. ระบุชื่อ amphetamine และ dextroamphetamine (ยาสมาธิสั้นตระกูล Adderall) "
            "รวมทั้งวัตถุออกฤทธิ์ประเภท 1 เช่น dronabinol (THC), GHB, psilocin ว่า "
            "ห้ามนำเข้าโดยไม่มีข้อยกเว้น เพราะกฎหมายไทยจัดว่าไม่มีการใช้ทางการแพทย์ในประเทศ "
            "เรื่องยาสมาธิสั้นทั้งเรื่อง — บัญชีไหน มีตัวไหนในระบบไทย ถามหมอที่ไหน — "
            "อยู่ที่หน้า <a href=\"adhd.html\">สมาธิสั้น</a>",
            "The FDA names amphetamine and dextroamphetamine (the Adderall family) plus "
            "Schedule I psychotropics such as dronabinol (THC), GHB and psilocin as "
            "prohibited with no exception — Thai law classes them as having no medical "
            "use in the country. The whole ADHD-medicine story — which list, what the "
            "Thai system stocks, where to ask — lives on the "
            "<a href=\"adhd.html\">ADHD page</a>.", raw=True) + "</p>" + src_in + "</div>"

        + "<h2 class=\"mv-h\">" + bi("ใบรับรองแพทย์ต้องมีอะไรบ้าง",
                                     "What the doctor's paper must contain") + "</h2>"
        + '<p class="mv-note">' + bi(
            "อย. ระบุหัวข้อไว้ห้าข้อ ฉลากขวดยาอย่างเดียวไม่ครบ — ขอจดหมายจากแพทย์ที่มีครบทุกข้อ",
            "The FDA lists five required items. A pharmacy label alone does not carry all "
            "five — ask the prescribing doctor for a letter that does.") + "</p>"
        + '<ul class="mv-list">'
        + "<li>" + bi("ชื่อและที่อยู่ของผู้ป่วย (ต้องตรงกับพาสปอร์ต)",
                      "The patient's name and address (matching the passport)") + "</li>"
        + "<li>" + bi("โรคหรือภาวะที่วินิจฉัย", "The diagnosed condition") + "</li>"
        + "<li>" + bi("ชื่อยา ความแรง วิธีใช้ และเหตุผลที่สั่ง",
                      "Medication names, strengths, instructions, and the reason prescribed") + "</li>"
        + "<li>" + bi("ขนาดใช้และจำนวนรวมที่สั่ง", "Dosage and total amount prescribed") + "</li>"
        + "<li>" + bi("ชื่อ ที่อยู่ และเลขใบอนุญาตของแพทย์ผู้สั่ง",
                      "The prescribing physician's name, address, and license number") + "</li>"
        + "</ul>" + src_in

        + "<h2 class=\"mv-h\">" + bi("ใบอนุญาต IC-2 ขอยังไง", "How the Form IC-2 permit works") + "</h2>"
        + '<ul class="mv-list">'
        + "<li>" + bi("ยื่นออนไลน์ที่ <a href=\"" + att(FDA_PORTAL) + "\" rel=\"noopener\">permitfortraveler.fda.moph.go.th</a> ล่วงหน้าอย่างน้อย 15 วันก่อนถึงไทย ใช้เวลาพิจารณาประมาณ 3 วันทำการ",
                      "Apply online at <a href=\"" + att(FDA_PORTAL) + "\" rel=\"noopener\">permitfortraveler.fda.moph.go.th</a> at least 15 days before arrival; processing takes about 3 working days", raw=True) + "</li>"
        + "<li>" + bi("อย. ระบุเองว่าต้องใช้คอมพิวเตอร์กับเบราว์เซอร์ Chrome — กรอกบนมือถือไม่ได้",
                      "The FDA's own words: use a PC or laptop with Chrome — the form cannot be completed on a phone") + "</li>"
        + "<li>" + bi("ใบอนุญาตส่งมาทางอีเมล พิมพ์หรือโชว์ไฟล์บนมือถือก็ได้ เอกสารตัวจริงเก็บติดตัว ไม่ต้องส่งไปที่ อย.",
                      "The permit arrives by email; print it or show the file on your phone. Originals stay with you — nothing is mailed to the FDA") + "</li>"
        + "<li>" + bi("ถ้าได้ใบอนุญาตขาเข้าแล้ว อย. ระบุว่าไม่ต้องขอใบอนุญาตส่งออกอีกตอนพายากลับบ้าน",
                      "If you obtained the import permit, the FDA states no separate export permit is needed to carry the same medicine home") + "</li>"
        + "</ul>" + src_in

        + "<h2 class=\"mv-h\">" + bi("ขาออก — พายาที่หมอไทยสั่งขึ้นเครื่อง",
                                     "Departing — flying with Thai-prescribed medicine") + "</h2>"
        + '<div class="mv-lane"><h3>' + bi("ยาทั่วไปจากโรงพยาบาลหรือร้านยา",
                                           "Ordinary medicine from a hospital or pharmacy")
        + '<span class="mv-badge go">' + bi("เก็บฉลากกับใบเสร็จ", "keep the label and receipt") + "</span></h3>"
        + "<p>" + bi(
            "ฝั่งไทยง่าย — เก็บฉลากยาและใบเสร็จไว้ ด่านที่กัดจริงคือประเทศปลายทาง "
            "กฎนำเข้ายาของประเทศที่คุณจะลงเครื่องเป็นกฎที่ต้องเช็กก่อนบิน",
            "The Thai side is easy — keep the pharmacy label and the receipt. The "
            "checkpoint that bites is the destination: the import rules of the country "
            "you land in are the ones to check before flying.") + "</p></div>"

        + '<div class="mv-lane"><h3>' + bi("วัตถุออกฤทธิ์ที่หมอไทยสั่ง",
                                           "Thai-prescribed psychotropics")
        + '<span class="mv-badge paper">' + bi("ไม่เกิน 30 วัน + ใบสั่งยา", "≤30 days + prescription") + "</span></h3>"
        + "<p>" + bi(
            "พกออกได้ไม่เกินปริมาณใช้ 30 วัน พร้อมใบรับรองแพทย์หรือใบสั่งยาครบห้าหัวข้อ "
            "อย. ระบุว่าไม่ต้องขอใบอนุญาต",
            "Up to a 30-day supply may leave with the five-item certificate or "
            "prescription; the FDA states no permit is required.") + "</p>" + src_out + "</div>"

        + '<div class="mv-lane"><h3>' + bi("ยาเสพติดให้โทษประเภท 2 ที่หมอไทยสั่ง",
                                           "Thai-prescribed Category 2 narcotics")
        + '<span class="mv-badge paper">' + bi("ใบอนุญาต OC-2 ล่วงหน้า 2 สัปดาห์", "Form OC-2, two weeks ahead") + "</span></h3>"
        + "<p>" + bi(
            "ยากลุ่มโอปิออยด์ที่แพทย์ในไทยสั่ง ต้องขอใบอนุญาต OC-2 จากพอร์ทัลเดียวกัน "
            "ล่วงหน้าอย่างน้อย 2 สัปดาห์ พกได้ไม่เกิน 90 วัน และ อย. ระบุว่าใบเดียวกัน "
            "ครอบคลุมยาที่เหลือตอนกลับเข้าไทยด้วย — ออกแบบมาสำหรับชีวิตรักษาที่นี่ "
            "กลับบ้านพักหนึ่ง แล้วบินกลับมาตามนัด",
            "Opioid-class medicine prescribed by a physician in Thailand needs a Form "
            "OC-2 permit from the same portal, applied for at least two weeks before "
            "departure, up to a 90-day supply — and the FDA states the same permit "
            "covers whatever remains when you return to Thailand. Built for exactly the "
            "treated-here, home-for-a-while, back-for-follow-up rhythm.") + "</p>" + src_out + "</div>"

        + '<div class="mv-lane"><h3>' + bi("ซื้อถูกกฎหมายที่นี่ ≠ บินได้",
                                           "Bought legally here ≠ flies legally")
        + '<span class="mv-badge stop">' + bi("ไม่ขึ้นเครื่อง", "does not board") + "</span></h3>"
        + "<p>" + bi(
            "กัญชาและกระท่อมขายหน้าร้านได้ในไทย แต่ไม่ข้ามพรมแดน — เอกสารขาออกของ อย. "
            "ระบุว่าการนำเข้า-ส่งออกผลิตภัณฑ์ยาจากกัญชายังเป็นสิ่งต้องห้าม "
            "และกฎหมายประเทศปลายทางซ้อนทับอีกชั้น ของที่ลังเลจะยื่นให้เจ้าหน้าที่ศุลกากรดู อย่าใส่กระเป๋า",
            "Cannabis and kratom are sold openly in Thailand and cross no border — the "
            "FDA's outbound guidance states that import and export of cannabis-made "
            "medicinal products is prohibited, and the destination country's law stacks "
            "on top. Anything you would hesitate to show a customs officer, don't pack.")
        + "</p>" + src_out + "</div>"

        + "<h2 class=\"mv-h\">" + bi("สายพานตรวจของเหลว เป็นอีกด่านหนึ่ง",
                                     "The security belt is a different checkpoint") + "</h2>"
        + "<p>" + bi(
            "ศุลกากรสนใจว่ายาคือสารอะไร จุดตรวจความปลอดภัยสนใจว่าเป็นของเหลวไหม "
            "สนามบินไทยใช้กติกา 100 มล. มาตรฐาน โดยมีข้อยกเว้นที่ประกาศไว้: "
            "ยาน้ำ เจล สเปรย์เกิน 100 มล. ผ่านได้เมื่อมีเอกสารระบุชื่อผู้โดยสาร — "
            "ใบรับรองแพทย์หรือฉลากใบสั่งยา — และจะถูกตรวจเพิ่มที่จุดตรวจ "
            "ยาที่กลัวความร้อนอย่างอินซูลิน ควรอยู่กระเป๋าถือขึ้นเครื่องเสมอ",
            "Customs cares what the substance is; the security checkpoint cares that it "
            "is a liquid. Thai airports run the standard 100ml carry-on rule with a "
            "stated exemption: liquid, gel or aerosol medicine over 100ml passes when "
            "accompanied by documentation bearing the passenger's name — a doctor's note "
            "or the prescription label — with an extra check at the belt. "
            "Temperature-sensitive medicine like insulin belongs in the carry-on, always.")
        + "</p>"

        + "<h2 class=\"mv-h\">" + bi("คำบนป้ายและแบบฟอร์ม",
                                     "Words on the sign and the form") + "</h2>"
        + '<p class="mv-note">' + bi(
            "อักษรไทย · คำอ่านแบบ RTGS · ความหมาย — เทียบรูปคำกับป้ายได้แม้อ่านไทยไม่ออก",
            "Thai script · RTGS spelling · what it means — enough to match a word by its "
            "shape, without reading Thai.") + "</p>"
        + gloss_html

        + "<h2 class=\"mv-h\">" + bi("ตรวจสอบเองได้ที่ไหน", "Where to check for yourself") + "</h2>"
        + '<ul class="mv-list">'
        + "<li><a href=\"" + att(FDA_TOOL) + "\" rel=\"noopener\">"
        + bi("เครื่องมือตรวจสอบยาของ อย.", "The FDA's check-the-drug tool") + "</a></li>"
        + "<li><a href=\"" + att(FDA_PORTAL) + "\" rel=\"noopener\">"
        + bi("พอร์ทัลขอใบอนุญาต IC-2 / OC-2", "The IC-2 / OC-2 permit portal") + "</a></li>"
        + "<li><a href=\"" + att(FDA_IN) + "\" rel=\"noopener\">"
        + bi("เอกสารแนะนำขาเข้า (อังกฤษ, PDF)", "Inbound guidance (English, PDF)") + "</a></li>"
        + "<li><a href=\"" + att(FDA_OUT) + "\" rel=\"noopener\">"
        + bi("เอกสารแนะนำขาออก (อังกฤษ, PDF)", "Outbound guidance (English, PDF)") + "</a></li>"
        + "<li>" + bi("กองควบคุมวัตถุเสพติด อย. — tnarcotics@fda.moph.go.th · +66 2590 7346",
                      "FDA Narcotics Control Division — tnarcotics@fda.moph.go.th · +66 2590 7346") + "</li>"
        + "</ul>"

        + '<p class="mv-note">' + bi(
            "มดแดงเป็นสารบัญของสถานที่ ไม่ใช่คำแนะนำทางการแพทย์หรือกฎหมาย หน้านี้ไม่มีขนาดยา "
            "กฎและบัญชียาเปลี่ยนได้ — ตรวจกับต้นทางที่ลิงก์ไว้ก่อนเดินทางทุกครั้ง "
            "เห็นอะไรที่เปลี่ยนไป บอกมดได้ที่หน้าเสนอแนะ",
            "Mot Dang is a directory of places. This page is not medical or legal advice, "
            "names no dose, recommends no brand and no doctor, and holds no view on what "
            "anyone should take. Rules and schedules change — check the linked sources "
            "before every trip. If something here has changed, tell the ants via the "
            "suggestion page.") + "</p>"
        + '<p class="mv-note"><a href="care.html">'
        + bi("ดูแลต่อเนื่อง — แผนก คลินิกนอกเวลา เอกสารเคลม", "Ongoing care — departments, after-hours clinics, claim paperwork")
        + "</a> · <a href=\"adhd.html\">"
        + bi("สมาธิสั้น — ยาและการรักษา", "ADHD — the medicine and the care")
        + "</a> · <a href=\"transport.html\">"
        + bi("รถ-เดินทาง — รวมเที่ยวบิน", "Transport — including flights")
        + "</a></p>"
        + share_block(BASE + "medicine-airport.html",
                      "ยาข้ามพรมแดน — พกยาผ่านสนามบิน · มดแดง", card=og))

    (DOCS / "medicine-airport.html").write_text(page(
        "ยาข้ามพรมแดน — พกยาผ่านสนามบิน · Medicine through Thai airports",
        body, depth=0, path="medicine-airport.html",
        desc=bi_text(
            "พกยาประจำตัวเข้า-ออกไทยผ่านสนามบิน — สามช่องทางขาเข้า ใบอนุญาต IC-2/OC-2 "
            "ใบรับรองแพทย์ต้องมีอะไร ของเหลวเกิน 100 มล. และอะไรที่ไม่ขึ้นเครื่อง "
            "อ่านจากเอกสารของ อย. เอง พร้อมลิงก์ต้นทาง",
            "Carrying personal medicine into and out of Thailand through the airport: "
            "the three arrival lanes, the IC-2 and OC-2 permits, what the doctor's "
            "letter must contain, liquids over 100ml, and what does not board — read "
            "from the Thai FDA's own guidance, with sources linked."),
        extra_head=head, og=og,
        crumbs='<a href="index.html">' + bi("หน้าแรก", "Home") + "</a> › "
               + bi("ยาข้ามพรมแดน", "Medicine through the airport")))

    return "built from 2 FDA guidance docs, 4 lanes in, 4 out-rules, 8 gloss rows"
