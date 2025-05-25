import json
from pathlib import Path

def load_chat_data() -> dict:
    file = Path(__file__).parent.parent / 'data' / 'chat_sample.json'
    with open(file, encoding='utf-8') as f:
        return json.load(f)