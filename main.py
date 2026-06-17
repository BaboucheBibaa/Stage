import threading
import yaml

from LLM.ollama_config import OllamaClient
from modules.DialogueModule import DialogueModule
from modules.BoucleProactivite import DeclenchementProactivite
from modules.GestionSorties import GestionSorties, MessageAffichage

ID_PROFIL  = 1
SEPARATEUR = "─" * 50


def boucle_affichage(router: GestionSorties) -> None:
    """
    Seul endroit du programme autorisé à faire print().
    Tourne dans son propre thread et vide la queue au fil de l'eau.
    S'arrête dès que router.stop() enfile la sentinelle None.
    """
    while True:
        item: MessageAffichage | None = router.get()

        if item is None:
            # si arrêt, on sort proprement
            break

        if item.source == "proactif":
            # Le message proactif arrive peut-être pendant une saisie utilisateur
            # On saute une ligne pour ne pas coller au prompt "Toi : " en cours,
            # puis on réaffiche le prompt après le message
            print(f"\n{SEPARATEUR}")
            print(f" Compagnon (proactif) : {item.texte}")
            print(f"{SEPARATEUR}")
            print("Toi : ", end="", flush=True)
        else:
            print(f" Compagnon : {item.texte}\n")


def boucle_chat(dm: DialogueModule, router: GestionSorties) -> None:
    """
    Boucle principale de conversation.
    Lit l'entrée utilisateur, appelle DialogueModule.chat(),
    et dépose la réponse dans la queue
    """
    print(SEPARATEUR)
    print(f" Compagnon prêt | modèle : {dm.compagnon.modele}")
    print(f" Bonjour {dm.profil.prenom} ! (tape 'quit' pour quitter)")
    print(SEPARATEUR)

    while True:
        try:
            user_input = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            router.enqueue("Au revoir !", source="dialogue")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            # Résumé de session avant de quitter
            dm.sauvegarder_MLT(dm.id_profil)
            router.enqueue("Au revoir !", source="dialogue")
            break

        reponse = dm.chat(user_input)
        router.enqueue(reponse, source="dialogue")


def main() -> None:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    llm    = OllamaClient()
    router = GestionSorties()

    # démarrage du thread d'affichage
    affichage_thread = threading.Thread(
        target=boucle_affichage,
        args=(router,),
        name="AffichageThread",
        daemon=True,
    )
    affichage_thread.start()

    # 2eme thread : le gestionnaire de proactivité, qui reçoit le gestionnaire de sorties pour qu'il puisse ajouter à la file les sorties proactives.
    schedule = DeclenchementProactivite(llm, ID_PROFIL, gestionnaire_sortie=router)
    schedule.start()

    #module de dialogue simple
    try:
        dm = DialogueModule(llm=llm, id_profil=ID_PROFIL)
    except Exception as e:
        print(f"Erreur d'initialisation : {e}")
        schedule.stop()
        router.stop()
        affichage_thread.join(timeout=2)
        return

    #boucle infinie tant que l'output != "quit"
    boucle_chat(dm, router)

    #arrêt
    schedule.stop()
    router.stop()
    affichage_thread.join(timeout=2)   # attend que le dernier message soit affiché

if __name__ == "__main__":
    main()