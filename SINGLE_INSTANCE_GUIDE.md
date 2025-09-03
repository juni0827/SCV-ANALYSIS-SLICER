# 단일 인스턴스 애플리케이션 구현 가이드

## 개요
CSV Analyzer 애플리케이션이 단일 인스턴스로 동작하도록 개선되었습니다. 이제 EXE 파일을 여러 번 실행해도 하나의 창만 열립니다.

## 구현된 기능

### 1. 단일 인스턴스 관리 (`single_instance.py`)
- **Windows 뮤텍스**: Windows 환경에서 시스템 전역 뮤텍스 사용
- **크로스 플랫폼 지원**: 다른 OS에서는 락 파일 방식 사용
- **프로세스 감지**: 실제로 프로세스가 실행 중인지 확인
- **자동 정리**: 애플리케이션 종료 시 리소스 자동 정리

### 2. 메인 애플리케이션 통합 (`app.py`)
- **최소한의 수정**: 기존 코드에 3줄만 추가
- **우아한 처리**: 중복 실행 시 사용자에게 메시지 표시
- **안전한 종료**: 리소스 정리를 포함한 완전한 cleanup

### 3. 빌드 설정 개선
- **PyInstaller 최적화**: 단일 인스턴스 모듈 포함
- **크기 최적화**: 불필요한 모듈 제외
- **Windows 호환성**: 필요한 ctypes 모듈 포함

## 사용법

### 빌드 방법
```bash
# Windows 배치 파일 사용
build.bat

# 또는 Python 스크립트 사용
python build.py

# 또는 PyInstaller 직접 사용
python -m PyInstaller csv_analyzer.spec
```

### 테스트 방법
1. 빌드된 `dist/CSV-Analyzer.exe` 실행
2. 같은 EXE 파일을 다시 더블클릭
3. 새 창이 열리지 않고 메시지가 표시되는지 확인
4. 기존 창이 앞으로 나오는지 확인

## 기술적 세부사항

### 단일 인스턴스 감지 방식
1. **Windows**: `CreateMutexW` API 사용
   - 전역 뮤텍스 생성: `Global\\CSV-Analyzer-SingleInstance-Mutex`
   - `ERROR_ALREADY_EXISTS` 반환 시 중복 실행 감지

2. **다른 플랫폼**: 락 파일 사용
   - 파일 위치: `/tmp/CSV-Analyzer.lock` (Unix) 또는 `%TEMP%\CSV-Analyzer.lock` (Windows 백업)
   - PID 기반 프로세스 존재 여부 확인

### 메모리 및 성능
- **오버헤드**: 거의 없음 (뮤텍스 1개 또는 작은 락 파일)
- **시작 시간**: 무시할 수 있는 지연 (< 10ms)
- **메모리 사용**: 추가 메모리 사용량 거의 없음

### 오류 처리
- **Fallback 메커니즘**: Windows API 실패 시 락 파일로 전환
- **Dead Lock 방지**: 프로세스 종료 감지 및 자동 정리
- **예외 안전성**: 모든 오류 상황에서 안전한 동작

## 파일 구조

```
├── single_instance.py      # 단일 인스턴스 관리 모듈
├── app.py                 # 메인 애플리케이션 (수정됨)
├── csv_analyzer.spec      # PyInstaller 빌드 설정
├── build.bat             # Windows 빌드 스크립트
├── build.py              # Python 빌드 스크립트
├── test_single_instance.py  # 단일 인스턴스 테스트
├── validate_build.py     # 빌드 설정 검증
└── requirements.txt      # 의존성 (PyInstaller 추가됨)
```

## 빌드 프로세스

1. **전제 조건 확인**: 필요한 파일 및 모듈 존재 여부
2. **단일 인스턴스 테스트**: 기능 동작 확인
3. **정리**: 이전 빌드 파일 삭제
4. **빌드**: PyInstaller로 EXE 생성
5. **검증**: 생성된 파일 확인

## 문제 해결

### 일반적인 문제
1. **뮤텍스 생성 실패**: 락 파일 방식으로 자동 전환
2. **권한 문제**: 임시 디렉토리 권한 확인
3. **빌드 실패**: `validate_build.py`로 설정 확인

### 디버깅
```python
# 단일 인스턴스 테스트
python test_single_instance.py

# 빌드 설정 검증
python validate_build.py

# 수동 테스트
python single_instance.py
```

## 향후 개선 사항
- [ ] 시스템 트레이 통합
- [ ] 명령줄 인수 전달
- [ ] 네트워크 기반 인스턴스 통신
- [ ] 설정 가능한 인스턴스 이름