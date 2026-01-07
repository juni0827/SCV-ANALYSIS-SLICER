#!/usr/bin/env python3
"""
DSL Automatic Analysis CLI Tool - Extended Version

ML-based DSL token prediction and code generation tool.
Predicts optimal analysis sequences based on user-input DSL tokens and
automatically creates executable Python code.

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
    """DSL analyzer class"""

    def __init__(self, csv_path: str = "your_file.csv"):
        self.csv_path = csv_path
        self.available_tokens = self._get_available_tokens()

    def _get_available_tokens(self) -> List[str]:
        """Return list of available DSL tokens"""
        return list(TOKEN_HANDLERS.keys())

    def show_help(self):
        """Display DSL token help"""
        print("=" * 60)
        print(" Available DSL Tokens (Extended)")
        print("=" * 60)

        categories = {
            "Basic Information": ["C1", "C2", "C4", "C9", "C15"],
            "Data Preview": ["C6", "C7", "C17", "C19"],
            "Missing Value Analysis": ["C3", "C11", "C21", "C33", "C48"],
            "Statistical Analysis": [
                "C1",
                "C14",
                "C29",
                "C30",
                "C41",
                "C42",
                "C43",
                "C58",
                "C59",
            ],
            "Correlation": ["C8", "C12", "C25", "C56", "C57"],
            "Visualization": ["C12", "C23", "C35", "C47", "C54", "C60", "C61"],
            "Data Manipulation": ["C36", "C37", "C26", "C46"],
            "Advanced Analysis (ML)": ["C50", "C51", "C52", "C53", "C55"],
            "Utilities": ["C27", "C28", "SAVE", "EXPORT", "PROFILE"],
        }

        for category, tokens in categories.items():
            print(f"\n {category}:")
            for token in tokens:
                if token in TOKEN_HANDLERS:
                    description = _get_token_description(token)
                    print(f"  {token}: {description}")

        print("\n Example Usage:")
        print("  C2 C1 C6          # Default Information + Preview")
        print("  C3 C11 C21 C48    # In-depth missing value analysis")
        print("  C51 C52 C53       # Time series, outlier, PCA analysis (advanced)")

    def analysis_mode(self):
        """Analysis mode"""
        print("\n" + "=" * 60)
        print("DSL Analysis Mode")
        print("=" * 60)

        while True:
            print("\n[Main Menu]")
            print("1.Use recommended template")
            print("2.Select by category")
            print("3.Direct input")
            print("0.Exit")

            choice = input("\nSelect > ").strip()

            if choice == "1":
                self._wizard_template()
            elif choice == "2":
                self._wizard_category()
            elif choice == "3":
                return  # Return to interactive mode's manual input
            elif choice == "0":
                sys.exit(0)
            else:
                print("Invalid selection.")

    def _wizard_template(self):
        print("\n[Recommended Templates]")
        templates = {
            "basic": "Basic analysis (data structure, top rows, missing values)",
            "statistical": "Statistical analysis (descriptive statistics, distribution, skewness/kurtosis)",
            "visualization": "Visualization package (histogram, box plot, heatmap)",
            "missing_data": "In-depth missing value analysis",
            "correlation": "Correlation analysis",
            "advanced_ml": "Advanced ML analysis (time series, outlier, PCA)",
            "comprehensive": "Comprehensive analysis (includes all major analyses)",
        }

        keys = list(templates.keys())
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key:<15} : {templates[key]}")

        try:
            sel = input("\nSelect template number (cancel: 0) > ").strip()
            if sel == "0":
                return

            idx = int(sel) - 1
            if 0 <= idx < len(keys):
                selected_key = keys[idx]
                tokens = generate_analysis_template(selected_key)
                print(f"\nSelected template: {selected_key}")
                self.analyze_tokens(tokens)
                input("\nPress Enter to return to menu...")
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")

    def _wizard_category(self):
        selected_tokens = []
        categories = {
            "Basic Information": ["C1", "C2", "C4", "C9", "C15"],
            "Data Preview": ["C6", "C7", "C17", "C19"],
            "Missing Value Analysis": ["C3", "C11", "C21", "C33", "C48"],
            "Statistical Analysis": [
                "C1",
                "C14",
                "C29",
                "C30",
                "C41",
                "C42",
                "C43",
                "C58",
                "C59",
            ],
            "Correlation": ["C8", "C12", "C25", "C56", "C57"],
            "Visualization": ["C12", "C23", "C35", "C47", "C54", "C60", "C61"],
            "Advanced Analysis (ML)": ["C50", "C51", "C52", "C53", "C55"],
        }

        print("\n[Select by Category]")
        print("Select the required analysis from each category.")

        for cat, tokens in categories.items():
            print(f"\n📂 {cat}")
            available = [t for t in tokens if t in TOKEN_HANDLERS]

            # Show options
            for i, t in enumerate(available, 1):
                desc = _get_token_description(t)
                print(f"  {i}. {desc} ({t})")

            sel = input(
                f"  Numbers to select (comma separated, skip: Enter) > "
            ).strip()
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
                    print("  Invalid input. Skipping.")

        if selected_tokens:
            print(f"\nFinally selected tokens: {selected_tokens}")
            self.analyze_tokens(selected_tokens)
            input("\nPress Enter to return to menu...")
        else:
            print("\nNo tokens selected.")

    def interactive_mode(self):
        """Interactive mode"""
        print(" DSL Interactive Analysis Mode")
        print("Enter 'help' to see help.")
        print("Enter 'analysis' to run analysis mode.")
        print("Enter 'quit' or 'exit' to exit.")

        while True:
            try:
                raw = input("\n Enter DSL tokens (e.g., C2 C1 C6): ").strip()

                if raw.lower() in ["quit", "exit", "q"]:
                    print(" Exiting DSL analyzer.")
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
                print("\n\n User interrupted.")
                break
            except Exception as e:
                print(f" Error occurred: {e}")

    def analyze_tokens(self, tokens: List[str], output_file: Optional[str] = None):
        """Token analysis and code generation"""
        # Valid token confirmation
        invalid_tokens = [t for t in tokens if t not in self.available_tokens]
        if invalid_tokens:
            print(f"  Unknown tokens: {invalid_tokens}")
            print("Use 'help' command to check available tokens.")
            return

        print(f"\n Entered tokens: {' '.join(tokens)}")
        print("\n[1] Predicting optimal sequence with ML model...")

        try:
            predicted = predict_dsl(tokens)
            print(f" Predicted DSL sequence: {' → '.join(predicted)}")
        except Exception as e:
            print(f"  Prediction failed (using original tokens): {e}")
            predicted = tokens

        print("\n[2] Generating Python analysis code...")
        code = dsl_to_code(predicted, self.csv_path)

        # Determine output file
        if not output_file:
            output_file = "generated_analysis.py"

        # Save code
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f" Code '{output_file}'saved to.")

            # Preview
            print(f"\n Preview of generated code:")
            print("-" * 40)
            print(code[:500] + "..." if len(code) > 500 else code)
            print("-" * 40)

        except Exception as e:
            print(f" File save failed: {e}")


def parse_arguments():
    """Command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="ML-based DSL automatic analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python main_cli.py                              # Interactive mode
  python main_cli.py --tokens C1,C2,C6           # Specify tokens directly
  python main_cli.py --file data.csv --interactive  # Specify file + interactive
  python main_cli.py --help-tokens                # View available tokens
        """,
    )

    parser.add_argument("--file", "-f", help="Path to CSV file to analyze")
    parser.add_argument(
        "--tokens", "-t", help="DSL tokens (comma separated, e.g., C1,C2,C6)"
    )
    parser.add_argument(
        "--output", "-o", help="Output file path (default: generated_analysis.py)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run interactive mode"
    )
    parser.add_argument(
        "--help-tokens",
        action="store_true",
        help="Display list of available DSL tokens",
    )

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()

    # CSV File Path Configuration
    csv_path = args.file if args.file else "your_file.csv"

    # Initialize analyzer
    analyzer = DSLAnalyzer(csv_path)

    try:
        # Token Help Mode
        if args.help_tokens:
            analyzer.show_help()
            return

        # When tokens are specified directly
        if args.tokens:
            tokens = [token.strip() for token in args.tokens.split(",")]
            analyzer.analyze_tokens(tokens, args.output)
            return

        # Interactive mode or default mode
        if args.interactive:
            analyzer.interactive_mode()
        else:
            print("=== DSL Automatic Analyzer ===")

            # File existence confirmation
            if args.file and not Path(args.file).exists():
                print(f"  File not found: {args.file}")
                print(
                    "If you continue, you will need to modify the file path in the generated code."
                )

            # Suggest analysis mode
            print("Tip: Enter 'analysis' to use menu-based analysis mode.")

            # Default mode (one-time execution)
            raw = input("Enter DSL tokens (e.g., C2 C1 C6) or 'analysis': ").strip()

            if raw.lower() == "analysis":
                analyzer.analysis_mode()
            elif raw:
                tokens = raw.split()
                analyzer.analyze_tokens(tokens, args.output)
            else:
                print(" No tokens entered.")

    except Exception as e:
        print(f" Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
