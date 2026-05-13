from toTag import ToTag
from bd import Database

def main():
    while 1:
        message= input("Saisir un message : ")
        tagsList = ToTag(message)
        print(tagsList.message)
        print("Message réduit : " + tagsList.message_reduit)

if __name__ == "__main__":
    main()