#!/bin/sh
# 한글 장을 이 맥의 SF Pro +KR 로 렌더링(헤드리스 크롬) → slides/. 피그마 서버 렌더는 한글이 대체 폰트라 쓰지 않음.
# 필요한 그림: tools/render/grid.png(피그마에서 글자 숨기고 내보낸 카드), rec0.png(media/03-02-rec.mp4 첫 장면)
cd "$(dirname "$0")"
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
shot() { "$C" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=$3 \
  --window-size=$2 --screenshot="$PWD/$1.png" "file://$PWD/$1.html" >/dev/null 2>&1; }
ffmpeg -v error -y -i ../../media/03-02-rec.mp4 -frames:v 1 rec0.png
shot usertest 1920,1080 1
shot ontology 2000,2160 0.96
pkill -f "Google Chrome.*--headless" 2>/dev/null   # 남은 헤드리스 크롬 회수(팬 소음 방지)
ls -la usertest.png ontology.png
