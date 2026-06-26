# Documentation Technique - Compagnon Virtuel Proactif

## 1. Présentation du projet

Le projet est un compagnon virtuel conversationnel en ligne de commande, développé en Python dans le cadre d'un stage de L2. Il se base sur un LLM local (Ollama) pour engager des conversations personnalisées et déclencher des messages **proactifs** à l'initiative du système, sans attendre un message de l'utilisateur.

Le projet s'inspire de [ComPeer](https://arxiv.org/abs/2407.18064), un système de support proactif entre pairs assisté par IA, dont il reprend les principes de mémoire à deux niveaux et de proactivité pilotée par le contexte.

**Fonctionnalités implémentées :**
- Dialogue conversationnel personnalisé avec mémoire
- Détection automatique d'événements dans les messages utilisateur
- Déclenchement de rappels proactifs avant et après un événement
- Système mémoire à deux niveaux (MCT / MLT) avec filtrage sémantique sur la MCT
- Analyse d'humeur et module d'initiative conversationnelle (non intégré au thread proactif)

---

## 2. Outils utilisés

| Parties | Bibliothèques |
|---|---|
| LLM | [Ollama](https://docs.ollama.com/) Qwen 14b / Qwen 4b |
| Base de données | [MariaDB](https://mariadb.com/docs/connectors/mariadb-connector-python) |
| Analyse sémantique | [spaCy](https://spacy.io/api/doc) `fr_core_news_md` |
| Sorties du LLM | [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/) |
| Configuration | [.venv Python](https://docs.python.org/3/library/venv.html) + [YAML](https://pypi.org/project/PyYAML/) |

*Le projet a été testé sur des versions cloud (gemma4:31b-cloud) pour des questions de rapidité, il est donc conseillé d'utiliser une version cloud si la machine utilisée n'est pas assez performante.*

---

## 3. Architecture générale

Le programme est organisé autour de **trois threads** qui s'exécutent en parallèle :

```
main.py
│
├── Thread principal      boucle_chat()
│       └── DialogueModule.chat()
│               ├── recup_MCT_pertinente()   envoi des données pertinentes au contexte LLM
│               ├── llm.send()               génération de réponse
│               ├── EventModule.detecter()   détection d'événement
│               ├── _add_MCT()               résumé de l'échange et ajout en BDD
│               └── GestionSorties.enqueue() dépôt dans la file
│
├── Thread proactif       DeclenchementProactivite._boucle()
│       └── EventModule.verifier_et_declencher()
│               └── GestionSorties.enqueue()  dépôt dans la file
│
└── Thread affichage      boucle_affichage()
        └── GestionSorties.get()   seul point autorisé à print()
```

**Règle** : aucun module n'appelle `print()` directement, pour des questions de superposition des messages les uns sur les autres. Tous les messages passent par `GestionSorties` (une `queue.Queue`, une file thread-safe), lue exclusivement par le thread d'affichage. Cela évite les collisions de terminal entre les threads.

---

## 4. Modules

### 4.1 `DialogueModule`

**Rôle** : point d'entrée de chaque message utilisateur. Gère le dialogue, la construction du system prompt personnalisé, l'ajout de la mémoire dans la MCT, et la génération du résumé MLT en fin de session puis le sauvegarde.

**Méthodes publiques principales :**

| Méthode | Description |
|---|---|
| `chat(message_user)` | Envoi un message au LLM, filtre la MCT pertinente, lance la détection d'évènement et sauvegarde en MCT |
| `recup_MCT_pertinente(message_user, seuil=0.6)` | Filtre la MCT du jour par similarité cosinus (*) spaCy |
| `sauvegarder_MLT(id_profil)` | Envoit un prompt au LLM et son retour est sauvegardé en MLT |
| `_build_system_prompt(mct_pertinente)` | Conçoit le prompt système avec profil, préférences, sujets sensibles, MCT, MLT |

\* Similarité cosinus: Méthode utilisé pour calculer la similarité entre deux vecteurs de n dimensions en calculant le cosinus de leur angle

**Cycle d'un échange :**

| Étapes | Fonction appelée | Description |
| :--- | :---: | --- |
| 1 | recup_MCT_pertinente() | Calcul de la similarité cosinus entre le message actuel et tous les messages dans la MCT |
| 2 | _build_system_prompt() | On injecte toutes les données formatées dans le prompt |
| 3 | llm.send() | Envoi du prompt système au LLM |
| 4 | EventModule.detecter() | Détection d'évènement dans le message que l'utilisateur envoit. |
| 5 | _sauvegarder_message() | Écriture du message en BDD (traçabilité des échanges LLM / Utilisateur)
| 6 | _add_MCT() | ajout de la mémoire formatée en MCT |
| 7 | Queue system | Affichage du message à l'utilisateur |

---

### 4.2 `EventModule`

**Rôle** : détection d'événements dans les messages utilisateur via un appel LLM structuré, et déclenchement des messages proactifs associés.

**Méthodes publiques principales :**

| Méthode | Description |
|---|---|
| `detecter(message_user)` | Appelle le LLM avec `EventDetectorOutput`, crée les entrées `Evenement` en BDD |
| `verifier_et_declencher()` | Évalue la fenêtre de notification pour chaque événement, retourne les messages proactifs à envoyer |

**Règles de notification (`_REGLES`) :**

Règles de notification définies en tant que constantes au sein du fichier `EventModule.py`.

| Type | Notifications planifiées |
|---|---|
| `rendez-vous` | -1h (rappel avant), +1h (suivi après) |
| `examen` | -13h (veille), -1h (jour J), +2h (suivi) |
| `deadline` | -24h, -2h |
| `maladie` | +2h |
| `bien-etre` | +1h |

**Fenêtre de déclenchement d'un évènement :**

Plutôt qu'un timing précis, le déclenchement est sur un intervalle. Pour une notification `avant`, la fenêtre est `[timing_événement + delta, timing_événement]`. Pour `après`, elle est `[timing_événement, timing_événement + delta]`. Le thread proactif vérifie chaque minute si `datetime.now()` tombe dans cette fenêtre.

---

### 4.3 `BoucleProactivite` (`DeclenchementProactivite`)

**Rôle** : thread de fond qui exécute `EventModule.verifier_et_declencher()` toutes les N minutes (configurable, par défaut : 1 minute). Cette boucle peut idéalement servir à lancer toutes les potentielles vérifications proactives nécessaires dans la vie du projet.

**Arrêt** : `threading.Event`: `stop()` pose le flag, `_boucle()` sort dès que le flag est levé.

---

### 4.4 `ModuleInitiative`

**Rôle** : analyse l'humeur de l'utilisateur à partir de la MCT du jour (`AnalyseHumeurOutput`), puis génère un message d'initiative basé sur la MLT si les conditions sont réunies (`confiance > 0.7` et `envie_interagir >= 0.6`).

> **Statut** : implémenté mais non intégré au thread proactif principal (`BoucleProactivite`). Le module existe dans `modules/ModuleInitiative.py` et est testé via `test.py`. De plus, Le module manque de fonctionnalités afin d'être totalement intégrée. Par exemple, il faudrait gérer le fait de ne pas harceler l'utilisateur avec la même prise d'initiative à chaque fois.

---

### 4.5 `GestionSorties`

**Rôle** : intègre une `queue.Queue` pour gérer tous les affichages qui arrivent depuis des threads distincts.

```python
# Dépôt (thread dialogue ou thread proactif)
file.enqueue("message", source="proactif")

# Lecture (thread affichage uniquement)
item: MessageAffichage = file.get()   # bloquant

# Arrêt
file.stop()   # enfile None pour définir que la file est finie
```

Les messages proactifs sont affichés avec un séparateur visuel distinct pour ne pas se mélanger avec le prompt `Toi :` en cours de saisie.

## 5. Modules externes

Ces modules sont vitaux au bon fonctionnement du projet, mais peuvent être remplaçables très facilement tant que les nouveaux modules intègrent exactement les mêmes fonctionnalités.

### 5.1 `OllamaClient`

**Rôle** : implémentation de `BaseLLMClient` pour Ollama. Gère les sorties texte libre et les sorties structurées Pydantic.

Le modèle par défaut est `gemma4:31b-cloud`, paramétrable dans `config.yaml`.

Une connexion par une autre IA comme Claude / ChatGPT peut aussi très bien faire l'affaire.

---

### 5.2 `Database`

**Rôle** : Connexion à la base de données et initialisation via variables d'environnement (`.env`).

| Méthode | Description |
|---|---|
| `execute(requete, valeurs)` | INSERT / UPDATE / DELETE avec commit automatique, rollback sur erreur |
| `executeFetch(requete, valeurs)` | SELECT, retourne `list[dict]` |

Variables d'environnement requises : `BD_USER`, `BD_MDP`, `BD_HOST`, `BD_NOM`, `BD_PORT`.

On peut ici être en mesure d'utiliser d'autres outils de stockage des données comme un JSON, une base de données vectorielle ou encore un graphe de connaissances au lieu d'une simple base de données.

### 5.3 Classes de données

Le fichier `data.dataclasses.py` contient toutes les classes qui elles mêmes contiennent les méthodes permettant d'utiliser la base de données. Afin de garantir le bon fonctionnement du projet, il est nécessaire des les réimplémenter en fonction du modèle de stockage de données utilisé. 

---

## 6. Modèles de données `data.projectTypes.py`

### 6.1 Types LLM - sorties structurées (héritage via `BaseModel`)

Ces modèles définissent le schéma JSON attendu en sortie du LLM via `format=output_model`.
`output_model` définit un objet qui hérite de `BaseModel` afin de pouvoir utiliser les fonctionnalités de la bibliothèque Pydantic afin de valider le modèle de données.

| Modèle | Champs principaux | Usage |
|---|---|---|
| `EventDetectorOutput` | `type`, `event`, `date`, `importance`, `confidence` | Détection d'événement |
| `ResumeMCTOutput` | `Sujet`, `intention`, `Evenements_Mentionnes`, `Resume_Reponse`, `Entites_Mentionnees`, `language`, `tags` | Résumé d'un échange (MCT) |
| `ResumeMLTOutput` | `date`, `nombre_echanges`, `humeur_generale`, `themes_abordes`, `centres_interets`, `evenements_mentionnes`, `resume_conversation` | Résumé de session (MLT) |
| `AnalyseHumeurOutput` | `emotion_actuelle`, `niveau_stress`, `envie_interagir`, `confiance` | Analyse émotionnelle (InitiativeModule) |

Tous les champs potentiellement absents sont déclarés `Optional[...]` pour éviter que le LLM ne soit contraint de fabriquer une valeur.

### 6.2 Types base de données (dataclasses Python)

| Dataclass | Table BDD | Description |
|---|---|---|
| `Profil` | `Profil` | Identité de l'utilisateur |
| `MCT` | `MCT` | Résumé structuré d'un échange (session courante) |
| `MLT` | `MLT` | Résumé de session persisté (long terme) |
| `Evenement` | `Evenement` | Événement détecté avec timing et statut de notification |
| `Preference` | `Preferences` | Centre d'intérêt avec niveau (0.0–1.0) |
| `SujetSensible` | `Sujets_Sensibles` | Sujet à traiter avec précaution, avec niveau de sensibilité |
| `CompagnonVirtuel` | `Compagnon_Virtuel` | Configuration de personnalité du compagnon |
| `Conversation` | `Conversation` | Session de dialogue horodatée |
| `Message` | `Messages` | Paire message/réponse brute |

### 6.3 Schéma de la base de données

Profil (<u>ID_Profil</u>, Nom, Prenom, Date_Naissance)

Preferences (<u>ID_Pref</u>, Sujet, Niveau, **ID_Profil**)

Sujets_Sensibles (<u>ID_Sujet</u>, Sujet, Niveau, **ID_Profil**)

Compagnon_Virtuel (<u>ID_Compagnon</u>,Modele,Empathie,Humour, Professionalisme, Patience)

Conversation(<u>ID_Conversation</u>, Sujet, **ID_Profil**, Date_Creation, **ID_Compagnon**)

Messages (<u>ID_Message</u>, Date_Message, Msg_User, Rep_Assistant, **ID_Conversation**)

Evenement (<u>ID_Event</u>, Contexte, Timing, Statut, **ID_Profil**, Type_Evenement, Importance, Timing_Evenement)

MLT (<u>ID_MLT</u>, Nombre_Echanges, Humeur_Generale, Themes_Abordes, Centres_Interets,Evenements,Mentionnes, Resume_Conversation, Date_Creation, **ID_Profil**)

MCT (<u>ID_MCT</u>, Date_Creation, **ID_Profil**, Sujet, Intention, Evenements_Mentionnes, Resume_Reponse, Entites_Mentionnees, Langage, Tags)

## Mémoire du Compagnon Virtuel

### 7.1 Mémoire Court Terme (MCT)

**Portée** : session courante. Ici, une session courante = une exécution du programme. Cependant, dans un cadre idéal, une session courante pourrait être une journée. Ainsi, le soir, le Compagnon Virtuel rentre en phase de "réorganisation des données".

**Contenu** : après chaque échange, un appel LLM génère un résumé structuré (`ResumeMCTOutput`) stocké en BDD. Ce résumé contient le sujet, l'intention de l'utilisateur, les entités mentionnées (entités = Noms / Lieux / Animaux / etc...), les événements, les tags (mots clés de la conversation), et un résumé de la réponse du compagnon.

**Filtrage sémantique** : avant injection dans le prompt système, `recup_MCT_pertinente()` calcule la similarité cosinus entre le message courant et chaque entrée MCT (champ `resume_reponse`) via spaCy. Seules les entrées dépassant le seuil de **0.6** sont injectées.

**Cycle de vie** : la MCT est vidée (`DonneesMCT.vider()`) lors de la sauvegarde MLT en fin de session.

### 7.2 Mémoire Long Terme (MLT)

**Portée** : persistante. N'est jamais censée se supprimer.

**Contenu** : à la déconnexion (`sauvegarder_MLT()`), toute la MCT du jour est résumée par le LLM (via le type structuré `ResumeMLTOutput`) et stockée comme une entrée MLT structurée (humeur générale, thèmes, centres d'intérêts, événements mentionnés, résumé).

> **Fonctionnalité souhaitée mais non implémentée** : contrairement à la MCT, la MLT n'est pas filtrée sémantiquement avant injection. Toutes les entrées passées sont envoyées au LLM, ce qui peut surcharger le contexte. ComPeer résout ce problème par une vectorisation des données afin de pouvoir faire un calcul de similarité cosine. Cependant, cela implique que chaque donnée de notre mémoire long terme soit "vectorisée". L'ajout d'un filtrage MLT par `sentence-transformers` semble être la meilleure approche pour avoir un filtrage pertinent de la mémoire long terme.

### 7.3 Utilisation de la mémoire dans le prompt système

Le system prompt (`prompts/system_prompt.txt`) injecte la mémoire de façon implicite :

> *"Quand le message de {prenom} a un lien sémantique avec un fait de ta mémoire long terme ou court terme, intègre ce fait NATURELLEMENT dans ta réponse, sans jamais dire que tu 'te souviens' ou que c'est dans ta mémoire."*

Le compagnon n'expose jamais explicitement ses sources mémoire à l'utilisateur.

De plus, le system prompt permet au LLM de pouvoir réutiliser cette mémoire afin d'enrichir le contexte actuel (lier le contenu d'une session passée avec la session actuelle)

---

## 8. Proactivité événementielle

### 8.1 Détection

Appelée dans `DialogueModule.chat()` après chaque échange, `EventModule.detecter()` soumet le message utilisateur au LLM avec le prompt `event_detector.txt`.

Le prompt est restrictif, il impose des conditions précises avant de valider un événement :
1. Une action planifiée doit être présente (rendez-vous, examen, deadline, soin)
2. Une date ou délai précis doit être mentionné
3. Un rappel doit avoir une valeur concrète pour l'utilisateur

Des exemples négatifs sont explicitement listés dans le prompt pour limiter les faux positifs. En cas de doute, le prompt demande de retourner `null` sur tous les champs.

**Seuils de validation** :
- `confidence < 0.6`,  rejeté
- `importance < 0.3`, rejeté
- `date` absent, rejeté

Pour chaque événement validé, **une entrée `Evenement` est créée par notification** (selon `_REGLES`), avec `timing_notification = "avant"` ou `"après"`.

### 8.2 Déclenchement (via un thread proactif)

Toutes les N minutes, `DeclenchementProactivite` appelle `verifier_et_declencher()`. Pour chaque événement en statut `Planifié` avec `Importance ≥ 0.3`, la méthode évalue si `datetime.now()` tombe dans la fenêtre de notification :

```
Notification "avant" :
    debut = timing_événement + delta (ex: -1h)
    fin   = timing_événement
    se déclenche si debut ≤ now ≤ fin

Notification "après" :
    debut = timing_événement
    fin   = timing_événement + delta (ex: +1h)
    se déclenche si debut ≤ now ≤ fin
```


Quand une notification se déclenche, `__declencher()` :
1. Sélectionne le prompt adapté (`event_user_avant.txt` ou `event_user_après.txt`)
2. Appelle le LLM avec le contexte (profil, MCT du jour, MLT, temps restant)
3. Met à jour le statut de l'événement à `Déclenché` en BDD
4. Retourne le message généré

Le message est ensuite enfilé dans `GestionSorties` avec `source="proactif"` pour un affichage distinct.

---

## 9. Prompts

Tous les prompts sont dans `prompts/` et chargés via `Path.read_text()`. Les variables sont injectées par `.format(**contexte)`.

| Fichier | Rôle |
|---|---|
| `system_prompt.txt` | Identité du compagnon, traits de personnalité, préférences, sujets sensibles, MCT, MLT, consignes d'utilisation de la mémoire |
| `event_detector.txt` | Détection d'événement - critères stricts, exemples positifs et négatifs, format JSON attendu |
| `mct/mct_resume_system.txt` | Résumé structuré d'un échange pour la MCT |
| `mlt/mlt_resume_system.txt` | Résumé de session pour la MLT (3ème personne, 3–5 phrases) |
| `proactive/event_system.txt` | Prompt système pour les messages proactifs événementiels |
| `proactive/event_user_avant.txt` | Prompt utilisateur - rappel avant un événement |
| `proactive/event_user_après.txt` | Prompt utilisateur - suivi après un événement |
| `initiative/analyse_humeur_system.txt` | Analyse émotionnelle de la MCT (stress, envie d'interagir, confiance) |
| `initiative/prompt_initiative_system.txt` | Prise d'initiative - extraction d'un sujet MLT pour relancer la conversation |

---

## 10. Configuration

Données du LLM modifiables directement dans `config.yaml`

**`.env`**
```
BD_USER=...
BD_MDP=...
BD_HOST=...
BD_NOM=...
BD_PORT=...
```

---

## 11. Installation et lancement

**Prérequis** : Python 3.12, Ollama installé et actif, une base de données MariaDB configurée.

```powershell
# 1. Créer un environnement virtuel
python -m venv .venv

# 2. Activer l'environnement virtuel
.venv/Scripts/activate.ps1

# 3. Installer les bibliothèques requises
pip install -r requirements.txt

# 4. Créer le fichier .env avec les données de la BDD

# 5. Installer un LLM via Ollama (ici, ce sera une version cloud)
ollama run gemma4:31b-cloud

# 6. Lancer le compagnon
python main.py
```

---

## 12. Manquements connus et perspectives d'amélioration

Tous les points suivants sont rangés par importance, du plus important, à implémenter en priorité, au moins important.

### 12.1 MLT sans filtrage sémantique

Le contexte envoyé au LLM grossit au fil du temps sans avoir de filtrage intégré. Concrètement, le LLM reçoit des évènements qu'il n'est pas pertinent pour lui d'avoir en mémoire lors de la génération de la réponse.

> Solution proposée : Refactoriser la mémoire long terme. L'idée serait, au lieu de regrouper la mémoire long terme en différents attributs comme actuellement, comme l'humeur actuelle, on regroupe tout sous forme de grands thèmes, comme un thème "Sports", un thème "Musique", un thème "Emotions" etc... Cela permettrait d'avoir une sorte de classification intégrée au sein de notre mémoire. On peut voir cela comme un classeur, avec un compartiment pour une catégorie spécifique. Toute la difficulté résiderait donc dans le fait d'établir des catégories suffisament larges (ou, à l'inverse, des catégories suffisament précises) afin de minimiser les erreurs de la part du LLM, afin que tout soit stocké à la bonne place. Un bon début serait éventuellement d'utiliser les tags (mots clés) actuellement présents dans la MLT afin de les restreindre et de proposer une table à part dans la base de données pour chacun de ces tags (donc les tags seraient uniquement des tags connus et définis)

### 12.2 `ModuleInitiative` non intégré au système actuel.

**Problème 1 :** Le LLM ne peut pas prendre d'initiative et relancer une conversation actuellement. Cependant, la fonctionnalité est en partie implémentée (de façon simple) dans `ModuleInitiative.py` en déterminant si l'utilisateur a envie d'interaction et si l'analyse du LLM est fiable ou non.<br>
**Problème 2 :** Le système est encore fragile car, tel qu'il est fait actuellement, il est très probable que le LLM relance une conversation à chaque fois que le thread va s'exécuter (les critères sur l'envie d'interaction de l'utilisateur et la fiabilité du message sont trop peu restrictifs).
De plus, le LLM peut relancer indéfiniment sur un sujet et il n'ajuste jamais l'importance d'un sujet.


>**Solution 1**: Intégrer davantage de critères de prise d'initiative, notamment une durée depuis le dernier message, afin de ne pas avoir le soucis de prise d'initiative à chaque exécution du thread.<br>**Solution 2** : Il faudrait aussi intégrer un concept de valeur d'importance sur chaque évènement que le LLM va sélectionner pour faire une prise d'initiative. Par exemple, pour un projet qui est en cours, la valeur d'importance doit être élevée et le LLM peut être en mesure de faire des relances plus souvent. Par contre, pour un projet qui est fini, on doit pouvoir avoir mettre une valeur d'importance nulle, afin que le LLM ne relance plus jamais sur ce projet. Mais il ne faut pas non plus supprimer ce projet de la mémoire, il faut toujours l'avoir en tête afin que le LLM puisse toujours savoir que l'utilisateur a fait un projet.

### 12.3 Proactivité basée sur l'habitude

Actuellement, cette fonctionnalité n'est pas du tout intégrée au projet. Cela consisterait à intégrer une détection d'habitudes au sein du projet, par exemple "promener le chien dehors" avec une heure "9 heures", et éventuellement un jour, "lundi". Cela sous-entendrait que l'utilisateur promène son chien tous les lundis à 9h. Le système devrait donc tourner toutes les N heures (ou minutes) afin de déterminer si l'habitude a été détectée. Il faudrait analyser la conversation actuelle (donc la MCT) afin de déterminer si, à une heure précise, l'habitude a été détectée ou non.

> Solution proposée: Intégrer une table "Habitude", qui permettrait de stocker une habitude. Tout l'enjeu serait de déterminer comment stocker une habitude sans pour autant exagérer sur l'ajout de l'habitude en mémoire. Concrètement, une idée proposée actuellement serait de laisser le LLM ajouter ce qu'il souhaite comme habitude qu'il détermine, le tout avec une valeur d'importance de cette habitude. Cette valeur augmenterait ou descendrait en fonction de si elle cette habitude est répétée ou non à la date indiquée dans l'enregistrement de la base. Cependant, cette solution engendrerait énormément de données non utilisées au sein de la BD. Il faudrait donc intégrer un système de nettoyage de la mémoire derrière. Ce système s'exécuterait à chaque fin de conversation. Le concept est abordé plus en détails plus bas.

### 12.4 Sauvegarde de la mémoire sous forme de graphe de connaissances

Le concept de graphe de mémoire est abordé notamment dans le cas de Mem0, un système de mémoire utilisable notamment dans des agents conversationnels avec un système de mémoire long terme. Concrètement, on utiliserait des graphes afin d'associer des entitées (sommets du graphes) entre eux, via des associations (arêtes du graphe), afin d'avoir des connexions entre entités, par exemple: Utilisateur A (sommet du graphe) aime se promener (arête du graphe) avec son chien (sommet du graphe). Ce système est beaucoup plus pertinent qu'une mémoire relationnelle telle qu'elle est implémentée actuellement car beaucoup plus humaine et les possibilités sont beaucoup plus importantes.

> De plus, il faudrait aussi pouvoir hiérarchiser les données entre elles, par exemple, je peux aimer la musique et l'escalade, mais je peux préférer l'escalade, il faut pouvoir prendre cette hiérarchie en compte. Se renseigner sur l'implémentation de Neo4J, qui semble être la solution à la bonne échelle pour cela, mais nécessite de préparer un serveur pour cela. Certains modèles de graphes de connaissances ne proposent pas par eux-mêmes une solution persistante. Neo4J et Kuzu semblent être des options intéressantes, les autres options ne proposent pas de persistance des données. Cependant, Kuzu propose d'embarquer directement le graphe de données au sein de la machine, donc à moins d'avoir un serveur à part pour héberger une base de données Neo4J, Kuzu semble être bien.

### 12.5 Nettoyage de la mémoire

Tout comme un humain, le système a besoin de nettoyer sa mémoire afin de ne pas garder des informations en double ou des informations inutiles (comme les habitudes détectées et non utilisées si la solution d'habitude est implémentée comme elle est décrite au dessus). Le système de nettoyage de la mémoire permettrait aussi de regrouper les éléments de la mémoire long terme entre eux. Actuellement, c'est complexe a implémenter avec le système de mémoire long terme qui n'est pas basée sur des thèmes (voir la solution en 12.1), étant donné que la mémoire long terme n'est pas organisée. Mais avec une mémoire long terme basée sur les thèmes, cela peut s'implémenter en détectant des choses redondantes et en les fusionnant entre elles. Avec une mémoire sous forme de graphes, cela semble pouvoir se faire en fusionnant des sommets entre eux.
> Solution : Implémenter une logique de session. Comme dit sur le [point 7.1](#71-mémoire-court-terme-mct), une session actuelle correspond au cycle de vie du programme, donc durant le temps de son exécution. Dans le cadre d'un projet de grande envergure, le cerveau du système tournerait en permanence, en journée afin de pouvoir être un agent conversationnel, et le soir afin de pouvoir être un agent d'organisation de mémoire, afin de restructurer la mémoire de façon cohérente et exploitable. Une journée = un cycle de MCT, une fois que la journée est finie, on restructure la MCT de sorte à avoir une MLT (peu importe la forme, que ce soit géré par thèmes via une BD ou par graphe de connaissances)

### 12.6 Mise à jour dynamique de la mémoire du profil

L'idée serait de laisser au LLM la possiblité de mettre à jour lui-même le profil de l'utilisateur en fonction du temps. Imaginons que l'utilisateur possède dans ses préférences "cinéma" et qu'un jour il dit au compagnon virtuel qu'il a été voir un film qu'il l'a traumatisé et qu'il n'ira plus jamais au cinéma de sa vie. L'idéal serait que le compagnon virtuel mette à jour sa mémoire sur l'utilisateur, en remettant à jour le fait qu'il n'aime plus le cinéma.
> Cependant, cela ne laisserait-il pas trop de libertés au LLM ? Le fait qu'il puisse lui-même déterminer si un profil doit être modifié ou non ne peut-il pas conduire à des hallucinations ? Sur une donnée aussi importante que le profil utilisateur, cela doit être quelque chose à prendre en compte. De plus, est-ce que la MLT en elle-même ne consitue-elle pas déjà une sorte de profil dynamique de l'utilisateur ? Le soucis résiderait dans le fait que l'on souhaite filtrer la mémoire long terme transmise au LLM (voir le [point 12.1](#121-MLT-sans-filtrage-sémantique)), donc il faudrait filtrer la mémoire long terme à chaque message par rapport à la pertinence sémantique entre le message envoyé par l'utilisateur, mais il faut tout de même prendre les données sauvegardées par le LLM qui concerneraient le profil ? (si on change la façon dont fonctionne la mémoire long terme pour partir sur un concept de "thèmes", voir le [point 12.1](#121-MLT-sans-filtrage-sémantique).)

### 12.7 Renforcer la personnalité du LLM

Actuellement, la façon dont la personnalité du LLM est gérée se base uniquement sur 4 émotions, c'est peu, mais cela permet de tester sa façon de changer de ton par rapport au degré qu'on attribue à une émotion particulière. Afin de rendre cela plus cohérent, il faudrait idéalement réutiliser le système de préférences et de sujets sensibles, tout comme un humain (l'objectif ici est de modéliser un compagnon virtuel étant le plus humain possible)

### 12.8 Concevoir un dataset

Dans le cadre d'un LLM, on parle même de **golden dataset**, il s'agit d'un jeu de données conçu par l'humain afin de tester nous-même la fiabilité du LLM. L'idée serait donc de concevoir cela pour chacune des phases où un appel LLM est requis (sauvegarde en MCT / MLT, détection d'évènement, prise d'initiative) afin de vérifier la fiabilité du modèle. L'intérêt de ce dataset est de vérifier que, si on décide de changer de modèle (pour une version locale, par exemple), on puisse appliquer des tests sur ce modèle pour vérifier sa fiabilité.

### 12.9 Prise en compte du feedback utilisateur dans le cas des actions proactives

Si l'utilisateur dit au compagnon virtuel qu'un message proactif en particulier (que ce soit une prise d'initiative ou un rappel d'évènement) n'était pas pertinent sur un moment donné, l'idée serait que le compagnon puisse lui même se "restreindre" afin de proposer uniquement des messages qui pourraient être pertinents pour l'utilisateur.

> Solution proposée : Dans le cas de la détection d'évènements, si le LLM fait des rappels sur des évènements pas pertinents, il faudrait augmenter le seuil d'importance nécessaire au sein de la détection d'évènement. Lors d'une prise d'initiative, cette même idée pourrait être utilisée.

### 12.10 Annulation d'évènements

Actuellement, le système de détection d'évènements est fonctionnel et hallucine très très peu. Cependant, il n'y a pas la possibilité de dire à notre compagnon virtuel si on annule un évènement qui est prévu ou non. Par exemple, si je lui dis que j'ai un examen à 16h mais qu'au final il est annulé, ce serait peu réaliste qu'il envoie tout de même le message proactif pour prévenir de l'examen.

> Solution : La solution m'a l'air complexe à implémenter, il faudrait que le LLM puisse lui-même détecter le fait que l'utilisateur annule un évènement prévu. Cela laisse une grande part à l'hallucination. Mais une piste serait déjà de faire une analyse sémantique entre le message de l'utilisateur et chaque contexte d'évènement sauvegardé.
