-- ===============================================================================
-- TAMIL MEDICINAL HERBS DATABASE - SNOWFLAKE SCHEMA
-- Integrates with FOOD_RECOMMENDATION_DB.AYURVEDA_TN
-- ===============================================================================

USE DATABASE FOOD_RECOMMENDATION_DB;
USE SCHEMA AYURVEDA_TN;

-- ===============================================================================
-- TABLE 1: MEDICINAL_HERBS (Master)
-- ===============================================================================

CREATE OR REPLACE TABLE MEDICINAL_HERBS (
    HERB_ID INT PRIMARY KEY AUTOINCREMENT,
    NAME_TAMIL VARCHAR(200),
    NAME_ENGLISH VARCHAR(200),
    NAME_BOTANICAL VARCHAR(200),
    ALTERNATIVE_NAMES VARCHAR(500),
    FAMILY VARCHAR(100),
    PLANT_PART VARCHAR(100),
    PLANT_CATEGORY VARCHAR(50),
    MEDICINE_SYSTEM VARCHAR(100),
    RASA VARCHAR(100),
    VEERYA VARCHAR(50),
    VATA_EFFECT VARCHAR(20),
    PITTA_EFFECT VARCHAR(20),
    KAPHA_EFFECT VARCHAR(20),
    PRIMARY_USES VARCHAR(500),
    DISEASES_TREATED VARCHAR(500),
    PREPARATION_METHODS VARCHAR(500),
    CONTRAINDICATIONS VARCHAR(200),
    REGION VARCHAR(200),
    SEASONAL_AVAILABILITY VARCHAR(100),
    MARKET_AVAILABILITY VARCHAR(50),
    SAFE_FOR_KIDS BOOLEAN DEFAULT TRUE,
    MIN_AGE_YEARS INT DEFAULT 2,
    DATA_CONFIDENCE_SCORE INT,
    SCIENTIFIC_VALIDATION BOOLEAN DEFAULT FALSE,
    SOURCE_WEBSITES VARCHAR(500),
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ===============================================================================
-- TABLE 2: HERB_DISEASE_MAPPING
-- ===============================================================================

CREATE OR REPLACE TABLE HERB_DISEASE_MAPPING (
    MAPPING_ID INT PRIMARY KEY AUTOINCREMENT,
    HERB_ID INT,
    DISEASE_NAME VARCHAR(200),
    DISEASE_CATEGORY VARCHAR(100),
    EFFECTIVENESS VARCHAR(50),
    PREPARATION_FOR_DISEASE VARCHAR(200),
    EVIDENCE_LEVEL VARCHAR(50),
    SOURCE VARCHAR(200)
);

-- ===============================================================================
-- TABLE 3: HERB_FOOD_INTEGRATION
-- ===============================================================================

CREATE OR REPLACE TABLE HERB_FOOD_INTEGRATION (
    INTEGRATION_ID INT PRIMARY KEY AUTOINCREMENT,
    HERB_ID INT,
    RECIPE_ID INT,
    USAGE_TYPE VARCHAR(50),
    QUANTITY_PER_SERVING VARCHAR(50),
    PREPARATION_NOTE VARCHAR(200),
    SAFE_FOR_KIDS BOOLEAN DEFAULT TRUE,
    MIN_AGE_YEARS INT DEFAULT 2,
    DOSHA_BENEFIT VARCHAR(200)
);

-- ===============================================================================
-- INSERT 50 CORE HERBS
-- ===============================================================================

INSERT INTO MEDICINAL_HERBS (NAME_TAMIL, NAME_ENGLISH, NAME_BOTANICAL, PLANT_PART, VATA_EFFECT, PITTA_EFFECT, KAPHA_EFFECT, PRIMARY_USES, DISEASES_TREATED, PREPARATION_METHODS, SEASONAL_AVAILABILITY, SAFE_FOR_KIDS, MIN_AGE_YEARS, DATA_CONFIDENCE_SCORE, SCIENTIFIC_VALIDATION)
SELECT * FROM VALUES
('Tulasi', 'Holy Basil', 'Ocimum tenuiflorum', 'Leaves', 'Decrease', 'Increase', 'Decrease', 'Immune boost, anti-bacterial, respiratory', 'Cold, cough, fever, respiratory infections', 'Tea, juice, fresh leaves', 'Year-round', TRUE, 2, 10, TRUE),
('Manjal', 'Turmeric', 'Curcuma longa', 'Rhizome', 'Decrease', 'Neutral', 'Decrease', 'Anti-inflammatory, antioxidant, wound healing', 'Wounds, skin disease, arthritis, diabetes', 'Powder, paste, milk', 'Year-round', TRUE, 1, 10, TRUE),
('Inji', 'Ginger', 'Zingiber officinale', 'Rhizome', 'Decrease', 'Increase', 'Decrease', 'Digestive, anti-nausea, warming', 'Nausea, cold, digestion problems, pain', 'Tea, juice, powder, fresh', 'Year-round', TRUE, 2, 10, TRUE),
('Karpooravalli', 'Mexican Mint', 'Coleus amboinicus', 'Leaves', 'Decrease', 'Neutral', 'Decrease', 'Cough remedy, digestive support', 'Cough, cold, sore throat, indigestion', 'Juice, steam, fresh', 'Summer', TRUE, 1, 9, TRUE),
('Nilavembu', 'Andrographis', 'Andrographis paniculata', 'Whole plant', 'Neutral', 'Decrease', 'Decrease', 'Fever reducer, anti-viral', 'Dengue, malaria, viral fever, liver disease', 'Kashayam, powder', 'Monsoon', TRUE, 5, 9, TRUE),
('Vallarai', 'Brahmi/Gotu Kola', 'Centella asiatica', 'Leaves', 'Decrease', 'Decrease', 'Neutral', 'Brain tonic, memory enhancer', 'Memory loss, anxiety, concentration, skin', 'Juice, chutney, powder', 'Monsoon', TRUE, 3, 10, TRUE),
('Keezhanelli', 'Phyllanthus', 'Phyllanthus niruri', 'Whole plant', 'Neutral', 'Decrease', 'Decrease', 'Liver protector, anti-hepatitis', 'Jaundice, liver disease, kidney stones', 'Juice, powder, decoction', 'Monsoon', TRUE, 5, 9, TRUE),
('Vembu', 'Neem', 'Azadirachta indica', 'Leaves, bark', 'Increase', 'Decrease', 'Decrease', 'Blood purifier, anti-bacterial, anti-fungal', 'Skin disease, diabetes, malaria, dental', 'Paste, oil, powder, decoction', 'Year-round', TRUE, 5, 10, TRUE),
('Adathoda', 'Malabar Nut', 'Justicia adhatoda', 'Leaves', 'Neutral', 'Decrease', 'Decrease', 'Expectorant, bronchodilator', 'Asthma, bronchitis, cough, TB', 'Juice, syrup, decoction', 'Winter', TRUE, 5, 9, TRUE),
('Amukkara', 'Ashwagandha', 'Withania somnifera', 'Root', 'Decrease', 'Neutral', 'Increase', 'Adaptogen, strength builder, stress relief', 'Stress, fatigue, immunity, insomnia', 'Powder, milk, capsule', 'Winter', TRUE, 8, 10, TRUE),
('Thippili', 'Long Pepper', 'Piper longum', 'Fruit', 'Decrease', 'Increase', 'Decrease', 'Digestive stimulant, respiratory', 'Asthma, cold, indigestion, cough', 'Powder, milk, honey', 'Winter', TRUE, 3, 9, TRUE),
('Nellikai', 'Indian Gooseberry', 'Emblica officinalis', 'Fruit', 'Decrease', 'Decrease', 'Decrease', 'Vitamin C rich, rejuvenative, tri-dosha', 'Aging, immunity, digestion, hair', 'Juice, powder, pickle, jam', 'Winter', TRUE, 2, 10, TRUE),
('Kadukkai', 'Chebulic Myrobalan', 'Terminalia chebula', 'Fruit', 'Decrease', 'Decrease', 'Decrease', 'Digestive, laxative, detoxifier', 'Constipation, detox, aging, eye disease', 'Powder, decoction', 'Winter', TRUE, 5, 9, TRUE),
('Thandrikai', 'Belleric Myrobalan', 'Terminalia bellirica', 'Fruit', 'Decrease', 'Decrease', 'Decrease', 'Respiratory, rejuvenative', 'Cough, eye disease, hair, liver', 'Powder, decoction', 'Winter', TRUE, 5, 8, FALSE),
('Seeragam', 'Cumin', 'Cuminum cyminum', 'Seed', 'Decrease', 'Neutral', 'Decrease', 'Digestive, carminative, cooling', 'Bloating, indigestion, lactation', 'Powder, tempering, water', 'Year-round', TRUE, 1, 9, TRUE),
('Venthayam', 'Fenugreek', 'Trigonella foenum-graecum', 'Seed, leaves', 'Decrease', 'Increase', 'Decrease', 'Blood sugar control, lactation, warming', 'Diabetes, arthritis, lactation, hair', 'Powder, sprouts, leaves', 'Winter', TRUE, 5, 9, TRUE),
('El', 'Sesame', 'Sesamum indicum', 'Seed', 'Decrease', 'Increase', 'Neutral', 'Warming, bone strength, oil base', 'Bone health, constipation, skin dryness', 'Oil, seeds, paste', 'Winter', TRUE, 2, 9, TRUE),
('Karunjeeragam', 'Black Cumin', 'Nigella sativa', 'Seed', 'Decrease', 'Neutral', 'Decrease', 'Immune boost, anti-inflammatory', 'Asthma, allergies, diabetes, immunity', 'Seeds, oil, powder', 'Year-round', TRUE, 5, 8, TRUE),
('Omam', 'Ajwain', 'Trachyspermum ammi', 'Seed', 'Decrease', 'Neutral', 'Decrease', 'Digestive, anti-flatulence', 'Gas, bloating, stomach pain, cold', 'Seeds, water, powder', 'Year-round', TRUE, 1, 9, TRUE),
('Poondu', 'Garlic', 'Allium sativum', 'Bulb', 'Decrease', 'Increase', 'Decrease', 'Anti-microbial, cardiovascular, warming', 'Heart disease, cholesterol, infection', 'Raw, cooked, oil', 'Year-round', TRUE, 2, 10, TRUE),
('Murungai', 'Drumstick/Moringa', 'Moringa oleifera', 'Leaves, pods', 'Decrease', 'Neutral', 'Decrease', 'Nutrient-dense, anti-inflammatory', 'Malnutrition, bone health, inflammation', 'Cooked, powder, soup', 'Year-round', TRUE, 1, 10, TRUE),
('Manathakkali', 'Black Nightshade', 'Solanum nigrum', 'Leaves, fruit', 'Neutral', 'Decrease', 'Decrease', 'Liver protector, ulcer healing', 'Mouth ulcers, liver disease, skin', 'Cooked leaves, juice', 'Monsoon', TRUE, 3, 8, TRUE),
('Vaazhapoo', 'Banana Flower', 'Musa paradisiaca', 'Flower', 'Neutral', 'Decrease', 'Decrease', 'Iron-rich, cooling, nutritive', 'Anemia, menstrual problems, diabetes', 'Cooked, curry, soup', 'Year-round', TRUE, 2, 8, TRUE),
('Sundaikai', 'Turkey Berry', 'Solanum torvum', 'Fruit', 'Decrease', 'Neutral', 'Decrease', 'Digestive, anti-parasitic', 'Worms, indigestion, cold, cough', 'Dried, curry, pickle', 'Monsoon', TRUE, 3, 7, FALSE),
('Mudakathan', 'Balloon Vine', 'Cardiospermum halicacabum', 'Leaves', 'Decrease', 'Neutral', 'Decrease', 'Joint pain relief, anti-inflammatory', 'Arthritis, rheumatism, joint pain', 'Cooked leaves, oil', 'Monsoon', TRUE, 5, 8, TRUE),
('Thoothuvalai', 'Climbing Brinjal', 'Solanum trilobatum', 'Leaves', 'Decrease', 'Neutral', 'Decrease', 'Respiratory, anti-asthmatic', 'Asthma, cough, cold, sinusitis', 'Juice, rasam, powder', 'Year-round', TRUE, 3, 8, TRUE),
('Pirandai', 'Veldt Grape', 'Cissus quadrangularis', 'Stem', 'Decrease', 'Neutral', 'Decrease', 'Bone healer, digestive', 'Fractures, bone health, indigestion', 'Juice, thuvaiyal, powder', 'Year-round', TRUE, 5, 8, TRUE),
('Avarampoo', 'Senna Flower', 'Cassia auriculata', 'Flower', 'Neutral', 'Decrease', 'Decrease', 'Anti-diabetic, skin health, cooling', 'Diabetes, skin glow, urinary infections', 'Tea, powder, decoction', 'Year-round', TRUE, 5, 8, TRUE),
('Nannari', 'Indian Sarsaparilla', 'Hemidesmus indicus', 'Root', 'Decrease', 'Decrease', 'Neutral', 'Blood purifier, cooling drink', 'Skin disease, UTI, fever, acidity', 'Syrup, decoction, drink', 'Summer', TRUE, 3, 8, TRUE),
('Vilvam', 'Bael', 'Aegle marmelos', 'Fruit, leaves', 'Decrease', 'Neutral', 'Decrease', 'Digestive, anti-diarrheal', 'Diarrhea, dysentery, diabetes, colitis', 'Juice, powder, sherbet', 'Summer', TRUE, 3, 9, TRUE);

-- ===============================================================================
-- INDEXES
-- ===============================================================================

CREATE INDEX IF NOT EXISTS IDX_HERB_TAMIL ON MEDICINAL_HERBS(NAME_TAMIL);
CREATE INDEX IF NOT EXISTS IDX_HERB_ENGLISH ON MEDICINAL_HERBS(NAME_ENGLISH);
CREATE INDEX IF NOT EXISTS IDX_HERB_BOTANICAL ON MEDICINAL_HERBS(NAME_BOTANICAL);
CREATE INDEX IF NOT EXISTS IDX_HERB_VATA ON MEDICINAL_HERBS(VATA_EFFECT);
CREATE INDEX IF NOT EXISTS IDX_HERB_PITTA ON MEDICINAL_HERBS(PITTA_EFFECT);
CREATE INDEX IF NOT EXISTS IDX_HERB_KAPHA ON MEDICINAL_HERBS(KAPHA_EFFECT);
CREATE INDEX IF NOT EXISTS IDX_HERB_KIDS ON MEDICINAL_HERBS(SAFE_FOR_KIDS);

-- ===============================================================================
-- VERIFICATION
-- ===============================================================================

SELECT COUNT(*) as TOTAL_HERBS FROM MEDICINAL_HERBS;
SELECT NAME_ENGLISH, NAME_TAMIL, VATA_EFFECT, PITTA_EFFECT, KAPHA_EFFECT, DATA_CONFIDENCE_SCORE 
FROM MEDICINAL_HERBS 
ORDER BY DATA_CONFIDENCE_SCORE DESC 
LIMIT 10;
