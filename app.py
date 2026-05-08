import streamlit as st
import snowflake.connector
import os
from dotenv import load_dotenv
import json
from anthropic import Anthropic

load_dotenv()

st.set_page_config(page_title="Tamil Nadu Ayurvedic Food + Herbs Recommendation", layout="wide")

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

def get_herbs_for_dosha(dosha_type):
    """Fetch matching herbs from MEDICINAL_HERBS table"""
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
                "season": row[6], "safe_kids": row[7], "min_age": row[8],
                "score": row[9]
            })
        return herbs
    except Exception as e:
        return []

def get_all_herbs():
    """Fetch all herbs from MEDICINAL_HERBS table"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT NAME_ENGLISH, NAME_TAMIL, PLANT_PART, PRIMARY_USES,
                   VATA_EFFECT, PITTA_EFFECT, KAPHA_EFFECT,
                   DISEASES_TREATED, PREPARATION_METHODS, SEASONAL_AVAILABILITY,
                   SAFE_FOR_KIDS, MIN_AGE_YEARS, DATA_CONFIDENCE_SCORE
            FROM MEDICINAL_HERBS
            ORDER BY DATA_CONFIDENCE_SCORE DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except:
        return []

def classify_dosha_with_cortex(body_condition):
    prompt = f"""You are an Ayurvedic health expert specializing in Tamil Nadu Siddha medicine.

User's Body Condition:
- Cold intensity: {body_condition['cold']}/5
- Cough type: {body_condition['cough']}
- Cough severity: {body_condition['cough_severity']}/5
- Pain locations: {body_condition['pain_locations']}
- Pain severity: {body_condition['pain_severity']}/5
- Pimple count: {body_condition['pimple_count']}
- Sweating level: {body_condition['sweating']}
- Sputum color: {body_condition['sputum']}
- Urine color: {body_condition['urine']}
- Energy level: {body_condition['energy']}/10
- Digestion quality: {body_condition['digestion']}

Classify dosha. Return ONLY valid JSON, no markdown, no code blocks:

{{"primary_dosha": "Vata or Pitta or Kapha", "dosha_percent": 75, "secondary_dosha": "Pitta", "secondary_percent": 25, "confidence": 0.92, "summary": "Brief clinical summary"}}"""

    try:
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        return json.loads(response_text)
    except:
        return {"primary_dosha": "Vata", "dosha_percent": 70, "secondary_dosha": "Pitta", "secondary_percent": 30, "confidence": 0.5, "summary": "Default classification"}

def generate_recipes_with_cortex(dosha_info, season, user_energy, herbs_list):
    herbs_text = ""
    for h in herbs_list:
        herbs_text += f"- {h['english']} ({h['tamil']}): {h['uses']} | Preparation: {h['preparation']} | Season: {h['season']}\n"

    prompt = f"""You are a Tamil Nadu Ayurvedic chef with expertise in Siddha medicinal herbs.

User Profile:
- Primary Dosha: {dosha_info['primary_dosha']} ({dosha_info['dosha_percent']}%)
- Season: {season}
- Energy: {user_energy}/10

Available Tamil Dishes: Vaazhapoo Sambar, Manathakkali Keerai Sambar, Kathirikai Murungakkai Sambar, Vegetable Biryani with Pudhina, Toor Dall Tadka, Potato Fry, Sundakkai Kadaisal, Murungakkai Poriyal, Cauliflower Pakora, Vendakkai Poriyal

