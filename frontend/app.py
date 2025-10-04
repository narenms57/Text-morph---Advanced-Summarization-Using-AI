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
import nltk
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
from mysql.connector import Error
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from nltk.translate.meteor_score import meteor_score
from nltk.tokenize import word_tokenize
import nltk
import time
import pandas as pd
from transformers import MarianMTModel, MarianTokenizer

from dataset_viewer import show_dataset_viewer


#nltk.data.path.append("C:/Users/naren/AppData/Roaming/nltk_data")

#nltk.download('wordnet')
#nltk.download('punkt')
#nltk.download('punkt')


# Paths for backend imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
backend_dir = os.path.join(parent_dir, "backend")
sys.path.append(backend_dir)

from backend.api.summarization import generate_summary, summarize_long_text
from backend.api.para import generate_paraphrase, paraphrase_long_text
from backend.api.database import create_connection, save_generated_text,record_login, save_user_feedback, update_text_in_db, delete_text_in_db, fetch_all_users, fetch_user_texts_by_id,update_user_role,delete_user
from forget_password import reset_password_simple
from auth import login, logout
from profile import get_profile, profile_page

from transformers import BartForConditionalGeneration, BartTokenizer, PegasusForConditionalGeneration, PegasusTokenizer, T5ForConditionalGeneration, ByT5Tokenizer

from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from googletrans import Translator


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
import os
from pathlib import Path
from transformers import T5ForConditionalGeneration, ByT5Tokenizer
from pathlib import Path



MODEL_INFO = {
    "Pegasus-XSum": {
        "model_cls": PegasusForConditionalGeneration,
        "tokenizer_cls": PegasusTokenizer,
        "model_name": Path("C:/Users/naren/TextMorph/backend/models/google-pegasus-xsum-fine-tuned/exported")
    },
    "BART-Summary":{
        "model_cls": BartForConditionalGeneration,
        "tokenizer_cls": BartTokenizer,
        "model_name": Path("C:/Users/naren/TextMorph/backend/models/facebook-bart-summary")
    },
     "BART-Paraphrase":{
        "model_cls": BartForConditionalGeneration,
        "tokenizer_cls": BartTokenizer,
        "model_name": Path("C:/Users/naren/TextMorph/backend/models/facebook-bart-paraphrase")
    },

    
}


@st.cache_resource
def load_model_and_tokenizer(selected_model):
    info = MODEL_INFO[selected_model] 
    model_path = info["model_name"].as_posix()
    print("Loading model from:", model_path)
    print(f"Loading {selected_model} from: {model_path}")
    print(f"Model class: {info['model_cls']}")
    print(f"Tokenizer class: {info['tokenizer_cls']}")

    try:
        # Load tokenizer
        tokenizer = info["tokenizer_cls"].from_pretrained(
            pretrained_model_name_or_path=model_path, 
            local_files_only=True
        )
        
        # Load model with explicit generation config handling
        model = info["model_cls"].from_pretrained(
            pretrained_model_name_or_path=model_path, 
            local_files_only=True,
            # Force the model to use the generation_config.json from disk
            ignore_mismatched_sizes=True  # This might help with config issues
        )
        
        # Double-check and fix the generation config if needed
        if hasattr(model, 'generation_config') and model.generation_config is not None:
            print(f"Model generation config early_stopping: {getattr(model.generation_config, 'early_stopping', 'NOT_SET')}")
            if getattr(model.generation_config, 'early_stopping', None) is None:
                model.generation_config.early_stopping = True
                print("Fixed early_stopping in generation config")
        
        return tokenizer, model
        
    except Exception as e:
        print(f"Error loading model: {e}")
        # Try an alternative approach - load config separately
        try:
            from transformers import AutoConfig
            
            # Load config first
            config = AutoConfig.from_pretrained(model_path, local_files_only=True)
            
            # Load tokenizer
            tokenizer = info["tokenizer_cls"].from_pretrained(
                pretrained_model_name_or_path=model_path, 
                local_files_only=True
            )
            
            # Load model with the config
            model = info["model_cls"].from_pretrained(
                pretrained_model_name_or_path=model_path,
                config=config,
                local_files_only=True
            )
            
            return tokenizer, model
            
        except Exception as e2:
            print(f"Alternative loading also failed: {e2}")
            raise e
    #}
