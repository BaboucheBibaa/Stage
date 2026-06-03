"""
notification_timing.py — Calcul du moment de notification proactive.

Responsabilité unique : étant donné un événement et son type,
calculer QUAND le compagnon doit intervenir (pas à l'heure de l'événement lui-même).

Intégration : appelé dans DetectionEvent.detecter() au moment où l'événement
est créé en BD. Le timing stocké en BD est donc déjà le timing de notification,
pas le timing de l'événement.
"""

from datetime import datetime, timedelta
from enum import Enum


class TypeEvenement(str, Enum):
    RENDEZ_VOUS = "rendez-vous"
    EXAMEN      = "examen"
    DEADLINE    = "deadline"
    MALADIE     = "maladie"
    BIEN_ETRE   = "bien-etre"


# ── Règles de notification ────────────────────────────────────────────────────
#
# Chaque type peut produire PLUSIEURS notifications (liste de timedelta).
# Un timedelta négatif = "avant l'événement".
# timedelta(0)         = "au moment de l'événement" (pour maladie/bien-être).
#
# Exemples :
#   rendez-vous à 15h00 → notification à 14h00  (1h avant)
#   examen à 09h00      → notifications à 20h00 la veille ET à 08h00 le matin
#   deadline à 23h59    → notification à 23h59 la veille (24h avant)

_REGLES: dict[str, list[timedelta]] = {
    TypeEvenement.RENDEZ_VOUS: [
        timedelta(hours=-1),        # 1 heure avant
    ],
    TypeEvenement.EXAMEN: [
        timedelta(hours=-13),       # ~veille au soir (si exam à 9h → 20h la veille)
        timedelta(hours=-1),        # 1 heure avant le jour J
    ],
    TypeEvenement.DEADLINE: [
        timedelta(hours=-24),       # 24 heures avant
        timedelta(hours=-2),        # 2 heures avant (rappel urgent)
    ],
    TypeEvenement.MALADIE: [
        timedelta(hours=2),         # 2h après la mention (prendre des nouvelles)
    ],
    TypeEvenement.BIEN_ETRE: [
        timedelta(hours=1),         # 1h après la mention
    ],
}

# Délai par défaut si le type est inconnu
_DEFAUT = [timedelta(hours=-1)]

def calculer_timings_notification(
    timing_evenement: datetime,
    type_evenement: str,
) -> list[datetime]:
    """
    Calcule la liste des datetimes auxquelles le compagnon doit envoyer
    un message proactif pour cet événement.

    Args:
        timing_evenement: Heure réelle de l'événement (ex: 15h00 pour un RDV à 15h).
        type_evenement:   Type détecté par le LLM ('rendez-vous', 'examen', etc.).

    Returns:
        Liste de datetimes de notification, filtrée pour ne garder que les moments dans le futur (> maintenant + 1 minute de marge).
    """
    regles = _REGLES.get(type_evenement, _DEFAUT)
    maintenant = datetime.now()
    marge = timedelta(minutes=1)  # ignorer les notifications dans moins d'1 minute

    timings = []
    for delta in regles:
        t = timing_evenement + delta
        if t > maintenant + marge:
            timings.append(t)

    return timings

def timing_principal(
    timing_evenement: datetime,
    type_evenement: str,
) -> datetime | None:
    """
    Raccourci : retourne uniquement le PREMIER timing de notification
    (le plus proche dans le temps).
    Retourne None si tous les timings sont déjà passés.

    Utilisé par DetectionEvent quand on ne veut stocker qu'un seul événement en BD.
    """
    timings = calculer_timings_notification(timing_evenement, type_evenement)
    return timings[0] if timings else None