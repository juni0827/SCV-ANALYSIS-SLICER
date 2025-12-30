from __future__ import annotations
import io
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import dearpygui.dearpygui as dpg
import pandas as pd
import seaborn as sns
from scipy import stats
import textwrap

# Enhanced color palettes for better visual appeal
DARK_COLORS = {
    'primary': '#4ECDC4',
    'secondary': '#FF6B6B', 
    'accent': '#45B7D1',
    'success': '#96CEB4',
    'warning': '#FFEAA7',
    'info': '#74B9FF',
    'light': '#DDA0DD',
    'muted': '#B19CD9'
}

DARK_PALETTE = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98', '#F0E68C']
CATEGORICAL_PALETTE = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98', '#87CEEB']

def _smart_label_formatter(text, width=12, max_lines=2):
    """
    Smartly formats text for labels:
    1. Wraps text to specified width
    2. Truncates if exceeds max_lines
    """
    text = str(text)
    if len(text) <= width:
        return text
        
    wrapped = textwrap.wrap(text, width=width)
    if len(wrapped) > max_lines:
        # Join first (max_lines-1) lines and add the last line truncated with ...
        return "\n".join(wrapped[:max_lines-1] + [wrapped[max_lines-1][:width-3] + "..."])
    return "\n".join(wrapped)

def _apply_dark_theme_to_axis(ax, title=None):
    """Apply consistent dark theme styling to a matplotlib axis"""
    ax.set_facecolor("#1a1a1a")
    if title:
        ax.set_title(title, fontsize=11, color='#CCCCCC', fontweight='bold')
    ax.tick_params(colors='#CCCCCC', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#CCCCCC')
        spine.set_alpha(0.3)
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)

def _finalize_fig_to_texture(fig, texture_tag: str, parent_tag: str, width: int = 860, height: int = 320):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    w, h = img.size
    data = np.frombuffer(img.tobytes(), dtype=np.uint8) / 255.0
    if dpg.does_item_exist(texture_tag):
        dpg.delete_item(texture_tag)
    with dpg.texture_registry():
        dpg.add_static_texture(w, h, data, tag=texture_tag)
    dpg.delete_item(parent_tag, children_only=True)
    dpg.add_image(texture_tag, width=width, height=height, parent=parent_tag)

def plot_quick_distribution(df: pd.DataFrame, numeric_col: str, texture_tag: str, parent_tag: str):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#1a1a1a")
    _apply_dark_theme_to_axis(ax, f"{numeric_col} Distribution")
    
    ax.hist(df[numeric_col].dropna(), bins=30, alpha=0.8, color=DARK_COLORS['primary'], 
            edgecolor=DARK_COLORS['accent'], linewidth=0.5)
    
    _finalize_fig_to_texture(fig, texture_tag, parent_tag, width=880, height=220)

