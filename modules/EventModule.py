from datetime import datetime, timedelta
from pathlib import Path

from data.bd import Database
from data.dataclasses import (
    DonneesEvenement,
    DonneesMCT,
    DonneesMLT,
    DonneesPreferences,
    DonneesProfil,
)
from AI.ollama_config import LLMMessage
from data.projectTypes import (
    MCT,
    MLT,
    BaseLLMClient,
    Evenement,
    EventDetectorOutput,
    TypeEvenement,
)
import yaml

# Chaque type peut produire PLUSIEURS notifications (liste de timedelta).
_REGLES: dict[str, list[timedelta]] = {
    TypeEvenement.RENDEZ_VOUS: [
        timedelta(hours=-1),  # 1 heure avant
        timedelta(hours=1),  # 1 heure après ("comment ça s'est passé ?")
    ],
    TypeEvenement.EXAMEN: [
        timedelta(hours=-13),  # veille au soir
        timedelta(hours=-1),  # 1 heure avant le jour J
        timedelta(hours=2),  # 1 heure après ("comment s'est passé l'exam ?")
    ],
    TypeEvenement.DEADLINE: [
        timedelta(hours=-24),  # 24 heures avant
        timedelta(hours=-2),  # 2 heures avant
    ],
    TypeEvenement.MALADIE: [
        timedelta(hours=2),  # 2h après la mention
    ],
    TypeEvenement.BIEN_ETRE: [
        timedelta(hours=1),  # 1h après la mention
    ],
}

# Délai par défaut si le type est inconnu
_DEFAUT = [timedelta(hours=-1)]

_PROMPTS = Path(__file__).parent / "../prompts"


def _charger_prompt(nom: str) -> str:
    """Charge un fichier texte depuis le dossier prompts/."""
    return (_PROMPTS / nom).read_text(encoding="utf-8")


