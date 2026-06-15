from projectTypes import TypeEvenement
from datetime import timedelta

_REGLES: dict[str, list[timedelta]] = {
    TypeEvenement.RENDEZ_VOUS: [
        timedelta(hours=-1),        # 1 heure avant
        timedelta(hours=1)         # 1 heure après ("comment ça s'est passé ?")
    ],
    TypeEvenement.EXAMEN: [
        timedelta(hours=-13),       # veille au soir
        timedelta(hours=-1),        # 1 heure avant le jour J
        timedelta(hours=2),        # 1 heure après ("comment s'est passé l'exam ?")
    ],
    TypeEvenement.DEADLINE: [
        timedelta(hours=-24),       # 24 heures avant
        timedelta(hours=-2),        # 2 heures avant
    ],
    TypeEvenement.MALADIE: [
        timedelta(hours=2),         # 2h après la mention
    ],
    TypeEvenement.BIEN_ETRE: [
        timedelta(hours=1),         # 1h après la mention
    ],
}

# Délai par défaut si le type est inconnu
_DEFAUT = [timedelta(hours=-1)]

def get_event_status(offset: timedelta) -> str:
    if offset.total_seconds() < 0:
        return "pre-event"
    elif offset.total_seconds() > 0:
        return "post-event"
    else:
        return "at-event"  # optionnel pour t=0

def main():
    offsets = [
        timedelta(hours=-1),
        timedelta(hours=1)
    ]

    for offset in offsets:
        print(offset, get_event_status(offset))

if __name__ == "__main__":
    main()