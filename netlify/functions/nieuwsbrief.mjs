// Nieuwsbrief: elke ochtend (wie "dagelijks" koos) of elke maandag (wie "wekelijks" koos) de beste aanbiedingen.
// Aanmelden gaat via /api/email (met bevestigingsmail); afmelden met één klik onderaan elke mail.
// Aanbiedingen uit /data/aanbiedingen.json van de site. Alleen de supermarkten die iemand gekozen heeft (geen keuze = alle).
// Maximaal MAX_PER_DAG mails per dag (gratis Brevo-plan: 300 per dag; meldingen over je lijst gaan voor, zie MAX_MELDINGEN); de rest gaat de volgende keer.
import { getStore } from '@netlify/blobs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const NAMEN = { ah: 'Albert Heijn', jumbo: 'Jumbo', lidl: 'Lidl', aldi: 'Aldi', plus: 'PLUS', dirk: 'Dirk', hoogvliet: 'Hoogvliet', dekamarkt: 'DekaMarkt', poiesz: 'Poiesz', spar: 'SPAR', vomar: 'Vomar' };
const eur = v => '€ ' + v.toFixed(2).replace('.', ',');
const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());
const weekdag = () => new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Amsterdam', weekday: 'short' }).format(new Date());
// Geen non-food in de nieuwsbrief: mensen willen boodschappen.
const GEEN = /^(Huishouden|Verzorging|Drogisterij|Non-food|Overig)/i;

// De beste aanbiedingen: grootste korting eerst, per winkel hoogstens 3, liefst acties die vandaag beginnen.
export function besteAanbiedingen(offers, winkels, n = 12) {
  const dag = vandaag();
  const mag = o => (!winkels?.length || winkels.includes(o.s)) && o.was > o.p && o.p > 0 && (!o.t || o.t >= dag) && (!o.v || o.v <= dag) && !GEEN.test(o.c || '');
  const pct = o => 1 - o.p / o.was;
  const lijst = offers.filter(mag).filter(o => pct(o) >= 0.2 && pct(o) < 0.9)
    .sort((a, b) => ((b.v === dag) - (a.v === dag)) * 0.1 + pct(b) - pct(a));
  const per = {}, uit = [];
  const gezien = new Set();
  for (const o of lijst) {
    const k = o.s + ' ' + String(o.n).toLowerCase().split(/\s+/).slice(0, 3).join(' ');  // geen "Hak Witte bonen" én "Hak Witte bonen 4-pack"
    if (gezien.has(k) || (per[o.s] || 0) >= 3) continue;
    gezien.add(k); per[o.s] = (per[o.s] || 0) + 1; uit.push(o); if (uit.length >= n) break;
  }
  return uit;
}

export default async (req, context) => {
  const site = Netlify.env.get('URL') || context?.site?.url || 'https://boodschappenvergelijk.nl';
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  if (!user || !pass) return new Response('mail niet ingesteld');
  const max = +(Netlify.env.get('MAX_PER_DAG') || 120);
  const offers = (await (await fetch(`${site}/data/aanbiedingen.json`)).json()).offers || [];
  const dag = vandaag(), maandag = weekdag() === 'Mon';
  const store = getStore('email'), { blobs } = await store.list();
  let c = null, n = 0;
  try {
    for (const { key } of blobs) {
      if (n >= max) break;
      if (!key.startsWith('t-')) continue;
      const a = await store.get(key, { type: 'json' }).catch(() => null);
      if (!a?.bevestigd || !a.nieuws || a.nieuwsVerstuurd === dag) continue;
      if (a.nieuws === 'week' && !maandag) continue;
      const lijst = besteAanbiedingen(offers, a.winkels);
      if (lijst.length < 3) continue;
      const uit = `${site}/api/email?uit=${a.token}`;
      const kop = a.nieuws === 'dag' ? 'De beste aanbiedingen van vandaag' : 'De beste aanbiedingen van deze week';
      const regel = o => `${o.n}${o.sz ? ` (${o.sz})` : ''}: ${NAMEN[o.s] || o.s} ${eur(o.p)}, was ${eur(o.was)} (-${Math.round((1 - o.p / o.was) * 100)}%)${o.lbl ? `, ${o.lbl}` : ''}`;
      const tekst = `${kop}\n\n` + lijst.map(o => '- ' + regel(o)).join('\n') +
        `\n\nAlle aanbiedingen vergeleken: ${site}/aanbiedingen/?bron=nieuwsbrief\n\nGeen nieuwsbrief meer? Meld je af: ${uit}\n\nGoedkope Boodschappen is gratis en zonder reclame. De prijs aan de kassa is leidend.`;
      const html = opmaak({
        titel: kop,
        inhoud: `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:15px">` +
          lijst.map(o => `<tr><td style="padding:9px 0;border-bottom:1px solid #e1e7dc"><a href="${esc(`${site}/?q=${encodeURIComponent(o.n)}&bron=nieuwsbrief`)}" style="color:#1e2a22;text-decoration:none"><b>${esc(o.n)}</b></a>${o.sz ? ` <span style="color:#5d6a61">${esc(o.sz)}</span>` : ''}<br><span style="color:#5d6a61;font-size:13px">${esc(NAMEN[o.s] || o.s)}${o.lbl ? ' · ' + esc(o.lbl) : ''}${o.t ? ' · t/m ' + esc(o.t.slice(8, 10) + '-' + o.t.slice(5, 7)) : ''}</span></td>` +
            `<td align="right" style="padding:9px 0 9px 10px;border-bottom:1px solid #e1e7dc;white-space:nowrap"><b>${eur(o.p)}</b><br><span style="color:#5d6a61;font-size:13px;text-decoration:line-through">${eur(o.was)}</span> <span style="color:#c4381f;font-size:13px;font-weight:bold">-${Math.round((1 - o.p / o.was) * 100)}%</span></td></tr>`).join('') +
          `</table>`,
        knop: 'Alle aanbiedingen vergelijken', knopUrl: `${site}/aanbiedingen/?bron=nieuwsbrief`,
        voet: `Je krijgt dit omdat je je hebt aangemeld voor de nieuwsbrief (${a.nieuws === 'dag' ? 'dagelijks' : 'wekelijks'}). <a href="${esc(uit)}" style="color:#5d6a61">Afmelden</a>. Goedkope Boodschappen is gratis en zonder reclame. De prijs aan de kassa is leidend.`,
      });
      if (!c) c = await verbind({ user, pass });
      try {
        await c.stuur(bericht({ van: process.env.MAIL_FROM || user, vanNaam: 'Boodschappenvergelijk.nl', antwoordAan: 'info@boodschappenvergelijk.nl', aan: a.email, onderwerp: kop, tekst, html, afmelden: uit }));
        a.nieuwsVerstuurd = dag; await store.setJSON(key, a); n++;
      } catch (e) { console.log('nieuwsbrief mislukt', e.message); try { await c.reset(); } catch {} }
    }
  } finally { if (c) await c.sluit(); }
  return new Response(`${n} nieuwsbrieven verstuurd`);
};

// Elke ochtend om 07:40 (Nederlandse wintertijd).
export const config = { schedule: '40 6 * * *' };
