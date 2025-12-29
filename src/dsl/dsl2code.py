
# dsl2code.py
# Convert DSL token sequence (e.g., ["C1", "C2", "C6"]) to executable Python code

token_code_map = {
    "C1": "df.describe()",
    "C2": "df.info()",
    "C3": "df.isnull().sum()",
    "C4": "df.dtypes",
    "C5": "df.nunique()",
    "C6": "df.head()",
    "C7": "df.tail()",
    "C8": "df.corr()",
    "C9": "df.columns",
    "C10": "df.memory_usage()",
    "C11": "(df.isnull().sum() / len(df) * 100).round(2)",  # 결측치 비율(%)
    "C12": "import seaborn as sns; import matplotlib.pyplot as plt; sns.heatmap(df.corr(), annot=True); plt.show()",  # 상관관계 히트맵
    "C13": "print(df[df.columns[0]].value_counts())",  # 첫 번째 컬럼 값별 개수
    "C14": "df.describe(include='all')",
    "C15": "df.shape",
    "C16": "df.duplicated().sum()",
    "C17": "df.sample(10)",
    "C18": "{col: df[col].unique() for col in df.columns}",
    "C19": "df.T",
    "C20": "df.index"
    ,
    "C21": "df[df.isnull().any(axis=1)]",  # 결측치가 있는 행
    "C22": "{col: df[col].mode().tolist() for col in df.columns}",  # 각 컬럼별 최빈값
    "C23": "import matplotlib.pyplot as plt; df.select_dtypes(include='number').hist(figsize=(10,8)); plt.show()",  # 수치형 히스토그램
    "C24": "[df[col].value_counts().head() for col in df.select_dtypes(include='object').columns]",  # 상위 5개 범주형 컬럼 값별 개수
    "C25": "df.corr().unstack().sort_values(ascending=False)[len(df.columns):len(df.columns)+5]",  # 상관계수 상위 5개
    "C26": "df.groupby(df.columns[0]).mean()",  # 첫 컬럼 기준 그룹별 평균
    "C27": "df.to_excel('output.xlsx', index=False)",  # 엑셀 저장
    "C28": "df.to_json('output.json', orient='records')",  # json 저장
    "C29": "df.std()",  # 표준편차
    "C30": "{col: (df[col].min(), df[col].max()) for col in df.columns}",  # 최대/최소값
    "C31": "(df==0).all(axis=1).sum()",  # 모든 값이 0인 행 개수
    "C32": "df.duplicated(keep=False).sum()",  # 모든 값이 중복인 행 개수
    "C33": "df.count()",  # 결측치가 아닌 값 개수
    "C34": "df.index.nunique()",  # 고유 인덱스 개수
    "C35": "import seaborn as sns; import matplotlib.pyplot as plt; sns.pairplot(df.select_dtypes(include='number')); plt.show()",  # pairplot
    "C36": "df.sort_values(by=df.columns[0], ascending=True)",  # 첫 컬럼 기준 오름차순
    "C37": "df.sort_values(by=df.columns[0], ascending=False)",  # 첫 컬럼 기준 내림차순
    "C38": "df.memory_usage(deep=True).sum() / 1024**2",  # 메모리 사용량(MB)
    "C39": "pd.DataFrame({'col': df.columns, 'dtype': df.dtypes, 'nulls': df.isnull().sum()})",  # 컬럼명, 타입, 결측치
    "C40": "(df<0).all(axis=1).sum()",  # 모든 값이 음수인 행 개수
    
    # 고급 분석 토큰 (C41-C50)
    "C41": "df.skew(numeric_only=True)",  # 왜도 (비대칭도)
    "C42": "df.kurtosis(numeric_only=True)",  # 첨도
    "C43": "df.quantile([0.25, 0.5, 0.75])",  # 사분위수
    "C44": "df.select_dtypes(include='number').apply(lambda x: x.value_counts().head())",  # 수치형 컬럼 최빈값
    "C45": "{col: df[col].nunique()/len(df)*100 for col in df.columns}",  # 컬럼별 고유값 비율(%)
    "C46": "df.apply(lambda x: sum(x.duplicated()))",  # 컬럼별 중복값 개수
    "C47": "import matplotlib.pyplot as plt; df.boxplot(figsize=(12,6)); plt.xticks(rotation=45); plt.show()",  # 박스플롯
    "C48": "df.columns[df.isnull().any()].tolist()",  # 결측치가 있는 컬럼 목록
    "C49": "pd.crosstab(df.iloc[:,0], df.iloc[:,1]) if len(df.columns) >= 2 else 'Need at least 2 columns'",  # 교차표
    "C50": "from src.core.combinations import AdvancedCombinationsAnalyzer; AdvancedCombinationsAnalyzer().analyze_all_combinations(df)",  # 조합 분석
    
    # 특수 기능 토큰
    "SAVE": "save_results",  # 결과 저장 트리거
    "EXPORT": "df.to_csv('analyzed_data.csv', index=False)",  # CSV 내보내기
    "PROFILE": "df.profile_report() if 'profile_report' in dir(df) else print('pandas_profiling not available')",  # 프로파일링
}

