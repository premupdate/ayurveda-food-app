import streamlit as st
import psycopg2
import os
from datetime import date
import json
import requests
import google.generativeai as genai

# Support both local .env and Streamlit Cloud secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

if hasattr(st, 'secrets'):
    for key in ['SUPABASE_URL', 'GEMINI_API_KEY']:
        val = st.secrets.get(key, os.getenv(key, ''))
        if val:
            os.environ[key] = val

st.set_page_config(page_title="Tamil Ayurvedic Food + Herbs", layout="wide")

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def get_db_connection():
    return psycopg2.connect(os.getenv('SUPABASE_URL'))

def get_chennai_weather():
    try:
        url = "https://wttr.in/Chennai?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        c = data['current_condition'][0]
        return {"temp": c['temp_C'], "humidity": c['humidity'], "desc": c['weatherDesc'][0]['value'], "feels_like": c['FeelsLikeC'], "wind": c['windspeedKmph']}
    except:
        return {"temp": "32", "humidity": "65", "desc": "Partly Cloudy", "feels_like": "35", "wind": "15"}

def ask_gemini(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        st.warning(f"AI Error: {e}")
        return None

def get_herbs_for_dosha(dosha_type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        col = dosha_type.lower() + "_effect"
        cursor.execute(f"SELECT name_english, name_tamil, plant_part, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs WHERE {col} = 'Decrease' ORDER BY data_confidence_score DESC LIMIT 10")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{"english": r[0], "tamil": r[1], "part": r[2], "uses": r[3], "diseases": r[4], "preparation": r[5], "season": r[6], "safe_kids": r[7], "min_age": r[8], "score": r[9]} for r in rows]
    except:
        return []

def get_all_herbs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name_english, name_tamil, plant_part, primary_uses, vata_effect, pitta_effect, kapha_effect, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs ORDER BY data_confidence_score DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except:
        return []

def classify_dosha(body, weather):
    prompt = f"""You are a Tamil Nadu Siddha medicine expert.
Body: Cold {body['cold']}/5, Cough {body['cough']} severity {body['cough_severity']}/5, Pain {body['pain_locations']} severity {body['pain_severity']}/5, Pimples {body['pimple_count']}, Sweating {body['sweating']}, Sputum {body['sputum']}, Urine {body['urine']}, Energy {body['energy']}/10, Digestion {body['digestion']}
Weather: {weather['temp']}C, Humidity {weather['humidity']}%, {weather['desc']}

Return ONLY valid JSON, no markdown:
{{"primary_dosha": "Vata or Pitta or Kapha", "dosha_percent": 75, "secondary_dosha": "Pitta", "secondary_percent": 25, "confidence": 0.92, "summary": "Brief summary", "weather_impact": "Weather effect on dosha"}}"""
    return ask_gemini(prompt)

def generate_recipes(dosha, season, energy, herbs, weather):
    herbs_text = "\n".join([f"- {h['english']} ({h['tamil']}): {h['uses']}" for h in herbs[:8]])
    prompt = f"""Tamil Ayurvedic chef. Dosha: {dosha['primary_dosha']} {dosha['dosha_percent']}%, Season: {season}, Energy: {energy}/10, Weather: {weather['temp']}C {weather['desc']}
Herbs from database:
{herbs_text}

Return ONLY valid JSON:
{{"breakfast": {{"name": "Recipe", "ingredients": "List", "prep_time": "15 min", "medicinal_herbs": "Herbs to add", "herb_preparation": "How to prepare", "why_this_dish": "Why it helps", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "lunch": {{"name": "Recipe", "ingredients": "List", "prep_time": "20 min", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_this_dish": "Why", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "dinner": {{"name": "Recipe", "ingredients": "List", "prep_time": "15 min", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_this_dish": "Why", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "shopping_list": [{{"item": "Item", "quantity": "100", "unit": "g", "price_estimate": "10"}}], "total_cost": "140", "wellness_notes": "Benefits"}}"""
    return ask_gemini(prompt)

def generate_kids_recipes(age, dosha, herbs):
    kid_herbs = [h for h in herbs if h.get('safe_kids', True) and h.get('min_age', 2) <= int(age.split("-")[0])]
    herbs_text = "\n".join([f"- {h['english']} ({h['tamil']}): {h['uses']} | Age {h['min_age']}+" for h in kid_herbs[:8]])
    prompt = f"""Tamil pediatric nutritionist. Child: Age {age}yr, Dosha: {dosha}
Kid-safe herbs:
{herbs_text}

Return ONLY valid JSON:
{{"breakfast": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_better_than_junk": "Why better", "taste_profile": "Taste", "prep_time": "15 min", "portion_size": "Amount"}}, "lunch": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_better_than_junk": "Why", "taste_profile": "Taste", "prep_time": "20 min", "portion_size": "Amount"}}, "dinner": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_better_than_junk": "Why", "taste_profile": "Taste", "prep_time": "15 min", "portion_size": "Amount"}}, "parental_guidance": "Tips", "nutritional_summary": "Benefits"}}"""
    return ask_gemini(prompt)

# Sidebar
st.sidebar.title("🌿 Tamil Ayurvedic Food Platform")
st.sidebar.markdown("AI + Siddha + Weather + Herbs")
st.sidebar.markdown("🆓 **100% FREE Platform**")
st.sidebar.markdown("---")
weather = get_chennai_weather()
st.sidebar.markdown(f"🌤️ **Chennai:** {weather['temp']}°C")
st.sidebar.markdown(f"💧 Humidity: {weather['humidity']}%")
st.sidebar.markdown(f"🌬️ {weather['desc']}")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["👨‍🍳 Adult", "👶 Kids", "🌿 Herbs", "🔧 Admin", "📊 Feedback"])

