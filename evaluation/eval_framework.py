from test import HybridSearcher
import json
import asyncio
from typing import List, Dict
import pandas as pd
from datetime import datetime

class RAGEvaluator:
    def __init__(self):
        self.searcher = HybridSearcher()
        
    def load_test_dataset(self, file_path: str = "evaluation/test_dataset.json"):
        """Load your evaluation dataset"""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def evaluate_single_query(self, question: str, expected_answer: str, collections: List[str]):
        """Evaluate a single query through your RAG pipeline"""
        response_stream = self.searcher.process_query(question, collections)
        
        full_response = ""
        async for chunk in response_stream:
            if hasattr(chunk, 'text'):
                full_response += chunk.text
        
        return {
            "question": question,
            "expected_answer": expected_answer,
            "generated_answer": full_response,
            "collections_used": collections,
            "timestamp": datetime.now().isoformat()
        }
