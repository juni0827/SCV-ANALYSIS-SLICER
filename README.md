# SCV Analysis Slicer

Advanced tools for exploring, slicing, and visualizing large CSV files with ML-powered analysis capabilities. The project provides both a modern Tkinter-based GUI and intelligent command-line DSL analysis.

## Features

### Core Analysis

- Modular architecture (`src/core`, `src/gui`, `src/dsl`, `src/utils`)
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
python -m src.gui.app
```

> **Note**: The canonical implementation is in the `src/` directory. Legacy root-level GUI files have been removed.

Features:

- **Dark/Light theme toggle**: 사용자 환경에 맞는 테마 선택
- **Interactive data preview and filtering**: 대화형 데이터 미리보기 및 필터링
- **Advanced statistical analysis**: 고급 통계 분석 도구
- **Combinations Analysis**: 컬럼 간 관계 분석 (상관관계, 연관규칙, ANOVA)
- **Multiple visualization types**: 다양한 시각화 차트
- **Export capabilities**: 데이터 및 보고서 내보내기

#### Combinations Analysis 탭 사용법

1. **데이터 로드**: 먼저 CSV 파일을 로드합니다
2. **DSL 토큰 입력** (선택사항): 특정 컬럼만 분석하려면 토큰 입력 (예: C1,C2,C3)
3. **상위 결과 수 설정**: 표시할 결과의 개수 설정
4. **분석 실행**: '분석 실행' 버튼 클릭
5. **결과 확인**: 상관관계, 연관성, ANOVA 결과를 확인

### DSL Command Line Analysis (확장된 기능)

강력한 ML 기반 DSL 자동 분석 도구:

```bash
# 기본 대화형 모드
python main_cli.py

# 토큰 직접 지정
python main_cli.py --tokens C1,C2,C6 --file data.csv

# 대화형 모드 (파일 지정)
python main_cli.py --file data.csv --interactive

# 사용 가능한 토큰 목록 보기
python main_cli.py --help-tokens

# 출력 파일 지정
python main_cli.py --tokens C2,C1,C6 --output my_analysis.py
```

#### 주요 기능

- **ML 예측**: LSTM 모델이 최적 분석 시퀀스 예측
- **50+ 토큰**: C1~C50 + 특수 토큰 (SAVE, EXPORT, PROFILE)
- **템플릿 분석**: 기본, 통계, 시각화, 상관관계 등 미리 정의된 분석 패턴
- **스마트 코드 생성**: 실행 가능한 Python 코드 자동 생성
- **오류 처리**: 각 분석 단계별 예외 처리 포함

#### 분석 템플릿

- `basic`: C2, C15, C6, C3, C1 (기본 데이터 탐색)
- `statistical`: C1, C14, C29, C41, C42, C43 (고급 통계)
- `visualization`: C12, C23, C35, C47 (다양한 시각화)
- `correlation`: C8, C12, C25, C50 (상관관계 분석)

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

### Quick Build (Recommended)

```bash
# 표준 빌드 (빠름, 모든 기능 포함)
python build.py

# 최적화 빌드 (느림, 파일 크기 작음)
python build.py --optimized

# 빌드 파일 정리
python build.py --clean
```

실행 파일은 `dist/` 폴더에 생성됩니다:

- Windows: `CSV-Analyzer.exe`
- Linux/macOS: `CSV-Analyzer`

### Manual Build (Advanced)

```bash
# PyInstaller 설치
pip install pyinstaller

# 표준 빌드
python build.py

# 최적화 빌드
python build.py --optimized
```

## Notes

- Font loading is best-effort across Windows/macOS/Linux. If no font is found, the system default is used.
- For very large CSVs, consider providing explicit `dtype` maps in `data_loader.load_csv` for optimal memory usage.
- The ML model (`model.pt`) and tokenizer (`dsl_tokenizer.json`) are included for DSL functionality.
- Executable build size may be large (~200MB) due to PyTorch and other dependencies.
- Theme switching preserves user preferences and provides smooth transitions.

## 한국어 안내

SCV Analysis Slicer는 ML 기반 분석 기능을 갖춘 대규모 CSV 파일 탐색, 슬라이싱 및 시각화 도구입니다. 현대적인 Tkinter 기반 GUI와 지능형 DSL 명령줄 분석을 제공합니다.

### 주요 기능 (한국어)

#### 핵심 분석

- 모듈형 구조 (`src/core`, `src/gui`, `src/dsl`, `src/utils`)
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
python -m src.gui.app
```

