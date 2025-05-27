import streamlit as st
from auth_firebase import firebase_login, firebase_register
import uuid
import time
import threading
from firebase_admin import db
from chat_firebase import ChatFirebase
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import random
from collections import defaultdict

st.set_page_config(page_title="DormMood", page_icon="🔐", layout="centered")

# Hide sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ========== LOGIN ==========
if st.session_state["page"] == "login":
    st.title("🔐 DormMood Login Interface")
    st.write("Please choose a login method:")
    tabs = st.tabs(["Regular Login", "Register"])

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
                st.error("Login failed")
    with tabs[1]:
            new_email = st.text_input("Email", key="register_email")
            new_password = st.text_input("Password", type="password", key="register_password")
            if st.button("Register"):
                success, result = firebase_register(new_email, new_password)
                if success:
                    st.session_state["user_token"] = result["localId"]
                    st.session_state["page"] = "mood_journal"
                    st.rerun()
                else:
                    st.error("Registration failed")
    


# ========== JOURNAL ==========
elif st.session_state.get("page") == "mood_journal":
    # ========= Đa ngôn ngữ =========
    LANGUAGE_MAP = {
        "English": {
            "title": "🧠 Mood Journal",
            "write_thoughts": "Write your thoughts...",
            "submit": "Submit Entry",
            "saved": "✅ Entry saved with emotion:",
            "suggestion": "🧠 Suggested action:",
            "view_chart": "📈 View Mood Chart",
            "chart_title": "📈 Mood Trend Over Time",
            "date": "Date",
            "mood_score": "Mood Score"
        },
        "Vietnamese": {
            "title": "🧠 Nhật ký cảm xúc",
            "write_thoughts": "Viết suy nghĩ của bạn...",
            "submit": "Ghi lại",
            "saved": "✅ Đã lưu với cảm xúc:",
            "suggestion": "🧠 Gợi ý hành động:",
            "view_chart": "📈 Xem biểu đồ cảm xúc",
            "chart_title": "📈 Biểu đồ xu hướng cảm xúc",
            "date": "Ngày",
            "mood_score": "Chỉ số cảm xúc"
        },
        "繁體中文": {
            "title": "🧠 心情日記",
            "write_thoughts": "寫下你的心情...",
            "submit": "提交紀錄",
            "saved": "✅ 已儲存，偵測到情緒:",
            "suggestion": "🧠 建議行動:",
            "view_chart": "📈 查看心情圖表",
            "chart_title": "📈 心情變化趨勢圖",
            "date": "日期",
            "mood_score": "心情分數"
        }
    }
    
    SAD_ACTION_SUGGESTIONS = {
        "English": [
            "🧘 Try 5 minutes of deep breathing or meditation.",
            "📞 Call a friend or family member you trust.",
            "✍️ Write in a personal journal or draw your emotions.",
            "🚶 Go for a short walk outside, even just around the dorm.",
            "🎵 Listen to music that makes you feel understood or calm."
        ],
        "Vietnamese": [
            "🧘 Hãy thử hít thở sâu hoặc thiền trong 5 phút.",
            "📞 Gọi cho một người bạn hoặc người thân đáng tin cậy.",
            "✍️ Viết nhật ký hoặc vẽ ra cảm xúc của bạn.",
            "🚶 Đi bộ một chút bên ngoài, quanh ký túc xá cũng được.",
            "🎵 Nghe một bản nhạc khiến bạn thấy được chia sẻ."
        ],
        "繁體中文": [
            "🧘 試著深呼吸或冥想 5 分鐘。",
            "📞 打給你信任的朋友或家人。",
            "✍️ 寫日記或畫出你的情緒。",
            "🚶 出去走走，即使只是在宿舍附近。",
            "🎵 聽些能讓你平靜或被理解的音樂。"
        ]
    }
    
    # ========= Mood Mapping =========
    EMOJI_MAP = {
        "positive": ("😊", "Happy", 2),
        "neutral": ("😐", "Neutral", 0),
        "negative": ("🥺", "Depressed", -2)
    }

    lang = st.selectbox("🌐 Language / Ngôn ngữ / 語言", options=list(LANGUAGE_MAP.keys()), key="language_select")
    L = LANGUAGE_MAP.get(lang, LANGUAGE_MAP["English"])

    st.title(L["title"])

    user_id = st.session_state.get("user_token")
    analyzer = SentimentIntensityAnalyzer()

    user_text = st.text_area(L["write_thoughts"], key="thought_box")
    if st.button(L["submit"]):
        if user_text:
            score = analyzer.polarity_scores(user_text)["compound"]
            if score >= 0.4:
                emoji, emotion, mood_score = EMOJI_MAP["positive"]
            elif score <= -0.4:
                emoji, emotion, mood_score = EMOJI_MAP["negative"]
            else:
                emoji, emotion, mood_score = EMOJI_MAP["neutral"]

            timestamp = datetime.now().timestamp()
            db.reference("/journal_entries").push({
                "user_id": user_id,
                "text": user_text,
                "emotion": emotion,
                "emoji": emoji,
                "timestamp": timestamp,
                "score": mood_score
            })

            st.success(f"{L['saved']} {emoji} {emotion}")

            if emotion == "Depressed":
                suggestion = random.choice(SAD_ACTION_SUGGESTIONS[lang])
                st.info(f"{L['suggestion']} {suggestion}")

    if st.button(L["view_chart"]):
    st.session_state["view_chart"] = True
    st.rerun()
    
    if st.session_state.get("view_chart"):
        st.markdown("### 📈 " + {
            "en": "Mood Trend Over Time",
            "vi": "Biểu đồ xu hướng cảm xúc",
            "zh": "心情趨勢圖"
        }[st.session_state["lang"]])
    
        # Lấy dữ liệu từ Firebase (an toàn)
        all_entries = db.reference("/journal_entries").get() or {}
        entries = [entry for entry in all_entries.values() if entry.get("user_id") == user_id]
    
        if not entries:
            st.warning({
                "en": "No entries to display.",
                "vi": "Chưa có bản ghi nào để hiển thị.",
                "zh": "尚無紀錄可顯示。"
            }[st.session_state["lang"]])
        else:
            entries.sort(key=lambda e: e.get("timestamp", 0))
    
            dates = []
            scores = []
            for entry in entries:
                ts = entry.get("timestamp")
                emo = entry.get("emotion")
                if ts and emo in EMOTION_SCORE_MAP:
                    date = datetime.fromtimestamp(ts)
                    dates.append(date)
                    scores.append(EMOTION_SCORE_MAP[emo])
    
            # Vẽ biểu đồ
            fig, ax = plt.subplots()
            ax.plot(dates, scores, marker="o")
            ax.set_xlabel({
                "en": "Date",
                "vi": "Ngày",
                "zh": "日期"
            }[st.session_state["lang"]])
            ax.set_ylabel({
                "en": "Mood Score",
                "vi": "Điểm cảm xúc",
                "zh": "心情分數"
            }[st.session_state["lang"]])
            ax.set_title({
                "en": "🧠 Mood Trend Over Time",
                "vi": "🧠 Xu hướng cảm xúc theo thời gian",
                "zh": "🧠 心情隨時間變化圖"
            }[st.session_state["lang"]])
            ax.grid(True)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            fig.autofmt_xdate()
            st.pyplot(fig)

        if st.button(L["view_chart"]):
        st.session_state["view_chart"] = True
        st.rerun()
    
        if st.session_state.get("view_chart"):
            if st.button("🔙 " + {
                "English": "Back to Journal",
                "Vietnamese": "Quay lại nhật ký",
                "繁體中文": "返回日記"
            }[lang]):
                st.session_state["view_chart"] = False
                st.rerun()

 




