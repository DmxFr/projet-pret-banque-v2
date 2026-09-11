"""Entraînement et évaluation : LogReg (baseline) vs Random Forest."""
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import (CLEAN_CSV, MODEL_PATH, PREDICTIONS_CSV, RAPPORTS_DIR,
                        RANDOM_STATE, TARGET)

COLS_A_EXCLURE = ["ID", "ZIP_Code", "Age_Group", "Income_Group"]  # ZIP = 500 modalités


def build_models() -> dict:
    return {
        "Regression logistique": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced",
                                       random_state=RANDOM_STATE)),
        ]),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=2, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1),
    }


def run(csv_path=None) -> None:
    df = pd.read_csv(csv_path or CLEAN_CSV)
    exclude = [c for c in COLS_A_EXCLURE + [TARGET] if c in df.columns]
    X, y = df.drop(columns=exclude), df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE)

    resultats = {}
    for nom, modele in build_models().items():
        modele.fit(X_train, y_train)
        proba = modele.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
        resultats[nom] = {"modele": modele, "proba": proba, "auc": auc}
        print(f"\n=== {nom} — ROC-AUC : {auc:.3f} ===")
        print(classification_report(y_test, (proba >= 0.5).astype(int), digits=3))

    meilleur_nom = max(resultats, key=lambda k: resultats[k]["auc"])
    meilleur = resultats[meilleur_nom]
    print(f">>> Meilleur modele : {meilleur_nom} (AUC = {meilleur['auc']:.3f})")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ConfusionMatrixDisplay.from_predictions(
        y_test, (meilleur["proba"] >= 0.5).astype(int), cmap="Blues")
    plt.title(f"Matrice de confusion — {meilleur_nom}")
    plt.tight_layout()
    plt.savefig(RAPPORTS_DIR / "matrice_confusion.png", dpi=150)
    plt.close()

    r = permutation_importance(meilleur["modele"], X_test, y_test,
                               n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1)
    ordre = r.importances_mean.argsort()
    plt.figure(figsize=(8, 5))
    plt.barh(X.columns[ordre], r.importances_mean[ordre])
    plt.title("Importance des variables (permutation)")
    plt.tight_layout()
    plt.savefig(RAPPORTS_DIR / "importance_variables.png", dpi=150)
    plt.close()

    out = X_test.copy()
    out[TARGET + "_reel"] = y_test
    out["proba_acceptation"] = np.round(meilleur["proba"], 4)
    out["prediction"] = (meilleur["proba"] >= 0.5).astype(int)
    out.to_csv(PREDICTIONS_CSV, index=False)

    joblib.dump(meilleur["modele"], MODEL_PATH)
    print(f"[OK] {MODEL_PATH.name} + {PREDICTIONS_CSV.name} + 2 PNG dans rapports/")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
