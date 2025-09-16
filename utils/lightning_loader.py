import json

def get_lightning_name(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("Lightning Name") or data.get("lightningName") or ""
