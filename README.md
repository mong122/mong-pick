# 🎯 오늘 놓치면 아까운 공고 (MONG 생활노트)

주소: https://mong122.github.io/mong-pick/

- 누르면 MONG 생활노트 **채용정보** 글 중 **마감 안 지난 공고 하나**를 골라 (마감이 가까울수록 자주) 카드로 보여 주고 3초 뒤 그 글로 보냄
- 목록 `jobs.json` = 깃허브 Actions 가 한 시간마다 블로그 RSS 로 다시 만듦 (`scripts/update.py`, 사람 손·열쇠 필요 없음)
- 마감일은 글 제목·첫 문단의 "M월 D일 … 마감/까지" 에서 뽑음. 못 뽑거나 틀리면 `overrides.json` 에 `{"글 주소": {"end": "2026-10-28T10:00"}}` (숨기려면 `{"hide": true}`)
- 링크 카드 그림 = `og.png`

## 방문 수 보기
- 전체: https://hitscounter.dev/history?url=mong122.github.io%2Fmong-pick%2Fall
- 블로그 글에서: https://hitscounter.dev/history?url=mong122.github.io%2Fmong-pick%2Fblog
- 쓰레드: https://hitscounter.dev/history?url=mong122.github.io%2Fmong-pick%2Fthreads
- X: https://hitscounter.dev/history?url=mong122.github.io%2Fmong-pick%2Fx
- 링크 주소 끝에 `?from=blog` · `?from=threads` · `?from=x` 를 붙여서 씀
