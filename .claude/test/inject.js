// Wird von make.py ganz oben in die Testkopien eingesetzt: sammelt JS-Fehler, fehlende Dateien und console.error
(function(){
  var E = window.__errs = [];
  addEventListener('error', function(e){
    var t = e.target;
    if(t && t !== window) E.push('datei: ' + (t.currentSrc || t.src || t.href || t.tagName));
    else E.push('js: ' + e.message + ' @' + String(e.filename || '').split('/').pop() + ':' + e.lineno);
  }, true);
  addEventListener('unhandledrejection', function(e){
    var r = e.reason; E.push('promise: ' + (r && r.message ? r.message : r));
  });
  var ce = console.error;
  console.error = function(){ E.push('console: ' + [].map.call(arguments, String).join(' ')); return ce.apply(console, arguments); };
})();
