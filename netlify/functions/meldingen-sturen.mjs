// Elke ochtend: per abonnee kijken of er iets van de lijst in de aanbieding is, en daar één melding over sturen.
// Een aanbieding wordt maar één keer gemeld. Verlopen abonnementen (404/410) worden opgeruimd.
import { getStore } from '@netlify/blobs';
import { stuur } from '../webpush.mjs';
import { passend, sleutelVan, alarmTreffers } from '../zoek.mjs';
import { verbind, bericht, opmaak, esc } from '../mail.mjs';

const NAMEN = { ah: 'AH', jumbo: 'Jumbo', lidl: 'Lidl', aldi: 'Aldi', plus: 'PLUS', dirk: 'Dirk', hoogvliet: 'Hoogvliet', dekamarkt: 'DekaMarkt', poiesz: 'Poiesz' };
const eur = v => '€ ' + v.toFixed(2).replace('.', ',');

export default async (req, context) => {
  const site = Netlify.env.get('URL') || context?.site?.url || 'https://boodschappenvergelijk.nl';
  const offers = (await (await fetch(`${site}/data/aanbiedingen.json`)).json()).offers || [];
  try { await pushRonde(site, offers); } catch (e) { console.log('push-ronde fout', e.message); }
  try { await mailRonde(site, offers); } catch (e) { console.log('mail-ronde fout', e.message); }
};

async function pushRonde(site, offers) {
  const pub = Netlify.env.get('VAPID_PUBLIC'), priv = Netlify.env.get('VAPID_PRIVATE');
  if (!pub || !priv) { console.log('VAPID-sleutels ontbreken'); return; }
  const store = getStore('meldingen');
  const { blobs } = await store.list();
  let gestuurd = 0, weg = 0;
  const grens = new Date(Date.now() - 45 * 864e5).toISOString().slice(0, 10);
  await Promise.all(blobs.map(async ({ key }) => {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (!a?.sub || !a.termen?.length) return;
    const nieuw = passend(offers, a.termen, a.winkels).filter(({ o }) => !a.verstuurd[sleutelVan(o)]);
    if (!nieuw.length) return;
    const n = nieuw.length;
    const titel = n === 1 ? `🔥 ${nieuw[0].term} is in de aanbieding` : `🔥 ${n} artikelen van je lijst in de aanbieding`;
    const tekst = nieuw.slice(0, 4).map(({ o }) => `${NAMEN[o.s] || o.s}: ${o.n} ${eur(o.p)}${o.lbl ? ' (' + o.lbl + ')' : ''}`).join('\n') + (n > 4 ? `\n+ ${n - 4} meer` : '');
    try {
      const status = await stuur(a.sub, { titel, tekst, url: '/?bron=melding#lijst' }, pub, priv);
      if (status === 404 || status === 410) { await store.delete(key); weg++; return; }
      if (status >= 400) { console.log('push mislukt', status); return; }
      gestuurd++;
      const d = new Date().toISOString().slice(0, 10);
      for (const { o } of nieuw) a.verstuurd[sleutelVan(o)] = d;
      for (const [k, v] of Object.entries(a.verstuurd)) if (v < grens) delete a.verstuurd[k];
      await store.setJSON(key, a);
    } catch (e) { console.log('push fout', e.message); }
  }));
  console.log(`meldingen: ${gestuurd} verstuurd, ${weg} verlopen abonnementen opgeruimd, ${blobs.length} abonnees`);
}

