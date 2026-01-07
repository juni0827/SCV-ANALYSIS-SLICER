# dsl2code.py
# Convert DSL token sequence to executable Python code with dynamic generation

import textwrap
from datetime import datetime


class DSLHandler:
    """DSL token을 Processing하고 동적으로 코드를 Create하는 Handler"""

    @staticmethod
    def _get_basic_stats(df_name="df"):
        return f"{df_name}.describe()"

    @staticmethod
    def _get_info(df_name="df"):
        return f"{df_name}.info()"

    @staticmethod
    def _get_missing_values(df_name="df"):
        return f"{df_name}.isnull().sum()"

    @staticmethod
    def _get_correlation_heatmap(df_name="df"):
        return textwrap.dedent(
            f"""
            import seaborn as sns
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 8))
            sns.heatmap({df_name}.corr(numeric_only=True), annot=True, cmap='coolwarm', fmt='.2f')
            plt.title('Correlation Heatmap')
            plt.show()
        """
        ).strip()

    @staticmethod
    def _get_distribution_plot(df_name="df", col_idx=0):
        return textwrap.dedent(
            f"""
            import seaborn as sns
            import matplotlib.pyplot as plt
            
            target_col = {df_name}.columns[{col_idx}]
            if pd.api.types.is_numeric_dtype({df_name}[target_col]):
                plt.figure(figsize=(10, 6))
                sns.histplot({df_name}[target_col], kde=True)
                plt.title(f'Distribution of {{target_col}}')
                plt.show()
            else:
                print(f'{{target_col}} is not numeric, skipping histogram.')
        """
        ).strip()

    @staticmethod
    def _get_advanced_combinations(df_name="df"):
        return textwrap.dedent(
            f"""
            from src.core.combinations import AdvancedCombinationsAnalyzer
            analyzer = AdvancedCombinationsAnalyzer()
            analyzer.analyze_all_combinations({df_name})
        """
        ).strip()

    # --- 확장된 Advanced analysis Feature (C51 ~ C70) ---

    @staticmethod
    def _get_time_series_analysis(df_name="df"):
        """C51: 시계열 분석 (날짜 Column Automatic 감지)"""
        return textwrap.dedent(
            f"""
            # 날짜 Column Automatic 감지 및 시계열 분석
            date_cols = {df_name}.select_dtypes(include=['datetime64']).columns
            if len(date_cols) == 0:
                # 문자열에서 날짜 변환 시도
                for col in {df_name}.select_dtypes(include='object').columns:
                    try:
                        {df_name}[col] = pd.to_datetime({df_name}[col])
                        date_cols = {df_name}.select_dtypes(include=['datetime64']).columns
                        print(f"Converted {{col}} to datetime")
                    except:
                        pass
            
            if len(date_cols) > 0:
                target_date = date_cols[0]
                print(f"Analyzing time series on {{target_date}}")
                {df_name}.set_index(target_date)[{df_name}.select_dtypes(include='number').columns[0]].plot(figsize=(12, 6))
                plt.title(f'Time Series Trend')
                plt.show()
            else:
                print("No datetime columns found for time series analysis")
        """
        ).strip()

    @staticmethod
    def _get_outlier_detection(df_name="df"):
        """C52: IQR based 이상치 탐지"""
        return textwrap.dedent(
            f"""
            # IQR 방식으로 이상치 탐지
            numeric_cols = {df_name}.select_dtypes(include='number').columns
            for col in numeric_cols:
                Q1 = {df_name}[col].quantile(0.25)
                Q3 = {df_name}[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = {df_name}[({df_name}[col] < (Q1 - 1.5 * IQR)) | ({df_name}[col] > (Q3 + 1.5 * IQR))]
                if len(outliers) > 0:
                    print(f"Column {{col}}: {{len(outliers)}} outliers detected")
        """
        ).strip()

    @staticmethod
    def _get_pca_analysis(df_name="df"):
        """C53: PCA 차원 축소 및 Visualization"""
        return textwrap.dedent(
            f"""
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            
            # 수치형 Data만 Optional 및 결측치 Remove
            numeric_df = {df_name}.select_dtypes(include='number').dropna()
            if len(numeric_df.columns) >= 2:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(numeric_df)
                
                pca = PCA(n_components=2)
                pca_result = pca.fit_transform(scaled_data)
                
                plt.figure(figsize=(10, 8))
                plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.5)
                plt.title('PCA Result (2 Components)')
                plt.xlabel(f'PC1 ({{pca.explained_variance_ratio_[0]:.2%}})')
                plt.ylabel(f'PC2 ({{pca.explained_variance_ratio_[1]:.2%}})')
                plt.show()
            else:
                print("Not enough numeric columns for PCA")
        """
        ).strip()

    @staticmethod
    def _get_text_analysis(df_name="df"):
        """C54: 텍스트 Column 워드클라우드"""
        return textwrap.dedent(
            f"""
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            text_cols = {df_name}.select_dtypes(include='object').columns
            if len(text_cols) > 0:
                text_data = ' '.join({df_name}[text_cols[0]].dropna().astype(str).tolist())
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_data)
                
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title(f'Word Cloud for {{text_cols[0]}}')
                plt.show()
            else:
                print("No text columns found for Word Cloud")
        """
        ).strip()

    @staticmethod
    def _get_cluster_analysis(df_name="df"):
        """C55: K-Means 클러스터링"""
        return textwrap.dedent(
            f"""
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            numeric_df = {df_name}.select_dtypes(include='number').dropna()
            if len(numeric_df) > 0:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(numeric_df)
                
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(scaled_data)
                
                print("Cluster Centers:")
                print(pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=numeric_df.columns))
                
                # Visualization (첫 두 Column 기준)
                if len(numeric_df.columns) >= 2:
                    plt.scatter(numeric_df.iloc[:, 0], numeric_df.iloc[:, 1], c=clusters, cmap='viridis')
                    plt.title('K-Means Clustering Result')
                    plt.xlabel(numeric_df.columns[0])
                    plt.ylabel(numeric_df.columns[1])
                    plt.show()
            else:
                print("Not enough numeric data for clustering")
        """
        ).strip()

    @staticmethod
    def _get_smart_visualization(df_name="df"):
        """C60: Data Type에 according to 스마트 Visualization 추천"""
        return textwrap.dedent(
            f"""
            # 스마트 Visualization: Data Type Automatic 감지 및 최적 그래프 Create
            num_cols = {df_name}.select_dtypes(include='number').columns
            cat_cols = {df_name}.select_dtypes(include='object').columns
            
            print(f"Smart Viz: Found {{len(num_cols)}} numeric and {{len(cat_cols)}} categorical columns")
            
            # Case 1: 수치형 1개 (히스토그램 + 박스플롯)
            if len(num_cols) >= 1:
                target = num_cols[0]
                fig, ax = plt.subplots(1, 2, figsize=(12, 5))
                sns.histplot({df_name}[target], kde=True, ax=ax[0])
                ax[0].set_title(f'Histogram of {{target}}')
                sns.boxplot(x={df_name}[target], ax=ax[1])
                ax[1].set_title(f'Boxplot of {{target}}')
                plt.tight_layout()
                plt.show()
                
            # Case 2: 범주형 1개 (막대 차트)
            if len(cat_cols) >= 1:
                target = cat_cols[0]
                top_n = {df_name}[target].value_counts().head(10)
                plt.figure(figsize=(10, 5))
                sns.barplot(x=top_n.index, y=top_n.values)
                plt.title(f'Top 10 Categories in {{target}}')
                plt.xticks(rotation=45)
                plt.show()
                
            # Case 3: 수치형 2개 (산점도 + 회귀선)
            if len(num_cols) >= 2:
                x, y = num_cols[0], num_cols[1]
                plt.figure(figsize=(8, 6))
                sns.regplot(data={df_name}, x=x, y=y, scatter_kws={{'alpha':0.5}})
                plt.title(f'Scatter Plot: {{x}} vs {{y}}')
                plt.show()
                
            # Case 4: 범주형 2개 (히트맵)
            if len(cat_cols) >= 2:
                c1, c2 = cat_cols[0], cat_cols[1]
                ct = pd.crosstab({df_name}[c1], {df_name}[c2])
                plt.figure(figsize=(10, 8))
                sns.heatmap(ct, annot=True, fmt='d', cmap='YlGnBu')
                plt.title(f'Heatmap: {{c1}} vs {{c2}}')
                plt.show()
        """
        ).strip()

    @staticmethod
    def _get_pie_chart(df_name="df"):
        """C61: 범주형 Data 원형 차트"""
        return textwrap.dedent(
            f"""
            # 원형 차트 (Pie Chart)
            cat_cols = {df_name}.select_dtypes(include='object').columns
            if len(cat_cols) > 0:
                target = cat_cols[0]
                counts = {df_name}[target].value_counts()
                
                # 항목이 많으면 상위 9개 + Others로 묶기
                if len(counts) > 10:
                    top_9 = counts[:9]
                    others = pd.Series([counts[9:].sum()], index=['Others'])
                    counts = pd.concat([top_9, others])
                
                plt.figure(figsize=(8, 8))
                plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
                plt.title(f'Pie Chart of {{target}}')
                plt.show()
            else:
                print("No categorical columns found for Pie Chart")
        """
        ).strip()


