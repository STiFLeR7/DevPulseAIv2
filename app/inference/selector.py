class ModelSelector:
    """
    Determines which model to use for a given agent task.
    """
    
    # Configuration map: Task Type -> Model ID
    # These should be updated based on Bytez.com available models
    MODEL_MAP = {
        "summarization": "meta-llama/Llama-3-8b-instruct",
        "relevance": "mistralai/Mistral-7B-Instruct-v0.2",
        "risk_analysis": "google/gemma-7b-it",
        "trend_detection": "microsoft/phi-3-mini-128k-instruct"
    }

    @classmethod
    def get_model_for_task(cls, task_type: str) -> str:
        return cls.MODEL_MAP.get(task_type, "meta-llama/Llama-3-8b-instruct")
