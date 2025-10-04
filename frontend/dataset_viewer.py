import streamlit as st


def show_dataset_viewer(df):
    st.title("Dataset Viewer: Dataset 1")
    st.markdown("**Tasks:** Summarization & Paraphrasing")
    st.markdown("**Domains:** News (CNN), Science, Medical (PubMed), Paraphrase (PAWS, GPT Phrases)")

    total_rows = df.shape[0]
    st.write(f"Total samples: {total_rows}")

    page_size = 20
    max_page = (total_rows - 1) // page_size + 1
    page_num = st.number_input("Page number", min_value=1, max_value=max_page, value=1)

    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    subset = df.iloc[start_idx:end_idx]

    for i, row in subset.iterrows():
        st.markdown(f"### Sample {i+1} - Task: {row['task']} - Domain: {row['domain']}")
        with st.expander("Input Text"):
            st.write(row['input_text'])
        with st.expander("Target Text"):
            st.write(row['target_text'])

  
