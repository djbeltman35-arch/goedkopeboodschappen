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

export async function stuurBevestiging(site, a) {
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  const link = `${site}/api/email?bevestig=${a.token}`, uit = `${site}/api/email?uit=${a.token}`;
  const v = await verbind({ user, pass });
  try {
    await v.stuur(bericht({
      van: user, vanNaam: 'Goedkope Boodschappen', antwoordAan: 'goedkopeboodschappen@proton.me', aan: a.email,
      onderwerp: 'Bevestig je e-mailmeldingen', afmelden: uit,
      tekst: `Hallo!\n\nBevestig dat je een mail wilt als iets van je boodschappenlijst in de aanbieding is:\n${link}\n\nHeb je dit niet aangevraagd? Dan kun je deze mail negeren. Zonder bevestiging sturen we niets en wissen we je adres na 7 dagen.\n\nGoedkope Boodschappen is gratis, zonder reclame. Ik verdien er niets aan.\nhttps://boodschappenvergelijk.nl`,
      html: opmaak({
        titel: 'Bevestig je e-mailmeldingen',
        inhoud: `<p style="margin:0 0 10px;font-size:16px;line-height:1.5">Tik op de knop, dan krijg je voortaan een mail als iets van je boodschappenlijst in de aanbieding is (${a.termen.length} ${a.termen.length === 1 ? 'artikel' : 'artikelen'}).</p><p style="margin:0;font-size:15px;line-height:1.5;color:#5d6a61">Heb je dit niet aangevraagd? Negeer deze mail dan. Zonder bevestiging sturen we niets en wissen we je adres na 7 dagen.</p>`,
        knop: 'Ja, stuur mij meldingen', knopUrl: link,
        voet: 'Goedkope Boodschappen is gratis en onafhankelijk: geen reclame, geen commissie, ik verdien er geen cent aan.',
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
    if (!t) return json({ aan });
    const a = geldigToken(t) ? await store.get('t-' + t, { type: 'json' }).catch(() => null) : null;
    return json({ aan, status: a ? (a.bevestigd ? 'bevestigd' : 'wacht') : 'onbekend', adres: a ? a.email.replace(/^(.).*(@.*)$/, '$1…$2') : null, week: !!a?.week });
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
    if (Array.isArray(body.termen)) { a.termen = termen; a.winkels = winkels; }
    // Prijsalarmen: hoogstens 25, per soort een maximale prijs per kilo, liter of stuk.
    if (Array.isArray(body.alarm)) a.alarm = body.alarm.slice(0, 25).map(x => ({ t: String(x?.t || '').slice(0, 60).trim(), max: Math.round(+x?.max * 100) / 100, u: ['kg', 'l', 'st'].includes(x?.u) ? x.u : 'kg' })).filter(x => x.t && x.max > 0 && x.max < 1000);
    a.bijgewerkt = new Date().toISOString();
    await store.setJSON('t-' + body.token, a);
    return json({ status: a.bevestigd ? 'bevestigd' : 'wacht', week: !!a.week, alarm: a.alarm || [] });
  }

  // Nieuwe aanmelding
  if (!aan) return json({ fout: 'E-mailmeldingen zijn nog niet beschikbaar.' }, 503);
  const email = String(body.email || '').trim().toLowerCase();
  if (!GELDIG.test(email)) return json({ fout: 'Dat e-mailadres klopt niet.' }, 400);
  if (!termen.length) return json({ fout: 'Zet eerst iets op je lijst.' }, 400);
  const ak = adresSleutel(email);
  const bestaand = await store.get(ak, { type: 'json' }).catch(() => null);
  if (bestaand?.token) {
    const a = await store.get('t-' + bestaand.token, { type: 'json' }).catch(() => null);
    if (a?.bevestigd) return json({ status: 'al', fout: 'Dit adres is al aangemeld. Je krijgt al meldingen; afmelden kan onderaan elke mail.' });
    // Nog niet bevestigd: hoogstens één bevestigingsmail per 10 minuten.
    if (a && Date.now() - Date.parse(a.mailVerstuurd || 0) < 10 * 60e3) return json({ status: 'wacht', token: a.token });
    if (a) await store.delete('t-' + a.token);
  }
  const token = crypto.randomBytes(24).toString('hex');
  const a = { email, token, termen, winkels, bevestigd: null, sinds: new Date().toISOString(), verstuurd: {}, mailVerstuurd: new Date().toISOString() };
  try { await stuurBevestiging(site, a); }
  catch (e) { console.log('bevestigingsmail mislukt', e.message); return json({ fout: 'De bevestigingsmail kon niet worden verstuurd. Probeer het later nog eens.' }, 502); }
  await store.setJSON('t-' + token, a);
  await store.setJSON(ak, { token });
  return json({ status: 'wacht', token });
};

export const config = { path: '/api/email', method: ['GET', 'POST'] };
