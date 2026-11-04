"""상단 메뉴 띠(0~119줄) 배경을 바로 아래 콘텐츠 색에 맞춤 — 메뉴만 다른 색으로 보이는 투톤 방지.
메뉴 글자는 단색(어두운 띠는 흰색, 밝은 띠는 #111)이라 밝기 차이로 투명도를 구해 새 배경 위에 다시 얹음.
대상: 메뉴가 PNG 에 들어 있는 장(스크롤 장·04-01 처럼 메뉴를 따로 얹는 장은 제외). 피그마에서 PNG 를 새로 받으면 다시 실행."""
import glob, os
import numpy as np
from PIL import Image

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {'02-01', '02-04', '03-02', '04-01', '04-03', '06-02', '04-04'}  # 메뉴를 따로 얹는 장, 04-04 는 메뉴 아래가 큐브 영상(장면마다 색이 바뀜)
L = lambda c: c @ np.array([.2126, .7152, .0722])

def fix(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(float)
    nb = np.median(a[2:8], axis=(0, 1))                      # 지금 메뉴 띠 색
    # 바로 아래 줄에서 가장 많이 쓰인 색 = 콘텐츠 배경색(이미지가 메뉴에 닿는 장도 이미지 색이 번지지 않게 한 가지 색으로)
    row = a[121:125].reshape(-1, 3).round().astype(int); u, n = np.unique(row, axis=0, return_counts=True); tgt = u[n.argmax()].astype(float)
    if n.max() < row.shape[0] * 0.3 or np.abs(tgt - nb).max() <= 1: return False
    fg = np.array([255.] * 3) if L(nb) < 128 else np.array([17.] * 3)
    band = a[:120]; al = ((L(band) - L(nb)) / (L(fg) - L(nb))).clip(0, 1)[..., None]
    a[:120] = tgt[None] * (1 - al) + fg * al
    Image.fromarray(a.round().clip(0, 255).astype('uint8')).save(p); return True

if __name__ == '__main__':
    for p in sorted(glob.glob(f'{root}/slides/[0-9][0-9]-[0-9][0-9].png')):
        k = os.path.basename(p)[:5]
        if k not in SKIP and fix(p): print('fixed', k)
