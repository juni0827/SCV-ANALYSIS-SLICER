from __future__ import annotations
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import threading
import time
from tkinter import font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
import numpy as np

# Import from modular structure
from src.gui.state import AppState
from src.gui.components.toast import ToastWindow
from src.gui.components.cache import DataCache
from src.gui.threads import BackgroundTaskManager


def format_bytes(size: int) -> str:
    power = 1024
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power and n < len(power_labels):
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


def load_csv(state: AppState, file_path: str):
    state.df = pd.read_csv(file_path)
    state.numeric_cols = state.df.select_dtypes(include="number").columns.tolist()


def column_profile(df: pd.DataFrame, column: str) -> dict:
    return {
        "Type": str(df[column].dtype),
        "Unique": len(df[column].unique()),
        "Missing": f"{df[column].isnull().sum()}",
        "Non-null": f"{df[column].notna().sum()}",
        "Min": (
            str(df[column].min()) if df[column].dtype in ["int64", "float64"] else "N/A"
        ),
        "Max": (
            str(df[column].max()) if df[column].dtype in ["int64", "float64"] else "N/A"
        ),
        "Mean": (
            f"{df[column].mean():.2f}"
            if df[column].dtype in ["int64", "float64"]
            else "N/A"
        ),
    }


class CSVAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.state = AppState()
        self.toast = None
        self.busy_after_id = None

        # Add caching system
        self.data_cache = DataCache()

        # Background task manager Add
        self.task_manager = BackgroundTaskManager(root)

        # Dark mode configuration
        self.is_dark_mode = False
        self.setup_themes()
        self.setup_styles()
        self.setup_ui()

    def setup_themes(self):
        """Light/dark mode color theme configuration"""
        self.themes = {
            "light": {
                "bg": "#FAFAFA",
                "panel_bg": "#FFFFFF",
                "text_color": "#2C3E50",
                "secondary_text": "#7F8C8D",
                "accent": "#3498DB",
                "button_bg": "#3498DB",
                "button_fg": "#FFFFFF",
                "entry_bg": "#FFFFFF",
                "tree_bg": "#F8F9FA",
                "border": "#E9ECEF",
                "hover": "#E3F2FD",
            },
            "dark": {
                "bg": "#1E1E1E",
                "panel_bg": "#2D2D30",
                "text_color": "#CCCCCC",  # softer gray
                "secondary_text": "#9E9E9E",  # secondary text also soft
                "accent": "#0E7EB8",
                "button_bg": "#0E7EB8",
                "button_fg": "#F5F5F5",  # button text soft white instead of pure white
                "entry_bg": "#3C3C3C",
                "tree_bg": "#252526",
                "border": "#3E3E42",
                "hover": "#094771",
            },
        }

    def update_widget_theme_optimized(self, widget, theme, visited=None, max_depth=10):
        """Optimized theme update (recursive call limit 및 캐싱)"""
        if visited is None:
            visited = set()

        widget_id = id(widget)
        if widget_id in visited:
            return
        visited.add(widget_id)

        # maximum visit limit 및 depth limit
        if len(visited) > 1000 or max_depth <= 0:
            return

        try:
            widget_class = widget.winfo_class()

            # 자주 Use되는 위젯 Type 우선 Processing
            if widget_class in ["Frame", "Toplevel"]:
                if widget_class == "Frame":
                    widget.configure(bg=theme["panel_bg"])
            elif widget_class == "Label":
                # 라벨 Background color이 테마 색상if Update
                current_bg = str(widget.cget("bg"))
                if current_bg in [
                    "white",
                    "#FFFFFF",
                    "#2D2D30",
                    "#FAFAFA",
                    "#383838",
                    "#2B2B2B",
                ]:
                    widget.configure(bg=theme["panel_bg"], fg=theme["text_color"])
            elif widget_class == "Button":
                # 일반 버튼만 Update (특정 버튼 Exclude)
                current_text = str(widget.cget("text"))
                if current_text not in ["🌙", "☀️", "Toggle Dark Mode"]:
                    current_bg = str(widget.cget("bg"))
                    if current_bg in [
                        "#F0F0F0",
                        "#FAFAFA",
                        "#E1E1E1",
                        "#D4D4D4",
                        "#2B2B2B",
                        "#383838",
                        "SystemButtonFace",
                    ]:
                        widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
            elif widget_class == "Text":
                widget.configure(
                    bg=theme["tree_bg"],
                    fg=theme["text_color"],
                    insertbackground=theme["text_color"],
                )
            elif widget_class == "Entry":
                widget.configure(
                    bg=theme["entry_bg"],
                    fg=theme["text_color"],
                    insertbackground=theme["text_color"],
                    relief="flat",
                    bd=1,
                )

            # 자식 위젯들에 제한된 깊이로 재귀 적용
            for child in widget.winfo_children():
                self.update_widget_theme_optimized(child, theme, visited, max_depth - 1)

        except tk.TclError:
            # Some 위젯은 특정 속성을 Support하지 않을 수 Exists
            pass
        """스타일 Configuration"""
        style = ttk.Style()
        style.theme_use("clam")
        self.apply_theme_styles()

    def apply_theme_styles(self):
        """현재 테마에 맞는 스타일 적용"""
        style = ttk.Style()
        theme = self.current_theme

        # TTK 스타일 Configuration
        style.configure(
            "Title.TLabel", font=("Arial", 12, "bold"), foreground=theme["accent"]
        )
        style.configure(
            "Subtitle.TLabel", font=("Arial", 9), foreground=theme["secondary_text"]
        )
        style.configure(
            "Stats.TLabel", font=("Arial", 9), foreground=theme["text_color"]
        )
        style.configure(
            "BigButton.TButton", font=("Arial", 10, "bold"), padding=(10, 15)
        )

        # Notebook 스타일
        style.configure("TNotebook", background=theme["panel_bg"])
        style.configure(
            "TNotebook.Tab",
            background=theme["button_bg"],
            foreground=theme["button_fg"],
        )

        # Frame 스타일
        style.configure("TFrame", background=theme["panel_bg"])
        style.configure(
            "TLabelFrame", background=theme["panel_bg"], foreground=theme["text_color"]
        )

        # Treeview 스타일
        style.configure(
            "Treeview",
            background=theme["tree_bg"],
            foreground=theme["text_color"],
            fieldbackground=theme["tree_bg"],
        )
        style.configure(
            "Treeview.Heading",
            background=theme["button_bg"],
            foreground=theme["button_fg"],
        )

    def toggle_dark_mode(self):
        """다크Mode 토글 (부드러운 전환 효과)"""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = (
            self.themes["dark"] if self.is_dark_mode else self.themes["light"]
        )

        # 부드러운 전환을 위한 단계별 적용
        self.apply_theme_transition()

        # Statistics 컨테이너 스타일 Update
        self.root.after(100, self.update_stats_container_style)

        # Statistics 라벨 강제 Update
        self.root.after(200, lambda: self.force_update_stat_labels(self.current_theme))

    def apply_theme_transition(self):
        """부드러운 Theme switching"""
        # 스타일 먼저 적용
        self.apply_theme_styles()

        # 위젯들에 Sequential적으로 적용 (애니메이션 효과)
        self.transition_step = 0
        self.transition_widgets()

    def transition_widgets(self):
        """위젯 전환 애니메이션"""
        if self.transition_step == 0:
            # 1단계: 메인 배경
            self.root.configure(bg=self.current_theme["bg"])
            self.transition_step += 1
            self.root.after(50, self.transition_widgets)
        elif self.transition_step == 1:
            # 2단계: 패널들
            self.apply_theme_to_panels()
            self.transition_step += 1
            self.root.after(50, self.transition_widgets)
        elif self.transition_step == 2:
            # 3단계: 텍스트 요소들
            self.apply_theme_to_text_elements()
            self.transition_step += 1
            self.root.after(50, self.transition_widgets)
        elif self.transition_step == 3:
            # 4단계: 마무리 및 버튼 Update
            self.finalize_theme_transition()

    def apply_theme_to_panels(self):
        """패널 위젯들에 테마 적용"""
        theme = self.current_theme

        # 메인 컨테이너들 찾아서 Update
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                self.update_frame_theme(widget, theme)

    def apply_theme_to_text_elements(self):
        """텍스트 요소들에 테마 적용"""
        theme = self.current_theme

        # 분석 텍스트 영역
        if hasattr(self, "analysis_text"):
            self.analysis_text.configure(
                bg=theme["tree_bg"],
                fg=theme["text_color"],
                insertbackground=theme["text_color"],
            )

        # Statistics 라벨들 색상 Update
        if hasattr(self, "rows_label") and self.rows_label.winfo_exists():
            current_text = self.rows_label.cget("text")
            self.rows_label.config(bg=theme["panel_bg"], fg=theme["text_color"])

        if hasattr(self, "cols_label") and self.cols_label.winfo_exists():
            current_text = self.cols_label.cget("text")
            self.cols_label.config(bg=theme["panel_bg"], fg=theme["text_color"])

        if hasattr(self, "memory_label") and self.memory_label.winfo_exists():
            current_text = self.memory_label.cget("text")
            self.memory_label.config(bg=theme["panel_bg"], fg=theme["text_color"])

    def finalize_theme_transition(self):
        """Theme switching 마무리"""
        # All 위젯 Update
        self.apply_theme_to_widgets()

        # 토글 버튼 Update (부드러운 효과)
        self.animate_toggle_button()

    def animate_toggle_button(self):
        """토글 버튼 애니메이션"""
        theme = self.current_theme

        # Button color 전환
        self.theme_toggle_btn.configure(
            text="🌙 Dark" if not self.is_dark_mode else "☀️ Light",
            bg=theme["accent"],
            fg=theme["button_fg"],
            activebackground=theme["hover"],
        )

        # 버튼 Size 애니메이션 (약간의 펄스 효과)
        original_font = self.theme_toggle_btn.cget("font")
        self.theme_toggle_btn.configure(font=("Arial", 9, "bold"))
        self.root.after(100, lambda: self.theme_toggle_btn.configure(font=("Arial", 8)))

    def update_frame_theme(self, frame, theme):
        """프레임과 자식 위젯들 테마 Update"""
        try:
            frame.configure(bg=theme["panel_bg"])

            for child in frame.winfo_children():
                widget_class = child.winfo_class()

                if widget_class == "Frame":
                    self.update_frame_theme(child, theme)
                elif widget_class == "Label":
                    # 라벨 Background color이 패널 색상if Update
                    current_bg = str(child.cget("bg"))
                    if current_bg in [
                        "white",
                        "#FFFFFF",
                        "#2D2D30",
                        "#FAFAFA",
                        "#383838",
                        "#2B2B2B",
                    ]:
                        child.configure(bg=theme["panel_bg"], fg=theme["text_color"])
                elif widget_class == "LabelFrame":
                    child.configure(bg=theme["panel_bg"], fg=theme["text_color"])
                elif widget_class == "Entry":
                    child.configure(
                        bg=theme["entry_bg"],
                        fg=theme["text_color"],
                        insertbackground=theme["text_color"],
                        selectbackground=theme["accent"],
                    )
                elif widget_class == "Checkbutton":
                    child.configure(
                        bg=theme["panel_bg"],
                        fg=theme["text_color"],
                        selectcolor=theme["entry_bg"],
                        activebackground=theme["hover"],
                    )

        except tk.TclError:
            pass

    def bind_hover_effects(self, button):
        """버튼 호버 효과 바인딩"""
        original_bg = button.cget("bg")
        hover_color = self.current_theme["hover"]

        def on_enter(e):
            button.configure(bg=hover_color)

        def on_leave(e):
            button.configure(bg=original_bg)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def create_styled_button(self, parent, text, command, bg_color, fg_color="white"):
        """스타일이 적용된 버튼 Create"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Arial", 10),
            bg=bg_color,
            fg=fg_color,
            relief="flat",
            bd=0,
            command=command,
            cursor="hand2",
        )

        # 호버 효과
        def on_enter(e):
            # 색상을 약간 어둡게
            r, g, b = btn.winfo_rgb(bg_color)
            r, g, b = int(r / 256 * 0.8), int(g / 256 * 0.8), int(b / 256 * 0.8)
            hover_color = f"#{r:02x}{g:02x}{b:02x}"
            btn.configure(bg=hover_color)

        def on_leave(e):
            btn.configure(bg=bg_color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def apply_theme_to_widgets(self):
        """모든 위젯에 테마 적용"""
        theme = self.current_theme

        # 루트 윈도우
        self.root.configure(bg=theme["bg"])

        # 재귀적으로 모든 위젯 Update
        self.update_widget_theme(self.root, theme)

    def update_widget_theme(self, widget, theme):
        """위젯과 자식 위젯들에 테마 적용"""
        try:
            widget_class = widget.winfo_class()

            if widget_class in ["Frame", "Toplevel"]:
                widget.configure(bg=theme["panel_bg"])
            elif widget_class == "Label":
                # 라벨의 현재 색상 Confirmation
                current_bg = str(widget.cget("bg"))
                current_fg = str(widget.cget("fg"))

                # 더 포괄적인 조건으로 라벨 Update
                should_update_bg = current_bg in [
                    "white",
                    "#FFFFFF",
                    "#F0F0F0",
                    "#FAFAFA",
                    "#383838",
                    "#2B2B2B",
                    "#2D2D30",
                    "SystemButtonFace",
                ]
                should_update_fg = current_fg in [
                    "black",
                    "#000000",
                    "white",
                    "#FFFFFF",
                    "#E8E8E8",
                    "#CCCCCC",
                    "SystemWindowText",
                    "SystemButtonText",
                ]

                if should_update_bg or should_update_fg:
                    widget.configure(bg=theme["panel_bg"], fg=theme["text_color"])
            elif widget_class == "Button":
                # 테마 토글 버튼과 일반 버튼 구분
                current_text = str(widget.cget("text"))

                # 테마 토글 버튼은 Exclude
                if current_text not in ["🌙", "☀️"]:
                    current_bg = str(widget.cget("bg"))
                    current_fg = str(widget.cget("fg"))

                    # 일반적인 버튼 Background color을 가진 경우
                    if current_bg in [
                        "#F0F0F0",
                        "#FAFAFA",
                        "#E1E1E1",
                        "#D4D4D4",
                        "#2B2B2B",
                        "#383838",
                        "SystemButtonFace",
                    ]:
                        widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
                    # 텍스트가 Default 색상인 경우 텍스트만 Change
                    elif current_fg in [
                        "black",
                        "#000000",
                        "white",
                        "#FFFFFF",
                        "SystemButtonText",
                    ]:
                        widget.configure(fg=theme["button_fg"])
            elif widget_class == "Text":
                widget.configure(
                    bg=theme["tree_bg"],
                    fg=theme["text_color"],
                    insertbackground=theme["text_color"],
                )
            elif widget_class == "Entry":
                # Entry 위젯은 항상 테마 색상으로 Update
                widget.configure(
                    bg=theme["entry_bg"],
                    fg=theme["text_color"],
                    insertbackground=theme["text_color"],
                    relief="flat",
                    bd=1,
                )
            elif widget_class == "Checkbutton":
                widget.configure(
                    bg=theme["panel_bg"],
                    fg=theme["text_color"],
                    selectcolor=theme["entry_bg"],
                )
            elif widget_class == "LabelFrame":
                widget.configure(
                    bg=theme["panel_bg"],
                    fg=theme["text_color"],
                    relief="flat",
                    bd=1,
                    highlightthickness=0,
                )

            # 자식 위젯들에 재귀 적용
            for child in widget.winfo_children():
                self.update_widget_theme(child, theme)

        except tk.TclError:
            # Some 위젯은 특정 속성을 Support하지 않을 수 Exists
            pass

        # 특정 라벨들을 강제로 Update (테마 Change 시)
        if widget == self.root:  # 루트 위젯 Processing 시에만 Execution
            self.force_update_stat_labels(theme)

    def update_stats_container_style(self):
        """Statistics 컨테이너 스타일 Update"""
        if hasattr(self, "stats_container") and self.stats_container.winfo_exists():
            if self.is_dark_mode:
                # 다크Mode에서는 테두리 없이 배경 색상만으로 구분
                self.stats_container.configure(
                    bg=self.current_theme["panel_bg"], relief="flat", bd=0
                )
            else:
                # 라이트Mode에서는 얇은 테두리로 구분
                self.stats_container.configure(
                    bg=self.current_theme["panel_bg"], relief="solid", bd=1
                )

    def force_update_stat_labels(self, theme):
        """Statistics 라벨들을 강제로 Update"""
        try:
            if hasattr(self, "rows_label") and self.rows_label.winfo_exists():
                self.rows_label.configure(bg=theme["panel_bg"], fg=theme["text_color"])
            if hasattr(self, "cols_label") and self.cols_label.winfo_exists():
                self.cols_label.configure(bg=theme["panel_bg"], fg=theme["text_color"])
            if hasattr(self, "memory_label") and self.memory_label.winfo_exists():
                self.memory_label.configure(
                    bg=theme["panel_bg"], fg=theme["text_color"]
                )
        except tk.TclError:
            pass

    def setup_ui(self):
        """UI Configuration - 원래 dearpygui 디자인 Restore"""
        self.root.title("CSV Analyzer (Compatible)")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.current_theme["bg"])

        # 상단 메뉴바
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 테마 메뉴
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)

        # 메인 컨테이너 (수평 레이아웃)
        main_container = tk.Frame(self.root, bg=self.current_theme["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 왼쪽 패널 (300px 고정)
        self.build_left_panel(main_container)

        # 오른쪽 패널
        self.build_right_panel(main_container)

    def build_left_panel(self, parent):
        """왼쪽 패널 구성"""
        left_frame = tk.Frame(
            parent, bg=self.current_theme["panel_bg"], relief="solid", bd=1, width=300
        )
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)  # Size 고정

        # 제목과 테마 토글 버튼
        header_frame = tk.Frame(left_frame, bg=self.current_theme["panel_bg"])
        header_frame.pack(fill="x", pady=(15, 5))

        title_label = tk.Label(
            header_frame,
            text="CSV ANALYZER",
            font=("Arial", 14, "bold"),
            fg=self.current_theme["accent"],
            bg=self.current_theme["panel_bg"],
        )
        title_label.pack(side="left")

        # 다크Mode 토글 버튼 (호버 효과 Add)
        self.theme_toggle_btn = tk.Button(
            header_frame,
            text="🌙 Dark",
            font=("Arial", 8),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief="flat",
            bd=0,
            command=self.toggle_dark_mode,
            activebackground=self.current_theme["hover"],
            cursor="hand2",
        )
        self.theme_toggle_btn.pack(side="right", padx=(5, 0))

        # 호버 효과 바인딩
        self.bind_hover_effects(self.theme_toggle_btn)

        # 구분선
        sep1 = ttk.Separator(left_frame, orient="horizontal")
        sep1.pack(fill="x", padx=10, pady=5)

        # Load CSV 버튼 (호버 효과 Add)
        self.load_btn = tk.Button(
            left_frame,
            text="Load CSV File",
            font=("Arial", 11, "bold"),
            bg="#3498DB",
            fg=self.current_theme["button_fg"],
            relief="flat",
            bd=0,
            height=2,
            command=self.load_csv_file,
            cursor="hand2",
        )
        self.load_btn.pack(fill="x", padx=15, pady=(10, 5))

        # Load 버튼 호버 효과
        def load_btn_hover_enter(e):
            self.load_btn.configure(bg="#2980B9")

        def load_btn_hover_leave(e):
            self.load_btn.configure(bg="#3498DB")

        self.load_btn.bind("<Enter>", load_btn_hover_enter)
        self.load_btn.bind("<Leave>", load_btn_hover_leave)

        # 드래그 앤 드롭 안내
        drag_label = tk.Label(
            left_frame,
            text="or drag and drop CSV file anywhere",
            font=("Arial", 9),
            fg=self.current_theme["secondary_text"],
            bg=self.current_theme["panel_bg"],
        )
        drag_label.pack(pady=(5, 15))

        # Statistics 섹션
        # Statistics 섹션 (일반 Frame으로 Change)
        stats_section = tk.Frame(left_frame, bg=self.current_theme["panel_bg"])
        stats_section.pack(fill="x", padx=15, pady=10)

        # Statistics 제목
        stats_title = tk.Label(
            stats_section,
            text="Statistics",
            font=("Arial", 10, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        stats_title.pack(anchor="w", pady=(0, 5))

        # Statistics Table
        self.stats_container = tk.Frame(
            stats_section, bg=self.current_theme["panel_bg"]
        )
        self.update_stats_container_style()
        self.stats_container.pack(fill="x", padx=5, pady=5)

        # Rows
        row1 = tk.Frame(self.stats_container, bg=self.current_theme["panel_bg"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Rows:",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="w",
        ).pack(side="left")
        self.rows_label = tk.Label(
            row1,
            text="0",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="e",
        )
        self.rows_label.pack(side="right")

        # Columns
        row2 = tk.Frame(self.stats_container, bg=self.current_theme["panel_bg"])
        row2.pack(fill="x", pady=2)
        tk.Label(
            row2,
            text="Columns:",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="w",
        ).pack(side="left")
        self.cols_label = tk.Label(
            row2,
            text="0",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="e",
        )
        self.cols_label.pack(side="right")

        # Memory
        row3 = tk.Frame(self.stats_container, bg=self.current_theme["panel_bg"])
        row3.pack(fill="x", pady=2)
        tk.Label(
            row3,
            text="Memory:",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="w",
        ).pack(side="left")
        self.memory_label = tk.Label(
            row3,
            text="0 MB",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
            anchor="e",
        )
        self.memory_label.pack(side="right")

        # 구분선
        sep2 = ttk.Separator(left_frame, orient="horizontal")
        sep2.pack(fill="x", padx=10, pady=15)

        # State 표시
        status_container = tk.Frame(left_frame, bg=self.current_theme["panel_bg"])
        status_container.pack(fill="x", padx=15, pady=(0, 15))

        # 로딩 스피너 (간단한 점 애니메이션)
        self.spinner_label = tk.Label(
            status_container,
            text="",
            font=("Arial", 12),
            fg=self.current_theme["accent"],
            bg=self.current_theme["panel_bg"],
        )
        self.spinner_label.pack(side="left")

        # State 텍스트
        self.status_label = tk.Label(
            status_container,
            text="Ready",
            font=("Arial", 9),
            fg=self.current_theme["secondary_text"],
            bg=self.current_theme["panel_bg"],
        )
        self.status_label.pack(side="left", padx=(5, 0))

    def build_right_panel(self, parent):
        """오른쪽 패널 구성"""
        right_frame = tk.Frame(
            parent, bg=self.current_theme["panel_bg"], relief="solid", bd=1
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 탭 노트북
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Data Preview 탭
        self.build_preview_tab()

        # Analysis 탭
        self.build_analysis_tab()

        # CSV Slicer 탭
        self.build_slicer_tab()

        # Combinations Analysis 탭
        self.build_combinations_tab()

    def build_slicer_tab(self):
        """CSV 슬라이싱 탭 - Large Data Support"""
        slicer_frame = ttk.Frame(self.notebook)
        self.notebook.add(slicer_frame, text="CSV Slicer")

        # 컨트롤 영역
        control_frame = tk.Frame(slicer_frame, bg=self.current_theme["panel_bg"])
        control_frame.pack(fill="x", padx=10, pady=10)

        # Row 범위 Optional
        range_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        range_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            range_frame,
            text="Row Range:",
            font=("Arial", 10, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left")

        # Start Row
        tk.Label(
            range_frame,
            text="Start:",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left", padx=(10, 5))
        self.start_row_var = tk.StringVar(value="0")
        self.start_row_entry = tk.Entry(
            range_frame,
            textvariable=self.start_row_var,
            width=10,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
        )
        self.start_row_entry.pack(side="left", padx=(0, 10))

        # 끝 Row
        tk.Label(
            range_frame,
            text="End:",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left", padx=(0, 5))
        self.end_row_var = tk.StringVar(value="1000")
        self.end_row_entry = tk.Entry(
            range_frame,
            textvariable=self.end_row_var,
            width=10,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
        )
        self.end_row_entry.pack(side="left", padx=(0, 10))

        # Column Optional
        column_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        column_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            column_frame,
            text="Columns:",
            font=("Arial", 10, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left")

        # Column Optional 체크박스들
        self.column_checkboxes = {}
        self.column_vars = {}

        # Column Optional을 위한 스크롤 Available한 프레임
        column_scroll_frame = tk.Frame(column_frame, bg=self.current_theme["panel_bg"])
        column_scroll_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.column_canvas = tk.Canvas(
            column_scroll_frame, height=60, bg=self.current_theme["panel_bg"]
        )
        scrollbar = ttk.Scrollbar(
            column_scroll_frame, orient="horizontal", command=self.column_canvas.xview
        )
        self.column_canvas.configure(xscrollcommand=scrollbar.set)

        self.column_canvas.pack(side="top", fill="x", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        self.column_inner_frame = tk.Frame(
            self.column_canvas, bg=self.current_theme["panel_bg"]
        )
        self.column_canvas.create_window(
            (0, 0), window=self.column_inner_frame, anchor="nw"
        )

        # Select All / Clear All 버튼들
        button_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        button_frame.pack(fill="x", pady=(0, 10))

        self.select_all_btn = self.create_styled_button(
            button_frame, "Select All", self.select_all_columns, "#27AE60"
        )
        self.select_all_btn.pack(side="left", padx=(0, 5))

        self.clear_all_btn = self.create_styled_button(
            button_frame, "Clear All", self.clear_all_columns, "#E74C3C"
        )
        self.clear_all_btn.pack(side="left", padx=(0, 5))

        # 슬라이스 및 Export 버튼
        self.slice_btn = self.create_styled_button(
            control_frame, "Slice Data", self.slice_data, "#3498DB"
        )
        self.slice_btn.pack(side="left", padx=(0, 5))

        self.export_slice_btn = self.create_styled_button(
            control_frame, "Export Sliced Data", self.export_sliced_data, "#9B59B6"
        )
        self.export_slice_btn.pack(side="left")

        # 슬라이스된 Data 표시 영역
        result_frame = tk.Frame(slicer_frame, bg=self.current_theme["panel_bg"])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Result Information
        info_frame = tk.Frame(result_frame, bg=self.current_theme["panel_bg"])
        info_frame.pack(fill="x", pady=(0, 5))

        self.slice_info_label = tk.Label(
            info_frame,
            text="No data sliced yet",
            font=("Arial", 9),
            fg=self.current_theme["secondary_text"],
            bg=self.current_theme["panel_bg"],
        )
        self.slice_info_label.pack(side="left")

        # 슬라이스된 Data Treeview
        tree_container = tk.Frame(result_frame, bg=self.current_theme["panel_bg"])
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.slicer_tree = ttk.Treeview(tree_container, show="tree headings", height=20)

        # 스크롤바
        v_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.VERTICAL, command=self.slicer_tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.HORIZONTAL, command=self.slicer_tree.xview
        )

        self.slicer_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # 그리드 배치
        self.slicer_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # seconds기 State
        self.current_sliced_data = None
        self.update_column_checkboxes()

    def update_column_checkboxes(self):
        """Column 체크박스 Update"""
        # 기존 체크박스 Remove
        for widget in self.column_inner_frame.winfo_children():
            widget.destroy()

        if self.state.df is None:
            return

        # Column별 체크박스 Create
        for i, col in enumerate(self.state.df.columns):
            var = tk.BooleanVar(value=True)  # Default적으로 모두 Optional
            self.column_vars[col] = var

            cb = tk.Checkbutton(
                self.column_inner_frame,
                text=col,
                variable=var,
                bg=self.current_theme["panel_bg"],
                fg=self.current_theme["text_color"],
                selectcolor=self.current_theme["entry_bg"],
            )
            cb.pack(side="left", padx=5)

        # 캔버스 Size Update
        self.column_inner_frame.update_idletasks()
        self.column_canvas.configure(scrollregion=self.column_canvas.bbox("all"))

    def select_all_columns(self):
        """모든 Column Optional"""
        for var in self.column_vars.values():
            var.set(True)

    def clear_all_columns(self):
        """모든 Column Optional 해제"""
        for var in self.column_vars.values():
            var.set(False)

    def slice_data(self):
        """Data 슬라이싱 Execution"""
        if self.state.df is None:
            self.show_toast("No data loaded", "error")
            return

        try:
            # Row 범위 파싱
            start_row = int(self.start_row_var.get())
            end_row = int(self.end_row_var.get())

            # Valid성 검사
            if start_row < 0:
                start_row = 0
            if end_row > len(self.state.df):
                end_row = len(self.state.df)
            if start_row >= end_row:
                self.show_toast("Invalid row range", "error")
                return

            # Optional된 Column들
            selected_columns = [
                col for col, var in self.column_vars.items() if var.get()
            ]
            if not selected_columns:
                self.show_toast("No columns selected", "error")
                return

            # Data 슬라이싱 (Optimization된 방식)
            self.current_sliced_data = self.state.df.iloc[start_row:end_row][
                selected_columns
            ].copy()

            # Result 표시
            self.display_sliced_data()

            # Information Update
            info_text = f"Sliced {len(self.current_sliced_data):,} rows, {len(selected_columns)} columns"
            self.slice_info_label.config(text=info_text)

            self.show_toast(
                f"Data sliced successfully: {len(self.current_sliced_data)} rows", "ok"
            )

        except ValueError as e:
            self.show_toast(f"Invalid input: {e}", "error")
        except Exception as e:
            self.show_toast(f"Slicing failed: {e}", "error")

    def display_sliced_data(self):
        """슬라이스된 Data 표시 (페이지네이션 Support)"""
        if self.current_sliced_data is None or self.current_sliced_data.empty:
            return

        # Treeview Initialize
        for item in self.slicer_tree.get_children():
            self.slicer_tree.delete(item)

        # Column Header Configuration
        self.slicer_tree["columns"] = list(self.current_sliced_data.columns)
        for col in self.current_sliced_data.columns:
            self.slicer_tree.heading(col, text=col)
            self.slicer_tree.column(col, width=min(120, len(str(col)) * 8))

        # Data 표시 (최대 10000Row까지 표시 제한 해제 - 페이지네이션으로 Processing)
        max_display_rows = min(
            5000, len(self.current_sliced_data)
        )  # Performance을 for 5000Row으로 제한

        for idx, row in self.current_sliced_data.head(max_display_rows).iterrows():
            values = []
            for val in row:
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                elif pd.isna(val):
                    values.append("")
                else:
                    values.append(str(val))
            self.slicer_tree.insert("", "end", values=values)

        # Large Data 안내
        if len(self.current_sliced_data) > max_display_rows:
            self.show_toast(
                f"Showing first {max_display_rows:,} rows of {len(self.current_sliced_data):,} total rows",
                "info",
            )

    def export_sliced_data(self):
        """슬라이스된 Data Export"""
        if self.current_sliced_data is None:
            self.show_toast("No sliced data to export", "error")
            return

        try:
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save sliced data",
            )

            if file_path:
                self.current_sliced_data.to_csv(file_path, index=True)
                self.show_toast(f"Exported to {file_path}", "success")

        except Exception as e:
            self.show_toast(f"Export failed: {e}", "error")

    def build_combinations_tab(self):
        """Combinations analysis 탭"""
        combinations_frame = ttk.Frame(self.notebook)
        self.notebook.add(combinations_frame, text="Combinations Analysis")

        # 메인 컨테이너
        main_container = tk.Frame(combinations_frame, bg=self.current_theme["panel_bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 상단 컨트롤 영역
        control_frame = tk.Frame(main_container, bg=self.current_theme["panel_bg"])
        control_frame.pack(fill="x", pady=(0, 10))

        # 제목
        title_label = tk.Label(
            control_frame,
            text="데이터 관계 분석",
            font=("Arial", 12, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        title_label.pack(side="left")

        # Run analysis 버튼
        self.run_combinations_btn = tk.Button(
            control_frame,
            text="분석 실행",
            command=self.run_combinations_analysis,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            font=("Arial", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
        )
        self.run_combinations_btn.pack(side="right")

        # Configuration 영역
        settings_frame = tk.Frame(main_container, bg=self.current_theme["panel_bg"])
        settings_frame.pack(fill="x", pady=(0, 10))

        # DSL token Input
        dsl_label = tk.Label(
            settings_frame,
            text="DSL 토큰 (선택사항):",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        dsl_label.pack(side="left", padx=(0, 10))

        self.dsl_tokens_entry = tk.Entry(
            settings_frame,
            width=30,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
            insertbackground=self.current_theme["text_color"],
        )
        self.dsl_tokens_entry.pack(side="left", padx=(0, 20))

        # 상위 K개 Result Configuration
        topk_label = tk.Label(
            settings_frame,
            text="상위 결과 수:",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        topk_label.pack(side="left", padx=(0, 5))

        self.topk_var = tk.StringVar(value="10")
        topk_entry = tk.Entry(
            settings_frame,
            textvariable=self.topk_var,
            width=5,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
            insertbackground=self.current_theme["text_color"],
        )
        topk_entry.pack(side="left")

        # Result 표시 영역
        result_frame = tk.Frame(main_container, bg=self.current_theme["panel_bg"])
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Result 텍스트 위젯 (스크롤 Include)
        text_frame = tk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.combinations_result_text = tk.Text(
            text_frame,
            bg=self.current_theme["tree_bg"],
            fg=self.current_theme["text_color"],
            insertbackground=self.current_theme["text_color"],
            font=("Consolas", 9),
            wrap=tk.WORD,
        )

        # 스크롤바
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.combinations_result_text.yview
        )
        self.combinations_result_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.combinations_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # seconds기 안내 Message
        initial_message = """
