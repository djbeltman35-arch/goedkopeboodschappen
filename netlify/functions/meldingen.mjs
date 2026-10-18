// Aan- en afmelden voor meldingen bij aanbiedingen. Bewaart per apparaat het push-abonnement, de woorden op de lijst
// en de gekozen supermarkten in Netlify Blobs. Geen namen, e-mailadressen of andere persoonsgegevens.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const PUSHDIENSTEN = /^https:\/\/([a-z0-9-]+\.)*(googleapis\.com|mozilla\.com|mozaws\.net|push\.apple\.com|notify\.windows\.com)\//;
const sleutel = endpoint => crypto.createHash('sha256').update(endpoint).digest('hex').slice(0, 40);
const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });

export default async req => {
  if (req.method === 'GET') return json({ sleutel: Netlify.env.get('VAPID_PUBLIC') || null });
  let body; try { body = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  const sub = body?.sub;
  if (!sub?.endpoint || !PUSHDIENSTEN.test(sub.endpoint)) return json({ fout: 'onbekende pushdienst' }, 400);
  const store = getStore('meldingen'), k = sleutel(sub.endpoint);
  if (req.method === 'DELETE') { await store.delete(k); return json({ ok: true }); }
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  if (!sub.keys?.p256dh || !sub.keys?.auth) return json({ fout: 'sleutels ontbreken' }, 400);
  const termen = [...new Set((Array.isArray(body.termen) ? body.termen : []).map(t => String(t).slice(0, 60).trim()).filter(Boolean))].slice(0, 80);
  const winkels = (Array.isArray(body.winkels) ? body.winkels : []).map(String).filter(w => /^[a-z]{2,12}$/.test(w)).slice(0, 15);
  const oud = await store.get(k, { type: 'json' }).catch(() => null);
  await store.setJSON(k, { sub: { endpoint: sub.endpoint, keys: { p256dh: String(sub.keys.p256dh), auth: String(sub.keys.auth) } }, termen, winkels, verstuurd: oud?.verstuurd || {}, sinds: oud?.sinds || new Date().toISOString(), bijgewerkt: new Date().toISOString() });
  return json({ ok: true, termen: termen.length });
};

export const config = { path: '/api/meldingen', method: ['GET', 'POST', 'DELETE'] };
