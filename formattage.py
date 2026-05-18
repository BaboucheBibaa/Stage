from litellm import completion
from spacy import load
from json import dumps
from datetime import datetime

nlp = load("fr_core_news_sm")

class Formattage:
    """
    Transforme un message utilisateur en un message réduit et exploitable par une IA
    """

    def __init__(self, message: str):
        self.message = message
        self.features = self.__extract_features(message)
        self.message = self.__generate_output()
    #Analyse sémantique
    def __extract_features(self, message: str):
        doc = nlp(message)

        """
        Récupération d'entités spaCy: 
        PER -> nom propres
        LOC -> Localisations (non gps)
        ORG -> Compagnies / Agences / Institutions etc
        DATE -> date ou période relative
        TIME -> Temps inférieur à une journée
        """
        entities = [
            {
                "text": ent.text,
                "label": ent.label_
            }
            for ent in doc.ents
            if ent.label_ in ["PER", "LOC", "ORG", "DATE", "TIME"]
        ]

        verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

        #token.lemma_ -> récupère les mots sous leur forme de base afin d'extraire un vrai sens plutôt que 50 variantes du même mot.
        nouns = [
            token.lemma_
            for token in doc
            if token.pos_ == "NOUN" and len(token.text) > 3
        ]

        return {
            "entities": entities,
            "verbes": verbs,
            "noms": nouns,
            "timestamp": datetime.now().isoformat() #heure au format courant (voir doc .isoformat())
        }


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