#translation 
@st.cache_resource
def get_translator():
    return Translator()

def google_translate(text, dest_language_code):
    translator = get_translator()
    translated = translator.translate(text, dest=dest_language_code)
    return translated.text

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


def show_feedback_ui(user_id, feedback_key):
    st.write("Was the output helpful?")

    # Maintain selected feedback in session state for persistence
    selected = st.session_state.get(f"{feedback_key}_selected", None)

    col1, col2 = st.columns(2)

    def on_select(value):
        st.session_state[f"{feedback_key}_selected"] = value

    with col1:
        if st.button("👍", key=f"{feedback_key}_like_btn", on_click=on_select, args=("like",)):
            pass
    with col2:
        if st.button("👎", key=f"{feedback_key}_dislike_btn", on_click=on_select, args=("dislike",)):
            pass

    # Highlight selected button with emoji or style
    if selected == "like":
        st.markdown("**👍 Selected**")
    elif selected == "dislike":
        st.markdown("**👎 Selected**")

    comment = st.text_area("Optional feedback comment", key=f"{feedback_key}_comment")

    if st.button("Submit Feedback", key=f"{feedback_key}_submit_btn"):
        if not selected:
            st.warning("Please select thumbs up or down before submitting feedback.")
        else:
            comment_text = comment or ""
            success = save_user_feedback(user_id, selected, comment_text)
            if success:
                st.success("Thanks for your feedback!")
                # Clear feedback states to reset UI
                st.rerun()
            else:
                st.error("Failed to save feedback.")



