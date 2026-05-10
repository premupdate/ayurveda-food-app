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

def get_weather():
    try:
        r = requests.get("https://wttr.in/Chennai?format=j1", timeout=5).json()
        c = r['current_condition'][0]
        return {"temp": c['temp_C'], "humidity": c['humidity'], "desc": c['weatherDesc'][0]['value'], "feels_like": c['FeelsLikeC']}
    except:
        return {"temp": "32", "humidity": "65", "desc": "Partly Cloudy", "feels_like": "35"}

def get_herbs_for_dosha(dosha):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(f"SELECT name_english, name_tamil, plant_part, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs WHERE {dosha.lower()}_effect = 'Decrease' ORDER BY data_confidence_score DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [{"english": r[0], "tamil": r[1], "part": r[2], "uses": r[3], "diseases": r[4], "preparation": r[5], "season": r[6], "safe_kids": r[7], "min_age": r[8], "score": r[9]} for r in rows]
    except:
        return []

def get_all_herbs():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name_english, name_tamil, plant_part, primary_uses, vata_effect, pitta_effect, kapha_effect, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score FROM medicinal_herbs ORDER BY data_confidence_score DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except:
        return []

def parse_feedback_notes(notes, user_id):
    """Use Gemini to parse user notes and extract dish/herb info"""
    prompt = f"""You are a Tamil food analyst. The user wrote this note about what they ate:
"{notes}"

Extract the dish name, vegetables used, herbs used, and any spices. Return ONLY valid JSON:
{{"dish_name": "Name of dish", "vegetables": ["veg1", "veg2"], "herbs": ["herb1", "herb2"], "spices": ["spice1", "spice2"], "dosha_assessment": "Which dosha this meal likely balances", "health_benefits": "Brief health benefits"}}"""
    return ask_gemini(prompt)

# Sidebar
weather = get_weather()
st.sidebar.title("🌿 Tamil Ayurvedic Platform")
st.sidebar.markdown(f"🌤️ Chennai: {weather['temp']}°C | {weather['desc']}")
st.sidebar.markdown("🆓 100% FREE Platform")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["👨‍🍳 Adult", "👶 Kids", "🏔️ Ainthinai", "🌦️ Seasons", "🌿 Herbs", "🔧 Admin", "📊 Feedback"])

