"""Head-to-head robustness checks for the recommended moves.

Each check asks a plain question: if the projections are off by a realistic amount (each
player's total ±20%, independently), how often does the choice still come out ahead of its
nearest rival? Comparing against one rival at a time avoids the trap of measuring noise:
across hundreds of players, some cheap player always gets a lucky draw.
"""
from __future__ import annotations

import random

NOISE = 0.2
DRAWS = 4000


def beat_prob(a: float, b: float, seed: int = 11) -> float:
    """P(a x noise > b x noise) with independent lognormal noise on each."""
    if a <= 0 and b <= 0:
        return 0.5
    rng = random.Random(seed)
    wins = sum(a * rng.lognormvariate(0, NOISE) > b * rng.lognormvariate(0, NOISE) for _ in range(DRAWS))
    return wins / DRAWS


def check_moves(players: list[dict], state, g0: dict, pairs: list[tuple[int, int]]) -> list[dict]:
    """For each (out, in): the chance the buy beats the sale, and beats the best alternative buy
    for the same slot that the same money could have bought."""
    by = {p["id"]: p for p in players}
    owned = set(state.ids)
    squad_after = set(g0["squad"])
    out = []
    for o, i in pairs:
        if i is None:
            continue
        budget = by[i]["price"] + g0["bank"]
        clubs = {}
        for pid in squad_after - {i}:
            clubs[by[pid]["team_id"]] = clubs.get(by[pid]["team_id"], 0) + 1
        alts = sorted((p for p in players if p["pos"] == by[i]["pos"] and p["id"] not in owned | squad_after
                       and p["price"] <= budget and clubs.get(p["team_id"], 0) < 3 and p["avail_next"] > 0.5),
                      key=lambda p: -p["total"])[:3]
        out.append({
            "out": o, "in": i,
            "beats_sale": beat_prob(by[i]["total"], by[o]["total"]),
            "alts": [(a["id"], beat_prob(by[i]["total"], a["total"])) for a in alts],
        })
    return out


def check_captain(players: list[dict], g0: dict) -> dict:
    by = {p["id"]: p for p in players}
    gw = g0["gw"]
    ranked = sorted(g0["xi"], key=lambda i: -by[i]["proj"].get(gw, 0))
    cap, rival = ranked[0], ranked[1]
    return {"captain": cap, "rival": rival,
            "prob": beat_prob(by[cap]["proj"].get(gw, 0), by[rival]["proj"].get(gw, 0))}
