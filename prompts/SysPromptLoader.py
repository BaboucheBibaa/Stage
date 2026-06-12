"""
PromptLoader — charge et formate l'unique template system_prompt.txt.
"""

from pathlib import Path
import data.modeles as md
import json
from datetime import datetime

_TEMPLATE = (Path(__file__).parent / "system_prompt.txt").read_text(encoding="utf-8")

def format_mct(mct: md.MCT) -> str:
    try:
        data : dict = json.loads(mct.message)
        return f"  [{mct.date_creation:%H:%M}] {data.get('sujet','')} — {data.get('intention_utilisateur','')}"
    except json.JSONDecodeError:
        return f"  {mct.message}"

def build_system_prompt(nom_compagnon: str,prenom: str, nom: str, age: int,profil: dict[str,float],preferences: list[md.Preference],sujets_sensibles: list[md.SujetSensible],mlt_text: str,mct_list: list[md.MCT],) -> str:

    # Préférences
    if preferences:
        lignes_preferences = "\n".join(f"  - {p.sujet} (intérêt : {p.niveau:.0%})" for p in preferences)
    else:
        lignes_preferences = "  Aucune préférence enregistrée pour l'instant."

    # Sujets sensibles
    if sujets_sensibles:
        lignes = []
        for s in sujets_sensibles:
            if s.niveau >= 0.7:
                consigne = "éviter absolument"
            elif s.niveau >= 0.4:
                consigne = "aborder avec beaucoup de délicatesse"
            else:
                consigne = "aborder avec prudence"
            lignes.append(f"  - {s.sujet} ({consigne})")
        lignes_sujets_sensibles = "\n".join(lignes)
    else:
        lignes_sujets_sensibles = "  Aucun sujet sensible enregistré."

    # MLT
    contenu_mlt = mlt_text.strip() if mlt_text else "Aucune mémoire long terme disponible pour l'instant."

    # MCT
    if mct_list:
        lignes_mct = "\n".join(format_mct(mct) for mct in reversed(mct_list))
    else:
        lignes_mct = "  Aucun échange précédent."

    return _TEMPLATE.format(date_jour=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),nom_compagnon=nom_compagnon,prenom=prenom,nom=nom,age=age,empathie=f"{profil['empathie']:.0%}",humour=f"{profil['humour']:.0%}",professionalisme=f"{profil['professionalisme']:.0%}",patience=f"{profil['patience']:.0%}",lignes_preferences=lignes_preferences,lignes_sujets_sensibles=lignes_sujets_sensibles,contenu_mlt=contenu_mlt,lignes_mct=lignes_mct)
    
