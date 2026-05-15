import streamlit as st
import psycopg2
import os
from datetime import date, timedelta
import json
import requests
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass
if hasattr(st, 'secrets'):
    for key in ['SUPABASE_HOST','SUPABASE_DB','SUPABASE_PORT','SUPABASE_USER','SUPABASE_PASSWORD','GEMINI_API_KEY']:
        val = st.secrets.get(key, os.getenv(key, ''))
        if val: os.environ[key] = val

st.set_page_config(page_title="Tamil Ayurvedic Platform", layout="wide")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gm = genai.GenerativeModel('gemini-2.5-flash')

# ==================== CORE FUNCTIONS ====================
def db():
    return psycopg2.connect(host=os.getenv('SUPABASE_HOST'),database=os.getenv('SUPABASE_DB'),port=os.getenv('SUPABASE_PORT'),user=os.getenv('SUPABASE_USER'),password=os.getenv('SUPABASE_PASSWORD'))

def ai(prompt):
    try:
        r = gm.generate_content(prompt)
        if not r or not r.text: return None
        t = r.text.strip()
        if "```json" in t: t = t.split("```json")[1].split("```")[0]
        elif "```" in t: t = t.split("```")[1].split("```")[0]
        t = t.strip()
        if not t: return None
        return json.loads(t)
    except json.JSONDecodeError:
        try:
            r2 = gm.generate_content(prompt + "\n\nCRITICAL: Return ONLY valid JSON.")
            t2 = r2.text.strip()
            if "```json" in t2: t2 = t2.split("```json")[1].split("```")[0]
            elif "```" in t2: t2 = t2.split("```")[1].split("```")[0]
            return json.loads(t2.strip())
        except: return None
    except: return None

def get_weather(loc="Chennai"):
    try:
        r = requests.get(f"https://wttr.in/{loc}?format=j1",timeout=5).json()
        c = r['current_condition'][0]
        return {"temp":c['temp_C'],"humidity":c['humidity'],"desc":c['weatherDesc'][0]['value'],"feels":c['FeelsLikeC']}
    except: return {"temp":"32","humidity":"65","desc":"Partly Cloudy","feels":"35"}

def tamil_season():
    m = date.today().month
    s = {4:("இளவேனில்","Ilavenil (Early Summer)","Pitta"),5:("இளவேனில்","Ilavenil (Early Summer)","Pitta"),6:("முதுவேனில்","Mudhuvenil (Late Summer)","Pitta/Vata"),7:("முதுவேனில்","Mudhuvenil (Late Summer)","Pitta/Vata"),8:("கார்","Kaar (Monsoon)","Vata"),9:("கார்","Kaar (Monsoon)","Vata"),10:("கூதிர்","Koothir (Autumn)","Vata/Kapha"),11:("கூதிர்","Koothir (Autumn)","Vata/Kapha"),12:("முன்பனி","Munpani (Early Winter)","Kapha"),1:("முன்பனி","Munpani (Early Winter)","Kapha"),2:("பின்பனி","Pinpani (Late Winter)","Kapha/Pitta"),3:("பின்பனி","Pinpani (Late Winter)","Kapha/Pitta")}
    return s.get(m,("கார்","Kaar","Vata"))

def season_kw(s):
    if "Summer" in s: return "Summer"
    elif "Monsoon" in s: return "Monsoon"
    elif "Winter" in s: return "Winter"
    elif "Autumn" in s: return "Monsoon"
    return "Year-round"

def lookup_pincode(pincode):
    try:
        resp = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", timeout=10)
        r = resp.json()
        if r and r[0].get('Status')=='Success' and r[0].get('PostOffice'):
            po = r[0]['PostOffice'][0]
            return {"area":po.get('Name',''),"district":po.get('District',''),"state":po.get('State','')}
    except: pass
    return None

def get_pincode_land(pincode):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT pincode,area_name,area_name_tamil,specific_land,elevation_category,weather_location,notes FROM pincode_land_mapping WHERE pincode=%s",(pincode,))
        r = cur.fetchone(); cur.close(); c.close(); return r
    except: return None

