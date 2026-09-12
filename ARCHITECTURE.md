# ARCHITECTURE.md — Décisions techniques (ADR)

Ce fichier documente le *pourquoi* des choix non triviaux du projet. Rédigé à
partir des choix effectivement présents dans le code (commentaires, structure,
tests) — à corriger si une intention diffère de ce qui est décrit ici.

## D1 — Trois couches SQL : RAW → DIM → CLEAN plutôt qu'une table plate

`sql/01_schema.sql` sépare le chargement brut (`staging_bank`, sans contrainte,
tolérant à l'import) de la couche exploitable (`clients`, typée, contrainte par
clé étrangère vers `dim_education`, avec `CHECK (personal_loan IN (0,1))`).
Séparer permet de rejouer l'import brut sans jamais casser la couche propre, et
de faire échouer tôt une donnée invalide (contrainte SQL) plutôt que de la
découvrir en aval dans une analyse.

## D2 — Colonnes générées (STORED) pour les tranches d'âge et de revenu

`age_group` et `income_group` sont calculées une seule fois à l'insertion
(`GENERATED ALWAYS AS (...) STORED`) plutôt que recalculées dans chaque requête
BI. Les bornes sont volontairement alignées sur `src/data_prep.py::add_segments`
(voir D6) pour que la couche SQL et la couche Python racontent la même histoire.

## D3 — `class_weight="balanced"` sur les deux modèles

La classe positive (prêt accepté) ne représente que ~9,6 % du dataset. Sans
repondération, un modèle qui prédirait systématiquement "refus" atteindrait déjà
~90 % d'accuracy sans détecter un seul client intéressé. `class_weight="balanced"`
pénalise davantage les erreurs sur la classe minoritaire pour éviter ce piège
(voir aussi `rapports/01_distribution_cible.png`).

## D4 — `stratify=y` dans le split train/test

Avec un tel déséquilibre, un split purement aléatoire pourrait, par hasard,
sous-représenter les rares acceptations côté test et fausser l'évaluation.
`stratify=y` garantit que train et test conservent chacun ~9,6 % de classe
positive.

## D5 — Comparer une baseline interprétable à un modèle plus complexe

`src/train.py` entraîne systématiquement une régression logistique *avant* la
Random Forest. La régression logistique sert de repère interprétable (et de
garde-fou : si la RF ne fait pas mieux qu'elle, c'est suspect) ; la RF est
retenue et déployée pour sa performance (AUC 0.998 vs 0.964, recall classe 1
0.975 vs 0.917 — voir README.md).

## D6 — Exclusion de `ID`, `ZIP_Code`, `Age_Group`, `Income_Group` des features

`ID` n'a aucune valeur prédictive. `ZIP_Code` compte ~500 modalités : un
one-hot naïf sur une telle cardinalité expose à du surapprentissage. `Age_Group`
et `Income_Group` sont dérivées d'`Age` et `Income`, déjà présentes dans les
features — les garder serait redondant sans apporter d'information nouvelle au
modèle.

## D7 — Bornes des tranches : `right=False`, alignées entre Python et SQL

Bug détecté par les tests (`test_segments_couvrant_tous_les_cas`) : avec les
bornes par défaut de `pandas.cut` (`right=True`), une valeur pile sur une borne
(30 ans, 50 k$...) tombe dans la tranche du dessous au lieu de celle du dessus,
au mépris de la logique métier voulue ("30 ans = déjà 30-50", pas "<30").
`add_segments` force donc `right=False`, et `sql/01_schema.sql` reproduit
exactement la même logique de bornes (`age < 30`, `age < 50`, ...) pour que les
deux couches soient cohérentes entre elles.

## Pourquoi `app/app.py` réimporte `src/eda.py` plutôt que dupliquer les graphiques

Les fonctions `plot_*` de `src/eda.py` servent deux consommateurs : le rapport
statique (`make eda`, sorties dans `rapports/`) et l'onglet "Analyse du dataset"
de l'app Streamlit, qui les appelle en direct pour un rendu interactif. `_save()`
avale silencieusement les erreurs d'écriture (`except OSError: pass`) pour ne
pas faire planter l'app sur un filesystem en lecture seule (Streamlit Cloud) tout
en conservant l'écriture disque pour l'usage local/CI.
