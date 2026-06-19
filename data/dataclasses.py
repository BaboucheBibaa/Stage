from datetime import datetime

from projectTypes import (
    MCT,
    MLT,
    CompagnonVirtuel,
    Conversation,
    Evenement,
    Message,
    Preference,
    Profil,
    SujetSensible,
)

from .bd import Database


class DonneesProfil:
    """Classe permettant de gérer les données du profil au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def getProfil(self, id_profil: int) -> Profil | None:
        """Retourne le profil de l'utilisateur id_profil

        Args:
            id_profil (int): Identifiant de l'utilisateur en BD

        Returns:
            Profil | None: Retourne les données du profil ou None si aucun résultat
        """
        lignes = self._db.executeFetch(
            "SELECT * FROM Profil WHERE ID_Profil = ?", (id_profil,)
        )
        if not lignes:
            return None
        ligne = lignes[0]
        return Profil(
            id=ligne["ID_Profil"],
            nom=ligne["Nom"],
            prenom=ligne["Prenom"],
            date_naissance=ligne["Date_Naissance"],
        )

    def create(self, profil: Profil) -> int:
        """Crée un profil et retourne son identifiant.

        Args:
            profil (Profil): Données du profil à ajouter

        Returns:
            int: identifiant du profil ajouté.
        """
        self._db.execute(
            "INSERT INTO Profil (Nom, Prenom, Date_Naissance) VALUES (?, ?, ?)",
            (
                profil.nom,
                profil.prenom,
                datetime.strptime(profil.date_naissance, "%Y-%m-%d %H:%M:%S"),
            ),
        )
        resultat = self._db.executeFetch(
            "SELECT ID_Profil FROM Profil WHERE Nom = ? AND Prenom = ? AND Date_Naissance = ?",
            (profil.nom, profil.prenom, profil.date_naissance),
        )
        return resultat[0]["ID_Profil"] if resultat else None

    def update(self, profil: Profil) -> None:
        """Met à jour un profil

        Args:
            profil (Profil): Données qui remplaceront les anciennes données du profil

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            "UPDATE Profil SET Nom=?, Prenom=?, Date_Naissance=? WHERE ID_Profil=?",
            (profil.nom, profil.prenom, profil.date_naissance, profil.id),
        )
        return res


