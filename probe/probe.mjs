// Verkenning: waar staan de aanbiedingen van volgende week? Resultaat naar probe/uit.json.
import fs from 'fs';
const uit = {};
const UA = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36', 'Accept-Language': 'nl-NL' };
async function probeer(naam, fn) { try { uit[naam] = await fn(); } catch (e) { uit[naam] = { fout: String(e).slice(0, 300) }; } }
async function tekst(url, o = {}) { const r = await fetch(url, { ...o, headers: { ...UA, ...(o.headers || {}) } }); const t = await r.text(); return { status: r.status, t }; }
function nextMon() { const d = new Date(); d.setDate(d.getDate() + ((8 - d.getDay()) % 7 || 7)); return d.toISOString().slice(0, 10); }
// Dirk / DekaMarkt: schema van listOffers
for (const [n, gw] of [['dirk', 'https://web-gateway.dirk.nl/graphql'], ['deka', 'https://web-deka-gateway.dekamarkt.nl/graphql']]) {
  await probeer(n + '_schema', async () => {
    const q = '{__type(name:"Query"){fields{name args{name type{name kind ofType{name}}} type{name kind ofType{name}}}}}';
    const r = await tekst(gw, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) });
    let j; try { j = JSON.parse(r.t); } catch { return { status: r.status, t: r.t.slice(0, 500) }; }
    const f = (j?.data?.__type?.fields || []).filter(x => /offer|folder|promo|week/i.test(x.name));
    const out = { status: r.status, velden: f };
    for (const x of f) { const tn = x.type?.name || x.type?.ofType?.name; if (tn) { const r2 = await tekst(gw, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: `{__type(name:"${tn}"){fields{name type{name kind ofType{name}}}}}` }) }); try { out[tn] = JSON.parse(r2.t)?.data?.__type?.fields?.map(z => z.name + ':' + (z.type?.name || z.type?.ofType?.name)); } catch { } } }
    if (j?.errors) out.errors = j.errors.slice(0, 2);
    return out;
  });
}
// AH bonus metadata
await probeer('ah', async () => {
  const H = { 'User-Agent': 'Appie/8.22.3', 'x-application': 'AHWEBSHOP', 'Content-Type': 'application/json' };
  const tok = await (await fetch('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: H, body: JSON.stringify({ clientId: 'appie' }) })).json();
  const A = { ...H, Authorization: 'Bearer ' + tok.access_token };
  const res = {};
  for (const u of ['https://api.ah.nl/mobile-services/bonuspage/v1/metadata', 'https://api.ah.nl/mobile-services/bonuspage/v2/metadata', `https://api.ah.nl/mobile-services/bonuspage/v1/section?date=${nextMon()}`, `https://api.ah.nl/mobile-services/bonuspage/v2/section/spotlight?date=${nextMon()}`]) {
    try { const r = await fetch(u, { headers: A }); const t = await r.text(); res[u] = { status: r.status, t: t.slice(0, 1500) }; } catch (e) { res[u] = String(e); }
  }
  return res;
});
// Jumbo: filterwaarden voor aanbiedingen
await probeer('jumbo', async () => {
  const H = { 'content-type': 'application/json', 'apollographql-client-name': 'JUMBO_WEB-search', 'apollographql-client-version': 'master-v29.4.0-web' };
  const res = {};
  for (const v of ['Alle aanbiedingen', 'Volgende week', 'Aanbiedingen volgende week', 'Komende week']) {
    const Q = 'query($input:ProductSearchInput!){searchProducts(input:$input){count products{title promotions{tags{text} start{iso} end{iso}}}}}';
    const r = await tekst('https://www.jumbo.com/api/graphql', { method: 'POST', headers: H, body: JSON.stringify({ query: Q, variables: { input: { searchType: 'keyword', searchTerms: '*', offSet: 0, limit: 3, filters: [{ key: 'Aanbiedingen', values: [v] }] } } }) });
    res[v] = r.t.slice(0, 800);
  }
  const p = await tekst('https://www.jumbo.com/aanbiedingen/volgende-week');
  res.pagina = { status: p.status, len: p.t.length, volgende: (p.t.match(/volgende week/gi) || []).length, stukje: p.t.slice(0, 300) };
  return res;
});
for (const [n, u] of [['hoogvliet', 'https://www.hoogvliet.com/aanbiedingen'], ['aldi', 'https://www.aldi.nl/aanbiedingen.html'], ['vomar', 'https://www.vomar.nl/aanbiedingen'], ['spar', 'https://www.spar.nl/aanbiedingen/'], ['plus', 'https://www.plus.nl/aanbiedingen'], ['dirkweb', 'https://www.dirk.nl/aanbiedingen'], ['ahweb', 'https://www.ah.nl/bonus/volgende-week']]) {
  await probeer(n + '_pagina', async () => { const r = await tekst(u); const links = [...new Set((r.t.match(/href="[^"]*(volgende|komende|vanaf|week)[^"]*"/gi) || []))].slice(0, 15); return { status: r.status, len: r.t.length, volgende: (r.t.match(/volgende week|vanaf (maandag|woensdag|zondag|donderdag)/gi) || []).slice(0, 10), links }; });
}
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
