# SCV Analysis Slicer

Tools for exploring, slicing, and visualizing large CSV files.  The project
provides both a DearPyGui interface and a command-line entry point.

## Features

- Modular architecture (`app.py`, `ui.py`, `data_loader.py`, `analysis.py`,
  `visualization.py`, `utils.py`)
- In-memory rendering pipeline so Matplotlib figures become DearPyGui textures
  without temporary files
- Extended statistics: median, IQR, skewness, kurtosis, and missing percentages
- Pagination to preview large tables page by page
- Histogram, box, scatter, line, and ECDF plots
- Automatically selects the fastest CSV reader (`pyarrow` when available)
- CLI support via `main_cli.py`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### GUI

```bash
python app.py
```

### Command line

```bash
python main_cli.py --help
```

## Notes

- Font loading is best-effort across Windows/macOS/Linux. If no font is
  found, DearPyGui's default is used.
- For very large CSVs, consider providing explicit `dtype` maps inside
  `data_loader.load_csv` for optimal memory usage.