def classify_and_save_pincode(pincode, api_data):
    lr = ai(f"""Geography expert. {api_data['area']}, {api_data['district']}, Tamil Nadu. Pincode {pincode}.
Ainthinai: Kurinji(mountains), Mullai(forest), Marutham(plains), Neidhal(coastal), Palai(arid).
Return JSON: {{"area_name":"{api_data['area']}","area_name_tamil":"Tamil","specific_land":"X","elevation":"Plains/Foothills/Hills/Coastal","weather_location":"{api_data['district']}","notes":"Brief"}}""")
    if lr:
        try:
            c = db(); cur = c.cursor()
            cur.execute("INSERT INTO pincode_land_mapping (pincode,area_name,area_name_tamil,district_name,specific_land,elevation_category,weather_location,notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (pincode,lr.get('area_name',''),lr.get('area_name_tamil',''),api_data['district'],lr.get('specific_land','Marutham'),lr.get('elevation',''),lr.get('weather_location',api_data['district']),lr.get('notes','')))
            c.commit(); cur.close(); c.close()
        except: pass
    return lr

def get_flora(lid, skw):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT flora_type,name_tamil,name_english,name_botanical,category,seasonal_availability,medicinal_uses,culinary_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s AND (seasonal_availability='Year-round' OR seasonal_availability ILIKE %s)",(lid,f"%{skw}%"))
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def get_herbs_dosha(dosha):
    try:
        c = db(); cur = c.cursor()
        cur.execute(f"SELECT name_english,name_tamil,plant_part,primary_uses,diseases_treated,preparation_methods,seasonal_availability,safe_for_kids,min_age_years,data_confidence_score FROM medicinal_herbs WHERE {dosha.lower()}_effect='Decrease' ORDER BY data_confidence_score DESC LIMIT 10")
        r = cur.fetchall(); cur.close(); c.close()
        return [{"english":x[0],"tamil":x[1],"part":x[2],"uses":x[3],"diseases":x[4],"prep":x[5],"season":x[6],"safe_kids":x[7],"min_age":x[8],"score":x[9]} for x in r]
    except: return []

def get_all_herbs():
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT name_english,name_tamil,plant_part,primary_uses,vata_effect,pitta_effect,kapha_effect,diseases_treated,preparation_methods,seasonal_availability,safe_for_kids,min_age_years,data_confidence_score FROM medicinal_herbs ORDER BY data_confidence_score DESC")
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def get_health_profile(uid):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs FROM user_health_profile WHERE user_id=%s AND is_active=TRUE",(uid,))
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def save_health_conditions(uid, conds):
    try:
        c = db(); cur = c.cursor()
        for co in conds:
            cur.execute("INSERT INTO user_health_profile (user_id,condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (uid,co.get('name',''),co.get('category',''),co.get('severity',''),co.get('dietary_impact',''),co.get('avoid_herbs',''),co.get('recommended_herbs','')))
        c.commit(); cur.close(); c.close()
    except: pass

def get_user_profiles():
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT user_name,pincode,area_name,district,specific_land FROM user_profiles WHERE is_active=TRUE ORDER BY user_name")
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def get_user_scores(uid, days=7):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT feedback_date,daily_health_score,junk_count,energy_level FROM feedback_detailed WHERE user_id=%s AND feedback_date >= %s ORDER BY feedback_date DESC",(uid,date.today()-timedelta(days=days)))
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def save_discovered_food(food_name, food_type, user, symptom, dosha, land, season):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT food_id,times_mentioned,associated_symptoms FROM discovered_foods WHERE food_name=%s",(food_name,))
        existing = cur.fetchone()
        if existing:
            new_count = existing[1] + 1
            symptoms = existing[2] or ""
            if symptom and symptom not in symptoms:
                symptoms = f"{symptoms}, {symptom}" if symptoms else symptom
            cur.execute("UPDATE discovered_foods SET times_mentioned=%s,associated_symptoms=%s,last_mentioned=%s WHERE food_id=%s",(new_count,symptoms,date.today(),existing[0]))
        else:
            cur.execute("INSERT INTO discovered_foods (food_name,food_type,discovered_by,associated_symptoms,dosha_assessment,land_discovered,season_discovered) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (food_name,food_type,user,symptom,dosha,land,season))
        c.commit(); cur.close(); c.close()
    except: pass

def save_remedy(food, ingredient, symptom, dosha, land, season, helped):
    if not symptom or not food: return
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT remedy_id,times_reported,times_helped,times_partial,times_not_helped FROM remedy_mapping WHERE food_name=%s AND symptom=%s",(food,symptom))
        ex = cur.fetchone()
        if ex:
            tr = ex[1]+1
            th = ex[2]+(1 if helped=="Yes" else 0)
            tp = ex[3]+(1 if helped=="Partially" else 0)
            tn = ex[4]+(1 if helped=="No" else 0)
            eff = round((th/tr)*100,1) if tr>0 else 0
            cur.execute("UPDATE remedy_mapping SET times_reported=%s,times_helped=%s,times_partial=%s,times_not_helped=%s,effectiveness_percent=%s,last_reported=%s WHERE remedy_id=%s",(tr,th,tp,tn,eff,date.today(),ex[0]))
        else:
            th = 1 if helped=="Yes" else 0
            cur.execute("INSERT INTO remedy_mapping (food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s)",
                (food,ingredient,symptom,dosha,land,season,th,th*100))
        c.commit(); cur.close(); c.close()
    except: pass

land_icons = {"Kurinji":"🏔️","Mullai":"🌳","Marutham":"🌾","Neidhal":"🌊","Palai":"🏜️"}
land_id_map = {"Kurinji":1,"Mullai":2,"Marutham":3,"Neidhal":4,"Palai":5}

# ==================== SIDEBAR ====================
st.sidebar.title("🌿 Tamil Ayurvedic Platform")

# User selector
users = get_user_profiles()
user_names = [u[0] for u in users]
user_names.insert(0, "➕ New User")

sel_user = st.sidebar.selectbox("👤 Select User", user_names)

if sel_user == "➕ New User":
    with st.sidebar.expander("Register New User", expanded=True):
        new_name = st.text_input("Your Name", "", key="newname")
        new_pin = st.text_input("Your Pincode", "", key="newpin", placeholder="625531")
        if st.button("✅ Register", key="regbtn"):
            if new_name and new_pin and len(new_pin)==6:
                api = lookup_pincode(new_pin)
                area = api['area'] if api else ""
                dist = api['district'] if api else ""
                db_pin = get_pincode_land(new_pin)
                land = db_pin[3] if db_pin else "Marutham"
                try:
                    c = db(); cur = c.cursor()
                    cur.execute("INSERT INTO user_profiles (user_name,pincode,area_name,district,specific_land) VALUES (%s,%s,%s,%s,%s)",(new_name,new_pin,area,dist,land))
                    c.commit(); cur.close(); c.close()
                    st.sidebar.success(f"✅ {new_name} registered!")
                    st.rerun()
                except: st.sidebar.warning("Name already exists")
            else: st.sidebar.warning("Enter name and 6-digit pincode")
    typed_pin = new_pin if 'new_pin' in dir() and new_pin else ""
    pin_area = ""; pin_district = ""; specific_land = "Marutham"; weather_loc = "Chennai"
    current_user = new_name if 'new_name' in dir() else "guest"
else:
    current_user = sel_user
    user_data = None
    for u in users:
        if u[0] == sel_user: user_data = u; break
    typed_pin = user_data[1] if user_data else ""
    pin_area = user_data[2] if user_data else ""
    pin_district = user_data[3] if user_data else ""
    specific_land = user_data[4] if user_data else "Marutham"

    if typed_pin:
        db_pin = get_pincode_land(typed_pin)
        weather_loc = db_pin[5] if db_pin else pin_district if pin_district else "Chennai"
        st.sidebar.markdown(f"📍 **{pin_area}**, {pin_district}")
        st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **{specific_land}**")
    else:
        weather_loc = "Chennai"

current_land_id = land_id_map.get(specific_land, 3)
w = get_weather(weather_loc)
ts = tamil_season()
skw = season_kw(ts[1])

st.sidebar.markdown("---")
st.sidebar.markdown(f"🌦️ {ts[0]} ({ts[1].split('(')[0].strip()}) | {ts[2]}")
st.sidebar.markdown(f"🌤️ {w['temp']}°C | {w['desc']} | 💧{w['humidity']}%")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate",["📝 Daily Food Log","🍽️ Discovered Foods","🏥 Remedy Map","👨‍🍳 Recommendations","👶 Kids","🏔️ Ainthinai","🌦️ Seasons","🌿 Herbs","🔧 Admin"])

# ==================== PAGE 1: DAILY FOOD LOG ====================
if page=="📝 Daily Food Log":
    st.title(f"📝 Daily Food Log")

    if current_user and current_user != "➕ New User" and current_user != "guest":
        # HEALTH DASHBOARD
        scores = get_user_scores(current_user)
        if scores:
            st.subheader(f"👋 Welcome back, {current_user}!")
            last_score = scores[0][1] if scores[0][1] else 5
            avg_score = round(sum(s[1] for s in scores if s[1])/len([s for s in scores if s[1]]),1) if scores else 0
            best_score = max(s[1] for s in scores if s[1]) if [s for s in scores if s[1]] else 0
            streak = len(scores)
            total_junk = sum(s[2] for s in scores if s[2])

            col1,col2,col3,col4,col5 = st.columns(5)
            col1.metric("🏥 Last Score", f"{last_score}/10")
            col2.metric("📊 Avg (7 days)", f"{avg_score}/10")
            col3.metric("⭐ Best", f"{best_score}/10")
            col4.metric("🔥 Streak", f"{streak} days")
            col5.metric("🍟 Junk (week)", total_junk)

            # Trend
            if len(scores) > 1:
                st.markdown("**📈 Recent Trend:**")
                for s in reversed(scores):
                    d = s[0].strftime("%a %d") if s[0] else "?"
                    sc = s[1] if s[1] else 0
                    jk = s[2] if s[2] else 0
                    bar = "⭐" * sc
                    junk_warn = f" (🍟×{jk})" if jk > 0 else ""
                    st.write(f"{d}: {bar} ({sc}/10){junk_warn}")

            if avg_score >= 7: st.success("🌟 You're doing amazing! Keep up the traditional food habits!")
            elif avg_score >= 5: st.info("👍 Good progress! Reducing junk will push you higher.")
            else: st.warning("⚠️ More traditional food, less junk = better health!")
            st.markdown("---")
        else:
            st.subheader(f"👋 Welcome, {current_user}! Start logging your food to see your health score.")
    else:
        st.info("👆 Select or register a user in the sidebar")

    # Context bar
    if pin_area:
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("📍", pin_area)
        col2.metric(f"{land_icons.get(specific_land,'🌍')}", specific_land)
        col3.metric("🌦️", ts[1].split("(")[0].strip())
        col4.metric("🌤️", f"{w['temp']}°C")

    st.markdown("---")
    st.markdown("*Log what you eat daily. AI learns from your choices!*")

    with st.form("food_log"):
        st.subheader("☀️ Morning (Breakfast)")
        mn = st.text_area("What & WHY:","",height=70,key="mn",placeholder="Had thulasi kadaisal for running nose")
        col1,col2 = st.columns(2)
        with col1: mr = st.slider("Rating",1,5,3,key="mr")
        with col2: mh = st.selectbox("Helped?",["Yes","Partially","No","Not for health"],key="mh")

        st.markdown("---")
        st.subheader("🌞 Afternoon (Lunch)")
        an = st.text_area("What & WHY:","",height=70,key="an",placeholder="Manathakkali sambar for stomach pain")
        col1,col2 = st.columns(2)
        with col1: ar = st.slider("Rating",1,5,3,key="ar")
        with col2: ah = st.selectbox("Helped?",["Yes","Partially","No","Not for health"],key="ah")

        st.markdown("---")
        st.subheader("🌙 Evening (Dinner)")
        en = st.text_area("What & WHY:","",height=70,key="en",placeholder="Ragi porridge with honey for weakness")
        col1,col2 = st.columns(2)
        with col1: er = st.slider("Rating",1,5,3,key="er")
        with col2: eh = st.selectbox("Helped?",["Yes","Partially","No","Not for health"],key="eh")

        st.markdown("---")
        st.subheader("🍟 Snacks & Junk Food")
        st.markdown("⚠️ Be honest! AI shows impact & Tamil alternatives")
        jn = st.text_area("Junk/snacks:","",height=70,key="jn",placeholder="Chips at 11am, pepsi, kids had kurkure")

        st.markdown("---")
        col1,col2,col3,col4 = st.columns(4)
        with col1: fe = st.slider("Energy",1,10,5,key="fe")
        with col2: fd = st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"],key="fd")
        with col3: fsl = st.selectbox("Sleep",["Good","Normal","Disturbed","Poor"],key="fsl")
        with col4: fmo = st.selectbox("Mood",["Happy","Normal","Tired","Irritable"],key="fmo")

        if st.form_submit_button("🤖 Submit & Let AI Learn",type="primary"):
            has_meals = mn.strip() or an.strip() or en.strip()
            has_junk = jn.strip()

            meal_results = {}
            if has_meals:
                with st.spinner("🤖 Parsing meals..."):
                    for slot,txt,rating,helped in [("morning",mn,mr,mh),("afternoon",an,ar,ah),("evening",en,er,eh)]:
                        if txt.strip():
                            p = ai(f"""Tamil food analyst. Parse: "{txt}". Location: {pin_area} ({specific_land}). Season: {ts[1]}.
Return JSON: {{"dishes":[{{"name":"Dish","dish_type":"Type","vegetables":["v"],"leaves_greens":["l"],"herbs":["h"],"spices":["s"],"grains":["g"],"symptom_treated":"Symptom","symptom_dosha":"Dosha"}}],"overall_dosha_impact":"Impact","ai_note":"Siddha insight"}}""")
                            meal_results[slot] = p
                            # Save to discovered_foods and remedy_mapping
                            if p and p.get('dishes'):
                                for dish in p['dishes']:
                                    dn = dish.get('name','')
                                    if dn:
                                        save_discovered_food(dn,"Dish",current_user,dish.get('symptom_treated',''),dish.get('symptom_dosha',''),specific_land,ts[1])
                                        if dish.get('symptom_treated'):
                                            ingr = ", ".join(dish.get('herbs',[])+dish.get('leaves_greens',[]))
                                            save_remedy(dn,ingr,dish['symptom_treated'],dish.get('symptom_dosha',''),specific_land,ts[1],helped)
                                    for v in dish.get('vegetables',[]):
                                        save_discovered_food(v,"Vegetable",current_user,"","",specific_land,ts[1])
                                    for l in dish.get('leaves_greens',[]):
                                        save_discovered_food(l,"Leaf/Green",current_user,"","",specific_land,ts[1])
                                    for h in dish.get('herbs',[]):
                                        save_discovered_food(h,"Herb",current_user,"","",specific_land,ts[1])
                                    for g in dish.get('grains',[]):
                                        save_discovered_food(g,"Grain",current_user,"","",specific_land,ts[1])

            junk_result = None; junk_count = 0
            if has_junk:
                with st.spinner("🤖 Analyzing junk..."):
                    junk_result = ai(f"""Nutritionist. Junk: "{jn}". Location: {pin_area} ({specific_land}).
Return JSON: {{"items":[{{"name":"Item","calories":"est","sugar_g":"est","dosha_impact":"impact","healing_interference":"effect","consumed_by":"Adult/Kids/Both","tamil_alternative":"replacement","alternative_benefit":"why"}}],"total_junk_count":3,"daily_health_reduction_percent":35,"kids_impact":"impact","overall_message":"advice"}}""")
                    if junk_result: junk_count = junk_result.get('total_junk_count',0)

            mc = sum(1 for s in ["morning","afternoon","evening"] if s in meal_results)
            hc = sum(1 for h in [mh,ah,eh] if h=="Yes")
            hs = min(10,max(1,(mc*2)+(hc*2)-(junk_count)+(fe//3)))

            try:
                conn=db();cur=conn.cursor()
                cur.execute("""INSERT INTO feedback_detailed (user_id,feedback_date,pincode,area_name,specific_land,tamil_season,weather_condition,morning_notes,morning_rating,morning_helped,morning_parsed,afternoon_notes,afternoon_rating,afternoon_helped,afternoon_parsed,evening_notes,evening_rating,evening_helped,evening_parsed,junk_notes,junk_parsed,junk_count,energy_level,digestion,sleep_quality,mood,daily_health_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (current_user,date.today(),typed_pin,f"{pin_area}, {pin_district}",specific_land,ts[1],f"{w['temp']}C {w['desc']}",mn,mr,mh,json.dumps(meal_results.get('morning')),an,ar,ah,json.dumps(meal_results.get('afternoon')),en,er,eh,json.dumps(meal_results.get('evening')),jn,json.dumps(junk_result),junk_count,fe,fd,fsl,fmo,hs))
                conn.commit();cur.close();conn.close()
                st.success("✅ Food log saved! AI is learning!")
            except Exception as e: st.warning(f"Save: {e}")

            # Display results
            st.markdown("---"); st.title("🤖 AI Analysis")
            for slot,icon,txt,rating,helped in [("morning","☀️",mn,mr,mh),("afternoon","🌞",an,ar,ah),("evening","🌙",en,er,eh)]:
                if slot in meal_results and meal_results[slot]:
                    st.markdown("---"); st.subheader(f"{icon} {slot.title()}")
                    mr2 = meal_results[slot]
                    if mr2.get('dishes'):
                        for dish in mr2['dishes']:
                            st.markdown(f"**📌 {dish.get('name','')}** ({dish.get('dish_type','')})")
                            parts = []
                            if dish.get('vegetables'): parts.append(f"🥬 {', '.join(dish['vegetables'])}")
                            if dish.get('leaves_greens'): parts.append(f"🌿 {', '.join(dish['leaves_greens'])}")
                            if dish.get('herbs'): parts.append(f"🌱 {', '.join(dish['herbs'])}")
                            if dish.get('spices'): parts.append(f"🌶️ {', '.join(dish['spices'])}")
                            if dish.get('grains'): parts.append(f"🌾 {', '.join(dish['grains'])}")
                            for p in parts: st.write(p)
                            if dish.get('symptom_treated'): st.write(f"🤒 **For:** {dish['symptom_treated']}")
                            eff={"Yes":"✅","Partially":"⚠️","No":"❌"}.get(helped,"ℹ️")
                            st.write(f"{eff} {helped} | {'⭐'*rating}")
                    if mr2.get('ai_note'): st.info(f"💡 {mr2['ai_note']}")

            if junk_result and junk_result.get('items'):
                st.markdown("---"); st.subheader("🍟 Junk Impact")
                for item in junk_result['items']:
                    st.markdown(f"**⚠️ {item.get('name','')}**")
                    st.write(f"⚖️ {item.get('dosha_impact','')}"); st.warning(f"🔄 {item.get('healing_interference','')}")
                    st.success(f"🌿 Alternative: {item.get('tamil_alternative','')} → {item.get('alternative_benefit','')}")
                if junk_result.get('overall_message'): st.info(f"💡 {junk_result['overall_message']}")

            st.markdown("---"); st.subheader("📊 Today's Score")
            col1,col2,col3 = st.columns(3)
            col1.metric("🏥 Score",f"{hs}/10"); col2.metric("🟢 Meals",f"{mc}/3"); col3.metric("🔴 Junk",junk_count)

# ==================== PAGE 2: DISCOVERED FOODS ====================
elif page=="🍽️ Discovered Foods":
    st.title("🍽️ Discovered Foods (Auto-Growing)")
    st.markdown("Every food logged by users appears here automatically!")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT food_name,food_type,discovered_by,times_mentioned,associated_symptoms,dosha_assessment,land_discovered,season_discovered,first_discovered,last_mentioned FROM discovered_foods ORDER BY last_mentioned DESC")
        foods = cur.fetchall(); cur.close(); c.close()
        if foods:
            st.write(f"**Total: {len(foods)} foods discovered!**")
            type_filter = st.selectbox("Filter by type",["All","Dish","Vegetable","Leaf/Green","Herb","Grain","Spice"])
            for f in foods:
                if type_filter!="All" and f[1]!=type_filter: continue
                ti={"Dish":"🍽️","Vegetable":"🥬","Leaf/Green":"🌿","Herb":"🌱","Grain":"🌾","Spice":"🌶️"}.get(f[1],"🍽️")
                col1,col2 = st.columns([1,2])
                with col1:
                    st.markdown(f"### {ti} {f[0]}")
                    st.write(f"**Type:** {f[1]} | **Mentioned:** {f[3]}x")
                    st.write(f"**By:** {f[2]} | **First:** {f[8]}")
                with col2:
                    if f[4]: st.write(f"🤒 **For:** {f[4]}")
                    if f[5]: st.write(f"⚖️ **Dosha:** {f[5]}")
                    if f[6]: st.write(f"📍 **Land:** {f[6]} | **Season:** {f[7]}")
                st.markdown("---")
        else:
            st.info("No foods discovered yet. Log meals in Daily Food Log to start!")
    except Exception as e: st.error(str(e))

# ==================== PAGE 3: REMEDY MAP ====================
elif page=="🏥 Remedy Map":
    st.title("🏥 Remedy Map (Community-Learned)")
    st.markdown("What food works for what symptom? Learned from real user feedback!")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT DISTINCT symptom FROM remedy_mapping ORDER BY symptom")
        symptoms = [s[0] for s in cur.fetchall()]
        if symptoms:
            sel_symptom = st.selectbox("🤒 Select Symptom", ["All"] + symptoms)
            if sel_symptom == "All":
                cur.execute("SELECT food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent FROM remedy_mapping ORDER BY effectiveness_percent DESC")
            else:
                cur.execute("SELECT food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent FROM remedy_mapping WHERE symptom=%s ORDER BY effectiveness_percent DESC",(sel_symptom,))
            remedies = cur.fetchall()
            if remedies:
                st.write(f"**{len(remedies)} remedies found**")
                for r in remedies:
                    eff = r[8] if r[8] else 0
                    eff_icon = "🟢" if eff>=80 else "🟡" if eff>=50 else "🔴"
                    col1,col2 = st.columns([1,2])
                    with col1:
                        st.markdown(f"### {eff_icon} {r[0]}")
                        st.write(f"**Effectiveness:** {eff}%")
                        st.write(f"**Reported:** {r[6]}x | Helped: {r[7]}x")
                    with col2:
                        st.write(f"🤒 **For:** {r[2]}")
                        if r[1]: st.write(f"🌱 **Key:** {r[1]}")
                        st.write(f"⚖️ {r[3]} | 📍 {r[4]} | 🌦️ {r[5]}")
                    st.markdown("---")
            else:
                st.info("No remedies for this symptom yet.")
        else:
            st.info("No remedies mapped yet. Log meals with symptoms in Daily Food Log!")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 4: RECOMMENDATIONS ====================
elif page=="👨‍🍳 Recommendations":
    st.title("🌿 Get Personalized Recommendations")
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("📍",pin_area if pin_area else "Set pincode"); col2.metric(f"{land_icons.get(specific_land,'🌍')}",specific_land)
    col3.metric("🌦️",ts[1].split("(")[0].strip()); col4.metric("🌤️",f"{w['temp']}°C")
    local_flora = get_flora(current_land_id, skw)
    if local_flora: st.info(f"🌿 **Available:** {', '.join([f[2] for f in local_flora[:8]])}")
    st.markdown("---")
    with st.form("body"):
        col1,col2 = st.columns(2)
        with col1:
            cold=st.slider("Cold",0,5,0);cough=st.selectbox("Cough",["None","Dry","Wet"]);cough_sev=st.slider("Cough Severity",0,5,0)
            pain=st.multiselect("Pain",["Head","Neck","Joints","Abdomen","Chest","Back","None"]);pain_sev=st.slider("Pain Severity",0,5,0)
            pimples=st.number_input("Pimples",0,100,0)
        with col2:
            sweating=st.selectbox("Sweating",["Normal","Excessive"]);sputum=st.selectbox("Sputum",["Clear","Yellow","Green"]);urine=st.selectbox("Urine",["Pale","Amber","Dark"])
            energy=st.slider("Energy",1,10,5);digestion=st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"])
        st.markdown("---")
        existing = get_health_profile(current_user)
        if existing:
            st.markdown("**⚠️ On file:**")
            for ex in existing: st.write(f"• {ex[0]} ({ex[1]})")
        health_notes = st.text_area("Health conditions","",height=70,placeholder="Diabetes, knee pain, etc.")
        if st.form_submit_button("🤖 Get Recommendations",type="primary"):
            try:
                conn=db();cur=conn.cursor();pain_locs=",".join(pain) if pain else "None"
                cur.execute("INSERT INTO body_condition_log (user_id,log_date,cold_intensity,cough_type,cough_severity,pain_locations,pain_severity,pimple_count,sweating_level,sputum_color,urine_color,energy_level,digestion_quality,weather_condition,health_notes,pincode,specific_land) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (current_user,date.today(),cold,cough,cough_sev,pain_locs,pain_sev,pimples,sweating,sputum,urine,energy,digestion,f"{weather_loc} {w['temp']}C",health_notes,typed_pin,specific_land))
                conn.commit();cur.close();conn.close()

                if health_notes.strip():
                    parsed = ai(f"""Parse: "{health_notes}". Return JSON: {{"conditions":[{{"name":"X","category":"X","severity":"X","dietary_impact":"X","avoid_herbs":"X","recommended_herbs":"X"}}]}}""")
                    if parsed and parsed.get('conditions'): save_health_conditions(current_user, parsed['conditions'])

                all_conds = existing
                health_ctx = "\n".join([f"- {c[0]}: {c[3]}" for c in all_conds]) if all_conds else "None"
                avoid = ", ".join([c[4] for c in all_conds if c[4]]) if all_conds else "None"
                body = {'cold':cold,'cough':cough,'cough_severity':cough_sev,'pain_locations':pain_locs,'energy':energy,'digestion':digestion,'sweating':sweating,'sputum':sputum,'urine':urine}

                with st.spinner("🤖 Dosha..."):
                    dosha = ai(f"""Siddha. Body:{json.dumps(body)}, Location:{pin_area}({specific_land}), Season:{ts[1]}({ts[2]}), Weather:{w['temp']}C, Health:{health_ctx}
Return JSON: {{"primary_dosha":"X","dosha_percent":75,"secondary_dosha":"X","secondary_percent":25,"confidence":0.9,"summary":"Brief","health_impact":"X"}}""")
                    if dosha:
                        col1,col2 = st.columns(2)
                        col1.metric("Dosha",f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        col2.metric("Secondary",dosha.get('secondary_dosha','None'))
                        st.info(f"📋 {dosha['summary']}")
                        herbs = get_herbs_dosha(dosha['primary_dosha'])
                        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in herbs[:8]])
                        flora_text = "\n".join([f"- {f[2]}: {f[6]}" for f in local_flora[:8]])
                        with st.spinner("🤖 Recipes..."):
                            recipes = ai(f"""Tamil chef. Dosha:{dosha['primary_dosha']}({dosha['dosha_percent']}%), Location:{pin_area}({specific_land}), Season:{ts[1]}, Weather:{w['temp']}C, Energy:{energy}/10, Health:{health_ctx}, AVOID:{avoid}
Herbs:{herbs_text}. Flora:{flora_text}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"lunch":{{"name":"X","ingredients":"X","prep_time":"20min","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"dinner":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"wellness_notes":"X"}}""")
                            if recipes:
                                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                                    st.markdown("---"); st.subheader(f"{mi} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 {recipes[meal]['ingredients']}"); st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"📍 {recipes[meal].get('why_local','')}"); st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                                st.info(f"💡 {recipes.get('wellness_notes','')}")
            except Exception as e: st.error(str(e))

# ==================== PAGE 5: KIDS ====================
elif page=="👶 Kids":
    st.title("👶 Kids Nutrition")
    col1,col2 = st.columns(2)
    with col1: age = st.selectbox("Age",["2-3","4-6","7-10","11+"])
    with col2: kd = st.selectbox("Dosha",["Not Sure","Vata","Pitta","Kapha"])
    if st.button("🤖 Get Meal Plan",type="primary"):
        all_h = get_all_herbs()
        kh = [{"english":r[0],"uses":r[3]} for r in all_h if (r[10] if len(r)>10 else True) and (r[11] if len(r)>11 else 2)<=int(age.split("-")[0])]
        ht = "\n".join([f"- {h['english']}: {h['uses']}" for h in kh[:8]])
        fl = get_flora(current_land_id, skw)
        ft = "\n".join([f"- {f[2]}: {f[6]}" for f in fl[:6]])
        with st.spinner("Creating..."):
            kids = ai(f"""Pediatric nutritionist. Child {age}yr, Dosha {kd}. Location: {pin_area} ({specific_land}), Season: {ts[1]}. Flora:{ft}. Herbs:{ht}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X","prep_time":"15min"}},"lunch":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X","prep_time":"20min"}},"dinner":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X","prep_time":"15min"}},"parental_guidance":"X"}}""")
            if kids:
                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                    st.markdown("---"); st.subheader(f"{mi} {meal.title()}")
                    st.markdown(f"**{kids[meal]['name']}**"); st.write(f"📝 {kids[meal]['ingredients']}")
                    st.write(f"💪 {kids[meal]['health_benefits']}"); st.write(f"🌿 {kids[meal]['medicinal_herbs']}")
                    st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance','')}")

# ==================== PAGE 6: AINTHINAI ====================
elif page=="🏔️ Ainthinai":
    st.title("🏔️ ஐந்திணை - Five Lands")
    try:
        c=db();cur=c.cursor(); cur.execute("SELECT * FROM ainthinai_lands ORDER BY land_id"); lands=cur.fetchall()
        tabs=st.tabs([f"{land_icons.get(l[2],'🌍')} {l[1]} ({l[2]})" for l in lands])
        for i,land in enumerate(lands):
            with tabs[i]:
                col1,col2=st.columns(2)
                with col1: st.subheader(f"{land[1]} - {land[2]}"); st.write(f"**{land[5]}**"); st.write(f"🙏 {land[6]} ({land[7]})"); st.write(f"🌸 {land[8]}"); st.write(f"🌳 {land[10]}")
                with col2: st.write(f"👷 {land[12]}"); st.write(f"🍚 {land[14]}"); st.write(f"💕 {land[16]}"); st.write(f"📍 {land[18]}")
                st.markdown("---"); st.subheader("🌿 Flora")
                cur.execute("SELECT flora_type,name_tamil,name_english,medicinal_uses,culinary_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s",(land[0],))
                for f in cur.fetchall():
                    ti={"Herb":"🌱","Flower":"🌸","Fruit":"🍎","Tree":"🌳","Grain":"🌾"}.get(f[0],"🌿")
                    st.write(f"{ti} **{f[2]}** ({f[1]}) | {f[3]} | {f[5]}")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 7: SEASONS ====================
elif page=="🌦️ Seasons":
    st.title("🌦️ Tamil Seasons")
    try:
        c=db();cur=c.cursor(); cur.execute("SELECT * FROM tamil_seasons ORDER BY season_id"); seasons=cur.fetchall()
        icons=["☀️","🔥","🌧️","🍂","❄️","🌸"]
        for i,s in enumerate(seasons):
            ic=icons[i] if i<len(icons) else "🌤️"
            is_cur=ts[0]==s[1]
            with st.expander(f"{ic} {s[1]} - {s[2]} ({s[4]})" + (" ← NOW" if is_cur else ""),expanded=is_cur):
                col1,col2=st.columns(2)
                with col1: st.write(f"**Months:** {s[3]}"); st.write(f"**Dosha:** {s[7]}"); st.write(f"**Food:** {s[8]}")
                with col2: st.write(f"🌿 {s[9]}"); st.write(f"🍎 {s[10]}"); st.write(f"🌸 {s[11]}")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 8: HERBS ====================
elif page=="🌿 Herbs":
    st.title("🌿 Herbs Database")
    search=st.text_input("Search",""); df=st.selectbox("Dosha",["All","Vata","Pitta","Kapha"])
    for r in get_all_herbs():
        e,t,p,u=r[0] or "",r[1] or "",r[2] or "",r[3] or ""
        v,pi,k=r[4] or "",r[5] or "",r[6] or ""
        if search and search.lower() not in e.lower() and search.lower() not in t.lower(): continue
        if df!="All" and {"Vata":v,"Pitta":pi,"Kapha":k}[df]!="Decrease": continue
        col1,col2=st.columns([1,2])
        with col1: st.markdown(f"### 🌱 {e}"); st.write(f"**{t}** | {p} | {r[12] or 7}/10")
        with col2: st.write(f"{u} | V:{v} P:{pi} K:{k}")
        st.markdown("---")

# ==================== PAGE 9: ADMIN ====================
elif page=="🔧 Admin":
    st.title("🔧 Admin")
    tab=st.radio("Add:",["🌿 Herb","🍽️ Dish","👤 Users"])
    if tab=="🌿 Herb":
        with st.form("herb"):
            col1,col2=st.columns(2)
            with col1: ht=st.text_input("Tamil *"); he=st.text_input("English *"); hb=st.text_input("Botanical"); hp=st.selectbox("Part",["Leaves","Root","Seed","Flower","Bark","Fruit","Whole plant","Rhizome"]); hu=st.text_area("Uses *")
            with col2: hv=st.selectbox("Vata",["Decrease","Increase","Neutral"]); hpi=st.selectbox("Pitta",["Decrease","Increase","Neutral"]); hk=st.selectbox("Kapha",["Decrease","Increase","Neutral"]); hpr=st.text_input("Preparation"); hs=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]); hsc=st.slider("Score",1,10,7)
            if st.form_submit_button("✅ Add Herb",type="primary") and ht and he and hu:
                try:
                    c=db();cur=c.cursor()
                    cur.execute("INSERT INTO medicinal_herbs (name_tamil,name_english,name_botanical,plant_part,vata_effect,pitta_effect,kapha_effect,primary_uses,preparation_methods,seasonal_availability,data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(ht,he,hb,hp,hv,hpi,hk,hu,hpr,hs,hsc))
                    c.commit();cur.close();c.close();st.success(f"✅ '{he}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    elif tab=="🍽️ Dish":
        with st.form("dish"):
            dn=st.text_input("Name *"); dd=st.selectbox("Dosha",["Vata","Pitta","Kapha","Neutral"]); ds=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]); di=st.text_area("Instructions")
            if st.form_submit_button("✅ Add Dish",type="primary") and dn:
                try:
                    c=db();cur=c.cursor()
                    cur.execute("INSERT INTO recipes (recipe_name,primary_ingredient_id,serves,prep_time_min,dosha_suitability,seasonal_best,instructions) VALUES (%s,1,4,20,%s,%s,%s)",(dn,dd,ds,di))
                    c.commit();cur.close();c.close();st.success(f"✅ '{dn}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    elif tab=="👤 Users":
        st.subheader("Registered Users")
        for u in get_user_profiles():
            st.write(f"👤 **{u[0]}** | 📮 {u[1]} | 📍 {u[2]}, {u[3]} | {land_icons.get(u[4],'🌍')} {u[4]}")
    st.markdown("---")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT COUNT(*) FROM medicinal_herbs");h=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recipes");r=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM feedback_detailed");f=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM discovered_foods");d=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM remedy_mapping");rm=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_profiles");u=cur.fetchone()[0]
        cur.close();c.close()
        col1,col2,col3 = st.columns(3)
        col1.metric("🌿 Herbs",h); col1.metric("🍽️ Dishes",r)
        col2.metric("📝 Logs",f); col2.metric("🍽️ Foods Found",d)
        col3.metric("🏥 Remedies",rm); col3.metric("👤 Users",u)
    except: pass
