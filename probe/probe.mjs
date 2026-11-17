import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const out={};const log=(k,v)=>{out[k]=v;console.log(k,JSON.stringify(v).slice(0,200));};
async function f(url){try{const r=await fetch(url,{headers:{'User-Agent':UA,'Accept-Language':'nl-NL'},signal:AbortSignal.timeout(30000)});return {st:r.status,t:await r.text()};}catch(e){return {st:0,t:String(e)}}}
// Vomar: categorieboom en prijzen op productpagina
const links=(t,re)=>[...new Set((t.match(/href="(\/producten\/[^"#?]+)"/g)||[]).map(x=>x.slice(6,-1)))];
{const top=links((await f('https://www.vomar.nl/producten')).t).filter(x=>x.split('/').length===3);
 let subs=[];for(const t of top){const L=links((await f('https://www.vomar.nl'+t)).t);subs.push(...L.filter(x=>x.startsWith(t+'/')&&x.split('/').length===4));}
 subs=[...new Set(subs)];let prods=new Set();const per={};
 for(const s of subs){const L=links((await f('https://www.vomar.nl'+s)).t).filter(x=>/\/\d+$/.test(x));L.forEach(x=>prods.add(x));per[s]=L.length;await new Promise(r=>setTimeout(r,300));}
 log('vomar_boom',{top:top.length,subs:subs.length,producten:prods.size,per});
 const p=(await f('https://www.vomar.nl'+[...prods][0])).t;const m=p.match(/<p class="price"[^>]*>[\s\S]{0,300}?<\/p>/);
 const nd=p.match(/window\.__NUXT__=([\s\S]{0,50})/);log('vomar_prod',{u:[...prods][0],price:m&&m[0],h1:(p.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)||[])[1],nuxt:!!nd,ld:(p.match(/application\/ld\+json[^>]*>([\s\S]*?)<\/script>/)||[])[1]?.slice(0,600)});}
// Nettorama: wat staat er op de site
{const t=(await f('https://www.nettorama.nl/')).t;log('netto_links',[...new Set((t.match(/href="([^"#]+)"/g)||[]).map(x=>x.slice(6,-1)))].filter(x=>!/\.(css|png|jpg|svg|ico|js)/.test(x)).slice(0,80));}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
