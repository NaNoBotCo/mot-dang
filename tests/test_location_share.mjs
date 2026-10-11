import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { JSDOM } from 'jsdom';

const JS = execFileSync("python3", ["-c", "import share_layer;print(share_layer.PAGE_JS)"]).toString();

test("location share from sendRow headless", () => {
  const dom = new JSDOM(`<!DOCTYPE html><html><body><div class="ls-out"></div></body></html>`);
  const window = dom.window;
  const document = window.document;
  
  // mock environment
  window.APP = null;
  window.navigator.share = null;
  
  // run share_layer.js
  const script = document.createElement("script");
  script.textContent = JS + "\nwindow.sendRow = sendRow;\n";
  document.head.appendChild(script);
  
  const text = 'ฉันอยู่ตรงนี้ เมื่อ 07:38 · I am here, as of 07:38\nhttps://motdang.net/live.html?p=18.789021,99.045901,35,1791419895';
  const ll = '18.789021,99.045901';
  const html = window.sendRow(text, ll);
  
  const out = document.querySelector('.ls-out');
  out.innerHTML = html;
  
  // Apple maps
  const apple = out.querySelector('a.ls-alt[href^="https://maps.apple.com"]');
  assert.ok(apple, "Apple Maps link missing");
  assert.equal(apple.href, `https://maps.apple.com/?ll=${ll}&q=${ll}`);
  
  // Google maps
  const google = out.querySelector('a.ls-alt[href^="https://www.google.com/maps/search/"]');
  assert.ok(google, "Google Maps link missing");
  assert.equal(google.href, `https://www.google.com/maps/search/?api=1&query=${ll}`);
  
  // Geo URI
  const geo = out.querySelector('a.ls-alt[href^="geo:"]');
  assert.ok(geo, "Geo URI missing");
  assert.equal(geo.href, `geo:${ll}?q=${ll}`);
  
});
