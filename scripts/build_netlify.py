import sys,re,os
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read().replace('<span class="proto">Prototype</span>','')
s=re.sub(r'<title>.*?</title>\n','',s,count=1)
s=s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
head='''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Boodschappen vergelijken en aanbiedingen deze week | Goedkope Boodschappen</title>
<meta name="description" content="Vergelijk je boodschappen bij Albert Heijn, Jumbo, Lidl, Aldi, PLUS, Dirk en meer. Zie per artikel de goedkoopste supermarkt, alle aanbiedingen van deze week en wat je hele lijst kost bij de 3 voordeligste supermarkten.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://goedkopeboodschappen.netlify.app/">
<meta property="og:url" content="https://goedkopeboodschappen.netlify.app/">
<meta name="theme-color" content="#ffcf1f">
<meta property="og:type" content="website">
<meta name="google-site-verification" content="A7YLnMM23y16A-WSlNAJXJ_tnVpGrncvf_dhjl522pM"><meta property="og:locale" content="nl_NL"><meta property="og:image" content="https://goedkopeboodschappen.netlify.app/icons/icon-512.png"><meta property="og:site_name" content="Goedkope Boodschappen"><meta name="twitter:card" content="summary">
<meta property="og:title" content="Goedkope Boodschappen: waar zijn je boodschappen het goedkoopst?">
<meta property="og:description" content="Maak je boodschappenlijst en zie per artikel de goedkoopste supermarkt, plus de top 3 winkels voor je hele lijst.">
<link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="icon" href="/icons/icon-192.png" sizes="192x192" type="image/png"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">
<script type="application/ld+json">[{"@context":"https://schema.org","@type":"WebSite","name":"Goedkope Boodschappen","url":"https://goedkopeboodschappen.netlify.app/","inLanguage":"nl-NL","description":"Boodschappen vergelijken bij Nederlandse supermarkten, met directe links naar elk product.","potentialAction":{"@type":"SearchAction","target":"https://goedkopeboodschappen.netlify.app/?q={search_term_string}","query-input":"required name=search_term_string"}},{"@context":"https://schema.org","@type":"Organization","name":"Goedkope Boodschappen","url":"https://goedkopeboodschappen.netlify.app/","logo":"https://goedkopeboodschappen.netlify.app/icons/icon-512.png"}]</script>
<style>*,*::before,*::after{box-sizing:border-box}html{-webkit-text-size-adjust:100%}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
'''
i=s.index('<div class="bar">')
seo='''<section class="wrap" aria-label="Over Goedkope Boodschappen" style="padding-block:8px 24px">
  <div class="step seo">
    <h2>Boodschappen vergelijken bij alle grote supermarkten</h2>
    <p>Goedkope Boodschappen zoekt bij Albert Heijn, Jumbo, Lidl, Aldi, PLUS, Dirk, DekaMarkt, Hoogvliet, SPAR, Poiesz en Vomar het goedkoopste product voor elk artikel op je boodschappenlijst. Je ziet de prijs per kilo of liter, bij welke supermarkt het artikel het goedkoopst is, en een directe link naar het product op de site van de supermarkt.</p>
    {LINKS}
    <p>De top 3 laat zien in welke winkel je de meeste artikelen goedkoop in één keer haalt. Bewaar je lijst, dan vergelijken we hem bij je volgende bezoek automatisch opnieuw.</p>
  </div>
</section>
<noscript><p class="wrap">Zet JavaScript aan om prijzen te vergelijken.</p></noscript>
'''
vd=os.path.join(os.path.dirname(dst),'vergelijk')
pop=['halfvolle-melk','eieren','jonge-kaas','pindakaas','hagelslag','volkoren-brood','koffiebonen','bananen','kipfilet','gehakt','pasta','rijst','coca-cola','chips','toiletpapier','wasmiddel']
pop=[p for p in pop if os.path.isdir(os.path.join(vd,p))]
links='<h3>Populaire producten vergelijken</h3><p>'+' · '.join(f'<a href="/vergelijk/{p}/">{p.replace("-"," ").capitalize()}</a>' for p in pop)+' · <a href="/vergelijk/">Alle producten</a></p>'
ct=os.path.join(os.path.dirname(dst),'categorieen.txt')
if os.path.exists(ct):
    cats=[l.split('\t') for l in open(ct).read().splitlines() if l]
    links='<h3>Categorieën</h3><p>'+' · '.join(f'<a href="{p}">{n}</a>' for n,p in cats)+'</p>'+links
    os.remove(ct)
at=os.path.join(os.path.dirname(dst),'aanbiedingen.txt')
if os.path.exists(at):
    st=[l.split('\t') for l in open(at).read().splitlines() if l]
    links='<h3>Aanbiedingen deze week</h3><p><a href="/aanbiedingen/">Alle aanbiedingen</a> · '+' · '.join(f'<a href="{p}">{n} aanbiedingen</a>' for n,p in st)+'</p>'+links
    os.remove(at)
seo=seo.replace('{LINKS}',links)
body=s[i:].replace('<footer class="wrap site-foot">',seo+'<footer class="wrap site-foot">',1)
# Versie onderaan, zodat je kunt zien welke zip er online staat.
import datetime,zoneinfo
ver=datetime.datetime.now(zoneinfo.ZoneInfo('Europe/Amsterdam')).strftime('%d-%m-%Y %H:%M')
body=body.replace('Made by Erik</a></p></footer>',f'Made by Erik</a></p><p style="font-size:12px;opacity:.6;margin:4px 0 0">Versie {ver}</p></footer>',1)
open(dst,'w').write(head+s[:i]+'</head>\n<body>\n'+body+'\n</body>\n</html>\n')
