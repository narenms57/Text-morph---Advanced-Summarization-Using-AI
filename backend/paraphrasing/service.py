from functools import lru_cache
from typing import List, Dict
from transformers import pipeline

# Default T5 paraphraser
DEFAULT_T5 = "ramsrigouthamg/t5_paraphraser"

# Presets for creativity levels
LEVEL_PRESETS: Dict[str, Dict] = {
    "conservative": {"temperature": 0.5, "top_p": 0.7, "repetition_penalty": 1.3},
    "balanced": {"temperature": 0.9, "top_p": 0.92, "repetition_penalty": 1.1},
    "creative": {"temperature": 1.2, "top_p": 0.95, "repetition_penalty": 1.0},
}

@lru_cache(maxsize=2)
def get_pipe(model_name: str = DEFAULT_T5):
    return pipeline("text2text-generation", model=model_name)

def paraphrase(
    text: str,
    level: str = "balanced",
    num_return_sequences: int = 3,
    max_new_tokens: int = 50,
    model_name: str = "t5"
):
    """
    Paraphrase text in three styles:
    - conservative: professional/formal
    - balanced: natural word changes
    - creative: story-like / expressive
    Ensures outputs are **sentences**, not questions.
    """
    # Map model
    if model_name.lower() == "t5":
        model_id = "ramsrigouthamg/t5_paraphraser"
    elif model_name.lower() == "bart":
        model_id = "eugenesiow/bart-paraphrase"
    else:
        model_id = model_name

    pipe = get_pipe(model_id)

    # Use text as prompt directly; avoid question-style generation
    prompt = text

    # Prepare generation parameters
    params = LEVEL_PRESETS.get(level, LEVEL_PRESETS["balanced"]).copy()
    params.update({
        "do_sample": True,
        "num_return_sequences": num_return_sequences,
        "max_new_tokens": max_new_tokens,
        "num_beams": 1,
        "clean_up_tokenization_spaces": True,
    })

    # Generate paraphrases
    outputs = pipe(prompt, **params)
    paraphrases = [o["generated_text"].strip() for o in outputs]

    # Remove duplicates and exact copies
    paraphrases = list(dict.fromkeys([p for p in paraphrases if p.lower() != text.lower()]))

    # If no valid paraphrase, return original
    return paraphrases or [text], params
