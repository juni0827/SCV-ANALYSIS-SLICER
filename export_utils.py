from __future__ import annotations
from pathlib import Path
import pandas as pd
import json


def save_dataframe(df: pd.DataFrame, path: str, fmt: str = "CSV") -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fmt = fmt.upper()
    if fmt == "CSV":
        if p.suffix.lower() != ".csv":
            p = p.with_suffix(".csv")
        df.to_csv(p, index=False)
    elif fmt == "EXCEL":
        if p.suffix.lower() not in (".xlsx", ".xls"):
            p = p.with_suffix(".xlsx")
        df.to_excel(p, index=False)
    elif fmt == "JSON":
        if p.suffix.lower() != ".json":
            p = p.with_suffix(".json")
        df.to_json(p, orient="records", force_ascii=False)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return str(p)


def save_analysis_report(report: dict, path: str) -> str:
    p = Path(path)
    if p.suffix.lower() != ".json":
        p = p.with_suffix(".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)
