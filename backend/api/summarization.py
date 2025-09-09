import os
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from concurrent.futures import ThreadPoolExecutor


# Set path to save inputs and outputs
print(os.getcwd())
SAVE_PATH = "summarization_samples"
os.makedirs(SAVE_PATH, exist_ok=True)


# Load tokenizer and model (Pegasus Large)
model_name = "google/pegasus-large"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)


def chunk_text_tokenwise(text, max_chunk_tokens=512):
    tokens = tokenizer.tokenize(text)
    chunks = []
    for i in range(0, len(tokens), max_chunk_tokens):
        chunk_tokens = tokens[i:i + max_chunk_tokens]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

def generate_summary(
    text,
    max_length=40,
    min_length=10,
    length_penalty=1.0,
    num_beams=3,
    temperature=None,
    no_repeat_ngram_size=None,
    repetition_penalty=None
):
    prompted_text = text
    inputs = tokenizer([prompted_text], truncation=True, padding='longest', return_tensors="pt")

    # Avoid unwanted words in summary
    bad_words = [
        "series", "part", "article", "copyright", "postmedia",
        "http", "www", ".com", "email", "share", "click",
        "including", "such as"
    ]
    bad_word_ids = [tokenizer.encode(word, add_special_tokens=False) for word in bad_words]

    # Build kwargs dynamically
    generate_kwargs = dict(
        max_length=max_length,
        min_length=min_length,
        length_penalty=length_penalty,
        num_beams=num_beams,
        early_stopping=True,
        bad_words_ids=bad_word_ids,
    )
    if temperature is not None:
        generate_kwargs["temperature"] = temperature
    if no_repeat_ngram_size is not None:
        generate_kwargs["no_repeat_ngram_size"] = no_repeat_ngram_size
    if repetition_penalty is not None:
        generate_kwargs["repetition_penalty"] = repetition_penalty

    summary_ids = model.generate(inputs.input_ids, **generate_kwargs)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary


def summarize_chunk(chunk, params):
    return generate_summary(
        chunk,
        max_length=params["max_length"],
        min_length=params["min_length"],
        length_penalty=params["length_penalty"],
        num_beams=params["num_beams"],
    )


def summarize_long_text(text, chunk_token_limit=512, summary_params=None):
    if summary_params is None:
        summary_params = {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6}

    chunks = chunk_text_tokenwise(text, max_chunk_tokens=chunk_token_limit)

    # Parallel summarize chunks
    with ThreadPoolExecutor(max_workers=4) as executor:
        chunk_summaries = list(executor.map(lambda c: summarize_chunk(c, summary_params), chunks))

    aggregated_summary = " ".join(chunk_summaries)

    # Hierarchical summarization (final summary of summaries)
    final_summary = generate_summary(
        aggregated_summary,
        max_length=summary_params["max_length"],
        min_length=summary_params["min_length"],
        length_penalty=summary_params["length_penalty"],
        temperature=0.3,
        no_repeat_ngram_size=4,
        repetition_penalty=2.5,
        num_beams=summary_params["num_beams"],
    )
    return final_summary


if __name__ == "__main__":
    # For testing standalone
    input_text = """Pegasus is a transformer model designed for abstractive text summarization.
    It is trained on large-scale datasets and performs strongly on multiple benchmarks."""

    summary_params = [
        {"max_length": 45, "min_length": 10, "length_penalty": 1.0, "num_beams": 3, "name": "short_summary.txt"},
        {"max_length": 70, "min_length": 40, "length_penalty": 1.5, "num_beams": 5, "name": "medium_summary.txt"},
        {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6, "name": "long_summary.txt"},
    ]

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
