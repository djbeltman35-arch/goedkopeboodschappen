import fs from 'node:fs';
import {execSync} from 'node:child_process';
try{execSync('WINKELS=dekamarkt,vomar PER_DAG=30 node probe/ass.mjs',{stdio:'inherit'})}catch(e){}
const out={};
for(const id of ['dekamarkt','vomar']){try{const d=JSON.parse(fs.readFileSync(`data/assortiment-${id}.json`,'utf8'));out[id]={n:d.d.length,bek:Object.keys(d.bekeken).length,weg:Object.values(d.bekeken).filter(x=>x.weg).length,vb:d.d.slice(0,10)};}catch(e){out[id]=String(e)}}
fs.writeFileSync('probe/out.json',JSON.stringify(out,null,1));
