import os
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from concurrent.futures import ThreadPoolExecutor

# Save path for paraphrased samples
SAVE_PATH = "paraphrase_samples"
os.makedirs(SAVE_PATH, exist_ok=True)

# Load tokenizer and model (reuse Pegasus)
model_name = "google/pegasus-large"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)

def chunk_text_tokenwise(text, max_chunk_tokens=512):
    tokens = tokenizer.tokenize(text)
    chunks = []
    for i in range(0, len(tokens), max_chunk_tokens):
        chunk_tokens = tokens[i:i+max_chunk_tokens]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

def generate_paraphrase(text, max_length=100, min_length=20, length_penalty=1.0, num_beams=4):
    prompted_text = text
    inputs = tokenizer([prompted_text], truncation=True, padding='longest', return_tensors="pt")

    paraphrase_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=min_length,
        length_penalty=length_penalty,
        num_beams=num_beams,
        early_stopping=True
    )

    paraphrased = tokenizer.decode(paraphrase_ids[0], skip_special_tokens=True)
    return paraphrased

def paraphrase_long_text(text, chunk_token_limit=512, paraphrase_params=None):
    if paraphrase_params is None:
        paraphrase_params = {"max_length": 120, "min_length": 30, "length_penalty": 1.2, "num_beams": 4}
    
    chunks = chunk_text_tokenwise(text, max_chunk_tokens=chunk_token_limit)

    with ThreadPoolExecutor(max_workers=4) as executor:
        chunk_paraphrases = list(executor.map(lambda c: generate_paraphrase(
            c,
            max_length=paraphrase_params["max_length"],
            min_length=paraphrase_params["min_length"],
            length_penalty=paraphrase_params["length_penalty"],
            num_beams=paraphrase_params["num_beams"],
        ), chunks))

    aggregated_paraphrase = " ".join(chunk_paraphrases)
    return aggregated_paraphrase