def dsl_to_code(dsl_sequence, csv_path="your_file.csv"):
    """Convert a sequence of DSL tokens into executable Python code.

    Parameters
    ----------
    dsl_sequence : list[str]
        Ordered DSL tokens such as ["C1", "C2"].
    csv_path : str, optional
        Path to the CSV file that should be read in the generated code.
        Defaults to "your_file.csv" for backward compatibility.
    """
    # 헤더 생성
    lines = [
        "#!/usr/bin/env python3",
        '"""',
        f'자동 생성된 데이터 분석 코드',
        f'DSL 시퀀스: {" → ".join(dsl_sequence)}',
        f'생성 시간: {_get_timestamp()}',
        '"""',
        "",
        "import pandas as pd",
        "import numpy as np",
        ""
    ]
    
    # 파일 로딩 및 기본 확인
    lines.extend([
        "# 데이터 로딩",
        f"print(' 데이터 로딩: {csv_path}')",
        f"df = pd.read_csv({repr(csv_path)})",
        f"print(f' 데이터 로드 완료: {{len(df):,}}행 × {{len(df.columns)}}열')",
        ""
    ])
    
    # 각 토큰에 대한 코드 생성
    for i, token in enumerate(dsl_sequence, 1):
        code_line = token_code_map.get(token)
        if code_line:
            lines.extend([
                f"# {i}. 분석: {token}",
                f"print('\\n=== {token}: {_get_token_description(token)} ===')",
                "try:",
                f"    result_{i} = {code_line}",
                f"    print(result_{i})",
                "except Exception as e:",
                f"    print(f' {token} 분석 중 오류: {{e}}')",
                ""
            ])
    
    # 푸터 추가
    lines.extend([
        "print('\\n 모든 분석이 완료되었습니다!')",
        f"print(' 총 {len(dsl_sequence)}개의 분석을 수행했습니다.')"
    ])
    
    return "\n".join(lines)

def _get_timestamp():
    """현재 시간 반환"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _get_token_description(token):
    """토큰 설명 반환"""
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
        "C13": "첫 번째 컬럼 값 분포",
        "C14": "전체 기술통계",
        "C15": "데이터 크기",
        "C16": "중복행 개수",
        "C17": "랜덤 샘플 10개",
        "C18": "각 컬럼별 고유값",
        "C19": "데이터 전치",
        "C20": "인덱스 정보",
        "C21": "결측치 포함 행",
        "C22": "각 컬럼별 최빈값",
        "C23": "수치형 히스토그램",
        "C24": "범주형 값 분포",
        "C25": "상관계수 상위 5개",
        "C26": "첫 컬럼 기준 그룹별 평균",
        "C27": "엑셀 파일로 저장",
        "C28": "JSON 파일로 저장",
        "C29": "표준편차",
        "C30": "최대/최소값",
        "C31": "모든 값이 0인 행",
        "C32": "중복 행 개수",
        "C33": "유효값 개수",
        "C34": "고유 인덱스 개수",
        "C35": "수치형 변수 간 관계도",
        "C36": "오름차순 정렬",
        "C37": "내림차순 정렬",
        "C38": "메모리 사용량(MB)",
        "C39": "컬럼 정보 요약",
        "C40": "음수값 행 개수",
        "C41": "왜도 분석",
        "C42": "첨도 분석",
        "C43": "사분위수",
        "C44": "수치형 최빈값",
        "C45": "고유값 비율",
        "C46": "컬럼별 중복값",
        "C47": "박스플롯 시각화",
        "C48": "결측치 컬럼 목록",
        "C49": "교차표 분석",
        "C50": "조합 분석",
        "SAVE": "결과 저장",
        "EXPORT": "CSV 내보내기",
        "PROFILE": "데이터 프로파일링"
    }
    return descriptions.get(token, "알 수 없는 분석")

def generate_analysis_template(analysis_type="basic"):
    """분석 템플릿 생성"""
    templates = {
        "basic": ["C2", "C15", "C6", "C3", "C1"],
        "statistical": ["C1", "C14", "C29", "C41", "C42", "C43"],
        "visualization": ["C12", "C23", "C35", "C47"],
        "missing_data": ["C3", "C11", "C21", "C48"],
        "correlation": ["C8", "C12", "C25", "C50"],
        "comprehensive": ["C2", "C15", "C3", "C1", "C8", "C12", "C23", "C50"]
    }
    return templates.get(analysis_type, templates["basic"])

# 사용 예시:
# basic_analysis = generate_analysis_template("basic")
# code = dsl_to_code(basic_analysis, "data.csv")
# print(code)
