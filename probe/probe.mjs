import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const out={};const log=(k,v)=>{out[k]=v;console.log(k,JSON.stringify(v).slice(0,200));};
async function f(url){try{const r=await fetch(url,{redirect:'manual',headers:{'User-Agent':UA,'Accept-Language':'nl-NL'},signal:AbortSignal.timeout(30000)});const t=await r.text();return {st:r.status,t,loc:r.headers.get('location')};}catch(e){return {st:0,t:String(e)}}}
const links=t=>[...new Set((t.match(/href="(\/producten\/[^"#?]+)"/g)||[]).map(x=>x.slice(6,-1)))];
{const r=await f('https://www.vomar.nl/producten/bier-wijn-sterke-drank/bier');const L=links(r.t);log('vomar1',{st:r.st,n:L.length,L:L.slice(0,40),prijzen:(r.t.match(/class="price"/g)||[]).length});
 const sub=L.find(x=>x.split('/').length>=5&&!/\d+$/.test(x));if(sub){const r2=await f('https://www.vomar.nl'+sub);const L2=links(r2.t);log('vomar2',{u:sub,st:r2.st,n:L2.length,L:L2.slice(0,40),prijzen:(r2.t.match(/class="price"/g)||[]).length});}}
for(const u of ['https://www.nettorama.nl/robots.txt','https://www.nettorama.nl/sitemap.xml','https://www.nettorama.nl/','https://www.nettorama.nl/aanbiedingen']){const r=await f(u);log('netto '+u,{st:r.st,loc:r.loc,len:r.t.length,b:r.t.slice(0,700)});}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