class EventModule:
    def __init__(
        self,
        llm: BaseLLMClient,
        id_profil: int,
        evt_repo: DonneesEvenement,
        intervalle_minutes: int = 5,
        fenetre_minutes: int = 30,
    ):
        self._db = Database()
        self.llm = llm
        self.id_profil = id_profil
        self.intervalle_minutes = intervalle_minutes
        self.fenetre_minutes = fenetre_minutes
        self.evt_repo = evt_repo
        self._data_evt = DonneesEvenement(db=self._db)

    def detecter(self, message_user: str) -> None:
        prompt = _charger_prompt("event_detector.txt").format(
            datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        llm_reponse: EventDetectorOutput = self.llm.send(
            messages=[LLMMessage(role="user", contenu=message_user)],
            system_prompt=prompt,
            output_model=EventDetectorOutput,
        )
        # model structuré de la réponse du LLM
        if llm_reponse.importance is None:
            return

        confiance = float(llm_reponse.confidence or 0.0)
        if confiance < 0.6:
            return

        importance = max(0.0, min(1.0, float(llm_reponse.importance or 0.5)))
        if importance < 0.3:
            return

        # timing_evenement = heure réelle de l'événement
        timing_evenement = llm_reponse.date
        # importance : score fourni par le LLM, borné entre 0.0 et 1.0
        importance = llm_reponse.importance or 0.5
        try:
            importance = max(0.0, min(1.0, float(importance)))
        except (ValueError, TypeError):
            importance = 0.5
        for timing in _REGLES.get(llm_reponse.type.value, _DEFAUT):
            notification = ""
            if timing.total_seconds() < 0:
                notification = "avant"
            else:
                notification = "après"
            evenement_detecte = Evenement(
                id_profil=self.id_profil,
                description=llm_reponse.event,
                timing=timing_evenement,
                statut="Planifié",
                timing_notification=notification,
                type_evenement=llm_reponse.type.value,
                importance=importance,
            )
            self.evt_repo.create(evenement_detecte)

    def verifier_et_declencher(self) -> list[str]:
        """
        Déclenche les messages proactifs dont l'heure de notification
        se trouve dans la fenêtre de surveillance.
        """

        evenements = self._data_evt.getFuturs(self.id_profil)
        messages = []
        for evt in evenements:
            regles = _REGLES.get(evt.type_evenement, _DEFAUT)

            for delta in regles:
                # On ne garde que les notifications correspondant
                # au type demandé
                maintenant = datetime.now()
                if evt.timing_notification == "avant":
                    # si notre durée est positive mais que le timing de notification dit "avant", on ignore cette itération de la boucle.

                    if delta >= timedelta(0):
                        continue
                    # dans le cas où la notification doit être envoyée avant le timing, la borne basse correspond au timing de notification (timing + le delta déterminé) et la limite correspond au timing lui-même. On fait un intervalle, pas un timing précis de notification.
                    debut = evt.timing + delta
                    fin = evt.timing

                else:
                    # même logique ici
                    if delta <= timedelta(0):
                        continue
                    # dans le cas où la notification doit être envoyée après le timing, la borne basse doit être le timing lui-même, + une marge de 3 minutes, et la limite pour envoyer la notification correspond au timing de la notification (timing de l'évènement + le delta)
                    debut = evt.timing
                    fin = evt.timing + delta
                # La notification doit être envoyée maintenant
                if debut <= maintenant <= fin:
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
        promptPath = ""
        if evt.timing_notification == "avant":
            promptPath = "proactive/event_user_avant.txt"
        else:
            promptPath = "proactive/event_user_après.txt"

        contexte = self._construire_contexte(evt)
        system_prompt = _charger_prompt("proactive/event_system.txt").format(**contexte)
        user_prompt = _charger_prompt(promptPath).format(**contexte)
        message_proactif = self.llm.send(
            messages=[LLMMessage(role="user", contenu=user_prompt)],
            system_prompt=system_prompt,
        )
        self._data_evt.updateEvent(evt.id, "Déclenché")
        return message_proactif

    def calculer_timings_notification(
        self,
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
            list[datetime]: Datetimes de notification dans le futur (> maintenant + 1min).
        """
        regles = _REGLES.get(type_evenement, _DEFAUT)
        maintenant = datetime.now()
        marge = timedelta(minutes=1)

        timings = []
        for delta in regles:
            t = timing_evenement + delta
            if t > maintenant + marge:
                timings.append(t)

        return timings

    def format_mlt(self, mlt: MLT) -> str:
        return f"""
        Enregistrement de la mémoire long terme sur l'utilisateur:
        Date de création: {mlt.date_creation}
        Nombre de messages : {mlt.nombre_echanges}
        Humeur Générale : {mlt.humeur_generale}
        Centres d'intérêts : {mlt.centres_interets}
        Thèmes abordés : {mlt.themes_abordes}
        Résumé de la conversation : {mlt.resume_conversation}
        Évènements mentionnés : {mlt.evenements_mentionnes}
    """

    def format_mct(self, mct: MCT) -> str:
        return f"""
        Enregistrement de la conversation actuelle avec l'utilisateur:

        Date de création : {mct.date_creation}
        Sujet de la conversation : {mct.sujet}
        Intention de l'utilisateur : {mct.intention}
        Évènements mentionnés par l'utilisateur : {mct.evenements_mentionnes}
        Résumé de la réponse proposée par le compagnon virtuel : {mct.resume_reponse}
        Entités (Personnes, lieux, entreprises, etc...) mentionnées dans la conversation : {mct.entites_mentionnees}
        Langage de la conversation : {mct.langage}
        Tags (mots-clés) de la conversation: {mct.tags}
        """

    def _construire_contexte(self, evt: Evenement) -> dict:
        """
        Rassemble toutes les informations nécessaires au prompt proactif.

        Args:
            evt: L'événement pour lequel construire le contexte.

        Returns:
            dict: Dictionnaire de variables à injecter dans le template de prompt.
        """
        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        data_mct = DonneesMCT(db=self._db)
        data_mlt = DonneesMLT(db=self._db)
        data_profil = DonneesProfil(db=self._db)
        data_prefs = DonneesPreferences(db=self._db)

        profil = data_profil.getProfil(self.id_profil)
        prefs = data_prefs.getPreferences(self.id_profil)
        mct_list = data_mct.getToday(self.id_profil)
        mlt_liste = data_mlt.getMLT(self.id_profil)

        # Formatage des préférences
        if prefs:
            lignes_prefs = "\n".join(
                f"  - {p.sujet} (intérêt : {p.niveau:.0%})" for p in prefs
            )
        else:
            lignes_prefs = "  Aucune préférence enregistrée."

        # Formatage de la MCT du jour (ordre chronologique)
        if mct_list:
            lignes_mct = "\n".join(self.format_mct(mct) for mct in reversed(mct_list))
        else:
            lignes_mct = "  Aucun échange aujourd'hui pour l'instant."
        if mlt_liste:
            contenu_mlt = "\n".join(self.format_mct(mlt) for mlt in reversed(mlt_liste))
        else:
            contenu_mlt = "Aucune mémoire long terme sauvegardée pour l'instant"
        # Calcul de l'âge
        age = 0
        if profil and profil.date_naissance:
            today = datetime.now()
            dn = profil.date_naissance
            age = today.year - dn.year
            if (today.month, today.day) < (dn.month, dn.day):
                age -= 1

        # Formatage du délai restant avant l'événement
        delta = evt.timing - datetime.now()
        minutes_restantes = max(0, int(delta.total_seconds() / 60))

        if minutes_restantes == 0:
            delai_str = "maintenant"
        elif minutes_restantes < 60:
            delai_str = f"dans {minutes_restantes} minute(s)"
        else:
            heures = minutes_restantes // 60
            minutes = minutes_restantes % 60
            if minutes > 0:
                delai_str = f"dans environ {heures}h{minutes:02d}"
            else:
                delai_str = f"dans environ {heures} heure(s)"

        return {
            "nom_compagnon": config['companion']['name'],
            "prenom": profil.prenom if profil else "l'utilisateur",
            "nom": profil.nom if profil else "",
            "age": age,
            "description_evenement": evt.description or "événement sans description",
            "delai_evenement": delai_str,
            "lignes_preferences": lignes_prefs,
            "lignes_mct": lignes_mct,
            "contenu_mlt": contenu_mlt,
        }
