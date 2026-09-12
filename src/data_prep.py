"""Préparation des données : chargement, contrôle qualité, correction, segments."""
import io
import sys
from typing import Optional

import numpy as np
import pandas as pd

from src.config import CLEAN_CSV, DATA_URL, RAW_CSV, TARGET

try:
    import requests
except ImportError:
    requests = None  # chargement via URL désactivé


def load_data(source_path: Optional[str] = None) -> pd.DataFrame:
    """Charge depuis un chemin explicite, sinon le CSV brut versionné dans le repo,
    sinon l'URL Hugging Face en dernier recours — pour que le pipeline tourne même
    si data/raw/ n'est pas disponible (ex. exécution hors du repo complet)."""
    if source_path:
        df = pd.read_csv(source_path)
    elif RAW_CSV.exists():
        df = pd.read_csv(RAW_CSV)
    else:
        if requests is None:
            raise RuntimeError("Aucun fichier local et module 'requests' absent.")
        resp = requests.get(DATA_URL, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df


def quick_overview(df: pd.DataFrame) -> None:
    """Diagnostic rapide + garde-fou : échoue tôt si la colonne cible est absente,
    plutôt que de laisser une erreur confuse plus loin dans le pipeline."""
    print(f"[INFO] {df.shape[0]} lignes x {df.shape[1]} colonnes")
    print(f"[INFO] Manquantes : {df.isna().sum().sum()} | Doublons : {df.duplicated().sum()}")
    if TARGET not in df.columns:
        raise ValueError(f"Colonne cible '{TARGET}' absente.")
    print(f"[INFO] Taux d'acceptation : {100 * df[TARGET].mean():.2f}%")


def fix_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Corrige les valeurs négatives d'Experience (erreur de saisie connue)."""
    n = int((df["Experience"] < 0).sum())
    if n:
        print(f"[FIX] {n} valeurs d'Experience negatives -> valeur absolue")
        df["Experience"] = df["Experience"].abs()
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les doublons exacts ; le compte supprimé est loggé pour repérer
    un éventuel problème d'extraction en amont plutôt que de nettoyer en silence."""
    before = len(df)
    df = df.drop_duplicates().copy()
    if len(df) != before:
        print(f"[INFO] {before - len(df)} doublons supprimes")
    return df


def add_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Tranches d'âge et de revenu pour la BI.
    right=False : bornes basses incluses, aligné sur la logique SQL
    (30 -> '30-50', 50 -> '<50k'->'50-100k', etc.)."""
    df = df.copy()
    df["Age_Group"] = pd.cut(df["Age"], bins=[0, 30, 50, 70, np.inf],
                             labels=["<30", "30-50", "50-70", "70+"],
                             right=False)
    df["Income_Group"] = pd.cut(df["Income"], bins=[0, 50, 100, 150, np.inf],
                                labels=["<50k", "50-100k", "100-150k", "150k+"],
                                right=False)
    return df

def run(source_path: Optional[str] = None) -> pd.DataFrame:
    """Pipeline complet de préparation."""
    df = load_data(source_path)
    quick_overview(df)
    df = drop_duplicates(df)
    df = fix_experience(df)
    df = add_segments(df)
    CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8")
    print(f"[OK] Export : {CLEAN_CSV} ({len(df)} lignes)")
    return df


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
