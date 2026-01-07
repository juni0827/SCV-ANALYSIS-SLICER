#!/usr/bin/env python3
"""
DSL Automatic 분석 CLI Tool - 확장된 버전

ML based DSL token Yes측 및 Code generation Tool입니다.
Use자가 Input한 DSL token을 based으로 최적의 분석 시퀀스를 Yes측하고
Execution Available한 Python 코드를 Automatic Create합니다.

Usage:
    python main_cli.py
    python main_cli.py --file data.csv --interactive
    python main_cli.py --tokens C1,C2,C6 --output analysis.py
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from src.dsl.inference_dsl import predict_dsl
from src.dsl.dsl2code import (
    dsl_to_code,
    TOKEN_HANDLERS,
    _get_token_description,
    generate_analysis_template,
)


class DSLAnalyzer:
    """DSL 분석기 Class"""

    def __init__(self, csv_path: str = "your_file.csv"):
        self.csv_path = csv_path
        self.available_tokens = self._get_available_tokens()

    def _get_available_tokens(self) -> List[str]:
        """Use Available한 DSL token 목록 Return"""
        return list(TOKEN_HANDLERS.keys())

    def show_help(self):
        """DSL token Help 표시"""
        print("=" * 60)
        print(" 사용 가능한 DSL 토큰 (확장됨)")
        print("=" * 60)

        categories = {
            "기본 정보": ["C1", "C2", "C4", "C9", "C15"],
            "데이터 미리보기": ["C6", "C7", "C17", "C19"],
            "결측치 분석": ["C3", "C11", "C21", "C33", "C48"],
            "통계 분석": ["C1", "C14", "C29", "C30", "C41", "C42", "C43", "C58", "C59"],
            "상관관계": ["C8", "C12", "C25", "C56", "C57"],
            "시각화": ["C12", "C23", "C35", "C47", "C54", "C60", "C61"],
            "데이터 조작": ["C36", "C37", "C26", "C46"],
            "고급 분석 (ML)": ["C50", "C51", "C52", "C53", "C55"],
            "유틸리티": ["C27", "C28", "SAVE", "EXPORT", "PROFILE"],
        }

        for category, tokens in categories.items():
            print(f"\n {category}:")
            for token in tokens:
                if token in TOKEN_HANDLERS:
                    description = _get_token_description(token)
                    print(f"  {token}: {description}")

        print("\n 예시 사용법:")
        print("  C2 C1 C6          # Default Information + 미리보기")
        print("  C3 C11 C21 C48    # 심층 결측치 분석")
        print("  C51 C52 C53       # 시계열, 이상치, PCA 분석 (고급)")

    def analysis_mode(self):
        """분석 Mode"""
        print("\n" + "=" * 60)
        print("DSL 분석 모드")
        print("=" * 60)

        while True:
            print("\n[메인 메뉴]")
            print("1.추천 템플릿 사용")
            print("2.카테고리별 선택")
            print("3.직접 입력")
            print("0.종료")

            choice = input("\n선택 > ").strip()

            if choice == "1":
                self._wizard_template()
            elif choice == "2":
                self._wizard_category()
            elif choice == "3":
                return  # Return to interactive mode's manual input
            elif choice == "0":
                sys.exit(0)
            else:
                print("잘못된 선택입니다.")

    def _wizard_template(self):
        print("\n[추천 템플릿]")
        templates = {
            "basic": "기본 분석 (데이터 구조, 상위 행, 결측치)",
            "statistical": "통계 분석 (기술통계, 분포, 왜도/첨도)",
            "visualization": "시각화 패키지 (히스토그램, 박스플롯, 히트맵)",
            "missing_data": "결측치 심층 분석",
            "correlation": "상관관계 분석",
            "advanced_ml": "고급 ML 분석 (시계열, 이상치, PCA)",
            "comprehensive": "종합 분석 (모든 주요 분석 포함)",
        }

        keys = list(templates.keys())
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key:<15} : {templates[key]}")

        try:
            sel = input("\n템플릿 번호 선택 (취소: 0) > ").strip()
            if sel == "0":
                return

            idx = int(sel) - 1
            if 0 <= idx < len(keys):
                selected_key = keys[idx]
                tokens = generate_analysis_template(selected_key)
                print(f"\n선택된 템플릿: {selected_key}")
                self.analyze_tokens(tokens)
                input("\n엔터를 누르면 메뉴로 돌아갑니다...")
            else:
                print("잘못된 번호입니다.")
        except ValueError:
            print("숫자를 입력해주세요.")

    def _wizard_category(self):
        selected_tokens = []
        categories = {
            "기본 정보": ["C1", "C2", "C4", "C9", "C15"],
            "데이터 미리보기": ["C6", "C7", "C17", "C19"],
            "결측치 분석": ["C3", "C11", "C21", "C33", "C48"],
            "통계 분석": ["C1", "C14", "C29", "C30", "C41", "C42", "C43", "C58", "C59"],
            "상관관계": ["C8", "C12", "C25", "C56", "C57"],
            "시각화": ["C12", "C23", "C35", "C47", "C54", "C60", "C61"],
            "고급 분석 (ML)": ["C50", "C51", "C52", "C53", "C55"],
        }

        print("\n[카테고리별 선택]")
        print("각 카테고리에서 필요한 분석을 선택하세요.")

        for cat, tokens in categories.items():
            print(f"\n📂 {cat}")
            available = [t for t in tokens if t in TOKEN_HANDLERS]

            # Show options
            for i, t in enumerate(available, 1):
                desc = _get_token_description(t)
                print(f"  {i}. {desc} ({t})")

            sel = input(f"  선택할 번호 (쉼표 구분, 건너뛰기: 엔터) > ").strip()
            if sel:
                try:
                    indices = [
                        int(x.strip()) for x in sel.split(",") if x.strip().isdigit()
                    ]
                    for idx in indices:
                        if 1 <= idx <= len(available):
                            token = available[idx - 1]
                            if token not in selected_tokens:
                                selected_tokens.append(token)
                except ValueError:
                    print("  잘못된 입력입니다. 건너뜁니다.")

        if selected_tokens:
            print(f"\n최종 선택된 토큰: {selected_tokens}")
            self.analyze_tokens(selected_tokens)
            input("\n엔터를 누르면 메뉴로 돌아갑니다...")
        else:
            print("\n선택된 토큰이 없습니다.")

    def interactive_mode(self):
        """대화형 Mode"""
        print(" DSL 대화형 분석 모드")
        print("도움말을 보려면 'help'를 입력하세요.")
        print("분석 모드를 실행하려면 'analsis'를 입력하세요.")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")

        while True:
            try:
                raw = input("\n DSL 토큰 입력 (예: C2 C1 C6): ").strip()

                if raw.lower() in ["quit", "exit", "q"]:
                    print(" DSL 분석기를 종료합니다.")
                    break
                elif raw.lower() == "help":
                    self.show_help()
                    continue
                elif raw.lower() == "analysis":
                    self.analysis_mode()
                    continue
                elif not raw:
                    continue

                tokens = raw.split()
                self.analyze_tokens(tokens)

            except KeyboardInterrupt:
                print("\n\n 사용자가 중단했습니다.")
                break
            except Exception as e:
                print(f" 오류 발생: {e}")

    def analyze_tokens(self, tokens: List[str], output_file: Optional[str] = None):
        """Token 분석 및 Code generation"""
        # Valid한 Token Confirmation
        invalid_tokens = [t for t in tokens if t not in self.available_tokens]
        if invalid_tokens:
            print(f"  알 수 없는 토큰: {invalid_tokens}")
            print("'help' 명령어로 사용 가능한 토큰을 확인하세요.")
            return

        print(f"\n 입력된 토큰: {' '.join(tokens)}")
        print("\n[1] ML 모델로 최적 시퀀스 예측 중...")

        try:
            predicted = predict_dsl(tokens)
            print(f" 예측된 DSL 시퀀스: {' → '.join(predicted)}")
        except Exception as e:
            print(f"  예측 실패 (원본 토큰 사용): {e}")
            predicted = tokens

        print("\n[2] Python 분석 코드 생성 중...")
        code = dsl_to_code(predicted, self.csv_path)

        # Output File 결정
        if not output_file:
            output_file = "generated_analysis.py"

        # 코드 Save
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f" 코드가 '{output_file}'에 저장되었습니다.")

            # 미리보기
            print(f"\n 생성된 코드 미리보기:")
            print("-" * 40)
            print(code[:500] + "..." if len(code) > 500 else code)
            print("-" * 40)

        except Exception as e:
            print(f" 파일 저장 실패: {e}")


def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="ML 기반 DSL 자동 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python main_cli.py                              # 대화형 Mode
  python main_cli.py --tokens C1,C2,C6           # Token 직접 지정
  python main_cli.py --file data.csv --interactive  # File 지정 + 대화형
  python main_cli.py --help-tokens                # Use Available한 Token 보기
        """,
    )

    parser.add_argument("--file", "-f", help="분석할 CSV 파일 경로")
    parser.add_argument("--tokens", "-t", help="DSL 토큰 (쉼표로 구분, 예: C1,C2,C6)")
    parser.add_argument(
        "--output", "-o", help="출력 파일 경로 (기본값: generated_analysis.py)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="대화형 모드 실행"
    )
    parser.add_argument(
        "--help-tokens", action="store_true", help="사용 가능한 DSL 토큰 목록 표시"
    )

    return parser.parse_args()


