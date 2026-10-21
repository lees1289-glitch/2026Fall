# 중간고사 대체 과제

2026학년도 2학기 영어음성학응용 | 영어영문학과 2023130847 이승목

## 주제: 요리 할래말래

‘요리 할래말래’는 먹고 싶은 메뉴와 집에 있는 재료를 바탕으로 직접 요리와 배달의 **오늘 결제액, 한 끼 평균 비용, 식사까지 걸리는 시간**을 비교하고, 그날의 조건에 맞는 식사 선택을 돕는 서비스 구상입니다. 요리가 항상 정답이라고 말하지 않고, 배달이 더 맞는 날도 함께 보여 줍니다.

공모전(KOSAC) 준비 과정에서 출발한 아이디어를 이번 사업 구상 과제로 발전시켰습니다. 대상은 혼자 생활하는 2030세대입니다.

> 영상과 보고서의 금액·시간은 모두 시연용 예시이며 실제 가격이나 실제 절약을 보장하지 않습니다. 특정 배달 플랫폼의 공식 서비스가 아닌 개인 사업 제안입니다.

## 제출물

- [모션그래픽 영상 열기](video/motion_graphic_90s.mp4) · [AI 영화 열기](video/ai_film_90s.mp4) · [보고서 PDF 열기](report/final_report.pdf)
- [영상 재생 페이지](index.html): 전체 폴더를 내려받은 뒤 브라우저에서 열면 두 영상을 재생할 수 있습니다.
- 영상 파일 화면에서 재생되지 않으면 **Download raw file**로 내려받아 재생합니다.

한국어 설명 문장과 영상 자막은 보고서·HTML·제작 자료까지 격식체로 통일했습니다.

AI 영화에는 최종 호환성 개선본(H.264 / yuv420p / AAC, 90초)이 반영되어 있습니다.

## 파일 안내

| 구분 | 파일 | 설명 |
| --- | --- | --- |
| 모션그래픽 영상 | [video/motion_graphic_90s.mp4](video/motion_graphic_90s.mp4) | 90초, 1920×1080, 24fps. 한국어 자막, 합성 음악·효과음, 나레이션 없음. 문제·비교 방식·대상·실행 계획을 설명 |
| AI 영화 영상 | [video/ai_film_90s.mp4](video/ai_film_90s.mp4) | 90초, 1920×1080, 24fps. AI 생성 영상 컷과 서비스 화면으로 구성한 생활 단편. 대사 없음 |
| 보고서(PDF) | [report/final_report.pdf](report/final_report.pdf) | 사업 구상의 이유·내용·계획·절차, 두 영상의 구성과 제작 과정 |

## 제작 자료

- 모션그래픽: [최종 장면 구성](materials/motion_graphic/storyboard_final.md), [자막](materials/motion_graphic/subtitles_v3.srt), 제작 코드([build_v3.py](materials/motion_graphic/build_v3.py), [core.py](materials/motion_graphic/core.py))
- AI 영화: [콘티](materials/ai_film/01_film_storyboard_v5.md), [AI 영상 생성 프롬프트](materials/ai_film/02_higgsfield_prompts_v5.txt), 화면·소리·조립 코드([build_film.py](materials/ai_film/build_film.py), [core.py](materials/ai_film/core.py))

## 제작 방법 요약

- **모션그래픽:** Python(Pillow)으로 프레임을 직접 그리고, 음악·효과음은 NumPy로 합성한 뒤 FFmpeg로 인코딩했습니다.
- **AI 영화:** Higgsfield(모델명은 제출자 제공 기록 기준이며 상세 실행 로그는 미첨부)로 인물·방 기준 이미지와 컷별 첫 장면을 만든 뒤 영상을 생성했습니다. 서비스 화면과 소리는 코드로 만들어 합성했습니다. 영화 속 인물과 장소는 AI가 만든 가상의 사람과 공간입니다.
- **도구:** 사업 구상과 장면 결정은 이승목, 초기 기획·콘티 정리와 이번 제출본 검수·수정에는 ChatGPT/Codex를, 제공된 영상의 콘티·코드·문서 제작에는 Claude(Anthropic)를 활용했습니다.

## HTML 시연 및 제작 기록

- [HTML 시연](prototype/yori_prototype.html): 내려받아 브라우저에서 엽니다. GitHub의 파일 화면은 실행 화면이 아닙니다.
- [제작·재현 안내](materials/PRODUCTION_NOTES.md)
- [수정 이력과 확인 범위](CHANGELOG.md)
- [편집 가능한 보고서 본문](report/report_source.md)

2026-10-21 정리본: 모션그래픽 45~55초의 자막 타이밍과 AI 영화 36~44초의 비교 화면을 수정했습니다. 원본 AI 인물 영상과 오디오는 유지했습니다. 상세 생성 로그·원본 참조 이미지는 미첨부이며 제출된 프롬프트를 실제 작업 로그라고 주장하지 않습니다.

---

[학기 전체 안내로 돌아가기](../README.md)
