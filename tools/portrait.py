"""세로 화면(스탠바이미 2 세로, 1440x2560) 배치표 → media/portrait.js
가로 장(slides/키.png + 영상)의 영역을 잘라 세로 화면에 다시 놓는 '창' 목록을 만든다.
창 = [sx, sy, sw, sh (가로 캔버스 좌표), dx, dy (세로 화면 좌표), k(배율), v(영상 포함 여부)]
제목·글은 위, 화면·이미지는 아래로 쌓고, 묶음은 화면 가운데(CY)에 모은다."""
import json, os
import numpy as np
from PIL import Image

PW, PH, NAV = 1440, 2560, 90          # 세로 화면, 메뉴 높이(가로 메뉴 120 x 0.75)
CY, MAXW, MAXH = 1330, 1320, 1900     # 묶음 중심 y, 최대 폭/높이
PAD = 44                              # 창 가장자리 흐림(40px)보다 넉넉히
T1 = ['06-02', '06-03', '06-04', '06-05', '06-07']           # 제목 위 + 화면
T2 = ['06-01', '06-09', '06-11', '06-13', '06-14', '06-15']  # 글 왼쪽 + 이미지 오른쪽
SCROLL = {'02-01': 1714, '02-04': 1953, '03-01': 2110, '04-03': 1869, '07-02': 6246}
NAV_ON_TOP = {'04-01': (180, 120, 1560, 960)}                # 영상이 메뉴까지 덮는 장: 메뉴 줄 빼고 영상 영역만

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def bbox(a, R, th=30):
    x, y, w, h = R; sub = a[y:y + h, x:x + w]; bg = a[y:y + h, 3:4]
    d = np.abs(sub - bg).sum(2) > th
    ys = np.where(d.sum(1) > 2)[0]; xs = np.where(d.sum(0) > 2)[0]
    if not len(ys): return None
    x0, y0, x1, y1 = x + xs[0] - PAD, y + ys[0] - PAD, x + xs[-1] + PAD, y + ys[-1] + PAD
    x0, y0 = max(x0, x), max(y0, y); x1, y1 = min(x1, x + w), min(y1, y + h)  # 이웃 영역(제목↔화면)을 침범하지 않게
    return [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]

def colgap(a, b, th=30, need=80):
    """b 안에서 세로로 빈 가장 넓은 띠(폭 need 이상)를 찾음 → (시작 x, 끝 x) 또는 None"""
    x, y, w, h = b; sub = a[y:y + h, x:x + w]; d = (np.abs(sub - a[y:y + h, 3:4]).sum(2) > th).sum(0) > 2
    best, run, start = None, 0, 0
    for i, on in enumerate(d):
        if not on:
            if run == 0: start = i
            run += 1
            if run >= need and (best is None or run > best[1] - best[0]) and i < w - 1: best = (start, i + 1)
        else: run = 0
    return (x + best[0], x + best[1]) if best and best[0] > 0 else None

def stack(items, gap):
    """items: [(box, k, v)] 위에서 아래로. 가운데 정렬, 묶음 중심 CY. 넘치면 같이 줄임."""
    tot = sum(b[3] * k for b, k, v in items) + gap * (len(items) - 1)
    f = min(1, MAXH / tot); tot *= f
    y = CY - tot / 2; out = []
    for b, k, v in items:
        k *= f; out.append([*b, round((PW - b[2] * k) / 2, 1), round(y, 1), round(k, 4), v]); y += b[3] * k + gap * f
    return out

P = {}
for f in sorted(os.listdir(f'{root}/slides')):
    if not f.endswith('.png') or 'nav' in f: continue
    key = f[:5]; a = np.asarray(Image.open(f'{root}/slides/{f}').convert('RGB')).astype(int)
    top, bot = a[min(125, a.shape[0] - 1), 3], a[-5, 3]
    e = dict(bg=['rgb(%d,%d,%d)' % tuple(top), 'rgb(%d,%d,%d)' % tuple(bot)])
    if key in SCROLL:
        k = PW / 1920; h = SCROLL[key] * k
        e['wins'] = [[0, 0, 1920, SCROLL[key], 0, round(max(NAV, CY - h / 2), 1), k, True]]
    elif key in NAV_ON_TOP:
        b = list(NAV_ON_TOP[key]); e['wins'] = stack([(b, min(MAXW / b[2], 1.2), True)], 0)
    elif key in T1:
        t = bbox(a, (0, 125, 1920, 265)); v = bbox(a, (0, 392, 1920, 688))
        e['wins'] = stack([(t, min(1.3, MAXW / t[2]), False), (v, min(1.45, MAXW / v[2], 1000 / v[3]), True)], 70)
    elif key in T2:
        t = bbox(a, (0, 125, 860, 955)); v = bbox(a, (862, 125, 1058, 955))
        e['wins'] = stack([(t, min(1.35, MAXW / t[2]), False), (v, min(1.45, 1300 / v[2], 1150 / v[3]), True)], 90)
    else:
        b = bbox(a, (0, 125, 1920, 955)); g = colgap(a, b)
        if g:  # 좌우로 나뉜 장(글 | 이미지): 위아래로 쌓음
            L = bbox(a, (b[0], b[1], g[0] - b[0], b[3])); R = bbox(a, (g[1], b[1], b[0] + b[2] - g[1], b[3]))
            e['wins'] = stack([(L, min(1.35, MAXW / L[2], 1100 / L[3]), True), (R, min(1.35, MAXW / R[2], 1100 / R[3]), True)], 90)
        else:
            e['wins'] = stack([(b, min(1360 / b[2], 1800 / b[3], 1.5), True)], 0)
    e['nav'] = e['bg'][0]
    grad = np.abs(top - bot).sum() > 12 and key not in SCROLL  # 배경이 그라디언트인 장만 창 가장자리를 흐려 경계를 숨김
    if key in SCROLL:  # 콘텐츠 위는 위쪽 색, 아래는 아래쪽 색(콘텐츠 창이 가운데를 덮음)
        t0, t1 = e['bg']; y0 = e['wins'][0][5] / PH * 100; y1 = (e['wins'][0][5] + SCROLL[key] * PW / 1920) / PH * 100
        e['bg'] = [f'{t0} 0%', f'{t0} {y0:.2f}%', f'{t1} {y1:.2f}%', f'{t1} 100%']
    for w in e['wins']: w.append(bool(grad))
    P[key] = e

open(f'{root}/media/portrait.js', 'w').write('var PORTRAIT = ' + json.dumps(P) + ';\n')
print(len(P), 'slides')
if __name__ == '__main__':
    assert all(w[2] > 0 and w[3] > 0 for e in P.values() for w in e['wins'])
    for k in ('06-03', '06-11', '02-01'): print(k, P[k]['wins'])
