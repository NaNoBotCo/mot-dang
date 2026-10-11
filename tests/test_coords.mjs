/** coords.js (coords_layer.py): every format read and written, checked against published values.
 *  Run: node --test tests/test_coords.mjs */
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const JS = execFileSync('python3', ['-c', 'import coords_layer; print(coords_layer.JS)'], { cwd: ROOT, encoding: 'utf8' });

function load(src, ctx = {}) {
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  return ctx;
}
const M = load(JS).MDCOORDS;
// Objects made inside the vm context have their own prototypes; compare them as plain JSON.
const plain = x => JSON.parse(JSON.stringify(x));

const lngDiff = (a, b) => Math.abs(((a - b + 540) % 360) - 180);
function near(got, lat, lng, tol, msg) {
  assert.ok(got && typeof got.lat === 'number', `${msg}: no point (${JSON.stringify(got)})`);
  assert.ok(Math.abs(got.lat - lat) <= tol && lngDiff(got.lng, lng) <= tol,
    `${msg}: got ${got.lat},${got.lng} want ${lat},${lng} (tol ${tol})`);
}

// ---------------------------------------------------------------------------
test('emit writes docs/coords.js and it sets window and globalThis MDCOORDS', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'coords-'));
  const status = execFileSync('python3', ['-c', 'import coords_layer, sys; print(coords_layer.emit(sys.argv[1]))', dir],
    { cwd: ROOT, encoding: 'utf8' });
  assert.match(status, /coords\.js/);
  const src = fs.readFileSync(path.join(dir, 'coords.js'), 'utf8');
  assert.equal(src + '\n', JS);
  const ctx = load(src, { window: {} });
  assert.equal(typeof ctx.MDCOORDS.parse, 'function');
  assert.equal(ctx.window.MDCOORDS, ctx.MDCOORDS);
  fs.rmSync(dir, { recursive: true });
});

