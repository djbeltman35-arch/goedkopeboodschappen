// Lidl-prijzen van bezoekers: foto van een Lidl-kassabon -> AI leest de producten en prijzen -> bewaard met datum.
// Lidl zet de prijzen van de meeste boodschappen niet online; zo komen er toch actuele, echte Lidl-prijzen op de site.
// POST /api/lidl-bon  {beeld: dataURL}  -> {aantal, regels:[{naam, prijs}]}  (de foto zelf wordt niet bewaard)
// GET  /api/lidl-bon                    -> per product de nieuwste prijs van de laatste 60 dagen (voor de build)
// Bewaard per bon: alleen datum van de bon, producten en prijzen. Geen foto, geen IP, geen winkeladres, geen betaalgegevens.
// Tegen misbruik: hooguit 5 bonnen per dag per bezoeker (onomkeerbare code), 150 per dag in totaal, alleen Lidl, alleen bonnen van de laatste 30 dagen.
// Nodig in Netlify: ANTHROPIC_API_KEY (dezelfde als foto-lijst).
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const json = (data, status = 200, cache = 'no-store') => Response.json(data, { status, headers: { 'Cache-Control': cache, 'X-Robots-Tag': 'noindex' } });
const hash = s => crypto.createHash('sha256').update(s).digest('hex').slice(0, 24);
const PER_BEZOEKER = 5, PER_DAG = 150, DAGEN_GELDIG = 60;

const OPDRACHT = `Dit is een foto van een kassabon. Antwoord ALLEEN met JSON, zonder uitleg:
{"lidl": true/false, "datum": "JJJJ-MM-DD" of null, "regels": [{"bon": "tekst zoals op de bon", "naam": "productnaam", "prijs": 1.23, "inhoud": "500 g" of null}]}
Regels:
- "lidl": true alleen als het duidelijk een bon van Lidl is (logo of naam Lidl op de bon).
- "datum": de aankoopdatum op de bon.
- Eén regel per product. "prijs" is de prijs van ÉÉN stuk zonder korting (bij "2 x 1,29" is de prijs 1.29). Bij gewogen producten ("0,512 kg x 2,99 EUR/kg") is "prijs" 2.99 en "inhoud" "1 kg".
- "naam": gewone Nederlandse productnaam, zoals een klant hem zou zoeken ("HALFV MELK" wordt "Halfvolle melk", "KIPFIL" wordt "Kipfilet"). Verzin geen merk dat er niet staat.
- "inhoud": alleen als die op de bon staat (bijv. "1L", "500G"), anders null.
- Sla over: kortingsregels, statiegeld, tassen, totalen, btw, betaalregels, Lidl Plus-regels, regels die je niet goed kunt lezen.
Is het geen kassabon, antwoord dan {"lidl": false, "datum": null, "regels": []}.`;

