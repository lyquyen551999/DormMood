import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
import auth_firebase  


# Cấu hình layout và ẩn sidebar
st.set_page_config(page_title="DormMood", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")

# CSS để ẩn sidebar hoàn toàn
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

# Khởi tạo session state
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# LOGIN PAGE
if st.session_state["page"] == "login":
    st.title("🔐 DormMood Login Interface")
    st.write("Please choose a login method:")
    tabs = st.tabs(["🔐 Regular Login", "🕵️ Anonymous Login", "📝 Register"])

    # Regular Login
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
                st.error("❌ Login failed")

    # Anonymous Login
    with tabs[1]:
        if st.button("Continue as Anonymous"):
            st.session_state["user_token"] = f"anon-{uuid.uuid4()}"
            st.session_state["page"] = "mood_journal"
            st.rerun()

    # Register
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
                st.error("❌ Registration failed")

# MOOD JOURNAL PAGE
elif st.session_state["page"] == "mood_journal":
    st.title("📔 Mood Journal")
    st.write(f"Welcome, user: `{st.session_state['user_token']}`")

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
        st.session_state.clear()
        st.rerun()

# CHAT MATCHING PAGE
elif st.session_state["page"] == "chat_match":
    from matchmaker import MatchMaker
    st.title("💬 Chat Matching")

    emotion = st.session_state.get("latest_emotion", "neutral")
    user_id = st.session_state.get("user_token", "anonymous")
    st.markdown(f"🧠 Your current emotion: **{emotion}**")
    st.write("🔍 Searching for someone to talk to...")

    matcher = MatchMaker()
    match_result = matcher.find_match(emotion, user_id)

    if match_result["success"]:
        st.success(f"🎉 Matched with: {match_result['partner_name']} (ID: {match_result['partner_id']})")
        st.markdown("✅ You can now enter the chat room.")
    else:
        st.error("😢 No suitable match found at the moment. Please try again later.")

    if st.button("← Back to Journal"):
        st.session_state["page"] = "mood_journal"
        st.rerun()

   
