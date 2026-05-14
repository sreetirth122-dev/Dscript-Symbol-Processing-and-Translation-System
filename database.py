import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DB_FOLDER, "symbol_database.json")

os.makedirs(DB_FOLDER, exist_ok=True)

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"symbols": []}

def save_database(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def generate_symbol_id(db):
    return f"sym_{len(db.get('symbols', [])) + 1:03d}"

def current_timestamp():
    return datetime.now().isoformat()