def plot_generic(df: pd.DataFrame, column: str, plot_type: str, texture_tag: str, parent_tag: str):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    _apply_dark_theme_to_axis(ax, f"{plot_type}: {column}")

    if plot_type == "Histogram":
        ax.hist(df[column].dropna(), bins=30, alpha=0.8, color=DARK_COLORS['primary'], 
                edgecolor=DARK_COLORS['accent'], linewidth=0.5)
    elif plot_type == "Box Plot":
        bp = ax.boxplot(df[column].dropna().values, vert=True, labels=[column], patch_artist=True)
        bp['boxes'][0].set_facecolor(DARK_COLORS['secondary'])
        bp['boxes'][0].set_alpha(0.7)
        for element in ['whiskers', 'fliers', 'medians', 'caps']:
            plt.setp(bp[element], color=DARK_COLORS['accent'])
    elif plot_type == "Scatter Plot":
        ax.scatter(range(len(df[column])), df[column], alpha=0.6, color=DARK_COLORS['primary'], s=20)
    elif plot_type == "Line":
        ax.plot(df[column].values, color=DARK_COLORS['accent'], linewidth=2, alpha=0.8)
    elif plot_type == "ECDF":
        vals = pd.Series(df[column]).dropna().sort_values().values
        y = np.linspace(0, 1, len(vals), endpoint=True)
        ax.step(vals, y, where="post", color=DARK_COLORS['info'], linewidth=2)
    elif plot_type == "Violin":
        data_clean = df[column].dropna()
        if pd.api.types.is_numeric_dtype(data_clean):
            parts = ax.violinplot([data_clean.values], positions=[1], showmeans=True, showmedians=True)
            for pc in parts['bodies']:
                pc.set_facecolor(DARK_COLORS['success'])
                pc.set_alpha(0.7)
            ax.set_xticks([1])
            ax.set_xticklabels([column])
        else:
            ax.text(0.5, 0.5, "Violin plot requires numeric data", ha="center", va="center", color='#CCCCCC')
    elif plot_type == "Density":
        data_clean = df[column].dropna()
        if pd.api.types.is_numeric_dtype(data_clean):
            data_clean.plot.density(ax=ax, alpha=0.8, color=DARK_COLORS['warning'], linewidth=2)
        else:
            ax.text(0.5, 0.5, "Density plot requires numeric data", ha="center", va="center", color='#CCCCCC')
    elif plot_type == "QQ Plot":
        data_clean = df[column].dropna()
        if pd.api.types.is_numeric_dtype(data_clean):
            stats.probplot(data_clean, dist="norm", plot=ax)
            ax.get_lines()[0].set_markerfacecolor(DARK_COLORS['secondary'])
            ax.get_lines()[0].set_markeredgecolor(DARK_COLORS['accent'])
            ax.get_lines()[1].set_color(DARK_COLORS['primary'])
        else:
            ax.text(0.5, 0.5, "Q-Q plot requires numeric data", ha="center", va="center", color='#CCCCCC')
    elif plot_type == "Ridge":
        data_clean = df[column].dropna()
        if pd.api.types.is_numeric_dtype(data_clean):
            data_clean.plot.density(ax=ax, alpha=0.7, color=DARK_COLORS['light'], linewidth=2)
            ax.fill_between(ax.get_lines()[-1].get_xdata(), ax.get_lines()[-1].get_ydata(), 
                           alpha=0.4, color=DARK_COLORS['light'])
        else:
            ax.text(0.5, 0.5, "Ridge plot requires numeric data", ha="center", va="center", color='#CCCCCC')
    else:
        ax.text(0.5, 0.5, f"Unsupported plot: {plot_type}", ha="center", va="center", color='#FF6B6B')

    _finalize_fig_to_texture(fig, texture_tag, parent_tag)

# --- 추가: combinations add-on helpers (병합) ---

def plot_bar_topk(df: pd.DataFrame, col: str, k: int = 20, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,5), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    vc = df[col].astype("object").value_counts(dropna=False).head(k)
    vc.plot(kind="bar", ax=ax)
    ax.set_title(f"Top-{k} values of {col}")
    
    # Smart label formatting
    labels = [_smart_label_formatter(x) for x in vc.index]
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    
    for side in ("top","right"): ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=360)

def plot_hist_ecdf(df: pd.DataFrame, col: str, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,5), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    ax.hist(s, bins=30, alpha=0.7)
    ax2 = ax.twinx()
    s_sorted = s.sort_values().values
    y = np.linspace(0,1,len(s_sorted), endpoint=True)
    ax2.plot(s_sorted, y, alpha=0.9)
    ax.set_title(f"Histogram + ECDF: {col}")
    for side in ("top","right"): ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=360)

def plot_heatmap_crosstab(df: pd.DataFrame, col_a: str, col_b: str, metric: str = "lift", max_levels: int = 30, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,6), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    a = df[col_a].astype("object"); b = df[col_b].astype("object")
    top_a = a.value_counts().head(max_levels).index
    top_b = b.value_counts().head(max_levels).index
    a = a.where(a.isin(top_a)); b = b.where(b.isin(top_b))
    ct = pd.crosstab(a,b).fillna(0)
    if ct.size == 0:
        ax.text(0.5,0.5,"No data", ha="center", va="center"); _finalize_fig_to_texture(fig, "hist_tex", parent_tag); return
    if metric == "lift":
        total = ct.values.sum()
        px = ct.sum(axis=1)/total; py = ct.sum(axis=0)/total
        exp = np.outer(px.values, py.values) * total
        mat = ct.values / np.maximum(exp, 1e-9)
        im = ax.imshow(mat, aspect="auto")
        ax.set_title(f"Lift heatmap: {col_a} × {col_b}")
    else:
        im = ax.imshow(ct.values, aspect="auto")
        ax.set_title(f"Count heatmap: {col_a} × {col_b}")
    ax.set_xticks(range(min(len(ct.columns), max_levels)))
    ax.set_yticks(range(min(len(ct.index), max_levels)))
    
    # Smart label formatting for heatmap
    x_labels = [_smart_label_formatter(x, width=10) for x in ct.columns]
    y_labels = [_smart_label_formatter(y, width=10) for y in ct.index]
    
    ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(y_labels, fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)

