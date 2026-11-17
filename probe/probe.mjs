import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const out={};const f=async u=>{try{const r=await fetch(u,{headers:{'User-Agent':UA}});return {st:r.status,t:await r.text()}}catch(e){return{st:0,t:String(e)}}};
const V='https://view.publitas.com/bv-nettorama-verbruikersmarkten/nettorama-folder-47-2026/';
const h=(await f(V)).t;out.viewer={len:h.length,urls:[...new Set(h.match(/https?:\/\/[^"' )]+\.json[^"' )]*/g)||[])].slice(0,20),data:(h.match(/[a-zA-Z_]*(?:data|spreads|hotspot|products)[a-zA-Z_]*\.json/gi)||[]).slice(0,20),sn:h.slice(0,1500)};
for(const u of [V+'data.json',V+'spreads.json',V+'hotspots_data.json','https://view.publitas.com/bv-nettorama-verbruikersmarkten/nettorama-folder-47-2026/hotspots_data.json']){const r=await f(u);out[u]={st:r.st,b:r.t.slice(0,1500)};}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
