# TODO List

## Améliorer le prompt système
Le LLM récupère les bonnes données pour faire de la proactivité simple durant une discussion, mais est-ce que le prompt système permet de pouvoir faire de la proactivité simple telle qu'elle est décrite ci dessous ?

## Proactivité

La proactivité dans le projet peut se distinguer de plusieurs manières, l'intérêt de faire cette distinction et de pouvoir ensuite concevoir différents modules de proactivité qui seront tous idéalement exécutés en parallèle afin de pouvoir gagner du temps dans la génération de la réponse (aucun de ces modules n'est censé être dépendant d'un autre). L'idéal serait de se dire qu'un module = un type de proactivité, et que cette proactivité peut être vérifiée toutes les X secondes par un thread qui analyse la conversation récente afin de pouvoir fournir des données au LLM pour qu'il puisse extraire de la proactivité à partir de ces données.
### Proactivité simple (au cours d'une discussion)
Utilise la mémoire long terme pour alimenter une conversation.
Cette proactivité n'est pas clairement visible, elle est présente uniquement pour enrichir une réponse du compagnon virtuel.
Utilise uniquement les données pertinentes d'un point de vue sémantique.
(On ne va pas envoyer le fait qu'on a été à la plage il y a 3 semaines à un modèle qui a besoin d'avoir du contexte sur nos rendez-vous professionnels par exemple)

Exemple : Si dans la MLT il y a le fait que l'utilisateur aime bien les musées, et qu'aujourd'hui, l'utilisateur dit "j'ai envie d'aller à Paris, dis moi quoi faire". L'objectif est que le compagnon accentue le fait de lui conseiller les musées dans Paris.

#### Proactivité basée sur des événements <span style="color:red">(IMPLÉMENTÉ)</span>

Analyse constamment le message utilisateur pour y extraire un événement qui sera déclenché.

Exemple : Si je dis au compagnon virtuel que j'ai un rendez-vous demain à 17h, il doit être en mesure de me rappeler quelques heures auparavant que j'ai un rendez-vous à 17h. Même logique pour un examen.

Problèmes de cette proactivité : La logique de timing de notification de l'événement avant qu'il ne se passe ne fonctionne que pour un nombre prédéfini d'événements, prévus dans le script.
#### Proactivité basée sur l'habitude
Utilise la mémoire long terme pour déterminer une habitude. Si elle n'a pas été faite en ce jour-ci, déclencher un message proactif pour prendre des nouvelles concernant cette habitude.

#### Proactivité basée sur l'anomalie ?
Une chose qui sort de l'ordinaire, un manque de discussion dans une journée ? ça semble se rapproche de la proactivité basée sur l'habitude.

## Bugs sur la proactivité
Proactivité événementielle : Le modèle me harcèle jusqu'à la date du rendez-vous. J'ai dit que j'avais un rendez-vous à 17h, il me harcèle toutes les 5 minutes pour me le rappeler.

# Bonus

## TODO : hiérarchiser les bonus à faire + est-ce que c'est important ?

Proposer une application Tkinter afin de pouvoir tester une discussion simple entre le compagnon virtuel et l'utilisateur

# Mémoire

Proposer un système permettant d'analyser toutes les X minutes la MLT afin de vérifier en parallèle (via un thread) la pertinence des informations sur l'utilisateur afin de nettoyer / fusionner des données redondantes

Exemple : Si l'utilisateur dit un jour qu'il a perdu son père lors d'un accident, il n'est pas forcément nécessaire de le garder sur le long terme si un jour il le répète. Sur le moment, le compagnon virtuel va stocker la donnée, mais derrière, un agent doit pouvoir détecter cette redondance des données et la supprimer.

# Annuler un événement planifié

Si l'utilisateur a dit qu'il voulait planifier un événement et un autre jour il dit qu'il a été annulé, ce serait bien de pouvoir mettre à jour à BD en supprimant l'événement.

