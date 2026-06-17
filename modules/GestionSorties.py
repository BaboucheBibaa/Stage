import queue
from dataclasses import dataclass
from typing import Literal


@dataclass
class MessageAffichage:
    texte: str
    source: Literal["dialogue", "proactif"] = "dialogue"


class GestionSorties:
    """
    File d'attente pour l'affichage.

    Tous les modules y déposent leurs messages via enqueue().
    uniquement boucle_affichage dans main.py les lit via un get()

    L'arrêt se fait en appelant stop(), qui enfile un None
    que la boucle d'affichage interprète comme un signal de fin.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[MessageAffichage | None] = queue.Queue()

    def enqueue(self,texte: str,source: Literal["dialogue", "proactif"] = "dialogue") -> None:
        """
        Dépose un message dans la file.

        Args:
            texte:  Contenu du message à afficher.
            source: Origine du message ('dialogue' ou 'proactif').
        """
        self._queue.put(MessageAffichage(texte=texte, source=source))

    def get(self) -> MessageAffichage | None:
        """
        Récupère le prochain message. Bloque jusqu'à ce qu'un message
        soit disponible.

        Returns:
            MessageAffichage suivant, ou None si stop() a été appelé.
        """
        return self._queue.get()

    def stop(self) -> None:
        """
        Enfile une sentinelle None pour signaler l'arrêt à la boucle
        d'affichage.
        """
        self._queue.put(None)