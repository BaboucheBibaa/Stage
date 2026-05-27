def charger_prompt(filename: str):
    file_path = f'prompt_en/{filename}'
    with open(file_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    return system_prompt