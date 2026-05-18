from bd import Database
from dataclasses import dataclass

@dataclass
class ProfilUser:
    id_profil: int
    nom: str
    prenom: str
    date_naissance: str
    preferences: dict
    sujets_sensibles: dict

class GestionProfil:
    def __init__(self):
        self.db = Database()
    
    def get_profile(self, id_profil: int) -> ProfilUser:
        """Récupère le profil d'un utilisateur"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Profil, Nom, Prenom, Date_Naissance FROM Profil WHERE ID_Profil = ?",
                (id_profil,)
            )
            if result:
                donnees_profil = result[0]
                preferences = self._get_prefererences_utilisateur(id_profil)
                sujets = self._get_sujets_sensibles(id_profil)
                
                return ProfilUser(
                    id_profil=donnees_profil[0],
                    nom=donnees_profil[1],
                    prenom=donnees_profil[2],
                    date_naissance=donnees_profil[3],
                    preferences=preferences,
                    sujets_sensibles=sujets
                )
        except Exception as e:
            print(f"Erreur lors de la récupération du profil: {e}")
        return None
    
    def _get_prefererences_utilisateur(self, id_profil: int) -> dict[str, int]:
        """Récupère les préférences de l'utilisateur"""
        try:
            result = self.db.executeFetch(
                "SELECT Sujet, Niveau FROM Preferences WHERE ID_Profil = ?",
                (id_profil,)
            )
            return {row[0]: row[1] for row in result}
        except Exception as e:
            print(f"Erreur lors de la récupération des préférences: {e}")
            return {}
    
    def _get_sujets_sensibles(self, id_profil: int) -> dict[str, int]:
        """Récupère les sujets sensibles pour l'utilisateur"""
        try:
            result = self.db.executeFetch(
                "SELECT Sujet, Niveau FROM Sujets_Sensibles WHERE ID_Profil = ?",
                (id_profil,)
            )
            return {row[0]: row[1] for row in result}
        except Exception as e:
            print(f"Erreur lors de la récupération des sujets sensibles: {e}")
            return {}
    
    def add_preference(self, id_profil: int, sujet: str, niveau: int):
        """Ajoute ou met à jour une préférence"""
        try:
            self.db.execute(
                "INSERT INTO Preferences (ID_Profil, Sujet, Niveau) "
                "VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE Niveau = ?",
                (id_profil, sujet, niveau, niveau)
            )
        except Exception as e:
            print(f"Erreur lors de l'ajout de préférence: {e}")
    
    def add_sujet_sensible(self, id_profil: int, sujet: str, niveau: int):
        """Ajoute ou met à jour un sujet sensible"""
        try:
            self.db.execute(
                "INSERT INTO Sujets_Sensibles (ID_Profil, Sujet, Niveau) "
                "VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE Niveau = ?",
                (id_profil, sujet, niveau, niveau)
            )
        except Exception as e:
            print(f"Erreur lors de l'ajout du sujet sensible: {e}")
