from litellm import completion
from json import loads,dumps
from db.bd import Database

class ToTag:
    def __init__(self, message: str):
        #message original
        self.original_message = message
        self.__tags_list = self.__load_tags_config()
        #dump du json des tags
        self.__tags_autorises = dumps(self.__tags_list, ensure_ascii=False)
        self.__result = self._classification()
        self._confirmation()

    def toString(self):
        return self.__result
    #Extrait la liste des tags proposés par défaut. L'IA se basera uniquement sur cette liste de tags.
    def __load_tags_config(self):
        json = {}
        bd = Database()
        results = bd.executeFetch("SELECT NomTag,Categorie FROM Tag")
        categories = list({row[1] for row in results})
        for categorie in categories:
            json[categorie] = []
        for nom_tag,categorie in results:
            json[categorie].append(nom_tag)
        return json

    #Retourne sous forme de JSON la liste des données utiles pour gérer un message via des tags.
    def _classification(self):

        prompt = f"""
            Tu es un classificateur strict.

            MISSION :
            Associer un message utilisateur à des tags existants uniquement.

            TAGS AUTORISÉS :
            {self.__tags_autorises}

            RÈGLE ABSOLUE :
            Un tag retourné doit exister EXACTEMENT dans cette liste.

            Interdiction de :
            - créer un tag
            - reformuler
            - spécialiser
            - fusionner des tags

            Si aucun tag exact ne correspond :
            retourner []

            FORMAT UNIQUE :

            {{
            "intensite": [],
            "emotion": [],
            "etat": [],
            "domaines": [],
            "besoins": [],
            "contexte": []
            }}

            Toujours inclure les 6 clés.

            Aucun texte hors JSON.

            Ne pas interpréter au-delà du message explicite.

            Ne pas surinterpréter une salutation.

            Si message neutre :
            toutes listes vides.

            Vérification finale :
            supprimer tout tag absent de TAGS AUTORISÉS.
            """
        try:

            response = completion(
                model="ollama/mistral",
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": f"""
                        MESSAGE :
                        {self.original_message}"""
                    }
                ]
            )

            content = response.choices[0].message.content.strip()
            return loads(content)

        except Exception as e:
            print(e)
            #Retourne json vide
            return {
                "intensite": "Normale",
                "domaines": [],
                "etat": [],
                "emotion": [],
                "besoins": [],
                "contexte": []
            }
    def _confirmation(self):
        required = [
            "intensite",
            "domaines",
            "etat",
            "emotion",
            "besoins",
            "contexte"
        ]

        for key in required:
            if key not in self.__result:
                raise ValueError(
                    f"Sortie invalide : {self.__result}"
                )
        # Validation stricte des listes
        self.__result["domaines"] = self._validate_list(
            self.__result["domaines"],
            "domaines"
        )

        self.__result["etat"] = self._validate_list(
            self.__result["etat"],
            "etat"
        )

        self.__result["emotion"] = self._validate_list(
            self.__result["emotion"],
            "emotion"
        )

        self.__result["besoins"] = self._validate_list(
            self.__result["besoins"],
            "besoins"
        )
        
        self.__result["contexte"] = self._validate_list(
            self.__result["contexte"],
            "contexte"
        )
        
    #Vérifie si une liste est valide ou non.
    def _validate_list(self, values, category):
        allowed = set(
            self.__tags_list.get(category, [])
        )

        if not isinstance(values, list):
            return []

        return [
            v for v in values
            if v in allowed
        ]
        
def main():
    tag = ToTag("explique moi le fonctionnement d'une IA")
    print(tag.toString())
if __name__ == '__main__':
    main()