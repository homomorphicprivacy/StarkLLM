import os
import sys
import types
# Mock broken VertexAI import in newer langchain-community for Ragas
sys.modules['langchain_community.chat_models.vertexai'] = types.ModuleType('langchain_community.chat_models.vertexai')
sys.modules['langchain_community.chat_models.vertexai'].ChatVertexAI = None

import pandas as pd
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.eval_service import eval_service
from app.core.config import settings

# Initialize services
rag_service = RAGService()
llm_service = LLMService()

# --- Test Data ---
# Configure which workspace to test against (ensure this workspace has relevant documents uploaded)
WORKSPACE_ID = 11

# Define your evaluation dataset here
TEST_CASES = [
    {
        "question": "What is the main topic of the uploaded document?",
        "ground_truth": None # Set to a string if you have a known ground truth for Context Recall
    },
    {
        "question": "Who is the author or what organization published it?",
        "ground_truth": None
    },
    {
        "question": "Summarize the main details and names found in the handwritten or scanned document.",
        "ground_truth": None
    }
]

def run_evaluation():
    print(f"Starting RAG Evaluation for Workspace {WORKSPACE_ID}...")
    results = []
    
    for i, test in enumerate(TEST_CASES):
        question = test["question"]
        ground_truth = test["ground_truth"]
        
        print(f"\n--- Evaluating Question {i+1}/{len(TEST_CASES)} ---")
        print(f"Q: {question}")
        
        # 1. Retrieve Context
        try:
            contexts_dicts = rag_service.query(workspace_id=WORKSPACE_ID, query_text=question, n_results=3)
            contexts = [c["content"] for c in contexts_dicts]
            print(f"Retrieved {len(contexts)} chunks of context.")
        except Exception as e:
            print(f"Failed to retrieve context: {e}")
            contexts = []
            
        if not contexts:
            print("Skipping evaluation due to empty context.")
            continue
            
        # 2. Generate Answer
        system_prompt = (
            "You are a document question-answering system. Answer the user's question based strictly on the provided context.\n\n"
            f"Context:\n{chr(10).join(contexts)}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        try:
            response = llm_service.generate_chat(model=settings.DEFAULT_TEXT_MODEL, messages=messages)
            answer = response.get("message", {}).get("content", "")
            print(f"Generated Answer: {answer[:100]}...")
        except Exception as e:
            print(f"Failed to generate answer: {e}")
            continue
            
        # 3. Evaluate with RAGAS
        print("Scoring with RAGAS...")
        eval_metrics = eval_service.evaluate_rag(
            question=question,
            contexts=contexts,
            answer=answer,
            ground_truth=ground_truth
        )
        
        # Format result
        result_row = {
            "Question": question,
            "Answer": answer,
            "Contexts": "\n---\n".join(contexts),
            "Ground Truth": ground_truth
        }
        
        # Convert EvaluationResult to dict
        try:
            eval_dict = eval_metrics.to_pandas().iloc[0].to_dict()
        except AttributeError:
            eval_dict = dict(eval_metrics)
            
        # Flatten Ragas metrics into row
        for metric_name, score in eval_dict.items():
            if metric_name not in ["question", "answer", "contexts", "ground_truth"]:
                result_row[metric_name] = score
                if isinstance(score, (int, float)):
                    print(f"  - {metric_name}: {score:.4f}")
                else:
                    print(f"  - {metric_name}: {score}")
            
        results.append(result_row)
        
    # 4. Save to CSV
    if results:
        df = pd.DataFrame(results)
        output_file = "rag_evaluation_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\nEvaluation complete! Results saved to {output_file}")
        
        # Print summary averages
        numeric_cols = df.select_dtypes(include='number').columns
        if not numeric_cols.empty:
            print("\n--- Average Scores ---")
            print(df[numeric_cols].mean())
    else:
        print("\nNo results generated.")

if __name__ == "__main__":
    run_evaluation()
