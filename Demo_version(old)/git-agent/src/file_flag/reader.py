# file_flag/reader.py
import json
import os
from typing import Optional, Dict, Any

def read_last_flag(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list) and data:
        return data[-1]
    return None
