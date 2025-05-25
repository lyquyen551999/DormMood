
import streamlit as st
from matchmaker import MatchMaker
import threading
import time
from firebase_admin import db

st.set_page_config(page_title="Chat Matching", page_icon="💬")

st.title("💬 Chat Matching")

user_id = st.session_state.get("user_token", "anonymous")
emotion = st.session_state.get("latest_emotion", "neutral")

st.markdown(f"🧠 Your current emotion: **{emotion}**")
st.write("🔍 Searching for someone to talk to...")

# Tạo matchmaker và tìm người phù hợp
matcher = MatchMaker()
nickname = st.session_state.get("nickname", "Anonymous")
match_result = matcher.find_match(emotion, user_id)

if match_result["success"]:
    st.success(f"🎉 Matched with: {match_result['partner_name']} (ID: {match_result['partner_id']})")
    st.markdown("✅ You can now enter the chat room.")
else:
    st.error("😢 No suitable match found at the moment. Please try again later.")

def heartbeat(user_id):
    ref = db.reference("/waiting_list").child(user_id)
    while True:
        try:
            ref.update({
                "is_online": True,
                "timestamp": time.time()
            })
            time.sleep(10)  # Cập nhật mỗi 10 giây
        except:
            break  # Stop nếu bị lỗi hoặc thoát app

# Gọi sau khi user nhấn 我要傾訴
threading.Thread(target=heartbeat, args=(user_id,), daemon=True).start()
