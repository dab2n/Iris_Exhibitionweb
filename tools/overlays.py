"""GIF → 슬라이드 영역에 맞춘 mp4 로 변환. python3 tools/overlays.py [check]
각 항목: slide, gif, 블록 크기(B, Figma 원본 블록 px), 슬라이드에서의 창 크롭 r(블록 좌표), 배치 d=(x,y,scale)
recording 은 블록이 아닌 화면 녹화라 r 대신 box 를 직접 지정."""
import json, os, subprocess, sys
from PIL import Image
H = os.path.expanduser('~')
D = H + '/Desktop/'; DL = H + '/Downloads/iris-gif/'
def fit(rw, rh, hh=960):  # 메뉴 아래(960)에서 높이 hh 로 가운데 정렬
    s = min(1920 / rw, hh / rh); return ((1920 - rw * s) / 2, 120 + (960 - rh * s) / 2, s)
def cy(x, w, rw, rh):
    s = w / rw; return (x, 120 + (960 - rh * s) / 2, s)
O = [  # slide, gif, block(w,h), region r, placement (x,y,s)
 # 스크롤 장(세로로 긴 캔버스, CANVAS_H): 키 끝 b = 스크롤이 끝난 뒤 재생
 ('02-01',  D+'Iris_StartingQuestion_v3_2000.gif', (2000,1322), (0,0,2000,694),    (0,267,0.96)),
 ('02-01b', D+'Iris_StartingQuestion_v3_2000.gif', (2000,1322), (0,694,2000,628),  (0,267+694*0.96,0.96)),
 ('02-04b', D+'Iris_InterviewPeel_4000.gif',       (2000,2168), (0,940,2000,1228), (200,205+940*0.76+60,0.76)),
 ('03-04', D+'Iris_DiscussionFlow_4064.mp4',      (2000,1528), (0,72,2000,1384),  (180,0,0.78)),
 ('04-01', D+'Iris_GridSystem_4000.gif',          (2000,1358), (0,80,2000,1220),  fit(2000,1220)),
 ('05-01', D+'Iris_FlowMap_4000.gif',             (2000,1324), (100,100,1800,1110), cy(800,1080,1800,1110)),
 ('04-03', D+'Iris_CubeSlides_2000_HQ.gif',       (2000,1064), (0,0,2000,1000),   (0,120,0.96)),
 ('05-02', DL+'요약-플로우맵-전환.gif',              (1024,640),  (0,0,1024,640),    (448,400,1.0)),
 ('05-05', D+'Iris_FlowMapCardSelect_2000.gif',   (2000,1543), (0,0,2000,1543),   fit(2000,1543,840)),
 ('05-07', D+'Iris_Figjam_2000.gif',              (2000,1543), (0,0,2000,1543),   fit(2000,1543,840)),
 ('05-08', D+'Iris_Notion_2000.gif',              (2000,1403), (0,0,2000,1403),   fit(2000,1403,840)),
 ('05-11', D+'Iris_Recording_2000.gif',           (2000,1162), (420,20,1160,1122),(885,150,0.811)),
 ('05-12', D+'Iris_12-1.gif',                     (2000,1102), (0,0,2000,1102),   fit(2000,1102)),
]
# 영상 앞 정지 구간을 뒤로 보내 들어오자마자 움직이게(초). 반복 주기는 같음
ROTATE = {'02-01b': 2.2}
NOLOOP = {'02-04b': 3.0}  # 한 번만 재생, 값(초)에서 잘라 마지막 장면(카드 펼쳐진 상태)에 멈춤
FEATHER = {'03-04'}  # 좌우 끝을 배경으로 흐리게(메뉴는 slides/키-nav.png 로 위에)  # 한 번만 재생하고 마지막 장면에서 멈춤
CANVAS_H = {'02-01': 1714, '02-04': 1953, '04-02': 1869}
# 영상은 슬라이드 PNG 위에 합성해 가로 전체(스크롤 장은 그 띠, 나머지는 화면 전체)로 만든다.
# 감마는 sRGB(iec61966-2-1)로 표기해야 크롬이 PNG·CSS 색과 똑같이 그린다(bt709 이면 어두운 색이 떠 보임). 스크롤 장 띠의 위/아래 끝은 CSS 로 흐림
FADE = {'02-01': 't', '02-01b': 'b', '02-04b': 'tb'}  # 피그마 '(스크롤)' 프레임 높이
# 플로우맵 화면 녹화(프레임N_ GIF, 2000폭): 안의 화면(302,404 1395x902)만 잘라 블록 130:5140 플로우맵 프레임 위치에
for sl, f, fy, r in [('05-03','프레임1_일반요약-플로우맵-오른쪽스크롤.gif',405,(0,90,2000,1240)),
                     ('05-04','프레임2_화면확대-자유확대축소-오른쪽스크롤.gif',1813,(0,1490,2000,1260))]:
    x, y, s = fit(r[2], r[3], 840)
    O.append((sl, DL+f, None, None, (x + 302*s, y + (fy - r[1])*s, s, 1395*s, 902*s)))

