from __future__ import annotations
import io
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import dearpygui.dearpygui as dpg
import pandas as pd

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
    ax.set_facecolor("#1a1a1a")
    ax.hist(df[numeric_col].dropna(), bins=30, alpha=0.8)
    ax.set_title(f"{numeric_col} Distribution")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, texture_tag, parent_tag, width=880, height=220)

def plot_generic(df: pd.DataFrame, column: str, plot_type: str, texture_tag: str, parent_tag: str):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    if plot_type == "Histogram":
        ax.hist(df[column].dropna(), bins=30, alpha=0.8)
    elif plot_type == "Box Plot":
        ax.boxplot(df[column].dropna().values, vert=True, labels=[column])
    elif plot_type == "Scatter Plot":
        ax.scatter(range(len(df[column])), df[column], alpha=0.5)
    elif plot_type == "Line":
        ax.plot(df[column].values)
    elif plot_type == "ECDF":
        vals = pd.Series(df[column]).dropna().sort_values().values
        y = np.linspace(0, 1, len(vals), endpoint=True)
        ax.step(vals, y, where="post")
    else:
        ax.text(0.5, 0.5, f"Unsupported plot: {plot_type}", ha="center", va="center")

    ax.set_title(f"{plot_type}: {column}")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    _finalize_fig_to_texture(fig, texture_tag, parent_tag)

# --- 추가: combinations add-on helpers (병합) ---

def plot_bar_topk(df: pd.DataFrame, col: str, k: int = 20, parent_tag: str = "plot_canvas"):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10,5), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    vc = df[col].astype("object").value_counts(dropna=False).head(k)
    vc.plot(kind="bar", ax=ax)
    ax.set_title(f"Top-{k} values of {col}")
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
    ax.set_xticklabels([str(x) for x in ct.columns], rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels([str(y) for y in ct.index], fontsize=9)
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
    ax.set_xticks(range(len(sel))); ax.set_xticklabels(sel, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(sel))); ax.set_yticklabels(sel, fontsize=9)
    ax.set_title(f"{method.title()} correlation (top pairs)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _finalize_fig_to_texture(fig, "hist_tex", parent_tag, width=860, height=500)
