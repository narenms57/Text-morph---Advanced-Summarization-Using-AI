import httpx
import streamlit as st

API_URL = "http://localhost:8000"  # Replace with your backend URL

def login(email: str, password: str):
    """
    Calls your backend /login endpoint with email and password.
    On success, stores the JWT access token in Streamlit session_state.
    """
    login_data = {"email": email, "password": password}
    try:
        response = httpx.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        user = data.get("user") #user info from backend
        if token and user:
            st.session_state["access_token"] = token
            st.session_state["logged_in"] = True
            st.session_state["email"] = user.get("email")
            st.session_state["user_id"]= user.get("id")  # Store user ID in session state
            return True,user
        else:
            return False,None
    except httpx.HTTPError as e:
        error_detail = "Unknown error"
        if e.response is not None:
            try:

                error_detail = e.response.json().get('detail', error_detail)
            except Exception:
                error_detail = e.response.text or error_detail
        st.error(f"Login failed: {error_detail}")
        return False,None

def logout():
    """
    Clears Streamlit session state.
    """
    st.session_state.clear()
