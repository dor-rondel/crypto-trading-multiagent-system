"""
Base class for specialized analyst agents.
"""

from typing import Type

from pydantic import BaseModel

from src.config import Config
from src.utils.llm import get_groq_llm


class BaseAnalyst:
    """
    Base class for all analyst subagents.
    """

    def __init__(
        self,
        output_model: Type[BaseModel],
        model_name: str = Config.GROQ_MODEL_NAME or "",
    ):
        self.llm = get_groq_llm(model_name=model_name)
        self.structured_llm = self.llm.with_structured_output(output_model)
