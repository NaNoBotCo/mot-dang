#!/usr/bin/env python3
"""enrich.py — the demand engine. What people actually asked, against what
this corpus can actually answer, turned into work that lands.

WHY THIS EXISTS. Mot Dang has always been enriched from the supply side: a
crawl runs, a shelf fills, a test counts the rows. Nothing has ever been
enriched from the DEMAND side, because nothing kept the demand. Questions
arrived, were answered badly or well, and evaporated. The assistant's own
log is the clearest case: on 2026-09-05 it held 181 searches, 66 distinct
questions and 54 harvested gap candidates — six real ice rinks among them,
named, categorised, with URLs and evidence — and not one had become a
record. The loop was built and had never once been closed.

This closes it, and widens it. Demand comes from four places:

    gpt     Nan's ChatGPT archive, Mar 2023 – Feb 2026. Three years of her
            asking a machine where to find things in this city, before this
            city had a directory. The single largest honest demand corpus
            we will ever get, and it is already on the disk.
    ai      the live assistant: what was asked, what came back, what it
            could not cite, and — this is the new one — what it had to
            GUESS. An answer that says "listed as having English-speaking
            staff" about a record holding no such field is not just a bad
            answer, it is a work item: the corpus lacks a fact a reader
            wanted badly enough that a model invented it.
    asked   data/asked.json, the questions carried in by hand.
    search  site-search misses, when that counter exists.

Then every question is put to the live index, and the failures are sorted
by WHY they failed — because the fix is different for each, and five of the
six are cheap:

    HELD      we already hold a record that answers it, filed elsewhere.
              No crawl. A tag.
    UNINDEXED the answer is in a field the index does not read (facets,
              cuisine, specialty). No crawl. An indexer edit.
    WORD      the term is missing from the thesaurus, so the question and
              the record never meet. No crawl. A line of vocabulary.
    SHELF     nothing in the tree can express the need.
    ABSENT    nothing on this disk answers it. This one needs a source.
    SCOPE     not a Mot Dang question.

    python3 enrich.py run                  harvest, score, classify, report
    python3 enrich.py harvest --source gpt just the archive
    python3 enrich.py score --limit 200    ask the live index
    python3 enrich.py classify
    python3 enrich.py report
    python3 enrich.py status               where the ledger stands

The ledger is `_incoming/enrich/demand.jsonl`, append-only, one row per
distinct question, keyed by a hash of the normalised text so a re-run
updates rather than duplicates. `_incoming/` is gitignored: the archive
holds Nan's unguarded personal and legal talk and none of it leaves this
machine. What ships is the queue and the build file, both written fresh.
"""
import argparse, collections, datetime, glob, hashlib, json, os, pathlib, re, subprocess, sys, time, unicodedata, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "_incoming" / "enrich"
LEDGER = OUT / "demand.jsonl"
TODAY = datetime.date.today().isoformat()

# The transcript folder this reads sits outside the repo and is named only on
# this Mac, in cache/enrich_archive.txt (one line, a path) or MD_ENRICH_ARCHIVE.
_arch = os.environ.get("MD_ENRICH_ARCHIVE") or (
    (HERE / "cache" / "enrich_archive.txt").read_text().strip()
    if (HERE / "cache" / "enrich_archive.txt").exists() else "")
ARCHIVE = pathlib.Path(_arch) if _arch else HERE / "cache" / "enrich-archive-not-set"
WLAI = pathlib.Path.home() / "Developer" / "claude code projects" / "white-label-ai"
SEARCH = "https://ask.motdang.net/api/search"
UA = "mot-dang-enrich/1.0 (+https://motdang.net)"   # the zone 403s python-urllib's default

WEAK = 0.60      # below this the index did not really answer
NOTHING = 0.50   # below this it returned noise

# ---------------------------------------------------------------- demand shapes

# A question that could send someone somewhere. Deliberately generous: the
# scope call is made later, against the corpus, with evidence — not here by
# a regex deciding what Nan is allowed to have wanted.
ASKISH = re.compile(
    r"(^|\s)(where|who|what|which|when|how much|how do i|how can i|is there|are there|any(one|where|body)?\b|"
    r"can i (get|buy|find|rent|hire)|looking for|need (a|an|to find)|recommend|suggest|best place|"
    r"ที่ไหน|ร้านไหน|มีไหม|หา|แนะนำ|อยู่ไหน|ราคาเท่าไห?ร่|ยังไง)", re.I)

