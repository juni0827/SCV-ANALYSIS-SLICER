import os
import pandas as pd
from math import ceil

def smart_csv_slicer_visual(
    input_path: str,
    num_slices: int = None,             #자르고 싶은 조각 개수 (예: 10개로 나누기)
    max_mb_per_slice: int = 100,        #슬라이스당 최대 용량(MB), num_slices가 None일 때만 적용됨
    output_dir: str = None,             #결과 저장 디렉토리 경로 (None이면 자동 생성)
    include_summary: bool = True,       #각 분할 파일에 대해 describe() 통계 생성 여부
    save_summary_to_file: bool = True   #생성된 통계 요약을 .txt 파일로 저장할지 여부
):
    """
    대용량 CSV 파일을 슬라이스 개수 또는 용량(MB) 기준으로 나누고,
    각 슬라이스의 통계 요약도 출력 및 저장하는 함수입니다.

    Parameters
    ----------
    input_path : str
        분석할 원본 CSV 파일 경로
    num_slices : int or None
        조각 수 기준으로 나누고 싶을 때 사용 (예: 10 → 10조각)
    max_mb_per_slice : int
        num_slices가 None일 때만 작동. 조각당 최대 용량(MB) 기준 분할
    output_dir : str or None
        분할 파일 저장 디렉토리 (None이면 자동 생성됨)
    include_summary : bool
        각 슬라이스에 대해 요약 통계(describe) 생성 여부
    save_summary_to_file : bool
        생성된 요약 통계를 텍스트 파일로 저장할지 여부
    """

    # 입력 파일 존재 확인
    assert os.path.isfile(input_path), f"❌ 파일이 존재하지 않습니다: {input_path}"

    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = os.path.splitext(input_path)[0] + "_sliced"
    os.makedirs(output_dir, exist_ok=True)

    # 기본 정보 출력
    print("════════════════════════════════════════════════════════════════════")
    print(f" 입력 파일       : {input_path}")
    print(f" 출력 디렉토리   : {output_dir}")
    print(f" 분할 기준       : {'개수 기준 ' + str(num_slices) if num_slices else '용량 기준 ' + str(max_mb_per_slice) + 'MB'}")
    print("════════════════════════════════════════════════════════════════════\n")

    #헤더 따로 추출 (사용되진 않지만 향후 필요 가능)
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        header = f.readline()

    #전체 파일 크기 (Byte → MB)
    file_size = os.path.getsize(input_path)
    file_mb = file_size / (1024 * 1024)

    #슬라이스 개수 계산 (개수 기준 vs 용량 기준)
    if num_slices:
        estimated_slices = num_slices
    else:
        estimated_slices = ceil(file_mb / max_mb_per_slice)

    #전체 행 수 계산 (헤더 제외)
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        total_rows = sum(1 for _ in f) - 1

    #슬라이스당 행 수 계산
    rows_per_slice = ceil(total_rows / estimated_slices)

    print(f" 전체 파일 크기  : {file_mb:.2f} MB")
    print(f" 전체 행 수       : {total_rows}")
    print(f" 슬라이스당 행수 : ~{rows_per_slice}\n")

    #슬라이스 처리 시작
    summaries = []  # 슬라이스별 통계 요약 저장용 리스트
    reader = pd.read_csv(input_path, chunksize=rows_per_slice)

    for i, chunk in enumerate(reader):
        #슬라이스 파일명 구성 (예: CSV_SLICER.csv)
        slice_name = f"slice_{i+1:02}.csv"
        slice_path = os.path.join(output_dir, slice_name)

        #슬라이스 CSV 저장
        chunk.to_csv(slice_path, index=False)
        print(f" 저장 완료: {slice_name} ({len(chunk)} rows)")

        #통계 요약 처리
        if include_summary:
            summary = chunk.describe(include='all')
            summaries.append((slice_name, summary))

            #통계 요약 파일 저장
            if save_summary_to_file:
                summary_path = os.path.join(output_dir, f"{slice_name}_summary.txt")
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(f" 통계 요약 - {slice_name}\n\n")
                    f.write(summary.to_string())
                print(f" 통계 저장   : {slice_name}_summary.txt")

        print("────────────────────────────────────────────────────────────────────\n")

    #작업 완료 메시지
    print("모든 슬라이싱 작업이 완료되었습니다")
    return summaries