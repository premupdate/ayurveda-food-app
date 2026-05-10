import streamlit as st
import snowflake.connector
import os
from dotenv import load_dotenv
import json
import requests
from anthropic import Anthropic

load_dotenv()

# Support both local .env and Streamlit Cloud secrets
if hasattr(st, 'secrets'):
    for key in ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD', 'SNOWFLAKE_WAREHOUSE', 'SNOWFLAKE_DATABASE', 'SNOWFLAKE_SCHEMA', 'ANTHROPIC_API_KEY']:
        val = st.secrets.get(key, os.getenv(key, ''))
        if val:
            os.environ[key] = val

st.set_page_config(page_title="Tamil Ayurvedic Food + Herbs + Weather", layout="wide")

client = Anthropic()

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )

def get_chennai_weather():
    """Get live Chennai weather - no API key needed"""
    try:
        url = "https://wttr.in/Chennai?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data['current_condition'][0]
        return {
            "temp": current['temp_C'],
            "humidity": current['humidity'],
            "desc": current['weatherDesc'][0]['value'],
            "feels_like": current['FeelsLikeC'],
            "wind": current['windspeedKmph']
        }
    except:
        return {"temp": "32", "humidity": "65", "desc": "Partly Cloudy", "feels_like": "35", "wind": "15"}

