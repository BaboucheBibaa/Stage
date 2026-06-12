from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional

class TypeEvenement(str, Enum):
    RENDEZ_VOUS = "rendez-vous"
    BIEN_ETRE = "bien-etre"
    DEADLINE = "deadline"
    MALADIE = "maladie"
    EXAMEN = "examen"

class EventDetectorOutput(BaseModel):
    Type: TypeEvenement
    Evenement: str
    Timing_Evenement: Optional[datetime] 
    Importance: float 
    Confiance: float
    
class ResumeMCTOutput(BaseModel):
    Sujet : str 
    Intention : str 
    Evenements_Mentionnes : list[str] 
    Resume_Reponse : list[str] 
    Entites_Mentionnees : list[str] 
    Langue : str 
    Tags : list[str] 

class ResumeMLTOutput(BaseModel):
    Date : datetime 
    Nombre_Echanges : int 
    Humeur_Generale : str 
    Themes_Du_Jour : list[str] 
    Taches_Et_Demandes : list[dict[str,str]] 
    Sujet_D_Interet : list[str] 
    Evenements_Mentionnes : list[str] 
    Points_attention : list[str] 
    Resume_Journee : str 


class GeneralOutput(BaseModel):
    Message: str 