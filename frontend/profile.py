import httpx
import streamlit as st


API_URL = "http://localhost:8000"

def get_profile():
    """
    Fetches the current user profile from backend /profile (GET).
    Uses JWT access token stored in session_state.
    """
    token = st.session_state.get('access_token')
    if not token:
        st.error("Access token missing. Please login again.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = httpx.get(f"{API_URL}/profile/read", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        detail = e.response.json().get('detail') if e.response else "HTTP error"
        st.error(f"Error fetching profile: {detail}")
        return None
    except Exception:
        st.error("Unexpected error fetching profile")
        return None

def update_profile(age_group, language_preference):
    """
    Sends profile updates to backend /profile (PUT).
    """
    token = st.session_state.get('access_token')
    if not token:
        st.error("Access token missing. Please login again.")
        return False

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"age_group": str(age_group), "language_preference": language_preference}
    try:
        response = httpx.put(f"{API_URL}/profile/update", json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        detail = e.response.json().get('detail') if e.response else "HTTP error"
        st.error(f"Error updating profile: {detail}")
        return False
    except Exception:
        st.error("Unexpected error updating profile")
        return False

def profile_page():
    # Load profile once
    if "profile_loaded" not in st.session_state or not st.session_state.profile_loaded:
        profile = get_profile()
        if not profile:
            st.error("Could not load profile.")
            return
        try:
            age_value = int(profile.get("age_group", 18))
        except (ValueError, TypeError):
            age_value = 18
        st.session_state.age_group = age_value
        st.session_state.language_preference = profile.get("language_preference", "English")
        st.session_state.profile_loaded = True

    age_min = 18
    age_max = 65

    # Editable fields
    age_group = st.number_input(
        "Age",
        min_value=age_min,
        max_value=age_max,
        value=st.session_state.age_group,
        step=1
    )

    language_preference = st.radio(
    "Language Preference",
    options=["English", "Hindi"],
    index=0 if st.session_state.language_preference == "English" else 1,
    horizontal=True  # This makes it look cleaner than a dropdown
)

    st.write(f"Current Age: {age_group}")
    st.write(f"Current Language Preference: {language_preference}")

    # Save selections in session_state
    st.session_state.age_group = age_group
    st.session_state.language_preference = language_preference

    if st.button("Save Profile"):
        success = update_profile(age_group, language_preference)
        if success:
            st.success("Profile updated successfully!")
