// Indeling van aanbiedingen in dezelfde categorieën als de site (scripts/cats.json).
// De eerste regel die past wint, dus specifieke regels (huisdieren, verzorging) staan bovenaan.
// Gebruik los: node ophalen/categorie.mjs data/aanbiedingen.json  (deelt bestaande aanbiedingen opnieuw in)
import fs from 'node:fs';

export const zonderAccent = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

export const CAT_REGELS = [
  ['Huisdieren', /(\bkat\b|\bkatten|\bhond\b|\bhonden|kattenbak|dierenvoer|whiskas|felix|pedigree|sheba|(?<!garden )gourmet (gold|perle|mon petit)|beneful|kauwstaven|hondensnack|kattensnack|huisdier)/],
  ['Verzorging en baby', /(drogisterij|\bbaby\b|tandpasta|tandenborstel|opzetborstel|flosdraad|floss|shampoo|conditioner|douche|deo|zeep|luier|billendoek|scheer|trimmer|\bcreme\b|dagcreme|nachtcreme|handcreme|bodycreme|bodylotion|maandverband|verband|tampon|urineverlies|incontinentie|inlegkruis|mondwater|nivea|dove|axe\b|haarverf|haargel|haarspray|haarlak|gel styler|styler|hair|wax\b|paste\b|clay\b|anti-klit|gliss|syoss|wella|elvive|l'oreal|loreal|garnier|gillette|pampers|zonnebrand|wattenschijf|rexona|transpirant|sanex|palmolive|tissue|zakdoek|maskara|mascara|lippen|nagellak|tandzijde|oral-b|sensodyne|vaseline|always|libresse|vitamine|multivitamin|dagravit|curalyn|roter\b|probiotica|visolie|supplement|bruistablet|panty|haaraccessoire)/],
  ['Huishouden', /(toiletpapier|\bwc|keukenrol|keukenpapier|wasmiddel|wasverzachter|\bwaspod|wasbeurt|afwas|vaatwas|schoonmaak|reiniger|schuurmiddel|ontvetter|vuilniszak|afvalzak|aluminiumfolie|batterij|bleek|robijn|ariel|persil|dreft|sun\b|vanish|glorix|ajax|andy\b|fairy|\bomo\b|reus\b|lenor|luchtverfrisser|air ?wick|cif\b|harpic|cillit|colour catcher|k2r|theelicht|kaars|pedaalemmer|vershouddoos|toiletblok)/],
  ['Koffie en thee', /(koffie|thee\b|thee |theezak|infusion|espresso|cappuccino|latte|senseo|nespresso|dolce gusto|douwe egberts|pukka|clipper|lipton)/],
  ['Bier en wijn', /(bier|\bipa\b|tripel|dubbel\b|\bbock|\bbok\b|ijsbock|trappist|blond 7|abdij|krat\b|veltliner|riesling|\bwitte wijn|\brode wijn|pils|\bwijn\b|wijnen\b|\brose\b|ros[eé]\b|prosecco|cava\b|frizzante|moscato|verdejo|garnacha|grand cru|radler|whisky|wodka|mixdrink|tempranillo|syrah|merlot|cabernet|chardonnay|sauvignon|shiraz|pinot|rioja|primitivo|montepulciano|malbec|champagne|port\b|aperol|\bgin\b|\brum\b(?! ?rozijn)|likeur|jenever|heineken|grolsch|hertog jan|amstel|brand\b|jupiler|leffe|stella artois|\bperoni\b|weihenstephan|gulpener|la trappe|westmalle|chouffe|duvel|affligem|grimbergen|crystal clear|75 ?cl|750 ?ml)/],
  ['Frisdrank en sap', /(\bcola|coca|pepsi|frisdrank|\bsap\b|sappen|appelsap|sinaasappelsap|juice|limonade|siroop|\bwater\b|mineraalwater|\bspa\b|sourcy|ice ?tea|energy|red bull|monster|fanta|sprite|7up|chocomel|chocolademelk|smoothie|healthy people|coolbest|appelsientje|dubbelfris|capri-?sun|wicky|taksi|roosvicee|karvan|teisseire|drank\b|\d ?x ?\d+ ?ml)/],
  ['Broodbeleg', /(\bbeleg\b(?! ?kaas)|pindakaas|hagelslag|hagel\b|vlokken|muisjes|de ruijter|\bjam\b|appelstroop|chocopasta|chocoladepasta|hazelnootpasta|\bhoning|nutella|speculoospasta|calve)/],
  ['Brood en ontbijt', /(bakkerij|brood|bolletjes|\bbollen|beschuit|cracker|ontbijtkoek|cornflakes|havermout|muesli|cruesli|granola|overnight oats|quaker|croissant|stokbrood|pistolet|krentenbol|\btoast|wraps|tortilla(?! ?chips)|ontbijtgranen|crispies|kellogg|brinta|knackebrod|rozijnenbrood|afbak|pannenkoek|poffertjes)/],
  ['Diepvries', /(diepvries|bevroren|\bijs\b|ijsjes|ijsco|ben & jerry|magnum|hertog ijs|\bola\b|cornetto|raket|pizza|friet|frites|aviko|kroket|frikandel|bitterbal|vissticks|snackbal|loempia|mora\b|kwekkeboom|iglo|\bdiepvr)/],
  ['Kaas', /(\bkaas|kaasje|smeerkaas|roomkaas|mozzarella|brie|feta|parmezaan|camembert|old amsterdam|leerdammer|beemster|marcaire|bleu d|blauwschimmel|paturain|heks'?nkaas|geitenkaas|burrata|mascarpone|ricotta|halloumi|\bgouda\b|emmentaler|gruyere|cheddar)/],
  ['Vleeswaren en tapas', /(plakken|ham\b|salami|salame|leverworst|snijworst|palingworst|metworst|vleeswaren|filet americain|cervelaat|boterhamworst|rookvlees|kipfilet beleg|kabanos|fuet|iberico|chorizo|serrano|prosciutto|coppa|coburger|carpaccio|pepperoni|spianata|pat[eé]\b|tapas|olijven|hummus|tzatziki|aioli|\bdip\b|babaganoush|muhammara|gevulde (zoete )?peper|tapenade|antipasti)/],
  ['Sauzen, olie en kruiden', /(saus|mayonaise|ketchup|mosterd|dressing|sambal|pesto|fritessaus|tomato frito|ketjap|\bolie|olijfolie|bakboter|braadboter|\bzout\b|\bpeper\b|kruidenmix|\bkruiden\b|specerij|bouillon|fond\b|jus\b|marinade|azijn)/],
  ['Chips en noten', /(chips|pinda|noten|nootjes|cashew|amandel|popcorn|zoutje|tuc\b|kroepoek|lay'?s\b|pringles|doritos|snack a jacks|\bchio\b|borrel)/],
  ['Koek en snoep', /(chocola|\breep|repen|\bdrop|snoep|(?<!pannen)koek|wafel|biscuit|\bcake|gebak|taart|kauwgom|speculaas|bonbon|cupcake|cream roll|\bchoco|lolly|proteinbar|proteinereep|chewy bar|muffin|donut|brownie|tompouce|marshmallow|m&m|milka|tony|haribo|mentos|kitkat|snickers|twix|bounty|mars\b|maoam|frisia|lutti|klene|true dates|nougat|fudge|soezen|zoenen|mouse\b|munten|winegum)/],
  ['Zuivel en eieren', /(\bmelk|yoghurt|kwark|\bvla\b|\bvla |slagroom|room\b|kookroom|\bboter|margarine|halvarine|eieren|zuivel|skyr|kefir|toetje|pudding|danone|optimel|almhof|campina|arla|mona|becel|blue band|alpro|sojadrink|havermelk|haverdrink|creme fraiche)/],
  ['Vlees en vis', /(\bkip|gehakt|vlees|biefstuk|varken|speklap|spek\b|\bspek|\bworst|rookworst|braadworst|grillworst|schnitzel|hamburger|burger|slavink|zalm|tonijn|\bvis\b|fish|garnal|kabeljauw|pangasius|heek|haring|makreel|ansjovis|shoarma|saucijs|drumstick|kalkoen|rund|kipfilet|kipdij|bacon|gyros|sate|spareribs|steak|filet\b|entrecote|ossenhaas|rollade|kipkluif|kippenpoot|pulled|vegetarische slager|speckjes)/],
  ['Pasta, rijst en wereldkeuken', /(pasta|spaghetti|macaroni|penne|fusilli|rigatoni|pappardelle|tagliatelle|chitarra|gnocchi|\brijst|risotto|noedel|\bmie\b|mihoen|lasagne|tortellini|ravioli|wereldkeuken|couscous|bulgur|quinoa|conimex|nasi|bami|babi|foe yong|curry|roerbakmix|basismix|kroepoek|taco|burrito|fajita|sushi|wok)/],
  ['Soep, conserven en bakken', /(\bsoep|conserv|bonen in|knorr|honig|maggi|blik|appelmoes|compote|tomatenpuree|tomato puree|passata|tomatenblokjes|augurk|zilverui|bloem\b|suiker|bakmix|bak specialiteit|bakvulling|bakdecoratie|sukade|maaltijd|ovenschotel|stamppot|quiche|verspakket|dwarsliggers|sesamzaad|kidneybonen|kikkererwten|linzen|kapucijners)/],
  ['Fruit', /(banan|\bappel|\bpeer|peren|sinaasappel|mandarijn|clementine|druiven|aardbei|bessen|framboz|avocado|citroen|limoen|kiwi|mango|ananas|meloen|fruit|minneola|grapefruit|nectarine|perzik|pruim|vijg|dadel|granaatappel|bosbes|blauwe bes|kaki|cranberr)/],
  ['Groente en aardappelen', /(aardappel|krieltjes|\buien|\bui\b|tomaat|tomaten|komkommer|paprika|wortel|broccoli|bloemkool|\bsla\b|salade|spinazie|champignon|paddenstoel|courgette|\bprei|groente|kool\b|kool |sperziebonen|boontjes|bonen|veldertjes|doperw|\bmais\b|edamame|cannellini|zuurkool|andijvie|spruit|knoflook|bosui|rucola|pompoen|sweet dumpling|biet|rauwkost|pastinaak|knolselderij|venkel|aubergine|radijs|bieslook|peterselie|witlof|snoepgroente|snoeptomaat)/],
];

export function categorieVan(naam) {
  const t = zonderAccent(naam);
  for (const [c, re] of CAT_REGELS) if (re.test(t)) return c;
  return 'Overig';
}

// Losse aanroep: bestaande aanbiedingen opnieuw indelen.
if (process.argv[1] && process.argv[1].endsWith('categorie.mjs') && process.argv[2]) {
  const f = process.argv[2], d = JSON.parse(fs.readFileSync(f, 'utf8'));
  const tel = {};
  // Oude namen voor als alleen de winkelcategorie iets opleverde.
  const OUD = { 'Groente en fruit': 'Groente en aardappelen', 'Kaas en vleeswaren': 'Vleeswaren en tapas', 'Pasta, rijst en koken': 'Pasta, rijst en wereldkeuken', 'Sauzen': 'Sauzen, olie en kruiden', 'Dranken': 'Frisdrank en sap', 'Snoep en chips': 'Koek en snoep' };
  for (const o of d.offers) {
    let c = categorieVan(o.n + ' ' + (o.sz || ''));
    if (c === 'Overig' && o.c && o.c !== 'Overig') c = OUD[o.c] || o.c;
    o.c = c; tel[c] = (tel[c] || 0) + 1;
  }
  fs.writeFileSync(f, JSON.stringify(d));
  console.log(tel);
}
