// Afgeschermde beheerpagina voor Erik: alle e-mailaanmeldingen (nieuwsbrief en lijstmeldingen) in één overzicht.
// Toegang met een geheime code; hier staat alleen de SHA-256 ervan, de code zelf staat nergens in de repo.
// Alle tegels zijn klikbaar: ze filteren de lijst eronder (?f=dag, ?f=week, ?f=lijst, ...).
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const HASH = 'fdd2bdb34df698ad6356f74a5cb08d7573ee285356ee6a9a7104802be62d12c3';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const datum = d => d ? new Intl.DateTimeFormat('nl-NL', { timeZone: 'Europe/Amsterdam', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(d)) : '';
const CSS = 'body{font:16px/1.4 system-ui,sans-serif;margin:0;padding:16px;background:#f4f7f1;color:#1e2a22}h1{font-size:22px;margin:0 0 12px}h2{font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:#5d6a61;margin:18px 0 8px}'
  + '.tegels{display:grid;gap:8px}.t3{grid-template-columns:repeat(3,1fr)}.t2{grid-template-columns:repeat(2,1fr)}'
  + 'a.tegel{display:block;background:#fff;border:2px solid #e1e7dc;border-radius:14px;padding:12px;color:#1e2a22;text-decoration:none;position:relative}a.tegel:active{transform:scale(.98)}a.tegel.aan{border-color:#0e7c4a;background:#e6f4ec}'
  + 'a.tegel b{display:block;font-size:28px;line-height:1.1;color:#0e7c4a}a.tegel span{display:block;font-weight:600}a.tegel small{display:block;color:#5d6a61;font-size:13px;margin-top:2px}a.tegel:after{content:"›";position:absolute;right:10px;top:8px;color:#9aa89f;font-size:20px}'
  + 'a.t-dag b{color:#0e7c4a}a.t-week b{color:#1f5fa8}a.t-lijst b{color:#b26b00}a.tegel.wachtt b{color:#b26b00}'
  + '.kop{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:20px 0 8px}.kop h2{margin:0}.kop a{color:#0e7c4a;font-weight:600;text-decoration:none;white-space:nowrap}'
  + 'ul{list-style:none;margin:0;padding:0}li{background:#fff;border:1px solid #e1e7dc;border-radius:12px;padding:10px 14px;margin:0 0 8px}li .m{font-weight:700;word-break:break-all}li small{color:#5d6a61;display:block}.ok{color:#0e7c4a}.wacht{color:#b26b00}'
  + '.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 4px}.chip{font-size:13px;font-weight:600;border-radius:999px;padding:2px 10px;text-decoration:none}.c-dag{background:#e6f4ec;color:#0e7c4a}.c-week{background:#e3edf9;color:#1f5fa8}.c-lijst{background:#fdf0dc;color:#8a5300}.c-grijs{background:#eef1ec;color:#5d6a61}'
  + 'form{display:flex;gap:8px;max-width:420px}details{margin-top:6px}summary{cursor:pointer;color:#0e7c4a;font-weight:600}form.wijzig{flex-direction:column;align-items:flex-start;gap:8px;margin:8px 0}form.wijzig label{display:flex;gap:6px;align-items:center}select{padding:8px;border:1px solid #e1e7dc;border-radius:10px;font:inherit}.weg{background:#c0392b;margin-top:4px}.grijs{background:#5d6a61;margin-top:12px}.melding{background:#e6f4ec;border:1px solid #0e7c4a;border-radius:12px;padding:10px 14px}input{flex:1;padding:12px;border:1px solid #e1e7dc;border-radius:12px;font:inherit}button{padding:12px 16px;border:0;border-radius:12px;background:#0e7c4a;color:#fff;font:700 16px system-ui}.fout{color:#c0392b}.leeg{color:#5d6a61}';
export const pagina = inhoud => new Response('<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Beheer · Boodschappenvergelijk</title>'
  + '<style>' + CSS + '</style></head><body>' + inhoud + '</body></html>',
  { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow', 'Referrer-Policy': 'no-referrer' } });
const inlog = fout => pagina('<h1>Beheer</h1>' + (fout ? '<p class="fout">Onjuiste code.</p>' : '') + '<form method="post"><input type="password" name="code" placeholder="Code" autocomplete="current-password" required autofocus><button>Inloggen</button></form>');

// Na inloggen een sessie van 12 uur: willekeurige sleutel in een cookie, alleen de hash ervan in Blobs.
const SESSIE_UUR = 12;
const sha = t => crypto.createHash('sha256').update(t).digest('hex');
const cookieVan = req => (req.headers.get('cookie') || '').split(/;\s*/).map(c => c.split('=')).find(([k]) => k === 'gb_beheer')?.[1] || '';
async function geldigeSessie(req) {
  const t = cookieVan(req);
  if (!/^[a-f0-9]{64}$/.test(t)) return false;
  const s = await getStore('beheer').get('s-' + sha(t), { type: 'json' }).catch(() => null);
  return !!s && Date.parse(s.tot) > Date.now();
}
async function nieuweSessie() {
  const t = crypto.randomBytes(32).toString('hex');
  await getStore('beheer').setJSON('s-' + sha(t), { tot: new Date(Date.now() + SESSIE_UUR * 36e5).toISOString() });
  return `gb_beheer=${t}; Path=/beheer; Max-Age=${SESSIE_UUR * 3600}; HttpOnly; Secure; SameSite=Strict`;
}
const adresSleutel = e => 'a-' + crypto.createHash('sha256').update(e).digest('hex').slice(0, 40);
const geldigToken = t => typeof t === 'string' && /^[a-f0-9]{48}$/.test(t);

// Wijzigingen door Erik zelf: afmelden, nieuwsbrief en weekoverzicht aanpassen, handmatig bevestigen.
async function verwerk(f) {
  const token = String(f.get('token') || ''), actie = String(f.get('actie') || '');
  if (!geldigToken(token)) return 'Onbekende aanmelding.';
  const store = getStore('email'), a = await store.get('t-' + token, { type: 'json' }).catch(() => null);
  if (!a) return 'Deze aanmelding bestaat niet meer.';
  if (actie === 'afmelden') {
    await store.delete('t-' + token); await store.delete(adresSleutel(a.email));
    return a.email + ' is afgemeld en verwijderd.';
  }
  if (actie === 'wijzig') {
    const nieuws = String(f.get('nieuws') || '');
    a.nieuws = ['dag', 'week'].includes(nieuws) ? nieuws : null;
    a.week = f.get('week') === 'on';
    if (f.get('lijst') !== 'on') { a.termen = []; a.alarm = []; }
    if (f.get('bevestigd') === 'on' && !a.bevestigd) a.bevestigd = new Date().toISOString();
    a.bijgewerkt = new Date().toISOString();
    await store.setJSON('t-' + token, a);
    return 'Aanmelding van ' + a.email + ' is aangepast.';
  }
  return 'Onbekende actie.';
}

// Filters achter de tegels.
const DAG = 864e5;
const FILTERS = {
  alle: { naam: 'Alle aanmeldingen', test: () => true },
  dag: { naam: 'Dagelijkse aanbiedingen', test: a => a.nieuws === 'dag' },
  week: { naam: 'Wekelijkse aanbiedingen', test: a => a.nieuws === 'week' },
  lijst: { naam: 'Eigen lijst', test: a => a.termen?.length > 0 },
  bevestigd: { naam: 'Bevestigd', test: a => !!a.bevestigd },
  wacht: { naam: 'Wacht op bevestiging', test: a => !a.bevestigd },
  nieuw: { naam: 'Nieuw (24 uur)', test: a => Date.parse(a.sinds) > Date.now() - DAG },
};
const filterVan = v => FILTERS[v] ? v : 'alle';

export function overzichtHtml(rijen, melding, filter) {
  filter = filterVan(filter);
  rijen = [...rijen].sort((x, y) => String(y.sinds || '').localeCompare(String(x.sinds || '')));
  const tel = k => rijen.filter(FILTERS[k].test);
  const tegel = (k, label, sub, extra = '') => {
    const alle = tel(k), bev = alle.filter(a => a.bevestigd).length, wacht = alle.length - bev;
    const groot = ['dag', 'week', 'lijst'].includes(k) ? bev : alle.length;
    const onder = ['dag', 'week', 'lijst'].includes(k) ? (sub + (wacht ? ' · +' + wacht + ' wacht' : '')) : sub;
    return '<a class="tegel t-' + k + (k === 'wacht' ? ' wachtt' : '') + (filter === k ? ' aan' : '') + '" href="?f=' + k + '#lijst"><b>' + groot + '</b><span>' + label + '</span>' + (onder ? '<small>' + esc(onder) + '</small>' : '') + extra + '</a>';
  };
  const weekov = rijen.filter(a => a.bevestigd && a.termen?.length && a.week).length;
  const chips = a => [
    a.nieuws === 'dag' ? '<a class="chip c-dag" href="?f=dag#lijst">Dagelijks</a>' : '',
    a.nieuws === 'week' ? '<a class="chip c-week" href="?f=week#lijst">Wekelijks</a>' : '',
    a.termen?.length ? '<a class="chip c-lijst" href="?f=lijst#lijst">Eigen lijst · ' + a.termen.length + '</a>' : '',
    a.week ? '<span class="chip c-grijs">Weekoverzicht</span>' : '',
    a.alarm?.length ? '<span class="chip c-grijs">' + a.alarm.length + ' prijsalarm' + (a.alarm.length > 1 ? 'en' : '') + '</span>' : '',
  ].filter(Boolean).join('') || '<span class="chip c-grijs">Niets gekozen</span>';
  const sel = (v, w) => v === w ? ' selected' : '';
  const verborgen = a => '<input type="hidden" name="token" value="' + esc(a.token) + '"><input type="hidden" name="f" value="' + filter + '">';
  const bewerk = a => '<details><summary>Aanpassen</summary><form method="post" class="wijzig">'
    + verborgen(a) + '<input type="hidden" name="actie" value="wijzig">'
    + '<label>Nieuwsbrief <select name="nieuws"><option value=""' + sel(a.nieuws || '', '') + '>Uit</option><option value="dag"' + sel(a.nieuws, 'dag') + '>Dagelijks</option><option value="week"' + sel(a.nieuws, 'week') + '>Wekelijks</option></select></label>'
    + '<label><input type="checkbox" name="week"' + (a.week ? ' checked' : '') + '> Weekoverzicht</label>'
    + (a.termen?.length || a.alarm?.length ? '<label><input type="checkbox" name="lijst" checked> Lijstmeldingen en prijsalarmen houden</label>' : '<input type="hidden" name="lijst" value="on">')
    + (a.bevestigd ? '' : '<label><input type="checkbox" name="bevestigd"> Handmatig bevestigen</label>')
    + '<button>Opslaan</button></form>'
    + '<form method="post" onsubmit="return confirm(\'' + esc(a.email).replace(/'/g, '') + ' afmelden en verwijderen?\')">'
    + verborgen(a) + '<input type="hidden" name="actie" value="afmelden"><button class="weg">Afmelden en verwijderen</button></form></details>';
  const lijst = tel(filter);
  return '<h1>Aanmeldingen</h1>' + (melding ? '<p class="melding">' + esc(melding) + '</p>' : '')
    + '<h2>Wat ontvangen ze?</h2><div class="tegels t3">'
    + tegel('dag', 'Dagelijks', 'aanbiedingen')
    + tegel('week', 'Wekelijks', 'aanbiedingen')
    + tegel('lijst', 'Eigen lijst', weekov ? weekov + ' met weekoverzicht' : 'meldingen')
    + '</div><h2>Totaalbeeld</h2><div class="tegels t2">'
    + tegel('alle', 'Totaal', 'alle adressen')
    + tegel('bevestigd', 'Bevestigd', '')
    + tegel('wacht', 'Wacht op bevestiging', '')
    + tegel('nieuw', 'Nieuw (24 uur)', '')
    + '</div><div class="kop" id="lijst"><h2>' + esc(FILTERS[filter].naam) + ' · ' + lijst.length + '</h2>' + (filter !== 'alle' ? '<a href="?f=alle#lijst">× Toon alles</a>' : '') + '</div><ul>'
    + lijst.map(a => '<li><span class="m">' + esc(a.email) + '</span><div class="chips">' + chips(a) + '</div><small>Aangemeld ' + esc(datum(a.sinds)) + ' · '
      + (a.bevestigd ? '<span class="ok">bevestigd</span>' : '<span class="wacht">wacht op bevestiging</span>') + '</small>' + bewerk(a) + '</li>').join('')
    + '</ul>' + (lijst.length ? '' : '<p class="leeg">Geen aanmeldingen in deze groep.</p>')
    + '<form method="post"><input type="hidden" name="actie" value="uitloggen"><button class="grijs">Uitloggen</button></form>';
}

async function overzicht(melding, filter) {
  const store = getStore('email'), rijen = [];
  for (const { key } of (await store.list({ prefix: 't-' })).blobs) {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (a?.email) rijen.push(a);
  }
  return overzichtHtml(rijen, melding, filter);
}

export default async req => {
  const ingelogd = await geldigeSessie(req);
  const filter = filterVan(new URL(req.url).searchParams.get('f'));
  if (req.method !== 'POST') return ingelogd ? pagina(await overzicht('', filter)) : inlog(false);
  const f = await req.formData().catch(() => null);
  if (!f) return inlog(false);
  if (ingelogd && f.get('actie') === 'uitloggen') {
    await getStore('beheer').delete('s-' + sha(cookieVan(req))).catch(() => {});
    const r = inlog(false); r.headers.set('Set-Cookie', 'gb_beheer=; Path=/beheer; Max-Age=0; HttpOnly; Secure; SameSite=Strict'); return r;
  }
  if (ingelogd && f.get('actie')) return pagina(await overzicht(await verwerk(f), filterVan(String(f.get('f') || ''))));
  const code = String(f.get('code') || '').trim();
  const h = crypto.createHash('sha256').update(code).digest();
  if (!crypto.timingSafeEqual(h, Buffer.from(HASH, 'hex'))) { await new Promise(r => setTimeout(r, 1500)); return inlog(true); }
  const r = pagina(await overzicht('', filter));
  r.headers.set('Set-Cookie', await nieuweSessie());
  return r;
};

export const config = { path: '/beheer', method: ['GET', 'POST'] };