# Something you can walk into, buy, hire or be treated by. The list is the
# trade vocabulary of an actual city, not a category tree.
TRADE = re.compile(
    r"\b(shop|store|market|mall|restaurant|cafe|coffee|bar|pub|food|eat|dinner|lunch|breakfast|bakery|"
    r"clinic|hospital|doctor|dentist|pharmacy|chemist|optician|physio|therapist|vet|"
    r"massage|spa|salon|barber|hairdresser|nails|tattoo|gym|yoga|pool|"
    r"hotel|guesthouse|hostel|condo|apartment|rent|room|"
    r"school|class|course|lesson|teacher|tutor|university|"
    r"tailor|laundry|repair|mechanic|garage|locksmith|plumber|electrician|printer|print|copy|framing|"
    r"visa|immigration|bank|atm|post|courier|notary|lawyer|accountant|translation|"
    r"temple|wat|museum|gallery|park|waterfall|hot spring|viewpoint|"
    r"taxi|songthaew|bus|train|airport|scooter|motorbike|bicycle|car|"
    r"buy|sell|price|cost|delivery|open|hours|near|nearby|walking distance)\b|"
    r"(ร้าน|คลินิก|โรงพยาบาล|หมอ|ทันตแพทย์|ร้านขายยา|นวด|สปา|โรงแรม|ที่พัก|คอนโด|หอพัก|โรงเรียน|"
    r"ตลาด|ห้าง|วัด|พิพิธภัณฑ์|น้ำตก|สนามบิน|ซื้อ|ขาย|ราคา|เช่า|ซ่อม|ส่ง)", re.I)

# Where the question is. A Thailand cue makes it ours even without a trade word.
HERE_CUE = re.compile(
    r"\b(chiang\s?mai|chiangmai|cnx|chiang\s?rai|lamphun|lampang|\bpai\b|mae\s?rim|hang\s?dong|"
    r"nimman|santitham|tha\s?phae|old city|doi\s?suthep|san\s?kamphaeng|thailand|thai)\b|"
    r"(เชียงใหม่|เชียงราย|ลำพูน|ลำปาง|นิมมาน|ท่าแพ|เมืองเก่า|ดอยสุเทพ|สันกำแพง|ประเทศไทย)", re.I)

# Attributes a reader asks for that a model will happily invent. Each is a
# claim about a named business, so each needs a field behind it.
ATTRS = {
    "english": r"english[- ]speaking|speaks? english|พูดอังกฤษ",
    "wifi": r"\bwi-?fi\b|ไวไฟ|เน็ต",
    "aircon": r"air[- ]?con(ditioned|ditioning)?\b|aircon|มีแอร์|ติดแอร์|ห้องแอร์",
    "wheelchair": r"wheelchair|step[- ]free|accessible|รถเข็น",
    "open-late": r"open (late|until|till)|late[- ]night|24 ?h(ou)?rs?|เปิดดึก|24 ชั่วโมง",
    "delivery": r"deliver(y|s)?|ส่งถึงบ้าน|เดลิเวอรี",
    "card": r"credit card|accepts? cards?|รับบัตร",
    "parking": r"parking|ที่จอดรถ",
    "women-only": r"women[- ]only|female (only|staff|therapist)|ผู้หญิงล้วน",
    "halal": r"halal|ฮาลาล",
    "vegetarian": r"vegetarian|vegan|มังสวิรัติ|เจ|วีแกน",
    "price": r"how much|cheap|budget|price|cost|ราคา|ถูก",
}

STOP = set("""a an the and or of for in on at to with without my your this that these those is are was were be been
i we you they it he she what which who whom where when why how do does did can could should would will shall
me us them his her its their our there here get got go going near nearby around any some good best better
place places thing things one two find looking need want know like about from into out up down over under
please thanks thank ok okay hi hello""".split())


def norm(q):
    q = unicodedata.normalize("NFKC", q).strip().lower()
    q = re.sub(r"\s+", " ", q)
    return re.sub(r"[^\w฀-๿ ]+", "", q)


