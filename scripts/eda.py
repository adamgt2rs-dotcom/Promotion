"""
Explorative Datenanalyse (Pipeline-Schritt 1, CLAUDE.md Abschnitt 5).
Fokus: DA718 (Lochkreis "aussen") als Hauptwerkstoff. IN718 nur zum
groben Streuungsvergleich (Detailanalyse ist optional, Schritt 7).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

IN_PATH = "data/processed/messpunkte_long.csv"
OUT_DIR = "results/eda"

SIGNALS = ["isp_max", "isp_mittel", "isp_std", "iz_max", "iz_mittel", "iz_std"]
WEAR = ["VB", "VBmax"]


def main():
    df = pd.read_csv(IN_PATH)
    da = df[df["werkstoff"] == "DA718"].copy()

    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Verteilungen VB / VBmax (DA718)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, col in zip(axes, WEAR):
        ax.hist(da[col], bins=15, color="steelblue", edgecolor="white")
        ax.set_title(f"Verteilung {col} (DA718)")
        ax.set_xlabel(f"{col} [µm]")
        ax.set_ylabel("Anzahl Messpunkte")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/wear_distributions.png", dpi=150)
    plt.close(fig)

    # 2. Verschleissverlauf pro Werkzeug, facettiert nach Scheibe
    scheiben = sorted(da["scheibe_id"].unique())
    fig, axes = plt.subplots(1, len(scheiben), figsize=(4 * len(scheiben), 4), sharey=True)
    for ax, sid in zip(axes, scheiben):
        sub = da[da["scheibe_id"] == sid]
        for wid, g in sub.groupby("werkzeug_id"):
            g = g.sort_values("bohrung_nr")
            ax.plot(g["bohrung_nr"], g["VB"], marker="o", alpha=0.7, label=f"WZ {wid}")
        ax.set_title(f"Scheibe {sid} (DA718)")
        ax.set_xlabel("Bohrung Nr.")
        ax.set_xticks([2, 6, 10, 14, 18])
    axes[0].set_ylabel("VB [µm]")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/wear_progression_by_tool.png", dpi=150)
    plt.close(fig)

    # 3. Streudiagramme Signalkennzahl vs. Verschleiss
    fig, axes = plt.subplots(len(SIGNALS), 2, figsize=(9, 3 * len(SIGNALS)))
    for i, sig in enumerate(SIGNALS):
        for j, w in enumerate(WEAR):
            ax = axes[i, j]
            ax.scatter(da[sig], da[w], s=12, alpha=0.6, c=da["scheibe_id"], cmap="viridis")
            r = da[sig].corr(da[w])
            ax.set_title(f"{sig} vs {w}  (r={r:.2f})", fontsize=9)
            ax.set_xlabel(sig, fontsize=8)
            ax.set_ylabel(w, fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/signal_vs_wear_scatter.png", dpi=150)
    plt.close(fig)

    # 4. Korrelationsmatrix (Signale + VB/VBmax) -> Multikollinearitaet
    corr = da[SIGNALS + WEAR].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns, fontsize=8)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Korrelationsmatrix Signalkennzahlen & Verschleiss (DA718)")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/correlation_matrix.png", dpi=150)
    plt.close(fig)
    corr.to_csv(f"{OUT_DIR}/correlation_matrix.csv")

    # 5. Scheibenvergleich (Kennzahlen)
    disk_summary = da.groupby("scheibe_id").agg(
        n_werkzeuge=("werkzeug_id", "nunique"),
        n_messpunkte=("werkzeug_id", "size"),
        VB_mean=("VB", "mean"),
        VB_std=("VB", "std"),
        VB_max=("VB", "max"),
        VBmax_mean=("VBmax", "mean"),
        VBmax_std=("VBmax", "std"),
        VBmax_max=("VBmax", "max"),
    )
    disk_summary.to_csv(f"{OUT_DIR}/disk_summary.csv")

    # 6. DA718 vs IN718 grober Streuungsvergleich
    material_summary = df.groupby("werkstoff").agg(
        n_messpunkte=("werkzeug_id", "size"),
        VB_mean=("VB", "mean"),
        VB_std=("VB", "std"),
        VB_cv=("VB", lambda x: x.std() / x.mean()),
        VBmax_mean=("VBmax", "mean"),
        VBmax_std=("VBmax", "std"),
        VBmax_cv=("VBmax", lambda x: x.std() / x.mean()),
    )
    material_summary.to_csv(f"{OUT_DIR}/material_summary.csv")

    print("=== Scheibenvergleich (DA718) ===")
    print(disk_summary)
    print()
    print("=== Werkstoffvergleich (DA718 vs IN718, alle Scheiben) ===")
    print(material_summary)
    print()
    print("=== Korrelationen Signalkennzahl vs. Verschleiss (DA718) ===")
    print(corr.loc[SIGNALS, WEAR])
    print()
    print(f"Plots und Tabellen geschrieben nach {OUT_DIR}/")


if __name__ == "__main__":
    main()
