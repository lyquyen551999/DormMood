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
    tabs = st.tabs(["Regular Login", "Register"])

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
        db.reference("/waiting_list").child(st.session_state["user_token"]).delete()
        st.session_state.pop("matching_initialized", None)
        db.reference("/match_confirmations").child(st.session_state["user_token"]).delete()
        st.session_state.clear()
        st.rerun()

# ========== CHAT MATCH ==========
elif st.session_state["page"] == "chat_match":
    st.title("💬 Chat Matching")
    user_id = st.session_state.get("user_token")
    emotion = st.session_state.get("latest_emotion", "neutral")
    nickname = st.session_state.get("nickname", "Anonymous")
    now = time.time()

    # Clean up old entries (>30s)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if time.time() - info.get("timestamp", 0) > 30:
            db.reference("/waiting_list").child(uid).delete()

    # Add to waiting list only if not already in and not already matched
    if not db.reference("/waiting_list").child(user_id).get() and "matching_initialized" not in st.session_state:
        st.session_state["matching_initialized"] = True
        db.reference("/waiting_list").child(user_id).set({
            "emotion": emotion,
            "name": nickname,
            "timestamp": now,
            "is_online": True,
            "status": "matching"
        })

    # Match candidate (tôi là người chủ động)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if uid != user_id and info.get("emotion") == emotion and info.get("is_online") and now - info.get("timestamp", now) < 30:
            if info.get("status") == "matching":
                partner_id = uid
                room_id = "_".join(sorted([user_id, partner_id]))
                st.session_state["potential_match"] = {
                    "partner_id": partner_id,
                    "room_id": room_id,
                    "partner_name": info.get("name", "Stranger")
                }
                break

    # Nếu tôi là người bị match (bị mời)
    if "potential_match" not in st.session_state:
        confirmations = db.reference("/match_confirmations").get() or {}
        for room_id, confirms in confirmations.items():
            if user_id in confirms and confirms[user_id] != True:
                partner_id = next((uid for uid in confirms if uid != user_id), None)
                if partner_id:
                    partner_info = db.reference("/waiting_list").child(partner_id).get()
                    st.session_state["potential_match"] = {
                        "partner_id": partner_id,
                        "room_id": room_id,
                        "partner_name": partner_info.get("name", "Stranger") if partner_info else "Stranger"
                    }
                    break

    # Matching confirmation
    if "potential_match" in st.session_state:
        match = st.session_state["potential_match"]
        confirmation_ref = db.reference("/match_confirmations").child(match["room_id"])
        current_confirmations = confirmation_ref.get() or {}

        if current_confirmations.get(user_id) != True:
            decision = st.radio(
                f"🤝 {match['partner_name']} is available to chat. Do you want to connect?",
                ["Yes", "No"], index=None, horizontal=True
            )
            if decision == "Yes":
                confirmation_ref.update({user_id: True})
                st.info("✅ Waiting for your partner to confirm...")
                time.sleep(3)
                st.rerun()
            elif decision == "No":
                st.info("❌ You declined the match. Looking for someone else...")
                st.session_state.pop("potential_match", None)
                confirmation_ref.delete()
                time.sleep(2)
                st.rerun()

        # Nếu cả hai đã xác nhận
        current_confirmations = confirmation_ref.get() or {}
        if set(current_confirmations.keys()) == {user_id, match["partner_id"]} and all(current_confirmations.values()):
            room_ref = db.reference("/chat_rooms").child(match["room_id"])
            if not room_ref.get():
                room_ref.set({
                    "members": [user_id, match["partner_id"]],
                    "timestamp": now
                })

            db.reference("/waiting_list").child(user_id).delete()
            db.reference("/waiting_list").child(match["partner_id"]).delete()
            db.reference("/match_confirmations").child(match["room_id"]).delete()

            st.session_state["partner_id"] = match["partner_id"]
            st.session_state["partner_name"] = match["partner_name"]
            st.session_state["chat_mode"] = "1-1"
            st.session_state["page"] = "chat_room"
            st.session_state.pop("potential_match", None)
            st.rerun()
        elif current_confirmations.get(user_id) == True:
            st.info("⏳ Waiting for your partner to confirm...")

    # Nút huỷ
    if st.button("🛑 Stop Matching and Go Back"):
        db.reference("/waiting_list").child(user_id).delete()
        st.session_state.pop("matching_initialized", None)
        st.session_state.pop("potential_match", None)
        st.session_state["page"] = "mood_journal"
        st.rerun()

    time.sleep(5)
    st.rerun()

    current_confirmations = confirmation_ref.get() or {}
    st.write("🧪 DEBUG:", {
        "room_id": match["room_id"],
        "user_id": user_id,
        "partner_id": match["partner_id"],
        "confirmations": current_confirmations
    })



# ========== CHAT ROOM ==========
elif st.session_state["page"] == "chat_room":
    st.title("💬 Realtime Chat Room")
    chat_db = ChatFirebase()

    user_id = st.session_state.get("user_token", "anonymous")
    if "nickname" not in st.session_state:
        st.session_state["nickname"] = f"User-{user_id[-5:]}"
    nickname = st.text_input("Your nickname:", st.session_state["nickname"])
    st.session_state["nickname"] = nickname

    mode = st.session_state.get("chat_mode", "1-1")
    partner_id = st.session_state.get("partner_id")
    is_group = False

    if mode == "1-1" and partner_id:
        room_id = "_".join(sorted([user_id, partner_id]))
    else:
        room_id = "group_room"
        is_group = True

    if not chat_db.room_exists(room_id):
        members = [user_id] if is_group else [user_id, partner_id]
        chat_db.create_room(room_id, members, is_group)

    with st.form("chat_form", clear_on_submit=True):
        text = st.text_input("Your message:")
        submitted = st.form_submit_button("Send")
        if submitted and text.strip():
            chat_db.send_message(room_id, user_id, nickname, text)

    st.markdown("---")
    st.subheader("📨 Chat messages")
    messages = chat_db.get_messages(room_id)

    if messages:
        for msg in messages[-50:]:
            sender = msg.get("display_name", "Unknown")
            content = msg.get("text", "")
            raw_ts = msg.get("timestamp", "")
            try:
                formatted_ts = datetime.fromisoformat(raw_ts).strftime("%Y/%m/%d %H:%M")
            except:
                formatted_ts = raw_ts
            st.markdown(f"**{sender}** ({formatted_ts}): {content}")
    else:
        st.info("No messages yet.")

    if st.button("🚪 Leave Chat Room"):
        if mode == "1-1" and partner_id:
            db.reference("/chat_rooms").child(room_id).delete()
        st.session_state.pop("partner_id", None)
        st.session_state.pop("partner_name", None)
        st.session_state.pop("chat_mode", None)
        st.session_state.pop("matching_initialized", None)  # 💥 THÊM DÒNG NÀY
        st.session_state["page"] = "mood_journal"
        st.rerun()


    time.sleep(5)
    st.rerun()

