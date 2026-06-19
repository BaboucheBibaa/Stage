from datetime import datetime
from pathlib import Path

from spacy import load

from data.bd import Database
from data.dataclasses import (
    DonneesCompagnon,
    DonneesConversation,
    DonneesEvenement,
    DonneesMCT,
    DonneesMessage,
    DonneesMLT,
    DonneesPreferences,
    DonneesProfil,
    DonneesSujetSensible,
)
from projectTypes import (
    MCT,
    MLT,
    BaseLLMClient,
    Conversation,
    LLMMessage,
    Message,
    ResumeMCTOutput,
    ResumeMLTOutput,
)

from .EventModule import EventModule

_TEMPLATE = (Path(__file__).parent / "../prompts/system_prompt.txt").read_text(
    encoding="utf-8"
)

_PROMPTS = Path(__file__).parent / "../prompts"


def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")


nlp = load("fr_core_news_md")


class DialogueModule:
    """Gère les dialogues entre l'utilisateur et le compagnon virtuel"""

    def __init__(self, llm: BaseLLMClient, id_profil: int):
        # dataclasses
        self._db = Database()
        self.data_mlt = DonneesMLT(db=self._db)
        self.data_mct = DonneesMCT(db=self._db)
        self.id_profil = id_profil
        self.profil = DonneesProfil(self._db).getProfil(self.id_profil)

        self.llm = llm
        # Charger les données du profil du compagnon
        data_compagnon = DonneesCompagnon(db=self._db)
        self.compagnon = data_compagnon.getCompagnon(1)
        if not self.compagnon:
            raise ValueError("Aucun compagnon virtuel trouvé en base de données")

        # Historique de la conversation courante
        self._historique: list[LLMMessage] = []

        self._id_conversation = self._nouvelle_conversation()
        if not self._id_conversation:
            raise RuntimeError("Impossible de créer une nouvelle conversation")

    def chat(self, message_user: str) -> str:
        """Envoie un message et reçoit une réponse personnalisée"""
        # filtre de la mémoire court terme pertinente par rapport au message de l'utilisateur pour pas surcharger le compagnon avec de la mémoire inutile.
        mct_pertinente = self.recup_MCT_pertinente(message_user=message_user)
        prompt_systeme = self._build_system_prompt(mct_pertinente)
        # Ajouter le message utilisateur à l'historique (on ne lit que l'historique)
        self._historique.append(LLMMessage(role="user", contenu=message_user))
        # Appeler le LLM
        response = self.llm.send(
            # envoie de l'historique de conversation récent
            messages=self._historique,
            system_prompt=prompt_systeme,
        )

        # Ajouter la réponse à l'historique
        self._historique.append(LLMMessage(role="assistant", contenu=response))
        # détection d'événement dans un message
        data_evenement = DonneesEvenement(self._db)
        event_module = EventModule(self.llm, self.id_profil, data_evenement)
        event_module.detecter(message_user)

        self._sauvegarder_message(message_user, response)
        self._add_MCT(message_user, response)
        return response

    def _nouvelle_conversation(self) -> int:
        """Crée une nouvelle conversation"""
        data_conv = DonneesConversation(db=self._db)
        conv = Conversation(
            sujet="Session du " + datetime.now().strftime("%d/%m/%Y %H:%M"),
            id_user=self.id_profil,
            id_companion=self.compagnon.id,
            date_creation=datetime.now(),
        )
        return data_conv.create(conv)

    def _sauvegarder_message(self, msg_user: str, rep_assistant: str) -> None:
        """Sauvegarde le message et la réponse en BD"""
        try:
            data_msg = DonneesMessage(db=self._db)
            data_msg.create(
                Message(
                    msg_user=msg_user,
                    reponse_assistant=rep_assistant,
                    id_conversation=self._id_conversation,
                    date_creation=datetime.now(),
                )
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {e}")

    def sauvegarder_MLT(self, id_profil: int) -> bool:
        """Sauvegarde la mémoire long terme (MLT) et nettoie la MCT"""
        # Récupération de la discussion de la journée
        historique = self.data_mct.getToday(id_profil)
        if not historique:
            return False
        # Création de l'enregistrement de la mémoire long terme avec les données
        mlt_resume = self.resumer_session(self.llm, historique)
        mlt_id = self.data_mlt.create(
            MLT(
                id_profil=self.id_profil,
                date_creation=datetime.now(),  # Datetime objet, pas string
                resume_conversation=mlt_resume.resume_conversation,
                nombre_echanges=mlt_resume.nombre_echanges,
                themes_abordes=mlt_resume.themes_abordes,
                centres_interets=mlt_resume.centres_interets,
                humeur_generale=mlt_resume.humeur_generale,
                evenements_mentionnes=mlt_resume.evenements_mentionnes,
            )
        )
        if mlt_id:
            # Si ça a bien été créé, alors on vide la MCT
            self.data_mct.vider(id_profil)

            return True
        else:
            print("Erreur: Impossible de sauvegarder la MLT")
            return False

    def _add_MCT(self, msg_user: str, rep_assistant: str) -> bool:
        """Ajoute une donnée dans la mémoire court terme (MCT)"""
        resume_obj = self.resumer_echange(self.llm, msg_user, rep_assistant)

        # Convertir l'objet Pydantic en JSON pour le stocker
        mct_creee = MCT(
            sujet=resume_obj.Sujet,
            intention=resume_obj.intention,
            evenements_mentionnes=resume_obj.Evenements_Mentionnes,
            resume_reponse=resume_obj.Resume_Reponse,
            entites_mentionnees=resume_obj.Entites_Mentionnees,
            langage=resume_obj.language,
            tags=resume_obj.tags,
            id_profil=self.id_profil,
            date_creation=datetime.now(),
        )
        print(mct_creee)
        mct_id = self.data_mct.create(mct_creee)

        if mct_id:
            return True
        else:
            print("Erreur: Impossible de créer la MCT")
            return False

    @staticmethod
    def _calculer_age(date_naissance: datetime) -> int:
        """Calcule l'âge à partir de la date de naissance

        Args:
            date_naissance: datetime.date, datetime.datetime, ou string au format 'YYYY-MM-DD'

        Returns:
            int: Age en années
        """
        try:
            today = datetime.now()
            age = today.year - date_naissance.year

            # Ajuster si l'anniversaire n'a pas eu lieu cette année
            if (today.month, today.day) < (date_naissance.month, date_naissance.day):
                age -= 1

            return age
        except Exception as e:
            print(f"Erreur lors du calcul de l'âge: {e}")
            return 0

    def recup_MCT_pertinente(self, message_user: str, seuil: float = 0.6) -> list[MCT]:
        mct_pertinente: list[MCT] = []
        doc = nlp(message_user)
        donnees_mct = self.data_mct.getToday(self.id_profil)
        for donnee_mct in donnees_mct:
            # Extraire le texte depuis le JSON MCT
            texte_compare = f"{donnee_mct.resume_reponse}"
            doc_mct = nlp(texte_compare)
            if doc.vector_norm != 0 or doc_mct.vector_norm != 0:
                if doc.similarity(doc_mct) > seuil:
                    mct_pertinente.append(donnee_mct)
        return mct_pertinente

    def resumer_echange(
        self, llm: BaseLLMClient, msg_user: str, rep_assistant: str
    ) -> ResumeMCTOutput:
        """
        Résume un échange en une phrase courte pour la MCT.
        """
        system_prompt = _charger("mct/mct_resume_system.txt")
        user_prompt = _charger("mct/mct_resume_user.txt").format(
            msg_user=msg_user, rep_assistant=rep_assistant
        )
        res = llm.send(
            messages=[LLMMessage(role="user", contenu=user_prompt)],
            system_prompt=system_prompt,
            output_model=ResumeMCTOutput,
        )
        return res

    def resumer_session(
        self, llm: BaseLLMClient, historique: list[MCT]
    ) -> ResumeMLTOutput:
        """
        Résume toute la session pour mettre à jour la MLT.
        Appelé en fin de conversation (quand l'utilisateur quitte).

        historique : liste de LLMMessage de la session courante
        mlt_existante : texte de la dernière MLT en base (peut être vide)
        """
        lignes = [
            f"Résumé de la conversation à {msg.date_creation} : {msg.resume_reponse}"
            for msg in historique
        ]
        system_prompt = _charger("mlt/mlt_resume_system.txt")
        user_prompt = _charger("mlt/mlt_resume_user.txt").format(
            liste_messages="\n".join(lignes)
        )
        res = llm.send(
            messages=[LLMMessage(role="user", contenu=user_prompt)],
            system_prompt=system_prompt,
            output_model=ResumeMLTOutput,
        )
        return res

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

    def _build_system_prompt(self, mct_Pertinente: list[MCT]) -> str:
        data_prefs = DonneesPreferences(db=self._db)
        data_profil = DonneesProfil(db=self._db)
        data_sujets = DonneesSujetSensible(db=self._db)

        liste_mlt = self.data_mlt.getMLT(self.id_profil)
        profil = data_profil.getProfil(self.id_profil)

        prefs = data_prefs.getPreferences(self.id_profil)
        sensibles = data_sujets.getSujets(self.id_profil)

        if not profil:
            raise ValueError(
                f"Profil avec l'ID {self.id_profil} introuvable en base de données"
            )

        # Préférences
        if prefs:
            lignes_preferences = "\n".join(
                f"  - {p.sujet} (intérêt : {p.niveau:.0%})" for p in prefs
            )
        else:
            lignes_preferences = "  Aucune préférence enregistrée pour l'instant."

        # Sujets sensibles
        if sensibles:
            lignes = []
            for s in sensibles:
                if s.niveau >= 0.7:
                    consigne = "éviter absolument"
                elif s.niveau >= 0.4:
                    consigne = "aborder avec beaucoup de délicatesse"
                else:
                    consigne = "aborder avec prudence"
                lignes.append(f"  - {s.sujet} ({consigne})")
            lignes_sujets_sensibles = "\n".join(lignes)
        else:
            lignes_sujets_sensibles = "  Aucun sujet sensible enregistré."

        # MLT
        if liste_mlt:
            contenu_mlt = "\n".join(self.format_mct(mlt) for mlt in reversed(liste_mlt))
        else:
            contenu_mlt = " Aucune mémoire long terme sauvegardée."
        # MCT
        if mct_Pertinente:
            lignes_mct = "\n".join(
                self.format_mct(mct) for mct in reversed(mct_Pertinente)
            )
        else:
            lignes_mct = "  Aucun échange précédent."

        return _TEMPLATE.format(
            date_jour=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            nom_compagnon=self.compagnon.modele,
            prenom=profil.prenom,
            nom=profil.nom,
            age=self._calculer_age(profil.date_naissance),
            empathie=f"{self.compagnon.profil['empathie']:.0%}",
            humour=f"{self.compagnon.profil['humour']:.0%}",
            professionalisme=f"{self.compagnon.profil['professionalisme']:.0%}",
            patience=f"{self.compagnon.profil['patience']:.0%}",
            lignes_preferences=lignes_preferences,
            lignes_sujets_sensibles=lignes_sujets_sensibles,
            contenu_mlt=contenu_mlt,
            lignes_mct=lignes_mct,
        )
