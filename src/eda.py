"""Analyse exploratoire : génère les graphiques du rapport dans rapports/.
Usage : python -m src.eda"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config import CLEAN_CSV, RAPPORTS_DIR, TARGET

BLEU = "#1f77b4"
ORANGE = "#ff7f0e"


def _save(fig, nom: str):
    try:
        RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)
        fig.tight_layout()
        fig.savefig(RAPPORTS_DIR / nom, dpi=150)
        print(f"[OK] rapports/{nom}")
    except OSError:
        pass  # filesystem lecture seule (ex: cloud)
    return fig

def plot_distribution_cible(df: pd.DataFrame) -> None:
    counts = df[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(["Refus (0)", "Acceptation (1)"], counts.values, color=[BLEU, ORANGE])
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 30, f"{v}\n({100*v/len(df):.1f}%)",
                ha="center", fontsize=9)
    ax.set_title("Répartition de la cible — déséquilibre des classes")
    ax.set_ylabel("Nombre de clients")
    return _save(fig, "01_distribution_cible.png")


def plot_taux_par_revenu(df: pd.DataFrame) -> None:
    taux = df.groupby("Income_Group", observed=True)[TARGET].mean() * 100
    fig, ax = plt.subplots(figsize=(6, 4))
    taux.plot(kind="bar", ax=ax, color=BLEU)
    ax.axhline(df[TARGET].mean() * 100, color="red", ls="--", lw=1,
               label=f"Moyenne globale ({df[TARGET].mean()*100:.1f}%)")
    ax.set_title("Taux d'acceptation par tranche de revenu")
    ax.set_ylabel("% acceptation")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=0)
    return _save(fig, "02_taux_par_revenu.png")


def plot_taux_par_education(df: pd.DataFrame) -> None:
    labels = {1: "Undergrad", 2: "Graduate", 3: "Advanced/Pro"}
    taux = df.groupby("Education")[TARGET].mean() * 100
    taux.index = [labels.get(i, i) for i in taux.index]
    fig, ax = plt.subplots(figsize=(6, 4))
    taux.plot(kind="bar", ax=ax, color=ORANGE)
    ax.axhline(df[TARGET].mean() * 100, color="red", ls="--", lw=1,
               label=f"Moyenne globale ({df[TARGET].mean()*100:.1f}%)")
    ax.set_title("Taux d'acceptation par niveau d'éducation")
    ax.set_ylabel("% acceptation")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=0)
    return _save(fig, "03_taux_par_education.png")


def plot_income_vs_ccavg(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    for valeur, couleur, label in [(0, BLEU, "Refus"), (1, ORANGE, "Acceptation")]:
        sub = df[df[TARGET] == valeur]
        ax.scatter(sub["Income"], sub["CCAvg"], alpha=0.4, s=12,
                   c=couleur, label=label)
    ax.set_title("Revenu vs dépenses carte de crédit — séparation nette des classes")
    ax.set_xlabel("Revenu annuel (k$)")
    ax.set_ylabel("CCAvg mensuel (k$)")
    ax.legend()
    return _save(fig, "04_income_vs_ccavg.png")


def run() -> None:
    df = pd.read_csv(CLEAN_CSV)
    plot_distribution_cible(df)
    plot_taux_par_revenu(df)
    plot_taux_par_education(df)
    plot_income_vs_ccavg(df)
    print("[OK] EDA terminé")


if __name__ == "__main__":
    run()