if page == "👨‍🍳 Adult":
    st.title("🌿 Daily Body Condition Check")
    st.markdown(f"🌤️ **Chennai Weather:** {weather['temp']}°C, {weather['desc']}")
    with st.form("body_form"):
        col1, col2 = st.columns(2)
        with col1:
            cold = st.slider("Cold/Runny Nose", 0, 5, 0)
            cough = st.selectbox("Cough Type", ["None", "Dry", "Wet"])
            cough_severity = st.slider("Cough Severity", 0, 5, 0)
            pain_locations = st.multiselect("Pain", ["Head", "Neck", "Shoulders", "Joints", "Abdomen", "Chest", "Back", "None"])
            pain_severity = st.slider("Pain Severity", 0, 5, 0)
            pimple_count = st.number_input("Pimple Count", 0, 100, 0)
        with col2:
            sweating = st.selectbox("Sweating", ["Normal", "Excessive"])
            sputum = st.selectbox("Sputum", ["Clear", "Yellow", "Green"])
            urine = st.selectbox("Urine", ["Pale", "Amber", "Dark"])
            energy = st.slider("Energy Level", 1, 10, 5)
            digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        user_id = st.text_input("Your ID", "user_001")
        submitted = st.form_submit_button("🤖 Analyze with AI + Weather", type="primary")
        if submitted:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                pain_locs = ",".join(pain_locations) if pain_locations else "None"
                cursor.execute("INSERT INTO body_condition_log (user_id, log_date, cold_intensity, cough_type, cough_severity, pain_locations, pain_severity, pimple_count, sweating_level, sputum_color, urine_color, energy_level, digestion_quality, weather_condition) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, date.today(), cold, cough, cough_severity, pain_locs, pain_severity, pimple_count, sweating, sputum, urine, energy, digestion, f"{weather['temp']}C {weather['desc']}"))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("✅ Logged!")

                with st.spinner("🤖 Gemini analyzing..."):
                    body = {'cold': cold, 'cough': cough, 'cough_severity': cough_severity, 'pain_locations': pain_locs, 'pain_severity': pain_severity, 'pimple_count': pimple_count, 'energy': energy, 'digestion': digestion, 'sweating': sweating, 'sputum': sputum, 'urine': urine}
                    dosha = classify_dosha(body, weather)
                    if dosha:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Primary Dosha", f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        with col2:
                            st.metric("Secondary", f"{dosha.get('secondary_dosha', 'None')}")
                        st.info(f"📋 {dosha['summary']}")
                        st.info(f"🌤️ {dosha.get('weather_impact', '')}")

                        herbs = get_herbs_for_dosha(dosha['primary_dosha'])
                        if herbs:
                            st.markdown("---")
                            st.subheader(f"🌿 {len(herbs)} Matching Herbs")
                            for h in herbs:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']} | Score: {h['score']}/10")

                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT season FROM seasonal_calendar WHERE month_num = %s", (date.today().month,))
                            sr = cursor.fetchone()
                            cursor.close()
                            conn.close()
                            season = sr[0] if sr else "Monsoon"
                        except:
                            season = "Monsoon"

                        with st.spinner("🤖 Generating recipes..."):
                            recipes = generate_recipes(dosha, season, energy, herbs, weather)
                            if recipes:
                                for meal, icon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                                    st.markdown("---")
                                    st.subheader(f"{icon} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 {recipes[meal]['ingredients']}")
                                    st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 {recipes[meal].get('herb_preparation', '')}")
                                    st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                                    st.write(f"⏱️ {recipes[meal]['prep_time']}")
                                st.markdown("---")
                                if recipes.get('shopping_list'):
                                    st.subheader("🛒 Shopping List")
                                    for item in recipes['shopping_list']:
                                        st.write(f"• {item.get('item','')} - {item.get('quantity','')} {item.get('unit','')} (₹{item.get('price_estimate','')})")
                                st.metric("Total Cost", f"₹{recipes.get('total_cost', '0')}")
                                st.info(f"💡 {recipes.get('wellness_notes', '')}")
            except Exception as e:
                st.error(str(e))

elif page == "👶 Kids":
    st.title("👶 Kids Nutrition with Herbs")
    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("Age", ["2-3 years", "4-6 years", "7-10 years", "11+ years"])
        age_val = {"2-3 years": "2-3", "4-6 years": "4-6", "7-10 years": "7-10", "11+ years": "11+"}[age]
    with col2:
        dosha = st.selectbox("Dosha", ["Not Sure", "Vata", "Pitta", "Kapha"])
    all_herbs = get_all_herbs()
    herbs = [{"english": r[0], "tamil": r[1], "part": r[2], "uses": r[3], "preparation": r[8] if len(r)>8 else "", "season": r[9] if len(r)>9 else "", "safe_kids": r[10] if len(r)>10 else True, "min_age": r[11] if len(r)>11 else 2, "score": r[12] if len(r)>12 else 7} for r in all_herbs]
    if st.button("🤖 Get Meal Plan", type="primary"):
        with st.spinner("Creating..."):
            kids = generate_kids_recipes(age_val, dosha, herbs)
            if kids:
                st.success("✅ Created!")
                for meal, icon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                    st.markdown("---")
                    st.subheader(f"{icon} {meal.title()}")
                    st.markdown(f"**{kids[meal]['name']}**")
                    st.write(f"📝 {kids[meal]['ingredients']}")
                    st.write(f"💪 {kids[meal]['health_benefits']}")
                    st.write(f"🌿 {kids[meal]['medicinal_herbs']}")
                    st.write(f"🧪 {kids[meal].get('herb_preparation', '')}")
                    st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance', '')}")

elif page == "🌿 Herbs":
    st.title("🌿 Medicinal Herbs Database")
    search = st.text_input("Search herb", "")
    dosha_filter = st.selectbox("Filter by Dosha", ["All", "Vata", "Pitta", "Kapha"])
    all_herbs = get_all_herbs()
    st.write(f"**Total: {len(all_herbs)} herbs**")
    for row in all_herbs:
        eng, tam, part, uses = row[0] or "", row[1] or "", row[2] or "", row[3] or ""
        vata, pitta, kapha = row[4] or "", row[5] or "", row[6] or ""
        diseases, prep, season = row[7] or "", row[8] or "", row[9] or ""
        safe, min_age, score = row[10], row[11] or 2, row[12] or 7
        if search and search.lower() not in eng.lower() and search.lower() not in tam.lower():
            continue
        if dosha_filter != "All":
            col_val = {"Vata": vata, "Pitta": pitta, "Kapha": kapha}[dosha_filter]
            if col_val != "Decrease":
                continue
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### 🌱 {eng}")
            st.write(f"**Tamil:** {tam} | **Part:** {part} | **Score:** {score}/10")
        with col2:
            st.write(f"**Uses:** {uses}")
            st.write(f"**Diseases:** {diseases}")
            st.write(f"**Dosha:** V:{vata} | P:{pitta} | K:{kapha}")
        st.markdown("---")

elif page == "🔧 Admin":
    st.title("🔧 Admin - Add Herbs & Dishes")
    admin_tab = st.radio("What to add?", ["🌿 New Herb", "🍽️ New Dish"])
    if admin_tab == "🌿 New Herb":
        st.subheader("🌿 Add New Medicinal Herb")
        with st.form("add_herb"):
            col1, col2 = st.columns(2)
            with col1:
                h_tamil = st.text_input("Tamil Name *")
                h_english = st.text_input("English Name *")
                h_botanical = st.text_input("Botanical Name")
                h_part = st.selectbox("Plant Part", ["Leaves", "Root", "Seed", "Flower", "Bark", "Fruit", "Whole plant", "Rhizome", "Stem", "Bulb", "Oil", "Grain"])
                h_uses = st.text_area("Primary Uses *")
                h_diseases = st.text_area("Diseases Treated")
            with col2:
                h_vata = st.selectbox("Vata Effect", ["Decrease", "Increase", "Neutral"])
                h_pitta = st.selectbox("Pitta Effect", ["Decrease", "Increase", "Neutral"])
                h_kapha = st.selectbox("Kapha Effect", ["Decrease", "Increase", "Neutral"])
                h_prep = st.text_input("Preparation Methods")
                h_season = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
                h_kids = st.checkbox("Safe for Kids", True)
                h_age = st.number_input("Minimum Age", 1, 18, 3)
                h_score = st.slider("Confidence Score", 1, 10, 7)
            if st.form_submit_button("✅ Add Herb", type="primary"):
                if h_tamil and h_english and h_uses:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO medicinal_herbs (name_tamil, name_english, name_botanical, plant_part, vata_effect, pitta_effect, kapha_effect, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (h_tamil, h_english, h_botanical, h_part, h_vata, h_pitta, h_kapha, h_uses, h_diseases, h_prep, h_season, h_kids, h_age, h_score))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"✅ '{h_english}' added!")
                        st.balloons()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Fill Tamil Name, English Name, Uses")

    elif admin_tab == "🍽️ New Dish":
        st.subheader("🍽️ Add New Tamil Dish")
        with st.form("add_dish"):
            col1, col2 = st.columns(2)
            with col1:
                d_name = st.text_input("Dish Name *")
                d_serves = st.number_input("Serves", 1, 10, 4)
                d_prep = st.number_input("Prep Time (min)", 5, 120, 20)
            with col2:
                d_dosha = st.selectbox("Dosha", ["Vata", "Pitta", "Kapha", "Neutral", "Vata/Pitta", "Vata/Kapha"])
                d_season = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
                d_method = st.text_input("Cooking Method")
            d_instructions = st.text_area("Instructions")
            if st.form_submit_button("✅ Add Dish", type="primary"):
                if d_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO recipes (recipe_name, primary_ingredient_id, serves, prep_time_min, dosha_suitability, seasonal_best, cooking_method, instructions) VALUES (%s,1,%s,%s,%s,%s,%s,%s)",
                            (d_name, d_serves, d_prep, d_dosha, d_season, d_method, d_instructions))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"✅ '{d_name}' added!")
                        st.balloons()
                    except Exception as e:
                        st.error(str(e))

    st.markdown("---")
    st.subheader("📊 Database Stats")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medicinal_herbs")
        herbs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM recipes")
        recipes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM body_condition_log")
        logs = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        col1, col2, col3 = st.columns(3)
        col1.metric("🌿 Herbs", herbs)
        col2.metric("🍽️ Dishes", recipes)
        col3.metric("📋 Logs", logs)
    except:
        st.info("Connect to Supabase to see stats")

elif page == "📊 Feedback":
    st.title("📊 Feedback")
    with st.form("feedback"):
        col1, col2, col3 = st.columns(3)
        with col1:
            br = st.slider("Breakfast", 1, 5, 3, key="br")
        with col2:
            lr = st.slider("Lunch", 1, 5, 3, key="lr")
        with col3:
            dr = st.slider("Dinner", 1, 5, 3, key="dr")
        energy = st.slider("Energy Today", 1, 10, 5)
        digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        user_id = st.text_input("ID", "user_001")
        if st.form_submit_button("Submit", type="primary"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user_feedback (user_id, recommendation_date, feedback_date, breakfast_rating, lunch_rating, dinner_rating, energy_level_next_day, digestion_quality) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, date.today(), date.today(), br, lr, dr, energy, digestion))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("✅ Saved!")
            except Exception as e:
                st.error(str(e))
