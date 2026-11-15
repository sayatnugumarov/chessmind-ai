"""The ONLY module that talks to an LLM provider.

Uses the OpenAI-compatible Chat Completions API, which Groq, Gemini
(AI Studio), OpenRouter and OpenAI all accept. Switching provider means
changing LLM_BASE_URL / LLM_MODEL / LLM_API_KEY in .env; no code changes.
The rest of the backend depends only on the `LLM` protocol below, so tests
can pass a fake.
"""

import json
from dataclasses import dataclass, field
from typing import Protocol

from ..config import settings


class LLMError(RuntimeError):
    """Provider unreachable, rate-limited, misconfigured or returned junk."""


@dataclass
class ToolRequest:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMReply:
    content: str
    tool_requests: list[ToolRequest] = field(default_factory=list)


class LLM(Protocol):
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply: ...


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 45.0):
        from openai import OpenAI  # imported here so tests never need network setup

        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout, max_retries=1)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply:
        import openai

        kwargs: dict = {"model": self.model, "messages": messages, "temperature": 0.3}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        try:
            resp = self._client.chat.completions.create(**kwargs)
        except openai.RateLimitError as e:
            raise LLMError("LLM rate limit reached. Wait a minute and try again.") from e
        except openai.AuthenticationError as e:
            raise LLMError("LLM API key rejected. Check LLM_API_KEY.") from e
        except openai.OpenAIError as e:
            raise LLMError(f"LLM request failed: {type(e).__name__}") from e

        if not resp.choices:
            raise LLMError("LLM returned no answer.")
        msg = resp.choices[0].message
        requests = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            requests.append(ToolRequest(id=tc.id, name=tc.function.name, arguments=args))
        return LLMReply(content=(msg.content or "").strip(), tool_requests=requests)


def get_llm() -> LLM | None:
    """The configured LLM, or None if no API key is set."""
    if not settings.llm_api_key:
        return None
    return OpenAICompatibleLLM(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