class DonneesPreferences:
    """Classe permettant de gérer les préférences d'un profil au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def getPreferences(self, id_profil: int) -> list[Preference]:
        """Récupère les préférences d'un profil avec pour identifiant id_profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[Preference]: Liste des préférences du profil
        """
        lignes = self._db.executeFetch(
            "SELECT * FROM Preferences WHERE ID_Profil = ? ORDER BY Niveau DESC",
            (id_profil,),
        )
        return [
            Preference(
                id=l["ID_Pref"],
                sujet=l["Sujet"],
                niveau=l["Niveau"],
                id_profil=l["ID_Profil"],
            )
            for l in lignes
        ]

    def create(self, pref: Preference) -> int:
        """Insère une nouvelle préférence et retourne son identifiant.

        Args:
            pref (Preference): Données de la préférence à ajouter

        Returns:
            int: Identifiant de la préférence créée
        """
        self._db.execute(
            "INSERT INTO Preferences (Sujet, Niveau, ID_Profil) VALUES (?, ?, ?)",
            (pref.sujet, pref.niveau, pref.id_profil),
        )
        resultat = self._db.executeFetch(
            "SELECT ID_Pref FROM Preferences WHERE ID_Profil = ? ORDER BY ID_Pref DESC LIMIT 1",
            (pref.id_profil,),
        )
        return resultat[0]["ID_Pref"] if resultat else None

    def update(self, pref: Preference) -> bool:
        """Met à jour le niveau d'une préférence existante.

        Args:
            pref (Preference): Préférence à mettre à jour (doit avoir un id renseigné)

        Returns:
            bool: Requête réussie ou non
        """
        return self._db.execute(
            "UPDATE Preferences SET Niveau = ? WHERE ID_Pref = ?",
            (pref.niveau, pref.id),
        )


class DonneesSujetSensible:
    """Classe permettant de gérer les sujets sensibles d'un profil au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def getSujets(self, id_profil: int) -> list[SujetSensible]:
        """Récupère les sujets sensibles d'un profil avec pour identifiant id_profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[SujetSensible]: Liste des sujets sensibles du profil, triés par niveau (décroissant)
        """
        lignes = self._db.executeFetch(
            "SELECT * FROM Sujets_Sensibles WHERE ID_Profil = ? ORDER BY Niveau DESC",
            (id_profil,),
        )
        return [
            SujetSensible(
                id=l["ID_Sujet"],
                sujet=l["Sujet"],
                niveau=l["Niveau"],
                id_profil=l["ID_Profil"],
            )
            for l in lignes
        ]

    def create(self, sujet: SujetSensible) -> int:
        """Insère un nouveau sujet sensible et retourne son identifiant.

        Args:
            sujet (SujetSensible): Données du sujet sensible à ajouter

        Returns:
            int: Identifiant du sujet sensible créé
        """
        self._db.execute(
            "INSERT INTO Sujets_Sensibles (Sujet, Niveau, ID_Profil) VALUES (?, ?, ?)",
            (sujet.sujet, sujet.niveau, sujet.id_profil),
        )
        result = self._db.executeFetch(
            "SELECT ID_Sujet FROM sujets_sensibles WHERE ID_Profil = ? ORDER BY ID_Sujet",
            (sujet.id_profil,),
        )
        return result[0]["ID_Sujet"] if result else None

    def update(self, sujet: SujetSensible) -> bool:
        """Met à jour le niveau d'un sujet sensible existant.

        Args:
            sujet (SujetSensible): Sujet sensible à mettre à jour (doit avoir un id renseigné)

        Returns:
            bool: Requête réussie ou non
        """
        return self._db.execute(
            "UPDATE Sujets_Sensibles SET Niveau = ? WHERE ID_Sujet = ?",
            (sujet.niveau, sujet.id),
        )


class DonneesCompagnon:
    """Classe permettant de gérer les données des compagnons virtuels au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def getCompagnon(self, id_compagnon: int) -> CompagnonVirtuel:
        """Récupère un compagnon virtuel par son identifiant

        Args:
            id_compagnon (int): Identifiant du compagnon virtuel

        Returns:
            CompagnonVirtuel | None: Données du compagnon ou None si aucun résultat
        """
        lignes = self._db.executeFetch(
            "SELECT * FROM Compagnon_Virtuel WHERE ID_Compagnon = ?", (id_compagnon,)
        )
        if not lignes:
            return None
        ligne = lignes[0]
        return CompagnonVirtuel(
            id=ligne["ID_Compagnon"],
            modele=ligne["Modele"],
            profil={
                "empathie": ligne["Empathie"],
                "humour": ligne["Humour"],
                "professionalisme": ligne["Professionalisme"],
                "patience": ligne["Patience"],
            },
        )


class DonneesConversation:
    """Classe permettant de gérer les conversations entre un profil et un compagnon au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def create(self, conv: Conversation) -> int:
        """Crée une nouvelle conversation et retourne son identifiant

        Args:
            conv (Conversation): Données de la conversation à créer

        Returns:
            int: Identifiant de la conversation créée
        """
        self._db.execute(
            """INSERT INTO Conversation (Sujet, ID_Profil, Date_Creation, ID_Compagnon)
                VALUES (?, ?, ?, ?)""",
            (conv.sujet, conv.id_user, conv.date_creation, conv.id_companion),
        )
        # retourne l'id de la conversation créée.
        result = self._db.executeFetch(
            "SELECT ID_Conversation FROM Conversation "
            "WHERE ID_Profil = ? AND ID_Compagnon = ? "
            "ORDER BY ID_Conversation DESC LIMIT 1",
            (conv.id_user, conv.id_companion),
        )
        return result[0]["ID_Conversation"] if result else None

    def getConversation(self, id_conversation: int) -> Conversation:
        """Récupère une conversation par son identifiant

        Args:
            id_conversation (int): Identifiant de la conversation

        Returns:
            Conversation | None: Données de la conversation ou None si aucun résultat
        """
        res = self._db.executeFetch(
            """SELECT id_conversation, id_profil, id_compagnon,sujet, date_creation FROM Conversation WHERE ID_Conversation = ?""",
            (id_conversation,),
        )
        if res:
            return Conversation(
                id=res[0],
                id_user=res[1],
                id_companion=res[2],
                sujet=res[3],
                date_creation=res[4],
            )

    def get_recent(self, id_profil: int, limit: int = 5) -> list[Conversation]:
        """Récupère les N dernières conversations d'un profil

        Args:
            id_profil (int): Identifiant du profil
            limit (int): Nombre maximum de conversations à retourner (défaut: 5)

        Returns:
            list[Conversation]: Liste des conversations récentes, triées par date décroissante
        """
        lignes = self._db.executeFetch(
            """SELECT * FROM Conversation
                WHERE ID_Profil = ?
                ORDER BY Date_Creation DESC LIMIT ?""",
            (id_profil, limit),
        )
        return [
            Conversation(
                id=l["ID_Conversation"],
                sujet=l["Sujet"],
                id_profil=l["ID_Profil"],
                id_compagnon=l["ID_Compagnon"],
                date_creation=l["Date_Creation"],
            )
            for l in lignes
        ]

    def updateSubject(self, id_conv: int, sujet: str):
        """Supprime une conversation par son identifiant

        Args:
            id_conv (int): Identifiant de la conversation à supprimer

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            """UPDATE Conversation SET Sujet = ? WHERE ID_Conversation = ?""",
            (sujet, id_conv),
        )
        return res

    def delete(self, id_conv: int):
        """Supprime une conversation par son identifiant

        Args:
            id_conv (int): Identifiant de la conversation à supprimer

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            """DELETE FROM Conversation WHERE ID_Conversation = ?""", (id_conv,)
        )
        return res


