from projectTypes import MCT, BaseLLMClient, LLMMessage,AnalyseHumeurOutput
from data.dataclasses import DonneesMCT,DonneesCompagnon, DonneesProfil, DonneesMLT
from pathlib import Path
from datetime import datetime
import json

_PROMPTS = Path(__file__).parent / "../" "prompts"

def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")

class InitiativeModule():
    def __init__(self, id_profil : int, data_mct : DonneesMCT, data_compagnon: DonneesCompagnon, data_profil: DonneesProfil, data_mlt: DonneesMLT, llm: BaseLLMClient):
        self._data_mct = data_mct
        self._id_profil = id_profil
        self.llm = llm
        self.compagnon = data_compagnon.getCompagnon(1)
        self.profil = data_profil.getProfil(self._id_profil)
        self._data_mlt = data_mlt.getMLT(self._id_profil)
        
    def format_mct(self,mct: MCT) -> str:
        try:
            data : dict = json.loads(mct.message)
            return f"  [{mct.date_creation:%H:%M}] {data.get('sujet','')} — {data.get('Resume_Reponse','')}"
        except json.JSONDecodeError:
            return f"  {mct.message}"

    def analyse_conversation(self) -> AnalyseHumeurOutput:
        mct_recente = self._data_mct.getToday(self._id_profil)
        lignes_mct = "\n".join(self.format_mct(mct) for mct in reversed(mct_recente))
        system_prompt = _charger("initiative/analyse_humeur_system.txt")
        user_prompt = _charger("initiative/analyse_humeur_user.txt").format(lignes_mct=lignes_mct)
        reponse = self.llm.send(
            messages=[LLMMessage(role="user", contenu=user_prompt)],
            system_prompt=system_prompt,
            output_model=AnalyseHumeurOutput
        )
        return reponse
    @staticmethod
    def _calculer_age(date_naissance : datetime) -> int:
        """Calcule l'âge à partir de la date de naissance
        
        Args:
            date_naissance: datetime.date, datetime.datetime, ou string au format 'YYYY-MM-DD'
            
        Returns:
            int: Age en années
        """
        try:
            today = datetime.now()
            age = today.year - date_naissance.year
            
            # Ajuster si l'anniversaire n'a pas eu lieu cette année
            if (today.month, today.day) < (date_naissance.month, date_naissance.day):
                age -= 1
            
            return age
        except Exception as e:
            print(f"Erreur lors du calcul de l'âge: {e}")
            return 0

    def prise_initiative(self):
        resultat_analyse = self.analyse_conversation()
        if resultat_analyse.confiance > 0.7 and resultat_analyse.envie_interagir > 0.6:
            prompt_initiative_system = _charger("initiative/prompt_initiative_system.txt").format(
                date_jour=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                nom_compagnon=self.compagnon.modele,
                prenom=self.profil.prenom,
                nom=self.profil.nom,
                age=self._calculer_age(self.profil.date_naissance),
                contenu_mlt = 

            )