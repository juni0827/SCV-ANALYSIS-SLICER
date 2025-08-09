from __future__ import annotations
import dearpygui.dearpygui as dpg
from utils import AppState

# Tag strings
TAG_PRIMARY = "Primary"
TAG_LEFT = "left_panel"
TAG_RIGHT = "right_panel"
TAG_SPLITTER = "splitter_table"  # legacy (unused with group splitter)

def auto_ratio(state: AppState):
    """자동 비율 산정: 컬럼 수가 많을수록 오른쪽(표/그래프) 더 넓게, 좌측은 22–34% 범위."""
    try:
        vw = max(800, dpg.get_viewport_client_width())
        cols = int(state.df.shape[1]) if state.df is not None else 0
        right_ratio = 0.64 + min(0.18, max(0.0, (cols - 6) * 0.005))
        left_ratio = 1.0 - right_ratio
        state.split_ratio = max(0.22, min(0.34, left_ratio))
    except Exception:
        state.split_ratio = 0.26

def apply_layout(state: AppState):
    try:
        vw = dpg.get_viewport_client_width()
        vh = dpg.get_viewport_client_height()

        # 주창 크기
        dpg.set_item_width(TAG_PRIMARY, vw)
        dpg.set_item_height(TAG_PRIMARY, vh)

        # 패널 폭
        left_w = max(int(vw * state.split_ratio), state.min_left_px)
        right_w = max(vw - left_w - 24, state.min_right_px)

        if dpg.does_item_exist(TAG_LEFT):
            dpg.set_item_width(TAG_LEFT, left_w)
            dpg.set_item_height(TAG_LEFT, vh - 35)
        if dpg.does_item_exist(TAG_RIGHT):
            dpg.set_item_width(TAG_RIGHT, right_w)
            dpg.set_item_height(TAG_RIGHT, vh - 35)
    except Exception:
        pass

def on_resize(sender, app_data, state: AppState):
    # 항상 자동
    auto_ratio(state)
    apply_layout(state)
