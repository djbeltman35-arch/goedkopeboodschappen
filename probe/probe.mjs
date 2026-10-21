import fs from 'fs';
const H = { 'User-Agent': 'Appie/8.22.3', 'x-application': 'AHWEBSHOP', 'Content-Type': 'application/json' };
const tok = await (await fetch('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: H, body: JSON.stringify({ clientId: 'appie' }) })).json();
const A = { ...H, Authorization: 'Bearer ' + tok.access_token };
const uit = {};
const ds = new Date().toISOString().slice(0, 10);
uit.spotlight = await (await fetch(`https://api.ah.nl/mobile-services/bonuspage/v2/section/spotlight?date=${ds}`, { headers: A })).json().catch(e => String(e));
for (const sec of ['spotlight', 'SP', 'OTHER', 'BG', 'bonus', 'categories', 'group', 'segments']) { const r = await fetch(`https://api.ah.nl/mobile-services/bonuspage/v2/section/${sec}?date=${ds}`, { headers: A }); uit['sec_' + sec] = r.status; }
for (const u of ['https://api.ah.nl/mobile-services/bonuspage/v2/metadata', 'https://api.ah.nl/mobile-services/bonuspage/v3/metadata', 'https://api.ah.nl/mobile-services/bonuspage/v1/periods', 'https://api.ah.nl/mobile-services/bonuspage/v2/periods', `https://api.ah.nl/mobile-services/bonuspage/v2/sections?date=${ds}`, `https://api.ah.nl/mobile-services/bonuspage/v2/section?date=${ds}`]) { const r = await fetch(u, { headers: A }); uit[u] = r.status + ' ' + (await r.text()).slice(0, 600); }
// productzoeker met bonusfilter: welke filters bestaan er?
const r = await fetch('https://api.ah.nl/mobile-services/product/search/v2?sortOn=RELEVANCE&size=1&page=0&query=melk', { headers: A }); const j = await r.json(); uit.filters = (j.filters || []).map(f => f.id + ':' + (f.options || []).slice(0, 8).map(o => o.id + '=' + o.label).join('|'));
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
