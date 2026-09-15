const CACHE_NAME = 'almox-fiep-v1';
const ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/Adobe Express - file.png',
  '/static/novalogo.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS).catch(err => console.log("Assets caching skipped: ", err));
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
