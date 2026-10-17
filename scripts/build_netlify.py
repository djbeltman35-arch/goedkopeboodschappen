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
<title>Boodschappen vergelijken: goedkoopste supermarkt per product | Goedkope Boodschappen</title>
<meta name="description" content="Vergelijk je boodschappen bij Albert Heijn, Jumbo, Lidl, PLUS, Dirk, DekaMarkt, Hoogvliet, SPAR, Poiesz en Vomar. Zie per artikel de goedkoopste supermarkt, de top 3 winkels voor je hele lijst, en ga direct naar het product.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://goedkopeboodschappen.netlify.app/">
<meta property="og:url" content="https://goedkopeboodschappen.netlify.app/">
<meta name="theme-color" content="#ffcf1f">
<meta property="og:type" content="website">
<meta property="og:locale" content="nl_NL">
<meta property="og:title" content="Goedkope Boodschappen: waar zijn je boodschappen het goedkoopst?">
<meta property="og:description" content="Maak je boodschappenlijst en zie per artikel de goedkoopste supermarkt, plus de top 3 winkels voor je hele lijst.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23ffcf1f'/%3E%3Cpath d='M7 10h3l2.5 10h10l2-7H12' fill='none' stroke='%23221f17' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3Ccircle cx='14' cy='24' r='1.8' fill='%23221f17'/%3E%3Ccircle cx='21' cy='24' r='1.8' fill='%23b8322a'/%3E%3C/svg%3E">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Goedkope Boodschappen","url":"https://goedkopeboodschappen.netlify.app/","inLanguage":"nl-NL","description":"Boodschappen vergelijken bij Nederlandse supermarkten, met directe links naar elk product."}</script>
<style>*,*::before,*::after{box-sizing:border-box}html{-webkit-text-size-adjust:100%}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
'''
i=s.index('<div class="bar">')
seo='''<section class="wrap" aria-label="Over Goedkope Boodschappen" style="padding-block:8px 24px">
  <div class="step seo">
    <h2>Boodschappen vergelijken bij alle grote supermarkten</h2>
    <p>Goedkope Boodschappen zoekt bij Albert Heijn, Jumbo, Lidl, PLUS, Dirk, DekaMarkt, Hoogvliet, SPAR, Poiesz en Vomar het goedkoopste product voor elk artikel op je boodschappenlijst. Je ziet de prijs per kilo of liter, bij welke supermarkt het artikel het goedkoopst is, en een directe link naar het product op de site van de supermarkt.</p>
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
seo=seo.replace('{LINKS}',links)
body=s[i:].replace('<footer class="wrap site-foot">',seo+'<footer class="wrap site-foot">',1)
open(dst,'w').write(head+s[:i]+'</head>\n<body>\n'+body+'\n</body>\n</html>\n')
