import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const H={headers:{'User-Agent':UA,'Accept-Language':'nl-NL'}};
const out={};
const t=await (await fetch('https://www.lidl.nl/c/service-contact-folders/s10008124',H)).text();
out.leaflets=[...new Set([...t.matchAll(/https?:\/\/[^"'\s]*leaflet[^"'\s]*/gi)].map(m=>m[0]))].slice(0,40);
out.flyerIds=[...new Set([...t.matchAll(/flyer[_-]?identifier["=:]+([\w-]+)/gi)].map(m=>m[1]))];
out.snip=[...t.matchAll(/(folder|Folder)[^<]{0,80}/g)].map(m=>m[0]).slice(0,30);
const res=[];
for(const u of out.leaflets.slice(0,6)){try{const r=await fetch(u,H);const x=await r.text();res.push({u,status:r.status,len:x.length,title:(x.match(/<title>([^<]*)/)||[])[1],flyer:[...new Set([...x.matchAll(/flyer_identifier=([\w-]+)|"flyer_identifier":"([^"]+)"/g)].map(m=>m[1]||m[2]))].slice(0,5),api:[...new Set([...x.matchAll(/https?:\/\/endpoints[^"'\s]+/g)].map(m=>m[0]))].slice(0,5)})}catch(e){res.push({u,err:String(e)})}}
out.res=res;
// bekende openbare flyer-api proberen voor de eerste flyer-id
const ids=[...new Set(res.flatMap(r=>r.flyer||[]).concat(out.flyerIds))];
out.api=[];
for(const id of ids.slice(0,4)){for(const u of [`https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=${id}&region_id=0&region_code=0`,`https://endpoints.leaflets.schwarz/v3/flyer?flyer_identifier=${id}&region_id=0&region_code=0`]){try{const r=await fetch(u,H);const j=await r.json();const f=j.flyer||j;out.api.push({u,status:r.status,keys:Object.keys(f).slice(0,40),name:f.name||f.title,van:f.offerStartDate||f.startDate,tot:f.offerEndDate||f.endDate,products:(f.products?Object.keys(f.products).length:null),voorbeeld:f.products?Object.values(f.products).slice(0,3):null});break}catch(e){out.api.push({u,err:String(e)})}}}
fs.writeFileSync('probe/lidl-uit.json',JSON.stringify(out,null,1));