const schoon = t => String(t || '').replace(/[^\p{L}\p{N}%'&.,()\- ]/gu, ' ').replace(/\s+/g, ' ').trim();
const sleutel = n => schoon(n).toLowerCase();

async function export_() {
  const st = getStore('lidl-bonnen'), grens = new Date(Date.now() - DAGEN_GELDIG * 864e5).toISOString().slice(0, 10);
  const { blobs } = await st.list().catch(() => ({ blobs: [] }));
  const per = new Map();
  for (const { key } of blobs) {
    if (key.slice(0, 10) < grens) continue;
    const b = await st.get(key, { type: 'json' }).catch(() => null); if (!b) continue;
    for (const r of b.regels || []) {
      const k = sleutel(r.naam), oud = per.get(k);
      if (!oud || b.datum > oud.datum) per.set(k, { n: r.naam, p: r.prijs, s: r.inhoud || '', datum: b.datum, bonnen: (oud?.bonnen || 0) + 1 });
      else oud.bonnen++;
    }
  }
  return json({ bijgewerkt: new Date().toISOString(), producten: [...per.values()].sort((a, b) => a.n.localeCompare(b.n)) }, 200, 'public, max-age=600');
}

export default async (req, context) => {
  if (req.method === 'GET') return export_();
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  const api = Netlify.env.get('ANTHROPIC_API_KEY');
  if (!api) return json({ fout: 'Het inlezen van bonnen werkt nu even niet. Probeer het later nog eens.' }, 503);
  let b; try { b = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  const m = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/.exec(String(b?.beeld || ''));
  if (!m) return json({ fout: 'Geen geldige foto.' }, 400);
  if (m[2].length > 4_500_000) return json({ fout: 'De foto is te groot.' }, 413);

  const geheim = Netlify.env.get('FOUT_GEHEIM') || Netlify.env.get('GMAIL_APP_PASSWORD') || 'goedkope-boodschappen';
  const dag = new Date().toISOString().slice(0, 10), wie = hash(`${context?.ip || '?'}|${geheim}|${dag}`);
  const teller = getStore('lidl-bon-teller');
  const nWie = +(await teller.get(`${dag}-${wie}`).catch(() => 0)) || 0, nDag = +(await teller.get(`${dag}-totaal`).catch(() => 0)) || 0;
  if (nWie >= PER_BEZOEKER || nDag >= PER_DAG) return json({ fout: 'Je hebt vandaag al genoeg bonnen gestuurd. Dank je wel! Morgen kan het weer.' }, 429);
  await Promise.all([teller.set(`${dag}-${wie}`, String(nWie + 1)), teller.set(`${dag}-totaal`, String(nDag + 1))]).catch(() => {});

  let d;
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': api, 'anthropic-version': '2026-10-21', 'content-type': 'application/json' },
      body: JSON.stringify({
        model: Netlify.env.get('FOTO_MODEL') || 'claude-haiku-5-5', max_tokens: 4000,
        messages: [{ role: 'user', content: [{ type: 'image', source: { type: 'base64', media_type: m[1], data: m[2] } }, { type: 'text', text: OPDRACHT }] }],
      }),
      signal: AbortSignal.timeout(24000),
    });
    if (!r.ok) throw new Error('AI ' + r.status);
    const tekst = ((await r.json()).content || []).filter(c => c.type === 'text').map(c => c.text).join('');
    d = JSON.parse(tekst.slice(tekst.indexOf('{'), tekst.lastIndexOf('}') + 1));
  } catch (e) {
    console.error('lidl-bon mislukt', e?.message);
    return json({ fout: 'De bon kon niet gelezen worden. Probeer een scherpere foto, recht van boven en met genoeg licht.' }, 502);
  }

  if (!d?.lidl) return json({ fout: 'Dit lijkt geen Lidl-bon. Alleen bonnen van Lidl helpen hier, omdat de andere supermarkten hun prijzen al online zetten.' }, 422);
  const datum = /^\d{4}-\d{2}-\d{2}$/.test(d.datum || '') ? d.datum : null;
  const leeftijd = datum ? (Date.parse(dag) - Date.parse(datum)) / 864e5 : null;
  if (leeftijd == null || leeftijd < -1 || leeftijd > 30) return json({ fout: datum ? 'Deze bon is ouder dan 30 dagen. Alleen recente bonnen geven actuele prijzen.' : 'De datum op de bon is niet te lezen. Zorg dat de datum ook op de foto staat.' }, 422);
  const regels = [], gezien = new Set();
  for (const r of Array.isArray(d.regels) ? d.regels : []) {
    const naam = schoon(r?.naam).slice(0, 60), prijs = Math.round(+r?.prijs * 100) / 100, inhoud = schoon(r?.inhoud).slice(0, 20) || null;
    if (naam.length < 3 || !(prijs >= 0.05 && prijs <= 80) || gezien.has(sleutel(naam))) continue;
    gezien.add(sleutel(naam)); regels.push({ naam: naam[0].toUpperCase() + naam.slice(1), prijs, inhoud });
  }
  if (!regels.length) return json({ fout: 'Er zijn geen producten met een prijs gevonden op deze bon. Probeer een scherpere foto.' }, 422);
  // Dezelfde bon twee keer telt één keer: de sleutel is de bondatum plus de inhoud.
  const id = hash(datum + JSON.stringify(regels.map(r => [r.naam, r.prijs])));
  await getStore('lidl-bonnen').setJSON(`${datum}/${id}`, { datum, regels, op: new Date().toISOString() });
  return json({ aantal: regels.length, datum, regels: regels.map(({ naam, prijs }) => ({ naam, prijs })) });
};

export const config = { path: '/api/lidl-bon', method: ['GET', 'POST'] };
