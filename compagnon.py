from data.profil import GestionProfil
from data.personnality import PersonnalityManager
from data.conversation import GestionConversation, Conversation
from toTag import ToTag
from prompt import Prompt
import litellm
from formattage import Formattage

class CompagnonVirtuel:
    def __init__(self, id_profil: int, id_compagnon: int, model: str = "ollama/mistral"):
        self.id_profil = id_profil
        self.id_compagnon = id_compagnon
        self.model = model
        
        self.profile_manager = GestionProfil()
        self.personality_manager = PersonnalityManager()
        self.conversation_manager = GestionConversation()
        
        self.current_conversation: Conversation = None
    def commencer_conversation(self, sujet: str = "Conversation générale") -> Conversation:
        """Démarre une nouvelle conversation"""
        #création de la conversation + stockage de l'id pour pouvoir la réutiliser après
        conversation_id = self.conversation_manager.create_conversation(
            self.id_profil, 
            self.id_compagnon, 
            sujet
        )
        #Si la conversation a été créée alors on retourne son contenu (Conversation vide évidemment)
        if conversation_id:
            self.current_conversation = self.conversation_manager.get_conversation(conversation_id)
            return self.current_conversation
        return None
    
    def envoyer_message(self, user_message: str) -> str:
        """Envoie un message et reçoit une réponse"""
        if not self.current_conversation:
            print("Erreur: Aucune conversation active")
            return ""
        
        # Ajoute le message de l'utilisateur
        self.conversation_manager.add_message(
            self.current_conversation.id_conversation,
            "USER",
            user_message
        )
        
        self.__tags = self._recup_tags(user_message)
        reponse = self._generer_reponse(user_message)
        #on stocke la version formattée de cet échange et on affiche la version complète.
        reponse_formattee = Formattage(user_message,reponse).toString()
        # Ajoute la réponse du compagnon
        self.conversation_manager.add_message(
            self.current_conversation.id_conversation,
            "ASSISTANT",
            reponse_formattee,
            self.__tags
        )
        return reponse
    
    def _recup_tags(self, message: str) -> list[str]:
        """Récupère les tags du message"""
        try:
            tags_message = ToTag(message)
            tags = []
            for tag_list in tags_message.toString().values():
                #permet de mettre deux listes [a,b,c] et [d,e,f] dans une liste [a,b,c,d,e,f]
                tags.extend(tag_list)
            return tags
        except Exception as e:
            print(f"Erreur lors de l'extraction des tags: {e}")
            return []
    def __recup_tags_actions(self,tag_list: list[str]) -> list[str]:
        """Retourne les actions liées à une liste de tags.

        Args:
            tag_list (list[str]): Liste des tags d'un message.

        Returns:
            list[str]: Liste des actions à accomplir par l'IA
        """
        return self.conversation_manager.get_tag_actions(tag_list)
    
    def _generer_reponse(self, user_message: str) -> str:
        """Génère une réponse avec le LLM"""
        actions = self.__recup_tags_actions(self.__tags)
        prompt = Prompt(self.id_profil, self.id_compagnon, user_message,actions).get_prompt()        
        messages = prompt
        response = litellm.completion(
            model=self.model,
            messages=messages
        )
        
        return response.choices[0].message.content.strip()
