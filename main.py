import yaml
from LLM.ollama_config import OllamaClient
from modules.DialogueModule import DialogueModule
from modules.Proactive import ProactiveScheduler

ID_PROFIL = 1
SEPARATEUR = "-" * 50

def boucle_chat(dm: DialogueModule):
    print(SEPARATEUR)
    print(f" Compagnon prêt | modèle : {dm.compagnon.modele}")
    print(f" Bonjour {dm.profil.prenom} ! (tape 'quit' pour quitter)")
    print(SEPARATEUR)

    while True:
        try:
            user_input = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            #ici, une session = une exécution du programme, dans un autre contexte, le résumé de la session se ferait chaque jour idéalement
            dm.sauvegarder_MLT(dm.id_profil)
            print("Au revoir !")
            break
        reponse = dm.chat(user_input)
        print(f"Réponse : {reponse}\n")

def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    llm = OllamaClient(model=config["llm"]["model"])
    schedule = ProactiveScheduler(llm, ID_PROFIL)
    schedule.start()
    try:
        dm = DialogueModule(
            llm=llm,
            id_profil=ID_PROFIL
        )
    except Exception as e:
        print(e)
        return
    boucle_chat(dm)
    schedule.stop()

if __name__ == "__main__":
    main()