class DonneesMessage:
    """Classe permettant de gérer les messages d'une conversation au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def create(self, msg: Message) -> int:
        """Crée un message dans une conversation et retourne son identifiant

        Args:
            msg (Message): Données du message (message utilisateur + réponse assistant)

        Returns:
            int: Identifiant du message créé
        """
        self._db.execute(
            """INSERT INTO Messages (Date_Message, Msg_User, Rep_Assistant, ID_Conversation)
                VALUES (?, ?, ?, ?)""",
            (
                msg.date_creation,
                msg.msg_user,
                msg.reponse_assistant,
                msg.id_conversation,
            ),
        )
        result = self._db.executeFetch(
            """SELECT ID_Message FROM Messages WHERE ID_Conversation = ? ORDER BY Date_Message DESC LIMIT 1""",
            (msg.id_conversation,),
        )
        return result[0]["ID_Message"] if result else None

    def getMessages(self, id_conversation: int) -> list[Message]:
        """Récupère tous les messages d'une conversation

        Args:
            id_conversation (int): Identifiant de la conversation

        Returns:
            list[Message]: Liste des messages, triés par date croissante
        """
        lignes = self._db.executeFetch(
            "SELECT * FROM Messages WHERE ID_Conversation = ? ORDER BY Date_Message",
            (id_conversation,),
        )
        return [
            Message(
                id=l["ID_Message"],
                msg_user=l["Msg_User"],
                rep_assistant=l["Rep_Assistant"],
                id_conversation=l["ID_Conversation"],
                date_message=l["Date_Message"],
            )
            for l in lignes
        ]


class DonneesEvenement:
    """Classe permettant de gérer les événements détectés au sein d'une BD."""

    def __init__(self, db: Database):
        self._db = db

    def create(self, evt: Evenement) -> int:
        """Crée un événement et retourne son identifiant

        Args:
            evt (Evenement): Données de l'événement

        Returns:
            int: Identifiant de l'événement créé
        """
        self._db.execute(
            """INSERT INTO Evenement (Timing, Statut, Contexte, ID_Profil, Type_Evenement, Importance, Timing_Evenement)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                evt.timing,
                evt.statut,
                evt.description,
                evt.id_profil,
                evt.type_evenement,
                evt.importance,
                evt.timing_notification,
            ),
        )
        result = self._db.executeFetch(
            """SELECT ID_Event FROM Evenement WHERE ID_Profil = ? ORDER BY ID_Event DESC LIMIT 1""",
            (evt.id_profil,),
        )
        return result[0]["ID_Event"] if result else None

    def getFuturs(
        self, id_profil: int, seuil_importance: float = 0.3
    ) -> list[Evenement]:
        """Récupère les événements futurs dont le score d'importance dépasse le seuil.

        Args:
            id_profil (int): Identifiant du profil
            seuil_importance (float): Score minimum pour déclencher une notification (défaut: 0.3)

        Returns:
            list[Evenement]: Événements futurs triés par timing, filtrés par importance
        """
        lignes = self._db.executeFetch(
            """SELECT * FROM Evenement
                WHERE ID_Profil = ? AND Statut != 'Déclenché'
                AND Importance >= ?
                ORDER BY Importance DESC, Timing""",
            (id_profil, seuil_importance),
        )
        return [
            Evenement(
                id=l["ID_Event"],
                timing=l["Timing"],
                statut=l["Statut"],
                description=l["Contexte"],
                id_profil=l["ID_Profil"],
                type_evenement=l["Type_Evenement"],
                importance=l["Importance"] if l["Importance"] is not None else 0.5,
                timing_notification=l["Timing_Evenement"],
            )
            for l in lignes
        ]

    def updateEvent(self, id_event: int, statut: str) -> None:
        """Met à jour le statut d'un événement

        Args:
            id_event (int): Identifiant de l'événement
            statut (str): Nouveau statut de l'événement

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            "UPDATE Evenement SET Statut = ? WHERE ID_Event = ?", (statut, id_event)
        )
        return res

    def updateImportance(self, id_event: int, importance: float) -> bool:
        """Met à jour le score d'importance d'un événement.

        Utile pour affiner le score après la détection initiale
        (ex: recalcul).

        Args:
            id_event (int): Identifiant de l'événement
            importance (float): Nouveau score d'importance (0.0 à 1.0)

        Returns:
            bool: Requête réussie ou non
        """
        importance = max(0.0, min(1.0, importance))
        res = self._db.execute(
            "UPDATE Evenement SET Importance = ? WHERE ID_Event = ?",
            (importance, id_event),
        )
        return res


