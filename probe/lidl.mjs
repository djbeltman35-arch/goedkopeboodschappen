import fs from 'node:fs';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const H={headers:{'User-Agent':UA}};
const out={};
for(const id of ['hah-wk46-2026','hah-wk45-2026']){const j=await (await fetch(`https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=${id}&region_id=0&region_code=0`,H)).json();const f=j.flyer||j;
out[id]={start:f.offerStartDate,end:f.offerEndDate,startDate:f.startDate,endDate:f.endDate,pages:(f.pages||[]).length,prod:Object.values(f.products||{}).map(x=>[x.title,x.price,x.categoryPrimary,x.wonCategoryPrimary].join(' | ')),pageKeys:f.pages?.[0]?Object.keys(f.pages[0]):null,page1:JSON.stringify(f.pages?.[1]||'').slice(0,1500)}}
fs.writeFileSync('probe/lidl-uit.json',JSON.stringify(out,null,1));
