from datetime import datetime
from data.modeles import Conversation, Message, MCT
from LLM.LLMBase import Message as LLMMessage, BaseLLMClient
from prompts.prompt_loader import build_system_prompt
import data.dataclasses as dt
from .resume import resumer_echange, resumer_session
MCT_WINDOW = 10  # Garder les 10 derniers messages en mémoire court terme

class DialogueModule:
    """Gère les dialogues entre l'utilisateur et le compagnon virtuel"""
    
    def __init__(self, data_repos: dict, llm: BaseLLMClient, id_profil: int):
        #dataclasses
        self.profil_repo : dt.DonneesProfil = data_repos['profil']
        self.prefs_repo : dt.DonneesPreferences = data_repos['preferences']
        self.sujets_repo : dt.DonneesSujetSensible = data_repos['sujets_sensibles']
        self.compagnon_repo : dt.DonneesCompagnon = data_repos['compagnon']
        self.conv_repo : dt.DonneesConversation = data_repos['conversation']
        self.msg_repo : dt.DonneesMessage = data_repos['message']
        self.mlt_repo : dt.DonneesMLT = data_repos['mlt']
        self.mct_repo : dt.DonneesMCT = data_repos['mct']
        
        self.llm = llm
        self.id_profil = id_profil
        
        # Charger les données du profil
        self.profil = self.profil_repo.getProfil(id_profil)
        self.compagnon = self.compagnon_repo.getCompagnon(1)
        self.prefs = self.prefs_repo.getPreferences(id_profil)
        self.sensibles = self.sujets_repo.getSujets(id_profil)
        self.mlt = self.mlt_repo.getRecente(id_profil)
        
        #Historique de la conversation
        self._historique: list[LLMMessage] = []
        self._id_conversation = self._nouvelle_conversation()

    def chat(self, message_user: str) -> str:
        """Envoie un message et reçoit une réponse personnalisée"""
        system_prompt = self._build_system_prompt()
        # Ajouter le message utilisateur à l'historique (on ne lit que l'historique)
        self._historique.append(LLMMessage(role="user", content=message_user))
        
        # Appeler le LLM
        response = self.llm.send(
            messages=self._historique, 
            system_prompt=system_prompt
        )
        reponse_texte = response.content
        
        # Ajouter la réponse à l'historique
        self._historique.append(LLMMessage(role="assistant", content=reponse_texte))
        
        # Persister les données
        self._sauvegarder_message(message_user, reponse_texte)
        self._mettre_a_jour_mct(message_user, reponse_texte)
        
        return reponse_texte

    def _build_system_prompt(self) -> str:
        """Construit le prompt système personnalisé"""
        return build_system_prompt(
            nom_compagnon=self.compagnon.modele,
            prenom=self.profil.prenom,
            nom=self.profil.nom,
            age=self._calculer_age(self.profil.date_naissance),
            profil=self.compagnon.profil,
            preferences=self.prefs,
            sujets_sensibles=self.sensibles,
            mlt_text=self.mlt.text if self.mlt else "",
            mct_list=self.mct_repo.getToday(self.id_profil),
        )

    def _nouvelle_conversation(self) -> int:
        """Crée une nouvelle conversation"""
        conv = Conversation(
            sujet="Session du " + datetime.now().strftime("%d/%m/%Y %H:%M"),
            id_user=self.id_profil,
            id_companion=self.compagnon.id,
            date_creation=datetime.now(),
        )
        return self.conv_repo.create(conv)

    def _sauvegarder_message(self, msg_user: str, rep_assistant: str) -> None:
        """Sauvegarde le message et la réponse en BD"""
        self.msg_repo.create(Message(
            msg_user=msg_user,
            reponse_assistant=rep_assistant,
            id_conversation=self._id_conversation,
            date_creation=datetime.now(),
        ))

    def _mettre_a_jour_mct(self, msg_user: str, rep_assistant: str) -> None:
        """Met à jour la mémoire court terme (MCT)"""
        self.mct_repo.create(MCT(
            message=resumer_echange(self.llm, msg_user,rep_assistant),
            id_profil=self.id_profil,
            date_creation=datetime.now(),
        ))
        # Garder seulement les N derniers messages
        self.mct_repo.nettoyage(self.id_profil, conserver=MCT_WINDOW)

    @staticmethod
    def _calculer_age(date_naissance : datetime) -> int:
        """Calcule l'âge à partir de la date de naissance"""
        today = datetime.today()
        return today.year - date_naissance.year - (
            (today.month, today.day) < (date_naissance.month, date_naissance.day)
        )