// "Samen een lijst": één boodschappenlijst voor het hele huishouden, zonder account.
// Bewaard in Netlify Blobs (store "samen") onder een willekeurige code van 24 tekens; wie de link heeft, kan de lijst zien en wijzigen.
// Alleen wat nodig is: per artikel de zoekterm, winkel, productnaam, link, prijs, aantal en of het is afgevinkt. Na 60 dagen zonder gebruik gewist (fouten-mail ruimt op).
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const geldig = id => typeof id === 'string' && /^[a-f0-9]{24}$/.test(id);
const kort = (v, n) => String(v ?? '').replace(/[\u0000-\u001f]/g, ' ').slice(0, n);

function schoon(lijst) {
  if (!Array.isArray(lijst)) return [];
  return lijst.slice(0, 150).map(x => ({
    term: kort(x?.term, 80), s: kort(x?.s, 12), name: kort(x?.name, 160), link: kort(x?.link, 400),
    price: Math.round((+x?.price || 0) * 100) / 100,
    ...(x?.q > 1 ? { q: Math.min(99, Math.round(+x.q)) } : {}), ...(x?.done ? { done: true } : {}),
    ...(x?.m ? { m: kort(x.m, 80) } : {}), ...(x?.offerTill ? { offerTill: kort(x.offerTill, 10) } : {}),
  })).filter(x => x.term && x.link && x.s);
}
function schoonMaal(maal) {
  if (!Array.isArray(maal)) return [];
  return maal.slice(0, 30).map(m => ({ slug: kort(m?.slug, 80), n: kort(m?.n, 120), k: Math.max(0, Math.round(+m?.k || 0)), pp: Math.min(20, Math.max(1, Math.round(+m?.pp || 4))) })).filter(m => m.slug);
}

export default async (req) => {
  const store = getStore('samen'), url = new URL(req.url);
  if (req.method === 'GET') {
    const id = url.searchParams.get('id');
    if (!geldig(id)) return json({ fout: 'onbekend' }, 404);
    const l = await store.get(id, { type: 'json' }).catch(() => null);
    return l ? json(l) : json({ fout: 'onbekend' }, 404);
  }
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  let b; try { b = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  let id = b.id;
  if (id && !geldig(id)) return json({ fout: 'onbekend' }, 404);
  if (!id) id = crypto.randomBytes(12).toString('hex');
  const l = { lijst: schoon(b.lijst), maal: schoonMaal(b.maal), v: Date.now() };
  if (JSON.stringify(l).length > 120000) return json({ fout: 'lijst te groot' }, 413);
  await store.setJSON(id, l);
  return json({ id, v: l.v });
};

export const config = { path: '/api/samen', method: ['GET', 'POST'] };
