"""
Deliverable 3 (CLAUDE.md Abschnitt 7): Abbildung mit geschaetztem vs.
gemessenem Verschleiss fuer ein Beispielwerkzeug.

Hinweis: die durchgehende Signaltabelle fuer *alle* Bohrungen (Schritt 6)
liegt noch nicht vor. Diese Version nutzt daher Out-of-fold-Vorhersagen
(Leave-one-tool-out) an den 5 gemessenen Punkten je Werkzeug als
Naeherung. Sobald die vollstaendigen Bohrungsdaten vorliegen, kann
dasselbe Modell auf jede einzelne Bohrung angewendet werden (Schritt 6),
was eine durchgehende statt nur 5-Punkte-Kurve ergibt.
"""

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_PATH = "results/figures/example_tool_reconstruction.png"
REDUCED_SIGNALS = ["isp_mittel", "iz_max", "iz_std"]
EXAMPLE_TOOL = 8  # Scheibe 1, unauffaellig (nicht das WZ7-Sonderfall-Werkzeug)


def oof_predict_for_tool(da, target, tool_id, model_factory):
    train = da[da["werkzeug_id"] != tool_id]
    test = da[da["werkzeug_id"] == tool_id].sort_values("bohrung_nr")
    model = model_factory()
    model.fit(train[REDUCED_SIGNALS], train[target])
    pred = model.predict(test[REDUCED_SIGNALS])
    return test["bohrung_nr"].values, test[target].values, pred


def main():
    df = pd.read_csv(IN_PATH)
    da = df[df["werkstoff"] == "DA718"].dropna(subset=REDUCED_SIGNALS)

    linear_factory = lambda: make_pipeline(StandardScaler(), LinearRegression())
    gb_factory = lambda: GradientBoostingRegressor(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=5, random_state=0
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, target in zip(axes, ["VB", "VBmax"]):
        bohrungen, measured, pred_lin = oof_predict_for_tool(da, target, EXAMPLE_TOOL, linear_factory)
        _, _, pred_gb = oof_predict_for_tool(da, target, EXAMPLE_TOOL, gb_factory)

        ax.plot(bohrungen, measured, "o-", color="black", label="gemessen", linewidth=2)
        ax.plot(bohrungen, pred_lin, "s--", color="tab:blue", label="geschätzt (lineare Regr., reduziert)")
        ax.plot(bohrungen, pred_gb, "^--", color="tab:orange", label="geschätzt (Gradient Boosting)")
        ax.set_title(f"{target}, Werkzeug {EXAMPLE_TOOL} (Scheibe 1, DA718)")
        ax.set_xlabel("Bohrung Nr.")
        ax.set_ylabel(f"{target} [µm]")
        ax.set_xticks([2, 6, 10, 14, 18])
        ax.legend(fontsize=8)

    fig.suptitle(
        "Vorläufig: Out-of-fold-Schätzung an 5 Messpunkten (LOTO)\n"
        "— volle Bohrungskurve folgt nach Schritt 6 (durchgehende Signaldaten)",
        fontsize=9,
    )
    fig.tight_layout()

    import os
    os.makedirs("results/figures", exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Geschrieben: {OUT_PATH}")


if __name__ == "__main__":
    main()
