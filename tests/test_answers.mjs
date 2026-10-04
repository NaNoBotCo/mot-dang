// The answer box on motdang.net/find: which answer each query reaches, across the visa, compound
// and care files, and which queries must reach none. Reads the files as they are on disk.
//   node tests/test_answers.mjs
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const src = fs.readFileSync(path.join(ROOT, "publish/fleetsearch.js"), "utf8");
const fold = src.match(/const fold = [\s\S]*?\.trim\(\);/)[0];
const blk = src.slice(src.indexOf("function normAnswers"), src.indexOf("function answerPanel")).replace(/export /g, "");
const match = new Function("docs", "q", fold + "\n" + blk + "\nreturn answerMatch(q, docs);");

const files = ["docs/sites/long-stay/answers.json", "data/curated/answers_compounds.json", "data/curated/answers_health.json"];
const docs = files.filter((f) => fs.existsSync(path.join(ROOT, f)))
  .map((f) => JSON.parse(fs.readFileSync(path.join(ROOT, f), "utf8")));
const norm = new Function("doc", fold + "\n" + blk + "\nreturn normAnswers(doc);");
const D = docs.map(norm).filter(Boolean);

const want = {
  "retatrutide": "c-retatrutide", "retatrutid": "c-retatrutide", "reta peptide": "c-retatrutide",
  "semaglutid": "c-semaglutide", "ozempic": "c-semaglutide", "mounjaro": "c-tirzepatide",
  "bpc-157": "c-bpc-157", "bpc 157 chiang mai": "c-bpc-157", "tb500": "c-tb-500",
  "anavar": "c-oxandrolone", "test e": "c-testosterone", "testosterone injection": "c-testosterone",
  "rad 140": "c-rad-140", "mk-677": "c-mk-677", "ovestin": "c-estriol", "spironolactone": "c-spironolactone",
  "adderall": "c-amphetamine", "ritalin": "c-methylphenidate", "humira": "c-adalimumab", "ilumya": "c-tildrakizumab",
  "kratom": "c-kratom", "กระท่อม": "c-kratom", "prep hiv": "c-emtricitabine-tenofovir",
  "vaginoplasty thailand": "vaginoplasty", "ftm top surgery thailand": "top", "hemiarthroplasty thailand": "joint",
  "english speaking dentist": "dental", "is this clinic reviews": "vet", "วัยทอง": "menopause",
  "medical tourism chiang mai": "care", "chiang mai visa desk": "visa", "90 day report": "report90",
};
const none = ["physical therapy", "massage near tha phae gate", "restaurant reviews", "animal hospital", "vet clinic",
  "rajavej hospital", "hair extension", "condo for rent", "coffee", "knee rehab", "is it safe to swim", "khao soi",
  "transport to airport", "กายภาพบำบัด", "power buy", "test drive", "deca joint", "primo pizza", "eq bar", "tren station"];

let bad = 0;
for (const [q, id] of Object.entries(want)) {
  const h = match(D, q);
  const got = h ? h.a.id : "-";
  if (got !== id) { bad++; console.log(`  FAIL ${JSON.stringify(q)} → ${got}, want ${id}`); }
}
for (const q of none) {
  const h = match(D, q);
  if (h) { bad++; console.log(`  FAIL ${JSON.stringify(q)} → ${h.a.id}, want none`); }
}
console.log(bad ? `${bad} FAILED` : `answers: ok (${Object.keys(want).length} reach, ${none.length} stay quiet)`);
process.exit(bad ? 1 : 0);
