import litellm


class DiscussionAnalysis():
    """
    Analyse un message de l'utilisateur et détermine de quel type de message il s'agit.
    """
    def __init__(self,message):
        self.message = self.__generateOutput(message)
    def __generateOutput(self,message):
        response = litellm.completion(
            model="ollama/mistral",
            messages=[
                {
    
                "role": "system",
                "content": f"""Ton objectif est de déterminer de quoi l'utilisateur parle.

                INSTRUCTIONS :
                - Le résultat donné doit être entre 1 ou 3 mots MAXIMUM
                - Le résultat DOIT être en français
                EXEMPLES :

                Entrée :
                Hier après-midi, je suis allé au magasin de sport pour acheter un vélo parce que l’ancien était cassé, et après avoir comparé plusieurs modèles, j’ai finalement choisi un vélo blanc assez cher mais de très bonne qualité, que j’ai ensuite utilisé pour aller travailler aujourd’hui.

                Sortie :
                Quotidien, Achat

                Entrée :
                J'adore aller à la piscine, ça me détend tellement. Je fais quotidiennement 10 allers-retours de piscine.

                Sortie :
                Passion, Sport
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
    reduct = DiscussionAnalysis("Hier j'ai été me balader au centre-ville. \
                       C'était trop bien ! J'ai pu découvrir des magasins que je n'avais jamais pu voir auparavant. \
                    Cependant, les articles proposés étaient trop chers pour moi, je n'ai donc rien acheté. \
                        Cela m'a rendu triste.")
    res = reduct.message
    print(res)

if __name__ == "__main__":
    main()