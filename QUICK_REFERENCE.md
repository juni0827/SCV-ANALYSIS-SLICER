# 🚀 SCV-ANALYSIS-SLICER 빠른 참조 카드

> **전체 분석**: [ANALYSIS_REPORT.md](ANALYSIS_REPORT.md) | **한글 요약**: [분석_요약_한글.md](분석_요약_한글.md)

---

## ⚡ 1분 요약

**무엇인가요?**  
ML 기반 자동 분석을 갖춘 CSV 데이터 분석 플랫폼 (Python)

**왜 좋은가요?**  
✅ 분석 시간 90% 단축  
✅ 무료 오픈소스  
✅ 코딩 불필요 (GUI)  
✅ 대용량 파일 처리  

**평가**: ⭐⭐⭐⭐☆ (4.5/5)

---

## 🎯 핵심 기능 3가지

### 1. 🤖 ML 자동 분석
```bash
python main_cli.py --tokens C1,C2,C6 --file data.csv
# → 실행 가능한 Python 코드 자동 생성
```

### 2. 📊 고급 조합 분석
- 컬럼 간 숨은 관계 자동 발견
- 상관관계, 연관규칙, ANOVA
- 병렬 처리로 빠른 분석

### 3. 🎨 현대적 GUI
```bash
python app.py
# → 다크/라이트 테마, 백그라운드 처리
```

---

## 📊 성능

| 작업 | 시간 | 비교 |
|------|------|------|
| CSV 로딩 (100MB) | 1.2초 | Excel 크래시 |
| 조합 분석 (20 컬럼) | 15초 | 수동 60초 |
| 메모리 사용 | -30% | 최적화 적용 |

---

## 🏗️ 구조

```
src/
├── core/      # 데이터, 분석, 조합
├── dsl/       # ML 기반 DSL (PyTorch)
├── gui/       # Tkinter GUI
└── utils/     # 유틸리티
```

**코드**: ~9,000 라인 (23개 모듈)

---

## 💻 빠른 시작

### GUI 실행
```bash
pip install -r requirements.txt
python app.py
```

### CLI 사용
```bash
# 대화형
python main_cli.py --interactive

# 템플릿
python main_cli.py --template statistical --file data.csv
```

### 빌드
```bash
python build.py
# → dist/CSV-Analyzer.exe
```

---

## 🌟 차별점

| 기능 | SCV | Excel | Tableau |
|------|-----|-------|---------|
| ML | ✅ | ❌ | ❌ |
| 대용량 | ✅ | ❌ | ✅ |
| 무료 | ✅ | ❌ | ❌ |
| 병렬 | ✅ | ❌ | ⚠️ |

---

## 🎯 누가 쓰나요?

✅ 데이터 분석가  
✅ 데이터 과학자  
✅ 연구자  
✅ 학생  
✅ 중소기업  

---

## 📈 로드맵

**지금 (1개월)**  
- [ ] 프로그레스 바  
- [ ] 작업 취소  
- [ ] 로깅  

**중기 (2-3개월)**  
- [ ] 설정 파일  
- [ ] 테스트 확대  
- [ ] API 문서  

**장기 (4-6개월)**  
- [ ] DB 연결  
- [ ] 웹 버전  
- [ ] 국제화  

---

## �� 최종 평가

**한 줄**: "상용급 무료 데이터 분석 플랫폼"

**점수**: 4.5/5 ⭐⭐⭐⭐☆

**추천**: 
- 개인/소규모: ⭐⭐⭐⭐⭐
- 중대형: ⭐⭐⭐⭐
- 학습: ⭐⭐⭐⭐⭐

---

**더 알아보기**:
- 📄 [전체 분석 보고서](ANALYSIS_REPORT.md)
- 📝 [한글 요약](분석_요약_한글.md)
- 📖 [README](README.md)
- 🏗️ [구조](STRUCTURE.md)
