"""
Pipeline-Schritt 7 (optional, CLAUDE.md Abschnitt 5): gleiche Pipeline auf
IN718 anwenden und Ergebnis DA718 gegenueberstellen (Diskussionspunkt:
bestaetigt hoehere DA718-Streuung als werkstoffbedingt, nicht methodisch
bedingt). Gleiches reduziertes Feature-Set (isp_mittel, iz_max, iz_std),
VIF fuer IN718 separat geprueft (alle < 1.8) - Set ist fuer beide
Werkstoffe gueltig, Vergleich also methodisch fair.
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cv_utils import group_cv_evaluate, summarize_folds

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_PATH = "results/models/da718_vs_in718_comparison.csv"

REDUCED_SIGNALS = ["isp_mittel", "iz_max", "iz_std"]
TARGETS = ["VB", "VBmax"]

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

    results = []
    for werkstoff in ["DA718", "IN718"]:
        sub_material = df[df["werkstoff"] == werkstoff]
        for target in TARGETS:
            sub = sub_material.dropna(subset=REDUCED_SIGNALS + [target])
            X = sub[REDUCED_SIGNALS]
            y = sub[target]
            groups = sub["werkzeug_id"]  # LOTO als Hauptprotokoll

            for model_name, factory in MODEL_FACTORIES.items():
                folds = group_cv_evaluate(factory, X, y, groups)
                summary = summarize_folds(folds)
                summary["werkstoff"] = werkstoff
                summary["target"] = target
                summary["model"] = model_name
                summary["n_obs"] = len(sub)
                summary["target_mean"] = y.mean()
                summary["target_std"] = y.std()
                summary["target_cv"] = y.std() / y.mean()
                results.append(summary)

    res_df = pd.DataFrame(results)
    res_df["rmse_rel_pct"] = 100 * res_df["rmse_mean"] / res_df["target_mean"]
    res_df = res_df[
        ["werkstoff", "target", "model", "n_obs", "n_folds",
         "target_mean", "target_std", "target_cv",
         "rmse_mean", "rmse_rel_pct", "mae_mean", "r2_mean", "r2_std"]
    ].sort_values(["target", "model", "werkstoff"])

    import os
    os.makedirs("results/models", exist_ok=True)
    res_df.to_csv(OUT_PATH, index=False)

    pd.set_option("display.width", 200)
    print("=== DA718 vs. IN718: Streuung und Modellguete (LOTO-CV, reduziertes Feature-Set) ===")
    print(res_df.round(3).to_string(index=False))
    print(f"\nGeschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
