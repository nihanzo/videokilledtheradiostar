// Handy oder Desktop? Fragen die Ladeseite (welche Startseite vorladen/öffnen) und startpage.html (Handys umleiten).
// Handy = Touch ohne Maus UND kurze Bildschirmseite < 600 px (Tablets und Laptops mit Touchscreen bleiben Desktop).
// Zum Testen erzwingen: ?mobile (Handy-Seite) oder ?desktop (Desktop-Seite, wird von der Ladeseite weitergereicht).
window.NIH_PHONE = (function(){
  const q = location.search;
  if(/[?&]desktop\b/.test(q)) return false;
  if(/[?&]mobile\b/.test(q)) return true;
  return matchMedia('(hover: none) and (pointer: coarse)').matches && Math.min(screen.width, screen.height) < 600;
})();
window.NIH_PAGE = window.NIH_PHONE ? 'startpage-mobile.html' : 'startpage.html' + (/[?&]desktop\b/.test(location.search) ? '?desktop' : '');
