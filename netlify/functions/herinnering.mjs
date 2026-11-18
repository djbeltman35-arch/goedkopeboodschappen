// Eén herinnering aan wie zich (voor de nieuwsbrief of meldingen over zijn lijst) heeft aangemeld maar na 24 uur nog niet
// heeft bevestigd. Elk uur een ronde; per aanmelding hoogstens één herinnering. Na 7 dagen ruimt meldingen-sturen
// onbevestigde aanmeldingen op.
import { getStore } from '@netlify/blobs';
import { stuurBevestiging } from './email.mjs';

export default async () => {
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  if (!user || !pass) return new Response('mail niet ingesteld');
  const site = Netlify.env.get('URL') || 'https://boodschappenvergelijk.nl';
  const store = getStore('email'), { blobs } = await store.list({ prefix: 't-' });
  let n = 0;
  for (const { key } of blobs) {
    if (n >= 50) break;  // ruim binnen de dagelijkse grens van Brevo
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (!a || a.bevestigd || a.herinnerd || !a.sinds) continue;
    const oud = Date.now() - Date.parse(a.sinds);
    if (oud < 24 * 36e5 || oud > 6 * 864e5) continue;
    try {
      await stuurBevestiging(site, a, true);
      a.herinnerd = new Date().toISOString(); a.mailVerstuurd = a.herinnerd;
      await store.setJSON(key, a); n++;
    } catch (e) { console.log('herinnering mislukt', e.message); break; }
  }
  console.log(`herinnering: ${n} verstuurd, ${blobs.length} adressen bekeken`);
  return new Response(`${n} herinneringen`);
};

export const config = { schedule: '17 * * * *' };
