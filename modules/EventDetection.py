from LLM.LLMBase import BaseLLMClient
from data.dataclasses import DonneesEvenement
from data.modeles import Evenement
from pathlib import Path
from datetime import datetime
from data.output_models import EventDetectorOutput

_PROMPTS = Path(__file__).parent / "../" "prompts"


def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")

class DetectionEvent:
    def __init__(self, llm: BaseLLMClient, evt_repo: DonneesEvenement, id_profil: int):
        self.llm = llm
        self.evt_repo = evt_repo
        self.id_profil = id_profil

    def detecter(self, message_user: str) -> None:
        prompt = _charger("event_detector.txt").format(
            datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        llm_reponse = self.llm.send_simple(user_text=message_user, system_prompt=prompt, json_schema=EventDetectorOutput.model_json_schema())
        print("llm reponse : "+str(llm_reponse))
        #model structuré de la réponse du LLM
        contenu_brut = EventDetectorOutput.model_validate_json(llm_reponse)
        print(contenu_brut)
        
        if contenu_brut.Timing_Evenement is None:
            return
        
        confiance = float(contenu_brut.Confiance or 0.0)
        if confiance < 0.6:
            return
        
        importance = max(0.0, min(1.0, float(contenu_brut.Importance or 0.5)))
        if importance < 0.3:
            return

        # timing_evenement = heure réelle de l'événement
        timing_evenement = contenu_brut.Timing_Evenement
        # importance : score fourni par le LLM, borné entre 0.0 et 1.0
        importance_brute = contenu_brut.Importance or 0.5
        try:
            importance = max(0.0, min(1.0, float(importance_brute)))
        except (ValueError, TypeError):
            importance = 0.5
        self.evt_repo.create(Evenement(
            id_profil=self.id_profil,
            description=contenu_brut.Evenement,
            timing=timing_evenement,
            statut='Planifié',
            type_evenement=contenu_brut.Type.value,
            importance=importance,
        ))