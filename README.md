# Compagnon Virtuel

Un système de dialogue IA personnalisé avec mémoire court/long terme, détection d'événements et gestion adaptée des sujets sensibles.

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Fonctionnalités principales](#fonctionnalités-principales)

---

## Vue d'ensemble

Ce projet crée un **compagnon virtuel intelligent** capable de:

- **Dialoguer** avec l'utilisateur via un LLM local (Ollama)
- **Mémoriser le contexte** avec une mémoire court terme (MCT) et long terme (MLT)
- **Personnaliser les réponses** selon les préférences et sujets sensibles de l'utilisateur
- **Détecter des événements** importants dans les conversations
- **Stocker les données** en base de données MariaDB

### Caractéristiques clés

| Fonctionnalité | Description |
|---|---|
| **LLM Local** | Ollama (Mistral, Llama, etc.)  |
| **Mémoire** | MCT (Messages de la journée) + MLT (résumés de sessions) |
| **Personnalisation** | Préférences utilisateur + sujets sensibles + traits du compagnon |
| **Persistance** | Base de données MariaDB pour toutes les données |

### Modules principaux

| Module | Rôle |
|--------|------|
| **DialogueModule** | Orchestre les dialogues, gère l'historique et les prompts |
| **DetectionEvent** | Détecte les événements importants via le LLM |
| **prompt_loader** | Construit les prompts système personnalisés |
| **resume.py** | Génère des résumés pour MCT et MLT |
| **dataclasses.py** | Classes de données (couche d'accès BD) |
| **LLMBase** | Interface abstraite pour fournisseurs LLM |

---

## Installation

### Prérequis

- **Python 3.10+**
- **MariaDB** (ou MySQL compatible) en cours d'exécution
- **Ollama** installé et en cours d'exécution

### Étape 1: Créer un environnement virtuel

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Étape 2: Installer les dépendances

```bash
pip install -r requirements.txt
```

**Dépendances:**
- `pyyaml==6.0.1` - config YAML
- `python-dotenv==1.0.0` - Variables d'environnement
- `ollama==0.1.32` - LLM Ollama
- `mariadb==1.1.10` - BD MariaDB

### Étape 4: Démarrer les services externes

#### MariaDB
```bash
# Windows (si installé comme service)
net start MySQL80

# Ou utiliser Docker
docker run -d --name mariadb -e MYSQL_ROOT_PASSWORD=110905 -p 3306:3306 mariadb:latest
```

#### Ollama
```bash
ollama serve
# Dans un autre terminal, télécharger un modèle:
ollama pull mistral
```

---

## ⚙️ Configuration

### Fichier `.env`

Créez un fichier `.env` à la racine avec:

```env
BD_USER=root
BD_MDP=110905
BD_HOST=localhost
BD_PORT=3306
BD_NOM=Stage
```

### Fichier `config.yaml`

```yaml
llm:
  model: mistral          # Modèle Ollama à utiliser
  temperature: 0.7        # Créativité (0.0-1.0)
  max_tokens: 512         # Longueur max de réponse

companion:
  name: "Apagnan"         # Nom du compagnon
  language: "fr"          # Langue (fr/en)
  proactive_interval_minutes: 60  # Intervalle de proactivité
```

### Base de données

Exécutez les scripts SQL:

```bash
# Créer les tables
mysql -u root -p Stage < db/create.sql

# Nettoyer les données (optionnel)
mysql -u root -p Stage < db/delete.sql
```

---

## Utilisation

### Démarrer le compagnon

```bash
python main.py
```

### Commandes de chat

| Commande | Effet |
|----------|-------|
| `quit` | Quitter et sauvegarder la session (MLT) |
| `Ctrl+C` | Arrêt forcé |
| `Ctrl+D` (Linux) | Fin d'entrée |

---

## Fonctionnalités principales

### 1. Dialogue personnalisé

Le compagnon adapte ses réponses selon:

- **Préférences**: Centres d'intérêt de l'utilisateur
- **Sujets sensibles**: Traitement délicatesse selon le sujet
- **Traits du compagnon**: Empathie, humour, professionnalisme, patience

### 2. Mémoire Court Terme (MCT)

- Stocke **tous les messages** de la session
- Résumé automatique via LLM à chaque échange
- Nettoyée en fin de session

**Exemple de MCT:**
```
- 16:32:42 - Utilisateur a demandé des conseils sur programmation
- 16:33:15 - Assistant a recommandé Python comme langage d'apprentissage
- 16:34:20 - Utilisateur a confirmé son intérêt pour web development
```

### 3. Mémoire Long Terme (MLT)

- Résumé permanent des **connaissances sur l'utilisateur**
- Régénérée à chaque fin de session
- Persiste entre les sessions

**Exemple de MLT:**
```
Alice s'intéresse à:
- Programmation (Python, JavaScript)
- Intelligence artificielle et ML
- Développement web

Points importants:
- Préfère apprendre par la pratique
- Très intéressée par les projets réels
- Étudiante en informatique
```

### 4. Détection d'événements

Le système détecte automatiquement:

- **Anniversaires** mentionnés
- **Problèmes de santé**
- **Changements professionnels**
- **Voyages prévus**

Les événements sont stockés et utilisables pour des actions proactives.