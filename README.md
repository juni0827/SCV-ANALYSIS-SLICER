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

- **Dark/Light theme toggle**: Choose theme that fits user environment
- **Interactive data preview and filtering**: Interactive data preview and filtering
- **Advanced statistical analysis**: Advanced statistical analysis tools
- **Combinations Analysis**: Column relationship analysis (correlation, association rules, ANOVA)
- **Multiple visualization types**: Various visualization charts
- **Export capabilities**: Export data and reports

#### Combinations Analysis Tab Usage

#### Combinations Analysis Tab Usage

1. **Load Data**: First, load a CSV file
2. **Input DSL Tokens** (optional): Enter tokens to analyze specific columns only (e.g., C1,C2,C3)
3. **Set Top Results Count**: Configure number of results to display
4. **Run Analysis**: Click the 'Run Analysis' button
5. **Check Results**: Review correlation, association, and ANOVA results

### DSL Command Line Analysis (Extended Features)

Powerful ML-based DSL automated analysis tool:

```bash
# Basic interactive mode
python main_cli.py

# Specify tokens directly
python main_cli.py --tokens C1,C2,C6 --file data.csv

# Interactive mode (with file specification)
python main_cli.py --file data.csv --interactive

# View available token list
python main_cli.py --help-tokens

# Specify output file
python main_cli.py --tokens C2,C1,C6 --output my_analysis.py
```

#### Key Features

- **ML Prediction**: LSTM model predicts optimal analysis sequence
- **50+ Tokens**: C1~C50 + special tokens (SAVE, EXPORT, PROFILE)
- **Template Analysis**: Predefined analysis patterns for basic, statistical, visualization, correlation, etc.
- **Smart Code Generation**: Automatically generates executable Python code
- **Error Handling**: Includes exception handling for each analysis step

#### Analysis Templates

- `basic`: C2, C15, C6, C3, C1 (basic data exploration)
- `statistical`: C1, C14, C29, C41, C42, C43 (advanced statistics)
- `visualization`: C12, C23, C35, C47 (various visualizations)
- `correlation`: C8, C12, C25, C50 (correlation analysis)

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
# Standard build (fast, all features included)
python build.py

# Optimized build (slow, smaller file size)
python build.py --optimized

# Clean build files
python build.py --clean
```

The executable is created in the `dist/` folder:

- Windows: `CSV-Analyzer.exe`
- Linux/macOS: `CSV-Analyzer`

### Manual Build (Advanced)

```bash
# Install PyInstaller
pip install pyinstaller

# Standard build
python build.py

