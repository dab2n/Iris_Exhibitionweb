"""GIF → 슬라이드 영역에 맞춘 mp4 로 변환. python3 tools/overlays.py [check]
각 항목: slide, gif, 블록 크기(B, Figma 원본 블록 px), 슬라이드에서의 창 크롭 r(블록 좌표), 배치 d=(x,y,scale)
recording 은 블록이 아닌 화면 녹화라 r 대신 box 를 직접 지정."""
import json, os, subprocess, sys
from PIL import Image
H = os.path.expanduser('~')
D = H + '/Desktop/'; DL = H + '/Downloads/iris-gif/화면만/'
def fit(rw, rh):
    s = min(1920 / rw, 960 / rh); return ((1920 - rw * s) / 2, 120 + (960 - rh * s) / 2, s)
def cy(x, w, rw, rh):
    s = w / rw; return (x, 120 + (960 - rh * s) / 2, s)
O = [  # slide, gif, block(w,h), region r, placement (x,y,s)
 # 스크롤 장(세로로 긴 캔버스, CANVAS_H): 키 끝 b = 스크롤이 끝난 뒤 재생
 ('02-01',  D+'Iris_StartingQuestion_v3_2000.gif', (2000,1322), (0,0,2000,694),    (0,267,0.96)),
 ('02-01b', D+'Iris_StartingQuestion_v3_2000.gif', (2000,1322), (0,694,2000,628),  (0,267+694*0.96,0.96)),
 ('02-04b', D+'Iris_InterviewPeel_4000.gif',       (2000,2168), (0,940,2000,1228), (200,205+940*0.76+60,0.76)),
 ('04-01', D+'Iris_GridSystem_4000.gif',          (2000,1358), (0,80,2000,1220),  fit(2000,1220)),
 ('05-01', D+'Iris_FlowMap_4000.gif',             (2000,1324), (100,100,1800,1110), cy(800,1080,1800,1110)),
 ('04-04', D+'Iris_CubeSlides_2000_HQ.gif',       (2000,1064), (0,0,2000,1000),   (0,120,0.96)),
 ('05-06', D+'Iris_FigjamPlugin_Flow_2000.gif',   (2000,1449), (0,0,2000,1449),   fit(2000,1449)),
 ('05-10', D+'Iris_Recording_2000.gif',           (2000,1162), (420,20,1160,1122),(885,150,0.811)),
 ('05-11', D+'Iris_12-1.gif',                     (2000,1102), (0,0,2000,1102),   fit(2000,1102)),
]
# 영상 앞 정지 구간을 뒤로 보내 들어오자마자 움직이게(초). 반복 주기는 같음
ROTATE = {'02-01b': 2.2}
CANVAS_H = {'02-01': 1714, '02-04': 1953}  # 피그마 '(스크롤)' 프레임 높이
# 플로우맵 화면 녹화: 블록 130:5140 안 플로우맵 프레임(1395x902) 위치에 그대로
for sl, f, fy, r in [('05-02','1_일반요약-플로우맵-오른쪽스크롤.gif',405,(0,90,2000,1240)),
                     ('05-03','2_화면확대-자유확대축소-오른쪽스크롤.gif',1813,(0,1490,2000,1260)),
                     ('05-04','3_플로우맵카드선택-원문확인.gif',3402,(0,3040,2000,1300))]:
    x, y, s = fit(r[2], r[3])
    O.append((sl, DL+f, None, None, (x + 302*s, y + (fy - r[1])*s, s, 1395*s, 902*s)))

def boxes(o):
    sl, gif, B, r, p = o
    if B is None: return dict(box=p[:2]+p[3:], crop=None)
    x, y, s = p; rx, ry, rw, rh = r
    rh = min(rh, B[1] - ry)  # 블록 끝에서 자름
    return dict(box=(x, y, rw*s, rh*s), crop=(rx, ry, rw, rh))

if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check = sys.argv[1:] == ['check']
    out = []
    for o in O:
        sl, gif = o[0], o[1]; b = boxes(o)
        bx, by, bw, bh = [round(v) for v in b['box']]; bw -= bw % 2; bh -= bh % 2
        im = Image.open(gif); g = im.size[0] / (o[2][0] if o[2] else im.size[0])
        if check:
            im.seek(im.n_frames - 1); fr = im.convert('RGB')
            if b['crop']: fr = fr.crop(tuple(round(v*g) for v in (b['crop'][0], b['crop'][1], b['crop'][0]+b['crop'][2], b['crop'][1]+b['crop'][3])))
            base = Image.open(f'{root}/slides/{sl[:5]}.png').convert('RGB'); base.paste(fr.resize((bw, bh)), (bx, by))
            base.save(f'/private/tmp/claude-501/-Users-bugi/06fa9a8d-6a63-4309-b4cc-1ac1b1af8b0e/scratchpad/gif/chk_{sl}.png'); continue
        vf = (f"crop={round(b['crop'][2]*g)}:{round(b['crop'][3]*g)}:{round(b['crop'][0]*g)}:{round(b['crop'][1]*g)}," if b['crop'] else '') + \
             f"scale={bw}:{bh}:flags=lanczos,format=yuv420p"
        name = f'media/{sl}.mp4'
        if sl in ROTATE:
            t = ROTATE[sl]
            vf = f"split[a][b];[a]trim=start={t},setpts=PTS-STARTPTS[x];[b]trim=end={t},setpts=PTS-STARTPTS[y];[x][y]concat," + vf
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',gif,'-filter_complex' if sl in ROTATE else '-vf',vf,'-c:v','libx264','-crf','16','-preset','slow',
                        '-movflags','+faststart','-an', f'{root}/{name}'], check=True)
        ch = CANVAS_H.get(sl[:5], 1080)
        out.append(dict(slide=sl[:5], after=sl.endswith('b'), src=name, box=[bx/1920, by/ch, bw/1920, bh/ch]))
    if not check:
        open(f'{root}/media/overlays.js','w').write('var OVERLAYS = ' + json.dumps(out, indent=1) + ';\n')
        print(len(out), 'videos')
