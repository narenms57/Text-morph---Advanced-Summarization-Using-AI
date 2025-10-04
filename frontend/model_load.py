from transformers import ByT5Tokenizer, T5ForConditionalGeneration
import torch

model_path = "C:/Users/naren/TextMorph/backend/models/google-byt5-base-fine-tuned/content/t5_finetuned_prefix/checkpoint-339"

# Load tokenizer and model
tokenizer = ByT5Tokenizer.from_pretrained("google/byt5-base")
model = T5ForConditionalGeneration.from_pretrained(model_path)

# Prepare input
text = "My name is Naren and I live in Chennai."
inputs = tokenizer(text, return_tensors="pt")

# Generate output (with better sampling settings)
output_ids = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=True,
    top_p=0.95,
    top_k=50,
    num_beams=5,
    no_repeat_ngram_size=2,
    repetition_penalty=1.5,
    early_stopping=True
)

# Decode output safely
try:
    decoded = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
except Exception as e:
    print("Decoding error:", e)
    decoded = tokenizer.decode(output_ids[0], skip_special_tokens=True)

print("Generated paraphrase:", decoded)