class DonneesMLT:
    """Classe permettant de gérer la Mémoire Long Terme (MLT) d'un profil au sein d'une BD.

    La MLT conserve les résumés et informations durables sur le profil, basés sur les conversations passées.
    """

    def __init__(self, db: Database):
        self._db = db

    def create(self, mlt: MLT) -> int:
        """Crée une entrée MLT et retourne son identifiant

        Args:
            mlt (MLT): Données de la mémoire long terme

        Returns:
            int: Identifiant de l'entrée MLT créée
        """
        self._db.execute(
            "INSERT INTO MLT (Nombre_Echanges, Humeur_Generale, Themes_Abordes, Centres_Interets, Evenements_Mentionnes, Resume_Conversation, Date_Creation, ID_Profil) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mlt.nombre_echanges,
                mlt.humeur_generale,
                mlt.themes_abordes,
                mlt.centres_interets,
                mlt.evenements_mentionnes,
                mlt.resume_conversation,
                mlt.date_creation,
                mlt.id_profil,
            ),
        )
        result = self._db.executeFetch(
            """SELECT ID_MLT FROM MLT WHERE ID_Profil = ? ORDER BY DATE_CREATION DESC LIMIT 1""",
            (mlt.id_profil,),
        )
        return result[0]["ID_MLT"] if result else None

    def getMLT(self, id_profil: int) -> list[MLT] | None:
        """Récupère toute la MLT d'un profil.

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[MLT] | None: Liste de toutes les MLT du profil
        """
        result = self._db.executeFetch(
            "SELECT * FROM MLT WHERE ID_Profil = ?", (id_profil,)
        )
        if result:
            return
        [
            MLT(
                nombre_echanges=l["Nombre_Echanges"],
                humeur_generale=l["Humeur_Generale"],
                themes_abordes=l["Themes_Abordes"],
                centres_interets=l["Centres_Interets"],
                evenements_mentionnes=l["Evenements_Mentionnes"],
                resume_conversation=l["Resume_Conversation"],
                id_profil=l["ID_Profil"],
                date_creation=l["Date_Creation"],
            )
            for l in result
        ]

    def getRecente(self, id_profil: int) -> MLT | None:
        """Récupère la MLT la plus récente d'un profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            MLT | None: Données de la MLT la plus récente ou None si aucune MLT
        """
        result = self._db.executeFetch(
            "SELECT * FROM MLT WHERE ID_Profil = ? ORDER BY Date_Creation DESC LIMIT 1",
            (id_profil,),
        )
        if result:
            l = result[0]
            return MLT(
                id=l["ID_MLT"],
                nombre_echanges=l["Nombre_Echanges"],
                humeur_generale=l["Humeur_Generale"],
                themes_abordes=l["Themes_Abordes"],
                centres_interets=l["Centres_Interets"],
                evenements_mentionnes=l["Evenements_Mentionnes"],
                resume_conversation=l["Resume_Conversation"],
                id_profil=l["ID_Profil"],
                date_creation=l["Date_Creation"],
            )
        return None


