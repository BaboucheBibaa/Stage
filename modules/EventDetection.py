from LLM.LLMBase import BaseLLMClient
from data.dataclasses import DonneesEvenement
from data.modeles import Evenement
import json
from pathlib import Path
from datetime import datetime, timedelta

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
            message_user=message_user,
            datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        print("prompt : \n" + str(prompt))
        contenu_brut = self.llm.send_simple(prompt)
        print("Fonction detecter()\n\n")
        try:
            evenements : dict[str,list[dict[str,str]]] = json.loads(contenu_brut)
        except json.JSONDecodeError:
            print("Erreur au niveau du JSON converti dans la détection d'événements")
            return
        liste_events = evenements.get("evenements", [])
        for evt in liste_events:
            # timing_evenement = heure réelle de l'événement
            timing_evenement = datetime.strptime(evt["timing_evenement"], "%Y-%m-%d %H:%M:%S")
            # importance : score fourni par le LLM, borné entre 0.0 et 1.0
            importance_brute = evt.get("importance", 0.5)
            try:
                importance = max(0.0, min(1.0, float(importance_brute)))
            except (ValueError, TypeError):
                importance = 0.5
            self.evt_repo.create(Evenement(
                id_profil=self.id_profil,
                description=evt['contexte'],
                timing=timing_evenement,
                statut='Planifié',
                type_evenement=evt['type'],
                importance=importance,
            ))