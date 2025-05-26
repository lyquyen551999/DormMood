import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
import time
import threading
from firebase_admin import db
from matchmaker import MatchMaker
from chat_firebase import ChatFirebase
from datetime import datetime

st.set_page_config(page_title="DormMood", page_icon="🔐", layout="centered")

# Hide sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ========== LOGIN ==========
if st.session_state["page"] == "login":
    st.title("🔐 DormMood Login Interface")
    st.write("Please choose a login method:")
    tabs = st.tabs(["Regular Login", "Anonymous Login", "Register"])

    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            success, result = firebase_login(email, password)
            if success:
                st.session_state["user_token"] = result["localId"]
                st.session_state["page"] = "mood_journal"
                st.rerun()
            else:
                st.error("Login failed")

    with tabs[1]:
        if st.button("Continue as Anonymous"):
            anon_id = f"anon-{uuid.uuid4()}"
            st.session_state["user_token"] = anon_id
            st.session_state["nickname"] = "Stranger"
            st.session_state["page"] = "mood_journal"
            st.rerun()

    with tabs[2]:
        new_email = st.text_input("Email", key="register_email")
        new_password = st.text_input("Password", type="password", key="register_password")
        if st.button("Register"):
            success, result = firebase_register(new_email, new_password)
            if success:
                st.session_state["user_token"] = result["localId"]
                st.session_state["page"] = "mood_journal"
                st.rerun()
            else:
                st.error("Registration failed")

# ========== JOURNAL ==========
elif st.session_state["page"] == "mood_journal":
    st.title("📔 Mood Journal")
    st.write(f"Welcome, user: **{st.session_state.get('nickname', st.session_state['user_token'])}**")

    mood = st.selectbox("How do you feel today?", ["😊 Happy", "😢 Sad", "😠 Angry", "😰 Anxious", "😴 Tired"])
    note = st.text_area("Write your thoughts...")

    if st.button("Submit Entry"):
        with open("mood_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{st.session_state['user_token']}: {mood} - {note}\n")
        st.success("Entry saved!")

    if st.button("View My Timeline"):
        st.subheader("🕒 Mood Timeline")
        with open("mood_log.txt", "r", encoding="utf-8") as f:
            entries = f.readlines()
            for line in entries:
                if st.session_state["user_token"] in line:
                    st.markdown(f"- {line.strip()}")

    if st.button("🗣️ 我要傾訴"):
        st.session_state["latest_emotion"] = mood
        st.session_state["page"] = "chat_match"
        st.rerun()

    if st.button("Log out"):
        db.reference("/waiting_list").child(st.session_state["user_token"]).delete()  # ❌ Xóa khỏi waitlist nếu có
        st.session_state.clear()
        st.rerun()

# ========== CHAT MATCH ==========
elif st.session_state["page"] == "chat_match":
    st.title("💬 Chat Matching")
    user_id = st.session_state.get("user_token")
    emotion = st.session_state.get("latest_emotion", "neutral")
    nickname = st.session_state.get("nickname", "Anonymous")

    st.markdown(f"🧠 Your current emotion: **{emotion}**")
    st.info("🔍 Looking for someone with similar feelings to talk to...")

    # Add user to waiting list
    db.reference("/waiting_list").child(user_id).set({
        "emotion": emotion,
        "name": nickname,
        "timestamp": time.time()
    })

    # Step 2: try to find a match
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if uid != user_id and info.get("emotion") == emotion:
            partner_id = uid
            room_id = "_".join(sorted([user_id, partner_id]))
            st.session_state["potential_match"] = {
                "partner_id": partner_id,
                "room_id": room_id,
                "partner_name": info.get("name", "Stranger")
            }
            break

    if "potential_match" in st.session_state:
        match = st.session_state["potential_match"]
        decision = st.radio(f"🤝 {match['partner_name']} is available to chat. Do you want to connect?", ["Yes", "No"], index=None, horizontal=True)
        if decision == "Yes":
            db.reference("/match_confirmations").child(match["room_id"]).update({user_id: True})
            confirmations = db.reference("/match_confirmations").child(match["room_id"]).get()
            if confirmations.get(match["partner_id"]) == True and confirmations.get(user_id) == True:
                db.reference("/waiting_list").child(user_id).delete()
                db.reference("/waiting_list").child(match["partner_id"]).delete()
                db.reference("/chat_rooms").child(match["room_id"]).set({"members": [user_id, match["partner_id"]], "timestamp": time.time()})
                st.session_state["partner_id"] = match["partner_id"]
                st.session_state["partner_name"] = match["partner_name"]
                st.session_state["chat_mode"] = "1-1"
                st.session_state["page"] = "chat_room"
                st.session_state.pop("potential_match")
                st.rerun()
            else:
                st.info("Waiting for your partner to confirm...")
                time.sleep(5)
                st.rerun()
        elif decision == "No":
            st.info("You declined the match. Looking for someone else...")
            st.session_state.pop("potential_match")
            time.sleep(3)
            st.rerun()

    if st.button("🛑 Stop Matching and Go Back"):
        db.reference("/waiting_list").child(user_id).delete()
        st.session_state["page"] = "mood_journal"
        st.rerun()

    time.sleep(5)
    st.rerun()

# ========== CHAT ROOM ==========
elif st.session_state["page"] == "chat_room":
    st.title("💬 Realtime Chat Room")
    st.write("🚧 Chat room feature temporarily paused. Return to mood journal.")
    if st.button("⬅️ Go Back"):
        st.session_state.pop("partner_id", None)
        st.session_state.pop("partner_name", None)
        st.session_state.pop("chat_mode", None)
        st.session_state["page"] = "mood_journal"
        st.rerun()
