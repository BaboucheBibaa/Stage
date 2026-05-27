"""
Exemple d'utilisation de LLMClient.
Lance avec : python example_usage.py
"""

import yaml
from  LLM.ollama_config import OllamaClient
from LLM.LLMBase import Message

with open("config.yaml") as f:
    config = yaml.safe_load(f)

llm = OllamaClient(config['llm']['model'],temperature=config['llm']['temperature'])
print(f"modèle : {llm.model}\n")

reply = llm.send_simple(
    "Dis bonjour en une phrase courte.",
    system_prompt="Tu es un compagnon virtuel amical.",
)
print("Réponse simple :", reply)

# 3b. Appel multi-tours (conversation)
history = [
    Message(role="user",      content="Mon film préféré est Interstellar."),
    Message(role="assistant", content="C'est un excellent choix, j'adore la bande-son de Hans Zimmer !"),
    Message(role="user",      content="Qu'est-ce que tu pourrais me recommander de similaire ?"),
]

response = llm.send(
    messages=history,
    system_prompt="Tu es un compagnon virtuel qui connaît bien les goûts de l'utilisateur.",
)
print("\nRéponse multi-tours :", response.content)
print(f"Tokens utilisés : {response.input_tokens} in / {response.output_tokens} out")