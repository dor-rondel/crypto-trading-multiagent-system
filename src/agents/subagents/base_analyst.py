"""
Base class for specialized analyst subagents.
"""

from typing import Type

from pydantic import BaseModel

from src.utils.llm import get_groq_llm


class BaseAnalyst:
    """
    Base class providing common LLM initialization for analysts.
    """

    def __init__(
        self,
        output_model: Type[BaseModel],
        model_name: str = "llama-3.3-70b-versatile",
    ):
        self.llm = get_groq_llm(model_name=model_name)
        self.structured_llm = self.llm.with_structured_output(output_model)
