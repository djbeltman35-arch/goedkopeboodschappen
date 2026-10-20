// "Klopt niet?": een knopje bij elk product (data-fout met JSON: term, winkel, naam, link, prijs).
// Opent een klein venster en stuurt de melding naar /api/fout. Gebruikt in de app en op de losse pagina's.
(() => {
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let dlg, info, open0 = 0;
  function maak() {
    dlg = document.createElement("dialog");
    dlg.className = "foutdlg";
    dlg.innerHTML = `<form method="dialog"><h2>Wat klopt er niet?</h2><p class="wat"></p>
      <label><input type="radio" name="reden" value="product" checked> Verkeerd product (het is iets anders)</label>
      <label><input type="radio" name="reden" value="prijs"> De prijs klopt niet</label>
      <label><input type="radio" name="reden" value="anders"> Iets anders</label>
      <label class="tl">Toelichting (mag leeg blijven)<textarea name="toelichting" rows="2" maxlength="300" placeholder="Bijvoorbeeld: dit is geen pindakaas maar pindasaus"></textarea></label>
      <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
      <p class="priv">We bewaren alleen het product en je toelichting. Om dubbele meldingen en misbruik te herkennen gebruiken we een anonieme code die na hooguit een maand verloopt.</p>
      <div class="knoppen"><button type="submit" value="stuur" class="stuur">Versturen</button><button type="submit" value="nee" class="nee">Annuleren</button></div></form>`;
    document.body.appendChild(dlg);
    dlg.addEventListener("close", async () => {
      if (dlg.returnValue !== "stuur" || !info) return;
      const f = dlg.querySelector("form");
      const body = { ...info, reden: f.reden.value, toelichting: f.toelichting.value, pagina: location.pathname + location.search, website: f.website.value, ms: Date.now() - open0 };
      let ok = false, tekst = "", j = {};
      try { const r = await fetch("/api/fout", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); ok = r.ok; j = await r.json().catch(() => ({})); tekst = ok ? j.melding || "" : j.fout || ""; } catch (e) {}
      if (j.blok) blokkeer(j.blok, ok ? "" : tekst);
      toast(tekst || (ok ? "Bedankt! We kijken ernaar." : "Versturen lukte niet. Probeer het later nog eens."), !!tekst);
      try { window.goatcounter?.count?.({ path: "fout/" + (body.reden || ""), title: "Klopt niet", event: true }); } catch (e) {}
    });
  }
  function toast(t, lang) {
    const el = document.createElement("div"); el.className = "fouttoast"; el.setAttribute("role", "status"); el.textContent = t;
    document.body.appendChild(el); setTimeout(() => el.remove(), lang ? 7000 : 3500);
  }
  // Geblokkeerd (daggrens of maandgrens): onthouden in de browser, zodat het venster niet eens opent.
  const vandaag = () => new Date().toISOString().slice(0, 10);
  function blokkeer(tot, tekst) { try { localStorage.setItem("fout-blok", JSON.stringify({ tot, tekst })); } catch (e) {} }
  function geblokkeerd() { try { const b = JSON.parse(localStorage.getItem("fout-blok") || "null"); if (b && b.tot > vandaag()) return b; } catch (e) {} return null; }
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-fout]"); if (!b) return;
    e.preventDefault();
    const bl = geblokkeerd();
    if (bl) { toast(bl.tekst || "Je kunt vandaag niets meer melden. Morgen kan het weer.", true); return; }
    try { info = JSON.parse(b.dataset.fout); } catch (x) { return; }
    if (!dlg) maak();
    const f = dlg.querySelector("form"); f.reset(); dlg.returnValue = "";
    dlg.querySelector(".wat").innerHTML = `<b>${esc(info.term || info.naam)}</b>${info.winkel ? " bij " + esc(info.winkel) : ""}${info.naam && info.term ? `<br><span>${esc(info.naam)}${info.prijs ? " · " + esc(info.prijs) : ""}</span>` : ""}`;
    open0 = Date.now(); dlg.showModal();
  });
})();
