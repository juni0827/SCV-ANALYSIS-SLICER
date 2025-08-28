# SCV Analysis Slicer

Advanced tools for exploring, slicing, and visualizing large CSV files with ML-powered analysis capabilities. The project provides both a modern Tkinter-based GUI and intelligent command-line DSL analysis.

## Features

### Core Analysis
- Modular architecture (`app.py`, `ui.py`, `data_loader.py`, `analysis.py`, `visualization.py`, `utils.py`, `combinations.py`)
- Extended statistics: median, IQR, skewness, kurtosis, and missing percentages
- Pagination to preview large tables page by page (up to 1000 rows)
- Automatically selects the fastest CSV reader (`pyarrow` when available)
- Advanced combinations analysis for discovering relationships between columns

### Visualization & UI
- Modern Tkinter-based GUI with dark/light theme switching
- Histogram, box, scatter, line, ECDF, heatmap, and correlation plots
- In-memory rendering pipeline for Matplotlib figures
- Interactive data exploration with filtering and slicing
- Export utilities for saving dataframes and analysis reports

### ML-Powered DSL Analysis
- Domain Specific Language (DSL) for automated analysis workflows
- PyTorch-based LSTM model for intelligent code generation
- CLI support via `main_cli.py` for DSL-based analysis
- Automatic prediction of analysis sequences from user input

## Installation

```bash
pip install -r requirements.txt
```

### Requirements
- Python 3.8+
- pandas >= 2.0.0
- tkinter (usually included with Python)
- matplotlib >= 3.7.0
- pyarrow >= 16.0.0
- torch (for ML-powered DSL features)
- Pillow >= 10.0.0

## Usage

### GUI Application
Launch the modern Tkinter-based interface with theme switching:

```bash
python app.py
```

Features:
- Dark/Light theme toggle
- Interactive data preview and filtering
- Advanced statistical analysis
- Multiple visualization types
- Export capabilities for data and reports

### DSL Command Line Analysis
Use the intelligent DSL system for automated analysis:

```bash
python main_cli.py
```

Enter DSL tokens (e.g., `C1 C2 C6`) to generate analysis code automatically. The ML model will predict the optimal analysis sequence and generate executable Python code.

### Classic Command Line
```bash
python main_cli.py --help
```

## DSL (Domain Specific Language) System

The project includes an innovative ML-powered DSL system for automated data analysis:

### DSL Tokens
- `C1`: `df.describe()` - Statistical summary
- `C2`: `df.info()` - DataFrame information
- `C3`: `df.isnull().sum()` - Missing values count
- `C4`: `df.dtypes` - Data types
- `C5`: `df.nunique()` - Unique values count
- `C6`: `df.head()` - First few rows
- `C7`: `df.tail()` - Last few rows
- `C8`: `df.corr()` - Correlation matrix
- `C9`: `df.columns` - Column names
- `C10`: `df.memory_usage()` - Memory usage

### How it Works
1. Input DSL tokens in the CLI interface
2. PyTorch LSTM model predicts optimal analysis sequence
3. Generated Python code is saved to `generated_analysis.py`
4. Execute the code for automated analysis

## Build Executable

### Automated Build (Recommended)
```batch
# Windows
build_new.bat

# Choose option 2 for optimized build (faster, smaller size)
```

### Manual Build
```bash
# Install PyInstaller
pip install pyinstaller

# Optimized build
python build_optimized.py

# Or use the basic build script
python build.py
```

The executable will be created in the `dist/` folder as `CSV-Analyzer.exe`.

## Notes

- Font loading is best-effort across Windows/macOS/Linux. If no font is found, the system default is used.
- For very large CSVs, consider providing explicit `dtype` maps in `data_loader.load_csv` for optimal memory usage.
- The ML model (`model.pt`) and tokenizer (`dsl_tokenizer.json`) are included for DSL functionality.
- Executable build size may be large (~200MB) due to PyTorch and other dependencies.
- Theme switching preserves user preferences and provides smooth transitions.

## 한국어 안내

SCV Analysis Slicer는 ML 기반 분석 기능을 갖춘 대규모 CSV 파일 탐색, 슬라이싱 및 시각화 도구입니다. 현대적인 Tkinter 기반 GUI와 지능형 DSL 명령줄 분석을 제공합니다.

### 주요 기능

#### 핵심 분석
- 모듈형 구조 (`app.py`, `ui.py`, `data_loader.py`, `analysis.py`, `visualization.py`, `utils.py`, `combinations.py`)
- 중앙값, IQR, 왜도, 첨도, 결측 비율 등의 확장 통계
- 대규모 테이블을 페이지 단위로 미리보기 (최대 1000행)
- 가능한 경우 가장 빠른 CSV 리더를 자동 선택 (`pyarrow`)
- 컬럼 간 관계 발견을 위한 고급 조합 분석

