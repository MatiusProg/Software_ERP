// Service worker para que la app sea instalable y funcione offline.
// v2: la app ya habla con la API del ERP, así que el SW deja pasar de largo
// todo lo que no sea de este mismo origen (si no, cachearía respuestas de la
// API y, sin internet, devolvería el index.html en lugar de un error claro).
const CACHE = "listas-compras-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-maskable.png"
];

self.addEventListener("install", (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).catch(() => {})
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Estrategia: red primero, con respaldo a caché (para usar sin internet).
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  // Las llamadas a la API (otro origen) no se tocan: van directo a la red.
  if (new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html")))
  );
});
