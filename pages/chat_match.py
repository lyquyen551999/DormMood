import streamlit as st
from matchmaker import MatchMaker
import threading
import time
from firebase_admin import db
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Chat Matching", page_icon="💬")

st.title("💬 Chat Matching")

user_id = st.session_state.get("user_token", "anonymous")
emotion = st.session_state.get("latest_emotion", "neutral")
nickname = st.session_state.get("nickname", "Anonymous")

st.markdown(f"🧠 Your current emotion: **{emotion}**")
st.write("🔍 Searching for someone to talk to...")

matcher = MatchMaker()
match_result = matcher.find_match(emotion, user_id, name=nickname)

# Sau khi match thành công:
if match_result["success"]:
    st.session_state["partner_id"] = match_result["partner_id"]
    st.session_state["partner_name"] = match_result["partner_name"]
    st.session_state["chat_mode"] = "1-1"
    switch_page("chat_room")  # Chuyển sang file pages/chat_room.py
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
            time.sleep(10)
        except:
            break

threading.Thread(target=heartbeat, args=(user_id,), daemon=True).start()
