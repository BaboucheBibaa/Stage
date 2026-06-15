from projectTypes import BaseLLMClient, Evenement, EventDetectorOutput, LLMMessage,TypeEvenement
from data.dataclasses import DonneesEvenement
from pathlib import Path
from datetime import datetime
from datetime import timedelta
# Chaque type peut produire PLUSIEURS notifications (liste de timedelta).
_REGLES: dict[str, list[timedelta]] = {
    TypeEvenement.RENDEZ_VOUS: [
        timedelta(hours=-1),        # 1 heure avant
        timedelta(hours=1)         # 1 heure après ("comment ça s'est passé ?")
    ],
    TypeEvenement.EXAMEN: [
        timedelta(hours=-13),       # veille au soir
        timedelta(hours=-1),        # 1 heure avant le jour J
        timedelta(hours=2),        # 1 heure après ("comment s'est passé l'exam ?")
    ],
    TypeEvenement.DEADLINE: [
        timedelta(hours=-24),       # 24 heures avant
        timedelta(hours=-2),        # 2 heures avant
    ],
    TypeEvenement.MALADIE: [
        timedelta(hours=2),         # 2h après la mention
    ],
    TypeEvenement.BIEN_ETRE: [
        timedelta(hours=1),         # 1h après la mention
    ],
}

# Délai par défaut si le type est inconnu
_DEFAUT = [timedelta(hours=-1)]

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
        llm_reponse = self.llm.send(
            messages=[LLMMessage(role="user", contenu=message_user)], 
            system_prompt=prompt,
            json_schema=EventDetectorOutput.model_json_schema()
        )
        #model structuré de la réponse du LLM
        contenu_brut = EventDetectorOutput.model_validate_json(llm_reponse.contenu)
        
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
        importance = contenu_brut.Importance or 0.5
        try:
            importance = max(0.0, min(1.0, float(importance)))
        except (ValueError, TypeError):
            importance = 0.5
        for timing in _REGLES.get(contenu_brut.Type.value, _DEFAUT):
            notification = ""
            if timing.total_seconds() < 0:
                notification = "avant"
            else:
                notification = "après"
            self.evt_repo.create(Evenement(
                id_profil=self.id_profil,
                description=contenu_brut.Evenement,
                timing=timing_evenement,
                statut='Planifié',
                timing_notification = notification,
                type_evenement=contenu_brut.Type.value,
                importance=importance,
            ))