-- ===============================================================
-- PROJET 11 — v2 : architecture RAW -> DIM -> CLEAN -> VUES
-- Nécessite MySQL 8.0.16+
-- ===============================================================
DROP DATABASE IF EXISTS bank_loan;
CREATE DATABASE bank_loan CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE bank_loan;

-- ---------- Couche RAW (données brutes) ----------
CREATE TABLE staging_bank (
    ID INT PRIMARY KEY,
    Age INT, Experience INT, Income INT, ZIP_Code INT,
    Family INT, CCAvg FLOAT, Education INT, Mortgage INT,
    Personal_Loan INT, Securities_Account INT, CD_Account INT,
    Online INT, CreditCard INT
);

SET GLOBAL local_infile = 1;
LOAD DATA LOCAL INFILE 'data/raw/Bank_Personal_Loan_Modelling.csv'
INTO TABLE staging_bank
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ID, Age, Experience, Income, ZIP_Code, Family, CCAvg, Education, Mortgage,
 Personal_Loan, Securities_Account, CD_Account, Online, CreditCard);

-- ---------- Couche DIMENSION ----------
CREATE TABLE dim_education (
    education_id TINYINT PRIMARY KEY,
    education_label VARCHAR(40) NOT NULL
);
INSERT INTO dim_education VALUES
    (1,'Undergrad'),(2,'Graduate'),(3,'Advanced/Professional');

-- ---------- Couche CLEAN : typée, contrainte, corrigée ----------
CREATE TABLE clients (
    client_id          INT      NOT NULL PRIMARY KEY,
    age                TINYINT  NOT NULL,
    experience         TINYINT  NOT NULL,
    income_k           SMALLINT NOT NULL,
    zip_code           INT,
    family_size        TINYINT  NOT NULL,
    cc_avg_k           FLOAT,
    education_id       TINYINT  NOT NULL,
    mortgage_k         SMALLINT DEFAULT 0,
    personal_loan      TINYINT  NOT NULL,
    securities_account TINYINT  DEFAULT 0,
    cd_account         TINYINT  DEFAULT 0,
    online             TINYINT  DEFAULT 0,
    credit_card        TINYINT  DEFAULT 0,
    -- Colonnes générées : tranches calculées une seule fois
    age_group VARCHAR(8)  AS (CASE WHEN age < 30 THEN '<30'
                                   WHEN age < 50 THEN '30-50'
                                   WHEN age < 70 THEN '50-70'
                                   ELSE '70+' END) STORED,
    income_group VARCHAR(10) AS (CASE WHEN income_k < 50 THEN '<50k'
                                      WHEN income_k < 100 THEN '50-100k'
                                      WHEN income_k < 150 THEN '100-150k'
                                      ELSE '150k+' END) STORED,
    CONSTRAINT chk_loan CHECK (personal_loan IN (0,1)),
    CONSTRAINT fk_edu FOREIGN KEY (education_id) REFERENCES dim_education(education_id)
);

-- Insertion + correction Experience négative directement en SQL
INSERT INTO clients (client_id, age, experience, income_k, zip_code, family_size,
                     cc_avg_k, education_id, mortgage_k, personal_loan,
                     securities_account, cd_account, online, credit_card)
SELECT ID, Age, ABS(Experience), Income, ZIP_Code, Family, CCAvg, Education,
       Mortgage, Personal_Loan, Securities_Account, CD_Account, Online, CreditCard
FROM staging_bank;

CREATE INDEX idx_loan   ON clients (personal_loan);
CREATE INDEX idx_income ON clients (income_k);

-- Contrôles qualité
SELECT COUNT(*) AS nb_clients FROM clients;                -- 5000 attendu
SELECT COUNT(*) AS exp_negatives FROM clients WHERE experience < 0;  -- 0 attendu
SELECT ROUND(100*AVG(personal_loan),2) AS taux_acceptation_pct FROM clients;  -- ~9.6
