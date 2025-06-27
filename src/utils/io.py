from pathlib import Path
import numpy as np
import pandas as pd

def load_instance(path: str | Path):
    """
    Formatos suportados:
      1) Low-dimensional TXT (linha 'n C', seguidas de 'value weight')
      2) Formato simples (n, \n, C, \n, 'weight value')
      3) Large-scale CSV (_info.csv + _items.csv)
    Retorna (weights, values, capacity).
    """
    path = Path(path)

    # --- large-scale CSV ---
    if path.suffix == ".csv":
        if not path.name.endswith("_info.csv"):
            raise ValueError("Use o arquivo *_info.csv.")

        base    = path.stem.replace("_info", "")
        folder  = path.parent
        items_f = folder / f"{base}_items.csv"

        info = pd.read_csv(path, header=None, names=["label", "value"])
        capacity = int(info.loc[info["label"] == "c", "value"].values[0])

        items = pd.read_csv(items_f, header=None, names=["value", "weight"])
        values  = items["value"].to_numpy(dtype=int)
        weights = items["weight"].to_numpy(dtype=int)
        return weights, values, capacity

    # --- formatos TXT ---
    with open(path, "r", encoding="utf-8") as f:
        header = f.readline().split()

        if len(header) == 2:                             # Pisinger
            n, capacity = map(int, header)
            values, weights = [], []
            for _ in range(n):
                v, w = map(float, f.readline().split())
                values.append(int(round(v)))
                weights.append(int(round(w)))
            return np.array(weights), np.array(values), capacity

        elif len(header) == 1:                           # simples
            n = int(header[0])
            capacity = int(f.readline())
            weights, values = [], []
            for _ in range(n):
                w, v = map(int, f.readline().split())
                weights.append(w)
                values.append(v)
            return np.array(weights), np.array(values), capacity

        else:
            raise ValueError(f"Formato desconhecido em {path}")
