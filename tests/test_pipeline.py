"""Tests du pipeline : nettoyage, segments, smoke test ML."""
import numpy as np
import pandas as pd
import pytest

from src.data_prep import add_segments, drop_duplicates, fix_experience
from src.train import build_models


@pytest.fixture
def df_sale():
    """Petit dataset de test avec anomalies connues."""
    return pd.DataFrame({
        "Age": [25, 45, 60, 35],
        "Experience": [-3, 10, -1, 20],          # 2 negatives
        "Income": [49, 80, 120, 45],
        "Personal_Loan": [0, 1, 1, 0],
    })


def test_fix_experience(df_sale):
    df = fix_experience(df_sale.copy())
    assert (df["Experience"] >= 0).all()
    assert df.loc[0, "Experience"] == 3          # -3 -> 3


def test_fix_experience_sans_negatives(df_sale):
    df = df_sale.copy()
    df["Experience"] = [5, 10, 15, 20]
    assert (fix_experience(df)["Experience"] == [5, 10, 15, 20]).all()


def test_drop_duplicates(df_sale):
    df = pd.concat([df_sale, df_sale.head(1)], ignore_index=True)
    assert len(drop_duplicates(df)) == 4


def test_segments(df_sale):
    df = add_segments(df_sale)
    assert list(df["Age_Group"][:3]) == ["<30", "30-50", "50-70"]
    assert list(df["Income_Group"][:3]) == ["<50k", "50-100k", "100-150k"]


def test_segments_couvrant_tous_les_cas():
    """Bornes basses incluses : 30 -> '30-50', 70 -> '70+', 49 -> '<50k', 50 -> '50-100k'."""
    df = pd.DataFrame({"Age": [30, 70], "Income": [150, 49]})
    df = add_segments(df)
    df2 = pd.DataFrame({"Age": [45], "Income": [50]})
    df2 = add_segments(df2)
    assert df.loc[0, "Age_Group"] == "30-50" and df.loc[0, "Income_Group"] == "150k+"
    assert df.loc[1, "Age_Group"] == "70+"  and df.loc[1, "Income_Group"] == "<50k"
    assert df2.loc[0, "Income_Group"] == "50-100k"

def test_modeles_instanciables():
    """Smoke test : les 2 modeles se construisent et predisent."""
    from sklearn.model_selection import train_test_split
    rng = np.random.RandomState(42)
    X = pd.DataFrame(rng.rand(100, 3), columns=["a", "b", "c"])
    y = (X["a"] > 0.5).astype(int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, stratify=y, random_state=42)
    for nom, m in build_models().items():
        m.fit(Xtr, ytr)
        proba = m.predict_proba(Xte)[:, 1]
        assert len(proba) == len(yte) and proba.min() >= 0 and proba.max() <= 1
