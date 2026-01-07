#!/usr/bin/env python3
"""
통합 Combinations analysis Module (combinations.py)

이 Module은 Data프레임의 Column 간 관계를 종합적으로 분석합니다.
- 수치형 Column 간 Correlation analysis (Pearson, Spearman)
- 범주형 Column 간 연관규칙 분석 (Cramér's V, Theil's U, 카이제곱 검정)
- 수치형-범주형 간 ANOVA 및 Kruskal-Wallis 분석
- Performance 모니터링 및 고도화된 Memory Optimization
- Joblib based Parallel Processing 및 캐싱

Usage:
    # Python Module로 Use
    from combinations import AdvancedCombinationsAnalyzer
    analyzer = AdvancedCombinationsAnalyzer()
    results = analyzer.analyze_all_combinations(df)

    # CLI로 Use
    python combinations.py --file data.csv --output results.json
"""

import argparse
import hashlib
import json
import logging
import sys
import time
import gzip
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Required/Optional적 의존성
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from scipy.stats import chi2_contingency, f_oneway, kruskal, spearmanr, entropy

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from joblib import Parallel, delayed, Memory

    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

# Logging Configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class AnalysisConfig:
    """Analysis configuration Class"""

    max_cardinality: int = 50
    top_k: int = 20
    sample_cap: int = 200_000
    min_sample_size: int = 30
    correlation_threshold: float = 0.3
    lift_threshold: float = 1.5
    eta2_threshold: float = 0.1
    parallel_processing: bool = True
    n_jobs: int = -1  # -1: 모든 CPU 코어 Use
    enable_caching: bool = True
    cache_dir: str = ".analysis_cache"
    memory_optimization: bool = True
    advanced_stats: bool = True  # Theil's U, Spearman 등 고급 Statistics Use 여부


@dataclass
class PerformanceMetrics:
    """Performance Metrics Class"""

    start_time: float
    end_time: float = None
    memory_usage: Dict[str, float] = None
    cpu_usage: float = None
    operation_count: int = 0
    error_count: int = 0

    @property
    def duration(self) -> float:
        return (self.end_time - self.start_time) if self.end_time else 0


