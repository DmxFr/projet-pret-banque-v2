"""App de scoring + analyse : streamlit run app/app.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd
import streamlit as st

from src import eda
from src.config import CLEAN_CSV, MODEL_PATH

st.set_page_config(page_title="Scoring Prêt Personnel", page_icon="🏦", layout="centered")


@st.cache_resource
def charger_modele():
    return joblib.load(MODEL_PATH)


@st.cache_data
def charger_donnees():
    return pd.read_csv(CLEAN_CSV)


onglet_score, onglet_analyse = st.tabs(["🎯 Scoring", "📊 Analyse du dataset"])

with onglet_score:
    st.title("🏦 Prédiction d'acceptation d'un prêt personnel")
    st.caption("Modèle Random Forest — AUC 0.998 — entraîné sur 5 000 clients")

with st.sidebar.header("Profil du client"):
    pass  # (les widgets ci-dessous restent dans la sidebar)

age = st.sidebar.slider("Âge", 23, 67, 40)
experience = st.sidebar.slider("Expérience (années)", 0, 45, 10)
income = st.sidebar.slider("Revenu annuel (k$)", 8, 224, 60)
family = st.sidebar.select_slider("Taille du foyer", options=[1, 2, 3, 4], value=2)
ccavg = st.sidebar.slider("Dépenses mensuelles carte (k$)", 0.0, 10.0, 1.5, 0.1)
education = st.sidebar.selectbox("Éducation", [1, 2, 3],
                                 format_func=lambda x: {1: "Undergrad", 2: "Graduate",
                                                        3: "Advanced/Professional"}[x])
mortgage = st.sidebar.slider("Hypothèque (k$)", 0, 635, 0)
cd_account = st.sidebar.checkbox("Compte à terme (CD Account)")
securities = st.sidebar.checkbox("Compte titres")
online = st.sidebar.checkbox("Banque en ligne", value=True)
credit_card = st.sidebar.checkbox("Carte de crédit de la banque")

with onglet_score:
    if st.button("Prédire", type="primary"):
        X = pd.DataFrame([{
            "Age": age, "Experience": experience, "Income": income, "Family": family,
            "CCAvg": ccavg, "Education": education, "Mortgage": mortgage,
            "Securities_Account": int(securities), "CD_Account": int(cd_account),
            "Online": int(online), "CreditCard": int(credit_card),
        }])
        proba = charger_modele().predict_proba(X)[0, 1]

        st.subheader(f"Probabilité d'acceptation : {proba*100:.1f} %")
        if proba >= 0.5:
            st.success("✅ Client à cibler en priorité")
        elif proba >= 0.2:
            st.warning("⚠️ Profil intermédiaire — ciblage secondaire")
        else:
            st.error("❌ Peu probable — ne pas solliciter")
        st.progress(min(proba, 1.0))
        with st.expander("Données envoyées au modèle"):
            st.dataframe(X.T.rename(columns={0: "valeur"}))

with onglet_analyse:
    st.header("📊 Ce que disent les données")
    df = charger_donnees()
    st.pyplot(eda.plot_income_vs_ccavg(df))
    st.markdown("**Séparation nette des classes** : c'est ce motif que le modèle apprend "
                "(AUC 0.998). Revenu et dépenses carte sont les 2 variables dominantes.")
    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(eda.plot_taux_par_revenu(df))
    with c2:
        st.pyplot(eda.plot_taux_par_education(df))
    st.pyplot(eda.plot_distribution_cible(df))
    st.caption("Classe minoritaire (~9,6 %) → stratification et class_weight lors de l'entraînement.")