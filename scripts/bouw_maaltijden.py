"""Pagina's voor complete maaltijden. Wordt met exec() in bouw_paginas.py gedraaid (gebruikt diens sjabloon-functies)."""
from maaltijd_kosten import MAAL, SOORTEN, NOTITIE, I

def hoev(q, eenheid_):
    if eenheid_ == "l": return f"{round(q * 1000)} ml" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} liter"
    return f"{round(q * 1000)} g" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} kg"
def pp(v): return eur(v / 4)
# Echte foto's (vrije licentie, Wikimedia Commons); maaltijden zonder foto houden de grafische afbeelding.
FOTO = json.load(open(os.path.join(ROOT, "scripts", "maaltijd_fotos.json")))
LIC = {"CC0": "https://creativecommons.org/publicdomain/zero/1.0/deed.nl"}
def lic_url(l):
    if l in LIC: return LIC[l]
    m_ = re.match(r"CC (BY(?:-SA)?) ([0-9.]+)", l)
    return f"https://creativecommons.org/licenses/{m_.group(1).lower()}/{m_.group(2)}/deed.nl" if m_ else None
def foto_html(m):
    f = FOTO.get(m["slug"])
    if not f: return ""
    lu, lt = lic_url(f["licentie"]), esc(f["licentie"])
    maker = esc(f["maker"]) + ", " if f["maker"] else ""
    licentie = f'<a href="{lu}" rel="noopener" target="_blank">{lt}</a>' if lu else lt
    return (f'<figure class="mfoto"><img src="/maaltijden-foto/{m["slug"]}-16x9.jpg" srcset="/maaltijden-foto/{m["slug"]}-kaart.jpg 640w, /maaltijden-foto/{m["slug"]}-16x9.jpg 1200w" sizes="(max-width: 760px) 100vw, 720px" width="1200" height="675" alt="{esc(m["naam"])}" fetchpriority="high" decoding="async">'
            f'<figcaption>Foto: {maker}{licentie}, via <a href="{esc(f["bron"])}" rel="noopener" target="_blank">Wikimedia Commons</a> (bijgesneden)</figcaption></figure>')
MAAL_BEELDEN = {}  # pad -> lijst afbeeldings-url's, voor de afbeeldingen-sitemap
def beeld_objecten(m):
    """Afbeeldingen als ImageObject met maker en licentie (Google toont dan de juiste bronvermelding)."""
    f = FOTO.get(m["slug"])
    if not f: return beelden(m)
    maten = {"16x9": (1200, 675), "4x3": (1200, 900), "1x1": (1200, 1200)}
    return [{"@type": "ImageObject", "url": u, "contentUrl": u, "width": maten[x][0], "height": maten[x][1],
             "creditText": f"{f['maker'] or 'Wikimedia Commons'} via Wikimedia Commons", "license": lic_url(f["licentie"]) or f["bron"],
             "acquireLicensePage": f["bron"], **({"creator": {"@type": "Person", "name": f["maker"]}} if f["maker"] else {})}
            for x, u in zip(("16x9", "4x3", "1x1"), beelden(m))]
def beelden(m):
    if m["slug"] in FOTO: return [f"{BASE}/maaltijden-foto/{m['slug']}-{x}.jpg" for x in ("16x9", "4x3", "1x1")]
    return [f"{BASE}/maaltijden-img/{m['slug']}-16x9.png", f"{BASE}/maaltijden-img/{m['slug']}-1x1.png"]
def kaartbeeld(m):
    if m["slug"] in FOTO: return f'<img class="mimg" src="/maaltijden-foto/{m["slug"]}-kaart.jpg" width="640" height="360" alt="" loading="lazy">'
    emo = {k: e_ for k, _, e_ in SOORTEN}.get(m["soort"], "🍽️")
    return f'<div class="mimg mleeg" aria-hidden="true">{emo}</div>'

