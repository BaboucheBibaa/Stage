from projectTypes import LLMResponse, LLMMessage,BaseLLMClient
import ollama  as _ollama
class OllamaClient(BaseLLMClient):
    def __init__(self,model: str = "mistral",base_url: str = "http://localhost:11434",temperature: float = 0.7,**kwargs):
        super().__init__(model=model,temperature=temperature, **kwargs)
        
        self.base_url = base_url
        self._ollama = _ollama

    def send(self,messages: list[LLMMessage],json_schema : object = None, system_prompt: str = None) -> LLMResponse:
        """Envoie un message au LLM

        Args:
            messages (list[LLMMessage]): Contexte
            json_schema (object, optional): Modèle permettant de structurer la réponse générée par le LLM. Defaults to None.
            system_prompt (str, optional): Prompt système. Defaults to None.

        Returns:
            LLMResponse: _description_
        """
        api_messages = []
        args={}
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        if json_schema is not None:
            args['format'] = json_schema
        api_messages += [{"role": m.role, "content": m.contenu} for m in messages]
        response = self._ollama.chat(
            model=self.model,
            messages=api_messages,
            options={"temperature": self.temperature, "num_predict": self.max_tokens},
            **args
        )
        try:
            contenu_brut = response["message"]["content"]
            return LLMResponse(
                contenu=contenu_brut,
                modele=self.model,
                tokens_entree=response["prompt_eval_count"],
                tokens_sortie=response["eval_count"]
            )
        except Exception:
            return LLMResponse(contenu="", modele=self.model)