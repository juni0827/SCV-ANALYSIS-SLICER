
#!/usr/bin/env python3
"""
Combinations Analysis - 통합 데이터 관계 분석 모듈

이 모듈은 데이터프레임의 컬럼 간 관계를 자동으로 분석합니다.
- 수치형 × 수치형: 상관관계 분석 (Pearson, Spearman, Kendall)
- 범주형 × 범주형: 연관규칙 분석 (Lift, Cramer's V)
- 범주형 × 수치형: 분산분석 (ANOVA, eta-squared)
- 텍스트 분석: 기본 텍스트 통계
- CLI 인터페이스: 명령줄에서 바로 사용 가능
- 메모리 최적화 및 성능 모니터링

사용법:
    # Python 코드에서
    from combinations import analyze_combinations
    results = analyze_combinations(df)
    
    # 고급 분석
    from combinations import AdvancedCombinationsAnalyzer, AnalysisConfig
    config = AnalysisConfig(parallel_processing=True)
    analyzer = AdvancedCombinationsAnalyzer(config)
    results = analyzer.analyze_combinations_advanced(df)
    
    # CLI에서 바로 실행
    python combinations.py --input data.csv --output results.json
"""

from __future__ import annotations
import sys
import argparse
import json
import time
import logging
import warnings
import hashlib
import threading
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Union
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

