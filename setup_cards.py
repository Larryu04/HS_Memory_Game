import requests
import json

URL = "https://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"

print("⏳ Downloading specific card data...")

try:
    response = requests.get(URL)
    data = response.json()

    TARGET_SETS_MAPPING = {
        "The Great Dark Beyond": ["SPACE"],
        "Perils in Paradise": ["ISLAND_VACATION"],
        "Whizbang's Workshop": ["WHIZBANGS_WORKSHOP"],
        "Into the Emerald Dream": ["EMERALD_DREAM"],
        "The Lost City of Un'Goro": ["THE_LOST_CITY"],
        "Across the Timeways": ["TIME_TRAVEL"],
        "Event": ["EVENT"],
        "Core": ["CORE"]
    }

    ALL_VALID_CODES = {code for codes in TARGET_SETS_MAPPING.values() for code in codes}

    processed_cards = []
    found_counts = {name: 0 for name in TARGET_SETS_MAPPING.keys()}

    for card in data:
        card_set = card.get("set")

        if card_set in ALL_VALID_CODES and "id" in card:
            pretty_name = next((name for name, codes in TARGET_SETS_MAPPING.items() if card_set in codes), card_set)

            new_card = {
                "name": card.get("name"),
                "rarity": card.get("rarity", "Common").capitalize(),
                "set": pretty_name,
                "cost": card.get("cost", 0),
                "img": f"https://art.hearthstonejson.com/v1/render/latest/enUS/256x/{card['id']}.png"
            }
            processed_cards.append(new_card)
            found_counts[pretty_name] += 1

    processed_cards.sort(key=lambda x: (x["set"], x["cost"], x["name"]))

    with open("cards_data.json", "w", encoding="utf-8") as f:
        json.dump(processed_cards, f, indent=2)

    print("\n✅ Status Report:")
    for set_name, count in found_counts.items():
        status = "✅" if count > 0 else "❌ (Check ID)"
        print(f"{status} {set_name}: {count} cards")

    print(f"\n✨ Total cards saved: {len(processed_cards)}")

except Exception as e:
    print(f"❌ Error: {e}")