// Haalt het Aldi-assortiment en de aanbiedingen van een aantal supermarkten op en schrijft:
//   data/aldi.json         { updated, products: [[naam, link, prijs, inhoud, prijsPerEenheid, eenheid], ...] }
//   data/aanbiedingen.json { updated, offers: [{ s, n, sz, p, was, lbl, u, t }, ...] }
//   data/status.json       per winkel het aantal en een eventuele foutmelding
// Elke winkel staat los: als er een faalt, blijven de vorige gegevens van die winkel staan.
// Draait met Node 22 zonder extra pakketten.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { categorieVan, zonderAccent } from './categorie.mjs';

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data');
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const slaap = ms => new Promise(r => setTimeout(r, ms));
const r2 = n => (n == null || !isFinite(n) ? null : Math.round(n * 100) / 100);
const getal = s => parseFloat(String(s).replace(',', '.'));
// Productnaam als stukje url: "Milka Reep 100 g" -> "milka-reep-100-g". Jumbo en Dirk vinden het product op het id.
const slug = s => String(s || 'product').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'product';
const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());
const dagVan = v => {
  if (v == null || v === '') return null;
  const d = typeof v === 'number' ? new Date(v < 1e12 ? v * 1000 : v) : new Date(v);
  return isNaN(d) ? null : new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(d);
};