def plot_scatter_corr(df: pd.DataFrame, x: str, y: str, log: bool = False, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,6), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    xs = pd.to_numeric(df[x], errors="coerce")
    ys = pd.to_numeric(df[y], errors="coerce")
    s = pd.concat([xs,ys], axis=1).dropna()
    if log:
        s = s[(s[x] > 0) & (s[y] > 0)]
        ax.set_xscale("log"); ax.set_yscale("log")
    if len(s) > 200000:
        hb = ax.hexbin(s[x].values, s[y].values, gridsize=40)
        fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
    else:
        ax.scatter(s[x].values, s[y].values, alpha=0.4)
    ax.set_title(f"Scatter: {x} vs {y}")
    for side in ("top","right"): ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)

def plot_box_group(df: pd.DataFrame, cat: str, num: str, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,6), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    s = df[[cat, num]].dropna()
    if s[cat].nunique() > 30:
        top = s[cat].value_counts().head(15).index
        s = s[s[cat].isin(top)]
    s.boxplot(column=num, by=cat, ax=ax, rot=45)
    ax.set_title(f"{num} by {cat}"); ax.figure.suptitle("")
    for side in ("top","right"): ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)

def plot_corr_heatmap(df: pd.DataFrame, num_cols, top_k: int = 20, method: str = "pearson", parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,8), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    data = df[num_cols].select_dtypes(include="number").copy()
    corr = data.corr(method=method)
    tri = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool))
    pairs = tri.unstack().dropna().abs().sort_values(ascending=False)
    keep = set()
    for (a,b), _ in pairs.head(top_k).items():
        keep.add(a); keep.add(b)
    sel = sorted(list(keep))
    c = corr.loc[sel, sel]
    im = ax.imshow(c.values, aspect="auto")
    ax.set_xticks(range(len(sel)))
    ax.set_yticks(range(len(sel)))
    
    # Smart label formatting for correlation heatmap
    labels = [_smart_label_formatter(x, width=10) for x in sel]
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    
    ax.set_title(f"{method.title()} correlation (top pairs)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=500)

# --- New Advanced Visualization Functions ---

def plot_regression_with_ci(df: pd.DataFrame, x_col: str, y_col: str, parent_tag: str = "plot_canvas"):
    """Create a regression plot with confidence interval"""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    
    # Clean data
    x = pd.to_numeric(df[x_col], errors='coerce')
    y = pd.to_numeric(df[y_col], errors='coerce')
    clean_data = pd.concat([x, y], axis=1).dropna()
    
    if len(clean_data) < 3:
        _apply_dark_theme_to_axis(ax, "Insufficient Data for Regression")
        ax.text(0.5, 0.5, "Insufficient numeric data for regression", ha="center", va="center", color='#CCCCCC')
    else:
        # Use seaborn for better regression plot with custom colors
        sns.regplot(data=clean_data, x=x_col, y=y_col, ax=ax, 
                   scatter_kws={'alpha': 0.6, 'color': DARK_COLORS['primary'], 's': 25}, 
                   line_kws={'color': DARK_COLORS['secondary'], 'linewidth': 2})
        
        # Calculate correlation
        corr = clean_data[x_col].corr(clean_data[y_col])
        _apply_dark_theme_to_axis(ax, f"Regression: {x_col} vs {y_col} (r={corr:.3f})")
        
        # Add correlation text box
        ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK_COLORS['accent'], alpha=0.7),
                color='white', fontweight='bold')
    
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)

