from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class TypeEvenement(str, Enum):
    RENDEZ_VOUS = "rendez-vous"
    BIEN_ETRE = "bien-être"
    DEADLINE = "deadline"
    MALADIE = "maladie"
    EXAMEN = "examen"

class EventDetectorOutput(BaseModel):
    Type: TypeEvenement = None
    Contexte: str = None
    Timing_Evenement: datetime= None
    Importance: float = None
    Confiance: float = None
    
class ResumeMCTOutput(BaseModel):
    Sujet : str = None
    Intention : str = None
    Evenements_Mentionnes : list[str] = None
    Resume_Reponse : list[str] = None
    Entites_Mentionnees : list[str] = None
    Langue : str = None
    Tags : list[str] = None

class ResumeMLTOutput(BaseModel):
    Date : datetime = None
    Nombre_Echanges : int = None
    Humeur_Generale : str = None
    Themes_Du_Jour : list[str] = None
    Taches_Et_Demandes : list[dict[str,str]] = None
    Sujet_D_Interet : list[str] = None
    Evenements_Mentionnes : list[str] = None
    Points_attention : list[str] = None
    Resume_Journee : str = None


class GeneralOutput(BaseModel):
    Message: str = None