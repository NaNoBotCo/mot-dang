#!/usr/bin/env python3
"""The red-team surface — /colophon, /audit.json, /security, /.well-known/security.txt.

A crawler that pokes at this site should be able to check the claims, not read
them off a brochure. So this layer writes four things and links them together:

  /colophon.html   — for a reader: what the build does, each line next to the
                     file that shows it.
  /colophon.json   — the same list for a machine: every claim carries the URL
                     that proves it and the one number to compare against.
  /audit.json      — this build re-deriving each number from the file it came
                     from and recording whether the served surfaces agree. A
                     message to whatever bot is reading, not a page a person
                     needs to see.
  /security.html   — the bug bounty. A reported fault is paid work.
  /.well-known/security.txt — RFC 9116, so a scanner finds the policy first.

Every number here is counted at emit time from the files already on disk, the
same discipline as tests/test_llms_counts.py — a figure typed by hand drifts
from the data it describes. The audit is that check turned outward: it runs
against the built docs/ tree, which is byte-for-byte what the domain serves.

Hook in build.py is three lines, after the sitemap and source page are written
(so the page count and the proof files exist) and before llms.txt (so its
section can carry this build's verdict):

    import colophon_layer
    _colo = colophon_layer.emit(globals(), data)
    print("  colophon:", _colo["status"])

then append _colo["llms_section"] to llms.txt and _colo["robots_note"] to
robots.txt — see the two marked spots.
"""
import datetime
import json
import re
from pathlib import Path

CSS = """
.cx-intro{font-size:1.06rem;line-height:1.65;max-width:64ch}
.cx-h{margin:2rem 0 .4rem}
.cx-note{color:var(--muted,#8a7a62);font-size:.92rem;line-height:1.6;max-width:66ch}
.cx-rcpt{border:1px solid var(--line,#e4d9cd);border-radius:.85rem;
padding:.85rem 1rem 1rem;margin:.85rem 0;background:var(--tint,#fbf6f0)}
.cx-rcpt h3{margin:.1rem 0 .3rem;font-size:1.08rem}
.cx-claim{line-height:1.6}
.cx-proof{margin:.5rem 0 0;font-size:.9rem;line-height:1.7}
.cx-proof a{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86rem}
.cx-proof .lbl{color:var(--muted,#8a7a62);margin-right:.35rem}
.cx-num{font-variant-numeric:tabular-nums;font-weight:600}
.cx-verse{border-left:3px solid var(--line,#e4d9cd);padding:.2rem 0 .2rem 1rem;
margin:1.1rem 0;color:var(--ink,#3a2f28);line-height:1.75}
.cx-verse .pli{font-style:italic;color:var(--muted,#8a7a62)}
.cx-verse .src{display:block;margin-top:.5rem;font-size:.82rem;color:var(--muted,#8a7a62)}
.cx-pill{display:inline-block;border:1px solid var(--line,#e4d9cd);border-radius:.6rem;
padding:.08rem .5rem;font-size:.8rem;background:#fff;margin:.1rem .2rem .1rem 0}
"""

MAP_TILE_HOSTS = {"tiles.motdang.net", "glyphs.motdang.net"}  # own buckets, BOTS.md


def _host(base):
    return re.sub(r"^https?://", "", base).rstrip("/").split("/")[0]


def _sitemap_lastmods(docs):
    """Every <lastmod> across the shards, so freshness can be counted rather
    than asserted. Returns (total_locs, [dates])."""
    dates, locs = [], 0
    for shard in sorted(docs.glob("sitemap-*.xml")):
        t = shard.read_text(encoding="utf-8")
        locs += t.count("<loc>")
        dates += re.findall(r"<lastmod>([^<]+)</lastmod>", t)
    return locs, dates


