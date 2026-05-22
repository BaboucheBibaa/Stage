from compagnon import CompagnonVirtuel
from data.conversation import GestionConversation
def main():
    compagnon = CompagnonVirtuel(1,1)
    compagnon.commencer_conversation("Test")
    while 1:
        message = input("Message : ")
        #envoi du message au llm
        reponse = compagnon.envoyer_message(message)
        print(reponse)  
        
if __name__ == "__main__":
    main()