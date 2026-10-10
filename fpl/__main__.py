"""Command line: ``python -m fpl audit --team 2347384``.

Run from the repository root. Writes the audit to fpl/reports/ and prints the path.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from . import elite as elite_mod
from . import understat
from .api import FPLClient
from .model import fixtures_by_team, project
from .optimise import PlanSettings, plan, stability
from .report import render
from .state import build_state

HERE = Path(__file__).resolve().parent
DEFAULT_TEAM = 2347384


def load_notes(path: Path) -> dict:
    if not path.exists():
        return {}
    notes = json.loads(path.read_text(encoding="utf-8"))
    for section in ("players", "teams"):  # keys starting with "_" are examples/comments
        notes[section] = {k: v for k, v in notes.get(section, {}).items() if not k.startswith("_")}
    return notes


def resolve(boot: dict, names: list[str]) -> tuple[int, ...]:
    ids = []
    for n in names:
        hit = [e["id"] for e in boot["elements"] if e["web_name"].lower() == n.lower() or str(e["id"]) == n]
        if not hit:
            sys.exit(f"Unknown player: {n}")
        ids.append(hit[0])
    return tuple(ids)


def audit(args) -> Path:
    client = FPLClient(args.offline)
    boot = client.bootstrap()
    fixtures = client.fixtures()
    st = build_state(client, args.team, args.ft)
    if args.bank is not None:
        st.bank = round(args.bank * 10)
    notes = load_notes(Path(args.notes))
    gws = list(range(st.next_gw, min(st.next_gw + args.horizon, 39)))

    us_ok, us_teams, us_players = False, None, {}
    if not args.no_understat:
        try:
            season = int(boot["events"][0]["deadline_time"][:4])
            us = understat.fetch_league(season, client.cache, offline=bool(args.offline))
            us_teams = understat.team_table(us, boot["teams"])
            us_players = understat.match_players(us, boot["elements"], boot["teams"])
            us_ok = bool(us_teams)
        except Exception as exc:  # report says plainly that Understat was missing
            print(f"Understat unavailable: {exc}", file=sys.stderr)

    players, rates, log = project(boot, fixtures, st.next_gw, args.horizon, us_teams, notes)

    avoid = {t["id"] for t in boot["teams"] if t["short_name"] in {x.upper() for x in args.avoid_teams}}
    owned_ids = set(st.ids)
    banned = resolve(boot, args.ban) + tuple(e["id"] for e in boot["elements"] if e["team"] in avoid and e["id"] not in owned_ids)
    settings = PlanSettings(
        wildcard_gw=args.wildcard, banned=banned, locked=resolve(boot, args.lock),
        hit_cost=4.0, ft_value=args.ft_value,
    )
    best = plan(players, st, gws, settings)
    hold = plan(players, st, gws, replace(settings, freeze_first=True))
    gain = best["objective"] - hold["objective"]
    by_count = [(0, hold, 0.0)]
    for n in range(1, min(st.free_transfers, 5) + 1):
        if n == len(best["gws"][0]["in"]) and not best["gws"][0]["hits"]:
            r = best
        else:
            r = plan(players, st, gws, replace(settings, first_gw_transfers=n))
        by_count.append((n, r, r["objective"] - hold["objective"]))
    # Don't churn: take the fewest moves that get within 0.5 pts of the best plan.
    _, best, gain = next((c for c in by_count if c[2] >= gain - 0.5), (None, best, gain))
    stab = stability(players, st, gws, settings, runs=args.stability) if args.stability else None

    last_gw = st.next_gw - 1
    elite = elite_mod.global_elite(client, last_gw, args.elite) if args.elite else None
    leagues = elite_mod.mini_leagues(client, args.team, last_gw) if args.leagues else []

    next_event = next(e for e in boot["events"] if e["id"] == st.next_gw)
    ctx = {
        "state": st, "players": players, "plan": best, "gws": gws, "gain": gain, "stability": stab,
        "by_count": by_count, "avoided": sorted(t["short_name"] for t in boot["teams"] if t["id"] in avoid),
        "elite": elite, "leagues": leagues, "rates": rates, "log": log, "settings": settings,
        "teams": boot["teams"], "team_short": {t["id"]: t["short_name"] for t in boot["teams"]},
        "fixtures": fixtures_by_team(fixtures, gws), "deadline": next_event["deadline_time"].replace("T", " ").replace("Z", " UTC"),
        "understat_ok": us_ok, "understat_players": us_players, "understat_teams": us_teams,
        "source": f"cached data in {args.offline}" if args.offline else "live FPL data",
    }
    out_dir = HERE / "reports"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"gw{st.next_gw:02d}-audit.md"
    path.write_text(render(ctx), encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m fpl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="full weekly audit: state, transfers, XI, captain, ownership")
    a.add_argument("--team", type=int, default=DEFAULT_TEAM)
    a.add_argument("--horizon", type=int, default=6, help="gameweeks to plan over")
    a.add_argument("--ft", type=int, help="override free transfers if the derived number is wrong")
    a.add_argument("--bank", type=float, help="override bank in £m")
    a.add_argument("--wildcard", type=int, help="plan with a Wildcard played in this gameweek")
    a.add_argument("--ban", nargs="*", default=[], help="players never to buy (web names)")
    a.add_argument("--lock", nargs="*", default=[], help="players never to sell (web names)")
    a.add_argument("--avoid-teams", nargs="*", default=[], help="clubs never to buy from (short names, e.g. COV TOT)")
    a.add_argument("--ft-value", type=float, default=1.5, help="points value of a banked free transfer")
    a.add_argument("--stability", type=int, default=12, help="perturbed re-runs for confidence (0 to skip)")
    a.add_argument("--elite", type=int, default=50, help="top-N overall managers to compare (0 to skip)")
    a.add_argument("--no-leagues", dest="leagues", action="store_false", help="skip mini-league comparison")
    a.add_argument("--no-understat", action="store_true")
    a.add_argument("--notes", default=str(HERE / "notes.json"))
    a.add_argument("--offline", help="replay a cached data folder instead of fetching")
    args = ap.parse_args(argv)
    if args.cmd == "audit":
        print(audit(args))


if __name__ == "__main__":
    main()
