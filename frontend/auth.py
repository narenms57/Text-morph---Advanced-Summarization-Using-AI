import httpx
import streamlit as st

API_URL = "http://localhost:8000"  # Backend URL

def login(email: str, password: str):
    """
    Calls backend /auth/login endpoint.
    Returns a tuple: (success: bool, user_data: dict or None, token: str or None)
    """
    login_data = {"email": email, "password": password}
    try:
        response = httpx.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        user = data.get("user")  # user info from backend

        if token and user:
            return True, user, token
        else:
            return False, None, None  # must return 3 values

    except httpx.HTTPError as e:
        detail = e.response.json().get("detail") if e.response else "HTTP error"
        st.error(f"Login failed: {detail}")
        return False, None, None  # must return 3 values
    except Exception as ex:
        st.error(f"Unexpected error during login: {str(ex)}")
        return False, None, None  # must return 3 values

def logout():
    """
    Clears Streamlit session state.
    """
    st.session_state.clear()