class PerformanceMonitor:
    """Performance 모니터링 Class"""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []

    @contextmanager
    def track_operation(self, operation_name: str):
        """Task 수Row 시간 추적"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used if HAS_PSUTIL else 0

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used if HAS_PSUTIL else 0

            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                memory_usage=(
                    {
                        "start": start_memory,
                        "end": end_memory,
                        "delta": end_memory - start_memory,
                    }
                    if HAS_PSUTIL
                    else {"start": 0, "end": 0, "delta": 0}
                ),
                cpu_usage=psutil.cpu_percent(interval=0.1) if HAS_PSUTIL else 0,
            )

            self.metrics_history.append(metrics)
            logger.info(f"{operation_name} 완료: {metrics.duration:.2f}초")

    def get_performance_report(self) -> Dict[str, Any]:
        """Performance 보고서 Create"""
        if not self.metrics_history:
            return {"error": "no_metrics_available"}

        total_duration = sum(m.duration for m in self.metrics_history)
        avg_memory_delta = sum(
            m.memory_usage["delta"] for m in self.metrics_history
        ) / len(self.metrics_history)

        return {
            "total_operations": len(self.metrics_history),
            "total_duration": total_duration,
            "average_duration": total_duration / len(self.metrics_history),
            "average_memory_delta": avg_memory_delta,
            "memory_efficiency": (
                "good" if avg_memory_delta < 100 * 1024 * 1024 else "needs_optimization"
            ),
        }


class MemoryOptimizer:
    """고도화된 Memory Optimization Class"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Data프레임 Memory Optimization (Downcasting & Smart Categorization)"""
        optimized_df = df.copy()

        # 1. 수치형 Data 다운캐스팅
        for col in optimized_df.select_dtypes(include=["int", "float"]).columns:
            try:
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast="integer")
            except:
                pass
            try:
                if optimized_df[col].dtype == "float64":
                    optimized_df[col] = pd.to_numeric(
                        optimized_df[col], downcast="float"
                    )
            except:
                pass

        # 2. 객체형(문자열) Data Optimization
        for col in optimized_df.select_dtypes(include=["object"]).columns:
            try:
                num_unique = optimized_df[col].nunique()
                num_total = len(optimized_df)

                # 카테고리 변환 조건: UniqueValue Ratio이 Less than 50%이고, UniqueValue이 아주 많지 않은 경우
                if num_unique / num_total < 0.5:
                    # Add 조건: Average 문자열 길이가 짧은 경우에만 변환 (Memory 오버헤드 방지)
                    # 샘플링하여 Average 길이 측정
                    sample = optimized_df[col].dropna().sample(min(1000, num_total))
                    if sample.empty:
                        continue

                    avg_len = sample.map(str).map(len).mean()

                    # 문자열이 길거나 반복이 많으면 카테고리가 유리
                    if avg_len > 2 or num_unique < 1000:
                        optimized_df[col] = optimized_df[col].astype("category")
            except Exception as e:
                logger.warning(f"컬럼 {col} 최적화 중 오류: {e}")
                continue

        return optimized_df

    @staticmethod
    def get_memory_usage_info(df: pd.DataFrame) -> Dict[str, Any]:
        """Memory Use량 Information"""
        memory_usage = df.memory_usage(deep=True)
        total_memory = memory_usage.sum()

        return {
            "total_memory_mb": total_memory / 1024 / 1024,
            "memory_per_column": {
                col: usage / 1024 / 1024 for col, usage in memory_usage.items()
            },
            "largest_column": memory_usage.idxmax(),
            "optimization_potential": MemoryOptimizer._calculate_optimization_potential(
                df
            ),
        }

    @staticmethod
    def _calculate_optimization_potential(df: pd.DataFrame) -> str:
        """Optimization 잠재력 계산"""
        try:
            original_memory = df.memory_usage(deep=True).sum()
            # 실제 변환하지 않고 추정만 하거나, 샘플로 Test
            return "high" if original_memory > 100 * 1024 * 1024 else "low"
        except Exception:
            return "unknown"


class AnalysisCache:
    """압축 및 Pickle을 Support하는 고급 Cache Class"""

    def __init__(self, cache_dir: str = ".analysis_cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age_hours = max_age_hours

    def get_cache_key(
        self, df_hash: str, analysis_type: str, params: Dict[str, Any]
    ) -> str:
        """Cache 키 Create"""
        params_str = json.dumps(params, sort_keys=True, default=str)
        key = hashlib.md5(
            f"{df_hash}_{analysis_type}_{params_str}".encode()
        ).hexdigest()
        return key

    def get(self, key: str) -> Optional[Any]:
        """Cache에서 Data Import (gzip + pickle)"""
        cache_file = self.cache_dir / f"{key}.pkl.gz"

        if not cache_file.exists():
            return None

        # Cache File 나이 Confirmation
        file_age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if file_age_hours > self.max_age_hours:
            try:
                cache_file.unlink()
            except:
                pass
            return None

        try:
            with gzip.open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"캐시 로드 실패: {e}")
            return None

    def set(self, key: str, data: Any):
        """Data를 Cache에 Save (gzip + pickle)"""
        cache_file = self.cache_dir / f"{key}.pkl.gz"
        try:
            with gzip.open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

    def clear_expired(self):
        """만료된 Cache File들 Cleanup"""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.pkl.gz"):
            try:
                file_age_hours = (current_time - cache_file.stat().st_mtime) / 3600
                if file_age_hours > self.max_age_hours:
                    cache_file.unlink()
            except:
                pass


# --- Statistical analysis Helper Function (Parallel Processing를 for Class 외부로 분리) ---


def calculate_theils_u(x, y):
    """Theil's U (Uncertainty Coefficient) 계산 - 비대칭 연관성"""
    s_xy = conditional_entropy(x, y)
    x_counter = pd.Series(x).value_counts()
    total_occurrences = x_counter.sum()
    p_x = x_counter / total_occurrences
    s_x = -np.sum(p_x * np.log(p_x))
    if s_x == 0:
        return 0
    return (s_x - s_xy) / s_x


