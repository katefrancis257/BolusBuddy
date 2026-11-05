// Offline support. The cache name is stamped by tools/stamp_sw.py from the app's files, so any
// change to the app or its food data installs a fresh copy.
var CACHE = "bolusbuddy-a263718fc4";
var SHELL = ["./", "index.html", "core.js", "foods.js", "restaurants.js", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

// The network first, so corrected figures arrive on the next open; the cache when offline or slow.
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  e.respondWith(caches.open(CACHE).then(function (c) {
    var net = fetch(e.request).then(function (res) {
      if (res && (res.ok || res.type === "opaque")) c.put(e.request, res.clone());
      return res;
    });
    var timeout = new Promise(function (resolve, reject) { setTimeout(reject, 4000); });
    return Promise.race([net, timeout]).catch(function () {
      return c.match(e.request).then(function (hit) { return hit || net; });
    });
  }));
});
