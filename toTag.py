from litellm import completion
from json import loads,dumps,load
from formattage import Formattage
from bd import Database

class ToTag:
    def __init__(self, message: str):
        #message original
        self.original_message = message
        #message réduit après passage sous réducteur
        self.message_reduit = Formattage(self.original_message).message
        self.tags_list = self.__load_tags_config()
        #dump du json des tags
        self.tags_autorises = dumps(self.tags_list, ensure_ascii=False)
        self.result = self._classification()

        self._confirmation()

        self.message = dumps(
            self.result,
            ensure_ascii=False,
            indent=2
        )

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
            Tu es un système expert de classification émotionnelle et contextuelle.

            Ta mission :
            Analyser un message utilisateur et l’associer STRICTEMENT aux tags fournis en prenant UNIQUEMENT les idées explicites ou fortement implicites.

            RÈGLES IMPORTANTES :
            - Tu dois inférer le contexte implicite (ex : examen, soutenance = Études + Pression)
            - Ne jamais inventer de tags
            - Ne pas proposer de needs si aucun besoin implicite clair.
            - si implicite, n’ajoute qu’un seul tag le plus probable.
            - max 1–2 tags par champ sauf si explicitement multiple
            - Si aucun tag pertinent : liste vide
            - Retour JSON strict uniquement
            - Le JSON doit contenir obligatoirement 6 champs : intensite, emotion, etat, domaines, besoins, contexte.
            - Le champ intensite contient UN SEUL tag ou AUCUN si c'est pertinent.

            LOGIQUE ATTENDUE :
            - intensite = importance du message pour l'utilisateur
            - emotion = ressenti interne (stress, joie, anxiété...)
            - etat = état global (fatigue, pression, motivation...)
            - domaines = domaine de vie concerné
            - besoins = besoin implicite de l'utilisateur
            - contexte = contexte concerné par le message

            TAGS DISPONIBLES :
            {self.tags_autorises}
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
            #Retourne json vide
            return {
                "intensity": "Normale",
                "domain": [],
                "state": [],
                "emotion": [],
                "needs": [],
                "contexte": []
            }
    def _confirmation(self):
        required = [
            "intensite",
            "domaines",
            "etat",
            "emotion",
            "besoins",
        ]

        for key in required:
            if key not in self.result:
                raise ValueError(
                    f"Sortie invalide : clé manquante {key}"
                )
        # Validation stricte des listes
        self.result["domaines"] = self._validate_list(
            self.result["domaines"],
            "domaines"
        )

        self.result["etat"] = self._validate_list(
            self.result["etat"],
            "etat"
        )

        self.result["emotion"] = self._validate_list(
            self.result["emotion"],
            "emotion"
        )

        self.result["besoins"] = self._validate_list(
            self.result["besoins"],
            "besoins"
        )
        
        self.result["contexte"] = self._validate_list(
            self.result["contexte"],
            "contexte"
        )
        
    #Vérifie si une liste est valide ou non.
    def _validate_list(self, values, category):
        allowed = set(
            self.tags_list.get(category, [])
        )

        if not isinstance(values, list):
            return []

        return [
            v for v in values
            if v in allowed
        ]