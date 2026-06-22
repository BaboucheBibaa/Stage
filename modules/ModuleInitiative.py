from projectTypes import MCT, BaseLLMClient, LLMMessage,AnalyseHumeurOutput, MLT
from data.dataclasses import DonneesMCT, DonneesProfil, DonneesMLT
from pathlib import Path
from datetime import datetime
import yaml
_PROMPTS = Path(__file__).parent / "../" "prompts"

def _charger(nom: str) -> str:
    return (_PROMPTS / nom).read_text(encoding="utf-8")

class InitiativeModule():
    def __init__(self, id_profil : int, data_mct : DonneesMCT, data_profil: DonneesProfil, data_mlt: DonneesMLT, llm: BaseLLMClient):
        self._data_mct = data_mct
        self._id_profil = id_profil
        self.llm = llm
        self.profil = data_profil.getProfil(self._id_profil)
        self._data_mlt = data_mlt.getMLT(self._id_profil)
        
    def format_mlt(self, mlt: MLT) -> str:
        return f"""
        Enregistrement de la mémoire long terme sur l'utilisateur:
        Date de création: {mlt.date_creation}
        Nombre de messages : {mlt.nombre_echanges}
        Humeur Générale : {mlt.humeur_generale}
        Centres d'intérêts : {mlt.centres_interets}
        Thèmes abordés : {mlt.themes_abordes}
        Résumé de la conversation : {mlt.resume_conversation}
        Évènements mentionnés : {mlt.evenements_mentionnes}
    """

    def format_mct(self, mct: MCT) -> str:
        return f"""
        Enregistrement de la conversation actuelle avec l'utilisateur:

        Date de création : {mct.date_creation}
        Sujet de la conversation : {mct.sujet}
        Intention de l'utilisateur : {mct.intention}
        Évènements mentionnés par l'utilisateur : {mct.evenements_mentionnes}
        Résumé de la réponse proposée par le compagnon virtuel : {mct.resume_reponse}
        Entités (Personnes, lieux, entreprises, etc...) mentionnées dans la conversation : {mct.entites_mentionnees}
        Langage de la conversation : {mct.langage}
        Tags (mots-clés) de la conversation: {mct.tags}
        """
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
        
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        resultat_analyse = self.analyse_conversation()
        print(resultat_analyse.confiance)
        print(resultat_analyse.envie_interagir)
        print(self._data_mlt)
        if resultat_analyse.confiance > 0.7 and resultat_analyse.envie_interagir >= 0.6:
            prompt_initiative_system = _charger("initiative/prompt_initiative_system.txt").format(
                date_jour=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                nom_compagnon=config["companion"]['name'],
                prenom=self.profil.prenom,
                nom=self.profil.nom,
                age=self._calculer_age(self.profil.date_naissance),
            )
            if (self._data_mlt is not None):
                donnees_mlt = [self.format_mlt(mlt) for mlt in self._data_mlt]
            else:
                donnees_mlt = "Aucune mémoire long terme pour l'utilisateur."
            prompt_initiative_user = _charger("initiative/prompt_initiative_user.txt").format(
                donnees_mlt=donnees_mlt
            )
            print(prompt_initiative_user)
            reponse = self.llm.send(
                messages=[LLMMessage(role="user", contenu=prompt_initiative_user)],
                system_prompt=prompt_initiative_system,
            )
            print(reponse)