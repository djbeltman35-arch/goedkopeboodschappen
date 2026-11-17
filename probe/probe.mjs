import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const out={};const f=async u=>{try{const r=await fetch(u,{headers:{'User-Agent':UA,'Accept-Language':'nl-NL'}});return {st:r.status,t:await r.text()}}catch(e){return{st:0,t:String(e)}}};
const sl=ms=>new Promise(r=>setTimeout(r,ms));
const rb=await f('https://www.lidl.nl/robots.txt');out.robots=rb.t.slice(0,3000);
const maps=[...rb.t.matchAll(/Sitemap:\s*(\S+)/gi)].map(m=>m[1]);out.maps=maps;
const alle=[];
for(const m of maps){const r=await f(m);const locs=[...r.t.matchAll(/<loc>([^<]+)<\/loc>/g)].map(x=>x[1]);out['map '+m]={st:r.st,n:locs.length,eerste:locs.slice(0,15)};
  for(const s of locs.filter(l=>/xml/.test(l)).slice(0,40)){const q=await f(s);const l2=[...q.t.matchAll(/<loc>([^<]+)<\/loc>/g)].map(x=>x[1]);out['sub '+s]={st:q.st,n:l2.length,vb:l2.slice(0,5)};alle.push(...l2);await sl(300);}
  alle.push(...locs.filter(l=>!/xml/.test(l)));}
const prod=alle.filter(u=>/\/p\//.test(u));out.nProd=prod.length;out.pad=Object.entries(prod.reduce((a,u)=>{const k=u.split('/').slice(3,5).join('/');a[k]=(a[k]||0)+1;return a},{})).sort((a,b)=>b[1]-a[1]).slice(0,40);
const kies=prod.filter(u=>/melk|kaas|brood|koffie|ei|yoghurt|pasta|boter/i.test(u)).slice(0,6).concat(prod.slice(0,3));out.kies=kies;
for(const u of kies){const r=await f(u);const t=r.t;out['p '+u]={st:r.st,len:t.length,price:(t.match(/"price"\s*:\s*"?[\d.,]+/g)||[]).slice(0,5),ld:(t.match(/<script type="application\/ld\+json">[\s\S]{0,1200}/)||[''])[0],titel:(t.match(/<title>[^<]*/)||[''])[0]};await sl(800);}
for(const q of ['melk','kaas','koffie']){const r=await f('https://www.lidl.nl/q/api/search?q='+q+'&fetchsize=48&offset=0&locale=nl_NL&assortment=NL&version=2.1.0');out['zoek '+q]={st:r.st,b:r.t.slice(0,2500)};await sl(800);}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
