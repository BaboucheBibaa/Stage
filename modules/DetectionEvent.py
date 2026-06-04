"""
DetectionEvent — Extrait les événements d'un message utilisateur
et les stocke en BD avec le timing de NOTIFICATION (pas le timing de l'événement).
"""

from LLM.LLMBase import BaseLLMClient
from data.dataclasses import DonneesEvenement
from data.modeles import Evenement
from modules.NotificationTiming import calculer_timings_notification
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
        print("Fonction detecter()\nParamètre entrée : " + message_user+ "\n\n\n")
        prompt = _charger("event_detector.txt").format(
            message_user=message_user,
            datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        contenu_brut = self.llm.send_simple(prompt).strip()
        print("Fonction detecter()\n Affichage du contenu brut : "+ str(contenu_brut) + "\n\n\n")
        try:
            evenements : dict[dict[str,str]] = json.loads(contenu_brut)
        except json.JSONDecodeError:
            print("Erreur au niveau du JSON converti dans la détection d'événements")
            return
        for evt in evenements.get("evenements", []):
            try:
                # timing_evenement = heure réelle de l'événement (ex: 15h pour un RDV à 15h)
                timing_evenement = datetime.strptime(evt["timing"], "%Y-%m-%d %H:%M:%S")
                type_evt = evt.get("type", "rendez-vous")
            except (KeyError, ValueError):
                continue

            # Calcul des timings de notification selon le type
            timings_notif = calculer_timings_notification(timing_evenement, type_evt)

            if not timings_notif:
                # Tous les timings sont déjà passés : événement ignoré
                continue

            # On crée un enregistrement en BD par timing de notification
            for timing_notif in timings_notif:
                self.evt_repo.create(Evenement(
                    id_profil=self.id_profil,
                    description=evt.get("contexte", ""),
                    timing=timing_notif,      # ← timing de notification, pas de l'événement
                    statut="Planifié",
                ))
