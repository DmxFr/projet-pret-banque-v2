"""App scoring + dashboard : streamlit run app/app.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import altair as alt          # déjà installé (dépendance de streamlit)
import joblib
import pandas as pd
import streamlit as st

from src import eda
from src.config import CLEAN_CSV, MODEL_PATH, TARGET

ORDRE_REVENU = ["<50k", "50-100k", "100-150k", "150k+"]
EDUS = ["Undergrad", "Graduate", "Advanced/Pro"]
EDU_MAP = {1: "Undergrad", 2: "Graduate", 3: "Advanced/Pro"}

st.set_page_config(page_title="Scoring Prêt Personnel", page_icon="🏦", layout="centered")


@st.cache_resource
def charger_modele():
    """Charge le .joblib une seule fois par session : Streamlit ré-exécute tout
    le script à chaque interaction utilisateur, recharger le modèle à chaque fois
    serait coûteux et inutile."""
    return joblib.load(MODEL_PATH)


@st.cache_data
def charger_donnees():
    """Charge le CSV nettoyé une seule fois par session, pour la même raison."""
    return pd.read_csv(CLEAN_CSV)


onglet_score, onglet_dash, onglet_eda = st.tabs(
    ["🎯 Scoring", "📊 Dashboard", "🔬 Analyse du dataset"])

# ---------------- Sidebar (profil à scorer) ----------------
st.sidebar.header("Profil du client")
age = st.sidebar.slider("Âge", 23, 67, 40)
experience = st.sidebar.slider("Expérience (années)", 0, 45, 10)
income = st.sidebar.slider("Revenu annuel (k$)", 8, 224, 60)
family = st.sidebar.select_slider("Taille du foyer", options=[1, 2, 3, 4], value=2)
ccavg = st.sidebar.slider("Dépenses mensuelles carte (k$)", 0.0, 10.0, 1.5, 0.1)
education = st.sidebar.selectbox("Éducation", [1, 2, 3], format_func=lambda x: EDU_MAP[x])
mortgage = st.sidebar.slider("Hypothèque (k$)", 0, 635, 0)
cd_account = st.sidebar.checkbox("Compte à terme (CD Account)")
securities = st.sidebar.checkbox("Compte titres")
online = st.sidebar.checkbox("Banque en ligne", value=True)
credit_card = st.sidebar.checkbox("Carte de crédit de la banque")

# ---------------- Onglet Scoring ----------------
with onglet_score:
    st.title("🏦 Prédiction d'acceptation d'un prêt personnel")
    st.caption("Modèle Random Forest — AUC 0.998 — entraîné sur 5 000 clients")

    if st.button("Prédire", type="primary"):
        X = pd.DataFrame([{
            "Age": age, "Experience": experience, "Income": income, "Family": family,
            "CCAvg": ccavg, "Education": education, "Mortgage": mortgage,
            "Securities_Account": int(securities), "CD_Account": int(cd_account),
            "Online": int(online), "CreditCard": int(credit_card),
        }])
        proba = charger_modele().predict_proba(X)[0, 1]

        st.subheader(f"Probabilité d'acceptation : {proba*100:.1f} %")
        # Seuils de lecture métier : 0.5 = seuil de décision standard (aligné sur
        # l'évaluation du modèle dans train.py) ; 0.2 = zone grise "à surveiller"
        # plutôt qu'un simple oui/non, pour ne pas écarter trop vite un profil mitigé.
        if proba >= 0.5:
            st.success("✅ Client à cibler en priorité")
        elif proba >= 0.2:
            st.warning("⚠️ Profil intermédiaire — ciblage secondaire")
        else:
            st.error("❌ Peu probable — ne pas solliciter")
        st.progress(min(proba, 1.0))
        with st.expander("Données envoyées au modèle"):
            st.dataframe(X.T.rename(columns={0: "valeur"}))

# ---------------- Onglet Dashboard ----------------
with onglet_dash:
    st.header("📊 Dashboard interactif")
    df = charger_donnees().copy()
    df["Education_Label"] = df["Education"].map(EDU_MAP)

    # --- Filtres (slicers) ---
    f1, f2, f3 = st.columns(3)
    edu_ok = f1.multiselect("Éducation", EDUS, default=EDUS)
    inc_ok = f2.multiselect("Tranche de revenu", ORDRE_REVENU, default=ORDRE_REVENU)
    a_min, a_max = f3.slider("Âge", int(df["Age"].min()), int(df["Age"].max()),
                             (int(df["Age"].min()), int(df["Age"].max())))

    dff = df[df["Education_Label"].isin(edu_ok)
             & df["Income_Group"].isin(inc_ok)
             & df["Age"].between(a_min, a_max)]

    if dff.empty:
        st.warning("Aucun client ne correspond à ces filtres.")
    else:
        # --- KPI qui réagissent aux filtres ---
        taux_global = 100 * df[TARGET].mean()
        taux_filtre = 100 * dff[TARGET].mean()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Clients (filtrés)", f"{len(dff):,}")
        k2.metric("Taux d'acceptation", f"{taux_filtre:.1f} %",
                  delta=f"{taux_filtre - taux_global:+.1f} pts vs global")
        k3.metric("Revenu moyen", f"{dff['Income'].mean():.0f} k$")
        k4.metric("Dép. carte moy.", f"{dff['CCAvg'].mean():.1f} k$")

        # --- Graphiques réactifs ---
        c1, c2 = st.columns(2)
        with c1:
            t = (dff.groupby("Income_Group", observed=True)[TARGET].mean() * 100).reset_index()
            t.columns = ["Tranche", "taux"]
            ch = alt.Chart(t).mark_bar(color="#1f77b4").encode(
                x=alt.X("Tranche:N", sort=ORDRE_REVENU, title="Tranche de revenu"),
                y=alt.Y("taux:Q", title="% acceptation"),
                tooltip=["Tranche", "taux"]).properties(title="Acceptation par revenu")
            st.altair_chart(ch, use_container_width=True)
        with c2:
            t = (dff.groupby("Education_Label", observed=True)[TARGET].mean() * 100).reset_index()
            t.columns = ["Éducation", "taux"]
            ch = alt.Chart(t).mark_bar(color="#ff7f0e").encode(
                x=alt.X("Éducation:N", sort=EDUS, title="Niveau d'éducation"),
                y=alt.Y("taux:Q", title="% acceptation"),
                tooltip=["Éducation", "taux"]).properties(title="Acceptation par éducation")
            st.altair_chart(ch, use_container_width=True)

        sc = alt.Chart(dff).mark_circle(size=40, opacity=0.45).encode(
            x=alt.X("Income:Q", title="Revenu annuel (k$)"),
            y=alt.Y("CCAvg:Q", title="Dépenses carte (k$/mois)"),
            color=alt.Color("Personal_Loan:N",
                            scale=alt.Scale(domain=[0, 1], range=["#1f77b4", "#ff7f0e"]),
                            legend=alt.Legend(title="Prêt accepté")),
            tooltip=["Age", "Income", "CCAvg", "Education_Label"]
        ).properties(title="Revenu vs dépenses carte — classes séparées")
        st.altair_chart(sc, use_container_width=True)

        with st.expander(f"Voir les {len(dff)} clients filtrés"):
            st.dataframe(dff.drop(columns=["Education_Label"]), use_container_width=True)

# ---------------- Onglet Analyse statique ----------------
with onglet_eda:
    st.header("🔬 Ce que disent les données")
    dfe = charger_donnees()
    st.pyplot(eda.plot_income_vs_ccavg(dfe))
    st.markdown("**Séparation nette des classes** : c'est ce motif que le modèle apprend (AUC 0.998).")
    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(eda.plot_taux_par_revenu(dfe))
    with c2:
        st.pyplot(eda.plot_taux_par_education(dfe))
    st.pyplot(eda.plot_distribution_cible(dfe))
    st.caption("Classe minoritaire (~9,6 %) → stratification et class_weight lors de l'entraînement.")