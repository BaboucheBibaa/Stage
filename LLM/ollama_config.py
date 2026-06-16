from projectTypes import LLMResponse, LLMMessage,BaseLLMClient
import ollama  as _ollama
class OllamaClient(BaseLLMClient):

    def __init__(self):
        self._client = _ollama

    def send(
        self,
        messages: list[LLMMessage],
        model: str = "qwen3:14b",
        system_prompt: str | None = None,
        json_schema: object | None = None,
        options: dict | None = None,
        keep_alive: str | float | None = None,
        stream: bool = False,
        think: bool = False,
        tools: list | None = None
    ) -> LLMResponse:

        api_messages = []

        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })

        api_messages.extend({"role": m.role,"content": m.contenu} for m in messages)

        parametres = {
            "model": model,
            "messages": api_messages,
            "stream": stream
        }

        if options:
            parametres["options"] = options

        if keep_alive is not None:
            parametres["keep_alive"] = keep_alive

        if json_schema is not None:
            parametres["format"] = json_schema

        if think:
            parametres["think"] = think

        if tools:
            parametres["tools"] = tools

        response = self._client.chat(**parametres)

        return LLMResponse(
            contenu=response["message"]["content"],
            thinking=response["message"].get("thinking"),
            modele=model,
            tokens_entree=response.get("prompt_eval_count", 0),
            tokens_sortie=response.get("eval_count", 0)
        )