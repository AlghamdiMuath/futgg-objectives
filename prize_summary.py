"""Conservative, label-only summaries of published group completion rewards."""

import re


def _prize(label):
    coin = re.fullmatch(r"([\d,]+) Coins", label, re.I)
    if coin:
        return {"kind": "coins", "label": f"{int(coin[1].replace(',', '')):,} Coins",
                "coins": int(coin[1].replace(',', ''))}
    if "pack" in label.lower():
        rating = re.search(r"(?<!\d)(\d{2})\+", label)
        # "3 x 75+ Player Pack" means three one-player packs; "3X 75+ Players"
        # describes one pack with three players. Only the latter is pack size.
        pack_label = re.sub(r"^\d+\s+x\s+", "", label, flags=re.I)
        count = re.match(r"(\d+)\s*x\s*", pack_label, re.I)
        player_count = int(count[1]) if count and "player" in label.lower() else (
            1 if re.search(r"\bPlayer Pack\b", label, re.I) else None)
        return {"kind": "pack", "label": label, "quality": {
            "minimum_rating": int(rating[1]) if rating else None,
            "player_count": player_count}}
    # A player name is identifiable only when the completion label is a name.
    generic = ("point", "sp", "token", "badge", "award", "consumable", "manager",
               "trophy", "boost", "unlock", "access", "pick", "tifo", "theme", "ball")
    if any(word in label.lower() for word in generic):
        return {"kind": "other", "label": label}
    rating = re.fullmatch(r"(.+?)\s*\((\d{2})\)", label)
    return {"kind": "player", "label": rating[1] if rating else label,
            "rating": int(rating[2]) if rating else None}


def summarize(group):
    completion = [_prize(value) for value in group.get("completion_rewards", [])]
    listed = completion + [_prize(value) for value in group.get("available_rewards", [])]
    players = [r for r in listed if r["kind"] == "player"]
    coins = [r for r in listed if r["kind"] == "coins"]
    packs = [r for r in listed if r["kind"] == "pack"]
    main_players = [r for r in completion if r["kind"] == "player"]
    main_coins = [r for r in completion if r["kind"] == "coins"]
    main_packs = [r for r in completion if r["kind"] == "pack"]
    main = (main_players or main_coins or main_packs or completion or [{"kind": "unknown", "label": "Unknown"}])[0]
    other_players = list(dict.fromkeys(r["label"] for r in players
                                       if main["kind"] != "player" or r["label"] != main["label"]))
    rated = [r["rating"] for r in players if r["rating"] is not None]
    comparable_packs = [r for r in packs if r["quality"]["minimum_rating"] is not None]
    best_pack = max(comparable_packs, key=lambda r: (r["quality"]["minimum_rating"],
                    r["quality"]["player_count"] or 0), default=None)
    return {"main": main, "other_players": other_players,
            "has_player": bool(players), "has_pack": bool(packs),
            "rating": max(rated, default=None),
            "coins": max((r["coins"] for r in coins), default=None),
            "pack_quality": best_pack["quality"] if best_pack else None,
            "best_pack_label": best_pack["label"] if best_pack else None}
