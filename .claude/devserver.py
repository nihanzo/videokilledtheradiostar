# Lokaler Vorschau-Server fuer nihanzo: wie `python3 -m http.server`, aber der Browser muss JEDE Datei vor dem Benutzen
# neu pruefen (no-cache = speichern erlaubt, aber immer mit If-Modified-Since nachfragen -> 304, wenn unveraendert).
# So zeigt die Vorschau nach Aenderungen nie alte Staende, und das Vorladen der Ladeseite (index.html) wirkt trotzdem
# (vorher no-store: der Browser verwarf alles Vorgeladene).
import functools, http.server, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # Projektordner (eine Ebene ueber .claude)

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8756
http.server.ThreadingHTTPServer.request_queue_size = 128   # Standard 5 -> bei vielen parallelen Bildern ERR_CONNECTION_RESET
http.server.ThreadingHTTPServer(('', port), functools.partial(NoCache, directory=ROOT)).serve_forever()
