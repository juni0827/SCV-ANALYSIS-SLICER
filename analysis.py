
from __future__ import annotations
import numpy as np
import pandas as pd

EXT_NUM_STATS = ("count", "mean", "std", "min", "25%", "50%", "75%", "max")

def column_profile(df: pd.DataFrame, col: str) -> dict:
    """Compute summary statistics for a single DataFrame column.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the column to profile.
    col : str
        Name of the column to analyze.

    Returns
    -------
    dict
        A mapping of metric names to values such as dtype, missing counts,
        summary statistics and additional shape metrics when the column is
        numeric.
    """
    s = df[col]
    info = {
        "dtype": str(s.dtype),
        "nulls": int(s.isna().sum()),
        "unique": int(s.nunique(dropna=True)),
        "missing_pct": float(s.isna().mean() * 100.0),
    }
    if pd.api.types.is_numeric_dtype(s):
        desc = s.describe()
        for k in EXT_NUM_STATS:
            if k in desc:
                info[k] = float(desc[k])
        # extra shape metrics
        vals = s.dropna().values.astype(float)
        if len(vals) > 2:
            info["median"] = float(np.median(vals))
            info["iqr"] = float(np.percentile(vals, 75) - np.percentile(vals, 25))
            info["skew"] = float(pd.Series(vals).skew())
            info["kurtosis"] = float(pd.Series(vals).kurtosis())
    return info

def quick_eda(df: pd.DataFrame) -> dict:
    """Generate basic exploratory data analysis information for a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The input data.

    Returns
    -------
    dict
        Row and column counts along with per-column dtypes and null counts.
    """
    out = {
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "nulls_by_col": {c: int(df[c].isna().sum()) for c in df.columns},
    }
    return out
