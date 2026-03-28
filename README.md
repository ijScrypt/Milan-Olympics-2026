<div align="center">

# Milano 2026: NoSQL Analytics Dashboard

![University Logo](screenshots/university_logo.png) 
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) 
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white) 
![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white) 
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white) 
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

</div>

## Demo

https://github.com/user-attachments/assets/f26d1df0-c75f-4d38-b9db-68bb1854df22

---

## Prérequis

Assurez-vous que les éléments suivants sont installés et en cours d'exécution sur votre machine :

1.  **Python 3.8+**
2.  **Serveur MongoDB** (Port par défaut : `27017`)
3.  **Neo4j Desktop ou Server** (Port Bolt par défaut : `7687`)

---

## Installation et Configuration

### 1. Clonage et Environnement
Clonez le dépôt et configurez un environnement virtuel Python :

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sous Windows :
venv\Scripts\activate
# Sous Unix ou MacOS :
source venv/bin/activate
```

### 2. Installation des Dépendances
Installez toutes les bibliothèques requises pour le backend Flask et le traitement des données :

```bash
pip install -r requirements.txt
```

### 3. Configuration
Créez un fichier `.env` à la racine du projet et configurez vos identifiants de base de données :

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=milano2026
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=votre_mot_de_passe
```

---

## Initialisation de la Base de Données (Seeding)

L'application nécessite des données initiales pour alimenter les graphiques et les relations.

*   **Seeding Automatique** : Lors du premier lancement du backend (`api.py`), le système vérifie si MongoDB est vide. Si c'est le cas, il générera automatiquement environ 30 utilisateurs et 200 tweets via le `SeedService`.
*   **Re-seed Manuel** : Vous pouvez déclencher une réinitialisation complète des données directement depuis l'interface du Dashboard via le bouton **"Re-seed"** dans la barre de navigation.

---

## Lancement de l'Application

Suivez ces étapes pour lancer le dashboard :

### Étape 1 : Démarrer l'API Backend
Le serveur Flask gère les connexions aux bases de données et exécute les requêtes NoSQL.

```bash
python api.py
```
> [!TIP]
> L'API sera accessible sur `http://127.0.0.1:5000/api`.

### Étape 2 : Ouvrir le Dashboard
Le frontend est construit en HTML/JS/CSS pur. Comme il s'agit d'un client autonome :

1.  Localisez le fichier `dashboard.html` dans le dossier racine.
2.  Ouvrez-le directement dans votre navigateur Web (Chrome, Edge ou Firefox recommandé).
3.  Vérifiez que l'indicateur d'état en haut à droite affiche **"Connecté"**.

---

## Structure du Projet

| Fichier | Description |
| :--- | :--- |
| `api.py` | **Point d'entrée principal**. API REST Flask exposant tous les points de terminaison. |
| `dashboard.html` | Conteneur principal de l'interface utilisateur pour la plateforme d'analyse. |
| `services_mongo.py` | Logique métier pour toutes les agrégations MongoDB et les opérations CRUD. |
| `services_neo4j.py` | Logique pour l'import des relations et les requêtes Cypher complexes. |
| `seed.py` | Moteur de génération de données utilisant la bibliothèque `Faker`. |
| `config.py` | Gestion des variables d'environnement et paramètres globaux. |

---

## Fonctionnalités Disponibles
*   **Tableau de bord KPI** : Compteurs en temps réel pour les utilisateurs, les tweets et les tags populaires.
*   **Graphes de Réseau** : Visualisation interactive des followers, retweets et fils de discussion via `vis-network`.
*   **Moteur de Requêtes NoSQL** : Onglet dédié pour exécuter 16 requêtes analytiques spécifiques sur les deux moteurs de base de données.
*   **Gestion CRUD** : Interface directe pour Créer, Lire, Mettre à jour et Supprimer des documents et des utilisateurs.

---
<div align="center">
  <i>Technical Readme - Projet NoSQL Milano 2026</i>
</div>
