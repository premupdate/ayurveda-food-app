-- ===============================================================================
-- PHASE 2: AINTHINAI (Five Lands) + Tamil Seasons + Flora Mapping
-- Run in Supabase SQL Editor
-- ===============================================================================

-- 1. FIVE LANDS OF TAMIL NADU
CREATE TABLE IF NOT EXISTS ainthinai_lands (
    land_id SERIAL PRIMARY KEY,
    name_tamil VARCHAR(100),
    name_english VARCHAR(100),
    land_type VARCHAR(100),
    description_tamil TEXT,
    description_english TEXT,
    deity_tamil VARCHAR(100),
    deity_english VARCHAR(100),
    signature_flower_tamil VARCHAR(100),
    signature_flower_english VARCHAR(100),
    signature_tree_tamil VARCHAR(100),
    signature_tree_english VARCHAR(100),
    primary_occupation TEXT,
    people_name VARCHAR(200),
    staple_food TEXT,
    musical_instrument VARCHAR(100),
    associated_emotion VARCHAR(100),
    time_of_day VARCHAR(50),
    modern_districts TEXT,
    climate_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO ainthinai_lands (name_tamil, name_english, land_type, description_tamil, description_english, deity_tamil, deity_english, signature_flower_tamil, signature_flower_english, signature_tree_tamil, signature_tree_english, primary_occupation, people_name, staple_food, musical_instrument, associated_emotion, time_of_day, modern_districts, climate_type) VALUES
(
    'குறிஞ்சி', 'Kurinji', 'Mountain & Hills',
    'மலையும் மலை சார்ந்த பகுதிகளும்',
    'Mountainous terrain and surrounding hill areas. Rich in biodiversity, waterfalls, and rare medicinal plants. Home to the famous Kurinji flower that blooms once every 12 years.',
    'முருகன்', 'Murugan',
    'குறிஞ்சி', 'Kurinji (Strobilanthes kunthiana)',
    'வேங்கை', 'Vengai (Pterocarpus marsupium)',
    'Hunting, honey gathering, slash-and-burn farming, collecting roots and herbs',
    'Kuravar, Kanavar, Vettuvar',
    'Millet (Thinai, Varagu), hill paddy, honey, roots, wild fruits',
    'Tontaka (drum), Kuravai koothu',
    'Union/Love (புணர்ச்சி)',
    'Midnight (யாமம்)',
    'Nilgiris, Kodaikanal, Courtallam, Yelagiri, Javadi Hills, Kolli Hills, Palani',
    'Cool, misty, high rainfall'
),
(
    'முல்லை', 'Mullai', 'Forest & Pastoral',
    'காடும் காடு சார்ந்த பகுதிகளும்',
    'Dense tropical forests and pastoral regions. Rich in wildlife, timber, and grazing lands. Known for jasmine flowers and shepherd communities.',
    'திருமால்', 'Thirumal (Vishnu)',
    'முல்லை', 'Mullai/Jasmine (Jasminum auriculatum)',
    'கொன்றை', 'Konrai (Cassia fistula)',
    'Cattle rearing, shepherding, dairy farming, millet cultivation',
    'Ayar, Idaiyar, Yadavar',
    'Millet, dairy products, honey, wild roots, bamboo rice',
    'Yal (stringed instrument), Erudhu kuzhal (horn)',
    'Waiting/Patience (இருத்தல்)',
    'Evening (மாலை)',
    'Dharmapuri, Krishnagiri, Salem forest areas, Sathyamangalam, Anamalai',
    'Moderate, seasonal rains, warm'
),
(
    'மருதம்', 'Marutham', 'Agricultural Plains',
    'வயலும் வயல் சார்ந்த பகுதிகளும்',
    'Fertile river plains and agricultural heartland. Irrigated by major rivers like Cauvery, Vaigai, Thamiraparani. The rice bowl of Tamil Nadu.',
    'இந்திரன்', 'Indran',
    'மருதம்', 'Marutham (Lagerstroemia speciosa)',
    'மருதம்', 'Marutham tree (Lagerstroemia speciosa)',
    'Rice farming, sugarcane cultivation, vegetable growing, weaving',
    'Ulavar, Velanmadar, Toluvar, Kadaiyar',
    'Rice, sugarcane, vegetables, fruits, pulses, oil seeds',
    'Murasu (drum), Marutham yal',
    'Quarrel/Sulking (ஊடல்)',
    'Dawn (வைகறை)',
    'Thanjavur, Tiruvarur, Nagapattinam, Trichy, Madurai plains, Tirunelveli',
    'Hot, humid, well-irrigated, fertile'
),
(
    'நெய்தல்', 'Neidhal', 'Coastal & Seashore',
    'கடலும் கடல் சார்ந்த பகுதிகளும்',
    'Coastal regions and seashore areas. Rich in marine biodiversity, salt pans, and coconut groves. Home to fishing communities.',
    'வருணன்', 'Varunan',
    'நெய்தல்', 'Neidhal/Water Lily (Nymphaea nouchali)',
    'புன்னை', 'Punnai (Calophyllum inophyllum)',
    'Fishing, salt production, pearl diving, coconut cultivation, boat making',
    'Paravar, Meenavar, Nulaiyar',
    'Fish, prawns, coconut, palmyra products, seaweed',
    'Naval (conch), Meenava kuzhal',
    'Pining/Yearning (இரங்கல்)',
    'Sunset (சாய்ங்காலை)',
    'Chennai coast, Rameswaram, Kanyakumari, Cuddalore, Nagapattinam coast, Tuticorin',
    'Warm, humid, sea breeze, sandy'
),
(
    'பாலை', 'Palai', 'Arid & Desert',
    'வறண்ட நிலமும் பாலை சார்ந்த பகுதிகளும்',
    'Dry, arid regions formed when Kurinji and Mullai lands lose moisture. Not a permanent landscape but a seasonal transformation. Harsh terrain with thorny vegetation.',
    'கொற்றவை', 'Kottravai (Durga)',
    'பாலை', 'Palai (Wrightia tinctoria)',
    'உழிஞை', 'Uzhinjai (Cardiospermum halicacabum)',
    'Trade, caravan travel, highway robbery, nomadic herding',
    'Maravar, Eyinar, Kallar',
    'Dried foods, palmyra products, cactus fruits, stored grains',
    'Thudi (small drum)',
    'Separation/Parting (பிரிதல்)',
    'Noon (நண்பகல்)',
    'Ramanathapuram, Sivagangai dry areas, parts of Madurai, Virudhunagar arid zones',
    'Hot, dry, scarce water, thorny vegetation'
);

-- 2. TAMIL SEASONS (Perumpozhudu - 6 Seasons)
CREATE TABLE IF NOT EXISTS tamil_seasons (
    season_id SERIAL PRIMARY KEY,
    name_tamil VARCHAR(100),
    name_english VARCHAR(100),
    tamil_months VARCHAR(200),
    english_months VARCHAR(200),
    duration VARCHAR(100),
    weather_description TEXT,
    dominant_dosha VARCHAR(50),
    food_recommendation TEXT,
    herbs_in_season TEXT,
    fruits_in_season TEXT,
    flowers_in_season TEXT,
    farming_activity TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO tamil_seasons (name_tamil, name_english, tamil_months, english_months, duration, weather_description, dominant_dosha, food_recommendation, herbs_in_season, fruits_in_season, flowers_in_season, farming_activity) VALUES
(
    'இளவேனில்', 'Ilavenil (Early Summer)',
    'சித்திரை, வைகாசி', 'April - May',
    'Mid April to Mid June',
    'Increasing heat, dry winds, sun at its peak. Body tends to dehydrate.',
    'Pitta',
    'Cooling foods: buttermilk, tender coconut, watermelon, cucumber, nannari sherbet. Avoid spicy/oily.',
    'Vetiver, Nannari, Sandalwood, Aloe Vera, Brahmi',
    'Mango (Mangai), Jackfruit (Palaa), Watermelon (Tharbusani), Palm fruit (Nungu)',
    'Neidhal (Water lily), Marutham, Avarampoo, Jasmine',
    'Summer ploughing, groundnut harvesting, mango season'
),
(
    'முதுவேனில்', 'Mudhuvenil (Late Summer)',
    'ஆனி, ஆடி', 'June - July',
    'Mid June to Mid August',
    'Intense heat followed by early monsoon winds. Hot and increasingly humid.',
    'Pitta/Vata',
    'Hydrating foods: porridges, light soups, buttermilk rice. Start warming spices as monsoon approaches.',
    'Nilavembu, Tulasi, Ginger, Neem, Thoothuvalai',
    'Mango (late), Guava (Koyyaa), Wood apple (Villathi)',
    'Mullai (Jasmine), Arali, Hibiscus',
    'Paddy transplanting begins, monsoon preparation'
),
(
    'கார்', 'Kaar (Rainy/Monsoon)',
    'ஆவணி, புரட்டாசி', 'August - September',
    'Mid August to Mid October',
    'Southwest monsoon rains. Heavy rainfall, flooding in delta regions. Cool and damp.',
    'Vata',
    'Warming foods: ginger kashayam, turmeric milk, sesame-based dishes, well-cooked lentils. Avoid raw/cold.',
    'Ginger, Turmeric, Tulasi, Pepper, Thippili, Omam',
    'Banana (Vaazhai), Pomegranate (Maathulai), Guava',
    'Kurinji (blooms every 12 years), Kaaththamanalli, Thumpai',
    'Paddy growing season, vegetable sowing'
),
(
    'கூதிர்', 'Koothir (Autumn/Post-Monsoon)',
    'ஐப்பசி, கார்த்திகை', 'October - November',
    'Mid October to Mid December',
    'Northeast monsoon. Continued rains especially on east coast. Cool temperatures settling in.',
    'Vata/Kapha',
    'Warming with grounding foods: root vegetables, drumstick, pumpkin, millets. Include ghee.',
    'Ashwagandha, Fenugreek, Sesame, Curry leaves, Moringa',
    'Amla (Nellikai), Custard apple (Seetha), Sapota (Sapotta)',
    'Konrai (Cassia fistula), Lotus, Parijatham',
    'Northeast monsoon paddy, harvest preparation'
),
(
    'முன்பனி', 'Munpani (Early Winter)',
    'மார்கழி, தை', 'December - January',
    'Mid December to Mid February',
    'Cool dry weather. Morning mist and dew. Comfortable temperatures, especially in hill regions.',
    'Kapha',
    'Warming foods: pongal, sesame laddoo, jaggery sweets, ginger-pepper kashayam, ghee-rich foods.',
    'Sesame, Ashwagandha, Black pepper, Cinnamon, Fenugreek, Dry ginger',
    'Orange (Kamala), Grape (Thiratchai), Strawberry (hill areas), Carrot',
    'Rose (Panneer), Marigold (Samandhi), Chrysanthemum (Sevvandhi)',
    'Pongal harvest festival, sugarcane harvest, paddy harvest'
),
(
    'பின்பனி', 'Pinpani (Late Winter)',
    'மாசி, பங்குனி', 'February - March',
    'Mid February to Mid April',
    'End of winter, warming up. Pleasant weather, ideal for outdoor activities.',
    'Kapha/Pitta',
    'Transition foods: lighter than winter but warming. Start including bitter vegetables, leafy greens.',
    'Neem (spring shoots), Turmeric, Brahmi, Manathakkali, Agathi',
    'Banana, Papaya (Pappali), Jackfruit (early), Mango (raw)',
    'Flame of forest (Purasu), Neem flowers, Iluppai',
    'Summer crop sowing, festival season (Panguni Uthiram)'
);

-- 3. LAND-FLORA MAPPING (What grows where)
CREATE TABLE IF NOT EXISTS land_flora_mapping (
    mapping_id SERIAL PRIMARY KEY,
    land_id INT REFERENCES ainthinai_lands(land_id),
    flora_type VARCHAR(50),
    name_tamil VARCHAR(200),
    name_english VARCHAR(200),
    name_botanical VARCHAR(200),
    category VARCHAR(50),
    seasonal_availability VARCHAR(100),
    medicinal_uses TEXT,
    culinary_uses TEXT,
    dosha_impact VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO land_flora_mapping (land_id, flora_type, name_tamil, name_english, name_botanical, category, seasonal_availability, medicinal_uses, culinary_uses, dosha_impact) VALUES
-- KURINJI (Mountains) - ID 1
(1, 'Herb', 'வல்லாரை', 'Brahmi/Gotu Kola', 'Centella asiatica', 'Medicinal Herb', 'Monsoon', 'Brain tonic, memory, anxiety relief', 'Chutney, juice, salad', 'V↓ P↓'),
(1, 'Herb', 'கற்பூரவள்ளி', 'Mexican Mint', 'Coleus amboinicus', 'Medicinal Herb', 'Year-round', 'Cough, cold, throat infection', 'Juice, fried snack', 'V↓ K↓'),
(1, 'Fruit', 'நாவல்பழம்', 'Indian Blackberry', 'Syzygium cumini', 'Fruit', 'Summer', 'Anti-diabetic, mouth ulcers', 'Fresh fruit, seed powder', 'P↓ K↓'),
(1, 'Herb', 'ஆடாதொடை', 'Malabar Nut', 'Justicia adhatoda', 'Medicinal Herb', 'Winter', 'Asthma, bronchitis, cough', 'Syrup, decoction', 'K↓ P↓'),
(1, 'Flower', 'குறிஞ்சி', 'Kurinji Flower', 'Strobilanthes kunthiana', 'Sacred Flower', 'Every 12 years', 'Rare medicinal, ceremonial', 'Honey source', 'P↓'),
(1, 'Herb', 'சீந்தில்', 'Guduchi', 'Tinospora cordifolia', 'Medicinal Herb', 'Year-round', 'Immunity, fever, diabetes', 'Kashayam, powder', 'V↓ P↓ K↓'),
(1, 'Grain', 'தினை', 'Foxtail Millet', 'Setaria italica', 'Staple Grain', 'Kaar season', 'Blood sugar control, light', 'Rice replacement', 'V↓ K↓'),
(1, 'Fruit', 'சீதாப்பழம்', 'Custard Apple', 'Annona squamosa', 'Fruit', 'Koothir', 'Energy, cooling', 'Fresh fruit', 'V↓ P↓'),
-- MULLAI (Forest) - ID 2
(2, 'Flower', 'முல்லை', 'Jasmine', 'Jasminum auriculatum', 'Sacred Flower', 'Year-round', 'Calming, mood enhancer, skin', 'Garlands, essential oil', 'V↓ P↓'),
(2, 'Herb', 'அமுக்கரா', 'Ashwagandha', 'Withania somnifera', 'Medicinal Herb', 'Winter', 'Stress, strength, immunity', 'Powder in milk', 'V↓'),
(2, 'Herb', 'முடக்கத்தான்', 'Balloon Vine', 'Cardiospermum halicacabum', 'Medicinal Herb', 'Monsoon', 'Joint pain, arthritis', 'Cooked greens, oil', 'V↓ K↓'),
(2, 'Fruit', 'கொய்யா', 'Guava', 'Psidium guajava', 'Fruit', 'Mudhuvenil', 'Vitamin C, digestion', 'Fresh, juice', 'V↓ K↓'),
(2, 'Herb', 'தூதுவளை', 'Climbing Brinjal', 'Solanum trilobatum', 'Medicinal Herb', 'Year-round', 'Asthma, cough, cold', 'Rasam, juice', 'K↓ V↓'),
(2, 'Tree', 'கொன்றை', 'Indian Laburnum', 'Cassia fistula', 'Medicinal Tree', 'Summer', 'Laxative, skin care', 'Pod pulp, decoction', 'P↓ K↓'),
(2, 'Grain', 'வரகு', 'Kodo Millet', 'Paspalum scrobiculatum', 'Staple Grain', 'Kaar season', 'Anti-diabetic, cooling', 'Rice replacement', 'P↓ K↓'),
(2, 'Herb', 'நிலவேம்பு', 'Andrographis', 'Andrographis paniculata', 'Medicinal Herb', 'Monsoon', 'Fever, anti-viral', 'Kashayam', 'P↓ K↓'),
-- MARUTHAM (Agricultural Plains) - ID 3
(3, 'Grain', 'நெல்', 'Rice/Paddy', 'Oryza sativa', 'Staple Grain', 'Kaar-Koothir', 'Staple food, energy', 'Boiled rice, idli, dosa', 'V↓ K↑'),
(3, 'Herb', 'மஞ்சள்', 'Turmeric', 'Curcuma longa', 'Spice/Herb', 'Year-round', 'Anti-inflammatory, healing', 'Cooking, paste, milk', 'V↓ K↓'),
(3, 'Herb', 'முருங்கை', 'Moringa', 'Moringa oleifera', 'Medicinal Tree', 'Year-round', 'Nutrient-dense, bone health', 'Sambar, poriyal, soup', 'V↓ K↓'),
(3, 'Herb', 'மணத்தக்காளி', 'Black Nightshade', 'Solanum nigrum', 'Medicinal Herb', 'Monsoon', 'Liver care, ulcer healing', 'Sambar, poriyal', 'P↓ K↓'),
(3, 'Fruit', 'வாழை', 'Banana', 'Musa paradisiaca', 'Fruit', 'Year-round', 'Energy, digestion', 'Fruit, flower, stem all used', 'V↓ P↓'),
(3, 'Flower', 'அவரம்பூ', 'Senna Flower', 'Cassia auriculata', 'Medicinal Flower', 'Year-round', 'Diabetes, skin glow', 'Tea, powder', 'P↓ K↓'),
(3, 'Herb', 'வெந்தயம்', 'Fenugreek', 'Trigonella foenum-graecum', 'Spice/Herb', 'Winter', 'Diabetes, lactation', 'Sprouts, powder, leaves', 'V↓ K↓'),
(3, 'Herb', 'கறிவேப்பிலை', 'Curry Leaves', 'Murraya koenigii', 'Culinary Herb', 'Year-round', 'Diabetes, hair, digestion', 'Tempering, chutney', 'V↓ K↓'),
-- NEIDHAL (Coastal) - ID 4
(4, 'Flower', 'நெய்தல்', 'Blue Water Lily', 'Nymphaea nouchali', 'Sacred Flower', 'Year-round', 'Cooling, cardiac tonic', 'Tea, powder', 'P↓ V↓'),
(4, 'Tree', 'புன்னை', 'Punnai/Beauty Leaf', 'Calophyllum inophyllum', 'Medicinal Tree', 'Year-round', 'Wound healing, rheumatism', 'Seed oil', 'V↓ P↓'),
(4, 'Herb', 'வெட்டிவேர்', 'Vetiver', 'Chrysopogon zizanioides', 'Medicinal Herb', 'Summer', 'Cooling, skin, fever', 'Water infusion, mat', 'P↓ V↓'),
(4, 'Fruit', 'நுங்கு', 'Palm Fruit', 'Borassus flabellifer', 'Fruit', 'Ilavenil', 'Cooling, liver tonic', 'Fresh, toddy, jaggery', 'P↓ V↓'),
(4, 'Herb', 'கும்மட்டி', 'Sea Purslane', 'Sesuvium portulacastrum', 'Coastal Herb', 'Year-round', 'Anti-inflammatory, cooling', 'Pickled, cooked', 'P↓'),
(4, 'Tree', 'தென்னை', 'Coconut', 'Cocos nucifera', 'Fruit/Oil', 'Year-round', 'Cooling, hair, cooking oil', 'Milk, oil, water, flesh', 'P↓ K↑'),
(4, 'Herb', 'நன்னாரி', 'Indian Sarsaparilla', 'Hemidesmus indicus', 'Medicinal Root', 'Summer', 'Blood purifier, cooling drink', 'Sherbet, syrup', 'P↓ V↓'),
-- PALAI (Arid) - ID 5
(5, 'Tree', 'பாலை', 'Ivory Tree', 'Wrightia tinctoria', 'Medicinal Tree', 'Year-round', 'Skin disease, wounds, dental', 'Bark decoction, dye', 'P↓ K↓'),
(5, 'Fruit', 'கள்ளி', 'Cactus/Prickly Pear', 'Opuntia ficus-indica', 'Fruit', 'Summer', 'Cooling, anti-diabetic', 'Fruit, juice', 'P↓'),
(5, 'Tree', 'பனை', 'Palmyra Palm', 'Borassus flabellifer', 'Multi-use Tree', 'Year-round', 'Cooling, liver, all parts used', 'Toddy, jaggery, fruit, fiber', 'P↓ V↓'),
(5, 'Herb', 'சோற்றுக்கற்றாழை', 'Aloe Vera', 'Aloe barbadensis', 'Medicinal Herb', 'Year-round', 'Skin, burns, digestion', 'Gel, juice', 'P↓ K↓'),
(5, 'Herb', 'ஆவாரம்பூ', 'Senna', 'Cassia auriculata', 'Medicinal Flower', 'Year-round', 'Diabetes, skin, hair', 'Tea, powder', 'P↓ K↓'),
(5, 'Tree', 'வேம்பு', 'Neem', 'Azadirachta indica', 'Medicinal Tree', 'Year-round', 'Blood purifier, anti-bacterial', 'Leaves cooked, powder', 'P↓ K↓');

-- 4. SMART FEEDBACK PARSING LOG
CREATE TABLE IF NOT EXISTS feedback_parsed_items (
    parsed_id SERIAL PRIMARY KEY,
    feedback_id INT,
    user_id VARCHAR(100),
    original_note TEXT,
    parsed_dish_name VARCHAR(200),
    parsed_ingredients TEXT,
    parsed_herbs TEXT,
    parsed_vegetables TEXT,
    ai_classification TEXT,
    dosha_assessment VARCHAR(100),
    added_to_recipes BOOLEAN DEFAULT FALSE,
    added_to_herbs BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- VERIFY
SELECT 'ainthinai_lands' as tbl, COUNT(*) as cnt FROM ainthinai_lands
UNION ALL SELECT 'tamil_seasons', COUNT(*) FROM tamil_seasons
UNION ALL SELECT 'land_flora_mapping', COUNT(*) FROM land_flora_mapping;
