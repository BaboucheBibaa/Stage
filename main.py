import yaml
from data.bd import Database
from data.dataclasses import (
    DonneesProfil, DonneesPreferences, DonneesSujetSensible,
    DonneesCompagnon, DonneesConversation, DonneesMessage,
    DonneesMLT, DonneesMCT,DonneesEvenement
)
from LLM.ollama_config import OllamaClient
from modules.DialogueModule import DialogueModule

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
    db = Database()
    data_profil = DonneesProfil(db)
    data_prefs = DonneesPreferences(db)
    data_sujets = DonneesSujetSensible(db)
    data_compagnon = DonneesCompagnon(db)
    data_conv = DonneesConversation(db)
    data_msg = DonneesMessage(db)
    data_mlt = DonneesMLT(db)
    data_mct = DonneesMCT(db)
    data_evenement = DonneesEvenement(db)
    llm = OllamaClient(model=config["llm"]["model"])
    try:
        dm = DialogueModule(
            data_repos={
                'profil': data_profil,
                'preferences': data_prefs,
                'sujets_sensibles' : data_sujets,
                'compagnon': data_compagnon,
                'conversation': data_conv,
                'message':data_msg,
                'mlt': data_mlt,
                'mct':data_mct,
                'event': data_evenement
            },
            llm=llm,
            id_profil=ID_PROFIL
        )
    except Exception as e:
        print(e)
        return
    boucle_chat(dm)

if __name__ == "__main__":
    main()