"""
Pipeline-Schritt 5 (CLAUDE.md Abschnitt 5): Random Forest / Gradient
Boosting, gleiches Validierungsprotokoll wie Regression (Schritt 3+4),
damit die Ergebnisse fair vergleichbar sind. Stichprobe ist klein
(~138-140 Punkte), daher bewusst einfache/konservative Hyperparameter
und Train- vs. Test-RMSE als Overfitting-Check (rmse_train_mean).
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cv_utils import group_cv_evaluate, summarize_folds

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_PATH = "results/models/full_model_comparison.csv"

ALL_SIGNALS = ["isp_max", "isp_mittel", "isp_std", "iz_max", "iz_mittel", "iz_std"]
REDUCED_SIGNALS = ["isp_mittel", "iz_max", "iz_std"]
TARGETS = ["VB", "VBmax"]

FEATURE_SETS = {
    "reduced (VIF<1.2)": REDUCED_SIGNALS,
    "all6": ALL_SIGNALS,
}

PROTOCOLS = {
    "LOTO (werkzeug_id)": "werkzeug_id",
    "LODO (scheibe_id)": "scheibe_id",
}

MODEL_FACTORIES = {
    "linear_regression": lambda: make_pipeline(StandardScaler(), LinearRegression()),
    "random_forest": lambda: RandomForestRegressor(
        n_estimators=200, max_depth=3, min_samples_leaf=5, random_state=0
    ),
    "gradient_boosting": lambda: GradientBoostingRegressor(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=5, random_state=0
    ),
}


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

                for model_name, factory in MODEL_FACTORIES.items():
                    folds = group_cv_evaluate(factory, X, y, groups)
                    summary = summarize_folds(folds)
                    summary["target"] = target
                    summary["feature_set"] = fset_name
                    summary["protocol"] = proto_name
                    summary["model"] = model_name
                    summary["n_obs"] = len(sub)
                    results.append(summary)

    res_df = pd.DataFrame(results)[
        ["target", "protocol", "feature_set", "model", "n_obs", "n_folds",
         "rmse_mean", "rmse_std", "rmse_train_mean", "mae_mean", "mae_std", "r2_mean", "r2_std"]
    ]
    res_df["overfit_gap"] = res_df["rmse_mean"] - res_df["rmse_train_mean"]
    res_df = res_df.sort_values(["target", "protocol", "feature_set", "rmse_mean"])

    import os
    os.makedirs("results/models", exist_ok=True)
    res_df.to_csv(OUT_PATH, index=False)

    pd.set_option("display.width", 200)
    print("=== Modellvergleich: linear vs. Random Forest vs. Gradient Boosting (LOTO + LODO) ===")
    print(res_df.round(3).to_string(index=False))
    print(f"\nGeschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