def qid(q):
    return hashlib.sha1(norm(q).encode()).hexdigest()[:12]


def content_words(q):
    """The words that carry the ask. Thai runs stay whole — no segmenter here,
    and a wrong split is worse than a long token."""
    words = re.findall(r"[a-zA-Z]{3,}|[฀-๿]{3,}", q.lower())
    return [w for w in dict.fromkeys(words) if w not in STOP]


# ---------------------------------------------------------------- the ledger

def load():
    rows = {}
    if LEDGER.exists():
        for line in LEDGER.open():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            rows[r["id"]] = r          # a later line replaces an earlier one
    return rows


def save(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".tmp")
    with tmp.open("w") as f:
        for r in sorted(rows.values(), key=lambda r: (-(r.get("times") or 1), r["id"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(LEDGER)


def add(rows, q, source, prov, when):
    """One question, however many times it was asked. Provenance accumulates:
    the same question from the archive AND from a live reader is a stronger
    signal than either alone, and the row must be able to say so."""
    q = re.sub(r"\s+", " ", q).strip()
    if not (6 <= len(q) <= 300):
        return False
    i = qid(q)
    r = rows.get(i)
    if not r:
        rows[i] = {"id": i, "q": q, "sources": [source], "provenance": [prov][:1],
                   "times": 1, "first_seen": when, "last_seen": when, "status": "open"}
        return True
    r["times"] = (r.get("times") or 1) + 1
    if source not in r["sources"]:
        r["sources"].append(source)
    if len(r.get("provenance") or []) < 5 and prov not in r["provenance"]:
        r["provenance"].append(prov)
    r["first_seen"] = min(r.get("first_seen") or when, when)
    r["last_seen"] = max(r.get("last_seen") or when, when)
    return False


# ---------------------------------------------------------------- harvest: gpt

USER_BLOCK = re.compile(r"^## USER\b.*?$", re.M)


def user_messages(path):
    """Her side of one conversation. The archive interleaves ## USER and
    ## ASSISTANT blocks; only the first is a person wanting something."""
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return []
    out, keep = [], False
    buf = []
    for line in text.split("\n"):
        if line.startswith("## USER"):
            keep = True
            if buf:
                out.append("\n".join(buf)); buf = []
            continue
        if line.startswith(("## ASSISTANT", "## TOOL", "## SYSTEM")):
            keep = False
            if buf:
                out.append("\n".join(buf)); buf = []
            continue
        if keep:
            buf.append(line)
    if buf:
        out.append("\n".join(buf))
    return out


def harvest_gpt(rows, loose=False):
    """Three years of asking a machine where things are, in a city that had
    no directory. Read every transcript, not only the ones already labelled
    Thailand: the earlier pass filtered to 1,139 conversations first and so
    could never find a demand it had not already assumed."""
    if not ARCHIVE.exists():
        print(f"  archive not found at {ARCHIVE} — skipping (not proof it is absent)")
        return 0
    files = sorted(ARCHIVE.glob("*.md"))
    print(f"  {len(files)} transcripts")
    n = new = 0
    for i, f in enumerate(files):
        if i % 500 == 0:
            print(f"    {i}/{len(files)}", end="\r", flush=True)
        date = f.name[:10] if re.match(r"\d{4}-\d{2}-\d{2}", f.name) else ""
        title = f.name[12:-12].replace("-", " ") if len(f.name) > 24 else f.name
        for msg in user_messages(f):
            for line in re.split(r"(?<=[?.!\n])\s+", msg):
                line = line.strip(" -*·\t")
                if not (6 <= len(line) <= 300) or not ASKISH.search(line):
                    continue
                if not loose and not (TRADE.search(line) or HERE_CUE.search(line)):
                    continue
                n += 1
                if add(rows, line, "gpt", {"conv": title, "date": date}, date or "2023-01-01"):
                    new += 1
    print(f"    {len(files)}/{len(files)}")
    return new


# ---------------------------------------------------------------- harvest: ai

def d1(sql):
    """The assistant's own memory. Read-only here; enrich never writes to it."""
    keys = pathlib.Path.home() / ".config/nanobotco/keys.json"
    env = dict(os.environ, CLOUDFLARE_API_TOKEN=json.load(open(keys))["cloudflare"]["api_token"])
    r = subprocess.run(["npx", "wrangler", "d1", "execute", "white-label-ai", "--remote", "--json",
                        "--command", sql], cwd=WLAI, env=env, capture_output=True, text=True)
    if r.returncode:
        print("  d1 failed:", (r.stderr or "")[-300:])
        return []
    try:
        return json.loads(r.stdout)[0]["results"]
    except Exception:
        return []


def harvest_ai(rows):
    """Questions AND answers. The answers are the half nobody was reading, and
    they carry the sharpest signal in the system: every place an answer had to
    guess is a fact a reader wanted and the corpus could not supply."""
    new = 0

    # 1. every question asked of the assistant
    for r in d1("SELECT question, ts, cues, results, cited FROM search_log ORDER BY rowid"):
        q = (r.get("question") or "").strip()
        if not q:
            continue
        when = (r.get("ts") or TODAY)[:10]
        if add(rows, q, "ai-log", {"ts": when, "cited": r.get("cited")}, when):
            new += 1

    # 2. the gap harvester's own candidates, which name what is missing
    for r in d1("SELECT question, name, category, area, url, evidence, ts, status FROM site_gaps WHERE site='motdang'"):
        q = (r.get("question") or "").strip()
        if not q:
            continue
        when = (r.get("ts") or TODAY)[:10]
        add(rows, q, "ai-gap", {"candidate": r.get("name"), "cat": r.get("category"),
                                "area": r.get("area"), "url": r.get("url"),
                                "evidence": (r.get("evidence") or "")[:160]}, when)
        i = qid(q)
        rows[i].setdefault("candidates", [])
        cand = {"name": r.get("name"), "cat": r.get("category"), "area": r.get("area"),
                "url": r.get("url"), "evidence": (r.get("evidence") or "")[:200]}
        if cand not in rows[i]["candidates"]:
            rows[i]["candidates"].append(cand)

    # 3. the answers. A reader asked for an attribute; did the answer have a
    #    source for it, or did it reach for what it knows about the world?
    msgs = d1("SELECT id, chat_id, role, content, sources, created_at FROM messages ORDER BY id")
    prev_user = {}
    for m in msgs:
        if m.get("role") == "user":
            prev_user[m.get("chat_id")] = (m.get("content") or "").strip()
            continue
        q = prev_user.get(m.get("chat_id"), "")
        if not q:
            continue
        answer = m.get("content") or ""
        try:
            srcs = json.loads(m.get("sources") or "[]")
        except ValueError:
            srcs = []
        src_text = " ".join((s.get("snippet") or "") + " " + (s.get("name") or "") for s in srcs).lower()
        wanted = [a for a, pat in ATTRS.items() if re.search(pat, q, re.I)]
        claimed = [a for a, pat in ATTRS.items() if re.search(pat, answer, re.I)]
        # An attribute the ANSWER states that no source text carries.
        unsupported = [a for a in claimed if not re.search(ATTRS[a], src_text, re.I)]
        when = (m.get("created_at") or TODAY)[:10]
        if wanted or unsupported:
            add(rows, q, "ai-answer", {"ts": when, "wanted": wanted, "unsupported": unsupported}, when)
            i = qid(q)
            if unsupported:
                rows[i]["unsupported"] = sorted(set((rows[i].get("unsupported") or []) + unsupported))
            if wanted:
                rows[i]["wanted"] = sorted(set((rows[i].get("wanted") or []) + wanted))
            new += 1

    # 4. a thumbs-down is a reader saying it plainly
    for r in d1("SELECT m.content AS q, f.vote FROM feedback f "
                "JOIN messages a ON a.id = f.message_id "
                "JOIN messages m ON m.chat_id = a.chat_id AND m.id < a.id AND m.role='user' "
                "WHERE f.vote < 0 GROUP BY f.id"):
        q = (r.get("q") or "").strip()
        if q:
            add(rows, q, "ai-thumbsdown", {"vote": r.get("vote")}, TODAY)
            rows[qid(q)]["thumbs_down"] = True
    return new


def harvest_asked(rows):
    p = HERE / "data" / "asked.json"
    if not p.exists():
        return 0
    try:
        data = json.load(open(p))
    except ValueError:
        return 0
    items = data if isinstance(data, list) else (data.get("asked") or data.get("items") or [])
    n = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        for k in ("q_en", "q_th", "question", "q"):
            q = (it.get(k) or "").strip()
            if q and add(rows, q, "asked", {"key": it.get("key"), "via": it.get("via")},
                         (it.get("asked") or TODAY)[:10]):
                n += 1
    return n


# ---------------------------------------------------------------- score

def ask_index(q, n=5):
    """What the live index returns today. The live one, not a local rebuild:
    the thing readers hit is the thing that has to answer."""
    url = f"{SEARCH}?q={urllib.parse.quote(q[:300])}&n={n}"
    req = urllib.request.Request(url, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def score(rows, limit=0, redo=False):
    todo = [r for r in rows.values()
            if r.get("status") == "open" and (redo or not r.get("scored"))]
    todo.sort(key=lambda r: -(r.get("times") or 1))
    if limit:
        todo = todo[:limit]
    print(f"  {len(todo)} to score")
    for i, r in enumerate(todo):
        try:
            j = ask_index(r["q"])
        except Exception as e:
            print(f"    {r['q'][:50]}: {e}")
            time.sleep(2)
            continue
        hits = j.get("results") or []
        r["best"] = hits[0]["score"] if hits else 0
        r["top"] = [{"score": h["score"], "title": h["title"], "url": h["url"]} for h in hits[:3]]
        r["scored"] = TODAY
        if i % 10 == 0:
            print(f"    {i}/{len(todo)}", end="\r", flush=True)
        time.sleep(0.15)
    print(f"    {len(todo)}/{len(todo)}")
    return len(todo)


# ---------------------------------------------------------------- classify

def corpus():
    """One pass over the canonical records, kept in memory: what each record
    calls itself, and the four fields the assistant's index never reads."""
    names, facets, cuisine, specialty, facility, labels = [], collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter(), set()
    for p in ("cm", "cr"):
        f = HERE / "data" / "canonical" / f"{p}.json"
        if not f.exists():
            continue
        for d in json.load(open(f)):
            a = d.get("attrs") or {}
            blob = " ".join(str(d.get(k) or "") for k in ("name", "nameTh", "nameEn")).lower()
            names.append((blob, d.get("name") or "", list(d.get("cat") or []), list(d.get("sub") or [])))
            for k in (a.get("facets") or {}):
                facets[k] += 1
            for c in str(a.get("cuisine") or "").split(";"):
                if c.strip():
                    cuisine[c.strip().lower()] += 1
            for s in (a.get("specialty") or []):
                specialty[str(s).lower()] += 1
            if a.get("facilityType"):
                facility[str(a["facilityType"]).lower()] += 1
    lab = json.load(open(HERE / "data" / "curated" / "index_labels.json"))
    for k, v in lab["labels"].items():
        labels.add(k.lower())
        for w in v:
            labels.add(str(w).lower())
    for k, v in lab["synonyms"].items():
        for w in v:
            labels.add(str(w).lower())
    return {"names": names, "facets": facets, "cuisine": cuisine,
            "specialty": specialty, "facility": facility, "labels": labels}


def classify(rows, c=None):
    """Why it failed — and the evidence, because a class without evidence is
    a guess with a label on it. Absence is only ever reported as 'nothing on
    this disk', never as 'this does not exist'."""
    c = c or corpus()
    done = 0
    for r in rows.values():
        if r.get("status") != "open" or not r.get("scored"):
            continue
        q, best = r["q"], (r.get("best") or 0)
        words = content_words(q)
        local = bool(TRADE.search(q) or HERE_CUE.search(q))

        if best >= WEAK:
            r["class"], r["evidence"] = "ANSWERED", []
            r["classified"] = TODAY
            done += 1
            continue

        ev = []
        # Does a record already call itself this? The cheapest fix there is.
        held = []
        for blob, name, cat, sub in c["names"]:
            if any(w in blob for w in words if len(w) >= 4):
                held.append((name, (cat or [""])[0], (sub or [""])[0]))
                if len(held) >= 8:
                    break
        # Is the answer in a field the index throws away?
        unindexed = []
        for w in words:
            for field, counter in (("facets", c["facets"]), ("cuisine", c["cuisine"]),
                                   ("specialty", c["specialty"]), ("facilityType", c["facility"])):
                for key, n in counter.items():
                    if w == key or (len(w) >= 4 and w in key):
                        unindexed.append(f"{field}.{key} on {n} records")
        unindexed = sorted(set(unindexed))[:6]
        # Attributes the assistant had to invent are unindexed by definition.
        for a in (r.get("unsupported") or []):
            unindexed.append(f"the answer claimed '{a}' with no source carrying it")
        # Is the word simply not in the thesaurus?
        unknown = [w for w in words if len(w) >= 4 and w not in c["labels"]]

        if not local and best < NOTHING:
            r["class"] = "SCOPE"
        elif unindexed:
            r["class"] = "UNINDEXED"
            ev = unindexed
        elif held:
            r["class"] = "HELD"
            ev = [f"{n} (filed {cat}/{sub})" for n, cat, sub in held]
        elif r.get("candidates"):
            r["class"] = "ABSENT"
            ev = [f"{x['name']} — {x.get('url','')}" for x in r["candidates"][:4]]
        elif unknown and best >= NOTHING:
            r["class"] = "WORD"
            ev = [f"not in any label or synonym: {', '.join(unknown[:5])}"]
        else:
            r["class"] = "ABSENT"
            ev = ["nothing on this disk matches these words: " + ", ".join(words[:6])]
        r["evidence"] = ev
        r["classified"] = TODAY
        done += 1
    return done


# ---------------------------------------------------------------- report

ORDER = ["UNINDEXED", "HELD", "WORD", "SHELF", "ABSENT", "ANSWERED", "SCOPE"]
BLURB = {
    "UNINDEXED": "The answer is already on this disk, in a field the index does not read.\n"
                 "  Fix: one edit to white-label-ai/scripts/index_motdang.py, then re-index.",
    "HELD":      "A record we already hold answers it, filed on another shelf.\n"
                 "  Fix: a tag, through data/curated/shelves.json. No crawl.",
    "WORD":      "The word never reaches the record. The question and the listing\n"
                 "  are about the same thing in different scripts or registers.\n"
                 "  Fix: a line in the thesaurus / index_labels synonyms.",
    "SHELF":     "Nothing in the tree can express this need.\n"
                 "  Fix: a child shelf in data/categories.json, with its test.",
    "ABSENT":    "Nothing on this disk answers it. This is the only class that\n"
                 "  needs a source — a register, a directory, a crawl.",
    "ANSWERED":  "The index already answers this. Kept as the control group:\n"
                 "  if this list shrinks, something regressed.",
    "SCOPE":     "Not a Mot Dang question. Listed so the harvest can be audited,\n"
                 "  never silently dropped.",
}


def report(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    by = collections.defaultdict(list)
    for r in rows.values():
        if r.get("status") == "open" and r.get("class"):
            by[r["class"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: (-(r.get("times") or 1), r.get("best") or 0))

    src = collections.Counter(s for r in rows.values() for s in (r.get("sources") or []))
    total = len(rows)
    scored = sum(1 for r in rows.values() if r.get("scored"))

    lines = []
    W = 78
    lines.append("MOT DANG — WHAT PEOPLE ASKED, AND WHAT THIS CORPUS CAN ANSWER")
    lines.append(f"Built {TODAY} by enrich.py. Every number computed today.")
    lines.append("")
    lines.append(f"{total} distinct questions harvested, {scored} put to the live index.")
    lines.append("Where they came from: " + " · ".join(f"{k} {n}" for k, n in src.most_common()))
    lines.append("")
    counts = {k: len(by.get(k, [])) for k in ORDER}
    answered = counts.get("ANSWERED", 0)
    inscope = sum(v for k, v in counts.items() if k != "SCOPE")
    if inscope:
        lines.append(f"Of {inscope} in-scope questions the index answers {answered} "
                     f"({round(100*answered/inscope)}%). The other {inscope-answered} are the work.")
    lines.append("")
    lines.append("  " + "  ".join(f"{k} {counts.get(k,0)}" for k in ORDER))
    lines.append("")
    lines.append("The order below is the order to work in: the first three classes need")
    lines.append("no new data at all, only that we read what we already hold.")

    for k in ORDER:
        items = by.get(k) or []
        if not items:
            continue
        lines.append("")
        lines.append("=" * W)
        lines.append(f"{k} — {len(items)}")
        lines.append("=" * W)
        lines.append("  " + BLURB[k].replace("\n", "\n"))
        lines.append("")
        show = items if k in ("UNINDEXED", "WORD", "SHELF") else items[:40]
        for r in show:
            times = r.get("times") or 1
            best = r.get("best") or 0
            where = "/".join(r.get("sources") or [])
            lines.append(f"  {r['q'][:96]}")
            lines.append(f"      asked {times}× · best match {best:.2f} · via {where}")
            for e in (r.get("evidence") or [])[:5]:
                lines.append(f"      → {e}")
            if r.get("unsupported"):
                lines.append(f"      ⚠ the assistant asserted {', '.join(r['unsupported'])} with nothing behind it")
            lines.append("")
        if len(items) > len(show):
            lines.append(f"  … and {len(items)-len(show)} more in demand.jsonl")

    txt = OUT / f"queue-{TODAY}.txt"
    txt.write_text("\n".join(lines) + "\n")

    builds = {
        "generated": TODAY,
        "counts": counts,
        "unindexed_fields": sorted({e.split(" on ")[0] for r in by.get("UNINDEXED", [])
                                    for e in (r.get("evidence") or []) if " on " in e}),
        "shelf_candidates": [{"q": r["q"], "times": r.get("times"), "evidence": r.get("evidence")}
                             for r in by.get("HELD", [])[:200]],
        "vocabulary": [{"q": r["q"], "missing": r.get("evidence")} for r in by.get("WORD", [])[:200]],
        "sources_needed": [{"q": r["q"], "times": r.get("times"),
                            "candidates": r.get("candidates") or []} for r in by.get("ABSENT", [])[:200]],
    }
    js = OUT / f"builds-{TODAY}.json"
    js.write_text(json.dumps(builds, ensure_ascii=False, indent=1))
    return txt, js, counts


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="the demand engine")
    ap.add_argument("command", choices=["run", "harvest", "score", "classify", "report", "status"])
    ap.add_argument("--source", default="all", help="gpt | ai | asked | all")
    ap.add_argument("--limit", type=int, default=0, help="how many to score this pass")
    ap.add_argument("--redo", action="store_true", help="re-score rows already scored")
    ap.add_argument("--loose", action="store_true", help="harvest questions with no trade or place word")
    a = ap.parse_args()

    rows = load()
    before = len(rows)

    if a.command in ("run", "harvest"):
        print("HARVEST")
        if a.source in ("all", "gpt"):
            print(" gpt — the ChatGPT archive")
            harvest_gpt(rows, a.loose)
        if a.source in ("all", "ai"):
            print(" ai — the live assistant")
            harvest_ai(rows)
        if a.source in ("all", "asked"):
            print(" asked — data/asked.json")
            harvest_asked(rows)
        save(rows)
        print(f"  {len(rows)} distinct questions ({len(rows)-before} new)")

    if a.command in ("run", "score"):
        print("SCORE")
        score(rows, a.limit or (400 if a.command == "run" else 0), a.redo)
        save(rows)

    if a.command in ("run", "classify"):
        print("CLASSIFY")
        n = classify(rows)
        save(rows)
        print(f"  {n} classified")

    if a.command in ("run", "report"):
        print("REPORT")
        txt, js, counts = report(rows)
        print("  " + "  ".join(f"{k} {counts.get(k,0)}" for k in ORDER))
        print(f"  {txt}")
        print(f"  {js}")

    if a.command == "status":
        scored = sum(1 for r in rows.values() if r.get("scored"))
        cls = collections.Counter(r.get("class") or "unclassified" for r in rows.values())
        src = collections.Counter(s for r in rows.values() for s in (r.get("sources") or []))
        print(f"{len(rows)} questions · {scored} scored")
        print("sources:", dict(src))
        print("classes:", dict(cls))


if __name__ == "__main__":
    main()
