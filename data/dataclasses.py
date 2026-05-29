"""
DataClasses — Couche d'abstraction pour accéder aux données en BD.

Ce module fournit des classes de gestion de données (repositories) pour persister
et récupérer les informations relatives aux profils, préférences, conversations,
mémoires, et autres entités du système.

Chaque classe correspond à une entité du modèle de données et expose des méthodes
de CRUD (Create, Read, Update, Delete) ou de requêtes spécifiques.
"""

from .bd import Database
from .modeles import Conversation, Profil, Preference, Message, MLT, MCT, SujetSensible, CompagnonVirtuel, Evenement
from datetime import datetime

class DonneesProfil:
    """Classe permettant de gérer les données du profil au sein d'une BD.
    """
    def __init__(self, db: Database):
        self._db = db

    def getProfil(self, id_profil: int) -> Profil | None:
        """Retourne le profil de l'utilisateur id_profil

        Args:
            id_profil (int): Identifiant de l'utilisateur en BD

        Returns:
            Profil | None: Retourne les données du profil ou None si aucun résultat
        """
        rows = self._db.executeFetch(
            "SELECT * FROM Profil WHERE ID_Profil = ?",
            (id_profil,)
        )
        if not rows:
            return None
        row = rows[0]
        return Profil(
            id=row["ID_Profil"],
            nom=row["Nom"],
            prenom=row["Prenom"],
            date_naissance=row["Date_Naissance"],
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
            (profil.nom, profil.prenom, profil.date_naissance),
        )
        result = self._db.executeFetch(
            "SELECT ID_Profil FROM Profil WHERE Nom = ? AND Prenom = ? AND Date_Naissance = ?", (profil.nom,profil.prenom,profil.date_naissance)
        )
        return result

    def update(self, profil: Profil) -> None:
        """Met à jour un profil

        Args:
            profil (Profil): Données qui remplaceront les anciennes données du profil

        Returns:
            bool: Requête réussie ou non
        """
        res =self._db.execute(
            "UPDATE Profil SET Nom=?, Prenom=?, Date_Naissance=? WHERE ID_Profil=?",
            (profil.nom, profil.prenom, profil.date_naissance, profil.id),
        )
        return res

class DonneesPreferences:
    """Classe permettant de gérer les préférences d'un profil au sein d'une BD.
    """
    def __init__(self, db: Database):
        self._db = db

    def getPreferences(self, id_profil: int) -> list[Preference]:
        """Récupère les préférences d'un profil avec pour identifiant id_profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[Preference]: Liste des préférences du profil
        """
        rows = self._db.executeFetch(
                "SELECT * FROM Preferences WHERE ID_Profil = ? ORDER BY Niveau DESC",
                (id_profil,)
            )
        return [
            Preference(id=r["ID_Pref"], sujet=r["Sujet"], niveau=r["Niveau"], id_profil=r["ID_Profil"])
            for r in rows
        ]

    def upsert(self, pref: Preference) -> int:
        """Insère ou met à jour une préférence utilisateur

        Args:
            pref (Preference): Données correspondant à une préférence utilisateur

        Returns:
            bool: Requête réussie ou non
        """
        res =self._db.execute(
            """INSERT INTO Preferences (Sujet, Niveau, ID_Profil)
                VALUES (?, ?, ?)
                ON DUPLICATE KEY UPDATE Niveau = ?""",
            (pref.sujet, pref.niveau, pref.id_profil, pref.niveau),
        )
        return res


