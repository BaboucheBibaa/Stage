from modules.ModuleInitiative import InitiativeModule
from data.bd import Database
from data.dataclasses import DonneesMCT,DonneesProfil,DonneesMLT,DonneesCompagnon
from LLM.ollama_config import OllamaClient

db = Database()
data_mct = DonneesMCT(db)
data_mlt = DonneesMLT(db)
data_compagnon = DonneesCompagnon(db)
data_profil = DonneesProfil(db)
llm = OllamaClient()

initiative = InitiativeModule(1, data_mct, llm=llm,data_profil=data_profil,data_mlt=data_mlt)

initiative.prise_initiative()
