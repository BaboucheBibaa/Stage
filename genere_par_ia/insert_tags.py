import json
import os

import mariadb
from dotenv import load_dotenv
from os import getenv


def load_tags(tags_path):
    with open(tags_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = set()
    ordered = []
    for category, group in data.items():
        for tag in group:
            if tag not in seen:
                seen.add(tag)
                ordered.append((tag, category))
    return ordered


def get_db_config():
    return {
        "user": getenv("BD_USER"),
        "password": getenv("BD_MDP"),
        "host": getenv("BD_HOST"),
        "database": getenv("BD_NOM"),
        "port": int(getenv("BD_PORT")),
    }


def main():
    load_dotenv()

    tags_path = os.path.join(os.path.dirname(__file__), "tags.json")
    tags = load_tags(tags_path)

    conn = mariadb.connect(**get_db_config())
    cur = conn.cursor()

    cur.execute("SELECT NomTag FROM Tag")
    existing = {row[0] for row in cur.fetchall()}

    cur.execute("SELECT COALESCE(MAX(ID_Tag), 0) FROM Tag")
    max_id = cur.fetchone()[0] or 0
    next_id = max_id + 1

    new_rows = []
    for tag, category in tags:
        if tag in existing:
            continue
        new_rows.append((next_id, tag, category))
        next_id += 1

    if new_rows:
        cur.executemany(
            "INSERT INTO Tag (ID_Tag, NomTag, Categorie) VALUES (?, ?, ?)",
            new_rows,
        )
        conn.commit()

    print(f"Tags existants : {len(existing)}")
    print(f"Tags inseres   : {len(new_rows)}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
