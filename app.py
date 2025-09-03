
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

class AppState:
    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.filtered_df: pd.DataFrame | None = None
        self.page_index: int = 0
        self.page_size: int = 100
        self.numeric_cols: list[str] = []
        self.categorical_cols: list[str] = []

def format_bytes(size: int) -> str:
    power = 1024; n = 0; power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < len(power_labels): size /= power; n += 1
    return f"{size:.2f} {power_labels[n]}B"

def load_csv(state: AppState, file_path: str):
    state.df = pd.read_csv(file_path)
    state.numeric_cols = state.df.select_dtypes(include='number').columns.tolist()

def column_profile(df: pd.DataFrame, column: str) -> dict:
    return {
        "Type": str(df[column].dtype), 
        "Unique": len(df[column].unique()), 
        "Missing": f"{df[column].isnull().sum()}",
        "Non-null": f"{df[column].notna().sum()}",
        "Min": str(df[column].min()) if df[column].dtype in ['int64', 'float64'] else "N/A",
        "Max": str(df[column].max()) if df[column].dtype in ['int64', 'float64'] else "N/A",
        "Mean": f"{df[column].mean():.2f}" if df[column].dtype in ['int64', 'float64'] else "N/A"
    }

class ToastWindow:
    def __init__(self, parent, message: str, kind: str = "info", is_dark_mode: bool = False):
        # 더 자연스러운 라이트/다크 모드별 색상
        if is_dark_mode:
            self.colors = {
                "info": "#2C5F7D", 
                "ok": "#2E7D4B", 
                "warn": "#8B6914", 
                "error": "#B85450"
            }
            text_color = "#E8E8E8"
            border_color = "#404040"
        else:
            self.colors = {
                "info": "#D4EDDA", 
                "ok": "#DFF0D8", 
                "warn": "#FCF8E3", 
                "error": "#F8D7DA"
            }
            text_color = "#2C3E50"
            border_color = "#D1ECF1"
        
        self.toast = tk.Toplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.configure(bg=self.colors.get(kind, self.colors["info"]))
        
        # 화면 중앙 상단에 위치
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_rooty() + 50
        self.toast.geometry(f"300x60+{x}+{y}")
        
        # 둥근 모서리 효과를 위한 프레임
        main_frame = tk.Frame(self.toast, 
                             bg=self.colors.get(kind, self.colors["info"]),
                             relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 메시지 라벨
        label = tk.Label(main_frame, text=message, 
                        bg=self.colors.get(kind, self.colors["info"]),
                        fg=text_color, font=('Arial', 10, 'normal'),
                        wraplength=280)
        label.pack(expand=True, fill='both', padx=15, pady=15)
        
        # 부드러운 나타나기 효과
        self.fade_in()
        
        # 3초 후 자동 닫기
        self.toast.after(3000, self.fade_out)
    
    def fade_in(self):
        """부드러운 나타나기 효과"""
        self.toast.attributes('-alpha', 0.0)
        self.fade_in_step(0.0)
    
    def fade_in_step(self, alpha):
        """페이드 인 단계"""
        if alpha < 0.95:
            alpha += 0.1
            self.toast.attributes('-alpha', alpha)
            self.toast.after(30, lambda: self.fade_in_step(alpha))
        else:
            self.toast.attributes('-alpha', 1.0)
    
    def fade_out(self):
        """부드러운 사라지기 효과"""
        self.fade_out_step(1.0)
    
    def fade_out_step(self, alpha):
        """페이드 아웃 단계"""
        if alpha > 0.05:
            alpha -= 0.1
            try:
                self.toast.attributes('-alpha', alpha)
                self.toast.after(30, lambda: self.fade_out_step(alpha))
            except:
                self.close()
        else:
            self.close()
    
    def close(self):
        try:
            self.toast.destroy()
        except:
            pass

class DataCache:
    """데이터 캐싱 시스템"""
    def __init__(self, max_size: int = 50):
        self._cache = {}
        self._max_size = max_size
        self._access_order = []
    
    def get(self, key):
        """캐시에서 데이터 가져오기"""
        if key in self._cache:
            # LRU 순서 업데이트
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key, value):
        """캐시에 데이터 저장"""
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            # 가장 오래된 항목 제거
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = value
        self._access_order.append(key)
    
    def clear(self):
        """캐시 비우기"""
        self._cache.clear()
        self._access_order.clear()

class CSVAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.state = AppState()
        self.toast = None
        self.busy_after_id = None
        
        # 캐싱 시스템 추가
        self.data_cache = DataCache()
        
        # 다크모드 설정
        self.is_dark_mode = False
        self.setup_themes()
        self.setup_styles()
        self.setup_ui()

    def setup_themes(self):
        """라이트/다크 모드 색상 테마 설정"""
        self.themes = {
            'light': {
                'bg': '#FAFAFA',
                'panel_bg': '#FFFFFF',
                'text_color': '#2C3E50',
                'secondary_text': '#7F8C8D',
                'accent': '#3498DB',
                'button_bg': '#3498DB',
                'button_fg': '#FFFFFF',
                'entry_bg': '#FFFFFF',
                'tree_bg': '#F8F9FA',
                'border': '#E9ECEF',
                'hover': '#E3F2FD'
            },
            'dark': {
                'bg': '#1E1E1E',
                'panel_bg': '#2D2D30',
                'text_color': '#CCCCCC',  # 더 부드러운 회색
                'secondary_text': '#9E9E9E',  # 보조 텍스트도 부드럽게
                'accent': '#0E7EB8',
                'button_bg': '#0E7EB8',
                'button_fg': '#F5F5F5',  # 버튼 텍스트도 순백이 아닌 부드러운 흰색
                'entry_bg': '#3C3C3C',
                'tree_bg': '#252526',
                'border': '#3E3E42',
                'hover': '#094771'
            }
        }
        
    def update_widget_theme_optimized(self, widget, theme, visited=None, max_depth=10):
        """최적화된 테마 업데이트 (재귀 호출 제한 및 캐싱)"""
        if visited is None:
            visited = set()
        
        widget_id = id(widget)
        if widget_id in visited:
            return
        visited.add(widget_id)
        
        # 최대 방문 제한 및 깊이 제한
        if len(visited) > 1000 or max_depth <= 0:
            return
        
        try:
            widget_class = widget.winfo_class()
            
            # 자주 사용되는 위젯 타입 우선 처리
            if widget_class in ['Frame', 'Toplevel']:
                if widget_class == 'Frame':
                    widget.configure(bg=theme['panel_bg'])
            elif widget_class == 'Label':
                # 라벨 배경색이 테마 색상이면 업데이트
                current_bg = str(widget.cget('bg'))
                if current_bg in ['white', '#FFFFFF', '#2D2D30', '#FAFAFA', '#383838', '#2B2B2B']:
                    widget.configure(bg=theme['panel_bg'], fg=theme['text_color'])
            elif widget_class == 'Button':
                # 일반 버튼만 업데이트 (특정 버튼 제외)
                current_text = str(widget.cget('text'))
                if current_text not in ['🌙', '☀️', 'Toggle Dark Mode']:
                    current_bg = str(widget.cget('bg'))
                    if current_bg in ['#F0F0F0', '#FAFAFA', '#E1E1E1', '#D4D4D4', '#2B2B2B', '#383838', 'SystemButtonFace']:
                        widget.configure(bg=theme['button_bg'], fg=theme['button_fg'])
            elif widget_class == 'Text':
                widget.configure(bg=theme['tree_bg'], fg=theme['text_color'], insertbackground=theme['text_color'])
            elif widget_class == 'Entry':
                widget.configure(
                    bg=theme['entry_bg'], 
                    fg=theme['text_color'], 
                    insertbackground=theme['text_color'],
                    relief='flat',
                    bd=1
                )
            
            # 자식 위젯들에 제한된 깊이로 재귀 적용
            for child in widget.winfo_children():
                self.update_widget_theme_optimized(child, theme, visited, max_depth - 1)
                
        except tk.TclError:
            # 일부 위젯은 특정 속성을 지원하지 않을 수 있음
            pass
        """스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        self.apply_theme_styles()

    def apply_theme_styles(self):
        """현재 테마에 맞는 스타일 적용"""
        style = ttk.Style()
        theme = self.current_theme
        
        # TTK 스타일 설정
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'), foreground=theme['accent'])
        style.configure('Subtitle.TLabel', font=('Arial', 9), foreground=theme['secondary_text'])
        style.configure('Stats.TLabel', font=('Arial', 9), foreground=theme['text_color'])
        style.configure('BigButton.TButton', font=('Arial', 10, 'bold'), padding=(10, 15))
        
        # Notebook 스타일
        style.configure('TNotebook', background=theme['panel_bg'])
        style.configure('TNotebook.Tab', background=theme['button_bg'], foreground=theme['button_fg'])
        
        # Frame 스타일
        style.configure('TFrame', background=theme['panel_bg'])
        style.configure('TLabelFrame', background=theme['panel_bg'], foreground=theme['text_color'])
        
        # Treeview 스타일
        style.configure('Treeview', background=theme['tree_bg'], foreground=theme['text_color'], fieldbackground=theme['tree_bg'])
        style.configure('Treeview.Heading', background=theme['button_bg'], foreground=theme['button_fg'])

    def toggle_dark_mode(self):
        """다크모드 토글 (부드러운 전환 효과)"""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = self.themes['dark'] if self.is_dark_mode else self.themes['light']
        
        # 부드러운 전환을 위한 단계별 적용
        self.apply_theme_transition()
        
        # 통계 컨테이너 스타일 업데이트
        self.root.after(100, self.update_stats_container_style)
        
        # 통계 라벨 강제 업데이트
        self.root.after(200, lambda: self.force_update_stat_labels(self.current_theme))

    def apply_theme_transition(self):
        """부드러운 테마 전환"""
        # 스타일 먼저 적용
        self.apply_theme_styles()
        
        # 위젯들에 순차적으로 적용 (애니메이션 효과)
        self.transition_step = 0
        self.transition_widgets()

    def transition_widgets(self):
        """위젯 전환 애니메이션"""
        if self.transition_step == 0:
            # 1단계: 메인 배경
            self.root.configure(bg=self.current_theme['bg'])
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
            # 4단계: 마무리 및 버튼 업데이트
            self.finalize_theme_transition()

    def apply_theme_to_panels(self):
        """패널 위젯들에 테마 적용"""
        theme = self.current_theme
        
        # 메인 컨테이너들 찾아서 업데이트
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                self.update_frame_theme(widget, theme)

    def apply_theme_to_text_elements(self):
        """텍스트 요소들에 테마 적용"""
        theme = self.current_theme
        
        # 분석 텍스트 영역
        if hasattr(self, 'analysis_text'):
            self.analysis_text.configure(
                bg=theme['tree_bg'], 
                fg=theme['text_color'], 
                insertbackground=theme['text_color']
            )
        
        # 통계 라벨들 색상 업데이트
        if hasattr(self, 'rows_label') and self.rows_label.winfo_exists():
            current_text = self.rows_label.cget('text')
            self.rows_label.config(bg=theme['panel_bg'], fg=theme['text_color'])
        
        if hasattr(self, 'cols_label') and self.cols_label.winfo_exists():
            current_text = self.cols_label.cget('text')
            self.cols_label.config(bg=theme['panel_bg'], fg=theme['text_color'])
        
        if hasattr(self, 'memory_label') and self.memory_label.winfo_exists():
            current_text = self.memory_label.cget('text')
            self.memory_label.config(bg=theme['panel_bg'], fg=theme['text_color'])

    def finalize_theme_transition(self):
        """테마 전환 마무리"""
        # 전체 위젯 업데이트
        self.apply_theme_to_widgets()
        
        # 토글 버튼 업데이트 (부드러운 효과)
        self.animate_toggle_button()

    def animate_toggle_button(self):
        """토글 버튼 애니메이션"""
        theme = self.current_theme
        
        # 버튼 색상 전환
        self.theme_toggle_btn.configure(
            text="🌙 Dark" if not self.is_dark_mode else "☀️ Light",
            bg=theme['accent'],
            fg=theme['button_fg'],
            activebackground=theme['hover']
        )
        
        # 버튼 크기 애니메이션 (약간의 펄스 효과)
        original_font = self.theme_toggle_btn.cget('font')
        self.theme_toggle_btn.configure(font=('Arial', 9, 'bold'))
        self.root.after(100, lambda: self.theme_toggle_btn.configure(font=('Arial', 8)))

    def update_frame_theme(self, frame, theme):
        """프레임과 자식 위젯들 테마 업데이트"""
        try:
            frame.configure(bg=theme['panel_bg'])
            
            for child in frame.winfo_children():
                widget_class = child.winfo_class()
                
                if widget_class == 'Frame':
                    self.update_frame_theme(child, theme)
                elif widget_class == 'Label':
                    # 라벨 배경색이 패널 색상이면 업데이트
                    current_bg = str(child.cget('bg'))
                    if current_bg in ['white', '#FFFFFF', '#2D2D30', '#FAFAFA', '#383838', '#2B2B2B']:
                        child.configure(bg=theme['panel_bg'], fg=theme['text_color'])
                elif widget_class == 'LabelFrame':
                    child.configure(bg=theme['panel_bg'], fg=theme['text_color'])
                elif widget_class == 'Entry':
                    child.configure(
                        bg=theme['entry_bg'], 
                        fg=theme['text_color'], 
                        insertbackground=theme['text_color'],
                        selectbackground=theme['accent']
                    )
                elif widget_class == 'Checkbutton':
                    child.configure(
                        bg=theme['panel_bg'], 
                        fg=theme['text_color'], 
                        selectcolor=theme['entry_bg'],
                        activebackground=theme['hover']
                    )
                    
        except tk.TclError:
            pass

    def bind_hover_effects(self, button):
        """버튼 호버 효과 바인딩"""
        original_bg = button.cget('bg')
        hover_color = self.current_theme['hover']
        
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=original_bg)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def create_styled_button(self, parent, text, command, bg_color, fg_color='white'):
        """스타일이 적용된 버튼 생성"""
        btn = tk.Button(parent, text=text,
                       font=('Arial', 10), 
                       bg=bg_color, fg=fg_color,
                       relief='flat', bd=0, 
                       command=command,
                       cursor='hand2')
        
        # 호버 효과
        def on_enter(e):
            # 색상을 약간 어둡게
            r, g, b = btn.winfo_rgb(bg_color)
            r, g, b = int(r/256*0.8), int(g/256*0.8), int(b/256*0.8)
            hover_color = f"#{r:02x}{g:02x}{b:02x}"
            btn.configure(bg=hover_color)
        
        def on_leave(e):
            btn.configure(bg=bg_color)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn

    def apply_theme_to_widgets(self):
        """모든 위젯에 테마 적용"""
        theme = self.current_theme
        
        # 루트 윈도우
        self.root.configure(bg=theme['bg'])
        
        # 재귀적으로 모든 위젯 업데이트
        self.update_widget_theme(self.root, theme)

    def update_widget_theme(self, widget, theme):
        """위젯과 자식 위젯들에 테마 적용"""
        try:
            widget_class = widget.winfo_class()
            
            if widget_class in ['Frame', 'Toplevel']:
                widget.configure(bg=theme['panel_bg'])
            elif widget_class == 'Label':
                # 라벨의 현재 색상 확인
                current_bg = str(widget.cget('bg'))
                current_fg = str(widget.cget('fg'))
                
                # 더 포괄적인 조건으로 라벨 업데이트
                should_update_bg = current_bg in ['white', '#FFFFFF', '#F0F0F0', '#FAFAFA', '#383838', '#2B2B2B', '#2D2D30', 'SystemButtonFace']
                should_update_fg = current_fg in ['black', '#000000', 'white', '#FFFFFF', '#E8E8E8', '#CCCCCC', 'SystemWindowText', 'SystemButtonText']
                
                if should_update_bg or should_update_fg:
                    widget.configure(bg=theme['panel_bg'], fg=theme['text_color'])
            elif widget_class == 'Button':
                # 테마 토글 버튼과 일반 버튼 구분
                current_text = str(widget.cget('text'))
                
                # 테마 토글 버튼은 제외
                if current_text not in ['🌙', '☀️']:
                    current_bg = str(widget.cget('bg'))
                    current_fg = str(widget.cget('fg'))
                    
                    # 일반적인 버튼 배경색을 가진 경우
                    if current_bg in ['#F0F0F0', '#FAFAFA', '#E1E1E1', '#D4D4D4', '#2B2B2B', '#383838', 'SystemButtonFace']:
                        widget.configure(bg=theme['button_bg'], fg=theme['button_fg'])
                    # 텍스트가 기본 색상인 경우 텍스트만 변경
                    elif current_fg in ['black', '#000000', 'white', '#FFFFFF', 'SystemButtonText']:
                        widget.configure(fg=theme['button_fg'])
            elif widget_class == 'Text':
                widget.configure(bg=theme['tree_bg'], fg=theme['text_color'], insertbackground=theme['text_color'])
            elif widget_class == 'Entry':
                # Entry 위젯은 항상 테마 색상으로 업데이트
                widget.configure(
                    bg=theme['entry_bg'], 
                    fg=theme['text_color'], 
                    insertbackground=theme['text_color'],
                    relief='flat',
                    bd=1
                )
            elif widget_class == 'Checkbutton':
                widget.configure(bg=theme['panel_bg'], fg=theme['text_color'], selectcolor=theme['entry_bg'])
            elif widget_class == 'LabelFrame':
                widget.configure(
                    bg=theme['panel_bg'], 
                    fg=theme['text_color'],
                    relief='flat',
                    bd=1,
                    highlightthickness=0
                )
            
            # 자식 위젯들에 재귀 적용
            for child in widget.winfo_children():
                self.update_widget_theme(child, theme)
                
        except tk.TclError:
            # 일부 위젯은 특정 속성을 지원하지 않을 수 있음
            pass
        
        # 특정 라벨들을 강제로 업데이트 (테마 변경 시)
        if widget == self.root:  # 루트 위젯 처리 시에만 실행
            self.force_update_stat_labels(theme)
    
    def update_stats_container_style(self):
        """통계 컨테이너 스타일 업데이트"""
        if hasattr(self, 'stats_container') and self.stats_container.winfo_exists():
            if self.is_dark_mode:
                # 다크모드에서는 테두리 없이 배경 색상만으로 구분
                self.stats_container.configure(
                    bg=self.current_theme['panel_bg'],
                    relief='flat', 
                    bd=0
                )
            else:
                # 라이트모드에서는 얇은 테두리로 구분
                self.stats_container.configure(
                    bg=self.current_theme['panel_bg'],
                    relief='solid', 
                    bd=1
                )
    
    def force_update_stat_labels(self, theme):
        """통계 라벨들을 강제로 업데이트"""
        try:
            if hasattr(self, 'rows_label') and self.rows_label.winfo_exists():
                self.rows_label.configure(bg=theme['panel_bg'], fg=theme['text_color'])
            if hasattr(self, 'cols_label') and self.cols_label.winfo_exists():
                self.cols_label.configure(bg=theme['panel_bg'], fg=theme['text_color'])
            if hasattr(self, 'memory_label') and self.memory_label.winfo_exists():
                self.memory_label.configure(bg=theme['panel_bg'], fg=theme['text_color'])
        except tk.TclError:
            pass

    def setup_ui(self):
        """UI 설정 - 원래 dearpygui 디자인 복원"""
        self.root.title("CSV Analyzer (Compatible)")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.current_theme['bg'])

        # 상단 메뉴바
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 테마 메뉴
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)

        # 메인 컨테이너 (수평 레이아웃)
        main_container = tk.Frame(self.root, bg=self.current_theme['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 왼쪽 패널 (300px 고정)
        self.build_left_panel(main_container)
        
        # 오른쪽 패널
        self.build_right_panel(main_container)

    def build_left_panel(self, parent):
        """왼쪽 패널 구성"""
        left_frame = tk.Frame(parent, bg=self.current_theme['panel_bg'], relief='solid', bd=1, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)  # 크기 고정

        # 제목과 테마 토글 버튼
        header_frame = tk.Frame(left_frame, bg=self.current_theme['panel_bg'])
        header_frame.pack(fill='x', pady=(15, 5))

        title_label = tk.Label(header_frame, text="CSV ANALYZER", 
                              font=('Arial', 14, 'bold'), 
                              fg=self.current_theme['accent'], bg=self.current_theme['panel_bg'])
        title_label.pack(side='left')

        # 다크모드 토글 버튼 (호버 효과 추가)
        self.theme_toggle_btn = tk.Button(header_frame, text="🌙 Dark",
                                         font=('Arial', 8), 
                                         bg=self.current_theme['button_bg'], 
                                         fg=self.current_theme['button_fg'],
                                         relief='flat', bd=0, 
                                         command=self.toggle_dark_mode,
                                         activebackground=self.current_theme['hover'],
                                         cursor='hand2')
        self.theme_toggle_btn.pack(side='right', padx=(5, 0))
        
        # 호버 효과 바인딩
        self.bind_hover_effects(self.theme_toggle_btn)

        # 구분선
        sep1 = ttk.Separator(left_frame, orient='horizontal')
        sep1.pack(fill='x', padx=10, pady=5)

        # Load CSV 버튼 (호버 효과 추가)
        self.load_btn = tk.Button(left_frame, text="Load CSV File",
                                 font=('Arial', 11, 'bold'),
                                 bg='#3498DB', fg=self.current_theme['button_fg'],
                                 relief='flat', bd=0,
                                 height=2, command=self.load_csv_file,
                                 cursor='hand2')
        self.load_btn.pack(fill='x', padx=15, pady=(10, 5))
        
        # 로드 버튼 호버 효과
        def load_btn_hover_enter(e):
            self.load_btn.configure(bg='#2980B9')
        def load_btn_hover_leave(e):
            self.load_btn.configure(bg='#3498DB')
        
        self.load_btn.bind('<Enter>', load_btn_hover_enter)
        self.load_btn.bind('<Leave>', load_btn_hover_leave)

        # 드래그 앤 드롭 안내
        drag_label = tk.Label(left_frame, text="or drag and drop CSV file anywhere",
                             font=('Arial', 9), fg=self.current_theme['secondary_text'], 
                             bg=self.current_theme['panel_bg'])
        drag_label.pack(pady=(5, 15))

        # 통계 섹션
        # Statistics 섹션 (일반 Frame으로 변경)
        stats_section = tk.Frame(left_frame, bg=self.current_theme['panel_bg'])
        stats_section.pack(fill='x', padx=15, pady=10)
        
        # Statistics 제목
        stats_title = tk.Label(stats_section, text="Statistics", 
                              font=('Arial', 10, 'bold'),
                              bg=self.current_theme['panel_bg'], 
                              fg=self.current_theme['text_color'])
        stats_title.pack(anchor='w', pady=(0, 5))
        
        # 통계 테이블
        self.stats_container = tk.Frame(stats_section, bg=self.current_theme['panel_bg'])
        self.update_stats_container_style()
        self.stats_container.pack(fill='x', padx=5, pady=5)

        # Rows
        row1 = tk.Frame(self.stats_container, bg=self.current_theme['panel_bg'])
        row1.pack(fill='x', pady=2)
        tk.Label(row1, text="Rows:", font=('Arial', 9), 
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='w').pack(side='left')
        self.rows_label = tk.Label(row1, text="0", font=('Arial', 9), 
                                  bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='e')
        self.rows_label.pack(side='right')

        # Columns
        row2 = tk.Frame(self.stats_container, bg=self.current_theme['panel_bg'])
        row2.pack(fill='x', pady=2)
        tk.Label(row2, text="Columns:", font=('Arial', 9), 
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='w').pack(side='left')
        self.cols_label = tk.Label(row2, text="0", font=('Arial', 9), 
                                  bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='e')
        self.cols_label.pack(side='right')

        # Memory
        row3 = tk.Frame(self.stats_container, bg=self.current_theme['panel_bg'])
        row3.pack(fill='x', pady=2)
        tk.Label(row3, text="Memory:", font=('Arial', 9), 
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='w').pack(side='left')
        self.memory_label = tk.Label(row3, text="0 MB", font=('Arial', 9), 
                                    bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], anchor='e')
        self.memory_label.pack(side='right')

        # 구분선
        sep2 = ttk.Separator(left_frame, orient='horizontal')
        sep2.pack(fill='x', padx=10, pady=15)

        # 상태 표시
        status_container = tk.Frame(left_frame, bg=self.current_theme['panel_bg'])
        status_container.pack(fill='x', padx=15, pady=(0, 15))

        # 로딩 스피너 (간단한 점 애니메이션)
        self.spinner_label = tk.Label(status_container, text="", 
                                     font=('Arial', 12), fg=self.current_theme['accent'], 
                                     bg=self.current_theme['panel_bg'])
        self.spinner_label.pack(side='left')

        # 상태 텍스트
        self.status_label = tk.Label(status_container, text="Ready", 
                                    font=('Arial', 9), fg=self.current_theme['secondary_text'], 
                                    bg=self.current_theme['panel_bg'])
        self.status_label.pack(side='left', padx=(5, 0))

    def build_right_panel(self, parent):
        """오른쪽 패널 구성"""
        right_frame = tk.Frame(parent, bg=self.current_theme['panel_bg'], relief='solid', bd=1)
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
        """CSV 슬라이싱 탭 - 대용량 데이터 지원"""
        slicer_frame = ttk.Frame(self.notebook)
        self.notebook.add(slicer_frame, text="CSV Slicer")

        # 컨트롤 영역
        control_frame = tk.Frame(slicer_frame, bg=self.current_theme['panel_bg'])
        control_frame.pack(fill='x', padx=10, pady=10)

        # 행 범위 선택
        range_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        range_frame.pack(fill='x', pady=(0, 10))

        tk.Label(range_frame, text="Row Range:", font=('Arial', 10, 'bold'),
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color']).pack(side='left')

        # 시작 행
        tk.Label(range_frame, text="Start:", bg=self.current_theme['panel_bg'], 
                fg=self.current_theme['text_color']).pack(side='left', padx=(10, 5))
        self.start_row_var = tk.StringVar(value="0")
        self.start_row_entry = tk.Entry(range_frame, textvariable=self.start_row_var, width=10,
                                       bg=self.current_theme['entry_bg'], fg=self.current_theme['text_color'])
        self.start_row_entry.pack(side='left', padx=(0, 10))

        # 끝 행
        tk.Label(range_frame, text="End:", bg=self.current_theme['panel_bg'], 
                fg=self.current_theme['text_color']).pack(side='left', padx=(0, 5))
        self.end_row_var = tk.StringVar(value="1000")
        self.end_row_entry = tk.Entry(range_frame, textvariable=self.end_row_var, width=10,
                                     bg=self.current_theme['entry_bg'], fg=self.current_theme['text_color'])
        self.end_row_entry.pack(side='left', padx=(0, 10))

        # 컬럼 선택
        column_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        column_frame.pack(fill='x', pady=(0, 10))

        tk.Label(column_frame, text="Columns:", font=('Arial', 10, 'bold'),
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color']).pack(side='left')

        # 컬럼 선택 체크박스들
        self.column_checkboxes = {}
        self.column_vars = {}
        
        # 컬럼 선택을 위한 스크롤 가능한 프레임
        column_scroll_frame = tk.Frame(column_frame, bg=self.current_theme['panel_bg'])
        column_scroll_frame.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        self.column_canvas = tk.Canvas(column_scroll_frame, height=60, bg=self.current_theme['panel_bg'])
        scrollbar = ttk.Scrollbar(column_scroll_frame, orient="horizontal", command=self.column_canvas.xview)
        self.column_canvas.configure(xscrollcommand=scrollbar.set)
        
        self.column_canvas.pack(side='top', fill='x', expand=True)
        scrollbar.pack(side='bottom', fill='x')
        
        self.column_inner_frame = tk.Frame(self.column_canvas, bg=self.current_theme['panel_bg'])
        self.column_canvas.create_window((0, 0), window=self.column_inner_frame, anchor='nw')
        
        # Select All / Clear All 버튼들
        button_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        button_frame.pack(fill='x', pady=(0, 10))
        
        self.select_all_btn = self.create_styled_button(button_frame, "Select All", 
                                                       self.select_all_columns, '#27AE60')
        self.select_all_btn.pack(side='left', padx=(0, 5))
        
        self.clear_all_btn = self.create_styled_button(button_frame, "Clear All", 
                                                      self.clear_all_columns, '#E74C3C')
        self.clear_all_btn.pack(side='left', padx=(0, 5))

        # 슬라이스 및 내보내기 버튼
        self.slice_btn = self.create_styled_button(control_frame, "Slice Data", 
                                                  self.slice_data, '#3498DB')
        self.slice_btn.pack(side='left', padx=(0, 5))

        self.export_slice_btn = self.create_styled_button(control_frame, "Export Sliced Data", 
                                                         self.export_sliced_data, '#9B59B6')
        self.export_slice_btn.pack(side='left')

        # 슬라이스된 데이터 표시 영역
        result_frame = tk.Frame(slicer_frame, bg=self.current_theme['panel_bg'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 결과 정보
        info_frame = tk.Frame(result_frame, bg=self.current_theme['panel_bg'])
        info_frame.pack(fill='x', pady=(0, 5))
        
        self.slice_info_label = tk.Label(info_frame, text="No data sliced yet", 
                                        font=('Arial', 9), fg=self.current_theme['secondary_text'],
                                        bg=self.current_theme['panel_bg'])
        self.slice_info_label.pack(side='left')

        # 슬라이스된 데이터 Treeview
        tree_container = tk.Frame(result_frame, bg=self.current_theme['panel_bg'])
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.slicer_tree = ttk.Treeview(tree_container, show='tree headings', height=20)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.slicer_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.slicer_tree.xview)
        
        self.slicer_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 그리드 배치
        self.slicer_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # 초기 상태
        self.current_sliced_data = None
        self.update_column_checkboxes()

    def update_column_checkboxes(self):
        """컬럼 체크박스 업데이트"""
        # 기존 체크박스 제거
        for widget in self.column_inner_frame.winfo_children():
            widget.destroy()
        
        if self.state.df is None:
            return
        
        # 컬럼별 체크박스 생성
        for i, col in enumerate(self.state.df.columns):
            var = tk.BooleanVar(value=True)  # 기본적으로 모두 선택
            self.column_vars[col] = var
            
            cb = tk.Checkbutton(self.column_inner_frame, text=col, variable=var,
                               bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'],
                               selectcolor=self.current_theme['entry_bg'])
            cb.pack(side='left', padx=5)
        
        # 캔버스 크기 업데이트
        self.column_inner_frame.update_idletasks()
        self.column_canvas.configure(scrollregion=self.column_canvas.bbox('all'))

    def select_all_columns(self):
        """모든 컬럼 선택"""
        for var in self.column_vars.values():
            var.set(True)

    def clear_all_columns(self):
        """모든 컬럼 선택 해제"""
        for var in self.column_vars.values():
            var.set(False)

    def slice_data(self):
        """데이터 슬라이싱 실행"""
        if self.state.df is None:
            self.show_toast("No data loaded", "error")
            return
        
        try:
            # 행 범위 파싱
            start_row = int(self.start_row_var.get())
            end_row = int(self.end_row_var.get())
            
            # 유효성 검사
            if start_row < 0:
                start_row = 0
            if end_row > len(self.state.df):
                end_row = len(self.state.df)
            if start_row >= end_row:
                self.show_toast("Invalid row range", "error")
                return
            
            # 선택된 컬럼들
            selected_columns = [col for col, var in self.column_vars.items() if var.get()]
            if not selected_columns:
                self.show_toast("No columns selected", "error")
                return
            
            # 데이터 슬라이싱 (최적화된 방식)
            self.current_sliced_data = self.state.df.iloc[start_row:end_row][selected_columns].copy()
            
            # 결과 표시
            self.display_sliced_data()
            
            # 정보 업데이트
            info_text = f"Sliced {len(self.current_sliced_data):,} rows, {len(selected_columns)} columns"
            self.slice_info_label.config(text=info_text)
            
            self.show_toast(f"Data sliced successfully: {len(self.current_sliced_data)} rows", "ok")
            
        except ValueError as e:
            self.show_toast(f"Invalid input: {e}", "error")
        except Exception as e:
            self.show_toast(f"Slicing failed: {e}", "error")

    def display_sliced_data(self):
        """슬라이스된 데이터 표시 (페이지네이션 지원)"""
        if self.current_sliced_data is None or self.current_sliced_data.empty:
            return
        
        # Treeview 초기화
        for item in self.slicer_tree.get_children():
            self.slicer_tree.delete(item)
        
        # 컬럼 헤더 설정
        self.slicer_tree['columns'] = list(self.current_sliced_data.columns)
        for col in self.current_sliced_data.columns:
            self.slicer_tree.heading(col, text=col)
            self.slicer_tree.column(col, width=min(120, len(str(col)) * 8))
        
        # 데이터 표시 (최대 10000행까지 표시 제한 해제 - 페이지네이션으로 처리)
        max_display_rows = min(5000, len(self.current_sliced_data))  # 성능을 위해 5000행으로 제한
        
        for idx, row in self.current_sliced_data.head(max_display_rows).iterrows():
            values = []
            for val in row:
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                elif pd.isna(val):
                    values.append("")
                else:
                    values.append(str(val))
            self.slicer_tree.insert('', 'end', values=values)
        
        # 대용량 데이터 안내
        if len(self.current_sliced_data) > max_display_rows:
            self.show_toast(f"Showing first {max_display_rows:,} rows of {len(self.current_sliced_data):,} total rows", "info")

    def export_sliced_data(self):
        """슬라이스된 데이터 내보내기"""
        if self.current_sliced_data is None:
            self.show_toast("No sliced data to export", "error")
            return
        
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save sliced data"
            )
            
            if file_path:
                self.current_sliced_data.to_csv(file_path, index=True)
                self.show_toast(f"Exported to {file_path}", "success")
                
        except Exception as e:
            self.show_toast(f"Export failed: {e}", "error")

    def build_combinations_tab(self):
        """조합 분석 탭"""
        combinations_frame = ttk.Frame(self.notebook)
        self.notebook.add(combinations_frame, text="Combinations Analysis")

        # 메인 컨테이너
        main_container = tk.Frame(combinations_frame, bg=self.current_theme['panel_bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 상단 컨트롤 영역
        control_frame = tk.Frame(main_container, bg=self.current_theme['panel_bg'])
        control_frame.pack(fill='x', pady=(0, 10))

        # 제목
        title_label = tk.Label(control_frame, text="데이터 관계 분석", 
                              font=('Arial', 12, 'bold'),
                              bg=self.current_theme['panel_bg'], 
                              fg=self.current_theme['text_color'])
        title_label.pack(side='left')

        # 분석 실행 버튼
        self.run_combinations_btn = tk.Button(control_frame, text="분석 실행",
                                            command=self.run_combinations_analysis,
                                            bg=self.current_theme['button_bg'],
                                            fg=self.current_theme['button_fg'],
                                            font=('Arial', 10, 'bold'),
                                            relief='flat', bd=0, padx=20, pady=8)
        self.run_combinations_btn.pack(side='right')

        # 설정 영역
        settings_frame = tk.Frame(main_container, bg=self.current_theme['panel_bg'])
        settings_frame.pack(fill='x', pady=(0, 10))

        # DSL 토큰 입력
        dsl_label = tk.Label(settings_frame, text="DSL 토큰 (선택사항):",
                           bg=self.current_theme['panel_bg'], 
                           fg=self.current_theme['text_color'])
        dsl_label.pack(side='left', padx=(0, 10))

        self.dsl_tokens_entry = tk.Entry(settings_frame, width=30,
                                       bg=self.current_theme['entry_bg'],
                                       fg=self.current_theme['text_color'],
                                       insertbackground=self.current_theme['text_color'])
        self.dsl_tokens_entry.pack(side='left', padx=(0, 20))

        # 상위 K개 결과 설정
        topk_label = tk.Label(settings_frame, text="상위 결과 수:",
                            bg=self.current_theme['panel_bg'], 
                            fg=self.current_theme['text_color'])
        topk_label.pack(side='left', padx=(0, 5))

        self.topk_var = tk.StringVar(value="10")
        topk_entry = tk.Entry(settings_frame, textvariable=self.topk_var, width=5,
                            bg=self.current_theme['entry_bg'],
                            fg=self.current_theme['text_color'],
                            insertbackground=self.current_theme['text_color'])
        topk_entry.pack(side='left')

        # 결과 표시 영역
        result_frame = tk.Frame(main_container, bg=self.current_theme['panel_bg'])
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 결과 텍스트 위젯 (스크롤 포함)
        text_frame = tk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.combinations_result_text = tk.Text(text_frame, 
                                              bg=self.current_theme['tree_bg'],
                                              fg=self.current_theme['text_color'],
                                              insertbackground=self.current_theme['text_color'],
                                              font=('Consolas', 9),
                                              wrap=tk.WORD)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.combinations_result_text.yview)
        self.combinations_result_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.combinations_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 초기 안내 메시지
        initial_message = """
