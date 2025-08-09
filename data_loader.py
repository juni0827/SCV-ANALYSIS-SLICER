
from __future__ import annotations
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd

from utils import AppState

def _infer_engine() -> str:
    # Try pyarrow if installed; fallback to c engine
    try:
        import pyarrow  # noqa: F401
        return "pyarrow"
    except Exception:
        return "c"

def load_csv(state: AppState, path: str | Path, dtype_map: Optional[Dict[str, str]] = None, nrows: Optional[int] = None) -> AppState:
    p = Path(path)
    if not p.exists() or p.suffix.lower() != ".csv":
        raise ValueError("Please select a valid .csv file")
    engine = _infer_engine()
    state.preview_only = False
    state.file_size = p.stat().st_size
    try:
        df = pd.read_csv(p, dtype=dtype_map, nrows=nrows, engine=engine)
    except MemoryError:
        # Fallback to preview mode
        df = pd.read_csv(p, dtype=dtype_map, nrows=100_000, engine=engine)
        state.preview_only = True
    except Exception as e:
        # Heuristic: for very large files, auto-preview
        if state.file_size > 200 * 1024 * 1024 and nrows is None:
            df = pd.read_csv(p, dtype=dtype_map, nrows=100_000, engine=engine)
            state.preview_only = True
        else:
            raise
    state.df = df
    state.filtered_df = None
    state.file_path = p
    # Cache numeric cols
    state.numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    return state

def memory_usage(df: pd.DataFrame) -> int:
    return int(df.memory_usage(deep=True).sum())

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
