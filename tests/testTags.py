from toTag import ToTag

dataset = [
    {
        "text": "Je ne dors plus depuis 3 jours, je suis épuisé",
        "expected": ["Santé", "Fatigue", "Tristesse", "Repos"]
    },
    {
        "text": "Demain je passe ma soutenance de projet à 16h30 et je stresse beaucoup",
        "expected": ["Études", "Stress", "Pression", "Surmenage", "Soutenance", "Échéance"]
    },
    {
        "text": "J’ai enfin réussi mon projet Python, je suis super fier",
        "expected": ["Projets", "Fierté", "Progrès", "Performance"]
    },
    {
        "text": "Je me sens seul depuis que mon meilleur ami est parti vivre loin",
        "expected": ["Relations", "Tristesse", "Isolement", "Réconfort"]
    },
    {
        "text": "Mon boss me met une pression énorme au travail",
        "expected": ["Travail", "Stress", "Pression", "Surmenage"]
    },
    {
        "text": "Je ne sais plus quoi faire pour mon avenir professionnel",
        "expected": ["Travail", "Doute", "Confusion", "Conseil"]
    },
    {
        "text": "Je suis allé courir ce matin et ça m’a donné plein d’énergie",
        "expected": ["Hobbies", "Joie", "Motivation"]
    },
    {
        "text": "Je n’ai jamais dit ça à personne mais je me sens perdu",
        "expected": ["Vie_personnelle", "Doute", "Confusion", "Réconfort"]
    },
    {
        "text": "J’ai besoin d’aide pour organiser mes révisions",
        "expected": ["Études", "Organisation", "Planification", "Conseil"]
    },
    {
        "text": "J’ai très mal au ventre depuis plusieurs heures",
        "expected": ["Santé", "Anxiété"]
    }
]

def normalize(tags):
    return set([t.lower() for t in tags])

all_true = []
all_pred = []

results = []

for item in dataset:
    text = item["text"]
    expected = normalize(item["expected"])

    result = ToTag(text)
    predicted = set()

    for key in ["emotion", "domain", "state", "needs"]:
        predicted.update([t.lower() for t in result.result.get(key, [])])

    tp = len(predicted & expected)
    fp = len(predicted - expected)
    fn = len(expected - predicted)

    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)

    results.append({
        "text": text,
        "expected": list(expected),
        "predicted": list(predicted),
        "precision": precision,
        "recall": recall,
        "f1": f1
    })

    all_true.extend([1] * len(expected))
    all_pred.extend([1] * len(predicted))

avg_precision = sum(r["precision"] for r in results) / len(results)
avg_recall = sum(r["recall"] for r in results) / len(results)
avg_f1 = sum(r["f1"] for r in results) / len(results)

print("\nRESULTATS GLOBAUX")
print(f"Precision moyenne : {avg_precision:.2f}")
print(f"Recall moyen      : {avg_recall:.2f}")
print(f"F1-score moyen    : {avg_f1:.2f}")