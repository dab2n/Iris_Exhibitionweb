#!/bin/sh
# 배포 전에 실행: index.html 의 V 를 지금 시각으로 바꿔 이미지·영상 캐시를 새로 받게 함
cd "$(dirname "$0")/.." && sed -i '' "s/^var V = '[^']*';/var V = 'v$(date +%y%m%d%H%M%S)';/" index.html && grep -m1 "^var V" index.html
