import fs from 'fs';
const uit = {};
for (const ua of ['GoedkopeBoodschappen/1.0 (https://boodschappenvergelijk.nl; goedkopeboodschappen@proton.me)', 'Mozilla/5.0']) {
  const r = await fetch('https://api.openverse.org/v1/images/?q=pumpkin%20tagine&license=cc0,pdm,by,by-sa&page_size=5&mature=false', { headers: { 'User-Agent': ua } });
  const t = await r.text(); uit[ua] = r.status + ' ' + t.slice(0, 1500);
}
fs.writeFileSync('probe/uit.json', JSON.stringify(uit, null, 1));
