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
    """Optimized CSV loading function"""
    return load_csv_optimized(state, path, dtype_map, nrows, chunk_size=50000)


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize data types for memory efficiency"""
    for col in df.columns:
        if df[col].dtype == "object":
            # Optimize string columns
            num_unique = df[col].nunique()
            num_total = len(df[col])

            if num_unique / num_total < 0.5:  # Less than 50% UniqueValue
                df[col] = df[col].astype("category")
        elif df[col].dtype == "int64":
            # Downcast integer types
            df[col] = pd.to_numeric(df[col], downcast="integer")
        elif df[col].dtype == "float64":
            # Downcast float types
            df[col] = pd.to_numeric(df[col], downcast="float")

    return df


def load_csv_optimized(
    state: AppState,
    path: str | Path,
    dtype_map: Optional[Dict[str, str]] = None,
    nrows: Optional[int] = None,
    chunk_size: Optional[int] = None,
) -> AppState:
    """Optimize memory usage with chunk-based loading"""
    p = Path(path)
    if not p.exists() or p.suffix.lower() != ".csv":
        raise ValueError("Please select a valid .csv file")

    engine = _infer_engine()
    state.preview_only = False
    state.file_size = p.stat().st_size

    try:
        # Load large files in chunks
        if chunk_size and p.stat().st_size > 100 * 1024 * 1024:  # 100MB or more
            chunks = []
            for chunk in pd.read_csv(
                p, chunksize=chunk_size, dtype=dtype_map, engine=engine
            ):
                chunks.append(chunk)
                # Monitor memory usage
                if len(chunks) * chunk_size > 1000000:  # 100만 Row 이상
                    break
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(p, dtype=dtype_map, nrows=nrows, engine=engine)

        # Apply data type optimization
        df = optimize_dtypes(df)

    except MemoryError:
        # Switch to preview mode on memory error
        df = pd.read_csv(p, dtype=dtype_map, nrows=50000, engine=engine)
        df = optimize_dtypes(df)
        state.preview_only = True

    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as err:
        # Preview mode also on parsing error
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
