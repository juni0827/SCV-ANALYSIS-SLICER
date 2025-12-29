"""
GUI Application State
"""
from __future__ import annotations
import pandas as pd


class AppState:
    """Application state for GUI"""
    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.filtered_df: pd.DataFrame | None = None
        self.page_index: int = 0
        self.page_size: int = 100
        self.numeric_cols: list[str] = []
        self.categorical_cols: list[str] = []
