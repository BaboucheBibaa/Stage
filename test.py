import json

test = '''
{
  "evenements": {
    "contexte": "Rendez-vous",
    "timing": "2026-06-02 17:00:00",
    "statut": "Planifié"
  }
}
'''
res = json.loads(test)  # Ça marche !
print(res['evenements']['contexte'])