# Interface 레이아웃 통일(2026-11-04): 장별로 화면/이미지 영역 V0(옛 슬라이드 좌표)를 배율 k 로 키워 V1 에 둔다.
# 영상은 V0 안쪽만 잘라 옮긴다(제목은 PNG 에서 따로 맞춤). 피그마 '여기' 프레임과 같은 값
XF = {'05-01': ((848,320,984,613), .915, (880,319.5)),   '05-02': ((448,400,1024,640), .9375, (480,400)),
      '05-03': ((479,385,960,627), 1, (480,400)),        '05-04': ((494,395,930,602), 960/930, (480,400)),
      '05-05': ((574,394,771,503), 960/771, (480,400)),  '05-07': ((544,432,832,553), 960/832, (480,400)),
      '05-08': ((431,297,1060,608), 1.1, (377,143.3)),   '05-11': ((885,150,941,910), .879, (916.5,200)),
      '05-12': ((106,137,1707,925), .865, (222,200))}
def remap(b, V0, k, V1):
    bx, by, bw, bh = b['box']; cx, cy, cw, ch = b['crop']; sx, sy = cw / bw, ch / bh
    x0, y0 = max(bx, V0[0]), max(by, V0[1]); x1, y1 = min(bx + bw, V0[0] + V0[2]), min(by + bh, V0[1] + V0[3])
    return dict(crop=(cx + (x0 - bx) * sx, cy + (y0 - by) * sy, (x1 - x0) * sx, (y1 - y0) * sy),
                box=(V1[0] + (x0 - V0[0]) * k, V1[1] + (y0 - V0[1]) * k, (x1 - x0) * k, (y1 - y0) * k))

def boxes(o):
    sl, gif, B, r, p = o
    if B is None: return dict(box=p[:2]+p[3:], crop=(302, 404, 1395, 902))
    x, y, s = p; rx, ry, rw, rh = r
    rh = min(rh, B[1] - ry)  # 블록 끝에서 자름
    return dict(box=(x, y, rw*s, rh*s), crop=(rx, ry, rw, rh))

if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check = sys.argv[1:] == ['check']
    out = []
    for o in O:
        sl, gif = o[0], o[1]; b = boxes(o)
        if sl in XF: b = remap(b, *XF[sl])
        bx, by, bw, bh = [round(v) for v in b['box']]; bw -= bw % 2; bh -= bh % 2
        if gif.endswith('.mp4'):
            sw = int(subprocess.check_output(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width','-of','csv=p=0',gif]))
            if check: continue
        else:
            im = Image.open(gif); sw = im.size[0]
        g = sw / (o[2][0] if o[2] else sw)
        if check:
            im.seek(im.n_frames - 1); fr = im.convert('RGB')
            if b['crop']: fr = fr.crop(tuple(round(v*g) for v in (b['crop'][0], b['crop'][1], b['crop'][0]+b['crop'][2], b['crop'][1]+b['crop'][3])))
            base = Image.open(f'{root}/slides/{sl[:5]}.png').convert('RGB'); base.paste(fr.resize((bw, bh)), (bx, by))
            base.save(f'/private/tmp/claude-501/-Users-bugi/06fa9a8d-6a63-4309-b4cc-1ac1b1af8b0e/scratchpad/gif/chk_{sl}.png'); continue
        vf = (f"crop={round(b['crop'][2]*g)}:{round(b['crop'][3]*g)}:{round(b['crop'][0]*g)}:{round(b['crop'][1]*g)}," if b['crop'] else '') + \
             f"scale={bw}:{bh}:flags=lanczos"
        if sl in ROTATE:
            t = ROTATE[sl]
            vf = f"split[a][b];[a]trim=start={t},setpts=PTS-STARTPTS[x];[b]trim=end={t},setpts=PTS-STARTPTS[y];[x][y]concat," + vf
        name = f'media/{sl}.mp4'; ch = CANVAS_H.get(sl[:5], 1080)
        if sl in FEATHER:  # 영상만(좌우 흐림은 CSS)
            fc = f"[0:v]{vf}"; ins = ['-i', gif]
        else:  # 배경 띠 위에 합성
            top = by if sl[:5] in CANVAS_H else 0; hh = bh if sl[:5] in CANVAS_H else 1080
            band = f'/private/tmp/claude-501/-Users-bugi/06fa9a8d-6a63-4309-b4cc-1ac1b1af8b0e/scratchpad/band_{sl}.png'
            Image.open(f'{root}/slides/{sl[:5]}.png').convert('RGB').crop((0, top, 1920, top + hh)).save(band)
            fc = f"[1:v]{vf}[g];[0:v][g]overlay={bx}:{by - top}:shortest=1"; ins = ['-loop', '1', '-framerate', '50', '-i', band, '-i', gif]
            bx, by, bw, bh = 0, top, 1920, hh
        fc += ",scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        if not sl.startswith(os.environ.get('ONLY', '')): pass  # ONLY=05- 처럼 일부만 다시 인코딩
        else: subprocess.run(['ffmpeg','-y','-loglevel','error'] + ins + ['-filter_complex', fc, '-fps_mode','cfr','-r','50','-c:v','libx264','-crf','16','-preset','slow',
                        '-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1','-color_range','tv',
                        '-movflags','+faststart','-an'] + (['-t', str(NOLOOP[sl])] if sl in NOLOOP else []) + [f'{root}/{name}'], check=True)
        out.append(dict(slide=sl[:5], after=sl.endswith('b'), loop=sl not in NOLOOP, feather=sl in FEATHER, fade=FADE.get(sl, ''), src=name, box=[bx/1920, by/ch, bw/1920, bh/ch]))
    if not check:
        open(f'{root}/media/overlays.js','w').write('var OVERLAYS = ' + json.dumps(out, indent=1) + ';\n')
        print(len(out), 'videos')
