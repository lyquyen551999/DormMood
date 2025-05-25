
import requests

# 🔑 Replace this with your actual Web API Key from Firebase Console
FIREBASE_WEB_API_KEY = "AIzaSyDFd8ctdKlwpHERA3xd38YJrQSd4VNDGWA"

def firebase_register(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload)
    return res.ok, res.json()

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload)
    return res.ok, res.json()