# ========== CHAT MATCH ==========
elif st.session_state["page"] == "chat_match":
    st.title("💬 Chat Matching")

    user_id = st.session_state.get("user_token")
    emotion = st.session_state.get("latest_emotion", "neutral")
    nickname = st.session_state.get("nickname", "Anonymous")
    now = time.time()

    # 🧹 Clean old waiting entries (>30s)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if time.time() - info.get("timestamp", 0) > 30:
            db.reference("/waiting_list").child(uid).delete()

    # ✅ Add to waiting_list if not already present
    if not db.reference("/waiting_list").child(user_id).get():
        db.reference("/waiting_list").child(user_id).set({
            "emotion": emotion,
            "name": nickname,
            "timestamp": now,
            "is_online": True,
            "status": "matching"
        })

    # 🚀 Try to find a match (active role)
    candidates = db.reference("/waiting_list").get()
    for uid, info in (candidates or {}).items():
        if uid != user_id and info.get("emotion") == emotion and info.get("is_online") and time.time() - info.get("timestamp", 0) < 30:
            room_id = "_".join(sorted([user_id, uid]))

            room_ref = db.reference("/chat_rooms").child(room_id)
            if not room_ref.get():
                room_ref.set({
                    "members": [user_id, uid],
                    "timestamp": now
                })

            # Remove both from waiting_list
            db.reference("/waiting_list").child(user_id).delete()
            db.reference("/waiting_list").child(uid).delete()

            # Redirect to chat room
            st.session_state["partner_id"] = uid
            st.session_state["partner_name"] = info.get("name", "Stranger")
            st.session_state["chat_mode"] = "1-1"
            st.session_state["page"] = "chat_room"
            st.rerun()

    # 👀 Passive role: check if someone already matched me and created room
    room_candidates = db.reference("/chat_rooms").get() or {}
    for room_id, room_data in room_candidates.items():
        members = room_data.get("members", [])
        if user_id in members:
            other_id = next((uid for uid in members if uid != user_id), None)
            if other_id:
                st.session_state["partner_id"] = other_id
                st.session_state["partner_name"] = "Stranger"
                st.session_state["chat_mode"] = "1-1"
                st.session_state["page"] = "chat_room"
                st.rerun()

    # Waiting display
    st.info("⏳ Looking for someone to chat with...")

    if st.button("🛑 Stop Matching and Go Back"):
        db.reference("/waiting_list").child(user_id).delete()
        st.session_state["page"] = "mood_journal"
        st.rerun()

    time.sleep(5)
    st.rerun()


# ========== CHAT ROOM ==========
elif st.session_state["page"] == "chat_room":
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
            raw_ts = msg.get("timestamp", "")
            try:
                formatted_ts = datetime.fromisoformat(raw_ts).strftime("%Y/%m/%d %H:%M")
            except:
                formatted_ts = raw_ts
            st.markdown(f"**{sender}** ({formatted_ts}): {content}")
    else:
        st.info("No messages yet.")

    if st.button("🚪 Leave Chat Room"):
        if mode == "1-1" and partner_id:
            db.reference("/chat_rooms").child(room_id).delete()
        st.session_state.pop("partner_id", None)
        st.session_state.pop("partner_name", None)
        st.session_state.pop("chat_mode", None)
        st.session_state.pop("matching_initialized", None)  # 💥 THÊM DÒNG NÀY
        st.session_state["page"] = "mood_journal"
        st.rerun()


    time.sleep(5)
    st.rerun()

