
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
