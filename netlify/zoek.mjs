// Gedeelde logica voor meldingen: welke aanbiedingen passen bij de woorden op iemands lijst.
const EXCL = new Set('choco chocolade saus smaak snack snacks reep koek koekjes chips drink mix siroop limonade ijs shampoo douchegel zeep kaars wasmiddel wafels koeken toetje dessert pudding cake taart soep dip vega vegan lactosevrij biologisch bio light zero suikervrij gevulde kattenvoer hondenvoer'.split(' '));
const UNITW = new Set('g gr gram kg kilo l liter ml cl st stuk stuks per x ca pak pack fles blik zak'.split(' '));
export const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9,.]+/g, ' ').replace(/(\d)[,.](\d)/g, '$1,$2').trim();
const woorden = s => norm(s).split(' ').filter(Boolean);
const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());

// Per zoekwoord de voordeligste geldige aanbieding, alleen bij de gekozen supermarkten.
export function passend(offers, termen, winkels) {
  const d = vandaag(), uit = [];
  const geldig = offers.filter(o => o.p > 0 && (!o.v || o.v <= d) && (!o.t || o.t >= d) && (!winkels?.length || winkels.includes(o.s)));
  for (const o of geldig) o._h = o._h || woorden(o.n + ' ' + (o.sz || ''));
  for (const term of termen) {
    const t = woorden(term).filter(w => w.length > 1 && !/^\d/.test(w));
    if (!t.length) continue;
    const m = geldig.filter(o => t.every(w => o._h.some(h => h === w || (w.length >= 5 && h.endsWith(w)))) &&
      !o._h.some(h => !t.includes(h) && EXCL.has(h)) &&
      o._h.filter(h => !/^[\d,.%+]+[a-z]*$/.test(h) && !UNITW.has(h)).length <= t.length + 3);
    if (!m.length) continue;
    m.sort((a, b) => (a.pp ?? a.p * 1000) - (b.pp ?? b.p * 1000));
    uit.push({ term, o: m[0] });
  }
  return uit;
}
export const sleutelVan = o => `${o.s}|${norm(o.n)}|${o.p}|${o.t || ''}`;