> **참고**: 정식 구현은 `src/` 디렉토리에 있습니다. 레거시 루트 레벨 GUI 파일이 제거되었습니다.

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

### Advanced Combinations Analysis (고급 조합 분석)

프로젝트의 핵심 기능인 `combinations.py`는 데이터 컬럼 간의 관계를 자동으로 분석합니다:

#### 새로운 고급 기능들

- **병렬 처리**: ThreadPoolExecutor를 통한 고성능 분석
- **메모리 최적화**: 데이터 타입 자동 최적화 및 메모리 사용량 모니터링
- **캐싱 시스템**: 분석 결과 자동 캐싱으로 반복 분석 속도 향상
- **텍스트 분석**: 텍스트 컬럼의 통계적 분석
- **실시간 모니터링**: 성능 메트릭 수집 및 분석
- **시각화 추천**: 분석 결과를 바탕으로 적절한 차트 자동 추천

#### 분석 기능

- **수치형 × 수치형**: Pearson, Spearman, Kendall 상관계수 + 신뢰성 평가
- **범주형 × 범주형**: Lift 분석 (연관규칙 마이닝)
- **범주형 × 수치형**: ANOVA 기반 분산분석 + 그룹별 통계
- **텍스트 분석**: 단어 빈도 분석 및 텍스트 통계

#### 사용 방법

**기본 사용:**

```python
from combinations import AdvancedCombinationsAnalyzer, AnalysisConfig

config = AnalysisConfig(
    max_cardinality=50,
    top_k=20,
    correlation_threshold=0.3,
    parallel_processing=True
)

analyzer = AdvancedCombinationsAnalyzer(config)
results = analyzer.analyze_combinations_advanced(df)
```

**통합 CLI 도구:**

```bash
# 기본 사용법
python combinations.py --file data.csv --output results.json

# DSL 토큰을 사용한 분석
python combinations.py --file data.csv --dsl-tokens C1,C2,C3 --verbose

# 설정 파일 사용
python combinations.py --file data.csv --config analysis_config.json

# 고급 옵션
python combinations.py --file data.csv --max-cardinality 30 --top-k 15 --no-cache
```

**Python 모듈로 사용:**

```python
from combinations import AdvancedCombinationsAnalyzer, AnalysisConfig

# 기본 분석
analyzer = AdvancedCombinationsAnalyzer()
results = analyzer.analyze_all_combinations(df)

# 설정 사용자 정의
config = AnalysisConfig(max_cardinality=30, top_k=15, parallel_processing=True)
analyzer = AdvancedCombinationsAnalyzer(config)
results = analyzer.analyze_all_combinations(df, dsl_tokens=['C1', 'C2'])

# 결과 요약 출력
print(analyzer.get_analysis_summary(results))
```

## 내장 기능

### 성능 최적화

- 메모리 최적화: 데이터프레임 타입 다운캐스팅으로 메모리 사용량 감소
- 캐싱 시스템: 분석 결과 자동 캐싱으로 반복 분석 속도 향상
- 병렬 처리: 대용량 데이터 분석 시 멀티프로세싱 지원

### 분석 유형

- **수치형 분석**: 상관관계 분석, 피어슨 상관계수
- **범주형 분석**: Cramér's V, 카이제곱 검정, 연관규칙
- **혼합형 분석**: ANOVA, 효과 크기 (eta-squared)

### 출력 형식

- JSON 결과 파일 저장
- 콘솔 요약 출력
- 성능 메트릭 포함

## 참고 사항

- **프로젝트 구조**: 모든 combinations 관련 기능이 `combinations.py` 하나의 파일에 통합되어 있습니다.
- **빌드 호환성**: Windows .exe 실행파일로 빌드 가능하며, GUI 중심 설계로 실용성을 고려했습니다.
- **성능 최적화**: 대용량 데이터 처리를 위한 메모리 최적화 및 캐싱 시스템이 내장되어 있습니다.
- **선택적 의존성**: scipy, psutil 등은 선택사항이며, 없어도 기본 기능은 동작합니다.
- **글꼴 로딩**: Windows/macOS/Linux 환경에서 최선을 다하며, 찾지 못하면 시스템 기본 글꼴이 사용됩니다.
- **DSL 기능**: ML 모델(`model.pt`)과 토크나이저(`dsl_tokenizer.json`)가 포함되어 있습니다.
- **테마 전환**: 사용자 기본 설정을 유지하고 부드러운 전환을 제공합니다.
