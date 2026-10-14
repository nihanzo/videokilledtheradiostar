# Lokaler Vorschau-Server fuer nihanzo: wie `python3 -m http.server`, aber der Browser muss JEDE Datei vor dem Benutzen
# neu pruefen (no-cache = speichern erlaubt, aber immer mit If-Modified-Since nachfragen -> 304, wenn unveraendert).
# So zeigt die Vorschau nach Aenderungen nie alte Staende, und das Vorladen der Ladeseite (index.html) wirkt trotzdem
# (vorher no-store: der Browser verwarf alles Vorgeladene).
import functools, http.server, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # Projektordner (eine Ebene ueber .claude)

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    # Range-Anfragen (bytes=a-b) -> 206 mit Teilstueck: Safari spielt MP4-Videos nur so ab
    def send_head(self):
        path = self.translate_path(self.path); rng = self.headers.get('Range')
        m = re.match(r'bytes=(\d*)-(\d*)$', (rng or '').strip())
        if not m or not os.path.isfile(path): return super().send_head()
        size = os.path.getsize(path); a, b = m.groups()
        start, end = (max(0, size - int(b)), size - 1) if a == '' else (int(a), min(size - 1, int(b)) if b else size - 1)
        if start > end: self.send_error(416); return None
        f = open(path, 'rb'); f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers(); self._remain = end - start + 1
        return f

    def copyfile(self, src, dst):
        n, self._remain = getattr(self, '_remain', None), None
        if n is None: return super().copyfile(src, dst)
        while n > 0:
            buf = src.read(min(65536, n))
            if not buf: break
            dst.write(buf); n -= len(buf)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8756
http.server.ThreadingHTTPServer.request_queue_size = 128   # Standard 5 -> bei vielen parallelen Bildern ERR_CONNECTION_RESET
http.server.ThreadingHTTPServer(('', port), functools.partial(NoCache, directory=ROOT)).serve_forever()
