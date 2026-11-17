// Haalt de GEWONE prijzen (het hele assortiment) op van winkels waarvan het open prijzenbestand van Checkjebon
// niet meer wordt bijgewerkt. Schrijft per winkel data/assortiment-<id>.json in hetzelfde formaat als Checkjebon:
//   { updated, n: id, c: naam, u: basislink, d: [{ n: naam, l: link (achter u), p: prijs, s: inhoud }, ...] }
// scripts/eigen_prijzen.py zet deze gegevens in de build in de plaats van de verouderde Checkjebon-gegevens.
// Rustig tempo: eens per dag, met pauzes tussen de verzoeken. Lukt een winkel niet, dan blijft het vorige bestand staan.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DATA = path.join(process.cwd(), 'data');
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

/* ---------- Lidl: dezelfde zoekdienst als voor de aanbiedingen, nu het hele assortiment ---------- */
async function lidl() {
  const uit = new Map();
  for (let off = 0, totaal = 1; off < totaal && off < 30000; off += 500) {
    const d = await haal(`https://www.lidl.nl/q/api/search?offset=${off}&fetchsize=500&locale=nl_NL&assortment=NL&version=2.1.0&q=`);
    totaal = d.numFound || 0;
    const items = d.items || [];
    for (const it of items) {
      const x = it.gridbox?.data; if (!x?.price || !x.fullTitle) continue;
      // Gewone prijs: bij een actie staat die als oldPrice; anders de prijs zelf.
      const oud = x.price.discount?.fromRecommendedPrice ? null : x.price.oldPrice;  // een adviesprijs is geen eigen Lidl-prijs
      const prijs = oud > x.price.price ? oud : x.price.price;
      if (!(prijs > 0)) continue;
      const k = String(it.code || x.productId || x.fullTitle);
      if (uit.has(k)) continue;
      uit.set(k, { n: String(x.fullTitle).replace(/[®™]/g, '').replace(/^[-–\s]+/, '').replace(/\s+/g, ' ').trim(), l: x.canonicalUrl || '/', p: r2(prijs), s: x.price.packaging?.text || '' });
    }
    if (!items.length) break;
    await slaap(1500);
  }
  return { c: 'Lidl', u: 'https://www.lidl.nl', d: [...uit.values()] };
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
  const pid = u => u.match(/\/(\d+)\/?$/)[1];
  const rij = urls.slice().sort((a, b) => String(vorig[pid(a)]?.dag || '').localeCompare(String(vorig[pid(b)]?.dag || '')));
  let n = 0, fout = 0;
  for (const u of rij.slice(0, +process.env.PER_DAG || perDag)) {
    const k = pid(u);
    try {
      const html = await tekst(u);
      if (html == null) { delete vorig[k]; continue; }
      const r = lees(html, k);
      if (r && r.p > 0 && r.n) { vorig[k] = { dag: vd, n: r.n.replace(/\s+/g, ' ').trim(), l: u, p: r2(r.p), s: String(r.s || '').trim() }; n++; }
      else vorig[k] = { ...(vorig[k] || {}), dag: vd, weg: true };
    } catch (e) { if (++fout > 50) throw new Error(`${naam}: te veel fouten (${e.message})`); }
    await slaap(500);
  }
  const bestaat = new Set(urls.map(pid));
  for (const k of Object.keys(vorig)) if (!bestaat.has(k)) delete vorig[k];
  const d = Object.values(vorig).filter(x => !x.weg && x.p > 0 && x.n && x.dag >= grens).map(({ dag, weg, ...x }) => x);
  console.log(naam, n, 'pagina\'s vandaag bekeken,', d.length, 'producten met een prijs van de afgelopen 21 dagen, in totaal', urls.length);
  return { c: naam, u: '', d, bekeken: vorig };
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
const dirk = detailresult('dirk', 'Dirk', 'https://www.dirk.nl', 1400);
// In de sitemap van DekaMarkt staat "/boodschappen/producten/..."; de werkende link is zonder "/producten".
const dekamarkt = detailresult('dekamarkt', 'DekaMarkt', 'https://www.dekamarkt.nl', 1400, u => u.replace('/boodschappen/producten/', '/boodschappen/'));

/* ---------- Vomar: productpagina's, gevonden via hun categoriepagina's ---------- */
async function vomar() {
  const B = 'https://www.vomar.nl';
  const links = t => [...new Set((String(t || '').match(/href="(\/producten\/[^"#?]+)"/g) || []).map(x => x.slice(6, -1)))];
  const top = links(await tekst(`${B}/producten`)).filter(x => x.split('/').length === 3);
  const subs = new Set();
  for (const t of top) { for (const x of links(await tekst(B + t))) if (x.startsWith(t + '/') && x.split('/').length === 4) subs.add(x); await slaap(500); }
  const prods = new Set();
  for (const s of subs) { for (const x of links(await tekst(B + s))) if (/\/\d+$/.test(x)) prods.add(B + x); await slaap(500); }
  const lees = html => {
    const m = html.match(/<p class="price"[^>]*>\s*<span class="large"[^>]*>(\d+)\.?<\/span>\s*<span class="small"[^>]*>(\d+)<\/span>/);
    const h1 = (html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/) || [])[1];
    return m && h1 ? { n: h1.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&#39;|&apos;/g, "'").trim(), p: +(m[1] + '.' + m[2]), s: '' } : null;
  };
  return roterend('vomar', 'Vomar', [...prods], lees, 1300);
}

// Lidl verkoopt zijn boodschappen niet online; de zoekdienst bevat vooral non-food. Lidl blijft daarom uit het open bestand komen.
const WINKELS = { ah, hoogvliet, plus, dirk, dekamarkt, vomar };
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
    if (!r.bekeken && (r.d.length < 1000 || (vorig && r.d.length < vorig * 0.7))) throw new Error(`maar ${r.d.length} producten (vorige keer ${vorig})`);
    fs.writeFileSync(path.join(DATA, `assortiment-${id}.json`), JSON.stringify({ updated: nu, n: id, ...r }));
    console.log(id, r.d.length, 'producten in', Math.round((Date.now() - t0) / 1000), 's');
    gelukt++;
  } catch (e) { console.error(id, 'MISLUKT:', e.message); }
}));
if (!gelukt) process.exitCode = 1;
