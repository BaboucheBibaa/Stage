from .LLMBase import BaseLLMClient, Message as LLMMessage, LLMResponse
import ollama  as _ollama
class OllamaClient(BaseLLMClient):
    def __init__(self,model: str = "mistral",base_url: str = "http://localhost:11434",temperature: float = 0.7,**kwargs):
        super().__init__(model=model,temperature=temperature, **kwargs)
        
        self.base_url = base_url
        self._ollama = _ollama

    def send(self,messages: list[LLMMessage],system_prompt: str = None,) -> LLMResponse:
        print("Fonction send()\n")
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
            
        api_messages += [{"role": m.role, "content": m.contenu} for m in messages]
        
        response = self._ollama.chat(
            model=self.model,
            messages=api_messages,
            options={"temperature": self.temperature, "num_predict": self.max_tokens},
            #formattage json imposé au LLM
            format='json'
        )
        print("Fonction send()\n Contenu du message retourné par le LLM: "+str(response) + "\n\n\n")
        try:
            contenu_brut = response["message"]["content"]
            return LLMResponse(
                contenu=contenu_brut,
                modele=self.model,
                tokens_entree=response.get("prompt_eval_count", 0),
                tokens_sortie=response.get("eval_count", 0),
            )
        except Exception:
            return LLMResponse(contenu="", modele=self.model)