def plot_distribution_comparison(df: pd.DataFrame, col: str, group_col: str = None, parent_tag: str = "plot_canvas"):
    """Compare distributions across groups or show enhanced single distribution"""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    
    data = pd.to_numeric(df[col], errors='coerce').dropna()
    
    if group_col and group_col in df.columns:
        # Group comparison
        _apply_dark_theme_to_axis(ax, f"Distribution of {col} by {group_col}")
        grouped_data = df.groupby(group_col)[col].apply(lambda x: pd.to_numeric(x, errors='coerce').dropna())
        
        for i, (group, group_data) in enumerate(grouped_data.head(5).items()):
            if len(group_data) > 0:
                group_data.plot.density(ax=ax, alpha=0.7, label=str(group), 
                                       color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)], linewidth=2)
        ax.legend(framealpha=0.9, facecolor='#2a2a2a', edgecolor='#CCCCCC')
    else:
        # Enhanced single distribution with statistical overlays
        _apply_dark_theme_to_axis(ax, f"Enhanced Distribution: {col}")
        data.plot.density(ax=ax, alpha=0.8, color=DARK_COLORS['primary'], linewidth=3)
        
        # Add statistical lines
        mean_val = data.mean()
        median_val = data.median()
        ax.axvline(mean_val, color=DARK_COLORS['secondary'], linestyle='--', alpha=0.8, 
                  linewidth=2, label=f'Mean: {mean_val:.2f}')
        ax.axvline(median_val, color=DARK_COLORS['warning'], linestyle='--', alpha=0.8, 
                  linewidth=2, label=f'Median: {median_val:.2f}')
        
        # Add quartiles
        q25, q75 = data.quantile([0.25, 0.75])
        ax.axvline(q25, color=DARK_COLORS['muted'], linestyle=':', alpha=0.7, 
                  linewidth=1.5, label=f'Q1: {q25:.2f}')
        ax.axvline(q75, color=DARK_COLORS['muted'], linestyle=':', alpha=0.7, 
                  linewidth=1.5, label=f'Q3: {q75:.2f}')
        
        ax.legend(framealpha=0.9, facecolor='#2a2a2a', edgecolor='#CCCCCC')
    
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)

def plot_pair_correlation(df: pd.DataFrame, columns: list = None, max_cols: int = 6, parent_tag: str = "plot_canvas"):
    """Create a correlation pair plot matrix for numeric columns"""
    plt.style.use("dark_background")
    
    # Select numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if columns:
        numeric_df = numeric_df[columns[:max_cols]]
    else:
        numeric_df = numeric_df.iloc[:, :max_cols]
    
    if numeric_df.shape[1] < 2:
        fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
        ax.set_facecolor("#1a1a1a")
        ax.text(0.5, 0.5, "Need at least 2 numeric columns for pair plot", ha="center", va="center")
        _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=420)
        return
    
    n_cols = len(numeric_df.columns)
    fig, axes = plt.subplots(n_cols, n_cols, figsize=(12, 10), facecolor="#1a1a1a")
    
    for i, col1 in enumerate(numeric_df.columns):
        for j, col2 in enumerate(numeric_df.columns):
            ax = axes[i, j] if n_cols > 1 else axes
            ax.set_facecolor("#1a1a1a")
            
            if i == j:
                # Diagonal: histogram
                ax.hist(numeric_df[col1].dropna(), bins=20, alpha=0.7, color='#4ECDC4')
                ax.set_title(col1, fontsize=8)
            elif i < j:
                # Upper triangle: scatter with correlation
                clean_data = numeric_df[[col1, col2]].dropna()
                if len(clean_data) > 1:
                    ax.scatter(clean_data[col2], clean_data[col1], alpha=0.6, s=10, color='#FF6B6B')
                    corr = clean_data[col1].corr(clean_data[col2])
                    ax.text(0.05, 0.95, f'r={corr:.2f}', transform=ax.transAxes, fontsize=8)
            else:
                # Lower triangle: correlation value
                corr = numeric_df[col1].corr(numeric_df[col2])
                ax.text(0.5, 0.5, f'{corr:.3f}', ha='center', va='center', fontsize=14,
                       color='#4ECDC4' if abs(corr) > 0.5 else '#FFFFFF')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
            
            ax.tick_params(labelsize=6)
            for side in ("top", "right"): 
                ax.spines[side].set_visible(False)
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=720)

