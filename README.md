[![CI](https://github.com/DmxFr/projet-pret-banque-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/DmxFr/projet-pret-banque-v2/actions/workflows/ci.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://projet-pret-banque-v2-pksaavqoyurtxyvuhiovas.streamlit.app/)

# 🏦 Scoring d'acceptation d'un prêt personnel

Une banque veut identifier, parmi sa base de clients, ceux les plus susceptibles
d'accepter un prêt personnel — pour cibler une campagne plutôt que la diffuser à
l'aveugle. Sur les 5 000 clients du dataset, seuls **9,6 %** ont historiquement
accepté une offre : un ciblage aléatoire gaspille l'essentiel de l'effort commercial.
Ce projet livre un modèle de scoring et une app Streamlit pour transformer ce
ciblage en décision, client par client.

## 📊 Résultats

| Modèle | ROC-AUC | Recall (classe 1) | Precision (classe 1) |
|---|---|---|---|
| Régression logistique (baseline) | 0.964 | 0.917 | 0.474 |
| **Random Forest (retenu, déployé)** | **0.998** | **0.975** | **0.873** |

À titre de repère : un modèle qui prédirait systématiquement "refus" atteindrait
déjà ~90 % d'accuracy sans détecter un seul client intéressé — c'est le piège de
l'accuracy sur des classes déséquilibrées. Le recall sur la classe 1 (clients qui
acceptent réellement) est la métrique qui compte ici, pas l'accuracy globale.

**Insights clés :**
- Revenu > 100 k$ **et** niveau d'éducation Graduate/Advanced → 78-100 % d'acceptation.
- Les meilleurs codes postaux ciblés correspondent à des campus universitaires
  (Berkeley, Stanford...).
- Revenu et dépenses carte à eux seuls séparent déjà nettement les deux classes
  (voir `rapports/04_income_vs_ccavg.png`).

## 🏗️ Pipeline

```
data/raw/Bank_Personal_Loan_Modelling.csv
            │
            ▼
   src/data_prep.py     nettoyage (doublons, Experience négative), tranches Age/Income
            │
            ▼
data/processed/Bank_Personal_Loan_Clean.csv
            │
            ▼
     src/train.py       LogReg (baseline) vs Random Forest — class_weight, stratify
            │
            ├──▶ models/modele_pret.joblib
            ├──▶ data/processed/predictions_clients.csv
            └──▶ rapports/*.png (matrice de confusion, importance des variables)
            │
            ▼
      app/app.py         Streamlit : Scoring · Dashboard interactif · Analyse du dataset

data/raw/*.csv ──▶ sql/01_schema.sql (RAW → DIM → CLEAN, MySQL) ──▶ sql/02_analyses.sql (vues, CTE)
                                                                      └─▶ BI (Power BI / Metabase...)
```

Détail des choix (déséquilibre de classes, colonnes générées SQL, exclusions de
variables...) dans [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 🛠️ Stack

Python 3.12 · pandas / numpy · scikit-learn · matplotlib · Streamlit + Altair ·
MySQL 8 · pytest · Docker · GitHub Actions

## 📁 Structure

```
├── src/            pipeline : config, préparation, EDA, entraînement
├── app/            application Streamlit (scoring + dashboard + EDA)
├── tests/          tests pytest du pipeline
├── sql/            schéma MySQL (RAW→DIM→CLEAN) + analyses BI (vues, CTE)
├── data/raw/       dataset source (versionné, 5 000 lignes)
├── data/processed/ données nettoyées + prédictions (générées par le pipeline)
├── models/         modèle entraîné (.joblib, versionné)
├── rapports/       graphiques exportés (EDA + évaluation du modèle)
└── .github/        CI (tests + build Docker)
```

## 🚀 Reproduction en local

```bash
git clone https://github.com/DmxFr/projet-pret-banque-v2.git
cd projet-pret-banque-v2

make setup      # crée le venv, installe requirements.txt + pytest
make data       # régénère data/processed/ depuis data/raw/
make train      # entraîne les 2 modèles, exporte modèle + rapports
make test       # pytest tests/ -v (6 tests)
make eda        # régénère les graphiques d'analyse exploratoire

# app en local
venv/bin/streamlit run app/app.py

# couche SQL (nécessite MySQL 8.0.16+ avec local_infile activé)
make analyses   # charge sql/01_schema.sql puis sql/02_analyses.sql

# Docker (build géré par la CI — voir .github/workflows/ci.yml)
docker build -t pret-banque .
docker run -p 8501:8501 pret-banque
```

**Démo en ligne :** [projet-pret-banque-v2.streamlit.app](https://projet-pret-banque-v2-pksaavqoyurtxyvuhiovas.streamlit.app/)

## 🎯 Compétences mobilisées

Data cleaning & feature engineering (pandas) · gestion de classes déséquilibrées
(`class_weight`, `stratify`) · comparaison de modèles (scikit-learn) ·
modélisation SQL (schéma en couches, contraintes, colonnes générées, vues, CTE,
fonctions fenêtrées) · développement d'application interactive (Streamlit,
Altair) · tests unitaires (pytest) · CI/CD (GitHub Actions) · conteneurisation
(Docker) · documentation d'architecture (ADR).
