from __future__ import annotations
from pathlib import Path
import dearpygui.dearpygui as dpg
import numpy as np

from src.utils import AppState, format_bytes
from src.core.data_loader import load_csv, apply_filter, clear_filter
from src.core.analysis import column_profile
from src.gui.visualization import (
    plot_quick_distribution, plot_generic,
    # 병합본 visualization.py의 추가 플롯들
    plot_heatmap_crosstab, plot_scatter_corr, plot_box_group,
    # New advanced visualization functions
    plot_regression_with_ci, plot_distribution_comparison, plot_pair_correlation,
    plot_time_series_decomposition, plot_advanced_categorical
)
from src.gui.layout import auto_ratio, apply_layout
from src.utils.export_utils import save_dataframe, save_analysis_report

# (Optional) combinations add-on: import if present
try:
    from src.core.combinations import analyze_combinations, suggest_plots
    HAVE_COMB = True
except Exception:
    HAVE_COMB = False

# Tags
TAG_PRIMARY = "Primary"
TAG_ANALYSIS_SCROLL = "analysis_scroll"
TAG_PLOT_CANVAS = "plot_canvas"
TAG_PREVIEW_TABLE = "preview_table"
TAG_LEFT = "left_panel"
TAG_RIGHT = "right_panel"
TAG_SPLITTER = "splitter_table"
TAG_SPLIT_GROUP = "split_group"
TAG_COMB_SCROLL = "comb_scroll"
TAG_RECO_GROUP = "reco_group"
TAG_FILE_DROP = "file_drop_handler"

LAST_REPORT = None  # 마지막 조합/분석 결과 저장

def _safe_set_value(tag: str, value: str):
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)

