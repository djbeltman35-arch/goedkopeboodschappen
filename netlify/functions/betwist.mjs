// Producten die door minstens 3 verschillende bezoekers als "klopt niet" zijn gemeld: de app laat ze tijdelijk weg.
// Na 7 dagen komen ze vanzelf terug (de prijzen worden elke dag ververst; de dagelijkse mail noemt ze ter controle).
import { getStore } from '@netlify/blobs';

export default async () => {
  const s = getStore('betwist'), grens = new Date(Date.now() - 7 * 864e5).toISOString(), links = [];
  for (const { key } of (await s.list()).blobs) {
    const b = await s.get(key, { type: 'json' }).catch(() => null);
    if (b?.verborgen && b.verborgen >= grens && b.link) links.push(b.link);
  }
  return Response.json({ links }, { headers: { 'Cache-Control': 'public, max-age=600' } });
};

export const config = { path: '/api/betwist', method: ['GET'] };
