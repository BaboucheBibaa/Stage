import litellm
import os
from datetime import datetime

f = open('contexte.txt')
content = f.read()
f.close()

if not os.path.exists('resultat.txt'):
    with open('resultat.txt', 'w') as f:
        f.write("=== HISTORIQUE DE CONVERSATION ===\n\n")

numero_echange = 1

while 1:
    with open('resultat.txt', 'r') as f:
        contexte = f.read()
    entree_utilisateur = input("\nEcrivez un message : ")
    
    response = litellm.completion(
        model="ollama/llama3.2",
        messages=[
            {
            "role": "system",
            "content": f"""Tu es un assistant utile et concis.

PROFIL DE L'UTILISATEUR :
{content}

CONTEXTE DE LA CONVERSATION (échanges antérieurs) :
{contexte}

INSTRUCTIONS CRITIQUES (PAR ORDRE DE PRIORITÉ) :
1. ⭐ PRIORITÉ ABSOLUE : Réponds directement au message utilisateur actuellement posé
2. Utilise l'historique UNIQUEMENT pour rester cohérent, pas pour distraire du message actuel
3. Le message utilisateur actuel PRIME TOUJOURS sur l'historique
4. Réponds de manière courte et simple
5. Si le contexte passé est pertinent, fais référence discrètement (ne domine pas la réponse)
            """
            },
            {
                "role": "user", 
                "content": entree_utilisateur
            }
        ]
    )

    reponse_ia = response.choices[0].message['content']

    with open('resultat.txt', 'a') as f:
        f.write(f"--- ÉCHANGE #{numero_echange} ---\n")
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}]\n")
        f.write(f"UTILISATEUR: {entree_utilisateur}\n")
        f.write(f"IA: {reponse_ia}\n")
        f.write("\n")
    
    numero_echange += 1
    print(reponse_ia)