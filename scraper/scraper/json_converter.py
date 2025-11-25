import json
import pandas as pd

INPUT_FILE = "cards.json"       # change to "cards_test.json" if testing
OUTPUT_FILE = "cards.xlsx"

# Load JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

# Prepare flattened data
rows = []
for card in cards:
    row = {
        "name": card.get("name"),
        "type": card.get("type"),
        "stage": card.get("stage"),
        "rarity": card.get("rarity")
    }

    # Weakness (type + modifier, no URLs)
    if card.get("weakness"):
        row["weakness"] = ", ".join(
            [f"{w['type']} {w['modifier'] or ''}".strip() for w in card["weakness"]]
        )
    else:
        row["weakness"] = ""

    # Retreat cost as a count (handles list or int)
    retreat_cost = card.get("retreat_cost", [])
    if isinstance(retreat_cost, list):
        row["retreat_cost_count"] = len(retreat_cost)
    elif isinstance(retreat_cost, int):
        row["retreat_cost_count"] = retreat_cost
    else:
        row["retreat_cost_count"] = 0

    # Attacks (expand to columns)
    for i, attack in enumerate(card.get("attacks", []), start=1):
        row[f"attack_{i}_name"] = attack.get("name", "")
        row[f"attack_{i}_damage"] = attack.get("damage", "")
        row[f"attack_{i}_text"] = attack.get("text", "")
    
    rows.append(row)

# Convert to DataFrame
df = pd.DataFrame(rows)

# Save to Excel
df.to_excel(OUTPUT_FILE, index=False)
print(f"Saved spreadsheet to {OUTPUT_FILE}")
