"""Déclenche une action proactive du compagnon virtuel"""

import threading

from LLM.LLMBase import BaseLLMClient
from .EventAction import EventAction
class ProactiveScheduler:
    """
    Thread de fond qui se déclenche toutes les intervalle_minutes.

    Attributes:
        llm (BaseLLMClient): Client LLM partagé avec le DialogueModule.
        id_profil (int): Identifiant du profil surveillé.
        intervalle_minutes (int): Fréquence de vérification en minutes.
    """

    def __init__(self,llm: BaseLLMClient,id_profil: int,intervalle_minutes: int = 5):
        self.llm = llm
        self.id_profil = id_profil
        self.intervalle_minutes = intervalle_minutes
        #codé en dur ici, voir pour le mettre dans le fichier de config ?
        self.fenetre_minutes = 30
        self.event_actions = EventAction(self.llm, self.id_profil, self.intervalle_minutes, self.fenetre_minutes)

        # contrôle du signal d'arrêt du thread
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            #ce thread exécute la fonction boucle en parallèle de l'exécution du main.
            target=self._boucle,
            name="ProactiveScheduler",
            daemon=True,
        )

    def start(self) -> None:
        """Démarre le thread."""
        self._thread.start()

    def stop(self) -> None:
        """Arrête le thread (attend qu'il finisse le cycle en cours)."""
        self._stop_event.set()
        self._thread.join(timeout=5)

    def _boucle(self) -> None:
        """
        Boucle infinie du thread.
        """
        #tant que le thread n'est pas fini (finir = déclencher stop() afin de mettre le flag interne à true, donc fini)
        while not self._stop_event.is_set():
            self.event_actions.verifier_et_declencher()
            arret_demande = self._stop_event.wait(timeout=self.intervalle_minutes * 60)
            if arret_demande:
                break