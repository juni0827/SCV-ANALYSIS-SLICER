
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
    "C10": "df.memory_usage()"
    # Add more mappings as needed
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
    lines = [
        "import pandas as pd",
        f"df = pd.read_csv({repr(csv_path)})",
        ""
    ]
    for token in dsl_sequence:
        code_line = token_code_map.get(token)
        if code_line:
            lines.append(f"print('>>> {token}:')\n{code_line}")
    return "\n".join(lines)

# Example:
# dsl = ['C1', 'C2', 'C6']
# print(dsl_to_code(dsl, 'data.csv'))