def conditional_entropy(x, y):
    """조건부 엔트로피 H(X|Y)"""
    y_counter = pd.Series(y).value_counts()
    xy_counter = pd.Series(list(zip(x, y))).value_counts()
    total_occurrences = y_counter.sum()
    entropy = 0
    for xy, count in xy_counter.items():
        p_xy = count / total_occurrences
        p_y = y_counter[xy[1]] / total_occurrences
        entropy += p_xy * np.log(p_y / p_xy)
    return -entropy


def process_categorical_pair(df_subset, col1, col2, config_dict):
    """범주형 쌍 분석 (Parallel Processing용)"""
    try:
        crosstab = pd.crosstab(df_subset[col1], df_subset[col2])

        # 카이제곱 검정
        if HAS_SCIPY:
            chi2, p_value, dof, expected = chi2_contingency(crosstab)
            n = crosstab.sum().sum()
            min_dim = min(crosstab.shape) - 1
            cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

            # Theil's U (비대칭)
            theils_u = calculate_theils_u(df_subset[col1], df_subset[col2])
        else:
            chi2, p_value, cramers_v, theils_u = 0, 1, 0, 0

        # 연관 규칙 (Lift)
        rules = []  # _calculate_association_rules 로직 인라인화 or 간소화
        # (Performance을 for 여기서는 생략하거나 필요시 Add)

        return {
            "column1": col1,
            "column2": col2,
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "cramers_v": float(cramers_v),
            "theils_u": float(theils_u),
            "significant": p_value < 0.05,
        }
    except Exception as e:
        return None


def process_mixed_pair(df_subset, num_col, cat_col, config_dict):
    """혼합형 쌍 분석 (Parallel Processing용)"""
    try:
        groups = [group[num_col].values for name, group in df_subset.groupby(cat_col)]
        groups = [g for g in groups if len(g) >= config_dict["min_sample_size"]]

        if len(groups) < 2:
            return None

        if HAS_SCIPY:
            # ANOVA
            f_stat, p_value = f_oneway(*groups)
            # Kruskal-Wallis (비모수)
            k_stat, k_p_value = kruskal(*groups)
        else:
            f_stat, p_value, k_stat, k_p_value = 0, 1, 0, 1

        # Eta Squared
        # 간단한 계산
        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)
        sst = np.sum((all_data - grand_mean) ** 2)
        ssb = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
        eta_squared = ssb / sst if sst > 0 else 0

        return {
            "numerical_column": num_col,
            "categorical_column": cat_col,
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "kruskal_statistic": float(k_stat),
            "kruskal_p_value": float(k_p_value),
            "eta_squared": float(eta_squared),
            "significant": p_value < 0.05,
        }
    except Exception:
        return None


