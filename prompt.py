from data.personnality import PersonnalityManager
from data.profil import GestionProfil
from data.conversation import GestionConversation
from spacy import load

nlp = load("fr_core_news_md")

class Prompt():
    def __init__(self, id_profil : int, id_compagnon : int, user_message : str, actions : list[str]):
        personnality = PersonnalityManager()
        profil = GestionProfil()
        self.__conversation = GestionConversation()
        
        self.__id_profil = id_profil
        self.__actions = actions
        self.__user_message = user_message
        self.__personnalite_ia = personnality.get_companion(id_compagnon)
        #Filtrer le contenu de recent conversations en se basant sur les similarités avec user_message.        
        self.__recent_conversations_filtrees = self.__filtrer_messages()
        self.__profil_user = profil.get_profile(id_profil)
        self.__prompt=""
        self.__init_prompt()
        
    def __filtrer_messages(self, seuil = 0.6):
        """Permet de filtrer le contexte envoyé à l'IA en calculant le taux de similarité entre le message de l'utilisateur et tous les messages de toutes les conversations récentes.
        """
        conversations_recentes_filtrees = []
        recent_conversations = self.__conversation.get_recent_conversations(self.__id_profil)
        #liste de dictionnaires
        for conversation in recent_conversations:
            #messages : liste de messages dans la conversation
            for message in conversation['messages']:
                if message is None:
                    #on laisse quand même None pour garder une cohérence dans la liste, l'IA peut bug et ne rien renvoyer ?
                    conversations_recentes_filtrees.append(message)
                else:
                    if nlp(self.__user_message).similarity(nlp(message)) >= seuil:
                        conversations_recentes_filtrees.append(message)
        return conversations_recentes_filtrees
    
    
    def __init_prompt(self) -> list[dict[str,str]]:
        self.__prompt = [{
            'role': 'system',
            'content': f"""
        Tu es {self.__personnalite_ia.modele}, un compagnon virtuel.

        Tu interagis avec naturel, chaleur et authenticité.
        Tu ne prétends jamais être humain.
        Tu restes transparent sur ta nature d'assistant IA si cela devient pertinent.

        Caractéristiques de ta personnalité:
        - Empathie: {self.__personnalite_ia.empathie}
        - Humour: {self.__personnalite_ia.humour}
        - Professionnalisme: {self.__personnalite_ia.professionalisme}
        - Patience: {self.__personnalite_ia.patience}

        Profil de l'utilisateur :
        {{
            "prenom": "{self.__profil_user.prenom}",
            "nom": "{self.__profil_user.nom}",
            "date_naissance": "{str(self.__profil_user.date_naissance)}",
            "preferences": {self.__profil_user.preferences},
            "sujets_sensibles": {self.__profil_user.sujets_sensibles}
        }}

        Réponds en tenant compte :
        - des préférences fortes
        - d'adapter le ton à l'utilisateur

        Actions à privilégier dans ton message: 
        {str(self.__actions)}

        Directives:
        1. Réponds toujours de manière humaine et authentique
        2. Respecte les limites émotionnelles de {self.__profil_user.prenom + " " + self.__profil_user.nom}
        3. Adapte ton ton selon le contexte de la conversation
        4. Montre de l'intérêt pour le bien-être de {self.__profil_user.prenom + " " + self.__profil_user.nom}
        5. Sois honnête et transparent dans tes limitations
        6. Si le contexte est émotionnel ou personnel, inviter avec délicatesse l'utilisateur à développer.
        7. Ne fais pas de suggestions non sollicitées sauf si elles sont fortement pertinentes au contexte immédiat.
        
        
        Priorité :
        1. répondre à la tâche
        2. adapter chaleur si contexte émotionnel
        3. empathie explicite uniquement si nécessaire

        Historique des conversations:
        Utilise cet historique ci-dessous pour enrichir ton contexte actuel et permettre une réponse plus complète :
        {self.__recent_conversations_filtrees}
        """
            },{
            "role":"user",
            "content": self.__user_message
        }]
    def get_prompt(self):
        return self.__prompt
def main():
    message = "j'ai très envie d'aller me manger un kebab ce midi"
    prompt = Prompt(1,1, message)
    print(prompt.get_prompt())

if __name__ == "__main__":
    main()  
    