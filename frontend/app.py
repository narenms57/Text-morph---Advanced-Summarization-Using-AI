import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
backend_dir = os.path.join(parent_dir, "backend")
sys.path.append(backend_dir)

import sys
import os
from io import StringIO
import streamlit as st
import httpx
import textstat
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
from rouge_score import rouge_scorer
import fitz  # PyMuPDF


# Paths for backend imports
from backend.api.summarization import generate_summary, summarize_long_text
from backend.api.para import generate_paraphrase, paraphrase_long_text

from backend.api.database import save_generated_text
from forget_password import reset_password_simple
from auth import login, logout
from profile import get_profile, profile_page

API_URL = "http://localhost:8000"

st.markdown("""
<style>
/* Include teammate's CSS styles here */
.stApp {
    background-color: #0A2239;
    color: #E0F7FA;
    font-family: 'Orbitron', sans-serif;
}
/* ... rest of teammate CSS ... */
</style>
""", unsafe_allow_html=True)


def sidebar_menu():
    st.sidebar.title("Menu")
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
        st.rerun()
    if st.sidebar.button("Logout"):
        logout()
        st.session_state.page = "login"
        st.session_state.logged_in = False
        st.rerun()


def show_scores(flesch, fog, smog):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flesch-Kincaid", f"{flesch:.1f}")
    with col2:
        st.metric("Gunning Fog", f"{fog:.1f}")
    with col3:
        st.metric("SMOG Index", f"{smog:.1f}")