# Mise à jour dynamique des préférences / sujets sensibles ?

Un LLM qui met à jour lui-même les préférences utilisateurs en ajoutant une donnée ? ça peut se faire selon moi mais faut être super rigoureux et restrictif dans ce qu'il peut ajouter, sinon il peut ajouter des choses bizarres ou des phrases à rallonge dans les préférences.

# Feedback utilisateur à prendre en compte ?

Lors d'une remarque proactive, il serait peut-être bien de prendre en compte le retour de l'utilisateur sur le message proactif.

S'il répond positivement, ce serait bien d'avoir un score de proactivité, plus ce score est haut, et plus le compagnon virtuel pourrait lancer des remarques proactives ? Et inversement si l'utilisateur dit que la remarque ne sert à rien, réduire le score ? 
L'idée semble bien mais un peu trop "noir ou blanc". Il n'y a pas d'entre deux, ce sera toujours une croissance positive ou négative du taux de remarques positives, avec cette logique là, ce ne sera jamais un taux constant, le compagnon regardera toujours une réponse à sa remarque proactive comme étant positive ou négative, jamais neutre. Donc le taux de remarques proactive ne sera jamais idéal pour un utilisateur, il variera toujours. Est-ce une bonne idée d'augmenter le taux de remarques proactives si l'utilisateur dit que c'est une bonne remarque ? à voir.

# Lien entre différents éléments de la MLT

Ce serait sympa de pouvoir établir des liens entre différents éléments dans la MLT. Je m'explique, si un jour je dis que je vais en voyage à Paris tel jour, et un autre jour je dis que j'aime beaucoup l'art contemporain, il serait pertinent que le compagnon me dise "tiens, si tu vas à Paris tel jour, je te conseille d'aller ici, il y a une exposition sur l'art contemporain" cela me semble compliqué à implémenter sur des LLM "bas de gamme" car cela implique d'être au courant de l'actualité locale, mais c'est une amélioration envisageable si on utilise une API ChatGPT ou Claude.
De plus, cela pourrait être vraiment idéal de représenter la mémoire du compagnon virtuel par un graphe de mémoire, on pourrait associer les données (qui seraient les sommets) entre elles (les arêtes = description du lien entre les deux sommets, "est allé", "aime", "déteste", etc...). Voir le fonctionnement de Mem0, cela pourrait être vraiment puissant, et en plus, cela ressemblerait à notre fonctionnement, on associe des personnes à des idées, des lieux, etc... On peut tout aussi bien associer des émotions à des événements, par exemple si un utilisateur dit qu'il est stressé, sans être très explicite, on peut se référer à cet émotion dans le graphe si elle existe déjà, par exemple si l'utilisateur a dit qu'il avait un examen bientôt, le compagnon pourrait dire que ce stress est peut-être engendré par cet examen. Le compagnon aurait ainsi la capacité de "déduire" quelque chose ?
De plus, cette association entre deux entités pourrait être valuée, afin de pouvoir hiérarchiser deux liens, peut-être que l'utilisateur A aime davantage les jeux vidéos qu'il aime le football, dans ce cas la valuation sur l'arête entre "utilisateur A" et "jeux vidéos" pourrait être plus forte que celle entre "utilisateur A" et "football".
Pour une amélioration du système, un graphe de mémoire serait réellement la meilleure chose à faire, les possibilités avec ce système seraient vraiment sympa à explorer, on pourrait distinguer BEAUCOUP plus de cas de proactivités qu'avec une base de données simple comme ce qui est implémenté actuellement.

# Idées purement folles et éventuellement inutiles

## Réponse vocale du compagnon ? + évidemment la possibilité de pouvoir communiquer à l'oral avec le compagnon virtuel.
## Intégration de ce système à un avatar généré par IA qui répondrait en direct à l'utilisateur ? (étrange éthiquement mais d'un point de vue technique ce serait fort)