def main():
    """메인 Function"""
    args = parse_arguments()

    # CSV File Path Configuration
    csv_path = args.file if args.file else "your_file.csv"

    # 분석기 Initialize
    analyzer = DSLAnalyzer(csv_path)

    try:
        # Token Help Mode
        if args.help_tokens:
            analyzer.show_help()
            return

        # Token이 직접 지정된 경우
        if args.tokens:
            tokens = [token.strip() for token in args.tokens.split(",")]
            analyzer.analyze_tokens(tokens, args.output)
            return

        # 대화형 Mode or Default Mode
        if args.interactive:
            analyzer.interactive_mode()
        else:
            print("=== DSL 자동 분석기 ===")

            # File 존재 Confirmation
            if args.file and not Path(args.file).exists():
                print(f"  파일을 찾을 수 없습니다: {args.file}")
                print("계속 진행하면 생성된 코드에서 파일 경로를 수정해야 합니다.")

            # Suggest analysis mode
            print(
                "팁: 'analysis'를 입력하면 메뉴 방식의 분석 모드를 사용할 수 있습니다."
            )

            # 한 번만 Execution하는 Default Mode
            raw = input(
                "DSL 토큰을 입력하세요 (예: C2 C1 C6) 또는 'analysis': "
            ).strip()

            if raw.lower() == "analysis":
                analyzer.analysis_mode()
            elif raw:
                tokens = raw.split()
                analyzer.analyze_tokens(tokens, args.output)
            else:
                print(" 토큰이 입력되지 않았습니다.")

    except Exception as e:
        print(f" 예상치 못한 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
