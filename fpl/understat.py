"""Understat league data (team xG/xGA, player npxG/xA), matched onto FPL players.

Understat is the independent second source: FPL/Opta xG drives the projections,
Understat is used to cross-check them and to flag over/under-performance.
"""
from __future__ import annotations

import codecs
import json
import re
import unicodedata
from pathlib import Path

import requests

URL = "https://understat.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (fpl-engine)", "X-Requested-With": "XMLHttpRequest"}

# Understat team title -> FPL team "name". Unlisted names are matched loosely.
TEAM_ALIASES = {
    "Manchester City": "Man City",
    "Manchester United": "Man Utd",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham": "Spurs",
    "Wolverhampton Wanderers": "Wolves",
    "West Ham": "West Ham",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Coventry City": "Coventry",
    "Leeds United": "Leeds",
    "Sheffield United": "Sheffield Utd",
}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", s.replace("-", " ")).strip()


def _embedded(html: str, var: str):
    m = re.search(var + r"\s*=\s*JSON\.parse\('(.*?)'\)", html)
    if not m:
        return None
    return json.loads(codecs.decode(m.group(1), "unicode_escape"))


def fetch_league(season: int, cache_dir: Path, offline: bool = False) -> dict:
    """Return {"players": [...], "teams": {...}} for an EPL season (season = starting year)."""
    path = cache_dir / f"understat_EPL_{season}.json"
    if offline or path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    s = requests.Session()
    s.headers.update(HEADERS)
    data = None
    try:  # current site: JSON endpoint
        r = s.get(f"{URL}/getLeagueData/EPL/{season}", timeout=30)
        r.raise_for_status()
        j = r.json()
        data = {"players": j["players"], "teams": j["teams"]}
    except (requests.RequestException, ValueError, KeyError):
        r = s.get(f"{URL}/league/EPL/{season}", timeout=30)  # older site: data embedded in page
        r.raise_for_status()
        data = {"players": _embedded(r.text, "playersData"), "teams": _embedded(r.text, "teamsData")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def team_table(us: dict, fpl_teams: list[dict]) -> dict[int, dict]:
    """Per FPL team id: games, npxG, npxGA, xG, xGA, goals, conceded (season totals)."""
    by_name = {t["name"]: t["id"] for t in fpl_teams}
    folded = {_fold(t["name"]): t["id"] for t in fpl_teams}
    out = {}
    for t in us["teams"].values():
        title = t["title"]
        fid = by_name.get(TEAM_ALIASES.get(title, title)) or folded.get(_fold(title))
        if fid is None:
            continue
        h = t["history"]
        out[fid] = {
            "games": len(h),
            "xG": sum(float(x["xG"]) for x in h),
            "xGA": sum(float(x["xGA"]) for x in h),
            "npxG": sum(float(x["npxG"]) for x in h),
            "npxGA": sum(float(x["npxGA"]) for x in h),
            "goals": sum(int(x["scored"]) for x in h),
            "conceded": sum(int(x["missed"]) for x in h),
        }
    return out


def match_players(us: dict, elements: list[dict], fpl_teams: list[dict]) -> dict[int, dict]:
    """Map FPL element id -> Understat player row, by team plus folded name."""
    team_of = {}
    for t in fpl_teams:
        team_of[t["name"]] = t["id"]
    by_team: dict[int, list[dict]] = {}
    for p in us["players"]:
        last_team = p["team_title"].split(",")[-1].strip()  # transferred players list several clubs
        fid = team_of.get(TEAM_ALIASES.get(last_team, last_team))
        if fid is None:
            fid = next((t["id"] for t in fpl_teams if _fold(t["name"]) == _fold(last_team)), None)
        if fid is not None:
            by_team.setdefault(fid, []).append(p)
    out = {}
    for el in elements:
        cands = by_team.get(el["team"], [])
        full = _fold(f'{el["first_name"]} {el["second_name"]}')
        web = _fold(el["web_name"])
        best = None
        for p in cands:
            un = _fold(p["player_name"])
            if un == full:
                best = p
                break
            toks = set(un.split())
            if web in toks or (web and web in un) or toks <= set(full.split()):
                best = best or p
        if best:
            out[el["id"]] = best
    return out
