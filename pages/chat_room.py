
import streamlit as st
from chat_firebase import ChatFirebase
from datetime import datetime
import time

st.set_page_config(page_title="💬 Realtime Chat", page_icon="💬")

st.title("💬 Realtime Chat Room")

# Khởi tạo Firebase chat
chat_db = ChatFirebase()

# Lấy user_id và chọn nickname tạm thời
user_id = st.session_state.get("user_token", "anonymous")
if "nickname" not in st.session_state:
    st.session_state["nickname"] = f"User-{user_id[-5:]}"
nickname = st.text_input("Your nickname (you can change):", st.session_state["nickname"])
st.session_state["nickname"] = nickname

# Chọn chế độ 1-1 hoặc nhóm
mode = st.radio("Chat mode", ["1-1", "Group"])
partner_id = None
is_group = False

if mode == "1-1":
    partner_id = st.text_input("Enter partner ID:")
    if partner_id:
        room_id = "_".join(sorted([user_id, partner_id]))
else:
    room_id = "group_room"
    is_group = True

# Tạo phòng nếu chưa có
if not chat_db.room_exists(room_id):
    members = [user_id] if is_group else [user_id, partner_id]
    chat_db.create_room(room_id, members, is_group)

# Gửi tin nhắn
with st.form("chat_form", clear_on_submit=True):
    text = st.text_input("Your message:")
    submitted = st.form_submit_button("Send")
    if submitted and text.strip():
        chat_db.send_message(room_id, user_id, nickname, text)

# Hiển thị tin nhắn
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

# Tự động refresh mỗi 5 giây
time.sleep(5)
st.rerun()
