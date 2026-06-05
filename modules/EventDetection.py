from LLM.LLMBase import BaseLLMClient
from data.dataclasses import DonneesEvenement
from data.modeles import Evenement
import json
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

#types de déclencheurs proactifs événementiels possibles
class TypeEvenement(str, Enum):
    RENDEZ_VOUS = "rendez-vous"
    EXAMEN      = "examen"
    DEADLINE    = "deadline"
    MALADIE     = "maladie"
    BIEN_ETRE   = "bien-etre"

# Chaque type peut produire PLUSIEURS notifications (liste de timedelta).#

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
        timedelta(hours=2),         # 2h après la mention (prendre des nouvelles par ex)
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
            timings_notif = self.calculer_timings_notification(timing_evenement, type_evt)

            if not timings_notif:
                # Tous les timings sont déjà passés : événement ignoré
                continue

            # On crée un enregistrement en BD par timing de notification
            for timing_notif in timings_notif:
                self.evt_repo.create(Evenement(
                    id_profil=self.id_profil,
                    description=evt.get("contexte", ""),
                    timing=timing_notif,      #timing de notification, pas de l'événement
                    statut="Planifié",
                ))
    def calculer_timings_notification(self, timing_evenement: datetime, type_evenement: str,) -> list[datetime]:
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
            #timing de l'événement + délai de notification (négatif ou positif)
            t = timing_evenement + delta
            #on ignore les notifs qui doivent arriver dans 1 min
            if t > maintenant + marge:
                timings.append(t)
        #moments futurs
        return timings