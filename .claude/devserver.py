# Lokaler Vorschau-Server fuer nihanzo: wie `python3 -m http.server`, aber OHNE Browser-Cache.
# Sonst zeigt die Vorschau nach Aenderungen alte Seitenstaende (z. B. curtain.html ohne Weiterleitung).
import functools, http.server, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # Projektordner (eine Ebene ueber .claude)

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8756
http.server.ThreadingHTTPServer(('', port), functools.partial(NoCache, directory=ROOT)).serve_forever()
