#!/usr/bin/env python3
"""
통합 조합 분석 모듈 (combinations.py)

이 모듈은 데이터프레임의 컬럼 간 관계를 종합적으로 분석합니다.
- 수치형 컬럼 간 상관관계 분석
- 범주형 컬럼 간 연관규칙 분석 (Cramér's V, 카이제곱 검정)
- 수치형-범주형 간 ANOVA 분석
- 성능 모니터링 및 메모리 최적화
- CLI 인터페이스 제공

사용법:
    # Python 모듈로 사용
    from combinations import AdvancedCombinationsAnalyzer
    analyzer = AdvancedCombinationsAnalyzer()
    results = analyzer.analyze_all_combinations(df)

    # CLI로 사용
    python combinations.py --file data.csv --output results.json
    python combinations.py --file data.csv --dsl-tokens C1,C2,C3 --verbose
"""

import argparse
import hashlib
import json
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# 선택적 의존성
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from scipy.stats import chi2_contingency, f_oneway

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class AnalysisConfig:
    """분석 설정 클래스"""

    max_cardinality: int = 50
    top_k: int = 20
    sample_cap: int = 200_000
    min_sample_size: int = 30
    correlation_threshold: float = 0.3
    lift_threshold: float = 1.5
    eta2_threshold: float = 0.1
    parallel_processing: bool = True
    max_workers: int = 4
    enable_caching: bool = True
    cache_dir: str = ".analysis_cache"
    memory_optimization: bool = True


@dataclass
class PerformanceMetrics:
    """성능 메트릭 클래스"""

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
    """성능 모니터링 클래스"""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []

    @contextmanager
    def track_operation(self, operation_name: str):
        """작업 수행 시간 추적"""
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
        """성능 보고서 생성"""
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
                "good" if avg_memory_delta < 50 * 1024 * 1024 else "needs_optimization"
            ),
        }


class MemoryOptimizer:
    """메모리 최적화 클래스"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 메모리 최적화"""
        optimized_df = df.copy()

        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype

            try:
                if col_type == "object":
                    # 범주형 데이터로 변환 가능한지 확인
                    if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                        optimized_df[col] = optimized_df[col].astype("category")
                elif col_type == "int64":
                    # 정수 타입 다운캐스팅
                    col_min, col_max = optimized_df[col].min(), optimized_df[col].max()
                    if col_min >= 0:
                        if col_max < 256:
                            optimized_df[col] = optimized_df[col].astype("uint8")
                        elif col_max < 65536:
                            optimized_df[col] = optimized_df[col].astype("uint16")
                        elif col_max < 4294967296:
                            optimized_df[col] = optimized_df[col].astype("uint32")
                    else:
                        if col_min > -129 and col_max < 128:
                            optimized_df[col] = optimized_df[col].astype("int8")
                        elif col_min > -32769 and col_max < 32768:
                            optimized_df[col] = optimized_df[col].astype("int16")
                        elif col_min > -2147483649 and col_max < 2147483648:
                            optimized_df[col] = optimized_df[col].astype("int32")
                elif col_type == "float64":
                    # 실수 타입 다운캐스팅
                    optimized_df[col] = optimized_df[col].astype("float32")
            except Exception as e:
                logger.warning(f"컬럼 {col} 최적화 실패: {e}")
                continue

        return optimized_df

    @staticmethod
    def get_memory_usage_info(df: pd.DataFrame) -> Dict[str, Any]:
        """메모리 사용량 정보"""
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
        """최적화 잠재력 계산"""
        try:
            original_memory = df.memory_usage(deep=True).sum()
            optimized_df = MemoryOptimizer.optimize_dataframe(df)
            optimized_memory = optimized_df.memory_usage(deep=True).sum()

            savings_percent = (
                (original_memory - optimized_memory) / original_memory * 100
            )

            if savings_percent > 30:
                return "high"
            elif savings_percent > 15:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"


class AnalysisCache:
    """분석 결과 캐시 클래스"""

    def __init__(self, cache_dir: str = ".analysis_cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age_hours = max_age_hours

    def get_cache_key(
        self, df_hash: str, analysis_type: str, params: Dict[str, Any]
    ) -> str:
        """캐시 키 생성"""
        params_str = json.dumps(params, sort_keys=True)
        key = hashlib.md5(
            f"{df_hash}_{analysis_type}_{params_str}".encode()
        ).hexdigest()
        return key

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # 캐시 파일 나이 확인
        file_age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if file_age_hours > self.max_age_hours:
            cache_file.unlink()
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, key: str, data: Any):
        """데이터를 캐시에 저장"""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

    def clear_expired(self):
        """만료된 캐시 파일들 정리"""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            file_age_hours = (current_time - cache_file.stat().st_mtime) / 3600
            if file_age_hours > self.max_age_hours:
                cache_file.unlink()