# Token 정의 및 Handler 매핑
TOKEN_HANDLERS = {
    # Basic analysis
    "C1": lambda: "df.describe()",
    "C2": lambda: "df.info()",
    "C3": lambda: "df.isnull().sum()",
    "C4": lambda: "df.dtypes",
    "C5": lambda: "df.nunique()",
    "C6": lambda: "df.head()",
    "C7": lambda: "df.tail()",
    "C8": lambda: "df.corr(numeric_only=True)",
    "C9": lambda: "df.columns.tolist()",
    "C10": lambda: "df.memory_usage(deep=True)",
    # 중급 분석
    "C11": lambda: "(df.isnull().sum() / len(df) * 100).round(2)",
    "C12": DSLHandler._get_correlation_heatmap,
    "C13": lambda: "df[df.columns[0]].value_counts()",
    "C14": lambda: "df.describe(include='all')",
    "C15": lambda: "print(f'Shape: {df.shape}')",
    "C16": lambda: "df.duplicated().sum()",
    "C17": lambda: "df.sample(min(10, len(df)))",
    "C18": lambda: "{col: df[col].unique()[:10] for col in df.columns}",  # 너무 길어질 수 있어 10개로 제한
    "C19": lambda: "df.head().T",
    "C20": lambda: "df.index",
    # Data 조작 및 Filter링
    "C21": lambda: "df[df.isnull().any(axis=1)].head()",
    "C22": lambda: "df.mode().iloc[0]",
    "C23": lambda: "df.hist(figsize=(12, 10)); plt.show()",
    "C24": lambda: "df.select_dtypes(include='object').describe()",
    "C25": lambda: "df.corr(numeric_only=True).unstack().sort_values(ascending=False).drop_duplicates().head(10)",
    "C26": lambda: "df.groupby(df.columns[0]).mean(numeric_only=True)",
    "C27": lambda: "df.to_excel('output.xlsx', index=False)",
    "C28": lambda: "df.to_json('output.json', orient='records')",
    "C29": lambda: "df.std(numeric_only=True)",
    "C30": lambda: "df.agg(['min', 'max'])",
    # 고급 Statistics 및 Visualization
    "C31": lambda: "(df == 0).sum()",
    "C32": lambda: "df[df.duplicated()]",
    "C33": lambda: "df.notnull().sum()",
    "C34": lambda: "df.index.is_unique",
    "C35": lambda: "sns.pairplot(df.select_dtypes(include='number').dropna().sample(min(100, len(df)))); plt.show()",
    "C36": lambda: "df.sort_values(by=df.columns[0])",
    "C37": lambda: "df.sort_values(by=df.columns[0], ascending=False)",
    "C38": lambda: "f'{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB'",
    "C39": lambda: "pd.concat([df.dtypes, df.isnull().sum()], axis=1, keys=['Type', 'Nulls'])",
    "C40": lambda: "(df.select_dtypes(include='number') < 0).sum()",
    # 심화 분석 (C41-C50)
    "C41": lambda: "df.skew(numeric_only=True)",
    "C42": lambda: "df.kurtosis(numeric_only=True)",
    "C43": lambda: "df.quantile([0.25, 0.5, 0.75], numeric_only=True)",
    "C44": lambda: "df.select_dtypes(include='number').mode().iloc[0]",
    "C45": lambda: "(df.nunique() / len(df) * 100).round(2)",
    "C46": lambda: "df.apply(lambda x: x.duplicated().sum())",
    "C47": lambda: "df.boxplot(figsize=(12, 6)); plt.xticks(rotation=45); plt.show()",
    "C48": lambda: "df.columns[df.isnull().any()].tolist()",
    "C49": lambda: "pd.crosstab(df.iloc[:, 0], df.iloc[:, 1]) if len(df.columns) > 1 else 'Not enough columns'",
    "C50": DSLHandler._get_advanced_combinations,
    # --- 확장된 Feature (C51-C70) ---
    "C51": DSLHandler._get_time_series_analysis,
    "C52": DSLHandler._get_outlier_detection,
    "C53": DSLHandler._get_pca_analysis,
    "C54": DSLHandler._get_text_analysis,
    "C55": DSLHandler._get_cluster_analysis,
    "C56": lambda: "df.corr(method='spearman', numeric_only=True)",  # 스피어만 상관계수
    "C57": lambda: "df.corr(method='kendall', numeric_only=True)",  # 켄달 상관계수
    "C58": lambda: "df.select_dtypes(include='number').var()",  # 분산
    "C59": lambda: "df.select_dtypes(include='number').sem()",  # 표준오차
    "C60": DSLHandler._get_smart_visualization,  # 스마트 Visualization 추천
    "C61": DSLHandler._get_pie_chart,  # 원형 차트
    "SAVE": lambda: "# Result Save 로직 (Execution 환경에 따라 다름)",
    "EXPORT": lambda: "df.to_csv('analysis_result.csv', index=False)",
    "PROFILE": lambda: "import ydata_profiling; ydata_profiling.ProfileReport(df).to_file('report.html')",
}


