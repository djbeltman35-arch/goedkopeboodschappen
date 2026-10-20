// Elke ochtend: de nieuwe "klopt niet"-meldingen in één mail naar de beheerder, per product gebundeld, daarna naar het archief.
// Producten die door 3 of meer verschillende bezoekers zijn gemeld, staan bovenaan: die zijn in de app tijdelijk verborgen.
// Meldt één bezoeker heel veel verschillende producten, dan staat dat erbij (mogelijk een grapjas).
import { getStore } from '@netlify/blobs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const NAAR = 'goedkopeboodschappen@proton.me';
const REDEN = { product: 'Verkeerd product', prijs: 'Prijs klopt niet', anders: 'Iets anders' };

export default async () => {
  const nieuw = getStore('fouten'), archief = getStore('fouten-archief'), betwist = getStore('betwist');
  // Oude tellers en oude betwiste producten opruimen.
  const teller = getStore('fouten-teller'), gisteren = new Date(Date.now() - 864e5).toISOString().slice(0, 10), weekterug = new Date(Date.now() - 14 * 864e5).toISOString();
  for (const t of (await teller.list()).blobs) if (t.key.slice(0, 10) < gisteren) await teller.delete(t.key);
  const blokStore = getStore('fouten-blok'), dezeMaand = new Date().toISOString().slice(0, 7);
  for (const t of (await blokStore.list()).blobs) if (t.key.slice(0, 7) < dezeMaand) await blokStore.delete(t.key);
  for (const { key } of (await betwist.list()).blobs) {
    const b = await betwist.get(key, { type: 'json' }).catch(() => null);
    if (!b || Object.values(b.wie || {}).every(t => t < weekterug)) await betwist.delete(key);
  }
  // Gedeelde lijsten die 60 dagen niet zijn gebruikt, opruimen.
  try {
    const samen = getStore('samen'), grens60 = Date.now() - 60 * 864e5;
    for (const { key } of (await samen.list()).blobs) {
      const l = await samen.get(key, { type: 'json' }).catch(() => null);
      if (!l || (l.v || 0) < grens60) await samen.delete(key);
    }
  } catch (e) { console.log('samen opruimen mislukt', e.message); }
  const { blobs } = await nieuw.list();
  if (!blobs.length) return new Response('geen meldingen');
  const m = [];
  for (const { key } of blobs.sort((a, b) => a.key.localeCompare(b.key))) {
    const v = await nieuw.get(key, { type: 'json' }).catch(() => null); if (v) m.push([key, v]);
  }
  // Per product bundelen; per bezoeker tellen hoeveel producten hij meldde.
  const per = new Map(), perWie = new Map();
  for (const [, v] of m) {
    const k = v.product || v.link || v.naam;
    (per.get(k) || per.set(k, []).get(k)).push(v);
    perWie.set(v.wie, (perWie.get(v.wie) || 0) + 1);
  }
  const veelmelders = [...perWie.values()].filter(n => n >= 5).length;
  const groepen = [...per.values()].map(lijst => ({ v: lijst[0], lijst, mensen: new Set(lijst.map(x => x.wie)).size, verborgen: lijst.some(x => x.aantal >= 3) }))
    .sort((a, b) => b.verborgen - a.verborgen || b.mensen - a.mensen);
  const regelTekst = g => `${g.verborgen ? '[VERBORGEN] ' : ''}${g.v.term || g.v.naam} · ${g.v.winkel} · ${g.v.naam}${g.v.prijs ? ' · ' + g.v.prijs : ''}\n   ${g.mensen} ${g.mensen === 1 ? 'persoon' : 'personen'}: ${[...new Set(g.lijst.map(x => REDEN[x.reden] || x.reden))].join(', ')}` +
    g.lijst.filter(x => x.toelichting).map(x => `\n   "${x.toelichting}"`).join('') + (g.v.link ? `\n   ${g.v.link}` : '');
  const kop = `${m.length} ${m.length === 1 ? 'melding' : 'meldingen'} over ${per.size} ${per.size === 1 ? 'product' : 'producten'}`;
  const waarschuwing = veelmelders ? `Let op: ${veelmelders} ${veelmelders === 1 ? 'bezoeker meldde' : 'bezoekers meldden'} 5 of meer producten. Dat kan een grapjas zijn; één persoon kan nooit zelf iets laten verbergen.` : '';
  const tekst = `${kop} via "Klopt niet?".\n${waarschuwing ? '\n' + waarschuwing + '\n' : ''}\n` + groepen.map((g, i) => `${i + 1}. ${regelTekst(g)}`).join('\n\n') +
    '\n\n[VERBORGEN] = door 3 of meer verschillende bezoekers gemeld en daarom een week niet getoond in de app.\nStuur dit overzicht door aan Claude om de fouten te laten verbeteren.';
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  const c = await verbind({ user, pass });
  try {
    await c.stuur(bericht({
      van: user, vanNaam: 'Goedkope Boodschappen', aan: NAAR, onderwerp: `"Klopt niet?": ${kop}`, tekst,
      html: opmaak({
        titel: `"Klopt niet?": ${kop}`,
        inhoud: (waarschuwing ? `<p style="margin:0 0 12px;padding:10px;background:#fde9e5;border-radius:8px;font-size:14px">${esc(waarschuwing)}</p>` : '') +
          '<ol style="margin:0;padding-left:20px;font-size:15px;line-height:1.5">' + groepen.map(g => `<li style="margin:0 0 12px">${g.verborgen ? '<b style="color:#e0472f">Verborgen</b> · ' : ''}<b>${esc(g.v.term || g.v.naam)}</b> · ${esc(g.v.winkel)}<br><span style="color:#5d6a61">${esc(g.v.naam)}${g.v.prijs ? ' · ' + esc(g.v.prijs) : ''}</span><br>${g.mensen} ${g.mensen === 1 ? 'persoon' : 'personen'}: ${esc([...new Set(g.lijst.map(x => REDEN[x.reden] || x.reden))].join(', '))}${g.lijst.filter(x => x.toelichting).map(x => '<br><i>"' + esc(x.toelichting) + '"</i>').join('')}${g.v.link ? '<br><a href="' + esc(g.v.link) + '">product bekijken</a>' : ''}</li>`).join('') + '</ol>',
        voet: 'Verborgen = door 3 of meer verschillende bezoekers gemeld, en daarom een week niet getoond in de app. Stuur dit overzicht door aan Claude om de fouten te laten verbeteren.',
      }),
    }));
  } finally { await c.sluit(); }
  for (const [key, v] of m) { await archief.setJSON(key, v); await nieuw.delete(key); }
  return new Response(`${m.length} meldingen verstuurd`);
};

export const config = { schedule: '0 6 * * *' };
