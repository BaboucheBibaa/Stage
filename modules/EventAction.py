from data.dataclasses import DonneesEvenement, Evenement
from data.bd import Database
from datetime import datetime
class EventAction:
    def __init__(self, id_profil: int):
        db = Database()
        data_event = DonneesEvenement(db)
        self.evenements_futurs = data_event.getFuturs(id_profil=id_profil)
        
    
    def detecter_timing(self):
        for evt in self.evenements_futurs:
            if evt.timing == datetime.now().strptime(evt['timing'], "%Y-%m-%d %H:%M:%S"):
                pass
                
                