def plot_time_series_decomposition(df: pd.DataFrame, date_col: str, value_col: str, parent_tag: str = "plot_canvas"):
    """Create time series visualization with trend analysis"""
    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#1a1a1a")
    
    # Convert to datetime
    try:
        dates = pd.to_datetime(df[date_col])
        values = pd.to_numeric(df[value_col], errors='coerce')
        ts_data = pd.Series(values.values, index=dates).dropna().sort_index()
        
        if len(ts_data) < 3:
            axes[0, 0].text(0.5, 0.5, "Insufficient time series data", ha="center", va="center")
            _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=600)
            return
        
        # 1. Original time series
        axes[0, 0].plot(ts_data.index, ts_data.values, color='#4ECDC4', alpha=0.8)
        axes[0, 0].set_title("Time Series", fontsize=10)
        axes[0, 0].set_facecolor("#1a1a1a")
        
        # 2. Rolling statistics
        if len(ts_data) > 10:
            window = max(3, len(ts_data) // 10)
            rolling_mean = ts_data.rolling(window=window).mean()
            rolling_std = ts_data.rolling(window=window).std()
            
            axes[0, 1].plot(ts_data.index, rolling_mean, color='#FF6B6B', label=f'Rolling Mean (w={window})')
            axes[0, 1].plot(ts_data.index, rolling_std, color='#FFEAA7', label=f'Rolling Std (w={window})')
            axes[0, 1].legend(fontsize=8)
        axes[0, 1].set_title("Rolling Statistics", fontsize=10)
        axes[0, 1].set_facecolor("#1a1a1a")
        
        # 3. Distribution
        axes[1, 0].hist(ts_data.values, bins=20, alpha=0.7, color='#96CEB4')
        axes[1, 0].set_title("Value Distribution", fontsize=10)
        axes[1, 0].set_facecolor("#1a1a1a")
        
        # 4. Autocorrelation (simplified)
        if len(ts_data) > 20:
            # Limit autocorrelation computation for very large time series
            if len(ts_data) > 5000:
                axes[1, 1].text(0.5, 0.5, "Autocorrelation skipped for large time series", ha="center", va="center", fontsize=9)
            else:
                lags = range(1, min(21, len(ts_data)//2))
                try:
                    autocorrs = [ts_data.autocorr(lag=lag) for lag in lags]
                    axes[1, 1].bar(lags, autocorrs, alpha=0.7, color='#B19CD9')
                    axes[1, 1].axhline(y=0, color='white', linestyle='-', alpha=0.3)
                except Exception as acorr_err:
                    axes[1, 1].text(0.5, 0.5, f"Autocorrelation error:\n{acorr_err}", ha="center", va="center", fontsize=9)
        axes[1, 1].set_title("Autocorrelation", fontsize=10)
        axes[1, 1].set_facecolor("#1a1a1a")
        
        for ax in axes.flat:
            ax.tick_params(labelsize=8)
            for side in ("top", "right"): 
                ax.spines[side].set_visible(False)
        
    except Exception as e:
        axes[0, 0].text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=600)

# --- Advanced Visualization Functions (사용자 요청 기능) ---

def plot_scalar_field(df: pd.DataFrame, x_col: str, y_col: str, z_col: str, parent_tag: str = "plot_canvas"):
    """Create a scalar field visualization using contour plots"""
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="#1a1a1a")
    
    try:
        # Clean and prepare data
        x = pd.to_numeric(df[x_col], errors='coerce')
        y = pd.to_numeric(df[y_col], errors='coerce')
        z = pd.to_numeric(df[z_col], errors='coerce')
        
        clean_data = pd.concat([x, y, z], axis=1).dropna()
        
        if len(clean_data) < 10:
            axes[0].text(0.5, 0.5, "Insufficient data for scalar field", ha="center", va="center", color='#CCCCCC')
            _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=1120, height=420)
            return
        
        # Create grid for interpolation
        x_vals = clean_data[x_col].values
        y_vals = clean_data[y_col].values
        z_vals = clean_data[z_col].values
        
        # Create meshgrid for contour
        xi = np.linspace(x_vals.min(), x_vals.max(), 100)
        yi = np.linspace(y_vals.min(), y_vals.max(), 100)
        XI, YI = np.meshgrid(xi, yi)
        
        # Interpolate Z values
        from scipy.interpolate import griddata
        ZI = griddata((x_vals, y_vals), z_vals, (XI, YI), method='linear')
        
        # 1. Contour plot
        cs = axes[0].contourf(XI, YI, ZI, levels=20, cmap='viridis', alpha=0.8)
        axes[0].scatter(x_vals, y_vals, c=z_vals, s=20, edgecolor='white', alpha=0.6, cmap='viridis')
        axes[0].set_xlabel(x_col)
        axes[0].set_ylabel(y_col)
        axes[0].set_title(f"Scalar Field: {z_col}")
        axes[0].set_facecolor("#1a1a1a")
        fig.colorbar(cs, ax=axes[0], fraction=0.046, pad=0.04)
        
        # 2. Contour lines
        cs2 = axes[1].contour(XI, YI, ZI, levels=10, colors='white', alpha=0.7)
        axes[1].clabel(cs2, inline=True, fontsize=8, colors='white')
        axes[1].scatter(x_vals, y_vals, c=z_vals, s=30, edgecolor='white', alpha=0.8, cmap='viridis')
        axes[1].set_xlabel(x_col)
        axes[1].set_ylabel(y_col)
        axes[1].set_title(f"Contour Lines: {z_col}")
        axes[1].set_facecolor("#1a1a1a")
        
        for ax in axes:
            ax.tick_params(colors='#CCCCCC', labelsize=9)
            for spine in ax.spines.values():
                spine.set_color('#CCCCCC')
                spine.set_alpha(0.3)
            ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
    
    except Exception as e:
        axes[0].text(0.5, 0.5, f"Error creating scalar field:\n{str(e)}", ha="center", va="center", color='#FF6B6B')
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=1120, height=420)

