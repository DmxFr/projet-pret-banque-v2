-- ===============================================================
-- PROJET 11 : Analyse des profils clients susceptibles d'accepter un prêt personnel
-- Auteur : CY Tech - Damien
-- Base : bank_loan
-- ===============================================================

-- Étape 1 : Création de la base
DROP DATABASE IF EXISTS bank_loan;
CREATE DATABASE bank_loan CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE bank_loan;

-- Étape 2 : Création de la table de staging
DROP TABLE IF EXISTS staging_bank;
CREATE TABLE staging_bank (
    ID INT PRIMARY KEY,
    Age INT,
    Experience INT,
    Income INT,
    ZIP_Code INT,
    Family INT,
    CCAvg FLOAT,
    Education INT,
    Mortgage INT,
    Personal_Loan INT,
    Securities_Account INT,
    CD_Account INT,
    Online INT,
    CreditCard INT
);

-- Étape 3 : Import du fichier CSV
-- ⚠️ IMPORTANT : nécessite que LOCAL INFILE soit activé
-- Active-le si nécessaire : SET GLOBAL local_infile = 1;

LOAD DATA LOCAL INFILE '/imports/Bank_Personal_Loan_Modelling.csv'
INTO TABLE staging_bank
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ID, Age, Experience, Income, ZIP_Code, Family, CCAvg, Education, Mortgage,
 Personal_Loan, Securities_Account, CD_Account, Online, CreditCard);

-- Étape 4 : Vérification du chargement
SELECT COUNT(*) AS total_lignes FROM staging_bank;

-- Étape 5 : Vérification du contenu (5 premières lignes)
SELECT * FROM staging_bank LIMIT 5;

-- Étape 6 : Nettoyage des valeurs incohérentes (optionnel)
-- Exemple : suppression des doublons
DELETE t1 FROM staging_bank t1
INNER JOIN staging_bank t2 
WHERE t1.ID > t2.ID AND t1.ID = t2.ID;

-- Étape 7 : Quelques analyses rapides

-- Taux d’acceptation global du prêt
SELECT 
    ROUND(SUM(Personal_Loan)/COUNT(*)*100,2) AS taux_acceptation_pourcent
FROM staging_bank;

-- Taux d’acceptation par tranche d’âge
SELECT 
    CASE
        WHEN Age < 30 THEN '<30'
        WHEN Age BETWEEN 30 AND 50 THEN '30-50'
        ELSE '>50'
    END AS Tranche_Age,
    ROUND(SUM(Personal_Loan)/COUNT(*)*100,2) AS Taux_Acceptation
FROM staging_bank
GROUP BY Tranche_Age
ORDER BY Tranche_Age;

-- Taux d’acceptation par niveau d’éducation
SELECT 
    CASE 
        WHEN Education = 1 THEN 'Undergrad'
        WHEN Education = 2 THEN 'Graduate'
        WHEN Education = 3 THEN 'Advanced/Professional'
        ELSE 'Inconnu'
    END AS Niveau_Education,
    ROUND(SUM(Personal_Loan)/COUNT(*)*100,2) AS Taux_Acceptation
FROM staging_bank
GROUP BY Education
ORDER BY Education;

-- Taux d’acceptation selon la tranche de revenu
SELECT 
    CASE 
        WHEN Income < 50 THEN '<50k'
        WHEN Income BETWEEN 50 AND 100 THEN '50–100k'
        ELSE '>100k'
    END AS Tranche_Revenu,
    ROUND(SUM(Personal_Loan)/COUNT(*)*100,2) AS Taux_Acceptation
FROM staging_bank
GROUP BY Tranche_Revenu
ORDER BY Tranche_Revenu;

-- Étape 8 : Export possible (pour Power BI)
-- On peut exporter cette table avec :
-- SELECT * INTO OUTFILE '/var/lib/mysql-files/bank_clean.csv'
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n'
-- FROM staging_bank;