class DonneesSujetSensible:
    """Classe permettant de gérer les sujets sensibles d'un profil au sein d'une BD.
    """
    def __init__(self, db: Database):
        self._db = db

    def getSujets(self, id_profil: int) -> list[SujetSensible]:
        """Récupère les sujets sensibles d'un profil avec pour identifiant id_profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[SujetSensible]: Liste des sujets sensibles du profil, triés par niveau (décroissant)
        """
        rows = self._db.executeFetch(
            "SELECT * FROM Sujets_Sensibles WHERE ID_Profil = ? ORDER BY Niveau DESC",
            (id_profil,)
        )
        return [
            SujetSensible(id=r["ID_Sujet"], sujet=r["Sujet"], niveau=r["Niveau"], id_profil=r["ID_Profil"])
            for r in rows
        ]

    def upsert(self, sujet: SujetSensible) -> int:
        """Insère ou met à jour un sujet sensible

        Args:
            sujet (SujetSensible): Données correspondant à un sujet sensible

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            "INSERT INTO Sujets_Sensibles (Sujet, Niveau, ID_Profil) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE Niveau = ?",
            (sujet.sujet, sujet.niveau, sujet.id_profil, sujet.niveau),
        )
        return res

class DonneesCompagnon:
    """Classe permettant de gérer les données des compagnons virtuels au sein d'une BD.
    """
    def __init__(self, db: Database):
        self._db = db

    def getCompagnon(self, id_compagnon: int) -> CompagnonVirtuel:
        """Récupère un compagnon virtuel par son identifiant

        Args:
            id_compagnon (int): Identifiant du compagnon virtuel

        Returns:
            CompagnonVirtuel | None: Données du compagnon ou None si aucun résultat
        """
        row = self._db.executeFetch(
            "SELECT * FROM Compagnon_Virtuel WHERE ID_Compagnon = ?",
            (id_compagnon,)
        )
        row = row[0]
        if not row:
            return None
        return CompagnonVirtuel(
            id=row["ID_Compagnon"],
            modele=row["Modele"],
            profil={
                'empathie': row["Empathie"],
                'humour':row["Humour"],
                'professionalisme':row["Professionalisme"],
                'patience':row["Patience"]
            },
        )

class DonneesConversation:
    """Classe permettant de gérer les conversations entre un profil et un compagnon au sein d'une BD.
    """
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
        #retourne l'id de la conversation créée.
        result = self._db.executeFetch(
                "SELECT ID_Conversation FROM Conversation "
                "WHERE ID_Profil = ? AND ID_Compagnon = ? "
                "ORDER BY ID_Conversation DESC LIMIT 1",
                (conv.id_user, conv.id_companion)
            )
        return result[0]['ID_Conversation']

    def getConversation(self, id_conversation : int) -> Conversation:
        """Récupère une conversation par son identifiant

        Args:
            id_conversation (int): Identifiant de la conversation

        Returns:
            Conversation | None: Données de la conversation ou None si aucun résultat
        """
        res = self._db.executeFetch(
            """SELECT id_conversation, id_profil, id_compagnon,sujet, date_creation FROM Conversation WHERE ID_Conversation = ?""",
            (id_conversation,)
        )
        if res:
            return Conversation(
                id = res[0],
                id_user=res[1],
                id_companion=res[2],
                sujet=res[3],
                date_creation=res[4]
            )
    def get_recent(self, id_profil: int, limit: int = 5) -> list[Conversation]:
        """Récupère les N dernières conversations d'un profil

        Args:
            id_profil (int): Identifiant du profil
            limit (int): Nombre maximum de conversations à retourner (défaut: 5)

        Returns:
            list[Conversation]: Liste des conversations récentes, triées par date décroissante
        """
        rows = self._db.executeFetch(
            """SELECT * FROM Conversation
                WHERE ID_Profil = ?
                ORDER BY Date_Creation DESC LIMIT ?""",
            (id_profil, limit),
        )
        return [
            Conversation(
                id=r["ID_Conversation"], sujet=r["Sujet"],
                id_profil=r["ID_Profil"], id_compagnon=r["ID_Compagnon"],
                date_creation=r["Date_Creation"],
            )
            for r in rows
        ]
    def updateSubject(self, id_conv : int) :
        """Supprime une conversation par son identifiant

        Args:
            id_conv (int): Identifiant de la conversation à supprimer

        Returns:
            bool: Requête réussie ou non
        """ 
        res = self._db.execute(
            """DELETE FROM Conversation WHERE ID_Conversation = ?""",
                (id_conv,)
        )
        return res
    
    def delete(self, id_conv : int):
        """Supprime une conversation par son identifiant

        Args:
            id_conv (int): Identifiant de la conversation à supprimer

        Returns:
            bool: Requête réussie ou non
        """
        res = self._db.execute(
            """DELETE FROM Conversation WHERE ID_Conversation = ?""",
            (id_conv,)
        )
        return res

class DonneesMessage:
    """Classe permettant de gérer les messages d'une conversation au sein d'une BD.
    """
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
            (msg.date_creation, msg.msg_user,msg.reponse_assistant, msg.id_conversation),
        )
        result = self._db.executeFetch(
            """SELECT ID_Message FROM Messages WHERE ID_Conversation = ? ORDER BY Date_Message DESC LIMIT 1""",
            (msg.id_conversation,)
        )
        return result[0]

    def getMessages(self, id_conversation: int) -> list[Message]:
        """Récupère tous les messages d'une conversation

        Args:
            id_conversation (int): Identifiant de la conversation

        Returns:
            list[Message]: Liste des messages, triés par date croissante
        """
        rows = self._db.executeFetch(
            "SELECT * FROM Messages WHERE ID_Conversation = ? ORDER BY Date_Message",
            (id_conversation,)
        )
        return [
            Message(
                id=r["ID_Message"], msg_user=r["Msg_User"],
                rep_assistant=r["Rep_Assistant"], id_conversation=r["ID_Conversation"],
                date_message=r["Date_Message"],
            )
            for r in rows
        ]

class DonneesEvenement:
    """Classe permettant de gérer les événements détectés au sein d'une BD.
    """
    def __init__(self, db: Database):
        self._db = db

    def create(self, evt: Evenement) -> int:
        """Crée un événement et retourne son identifiant

        Args:
            evt (Evenement): Données de l'événement

        Returns:
            int: Identifiant de l'événement créé
        """
        res = self._db.execute(
            """INSERT INTO Evenement (Timing, Statut, Description, ID_Profil)
                VALUES (?, ?, ?, ?)""",
            (evt.timing, evt.statut, evt.description, evt.id_profil),
        )
        result = self._db.execute(
            """SELECT ID_Event FROM Evenement WHERE ID_Profil = ? ORDER BY Date_Message DESC LIMIT 1""",
            (evt.id_profil,)
        )
        return result[0][0]

    def getFuturs(self, id_profil: int) -> list[Evenement]:
        """Récupère les événements futurs ou en cours d'un profil
        
        Retourne uniquement les événements dont le statut n'est pas 'Terminé' et 
        dont la date est supérieure ou égale à maintenant.

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            list[Evenement]: Liste des événements futurs, triés par date croissante
        """
        rows = self._db.executeFetch(
            """SELECT * FROM Evenement
                WHERE ID_Profil = ? AND Statut != 'Terminé' AND Date_Event >= NOW()
                ORDER BY Date_Event""",
            (id_profil,)
        )
        return [
            Evenement(
                id=r["ID_Event"], titre=r["Titre"], date_event=r["Date_Event"],
                statut=r["Statut"], contexte=r["Contexte"], id_profil=r["ID_Profil"],
            )
            for r in rows
        ]

    def updateEvent(self, id_event: int, statut: str) -> None:
        """Met à jour le statut d'un événement

        Args:
            id_event (int): Identifiant de l'événement
            statut (str): Nouveau statut de l'événement

        Returns:
            bool: Requête réussie ou non
        """
        res =self._db.execute(
            "UPDATE Evenement SET Statut = ? WHERE ID_Event = ?",
            (statut, id_event),
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
            "INSERT INTO MLT (Message, Date_Creation, ID_Profil) VALUES (?, ?, ?)",
            (mlt.text, mlt.date_creation, mlt.id_profil),
        )
        result = self._db.executeFetch(
            """SELECT ID_MLT FROM MLT WHERE ID_Profil = ? ORDER BY DATE_CREATION DESC LIMIT 1""",
            (mlt.id_profil,)
        )
        return result
    
    def getRecente(self, id_profil: int) -> MLT | None:
        """Récupère la MLT la plus récente d'un profil

        Args:
            id_profil (int): Identifiant du profil

        Returns:
            MLT | None: Données de la MLT la plus récente ou None si aucune MLT
        """
        result = self._db.executeFetch(
            "SELECT * FROM MLT WHERE ID_Profil = ? ORDER BY Date_Creation DESC LIMIT 1",
            (id_profil,)
        )
        if result:
            r = result[0]
            return MLT(id=r["ID_MLT"], text=r["Message"], id_profil=r["ID_Profil"], date_creation=r["Date_Creation"])
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
            "INSERT INTO MCT (Date_Creation, ID_Profil, Message) VALUES (?, ?, ?)",
            (mct.date_creation, mct.id_profil, mct.message),
        )
        result = self._db.executeFetch(
            """SELECT ID_MCT FROM MCT WHERE ID_Profil = ? ORDER BY DATE_CREATION DESC LIMIT 1""",
            (mct.id_profil,)
        )
        return result
    
    def getToday(self, id_profil: int) -> list[MCT]:
        """Récupère les N échanges les plus récents d'un profil

        Args:
            id_profil (int): Identifiant du profil
            limit (int): Nombre maximum d'échanges à retourner (défaut: 10)

        Returns:
            list[MCT]: Liste des échanges récents, triés par date décroissante (plus récent en premier)
        """
        rows = self._db.executeFetch(
            """SELECT * FROM MCT WHERE ID_Profil = ? AND DATE(Date_Creation) = ? 
                ORDER BY Date_Creation DESC""",
            (id_profil, str(datetime.date(datetime.now()))),
        )
        return [
            MCT(id=r["ID_MCT"], message=r["Message"],
                id_profil=r["ID_Profil"], date_creation=r["Date_Creation"])
            for r in rows
        ]

    def nettoyage(self, id_profil: int) -> None:
        """Nettoie la MCT en conservant seulement les K entrées les plus récentes
        Args:
            id_profil (int): Identifiant du profil
            conserver (int): Nombre d'entrées à conserver (défaut: 20)
        Returns:
            None
        """
        self._db.execute("DELETE FROM MCT WHERE ID_Profil = ?",(id_profil,))
        