MEDICINAL HERBS FROM DATABASE (matching user's dosha):
{herbs_text}

Generate 3 recipes that INCLUDE specific medicinal herbs from the database above. Return ONLY valid JSON, no markdown, no code blocks:

{{"breakfast": {{"name": "Recipe name", "ingredients": "Ingredients list", "prep_time": "15 minutes", "medicinal_herbs": "Which herbs from database to add and why", "herb_preparation": "How to prepare the herb for this dish", "why_this_dish": "Why it helps their dosha", "nutritional_benefits": "Key nutrients", "dosha_fit": "How it balances dosha"}}, "lunch": {{"name": "Recipe name", "ingredients": "Ingredients list", "prep_time": "20 minutes", "medicinal_herbs": "Herbs to add", "herb_preparation": "How to prepare herbs", "why_this_dish": "Why it helps", "nutritional_benefits": "Key nutrients", "dosha_fit": "Balance"}}, "dinner": {{"name": "Recipe name", "ingredients": "Ingredients list", "prep_time": "15 minutes", "medicinal_herbs": "Herbs to add", "herb_preparation": "How to prepare herbs", "why_this_dish": "Why it helps", "nutritional_benefits": "Key nutrients", "dosha_fit": "Balance"}}, "shopping_list": [{{"item": "Ingredient", "quantity": "100", "unit": "g", "price_estimate": "10"}}], "total_cost": "140", "wellness_notes": "Overall benefits including herb therapy"}}"""

    try:
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        return json.loads(response_text)
    except Exception as e:
        st.warning(f"Could not generate recipes: {e}")
        return None

def generate_kids_recipes_with_cortex(child_age, dosha_type, herbs_list):
    kid_herbs = [h for h in herbs_list if h.get('safe_kids', True) and h.get('min_age', 2) <= int(child_age.split("-")[0])]
    herbs_text = ""
    for h in kid_herbs[:8]:
        herbs_text += f"- {h['english']} ({h['tamil']}): {h['uses']} | Prep: {h['preparation']} | Min Age: {h['min_age']}yr\n"

    prompt = f"""You are a Tamil Nadu pediatric nutritionist with Siddha medicine expertise.
Child Age: {child_age} years, Dosha: {dosha_type}

Available Tamil Dishes: Vaazhapoo Sambar, Manathakkali Sambar, Kathirikai Murungakkai Sambar, Vegetable Biryani, Toor Dall Tadka, Potato Fry, Sundakkai Kadaisal, Murungakkai Poriyal, Cauliflower Pakora, Vendakkai Poriyal

KID-SAFE MEDICINAL HERBS FROM DATABASE:
{herbs_text}

Generate 3 kid-friendly recipes INCORPORATING these herbs. Return ONLY valid JSON, no markdown, no code blocks:

{{"breakfast": {{"name": "Kid-friendly dish", "ingredients": "Simple ingredients", "health_benefits": "Growth and development benefits", "medicinal_herbs": "Which kid-safe herbs to add from database", "herb_preparation": "How to prepare herbs for kids", "why_better_than_junk": "Why better than junk food", "taste_profile": "Kid-friendly taste", "prep_time": "10-15 minutes", "portion_size": "Age-appropriate"}}, "lunch": {{"name": "Dish", "ingredients": "Ingredients", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep method", "why_better_than_junk": "Why better", "taste_profile": "Taste", "prep_time": "15-20 min", "portion_size": "Amount"}}, "dinner": {{"name": "Dish", "ingredients": "Ingredients", "health_benefits": "Benefits", "medicinal_herbs": "Herbs", "herb_preparation": "Prep method", "why_better_than_junk": "Why better", "taste_profile": "Taste", "prep_time": "10-15 min", "portion_size": "Amount"}}, "parental_guidance": "Tips for introducing herbs to kids", "nutritional_summary": "Overall child development benefits"}}"""

    try:
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        return json.loads(response_text)
    except Exception as e:
        st.warning(f"Could not generate kids recipes: {e}")
        return None

st.sidebar.title("🌿 AI Ayurvedic Food + Herbs")
st.sidebar.markdown("Powered by Claude AI + Snowflake + Siddha Medicine")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", ["👨‍🍳 Adult Nutrition", "👶 Kids Nutrition", "🌿 Herb Database", "📊 Feedback"])

if page == "👨‍🍳 Adult Nutrition":
    st.title("🌿 Daily Body Condition Check")
    st.markdown("Log your symptoms - AI will classify dosha, match herbs from database, and recommend meals")

    with st.form("body_condition_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.header("Symptoms")
            cold = st.slider("Cold/Runny Nose (0=None, 5=Severe)", 0, 5, 0)
            cough = st.selectbox("Cough Type", ["None", "Dry", "Wet"])
            cough_severity = st.slider("Cough Severity", 0, 5, 0)
            pain_locations = st.multiselect("Pain Locations", ["Head", "Neck", "Shoulders", "Joints", "Abdomen", "Chest", "Back", "None"])
            pain_severity = st.slider("Pain Severity", 0, 5, 0)
            pimple_count = st.number_input("Pimple/Acne Count", 0, 100, 0)
        with col2:
            st.header("Body State")
            sweating = st.selectbox("Sweating Level", ["Normal", "Excessive"])
            sputum = st.selectbox("Sputum Color", ["Clear", "Yellow", "Green"])
            urine = st.selectbox("Urine Color", ["Pale", "Amber", "Dark"])
            st.header("Energy & Digestion")
            energy = st.slider("Energy Level (1=Very Low, 10=Very High)", 1, 10, 5)
            digestion = st.selectbox("Digestion Quality", ["Good", "Normal", "Sluggish", "Weak"])

        user_id = st.text_input("Your ID", "user_001")
        notes = st.text_area("Additional Notes", "")
        submitted = st.form_submit_button("🤖 Analyze & Generate Recommendations", type="primary")

        if submitted:
            try:
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                pain_locs = ",".join(pain_locations) if pain_locations else "None"
                cursor.execute(f"""
                    INSERT INTO BODY_CONDITION_LOG
                    (USER_ID, LOG_DATE, COLD_INTENSITY, COUGH_TYPE, COUGH_SEVERITY,
                     PAIN_LOCATIONS, PAIN_SEVERITY, PIMPLE_COUNT, SWEATING_LEVEL,
                     SPUTUM_COLOR, URINE_COLOR, ENERGY_LEVEL, DIGESTION_QUALITY, NOTES)
                    VALUES
                    ('{user_id}', CURRENT_DATE(), {cold}, '{cough}', {cough_severity},
                     '{pain_locs}', {pain_severity}, {pimple_count}, '{sweating}',
                     '{sputum}', '{urine}', {energy}, '{digestion}', '{notes}')
                """)
                cursor.close()
                conn.close()
                st.success("✅ Body condition logged!")

                with st.spinner("🤖 AI analyzing symptoms..."):
                    body_condition = {
                        'cold': cold, 'cough': cough, 'cough_severity': cough_severity,
                        'pain_locations': pain_locs, 'pain_severity': pain_severity,
                        'pimple_count': pimple_count, 'energy': energy, 'digestion': digestion,
                        'sweating': sweating, 'sputum': sputum, 'urine': urine
                    }
                    dosha_result = classify_dosha_with_cortex(body_condition)

                    if dosha_result:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Primary Dosha", f"{dosha_result['primary_dosha']}")
                            st.metric("Primary %", f"{dosha_result['dosha_percent']}%")
                        with col2:
                            st.metric("Secondary Dosha", f"{dosha_result.get('secondary_dosha', 'None')}")
                            st.metric("Secondary %", f"{dosha_result.get('secondary_percent', 0)}%")
                        with col3:
                            confidence = dosha_result.get('confidence', 0.8)
                            if isinstance(confidence, str):
                                confidence = float(confidence)
                            st.metric("Confidence", f"{confidence:.0%}")

                        st.info(f"📋 **Analysis:** {dosha_result['summary']}")

                        # Fetch matching herbs from Snowflake
                        herbs = get_herbs_for_dosha(dosha_result['primary_dosha'])

                        if herbs:
                            st.markdown("---")
                            st.subheader(f"🌿 Matching Medicinal Herbs for {dosha_result['primary_dosha']} Balance")
                            st.write(f"Found **{len(herbs)} herbs** from database that reduce {dosha_result['primary_dosha']}:")
                            for h in herbs:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']} | Confidence: {h['score']}/10")

                        # Get season
                        try:
                            conn = get_snowflake_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT SEASON FROM V_TODAY_DOSHA_RECOMMENDATION")
                            season_result = cursor.fetchone()
                            cursor.close()
                            conn.close()
                            season = season_result[0] if season_result else "Monsoon"
                        except:
                            season = "Monsoon"

                        # Generate recipes with herbs
                        with st.spinner("🤖 Generating herb-enhanced recipes..."):
                            recipes = generate_recipes_with_cortex(dosha_result, season, energy, herbs)

                            if recipes:
                                st.markdown("---")
                                st.subheader("☀️ Breakfast")
                                st.markdown(f"**{recipes['breakfast']['name']}**")
                                st.write(f"📝 **Ingredients:** {recipes['breakfast']['ingredients']}")
                                st.write(f"🌿 **Medicinal Herbs:** {recipes['breakfast']['medicinal_herbs']}")
                                st.write(f"🧪 **Herb Preparation:** {recipes['breakfast'].get('herb_preparation', 'As directed')}")
                                st.write(f"💪 **Health Benefits:** {recipes['breakfast']['nutritional_benefits']}")
                                st.write(f"✨ **Why This Dish:** {recipes['breakfast']['why_this_dish']}")
                                st.write(f"⏱️ **Prep Time:** {recipes['breakfast']['prep_time']}")

                                st.markdown("---")
                                st.subheader("🌞 Lunch")
                                st.markdown(f"**{recipes['lunch']['name']}**")
                                st.write(f"📝 **Ingredients:** {recipes['lunch']['ingredients']}")
                                st.write(f"🌿 **Medicinal Herbs:** {recipes['lunch']['medicinal_herbs']}")
                                st.write(f"🧪 **Herb Preparation:** {recipes['lunch'].get('herb_preparation', 'As directed')}")
                                st.write(f"💪 **Health Benefits:** {recipes['lunch']['nutritional_benefits']}")
                                st.write(f"✨ **Why This Dish:** {recipes['lunch']['why_this_dish']}")
                                st.write(f"⏱️ **Prep Time:** {recipes['lunch']['prep_time']}")

                                st.markdown("---")
                                st.subheader("🌙 Dinner")
                                st.markdown(f"**{recipes['dinner']['name']}**")
                                st.write(f"📝 **Ingredients:** {recipes['dinner']['ingredients']}")
                                st.write(f"🌿 **Medicinal Herbs:** {recipes['dinner']['medicinal_herbs']}")
                                st.write(f"🧪 **Herb Preparation:** {recipes['dinner'].get('herb_preparation', 'As directed')}")
                                st.write(f"💪 **Health Benefits:** {recipes['dinner']['nutritional_benefits']}")
                                st.write(f"✨ **Why This Dish:** {recipes['dinner']['why_this_dish']}")
                                st.write(f"⏱️ **Prep Time:** {recipes['dinner']['prep_time']}")

                                st.markdown("---")
                                st.subheader("🛒 Shopping List")
                                total_cost = recipes.get('total_cost', '0')
                                if recipes.get('shopping_list'):
                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.write("**Item**")
                                    col2.write("**Qty**")
                                    col3.write("**Unit**")
                                    col4.write("**Price**")
                                    for item in recipes['shopping_list']:
                                        col1, col2, col3, col4 = st.columns(4)
                                        col1.write(item.get('item', ''))
                                        col2.write(str(item.get('quantity', '')))
                                        col3.write(item.get('unit', ''))
                                        col4.write(str(item.get('price_estimate', '')))
                                st.metric("Total Cost", f"₹{total_cost}")
                                st.info(f"💡 **Wellness Notes:** {recipes.get('wellness_notes', 'Personalized meal plan with medicinal herbs.')}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "👶 Kids Nutrition":
    st.title("👶 Healthy Kids Nutrition with Medicinal Herbs")
    st.markdown("Authentic Tamil recipes with kid-safe Siddha herbs - better than junk food!")

    col1, col2 = st.columns(2)
    with col1:
        child_age = st.selectbox("Child's Age", ["2-3 years", "4-6 years", "7-10 years", "11+ years"])
        age_mapping = {"2-3 years": "2-3", "4-6 years": "4-6", "7-10 years": "7-10", "11+ years": "11+"}
        age_value = age_mapping[child_age]
    with col2:
        dosha_type = st.selectbox("Dosha Type (if known)", ["Not Sure", "Vata", "Pitta", "Kapha"])

    st.markdown("---")
    st.subheader("📚 Available Tamil Dishes")
    st.write("🍽️ Vaazhapoo Sambar | Manathakkali Keerai Sambar | Kathirikai Murungakkai Sambar")
    st.write("🍽️ Vegetable Biryani | Toor Dall Tadka | Potato Fry | Sundakkai Kadaisal")
    st.write("🍽️ Murungakkai Poriyal | Cauliflower Pakora | Vendakkai Poriyal")

    st.markdown("---")
    st.subheader("🌿 Kid-Safe Medicinal Herbs from Database")
    all_herbs = get_all_herbs()
    kid_safe_count = 0
    for row in all_herbs:
        safe = row[10]
        min_age = row[11]
        age_num = int(age_value.split("-")[0])
        if safe and min_age <= age_num:
            kid_safe_count += 1
            st.write(f"🌱 **{row[0]}** ({row[1]}) - {row[3]} | Min age: {min_age}yr | Score: {row[12]}/10")
    st.write(f"**Total kid-safe herbs for age {child_age}: {kid_safe_count}**")

    st.markdown("---")

    if st.button("🤖 Get Personalized Herb-Enhanced Meal Plan", type="primary"):
        herbs = []
        for row in all_herbs:
            herbs.append({
                "english": row[0], "tamil": row[1], "part": row[2], "uses": row[3],
                "preparation": row[8] if len(row) > 8 else "", "season": row[9] if len(row) > 9 else "",
                "safe_kids": row[10] if len(row) > 10 else True, "min_age": row[11] if len(row) > 11 else 2,
                "score": row[12] if len(row) > 12 else 7
            })

        with st.spinner("🤖 Creating herb-enhanced meal plan for your child..."):
            kids_recipes = generate_kids_recipes_with_cortex(age_value, dosha_type, herbs)

            if kids_recipes:
                st.success("✅ Personalized meal plan created with medicinal herbs!")

                st.subheader("☀️ Breakfast")
                st.markdown(f"**{kids_recipes['breakfast']['name']}**")
                st.write(f"📝 **Ingredients:** {kids_recipes['breakfast']['ingredients']}")
                st.write(f"💪 **Health Benefits:** {kids_recipes['breakfast']['health_benefits']}")
                st.write(f"🌿 **Medicinal Herbs:** {kids_recipes['breakfast']['medicinal_herbs']}")
                st.write(f"🧪 **Herb Preparation:** {kids_recipes['breakfast'].get('herb_preparation', 'As directed')}")
                st.write(f"😋 **Taste:** {kids_recipes['breakfast']['taste_profile']}")
                st.write(f"📏 **Portion:** {kids_recipes['breakfast'].get('portion_size', 'Age-appropriate')}")
                st.write(f"⏱️ **Prep Time:** {kids_recipes['breakfast']['prep_time']}")
                st.info(f"✨ **Why Better Than Junk:** {kids_recipes['breakfast']['why_better_than_junk']}")

                st.markdown("---")

                st.subheader("🌞 Lunch")
                st.markdown(f"**{kids_recipes['lunch']['name']}**")
                st.write(f"📝 **Ingredients:** {kids_recipes['lunch']['ingredients']}")
                st.write(f"💪 **Health Benefits:** {kids_recipes['lunch']['health_benefits']}")
                st.write(f"🌿 **Medicinal Herbs:** {kids_recipes['lunch']['medicinal_herbs']}")
                st.write(f"🧪 **Herb Preparation:** {kids_recipes['lunch'].get('herb_preparation', 'As directed')}")
                st.write(f"😋 **Taste:** {kids_recipes['lunch']['taste_profile']}")
                st.write(f"📏 **Portion:** {kids_recipes['lunch'].get('portion_size', 'Age-appropriate')}")
                st.write(f"⏱️ **Prep Time:** {kids_recipes['lunch']['prep_time']}")
                st.info(f"✨ **Why Better Than Junk:** {kids_recipes['lunch']['why_better_than_junk']}")

                st.markdown("---")

                st.subheader("🌙 Dinner")
                st.markdown(f"**{kids_recipes['dinner']['name']}**")
                st.write(f"📝 **Ingredients:** {kids_recipes['dinner']['ingredients']}")
                st.write(f"💪 **Health Benefits:** {kids_recipes['dinner']['health_benefits']}")
                st.write(f"🌿 **Medicinal Herbs:** {kids_recipes['dinner']['medicinal_herbs']}")
                st.write(f"🧪 **Herb Preparation:** {kids_recipes['dinner'].get('herb_preparation', 'As directed')}")
                st.write(f"😋 **Taste:** {kids_recipes['dinner']['taste_profile']}")
                st.write(f"📏 **Portion:** {kids_recipes['dinner'].get('portion_size', 'Age-appropriate')}")
                st.write(f"⏱️ **Prep Time:** {kids_recipes['dinner']['prep_time']}")
                st.info(f"✨ **Why Better Than Junk:** {kids_recipes['dinner']['why_better_than_junk']}")

                st.markdown("---")
                st.subheader("👨‍👩‍👧 Parental Guidance")
                st.write(kids_recipes.get('parental_guidance', 'Introduce herbs gradually.'))
                st.subheader("📊 Nutritional Summary")
                st.write(kids_recipes.get('nutritional_summary', 'Supports healthy development.'))

elif page == "🌿 Herb Database":
    st.title("🌿 Tamil Medicinal Herbs Database")
    st.markdown("30 Siddha/Ayurvedic herbs from Snowflake MEDICINAL_HERBS table")

    search = st.text_input("Search herb (English or Tamil name)", "")
    dosha_filter = st.selectbox("Filter by Dosha Balance", ["All", "Vata", "Pitta", "Kapha"])

    all_herbs = get_all_herbs()

    if all_herbs:
        st.write(f"**Total herbs in database: {len(all_herbs)}**")
        st.markdown("---")

        for row in all_herbs:
            english = row[0] or ""
            tamil = row[1] or ""
            part = row[2] or ""
            uses = row[3] or ""
            vata = row[4] or ""
            pitta = row[5] or ""
            kapha = row[6] or ""
            diseases = row[7] or ""
            preparation = row[8] or ""
            season = row[9] or ""
            safe_kids = row[10]
            min_age = row[11] or 2
            score = row[12] or 7

            if search and search.lower() not in english.lower() and search.lower() not in tamil.lower():
                continue

            if dosha_filter == "Vata" and vata != "Decrease":
                continue
            if dosha_filter == "Pitta" and pitta != "Decrease":
                continue
            if dosha_filter == "Kapha" and kapha != "Decrease":
                continue

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"### 🌱 {english}")
                st.write(f"**Tamil:** {tamil}")
                st.write(f"**Part Used:** {part}")
                st.write(f"**Season:** {season}")
                st.write(f"**Score:** {score}/10")
                kids_text = f"✅ Safe (age {min_age}+)" if safe_kids else "❌ Not recommended"
                st.write(f"**Kids:** {kids_text}")
            with col2:
                st.write(f"**Uses:** {uses}")
                st.write(f"**Diseases:** {diseases}")
                st.write(f"**Preparation:** {preparation}")
                st.write(f"**Dosha:** Vata {vata} | Pitta {pitta} | Kapha {kapha}")
            st.markdown("---")
    else:
        st.warning("No herbs found. Run MEDICINAL_HERBS_SCHEMA.sql in Snowflake first.")

elif page == "📊 Feedback":
    st.title("📊 How Was Yesterday?")
    st.markdown("Your feedback helps Claude improve recommendations")

    with st.form("feedback_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**☀️ Breakfast**")
            breakfast_rating = st.slider("Breakfast Rating", 1, 5, 3, key="br")
            breakfast_comment = st.text_area("Notes", "", key="bc")
        with col2:
            st.write("**🌞 Lunch**")
            lunch_rating = st.slider("Lunch Rating", 1, 5, 3, key="lr")
            lunch_comment = st.text_area("Notes", "", key="lc")
        with col3:
            st.write("**🌙 Dinner**")
            dinner_rating = st.slider("Dinner Rating", 1, 5, 3, key="dr")
            dinner_comment = st.text_area("Notes", "", key="dc")

        st.markdown("---")
        energy_today = st.slider("Energy Level Today", 1, 10, 5)
        digestion_today = st.selectbox("Digestion Quality Today", ["Good", "Normal", "Sluggish", "Weak"])
        overall_satisfaction = st.slider("Overall Satisfaction", 1, 5, 3)
        user_id = st.text_input("Your ID", "user_001")

        submitted = st.form_submit_button("Submit Feedback", type="primary")
        if submitted:
            try:
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO USER_FEEDBACK
                    (USER_ID, RECOMMENDATION_DATE, FEEDBACK_DATE, BREAKFAST_RATING, LUNCH_RATING, DINNER_RATING,
                     OVERALL_SATISFACTION, ENERGY_LEVEL_NEXT_DAY, DIGESTION_QUALITY)
                    VALUES
                    ('{user_id}', CURRENT_DATE() - 1, CURRENT_DATE(), {breakfast_rating}, {lunch_rating},
                     {dinner_rating}, {overall_satisfaction}, {energy_today}, '{digestion_today}')
                """)
                cursor.close()
                conn.close()
                st.success("✅ Feedback recorded!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
