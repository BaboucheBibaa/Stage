"""Déclenche une action proactive du compagnon virtuel"""

import threading
from datetime import datetime, timedelta
from pathlib import Path

from LLM.LLMBase import BaseLLMClient
from data.dataclasses import (
    DonneesEvenement,
    DonneesProfil,
    DonneesPreferences,
    DonneesSujetSensible,
    DonneesCompagnon,
    DonneesMCT,
    DonneesMLT,
)
from data.modeles import Evenement

_PROMPTS = Path(__file__).parent / "../" "prompts"

def _charger_prompt(nom: str) -> str:
    """Charge un fichier texte depuis le dossier prompts/."""
    return (_PROMPTS / nom).read_text(encoding="utf-8")


class ProactiveScheduler:
    """
    Thread de fond qui surveille les événements et déclenche des messages proactifs.

    Attributes:
        llm (BaseLLMClient): Client LLM partagé avec le DialogueModule.
        id_profil (int): Identifiant du profil surveillé.
        intervalle_minutes (int): Fréquence de vérification en minutes.
        fenetre_minutes (int): Événements dans [maintenant, maintenant + fenetre] sont déclenchés.
    """

    def __init__(
        self,
        llm: BaseLLMClient,
        id_profil: int,
        intervalle_minutes: int = 5,
        fenetre_minutes: int = 30,
    ):
        self.llm = llm
        self.id_profil = id_profil
        self.intervalle_minutes = intervalle_minutes
        self.fenetre_minutes = fenetre_minutes

        self._data_evt = DonneesEvenement()
        self._data_profil = DonneesProfil()
        self._data_prefs = DonneesPreferences()
        self._data_sujets = DonneesSujetSensible()
        self._data_compagnon = DonneesCompagnon()
        self._data_mct = DonneesMCT()
        self._data_mlt = DonneesMLT()

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
            self._verifier_et_declencher()
            arret_demande = self._stop_event.wait(timeout=self.intervalle_minutes * 60)
            if arret_demande:
                break

    def _verifier_et_declencher(self) -> None:
        """
        Récupère les événements futurs et déclenche ceux qui tombent
        dans la fenêtre [maintenant, maintenant + fenetre_minutes].
        """
        
        maintenant = datetime.now()
        #marge d'erreur d'une minute
        borne_basse = maintenant - timedelta(minutes=1)
        #marge d'erreur définie dans le constructeur
        limite = maintenant + timedelta(minutes=self.fenetre_minutes)

        evenements = self._data_evt.getFuturs(self.id_profil)


        for evt in evenements:
            if evt.timing is None:
                continue

            # L'événement est dans la fenêtre de déclenchement ?
            if borne_basse <= evt.timing <= limite:
                self._declencher(evt)

    def _declencher(self, evt: Evenement) -> None:
        """
        Génère et affiche un message proactif pour un événement donné.
        Met à jour le statut de l'événement en BD.
        """
        #formattage des données sous dictionnaire + création du prompt avec ces données
        contexte = self._construire_contexte(evt)

        template = _charger_prompt("proactive.txt")
        prompt = template.format(**contexte)

        #envoi du prompt au LLM
        message_proactif = self.llm.send_simple(prompt).strip()
        _afficher_message_proactif(message_proactif)
        #maj de l'event en BD
        self._data_evt.updateEvent(evt.id, "Déclenché")

    def _construire_contexte(self, evt: Evenement) -> dict:
        """
        Rassemble toutes les informations nécessaires au prompt proactif.
        """
        profil = self._data_profil.getProfil(self.id_profil)
        prefs = self._data_prefs.getPreferences(self.id_profil)
        mct_list = self._data_mct.getToday(self.id_profil)
        mlt = self._data_mlt.getRecente(self.id_profil)
        compagnon = self._data_compagnon.getCompagnon(1)

        # Formatage des préférences
        if prefs:
            lignes_prefs = "\n".join(f"  - {p.sujet} (intérêt : {p.niveau:.0%})" for p in prefs)
        else:
            lignes_prefs = "  Aucune préférence enregistrée."

        # Formatage de la MCT du jour
        if mct_list:
            lignes_mct = "\n".join(f"  {mct.message}" for mct in reversed(mct_list))
        else:
            lignes_mct = "  Aucun échange aujourd'hui pour l'instant."

        # Calcul de l'âge
        age = 0
        if profil and profil.date_naissance:
            today = datetime.now()
            dn = profil.date_naissance
            age = today.year - dn.year
            if (today.month, today.day) < (dn.month, dn.day):
                age -= 1

        # si le scheduler se déclenche quelques secondes après le timing prévu.
        delta = evt.timing - datetime.now()
        minutes_restantes = max(0, int(delta.total_seconds() / 60))
        if minutes_restantes == 0:
            delai_str = "maintenant"
        elif minutes_restantes < 60:
            delai_str = f"dans {minutes_restantes} minute(s)"
        else:
            heures = minutes_restantes // 60
            minutes_restantes_apres = minutes_restantes % 60
            if minutes_restantes_apres > 0:
                delai_str = f"dans environ {heures}h{minutes_restantes_apres:02d}"
            else:
                delai_str = f"dans environ {heures} heure(s)"

        return {
            "nom_compagnon": compagnon.modele if compagnon else "Compagnon",
            "prenom": profil.prenom if profil else "l'utilisateur",
            "nom": profil.nom if profil else "",
            "age": age,
            "description_evenement": evt.description or "événement sans description",
            "timing_evenement": evt.timing.strftime("%d/%m/%Y à %H:%M") if evt.timing else "date inconnue",
            "delai_evenement": delai_str,
            "lignes_preferences": lignes_prefs,
            "lignes_mct": lignes_mct,
            "contenu_mlt": mlt.text if mlt else "Aucune mémoire long terme disponible.",
        }

def _afficher_message_proactif(message: str) -> None:
    """
    Affiche le message proactif dans la console de façon visible,
    sans écraser le prompt en cours de l'utilisateur.
    """
    separateur = "─" * 50
    print(f"\n{separateur}")
    print(f" Compagnon (message proactif) :")
    print(f" {message}")
    print(f"{separateur}")
    print("Toi : ", end="", flush=True)