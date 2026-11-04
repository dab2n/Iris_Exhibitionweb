#!/bin/sh
# 스크롤 장의 '위 정렬로 나타남 → 카메라가 아래로 내려감 → 아래 영상 재생' 을 한 편의 1920x1080 영상으로 미리 렌더링
# (긴 이미지 안에서 영상 두 개를 같이 움직이면 기기에 따라 깜빡이고 어긋나서). tools/overlays.py 다음에 실행.
# 값은 index.html SCROLL 과 같아야 함: 대기 4초, 이동 1.8초(사인 곡선), end(px)
cd "$(dirname "$0")/.."
ENC="-fps_mode cfr -r 50 -c:v libx264 -crf 16 -preset slow -threads 3 -colorspace bt709 -color_primaries bt709 -color_trc iec61966-2-1 -color_range tv -movflags +faststart -an"
CS="scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
Y() { echo "if(lt(t,4),0,if(gt(t,5.8),$1,$1*(1-cos(PI*(t-4)/1.8))/2))"; }   # 카메라 y(t)

# Research 01: 위 그래프(02-01, 반복) 는 처음부터, 아래 그래프(02-01b) 는 이동이 끝난 5.8초부터. 전체 16.3초, JS 가 5.8초~끝을 반복
nice -n 19 ffmpeg -y -loglevel error -loop 1 -framerate 50 -i slides/02-01.png -stream_loop -1 -i media/02-01.mp4 -i media/02-01b.mp4 -filter_complex \
 "[0:v]format=rgb24[bg];[2:v]tpad=start_duration=5.8:start_mode=clone[b];[bg][1:v]overlay=0:267:eof_action=repeat[x];[x][b]overlay=0:933:eof_action=repeat,crop=1920:1080:0:'$(Y 634)',trim=duration=16.3,$CS" \
 $ENC media/02-01-cam.mp4
# Research 04: 아래 카드(02-04b, 한 번) 는 5.8초부터 3초, 끝 장면에서 멈춤. 전체 8.8초
nice -n 19 ffmpeg -y -loglevel error -loop 1 -framerate 50 -i slides/02-04.png -i media/02-04b.mp4 -filter_complex \
 "[0:v]format=rgb24[bg];[1:v]tpad=start_duration=5.8:start_mode=clone[b];[bg][b]overlay=0:979:eof_action=repeat,crop=1920:1080:0:'$(Y 850)',trim=duration=8.8,$CS" \
 $ENC media/02-04-cam.mp4
ls -la media/*-cam.mp4
