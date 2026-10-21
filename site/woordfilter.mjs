// Woordfilter voor het tipsformulier: vloeken, scheldwoorden en seksueel getinte woorden (Nederlands en Engels).
// Wordt gebruikt in de browser (directe melding) én op de server (definitieve controle), zodat het niet te omzeilen is.
const HEEL = `kut kutje kutten klote kloten klootzak klootzakken lul lullen lulletje eikel eikels hoer hoeren hoerig slet sletten trut trutten teef
kanker kankeren tering teringlijer tyfus tyfuslijer pest pestlijer pokke pokken klere kolere godverdomme godver godsamme jezus christus
gadverdamme verdomme verdomd shit shitzooi kak kakken stront zeik zeiken pis pissen mongool mongolen debiel debielen idioot idioten imbeciel
achterlijk achterlijke sukkel sukkels oetlul zakkenwasser rotzak rotzakken schoft schoften smeerlap smeerlappen klootviool hufter hufters
homo flikker flikkers nicht poot pottenkijker mof moffen neger negers nikker nikkers zigeuner kaaskop
neuken neukt geneukt neuker pijpen pijpbeurt beffen vingeren rukken afrukken aftrekken klaarkomen geil geile geiler seks sex sexy
porno porn pornografie naakt naaktfoto tieten tiet borsten kont kontje reet pik pikken penis vagina lul clitoris anaal orgasme sperma
erectie stijve hoerenloper prostituee escort bordeel stripper milf
fuck fucking fucker fucked motherfucker shit bullshit bitch bitches asshole ass bastard cunt dick dickhead cock pussy whore slut
wanker twat prick boobs tits nude nudes porn horny sexy blowjob handjob dildo vibrator nigger nigga faggot retard`;
const STAM = ["kanker", "tering", "tyfus", "neuk", "fuck", "porno", "klootz", "hoeren", "teringl", "godver", "kutwijf", "kutmoek", "pijpbeurt", "nigger", "motherf", "klaarkom"];
const VOOR = ["kut", "klote", "kanker", "tering", "tyfus", "kolere", "klere", "pokke", "godver", "hoere", "neuk", "fuck", "shit", "sukkel", "debiel", "mongool", "porno", "slet"];
const WOORDEN = new Set(HEEL.split(/\s+/).filter(Boolean));
const LEET = { "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s", "!": "i", "€": "e" };
export function normaliseer(t) {
  return String(t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[0134578@$!€]/g, c => LEET[c] || c).replace(/(.)\1{2,}/g, "$1$1");
}
// Geeft de gevonden verboden woorden terug (leeg = in orde).
export function verbodenWoorden(tekst) {
  const n = normaliseer(tekst), gevonden = new Set();
  const tokens = n.split(/[^a-z]+/).filter(Boolean);
  for (const w of tokens) {
    if (WOORDEN.has(w) || WOORDEN.has(w.replace(/(.)\1+/g, "$1"))) gevonden.add(w);
    else for (const v of VOOR) if (w.startsWith(v) && w.length > v.length + 1) gevonden.add(w);   // samenstellingen: kutsite, klotewinkel
  }
  // Woorden met puntjes of spaties ertussen (k.u.t, f u c k): letters achter elkaar plakken en op stammen zoeken.
  const plak = n.replace(/[^a-z]/g, "");
  for (const s of STAM) if (n.includes(s) || plak.includes(s)) gevonden.add(s);
  const enkel = tokens.filter(t => t.length === 1).join("");
  for (const w of WOORDEN) if (w.length >= 3 && enkel.includes(w)) gevonden.add(w);
  return [...gevonden];
}