def plot_gradient_field(df: pd.DataFrame, x_col: str, y_col: str, u_col: str, v_col: str, parent_tag: str = "plot_canvas"):
    """Create a gradient/vector field visualization"""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1a1a1a")
    
    try:
        # Clean and prepare data
        x = pd.to_numeric(df[x_col], errors='coerce')
        y = pd.to_numeric(df[y_col], errors='coerce')
        u = pd.to_numeric(df[u_col], errors='coerce')
        v = pd.to_numeric(df[v_col], errors='coerce')
        
        clean_data = pd.concat([x, y, u, v], axis=1).dropna()
        
        if len(clean_data) < 5:
            ax.text(0.5, 0.5, "Insufficient data for gradient field", ha="center", va="center", color='#CCCCCC')
            _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=600)
            return
        
        # Create quiver plot
        x_vals = clean_data[x_col].values
        y_vals = clean_data[y_col].values
        u_vals = clean_data[u_col].values
        v_vals = clean_data[v_col].values
        
        # Normalize vectors for better visualization
        magnitude = np.sqrt(u_vals**2 + v_vals**2)
        max_magnitude = np.max(magnitude)
        if max_magnitude > 0:
            u_norm = u_vals / max_magnitude
            v_norm = v_vals / max_magnitude
        else:
            u_norm, v_norm = u_vals, v_vals
        
        # Create the quiver plot
        Q = ax.quiver(x_vals, y_vals, u_norm, v_norm, magnitude, 
                     scale=30, scale_units='xy', angles='xy', 
                     cmap='plasma', alpha=0.8, width=0.005)
        
        # Add colorbar
        cbar = fig.colorbar(Q, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Magnitude', color='#CCCCCC')
        cbar.ax.yaxis.set_tick_params(color='#CCCCCC')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#CCCCCC')
        
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f"Gradient Field: {u_col} × {v_col}")
        ax.set_facecolor("#1a1a1a")
        
        # Styling
        ax.tick_params(colors='#CCCCCC', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#CCCCCC')
            spine.set_alpha(0.3)
        ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Add magnitude statistics
        mean_mag = np.mean(magnitude)
        max_mag = np.max(magnitude)
        ax.text(0.02, 0.98, f'Mean Magnitude: {mean_mag:.2f}\nMax Magnitude: {max_mag:.2f}', 
                transform=ax.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#2a2a2a', alpha=0.8),
                color='#CCCCCC')
    
    except Exception as e:
        ax.text(0.5, 0.5, f"Error creating gradient field:\n{str(e)}", ha="center", va="center", color='#FF6B6B')
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=600)

