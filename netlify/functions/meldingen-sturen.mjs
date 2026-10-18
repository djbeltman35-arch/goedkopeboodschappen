// Elke ochtend: per abonnee kijken of er iets van de lijst in de aanbieding is, en daar één melding over sturen.
// Een aanbieding wordt maar één keer gemeld. Verlopen abonnementen (404/410) worden opgeruimd.
import { getStore } from '@netlify/blobs';
import { stuur } from '../webpush.mjs';
import { passend, sleutelVan } from '../zoek.mjs';

const NAMEN = { ah: 'AH', jumbo: 'Jumbo', lidl: 'Lidl', aldi: 'Aldi', plus: 'PLUS', dirk: 'Dirk', hoogvliet: 'Hoogvliet', dekamarkt: 'DekaMarkt', poiesz: 'Poiesz' };
const eur = v => '€ ' + v.toFixed(2).replace('.', ',');

export default async (req, context) => {
  const pub = Netlify.env.get('VAPID_PUBLIC'), priv = Netlify.env.get('VAPID_PRIVATE');
  if (!pub || !priv) { console.log('VAPID-sleutels ontbreken'); return; }
  const site = Netlify.env.get('URL') || context?.site?.url || 'https://goedkopeboodschappen.netlify.app';
  const offers = (await (await fetch(`${site}/data/aanbiedingen.json`)).json()).offers || [];
  const store = getStore('meldingen');
  const { blobs } = await store.list();
  let gestuurd = 0, weg = 0;
  const grens = new Date(Date.now() - 45 * 864e5).toISOString().slice(0, 10);
  await Promise.all(blobs.map(async ({ key }) => {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (!a?.sub || !a.termen?.length) return;
    const nieuw = passend(offers, a.termen, a.winkels).filter(({ o }) => !a.verstuurd[sleutelVan(o)]);
    if (!nieuw.length) return;
    const n = nieuw.length;
    const titel = n === 1 ? `🔥 ${nieuw[0].term} is in de aanbieding` : `🔥 ${n} artikelen van je lijst in de aanbieding`;
    const tekst = nieuw.slice(0, 4).map(({ o }) => `${NAMEN[o.s] || o.s}: ${o.n} ${eur(o.p)}${o.lbl ? ' (' + o.lbl + ')' : ''}`).join('\n') + (n > 4 ? `\n+ ${n - 4} meer` : '');
    try {
      const status = await stuur(a.sub, { titel, tekst, url: '/?bron=melding#lijst' }, pub, priv);
      if (status === 404 || status === 410) { await store.delete(key); weg++; return; }
      if (status >= 400) { console.log('push mislukt', status); return; }
      gestuurd++;
      const d = new Date().toISOString().slice(0, 10);
      for (const { o } of nieuw) a.verstuurd[sleutelVan(o)] = d;
      for (const [k, v] of Object.entries(a.verstuurd)) if (v < grens) delete a.verstuurd[k];
      await store.setJSON(key, a);
    } catch (e) { console.log('push fout', e.message); }
  }));
  console.log(`meldingen: ${gestuurd} verstuurd, ${weg} verlopen abonnementen opgeruimd, ${blobs.length} abonnees`);
};

// 06:20 UTC = 08:20 in de zomer, 07:20 in de winter: na het ophalen van de aanbiedingen en het opnieuw bouwen van de site.
export const config = { schedule: '20 6 * * *' };
