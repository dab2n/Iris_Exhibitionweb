"""영상 첫 프레임을 그 장 PNG(slides/키.png) 의 같은 자리에 붙여 둠.
영상이 아직 준비되지 않은 순간에도 PNG 가 영상 첫 장면과 똑같아서 바뀌는 티(깜빡임)가 나지 않게.
tools/overlays.py 다음, tools/camera.sh 전에 실행. (좌우가 흐려지는 feather 영상은 제외)"""
import json, os, subprocess, tempfile
from PIL import Image

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = json.loads(open(f'{root}/media/overlays.js').read()[len('var OVERLAYS = '):].rstrip(';\n'))
CH = {'02-01': 1714, '02-04': 1953, '04-03': 1869}
tmp = tempfile.mkdtemp()
for o in O:
    if o.get('feather'): continue
    k = o['slide']; ch = CH.get(k, 1080); p = f'{root}/slides/{k}.png'
    f0 = f'{tmp}/f.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{root}/{o["src"]}', '-frames:v', '1', '-update', '1', f0], check=True)
    im = Image.open(p).convert('RGB'); fr = Image.open(f0).convert('RGB')
    x, y = round(o['box'][0] * 1920), round(o['box'][1] * ch); w, h = round(o['box'][2] * 1920), round(o['box'][3] * ch)
    if fr.size != (w, h): fr = fr.resize((w, h))
    # 합성 영상 전체가 아니라 GIF 가 움직이는 영역만 붙임 — 영상에 담긴 옛 배치(글자 위치 등)가 PNG 로 번지지 않게
    gx, gy, gw, gh = [x, y, w, h] if (w, h) == (1920, 1080) else o.get('gbox', [x, y, w, h])  # 화면 전체 영상이면 통째로(PNG = 영상 첫 장면)
    im.paste(fr.crop((gx - x, gy - y, gx - x + gw, gy - y + gh)), (gx, gy)); im.save(p)
    print(k, o['src'], (gx, gy, gw, gh))
