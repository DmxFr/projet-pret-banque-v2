.PHONY: setup data train test analyses all

setup:            ## Installe l'environnement
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install pytest

data:             ## Prépare les données propres
	venv/bin/python -m src.data_prep

train:            ## Entraîne et évalue les modèles
	venv/bin/python -m src.train

test:             ## Lance les tests
	venv/bin/pytest tests/ -v

analyses:         ## Recharge le schéma SQL et les analyses
	mysql --local-infile -u root -p < sql/01_schema.sql
	mysql -u root -p < sql/02_analyses.sql

eda:              ## Génère les graphiques d'analyse exploratoire
	venv/bin/python -m src.eda

all: data train test
