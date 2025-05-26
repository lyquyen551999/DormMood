import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
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
    # ===== NỘI DUNG TỪ chat_room.py =====
    import streamlit as st
    from chat_firebase import ChatFirebase
    import time

    st.set_page_config(page_title="💬 Realtime Chat", page_icon="💬")
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
            timestamp = msg.get("timestamp", "")
            st.markdown(f"**{sender}** ({timestamp}): {content}")
    else:
        st.info("No messages yet.")

    time.sleep(5)
    st.rerun()

