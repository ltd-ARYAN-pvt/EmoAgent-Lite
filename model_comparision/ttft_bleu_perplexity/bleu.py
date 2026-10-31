
import os
import requests
import pandas as pd
import sacrebleu

from config import OLLAMA_URL, MODELS, MAX_TOKENS

DATASET = "dataset/questions.csv"
OUTPUT_FILE = "results/bleu_results.csv"


def generate(model_tag, prompt):

    payload = {
        "model": model_tag,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,

        # Important: Disable thinking
        "think": False,

        "options": {
            "num_predict": MAX_TOKENS,
            "temperature": 0
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=600
        )

        response.raise_for_status()

        result = response.json()

        # Chat API returns the answer inside message.content
        prediction = result.get("message", {}).get("content", "").strip()

        print(f"Model: {model_tag}")
        print(f"Prediction: {repr(prediction)}")

        if not prediction:
            print("WARNING: Model returned an empty answer!")
            print("Full response:", result)

        return prediction

    except requests.exceptions.RequestException as e:
        print(f"API Error for {model_tag}: {e}")
        return ""


if __name__ == "__main__":

    # Create results folder if it does not exist
    os.makedirs("results", exist_ok=True)

    # Load dataset
    data = pd.read_csv(DATASET)

    # Validate dataset
    required_columns = {"question", "reference"}

    if not required_columns.issubset(data.columns):
        raise ValueError(
            "CSV must contain question and reference columns."
        )

    rows = []

    references = data["reference"].fillna("").astype(str).tolist()

    # Compare all models
    for model_name, model_tag in MODELS.items():

        print("\n" + "=" * 50)
        print(f"Evaluating model: {model_name}")
        print(f"Model tag: {model_tag}")
        print("=" * 50)

        predictions = []

        for index, row in data.iterrows():

            prompt = (
                "Answer the following question clearly and concisely. "
                "Do not add unrelated information.\n"
                f"Question: {row['question']}\n"
                "Answer:"
            )

            prediction = generate(model_tag, prompt)

            predictions.append(prediction)

            rows.append({
                "model": model_name,
                "model_tag": model_tag,
                "question": row["question"],
                "reference": row["reference"],
                "prediction": prediction
            })

            print(
                f"{model_name}: completed question "
                f"{index + 1}/{len(data)}"
            )

        # Calculate BLEU only using generated predictions
        valid_predictions = [
            p for p in predictions if p.strip()
        ]

        valid_references = [
            ref for p, ref in zip(predictions, references)
            if p.strip()
        ]

        if not valid_predictions:
            score = 0.0
            status = "FAILED - No answers generated"

        else:
            score = sacrebleu.corpus_bleu(
                valid_predictions,
                [valid_references],
                smooth_method="exp",
                use_effective_order=True
            ).score

            status = "SUCCESS"

        # Add score and status to each row of this model
        for item in rows:
            if item["model"] == model_name:
                item["corpus_bleu"] = score
                item["status"] = status

        print("\nModel:", model_name)
        print("Generated answers:", len(valid_predictions))
        print("Empty answers:", len(predictions) - len(valid_predictions))
        print(f"Corpus BLEU: {score:.4f}")
        print("Status:", status)

    # Save results
    results = pd.DataFrame(rows)

    results.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 50)
    print("FINAL MODEL COMPARISON")
    print("=" * 50)

    summary = results.groupby(
        ["model", "model_tag"]
    ).agg(
        corpus_bleu=("corpus_bleu", "first"),
        generated_answers=("prediction", lambda x: x.str.strip().ne("").sum()),
        total_questions=("question", "count")
    ).reset_index()

    print(summary.to_string(index=False))

    print(f"\nSaved results to: {OUTPUT_FILE}")

    print(
        "\nNote: BLEU measures textual similarity with reference answers, "
        "not factual correctness or semantic quality."
    )
