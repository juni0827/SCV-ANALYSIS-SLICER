#!/usr/bin/env python3
"""
Build configuration constants for PyInstaller and application settings.
Centralizes hardcoded values for better maintainability.
"""

# PyInstaller Build Configuration
EXECUTABLE_NAME = "CSV-Analyzer"
OUTPUT_DIRECTORY = "dist"
BUILD_DIRECTORY = "build"

# Excluded modules for smaller build size
EXCLUDED_MODULES = [
    "dearpygui",
    "PyQt5",
    "PyQt6", 
    "PySide2",
    "PySide6",
    "wx",
    "test",
    "unittest"
]

# Additional data files to include
DATA_FILES = [
    "README.md"
]

# Hidden imports required for proper functionality
HIDDEN_IMPORTS = [
    "single_instance",
    "ctypes",
    "ctypes.wintypes"
]

# Build optimization settings
BUILD_OPTIMIZATION_LEVEL = 2
ENABLE_CLEAN_BUILD = True
ENABLE_WINDOWED_MODE = True
ENABLE_ONE_FILE = True

# File size calculation constants
BYTES_PER_KB = 1024
BYTES_PER_MB = BYTES_PER_KB * 1024
BYTES_PER_GB = BYTES_PER_MB * 1024

# Application metadata
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Advanced CSV Analysis and Visualization Tool"
APP_AUTHOR = "CSV Analyzer Development Team"