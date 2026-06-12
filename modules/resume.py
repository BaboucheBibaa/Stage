"""
Summarizer — résumé des échanges via LLM.
Utilisé par le DialogueManager pour alimenter la MCT et la MLT.
"""

from pathlib import Path
from projectTypes import BaseLLMClient,MCT, ResumeMCTOutput, ResumeMLTOutput,LLMMessage
_PROMPTS = Path(__file__).parent / "../" "prompts"


def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")


def resumer_echange(llm : BaseLLMClient, msg_user: str, rep_assistant: str) -> ResumeMCTOutput:
    """
    Résume un échange en une phrase courte pour la MCT.
    """
    system_prompt = _charger("mct/mct_resume_system.txt")
    user_prompt = _charger("mct/mct_resume_user.txt").format(
        msg_user=msg_user,
        rep_assistant=rep_assistant
    )
    res = llm.send(
        messages=[LLMMessage(role="user", contenu=user_prompt)],
        system_prompt=system_prompt,
        json_schema=ResumeMCTOutput.model_json_schema()
    )
    resume = ResumeMCTOutput.model_validate_json(res)
    return resume

def resumer_session(llm : BaseLLMClient, historique: list[MCT]) -> ResumeMLTOutput:
    """
    Résume toute la session pour mettre à jour la MLT.
    Appelé en fin de conversation (quand l'utilisateur quitte).

    historique : liste de LLMMessage de la session courante
    mlt_existante : texte de la dernière MLT en base (peut être vide)
    """
    lignes = [
        f"Résumé de la conversation à {msg.date_creation} : {msg.message}"
        for msg in historique
    ]
    system_prompt = _charger("mlt/mlt_resume_system.txt")
    user_prompt = _charger("mlt/mlt_resume_user.txt").format(
        liste_messages="\n".join(lignes)
    )
    res = llm.send(
        messages=[LLMMessage(role="user", contenu=user_prompt)],
        system_prompt=system_prompt,
        json_schema=ResumeMLTOutput.model_json_schema())
    resume = ResumeMLTOutput.model_validate_json(res)
    return resume