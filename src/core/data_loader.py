from __future__ import annotations
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import pandas as pd

from src.utils import AppState


def _infer_engine() -> str:
    # Try pyarrow if installed; fallback to c engine
    try:
        import pyarrow  # noqa: F401

        return "pyarrow"
    except Exception:
        return "c"


def load_csv(
    state: AppState,
    path: str | Path,
    dtype_map: Optional[Dict[str, str]] = None,
    nrows: Optional[int] = None,
) -> AppState:
    """최적화된 CSV 로딩 함수"""
    return load_csv_optimized(state, path, dtype_map, nrows, chunk_size=50000)


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 타입을 메모리 효율적으로 최적화"""
    for col in df.columns:
        if df[col].dtype == "object":
            # 문자열 컬럼 최적화
            num_unique = df[col].nunique()
            num_total = len(df[col])

            if num_unique / num_total < 0.5:  # 50% 미만 고유값
                df[col] = df[col].astype("category")
        elif df[col].dtype == "int64":
            # 정수 타입 다운캐스팅
            df[col] = pd.to_numeric(df[col], downcast="integer")
        elif df[col].dtype == "float64":
            # 실수 타입 다운캐스팅
            df[col] = pd.to_numeric(df[col], downcast="float")

    return df


def load_csv_optimized(
    state: AppState,
    path: str | Path,
    dtype_map: Optional[Dict[str, str]] = None,
    nrows: Optional[int] = None,
    chunk_size: Optional[int] = None,
) -> AppState:
    """청크 단위 로딩으로 메모리 사용 최적화"""
    p = Path(path)
    if not p.exists() or p.suffix.lower() != ".csv":
        raise ValueError("Please select a valid .csv file")

    engine = _infer_engine()
    state.preview_only = False
    state.file_size = p.stat().st_size

    try:
        # 대용량 파일은 청크 단위로 로드
        if chunk_size and p.stat().st_size > 100 * 1024 * 1024:  # 100MB 이상
            chunks = []
            for chunk in pd.read_csv(
                p, chunksize=chunk_size, dtype=dtype_map, engine=engine
            ):
                chunks.append(chunk)
                # 메모리 사용량 모니터링
                if len(chunks) * chunk_size > 1000000:  # 100만 행 이상
                    break
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(p, dtype=dtype_map, nrows=nrows, engine=engine)

        # 데이터 타입 최적화 적용
        df = optimize_dtypes(df)

    except MemoryError:
        # 메모리 부족 시 프리뷰 모드로 전환
        df = pd.read_csv(p, dtype=dtype_map, nrows=50000, engine=engine)
        df = optimize_dtypes(df)
        state.preview_only = True

    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as err:
        # 파싱 오류 시에도 프리뷰 모드
        if state.file_size > 200 * 1024 * 1024 and nrows is None:
            df = pd.read_csv(p, dtype=dtype_map, nrows=50000, engine=engine)
            df = optimize_dtypes(df)
            state.preview_only = True
            logging.warning(
                "Failed to read full CSV (%s); loaded optimized preview instead.", err
            )
        else:
            raise

    state.df = df
    state.filtered_df = None
    state.file_path = p
    # Cache numeric cols
    state.numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    return state


def apply_filter(state: AppState, column: str, condition: str, value: str) -> AppState:
    if state.df is None:
        return state
    df = state.df
    try:
        if condition == "Equals":
            mask = df[column].astype(str) == value
        elif condition == "Greater Than":
            mask = pd.to_numeric(df[column], errors="coerce") > float(value)
        elif condition == "Less Than":
            mask = pd.to_numeric(df[column], errors="coerce") < float(value)
        elif condition == "Contains":
            mask = df[column].astype(str).str.contains(value, case=False, na=False)
        else:
            mask = pd.Series([True] * len(df), index=df.index)
        state.filtered_df = df[mask].copy()
    except Exception:
        # On any error, keep no filter rather than crashing
        state.filtered_df = df.copy()
    state.page_index = 0
    return state


def clear_filter(state: AppState) -> AppState:
    state.filtered_df = None
    state.page_index = 0
    return state
