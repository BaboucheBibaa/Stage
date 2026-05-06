import litellm


class Reducteur():
    """
    Réduit un message utilisateur tout en gardant son essence, 
    afin qu'il puisse être stocké en BD et exploité par l'IA plus tard afin qu'il puisse extraire des informations.\n
    <strong>L'objet utilisé pour instancier l'objet contient immédiatement (via objet.message) le résultat de la réduction.</strong>
    """
    def __init__(self,message):
        self.message = self.__generateOutput(message)
    def __generateOutput(self,message):
        response = litellm.completion(
            model="ollama/mistral",
            messages=[
                {
    
                "role": "system",
                "content": f"""Ton objectif est de résumer de façon concise le message que tu reçois.

                INSTRUCTIONS :
                - Garde uniquement les informations essentielles
                - Formule une phrase courte, claire et naturelle
                - Si une émotion ou un ressenti est exprimé, conserve-le
                - Utilise TOUJOURS "L’utilisateur" pour désigner la personne
                - N’utilise jamais "je", "tu" ou "vous"
                - Commence toujours la phrase par "L’utilisateur"
                - Supprime les détails secondaires (temps précis, hésitations, etc.)
                - La sortie doit être UNE SEULE phrase
                - Ne retourne QUE la phrase, sans explication

                EXEMPLES :

                Entrée :
                Hier après-midi, je suis allé au magasin de sport pour acheter un vélo parce que l’ancien était cassé, et après avoir comparé plusieurs modèles, j’ai finalement choisi un vélo blanc assez cher mais de très bonne qualité, que j’ai ensuite utilisé pour aller travailler aujourd’hui.

                Sortie :
                L’utilisateur a acheté un nouveau vélo blanc après que l’ancien soit cassé.

                Entrée :
                J'adore aller à la piscine, ça me détend tellement. Je fais quotidiennement 10 allers-retours de piscine.

                Sortie :
                L’utilisateur aime aller à la piscine pour se détendre et fait 10 allers-retours quotidiennement.
                """
                },

                {
                    "role": "user", 
                    "content": message
                    
                }
            ]
        )
        return response.choices[0].message['content']


def main():
    reduct = Reducteur("J'ai un rendez-vous demain à 19h, je stresse car c'est pour un entretien pour devenir devops, dans l'une des plus grosses boîtes de france actuellement sur le marché. j'ai terriblement peur de dire n'importe quoi.")
    res = reduct.message
    print(res)

if __name__ == "__main__":
    main()