"""
Firebase Authentication Module for Canvas Color Updater
Handles user authentication via Firebase Auth REST API
"""

import streamlit as st
import requests
import os
from typing import Optional, Dict, Any

# Firebase Auth REST API endpoint
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"


def get_firebase_api_key() -> Optional[str]:
    """Get Firebase API key from environment or session state."""
    return os.environ.get("FIREBASE_API_KEY") or st.session_state.get("firebase_api_key")


def sign_in_with_email_password(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in user with email and password using Firebase Auth REST API.

    Returns:
        Dict with user info on success, or error info on failure
    """
    api_key = get_firebase_api_key()
    if not api_key:
        return {"error": "Firebase API key not configured"}

    url = f"{FIREBASE_AUTH_URL}:signInWithPassword?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "user_id": data.get("localId"),
                "email": data.get("email"),
                "id_token": data.get("idToken"),
                "refresh_token": data.get("refreshToken"),
                "expires_in": data.get("expiresIn")
            }
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_message}

    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def sign_up_with_email_password(email: str, password: str) -> Dict[str, Any]:
    """
    Create new user with email and password using Firebase Auth REST API.

    Returns:
        Dict with user info on success, or error info on failure
    """
    api_key = get_firebase_api_key()
    if not api_key:
        return {"error": "Firebase API key not configured"}

    url = f"{FIREBASE_AUTH_URL}:signUp?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "user_id": data.get("localId"),
                "email": data.get("email"),
                "id_token": data.get("idToken"),
                "refresh_token": data.get("refreshToken")
            }
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_message}

    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def send_password_reset(email: str) -> Dict[str, Any]:
    """Send password reset email."""
    api_key = get_firebase_api_key()
    if not api_key:
        return {"error": "Firebase API key not configured"}

    url = f"{FIREBASE_AUTH_URL}:sendOobCode?key={api_key}"

    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return {"success": True, "message": "Password reset email sent"}
        else:
            data = response.json()
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_message}

    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def refresh_id_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh the ID token using a refresh token."""
    api_key = get_firebase_api_key()
    if not api_key:
        return {"error": "Firebase API key not configured"}

    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    try:
        response = requests.post(url, data=payload)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "id_token": data.get("id_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in")
            }
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_message}

    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def init_session_state():
    """Initialize authentication-related session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "id_token" not in st.session_state:
        st.session_state.id_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None


def login(email: str, password: str) -> bool:
    """
    Attempt to log in user and update session state.

    Returns:
        True if login successful, False otherwise
    """
    result = sign_in_with_email_password(email, password)

    if result.get("success"):
        st.session_state.authenticated = True
        st.session_state.user_email = result.get("email")
        st.session_state.user_id = result.get("user_id")
        st.session_state.id_token = result.get("id_token")
        st.session_state.refresh_token = result.get("refresh_token")
        return True
    else:
        st.error(f"Login failed: {result.get('error')}")
        return False


def logout():
    """Clear session state and log out user."""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_id = None
    st.session_state.id_token = None
    st.session_state.refresh_token = None
    # Clear any stored credentials
    if "canvas_token" in st.session_state:
        del st.session_state.canvas_token
    if "openrouter_key" in st.session_state:
        del st.session_state.openrouter_key


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return st.session_state.get("authenticated", False)


def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("Please log in to access this feature.")
            return None
        return func(*args, **kwargs)
    return wrapper


def render_login_form():
    """Render the login/signup form UI."""
    init_session_state()

    if is_authenticated():
        st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()
        return True

    # Check if Firebase is configured
    if not get_firebase_api_key():
        st.sidebar.info("Authentication disabled (no Firebase API key)")
        return True  # Allow access without auth if not configured

    st.sidebar.header("🔐 Authentication")

    tab1, tab2 = st.sidebar.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if email and password:
                    if login(email, password):
                        st.success("Login successful!")
                        st.rerun()
                else:
                    st.warning("Please enter email and password")

        if st.button("Forgot Password?", key="forgot_pwd"):
            email = st.text_input("Enter your email for reset", key="reset_email")
            if email:
                result = send_password_reset(email)
                if result.get("success"):
                    st.success("Password reset email sent!")
                else:
                    st.error(result.get("error"))

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="new_email")
            new_password = st.text_input("Password", type="password", key="new_pwd")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pwd")
            signup_submit = st.form_submit_button("Create Account")

            if signup_submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_email and new_password:
                    result = sign_up_with_email_password(new_email, new_password)
                    if result.get("success"):
                        st.success("Account created! Please log in.")
                    else:
                        st.error(f"Sign up failed: {result.get('error')}")

    return False
