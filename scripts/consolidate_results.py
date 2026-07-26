"""
Deliverable 1 (CLAUDE.md Abschnitt 7): Vergleichstabelle aller Modelle
(einfache Regression je Kennzahl, multiple Regression, Random Forest,
Gradient Boosting) mit CV-Metriken, getrennt fuer VB und VBmax.
Fasst die Ergebnisse aus baseline_simple_regression.csv,
multiple_regression_comparison.csv und full_model_comparison.csv
in einer einheitlichen Tabelle zusammen (LOTO-Protokoll als gemeinsamer
Nenner, da fuer alle drei Skripte verfuegbar).
"""

import pandas as pd

OUT_PATH = "results/models/master_comparison_LOTO.csv"


def main():
    simple = pd.read_csv("results/models/baseline_simple_regression.csv")
    simple["model_type"] = "einfache Regression (1 Signal)"
    simple["detail"] = simple["signal"]
    simple["protocol"] = "LOTO (werkzeug_id)"  # baseline script nutzt nur LOTO

    multi = pd.read_csv("results/models/multiple_regression_comparison.csv")
    multi = multi[multi["protocol"] == "LOTO (werkzeug_id)"].copy()
    multi["model_type"] = multi["feature_set"].map({
        "single_best (isp_mittel)": "einfache Regression (1 Signal)",
        "multiple_all6": "multiple Regression (alle 6)",
        "multiple_reduced (VIF<1.2)": "multiple Regression (VIF-reduziert)",
    })
    multi["detail"] = multi["feature_set"]
    # single_best ist bereits in `simple` enthalten -> hier nur die multiplen behalten
    multi = multi[multi["model_type"] != "einfache Regression (1 Signal)"]

    ml = pd.read_csv("results/models/full_model_comparison.csv")
    ml = ml[(ml["protocol"] == "LOTO (werkzeug_id)") & (ml["feature_set"] == "reduced (VIF<1.2)")].copy()
    ml["model_type"] = ml["model"].map({
        "linear_regression": "multiple Regression (VIF-reduziert)",
        "random_forest": "Random Forest (VIF-reduziert)",
        "gradient_boosting": "Gradient Boosting (VIF-reduziert)",
    })
    ml = ml[ml["model_type"] != "multiple Regression (VIF-reduziert)"]  # Duplikat zu `multi`
    ml["detail"] = ml["feature_set"]

    cols = ["target", "model_type", "detail", "n_obs", "n_folds",
            "rmse_mean", "rmse_std", "mae_mean", "mae_std", "r2_mean", "r2_std"]

    master = pd.concat([simple[cols], multi[cols], ml[cols]], ignore_index=True)
    master = master.sort_values(["target", "rmse_mean"])
    master.to_csv(OUT_PATH, index=False)

    pd.set_option("display.width", 160)
    print("=== Gesamtvergleich aller Modelle (LOTO-CV, DA718) ===")
    print(master.round(3).to_string(index=False))
    print(f"\nGeschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