def show_dashboard():
    st.title("Dashboard - Smart Text Tools")
    st.write("Upload a text file (.txt) or image to summarize, paraphrase, or check readability.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'png', 'jpg', 'jpeg'])
    if not uploaded_file:
        return

    text = ""
    if uploaded_file.type.startswith("text"):
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        text = stringio.read()
    else:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    st.markdown("### What would you like to do?")
    tab1, tab2, tab3 = st.tabs(["📄 Summarize", "🔄 Paraphrase", "📊 Readability"])

    summary_params = [
        {"max_length": 45, "min_length": 10, "length_penalty": 1.0, "num_beams": 3, "name": "short_summary.txt"},
        {"max_length": 70, "min_length": 40, "length_penalty": 1.5, "num_beams": 5, "name": "medium_summary.txt"},
        {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6, "name": "long_summary.txt"},
    ]

    paraphrase_options = {
        "Beginner": {"max_length": 60, "min_length": 20, "length_penalty": 0.8, "num_beams": 3},
        "Intermediate": {"max_length": 100, "min_length": 40, "length_penalty": 1.2, "num_beams": 4},
        "Advanced": {"max_length": 140, "min_length": 80, "length_penalty": 1.5, "num_beams": 6},
    }

    # Summarize Tab
    with tab1:
        if st.button("Generate Summary"):
            st.session_state.show_summary_options = True

        if st.session_state.get("show_summary_options"):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Short Summary"):
                    try:
                        params = summary_params[0]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        st.success("Short summary generated!")
                    except Exception as e:
                        st.error(f"Error generating short summary: {str(e)}")

            with col2:
                if st.button("Medium Summary"):
                    try:
                        params = summary_params[1]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        st.success("Medium summary generated!")
                    except Exception as e:
                        st.error(f"Error generating medium summary: {str(e)}")

            with col3:
                if st.button("Long Summary"):
                    try:
                        params = summary_params[2]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        st.success("Long summary generated!")
                    except Exception as e:
                        st.error(f"Error generating long summary: {str(e)}")

        if st.session_state.get("summary"):
            # Side by side display original and summary with truncation
            max_chars = 1000
            display_input = text if len(text) <= max_chars else text[:max_chars] + "..."

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Input Text")
                st.text_area("Original Text", display_input, height=200, disabled=True, key="summary_input_text")
            with col2:
                st.subheader("Summary")
                st.text_area("Generated Summary", st.session_state.summary, height=200, key="summary_generated_text")

            st.download_button("Download Summary", st.session_state.summary, file_name="summary.txt")

            if "user_id" in st.session_state:
                save_generated_text(st.session_state.user_id, st.session_state.summary, "summary")

    # Paraphrase Tab
    with tab2:
        if st.button("Generate Paraphrase"):
            st.session_state.show_paraphrase_options = True
            st.session_state.paraphrased = None  # reset previous paraphrased

        if st.session_state.get("show_paraphrase_options"):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Beginner", key="btn_beginner"):
                    params = paraphrase_options["Beginner"]
                    try:
                        if len(text.split()) <= 100:
                            paraphrased = generate_paraphrase(text, **params)
                        else:
                            paraphrased = paraphrase_long_text(text, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.session_state.show_paraphrase_options = False
                        st.success("Paraphrasing (Beginner) completed!")
                    except Exception as e:
                        st.error(f"Error during Beginner paraphrase: {e}")

            with col2:
                if st.button("Intermediate", key="btn_intermediate"):
                    params = paraphrase_options["Intermediate"]
                    try:
                        if len(text.split()) <= 100:
                            paraphrased = generate_paraphrase(text, **params)
                        else:
                            paraphrased = paraphrase_long_text(text, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.session_state.show_paraphrase_options = False
                        st.success("Paraphrasing (Intermediate) completed!")
                    except Exception as e:
                        st.error(f"Error during Intermediate paraphrase: {e}")

            with col3:
                if st.button("Advanced", key="btn_advanced"):
                    params = paraphrase_options["Advanced"]
                    try:
                        if len(text.split()) <= 100:
                            paraphrased = generate_paraphrase(text, **params)
                        else:
                            paraphrased = paraphrase_long_text(text, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.session_state.show_paraphrase_options = False
                        st.success("Paraphrasing (Advanced) completed!")
                    except Exception as e:
                        st.error(f"Error during Advanced paraphrase: {e}")

        if st.session_state.get("paraphrased"):
            max_chars = 1000
            display_input = text if len(text) <= max_chars else text[:max_chars] + "..."

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Input Text")
                st.text_area("Original Text", display_input, height=200, disabled=True, key="paraphrase_input_text")
            with col2:
                st.subheader("Paraphrased Text")
                st.text_area("Paraphrased Text", st.session_state.paraphrased, height=200, key="paraphrased_text")

            st.download_button("Download Paraphrase", st.session_state.paraphrased, file_name="paraphrase.txt")

            # ROUGE score visualization for paraphrase only
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            rouge_scores = scorer.score(text, st.session_state.paraphrased)
            rouge_values = [
                rouge_scores['rouge1'].fmeasure,
                rouge_scores['rouge2'].fmeasure,
                rouge_scores['rougeL'].fmeasure
            ]
            labels = ['ROUGE-1', 'ROUGE-2', 'ROUGE-L']
            colors = ['blue', 'orange', 'green']
            fig, ax = plt.subplots()
            ax.bar(labels, rouge_values, color=colors)
            ax.set_ylim(0, 1)
            ax.set_ylabel("ROUGE Score")
            ax.set_title("ROUGE Visual Representation - Paraphrase")
            st.pyplot(fig)

            if "user_id" in st.session_state:
                saved = save_generated_text(st.session_state.user_id, st.session_state.paraphrased, "paraphrase")
                if saved:
                    st.success("Paraphrased text saved to database.")
                else:
                    st.warning("Failed to save paraphrased text to database.")

    # Readability Tab
    with tab3:
        if st.button("Analyze Readability"):
            flesch = textstat.flesch_reading_ease(text)
            fog = textstat.gunning_fog(text)
            smog = textstat.smog_index(text)
            st.subheader("Readability Scores")
            show_scores(flesch, fog, smog)

            def norm_flesch(score): return max(0, min(score, 100))
            def norm_fog_smog(score): return max(0, min((20 - score) * 5, 100))

            beginner_score = (norm_flesch(flesch) + norm_fog_smog(fog) + norm_fog_smog(smog)) / 3
            intermediate_score = 100 - abs(50 - beginner_score) * 2
            advanced_score = 100 - beginner_score

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
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f'{score:.1f}%', ha='center')

            st.pyplot(fig)
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




def show_login():
    st.title("SmartText Summarizer and Paraphraser")
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, user_data = login(email, password)
        if success:
            st.session_state.user_id = user_data['id']
            st.session_state.username = user_data['username']
            st.session_state.email = user_data['email']
            st.session_state.logged_in = True
            st.success(f"Logged in successfully as {user_data['username']}")
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid email or password")
    if st.button("Forgot Password?"):
        st.session_state.page = "reset_password"
        st.rerun()
    if st.button("Create a new account"):
        st.session_state.page = "register"
        st.rerun()

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

def sidebar_menu():
    st.sidebar.title("Menu")
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
        st.rerun()
    if st.sidebar.button("Logout"):
        logout()
        st.session_state.page = "login"
        st.session_state.logged_in = False
        st.rerun()

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
        elif st.session_state.page == "register":
            show_register()
        else:
            show_register()
    else:
        sidebar_menu()
        st.write(f"Logged in as {st.session_state.get('username', 'Unknown')}")
        if st.session_state.page in ["dashboard", "home"]:
            show_dashboard()
        elif st.session_state.page == "profile":
            profile_page()

if __name__ == "__main__":
    main()
