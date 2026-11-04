"""상단 메뉴를 모든 장에 새로 그림(피그마 메뉴 스펙 그대로, 시스템 SF Pro 로 헤드리스 크롬 렌더).
탭/장 수가 바뀌면 TABS·SUB 만 고치고 실행: python3 tools/render/nav.py
- 메뉴가 PNG 안에 있는 장: 0~119 줄을 '배경색 + 새 메뉴' 로 덮음(배경색 = 지금 메뉴 띠 색)
- 메뉴를 따로 얹는 장(스크롤 장, 04-01): slides/키-nav.png(투명) 로 저장
글자색: 배경이 어두우면 흰색, 밝으면 #111. 그 다음 overlays.py(화면 전체 영상은 메뉴 포함) → bake.py → camera.sh"""
import os, subprocess, json
import numpy as np
from PIL import Image

R = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(os.path.dirname(R))
TABS = [('Background', 2), ('Research', 5), ('Process', 2), ('Design System', 4), ('Scenario', 16), ('Credit', 2)]
SUB = {4: [('Web', 0, 10), ('Mobile', 10, 6)]}   # 탭 번호: [(이름, 시작 장, 장 수)]
SEP = {'02-01', '02-04', '03-01', '04-03', '06-02', '04-01'}  # 메뉴를 따로 얹는 장
W18 = {'Background': 104, 'Research': 81, 'Process': 70, 'Design System': 130, 'Scenario': 76, 'Credit': 54}  # 피그마 글자 폭
GAP, RIGHT = 56, 1840

def layout():
    x = RIGHT; out = []
    for name, _ in reversed(TABS): w = W18[name]; x -= w; out.append((name, x, w)); x -= GAP
    return out[::-1]

def slides():
    for ti, (name, n) in enumerate(TABS):
        for i in range(n):
            key = f'{ti + 1:02d}-{i + 1:02d}'; sub = None; idx, tot = i + 1, n
            for sname, s0, cnt in SUB.get(ti, []):
                if s0 <= i < s0 + cnt: sub, idx, tot = sname, i - s0 + 1, cnt
            yield key, ti, f'{idx:02d} / {tot:02d}', sub

def html(rows):
    L = layout(); h = ['<!doctype html><html><head><meta charset="utf-8"><style>',
         'html,body{margin:0;background:transparent}body{width:1920px;-webkit-font-smoothing:antialiased}',
         '.n{position:relative;width:1920px;height:120px;overflow:hidden}.n *{position:absolute;margin:0;white-space:nowrap;font-family:-apple-system,BlinkMacSystemFont,"SF Pro";line-height:21px}',
         '.t{top:49px;font-size:18px;text-align:center;font-weight:400;opacity:.45}.t.on{font-weight:500;opacity:1}',
         '.c{left:170px;top:56px;font-size:18px;opacity:.5}.u{top:82px;width:20px;height:2px}',
         '.s{top:94px;width:64px;font-size:14px;line-height:17px;text-align:center;opacity:.4}.s.on{font-weight:500;opacity:1}',
         '.l{left:70px;top:30px;width:90px;height:60px;-webkit-mask:url(logo.png) 0 0/90px 60px}</style></head><body>']
    for key, ti, cnt, sub, col in rows:
        h.append(f'<div class="n" style="color:{col}"><div class="l" style="background:{col}"></div><p class="c">{cnt}</p>')
        for j, (name, x, w) in enumerate(L):
            h.append(f'<p class="t{" on" if j == ti else ""}" style="left:{x}px;width:{w}px">{name}</p>')
        name, x, w = L[ti]; h.append(f'<div class="u" style="left:{x + w / 2 - 10}px;background:{col}"></div>')
        if ti in SUB:
            cx = x + w / 2 - 64
            for k, (sname, _, _) in enumerate(SUB[ti]):
                h.append(f'<p class="s{" on" if sname == sub else ""}" style="left:{cx + 64 * k}px">{sname}</p>')
        h.append('</div>')
    return '\n'.join(h + ['</body></html>'])

if __name__ == '__main__':
    rows = []
    for key, ti, cnt, sub in slides():
        p = f'{root}/slides/{key}.png'
        if not os.path.exists(p): print('없음', key); continue
        a = np.asarray(Image.open(p).convert('RGB'))
        bg = np.median(a[2:8].reshape(-1, 3), 0) if key not in SEP else a[min(130, a.shape[0] - 1), 3]
        dark = bg @ [.2126, .7152, .0722] < 128
        rows.append((key, ti, cnt, sub, '#fff' if dark else '#111', tuple(int(v) for v in bg)))
    open(f'{R}/nav.html', 'w').write(html([r[:5] for r in rows]))
    C = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    subprocess.run([C, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files', '--default-background-color=00000000',
                    '--force-device-scale-factor=1', f'--window-size=1920,{120 * len(rows)}', f'--screenshot={R}/nav.png', f'file://{R}/nav.html'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'Google Chrome.*--headless'])
    sheet = Image.open(f'{R}/nav.png').convert('RGBA')
    for i, (key, ti, cnt, sub, col, bg) in enumerate(rows):
        nav = sheet.crop((0, 120 * i, 1920, 120 * i + 120))
        if key in SEP: nav.save(f'{root}/slides/{key}-nav.png')
        else:
            im = Image.open(f'{root}/slides/{key}.png').convert('RGB')
            # 메뉴 띠 배경 = 줄마다 왼쪽 끝(0~40px) 색 → 그라디언트 장도 메뉴와 콘텐츠가 이어짐
            col = np.median(np.asarray(im)[:120, :40], axis=1).astype('uint8')
            band = Image.fromarray(np.repeat(col[:, None, :], 1920, axis=1)).convert('RGBA'); band.alpha_composite(nav)
            im.paste(band.convert('RGB'), (0, 0)); im.save(f'{root}/slides/{key}.png')
    L = layout(); print('TAB_R', json.dumps([[x, x + w] for _, x, w in L]), 'SUB_X', L[4][1] + L[4][2] / 2 - 64)
    print(len(rows), 'navs')
