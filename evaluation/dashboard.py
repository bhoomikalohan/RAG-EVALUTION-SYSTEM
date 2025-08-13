import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def generate_evaluation_dashboard():
    """Generate simple evaluation dashboard"""
    try:
        with open("evaluation/latest_report.json", "r") as f:
            report = json.load(f)
        
        results_df = pd.DataFrame(report["detailed_results"])
        
        print("=== RAG System Performance Dashboard ===")
        print(f"Last Evaluation: {report['timestamp']}")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Average Similarity: {report['average_semantic_similarity']:.3f}")
        print("\nTop Performing Queries:")
        top_results = results_df.nlargest(3, 'semantic_similarity')
        for _, row in top_results.iterrows():
            print(f"  • {row['question'][:50]}... (Score: {row['semantic_similarity']:.3f})")
        
        print("\nLowest Performing Queries:")
        bottom_results = results_df.nsmallest(3, 'semantic_similarity')
        for _, row in bottom_results.iterrows():
            print(f"  • {row['question'][:50]}... (Score: {row['semantic_similarity']:.3f})")
            
    except FileNotFoundError:
        print("No evaluation report found. Run evaluation first.")

if __name__ == "__main__":
    generate_evaluation_dashboard()
