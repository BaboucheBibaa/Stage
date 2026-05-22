from mariadb import connect
from dotenv import load_dotenv
from os import getenv

load_dotenv()

class Database():
    """Classe permettant de gérer les fonctionnalités de base dans une base de données MariaDB
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
        self.__cursor = self.__conn.cursor()
    def __del__(self):
        self.close()
    def execute(self, requete: str, valeurs: tuple = None):
        """Exécute une requête SQL qui ne doit pas retourner de résultat.

        Args:
            requete (str): Requête SQL à exécuter (mettre des ? pour bind les paramètres)
            valeurs (tuple, optional): Valeurs à passer en paramètres. Defaults to None.
        """
        self.__cursor.execute(requete, valeurs)
        self.__conn.commit()
        
    def executeFetch(self,requete: str, valeurs=None):
        """Exécute une requête qui doit retourner un ou plusieurs résultats.

        Args:
            requete (str): Requête SQL à exécuter (mettre des ? pour bind les paramètres)
            valeurs (tuple, optional): tuple de valeurs à passer dans la requête. Defaults to None.

        Returns:
            list[tuple]: Résultats de la requête
        """
        self.__cursor.execute(requete,valeurs)
        self.__conn.commit()
        result = self.__cursor.fetchall()
        return result
    def close(self):
        self.__conn.close()