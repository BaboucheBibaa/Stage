"""
EventAction — Détecte si un événement planifié arrive à son timing
et déclenche l'action proactive correspondante.
"""

from data.dataclasses import DonneesEvenement
from data.modeles import Evenement
from datetime import datetime


class EventAction:
    def __init__(self, id_profil: int):
        data_event = DonneesEvenement()
        self.evenements_futurs = data_event.getFuturs(id_profil=id_profil)

    def detecter_timing(self) -> list[Evenement]:
        """
        Retourne les événements dont le timing correspond à la minute courante.
        """
        maintenant = datetime.now().replace(second=0, microsecond=0)
        declenchables = []

        for evt in self.evenements_futurs:
            if evt.timing is None:
                continue
            # Comparer à la minute près
            timing_arrondi = evt.timing.replace(second=0, microsecond=0)
            if timing_arrondi == maintenant:
                declenchables.append(evt)

        return declenchables