def plot_enhanced_scatter(df: pd.DataFrame, x_col: str, y_col: str, size_col: str = None, color_col: str = None, parent_tag: str = "plot_canvas"):
    """Create an enhanced scatter plot with size and color encoding"""
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="#1a1a1a")
    
    try:
        # Clean and prepare data
        x = pd.to_numeric(df[x_col], errors='coerce')
        y = pd.to_numeric(df[y_col], errors='coerce')
        
        clean_cols = [x, y]
        col_names = [x_col, y_col]
        
        if size_col and size_col in df.columns:
            size = pd.to_numeric(df[size_col], errors='coerce')
            clean_cols.append(size)
            col_names.append(size_col)
        
        if color_col and color_col in df.columns:
            if df[color_col].dtype in ['object', 'category']:
                color = df[color_col].astype('category').cat.codes
                is_categorical = True
            else:
                color = pd.to_numeric(df[color_col], errors='coerce')
                is_categorical = False
            clean_cols.append(color)
            col_names.append(color_col)
        
        clean_data = pd.concat(clean_cols, axis=1).dropna()
        
        if len(clean_data) < 3:
            axes[0].text(0.5, 0.5, "Insufficient data for enhanced scatter", ha="center", va="center", color='#CCCCCC')
            _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=1120, height=420)
            return
        
        # 1. Enhanced scatter plot
        ax1 = axes[0]
        
        # Base scatter parameters
        scatter_kwargs = {
            'x': clean_data[x_col],
            'y': clean_data[y_col],
            'alpha': 0.7,
            'edgecolors': 'white',
            'linewidth': 0.5
        }
        
        # Add size encoding
        if size_col and size_col in clean_data.columns:
            sizes = (clean_data[size_col] - clean_data[size_col].min()) / (clean_data[size_col].max() - clean_data[size_col].min())
            scatter_kwargs['s'] = 20 + sizes * 80  # Size range: 20-100
        
        # Add color encoding
        if color_col and color_col in clean_data.columns:
            if is_categorical:
                scatter_kwargs['c'] = clean_data[color_col]
                scatter_kwargs['cmap'] = 'tab10'
            else:
                scatter_kwargs['c'] = clean_data[color_col]
                scatter_kwargs['cmap'] = 'viridis'
        
        scatter = ax1.scatter(**scatter_kwargs)
        
        ax1.set_xlabel(x_col)
        ax1.set_ylabel(y_col)
        ax1.set_title("Enhanced Scatter Plot")
        ax1.set_facecolor("#1a1a1a")
        
        # Add colorbar if numeric color
        if color_col and color_col in clean_data.columns and not is_categorical:
            cbar = fig.colorbar(scatter, ax=ax1, fraction=0.046, pad=0.04)
            cbar.set_label(color_col, color='#CCCCCC')
            cbar.ax.yaxis.set_tick_params(color='#CCCCCC')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#CCCCCC')
        
        # 2. Marginal distributions
        ax2 = axes[1]
        
        # X marginal
        ax2_x = ax2.inset_axes([0, 0.5, 1, 0.4])
        ax2_x.hist(clean_data[x_col], bins=30, alpha=0.7, color='#4ECDC4', density=True)
        ax2_x.set_xticklabels([])
        ax2_x.set_yticklabels([])
        ax2_x.set_title("X Distribution", fontsize=9)
        ax2_x.set_facecolor("#2a2a2a")
        
        # Y marginal
        ax2_y = ax2.inset_axes([0.1, 0, 0.4, 0.5])
        ax2_y.hist(clean_data[y_col], bins=30, alpha=0.7, color='#FF6B6B', density=True, orientation='horizontal')
        ax2_y.set_xticklabels([])
        ax2_y.set_yticklabels([])
        ax2_y.set_title("Y Distribution", fontsize=9)
        ax2_y.set_facecolor("#2a2a2a")
        
        # Main area for correlation info
        ax2.text(0.6, 0.3, f"Points: {len(clean_data):,}\nCorrelation: {clean_data[x_col].corr(clean_data[y_col]):.3f}", 
                transform=ax2.transAxes, fontsize=10, verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='#2a2a2a', alpha=0.8),
                color='#CCCCCC')
        
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        ax2.set_title("Statistics", fontsize=11)
        
        # Styling
        for ax in [ax1, ax2_x, ax2_y]:
            ax.tick_params(colors='#CCCCCC', labelsize=9)
            for spine in ax.spines.values():
                spine.set_color('#CCCCCC')
                spine.set_alpha(0.3)
            if ax != ax2_x and ax != ax2_y:
                ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
    
    except Exception as e:
        axes[0].text(0.5, 0.5, f"Error creating enhanced scatter:\n{str(e)}", ha="center", va="center", color='#FF6B6B')
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=1120, height=420)

