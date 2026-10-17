import json,re,sys,html,unicodedata,datetime
BASE="https://goedkopeboodschappen.netlify.app"
d=json.load(open(sys.argv[1])); out=sys.argv[2]
stores=d['stores']; prods=d['products']
def norm(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=re.sub(r'[^a-z0-9,.]+',' ',s); s=re.sub(r'(\d)[,.](\d)',r'\1,\2',s); return s.split()
for p in prods: p.append(set(norm(p[1]+' '+(p[4] or ''))))
TERMS=["halfvolle melk","volle melk","karnemelk","yoghurt","kwark","vla","boter","roomboter","margarine","eieren","jonge kaas","belegen kaas","oude kaas","geraspte kaas","hagelslag","pindakaas","jam","appelstroop","chocoladepasta","volkoren brood","wit brood","beschuit","crackers","ontbijtkoek","cornflakes","havermout","muesli","koffiebonen","koffiepads","filterkoffie","thee","suiker","bloem","rijst","pasta","spaghetti","macaroni","penne","tomatenpuree","pastasaus","olijfolie","zonnebloemolie","mayonaise","ketchup","mosterd","appelmoes","bananen","appels","sinaasappels","aardappelen","uien","tomaten","komkommer","paprika","wortels","broccoli","sla","champignons","kipfilet","gehakt","rookworst","ham","salami","zalm","tonijn","eierkoeken","stroopwafels","chips","pinda","chocolade","drop","cola","coca cola","sinaasappelsap","appelsap","bier","spa","toiletpapier","keukenrol","wasmiddel","afwasmiddel","tandpasta","shampoo","luiers","kattenvoer","hondenvoer"]
# Categorieen komen uit de site zelf (const CATS in site/index.html), zodat site en SEO-pagina's gelijk blijven.
CATS=json.loads(re.search(r'const CATS=(\[.*?\]);//EINDE CATS',open(sys.argv[3]).read()).group(1)) if len(sys.argv)>3 else []
for c in CATS:
    for t in c[2]:
        if t not in TERMS: TERMS.append(t)
EXCL={'choco','chocolade','gekookte','spinazie','roasted','americanos','krieltjes','salade','saus','smaak','snack','reep','koek','koekjes','chips','drink','mix'}
def slug(t): return re.sub(r'[^a-z0-9]+','-',t).strip('-')
CSS='''*,*::before,*::after{box-sizing:border-box}body{margin:0;font-family:"Public Sans",system-ui,sans-serif;background:#fbfaf5;color:#221f17;line-height:1.5}
.bar{background:#c8281e}.bar .wrap{padding-block:10px}.nav{display:flex;align-items:center;gap:14px}.nav .nl{color:#fff;font-weight:700;font-size:14px;text-decoration:none;white-space:nowrap}.nav .brand{margin-right:auto}@media (max-width:520px){.brand{font-size:16px!important}.nav .nl{font-size:13px}.nav{gap:10px}}.top{background:#ffcf1f;border-bottom:4px solid #c8281e}.wrap{max-width:900px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.top .wrap{padding-block:16px 20px}.brand{font:700 19px "Familjen Grotesk",system-ui,sans-serif;color:#fff;text-decoration:none}
h1{font:700 clamp(26px,4vw,36px)/1.15 "Familjen Grotesk",system-ui,sans-serif;margin:10px 0 6px}
.lead{margin:0;max-width:65ch}main{padding-block:20px 32px}
.tbl{overflow-x:auto;background:#fff;border:1px solid #ebe5d3;border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:10px 12px;text-align:left;border-top:1px solid #ebe5d3;vertical-align:top}th{border-top:none;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#6b6455}
td.p{font:700 15px "JetBrains Mono",ui-monospace,monospace;white-space:nowrap;text-align:right}tr.best td{background:#fff6d1}tr.best td:first-child{box-shadow:inset 4px 0 0 #c8281e}
a{color:inherit}.cta{display:inline-block;margin:18px 0;background:#c8281e;color:#fff;font-weight:700;padding:12px 18px;border-radius:10px;text-decoration:none}
.links{columns:3 180px;padding:0;list-style:none}.links li{padding:3px 0}.note{color:#6b6455;font-size:13px}
footer{text-align:center;color:#6b6455;font-size:14px;padding:8px 16px 32px}footer a{color:#c8281e;font-weight:600;text-decoration:none}
@media (prefers-color-scheme:dark){body{background:#16140f;color:#f1ecdf}.tbl{background:#1f1c15;border-color:#363126}th,td{border-color:#363126}th,.note,footer{color:#aba28c}tr.best td{background:#3a3214}}'''
FONT='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@700&family=Public+Sans:wght@400;700&family=JetBrains+Mono:wght@700&display=swap">'
FAV='<link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="icon" href="/icons/icon-192.png" sizes="192x192" type="image/png"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
FOOT='<footer><a href="/">Goedkope Boodschappen</a> · <a href="/vergelijk/">Alle producten</a><br><a href="mailto:erik@beltman.email" title="Mail naar erik@beltman.email">Made by Erik</a></footer>'
def page(title,desc,path,body,ld):
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{BASE}{path}">
<meta property="og:type" content="website"><meta property="og:locale" content="nl_NL"><meta property="og:url" content="{BASE}{path}"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta name="theme-color" content="#ffcf1f">
{FAV}{FONT}<style>{CSS}</style><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script></head><body>
<div class="bar"><div class="wrap nav"><a class="brand" href="/">Goedkope Boodschappen</a><a class="nl" href="/aanbiedingen/">Aanbiedingen</a><a class="nl" href="/vergelijk/">Alle producten</a></div></div><header class="top"><div class="wrap">{body[0]}</div></header><main class="wrap">{body[1]}</main>{FOOT}</body></html>'''
eur=lambda v:("€ %.2f"%v).replace('.',',')
made=[]
import os
os.makedirs(f'{out}/vergelijk',exist_ok=True)
for t in TERMS:
    toks=norm(t); rows=[]
    for si,s in enumerate(stores):
        cand=[p for p in prods if p[0]==si and all(w in p[7] for w in toks) and not ((p[7]&EXCL)-set(toks))]
        if not cand: continue
        m=min(len(p[7]) for p in cand); cand=[p for p in cand if len(p[7])<=m+3]
        best=min(cand,key=lambda p:(p[5] if p[5] is not None else 1e9,p[3]))
        rows.append((s,best))
    if len(rows)<3: continue
    rows.sort(key=lambda r:(r[1][5] if r[1][5] is not None else 1e9, r[1][3]))
    name=t[0].upper()+t[1:]; sl=slug(t); path=f'/vergelijk/{sl}/'
    cheapest=rows[0]
    unit=lambda p: f'{eur(p[5])} / {p[6]}' if p[5] is not None else ''
    trs=''.join(f'<tr{" class=best" if i==0 else ""}><td><b>{html.escape(s["name"])}</b></td><td><a href="{html.escape(s["base"]+p[2])}" rel="nofollow noopener" target="_blank">{html.escape(p[1])}</a><br><span class="note">{html.escape(p[4] or "")}</span></td><td class="p">{eur(p[3])}</td><td class="p">{unit(p)}</td></tr>' for i,(s,p) in enumerate(rows))
    prices=[p[3] for _,p in rows]
    title=f'{name} prijs vergelijken: goedkoopste supermarkt | Goedkope Boodschappen'
    desc=f'{name} is het goedkoopst bij {cheapest[0]["name"]} ({unit(cheapest[1]) or eur(cheapest[1][3])}). Vergelijk {name.lower()} bij {len(rows)} supermarkten, met directe links naar het product.'
    ld=[{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Goedkope Boodschappen","item":BASE+"/"},{"@type":"ListItem","position":2,"name":"Vergelijken","item":BASE+"/vergelijk/"},{"@type":"ListItem","position":3,"name":name,"item":BASE+path}]},
        {"@context":"https://schema.org","@type":"ItemList","name":f"{name} per supermarkt","itemListElement":[{"@type":"ListItem","position":i+1,"item":{"@type":"Product","name":p[1],"offers":{"@type":"Offer","price":f"{p[3]:.2f}","priceCurrency":"EUR","url":s["base"]+p[2],"seller":{"@type":"Organization","name":s["name"]}}}} for i,(s,p) in enumerate(rows)]}]
    per={'kg':'per kilo','l':'per liter','st':'per stuk'}.get(cheapest[1][6],'')
    head=f'<h1>{html.escape(name)}: waar is het het goedkoopst?</h1><p class="lead">{html.escape(name)} koop je {per} het voordeligst bij <b>{html.escape(cheapest[0]["name"])}</b>. Hieronder per supermarkt het voordeligste product, van goedkoop naar duur.</p>'
    main=f'<div class="tbl"><table><thead><tr><th>Supermarkt</th><th>Product</th><th>Prijs</th><th>Per kg/l</th></tr></thead><tbody>{trs}</tbody></table></div><a class="cta" href="/">Zet {html.escape(name.lower())} op je boodschappenlijst</a><p class="note">Prijzen van {len(rows)} supermarkten, van {eur(min(prices))} tot {eur(max(prices))}. Reguliere webshopprijzen uit de open dataset van Checkjebon, zonder aanbiedingen. De prijs aan de kassa is leidend.</p>'
    os.makedirs(f'{out}/vergelijk/{sl}',exist_ok=True)
    open(f'{out}/vergelijk/{sl}/index.html','w').write(page(title,desc,path,(head,main),ld))
    made.append((name,path))
best={}
for name,path in made: best[name.lower()]=path
cats=[]
for c in CATS:
    items=[t for t in c[2] if t in best]
    if not items: continue
    cs=slug(c[0].lower()); cpath=f'/categorie/{cs}/'
    li=''.join(f'<li><a href="{best[t]}">{html.escape(t[0].upper()+t[1:])}</a></li>' for t in items)
    head=f'<h1>{html.escape(c[0])} vergelijken</h1><p class="lead">Bij welke supermarkt koop je {html.escape(c[0].lower())} het goedkoopst? Kies een product en zie de prijzen van alle grote supermarkten naast elkaar.</p>'
    main=f'<ul class="links">{li}</ul><a class="cta" href="/">Maak je boodschappenlijst</a>'
    ld={"@context":"https://schema.org","@type":"CollectionPage","name":f"{c[0]} vergelijken","url":BASE+cpath,"breadcrumb":{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Goedkope Boodschappen","item":BASE+"/"},{"@type":"ListItem","position":2,"name":c[0],"item":BASE+cpath}]}}
    os.makedirs(f'{out}/categorie/{cs}',exist_ok=True)
    open(f'{out}/categorie/{cs}/index.html','w').write(page(f'{c[0]} prijzen vergelijken bij alle supermarkten | Goedkope Boodschappen',f'Vergelijk de prijzen van {", ".join(items[:4])} en meer {c[0].lower()} bij Albert Heijn, Jumbo, Lidl, PLUS, Dirk en andere supermarkten.',cpath,(head,main),ld))
    cats.append((c[0],cpath))
open(f'{out}/categorieen.txt','w').write('\n'.join(f'{n}\t{p}' for n,p in cats))
lis=''.join(f'<li><a href="{p}">{html.escape(n)}</a></li>' for n,p in sorted(made))
open(f'{out}/vergelijk/index.html','w').write(page('Boodschappen vergelijken per product | Goedkope Boodschappen',f'Vergelijk de prijs van {len(made)} veelgekochte boodschappen bij Albert Heijn, Jumbo, Lidl, PLUS, Dirk en meer supermarkten.','/vergelijk/',('<h1>Boodschappen vergelijken per product</h1><p class="lead">Kies een product en zie bij welke supermarkt het het goedkoopst is.</p>',('<h2>Categorieën</h2><ul class="links">'+''.join(f'<li><a href="{p}">{html.escape(n)}</a></li>' for n,p in cats)+'</ul><h2>Alle producten</h2>' if cats else '')+f'<ul class="links">{lis}</ul><a class="cta" href="/">Maak je boodschappenlijst</a>'),{"@context":"https://schema.org","@type":"CollectionPage","name":"Boodschappen vergelijken per product","url":BASE+"/vergelijk/"}))
today=datetime.date.today().isoformat()
urls=['/','/vergelijk/']+[p for _,p in cats]+[p for _,p in made]
open(f'{out}/sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)+'</urlset>\n')
open(f'{out}/robots.txt','w').write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(len(made),'paginas')

# ---------- Aanbiedingenpagina's (optioneel 4e argument: data/aanbiedingen.json) ----------
# Statische HTML met de aanbiedingen van het moment (voor Google), die in de browser wordt ververst met de dagelijkse data.
if len(sys.argv)>4 and os.path.exists(sys.argv[4]):
    off=json.load(open(sys.argv[4]))
    today=datetime.date.today().isoformat()
    O=[o for o in off['offers'] if o.get('p') and (not o.get('t') or o['t']>=today)]
    NAMES={'ah':'Albert Heijn','jumbo':'Jumbo','lidl':'Lidl','aldi':'Aldi','dirk':'Dirk','plus':'PLUS','dekamarkt':'DekaMarkt','hoogvliet':'Hoogvliet','vomar':'Vomar','spar':'SPAR','poiesz':'Poiesz'}
    SHORT={'ah':'AH'}
    pct=lambda o:(o['was']-o['p'])/o['was'] if o.get('was') and o['was']>o['p'] else 0
    O.sort(key=lambda o:(-pct(o),o['p']))
    per={}
    for o in O: per.setdefault(o['s'],[]).append(o)
    stores_o=[s for s in NAMES if s in per]
    DAG=['ma','di','wo','do','vr','za','zo'];MND=['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec']
    def tot(t):
        d=datetime.date.fromisoformat(t); return f'{DAG[d.weekday()]} {d.day} {MND[d.month-1]}'
    OCSS='''.grid{list-style:none;padding:0;margin:16px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.o{background:#fff;border:2px solid #ebe5d3;border-radius:12px;padding:12px;display:grid;gap:6px;align-content:start}
.s{display:inline-block;font:700 11px "Public Sans",system-ui,sans-serif;text-transform:uppercase;letter-spacing:.05em;color:#fff;background:#c8281e;padding:2px 7px;border-radius:4px}
.l{display:inline-block;margin-left:6px;font:700 11px "Public Sans",system-ui,sans-serif;text-transform:uppercase;background:#ffcf1f;color:#221f17;padding:2px 7px;border-radius:4px}
.o b{font-weight:700;overflow-wrap:anywhere}.o .z{color:#6b6455;font-size:13px}
.pr{font:700 16px "JetBrains Mono",ui-monospace,monospace;background:#ffcf1f;color:#221f17;padding:3px 8px;border-radius:4px}.o s{color:#6b6455;font-size:13px;margin-left:6px}.o .t{font-size:12px;color:#6b6455}
.add{width:100%;margin-top:4px;background:#c8281e;color:#fff;border:none;border-radius:10px;padding:9px;font:700 14px "Public Sans",system-ui,sans-serif;cursor:pointer}.add:hover{background:#a11d15}.add.on{background:#eef7f1;color:#1d7a46}
.bar2{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);width:min(560px,calc(100% - 32px));display:flex;justify-content:space-between;align-items:center;gap:10px;background:#221f17;color:#fff;padding:10px 10px 10px 16px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.25);font-size:14px;z-index:5}.bar2 a{background:#c8281e;color:#fff;font-weight:700;padding:8px 12px;border-radius:10px;text-decoration:none;white-space:nowrap}.bar2[hidden]{display:none}
.fsel{display:block;margin:12px 0 0;max-width:420px}.fsel select{width:100%;font:600 15px "Public Sans",system-ui,sans-serif;padding:10px 12px;border:2px solid #ebe5d3;border-radius:10px;background:#fff;color:#221f17}.fsel select:focus{border-color:#c8281e;outline:none}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.o[hidden]{display:none}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 0}.chips a{background:#fff;border:1px solid #ebe5d3;border-radius:999px;padding:5px 12px;font-weight:700;font-size:14px;text-decoration:none}.chips a.on{background:#c8281e;border-color:#c8281e;color:#fff}
@media (prefers-color-scheme:dark){.o,.chips a{background:#1f1c15;border-color:#363126}}'''
    def card(o):
        lbl=f'<span class="l">{html.escape(o["lbl"])}</span>' if o.get('lbl') else ''
        was=f'<s>{eur(o["was"])}</s>' if o.get('was') and o['was']>o['p'] else ''
        t=f'<span class="t">t/m {tot(o["t"])}</span>' if o.get('t') else ''
        return f'<li class="o" data-c="{html.escape(o.get("c") or "Overig")}"><span><span class="s">{html.escape(SHORT.get(o["s"],NAMES[o["s"]]))}</span>{lbl}</span><a href="{html.escape(o["u"])}" rel="nofollow noopener" target="_blank"><b>{html.escape(o["n"])}</b></a><span class="z">{html.escape(o.get("sz") or "")}</span><span><span class="pr">{eur(o["p"])}</span>{was}</span>{t}<button type="button" class="add" data-o="{html.escape(json.dumps({k:o.get(k) for k in ('s','n','sz','p','u','t')},ensure_ascii=False))}">+ Op mijn lijst</button></li>'
    JS='''<script>(()=>{const S=document.currentScript.dataset.s,N=%s,SH={ah:"AH"},e=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])),eur=v=>"€ "+v.toFixed(2).replace(".",","),d=new Date().toISOString().slice(0,10),
t=x=>new Date(x+"T12:00:00").toLocaleDateString("nl-NL",{weekday:"short",day:"numeric",month:"short"}).replace(".","");
fetch("https://raw.githubusercontent.com/djbeltman35-arch/goedkopeboodschappen/main/data/aanbiedingen.json",{cache:"no-cache"}).then(r=>r.json()).then(j=>{
let o=j.offers.filter(x=>N[x.s]&&x.p>0&&(!x.t||x.t>=d)&&(!S||x.s===S));const p=x=>x.was>x.p?(x.was-x.p)/x.was:0;o.sort((a,b)=>p(b)-p(a)||a.p-b.p);if(!o.length)return;
document.getElementById("cnt").textContent=o.length;
document.getElementById("grid").innerHTML=o.slice(0,2500).map(x=>`<li class="o" data-c="${e(x.c||"Overig")}"><span><span class="s">${e(SH[x.s]||N[x.s])}</span>${x.lbl?`<span class="l">${e(x.lbl)}</span>`:""}</span><a href="${e(x.u)}" rel="nofollow noopener" target="_blank"><b>${e(x.n)}</b></a><span class="z">${e(x.sz||"")}</span><span><span class="pr">${eur(x.p)}</span>${x.was>x.p?`<s>${eur(x.was)}</s>`:""}</span>${x.t?`<span class="t">t/m ${t(x.t)}</span>`:""}<button type="button" class="add" data-o="${e(JSON.stringify({s:x.s,n:x.n,sz:x.sz,p:x.p,u:x.u,t:x.t}))}">+ Op mijn lijst</button></li>`).join("");mark();applyCat(1)}).catch(()=>{})})()</script>
<div class="bar2" id="bar2" hidden><span id="bar2t"></span><a href="/#lijst">Naar mijn lijst</a></div>
<script>window.applyCat=(keep)=>{const s=document.getElementById("fcat");if(!s)return;const v=s.value,g=document.getElementById("grid");if(keep&&v&&![...g.children].some(li=>li.dataset.c===v)){s.value="";}const w=s.value;let n=0;[...g.children].forEach(li=>{const h=!!w&&li.dataset.c!==w;li.hidden=h;if(!h)n++});document.getElementById("cnt").textContent=n};
document.addEventListener("change",e=>{if(e.target.id==="fcat")applyCat()});</script>
<script>(()=>{const K="lijst-erbij",get=()=>{try{return JSON.parse(localStorage.getItem(K)||"[]")}catch(e){return []}},put=v=>{try{localStorage.setItem(K,JSON.stringify(v));return true}catch(e){return false}};
window.mark=()=>{const q=get(),u=new Set(q.map(x=>x.u));document.querySelectorAll(".add").forEach(b=>{const o=JSON.parse(b.dataset.o);if(u.has(o.u)){b.textContent="✓ Op je lijst";b.classList.add("on")}});const n=q.length;document.getElementById("bar2").hidden=!n;document.getElementById("bar2t").textContent=n+(n===1?" aanbieding":" aanbiedingen")+" klaar voor je lijst"};
document.addEventListener("click",ev=>{const b=ev.target.closest(".add");if(!b)return;const o=JSON.parse(b.dataset.o),q=get();if(!q.some(x=>x.u===o.u)){q.push(o);if(!put(q)){b.textContent="Bewaren lukt niet in deze browser";return}}mark()});mark()})()</script>''' % json.dumps(NAMES)
    def chips(cur):
        return '<nav class="chips" aria-label="Supermarkten">'+f'<a href="/aanbiedingen/"{" class=on" if not cur else ""}>Alle</a>'+''.join(f'<a href="/aanbiedingen/{s}/"{" class=on" if cur==s else ""}>{html.escape(NAMES[s])}</a>' for s in stores_o)+'</nav>'
    def opage(cur,lst):
        nm=NAMES.get(cur,'')
        path=f'/aanbiedingen/{cur}/' if cur else '/aanbiedingen/'
        if cur:
            title=f'{nm} aanbiedingen deze week: alle acties op een rij | Goedkope Boodschappen'
            desc=f'Alle {len(lst)} aanbiedingen van {nm} deze week, met de grootste korting eerst. Elke dag bijgewerkt, met directe links naar het product.'
            h=f'<h1>{html.escape(nm)} aanbiedingen deze week</h1><p class="lead"><span id="cnt">{len(lst)}</span> acties van {html.escape(nm)}, de grootste korting eerst. Elke dag automatisch bijgewerkt.</p>'
        else:
            title='Aanbiedingen deze week bij alle supermarkten | Goedkope Boodschappen'
            desc=f'Alle supermarktaanbiedingen van deze week op een rij: {", ".join(NAMES[s] for s in stores_o)}. Grootste korting eerst, elke dag bijgewerkt.'
            h=f'<h1>Aanbiedingen deze week bij alle supermarkten</h1><p class="lead"><span id="cnt">{len(lst)}</span> acties van {", ".join(html.escape(NAMES[s]) for s in stores_o)}, de grootste korting eerst. Elke dag automatisch bijgewerkt.</p>'
        crumbs=[{"@type":"ListItem","position":1,"name":"Goedkope Boodschappen","item":BASE+"/"},{"@type":"ListItem","position":2,"name":"Aanbiedingen","item":BASE+"/aanbiedingen/"}]
        if cur: crumbs.append({"@type":"ListItem","position":3,"name":nm,"item":BASE+path})
        ld=[{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":crumbs},{"@context":"https://schema.org","@type":"CollectionPage","name":title.split(' | ')[0],"url":BASE+path}]
        cnt={}
        for o in lst: cnt[o.get('c') or 'Overig']=cnt.get(o.get('c') or 'Overig',0)+1
        corder=[c[0] for c in CATS if c[0] in cnt]+(['Overig'] if 'Overig' in cnt else [])
        icon={c[0]:c[1] for c in CATS}
        sel=f'<label class="fsel"><span class="sr">Categorie</span><select id="fcat"><option value="">Alle categorieën ({len(lst)})</option>'+''.join(f'<option value="{html.escape(c)}">{icon.get(c,"🛒")} {html.escape(c)} ({cnt[c]})</option>' for c in corder)+'</select></label>' if len(corder)>1 else ''
        main=chips(cur)+sel+f'<ul class="grid" id="grid">{"".join(card(o) for o in lst[:300])}</ul><a class="cta" href="/">Zet aanbiedingen op je boodschappenlijst</a><p class="note">Actieprijzen zoals de supermarkt ze online toont. Bij acties als 1+1 gratis staat de prijs per stuk bij afname van de actie. De prijs aan de kassa is leidend.</p>'+JS.replace('document.currentScript.dataset.s',json.dumps(cur or ''))
        pg=page(title,desc,path,(h,main),ld).replace('</style>',OCSS+'</style>',1)
        os.makedirs(out+path,exist_ok=True); open(out+path+'index.html','w').write(pg)
        return path
    opaths=[opage(None,O)]+[opage(s,per[s]) for s in stores_o]
    sm=open(f'{out}/sitemap.xml').read()
    sm=sm.replace('</urlset>',''.join(f'  <url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>\n' for u in opaths)+'</urlset>')
    open(f'{out}/sitemap.xml','w').write(sm)
    open(f'{out}/aanbiedingen.txt','w').write('\n'.join(f'{NAMES[s]}\t/aanbiedingen/{s}/' for s in stores_o))
    print(len(opaths),'aanbiedingenpaginas')
