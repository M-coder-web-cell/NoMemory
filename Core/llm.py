import anthropic
import base64
from pathlib import Path
from typing import Optional
from .models.llmresponse import ResponseModel
from .models.llmcontent import ImageSource, Content


class LLMClient:

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
        max_tokens: int = 4000,
        thinking_budget: Optional[int] = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.conversation_history: list[dict] = []

    def addmessage(self, role: str, content) -> None:
        self.conversation_history.append({"role": role, "content": content})

    def ask(
        self,
        prompt: Optional[str],
        system_prompt: str,
        images: Optional[list] = None,
        thinking_budget: Optional[int] = None,
        use_history: bool = True,
    ) -> ResponseModel:
        content = []

        if images:
            for b64, media_type in images:
                block = Content(
                    type="image",
                    source=ImageSource(data=b64, media_type=media_type)
                )
                content.append(block.to_dict())

        if prompt:
            content.append(Content(type="text", text=prompt).to_dict())

        user_message = {"role": "user", "content": content}

        if use_history:
            self.conversation_history.append(user_message)
            messages_to_send = self.conversation_history
        else:
            messages_to_send = [user_message]

        budget = thinking_budget if thinking_budget is not None else self.thinking_budget

        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": messages_to_send,
        }

        if budget:
            if budget < 1024:
                budget = 1024
            assert budget < self.max_tokens, (
                f"thinking_budget ({budget}) must be less than max_tokens ({self.max_tokens})"
            )
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }

        response = self.client.messages.create(**params)

        text = ""
        thinking = ""

        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "thinking":
                thinking += block.thinking

        if use_history:
            self.addmessage("assistant", text)

        return ResponseModel(text=text, thinking=thinking)

    def clear_history(self) -> None:
        """Wipe the conversation history to start a fresh session."""
        self.conversation_history = []

    def get_history(self) -> list[dict]:
        """Return a copy of the current conversation history."""
        return list(self.conversation_history)

    def extract_from_path(
        self,
        image_path: str,
        prompt: str,
        system_prompt: str,
        thinking_budget: Optional[int] = None,
    ) -> ResponseModel:
        path = Path(image_path)
        media_type = _get_media_type(path.suffix)
        image_base64 = base64.standard_b64encode(
            path.read_bytes()
        ).decode("utf-8")
        return self.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            images=[(image_base64, media_type)],
            thinking_budget=thinking_budget,
        )


def _get_media_type(suffix: str) -> str:
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return mapping.get(suffix.lower().strip(), "image/jpeg")