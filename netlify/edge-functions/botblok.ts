// Botblok: weigert robots die niets opleveren (geen bezoekers, alleen dataverbruik).
// Google, Bing, Yandex, Seznam, Apple, DuckDuckGo, ChatGPT-zoeken, Perplexity en Facebook/Instagram-linkvoorbeelden blijven toegestaan.
import type { Config, Context } from "@netlify/edge-functions";

// Onschuldig verklaarde nepbrowser: Linux-Chrome uit datacenters buiten NL/BE/DE.
const SCRAPER_LANDEN = ["US", "SG", "CN", "BD", "IN", "VN", "HK"];

export default async (request: Request, context: Context) => {
  const ua = request.headers.get("user-agent") ?? "";
  // Nep-"Linux Chrome" alleen blokkeren buiten de Benelux en Duitsland
  if (/X11; Linux x86_64\) AppleWebKit\/537\.36 \(KHTML, like Gecko\) Chrome\/\d+\.0\.0\.0 Safari\/537\.36$/.test(ua)) {
    const land = context.geo?.country?.code ?? "";
    if (!SCRAPER_LANDEN.includes(land)) return; // gewone bezoeker: doorlaten
  }
  return new Response("Geen toegang voor deze robot.", {
    status: 403,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
};

export const config: Config = {
  path: "/*",
  // De functie draait ALLEEN als de user-agent op deze lijst past. Gewone bezoekers kosten dus niets extra.
  header: {
    "user-agent":
      "(MJ12bot|SemrushBot|AhrefsBot|DotBot|PetalBot|DataForSeoBot|BLEXBot|Baiduspider|Reflectionbot|ShapBot|meta-externalagent|meta-webindexer|Amazonbot|Bytespider|CCBot|GPTBot|ClaudeBot|anthropic-ai|Google-Extended|Applebot-Extended|ImagesiftBot|Diffbot|HeadlessChrome|python-requests|python-httpx|aiohttp|Go-http-client|Scrapy|curl/|wget/|^Mozilla/5\\.0 \\(Windows NT 10\\.0; Win64; x64\\) AppleWebKit/537\\.36$|X11; Linux x86_64\\) AppleWebKit/537\\.36 \\(KHTML, like Gecko\\) Chrome/\\d+\\.0\\.0\\.0 Safari/537\\.36$)",
  },
};