# === Toast & Progress Utils ===
def show_toast(message: str, kind: str = "info", duration_ms: int = 2200):
    colors = {
        "info":  (200, 220, 255),
        "ok":    (180, 240, 200),
        "warn":  (255, 220, 170),
        "error": (255, 180, 180),
    }
    col = colors.get(kind, colors["info"])
    tag = f"toast_{dpg.generate_uuid()}"
    with dpg.window(tag=tag, no_title_bar=True, no_move=True, no_resize=True,
                    no_collapse=True, modal=False, autosize=True, pos=(16, 16),
                    no_close=True, no_background=False):
        dpg.add_text(message, color=col)
    frames = max(1, duration_ms // 16)
    dpg.set_frame_callback(dpg.get_frame_count() + frames, lambda: dpg.delete_item(tag))

def begin_busy(status_text: str = "Working..."):
    _safe_set_value("status_text", status_text)
    if dpg.does_item_exist("busy_spinner"):
        dpg.configure_item("busy_spinner", show=True)
    if dpg.does_item_exist("status_progress"):
        dpg.configure_item("status_progress", show=True)
        dpg.set_value("status_progress", 0.0)

def set_progress(p: float):
    if dpg.does_item_exist("status_progress"):
        try:
            dpg.set_value("status_progress", max(0.0, min(1.0, float(p))))
        except Exception:
            pass

def end_busy(done_text: str = "Done", ok: bool = True):
    _safe_set_value("status_text", done_text)
    if dpg.does_item_exist("busy_spinner"):
        dpg.configure_item("busy_spinner", show=False)
    if dpg.does_item_exist("status_progress"):
        dpg.configure_item("status_progress", show=False)
    show_toast(done_text, "ok" if ok else "error")

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

        # --- Export ---
        with dpg.collapsing_header(label="Export", default_open=True):
            dpg.add_text("Export data / analysis")
            dpg.add_input_text(label="Filename", tag="export_filename", hint="예: results/analysis_out")
            dpg.add_combo(("CSV", "Excel", "JSON"), tag="export_format", default_value="CSV")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Data", callback=lambda: on_save_data(state))
                dpg.add_button(label="Save Analysis", callback=on_save_analysis)

        # --- Status / Progress ---
        dpg.add_separator()
        dpg.add_text("Status")
        with dpg.group(horizontal=True):
            dpg.add_loading_indicator(tag="busy_spinner", show=False, radius=8)
            dpg.add_progress_bar(tag="status_progress", show=False, width=-1)
        dpg.add_text("", tag="status_text", color=(180, 180, 180))

    # Allow CSV files to be dropped onto the left panel
    with dpg.item_handler_registry(tag=TAG_FILE_DROP):
        dpg.add_file_drop_handler(callback=on_files_dropped, user_data=state)
    dpg.bind_item_handler_registry(TAG_LEFT, TAG_FILE_DROP)
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
                    dpg.add_combo(["Histogram", "Box Plot", "Scatter Plot", "Line", "ECDF", "Violin", "Density", "QQ Plot", "Ridge"], label="Plot Type", width=150, tag="plot_type")
                    dpg.add_button(label="Generate Plot", callback=lambda: on_generate_plot(state))
                with dpg.child_window(height=650, tag=TAG_PLOT_CANVAS):
                    dpg.add_text("Select plot options above", color=(130, 130, 140))

            with dpg.tab(label="Advanced Plots"):
                with dpg.group(horizontal=True):
                    dpg.add_combo(["Regression Analysis", "Distribution Comparison", "Correlation Matrix", "Time Series", "Enhanced Categorical"], 
                                 label="Advanced Plot", width=180, tag="advanced_plot_type")
                    dpg.add_combo(["No columns loaded"], width=150, tag="adv_column1", label="Column 1")
                    dpg.add_combo(["No columns loaded"], width=150, tag="adv_column2", label="Column 2 (optional)")
                    dpg.add_button(label="Generate Advanced Plot", callback=lambda: on_generate_advanced_plot(state))
                with dpg.child_window(height=620, tag="advanced_plot_canvas"):
                    dpg.add_text("Select advanced plot options above", color=(130, 130, 140))

            if HAVE_COMB:
                with dpg.tab(label="Combinations"):
                    with dpg.group(horizontal=True):
                        dpg.add_slider_int(label="Top-K", tag="comb_topk", default_value=20, min_value=5, max_value=100)
                        dpg.add_slider_int(label="Max Cardinality", tag="comb_maxcard", default_value=50, min_value=5, max_value=200)
                        dpg.add_button(label="Analyze", callback=lambda: on_analyze_combinations(state))
                    with dpg.child_window(height=260, tag=TAG_COMB_SCROLL):
                        dpg.add_text("Run analysis to see combinations...", color=(130, 130, 140))
                    dpg.add_separator()
                    dpg.add_text("Recommended plots")
                    with dpg.group(tag=TAG_RECO_GROUP):
                        dpg.add_text("No recommendations yet.", color=(130,130,140))

def build_splitter(state: AppState):
    with dpg.group(horizontal=True, tag=TAG_SPLIT_GROUP):
        build_left_panel(state)
        build_right_panel(state)


def on_files_dropped(sender, app_data, state: AppState):
    """Handle file drops and load the first CSV path."""
    if not app_data:
        return
    try:
        file_path = app_data[0]
        on_file_selected(state, file_path)
    except Exception as e:
        _safe_set_value("status", f"[ERROR] Drop failed: {e}")
        show_toast(f"드래그앤드롭 오류: {e}", "error")

def on_file_selected(state: AppState, app_data):
    try:
        begin_busy("Loading CSV...")
        file_path = app_data['file_path_name'] if isinstance(app_data, dict) else app_data
        if not str(file_path).lower().endswith(".csv"):
            raise ValueError("CSV 파일만 지원합니다. .csv 파일을 선택하세요.")
        load_csv(state, file_path)
        _safe_set_value("status", f"[OK] Loaded: {Path(file_path).name}")
        _safe_set_value("row_count", f"{len(state.df):,}")
        _safe_set_value("col_count", f"{len(state.df.columns):,}")
        _safe_set_value("memory_usage", f"{format_bytes(state.df.memory_usage(deep=True).sum())}")
        cols = list(state.df.columns)
        dpg.configure_item("column_selector", items=cols)
        dpg.configure_item("analysis_column", items=cols)
        # Update advanced plot column dropdowns
        dpg.configure_item("adv_column1", items=cols)
        dpg.configure_item("adv_column2", items=["No columns loaded"] + cols)
        # 기본 파일명
        stem = Path(file_path).stem
        if dpg.does_item_exist("export_filename"):
            dpg.set_value("export_filename", f"{stem}_analysis")
        update_preview_table(state)
        if state.numeric_cols:
            try:
                set_progress(0.4)
                plot_quick_distribution(state.df, state.numeric_cols[0], "hist_tex", TAG_PLOT_CANVAS)
            except Exception:
                pass
        set_progress(0.8)
        auto_ratio(state)
        apply_layout(state)
        end_busy(f"[OK] CSV 로드 완료: {Path(file_path).name}", ok=True)
    except Exception as e:
        _safe_set_value("status", f"[ERROR] {str(e)}")
        end_busy(f"[ERROR] 로드 실패: {str(e)}", ok=False)

def open_csv_dialog(state: AppState):
    try:
        if not dpg.does_item_exist("file_dialog_id"):
            build_file_dialog(state)
        dpg.show_item("file_dialog_id")
    except Exception as e:
        _safe_set_value("status", f"[ERROR] File dialog: {e}")
        show_toast(f"파일 대화상자 오류: {e}", "error")

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
        show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn"); return
    column = dpg.get_value("analysis_column")
    if not column:
        show_toast("컬럼을 선택하세요.", "warn"); return
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
        show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn"); return
    column = dpg.get_value("analysis_column")
    plot_type = dpg.get_value("plot_type")
    if not column or not plot_type:
        show_toast("컬럼/플롯 타입을 선택하세요.", "warn"); return
    begin_busy(f"Generating: {plot_type} / {column}")
    try:
        plot_generic(state.df, column, plot_type, "hist_tex", TAG_PLOT_CANVAS)
        end_busy("[OK] 시각화 완료", ok=True)
    except Exception as e:
        end_busy(f"[ERROR] 시각화: {str(e)}", ok=False)

def on_generate_advanced_plot(state: AppState):
    if state.df is None:
        show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn"); return
    
    plot_type = dpg.get_value("advanced_plot_type")
    column1 = dpg.get_value("adv_column1")
    column2 = dpg.get_value("adv_column2")
    
    if not plot_type:
        show_toast("고급 플롯 타입을 선택하세요.", "warn"); return
    if not column1:
        show_toast("최소 하나의 컬럼을 선택하세요.", "warn"); return
    
    begin_busy(f"Generating advanced plot: {plot_type}")
    try:
        if plot_type == "Regression Analysis":
            if not column2:
                show_toast("회귀 분석에는 두 개의 컬럼이 필요합니다.", "warn"); return
            plot_regression_with_ci(state.df, column1, column2, "advanced_plot_canvas")
        elif plot_type == "Distribution Comparison":
            plot_distribution_comparison(state.df, column1, column2 if column2 != "No columns loaded" else None, "advanced_plot_canvas")
        elif plot_type == "Correlation Matrix":
            numeric_cols = state.df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                show_toast("상관관계 매트릭스에는 최소 2개의 수치형 컬럼이 필요합니다.", "warn"); return
            plot_pair_correlation(state.df, numeric_cols, parent_tag="advanced_plot_canvas")
        elif plot_type == "Time Series":
            if not column2:
                show_toast("시계열 분석에는 날짜/시간 컬럼과 값 컬럼이 필요합니다.", "warn"); return
            plot_time_series_decomposition(state.df, column1, column2, "advanced_plot_canvas")
        elif plot_type == "Enhanced Categorical":
            plot_advanced_categorical(state.df, column1, "advanced_plot_canvas")
        
        end_busy("[OK] 고급 시각화 완료", ok=True)
    except Exception as e:
        end_busy(f"[ERROR] 고급 시각화: {str(e)}", ok=False)

def on_apply_filter(state: AppState):
    if state.df is None:
        show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn"); return
    col = dpg.get_value("column_selector")
    cond = dpg.get_value("filter_condition")
    val = dpg.get_value("filter_value")
    if not col:
        show_toast("컬럼을 선택하세요.", "warn"); return
    if not cond:
        show_toast("조건을 선택하세요.", "warn"); return
    if val is None or str(val).strip() == "":
        show_toast("값을 입력하세요.", "warn"); return
    try:
        begin_busy("Applying filter...")
        if cond in ("Greater Than", "Less Than"):
            try:
                float(val)
            except Exception:
                raise ValueError("숫자 비교 조건에는 숫자 값을 입력하세요. (예: 10, 3.14)")
        apply_filter(state, col, cond, val)
        update_preview_table(state)
        _safe_set_value("status", f"Filter applied: {len(state.filtered_df) if state.filtered_df is not None else len(state.df)} rows")
        end_busy("[OK] 필터 적용 완료", ok=True)
    except Exception as e:
        _safe_set_value("status", f"[ERROR] Filter: {str(e)}")
        end_busy(f"[ERROR] 필터: {str(e)}", ok=False)

def on_reset_filters(state: AppState):
    if state.df is None:
        return
    clear_filter(state)
    update_preview_table(state)
    _safe_set_value("filter_value", "")
    _safe_set_value("status", "Filters reset")
    show_toast("필터 초기화", "info")

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

# Save handlers
def on_save_data(state: AppState):
    try:
        if state.df is None:
            show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn")
            return
        fmt = dpg.get_value("export_format") or "CSV"
        name = dpg.get_value("export_filename") or "analysis_out"
        data = state.filtered_df if state.filtered_df is not None else state.df
        path = save_dataframe(data, name, fmt)
        show_toast(f"[OK] Saved data → {path}", "ok")
        _safe_set_value("status", f"Saved data: {path}")
    except Exception as e:
        _safe_set_value("status", f"Export error: {e}")
        show_toast(f"[ERROR] Export: {e}", "error")

def on_save_analysis():
    try:
        global LAST_REPORT
        if LAST_REPORT is None:
            show_toast("먼저 Analyze를 실행하세요.", "warn")
            return
        name = dpg.get_value("export_filename") or "analysis_out"
        path = save_analysis_report(LAST_REPORT, name)
        show_toast(f"[OK] Saved analysis → {path}", "ok")
        _safe_set_value("status", f"Saved analysis: {path}")
    except Exception as e:
        _safe_set_value("status", f"Export error: {e}")
        show_toast(f"[ERROR] Export: {e}", "error")

# If Combinations tab exists
def on_analyze_combinations(state: AppState):
    if not HAVE_COMB:
        return
    if state.df is None:
        show_toast("데이터가 없습니다. CSV를 먼저 로드하세요.", "warn"); return
    topk = int(dpg.get_value("comb_topk") or 20)
    maxcard = int(dpg.get_value("comb_maxcard") or 50)
    dpg.delete_item(TAG_COMB_SCROLL, children_only=True)
    dpg.delete_item(TAG_RECO_GROUP, children_only=True)
    begin_busy("Analyzing combinations...")
    try:
        report = analyze_combinations(state.df, max_cardinality=maxcard, top_k=topk)
        global LAST_REPORT
        LAST_REPORT = report
        dpg.add_text(f"Rows: {report['meta']['rows']} | Num cols: {len(report['meta']['num_cols'])} | Cat cols: {len(report['meta']['cat_cols'])}", parent=TAG_COMB_SCROLL)
        dpg.add_separator(parent=TAG_COMB_SCROLL)
        for entry in report.get("catcat", [])[:3]:
            a,b = entry["cols"]
            dpg.add_text(f"Cat×Cat: {a} × {b}", parent=TAG_COMB_SCROLL)
        for entry in report.get("numnum", [])[:3]:
            a,b = entry["cols"]
            strength = max(abs(entry.get('pearson') or 0.0), abs(entry.get('spearman') or 0.0))
            dpg.add_text(f"Num×Num: {a} vs {b} (|r|max={strength:.2f})", parent=TAG_COMB_SCROLL)
        for entry in report.get("catnum", [])[:3]:
            c,n = entry["cols"]
            dpg.add_text(f"Cat×Num: {c} -> {n} (eta²={entry['eta2']:.2f})", parent=TAG_COMB_SCROLL)
        recs = suggest_plots(report)
        if not recs:
            dpg.add_text("No recommendations.", color=(130,130,140), parent=TAG_RECO_GROUP)
        else:
            for rec in recs:
                t = rec["type"]; cols = rec["cols"]; why = rec["why"]
                label = f"{t}: {', '.join(cols)} — {why}"
                def _cb(kind=t, cols=cols): _do_plot_from_reco(state, kind, cols)
                dpg.add_button(label=label, callback=_cb, parent=TAG_RECO_GROUP)
        end_busy("[OK] 조합 분석 완료", ok=True)
    except Exception as e:
        end_busy(f"[ERROR] 조합 분석: {str(e)}", ok=False)

def _do_plot_from_reco(state: AppState, kind: str, cols):
    if state.df is None:
        return
    if kind == "heatmap":
        plot_heatmap_crosstab(state.df, cols[0], cols[1], "lift")
    elif kind == "scatter":
        plot_scatter_corr(state.df, cols[0], cols[1])
    elif kind == "box":
        plot_box_group(state.df, cols[0], cols[1])
