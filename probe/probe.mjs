import fs from 'fs';
const uit = {};
const UA = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36', 'Accept-Language': 'nl-NL' };
async function probeer(n, fn) { try { uit[n] = await fn(); } catch (e) { uit[n] = { fout: String(e).slice(0, 300) }; } }
async function tekst(url, o = {}) { const r = await fetch(url, { ...o, headers: { ...UA, ...(o.headers || {}) } }); return { status: r.status, t: await r.text() }; }
await probeer('ah_chunks', async () => {
  const p = await tekst('https://www.ah.nl/bonus/volgende-week');
  const chunks = [...new Set(p.t.match(/https:\/\/static\.ah\.nl\/ah-bonus\/_next\/static\/chunks\/[^"\\]+\.js/g) || [])];
  const vond = [];
  for (const c of chunks.slice(0, 60)) { const j = (await tekst(c)).t; for (const m of j.matchAll(/(query|mutation)\s+([A-Za-z0-9_]*[Bb]onus[A-Za-z0-9_]*)[^`"]{0,600}/g)) vond.push(m[0].slice(0, 700)); const g = j.match(/["'](\/gql[^"']*|https:\/\/[a-z.]*ah\.nl\/[a-z\/]*gql[^"']*)["']/); if (g) vond.push('ENDPOINT ' + g[1]); }
  return { chunks: chunks.length, vond: [...new Set(vond)].slice(0, 25) };
});
await probeer('ah_spotlight_nu', async () => { const H = { 'User-Agent': 'Appie/8.22.3', 'x-application': 'AHWEBSHOP', 'Content-Type': 'application/json' }; const tok = await (await fetch('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: H, body: JSON.stringify({ clientId: 'appie' }) })).json(); const A = { ...H, Authorization: 'Bearer ' + tok.access_token }; const res = {}; const d = new Date(); for (const off of [0, 5, 7, 12]) { const x = new Date(d); x.setDate(d.getDate() + off); const ds = x.toISOString().slice(0, 10); for (const sec of ['spotlight', 'other', 'all']) { const r = await fetch(`https://api.ah.nl/mobile-services/bonuspage/v2/section/${sec}?date=${ds}`, { headers: A }); const t = await r.text(); res[ds + '_' + sec] = r.status + ' ' + t.length + ' ' + t.slice(0, 300); } } return res; });
await probeer('vomar', async () => { const p = await tekst('https://www.vomar.nl/aanbiedingen'); const api = [...new Set(p.t.match(/https?:\/\/[a-z0-9.-]*vomar[a-z0-9.-]*\/[a-zA-Z0-9\/_.-]*/g) || [])].slice(0, 30); const keys = [...new Set(p.t.match(/(offer|Offer|aanbieding|discount|promotion)[A-Za-z]*:/g) || [])].slice(0, 30); const i = p.t.indexOf('price'); return { api, keys, stuk: p.t.slice(Math.max(0, i - 1500), i + 1500) }; });
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
