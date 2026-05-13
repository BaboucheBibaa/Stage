CREATE TABLE IF NOT EXISTS Profil (
    ID_Profil INT PRIMARY KEY,
    Nom VARCHAR(50),
    Prenom VARCHAR(50),
    Date_Naissance DATE
);

CREATE TABLE IF NOT EXISTS Preferences (
    ID_Pref INT PRIMARY KEY,
    Sujet TEXT,
    Niveau FLOAT,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_pref_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Sujets_Sensibles(
    ID_Sujet INT PRIMARY KEY,
    Sujet TEXT,
    Niveau FLOAT,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_sujets_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Compagnon_Virtuel (
    ID_Compagnon INT PRIMARY KEY,
    Personnalite TEXT,
    Modele VARCHAR(100)

);

CREATE TABLE IF NOT EXISTS Tag(
    ID_Tag INT PRIMARY KEY,
    NomTag VARCHAR(50),
    Categorie VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS Tag_Actions(
    ID_Action INT PRIMARY KEY,
    Action VARCHAR(70),
    ID_Tag INT NOT NULL,

    CONSTRAINT fk_tagAction_tag FOREIGN KEY (ID_Tag) REFERENCES Tag(ID_Tag)
);

CREATE TABLE IF NOT EXISTS Conversation(
    ID_Conversation INT PRIMARY KEY,
    Sujet TEXT,
    ID_Profil INT NOT NULL,
    ID_Compagnon INT NOT NULL,

    CONSTRAINT fk_conversation_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_compagnon FOREIGN KEY (ID_Compagnon) REFERENCES Compagnon_Virtuel(ID_Compagnon)
);

CREATE TABLE IF NOT EXISTS Messages(
    ID_Message INT PRIMARY KEY,
    Date_Message DATETIME,
    Contenu TEXT,
    Role_Message ENUM('USER','ASSISTANT'),
    ID_Conversation INT NOT NULL,

    CONSTRAINT fk_message_conversation FOREIGN KEY (ID_Conversation) REFERENCES Conversation(ID_Conversation) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Evenement(
    ID_Event INT PRIMARY KEY,
    Titre VARCHAR(70),
    Date_Event DATETIME,
    Statut ENUM('Planifié','En Cours','Terminé'),
    Contexte TEXT,
    ID_Profil INT NOT NULL,
    ID_Tag INT NOT NULL,

    CONSTRAINT fk_event_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE,
    CONSTRAINT fk_event_tag FOREIGN KEY (ID_Tag) REFERENCES Tag(ID_Tag)
);

CREATE TABLE IF NOT EXISTS MLT(
    ID_MLT INT PRIMARY KEY,
    Donnees JSON,
    Date_Creation DATETIME,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_mlt_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Est_Associe (
    ID_Message INT NOT NULL,
    ID_Tag INT NOT NULL,
    PRIMARY KEY (ID_Message, ID_Tag),

    CONSTRAINT fk_EA_message FOREIGN KEY (ID_Message) REFERENCES Messages(ID_Message) ON DELETE CASCADE,
    CONSTRAINT fk_EA_tag FOREIGN KEY (ID_Tag) REFERENCES Tag(ID_Tag)
);

