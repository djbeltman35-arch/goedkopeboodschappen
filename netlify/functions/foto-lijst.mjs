// Foto van een (handgeschreven) boodschappenlijstje of kassabon lezen met een AI-model met beeldherkenning (Claude, Anthropic).
// Tesseract in de browser leest alleen gedrukte tekst; handschrift lukt daarmee niet. Deze functie is daarom de eerste keus;
// lukt ze niet (geen sleutel, limiet, storing), dan valt de app terug op Tesseract op het toestel.
// De foto wordt alleen doorgestuurd om de tekst te lezen en nergens bewaard of gelogd.
// Tegen misbruik en kosten: hooguit 10 foto's per dag per bezoeker (onomkeerbare code van het IP-adres) en 400 per dag in totaal.
// Tellers per dag (foto-teller): <dag>-totaal, <dag>-<bezoeker>, <dag>-geweigerd, <dag>-storing, <dag>-zondersleutel; te zien in /api/meldingen-export.
// Nodig in Netlify: ANTHROPIC_API_KEY. Optioneel: FOTO_MODEL (standaard claude-haiku-5-5).
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const hash = s => crypto.createHash('sha256').update(s).digest('hex').slice(0, 24);
const PER_BEZOEKER = 10, PER_DAG = 400;

const OPDRACHT = `Dit is een foto van een boodschappenlijstje (vaak handgeschreven) of een kassabon van een Nederlandse supermarkt.
Schrijf de boodschappen over, één product per regel, zodat iemand ze in een prijsvergelijker kan zoeken.
Regels:
- Gewone Nederlandse spelling, kleine letters. Verbeter schrijffouten en afkortingen (kassabon: "HALFV MLK" wordt "halfvolle melk").
- Laat gewichten, inhoud en prijzen weg ("200 gr. peultjes" wordt "peultjes", "400 ml tomatensaus" wordt "tomatensaus").
- Staat er een aantal stuks of pakken voor ("2 pakken melk", "3x yoghurt"), zet dat getal vooraan: "2 melk".
- Staan er alternatieven met een schuine streep ("spruiten/sperzieboontjes"), zet ze elk op een eigen regel.
- Laat algemene woorden als "fruit", "beleg" of "vlees" gewoon staan zoals ze er staan.
- Laat krabbels, doorgestreepte woorden, winkelnamen, totalen, betaalregels en datums weg.
- Twijfel je over een woord, kies dan het meest waarschijnlijke boodschappenproduct.
Antwoord alleen met de regels, zonder uitleg, nummering of opsommingstekens. Staat er geen boodschappenlijst of kassabon op de foto, antwoord dan alleen: GEEN`;

export default async (req, context) => {
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  const sleutel = Netlify.env.get('ANTHROPIC_API_KEY');
  if (!sleutel) { await getStore('foto-teller').set(`${new Date().toISOString().slice(0, 10)}-zondersleutel`, '1').catch(() => {}); return json({ fout: 'niet beschikbaar', terug: true }, 503); }
  let b; try { b = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  const m = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/.exec(String(b?.beeld || ''));
  if (!m) return json({ fout: 'Geen geldige foto.' }, 400);
  if (m[2].length > 4_500_000) return json({ fout: 'De foto is te groot.' }, 413);

  // Limieten (eerst tellen, dan pas de dure aanroep)
  const geheim = Netlify.env.get('FOUT_GEHEIM') || Netlify.env.get('GMAIL_APP_PASSWORD') || 'goedkope-boodschappen';
  const dag = new Date().toISOString().slice(0, 10), wie = hash(`${context?.ip || '?'}|${geheim}|${dag}`);
  const teller = getStore('foto-teller');
  const nWie = +(await teller.get(`${dag}-${wie}`).catch(() => 0)) || 0;
  const nDag = +(await teller.get(`${dag}-totaal`).catch(() => 0)) || 0;
  const tel = async k => teller.set(`${dag}-${k}`, String((+(await teller.get(`${dag}-${k}`).catch(() => 0)) || 0) + 1)).catch(() => {});
  if (nWie >= PER_BEZOEKER || nDag >= PER_DAG) { await tel('geweigerd'); return json({ fout: 'limiet', terug: true }, 429); }
  await Promise.all([teller.set(`${dag}-${wie}`, String(nWie + 1)), teller.set(`${dag}-totaal`, String(nDag + 1))]).catch(() => {});

  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': sleutel, 'anthropic-version': '2026-10-21', 'content-type': 'application/json' },
      body: JSON.stringify({
        model: Netlify.env.get('FOTO_MODEL') || 'claude-haiku-5-5',
        max_tokens: 2000,                       // ruimte voor het denkwerk van het model plus de lijst
        messages: [{ role: 'user', content: [
          { type: 'image', source: { type: 'base64', media_type: m[1], data: m[2] } },
          { type: 'text', text: OPDRACHT },
        ] }],
      }),
      signal: AbortSignal.timeout(22000),
    });
    if (!r.ok) { console.error('foto-lijst: AI gaf', r.status); await tel('storing'); return json({ fout: 'storing', terug: true }, 502); }
    const d = await r.json();
    const tekst = (d.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n').trim();
    if (/^GEEN\b/i.test(tekst)) return json({ regels: [] });
    const regels = [...new Set(tekst.split(/\n+/)
      .map(t => t.replace(/^\s*(?:[-•*·]+|\d{1,2}[.)])\s*/, '').replace(/[^\p{L}\p{N}'&\- ]/gu, ' ').replace(/\s+/g, ' ').trim().toLowerCase())
      .filter(t => t.length >= 2 && t.length <= 60))].slice(0, 60);
    return json({ regels });
  } catch (e) {
    console.error('foto-lijst mislukt', e?.name); await tel('storing');
    return json({ fout: 'storing', terug: true }, 502);
  }
};

export const config = { path: '/api/foto-lijst', method: ['POST'] };
