
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

# Kiểm tra nếu Firebase chưa được khởi tạo thì mới khởi tạo
if not firebase_admin._apps:
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


def firebase_register(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return True, {"localId": user.uid}
    except Exception as e:
        return False, str(e)

def firebase_login(email, password):
    import requests
    api_key = st.secrets["firebase"].get("api_key") or "AIzaSyATbz58jD0cuEMY8RS_0TSumY1-kDLgu6c"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.text
