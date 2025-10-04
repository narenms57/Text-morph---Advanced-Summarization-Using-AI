import os
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from concurrent.futures import ThreadPoolExecutor
#from rouge_score import rouge_scorer


# Set path to save inputs and outputs
print(os.getcwd())
SAVE_PATH = "summarization_samples"
os.makedirs(SAVE_PATH, exist_ok=True)


# Load tokenizer and model (Pegasus Large)
#model_name = "google/pegasus-large"
#tokenizer = PegasusTokenizer.from_pretrained(model_name)
#model = PegasusForConditionalGeneration.from_pretrained(model_name)


def chunk_text_tokenwise(text, tokenizer,max_chunk_tokens=512):
    tokens = tokenizer.tokenize(text)
    chunks = []
    for i in range(0, len(tokens), max_chunk_tokens):
        chunk_tokens = tokens[i:i+max_chunk_tokens]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


def generate_summary(text, tokenizer,model,max_length=40, min_length=10, length_penalty=1.0, num_beams=3,early_stopping=True,temperature=None,no_repeat_ngram_size=None,repetition_penalty=None):
    print(f"DEBUG: early_stopping parameter value: {early_stopping}")
    print(f"DEBUG: early_stopping type: {type(early_stopping)}")
    text_str = str(text)
    if "Pegasus" in model.config._name_or_path:
        prompted_text= f"Summarize the following text clearly and concisely without adding any external information: {text_str}"
    else:
        prompted_text = text_str
    inputs = tokenizer([prompted_text], truncation=True, padding='longest', return_tensors="pt")
    bad_words = [
        "series", "part", "conclusion","article", "copyright", "postmedia", 
        "http", "www", ".com", "email", "share", "click",
        "including", "such as"  # Add these to prevent list generation
    ]
    bad_word_ids = [tokenizer.encode(word, add_special_tokens=False) for word in bad_words]
    if early_stopping is None:
        early_stopping = True
        print("WARNING: early_stopping was None, setting to True")
    summary_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=min_length,
        length_penalty=length_penalty,
        num_beams=num_beams,
        #no_repeat_ngram_size=2,
        early_stopping=early_stopping,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,
        bad_words_ids=bad_word_ids,
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    unwanted_prefixes = ["conclusion:", "conclusion", "summary:", "summary", "in conclusion"]
    for prefix in unwanted_prefixes:
        if summary.lower().startswith(prefix):
            summary = summary[len(prefix):].strip()
            # Remove any leading colon or punctuation
            if summary.startswith((":", "-")):
                summary = summary[1:].strip()
    return summary


def summarize_chunk(chunk, params, tokenizer,model):
    return generate_summary(
        chunk,
        tokenizer,
        model,
        max_length=params["max_length"],
        min_length=params["min_length"],
        length_penalty=params["length_penalty"],
        num_beams=params["num_beams"],
        early_stopping=True
    )


def summarize_long_text(text,tokenizer,model, chunk_token_limit=512, summary_params=None):
    if summary_params is None:
        summary_params = {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6}

    #if "early_stopping" not in summary_params:
        #summary_params["early_stopping"] = True
    
    chunks = chunk_text_tokenwise(text, tokenizer,max_chunk_tokens=chunk_token_limit)

    # Parallel summarize chunks
    with ThreadPoolExecutor(max_workers=4) as executor:
        chunk_summaries = list(executor.map(lambda c: summarize_chunk(c, summary_params,tokenizer,model), chunks))

    aggregated_summary = " ".join(chunk_summaries)

    # Hierarchical summarization
    final_summary = generate_summary(
        aggregated_summary,
        tokenizer,
        model,
        max_length=summary_params["max_length"],
        min_length=summary_params["min_length"],
        length_penalty=summary_params["length_penalty"],
        temperature=0.3,
        no_repeat_ngram_size=4,
        repetition_penalty=2.5,
        early_stopping=True,
        num_beams=summary_params["num_beams"],
    )
    return final_summary


if __name__ == "__main__":
    # Commented out to avoid error if running without this text
    input_text = "Replace this with the text you want to summarize."
    
    # For testing standalone, uncomment input_text assignment above or provide other text to test

    summary_params = [
        {"max_length": 45, "min_length": 10, "length_penalty": 1.0, "num_beams": 3, "name": "short_summary.txt"},
        {"max_length": 70, "min_length": 40, "length_penalty": 1.5, "num_beams": 5, "name": "medium_summary.txt"},
        {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6, "name": "long_summary.txt"},
    ]

    # Check that input_text is defined before proceeding (avoid runtime error)
    if 'input_text' in globals():
        for params in summary_params:
            if params["name"] == "long_summary.txt" and len(tokenizer.tokenize(input_text)) > 512:
                summary = summarize_long_text(input_text, chunk_token_limit=512, summary_params=params)
            else:
                summary = generate_summary(
                    input_text,
                    max_length=params["max_length"],
                    min_length=params["min_length"],
                    length_penalty=params["length_penalty"],
                    num_beams=params["num_beams"],
                    early_stopping=True,
                )
            # Save summary
            summary_file = os.path.join(SAVE_PATH, params["name"])
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"Saved {params['name']}: {summary}")

            # Save input text alongside with a matching filename (for reference)
            input_file = os.path.join(SAVE_PATH, params["name"].replace("summary", "input"))
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(input_text)
            print(f"Saved input text: {input_file}")
    else:
        print("input_text not defined, skipping standalone summary generation.")