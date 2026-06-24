import json

import ollama as _ollama
from pydantic import BaseModel

from data.projectTypes import BaseLLMClient, LLMMessage


class OllamaClient(BaseLLMClient):
    def __init__(self):
        self._client = _ollama

    def send(
        self,
        messages: list[LLMMessage],
        model: str = "gemma4:31b-cloud",
        system_prompt: str | None = None,
        output_model: BaseModel | None = None,
        options: dict | None = None,
        keep_alive: float | None = None,
    ) -> BaseModel | str:

        msgs = []

        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})

        msgs.extend({"role": m.role, "content": m.contenu} for m in messages)

        args = {
            "model": model,
            "messages": msgs,
            "options": options,
            "keep_alive": keep_alive,
        }

        if output_model:
            args["format"] = output_model.model_json_schema()

        response = self._client.chat(**args)

        contenu: str = response["message"]["content"]

        if output_model:
            result = json.loads(contenu)
            validated: BaseModel = output_model.model_validate(result)
            return validated

        return contenu