def _get_token_description(token):
    """Token 설명 Return (확장됨)"""
    descriptions = {
        "C1": "기술통계 요약",
        "C2": "데이터 정보",
        "C3": "결측치 개수",
        "C4": "데이터 타입",
        "C5": "고유값 개수",
        "C6": "상위 5행",
        "C7": "하위 5행",
        "C8": "상관관계 행렬",
        "C9": "컬럼 목록",
        "C10": "메모리 사용량",
        "C11": "결측치 비율",
        "C12": "상관관계 히트맵",
        "C13": "첫 컬럼 값 분포",
        "C14": "상세 기술통계",
        "C15": "데이터 크기(Shape)",
        "C16": "중복행 개수",
        "C17": "랜덤 샘플링",
        "C18": "컬럼별 고유값 예시",
        "C19": "데이터 전치(Transpose)",
        "C20": "인덱스 정보",
        "C21": "결측치 포함 행 조회",
        "C22": "최빈값(Mode)",
        "C23": "히스토그램 시각화",
        "C24": "범주형 변수 요약",
        "C25": "주요 상관관계 쌍",
        "C26": "그룹별 평균",
        "C27": "엑셀 저장",
        "C28": "JSON 저장",
        "C29": "표준편차",
        "C30": "최대/최소값",
        "C31": "0인 값 개수",
        "C32": "중복 데이터 조회",
        "C33": "유효 데이터 개수",
        "C34": "고유 인덱스 여부",
        "C35": "Pairplot 시각화",
        "C36": "오름차순 정렬",
        "C37": "내림차순 정렬",
        "C38": "메모리 사용량(MB)",
        "C39": "데이터 품질 요약",
        "C40": "음수값 개수",
        "C41": "왜도(Skewness)",
        "C42": "첨도(Kurtosis)",
        "C43": "4분위수",
        "C44": "수치형 최빈값",
        "C45": "고유값 비율",
        "C46": "컬럼별 중복도",
        "C47": "박스플롯",
        "C48": "결측 컬럼 목록",
        "C49": "교차표(Crosstab)",
        "C50": "고급 조합 분석",
        # 확장된 설명
        "C51": "시계열 트렌드 분석",
        "C52": "이상치(Outlier) 탐지",
        "C53": "PCA 차원 축소",
        "C54": "워드클라우드(텍스트)",
        "C55": "K-Means 클러스터링",
        "C56": "스피어만 상관계수",
        "C57": "켄달 상관계수",
        "C58": "분산(Variance)",
        "C59": "표준오차(SEM)",
        "C60": "스마트 시각화 추천",
        "C61": "원형 차트(Pie Chart)",
    }
    return descriptions.get(token, f"분석 작업 ({token})")


