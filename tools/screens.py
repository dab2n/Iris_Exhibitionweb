"""시나리오 Web 화면 크기 통일(2026-11-10): 안쪽 폭 960(x 480~1440), 회색 #7C8F9D 8px 테두리, 바깥 r12 / 안쪽 r4, 테두리 위 끝 y=392.
- 05-04·05-05(정지 PNG): git 의 원본(SRC 커밋)에서 화면 안쪽을 잘라 960 폭으로 줄이고 테두리를 새로 그림
- 05-08: 테두리 고리(slides/05-08-top.png)를 GIF 바깥(480,400 960x638)으로 다시 그림
- 05-06: GIF(글 포함) 배경을 새 배치 기준으로 다시 만듦 → ONLY=05-06 overlays.py → bake.py
python3 tools/screens.py"""
import io, os, subprocess
import numpy as np
from PIL import Image, ImageDraw

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '0855034'  # 통일 전 PNG 가 있는 커밋
GRAY = (124, 143, 157); X0, IW, B, TOP, RO, RI = 480, 960, 8, 392, 12, 4
SS = 4  # 둥근 모서리 4배로 그려 줄임

def rr_mask(w, h, r):
    m = Image.new('L', (w * SS, h * SS), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255)
    return m.resize((w, h), Image.LANCZOS)

def ring(ih):  # 안쪽 높이 ih → (RGBA 고리, 바깥 좌상단)
    ow, oh = IW + 2 * B, ih + 2 * B
    a = np.asarray(rr_mask(ow, oh, RO)).astype(int)
    inner = np.zeros_like(a); inner[B:B + ih, B:B + IW] = np.asarray(rr_mask(IW, ih, RI))
    al = np.clip(a - inner, 0, 255).astype('uint8')
    im = Image.new('RGBA', (ow, oh), GRAY + (255,)); im.putalpha(Image.fromarray(al))
    return im, (X0 - B, TOP)

def git_png(k):
    return Image.open(io.BytesIO(subprocess.check_output(['git', '-C', root, 'show', f'{SRC}:slides/{k}.png']))).convert('RGB')

def rowbg(im, x=10):  # 줄마다 배경색(왼쪽 끝)
    return np.asarray(im)[:, x]

for k in ['05-04', '05-05']:
    im = git_png(k); a = np.asarray(im).astype(int)
    m = np.abs(a - GRAY).sum(2) < 30; m[:130] = False
    xs = np.nonzero(m.sum(0) > 100)[0]; ys = np.nonzero(m.sum(1) > 100)[0]
    ox0, ox1, oy0, oy1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1  # 지금 테두리 바깥
    inner = im.crop((ox0 + B, oy0 + B, ox1 - B, oy1 - B))
    ih = round(inner.size[1] * IW / inner.size[0]); inner = inner.resize((IW, ih), Image.LANCZOS)
    out = np.asarray(im).copy(); bg = rowbg(im)
    out[oy0 - 4:oy1 + 4, ox0 - 4:ox1 + 4] = bg[oy0 - 4:oy1 + 4, None, :]  # 옛 화면 지움
    out = Image.fromarray(out)
    out.paste(inner, (X0, TOP + B), rr_mask(IW, ih, RI))
    r, p = ring(ih); out.paste(r, p, r)
    out.save(f'{root}/slides/{k}.png'); print(k, 'old', (ox0, oy0, ox1 - ox0, oy1 - oy0), 'new inner', (X0, TOP + B, IW, ih))

# 05-08: 옛 GIF 자리(구운 첫 장면)를 배경으로 지움 → overlays.py 가 새 상자(GIF 자체 테두리 잘라 안쪽 960)로 다시 합성
im = git_png('05-08'); out = np.asarray(im).copy(); bg = rowbg(im)
out[380:1060, 460:1460] = bg[380:1060, None, :]; Image.fromarray(out).save(f'{root}/slides/05-08.png')
top = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); r, p = ring(622); top.paste(r, p, r)
top.save(f'{root}/slides/05-08-top.png'); print('05-08 ring', p, r.size)

# 05-06: GIF(글 포함)를 안쪽 화면이 960 이 되게 줄이고(0.938배), 그 배치 기준으로 배경(줄마다 GIF 왼쪽 끝 색)을 새로 만듦 + 고리(05-06-top.png)
S6 = 960 / 1310 * 960 / 1023; BX6, BY6 = 273.25, 173.37
gif = os.path.expanduser('~/Desktop/Iris_Behance/03_Iris_FlowMapCardSelect_2000.gif')
fr = Image.open(gif).convert('RGB').crop((0, 70, 2000, 1380)); bh = round(1310 * S6)
col = np.median(np.asarray(fr.resize((round(2000 * S6), bh), Image.LANCZOS))[:, :3], axis=1)
im = git_png('05-06'); out = np.asarray(im).copy(); y0 = round(BY6)
rows = np.array([col[min(max(y - y0, 0), bh - 1)] for y in range(1080)]).astype('uint8')
out[120:] = rows[120:, None, :]; Image.fromarray(out).save(f'{root}/slides/05-06.png')
top = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); r, p = ring(619); top.paste(r, p, r)
top.save(f'{root}/slides/05-06-top.png'); print('05-06 ring', p, r.size)