def get_herbs_for_dosha(dosha_type):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        column = dosha_type.upper() + "_EFFECT"
        cursor.execute(f"""
            SELECT NAME_ENGLISH, NAME_TAMIL, PLANT_PART, PRIMARY_USES, 
                   DISEASES_TREATED, PREPARATION_METHODS, SEASONAL_AVAILABILITY,
                   SAFE_FOR_KIDS, MIN_AGE_YEARS, DATA_CONFIDENCE_SCORE
            FROM MEDICINAL_HERBS 
            WHERE {column} = 'Decrease'
            ORDER BY DATA_CONFIDENCE_SCORE DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        herbs = []
        for row in rows:
            herbs.append({
                "english": row[0], "tamil": row[1], "part": row[2],
                "uses": row[3], "diseases": row[4], "preparation": row[5],
                "season": row[6], "safe_kids": row[7], "min_age": row[8], "score": row[9]
            })
        return herbs
    except:
        return []

def get_all_herbs():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT NAME_ENGLISH, NAME_TAMIL, PLANT_PART, PRIMARY_USES,
                   VATA_EFFECT, PITTA_EFFECT, KAPHA_EFFECT,
                   DISEASES_TREATED, PREPARATION_METHODS, SEASONAL_AVAILABILITY,
                   SAFE_FOR_KIDS, MIN_AGE_YEARS, DATA_CONFIDENCE_SCORE
            FROM MEDICINAL_HERBS ORDER BY DATA_CONFIDENCE_SCORE DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except:
        return []

def get_all_recipes():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT RECIPE_NAME, DOSHA_SUITABILITY, SEASONAL_BEST FROM RECIPES ORDER BY RECIPE_ID")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except:
        return []

def classify_dosha_with_cortex(body_condition, weather):
    prompt = f"""You are an Ayurvedic health expert specializing in Tamil Nadu Siddha medicine.

User's Body Condition:
- Cold intensity: {body_condition['cold']}/5
- Cough type: {body_condition['cough']}, severity: {body_condition['cough_severity']}/5
- Pain locations: {body_condition['pain_locations']}, severity: {body_condition['pain_severity']}/5
- Pimple count: {body_condition['pimple_count']}
- Sweating: {body_condition['sweating']}, Sputum: {body_condition['sputum']}, Urine: {body_condition['urine']}
- Energy: {body_condition['energy']}/10, Digestion: {body_condition['digestion']}

Current Weather in Chennai:
- Temperature: {weather['temp']}°C (Feels like: {weather['feels_like']}°C)
- Humidity: {weather['humidity']}%, Wind: {weather['wind']} km/h
- Condition: {weather['desc']}

Consider BOTH body symptoms AND current weather for dosha classification.
Return ONLY valid JSON, no markdown, no code blocks:

{{"primary_dosha": "Vata or Pitta or Kapha", "dosha_percent": 75, "secondary_dosha": "Pitta", "secondary_percent": 25, "confidence": 0.92, "summary": "Brief summary including weather impact", "weather_impact": "How today weather affects dosha"}}"""

    try:
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text.strip())
    except:
        return {"primary_dosha": "Vata", "dosha_percent": 70, "secondary_dosha": "Pitta", "secondary_percent": 30, "confidence": 0.5, "summary": "Default", "weather_impact": "Unable to assess"}

def generate_recipes_with_cortex(dosha_info, season, energy, herbs_list, weather):
    herbs_text = "\n".join([f"- {h['english']} ({h['tamil']}): {h['uses']} | Prep: {h['preparation']}" for h in herbs_list[:8]])
    prompt = f"""Tamil Nadu Ayurvedic chef. Generate herb-enhanced recipes.
Dosha: {dosha_info['primary_dosha']} ({dosha_info['dosha_percent']}%), Season: {season}, Energy: {energy}/10
Weather: {weather['temp']}°C, Humidity {weather['humidity']}%, {weather['desc']}

Matching herbs from database:
{herbs_text}

Return ONLY valid JSON, no markdown:
{{"breakfast": {{"name": "Recipe", "ingredients": "List", "prep_time": "15 min", "medicinal_herbs": "Herbs to add", "herb_preparation": "How to prepare herbs", "why_this_dish": "Why it helps", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "lunch": {{"name": "Recipe", "ingredients": "List", "prep_time": "20 min", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_this_dish": "Why", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "dinner": {{"name": "Recipe", "ingredients": "List", "prep_time": "15 min", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_this_dish": "Why", "nutritional_benefits": "Benefits", "dosha_fit": "Balance"}}, "shopping_list": [{{"item": "Item", "quantity": "100", "unit": "g", "price_estimate": "10"}}], "total_cost": "140", "wellness_notes": "Benefits including weather-adapted advice"}}"""
    try:
        message = client.messages.create(model="claude-opus-4-20250514", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text.strip())
    except Exception as e:
        st.warning(f"Recipe error: {e}")
        return None

def generate_kids_recipes_with_cortex(age, dosha, herbs_list):
    kid_herbs = [h for h in herbs_list if h.get('safe_kids', True) and h.get('min_age', 2) <= int(age.split("-")[0])]
    herbs_text = "\n".join([f"- {h['english']} ({h['tamil']}): {h['uses']} | Min Age: {h['min_age']}yr" for h in kid_herbs[:8]])
    prompt = f"""Tamil Nadu pediatric nutritionist. Child: Age {age}yr, Dosha: {dosha}
Kid-safe herbs from database:
{herbs_text}

Return ONLY valid JSON:
{{"breakfast": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep for kids", "why_better_than_junk": "Why better", "taste_profile": "Taste", "prep_time": "15 min", "portion_size": "Amount"}}, "lunch": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_better_than_junk": "Why", "taste_profile": "Taste", "prep_time": "20 min", "portion_size": "Amount"}}, "dinner": {{"name": "Dish", "ingredients": "List", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep", "why_better_than_junk": "Why", "taste_profile": "Taste", "prep_time": "15 min", "portion_size": "Amount"}}, "parental_guidance": "Tips", "nutritional_summary": "Benefits"}}"""
    try:
        message = client.messages.create(model="claude-opus-4-20250514", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text.strip())
    except Exception as e:
        st.warning(f"Kids recipe error: {e}")
        return None

# ==================== SIDEBAR ====================
st.sidebar.title("🌿 Tamil Ayurvedic Food Platform")
st.sidebar.markdown("AI + Siddha + Weather + Herbs")
st.sidebar.markdown("---")

# Show live weather in sidebar
weather = get_chennai_weather()
st.sidebar.markdown(f"🌤️ **Chennai Now:** {weather['temp']}°C")
st.sidebar.markdown(f"💧 Humidity: {weather['humidity']}%")
st.sidebar.markdown(f"🌬️ {weather['desc']}")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", ["👨‍🍳 Adult", "👶 Kids", "🌿 Herbs", "🔧 Admin", "📊 Feedback"])

# ==================== ADULT PAGE ====================
if page == "👨‍🍳 Adult":
    st.title("🌿 Daily Body Condition Check")
    st.markdown(f"🌤️ **Live Chennai Weather:** {weather['temp']}°C, Humidity {weather['humidity']}%, {weather['desc']}")

    with st.form("body_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.header("Symptoms")
            cold = st.slider("Cold/Runny Nose", 0, 5, 0)
            cough = st.selectbox("Cough Type", ["None", "Dry", "Wet"])
            cough_severity = st.slider("Cough Severity", 0, 5, 0)
            pain_locations = st.multiselect("Pain Locations", ["Head", "Neck", "Shoulders", "Joints", "Abdomen", "Chest", "Back", "None"])
            pain_severity = st.slider("Pain Severity", 0, 5, 0)
            pimple_count = st.number_input("Pimple Count", 0, 100, 0)
        with col2:
            st.header("Body State")
            sweating = st.selectbox("Sweating", ["Normal", "Excessive"])
            sputum = st.selectbox("Sputum", ["Clear", "Yellow", "Green"])
            urine = st.selectbox("Urine", ["Pale", "Amber", "Dark"])
            st.header("Energy & Digestion")
            energy = st.slider("Energy Level", 1, 10, 5)
            digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        user_id = st.text_input("Your ID", "user_001")
        submitted = st.form_submit_button("🤖 Analyze with Weather + Herbs", type="primary")

        if submitted:
            try:
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                pain_locs = ",".join(pain_locations) if pain_locations else "None"
                cursor.execute(f"""INSERT INTO BODY_CONDITION_LOG (USER_ID, LOG_DATE, COLD_INTENSITY, COUGH_TYPE, COUGH_SEVERITY, PAIN_LOCATIONS, PAIN_SEVERITY, PIMPLE_COUNT, SWEATING_LEVEL, SPUTUM_COLOR, URINE_COLOR, ENERGY_LEVEL, DIGESTION_QUALITY, WEATHER_CONDITION) VALUES ('{user_id}', CURRENT_DATE(), {cold}, '{cough}', {cough_severity}, '{pain_locs}', {pain_severity}, {pimple_count}, '{sweating}', '{sputum}', '{urine}', {energy}, '{digestion}', '{weather["temp"]}C {weather["desc"]}')""")
                cursor.close()
                conn.close()
                st.success("✅ Logged with weather data!")

                with st.spinner("🤖 Analyzing symptoms + weather..."):
                    body = {'cold': cold, 'cough': cough, 'cough_severity': cough_severity, 'pain_locations': pain_locs, 'pain_severity': pain_severity, 'pimple_count': pimple_count, 'energy': energy, 'digestion': digestion, 'sweating': sweating, 'sputum': sputum, 'urine': urine}
                    dosha = classify_dosha_with_cortex(body, weather)
                    if dosha:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Primary Dosha", dosha['primary_dosha'])
                            st.metric("Primary %", f"{dosha['dosha_percent']}%")
                        with col2:
                            st.metric("Secondary", dosha.get('secondary_dosha', 'None'))
                        with col3:
                            conf = dosha.get('confidence', 0.8)
                            if isinstance(conf, str):
                                conf = float(conf)
                            st.metric("Confidence", f"{conf:.0%}")
                        st.info(f"📋 {dosha['summary']}")
                        st.info(f"🌤️ **Weather Impact:** {dosha.get('weather_impact', 'Weather considered')}")

                        herbs = get_herbs_for_dosha(dosha['primary_dosha'])
                        if herbs:
                            st.markdown("---")
                            st.subheader(f"🌿 {len(herbs)} Matching Herbs from Database")
                            for h in herbs:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']} | Score: {h['score']}/10")

                        try:
                            conn = get_snowflake_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT SEASON FROM V_TODAY_DOSHA_RECOMMENDATION")
                            sr = cursor.fetchone()
                            cursor.close()
                            conn.close()
                            season = sr[0] if sr else "Monsoon"
                        except:
                            season = "Monsoon"

                        with st.spinner("🤖 Generating weather-adapted herb recipes..."):
                            recipes = generate_recipes_with_cortex(dosha, season, energy, herbs, weather)
                            if recipes:
                                for meal, icon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                                    st.markdown("---")
                                    st.subheader(f"{icon} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 **Ingredients:** {recipes[meal]['ingredients']}")
                                    st.write(f"🌿 **Herbs:** {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 **Herb Prep:** {recipes[meal].get('herb_preparation', '')}")
                                    st.write(f"💪 **Benefits:** {recipes[meal]['nutritional_benefits']}")
                                    st.write(f"⏱️ **Time:** {recipes[meal]['prep_time']}")
                                st.markdown("---")
                                if recipes.get('shopping_list'):
                                    st.subheader("🛒 Shopping List")
                                    for item in recipes['shopping_list']:
                                        st.write(f"• {item.get('item','')} - {item.get('quantity','')} {item.get('unit','')} (₹{item.get('price_estimate','')})")
                                st.metric("Total Cost", f"₹{recipes.get('total_cost', '0')}")
                                st.info(f"💡 {recipes.get('wellness_notes', '')}")
            except Exception as e:
                st.error(str(e))

# ==================== KIDS PAGE ====================
elif page == "👶 Kids":
    st.title("👶 Kids Nutrition with Medicinal Herbs")
    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("Age", ["2-3 years", "4-6 years", "7-10 years", "11+ years"])
        age_val = {"2-3 years": "2-3", "4-6 years": "4-6", "7-10 years": "7-10", "11+ years": "11+"}[age]
    with col2:
        dosha = st.selectbox("Dosha", ["Not Sure", "Vata", "Pitta", "Kapha"])

    all_herbs = get_all_herbs()
    herbs = [{"english": r[0], "tamil": r[1], "part": r[2], "uses": r[3], "preparation": r[8] if len(r)>8 else "", "season": r[9] if len(r)>9 else "", "safe_kids": r[10] if len(r)>10 else True, "min_age": r[11] if len(r)>11 else 2, "score": r[12] if len(r)>12 else 7} for r in all_herbs]

    if st.button("🤖 Get Herb-Enhanced Meal Plan", type="primary"):
        with st.spinner("Creating..."):
            kids = generate_kids_recipes_with_cortex(age_val, dosha, herbs)
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

# ==================== HERB DATABASE PAGE ====================
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

# ==================== ADMIN PAGE ====================
elif page == "🔧 Admin":
    st.title("🔧 Admin - Add Herbs & Dishes")
    st.markdown("Add new herbs and dishes directly to Snowflake")

    admin_tab = st.radio("What to add?", ["🌿 New Herb", "🍽️ New Dish"])

    if admin_tab == "🌿 New Herb":
        st.subheader("🌿 Add New Medicinal Herb")
        with st.form("add_herb"):
            col1, col2 = st.columns(2)
            with col1:
                h_tamil = st.text_input("Tamil Name *", "")
                h_english = st.text_input("English Name *", "")
                h_botanical = st.text_input("Botanical Name", "")
                h_part = st.selectbox("Plant Part", ["Leaves", "Root", "Seed", "Flower", "Bark", "Fruit", "Whole plant", "Rhizome", "Stem", "Bulb", "Oil", "Grain"])
                h_uses = st.text_area("Primary Uses *", "")
                h_diseases = st.text_area("Diseases Treated", "")
            with col2:
                h_vata = st.selectbox("Vata Effect", ["Decrease", "Increase", "Neutral"])
                h_pitta = st.selectbox("Pitta Effect", ["Decrease", "Increase", "Neutral"])
                h_kapha = st.selectbox("Kapha Effect", ["Decrease", "Increase", "Neutral"])
                h_prep = st.text_input("Preparation Methods", "")
                h_season = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
                h_kids = st.checkbox("Safe for Kids", True)
                h_age = st.number_input("Minimum Age", 1, 18, 3)
                h_score = st.slider("Data Confidence Score", 1, 10, 7)

            submitted = st.form_submit_button("✅ Add Herb to Database", type="primary")
            if submitted and h_tamil and h_english and h_uses:
                try:
                    conn = get_snowflake_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        INSERT INTO MEDICINAL_HERBS 
                        (NAME_TAMIL, NAME_ENGLISH, NAME_BOTANICAL, PLANT_PART, VATA_EFFECT, PITTA_EFFECT, KAPHA_EFFECT, PRIMARY_USES, DISEASES_TREATED, PREPARATION_METHODS, SEASONAL_AVAILABILITY, SAFE_FOR_KIDS, MIN_AGE_YEARS, DATA_CONFIDENCE_SCORE, SCIENTIFIC_VALIDATION)
                        SELECT '{h_tamil}', '{h_english}', '{h_botanical}', '{h_part}', '{h_vata}', '{h_pitta}', '{h_kapha}', '{h_uses}', '{h_diseases}', '{h_prep}', '{h_season}', {h_kids}, {h_age}, {h_score}, FALSE
                    """)
                    cursor.close()
                    conn.close()
                    st.success(f"✅ Herb '{h_english}' added successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            elif submitted:
                st.warning("Please fill Tamil Name, English Name, and Primary Uses")

    elif admin_tab == "🍽️ New Dish":
        st.subheader("🍽️ Add New Tamil Dish")
        with st.form("add_dish"):
            col1, col2 = st.columns(2)
            with col1:
                d_name = st.text_input("Dish Name *", "")
                d_serves = st.number_input("Serves", 1, 10, 4)
                d_prep = st.number_input("Prep Time (minutes)", 5, 120, 20)
                d_dosha = st.selectbox("Dosha Suitability", ["Vata", "Pitta", "Kapha", "Neutral", "Vata/Pitta", "Vata/Kapha", "Pitta/Kapha"])
            with col2:
                d_season = st.selectbox("Best Season", ["Year-round", "Summer", "Winter", "Monsoon", "Post-Monsoon", "Summer/Monsoon", "Monsoon/Winter"])
                d_method = st.text_input("Cooking Method", "")
                d_instructions = st.text_area("Instructions", "")

            submitted = st.form_submit_button("✅ Add Dish to Database", type="primary")
            if submitted and d_name:
                try:
                    conn = get_snowflake_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        INSERT INTO RECIPES (RECIPE_NAME, PRIMARY_INGREDIENT_ID, SERVES, PREP_TIME_MIN, DOSHA_SUITABILITY, SEASONAL_BEST, COOKING_METHOD, INSTRUCTIONS)
                        VALUES ('{d_name}', 1, {d_serves}, {d_prep}, '{d_dosha}', '{d_season}', '{d_method}', '{d_instructions}')
                    """)
                    cursor.close()
                    conn.close()
                    st.success(f"✅ Dish '{d_name}' added successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            elif submitted:
                st.warning("Please enter Dish Name")

    st.markdown("---")
    st.subheader("📊 Current Database Stats")
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MEDICINAL_HERBS")
        herb_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM RECIPES")
        recipe_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM BODY_CONDITION_LOG")
        log_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM USER_FEEDBACK")
        feedback_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🌿 Herbs", herb_count)
        col2.metric("🍽️ Dishes", recipe_count)
        col3.metric("📋 Logs", log_count)
        col4.metric("📊 Feedback", feedback_count)
    except:
        st.info("Connect to Snowflake to see stats")

# ==================== FEEDBACK PAGE ====================
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
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                cursor.execute(f"""INSERT INTO USER_FEEDBACK (USER_ID, RECOMMENDATION_DATE, FEEDBACK_DATE, BREAKFAST_RATING, LUNCH_RATING, DINNER_RATING, ENERGY_LEVEL_NEXT_DAY, DIGESTION_QUALITY) VALUES ('{user_id}', CURRENT_DATE()-1, CURRENT_DATE(), {br}, {lr}, {dr}, {energy}, '{digestion}')""")
                cursor.close()
                conn.close()
                st.success("✅ Saved!")
            except Exception as e:
                st.error(str(e))
