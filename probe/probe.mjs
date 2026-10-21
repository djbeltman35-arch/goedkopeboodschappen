import fs from 'fs';
const H = { 'User-Agent': 'Appie/8.22.3', 'x-application': 'AHWEBSHOP', 'Content-Type': 'application/json' };
const tok = await (await fetch('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: H, body: JSON.stringify({ clientId: 'appie' }) })).json();
const A = { ...H, Authorization: 'Bearer ' + tok.access_token };
const uit = {};
for (const seg of [815112, 815124]) { const j = await (await fetch(`https://api.ah.nl/mobile-services/bonuspage/v1/segment?segmentId=${seg}&date=2026-10-19`, { headers: A })).json(); const p = (j.products || [])[0] || {}; delete p.images; uit[seg] = { groep: Object.fromEntries(Object.entries(j).filter(([k]) => k !== 'products' && k !== 'images')), product: p, n: (j.products || []).length }; }
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
