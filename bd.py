import mariadb
# Détails de la connexion à la base de données
db_config = {
    'user': 'root',
    'password': '110905',
    'host': 'localhost',
    'database': 'Stage',
    'port': 3306  # Port standard pour MariaDB
}
# Établir la connexion
conn = mariadb.connect(**db_config)
# Création d'un curseur pour l'exécution des requêtes
cursor = conn.cursor()