# ==================== ADULT PAGE ====================
if page == "👨‍🍳 Adult":
    st.title("🌿 Daily Body Condition")
    st.markdown(f"🌤️ {weather['temp']}°C, {weather['desc']}")
    with st.form("body"):
        col1, col2 = st.columns(2)
        with col1:
            cold = st.slider("Cold", 0, 5, 0); cough = st.selectbox("Cough", ["None", "Dry", "Wet"]); cough_sev = st.slider("Cough Severity", 0, 5, 0)
            pain = st.multiselect("Pain", ["Head", "Neck", "Joints", "Abdomen", "Chest", "Back", "None"]); pain_sev = st.slider("Pain Severity", 0, 5, 0)
            pimples = st.number_input("Pimples", 0, 100, 0)
        with col2:
            sweating = st.selectbox("Sweating", ["Normal", "Excessive"]); sputum = st.selectbox("Sputum", ["Clear", "Yellow", "Green"]); urine = st.selectbox("Urine", ["Pale", "Amber", "Dark"])
            energy = st.slider("Energy", 1, 10, 5); digestion = st.selectbox("Digestion", ["Good", "Normal", "Sluggish", "Weak"])
        user_id = st.text_input("ID", "user_001")
        if st.form_submit_button("🤖 Analyze", type="primary"):
            try:
                conn = get_db(); cur = conn.cursor(); pain_locs = ",".join(pain) if pain else "None"
                cur.execute("INSERT INTO body_condition_log (user_id, log_date, cold_intensity, cough_type, cough_severity, pain_locations, pain_severity, pimple_count, sweating_level, sputum_color, urine_color, energy_level, digestion_quality, weather_condition) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id, date.today(), cold, cough, cough_sev, pain_locs, pain_sev, pimples, sweating, sputum, urine, energy, digestion, f"{weather['temp']}C {weather['desc']}"))
                conn.commit(); cur.close(); conn.close(); st.success("✅ Logged!")
                body = {'cold': cold, 'cough': cough, 'cough_severity': cough_sev, 'pain_locations': pain_locs, 'pain_severity': pain_sev, 'pimple_count': pimples, 'energy': energy, 'digestion': digestion, 'sweating': sweating, 'sputum': sputum, 'urine': urine}
                with st.spinner("🤖 Analyzing..."):
                    dosha = ask_gemini(f"""Siddha expert. Body: {json.dumps(body)}, Weather: {weather['temp']}C {weather['desc']}. Return JSON: {{"primary_dosha": "Vata/Pitta/Kapha", "dosha_percent": 75, "secondary_dosha": "X", "secondary_percent": 25, "confidence": 0.9, "summary": "Brief", "weather_impact": "Impact"}}""")
                    if dosha:
                        col1, col2 = st.columns(2)
                        col1.metric("Dosha", f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        col2.metric("Secondary", dosha.get('secondary_dosha', 'None'))
                        st.info(f"📋 {dosha['summary']}")
                        st.info(f"🌤️ {dosha.get('weather_impact', '')}")
                        herbs = get_herbs_for_dosha(dosha['primary_dosha'])
                        if herbs:
                            st.markdown("---"); st.subheader(f"🌿 {len(herbs)} Matching Herbs")
                            for h in herbs:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']}")
                        try:
                            conn = get_db(); cur = conn.cursor(); cur.execute("SELECT season FROM seasonal_calendar WHERE month_num = %s", (date.today().month,))
                            sr = cur.fetchone(); cur.close(); conn.close(); season = sr[0] if sr else "Monsoon"
                        except:
                            season = "Monsoon"
                        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in herbs[:8]])
                        with st.spinner("🤖 Recipes..."):
                            recipes = ask_gemini(f"""Tamil chef. Dosha: {dosha['primary_dosha']} {dosha['dosha_percent']}%, Season: {season}, Energy: {energy}/10, Weather: {weather['temp']}C. Herbs: {herbs_text}. Return JSON: {{"breakfast": {{"name": "X", "ingredients": "X", "prep_time": "15min", "medicinal_herbs": "X", "herb_preparation": "X", "why_this_dish": "X", "nutritional_benefits": "X", "dosha_fit": "X"}}, "lunch": {{"name": "X", "ingredients": "X", "prep_time": "20min", "medicinal_herbs": "X", "herb_preparation": "X", "why_this_dish": "X", "nutritional_benefits": "X", "dosha_fit": "X"}}, "dinner": {{"name": "X", "ingredients": "X", "prep_time": "15min", "medicinal_herbs": "X", "herb_preparation": "X", "why_this_dish": "X", "nutritional_benefits": "X", "dosha_fit": "X"}}, "wellness_notes": "X"}}""")
                            if recipes:
                                for meal, icon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                                    st.markdown("---"); st.subheader(f"{icon} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 {recipes[meal]['ingredients']}"); st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 {recipes[meal].get('herb_preparation', '')}"); st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                                st.info(f"💡 {recipes.get('wellness_notes', '')}")
            except Exception as e:
                st.error(str(e))

# ==================== KIDS PAGE ====================
elif page == "👶 Kids":
    st.title("👶 Kids Nutrition")
    col1, col2 = st.columns(2)
    with col1:
        age = st.selectbox("Age", ["2-3", "4-6", "7-10", "11+"])
    with col2:
        dosha = st.selectbox("Dosha", ["Not Sure", "Vata", "Pitta", "Kapha"])
    all_herbs = get_all_herbs()
    herbs = [{"english": r[0], "tamil": r[1], "uses": r[3], "preparation": r[8] if len(r)>8 else "", "safe_kids": r[10] if len(r)>10 else True, "min_age": r[11] if len(r)>11 else 2} for r in all_herbs]
    kid_herbs = [h for h in herbs if h.get('safe_kids', True) and h.get('min_age', 2) <= int(age.split("-")[0])]
    if st.button("🤖 Get Meal Plan", type="primary"):
        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in kid_herbs[:8]])
        with st.spinner("Creating..."):
            kids = ask_gemini(f"""Tamil pediatric nutritionist. Child Age {age}yr, Dosha {dosha}. Herbs: {herbs_text}. Return JSON: {{"breakfast": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "15min"}}, "lunch": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "20min"}}, "dinner": {{"name": "X", "ingredients": "X", "health_benefits": "X", "medicinal_herbs": "X", "why_better_than_junk": "X", "taste_profile": "X", "prep_time": "15min"}}, "parental_guidance": "X"}}""")
            if kids:
                for meal, icon in [("breakfast", "☀️"), ("lunch", "🌞"), ("dinner", "🌙")]:
                    st.markdown("---"); st.subheader(f"{icon} {meal.title()}")
                    st.markdown(f"**{kids[meal]['name']}**")
                    st.write(f"📝 {kids[meal]['ingredients']}"); st.write(f"💪 {kids[meal]['health_benefits']}")
                    st.write(f"🌿 {kids[meal]['medicinal_herbs']}"); st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance', '')}")

