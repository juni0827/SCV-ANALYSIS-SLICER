#!/usr/bin/env python3
"""
CSV Analyzer - Main GUI Application Entry Point

This is a wrapper that imports the main application from the new modular structure.
The actual application code is in src/gui/app.py
"""

# Import from the new modular structure
from src.gui.app import CSVAnalyzerApp
import tkinter as tk


def main():
    root = tk.Tk()
    root.title("CSV Analysis Slicer")
    root.geometry("1400x900")
    app = CSVAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
