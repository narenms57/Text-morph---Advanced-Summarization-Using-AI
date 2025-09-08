import csv
import requests
import os

# Backend API URL
API_URL = "http://127.0.0.1:8000/paraphrasing/generate"

# Input/Output CSV paths
INPUT_CSV = "backend/paraphrasing/sample_text_para/paraphrase_eval.csv"
OUTPUT_CSV = "backend/paraphrasing/sample_text_para/paraphrase_eval_filled_all_levels.csv"

# Model settings
MODEL_NAME = "t5"
NUM_RETURN_SEQUENCES = 1
MAX_NEW_TOKENS = 100

# Levels
LEVELS = ["conservative", "balanced", "creative"]

def get_paraphrase(text: str, level: str):
    """Call backend API for one level and return first paraphrase."""
    resp = requests.post(API_URL, json={
        "text": text,
        "level": level,
        "num_return_sequences": NUM_RETURN_SEQUENCES,
        "max_new_tokens": MAX_NEW_TOKENS,
        "model_name": MODEL_NAME
    })
    if resp.status_code == 200:
        return resp.json()["paraphrases"][0]
    else:
        return f"ERROR {resp.status_code}"

def main():
    rows = []

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row["original"]
            ref = row.get("reference", "")

            generated = {}
            for level in LEVELS:
                generated[level] = get_paraphrase(text, level)

            rows.append({
                "original": text,
                "reference": ref,
                "generated_conservative": generated["conservative"],
                "generated_balanced": generated["balanced"],
                "generated_creative": generated["creative"]
            })

    # Write output CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "original",
            "reference",
            "generated_conservative",
            "generated_balanced",
            "generated_creative"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Filled CSV with all levels saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
