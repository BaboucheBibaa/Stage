from llm import LLM
def main():
    llm = LLM("ollama/mistral")
    while 1:
        message = "bonjour ! comment vas tu ?"
        print("Réponse de l'IA: " + llm.reponse(message))
if __name__ == "__main__":
    main()