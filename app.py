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
from matplotlib.ticker import MaxNLocator
import pytz


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
elif st.session_state["page"] == "mood_journal":
    
    # Ngôn ngữ hỗ trợ
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
            "mood_score": "Mood Score",
            "timeline": "Mood Timeline",
            "back": "Back to Journal"
        },
        "Vietnamese": {
            "title": "🧠 Nhật ký cảm xúc",
            "write_thoughts": "Viết suy nghĩ của bạn...",
            "submit": "Ghi lại",
            "saved": "✅ Đã lưu với cảm xúc:",
            "suggestion": "🧠 Gợi ý hành động:",
            "view_chart": "📈 Xem biểu đồ cảm xúc",
            "chart_title": "📈 Xu hướng cảm xúc theo thời gian",
            "date": "Ngày",
            "mood_score": "Chỉ số cảm xúc",
            "timeline": "Dòng thời gian cảm xúc",
            "back": "Quay lại nhật ký"
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
            "mood_score": "心情分數",
            "timeline": "心情時間軸",
            "back": "返回日記"
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
            "✍️ 寫日誌或畫出你的情緒。",
            "🚶 出去走走，即使只是在宿舍附近。",
            "🎵 聽些能讓你平靜或被理解的音樂。"
        ]
    }

    EMOTION_SCORE_MAP = {
        "Happy": ("😊", 2),
        "Neutral": ("😐", 0),
        "Depressed": ("🥺", -2)
    }

    lang = st.selectbox("🌐 Language / Ngôn ngữ / 語言", list(LANGUAGE_MAP.keys()))
    L = LANGUAGE_MAP[lang]
    st.session_state["lang"] = lang
    st.title(L["title"])

    user_id = st.session_state.get("user_token", "demo")
    analyzer = SentimentIntensityAnalyzer()

    user_text = st.text_area(L["write_thoughts"], key="journal_input")
    if st.button(L["submit"]):
        if user_text:
            score = analyzer.polarity_scores(user_text)["compound"]
            if score >= 0.4:
                emotion = "Happy"
            elif score <= -0.4:
                emotion = "Depressed"
            else:
                emotion = "Neutral"

            emoji, mood_score = EMOTION_SCORE_MAP[emotion]

            db.reference("/journal_entries").push({
                "user_id": user_id,
                "text": user_text,
                "emotion": emotion,
                "emoji": emoji,
                "timestamp": time.time(),
                "score": mood_score
            })

            st.session_state["latest_emotion"] = emoji
            st.success(f"{L['saved']} {emoji} {emotion}")

            if emotion == "Depressed":
                st.info(f"{L['suggestion']} {random.choice(SAD_ACTION_SUGGESTIONS[lang])}")
        else:
            st.warning("⚠ Please enter some text.")

    # Nút hiển thị biểu đồ
    if st.button(L["view_chart"]):
        st.session_state["view_chart"] = True
        st.rerun()

    # Nếu ở chế độ xem biểu đồ
    if st.session_state.get("view_chart"):
        if st.button("🔙 " + L["back"]):
            st.session_state["view_chart"] = False
            st.rerun()

        all_entries = db.reference("/journal_entries").get() or {}
        entries = [e for e in all_entries.values() if e.get("user_id") == user_id]

        # Sắp xếp theo thời gian
        entries = sorted(entries, key=lambda e: e.get("timestamp", 0))

        if entries:
            dates = []
            scores = []
            for e in entries:
                emo = e.get("emotion", "").strip().capitalize()
                ts = e.get("timestamp")
                tz = pytz.timezone("Asia/Taipei")
                if ts and emo in EMOTION_SCORE_MAP:
                    dt = datetime.fromtimestamp(ts, tz)
                    dates.append(dt)
                    scores.append(EMOTION_SCORE_MAP[emo][1])

            if dates and scores:
                fig, ax = plt.subplots()
                ax.plot(dates, scores, marker='o')
                ax.set_title(L["chart_title"])
                ax.set_xlabel(L["date"])
                ax.set_ylabel(L["mood_score"])
                ax.grid(True, linestyle="--", alpha=0.3)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
                ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.info("📭 No mood scores yet.")
        else:
            st.info("📭 No entries found.")

    # Timeline bên dưới
    all_entries = db.reference("/journal_entries").get() or {}
    timeline_entries = [e for e in all_entries.values() if e.get("user_id") == user_id]
    if timeline_entries:
        st.subheader("🕰️ " + L["timeline"])
        for e in sorted(timeline_entries, key=lambda x: x.get("timestamp", 0), reverse=True):       
            
            emo = e.get("emotion", "Neutral").strip().capitalize()
            if emo in EMOTION_SCORE_MAP:
                emoji = EMOTION_SCORE_MAP[emo][0]
            else:
                emoji = "❓"
                
            text = e.get("text", "")
            ts = e.get("timestamp")
            time_str = datetime.fromtimestamp(ts, tz).strftime("%d/%m %H:%M") if ts else ""
            st.markdown(f"- **{emoji} {emo}** ({time_str}): {text}")
    else:
        st.info("📭 No entries yet.")

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

