from bd import Database
from profile import GestionProfil,ProfilUser
from personnality import PersonnalityManager, PersonnaliteCompagnon
from conversation import GestionConversation, Conversation
from toTag import ToTag
from llm import LLM
import litellm
from datetime import datetime, timedelta

class CompagnonVirtuel:
    def __init__(self, id_profil: int, id_compagnon: int, model: str = "ollama/mistral"):
        self.id_profil = id_profil
        self.id_compagnon = id_compagnon
        self.model = model
        
        self.db = Database()
        self.profile_manager = GestionProfil()
        self.personality_manager = PersonnalityManager()
        self.conversation_manager = GestionConversation()
        self.llm = LLM(model)
        
        # Charge les données
        self.profile: ProfilUser = self.profile_manager.get_profil(id_profil)
        self.personality: PersonnaliteCompagnon = self.personality_manager.get_companion(id_compagnon)
        self.current_conversation: Conversation = None
    
    def commencer_conversation(self, sujet: str = "Conversation générale") -> Conversation:
        """Démarre une nouvelle conversation"""
        if not self.profile or not self.personality:
            print("Erreur: Profil ou personnalité non chargés")
            return None
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
            "user",
            user_message
        )
        
        # Détecte les tags du message
        tags = self._recup_tags(user_message)
        
        # Vérifie les sujets sensibles
        self._check_sujets_sensibles(user_message, tags)
        
        # Génère la réponse
        system_prompt = self.personality_manager.get_prompt(
            self.personality,
            self.profile.prenom
        )
        
        response = self._generer_reponse(user_message, system_prompt)
        
        # Ajoute la réponse du compagnon
        self.conversation_manager.add_message(
            self.current_conversation.id_conversation,
            "assistant",
            response,
            tags
        )
        
        return response
    
    def _recup_tags(self, message: str) -> list[str]:
        """Récupère les tags du message"""
        try:
            tags_message = ToTag(message)
            tags = []
            for tag_list in tags_message.result.values():
                tags.extend(tag_list)
            return tags
        except Exception as e:
            print(f"Erreur lors de l'extraction des tags: {e}")
            return []
    
    def _check_sujets_sensibles(self, message: str, tags: list[str]):
        """Vérifie si le message touche à des sujets sensibles"""
        sensitive_subjects = self.profile.sujets_sensibles if self.profile else {}
        
        for tag in tags:
            if tag in sensitive_subjects:
                print(f"Sujet sensible détecté: {tag} (niveau: {sensitive_subjects[tag]})")
    
    def _generer_reponse(self, user_message: str, system_prompt: str) -> str:
        """Génère une réponse avec le LLM"""
        try:
            # Récupère l'historique des messages
            messages = [{"role": "system", "content": system_prompt}]
            
            if self.current_conversation and self.current_conversation.messages:
                for msg in self.current_conversation.messages[-10:]:  # Derniers 10 messages
                    messages.append({
                        "role": msg.role,
                        "content": msg.contenu_message
                    })
            
            messages.append({"role": "user", "content": user_message})
            
            response = litellm.completion(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erreur lors de la génération de la réponse: {e}")
            return "Je suis désolé, une erreur s'est produite."
    
    def be_proactive(self) -> str:
        """Compagnon proactif: initie une conversation basée sur les préférences"""
        if not self.profile or not self.personality:
            return None
        
        # Vérifie si la dernière conversation remonte à plusieurs heures
        recent_conversations = self.conversation_manager.get_recent_conversations(
            self.id_profil, 
            limit=1
        )
        
        if recent_conversations:
            last_conv_date = recent_conversations[0].date_creation
            time_diff = datetime.now() - last_conv_date
            
            if time_diff < timedelta(hours=4):
                return None  # Conversation trop récente
        
        # Génère une suggestion de conversation basée sur les préférences
        proactive_prompt = self._generer_prompt_proactif()
        
        # Démarre une nouvelle conversation
        self.commencer_conversation("Conversation proactive")
        
        # Envoie le message proactif
        response = self.envoyer_message(proactive_prompt)
        
        return response
    
    def _generer_prompt_proactif(self) -> str:
        """Génère un prompt proactif basé sur les préférences de l'utilisateur"""
        preferences = self.profile.preferences if self.profile else {}
        
        # Sélectionne un sujet basé sur les préférences
        if preferences:
            favorite_subject = max(preferences, key=preferences.get)
            return f"Parlons de {favorite_subject}. Comment ça se passe pour toi avec ça?"
        
        return "Comment vas-tu aujourd'hui? Il y a quelque chose que tu aimerais partager?"
    
    def suggerer_event(self, titre: str, description: str, date_event: str, tags: list[str] = None) -> bool:
        """Suggère un événement à l'utilisateur"""
        try:
            # Crée un événement
            self.db.execute(
                "INSERT INTO Event (ID_Profil, Titre, Date_Event, Statut, Contexte) "
                "VALUES (?, ?, ?, ?, ?)",
                (self.id_profil, titre, date_event, "suggéré", description)
            )
            
            # Récupère l'ID de l'événement
            result = self.db.executeFetch(
                "SELECT ID_Event FROM Event WHERE ID_Profil = ? "
                "ORDER BY Date_Event DESC LIMIT 1",
                (self.id_profil,)
            )
            
            if result and tags:
                # Associe les tags à l'événement si nécessaire
                for tag in tags:
                    tag_result = self.db.executeFetch(
                        "SELECT ID_Tag FROM Tags WHERE Nom_Tag = ?",
                        (tag,)
                    )
                    #si le résultat existe, alors on regarde le tag suivant (juste une question de sécurité)
                    if tag_result:
                        pass
            
            return True
        except Exception as e:
            print(f"Erreur lors de la création de l'événement: {e}")
            return False
    
    def save_memoire(self, donnees: str, id_profil: int = None) -> bool:
        """Sauvegarde des informations en mémoire long terme"""
        if id_profil is None:
            id_profil = self.id_profil
        
        try:
            self.db.execute(
                "INSERT INTO MLT (ID_Profil, Donnees, Date_Creation) "
                "VALUES (?, ?, ?)",
                (id_profil, donnees, datetime.now())
            )
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde en mémoire: {e}")
            return False
    
    def get_memoire(self, id_profil: int = None, days: int = 7) -> list[str]:
        """Récupère les souvenirs long terme"""
        if id_profil is None:
            id_profil = self.id_profil
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            result = self.db.executeFetch(
                "SELECT Donnees FROM MLT WHERE ID_Profil = ? "
                "AND Date_Creation >= ? "
                "ORDER BY Date_Creation DESC",
                (id_profil, cutoff_date)
            )
            return [row[0] for row in result]
        except Exception as e:
            print(f"Erreur lors de la récupération de la mémoire: {e}")
            return []
    
    def get_resume(self) -> dict:
        """Retourne un résumé de l'état du compagnon"""
        return {
            "utilisateur": f"{self.profile.prenom} {self.profile.nom}" if self.profile else "Inconnu",
            "compagnon": self.personality.personnalite if self.personality else "Inconnu",
            "conversations_actives": len(self.conversation_manager.get_recent_conversations(self.id_profil, limit=30)),
            "conversation_courante": self.current_conversation.id_conversation if self.current_conversation else None,
            "preferences": self.profile.preferences if self.profile else {},
            "sujets_sensibles": self.profile.sujets_sensibles if self.profile else {}
        }
