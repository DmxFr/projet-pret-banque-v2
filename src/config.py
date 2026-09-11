"""Chemins et constantes du projet — une seule source de vérité."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
RAPPORTS_DIR = PROJECT_ROOT / "rapports"

RAW_CSV        = DATA_RAW / "Bank_Personal_Loan_Modelling.csv"
CLEAN_CSV      = DATA_PROCESSED / "Bank_Personal_Loan_Clean.csv"
PREDICTIONS_CSV = DATA_PROCESSED / "predictions_clients.csv"
MODEL_PATH     = MODELS_DIR / "modele_pret.joblib"

DATA_URL = ("https://huggingface.co/datasets/kheejay88/Bank_Personal_Loan_Modelling"
            "/resolve/main/Bank_Personal_Loan_Modelling.csv")

TARGET = "Personal_Loan"
RANDOM_STATE = 42
