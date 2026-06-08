from datetime import datetime
from data.modeles import Conversation, Message, MCT, MLT
from LLM.LLMBase import Message as LLMMessage, BaseLLMClient
from prompts.prompt_loader import build_system_prompt
from data.dataclasses import (
    DonneesProfil, DonneesPreferences, DonneesSujetSensible,
    DonneesCompagnon, DonneesConversation, DonneesMessage,
    DonneesMLT, DonneesMCT,DonneesEvenement
)
from .resume import resumer_echange, resumer_session
from .EventDetection import DetectionEvent
import json

class DialogueModule:
    """Gère les dialogues entre l'utilisateur et le compagnon virtuel"""
    def __init__(self, llm: BaseLLMClient, id_profil: int):
        #dataclasses
        self.data_profil = DonneesProfil()
        self.data_prefs = DonneesPreferences()
        self.data_sujets = DonneesSujetSensible()
        self.data_compagnon = DonneesCompagnon()
        self.data_conv = DonneesConversation()
        self.data_msg = DonneesMessage()
        self.data_mlt = DonneesMLT()
        self.data_mct = DonneesMCT()
        self.data_evenement = DonneesEvenement()
        
        self.llm = llm
        self.id_profil = id_profil
        self.detection_event = DetectionEvent(self.llm, self.data_evenement, self.id_profil)
        
        # Charger les données du profil
        self.profil = self.data_profil.getProfil(id_profil)
        if not self.profil:
            raise ValueError(f"Profil avec l'ID {id_profil} introuvable en base de données")
        
        self.compagnon = self.data_compagnon.getCompagnon(1)
        if not self.compagnon:
            raise ValueError("Aucun compagnon virtuel trouvé en base de données")
        
        self.prefs = self.data_prefs.getPreferences(id_profil)
        self.sensibles = self.data_sujets.getSujets(id_profil)
        self.mlt = self.data_mlt.getRecente(id_profil)
        
        # Historique de la conversation
        self._historique: list[LLMMessage] = []
        self._id_conversation = self._nouvelle_conversation()
        if not self._id_conversation:
            raise RuntimeError("Impossible de créer une nouvelle conversation")
        
    def chat(self, message_user: str) -> str:
        """Envoie un message et reçoit une réponse personnalisée"""
        prompt_systeme = self._build_system_prompt()
        # Ajouter le message utilisateur à l'historique (on ne lit que l'historique)
        self._historique.append(LLMMessage(role="user", contenu=message_user))
        
        # Appeler le LLM
        response = self.llm.send(
            messages=self._historique, 
            system_prompt=prompt_systeme
        )
        reponse_texte = response.contenu
        
        # Ajouter la réponse à l'historique
        self._historique.append(LLMMessage(role="assistant", contenu=reponse_texte))
        #détection d'événement dans un message
        self.detection_event.detecter(message_user)
        
        self._sauvegarder_message(message_user, reponse_texte)
        self._add_MCT(message_user, reponse_texte)
        json_result = json.loads(reponse_texte)
        return json_result['message']
    
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
            mct_list=self.data_mct.getToday(self.id_profil),
        )
    def _nouvelle_conversation(self) -> int:
        """Crée une nouvelle conversation"""
        conv = Conversation(
            sujet="Session du " + datetime.now().strftime("%d/%m/%Y %H:%M"),
            id_user=self.id_profil,
            id_companion=self.compagnon.id,
            date_creation=datetime.now(),
        )
        return self.data_conv.create(conv)
    def _sauvegarder_message(self, msg_user: str, rep_assistant: str) -> None:
        """Sauvegarde le message et la réponse en BD"""
        try:
            self.data_msg.create(Message(
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
            historique = self.data_mct.getToday(id_profil)
            if not historique:
                return False
            # Création de l'enregistrement de la mémoire long terme avec les données
            mlt_resume = resumer_session(self.llm, historique, self.data_mlt.getRecente(id_profil))
            mlt_id = self.data_mlt.create(MLT(
                id_profil=self.id_profil,
                date_creation=datetime.now(),  # Datetime object, pas string
                text=mlt_resume
            ))
            if mlt_id:
                # Si ça a bien été créé, alors on vide la MCT
                self.data_mct.nettoyage(id_profil)
                # Rafraîchir le cache de MLT
                self.mlt = self.data_mlt.getRecente(id_profil)
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
            message_brut = resumer_echange(self.llm, msg_user, rep_assistant)
            #On tente de formatter le résultat du LLM en JSON pour voir si c'est correct ou non. On veut juste vérifer que c'est un format valide.
            try:
                json.loads(message_brut)
                message = message_brut
            except json.JSONDecodeError:
                message = json.dumps({
                    "sujet": message_brut,
                    "intention_utilisateur": "",
                    "evenements_mentionnes": [],
                    "tags": [],
                    "resume_reponse": [],
                    "entites_mentionnees": [],
                    "langue": "français"
                })
            
            mct_id = self.data_mct.create(MCT(
                message=message,
                id_profil=self.id_profil,
                date_creation=datetime.now(),
            ))
            
            if mct_id:
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