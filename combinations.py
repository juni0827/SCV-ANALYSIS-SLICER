
from __future__ import annotations
import numpy as np, pandas as pd
from itertools import combinations

def _split_types(df, max_cardinality=50):
    num, cat = [], []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            num.append(c)
        else:
            if df[c].nunique(dropna=True) <= max_cardinality:
                cat.append(c)
    return num, cat

def _value_counts_top(s: pd.Series, top_k=20):
    vc = s.astype("object").value_counts(dropna=False).head(top_k)
    total = len(s)
    return [{"value": str(k), "count": int(v), "ratio": float(v/total)} for k, v in vc.items()]

def _lift_table(df, a, b, top_k=20):
    x = df[a].astype("object")
    y = df[b].astype("object")
    ct = pd.crosstab(x, y)
    total = ct.values.sum()
    if total == 0 or ct.shape[0] == 0 or ct.shape[1] == 0:
        return []
    px = ct.sum(axis=1)/total
    py = ct.sum(axis=0)/total
    expected = np.outer(px.values, py.values) * total
    lift = ct.values / np.maximum(expected, 1e-9)
    rows = []
    xi = list(ct.index); yi = list(ct.columns)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            rows.append({
                "a_val": str(xi[i]),
                "b_val": str(yi[j]),
                "count": int(ct.values[i,j]),
                "lift": float(lift[i,j])
            })
    rows.sort(key=lambda r: (r["lift"]*np.log1p(r["count"])), reverse=True)
    return rows[:top_k]

def _pearson_spearman(df, x, y, method="pearson"):
    s1, s2 = df[x], df[y]
    s1, s2 = s1.replace([np.inf, -np.inf], np.nan), s2.replace([np.inf, -np.inf], np.nan)
    s = pd.concat([s1, s2], axis=1).dropna()
    if len(s) < 3: return None
    if method == "spearman":
        r = s.corr(method="spearman").iloc[0,1]
    else:
        r = s.corr(method="pearson").iloc[0,1]
    return float(r)

def _anova_eta2(df, cat, num):
    s = df[[cat, num]].dropna()
    if s[cat].nunique() < 2: return None
    groups = [g[num].values for _, g in s.groupby(cat)]
    overall = s[num].values
    grand_mean = overall.mean()
    ss_between = sum(len(g)*(g.mean()-grand_mean)**2 for g in groups)
    ss_total = ((overall - grand_mean)**2).sum()
    eta2 = float(ss_between/ss_total) if ss_total > 0 else 0.0
    return eta2

def analyze_combinations(df: pd.DataFrame, *, max_cardinality=50, top_k=20, sample_cap=200_000):
    if len(df) > sample_cap:
        df = df.sample(sample_cap, random_state=42)

    num_cols, cat_cols = _split_types(df, max_cardinality=max_cardinality)
    report = {"meta": {
        "rows": int(len(df)), "num_cols": num_cols, "cat_cols": cat_cols,
        "params": {"top_k": top_k, "max_cardinality": max_cardinality}
    }}

    univariate = {}
    for c in cat_cols:
        univariate[c] = _value_counts_top(df[c], top_k=top_k)
    report["univariate"] = univariate

    cc_pairs = []
    for a, b in combinations(cat_cols, 2):
        rows = _lift_table(df, a, b, top_k=top_k)
        if rows:
            cc_pairs.append({"cols": (a,b), "pairs": rows})
    report["catcat"] = cc_pairs

    nn_pairs = []
    for a, b in combinations(num_cols, 2):
        r_p = _pearson_spearman(df, a, b, "pearson")
        r_s = _pearson_spearman(df, a, b, "spearman")
        if r_p is not None or r_s is not None:
            nn_pairs.append({"cols": (a,b), "pearson": r_p, "spearman": r_s})
    nn_pairs.sort(key=lambda x: max(abs(x.get("pearson") or 0.0), abs(x.get("spearman") or 0.0)), reverse=True)
    report["numnum"] = nn_pairs[:top_k]

    cn_pairs = []
    for c in cat_cols:
        for n in num_cols:
            eta2 = _anova_eta2(df, c, n)
            if eta2 is not None:
                cn_pairs.append({"cols": (c, n), "eta2": eta2})
    cn_pairs.sort(key=lambda x: x["eta2"], reverse=True)
    report["catnum"] = cn_pairs[:top_k]

    return report

def suggest_plots(report):
    recs = []
    for entry in report.get("catcat", [])[:3]:
        a, b = entry["cols"]
        recs.append({"type": "heatmap", "cols": [a,b], "why": "high lift co-occurrence"})
    for entry in report.get("numnum", [])[:3]:
        a, b = entry["cols"]
        recs.append({"type": "scatter", "cols": [a,b], "why": "strong correlation"})
    for entry in report.get("catnum", [])[:3]:
        c, n = entry["cols"]
        recs.append({"type": "box", "cols": [c,n], "why": "large between-group variance"})
    return recs
