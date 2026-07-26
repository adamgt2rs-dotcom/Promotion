"""
Import des Master-Datensatzes (Werkstück/Werkzeug/iba/VB) aus dem Excel-Rohformat
in das Long-Format-Schema gemaess CLAUDE.md Abschnitt 3.

Spaltengruppen im Rohformat: ws{scheibe}{lochkreis}, z.B. ws1a, ws2m, ws3i.
  - scheibe: Nummer der Turbinenscheibe (1-4)
  - lochkreis-Suffix:
      a = aussen  -> Werkstoff DA718 (realer Werkstoff, hohe Streuung durch
                     Spannungs-/Temperaturgradienten und lokale Materialheterogenitaeten)
      m = mittel  -> Werkstoff IN718
      i = innen   -> Werkstoff IN718
Jede Gruppe hat 10 Spalten: [werkzeug_id, Bohrungen, isp_max, isp_mittel, isp_std,
iz_max, iz_mittel, iz_std, vb_avg, vbmax]. Die werkzeug_id steht nur in der ersten
Zeile jedes 5-Zeilen-Blocks (ein Block = 5 Messpunkte eines Werkzeugs) und muss
nach unten aufgefuellt werden (forward fill).
"""

import pandas as pd

RAW_PATH = "data/raw/master_ws_wz_iba_vb.xlsx"
OUT_PATH = "data/processed/messpunkte_long.csv"

SUFFIX_TO_LOCHKREIS = {"a": "aussen", "m": "mittel", "i": "innen"}
SUFFIX_TO_WERKSTOFF = {"a": "DA718", "m": "IN718", "i": "IN718"}

COLS_PER_GROUP = [
    "werkzeug_id_raw", "bohrung_nr",
    "isp_max", "isp_mittel", "isp_std",
    "iz_max", "iz_mittel", "iz_std",
    "vb_avg", "vbmax",
]


def main():
    raw = pd.read_excel(RAW_PATH, sheet_name="Tabelle1", header=0)
    header = list(raw.columns)

    # Gruppen anhand der ersten Spalte jeder 10er-Bloecke identifizieren
    # (Spaltenname der ersten Spalte jeder Gruppe = "ws{n}{suffix}")
    n_groups = len(header) // 10
    frames = []

    for gi in range(n_groups):
        start = gi * 10
        group_name = header[start]  # z.B. "ws1a"
        scheibe = int(group_name[2])
        suffix = group_name[3]

        block = raw.iloc[:, start:start + 10].copy()
        block.columns = COLS_PER_GROUP
        block["werkzeug_id_raw"] = block["werkzeug_id_raw"].ffill()
        block = block.dropna(subset=["bohrung_nr"])

        block["scheibe_id"] = scheibe
        block["lochkreis"] = SUFFIX_TO_LOCHKREIS[suffix]
        block["werkstoff"] = SUFFIX_TO_WERKSTOFF[suffix]
        block["werkzeug_id"] = block["werkzeug_id_raw"].astype(int)
        block["bohrung_nr"] = block["bohrung_nr"].astype(int)

        frames.append(block)

    long_df = pd.concat(frames, ignore_index=True)
    long_df = long_df.rename(columns={"vb_avg": "VB", "vbmax": "VBmax"})

    # Bekannter Datenfehler: Scheibe 1, Werkzeug 7, Bohrung 2 und 14 - waehrend
    # dieser Bohrungen fand ein Lochkreis-Wechsel auf derselben Scheibe statt,
    # wodurch die iz-Kennzahlen (Vorschubachsenstrom) verfaelscht aufgezeichnet
    # wurden (isp-Kennzahlen sind davon nicht betroffen). VB/VBmax bleiben
    # gueltige Verschleissmessungen des Werkzeugs und werden nicht veraendert.
    iz_cols = ["iz_max", "iz_mittel", "iz_std"]
    bad = (
        (long_df["scheibe_id"] == 1)
        & (long_df["werkzeug_id"] == 7)
        & (long_df["bohrung_nr"].isin([2, 14]))
    )
    long_df.loc[bad, iz_cols] = pd.NA

    long_df = long_df[[
        "scheibe_id", "lochkreis", "werkstoff", "werkzeug_id", "bohrung_nr",
        "VB", "VBmax",
        "isp_max", "isp_mittel", "isp_std",
        "iz_max", "iz_mittel", "iz_std",
    ]].sort_values(["scheibe_id", "lochkreis", "werkzeug_id", "bohrung_nr"])

    long_df.to_csv(OUT_PATH, index=False)

    print(f"Geschrieben: {OUT_PATH}  ({len(long_df)} Zeilen)")
    print()
    print("Werkzeuge und Messpunkte je scheibe_id x werkstoff x lochkreis:")
    summary = long_df.groupby(["scheibe_id", "werkstoff", "lochkreis"]).agg(
        n_werkzeuge=("werkzeug_id", "nunique"),
        n_messpunkte=("werkzeug_id", "size"),
    )
    print(summary)
    print()
    print(f"Gesamt Messpunkte: {len(long_df)}")
    print(f"DA718 (aussen) Messpunkte: {(long_df['werkstoff'] == 'DA718').sum()}")
    print(f"IN718 (mittel+innen) Messpunkte: {(long_df['werkstoff'] == 'IN718').sum()}")


if __name__ == "__main__":
    main()