📊 Combinations analysis Tool

이 Tool는 Data의 Column 간 관계를 Automatic으로 분석합니다:

🔢 수치형 분석: 
   • Correlation analysis
   • 피어슨 상관계수
   
📊 범주형 분석:
   • Cramér's V 계산
   • 카이제곱 검정
   • 연관규칙 분석
   
🔀 혼합형 분석:
   • ANOVA 분석
   • 효과 Size 계산

Usage:
1. Data를 먼저 Load하세요
2. 필요시 DSL token을 Input하세요 (Yes: C1,C2,C3)
3. 'Run analysis' 버튼을 클릭하세요

Analysis results는 아래에 표시됩니다.
        """
        self.combinations_result_text.insert(1.0, initial_message)
        self.combinations_result_text.config(state=tk.DISABLED)

    def run_combinations_analysis(self):
        """조합 Run analysis (Background Thread Use)"""
        if self.state.df is None:
            self.show_toast("데이터를 먼저 로드해주세요", "error")
            return

        # 분석 중 State 표시
        self.run_combinations_btn.config(text="분석 중...", state="disabled")
        self.combinations_result_text.config(state=tk.NORMAL)
        self.combinations_result_text.delete(1.0, tk.END)
        self.combinations_result_text.insert(1.0, "🔄 분석을 실행 중입니다...\n")
        self.combinations_result_text.config(state=tk.DISABLED)
        self.root.update()

        # DSL token 파싱
        dsl_tokens = None
        if self.dsl_tokens_entry.get().strip():
            dsl_tokens = [
                token.strip() for token in self.dsl_tokens_entry.get().split(",")
            ]

        try:
            top_k = int(self.topk_var.get())
        except ValueError:
            top_k = 10

        # Background Thread에서 Execution될 Function
        def run_analysis():
            from src.core.combinations import (
                AdvancedCombinationsAnalyzer,
                AnalysisConfig,
            )

            config = AnalysisConfig(
                top_k=top_k,
                parallel_processing=True,  # Background에서 Parallel Processing Use
                enable_caching=True,
            )

            # Run analysis
            analyzer = AdvancedCombinationsAnalyzer(config)
            results = analyzer.analyze_all_combinations(self.state.df, dsl_tokens)

            # Result 포맷팅
            summary = analyzer.get_analysis_summary(results)
            detailed_results = self.format_detailed_results(results)

            return (summary, detailed_results)

        # Complete 콜백
        def on_complete(result):
            try:
                if result.success:
                    summary, detailed = result.data
                    # 텍스트 위젯에 Result 표시
                    self.combinations_result_text.config(state=tk.NORMAL)
                    self.combinations_result_text.delete(1.0, tk.END)
                    self.combinations_result_text.insert(
                        1.0, summary + "\n\n" + detailed
                    )
                    self.combinations_result_text.config(state=tk.DISABLED)
                    self.show_toast("분석이 완료되었습니다", "ok")
                else:
                    # Error Processing
                    self.combinations_result_text.config(state=tk.NORMAL)
                    self.combinations_result_text.delete(1.0, tk.END)
                    self.combinations_result_text.insert(
                        1.0, f"❌ 분석 중 오류가 발생했습니다:\n\n{result.error}"
                    )
                    self.combinations_result_text.config(state=tk.DISABLED)
                    self.show_toast(f"분석 실패: {result.error}", "error")
            finally:
                # 버튼 State Restore
                self.run_combinations_btn.config(text="분석 실행", state="normal")

        # Background 태스크 Execution
        self.task_manager.run_task(run_analysis, on_complete)

    def format_detailed_results(self, results):
        """상세 Result 포맷팅"""
        detailed = ["=" * 60, "📈 상세 분석 결과", "=" * 60, ""]

        # 수치형 조합 Result
        if (
            "numerical_combinations" in results
            and "error" not in results["numerical_combinations"]
        ):
            num_results = results["numerical_combinations"]
            detailed.extend(["🔢 수치형 컬럼 Correlation analysis:", "-" * 30])

            for idx, corr in enumerate(
                num_results.get("strong_correlations", [])[:5], 1
            ):
                detailed.append(f"{idx}. {corr['column1']} ↔ {corr['column2']}")
                detailed.append(
                    f"   상관계수: {corr['correlation']:.3f} ({corr['strength']})"
                )
                detailed.append(f"   방향: {corr['direction']}")
                detailed.append("")

        # 범주형 조합 Result
        if (
            "categorical_combinations" in results
            and "error" not in results["categorical_combinations"]
        ):
            cat_results = results["categorical_combinations"]
            detailed.extend(["📊 범주형 컬럼 연관성 분석:", "-" * 30])

            for idx, assoc in enumerate(cat_results.get("associations", [])[:5], 1):
                detailed.append(f"{idx}. {assoc['column1']} ↔ {assoc['column2']}")
                detailed.append(
                    f"   Cramér's V: {assoc['cramers_v']:.3f} ({assoc['association_strength']})"
                )
                detailed.append(
                    f"   유의성: {'유의함' if assoc['significant'] else '유의하지 않음'}"
                )
                detailed.append("")

        # 혼합형 조합 Result
        if (
            "mixed_combinations" in results
            and "error" not in results["mixed_combinations"]
        ):
            mixed_results = results["mixed_combinations"]
            detailed.extend(["🔀 혼합형 분석 (수치형 vs 범주형):", "-" * 30])

            for idx, anova in enumerate(mixed_results.get("anova_results", [])[:5], 1):
                detailed.append(
                    f"{idx}. {anova['numerical_column']} vs {anova['categorical_column']}"
                )
                detailed.append(f"   F-통계량: {anova['f_statistic']:.3f}")
                detailed.append(
                    f"   효과 크기: {anova['eta_squared']:.3f} ({anova['effect_size']})"
                )
                detailed.append(
                    f"   유의성: {'유의함' if anova['significant'] else '유의하지 않음'}"
                )
                detailed.append("")

        return "\n".join(detailed)

    def build_preview_tab(self):
        """Data preview 탭"""
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="Data Preview")

        # Preview 라벨과 Row 수 Information
        header_frame = tk.Frame(preview_frame, bg=self.current_theme["panel_bg"])
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        preview_label = tk.Label(
            header_frame,
            text="Preview",
            font=("Arial", 11, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        preview_label.pack(side="left")

        self.row_count_label = tk.Label(
            header_frame,
            text="",
            font=("Arial", 9),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["secondary_text"],
        )
        self.row_count_label.pack(side="right")

        # Table 프레임
        table_frame = tk.Frame(preview_frame, bg=self.current_theme["panel_bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Treeview with scrollbars
        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Treeview Create (show Options과 height 명시적 Configuration)
        self.preview_tree = ttk.Treeview(
            tree_container, show="tree headings", height=25
        )

        # 스크롤바
        v_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.VERTICAL, command=self.preview_tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.HORIZONTAL, command=self.preview_tree.xview
        )

        self.preview_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # 그리드 배치
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

    def build_analysis_tab(self):
        """분석 탭 - Visualization Include"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")

        # 컨트롤 영역
        control_frame = tk.Frame(analysis_frame, bg=self.current_theme["panel_bg"])
        control_frame.pack(fill="x", padx=10, pady=10)

        # Column Optional
        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(
            control_frame,
            textvariable=self.column_var,
            values=["No columns loaded"],
            width=30,
        )
        self.column_combo.pack(side="left", padx=(0, 10))

        # 분석 버튼
        analyze_btn = self.create_styled_button(
            control_frame, "Analyze Column", self.analyze_column, "#3498DB"
        )
        analyze_btn.pack(side="left", padx=(0, 10))

        # Visualization 버튼
        visualize_btn = self.create_styled_button(
            control_frame, "Create Visualization", self.create_visualization, "#E74C3C"
        )
        visualize_btn.pack(side="left")

        # 메인 컨텐츠 영역을 좌우로 분할
        main_paned = ttk.PanedWindow(analysis_frame, orient="horizontal")
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 왼쪽: Analysis results 텍스트
        left_frame = tk.Frame(main_paned, bg=self.current_theme["panel_bg"])
        main_paned.add(left_frame, weight=1)

        # Analysis results 라벨
        result_label = tk.Label(
            left_frame,
            text="Analysis Results",
            font=("Arial", 11, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        result_label.pack(anchor="w", pady=(0, 5))

        # 스크롤 Available한 텍스트 영역
        text_container = tk.Frame(left_frame, bg=self.current_theme["panel_bg"])
        text_container.pack(fill=tk.BOTH, expand=True)

        self.analysis_text = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=self.current_theme["tree_bg"],
            fg=self.current_theme["text_color"],
            height=20,
            insertbackground=self.current_theme["text_color"],
        )
        text_scrollbar = ttk.Scrollbar(text_container, command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=text_scrollbar.set)

        self.analysis_text.pack(side="left", fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side="right", fill="y")

        # 오른쪽: Visualization 영역
        right_frame = tk.Frame(main_paned, bg=self.current_theme["panel_bg"])
        main_paned.add(right_frame, weight=1)

        # Visualization 라벨
        viz_label = tk.Label(
            right_frame,
            text="Visualization",
            font=("Arial", 11, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        viz_label.pack(anchor="w", pady=(0, 5))

        # Visualization 캔버스 영역
        self.viz_frame = tk.Frame(
            right_frame, bg=self.current_theme["panel_bg"], relief="sunken", bd=1
        )
        self.viz_frame.pack(fill=tk.BOTH, expand=True)

        # seconds기 Message
        self.analysis_text.insert(
            "1.0", "Select a column and click 'Analyze Column' to view statistics."
        )
        self.analysis_text.configure(state="disabled")

        # seconds기 Visualization Message
        initial_viz_label = tk.Label(
            self.viz_frame,
            text="Select a column and click 'Create Visualization'\nto generate charts.",
            font=("Arial", 10),
            fg=self.current_theme["secondary_text"],
            bg=self.current_theme["panel_bg"],
        )
        initial_viz_label.pack(expand=True)

    def show_toast(self, message: str, kind: str = "info"):
        """Toast message 표시"""
        if self.toast:
            try:
                self.toast.close()
            except:
                pass
        self.toast = ToastWindow(self.root, message, kind, self.is_dark_mode)

    def begin_busy(self, status_text: str = "Working..."):
        """로딩 State Start"""
        self.status_label.config(text=status_text)
        self.load_btn.config(state="disabled")
        self.animate_spinner()

    def end_busy(self, done_text: str = "Done", ok: bool = True):
        """로딩 State Exit"""
        self.status_label.config(text=done_text)
        self.load_btn.config(state="normal")
        self.stop_spinner()
        self.show_toast(done_text, "ok" if ok else "error")

    def animate_spinner(self):
        """스피너 애니메이션"""
        current = self.spinner_label.cget("text")
        if len(current) >= 3:
            self.spinner_label.config(text=".")
        else:
            self.spinner_label.config(text=current + ".")

        self.busy_after_id = self.root.after(500, self.animate_spinner)

    def stop_spinner(self):
        """스피너 Stop"""
        if self.busy_after_id:
            self.root.after_cancel(self.busy_after_id)
            self.busy_after_id = None
        self.spinner_label.config(text="")

    def load_csv_file(self):
        """CSV File Load 다이얼로그"""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path: str):
        """CSV File Load (청킹 및 슬라이싱 적용)"""
        if not file_path.lower().endswith(".csv"):
            self.show_toast("Error: Not a CSV file", "error")
            return

        self.begin_busy("Loading...")

        def load_thread():
            try:
                # 큰 File Processing를 위한 청킹
                chunk_size = 50000  # 50K로 Increase
                chunks = []
                total_rows = 0

                # File Size 체크
                file_size = Path(file_path).stat().st_size
                if file_size > 100 * 1024 * 1024:  # 100MB or more (기준 상향)
                    # 샘플링 Load (처음 50000Row으로 Increase)
                    self.state.df = pd.read_csv(file_path, nrows=50000)
                    self.root.after(
                        0, lambda: self.on_csv_loaded(file_path, is_sample=True)
                    )
                else:
                    # All Load
                    self.state.df = pd.read_csv(file_path)
                    self.root.after(
                        0, lambda: self.on_csv_loaded(file_path, is_sample=False)
                    )

                self.state.numeric_cols = self.state.df.select_dtypes(
                    include="number"
                ).columns.tolist()

            except Exception as e:
                self.root.after(0, lambda: self.on_csv_error(str(e)))

        threading.Thread(target=load_thread, daemon=True).start()

    def on_csv_loaded(self, file_path: str, is_sample: bool = False):
        """CSV Load Complete"""
        # Statistics Update (테마 색상도 함께 적용)
        self.rows_label.config(
            text=f"{len(self.state.df):,}" + (" (sample)" if is_sample else ""),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        self.cols_label.config(
            text=f"{len(self.state.df.columns):,}",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        self.memory_label.config(
            text=format_bytes(self.state.df.memory_usage(deep=True).sum()),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )

        # Column 콤보박스 Update
        self.column_combo["values"] = list(self.state.df.columns)
        if len(self.state.df.columns) > 0:  # Modify: .empty instead len() Use
            self.column_combo.current(0)

        # 슬라이서 탭의 Column 체크박스 Update
        self.update_column_checkboxes()

        # Preview Table Update (슬라이싱 적용)
        self.update_preview_table()

        file_name = Path(file_path).name
        status_msg = f"Loaded: {file_name}" + (" (first 10K rows)" if is_sample else "")
        self.end_busy(status_msg, True)

    def on_csv_error(self, error_msg: str):
        """CSV Load Error"""
        self.end_busy(f"Failed to load: {error_msg}", False)

    def update_preview_table(self):
        """Preview Table Update (슬라이싱 적용)"""
        # 기존 Data Remove
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        if self.state.df is None or self.state.df.empty:
            self.row_count_label.config(text="No data loaded")
            return

        # Column Configuration
        columns = list(self.state.df.columns)

        # Treeview Column Configuration
        self.preview_tree["columns"] = columns
        self.preview_tree["show"] = "tree headings"  # Header 표시 확실히 Configuration

        # 인덱스 Column Configuration
        self.preview_tree.heading("#0", text="Index", anchor="w")
        self.preview_tree.column("#0", width=60, anchor="w", minwidth=60)

        # Data Column들 Configuration
        for col in columns:
            self.preview_tree.heading(col, text=col, anchor="w")
            self.preview_tree.column(col, width=120, anchor="w", minwidth=80)

        # Data Add (1000Row으로 제한 - 슬라이싱 Increase)
        preview_data = self.state.df.head(1000)

        for idx, row in preview_data.iterrows():
            # 텍스트 길이 제한 (50자)
            values = []
            for val in row:
                str_val = str(val)
                if len(str_val) > 50:
                    values.append(str_val[:47] + "...")
                else:
                    values.append(str_val)

            self.preview_tree.insert("", "end", text=str(idx), values=values)

        total_loaded = len(self.state.df)
        preview_shown = len(preview_data)

        # Row 수 Information Update
        self.row_count_label.config(
            text=f"Showing {preview_shown:,} of {total_loaded:,} rows"
        )

        # Treeview Update 강제
        self.preview_tree.update_idletasks()

    def analyze_column(self):
        """Column 분석"""
        if self.state.df is None:
            self.show_toast("No data loaded", "warn")
            return

        column = self.column_var.get()
        if not column or column == "No columns loaded":
            self.show_toast("Select a column", "warn")
            return

        try:
            info = column_profile(self.state.df, column)

            # Analysis results 표시
            self.analysis_text.configure(state="normal")
            self.analysis_text.delete("1.0", "end")

            # 제목
            self.analysis_text.insert("end", f"Analysis for: {column}\n", "title")
            self.analysis_text.insert("end", "=" * 50 + "\n\n")

            # Statistics Table
            for key, value in info.items():
                self.analysis_text.insert("end", f"{key:<15}: {value}\n")

            # 샘플 Data (슬라이싱 적용)
            self.analysis_text.insert("end", f"\nSample values (first 50):\n")
            self.analysis_text.insert("end", "-" * 30 + "\n")
            sample_values = self.state.df[column].dropna().head(50)
            for i, val in enumerate(sample_values, 1):
                val_str = str(val)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                self.analysis_text.insert("end", f"{i:2d}. {val_str}\n")

            self.analysis_text.configure(state="disabled")

        except Exception as e:
            self.show_toast(f"Failed to analyze: {e}", "error")

    def create_visualization(self):
        """Optional된 Column의 Visualization Create"""
        if self.state.df is None or self.state.df.empty:
            self.show_toast("No data loaded", "error")
            return

        column = self.column_var.get()
        if not column or column == "No columns loaded":
            self.show_toast("Please select a column first", "error")
            return

        try:
            # 기존 Visualization Remove
            for widget in self.viz_frame.winfo_children():
                widget.destroy()

            # matplotlib 한글 폰트 Configuration
            plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False

            # 다크Mode에 according to 색상 Configuration
            current_theme = (
                self.themes["dark"] if self.is_dark_mode else self.themes["light"]
            )

            # Figure Create 및 테마 적용
            fig, axes = plt.subplots(2, 2, figsize=(8, 6))

            if self.is_dark_mode:
                fig.patch.set_facecolor("#2B2B2B")
                text_color = "#CCCCCC"
                grid_color = "#404040"
                chart_colors = ["#5DADE2", "#F1948A", "#82E0AA", "#F7DC6F"]
            else:
                fig.patch.set_facecolor("white")
                text_color = "#333333"
                grid_color = "#E0E0E0"
                chart_colors = ["skyblue", "lightcoral", "lightgreen", "orange"]

            fig.suptitle(
                f"Visualization: {column}",
                fontsize=12,
                fontweight="bold",
                color=text_color,
            )

            data = self.state.df[column].dropna()

            if pd.api.types.is_numeric_dtype(data):
                # 수치형 Data Visualization

                # 각 서브플롯에 테마 적용
                for ax in axes.flat:
                    if self.is_dark_mode:
                        ax.set_facecolor("#2B2B2B")
                        ax.tick_params(colors=text_color, labelsize=8)
                        ax.spines["bottom"].set_color(text_color)
                        ax.spines["top"].set_color(text_color)
                        ax.spines["right"].set_color(text_color)
                        ax.spines["left"].set_color(text_color)
                        ax.grid(True, color=grid_color, alpha=0.3)
                    else:
                        ax.tick_params(labelsize=8)
                        ax.grid(True, alpha=0.3)

                # 1. 히스토그램
                axes[0, 0].hist(
                    data,
                    bins=20,
                    alpha=0.7,
                    color=chart_colors[0],
                    edgecolor=text_color,
                )
                axes[0, 0].set_title("Histogram", fontsize=10, color=text_color)

                # 2. 박스플롯
                bp = axes[0, 1].boxplot(data, patch_artist=True)
                bp["boxes"][0].set_facecolor(chart_colors[0])
                bp["boxes"][0].set_alpha(0.7)
                axes[0, 1].set_title("Box Plot", fontsize=10, color=text_color)

                # 3. 라인 플롯 (인덱스별)
                sample_data = data.head(100)
                axes[1, 0].plot(
                    sample_data.index,
                    sample_data.values,
                    marker="o",
                    markersize=2,
                    alpha=0.7,
                    color=chart_colors[0],
                )
                axes[1, 0].set_title(
                    "Line Plot (First 100)", fontsize=10, color=text_color
                )

                # 4. 기술Statistics
                stats_text = f"Mean: {data.mean():.2f}\nMedian: {data.median():.2f}\nStd: {data.std():.2f}\nMin: {data.min():.2f}\nMax: {data.max():.2f}"
                axes[1, 1].text(
                    0.1,
                    0.5,
                    stats_text,
                    transform=axes[1, 1].transAxes,
                    fontsize=9,
                    verticalalignment="center",
                    color=text_color,
                )
                axes[1, 1].set_title("Statistics", fontsize=10, color=text_color)
                axes[1, 1].axis("off")
                if self.is_dark_mode:
                    axes[1, 1].set_facecolor("#2B2B2B")

            else:
                # 범주형 Data Visualization
                value_counts = data.value_counts().head(10)

                # 각 서브플롯에 테마 적용
                for ax in axes.flat:
                    if self.is_dark_mode:
                        ax.set_facecolor("#2B2B2B")
                        ax.tick_params(colors=text_color, labelsize=8)
                        ax.spines["bottom"].set_color(text_color)
                        ax.spines["top"].set_color(text_color)
                        ax.spines["right"].set_color(text_color)
                        ax.spines["left"].set_color(text_color)
                        ax.grid(True, color=grid_color, alpha=0.3)
                    else:
                        ax.tick_params(labelsize=8)
                        ax.grid(True, alpha=0.3)

                # 1. 막대 그래프
                axes[0, 0].bar(
                    range(len(value_counts)), value_counts.values, color=chart_colors[1]
                )
                axes[0, 0].set_title("Value Counts", fontsize=10, color=text_color)

                # 2. 파이 차트
                if len(value_counts) > 0:
                    wedges, texts, autotexts = axes[0, 1].pie(
                        value_counts.values,
                        labels=value_counts.index,
                        autopct="%1.1f%%",
                        startangle=90,
                        colors=chart_colors,
                    )
                    # 파이 차트 텍스트 색상 조정
                    for text in texts:
                        text.set_color(text_color)
                    for autotext in autotexts:
                        autotext.set_color(
                            "#FFFFFF" if self.is_dark_mode else "#000000"
                        )
                    axes[0, 1].set_title("Distribution", fontsize=10, color=text_color)

                # 3. 수평 막대
                axes[1, 0].barh(
                    range(len(value_counts)), value_counts.values, color=chart_colors[2]
                )
                axes[1, 0].set_title("Horizontal Bar", fontsize=10, color=text_color)

                # 4. Statistics
                stats_text = f"Unique: {data.nunique()}\nMost frequent: {data.mode().iloc[0] if len(data.mode()) > 0 else 'N/A'}\nTotal: {len(data)}"
                axes[1, 1].text(
                    0.1,
                    0.5,
                    stats_text,
                    transform=axes[1, 1].transAxes,
                    fontsize=9,
                    verticalalignment="center",
                    color=text_color,
                )
                axes[1, 1].set_title("Info", fontsize=10, color=text_color)
                axes[1, 1].axis("off")
                if self.is_dark_mode:
                    axes[1, 1].set_facecolor("#2B2B2B")

            plt.tight_layout()

            # tkinter에 matplotlib 캔버스 Add
            canvas = FigureCanvasTkAgg(fig, self.viz_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            self.show_toast(f"Failed to create visualization: {e}", "error")

    def build_slicer_tab(self):
        """CSV 슬라이싱 탭"""
        slicer_frame = ttk.Frame(self.notebook)
        self.notebook.add(slicer_frame, text="CSV Slicer")

        # 컨트롤 영역
        control_frame = tk.Frame(slicer_frame, bg=self.current_theme["panel_bg"])
        control_frame.pack(fill="x", padx=10, pady=10)

        # 제목
        title_label = tk.Label(
            control_frame,
            text="CSV Data Slicer",
            font=("Arial", 12, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        )
        title_label.pack(anchor="w", pady=(0, 10))

        # Row 범위 Configuration
        row_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        row_frame.pack(fill="x", pady=5)

        tk.Label(
            row_frame,
            text="Row Range:",
            font=("Arial", 10, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left")
        tk.Label(
            row_frame,
            text="From:",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left", padx=(10, 5))
        self.row_start_var = tk.StringVar(value="1")
        start_entry = tk.Entry(
            row_frame,
            textvariable=self.row_start_var,
            width=10,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
            insertbackground=self.current_theme["text_color"],
        )
        start_entry.pack(side="left", padx=(0, 10))

        tk.Label(
            row_frame,
            text="To:",
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left", padx=(0, 5))
        self.row_end_var = tk.StringVar(value="1000")
        end_entry = tk.Entry(
            row_frame,
            textvariable=self.row_end_var,
            width=10,
            bg=self.current_theme["entry_bg"],
            fg=self.current_theme["text_color"],
            insertbackground=self.current_theme["text_color"],
        )
        end_entry.pack(side="left")

        # Column Optional
        col_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        col_frame.pack(fill="x", pady=5)

        tk.Label(
            col_frame,
            text="Columns:",
            font=("Arial", 10, "bold"),
            bg=self.current_theme["panel_bg"],
            fg=self.current_theme["text_color"],
        ).pack(side="left")

        # Column Optional 프레임
        self.column_selection_frame = tk.Frame(
            col_frame, bg=self.current_theme["panel_bg"]
        )
        self.column_selection_frame.pack(side="left", padx=(10, 0))

        # 버튼 영역
        button_frame = tk.Frame(control_frame, bg=self.current_theme["panel_bg"])
        button_frame.pack(fill="x", pady=10)

        slice_btn = self.create_styled_button(
            button_frame, "Apply Slice", self.apply_slice, "#27AE60"
        )
        slice_btn.pack(side="left", padx=(0, 10))

        export_btn = self.create_styled_button(
            button_frame, "Export Sliced Data", self.export_sliced_data, "#F39C12"
        )
        export_btn.pack(side="left")

        # 슬라이싱 Result 영역
        result_frame = tk.Frame(slicer_frame, bg=self.current_theme["panel_bg"])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Result Table
        self.slice_tree_container = tk.Frame(
            result_frame, bg=self.current_theme["panel_bg"]
        )
        self.slice_tree_container.pack(fill=tk.BOTH, expand=True)

        # 슬라이싱된 Data용 Treeview
        self.slice_tree = ttk.Treeview(
            self.slice_tree_container, show="tree headings", height=15
        )

        # 스크롤바
        slice_v_scrollbar = ttk.Scrollbar(
            self.slice_tree_container, orient=tk.VERTICAL, command=self.slice_tree.yview
        )
        slice_h_scrollbar = ttk.Scrollbar(
            self.slice_tree_container,
            orient=tk.HORIZONTAL,
            command=self.slice_tree.xview,
        )

        self.slice_tree.configure(
            yscrollcommand=slice_v_scrollbar.set, xscrollcommand=slice_h_scrollbar.set
        )

        # 그리드 배치
        self.slice_tree.grid(row=0, column=0, sticky="nsew")
        slice_v_scrollbar.grid(row=0, column=1, sticky="ns")
        slice_h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.slice_tree_container.grid_rowconfigure(0, weight=1)
        self.slice_tree_container.grid_columnconfigure(0, weight=1)

    def update_column_checkboxes(self):
        """Column 체크박스 Update"""
        for widget in self.column_selection_frame.winfo_children():
            widget.destroy()

        if self.state.df is not None:
            self.column_vars = {}
            columns = list(self.state.df.columns)

            # All Optional/해제 버튼
            select_frame = tk.Frame(
                self.column_selection_frame, bg=self.current_theme["panel_bg"]
            )
            select_frame.pack(fill="x", pady=(0, 5))

            tk.Button(
                select_frame,
                text="All",
                font=("Arial", 8),
                command=self.select_all_columns,
            ).pack(side="left", padx=(0, 5))
            tk.Button(
                select_frame,
                text="None",
                font=("Arial", 8),
                command=self.deselect_all_columns,
            ).pack(side="left")

            # Column별 체크박스 (최대 10개만 표시)
            for col in columns[:10]:
                var = tk.BooleanVar(value=True)
                self.column_vars[col] = var
                cb = tk.Checkbutton(
                    self.column_selection_frame,
                    text=col[:15],
                    variable=var,
                    bg=self.current_theme["panel_bg"],
                    fg=self.current_theme["text_color"],
                    font=("Arial", 8),
                    selectcolor=self.current_theme["entry_bg"],
                )
                cb.pack(anchor="w")

    def select_all_columns(self):
        if hasattr(self, "column_vars"):
            for var in self.column_vars.values():
                var.set(True)

    def deselect_all_columns(self):
        if hasattr(self, "column_vars"):
            for var in self.column_vars.values():
                var.set(False)

    def apply_slice(self):
        """슬라이싱 적용"""
        if self.state.df is None:
            self.show_toast("No data loaded", "error")
            return

        try:
            start_row = int(self.row_start_var.get()) - 1
            end_row = int(self.row_end_var.get())

            if start_row < 0:
                start_row = 0
            if end_row > len(self.state.df):
                end_row = len(self.state.df)

            selected_columns = []
            if hasattr(self, "column_vars"):
                for col, var in self.column_vars.items():
                    if var.get():
                        selected_columns.append(col)

            if not selected_columns:
                selected_columns = list(self.state.df.columns)

            sliced_data = self.state.df.iloc[start_row:end_row][selected_columns]
            self.current_sliced_data = sliced_data
            self.update_slice_table(sliced_data)

            self.show_toast(
                f"Sliced: {len(sliced_data)} rows, {len(selected_columns)} cols",
                "success",
            )

        except Exception as e:
            self.show_toast(f"Failed to slice: {e}", "error")

    def update_slice_table(self, data):
        """슬라이싱 Result Table Update"""
        for item in self.slice_tree.get_children():
            self.slice_tree.delete(item)

        if data is None or data.empty:
            return

        columns = list(data.columns)
        self.slice_tree["columns"] = columns
        self.slice_tree["show"] = "tree headings"

        self.slice_tree.heading("#0", text="Index", anchor="w")
        self.slice_tree.column("#0", width=60, anchor="w")

        for col in columns:
            self.slice_tree.heading(col, text=col, anchor="w")
            self.slice_tree.column(col, width=100, anchor="w")

        display_data = data.head(500)
        for idx, row in display_data.iterrows():
            values = [
                str(val)[:30] + ("..." if len(str(val)) > 30 else "") for val in row
            ]
            self.slice_tree.insert("", "end", text=str(idx), values=values)

    def export_sliced_data(self):
        """슬라이싱된 Data Export"""
        if not hasattr(self, "current_sliced_data"):
            self.show_toast("No sliced data to export", "error")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save sliced data",
            )

            if file_path:
                self.current_sliced_data.to_csv(file_path, index=True)
                self.show_toast(f"Exported to {file_path}", "success")

        except Exception as e:
            self.show_toast(f"Export failed: {e}", "error")

    def display_data_paginated(
        self, df: pd.DataFrame, page: int = 0, page_size: int = 1000
    ):
        """페이지네이션으로 Large Data Efficient 표시"""
        if df is None or df.empty:
            return

        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(df))

        # 현재 페이지 Data만 표시
        page_data = df.iloc[start_idx:end_idx]

        # Cache 키 Create
        cache_key = f"page_{page}_{page_size}_{hash(str(df.columns.tolist()))}"
        cached_data = self.data_cache.get(cache_key)

        if cached_data is not None:
            # Cache된 Data Use
            display_data = cached_data
        else:
            # 새로 Processing 및 Cache에 Save
            display_data = page_data.copy()
            self.data_cache.set(cache_key, display_data)

        # Treeview Update (기존 Data 클리어 후 Add)
        if hasattr(self, "preview_tree"):
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)

            # Column Header Configuration (최seconds 1회만)
            if not self.preview_tree.get_children():
                self.preview_tree["columns"] = list(display_data.columns)
                for col in display_data.columns:
                    self.preview_tree.heading(col, text=col)
                    self.preview_tree.column(col, width=min(150, len(str(col)) * 10))

            # Data Row Add (Optimization된 방식)
            for idx, row in display_data.iterrows():
                values = []
                for val in row:
                    if isinstance(val, float):
                        values.append(f"{val:.2f}")
                    elif pd.isna(val):
                        values.append("")
                    else:
                        values.append(str(val))
                self.preview_tree.insert("", "end", values=values)

            # 페이지 Information Update
            if hasattr(self, "row_count_label"):
                total_rows = len(df)
                self.row_count_label.config(
                    text=f"Rows: {start_idx + 1}-{end_idx} of {total_rows:,}"
                )

    def animate_spinner_optimized(self):
        """Optimization된 스피너 애니메이션"""
        if not hasattr(self, "_spinner_active"):
            self._spinner_active = False

        if not self._spinner_active:
            return

        if hasattr(self, "spinner_label") and self.spinner_label.winfo_exists():
            current = self.spinner_label.cget("text")
            # 더 부드러운 애니메이션 패턴
            patterns = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            current_idx = patterns.index(current) if current in patterns else 0
            next_pattern = patterns[(current_idx + 1) % len(patterns)]
            self.spinner_label.config(text=next_pattern)

        # 100ms 간격으로 Optimization (기존 50ms에서 Increase)
        self.root.after(100, self.animate_spinner_optimized)

    def start_spinner(self):
        """스피너 Start"""
        self._spinner_active = True
        if hasattr(self, "spinner_label"):
            self.spinner_label.config(text="⠋")
        self.animate_spinner_optimized()

    def stop_spinner(self):
        """스피너 정지"""
        self._spinner_active = False
        if hasattr(self, "spinner_label"):
            self.spinner_label.config(text="")

    def show_toast(self, message: str, kind: str = "info"):
        """Toast message 표시"""
        # 간단한 Message 박스로 대체
        if kind == "error":
            messagebox.showerror("Error", message)
        elif kind == "success" or kind == "ok":
            messagebox.showinfo("Success", message)
        else:
            messagebox.showinfo("Info", message)


def main():
    root = tk.Tk()
    app = CSVAnalyzerApp(root)

    # 윈도우 Close 이벤트
    def on_closing():
        if app.busy_after_id:
            root.after_cancel(app.busy_after_id)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
