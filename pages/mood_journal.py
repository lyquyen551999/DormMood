import streamlit as st
from emotion_database import EmotionDatabase

st.set_page_config(page_title="Mood Journal", page_icon="📘")

db = EmotionDatabase()
user_id = st.session_state.get("user_token")

if not user_id:
    st.warning("You must log in first.")
    st.stop()

tab1, tab2 = st.tabs(["➕ Add Mood", "📜 My Mood Timeline"])

with tab1:
    st.subheader("📝 Add Mood Entry")
    mood = st.selectbox("Mood", ["😊 Happy", "😢 Sad", "😠 Angry", "😰 Anxious", "😐 Neutral", "😭 Depressed"])
    note = st.text_area("Your thoughts...")
    if st.button("Submit"):
        success = db.save_mood(user_id, mood, note)
        if success:
            st.success("Mood saved!")
        else:
            st.error("Something went wrong.")

    if st.button("🗣️ 我要傾訴"):
        # Ghi cảm xúc vào session_state để MatchMaker sử dụng
        st.session_state["latest_emotion"] = mood
        st.session_state["page"] = "chat_match"
        st.experimental_rerun()


with tab2:
    st.subheader("📅 Your Past Moods")
    entries = db.load_moods(user_id)
    if not entries:
        st.info("No moods yet.")
    else:
        for _, entry in entries:
            with st.expander(f"{entry['timestamp']} – {entry['mood']}"):
                st.write(entry["note"])

if st.button("🔙 Log out"):
    st.session_state.clear()
    st.experimental_rerun()
