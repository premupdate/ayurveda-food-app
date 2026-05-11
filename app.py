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
    for key in ['SUPABASE_HOST','SUPABASE_DB','SUPABASE_PORT','SUPABASE_USER','SUPABASE_PASSWORD','GEMINI_API_KEY']:
        val = st.secrets.get(key, os.getenv(key, ''))
        if val: os.environ[key] = val

st.set_page_config(page_title="Tamil Ayurvedic Platform", layout="wide")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gm = genai.GenerativeModel('gemini-2.5-flash')

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
            r2 = gm.generate_content(prompt + "\n\nCRITICAL: Return ONLY valid JSON. No text before or after. No markdown.")
            t2 = r2.text.strip()
            if "```json" in t2: t2 = t2.split("```json")[1].split("```")[0]
            elif "```" in t2: t2 = t2.split("```")[1].split("```")[0]
            return json.loads(t2.strip())
        except: return None
    except: return None

def weather(loc="Chennai"):
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

def get_districts():
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT district_id,district_name,district_tamil,primary_land_id,primary_land,secondary_land,weather_location FROM district_land_mapping ORDER BY district_name")
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def get_pincodes(district):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT pincode,area_name,area_name_tamil,specific_land,elevation_category,weather_location,notes FROM pincode_land_mapping WHERE district_name=%s ORDER BY pincode",(district,))
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def get_land_details(lid):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT name_tamil,name_english,land_type,description_english FROM ainthinai_lands WHERE land_id=%s",(lid,))
        r = cur.fetchone(); cur.close(); c.close(); return r
    except: return None

def get_flora(lid, skw):
    try:
        c = db(); cur = c.cursor()
        cur.execute("SELECT flora_type,name_tamil,name_english,name_botanical,category,seasonal_availability,medicinal_uses,culinary_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s AND (seasonal_availability='Year-round' OR seasonal_availability ILIKE %s) ORDER BY flora_type",(lid,f"%{skw}%"))
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
        cur.execute("SELECT condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs FROM user_health_profile WHERE user_id=%s AND is_active=TRUE ORDER BY created_at DESC",(uid,))
        r = cur.fetchall(); cur.close(); c.close(); return r
    except: return []

