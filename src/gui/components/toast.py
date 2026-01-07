"""
Toast notification window component
"""

from __future__ import annotations
import tkinter as tk


class ToastWindow:
    """Toast notification window with fade effects"""

    def __init__(
        self, parent, message: str, kind: str = "info", is_dark_mode: bool = False
    ):
        # more natural per light/dark mode 색상
        if is_dark_mode:
            self.colors = {
                "info": "#2C5F7D",
                "ok": "#2E7D4B",
                "warn": "#8B6914",
                "error": "#B85450",
            }
            text_color = "#E8E8E8"
            border_color = "#404040"
        else:
            self.colors = {
                "info": "#D4EDDA",
                "ok": "#DFF0D8",
                "warn": "#FCF8E3",
                "error": "#F8D7DA",
            }
            text_color = "#2C3E50"
            border_color = "#D1ECF1"

        self.toast = tk.Toplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.configure(bg=self.colors.get(kind, self.colors["info"]))

        # position at top center of screen
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_rooty() + 50
        self.toast.geometry(f"300x60+{x}+{y}")

        # for rounded corner effect 프레임
        main_frame = tk.Frame(
            self.toast,
            bg=self.colors.get(kind, self.colors["info"]),
            relief="solid",
            bd=1,
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # message label
        label = tk.Label(
            main_frame,
            text=message,
            bg=self.colors.get(kind, self.colors["info"]),
            fg=text_color,
            font=("Arial", 10, "normal"),
            wraplength=280,
        )
        label.pack(expand=True, fill="both", padx=15, pady=15)

        # smooth fade-in effect
        self.fade_in()

        # 3seconds 후 Automatic Close
        self.toast.after(3000, self.fade_out)

    def fade_in(self):
        """smooth fade-in effect"""
        self.toast.attributes("-alpha", 0.0)
        self.fade_in_step(0.0)

    def fade_in_step(self, alpha):
        """페이드 인 단계"""
        if alpha < 0.95:
            alpha += 0.1
            self.toast.attributes("-alpha", alpha)
            self.toast.after(30, lambda: self.fade_in_step(alpha))
        else:
            self.toast.attributes("-alpha", 1.0)

    def fade_out(self):
        """부드러운 사라지기 효과"""
        self.fade_out_step(1.0)

    def fade_out_step(self, alpha):
        """페이드 아웃 단계"""
        if alpha > 0.05:
            alpha -= 0.1
            try:
                self.toast.attributes("-alpha", alpha)
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
