/* The service worker exists for one reason: so the app opens on a phone with
 * no signal, exactly as the Android build does. It precaches every file the
 * app is made of at install time — the map data included — and afterwards
 * serves them from the cache without asking the network.
 *
 * Reports are the one thing that must reach the worker, so they are never
 * cached and never intercepted: a POST goes straight to the network and the
 * app itself queues it when that fails.
 *
 * Bump CACHE when any file below changes, or phones keep the old one.
 */
var CACHE = 'motdang-v1.1';
var SHELL = [
  './',
  'index.html',
  'app.css',
  'app.js',
  'manifest.webmanifest',
  'data/basemap.js',
  'data/landmarks.js',
  'data/toilets.js',
  'data/toilets-customers.js',
  'icons/icon-180.png',
  'icons/icon-192.png',
  'icons/icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(SHELL);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      return k === CACHE ? null : caches.delete(k);
    }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  // A toilet report is a POST to another origin. Leave it alone entirely.
  if (e.request.method !== 'GET') return;
  if (new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(function (hit) {
      if (hit) return hit;
      return fetch(e.request).then(function (res) {
        // Cache what we fetch so a first visit that missed the precache
        // still works offline afterwards.
        if (res && res.ok && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
        }
        return res;
      });
    })
  );
});
