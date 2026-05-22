from db.bd import Database
from dataclasses import dataclass
from datetime import datetime
import spacy

nlp = spacy.load("fr_core_news_md")

@dataclass
class Message:
    id_message: int
    date_message: datetime
    contenu: str
    role_message: str  # 'USER' ou 'ASSISTANT'
    id_conversation: int
    tags: list[str] = None

@dataclass
class Conversation:
    id_conversation: int
    sujet: str
    id_profil: int
    date_creation: datetime
    id_compagnon: int
    messages: list[Message] = None

class GestionConversation:
    def __init__(self):
        self.db = Database()
    
    def switch_conv(message1: str,message2: str,seuil=0.45) -> bool:
        """Retourne si la conversation a été changée entre deux messages ou non, via une analyse sémantique.

        Args:
            message1 (str): Premier message
            message2 (str): Second message
            seuil (float, optional): Seuil à partir duquel on considère qu'il n'y a aucune similarité entre deux messages. Defaults to 0.45.

        Returns:
            bool: True si similarité détectée, False sinon.
        """
        return True if (nlp(message1).similarity(nlp(message2)) < seuil) else False
    
    def create_conversation(self, id_profil: int, id_compagnon: int, sujet: str) -> int:
        """Crée une nouvelle conversation"""
        try:
            self.db.execute(
                "INSERT INTO Conversation (ID_Profil, ID_Compagnon,Date_Creation, Sujet) "
                "VALUES (?, ?, ?, ?)",
                (id_profil, id_compagnon, datetime.now(), sujet)
            )
            result = self.db.executeFetch(
                "SELECT ID_Conversation FROM Conversation "
                "WHERE ID_Profil = ? AND ID_Compagnon = ? "
                "ORDER BY ID_Conversation DESC LIMIT 1",
                (id_profil, id_compagnon)
            )
            #retourne l'ID de la conversation créé.
            return result[0][0] if result else None
        except Exception as e:
            print(f"Erreur lors de la création de la conversation: {e}")
            return None
    
    def get_conversation(self, id_conversation: int) -> Conversation:
        """Récupère une conversation complète avec tous ses messages"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Conversation, Sujet, ID_Profil, Date_Creation, ID_Compagnon "
                "FROM Conversation WHERE ID_Conversation = ?",
                (id_conversation,)
            )
            if result:
                data = result[0]
                msg = self._get_conversation_messages(id_conversation)
                return Conversation(
                    id_conversation=data[0],
                    sujet=data[1],
                    id_profil=data[2],
                    date_creation=data[3],
                    id_compagnon=data[4],
                    messages=msg
                )
        except Exception as e:
            print(f"Erreur lors de la récupération de la conversation: {e}")
        return None
    
    def _get_conversation_messages(self, id_conversation: int) -> list[Message]:
        """Récupère tous les messages d'une conversation"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Message, Date_Message, Contenu, Role_Message, ID_Conversation "
                "FROM Messages WHERE ID_Conversation = ? "
                "ORDER BY Date_Message ASC",
                (id_conversation,)
            )
            messages = []
            for row in result:
                tags = self._get_message_tags(row[0])
                messages.append(Message(
                    id_message=row[0],
                    date_message=row[1],
                    contenu=row[2],
                    role_message=row[3],
                    id_conversation=row[4],
                    tags=tags
                ))
            return messages
        except Exception as e:
            print(f"Erreur lors de la récupération des messages: {e}")
            return []
    
    def _get_message_tags(self, id_message: int) -> list[str]:
        """Récupère les tags associés à un message"""
        try:
            result = self.db.executeFetch(
                "SELECT T.NomTag FROM Tag T "
                "JOIN Est_Associe EA ON T.ID_Tag = EA.ID_Tag "
                "WHERE EA.ID_Message = ?",
                (id_message,)
            )
            return [row[0] for row in result]
        except Exception as e:
            print(f"Erreur lors de la récupération des tags: {e}")
            return []
        
    def get_tag_actions(self,list_tag: list[str]) -> list[str]:
        requete = "SELECT Action FROM Tag_Actions WHERE ID_Tag IN (SELECT ID_Tag FROM Tag WHERE NomTag = ?)"
        result = []
        for tag in list_tag:
            tag_actions = self.db.executeFetch(requete,(tag,))
            result.extend([elt[0] for elt in tag_actions])
        return result
    
    def add_message(self, id_conversation: int, role_message: str, contenu: str, tags: list[str] = None) -> int:
        """Ajoute un message à une conversation"""
        try:
            # Valider le rôle
            if role_message not in ['USER', 'ASSISTANT']:
                print("Le rôle doit être 'USER' ou 'ASSISTANT'")
                return None
            
            self.db.execute(
                "INSERT INTO Messages (Role_Message, Date_Message, Contenu, ID_Conversation) "
                "VALUES (?, ?, ?, ?)",
                (role_message, datetime.now(), contenu, id_conversation)
            )
            
            # Récupère l'ID du message inséré
            result = self.db.executeFetch(
                "SELECT ID_Message FROM Messages WHERE ID_Conversation = ? "
                "ORDER BY Date_Message DESC LIMIT 1",
                (id_conversation,)
            )
            if result and tags:
                id_message = result[0][0]
                self._associer_messages_et_tags(id_message, tags)
            
            return result[0][0] if result else None
        except Exception as e:
            print(f"Erreur lors de l'ajout du message: {e}")
            return None
    
    def _associer_messages_et_tags(self, id_message: int, tags: list[str]):
        """Associe les tags à un message"""
        try:
            for tag in tags:
                # Récupère ou crée le tag
                result = self.db.executeFetch(
                    "SELECT ID_Tag FROM Tag WHERE NomTag = ?",
                    (tag,)
                )
                
                if result:
                    id_tag = result[0][0]
                    if id_tag:
                        # Associe le tag au message
                        self.db.execute(
                            "INSERT INTO Est_Associe (ID_Message, ID_Tag) VALUES (?, ?)",
                            (id_message, id_tag)
                        )
        except Exception as e:
            print(f"Erreur lors de l'association des tags: {e}")
    
    def get_recent_conversations(self, id_profil: int, limit: int = 10) -> list[dict[str,str | list[str]]]:
        """Récupère les conversations récentes d'un utilisateur"""
        try:
            result = self.db.executeFetch(
                "SELECT ID_Conversation, Sujet, ID_Profil,Date_Creation, ID_Compagnon FROM Conversation WHERE ID_Profil = ? ORDER BY ID_Conversation DESC LIMIT ?",
                (id_profil, limit)
            )
            
            conversations = []
            for row in result:
                unformatted_liste = self.db.executeFetch("select contenu from messages where id_conversation = ?", (row[0],))
                liste_messages = [elt[0] for elt in unformatted_liste]
                conversations.append({
                    "sujet":row[1],
                    "date_creation":str(row[3]),
                    "messages": liste_messages
                })
            return conversations
        except Exception as e:
            print(f"Erreur lors de la récupération des conversations: {e}")
            return []
    
    def update_conversation_subject(self, id_conversation: int, nouveau_sujet: str) -> bool:
        """Met à jour le sujet d'une conversation"""
        try:
            self.db.execute(
                "UPDATE Conversation SET Sujet = ? WHERE ID_Conversation = ?",
                (nouveau_sujet, id_conversation)
            )
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du sujet: {e}")
            return False
    
    def delete_conversation(self, id_conversation: int) -> bool:
        """Supprime une conversation et ses messages"""
        try:
            self.db.execute(
                "DELETE FROM Conversation WHERE ID_Conversation = ?",
                (id_conversation,)
            )
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression de la conversation: {e}")
            return False