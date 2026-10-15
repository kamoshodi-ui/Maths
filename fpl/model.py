"""Expected-points projections, fixture by fixture, over a multi-gameweek horizon.

How a projection is built (all inputs are live FPL data unless noted):

* Team strength: each side's attacking xG and defensive xGA per game (Understat
  when available, otherwise FPL/Opta), shrunk towards a prior taken from FPL's own
  pre-season team strength ratings so five games of data don't overreact.
* Fixture: expected goals for each side = attack x opponent defence / league
  average x home advantage. Clean-sheet and goals-conceded odds come from Poisson.
* Player: xG and xA per 90 from FPL/Opta, shrunk towards a price-implied prior
  (price is the market's pre-season view of the player), then scaled by how
  good the fixture is for his team's attack.
* Minutes: start rate this season x availability (injury flag, news), x typical
  minutes per start.
* Points: FPL 2026/27 scoring, including defensive contributions (10 CBIT for
  defenders, 12 CBIRT for midfielders and forwards), saves, bonus and cards.
* Real-life adjustments: anything the numbers can't see yet (a new manager, a
  role change, an injury return date) goes in ``notes.json`` with a reason, and
  every adjustment is printed in the audit.
"""
from __future__ import annotations

import math
import re
from datetime import date
from dataclasses import dataclass, field

