from __future__ import annotations

from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI


def _build_openai_chat_chain(model_name: str, system_prompt: Optional[str] = None) -> Runnable:
    """Create the simplest LCEL chat chain for an OpenAI chat model.

    The chain expects an input mapping with the key "input" and returns a string.
    """
    effective_system = system_prompt or "You are a helpful assistant."
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", effective_system),
            ("human", "{input}"),
        ]
    )
    model = ChatOpenAI(model=model_name)
    return prompt | model | StrOutputParser()


def build_gpt5_chain(system_prompt: Optional[str] = None) -> Runnable:
    """Minimal chain using OpenAI GPT5."""
    return _build_openai_chat_chain("gpt-5", system_prompt)


def build_gpt5_nano_chain(system_prompt: Optional[str] = None) -> Runnable:
    """Minimal chain using OpenAI GPT5-nano."""
    return _build_openai_chat_chain("gpt-5-nano", system_prompt)


