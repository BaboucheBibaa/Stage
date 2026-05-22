from litellm import completion
from json import dumps


class Formattage:
    """
    Transforme un message de l'IA
    en mémoire compacte exploitable
    """

    def __init__(self, reponse_ia: str):
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
Récupérer un message généré par un assistant virtuel et en extraire les informations essentielles


RÈGLES STRICTES :

- Répond en commencant par "l'assistant à dit"
- Une seule phrase
- Extrais uniquement le sens utile retenu
- Ne jamais inventer d'information
- Ignore politesse et contexte inutile
- Sois synthétique, naturel et exploitable comme mémoire
"""
                },
                {
                    "role": "user",
                    "content": dumps({
                        "reponse_ia": self.reponse_ia
                    }, ensure_ascii=False)
                }
            ]
        )

        return response.choices[0].message.content.strip()


def main():

    reponse_ia = """
Salut Lucas ! C'est assez cool que tu te lances dans des jeux 2D d'exploration ! En faisant preuve de patience et de persévérance, j'ai le sentiment qu'on pourrait trouver un bon choix ensemble. Par exemple, si tu aimes les jeux indépendants, tu pourrais essayer "Hollow Knight". C'est un très bon jeu qui permet de voyager dans des paysages fantastiques et de dévoiler une histoire complexe. Si tu préfères des jeux plus connus, peut-être que "Limbo" ou "Inside" te plairont ! Tu peux toujours chercher d'autres options en faisant un petit tour sur le site de jeuvideo.com pour trouver ce qui correspond le mieux à ton goût. Quoi dirais-tu de ça ?
"""
    form = Formattage(reponse_ia)

    print(form.toString())


if __name__ == "__main__":
    main()