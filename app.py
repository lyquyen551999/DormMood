import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
import time
import threading
from firebase_admin import db
from chat_firebase import ChatFirebase
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

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
# 📔 Giao diện Mood Journal
elif st.session_state["page"] == "mood_journal":
    st.title("📔 Mood Journal")

    # 🌟 Gán điểm cảm xúc
    EMOTION_SCORES = {
        "😊 Happy": 2,
        "🙂 Content": 1,
        "😐 Neutral": 0,
        "😟 Sad": -1,
        "😢 Depressed": -2
    }
    
    # 💡 Phân tích cảm xúc tự động
    def detect_emotion_vader(text):
        analyzer = SentimentIntensityAnalyzer()
        score = analyzer.polarity_scores(text)["compound"]
    
        if score > 0.5:
            return "😊 Happy"
        elif score > 0.2:
            return "🙂 Content"
        elif score > -0.2:
            return "😐 Neutral"
        elif score > -0.5:
            return "😟 Sad"
        else:
            return "😢 Depressed"

    user_id = st.session_state.get("user_token")
    nickname = st.session_state.get("nickname", f"User-{user_id[-5:]}")

    st.markdown(f"Welcome, user: **{user_id}**")

    # Nhập nội dung
    user_text = st.text_area("Write your thoughts...", key="journal_text_area")

    if st.button("Submit Entry", key="submit_journal"):
        if not user_text.strip():
            st.warning("Please write something before submitting.")
        else:
            # Phát hiện cảm xúc
            auto_emoji = detect_emotion_vader(user_text)
            st.session_state["latest_emotion"] = auto_emoji

            # Lưu Firebase
            entry_ref = db.reference("/journal_entries").push()
            entry_ref.set({
                "user_id": user_id,
                "emotion": auto_emoji,
                "text": user_text,
                "timestamp": time.time()
            })

            st.success(f"✅ Entry saved with emotion: {auto_emoji}")

    # Timeline
    if st.button("View My Timeline", key="view_timeline"):
        all_entries = db.reference("/journal_entries").get()
        st.markdown("### 🕰️ Mood Timeline")

        if all_entries:
            user_entries = [
                entry for entry in all_entries.values()
                if entry.get("user_id") == user_id
            ]
            if user_entries:
                for entry in sorted(user_entries, key=lambda x: x["timestamp"], reverse=True):
                    st.markdown(f"- **{user_id}**: {entry['emotion']} - {entry['text']}")
            else:
                st.info("No entries yet.")
        else:
            st.info("No entries found.")

    # Mood Chart
    if st.button("📈 View Mood Chart", key="view_chart"):
        all_entries = db.reference("/journal_entries").get()
        user_entries = [
            entry for entry in (all_entries or {}).values()
            if entry.get("user_id") == user_id
        ]

        if not user_entries:
            st.info("You don't have any mood entries yet.")
        else:
            # Lấy ngày & điểm cảm xúc
            dates = []
            scores = []
            for entry in sorted(user_entries, key=lambda x: x["timestamp"]):
                score = EMOTION_SCORES.get(entry["emotion"], 0)
                date = datetime.fromtimestamp(entry["timestamp"]).date()
                dates.append(date)
                scores.append(score)

            # Vẽ biểu đồ
            fig, ax = plt.subplots()
            ax.plot(dates, scores, marker='o', linestyle='-')
            ax.set_title("📈 Mood Trend Over Time")
            ax.set_ylabel("Mood Score")
            ax.set_xlabel("Date")
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
            st.pyplot(fig)



# ========== CHAT MATCH ==========
elif st.session_state["page"] == "chat_match":
    st.title("💬 Chat Matching")

    user_id = st.session_state.get("user_token")
    emotion = st.session_state.get("latest_emotion", "neutral")
    nickname = st.session_state.get("nickname", "Anonymous")
    now = time.time()

    # 🧹 Clean old waiting entries (>30s)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if time.time() - info.get("timestamp", 0) > 30:
            db.reference("/waiting_list").child(uid).delete()

    # ✅ Add to waiting_list if not already present
    if not db.reference("/waiting_list").child(user_id).get():
        db.reference("/waiting_list").child(user_id).set({
            "emotion": emotion,
            "name": nickname,
            "timestamp": now,
            "is_online": True,
            "status": "matching"
        })

    # 🚀 Try to find a match (active role)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if uid != user_id and info.get("emotion") == emotion and info.get("is_online") and time.time() - info.get("timestamp", 0) < 30:
            room_id = "_".join(sorted([user_id, uid]))

            room_ref = db.reference("/chat_rooms").child(room_id)
            if not room_ref.get():
                room_ref.set({
                    "members": [user_id, uid],
                    "timestamp": now
                })

            # Remove both from waiting_list
            db.reference("/waiting_list").child(user_id).delete()
            db.reference("/waiting_list").child(uid).delete()

            # Redirect to chat room
            st.session_state["partner_id"] = uid
            st.session_state["partner_name"] = info.get("name", "Stranger")
            st.session_state["chat_mode"] = "1-1"
            st.session_state["page"] = "chat_room"
            st.rerun()

    # 👀 Passive role: check if someone already matched me and created room
    room_candidates = db.reference("/chat_rooms").get() or {}
    for room_id, room_data in room_candidates.items():
        members = room_data.get("members", [])
        if user_id in members:
            other_id = next((uid for uid in members if uid != user_id), None)
            if other_id:
                st.session_state["partner_id"] = other_id
                st.session_state["partner_name"] = "Stranger"
                st.session_state["chat_mode"] = "1-1"
                st.session_state["page"] = "chat_room"
                st.rerun()

    # Waiting display
    st.info("⏳ Looking for someone to chat with...")

    if st.button("🛑 Stop Matching and Go Back"):
        db.reference("/waiting_list").child(user_id).delete()
        st.session_state["page"] = "mood_journal"
        st.rerun()

    time.sleep(5)
    st.rerun()


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

