from data.profil import GestionProfil
from data.personnality import PersonnalityManager
from data.conversation import GestionConversation, Conversation
from toTag import ToTag
from prompt import Prompt
import litellm

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
        #création de la conversation + stockage de l'id pour pouvoir la get après
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
        
        tags = self._recup_tags(user_message)
                
        response = self._generer_reponse(user_message)
        
        # Ajoute la réponse du compagnon
        self.conversation_manager.add_message(
            self.current_conversation.id_conversation,
            "ASSISTANT",
            response,
            tags
        )
        return response
    
    def _recup_tags(self, message: str) -> list[str]:
        """Récupère les tags du message"""
        try:
            tags_message = ToTag(message)
            tags = []
            for tag_list in tags_message.toString().values():
                tags.extend(tag_list)
            return tags
        except Exception as e:
            print(f"Erreur lors de l'extraction des tags: {e}")
            return []
    
    def _generer_reponse(self, user_message: str) -> str:
        """Génère une réponse avec le LLM"""
        try:
            
            prompt = Prompt(self.id_profil, self.id_compagnon, user_message).get_prompt()        
            messages = prompt
            return None
            response = litellm.completion(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erreur lors de la génération de la réponse: {e}")
            return "Je suis désolé, une erreur s'est produite."