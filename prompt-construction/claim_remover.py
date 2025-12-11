import json
from pathlib import Path

def strip_claims():
    p = Path("patents_for_prompts.json")
    data = json.loads(p.read_text())
    if isinstance(data, dict):
        data.pop("claims", None)
    else:
        for item in data:
            if isinstance(item, dict):
                item.pop("claims", None)
    Path("patents_no_claims.json").write_text(json.dumps(data, indent=2))

if __name__ == "__main__":
    strip_claims()
