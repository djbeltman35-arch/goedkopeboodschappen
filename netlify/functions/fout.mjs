// "Klopt niet?": bezoekers melden een verkeerd product of een verkeerde prijs. Bewaard in Netlify Blobs (store "fouten").
//
// Tegen grapjassen en misbruik:
// - één melding verandert niets. Pas als 3 verschillende bezoekers binnen een week hetzelfde product melden, wordt het
//   automatisch tijdelijk verborgen ("betwist", zie /api/betwist) tot de dagelijkse controle;
// - per bezoeker telt elk product maar één keer, en hooguit 5 meldingen per dag (waarschuwing bij de 3e);
// - wie die grens op 3 dagen in een maand haalt, kan de rest van die maand niets meer melden;
// - bots vallen af via een verborgen veld en een minimale tijd tussen openen en versturen.
// Een bezoeker herkennen we alleen aan een onomkeerbare code van het IP-adres met een geheime sleutel per week;
// het IP-adres zelf bewaren we niet en de code verloopt vanzelf.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const kort = (v, n) => String(v ?? '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, n);
const REDENEN = { product: 'Verkeerd product', prijs: 'Prijs klopt niet', anders: 'Iets anders' };
const DREMPEL = 3, PER_DAG = 5, WAARSCHUW = 3, DAGEN_VOL = 3;
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

  // Maandblokkade: wie op 3 dagen in een maand de daggrens haalde, kan de rest van de maand niets melden.
  const maand = melding.op.slice(0, 7), mwie = hash(`${context?.ip || '?'}|${geheim}|${maand}`);
  const blok = getStore('fouten-blok'), bk = maand + '-' + mwie;
  const vol = (await blok.get(bk, { type: 'json' }).catch(() => null)) || { dagen: [] };
  const eindMaand = new Date(Date.UTC(nu.getUTCFullYear(), nu.getUTCMonth() + 1, 1)).toISOString().slice(0, 10);
  if (vol.dagen.length >= DAGEN_VOL) return json({ fout: 'Je hebt de meldknop deze maand vaak gebruikt. Je kunt deze maand niets meer melden.', blok: eindMaand }, 429);
  // Hooguit 5 meldingen per dag per bezoeker.
  const teller = getStore('fouten-teller'), tk = melding.op.slice(0, 10) + '-' + melding.wie;
  const n = +(await teller.get(tk).catch(() => 0) || 0);
  const morgen = new Date(Date.UTC(nu.getUTCFullYear(), nu.getUTCMonth(), nu.getUTCDate() + 1)).toISOString().slice(0, 10);
  if (n >= PER_DAG) {
    const dag = melding.op.slice(0, 10);
    if (!vol.dagen.includes(dag)) { vol.dagen.push(dag); await blok.setJSON(bk, vol); }
    return vol.dagen.length >= DAGEN_VOL
      ? json({ fout: 'Je hebt de meldknop deze maand vaak gebruikt. Je kunt deze maand niets meer melden.', blok: eindMaand }, 429)
      : json({ fout: `Je kunt vandaag niets meer melden. Morgen kan het weer. Let op: gebeurt dit ${DAGEN_VOL} keer in een maand, dan kun je de rest van die maand niets melden.`, blok: morgen }, 429);
  }

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
  const gedaan = n + 1;
  if (gedaan >= PER_DAG) return json({ ok: true, melding: 'Bedankt! Dit was je laatste melding voor vandaag.', blok: morgen });
  if (gedaan >= WAARSCHUW) return json({ ok: true, melding: `Bedankt! Je hebt vandaag ${gedaan} meldingen gedaan. Na ${PER_DAG} meldingen kun je vandaag niets meer melden.` });
  return json({ ok: true });
};

export const config = { path: '/api/fout', method: ['POST'] };
