"""
Groq LLM utility.
"""

from langchain_groq import ChatGroq

from src.config import Config


def get_groq_llm(
    model_name: str = Config.GROQ_MODEL_NAME or "llama-3.3-70b-versatile",
    temperature: float = 0.1,
) -> ChatGroq:
    """
    Returns a ChatGroq instance with the given model name and temperature.
    """
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        max_retries=2,
    )
