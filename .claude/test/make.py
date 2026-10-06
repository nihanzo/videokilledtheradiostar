# Testkopien für vergleich.html: alt = letzter Commit (git HEAD), neu = Arbeitsstand.
# <base href="/"> damit alle relativen Pfade wie im Projektordner auflösen, plus Fehler-Sammler (inject.js).
# Aufruf: python3 .claude/test/make.py   (nach jeder Änderung neu ausführen)
import pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INJ = (HERE / 'inject.js').read_text()

def write(name, html):
    assert html.count('<head>') == 1, name
    html = html.replace('<head>', '<head>\n<base href="/">\n<script>' + INJ + '</script>', 1)
    (HERE / name).write_text(html)

for page, tag in (('startpage.html', 'start'), ('index.html', 'lade')):
    write(tag + '-alt.html', subprocess.check_output(['git', 'show', 'HEAD:' + page], cwd=ROOT).decode())
    write(tag + '-neu.html', (ROOT / page).read_text())
print('ok')
