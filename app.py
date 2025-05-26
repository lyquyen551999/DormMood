import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
import chat_room  # ✅ import thủ công các module cần dùng
import matchmaker  # Chỉ cần nếu gọi trong login hoặc preload
import mood_journal  # Gợi ý nếu bạn đã chia file riêng
import chat_match  # Nếu tách file riêng
# Nếu không chia file riêng, thì viết từng phần trực tiếp (xem ví dụ dưới)

# Cấu hình
st.set_page_config(page_title="DormMood", page_icon="🔐", layout="centered")

# Ẩn sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo trạng thái trang
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ========== LOGIN PAGE ==========
if st.session_state["page"] == "login":
    st.title("🔐 DormMood Login Interface")
    st.write("Please choose a login method:")
    tabs = st.tabs(["🔐 Regular Login", "🕵️ Anonymous Login", "📝 Register"])

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

    with tabs[1]:
        if st.button("Continue as Anonymous"):
            st.session_state["user_token"] = f"anon-{uuid.uuid4()}"
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
                st.error("❌ Registration failed")

# ========== MOOD JOURNAL PAGE ==========
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

# ========== CHAT MATCHING PAGE ==========
elif st.session_state["page"] == "chat_match":
    import chat_match  # Gọi file riêng nếu bạn tách, hoặc dán nội dung trực tiếp vào đây

# ========== CHAT ROOM ==========
elif st.session_state["page"] == "chat_room":
    import chat_room  # Gọi file riêng nếu bạn tách, hoặc dán nội dung trực tiếp vào đây
