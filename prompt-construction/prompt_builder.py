import json
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def build_prompts(items):
    out = []
    for item in items:
        title = item.get("title", "").strip()
        summary = item.get("summary", "").strip()
        if not title or not summary:
            continue
        out.append(f"Make a patent description for {title} from the following summary: {summary}")
    return out

data = load_json("patents_for_prompts.json")
prompts = build_prompts(data)

Path("fifty_patent_prompts.json").write_text(json.dumps(prompts, indent=2))
