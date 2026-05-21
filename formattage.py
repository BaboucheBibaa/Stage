from litellm import completion
from json import dumps


class Formattage:
    """
    Transforme un échange (message utilisateur + réponse IA)
    en mémoire compacte exploitable
    """

    def __init__(self, message_utilisateur: str, reponse_ia: str):
        self.message_utilisateur = message_utilisateur
        self.reponse_ia = reponse_ia
        self.message = self.__generate_output()

    def toString(self):
        return self.message

    def __generate_output(self) -> str:
        response = completion(
            model="ollama/mistral",
            messages=[
                {
                    "role": "system",
"content": """
Tu es un système de mémoire conversationnelle.

Ta tâche :
Fusionner le message utilisateur et la réponse de l'IA
pour extraire UNE information durable utile pour comprendre
les intérêts, apprentissages ou besoins de l'utilisateur.

RÈGLES STRICTES :

- Commence obligatoirement par "L'utilisateur"
- Une seule phrase
- Pas de mention de "message", "réponse", "IA" ou "conversation"
- Ne décris jamais l’échange
- Extrais uniquement le sens utile retenu
- Ne jamais inventer d'information
- Ignore politesse et contexte inutile
- Sois synthétique, naturel et exploitable comme mémoire
"""
                },
                {
                    "role": "user",
                    "content": dumps({
                        "message_utilisateur": self.message_utilisateur,
                        "reponse_ia": self.reponse_ia
                    }, ensure_ascii=False)
                }
            ]
        )

        return response.choices[0].message.content.strip()


def main():

    reponse_ia = """
Bonjour Lucas, GitHub est un service permettant de gérer des projets
collaboratifs avec repositories, branches, forks, clone et push.
Pour commencer, il faut créer un compte, créer un repository,
puis utiliser git clone et git push localement.
"""

    message_utilisateur = "explique moi comment utiliser github"

    form = Formattage(message_utilisateur, reponse_ia)

    print(form.toString())


if __name__ == "__main__":
    main()