import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import tkinter as tk
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches


class Plotter:
    def __init__(self, is_dark_mode=False):
        self.is_dark_mode = is_dark_mode
        self.update_theme(is_dark_mode)

    def update_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        if is_dark_mode:
            self.bg_color = "#2B2B2B"
            self.text_color = "#CCCCCC"
            self.grid_color = "#404040"
            self.colors = ["#00FF9F", "#00B8FF", "#D600FF", "#F4D03F", "#FF0055"]
            plt.style.use("dark_background")
        else:
            self.bg_color = "white"
            self.text_color = "#333333"
            self.grid_color = "#E0E0E0"
            self.colors = ["#3498DB", "#E74C3C", "#2ECC71", "#F1C40F", "#9B59B6"]
            plt.style.use("default")

        plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

    def create_figure(self, figsize=(10, 6)):
        plt.close("all")  # Clear memory
        fig = plt.figure(figsize=figsize)
        fig.patch.set_facecolor(self.bg_color)
        return fig

    def style_axis(self, ax, is_3d=False):
        ax.set_facecolor(self.bg_color)
        if is_3d:
            ax.w_xaxis.set_pane_color((0.2, 0.2, 0.2, 1.0))
            ax.w_yaxis.set_pane_color((0.2, 0.2, 0.2, 1.0))
            ax.w_zaxis.set_pane_color((0.2, 0.2, 0.2, 1.0))
            ax.tick_params(colors=self.text_color)
            ax.xaxis.label.set_color(self.text_color)
            ax.yaxis.label.set_color(self.text_color)
            ax.zaxis.label.set_color(self.text_color)
        else:
            ax.tick_params(colors=self.text_color, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(self.text_color)
            ax.grid(True, color=self.grid_color, alpha=0.2)
            ax.xaxis.label.set_color(self.text_color)
            ax.yaxis.label.set_color(self.text_color)

    def plot(self, viz_type, data, column, parent_frame):
        # Clear previous
        for widget in parent_frame.winfo_children():
            widget.destroy()

        fig = self.create_figure()
        is_numeric = pd.api.types.is_numeric_dtype(data)

        # Sampling for large datasets
        if len(data) > 10000 and viz_type in [
            "Scatter Plot",
            "Line Plot",
            "3D Scatter",
        ]:
            plot_data = data.sample(10000).sort_index()
        else:
            plot_data = data

        try:
            if viz_type == "Auto (Smart)":
                self._plot_smart(fig, plot_data, column, is_numeric)
            else:
                if viz_type == "3D Scatter":
                    ax = fig.add_subplot(111, projection="3d")
                    self.style_axis(ax, is_3d=True)
                else:
                    ax = fig.add_subplot(111)
                    self.style_axis(ax)

                self._plot_specific(fig, ax, viz_type, plot_data, column, is_numeric)

            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            plt.close(fig)
            raise e

    def _plot_specific(self, fig, ax, viz_type, data, column, is_numeric):
        if viz_type == "Histogram":
            if is_numeric:
                n, bins, patches = ax.hist(
                    data,
                    bins=30,
                    color=self.colors[0],
                    edgecolor=self.text_color,
                    alpha=0.7,
                )
                ax.set_title(f"Histogram of {column}", color=self.text_color)
                self._add_hover_tooltip(fig, ax, patches, "bar", data)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type == "Box Plot":
            if is_numeric:
                bp = ax.boxplot(data, patch_artist=True)
                bp["boxes"][0].set_facecolor(self.colors[0])
                ax.set_title(f"Box Plot of {column}", color=self.text_color)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type == "Scatter Plot":
            if is_numeric:
                sc = ax.scatter(
                    data.index, data.values, c=self.colors[1], alpha=0.6, s=30
                )
                ax.set_title(f"Scatter Plot: Index vs {column}", color=self.text_color)
                self._add_hover_tooltip(fig, ax, sc, "scatter", data)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type == "Line Plot":
            if is_numeric:
                (line,) = ax.plot(
                    data.index, data.values, color=self.colors[2], linewidth=1.5
                )
                ax.set_title(f"Line Plot of {column}", color=self.text_color)
                self._add_hover_tooltip(fig, ax, line, "line", data)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type in ["Bar Chart", "Pie Chart", "Donut Chart"]:
            if is_numeric and data.nunique() > 20:
                vc = pd.cut(data, bins=10).value_counts().sort_index()
            else:
                vc = data.value_counts()
                if len(vc) > 15:
                    vc = pd.concat(
                        [vc.head(14), pd.Series({"Others": vc.iloc[14:].sum()})]
                    )

            if viz_type == "Bar Chart":
                bars = ax.bar(range(len(vc)), vc.values, color=self.colors, alpha=0.8)
                ax.set_xticks(range(len(vc)))
                ax.set_xticklabels(
                    [str(x)[:10] for x in vc.index], rotation=45, ha="right"
                )
                ax.set_title(f"Bar Chart of {column}", color=self.text_color)
                self._add_hover_tooltip(fig, ax, bars, "bar", vc)

            elif viz_type in ["Pie Chart", "Donut Chart"]:
                wedges, texts, autotexts = ax.pie(
                    vc.values,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=90,
                    colors=self.colors,
                    wedgeprops=dict(
                        width=0.5 if viz_type == "Donut Chart" else 1,
                        edgecolor=self.bg_color,
                    ),
                )
                ax.legend(
                    wedges,
                    vc.index,
                    title="Categories",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1),
                )
                ax.set_title(f"{viz_type} of {column}", color=self.text_color)
                for t in texts + autotexts:
                    t.set_color(self.text_color)
                self._add_hover_tooltip(fig, ax, wedges, "pie", vc)

        elif viz_type == "3D Scatter":
            if is_numeric:
                z = data.rolling(5).mean().fillna(method="bfill")
                sc = ax.scatter(
                    range(len(data)), data.values, z, c=data.values, cmap="viridis"
                )
                ax.set_xlabel("Index")
                ax.set_ylabel("Value")
                ax.set_zlabel("Rolling Mean")
                ax.set_title(f"3D Scatter of {column}", color=self.text_color)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type == "Violin Plot":
            if is_numeric:
                parts = ax.violinplot(data, showmeans=True)
                for pc in parts["bodies"]:
                    pc.set_facecolor(self.colors[3])
                    pc.set_alpha(0.6)
                ax.set_title(f"Violin Plot of {column}", color=self.text_color)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

        elif viz_type == "Hexbin Plot":
            if is_numeric:
                hb = ax.hexbin(data.index, data.values, gridsize=20, cmap="inferno")
                fig.colorbar(hb, ax=ax)
                ax.set_title(f"Hexbin Plot of {column}", color=self.text_color)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Requires numeric data",
                    ha="center",
                    color=self.text_color,
                )

    def _plot_smart(self, fig, data, column, is_numeric):
        if is_numeric:
            # 1. Histogram
            ax1 = fig.add_subplot(221)
            self.style_axis(ax1)
            n, bins, patches = ax1.hist(data, bins=30, color=self.colors[0], alpha=0.7)
            ax1.set_title("Histogram", color=self.text_color)
            self._add_hover_tooltip(fig, ax1, patches, "bar", data)

            # 2. Scatter
            ax2 = fig.add_subplot(222)
            self.style_axis(ax2)
            sample = data.sample(min(1000, len(data))).sort_index()
            sc = ax2.scatter(
                sample.index,
                sample.values,
                c=sample.values,
                cmap="viridis",
                alpha=0.6,
                s=15,
            )
            ax2.set_title("Scatter", color=self.text_color)
            self._add_hover_tooltip(fig, ax2, sc, "scatter", sample)

            # 3. 3D
            ax3 = fig.add_subplot(223, projection="3d")
            self.style_axis(ax3, is_3d=True)
            sample_3d = data.sample(min(500, len(data))).sort_index()
            ax3.scatter(
                np.arange(len(sample_3d)),
                sample_3d.values,
                sample_3d.rolling(5).mean().fillna(0),
                c=sample_3d.values,
                cmap="plasma",
            )
            ax3.set_title("3D Analysis", color=self.text_color)

            # 4. Violin
            ax4 = fig.add_subplot(224)
            self.style_axis(ax4)
            ax4.violinplot(data, vert=False)
            ax4.set_title("Violin", color=self.text_color)
        else:
            vc = data.value_counts()
            if len(vc) > 10:
                vc = pd.concat([vc.head(10), pd.Series({"Others": vc.iloc[10:].sum()})])

            # Bar
            ax1 = fig.add_subplot(121)
            self.style_axis(ax1)
            bars = ax1.barh(range(len(vc)), vc.values, color=self.colors)
            ax1.set_yticks(range(len(vc)))
            ax1.set_yticklabels([str(x)[:10] for x in vc.index], color=self.text_color)
            ax1.set_title("Bar Chart", color=self.text_color)
            self._add_hover_tooltip(fig, ax1, bars, "bar", vc)

            # Donut
            ax2 = fig.add_subplot(122)
            wedges, _, _ = ax2.pie(
                vc.values,
                autopct="%1.1f%%",
                colors=self.colors,
                wedgeprops=dict(width=0.5),
            )
            ax2.legend(
                wedges, vc.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1)
            )
            ax2.set_title("Donut Chart", color=self.text_color)
            self._add_hover_tooltip(fig, ax2, wedges, "pie", vc)

    def _add_hover_tooltip(self, fig, ax, artist, type, data):
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w", alpha=0.8),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)

        def update_annot(ind, artist_type):
            if artist_type == "scatter":
                pos = artist.get_offsets()[ind["ind"][0]]
                annot.xy = pos
                idx = ind["ind"][0]
                if hasattr(data, "index"):
                    val = data.iloc[idx]
                    idx_val = data.index[idx]
                    text = f"Index: {idx_val}\nValue: {val}"
                else:
                    text = f"Value: {pos}"
            elif artist_type == "bar":
                bar = artist[ind["ind"][0]]
                annot.xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                val = bar.get_height()
                if hasattr(data, "index"):
                    cat = data.index[ind["ind"][0]]
                    text = f"{cat}: {val}"
                else:
                    text = f"Value: {val}"
            elif artist_type == "pie":
                wedge = artist[ind["ind"][0]]
                center = wedge.center
                theta = (wedge.theta1 + wedge.theta2) / 2
                import math

                x = center[0] + math.cos(math.radians(theta)) * 0.5
                y = center[1] + math.sin(math.radians(theta)) * 0.5
                annot.xy = (x, y)
                if hasattr(data, "index"):
                    cat = data.index[ind["ind"][0]]
                    val = data.values[ind["ind"][0]]
                    text = f"{cat}: {val} ({val/data.sum()*100:.1f}%)"
                else:
                    text = f"Value: {val}"
            elif artist_type == "line":
                # Line tooltip is tricky, usually need to find nearest point
                x, y = artist.get_data()
                idx = ind["ind"][0]
                annot.xy = (x[idx], y[idx])
                text = f"x: {x[idx]}\ny: {y[idx]}"

            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.9)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont = False
                ind = None

                if type == "scatter":
                    cont, ind = artist.contains(event)
                elif type == "bar" or type == "pie":
                    for i, item in enumerate(artist):
                        if item.contains(event)[0]:
                            cont = True
                            ind = {"ind": [i]}
                            break
                elif type == "line":
                    cont, ind = artist.contains(event)

                if cont:
                    update_annot(ind, type)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
