USE bank_loan;

-- ---------- Vues pour Power BI ----------
CREATE OR REPLACE VIEW v_kpi_global AS
SELECT COUNT(*) AS nb_clients,
       ROUND(100*AVG(personal_loan), 2) AS taux_acceptation_pct,
       ROUND(AVG(income_k), 1)          AS revenu_moyen_k,
       SUM(cd_account = 1)              AS nb_cd_account,
       SUM(securities_account = 1)      AS nb_securities
FROM clients;

CREATE OR REPLACE VIEW v_profil_acceptation AS
SELECT c.age_group, c.income_group, e.education_label,
       COUNT(*)                          AS nb_clients,
       SUM(c.personal_loan)              AS nb_acceptations,
       ROUND(100*AVG(c.personal_loan),2) AS taux_acceptation_pct
FROM clients c JOIN dim_education e USING (education_id)
GROUP BY c.age_group, c.income_group, e.education_label;

-- ---------- Analyse avancée : CTE + fenêtrage ----------
-- Top zones résidentielles à cibler (min 50 clients pour être significatif)
WITH zip_stats AS (
    SELECT zip_code, COUNT(*) AS nb_clients,
           SUM(personal_loan) AS nb_prets,
           ROUND(100*AVG(personal_loan),2) AS taux_pct
    FROM clients GROUP BY zip_code HAVING nb_clients >= 50
)
SELECT zip_code, nb_clients, nb_prets, taux_pct,
       RANK() OVER (ORDER BY taux_pct DESC) AS rang
FROM zip_stats ORDER BY rang LIMIT 10;

-- Pivot taux d'acceptation : revenu x education
SELECT income_group,
       ROUND(100*AVG(CASE WHEN education_id=1 THEN personal_loan END),2) AS undergrad_pct,
       ROUND(100*AVG(CASE WHEN education_id=2 THEN personal_loan END),2) AS graduate_pct,
       ROUND(100*AVG(CASE WHEN education_id=3 THEN personal_loan END),2) AS advanced_pct
FROM clients GROUP BY income_group;

-- Test des vues
SELECT * FROM v_kpi_global;
SELECT * FROM v_profil_acceptation ORDER BY taux_acceptation_pct DESC LIMIT 5;
