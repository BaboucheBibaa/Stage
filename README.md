# Contexte 
Depuis l’avènement des LLM, les assistants conversa onnels répondent bien aux requêtes, 
mais restent majoritairement “réac fs”. L’objec f du stage est de produire un prototype 
(MVP) d’un compagnon virtuel capable d’interagir avec un humain en ini ant parfois une 
conversa on (proac vité). A par r de la connaissance du profil de l’humain (habitudes, 
centres d’intérêt, …)  qui s’affine au fur et à mesure des conversa ons, il doit pouvoir 
échanger sur des sujets d’ « actualité »  tout en restant contrôlable, explicable (journaliser 
“pourquoi” une ini a ve a eu lieu) et non intrusif. Le prototype sera développé en Python, 
avec une architecture modulaire perme ant de remplacer facilement le modèle de langage 
(LLM) et les composants (mémoire, planification, déclencheurs). 

# Objectif 
Développer en Python un MVP (Minimum Viable Prototype) démontrable qui : 
• Converse via une interface simple (ligne de commande, avatar Unity ou équivalent 
en bonus), 
• Dispose d’une mémoire basique (profil, notes, historique), 
• Déclenche des ac ons proac ves sur la base d’événements (temps, messages, 
règles simples), 
• Intègre un LLM (API ou modèle local léger) via une couche d’abstrac on, 
• Journalise et évalue son comportement (traces, tests, scénarios). 