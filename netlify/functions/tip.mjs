// Tipsformulier: bezoekers sturen een tip, idee of vraag. Bewaard in Netlify Blobs (store "tips"); elke ochtend gemaild (tips-mail.mjs).
// Tegen misbruik: woordfilter (vloeken, schelden, seksueel getint), verborgen veld en minimale tijd tegen bots,
// en hooguit 5 berichten per dag per bezoeker (herkend aan een onomkeerbare code van het IP-adres; het IP-adres zelf bewaren we niet).
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';
import { verbodenWoorden } from '../../site/woordfilter.mjs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const kort = (v, n) => String(v ?? '').replace(/[\u0000-\u0008\u000b-\u001f]/g, ' ').trim().slice(0, n);
const SOORTEN = { tip: 'Tip', idee: 'Idee voor de site', fout: 'Fout gezien', product: 'Product of winkel mist', vraag: 'Vraag', pers: 'Pers en media', samenwerking: 'Samenwerking', privacy: 'Privacy', anders: 'Overig' };
const NAAR = 'info@boodschappenvergelijk.nl';
const hash = s => crypto.createHash('sha256').update(s).digest('hex').slice(0, 24);

export default async (req, context) => {
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  let b; try { b = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  if (b.website || !(+b.ms >= 3000)) return json({ ok: true });               // bot: doen alsof het gelukt is
  const tip = { soort: SOORTEN[b.soort] ? b.soort : 'tip', bericht: kort(b.bericht, 1500), naam: kort(b.naam, 60), email: kort(b.email, 120), pagina: kort(b.pagina, 200), op: new Date().toISOString() };
  if (tip.bericht.length < 10) return json({ fout: 'Schrijf iets meer: minstens 10 tekens.' }, 400);
  if (tip.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(tip.email)) return json({ fout: 'Dat e-mailadres klopt niet. Je mag het ook leeg laten.' }, 400);
  if (verbodenWoorden(`${tip.bericht} ${tip.naam}`).length) return json({ fout: 'Je bericht bevat woorden die we niet toestaan. Pas het aan en probeer het opnieuw.' }, 400);
  if ((tip.bericht.match(/https?:\/\//g) || []).length > 2) return json({ fout: 'Gebruik hooguit 2 links in je bericht.' }, 400);
  const geheim = Netlify.env.get('FOUT_GEHEIM') || Netlify.env.get('GMAIL_APP_PASSWORD') || 'goedkope-boodschappen';
  const dag = tip.op.slice(0, 10); tip.wie = hash(`${context?.ip || '?'}|${geheim}|${dag}`);
  const teller = getStore('tips-teller'), tk = `${dag}-${tip.wie}`;
  const n = +(await teller.get(tk).catch(() => 0)) || 0;
  if (n >= 5) return json({ fout: 'Je hebt vandaag al 5 berichten gestuurd. Dank je wel! Probeer het morgen weer.' }, 429);
  await teller.set(tk, String(n + 1));
  const key = `${tip.op}-${tip.wie}`;
  // Meteen mailen; lukt dat niet, dan komt het bericht alsnog in de ochtendmail (tips-mail.mjs).
  try {
    const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
    if (!user || !pass) throw new Error('geen mailgegevens');
    const s = SOORTEN[tip.soort], wie = (tip.naam || tip.email || 'een bezoeker').replace(/\s+/g, ' ');
    const c = await verbind({ user, pass });
    try {
      await c.stuur(bericht({
        van: process.env.MAIL_FROM || user, vanNaam: 'Goedkope Boodschappen', aan: NAAR, antwoordAan: tip.email || undefined,
        onderwerp: `Contact: ${s} van ${wie}`,
        tekst: `${s} van ${wie}${tip.email ? ' <' + tip.email + '>' : ''}\n\n${tip.bericht}${tip.pagina ? '\n\nVanaf: ' + tip.pagina : ''}`,
        html: opmaak({ titel: `${s}`, inhoud: `<p style="margin:0 0 10px"><b>Van:</b> ${esc(tip.naam || 'geen naam')}${tip.email ? ` &lt;<a href="mailto:${esc(tip.email)}">${esc(tip.email)}</a>&gt;` : ''}</p><p style="white-space:pre-wrap;margin:0">${esc(tip.bericht)}</p>${tip.pagina ? `<p style="color:#666;font-size:13px">Vanaf ${esc(tip.pagina)}</p>` : ''}`,
          voet: tip.email ? 'Op Beantwoorden klikken gaat direct naar de afzender.' : 'De afzender heeft geen e-mailadres ingevuld.' }),
      }));
    } finally { await c.sluit(); }
    await getStore('tips-archief').setJSON(key, tip);
  } catch (e) {
    console.error('contactmail mislukt', e?.message);
    await getStore('tips').setJSON(key, tip);
  }
  return json({ ok: true });
};

export const config = { path: '/api/tip', method: ['POST'] };
