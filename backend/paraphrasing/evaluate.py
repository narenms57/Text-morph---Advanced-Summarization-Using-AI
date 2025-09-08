# backend/paraphrasing/evaluate_all_levels.py
import argparse
import csv
import json
import os
import time
from statistics import mean
from typing import List, Dict
from rouge_score import rouge_scorer

LEVELS = ["conservative", "balanced", "creative"]

def compute_rouge(ref: str, hyp: str):
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(ref, hyp)
    return {
        "rouge1_f": scores["rouge1"].fmeasure,
        "rouge2_f": scores["rouge2"].fmeasure,
        "rougeL_f": scores["rougeL"].fmeasure,
    }

def evaluate(csv_path: str):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    per_level_scores = {level: [] for level in LEVELS}
    agg_scores = {level: {} for level in LEVELS}

    for row in rows:
        ref = row.get("reference", "").strip()
        if not ref:
            continue
        for level in LEVELS:
            gen_key = f"generated_{level}"
            hyp = row.get(gen_key, "").strip() or row.get("original", "").strip()
            scores = compute_rouge(ref, hyp)
            per_level_scores[level].append({
                "original": row.get("original", ""),
                "reference": ref,
                "generated": hyp,
                **scores
            })

    # Compute aggregates
    for level in LEVELS:
        if per_level_scores[level]:
            agg_scores[level] = {
                "rouge1_f_mean": mean([r["rouge1_f"] for r in per_level_scores[level]]),
                "rouge2_f_mean": mean([r["rouge2_f"] for r in per_level_scores[level]]),
                "rougeL_f_mean": mean([r["rougeL_f"] for r in per_level_scores[level]]),
                "count": len(per_level_scores[level])
            }
        else:
            agg_scores[level] = {"rouge1_f_mean":0.0,"rouge2_f_mean":0.0,"rougeL_f_mean":0.0,"count":0}

    # Save JSON report
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_folder = "reports"
    os.makedirs(out_folder, exist_ok=True)
    outpath = os.path.join(out_folder, f"rouge_results_all_levels_{stamp}.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump({"aggregate": agg_scores, "per_level": per_level_scores}, f, indent=2, ensure_ascii=False)

    print(f"✅ ROUGE evaluation saved to: {outpath}")
    print(json.dumps(agg_scores, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="CSV with columns: original, reference, generated_conservative, generated_balanced, generated_creative")
    args = parser.parse_args()
    evaluate(args.csv)
