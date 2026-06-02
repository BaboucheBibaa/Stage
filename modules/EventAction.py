from data.dataclasses import DonneesEvenement, Evenement
from data.bd import Database
class EventAction:
    def __init__(self, id_profil: int):
        db = Database()
        data_event = DonneesEvenement(db)
        self.evenements_futurs = data_event.getFuturs(id_profil=id_profil)
    
    def detecter_timing(self):
        