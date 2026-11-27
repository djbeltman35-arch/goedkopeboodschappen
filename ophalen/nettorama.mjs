// Nettorama-aanbiedingen uit de weekfolder (zie folder-nettorama.mjs).
// Het uitlezen met AI gebeurt op Netlify (daar staat de AI-sleutel): netlify/functions/nettorama-folder-background.mjs
// leest elke nieuwe folder één keer uit en https://boodschappenvergelijk.nl/api/nettorama geeft de acties.
// Staat er toch een ANTHROPIC_API_KEY in GitHub, dan leest dit script de folder zelf uit.
// Laatste resultaat staat in data/nettorama-folder.json, zodat een storing niets wegvaagt.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { bijwerken, lopend } from './folder-nettorama.mjs';

const BESTAND = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data', 'nettorama-folder.json');

export async function nettorama() {
  let bewaard = (() => { try { return JSON.parse(fs.readFileSync(BESTAND, 'utf8')); } catch { return { folders: {} }; } })();
  if (process.env.ANTHROPIC_API_KEY) bewaard = await bijwerken(bewaard, process.env.ANTHROPIC_API_KEY);
  else {
    const r = await fetch('https://boodschappenvergelijk.nl/api/nettorama', { signal: AbortSignal.timeout(30_000) });
    if (!r.ok) throw new Error(`api/nettorama HTTP ${r.status}`);
    const d = await r.json();
    if (d?.folders && Object.keys(d.folders).length) bewaard = d;
  }
  fs.writeFileSync(BESTAND, JSON.stringify(bewaard));
  return lopend(bewaard);
}
