import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const out={};const f=async u=>{const r=await fetch(u,{headers:{'User-Agent':UA}});return r.text()};
{const t=await f('https://www.vomar.nl/producten/bier-wijn-sterke-drank/bier/amstel-pils-6x330ml-blik/149794');
 const i=t.indexOf('window.__NUXT__');const nx=t.slice(i,i+200000);
 out.vomar_keys=[...new Set(nx.match(/[A-Za-z]{3,30}(?=:)/g)||[])].slice(0,200);
 out.vomar_unit=(nx.match(/.{0,120}(?:ml|gram|stuks|[Uu]nit|[Cc]ontent|[Ww]eight|[Ss]ize).{0,120}/g)||[]).slice(0,15);}
{const t=await f('https://www.nettorama.nl/actiefolder');out.netto_folder={len:t.length,ifr:(t.match(/<iframe[^>]*src="[^"]+"/g)||[]),links:[...new Set((t.match(/(?:href|src)="([^"]+)"/g)||[]))].filter(x=>/folder|publitas|issuu|pdf|flipp/i.test(x)).slice(0,20),tekst:t.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').slice(0,1500)};}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