def plot_3d_surface(df: pd.DataFrame, x_col: str, y_col: str, z_col: str, parent_tag: str = "plot_canvas"):
    """Create a 3D surface plot for scalar field visualization"""
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(12, 8), facecolor="#1a1a1a")
    ax = fig.add_subplot(111, projection='3d')
    
    try:
        # Clean and prepare data
        x = pd.to_numeric(df[x_col], errors='coerce')
        y = pd.to_numeric(df[y_col], errors='coerce')
        z = pd.to_numeric(df[z_col], errors='coerce')
        
        clean_data = pd.concat([x, y, z], axis=1).dropna()
        
        if len(clean_data) < 10:
            ax.text2D(0.5, 0.5, "Insufficient data for 3D surface", ha="center", va="center", color='#CCCCCC')
            _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=720)
            return
        
        # Create grid for surface
        x_vals = clean_data[x_col].values
        y_vals = clean_data[y_col].values
        z_vals = clean_data[z_col].values
        
        # Create meshgrid
        xi = np.linspace(x_vals.min(), x_vals.max(), 50)
        yi = np.linspace(y_vals.min(), y_vals.max(), 50)
        XI, YI = np.meshgrid(xi, yi)
        
        # Interpolate Z values
        from scipy.interpolate import griddata
        ZI = griddata((x_vals, y_vals), z_vals, (XI, YI), method='cubic')
        
        # Create 3D surface
        surf = ax.plot_surface(XI, YI, ZI, cmap='viridis', alpha=0.8, 
                              linewidth=0, antialiased=True)
        
        # Add scatter points
        ax.scatter(x_vals, y_vals, z_vals, c=z_vals, cmap='viridis', 
                  s=20, alpha=0.6, edgecolors='white')
        
        # Styling
        ax.set_xlabel(x_col, color='#CCCCCC')
        ax.set_ylabel(y_col, color='#CCCCCC')
        ax.set_zlabel(z_col, color='#CCCCCC')
        ax.set_title(f"3D Surface: {z_col}", color='#CCCCCC')
        
        # Set background colors
        ax.set_facecolor("#1a1a1a")
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('#404040')
        ax.yaxis.pane.set_edgecolor('#404040')
        ax.zaxis.pane.set_edgecolor('#404040')
        
        # Set tick colors
        ax.tick_params(colors='#CCCCCC', labelsize=8)
        
        # Add colorbar
        cbar = fig.colorbar(surf, ax=ax, fraction=0.046, pad=0.04, shrink=0.8)
        cbar.set_label(z_col, color='#CCCCCC')
        cbar.ax.yaxis.set_tick_params(color='#CCCCCC')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#CCCCCC')
        
        # Set viewing angle
        ax.view_init(elev=30, azim=45)
    
    except Exception as e:
        ax.text2D(0.5, 0.5, f"Error creating 3D surface:\n{str(e)}", ha="center", va="center", color='#FF6B6B')
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=720)

def plot_categorical_overview(df: pd.DataFrame, col: str, parent_tag: str = "plot_canvas"):
    """Enhanced categorical visualization with multiple perspectives"""
    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#1a1a1a")
    
    value_counts = df[col].value_counts()
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98', '#F0E68C']
    
    # 1. Horizontal bar chart (top values)
    top_values = value_counts.head(15)
    axes[0, 0].barh(range(len(top_values)), top_values.values, 
                    color=[colors[i % len(colors)] for i in range(len(top_values))])
    axes[0, 0].set_yticks(range(len(top_values)))
    axes[0, 0].set_yticklabels(top_values.index, fontsize=8)
    axes[0, 0].set_title("Top Categories", fontsize=10)
    axes[0, 0].set_facecolor("#1a1a1a")
    
    # 2. Pie chart (top 8)
    if len(value_counts) > 0:
        top_8 = value_counts.head(8)
        if len(value_counts) > 8:
            others = value_counts.iloc[8:].sum()
            top_8 = pd.concat([top_8, pd.Series([others], index=['Others'])])
        
        wedges, texts, autotexts = axes[0, 1].pie(top_8.values, labels=top_8.index, autopct='%1.1f%%', 
                                                  colors=colors[:len(top_8)], startangle=90)
        for text in texts:
            text.set_fontsize(7)
        for autotext in autotexts:
            autotext.set_fontsize(7)
    axes[0, 1].set_title("Distribution", fontsize=10)
    
    # 3. Frequency distribution
    freq_dist = value_counts.value_counts().sort_index()
    axes[1, 0].bar(range(len(freq_dist)), freq_dist.values, alpha=0.7, color='#B19CD9')
    axes[1, 0].set_xlabel("Frequency")
    axes[1, 0].set_ylabel("Count of Categories")
    axes[1, 0].set_title("Frequency Distribution", fontsize=10)
    axes[1, 0].set_facecolor("#1a1a1a")
    
    # 4. Summary statistics
    stats_text = f"""
    Unique Values: {df[col].nunique():,}
    Most Common: {value_counts.index[0]}
    Frequency: {value_counts.iloc[0]:,}
    Total Records: {len(df[col]):,}
    Missing: {df[col].isna().sum():,}
    
    Top 5 Categories:
    """
    for i, (cat, count) in enumerate(value_counts.head(5).items()):
        stats_text += f"\n{i+1}. {cat}: {count:,} ({100*count/len(df[col]):.1f}%)"
    
    axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes, 
                    fontsize=8, verticalalignment='top', fontfamily='monospace')
    axes[1, 1].set_title("Statistics", fontsize=10)
    axes[1, 1].axis('off')
    axes[1, 1].set_facecolor("#1a1a1a")
    
    for ax in axes.flat:
        if ax != axes[1, 1]:  # Skip the text axis
            ax.tick_params(labelsize=8)
            for side in ("top", "right"): 
                ax.spines[side].set_visible(False)
    
    plt.tight_layout()
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=960, height=600)
