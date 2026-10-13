#!/usr/bin/env node
// worker-media: the four picture prefixes from the bucket, everything else to the site Worker.
//
//   node tests/test_media_worker.mjs
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join, resolve } from "node:path";
import assert from "node:assert/strict";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.MD_ROOT ? resolve(process.env.MD_ROOT) : resolve(HERE, "..");
const { serve, keyOf } = await import(pathToFileURL(join(ROOT, "worker-media/src/index.js")).href);

const BODY = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
function env(objects = { "photos/a.jpg": BODY, "streetphotos/cm-x.jpg": BODY, "og/c.png": BODY, "inat/1.jpg": BODY }) {
  const asked = [];
  return {
    asked,
    MEDIA: {
      async get(key, opts) {
        const o = objects[key];
        if (!o) return null;
        const inm = opts?.onlyIf?.get?.("if-none-match");
        const base = { size: o.length, httpEtag: '"abc"' };
        if (inm === '"abc"') return base;
        const r = opts?.range?.get?.("range");
        if (r) {
          const m = /bytes=(\d+)-(\d+)/.exec(r);
          const [a, b] = [Number(m[1]), Number(m[2])];
          return { ...base, body: new Blob([o.slice(a, b + 1)]).stream(), range: { offset: a, length: b - a + 1 } };
        }
        return { ...base, body: new Blob([o]).stream() };
      },
    },
    SITE_WORKER: { async fetch(req) { asked.push(req.url + " " + req.method); return new Response("site", { status: 200 }); } },
  };
}
const get = (e, path, init) => serve(new Request("https://motdang.net" + path, init), e);

let n = 0;
const ok = (name) => console.log("  ok   " + name) || n++;

{ const e = env(); const r = await get(e, "/photos/a.jpg");
  assert.equal(r.status, 200); assert.equal(r.headers.get("content-type"), "image/jpeg");
  assert.equal(r.headers.get("etag"), '"abc"'); assert.equal(r.headers.get("x-served-by"), "mot-dang-media");
  assert.match(r.headers.get("cache-control"), /max-age=2592000/);
  assert.equal(r.headers.get("access-control-allow-origin"), "*");
  assert.deepEqual(new Uint8Array(await r.arrayBuffer()), BODY); assert.equal(e.asked.length, 0);
  ok("a hit comes from the bucket with its type, etag and cache life"); }

{ const e = env();
  assert.match((await get(e, "/streetphotos/cm-x.jpg")).headers.get("cache-control"), /31536000, immutable/);
  assert.equal((await get(e, "/og/c.png")).headers.get("content-type"), "image/png");
  assert.match((await get(e, "/inat/1.jpg")).headers.get("cache-control"), /immutable/);
  ok("each prefix has its own life and type"); }

{ const e = env(); const r = await get(e, "/photos/missing.jpg");
  assert.equal(await r.text(), "site"); assert.equal(e.asked.length, 1);
  ok("a miss goes to the site Worker"); }

{ const e = env();
  for (const p of ["/", "/cm/p/x.html", "/photos/", "/photos/credits.json", "/listings/photos/p1/1.jpg", "/sites/x/og/c.png", "/photos"]) {
    const r = await get(e, p); assert.equal(await r.text(), "site", p);
  }
  assert.equal(e.asked.length, 7);
  ok("paths outside the four prefixes and the image types never reach the bucket"); }

{ const e = env(); const r = await get(e, "/photos/a.jpg", { method: "POST" });
  assert.equal(await r.text(), "site"); assert.equal(e.asked.length, 1);
  ok("methods other than GET and HEAD go to the site Worker"); }

{ const e = env(); const r = await get(e, "/photos/a.jpg", { headers: { "if-none-match": '"abc"' } });
  assert.equal(r.status, 304); assert.equal(r.headers.get("etag"), '"abc"');
  ok("a matching etag answers 304"); }

{ const e = env(); const r = await get(e, "/photos/a.jpg", { headers: { range: "bytes=2-4" } });
  assert.equal(r.status, 206); assert.equal(r.headers.get("content-range"), "bytes 2-4/10");
  assert.deepEqual(new Uint8Array(await r.arrayBuffer()), BODY.slice(2, 5));
  ok("a range answers 206 with its content-range"); }

{ const e = env(); const r = await get(e, "/photos/a.jpg", { method: "HEAD" });
  assert.equal(r.status, 200); assert.equal(r.headers.get("content-length"), "10"); assert.equal(await r.text(), "");
  ok("HEAD carries the length and no body"); }

{ const e = env(); const r = await get(e, "/media-check/photos/a.jpg");
  assert.equal(r.status, 200); assert.equal(r.headers.get("x-served-by"), "mot-dang-media");
  const m = await get(e, "/media-check/photos/none.jpg");
  assert.equal(await m.text(), "site"); assert.match(e.asked[0], /^https:\/\/motdang\.net\/photos\/none\.jpg GET$/);
  ok("the test route reads the same keys and hands a miss on without its prefix"); }

{ const e = env({ "streetphotos/cm-condoreg-กลอรี่.jpg": BODY });
  const r = await get(e, "/streetphotos/" + encodeURIComponent("cm-condoreg-กลอรี่.jpg"));
  assert.equal(r.status, 200);
  ok("a Thai key is found by its percent-encoded path"); }

{ assert.equal(keyOf("/photos/%E0%A4%A.jpg"), null); assert.equal(keyOf("/photos/../x.jpg"), null);
  ok("a bad escape or a .. is not a key"); }

{ const e = env(); e.MEDIA.get = async () => { throw new Error("r2 down"); };
  const r = await get(e, "/photos/a.jpg"); assert.equal(await r.text(), "site");
  ok("a bucket error goes to the site Worker"); }

console.log(`all ${n} checks passed`);
