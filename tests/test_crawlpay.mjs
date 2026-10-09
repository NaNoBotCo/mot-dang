// node tests/test_crawlpay.mjs — the crawl test's arms, ask and listen.
import assert from "node:assert/strict";
import { armOf, slot, crawlAsk, crawlListen, TRAINING } from "../publish/crawlpay.js";

const req = (path, ua, h = {}) => new Request("https://motdang.net" + path, { headers: { "user-agent": ua, ...h } });
const ON = { CRAWLPAY_ASK: "on", CRAWLPAY_PRICE_LO: "USD 0.001", CRAWLPAY_PRICE_HI: "USD 0.01" };

// arms: stable, about one in ten asked, open paths never
assert.equal(armOf("/robots.txt"), "open");
assert.equal(armOf("/sitemap-1.xml"), "open");
assert.equal(slot("/cm/p/x.html"), slot("/cm/p/x.html"));
let asked = 0; const N = 20000;
for (let i = 0; i < N; i++) if (armOf(`/cm/p/place-${i}.html`).startsWith("ask")) asked++;
assert.ok(asked / N > 0.08 && asked / N < 0.12, `asked share ${asked / N}`);

const askPath = [...Array(500).keys()].map(i => `/cm/p/p${i}.html`).find(p => armOf(p) === "ask-hi");
const ctlPath = [...Array(500).keys()].map(i => `/cm/p/p${i}.html`).find(p => armOf(p) === "control");

// ask: training crawler on the slice gets 402 + crawler-price
let r = crawlAsk(req(askPath, "GPTBot"), ON, "ai", "GPTBot");
assert.equal(r.status, 402);
assert.equal(r.headers.get("crawler-price"), "USD 0.01");
// control page, person-triggered fetcher, search engine, off switch, missing price: no 402
assert.equal(crawlAsk(req(ctlPath, "GPTBot"), ON, "ai", "GPTBot"), null);
assert.equal(crawlAsk(req(askPath, "ChatGPT-User"), ON, "ai", "ChatGPT-User"), null);
assert.equal(crawlAsk(req(askPath, "OAI-SearchBot"), ON, "ai", "OAI-SearchBot"), null);
assert.equal(crawlAsk(req(askPath, "Googlebot"), ON, "search", "Googlebot"), null);
assert.equal(crawlAsk(req(askPath, "GPTBot"), { ...ON, CRAWLPAY_ASK: "off" }, "ai", "GPTBot"), null);
assert.equal(crawlAsk(req(askPath, "GPTBot"), { ...ON, CRAWLPAY_PRICE_HI: "" }, "ai", "GPTBot"), null);
assert.equal(crawlAsk(new Request("https://motdang.net" + askPath, { method: "POST", headers: { "user-agent": "GPTBot" } }), ON, "ai", "GPTBot"), null);
assert.equal(crawlAsk(req(askPath, "GPTBot"), { ...ON, CRAWLPAY_UNTIL: "2020-01-01T00:00:00Z" }, "ai", "GPTBot"), null);
assert.equal(crawlAsk(req(askPath, "GPTBot"), { ...ON, CRAWLPAY_UNTIL: "2099-01-01T00:00:00Z" }, "ai", "GPTBot").status, 402);
assert.ok(!TRAINING.has("OAI-SearchBot") && !TRAINING.has("ChatGPT-User"));

// listen: a row only when a request says it can pay or signs itself
const rows = []; const env = { TRAFFIC: { writeDataPoint: d => rows.push(d) } };
crawlListen(req(ctlPath, "GPTBot"), new Response("x"), env, "ai", "GPTBot", 3);
assert.equal(rows.length, 0);
crawlListen(req(askPath, "GPTBot", { "crawler-max-price": "USD 0.005" }), new Response("x", { status: 402 }), env, "ai", "GPTBot", 3);
crawlListen(req(ctlPath, "ChatGPT-User", { "signature-agent": '"https://chatgpt.com"', "signature-input": "sig1=()" }), new Response("x"), env, "ai", "ChatGPT-User", 3);
assert.equal(rows.length, 2);
assert.deepEqual(rows[0].blobs.slice(8, 11), ["crawlpay", "ask-hi", "crawler-max-price=USD 0.005"]);
assert.equal(rows[0].doubles[0], 0); // arrivals unchanged
assert.equal(rows[1].blobs[11], '"https://chatgpt.com"');
crawlListen(req(ctlPath, "GPTBot", { "x-payment": "abc" }), new Response("x"), {}, "ai", "GPTBot", 3); // no binding: no throw
console.log("crawlpay: ok");
