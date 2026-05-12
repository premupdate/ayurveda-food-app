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

def lookup_pincode(pincode):
    try:
        resp = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", timeout=10)
        api_r = resp.json()
        if api_r and api_r[0].get('Status') == 'Success' and api_r[0].get('PostOffice'):
            po = api_r[0]['PostOffice'][0]
            return {"area": po.get('Name',''), "district": po.get('District',''), "state": po.get('State',''), "region": po.get('Region','')}
    except: pass
    return None

land_icons = {"Kurinji":"🏔️","Mullai":"🌳","Marutham":"🌾","Neidhal":"🌊","Palai":"🏜️"}
land_id_map = {"Kurinji":1,"Mullai":2,"Marutham":3,"Neidhal":4,"Palai":5}

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

# Pincode
pincodes = get_pincodes(sel_dist)
pin_info = None
typed_pin = st.sidebar.text_input("📮 Pincode", "", placeholder="e.g., 625531")

if typed_pin.strip() and len(typed_pin.strip()) == 6:
    pincode = typed_pin.strip()
    found = None
    try:
        conn = db(); cur = conn.cursor()
        cur.execute("SELECT pincode,area_name,area_name_tamil,specific_land,elevation_category,weather_location,notes FROM pincode_land_mapping WHERE pincode=%s", (pincode,))
        row = cur.fetchone(); cur.close(); conn.close()
        if row: found = row
    except: pass

    if found:
        pin_info = found
        specific_land = pin_info[3]; weather_loc = pin_info[5]
        st.sidebar.success(f"📍 {pin_info[1]} ({pin_info[2]})")
        st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} {specific_land} ({pin_info[4]})")
    else:
        with st.sidebar.status("🔍 Looking up pincode..."):
            api_data = lookup_pincode(pincode)
            if api_data:
                st.sidebar.info(f"📮 {api_data['area']}, {api_data['district']}")
                land_result = ai(f"""Geography expert. Location: {api_data['area']}, {api_data['district']}, Tamil Nadu. Pincode: {pincode}.
Classify Ainthinai: Kurinji(mountains), Mullai(forest), Marutham(plains), Neidhal(coastal), Palai(arid).
Return JSON: {{"area_name":"{api_data['area']}","area_name_tamil":"Tamil name","specific_land":"Kurinji/Mullai/Marutham/Neidhal/Palai","elevation":"Plains/Foothills/Hills/Coastal/Dry Plains","weather_location":"{api_data['district']}","notes":"Brief terrain description"}}""")
                if land_result:
                    specific_land = land_result.get('specific_land', d_info[4] if d_info else 'Marutham')
                    weather_loc = land_result.get('weather_location', api_data['district'])
                    st.sidebar.success(f"📍 {land_result.get('area_name','')} ({land_result.get('area_name_tamil','')})")
                    st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} {specific_land} ({land_result.get('elevation','')})")
                    try:
                        conn = db(); cur = conn.cursor()
                        cur.execute("INSERT INTO pincode_land_mapping (pincode,area_name,area_name_tamil,district_name,specific_land,elevation_category,weather_location,notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                            (pincode,land_result.get('area_name',''),land_result.get('area_name_tamil',''),api_data['district'],specific_land,land_result.get('elevation',''),weather_loc,land_result.get('notes','')))
                        conn.commit(); cur.close(); conn.close()
                        st.sidebar.info("✅ Saved for next time!")
                    except: pass
                    pin_info = (pincode,land_result.get('area_name',''),land_result.get('area_name_tamil',''),specific_land,land_result.get('elevation',''),weather_loc,land_result.get('notes',''))
                else:
                    specific_land = d_info[4] if d_info else "Marutham"; weather_loc = api_data['district']
            else:
                specific_land = d_info[4] if d_info else "Marutham"; weather_loc = d_info[6] if d_info else "Chennai"
                st.sidebar.warning("Pincode not found.")
elif pincodes:
    st.sidebar.markdown("**Known areas:**")
    pin_labels = [f"{p[0]} - {p[1]} ({p[3]})" for p in pincodes]
    sel_idx = st.sidebar.selectbox("Areas", range(len(pin_labels)), format_func=lambda i: pin_labels[i])
    pin_info = pincodes[sel_idx]; specific_land = pin_info[3]; weather_loc = pin_info[5]
else:
    specific_land = d_info[4] if d_info else "Marutham"; weather_loc = d_info[6] if d_info else "Chennai"

current_land_id = land_id_map.get(specific_land, 3)
w = get_weather(weather_loc)
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
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("📍",pin_info[1] if pin_info else sel_dist)
    col2.metric(f"{land_icons.get(specific_land,'🌍')} Land",specific_land)
    col3.metric("🌦️ Season",ts[1].split("(")[0].strip())
    col4.metric("🌤️",f"{w['temp']}°C")

    local_flora = get_flora(current_land_id, skw)
    if local_flora:
        st.info(f"🌿 **Available now in {specific_land}:** {', '.join([f[2] for f in local_flora[:8]])}")

    st.markdown("---")
    with st.form("body"):
        col1,col2 = st.columns(2)
        with col1:
            st.header("Symptoms")
            cold = st.slider("Cold/Runny Nose",0,5,0); cough = st.selectbox("Cough",["None","Dry","Wet"]); cough_sev = st.slider("Cough Severity",0,5,0)
            pain = st.multiselect("Pain",["Head","Neck","Joints","Abdomen","Chest","Back","None"]); pain_sev = st.slider("Pain Severity",0,5,0)
            pimples = st.number_input("Pimples",0,100,0)
        with col2:
            st.header("Body State")
            sweating = st.selectbox("Sweating",["Normal","Excessive"]); sputum = st.selectbox("Sputum",["Clear","Yellow","Green"]); urine = st.selectbox("Urine",["Pale","Amber","Dark"])
            energy = st.slider("Energy",1,10,5); digestion = st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"])

        st.markdown("---")
        st.header("📝 Health Conditions")
        user_id = st.text_input("Your ID","user_001")
        existing = get_health_profile(user_id)
        if existing:
            st.markdown("**⚠️ On file:**")
            for ex in existing: st.write(f"• **{ex[0]}** ({ex[1]}) - {ex[2]}")
        health_notes = st.text_area("Describe conditions (AI parses & remembers)","",height=80,placeholder="Example: Type 2 diabetes, knee arthritis, wife is pregnant")

        if st.form_submit_button("🤖 Analyze with Full Context",type="primary"):
            try:
                conn = db(); cur = conn.cursor(); pain_locs = ",".join(pain) if pain else "None"
                cur.execute("INSERT INTO body_condition_log (user_id,log_date,cold_intensity,cough_type,cough_severity,pain_locations,pain_severity,pimple_count,sweating_level,sputum_color,urine_color,energy_level,digestion_quality,weather_condition,health_notes,pincode,specific_land) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user_id,date.today(),cold,cough,cough_sev,pain_locs,pain_sev,pimples,sweating,sputum,urine,energy,digestion,f"{weather_loc} {w['temp']}C {w['desc']}",health_notes,typed_pin.strip() if typed_pin.strip() else "",specific_land))
                conn.commit(); cur.close(); conn.close()
                st.success("✅ Logged!")

                parsed_conditions = []
                if health_notes.strip():
                    with st.spinner("🤖 Parsing health conditions..."):
                        parsed = ai(f"""Parse health conditions: "{health_notes}". Return JSON: {{"conditions":[{{"name":"Condition","category":"Metabolic/Musculoskeletal/Reproductive/Allergy","severity":"Mild/Moderate/Severe","dietary_impact":"Diet restrictions","avoid_herbs":"Herbs to avoid","recommended_herbs":"Herbs that help"}}]}}""")
                        if parsed and parsed.get('conditions'):
                            parsed_conditions = parsed['conditions']
                            save_health_conditions(user_id, parsed_conditions)
                            for pc in parsed_conditions:
                                st.write(f"⚠️ **{pc.get('name','')}** - ❌ Avoid: {pc.get('avoid_herbs','')} | ✅ Use: {pc.get('recommended_herbs','')}")

                all_conds = existing + [(pc.get('name',''),pc.get('category',''),pc.get('severity',''),pc.get('dietary_impact',''),pc.get('avoid_herbs',''),pc.get('recommended_herbs','')) for pc in parsed_conditions]
                health_ctx = "\n".join([f"- {c[0]}: {c[3]}" for c in all_conds]) if all_conds else "None"
                avoid = ", ".join([c[4] for c in all_conds if c[4]]) if all_conds else "None"
                recommend = ", ".join([c[5] for c in all_conds if c[5]]) if all_conds else "Any"

                body = {'cold':cold,'cough':cough,'cough_severity':cough_sev,'pain_locations':pain_locs,'pain_severity':pain_sev,'pimple_count':pimples,'energy':energy,'digestion':digestion,'sweating':sweating,'sputum':sputum,'urine':urine}

                with st.spinner("🤖 Classifying dosha..."):
                    dosha = ai(f"""Siddha expert. Body: {json.dumps(body)}, Location: {pin_info[1] if pin_info else sel_dist} ({specific_land}), Season: {ts[1]} ({ts[2]}), Weather: {w['temp']}C {w['desc']}, Health: {health_ctx}
Return JSON: {{"primary_dosha":"Vata/Pitta/Kapha","dosha_percent":75,"secondary_dosha":"X","secondary_percent":25,"confidence":0.9,"summary":"Brief","weather_impact":"Weather","season_impact":"Season","land_impact":"Land","health_impact":"Health conditions impact"}}""")

                    if dosha:
                        col1,col2,col3 = st.columns(3)
                        col1.metric("Dosha",f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)")
                        col2.metric("Secondary",dosha.get('secondary_dosha','None'))
                        conf=dosha.get('confidence',0.8)
                        if isinstance(conf,str): conf=float(conf)
                        col3.metric("Confidence",f"{conf:.0%}")
                        st.info(f"📋 {dosha['summary']}")
                        if dosha.get('health_impact'): st.warning(f"⚠️ Health: {dosha['health_impact']}")

                        herbs = get_herbs_dosha(dosha['primary_dosha'])
                        if herbs:
                            st.markdown("---"); st.subheader(f"🌿 {len(herbs)} Matching Herbs")
                            for h in herbs[:6]: st.write(f"🌱 **{h['english']}** ({h['tamil']}) - {h['uses']}")

                        herbs_text = "\n".join([f"- {h['english']}: {h['uses']}" for h in herbs[:8]])
                        flora_text = "\n".join([f"- {f[2]}: {f[6]} | Cook: {f[7]}" for f in local_flora[:8]])

                        with st.spinner("🤖 Generating recipes..."):
                            recipes = ai(f"""Tamil chef. LOCAL recipes. Dosha: {dosha['primary_dosha']} ({dosha['dosha_percent']}%), Location: {pin_info[1] if pin_info else sel_dist} ({specific_land}), Season: {ts[1]}, Weather: {w['temp']}C, Energy: {energy}/10
Health: {health_ctx}. AVOID: {avoid}. PREFER: {recommend}
Herbs: {herbs_text}
Local flora: {flora_text}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","herb_preparation":"X","why_local":"X","why_seasonal":"X","health_safety":"X","nutritional_benefits":"X","dosha_fit":"X"}},"lunch":{{"name":"X","ingredients":"X","prep_time":"20min","medicinal_herbs":"X","herb_preparation":"X","why_local":"X","why_seasonal":"X","health_safety":"X","nutritional_benefits":"X","dosha_fit":"X"}},"dinner":{{"name":"X","ingredients":"X","prep_time":"15min","medicinal_herbs":"X","herb_preparation":"X","why_local":"X","why_seasonal":"X","health_safety":"X","nutritional_benefits":"X","dosha_fit":"X"}},"wellness_notes":"X"}}""")
                            if recipes:
                                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                                    st.markdown("---"); st.subheader(f"{mi} {meal.title()}")
                                    st.markdown(f"**{recipes[meal]['name']}**")
                                    st.write(f"📝 {recipes[meal]['ingredients']}"); st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                                    st.write(f"🧪 {recipes[meal].get('herb_preparation','')}"); st.write(f"📍 {recipes[meal].get('why_local','')}")
                                    st.write(f"🌦️ {recipes[meal].get('why_seasonal','')}"); st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                                    hs = recipes[meal].get('health_safety','')
                                    if hs: st.success(f"✅ {hs}")
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
            kids = ai(f"""Tamil pediatric nutritionist. Child {age}yr, Dosha {kid_dosha}. Location: {pin_info[1] if pin_info else sel_dist} ({specific_land}), Season: {ts[1]}
Local flora: {ft}
Kid herbs: {ht}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"15min"}},"lunch":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"20min"}},"dinner":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_local":"X","why_better_than_junk":"X","taste_profile":"X","prep_time":"15min"}},"parental_guidance":"X"}}""")
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
                    st.write(f"{ti} **{f[2]}** ({f[1]}) | {f[3]} | Cook: {f[4]} | {f[5]}")
                st.markdown("---"); st.subheader("📍 Districts")
                cur.execute("SELECT district_name,district_tamil FROM district_land_mapping WHERE primary_land=%s ORDER BY district_name",(land[2],))
                for d in cur.fetchall(): st.write(f"📍 {d[0]} ({d[1]})")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== SEASONS PAGE ====================
elif page=="🌦️ Seasons":
    st.title("🌦️ Tamil Seasons (பெரும்பொழுது)")
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
        with col1: st.markdown(f"### 🌱 {e}"); st.write(f"**{t}** | {p} | {r[12] or 7}/10")
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

# ==================== ENHANCED FEEDBACK PAGE ====================
elif page=="📊 Feedback":
    st.title("📊 Smart Feedback - Track Every Meal")
    st.markdown("AI parses your meals, analyzes junk food impact, and learns what works")

    with st.form("feedback_detailed"):
        st.subheader("📍 Your Location")
        fb_pincode = st.text_input("📮 Pincode","",placeholder="e.g., 625531",key="fbpin")
        fb_area = ""; fb_weather_loc = ""; fb_land = specific_land
        if fb_pincode.strip() and len(fb_pincode.strip())==6:
            api_data = lookup_pincode(fb_pincode.strip())
            if api_data:
                fb_area = f"{api_data['area']}, {api_data['district']}"
                fb_weather_loc = api_data['district']
                st.success(f"📍 {fb_area}")
            try:
                conn=db();cur=conn.cursor()
                cur.execute("SELECT specific_land FROM pincode_land_mapping WHERE pincode=%s",(fb_pincode.strip(),))
                lr=cur.fetchone();cur.close();conn.close()
                if lr: fb_land=lr[0]
            except: pass
        else:
            fb_area = pin_info[1] if pin_info else sel_dist
            fb_weather_loc = weather_loc

        st.markdown("---")
        st.subheader("☀️ Morning (Breakfast)")
        morning_notes = st.text_area("What you ate & WHY:","",height=80,key="mn",placeholder="Had thulasi kadaisal for running nose, kanji with inji for cold")
        col1,col2 = st.columns(2)
        with col1: morning_rating = st.slider("Rating",1,5,3,key="mr")
        with col2: morning_helped = st.selectbox("Did it help?",["Yes","Partially","No","Not for health"],key="mh")

        st.markdown("---")
        st.subheader("🌞 Afternoon (Lunch)")
        afternoon_notes = st.text_area("What you ate & WHY:","",height=80,key="an",placeholder="Manathakkali sambar with rice for stomach pain. Carrot poriyal.")
        col1,col2 = st.columns(2)
        with col1: afternoon_rating = st.slider("Rating",1,5,3,key="ar")
        with col2: afternoon_helped = st.selectbox("Did it help?",["Yes","Partially","No","Not for health"],key="ah")

        st.markdown("---")
        st.subheader("🌙 Evening (Dinner)")
        evening_notes = st.text_area("What you ate & WHY:","",height=80,key="en",placeholder="Ragi porridge with honey and ghee for weakness and body pain")
        col1,col2 = st.columns(2)
        with col1: evening_rating = st.slider("Rating",1,5,3,key="er")
        with col2: evening_helped = st.selectbox("Did it help?",["Yes","Partially","No","Not for health"],key="eh")

        st.markdown("---")
        st.subheader("🍟 Snacks & Junk Food")
        st.markdown("⚠️ **Be honest!** AI shows health impact and Tamil alternatives")
        junk_notes = st.text_area("Junk/snacks you or family had:","",height=80,key="jn",placeholder="Chips at 11am, pepsi with lunch, kids had kurkure and frooti")

        st.markdown("---")
        st.subheader("📊 Overall")
        col1,col2,col3,col4 = st.columns(4)
        with col1: fb_energy = st.slider("Energy",1,10,5,key="fe")
        with col2: fb_digestion = st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"],key="fd")
        with col3: fb_sleep = st.selectbox("Sleep",["Good","Normal","Disturbed","Poor"],key="fsl")
        with col4: fb_mood = st.selectbox("Mood",["Happy","Normal","Tired","Irritable","Stressed"],key="fmo")

        fb_user_id = st.text_input("Your ID","user_001",key="fuid")
        submitted = st.form_submit_button("🤖 Submit, Parse & Analyze",type="primary")

        if submitted:
            fb_ts = tamil_season()
            fb_w = get_weather(fb_weather_loc) if fb_weather_loc else w
            all_notes = f"Morning: {morning_notes}\nAfternoon: {afternoon_notes}\nEvening: {evening_notes}"
            has_meals = morning_notes.strip() or afternoon_notes.strip() or evening_notes.strip()
            has_junk = junk_notes.strip()

            meal_results = {}
            if has_meals:
                with st.spinner("🤖 Parsing meals..."):
                    for slot,notes_text,rating,helped in [("morning",morning_notes,morning_rating,morning_helped),("afternoon",afternoon_notes,afternoon_rating,afternoon_helped),("evening",evening_notes,evening_rating,evening_helped)]:
                        if notes_text.strip():
                            parsed = ai(f"""Tamil food analyst. Parse meal: "{notes_text}". Time: {slot}. Location: {fb_area} ({fb_land}). Season: {fb_ts[1]}.
Return JSON: {{"dishes":[{{"name":"Dish","dish_type":"Type","vegetables":["v"],"leaves_greens":["l"],"herbs":["h"],"spices":["s"],"grains":["g"],"symptom_treated":"Symptom or empty","symptom_dosha":"Dosha or empty"}}],"overall_dosha_impact":"Impact","ai_note":"Siddha insight"}}""")
                            meal_results[slot] = parsed

            junk_result = None; junk_count = 0
            if has_junk:
                with st.spinner("🤖 Analyzing junk impact..."):
                    junk_result = ai(f"""Nutritionist. Junk: "{junk_notes}". User also ate: {all_notes}. Location: {fb_area} ({fb_land}).
Return JSON: {{"items":[{{"name":"Item","calories":"est","sugar_g":"est","sodium_mg":"est","harmful_chemicals":"list","dosha_impact":"impact","healing_interference":"how it reduces healthy food","consumed_by":"Adult/Kids/Both","tamil_alternative":"healthy replacement","alternative_benefit":"why better"}}],"total_junk_count":3,"daily_health_reduction_percent":35,"kids_impact":"impact on children","overall_message":"summary"}}""")
                    if junk_result: junk_count = junk_result.get('total_junk_count',0)

            meal_count = sum(1 for s in ["morning","afternoon","evening"] if s in meal_results)
            helped_count = sum(1 for h in [morning_helped,afternoon_helped,evening_helped] if h=="Yes")
            health_score = min(10,max(1,(meal_count*2)+(helped_count*2)-(junk_count*1)+(fb_energy//3)))

            try:
                conn=db();cur=conn.cursor()
                cur.execute("""INSERT INTO feedback_detailed (user_id,feedback_date,pincode,area_name,specific_land,tamil_season,weather_condition,morning_notes,morning_rating,morning_helped,morning_parsed,afternoon_notes,afternoon_rating,afternoon_helped,afternoon_parsed,evening_notes,evening_rating,evening_helped,evening_parsed,junk_notes,junk_parsed,junk_count,energy_level,digestion,sleep_quality,mood,daily_health_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (fb_user_id,date.today(),fb_pincode.strip(),fb_area,fb_land,fb_ts[1],f"{fb_w['temp']}C {fb_w['desc']}",morning_notes,morning_rating,morning_helped,json.dumps(meal_results.get('morning')) if meal_results.get('morning') else None,afternoon_notes,afternoon_rating,afternoon_helped,json.dumps(meal_results.get('afternoon')) if meal_results.get('afternoon') else None,evening_notes,evening_rating,evening_helped,json.dumps(meal_results.get('evening')) if meal_results.get('evening') else None,junk_notes,json.dumps(junk_result) if junk_result else None,junk_count,fb_energy,fb_digestion,fb_sleep,fb_mood,health_score))
                conn.commit();cur.close();conn.close()
                st.success("✅ All data saved!")
            except Exception as e: st.warning(f"Save: {e}")

            st.markdown("---")
            st.title("🤖 AI Analysis")

            for slot,icon,notes_text,rating,helped in [("morning","☀️",morning_notes,morning_rating,morning_helped),("afternoon","🌞",afternoon_notes,afternoon_rating,afternoon_helped),("evening","🌙",evening_notes,evening_rating,evening_helped)]:
                if slot in meal_results and meal_results[slot]:
                    st.markdown("---"); st.subheader(f"{icon} {slot.title()}")
                    mr = meal_results[slot]
                    if mr.get('dishes'):
                        for dish in mr['dishes']:
                            st.markdown(f"**📌 {dish.get('name','')}** ({dish.get('dish_type','')})")
                            parts = []
                            if dish.get('vegetables'): parts.append(f"🥬 Veg: {', '.join(dish['vegetables'])}")
                            if dish.get('leaves_greens'): parts.append(f"🌿 Leaves: {', '.join(dish['leaves_greens'])}")
                            if dish.get('herbs'): parts.append(f"🌱 Herbs: {', '.join(dish['herbs'])}")
                            if dish.get('spices'): parts.append(f"🌶️ Spices: {', '.join(dish['spices'])}")
                            if dish.get('grains'): parts.append(f"🌾 Grains: {', '.join(dish['grains'])}")
                            for p in parts: st.write(p)
                            if dish.get('symptom_treated'): st.write(f"🤒 **For:** {dish['symptom_treated']} ({dish.get('symptom_dosha','')})")
                            eff={"Yes":"✅","Partially":"⚠️","No":"❌"}.get(helped,"ℹ️")
                            st.write(f"{eff} Helped: {helped} | {'⭐'*rating}")
                    if mr.get('ai_note'): st.info(f"💡 {mr['ai_note']}")

            if junk_result and junk_result.get('items'):
                st.markdown("---"); st.subheader("🍟 Junk Food Impact")
                for item in junk_result['items']:
                    st.markdown(f"**⚠️ {item.get('name','')}**")
                    st.write(f"🔥 Cal: ~{item.get('calories','?')} | Sugar: ~{item.get('sugar_g','?')}g | Sodium: ~{item.get('sodium_mg','?')}mg")
                    if item.get('harmful_chemicals'): st.write(f"☠️ {item['harmful_chemicals']}")
                    st.write(f"⚖️ Dosha: {item.get('dosha_impact','')}")
                    if item.get('healing_interference'): st.warning(f"🔄 {item['healing_interference']}")
                    if item.get('consumed_by') and 'kid' in item.get('consumed_by','').lower(): st.error(f"👶 Extra harmful for children!")
                    st.success(f"🌿 **Alternative:** {item.get('tamil_alternative','')} → {item.get('alternative_benefit','')}")
                if junk_result.get('kids_impact'): st.error(f"👶 {junk_result['kids_impact']}")
                if junk_result.get('daily_health_reduction_percent'): st.warning(f"📉 Junk reduced healing by ~{junk_result['daily_health_reduction_percent']}%")
                if junk_result.get('overall_message'): st.info(f"💡 {junk_result['overall_message']}")

            st.markdown("---"); st.subheader("📊 Daily Health Score")
            col1,col2,col3,col4 = st.columns(4)
            col1.metric("🏥 Score",f"{health_score}/10"); col2.metric("🟢 Meals",f"{meal_count}/3")
            col3.metric("🔴 Junk",junk_count); col4.metric("⚡ Energy",f"{fb_energy}/10")
            if health_score>=8: st.success("🌟 Excellent! Traditional meals working well!")
            elif health_score>=5: st.info("👍 Good! Reduce junk to improve.")
            else: st.warning("⚠️ Too much junk. Try Tamil snacks tomorrow.")
            st.success("✅ All feedback saved! AI is learning from your data.")
