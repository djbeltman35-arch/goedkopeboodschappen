// Leest nieuwe Nettorama-folders uit met AI (achtergrondfunctie, mag tot 15 minuten duren) en bewaart de acties in
// Netlify Blobs. Een folder die al is uitgelezen wordt overgeslagen, dus vaker aanroepen kost niets.
// Wordt gestart door nettorama-plan.mjs (elke ochtend en vrijdagavond na 17.00 uur, als de nieuwe folder online komt).
import { getStore } from '@netlify/blobs';
import { bijwerken } from '../../ophalen/folder-nettorama.mjs';

export default async () => {
  const st = getStore('nettorama');
  const bewaard = await st.get('folders', { type: 'json' }).catch(() => null);
  const nieuw = await bijwerken(bewaard, Netlify.env.get('ANTHROPIC_API_KEY'));
  await st.setJSON('folders', nieuw);
};
