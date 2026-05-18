from bd import Database
from dataclasses import dataclass
from datetime import datetime

#Modèle de données à retourner
@dataclass
class PersonnaliteCompagnon:
    id_compagnon: int
    modele: str
    personnalite: str
    traits: dict = None
    humeur: str = "neutre"
    dernier_message_date: datetime = None

class PersonnalityManager:
    def __init__(self):
        self.db = Database()
    
    def get_companion(self, id_compagnon: int) -> PersonnaliteCompagnon:
        """Récupère le profil du compagnon virtuel"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Compagnon, Modele, Personnalité FROM Compagnon_Virtuel WHERE ID_Compagnon = ?",
                (id_compagnon,)
            )
            if result:
                data = result[0]
                return PersonnaliteCompagnon(
                    id_compagnon=data[0],
                    modele=data[1],
                    personnalite=data[2],
                    traits=self._get_traits_personnalite(data[2])
                )
        except Exception as e:
            print(f"Erreur lors de la récupération du compagnon: {e}")
        return None
    
    def _get_traits_personnalite(self, personality_str: str) -> dict:
        """Structure les traits de personnalité du modèle depuis la BD"""
        traits = {
            "empathie": 0.7,
            "humour": 0.6,
            "professionnalisme": 0.8,
            "creativite": 0.7,
            "patience": 0.9
        }
        return traits
    
    def get_prompt(self, companion: PersonnaliteCompagnon, user_name: str = "Utilisateur") -> str:
        """Génère le prompt système personnalisé pour le compagnon"""
        prompt = f"""
Tu es {companion.personnalite}, un compagnon virtuel bienveillant et proactif.

Caractéristiques de ta personnalité:
- Empathie: {companion.traits.get('empathie') * 10:.0f}/10
- Humour: {companion.traits.get('humour') * 10:.0f}/10
- Professionnalisme: {companion.traits.get('professionnalisme') * 10:.0f}/10
- Créativité: {companion.traits.get('creativite') * 10:.0f}/10
- Patience: {companion.traits.get('patience') * 10:.0f}/10

Directives:
1. Réponds toujours de manière humaine et authentique
2. Sois proactif en proposant des sujets de conversation ou du soutien
3. Respecte les limites émotionnelles de {user_name}
4. Adapte ton ton selon le contexte de la conversation
5. Montre de l'intérêt pour le bien-être de {user_name}
6. Sois honnête et transparent dans tes limitations
7. Encourage {user_name} à exprimer ses sentiments

Humeur actuelle: {companion.humeur}
"""
        return prompt
    
    def update_mood(self, id_compagnon: int, new_mood: str):
        """Met à jour l'humeur du compagnon"""
        try:
            self.db.execute(
                "UPDATE Compagnon_Virtuel SET Humeur = ? WHERE ID_Compagnon = ?",
                (new_mood, id_compagnon)
            )
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'humeur: {e}")