def save_health_conditions(uid, conditions):
    try:
        c = db(); cur = c.cursor()
        for cond in conditions:
            cur.execute("INSERT INTO user_health_profile (user_id,condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (uid,cond.get('name',''),cond.get('category',''),cond.get('severity',''),cond.get('dietary_impact',''),cond.get('avoid_herbs',''),cond.get('recommended_herbs','')))
        c.commit(); cur.close(); c.close(); return True
    except: return False

land_icons = {"Kurinji":"🏔️","Mullai":"🌳","Marutham":"🌾","Neidhal":"🌊","Palai":"🏜️"}

# ==================== SIDEBAR ====================
st.sidebar.title("🌿 Tamil Ayurvedic Platform")
districts = get_districts()
d_names = [d[1] for d in districts]
if 'dist' not in st.session_state: st.session_state.dist = "Theni"
sel_dist = st.sidebar.selectbox("📍 District",d_names,index=d_names.index(st.session_state.dist) if st.session_state.dist in d_names else 0)
st.session_state.dist = sel_dist

d_info = None
for d in districts:
    if d[1]==sel_dist: d_info=d; break

# Pincode selector - type any pincode OR choose from list
pincodes = get_pincodes(sel_dist)
pin_info = None

typed_pin = st.sidebar.text_input("📮 Enter Pincode", "", placeholder="e.g., 625531")

if typed_pin.strip():
    # Check if pincode exists in database
    found = None
    for p in pincodes:
        if p[0] == typed_pin.strip():
            found = p
            break
    
    if found:
        pin_info = found
        specific_land = pin_info[3]
        weather_loc = pin_info[5]
        st.sidebar.success(f"📍 **{pin_info[1]}** ({pin_info[2]})")
        st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **Land:** {specific_land} ({pin_info[4]})")
        if pin_info[6]:
            st.sidebar.markdown(f"📝 {pin_info[6]}")
    else:
        # AI classifies unknown pincode
        with st.sidebar.status("🤖 AI identifying area..."):
            pin_result = ai(f"""Indian geography expert. Pincode {typed_pin} in {sel_dist} district, Tamil Nadu.
Identify the area and classify which Ainthinai land it belongs to.
Ainthinai options: Kurinji (mountains/hills), Mullai (forest/pastoral), Marutham (agricultural plains), Neidhal (coastal), Palai (arid/desert)

Return JSON: {{"area_name": "Name of area", "area_name_tamil": "Tamil name", "specific_land": "Kurinji or Mullai or Marutham or Neidhal or Palai", "elevation": "Plains or Foothills or Hills or Coastal or Dry Plains", "latitude": 10.5, "longitude": 77.5, "weather_location": "Nearest city for weather", "notes": "Brief description of the area"}}""")
            
            if pin_result:
                specific_land = pin_result.get('specific_land', d_info[4] if d_info else 'Marutham')
                weather_loc = pin_result.get('weather_location', d_info[6] if d_info else 'Chennai')
                
                st.sidebar.success(f"📍 **{pin_result.get('area_name', 'Unknown')}** ({pin_result.get('area_name_tamil', '')})")
                st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **Land:** {specific_land} ({pin_result.get('elevation', '')})")
                st.sidebar.markdown(f"📝 {pin_result.get('notes', '')}")
                
                # Save to database for future use
                try:
                    conn = db(); cur = conn.cursor()
                    cur.execute("INSERT INTO pincode_land_mapping (pincode, area_name, area_name_tamil, district_name, specific_land, elevation_category, latitude, longitude, weather_location, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (typed_pin, pin_result.get('area_name',''), pin_result.get('area_name_tamil',''), sel_dist, specific_land, pin_result.get('elevation',''), pin_result.get('latitude',0), pin_result.get('longitude',0), weather_loc, pin_result.get('notes','')))
                    conn.commit(); cur.close(); conn.close()
                    st.sidebar.info("✅ Saved! Next time this pincode loads instantly.")
                except:
                    pass
                
                pin_info = (typed_pin, pin_result.get('area_name',''), pin_result.get('area_name_tamil',''), specific_land, pin_result.get('elevation',''), weather_loc, pin_result.get('notes',''))
            else:
                specific_land = d_info[4] if d_info else "Marutham"
                weather_loc = d_info[6] if d_info else "Chennai"
                st.sidebar.warning(f"Could not identify pincode. Using district default: {specific_land}")

elif pincodes:
    st.sidebar.markdown("**Or choose from known areas:**")
    pin_labels = [f"{p[0]} - {p[1]} ({p[3]})" for p in pincodes]
    sel_pin_idx = st.sidebar.selectbox("Known Areas", range(len(pin_labels)), format_func=lambda i: pin_labels[i])
    pin_info = pincodes[sel_pin_idx]
    specific_land = pin_info[3]
    weather_loc = pin_info[5]
    st.sidebar.markdown(f"📍 **{pin_info[1]}** ({pin_info[2]})")
    st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **Land:** {specific_land} ({pin_info[4]})")
else:
    specific_land = d_info[4] if d_info else "Marutham"
    weather_loc = d_info[6] if d_info else "Chennai"
    st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **Land:** {specific_land}")

# Map specific_land to land_id
land_id_map = {"Kurinji":1,"Mullai":2,"Marutham":3,"Neidhal":4,"Palai":5}
current_land_id = land_id_map.get(specific_land, 3)

w = weather(weather_loc)
ts = tamil_season()
skw = season_kw(ts[1])

st.sidebar.markdown("---")
st.sidebar.markdown(f"🌦️ **{ts[0]}** ({ts[1].split('(')[0].strip()})")
st.sidebar.markdown(f"   Dosha: {ts[2]}")
st.sidebar.markdown(f"🌤️ **{w['temp']}°C** | {w['desc']}")
st.sidebar.markdown(f"   Humidity: {w['humidity']}%")
st.sidebar.markdown("---")
st.sidebar.markdown("🆓 100% FREE Platform")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate",["👨‍🍳 Adult","👶 Kids","🏔️ Ainthinai","🌦️ Seasons","🌿 Herbs","🔧 Admin","📊 Feedback"])

# ==================== ADULT PAGE ====================
if page=="👨‍🍳 Adult":
    st.title("🌿 Daily Body Condition Check")
    
    # Context bar
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("📍 Location",pin_info[1] if pin_info else sel_dist)
    col2.metric(f"{land_icons.get(specific_land,'🌍')} Land",f"{specific_land}")
    col3.metric("🌦️ Season",ts[1].split("(")[0].strip())
    col4.metric("🌤️ Weather",f"{w['temp']}°C")
    
    # Local flora
    local_flora = get_flora(current_land_id, skw)
    if local_flora:
        ft = ", ".join([f[2] for f in local_flora[:8]])
        st.info(f"🌿 **Available now in {specific_land} during {ts[1]}:** {ft}")

    st.markdown("---")
    
    with st.form("body"):
        col1,col2 = st.columns(2)
        with col1:
            st.header("Symptoms")
            cold = st.slider("Cold/Runny Nose",0,5,0)
            cough = st.selectbox("Cough",["None","Dry","Wet"])
            cough_sev = st.slider("Cough Severity",0,5,0)
            pain = st.multiselect("Pain",["Head","Neck","Joints","Abdomen","Chest","Back","None"])
            pain_sev = st.slider("Pain Severity",0,5,0)
            pimples = st.number_input("Pimples",0,100,0)
        with col2:
            st.header("Body State")
            sweating = st.selectbox("Sweating",["Normal","Excessive"])
            sputum = st.selectbox("Sputum",["Clear","Yellow","Green"])
            urine = st.selectbox("Urine",["Pale","Amber","Dark"])
            energy = st.slider("Energy",1,10,5)
            digestion = st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"])
        
        st.markdown("---")
        st.header("📝 Your Health Conditions")
        st.markdown("Tell AI about chronic conditions, allergies, medications, pregnancy, etc.")
        
        user_id = st.text_input("Your ID","user_001")
        
        # Show existing health profile
        existing = get_health_profile(user_id)
        if existing:
            st.markdown("**⚠️ Conditions already on file:**")
            for ex in existing:
                st.write(f"• **{ex[0]}** ({ex[1]}) - {ex[2]} | Diet: {ex[3]}")
        
        health_notes = st.text_area("Describe your health conditions (AI will parse and remember)","",height=100,
            placeholder="Example: I have Type 2 diabetes for 5 years, taking Metformin. Mild knee arthritis. Wife is 6 months pregnant. Child has lactose intolerance.")
        
        if st.form_submit_button("🤖 Analyze with Full Context",type="primary"):
            try:
                conn = db(); cur = conn.cursor()
                pain_locs = ",".join(pain) if pain else "None"
                pincode_val = pin_info[0] if pin_info else ""
                cur.execute("INSERT INTO body_condition_log (user_id,log_date,cold_intensity,cough_type,cough_severity,pain_locations,pain_severity,pimple_count,sweating_level,sputum_color,urine_color,energy_level,digestion_quality,weather_condition,health_notes,pincode,specific_land) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id,date.today(),cold,cough,cough_sev,pain_locs,pain_sev,pimples,sweating,sputum,urine,energy,digestion,f"{weather_loc} {w['temp']}C {w['desc']}",health_notes,pincode_val,specific_land))
                conn.commit(); cur.close(); conn.close()
                st.success("✅ Logged with location + health data!")
                
                # Parse health notes with AI
                parsed_conditions = []
                if health_notes.strip():
                    with st.spinner("🤖 Parsing health conditions..."):
                        parsed = ai(f"""Medical analyst. Parse health conditions from: "{health_notes}"
Return JSON: {{"conditions": [{{"name": "Condition", "category": "Metabolic/Musculoskeletal/Reproductive/Allergy/Recent", "severity": "Mild/Moderate/Severe", "dietary_impact": "Diet restrictions", "avoid_herbs": "Herbs to avoid", "recommended_herbs": "Herbs that help"}}]}}""")
                        if parsed and parsed.get('conditions'):
                            parsed_conditions = parsed['conditions']
                            save_health_conditions(user_id, parsed_conditions)
                            st.markdown("---")
                            st.subheader("⚠️ Health Conditions Detected & Saved:")
                            for pc in parsed_conditions:
                                st.write(f"• **{pc.get('name','')}** ({pc.get('category','')}) - {pc.get('severity','')}")
                                st.write(f"  🍽️ Diet: {pc.get('dietary_impact','')}")
                                st.write(f"  ❌ Avoid: {pc.get('avoid_herbs','')}")
                                st.write(f"  ✅ Recommended: {pc.get('recommended_herbs','')}")
                
                # Build full health context
                all_conditions = existing + [(pc.get('name',''),pc.get('category',''),pc.get('severity',''),pc.get('dietary_impact',''),pc.get('avoid_herbs',''),pc.get('recommended_herbs','')) for pc in parsed_conditions]
                health_context = ""
                avoid_herbs = ""
                recommend_herbs = ""
                if all_conditions:
                    health_context = "\n".join([f"- {c[0]} ({c[1]}): {c[2]}. Diet: {c[3]}" for c in all_conditions])
                    avoid_herbs = ", ".join([c[4] for c in all_conditions if c[4]])
                    recommend_herbs = ", ".join([c[5] for c in all_conditions if c[5]])
                
                body = {'cold':cold,'cough':cough,'cough_severity':cough_sev,'pain_locations':pain_locs,'pain_severity':pain_sev,'pimple_count':pimples,'energy':energy,'digestion':digestion,'sweating':sweating,'sputum':sputum,'urine':urine}
                
                # Classify dosha
                with st.spinner("🤖 Classifying dosha..."):
                    dosha = ai(f"""Tamil Siddha expert. Consider body, land, season, weather, AND health conditions.
Body: {json.dumps(body)}
Location: {pin_info[1] if pin_info else sel_dist} ({specific_land} land, {pin_info[4] if pin_info else 'Plains'})
Season: {ts[1]} (Dominant: {ts[2]})
Weather: {w['temp']}C, Humidity {w['humidity']}%, {w['desc']}
Health Conditions: {health_context if health_context else 'None reported'}

Return JSON: {{"primary_dosha":"Vata/Pitta/Kapha","dosha_percent":75,"secondary_dosha":"X","secondary_percent":25,"confidence":0.9,"summary":"Include land+season+health impact","weather_impact":"Weather effect","season_impact":"Season effect","land_impact":"Land effect","health_impact":"How conditions affect recommendation"}}""")
                    
                    if dosha:
                        col1,col2,col3 = st.columns(3)
                        col1.metric("Dosha",f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        col2.metric("Secondary",dosha.get('secondary_dosha','None'))
                        conf=dosha.get('confidence',0.8)
                        if isinstance(conf,str): conf=float(conf)
                        col3.metric("Confidence",f"{conf:.0%}")
                        
                        st.info(f"📋 {dosha['summary']}")
                        st.info(f"🌤️ Weather: {dosha.get('weather_impact','')}")
                        st.info(f"🌦️ Season: {dosha.get('season_impact','')}")
                        st.info(f"🏔️ Land: {dosha.get('land_impact','')}")
                        if dosha.get('health_impact'):
                            st.warning(f"⚠️ Health: {dosha.get('health_impact','')}")
                        
                        herbs = get_herbs_dosha(dosha['primary_dosha'])
                        if herbs:
                            st.markdown("---")
                            st.subheader(f"🌿 {len(herbs)} Matching Herbs")
                            for h in herbs[:6]:
                                st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']}")
                        
                        if local_flora:
                            st.markdown("---")
                            st.subheader(f"🌾 Local Flora in {specific_land}")
                            for f in local_flora[:6]:
                                ti={"Herb":"🌱","Flower":"🌸","Fruit":"🍎","Tree":"🌳","Grain":"🌾"}.get(f[0],"🌿")
                                st.write(f"{ti} **{f[2]}** ({f[1]}) - {f[6]}")
                        
                        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in herbs[:8]])
                        flora_text = "\n".join([f"- {f[2]}: {f[6]} | Cook: {f[7]}" for f in local_flora[:8]])
                        
                        with st.spinner("🤖 Generating hyper-local recipes..."):
                            recipes = ai(f"""Tamil Ayurvedic chef. HYPER-LOCAL recipes using locally available ingredients.
Dosha: {dosha['primary_dosha']} ({dosha['dosha_percent']}%)
Location: {pin_info[1] if pin_info else sel_dist} ({specific_land}, {pin_info[4] if pin_info else 'Plains'})
Season: {ts[1]}, Weather: {w['temp']}C {w['desc']}
Energy: {energy}/10

HEALTH CONDITIONS (MUST RESPECT):
{health_context if health_context else 'None'}
AVOID these herbs/foods: {avoid_herbs if avoid_herbs else 'None'}
PREFER these herbs: {recommend_herbs if recommend_herbs else 'Any matching dosha'}

Dosha herbs: {herbs_text}
Local flora: {flora_text}

CRITICAL: Recipes MUST be safe for user's health conditions. Flag any concerns.

Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","herb_preparation":"X","why_local":"Why from this land","why_seasonal":"Why this season","health_safety":"Safe for conditions or warnings","nutritional_benefits":"X","dosha_fit":"X"}},"lunch":{{"name":"X","ingredients":"X","prep_time":"20min","medicinal_herbs":"X","herb_preparation":"X","why_local":"X","why_seasonal":"X","health_safety":"X","nutritional_benefits":"X","dosha_fit":"X"}},"dinner":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","herb_preparation":"X","why_local":"X","why_seasonal":"X","health_safety":"X","nutritional_benefits":"X","dosha_fit":"X"}},"health_warnings":"Any specific warnings for this user","wellness_notes":"Overall benefits"}}""")
                            
                            if recipes:
                                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                                    st.markdown("---")
                                    st.subheader(f"{mi} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 {recipes[meal]['ingredients']}")
                                    st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 {recipes[meal].get('herb_preparation','')}")
                                    st.write(f"📍 {recipes[meal].get('why_local','')}")
                                    st.write(f"🌦️ {recipes[meal].get('why_seasonal','')}")
                                    st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                                    hs = recipes[meal].get('health_safety','')
                                    if hs and 'warning' in hs.lower():
                                        st.warning(f"⚠️ {hs}")
                                    elif hs:
                                        st.success(f"✅ {hs}")
                                st.markdown("---")
                                if recipes.get('health_warnings'):
                                    st.warning(f"⚠️ **Health Note:** {recipes['health_warnings']}")
                                st.info(f"💡 {recipes.get('wellness_notes','')}")
            except Exception as e:
                st.error(str(e))

# ==================== KIDS PAGE ====================
elif page=="👶 Kids":
    st.title("👶 Kids Nutrition")
    st.markdown(f"📍 {pin_info[1] if pin_info else sel_dist} ({specific_land}) | 🌦️ {ts[1]} | 🌤️ {w['temp']}°C")
    col1,col2 = st.columns(2)
    with col1: age = st.selectbox("Age",["2-3","4-6","7-10","11+"])
    with col2: kid_dosha = st.selectbox("Dosha",["Not Sure","Vata","Pitta","Kapha"])
    
    all_h = get_all_herbs()
    herbs = [{"english":r[0],"tamil":r[1],"uses":r[3],"prep":r[8] if len(r)>8 else "","safe_kids":r[10] if len(r)>10 else True,"min_age":r[11] if len(r)>11 else 2} for r in all_h]
    kid_herbs = [h for h in herbs if h.get('safe_kids',True) and h.get('min_age',2)<=int(age.split("-")[0])]
    local_flora = get_flora(current_land_id, skw)
    
    if st.button("🤖 Get Local Meal Plan",type="primary"):
        ht = "\n".join([f"- {h['english']}: {h['uses']}" for h in kid_herbs[:8]])
        ft = "\n".join([f"- {f[2]}: {f[6]}" for f in local_flora[:6]])
        with st.spinner("Creating..."):
            kids = ai(f"""Tamil pediatric nutritionist. Child {age}yr, Dosha {kid_dosha}.
Location: {pin_info[1] if pin_info else sel_dist} ({specific_land}), Season: {ts[1]}
Local flora: {ft}
Kid herbs: {ht}
Use LOCAL seasonal ingredients. Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"15min"}},"lunch":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"20min"}},"dinner":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"15min"}},"parental_guidance":"X"}}""")
            if kids:
                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                    st.markdown("---"); st.subheader(f"{mi} {meal.title()}")
                    st.markdown(f"**{kids[meal]['name']}**")
                    st.write(f"📝 {kids[meal]['ingredients']}"); st.write(f"💪 {kids[meal]['health_benefits']}")
                    st.write(f"🌿 {kids[meal]['medicinal_herbs']}"); st.write(f"📍 {kids[meal].get('why_local','')}")
                    st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance','')}")

# ==================== AINTHINAI PAGE ====================
elif page=="🏔️ Ainthinai":
    st.title("🏔️ ஐந்திணை - Five Lands")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT * FROM ainthinai_lands ORDER BY land_id")
        lands=cur.fetchall()
        tabs=st.tabs([f"{land_icons.get(l[2],'🌍')} {l[1]} ({l[2]})" for l in lands])
        for i,land in enumerate(lands):
            with tabs[i]:
                col1,col2=st.columns(2)
                with col1:
                    st.subheader(f"{land[1]} - {land[2]}"); st.write(f"**{land[5]}**")
                    st.write(f"🙏 Deity: {land[6]} ({land[7]})"); st.write(f"🌸 Flower: {land[8]} ({land[9]})")
                    st.write(f"🌳 Tree: {land[10]} ({land[11]})")
                with col2:
                    st.write(f"👷 Occupation: {land[12]}"); st.write(f"🍚 Food: {land[14]}")
                    st.write(f"💕 Emotion: {land[16]}"); st.write(f"📍 Districts: {land[18]}")
                st.markdown("---"); st.subheader("🌿 Flora")
                cur.execute("SELECT flora_type,name_tamil,name_english,medicinal_uses,culinary_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s",(land[0],))
                for f in cur.fetchall():
                    ti={"Herb":"🌱","Flower":"🌸","Fruit":"🍎","Tree":"🌳","Grain":"🌾"}.get(f[0],"🌿")
                    st.write(f"{ti} **{f[2]}** ({f[1]}) | {f[3]} | Cook: {f[4]} | Dosha: {f[5]}")
                st.markdown("---"); st.subheader("📍 Districts & Pincodes")
                cur.execute("SELECT district_name,district_tamil FROM district_land_mapping WHERE primary_land=%s ORDER BY district_name",(land[2],))
                for d in cur.fetchall(): st.write(f"📍 {d[0]} ({d[1]})")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== SEASONS PAGE ====================
elif page=="🌦️ Seasons":
    st.title("🌦️ Tamil Seasons")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT * FROM tamil_seasons ORDER BY season_id")
        seasons=cur.fetchall()
        icons=["☀️","🔥","🌧️","🍂","❄️","🌸"]
        cur_ts=ts[0]
        for i,s in enumerate(seasons):
            ic=icons[i] if i<len(icons) else "🌤️"
            is_cur=cur_ts==s[1]
            with st.expander(f"{ic} {s[1]} - {s[2]} ({s[4]})" + (" ← NOW" if is_cur else ""),expanded=is_cur):
                col1,col2=st.columns(2)
                with col1: st.write(f"**Months:** {s[3]}"); st.write(f"**Weather:** {s[6]}"); st.write(f"**Dosha:** {s[7]}"); st.write(f"**Food:** {s[8]}")
                with col2: st.write(f"🌿 **Herbs:** {s[9]}"); st.write(f"🍎 **Fruits:** {s[10]}"); st.write(f"🌸 **Flowers:** {s[11]}"); st.write(f"🌾 **Farming:** {s[12]}")
        cur.close();c.close()
        st.success(f"📅 Now: {ts[0]} - {ts[1]} | Dosha: {ts[2]}")
    except Exception as e: st.error(str(e))

# ==================== HERBS PAGE ====================
elif page=="🌿 Herbs":
    st.title("🌿 Herbs Database")
    search=st.text_input("Search",""); df=st.selectbox("Dosha",["All","Vata","Pitta","Kapha"])
    for r in get_all_herbs():
        e,t,p,u=r[0] or "",r[1] or "",r[2] or "",r[3] or ""
        v,pi,k=r[4] or "",r[5] or "",r[6] or ""
        if search and search.lower() not in e.lower() and search.lower() not in t.lower(): continue
        if df!="All" and {"Vata":v,"Pitta":pi,"Kapha":k}[df]!="Decrease": continue
        col1,col2=st.columns([1,2])
        with col1: st.markdown(f"### 🌱 {e}"); st.write(f"**{t}** | {p} | Score: {r[12] or 7}/10")
        with col2: st.write(f"{u} | V:{v} P:{pi} K:{k}")
        st.markdown("---")

# ==================== ADMIN PAGE ====================
elif page=="🔧 Admin":
    st.title("🔧 Admin")
    tab=st.radio("Add:",["🌿 Herb","🍽️ Dish"])
    if tab=="🌿 Herb":
        with st.form("herb"):
            col1,col2=st.columns(2)
            with col1: ht=st.text_input("Tamil *"); he=st.text_input("English *"); hb=st.text_input("Botanical"); hp=st.selectbox("Part",["Leaves","Root","Seed","Flower","Bark","Fruit","Whole plant","Rhizome"]); hu=st.text_area("Uses *"); hd=st.text_area("Diseases")
            with col2: hv=st.selectbox("Vata",["Decrease","Increase","Neutral"]); hpi=st.selectbox("Pitta",["Decrease","Increase","Neutral"]); hk=st.selectbox("Kapha",["Decrease","Increase","Neutral"]); hpr=st.text_input("Preparation"); hs=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]); hkid=st.checkbox("Safe Kids",True); hage=st.number_input("Min Age",1,18,3); hsc=st.slider("Score",1,10,7)
            if st.form_submit_button("✅ Add",type="primary") and ht and he and hu:
                try:
                    c=db();cur=c.cursor()
                    cur.execute("INSERT INTO medicinal_herbs (name_tamil,name_english,name_botanical,plant_part,vata_effect,pitta_effect,kapha_effect,primary_uses,diseases_treated,preparation_methods,seasonal_availability,safe_for_kids,min_age_years,data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(ht,he,hb,hp,hv,hpi,hk,hu,hd,hpr,hs,hkid,hage,hsc))
                    c.commit();cur.close();c.close();st.success(f"✅ '{he}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    else:
        with st.form("dish"):
            dn=st.text_input("Name *"); dd=st.selectbox("Dosha",["Vata","Pitta","Kapha","Neutral"]); ds=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]); di=st.text_area("Instructions")
            if st.form_submit_button("✅ Add",type="primary") and dn:
                try:
                    c=db();cur=c.cursor()
                    cur.execute("INSERT INTO recipes (recipe_name,primary_ingredient_id,serves,prep_time_min,dosha_suitability,seasonal_best,instructions) VALUES (%s,1,4,20,%s,%s,%s)",(dn,dd,ds,di))
                    c.commit();cur.close();c.close();st.success(f"✅ '{dn}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    st.markdown("---")
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT COUNT(*) FROM medicinal_herbs");h=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recipes");r=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM body_condition_log");l=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM pincode_land_mapping");p=cur.fetchone()[0]
        cur.close();c.close()
        col1,col2,col3,col4=st.columns(4)
        col1.metric("🌿 Herbs",h);col2.metric("🍽️ Dishes",r);col3.metric("📋 Logs",l);col4.metric("📮 Pincodes",p)
    except: pass

