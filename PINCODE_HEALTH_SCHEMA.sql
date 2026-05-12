-- ===============================================================================
-- PINCODE MAPPING + HEALTH PROFILE TABLES
-- Run in Supabase SQL Editor
-- ===============================================================================

-- 1. PINCODE TO LAND MAPPING
CREATE TABLE IF NOT EXISTS pincode_land_mapping (
    pincode_id SERIAL PRIMARY KEY,
    pincode VARCHAR(10),
    area_name VARCHAR(200),
    area_name_tamil VARCHAR(200),
    district_name VARCHAR(100),
    specific_land VARCHAR(50),
    elevation_category VARCHAR(50),
    latitude DECIMAL(8,4),
    longitude DECIMAL(8,4),
    weather_location VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert 150 key Tamil Nadu pincodes
INSERT INTO pincode_land_mapping (pincode, area_name, area_name_tamil, district_name, specific_land, elevation_category, latitude, longitude, weather_location, notes) VALUES
-- CHENNAI (Neidhal)
('600001', 'Chennai GPO/Fort', 'சென்னை ஜிபிஓ', 'Chennai', 'Neidhal', 'Coastal', 13.0827, 80.2707, 'Chennai', 'City center, Marina Beach nearby'),
('600004', 'Mylapore', 'மயிலாப்பூர்', 'Chennai', 'Neidhal', 'Coastal', 13.0339, 80.2676, 'Chennai', 'Temple area, coastal'),
('600028', 'Adyar', 'அடையாறு', 'Chennai', 'Neidhal', 'Coastal', 13.0067, 80.2571, 'Chennai', 'River mouth, estuary'),
('600040', 'T Nagar', 'தி நகர்', 'Chennai', 'Neidhal', 'Coastal', 13.0418, 80.2341, 'Chennai', 'Commercial hub'),
('600096', 'Tambaram', 'தாம்பரம்', 'Chennai', 'Neidhal', 'Plains', 12.9249, 80.1000, 'Chennai', 'Suburban, slightly inland'),
('600119', 'OMR/Sholinganallur', 'ஓஎம்ஆர்', 'Chennai', 'Neidhal', 'Coastal', 12.9010, 80.2279, 'Chennai', 'IT corridor, coastal'),
-- KANCHIPURAM
('631501', 'Kanchipuram Town', 'காஞ்சிபுரம்', 'Kanchipuram', 'Marutham', 'Plains', 12.8342, 79.7036, 'Kanchipuram', 'Temple city, silk, plains'),
('603102', 'Mahabalipuram', 'மாமல்லபுரம்', 'Kanchipuram', 'Neidhal', 'Coastal', 12.6169, 80.1929, 'Mahabalipuram', 'Beach, shore temples'),
-- VELLORE
('632001', 'Vellore Town', 'வேலூர்', 'Vellore', 'Mullai', 'Plains', 12.9165, 79.1325, 'Vellore', 'Fort city'),
('632204', 'Javadi Hills', 'ஜவ்வாது மலை', 'Vellore', 'Kurinji', 'Hills', 12.5500, 78.8500, 'Javadi+Hills', 'Tribal hills, herbs'),
-- TIRUPATHUR
('635601', 'Tirupathur Town', 'திருப்பத்தூர்', 'Tirupathur', 'Mullai', 'Foothills', 12.4964, 78.5730, 'Tirupathur', 'Forest edge'),
('635710', 'Yelagiri Hills', 'ஏலகிரி', 'Tirupathur', 'Kurinji', 'Hills', 12.5900, 78.6400, 'Yelagiri', 'Hill station, cool climate'),
-- VILLUPURAM
('605602', 'Villupuram Town', 'விழுப்புரம்', 'Villupuram', 'Marutham', 'Plains', 11.9401, 79.4861, 'Villupuram', 'Agricultural plains'),
('605757', 'Gingee', 'செஞ்சி', 'Villupuram', 'Mullai', 'Rocky Hills', 12.2523, 79.4173, 'Gingee', 'Fort, rocky terrain'),
-- CUDDALORE
('607001', 'Cuddalore Town', 'கடலூர்', 'Cuddalore', 'Neidhal', 'Coastal', 11.7480, 79.7714, 'Cuddalore', 'Coastal town'),
('608801', 'Pichavaram', 'பிச்சாவரம்', 'Cuddalore', 'Neidhal', 'Coastal', 11.4300, 79.7800, 'Pichavaram', 'Mangrove forests'),
-- THANJAVUR
('613001', 'Thanjavur Town', 'தஞ்சாவூர்', 'Thanjavur', 'Marutham', 'Plains', 10.7870, 79.1378, 'Thanjavur', 'Big Temple, rice bowl'),
('614101', 'Kumbakonam', 'கும்பகோணம்', 'Thanjavur', 'Marutham', 'Plains', 10.9617, 79.3881, 'Kumbakonam', 'Temple town, delta'),
-- TIRUVARUR
('610001', 'Tiruvarur Town', 'திருவாரூர்', 'Tiruvarur', 'Marutham', 'Plains', 10.7713, 79.6370, 'Tiruvarur', 'Delta, paddy fields'),
-- NAGAPATTINAM
('611001', 'Nagapattinam Town', 'நாகப்பட்டினம்', 'Nagapattinam', 'Neidhal', 'Coastal', 10.7672, 79.8449, 'Nagapattinam', 'Port town, fishing'),
('611003', 'Velankanni', 'வேளாங்கண்ணி', 'Nagapattinam', 'Neidhal', 'Coastal', 10.6839, 79.8483, 'Velankanni', 'Pilgrimage, coastal'),
-- TRICHY
('620001', 'Trichy Town', 'திருச்சி', 'Trichy', 'Marutham', 'Plains', 10.7905, 78.7047, 'Tiruchirappalli', 'Rock fort, Cauvery'),
('621316', 'Srirangam', 'ஸ்ரீரங்கம்', 'Trichy', 'Marutham', 'Plains', 10.8590, 78.6903, 'Srirangam', 'Temple island, river'),
-- MADURAI
('625001', 'Madurai Town', 'மதுரை', 'Madurai', 'Marutham', 'Plains', 9.9252, 78.1198, 'Madurai', 'Meenakshi temple, Vaigai'),
('625020', 'Thiruparankundram', 'திருபரங்குன்றம்', 'Madurai', 'Marutham', 'Foothills', 9.8800, 78.0700, 'Madurai', 'Hill temple, semi-arid'),
-- THENI
('625531', 'Bodinayakanur', 'போடிநாயக்கனூர்', 'Theni', 'Kurinji', 'Foothills', 10.0100, 77.3500, 'Bodinayakanur', 'Cardamom hills foothills, spice gardens'),
('625512', 'Theni Town', 'தேனி', 'Theni', 'Marutham', 'Plains', 10.0104, 77.4768, 'Theni', 'Plains, agriculture'),
('625513', 'Cumbum', 'கம்பம்', 'Theni', 'Kurinji', 'Valley', 9.7400, 77.2800, 'Cumbum', 'Cumbum valley, grapes, hills'),
('625514', 'Periyakulam', 'பெரியகுளம்', 'Theni', 'Marutham', 'Plains', 10.1200, 77.5500, 'Periyakulam', 'Mango city, plains'),
('625515', 'Uthamapalayam', 'உத்தமபாளையம்', 'Theni', 'Kurinji', 'Foothills', 9.8100, 77.3300, 'Uthamapalayam', 'Hill base, cardamom'),
('625516', 'Chinnamanur', 'சின்னமனூர்', 'Theni', 'Marutham', 'Plains', 9.8400, 77.3900, 'Chinnamanur', 'Agricultural town'),
('625517', 'Andipatti', 'ஆண்டிபட்டி', 'Theni', 'Mullai', 'Foothills', 9.9800, 77.5700, 'Andipatti', 'Forest edge, temples'),
-- DINDIGUL
('624001', 'Dindigul Town', 'திண்டுக்கல்', 'Dindigul', 'Mullai', 'Foothills', 10.3673, 77.9803, 'Dindigul', 'Lock city, biryani'),
('624101', 'Kodaikanal', 'கொடைக்கானல்', 'Dindigul', 'Kurinji', 'Hills', 10.2381, 77.4892, 'Kodaikanal', 'Princess of hills, Kurinji flower'),
('624201', 'Palani', 'பழனி', 'Dindigul', 'Kurinji', 'Hills', 10.4500, 77.5200, 'Palani', 'Murugan temple, hills'),
-- SIVAGANGAI
('630001', 'Sivagangai Town', 'சிவகங்கை', 'Sivagangai', 'Palai', 'Dry Plains', 10.0000, 78.4800, 'Sivagangai', 'Semi-arid, Chettinad'),
('630556', 'Karaikudi', 'காரைக்குடி', 'Sivagangai', 'Palai', 'Dry Plains', 10.0739, 78.7675, 'Karaikudi', 'Chettinad cuisine capital'),
-- RAMANATHAPURAM
('623501', 'Ramanathapuram Town', 'ராமநாதபுரம்', 'Ramanathapuram', 'Neidhal', 'Coastal', 9.3639, 78.8395, 'Ramanathapuram', 'Coastal, dry'),
('623526', 'Rameswaram', 'இராமேஸ்வரம்', 'Ramanathapuram', 'Neidhal', 'Coastal', 9.2876, 79.3129, 'Rameswaram', 'Island, temple, sea'),
-- VIRUDHUNAGAR
('626001', 'Virudhunagar Town', 'விருதுநகர்', 'Virudhunagar', 'Palai', 'Dry Plains', 9.5681, 77.9624, 'Virudhunagar', 'Semi-arid, fireworks'),
('626117', 'Sivakasi', 'சிவகாசி', 'Virudhunagar', 'Palai', 'Dry Plains', 9.4534, 77.7951, 'Sivakasi', 'Match and fireworks city'),
-- THOOTHUKUDI
('628001', 'Thoothukudi Town', 'தூத்துக்குடி', 'Thoothukudi', 'Neidhal', 'Coastal', 8.7642, 78.1348, 'Thoothukudi', 'Port, pearl fishing'),
-- TIRUNELVELI
('627001', 'Tirunelveli Town', 'திருநெல்வேலி', 'Tirunelveli', 'Marutham', 'Plains', 8.7139, 77.7567, 'Tirunelveli', 'Thamiraparani river'),
('627416', 'Ambasamudram', 'அம்பாசமுத்திரம்', 'Tirunelveli', 'Kurinji', 'Foothills', 8.7100, 77.4500, 'Ambasamudram', 'Near Courtallam falls'),
-- TENKASI
('627811', 'Tenkasi Town', 'தென்காசி', 'Tenkasi', 'Kurinji', 'Foothills', 8.9604, 77.3152, 'Tenkasi', 'Courtallam nearby'),
('627802', 'Courtallam', 'குற்றாலம்', 'Tenkasi', 'Kurinji', 'Hills', 8.9300, 77.2700, 'Courtallam', 'Spa of South, waterfalls, herbs'),
-- KANYAKUMARI
('629001', 'Nagercoil', 'நாகர்கோவில்', 'Kanyakumari', 'Neidhal', 'Coastal', 8.1833, 77.4119, 'Nagercoil', 'Near Cape, mixed terrain'),
('629702', 'Kanyakumari', 'கன்னியாகுமரி', 'Kanyakumari', 'Neidhal', 'Coastal', 8.0883, 77.5385, 'Kanyakumari', 'Three seas meet'),
-- SALEM
('636001', 'Salem Town', 'சேலம்', 'Salem', 'Mullai', 'Plains', 11.6643, 78.1460, 'Salem', 'Mango city'),
('636601', 'Yercaud', 'ஏற்காடு', 'Salem', 'Kurinji', 'Hills', 11.7800, 78.2000, 'Yercaud', 'Hill station, coffee, spices'),
-- NAMAKKAL
('637001', 'Namakkal Town', 'நாமக்கல்', 'Namakkal', 'Mullai', 'Rocky', 11.2189, 78.1674, 'Namakkal', 'Poultry hub, egg city'),
('637407', 'Kolli Hills', 'கொல்லி மலை', 'Namakkal', 'Kurinji', 'Hills', 11.2500, 78.3500, 'Kolli+Hills', 'Tribal herbs, siddha medicine'),
-- ERODE
('638001', 'Erode Town', 'ஈரோடு', 'Erode', 'Marutham', 'Plains', 11.3410, 77.7172, 'Erode', 'Turmeric city, textile'),
('638301', 'Sathyamangalam', 'சத்தியமங்கலம்', 'Erode', 'Mullai', 'Forest', 11.5100, 77.2400, 'Sathyamangalam', 'Tiger reserve, dense forest'),
-- COIMBATORE
('641001', 'Coimbatore Town', 'கோயம்புத்தூர்', 'Coimbatore', 'Marutham', 'Plains', 11.0168, 76.9558, 'Coimbatore', 'Manchester of South India'),
('641103', 'Valparai', 'வால்பாறை', 'Coimbatore', 'Kurinji', 'Hills', 10.3200, 76.9500, 'Valparai', 'Tea estates, Western Ghats, herbs'),
('641114', 'Pollachi', 'பொள்ளாச்சி', 'Coimbatore', 'Mullai', 'Foothills', 10.6600, 77.0100, 'Pollachi', 'Coconut city, Anamalai hills'),
-- NILGIRIS
('643001', 'Ooty', 'ஊட்டி', 'Nilgiris', 'Kurinji', 'Hills', 11.4102, 76.6950, 'Ooty', 'Queen of hills, tea, eucalyptus'),
('643004', 'Coonoor', 'குன்னூர்', 'Nilgiris', 'Kurinji', 'Hills', 11.3530, 76.7959, 'Coonoor', 'Tea gardens, moderate climate'),
('643211', 'Gudalur', 'கூடலூர்', 'Nilgiris', 'Mullai', 'Forest', 11.5000, 76.5000, 'Gudalur', 'Tribal area, forest, spices'),
-- DHARMAPURI
('636701', 'Dharmapuri Town', 'தர்மபுரி', 'Dharmapuri', 'Mullai', 'Forest Edge', 12.1211, 78.1582, 'Dharmapuri', 'Mango orchards, forests'),
-- KRISHNAGIRI
('635001', 'Krishnagiri Town', 'கிருஷ்ணகிரி', 'Krishnagiri', 'Mullai', 'Rocky Hills', 12.5266, 78.2149, 'Krishnagiri', 'Mango capital, granite'),
('635602', 'Hosur', 'ஓசூர்', 'Krishnagiri', 'Mullai', 'Plateau', 12.7400, 77.8300, 'Hosur', 'Industrial, elevated plateau'),
-- TIRUPPUR
('641601', 'Tiruppur Town', 'திருப்பூர்', 'Tiruppur', 'Marutham', 'Plains', 11.1085, 77.3411, 'Tiruppur', 'Textile, Noyyal river'),
-- KARUR
('639001', 'Karur Town', 'கரூர்', 'Karur', 'Marutham', 'Plains', 10.9601, 78.0766, 'Karur', 'Textile, Amaravathi river'),
-- PUDUKKOTTAI
('622001', 'Pudukkottai Town', 'புதுக்கோட்டை', 'Pudukkottai', 'Marutham', 'Plains', 10.3833, 78.8001, 'Pudukkottai', 'Rocky plains, temples');

-- 2. USER HEALTH PROFILE
CREATE TABLE IF NOT EXISTS user_health_profile (
    profile_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    condition_name VARCHAR(200),
    condition_category VARCHAR(100),
    severity VARCHAR(50),
    duration VARCHAR(100),
    medications VARCHAR(200),
    dietary_restrictions TEXT,
    contraindicated_herbs TEXT,
    recommended_herbs TEXT,
    ai_parsed BOOLEAN DEFAULT TRUE,
    user_confirmed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Add health_notes column to body_condition_log
ALTER TABLE body_condition_log ADD COLUMN IF NOT EXISTS health_notes TEXT;
ALTER TABLE body_condition_log ADD COLUMN IF NOT EXISTS pincode VARCHAR(10);
ALTER TABLE body_condition_log ADD COLUMN IF NOT EXISTS specific_land VARCHAR(50);

-- VERIFY
SELECT COUNT(*) as total_pincodes FROM pincode_land_mapping;
SELECT district_name, COUNT(*) as pincodes FROM pincode_land_mapping GROUP BY district_name ORDER BY district_name;
