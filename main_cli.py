
# main_cli.py
# Entry point for CLI-based DSL analysis tool

from inference_dsl import predict_dsl
from dsl2code import dsl_to_code

def main():
    print("=== DSL AUTO ANALYZER CLI ===")
    raw = input("Enter DSL tokens separated by space (e.g., C2 C1 C6): ").strip()
    tokens = raw.split()

    print("\n[1] Predicting DSL sequence using trained model...")
    predicted = predict_dsl(tokens)
    print("Predicted DSL:", " → ".join(predicted))

    print("\n[2] Generating Python analysis code...")
    code = dsl_to_code(predicted)
    print(code)

    with open("generated_analysis.py", "w", encoding="utf-8") as f:
        f.write(code)

    print("\n✅ Code saved to 'generated_analysis.py'")

if __name__ == "__main__":
    main()
