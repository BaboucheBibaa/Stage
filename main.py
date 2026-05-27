import yaml
from data.bd import Database
from data.dataclasses import (
    DonneesProfil, DonneesPreferences, DonneesSujetSensible,
    DonneesCompagnon, DonneesConversation, DonneesMessage,
    DonneesMLT, DonneesMCT,
)
from LLM.ollama_config import OllamaClient
from modules.DialogueModule import DialogueModule

ID_PROFIL = 1
SEPARATEUR = "-" * 50


def tester_connexion_bd(db: Database) -> bool:
    print("[ BD ] Connexion MariaDB...", end=" ")
    try:
        db.executeFetch("SELECT 1")
        print("OK")
        return True
    except Exception as e:
        print(f"ERREUR — {e}")
        return False


def tester_chargement_profil(repo_profil: DonneesProfil) -> bool:
    print(f"[ BD ] Chargement du profil ID={ID_PROFIL}...", end=" ")
    try:
        profil = repo_profil.getProfil(ID_PROFIL)
        if profil is None:
            print(f"ERREUR — aucun profil trouvé avec ID={ID_PROFIL}")
            return False
        print(f"OK — {profil.prenom} {profil.nom}")
        return True
    except Exception as e:
        print(f"ERREUR — {e}")
        return False


def tester_compagnon(repo_compagnon: DonneesCompagnon) -> bool:
    print("[ BD ] Chargement du compagnon...", end=" ")
    try:
        compagnon = repo_compagnon.getCompagnon(1)
        if compagnon is None:
            print("ERREUR — aucun compagnon en base")
            return False
        print(f"OK — modèle : {compagnon.modele}")
        return True
    except Exception as e:
        print(f"PROUT — {e}")
        return False


def tester_ollama(llm: OllamaClient) -> bool:
    print(f"[LLM] Connexion Ollama (modèle : {llm.model})...", end=" ")
    try:
        reponse = llm.send_simple("Réponds uniquement par le mot : OK")
        print(f"OK — réponse : {reponse.strip()}")
        return True
    except Exception as e:
        print(f"ERREUR — {e}")
        return False


def tester_system_prompt(dm: DialogueModule) -> bool:
    print("[PRM] Construction du system prompt...", end=" ")
    try:
        prompt = dm._build_system_prompt()
        lignes = len(prompt.splitlines())
        print(f"OK — {lignes} lignes, {len(prompt)} caractères")
        print()
        print("── Aperçu du system prompt ──────────────────────")
        print(prompt)
        print(SEPARATEUR)
        return True
    except Exception as e:
        print(f"ERREUR — {e}")
        return False


def tester_persistance(dm: DialogueModule, db: Database) -> bool:
    print("[MSG] Test persistance d'un message en BD...", end=" ")
    # Vérifie que la conversation a bien été créée
    rows = db.executeFetch(
        "SELECT * FROM Conversation WHERE ID_Conversation = ?",
        (dm._id_conversation,)
    )
    if not rows:
        print("ERREUR — conversation non trouvée en base")
        return False

    # Envoie un message de test et vérifie qu'il est sauvegardé
    dm.chat("Ceci est un message de test.")
    msgs = db.executeFetch(
        "SELECT * FROM Messages WHERE ID_Conversation = ?",
        (dm._id_conversation,)
    )
    if not msgs:
        print("ERREUR — message non trouvé en base après chat()")
        return False

    print(f"OK — {len(msgs)} message(s) en base")
    return True

def boucle_chat(dm: DialogueModule):
    print()
    print(SEPARATEUR)
    print(f" Compagnon prêt | modèle : {dm.compagnon.modele}")
    print(f" Bonjour {dm.profil.prenom} ! (tape 'quit' pour quitter)")
    print(SEPARATEUR)
    print()

    while True:
        try:
            user_input = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Au revoir !")
            break

        print(f"Réponse : {dm.chat(user_input)}\n")


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    print(SEPARATEUR)
    print(" PHASE 1 — Tests de démarrage")
    print(SEPARATEUR)

    # ── Connexion BD ──────────────────────────────
    db = Database()
    if not tester_connexion_bd(db):
        print("\nImpossible de continuer sans connexion BD.")
        return

    # ── Repositories ─────────────────────────────
    repo_profil    = DonneesProfil(db)
    repo_prefs     = DonneesPreferences(db)
    repo_sujets    = DonneesSujetSensible(db)
    repo_compagnon = DonneesCompagnon(db)
    repo_conv      = DonneesConversation(db)
    repo_msg       = DonneesMessage(db)
    repo_mlt       = DonneesMLT(db)
    repo_mct       = DonneesMCT(db)

    if not tester_chargement_profil(repo_profil):
        return
    if not tester_compagnon(repo_compagnon):
        return

    # ── LLM ──────────────────────────────────────
    llm = OllamaClient(model=config["llm"]["model"])
    if not tester_ollama(llm):
        print("\nImpossible de continuer sans Ollama.")
        return

    # ── DialogueManager ───────────────────────────
    print("[ DM ] Initialisation du DialogueManager...", end=" ")
    try:
        dm = DialogueModule(
            data_repos={
                'profil': repo_profil,
                'preferences': repo_prefs,
                'sujets_sensibles' : repo_sujets,
                'compagnon': repo_compagnon,
                'conversation': repo_conv,
                'message':repo_msg,
                'mlt': repo_mlt,
                'mct':repo_mct,
            },
            llm=llm,
            id_profil=ID_PROFIL
        )
        print(f"OK — conversation ID={dm._id_conversation}")
    except Exception as e:
        print(f"ERREUR — {e}")
        return

    print()
    print(SEPARATEUR)
    print(" PHASE 2 — Vérification du system prompt")
    print(SEPARATEUR)
    if not tester_system_prompt(dm):
        return

    print()
    print(SEPARATEUR)
    print(" PHASE 3 — Test de persistance BD")
    print(SEPARATEUR)
    if not tester_persistance(dm, db):
        return

    print()
    print(SEPARATEUR)
    print(" PHASE 4 — Conversation libre")
    print(SEPARATEUR)
    boucle_chat(dm)


if __name__ == "__main__":
    main()