#!/bin/bash

# 🕒 현재 날짜와 시간 포맷으로 커밋 메시지 자동 생성
now=$(date +"%Y-%m-%d %H:%M:%S")

# ✍️ 커밋 메시지: "📦 업데이트 - 2024-04-13 14:25:32"
commit_message="📦 업데이트 - $now"

# 🔁 Git 작업 순서
git add .
git commit -m "$commit_message"
git push origin main

# ✅ 성공 메시지
echo ""
echo "🎉 GitHub에 성공적으로 푸시되었습니다!"
echo "🚀 Render에서 자동 배포가 시작됩니다 (잠시 후 URL에서 확인 가능)"
