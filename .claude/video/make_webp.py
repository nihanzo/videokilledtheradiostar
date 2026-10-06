# Grünkohl als animiertes WebP aus den key4-Bildern (kgif/seq/f*.png, hin und zurück, 1278×709 -> 960 breit, 24 fps).
# Verlustbehaftet (q80, 4.7 MB statt 12.6 MB als GIF); Weiß wird dabei 254 -> im CSS filter:brightness(1.012).
# Aufruf: python3 make_webp.py ../../assets/img/kale.webp   (danach ?v= in startpage.html hochzählen)
import sys, glob
from PIL import Image
fr = [Image.open(f).convert('RGB').resize((960, 532), Image.LANCZOS) for f in sorted(glob.glob('kgif/seq/f*.png'))]
fr[0].save(sys.argv[1], 'WEBP', save_all=True, append_images=fr[1:], loop=0, quality=80, method=6,
           duration=[42 if i % 3 else 41 for i in range(len(fr))])   # Mittel 41.67 ms = 24 fps
