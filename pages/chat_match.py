import streamlit as st
from matchmaker import MatchMaker
import threading
import time
from firebase_admin import db
from streamlit_extras.switch_page_button import switch_page  # pip install streamlit-extras

st.set_page_config(page_title="Chat Matching", page_icon="💬")
st.title("💬 Chat Matching")

user_id = st.session_state.get("user_token", "anonymous")
emotion = st.session_state.get("latest_emotion", "neutral")
nickname = st.session_state.get("nickname", "Anonymous")

st.markdown(f"🧠 Your current emotion: **{emotion}**")
st.write("🔍 Searching for someone to talk to...")

# Khởi tạo MatchMaker
matcher = MatchMaker()

# Match thử
match_result = matcher.find_match(emotion, user_id, name=nickname)
st.write("✅ Match result:", match_result)

if match_result["success"]:
    st.success(f"🎉 Matched with: {match_result['partner_name']} (ID: {match_result['partner_id']})")
    st.session_state["partner_id"] = match_result["partner_id"]
    st.session_state["partner_name"] = match_result["partner_name"]
    st.session_state["chat_mode"] = "1-1"
    switch_page("chat_room")  # Tự động sang chat room
else:
    st.info("⏳ No match yet... retrying in 5 seconds")

    # Chỉ rerun mỗi 5 giây 1 lần (để tránh vòng lặp vô tận)
    now = time.time()
    last_attempt = st.session_state.get("last_match_attempt", 0)
    if now - last_attempt > 5:
        st.session_state["last_match_attempt"] = now
        time.sleep(5)
        st.experimental_rerun()

# 💓 Heartbeat giữ online
def heartbeat(user_id):
    ref = db.reference("/waiting_list").child(user_id)
    while True:
        try:
            ref.update({
                "timestamp": time.time()
            })
            time.sleep(10)
        except:
            break

threading.Thread(target=heartbeat, args=(user_id,), daemon=True).start()