class AdvancedCombinationsAnalyzer:
    """통합 고급 조합 분석기 - 모든 분석 기능을 포함한 메인 클래스"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.performance_monitor = PerformanceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        self.cache = (
            AnalysisCache(self.config.cache_dir) if self.config.enable_caching else None
        )

        logger.info(f"AdvancedCombinationsAnalyzer 초기화 완료")
        logger.info(f"  - 병렬 처리: {self.config.parallel_processing}")
        logger.info(f"  - 메모리 최적화: {self.config.memory_optimization}")
        logger.info(f"  - 캐싱: {self.config.enable_caching}")

    def _get_dataframe_hash(self, df: pd.DataFrame) -> str:
        """데이터프레임 해시 생성"""
        try:
            info_str = f"{df.shape}_{list(df.columns)}_{df.dtypes.to_dict()}"
            return hashlib.md5(info_str.encode()).hexdigest()[:16]
        except Exception:
            return str(hash(str(df.shape)))

    def _optimize_dataframe_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요시 데이터프레임 최적화"""
        if not self.config.memory_optimization:
            return df

        with self.performance_monitor.track_operation("dataframe_optimization"):
            return self.memory_optimizer.optimize_dataframe(df)

    def _sample_dataframe_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        """큰 데이터셋 샘플링"""
        if len(df) <= self.config.sample_cap:
            return df

        logger.info(
            f"데이터셋이 너무 큽니다 ({len(df):,}행). {self.config.sample_cap:,}행으로 샘플링합니다."
        )
        return df.sample(n=self.config.sample_cap, random_state=42)

    def analyze_all_combinations(
        self, df: pd.DataFrame, dsl_tokens: List[str] = None
    ) -> Dict[str, Any]:
        """모든 조합 분석 수행"""
        with self.performance_monitor.track_operation("full_analysis"):
            # 데이터프레임 전처리
            df = self._optimize_dataframe_if_needed(df)
            df = self._sample_dataframe_if_needed(df)

            # DSL 토큰이 제공된 경우 해당 컬럼만 분석
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

            # 성능 정보 추가
            results["performance"] = self.performance_monitor.get_performance_report()

            return results

    def _analyze_numerical_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """수치형 컬럼 간 조합 분석"""
        numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numerical_columns) < 2:
            return {"error": "수치형 컬럼이 2개 미만입니다"}

        with self.performance_monitor.track_operation("numerical_analysis"):
            # 캐시 확인
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(df[numerical_columns])
                cache_key = self.cache.get_cache_key(
                    df_hash, "numerical", {"columns": numerical_columns}
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logger.info("수치형 분석 캐시 결과 사용")
                    return cached_result

            # 상관관계 분석
            correlation_matrix = df[numerical_columns].corr()

            # 강한 상관관계 찾기
            strong_correlations = []
            for i in range(len(numerical_columns)):
                for j in range(i + 1, len(numerical_columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) >= self.config.correlation_threshold:
                        strong_correlations.append(
                            {
                                "column1": numerical_columns[i],
                                "column2": numerical_columns[j],
                                "correlation": float(corr_value),
                                "strength": (
                                    "강함" if abs(corr_value) >= 0.7 else "보통"
                                ),
                                "direction": (
                                    "양의 상관관계"
                                    if corr_value > 0
                                    else "음의 상관관계"
                                ),
                            }
                        )

            # 상관관계 순으로 정렬
            strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

            result = {
                "total_combinations": len(numerical_columns)
                * (len(numerical_columns) - 1)
                // 2,
                "strong_correlations_count": len(strong_correlations),
                "strong_correlations": strong_correlations[: self.config.top_k],
                "correlation_matrix": correlation_matrix.round(3).to_dict(),
                "summary": {
                    "max_correlation": (
                        float(correlation_matrix.abs().max().max())
                        if len(strong_correlations) > 0
                        else 0
                    ),
                    "avg_correlation": float(correlation_matrix.abs().mean().mean()),
                    "highly_correlated_pairs": len(
                        [c for c in strong_correlations if abs(c["correlation"]) >= 0.7]
                    ),
                },
            }

            # 캐시 저장
            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def _analyze_categorical_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """범주형 컬럼 간 조합 분석"""
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # 카디널리티가 너무 높은 컬럼 제외
        categorical_columns = [
            col
            for col in categorical_columns
            if df[col].nunique() <= self.config.max_cardinality
        ]

        if len(categorical_columns) < 2:
            return {"error": "적절한 범주형 컬럼이 2개 미만입니다"}

        with self.performance_monitor.track_operation("categorical_analysis"):
            # 캐시 확인
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(df[categorical_columns])
                cache_key = self.cache.get_cache_key(
                    df_hash, "categorical", {"columns": categorical_columns}
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logger.info("범주형 분석 캐시 결과 사용")
                    return cached_result

            associations = []

            for i in range(len(categorical_columns)):
                for j in range(i + 1, len(categorical_columns)):
                    col1, col2 = categorical_columns[i], categorical_columns[j]

                    try:
                        # 교차표 생성
                        crosstab = pd.crosstab(df[col1], df[col2])

                        # 카이제곱 검정 (scipy가 있는 경우만)
                        if HAS_SCIPY:
                            chi2, p_value, dof, expected = chi2_contingency(crosstab)

                            # Cramér's V 계산
                            n = crosstab.sum().sum()
                            cramers_v = np.sqrt(chi2 / (n * (min(crosstab.shape) - 1)))
                        else:
                            chi2, p_value, cramers_v = 0, 1, 0

                        # 연관 규칙 계산
                        rules = self._calculate_association_rules(crosstab)

                        association = {
                            "column1": col1,
                            "column2": col2,
                            "chi2_statistic": float(chi2),
                            "p_value": float(p_value),
                            "cramers_v": float(cramers_v),
                            "association_strength": self._get_association_strength(
                                cramers_v
                            ),
                            "significant": p_value < 0.05,
                            "top_rules": rules[:5],
                        }

                        associations.append(association)

                    except Exception as e:
                        logger.warning(f"범주형 분석 오류 ({col1} vs {col2}): {e}")
                        continue

            # 강도순으로 정렬
            associations.sort(key=lambda x: x["cramers_v"], reverse=True)

            result = {
                "total_combinations": len(categorical_columns)
                * (len(categorical_columns) - 1)
                // 2,
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
                    "avg_cramers_v": (
                        float(np.mean([a["cramers_v"] for a in associations]))
                        if associations
                        else 0
                    ),
                    "strong_associations": len(
                        [a for a in associations if a["cramers_v"] >= 0.3]
                    ),
                },
            }

            # 캐시 저장
            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def _analyze_mixed_combinations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """수치형-범주형 간 조합 분석 (ANOVA)"""
        numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # 카디널리티 제한
        categorical_columns = [
            col
            for col in categorical_columns
            if 2 <= df[col].nunique() <= self.config.max_cardinality
        ]

        if not numerical_columns or not categorical_columns:
            return {"error": "수치형 또는 범주형 컬럼이 부족합니다"}

        with self.performance_monitor.track_operation("mixed_analysis"):
            # 캐시 확인
            cache_key = None
            if self.cache:
                df_hash = self._get_dataframe_hash(
                    df[numerical_columns + categorical_columns]
                )
                cache_key = self.cache.get_cache_key(
                    df_hash,
                    "mixed",
                    {
                        "numerical": numerical_columns,
                        "categorical": categorical_columns,
                    },
                )
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logger.info("혼합형 분석 캐시 결과 사용")
                    return cached_result

            anova_results = []

            for num_col in numerical_columns:
                for cat_col in categorical_columns:
                    try:
                        # 각 그룹별 데이터 준비
                        groups = df.groupby(cat_col)[num_col].apply(list)

                        # 최소 샘플 크기 확인
                        if all(
                            len(group) >= self.config.min_sample_size
                            for group in groups
                        ):
                            if HAS_SCIPY:
                                f_stat, p_value = f_oneway(*groups)
                            else:
                                f_stat, p_value = 0, 1

                            # 효과 크기 (eta-squared) 계산
                            eta_squared = self._calculate_eta_squared(
                                df, num_col, cat_col
                            )

                            # 그룹별 통계
                            group_stats = (
                                df.groupby(cat_col)[num_col]
                                .agg(["mean", "std", "count"])
                                .round(3)
                            )

                            anova_result = {
                                "numerical_column": num_col,
                                "categorical_column": cat_col,
                                "f_statistic": float(f_stat),
                                "p_value": float(p_value),
                                "eta_squared": float(eta_squared),
                                "effect_size": self._get_effect_size(eta_squared),
                                "significant": p_value < 0.05,
                                "group_stats": group_stats.to_dict(),
                            }

                            anova_results.append(anova_result)

                    except Exception as e:
                        logger.warning(f"ANOVA 분석 오류 ({num_col} vs {cat_col}): {e}")
                        continue

            # 효과 크기순으로 정렬
            anova_results.sort(key=lambda x: x["eta_squared"], reverse=True)

            result = {
                "total_combinations": len(numerical_columns) * len(categorical_columns),
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
                    "avg_eta_squared": (
                        float(np.mean([r["eta_squared"] for r in anova_results]))
                        if anova_results
                        else 0
                    ),
                    "large_effects": len(
                        [r for r in anova_results if r["eta_squared"] >= 0.14]
                    ),
                },
            }

            # 캐시 저장
            if self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

    def _calculate_association_rules(
        self, crosstab: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """연관 규칙 계산"""
        rules = []
        total = crosstab.sum().sum()

        for row_idx, row_name in enumerate(crosstab.index):
            for col_idx, col_name in enumerate(crosstab.columns):
                # 지지도 (Support)
                support = crosstab.iloc[row_idx, col_idx] / total

                # 신뢰도 (Confidence)
                confidence = (
                    crosstab.iloc[row_idx, col_idx] / crosstab.iloc[row_idx, :].sum()
                )

                # 향상도 (Lift)
                expected = (
                    crosstab.iloc[row_idx, :].sum() * crosstab.iloc[:, col_idx].sum()
                ) / total
                lift = (
                    (crosstab.iloc[row_idx, col_idx] / expected) if expected > 0 else 0
                )

                if lift >= self.config.lift_threshold:
                    rules.append(
                        {
                            "antecedent": str(row_name),
                            "consequent": str(col_name),
                            "support": float(support),
                            "confidence": float(confidence),
                            "lift": float(lift),
                        }
                    )

        return sorted(rules, key=lambda x: x["lift"], reverse=True)

    def _get_association_strength(self, cramers_v: float) -> str:
        """연관성 강도 분류"""
        if cramers_v >= 0.5:
            return "매우 강함"
        elif cramers_v >= 0.3:
            return "강함"
        elif cramers_v >= 0.1:
            return "보통"
        else:
            return "약함"

    def _calculate_eta_squared(
        self, df: pd.DataFrame, num_col: str, cat_col: str
    ) -> float:
        """효과 크기 (eta-squared) 계산"""
        try:
            groups = df.groupby(cat_col)[num_col]
            overall_mean = df[num_col].mean()

            # 그룹 간 제곱합 (SSB)
            ssb = sum(
                len(group) * (group.mean() - overall_mean) ** 2 for _, group in groups
            )

            # 총 제곱합 (SST)
            sst = sum((df[num_col] - overall_mean) ** 2)

            return ssb / sst if sst > 0 else 0
        except Exception:
            return 0

    def _get_effect_size(self, eta_squared: float) -> str:
        """효과 크기 분류"""
        if eta_squared >= 0.14:
            return "큰 효과"
        elif eta_squared >= 0.06:
            return "중간 효과"
        elif eta_squared >= 0.01:
            return "작은 효과"
        else:
            return "효과 없음"

    def get_analysis_summary(self, results: Dict[str, Any]) -> str:
        """분석 결과 요약 생성"""
        summary_lines = [
            "=== 조합 분석 결과 요약 ===",
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
                    f"혼합형 분석 (ANOVA):",
                    f"  - 전체 조합: {mixed_results['total_combinations']}개",
                    f"  - 유의한 결과: {mixed_results['significant_results_count']}개",
                    f"  - 최대 효과 크기: {mixed_results['summary']['max_eta_squared']:.3f}",
                    "",
                ]
            )

        # 성능 정보
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


# CLI 기능 통합
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
    """설정 파일에서 설정 로드"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return AnalysisConfig(**config_data)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return AnalysisConfig()


def setup_logging(verbose: bool = False):
    """로깅 설정"""
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
    """CLI 메인 함수"""
    args = parse_arguments()
    setup_logging(args.verbose)

    try:
        # 설정 로드
        if args.config:
            config = load_config_from_file(args.config)
        else:
            config = AnalysisConfig(
                max_cardinality=args.max_cardinality,
                top_k=args.top_k,
                enable_caching=not args.no_cache,
                parallel_processing=not args.no_parallel,
            )

        # 데이터 로드
        logger.info(f"데이터 파일 로드: {args.file}")
        if args.file.endswith(".csv"):
            df = pd.read_csv(args.file)
        elif args.file.endswith(".xlsx"):
            df = pd.read_excel(args.file)
        else:
            raise ValueError("지원되지 않는 파일 형식 (CSV, XLSX만 지원)")

        # DSL 토큰 파싱
        dsl_tokens = None
        if args.dsl_tokens:
            dsl_tokens = [token.strip() for token in args.dsl_tokens.split(",")]
            logger.info(f"DSL 토큰: {dsl_tokens}")

        # 분석 실행
        analyzer = AdvancedCombinationsAnalyzer(config)
        results = analyzer.analyze_all_combinations(df, dsl_tokens)

        # 결과 출력
        print(analyzer.get_analysis_summary(results))

        # 결과 저장
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
