# CSV-ANALYSIS-SLICER

CSV-ANALYSIS-SLICER는 대용량 CSV 파일을 슬라이스 개수 또는 용량(MB) 기준으로 자동 분할하고, 각 조각에 대해 통계 요약(describe)을 생성 및 저장하는 Python 유틸리티입니다.

## 기능

- 슬라이스 개수 기준 또는 용량(MB) 기준 분할 지원
- 각 슬라이스에 대해 pandas.describe() 통계 요약 생성
- .txt 형식으로 통계 요약 저장
- CLI, Jupyter Notebook, 일반 Python 스크립트 환경 모두 사용 가능

## 사용 예시

1. 슬라이스 개수 기준 (예: 10개로 분할):

from csv_analysis_slicer import smart_csv_slicer_visual

smart_csv_slicer_visual(
    input_path="data.csv",
    num_slices=10
)

2. 용량 기준 (예: 50MB 단위로 분할):

smart_csv_slicer_visual(
    input_path="data.csv",
    num_slices=None,
    max_mb_per_slice=50
)

## 출력 구조 예시

data_sliced/
├── slice_01.csv
├── slice_01_summary.txt
├── slice_02.csv
├── slice_02_summary.txt
...

## 요구 사항

- Python 3.7 이상
- pandas

설치 방법:

pip install pandas

## 라이선스

MIT License

## 작성자

프로젝트명: SCV-ANALYSIS-SLICER  
작성자: JUNI0827