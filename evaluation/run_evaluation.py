import asyncio
import json
from eval_framework import RAGEvaluator
from metrics import RAGMetrics
import sys

async def main():
    evaluator = RAGEvaluator()
    metrics = RAGMetrics()
    
    # Load test cases
    dataset = evaluator.load_test_dataset()
    
    results = []
    total_similarity = 0
    
    print("🚀 Starting RAG Evaluation...")
    
    for i, test_case in enumerate(dataset["test_cases"]):
        print(f"📝 Evaluating question {i+1}/{len(dataset['test_cases'])}")
        
        result = await evaluator.evaluate_single_query(
            test_case["question"],
            test_case["expected_answer"],
            test_case.get("collections", ["best_practices", "policies", "data"])
        )
        
        # Calculate metrics
        similarity = metrics.semantic_similarity(
            result["generated_answer"],
            result["expected_answer"]
        )
        
        result["semantic_similarity"] = similarity
        total_similarity += similarity
        results.append(result)
        
        print(f"   ✅ Similarity Score: {similarity:.3f}")
    
    avg_similarity = total_similarity / len(results)
    
    # Save results
    evaluation_report = {
        "timestamp": datetime.now().isoformat(),
        "average_semantic_similarity": avg_similarity,
        "total_tests": len(results),
        "detailed_results": results
    }
    
    with open("evaluation/latest_report.json", "w") as f:
        json.dump(evaluation_report, f, indent=2)
    
    print(f"\n📊 Evaluation Complete!")
    print(f"   Average Similarity: {avg_similarity:.3f}")
    print(f"   Results saved to: evaluation/latest_report.json")
    
    # Exit with error if performance is below threshold
    if avg_similarity < 0.7:  # Adjust threshold as needed
        print("❌ Performance below threshold!")
        sys.exit(1)
    else:
        print("✅ Performance meets expectations!")

if __name__ == "__main__":
    asyncio.run(main())
