// E-mailmeldingen bij aanbiedingen: aanmelden (met bevestigingsmail), lijst bijwerken, status opvragen en afmelden.
// Bewaard in Netlify Blobs: het e-mailadres, de woorden op de lijst, de gekozen supermarkten, of je het weekoverzicht wilt en je prijsalarmen. Niets anders.
// Onbevestigde aanmeldingen ruimt meldingen-sturen na 7 dagen op.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const naar = url => new Response(null, { status: 302, headers: { Location: url, 'Cache-Control': 'no-store' } });
const adresSleutel = e => 'a-' + crypto.createHash('sha256').update(e).digest('hex').slice(0, 40);
const geldigToken = t => typeof t === 'string' && /^[a-f0-9]{48}$/.test(t);
const GELDIG = /^[^\s@<>()",;:]{1,64}@[a-z0-9.-]{1,200}\.[a-z]{2,24}$/;

function lijst(body) {
  const termen = [...new Set((Array.isArray(body.termen) ? body.termen : []).map(t => String(t).slice(0, 60).trim()).filter(Boolean))].slice(0, 80);
  const winkels = (Array.isArray(body.winkels) ? body.winkels : []).map(String).filter(w => /^[a-z]{2,12}$/.test(w)).slice(0, 15);
  return { termen, winkels };
}

export async function stuurBevestiging(site, a, herinnering = false) {
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  const link = `${site}/api/email?bevestig=${a.token}`, uit = `${site}/api/email?uit=${a.token}`;
  const lijstdeel = a.termen.length ? `een mail als iets van je boodschappenlijst in de aanbieding is (${a.termen.length} ${a.termen.length === 1 ? 'artikel' : 'artikelen'})` : '';
  const nieuwsdeel = a.nieuws === 'dag' ? 'elke ochtend de beste aanbiedingen van de dag' : a.nieuws === 'week' ? 'elke maandag de beste aanbiedingen van de week' : '';
  const wat = [lijstdeel, nieuwsdeel].filter(Boolean).join(' en ');
  const v = await verbind({ user, pass });
  try {
    await v.stuur(bericht({
      van: process.env.MAIL_FROM || user, vanNaam: 'Boodschappenvergelijk.nl', antwoordAan: 'info@boodschappenvergelijk.nl', aan: a.email,
      onderwerp: (herinnering ? 'Herinnering: ' : '') + (a.nieuws && !a.termen.length ? 'Bevestig je aanmelding voor de nieuwsbrief' : 'Bevestig je e-mailmeldingen'), afmelden: uit,
      tekst: `Hallo!\n\n${herinnering ? 'Je hebt je gisteren aangemeld, maar nog niet bevestigd. ' : ''}Bevestig dat je ${wat} wilt ontvangen:\n${link}\n\nHeb je dit niet aangevraagd? Dan kun je deze mail negeren. Zonder bevestiging sturen we niets en wissen we je adres na 7 dagen.\n\nGoedkope Boodschappen is gratis, zonder reclame.\nhttps://boodschappenvergelijk.nl`,
      html: opmaak({
        titel: 'Bevestig je e-mailmeldingen',
        inhoud: `${herinnering ? '<p style="margin:0 0 10px;font-size:16px;line-height:1.5">Je hebt je gisteren aangemeld, maar nog niet bevestigd. Dit is de enige herinnering die je krijgt.</p>' : ''}<p style="margin:0 0 10px;font-size:16px;line-height:1.5">Tik op de knop, dan krijg je voortaan ${esc(wat)}.</p><p style="margin:0;font-size:15px;line-height:1.5;color:#5d6a61">Heb je dit niet aangevraagd? Negeer deze mail dan. Zonder bevestiging sturen we niets en wissen we je adres na 7 dagen.</p><p style="margin:10px 0 0;font-size:15px;line-height:1.5;color:#5d6a61"><b>Tip:</b> zet de afzender in je contacten. Dan komt de nieuwsbrief niet in je spam.</p>`,
        knop: 'Ja, aanmelden', knopUrl: link,
        voet: 'Goedkope Boodschappen is gratis en onafhankelijk: geen reclame en geen commissie.',
      }),
    }));
  } finally { await v.sluit(); }
}

export default async (req, context) => {
  const url = new URL(req.url), site = Netlify.env.get('URL') || url.origin;
  const aan = !!(Netlify.env.get('GMAIL_USER') && Netlify.env.get('GMAIL_APP_PASSWORD'));
  const store = getStore('email');

  // Bevestigen en afmelden gaan via een link in de mail (GET), afmelden ook via de afmeldknop van Gmail (POST).
  const bevestig = url.searchParams.get('bevestig'), uit = url.searchParams.get('uit');
  if (bevestig) {
    if (!geldigToken(bevestig)) return naar('/?email=onbekend#lijst');
    const a = await store.get('t-' + bevestig, { type: 'json' }).catch(() => null);
    if (!a) return naar('/?email=onbekend#lijst');
    if (!a.bevestigd) { a.bevestigd = new Date().toISOString(); await store.setJSON('t-' + bevestig, a); }
    return naar(`/?email=bevestigd&t=${bevestig}#lijst`);
  }
  if (uit) {
    if (geldigToken(uit)) {
      const a = await store.get('t-' + uit, { type: 'json' }).catch(() => null);
      if (a) { await store.delete('t-' + uit); await store.delete(adresSleutel(a.email)); }
    }
    return req.method === 'POST' ? json({ ok: true }) : naar('/?email=uit#lijst');
  }

  if (req.method === 'GET') {
    const t = url.searchParams.get('token');
    // Zonder token is het antwoord voor iedereen gelijk: laat het CDN het bewaren, zodat drukte de functie niet raakt.
    if (!t) return Response.json({ aan }, { headers: { 'Cache-Control': 'public, max-age=300', 'Netlify-CDN-Cache-Control': 'public, durable, s-maxage=900', 'Netlify-Vary': 'query' } });
    const a = geldigToken(t) ? await store.get('t-' + t, { type: 'json' }).catch(() => null) : null;
    return json({ aan, status: a ? (a.bevestigd ? 'bevestigd' : 'wacht') : 'onbekend', adres: a ? a.email.replace(/^(.).*(@.*)$/, '$1…$2') : null, week: !!a?.week, nieuws: a?.nieuws || null });
  }
  if (req.method !== 'POST') return json({ fout: 'niet toegestaan' }, 405);
  let body; try { body = await req.json(); } catch { return json({ fout: 'ongeldig verzoek' }, 400); }
  const { termen, winkels } = lijst(body);

  // Bestaande aanmelding: lijst bijwerken of afmelden met het token dat de browser bewaart.
  if (body.token) {
    if (!geldigToken(body.token)) return json({ status: 'onbekend' });
    const a = await store.get('t-' + body.token, { type: 'json' }).catch(() => null);
    if (!a) return json({ status: 'onbekend' });
    if (body.afmelden) { await store.delete('t-' + body.token); await store.delete(adresSleutel(a.email)); return json({ status: 'uit' }); }
    // Alleen het weekoverzicht aan- of uitzetten, of de lijst bijwerken (of allebei).
    if ('week' in body) a.week = !!body.week;
    if ('nieuws' in body) a.nieuws = ['dag', 'week'].includes(body.nieuws) ? body.nieuws : null;
    if (Array.isArray(body.termen)) { a.termen = termen; a.winkels = winkels; }
    // Prijsalarmen: hoogstens 25, per soort een maximale prijs per kilo, liter of stuk.
    if (Array.isArray(body.alarm)) a.alarm = body.alarm.slice(0, 25).map(x => ({ t: String(x?.t || '').slice(0, 60).trim(), max: Math.round(+x?.max * 100) / 100, u: ['kg', 'l', 'st'].includes(x?.u) ? x.u : 'kg' })).filter(x => x.t && x.max > 0 && x.max < 1000);
    a.bijgewerkt = new Date().toISOString();
    await store.setJSON('t-' + body.token, a);
    return json({ status: a.bevestigd ? 'bevestigd' : 'wacht', week: !!a.week, nieuws: a.nieuws || null, alarm: a.alarm || [] });
  }

  // Nieuwe aanmelding
  if (!aan) return json({ fout: 'E-mailmeldingen zijn nog niet beschikbaar.' }, 503);
  const email = String(body.email || '').trim().toLowerCase();
  if (!GELDIG.test(email)) return json({ fout: 'Dat e-mailadres klopt niet.' }, 400);
  const nieuws = ['dag', 'week'].includes(body.nieuws) ? body.nieuws : null;
  if (!termen.length && !nieuws) return json({ fout: 'Zet eerst iets op je lijst.' }, 400);
  const ak = adresSleutel(email);
  const bestaand = await store.get(ak, { type: 'json' }).catch(() => null);
  if (bestaand?.token) {
    const a = await store.get('t-' + bestaand.token, { type: 'json' }).catch(() => null);
    if (a?.bevestigd) {
      // Al aangemeld en nu (ook) de nieuwsbrief gekozen: die gewoon aanzetten.
      if (nieuws && a.nieuws !== nieuws) { a.nieuws = nieuws; await store.setJSON('t-' + a.token, a); return json({ status: 'bevestigd', nieuws, token: a.token }); }
      return json({ status: 'al', fout: 'Dit adres is al aangemeld. Afmelden kan onderaan elke mail.' });
    }
    // Nog niet bevestigd: hoogstens één bevestigingsmail per 10 minuten.
    if (a && Date.now() - Date.parse(a.mailVerstuurd || 0) < 10 * 60e3) return json({ status: 'wacht', token: a.token });
    if (a) await store.delete('t-' + a.token);
  }
  // Tegen misbruik (iemand die de site laat mailen naar vreemde adressen): hoogstens 5 bevestigingsmails per dag per bezoeker.
  const ip = context?.ip || req.headers.get('x-nf-client-connection-ip') || 'onbekend';
  const tk = new Date().toISOString().slice(0, 10) + '-' + crypto.createHash('sha256').update(ip + 'gb-email').digest('hex').slice(0, 24);
  const teller = getStore('email-teller'), nIp = +(await teller.get(tk).catch(() => 0) || 0);
  if (nIp >= 5) return json({ fout: 'Je hebt vandaag al een paar keer een aanmelding gestuurd. Kijk in je mail (ook bij spam) of probeer het morgen weer.' }, 429);
  await teller.set(tk, String(nIp + 1));
  const token = crypto.randomBytes(24).toString('hex');
  const a = { email, token, termen, winkels, nieuws, bevestigd: null, sinds: new Date().toISOString(), verstuurd: {}, mailVerstuurd: new Date().toISOString() };
  try { await stuurBevestiging(site, a); }
  catch (e) { console.log('bevestigingsmail mislukt', e.message); return json({ fout: 'De bevestigingsmail kon niet worden verstuurd. Probeer het later nog eens.' }, 502); }
  await store.setJSON('t-' + token, a);
  await store.setJSON(ak, { token });
  return json({ status: 'wacht', token });
};

export const config = { path: '/api/email', method: ['GET', 'POST'] };
