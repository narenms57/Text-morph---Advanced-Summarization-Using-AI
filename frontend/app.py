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

# Fix path imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
backend_dir = os.path.join(parent_dir, "backend")
sys.path.append(backend_dir)

# Backend imports
from backend.api.paraphrasing import generate_paraphrase, paraphrase_long_text
from backend.api.summarization import generate_summary, summarize_long_text
from backend.api.database import save_generated_text
from forget_password import reset_password_with_otp
from auth import login as backend_login, logout
from profile import profile_page

API_URL = "http://localhost:8000"

st.markdown("""
<style>
    .stApp {
        background-color: #0A2239;
        color: #E0F7FA;
        font-family: 'Orbitron', sans-serif;
    }
    h1, h2, h3 {
        color: #E0F7FA;
        text-align: center;
    }
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #05668D !important;
        color: #E0F7FA !important;
        border-radius: 6px;
        padding: 6px !important;
    }
    .stButton>button {
        background-color: #028090 !important;
        color: #E0F7FA !important;
        border-radius: 6px;
        font-weight: bold;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #00A896 !important;
        transform: scale(1.05);
    }
    [data-testid="stSidebar"] {
        background-color: #05668D;
    }
    [data-testid="stSidebar"] * {
        color: #E0F7FA !important;
    }
    .stTextArea textarea {
        height: 200px !important;
    }
</style>
""", unsafe_allow_html=True)

#-------------- AUTH ------------
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
        elif response.status_code in [400, 409]:
            st.warning(f"{response.json().get('detail', 'User already exists.')}")
        else:
            st.error(f"Registration failed: {response.json().get('detail')}")
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


def show_login():
    st.title("SmartText Summarizer and Paraphraser")
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, user_data, token = backend_login(email, password)
        if success:
            st.session_state.user_id = user_data['id']
            st.session_state.username = user_data['username']
            st.session_state.email = user_data['email']
            st.session_state.access_token = token
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


# --------------------------- SIDEBAR ---------------------------
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


# --------------------------- DASHBOARD ---------------------------
def show_scores(flesch, fog, smog):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flesch-Kincaid", f"{flesch:.1f}")
    with col2:
        st.metric("Gunning Fog", f"{fog:.1f}")
    with col3:
        st.metric("SMOG Index", f"{smog:.1f}")


def compute_rouge_scores(reference_text, paraphrased_text):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference_text, paraphrased_text)
    return {k: v.fmeasure for k, v in scores.items()}


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

    # --- Summarize Tab
    with tab1:
        if st.button("Generate Summary"):
            try:
                summary = generate_summary(text) if len(text.split()) < 500 else summarize_long_text(text)
                st.session_state.summary = summary  # ✅ store in session
                st.text_area("Generated Summary", summary, height=200)

                st.download_button("Download Summary", summary, file_name="summary.txt")

                if "user_id" in st.session_state:
                    save_generated_text(st.session_state.user_id, summary, "summary")

            except Exception as e:
                st.error(f"Error summarizing text: {str(e)}")

        if st.session_state.get("summary") and st.button("Compare Summary with Input"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Input Text")
                st.text_area("Original Text", text, height=200, disabled=True)
            with col2:
                st.subheader("Summary")
                st.text_area("Summary", st.session_state.summary, height=200)

    # --- Paraphrase Tab
    with tab2:
        if st.button("Generate Paraphrase"):
            try:
                paraphrased = generate_paraphrase(text) if len(text.split()) <= 100 else paraphrase_long_text(text)
                st.session_state.paraphrased = paraphrased  # ✅ store in session
                st.text_area("Paraphrased Text", paraphrased, height=200)

                st.download_button("Download Paraphrase", paraphrased, file_name="paraphrase.txt")

                if "user_id" in st.session_state:
                    save_generated_text(st.session_state.user_id, paraphrased, "paraphrase")

            except Exception as e:
                st.error(f"Error while paraphrasing: {str(e)}")

        if st.session_state.get("paraphrased") and st.button("Compare Paraphrase with Input"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Input Text")
                st.text_area("Original Text", text, height=200, disabled=True)
            with col2:
                st.subheader("Paraphrased")
                st.text_area("Paraphrased", st.session_state.paraphrased, height=200)

        # ROUGE score visualization
        if st.session_state.get("paraphrased"):
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
            ax.set_title("ROUGE Visual Representation")
            st.pyplot(fig)

    # --- Readability Tab
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
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                        f'{score:.1f}%', ha='center')
            st.pyplot(fig)


# --------------------------- MAIN ---------------------------
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "reset_password":
            reset_password_with_otp()
        else:
            show_register()
    else:
        sidebar_menu()
        st.write(f"Logged in as {st.session_state.get('username', 'Unknown')}")
        if st.session_state.page in ["dashboard", "home"]:
            show_dashboard()
        elif st.session_state.page == "profile":
            profile_page()


# --------------------------- ENTRY POINT ---------------------------
if __name__ == "__main__":
    main()