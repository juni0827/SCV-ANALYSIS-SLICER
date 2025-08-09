
# CSV Analyzer (Modular Refactor)

A refactored, modular DearPyGui application for fast CSV inspection, filtering, and visualization.

## Highlights
- **Modular**: `app.py`, `ui.py`, `data_loader.py`, `analysis.py`, `visualization.py`, `utils.py`
- **No disk I/O for plots**: In-memory (BytesIO) pipeline to render Matplotlib figures into DearPyGui textures
- **Extended stats**: median, IQR, skewness, kurtosis, missing%
- **Pagination**: preview large tables with adjustable page size
- **Extra plots**: Histogram, Box, Scatter, Line, ECDF
- **Engine auto-select**: uses **pyarrow** CSV reader if available

## Install
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

## Notes
- Font loading is **best-effort** across Windows/macOS/Linux. If no font is found, DearPyGui's default is used.
- For very large CSVs, consider providing explicit `dtype` maps inside `data_loader.load_csv` for optimal memory usage.
