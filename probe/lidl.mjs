import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const H={headers:{'User-Agent':UA,'Accept-Language':'nl-NL'}};
const ams=v=>{if(v==null||v==='')return null;const d=typeof v==='number'?new Date(v<1e12?v*1000:v):new Date(v);return isNaN(d)?String(v):new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam'}).format(d)};
const out={};
const hoofd=await (await fetch('https://www.lidl.nl/c/aanbiedingen/a10008785',H)).text();
out.hrefs=[...new Set([...hoofd.matchAll(/href="([^"]*\/(?:c|h)\/[^"]+)"/g)].map(m=>m[1]))].slice(0,150);
out.catIds=[...new Set([...hoofd.matchAll(/category\.id=(\d+)/g)].map(m=>m[1]))];
out.textVanaf=[...new Set([...hoofd.matchAll(/(vanaf|Vanaf|geldig|Geldig)[^<"]{0,60}/g)].map(m=>m[0]))].slice(0,40);
const alle=[];let facets=null;
for(let off=0;off<1200;off+=60){const d=await (await fetch(`https://www.lidl.nl/q/api/search?offset=${off}&fetchsize=60&locale=nl_NL&assortment=NL&version=2.1.0&category.id=10068374&q=`,H)).json();
 if(!facets)facets=(d.facets||[]).map(f=>({n:f.name||f.key||f.label,v:(f.values||f.items||[]).slice(0,40).map(v=>[v.label||v.name||v.value,v.count,v.id||v.key||v.value])}));
 for(const it of d.items||[]){const x=it.gridbox?.data||{};alle.push({n:x.fullTitle,p:x.price?.price,was:x.price?.oldPrice,lp:(x.lidlPlus||[]).length,van:ams(x.storeStartDate),tot:ams(x.storeEndDate),cat:x.category,ribbons:(x.ribbons||[]).map(b=>b.text).join('/'),badge:JSON.stringify(x.stockAvailability||x.badges||'').slice(0,80)})}
 if((d.items||[]).length<60)break;await new Promise(r=>setTimeout(r,500));}
out.facets=facets;out.n=alle.length;
const per={};for(const i of alle){const k=(i.van||'-')+'..'+(i.tot||'-')+(i.was>i.p?' korting':' vast');per[k]=(per[k]||0)+1}
out.per=per;out.alle=alle;
fs.writeFileSync('probe/lidl-uit.json',JSON.stringify(out,null,1));