class AdvancedCombinationsAnalyzer:
    """통합 고급 Combinations analysis기 - 모든 분석 Feature을 Include한 메인 Class"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.performance_monitor = PerformanceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        self.cache = (
            AnalysisCache(self.config.cache_dir) if self.config.enable_caching else None
        )

        logger.info(f"AdvancedCombinationsAnalyzer 초기화 완료")
        logger.info(
            f"  - 병렬 처리: {self.config.parallel_processing} (Jobs: {self.config.n_jobs})"
        )
        logger.info(f"  - 메모리 최적화: {self.config.memory_optimization}")
        logger.info(f"  - 고급 통계: {self.config.advanced_stats}")

    def _get_dataframe_hash(self, df: pd.DataFrame) -> str:
        """Data프레임 Hash Create"""
        try:
            # Data의 Some만 샘플링하여 Hash Create (속도 Optimization)
            sample = df.sample(min(100, len(df)), random_state=42)
            info_str = f"{df.shape}_{list(df.columns)}_{sample.values.tobytes()}"
            return hashlib.md5(info_str.encode()).hexdigest()[:16]
        except Exception:
            return str(hash(str(df.shape)))

    def _optimize_dataframe_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요시 Data프레임 Optimization"""
        if not self.config.memory_optimization:
            return df

        with self.performance_monitor.track_operation("dataframe_optimization"):
            return self.memory_optimizer.optimize_dataframe(df)

    def _sample_dataframe_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """큰 Data셋 샘플링"""
        if len(df) <= self.config.sample_cap:
            return df

        logger.info(
            f"데이터셋이 너무 큽니다 ({len(df):,}행). {self.config.sample_cap:,}행으로 샘플링합니다."
        )
        return df.sample(n=self.config.sample_cap, random_state=42)

    def analyze_all_combinations(
        self, df: pd.DataFrame, dsl_tokens: List[str] = None
    ) -> Dict[str, Any]:
        """모든 Combinations analysis 수Row"""
        with self.performance_monitor.track_operation("full_analysis"):
            # Data프레임 전Processing
            df = self._optimize_dataframe_if_needed(df)
            df = self._sample_dataframe_if_needed(df)

            # DSL token이 제공된 경우 해당 Column만 분석
            if dsl_tokens:
                available_columns = [
                    col
                    for col in df.columns
                    if any(token in col for token in dsl_tokens)
                ]
                if available_columns:
                    df = df[available_columns]
                    logger.info(
                        f"DSL 토큰 기반 컬럼 필터링: {len(available_columns)}개 컬럼"
                    )

            results = {
                "metadata": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "config": asdict(self.config),
                },
                "numerical_combinations": self._analyze_numerical_combinations(df),
                "categorical_combinations": self._analyze_categorical_combinations(df),
                "mixed_combinations": self._analyze_mixed_combinations(df),
            }

            # Performance Information Add
            results["performance"] = self.performance_monitor.get_performance_report()

            return results

    def _analyze_numerical_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """수치형 Column 간 Combinations analysis (Pearson & Spearman)"""
        numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numerical_columns) < 2:
            return {"error": "수치형 컬럼이 2개 미만입니다"}

        with self.performance_monitor.track_operation("numerical_analysis"):
            # Cache Confirmation
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(df[numerical_columns])
                cache_key = self.cache.get_cache_key(
                    df_hash, "numerical", {"columns": numerical_columns}
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result

            # Pearson 상관관계
            corr_matrix = df[numerical_columns].corr(method="pearson")

            # Spearman 상관관계 (비선형 관계 탐지)
            if self.config.advanced_stats:
                spearman_matrix = df[numerical_columns].corr(method="spearman")
            else:
                spearman_matrix = corr_matrix

            strong_correlations = []
            for i in range(len(numerical_columns)):
                for j in range(i + 1, len(numerical_columns)):
                    col1, col2 = numerical_columns[i], numerical_columns[j]
                    p_corr = corr_matrix.iloc[i, j]
                    s_corr = spearman_matrix.iloc[i, j]

                    # 둘 중 하나라도 임계Value을 넘으면 기록
                    max_corr = max(abs(p_corr), abs(s_corr))

                    if max_corr >= self.config.correlation_threshold:
                        strong_correlations.append(
                            {
                                "column1": col1,
                                "column2": col2,
                                "correlation": float(p_corr),
                                "spearman_correlation": float(s_corr),
                                "strength": "강함" if max_corr >= 0.7 else "보통",
                                "type": (
                                    "선형"
                                    if abs(p_corr) >= abs(s_corr)
                                    else "비선형(단조)"
                                ),
                            }
                        )

            strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

            result = {
                "total_combinations": len(numerical_columns)
                * (len(numerical_columns) - 1)
                // 2,
                "strong_correlations_count": len(strong_correlations),
                "strong_correlations": strong_correlations[: self.config.top_k],
                "summary": {
                    "max_correlation": (
                        float(corr_matrix.abs().max().max())
                        if not corr_matrix.empty
                        else 0
                    ),
                },
            }

            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def _analyze_categorical_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """범주형 Column 간 Combinations analysis (Parallel Processing 적용)"""
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # 카디널리티 Filter링
        categorical_columns = [
            col
            for col in categorical_columns
            if df[col].nunique() <= self.config.max_cardinality
        ]

        if len(categorical_columns) < 2:
            return {"error": "적절한 범주형 컬럼이 2개 미만입니다"}

        with self.performance_monitor.track_operation("categorical_analysis"):
            # Cache Confirmation
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(df[categorical_columns])
                cache_key = self.cache.get_cache_key(
                    df_hash, "categorical", {"columns": categorical_columns}
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result

            pairs = []
            for i in range(len(categorical_columns)):
                for j in range(i + 1, len(categorical_columns)):
                    pairs.append((categorical_columns[i], categorical_columns[j]))

            # Parallel Processing Execution
            if HAS_JOBLIB and self.config.parallel_processing:
                results = Parallel(n_jobs=self.config.n_jobs)(
                    delayed(process_categorical_pair)(
                        df[[p[0], p[1]]], p[0], p[1], asdict(self.config)
                    )
                    for p in pairs
                )
            else:
                results = [
                    process_categorical_pair(df, p[0], p[1], asdict(self.config))
                    for p in pairs
                ]

            # None Remove 및 Sort
            associations = [r for r in results if r is not None]
            associations.sort(key=lambda x: x["cramers_v"], reverse=True)

            result = {
                "total_combinations": len(pairs),
                "significant_associations_count": len(
                    [a for a in associations if a["significant"]]
                ),
                "associations": associations[: self.config.top_k],
                "summary": {
                    "max_cramers_v": (
                        float(max([a["cramers_v"] for a in associations]))
                        if associations
                        else 0
                    ),
                },
            }

            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def _analyze_mixed_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """수치형-범주형 간 Combinations analysis (Parallel Processing 적용)"""
        numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        categorical_columns = [
            col
            for col in categorical_columns
            if 2 <= df[col].nunique() <= self.config.max_cardinality
        ]

        if not numerical_columns or not categorical_columns:
            return {"error": "수치형 또는 범주형 컬럼이 부족합니다"}

        with self.performance_monitor.track_operation("mixed_analysis"):
            # Cache Confirmation
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(
                    df[numerical_columns + categorical_columns]
                )
                cache_key = self.cache.get_cache_key(
                    df_hash,
                    "mixed",
                    {"num": numerical_columns, "cat": categorical_columns},
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result

            pairs = []
            for num in numerical_columns:
                for cat in categorical_columns:
                    pairs.append((num, cat))

            # Parallel Processing Execution
            if HAS_JOBLIB and self.config.parallel_processing:
                results = Parallel(n_jobs=self.config.n_jobs)(
                    delayed(process_mixed_pair)(
                        df[[p[0], p[1]]], p[0], p[1], asdict(self.config)
                    )
                    for p in pairs
                )
            else:
                results = [
                    process_mixed_pair(df, p[0], p[1], asdict(self.config))
                    for p in pairs
                ]

            anova_results = [r for r in results if r is not None]
            anova_results.sort(key=lambda x: x["eta_squared"], reverse=True)

            result = {
                "total_combinations": len(pairs),
                "significant_results_count": len(
                    [r for r in anova_results if r["significant"]]
                ),
                "anova_results": anova_results[: self.config.top_k],
                "summary": {
                    "max_eta_squared": (
                        float(max([r["eta_squared"] for r in anova_results]))
                        if anova_results
                        else 0
                    ),
                },
            }

            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def get_analysis_summary(self, results: Dict[str, Any]) -> str:
        """Analysis results 요약 Create"""
        summary_lines = [
            "=== 고급 조합 분석 결과 요약 ===",
            f"분석 시간: {results['metadata']['analysis_timestamp']}",
            f"전체 데이터: {results['metadata']['total_rows']:,}행 × {results['metadata']['total_columns']}열",
            "",
        ]

        # 수치형 분석 요약
        if (
            "numerical_combinations" in results
            and "error" not in results["numerical_combinations"]
        ):
            num_results = results["numerical_combinations"]
            summary_lines.extend(
                [
                    f"수치형 컬럼 분석:",
                    f"  - 전체 조합: {num_results['total_combinations']}개",
                    f"  - 강한 상관관계: {num_results['strong_correlations_count']}개",
                    f"  - 최대 상관계수: {num_results['summary']['max_correlation']:.3f}",
                    "",
                ]
            )

        # 범주형 분석 요약
        if (
            "categorical_combinations" in results
            and "error" not in results["categorical_combinations"]
        ):
            cat_results = results["categorical_combinations"]
            summary_lines.extend(
                [
                    f"범주형 컬럼 분석:",
                    f"  - 전체 조합: {cat_results['total_combinations']}개",
                    f"  - 유의한 연관성: {cat_results['significant_associations_count']}개",
                    f"  - 최대 Cramér's V: {cat_results['summary']['max_cramers_v']:.3f}",
                    "",
                ]
            )

        # 혼합형 분석 요약
        if (
            "mixed_combinations" in results
            and "error" not in results["mixed_combinations"]
        ):
            mixed_results = results["mixed_combinations"]
            summary_lines.extend(
                [
                    f"혼합형 분석 (ANOVA/Kruskal):",
                    f"  - 전체 조합: {mixed_results['total_combinations']}개",
                    f"  - 유의한 결과: {mixed_results['significant_results_count']}개",
                    f"  - 최대 효과 크기: {mixed_results['summary']['max_eta_squared']:.3f}",
                    "",
                ]
            )

        # Performance Information
        if "performance" in results:
            perf = results["performance"]
            summary_lines.extend(
                [
                    f"성능 정보:",
                    f"  - 총 작업 수: {perf.get('total_operations', 0)}개",
                    f"  - 총 실행 시간: {perf.get('total_duration', 0):.2f}초",
                    f"  - 메모리 효율성: {perf.get('memory_efficiency', 'unknown')}",
                ]
            )

        return "\n".join(summary_lines)


# CLI Feature 통합
def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description="고급 조합 분석 도구")
    parser.add_argument("--file", "-f", required=True, help="분석할 데이터 파일 경로")
    parser.add_argument("--output", "-o", help="결과 저장 경로 (선택사항)")
    parser.add_argument("--config", "-c", help="설정 파일 경로")
    parser.add_argument("--dsl-tokens", help="DSL 토큰 (쉼표로 구분)")
    parser.add_argument(
        "--max-cardinality", type=int, default=50, help="최대 카디널리티"
    )
    parser.add_argument("--top-k", type=int, default=20, help="상위 K개 결과")
    parser.add_argument("--no-cache", action="store_true", help="캐시 비활성화")
    parser.add_argument("--no-parallel", action="store_true", help="병렬 처리 비활성화")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그 출력")

    return parser.parse_args()


def load_config_from_file(config_path: str) -> AnalysisConfig:
    """Configuration File에서 Configuration Load"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return AnalysisConfig(**config_data)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return AnalysisConfig()


def setup_logging(verbose: bool = False):
    """Logging Configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("combinations_analysis.log", encoding="utf-8"),
        ],
    )


