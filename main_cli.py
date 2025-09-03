
#!/usr/bin/env python3
"""
DSL 자동 분석 CLI 도구 - 확장된 버전

ML 기반 DSL 토큰 예측 및 코드 생성 도구입니다.
사용자가 입력한 DSL 토큰을 기반으로 최적의 분석 시퀀스를 예측하고
실행 가능한 Python 코드를 자동 생성합니다.

사용법:
    python main_cli.py
    python main_cli.py --file data.csv --interactive
    python main_cli.py --tokens C1,C2,C6 --output analysis.py
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from inference_dsl import predict_dsl
from dsl2code import dsl_to_code

class DSLAnalyzer:
    """DSL 분석기 클래스"""
    
    def __init__(self, csv_path: str = "your_file.csv"):
        self.csv_path = csv_path
        self.available_tokens = self._get_available_tokens()
    
    def _get_available_tokens(self) -> List[str]:
        """사용 가능한 DSL 토큰 목록 반환"""
        from dsl2code import token_code_map
        return list(token_code_map.keys())
    
    def show_help(self):
        """DSL 토큰 도움말 표시"""
        print("=" * 60)
        print("📋 사용 가능한 DSL 토큰")
        print("=" * 60)
        
        categories = {
            "기본 정보": ["C1", "C2", "C4", "C9", "C15"],
            "데이터 미리보기": ["C6", "C7", "C17", "C19"],
            "결측치 분석": ["C3", "C11", "C21", "C33"],
            "통계 분석": ["C1", "C14", "C29", "C30"],
            "상관관계": ["C8", "C12", "C25"],
            "시각화": ["C12", "C23", "C35"],
            "데이터 조작": ["C36", "C37", "C26"],
            "저장/내보내기": ["C27", "C28"]
        }
        
        from dsl2code import token_code_map
        
        for category, tokens in categories.items():
            print(f"\n🔸 {category}:")
            for token in tokens:
                if token in token_code_map:
                    description = token_code_map[token][:50] + "..." if len(token_code_map[token]) > 50 else token_code_map[token]
                    print(f"  {token}: {description}")
        
        print("\n💡 예시 사용법:")
        print("  C2 C1 C6    # 기본 정보 + 미리보기")
        print("  C3 C11 C21  # 결측치 전체 분석")
        print("  C8 C12 C25  # 상관관계 분석")
    
    def interactive_mode(self):
        """대화형 모드"""
        print("🤖 DSL 대화형 분석 모드")
        print("도움말을 보려면 'help'를 입력하세요.")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
        
        while True:
            try:
                raw = input("\n📝 DSL 토큰 입력 (예: C2 C1 C6): ").strip()
                
                if raw.lower() in ['quit', 'exit', 'q']:
                    print("👋 DSL 분석기를 종료합니다.")
                    break
                elif raw.lower() == 'help':
                    self.show_help()
                    continue
                elif not raw:
                    continue
                
                tokens = raw.split()
                self.analyze_tokens(tokens)
                
            except KeyboardInterrupt:
                print("\n\n👋 사용자가 중단했습니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
    
    def analyze_tokens(self, tokens: List[str], output_file: Optional[str] = None):
        """토큰 분석 및 코드 생성"""
        # 유효한 토큰 확인
        invalid_tokens = [t for t in tokens if t not in self.available_tokens]
        if invalid_tokens:
            print(f"⚠️  알 수 없는 토큰: {invalid_tokens}")
            print("'help' 명령어로 사용 가능한 토큰을 확인하세요.")
            return
        
        print(f"\n🔍 입력된 토큰: {' '.join(tokens)}")
        print("\n[1] ML 모델로 최적 시퀀스 예측 중...")
        
        try:
            predicted = predict_dsl(tokens)
            print(f"🎯 예측된 DSL 시퀀스: {' → '.join(predicted)}")
        except Exception as e:
            print(f"⚠️  예측 실패 (원본 토큰 사용): {e}")
            predicted = tokens
        
        print("\n[2] Python 분석 코드 생성 중...")
        code = dsl_to_code(predicted, self.csv_path)
        
        # 출력 파일 결정
        if not output_file:
            output_file = "generated_analysis.py"
        
        # 코드 저장
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"✅ 코드가 '{output_file}'에 저장되었습니다.")
            
            # 미리보기
            print(f"\n📝 생성된 코드 미리보기:")
            print("-" * 40)
            print(code[:500] + "..." if len(code) > 500 else code)
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="ML 기반 DSL 자동 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main_cli.py                              # 대화형 모드
  python main_cli.py --tokens C1,C2,C6           # 토큰 직접 지정
  python main_cli.py --file data.csv --interactive  # 파일 지정 + 대화형
  python main_cli.py --help-tokens                # 사용 가능한 토큰 보기
        """
    )
    
    parser.add_argument('--file', '-f', 
                       help='분석할 CSV 파일 경로')
    parser.add_argument('--tokens', '-t',
                       help='DSL 토큰 (쉼표로 구분, 예: C1,C2,C6)')
    parser.add_argument('--output', '-o',
                       help='출력 파일 경로 (기본값: generated_analysis.py)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='대화형 모드 실행')
    parser.add_argument('--help-tokens', action='store_true',
                       help='사용 가능한 DSL 토큰 목록 표시')
    
    return parser.parse_args()

def main():
    """메인 함수"""
    args = parse_arguments()
    
    # CSV 파일 경로 설정
    csv_path = args.file if args.file else "your_file.csv"
    
    # 분석기 초기화
    analyzer = DSLAnalyzer(csv_path)
    
    try:
        # 토큰 도움말 모드
        if args.help_tokens:
            analyzer.show_help()
            return
        
        # 토큰이 직접 지정된 경우
        if args.tokens:
            tokens = [token.strip() for token in args.tokens.split(',')]
            analyzer.analyze_tokens(tokens, args.output)
            return
        
        # 대화형 모드 또는 기본 모드
        if args.interactive:
            analyzer.interactive_mode()
        else:
            print("=== DSL 자동 분석기 ===")
            
            # 파일 존재 확인
            if args.file and not Path(args.file).exists():
                print(f"⚠️  파일을 찾을 수 없습니다: {args.file}")
                print("계속 진행하면 생성된 코드에서 파일 경로를 수정해야 합니다.")
            
            # 한 번만 실행하는 기본 모드
            raw = input("DSL 토큰을 입력하세요 (예: C2 C1 C6): ").strip()
            if raw:
                tokens = raw.split()
                analyzer.analyze_tokens(tokens, args.output)
            else:
                print("❌ 토큰이 입력되지 않았습니다.")
                
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
