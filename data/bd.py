from mariadb import connect
from dotenv import load_dotenv
from os import getenv

load_dotenv()

class Database():
    """Classe permettant de gérer les fonctionnalités de base dans une base de données MariaDB
        - Passage des paramètres de connexion via les variables d'environnement locales du projet:
            BD_USER: nom d'utilisateur de la base
            BD_MDP: mot de passe de la base
            BD_HOST: hôte
            BD_NOM: Nom de la base
            BD_PORT: Port de connexion de la base
            
            Connexion automatique à l'initialisation
            Fermeture du curseur à la destruction de l'objet
        """
    def __init__(self):
        self.db_config = {
        'user': getenv("BD_USER"),
        'password': getenv("BD_MDP"),
        'host': getenv("BD_HOST"),
        'database': getenv("BD_NOM"),
        'port': int(getenv("BD_PORT"))
        }
        self.__conn = connect(**self.db_config)
        self.__cursor = self.__conn.cursor(dictionary=True)
    def __del__(self):
        self.close()
    def execute(self, requete: str, valeurs: tuple = None) -> bool:
        """Exécute une requête SQL qui ne doit pas retourner de résultat.

        Args:
            requete (str): Requête SQL à exécuter (mettre des ? pour bind les paramètres)
            valeurs (tuple, optional): Valeurs à passer en paramètres. Defaults to None.
        """
        if self.__cursor.execute(requete, valeurs):
            self.__conn.commit()
            return True
        return False
        
    def executeFetch(self,requete: str, valeurs=None) -> list[tuple]:
        """Exécute une requête qui doit retourner un ou plusieurs résultats.

        Args:
            requete (str): Requête SQL à exécuter (mettre des ? pour bind les paramètres)
            valeurs (tuple, optional): tuple de valeurs à passer dans la requête. Defaults to None.

        Returns:
            list[tuple]: Résultats de la requête, renvoie même une liste s'il n'y a qu'un seul enregistrement comme résultat
        """
        self.__cursor.execute(requete,valeurs)
        self.__conn.commit()
        result = self.__cursor.fetchall()
        return result
    def close(self):
        self.__conn.close()