# ==================== AINTHINAI (5 LANDS) PAGE ====================
elif page == "🏔️ Ainthinai":
    st.title("🏔️ ஐந்திணை - Five Lands of Tamil Nadu")
    st.markdown("Ancient Tamil land classification from Sangam literature with medicinal flora")

    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM ainthinai_lands ORDER BY land_id")
        lands = cur.fetchall()

        land_icons = {"Kurinji": "🏔️", "Mullai": "🌳", "Marutham": "🌾", "Neidhal": "🌊", "Palai": "🏜️"}
        land_colors = {"Kurinji": "violet", "Mullai": "green", "Marutham": "orange", "Neidhal": "blue", "Palai": "red"}

        tabs = st.tabs([f"{land_icons.get(l[2], '🌍')} {l[1]} ({l[2]})" for l in lands])

        for i, land in enumerate(lands):
            with tabs[i]:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f"{land[1]} - {land[2]}")
                    st.write(f"**Tamil:** {land[3]}")
                    st.write(f"**English:** {land[4]}")
                    st.write(f"**Description:** {land[5]}")
                    st.write(f"🙏 **Deity:** {land[6]} ({land[7]})")
                    st.write(f"🌸 **Signature Flower:** {land[8]} ({land[9]})")
                    st.write(f"🌳 **Signature Tree:** {land[10]} ({land[11]})")
                with col2:
                    st.write(f"👷 **Occupation:** {land[12]}")
                    st.write(f"👥 **People:** {land[13]}")
                    st.write(f"🍚 **Staple Food:** {land[14]}")
                    st.write(f"🎵 **Music:** {land[15]}")
                    st.write(f"💕 **Emotion:** {land[16]}")
                    st.write(f"⏰ **Time:** {land[17]}")
                    st.write(f"📍 **Modern Districts:** {land[18]}")
                    st.write(f"🌤️ **Climate:** {land[19]}")

                # Show flora for this land
                st.markdown("---")
                st.subheader(f"🌿 Flora of {land[2]}")
                cur.execute("SELECT flora_type, name_tamil, name_english, name_botanical, category, seasonal_availability, medicinal_uses, culinary_uses, dosha_impact FROM land_flora_mapping WHERE land_id = %s ORDER BY flora_type", (land[0],))
                flora = cur.fetchall()

                for f in flora:
                    type_icon = {"Herb": "🌱", "Flower": "🌸", "Fruit": "🍎", "Tree": "🌳", "Grain": "🌾"}.get(f[0], "🌿")
                    st.write(f"{type_icon} **{f[2]}** ({f[1]}) | *{f[3]}* | {f[4]}")
                    st.write(f"   💊 Medicinal: {f[6]} | 🍳 Culinary: {f[7]} | Season: {f[5]} | Dosha: {f[8]}")

        cur.close(); conn.close()
    except Exception as e:
        st.error(f"Load Ainthinai data: {e}")
        st.info("Run PHASE2_AINTHINAI_SCHEMA.sql in Supabase first!")

