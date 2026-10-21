# 제작 및 재현 안내

## 제출본의 범위

- 영상은 각각 90초, 1920×1080, 24fps, H.264/AAC입니다.
- 원본 제출물의 AI 인물 컷 11개와 오디오는 유지했습니다. 새 AI 생성이나 유료 API 호출은 수행하지 않았습니다.
- 모션그래픽 M06(45~55초): 선택 → 숫자 이동 → 결과 자막 순으로 조정했습니다.
- AI 영화 S07(36~44초): 비교 카드를 크게 가로 배치했습니다. 인물 반응 컷을 새로 추가하지 않았습니다.
- HTML은 기존 기획을 최종 영상의 계산에 맞춰 정리한 제출용 인터랙티브 시연입니다. 기존 영상의 직접 캡처 소스라는 의미는 아닙니다.

## 폴더와 실행

Python 3, Pillow, NumPy와 FFmpeg가 필요합니다. `requirements.txt`를 참고합니다. 렌더링 폰트는 `fonts/`의 Noto Sans CJK KR이며 라이선스는 같은 폴더의 LICENSE에 있습니다.

```bash
pip install -r requirements.txt
python motion_graphic/build_v3.py render
python ai_film/build_film.py ui
python ai_film/build_film.py audio
```

기본 결과는 각 스크립트 옆의 `_render/`에 생성됩니다. `OUT` 환경 변수로 바꿀 수 있습니다. 파일명의 v3/v5는 원본 제작 계보를 보존한 것이며 코드에는 2026-10-21 제출 정리 수정이 반영되어 있습니다.

AI 영화 전체를 처음부터 다시 조립하려면 Higgsfield 원본 클립이 별도로 필요합니다. 이 ZIP에는 생성 원본 클립과 참조 이미지가 없습니다. `build_film.py`의 `TL`에서 요구하는 S01, S02, S03, S05A, S08, S09A, S09B, S10A, S10B, S12A, S13 파일을 `_render/clips/`에 준비한 후 `assemble`을 실행해야 합니다. 원본이 없으면 코드가 자리표시 화면을 만들므로, 이를 완성 영상으로 제출하면 안 됩니다. 이미 완성된 제출 영상은 `video/`에 있습니다.

## 생성 기록과 프롬프트

`02_higgsfield_prompts_v5.txt`는 기획 단계의 생성용 프롬프트 문서입니다. 실제 영상 생성에는 이를 줄여 쓴 프롬프트를 사용했고, 모델은 이미지 gpt_image_2_5, 영상 seedance_2_5입니다. 생성 원본 클립은 Higgsfield 계정에 있으며 이 저장소에는 포함하지 않았습니다.

생성 작업 ID(Higgsfield): 인물 기준 이미지 0f88b07e-4a33-4b93-9103-e785236b6e2f, 방 기준 이미지 bd3ce6b0-9e8d-4b96-9746-d7e7fab13164, 영상 S01 67ceb9ab-01bb-4555-9cbe-57af2fefe0df, S02 7a9f59f4-c3d8-47cc-9052-1bae7962d8a4, S03 2155cb5e-a377-4833-9946-5a09cb306f96, S05A 7d300fea-25cb-4071-98be-a39b7e8370bf, S08 8f26f5af-81db-48c0-b085-0498d9688a23, S09A 5fb22553-238d-4977-85b4-f1e3995dd7e1, S09B 7ae43a02-4f1f-4c27-87b9-e366e29a591a, S10A 5e8602b9-beaa-43c0-89d4-46470af26602, S10B 74cfc787-5274-45b4-8b89-4625cf755a1d, S12A 9ec68058-b0ba-464b-ad6f-d2fc10941ca0, S13 039dd675-a19d-4c79-b200-beafb4ad045b.

## 음향

두 영상의 기존 AAC 오디오를 그대로 복사했습니다. 최종 기술 검수는 길이·규격·프레임 및 오디오 일치 검사입니다. 청감상의 음악적 완성도와 실제 스피커에서의 재생 품질은 별도 청취 대상입니다.

## GitHub

ZIP을 해제한 뒤 `midterm/` 폴더 내부의 파일과 하위 폴더를 저장소의 같은 위치에 업로드합니다. 학기 전체 README는 덮어쓰지 않습니다. 업로드 후 `midterm/README.md`에서 두 영상과 `report/final_report.pdf` 링크를 열어 확인합니다. 이 문서는 ZIP 제작 당시의 재현 안내입니다. 현재 제출 폴더에는 호환성을 개선한 AI 영화가 반영되어 있으며, 업로드 이력은 저장소의 커밋 기록에서 확인할 수 있습니다.