def show_dashboard():
    LANG_CODE_MAP = {
    "English": "en",
    "Tamil":"ta",
    "Hindi": "hi",

    "French": "fr",
    "German": "de",
    "Spanish": "es",
    
    # Add more as needed
}
    st.title("Dashboard - Smart Text Tools")
 
    input_method = st.radio("Select input method", ("Text Box", "Upload File"), key="global_input_method")
    input_text = ""
 
    if input_method == "Text Box":
        input_text = st.text_area("Enter your text here", height=200)
    else:
        uploaded_file = st.file_uploader("Choose a text file to upload", type=["txt"], key="global_file_upload")
        if uploaded_file:
            input_text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()

    if not input_text:
        st.info("Please input text through above options to proceed to summarization, paraphrasing, or readability.")
    else:
        st.markdown("### What would you like to do?")
        tab1, tab2, tab3 = st.tabs(["📄 Summarize", "🔄 Paraphrase", "📊 Readability"])

        if "selected_summary_model" not in st.session_state:
            st.session_state.selected_summary_model = "Pegasus-XSum"
        if "selected_paraphrase_model" not in st.session_state:
            st.session_state.selected_paraphrase_model = "Pegasus-XSum"

        summary_params = [
            {"max_length": 45, "min_length": 10, "length_penalty": 1.0, "num_beams": 3, "name": "short_summary.txt", },
            {"max_length": 70, "min_length": 40, "length_penalty": 1.5, "num_beams": 5, "name": "medium_summary.txt"},
            {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6,"name": "long_summary.txt"},
        ]

        paraphrase_options = {
            "Beginner": {"max_length": 60, "min_length": 20, "length_penalty": 0.8, "num_beams": 3},
            "Intermediate": {"max_length": 100, "min_length": 40, "length_penalty": 1.2, "num_beams": 4},
            "Advanced": {"max_length": 140, "min_length": 80, "length_penalty": 1.5, "num_beams": 6},
    }

    # Summarize Tab
        with tab1:
        # Always show model selector
            st.session_state.selected_summary_model = st.selectbox(
                "Choose Summarization Model",
                ["Pegasus-XSum", "BART-Summary"],
                index=["Pegasus-XSum", "BART-Summary"].index(st.session_state.selected_summary_model),
                key="summary_model"
            )  

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Generate Short Summary"):
                    if not input_text.strip():
                        st.warning("Please provide input text.")
                    else:
                        try:
                            tokenizer, model = load_model_and_tokenizer(st.session_state.selected_summary_model)
                            params = summary_params[0]
                            if len(input_text.split()) < 500:
                                summary = generate_summary(
                                    input_text, tokenizer, model,
                                    max_length=params["max_length"],
                                    min_length=params["min_length"],
                                    length_penalty=params["length_penalty"],
                                    num_beams=params["num_beams"],
                                    early_stopping=True,
                                )
                            else:
                                print(f"DEBUG: Calling summarize_long_text with params: {params}")
                                summary = summarize_long_text(input_text, tokenizer, model, summary_params=params)
                            st.session_state.summary = summary
                            st.success("Short summary generated!")
                        except Exception as e:
                            st.error(f"Error generating short summary: {e}")
                            import traceback
                            st.text(traceback.format_exc())

            with col2:
                if st.button("Generate Medium Summary"):
                    try:
                        tokenizer, model = load_model_and_tokenizer(st.session_state.selected_summary_model)
                        params = summary_params[1]
                        if len(input_text.split()) < 500:
                            summary = generate_summary(
                                input_text, tokenizer, model,
                                max_length=params["max_length"],
                                min_length=params["min_length"],
                                length_penalty=params["length_penalty"],
                                num_beams=params["num_beams"],
                                early_stopping=True,
                            )
                        else:
                            summary = summarize_long_text(input_text, tokenizer, model, summary_params=params)
                        st.session_state.summary = summary
                        st.success("Medium summary generated!")
                    except Exception as e:
                        st.error(f"Error generating medium summary: {e}")

            with col3:
                if st.button("Generate Long Summary"):
                    try:
                        tokenizer, model = load_model_and_tokenizer(st.session_state.selected_summary_model)
                        params = summary_params[2]
                        if len(input_text.split()) < 500:
                            summary = generate_summary(
                                input_text, tokenizer, model,
                                max_length=params["max_length"],
                                min_length=params["min_length"],
                                length_penalty=params["length_penalty"],
                                num_beams=params["num_beams"],
                                early_stopping=True,
                            )
                        else:
                            summary = summarize_long_text(input_text, tokenizer, model, summary_params=params)
                        st.session_state.summary = summary
                        st.success("Long summary generated!")
                    except Exception as e:
                        st.error(f"Error generating long summary: {e}")

            if st.session_state.get("summary"):
                
                max_chars = 1000
                display_input = input_text if len(input_text) <= max_chars else input_text[:max_chars] + "..."
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Input Text")
                    st.text_area("Original Text", display_input, height=200, disabled=True, key="summary_input_text")
                with col2:
                    st.subheader("Summary")
                    st.text_area("Generated Summary", st.session_state.summary, height=200, key="summary_generated_text")
                st.download_button("Download Summary", st.session_state.summary, file_name="summary.txt")

                if "user_id" in st.session_state:
                    save_generated_text(st.session_state.user_id, st.session_state.summary, "summary",input_text=input_text, model_used=st.session_state.selected_summary_model)
                    show_feedback_ui(st.session_state["user_id"], "summary")
                lang_list = list(LANG_CODE_MAP.keys())
                selected_lang = st.selectbox("Translate output to:", lang_list, key="trans_google_summary")
                if st.button("Translate with Google", key="btn_google_summary"):
   
                    text_to_translate = st.session_state.get("summary") 
                    if text_to_translate:
                        translated = google_translate(text_to_translate, LANG_CODE_MAP[selected_lang])
                        st.text_area("Google Translated Output", translated, height=200)


        # Paraphrase Tab
        with tab2:
            # Always show model selector
            st.session_state.selected_paraphrase_model = st.selectbox(
                "Choose Paraphrasing Model",
                ["Pegasus-XSum", "BART-Paraphrase"],
                index=["Pegasus-XSum", "BART-Paraphrase"].index(st.session_state.selected_paraphrase_model),
                key="paraphrase_model"
            )
            

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Paraphrase Beginner", key="btn_beginner"):
                    try:
                        tokenizer, model = load_model_and_tokenizer(st.session_state.selected_paraphrase_model)
                        params = paraphrase_options["Beginner"]
                        if len(input_text.split()) <= 100:
                            paraphrased = generate_paraphrase(input_text, tokenizer, model, **params)
                        else:
                            paraphrased = paraphrase_long_text(input_text, tokenizer, model, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.success("Paraphrasing (Beginner) completed!")
                    except Exception as e:
                        st.error(f"Error during Beginner paraphrase: {e}")

            with col2:
                if st.button("Paraphrase Intermediate", key="btn_intermediate"):
                    try:
                        tokenizer, model = load_model_and_tokenizer(st.session_state.selected_paraphrase_model)
                        params = paraphrase_options["Intermediate"]
                        if len(input_text.split()) <= 100:
                            paraphrased = generate_paraphrase(input_text, tokenizer, model, **params)
                        else:
                            paraphrased = paraphrase_long_text(input_text, tokenizer, model, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.success("Paraphrasing (Intermediate) completed!")
                    except Exception as e:
                        st.error(f"Error during Intermediate paraphrase: {e}")

            with col3:
                if st.button("Paraphrase Advanced", key="btn_advanced"):
                    try:
                        tokenizer, model = load_model_and_tokenizer(st.session_state.selected_paraphrase_model)
                        params = paraphrase_options["Advanced"]
                        if len(input_text.split()) <= 100:
                            paraphrased = generate_paraphrase(input_text, tokenizer, model, **params)
                        else:
                            paraphrased = paraphrase_long_text(input_text, tokenizer, model, paraphrase_params=params)
                        st.session_state.paraphrased = paraphrased
                        st.success("Paraphrasing (Advanced) completed!")
                    except Exception as e:
                        st.error(f"Error during Advanced paraphrase: {e}")

            if st.session_state.get("paraphrased"):
               
                
                max_chars = 1000
                display_input = input_text if len(input_text) <= max_chars else input_text[:max_chars] + "..."
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Input Text")
                    st.text_area("Original Text", display_input, height=200, disabled=True, key="paraphrase_input_text")
                with col2:
                    st.subheader("Paraphrased Text")
                    st.text_area("Paraphrased Text", st.session_state.paraphrased, height=200, key="paraphrased_text")
                lang_list = list(LANG_CODE_MAP.keys())
                selected_lang = st.selectbox("Translate output to:", lang_list, key="trans_google_paraphrase")
                if st.button("Translate with Google", key="btn_google_paraphrase"):
                    # This works for both summary and paraphrased
                    text_to_translate = st.session_state.get("paraphrased") 
                    if text_to_translate:
                        translated = google_translate(text_to_translate, LANG_CODE_MAP[selected_lang])
                        st.text_area("Google Translated Output", translated, height=200)

                st.download_button("Download Paraphrase", st.session_state.paraphrased, file_name="paraphrase.txt")

                # ROUGE score visualization for paraphrase only
                scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
                rouge_scores = scorer.score(input_text, st.session_state.paraphrased)
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
                    saved = save_generated_text(st.session_state.user_id, st.session_state.paraphrased, "paraphrase", input_text=input_text, model_used=st.session_state.selected_paraphrase_model)
                    show_feedback_ui(st.session_state["user_id"], "paraphrase")
                    if saved:
                        st.success("Paraphrased text saved to database.")
                    else:
                        st.warning("Failed to save paraphrased text to database.")

        

        # Readability Tab
        with tab3:
            if st.button("Analyze Readability"):
                flesch = textstat.flesch_reading_ease(input_text)
                fog = textstat.gunning_fog(input_text)
                smog = textstat.smog_index(input_text)
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
            time.sleep(2)
            st.session_state.page = "login"
            st.rerun()
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
            st.session_state.role = user_data['role']
            st.session_state.logged_in = True
            record_login(user_data['id'])
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
def fetch_user_texts(user_id):
    connection = create_connection()
    results = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT input_text, content_text, content_type, model_used, created_at FROM user_texts WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            results = cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            cursor.close()
            connection.close()
    return results


#refernce_text model flan-t5
@st.cache_resource
def load_flant5():
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
    return tokenizer, model

def flant5_generate(task_type, input_str):
    tokenizer, model = load_flant5()
    if task_type == "summary":
        prompt = f"Summarize: {input_str}"
    else:
        prompt = f"Paraphrase this academically: {input_str}"
    tokens = tokenizer(prompt, return_tensors="pt")
    output_ids = model.generate(**tokens, max_new_tokens=128, num_beams=4, early_stopping=True,repetition_penalty=1.5,temperature=1.0)
    return tokenizer.decode(output_ids[0], skip_special_tokens=True)

from bert_score import score
@st.cache_data
def get_dataset_entries():
    import pandas as pd

    try:
        df = pd.read_csv("C:\\Users\\naren\\TextMorph\\dataset\\cleaned_4k.csv")  # Update path if needed
        return df[["input_text", "target_text"]].dropna().to_dict(orient="records")
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return []




def show_evaluation():
    st.title("Model Evaluation & Comparison")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please login to view evaluation and history.")
        return

    records = fetch_user_texts(user_id)
    if not records:
        st.write("No history available.")
        return

    selected_index = st.selectbox(
        "Select past generated record to view and compare",
        range(len(records)),
        format_func=lambda i: f"{records[i]['created_at']} - {records[i]['content_type']} - {records[i]['model_used']}"
    )

    record = records[selected_index]

    tab1, tab2 = st.tabs(["Comparison & Metrics", "History"])

    with tab1:
        current_input = st.text_area("Input Text", record['input_text'] or "")
        generated_text = st.text_area("Generated Text", record['content_text'] or "")
        ref_placeholder = st.empty()

        if st.button("Compare and Evaluate"):

            # Load dataset entries
            dataset_entries = get_dataset_entries()  # You must define this function to return list of dicts with 'input_text' and 'target_text'
            matched_entry = next((entry for entry in dataset_entries if entry['input_text'].strip() == current_input.strip()), None)

            if not matched_entry:
                st.error("⚠️ The input text does not match any known dataset entry. Metrics cannot be computed for external inputs.")
                return

            reference_text = matched_entry['target_text']
            ref_placeholder.text_area("Reference Text (Target from Dataset)", reference_text, height=150)

            # Metrics calculation
            rouge_scorer_obj = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            rouge_scores = rouge_scorer_obj.score(reference_text, generated_text)

            ref_tokens = [reference_text.split()]
            gen_tokens = generated_text.split()
            smoothing = nltk.translate.bleu_score.SmoothingFunction().method1
            bleu = sentence_bleu(ref_tokens, gen_tokens, smoothing_function=smoothing)

            P, R, F1 = score([generated_text], [reference_text], lang="en", verbose=False)
            bert_ref = F1[0].item()

            from sentence_transformers import SentenceTransformer
            model_st = SentenceTransformer('all-MiniLM-L6-v2')
            emb_input = model_st.encode([current_input], convert_to_tensor=True)
            emb_gen = model_st.encode([generated_text], convert_to_tensor=True)
            cosine_sim_val = cosine_similarity(emb_input.cpu().numpy(), emb_gen.cpu().numpy())[0][0]

            # Stylish Evaluation Card
            st.markdown("""<style> .eval-card {background: #181e36; padding: 1.5em 2em; border-radius: 15px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6); margin-bottom: 1em;} .eval-header {color: #26b5ff; font-size: 1.9rem; margin-bottom: 1rem;} .eval-label {color: #9ab9e7; font-weight:600; margin-bottom:0.3rem;} .eval-metric {color:#e1faff; font-size:1.7rem; font-weight:bold; margin-bottom:0.6rem;} .text-area-dark textarea {background-color: #14213d !important; color: #e0e0e0 !important; border-radius: 8px; padding: 5px;} </style>""", unsafe_allow_html=True)
            st.markdown('''<div class="eval-card" style="display: flex; justify-content: center; align-items: center; height: 100px;"><div class="eval-header" style="text-align: center;">Model Evaluation Summary</div></div>''', unsafe_allow_html=True)

            cols = st.columns(3)
            with cols[0]:
                st.markdown('<div class="eval-label mb-0">Input Text</div>', unsafe_allow_html=True)
                st.text_area("", current_input, height=120, key="inp_text")
            with cols[1]:
                st.markdown('<div class="eval-label mb-0">Generated Text</div>', unsafe_allow_html=True)
                st.text_area("", generated_text, height=120, key="gen_text")
            with cols[2]:
                st.markdown('<div class="eval-label mb-0">Reference Text (Target)</div>', unsafe_allow_html=True)
                st.text_area("", reference_text, height=120, key="ref_text")

            metrics = {
                "BLEU": bleu,
                "ROUGE-1": rouge_scores['rouge1'].fmeasure,
                "ROUGE-2": rouge_scores['rouge2'].fmeasure,
                "ROUGE-L": rouge_scores['rougeL'].fmeasure,
                "BERTScore": bert_ref,
                "CosineSim": cosine_sim_val
            }
            display_metrics = ["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BERTScore", "CosineSim"]
            cols = st.columns(len(display_metrics))
            for i, metric_name in enumerate(display_metrics):
                with cols[i]:
                    st.markdown(f'<div class="eval-label">{metric_name}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="eval-metric">{metrics[metric_name]:.3f}</div>', unsafe_allow_html=True)

            radar_fig = go.Figure()
            radar_fig.add_trace(go.Scatterpolar(
                r=[metrics[x] for x in ["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L"]],
                theta=["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L"],
                fill='toself',
                line=dict(color='#26b5ff', width=3),
                marker=dict(size=8)
            ))
            radar_fig.update_layout(
                polar=dict(
                    bgcolor='#16223e',
                    radialaxis=dict(visible=True, range=[0, 1], gridcolor='#2b3b70'),
                    angularaxis=dict(tickfont=dict(color="#9ab9e7"))
                ),
                showlegend=False,
                paper_bgcolor='#14234a',
                height=350,
                margin=dict(t=40, b=30)
            )
            st.plotly_chart(radar_fig, use_container_width=True)

            fig2, ax = plt.subplots(facecolor="#1a2243")
            ax.bar(['ROUGE-1', 'ROUGE-2', 'ROUGE-L'], [metrics["ROUGE-1"], metrics["ROUGE-2"], metrics["ROUGE-L"]],
                   color='#26b5ff', edgecolor='#195a8b', linewidth=1.7)
            ax.set_ylim(0, 1)
            ax.set_title("Detailed ROUGE Metrics", color="#8fb8e4", fontsize=16)
            ax.tick_params(colors="#9ab9e7")
            for i, v in enumerate([metrics["ROUGE-1"], metrics["ROUGE-2"], metrics["ROUGE-L"]]):
                ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontweight='bold', color="#c6e2ff")
            st.pyplot(fig2)

    with tab2:
        st.header("History")
        for i, row in enumerate(records, 1):
            st.markdown(f"### Record {i}")
            st.write(f"**Input:** {row['input_text']}")
            st.write(f"**Output:** {row['content_text']}")
            st.write(f"**Type:** {row['content_type']}")
            st.write(f"**Model:** {row['model_used']}")
            st.write(f"**Created at:** {row['created_at']}")
            st.markdown("---")


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

#admin dashboard
def show_admin_dashboard():
    if st.session_state.get("role") != "admin":
        st.warning("Access denied. Admins only.")
        return

    st.title("Admin Dashboard")

    tab1, tab2, tab3,tab4= st.tabs(["Content Curation", "User Feedback", "Analytics","User Management"])

    # ---- Tab 1: User Texts ----
    with tab1:
        st.header("User Generated Texts")
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT ut.id, ut.input_text, ut.content_text, ut.content_type, ut.model_used, ut.created_at, u.username 
                FROM user_texts ut 
                JOIN users u ON ut.user_id = u.id
                ORDER BY ut.created_at DESC
            """)
            records = cursor.fetchall()
            cursor.close()
            connection.close()

            for r in records:
                st.markdown(f"#### Record ID: {r['id']} — User: {r['username']}")
                st.write(f"**Input Text:** {r['input_text']}")
                st.write(f"**Output Text:** {r['content_text']}")
                st.write(f"**Type:** {r['content_type']} | Model: {r['model_used']} | Created At: {r['created_at']}")
                cols = st.columns([3,1,1])
                with cols[0]:
                    new_content = st.text_area(f"Edit Content #{r['id']}", value=r['content_text'], key=f"edit_{r['id']}")
                with cols[1]:
                    if st.button(f"Update #{r['id']}", key=f"update_{r['id']}"):
                        # Update DB logic here
                        update_text_in_db(r['id'], new_content)
                        st.success(f"Record {r['id']} updated.")
                        st.rerun()
                with cols[2]:
                    if st.button(f"Delete #{r['id']}", key=f"delete_{r['id']}"):
                        delete_text_in_db(r['id'])
                        st.warning(f"Record {r['id']} deleted.")
                        st.rerun()
        else:
            st.error("Database connection failed.")

    # ---- Tab 2: User Feedback ----
    with tab2:
        # Filter option
        filter_option = st.selectbox("Filter feedback by:", ["Most Recent", "Liked", "Disliked"])

        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Base query to fetch feedback with username
            base_query = """
                SELECT uf.id, uf.feedback_type, uf.comment, uf.created_at, u.username
                FROM user_feedback uf
                JOIN users u ON uf.user_id = u.id
            """

            # Add filter conditions to query
            if filter_option == "Most Recent":
                query = base_query + " ORDER BY uf.created_at DESC"
                params = ()
            elif filter_option == "Liked":
                query = base_query + " WHERE uf.feedback_type = %s ORDER BY uf.created_at DESC"
                params = ("like",)
            elif filter_option == "Disliked":
                query = base_query + " WHERE uf.feedback_type = %s ORDER BY uf.created_at DESC"
                params = ("dislike",)
            else:
                query = base_query + " ORDER BY uf.created_at DESC"
                params = ()

            cursor.execute(query, params)
            feedbacks = cursor.fetchall()
            cursor.close()
            connection.close()

            if feedbacks:
                for fb in feedbacks:
                    st.markdown(f"**User:** {fb['username']} &nbsp;&nbsp;|&nbsp;&nbsp; **Feedback:** {fb['feedback_type'].capitalize()} &nbsp;&nbsp;|&nbsp;&nbsp; **Time:** {fb['created_at']}")
                    if fb['comment']:
                        st.markdown(f"> {fb['comment']}")
                    st.markdown("---")
            else:
                st.info("No feedback found for selected filter.")
        else:
            st.error("Database connection failed.")

    # ---- Tab 3: Analytics ----
       
    with tab3:

        st.header("Analytics Overview")
        connection = create_connection()
        if connection:
            cursor = connection.cursor()

            # Total unique users logged in
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM login_history")
            total_users = cursor.fetchone()[0]

            # Total generated texts (summaries + paraphrases)
            cursor.execute("SELECT COUNT(*) FROM user_texts")
            total_texts = cursor.fetchone()[0]

            # Model usage counts
            cursor.execute("""
                SELECT model_used, COUNT(*) as usage_count
                FROM user_texts
                WHERE model_used NOT REGEXP '^[0-9]+$'
                GROUP BY model_used
                ORDER BY usage_count DESC
            """)
            model_usage = cursor.fetchall()

            # Recent logins (last 10)
            cursor.execute("""
                SELECT u.username, lh.login_time FROM login_history lh
                JOIN users u ON lh.user_id = u.id
                ORDER BY lh.login_time DESC
                LIMIT 10
            """)
            recent_logins = cursor.fetchall()

            # Average ratings: likes & dislikes
            cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE feedback_type = 'like'")
            total_likes = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE feedback_type = 'dislike'")
            total_dislikes = cursor.fetchone()[0] or 0
            total_feedback = total_likes + total_dislikes
            if total_feedback > 0:
                like_percentage = (total_likes / total_feedback) * 100
                dislike_percentage = (total_dislikes / total_feedback) * 100
            else:
                like_percentage = dislike_percentage = 0

            cursor.close()
            connection.close()

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Unique Users Logged In", total_users)
            col2.metric("Total Generated Texts", total_texts)
            top_model = model_usage[0][0] if model_usage else "N/A"
            col3.markdown(f"### Top Used Model\n**{top_model}**")

            # Model usage bar chart
            if model_usage:
                models = [row[0] for row in model_usage]
                counts = [row[1] for row in model_usage]
                fig = go.Figure([go.Bar(x=models, y=counts, marker_color='rgb(26, 118, 255)')])
                fig.update_layout(title="Model Usage Counts", xaxis_title="Model", yaxis_title="Usage Count", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No model usage data available.")

            # Average user ratings: likes/dislikes
            st.subheader("User Feedback Summary")
            rc1, rc2 = st.columns(2)
            rc1.metric("Likes", f"{total_likes} ({like_percentage:.1f}%)")
            rc2.metric("Dislikes", f"{total_dislikes} ({dislike_percentage:.1f}%)")

            # Recent login cards
            st.subheader("Recent Logins")
            if recent_logins:
                for rl in recent_logins:
                    username = rl[0] if isinstance(rl, tuple) else rl['username']
                    login_time = rl[1] if isinstance(rl, tuple) else rl['login_time']
                    st.markdown(f"**{username}** logged in at {login_time}")
            else:
                st.info("No recent logins found.")
        else:
            st.error("Failed to connect to database.")
    
    with tab4:  # Add a 4th tab "User Management" or add this in Content Curation
        st.header("User Management")
        users = fetch_all_users()
        for user in users:
            st.markdown(f"**{user['username']}** | Role: {user['role']} | ID: {user['id']}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("Promote to Admin", key=f"admin_tab_promote_{user['id']}"):

                    update_user_role(user['id'], "admin")
                    st.success(f"{user['username']} promoted!")
                    st.rerun()
            with col2:
                if st.button("Demote to User", key=f"admin_tab_demote_{user['id']}"):
                    update_user_role(user['id'], "user")
                    st.success(f"{user['username']} demoted!")
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"admin_tab_delete_{user['id']}"):
                    delete_user(user['id'])
                    st.warning(f"{user['username']} deleted!")
                    st.rerun()
            with col4:
                if st.button("Review Records", key=f"admin_tab_review_{user['id']}"):
                    texts = fetch_user_texts_by_id(user['id'])
                    st.write(f"**Records for {user['username']}:**")
                    for t in texts:
                        st.write(f"{t['content_type']} ({t['model_used']}) at {t['created_at']}:")
                        st.code(f"Input: {t['input_text']}")
                        st.code(f"Output: {t['content_text']}")

            st.markdown("---")


def sidebar_menu():
    st.sidebar.title("Menu")
    username = st.session_state.get("username", "Unknown")
    st.sidebar.markdown(f"**Logged in as:** {username}")
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    if st.sidebar.button("Evaluation"):
        st.session_state.page = "evaluation"
        st.rerun()
    if st.sidebar.button("Dataset Viewer"):
        st.session_state.page = "dataset_viewer"
        st.rerun()
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
        st.rerun()
    if st.session_state.get("role") == "admin":
        if st.sidebar.button("Admin Dashboard"): 
            st.session_state.page = "admin_dashboard"
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
        #st.write(f"Logged in as {st.session_state.get('username', 'Unknown')}")
        if st.session_state.page in ["dashboard", "home"]:
            show_dashboard()
        elif st.session_state.page == "profile":
            profile_page()
        elif st.session_state.page == "evaluation":
            show_evaluation()
        elif st.session_state.page == "dataset_viewer":
            
                
            dataset_path = "C:\\Users\\naren\\TextMorph\\dataset\\cleaned_4k.csv"
            df = pd.read_csv(dataset_path) 
            show_dataset_viewer(df)
        elif st.session_state.page =="admin_dashboard":
            show_admin_dashboard()
 


if __name__ == "__main__":
    main()

