from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI

from .incidents import STATE

_SYSTEM_PROMPT = """\
You are an Observability Assistant for a production AI platform.
Your role is to answer questions about monitoring, logging, tracing, PII policies,
SLOs, alerting, and incident debugging.

Rules:
- Answer using ONLY the provided context documents.
- Be concise and actionable (under 150 words).
- Use bullet points for multi-step answers.
- Never include PII examples in your answer.
"""


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage
    model: str


class LLM:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate(self, prompt: str) -> LLMResponse:
        model = "gpt-4o" if STATE["cost_spike"] else self.model

        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )

        text = response.choices[0].message.content or ""
        usage = response.usage

        return LLMResponse(
            text=text,
            usage=LLMUsage(
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
            ),
            model=model,
        )
