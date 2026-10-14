"""Per-player history: recent starts (FPL) and recent and last-season output (Understat).

This is what stops five games of season averages from hiding a change that's happening right now.
Examples are a player who has been benched for the last two games, or a striker whose chances
have dried up. It also gives each player a sensible starting point from last season's numbers
instead of his price alone.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

UNDERSTAT = "https://understat.com/getPlayerData/{}"
HEADERS = {"User-Agent": "Mozilla/5.0 (fpl-engine)", "X-Requested-With": "XMLHttpRequest"}
RECENT_MATCHES = 4


def _understat_player(uid: str, cache: Path, offline: bool) -> dict | None:
    path = cache / "understat_players" / f"{uid}.json"
    if path.exists() or offline:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    try:
        r = requests.get(UNDERSTAT.format(uid), headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return None
    keep = {"matches": data.get("matches", []), "season": data.get("groups", {}).get("season", [])}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(keep), encoding="utf-8")
    return keep


def _relevant(e: dict) -> bool:
    return e["status"] != "u" and (e["minutes"] >= 90 or e["now_cost"] >= 55)


def collect(client, boot: dict, fixtures: list[dict], next_gw: int, us_players: dict[int, dict],
            season: int, offline: bool = False) -> dict[int, dict]:
    """pid -> {recent_start_rate, recent_starts, recent_team_games, recent_xgi90, recent_mins,
    last_xg90, last_xa90, last_mins}. Fields are missing when there's no data."""
    els = [e for e in boot["elements"] if _relevant(e)]
    team_gws: dict[int, list[int]] = {}
    for f in fixtures:
        if f.get("finished") and f.get("event"):
            team_gws.setdefault(f["team_h"], []).append(f["event"])
            team_gws.setdefault(f["team_a"], []).append(f["event"])

    def fpl_part(e):
        try:
            hist = client.get(f"element-summary/{e['id']}")["history"]
        except Exception:
            return e["id"], {}
        last = sorted(set(team_gws.get(e["team"], [])))[-3:]
        rows = [h for h in hist if h["round"] in last]
        if not last:
            return e["id"], {}
        started = {h["round"] for h in rows if h.get("starts", 1 if h["minutes"] >= 60 else 0)}
        starts = len(started & set(last))
        # The latest game counts most: a player who started it is back in the side, whatever
        # (often an injury) kept him out before; one who didn't is the real warning sign.
        latest = 1.0 if last[-1] in started else 0.0
        earlier = last[:-1]
        rate = latest if not earlier else 0.6 * latest + 0.4 * len(started & set(earlier)) / len(earlier)
        return e["id"], {"recent_starts": starts, "recent_team_games": len(last), "recent_start_rate": rate}

    def us_part(e):
        u = us_players.get(e["id"])
        if not u:
            return e["id"], {}
        data = _understat_player(u["id"], client.cache, offline)
        if not data:
            return e["id"], {}
        out = {}
        cur = sorted((m for m in data["matches"] if m.get("season") == str(season)), key=lambda m: m["date"], reverse=True)
        recent = cur[:RECENT_MATCHES]
        mins = sum(int(m["time"]) for m in recent)
        if mins:
            out["recent_xgi90"] = sum(float(m["xG"]) + float(m["xA"]) for m in recent) / mins * 90
            out["recent_mins"] = mins
        prev = [s for s in data["season"] if s.get("season") == str(season - 1)]
        pm = sum(int(s["time"]) for s in prev)
        if pm:
            out["last_mins"] = pm
            out["last_xg90"] = sum(float(s["xG"]) for s in prev) / pm * 90
            out["last_xa90"] = sum(float(s["xA"]) for s in prev) / pm * 90
        return e["id"], out

    result: dict[int, dict] = {e["id"]: {} for e in els}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for pid, part in pool.map(fpl_part, els):
            result[pid].update(part)
        for pid, part in pool.map(us_part, els):
            result[pid].update(part)
    return result
