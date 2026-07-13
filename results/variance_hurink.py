"""
Berechnet pro Hurink-FJSP-Instanz (edata, rdata, vdata) die durchschnittliche
Varianz der Processing Times ueber die eligible Maschinen jeder Operation.

Fuer jede Operation mit mehreren eligible Maschinen wird die (Populations-)
Varianz der zugehoerigen Processing Times berechnet. Der Wert pro Instanz
ist der Mittelwert dieser Operations-Varianzen ueber alle Operationen der
Instanz.

Ergebnis wird als Excel-Tabelle in results/variance_hurink.xlsx gespeichert.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "fjsp"
DATASETS = ["edata", "rdata", "vdata"]


def parse_instance_operation_variances(file_path: Path) -> list[float]:
    """Liest eine .fjs Datei und gibt fuer jede Operation die Varianz der
    Processing Times ueber ihre eligible Maschinen zurueck."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    header = re.findall(r"\S+", lines[0])
    number_total_jobs = int(header[0])

    operation_variances = []

    for line in lines[1:1 + number_total_jobs]:
        parsed = re.findall(r"\S+", line)
        if not parsed:
            continue
        i = 1  # parsed[0] ist die Anzahl Operationen des Jobs
        while i < len(parsed):
            operation_options = int(parsed[i])
            durations = [
                int(parsed[i + 2 + 2 * k]) for k in range(operation_options)
            ]
            operation_variances.append(float(np.var(durations)))
            i += 1 + 2 * operation_options

    return operation_variances


def main():
    results = {}
    instance_names = None

    for dataset in DATASETS:
        dataset_dir = DATA_DIR / dataset
        files = sorted(dataset_dir.glob("*.fjs"))
        variances = {}
        for file_path in files:
            op_variances = parse_instance_operation_variances(file_path)
            variances[file_path.stem] = float(np.mean(op_variances))
        results[dataset] = variances
        if instance_names is None:
            instance_names = sorted(variances.keys())

    df = pd.DataFrame(index=instance_names, columns=DATASETS, dtype=float)
    for dataset in DATASETS:
        for instance in instance_names:
            df.loc[instance, dataset] = results[dataset].get(instance, np.nan)

    # Durchschnitt pro Datensatz ueber alle 66 Instanzen
    average_row = df.mean(axis=0)
    # Wie stark die Varianz ueber die 66 Instanzen selbst variiert (Std.abw.)
    std_row = df.std(axis=0, ddof=0)

    df.loc["Average"] = average_row
    df.loc["Std over instances"] = std_row

    output_path = BASE_DIR / "results" / "variance_hurink.xlsx"
    df.to_excel(output_path, sheet_name="variance_hurink")
    print(f"Ergebnis gespeichert unter: {output_path}")
    print(df.tail(5))


if __name__ == "__main__":
    main()
