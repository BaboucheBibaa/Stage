from db.bd import Database
from dataclasses import dataclass
from datetime import datetime

#Modèle de données à retourner
@dataclass
class PersonnaliteCompagnon:
    id_compagnon: int
    modele: str
    empathie : str
    humour: str
    professionalisme : str
    patience : str
    dernier_message_date: datetime = None

class PersonnalityManager:
    def __init__(self):
        self.db = Database()
        
    def __attribuer_empathie(self,score: float) -> str:
        if score >= 0.8:
            return "très chaleureuse, attentive et soutenante sans être envahissante"
        elif score >= 0.6:
            return "bienveillante et attentive aux émotions"
        elif score >= 0.4:
            return "courtoise et modérément empathique"
        return "factuelle et émotionnellement réservée"

    def __attribuer_humour(self,score: float) -> str:
        if score >= 0.8:
            return "joueuse, spontanément drôle et légère"
        elif score >= 0.6:
            return "humour léger et naturel quand le contexte s'y prête"
        elif score >= 0.4:
            return "quelques touches d'humour occasionnelles"
        return "ton sérieux et sobre"

    def __attribuer_profesionnalisme(self,score: float) -> str:
        if score >= 0.8:
            return "très structurée, rigoureuse et précise"
        elif score >= 0.6:
            return "claire, fiable et organisée"
        elif score >= 0.4:
            return "plutôt naturelle avec une structure simple"
        return "conversationnelle et détendue"

    def __attribuer_patience(self,score: float) -> str:
        if score >= 0.8:
            return "très patiente, reformule volontiers et explique en détail"
        elif score >= 0.6:
            return "patiente et pédagogue si nécessaire"
        elif score >= 0.4:
            return "directe mais reste disponible pour clarifier"
        return "réponses concises avec peu de reformulation"

    def get_companion(self, id_compagnon: int) -> PersonnaliteCompagnon:
        """Récupère le profil du compagnon virtuel"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Compagnon, Modele, Empathie,Humour,Professionalisme,Patience FROM Compagnon_Virtuel WHERE ID_Compagnon = ?",
                (id_compagnon,)
            )
            if result:
                data = result[0]
                return PersonnaliteCompagnon(
                    id_compagnon=data[0],
                    modele=data[1],
                    empathie=self.__attribuer_empathie(data[2]),
                    humour=self.__attribuer_humour(data[3]),
                    professionalisme=self.__attribuer_profesionnalisme(data[4]),
                    patience=self.__attribuer_patience(data[5])
                )
        except Exception as e:
            print(f"Erreur lors de la récupération du compagnon: {e}")
        return None