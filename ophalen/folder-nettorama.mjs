// Gedeeld door ophalen/nettorama.mjs (GitHub) en netlify/functions/nettorama-folder-background.mjs (Netlify):
// de Nettorama-weekfolder (Publitas) vinden en per pagina met AI de acties uitlezen.
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const GROEP = 'bv-nettorama-verbruikersmarkten';
const MODEL = process.env.FOLDER_MODEL || 'claude-sonnet-5-5';
const iso = d => d.toISOString().slice(0, 10);

export async function haal(url, soort = 'text') {
  for (let poging = 1; poging <= 3; poging++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA, 'Accept-Language': 'nl-NL' }, signal: AbortSignal.timeout(30_000) });
      if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
      return soort === 'json' ? await r.json() : await r.text();
    } catch (e) { if (poging === 3) throw e; await new Promise(r => setTimeout(r, 3000 * poging)); }
  }
}

// "nettorama-folder-wk48-2026" -> maandag t/m zondag van week 48 van 2026 (ISO-week).
export function weekVan(slug) {
  const m = slug.match(/wk-?(\d{1,2})-(\d{4})/);
  if (!m) return null;
  const [wk, jaar] = [+m[1], +m[2]];
  const jan4 = new Date(Date.UTC(jaar, 0, 4));
  const ma = new Date(jan4); ma.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7) + (wk - 1) * 7);
  const zo = new Date(ma); zo.setUTCDate(ma.getUTCDate() + 6);
  return { van: iso(ma), tot: iso(zo) };
}

const OPDRACHT = `Dit is een pagina uit de weekfolder van supermarkt Nettorama. Daaronder staat de tekst die op de pagina staat (in losse stukjes; "1" en "49" naast elkaar is € 1,49).
Antwoord ALLEEN met JSON, zonder uitleg: {"acties": [{"naam": "...", "inhoud": "500 g" of null, "prijs": 1.49, "was": 2.19 of null, "actie": "2e halve prijs" of null}]}
Regels:
- Alleen boodschappen en drogisterij met een duidelijke prijs. Geen non-food zoals kleding of gereedschap.
- "naam": merk en product zoals in de folder, zonder hoofdletters-schreeuw ("MAASLANDER" wordt "Maaslander").
- "prijs": wat je voor ÉÉN verpakking betaalt met de actie. Bij "2 voor 3,00" is dat 1.50. Bij "1+1 gratis" de helft van de gewone prijs. Bij "per kilo" is "inhoud" "1 kg".
- Kies je bij meerdere smaken of soorten één regel met de gezamenlijke naam ("Maaslander gesneden kaas jong, jong belegen of belegen").
- "was": alleen als de folder een oude of van-prijs noemt.
- Twijfel je over een prijs, laat dat product dan weg.`;

async function leesPagina(sleutel, beeld, tekst) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST', signal: AbortSignal.timeout(120_000),
    headers: { 'x-api-key': sleutel, 'anthropic-version': '2026-10-21', 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, max_tokens: 4000, messages: [{ role: 'user', content: [
      { type: 'image', source: { type: 'url', url: beeld } },
      { type: 'text', text: OPDRACHT + '\n\nTekst op de pagina:\n' + String(tekst || '').slice(0, 6000) },
    ] }] }),
  });
  if (!r.ok) throw new Error(`AI HTTP ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const d = await r.json();
  const t = (d.content || []).map(c => c.text || '').join('');
  const j = JSON.parse(t.slice(t.indexOf('{'), t.lastIndexOf('}') + 1));
  return (j.acties || []).filter(a => a && a.naam && typeof a.prijs === 'number' && a.prijs > 0 && a.prijs < 100);
}

export async function leesFolder(slug, sleutel) {
  const basis = `https://view.publitas.com/${GROEP}/${slug}`;
  const spreads = await haal(`${basis}/spreads.json`, 'json');
  const week = weekVan(slug);
  const acties = [];
  for (const sp of spreads) for (const pg of sp.pages || []) {
    const img = pg.images?.at1600 || pg.images?.at1200 || pg.images?.at2000;
    if (!img) continue;
    try {
      const lijst = await leesPagina(sleutel, new URL(img, 'https://view.publitas.com').href, pg.text);
      for (const a of lijst) acties.push({ s: 'nettorama', n: String(a.naam).replace(/\s+/g, ' ').trim(), sz: a.inhoud || '', p: Math.round(a.prijs * 100) / 100,
        was: a.was && a.was > a.prijs ? Math.round(a.was * 100) / 100 : null, lbl: a.actie || 'Folderaanbieding',
        u: `${basis}/page/${pg.number}`, t: week?.tot || null, v: week?.van || null });
      console.log(`nettorama ${slug} pagina ${pg.number}: ${lijst.length} acties`);
    } catch (e) { console.warn(`nettorama ${slug} pagina ${pg.number} mislukt:`, e.message); }
  }
  return { ...week, acties };
}

export const vandaag = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam' }).format(new Date());
export async function vindFolders() {
  const html = await haal('https://www.nettorama.nl/actiefolder');
  const slugs = [...new Set([...html.matchAll(new RegExp(`view\\.publitas\\.com/${GROEP}/([a-z0-9-]+)`, 'g'))].map(m => m[1]))];
  if (!slugs.length) throw new Error('geen folder gevonden op nettorama.nl/actiefolder');
  return slugs;
}
// Nieuwe folders uitlezen (bestaande overslaan), verlopen weggooien. Geeft het bijgewerkte geheel terug.
export async function bijwerken(bewaard, sleutel, log = console.log) {
  bewaard = bewaard && bewaard.folders ? bewaard : { folders: {} };
  for (const slug of await vindFolders()) {
    if (bewaard.folders[slug]?.acties?.length || !sleutel) continue;
    const f = await leesFolder(slug, sleutel);
    if (f.acties.length) { bewaard.folders[slug] = f; log(`nettorama: ${slug} uitgelezen, ${f.acties.length} acties`); }
  }
  const vd = vandaag();
  for (const [slug, f] of Object.entries(bewaard.folders)) if (f.tot && f.tot < vd) delete bewaard.folders[slug];
  return bewaard;
}
export function lopend(bewaard) {
  const vd = vandaag();
  return Object.values(bewaard?.folders || {}).flatMap(f => f.acties).filter(o => !o.t || o.t >= vd).map(o => ({ ...o, v: o.v && o.v > vd ? o.v : null }));
}