def main():
    """CLI 메인 Function"""
    args = parse_arguments()
    setup_logging(args.verbose)

    try:
        # Configuration Load
        if args.config:
            config = load_config_from_file(args.config)
        else:
            config = AnalysisConfig(
                max_cardinality=args.max_cardinality,
                top_k=args.top_k,
                enable_caching=not args.no_cache,
                parallel_processing=not args.no_parallel,
            )

        # Load data
        logger.info(f"데이터 파일 로드: {args.file}")
        if args.file.endswith(".csv"):
            df = pd.read_csv(args.file)
        elif args.file.endswith(".xlsx"):
            df = pd.read_excel(args.file)
        else:
            raise ValueError("지원되지 않는 파일 형식 (CSV, XLSX만 지원)")

        # DSL token 파싱
        dsl_tokens = None
        if args.dsl_tokens:
            dsl_tokens = [token.strip() for token in args.dsl_tokens.split(",")]
            logger.info(f"DSL 토큰: {dsl_tokens}")

        # Run analysis
        analyzer = AdvancedCombinationsAnalyzer(config)
        results = analyzer.analyze_all_combinations(df, dsl_tokens)

        # Result Output
        print(analyzer.get_analysis_summary(results))

        # Result Save
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"결과 저장 완료: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"분석 실행 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
