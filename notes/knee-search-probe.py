#!/usr/bin/env python3
"""Run arbitrary queries through the shipped search block. Reuses the
test_search harness wholesale so the measurement is the real code."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, "tests")
import test_search as T

QUERIES = [
    "viscosupplementation", "knee injection", "knee", "hyaluronic acid",
    "orthopedic", "orthopaedic", "ortho", "orthopedic surgeon", "bone doctor",
    "arthritis", "osteoarthritis", "joint pain",
    "ฉีดน้ำเลี้ยงข้อเข่า", "ฉีดน้ำไขข้อ", "น้ำไขข้อเทียม", "ไฮยาลูรอน",
    "ข้อเข่าเสื่อม", "ข้อเข่า", "เข่า", "กระดูกและข้อ", "กระดูก",
    "หมอกระดูก", "ออร์โธปิดิกส์", "ปวดเข่า", "ข้ออักเสบ", "รูมาตอยด์",
    "physiotherapy", "กายภาพบำบัด",
]

idx = json.load(open(T.INDEX, encoding="utf-8"))
NAME = {e["id"]: (e.get("n") or e.get("e") or "?") for e in idx}
js = T.extract_js()
thes = json.load(open("data/search_thesaurus.json", encoding="utf-8"))["groups"]
seg = open("data/search_segdict.txt", encoding="utf-8").read()
shelves = json.load(open("data/search_shelves.json", encoding="utf-8"))
panels = json.load(open("data/curated/search_panels.json", encoding="utf-8"))
cfg = json.load(open("data/categories.json", encoding="utf-8"))
catwords = {c["key"]: f'{c["th"]} · {c["en"]}' for c in cfg["categories"]}
subwords = {}
for c in cfg["categories"]:
    for ch in c.get("children") or []:
        k = (ch.get("match") or {}).get("sub") or ch.get("key")
        if k:
            subwords.setdefault(k, f'{ch.get("th","")} {ch.get("en","")}'.strip())
harness = (
    "import fs from 'fs';\nimport {createRequire} from 'module';\n"
    "const require=createRequire(import.meta.url);\n"
    f"const SEARCHCORE=require({json.dumps(os.path.abspath('assets/searchcore.js'))});\n"
    f"const MD_CATWORDS={json.dumps(catwords, ensure_ascii=False)};\n"
    f"const MD_SUBWORDS={json.dumps(subwords, ensure_ascii=False)};\n"
    f"const thesDoc={{groups:{json.dumps(thes, ensure_ascii=False)}}};\n"
    f"const segText={json.dumps(seg, ensure_ascii=False)};\n"
    f"const shelfDoc={json.dumps(shelves, ensure_ascii=False)};\n"
    f"const panelDoc={json.dumps(panels, ensure_ascii=False)};\n"
    f"const idx=JSON.parse(fs.readFileSync({json.dumps(T.INDEX)},'utf8'));\n"
    "function search(q){\n" + js + "\n"
    "return {n:found.length,tier:found.length?found[0].tier:null,"
    "ids:hits.slice(0,6).map(e=>e.id),panel:panel?panel.id:null};}\n"
    "const out=JSON.parse(process.argv[2]).map(q=>search(q));\n"
    "console.log(JSON.stringify(out));\n")
with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
    fh.write(harness); path = fh.name
try:
    p = subprocess.run(["node", path, json.dumps(QUERIES)], capture_output=True,
                       text=True, timeout=300)
finally:
    os.unlink(path)
if p.returncode:
    print(p.stderr[-2000:]); sys.exit(1)
for q, r in zip(QUERIES, json.loads(p.stdout)):
    top = " · ".join(NAME.get(i, i)[:34] for i in r["ids"][:4])
    print(f"{q:24} n={r['n']:<6} tier={r['tier'] or '-':8} panel={r['panel'] or '-':13} {top}")
