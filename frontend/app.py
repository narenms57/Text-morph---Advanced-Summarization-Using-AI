import sys
import os

# Get the absolute path of the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
# Add parent directory to Python path
sys.path.append(parent_dir)
#project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
#print("Project root path to add:", project_root)
#sys.path.insert(0, project_root)

#print("Updated sys.path:", sys.path)
#print("Current working directory:", os.getcwd())
#print("Backend folder exists at project root:", os.path.isdir(os.path.join(project_root, 'backend')))

#the above three lines help find backend modules when running streamlit app

import streamlit as st
import httpx
import textstat
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
from io import StringIO
from backend.api.summarization import generate_summary, summarize_long_text
from backend.api.database import save_generated_text

 



import os
print("Current working directory:", os.getcwd())


# Your existing imports and API_URL
from forget_password import reset_password_simple
from auth import login, logout
from profile import get_profile, profile_page

API_URL = "http://localhost:8000"

def register_user(username, email, password, language_preference):
    url = f"{API_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password,
        "language_preference": language_preference
    }
    try:
        response = httpx.post(url, json=data, timeout=10)
        if response.status_code == 201:
            st.success("Registration successful! Please login now.")
        elif response.status_code == 409:
            error_detail = response.json().get("detail", "User already exists.")
            st.warning(f"{error_detail} Please login instead.")
        else:
            error_detail = response.json().get("detail", "Registration failed.")
            st.error(f"Error: {error_detail}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")

def show_register():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    language_preference = st.selectbox("Language Preference", ["English", "Hindi"])

    if st.button("Register"):
        if username and email and password:
            register_user(username, email, password, language_preference)
        else:
            st.error("Please fill in all fields.")

    if st.button("Already have an account? Login"):
        st.session_state.page = "login"
        st.rerun()

def login_user(email, password):
    url = f"{API_URL}/auth/login"
    data = {"email": email, "password": password}
    try:
        response = httpx.post(url, json=data, timeout=10)
        if response.status_code == 200:
            user_data = response.json().get("user")
            return True, user_data
        else:
            return False, None
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False, None


def show_login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, user_data = login_user(email, password)
        if success:
            st.session_state.user_id = user_data['id']
            st.session_state.email = user_data['email']
            st.success("Logged in successfully")
            st.session_state.page = "dashboard"
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid email or password")

    if st.button("Forgot Password?"):
        st.session_state.page = "reset_password"
        st.rerun()

    if st.button("Create a new account"):
        st.session_state.page = "register"
        st.rerun()

def sidebar_menu():
    st.sidebar.title("Menu")
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    #if st.sidebar.button("Home"):
        # Redirecting home to dashboard since home is not used
        #st.session_state.page = "dashboard"
       # st.rerun()
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
        st.rerun()
    if st.sidebar.button("Logout"):
        logout()
        st.session_state.page = "login"
        st.session_state.logged_in = False
        st.rerun()

def show_profile():
    st.title("Profile Management")
    profile = get_profile()
    # Add your profile UI updates here
user_id = st.session_state.get("user_id")
st.write(f"User ID: {user_id}")
def show_scores(flesch, fog, smog):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"<div style='text-align:center; color:green; font-size:36px; font-weight:bold;'>{flesch:.1f}</div>"
            f"<div style='text-align:center; font-size:18px;'>Flesch-Kincaid</div>", 
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            f"<div style='text-align:center; color:goldenrod; font-size:36px; font-weight:bold;'>{fog:.1f}</div>"
            f"<div style='text-align:center; font-size:18px;'>Gunning Fog</div>", 
            unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            f"<div style='text-align:center; color:red; font-size:36px; font-weight:bold;'>{smog:.1f}</div>"
            f"<div style='text-align:center; font-size:18px;'>SMOG Index</div>", 
            unsafe_allow_html=True
        )

def show_dashboard():
    st.title("Dashboard - Readability Checker")
    st.write("Upload a text file (.txt) to analyze readability.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt','png','jpg','jpeg'])

    if uploaded_file:
        text = ""
        if uploaded_file.type.startswith("text"):
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text = stringio.read()
        else:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)

        # Optionally show extracted text
        # st.subheader("Extracted Text")
        # st.write(text)

        #buttons for summarization and paraphrasing
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Summarize Text"):
                st.subheader("Summary")
                #summary = generate_summary(text)
                summary = "Summary functionality is currently disabled."
                st.write(summary)
        with col2:
            if st.button("Paraphrase Text"):
                st.subheader("Paraphrased Text")
                #paraphrased = paraphrase_text(text)
                paraphrased = "Paraphrasing functionality is currently disabled."
                st.write(paraphrased)

        # Calculate readability scores
        flesch = textstat.flesch_reading_ease(text)
        fog = textstat.gunning_fog(text)
        smog = textstat.smog_index(text)

        st.subheader("Readability Scores")
        show_scores(flesch, fog, smog)

        # Normalize scores for visualization:
        # Flesch is 0-100 (higher is easier)
        # Fog and Smog higher means harder, so invert and scale to 0-100
        def norm_flesch(score): 
            return max(0, min(score, 100))
        def norm_fog_smog(score):
            inv = 20 - score
            norm = max(0, min(inv, 20)) * 5
            return norm

        beginner_score = (norm_flesch(flesch) + norm_fog_smog(fog) + norm_fog_smog(smog)) / 3
        intermediate_score = 100 - abs(50 - beginner_score) * 2
        advanced_score = 100 - beginner_score

        # Clamp scores to 0-100 for display
        beginner_score = max(0, min(beginner_score, 100))
        intermediate_score = max(0, min(intermediate_score, 100))
        advanced_score = max(0, min(advanced_score, 100))

        labels = ['Beginner', 'Intermediate', 'Advanced']
        scores = [beginner_score, intermediate_score, advanced_score]
        colors = ['green', 'orange', 'red']

        fig, ax = plt.subplots()
        bars = ax.bar(labels, scores, color=colors)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score (%)")
        ax.set_title("Readability Level Distribution")

        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 2, f'{score:.1f}%', ha='center')

        st.pyplot(fig)

def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "reset_password":
            reset_password_simple()
        else:
            show_register()
    else:
        sidebar_menu()
        st.write(f"Logged in as {st.session_state.get('email', 'Unknown')}")
        if st.session_state.page == "dashboard" or st.session_state.page == "home":  
            show_dashboard()
        elif st.session_state.page == "profile":
            profile_page()

if __name__ == "__main__":
    main()
