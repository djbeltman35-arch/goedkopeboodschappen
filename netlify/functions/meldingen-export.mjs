// Alleen-lezen export van "Klopt niet?"-meldingen en tips/contactberichten van de laatste dagen, voor de dagelijkse
// automatische verwerking. Toegang met een geheime sleutel in de kop "x-sleutel"; hier staat alleen de SHA-256 ervan.
// Ook: per dag de tellers van de fotolezer (foto-lijst.mjs), zonder bezoekerscodes.
// Gebruik: GET /api/meldingen-export?dagen=2
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const HASH = 'b28c11e7e70ad85cc7f70609d7127b4f270912c7e3a865b761d893c6f2e6a603';
const json = (d, status = 200) => Response.json(d, { status, headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' } });

async function lees(naam, dagen) {
  const store = getStore(naam), uit = [];
  for (const dag of dagen) {
    const { blobs } = await store.list({ prefix: dag }).catch(() => ({ blobs: [] }));
    for (const { key } of blobs) { const v = await store.get(key, { type: 'json' }).catch(() => null); if (v) uit.push({ key, ...v }); }
  }
  return uit;
}

export default async req => {
  const s = req.headers.get('x-sleutel') || '';
  const h = crypto.createHash('sha256').update(s).digest();
  if (!crypto.timingSafeEqual(h, Buffer.from(HASH, 'hex'))) { await new Promise(r => setTimeout(r, 1500)); return json({ fout: 'geen toegang' }, 403); }
  const n = Math.min(14, Math.max(1, +new URL(req.url).searchParams.get('dagen') || 2));
  const dagen = Array.from({ length: n }, (_, i) => new Date(Date.now() - i * 864e5).toISOString().slice(0, 10));
  const [f1, f2, t1, t2] = await Promise.all([lees('fouten', dagen), lees('fouten-archief', dagen), lees('tips', dagen), lees('tips-archief', dagen)]);
  const zonderWie = a => a.map(({ wie, email, ...r }) => ({ ...r, metEmail: !!email })).sort((a, b) => String(a.op).localeCompare(String(b.op)));
  const fotos = await Promise.all(dagen.map(async dag => {
    const st = getStore('foto-teller'), { blobs } = await st.list({ prefix: dag }).catch(() => ({ blobs: [] }));
    const t = { dag, totaal: 0, bezoekersOpLimiet: 0, geweigerd: 0, storing: 0, zonderSleutel: false };
    for (const { key } of blobs) {
      const k = key.slice(dag.length + 1), v = +(await st.get(key).catch(() => 0)) || 0;
      if (k === 'totaal') t.totaal = v; else if (k === 'geweigerd') t.geweigerd = v; else if (k === 'storing') t.storing = v;
      else if (k === 'zondersleutel') t.zonderSleutel = true; else if (v >= 10) t.bezoekersOpLimiet++;
    }
    t.dagLimietBereikt = t.totaal >= 400;
    return t;
  }));
  return json({ dagen, fotos, meldingen: zonderWie([...f1, ...f2]), tips: zonderWie([...t1, ...t2]) });
};

export const config = { path: '/api/meldingen-export', method: ['GET'] };
