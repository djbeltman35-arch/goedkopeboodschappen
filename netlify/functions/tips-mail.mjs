// Elke ochtend: de nieuwe tips uit het tipsformulier in één mail naar de beheerder, daarna naar het archief.
import { getStore } from '@netlify/blobs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const NAAR = 'goedkopeboodschappen@proton.me';
const SOORT = { tip: 'Tip', idee: 'Idee voor de site', fout: 'Fout gezien', product: 'Product of winkel mist', vraag: 'Vraag', anders: 'Iets anders' };

export default async () => {
  const nieuw = getStore('tips'), archief = getStore('tips-archief'), teller = getStore('tips-teller');
  const gisteren = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
  for (const t of (await teller.list()).blobs) if (t.key.slice(0, 10) < gisteren) await teller.delete(t.key);
  const { blobs } = await nieuw.list();
  if (!blobs.length) return new Response('geen tips');
  const t = [];
  for (const { key } of blobs.sort((a, b) => a.key.localeCompare(b.key))) { const v = await nieuw.get(key, { type: 'json' }).catch(() => null); if (v) t.push([key, v]); }
  const kop = `${t.length} ${t.length === 1 ? 'nieuwe tip' : 'nieuwe tips'}`;
  const regel = v => `${SOORT[v.soort] || 'Tip'}${v.naam ? ' van ' + v.naam : ''}${v.email ? ' <' + v.email + '>' : ''} (${v.op.slice(0, 16).replace('T', ' ')})\n${v.bericht}${v.pagina ? '\nVanaf: ' + v.pagina : ''}`;
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  const c = await verbind({ user, pass });
  try {
    await c.stuur(bericht({
      van: user, vanNaam: 'Goedkope Boodschappen', aan: NAAR, onderwerp: `Tipsformulier: ${kop}`,
      tekst: `${kop} via het tipsformulier.\n\n` + t.map(([, v], i) => `${i + 1}. ${regel(v)}`).join('\n\n'),
      html: opmaak({ titel: `Tipsformulier: ${kop}`,
        inhoud: '<ol style="margin:0;padding-left:20px;font-size:15px;line-height:1.5">' + t.map(([, v]) => `<li style="margin:0 0 14px"><b>${esc(SOORT[v.soort] || 'Tip')}</b>${v.naam ? ' van ' + esc(v.naam) : ''}${v.email ? ` &lt;<a href="mailto:${esc(v.email)}">${esc(v.email)}</a>&gt;` : ''}<br><span style="white-space:pre-wrap">${esc(v.bericht)}</span>${v.pagina ? `<br><small style="color:#666">Vanaf ${esc(v.pagina)}</small>` : ''}</li>`).join('') + '</ol>',
        voet: 'Antwoorden kan door op het e-mailadres te klikken (als de afzender dat heeft ingevuld).' }),
    }));
  } finally { await c.sluit(); }
  for (const [key, v] of t) { await archief.setJSON(key, v); await nieuw.delete(key); }
  return new Response(`${t.length} tips verstuurd`);
};

export const config = { schedule: '10 6 * * *' };
