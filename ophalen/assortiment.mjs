// Haalt de GEWONE prijzen (het hele assortiment) op van winkels waarvan het open prijzenbestand van Checkjebon
// niet meer wordt bijgewerkt. Schrijft per winkel data/assortiment-<id>.json in hetzelfde formaat als Checkjebon:
//   { updated, n: id, c: naam, u: basislink, d: [{ n: naam, l: link (achter u), p: prijs, s: inhoud }, ...] }
// scripts/eigen_prijzen.py zet deze gegevens in de build in de plaats van de verouderde Checkjebon-gegevens.
// Rustig tempo: eens per dag, met pauzes tussen de verzoeken. Lukt een winkel niet, dan blijft het vorige bestand staan.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data');
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const slaap = ms => new Promise(r => setTimeout(r, ms));
const r2 = n => Math.round(n * 100) / 100;
const slug = s => String(s || 'product').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'product';

async function haal(url, opts = {}, pogingen = 4) {
  let fout;
  for (let i = 1; i <= pogingen; i++) {
    try {
      const r = await fetch(url, { ...opts, headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL', ...(opts.headers || {}) }, signal: AbortSignal.timeout(45_000) });
      if (r.status === 429 || r.status >= 500) throw new Error(`HTTP ${r.status}`);
      if (!r.ok) { const e = new Error(`HTTP ${r.status} ${url}`); e.stop = true; throw e; }
      return await r.json();
    } catch (e) { fout = e; if (e.stop) break; await slaap(4000 * i); }
  }
  throw fout;
}

/* ---------- Albert Heijn: dezelfde zoekdienst als voor de Bonus, per productsoort (elk minder dan 3000 producten) ---------- */
async function ah() {
  const H = { 'User-Agent': 'Appie/8.22.3', 'X-Application': 'AHWEBSHOP' };
  let tok;
  for (let i = 0; i < 6 && !tok; i++) {
    try { tok = (await haal('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: JSON.stringify({ clientId: 'appie' }) })).access_token; }
    catch (e) { await slaap(5000 * (i + 1)); }
  }
  if (!tok) throw new Error('geen AH-token');
  const A = { headers: { ...H, Authorization: `Bearer ${tok}` } };
  const basis = await haal('https://api.ah.nl/mobile-services/product/search/v2?query=&size=1&page=0', A);
  const soorten = ((basis.filters || []).find(f => f.id === 'taxonomy')?.options || []).map(o => o.id);
  if (soorten.length < 20) throw new Error(`te weinig AH-productsoorten (${soorten.length})`);
  const uit = new Map();
  for (const id of soorten) {
    for (let page = 0; page < 3; page++) {
      let d;
      try { d = await haal(`https://api.ah.nl/mobile-services/product/search/v2?taxonomyId=${id}&size=1000&page=${page}`, A); }
      catch (e) { console.warn('ah soort', id, e.message); break; }
      for (const p of d.products || []) {
        const prijs = p.priceBeforeBonus ?? p.currentPrice;
        if (!(prijs > 0) || uit.has(p.webshopId)) continue;
        if (p.orderAvailabilityStatus && p.orderAvailabilityStatus !== 'IN_ASSORTMENT') continue;
        // Bundels als "Leffe 12-pack" met maat "2 stuks" zijn meerdere verpakkingen van een product dat al los in de lijst staat: overslaan.
        if (/\d+\s*-?\s*(?:pack|pck)\b/i.test(p.title) && /^\d+ stuks?$/i.test(p.salesUnitSize || '')) continue;
        uit.set(p.webshopId, { n: String(p.title || '').replace(/\s+/g, ' ').trim(), l: `wi${p.webshopId}/${slug(p.title)}`, p: r2(prijs), s: p.salesUnitSize || '' });
      }
      if (!d.page || page + 1 >= d.page.totalPages) break;
      await slaap(700);
    }
    await slaap(700);
  }
  // De lijst met productsoorten is niet volledig (zo ontbreken koffiebonen); daarom daarna ook elke zoekterm van de site zelf.
  const neem = p => {
    const prijs = p.priceBeforeBonus ?? p.currentPrice;
    if (!(prijs > 0) || uit.has(p.webshopId)) return;
    if (p.orderAvailabilityStatus && p.orderAvailabilityStatus !== 'IN_ASSORTMENT') return;
    if (/\d+\s*-?\s*(?:pack|pck)\b/i.test(p.title) && /^\d+ stuks?$/i.test(p.salesUnitSize || '')) return;
    uit.set(p.webshopId, { n: String(p.title || '').replace(/\s+/g, ' ').trim(), l: `wi${p.webshopId}/${slug(p.title)}`, p: r2(prijs), s: p.salesUnitSize || '' });
  };
  let termen = [];
  try { termen = [...new Set(JSON.parse(fs.readFileSync(path.join(DATA, '..', 'scripts', 'cats.json'), 'utf8')).flatMap(c => c[2] || []))]; } catch (e) { console.warn('geen zoektermen', e.message); }
  const voor = uit.size;
  for (const t of termen) {
    try { const d = await haal(`https://api.ah.nl/mobile-services/product/search/v2?query=${encodeURIComponent(t)}&size=150&page=0`, A); for (const p of d.products || []) neem(p); }
    catch (e) { console.warn('ah zoekterm', t, e.message); }
    await slaap(400);
  }
  console.log('ah:', voor, 'via productsoorten,', uit.size - voor, 'extra via', termen.length, 'zoektermen');
  return { c: 'AH', u: 'https://www.ah.nl/producten/product/', d: [...uit.values()] };
}

/* ---------- Hoogvliet: de productcatalogus van hun eigen webwinkel, per hoofdgroep ---------- */
// De naam bevat het merk niet; dat staat wel vooraan in de url ("lavazza-qualita-oro-filterkoffie-695636000").
function hvMerk(urlKey, naam, sku) {
  let k = String(urlKey || '');
  if (sku && k.endsWith('-' + sku)) k = k.slice(0, -(String(sku).length + 1));
  const n = slug(naam);
  if (!n || !k.endsWith(n)) return '';
  const m = k.slice(0, -n.length).replace(/-$/, '');
  if (!m) return '';
  return m.replace(/-amp-/g, ' & ').replace(/-apos-/g, "'").split('-').map(w => w.length > 1 ? w[0].toUpperCase() + w.slice(1) : w).join(' ').replace(/ ' /g, "'").replace(/^G'woon$/i, "g'woon");
}
async function hoogvliet() {
  const G = 'https://www.hoogvliet.com/graphql';
  const vraag = async q => (await haal(G, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) })).data;
  const boom = await vraag('{categoryList{id children{id name}}}');
  const groepen = (boom?.categoryList?.[0]?.children || []).filter(c => !/aanbieding/i.test(c.name));
  if (groepen.length < 10) throw new Error(`te weinig Hoogvliet-groepen (${groepen.length})`);
  // 1. Alle artikelnummers per hoofdgroep.
  const skus = new Set();
  for (const g of groepen) {
    for (let page = 1; page <= 20; page++) {
      let d;
      try { d = await vraag(`{categoryList(filters:{ids:{eq:"${g.id}"}}){products(pageSize:500,currentPage:${page}){page_info{total_pages} items{sku}}}}`); }
      catch (e) { console.warn('hoogvliet groep', g.name, e.message); break; }
      const pr = d?.categoryList?.[0]?.products;
      for (const it of pr?.items || []) if (it.sku) skus.add(it.sku);
      if (!pr?.page_info || page >= pr.page_info.total_pages) break;
      await slaap(800);
    }
    await slaap(500);
  }
  // 2. Naam, inhoud en prijs per 100 artikelen (de inhoud geeft de webwinkel alleen zo mee).
  const uit = new Map();
  const lijst = [...skus];
  for (let i = 0; i < lijst.length; i += 100) {
    const deel = lijst.slice(i, i + 100);
    let d;
    try { d = await vraag(`{products(filter:{sku:{in:${JSON.stringify(deel)}}},pageSize:100){items{name sku url_key sub_title_attributes{volume unit} price_range{minimum_price{regular_price{value} final_price{value}}}}}}`); }
    catch (e) { console.warn('hoogvliet details', i, e.message); continue; }
    for (const it of d?.products?.items || []) {
      const mp = it.price_range?.minimum_price || {};
      const prijs = mp.regular_price?.value ?? mp.final_price?.value;
      if (!(prijs > 0) || uit.has(it.sku)) continue;
      const merk = hvMerk(it.url_key, it.name, it.sku);
      const naam = (merk && !String(it.name).toLowerCase().startsWith(merk.toLowerCase()) ? merk + ' ' : '') + it.name;
      const st = it.sub_title_attributes || {};
      uit.set(it.sku, { n: naam.replace(/\s+/g, ' ').trim(), l: it.url_key, p: r2(prijs), s: st.volume ? `${st.volume} ${String(st.unit || '').toLowerCase()}`.trim() : '' });
    }
    await slaap(600);
  }
  return { c: 'Hoogvliet', u: 'https://hoogvliet.nl/product/', d: [...uit.values()] };
}

/* ---------- Lidl: de open zoekdienst bevat ook de boodschappen, maar alleen als je op een woord zoekt.
   Daarom zoeken we op een lange lijst boodschappenwoorden en houden we alleen Food en groente/fruit (F+V) over.
   Dat zijn de gewone winkelprijzen (geen actieprijzen: bij een actie staat de gewone prijs als oldPrice). ---------- */
const LIDL_WOORDEN = `melk halfvolle volle karnemelk chocolademelk yoghurt kwark vla pudding room slagroom boter margarine roomboter eieren
kaas jong belegen oud geraspte mozzarella feta brie camembert smeerkaas roomkaas hüttenkäse plakken
brood volkoren wit bruin tijger meergranen spelt casino bolletjes broodjes croissant stokbrood pistolet krentenbol beschuit crackers knäckebrood toast ontbijtkoek
appel peer banaan sinaasappel mandarijn citroen limoen druiven aardbeien blauwe bessen frambozen kiwi mango ananas meloen avocado granaatappel pruimen nectarines
tomaat komkommer paprika ui rode ui knoflook aardappel krieltjes zoete wortel winterpeen sla ijsbergsla rucola spinazie andijvie broccoli bloemkool courgette aubergine champignons prei boontjes sperziebonen spruitjes rode kool witlof bleekselderij radijs mais doperwten
kip kipfilet kippendijen drumsticks gehakt rundergehakt half-om-half hamburger biefstuk speklappen varkenshaas schnitzel slavink rookworst worst braadworst knakworst frikandel kroket bitterballen ham kipfilet beleg salami cervelaat leverworst filet americain spek ontbijtspek
vis zalm kabeljauw pangasius tilapia garnalen mosselen tonijn makreel haring sardines vissticks lekkerbekje
pasta spaghetti macaroni penne tagliatelle lasagne rijst basmati zilvervlies noedels couscous bulgur quinoa wraps tortilla
saus pastasaus tomatenblokjes passata pesto ketchup mayonaise mosterd curry satésaus sambal sojasaus bouillon jus olie olijfolie zonnebloemolie azijn kruiden peper zout suiker meel bakmix
soep cup-a-soup erwtensoep tomatensoep
koffie koffiebonen koffiepads capsules oploskoffie thee sap appelsap sinaasappelsap frisdrank cola sinas cassis ice tea limonade siroop water bruisend mineraalwater energiedrank bier pils alcoholvrij wijn rode witte rosé prosecco
chips nootjes pinda's cashew borrelnootjes popcorn zoutjes koek koekjes stroopwafels speculaas biscuit chocolade reep bonbons snoep drop winegums kauwgom
hagelslag vlokken pindakaas jam honing chocopasta appelstroop muesli granola cornflakes havermout cruesli ontbijtgranen
diepvries pizza friet patat ijs groente diepvriesgroente spinazie à la crème
babyvoeding luiers billendoekjes
toiletpapier keukenrol tissues wasmiddel wasverzachter vaatwastabletten afwasmiddel allesreiniger schoonmaak vuilniszakken aluminiumfolie
shampoo douchegel deodorant tandpasta tandenborstel zeep handzeep scheermesjes maandverband tampons
kattenvoer kattenbrokken hondenvoer hondenbrokken kattenbakvulling
vega vegetarisch vegan tofu hummus falafel plantaardig haverdrank sojadrink amandeldrink
bio biologisch glutenvrij lactosevrij`.split(/\s+/).filter(Boolean);
const LIDL_MERKEN = `Milbona Pilos Chef Select Freshona Solevita Bellarom Fin Carré Crownfield Belbake Kania Vitasia Combino Snack Day Deluxe Cien Formil W5
Dentalux Lupilu Floralys Nautica Pikok Dulano Tastino Mcennedy Italiamo Sondey Perlenbacher Freeway Saskia Alesto Rivercote Ocean Sea Baresa Gelatelli
Nussa Vemondo Envia Favorina Trattoria Alfredo Eridanous Cucina Nobile Golden Seafood Harvest Basket Oaklands Coshida Orlando Grafschafter Bergader Linessa
Cantina Tequito Lyttos Toujours Biotrend Fairglobe Ventura Purland Perlinger Grafenwalder Batts Belweder Zwagerman`.split(/\s+/);
// Zoekwoorden: de vaste lijst, de huismerken van Lidl en de meest voorkomende woorden uit de productnamen van de andere supermarkten.
function lidlWoorden() {
  const tel = new Map();
  for (const w of ['ah', 'jumbo', 'plus', 'dirk', 'hoogvliet', 'dekamarkt', 'vomar']) {
    try {
      for (const x of JSON.parse(fs.readFileSync(path.join(DATA, `assortiment-${w}.json`), 'utf8')).d)
        for (const t of String(x.n).toLowerCase().match(/[a-zà-ÿ]{4,}/g) || []) tel.set(t, (tel.get(t) || 0) + 1);
    } catch {}
  }
  const vaak = [...tel].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).slice(0, 400).map(([t]) => t);
  return [...new Set([...LIDL_WOORDEN, ...LIDL_MERKEN.map(m => m.toLowerCase()), ...vaak])].filter(w => w.length >= 3);
}
async function lidl() {
  const uit = new Map(), woorden = lidlWoorden();
  const neem = it => {
    const x = it.gridbox?.data; if (!x?.price || !x.fullTitle) return;
    if (!['Food', 'F+V'].includes(x.category)) return;
    const oud = x.price.discount?.fromRecommendedPrice ? null : x.price.oldPrice;  // een adviesprijs is geen eigen Lidl-prijs
    const prijs = oud > x.price.price ? oud : x.price.price;
    if (!(prijs > 0)) return;
    const k = String(x.productId || it.code || x.fullTitle);
    if (!uit.has(k)) uit.set(k, { n: String(x.fullTitle).replace(/[®™]/g, '').replace(/^[-–\s]+/, '').replace(/\s+/g, ' ').trim(), l: x.canonicalPath || '/', p: r2(prijs), s: x.price.packaging?.text || '' });
  };
  // Eerst de hele categorie "Eten & drinken" (zonder zoekwoord), daarna de zoekwoorden voor wat daar niet in staat.
  for (let off = 0, tot = 1; off < tot && off < 5000; off += 500) {
    try { const d = await haal(`https://www.lidl.nl/q/api/search?offset=${off}&fetchsize=500&locale=nl_NL&assortment=NL&version=2.1.0&category.id=10068374&q=`); tot = d.numFound || 0; (d.items || []).forEach(neem); }
    catch (e) { console.warn('lidl categorie', e.message); break; }
    await slaap(1000);
  }
  // Dan alle producten uit de productsitemap van Lidl (±14.000), per 50 opgevraagd bij de gridbox-dienst:
  // die geeft de prijs voor elk product waarvan Lidl online een prijs toont.
  try {
    const r = await fetch('https://www.lidl.nl/p/export/NL/nl/product_sitemap.xml.gz', { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(60_000) });
    let buf = Buffer.from(await r.arrayBuffer());
    try { buf = zlib.gunzipSync(buf); } catch {}
    const ids = [...new Set([...buf.toString('utf8').matchAll(/\/p(\d+)<\/loc>/g)].map(m => m[1]))];
    let j = 0;
    const gw = async () => {
      while (j < ids.length) {
        const b = ids.slice(j, j += 50);
        try {
          const lijst = await haal('https://www.lidl.nl/p/api/gridboxes/NL/nl?erpNumbers=' + b.join(','), {}, 2);
          for (const x of lijst || []) neem({ gridbox: { data: x } });
        } catch (e) { await slaap(3000); }
        await slaap(300);
      }
    };
    await Promise.all([gw(), gw(), gw(), gw()]);
    console.log('lidl sitemap:', ids.length, 'producten bekeken');
  } catch (e) { console.warn('lidl sitemap mislukt', e.message); }
  let i = 0;
  const werker = async () => {
    while (i < woorden.length) {
      const w = woorden[i++];
      let d;
      try { d = await haal(`https://www.lidl.nl/q/api/search?offset=0&fetchsize=200&locale=nl_NL&assortment=NL&version=2.1.0&q=${encodeURIComponent(w)}`, {}, 2); }
      catch (e) { await slaap(5000); continue; }
      (d.items || []).forEach(neem);
      await slaap(400);
    }
  };
  await Promise.all([werker(), werker(), werker()]);
  console.log('lidl:', woorden.length, 'zoekwoorden');
  return { c: 'Lidl', u: 'https://www.lidl.nl', d: [...uit.values()], klein: true };
}

/* ---------- Jumbo: dezelfde open GraphQL-zoekdienst als voor de aanbiedingen, nu zonder filter (het hele assortiment) ---------- */
async function jumbo() {
  const H = { 'content-type': 'application/json', 'apollographql-client-name': 'JUMBO_WEB-search', 'apollographql-client-version': 'master-v29.4.0-web' };
  const Q = 'query($input:ProductSearchInput!){searchProducts(input:$input){count products{id title subtitle packSizeDisplay price{price}}}}';
  const uit = new Map(); let count = 0;
  for (let off = 0; off < Math.max(1, count) && off < 40000; off += 200) {
    const j = await haal('https://www.jumbo.com/api/graphql', { method: 'POST', headers: H, body: JSON.stringify({ query: Q, variables: { input: { searchType: 'keyword', searchTerms: '*', offSet: off, limit: 200 } } }) });
    const d = j?.data?.searchProducts;
    if (!d) throw new Error(j?.errors?.[0]?.message || 'onverwacht antwoord van Jumbo');
    count = d.count || 0;
    for (const p of d.products || []) {
      const prijs = p.price?.price != null ? p.price.price / 100 : null;  // gewone prijs (promoPrice laten we hier weg)
      if (!(prijs > 0) || !p.title || uit.has(p.id)) continue;
      uit.set(p.id, { n: String(p.title).replace(/\s+/g, ' ').trim(), l: `${slug(p.title)}-${p.id}`, p: r2(prijs), s: p.subtitle || p.packSizeDisplay || '' });
    }
    if (!(d.products || []).length) break;
    await slaap(700);
  }
  // Geeft de zoekdienst maar een deel van het assortiment terug, dan liever het open bestand houden dan producten kwijtraken.
  if (uit.size < 0.85 * count) throw new Error(`maar ${uit.size} van de ${count} Jumbo-producten opgehaald`);
  return { c: 'Jumbo', u: 'https://www.jumbo.com/producten/', d: [...uit.values()] };
}

/* ---------- PLUS: de productlijsten van hun webwinkel, per hoofdgroep (12 producten per pagina) ---------- */
// Versie en api-sleutel staan in het script van de productlijst; die lezen we elke keer opnieuw (net als bij de aanbiedingen).
async function plus() {
  const B = 'https://www.plus.nl';
  const txt = async (u, o = {}) => { const r = await fetch(u, { ...o, headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL', ...(o.headers || {}) }, signal: AbortSignal.timeout(45_000) }); if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + u); return r.text(); };
  const tok = (await haal(`${B}/moduleservices/moduleversioninfo`)).versionToken;
  const info = (await haal(`${B}/moduleservices/moduleinfo`)).manifest?.urlVersions || {};
  const pad = Object.keys(info).find(u => u.endsWith('ECP_Composition_CW.ProductLists.PLP_Content.mvc.js'));
  if (!pad) throw new Error('PLUS-productlijstscript niet gevonden');
  const api = ((await txt(B + pad + info[pad])).match(/DataActionGetProductListAndCategoryInfo", "[^"]+", "([^"]+)"/) || [])[1];
  if (!api) throw new Error('PLUS-api-sleutel niet gevonden');
  const H = { 'Content-Type': 'application/json; charset=UTF-8', 'X-CSRFToken': 'T6C+9iB49TLra4jEsMeSckDMNhQ=', 'OutSystems-locale': 'nl-NL', Referer: `${B}/producten` };
  const sm = await txt(`${B}/ECP_Sitemap_Engine/rest/Sitemap/category`);
  const groepen = [...new Set([...sm.matchAll(/<loc>https:\/\/www\.plus\.nl\/producten\/([a-z0-9-]+)<\/loc>/g)].map(m => m[1]))];
  if (groepen.length < 8) throw new Error(`te weinig PLUS-groepen (${groepen.length})`);
  const uit = new Map();
  for (const g of groepen) {
    for (let pn = 1, tp = 1; pn <= tp && pn <= 400; pn++) {
      let d;
      try {
        d = (await haal(`${B}/screenservices/ECP_Composition_CW/ProductLists/PLP_Content/DataActionGetProductListAndCategoryInfo`, { method: 'POST', headers: H, body: JSON.stringify({ versionInfo: { moduleVersion: tok, apiVersion: api }, viewName: 'MainFlow.ProductListPage', screenData: { variables: { CategorySlug: g, PageNumber: pn } } }) })).data;
      } catch (e) { console.warn('plus', g, pn, e.message); break; }
      tp = d?.TotalPages || 0;
      for (const x of d?.ProductList?.List || []) {
        const p = x.PLP_Str || {};
        const prijs = parseFloat(p.OriginalPrice) > 0 ? parseFloat(p.OriginalPrice) : parseFloat(p.NewPrice);
        if (!(prijs > 0) || !p.Slug || uit.has(p.SKU || p.Slug)) continue;
        uit.set(p.SKU || p.Slug, { n: String(p.Name || '').replace(/\s+/g, ' ').trim(), l: p.Slug, p: r2(prijs), s: String(p.Product_Subtitle || '').trim() });
      }
      await slaap(500);
    }
    console.log('plus', g, uit.size);
  }
  return { c: 'PLUS', u: `${B}/product/`, d: [...uit.values()] };
}

/* ---------- Dirk en DekaMarkt: productpagina's uit hun sitemap, verdeeld over de week ---------- */
// Elke productpagina bevat de prijs (normalPrice) in de Nuxt-gegevens. Het zijn er duizenden; daarom per dag een deel,
// eerst nooit bekeken, dan de langst niet bekeken. Prijzen blijven 21 dagen geldig als de pagina niet opnieuw aan de beurt was.
function nuxtData(html) {
  const m = html.match(/<script[^>]*id="__NUXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
  if (!m) return null;
  const a = JSON.parse(m[1]);
  const memo = new Map();
  const rev = i => {
    if (memo.has(i)) return memo.get(i);
    const v = a[i];
    let r;
    if (Array.isArray(v)) {
      if (typeof v[0] === 'string' && ['Reactive', 'ShallowReactive', 'Ref', 'ShallowRef', 'NuxtError'].includes(v[0])) { memo.set(i, null); r = rev(v[1]); }
      else if (typeof v[0] === 'string' && ['EmptyRef', 'EmptyShallowRef', 'Set', 'Map', 'Date'].includes(v[0])) r = null;
      else { r = []; memo.set(i, r); for (const x of v) r.push(typeof x === 'number' ? rev(x) : x); }
    } else if (v && typeof v === 'object') {
      r = {}; memo.set(i, r);
      for (const [k, x] of Object.entries(v)) r[k] = typeof x === 'number' ? rev(x) : x;
    } else r = v;
    memo.set(i, r);
    return r;
  };
  return rev(0);
}
function zoek(node, test, diepte = 0) {
  if (!node || typeof node !== 'object' || diepte > 40) return null;
  if (test(node)) return node;
  for (const v of Array.isArray(node) ? node : Object.values(node)) { const r = zoek(v, test, diepte + 1); if (r) return r; }
  return null;
}
async function tekst(url) {
  for (let i = 1; i <= 3; i++) {
    try { const r = await fetch(url, { headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL' }, signal: AbortSignal.timeout(45_000) }); if (r.status === 404) return null; if (r.ok) return await r.text(); throw new Error('HTTP ' + r.status); }
    catch (e) { if (i === 3) throw e; await slaap(3000 * i); }
  }
}
const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());
// Algemeen: een lijst productpagina's, per dag een deel bekijken (eerst nooit bekeken, dan de langst niet bekeken).
// lees(html, id) geeft { n, p, s } of null. Prijzen blijven 21 dagen geldig als een pagina niet opnieuw aan de beurt was.
async function roterend(id, naam, urls, lees, perDag) {
  if (urls.length < 1000) throw new Error(`te weinig ${naam}-producten gevonden (${urls.length})`);
  const pad = path.join(DATA, `assortiment-${id}.json`);
  let vorig = {}; try { vorig = JSON.parse(fs.readFileSync(pad, 'utf8')).bekeken || {}; } catch {}
  const vd = vandaag();
  const grens = new Date(Date.now() - 21 * 864e5).toISOString().slice(0, 10);
  const pid = u => u.match(/(\d+)\/?$/)[1];
  const rij = urls.slice().sort((a, b) => String(vorig[pid(a)]?.dag || '').localeCompare(String(vorig[pid(b)]?.dag || '')));
  let n = 0, fout = 0;
  // Normaal één pagina tegelijk; bij een inhaalslag (WERKERS) een paar tegelijk.
  const taken = rij.slice(0, +process.env.PER_DAG || perDag);
  const werker = async () => {
    while (taken.length) {
      const u = taken.shift(), k = pid(u);
      try {
        const html = await tekst(u);
        if (html == null) { delete vorig[k]; continue; }
        const r = lees(html, k);
        if (r && r.p > 0 && r.n) { vorig[k] = { dag: vd, n: r.n.replace(/\s+/g, ' ').trim(), l: u, p: r2(r.p), s: String(r.s || '').trim() }; n++; }
        else vorig[k] = { ...(vorig[k] || {}), dag: vd, weg: true };
      } catch (e) {
        // Te veel fouten (bijv. 403 omdat de winkel ons even weert): stoppen, maar wat al gelukt is wel bewaren.
        if (++fout > 30) { console.warn(`${naam}: gestopt na ${fout} fouten (${e.message}); ${n} pagina's gelukt`); taken.length = 0; }
      }
      await slaap(500);
    }
  };
  await Promise.all(Array.from({ length: Math.max(1, Math.min(6, +process.env.WERKERS || 1)) }, werker));
  const bestaat = new Set(urls.map(pid));
  for (const k of Object.keys(vorig)) if (!bestaat.has(k)) delete vorig[k];
  const d = Object.values(vorig).filter(x => !x.weg && x.p > 0 && x.n && x.dag >= grens).map(({ dag, weg, ...x }) => x);
  console.log(naam, n, 'pagina\'s vandaag bekeken,', d.length, 'producten met een prijs van de afgelopen 21 dagen, in totaal', urls.length);
  return { c: naam, u: '', t: urls.length, d, bekeken: vorig };
}

/* ---------- Dirk en DekaMarkt (zelfde webwinkel): productpagina's uit hun sitemap ---------- */
// Elke productpagina bevat de prijs (normalPrice) in de Nuxt-gegevens.
const leesDetailresult = (html, k) => {
  const p = zoek(nuxtData(html), x => x && String(x.productId) === k && x.normalPrice != null && x.productInformation);
  return p ? { n: p.productInformation?.headerText || '', p: p.normalPrice, s: p.productInformation?.packaging || '' } : null;
};
function detailresult(id, naam, site, perDag, maakLink = u => u) {
  return async () => {
    const sm = await tekst(`${site}/products-sitemap.xml`);
    const urls = [...String(sm || '').matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => maakLink(m[1].trim())).filter(u => /\/(\d+)$/.test(u));
    return roterend(id, naam, urls, leesDetailresult, perDag);
  };
}
// Dirk weert te veel verzoeken tegelijk (403): altijd één tegelijk, met wat meer tijd ertussen.
const dirk = detailresult('dirk', 'Dirk', 'https://www.dirk.nl', 1400);
// In de sitemap van DekaMarkt staat "/boodschappen/producten/..."; de werkende link is zonder "/producten".
const dekamarkt = detailresult('dekamarkt', 'DekaMarkt', 'https://www.dekamarkt.nl', 1400, u => u.replace('/boodschappen/producten/', '/boodschappen/'));

/* ---------- Vomar: productpagina's, gevonden via hun categoriepagina's ---------- */
async function vomar() {
  const B = 'https://www.vomar.nl';
  const links = t => [...new Set((String(t || '').match(/href="(\/producten\/[^"#?]+)"/g) || []).map(x => x.slice(6, -1)))];
  const veilig = async u => { try { return await tekst(u); } catch (e) { console.warn('vomar', u, e.message); return ''; } };
  const top = links(await tekst(`${B}/producten`)).filter(x => x.split('/').length === 3);
  const subs = new Set();
  for (const t of top) { for (const x of links(await veilig(B + t))) if (x.startsWith(t + '/') && x.split('/').length === 4) subs.add(x); await slaap(500); }
  const prods = new Set();
  for (const s of subs) { for (const x of links(await veilig(B + s))) if (/\/\d+$/.test(x)) prods.add(B + x); await slaap(500); }
  const lees = (html, k) => {
    // In de Nuxt-gegevens: productDetails met omschrijving, inhoud, eenheid en prijs.
    const pd = html.match(new RegExp(`articleNumber:${k},description:"((?:[^"\\\\]|\\\\.)*)",contents:"([^"]*)",unit:"([^"]*)",price:([\\d.]+)`));
    if (pd) return { n: JSON.parse(`"${pd[1]}"`), p: +pd[4], s: pd[2] && pd[3] ? `${pd[2]} ${pd[3]}` : '' };
    const m = html.match(/<p class="price"[^>]*>\s*<span class="large"[^>]*>(\d+)\.?<\/span>\s*<span class="small"[^>]*>(\d+)<\/span>/);
    const h1 = (html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/) || [])[1];
    return m && h1 ? { n: h1.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&#39;|&apos;/g, "'").trim(), p: +(m[1] + '.' + m[2]), s: '' } : null;
  };
  return roterend('vomar', 'Vomar', [...prods], lees, 1300);
}

/* ---------- Ekoplaza (biologisch): productpagina's uit de sitemap; elke pagina heeft de prijs in de schema.org-gegevens ---------- */
async function ekoplaza() {
  const sm = await tekst('https://www.ekoplaza.nl/sitemap-products.xml');
  const urls = [...new Set([...String(sm || '').matchAll(/<loc>\s*(?:<!\[CDATA\[)?\s*([^<\]\s]+)/g)].map(m => m[1].trim()).filter(u => /\/producten\/product\/[a-z0-9-]+-\d+$/.test(u)))];
  const lees = html => {
    for (const m of html.matchAll(/<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)) {
      let d; try { d = JSON.parse(m[1]); } catch { continue; }
      for (const g of d['@graph'] || [d]) {
        if (g['@type'] !== 'Product') continue;
        const o = Array.isArray(g.offers) ? g.offers[0] : g.offers;
        if (!o || !(+o.price > 0) || /Discontinued/.test(o.availability || '')) return null;
        return { n: g.name, p: +o.price, s: g.size || '' };
      }
    }
    return null;
  };
  return roterend('ekoplaza', 'Ekoplaza', urls, lees, 1500);
}

// Lidl verkoopt zijn boodschappen niet online; via de zoekdienst (op woorden) halen we wel de gewone prijzen van de boodschappen op.
const WINKELS = { ah, jumbo, hoogvliet, plus, dirk, dekamarkt, vomar, ekoplaza, lidl };
const alleen = (process.env.WINKELS || '').split(',').filter(Boolean);
const nu = new Date().toISOString();
let gelukt = 0;
// Alle winkels tegelijk (elke winkel houdt zelf een rustig tempo aan).
await Promise.all(Object.entries(WINKELS).filter(([id]) => !alleen.length || alleen.includes(id)).map(async ([id, fn]) => {
  const t0 = Date.now();
  try {
    const r = await fn();
    // Veiligheidsgrens: een kapotte ophaalbeurt met veel te weinig producten niet opslaan.
    const vorig = (() => { try { return JSON.parse(fs.readFileSync(path.join(DATA, `assortiment-${id}.json`), 'utf8')).d.length; } catch { return 0; } })();
    if (!r.bekeken && (r.d.length < (r.klein ? 300 : 1000) || (vorig && r.d.length < vorig * 0.7))) throw new Error(`maar ${r.d.length} producten (vorige keer ${vorig})`);
    fs.writeFileSync(path.join(DATA, `assortiment-${id}.json`), JSON.stringify({ updated: nu, n: id, ...r }));
    console.log(id, r.d.length, 'producten in', Math.round((Date.now() - t0) / 1000), 's');
    gelukt++;
  } catch (e) { console.error(id, 'MISLUKT:', e.message); }
}));
if (!gelukt) process.exitCode = 1;
