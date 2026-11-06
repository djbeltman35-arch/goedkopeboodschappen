// Tijdelijk: verkennen welke aanbiedingspagina's Lidl online heeft (deze week, volgende week, weekend).
import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const haal=async u=>{const r=await fetch(u,{headers:{'User-Agent':UA,'Accept-Language':'nl-NL'}});return {status:r.status,text:await r.text()}};
const ont=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const dag=v=>{if(v==null||v==='')return null;const d=typeof v==='number'?new Date(v<1e12?v*1000:v):new Date(v);return isNaN(d)?String(v):d.toISOString().slice(0,10)};
const out={pages:[]};
const base='https://www.lidl.nl/c/aanbiedingen/a10008785';
const hoofd=await haal(base);
const links=[...new Set([...hoofd.text.matchAll(/href="(\/c\/[^"#?]+\/a\d+)[^"]*"[^>]*>([\s\S]{0,200}?)<\/a>/g)].map(m=>m[1]+' | '+ont(m[2].replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim()).slice(0,80)))];
out.links=links;
const urls=[base,...new Set(links.map(l=>'https://www.lidl.nl'+l.split(' | ')[0]))].slice(0,40);
for(const u of urls){
  const r=u===base?hoofd:await haal(u); await new Promise(r=>setTimeout(r,700));
  const items=[];for(const m of r.text.matchAll(/data-grid-data="([^"]*)"/g)){try{const x=JSON.parse(ont(m[1]));items.push({n:x.fullTitle,p:x.price?.price,was:x.price?.oldPrice,lp:!!(x.lidlPlus||[]).length,van:dag(x.storeStartDate),tot:dag(x.storeEndDate),cat:x.category,ribbons:(x.ribbons||[]).map(b=>b.text).join('/'),keys:Object.keys(x).slice(0,60).join(',')})}catch{}}
  const ranges={};for(const i of items){const k=(i.van||'-')+'..'+(i.tot||'-');ranges[k]=(ranges[k]||0)+1}
  const title=(r.text.match(/<title>([^<]*)<\/title>/)||[])[1];
  out.pages.push({u,status:r.status,title,n:items.length,ranges,voorbeeld:items.slice(0,4)});
}
// zoekdienst: welke datums geeft die
const z=await (await fetch('https://www.lidl.nl/q/api/search?offset=0&fetchsize=60&locale=nl_NL&assortment=NL&version=2.1.0&category.id=10068374&q=',{headers:{'User-Agent':UA}})).json().catch(e=>({err:String(e)}));
out.zoek={total:z.numFound??z.total??null,keys:Object.keys(z),n:(z.items||[]).length,ranges:(z.items||[]).reduce((a,it)=>{const x=it.gridbox?.data||{};const k=dag(x.storeStartDate)+'..'+dag(x.storeEndDate);a[k]=(a[k]||0)+1;return a},{})};
fs.writeFileSync('probe/lidl-uit.json',JSON.stringify(out,null,1));
console.log(JSON.stringify(out.pages.map(p=>[p.u,p.status,p.n,p.ranges]),null,0));
