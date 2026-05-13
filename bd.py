from mariadb import connect
from dotenv import load_dotenv
from os import getenv

load_dotenv()

class Database():
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
    def execute(self, requete: str, valeurs=None):
        self.__cursor.execute(requete, valeurs)
        self.__conn.commit()
    def executeFetch(self,requete: str, valeurs=None):
        self.__cursor.execute(requete,valeurs)
        self.__conn.commit()
        result = self.__cursor.fetchall()
        return result
    def close(self):
        self.__conn.close()