# ==================== TAMIL SEASONS PAGE ====================
elif page == "🌦️ Seasons":
    st.title("🌦️ Tamil Seasons (பெரும்பொழுது)")
    st.markdown("Six seasons of Tamil Nadu with seasonal food, herbs, fruits, and flowers")

    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM tamil_seasons ORDER BY season_id")
        seasons = cur.fetchall()

        season_icons = ["☀️", "🔥", "🌧️", "🍂", "❄️", "🌸"]

        for i, s in enumerate(seasons):
            icon = season_icons[i] if i < len(season_icons) else "🌤️"
            with st.expander(f"{icon} {s[1]} - {s[2]} ({s[4]})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Tamil Months:** {s[3]}")
                    st.write(f"**Duration:** {s[5]}")
                    st.write(f"**Weather:** {s[6]}")
                    st.write(f"**Dominant Dosha:** {s[7]}")
                    st.write(f"**Food Recommendation:** {s[8]}")
                with col2:
                    st.write(f"🌿 **Herbs in Season:** {s[9]}")
                    st.write(f"🍎 **Fruits in Season:** {s[10]}")
                    st.write(f"🌸 **Flowers in Season:** {s[11]}")
                    st.write(f"🌾 **Farming:** {s[12]}")

        # Current season highlight
        month = date.today().month
        season_map = {1: 4, 2: 5, 3: 5, 4: 0, 5: 0, 6: 1, 7: 1, 8: 2, 9: 2, 10: 3, 11: 3, 12: 4}
        idx = season_map.get(month, 0)
        if idx < len(seasons):
            st.markdown("---")
            st.success(f"📅 **Current Season:** {season_icons[idx]} {seasons[idx][2]} ({seasons[idx][4]})")
            st.info(f"🍽️ **Eat Today:** {seasons[idx][8]}")
            st.info(f"🌿 **Use These Herbs:** {seasons[idx][9]}")

        cur.close(); conn.close()
    except Exception as e:
        st.error(f"Load Seasons data: {e}")
        st.info("Run PHASE2_AINTHINAI_SCHEMA.sql in Supabase first!")

# ==================== HERBS DATABASE ====================
elif page == "🌿 Herbs":
    st.title("🌿 Medicinal Herbs Database")
    search = st.text_input("Search", "")
    dosha_filter = st.selectbox("Filter", ["All", "Vata", "Pitta", "Kapha"])
    all_herbs = get_all_herbs()
    st.write(f"**Total: {len(all_herbs)} herbs**")
    for r in all_herbs:
        eng, tam, part, uses = r[0] or "", r[1] or "", r[2] or "", r[3] or ""
        vata, pitta, kapha = r[4] or "", r[5] or "", r[6] or ""
        diseases, prep, season = r[7] or "", r[8] or "", r[9] or ""
        score = r[12] or 7
        if search and search.lower() not in eng.lower() and search.lower() not in tam.lower():
            continue
        if dosha_filter != "All" and {"Vata": vata, "Pitta": pitta, "Kapha": kapha}[dosha_filter] != "Decrease":
            continue
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### 🌱 {eng}")
            st.write(f"**{tam}** | {part} | Score: {score}/10")
        with col2:
            st.write(f"{uses} | Diseases: {diseases}")
            st.write(f"V:{vata} P:{pitta} K:{kapha} | {prep}")
        st.markdown("---")

