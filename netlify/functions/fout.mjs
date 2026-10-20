// "Klopt niet?": bezoekers melden een verkeerd product of een verkeerde prijs. Bewaard in Netlify Blobs (store "fouten").
//
// Tegen grapjassen en misbruik:
// - één melding verandert niets. Pas als 3 verschillende bezoekers binnen een week hetzelfde product melden, wordt het
//   automatisch tijdelijk verborgen ("betwist", zie /api/betwist) tot de dagelijkse controle;
// - per bezoeker telt elk product maar één keer, en hooguit 10 meldingen per dag;
// - bots vallen af via een verborgen veld en een minimale tijd tussen openen en versturen.
// Een bezoeker herkennen we alleen aan een onomkeerbare code van het IP-adres met een geheime sleutel per week;
// het IP-adres zelf bewaren we niet en de code verloopt vanzelf.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const kort = (v, n) => String(v ?? '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, n);
const REDENEN = { product: 'Verkeerd product', prijs: 'Prijs klopt niet', anders: 'Iets anders' };
const DREMPEL = 3, PER_DAG = 10;
const week = d => { const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())); t.setUTCDate(t.getUTCDate() + 4 - (t.getUTCDay() || 7)); return t.getUTCFullYear() + '-' + Math.ceil(((t - Date.UTC(t.getUTCFullYear(), 0, 1)) / 864e5 + 1) / 7); };
const hash = s => crypto.createHash('sha256').update(s).digest('hex').slice(0, 24);

export default async (req, context) => {
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  let b; try { b = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  // Bots: het verborgen veld moet leeg zijn en het venster moet minstens 2 seconden open zijn geweest.
  if (b.website || !(+b.ms >= 2000)) return json({ ok: true });
  const nu = new Date();
  const melding = {
    term: kort(b.term, 80), winkel: kort(b.winkel, 20), naam: kort(b.naam, 160), link: kort(b.link, 300),
    prijs: kort(b.prijs, 20), reden: REDENEN[b.reden] ? b.reden : 'anders', toelichting: kort(b.toelichting, 300),
    pagina: kort(b.pagina, 200), op: nu.toISOString(),
  };
  if (!melding.term && !melding.naam) return json({ fout: 'product ontbreekt' }, 400);
  const geheim = Netlify.env.get('FOUT_GEHEIM') || Netlify.env.get('GMAIL_APP_PASSWORD') || 'goedkope-boodschappen';
  melding.wie = hash(`${context?.ip || '?'}|${geheim}|${week(nu)}`);
  const product = hash(melding.link || melding.naam);

  // Hooguit 10 meldingen per dag per bezoeker.
  const teller = getStore('fouten-teller'), tk = melding.op.slice(0, 10) + '-' + melding.wie;
  const n = +(await teller.get(tk).catch(() => 0) || 0);
  if (n >= PER_DAG) return json({ fout: 'Je hebt vandaag al veel gemeld. Dank je wel!' }, 429);

  // Per bezoeker telt elk product één keer.
  const betwist = getStore('betwist');
  const b0 = await betwist.get(product, { type: 'json' }).catch(() => null) || { link: melding.link, naam: melding.naam, term: melding.term, winkel: melding.winkel, wie: {}, sinds: melding.op };
  if (b0.wie[melding.wie]) return json({ ok: true, al: true });
  await teller.set(tk, String(n + 1));
  b0.wie[melding.wie] = melding.op;
  // Alleen meldingen van de afgelopen 7 dagen tellen mee.
  const grens = new Date(nu - 7 * 864e5).toISOString();
  for (const [w, t] of Object.entries(b0.wie)) if (t < grens) delete b0.wie[w];
  const aantal = Object.keys(b0.wie).length;
  if (aantal >= DREMPEL && !b0.verborgen) b0.verborgen = melding.op;
  await betwist.setJSON(product, b0);
  await getStore('fouten').setJSON(`${melding.op}-${crypto.randomBytes(4).toString('hex')}`, { ...melding, product, aantal });
  return json({ ok: true });
};

export const config = { path: '/api/fout', method: ['POST'] };
