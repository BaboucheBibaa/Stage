from datetime import datetime
from data.modeles import Conversation, Message, MCT, MLT
from LLM.LLMBase import Message as LLMMessage, BaseLLMClient
from prompts.prompt_loader import build_system_prompt
import data.dataclasses as dt
from .resume import resumer_echange, resumer_session
from .DetectionEvent import DetectionEvent
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
        self.event_repo : dt.DonneesEvenement = data_repos['event']
        
        self.llm = llm
        self.id_profil = id_profil
        self.detection_event = DetectionEvent(self.llm, self.event_repo, self.id_profil)
        
        # Charger les données du profil
        self.profil = self.profil_repo.getProfil(id_profil)
        if not self.profil:
            raise ValueError(f"Profil avec l'ID {id_profil} introuvable en base de données")
        
        self.compagnon = self.compagnon_repo.getCompagnon(1)
        if not self.compagnon:
            raise ValueError("Aucun compagnon virtuel trouvé en base de données")
        
        self.prefs = self.prefs_repo.getPreferences(id_profil)
        self.sensibles = self.sujets_repo.getSujets(id_profil)
        self.mlt = self.mlt_repo.getRecente(id_profil)
        
        # Historique de la conversation
        self._historique: list[LLMMessage] = []
        self._id_conversation = self._nouvelle_conversation()
        if not self._id_conversation:
            raise RuntimeError("Impossible de créer une nouvelle conversation")

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
        self.detection_event.detecter(message_user)
        self._sauvegarder_message(message_user, reponse_texte)
        self._add_MCT(message_user, reponse_texte)
        
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
        try:
            self.msg_repo.create(Message(
                msg_user=msg_user,
                reponse_assistant=rep_assistant,
                id_conversation=self._id_conversation,
                date_creation=datetime.now(),
            ))
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {e}")
    def sauvegarder_MLT(self, id_profil: int) -> bool:
        """Sauvegarde la mémoire long terme (MLT) et nettoie la MCT"""
        try:
            # Récupération de la discussion de la journée
            historique = self.mct_repo.getToday(id_profil)
            if not historique:
                print("Aucune conversation à sauvegarder dans la MLT")
                return False
            
            # Création de l'enregistrement de la mémoire long terme avec les données
            mlt_resume = resumer_session(self.llm, historique, self.mlt_repo.getRecente(id_profil))
            mlt_id = self.mlt_repo.create(MLT(
                id_profil=self.id_profil,
                date_creation=datetime.now(),  # Datetime object, pas string
                text=mlt_resume
            ))
            
            if mlt_id:
                # Si ça a bien été créé, alors on vide la MCT
                self.mct_repo.nettoyage(id_profil)
                # Rafraîchir le cache de MLT
                self.mlt = self.mlt_repo.getRecente(id_profil)
                print(f"MLT sauvegardée avec succès (ID: {mlt_id})")
                return True
            else:
                print("Erreur: Impossible de sauvegarder la MLT")
                return False
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la MLT: {e}")
            return False

    def _add_MCT(self, msg_user: str, rep_assistant: str) -> bool:
        """Ajoute une donnée dans la mémoire court terme (MCT)"""
        try:
            resume = resumer_echange(self.llm, msg_user, rep_assistant)
            mct_id = self.mct_repo.create(MCT(
                message=resume,
                id_profil=self.id_profil,
                date_creation=datetime.now(),
            ))
            if mct_id:
                print(f"MCT créée avec succès (ID: {mct_id})")
                return True
            else:
                print("Erreur: Impossible de créer la MCT")
                return False
        except Exception as e:
            print(f"Erreur lors de l'ajout en MCT: {e}")
            return False
    @staticmethod
    def _calculer_age(date_naissance : datetime) -> int:
        """Calcule l'âge à partir de la date de naissance
        
        Args:
            date_naissance: datetime.date, datetime.datetime, ou string au format 'YYYY-MM-DD'
            
        Returns:
            int: Age en années
        """
        try:
            today = datetime.now()
            age = today.year - date_naissance.year
            
            # Ajuster si l'anniversaire n'a pas eu lieu cette année
            if (today.month, today.day) < (date_naissance.month, date_naissance.day):
                age -= 1
            
            return age
        except Exception as e:
            print(f"Erreur lors du calcul de l'âge: {e}")
            return 0