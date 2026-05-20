CREATE TABLE IF NOT EXISTS Profil (
    ID_Profil INT PRIMARY KEY AUTO_INCREMENT,
    Nom VARCHAR(50),
    Prenom VARCHAR(50),
    Date_Naissance DATE
);

CREATE TABLE IF NOT EXISTS Preferences (
    ID_Pref INT PRIMARY KEY AUTO_INCREMENT,
    Sujet TEXT,
    Niveau FLOAT,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_pref_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Sujets_Sensibles(
    ID_Sujet INT PRIMARY KEY AUTO_INCREMENT,
    Sujet TEXT,
    Niveau FLOAT,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_sujets_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Compagnon_Virtuel (
    ID_Compagnon INT PRIMARY KEY AUTO_INCREMENT,
    Modele VARCHAR(100),
    Empathie FLOAT(1,1),
    Humour FLOAT(1,1),
    Professionalisme FLOAT(1,1),
    Patience FLOAT(1,1)
);

CREATE TABLE IF NOT EXISTS Tag(
    ID_Tag INT PRIMARY KEY AUTO_INCREMENT,
    NomTag VARCHAR(50),
    Categorie VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS Tag_Actions(
    ID_Action INT PRIMARY KEY AUTO_INCREMENT,
    Action VARCHAR(70),
    ID_Tag INT NOT NULL,

    CONSTRAINT fk_tagAction_tag FOREIGN KEY (ID_Tag) REFERENCES Tag(ID_Tag) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Conversation(
    ID_Conversation INT PRIMARY KEY AUTO_INCREMENT,
    Sujet TEXT,
    ID_Profil INT NOT NULL,
    Date_Creation DATETIME,
    ID_Compagnon INT NOT NULL,

    CONSTRAINT fk_conversation_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_compagnon FOREIGN KEY (ID_Compagnon) REFERENCES Compagnon_Virtuel(ID_Compagnon)
);

CREATE TABLE IF NOT EXISTS Messages(
    ID_Message INT PRIMARY KEY AUTO_INCREMENT,
    Date_Message DATETIME,
    Contenu TEXT,
    Role_Message ENUM('USER','ASSISTANT'),
    ID_Conversation INT NOT NULL,

    CONSTRAINT fk_message_conversation FOREIGN KEY (ID_Conversation) REFERENCES Conversation(ID_Conversation) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Evenement(
    ID_Event INT PRIMARY KEY AUTO_INCREMENT,
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
    ID_MLT INT PRIMARY KEY AUTO_INCREMENT,
    Donnees JSON,
    Date_Creation DATETIME,
    ID_Profil INT NOT NULL,

    CONSTRAINT fk_mlt_profil FOREIGN KEY (ID_Profil) REFERENCES Profil(ID_Profil) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Est_Associe (
    ID_Message INT NOT NULL ,
    ID_Tag INT NOT NULL,
    PRIMARY KEY (ID_Message, ID_Tag),

    CONSTRAINT fk_EA_message FOREIGN KEY (ID_Message) REFERENCES Messages(ID_Message) ON DELETE CASCADE,
    CONSTRAINT fk_EA_tag FOREIGN KEY (ID_Tag) REFERENCES Tag(ID_Tag)
);

INSERT INTO Profil (Nom,Prenom,Date_Naissance) VALUES ('Delcroix','Lucas','2005-09-11');
INSERT INTO Preferences (Sujet,Niveau,ID_Profil) VALUES ('Jeux vidéos',0.7,1);
INSERT INTO Compagnon_Virtuel (Modele, Empathie, Professionalisme, Patience, Humour) VALUES ('mistral', 0.7, 0.8, 0.9, 0.6);