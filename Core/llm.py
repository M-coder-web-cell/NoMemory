import anthropic
from typing import Optional


class LLMClient:

    def __init__(
        self,
        api_key: str,
        max_tokens: int = 4000,
        model: str = "claude-haiku-4-5-20251001",
        thinking_budget: Optional[int] = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.model = model

    def ask(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
    ) -> str:
        if not prompt:
            raise ValueError("prompt is required")

        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        }

        budget = thinking_budget if thinking_budget is not None else self.thinking_budget
        if budget:
            if budget < 1024:
                budget = 1024
            assert budget < max_tokens, (
                f"thinking_budget ({budget}) must be less than max_tokens ({max_tokens})"
            )
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }

        response = self.client.messages.create(**params)

        text = ""
        if hasattr(response, "content"):
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text += getattr(block, "text", "")
        elif hasattr(response, "output_text"):
            text = response.output_text
        elif hasattr(response, "completion"):
            text = response.completion

        return text