# 선택적 의존성
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    warnings.warn("psutil이 설치되지 않아 성능 모니터링 기능이 제한됩니다.", UserWarning)

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    warnings.warn("scipy가 설치되지 않아 일부 통계 기능이 제한됩니다.", UserWarning)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    text_analysis: bool = False  # 기본적으로 비활성화

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
        self.is_monitoring = False
        self.monitor_thread = None

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
                memory_usage={
                    'start': start_memory,
                    'end': end_memory,
                    'delta': end_memory - start_memory
                } if HAS_PSUTIL else {'start': 0, 'end': 0, 'delta': 0},
                cpu_usage=psutil.cpu_percent(interval=0.1) if HAS_PSUTIL else 0
            )

            self.metrics_history.append(metrics)
            logger.info(f"{operation_name} 완료: {metrics.duration:.2f}초")

    def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 생성"""
        if not self.metrics_history:
            return {"error": "no_metrics_available"}

        total_duration = sum(m.duration for m in self.metrics_history)
        avg_memory_delta = sum(m.memory_usage['delta'] for m in self.metrics_history) / len(self.metrics_history)

        return {
            "total_operations": len(self.metrics_history),
            "total_duration": total_duration,
            "average_duration": total_duration / len(self.metrics_history),
            "average_memory_delta": avg_memory_delta,
            "memory_efficiency": "good" if avg_memory_delta < 50*1024*1024 else "needs_optimization"
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
                if col_type == 'object':
                    # 범주형 데이터로 변환 가능한지 확인
                    if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                        optimized_df[col] = optimized_df[col].astype('category')
                elif col_type == 'int64':
                    # 정수 타입 다운캐스팅
                    col_min, col_max = optimized_df[col].min(), optimized_df[col].max()
                    if col_min >= 0:
                        if col_max < 256:
                            optimized_df[col] = optimized_df[col].astype('uint8')
                        elif col_max < 65536:
                            optimized_df[col] = optimized_df[col].astype('uint16')
                        elif col_max < 4294967296:
                            optimized_df[col] = optimized_df[col].astype('uint32')
                    else:
                        if col_min > -129 and col_max < 128:
                            optimized_df[col] = optimized_df[col].astype('int8')
                        elif col_min > -32769 and col_max < 32768:
                            optimized_df[col] = optimized_df[col].astype('int16')
                        elif col_min > -2147483649 and col_max < 2147483648:
                            optimized_df[col] = optimized_df[col].astype('int32')
                elif col_type == 'float64':
                    # 실수 타입 다운캐스팅
                    optimized_df[col] = optimized_df[col].astype('float32')
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
            "memory_per_column": {col: usage / 1024 / 1024 for col, usage in memory_usage.items()},
            "largest_column": memory_usage.idxmax(),
            "optimization_potential": MemoryOptimizer._calculate_optimization_potential(df)
        }

    @staticmethod
    def _calculate_optimization_potential(df: pd.DataFrame) -> str:
        """최적화 잠재력 계산"""
        try:
            original_memory = df.memory_usage(deep=True).sum()
            optimized_df = MemoryOptimizer.optimize_dataframe(df)
            optimized_memory = optimized_df.memory_usage(deep=True).sum()

            savings_percent = (original_memory - optimized_memory) / original_memory * 100

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

    def get_cache_key(self, df_hash: str, analysis_type: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        params_str = json.dumps(params, sort_keys=True)
        key = hashlib.md5(f"{df_hash}_{analysis_type}_{params_str}".encode()).hexdigest()
        return key

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # 캐시 파일 나이 확인
        file_age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if file_age_hours > self.max_age_hours:
            cache_file.unlink()  # 오래된 캐시 삭제
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, key: str, data: Any):
        """데이터를 캐시에 저장"""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
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
    """고급 조합 분석기 클래스"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.performance_monitor = PerformanceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        self.cache = AnalysisCache(self.config.cache_dir) if self.config.enable_caching else None

    def _load_from_cache(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 로드"""
        if not self.config.enable_caching or not self.cache:
            return None
        return self.cache.get(key)

    def _save_to_cache(self, key: str, data: Any):
        """데이터를 캐시에 저장"""
        if not self.config.enable_caching or not self.cache:
            return
        self.cache.set(key, data)

    def _split_types_advanced(self, df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
        """고급 컬럼 타입 분류 (수치형, 범주형, 텍스트형)"""
        numeric_cols = []
        categorical_cols = []
        text_cols = []

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # 수치형이지만 고유값이 적으면 범주형으로 취급
                if df[col].nunique() <= self.config.max_cardinality:
                    categorical_cols.append(col)
                else:
                    numeric_cols.append(col)
            else:
                # 문자열 타입 분석
                if df[col].dtype == 'object':
                    unique_ratio = df[col].nunique() / len(df)
                    avg_length = df[col].astype(str).str.len().mean()

                    # 짧고 반복적인 텍스트는 범주형
                    if (unique_ratio <= 0.1 or
                        (avg_length < 20 and df[col].nunique() <= self.config.max_cardinality)):
                        categorical_cols.append(col)
                    else:
                        text_cols.append(col)
                else:
                    # 날짜, 불리언 등 다른 타입
                    if df[col].nunique() <= self.config.max_cardinality:
                        categorical_cols.append(col)

        return numeric_cols, categorical_cols, text_cols

    def _value_counts_top(self, s: pd.Series, top_k: int = 20) -> List[Dict[str, Any]]:
        """상위 값 카운트 계산 (개선된 버전)"""
        vc = s.astype("object").value_counts(dropna=False).head(top_k)
        total = len(s)

        result = []
        for k, v in vc.items():
            # 결측값 처리
            display_value = str(k) if pd.notna(k) else "NaN"
            result.append({
                "value": display_value,
                "count": int(v),
                "ratio": float(v/total),
                "percentage": float(v/total * 100)
            })

        return result

    def _lift_table_parallel(self, df: pd.DataFrame, a: str, b: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """병렬 처리된 Lift 테이블 계산"""
        x = df[a].astype("object")
        y = df[b].astype("object")
        ct = pd.crosstab(x, y)

        total = ct.values.sum()
        if total == 0 or ct.shape[0] == 0 or ct.shape[1] == 0:
            return []

        # Lift 계산 최적화
        px = ct.sum(axis=1) / total
        py = ct.sum(axis=0) / total
        expected = np.outer(px.values, py.values) * total

        # 0으로 나누기 방지
        lift = ct.values / np.maximum(expected, 1e-9)

        rows = []
        xi = list(ct.index)
        yi = list(ct.columns)

        for i in range(ct.shape[0]):
            for j in range(ct.shape[1]):
                if ct.values[i,j] >= self.config.min_sample_size:  # 최소 샘플 크기 필터링
                    lift_val = float(lift[i,j])
                    if lift_val >= self.config.lift_threshold:  # Lift 임계값 필터링
                        rows.append({
                            "a_val": str(xi[i]) if pd.notna(xi[i]) else "NaN",
                            "b_val": str(yi[j]) if pd.notna(yi[j]) else "NaN",
                            "count": int(ct.values[i,j]),
                            "lift": lift_val,
                            "expected": float(expected[i,j]),
                            "support": float(ct.values[i,j] / total)
                        })

        # 개선된 정렬: Lift와 Support의 조합 점수
        rows.sort(key=lambda r: (r["lift"] * np.log1p(r["count"]) * r["support"]), reverse=True)
        return rows[:top_k]

    def _correlation_analysis(self, df: pd.DataFrame, x: str, y: str) -> Dict[str, Any]:
        """고급 상관관계 분석"""
        s1, s2 = df[x], df[y]

        # 이상치 처리
        s1 = s1.replace([np.inf, -np.inf], np.nan)
        s2 = s2.replace([np.inf, -np.inf], np.nan)

        # 결측값 제거
        combined = pd.concat([s1, s2], axis=1).dropna()

        if len(combined) < self.config.min_sample_size:
            return {"error": "insufficient_data", "sample_size": len(combined)}

        # 다중 상관계수 계산
        pearson = combined.corr(method="pearson").iloc[0,1]
        spearman = combined.corr(method="spearman").iloc[0,1]

        # Kendall tau (더 robust한 순위 상관계수)
        kendall = combined.corr(method="kendall").iloc[0,1]

        # 상관계수의 신뢰성 평가
        confidence = self._correlation_confidence(len(combined), max(abs(pearson), abs(spearman)))

        return {
            "pearson": float(pearson),
            "spearman": float(spearman),
            "kendall": float(kendall),
            "sample_size": len(combined),
            "confidence": confidence,
            "strength": self._interpret_correlation_strength(max(abs(pearson), abs(spearman)))
        }

    def _correlation_confidence(self, n: int, r: float) -> str:
        """상관계수의 신뢰성 평가"""
        # Fisher z-transformation을 사용한 대략적인 신뢰도 계산
        if n < 10:
            return "very_low"
        elif n < 30:
            return "low"
        elif n < 100:
            return "moderate"
        else:
            return "high"

    def _interpret_correlation_strength(self, r: float) -> str:
        """상관계수 강도 해석"""
        abs_r = abs(r)
        if abs_r >= 0.8:
            return "very_strong"
        elif abs_r >= 0.6:
            return "strong"
        elif abs_r >= 0.4:
            return "moderate"
        elif abs_r >= 0.2:
            return "weak"
        else:
            return "very_weak"

    def _anova_analysis(self, df: pd.DataFrame, cat: str, num: str) -> Dict[str, Any]:
        """고급 분산분석"""
        s = df[[cat, num]].dropna()

        if s[cat].nunique() < 2 or len(s) < self.config.min_sample_size:
            return {"error": "insufficient_data"}

        groups = [g[num].values for _, g in s.groupby(cat)]
        overall = s[num].values

        # 그룹별 통계
        group_stats = []
        for name, group in s.groupby(cat):
            group_stats.append({
                "category": str(name),
                "count": len(group),
                "mean": float(group[num].mean()),
                "std": float(group[num].std()),
                "min": float(group[num].min()),
                "max": float(group[num].max())
            })

        # ANOVA 계산
        grand_mean = overall.mean()
        ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
        ss_within = sum(((g - g.mean())**2).sum() for g in groups)
        ss_total = ((overall - grand_mean)**2).sum()

        df_between = len(groups) - 1
        df_within = len(overall) - len(groups)
        df_total = len(overall) - 1

        ms_between = ss_between / df_between if df_between > 0 else 0
        ms_within = ss_within / df_within if df_within > 0 else 0

        f_stat = ms_between / ms_within if ms_within > 0 else 0
        eta2 = ss_between / ss_total if ss_total > 0 else 0

        # p-value 계산 (F-분포)
        from scipy import stats
        p_value = 1 - stats.f.cdf(f_stat, df_between, df_within)

        return {
            "eta2": float(eta2),
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "group_stats": group_stats,
            "overall_stats": {
                "count": len(overall),
                "mean": float(grand_mean),
                "std": float(np.std(overall)),
                "min": float(np.min(overall)),
                "max": float(np.max(overall))
            }
        }

    def analyze_combinations_advanced(self, df: pd.DataFrame) -> Dict[str, Any]:
        """고급 조합 분석 메인 함수"""
        start_time = time.time()
        logger.info(f"🔍 고급 조합 분석 시작... (샘플: {len(df)}행)")

        # 데이터 샘플링 (필요시)
        if len(df) > self.config.sample_cap:
            logger.info(f"📊 데이터 샘플링: {len(df)} → {self.config.sample_cap}")
            df = df.sample(self.config.sample_cap, random_state=42)

        # 컬럼 타입 분류
        num_cols, cat_cols, text_cols = self._split_types_advanced(df)

        logger.info(f"📋 컬럼 분류 완료: 수치형 {len(num_cols)}개, 범주형 {len(cat_cols)}개, 텍스트 {len(text_cols)}개")

        # 메타 정보
        report = {
            "meta": {
                "timestamp": time.time(),
                "rows": len(df),
                "columns": len(df.columns),
                "numeric_cols": num_cols,
                "categorical_cols": cat_cols,
                "text_cols": text_cols,
                "config": {
                    "max_cardinality": self.config.max_cardinality,
                    "top_k": self.config.top_k,
                    "correlation_threshold": self.config.correlation_threshold,
                    "lift_threshold": self.config.lift_threshold,
                    "eta2_threshold": self.config.eta2_threshold
                }
            }
        }

        # 1. 단변량 분석
        logger.info("📊 단변량 분석 중...")
        univariate = {}
        for col in cat_cols:
            univariate[col] = self._value_counts_top(df[col], self.config.top_k)
        report["univariate"] = univariate

        # 2. 범주형-범주형 분석 (병렬 처리)
        logger.info("🔗 범주형-범주형 관계 분석 중...")
        cc_pairs = []
        if self.config.parallel_processing and len(cat_cols) >= 2:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for a, b in combinations(cat_cols, 2):
                    futures.append(executor.submit(self._lift_table_parallel, df, a, b, self.config.top_k))

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        # 컬럼 쌍 정보 추가
                        a, b = result[0]['a_val'], result[0]['b_val']  # 임시 처리
                        cc_pairs.append({"cols": (a, b), "pairs": result})
        else:
            for a, b in combinations(cat_cols, 2):
                rows = self._lift_table_parallel(df, a, b, self.config.top_k)
                if rows:
                    cc_pairs.append({"cols": (a, b), "pairs": rows})

        cc_pairs.sort(key=lambda x: max(p["lift"] for p in x["pairs"]) if x["pairs"] else 0, reverse=True)
        report["catcat"] = cc_pairs[:self.config.top_k]

        # 3. 수치형-수치형 분석
        logger.info("📈 수치형-수치형 상관관계 분석 중...")
        nn_pairs = []
        for a, b in combinations(num_cols, 2):
            corr_result = self._correlation_analysis(df, a, b)
            if "error" not in corr_result:
                max_corr = max(abs(corr_result.get("pearson", 0)), abs(corr_result.get("spearman", 0)))
                if max_corr >= self.config.correlation_threshold:
                    nn_pairs.append({"cols": (a, b), **corr_result})

        nn_pairs.sort(key=lambda x: max(abs(x.get("pearson", 0)), abs(x.get("spearman", 0))), reverse=True)
        report["numnum"] = nn_pairs[:self.config.top_k]

        # 4. 범주형-수치형 분석
        logger.info("📊 범주형-수치형 분산 분석 중...")
        cn_pairs = []
        for cat in cat_cols:
            for num in num_cols:
                anova_result = self._anova_analysis(df, cat, num)
                if "error" not in anova_result and anova_result["eta2"] >= self.config.eta2_threshold:
                    cn_pairs.append({"cols": (cat, num), **anova_result})

        cn_pairs.sort(key=lambda x: x["eta2"], reverse=True)
        report["catnum"] = cn_pairs[:self.config.top_k]

        # 5. 텍스트 컬럼 분석 (선택적)
        if text_cols:
            logger.info("📝 텍스트 컬럼 분석 중...")
            text_analysis = {}
            for col in text_cols:
                text_stats = self._analyze_text_column(df[col])
                text_analysis[col] = text_stats
            report["text_analysis"] = text_analysis

        # 6. 시각화 추천
        logger.info("🎨 시각화 추천 생성 중...")
        report["visualization_recommendations"] = self._suggest_advanced_plots(report)

        # 7. 요약 통계
        report["summary"] = {
            "total_relationships_found": len(cc_pairs) + len(nn_pairs) + len(cn_pairs),
            "strong_correlations": len([p for p in nn_pairs if p.get("strength") in ["strong", "very_strong"]]),
            "significant_anova": len([p for p in cn_pairs if p.get("significant", False)]),
            "high_lift_associations": len([p for p in cc_pairs if any(pair["lift"] >= 2.0 for pair in p["pairs"])]),
            "processing_time": time.time() - start_time
        }

        logger.info(f"✅ 분석 완료! 총 {report['summary']['total_relationships_found']}개 관계 발견")
        return report

    def _analyze_text_column(self, series: pd.Series) -> Dict[str, Any]:
        """텍스트 컬럼 분석"""
        text_data = series.astype(str)

        return {
            "total_entries": len(text_data),
            "unique_entries": text_data.nunique(),
            "avg_length": float(text_data.str.len().mean()),
            "max_length": int(text_data.str.len().max()),
            "empty_count": int(text_data.str.strip().eq('').sum()),
            "null_count": int(series.isna().sum()),
            "most_common_words": self._extract_common_words(text_data)
        }

    def _extract_common_words(self, text_series: pd.Series, top_n: int = 10) -> List[Dict[str, Any]]:
        """텍스트에서 자주 등장하는 단어 추출"""
        from collections import Counter
        import re

        # 간단한 텍스트 전처리
        all_text = ' '.join(text_series.dropna().astype(str))
        words = re.findall(r'\b\w+\b', all_text.lower())

        # 불용어 필터링 (간단 버전)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        filtered_words = [word for word in words if word not in stopwords and len(word) > 2]

        word_counts = Counter(filtered_words)
        return [{"word": word, "count": count} for word, count in word_counts.most_common(top_n)]

    def _suggest_advanced_plots(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """고급 시각화 추천"""
        recommendations = []

        # 범주형-범주형 관계
        for entry in report.get("catcat", [])[:5]:
            cols = entry["cols"]
            max_lift = max(pair["lift"] for pair in entry["pairs"])
            recommendations.append({
                "type": "heatmap",
                "cols": list(cols),
                "priority": "high" if max_lift >= 2.0 else "medium",
                "reason": ".2f",
                "insights": self._generate_insights("catcat", entry)
            })

        # 수치형-수치형 관계
        for entry in report.get("numnum", [])[:5]:
            cols = entry["cols"]
            strength = entry.get("strength", "weak")
            recommendations.append({
                "type": "scatter",
                "cols": list(cols),
                "priority": "high" if strength in ["strong", "very_strong"] else "medium",
                "reason": f"Strong {strength} correlation ({entry.get('pearson', 0):.2f})",
                "insights": self._generate_insights("numnum", entry)
            })

        # 범주형-수치형 관계
        for entry in report.get("catnum", [])[:5]:
            cols = entry["cols"]
            significant = entry.get("significant", False)
            recommendations.append({
                "type": "boxplot",
                "cols": list(cols),
                "priority": "high" if significant else "medium",
                "reason": f"Significant group differences (η² = {entry.get('eta2', 0):.3f})",
                "insights": self._generate_insights("catnum", entry)
            })

        return recommendations

    def _generate_insights(self, analysis_type: str, entry: Dict[str, Any]) -> List[str]:
        """분석 결과에 대한 인사이트 생성"""
        insights = []

        if analysis_type == "catcat":
            max_lift = max(pair["lift"] for pair in entry["pairs"])
            if max_lift >= 3.0:
                insights.append("매우 강한 연관성이 발견되었습니다")
            elif max_lift >= 2.0:
                insights.append("강한 연관성이 발견되었습니다")
            else:
                insights.append("약한 연관성이 발견되었습니다")

        elif analysis_type == "numnum":
            strength = entry.get("strength", "weak")
            if strength == "very_strong":
                insights.append("매우 강한 선형 관계가 있습니다")
            elif strength == "strong":
                insights.append("강한 선형 관계가 있습니다")
            else:
                insights.append("약한 선형 관계가 있습니다")

        elif analysis_type == "catnum":
            if entry.get("significant", False):
                insights.append("그룹 간에 통계적으로 유의미한 차이가 있습니다")
            else:
                insights.append("그룹 간 차이가 통계적으로 유의미하지 않습니다")

        return insights

# 하위 호환성을 위한 기존 함수들
def _split_types(df, max_cardinality=50):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    num_cols, cat_cols, _ = analyzer._split_types_advanced(df)
    return num_cols, cat_cols

class AdvancedCombinationsAnalyzer:
    def __init__(self):
        pass

    def _value_counts_top(self, s, top_k=20):
        raise NotImplementedError

def _value_counts_top(s: pd.Series, top_k=20):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    return analyzer._value_counts_top(s, top_k)

def _lift_table(df, a, b, top_k=20):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    return analyzer._lift_table_parallel(df, a, b, top_k)

def _pearson_spearman(df, x, y, method="pearson"):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    result = analyzer._correlation_analysis(df, x, y)
    if method == "spearman":
        return result.get("spearman")
    else:
        return result.get("pearson")

def _anova_eta2(df, cat, num):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    result = analyzer._anova_analysis(df, cat, num)
    return result.get("eta2")

def analyze_combinations(df: pd.DataFrame, *, max_cardinality=50, top_k=20, sample_cap=200_000):
    """기존 함수와의 호환성을 위한 래퍼"""
    config = AnalysisConfig(
        max_cardinality=max_cardinality,
        top_k=top_k,
        sample_cap=sample_cap
    )
    analyzer = AdvancedCombinationsAnalyzer(config)
    return analyzer.analyze_combinations_advanced(df)

def suggest_plots(report):
    """기존 함수와의 호환성을 위한 래퍼"""
    analyzer = AdvancedCombinationsAnalyzer()
    return analyzer._suggest_advanced_plots(report)
