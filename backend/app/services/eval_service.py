import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_ollama import ChatOllama, OllamaEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)

class EvalService:
    def __init__(self):
        self.llm = ChatOllama(model=settings.DEFAULT_TEXT_MODEL, base_url=settings.OLLAMA_BASE_URL)
        self.embeddings = OllamaEmbeddings(model=settings.DEFAULT_EMBEDDING_MODEL, base_url=settings.OLLAMA_BASE_URL)
        
        # We need ground_truth for context_recall, but we can evaluate faithfulness and answer_relevancy without it.
        # We will dynamically select metrics based on provided data.
        self.metrics_with_gt = [faithfulness, answer_relevancy, context_precision, context_recall]
        self.metrics_without_gt = [faithfulness, answer_relevancy]

    def evaluate_rag(self, question: str, contexts: list[str], answer: str, ground_truth: str = None) -> dict:
        """
        Evaluate a single RAG response.
        """
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
        
        metrics = self.metrics_without_gt
        
        if ground_truth:
            data["ground_truth"] = [ground_truth]
            metrics = self.metrics_with_gt
            
        dataset = Dataset.from_dict(data)
        
        try:
            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )
            return result
        except Exception as e:
            logger.error(f"RAGAS Evaluation failed: {e}", exc_info=True)
            return {}

eval_service = EvalService()
