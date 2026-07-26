"""
Pipeline-Schritt 2 (CLAUDE.md Abschnitt 5): Baseline einfache lineare
Regression. Eine Signalkennzahl -> VB (und separat -> VBmax), je Kennzahl
einzeln. Validierung: Leave-one-tool-out CV (Hauptprotokoll, Schritt 4),
damit auch die Baseline schon leakage-frei bewertet wird.
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cv_utils import group_cv_evaluate, summarize_folds

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_PATH = "results/models/baseline_simple_regression.csv"

SIGNALS = ["isp_max", "isp_mittel", "isp_std", "iz_max", "iz_mittel", "iz_std"]
TARGETS = ["VB", "VBmax"]


def model_factory():
    return make_pipeline(StandardScaler(), LinearRegression())


def main():
    df = pd.read_csv(IN_PATH)
    da = df[df["werkstoff"] == "DA718"].copy()

    results = []
    for target in TARGETS:
        for sig in SIGNALS:
            sub = da.dropna(subset=[sig, target])
            X = sub[[sig]]
            y = sub[target]
            groups = sub["werkzeug_id"]

            folds = group_cv_evaluate(model_factory, X, y, groups)
            summary = summarize_folds(folds)
            summary["target"] = target
            summary["signal"] = sig
            summary["n_obs"] = len(sub)
            results.append(summary)

    res_df = pd.DataFrame(results)[
        ["target", "signal", "n_obs", "n_folds",
         "rmse_mean", "rmse_std", "mae_mean", "mae_std", "r2_mean", "r2_std"]
    ]
    res_df = res_df.sort_values(["target", "rmse_mean"])

    import os
    os.makedirs("results/models", exist_ok=True)
    res_df.to_csv(OUT_PATH, index=False)

    pd.set_option("display.width", 140)
    print("=== Baseline einfache lineare Regression (Leave-one-tool-out CV, DA718) ===")
    print(res_df.round(3).to_string(index=False))
    print(f"\nGeschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
