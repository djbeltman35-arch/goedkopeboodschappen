// Goedkope Boodschappen: snel opnieuw openen. De prijslijst komt direct uit de cache en wordt op de achtergrond ververst.
const C = 'gb-v2';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (u.pathname === '/producten.json' || u.pathname === '/stijl.css' || u.pathname.startsWith('/icons/')) {
    e.respondWith(caches.open(C).then(async c => {
      const hit = await c.match(e.request, { ignoreSearch: true });
      const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
  } else if (e.request.mode === 'navigate') {
    // Pagina's altijd vers; zonder internet de laatst bekeken versie.
    e.respondWith(fetch(e.request).then(r => { const k = r.clone(); caches.open(C).then(c => c.put(e.request, k)); return r; }).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
  }
});
