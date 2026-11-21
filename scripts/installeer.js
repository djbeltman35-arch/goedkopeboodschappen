/* Stijl zonder inline <style> (werkt ook met een strenge CSP) */
function __ibCss(css) {
  try { if (document.adoptedStyleSheets && window.CSSStyleSheet) { var sh = new CSSStyleSheet(); sh.replaceSync(css); document.adoptedStyleSheets = document.adoptedStyleSheets.concat(sh); return; } } catch (e) {}
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
}
/* Home- en terugknop: altijd in beeld op elke pagina behalve de startpagina. Uitzetten: <html data-geen-navknoppen>. */
(function () {
  var html = document.documentElement;
  if (html.hasAttribute('data-geen-navknoppen')) return;
  var pad = location.pathname.replace(/index\.html?$/, '');
  if (pad === '/' || pad === '') return;
  var lang = (html.lang || 'nl').slice(0, 2).toLowerCase();
  var W = { nl: ['Startpagina', 'Terug'], en: ['Home', 'Back'], de: ['Startseite', 'Zurück'], fr: ['Accueil', 'Retour'], es: ['Inicio', 'Atrás'], it: ['Home', 'Indietro'], pl: ['Start', 'Wstecz'] }[lang] || ['Home', 'Back'];
  var thuis = '/' + (/^\/[a-z]{2}\//.test(pad) && lang !== 'nl' ? pad.slice(1, 3) + '/' : '');
  function start() {
    __ibCss('#ia-nav{position:fixed;left:12px;bottom:12px;z-index:2147482999;display:flex;gap:8px}' +
      '#ia-nav a{display:inline-grid;place-items:center;width:48px;height:48px;border-radius:50%;background:#0e7c4a;color:#fff;box-shadow:0 4px 14px rgba(0,0,0,.22);text-decoration:none}' +
      '#ia-nav a:focus-visible{outline:3px solid #ffd43b;outline-offset:2px}#ia-nav svg{width:24px;height:24px}' +
      '@media print{#ia-nav{display:none}}body{padding-bottom:max(76px,env(safe-area-inset-bottom))}');
    var n = document.createElement('nav'); n.id = 'ia-nav'; n.setAttribute('aria-label', W[0] + ' / ' + W[1]);
    var i = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
    n.innerHTML = '<a href="' + thuis + '" class="terug" aria-label="' + W[1] + '" title="' + W[1] + '">' + i + '<path d="M15 18l-6-6 6-6"/></svg></a>' +
      '<a href="' + thuis + '" aria-label="' + W[0] + '" title="' + W[0] + '">' + i + '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/></svg></a>';
    document.body.appendChild(n);
    n.querySelector('.terug').addEventListener('click', function (e) {
      var vanHier = false; try { vanHier = document.referrer && new URL(document.referrer).origin === location.origin; } catch (x) {}
      if (vanHier && history.length > 1) { e.preventDefault(); history.back(); }
    });
    document.documentElement.classList.add('met-navknoppen');
  }
  if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
})();

/* Installeer-als-app balk. Werkt op Android/Chrome/Edge (knop) en iPhone/iPad Safari (uitleg). */
/* Installeren als app: geen balk meer (werd vaak weggeklikt), maar een rustige link in de footer. */
(function () {
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  if (standalone) return;
  var ua = navigator.userAgent || '';
  var ios = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var uitgesteld = null;
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); uitgesteld = e; });
  var gc = function (p, t) { try { window.goatcounter && goatcounter.count && goatcounter.count({ path: p, title: t, event: true }); } catch (e) {} };
  function start() {
    var nav = document.querySelector('footer nav[aria-label="Over"]') || document.querySelector('footer nav');
    if (!nav || nav.querySelector('.ia-link')) return;
    var a = document.createElement('a'); a.href = '#'; a.className = 'ia-link'; a.textContent = '📲 Zet op je beginscherm';
    var uitleg = document.createElement('p'); uitleg.className = 'small ia-uitleg'; uitleg.hidden = true;
    uitleg.innerHTML = ios
      ? 'Tik onderin Safari op <b>Deel</b> (vierkantje met pijltje omhoog) en kies <b>Zet op beginscherm</b>.'
      : 'Open het menu van je browser (<b>⋮</b> rechtsboven) en kies <b>App installeren</b> of <b>Toevoegen aan startscherm</b>.';
    a.addEventListener('click', function (e) {
      e.preventDefault();
      if (uitgesteld) {
        uitgesteld.prompt();
        uitgesteld.userChoice.then(function (k) { gc('installeer/' + (k && k.outcome), 'Installeren via footer'); uitgesteld = null; }, function () {});
      } else { uitleg.hidden = !uitleg.hidden; gc('installeer/uitleg', 'Installeer-uitleg footer'); }
    });
    window.addEventListener('appinstalled', function () { a.remove(); uitleg.remove(); });
    nav.appendChild(a); nav.parentNode.insertBefore(uitleg, nav.nextSibling);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
