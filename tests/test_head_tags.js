/* The tags publish/worker.js writes into every page's <head>: the notranslate
 * pair and its script (Nan, 2026-09-23), the Travelpayouts site script for
 * project Motdang 581229 (Nan, 2026-10-11), and the reader's-city meta.
 *
 * An element holds one end-tag handler. A second onEndTag on <head> silently
 * replaces the first, and the first handler's tags then land before <body>
 * instead; that happened until 2026-10-11. Plain node has no HTMLRewriter, so
 * the source is read here; --live fetches real pages and looks for each tag
 * inside <head>, once.
 *
 *     node tests/test_head_tags.js
 *     node tests/test_head_tags.js --live      (after a Worker deploy)
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = readFileSync(join(ROOT, "publish/worker.js"), "utf8");

let failures = 0;
async function t(name, fn) {
  try { await fn(); console.log("  ok   " + name); }
  catch (e) { failures++; console.log("  FAIL " + name + "\n       " + e.message); }
}
const must = (c, m) => { if (!c) throw new Error(m); };

await t("the Travelpayouts script is written for project 581229", () => {
  must(/const TP_SCRIPT = '[^\n]*tp-em\.com\/NTgxMjI5\.js\?t=581229/.test(src), "TP_SCRIPT is gone or changed");
  must(/\(tp \? "" : TP_SCRIPT\)/.test(src), "TP_SCRIPT is not among the tags noTranslate writes");
});

await t("one end-tag handler on <head>", () => {
  const n = (src.match(/\.onEndTag\(/g) || []).length;
  must(n === 1, `${n} onEndTag calls; a second one on <head> replaces noTranslate's — pass it to noTranslate as atHeadEnd`);
});

if (process.argv.includes("--live")) {
  const pages = ["/", "/sites/bum-gun/", "/cm/medical/index.html"];
  const tags = { travelpayouts: "tp-em.com/NTgxMjI5.js", notranslate: 'content="notranslate"', city: 'name="md-where"' };
  for (const p of pages) {
    await t(`live ${p}: every tag inside <head>, the script once`, async () => {
      const html = await (await fetch(`https://motdang.net${p}`)).text();
      const end = html.indexOf("</head>");
      for (const [k, v] of Object.entries(tags)) {
        const i = html.indexOf(v);
        must(i >= 0, `${k} missing`);
        must(i < end, `${k} is after </head>`);
      }
      must(html.split(tags.travelpayouts).length === 2, "travelpayouts script written more than once");
    });
  }
}

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
