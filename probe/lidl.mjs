import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const H={headers:{'User-Agent':UA,'Accept-Language':'nl-NL'}};
const out={api:[]};
for(const id of ['hah-wk46-2026','hah-wk46-weekenddeals-2026','hah-wk45-2026']){
 for(const v of ['v4','v3']){const u=`https://endpoints.leaflets.schwarz/${v}/flyer?flyer_identifier=${id}&region_id=0&region_code=0`;
  try{const r=await fetch(u,H);const txt=await r.text();let j;try{j=JSON.parse(txt)}catch{out.api.push({u,status:r.status,txt:txt.slice(0,300)});continue}
   const f=j.flyer||j;const prods=f.products?Object.values(f.products):[];
   out.api.push({u,status:r.status,keys:Object.keys(f),name:f.name||f.title,meta:Object.fromEntries(Object.entries(f).filter(([k,v])=>typeof v!=='object').slice(0,30)),nProd:prods.length,prodKeys:prods[0]?Object.keys(prods[0]):null,voorbeeld:prods.slice(0,4)});
   if(r.ok)break}catch(e){out.api.push({u,err:String(e)})}}}
fs.writeFileSync('probe/lidl-uit.json',JSON.stringify(out,null,1));
