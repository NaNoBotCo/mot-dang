/* ---- WHAT GETS SHARED, AND WHO COMES BACK (Nan, 2026-10-03) ---------------
 * "Sharing should be encouraged and include lots of ways for me to measure."
 *
 * Two sources, both rows in traffic_eye beside the arrivals:
 *
 *   POST /api/share — the Send sheet's events (share_layer.py, sendBeacon):
 *   blob4 "/api/share", blob8 "SHARE", blob9 the event, blob10 the share code,
 *   blob11 the option or channel, blob12 the page, blob13 the code the reader
 *   arrived with (a share of a share), blob14 the place or event key.
 *
 *   land — written beside the arrival row for any request whose query carries
 *   ?s=<code>.<channel>: the link opened, by whoever opened it. A chat app's
 *   preview fetcher counts here as a machine, the reader as a person.
 *
 * double1 is 0 on both, so every SUM(double1) report counts arrivals as
 * before; the count is double5. A code is eight random letters.
 * share_learn.py reads these weekly. */

export const SHARE_EVENTS = new Set(["sheet", "option", "channel", "native-done", "native-cancel",
  "native-fail", "picture", "picture-saved", "calendar", "nudge", "nudge-tap", "nudge-shut",
  "welcome", "arrive"]);
const CODE = /^[a-km-np-z2-9]{8}$/;
const PARAM = /^([a-km-np-z2-9]{8})(?:\.([a-z]{1,2}))?$/;
const KEY = /^[a-z]{2}:[a-z0-9-]{1,90}$/;
const WORD = /^[a-z0-9_-]{1,24}$/;

/* The beacon. Anything malformed is dropped without a word; it answers 204
 * whatever arrives. */
export async function shareSense(request, env, classify) {
  const done = new Response(null, { status: 204, headers: { "cache-control": "no-store" } });
  if (request.method !== "POST" || !env.TRAFFIC) return done;
  let d;
  try {
    const text = await request.text();
    if (text.length > 8192) return done;
    d = JSON.parse(text);
  } catch { return done; }
  if (!d || !Array.isArray(d.ev)) return done;
  const url = new URL(request.url);
  const { category, agent } = classify(request.headers.get("user-agent") || "",
    { asn: request.cf?.asn, headers: request.headers });
  const pg = typeof d.pg === "string" && /^\/[\w\-\/.]{0,95}$/.test(d.pg) ? d.pg : "";
  try {
    for (const e of d.ev.slice(0, 30)) {
      if (!e || !SHARE_EVENTS.has(e.e)) continue;
      const s = typeof e.s === "string" && CODE.test(e.s) ? e.s : "";
      const p = typeof e.p === "string" && CODE.test(e.p) ? e.p : "";
      const k = typeof e.k === "string" && KEY.test(e.k) ? e.k : "";
      const w = typeof e.d === "string" && WORD.test(e.d) ? e.d : "";
      env.TRAFFIC.writeDataPoint({
        blobs: [url.host, category, agent, "/api/share", request.cf?.country || "XX",
                "204", "(same site)", "SHARE", e.e, s, w, pg, p, k],
        doubles: [0, 204, 0, 0, 1],
        indexes: [url.host],
      });
    }
  } catch { /* counting is never worth an error */ }
  return done;
}

/* A request that came in on a shared link. Called from record() with what it
 * already worked out; writes nothing for any other request. */
export function shareLand(env, url, request, response, category, agent, refHost) {
  const m = PARAM.exec(url.searchParams.get("s") || "");
  if (!m || !env.TRAFFIC) return;
  const path = url.pathname.length > 96 ? url.pathname.slice(0, 96) + "…" : url.pathname;
  env.TRAFFIC.writeDataPoint({
    blobs: [url.host, category, agent, "/api/share", request.cf?.country || "XX",
            String(response.status), refHost, "SHARE", "land", m[1], m[2] || "", path, "", ""],
    doubles: [0, response.status, 0, 0, 1],
    indexes: [url.host],
  });
}
