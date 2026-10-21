import fs from 'fs';
const H = { 'User-Agent': 'Appie/8.22.3', 'x-application': 'AHWEBSHOP', 'Content-Type': 'application/json' };
const tok = await (await fetch('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: H, body: JSON.stringify({ clientId: 'appie' }) })).json();
const A = { ...H, Authorization: 'Bearer ' + tok.access_token };
const uit = {};
const seg = 815112;
for (const u of [`https://api.ah.nl/mobile-services/product/search/v2?bonusSegmentId=${seg}&size=5&page=0`, `https://api.ah.nl/mobile-services/product/search/v2?filters=${encodeURIComponent('bonusSegmentId=' + seg)}&size=5`, `https://api.ah.nl/mobile-services/bonuspage/v1/segment?segmentId=${seg}&date=2026-10-19`, `https://api.ah.nl/mobile-services/bonuspage/v2/segment/${seg}?date=2026-10-19`, `https://api.ah.nl/mobile-services/product/search/v2?sortOn=RELEVANCE&size=3&page=0&filters=${encodeURIComponent('bonus=Bonus')}`]) {
  const r = await fetch(u, { headers: A }); const t = await r.text(); uit[u] = r.status + ' ' + t.slice(0, 1800);
}
const r2 = await fetch('https://api.ah.nl/mobile-services/product/search/v2?sortOn=RELEVANCE&size=1&page=0&query=bonus', { headers: A }); const j = await r2.json(); uit.bonusfilter = (j.filters || []).filter(f => /bonus/i.test(f.id)).map(f => ({ id: f.id, opties: f.options?.map(o => o.id + '=' + o.label + ':' + o.count) }));
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
