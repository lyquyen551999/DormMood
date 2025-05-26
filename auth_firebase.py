import firebase_admin
from firebase_admin import credentials, auth
import streamlit as st

# 👉 Hủy các app Firebase cũ nếu đã tồn tại
for app in firebase_admin._apps.values():
    firebase_admin.delete_app(app)

# 👉 Khởi tạo lại từ secrets đúng
cred = credentials.Certificate({
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"],
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
})
firebase_admin.initialize_app(cred, {
    "databaseURL": st.secrets["firebase"]["databaseURL"]
})
