from pydantic import BaseModel
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from abc import ABC, abstractmethod

@dataclass
class LLMMessage:
    """Un message tel qu'il est interprété par un LLM, il contient obligatoirement un rôle et un contenu (voir docu Ollama / OpenAI)."""
    role: str   # "user", "assistant", ou "system"
    contenu: str

class LLMResponse(BaseModel):
    contenu: str
    modele: str
    tokens_entree: int
    tokens_sortie: int

# --------------------------------- modèles des types reçus par le LLM -----------------------------------------

class AnalyseHumeurOutput(BaseModel):
    emotion_actuelle: str
    niveau_stress: float
    envie_interagir: float
    confiance: float

class TypeEvenement(str, Enum):
    RENDEZ_VOUS = "rendez-vous"
    BIEN_ETRE = "bien-etre"
    DEADLINE = "deadline"
    MALADIE = "maladie"
    EXAMEN = "examen"

class EventDetectorOutput(BaseModel):
    type: Optional[TypeEvenement]
    event: Optional[str]
    date: Optional[datetime]
    importance: Optional[float] 
    confidence: Optional[float]
    
class ResumeMCTOutput(BaseModel):
    Sujet: str
    intention: str
    Evenements_Mentionnes: str
    Resume_Reponse: str
    Entites_Mentionnees: str
    language: str
    tags: list[str]

class ResumeMLTOutput(BaseModel):
    date: datetime
    nombre_echanges: int
    humeur_generale: str
    themes_abordes: str
    centres_interets: str
    evenements_mentionnes: str
    resume_conversation: str 

# -------------------------- modèles des types en BD ----------------------------------------------
@dataclass
class Profil:
    """Profil utilisateur — Représente un utilisateur du système.
    
    Stocke les informations personnelles de l'utilisateur ainsi que des références
    à ses préférences et sujets sensibles. Ce modèle est la base pour personnaliser
    toutes les interactions avec le compagnon virtuel.
    
    Attributs:
        id (int): Identifiant unique du profil en BD
        nom (str): Nom de famille de l'utilisateur
        prenom (str): Prénom de l'utilisateur
        date_naissance (datetime): Date de naissance (format: YYYY-MM-DD)
        date_creation (datetime): Timestamp de création du profil
    """
    id: int = None
    nom: str = None
    prenom: str = None
    date_naissance: datetime = None
    date_creation: datetime = None

@dataclass
class Conversation:
    """Conversation entre un utilisateur et un compagnon virtuel.
    
    Représente une session de dialogue entre un profil et un compagnon. Chaque
    conversation a un sujet et une date de création, et contient multiple messages.
    
    Attributs:
        id (int): Identifiant unique de la conversation en BD
        id_user (int): Identifiant du profil utilisateur
        id_companion (int): Identifiant du compagnon virtuel
        sujet (str): Titre/sujet de la conversation
        date_creation (datetime): Timestamp de création de la conversation
    """
    id: int = None
    id_user: int = None
    id_companion: int = None
    sujet: str = None
    date_creation: datetime = None

@dataclass
class Message:
    """Message dans une conversation — Représente un échange utilisateur-assistant.
    
    Stocke une paire message/réponse d'une conversation. Chaque message lié à une
    conversation spécifique et daté pour la chronologie.
    
    Attributs:
        id (int): Identifiant unique du message en BD
        id_conversation (int): Identifiant de la conversation contenant ce message
        msg_user (str): Contenu du message envoyé par l'utilisateur
        reponse_assistant (str): Contenu de la réponse généré par le compagnon
        date_creation (datetime): Timestamp de création du message
    """
    id: int = None
    id_conversation: int = None
    msg_user: str = None
    reponse_assistant: str = None
    date_creation: datetime = None

@dataclass
class Evenement:
    """Événement détecté lors d'une conversation — Permet la proactivité du compagnon.
    
    Enregistre les événements détectés dans les conversations 
    (ex: anniversaire mentionné, problème de santé, changement professionnel, etc.).
    Ces événements peuvent déclencher des actions proactives du compagnon, à l'heure définie dans timing
    
    Attributs:
        id_profil (int): Identifiant du profil concerné par l'événement
        description (str): Description détaillée de l'événement
        timing (datetime): Moment/date de l'événement indiqué
        timing_notification (str): "avant" ou "après" en fonction de si la notification doit être envoyée avant ou après le timing de l'événement.
        statut (str): État de l'événement ('Planifié', 'Déclenché')
        importance (float): Score d'importance entre 0.0 (négligeable) et 1.0 (critique).
                           Calculé par le LLM à la détection.
                           Seuil de déclenchement par défaut : 0.3
    """
    id: int = None
    id_profil : int = None
    type_evenement: str = None
    description: str = None
    timing: datetime = None
    timing_notification : str = None # la notification de l'événement doit se faire avant ou après le timing de l'événement ?
    statut: bool = False
    importance: float = 0.5

