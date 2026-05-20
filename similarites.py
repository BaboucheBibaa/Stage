from bd import Database
from spacy import load

nlp = load("fr_core_news_md")

class Similarites():
    def __init__(self, message: str):
        self.__message = message
        self.__bd = Database()
        self.__getHistorique()
    def __getHistorique(self):
        id =self.__bd.executeFetch("SELECT ID_Conversation FROM Conversation WHERE ID_Profil = 1 ORDER BY Date_Creation DESC LIMIT 10")
        messages = self.__bd.executeFetch("select contenu from messages where id_conversation = ?",(3,))
        for message in messages:
            print(self.__message + " " + message[0])
            print(nlp(self.__message).similarity(nlp(message[0])))
    
def main():
    a = Similarites("bonjour ! ravi de te rencontrer, comment t'appelles tu ?")

if __name__ == "__main__":
    main()