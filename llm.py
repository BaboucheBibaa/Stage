import litellm

class LLM():
    def __init__(self,model):
        self.model = model
        self.input = ""
        self.output = ""
        self.userContext = ""
        self.conversationHistory = ""

    def setUserContext(self,context):
         self.userContext = context
    def setConversationHistory(self,history):
         self.conversationHistory = history
    def setInput(self,message):
        self.input = message
    def generateOutput(self):
        response = litellm.completion(
            model="ollama/llama3.2",
            messages=[
                {
                    "role": "user", 
                    "content": self.input
                    
                },
                {
                "role": "system",
                "content": f"""Tu es un assistant utile et concis.

                PROFIL DE L'UTILISATEUR :
                {self.userContext}

                CONTEXTE DE LA CONVERSATION (échanges antérieurs) utilise ce contexte uniquement si cela sert à répondre au message de l'utilisateur:
                {self.conversationHistory}

                INSTRUCTIONS :
                - Ta priorité est de répondre au contenu envoyé par l'utilisateur.
                - Réponds de manière courte et simple
                - Utilise l'historique fourni ci-dessus pour comprendre le contexte et les sujets abordés
                - Sois cohérent avec les messages précédents
                - Fais référence au contexte passé si pertinent
                - Si c'est la première interaction, réponds simplement à la question
                """
                }
            ]
        )
        return response.choices[0].message['content']

def main():
    llama = LLM('ollama/llama3.2')
    llama.setUserContext("Je m'appelle Lucas, j'ai 20 ans et ma plus grande passion c'est le tennis de table.")
    llama.setConversationHistory("""--- �CHANGE #1 ---
[15:30:00]
UTILISATEUR: Salut ! �a va ?
IA: Tu vas bien, merci ! Comment tu vas ?

--- �CHANGE #2 ---
[15:32:09]
UTILISATEUR: �a va super merci, qu'est-ce que tu me conseilles de faire ?
IA: �a va bien, Lucas ! Qu'est-ce que tu as fait de merveilleux ces derniers jours ?

--- �CHANGE #3 ---
[15:33:37]
UTILISATEUR: je suis actuellement en stage, que puis-je faire de beau ?
IA: Quelques id�es pour un stage agr�able :

- Participe � des �v�nements li�s � l'entreprise ou � la r�gion.
- Trouve un colocataire int�ressant ou un ami avec qui partager les activit�s.
- Explorez de nouveaux lieux dans votre ville.
- Pratiquez le tennis de table pour vous d�tendre.

Qu'est-ce que tu aimes faire pour t'amuser ?

--- �CHANGE #4 ---
[15:35:50]
UTILISATEUR: j'aime bien faire du tennis de table, est-ce un bon sport ?
IA: Bien s�r ! Le tennis de table est un excellent sport pour am�liorer votre coordination, vos r�flexes et votre condition physique. Il permet �galement de se d�tendre et d'avoir du plaisir en jouant avec des amis ou en pratiquant seul. Tu as d�j� une exp�rience positive dans ce domaine !
""")
    llama.setInput("Fais moi un résumé bref de ce message : J'adore aller à la piscine, ça me détend tellement. Je fais quotidiennement 10 allers-retours de piscine.")
    print(llama.input)
    res = llama.generateOutput()
    print(res)

if __name__ == "__main__":
    main()