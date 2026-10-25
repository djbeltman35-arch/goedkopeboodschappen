import json,sys,re
src,out=sys.argv[1],sys.argv[2]
d=json.load(open(src))
UNITS={'kg':('g',1000),'kilogram':('g',1000),'kilo':('g',1000),'gram':('g',1),'gr':('g',1),'g':('g',1),'centiliter':('ml',10),
       'rol':('st',1),'rollen':('st',1),'zakjes':('st',1),'wasbeurten':('st',1),'pads':('st',1),'capsules':('st',1),'cups':('st',1),'tabletten':('st',1),'pack':('st',1),'pak':('st',1),
       'l':('ml',1000),'liter':('ml',1000),'litre':('ml',1000),'ltr':('ml',1000),'cl':('ml',10),'ml':('ml',1),'milliliter':('ml',1),
       'st':('st',1),'stuk':('st',1),'stuks':('st',1),'stk':('st',1),'x':None}
rx=re.compile(r'(?:(\d+)\s*[x×]\s*)?(\d+(?:[.,]\d+)?)\s*-?\s*(kilogram|kg|kilo|gram|gr|g|liter|litre|ltr|l|centiliter|cl|milliliter|ml|stuks|stuk|stk|st|rollen|rol|zakjes|wasbeurten|pads|capsules|cups|tabletten|pack|pak)\b',re.I)
VAST={'per kilo':(1000,'g'),'per kg':(1000,'g'),'per stuk':(1,'st'),'per liter':(1000,'ml'),'per bos':(1,'st'),'per doos':(1,'st')}
def parse(*texts):
    for t in texts:
        if not t: continue
        # De maat zegt zelf "per kilo" of "per stuk": de prijs geldt dan per kilo of per stuk.
        if t.strip().lower() in VAST: q,u=VAST[t.strip().lower()]; return q,u
        m=rx.search(t.lower().replace('per ',''))
        if m:
            mult=int(m.group(1) or 1); q=float(m.group(2).replace(',','.')); u,f=UNITS[m.group(3).lower()]
            v=mult*q*f
            if v>0: return v,u
    return None,None
stores=[];prods=[];stats={}
for si,s in enumerate(d):
    items=s.get('d',[])
    if not items: continue
    stores.append({'id':s['n'],'name':s['c'],'base':s['u']})
    ok=0;conflict=0
    for p in items:
        if not p.get('p'): continue
        # Speelgoed-miniaturen (LidlMini) en prijzen van een paar cent zijn geen echte boodschappen.
        if p['p']<0.05 or 'lidlmini' in p['n'].lower().replace(' ',''): continue
        v,u=parse(p.get('s',''),p['n'])
        # Staat er in de naam een andere hoeveelheid dan in de maat ("Kipfilet 1000 g" met maat "150 g"), dan klopt een van beide niet:
        # dan geen prijs per kilo/liter, zodat het product niet onterecht als goedkoopste bovenaan komt.
        vn,un=parse(p['n']); vs,us=parse(p.get('s',''))
        if vn and vs and un==us and max(vn,vs)/min(vn,vs)>1.25:
            # Uitzondering: "12x0,33 l" in de naam met als maat "0,33 l" (één blikje): dan klopt de naam (12 x 0,33 = 3,96 liter).
            mm=rx.search(p['n'].lower()); stuks=int(mm.group(1)) if mm and mm.group(1) else 0
            if stuks>1 and abs(vn/stuks-vs)<=vs*.02: v,u=vn,un
            else: v=None; conflict+=1
        up=None
        if v:
            ok+=1
            up=round(p['p']/v*(1000 if u in('g','ml') else 1),2)
        prods.append([len(stores)-1,p['n'],p['l'],p['p'],p.get('s',''),up,{'g':'kg','ml':'l','st':'st'}.get(u,'')])
    stats[s['n']]=(len(items),ok)
    if conflict: print(s['n'],conflict,'producten met tegenstrijdige maat')
[[p.__setitem__(1,p[1].replace("\ufffd","")) for p in prods]];json.dump({'stores':stores,'products':prods},open(out,'w'),ensure_ascii=False,separators=(',',':'))
for k,(n,ok) in stats.items(): print(f'{k:10} {n:6} producten, eenheidsprijs bij {ok/n*100 if n else 0:4.0f}%')
