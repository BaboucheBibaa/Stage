from .LLMBase import BaseLLMClient, Message as LLMMessage, LLMResponse
import ollama  as _ollama
class OllamaClient(BaseLLMClient):
    """
    Fournisseur local via Ollama (llama3, mistral, phi3, etc.).
    Aucune clé API requise — tourne entièrement en local.
    Pré-requis : Ollama installé et `ollama serve` actif.
    """

    def __init__(self,model: str = "mistral",base_url: str = "http://localhost:11434",temperature: float = 0.7,**kwargs):
        super().__init__(model=model,temperature=temperature, **kwargs)
        
        self.base_url = base_url
        self._ollama = _ollama

    def send(self,messages: list[LLMMessage],system_prompt: str = None,) -> LLMResponse:
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages += [{"role": m.role, "content": m.content} for m in messages]
        response = self._ollama.chat(
            model=self.model,
            messages=api_messages,
            options={"temperature": self.temperature, "num_predict": self.max_tokens},
        )

        return LLMResponse(
            content=response["message"]["content"],
            model=self.model,
            input_tokens=response.get("prompt_eval_count", 0),
            output_tokens=response.get("eval_count", 0),
            raw=response,
        )