# ==================== ADMIN PAGE ====================
elif page == "🔧 Admin":
    st.title("🔧 Admin")
    tab = st.radio("Add:", ["🌿 Herb", "🍽️ Dish"])
    if tab == "🌿 Herb":
        with st.form("herb"):
            col1, col2 = st.columns(2)
            with col1:
                ht = st.text_input("Tamil Name *"); he = st.text_input("English Name *"); hb = st.text_input("Botanical"); hp = st.selectbox("Part", ["Leaves", "Root", "Seed", "Flower", "Bark", "Fruit", "Whole plant", "Rhizome"])
                hu = st.text_area("Uses *"); hd = st.text_area("Diseases")
            with col2:
                hv = st.selectbox("Vata", ["Decrease", "Increase", "Neutral"]); hpi = st.selectbox("Pitta", ["Decrease", "Increase", "Neutral"]); hk = st.selectbox("Kapha", ["Decrease", "Increase", "Neutral"])
                hpr = st.text_input("Preparation"); hs = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
                hkid = st.checkbox("Safe for Kids", True); hage = st.number_input("Min Age", 1, 18, 3); hsc = st.slider("Score", 1, 10, 7)
            if st.form_submit_button("✅ Add Herb", type="primary") and ht and he and hu:
                try:
                    conn = get_db(); cur = conn.cursor()
                    cur.execute("INSERT INTO medicinal_herbs (name_tamil, name_english, name_botanical, plant_part, vata_effect, pitta_effect, kapha_effect, primary_uses, diseases_treated, preparation_methods, seasonal_availability, safe_for_kids, min_age_years, data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (ht, he, hb, hp, hv, hpi, hk, hu, hd, hpr, hs, hkid, hage, hsc))
                    conn.commit(); cur.close(); conn.close(); st.success(f"✅ '{he}' added!"); st.balloons()
                except Exception as e:
                    st.error(str(e))
    elif tab == "🍽️ Dish":
        with st.form("dish"):
            dn = st.text_input("Dish Name *"); dd = st.selectbox("Dosha", ["Vata", "Pitta", "Kapha", "Neutral"]); ds = st.selectbox("Season", ["Year-round", "Summer", "Winter", "Monsoon"])
            di = st.text_area("Instructions")
            if st.form_submit_button("✅ Add Dish", type="primary") and dn:
                try:
                    conn = get_db(); cur = conn.cursor()
                    cur.execute("INSERT INTO recipes (recipe_name, primary_ingredient_id, serves, prep_time_min, dosha_suitability, seasonal_best, instructions) VALUES (%s,1,4,20,%s,%s,%s)", (dn, dd, ds, di))
                    conn.commit(); cur.close(); conn.close(); st.success(f"✅ '{dn}' added!"); st.balloons()
                except Exception as e:
                    st.error(str(e))
    st.markdown("---")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicinal_herbs"); herbs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recipes"); recipes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM body_condition_log"); logs = cur.fetchone()[0]
        cur.close(); conn.close()
        col1, col2, col3 = st.columns(3)
        col1.metric("🌿 Herbs", herbs); col2.metric("🍽️ Dishes", recipes); col3.metric("📋 Logs", logs)
    except:
        pass

# ==================== SMART FEEDBACK PAGE ====================
elif page == "📊 Feedback":
    st.title("📊 Smart Feedback")
    st.markdown("AI will parse your notes and extract dish/herb info for learning!")
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

        st.markdown("---")
        st.subheader("📝 What Did You Actually Eat? (AI Parses This!)")
        st.markdown("Write what you ate - AI will extract dishes, vegetables, herbs and store them")
        notes = st.text_area("Example: Had sundal with neem flower for breakfast, murungakkai sambar with manathakkali keerai for lunch, and ragi porridge for dinner", "", height=100)

        user_id = st.text_input("ID", "user_001")
        if st.form_submit_button("Submit & Parse", type="primary"):
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO user_feedback (user_id, recommendation_date, feedback_date, breakfast_rating, lunch_rating, dinner_rating, energy_level_next_day, digestion_quality) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id, date.today(), date.today(), br, lr, dr, energy, digestion))
                conn.commit()
                st.success("✅ Feedback saved!")

                # AI Parse notes
                if notes.strip():
                    with st.spinner("🤖 AI parsing your meal notes..."):
                        parsed = parse_feedback_notes(notes, user_id)
                        if parsed:
                            st.markdown("---")
                            st.subheader("🤖 AI Parsed Your Notes:")
                            st.write(f"🍽️ **Dish:** {parsed.get('dish_name', 'Unknown')}")
                            st.write(f"🥬 **Vegetables:** {', '.join(parsed.get('vegetables', []))}")
                            st.write(f"🌿 **Herbs:** {', '.join(parsed.get('herbs', []))}")
                            st.write(f"🌶️ **Spices:** {', '.join(parsed.get('spices', []))}")
                            st.write(f"⚖️ **Dosha:** {parsed.get('dosha_assessment', 'Unknown')}")
                            st.write(f"💪 **Benefits:** {parsed.get('health_benefits', 'Unknown')}")

                            # Save parsed data
                            try:
                                cur2 = conn.cursor()
                                cur2.execute("INSERT INTO feedback_parsed_items (user_id, original_note, parsed_dish_name, parsed_ingredients, parsed_herbs, parsed_vegetables, ai_classification, dosha_assessment) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                                    (user_id, notes, parsed.get('dish_name', ''), json.dumps(parsed.get('spices', [])), json.dumps(parsed.get('herbs', [])), json.dumps(parsed.get('vegetables', [])), parsed.get('health_benefits', ''), parsed.get('dosha_assessment', '')))
                                conn.commit(); cur2.close()
                                st.success("✅ Parsed data saved for model learning!")
                            except:
                                pass

                cur.close(); conn.close()
            except Exception as e:
                st.error(str(e))