MCSS = ""
# Toont alleen de supermarkten die de bezoeker bij "Mijn supermarkten" heeft aangevinkt (bewaard als "winkels-uit" in de browser).
# Zonder keuze blijft de pagina zoals hij gebouwd is (alle winkels); zo ziet Google ook de volledige vergelijking.
MKJS = ("<script>(()=>{const N=" + json.dumps({s_["id"]: NAMEN.get(s_["id"], s_["name"]) for s_ in stores}, ensure_ascii=False) + ",K=" + json.dumps({s_["id"]: KORT.get(s_["id"], NAMEN.get(s_["id"], s_["name"])) for s_ in stores}, ensure_ascii=False) + r""";
const e=v=>"€ "+v.toFixed(2).replace(".",","),tg=(v,c)=>`<span class="tag ${c||""}"><span class="e">€</span>${v.toFixed(2).replace(".",",")}</span>`,h=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const uit=()=>{try{return new Set(JSON.parse(localStorage.getItem("winkels-uit")||"[]")||[])}catch(x){return new Set()}};
const best=(p,off)=>{let b=null;for(const [s,v] of Object.entries(p))if(!off.has(s)&&(!b||v<b[1]))b=[s,v];return b};
function kaarten(off){document.querySelectorAll("[data-p]").forEach(el=>{const p=JSON.parse(el.dataset.p),b=best(p,off);el.dataset.best=b?b[1]:1e9;el.dataset.bs=b?b[0]:"";
 const k=el.querySelector(".kp"),w=el.querySelector(".kw"),q=el.querySelector(".kpp");if(!k)return;
 if(!b){k.innerHTML="";w.textContent="geen van jouw winkels";if(q)q.textContent="niet alle ingrediënten gevonden";return}
 k.innerHTML=tg(b[1]);w.textContent=N[b[0]]||b[0];if(q)q.textContent=e(b[1]/4)+(q.dataset.kort?" p.p.":" per persoon");
 const ws=el.querySelector(".mws");if(ws){const r=Object.entries(p).filter(([s])=>!off.has(s)).sort((a,c)=>a[1]-c[1]);ws.textContent=r.length===1?`🏪 Alleen bij ${K[r[0][0]]||N[r[0][0]]} ${e(r[0][1])}`:`🏪 Bij ${r.length} ${off.size?"van jouw ":""}winkels: `+r.map(([s,v])=>`${K[s]||N[s]} ${e(v)}`).join(", ")}});
 document.querySelectorAll("[data-sorteer]").forEach(tb=>{const rs=[...tb.children].sort((a,b)=>a.dataset.best-b.dataset.best);rs.forEach((r,i)=>{tb.appendChild(r);r.classList.toggle("win",i===0);const n=r.querySelector(".rn");if(n)n.textContent=(i+1)+"."})})}
function maaltijd(off){const el=document.getElementById("mdata");if(!el)return;const D=JSON.parse(el.textContent),ban=document.getElementById("mkeus");
 const ord=Object.keys(D.st).filter(s=>!off.has(s)).sort((a,b)=>D.st[a].t-D.st[b].t);const n=Object.keys(N).filter(s=>!off.has(s)).length;
 ban.hidden=false;const mist=Object.keys(N).filter(x=>!off.has(x)&&!D.st[x]);
 ban.innerHTML=`Vergeleken bij <b>jouw ${n} supermarkten</b>.`+(mist.length?` Bij ${mist.map(x=>h(N[x])).join(", ").replace(/, ([^,]*)$/," en $1")} vinden we niet alle ingrediënten online.`:"")+` <a href="/#mystores">Wijzig je supermarkten</a>`;
 if(!ord.length){document.getElementById("mlead").innerHTML="Bij jouw supermarkten vinden we niet alle ingrediënten online. Kies meer supermarkten om deze maaltijd te vergelijken.";
  ["mtop","mtab","malle"].forEach(i=>{const x=document.getElementById(i);if(x)x.innerHTML=""});return}
 const t3=ord.slice(0,3),b=D.st[ord[0]],l=D.st[ord[ord.length-1]];
 document.getElementById("mlead").innerHTML=`Bij jouw supermarkten kosten alle ingrediënten voor 4 personen het minst bij <b>${h(N[ord[0]])}</b>: <b>${e(b.t)}</b>. Daarvan gebruik je ${e(b.g)} in dit recept; de rest houd je over.`+(ord.length>1?` Bij ${h(N[ord[ord.length-1]])} betaal je ${e(l.t-b.t)} meer.`:"");
 document.getElementById("mtoph").textContent=t3.length===3?"De 3 goedkoopste supermarkten":t3.length===2?"Jouw 2 supermarkten":"Jouw supermarkt";document.getElementById("mtop").innerHTML=t3.map((s,i)=>`<li class="${i?"":"w"}"><span class="rk">${i+1}e goedkoopst</span><b style="font-size:19px">${h(N[s])}</b>${tg(D.st[s].t,i?"":"big")}<span class="muted">${e(D.st[s].t/4)} per persoon</span><button type="button" class="add addall" data-m="${D.slug}" data-os="${h(JSON.stringify(D.st[s].os))}">+ Alles op mijn lijst</button></li>`).join("");
 let j=0,rows="";for(const g of D.ing){if(g[2]){rows+=`<tr class="vk"><td>${h(g[0])}<span class="sub">uit de voorraadkast, niet meegeteld</span></td>${t3.map(()=>'<td class="c">–</td>').join("")}</tr>`;continue}
  rows+=`<tr><td><b>${h(g[0])}</b><span class="sub">${h(g[1])}${g[3]?" · optioneel":""}</span></td>${t3.map(s=>{const c=D.st[s].c[j];return c?`<td class="c"><a href="${h(c[2])}" rel="nofollow noopener" target="_blank" data-out="${s}" title="${h(c[1])}">${e(c[0])}</a>${c[3]>1?`<span class="sub">${c[3]} pakken</span>`:""}</td>`:'<td class="c"><span class="muted">niet gevonden</span></td>'}).join("")}</tr>`;j++}
 rows+=`<tr class="win"><td><b>Totaal voor 4 personen</b></td>${t3.map(s=>`<td class="c"><b>${e(D.st[s].t)}</b></td>`).join("")}</tr>`;
 document.getElementById("mtab").innerHTML=`<thead><tr><th>Ingrediënt</th>${t3.map(s=>`<th style="text-align:right">${h(K[s]||N[s])}</th>`).join("")}</tr></thead><tbody>${rows}</tbody>`;
 document.getElementById("malle").innerHTML=ord.map((s,i)=>`<tr${i?"":' class="win"'}><td><b>${i+1}. ${h(N[s])}</b></td><td class="p">${tg(D.st[s].t)}</td><td class="p">${e(D.st[s].t/4)}</td></tr>`).join("")}
function faq(D,ord){const nm=document.querySelector("h1")?.textContent.split(":")[0]||"Deze maaltijd",f1=document.getElementById("mfaq1"),f2=document.getElementById("mfaq2");if(!f1||!ord.length)return;
 document.title=`${nm}: wat kost het? Goedkoopst bij ${N[ord[0]]} (${e(D.st[ord[0]].t)} voor 4)`;
 const b=D.st[ord[0]],l=D.st[ord[ord.length-1]];f1.textContent=`${nm} voor 4 personen kost bij jouw supermarkten het minst bij ${N[ord[0]]}: ${e(b.t)}, dat is ${e(b.t/4)} per persoon.`+(ord.length>1?` Bij ${N[ord[ord.length-1]]} betaal je ${e(l.t)}.`:"");
 f2.textContent=`Van jouw supermarkten zijn de ingrediënten samen het goedkoopst bij `+ord.slice(0,3).map(s=>`${N[s]} (${e(D.st[s].t)})`).join(", ").replace(/, ([^,]*)$/," en $1")+"."}
function vragen(off){if(!off.size)return;const c=[...document.querySelectorAll("[data-best]")].filter(x=>x.dataset.bs);if(!c.length)return;
 const nm=x=>(x.querySelector("a")?.textContent||"").trim(),g=c.reduce((a,b)=>+b.dataset.best<+a.dataset.best?b:a);
 const z=`${nm(g)}: ${e(+g.dataset.best)} voor 4 personen bij ${N[g.dataset.bs]}, ${e(g.dataset.best/4)} per persoon (bij jouw supermarkten).`;
 for(const x of document.querySelectorAll("#ofaq1,.tfaqz"))x.textContent=z;
 const o2=document.getElementById("ofaq2");if(o2){const t={};c.forEach(x=>t[x.dataset.bs]=(t[x.dataset.bs]||0)+1);const w=Object.keys(t).sort((a,b)=>t[b]-t[a])[0];
  o2.textContent=`Van jouw supermarkten is ${N[w]} bij ${t[w]} van de ${c.length} maaltijden het goedkoopst. Per gerecht verschilt het, daarom staan bij elke maaltijd de goedkoopste supermarkten.`}}
function koppen(off){vragen(off);const t=[...document.querySelectorAll("[data-best]")].map(x=>+x.dataset.best).filter(v=>v<1e9);const m=t.length?Math.min(...t):null;
 document.querySelectorAll("[data-vanaf]").forEach(x=>{if(m!=null)x.innerHTML="<b>"+e(m)+"</b>"});
 document.querySelectorAll(".mkeus").forEach(x=>{const n=Object.keys(N).filter(s=>!off.has(s)).length;x.hidden=false;x.innerHTML=off.size?`Prijzen bij <b>jouw ${n} supermarkten</b>. <a href="/#mystores">Wijzig je supermarkten</a>`:`Prijzen van alle ${n} supermarkten. <a href="/#mystores">Kies je eigen winkels</a>`})}
function alles(){const off=uit();kaarten(off);koppen(off);const el=document.getElementById("mdata");if(!el)return;const ban=document.getElementById("mkeus");
 if(off.size){maaltijd(off);const D=JSON.parse(el.textContent);faq(D,Object.keys(D.st).filter(s=>!off.has(s)).sort((a,b)=>D.st[a].t-D.st[b].t))}
 else if(ban){ban.hidden=false;ban.innerHTML=`Prijzen van alle ${Object.keys(N).length} supermarkten. <a href="/#mystores">Kies je eigen winkels</a>`}}
document.addEventListener("click",async ev=>{const b=ev.target.closest(".maddkaart");if(!b)return;b.disabled=true;b.textContent="Bezig…";
 try{const t=await (await fetch(`/maaltijden/${b.dataset.m}/`)).text(),d=new DOMParser().parseFromString(t,"text/html"),D=JSON.parse(d.getElementById("mdata").textContent),off=uit();
  const s=Object.keys(D.st).filter(x=>!off.has(x)).sort((a,c)=>D.st[a].t-D.st[c].t)[0];
  if(!s){b.textContent="Niet bij jouw winkels";return}
  let q=[];try{q=JSON.parse(localStorage.getItem("lijst-erbij")||"[]")||[]}catch(x){}
  for(const o of D.st[s].os)if(!q.some(x=>x.u===o.u))q.push(o);localStorage.setItem("lijst-erbij",JSON.stringify(q));
  b.textContent=`✓ Op je lijst (${N[s]})`;b.classList.add("on");window.mark&&mark();document.dispatchEvent(new Event("erbij"));
  try{window.goatcounter&&goatcounter.count({path:"maaltijd/lijst/"+b.dataset.m,title:"Maaltijd op lijst",event:true})}catch(x){}
 }catch(x){b.disabled=false;b.textContent="Probeer opnieuw"}});
const flt={arm:false,gv:false,lv:false,vg:false,eiw:false,hl:false,ks:false},DIER=["kip","rund","varken","vis","vega"];
const dierOk=c=>{const kies=DIER.filter(d=>flt[d]);if(!kies.length)return true;const ds=(c.dataset.dier||"").split(" ").filter(Boolean);return kies.some(d=>d==="vega"?!ds.length:ds.includes(d))};function filter(){let tot=0,eerste=null;document.querySelectorAll(".msoort").forEach(sec=>{let n=0;sec.querySelectorAll("[data-kcal]").forEach(c=>{const h=(flt.arm&&+c.dataset.kcal>550)||(flt.gv&&!c.dataset.gv)||(flt.vg&&!c.dataset.vg)||(flt.eiw&&!c.dataset.eiw)||(flt.lv&&!c.dataset.lv)||(flt.hl&&!c.dataset.hl)||(flt.ks&&!c.dataset.ks)||!dierOk(c);c.hidden=h;if(!h){n++;if(!eerste)eerste=c}});sec.hidden=!n;tot+=n});
 // Laten zien wat er gebeurde: hoeveel maaltijden er over zijn, en naar de eerste schuiven.
 const el=document.getElementById("mfltn"),aan=flt.arm||flt.gv||flt.lv||flt.vg||flt.eiw||flt.hl||flt.ks||DIER.some(d=>flt[d]);if(el){el.hidden=!aan;el.textContent=aan?`${tot} ${tot===1?"maaltijd":"maaltijden"}${flt.arm?" tot 550 kcal per persoon":""}${flt.gv?(flt.arm?" en":"")+" glutenvrij":""}${flt.vg?(flt.arm||flt.gv?" en":"")+" vegan":""}${flt.eiw?(flt.arm||flt.gv||flt.vg?" en":"")+" eiwitrijk":""}${flt.lv?(flt.arm||flt.gv||flt.vg||flt.eiw?" en":"")+" lactosevrij":""}${flt.hl?" · halal":""}${flt.ks?" · koosjer":""}${DIER.some(d=>flt[d])?" · "+DIER.filter(d=>flt[d]).map(d=>({kip:"met gevogelte",rund:"met rundvlees",varken:"met varkensvlees",vis:"met vis",vega:"vegetarisch"})[d]).join(" of "):""}.`:""}
 return aan?eerste:null}
document.querySelectorAll("[data-meerf]").forEach(b=>b.addEventListener("click",()=>{const r=document.querySelector(".mdieet");const o=r.hidden;r.hidden=!o;b.setAttribute("aria-expanded",o);b.textContent=o?"⚙️ Filter verbergen ▴":"⚙️ Filter: vlees, vis, glutenvrij…"}));
document.querySelectorAll("[data-flt]").forEach(b=>b.addEventListener("click",()=>{const k=b.dataset.flt;flt[k]=!flt[k];b.setAttribute("aria-pressed",flt[k]);const e1=filter();
 // De filterbalk blijft bovenaan staan (sticky): naar de balk schuiven, dan staan de knoppen, het aantal en de eerste maaltijd samen in beeld.
 const bk=document.getElementById("mfbalk");if(e1&&bk&&bk.getBoundingClientRect().top>2||e1&&bk&&e1.getBoundingClientRect().top<bk.getBoundingClientRect().bottom)bk.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion:reduce)").matches?"auto":"smooth",block:"start"})}));
alles();document.addEventListener("winkels",alles);window.addEventListener("storage",ev=>{if(ev.key==="winkels-uit")alles()})})()</script>""")
MJS = """<script>document.addEventListener("click",e=>{const b=e.target.closest(".addall");if(!b)return;let q=[];try{q=JSON.parse(localStorage.getItem("lijst-erbij")||"[]")}catch(x){}
const os=JSON.parse(b.dataset.os);for(const o of os)if(!q.some(x=>x.u===o.u))q.push(o);try{localStorage.setItem("lijst-erbij",JSON.stringify(q));b.textContent="✓ Klaar voor je lijst";b.classList.add("on");window.mark&&mark();
try{window.goatcounter&&goatcounter.count({path:"maaltijd/lijst/"+b.dataset.m,title:"Maaltijd op lijst",event:true})}catch(x){}}catch(x){b.textContent="Bewaren lukt niet in deze browser"}});</script>"""

