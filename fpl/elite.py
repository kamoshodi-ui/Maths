"""What the best managers own: the global top N, and the leaders of your own mini-leagues.

Global elite ownership is a sanity check on the model. Mini-league ownership is
what actually decides mini-leagues: a player your rivals all own can't gain you
ground, and one none of them own is where you can catch up.
"""
from __future__ import annotations

OVERALL_LEAGUE = 314


def ownership(client, entry_ids: list[int], gw: int) -> dict:
    owners: dict[int, int] = {}
    captains: dict[int, int] = {}
    chips: dict[str, int] = {}
    n = 0
    for eid in entry_ids:
        try:
            pk = client.picks(eid, gw)
        except Exception:
            continue
        n += 1
        for p in pk["picks"]:
            owners[p["element"]] = owners.get(p["element"], 0) + 1
            if p["is_captain"]:
                captains[p["element"]] = captains.get(p["element"], 0) + 1
        if pk.get("active_chip"):
            chips[pk["active_chip"]] = chips.get(pk["active_chip"], 0) + 1
    return {"n": n, "owners": owners, "captains": captains, "chips": chips}


def global_elite(client, gw: int, top: int = 50) -> dict:
    ids, page = [], 1
    while len(ids) < top:
        res = client.league(OVERALL_LEAGUE, page)["standings"]["results"]
        if not res:
            break
        ids += [r["entry"] for r in res]
        page += 1
    return ownership(client, ids[:top], gw)


def mini_leagues(client, team_id: int, gw: int, top: int = 10, max_size: int = 500) -> list[dict]:
    """Private classic leagues the manager is in: your rank, the gap, and what the leaders own."""
    entry = client.entry(team_id)
    out = []
    for lg in entry.get("leagues", {}).get("classic", []):
        if lg.get("league_type") != "x" or (lg.get("rank_count") or 0) > max_size:  # skip public and huge leagues
            continue
        st = client.league(lg["id"])
        results = st["standings"]["results"]
        if not results:
            continue
        me = next((r for r in results if r["entry"] == team_id), None)
        my_rank = me["rank"] if me else lg.get("entry_rank") or len(results)
        ahead = [r for r in results if r["entry"] != team_id and r["rank"] < my_rank]
        # The people you have to pass (closest first); if you lead, the ones chasing you.
        leaders = sorted(ahead, key=lambda r: -r["rank"])[:top] if ahead else [r for r in results if r["entry"] != team_id][:5]
        out.append({
            "name": lg["name"], "id": lg["id"],
            "my_rank": me["rank"] if me else lg.get("entry_rank"),
            "my_total": me["total"] if me else entry.get("summary_overall_points"),
            "leader_total": results[0]["total"], "leader_name": results[0]["player_name"],
            "size": lg.get("rank_count") or len(results),
            "leaders": [{"name": r["player_name"], "team": r["entry_name"], "total": r["total"], "rank": r["rank"]} for r in leaders],
            "own": ownership(client, [r["entry"] for r in leaders], gw),
        })
    return out
