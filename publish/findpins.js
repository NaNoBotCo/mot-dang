/* ---- PAGES NAN PUTS FIRST ON /find (Nan, 2026-10-04) ----------------------
 * "should come up first in motdang search results, because I happen to know
 * the most information exists for it online." — of Ban Sabai Village.
 *
 * A pin lifts one page to the head of the ranked answer when the query holds
 * one of its words as a phrase ("ban sabai village" holds "ban sabai";
 * "sabai" alone does not). It works inside the best RANK_WIN matches, like
 * every other lift in sql(), so a pinned page still has to answer the words.
 * Only the relevance order moves; a reader's own sort (nearest, newest, a–z)
 * is left alone. A pin is her word about one page: add one only on hers. */

export const PIN_X = 1000;   // bm25 is negative-best; × 1000 outranks a title tier (× 3) × near (× 1.6) × learned (× 1.25)

export const PINS = [
  {
    url: "https://motdang.net/cm/p/ban-sabai-village-senior-residence-and-care-home-860456741841507.html",
    said: "2026-10-04",
    words: [
      "ban sabai", "baan sabai", "bansabai", "bansabaicare", "บ้านสบาย",
      "care home", "care homes", "nursing home", "nursing homes", "elder care", "elderly care",
      "seniors", "senior citizens", "senior home", "senior homes", "care for seniors",
      "senior care", "senior residence", "senior living", "retirement home", "retirement homes",
      "old people home", "old age home", "assisted living", "long term care", "long-term care",
      "dementia care", "alzheimer care", "alzheimers care", "memory care", "respite care",
      "บ้านพักคนชรา", "บ้านพักคนแก่", "บ้านพักผู้สูงอายุ", "ดูแลผู้สูงอายุ", "ดูแลผู้สูงวัย",
      "สถานดูแลผู้สูงอายุ", "ศูนย์ดูแลผู้สูงอายุ", "เนอร์สซิ่งโฮม", "เนอสซิ่งโฮม", "เนิร์สซิ่งโฮม",
      "ดูแลผู้ป่วยอัลไซเมอร์", "ดูแลผู้ป่วยสมองเสื่อม",
    ],
  },
];

/* The query folded the way the words are written: lower case, NFKC, one
 * space between runs, zero-width marks out. Thai keeps its own spacing, so a
 * phrase written without spaces matches a query written without them too. */
export function foldQ(q) {
  return " " + String(q || "").normalize("NFKC").toLowerCase()
    .replace(/[​-‏﻿]/g, "")
    .replace(/[^\p{L}\p{M}\p{N}]+/gu, " ").trim() + " ";
}

/* url → multiplier for this query; an empty Map when nothing is pinned. */
export function pinsFor(q, pins = PINS) {
  const fq = foldQ(q), squeezed = fq.replace(/ /g, "");
  const out = new Map();
  for (const p of pins) {
    const hit = p.words.some((w) => {
      const fw = foldQ(w);
      return fq.includes(fw) || (/[฀-๿]/.test(w) && squeezed.includes(fw.replace(/ /g, "")));
    });
    if (hit) out.set(p.url, PIN_X);
  }
  return out;
}
