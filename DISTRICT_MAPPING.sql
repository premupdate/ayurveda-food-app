-- ===============================================================================
-- DISTRICT TO AINTHINAI LAND MAPPING - 38 Tamil Nadu Districts
-- Run in Supabase SQL Editor
-- ===============================================================================

CREATE TABLE IF NOT EXISTS district_land_mapping (
    district_id SERIAL PRIMARY KEY,
    district_name VARCHAR(100),
    district_tamil VARCHAR(100),
    primary_land_id INT REFERENCES ainthinai_lands(land_id),
    primary_land VARCHAR(50),
    secondary_land VARCHAR(50),
    latitude DECIMAL(8,4),
    longitude DECIMAL(8,4),
    weather_location VARCHAR(100),
    notable_features TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO district_land_mapping (district_name, district_tamil, primary_land_id, primary_land, secondary_land, latitude, longitude, weather_location, notable_features) VALUES
('Chennai', 'சென்னை', 4, 'Neidhal', NULL, 13.0827, 80.2707, 'Chennai', 'Coastal metro, Marina Beach'),
('Kanchipuram', 'காஞ்சிபுரம்', 4, 'Neidhal', 'Marutham', 12.8342, 79.7036, 'Kanchipuram', 'Temple city, silk weaving, coast'),
('Tiruvallur', 'திருவள்ளூர்', 4, 'Neidhal', 'Marutham', 13.1439, 79.9086, 'Tiruvallur', 'Coast, lakes, suburban'),
('Chengalpattu', 'செங்கல்பட்டு', 4, 'Neidhal', 'Marutham', 12.6819, 79.9888, 'Chengalpattu', 'Coastal, Mahabalipuram'),
('Vellore', 'வேலூர்', 2, 'Mullai', 'Kurinji', 12.9165, 79.1325, 'Vellore', 'Fort city, forests, Yelagiri nearby'),
('Tirupathur', 'திருப்பத்தூர்', 1, 'Kurinji', 'Mullai', 12.4964, 78.5730, 'Tirupathur', 'Yelagiri Hills, Javadi Hills'),
('Ranipet', 'ராணிப்பேட்டை', 3, 'Marutham', 'Mullai', 12.9224, 79.3213, 'Ranipet', 'Industrial, plains'),
('Villupuram', 'விழுப்புரம்', 3, 'Marutham', NULL, 11.9401, 79.4861, 'Villupuram', 'Agricultural plains, Gingee fort'),
('Cuddalore', 'கடலூர்', 4, 'Neidhal', 'Marutham', 11.7480, 79.7714, 'Cuddalore', 'Coastal, Pichavaram mangroves'),
('Thanjavur', 'தஞ்சாவூர்', 3, 'Marutham', NULL, 10.7870, 79.1378, 'Thanjavur', 'Rice bowl, Cauvery delta, Big Temple'),
('Tiruvarur', 'திருவாரூர்', 3, 'Marutham', NULL, 10.7713, 79.6370, 'Tiruvarur', 'Cauvery delta, paddy fields'),
('Nagapattinam', 'நாகப்பட்டினம்', 4, 'Neidhal', 'Marutham', 10.7672, 79.8449, 'Nagapattinam', 'Coastal, fishing, Velankanni'),
('Mayiladuthurai', 'மயிலாடுதுறை', 3, 'Marutham', NULL, 11.1018, 79.6491, 'Mayiladuthurai', 'Cauvery delta, temples'),
('Trichy', 'திருச்சிராப்பள்ளி', 3, 'Marutham', NULL, 10.7905, 78.7047, 'Tiruchirappalli', 'Rock fort, Cauvery, plains'),
('Karur', 'கரூர்', 3, 'Marutham', NULL, 10.9601, 78.0766, 'Karur', 'Textile city, Amaravathi river'),
('Perambalur', 'பெரம்பலூர்', 3, 'Marutham', NULL, 11.2320, 78.8807, 'Perambalur', 'Agricultural, cement'),
('Ariyalur', 'அரியலூர்', 3, 'Marutham', NULL, 11.1401, 79.0783, 'Ariyalur', 'Fossils, limestone, plains'),
('Pudukkottai', 'புதுக்கோட்டை', 3, 'Marutham', 'Palai', 10.3833, 78.8001, 'Pudukkottai', 'Dry plains, temples'),
('Sivagangai', 'சிவகங்கை', 5, 'Palai', 'Marutham', 10.0000, 78.4800, 'Sivagangai', 'Semi-arid, Chettinad cuisine'),
('Madurai', 'மதுரை', 3, 'Marutham', 'Palai', 9.9252, 78.1198, 'Madurai', 'Temple city, Vaigai river, plains'),
('Theni', 'தேனி', 3, 'Marutham', 'Kurinji', 10.0104, 77.4768, 'Theni', 'Western Ghats, spice gardens, plains'),
('Dindigul', 'திண்டுக்கல்', 1, 'Kurinji', 'Mullai', 10.3673, 77.9803, 'Dindigul', 'Kodaikanal hills, lock city'),
('Ramanathapuram', 'ராமநாதபுரம்', 4, 'Neidhal', 'Palai', 9.3639, 78.8395, 'Ramanathapuram', 'Rameswaram, coastal, dry interior'),
('Virudhunagar', 'விருதுநகர்', 5, 'Palai', 'Marutham', 9.5681, 77.9624, 'Virudhunagar', 'Semi-arid, fireworks, match industry'),
('Thoothukudi', 'தூத்துக்குடி', 4, 'Neidhal', NULL, 8.7642, 78.1348, 'Thoothukudi', 'Pearl city, port, coastal'),
('Tirunelveli', 'திருநெல்வேலி', 3, 'Marutham', 'Kurinji', 8.7139, 77.7567, 'Tirunelveli', 'Thamiraparani river, Courtallam falls'),
('Tenkasi', 'தென்காசி', 1, 'Kurinji', 'Mullai', 8.9604, 77.3152, 'Tenkasi', 'Courtallam, Western Ghats, forests'),
('Kanyakumari', 'கன்னியாகுமரி', 4, 'Neidhal', 'Kurinji', 8.0883, 77.5385, 'Kanyakumari', 'Three seas meet, hills + coast'),
('Salem', 'சேலம்', 2, 'Mullai', 'Kurinji', 11.6643, 78.1460, 'Salem', 'Yercaud hills, mango city, forests'),
('Namakkal', 'நாமக்கல்', 2, 'Mullai', 'Marutham', 11.2189, 78.1674, 'Namakkal', 'Poultry hub, Kolli Hills nearby'),
('Erode', 'ஈரோடு', 2, 'Mullai', 'Marutham', 11.3410, 77.7172, 'Erode', 'Turmeric city, Sathyamangalam forests'),
('Coimbatore', 'கோயம்புத்தூர்', 1, 'Kurinji', 'Mullai', 11.0168, 76.9558, 'Coimbatore', 'Manchester of South India, Western Ghats'),
('Tiruppur', 'திருப்பூர்', 3, 'Marutham', NULL, 11.1085, 77.3411, 'Tiruppur', 'Textile hub, Noyyal river plains'),
('Nilgiris', 'நீலகிரி', 1, 'Kurinji', NULL, 11.4102, 76.6950, 'Ooty', 'Queen of hills, tea plantations, Kurinji flower'),
('Dharmapuri', 'தர்மபுரி', 2, 'Mullai', NULL, 12.1211, 78.1582, 'Dharmapuri', 'Dense forests, mango orchards'),
('Krishnagiri', 'கிருஷ்ணகிரி', 2, 'Mullai', 'Kurinji', 12.5266, 78.2149, 'Krishnagiri', 'Mango capital, granite hills, forests'),
('Kallakurichi', 'கள்ளக்குறிச்சி', 3, 'Marutham', 'Mullai', 11.7333, 78.9500, 'Kallakurichi', 'Agricultural, forests nearby'),
('Tenk District', 'தென்காசி மாவட்டம்', 1, 'Kurinji', 'Mullai', 8.9500, 77.3200, 'Tenkasi', 'Western Ghats, waterfalls');

-- VERIFY
SELECT COUNT(*) as total_districts FROM district_land_mapping;
SELECT district_name, primary_land, secondary_land FROM district_land_mapping ORDER BY district_name;
