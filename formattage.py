from litellm import completion
from json import dumps

class Formattage:
    """
    Transforme un message utilisateur en un message réduit et exploitable par une IA
    """

    def __init__(self, message: str):
        self.message = message
        self.message = self.__generate_output()
    def toString(self):
        return self.message
    def __generate_output(self) -> str:
        response = completion(
            model="ollama/llama3.2",
            messages=[
                {
                    "role": "system",
"content": f"""
Tu es un système de mémoire.

Tu DOIS reformuler le message afin de garder uniquement les informations importantes.

RÈGLES STRICTES :
- La phrase doit commencer par "L'utilisateur"
- Aucune explication.
- utilise uniquement les mots exacts du message original, sans synonymes, pas d’ajouts
- Ne jamais inventer d’informations
- Fais UNIQUEMENT une phrase
"""                },
                {
                    "role": "user",
                    "content": dumps({
                        "message": self.message,
                    }, ensure_ascii=False)
                }
            ]
        )

        return response.choices[0].message.content.strip()
