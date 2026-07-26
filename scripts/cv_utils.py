"""
Gemeinsame Kreuzvalidierungs-Hilfsfunktionen fuer alle Modellierungsschritte
(CLAUDE.md Abschnitt 5, Schritt 4): gruppenbasiert nach Werkzeug (leave-one-
tool-out, Hauptprotokoll) bzw. nach Scheibe (leave-one-disk-out, strengerer
Test der Generalisierung). Kein zufaelliger Split.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def group_cv_evaluate(model_factory, X, y, groups):
    """
    model_factory: Funktion ohne Argumente, die ein frisches (unfitted)
                   sklearn-Pipeline/Modell zurueckgibt.
    X: DataFrame/array der Features.
    y: Series/array des Zielwerts.
    groups: Series/array der Gruppen-IDs (werkzeug_id oder scheibe_id).

    Gibt ein DataFrame mit einer Zeile je Fold (RMSE, MAE, R2, n_test) zurueck.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    groups = np.asarray(groups)

    rows = []
    for g in np.unique(groups):
        test_mask = groups == g
        train_mask = ~test_mask
        if train_mask.sum() < 2 or test_mask.sum() < 1:
            continue

        model = model_factory()
        model.fit(X[train_mask], y[train_mask])
        pred = model.predict(X[test_mask])
        pred_train = model.predict(X[train_mask])

        y_test = y[test_mask]
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        mae = mean_absolute_error(y_test, pred)
        rmse_train = np.sqrt(mean_squared_error(y[train_mask], pred_train))
        # R2 braucht mind. 2 Testpunkte mit Varianz, sonst undefiniert
        r2 = r2_score(y_test, pred) if (test_mask.sum() >= 2 and np.var(y_test) > 0) else np.nan

        rows.append({
            "group": g, "n_test": int(test_mask.sum()),
            "rmse": rmse, "mae": mae, "r2": r2, "rmse_train": rmse_train,
        })

    return pd.DataFrame(rows)


def summarize_folds(fold_df):
    return pd.Series({
        "rmse_mean": fold_df["rmse"].mean(),
        "rmse_std": fold_df["rmse"].std(),
        "mae_mean": fold_df["mae"].mean(),
        "mae_std": fold_df["mae"].std(),
        "r2_mean": fold_df["r2"].mean(skipna=True),
        "r2_std": fold_df["r2"].std(skipna=True),
        "rmse_train_mean": fold_df["rmse_train"].mean(),
        "n_folds": len(fold_df),
    })
