from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Message:
    """Un message dans une conversation."""
    role: str   # "user", "assistant", ou "system"
    contenu: str

class LLMResponse(BaseModel):
    contenu: str
    modele: str
    tokens_entree: int = 0
    tokens_sortie: int = 0


class BaseLLMClient(ABC):
    """
    Interface commune pour tous les fournisseurs LLM.
    Tout le reste du code n'utilise que cette interface.
    """

    def __init__(self, model: str, temperature: float, max_tokens: int = 512):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def send(self,messages: list[Message],json_schema: object,system_prompt: str = None) -> LLMResponse:
        """
        Envoie une liste de messages et retourne une réponse normalisée.
        C'est la seule méthode que le reste du projet appelle.
        """
        ...

    def send_simple(self, user_text: str, json_schema : object, system_prompt: str = None) -> str:
        """
        Raccourci pour un échange simple : texte vers texte.
        Utile pour les tests rapides ou les appels internes (extraction de profil, etc.).
        """
        response = self.send(
            messages=[Message(role="user", contenu=user_text)],
            system_prompt=system_prompt,
            json_schema = json_schema
        )
        return response.contenu.strip()