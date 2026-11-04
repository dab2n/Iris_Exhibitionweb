#!/bin/sh
# 스크롤 장의 '위 정렬로 나타남 → 카메라가 아래로 내려감 → 아래 영상 재생' 을 한 편의 1920x1080 영상으로 미리 렌더링
# (긴 이미지 안에서 영상 두 개를 같이 움직이면 기기에 따라 깜빡이고 어긋나서). tools/overlays.py 다음에 실행.
# 값은 index.html SCROLL 과 같아야 함: 대기 4초, 이동 1.5초(3차 ease-in-out), end(px)
cd "$(dirname "$0")/.."
ENC="-fps_mode cfr -r 50 -c:v libx264 -crf 16 -preset slow -threads 3 -colorspace bt709 -color_primaries bt709 -color_trc iec61966-2-1 -color_range tv -movflags +faststart -an"
CS="scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
# 메뉴 줄(장 맨 위 색 + 메뉴 글자, 아래 24px 흐려짐)을 영상에 같이 그림 — 웹 메뉴 배경과 영상 색이 기기마다 달라 보이는 것 방지
T=$(mktemp -d)
mknav() { python3 - "$1" "$T/cnav_$1.png" <<'PY'
import sys
from PIL import Image
k, out = sys.argv[1], sys.argv[2]
c = Image.open(f'slides/{k}.png').convert('RGB').getpixel((4, 4))
s = Image.new('RGBA', (1920, 144), c + (255,)); s.alpha_composite(Image.open(f'slides/{k}-nav.png').convert('RGBA'), (0, 0))
a = s.getchannel('A')
for y in range(120, 144): a.paste(int(255 * (1 - (y - 120) / 24)), (0, y, 1920, y + 1))
s.putalpha(a); s.save(out)
PY
}
mknav 02-01; mknav 02-04
Y() { echo "if(lt(t,4),0,if(gt(t,5.5),$1,$1*if(lt(t,4.75),4*pow((t-4)/1.5,3),1-pow(2-2*(t-4)/1.5,3)/2)))"; }   # 카메라 y(t)

# Research 01: 위 그래프(02-01, 반복) 는 처음부터, 아래 그래프(02-01b) 는 이동이 끝난 5.5초부터. 전체 16초(끝나면 웹이 긴 이미지로 넘겨 아래에 머묾)
nice -n 19 ffmpeg -y -loglevel error -loop 1 -framerate 50 -i slides/02-01.png -stream_loop -1 -i media/02-01.mp4 -i media/02-01b.mp4 -loop 1 -i $T/cnav_02-01.png -filter_complex \
 "[0:v]format=rgb24[bg];[2:v]tpad=start_duration=5.5:start_mode=clone[b];[bg][1:v]overlay=0:267:eof_action=repeat[x];[x][b]overlay=0:933:eof_action=repeat,crop=1920:1080:0:'$(Y 634)'[c];[c][3:v]overlay=0:0,trim=duration=16.0,$CS" \
 $ENC media/02-01-cam.mp4
# Research 04: 아래 카드(02-04b, 한 번) 는 5.5초부터 3초, 끝 장면에서 멈춤. 전체 8.5초
nice -n 19 ffmpeg -y -loglevel error -loop 1 -framerate 50 -i slides/02-04.png -i media/02-04b.mp4 -loop 1 -i $T/cnav_02-04.png -filter_complex \
 "[0:v]format=rgb24[bg];[1:v]tpad=start_duration=5.5:start_mode=clone[b];[bg][b]overlay=0:979:eof_action=repeat,crop=1920:1080:0:'$(Y 850)'[c];[c][2:v]overlay=0:0,trim=duration=8.5,$CS" \
 $ENC media/02-04-cam.mp4
# Process 02 온톨로지: 화면 녹화(모서리 12px 둥글게)를 처음부터, 녹화 한 바퀴(17.5초)와 같은 길이 → 끝나면 웹이 긴 이미지 + 장 안 녹화(처음부터)로 이어 받음
mknav 03-01
python3 -c "
from PIL import Image, ImageDraw
m = Image.new('L', (1344, 840), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 1343, 839), 11.5, fill=255); m.save('$T/round.png')"
nice -n 19 ffmpeg -y -loglevel error -loop 1 -framerate 50 -i slides/03-01.png -i media/03-01-rec.mp4 -loop 1 -i $T/round.png -loop 1 -i $T/cnav_03-01.png -filter_complex \
 "[0:v]format=rgb24[bg];[1:v]fps=50,format=rgba[r];[2:v]format=gray[m];[r][m]alphamerge[rr];[bg][rr]overlay=288:684:eof_action=repeat,crop=1920:1080:0:'$(Y 1030)'[c];[c][3:v]overlay=0:0,trim=duration=17.5,$CS" \
 $ENC media/03-01-cam.mp4
ls -la media/*-cam.mp4
