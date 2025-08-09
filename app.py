from __future__ import annotations
from pathlib import Path
import dearpygui.dearpygui as dpg

from utils import AppState
from ui import build_splitter, build_file_dialog, TAG_PRIMARY
from layout import on_resize, apply_layout, auto_ratio

def _try_load_font(paths):
    for p in paths:
        try:
            return dpg.add_font(p, 18)
        except Exception:
            continue
    return None

def main():
    dpg.create_context()

    # Fonts (한글/기본 글리프 포함)
    with dpg.font_registry():
        default_paths = [
            r"C:\Windows\Fonts\malgun.ttf",                                  # Windows
            r"/System/Library/Fonts/Supplemental/AppleGothic.ttf",           # macOS
            r"/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",       # Linux
        ]
        base_font = _try_load_font(default_paths)

        # 글리프 힌트는 '해당 폰트'에 parent로 달아야 함
        if base_font is not None:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=base_font)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean,  parent=base_font)
            dpg.bind_font(base_font)

    # Global theme
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (22,22,24))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (28,28,32))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (40,40,45))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (40,40,45))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (230,230,230))
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
    dpg.bind_theme(global_theme)

    state = AppState()

    with dpg.window(tag=TAG_PRIMARY, width=1200, height=800, no_title_bar=True, no_move=True):
        build_splitter(state)

    build_file_dialog(state)
    dpg.add_text("", tag="status", parent=TAG_PRIMARY)

    dpg.create_viewport(title="CSV Analyzer (Modular)", width=1200, height=820)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(TAG_PRIMARY, True)

    # Initial auto layout
    auto_ratio(state)
    apply_layout(state)

    # 리사이즈 시 항상 자동 레이아웃
    dpg.set_viewport_resize_callback(lambda s,a: on_resize(s,a,state))
    on_resize(None, None, state)

    try:
        dpg.start_dearpygui()
    finally:
        dpg.destroy_context()

if __name__ == "__main__":
    main()

