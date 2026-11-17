// Afgeschermde beheerpagina voor Erik: alle e-mailaanmeldingen (nieuwsbrief en lijstmeldingen) in één overzicht.
// Toegang met een geheime code; hier staat alleen de SHA-256 ervan, de code zelf staat nergens in de repo.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const HASH = 'fdd2bdb34df698ad6356f74a5cb08d7573ee285356ee6a9a7104802be62d12c3';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const datum = d => d ? new Intl.DateTimeFormat('nl-NL', { timeZone: 'Europe/Amsterdam', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(d)) : '';
const pagina = inhoud => new Response('<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Beheer · Goedkope Boodschappen</title>'
  + '<style>body{font:16px/1.4 system-ui,sans-serif;margin:0;padding:16px;background:#f4f7f1;color:#1e2a22}h1{font-size:22px;margin:0 0 12px}.tel{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}.tel div{background:#fff;border:1px solid #e1e7dc;border-radius:12px;padding:10px 14px}.tel b{display:block;font-size:24px;color:#0e7c4a}'
  + 'ul{list-style:none;margin:0;padding:0}li{background:#fff;border:1px solid #e1e7dc;border-radius:12px;padding:10px 14px;margin:0 0 8px}li .m{font-weight:700;word-break:break-all}li small{color:#5d6a61;display:block}.ok{color:#0e7c4a}.wacht{color:#b26b00}'
  + 'form{display:flex;gap:8px;max-width:420px}input{flex:1;padding:12px;border:1px solid #e1e7dc;border-radius:12px;font:inherit}button{padding:12px 16px;border:0;border-radius:12px;background:#0e7c4a;color:#fff;font:700 16px system-ui}.fout{color:#c0392b}</style></head><body>' + inhoud + '</body></html>',
  { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow', 'Referrer-Policy': 'no-referrer' } });
const inlog = fout => pagina('<h1>Beheer</h1>' + (fout ? '<p class="fout">Onjuiste code.</p>' : '') + '<form method="post"><input type="password" name="code" placeholder="Code" autocomplete="current-password" required autofocus><button>Inloggen</button></form>');

export default async req => {
  if (req.method !== 'POST') return inlog(false);
  const code = String((await req.formData().catch(() => null))?.get('code') || '').trim();
  const h = crypto.createHash('sha256').update(code).digest();
  if (!crypto.timingSafeEqual(h, Buffer.from(HASH, 'hex'))) { await new Promise(r => setTimeout(r, 1500)); return inlog(true); }

  const store = getStore('email'), rijen = [];
  for (const { key } of (await store.list({ prefix: 't-' })).blobs) {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (a?.email) rijen.push(a);
  }
  rijen.sort((x, y) => String(y.sinds || '').localeCompare(String(x.sinds || '')));
  const bev = rijen.filter(a => a.bevestigd), nb = bev.filter(a => a.nieuws), dag = Date.now() - 864e5;
  const tel = [['Bevestigd', bev.length], ['Nieuwsbrief', nb.length], ['Lijstmeldingen', bev.filter(a => a.termen?.length).length], ['Wacht op bevestiging', rijen.length - bev.length], ['Nieuw (24 uur)', rijen.filter(a => Date.parse(a.sinds) > dag).length]];
  const wat = a => [a.nieuws === 'dag' ? 'Nieuwsbrief dagelijks' : a.nieuws === 'week' ? 'Nieuwsbrief wekelijks' : '', a.termen?.length ? 'Lijstmeldingen (' + a.termen.length + ' artikelen)' : '', a.week ? 'Weekoverzicht' : '', a.alarm?.length ? a.alarm.length + ' prijsalarm(en)' : ''].filter(Boolean).join(' · ') || 'Niets gekozen';
  return pagina('<h1>Aanmeldingen</h1><div class="tel">' + tel.map(([n, v]) => '<div><b>' + v + '</b>' + n + '</div>').join('') + '</div><ul>'
    + rijen.map(a => '<li><span class="m">' + esc(a.email) + '</span><small>' + esc(wat(a)) + '</small><small>Aangemeld ' + esc(datum(a.sinds)) + ' · '
      + (a.bevestigd ? '<span class="ok">bevestigd</span>' : '<span class="wacht">wacht op bevestiging</span>') + '</small></li>').join('')
    + '</ul>' + (rijen.length ? '' : '<p>Nog geen aanmeldingen.</p>'));
};

export const config = { path: '/beheer', method: ['GET', 'POST'] };
