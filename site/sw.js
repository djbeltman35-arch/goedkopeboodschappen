// Goedkope Boodschappen: snel opnieuw openen. De prijslijst komt direct uit de cache en wordt op de achtergrond ververst.
const C = 'gb-v27';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (u.pathname === '/producten.json' || u.pathname === '/producten-kern.json' || u.pathname === '/producten-rest.json' || u.pathname === '/winkels.json' || u.pathname.startsWith('/p/') || u.pathname === '/stijl.css' || u.pathname.startsWith('/icons/')) {
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

// Meldingen bij aanbiedingen voor je lijst
self.addEventListener('push', e => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (_) { d = { titel: 'Goedkope Boodschappen', tekst: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(d.titel || 'Goedkope Boodschappen', {
    body: d.tekst || 'Er is iets van je lijst in de aanbieding.', icon: '/icons/icon-192.png', badge: '/icons/icon-192.png',
    tag: 'aanbiedingen', renotify: true, data: { url: d.url || '/' },
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) if (c.url.startsWith(self.location.origin) && 'focus' in c) { c.navigate(url); return c.focus(); }
    return self.clients.openWindow(url);
  }));
});
