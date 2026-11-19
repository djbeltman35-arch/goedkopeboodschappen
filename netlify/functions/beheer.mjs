// Afgeschermde beheerpagina voor Erik: alle e-mailaanmeldingen (nieuwsbrief en lijstmeldingen) in één overzicht.
// Toegang met een geheime code; hier staat alleen de SHA-256 ervan, de code zelf staat nergens in de repo.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const HASH = 'fdd2bdb34df698ad6356f74a5cb08d7573ee285356ee6a9a7104802be62d12c3';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const datum = d => d ? new Intl.DateTimeFormat('nl-NL', { timeZone: 'Europe/Amsterdam', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(d)) : '';
const pagina = inhoud => new Response('<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Beheer · Goedkope Boodschappen</title>'
  + '<style>body{font:16px/1.4 system-ui,sans-serif;margin:0;padding:16px;background:#f4f7f1;color:#1e2a22}h1{font-size:22px;margin:0 0 12px}.tel{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}.tel div{background:#fff;border:1px solid #e1e7dc;border-radius:12px;padding:10px 14px}.tel b{display:block;font-size:24px;color:#0e7c4a}'
  + 'ul{list-style:none;margin:0;padding:0}li{background:#fff;border:1px solid #e1e7dc;border-radius:12px;padding:10px 14px;margin:0 0 8px}li .m{font-weight:700;word-break:break-all}li small{color:#5d6a61;display:block}.ok{color:#0e7c4a}.wacht{color:#b26b00}'
  + 'form{display:flex;gap:8px;max-width:420px}details{margin-top:8px}summary{cursor:pointer;color:#0e7c4a;font-weight:600}form.wijzig{flex-direction:column;align-items:flex-start;gap:8px;margin:8px 0}form.wijzig label{display:flex;gap:6px;align-items:center}select{padding:8px;border:1px solid #e1e7dc;border-radius:10px;font:inherit}.weg{background:#c0392b;margin-top:4px}.grijs{background:#5d6a61;margin-top:12px}.melding{background:#e6f4ec;border:1px solid #0e7c4a;border-radius:12px;padding:10px 14px}input{flex:1;padding:12px;border:1px solid #e1e7dc;border-radius:12px;font:inherit}button{padding:12px 16px;border:0;border-radius:12px;background:#0e7c4a;color:#fff;font:700 16px system-ui}.fout{color:#c0392b}</style></head><body>' + inhoud + '</body></html>',
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

async function overzicht(melding) {
  const store = getStore('email'), rijen = [];
  for (const { key } of (await store.list({ prefix: 't-' })).blobs) {
    const a = await store.get(key, { type: 'json' }).catch(() => null);
    if (a?.email) rijen.push(a);
  }
  rijen.sort((x, y) => String(y.sinds || '').localeCompare(String(x.sinds || '')));
  const bev = rijen.filter(a => a.bevestigd), nb = bev.filter(a => a.nieuws), dag = Date.now() - 864e5;
  const tel = [['Bevestigd', bev.length], ['Nieuwsbrief', nb.length], ['Lijstmeldingen', bev.filter(a => a.termen?.length).length], ['Wacht op bevestiging', rijen.length - bev.length], ['Nieuw (24 uur)', rijen.filter(a => Date.parse(a.sinds) > dag).length]];
  const wat = a => [a.nieuws === 'dag' ? 'Nieuwsbrief dagelijks' : a.nieuws === 'week' ? 'Nieuwsbrief wekelijks' : '', a.termen?.length ? 'Lijstmeldingen (' + a.termen.length + ' artikelen)' : '', a.week ? 'Weekoverzicht' : '', a.alarm?.length ? a.alarm.length + ' prijsalarm(en)' : ''].filter(Boolean).join(' · ') || 'Niets gekozen';
  const sel = (v, w) => v === w ? ' selected' : '';
  const bewerk = a => '<details><summary>Aanpassen</summary><form method="post" class="wijzig">'
    + '<input type="hidden" name="token" value="' + esc(a.token) + '"><input type="hidden" name="actie" value="wijzig">'
    + '<label>Nieuwsbrief <select name="nieuws"><option value=""' + sel(a.nieuws || '', '') + '>Uit</option><option value="dag"' + sel(a.nieuws, 'dag') + '>Dagelijks</option><option value="week"' + sel(a.nieuws, 'week') + '>Wekelijks</option></select></label>'
    + '<label><input type="checkbox" name="week"' + (a.week ? ' checked' : '') + '> Weekoverzicht</label>'
    + (a.termen?.length || a.alarm?.length ? '<label><input type="checkbox" name="lijst" checked> Lijstmeldingen en prijsalarmen houden</label>' : '<input type="hidden" name="lijst" value="on">')
    + (a.bevestigd ? '' : '<label><input type="checkbox" name="bevestigd"> Handmatig bevestigen</label>')
    + '<button>Opslaan</button></form>'
    + '<form method="post" onsubmit="return confirm(\'' + esc(a.email).replace(/'/g, '') + ' afmelden en verwijderen?\')">'
    + '<input type="hidden" name="token" value="' + esc(a.token) + '"><input type="hidden" name="actie" value="afmelden"><button class="weg">Afmelden en verwijderen</button></form></details>';
  return '<h1>Aanmeldingen</h1>' + (melding ? '<p class="melding">' + esc(melding) + '</p>' : '') + '<div class="tel">' + tel.map(([n, v]) => '<div><b>' + v + '</b>' + n + '</div>').join('') + '</div><ul>'
    + rijen.map(a => '<li><span class="m">' + esc(a.email) + '</span><small>' + esc(wat(a)) + '</small><small>Aangemeld ' + esc(datum(a.sinds)) + ' · '
      + (a.bevestigd ? '<span class="ok">bevestigd</span>' : '<span class="wacht">wacht op bevestiging</span>') + '</small>' + bewerk(a) + '</li>').join('')
    + '</ul>' + (rijen.length ? '' : '<p>Nog geen aanmeldingen.</p>')
    + '<form method="post"><input type="hidden" name="actie" value="uitloggen"><button class="grijs">Uitloggen</button></form>';
}

export default async req => {
  const ingelogd = await geldigeSessie(req);
  if (req.method !== 'POST') return ingelogd ? pagina(await overzicht('')) : inlog(false);
  const f = await req.formData().catch(() => null);
  if (!f) return inlog(false);
  if (ingelogd && f.get('actie') === 'uitloggen') {
    await getStore('beheer').delete('s-' + sha(cookieVan(req))).catch(() => {});
    const r = inlog(false); r.headers.set('Set-Cookie', 'gb_beheer=; Path=/beheer; Max-Age=0; HttpOnly; Secure; SameSite=Strict'); return r;
  }
  if (ingelogd && f.get('actie')) return pagina(await overzicht(await verwerk(f)));
  const code = String(f.get('code') || '').trim();
  const h = crypto.createHash('sha256').update(code).digest();
  if (!crypto.timingSafeEqual(h, Buffer.from(HASH, 'hex'))) { await new Promise(r => setTimeout(r, 1500)); return inlog(true); }
  const r = pagina(await overzicht(''));
  r.headers.set('Set-Cookie', await nieuweSessie());
  return r;
};

export const config = { path: '/beheer', method: ['GET', 'POST'] };
