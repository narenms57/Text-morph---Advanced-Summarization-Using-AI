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
        if token:
            st.session_state["access_token"] = token
            st.session_state["logged_in"] = True
            st.session_state["email"] = email
            return True
        else:
            return False
    except httpx.HTTPError as e:

        st.error(f"Login failed: {e.response.json().get('detail')}")
        return False
    except Exception:
        st.error("Unexpected error during login")
        return False

def logout():
    """
    Clears Streamlit session state.
    """
    st.session_state.clear()
