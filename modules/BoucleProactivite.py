"""Déclenche une action proactive du compagnon virtuel"""

import threading

from projectTypes import BaseLLMClient
from .EventAction import EventAction
from .GestionSorties import GestionSorties
class DeclenchementProactivite:
    """
    Thread de fond qui se déclenche toutes les intervalle_minutes.

    Attributes:
        llm (BaseLLMClient): Client LLM partagé avec le DialogueModule.
        id_profil (int): Identifiant du profil surveillé.
        intervalle_minutes (int): Fréquence de vérification en minutes.
    """

    def __init__(self,llm: BaseLLMClient,id_profil: int,intervalle_minutes: int = 5, gestionnaire_sortie : GestionSorties = None):
        self.llm = llm
        self.id_profil = id_profil
        self.intervalle_minutes = intervalle_minutes
        self._output = gestionnaire_sortie

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
        #tant que le flag du thread est pas à true
        while not self._stop_event.is_set():
            #proactivité événementielle (vérification et déclenchement d'une action proactive si nécessaire)
            messages = self.event_actions.verifier_et_declencher()
            #on met en queue les événements proactifs déclenchés par la proactivité événementielle (ce sera très souvent un seul événement, mais on fait une liste au cas où plusieurs événements doivent se déclencher dans la même plage horaire)
            for message in messages:
                print(message)
                if self._output:
                    #proactif sert surtout pour de la clarté, idéalement si on peut afficher les messages proactifs différemment.
                    self._output.enqueue(message, source="proactif")
            #le thread tourne toutes les x minutes
            self._stop_event.wait(timeout=self.intervalle_minutes * 60)