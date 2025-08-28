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

## 한국어 안내

SCV Analysis Slicer는 대규모 CSV 파일을 탐색하고 슬라이싱하며 시각화하는 도구입니다. DearPyGui 기반 UI와 명령줄 인터페이스를 제공합니다.

### 기능

- 모듈형 구조 (`app.py`, `ui.py`, `data_loader.py`, `analysis.py`, `visualization.py`, `utils.py`)
- 임시 파일 없이 Matplotlib 그림을 DearPyGui 텍스처로 렌더링하는 인메모리 파이프라인
- 중앙값, IQR, 왜도, 첨도, 결측 비율 등의 확장 통계
- 대규모 테이블을 페이지 단위로 미리보기
- 히스토그램, 박스, 산점도, 선, ECDF 플롯 지원
- 가능한 경우 가장 빠른 CSV 리더를 자동 선택 (`pyarrow`)
- `main_cli.py`를 통한 CLI 지원

### 설치

```bash
pip install -r requirements.txt
```

### 사용법

#### GUI

```bash
python app.py
```

#### 명령줄

```bash
python main_cli.py --help
```

### Windows 실행파일 빌드

#### 자동 빌드 스크립트 사용

```batch
build.bat
```

#### 수동 빌드

```bash
# PyInstaller 설치
pip install pyinstaller

# 실행파일 생성
python build.py
```

또는 직접 PyInstaller 명령어 사용:

```bash
python -m PyInstaller --onefile --windowed --name="CSV-Analyzer" app.py
```

빌드 완료 후 `dist/` 폴더에 `CSV-Analyzer.exe` 파일이 생성됩니다.

### 참고 사항

- 글꼴 로딩은 Windows/macOS/Linux 환경에서 최선을 다하며, 찾지 못하면 DearPyGui 기본 글꼴이 사용됩니다.
- 매우 큰 CSV 파일의 경우, 최적의 메모리 사용을 위해 `data_loader.load_csv` 함수에 `dtype` 맵을 명시적으로 제공하는 것이 좋습니다.
- Windows 실행파일 빌드 시 파일 크기가 클 수 있습니다 (약 200MB). 이는 PyTorch 등 대용량 라이브러리가 포함되기 때문입니다.