// E-mail: één mail per bevestigde abonnee met de nieuwe aanbiedingen voor de lijst. Gmail staat 500 mails per dag toe.
async function mailRonde(site, offers) {
  const user = Netlify.env.get('GMAIL_USER'), pass = Netlify.env.get('GMAIL_APP_PASSWORD');
  if (!user || !pass) { console.log('Gmail-instellingen ontbreken, geen e-mail'); return; }
  const store = getStore('email');
  const { blobs } = await store.list({ prefix: 't-' });
  const grens = new Date(Date.now() - 45 * 864e5).toISOString().slice(0, 10), d = new Date().toISOString().slice(0, 10);
  const taken = [];
  let soorten = {};
  try { soorten = (await (await fetch(`${site}/data/termprijzen.json`)).json()).soorten || {}; } catch (e) { console.log('termprijzen niet geladen', e.message); }
  for (const { key } of blobs) {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (!a) continue;
    if (!a.bevestigd) { // onbevestigd na 7 dagen weg
      if (Date.now() - Date.parse(a.sinds) > 7 * 864e5) { await store.delete(key); await store.delete('a-' + (await sha(a.email))); }
      continue;
    }
    const nieuw = passend(offers, a.termen || [], a.winkels).filter(({ o }) => !a.verstuurd?.[sleutelVan(o)]);
    const alarm = alarmTreffers(soorten, a.alarm, a.winkels, a.alarmGemeld || {});
    if (nieuw.length || alarm.length) taken.push({ key, a, nieuw, alarm });
  }
  if (!taken.length) { console.log(`e-mail: niets te sturen, ${blobs.length} adressen`); return; }
  let v = null, gestuurd = 0;
  try {
    v = await verbind({ user, pass });
    for (const { key, a, nieuw, alarm } of taken.slice(0, 450)) {
      const n = nieuw.length, uit = `${site}/api/email?uit=${a.token}`;
      const EH = { kg: 'kilo', l: 'liter', st: 'stuk' };
      const alarmTekst = alarm.map(h => `🔔 ${h.term}: nu ${eur(h.prijs)} per ${EH[h.u] || 'kilo'} bij ${NAMEN[h.w] || h.w}${h.naam ? ' (' + h.naam + ')' : ''}, je grens was ${eur(h.max)}`).join('\n');
      const alarmHtml = alarm.length ? `<p style="margin:0 0 6px;font-weight:bold;font-size:16px">🔔 Prijsalarm</p><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px">` + alarm.map(h => `<tr><td style="padding:8px 0;border-top:1px solid #e1e7dc;font-size:15px"><b>${esc(h.term)}</b> bij ${esc(NAMEN[h.w] || h.w)}${h.naam ? `<br><span style="color:#5d6a61;font-size:13px">${esc(h.naam)}</span>` : ''}<br><span style="color:#5d6a61;font-size:13px">Je grens: ${eur(h.max)} per ${EH[h.u] || 'kilo'}</span></td><td align="right" style="padding:8px 0;border-top:1px solid #e1e7dc;white-space:nowrap"><b style="font-size:18px">${eur(h.prijs)}</b><br><span style="font-size:12px;color:#5d6a61">per ${EH[h.u] || 'kilo'}</span></td></tr>`).join('') + '</table>' : '';
      const onderwerp = !n ? (alarm.length === 1 ? `🔔 ${alarm[0].term} is nu ${eur(alarm[0].prijs)} per ${EH[alarm[0].u] || 'kilo'}` : `🔔 ${alarm.length} prijsalarmen: je prijs is bereikt`) : n === 1 ? `🔥 ${nieuw[0].term} is in de aanbieding` : `🔥 ${n} artikelen van je lijst in de aanbieding`;
      const regels = nieuw.slice(0, 20);
      const tekst = (alarmTekst ? alarmTekst + '\n\n' : '') + regels.map(({ term, o }) => `${term}: ${NAMEN[o.s] || o.s}, ${o.n} ${o.sz || ''} voor ${eur(o.p)}${o.lbl ? ' (' + o.lbl + ')' : ''}${o.t ? ', t/m ' + o.t.slice(8, 10) + '-' + o.t.slice(5, 7) : ''}\n${o.u}`).join('\n\n') +
        `\n\nBekijk je lijst: ${site}/#lijst\n\nAfmelden: ${uit}\nGoedkope Boodschappen is gratis, zonder reclame. Ik verdien er niets aan.`;
      const rijen = regels.map(({ term, o }) => `<tr><td style="padding:10px 0;border-top:1px solid #e1e7dc;font-size:15px;line-height:1.4"><span style="font-size:13px;font-weight:bold;color:#0a6239;background:#e2f2e8;padding:2px 7px;border-radius:5px">${esc(NAMEN[o.s] || o.s)}</span>${o.lbl ? ` <span style="font-size:13px;font-weight:bold;color:#e0472f">${esc(o.lbl)}</span>` : ''}<br><a href="${esc(o.u)}" style="color:#1e2a22;font-weight:bold">${esc(o.n)}</a> <span style="color:#5d6a61">${esc(o.sz || '')}</span><br><span style="font-size:13px;color:#5d6a61">voor “${esc(term)}” op je lijst${o.t ? ` · t/m ${esc(o.t.slice(8, 10) + '-' + o.t.slice(5, 7))}` : ''}</span></td>
<td align="right" style="padding:10px 0 10px 10px;border-top:1px solid #e1e7dc;white-space:nowrap;vertical-align:middle"><span style="display:inline-block;background:#e0472f;color:#ffffff;font-weight:bold;font-size:18px;padding:5px 9px;border-radius:5px">${eur(o.p)}</span>${o.was ? `<br><span style="font-size:13px;color:#5d6a61;text-decoration:line-through">${eur(o.was)}</span>` : ''}</td></tr>`).join('');
      const html = opmaak({
        titel: onderwerp.replace(/^(🔥|🔔) /u, ''),
        inhoud: alarmHtml + (n ? `<table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rijen}</table>` : '') + `${n > 20 ? `<p style="color:#5d6a61">+ ${n - 20} meer op de site.</p>` : ''}`,
        knop: 'Bekijk waar je lijst het goedkoopst is', knopUrl: `${site}/?bron=mail#lijst`,
        voet: `Je krijgt deze mail omdat je je op Goedkope Boodschappen hebt aangemeld voor meldingen bij aanbiedingen. <a href="${esc(uit)}" style="color:#5d6a61">Afmelden</a> kan altijd, met één klik.<br>Gratis en onafhankelijk: geen reclame, geen commissie, ik verdien er geen cent aan.`,
      });
      try {
        await v.stuur(bericht({ van: user, vanNaam: 'Goedkope Boodschappen', antwoordAan: 'goedkopeboodschappen@proton.me', aan: a.email, onderwerp, tekst, html, afmelden: uit }));
        gestuurd++;
        a.verstuurd = a.verstuurd || {};
        for (const { o } of nieuw) a.verstuurd[sleutelVan(o)] = d;
        if (alarm.length) { a.alarmGemeld = a.alarmGemeld || {}; for (const h of alarm) a.alarmGemeld[h.k] = { d, p: h.prijs }; }
        for (const [k, w] of Object.entries(a.verstuurd)) if (w < grens) delete a.verstuurd[k];
        await store.setJSON(key, a);
      } catch (e) {
        console.log('mail mislukt', e.message);
        try { await v.reset(); } catch { try { await v.sluit(); } catch {} v = await verbind({ user, pass }); }
      }
    }
  } finally { if (v) await v.sluit(); }
  console.log(`e-mail: ${gestuurd} verstuurd, ${blobs.length} adressen`);
}
const sha = async s => (await import('node:crypto')).createHash('sha256').update(s).digest('hex').slice(0, 40);

// 06:20 UTC = 08:20 in de zomer, 07:20 in de winter: na het ophalen van de aanbiedingen en het opnieuw bouwen van de site.
export const config = { schedule: '20 6 * * *' };
