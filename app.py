import streamlit as st
import psycopg2
import os
from datetime import date
import json
import requests
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

if hasattr(st, 'secrets'):
    for key in ['SUPABASE_HOST', 'SUPABASE_DB', 'SUPABASE_PORT', 'SUPABASE_USER', 'SUPABASE_PASSWORD', 'GEMINI_API_KEY']:
        val = st.secrets.get(key, os.getenv(key, ''))
        if val:
            os.environ[key] = val

st.set_page_config(page_title="Tamil Ayurvedic Food Platform", layout="wide")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def get_db():
    return psycopg2.connect(host=os.getenv('SUPABASE_HOST'), database=os.getenv('SUPABASE_DB'), port=os.getenv('SUPABASE_PORT'), user=os.getenv('SUPABASE_USER'), password=os.getenv('SUPABASE_PASSWORD'))

def ask_gemini(prompt):
    try:
        r = gemini_model.generate_content(prompt)
        t = r.text.strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"):
                t = t[4:]
        return json.loads(t.strip())
    except Exception as e:
        st.warning(f"AI: {e}")
        return None

def get_weather(location="Chennai"):
    try:
        r = requests.get(f"https://wttr.in/{location}?format=j1", timeout=5).json()
        c = r['current_condition'][0]
        return {"temp": c['temp_C'], "humidity": c['humidity'], "desc": c['weatherDesc'][0]['value'], "feels_like": c['FeelsLikeC']}
    except:
        return {"temp": "32", "humidity": "65", "desc": "Partly Cloudy", "feels_like": "35"}

def get_tamil_season():
    month = date.today().month
    seasons = {
        4: ("இளவேனில்", "Ilavenil (Early Summer)", "Pitta"),
        5: ("இளவேனில்", "Ilavenil (Early Summer)", "Pitta"),
        6: ("முதுவேனில்", "Mudhuvenil (Late Summer)", "Pitta/Vata"),
        7: ("முதுவேனில்", "Mudhuvenil (Late Summer)", "Pitta/Vata"),
        8: ("கார்", "Kaar (Monsoon)", "Vata"),
        9: ("கார்", "Kaar (Monsoon)", "Vata"),
        10: ("கூதிர்", "Koothir (Autumn)", "Vata/Kapha"),
        11: ("கூதிர்", "Koothir (Autumn)", "Vata/Kapha"),
        12: ("முன்பனி", "Munpani (Early Winter)", "Kapha"),
        1: ("முன்பனி", "Munpani (Early Winter)", "Kapha"),
        2: ("பின்பனி", "Pinpani (Late Winter)", "Kapha/Pitta"),
        3: ("பின்பனி", "Pinpani (Late Winter)", "Kapha/Pitta"),
    }
    return seasons.get(month, ("கார்", "Kaar", "Vata"))

def get_districts():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT district_id, district_name, district_tamil, primary_land_id, primary_land, secondary_land, weather_location FROM district_land_mapping ORDER BY district_name")
        rows = cur.fetchall(); cur.close(); conn.close()
        return rows
    except:
        return []

