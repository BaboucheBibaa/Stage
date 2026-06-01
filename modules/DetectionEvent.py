# modules/EventDetector.py
from LLM.LLMBase import BaseLLMClient
from data.dataclasses import DonneesEvenement, Evenement
from datetime import datetime
import json
from pathlib import Path

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
        raw = self.llm.send_simple(prompt).strip()
        print("Résultat de la détection d'événements: ")
        print(raw)
        try:
            evenements = json.loads(raw)
        except json.JSONDecodeError:
            return
        for evt in evenements:
            self.evt_repo.create(Evenement(
                id_profil=self.id_profil,
                description=evt["description"],
                timing=datetime.strptime(evt["timing"], "%Y-%m-%d %H:%M:%S"),
                statut=False,
            ))