def deelknop(tekst, path):
    """Delen via het deelmenu van de telefoon; anders via WhatsApp."""
    url = f"{BASE}{path}"
    return f'<p class="deel"><a class="btn-line deelknop" href="https://wa.me/?text={quote(tekst + " " + url)}" target="_blank" rel="noopener" data-deel="{esc(json.dumps({"t": tekst, "u": url}, ensure_ascii=False))}">📤 Delen</a></p>'
def wnaam(si): return NAMEN.get(stores[si]["id"], stores[si]["name"])
def mlabels_kort(m):
    """Op kaarten en in lijsten hooguit 3 labels, de belangrijkste eerst; alle labels staan op de receptpagina."""
    l = [x for x in [('<a class="lbl vg" href="/maaltijden/vegan/">🌱 Vegan</a>' if m.get("vegan") else ""),
                     ('<a class="lbl gv" href="/maaltijden/glutenvrij/">🌾 Glutenvrij</a>' if m.get("glutenvrij") else ""),
                     ('<a class="lbl arm" href="/maaltijden/caloriearm/">🥗 Caloriearm</a>' if m["kcal"] <= KCAL_ARM else ""),
                     ('<a class="lbl eiw" href="/maaltijden/eiwitrijk/">💪 Eiwitrijk</a>' if m.get("eiwitrijk") else ""),
                     ('<a class="lbl lv" href="/maaltijden/lactosevrij/">🥛 Lactosevrij</a>' if m.get("lactosevrij") else "")] if x][:3]
    return f'<span class="mlbls">{"".join(l)}</span>' if l else ""
def mlabels(m):
    """Labels bij een maaltijd: glutenvrij en caloriearm (hooguit KCAL_ARM kcal per persoon)."""
    l = ('<a class="lbl gv" href="/maaltijden/glutenvrij/">🌾 Glutenvrij</a>' if m.get("glutenvrij") else "") + \
        ('<a class="lbl arm" href="/maaltijden/caloriearm/">🥗 Caloriearm</a>' if m["kcal"] <= KCAL_ARM else "") + \
        ('<a class="lbl lv" href="/maaltijden/lactosevrij/">🥛 Lactosevrij</a>' if m.get("lactosevrij") else "") + \
        ('<a class="lbl vg" href="/maaltijden/vegan/">🌱 Vegan</a>' if m.get("vegan") else "") + \
        ('<a class="lbl eiw" href="/maaltijden/eiwitrijk/">💪 Eiwitrijk</a>' if m.get("eiwitrijk") else "") + \
        ('<a class="lbl hl" href="/maaltijden/halal/" title="Zonder varkensvlees en alcohol; kies halal vlees">Halal</a>' if m.get("halal") else "") + \
        ('<a class="lbl ks" href="/maaltijden/koosjer/" title="Zonder varkensvlees, geen vlees met zuivel; kies koosjer vlees">Koosjer</a>' if m.get("koosjer") else "")
    return f'<span class="mlbls">{l}</span>' if l else ""
def kaart(m):
    si, r = m["rang"][0]
    return (f'<li class="mcard" data-kcal="{m["kcal"]}"{' data-gv="1"' if m.get("glutenvrij") else ""}{' data-vg="1"' if m.get("vegan") else ""}{' data-eiw="1"' if m.get("eiwitrijk") else ""}{' data-lv="1"' if m.get("lactosevrij") else ""}{' data-hl="1"' if m.get("halal") else ""}{' data-ks="1"' if m.get("koosjer") else ""} data-dier="{" ".join(m.get("dier", []))}" data-p="{esc(prijzen_json(m))}">{kaartbeeld(m)}<a class="mt" href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a>{mlabels_kort(m)}'
            f'<span class="mm">{m["kcal"]} kcal per persoon · {m["tijd"]} min · 4 personen</span>'
            f'<span class="mw"><span class="kp">{tag(r["tot"])}</span><span>bij <b class="kw">{esc(wnaam(si))}</b><br><span class="mm kpp">{pp(r["tot"])} per persoon</span></span></span>'
            + f'<span class="wk mws">{esc(winkelregel(m))}</span>'
            f'<button type="button" class="add maddkaart" data-m="{m["slug"]}">+ Op mijn lijst</button></li>')
def winkelregel(m):
    """Bij welke winkels de maaltijd te koop is, met de prijs voor 4 personen, van goedkoop naar duur."""
    r = m["rang"]
    return f'🏪 Bij {len(r)} winkels: ' + ", ".join(f'{KORT.get(stores[si]["id"], wnaam(si))} {eur(x["tot"])}' for si, x in r)
def prijzen_json(m): return json.dumps({stores[si]["id"]: round(r["tot"], 2) for si, r in m["rang"]}, separators=(",", ":"))

