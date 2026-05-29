"""
Summarizer — résumé des échanges via LLM.
Utilisé par le DialogueManager pour alimenter la MCT et la MLT.
"""

from pathlib import Path
from LLM.LLMBase import BaseLLMClient, LLMResponse
from data.modeles import MCT

_PROMPTS = Path(__file__).parent / "../" "prompts"


def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")


def resumer_echange(llm : BaseLLMClient, msg_user: str, rep_assistant: str) -> str:
    """
    Résume un échange en une phrase courte pour la MCT.
    """
    prompt = _charger("resume_mct.txt").format(
        msg_user=msg_user,
        rep_assistant=rep_assistant,
    )
    return llm.send_simple(prompt).strip()


def resumer_session(llm : BaseLLMClient, historique: list[MCT], mlt_existante: str) -> str:
    """
    Résume toute la session pour mettre à jour la MLT.
    Appelé en fin de conversation (quand l'utilisateur quitte).

    historique : liste de LLMMessage de la session courante
    mlt_existante : texte de la dernière MLT en base (peut être vide)
    """
    lignes = []
    for msg in historique:
        lignes.append("Résumé de la conversation à " + str(msg.date_creation) + " :" + msg.message )
    historique_texte = "\n".join(lignes)

    if not historique_texte.strip():
        return mlt_existante

    prompt = _charger("resume_mlt.txt").format(
        liste_messages=historique_texte,
    )
    return llm.send_simple(prompt).strip()