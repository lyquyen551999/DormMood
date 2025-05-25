
import streamlit as st
from matchmaker import MatchMaker

st.set_page_config(page_title="Chat Matching", page_icon="💬")

st.title("💬 Chat Matching")

user_id = st.session_state.get("user_token", "anonymous")
emotion = st.session_state.get("latest_emotion", "neutral")

st.markdown(f"🧠 Your current emotion: **{emotion}**")
st.write("🔍 Searching for someone to talk to...")

# Tạo matchmaker và tìm người phù hợp
matcher = MatchMaker()
match_result = matcher.find_match(emotion, user_id)

if match_result["success"]:
    st.success(f"🎉 Matched with: {match_result['partner_name']} (ID: {match_result['partner_id']})")
    st.markdown("✅ You can now enter the chat room.")
else:
    st.error("😢 No suitable match found at the moment. Please try again later.")
