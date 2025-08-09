from __future__ import annotations
from pathlib import Path
import dearpygui.dearpygui as dpg

from utils import AppState, format_bytes
from data_loader import load_csv, apply_filter, clear_filter
from analysis import column_profile
from visualization import plot_quick_distribution, plot_generic
from layout import auto_ratio, apply_layout

# Tags
TAG_PRIMARY = "Primary"
TAG_ANALYSIS_SCROLL = "analysis_scroll"
TAG_PLOT_CANVAS = "plot_canvas"
TAG_PREVIEW_TABLE = "preview_table"
TAG_LEFT = "left_panel"
TAG_RIGHT = "right_panel"
TAG_SPLITTER = "splitter_table"
TAG_SPLIT_GROUP = "split_group"

def _safe_set_value(tag: str, value: str):
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)

def build_left_panel(state: AppState):
    with dpg.child_window(tag=TAG_LEFT, width=300, autosize_y=True, border=True):
        with dpg.group(horizontal=True):
            dpg.add_text("CSV"); dpg.add_text("ANALYZER", color=(65, 105, 225))
        dpg.add_separator()
        dpg.add_button(label="Load CSV File", width=-1, height=45, callback=lambda: open_csv_dialog(state))
        dpg.add_text("or drag and drop CSV file here", color=(130, 130, 140))
        dpg.add_spacer(height=10)

        with dpg.collapsing_header(label="Data Filters", default_open=True):
            dpg.add_text("Filter Options")
            dpg.add_text("Column:")
            dpg.add_combo(["No data loaded"], width=-1, tag="column_selector")
            dpg.add_text("Condition:")
            dpg.add_radio_button(("Equals", "Greater Than", "Less Than", "Contains"),
                                 horizontal=False, tag="filter_condition")
            dpg.add_input_text(label="Value", tag="filter_value")
            dpg.add_button(label="Apply Filter", width=-1, callback=lambda: on_apply_filter(state))
            dpg.add_button(label="Reset", width=-1, callback=lambda: on_reset_filters(state))

        with dpg.collapsing_header(label="Statistics", default_open=True):
            dpg.add_text("Data Overview")
            with dpg.table(header_row=False):
                dpg.add_table_column(); dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_text("Total Rows:"); dpg.add_text("0", tag="row_count")
                with dpg.table_row():
                    dpg.add_text("Columns:"); dpg.add_text("0", tag="col_count")
                with dpg.table_row():
                    dpg.add_text("Memory:"); dpg.add_text("0 MB", tag="memory_usage")

        with dpg.collapsing_header(label="Preview Controls", default_open=True):
            dpg.add_slider_int(label="Rows per page", tag="page_size", default_value=100, min_value=50, max_value=1000, callback=lambda s,a: on_page_size_change(state))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Prev Page", callback=lambda: on_change_page(state, -1))
                dpg.add_spacer(width=8)
                dpg.add_button(label="Next Page", callback=lambda: on_change_page(state, +1))
            dpg.add_text("Page: 0", tag="page_label")

def build_right_panel(state: AppState):
    with dpg.child_window(tag=TAG_RIGHT, width=880, autosize_y=True):
        with dpg.tab_bar():
            with dpg.tab(label="Analysis"):
                with dpg.group(horizontal=True):
                    dpg.add_combo(["No columns loaded"], width=200, tag="analysis_column")
                    dpg.add_button(label="Analyze Column", callback=lambda: on_analyze_column(state))
                with dpg.child_window(height=350, tag=TAG_ANALYSIS_SCROLL):
                    dpg.add_text("Select a column to analyze", color=(130, 130, 140))
                dpg.add_separator()
                dpg.add_text("Preview (paginated)")
                with dpg.table(tag=TAG_PREVIEW_TABLE, resizable=True, policy=dpg.mvTable_SizingStretchProp, row_background=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True):
                    pass
            with dpg.tab(label="Visualization"):
                with dpg.group(horizontal=True):
                    dpg.add_combo(["Histogram", "Box Plot", "Scatter Plot", "Line", "ECDF"], label="Plot Type", width=150, tag="plot_type")
                    dpg.add_button(label="Generate Plot", callback=lambda: on_generate_plot(state))
                with dpg.child_window(height=650, tag=TAG_PLOT_CANVAS):
                    dpg.add_text("Select plot options above", color=(130, 130, 140))

def build_splitter(state: AppState):
    # 단순 수평 그룹 기반(완전 자동 레이아웃)
    with dpg.group(horizontal=True, tag=TAG_SPLIT_GROUP):
        build_left_panel(state)
        build_right_panel(state)