# ==================== FEEDBACK PAGE ====================
elif page=="📊 Feedback":
    st.title("📊 Smart Feedback")
    with st.form("fb"):
        col1,col2,col3=st.columns(3)
        with col1: br=st.slider("Breakfast",1,5,3,key="br")
        with col2: lr=st.slider("Lunch",1,5,3,key="lr")
        with col3: dr=st.slider("Dinner",1,5,3,key="dr")
        energy=st.slider("Energy",1,10,5); digestion=st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"])
        st.markdown("---"); st.subheader("📝 What Did You Eat?")
        notes=st.text_area("AI extracts dishes, herbs, vegetables","",height=100)
        user_id=st.text_input("ID","user_001")
        if st.form_submit_button("Submit",type="primary"):
            try:
                c=db();cur=c.cursor()
                cur.execute("INSERT INTO user_feedback (user_id,recommendation_date,feedback_date,breakfast_rating,lunch_rating,dinner_rating,energy_level_next_day,digestion_quality) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(user_id,date.today(),date.today(),br,lr,dr,energy,digestion))
                c.commit();st.success("✅ Saved!")
                if notes.strip():
                    with st.spinner("🤖 Parsing..."):
                        parsed=ai(f"""Parse: "{notes}". Return JSON: {{"dish_name":"X","vegetables":["v1"],"herbs":["h1"],"spices":["s1"],"dosha_assessment":"X","health_benefits":"X"}}""")
                        if parsed:
                            st.write(f"🍽️ **Dish:** {parsed.get('dish_name','')}"); st.write(f"🥬 **Veg:** {', '.join(parsed.get('vegetables',[]))}")
                            st.write(f"🌿 **Herbs:** {', '.join(parsed.get('herbs',[]))}"); st.write(f"⚖️ **Dosha:** {parsed.get('dosha_assessment','')}")
                            try:
                                cur.execute("INSERT INTO feedback_parsed_items (user_id,original_note,parsed_dish_name,parsed_herbs,parsed_vegetables,dosha_assessment) VALUES (%s,%s,%s,%s,%s,%s)",
                                    (user_id,notes,parsed.get('dish_name',''),json.dumps(parsed.get('herbs',[])),json.dumps(parsed.get('vegetables',[])),parsed.get('dosha_assessment','')))
                                c.commit();st.success("✅ Parsed & saved!")
                            except: pass
                cur.close();c.close()
            except Exception as e: st.error(str(e))