class DonneesMCT:
    """Classe permettant de gérer la Mémoire Court Terme (MCT) d'un profil au sein d'une BD.

    La MCT conserve les N derniers échanges avec le compagnon pour maintenir le contexte de conversation.
    """

    def __init__(self, db: Database):
        self._db = db

    def create(self, mct: MCT) -> int:
        """Crée une entrée MCT et retourne son identifiant

        Args:
            mct (MCT): Données de la mémoire court terme (échange utilisateur-assistant)

        Returns:
            int: Identifiant de l'entrée MCT créée
        """
        self._db.execute(
            "INSERT INTO MCT (Date_Creation, ID_Profil, Sujet, Intention, Evenements_Mentionnes, Resume_Reponse, Entites_Mentionnees, Langage, Tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mct.date_creation,
                mct.id_profil,
                mct.sujet,
                mct.intention,
                mct.evenements_mentionnes,
                mct.resume_reponse,
                mct.entites_mentionnees,
                mct.langage,
                mct.tags,
            ),
        )
        result = self._db.executeFetch(
            """SELECT ID_MCT FROM MCT WHERE ID_Profil = ? ORDER BY DATE_CREATION DESC LIMIT 1""",
            (mct.id_profil,),
        )
        return result[0]["ID_MCT"] if result else None

    def getToday(self, id_profil: int) -> list[MCT]:
        """Récupère les N échanges les plus récents d'un profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[MCT]: Liste des échanges récents, triés par date décroissante (plus récent en premier)
        """
        lignes = self._db.executeFetch(
            """SELECT * FROM MCT WHERE ID_Profil = ? AND DATE(Date_Creation) = ?
                ORDER BY Date_Creation DESC""",
            (id_profil, str(datetime.now().date())),
        )
        return [
            MCT(
                sujet=l["Sujet"],
                intention=l["Intention"],
                evenements_mentionnes=l["Evenements_Mentionnes"],
                id_profil=l["ID_Profil"],
                date_creation=l["Date_Creation"],
                resume_reponse=l["Resume_Reponse"],
                entites_mentionnees=l["Entites_Mentionnees"],
                tags=l["Tags"],
                langage=l["Langage"],
            )
            for l in lignes
        ]

    def vider(self, id_profil: int) -> None:
        """Nettoie la MCT en conservant seulement les K entrées les plus récentes
        Args:
            id_profil (int): Identifiant du profil
        Returns:
            None
        """
        res = self._db.execute("DELETE FROM MCT WHERE ID_Profil = ?", (id_profil,))
        print(res)
