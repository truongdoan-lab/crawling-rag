import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.config import load_settings
from chatbot_pipeline.chat_pipeline import ChatPipeline


def load_golden_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    return [{"question": it["question"], "reference": it["reference"]} for it in items]


def run_pipeline_on_dataset(pipeline: ChatPipeline, items: list[dict]) -> list[dict]:
    results = []
    for i, item in enumerate(items, start=1):
        question = item["question"]
        print(f"[{i}/{len(items)}] Asking: {question[:70]}...")
        try:
            out = pipeline.answer(question)
        except Exception as exc:
            print(f"Error occurred while answering this question: {exc}")
            out = {"answer": "", "context_texts": []}
        results.append(
            {
                "question": question,
                "reference": item["reference"],
                "answer": out.get("answer", ""),
                "context_texts": out.get("context_texts", []),
            }
        )
    return results


def build_ragas_dataset(results: list[dict]):
    from ragas import EvaluationDataset, SingleTurnSample

    samples = [
        SingleTurnSample(
            user_input=r["question"],
            response=r["answer"],
            retrieved_contexts=r["context_texts"] or [""],
            reference=r["reference"],
        )
        for r in results
    ]
    return EvaluationDataset(samples=samples)


def build_judge():
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    settings = load_settings()
    judge_llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    judge_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", google_api_key=settings.gemini_api_key
    )
    return LangchainLLMWrapper(judge_llm), LangchainEmbeddingsWrapper(judge_embeddings)


def evaluate_dataset(ragas_dataset):
    from ragas import evaluate
    from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

    evaluator_llm, evaluator_embeddings = build_judge()
    metrics = [
        Faithfulness(llm=evaluator_llm),
        AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
        ContextPrecision(llm=evaluator_llm),
        ContextRecall(llm=evaluator_llm),
    ]
    return evaluate(dataset=ragas_dataset, metrics=metrics)


def main():
    parser = argparse.ArgumentParser(description="Evaluate chatbot pipeline on a golden dataset using RAGAS.")
    parser.add_argument("dataset", help="Path to the golden_dataset.json file")
    parser.add_argument("--output", default="eval/eval_report.csv", help="CSV file to save detailed results")
    args = parser.parse_args()

    items = load_golden_dataset(args.dataset)
    print(f"Loaded {len(items)} questions from {args.dataset}\n")

    settings = load_settings()
    pipeline = ChatPipeline(settings)
    results = run_pipeline_on_dataset(pipeline, items)

    ragas_dataset = build_ragas_dataset(results)
    eval_result = evaluate_dataset(ragas_dataset)

    df = eval_result.to_pandas()
    df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print("\nAVERAGE SCORES")
    numeric_cols = df.select_dtypes(include="number").columns
    print(df[numeric_cols].mean().round(3).to_string())
    print(f"\nDetail for each question saved to: {args.output}")


if __name__ == "__main__":
    main()