def on_file_selected(state: AppState, app_data):
    try:
        file_path = app_data['file_path_name'] if isinstance(app_data, dict) else app_data
        load_csv(state, file_path)
        _safe_set_value("status", f"✓ Loaded: {Path(file_path).name}")
        _safe_set_value("row_count", f"{len(state.df):,}")
        _safe_set_value("col_count", f"{len(state.df.columns):,}")
        _safe_set_value("memory_usage", f"{format_bytes(state.df.memory_usage(deep=True).sum())}")
        cols = list(state.df.columns)
        dpg.configure_item("column_selector", items=cols)
        dpg.configure_item("analysis_column", items=cols)
        update_preview_table(state)
        if state.numeric_cols:
            try:
                plot_quick_distribution(state.df, state.numeric_cols[0], "hist_tex", TAG_PLOT_CANVAS)
            except Exception:
                pass
        # 파일 로드 후 자동 레이아웃 적용
        auto_ratio(state)
        apply_layout(state)
    except Exception as e:
        _safe_set_value("status", f"❌ Error: {str(e)}")

def open_csv_dialog(state: AppState):
    try:
        if not dpg.does_item_exist("file_dialog_id"):
            build_file_dialog(state)
        dpg.show_item("file_dialog_id")
    except Exception as e:
        _safe_set_value("status", f"❌ File dialog error: {e}")

def build_file_dialog(state: AppState):
    with dpg.file_dialog(directory_selector=False, show=False, callback=lambda s,a: on_file_selected(state, a),
                        tag="file_dialog_id", width=700, height=400, modal=True):
        dpg.add_file_extension(".csv", color=(65, 105, 225))
        dpg.add_file_extension(".*")

def update_preview_table(state: AppState):
    data = state.filtered_df if state.filtered_df is not None else state.df
    if data is None:
        return
    dpg.delete_item(TAG_PREVIEW_TABLE, children_only=True)
    for col in data.columns:
        dpg.add_table_column(label=str(col), parent=TAG_PREVIEW_TABLE)
    start = max(0, state.page_index * state.page_size)
    end = min(len(data), start + state.page_size)
    view = data.iloc[start:end]
    for _, row in view.iterrows():
        with dpg.table_row(parent=TAG_PREVIEW_TABLE):
            for col in data.columns:
                dpg.add_text(str(row[col]))
    _safe_set_value("page_label", f"Page: {state.page_index} (rows {start}-{end-1})")

def on_analyze_column(state: AppState):
    if state.df is None:
        return
    column = dpg.get_value("analysis_column")
    if not column:
        return
    dpg.delete_item(TAG_ANALYSIS_SCROLL, children_only=True)
    info = column_profile(state.df, column)
    dpg.add_text(f"Analysis for: {column}", color=(65,105,225), parent=TAG_ANALYSIS_SCROLL)
    dpg.add_separator(parent=TAG_ANALYSIS_SCROLL)
    with dpg.table(header_row=False, parent=TAG_ANALYSIS_SCROLL):
        dpg.add_table_column(); dpg.add_table_column()
        for k, v in info.items():
            with dpg.table_row():
                dpg.add_text(str(k)); dpg.add_text(f"{v}")

def on_generate_plot(state: AppState):
    if state.df is None:
        return
    column = dpg.get_value("analysis_column")
    plot_type = dpg.get_value("plot_type")
    if not column or not plot_type:
        return
    plot_generic(state.df, column, plot_type, "hist_tex", TAG_PLOT_CANVAS)

def on_apply_filter(state: AppState):
    if state.df is None:
        return
    col = dpg.get_value("column_selector")
    cond = dpg.get_value("filter_condition")
    val = dpg.get_value("filter_value")
    if not col or not cond or val is None:
        return
    apply_filter(state, col, cond, val)
    update_preview_table(state)
    _safe_set_value("status", f"Filter applied: {len(state.filtered_df) if state.filtered_df is not None else len(state.df)} rows")

def on_reset_filters(state: AppState):
    if state.df is None:
        return
    clear_filter(state)
    update_preview_table(state)
    _safe_set_value("filter_value", "")
    _safe_set_value("status", "Filters reset")

def on_change_page(state: AppState, delta: int):
    if state.df is None:
        return
    total_rows = len(state.filtered_df) if state.filtered_df is not None else len(state.df)
    max_page = max(0, (total_rows - 1) // state.page_size)
    state.page_index = min(max(state.page_index + delta, 0), max_page)
    update_preview_table(state)

def on_page_size_change(state: AppState):
    if state.df is None:
        return
    val = dpg.get_value("page_size")
    try:
        val = int(val)
    except Exception:
        val = 100
    state.page_size = max(10, min(val, 5000))
    state.page_index = 0
    update_preview_table(state)
