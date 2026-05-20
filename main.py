from compagnon import CompagnonVirtuel
from data.conversation import GestionConversation
def main():
    compagnon = CompagnonVirtuel(1,1)
    liste_messages = []
    i = 0
    conv = compagnon.commencer_conversation("Test")
    while 1:
        message = input("Message : ")
        #envoi du message au llm
        reponse = compagnon.envoyer_message(message)
        print(reponse)
        #ajout de la réponse dans un "cache"
        liste_messages.append(reponse)
        #stockage du message courant et ancien message pour analyse sémantique pour déterminer un changement de conversation ou non
        if i > 0:
            ancien_message = liste_messages[i-1]
            message_actuel = liste_messages[i]
            if GestionConversation.switch_conv(ancien_message,message_actuel):
                conv = compagnon.commencer_conversation("Nouveau"+i)
            #utile juste pour stocker dans le tableau
        i+= 1
        
if __name__ == "__main__":
    main()