@dataclass
class MLT:
    """Mémoire Long Terme — Résumés et faits persistants sur l'utilisateur.
    
    Stocke des résumés et informations dérables extraites des conversations.
    Contrairement à la MCT, la MLT est destinée à persister dans le temps et
    capturer les éléments importants sur le profil utilisateur.
    
    Attributs:
        id_profil (int): Identifiant du profil associé
        date_creation (datetime): Timestamp de création de l'entrée
        text (str): Contenu texte du résumé ou fait persistant
    """
    id_profil : int
    date_creation: datetime
    nombre_echanges: int
    humeur_generale: str
    themes_abordes: str
    centres_interets: str
    evenements_mentionnes: str
    resume_conversation: str
    
@dataclass
class MCT:
    """Mémoire Court Terme — Contexte récent de conversation.
    
    Stocke les N derniers échanges avec l'utilisateur pour maintenir le contexte
    lors de la génération de réponses. La MCT est régulièrement nettoyée pour
    garder seulement les messages pertinents les plus récents.
    
    Attributs:
        id (int): Identifiant unique de l'entrée MCT en BD
        id_profil (int): Identifiant du profil associé
        date_creation (datetime): Timestamp de création de l'entrée
        message (str): Contenu de l'échange (message utilisateur | réponse assistant)
    """
    id_profil: int = None
    date_creation : datetime = None
    sujet: str = None
    intention: str = None
    evenements_mentionnes : str = None
    langage : str = None
    entites_mentionnees : str = None
    resume_reponse : str = None
    tags : str = None

@dataclass
class Preference:
    """Préférence utilisateur — Représente un centre d'intérêt ou sujet apprécié.
    
    Enregistre les sujets qui intéressent l'utilisateur avec un niveau (0.0 à 1.0).
    Utilisé pour personnaliser les conversations et initier des sujets pertinents.
    
    Attributs:
        id (int): Identifiant unique de la préférence en BD
        id_profil (int): Identifiant du profil auquel appartient cette préférence
        sujet (str): Nom du sujet (ex: "Science-fiction", "Programmation")
        niveau (float): Niveau d'intérêt de 0.0 (minimal) à 1.0 (maximal)
    """
    id: int = None
    id_profil : int = None
    sujet : str = None
    niveau : float = None
   
@dataclass 
class SujetSensible:
    """Sujet sensible — Représente un thème à traiter avec prudence.
    
    Enregistre les sujets qui requirent une gestion délicate selon le profil
    (ex: santé mentale, finances, relations familiales). Chaque sujet a un niveau
    de sensibilité qui détermine comment le compagnon doit l'aborder.
    
    Attributs:
        id (int): Identifiant unique du sujet sensible en BD
        id_profil (int): Identifiant du profil pour lequel c'est sensible
        sujet (str): Nom du sujet sensible
        niveau (float): Niveau de sensibilité de 0.0 (minimal) à 1.0 (maximal)
                       Détermine la consigne: <0.4=prudence, 0.4-0.7=délicatesse, >=0.7=éviter
    """
    id: int = None
    id_profil : int = None
    sujet :str = None
    niveau : float = None

@dataclass
class CompagnonVirtuel:
    """Compagnon virtuel — Configuration et profil comportemental du bot IA.
    
    Représente une instance du compagnon avec ses paramètres de personnalité et
    configuration. Permet de personnaliser le comportement et le style du compagnon
    pour chaque interaction.
    
    Attributs:
        id (int): Identifiant unique du compagnon en BD
        modele (str): Nom du modèle LLM utilisé (ex: "mistral", "gpt-4")
        profil (dict): Dictionnaire contenant les traits de personnalité:
                      - empathie (float): 0.0 à 1.0
                      - humour (float): 0.0 à 1.0  
                      - professionalisme (float): 0.0 à 1.0
                      - patience (float): 0.0 à 1.0
    """
    id : int = None
    modele: str = "mistral"
    profil : dict[str,str] = None
    
    

#------------------------------------------ Classe abstraite ----------------------------------------------------
class BaseLLMClient(ABC):
    """
    Interface commune pour tous les fournisseurs LLM.
    Tout le reste du code n'utilise que cette interface.
    """
    @abstractmethod
    def send(
        self,
        messages: list[LLMMessage],
        model: str="gemma4:31b-cloud",
        system_prompt: str | None = None,
        output_model: BaseModel | None = None,
        options: dict | None = None,
        keep_alive: float | None = None
    ) -> BaseModel | str:
        """
        Envoie une liste de messages et retourne une réponse normalisée.
        C'est la seule méthode que le reste du projet appelle.
        """
        ...
