import streamlit as st
import psycopg2
import os
from datetime import date, timedelta
import json
import requests
import io
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS

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

def speak(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except: return None

def transcribe_audio(audio_bytes):
    try:
        r = gm.generate_content([
            "Transcribe this audio. The speaker may use Tamil, English or Tanglish (mixed). "
            "Extract what food was eaten and for what health reason. "
            "Separate into morning, afternoon, evening meals. "
            "Also note any junk food mentioned. "
            "Return JSON: {\"morning\": \"food and reason\", \"afternoon\": \"food and reason\", \"evening\": \"food and reason\", \"junk\": \"junk items\"}",
            {"mime_type": "audio/wav", "data": audio_bytes}
        ])
        if r and r.text:
            t = r.text.strip()
            if "```json" in t: t = t.split("```json")[1].split("```")[0]
            elif "```" in t: t = t.split("```")[1].split("```")[0]
            return json.loads(t.strip())
    except: pass
    return None

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

def lookup_pincode(pin):
    try:
        r = requests.get(f"https://api.postalpincode.in/pincode/{pin}",timeout=10).json()
        if r and r[0].get('Status')=='Success' and r[0].get('PostOffice'):
            po = r[0]['PostOffice'][0]
            return {"area":po.get('Name',''),"district":po.get('District',''),"state":po.get('State','')}
    except: pass
    return None

def get_pincode_land(pin):
    try:
        c=db();cur=c.cursor();cur.execute("SELECT pincode,area_name,area_name_tamil,specific_land,elevation_category,weather_location,notes FROM pincode_land_mapping WHERE pincode=%s",(pin,));r=cur.fetchone();cur.close();c.close();return r
    except: return None

def classify_and_save_pincode(pin, api):
    lr = ai(f"""Geography. {api['area']}, {api['district']}, TN. Pin {pin}. Ainthinai: Kurinji(mountain),Mullai(forest),Marutham(plains),Neidhal(coast),Palai(arid). Return JSON: {{"area_name":"{api['area']}","area_name_tamil":"Tamil","specific_land":"X","elevation":"X","weather_location":"{api['district']}","notes":"Brief"}}""")
    if lr:
        try:
            c=db();cur=c.cursor();cur.execute("INSERT INTO pincode_land_mapping (pincode,area_name,area_name_tamil,district_name,specific_land,elevation_category,weather_location,notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(pin,lr.get('area_name',''),lr.get('area_name_tamil',''),api['district'],lr.get('specific_land','Marutham'),lr.get('elevation',''),lr.get('weather_location',api['district']),lr.get('notes','')));c.commit();cur.close();c.close()
        except: pass
    return lr

def get_flora(lid,skw):
    try:
        c=db();cur=c.cursor();cur.execute("SELECT flora_type,name_tamil,name_english,name_botanical,category,seasonal_availability,medicinal_uses,culinary_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s AND (seasonal_availability='Year-round' OR seasonal_availability ILIKE %s)",(lid,f"%{skw}%"));r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_herbs_dosha(dosha):
    try:
        c=db();cur=c.cursor();cur.execute(f"SELECT name_english,name_tamil,plant_part,primary_uses,diseases_treated,preparation_methods,seasonal_availability,safe_for_kids,min_age_years,data_confidence_score FROM medicinal_herbs WHERE {dosha.lower()}_effect='Decrease' ORDER BY data_confidence_score DESC LIMIT 10");r=cur.fetchall();cur.close();c.close()
        return [{"english":x[0],"tamil":x[1],"part":x[2],"uses":x[3],"diseases":x[4],"prep":x[5],"season":x[6],"safe_kids":x[7],"min_age":x[8],"score":x[9]} for x in r]
    except: return []

def get_all_herbs():
    try:
        c=db();cur=c.cursor();cur.execute("SELECT name_english,name_tamil,plant_part,primary_uses,vata_effect,pitta_effect,kapha_effect,diseases_treated,preparation_methods,seasonal_availability,safe_for_kids,min_age_years,data_confidence_score FROM medicinal_herbs ORDER BY data_confidence_score DESC");r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_health_profile(uid):
    try:
        c=db();cur=c.cursor();cur.execute("SELECT condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs FROM user_health_profile WHERE user_id=%s AND is_active=TRUE",(uid,));r=cur.fetchall();cur.close();c.close();return r
    except: return []

def save_health_conditions(uid,conds):
    try:
        c=db();cur=c.cursor()
        for co in conds: cur.execute("INSERT INTO user_health_profile (user_id,condition_name,condition_category,severity,dietary_restrictions,contraindicated_herbs,recommended_herbs) VALUES (%s,%s,%s,%s,%s,%s,%s)",(uid,co.get('name',''),co.get('category',''),co.get('severity',''),co.get('dietary_impact',''),co.get('avoid_herbs',''),co.get('recommended_herbs','')))
        c.commit();cur.close();c.close()
    except: pass

def get_user_profiles():
    try:
        c=db();cur=c.cursor();cur.execute("SELECT user_name,pincode,area_name,district,specific_land FROM user_profiles WHERE is_active=TRUE ORDER BY user_name");r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_user_scores(uid,days=7):
    try:
        c=db();cur=c.cursor();cur.execute("SELECT feedback_date,daily_health_score,junk_count,energy_level FROM feedback_detailed WHERE user_id=%s AND feedback_date>=%s ORDER BY feedback_date DESC",(uid,date.today()-timedelta(days=days)));r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_food_history(uid,days=14):
    try:
        c=db();cur=c.cursor();cur.execute("SELECT feedback_date,morning_notes,morning_rating,morning_helped,afternoon_notes,afternoon_rating,afternoon_helped,evening_notes,evening_rating,evening_helped,junk_notes,junk_count,daily_health_score,energy_level,digestion,sleep_quality,mood,specific_land,tamil_season,weather_condition FROM feedback_detailed WHERE user_id=%s AND feedback_date>=%s ORDER BY feedback_date DESC",(uid,date.today()-timedelta(days=days)));r=cur.fetchall();cur.close();c.close();return r
    except: return []

def save_discovered_food(fn,ft,user,symptom,dosha,land,season,botanical="",importance="",remediates=""):
    """Insert or increment a discovered food (case/space-insensitive match). Returns (new_count, was_count, is_new)."""
    try:
        fn=(fn or "").strip()
        if not fn: return (None,None,None)
        c=db();cur=c.cursor()
        # Match ignoring case and surrounding whitespace; keep the first-seen spelling
        cur.execute("SELECT food_id,times_mentioned,associated_symptoms FROM discovered_foods WHERE LOWER(TRIM(food_name))=LOWER(TRIM(%s)) LIMIT 1",(fn,));ex=cur.fetchone()
        if ex:
            was=ex[1] or 0;n=was+1;sy=ex[2] or ""
            if symptom and symptom not in sy: sy=f"{sy}, {symptom}" if sy else symptom
            if botanical or importance or remediates:
                cur.execute("""UPDATE discovered_foods SET times_mentioned=%s,associated_symptoms=%s,last_mentioned=%s,
                    botanical_name=COALESCE(NULLIF(%s,''),botanical_name),
                    plant_importance=COALESCE(NULLIF(%s,''),plant_importance),
                    remediates=COALESCE(NULLIF(%s,''),remediates) WHERE food_id=%s""",
                    (n,sy,date.today(),botanical,importance,remediates,ex[0]))
            else:
                cur.execute("UPDATE discovered_foods SET times_mentioned=%s,associated_symptoms=%s,last_mentioned=%s WHERE food_id=%s",(n,sy,date.today(),ex[0]))
            c.commit();cur.close();c.close();return (n,was,False)
        else:
            cur.execute("INSERT INTO discovered_foods (food_name,food_type,discovered_by,associated_symptoms,dosha_assessment,land_discovered,season_discovered,botanical_name,plant_importance,remediates) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(fn,ft,user,symptom,dosha,land,season,botanical,importance,remediates))
            c.commit();cur.close();c.close();return (1,0,True)
    except Exception:
        return (None,None,None)

def get_foods_by_type(food_type):
    """Return list of (food_name, botanical_name, times_mentioned, remediates) for a given type."""
    try:
        c=db();cur=c.cursor();cur.execute("SELECT food_name,botanical_name,times_mentioned,remediates FROM discovered_foods WHERE food_type=%s ORDER BY food_name",(food_type,));r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_food_details(food_name):
    """Return stored details for a single food."""
    try:
        c=db();cur=c.cursor();cur.execute("SELECT food_name,food_type,botanical_name,plant_importance,remediates,times_mentioned,associated_symptoms FROM discovered_foods WHERE food_name=%s",(food_name,));r=cur.fetchone();cur.close();c.close();return r
    except: return None

def get_foods_missing_botanical():
    """Return [(food_id, food_name, food_type)] for PLANT foods (not dishes) with no botanical name yet."""
    try:
        c=db();cur=c.cursor();cur.execute("SELECT food_id,food_name,food_type FROM discovered_foods WHERE food_type<>'Dish' AND (botanical_name IS NULL OR botanical_name='') ORDER BY food_id");r=cur.fetchall();cur.close();c.close();return r
    except: return []

def get_all_discovered_foods():
    """Return [(food_id, food_name, food_type, botanical_name, times_mentioned)] for management."""
    try:
        c=db();cur=c.cursor();cur.execute("SELECT food_id,food_name,food_type,botanical_name,times_mentioned FROM discovered_foods ORDER BY food_type,food_name");r=cur.fetchall();cur.close();c.close();return r
    except: return []

def delete_discovered_food(food_id):
    try:
        c=db();cur=c.cursor();cur.execute("DELETE FROM discovered_foods WHERE food_id=%s",(food_id,));c.commit();cur.close();c.close();return True
    except: return False

def delete_discovered_foods(food_ids):
    """Delete many foods by id list. Returns count deleted."""
    if not food_ids: return 0
    try:
        c=db();cur=c.cursor();cur.execute("DELETE FROM discovered_foods WHERE food_id = ANY(%s)",(list(food_ids),));n=cur.rowcount;c.commit();cur.close();c.close();return n
    except: return 0

def merge_duplicate_foods():
    """Merge rows whose names match after lower+trim. Keep earliest (smallest food_id),
    sum times_mentioned, keep any non-empty botanical/importance/remediates. Returns (groups_merged, rows_removed)."""
    try:
        c=db();cur=c.cursor()
        cur.execute("SELECT food_id,food_name,times_mentioned,botanical_name,plant_importance,remediates,associated_symptoms FROM discovered_foods ORDER BY food_id")
        rows=cur.fetchall()
        groups={}
        for r in rows:
            key=(r[1] or "").strip().lower()
            groups.setdefault(key,[]).append(r)
        groups_merged=0;rows_removed=0
        for key,items in groups.items():
            if len(items)<2: continue
            keep=items[0]  # smallest id
            total=sum((it[2] or 0) for it in items)
            bot=next((it[3] for it in items if it[3]),keep[3])
            imp=next((it[4] for it in items if it[4]),keep[4])
            rem=next((it[5] for it in items if it[5]),keep[5])
            syms=set()
            for it in items:
                if it[6]:
                    for s in str(it[6]).split(','):
                        if s.strip(): syms.add(s.strip())
            sym_str=", ".join(sorted(syms)) if syms else keep[6]
            cur.execute("UPDATE discovered_foods SET times_mentioned=%s,botanical_name=%s,plant_importance=%s,remediates=%s,associated_symptoms=%s WHERE food_id=%s",
                        (total,bot,imp,rem,sym_str,keep[0]))
            dup_ids=[it[0] for it in items[1:]]
            cur.execute("DELETE FROM discovered_foods WHERE food_id = ANY(%s)",(dup_ids,))
            groups_merged+=1;rows_removed+=len(dup_ids)
        c.commit();cur.close();c.close()
        return (groups_merged,rows_removed)
    except Exception:
        return (0,0)

def update_food_botanical(food_id,botanical,importance,remediates):
    """Fill the 3 new columns for one food by id."""
    try:
        c=db();cur=c.cursor();cur.execute("""UPDATE discovered_foods SET
            botanical_name=COALESCE(NULLIF(%s,''),botanical_name),
            plant_importance=COALESCE(NULLIF(%s,''),plant_importance),
            remediates=COALESCE(NULLIF(%s,''),remediates) WHERE food_id=%s""",
            (botanical,importance,remediates,food_id));c.commit();cur.close();c.close();return True
    except: return False

def save_remedy(food,ingr,symptom,dosha,land,season,helped):
    if not symptom or not food: return
    try:
        c=db();cur=c.cursor();cur.execute("SELECT remedy_id,times_reported,times_helped,times_partial,times_not_helped FROM remedy_mapping WHERE food_name=%s AND symptom=%s",(food,symptom));ex=cur.fetchone()
        if ex:
            tr=ex[1]+1;th=ex[2]+(1 if helped=="Yes" else 0);tp=ex[3]+(1 if helped=="Partially" else 0);tn=ex[4]+(1 if helped=="No" else 0);eff=round((th/tr)*100,1) if tr>0 else 0
            cur.execute("UPDATE remedy_mapping SET times_reported=%s,times_helped=%s,times_partial=%s,times_not_helped=%s,effectiveness_percent=%s,last_reported=%s WHERE remedy_id=%s",(tr,th,tp,tn,eff,date.today(),ex[0]))
        else:
            th=1 if helped=="Yes" else 0;cur.execute("INSERT INTO remedy_mapping (food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s)",(food,ingr,symptom,dosha,land,season,th,th*100))
        c.commit();cur.close();c.close()
    except: pass

land_icons={"Kurinji":"🏔️","Mullai":"🌳","Marutham":"🌾","Neidhal":"🌊","Palai":"🏜️"}
land_id_map={"Kurinji":1,"Mullai":2,"Marutham":3,"Neidhal":4,"Palai":5}

# ==================== SIDEBAR ====================
st.sidebar.title("🌿 Tamil Ayurvedic Platform")
users=get_user_profiles();user_names=[u[0] for u in users];user_names.insert(0,"➕ New User")
sel_user=st.sidebar.selectbox("👤 User",user_names)

if sel_user=="➕ New User":
    with st.sidebar.expander("Register",expanded=True):
        nn=st.text_input("Name","",key="nn");np=st.text_input("Pincode","",key="np",placeholder="625531")
        if st.button("✅ Register",key="rb"):
            if nn and np and len(np)==6:
                ap=lookup_pincode(np);area=ap['area'] if ap else "";dist=ap['district'] if ap else "";dp=get_pincode_land(np);land=dp[3] if dp else "Marutham"
                try:
                    c=db();cur=c.cursor();cur.execute("INSERT INTO user_profiles (user_name,pincode,area_name,district,specific_land) VALUES (%s,%s,%s,%s,%s)",(nn,np,area,dist,land));c.commit();cur.close();c.close();st.sidebar.success(f"✅ {nn} registered!");st.rerun()
                except: st.sidebar.warning("Name exists")
    typed_pin="";pin_area="";pin_district="";specific_land="Marutham";weather_loc="Chennai";current_user="guest"
else:
    current_user=sel_user;ud=None
    for u in users:
        if u[0]==sel_user: ud=u;break
    typed_pin=ud[1] if ud else "";pin_area=ud[2] if ud else "";pin_district=ud[3] if ud else "";specific_land=ud[4] if ud else "Marutham"
    if typed_pin:
        dp=get_pincode_land(typed_pin);weather_loc=dp[5] if dp else pin_district or "Chennai"
        st.sidebar.markdown(f"📍 **{pin_area}**, {pin_district}");st.sidebar.markdown(f"{land_icons.get(specific_land,'🌍')} **{specific_land}**")
    else: weather_loc="Chennai"

current_land_id=land_id_map.get(specific_land,3);w=get_weather(weather_loc);ts=tamil_season();skw=season_kw(ts[1])
st.sidebar.markdown("---")
st.sidebar.markdown(f"🌦️ {ts[0]} | {ts[2]}");st.sidebar.markdown(f"🌤️ {w['temp']}°C | {w['desc']}")
st.sidebar.markdown("---")
page=st.sidebar.radio("Navigate",["📝 Food Log","📅 History","🍽️ Foods Found","🏥 Remedies","👨‍🍳 Recommend","👶 Kids","🏔️ Ainthinai","🌦️ Seasons","🌿 Herbs","🔧 Admin"])

# ==================== PAGE 1: FOOD LOG ====================
if page=="📝 Food Log":
    st.title("📝 Daily Food Log - Train the AI!")

    if current_user and current_user!="guest":
        scores=get_user_scores(current_user)
        if scores:
            st.subheader(f"👋 Welcome, {current_user}!")
            ls=scores[0][1] or 5;avg=round(sum(s[1] for s in scores if s[1])/max(len([s for s in scores if s[1]]),1),1);best=max((s[1] for s in scores if s[1]),default=0);streak=len(scores);tj=sum(s[2] for s in scores if s[2])
            col1,col2,col3,col4,col5=st.columns(5)
            col1.metric("🏥 Last",f"{ls}/10");col2.metric("📊 Avg",f"{avg}/10");col3.metric("⭐ Best",f"{best}/10");col4.metric("🔥 Streak",f"{streak}d");col5.metric("🍟 Junk",tj)
            if len(scores)>1:
                for s in reversed(scores):
                    d=s[0].strftime("%a %d") if s[0] else "?";sc=s[1] or 0;jk=s[2] or 0
                    st.write(f"{d}: {'⭐'*sc} ({sc}/10){f' 🍟×{jk}' if jk>0 else ''}")
            if avg>=7: st.success("🌟 Amazing! Keep it up!")
            elif avg>=5: st.info("👍 Good! Less junk = better score")
            else: st.warning("⚠️ More traditional food needed!")
            st.markdown("---")

    # Voice or Type toggle
    input_mode = st.radio("Input Mode:",["✍️ Type","🎤 Voice"],horizontal=True)

    if input_mode=="🎤 Voice":
        st.subheader("🎤 Record Your Meals")
        st.markdown("Speak in Tamil or English. Tell what you ate and why.")
        audio_bytes = audio_recorder(text="🎤 Click to record",pause_threshold=3.0,sample_rate=16000)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            with st.spinner("🤖 AI transcribing..."):
                transcript = transcribe_audio(audio_bytes)
                if transcript:
                    st.success("✅ Transcribed!")
                    st.session_state['voice_morning'] = transcript.get('morning','')
                    st.session_state['voice_afternoon'] = transcript.get('afternoon','')
                    st.session_state['voice_evening'] = transcript.get('evening','')
                    st.session_state['voice_junk'] = transcript.get('junk','')
                    st.write(f"☀️ **Morning:** {transcript.get('morning','(not mentioned)')}")
                    st.write(f"🌞 **Afternoon:** {transcript.get('afternoon','(not mentioned)')}")
                    st.write(f"🌙 **Evening:** {transcript.get('evening','(not mentioned)')}")
                    st.write(f"🍟 **Junk:** {transcript.get('junk','(none)')}")
                    st.info("👇 Review and submit below")
                else:
                    st.warning("Could not transcribe. Please try again or type manually.")

    # ===== NEW: Per-meal Analyze -> Verify -> Add flow (Option A) =====
    vm=st.session_state.get('voice_morning','');va=st.session_state.get('voice_afternoon','');ve=st.session_state.get('voice_evening','');vj=st.session_state.get('voice_junk','')

    st.markdown("Add each item you ate. Pick from existing foods, or type a new one for AI to analyze and verify before saving.")

    TYPE_OPTIONS = ["Dish","Vegetable","Leaf/Green","Herb","Grain","Spice"]

    def meal_item_widget(slot, icon, default_text):
        st.markdown(f"### {icon} {slot.title()}")
        note = st.text_area(f"{slot.title()} note (what & why):", default_text, height=60,
                            key=f"note_{slot}", placeholder="e.g. Seenthil kadaisal for fever")
        ftype = st.selectbox("Food type", TYPE_OPTIONS, key=f"ftype_{slot}")
        existing = get_foods_by_type(ftype)
        existing_names = [e[0] for e in existing]
        dropdown = ["+ Type new food"] + existing_names
        choice = st.selectbox(f"Pick existing {ftype.lower()} or add new", dropdown, key=f"pick_{slot}")
        akey = f"analyzed_{slot}"

        if choice != "+ Type new food":
            det = get_food_details(choice)
            if det:
                st.info(f"**{det[0]}** | *{det[2] or 'botanical n/a'}* | mentioned {det[5]}x")
                if det[4]: st.write(f"Remediates: {det[4]}")
                if det[3]: st.write(f"Importance: {det[3]}")
            if st.button(f"Add this {ftype.lower()}", key=f"addexist_{slot}"):
                n,was,isnew = save_discovered_food(choice,ftype,current_user,"","",specific_land,ts[1])
                if n is not None:
                    st.success(f"'{choice}' added! Now mentioned {n} times (was {was}).")
                else:
                    st.warning("Could not save. Try again.")
            return

        new_name = st.text_input(f"Type the {ftype.lower()} name", key=f"new_{slot}",
                                 placeholder="e.g. Seenthil kadaisal")
        col_a, col_b = st.columns(2)
        with col_a:
            analyze = st.button("Analyze", key=f"analyze_{slot}")
        with col_b:
            clear = st.button("Clear", key=f"clear_{slot}")
        if clear and akey in st.session_state:
            del st.session_state[akey]

        if analyze and new_name.strip():
            with st.spinner("Analyzing & identifying botanical name..."):
                prompt = (
                    'Tamil Siddha food & botany expert. The user ate: "' + new_name.strip() +
                    '" (type: ' + ftype + '). Identify the MAIN plant/ingredient and give scientific details. '
                    'Return ONLY JSON: {"clean_name":"Cleaned food name","key_plant_tamil":"Tamil/common name",'
                    '"botanical_name":"Latin botanical name","plant_importance":"Why this plant matters in Siddha/Ayurveda (1-2 sentences)",'
                    '"remediates":"Conditions/symptoms it helps (comma separated)","vegetables":[],"leaves_greens":[],'
                    '"herbs":[],"grains":[],"spices":[],"symptom_dosha":"Vata/Pitta/Kapha or empty"}'
                )
                res = ai(prompt)
            if res:
                st.session_state[akey] = res
            else:
                st.warning("AI couldn't analyze. Check spelling or try again.")

        if akey in st.session_state and st.session_state[akey]:
            res = st.session_state[akey]
            st.markdown("#### Verify AI Analysis")
            ver_name = st.text_input("Food name", res.get('clean_name', new_name), key=f"vername_{slot}")
            is_dish = (ftype == "Dish")
            if is_dish:
                ver_bot = ""
                st.caption("ℹ️ Dishes don't get a botanical name (it's a mix of ingredients).")
            else:
                ver_bot = st.text_input("Botanical name", res.get('botanical_name',''), key=f"verbot_{slot}")
            st.write(f"Key plant: {res.get('key_plant_tamil','')}")
            if res.get('plant_importance'): st.write(f"Importance: {res['plant_importance']}")
            if res.get('remediates'): st.success(f"Remediates: {res['remediates']}")
            extras=[]
            for k,lbl in [("vegetables","Veg"),("leaves_greens","Leaves"),("herbs","Herbs"),("grains","Grains"),("spices","Spices")]:
                if res.get(k): extras.append(f"{lbl}: {', '.join(res[k])}")
            if extras: st.caption(" | ".join(extras))
            symptom_guess = ""
            if note and (" for " in note.lower()):
                symptom_guess = note.lower().split(" for ",1)[1].strip()
            symptom = st.text_input("Symptom treated (optional)", symptom_guess, key=f"versym_{slot}")
            if st.button("Looks correct - Add to Database", key=f"confirm_{slot}", type="primary"):
                n,was,isnew = save_discovered_food(
                    ver_name.strip(), ftype, current_user, symptom,
                    res.get('symptom_dosha',''), specific_land, ts[1],
                    botanical=ver_bot.strip(), importance=res.get('plant_importance',''),
                    remediates=res.get('remediates',''))
                if n is not None:
                    bot_msg = f" Botanical: {ver_bot}" if ver_bot else ""
                    if isnew:
                        st.success(f"'{ver_name}' added as NEW!{bot_msg} First mention.")
                    else:
                        st.success(f"'{ver_name}' added! Now mentioned {n} times (was {was}).{bot_msg}")
                    if symptom:
                        save_remedy(ver_name.strip(), ver_bot.strip(), symptom, res.get('symptom_dosha',''), specific_land, ts[1], "Yes")
                    del st.session_state[akey]
                else:
                    st.warning("Could not save. Try again.")

    meal_item_widget("morning","Morning",vm)
    st.markdown("---")
    meal_item_widget("afternoon","Afternoon",va)
    st.markdown("---")
    meal_item_widget("evening","Evening",ve)
    st.markdown("---")

    st.subheader("Save Today's Daily Log")
    st.caption("Records ratings, energy, digestion, mood for your History & scores.")
    with st.form("daily_feedback"):
        c1,c2,c3=st.columns(3)
        with c1: mr=st.slider("Morning rating",1,5,3,key="mr"); mh=st.selectbox("Morning helped?",["Yes","Partially","No","Not for health"],key="mh")
        with c2: ar=st.slider("Afternoon rating",1,5,3,key="ar"); ah=st.selectbox("Afternoon helped?",["Yes","Partially","No","Not for health"],key="ah")
        with c3: er=st.slider("Evening rating",1,5,3,key="er"); eh=st.selectbox("Evening helped?",["Yes","Partially","No","Not for health"],key="eh")
        jn=st.text_area("Junk food today:",vj,height=50,key="jn",placeholder="Chips, pepsi, kurkure")
        c1,c2,c3,c4=st.columns(4)
        with c1: fe=st.slider("Energy",1,10,5,key="fe")
        with c2: fd=st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"],key="fd")
        with c3: fsl=st.selectbox("Sleep",["Good","Normal","Disturbed","Poor"],key="fsl")
        with c4: fmo=st.selectbox("Mood",["Happy","Normal","Tired","Irritable"],key="fmo")
        save_day=st.form_submit_button("Save Today's Log",type="primary")

    if save_day:
        mn=st.session_state.get('note_morning','');an=st.session_state.get('note_afternoon','');en=st.session_state.get('note_evening','')
        junk_result=None;junk_count=0
        if jn.strip():
            with st.spinner("Junk analysis..."):
                jprompt='Nutritionist. Junk: "'+jn+'". Return JSON: {"items":[{"name":"X","dosha_impact":"X","healing_interference":"X","consumed_by":"Adult/Kids/Both","tamil_alternative":"X","alternative_benefit":"X"}],"total_junk_count":3,"overall_message":"X"}'
                junk_result=ai(jprompt)
                if junk_result: junk_count=junk_result.get('total_junk_count',0)
        mc=sum(1 for t in [mn,an,en] if t and t.strip());hc=sum(1 for h in [mh,ah,eh] if h=="Yes")
        hs=min(10,max(1,(mc*2)+(hc*2)-(junk_count)+(fe//3)))
        try:
            conn=db();cur=conn.cursor()
            cur.execute("INSERT INTO feedback_detailed (user_id,feedback_date,pincode,area_name,specific_land,tamil_season,weather_condition,morning_notes,morning_rating,morning_helped,afternoon_notes,afternoon_rating,afternoon_helped,evening_notes,evening_rating,evening_helped,junk_notes,junk_parsed,junk_count,energy_level,digestion,sleep_quality,mood,daily_health_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (current_user,date.today(),typed_pin,f"{pin_area}, {pin_district}",specific_land,ts[1],f"{w['temp']}C {w['desc']}",mn,mr,mh,an,ar,ah,en,er,eh,jn,json.dumps(junk_result),junk_count,fe,fd,fsl,fmo,hs))
            conn.commit();cur.close();conn.close();st.success(f"Daily log saved! Score: {hs}/10")
            for k in ['voice_morning','voice_afternoon','voice_evening','voice_junk']:
                if k in st.session_state: del st.session_state[k]
        except Exception as e: st.warning(f"Save: {e}")
        if junk_result and junk_result.get('items'):
            st.markdown("#### Junk Impact")
            for item in junk_result['items']:
                st.warning(f"{item.get('name','')} - {item.get('dosha_impact','')}")
                st.success(f"Try instead: {item.get('tamil_alternative','')} -> {item.get('alternative_benefit','')}")
            if junk_result.get('overall_message'): st.info(junk_result['overall_message'])
        c1,c2,c3=st.columns(3)
        c1.metric("Score",f"{hs}/10");c2.metric("Meals",f"{mc}/3");c3.metric("Junk",junk_count)


# ==================== PAGE 2: FOOD HISTORY ====================
elif page=="📅 History":
    st.title(f"📅 Food History - {current_user}")

    days = st.selectbox("View period:",["Last 7 days","Last 14 days","Last 30 days"])
    d_map = {"Last 7 days":7,"Last 14 days":14,"Last 30 days":30}
    history = get_food_history(current_user, d_map[days])

    if history:
        # Weekly summary
        scores = [h[12] for h in history if h[12]]
        junks = [h[11] for h in history if h[11] is not None]
        energies = [h[13] for h in history if h[13]]

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("📊 Avg Score", f"{round(sum(scores)/max(len(scores),1),1)}/10" if scores else "N/A")
        col2.metric("📝 Days Logged", len(history))
        col3.metric("🍟 Total Junk", sum(junks) if junks else 0)
        col4.metric("⚡ Avg Energy", f"{round(sum(energies)/max(len(energies),1),1)}/10" if energies else "N/A")

        # Most eaten foods
        all_foods = []
        for h in history:
            for notes in [h[1],h[4],h[7]]:
                if notes: all_foods.append(notes)
        if all_foods:
            st.info(f"📊 **{len(history)} days logged** with {len(all_foods)} meal entries")

        st.markdown("---")

        # Day by day timeline
        for h in history:
            dt = h[0]
            score = h[12] or 0
            score_icon = "🌟" if score>=8 else "👍" if score>=5 else "⚠️"
            dt_str = dt.strftime("%A, %B %d, %Y") if dt else "Unknown"

            with st.expander(f"📅 {dt_str}  |  Score: {score}/10 {score_icon}  |  🍟 Junk: {h[11] or 0}",expanded=False):
                col1,col2 = st.columns(2)
                with col1:
                    if h[1]: st.write(f"☀️ **Morning:** {h[1]}")
                    if h[1]: st.write(f"   Rating: {'⭐'*(h[2] or 3)} | Helped: {h[3] or 'N/A'}")
                    if h[4]: st.write(f"🌞 **Afternoon:** {h[4]}")
                    if h[4]: st.write(f"   Rating: {'⭐'*(h[5] or 3)} | Helped: {h[6] or 'N/A'}")
                    if h[7]: st.write(f"🌙 **Evening:** {h[7]}")
                    if h[7]: st.write(f"   Rating: {'⭐'*(h[8] or 3)} | Helped: {h[9] or 'N/A'}")
                with col2:
                    if h[10]: st.write(f"🍟 **Junk:** {h[10]}")
                    st.write(f"⚡ Energy: {h[13] or 'N/A'}/10 | 🍽️ Digestion: {h[14] or 'N/A'}")
                    st.write(f"😴 Sleep: {h[15] or 'N/A'} | 😊 Mood: {h[16] or 'N/A'}")
                    st.write(f"📍 {h[17] or ''} | 🌦️ {h[18] or ''} | 🌤️ {h[19] or ''}")

        # Trend chart
        if len(scores) > 1:
            st.markdown("---"); st.subheader("📈 Score Trend")
            for h in reversed(history):
                if h[12]:
                    d = h[0].strftime("%a %d") if h[0] else "?"
                    st.write(f"{d}: {'⭐'*h[12]} ({h[12]}/10){f' 🍟×{h[11]}' if h[11] else ''}")
    else:
        st.info(f"No food history yet for {current_user}. Start logging in 📝 Food Log!")

# ==================== PAGE 3: DISCOVERED FOODS ====================
elif page=="🍽️ Foods Found":
    st.title("🍽️ Discovered Foods (Auto-Growing)")
    try:
        c=db();cur=c.cursor();cur.execute("SELECT food_name,food_type,discovered_by,times_mentioned,associated_symptoms,dosha_assessment,land_discovered,season_discovered,botanical_name,remediates,plant_importance FROM discovered_foods ORDER BY last_mentioned DESC");foods=cur.fetchall();cur.close();c.close()
        if foods:
            st.write(f"**Total: {len(foods)} foods discovered!**")
            tf=st.selectbox("Filter",["All","Dish","Vegetable","Leaf/Green","Herb","Grain","Spice"])
            for f in foods:
                if tf!="All" and f[1]!=tf: continue
                ti={"Dish":"🍽️","Vegetable":"🥬","Leaf/Green":"🌿","Herb":"🌱","Grain":"🌾","Spice":"🌶️"}.get(f[1],"🍽️")
                col1,col2=st.columns([1,2])
                with col1:
                    st.markdown(f"### {ti} {f[0]}")
                    if f[8]: st.caption(f"*{f[8]}*")
                    st.write(f"**{f[1]}** | Mentioned: {f[3]}x")
                with col2:
                    if f[9]: st.success(f"💊 Remediates: {f[9]}")
                    if f[10]: st.write(f"⭐ {f[10]}")
                    if f[4]: st.write(f"🤒 For: {f[4]}")
                    st.write(f"📍 {f[6] or ''} | 🌦️ {f[7] or ''} | By: {f[2] or ''}")
                st.markdown("---")
        else: st.info("No foods yet. Log meals to start!")
    except Exception as e: st.error(str(e))

# ==================== PAGE 4: REMEDY MAP ====================
elif page=="🏥 Remedies":
    st.title("🏥 Remedy Map (Community-Learned)")
    try:
        c=db();cur=c.cursor();cur.execute("SELECT DISTINCT symptom FROM remedy_mapping ORDER BY symptom");symptoms=[s[0] for s in cur.fetchall()]
        if symptoms:
            ss=st.selectbox("🤒 Symptom",["All"]+symptoms)
            if ss=="All": cur.execute("SELECT food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent FROM remedy_mapping ORDER BY effectiveness_percent DESC")
            else: cur.execute("SELECT food_name,ingredient,symptom,dosha,land_type,season,times_reported,times_helped,effectiveness_percent FROM remedy_mapping WHERE symptom=%s ORDER BY effectiveness_percent DESC",(ss,))
            for r in cur.fetchall():
                eff=r[8] or 0;ei="🟢" if eff>=80 else "🟡" if eff>=50 else "🔴"
                col1,col2=st.columns([1,2])
                with col1: st.markdown(f"### {ei} {r[0]}"); st.write(f"**{eff}%** effective | {r[6]}x reported")
                with col2: st.write(f"🤒 {r[2]} | 🌱 {r[1] or ''} | ⚖️ {r[3] or ''} | 📍 {r[4] or ''} | 🌦️ {r[5] or ''}")
                st.markdown("---")
        else: st.info("No remedies yet. Log meals with symptoms!")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 5: RECOMMENDATIONS ====================
elif page=="👨‍🍳 Recommend":
    st.title("🌿 Get Recommendations")
    col1,col2,col3=st.columns(3)
    col1.metric("📍",pin_area or "Set user");col2.metric(f"{land_icons.get(specific_land,'🌍')}",specific_land);col3.metric("🌤️",f"{w['temp']}°C")
    local_flora=get_flora(current_land_id,skw)
    if local_flora: st.info(f"🌿 Available: {', '.join([f[2] for f in local_flora[:8]])}")
    st.markdown("---")
    with st.form("body"):
        col1,col2=st.columns(2)
        with col1: cold=st.slider("Cold",0,5,0);cough=st.selectbox("Cough",["None","Dry","Wet"]);pain=st.multiselect("Pain",["Head","Neck","Joints","Abdomen","Back","None"]);energy=st.slider("Energy",1,10,5)
        with col2: sweating=st.selectbox("Sweating",["Normal","Excessive"]);sputum=st.selectbox("Sputum",["Clear","Yellow","Green"]);urine=st.selectbox("Urine",["Pale","Amber","Dark"]);digestion=st.selectbox("Digestion",["Good","Normal","Sluggish","Weak"])
        health_notes=st.text_area("Health conditions","",height=60)
        if st.form_submit_button("🤖 Recommend",type="primary"):
            existing=get_health_profile(current_user);health_ctx="\n".join([f"- {c[0]}: {c[3]}" for c in existing]) if existing else "None"
            body={'cold':cold,'cough':cough,'energy':energy,'digestion':digestion,'sweating':sweating,'sputum':sputum,'urine':urine}
            herbs=get_herbs_dosha("Vata");herbs_text="\n".join([f"- {h['english']}: {h['uses']}" for h in herbs[:8]])
            flora_text="\n".join([f"- {f[2]}: {f[6]}" for f in local_flora[:8]])
            with st.spinner("🤖 Generating..."):
                dosha=ai(f"""Siddha. Body:{json.dumps(body)}, Location:{pin_area}({specific_land}), Season:{ts[1]}, Weather:{w['temp']}C. Health:{health_ctx}. Return JSON: {{"primary_dosha":"X","dosha_percent":75,"summary":"Brief"}}""")
                if dosha:
                    st.metric("Dosha",f"{dosha['primary_dosha']} ({dosha['dosha_percent']}%)");st.info(f"📋 {dosha['summary']}")
                    recipes=ai(f"""Tamil chef. Dosha:{dosha['primary_dosha']}, Location:{pin_area}({specific_land}), Season:{ts[1]}, Weather:{w['temp']}C. Herbs:{herbs_text}. Flora:{flora_text}. Health:{health_ctx}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"lunch":{{"name":"X","ingredients":"X","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"dinner":{{"name":"X","ingredients":"X","medicinal_herbs":"X","why_local":"X","nutritional_benefits":"X"}},"wellness_notes":"X"}}""")
                    if recipes:
                        rec_text=""
                        for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                            st.markdown("---");st.subheader(f"{mi} {meal.title()}");st.markdown(f"**{recipes[meal]['name']}**")
                            st.write(f"📝 {recipes[meal]['ingredients']}");st.write(f"🌿 {recipes[meal]['medicinal_herbs']}")
                            st.write(f"📍 {recipes[meal].get('why_local','')}");st.write(f"💪 {recipes[meal]['nutritional_benefits']}")
                            rec_text+=f"{meal}: {recipes[meal]['name']}. {recipes[meal]['nutritional_benefits']}. "
                        st.info(f"💡 {recipes.get('wellness_notes','')}")
                        if st.button("🔊 Hear Recommendations"):
                            audio=speak(rec_text,'en')
                            if audio: st.audio(audio,format='audio/mp3')

# ==================== PAGE 6: KIDS ====================
elif page=="👶 Kids":
    st.title("👶 Kids Nutrition")
    col1,col2=st.columns(2)
    with col1: age=st.selectbox("Age",["2-3","4-6","7-10","11+"])
    with col2: kd=st.selectbox("Dosha",["Not Sure","Vata","Pitta","Kapha"])
    if st.button("🤖 Get Meal Plan",type="primary"):
        all_h=get_all_herbs();kh=[{"english":r[0],"uses":r[3]} for r in all_h if (r[10] if len(r)>10 else True) and (r[11] if len(r)>11 else 2)<=int(age.split("-")[0])]
        fl=get_flora(current_land_id,skw)
        with st.spinner("Creating..."):
            kids=ai(f"""Pediatric nutritionist. Child {age}yr, Dosha {kd}. Location: {pin_area}({specific_land}), Season:{ts[1]}. Herbs:{"\n".join([f"- {h['english']}: {h['uses']}" for h in kh[:8]])}. Flora:{"\n".join([f"- {f[2]}: {f[6]}" for f in fl[:6]])}
Return JSON: {{"breakfast":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X"}},"lunch":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X"}},"dinner":{{"name":"X","ingredients":"X","health_benefits":"X","medicinal_herbs":"X","why_better_than_junk":"X"}},"parental_guidance":"X"}}""")
            if kids:
                for meal,mi in [("breakfast","☀️"),("lunch","🌞"),("dinner","🌙")]:
                    st.markdown("---");st.subheader(f"{mi} {meal.title()}");st.markdown(f"**{kids[meal]['name']}**")
                    st.write(f"📝 {kids[meal]['ingredients']}");st.write(f"💪 {kids[meal]['health_benefits']}");st.write(f"🌿 {kids[meal]['medicinal_herbs']}")
                    st.info(f"✨ {kids[meal]['why_better_than_junk']}")
                st.write(f"👨‍👩‍👧 {kids.get('parental_guidance','')}")

# ==================== PAGE 7: AINTHINAI ====================
elif page=="🏔️ Ainthinai":
    st.title("🏔️ ஐந்திணை")
    try:
        c=db();cur=c.cursor();cur.execute("SELECT * FROM ainthinai_lands ORDER BY land_id");lands=cur.fetchall()
        tabs=st.tabs([f"{land_icons.get(l[2],'🌍')} {l[2]}" for l in lands])
        for i,land in enumerate(lands):
            with tabs[i]:
                st.subheader(f"{land[1]} - {land[2]}");st.write(f"**{land[5]}**")
                st.write(f"🙏 {land[6]} | 🌸 {land[8]} | 🌳 {land[10]} | 🍚 {land[14]} | 📍 {land[18]}")
                st.markdown("---")
                cur.execute("SELECT flora_type,name_tamil,name_english,medicinal_uses,dosha_impact FROM land_flora_mapping WHERE land_id=%s",(land[0],))
                for f in cur.fetchall():
                    ti={"Herb":"🌱","Flower":"🌸","Fruit":"🍎","Tree":"🌳","Grain":"🌾"}.get(f[0],"🌿")
                    st.write(f"{ti} **{f[2]}** ({f[1]}) | {f[3]} | {f[4]}")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 8: SEASONS ====================
elif page=="🌦️ Seasons":
    st.title("🌦️ Tamil Seasons")
    try:
        c=db();cur=c.cursor();cur.execute("SELECT * FROM tamil_seasons ORDER BY season_id");seasons=cur.fetchall()
        icons=["☀️","🔥","🌧️","🍂","❄️","🌸"]
        for i,s in enumerate(seasons):
            ic=icons[i] if i<len(icons) else "🌤️";is_cur=ts[0]==s[1]
            with st.expander(f"{ic} {s[1]} - {s[2]} ({s[4]})"+ (" ← NOW" if is_cur else ""),expanded=is_cur):
                col1,col2=st.columns(2)
                with col1: st.write(f"**{s[3]}** | **{s[7]}** | {s[8]}")
                with col2: st.write(f"🌿 {s[9]}");st.write(f"🍎 {s[10]}");st.write(f"🌸 {s[11]}")
        cur.close();c.close()
    except Exception as e: st.error(str(e))

# ==================== PAGE 9: HERBS ====================
elif page=="🌿 Herbs":
    st.title("🌿 Herbs")
    search=st.text_input("Search","");df=st.selectbox("Dosha",["All","Vata","Pitta","Kapha"])
    for r in get_all_herbs():
        e,t,p,u=r[0] or "",r[1] or "",r[2] or "",r[3] or "";v,pi,k=r[4] or "",r[5] or "",r[6] or ""
        if search and search.lower() not in e.lower() and search.lower() not in t.lower(): continue
        if df!="All" and {"Vata":v,"Pitta":pi,"Kapha":k}[df]!="Decrease": continue
        col1,col2=st.columns([1,2])
        with col1: st.markdown(f"### 🌱 {e}");st.write(f"**{t}** | {p} | {r[12] or 7}/10")
        with col2: st.write(f"{u} | V:{v} P:{pi} K:{k}")
        st.markdown("---")

# ==================== PAGE 10: ADMIN ====================
elif page=="🔧 Admin":
    st.title("🔧 Admin")
    tab=st.radio("",["🌿 Herb","🍽️ Dish","👤 Users","🧬 Backfill Botanical","🗑️ Manage Foods"])
    if tab=="🌿 Herb":
        with st.form("herb"):
            col1,col2=st.columns(2)
            with col1: ht=st.text_input("Tamil *");he=st.text_input("English *");hp=st.selectbox("Part",["Leaves","Root","Seed","Flower","Bark","Fruit","Whole plant"]);hu=st.text_area("Uses *")
            with col2: hv=st.selectbox("Vata",["Decrease","Increase","Neutral"]);hpi=st.selectbox("Pitta",["Decrease","Increase","Neutral"]);hk=st.selectbox("Kapha",["Decrease","Increase","Neutral"]);hs=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]);hsc=st.slider("Score",1,10,7)
            if st.form_submit_button("✅ Add",type="primary") and ht and he and hu:
                try:
                    c=db();cur=c.cursor();cur.execute("INSERT INTO medicinal_herbs (name_tamil,name_english,plant_part,vata_effect,pitta_effect,kapha_effect,primary_uses,seasonal_availability,data_confidence_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(ht,he,hp,hv,hpi,hk,hu,hs,hsc));c.commit();cur.close();c.close();st.success(f"✅ '{he}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    elif tab=="🍽️ Dish":
        with st.form("dish"):
            dn=st.text_input("Name *");dd=st.selectbox("Dosha",["Vata","Pitta","Kapha","Neutral"]);ds=st.selectbox("Season",["Year-round","Summer","Winter","Monsoon"]);di=st.text_area("Instructions")
            if st.form_submit_button("✅ Add",type="primary") and dn:
                try:
                    c=db();cur=c.cursor();cur.execute("INSERT INTO recipes (recipe_name,primary_ingredient_id,serves,prep_time_min,dosha_suitability,seasonal_best,instructions) VALUES (%s,1,4,20,%s,%s,%s)",(dn,dd,ds,di));c.commit();cur.close();c.close();st.success(f"✅ '{dn}' added!");st.balloons()
                except Exception as e: st.error(str(e))
    elif tab=="👤 Users":
        for u in get_user_profiles(): st.write(f"👤 **{u[0]}** | 📮 {u[1]} | 📍 {u[2]}, {u[3]} | {land_icons.get(u[4],'🌍')} {u[4]}")
    elif tab=="🧬 Backfill Botanical":
        st.subheader("🧬 Backfill Botanical Names")
        missing=get_foods_missing_botanical()
        st.write(f"**{len(missing)} foods** are missing a botanical name.")
        if missing:
            with st.expander("See the list"):
                for m in missing: st.write(f"• {m[1]} ({m[2]})")
            st.caption("This asks AI to identify the botanical name for each plant ingredient (vegetables, herbs, greens, grains, spices) and fills botanical name, importance, and what it remediates. Dishes are skipped — they're a mix of ingredients. Runs ~1 food/second. You can edit or delete any entry later.")
            colA,colB=st.columns(2)
            with colA: batch=st.number_input("How many to process now?",1,len(missing),min(len(missing),25))
            with colB: st.write("");st.write("")
            if st.button(f"🚀 Backfill {batch} foods now",type="primary"):
                prog=st.progress(0.0);done=0;filled=0;log_area=st.empty()
                for idx,(fid,fname,ftype) in enumerate(missing[:batch]):
                    prompt=('Tamil Siddha food & botany expert. Plant/ingredient: "'+fname+'" (type: '+(ftype or 'Herb')+'). '
                            'Identify its botanical (Latin) name. '
                            'Return ONLY JSON: {"botanical_name":"Latin name","plant_importance":"why it matters in Siddha/Ayurveda (1-2 sentences)","remediates":"conditions it helps, comma separated"}')
                    res=ai(prompt)
                    if res and res.get('botanical_name'):
                        ok=update_food_botanical(fid,res.get('botanical_name',''),res.get('plant_importance',''),res.get('remediates',''))
                        if ok: filled+=1
                        log_area.write(f"✅ {fname} → *{res.get('botanical_name','')}*")
                    else:
                        log_area.write(f"⚠️ {fname} → could not identify (skipped)")
                    done+=1;prog.progress(done/batch)
                st.success(f"Done! Filled {filled} of {done} processed. {len(missing)-done} still remaining — run again to continue.")
        else:
            st.success("🎉 All plant foods already have botanical names!")
    elif tab=="🗑️ Manage Foods":
        st.subheader("🗑️ Manage / Delete Foods")
        st.caption("Remove wrong/duplicate entries, or merge same-name duplicates (case differences).")

        # Merge duplicates
        st.markdown("**🔀 Merge duplicates** (same name, different case/spacing)")
        if st.button("🔀 Merge duplicate foods now"):
            g,rm=merge_duplicate_foods()
            if g: st.success(f"Merged {g} duplicate group(s), removed {rm} extra row(s). Refresh to see.")
            else: st.info("No duplicates found.")
        st.markdown("---")

        allfoods=get_all_discovered_foods()
        if not allfoods:
            st.info("No discovered foods yet.")
        else:
            st.write(f"**{len(allfoods)} foods** in database.")
            ticon={"Dish":"🍽️","Vegetable":"🥬","Leaf/Green":"🌿","Herb":"🌱","Grain":"🌾","Spice":"🌶️"}
            labels={a[0]:f"{ticon.get(a[2],'🍽️')} {a[1]}  ({a[2]}, {a[4]}x)" for a in allfoods}
            picked=st.multiselect("Select one or more foods to delete",options=[a[0] for a in allfoods],format_func=lambda fid:labels.get(fid,str(fid)))
            if picked:
                st.warning(f"{len(picked)} food(s) selected for deletion.")
                confirm=st.checkbox("Yes, permanently delete the selected foods",key="confirm_multidel")
                if st.button("🗑️ Delete selected",type="primary",disabled=not confirm):
                    n=delete_discovered_foods(picked)
                    st.success(f"Deleted {n} food(s). Refresh to update the list.")
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
        col1,col2,col3=st.columns(3)
        col1.metric("🌿 Herbs",h);col1.metric("🍽️ Dishes",r)
        col2.metric("📝 Logs",f);col2.metric("🍽️ Foods",d)
        col3.metric("🏥 Remedies",rm);col3.metric("👤 Users",u)
    except: pass