def dsl_to_code(dsl_sequence, csv_path="your_file.csv"):
    """
    DSL token 시퀀스를 Execution Available한 Python 코드로 변환합니다.
    Jinja2 없이도 동적인 Code generation을 Support합니다.
    """
    # Header Create
    lines = [
        "#!/usr/bin/env python3",
        '"""',
        f"Automatic Create된 고급 Data 분석 코드",
        f'DSL 시퀀스: {" → ".join(dsl_sequence)}',
        f'Create 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '"""',
        "",
        "import pandas as pd",
        "import numpy as np",
        "import matplotlib.pyplot as plt",
        "import seaborn as sns",
        "import warnings",
        "warnings.filterwarnings('ignore')",
        "",
    ]

    # Data 로딩
    lines.extend(
        [
            "# --- Data 로딩 ---",
            f"print('데이터 로딩 중: {csv_path}')",
            "try:",
            f"    df = pd.read_csv({repr(csv_path)})",
            "    print(f'데이터 로드 완료: {len(df):,}행 × {len(df.columns)}열')",
            "except Exception as e:",
            "    print(f'데이터 로드 실패: {e}')",
            "    exit(1)",
            "",
        ]
    )

    # Run analysis 루프
    lines.append("# --- 분석 Start ---")

    for i, token in enumerate(dsl_sequence, 1):
        handler = TOKEN_HANDLERS.get(token)
        description = _get_token_description(token)

        lines.append(f"\n# [{i}] {token}: {description}")
        lines.append(f"print('\\n🔹 {i}. {description} ({token})')")
        lines.append("try:")

        if handler:
            # Handler가 Function면 Call하여 코드 문자열을 얻고, 문자열if 그as Use
            code_block = handler() if callable(handler) else handler

            # 코드 블록 들여Write 적용
            indented_code = textwrap.indent(code_block, "    ")

            # Result Output 로직이 Include되어 있지 않으면 print로 감싸기 (단순 표현식인 경우)
            if (
                "print" not in code_block
                and "plt.show" not in code_block
                and "=" not in code_block
                and len(code_block.split("\n")) == 1
            ):
                lines.append(f"    print({code_block})")
            else:
                lines.append(indented_code)
        else:
            lines.append(f"    print('알 수 없는 토큰: {token}')")

        lines.append("except Exception as e:")
        lines.append(f"    print(f'오류 발생 ({token}): {{e}}')")

    lines.extend(
        ["", "# --- 분석 Complete ---", "print('\\n모든 분석이 Complete되었습니다.')"]
    )

    return "\n".join(lines)


def generate_analysis_template(analysis_type="basic"):
    """분석 템플릿 Create"""
    templates = {
        "basic": ["C2", "C15", "C6", "C3", "C1"],
        "statistical": ["C1", "C14", "C29", "C41", "C42", "C43"],
        "visualization": ["C12", "C23", "C35", "C47"],
        "missing_data": ["C3", "C11", "C21", "C48"],
        "correlation": ["C8", "C12", "C25", "C50"],
        "comprehensive": ["C2", "C15", "C3", "C1", "C8", "C12", "C23", "C50"],
        "advanced_ml": ["C51", "C52", "C53", "C55"],  # 새로 Add된 ML 템플릿
        "text_mining": ["C54"],  # 텍스트 분석 템플릿
    }
    return templates.get(analysis_type, templates["basic"])
