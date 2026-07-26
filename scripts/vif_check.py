"""
Multikollinearitaetspruefung (CLAUDE.md Abschnitt 6) per Variance Inflation
Factor (VIF) vor der multiplen Regression (Schritt 3).
"""

import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler

IN_PATH = "data/processed/messpunkte_long.csv"
SIGNALS = ["isp_max", "isp_mittel", "isp_std", "iz_max", "iz_mittel", "iz_std"]


def compute_vif(df, cols):
    X = StandardScaler().fit_transform(df[cols])
    X = pd.DataFrame(X, columns=cols)
    vifs = [variance_inflation_factor(X.values, i) for i in range(len(cols))]
    return pd.Series(vifs, index=cols).sort_values(ascending=False)


def main():
    df = pd.read_csv(IN_PATH)
    da = df[df["werkstoff"] == "DA718"].dropna(subset=SIGNALS)

    print("=== VIF: alle 6 Signalkennzahlen ===")
    print(compute_vif(da, SIGNALS).round(2))

    reduced = ["isp_mittel", "iz_max", "iz_std"]
    print(f"\n=== VIF: reduziertes Set {reduced} ===")
    print(compute_vif(da, reduced).round(2))


if __name__ == "__main__":
    main()
