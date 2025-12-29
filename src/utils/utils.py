
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import pandas as pd

@dataclass
class AppState:
    df: Optional[pd.DataFrame] = None
    filtered_df: Optional[pd.DataFrame] = None
    file_path: Optional[Path] = None
    file_size: int = 0
    preview_only: bool = False
    # table pagination
    page_size: int = 100
    page_index: int = 0
    # UI cache
    numeric_cols: List[str] = field(default_factory=list)
    # UI layout
    split_ratio: float = 0.26  # left panel width ratio (0..1)
    min_left_px: int = 260
    min_right_px: int = 560
    # user interaction
    user_overridden: bool = False

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def format_bytes(num_bytes: int) -> str:
    mb = num_bytes / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.1f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"
