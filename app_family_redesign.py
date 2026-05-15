import streamlit as st
import os
from datetime import date
import random
import json

st.set_page_config(page_title="Family Health Companion", layout="wide")

# ======================
# 🧠 MOCK DATA (Replace with DB later)
# ======================
if "family" not in st.session_state:
    st.session_state.family = [
        {"name": "Appa", "role": "Father", "energy": 6, "junk": 1},
        {"name": "Amma", "role": "Mother", "energy": 7, "junk": 0},
        {"name": "Anu", "role": "Kid", "energy": 8, "junk": 2},
        {"name": "Paati", "role": "Elder", "energy": 5, "junk": 0}
    ]

if "points" not in st.session_state:
    st.session_state.points = 0

if "streak" not in st.session_state:
    st.session_state.streak = 1


# ======================
# 🎯 HELPER FUNCTIONS
# ======================
def family_score():
    score = 0
    for m in st.session_state.family:
        score += m["energy"] * 10 - m["junk"] * 5
    return max(score // len(st.session_state.family), 0)


def get_badge(score):
    if score >= 80:
        return "🌟 Healthy Family"
    elif score >= 60:
        return "👍 Improving"
    else:
        return "⚠️ Needs Care"


def family_meal():
    meals = [
        "Ragi dosa + chutney",
        "Keerai sambar + red rice",
        "Vegetable soup + millet roti",
        "Idli + pepper rasam",
        "Curd rice + cucumber"
    ]
    return random.sample(meals, 3)


# ======================
# 🏡 SIDEBAR
# ======================
st.sidebar.title("🏡 Family Health")

page = st.sidebar.radio("Navigate", [
    "🏡 Today",
    "📝 Quick Log",
    "🍽️ Family Meal",
    "👶 Kids Fun",
    "🏆 Rewards"
])

# ======================
# 🏡 PAGE 1: TODAY DASHBOARD
# ======================
if page == "🏡 Today":
    st.title("🏡 Today at Home")

    score = family_score()
    badge = get_badge(score)

    cols = st.columns(len(st.session_state.family))

    for i, member in enumerate(st.session_state.family):
        with cols[i]:
            st.subheader(member["name"])
            st.write(f"👤 {member['role']}")
            st.metric("⚡ Energy", member["energy"])
            st.metric("🍔 Junk", member["junk"])

    st.markdown("---")

    st.metric("🏆 Family Score", f"{score}/100")
    st.success(f"Badge: {badge}")

    if score > 70:
        st.session_state.points += 10
        st.balloons()

    st.info("🌿 Tip: Avoid spicy food today. Drink buttermilk!")

# ======================
# 📝 PAGE 2: QUICK LOG
# ======================
elif page == "📝 Quick Log":
    st.title("📝 Log Your Day (Simple Mode)")

    name = st.selectbox("Who are you?", [m["name"] for m in st.session_state.family])

    mood = st.radio("How do you feel?", ["😊 Good", "😷 Sick", "⚡ Low Energy"])
    junk = st.radio("Did you eat junk?", ["No", "Yes"])

    if st.button("✅ Save"):
        for m in st.session_state.family:
            if m["name"] == name:
                m["energy"] = 8 if mood == "😊 Good" else 4
                m["junk"] = 1 if junk == "Yes" else 0

        st.session_state.streak += 1
        st.success("Saved!")

# ======================
# 🍽️ PAGE 3: FAMILY MEALS
# ======================
elif page == "🍽️ Family Meal":
    st.title("🍽️ Today's Family Meals")

    meals = family_meal()

    st.subheader("☀️ Breakfast")
    st.write(meals[0])

    st.subheader("🌞 Lunch")
    st.write(meals[1])

    st.subheader("🌙 Dinner")
    st.write(meals[2])

    st.info("🌿 These meals suit all family members")

# ======================
# 👶 PAGE 4: KIDS FUN MODE
# ======================
elif page == "👶 Kids Fun":
    st.title("👶 Kids Health Game")

    st.write("What did you eat today?")

    fruits = st.checkbox("🍎 Fruits")
    veggies = st.checkbox("🥦 Vegetables")
    junk = st.checkbox("🍫 Junk")

    if st.button("🎉 Check Result"):
        if junk:
            st.error("Oh no! Too much junk 😢")
        elif fruits and veggies:
            st.success("🎉 Super Kid! You are strong 💪")
            st.balloons()
        else:
            st.warning("Try eating more healthy food!")

# ======================
# 🏆 PAGE 5: REWARDS
# ======================
elif page == "🏆 Rewards":
    st.title("🏆 Family Rewards")

    st.metric("⭐ Points", st.session_state.points)
    st.metric("🔥 Streak", f"{st.session_state.streak} days")

    if st.session_state.points >= 50:
        st.success("🎉 You unlocked: Healthy Hero Badge")

    st.info("Keep eating healthy to earn rewards!")