KCAL_ARM = 550  # caloriearm: hoogstens zoveel kcal per persoon
SOORT_PAD = {"aardappel": ("aardappelgerechten", "Aardappelgerechten"), "oven": ("ovenschotels", "Ovenschotels"), "pasta": ("pasta", "Pasta"), "rijst": ("rijst-en-noedels", "Rijst en noedels"), "wereld": ("wereldkeuken", "Wereldkeuken"), "salade": ("salades", "Salades")}
maal_paden = []
for m in MAAL:
    path = f"/maaltijden/{m['slug']}/"
    top3 = m["rang"][:3]
    (s1, r1) = top3[0]; (sN, rN) = m["rang"][-1]
    naam = m["naam"]; kl = naam[0].lower() + naam[1:]
    title = f"{naam}: {eur(r1['tot'])} bij {KORT.get(stores[s1]['id'], wnaam(s1))}"
    desc = (f"{naam} voor 4 personen: {eur(r1['tot'])} bij {wnaam(s1)} ({pp(r1['tot'])} p.p.). {m['kcal']} kcal per persoon. "
            f"Vergelijk {len(m['rang'])} supermarkten, elke dag bijgewerkt.")
    sp = SOORT_PAD.get(m["soort"])
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), *([(sp[1], f"/maaltijden/{sp[0]}/")] if sp else []), (naam, None))
    # top 3
    ingdata = [[g["naam"], hoev(g["q"], "l" if g["sleutel"] in ("halfvolle melk", "kookroom", "mayonaise") else "kg"), 1 if g["voorraad"] else 0, 1 if g["optioneel"] else 0] for g in m["regels"]]
    stdata = {}
    for si, r in m["rang"]:
        stdata[stores[si]["id"]] = {"t": round(r["tot"], 2),
            "g": round(r["gebruik"], 2),
            "c": [[round(k, 2), p[1], plink(p), nn] if p else None for n, k, p, nn, gb in r["regels"]],
            "os": [{"s": stores[si]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": n.lower(), "m": m["slug"], **({"q": nn} if nn > 1 else {})} for n, k, p, nn, gb in r["regels"] if p]
                  + [{"u": "maal:" + m["slug"], "maal": {"slug": m["slug"], "n": naam, "k": m["kcal"], "pp": 4}}]}
    mdata = json.dumps({"slug": m["slug"], "ing": ingdata, "st": stdata}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tops = ""
    for i, (si, r) in enumerate(top3):
        os_ = [{"s": stores[si]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": n.lower(), "m": m["slug"], **({"q": nn} if nn > 1 else {})} for n, k, p, nn, gb in r["regels"] if p] + [{"u": "maal:" + m["slug"], "maal": {"slug": m["slug"], "n": naam, "k": m["kcal"], "pp": 4}}]
        tops += (f'<li class="{"w" if i == 0 else ""}"><span class="rk">{i + 1}e goedkoopst</span><b style="font-size:19px">{esc(wnaam(si))}</b>{tag(r["tot"], "big" if i == 0 else "")}'
                 f'<span class="muted">{pp(r["tot"])} per persoon</span>'
                 f'<button type="button" class="add addall" data-m="{m["slug"]}" data-os="{esc(json.dumps(os_, ensure_ascii=False))}">+ Alles op mijn lijst</button></li>')
    # ingrediënten x top 3
    kop = "".join(f'<th style="text-align:right">{esc(KORT.get(stores[si]["id"], wnaam(si)))}</th>' for si, _ in top3)
    rijen = ""
    for g in m["regels"]:
        r_ = next(x for x in m["ing"] if x[0] == g["sleutel"] and x[2] == g["naam"])
        eh = "l" if I.get(g["sleutel"], ("",))[0] and g["sleutel"] in ("halfvolle melk", "kookroom", "mayonaise") else "kg"
        hv = hoev(g["q"], eh)
        if g["voorraad"]:
            rijen += f'<tr class="vk"><td>{esc(g["naam"])}<span class="sub">uit de voorraadkast, niet meegeteld</span></td>' + '<td class="c">–</td>' * len(top3) + "</tr>"; continue
        cellen = ""
        for si, _ in top3:
            if si in g["prijzen"]:
                k, p, nn, gb = g["prijzen"][si]
                cellen += f'<td class="c"><a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[si]["id"]}" title="{esc(p[1])} {esc(p[4] or "")}">{eur(k)}</a>{f"<span class=sub>{nn} pakken</span>" if nn > 1 else ""}</td>'
            else: cellen += '<td class="c"><span class="muted">niet gevonden</span></td>'
        rijen += f'<tr><td><b>{esc(g["naam"])}</b><span class="sub">{hv}{" · optioneel" if g["optioneel"] else ""}</span></td>{cellen}</tr>'
    rijen += '<tr class="win"><td><b>Totaal voor 4 personen</b></td>' + "".join(f'<td class="c"><b>{eur(r["tot"])}</b></td>' for _, r in top3) + "</tr>"
    alle = "".join(f'<tr{" class=win" if i == 0 else ""}><td><b>{i + 1}. {esc(wnaam(si))}</b></td><td class="p">{tag(r["tot"])}</td><td class="p">{pp(r["tot"])}</td></tr>' for i, (si, r) in enumerate(m["rang"]))
    bnaam, burl = m["bron"]
    noot = NOTITIE.get(m["slug"], "")
    gvnoot = ""
    if m["glutenvrij"]:
        gvnoot = ("<p class=\"note\"><b>Glutenvrij:</b> in dit recept zitten geen ingrediënten met gluten."
                  + (f" Kies wel een glutenvrije variant van: {esc(', '.join(m['gv_let']))}." if m["gv_let"] else "")
                  + " Controleer bij coeliakie altijd het etiket.</p>")
    faq = [(f"Wat kost {kl}?", f"{naam} voor 4 personen kost nu {eur(r1['tot'])} bij {wnaam(s1)}, dat is {pp(r1['tot'])} per persoon. Bij {wnaam(sN)} betaal je {eur(rN['tot'])}."),
           (f"Waar is {kl} het goedkoopst?", f"De ingrediënten zijn samen het goedkoopst bij {wnaam(s1)} ({eur(r1['tot'])}), gevolgd door {wnaam(top3[1][0])} ({eur(top3[1][1]['tot'])}) en {wnaam(top3[2][0])} ({eur(top3[2][1]['tot'])})."),
           (f"Hoeveel calorieën heeft {kl}?", f"Ongeveer {m['kcal']} kcal per persoon, berekend uit de ingrediënten van het recept voor 4 personen."),
           ("Hoe wordt de prijs berekend?", "Per supermarkt zoeken we voor elk ingrediënt de goedkoopste verpakking waar genoeg in zit, en tellen we de prijzen op zoals je ze aan de kassa betaalt. Aanbiedingen die nu lopen tellen mee. We laten ook zien hoeveel daarvan je in het recept gebruikt; de rest houd je over. Olie, zout, kruiden en andere voorraadkastspullen tellen niet mee.")]
    head = (ch + f"<h1>{esc(naam)}: waar is het goedkoopst?</h1>{mlabels(m)}<p class=\"lead\" id=\"mlead\">Alle ingrediënten voor 4 personen: <b>{eur(r1['tot'])}</b> bij <b>{esc(wnaam(s1))}</b>. "
            f"Bij {esc(wnaam(sN))} betaal je {eur(rN['tot'] - r1['tot'])} meer. Je gebruikt er {eur(r1['gebruik'])} van; de rest houd je over.</p>"
            f'<p class="feiten"><span><b>{m["kcal"]}</b> kcal per persoon{" · <a href=/maaltijden/caloriearm/>caloriearm</a>" if m["kcal"] <= KCAL_ARM else ""}{" · <a href=/maaltijden/glutenvrij/>glutenvrij</a>" if m["glutenvrij"] else ""}{" · <a href=/maaltijden/lactosevrij/>lactosevrij</a>" if m.get("lactosevrij") else ""}{" · <a href=/maaltijden/vegan/>vegan</a>" if m.get("vegan") else ""}</span><span><b>{m.get("eiwit", 0)} g</b> eiwit{" · <a href=/maaltijden/eiwitrijk/>eiwitrijk</a>" if m.get("eiwitrijk") else ""}</span><span><b>{m["tijd"]}</b> minuten</span><span><b>4</b> personen</span><span>Recept: <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a></span></p>')
    andere = [x for x in MAAL if x["soort"] == m["soort"] and x is not m] + [x for x in MAAL if x["soort"] != m["soort"]]
    body = (deelknop(f"{naam}: alle ingrediënten voor 4 personen vanaf {eur(r1['tot'])}", f"/maaltijden/{m['slug']}/") + foto_html(m) + f'<p class="note" id="mkeus" hidden></p><h2 id="mtoph">De 3 goedkoopste supermarkten</h2><ul class="mtop" id="mtop">{tops}</ul>'
            f'<h2>Wat heb je nodig?</h2><div class="tblwrap"><table class="ptable" id="mtab"><thead><tr><th>Ingrediënt</th>{kop}</tr></thead><tbody>{rijen}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM} voor hele verpakkingen, zoals je ze aan de kassa betaalt en zoals ze op je lijst komen. Per supermarkt kiezen we de goedkoopste verpakking waar genoeg in zit. Tik op een prijs voor het product. {esc(noot)}</p>'
            + gvnoot + f'<h2>Bereiding</h2><p>De bereiding staat in het originele recept op <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a>. Daar vind je ook de stappen en tips.</p>'
            f'<h2>Alle supermarkten</h2><div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">4 personen</th><th style="text-align:right">Per persoon</th></tr></thead><tbody id="malle">{alle}</tbody></table></div>'
            f'<p class="note">Supermarkten waar we een ingrediënt niet online vinden, staan niet in de lijst.</p>'
            + faq_html(faq).replace(f"<p>{esc(faq[0][1])}</p>", f'<p id="mfaq1">{esc(faq[0][1])}</p>').replace(f"<p>{esc(faq[1][1])}</p>", f'<p id="mfaq2">{esc(faq[1][1])}</p>') + '<h2>Meer complete maaltijden</h2><ul class="mgrid">' + "".join(kaart(x) for x in andere[:6]) + '</ul><a class="cta" href="/maaltijden/">Alle complete maaltijden</a>' + MJS
            + f'<script type="application/json" id="mdata">{mdata}</script>' + MKJS)
    ing_lijst = [f'{hoev(x[1], "l" if x[0] in ("halfvolle melk", "kookroom", "mayonaise") else "kg")} {x[2].lower()}' for x in m["ing"]]
    recipe = {"@context": "https://schema.org", "@type": "Recipe", "name": naam, "description": desc, "recipeYield": "4 personen", "totalTime": f"PT{m['tijd']}M",
              "recipeCategory": "Hoofdgerecht", "recipeCuisine": "Nederlands", "inLanguage": "nl-NL", "recipeIngredient": ing_lijst,
              "nutrition": {"@type": "NutritionInformation", "calories": f"{m['kcal']} kcal", "servingSize": "1 persoon"},
              "isBasedOn": burl, "author": {"@type": "Organization", "name": bnaam},
              "image": beeld_objecten(m),
              "datePublished": "2026-10-19", "dateModified": VANDAAG,
              **({"suitableForDiet": [d for d, ok in (("https://schema.org/GlutenFreeDiet", m["glutenvrij"]), ("https://schema.org/LowCalorieDiet", m["kcal"] <= KCAL_ARM)) if ok]}
                 if (m["glutenvrij"] or m["kcal"] <= KCAL_ARM) else {}),
              "publisher": {"@type": "Organization", "name": "Goedkope Boodschappen", "url": BASE + "/"},
              "keywords": f"{kl}, goedkoop, prijs, {', '.join(wnaam(si) for si, _ in top3)}",
              "offers": {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": f"{r1['tot']:.2f}", "highPrice": f"{rN['tot']:.2f}", "offerCount": len(m["rang"])}}
    recipe.pop("offers")  # Recipe ondersteunt geen offers; prijs staat in de tekst en de FAQ.
    schrijf(path, page(path, title, desc, head, body, [cld, recipe, faq_ld(faq)], actief="/maaltijden/", extra_css=MCSS, og_title=f"{naam}: {eur(r1['tot'])} bij {wnaam(s1)}", og_img=beelden(m)[0].replace(BASE, "")))
    made.append((path, "0.8")); maal_paden.append(path); MAAL_BEELDEN[path] = beelden(m)[:1]

# ---------- overzicht ----------
if MAAL:
    goedkoopst = min(MAAL, key=lambda m: m["rang"][0][1]["tot"])
    winst = {}
    for m in MAAL: winst[m["rang"][0][0]] = winst.get(m["rang"][0][0], 0) + 1
    vaakst = max(winst, key=winst.get)
    secties = ""
    for key, titel, emo in SOORTEN:
        ms = sorted([m for m in MAAL if m["soort"] == key], key=lambda m: m["rang"][0][1]["tot"])
        if not ms: continue
        sp = SOORT_PAD.get(key)
        kop_ = f'<a href="/maaltijden/{sp[0]}/" style="text-decoration:none">{esc(titel)}</a>' if sp else esc(titel)
        secties += f'<section class="msoort" id="{key}"><h2>{emo} {kop_}</h2><ul class="mgrid">' + "".join(kaart(m) for m in ms) + "</ul></section>"
    sprong = " · ".join(f'<a href="#{k}">{esc(t)}</a>' for k, t, _ in SOORTEN if any(m["soort"] == k for m in MAAL))
    faq = [("Wat is de goedkoopste maaltijd?", f"Van de {len(MAAL)} maaltijden is {goedkoopst['naam'].lower()} het goedkoopst: {eur(goedkoopst['rang'][0][1]['tot'])} voor 4 personen bij {wnaam(goedkoopst['rang'][0][0])}, {pp(goedkoopst['rang'][0][1]['tot'])} per persoon."),
           ("Bij welke supermarkt kook je het goedkoopst?", f"{wnaam(vaakst)} is bij {winst[vaakst]} van de {len(MAAL)} maaltijden het goedkoopst. Per gerecht verschilt het, daarom staan bij elke maaltijd de 3 goedkoopste supermarkten."),
           ("Waar komen de recepten vandaan?", "Het zijn gangbare Nederlandse gerechten van bekende receptensites: Allerhande, Jumbo, Leukerecepten, 24Kitchen, Lekker en Simpel en Eef kookt zo. Bij elk gerecht staat een link naar het originele recept."),
           ("Hoe worden de calorieën berekend?", "Uit de ingrediënten van het recept, met de gemiddelde voedingswaarde per 100 gram uit de Nederlandse voedingsmiddelentabel. Het is een schatting per persoon bij 4 personen.")]
    ch, cld = crumbs(("Complete maaltijden", None))
    title = f"Complete maaltijden: {len(MAAL)} gerechten met prijs per supermarkt"
    desc = (f"Wat kost stamppot, spaghetti of nasi voor 4 personen? {len(MAAL)} gewone gerechten met calorieën en de goedkoopste supermarkt, "
            f"vanaf {eur(goedkoopst['rang'][0][1]['tot'])}. Elke dag bijgewerkt.")
    head = (ch + f"<h1>Complete maaltijden: waar kook je het goedkoopst?</h1><p class=\"lead\">{len(MAAL)} avondmaaltijden voor 4 personen. Per gerecht zie je de goedkoopste supermarkt. "
            f"Al vanaf <span data-vanaf><b>{eur(goedkoopst['rang'][0][1]['tot'])}</b></span>.</p><p class=\"note mkeus\" hidden></p>"
            '<div class="wmblok dierblok"><p><b>🍽️ Kies wat je wilt eten</b><br><span>Per soort vlees of vis.</span></p><div class="chips wmkeus"><a class="chip" href="/maaltijden/met-vis/">🐟 Vis</a><a class="chip" href="/maaltijden/met-gevogelte/">🍗 Gevogelte</a><a class="chip" href="/maaltijden/met-rundvlees/">🥩 Rundvlees</a><a class="chip" href="/maaltijden/met-varkensvlees/">🥓 Varkensvlees</a><a class="chip" href="/maaltijden/vegetarisch/">🥕 Vegetarisch</a><a class="chip" href="/maaltijden/vegan/">🌱 Vegan</a></div></div>'
            '<div class="wmblok"><p><b>📅 Weekmenu met boodschappenlijst</b><br><span>5 avondmaaltijden, in één keer ingekocht.</span></p><div class="chips wmkeus"><a class="chip" href="/maaltijden/weekmenu/">💶 Goedkoop</a><a class="chip" href="/maaltijden/weekmenu-glutenvrij/">🌾 Glutenvrij</a><a class="chip" href="/maaltijden/weekmenu-vegan/">🌱 Vegan</a><a class="chip" href="/maaltijden/weekmenu/#meer">Meer…</a></div></div>'
            f'<div class="mfbalk" id="mfbalk"><p class="mfilters"><button type="button" class="btn btn-line meerf" aria-expanded="false" data-meerf>⚙️ Filter: vlees, vis, glutenvrij…</button></p><p class="mfilters mdier mdieet" hidden><button type="button" class="btn btn-line" data-flt="kip" aria-pressed="false">🍗 Gevogelte</button> <button type="button" class="btn btn-line" data-flt="rund" aria-pressed="false">🥩 Rund</button> <button type="button" class="btn btn-line" data-flt="varken" aria-pressed="false">🥓 Varken</button> <button type="button" class="btn btn-line" data-flt="vis" aria-pressed="false">🐟 Vis</button> <button type="button" class="btn btn-line" data-flt="vega" aria-pressed="false">🥕 Vegetarisch</button> <button type="button" class="btn btn-line" data-flt="arm" aria-pressed="false">Caloriearm (tot {KCAL_ARM} kcal)</button> <button type="button" class="btn btn-line" data-flt="gv" aria-pressed="false">Glutenvrij</button> <button type="button" class="btn btn-line" data-flt="lv" aria-pressed="false">Lactosevrij</button> <button type="button" class="btn btn-line" data-flt="vg" aria-pressed="false">Vegan</button> <button type="button" class="btn btn-line" data-flt="eiw" aria-pressed="false">Eiwitrijk</button> <button type="button" class="btn btn-line" data-flt="hl" aria-pressed="false">Halal</button> <button type="button" class="btn btn-line" data-flt="ks" aria-pressed="false">Koosjer</button></p><p class="meta mfltn" id="mfltn" aria-live="polite" hidden></p></div>')
    themalinks = ('<h2>Meer overzichten</h2><ul class="links"><li><a href="/maaltijden/weekmenu/">📅 Goedkoop weekmenu met boodschappenlijst</a></li><li><a href="/maaltijden/goedkoop-avondeten/">De 10 goedkoopste maaltijden</a></li><li><a href="/maaltijden/caloriearm/">Caloriearme maaltijden</a></li><li><a href="/maaltijden/glutenvrij/">Glutenvrije maaltijden</a></li><li><a href="/maaltijden/lactosevrij/">🥛 Lactosevrije maaltijden</a></li><li><a href="/maaltijden/vegan/">🌱 Vegan maaltijden</a></li><li><a href="/maaltijden/eiwitrijk/">💪 Eiwitrijke maaltijden</a></li><li><a href="/maaltijden/halal/">Halal maaltijden</a></li><li><a href="/maaltijden/koosjer/">Koosjere maaltijden</a></li><li><a href="/maaltijden/met-gevogelte/">🍗 Met gevogelte</a></li><li><a href="/maaltijden/met-rundvlees/">🥩 Met rundvlees</a></li><li><a href="/maaltijden/met-varkensvlees/">🥓 Met varkensvlees</a></li><li><a href="/maaltijden/met-vis/">🐟 Met vis</a></li><li><a href="/maaltijden/vegetarisch/">🥕 Vegetarisch</a></li><li><a href="/maaltijden/stamppot/">Goedkope stamppotten</a></li>'
                  + "".join(f'<li><a href="/maaltijden/{v[0]}/">{esc(v[1])}</a></li>' for v in SOORT_PAD.values()) + '<li><a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a></li><li><a href="/aanbiedingen/">Aanbiedingen van deze week</a></li></ul>')
    body = (secties + themalinks + f'<p class="note" style="margin-top:20px">Prijzen van {DATUM} voor hele verpakkingen, zoals aan de kassa, aanbiedingen inbegrepen. Olie, zout en kruiden uit de voorraadkast tellen niet mee.</p>' + faq_html(faq) + MKJS)
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": "Complete maaltijden met prijs per supermarkt",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/maaltijden/{m['slug']}/", "name": m["naam"]} for i, m in enumerate(MAAL)]}
    body = body.replace(f"<p>{esc(faq[0][1])}</p>", f'<p id="ofaq1">{esc(faq[0][1])}</p>').replace(f"<p>{esc(faq[1][1])}</p>", f'<p id="ofaq2">{esc(faq[1][1])}</p>')
    schrijf("/maaltijden/", page("/maaltijden/", title, desc, head, body, [cld, il, faq_ld(faq)], actief="/maaltijden/", extra_css=MCSS, og_title="Complete maaltijden: waar kook je het goedkoopst?"))
    made.append(("/maaltijden/", "0.9"))
    # Blok voor de startpagina: de 6 goedkoopste, verdeeld over de soorten.
    keuze = []
    for key, _, _ in SOORTEN:
        ms = sorted([m for m in MAAL if m["soort"] == key], key=lambda m: m["rang"][0][1]["tot"])
        keuze += ms[:2]
    keuze = sorted(keuze, key=lambda m: m["rang"][0][1]["tot"])[:6]
    MAAL_HOME = (f'<section class="wrap maal" aria-labelledby="mh"><h2 id="mh">🍽️ Complete maaltijden</h2>'
                 f'<p class="meta">Wat kost avondeten voor 4 personen? Gewone gerechten met calorieën en de goedkoopste supermarkt.</p><p class="note mkeus" hidden></p><ul class="mgrid">'
                 + "".join(kaart(m) for m in keuze) + f'</ul><a class="cta" href="/maaltijden/">Alle {len(MAAL)} maaltijden: aardappel, pasta, rijst, salades en meer</a></section>' + MKJS)
else:
    MAAL_HOME = ""

# ---------- themapagina's ----------
def zicht_lead(lead):
    """Korte zichtbare intro: eerste zin zonder bijzinnen + 'Al vanaf ...'. De lange tekst blijft de meta-omschrijving voor Google."""
    m = re.search(r'<span data-vanaf>.*?</span>', lead)
    eerste = re.split(r'(?<=[.?])\s', lead, maxsplit=1)[0]
    if "data-vanaf" in eerste: return lead
    eerste = re.split(r': |, met |, handig |, van \d', eerste)[0].rstrip(".") + "."
    if eerste.startswith("Wat kost"): eerste = re.split(r'(?<=[.?])\s', lead)[1].split(" met de ")[0] + "."
    return eerste + ((f" Al vanaf {m.group(0)}." if "4 personen" in eerste else f" Al vanaf {m.group(0)} voor 4 personen.") if m else "")
def themapagina(slug_, kort, h1, title, lead, ms, faq_extra=()):
    path = f"/maaltijden/{slug_}/"
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), (kort, None))
    trs = "".join(f'<tr{" class=win" if i == 0 else ""} data-p="{esc(prijzen_json(m))}"><td><b><span class="rn">{i + 1}.</span> <a href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a></b><span class="sub">{m["kcal"]} kcal per persoon · {m["tijd"]} min</span><button type="button" class="add maddkaart" data-m="{m["slug"]}" style="margin-top:8px">+ Op mijn lijst</button></td>'
                  f'<td class="p"><span class="kp">{tag(m["rang"][0][1]["tot"])}</span><br><span class="unit">bij <b class="kw">{esc(wnaam(m["rang"][0][0]))}</b></span><br><span class="unit kpp" data-kort="1">{pp(m["rang"][0][1]["tot"])} p.p.</span></td></tr>' for i, m in enumerate(ms))
    g = ms[0]
    faq = [(f"Wat is de goedkoopste uit deze lijst?", f"{g['naam']}: {eur(g['rang'][0][1]['tot'])} voor 4 personen bij {wnaam(g['rang'][0][0])}, {pp(g['rang'][0][1]['tot'])} per persoon."), *faq_extra,
           ("Hoe actueel zijn de prijzen?", f"De prijzen worden elke dag bijgewerkt met de prijzen en aanbiedingen van de supermarkten. Deze pagina is van {DATUM}.")]
    andere = [(f"/maaltijden/{x}/", t) for x, t in [("weekmenu-glutenvrij" if slug_ == "glutenvrij" else "weekmenu-caloriearm" if slug_ == "caloriearm" else "weekmenu-vegan" if slug_ == "vegan" else "weekmenu-eiwitrijk" if slug_ == "eiwitrijk" else "weekmenu-lactosevrij" if slug_ == "lactosevrij" else "weekmenu-halal" if slug_ == "halal" else "weekmenu-koosjer" if slug_ == "koosjer" else "weekmenu", "📅 Glutenvrij weekmenu met boodschappenlijst" if slug_ == "glutenvrij" else "📅 Caloriearm weekmenu met boodschappenlijst" if slug_ == "caloriearm" else "📅 Vegan weekmenu met boodschappenlijst" if slug_ == "vegan" else "📅 Eiwitrijk weekmenu met boodschappenlijst" if slug_ == "eiwitrijk" else "📅 Lactosevrij weekmenu met boodschappenlijst" if slug_ == "lactosevrij" else "📅 Halal weekmenu met boodschappenlijst" if slug_ == "halal" else "📅 Koosjer weekmenu met boodschappenlijst" if slug_ == "koosjer" else "📅 Goedkoop weekmenu met boodschappenlijst"), ("goedkoop-avondeten", "De 10 goedkoopste maaltijden"), ("caloriearm", "Caloriearme maaltijden"), ("glutenvrij", "Glutenvrije maaltijden"), ("lactosevrij", "🥛 Lactosevrije maaltijden"), ("vegan", "🌱 Vegan maaltijden"), ("eiwitrijk", "💪 Eiwitrijke maaltijden"), ("halal", "Halal maaltijden"), ("koosjer", "Koosjere maaltijden"), ("met-gevogelte", "🍗 Met gevogelte"), ("met-rundvlees", "🥩 Met rundvlees"), ("met-varkensvlees", "🥓 Met varkensvlees"), ("met-vis", "🐟 Met vis"), ("vegetarisch", "🥕 Vegetarisch"), ("stamppot", "Goedkope stamppotten"), *SOORT_PAD.values()] if x != slug_]
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Maaltijd (4 personen)</th><th style="text-align:right">Goedkoopst</th></tr></thead><tbody data-sorteer="1">{trs}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM} voor alle ingrediënten in hele verpakkingen, zoals aan de kassa. Tik op een maaltijd voor de 3 goedkoopste supermarkten en wat elk ingrediënt kost.</p>'
            + re.sub(r'<p>((?:Nu is |[^<]*: )[^<]*? bij [^<]*?)</p>', r'<p class="tfaqz">\1</p>', faq_html(faq), count=2) + '<h2>Meer overzichten</h2><ul class="links">' + "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in andere) + '<li><a href="/maaltijden/">Alle complete maaltijden</a></li></ul>' + MKJS)
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/maaltijden/{m['slug']}/", "name": m["naam"]} for i, m in enumerate(ms)]}
    d_ = lead_txt(lead); d_ = d_ if len(d_) <= 158 else d_[:d_.rfind(" ", 0, 150)] + "…"
    schrijf(path, page(path, title, d_, crumbs_head(ch, h1, zicht_lead(lead)), body, [cld, il, faq_ld(faq)], actief="/maaltijden/", og_title=h1))
    made.append((path, "0.8"))
def lead_txt(h): return re.sub(r"<[^>]+>", "", h)
def crumbs_head(ch, h1, lead): return ch + f"<h1>{esc(h1)}</h1><p class=\"lead\">{lead}</p><p class=\"note mkeus\" hidden></p>"
pprs = lambda m: m["rang"][0][1]["tot"]
if MAAL:
    alle = sorted(MAAL, key=pprs)
    top = alle[:10]
    themapagina("goedkoop-avondeten", "Goedkoop avondeten", "Goedkoop avondeten: de 10 goedkoopste maaltijden",
                f"Goedkoop avondeten: de 10 goedkoopste maaltijden ({MAAND})",
                f"De 10 goedkoopste gewone avondmaaltijden van dit moment, voor 4 personen. Al vanaf <span data-vanaf><b>{eur(pprs(top[0]))}</b></span>, met de supermarkt waar je het minst betaalt.", top,
                [("Hoe kook je goedkoop?", "Kies gerechten met aardappelen, rijst, pasta of peulvruchten als basis, koop groente van het seizoen en let op de aanbiedingen. Rekenen met de prijs per kilo helpt: grote verpakkingen en huismerken zijn vaak het voordeligst.")])
    arm = sorted([m for m in MAAL if m["kcal"] <= KCAL_ARM], key=lambda m: m["kcal"])
    if len(arm) >= 3:
        themapagina("caloriearm", "Caloriearm", "Caloriearme maaltijden: lekker eten onder de 550 kcal",
                    f"Caloriearme maaltijden onder {KCAL_ARM} kcal, met prijs per winkel",
                    f"{len(arm)} gewone avondmaaltijden met hoogstens {KCAL_ARM} kcal per persoon, van {arm[0]['kcal']} tot {arm[-1]['kcal']} kcal. Met de supermarkt waar je ze het goedkoopst kookt, al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in arm))}</b></span> voor 4 personen.",
                    sorted(arm, key=pprs),
                    [("Hoeveel calorieën heeft een caloriearme maaltijd?", f"Wij noemen een avondmaaltijd caloriearm bij hoogstens {KCAL_ARM} kcal per persoon. Voor de meeste volwassenen is dat ongeveer een kwart van wat je op een dag nodig hebt. De calorieën zijn berekend uit de ingrediënten van het recept."),
                     ("Welke maaltijd heeft de minste calorieën?", f"{arm[0]['naam']}, met ongeveer {arm[0]['kcal']} kcal per persoon.")])
    gvm = [m for m in MAAL if m["glutenvrij"]]
    if len(gvm) >= 3:
        themapagina("glutenvrij", "Glutenvrij", "Glutenvrije maaltijden: zonder tarwe, met prijs per supermarkt",
                    f"Glutenvrije maaltijden: {len(gvm)} recepten met prijs per supermarkt",
                    f"{len(gvm)} gewone avondmaaltijden zonder ingrediënten met gluten: met aardappel, rijst of groente in plaats van pasta, brood of bloem. Met de supermarkt waar je ze het goedkoopst kookt, al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in gvm))}</b></span> voor 4 personen.",
                    sorted(gvm, key=pprs),
                    [("Zijn deze maaltijden echt glutenvrij?", "In de recepten zitten geen ingrediënten met gluten, zoals pasta, brood, bloem, mie, paneermeel of sojasaus. Bij sommige producten, zoals bouillon, rookworst en kruidenmixen, zit soms wel tarwe; kies daarvan een glutenvrije variant. Bij elke maaltijd staat waar je op moet letten. Controleer bij coeliakie altijd het etiket."),
                     ("Wat is de goedkoopste glutenvrije maaltijd?", f"{min(gvm, key=pprs)['naam']}: {eur(pprs(min(gvm, key=pprs)))} voor 4 personen.")])
    vgm = [m for m in MAAL if m.get("vegan")]
    if len(vgm) >= 3:
        themapagina("vegan", "Vegan", "Vegan maaltijden: helemaal plantaardig, met prijs per supermarkt",
                    f"Vegan maaltijden: {len(vgm)} recepten met prijs per supermarkt",
                    f"{len(vgm)} complete avondmaaltijden zonder vlees, vis, zuivel en ei: van vegan stamppot en linzenbolognese tot curry en noedels. Met de supermarkt waar je ze het goedkoopst kookt, al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in vgm))}</b></span> voor 4 personen.",
                    sorted(vgm, key=pprs),
                    [("Zijn deze maaltijden echt vegan?", "In de recepten zitten geen vlees, vis, melk, kaas, eieren of honing. Bij vleesvervangers, bouillon, currypasta en noedels zit soms toch ei, melk of vis; kies een product met vegan op het etiket."),
                     ("Wat is de goedkoopste vegan maaltijd?", f"{min(vgm, key=pprs)['naam']}: {eur(pprs(min(vgm, key=pprs)))} voor 4 personen."),
                     ("Waar vind ik vegan producten?", "Op onze pagina vegan boodschappen staan plantaardige melk, vegan kaas, vleesvervangers en tofu per soort, met de goedkoopste supermarkt.")])
    lvm = [m for m in MAAL if m.get("lactosevrij")]
    if len(lvm) >= 3:
        themapagina("lactosevrij", "Lactosevrij", "Lactosevrije maaltijden: zonder melk, kaas en room",
                    f"Lactosevrije maaltijden: {len(lvm)} recepten met prijs per supermarkt",
                    f"{len(lvm)} gewone avondmaaltijden zonder melk, room, boter, kaas of yoghurt. Met de supermarkt waar je ze het goedkoopst kookt, al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in lvm))}</b></span> voor 4 personen.",
                    sorted(lvm, key=pprs),
                    [("Zijn deze maaltijden echt lactosevrij?", "In de recepten zitten geen zuivelproducten zoals melk, room, boter, kaas of yoghurt. Bij kant-en-klare producten zoals worst, bouillon of sauzen zit soms melkpoeder; kijk bij een allergie altijd op het etiket. Optionele zuivel (zoals een scheutje room) laat je gewoon weg."),
                     ("Wat is de goedkoopste lactosevrije maaltijd?", f"{min(lvm, key=pprs)['naam']}: {eur(pprs(min(lvm, key=pprs)))} voor 4 personen."),
                     ("Waar vind ik lactosevrije producten?", "Op onze pagina lactosevrij staan lactosevrije melk, yoghurt, kaas en plantaardige alternatieven per soort, met de goedkoopste supermarkt.")])
    hlm = [m for m in MAAL if m.get("halal")]
    if len(hlm) >= 3:
        themapagina("halal", "Halal", "Halal maaltijden: zonder varkensvlees en alcohol",
                    f"Halal maaltijden: {len(hlm)} recepten met prijs per supermarkt",
                    f"{len(hlm)} gewone avondmaaltijden zonder varkensvlees en zonder alcohol. Kies voor vlees en kip een halal product; dat is bij steeds meer supermarkten te koop. Al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in hlm))}</b></span> voor 4 personen.",
                    sorted(hlm, key=pprs),
                    [("Zijn deze maaltijden halal?", "In de recepten zit geen varkensvlees (ook geen spek, ham of rookworst) en geen alcohol. Vlees en kip moeten halal geslacht zijn: kies daarvoor een product met een halal-keurmerk, zoals Wahid of het halal-vlees van de supermarkt. Let ook op bouillon, gelatine en kant-en-klare sauzen."),
                     ("Waar koop je halal vlees in de supermarkt?", "Halal kip, gehakt en vleeswaren vind je onder andere bij Albert Heijn, Jumbo, Lidl, Dirk en PLUS. Op onze pagina halal boodschappen staan ze naast elkaar met de prijs."),
                     ("Wat is de goedkoopste halal maaltijd?", f"{min(hlm, key=pprs)['naam']}: {eur(pprs(min(hlm, key=pprs)))} voor 4 personen.")])
    ksm = [m for m in MAAL if m.get("koosjer")]
    if len(ksm) >= 3:
        themapagina("koosjer", "Koosjer", "Koosjer koken: maaltijden zonder varkensvlees en zonder vlees met zuivel",
                    f"Koosjere maaltijden: {len(ksm)} recepten met prijs per supermarkt",
                    f"{len(ksm)} gewone avondmaaltijden zonder varkensvlees, zonder schaaldieren en zonder vlees samen met zuivel. Kies voor vlees en kip een koosjer product met hechsjer. Al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in ksm))}</b></span> voor 4 personen.",
                    sorted(ksm, key=pprs),
                    [("Zijn deze maaltijden koosjer?", "De recepten volgen de basisregels: geen varkensvlees of schaaldieren, en vlees en zuivel niet samen. Of een maaltijd echt koosjer is, hangt ook af van de producten: vlees moet koosjer geslacht zijn en veel producten hebben een hechsjer (keurmerk) nodig. Gewone supermarkten zetten dat zelden online; kijk op de verpakking of koop vlees bij een koosjere slager."),
                     ("Wat is de goedkoopste koosjere maaltijd?", f"{min(ksm, key=pprs)['naam']}: {eur(pprs(min(ksm, key=pprs)))} voor 4 personen.")])
    eim = [m for m in MAAL if m.get("eiwitrijk")]
    if len(eim) >= 3:
        themapagina("eiwitrijk", "Eiwitrijk", "Eiwitrijke maaltijden: minstens 30 gram eiwit per persoon",
                    f"Eiwitrijke maaltijden: {len(eim)} recepten met prijs per supermarkt",
                    f"{len(eim)} gewone avondmaaltijden met minstens 30 gram eiwit per persoon, handig als je sport of spieren wilt opbouwen. Met de supermarkt waar je ze het goedkoopst kookt, al vanaf <span data-vanaf><b>{eur(min(pprs(m) for m in eim))}</b></span> voor 4 personen.",
                    sorted(eim, key=pprs),
                    [("Wanneer is een maaltijd eiwitrijk?", "Wij noemen een avondmaaltijd eiwitrijk bij minstens 30 gram eiwit per persoon, waarbij ook minstens een vijfde van de calorieën uit eiwit komt. Het eiwit is berekend uit de ingrediënten van het recept, met gemiddelde voedingswaarden."),
                     ("Welke maaltijd heeft het meeste eiwit?", f"{max(eim, key=lambda m: m['eiwit'])['naam']}, met ongeveer {max(eim, key=lambda m: m['eiwit'])['eiwit']} gram eiwit per persoon."),
                     ("Wat is de goedkoopste eiwitrijke maaltijd?", f"{min(eim, key=pprs)['naam']}: {eur(pprs(min(eim, key=pprs)))} voor 4 personen.")])
    for _dk, _sl, _kort, _h1, _uitleg in [("kip", "met-gevogelte", "Met gevogelte", "Maaltijden met gevogelte: kip en kalkoen", "met gevogelte, zoals kip of kalkoen"),
                                          ("rund", "met-rundvlees", "Met rundvlees", "Maaltijden met rundvlees", "met rundvlees, zoals gehakt, biefstuk of stoofvlees"),
                                          ("varken", "met-varkensvlees", "Met varkensvlees", "Maaltijden met varkensvlees", "met varkensvlees, zoals spekjes, ham, rookworst of half-om-half gehakt"),
                                          ("vis", "met-vis", "Met vis", "Maaltijden met vis", "met vis, zoals zalm, kabeljauw of tonijn"),
                                          ("", "vegetarisch", "Vegetarisch", "Vegetarische maaltijden", "zonder vlees en vis")]:
        _ms = sorted([m for m in MAAL if (_dk in m.get("dier", []) if _dk else not m.get("dier"))], key=pprs)
        if len(_ms) < 3: continue
        themapagina(_sl, _kort, f"{_h1}: goedkoop koken per supermarkt", f"{_h1}: {len(_ms)} recepten met prijs per supermarkt",
                    f"{len(_ms)} gewone avondmaaltijden {_uitleg}, met calorieën en de supermarkt waar je het minst betaalt. Al vanaf <span data-vanaf><b>{eur(pprs(_ms[0]))}</b></span> voor 4 personen.", _ms)
    st = sorted([m for m in MAAL if any(w in m["slug"] for w in ("stamppot", "hutspot", "boerenkool"))], key=pprs)
    if len(st) >= 2:
        themapagina("stamppot", "Stamppot", "Goedkope stamppot: wat kost het per supermarkt?", f"Goedkope stamppot: prijs per supermarkt ({MAAND})",
                    f"Wat kost een stamppot voor 4 personen? {len(st)} Hollandse stamppotten met de supermarkt waar alle ingrediënten samen het goedkoopst zijn. Vanaf <span data-vanaf><b>{eur(pprs(st[0]))}</b></span>.", st,
                    [("Welke stamppot is het goedkoopst?", f"Nu is {st[0]['naam'].lower()} het goedkoopst: {eur(pprs(st[0]))} voor 4 personen bij {wnaam(st[0]['rang'][0][0])}.")])
    for key, (sl_, kort) in SOORT_PAD.items():
        ms = sorted([m for m in MAAL if m["soort"] == key], key=pprs)
        if len(ms) < 2: continue
        themapagina(sl_, kort, f"{kort}: goedkope maaltijden per supermarkt", f"Goedkope {kort.lower()}: prijs per supermarkt ({MAAND})",
                    f"{len(ms)} gewone {kort.lower()} voor 4 personen, met calorieën en de supermarkt waar je het minst betaalt. Vanaf <span data-vanaf><b>{eur(pprs(ms[0]))}</b></span> voor het hele gerecht.", ms)
# ---------- Weekmenu: 5 goedkope avondmaaltijden, samen ingekocht ----------
from maaltijd_kosten import ingredient_prijzen as _ingprijs
WM_GEBRUIKT = set()
def _weekmenu_kies(pool, vermijd=frozenset()):
    gekozen, gezien = [], set()
    for soort in ("aardappel", "pasta", "rijst", "oven", "wereld", "soep", "salade"):
        if len(gekozen) == 5: break
        c = sorted([m for m in pool if m["soort"] == soort and m["slug"] not in gezien], key=pprs)
        c = [m for m in c if m["slug"] not in vermijd] or c  # liefst iets anders dan in het goedkope weekmenu
        if c: gekozen.append(c[0]); gezien.add(c[0]["slug"])
    for m in sorted(pool, key=pprs):
        if len(gekozen) == 5: break
        if m["slug"] not in gezien: gekozen.append(m); gezien.add(m["slug"])
    return gekozen
def _weekmenu_samen(ms):
    """Alle ingrediënten van de 5 maaltijden bij elkaar opgeteld en per winkel als hele verpakkingen ingekocht."""
    som, namen = {}, {}
    for m in ms:
        schaal = 4 / m.get("porties", 4)
        for r in m["ing"]:
            extra = r[3] if len(r) > 3 else ""
            if extra in ("v", "o"): continue
            som[r[0]] = som.get(r[0], 0) + r[1] * schaal
            namen.setdefault(r[0], r[2].split(" (")[0])
    prijzen = {k: _ingprijs(k, q) for k, q in som.items()}
    uit = []
    for si, st_ in enumerate(stores):
        if not st_.get("count") or not all(si in prijzen[k] for k in som): continue
        regels = [(namen[k], som[k], *prijzen[k][si]) for k in som]
        uit.append((si, sum(r[2] for r in regels), regels))
    return sorted(uit, key=lambda x: x[1]), som
WEEKMENU_PRIJS = {}
def weekmenu(slug_, kort, h1, lead_extra, pool):
    ms = _weekmenu_kies(pool, frozenset(WM_GEBRUIKT) if slug_ != "weekmenu" else frozenset())
    if slug_ == "weekmenu": WM_GEBRUIKT.update(m["slug"] for m in ms)
    if len(ms) < 5: return
    rang, som = _weekmenu_samen(ms)
    # Lukt het niet om alles bij minstens 3 winkels samen te kopen? Dan het gerecht met de minste winkels vervangen.
    weg = set()
    while len(rang) < 3 and len(weg) < 12:
        slechtst = min(ms, key=lambda m: len(m["rang"])); weg.add(slechtst["slug"])
        rest = [m for m in pool if m["slug"] not in weg]
        ms = _weekmenu_kies(rest, frozenset(WM_GEBRUIKT) if slug_ != "weekmenu" else frozenset())
        if len(ms) < 5: return
        rang, som = _weekmenu_samen(ms)
    if len(rang) < 3: return
    path = f"/maaltijden/{slug_}/"
    si0, tot0, regels0 = rang[0]
    los = sum(pprs(m) for m in ms)
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), (kort, None))
    kcal_gem = round(sum(m["kcal"] for m in ms) / 5 / 5) * 5
    lead = (f"5 avondmaaltijden voor 4 personen, maandag tot en met vrijdag. Samen <b>{eur(tot0)}</b> bij <b>{esc(wnaam(si0))}</b>, "
            f"{pp(tot0 / 5)} per persoon per maaltijd. {lead_extra}")
    dagen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"]
    menu = "".join(f'<li><span class="rk">{d}</span> <a href="/maaltijden/{m["slug"]}/"><b>{esc(m["naam"])}</b></a>{mlabels_kort(m)}<span class="sub">{m["kcal"]} kcal p.p. · {m["tijd"]} min · los vanaf {eur(pprs(m))}</span></li>' for d, m in zip(dagen, ms))
    def os_van(si, regels):
        return ([{"s": stores[si]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": n.lower(), "m": slug_, **({"q": nn} if nn > 1 else {})} for n, q, k, p, nn, gb in regels]
                + [{"u": "maal:" + m["slug"], "maal": {"slug": m["slug"], "n": m["naam"], "k": m["kcal"], "pp": 4}} for m in ms])
    tops = "".join(f'<li class="{"w" if i == 0 else ""}"><span class="rk">{i + 1}e goedkoopst</span><b style="font-size:19px">{esc(wnaam(si))}</b>{tag(t, "big" if i == 0 else "")}'
                   f'<span class="muted">{pp(t / 5)} per persoon per maaltijd</span>'
                   f'<button type="button" class="add addall" data-m="{slug_}" data-os="{esc(json.dumps(os_van(si, rg), ensure_ascii=False))}">+ Hele weekmenu op mijn lijst</button></li>' for i, (si, t, rg) in enumerate(rang[:3]))
    lijst = "".join(f'<tr><td>{esc(n)}<span class="sub">{esc(p[1])}{" · " + str(nn) + "x" if nn > 1 else ""}</span></td><td class="p">{eur(k)}</td></tr>' for n, q, k, p, nn, gb in sorted(regels0, key=lambda r: -r[2]))
    allew = "".join(f'<tr{" class=win" if i == 0 else ""}><td><b>{i + 1}. {esc(wnaam(si))}</b></td><td class="p">{tag(t)}</td><td class="p">{"" if i == 0 else "+ " + eur(t - tot0)}</td></tr>' for i, (si, t, rg) in enumerate(rang))
    faq = [(f"Wat kost dit weekmenu?", f"Op {DATUM} kost het hele weekmenu voor 4 personen {eur(tot0)} bij {wnaam(si0)}, voor 5 avondmaaltijden. Bij {wnaam(rang[-1][0])} betaal je {eur(rang[-1][1] - tot0)} meer."),
           ("Waarom is samen inkopen goedkoper?", f"Ingrediënten die in meer gerechten zitten, zoals uien of knoflook, koop je maar één keer. Los gekocht kosten deze 5 maaltijden samen ongeveer {eur(los)}; samen ingekocht {eur(tot0)}."),
           ("Wat zit er niet bij?", "Olie, zout, peper, kruiden en bouillon uit de voorraadkast tellen niet mee in de prijs. Die staan wel bij elk recept.")]
    keus = '<div class="chips wmkeus" id="meer" role="navigation" aria-label="Kies een weekmenu">' + "".join(f'<a class="chip" href="/maaltijden/{x}/"{" aria-current=page" if x == slug_ else ""}>{t}</a>' for x, t in [("weekmenu", "💶 Goedkoop"), ("weekmenu-glutenvrij", "🌾 Glutenvrij"), ("weekmenu-caloriearm", "🥗 Caloriearm"), ("weekmenu-lactosevrij", "🥛 Lactosevrij"), ("weekmenu-vegan", "🌱 Vegan"), ("weekmenu-eiwitrijk", "💪 Eiwitrijk"), ("weekmenu-halal", "Halal"), ("weekmenu-koosjer", "Koosjer")]) + "</div>"
    body = (keus + deelknop(f"{h1}: 5 avondmaaltijden voor 4 personen, samen {eur(tot0)}", f"/maaltijden/{slug_}/") + f'<h2>Het menu</h2><ul class="links weekmenu">{menu}</ul>'
            f'<h2>Waar koop je alles het goedkoopst?</h2><ol class="mtop">{tops}</ol>'
            f'<h2>Boodschappenlijst bij {esc(wnaam(si0))}</h2><div class="tblwrap"><table class="ptable"><tbody>{lijst}</tbody><tfoot><tr><td><b>Totaal</b></td><td class="p"><b>{eur(tot0)}</b></td></tr></tfoot></table></div>'
            f'<p class="note">Hele verpakkingen, zoals aan de kassa. Prijzen van {DATUM}; lopende aanbiedingen tellen mee. Het menu wordt elke dag opnieuw gekozen op basis van de prijzen.</p>'
            f'<h2>Alle supermarkten</h2><div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">Weekmenu</th><th style="text-align:right">Verschil</th></tr></thead><tbody>{allew}</tbody></table></div>'
            + faq_html(faq) + '<h2>Meer weekmenu\'s</h2><ul class="links">'
            + "".join(f'<li><a href="/maaltijden/{x}/">{t}</a></li>' for x, t in [("weekmenu", "Goedkoop weekmenu"), ("weekmenu-glutenvrij", "Glutenvrij weekmenu"), ("weekmenu-caloriearm", "Caloriearm weekmenu"), ("weekmenu-lactosevrij", "Lactosevrij weekmenu"), ("weekmenu-vegan", "Vegan weekmenu"), ("weekmenu-eiwitrijk", "Eiwitrijk weekmenu"), ("weekmenu-halal", "Halal weekmenu"), ("weekmenu-koosjer", "Koosjer weekmenu")] if x != slug_)
            + '<li><a href="/maaltijden/">Alle complete maaltijden</a></li></ul>' + MJS)
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/maaltijden/{m['slug']}/", "name": m["naam"]} for i, m in enumerate(ms)]}
    title = f"{h1}: 5 avondmaaltijden voor {eur(tot0)} ({MAAND})"
    desc = f"{kort}: 5 avondmaaltijden voor 4 personen, samen ingekocht voor {eur(tot0)} bij {wnaam(si0)} ({pp(tot0 / 5)} p.p. per maaltijd). Met boodschappenlijst en prijs per supermarkt, elke dag bijgewerkt."
    schrijf(path, page(path, title, desc, crumbs_head(ch, h1, lead), body, [cld, il, faq_ld(faq)], actief="/maaltijden/", og_title=f"{h1} voor {eur(tot0)}"))
    made.append((path, "0.8"))
    WEEKMENU_PRIJS[slug_] = (tot0, si0)
    return tot0
if MAAL:
    weekmenu("weekmenu", "Goedkoop weekmenu", "Goedkoop weekmenu", "Elke dag wat anders.", MAAL)
    weekmenu("weekmenu-glutenvrij", "Glutenvrij weekmenu", "Glutenvrij weekmenu", "Alles zonder gluten. Check bij bouillon het etiket.", [m for m in MAAL if m["glutenvrij"]])
    weekmenu("weekmenu-caloriearm", "Caloriearm weekmenu", "Caloriearm weekmenu", f"Elke maaltijd hoogstens {KCAL_ARM} kcal per persoon.", [m for m in MAAL if m["kcal"] <= KCAL_ARM])
    weekmenu("weekmenu-lactosevrij", "Lactosevrij weekmenu", "Lactosevrij weekmenu", "Alle gerechten zonder melk, room, boter, kaas of yoghurt.", [m for m in MAAL if m.get("lactosevrij")])
    weekmenu("weekmenu-halal", "Halal weekmenu", "Halal weekmenu", "Zonder varkensvlees en alcohol. Kies voor vlees en kip een product met halal-keurmerk.", [m for m in MAAL if m.get("halal")])
    weekmenu("weekmenu-koosjer", "Koosjer weekmenu", "Koosjer weekmenu", "Zonder varkensvlees en schaaldieren, en nooit vlees samen met zuivel. Kies vlees en producten met een hechsjer.", [m for m in MAAL if m.get("koosjer")])
    weekmenu("weekmenu-vegan", "Vegan weekmenu", "Vegan weekmenu", "Alle gerechten helemaal plantaardig: zonder vlees, vis, zuivel en ei. Kies bij vleesvervangers en bouillon een vegan variant.", [m for m in MAAL if m.get("vegan")])
    weekmenu("weekmenu-eiwitrijk", "Eiwitrijk weekmenu", "Eiwitrijk weekmenu", "Elke maaltijd minstens 30 gram eiwit per persoon: handig als je sport.", [m for m in MAAL if m.get("eiwitrijk")])
print(len(MAAL), "maaltijdpagina's")
