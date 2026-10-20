// Elke zaterdagochtend: wie het weekoverzicht aan heeft gezet (bij de e-mailmeldingen), krijgt een mail met
// waar zijn boodschappenlijst die week het goedkoopst is: de 3 goedkoopste supermarkten en per artikel de goedkoopste winkel.
// Prijzen uit data/termprijzen.json (gemaakt bij het bouwen van de site): per soort het voordeligste product per winkel.
import { getStore } from '@netlify/blobs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const NAMEN = { ah: 'Albert Heijn', jumbo: 'Jumbo', lidl: 'Lidl', aldi: 'Aldi', plus: 'PLUS', dirk: 'Dirk', hoogvliet: 'Hoogvliet', dekamarkt: 'DekaMarkt', poiesz: 'Poiesz', spar: 'SPAR', vomar: 'Vomar' };
const eur = v => '€ ' + v.toFixed(2).replace('.', ',');

export function overzicht(prijzen, termen, winkels) {
  const soorten = [...new Set(termen.map(t => String(t).toLowerCase().trim()))].map(t => prijzen[t]).filter(Boolean);
  if (!soorten.length) return null;
  const mag = w => !winkels?.length || winkels.includes(w);
  const alle = [...new Set(soorten.flatMap(s => Object.keys(s.w)))].filter(mag);
  const rijen = alle.map(w => {
    const bij = soorten.filter(s => s.w[w] != null);
    return { w, som: bij.reduce((a, s) => a + s.w[w], 0), n: bij.length };
  }).filter(r => r.n).sort((a, b) => b.n - a.n || a.som - b.som);
  const per = soorten.map(s => {
    // Eerlijk vergelijken: op prijs per kilo, liter of stuk als die bekend is (een kleine pot is niet "goedkoper").
    const vgl = w => s.u?.[w] ?? s.w[w] * 1000;
    const [w] = Object.keys(s.w).filter(mag).sort((a, b) => vgl(a) - vgl(b));
    const p = w ? s.w[w] : null;
    return w ? { t: s.t, w, p } : null;
  }).filter(Boolean);
  return { rijen: rijen.slice(0, 3), per, totaal: soorten.length, onbekend: termen.length - soorten.length };
}

export default async (req, context) => {
  const site = Netlify.env.get('URL') || context?.site?.url || 'https://boodschappenvergelijk.nl';
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  if (!user || !pass) return new Response('mail niet ingesteld');
  const prijzen = (await (await fetch(`${site}/data/termprijzen.json`)).json()).soorten || {};
  const store = getStore('email'), { blobs } = await store.list();
  const week = new Date().toISOString().slice(0, 10);
  let c = null, n = 0;
  try {
    for (const { key } of blobs) {
      if (!key.startsWith('t-')) continue;
      const a = await store.get(key, { type: 'json' }).catch(() => null);
      if (!a?.bevestigd || !a.week || !a.termen?.length || a.weekVerstuurd === week) continue;
      const o = overzicht(prijzen, a.termen, a.winkels); if (!o || !o.rijen.length) continue;
      const best = o.rijen[0], uit = `${site}/api/email?uit=${a.token}`;
      const kop = `Deze week ben je het goedkoopst uit bij ${NAMEN[best.w] || best.w}`;
      const tekst = `${kop}.\n\n` + o.rijen.map((r, i) => `${i + 1}. ${NAMEN[r.w] || r.w}: ${eur(r.som)} (${r.n} van ${o.totaal} artikelen)`).join('\n') +
        `\n\nPer artikel het goedkoopst:\n` + o.per.map(x => `- ${x.t}: ${NAMEN[x.w] || x.w} ${eur(x.p)}`).join('\n') +
        `\n\nPer artikel het voordeligste product bij elke winkel, één van elk. Bekijk je lijst: ${site}/#lijst\n\nGeen weekoverzicht meer? Zet het uit in de app, of meld je helemaal af: ${uit}`;
      const html = opmaak({
        titel: kop,
        inhoud: `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:16px;margin:0 0 14px">` +
          o.rijen.map((r, i) => `<tr><td style="padding:8px 0;border-bottom:1px solid #e1e7dc">${i === 0 ? '🏆 ' : ''}<b>${esc(NAMEN[r.w] || r.w)}</b><br><span style="color:#5d6a61;font-size:13px">${r.n} van ${o.totaal} artikelen</span></td><td align="right" style="padding:8px 0;border-bottom:1px solid #e1e7dc;font-size:20px;font-weight:bold">${eur(r.som)}</td></tr>`).join('') + '</table>' +
          `<p style="margin:0 0 6px;font-weight:bold">Per artikel het goedkoopst</p><ul style="margin:0;padding-left:18px;font-size:14px;line-height:1.6">` +
          o.per.map(x => `<li>${esc(x.t)}: <b>${esc(NAMEN[x.w] || x.w)}</b> ${eur(x.p)}</li>`).join('') + '</ul>' +
          `<p style="margin:12px 0 0;font-size:13px;color:#5d6a61">Per artikel het voordeligste product bij elke winkel, één van elk. In de app zie je de precieze producten en aanbiedingen.</p>`,
        knop: 'Bekijk mijn lijst', knopUrl: `${site}/?bron=weekoverzicht#lijst`,
        voet: `Je krijgt dit omdat je het weekoverzicht aan hebt gezet. Uitzetten kan in de app; <a href="${esc(uit)}" style="color:#5d6a61">helemaal afmelden</a>. Goedkope Boodschappen is gratis en zonder reclame.`,
      });
      if (!c) c = await verbind({ user, pass });
      try {
        await c.stuur(bericht({ van: user, vanNaam: 'Goedkope Boodschappen', antwoordAan: 'goedkopeboodschappen@proton.me', aan: a.email, onderwerp: kop, tekst, html, afmelden: uit }));
        a.weekVerstuurd = week; await store.setJSON(key, a); n++;
      } catch (e) { console.log('weekoverzicht mislukt', e.message); }
    }
  } finally { if (c) await c.sluit(); }
  return new Response(`${n} weekoverzichten verstuurd`);
};

export const config = { schedule: '30 6 * * 6' };