#### 시각화 및 UI
- 다크/라이트 테마 전환이 가능한 현대적인 Tkinter 기반 GUI
- 히스토그램, 박스, 산점도, 선, ECDF, 히트맵, 상관관계 플롯
- Matplotlib 그림을 위한 인메모리 렌더링 파이프라인
- 필터링 및 슬라이싱이 가능한 대화형 데이터 탐색
- 데이터프레임 및 분석 보고서 저장을 위한 내보내기 유틸리티

#### ML 기반 DSL 분석
- 자동화된 분석 워크플로우를 위한 도메인 특화 언어(DSL)
- 지능형 코드 생성을 위한 PyTorch 기반 LSTM 모델
- DSL 기반 분석을 위한 `main_cli.py`를 통한 CLI 지원
- 사용자 입력으로부터 분석 시퀀스 자동 예측

### 설치

```bash
pip install -r requirements.txt
```

### 요구사항
- Python 3.8+
- pandas >= 2.0.0
- tkinter (보통 Python과 함께 포함됨)
- matplotlib >= 3.7.0
- pyarrow >= 16.0.0
- torch (ML 기반 DSL 기능용)
- Pillow >= 10.0.0

### 사용법

#### GUI 애플리케이션
테마 전환 기능이 있는 현대적인 Tkinter 기반 인터페이스 실행:

```bash
python app.py
```

기능:
- 다크/라이트 테마 토글
- 대화형 데이터 미리보기 및 필터링
- 고급 통계 분석
- 다양한 시각화 유형
- 데이터 및 보고서 내보내기 기능

#### DSL 명령줄 분석
자동화된 분석을 위한 지능형 DSL 시스템 사용:

```bash
python main_cli.py
```

DSL 토큰(예: `C1 C2 C6`)을 입력하여 분석 코드를 자동으로 생성합니다. ML 모델이 최적의 분석 시퀀스를 예측하고 실행 가능한 Python 코드를 생성합니다.

#### 기존 명령줄

```bash
python main_cli.py --help
```

### DSL (도메인 특화 언어) 시스템

프로젝트에는 자동화된 데이터 분석을 위한 혁신적인 ML 기반 DSL 시스템이 포함되어 있습니다:

#### DSL 토큰
- `C1`: `df.describe()` - 통계 요약
- `C2`: `df.info()` - 데이터프레임 정보
- `C3`: `df.isnull().sum()` - 결측값 개수
- `C4`: `df.dtypes` - 데이터 타입
- `C5`: `df.nunique()` - 고유값 개수
- `C6`: `df.head()` - 처음 몇 행
- `C7`: `df.tail()` - 마지막 몇 행
- `C8`: `df.corr()` - 상관관계 행렬
- `C9`: `df.columns` - 컬럼 이름
- `C10`: `df.memory_usage()` - 메모리 사용량

#### 작동 방식
1. CLI 인터페이스에서 DSL 토큰 입력
2. PyTorch LSTM 모델이 최적의 분석 시퀀스 예측
3. 생성된 Python 코드를 `generated_analysis.py`에 저장
4. 자동화된 분석을 위해 코드 실행

### Windows 실행파일 빌드

#### 자동 빌드 스크립트 사용 (권장)

```batch
build_new.bat
```

최적화된 빌드를 위해 옵션 2를 선택하세요 (더 빠르고 작은 크기).

#### 수동 빌드

```bash
# PyInstaller 설치
pip install pyinstaller

# 최적화된 빌드
python build_optimized.py

# 또는 기본 빌드 스크립트 사용
python build.py
```

실행파일은 `dist/` 폴더에 `CSV-Analyzer.exe`로 생성됩니다.

### 참고 사항

- 글꼴 로딩은 Windows/macOS/Linux 환경에서 최선을 다하며, 찾지 못하면 시스템 기본 글꼴이 사용됩니다.
- 매우 큰 CSV 파일의 경우, 최적의 메모리 사용을 위해 `data_loader.load_csv` 함수에 `dtype` 맵을 명시적으로 제공하는 것이 좋습니다.
- DSL 기능을 위해 ML 모델(`model.pt`)과 토크나이저(`dsl_tokenizer.json`)가 포함되어 있습니다.
- PyTorch 및 기타 종속성으로 인해 실행파일 빌드 크기가 클 수 있습니다(약 200MB).
- 테마 전환 기능은 사용자 기본 설정을 유지하고 부드러운 전환을 제공합니다.

