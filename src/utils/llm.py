"""
Utility for initializing LLM clients.
"""

import os

from langchain_groq import ChatGroq
from pydantic import SecretStr


def get_groq_llm(
    model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.1
) -> ChatGroq:
    """
    Initializes and returns a ChatGroq instance.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    return ChatGroq(
        model=model_name,
        api_key=SecretStr(api_key),
        temperature=temperature,
    )
