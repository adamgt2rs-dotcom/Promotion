"""
Pipeline-Schritt 3 (CLAUDE.md Abschnitt 5): multiple lineare Regression.
Kombiniert mehrere Signalkennzahlen -> VB/VBmax. Nach VIF-Pruefung
(vif_check.py) werden zwei Feature-Sets verglichen:
  - "alle 6 Signale"     (zeigt den Effekt der Multikollinearitaet)
  - "reduziert"          (isp_mittel, iz_max, iz_std; alle VIF < 1.2)
Validierung: Leave-one-tool-out (Hauptprotokoll) UND Leave-one-disk-out
(strengerer Test, Schritt 4), gleiches Protokoll wie fuer die Baseline,
damit die Ergebnisse fair vergleichbar sind.
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cv_utils import group_cv_evaluate, summarize_folds

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_PATH = "results/models/multiple_regression_comparison.csv"

ALL_SIGNALS = ["isp_max", "isp_mittel", "isp_std", "iz_max", "iz_mittel", "iz_std"]
REDUCED_SIGNALS = ["isp_mittel", "iz_max", "iz_std"]
TARGETS = ["VB", "VBmax"]

FEATURE_SETS = {
    "single_best (isp_mittel)": ["isp_mittel"],
    "multiple_all6": ALL_SIGNALS,
    "multiple_reduced (VIF<1.2)": REDUCED_SIGNALS,
}

PROTOCOLS = {
    "LOTO (werkzeug_id)": "werkzeug_id",
    "LODO (scheibe_id)": "scheibe_id",
}


def model_factory():
    return make_pipeline(StandardScaler(), LinearRegression())


def main():
    df = pd.read_csv(IN_PATH)
    da = df[df["werkstoff"] == "DA718"].copy()

    results = []
    for target in TARGETS:
        for fset_name, cols in FEATURE_SETS.items():
            sub = da.dropna(subset=cols + [target])
            X = sub[cols]
            y = sub[target]

            for proto_name, group_col in PROTOCOLS.items():
                groups = sub[group_col]
                folds = group_cv_evaluate(model_factory, X, y, groups)
                summary = summarize_folds(folds)
                summary["target"] = target
                summary["feature_set"] = fset_name
                summary["protocol"] = proto_name
                summary["n_obs"] = len(sub)
                results.append(summary)

    res_df = pd.DataFrame(results)[
        ["target", "protocol", "feature_set", "n_obs", "n_folds",
         "rmse_mean", "rmse_std", "mae_mean", "mae_std", "r2_mean", "r2_std"]
    ]
    res_df = res_df.sort_values(["target", "protocol", "rmse_mean"])

    import os
    os.makedirs("results/models", exist_ok=True)
    res_df.to_csv(OUT_PATH, index=False)

    pd.set_option("display.width", 160)
    print("=== Vergleich: single-best vs. multiple Regression (alle 6 vs. reduziert), LOTO + LODO ===")
    print(res_df.round(3).to_string(index=False))
    print(f"\nGeschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