async function haal(url, opts = {}, soort = 'json', pogingen = 3) {
  let fout;
  for (let poging = 1; poging <= pogingen; poging++) {
    try {
      const r = await fetch(url, { ...opts, headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL', ...(opts.headers || {}) }, signal: AbortSignal.timeout(30_000) });
      if (r.status === 429 || r.status >= 500) throw new Error(`HTTP ${r.status}`);
      if (!r.ok) { const e = new Error(`HTTP ${r.status} ${url}`); e.stop = true; throw e; }
      return soort === 'json' ? await r.json() : await r.text();
    } catch (e) {
      fout = e;
      if (e.stop) break;
      await slaap(3000 * poging);
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
  // Productpagina's uit de sitemap die nog niet gezien zijn ook bekijken (Aldi laat online vooral actieartikelen zien).
  const gezien = new Set([...alle.values()].map(p => String(p.objectID || '').replace(/\D/g, '')));
  let extra = 0;
  for (const [id, u] of linkVan) {
    if (gezien.has(id) || extra >= 1500) continue;
    extra++;
    try { const nd = nextData(await haal(u, {}, 'text')); if (nd) aldiProducten(nd.api ?? nd.d, alle); } catch (e) { if (extra < 5) console.warn('aldi product mislukt', u, e.message); }
    await slaap(150);
  }
  console.log(`aldi: ${paginas.length} categoriepagina's, ${extra} productpagina's, ${alle.size} producten gevonden`);
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
      // Ook in het assortiment, zodat Aldi meedoet in zoeken en totalen.
      producten.push([naam, link, p1, sz, ...perEenheid(p1, sz)]);
      aanbod.push({ s: 'aldi', k: String(p.objectID || id).replace(/\D/g, '') || null, n: naam, sz, p: p1, was: strike > p1 ? r2(strike / (tweeVoor ? 2 : 1)) : null, lbl: tweeVoor ? `2 voor ${String(per.priceValue.toFixed(2)).replace('.', ',')}` : label || null, u: link, t: per.validUntilLocalDate || null });
    } else {
      producten.push([naam, link, r2(prijs), sz, ppe, eh]);
    }
  }
  if (!producten.length && !aanbod.length) throw new Error(`geen Aldi-producten gevonden (${paginas.length} pagina's, ${zonderData} zonder data)`);
  return { producten, aanbod };
}

/* ---------- Albert Heijn: app-zoekdienst met anonieme token, filter bonus ---------- */
// AH geeft soms een tijdelijke 503; daarom meer pogingen met langere pauzes.
async function ah() {
  const H = { 'User-Agent': 'Appie/8.22.3', 'X-Application': 'AHWEBSHOP' };
  const tok = (await haal('https://api.ah.nl/mobile-auth/v1/auth/token/anonymous', { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: JSON.stringify({ clientId: 'appie' }) }, 'json', 6)).access_token;
  if (!tok) throw new Error('geen AH-token');
  const uit = new Map();
  // De zoekdienst geeft maximaal 3000 resultaten (3 pagina's van 1000); daarna antwoordt hij met 400.
  for (let page = 0; page < 3; page++) {
    let d;
    try { d = await haal(`https://api.ah.nl/mobile-services/product/search/v2?sortOn=RELEVANCE&filters=${encodeURIComponent('bonus=Bonus')}&size=1000&page=${page}`, { headers: { ...H, Authorization: `Bearer ${tok}` } }, 'json', 6); }
    catch (e) { if (uit.size && /HTTP 400/.test(e.message)) break; throw e; }
    const ps = d.products || [];
    for (const p of ps) {
      if (!p.isBonus && !p.bonusMechanism) continue;
      if (String(p.bonusEndDate || '').startsWith('2999')) continue;
      const was = p.priceBeforeBonus ?? null;
      const prijs = p.currentPrice ?? actiePrijs(p.bonusMechanism, was);
      if (!(prijs > 0)) continue;
      uit.set(p.webshopId, { s: 'ah', n: p.title, sz: p.salesUnitSize || '', p: r2(prijs), was: was > prijs ? r2(was) : null, lbl: p.bonusMechanism || 'Bonus', u: `https://www.ah.nl/producten/product/wi${p.webshopId}`, t: dagVan(p.bonusEndDate), k: `wi${p.webshopId}`, sc: [p.mainCategory, p.subCategory].filter(Boolean).join(' ') });
    }
    if (ps.length < 1000 || (d.page && page + 1 >= d.page.totalPages)) break;
    await slaap(800);
  }
  // Bonus van volgende week: AH zet die vanaf 'nextPeriodVisibleFrom' (meestal vrijdag) online.
  try {
    const A = { headers: { ...H, Authorization: `Bearer ${tok}` } };
    const meta = await haal('https://api.ah.nl/mobile-services/bonuspage/v3/metadata', A, 'json', 3);
    const vd = vandaag();
    for (const per of (meta?.periods || []).filter(x => x.bonusStartDate > vd)) {
      const segs = new Set();
      const urls = [...new Set((per.tabs || []).flatMap(t => (t.urlMetadataList || []).map(x => x.url)))];
      for (const u of urls) {
        let d; try { d = await haal('https://api.ah.nl/mobile-services/' + u, A, 'json', 2); } catch (e) { continue; }
        for (const x of d?.bonusGroupOrProducts || []) { const g = x.bonusGroup; if (g?.segmentId) segs.add(g.segmentId); if (x.product?.bonusSegmentId) segs.add(x.product.bonusSegmentId); }
        await slaap(300);
      }
      let n = 0;
      for (const sid of segs) {
        let g; try { g = await haal(`https://api.ah.nl/mobile-services/bonuspage/v1/segment?segmentId=${sid}&date=${per.bonusStartDate}`, A, 'json', 2); } catch (e) { continue; }
        for (const p of g?.products || []) {
          const was = p.priceBeforeBonus ?? null;
          const mech = p.bonusMechanism || g.discountDescription;
          const prijs = p.currentPrice ?? actiePrijs(mech, was);
          if (!(prijs > 0) || uit.has(p.webshopId)) continue;
          uit.set(p.webshopId, { s: 'ah', n: p.title, sz: p.salesUnitSize || '', p: r2(prijs), was: was > prijs ? r2(was) : null, lbl: mech || 'Bonus', u: `https://www.ah.nl/producten/product/wi${p.webshopId}`, t: dagVan(p.bonusEndDate || per.bonusEndDate), v: dagVan(p.bonusStartDate || per.bonusStartDate), k: `wi${p.webshopId}`, sc: [p.mainCategory, p.subCategory].filter(Boolean).join(' ') });
          n++;
        }
        await slaap(200);
      }
      console.log('AH volgende week:', per.bonusStartDate, segs.size, 'bonusgroepen,', n, 'producten');
    }
  } catch (e) { console.warn('AH volgende week niet gelukt:', e.message); }
  return [...uit.values()];
}

/* ---------- PLUS: OutSystems-dataservice van de actiepagina ---------- */
// De api-versie staat in het script van de actiepagina; die lezen we elke keer opnieuw, zodat een nieuwe PLUS-versie niets breekt.
async function plus() {
  const B = 'https://www.plus.nl';
  const H = { 'Content-Type': 'application/json; charset=UTF-8', 'X-CSRFToken': 'T6C+9iB49TLra4jEsMeSckDMNhQ=', 'OutSystems-locale': 'nl-NL', Referer: `${B}/aanbiedingen` };
  const tok = (await haal(`${B}/moduleservices/moduleversioninfo`)).versionToken;
  const info = (await haal(`${B}/moduleservices/moduleinfo`)).manifest?.urlVersions || {};
  const pad = Object.keys(info).find(u => /ECP_Composition_CW\.Promotions\.Promotion_LP_Content_TF\.mvc\.js$/.test(u));
  let api = 'JLLMwEcN2MnU+RXNqWqRIQ';
  if (pad) { const js = await haal(B + pad + info[pad], {}, 'text'); api = (js.match(/DataActionGetPromotionList", "[^"]+", "([^"]+)"/) || [])[1] || api; }
  const vars = { IsShowData: true, StoreNumber: 0, StoreChannel: '', CheckoutId: '', IsOrderEditMode: false, OrderEditId: '', PromotionPeriodId: 0, HideDummy: false, IsDesktop: true, IsTablet: false, IsPhone: false, OneWelcomeUserId: '', IsCustomerUnderAge: false, UserStoreId: '0', ItemsInCartJSON: '', IsTimetraveler: false, IsNextWeekPromotions: false };
  const vraag = async extra => (await haal(`${B}/screenservices/ECP_Composition_CW/Promotions/Promotion_LP_Content_TF/DataActionGetPromotionList`, { method: 'POST', headers: H, body: JSON.stringify({ versionInfo: { moduleVersion: tok, apiVersion: api }, viewName: 'MainFlow.Promotions', screenData: { variables: { ...vars, ...extra } } }) })).data;
  const vd = vandaag();
  const alle = new Map();
  const catVan = new Map();
  // Deze week en (als die al online staat) volgende week; acties die nog niet begonnen zijn, krijgen een startdatum mee.
  for (const extra of [{}, { IsNextWeekPromotions: true }]) {
    let d;
    try { d = await vraag(extra); } catch (e) { if (!alle.size) throw e; continue; }
    for (const cat of d?.PromotionOfferList?.List || []) for (const o of cat.Category?.Offers?.List || []) {
      if (o.IsFreeDeliveryOffer || !o.EndDate || o.EndDate < vd) continue;
      alle.set(o.Slug + o.StartDate, o); catVan.set(o.Slug + o.StartDate, cat.Category?.CategoryLabel || '');
    }
    await slaap(500);
  }
  const uit = [];
  for (const o of alle.values()) {
    const lbl = String(o.DisplayInfo_Label || '').replace(/\s+/g, ' ').trim();
    const l = lbl.toLowerCase().replace(/(\d)\.(\d)/g, '$1,$2');
    const nieuw = getal(o.NewPrice), orig = getal(o.PriceOriginal_Product), laag = getal(o.PriceOriginal_Lowest);
    let p = null, was = null, m;
    if ((m = l.match(/(\d+)\s*\+\s*(\d+) gratis/))) {
      const n = +m[1] + +m[2];
      if (o.IsSingleProduct && orig > 0) { p = actiePrijs(l, orig); was = orig; }
      else if (nieuw > 0) { p = nieuw / n; was = laag > 0 ? laag / n : null; }
    } else if (/voor \d/.test(l) || /halve prijs|% korting/.test(l)) {
      p = actiePrijs(l, orig > 0 ? orig : null) ?? (nieuw > 0 ? nieuw : null); was = orig > 0 ? orig : null;
    } else if (nieuw > 0) { p = nieuw; was = orig > nieuw ? orig : laag > nieuw ? laag : null; }
    if (!(p > 0)) continue;
    const naam = [o.Brand, o.Name].map(x => String(x || '').trim()).filter(Boolean).join(' ').replace(/\s+/g, ' ');
    const sz = String(o.Variant || o.Package || (o.IsSingleProduct ? (o.Slug.match(/-((?:schaal|zak|bakje|net|pak|fles|kuipje|doos|blik|pot|kg|stuk|tray)[a-z-]*-[\d,.]+-[a-z]+)-\d+$/) || [])[1]?.replace(/-/g, ' ') : '') || '').trim();
    uit.push({ s: 'plus', n: naam || lbl, sz, p: r2(p), was: was > p + .004 ? r2(was) : null, lbl: lbl ? lbl.charAt(0) + lbl.slice(1).toLowerCase() : null, u: o.IsSingleProduct ? `${B}/product/${o.Slug}` : `${B}/aanbiedingen`, t: o.EndDate, v: o.StartDate > vd ? o.StartDate : null, k: o.IsSingleProduct ? String(o.Product_SKU) : null, sc: catVan.get(o.Slug + o.StartDate) });
  }
  if (!uit.length) throw new Error('0 PLUS-aanbiedingen');
  return uit;
}

/* ---------- Hoogvliet: Next.js-pagina's met de actieweek per productgroep ---------- */
function nextJson(html) {
  const m = html.match(/<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
  return m ? JSON.parse(m[1]) : null;
}
async function hoogvliet() {
  const BASE = 'https://www.hoogvliet.com';
  const eerste = nextJson(await haal(`${BASE}/aanbiedingen`, {}, 'text'));
  const periodes = eerste?.props?.pageProps?.promotionPeriods || [];
  const vd = vandaag();
  const per = periodes.find(p => String(p.validFrom).slice(0, 10) <= vd && vd <= String(p.validTo).slice(0, 10)) || periodes[0];
  if (!per) throw new Error('geen Hoogvliet-actieweek gevonden');
  const tot = String(per.validTo).slice(0, 10);
  const items = new Map();
  const neem = p => {
    for (const g of p?.groups || []) for (const it of g.items || []) {
      const sku = it.sku || it.first_child_sku || it.id;
      if (!items.has(sku)) items.set(sku, { ...it, _groep: g.name || g.slug || '' });
    }
  };
  neem(per);
  for (const g of per.groups || []) {
    try {
      const d = nextJson(await haal(`${BASE}/aanbiedingen/${g.slug || g.id}`, {}, 'text'));
      const pp = (d?.props?.pageProps?.promotionPeriods || []).find(x => x.weekNr === per.weekNr);
      neem(pp);
    } catch (e) { console.warn('hoogvliet groep mislukt', g.slug, e.message); }
    await slaap(300);
  }
  const uit = [];
  for (const it of items.values()) {
    const pr = it.price_range?.minimum_price || {};
    const prijs = pr.final_price?.value ?? getal(it.meta_promotion_price?.value);
    const was = pr.regular_price?.value ?? getal(it.meta_original_price?.value);
    if (!(prijs > 0)) continue;
    const merk = it.brand?.value || it.display_name || '';
    const naam = (merk && !String(it.name).toLowerCase().startsWith(merk.toLowerCase()) ? merk + ' ' : '') + it.name;
    const st = it.sub_title_attributes || {};
    const sz = it.promotion_meta_data?.promotie_beschrijving || (st.volume ? `${st.volume} ${String(st.unit || '').toLowerCase()}` : '');
    const link = it.first_child_product_link || it.product_link;
    uit.push({ s: 'hoogvliet', n: naam.replace(/\s+/g, ' ').trim(), sz, p: r2(prijs), was: was > prijs + .004 ? r2(was) : null, lbl: [it.promotion_meta_data?.korting_label, it.discount_label].find(x => x && !/^per\b/i.test(x)) || null, u: link ? BASE + link : `${BASE}/aanbiedingen`, t: tot, sc: [it._groep, ...(it.categories || []).map(c => c.name)].join(' '), k: link ? link.replace(/^\/product\//, '').replace(/-\d+$/, '') : null });
  }
  if (!uit.length) throw new Error('geen Hoogvliet-aanbiedingen gevonden');
  return uit;
}

/* ---------- Poiesz: Nuxt-pagina, aanbiedingen staan in de __NUXT_DATA__-payload ---------- */
// Nuxt 3 zet de data als platte lijst met verwijzingen (indexen); dit zet hem terug in objecten.
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
  if (!node || typeof node !== 'object' || diepte > 30) return null;
  if (test(node)) return node;
  for (const v of Array.isArray(node) ? node : Object.values(node)) { const r = zoek(v, test, diepte + 1); if (r) return r; }
  return null;
}
async function poiesz() {
  const root = nuxtData(await haal('https://webwinkel.poiesz-supermarkten.nl/aanbiedingen', {}, 'text'));
  const blok = zoek(root, x => x.validFrom && Array.isArray(x.categories) && x.categories.some(c => Array.isArray(c?.offers)));
  if (!blok) throw new Error('geen Poiesz-aanbiedingen in de pagina');
  const tot = dagVan(blok.validUntil);
  // validUntil is het begin van de dag ná de laatste actiedag.
  const t = tot ? new Date(new Date(tot + 'T12:00:00Z').getTime() - 864e5).toISOString().slice(0, 10) : null;
  const uit = [];
  for (const c of blok.categories) for (const o of c.offers || []) {
    const regel1 = String(o.offerTypeLine1 || '').trim(), regel2 = String(o.offerTypeLine2 || '').trim().toLowerCase();
    const prods = (o.overviewProducts || []).filter(Boolean);
    const een = prods.length === 1 ? prods[0] : null;
    const prijsVan = o.newPriceLow;
    let p = null, was = null, lbl = null;
    if (/^\d+\s*\+\s*\d+$/.test(regel1)) { lbl = `${regel1} gratis`; was = prijsVan; p = actiePrijs(lbl, prijsVan); }
    else if (/^\d+$/.test(regel1) && regel2 === 'voor') { lbl = `${regel1} voor ${String(prijsVan?.toFixed?.(2) ?? prijsVan).replace('.', ',')}`; p = prijsVan / +regel1; was = een?.strikeThroughPrice ?? null; }
    else if (/%/.test(regel1 + regel2)) { lbl = `${regel1} ${regel2}`.trim(); p = een?.price ?? prijsVan; was = een?.strikeThroughPrice ?? o.oldPriceLow; }
    else { p = prijsVan ?? een?.price; was = een?.strikeThroughPrice ?? o.oldPriceLow ?? null; }
    if (!(p > 0)) continue;
    const naam = String(o.commercialTextLine1 || een?.name || '').replace(/\s+/g, ' ').trim();
    const sz = String(o.commercialTextDetailsLine2 || o.commercialTextDetailsLine1 || een?.packageDescription || '').replace(/\s+/g, ' ').trim();
    uit.push({ s: 'poiesz', n: naam, sz, p: r2(p), was: was > p + .004 ? r2(was) : null, lbl, u: een ? `https://webwinkel.poiesz-supermarkten.nl/boodschappen/producten/${een.id}` : 'https://webwinkel.poiesz-supermarkten.nl/aanbiedingen', t, k: een ? String(een.id) : null, sc: c.name || '' });
  }
  if (!uit.length) throw new Error('0 Poiesz-aanbiedingen');
  return uit;
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
      uit.push({ s: 'jumbo', n: p.title, sz: p.subtitle || p.packSizeDisplay || '', p: r2(prijs), was: normaal > prijs + .004 ? r2(normaal) : null, lbl: tags.join(', ') || null, u: `https://www.jumbo.com/producten/${slug(p.title)}-${p.id}`, t: dagVan(promo?.end?.iso), k: String(p.id) });
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
  // De actiepagina zelf: daar staan ook de Lidl Plus-acties en de acties van volgende week (vanaf maandag).
  try {
    const page = await haal('https://www.lidl.nl/c/aanbiedingen/a10008785', {}, 'text');
    const vd = vandaag();
    const ontsnap = s => s.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    for (const m of page.matchAll(/data-grid-data="([^"]*)"/g)) {
      let x; try { x = JSON.parse(ontsnap(m[1])); } catch { continue; }
      const sleutel = x.productId || x.erpNumber || x.fullTitle;
      if (!x.fullTitle || uit.has(sleutel)) continue;
      const pr = x.price || {}, lp = (x.lidlPlus || [])[0];
      let p = pr.price, was = pr.oldPrice || pr.discount?.deletedPrice || null, lbl = pr.discount?.percentageDiscount ? `-${pr.discount.percentageDiscount}%` : null;
      if (!(p > 0) && lp?.price?.price > 0) {
        p = lp.price.price; lbl = `${lp.highlightText || ''} ${lp.lidlPlusText || 'met Lidl Plus'}`.trim();
        const pct = +(String(lp.highlightText || '').match(/(\d+)\s*%/) || [])[1];
        if (pct > 0 && pct < 90) was = p / (1 - pct / 100);
      }
      if (!(p > 0)) continue;
      const van = dagVan(x.storeStartDate), tot = dagVan(x.storeEndDate);
      uit.set(sleutel, { s: 'lidl', n: String(x.fullTitle).replace(/[®™]/g, '').replace(/\s+/g, ' ').trim(), sz: pr.packaging?.text || lp?.price?.packaging?.text || '', p: r2(p), was: was > p + .004 ? r2(was) : null, lbl, u: x.canonicalUrl ? new URL(x.canonicalUrl, 'https://www.lidl.nl').href : 'https://www.lidl.nl/c/aanbiedingen/a10008785', t: tot, v: van && van > vd ? van : null });
    }
  } catch (e) { console.warn('lidl actiepagina mislukt', e.message); }
  if (!uit.size) throw new Error('geen Lidl-aanbiedingen gevonden');
  return [...uit.values()];
}

/* ---------- Dirk en DekaMarkt: zelfde GraphQL-gateway (Detailresult), aanbiedingen per afdeling ---------- */
async function detailresult(id, gateway, winkel, link) {
  const uit = new Map();
  for (let dep = 1; dep <= 20; dep++) {
    const velden = 'offerId headerText packaging offerPrice normalPrice startDate endDate products{productId offerPrice normalPrice productInformation{headerText packaging}}';
    // Ook de acties die nog moeten beginnen (bijvoorbeeld 'vanaf woensdag' of volgende week).
    const q = `{listOffers(department:${dep},store:${winkel}){currentOffers{${velden}} upcomingOffers{${velden}}}}`;
    let j;
    try { j = await haal(gateway, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) }); }
    catch (e) { j = null; console.warn(id, 'afdeling', dep, 'komende acties niet beschikbaar:', e.message); }
    if (!j?.data?.listOffers) { try { j = await haal(gateway, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: `{listOffers(department:${dep},store:${winkel}){currentOffers{${velden}}}}` }) }); } catch (e) { console.warn(id, 'afdeling', dep, e.message); continue; } }
    const vdag = vandaag();
    for (const o of [...(j?.data?.listOffers?.currentOffers || []), ...(j?.data?.listOffers?.upcomingOffers || [])]) {
      const start = dagVan(o.startDate);
      // Als geen enkel product een eigen actieprijs heeft, geldt de actie voor de combinatie: dan tonen we de actie zelf.
      const eigen = (o.products || []).filter(p => p && p.offerPrice > 0 && p.offerPrice < p.normalPrice - .004);
      const ps = eigen.length ? eigen : o.products?.length === 1 ? o.products : [{ productId: null, offerPrice: o.offerPrice, normalPrice: o.normalPrice, productInformation: { headerText: o.headerText, packaging: o.packaging } }];
      for (const p of ps) {
        if (!p) continue;
        // Bij een actie over meerdere producten staat de actieprijs soms alleen bij de actie zelf.
        const prijs = p.offerPrice > 0 && p.offerPrice < (p.normalPrice || 1e9) ? p.offerPrice : o.offerPrice > 0 ? o.offerPrice : p.offerPrice;
        const was = p.normalPrice > prijs ? p.normalPrice : o.normalPrice;
        if (!(prijs > 0)) continue;
        const naam = p.productInformation?.headerText || o.headerText;
        uit.set(o.offerId + ':' + p.productId, { s: id, n: naam, sz: p.productInformation?.packaging || o.packaging || '', p: r2(prijs), was: was > prijs + .004 ? r2(was) : null, lbl: null, u: link(naam, p.productId), t: dagVan(o.endDate), v: start && start > vdag ? start : null, k: p.productId ? String(p.productId) : null });
      }
    }
    await slaap(300);
  }
  if (!uit.size) throw new Error(`geen ${id}-aanbiedingen gevonden`);
  return [...uit.values()];
}
const dirk = () => detailresult('dirk', 'https://web-gateway.dirk.nl/graphql', 66, (naam, id) => id ? `https://www.dirk.nl/boodschappen/x/x/${slug(naam)}/${id}` : 'https://www.dirk.nl/aanbiedingen');
// DekaMarkt-productlinks werken niet los; daarom naar de actiepagina.
const dekamarkt = () => detailresult('dekamarkt', 'https://web-deka-gateway.dekamarkt.nl/graphql', 283, () => 'https://www.dekamarkt.nl/aanbiedingen');

/* ---------- categorie per aanbieding (zelfde namen als de categorieën op de site) ---------- */
// Volgorde telt: specifieke groepen eerst, zodat "pindakaas" niet bij Kaas en "appelsap" niet bij Groente komt.
// Categorieën van aanbiedingen staan in categorie.mjs (ook gebruikt om bestaande data opnieuw in te delen).

/* ---------- netjes maken: maten, prijs per eenheid, dubbele acties ---------- */
// "520 Mililiters" -> "520 ml", "1.25 KGrams" -> "1,25 kg", "15 Stuks" -> "15 stuks"
function netteMaat(sz) {
  let t = String(sz || '').replace(/\s+/g, ' ').trim();
  if (!t) return '';
  t = t.replace(/(\d)\s*(?:mililiters?|milliliters?|ml)\b/gi, '$1 ml').replace(/(\d)\s*(?:liters?|ltr|l)\b/gi, '$1 l')
    .replace(/(\d)\s*(?:kgrams?|kilograms?|kilo's?|kilo|kg)\b/gi, '$1 kg').replace(/(\d)\s*(?:grams?|gr|g)\b/gi, '$1 g')
    .replace(/(\d)\s*(?:centiliters?|cl)\b/gi, '$1 cl').replace(/\bstuks\b/gi, 'stuks').replace(/\bstuk\b/gi, 'stuk')
    .replace(/(\d)\.(\d)/g, '$1,$2');
  return /^[A-Z0-9 ,.]+$/.test(t) && /[A-Z]{3}/.test(t) ? t.toLowerCase() : t;
}
const sleutelNaam = s => zonderAccent(s).replace(/[^a-z0-9]+/g, ' ').trim();
function opschonen(lijst) {
  const gezien = new Map();
  for (const o of lijst) {
    o.n = String(o.n || '').replace(/[®™]/g, '').replace(/\s+/g, ' ').trim();
    o.sz = netteMaat(o.sz);
    if (o.sz && sleutelNaam(o.n).endsWith(sleutelNaam(o.sz))) o.sz = '';
    const [pp, eh] = perEenheid(o.p, o.sz || o.n);
    if (pp != null && pp < 2000) { o.pp = pp; o.eh = eh; }
    if (o.was != null && !(o.was > o.p + .004)) o.was = null;
    // Labels als "VOOR 0.99" of "1+1 GRATIS" -> "Voor 0,99", "1+1 gratis"
    if (o.lbl) {
      let l = String(o.lbl).replace(/\s+/g, ' ').trim().replace(/(\d)\.(\d)/g, '$1,$2');
      if (l === l.toUpperCase()) l = l.charAt(0) + l.slice(1).toLowerCase();
      o.lbl = l || null;
    }
    if (!o.k) delete o.k;
    if (!o.v) delete o.v;
    // Zelfde winkel, naam, maat en prijs = dubbel (komt voor bij acties die in twee afdelingen staan).
    const sl = [o.s, sleutelNaam(o.n), o.sz, o.p].join('|');
    const oud = gezien.get(sl);
    if (!oud || (!oud.k && o.k)) gezien.set(sl, o);
  }
  return [...gezien.values()];
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

// Alle winkels tegelijk; Aldi duurt het langst (honderden pagina's), de rest is in een paar minuten klaar.
const WINKELS = { aldi, ah, jumbo, lidl, plus, dirk, dekamarkt, hoogvliet, poiesz };
const alleen = (process.env.WINKELS || '').split(',').filter(Boolean);
await Promise.all(Object.entries(WINKELS).filter(([id]) => !alleen.length || alleen.includes(id)).map(async ([id, fn]) => {
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
}));
// Winkels die deze keer niet zijn opgehaald (WINKELS=...), houden hun vorige acties.
const overgeslagen = new Set(vorigAanbod.map(o => o.s).filter(id => !(id in aanbod)));
for (const o of vorigAanbod) if (overgeslagen.has(o.s)) (aanbod[o.s] ||= []).push(o);

const vd = vandaag();
const offers = opschonen(Object.values(aanbod).flat().filter(o => o.n && o.p > 0 && (!o.t || o.t >= vd))).map(({ sc, ...o }) => {
  // Eerst op de productnaam; lukt dat niet, dan op de afdeling van de supermarkt zelf.
  let c = categorieVan(o.n + ' ' + (o.sz || ''));
  if (c === 'Overig' && sc) c = categorieVan(sc);
  return { ...o, c };
});
schrijf('aanbiedingen.json', { updated: nu, offers });
if (aldiAssortiment?.length) schrijf('aldi.json', { updated: nu, products: aldiAssortiment });
schrijf('status.json', status);
console.log(`klaar: ${offers.length} aanbiedingen, Aldi-assortiment ${aldiAssortiment?.length ?? 'niet bijgewerkt'}`);
const tel = {}; for (const o of offers) tel[o.c] = (tel[o.c] || 0) + 1; console.log('categorieën', JSON.stringify(tel));
if (Object.values(status).every(s => !s.ok)) process.exit(1);
