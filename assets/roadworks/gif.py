# Hand-drawn 88x31 "under construction" button, 8 frames, 1994 idiom.
from PIL import Image
import sys
OUT = sys.argv[1]
W, H = 88, 31
PAL = {
 '.': (0, 0, 0), 'y': (255, 216, 0), 'r': (226, 34, 26), 'd': (128, 14, 10),
 'l': (255, 120, 90), 'w': (255, 255, 255), 'o': (255, 122, 0),
 'b': (140, 90, 43), 'g': (170, 170, 170),
}
ORDER = list(PAL)

FONT = {
 'U': ['101','101','101','101','111'],
 'N': ['1001','1101','1011','1001','1001'],
 'D': ['110','101','101','101','110'],
 'E': ['111','100','110','100','111'],
 'R': ['110','101','110','101','101'],
 'C': ['011','100','100','100','011'],
 'O': ['010','101','101','101','010'],
 'S': ['011','100','010','001','110'],
 'T': ['111','010','010','010','010'],
 'I': ['111','010','010','010','111'],
}
def text_w(s, sc=1):
    return (sum(len(FONT[c][0]) for c in s) + len(s) - 1) * sc
def draw_text(px, s, x, y, col, sc=1):
    for c in s:
        g = FONT[c]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == '1':
                    for a in range(sc):
                        for b in range(sc):
                            px[(x + i*sc + a, y + j*sc + b)] = col
        x += (len(g[0]) + 1) * sc

# Sprite 24 x 21, top-left at (2,5). Ant faces right, toward the words.
BODY = [
 "........................",  # 0
 "........................",  # 1
 "........................",  # 2
 "........................",  # 3
 "...................d.d..",  # 4  antennae tips
 "..L...............d.d...",  # 5  lamp (L)
 "..o...............dd....",  # 6
 "..o..............rrr....",  # 7  head
 "..o.............rrrwr...",  # 8
 ".www............rrrrrd..",  # 9
 ".ooo.....dddd....rrrdd..",  # 10
 ".ooo....drlrrd.rrd......",  # 11
 ".ooo....drrrrrdrrA......",  # 12 A = arm
 "wwwww...drrrrd.dd.......",  # 13
 "ooooo....dddd.d.d.d.....",  # 14 legs
 "ooooo........d..d..d....",  # 15
 "ooooo.......d...d..d....",  # 16
 "ooooo.......d..d....d...",  # 17
 "ooooo......d...d....d...",  # 18
 "oooooo.....d..d.....d...",  # 19
 "bbbbbbbbbbbbbbbbbbbbbbbb",  # 20 ground
]
def sprite(pose, f):
    rows = [list(r) for r in BODY]
    lamp_on = (f // 2) % 2 == 0
    rows[5][2] = 'y' if lamp_on else 'o'
    if pose == 'dig':
        rows[12][17] = 'd'
        for (x, y) in [(18,13),(19,14),(20,15),(21,16)]:
            rows[y][x] = 'g'
        for (x, y) in [(20,17),(21,17),(22,17),(21,18),(22,18),(20,18)]:
            rows[y][x] = 'g'
        for (x, y) in [(19,18),(23,18),(18,19),(19,19),(20,19),(21,19),(22,19),(23,19),(23,17)]:
            rows[y][x] = 'b'
    else:  # lift
        rows[12][17] = 'd'
        rows[11][18] = 'd'
        for (x, y) in [(19,10),(20,9),(21,8)]:
            rows[y][x] = 'g'
        for (x, y) in [(21,7),(22,7),(22,6),(23,6),(23,7)]:
            rows[y][x] = 'g'
        for (x, y) in [(22,5),(23,5)]:
            rows[y][x] = 'b'
        specks = [(21,3),(23,2)] if f % 2 == 0 else [(22,2),(20,1)]
        for (x, y) in specks:
            rows[y][x] = 'b'
        for (x, y) in [(20,19),(21,19),(22,19)]:
            rows[y][x] = 'b'
    return rows

def frame(f):
    im = Image.new('P', (W, H), 0)
    im.putpalette(sum((list(PAL[k]) for k in ORDER), []))
    px = im.load()
    idx = {k: i for i, k in enumerate(ORDER)}
    for y in list(range(1, 5)) + list(range(26, 30)):
        for x in range(1, W - 1):
            s = f if y < 5 else -f
            on = ((x + y - s) // 4) % 2 == 0
            px[(x, y)] = idx['y'] if on else idx['.']
    pose = 'dig' if (f // 2) % 2 == 0 else 'lift'
    for j, row in enumerate(sprite(pose, f)):
        for i, c in enumerate(row):
            if c != '.':
                px[(2 + i, 5 + j)] = idx[c]
    zone0, zone1 = 27, 86
    u = 'UNDER'
    ux = zone0 + (zone1 - zone0 - text_w(u, 2)) // 2
    blink = f < 4
    draw_text(px, u, ux, 7, idx['y'] if blink else idx['w'], 2)
    c = 'CONSTRUCTION'
    cx = zone0 + (zone1 - zone0 - text_w(c)) // 2
    draw_text(px, c, cx, 19, idx['y'], 1)
    return im

frames = [frame(f) for f in range(8)]
def save(frs, path, scale):
    fr = [im.resize((W*scale, H*scale), Image.NEAREST) for im in frs]
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=130, loop=3,
               optimize=False, disposal=1)   # four plays, about 4 s, then it rests: motion past 5 s needs a pause (WCAG 2.2.2)
save(frames, OUT + '/construction.gif', 1)
save(frames, OUT + '/construction@2x.gif', 2)
frames[0].convert('RGB').save(OUT + '/construction.png', optimize=True)
frames[0].resize((W*2, H*2), Image.NEAREST).convert('RGB').save(OUT + '/construction@2x.png', optimize=True)
# contact sheet for review
sheet = Image.new('RGB', (W*8 + 18, (H*8 + 6) * 2), (60, 60, 60))
for k in (0, 2):
    sheet.paste(frames[k].resize((W*8, H*8), Image.NEAREST).convert('RGB'), (9, 3 + (k//2) * (H*8 + 6)))
sheet.save(sys.argv[2])