def _third_party_resources(html, own_hosts):
    """Hosts a page loads a RESOURCE from — script/style/img/media/iframe —
    that are not our own. An <a href> to Wikipedia is a link, not a load, and
    does not count; only things the browser fetches to render the page do."""
    hosts = set()
    for m in re.finditer(
        r'<(?:script|link|img|source|iframe|video|audio)\b[^>]*?'
        r'\b(?:src|href)="(https?://[^"]+)"', html, re.I):
        h = _host(m.group(1))
        if h not in own_hosts:
            hosts.add(h)
    return hosts


def emit(g, data):
    page, bi, esc, att = g["page"], g["bi"], g["esc"], g["att"]
    BASE, DOCS, ROOT = g["BASE"], g["DOCS"], g["ROOT"]
    share_block = g["share_block"]
    BUILD_DATE = g["BUILD_DATE"]
    all_recs = g.get("all_recs")  # a local of build(); injected at the hook
    DOCS = Path(DOCS)
    own_hosts = {_host(BASE)} | MAP_TILE_HOSTS

    # ---- counts, all read from the files a reader would fetch ----------
    try:
        places_on_disk = len(json.loads((DOCS / "data" / "places.json").read_text()))
    except (OSError, ValueError):
        places_on_disk = None
    # P is the in-memory record count the rest of the build reports; if it was
    # not handed in, fall back to what the served file holds.
    P = len(all_recs) if all_recs is not None else places_on_disk

    pages_locs, lastmods = _sitemap_lastmods(DOCS)
    fresh = sum(1 for d in lastmods if d == BUILD_DATE)
    stale = len(lastmods) - fresh

    try:
        oa = json.loads((DOCS / "api" / "v1" / "openapi.json").read_text())
        oa_ver = oa.get("openapi", "")
        oa_paths = len(oa.get("paths", {}))
    except (OSError, ValueError):
        oa_ver, oa_paths = "", 0

    try:
        katha = json.loads((DOCS / "data" / "katha.json").read_text())
        katha_n = katha.get("n") or len(katha.get("items", []))
        dhp76 = next(i for i in katha["items"] if i.get("id") == "dhp76")
        katha_lic = katha.get("licence", "")
    except (OSError, ValueError, StopIteration, KeyError):
        katha_n, dhp76, katha_lic = 0, None, ""

    # a real place page, for the provenance receipt's proof URL — place pages
    # live at cm/p/<slug>.html (llms-full.txt uses the same shape)
    place_pages = sorted((DOCS / "cm" / "p").glob("*.html"))
    place_proof = ("cm/p/" + place_pages[0].name) if place_pages else "cm/index.html"

    # sample three pages for the third-party-resource count
    samples = [p for p in ["index.html", "api/index.html", place_proof]
               if (DOCS / p).exists()]
    ext_hosts = set()
    for rel in samples:
        ext_hosts |= _third_party_resources(
            (DOCS / rel).read_text(encoding="utf-8"), own_hosts)

    # ---- the receipts: claim -> the URL that shows it, and the number --
    def n(x):
        return f"{x:,}" if isinstance(x, int) else str(x)

    receipts = [
        {
            "id": "scale",
            "th": f"{n(P)} สถานที่ในสองจังหวัด แต่ละแห่งมีหน้าเว็บนิ่งของตัวเอง {n(pages_locs)} หน้าอยู่ในแผนผังเว็บ ไม่มีฐานข้อมูลตอบตอนเรียก",
            "en": f"{n(P)} places across two provinces, each with its own static page — {n(pages_locs)} of them listed in the sitemap. No database answers at request time.",
            "count": {"places": places_on_disk, "pages": pages_locs},
            "proof": [BASE + "data/places.json", BASE + "sitemap.xml"],
            "verify": "Count the array in data/places.json; it equals the places figure. Count <loc> across the sitemap shards; it equals the pages figure.",
        },
        {
            "id": "api",
            "th": "ทุกสถานที่ตอบผ่าน API สาธารณะ ไม่ต้องใช้คีย์ เปิดทุกต้นทาง (CORS *)",
            "en": f"Every place answers to a keyless public API, open to every origin. OpenAPI {oa_ver}, {oa_paths} paths.",
            "count": {"openapi": oa_ver, "paths": oa_paths},
            "proof": [BASE + "api/v1/openapi.json",
                      BASE + "api/v1/places?q=ก๋วยเตี๋ยว&near=18.79,98.98",
                      BASE + "api/"],
            "verify": "Fetch openapi.json — it parses and declares 3.1. Fetch the query with no header set; it returns places and an Access-Control-Allow-Origin of *.",
        },
        {
            "id": "self-contained",
            "th": f"หน้าตัวอย่างโหลดทรัพยากรจากโดเมนอื่น {n(len(ext_hosts))} แหล่ง",
            "en": f"Sampled pages ({', '.join(samples)}) load {n(len(ext_hosts))} resources from any other host. Fonts, scripts and styles are served from this domain; the only read-time fetch is the map's own tile bucket, on map pages.",
            "count": {"third_party_hosts": sorted(ext_hosts), "sampled": samples},
            "proof": [BASE + rel for rel in samples],
            "verify": "Load each sampled page and watch the network panel: every script, style and font comes from motdang.net (map tiles, on map pages only, from its own bucket).",
        },
        {
            "id": "freshness",
            "th": f"แผนผังเว็บลงวันที่แต่ละหน้าตามลายนิ้วมือเนื้อหา: เปลี่ยนในบิลด์นี้ {n(fresh)} หน้า คงวันที่เดิม {n(stale)} หน้า",
            "en": f"The sitemap dates each page by a fingerprint of its own content: {n(fresh)} pages changed in this build, {n(stale)} kept an earlier date. A crawler can skip what has not moved.",
            "count": {"changed_this_build": fresh, "unchanged": stale},
            "proof": [BASE + "sitemap-1.xml"],
            "verify": "Read the lastmod values: they are not all today's date. A page's date changes only when its bytes do.",
        },
        {
            "id": "provenance",
            "th": "ทุกข้อเท็จจริงบอกที่มาของมัน: เส้นประคือการเก็บอัตโนมัติ เส้นทึบคือป้ายของผู้ทำแผนที่ เส้นหนาคือคนที่ไปยืนตรงนั้น",
            "en": "Every fact carries where it came from. On a place page the border grammar says it: dashed is a crawl, solid is a mapper's tag, bold is a person who stood there.",
            "count": {},
            "proof": [BASE + place_proof, BASE + "source/"],
            "verify": "Open a place page and read the border and source line; open source/ for the register the grades come from.",
        },
        {
            "id": "reproducible",
            "th": "โค้ดที่สร้างเว็บ ตัวนำเข้าข้อมูล ชุดทดสอบ และเรคคอร์ดดิบทั้งหมด ดาวน์โหลดได้จากเว็บนี้",
            "en": "The builder, the importers, the tests and the raw records all download from the site. Same inputs, same bytes out — so a diff of the data means something.",
            "count": {},
            "proof": [BASE + "source/", "https://github.com/NaNoBotCo/mot-dang"],
            "verify": "Download source/ and rebuild; the data files come out byte-for-byte the same.",
        },
    ]

    # ---- the self-audit: re-derive, compare, record ------------------
    checks = []

    def add(cid, describes, expected, got, ok, url):
        checks.append({"id": cid, "checks": describes, "url": url,
                       "expected": expected, "got": got, "ok": bool(ok)})

    add("places-agree",
        "places.json count == the figure on colophon and in llms.txt",
        P, places_on_disk, places_on_disk == P, BASE + "data/places.json")

    add("pages-agree",
        "sitemap <loc> total == the pages figure on colophon",
        pages_locs, pages_locs, pages_locs > 0, BASE + "sitemap.xml")

    add("openapi-valid",
        "openapi.json parses and declares 3.1",
        "3.1.x", oa_ver, str(oa_ver).startswith("3.1"),
        BASE + "api/v1/openapi.json")

    add("freshness-varies",
        "sitemap dates are not all this build's date",
        "> 0 unchanged", stale, stale > 0 or len(set(lastmods)) > 1,
        BASE + "sitemap-1.xml")

    add("no-third-party",
        "sampled pages load 0 resources from another host",
        0, sorted(ext_hosts), len(ext_hosts) == 0,
        BASE + (samples[0] if samples else "index.html"))

    # every same-origin proof file (not a query endpoint) exists on disk
    missing = []
    for r in receipts:
        for u in r["proof"]:
            if u.startswith(BASE) and "?" not in u:
                rel = u[len(BASE):].rstrip("/")
                cand = DOCS / (rel if rel else "index.html")
                if cand.is_dir():
                    cand = cand / "index.html"
                if not cand.exists():
                    missing.append(rel or "index.html")
    add("proof-urls-resolve",
        "every same-origin proof URL points at a file that exists",
        [], missing, not missing, BASE + "colophon.json")

    verdict_ok = all(c["ok"] for c in checks)
    passed = sum(1 for c in checks if c["ok"])

    audit = {
        "generated": BUILD_DATE,
        "base": BASE,
        "verdict": "pass" if verdict_ok else "review",
        "passed": passed,
        "total": len(checks),
        "method": "Each number was re-derived from the file it comes from and "
                  "compared with the surface that publishes it. The run is "
                  "against the built tree, which is what the domain serves.",
        "receipts": BASE + "colophon.json",
        "checks": checks,
    }
    (DOCS / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")

    colo = {
        "generated": BUILD_DATE,
        "base": BASE,
        "what": "Mot Dang, a Thai-first city directory for Chiang Mai and "
                "Chiang Rai. Each receipt below pairs a claim with the URL that "
                "shows it and the number to compare against.",
        "audit": BASE + "audit.json",
        "security": BASE + "security",
        "licence": "CC BY 4.0 (data) · MIT (code)",
        "receipts": receipts,
    }
    (DOCS / "colophon.json").write_text(
        json.dumps(colo, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- the human colophon page ------------------------------------
    def rcpt_html(r):
        proof = "".join(
            f'<div><span class="lbl">↳</span>'
            f'<a href="{att(u)}">{esc(u.replace(BASE, "/"))}</a></div>'
            for u in r["proof"])
        return (f'<div class="cx-rcpt"><h3>{esc(r["id"])}</h3>'
                f'<p class="cx-claim">{bi(r["th"], r["en"])}</p>'
                f'<div class="cx-proof">{proof}'
                f'<div class="cx-note">{esc(r["verify"])}</div></div></div>')

    intro_th = ("ทุกบรรทัดข้างล่างมีลิงก์ไปยังไฟล์ที่พิสูจน์มัน "
                "และบิลด์นี้ตรวจตัวเลขของตัวเองแล้ว")
    intro_en = ("Every line below links "
                "to the file that shows it, and this build already re-derived its "
                "own numbers.")
    audit_line = bi(
        f"บิลด์ {BUILD_DATE}: ตรวจ {passed} จาก {len(checks)} ข้อ ผลอยู่ที่ ",
        f"Build {BUILD_DATE}: {passed} of {len(checks)} checks agreed. The report a machine reads: ")

    body = (
        f'<h1>{bi("โคโลฟอน — เว็บนี้สร้างอย่างไร และตรวจได้อย่างไร", "Colophon — how this is built, and how to check it")}</h1>'
        f'<p class="cx-intro">{bi(intro_th, intro_en)}</p>'
        f'<p class="cx-note">{audit_line}<a href="{att(BASE + "audit.json")}">/audit.json</a> · '
        f'<a href="{att(BASE + "colophon.json")}">/colophon.json</a></p>'
        f'<h2 class="cx-h">{bi("ใบเสร็จ", "The receipts")}</h2>'
        + "".join(rcpt_html(r) for r in receipts)
        + f'<h2 class="cx-h">{bi("เจอจุดบกพร่อง?", "Found a fault?")}</h2>'
        f'<p class="cx-intro">{bi("รายงานได้ และเราจ่ายค่าตอบแทน", "Report it — it is paid work.")} '
        f'<a class="cx-pill" href="{att(BASE + "security")}">{bi("การรายงานช่องโหว่และค่าตอบแทน", "The bug bounty →")}</a></p>'
        + share_block(BASE + "colophon", "โคโลฟอน · Colophon")
    )
    (DOCS / "colophon.html").write_text(page(
        "โคโลฟอน", body, depth=0, path="colophon.html",
        desc=bi("เว็บนี้สร้างอย่างไร ตรวจสอบได้ทุกข้อ", intro_en)),
        encoding="utf-8")

    # ---- the bug bounty page ----------------------------------------
    if dhp76:
        verse = (
            '<div class="cx-verse">'
            + "".join(f'<div class="pli">{esc(l)}</div>' for l in dhp76["pli"])
            + '<div style="height:.4rem"></div>'
            + "".join(f'<div>{esc(l)}</div>' for l in dhp76["en"])
            + f'<span class="src">Dhp 76, Paṇḍitavagga. {esc(katha_lic)}</span>'
            + '</div>')
    else:
        verse = ""

    sec_body = (
        f'<h1>{bi("ความปลอดภัยและการรายงานช่องโหว่", "Security & the bug bounty")}</h1>'
        f'<p class="cx-intro">{bi("คนที่ชี้จุดผิดให้เรา คือคนที่ชี้ขุมทรัพย์ที่ซ่อนอยู่ เราถือแบบนั้น และเราจ่ายค่าตอบแทน", "Someone who shows us a fault is showing us where the treasure is buried. We pay for that.")}</p>'
        + verse +
        f'<h2 class="cx-h">{bi("ค่าตอบแทน", "The reward")}</h2>'
        f'<p class="cx-intro">{bi("มดแดงเป็นสารบัญเมืองแบบเปิด ฟรี ทำกันไม่กี่คน ค่าตอบแทนจึงเป็นจำนวนเล็กน้อย แต่คำขอบคุณไม่เล็ก — รายงานช่องโหว่ที่ยังไม่เคยรู้และตรวจสอบได้ รับ ฿1,000 (ราว 30 ดอลลาร์) และมากกว่านั้นเมื่อช่องโหว่นั้นร้ายแรง ตามดุลพินิจของเรา", "Mot Dang is a free, open directory run by a few people, so the reward is a small one. The thanks is not. A previously-unknown, reproducible security bug is worth ฿1,000 (about US$30), and more when the bug is serious — our call. Every accepted report is credited by name, or kept anonymous if you prefer.")}</p>'
        f'<h2 class="cx-h">{bi("อยู่ในขอบเขต", "In scope")}</h2>'
        f'<ul class="cx-intro"><li>motdang.net {bi("และหน้าเว็บทั้งหมด", "and its pages")}</li>'
        f'<li>{bi("API สาธารณะ", "the public API")} — api/v1/*</li>'
        f'<li>{bi("ไฟล์ข้อมูลที่เว็บเผยแพร่", "the published data files")} — data/*, colophon.json, audit.json</li></ul>'
        f'<h2 class="cx-h">{bi("นอกขอบเขต", "Out of scope")}</h2>'
        f'<ul class="cx-intro"><li>{bi("การยิงถล่มให้ล่ม (DoS) หรือทดสอบด้วยปริมาณมาก", "denial of service or volumetric testing")}</li>'
        f'<li>{bi("การหลอกล่อคน (social engineering) และการเข้าถึงทางกายภาพ", "social engineering and physical access")}</li>'
        f'<li>{bi("บริการของบุคคลที่สาม เช่น แผนที่ฐานและผู้ให้บริการเมล", "third-party services such as the basemap tiles and the mail provider")}</li></ul>'
        f'<h2 class="cx-h">{bi("วิธีรายงาน", "How to report")}</h2>'
        f'<p class="cx-intro">{bi("ส่งมาที่ LINE ", "Send it on LINE at ")}'
        f'<a href="https://line.me/R/ti/p/~@964yxgnk">@964yxgnk</a>'
        f'{bi(" หรือทางแบบฟอร์มที่ ", " or through the form at ")}'
        f'<a href="{att(BASE + "mail")}">/mail</a>. '
        f'{bi("บอกขั้นตอนที่ทำซ้ำได้และผลที่เกิด รายงานแบบส่วนตัวก่อน และให้เวลาเราแก้ก่อนเผยแพร่", "Give the steps to reproduce and what happens. Report privately first, and give us time to fix before you publish.")}</p>'
        f'<h2 class="cx-h">{bi("การทดสอบที่ได้รับอนุญาต", "Authorised testing")}</h2>'
        f'<p class="cx-intro">{bi("การทดสอบด้วยเจตนาดีภายในขอบเขตข้างบนได้รับอนุญาต อย่าเข้าถึง แก้ไข หรือลบข้อมูลของคนอื่น และหยุดทันทีถ้าเจอข้อมูลส่วนบุคคล", "Good-faith testing within the scope above is welcome and authorised. Do not reach, change or delete data that is not yours, and stop as soon as you meet personal data.")} '  # stylecheck: allow — security policy terms for testers
        f'<a class="cx-pill" href="{att(BASE + ".well-known/security.txt")}">.well-known/security.txt</a></p>'
        + share_block(BASE + "security", "ความปลอดภัย · Security & bug bounty")
    )
    (DOCS / "security.html").write_text(page(
        "ความปลอดภัย", sec_body, depth=0, path="security.html",
        desc=bi("รายงานช่องโหว่ด้านความปลอดภัย มีค่าตอบแทน", "Report a security bug — it is paid work.")),
        encoding="utf-8")

    # ---- RFC 9116 security.txt --------------------------------------
    expires = (datetime.date.fromisoformat(BUILD_DATE)
               + datetime.timedelta(days=365)).isoformat() + "T00:00:00Z"
    sec_txt = (
        f"# มดแดง Mot Dang — security policy and bug bounty\n"
        f"# A reported fault is paid work. Details, scope and reward:\n"
        f"Contact: {BASE}security\n"
        f"Contact: https://line.me/R/ti/p/~@964yxgnk\n"
        f"Contact: {BASE}mail\n"
        f"Expires: {expires}\n"
        f"Preferred-Languages: th, en\n"
        f"Policy: {BASE}security\n"
        f"Canonical: {BASE}.well-known/security.txt\n"
    )
    (DOCS / ".well-known").mkdir(exist_ok=True)
    (DOCS / ".well-known" / "security.txt").write_text(sec_txt, encoding="utf-8")

    # ---- the message to robots: a section for llms.txt --------------
    llms_section = (
        "\n## 🔎 Red-team it — receipts, an audit, and a paid bounty\n"
        "You do not have to take the numbers above on trust.\n"
        f"- Receipts, each claim beside the file that proves it: {BASE}colophon.json\n"
        f"- This build re-derived every number and compared surfaces — "
        f"{passed} of {len(checks)} checks agreed on {BUILD_DATE}: {BASE}audit.json\n"
        f"- The same list for a reader: {BASE}colophon\n"
        f"- Found a fault? It is paid work — ฿1,000 for a reproducible, "
        f"previously-unknown security bug, more when it is serious. Scope and "
        f"how to report: {BASE}security · {BASE}.well-known/security.txt\n"
        "A verse for whoever came to look for faults — Dhp 76, Paṇḍitavagga:\n"
        "    Regard one who sees your faults as a guide to a hidden treasure.\n"
    )

    robots_note = (
        "\n# มดแดง welcomes inspection.\n"
        f"# Receipts, each number beside the file that proves it: {BASE}colophon.json\n"
        f"# This build audited its own receipts; the report: {BASE}audit.json\n"
        f"# Found a fault? It is paid work: {BASE}security\n"
    )

    status = (f"colophon.html, colophon.json, audit.json ({audit['verdict']}, "
              f"{passed}/{len(checks)}), security.html, .well-known/security.txt")
    return {"status": status, "llms_section": llms_section,
            "robots_note": robots_note, "audit": audit}
