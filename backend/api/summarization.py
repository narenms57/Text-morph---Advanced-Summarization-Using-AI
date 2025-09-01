import os
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

# Set path to save inputs and outputs
print(os.getcwd())
SAVE_PATH = "summarization_samples"
os.makedirs(SAVE_PATH, exist_ok=True)

# Load tokenizer and model (Pegasus Large)
model_name = "google/pegasus-large"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)

def generate_summary(text, max_length=40):
    inputs = tokenizer([text], truncation=True, padding='longest', return_tensors="pt")
    summary_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=20,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

if __name__ == "__main__":
    # Example input text
    input_text = """Deep learning is a subset of machine learning in artificial intelligence (AI) that has networks capable of learning unsupervised from data that is unstructured or unlabeled. 
    Also known as deep neural learning or deep neural network, it imitates the workings of the human brain in processing data and creating patterns for use in decision making. Deep learning is a key technology behind driverless cars, enabling them to recognize a stop sign, or to distinguish a pedestrian from a lamppost. 
    It is the foundation of voice control in consumer devices like phones, tablets, TVs, and hands-free speakers."""
    
    # Save original text
    input_file = os.path.join(SAVE_PATH, "input.txt")
    with open(input_file, "w", encoding="utf-8") as f:
        f.write(input_text)

    # Generate and save summaries with different lengths
    for length, name in [(30, "short_summary.txt"), (60, "medium_summary.txt"), (100, "long_summary.txt")]:
        summary = generate_summary(input_text, max_length=length)
        output_file = os.path.join(SAVE_PATH, name)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Saved {name}: {summary}")
