import fs from 'fs';
const uit = {};
const UA = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36', 'Accept-Language': 'nl-NL' };
async function probeer(n, fn) { try { uit[n] = await fn(); } catch (e) { uit[n] = { fout: String(e).slice(0, 300) }; } }
async function tekst(url, o = {}) { const r = await fetch(url, { ...o, headers: { ...UA, ...(o.headers || {}) } }); return { status: r.status, t: await r.text() }; }
function scripts(t) { return [...t.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)].map(m => ({ attr: m[1].slice(0, 120), len: m[2].length, begin: m[2].slice(0, 200) })).filter(x => x.len > 2000).slice(0, 12); }
function rond(t, w, n = 3) { const out = []; let i = 0; while (out.length < n && (i = t.indexOf(w, i + 1)) > 0) out.push(t.slice(Math.max(0, i - 400), i + 600)); return out; }
await probeer('ah_volgende', async () => { const r = await tekst('https://www.ah.nl/bonus/volgende-week'); return { status: r.status, scripts: scripts(r.t), rond: rond(r.t, 'bonusStartDate', 2).concat(rond(r.t, 'promotionStartDate', 1)).concat(rond(r.t, '"title"', 2)) }; });
await probeer('dirk_volgende', async () => { const r = await tekst('https://www.dirk.nl/aanbiedingen'); return { status: r.status, scripts: scripts(r.t), rond: rond(r.t, 'Volgende week', 2).concat(rond(r.t, 'startDate', 2)) }; });
await probeer('vomar', async () => { const r = await tekst('https://www.vomar.nl/aanbiedingen'); return { status: r.status, scripts: scripts(r.t), rond: rond(r.t, 'volgende week', 2).concat(rond(r.t, 'price', 2)) }; });
for (const [n, gw] of [['dirk', 'https://web-gateway.dirk.nl/graphql'], ['deka', 'https://web-deka-gateway.dekamarkt.nl/graphql']]) {
  await probeer(n + '_velden', async () => { const res = {}; for (const f of ['nextOffers', 'upcomingOffers', 'futureOffers', 'comingOffers', 'offers', 'previewOffers', 'nextWeekOffers']) { const q = `{listOffers(department:1,store:66){${f}{offerId headerText startDate endDate}}}`; const r = await tekst(gw, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) }); res[f] = r.t.slice(0, 400); } const q2 = '{listOffers(department:1,store:66){currentOffers{offerId startDate endDate}}}'; res.cur = (await tekst(gw, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q2 }) })).t.slice(0, 600); return res; });
}
await probeer('jumbo_start', async () => {
  const H = { 'content-type': 'application/json', 'apollographql-client-name': 'JUMBO_WEB-search', 'apollographql-client-version': 'master-v29.4.0-web' };
  const nu = new Date().toISOString(); let toekomst = 0, tot = 0; const vb = [];
  for (let off = 0; off < 1600; off += 200) { const Q = 'query($input:ProductSearchInput!){searchProducts(input:$input){count products{title promotions{tags{text} start{iso} end{iso}}}}}'; const j = await (await fetch('https://www.jumbo.com/api/graphql', { method: 'POST', headers: H, body: JSON.stringify({ query: Q, variables: { input: { searchType: 'keyword', searchTerms: '*', offSet: off, limit: 200, filters: [{ key: 'Aanbiedingen', values: ['Alle aanbiedingen'] }] } } }) })).json(); for (const p of j?.data?.searchProducts?.products || []) { tot++; for (const pr of p.promotions || []) if (pr.start?.iso && new Date(pr.start.iso) > new Date()) { toekomst++; if (vb.length < 5) vb.push(p.title + ' ' + pr.start.iso); } } }
  return { tot, toekomst, vb };
});
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
