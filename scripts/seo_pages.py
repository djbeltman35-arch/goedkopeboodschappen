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
.bar{background:#c8281e}.bar .wrap{padding-block:10px}.top{background:#ffcf1f;border-bottom:4px solid #c8281e}.wrap{max-width:900px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
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
FAV='<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' rx=\'8\' fill=\'%23ffcf1f\'/%3E%3Cpath d=\'M7 10h3l2.5 10h10l2-7H12\' fill=\'none\' stroke=\'%23221f17\' stroke-width=\'2.4\' stroke-linecap=\'round\' stroke-linejoin=\'round\'/%3E%3Ccircle cx=\'14\' cy=\'24\' r=\'1.8\' fill=\'%23221f17\'/%3E%3Ccircle cx=\'21\' cy=\'24\' r=\'1.8\' fill=\'%23c8281e\'/%3E%3C/svg%3E">'
FOOT='<footer><a href="/">Goedkope Boodschappen</a> · <a href="/vergelijk/">Alle producten</a><br><a href="mailto:erik@beltman.email" title="Mail naar erik@beltman.email">Made by Erik</a></footer>'
def page(title,desc,path,body,ld):
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{BASE}{path}">
<meta property="og:type" content="website"><meta property="og:locale" content="nl_NL"><meta property="og:url" content="{BASE}{path}"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta name="theme-color" content="#ffcf1f">
{FAV}{FONT}<style>{CSS}</style><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script></head><body>
<div class="bar"><div class="wrap"><a class="brand" href="/">Goedkope Boodschappen</a></div></div><header class="top"><div class="wrap">{body[0]}</div></header><main class="wrap">{body[1]}</main>{FOOT}</body></html>'''
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