POS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
GOAL_PTS = {1: 10, 2: 6, 3: 5, 4: 4}
CS_PTS = {1: 4, 2: 4, 3: 1, 4: 0}
DEFCON_THRESHOLD = {2: 10, 3: 12, 4: 12}
HOME_ADV = 1.10
TEAM_PRIOR_GAMES = 6.0
PLAYER_PRIOR_MINUTES = 540.0
LAST_SEASON_MIN_MINUTES = 900
MARKET_WEIGHT = 0.7


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def expected_conceded_deductions(lam: float) -> float:
    """E[floor(goals conceded / 2)] for Poisson(lam): -1 point per 2 conceded."""
    return sum((k // 2) * poisson_pmf(k, lam) for k in range(2, 15))


def prob_at_least(threshold: int, mean: float) -> float:
    """P(count >= threshold), overdispersed normal approximation (var = 1.6 x mean)."""
    if mean <= 0:
        return 0.0
    sd = math.sqrt(1.6 * mean)
    z = (threshold - 0.5 - mean) / sd
    return 0.5 * math.erfc(z / math.sqrt(2))


@dataclass
class TeamRates:
    attack: dict[int, float]  # expected goals scored per game
    defence: dict[int, float]  # expected goals conceded per game
    league_avg: float  # mean attack rate (goals per team per game)
    def_avg: float  # mean defence rate; the two match on real data, kept separate for safety
    observed: dict[int, dict] = field(default_factory=dict)


def team_rates(boot: dict, fixtures: list[dict], understat: dict[int, dict] | None, notes: dict, log: list) -> TeamRates:
    teams = boot["teams"]
    played = {t["id"]: 0 for t in teams}
    for f in fixtures:
        if f.get("finished"):
            played[f["team_h"]] += 1
            played[f["team_a"]] += 1

    # Observed rates: Understat first, FPL/Opta as fallback.
    obs_att, obs_def = {}, {}
    els = boot["elements"]
    for t in teams:
        tid = t["id"]
        g = played[tid]
        if understat and tid in understat and understat[tid]["games"]:
            u = understat[tid]
            obs_att[tid] = u["xG"] / u["games"]
            obs_def[tid] = u["xGA"] / u["games"]
            played[tid] = u["games"]
        elif g:
            obs_att[tid] = sum(float(e["expected_goals"]) for e in els if e["team"] == tid) / g
            keepers = [e for e in els if e["team"] == tid and e["element_type"] == 1 and e["minutes"] > 0]
            if keepers:
                gk = max(keepers, key=lambda e: e["minutes"])
                obs_def[tid] = float(gk["expected_goals_conceded"]) / (gk["minutes"] / 90)

    vals = list(obs_att.values()) or [1.35]
    avg = sum(vals) / len(vals)
    dvals = list(obs_def.values()) or vals
    davg = sum(dvals) / len(dvals)

    # Prior from FPL's own team strength ratings (pre-season real-world view). FPL sometimes
    # publishes only the coarse overall rating (2-5) with the attack/defence splits zeroed.
    detailed = all(t.get("strength_attack_home") and t.get("strength_defence_home") for t in teams)

    def rating(t):
        return (t.get("strength_overall_home") or 3) + (t.get("strength_overall_away") or 3)

    mean_r = sum(rating(t) for t in teams) / len(teams)

    def prior(t):
        if detailed:
            sa = (t["strength_attack_home"] + t["strength_attack_away"]) / 2
            sd = (t["strength_defence_home"] + t["strength_defence_away"]) / 2
            ma = sum((x["strength_attack_home"] + x["strength_attack_away"]) / 2 for x in teams) / len(teams)
            md = sum((x["strength_defence_home"] + x["strength_defence_away"]) / 2 for x in teams) / len(teams)
            return avg * sa / ma, davg * md / sd
        # each overall-rating step (summed home+away) ~ 10% more goals scored and 10% fewer conceded
        step = rating(t) - mean_r
        return avg * math.exp(0.1 * step), davg * math.exp(-0.1 * step)

    attack, defence = {}, {}
    for t in teams:
        tid, g = t["id"], played[t["id"]]
        prior_a, prior_d = prior(t)
        k = TEAM_PRIOR_GAMES
        attack[tid] = (g * obs_att.get(tid, prior_a) + k * prior_a) / (g + k)
        defence[tid] = (g * obs_def.get(tid, prior_d) + k * prior_d) / (g + k)

    observed = {tid: {"att": obs_att.get(tid), "def": obs_def.get(tid), "games": played[tid]} for tid in played}
    return TeamRates(attack, defence, avg, davg, observed)


def fixture_xg(rates: TeamRates, team: int, opp: int, home: bool) -> float:
    """Expected goals for ``team`` against ``opp``."""
    ha = HOME_ADV if home else 1 / HOME_ADV
    return rates.attack[team] * rates.defence[opp] / rates.def_avg * ha


def fixtures_by_team(fixtures: list[dict], gws: list[int]) -> dict[int, dict[int, list[tuple[int, bool]]]]:
    """team -> gw -> [(opponent, is_home)]; blanks are empty lists, doubles have two entries."""
    out: dict[int, dict[int, list]] = {}
    for f in fixtures:
        if f.get("event") in gws:
            out.setdefault(f["team_h"], {}).setdefault(f["event"], []).append((f["team_a"], True))
            out.setdefault(f["team_a"], {}).setdefault(f["event"], []).append((f["team_h"], False))
    return out


def _fit_price_prior(els: list[dict], key: str) -> dict[int, tuple[float, float]]:
    """Per position, minutes-weighted least squares of <key> per 90 on price."""
    fits = {}
    for pos in POS:
        rows = [(e["now_cost"] / 10, float(e[key]) / (e["minutes"] / 90), e["minutes"])
                for e in els if e["element_type"] == pos and e["minutes"] >= 270]
        if len(rows) < 5:
            fits[pos] = (0.05, 0.0)
            continue
        w = sum(r[2] for r in rows)
        mx = sum(r[0] * r[2] for r in rows) / w
        my = sum(r[1] * r[2] for r in rows) / w
        sxx = sum(r[2] * (r[0] - mx) ** 2 for r in rows)
        sxy = sum(r[2] * (r[0] - mx) * (r[1] - my) for r in rows)
        b = sxy / sxx if sxx else 0.0
        fits[pos] = (my - b * mx, b)
    return fits


def by_gw(value, gw: int, default: float = 1.0) -> float:
    """A notes.json value: a number, or {"<gw>": number, ...} where each value holds until the next listed gameweek."""
    if value is None:
        return default
    if not isinstance(value, dict):
        return float(value)
    pts = sorted((int(g), float(v)) for g, v in value.items())
    val = pts[0][1]
    for g, v in pts:
        if g <= gw:
            val = v
    return val


MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def return_gw(news: str, gw_start: dict[int, date]) -> int | None:
    """First gameweek a player can play, from FPL news like 'Expected back 1 Nov' or 'Suspended until 7 Nov'."""
    m = re.search(r"(?:Expected back|Suspended until)\s+(\d{1,2})\s+([A-Z][a-z]{2})", news or "")
    if not m or m.group(2) not in MONTHS:
        return None
    first = min(gw_start.values())
    month, day = MONTHS[m.group(2)], int(m.group(1))
    year = first.year if month >= first.month else first.year + 1
    back = date(year, month, day)
    later = [g for g, d in gw_start.items() if d >= back]
    return min(later) if later else max(gw_start) + 1


def _availability(el: dict, k: int, gw: int, override: dict | None, gw_start: dict[int, date] | None = None) -> float:
    """Chance of being available in ``gw``, which is k gameweeks after the next deadline."""
    if override and "availability" in override:
        return by_gw(override["availability"], gw)
    status = el.get("status", "a")
    if status == "u":
        return 0.0
    cop = el.get("chance_of_playing_next_round")
    if cop is None:
        return 1.0 if status == "a" else 0.5
    cop = cop / 100
    back = return_gw(el.get("news", ""), gw_start) if gw_start else None
    if back is not None:  # a dated return or ban: out until then, then a short ramp back to full
        return cop if gw < back else (0.85 if gw == back and status == "i" else 1.0)
    if status == "s":
        return 0.0 if k == 0 else 1.0
    if status == "i" and cop == 0:  # injured, no date: a slower return
        return min(1.0, 0.2 * k)
    return cop + (1 - cop) * min(1.0, k / 3)


def project(boot: dict, fixtures: list[dict], next_gw: int, horizon: int,
            understat_teams: dict[int, dict] | None = None, notes: dict | None = None,
            history: dict[int, dict] | None = None) -> tuple[list[dict], TeamRates, list[str]]:
    notes = notes or {}
    history = history or {}
    log: list[str] = []
    gws = list(range(next_gw, min(next_gw + horizon, 39)))
    rates = team_rates(boot, fixtures, understat_teams, notes, log)
    fx = fixtures_by_team(fixtures, gws)
    els = boot["elements"]
    teams = {t["id"]: t for t in boot["teams"]}
    prior_xg = _fit_price_prior(els, "expected_goals")
    prior_xa = _fit_price_prior(els, "expected_assists")
    games = {tid: max(o["games"], 1) for tid, o in rates.observed.items()}

    gw_start = {}
    for ev in boot["events"]:
        gw_start[ev["id"]] = date.fromisoformat(ev["deadline_time"][:10])
    team_notes = {t["id"]: notes.get("teams", {}).get(t["short_name"]) for t in boot["teams"]}
    for t in boot["teams"]:
        adj = team_notes[t["id"]]
        if adj:
            log.append(f'{t["short_name"]}: goals scored x{adj.get("attack_mult", 1.0)}, goals conceded x{adj.get("defence_mult", 1.0)}'
                       f' — {adj.get("reason", "no reason given")}')

    def tmult(team, key, gw):
        adj = team_notes.get(team)
        return by_gw(adj.get(key), gw) if adj else 1.0

    # Bookmaker goal lines for one gameweek: they already price in team news, home/away form and
    # everything else, so they're blended in (and replace the team multipliers) for those fixtures.
    market = notes.get("market") or {}
    market_gw = market.get("gw")
    market_fx = {tuple(k.split("-")): v for k, v in market.get("fixtures", {}).items()}
    short = {t["id"]: t["short_name"] for t in boot["teams"]}
    if market_fx:
        log.append(f'GW{market_gw}: bookmaker goal lines blended in at {MARKET_WEIGHT:.0%} for {len(market_fx)} fixtures'
                   f' — {market.get("source", "no source given")}')

    def fixture_goals(tid, opp, home, gw):
        """(goals for tid, goals for opp) in this fixture."""
        h, a = (tid, opp) if home else (opp, tid)
        line = market_fx.get((short[h], short[a])) if gw == market_gw else None
        for_t = fixture_xg(rates, tid, opp, home)
        for_o = fixture_xg(rates, opp, tid, not home)
        if line:
            mt, mo = (line[0], line[1]) if home else (line[1], line[0])
            return (MARKET_WEIGHT * mt + (1 - MARKET_WEIGHT) * for_t, MARKET_WEIGHT * mo + (1 - MARKET_WEIGHT) * for_o)
        return (for_t * tmult(tid, "attack_mult", gw) * tmult(opp, "defence_mult", gw),
                for_o * tmult(opp, "attack_mult", gw) * tmult(tid, "defence_mult", gw))

    by_name = {}
    for e in els:
        by_name.setdefault(e["web_name"].lower(), e["id"])
    overrides = {}
    for key, o in notes.get("players", {}).items():
        pid = int(key) if str(key).isdigit() else by_name.get(str(key).lower())
        if pid:
            overrides[pid] = o
        else:
            log.append(f"notes.json: no player called '{key}' — ignored")

    out = []
    for e in els:
        pos, tid = e["element_type"], e["team"]
        if pos not in POS:
            continue
        mins = e["minutes"]
        price = e["now_cost"] / 10
        ov = overrides.get(e["id"])

        # Attacking rates per 90, shrunk to a price-implied prior.
        a0, b0 = prior_xg[pos]
        a1, b1 = prior_xa[pos]
        m = PLAYER_PRIOR_MINUTES
        p_xg = max(a0 + b0 * price, 0.0)
        p_xa = max(a1 + b1 * price, 0.0)
        h = history.get(e["id"], {})
        if h.get("last_mins", 0) >= LAST_SEASON_MIN_MINUTES:
            # Last season's Understat output is a better starting point than price alone.
            p_xg = 0.5 * p_xg + 0.5 * h["last_xg90"]
            p_xa = 0.5 * p_xa + 0.5 * h["last_xa90"]
        xg90 = (float(e["expected_goals"]) + m / 90 * p_xg) / ((mins + m) / 90)
        xa90 = (float(e["expected_assists"]) + m / 90 * p_xa) / ((mins + m) / 90)
        n90 = max(mins / 90, 0.0)
        dc90 = float(e.get("defensive_contribution", 0) or 0) / n90 if n90 >= 1 else 0.0
        bonus90 = (e["bonus"] + m / 90 * 0.15) / ((mins + m) / 90)
        saves90 = e["saves"] / n90 if n90 >= 1 else 3.0
        yc90 = e["yellow_cards"] / n90 if n90 >= 1 else 0.1
        mult = 1.0
        if ov and "xgi_mult" in ov:
            mult = ov["xgi_mult"]
            xg90 *= mult
            xa90 *= mult

        start_rate = (e["starts"] + 0.5) / (games.get(tid, 1) + 1)
        if "recent_start_rate" in h:
            # Weight the last three team games as heavily as the whole season: catches benchings and returns.
            start_rate = 0.5 * start_rate + 0.5 * h["recent_start_rate"]
        start_override = ov.get("start_prob") if ov else None
        mins_per_start = min(90.0, max(60.0, mins / e["starts"])) if e["starts"] else 75.0
        f = mins_per_start / 90
        p60 = 0.92 if mins_per_start >= 80 else 0.75

        per_gw, nxt = {}, None
        for k, gw in enumerate(gws):
            av = _availability(e, k, gw, ov, gw_start)
            total = 0.0
            for opp, home in fx.get(tid, {}).get(gw, []):
                team_xg, opp_xg = fixture_goals(tid, opp, home, gw)
                scale = team_xg / rates.attack[tid]
                goals = xg90 * scale * f
                assists = xa90 * scale * f
                comp = {
                    "appearance": 2 * p60 + 1 * (1 - p60),
                    "goals": goals * GOAL_PTS[pos],
                    "assists": assists * 3,
                    "clean_sheet": CS_PTS[pos] * p60 * math.exp(-opp_xg * f),
                    "conceded": -expected_conceded_deductions(opp_xg * f) if pos in (1, 2) else 0.0,
                    "saves": (saves90 * opp_xg / rates.league_avg * f) / 3 * 0.85 if pos == 1 else 0.0,
                    "defcon": 2 * prob_at_least(DEFCON_THRESHOLD[pos], dc90 * f) if pos != 1 else 0.0,
                    "bonus": bonus90 * f * (0.7 + 0.3 * scale),
                    "cards": -yc90 * f,
                }
                sr = by_gw(start_override, gw, start_rate) if start_override is not None else start_rate
                pts = sum(comp.values()) * sr * av
                total += pts
                if k == 0 and nxt is None:
                    nxt = {"opp": teams[opp]["short_name"] + (" (H)" if home else " (A)"),
                           "team_xg": team_xg, "opp_xg": opp_xg,
                           "components": {c: v * sr * av for c, v in comp.items()}}
            per_gw[gw] = total

        if ov:
            log.append(f'{e["web_name"]}: ' + ", ".join(f"{k}={v}" for k, v in ov.items() if k not in ("reason", "name"))
                       + f' — {ov.get("reason", "no reason given")}')

        out.append({
            "id": e["id"], "name": e["web_name"], "team": teams[tid]["short_name"], "team_id": tid,
            "pos": pos, "pos_name": POS[pos], "price": e["now_cost"],
            "proj": per_gw, "total": sum(per_gw.values()), "next": nxt,
            "xg90": xg90, "xa90": xa90, "dc90": dc90,
            "start_rate": by_gw(start_override, next_gw, start_rate) if start_override is not None else start_rate,
            "avail_next": _availability(e, 0, next_gw, ov, gw_start), "status": e["status"], "news": e.get("news", ""),
            "ownership": float(e["selected_by_percent"]), "points": e["total_points"], "minutes": mins,
            "form": float(e["form"]), "xg": float(e["expected_goals"]), "xa": float(e["expected_assists"]),
            "goals": e["goals_scored"], "assists": e["assists"],
            "transfers_in_event": e.get("transfers_in_event", 0), "transfers_out_event": e.get("transfers_out_event", 0),
            "pen_order": e.get("penalties_order"),
            "recent_xgi90": h.get("recent_xgi90"), "recent_starts": h.get("recent_starts"),
            "recent_team_games": h.get("recent_team_games"),
        })
    return out, rates, log