# Optimized build
python build.py --optimized
```

## Notes

- Font loading is best-effort across Windows/macOS/Linux. If no font is found, the system default is used.
- For very large CSVs, consider providing explicit `dtype` maps in `data_loader.load_csv` for optimal memory usage.
- The ML model (`model.pt`) and tokenizer (`dsl_tokenizer.json`) are included for DSL functionality.
- Executable build size may be large (~200MB) due to PyTorch and other dependencies.
- Theme switching preserves user preferences and provides smooth transitions.

## Korean Documentation

SCV Analysis Slicer is a large CSV file exploration, slicing, and visualization tool with ML-based analysis capabilities. It provides a modern Tkinter-based GUI and intelligent DSL command-line analysis.

### Key Features (Korean)

#### Core Analysis

- Modular architecture (`src/core`, `src/gui`, `src/dsl`, `src/utils`)
- Extended statistics: median, IQR, skewness, kurtosis, missing percentages
- Pagination for previewing large tables page by page (up to 1000 rows)
- Automatically selects the fastest CSV reader (`pyarrow` when available)
- Advanced combinations analysis for discovering relationships between columns

#### Visualization & UI

- Modern Tkinter-based GUI with dark/light theme switching
- Histogram, box, scatter, line, ECDF, heatmap, and correlation plots
- In-memory rendering pipeline for Matplotlib figures
- Interactive data exploration with filtering and slicing
- Export utilities for saving dataframes and analysis reports

#### ML-Powered DSL Analysis

- Domain Specific Language (DSL) for automated analysis workflows
- PyTorch-based LSTM model for intelligent code generation
- CLI support via `main_cli.py` for DSL-based analysis
- Automatic prediction of analysis sequences from user input

### Installation

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

### Usage

#### GUI Application

Launch the modern Tkinter-based interface with theme switching:

```bash
python -m src.gui.app
```

> **Note**: The canonical implementation is in the `src/` directory. Legacy root-level GUI files have been removed.

Features:

- Dark/light theme toggle
- Interactive data preview and filtering
- Advanced statistical analysis
- Various visualization types
- Data and report export capabilities

#### DSL Command Line Analysis

Use the intelligent DSL system for automated analysis:

```bash
python main_cli.py
```

Enter DSL tokens (e.g., `C1 C2 C6`) to automatically generate analysis code. The ML model predicts optimal analysis sequences and generates executable Python code.

#### Classic Command Line

```bash
python main_cli.py --help
```

### Advanced Combinations Analysis

The project's core feature, `combinations.py`, automatically analyzes relationships between data columns:

#### New Advanced Features

- **Parallel Processing**: High-performance analysis through ThreadPoolExecutor
- **Memory Optimization**: Automatic data type optimization and memory usage monitoring
- **Caching System**: Automatic caching of analysis results for faster repeat analysis
- **Text Analysis**: Statistical analysis of text columns
- **Real-time Monitoring**: Performance metrics collection and analysis
- **Visualization Recommendations**: Automatic chart recommendations based on analysis results

#### Analysis Features

- **Numeric × Numeric**: Pearson, Spearman, Kendall correlation coefficients + reliability assessment
- **Categorical × Categorical**: Lift analysis (association rule mining)
- **Categorical × Numeric**: ANOVA-based variance analysis + group statistics
- **Text Analysis**: Word frequency analysis and text statistics

#### Usage

**Basic Usage:**

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

**Integrated CLI Tool:**

```bash
# Basic usage
python combinations.py --file data.csv --output results.json

# Analysis using DSL tokens
python combinations.py --file data.csv --dsl-tokens C1,C2,C3 --verbose

# Using configuration file
python combinations.py --file data.csv --config analysis_config.json

# Advanced options
python combinations.py --file data.csv --max-cardinality 30 --top-k 15 --no-cache
```

**Using as Python Module:**

```python
from combinations import AdvancedCombinationsAnalyzer, AnalysisConfig

# Basic analysis
analyzer = AdvancedCombinationsAnalyzer()
results = analyzer.analyze_all_combinations(df)

# Custom configuration
config = AnalysisConfig(max_cardinality=30, top_k=15, parallel_processing=True)
analyzer = AdvancedCombinationsAnalyzer(config)
results = analyzer.analyze_all_combinations(df, dsl_tokens=['C1', 'C2'])

# Print results summary
print(analyzer.get_analysis_summary(results))
```

## Built-in Features

### Performance Optimization

- Memory optimization: Reduce memory usage through dataframe type downcasting
- Caching system: Automatic caching of analysis results for faster repeat analysis
- Parallel processing: Multiprocessing support for large data analysis

### Analysis Types

- **Numeric Analysis**: Correlation analysis, Pearson correlation coefficient
- **Categorical Analysis**: Cramér's V, chi-square test, association rules
- **Mixed Analysis**: ANOVA, effect size (eta-squared)

### Output Formats

- Save JSON result files
- Console summary output
- Including performance metrics

## Notes

- **Project Structure**: All combinations-related features are integrated into a single `combinations.py` file.
- **Build Compatibility**: Can be built as Windows .exe executable, designed for practicality with GUI focus.
- **Performance Optimization**: Built-in memory optimization and caching system for large data processing.
- **Optional Dependencies**: scipy, psutil, etc. are optional; basic functions work without them.
- Font loading is best-effort across Windows/macOS/Linux. If no font is found, the system default is used.
- DSL functionality includes the ML model (`model.pt`) and tokenizer (`dsl_tokenizer.json`).
- Theme switching preserves user preferences and provides smooth transitions.