📊 조합 분석 도구

이 도구는 데이터의 컬럼 간 관계를 자동으로 분석합니다:

🔢 수치형 분석: 
   • 상관관계 분석
   • 피어슨 상관계수
   
📊 범주형 분석:
   • Cramér's V 계산
   • 카이제곱 검정
   • 연관규칙 분석
   
🔀 혼합형 분석:
   • ANOVA 분석
   • 효과 크기 계산

사용법:
1. 데이터를 먼저 로드하세요
2. 필요시 DSL 토큰을 입력하세요 (예: C1,C2,C3)
3. '분석 실행' 버튼을 클릭하세요

분석 결과는 아래에 표시됩니다.
        """
        self.combinations_result_text.insert(1.0, initial_message)
        self.combinations_result_text.config(state=tk.DISABLED)

    def run_combinations_analysis(self):
        """조합 분석 실행"""
        if self.state.df is None:
            self.show_toast("데이터를 먼저 로드해주세요", "error")
            return

        try:
            # 분석 중 상태 표시
            self.run_combinations_btn.config(text="분석 중...", state="disabled")
            self.combinations_result_text.config(state=tk.NORMAL)
            self.combinations_result_text.delete(1.0, tk.END)
            self.combinations_result_text.insert(1.0, "🔄 분석을 실행 중입니다...\n")
            self.combinations_result_text.config(state=tk.DISABLED)
            self.root.update()

            # DSL 토큰 파싱
            dsl_tokens = None
            if self.dsl_tokens_entry.get().strip():
                dsl_tokens = [token.strip() for token in self.dsl_tokens_entry.get().split(',')]

            # 분석 설정
            from combinations import AdvancedCombinationsAnalyzer, AnalysisConfig
            
            try:
                top_k = int(self.topk_var.get())
            except ValueError:
                top_k = 10

            config = AnalysisConfig(
                top_k=top_k,
                parallel_processing=False,  # GUI에서는 단일 스레드 사용
                enable_caching=True
            )

            # 분석 실행
            analyzer = AdvancedCombinationsAnalyzer(config)
            results = analyzer.analyze_all_combinations(self.state.df, dsl_tokens)

            # 결과 표시
            summary = analyzer.get_analysis_summary(results)
            detailed_results = self.format_detailed_results(results)

            # 텍스트 위젯에 결과 표시
            self.combinations_result_text.config(state=tk.NORMAL)
            self.combinations_result_text.delete(1.0, tk.END)
            self.combinations_result_text.insert(1.0, summary + "\n\n" + detailed_results)
            self.combinations_result_text.config(state=tk.DISABLED)

            # 성공 토스트
            self.show_toast("분석이 완료되었습니다", "success")

        except Exception as e:
            # 오류 처리
            self.combinations_result_text.config(state=tk.NORMAL)
            self.combinations_result_text.delete(1.0, tk.END)
            self.combinations_result_text.insert(1.0, f"❌ 분석 중 오류가 발생했습니다:\n\n{str(e)}")
            self.combinations_result_text.config(state=tk.DISABLED)
            self.show_toast(f"분석 실패: {str(e)}", "error")

        finally:
            # 버튼 상태 복원
            self.run_combinations_btn.config(text="분석 실행", state="normal")

    def format_detailed_results(self, results):
        """상세 결과 포맷팅"""
        detailed = ["=" * 60, "📈 상세 분석 결과", "=" * 60, ""]

        # 수치형 조합 결과
        if "numerical_combinations" in results and "error" not in results["numerical_combinations"]:
            num_results = results["numerical_combinations"]
            detailed.extend([
                "🔢 수치형 컬럼 상관관계 분석:", 
                "-" * 30
            ])
            
            for idx, corr in enumerate(num_results.get("strong_correlations", [])[:5], 1):
                detailed.append(f"{idx}. {corr['column1']} ↔ {corr['column2']}")
                detailed.append(f"   상관계수: {corr['correlation']:.3f} ({corr['strength']})")
                detailed.append(f"   방향: {corr['direction']}")
                detailed.append("")

        # 범주형 조합 결과
        if "categorical_combinations" in results and "error" not in results["categorical_combinations"]:
            cat_results = results["categorical_combinations"]
            detailed.extend([
                "📊 범주형 컬럼 연관성 분석:", 
                "-" * 30
            ])
            
            for idx, assoc in enumerate(cat_results.get("associations", [])[:5], 1):
                detailed.append(f"{idx}. {assoc['column1']} ↔ {assoc['column2']}")
                detailed.append(f"   Cramér's V: {assoc['cramers_v']:.3f} ({assoc['association_strength']})")
                detailed.append(f"   유의성: {'유의함' if assoc['significant'] else '유의하지 않음'}")
                detailed.append("")

        # 혼합형 조합 결과
        if "mixed_combinations" in results and "error" not in results["mixed_combinations"]:
            mixed_results = results["mixed_combinations"]
            detailed.extend([
                "🔀 혼합형 분석 (수치형 vs 범주형):", 
                "-" * 30
            ])
            
            for idx, anova in enumerate(mixed_results.get("anova_results", [])[:5], 1):
                detailed.append(f"{idx}. {anova['numerical_column']} vs {anova['categorical_column']}")
                detailed.append(f"   F-통계량: {anova['f_statistic']:.3f}")
                detailed.append(f"   효과 크기: {anova['eta_squared']:.3f} ({anova['effect_size']})")
                detailed.append(f"   유의성: {'유의함' if anova['significant'] else '유의하지 않음'}")
                detailed.append("")

        return "\n".join(detailed)

    def build_preview_tab(self):
        """데이터 미리보기 탭"""
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="Data Preview")

        # 미리보기 라벨과 행 수 정보
        header_frame = tk.Frame(preview_frame, bg=self.current_theme['panel_bg'])
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        preview_label = tk.Label(header_frame, text="Preview", 
                                font=('Arial', 11, 'bold'),
                                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])
        preview_label.pack(side='left')
        
        self.row_count_label = tk.Label(header_frame, text="", 
                                       font=('Arial', 9),
                                       bg=self.current_theme['panel_bg'], fg=self.current_theme['secondary_text'])
        self.row_count_label.pack(side='right')

        # 테이블 프레임
        table_frame = tk.Frame(preview_frame, bg=self.current_theme['panel_bg'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Treeview with scrollbars
        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Treeview 생성 (show 옵션과 height 명시적 설정)
        self.preview_tree = ttk.Treeview(tree_container, show='tree headings', height=25)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.preview_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        
        self.preview_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 그리드 배치
        self.preview_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

    def build_analysis_tab(self):
        """분석 탭 - 시각화 포함"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")

        # 컨트롤 영역
        control_frame = tk.Frame(analysis_frame, bg=self.current_theme['panel_bg'])
        control_frame.pack(fill='x', padx=10, pady=10)

        # 컬럼 선택
        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(control_frame, textvariable=self.column_var,
                                        values=["No columns loaded"], width=30)
        self.column_combo.pack(side='left', padx=(0, 10))

        # 분석 버튼
        analyze_btn = self.create_styled_button(control_frame, "Analyze Column", 
                                               self.analyze_column, '#3498DB')
        analyze_btn.pack(side='left', padx=(0, 10))

        # 시각화 버튼
        visualize_btn = self.create_styled_button(control_frame, "Create Visualization", 
                                                 self.create_visualization, '#E74C3C')
        visualize_btn.pack(side='left')

        # 메인 컨텐츠 영역을 좌우로 분할
        main_paned = ttk.PanedWindow(analysis_frame, orient='horizontal')
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 왼쪽: 분석 결과 텍스트
        left_frame = tk.Frame(main_paned, bg=self.current_theme['panel_bg'])
        main_paned.add(left_frame, weight=1)

        # 분석 결과 라벨
        result_label = tk.Label(left_frame, text="Analysis Results", 
                               font=('Arial', 11, 'bold'), bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])
        result_label.pack(anchor='w', pady=(0, 5))

        # 스크롤 가능한 텍스트 영역
        text_container = tk.Frame(left_frame, bg=self.current_theme['panel_bg'])
        text_container.pack(fill=tk.BOTH, expand=True)

        self.analysis_text = tk.Text(text_container, wrap=tk.WORD, 
                                    font=('Consolas', 9), bg=self.current_theme['tree_bg'], 
                                    fg=self.current_theme['text_color'], height=20,
                                    insertbackground=self.current_theme['text_color'])
        text_scrollbar = ttk.Scrollbar(text_container, command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=text_scrollbar.set)

        self.analysis_text.pack(side='left', fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side='right', fill='y')

        # 오른쪽: 시각화 영역
        right_frame = tk.Frame(main_paned, bg=self.current_theme['panel_bg'])
        main_paned.add(right_frame, weight=1)

        # 시각화 라벨
        viz_label = tk.Label(right_frame, text="Visualization", 
                            font=('Arial', 11, 'bold'), bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])
        viz_label.pack(anchor='w', pady=(0, 5))

        # 시각화 캔버스 영역
        self.viz_frame = tk.Frame(right_frame, bg=self.current_theme['panel_bg'], relief='sunken', bd=1)
        self.viz_frame.pack(fill=tk.BOTH, expand=True)

        # 초기 메시지
        self.analysis_text.insert('1.0', "Select a column and click 'Analyze Column' to view statistics.")
        self.analysis_text.configure(state='disabled')

        # 초기 시각화 메시지
        initial_viz_label = tk.Label(self.viz_frame, text="Select a column and click 'Create Visualization'\nto generate charts.", 
                                    font=('Arial', 10), fg=self.current_theme['secondary_text'], bg=self.current_theme['panel_bg'])
        initial_viz_label.pack(expand=True)

    def show_toast(self, message: str, kind: str = "info"):
        """토스트 메시지 표시"""
        if self.toast:
            try:
                self.toast.close()
            except:
                pass
        self.toast = ToastWindow(self.root, message, kind, self.is_dark_mode)

    def begin_busy(self, status_text: str = "Working..."):
        """로딩 상태 시작"""
        self.status_label.config(text=status_text)
        self.load_btn.config(state='disabled')
        self.animate_spinner()

    def end_busy(self, done_text: str = "Done", ok: bool = True):
        """로딩 상태 종료"""
        self.status_label.config(text=done_text)
        self.load_btn.config(state='normal')
        self.stop_spinner()
        self.show_toast(done_text, "ok" if ok else "error")

    def animate_spinner(self):
        """스피너 애니메이션"""
        current = self.spinner_label.cget('text')
        if len(current) >= 3:
            self.spinner_label.config(text='.')
        else:
            self.spinner_label.config(text=current + '.')
        
        self.busy_after_id = self.root.after(500, self.animate_spinner)

    def stop_spinner(self):
        """스피너 중지"""
        if self.busy_after_id:
            self.root.after_cancel(self.busy_after_id)
            self.busy_after_id = None
        self.spinner_label.config(text='')

    def load_csv_file(self):
        """CSV 파일 로드 다이얼로그"""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path: str):
        """CSV 파일 로드 (청킹 및 슬라이싱 적용)"""
        if not file_path.lower().endswith('.csv'):
            self.show_toast("Error: Not a CSV file", "error")
            return

        self.begin_busy("Loading...")

        def load_thread():
            try:
                # 큰 파일 처리를 위한 청킹
                chunk_size = 50000  # 50K로 증가
                chunks = []
                total_rows = 0
                
                # 파일 크기 체크
                file_size = Path(file_path).stat().st_size
                if file_size > 100 * 1024 * 1024:  # 100MB 이상 (기준 상향)
                    # 샘플링 로드 (처음 50000행으로 증가)
                    self.state.df = pd.read_csv(file_path, nrows=50000)
                    self.root.after(0, lambda: self.on_csv_loaded(file_path, is_sample=True))
                else:
                    # 전체 로드
                    self.state.df = pd.read_csv(file_path)
                    self.root.after(0, lambda: self.on_csv_loaded(file_path, is_sample=False))
                    
                self.state.numeric_cols = self.state.df.select_dtypes(include='number').columns.tolist()
                
            except Exception as e:
                self.root.after(0, lambda: self.on_csv_error(str(e)))

        threading.Thread(target=load_thread, daemon=True).start()

    def on_csv_loaded(self, file_path: str, is_sample: bool = False):
        """CSV 로드 완료"""
        # 통계 업데이트 (테마 색상도 함께 적용)
        self.rows_label.config(text=f"{len(self.state.df):,}" + (" (sample)" if is_sample else ""),
                              bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])
        self.cols_label.config(text=f"{len(self.state.df.columns):,}",
                              bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])
        self.memory_label.config(text=format_bytes(self.state.df.memory_usage(deep=True).sum()),
                                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'])

        # 컬럼 콤보박스 업데이트
        self.column_combo['values'] = list(self.state.df.columns)
        if len(self.state.df.columns) > 0:  # 수정: .empty 대신 len() 사용
            self.column_combo.current(0)

        # 슬라이서 탭의 컬럼 체크박스 업데이트
        self.update_column_checkboxes()

        # 미리보기 테이블 업데이트 (슬라이싱 적용)
        self.update_preview_table()

        file_name = Path(file_path).name
        status_msg = f"Loaded: {file_name}" + (" (first 10K rows)" if is_sample else "")
        self.end_busy(status_msg, True)

    def on_csv_error(self, error_msg: str):
        """CSV 로드 오류"""
        self.end_busy(f"Failed to load: {error_msg}", False)

    def update_preview_table(self):
        """미리보기 테이블 업데이트 (슬라이싱 적용)"""
        # 기존 데이터 제거
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        if self.state.df is None or self.state.df.empty:
            self.row_count_label.config(text="No data loaded")
            return

        # 컬럼 설정
        columns = list(self.state.df.columns)
        
        # Treeview 컬럼 설정
        self.preview_tree['columns'] = columns
        self.preview_tree['show'] = 'tree headings'  # 헤더 표시 확실히 설정
        
        # 인덱스 컬럼 설정
        self.preview_tree.heading('#0', text='Index', anchor='w')
        self.preview_tree.column('#0', width=60, anchor='w', minwidth=60)

        # 데이터 컬럼들 설정
        for col in columns:
            self.preview_tree.heading(col, text=col, anchor='w')
            self.preview_tree.column(col, width=120, anchor='w', minwidth=80)

        # 데이터 추가 (1000행으로 제한 - 슬라이싱 증가)
        preview_data = self.state.df.head(1000)
        
        for idx, row in preview_data.iterrows():
            # 텍스트 길이 제한 (50자)
            values = []
            for val in row:
                str_val = str(val)
                if len(str_val) > 50:
                    values.append(str_val[:47] + '...')
                else:
                    values.append(str_val)
            
            self.preview_tree.insert('', 'end', text=str(idx), values=values)
        
        total_loaded = len(self.state.df)
        preview_shown = len(preview_data)
        
        # 행 수 정보 업데이트
        self.row_count_label.config(text=f"Showing {preview_shown:,} of {total_loaded:,} rows")
        
        # Treeview 업데이트 강제
        self.preview_tree.update_idletasks()

    def analyze_column(self):
        """컬럼 분석"""
        if self.state.df is None:
            self.show_toast("No data loaded", "warn")
            return

        column = self.column_var.get()
        if not column or column == "No columns loaded":
            self.show_toast("Select a column", "warn")
            return

        try:
            info = column_profile(self.state.df, column)

            # 분석 결과 표시
            self.analysis_text.configure(state='normal')
            self.analysis_text.delete('1.0', 'end')

            # 제목
            self.analysis_text.insert('end', f"Analysis for: {column}\n", 'title')
            self.analysis_text.insert('end', "=" * 50 + "\n\n")

            # 통계 테이블
            for key, value in info.items():
                self.analysis_text.insert('end', f"{key:<15}: {value}\n")

            # 샘플 데이터 (슬라이싱 적용)
            self.analysis_text.insert('end', f"\nSample values (first 50):\n")
            self.analysis_text.insert('end', "-" * 30 + "\n")
            sample_values = self.state.df[column].dropna().head(50)
            for i, val in enumerate(sample_values, 1):
                val_str = str(val)
                if len(val_str) > 80:
                    val_str = val_str[:77] + '...'
                self.analysis_text.insert('end', f"{i:2d}. {val_str}\n")

            self.analysis_text.configure(state='disabled')

        except Exception as e:
            self.show_toast(f"Failed to analyze: {e}", "error")

    def create_visualization(self):
        """선택된 컬럼의 시각화 생성"""
        if self.state.df is None or self.state.df.empty:
            self.show_toast("No data loaded", "error")
            return

        column = self.column_var.get()
        if not column or column == "No columns loaded":
            self.show_toast("Please select a column first", "error")
            return

        try:
            # 기존 시각화 제거
            for widget in self.viz_frame.winfo_children():
                widget.destroy()

            # matplotlib 한글 폰트 설정
            plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 다크모드에 따른 색상 설정
            current_theme = self.themes['dark'] if self.is_dark_mode else self.themes['light']
            
            # Figure 생성 및 테마 적용
            fig, axes = plt.subplots(2, 2, figsize=(8, 6))
            
            if self.is_dark_mode:
                fig.patch.set_facecolor('#2B2B2B')
                text_color = '#CCCCCC'
                grid_color = '#404040'
                chart_colors = ['#5DADE2', '#F1948A', '#82E0AA', '#F7DC6F']
            else:
                fig.patch.set_facecolor('white')
                text_color = '#333333'
                grid_color = '#E0E0E0'
                chart_colors = ['skyblue', 'lightcoral', 'lightgreen', 'orange']
            
            fig.suptitle(f'Visualization: {column}', fontsize=12, fontweight='bold', color=text_color)
            
            data = self.state.df[column].dropna()
            
            if pd.api.types.is_numeric_dtype(data):
                # 수치형 데이터 시각화
                
                # 각 서브플롯에 테마 적용
                for ax in axes.flat:
                    if self.is_dark_mode:
                        ax.set_facecolor('#2B2B2B')
                        ax.tick_params(colors=text_color, labelsize=8)
                        ax.spines['bottom'].set_color(text_color)
                        ax.spines['top'].set_color(text_color)
                        ax.spines['right'].set_color(text_color)
                        ax.spines['left'].set_color(text_color)
                        ax.grid(True, color=grid_color, alpha=0.3)
                    else:
                        ax.tick_params(labelsize=8)
                        ax.grid(True, alpha=0.3)
                
                # 1. 히스토그램
                axes[0, 0].hist(data, bins=20, alpha=0.7, color=chart_colors[0], edgecolor=text_color)
                axes[0, 0].set_title('Histogram', fontsize=10, color=text_color)
                
                # 2. 박스플롯
                bp = axes[0, 1].boxplot(data, patch_artist=True)
                bp['boxes'][0].set_facecolor(chart_colors[0])
                bp['boxes'][0].set_alpha(0.7)
                axes[0, 1].set_title('Box Plot', fontsize=10, color=text_color)
                
                # 3. 라인 플롯 (인덱스별)
                sample_data = data.head(100)
                axes[1, 0].plot(sample_data.index, sample_data.values, marker='o', markersize=2, alpha=0.7, color=chart_colors[0])
                axes[1, 0].set_title('Line Plot (First 100)', fontsize=10, color=text_color)
                
                # 4. 기술통계
                stats_text = f"Mean: {data.mean():.2f}\nMedian: {data.median():.2f}\nStd: {data.std():.2f}\nMin: {data.min():.2f}\nMax: {data.max():.2f}"
                axes[1, 1].text(0.1, 0.5, stats_text, transform=axes[1, 1].transAxes, fontsize=9, 
                               verticalalignment='center', color=text_color)
                axes[1, 1].set_title('Statistics', fontsize=10, color=text_color)
                axes[1, 1].axis('off')
                if self.is_dark_mode:
                    axes[1, 1].set_facecolor('#2B2B2B')
                
            else:
                # 범주형 데이터 시각화
                value_counts = data.value_counts().head(10)
                
                # 각 서브플롯에 테마 적용
                for ax in axes.flat:
                    if self.is_dark_mode:
                        ax.set_facecolor('#2B2B2B')
                        ax.tick_params(colors=text_color, labelsize=8)
                        ax.spines['bottom'].set_color(text_color)
                        ax.spines['top'].set_color(text_color)
                        ax.spines['right'].set_color(text_color)
                        ax.spines['left'].set_color(text_color)
                        ax.grid(True, color=grid_color, alpha=0.3)
                    else:
                        ax.tick_params(labelsize=8)
                        ax.grid(True, alpha=0.3)
                
                # 1. 막대 그래프
                axes[0, 0].bar(range(len(value_counts)), value_counts.values, color=chart_colors[1])
                axes[0, 0].set_title('Value Counts', fontsize=10, color=text_color)
                
                # 2. 파이 차트
                if len(value_counts) > 0:
                    wedges, texts, autotexts = axes[0, 1].pie(value_counts.values, labels=value_counts.index, 
                                                             autopct='%1.1f%%', startangle=90, colors=chart_colors)
                    # 파이 차트 텍스트 색상 조정
                    for text in texts:
                        text.set_color(text_color)
                    for autotext in autotexts:
                        autotext.set_color('#FFFFFF' if self.is_dark_mode else '#000000')
                    axes[0, 1].set_title('Distribution', fontsize=10, color=text_color)
                
                # 3. 수평 막대
                axes[1, 0].barh(range(len(value_counts)), value_counts.values, color=chart_colors[2])
                axes[1, 0].set_title('Horizontal Bar', fontsize=10, color=text_color)
                
                # 4. 통계
                stats_text = f"Unique: {data.nunique()}\nMost frequent: {data.mode().iloc[0] if len(data.mode()) > 0 else 'N/A'}\nTotal: {len(data)}"
                axes[1, 1].text(0.1, 0.5, stats_text, transform=axes[1, 1].transAxes, fontsize=9, 
                               verticalalignment='center', color=text_color)
                axes[1, 1].set_title('Info', fontsize=10, color=text_color)
                axes[1, 1].axis('off')
                if self.is_dark_mode:
                    axes[1, 1].set_facecolor('#2B2B2B')
            
            plt.tight_layout()
            
            # tkinter에 matplotlib 캔버스 추가
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
        control_frame = tk.Frame(slicer_frame, bg=self.current_theme['panel_bg'])
        control_frame.pack(fill='x', padx=10, pady=10)

        # 제목
        title_label = tk.Label(control_frame, text="CSV Data Slicer", 
                              font=('Arial', 12, 'bold'), 
                              bg=self.current_theme['panel_bg'], 
                              fg=self.current_theme['text_color'])
        title_label.pack(anchor='w', pady=(0, 10))

        # 행 범위 설정
        row_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        row_frame.pack(fill='x', pady=5)

        tk.Label(row_frame, text="Row Range:", font=('Arial', 10, 'bold'), 
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color']).pack(side='left')
        tk.Label(row_frame, text="From:", bg=self.current_theme['panel_bg'], 
                fg=self.current_theme['text_color']).pack(side='left', padx=(10, 5))
        self.row_start_var = tk.StringVar(value="1")
        start_entry = tk.Entry(row_frame, textvariable=self.row_start_var, width=10,
                              bg=self.current_theme['entry_bg'], fg=self.current_theme['text_color'],
                              insertbackground=self.current_theme['text_color'])
        start_entry.pack(side='left', padx=(0, 10))
        
        tk.Label(row_frame, text="To:", bg=self.current_theme['panel_bg'], 
                fg=self.current_theme['text_color']).pack(side='left', padx=(0, 5))
        self.row_end_var = tk.StringVar(value="1000")
        end_entry = tk.Entry(row_frame, textvariable=self.row_end_var, width=10,
                            bg=self.current_theme['entry_bg'], fg=self.current_theme['text_color'],
                            insertbackground=self.current_theme['text_color'])
        end_entry.pack(side='left')

        # 컬럼 선택
        col_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        col_frame.pack(fill='x', pady=5)

        tk.Label(col_frame, text="Columns:", font=('Arial', 10, 'bold'), 
                bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color']).pack(side='left')
        
        # 컬럼 선택 프레임
        self.column_selection_frame = tk.Frame(col_frame, bg=self.current_theme['panel_bg'])
        self.column_selection_frame.pack(side='left', padx=(10, 0))

        # 버튼 영역
        button_frame = tk.Frame(control_frame, bg=self.current_theme['panel_bg'])
        button_frame.pack(fill='x', pady=10)

        slice_btn = self.create_styled_button(button_frame, "Apply Slice", 
                                             self.apply_slice, '#27AE60')
        slice_btn.pack(side='left', padx=(0, 10))

        export_btn = self.create_styled_button(button_frame, "Export Sliced Data", 
                                              self.export_sliced_data, '#F39C12')
        export_btn.pack(side='left')

        # 슬라이싱 결과 영역
        result_frame = tk.Frame(slicer_frame, bg=self.current_theme['panel_bg'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 결과 테이블
        self.slice_tree_container = tk.Frame(result_frame, bg=self.current_theme['panel_bg'])
        self.slice_tree_container.pack(fill=tk.BOTH, expand=True)

        # 슬라이싱된 데이터용 Treeview
        self.slice_tree = ttk.Treeview(self.slice_tree_container, show='tree headings', height=15)
        
        # 스크롤바
        slice_v_scrollbar = ttk.Scrollbar(self.slice_tree_container, orient=tk.VERTICAL, command=self.slice_tree.yview)
        slice_h_scrollbar = ttk.Scrollbar(self.slice_tree_container, orient=tk.HORIZONTAL, command=self.slice_tree.xview)
        
        self.slice_tree.configure(yscrollcommand=slice_v_scrollbar.set, xscrollcommand=slice_h_scrollbar.set)
        
        # 그리드 배치
        self.slice_tree.grid(row=0, column=0, sticky='nsew')
        slice_v_scrollbar.grid(row=0, column=1, sticky='ns')
        slice_h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.slice_tree_container.grid_rowconfigure(0, weight=1)
        self.slice_tree_container.grid_columnconfigure(0, weight=1)

    def update_column_checkboxes(self):
        """컬럼 체크박스 업데이트"""
        for widget in self.column_selection_frame.winfo_children():
            widget.destroy()

        if self.state.df is not None:
            self.column_vars = {}
            columns = list(self.state.df.columns)
            
            # 전체 선택/해제 버튼
            select_frame = tk.Frame(self.column_selection_frame, bg=self.current_theme['panel_bg'])
            select_frame.pack(fill='x', pady=(0, 5))
            
            tk.Button(select_frame, text="All", font=('Arial', 8), 
                     command=self.select_all_columns).pack(side='left', padx=(0, 5))
            tk.Button(select_frame, text="None", font=('Arial', 8), 
                     command=self.deselect_all_columns).pack(side='left')

            # 컬럼별 체크박스 (최대 10개만 표시)
            for col in columns[:10]:
                var = tk.BooleanVar(value=True)
                self.column_vars[col] = var
                cb = tk.Checkbutton(self.column_selection_frame, text=col[:15], variable=var, 
                                   bg=self.current_theme['panel_bg'], fg=self.current_theme['text_color'], 
                                   font=('Arial', 8), selectcolor=self.current_theme['entry_bg'])
                cb.pack(anchor='w')

    def select_all_columns(self):
        if hasattr(self, 'column_vars'):
            for var in self.column_vars.values():
                var.set(True)

    def deselect_all_columns(self):
        if hasattr(self, 'column_vars'):
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
            
            if start_row < 0: start_row = 0
            if end_row > len(self.state.df): end_row = len(self.state.df)
            
            selected_columns = []
            if hasattr(self, 'column_vars'):
                for col, var in self.column_vars.items():
                    if var.get():
                        selected_columns.append(col)
            
            if not selected_columns:
                selected_columns = list(self.state.df.columns)

            sliced_data = self.state.df.iloc[start_row:end_row][selected_columns]
            self.current_sliced_data = sliced_data
            self.update_slice_table(sliced_data)
            
            self.show_toast(f"Sliced: {len(sliced_data)} rows, {len(selected_columns)} cols", "success")

        except Exception as e:
            self.show_toast(f"Failed to slice: {e}", "error")

    def update_slice_table(self, data):
        """슬라이싱 결과 테이블 업데이트"""
        for item in self.slice_tree.get_children():
            self.slice_tree.delete(item)

        if data is None or data.empty:
            return

        columns = list(data.columns)
        self.slice_tree['columns'] = columns
        self.slice_tree['show'] = 'tree headings'
        
        self.slice_tree.heading('#0', text='Index', anchor='w')
        self.slice_tree.column('#0', width=60, anchor='w')

        for col in columns:
            self.slice_tree.heading(col, text=col, anchor='w')
            self.slice_tree.column(col, width=100, anchor='w')

        display_data = data.head(500)
        for idx, row in display_data.iterrows():
            values = [str(val)[:30] + ('...' if len(str(val)) > 30 else '') for val in row]
            self.slice_tree.insert('', 'end', text=str(idx), values=values)

    def export_sliced_data(self):
        """슬라이싱된 데이터 내보내기"""
        if not hasattr(self, 'current_sliced_data'):
            self.show_toast("No sliced data to export", "error")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save sliced data"
            )
            
            if file_path:
                self.current_sliced_data.to_csv(file_path, index=True)
                self.show_toast(f"Exported to {file_path}", "success")
                
        except Exception as e:
            self.show_toast(f"Export failed: {e}", "error")

    def display_data_paginated(self, df: pd.DataFrame, page: int = 0, page_size: int = 1000):
        """페이지네이션으로 대용량 데이터 효율적 표시"""
        if df is None or df.empty:
            return
        
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(df))
        
        # 현재 페이지 데이터만 표시
        page_data = df.iloc[start_idx:end_idx]
        
        # 캐시 키 생성
        cache_key = f"page_{page}_{page_size}_{hash(str(df.columns.tolist()))}"
        cached_data = self.data_cache.get(cache_key)
        
        if cached_data is not None:
            # 캐시된 데이터 사용
            display_data = cached_data
        else:
            # 새로 처리 및 캐시에 저장
            display_data = page_data.copy()
            self.data_cache.set(cache_key, display_data)
        
        # Treeview 업데이트 (기존 데이터 클리어 후 추가)
        if hasattr(self, 'preview_tree'):
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            
            # 컬럼 헤더 설정 (최초 1회만)
            if not self.preview_tree.get_children():
                self.preview_tree['columns'] = list(display_data.columns)
                for col in display_data.columns:
                    self.preview_tree.heading(col, text=col)
                    self.preview_tree.column(col, width=min(150, len(str(col)) * 10))
            
            # 데이터 행 추가 (최적화된 방식)
            for idx, row in display_data.iterrows():
                values = []
                for val in row:
                    if isinstance(val, float):
                        values.append(f"{val:.2f}")
                    elif pd.isna(val):
                        values.append("")
                    else:
                        values.append(str(val))
                self.preview_tree.insert('', 'end', values=values)
            
            # 페이지 정보 업데이트
            if hasattr(self, 'row_count_label'):
                total_rows = len(df)
                self.row_count_label.config(
                    text=f"Rows: {start_idx + 1}-{end_idx} of {total_rows:,}"
                )

    def animate_spinner_optimized(self):
        """최적화된 스피너 애니메이션"""
        if not hasattr(self, '_spinner_active'):
            self._spinner_active = False
        
        if not self._spinner_active:
            return
        
        if hasattr(self, 'spinner_label') and self.spinner_label.winfo_exists():
            current = self.spinner_label.cget('text')
            # 더 부드러운 애니메이션 패턴
            patterns = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            current_idx = patterns.index(current) if current in patterns else 0
            next_pattern = patterns[(current_idx + 1) % len(patterns)]
            self.spinner_label.config(text=next_pattern)
        
        # 100ms 간격으로 최적화 (기존 50ms에서 증가)
        self.root.after(100, self.animate_spinner_optimized)

    def start_spinner(self):
        """스피너 시작"""
        self._spinner_active = True
        if hasattr(self, 'spinner_label'):
            self.spinner_label.config(text='⠋')
        self.animate_spinner_optimized()

    def stop_spinner(self):
        """스피너 정지"""
        self._spinner_active = False
        if hasattr(self, 'spinner_label'):
            self.spinner_label.config(text='')

    def show_toast(self, message: str, kind: str = "info"):
        """토스트 메시지 표시"""
        # 간단한 메시지 박스로 대체
        if kind == "error":
            messagebox.showerror("Error", message)
        elif kind == "success" or kind == "ok":
            messagebox.showinfo("Success", message)
        else:
            messagebox.showinfo("Info", message)

def main():
    root = tk.Tk()
    app = CSVAnalyzerApp(root)
    
    # 윈도우 닫기 이벤트
    def on_closing():
        if app.busy_after_id:
            root.after_cancel(app.busy_after_id)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()