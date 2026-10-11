/* WHICH ROBOTS PAY, AND HOW MUCH (Nan, 2026-10-04: "I'm not sure which robots
 * should pay or how much. Let's run a test.")
 *
 * motdang.net applied to Cloudflare's pay-per-crawl beta the same day. Until
 * Cloudflare admits the site, no crawler can pay it — Cloudflare is the one
 * that collects. So this test measures the two things that can be measured
 * now, and the price question waits for the beta:
 *
 *   1. LISTEN (always on). A crawler that is ready to pay says so in its
 *      request: `crawler-max-price` / `crawler-exact-price` (Cloudflare's pay
 *      per crawl), `signature-agent` + `signature-input` (Web Bot Auth, the
 *      signed identity pay per crawl requires), `x-payment` (x402). Any
 *      request carrying one gets a row of its own in traffic_eye: blob9
 *      "crawlpay", blob10 the arm, blob11 the price header, blob12 the
 *      signature agent. double1 is 0 so every SUM(double1) still counts
 *      arrivals exactly as before; double5 is 1.
 *
 *   2. ASK (only while CRAWLPAY_ASK is "on"). A slice of pages — one path in
 *      ten, picked by a stable hash so the same page is always in or out —
 *      answers the training crawlers in TRAINING with 402 Payment Required
 *      and a `crawler-price` header, the shape pay per crawl uses. Half the
 *      slice shows CRAWLPAY_PRICE_LO, half CRAWLPAY_PRICE_HI. The other nine
 *      pages in ten are the control. The arrival row already records status
 *      402, so a crawler's behaviour on the slice (retry, give up, keep
 *      coming, send a price) can be read against the control.
 *
 * Left out of the ask, always: search engines, link previews, and the
 * fetchers that act for a person asking a question right now (ChatGPT-User,
 * Claude-User, Perplexity-User…) and the answer engines' own indexers
 * (OAI-SearchBot, PerplexityBot, Claude-SearchBot) — those are the ones that
 * can send a reader back. robots.txt, llms.txt and the sitemaps always answer.
 *
 * Like the counter, nothing here can break a page: any error means the
 * request is served as if this file did not exist.
 */

export const TRAINING = new Set([
  "meta-externalagent", "GPTBot", "Amazonbot", "Bytespider", "ClaudeBot",
  "anthropic-ai", "CCBot", "cohere-ai", "AI2Bot", "Diffbot", "Timpibot",
  "Omgilibot", "ImagesiftBot", "Kangaroo Bot", "Webzio",
]);

const OPEN = /^\/(robots\.txt|llms\.txt|sitemap[\w-]*\.xml|favicon\.ico|google[0-9a-f]+\.html)$/;

/* FNV-1a over the path: cheap, stable across deploys, and the report
 * (tools/crawlpay_report.py) computes the same number to find the slice. */
export function slot(pathname) {
  let h = 0x811c9dc5;
  for (let i = 0; i < pathname.length; i++) {
    h ^= pathname.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h % 20; // 0 → lo price, 1 → hi price, 2–19 → control
}

export function armOf(pathname) {
  if (OPEN.test(pathname)) return "open";
  const s = slot(pathname);
  return s === 0 ? "ask-lo" : s === 1 ? "ask-hi" : "control";
}

const PAY_HEADERS = ["crawler-max-price", "crawler-exact-price", "x-payment"];

function payHeader(headers) {
  for (const h of PAY_HEADERS) {
    const v = headers.get(h);
    if (v) return `${h}=${v}`.slice(0, 64);
  }
  return "";
}

/* 2. ASK — returns a 402 Response for a training crawler on the slice, else null. */
export function crawlAsk(request, env, category, agent) {
  try {
    if (env.CRAWLPAY_ASK !== "on") return null;
    if (env.CRAWLPAY_UNTIL && Date.now() > Date.parse(env.CRAWLPAY_UNTIL)) return null;
    if (category !== "ai" || !TRAINING.has(agent)) return null;
    if (request.method !== "GET" && request.method !== "HEAD") return null;
    const arm = armOf(new URL(request.url).pathname);
    if (arm !== "ask-lo" && arm !== "ask-hi") return null;
    const price = arm === "ask-lo" ? env.CRAWLPAY_PRICE_LO : env.CRAWLPAY_PRICE_HI;
    if (!price) return null;
    return new Response(
      `402 Payment Required\nPrice per request: ${price}\nLicensing: nan@motdang.net\n`,
      {
        status: 402,
        headers: {
          "crawler-price": price,
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "no-store",
        },
      },
    );
  } catch {
    return null;
  }
}

/* 1. LISTEN — one extra row when a request says it can pay or signs itself. */
export function crawlListen(request, response, env, category, agent, ms) {
  if (!env.TRAFFIC) return;
  const h = request.headers;
  const pay = payHeader(h);
  const sig = (h.get("signature-agent") || (h.get("signature-input") ? "(signed, no agent)" : "")).slice(0, 96);
  if (!pay && !sig) return;
  const url = new URL(request.url);
  env.TRAFFIC.writeDataPoint({
    blobs: [url.host, category, agent, url.pathname.slice(0, 96), request.cf?.country || "XX",
            String(response.status), "", request.method, "crawlpay", armOf(url.pathname), pay, sig],
    doubles: [0, response.status, ms, 0, 1],
    indexes: [url.host],
  });
}