test('source stays plain ES5 with no emoji', () => {
  assert.doesNotMatch(JS, /=>|`|\blet\s|\bconst\s|\bclass\s|\.\.\.[a-zA-Z]/);
  assert.doesNotMatch(JS, /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u);
});

// A real ES5 parse when an acorn copy is on this machine; the regex check above runs everywhere.
test('source parses as ECMAScript 5 (acorn)', (t) => {
  let acorn;
  for (const p of ['acorn', '/opt/homebrew/lib/node_modules/netlify-cli/node_modules/acorn']) {
    try { acorn = createRequire(import.meta.url)(p); break; } catch { /* try the next */ }
  }
  if (!acorn) return t.skip('acorn not installed');
  acorn.parse(JS, { ecmaVersion: 5 });
});

// ---------------------------------------------------------------------------
// Open Location Code. Rows copied from google/open-location-code test_data/
// encoding.csv, decoding.csv, shortCodeTests.csv and validityTests.csv.
test('Plus Codes: published encoding vectors', () => {
  const rows = [
    [20.375, 2.775, 6, '7FG49Q00+'],
    [20.3700625, 2.7821875, 10, '7FG49QCJ+2V'],
    [20.3701125, 2.782234375, 11, '7FG49QCJ+2VX'],
    [20.3701135, 2.78223535156, 13, '7FG49QCJ+2VXGJ'],
    [47.0000625, 8.0000625, 10, '8FVC2222+22'],
    [-41.2730625, 174.7859375, 10, '4VCPPQGP+Q9'],
    [0.5, -179.5, 4, '62G20000+'],
    [-89.5, -179.5, 4, '22220000+'],
    [-89.9999375, -179.9999375, 10, '22222222+22'],
    [0.5, 179.5, 4, '6VGX0000+'],
    [1, 1, 11, '6FH32222+222'],
    [90, 1, 4, 'CFX30000+'],
    [92, 1, 4, 'CFX30000+'],
    [90, 1, 10, 'CFX3X2X2+X2'],
  ];
  for (const [lat, lng, len, code] of rows) assert.equal(M.olc.encode(lat, lng, len), code, `${lat},${lng},${len}`);
  assert.equal(M.olc.encode(1, 1, 1), null);
  assert.equal(M.olc.encode(1, 1, 7), null);
});

test('Plus Codes: published decoding, validity, shorten and recover vectors', () => {
  const dec = [
    ['7FG49Q00+', 6, 20.35, 2.75, 20.4, 2.8],
    ['7FG49QCJ+2V', 10, 20.37, 2.782125, 20.370125, 2.78225],
    ['7FG49QCJ+2VX', 11, 20.3701, 2.78221875, 20.370125, 2.78225],
    ['8FVC2222+22', 10, 47.0, 8.0, 47.000125, 8.000125],
  ];
  for (const [code, len, a, b, c, d] of dec) {
    const r = M.olc.decode(code);
    assert.equal(r.length, len);
    for (const [x, y] of [[r.latLo, a], [r.lngLo, b], [r.latHi, c], [r.lngHi, d]]) assert.ok(Math.abs(x - y) < 1e-10, code);
  }
  const valid = [
    ['8FWC2345+G6', true, false, true], ['8fwc2345+', true, false, true], ['8FWCX400+', true, false, true],
    ['WC2345+G6g', true, true, false], ['2345+G6', true, true, false], ['45+G6', true, true, false],
    ['G+', false, false, false], ['+', false, false, false], ['8FWC2345+G', false, false, false],
    ['8FWC2_45+G6', false, false, false], ['8FWC2η45+G6', false, false, false], ['8FWC2345+G6+', false, false, false],
    ['8FWC2300+G6', false, false, false], ['WC2300+G6g', false, false, false], ['WC2345+G', false, false, false],
  ];
  for (const [c, v, s, f] of valid) assert.deepEqual([M.olc.isValid(c), M.olc.isShort(c), M.olc.isFull(c)], [v, s, f], c);
  const short = [
    ['9C3W9QCJ+2VX', 51.3701125, -1.217765625, '+2VX'],
    ['9C3W9QCJ+2VX', 51.3708675, -1.217765625, 'CJ+2VX'],
    ['9C3W9QCJ+2VX', 51.3701125, -1.232865625, '9QCJ+2VX'],
    ['8FJFW222+', 42.899, 9.012, '22+'],
  ];
  for (const [full, lat, lng, s] of short) {
    assert.equal(M.olc.shorten(full, lat, lng), s, full);
    assert.equal(M.olc.recoverNearest(s, lat, lng), full, s);
  }
});

// Geohash. "ezs42" -> 42.605, -5.603 is the worked example in the Wikipedia article
// "Geohash"; "u4pruydqqvj" (57.64911, 10.40744) is the example from geohash.org.
test('geohash: published examples', () => {
  const a = M.geohash.decode('ezs42');
  assert.ok(Math.abs(a.lat - 42.605) < 0.001 && Math.abs(a.lng - -5.603) < 0.001);
  assert.equal(M.geohash.encode(42.605, -5.603, 5), 'ezs42');
  assert.equal(M.geohash.encode(57.64911, 10.40744, 11), 'u4pruydqqvj');
  near(M.geohash.decode('u4pruydqqvj'), 57.64911, 10.40744, 1e-5, 'u4pruydqqvj');
  assert.equal(M.geohash.decode('ailo'), null);
});

// UTM and MGRS. The Baghdad row is the EXAMPLES section of the GeographicLib GeoConvert
// man page (38SMB4488 -> 33.33424 44.40363, UTM 38n 444500 3688500). The others were
// computed with GeographicLib's online GeoConvert (geographiclib.sourceforge.io/cgi-bin/GeoConvert,
// version 2.5.2), which is Karney's exact transverse Mercator.
const GEOCONVERT = [
  [18.7876, 98.9931, 47, 499272.86, 2077326.14, '47QMA 99272 77326'],
  [19.9094, 99.8325, 47, 587135.94, 2201671.14, '47QNC 87135 01671'],
  [13.7563, 100.5018, 47, 662366.60, 1521280.66, '47PPR 62366 21280'],
  [7.0, 97.0, 47, 279054.11, 774218.97, '47NKH 79054 74218'],
  [20.3, 105.9, 48, 593968.02, 2244935.93, '48QWH 93968 44935'],
  [-33.8568, 151.2153, 56, 334900.57, 6252288.75, '56HLH 34900 52288'],
  [0.5, -179.5, 1, 221734.22, 55318.04, '1NBA 21734 55318'],
  [-0.0001, -179.9999, 1, 166032.59, 9999988.93, '1MAV 66032 99988'],
  [0, 0, 31, 166021.44, 0.0, '31NAA 66021 00000'],
  [60.5, 5.5, 32, 307793.02, 6712209.07, '32VLN 07793 12209'],
  [-54.8, -68.3, 19, 545000.05, 3927239.38, '19FEV 45000 27239'],
  [33.33424, 44.40363, 38, 444500.20, 3688500.54, '38SMB 44500 88500'],
];
test('UTM and MGRS: GeographicLib GeoConvert values', () => {
  for (const [lat, lng, zone, e, n, mgrs] of GEOCONVERT) {
    const u = M.utm.fromLatLng(lat, lng);
    assert.equal(u.zone, zone, `${lat},${lng} zone`);
    assert.ok(Math.abs(u.easting - e) < 0.01 && Math.abs(u.northing - n) < 0.01, `${lat},${lng}: ${u.easting} ${u.northing}`);
    near(M.utm.toLatLng(zone, lat < 0, e, n), lat, lng, 2e-7, `inverse ${lat},${lng}`);
    assert.equal(M.mgrs.fromLatLng(lat, lng), mgrs);
  }
  const b = M.mgrs.toLatLng('38SMB4488');
  assert.equal(b.easting, 444500);
  assert.equal(b.northing, 3688500);
  assert.equal(b.lat.toFixed(5), '33.33424');
  assert.equal(b.lng.toFixed(5), '44.40363');
  assert.equal(M.utm.fromLatLng(85, 0), null);
});

// Maidenhead: Munich 48.14666 N 11.60833 E is JN58td, the example most often quoted for the system.
test('Maidenhead locators', () => {
  assert.equal(M.maidenhead.encode(48.14666, 11.60833, 6), 'JN58td');
  assert.equal(M.maidenhead.encode(18.7876, 98.9931, 6), 'NK98ls');
  assert.equal(M.maidenhead.encode(18.7876, 98.9931, 8), 'NK98ls99');
  near(M.maidenhead.decode('OK08'), 18.5, 101, 1e-9, 'OK08');
  near(M.maidenhead.decode('JN58td'), 48.14583, 11.625, 1e-4, 'JN58td');
});

// Organic Maps ge0 links: vectors from organicmaps libs/ge0/ge0_tests/parser_tests.cpp and
// url_generator_tests.cpp. The tolerance is the one those tests use for 9 coordinate bytes.
test('Organic Maps ge0 short links', () => {
  const eps = 8 / (2 ** 30 - 1) * 360 / 1.77;
  for (const [code, lat, lng, zoom] of [
    ['B4srhdHVVt', 64.5234, 12.1234, 4.25], ['Byqqqqqqqq', 45, 0, 4.25], ['Bzqqqqqqqq', 45, 45, 4.25],
    ['BaF6F6F6F6', -20, 20, 4.25], ['BP________', -0.000001, -0.000001, 4.25], ['8wAAAAAAAA', 0, 0, 19],
  ]) {
    const g = M.ge0.decode(code);
    near(g, lat, lng, eps, code);
    assert.equal(g.zoom, zoom);
  }
  assert.equal(M.ge0.encode(0, 0, 19, 9), '8wAAAAAAAA');
  assert.equal(M.ge0.encode(-90, -180, 4, 9), 'AAAAAAAAAA');
  assert.equal(M.ge0.encode(90, 179.999999, 4, 9), 'A_________');
  assert.equal(M.ge0.encode(-0.000001, -0.000001, 4, 9), 'AP________');
});

// OSM short links: codes produced by lib/short_link.rb from openstreetmap-website
// (ShortLink.encode) and the decoded values it returns.
test('OpenStreetMap short links', () => {
  for (const [code, lat, lng, zoom] of [
    ['4WxtYhllp-', 18.78759875893593, 98.99309813976288, 17],
    ['4Xi7ovpO--', 19.909393787384033, 99.83248472213745, 15],
    ['uN~Ra6l--', -33.85685920715332, 151.2151336669922, 12],
    ['~v2juONc--', 78.10350179672241, 178.41148853302002, 15],
  ]) {
    const o = M.osmShortLink.decode(code);
    near(o, lat, lng, 1e-9, code);
    assert.equal(o.zoom, zoom);
  }
  assert.deepEqual(plain(M.osmShortLink.decode('@v2juONc--')), plain(M.osmShortLink.decode('~v2juONc--')));
});

// ---------------------------------------------------------------------------
const POINTS = [
  ['Tha Phae Gate', 18.7877, 98.9938], ['Doi Suthep', 18.8048, 98.9217], ['Nimman', 18.7999, 98.9676],
  ['CM airport', 18.7668, 98.9626], ['Mae Rim', 18.9136, 98.9446], ['Warorot', 18.7903, 99.0006],
  ['White Temple', 19.8243, 99.7631], ['CR clock tower', 19.9076, 99.8309], ['Blue Temple', 19.9208, 99.8412],
  ['Golden Triangle', 20.3531, 100.0835], ['Doi Tung', 20.3294, 99.8347], ['Mae Sai', 20.4335, 99.8761],
  ['null island', 0, 0], ['equator east', 0.0001, 36.8], ['south of equator', -0.0001, -179.9999],
  ['antimeridian west', 0.5, 179.9999], ['Fiji', -16.5, -179.95], ['Chukotka', 65.0, -179.9],
  ['Sydney', -33.8568, 151.2153], ['Ushuaia', -54.8, -68.3], ['Wellington', -41.2865, 174.7762],
];
const TOL = { decimal: 1e-6, dms: 3e-6, ddm: 2e-6, pluscode: 7e-5, pluscode_short: 7e-5, geohash: 3e-5, utm: 2e-5, mgrs: 3e-5, maidenhead: 0.05 };
const KIND = { pluscode_short: 'pluscode' };

test('round trip: every format at every point parses back to the point', () => {
  let rows = 0;
  for (const [name, lat, lng] of POINTS) {
    for (const r of M.format(lat, lng)) {
      const got = M.parse(r.text);
      assert.equal(got && got.kind, KIND[r.kind] || r.kind, `${name} ${r.kind} "${r.text}"`);
      near(got, lat, lng, TOL[r.kind], `${name} ${r.kind} "${r.text}"`);
      rows++;
    }
    near(M.parse('gh:' + M.geohash.encode(lat, lng, 9)), lat, lng, TOL.geohash, `${name} gh:`);
  }
  assert.ok(rows > 170, `${rows} rows`);
});

test('round trip: every "open in" link parses back to the point', () => {
  for (const [name, lat, lng] of POINTS) {
    for (const l of M.links(lat, lng, 'Wat Phra Singh')) {
      const got = M.parse(l.href);
      near(got, lat, lng, 1e-5, `${name} ${l.id} ${l.href}`);
    }
  }
});

// ---------------------------------------------------------------------------
test('format: order, labels and the short Plus Code', () => {
  const f = M.format(18.7876, 98.9931);
  assert.deepEqual(plain(f.map(r => r.kind)),
    ['decimal', 'dms', 'ddm', 'pluscode', 'pluscode_short', 'geohash', 'utm', 'mgrs', 'maidenhead']);
  for (const r of f) assert.ok(/[\u0E00-\u0E7F]/.test(r.th) && r.en && r.text, r.kind);
  const t = Object.fromEntries(f.map(r => [r.kind, r.text]));
  assert.equal(t.decimal, '18.787600, 98.993100');
  assert.equal(t.dms, `18°47'15.36"N 98°59'35.16"E`);
  assert.equal(t.ddm, `18°47.2560'N 98°59.5860'E`);
  assert.equal(t.pluscode, '7MCWQXQV+26');
  assert.equal(t.pluscode_short, 'QXQV+26 Chiang Mai');
  assert.equal(t.geohash, 'w5q6ushtd');
  assert.equal(t.utm, '47Q 499273 2077326');
  assert.equal(t.mgrs, '47QMA 99272 77326');
  assert.equal(t.maidenhead, 'NK98ls');
  const cr = Object.fromEntries(M.format(19.9094, 99.8325).map(r => [r.kind, r.text]));
  assert.equal(cr.pluscode_short, 'WR5M+Q2 Chiang Rai');
  assert.ok(!M.format(-33.8568, 151.2153).some(r => r.kind === 'pluscode_short'));
  const pole = M.format(85, 10).map(r => r.kind);
  assert.ok(!pole.includes('utm') && !pole.includes('mgrs') && pole.includes('pluscode'));
  assert.equal(M.format(0, 180)[0].text, '0.000000, -180.000000');
  assert.deepEqual(plain(M.format('x', 1)), []);
});

test('links: open-source tools first, names encoded', () => {
  const l = M.links(18.7876, 98.9931, 'Tha Phae Gate');
  assert.deepEqual(plain(l.map(x => x.id)), ['osm', 'organicmaps', 'osmand', 'geo', 'umap', 'google', 'apple', 'waze']);
  const h = Object.fromEntries(l.map(x => [x.id, x.href]));
  assert.equal(h.osm, 'https://www.openstreetmap.org/?mlat=18.7876&mlon=98.9931#map=17/18.7876/98.9931');
  assert.match(h.organicmaps, /^https:\/\/omaps\.app\/0[A-Za-z0-9_-]{9}\/Tha_Phae_Gate$/);
  assert.equal(h.osmand, 'https://osmand.net/map?pin=18.7876,98.9931#17/18.7876/98.9931');
  assert.equal(h.geo, 'geo:18.7876,98.9931?q=18.7876,98.9931(Tha%20Phae%20Gate)');
  assert.equal(h.google, 'https://www.google.com/maps/search/?api=1&query=18.7876,98.9931');
  assert.equal(h.apple, 'https://maps.apple.com/?ll=18.7876,98.9931&q=Tha%20Phae%20Gate');
  assert.match(h.waze, /^https:\/\/www\.waze\.com\/ul\?ll=18\.7876,98\.9931/);
  for (const x of l) assert.ok(/[\u0E00-\u0E7F]/.test(x.th) && x.en, x.id);
  const om = M.parse(M.links(18.7876, 98.9931, 'ประตูท่าแพ')[1].href);
  assert.equal(om.label, 'ประตูท่าแพ');
});

// ---------------------------------------------------------------------------
const CMP = [18.7876, 98.9931];
const TEXT = [
  // decimal, with punctuation, letters, lng-first and Thai digits
  ['18.7876, 98.9931', 'decimal', CMP], ['18.7876 98.9931', 'decimal', CMP], ['  (18.7876, 98.9931).', 'decimal', CMP],
  ['98.9931, 18.7876', 'decimal', CMP], ['[98.9931, 18.7876]', 'decimal', CMP], ['18.7876N 98.9931E', 'decimal', CMP],
  ['N18.7876 E98.9931', 'decimal', CMP], ['18.7876° N, 98.9931° E', 'decimal', CMP], ['E 98.9931, N 18.7876', 'decimal', CMP],
  ['lat: 18.7876, lng: 98.9931', 'decimal', CMP], ['๑๘.๗๘๗๖, ๙๘.๙๙๓๑', 'decimal', CMP], ['18.7876，98.9931。', 'decimal', CMP],
  ['"18.7876,98.9931"', 'decimal', CMP], ['-33.8568, 151.2153', 'decimal', [-33.8568, 151.2153]],
  ['151.2153, -33.8568', 'decimal', [-33.8568, 151.2153]], ['33.8568S 151.2153E', 'decimal', [-33.8568, 151.2153]],
  ['0.5, -179.5', 'decimal', [0.5, -179.5]],
  // DMS and DDM
  [`18°47'15.4"N 98°59'35.2"E`, 'dms', [18.787611, 98.993111]], ['18°47′15.4″N 98°59′35.2″E', 'dms', [18.787611, 98.993111]],
  [`18° 47' 15.4" N, 98° 59' 35.2" E`, 'dms', [18.787611, 98.993111]], [`N 18°47'15.4" E 98°59'35.2"`, 'dms', [18.787611, 98.993111]],
  ['18 47 15.4 98 59 35.2', 'dms', [18.787611, 98.993111]], [`18°47'N 98°59'E`, 'ddm', [18.783333, 98.983333]],
  ['18 47.257N 98 59.587E', 'ddm', [18.787617, 98.993117]], ['18 47.257 98 59.587', 'ddm', [18.787617, 98.993117]],
  ['N 18 47.257 E 98 59.587', 'ddm', [18.787617, 98.993117]], [`33°51'24.48"S 151°12'55.08"E`, 'dms', [-33.8568, 151.2153]],
  // Plus Codes
  ['7MCWQXQV+26', 'pluscode', CMP], ['7mcwqxqv+26', 'pluscode', CMP], ['QXQV+26 Chiang Mai', 'pluscode', CMP],
  ['QXQV+26 เชียงใหม่', 'pluscode', CMP], ['QXQV+26', 'pluscode', CMP],
  ['QXQV+26 Mueang Chiang Mai District, Chiang Mai, Thailand', 'pluscode', CMP],
  ['WR5M+Q2 Chiang Rai', 'pluscode', [19.9094, 99.8325]], ['WR5M+Q2 เชียงราย', 'pluscode', [19.9094, 99.8325]],
  // geohash
  ['w5q6ushtd', 'geohash', CMP], ['gh:w5q6ushtd', 'geohash', CMP], ['GH: W5Q6USHTD', 'geohash', CMP],
  // UTM and MGRS
  ['47Q 499273 2077326', 'utm', CMP], ['47 499273 2077326', 'utm', CMP], ['47n 499273 2077326', 'utm', CMP],
  ['47N 499273 2077326', 'utm', CMP], ['47Q 499273mE 2077326mN', 'utm', CMP], ['Zone 47Q E 499273 N 2077326', 'utm', CMP],
  ['56H 334901 6252289', 'utm', [-33.8568, 151.2153]], ['56s 334901 6252289', 'utm', [-33.8568, 151.2153]],
  ['56S 334901 6252289', 'utm', [-33.8568, 151.2153]], ['38S 444500 3688500', 'utm', [33.33424, 44.40363]],
  ['47QMA 99272 77326', 'mgrs', CMP], ['47QMA9927277326', 'mgrs', CMP], ['47Q MA 99272 77326', 'mgrs', CMP],
  ['47qma9927277326', 'mgrs', CMP], ['47QMA 9927 7732', 'mgrs', CMP, 1e-3], ['47QMA 99 77', 'mgrs', CMP, 0.01],
  ['47QMA 9 7', 'mgrs', CMP, 0.1], ['38SMB4488', 'mgrs', [33.33424, 44.40363], 1e-5],
  ['56HLH 34900 52288', 'mgrs', [-33.8568, 151.2153]],
  // Maidenhead
  ['OK08', 'maidenhead', [18.5, 101], 1e-9], ['OK08fs', 'maidenhead', [18.770833, 100.458333]],
  ['OK08fs12', 'maidenhead', [18.760417, 100.429167]], ['NK98ls', 'maidenhead', CMP, 0.05], ['JN58td', 'maidenhead', [48.145833, 11.625]],
  // geo: URIs
  ['geo:18.7876,98.9931', 'geo', CMP], ['geo:18.7876,98.9931?z=15', 'geo', CMP],
  ['geo:0,0?q=18.7876,98.9931(Tha Phae Gate)', 'geo', CMP], ['geo:0,0?q=18.7876,98.9931(Tha%20Phae%20Gate)', 'geo', CMP],
];
const TOLS = { decimal: 1e-6, dms: 1e-5, ddm: 1e-5, pluscode: 1e-4, geohash: 3e-5, utm: 2e-5, mgrs: 2e-5, geo: 1e-6, maidenhead: 1e-5 };

test('parse: coordinate text in all its spellings', () => {
  for (const [text, kind, [lat, lng], tol] of TEXT) {
    const got = M.parse(text);
    assert.equal(got && got.kind, kind, `"${text}" -> ${JSON.stringify(got)}`);
    near(got, lat, lng, tol || TOLS[kind], `"${text}"`);
  }
  assert.equal(M.parse('geo:0,0?q=18.7876,98.9931(Tha Phae Gate)').label, 'Tha Phae Gate');
  assert.equal(M.parse('geo:18.7876,98.9931?z=15').zoom, 15);
});

test('parse: short Plus Code falls back to the reference point, else Chiang Mai', () => {
  near(M.parse('WR5M+Q2', { ref: { lat: 19.9094, lng: 99.8325 } }), 19.9094, 99.8325, 1e-4, 'ref CR');
  near(M.parse('QXQV+26', { ref: { lat: 18.5, lng: 98.8 } }), 18.7876, 98.9931, 1e-4, 'ref near CM');
  const far = M.parse('WR5M+Q2');
  assert.ok(Math.abs(far.lat - 18.7876) < 0.5 && Math.abs(far.lng - 98.9931) < 0.5, 'no ref: nearest to Chiang Mai');
});

const URLS = [
  ['https://www.openstreetmap.org/#map=16/18.7876/98.9931', 'osm', 16],
  ['https://www.openstreetmap.org/?mlat=18.7876&mlon=98.9931#map=17/18.79/98.99', 'osm', 17],
  ['openstreetmap.org/?lat=18.7876&lon=98.9931&zoom=12', 'osm', 12],
  ['https://osm.org/go/4WxtYhllp-', 'osm', 17, 1e-5],
  ['https://osm.org/go/4WxtYhllp-?m=', 'osm', 17, 1e-5],
  ['https://omaps.app/00pyekSaaW/Tha_Phae_Gate', 'organicmaps', 17],
  ['https://omaps.app/18.7876,98.9931/Tha_Phae_Gate?z=16', 'organicmaps', 16],
  ['om://00pyekSaaW', 'organicmaps', 17], ['ge0://00pyekSaaW/Name', 'organicmaps', 17],
  ['http://ge0.me/00pyekSaaW/Name', 'organicmaps', 17],
  ['https://osmand.net/go?lat=18.7876&lon=98.9931&z=16', 'osmand', 16],
  ['https://osmand.net/go.html?lat=18.7876&lon=98.9931&z=16', 'osmand', 16],
  ['https://osmand.net/map?pin=18.7876,98.9931#17/18.79/98.99', 'osmand', 17],
  ['https://osmand.net/map#15/18.7876/98.9931', 'osmand', 15],
  ['https://www.google.com/maps/@18.7876,98.9931,15z', 'google', 15],
  ['https://www.google.com/maps?q=18.7876,98.9931', 'google'],
  ['https://maps.google.com/?ll=18.7876,98.9931&z=14', 'google', 14],
  ['https://www.google.com/maps/search/?api=1&query=18.7876,98.9931', 'google'],
  ['https://www.google.com/maps/place/18.7876,98.9931', 'google'],
  ['https://www.google.co.th/maps/search/18.7876,+98.9931?hl=th', 'google'],
  ['https://www.google.com/maps/place/Tha+Phae+Gate/@18.78,98.98,17z/data=!3m1!4b1!4m6!3m5!1s0x0:0x0!8m2!3d18.7876!4d98.9931!16s', 'google', 17],
  ['https://www.google.com/maps/dir//18.7876,98.9931/@18.7,98.9,12z', 'google', 12],
  ['https://maps.apple.com/?ll=18.7876,98.9931&q=Tha%20Phae%20Gate', 'apple'],
  ['https://maps.apple.com/?q=18.7876,98.9931', 'apple'],
  ['https://maps.apple.com/?coordinate=18.7876,98.9931&name=Gate', 'apple'],
  ['https://www.bing.com/maps?cp=18.7876~98.9931&lvl=15', 'bing', 15],
  ['https://www.bing.com/maps?cp=18.7876%7E98.9931&lvl=15', 'bing', 15],
  ['https://www.waze.com/ul?ll=18.7876%2C98.9931&navigate=yes', 'waze'],
  ['https://www.waze.com/live-map/directions?to=ll.18.7876%2C98.9931', 'waze'],
  ['https://wego.here.com/?map=18.7876,98.9931,15,normal', 'here', 15],
  ['https://share.here.com/l/18.7876,98.9931,Tha%20Phae', 'here'],
  ['https://www.mapillary.com/app/?lat=18.7876&lng=98.9931&z=17', 'mapillary', 17],
  ['https://umap.openstreetmap.fr/en/map/chiang-mai_123#16/18.7876/98.9931', 'umap', 16],
  ['https://example.org/leaflet.html#16/18.7876/98.9931', 'url', 16],
  ['https://motdang.net/map.html#16/18.78760/98.99310/', 'mdmap', 16],
  ['map.html#16/18.7876/98.9931', 'mdmap', 16],
  ['https://plus.codes/7MCWQXQV+26', 'pluscode', undefined, 1e-4],
  ['http://geohash.org/w5q6ushtd', 'geohash', undefined, 3e-5],
];

test('parse: map links from every supported service', () => {
  for (const [url, kind, zoom, tol] of URLS) {
    const got = M.parse(url);
    assert.equal(got && got.kind, kind, `${url} -> ${JSON.stringify(got)}`);
    near(got, 18.7876, 98.9931, tol || 1e-5, url);
    if (zoom !== undefined) assert.equal(got.zoom, zoom, `${url} zoom`);
  }
  assert.equal(M.parse('https://omaps.app/00pyekSaaW/Tha_Phae_Gate').label, 'Tha Phae Gate');
  assert.equal(M.parse(URLS[20][0]).label, 'Tha Phae Gate');
  assert.equal(M.parse('https://maps.apple.com/?ll=18.7876,98.9931&q=Tha%20Phae%20Gate').label, 'Tha Phae Gate');
  // Organic Maps' own worked example (url_generator_tests.cpp): the clear-coordinate form.
  near(M.parse('https://omaps.app/33.890408,35.506645/Falafel_M._Sahyoun?z=16'), 33.890408, 35.506645, 1e-9, 'falafel');
  near(M.parse('https://omaps.app/B4srhdHVVt/Name'), 64.5234, 12.1234, 2e-6, 'ge0 test vector');
});

test('parse: what3words, Mot Dang codes and place pages', () => {
  for (const [t, words] of [['///index.home.raft', 'index.home.raft'], ['index.home.raft', 'index.home.raft'],
    ['  ///Filled.Count.Soap. ', 'filled.count.soap'], ['///ตั้งใจ.ภูเขา.ทะเล', 'ตั้งใจ.ภูเขา.ทะเล'],
    ['https://what3words.com/index.home.raft', 'index.home.raft'], ['https://w3w.co/index.home.raft', 'index.home.raft']]) {
    const r = M.parse(t);
    assert.deepEqual({ kind: r && r.kind, words: r && r.words }, { kind: 'w3w', words }, t);
    assert.equal(r.lat, undefined);
  }
  for (const [t, code] of [['MD-4F2K9', '4F2K9'], ['md-4f2k9', '4F2K9'], ['MD 4F2K9', '4F2K9'], ['MD4F2K9', '4F2K9'],
    ['MD-ABCDE', 'ABCDE'], ['MD-4F2KO', '4F2K0'], ['4F2K9', '4F2K9'], ['MD-7X9Q', '7X9Q'], ['MD-12345678', '12345678']]) {
    assert.deepEqual(plain(M.parse(t)), { kind: 'mdcode', code }, t);
  }
  assert.equal(M.parse('MD-4F2K9U'), null);
  assert.deepEqual(plain(M.parse('https://motdang.net/cm/p/wat-phra-singh.html')), { kind: 'mdplace', prov: 'cm', slug: 'wat-phra-singh' });
  assert.deepEqual(plain(M.parse('motdang.net/cr/p/white-temple.html')), { kind: 'mdplace', prov: 'cr', slug: 'white-temple' });
  assert.deepEqual(plain(M.parse('/cm/p/0-7621388049794598717523.html')), { kind: 'mdplace', prov: 'cm', slug: '0-7621388049794598717523' });
});

test('parse: plain words and weak input return null', () => {
  for (const t of ['coffee', '7-eleven', 'ร้านกาแฟ', '', '12', '   ', null, undefined, '7 11', '18 98', 'cafe',
    'hello world', 'Chiang Mai', 'เชียงใหม่', 'Nimman Soi 7', 'pretty', '2024', '12345', '18.78', 'N 18',
    'www.google.com', 'motdang.net', 'https://maps.app.goo.gl/abc123', 'https://www.openstreetmap.org/node/123',
    'geo:0,0?q=coffee', 'e.g. this', 'google.com.au', '200.5, 98.9931', '95.1, 98.9931']) {
    assert.equal(M.parse(t), null, JSON.stringify(t));
  }
});
