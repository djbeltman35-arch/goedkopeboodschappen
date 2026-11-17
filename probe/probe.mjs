import fs from 'node:fs'; import zlib from 'node:zlib';
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const sl=ms=>new Promise(r=>setTimeout(r,ms));
async function f(u,taal){try{const r=await fetch(u,{headers:{'User-Agent':UA,'Accept-Language':taal||'nl-NL','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},signal:AbortSignal.timeout(30000)});let b=Buffer.from(await r.arrayBuffer());if(b[0]===0x1f&&b[1]===0x8b){try{b=zlib.gunzipSync(b)}catch{}}return{st:r.status,t:b.toString('utf8')}}catch(e){return{st:0,t:String(e).slice(0,200)}}}
const locs=t=>[...t.matchAll(/<loc>\s*(?:<!\[CDATA\[)?([^<\]]+)/g)].map(x=>x[1].trim());
const PROD=/\/(p|product|producten|products|produkt|produkte|artikel|pd|groceries\/en-GB\/products|shop\/[^/]+\/[^/]+)\/|\/p\d|-p-|\/\d{5,}/i;
async function site(naam,basis,taal,extraMaps=[]){
  const o={};const rb=await f(basis+'/robots.txt',taal);o.robots_st=rb.st;
  o.disallow=(rb.t.match(/^Disallow:.*$/gmi)||[]).slice(0,25);
  let maps=[...rb.t.matchAll(/^Sitemap:\s*(\S+)/gmi)].map(m=>m[1]).concat(extraMaps);if(!maps.length)maps=[basis+'/sitemap.xml'];o.maps=maps.slice(0,8);
  const urls=[];const subs={};let n=0;
  const rij=maps.slice(0,6);
  while(rij.length&&n<40){const m=rij.shift();n++;const r=await f(m,taal);const l=locs(r.t);subs[m]={st:r.st,n:l.length};
    for(const x of l){if(/\.xml(\.gz)?(\?|$)/i.test(x)){if(rij.length<60)rij.push(x)}else urls.push(x)}await sl(400);}
  o.subs=Object.fromEntries(Object.entries(subs).slice(0,25));o.nUrls=urls.length;
  const prod=urls.filter(u=>PROD.test(u));o.nProd=prod.length;o.vb=prod.slice(0,4);
  const kies=[...prod.filter(u=>/milch|milk|melk|lait|kaese|cheese|kaas|brot|bread|brood|kaffee|coffee|koffie|butter|boter|joghurt|yogh|eier|eggs|eieren/i.test(u)).slice(0,3),...prod.slice(0,1)];
  o.pages=[];for(const u of kies){const r=await f(u,taal);const t=r.t;
    const ld=[...t.matchAll(/<script[^>]*application\/ld\+json[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>/"price"/.test(s))||'';
    o.pages.push({u,st:r.st,len:t.length,titel:(t.match(/<title[^>]*>([^<]*)/)||[])[1],ldprice:(ld.match(/"price"\s*:\s*"?[\d.,]+/)||[])[0]||null,ld:ld.slice(0,300),prijzen:(t.match(/(?:€|£)\s?\d+[.,]\d{2}|\d+[.,]\d{2}\s?(?:€|EUR)/g)||[]).slice(0,5)});await sl(1200);}
  return o;}
const LANDEN={
 nl:[['Lidl NL','https://www.lidl.nl','nl-NL']],
 de:[['Rewe','https://www.rewe.de','de-DE'],['Edeka24','https://www.edeka24.de','de-DE'],['Netto MD','https://www.netto-online.de','de-DE'],['Aldi Süd','https://www.aldi-sued.de','de-DE'],['Aldi Nord','https://www.aldi-nord.de','de-DE'],['Kaufland','https://filiale.kaufland.de','de-DE'],['Penny','https://www.penny.de','de-DE'],['Lidl DE','https://www.lidl.de','de-DE'],['Globus','https://www.globus.de','de-DE'],['dm','https://www.dm.de','de-DE'],['Rossmann','https://www.rossmann.de','de-DE'],['Norma','https://www.norma-online.de','de-DE']],
 be:[['Delhaize','https://www.delhaize.be','nl-BE'],['Colruyt','https://www.colruyt.be','nl-BE'],['Carrefour BE','https://www.carrefour.be','nl-BE'],['Aldi BE','https://www.aldi.be','nl-BE'],['Lidl BE','https://www.lidl.be','nl-BE'],['AH BE','https://www.ah.be','nl-BE'],['Jumbo BE','https://www.jumbo.com','nl-BE'],['Spar BE','https://www.spar.be','nl-BE'],['Intermarché BE','https://www.intermarche.be','nl-BE'],['Cora','https://www.cora.be','fr-BE']],
 uk:[['Tesco','https://www.tesco.com','en-GB'],['Sainsbury\'s','https://www.sainsburys.co.uk','en-GB'],['Asda','https://groceries.asda.com','en-GB'],['Morrisons','https://groceries.morrisons.com','en-GB'],['Aldi UK','https://www.aldi.co.uk','en-GB'],['Lidl UK','https://www.lidl.co.uk','en-GB'],['Waitrose','https://www.waitrose.com','en-GB'],['Ocado','https://www.ocado.com','en-GB'],['Iceland','https://www.iceland.co.uk','en-GB'],['Co-op','https://www.coop.co.uk','en-GB']]};
const out={};
await Promise.all(Object.entries(LANDEN).map(async([land,lijst])=>{for(const [n,b,t] of lijst){try{out[land+' '+n]=await site(n,b,t)}catch(e){out[land+' '+n]={fout:String(e)}}}}));
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