def get_land_details(land_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT name_tamil, name_english, land_type, description_english, signature_flower_english, signature_tree_english, staple_food, climate_type FROM ainthinai_lands WHERE land_id = %s", (land_id,))
        row = cur.fetchone(); cur.close(); conn.close()
        return row
    except:
        return None

def get_flora_for_land_and_season(land_id, season_keyword):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""SELECT flora_type, name_tamil, name_english, name_botanical, category, seasonal_availability, medicinal_uses, culinary_uses, dosha_impact 
            FROM land_flora_mapping WHERE land_id = %s AND (seasonal_availability = 'Year-round' OR seasonal_availability ILIKE %s)
            ORDER BY flora_type""", (land_id, f"%{season_keyword}%"))
        rows = cur.fetchall(); cur.close(); conn.close()
        return rows
    except:
        return []

def get_herbs_for_dosha(dosha):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(f"SELECT name_english, name_tamil, plant_part, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs WHERE {dosha.lower()}_effect = 'Decrease' ORDER BY data_confidence_score DESC LIMIT 10")
        rows = cur.fetchall(); cur.close(); conn.close()
        return [{"english": r[0], "tamil": r[1], "part": r[2], "uses": r[3], "diseases": r[4], "preparation": r[5], "season": r[6], "safe_kids": r[7], "min_age": r[8], "score": r[9]} for r in rows]
    except:
        return []

def get_all_herbs():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT name_english, name_tamil, plant_part, primary_uses, vata_effect, pitta_effect, kapha_effect, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs ORDER BY data_confidence_score DESC")
        rows = cur.fetchall(); cur.close(); conn.close()
        return rows
    except:
        return []

def parse_feedback_notes(notes, user_id):
    return ask_gemini(f"""Tamil food analyst. User wrote: "{notes}". Extract dish, vegetables, herbs, spices. Return JSON: {{"dish_name": "Name", "vegetables": ["v1"], "herbs": ["h1"], "spices": ["s1"], "dosha_assessment": "Which dosha", "health_benefits": "Benefits"}}""")

# Map season to search keyword
def season_to_keyword(season_english):
    if "Summer" in season_english:
        return "Summer"
    elif "Monsoon" in season_english:
        return "Monsoon"
    elif "Winter" in season_english:
        return "Winter"
    elif "Autumn" in season_english:
        return "Monsoon"
    else:
        return "Year-round"

# ==================== SIDEBAR ====================
st.sidebar.title("🌿 Tamil Ayurvedic Platform")

# District selector in sidebar
districts = get_districts()
district_names = [d[1] for d in districts]

if 'selected_district' not in st.session_state:
    st.session_state.selected_district = "Theni"

selected = st.sidebar.selectbox("📍 Your District", district_names, index=district_names.index(st.session_state.selected_district) if st.session_state.selected_district in district_names else 0)
st.session_state.selected_district = selected

# Find district details
district_info = None
for d in districts:
    if d[1] == selected:
        district_info = d
        break

# Get weather for selected district
weather_loc = district_info[6] if district_info else "Chennai"
weather = get_weather(weather_loc)

# Get Tamil season
tamil_season = get_tamil_season()

# Get land details
land_details = get_land_details(district_info[3]) if district_info else None

# Show context in sidebar
st.sidebar.markdown("---")
if district_info:
    land_icons = {"Kurinji": "🏔️", "Mullai": "🌳", "Marutham": "🌾", "Neidhal": "🌊", "Palai": "🏜️"}
    icon = land_icons.get(district_info[4], "🌍")
    st.sidebar.markdown(f"{icon} **Land:** {district_info[4]}")
    if district_info[5]:
        st.sidebar.markdown(f"   + {district_info[5]}")

st.sidebar.markdown(f"🌦️ **Season:** {tamil_season[0]}")
st.sidebar.markdown(f"   {tamil_season[1]}")
st.sidebar.markdown(f"   Dosha: {tamil_season[2]}")
st.sidebar.markdown(f"🌤️ **Weather:** {weather['temp']}°C")
st.sidebar.markdown(f"   {weather['desc']}")
st.sidebar.markdown(f"   Humidity: {weather['humidity']}%")
st.sidebar.markdown("---")
st.sidebar.markdown("🆓 100% FREE Platform")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", ["👨‍🍳 Adult", "👶 Kids", "🏔️ Ainthinai", "🌦️ Seasons", "🌿 Herbs", "🔧 Admin", "📊 Feedback"])

# ==================== ADULT PAGE ====================
if page == "👨‍🍳 Adult":
    st.title("🌿 Daily Body Condition Check")

    # Context bar
    if district_info and land_details:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📍 District", selected)
        icon = land_icons.get(district_info[4], "🌍")
        col2.metric(f"{icon} Land", district_info[4])
        col3.metric("🌦️ Season", tamil_season[1].split("(")[0].strip())
        col4.metric("🌤️ Weather", f"{weather['temp']}°C")

        # Show local flora
        season_kw = season_to_keyword(tamil_season[1])
        local_flora = get_flora_for_land_and_season(district_info[3], season_kw)
        if local_flora:
            flora_text = ", ".join([f"{f[2]}" for f in local_flora[:8]])
            st.info(f"🌿 **Locally available now in {district_info[4]} land during {tamil_season[1]}:** {flora_text}")

    st.markdown("---")

    with st.form("body"):
        col1, col2 = st.columns(2)
        with col1:
            cold = st.slider("Cold/Runny Nose", 0, 5, 0)
            cough = st.selectbox("Cough Type", ["None", "Dry", "Wet"])
            cough_sev = st.slider("Cough Severity", 0, 5, 0)
            pain = st.multiselect("Pain", ["Head", "Neck", "Joints", "Abdomen", "Chest", "Back", "None"])
            pain_sev = st.slider("Pain Severity", 0, 5, 0)
            pimples = st.number_input("Pimples", 0, 100, 0)
        with col2:
            sweating = st.selectbox("Sweating", ["Normal", "Excessive"])
            sputum = st.selectbox("Sputum", ["Clear", "Yellow", "Green"])
            urine = st.selectbox("Urine", ["Pale", "Amber", "Dark"])
            energy = st.slider("Energy", 1, 10, 5)
            digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        user_id = st.text_input("ID", "user_001")

        if st.form_submit_button("🤖 Analyze with Land + Season + Weather", type="primary"):
            try:
                conn = get_db(); cur = conn.cursor(); pain_locs = ",".join(pain) if pain else "None"
                cur.execute("INSERT INTO body_condition_log (user_id, log_date, cold_intensity, cough_type, cough_severity, pain_locations, pain_severity, pimple_count, sweating_level, sputum_color, urine_color, energy_level, digestion_quality, weather_condition) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id, date.today(), cold, cough, cough_sev, pain_locs, pain_sev, pimples, sweating, sputum, urine, energy, digestion, f"{selected} {weather['temp']}C {weather['desc']}"))
                conn.commit(); cur.close(); conn.close()
                st.success("✅ Logged!")

                body = {'cold': cold, 'cough': cough, 'cough_severity': cough_sev, 'pain_locations': pain_locs, 'pain_severity': pain_sev, 'pimple_count': pimples, 'energy': energy, 'digestion': digestion, 'sweating': sweating, 'sputum': sputum, 'urine': urine}

                with st.spinner("🤖 Classifying dosha with land + season + weather..."):
                    dosha = ask_gemini(f"""Tamil Siddha expert. Classify dosha considering body, land type, season, and weather.
Body: {json.dumps(body)}
District: {selected}, Ainthinai Land: {district_info[4] if district_info else 'Unknown'}
Tamil Season: {tamil_season[1]} (Dominant dosha: {tamil_season[2]})
Weather: {weather['temp']}C, Humidity {weather['humidity']}%, {weather['desc']}

Return JSON: {{"primary_dosha": "Vata/Pitta/Kapha", "dosha_percent": 75, "secondary_dosha": "X", "secondary_percent": 25, "confidence": 0.9, "summary": "Include land and season impact", "weather_impact": "Weather effect", "season_impact": "Tamil season effect on dosha", "land_impact": "How the Ainthinai land affects health"}}""")

                    if dosha:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Primary Dosha", f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        col2.metric("Secondary", dosha.get('secondary_dosha', 'None'))
                        conf = dosha.get('confidence', 0.8)
                        if isinstance(conf, str):
                            conf = float(conf)
                        col3.metric("Confidence", f"{conf:.0%}")

                        st.info(f"📋 {dosha['summary']}")
                        st.info(f"🌤️ **Weather:** {dosha.get('weather_impact', '')}")
                        st.info(f"🌦️ **Season:** {dosha.get('season_impact', '')}")
                        st.info(f"🏔️ **Land:** {dosha.get('land_impact', '')}")

                        # Get herbs for dosha
                        herbs = get_herbs_for_dosha(dosha['primary_dosha'])

                        # Get local flora
                        season_kw = season_to_keyword(tamil_season[1])
                        local_flora = get_flora_for_land_and_season(district_info[3], season_kw) if district_info else []

                        if herbs:
                            st.markdown("---")
                            st.subheader(f"🌿 Dosha-Matching Herbs ({len(herbs)} found)")
                            for h in herbs[:6]:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']}")

                        if local_flora:
                            st.markdown("---")
                            st.subheader(f"🌾 Locally Available in {district_info[4]} Land Now")
                            for f in local_flora:
                                type_icon = {"Herb": "🌱", "Flower": "🌸", "Fruit": "🍎", "Tree": "🌳", "Grain": "🌾"}.get(f[0], "🌿")
                                st.write(f"{type_icon} **{f[2]}** ({f[1]}) - {f[6]} | Dosha: {f[8]}")

                        # Build comprehensive Gemini prompt
                        herbs_text = "\n".join([f"- {h['english']} ({h['tamil']}): {h['uses']}" for h in herbs[:8]])
                        flora_text = "\n".join([f"- {f[2]} ({f[1]}): {f[6]} | Culinary: {f[7]}" for f in local_flora[:8]])

                        with st.spinner("🤖 Generating hyper-local recipes..."):
                            recipes = ask_gemini(f"""Tamil Ayurvedic chef. Generate recipes using LOCALLY AVAILABLE ingredients from the user's land and season.

User Context:
- Dosha: {dosha['primary_dosha']} ({dosha['dosha_percent']}%)
- District: {selected} ({district_info[4]} land)
- Tamil Season: {tamil_season[1]} (Dominant: {tamil_season[2]})
- Weather: {weather['temp']}C, {weather['desc']}, Humidity {weather['humidity']}%
- Energy: {energy}/10

Dosha-Matching Herbs:
{herbs_text}

LOCALLY Available Flora in {district_info[4]} during {tamil_season[1]}:
{flora_text}

IMPORTANT: Use ONLY locally available flora and seasonal herbs. Explain why each ingredient is chosen based on land type and season.

Return JSON: {{"breakfast": {{"name": "Recipe", "ingredients": "List", "prep_time": "15min", "medicinal_herbs": "Herbs from local flora", "herb_preparation": "How to prepare", "why_local": "Why this ingredient grows here", "why_seasonal": "Why its good this season", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "lunch": {{"name": "Recipe", "ingredients": "List", "prep_time": "20min", "medicinal_herbs": "Local herbs", "herb_preparation": "Prep", "why_local": "Local reason", "why_seasonal": "Season reason", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "dinner": {{"name": "Recipe", "ingredients": "List", "prep_time": "15min", "medicinal_herbs": "Local herbs", "herb_preparation": "Prep", "why_local": "Local reason", "why_seasonal": "Season reason", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "wellness_notes": "Overall benefits considering land, season, weather"}}""")

                            if recipes:
                                for meal, micon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                                    st.markdown("---")
                                    st.subheader(f"{micon} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 **Ingredients:** {recipes[meal]['ingredients']}")
                                    st.write(f"🌿 **Herbs:** {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 **Herb Prep:** {recipes[meal].get('herb_preparation', '')}")
                                    st.write(f"📍 **Why Local:** {recipes[meal].get('why_local', '')}")
                                    st.write(f"🌦️ **Why Seasonal:** {recipes[meal].get('why_seasonal', '')}")
                                    st.write(f"💪 **Benefits:** {recipes[meal]['nutritional_benefits']}")
                                st.markdown("---")
                                st.info(f"💡 {recipes.get('wellness_notes', '')}")
            except Exception as e:
                st.error(str(e))

# ==================== KIDS PAGE ====================
elif page == "👶 Kids":
    st.title("👶 Kids Nutrition")
    if district_info:
        st.markdown(f"📍 **{selected}** ({district_info[4]} land) | 🌦️ {tamil_season[1]} | 🌤️ {weather['temp']}°C")
    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("Age", ["2-3", "4-6", "7-10", "11+"])
    with col2:
        kid_dosha = st.selectbox("Dosha", ["Not Sure", "Vata", "Pitta", "Kapha"])
    all_herbs = get_all_herbs()
    herbs = [{"english": r[0], "tamil": r[1], "uses": r[3], "preparation": r[8] if len(r)>8 else "", "safe_kids": r[10] if len(r)>10 else True, "min_age": r[11] if len(r)>11 else 2} for r in all_herbs]
    kid_herbs = [h for h in herbs if h.get('safe_kids', True) and h.get('min_age', 2) <= int(age.split("-")[0])]

    season_kw = season_to_keyword(tamil_season[1])
    local_flora = get_flora_for_land_and_season(district_info[3], season_kw) if district_info else []
    flora_text = "\n".join([f"- {f[2]}: {f[6]} | Culinary: {f[7]}" for f in local_flora[:6]])

    if st.button("🤖 Get Local Seasonal Meal Plan", type="primary"):
        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in kid_herbs[:8]])
        with st.spinner("Creating..."):
            kids = ask_gemini(f"""Tamil pediatric nutritionist. Child Age {age}yr, Dosha {kid_dosha}.
District: {selected} ({district_info[4] if district_info else 'Unknown'} land), Season: {tamil_season[1]}
Local flora: {flora_text}
Kid-safe herbs: {herbs_text}
Use LOCAL and SEASONAL ingredients. Return JSON: {{"breakfast": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_local": "Why local", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "15min"}}, "lunch": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_local": "X", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "20min"}}, "dinner": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_local": "X", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "15min"}}, "parental_guidance": "X"}}""")
            if kids:
                for meal, micon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                    st.markdown("---"); st.subheader(f"{micon} {meal.title()}")
                    st.markdown(f"**{kids[meal]['name']}**")
                    st.write(f"📝 {kids[meal]['ingredients']}"); st.write(f"💪 {kids[meal]['health_benefits']}")
                    st.write(f"🌿 {kids[meal]['medicinal_herbs']}"); st.write(f"📍 {kids[meal].get('why_local', '')}")
                    st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance', '')}")

# ==================== AINTHINAI PAGE ====================
elif page == "🏔️ Ainthinai":
    st.title("🏔️ ஐந்திணை - Five Lands of Tamil Nadu")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM ainthinai_lands ORDER BY land_id")
        lands = cur.fetchall()
        land_icons_list = {"Kurinji": "🏔️", "Mullai": "🌳", "Marutham": "🌾", "Neidhal": "🌊", "Palai": "🏜️"}
        tabs = st.tabs([f"{land_icons_list.get(l[2], '🌍')} {l[1]} ({l[2]})" for l in lands])
        for i, land in enumerate(lands):
            with tabs[i]:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f"{land[1]} - {land[2]}")
                    st.write(f"**Description:** {land[5]}"); st.write(f"🙏 **Deity:** {land[6]} ({land[7]})")
                    st.write(f"🌸 **Flower:** {land[8]} ({land[9]})"); st.write(f"🌳 **Tree:** {land[10]} ({land[11]})")
                with col2:
                    st.write(f"👷 **Occupation:** {land[12]}"); st.write(f"👥 **People:** {land[13]}")
                    st.write(f"🍚 **Food:** {land[14]}"); st.write(f"💕 **Emotion:** {land[16]}")
                    st.write(f"📍 **Districts:** {land[18]}")
                st.markdown("---")
                st.subheader(f"🌿 Flora of {land[2]}")
                cur.execute("SELECT flora_type, name_tamil, name_english, name_botanical, medicinal_uses, culinary_uses, dosha_impact FROM land_flora_mapping WHERE land_id = %s", (land[0],))
                for f in cur.fetchall():
                    tipo = {"Herb": "🌱", "Flower": "🌸", "Fruit": "🍎", "Tree": "🌳", "Grain": "🌾"}.get(f[0], "🌿")
                    st.write(f"{tipo} **{f[2]}** ({f[1]}) | {f[4]} | Culinary: {f[5]} | Dosha: {f[6]}")
                # Show districts in this land
                st.markdown("---"); st.subheader(f"📍 Districts in {land[2]}")
                cur.execute("SELECT district_name, district_tamil FROM district_land_mapping WHERE primary_land = %s ORDER BY district_name", (land[2],))
                for d in cur.fetchall():
                    st.write(f"📍 {d[0]} ({d[1]})")
        cur.close(); conn.close()
    except Exception as e:
        st.error(str(e))

# ==================== SEASONS PAGE ====================
elif page == "🌦️ Seasons":
    st.title("🌦️ Tamil Seasons (பெரும்பொழுது)")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM tamil_seasons ORDER BY season_id")
        seasons = cur.fetchall()
        icons = ["☀️", "🔥", "🌧️", "🍂", "❄️", "🌸"]
        current_tamil = tamil_season[0]
        for i, s in enumerate(seasons):
            ic = icons[i] if i < len(icons) else "🌤️"
            is_current = current_tamil == s[1]
            label = f"{ic} {s[1]} - {s[2]} ({s[4]})" + (" ← CURRENT" if is_current else "")
            with st.expander(label, expanded=is_current):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Tamil Months:** {s[3]}"); st.write(f"**Duration:** {s[5]}")
                    st.write(f"**Weather:** {s[6]}"); st.write(f"**Dosha:** {s[7]}")
                    st.write(f"**Food:** {s[8]}")
                with col2:
                    st.write(f"🌿 **Herbs:** {s[9]}"); st.write(f"🍎 **Fruits:** {s[10]}")
                    st.write(f"🌸 **Flowers:** {s[11]}"); st.write(f"🌾 **Farming:** {s[12]}")
        cur.close(); conn.close()
        st.markdown("---")
        st.success(f"📅 **Today:** {tamil_season[0]} - {tamil_season[1]} | Dominant Dosha: {tamil_season[2]}")
    except Exception as e:
        st.error(str(e))

# ==================== HERBS PAGE ====================
elif page == "🌿 Herbs":
    st.title("🌿 Medicinal Herbs")
    search = st.text_input("Search", "")
    df = st.selectbox("Dosha Filter", ["All", "Vata", "Pitta", "Kapha"])
    for r in get_all_herbs():
        e, t, p, u = r[0] or "", r[1] or "", r[2] or "", r[3] or ""
        v, pi, k = r[4] or "", r[5] or "", r[6] or ""
        if search and search.lower() not in e.lower() and search.lower() not in t.lower():
            continue
        if df != "All" and {"Vata": v, "Pitta": pi, "Kapha": k}[df] != "Decrease":
            continue
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### 🌱 {e}")
            st.write(f"**{t}** | {p} | Score: {r[12] or 7}/10")
        with col2:
            st.write(f"{u} | V:{v} P:{pi} K:{k}")
        st.markdown("---")

# ==================== ADMIN PAGE ====================
elif page == "🔧 Admin":
    st.title("🔧 Admin")
    tab = st.radio("Add:", ["🌿 Herb", "🍽️ Dish"])
    if tab == "🌿 Herb":
        with st.form("herb"):
            col1, col2 = st.columns(2)
            with col1:
                ht = st.text_input("Tamil *"); he = st.text_input("English *"); hb = st.text_input("Botanical")
                hp = st.selectbox("Part", ["Leaves", "Root", "Seed", "Flower", "Bark", "Fruit", "Whole plant", "Rhizome"])
                hu = st.text_area("Uses *"); hd = st.text_area("Diseases")
            with col2:
                hv = st.selectbox("Vata", ["Decrease", "Increase", "Neutral"]); hpi = st.selectbox("Pitta", ["Decrease", "Increase", "Neutral"]); hk = st.selectbox("Kapha", ["Decrease", "Increase", "Neutral"])
                hpr = st.text_input("Preparation"); hs = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
                hkid = st.checkbox("Safe Kids", True); hage = st.number_input("Min Age", 1, 18, 3); hsc = st.slider("Score", 1, 10, 7)
            if st.form_submit_button("✅ Add", type="primary") and ht and he and hu:
                try:
                    conn = get_db(); cur = conn.cursor()
                    cur.execute("INSERT INTO medicinal_herbs (name_tamil, name_english, name_botanical, plant_part, vata_effect, pitta_effect, kapha_effect, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (ht, he, hb, hp, hv, hpi, hk, hu, hd, hpr, hs, hkid, hage, hsc))
                    conn.commit(); cur.close(); conn.close(); st.success(f"✅ '{he}' added!"); st.balloons()
                except Exception as e:
                    st.error(str(e))
    else:
        with st.form("dish"):
            dn = st.text_input("Name *"); dd = st.selectbox("Dosha", ["Vata", "Pitta", "Kapha", "Neutral"]); ds = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
            di = st.text_area("Instructions")
            if st.form_submit_button("✅ Add", type="primary") and dn:
                try:
                    conn = get_db(); cur = conn.cursor()
                    cur.execute("INSERT INTO recipes (recipe_name, primary_ingredient_id, serves, prep_time_min, dosha_suitability, seasonal_best, instructions) VALUES (%s,1,4,20,%s,%s,%s)", (dn, dd, ds, di))
                    conn.commit(); cur.close(); conn.close(); st.success(f"✅ '{dn}' added!"); st.balloons()
                except Exception as e:
                    st.error(str(e))
    st.markdown("---")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicinal_herbs"); h = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recipes"); r = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM body_condition_log"); l = cur.fetchone()[0]
        cur.close(); conn.close()
        col1, col2, col3 = st.columns(3)
        col1.metric("🌿 Herbs", h); col2.metric("🍽️ Dishes", r); col3.metric("📋 Logs", l)
    except:
        pass

# ==================== FEEDBACK PAGE ====================
elif page == "📊 Feedback":
    st.title("📊 Smart Feedback")
    with st.form("fb"):
        col1, col2, col3 = st.columns(3)
        with col1:
            br = st.slider("Breakfast", 1, 5, 3, key="br")
        with col2:
            lr = st.slider("Lunch", 1, 5, 3, key="lr")
        with col3:
            dr = st.slider("Dinner", 1, 5, 3, key="dr")
        energy = st.slider("Energy", 1, 10, 5)
        digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        st.markdown("---")
        st.subheader("📝 What Did You Actually Eat?")
        notes = st.text_area("AI will extract dishes, herbs, vegetables for learning", "")
        user_id = st.text_input("ID", "user_001")
        if st.form_submit_button("Submit & Parse", type="primary"):
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO user_feedback (user_id, recommendation_date, feedback_date, breakfast_rating, lunch_rating, dinner_rating, energy_level_next_day, digestion_quality) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id, date.today(), date.today(), br, lr, dr, energy, digestion))
                conn.commit(); st.success("✅ Saved!")
                if notes.strip():
                    with st.spinner("🤖 Parsing..."):
                        parsed = parse_feedback_notes(notes, user_id)
                        if parsed:
                            st.write(f"🍽️ **Dish:** {parsed.get('dish_name', '')}"); st.write(f"🥬 **Vegetables:** {', '.join(parsed.get('vegetables', []))}")
                            st.write(f"🌿 **Herbs:** {', '.join(parsed.get('herbs', []))}"); st.write(f"⚖️ **Dosha:** {parsed.get('dosha_assessment', '')}")
                            st.write(f"💪 **Benefits:** {parsed.get('health_benefits', '')}")
                            try:
                                cur.execute("INSERT INTO feedback_parsed_items (user_id, original_note, parsed_dish_name, parsed_herbs, parsed_vegetables, dosha_assessment) VALUES (%s,%s,%s,%s,%s,%s)",
                                    (user_id, notes, parsed.get('dish_name', ''), json.dumps(parsed.get('herbs', [])), json.dumps(parsed.get('vegetables', [])), parsed.get('dosha_assessment', '')))
                                conn.commit(); st.success("✅ Parsed & saved for learning!")
                            except:
                                pass
                cur.close(); conn.close()
            except Exception as e:
                st.error(str(e))
