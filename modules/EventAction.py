from datetime import datetime, timedelta
from pathlib import Path
from data.bd import Database
from projectTypes import BaseLLMClient,Evenement, TypeEvenement
from data.dataclasses import (
    DonneesEvenement,
    DonneesProfil,
    DonneesPreferences,
    DonneesCompagnon,
    DonneesMCT,
    DonneesMLT,
)
from LLM.ollama_config import LLMMessage

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


def _charger_prompt(nom: str) -> str:
    """Charge un fichier texte depuis le dossier prompts/."""
    return (_PROMPTS / nom).read_text(encoding="utf-8")

class EventAction:
    def __init__(self,llm: BaseLLMClient,id_profil: int,intervalle_minutes: int = 5,fenetre_minutes: int = 30):
        self._db = Database()
        self.llm = llm
        self.id_profil = id_profil
        self.intervalle_minutes = intervalle_minutes
        self.fenetre_minutes = fenetre_minutes

        self._data_evt = DonneesEvenement(db=self._db)

    def verifier_et_declencher(self) -> list[str]:
        """
        Récupère les événements futurs et déclenche ceux qui tombent
        dans la fenêtre [maintenant - 1min, maintenant + fenetre_minutes].

        Returns:
            list[str]: Messages proactifs générés lors de ce cycle.
                       Liste vide si aucun événement à déclencher.
        """
        maintenant  = datetime.now()
        borne_basse = maintenant - timedelta(minutes=1)
        limite      = maintenant + timedelta(minutes=self.fenetre_minutes)

        evenements = self._data_evt.getFuturs(self.id_profil)
        messages: list[str] = []
        for evt in evenements:
            timings = self.calculer_timings_notification(evt.timing, evt.type_evenement)
            for timing in timings:
                if borne_basse <= timing <= limite:
                    message = self.__declencher(evt)
                    messages.append(message)
        return messages

    def __declencher(self, evt: Evenement) -> str:
        """
        Génère un message proactif pour un événement donné et met à jour
        son statut en base de données.

        Args:
            evt: L'événement à traiter.

        Returns:
            str: Le message proactif généré par le LLM.
        """
        contexte = self._construire_contexte(evt)
        system_prompt   = _charger_prompt("proactive/proactive_system.txt").format(**contexte)
        user_prompt = _charger_prompt("proactive/proactive_user.txt").format(**contexte)
        message_proactif = self.llm.send(
            messages= [LLMMessage(role="user", contenu=user_prompt)],
            system_prompt=system_prompt,
            
        )
        self._data_evt.updateEvent(evt.id, "Déclenché")
        return message_proactif
    
    def calculer_timings_notification(self,timing_evenement: datetime,type_evenement: str,) -> list[datetime]:
        """
        Calcule la liste des datetimes auxquelles le compagnon doit envoyer
        un message proactif pour cet événement.

        Args:
            timing_evenement: Heure réelle de l'événement (ex: 15h00 pour un RDV à 15h).
            type_evenement:   Type détecté par le LLM ('rendez-vous', 'examen', etc.).

        Returns:
            list[datetime]: Datetimes de notification dans le futur (> maintenant + 1min).
        """
        regles    = _REGLES.get(type_evenement, _DEFAUT)
        maintenant = datetime.now()
        marge     = timedelta(minutes=1)

        timings = []
        for delta in regles:
            t = timing_evenement + delta
            if t > maintenant + marge:
                timings.append(t)

        return timings

    def _construire_contexte(self, evt: Evenement) -> dict:
        """
        Rassemble toutes les informations nécessaires au prompt proactif.

        Args:
            evt: L'événement pour lequel construire le contexte.

        Returns:
            dict: Dictionnaire de variables à injecter dans le template de prompt.
        """
        
        data_mct = DonneesMCT(db=self._db)
        data_mlt = DonneesMLT(db=self._db)
        data_profil = DonneesProfil(db=self._db)
        data_prefs = DonneesPreferences(db=self._db)
        data_compagnon = DonneesCompagnon(db=self._db)

        profil    = data_profil.getProfil(self.id_profil)
        prefs     = data_prefs.getPreferences(self.id_profil)
        mct_list  = data_mct.getToday(self.id_profil)
        mlt       = data_mlt.getRecente(self.id_profil)
        compagnon = data_compagnon.getCompagnon(1)

        # Formatage des préférences
        if prefs:
            lignes_prefs = "\n".join(f"  - {p.sujet} (intérêt : {p.niveau:.0%})" for p in prefs)
        else:
            lignes_prefs = "  Aucune préférence enregistrée."

        # Formatage de la MCT du jour (ordre chronologique)
        if mct_list:
            lignes_mct = "\n".join(f"  {mct.message}" for mct in reversed(mct_list))
        else:
            lignes_mct = "  Aucun échange aujourd'hui pour l'instant."

        # Calcul de l'âge
        age = 0
        if profil and profil.date_naissance:
            today = datetime.now()
            dn    = profil.date_naissance
            age   = today.year - dn.year
            if (today.month, today.day) < (dn.month, dn.day):
                age -= 1

        # Formatage du délai restant avant l'événement
        delta             = evt.timing - datetime.now()
        minutes_restantes = max(0, int(delta.total_seconds() / 60))

        if minutes_restantes == 0:
            delai_str = "maintenant"
        elif minutes_restantes < 60:
            delai_str = f"dans {minutes_restantes} minute(s)"
        else:
            heures  = minutes_restantes // 60
            minutes = minutes_restantes % 60
            if minutes > 0:
                delai_str = f"dans environ {heures}h{minutes:02d}"
            else:
                delai_str = f"dans environ {heures} heure(s)"

        return {
            "nom_compagnon"       : compagnon.modele if compagnon else "Compagnon",
            "prenom"              : profil.prenom if profil else "l'utilisateur",
            "nom"                 : profil.nom if profil else "",
            "age"                 : age,
            "description_evenement": evt.description or "événement sans description",
            "delai_evenement"     : delai_str,
            "lignes_preferences"  : lignes_prefs,
            "lignes_mct"          : lignes_mct,
            "contenu_mlt"         : mlt.text if mlt else "Aucune mémoire long terme disponible.",
        }