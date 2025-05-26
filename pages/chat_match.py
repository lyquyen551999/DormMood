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
    st.warning("😢 No suitable match found at the moment. Trying again...")

    # Countdown timer
    countdown = 5
    with st.empty():
        for i in range(countdown, 0, -1):
            st.info(f"🔄 Retrying match in **{i}** second(s)...")
            time.sleep(1)

    # Sau countdown, rerun
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
