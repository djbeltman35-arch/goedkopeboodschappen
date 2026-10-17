// Haalt het Aldi-assortiment en de aanbiedingen van een aantal supermarkten op en schrijft:
//   data/aldi.json         { updated, products: [[naam, link, prijs, inhoud, prijsPerEenheid, eenheid], ...] }
//   data/aanbiedingen.json { updated, offers: [{ s, n, sz, p, was, lbl, u, t }, ...] }
//   data/status.json       per winkel het aantal en een eventuele foutmelding
// Elke winkel staat los: als er een faalt, blijven de vorige gegevens van die winkel staan.
// Draait met Node 22 zonder extra pakketten.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data');
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const slaap = ms => new Promise(r => setTimeout(r, ms));
const r2 = n => (n == null || !isFinite(n) ? null : Math.round(n * 100) / 100);
const getal = s => parseFloat(String(s).replace(',', '.'));
const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());
const dagVan = v => {
  if (v == null || v === '') return null;
  const d = typeof v === 'number' ? new Date(v < 1e12 ? v * 1000 : v) : new Date(v);
  return isNaN(d) ? null : new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(d);
};

async function haal(url, opts = {}, soort = 'json') {
  let fout;
  for (let poging = 1; poging <= 3; poging++) {
    try {
      const r = await fetch(url, { ...opts, headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL', ...(opts.headers || {}) }, signal: AbortSignal.timeout(30_000) });
      if (r.status === 429 || r.status >= 500) throw new Error(`HTTP ${r.status}`);
      if (!r.ok) { const e = new Error(`HTTP ${r.status} ${url}`); e.stop = true; throw e; }
      return soort === 'json' ? await r.json() : await r.text();
    } catch (e) {
      fout = e;
      if (e.stop) break;
      await slaap(2000 * poging);
    }
  }
  throw fout;
}

// "6x330 ml", "Ca. 800 g", "1,5 l", "4 stuks" -> { eenheid: 'kg'|'l'|'st', hoeveelheid }
function inhoud(t) {
  if (!t) return null;
  const s = String(t).toLowerCase().replace(/^(inhoud:|ca\.?)\s*/g, '').replace(/\s+/g, ' ');
  let m = s.match(/(?:(\d+)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|kilo|gram|gr|g|liter|ltr|l|cl|ml)\b/);
  if (m) {
    const f = { kg: ['kg', 1], kilo: ['kg', 1], gram: ['kg', .001], gr: ['kg', .001], g: ['kg', .001], liter: ['l', 1], ltr: ['l', 1], l: ['l', 1], cl: ['l', .01], ml: ['l', .001] }[m[3]];
    return { eenheid: f[0], hoeveelheid: (m[1] ? +m[1] : 1) * getal(m[2]) * f[1] };
  }
  m = s.match(/(\d+)\s*(stuks?|st|rollen|tabletten|capsules|pads|wasbeurten)\b/);
  if (m) return { eenheid: 'st', hoeveelheid: +m[1] };
  if (/per stuk/.test(s)) return { eenheid: 'st', hoeveelheid: 1 };
  return null;
}
const perEenheid = (prijs, sz) => { const i = inhoud(sz); return i && i.hoeveelheid > 0 ? [r2(prijs / i.hoeveelheid), i.eenheid] : [null, '']; };

// Prijs per stuk bij een actie als "1+1 gratis", "2e halve prijs", "2 voor 3,00", "25% korting".
function actiePrijs(tekst, normaal) {
  const t = String(tekst || '').toLowerCase().replace(/\s+/g, ' ').trim();
  let m;
  if (normaal > 0) {
    if ((m = t.match(/(\d+)\s*\+\s*(\d+) gratis/))) return normaal * +m[1] / (+m[1] + +m[2]);
    if ((m = t.match(/(\d+)e halve prijs/))) return normaal * (+m[1] - .5) / +m[1];
    if ((m = t.match(/(\d+)e gratis/))) return normaal * (+m[1] - 1) / +m[1];
    if ((m = t.match(/(\d+)\s*%\s*korting/))) return normaal * (1 - +m[1] / 100);
  }
  if ((m = t.match(/(\d+) (?:voor|stapelen voor) (\d+(?:[.,]\d+)?)/))) return getal(m[2]) / +m[1];
  if ((m = t.match(/^voor (\d+(?:[.,]\d+)?)/))) return getal(m[1]);
  return null;
}

/* ---------- Aldi: Next.js-pagina's met productdata in __NEXT_DATA__ ---------- */
function nextData(html) {
  const m = html.match(/<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
  if (!m) return null;
  const d = JSON.parse(m[1]);
  let api = d?.props?.pageProps?.apiData;
  if (typeof api === 'string') { try { api = JSON.parse(api); } catch { api = null; } }
  return { d, api };
}
// Zoekt overal in de data naar Algolia-productobjecten (naam + currentPrice).
function aldiProducten(node, uit = new Map()) {
  if (!node || typeof node !== 'object') return uit;
  if (Array.isArray(node)) { for (const x of node) aldiProducten(x, uit); return uit; }
  if (typeof node.name === 'string' && node.currentPrice && typeof node.currentPrice === 'object') {
    const id = String(node.objectID || node.productId || node.id || node.name);
    if (!uit.has(id)) uit.set(id, node);
  }
  for (const v of Object.values(node)) if (v && typeof v === 'object') aldiProducten(v, uit);
  return uit;
}
async function locs(url) {
  const xml = await haal(url, {}, 'text');
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].trim());
}
async function aldi() {
  const productUrls = await locs('https://www.aldi.nl/sitemaps/.aldi-nord-sitemap-products.xml');
  const linkVan = new Map();
  for (const u of productUrls) { const m = u.match(/-(\d+)\.html$/); if (m) linkVan.set(m[1], u); }
  const paginas = (await locs('https://www.aldi.nl/sitemaps/.aldi-nord-sitemap-pages.xml'))
    .filter(u => /\/producten\/.+\.html$/.test(u));
  const alle = new Map();
  let zonderData = 0;
  for (const u of ['https://www.aldi.nl/aanbiedingen.html', ...paginas]) {
    try {
      const nd = nextData(await haal(u, {}, 'text'));
      if (!nd) { zonderData++; continue; }
      aldiProducten(nd.api ?? nd.d, alle);
    } catch (e) { console.warn('aldi pagina mislukt', u, e.message); }
    await slaap(400);
  }
  const vd = vandaag();
  const producten = [], aanbod = [];
  for (const [id, p] of alle) {
    const cp = p.currentPrice || {};
    const prijs = cp.priceValue;
    if (!(prijs > 0)) continue;
    const naam = [p.brandName && !String(p.name).toUpperCase().startsWith(String(p.brandName).toUpperCase()) ? p.brandName : '', p.name].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
    const link = linkVan.get(String(p.objectID || id).replace(/\D/g, '')) || linkVan.get(String(id)) || `https://www.aldi.nl/zoeken.html?query=${encodeURIComponent(p.name)}`;
    const sz = p.salesUnit || '';
    const bp = (cp.basePrice || [])[0];
    let [ppe, eh] = bp && (bp.basePriceScale === 'kg' || bp.basePriceScale === 'l') && bp.basePriceValue > 0 ? [r2(bp.basePriceValue), bp.basePriceScale] : perEenheid(prijs, sz);
    // Lopende actie: periode in promotionPrices die vandaag geldt.
    const per = (p.promotionPrices || []).find(x => x.validFromLocalDate <= vd && vd <= x.validUntilLocalDate);
    if (per && per.priceValue > 0) {
      const label = (per.priceTagLabels || cp.priceTagLabels || {}).promoText1 || '';
      const tweeVoor = /^2\s*voor$/i.test(label.trim());
      const p1 = r2(per.priceValue / (tweeVoor ? 2 : 1));
      const strike = (per.strikePrice || cp.strikePrice)?.strikePriceValue;
      aanbod.push({ s: 'aldi', n: naam, sz, p: p1, was: strike > p1 ? r2(strike / (tweeVoor ? 2 : 1)) : null, lbl: tweeVoor ? `2 voor ${String(per.priceValue.toFixed(2)).replace('.', ',')}` : label || null, u: link, t: per.validUntilLocalDate || null });
    } else {
      producten.push([naam, link, r2(prijs), sz, ppe, eh]);
    }
  }
  if (!producten.length && !aanbod.length) throw new Error(`geen Aldi-producten gevonden (${paginas.length} pagina's, ${zonderData} zonder data)`);
  return { producten, aanbod };
}

/* ---------- Albert Heijn: app-zoekdienst met anonieme token, filter bonus ---------- */
async function ah() {
  const H = { 'User-Agent': 'Appie/8.22.3', 'X-Application': 'AHWEBSHOP' };
  const tok = (await haal('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: JSON.stringify({ clientId: 'appie' }) })).access_token;
  if (!tok) throw new Error('geen AH-token');
  const uit = new Map();
  for (let page = 0; page < 3; page++) {
    const d = await haal(`https://api.ah.nl/mobile-services/product/search/v2?sortOn=RELEVANCE&filters=${encodeURIComponent('bonus=Bonus')}&size=1000&page=${page}`, { headers: { ...H, Authorization: `Bearer ${tok}` } });
    const ps = d.products || [];
    for (const p of ps) {
      if (!p.isBonus && !p.bonusMechanism) continue;
      if (String(p.bonusEndDate || '').startsWith('2999')) continue;
      const was = p.priceBeforeBonus ?? null;
      const prijs = p.currentPrice ?? actiePrijs(p.bonusMechanism, was);
      if (!(prijs > 0)) continue;
      uit.set(p.webshopId, { s: 'ah', n: p.title, sz: p.salesUnitSize || '', p: r2(prijs), was: was > prijs ? r2(was) : null, lbl: p.bonusMechanism || 'Bonus', u: `https://www.ah.nl/producten/product/wi${p.webshopId}`, t: dagVan(p.bonusEndDate) });
    }
    if (ps.length < 1000) break;
    await slaap(500);
  }
  return [...uit.values()];
}

/* ---------- Jumbo: open GraphQL-zoekdienst, filter aanbiedingen ---------- */
async function jumbo() {
  const H = { 'content-type': 'application/json', 'apollographql-client-name': 'JUMBO_WEB-search', 'apollographql-client-version': 'master-v29.4.0-web' };
  const Q = 'query($input:ProductSearchInput!){searchProducts(input:$input){count products{id title subtitle packSizeDisplay price{price promoPrice} promotions{tags{text} end{iso}}}}}';
  const uit = [];
  for (let off = 0, count = 1; off < count && off < 4000; off += 200) {
    const j = await haal('https://www.jumbo.com/api/graphql', { method: 'POST', headers: H, body: JSON.stringify({ query: Q, variables: { input: { searchType: 'keyword', searchTerms: '*', offSet: off, limit: 200, filters: [{ key: 'Aanbiedingen', values: ['Alle aanbiedingen'] }] } } }) });
    const d = j?.data?.searchProducts;
    if (!d) throw new Error(j?.errors?.[0]?.message || 'onverwacht antwoord van Jumbo');
    count = d.count;
    for (const p of d.products || []) {
      const normaal = p.price?.price != null ? p.price.price / 100 : null;
      const promo = (p.promotions || []).find(x => x.tags?.length) || (p.promotions || [])[0];
      const tags = (promo?.tags || []).map(t => t.text).filter(t => t && !/^alleen online$/i.test(t));
      const prijs = p.price?.promoPrice != null ? p.price.promoPrice / 100 : tags.map(t => actiePrijs(t, normaal)).find(x => x != null) ?? normaal;
      if (!(prijs > 0)) continue;
      uit.push({ s: 'jumbo', n: p.title, sz: p.subtitle || p.packSizeDisplay || '', p: r2(prijs), was: normaal > prijs + .004 ? r2(normaal) : null, lbl: tags.join(', ') || null, u: `https://www.jumbo.com/zoeken/?searchTerms=${encodeURIComponent(p.title)}`, t: dagVan(promo?.end?.iso) });
    }
    if (!(d.products || []).length) break;
    await slaap(400);
  }
  return uit;
}

/* ---------- Lidl: open zoekdienst, aanbieding = oldPrice hoger dan prijs ---------- */
async function lidl() {
  const uit = new Map();
  for (let off = 0; off < 1200; off += 60) {
    const d = await haal(`https://www.lidl.nl/q/api/search?offset=${off}&fetchsize=60&locale=nl_NL&assortment=NL&version=2.1.0&category.id=10068374&q=`);
    const items = d.items || [];
    for (const it of items) {
      const x = it.gridbox?.data; if (!x?.price) continue;
      const prijs = x.price.price, oud = x.price.oldPrice;
      if (!(prijs > 0) || !(oud > prijs)) continue;
      const pct = x.price.discount?.percentageDiscount;
      uit.set(it.code || x.productId || x.fullTitle, { s: 'lidl', n: String(x.fullTitle || '').replace(/[®™]/g, '').trim(), sz: x.price.packaging?.text || '', p: r2(prijs), was: r2(oud), lbl: pct ? `-${pct}%` : null, u: x.canonicalUrl ? new URL(x.canonicalUrl, 'https://www.lidl.nl').href : 'https://www.lidl.nl/c/aanbiedingen/a10008785', t: dagVan(x.storeEndDate) });
    }
    if (items.length < 60) break;
    await slaap(400);
  }
  return [...uit.values()];
}

/* ---------- Dirk: open GraphQL-gateway, aanbiedingen per afdeling ---------- */
async function dirk() {
  const uit = new Map();
  for (let dep = 1; dep <= 20; dep++) {
    const q = `{listOffers(department:${dep},store:66){currentOffers{offerId headerText packaging offerPrice normalPrice endDate products{productId offerPrice normalPrice productInformation{headerText packaging}}}}}`;
    let j;
    try { j = await haal('https://web-gateway.dirk.nl/graphql', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) }); }
    catch (e) { console.warn('dirk afdeling', dep, e.message); continue; }
    for (const o of j?.data?.listOffers?.currentOffers || []) {
      const ps = o.products?.length ? o.products : [{ productId: o.offerId, offerPrice: o.offerPrice, normalPrice: o.normalPrice, productInformation: { headerText: o.headerText, packaging: o.packaging } }];
      for (const p of ps) {
        const prijs = p.offerPrice > 0 ? p.offerPrice : o.offerPrice;
        const was = p.normalPrice > 0 ? p.normalPrice : o.normalPrice;
        if (!(prijs > 0)) continue;
        const naam = p.productInformation?.headerText || o.headerText;
        uit.set(o.offerId + ':' + p.productId, { s: 'dirk', n: naam, sz: p.productInformation?.packaging || o.packaging || '', p: r2(prijs), was: was > prijs ? r2(was) : null, lbl: null, u: 'https://www.dirk.nl/aanbiedingen', t: dagVan(o.endDate) });
      }
    }
    await slaap(300);
  }
  if (!uit.size) throw new Error('geen Dirk-aanbiedingen gevonden');
  return [...uit.values()];
}

/* ---------- samenvoegen ---------- */
const lees = (f, leeg) => { try { return JSON.parse(fs.readFileSync(path.join(DATA, f), 'utf8')); } catch { return leeg; } };
const schrijf = (f, d) => fs.writeFileSync(path.join(DATA, f), JSON.stringify(d));

fs.mkdirSync(DATA, { recursive: true });
const nu = new Date().toISOString();
const vorigAanbod = lees('aanbiedingen.json', { offers: [] }).offers || [];
const status = lees('status.json', {});
const aanbod = {};
let aldiAssortiment = null;

for (const [id, fn] of Object.entries({ aldi, ah, jumbo, lidl, dirk })) {
  const t0 = Date.now();
  try {
    const r = await fn();
    if (id === 'aldi') { aldiAssortiment = r.producten; aanbod.aldi = r.aanbod; }
    else aanbod[id] = r;
    if (!aanbod[id].length && id !== 'aldi') throw new Error('0 aanbiedingen');
    status[id] = { ok: true, aanbiedingen: aanbod[id].length, ...(id === 'aldi' ? { producten: r.producten.length } : {}), tijd: nu, sec: Math.round((Date.now() - t0) / 1000) };
    console.log(id, JSON.stringify(status[id]));
  } catch (e) {
    // Vorige aanbiedingen van deze winkel houden, de site filtert verlopen acties zelf weg.
    aanbod[id] = vorigAanbod.filter(o => o.s === id);
    status[id] = { ...(status[id] || {}), ok: false, fout: String(e.message || e).slice(0, 300), tijd: nu };
    console.error(id, 'MISLUKT:', e.message);
  }
}

const vd = vandaag();
const offers = Object.values(aanbod).flat().filter(o => o.n && o.p > 0 && (!o.t || o.t >= vd));
schrijf('aanbiedingen.json', { updated: nu, offers });
if (aldiAssortiment?.length) schrijf('aldi.json', { updated: nu, products: aldiAssortiment });
schrijf('status.json', status);
console.log(`klaar: ${offers.length} aanbiedingen, Aldi-assortiment ${aldiAssortiment?.length ?? 'niet bijgewerkt'}`);
if (Object.values(status).every(s => !s.ok)) process.exit(1);
