#!/usr/bin/env python3
"""Bundle index.html + data.js + img/ into one self-contained bikemap-video.html.

index.html is the editable source (serve the folder to preview). The bundle is
the deliverable: it inlines data.js and every image as a data URI, so it works
opened from anywhere — including the go/bikemap-video symlink, where relative
img/ paths would otherwise 404. Run this after any edit to index.html.
"""
import base64, glob, json, os

root = os.path.dirname(os.path.abspath(__file__))
os.chdir(root)

html = open("index.html").read()
html = html.replace('<script src="data.js"></script>',
                    '<script>\n' + open("data.js").read() + '\n</script>')

assets = {}
for p in sorted(glob.glob("img/**/*.jpg", recursive=True)):
    rel = p.replace("\\", "/")
    assets[rel] = "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()

html = html.replace('<body class="hideprompt">',
                    '<body class="hideprompt">\n<script>window.ASSETS=' + json.dumps(assets) + ';</script>')

open("bikemap-video.html", "w").write(html)
print(f"bundled {len(assets)} images -> bikemap-video.html "
      f"({os.path.getsize('bikemap-video.html')/1e6:.1f} MB)")
