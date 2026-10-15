"""Multi-gameweek transfer planner (mixed-integer programme, solved with HiGHS).

It plans the next ``horizon`` gameweeks at once, so a move is only made if it
pays off over the whole run, not just this weekend. It knows the real bank,
real selling prices, free transfers (rolling, capped at 5), hit cost, the
3-per-club rule, squad and formation rules, and gives banked free transfers a
value so it won't make marginal moves just because a transfer is available.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import pulp

SQUAD_SHAPE = {1: 2, 2: 5, 3: 5, 4: 3}
XI_MIN = {1: 1, 2: 3, 3: 2, 4: 1}
XI_MAX = {1: 1, 2: 5, 3: 5, 4: 3}


@dataclass
class PlanSettings:
    horizon_decay: float = 0.85  # weight on each later gameweek (later projections are less certain)
    bench_weight: float = 0.10  # value of bench points (auto-subs)
    hit_cost: float = 4.0
    ft_value: float = 1.5  # value of each free transfer still banked at the end of the plan
    transfer_cost: float = 0.3  # small cost per transfer so the plan doesn't churn for nothing
    max_transfers_per_gw: int = 5
    wildcard_gw: int | None = None  # gameweek in which transfers are free and unlimited
    candidates_per_pos: int = 45
    banned: tuple[int, ...] = ()
    locked: tuple[int, ...] = ()
    club_caps: dict | None = None  # team_id -> max players (stricter than the game's 3)
    freeze_first: bool = False  # forbid transfers in the first gameweek (the 'roll' baseline)
    first_gw_transfers: int | None = None  # force exactly this many transfers in the first gameweek


def _candidates(players: list[dict], owned: set[int], n: int) -> list[dict]:
    keep = []
    for pos in SQUAD_SHAPE:
        pool = sorted((p for p in players if p["pos"] == pos), key=lambda p: -p["total"])
        keep += pool[:n]
        # plus the cheapest fit players, so the plan can fund upgrades with real enablers
        cheap = sorted((p for p in pool[n:] if p.get("avail_next", 1) > 0.5), key=lambda p: (p["price"], -p["total"]))
        keep += cheap[:6]
    ids = {p["id"] for p in keep}
    keep += [p for p in players if p["id"] in owned and p["id"] not in ids]
    return keep


def plan(players: list[dict], state, gws: list[int], s: PlanSettings, proj_key: str = "proj") -> dict:
    owned = {p["id"]: p for p in state.picks}
    cands = [p for p in _candidates(players, set(owned), s.candidates_per_pos) if p["id"] not in s.banned]
    P = {p["id"]: p for p in cands}
    ids = list(P)
    T = gws
    prob = pulp.LpProblem("fpl", pulp.LpMaximize)
    B = pulp.LpVariable.dicts

    squad = B("squad", (ids, T), cat="Binary")
    xi = B("xi", (ids, T), cat="Binary")
    cap = B("cap", (ids, T), cat="Binary")
    tin = B("in", (ids, T), cat="Binary")
    tout = B("out", (ids, T), cat="Binary")
    bank = B("bank", T, lowBound=0)
    ft = B("ft", T, lowBound=0, upBound=5, cat="Integer")
    hits = B("hits", T, lowBound=0, cat="Integer")
    ft_end = pulp.LpVariable("ft_end", lowBound=0, upBound=5, cat="Integer")

    def sell(i):  # selling price: real one for owned players, purchase price for anyone bought in the plan
        return owned[i]["sell"] if i in owned else P[i]["price"]

    obj = 0
    for k, t in enumerate(T):
        w = s.horizon_decay ** k
        prev = (lambda i: 1 if i in owned else 0) if k == 0 else (lambda i, tp=T[k - 1]: squad[i][tp])
        prev_bank = state.bank if k == 0 else bank[T[k - 1]]
        for i in ids:
            prob += squad[i][t] == prev(i) + tin[i][t] - tout[i][t]
            prob += xi[i][t] <= squad[i][t]
            prob += cap[i][t] <= xi[i][t]
            if i in s.locked:
                prob += squad[i][t] == 1
            if i in owned:
                prob += tin[i][t] == 0 if k == 0 else tin[i][t] <= 1
            else:
                if k == 0:
                    prob += tout[i][t] == 0
        prob += bank[t] == prev_bank + pulp.lpSum(sell(i) * tout[i][t] - P[i]["price"] * tin[i][t] for i in ids)
        for pos, n in SQUAD_SHAPE.items():
            prob += pulp.lpSum(squad[i][t] for i in ids if P[i]["pos"] == pos) == n
            prob += pulp.lpSum(xi[i][t] for i in ids if P[i]["pos"] == pos) >= XI_MIN[pos]
            prob += pulp.lpSum(xi[i][t] for i in ids if P[i]["pos"] == pos) <= XI_MAX[pos]
        prob += pulp.lpSum(xi[i][t] for i in ids) == 11
        prob += pulp.lpSum(cap[i][t] for i in ids) == 1
        for club in {P[i]["team_id"] for i in ids}:
            cap_n = (s.club_caps or {}).get(club, 3)
            already = sum(1 for i in owned if P.get(i, {}).get("team_id") == club)
            prob += pulp.lpSum(squad[i][t] for i in ids if P[i]["team_id"] == club) <= max(cap_n, already)

        n_tr = pulp.lpSum(tin[i][t] for i in ids)
        if k == 0 and s.freeze_first:
            prob += n_tr == 0
        if k == 0 and s.first_gw_transfers is not None:
            prob += n_tr == s.first_gw_transfers
        next_ft = ft[T[k + 1]] if k + 1 < len(T) else ft_end
        if k == 0:
            prob += ft[t] == state.free_transfers
        if t == s.wildcard_gw:
            prob += hits[t] == 0
            prob += next_ft <= ft[t] + 1
        else:
            prob += n_tr <= s.max_transfers_per_gw
            prob += hits[t] >= n_tr - ft[t]
            prob += hits[t] <= n_tr
            prob += next_ft <= ft[t] - n_tr + hits[t] + 1
        prob += next_ft >= 1

        pts = {i: P[i][proj_key].get(t, 0.0) for i in ids}
        obj += w * (pulp.lpSum(pts[i] * (xi[i][t] + cap[i][t]) + s.bench_weight * pts[i] * (squad[i][t] - xi[i][t]) for i in ids)
                    - s.hit_cost * hits[t] - (0 if t == s.wildcard_gw else s.transfer_cost) * n_tr)
    obj += s.ft_value * ft_end
    prob += obj
    solver = pulp.HiGHS(msg=False, timeLimit=120, gapRel=0.002) if pulp.HiGHS().available() else pulp.PULP_CBC_CMD(msg=False, timeLimit=120, gapRel=0.002)
    prob.solve(solver)
    if pulp.LpStatus[prob.status] not in ("Optimal",):
        raise RuntimeError(f"optimiser status: {pulp.LpStatus[prob.status]}")

    v = lambda x: round(x.value() or 0)
    out = {"gws": []}
    for t in T:
        sq = [i for i in ids if v(squad[i][t])]
        lineup = [i for i in sq if v(xi[i][t])]
        bench = sorted((i for i in sq if i not in lineup), key=lambda i: (P[i]["pos"] != 1, -P[i][proj_key].get(t, 0)))
        bench = [b for b in bench if P[b]["pos"] != 1] + [b for b in bench if P[b]["pos"] == 1]
        ranked = sorted(lineup, key=lambda i: -P[i][proj_key].get(t, 0))
        captain = next(i for i in lineup if v(cap[i][t]))
        vice = next(i for i in ranked if i != captain)
        out["gws"].append({
            "gw": t,
            "in": [i for i in ids if v(tin[i][t])],
            "out": [i for i in ids if v(tout[i][t])],
            "hits": v(hits[t]),
            "ft": v(ft[t]),
            "bank": round(bank[t].value() or 0),
            "squad": sq, "xi": lineup, "bench": bench, "captain": captain, "vice": vice,
            "xi_points": sum(P[i][proj_key].get(t, 0) for i in lineup) + P[captain][proj_key].get(t, 0),
        })
    out["objective"] = pulp.value(prob.objective)
    return out


def stability(players: list[dict], state, gws: list[int], s: PlanSettings, runs: int = 12,
              player_noise: float = 0.2, week_noise: float = 0.1, seed: int = 7) -> dict:
    """Re-solve with every projection randomly perturbed, to see which first-gameweek moves survive.

    Most projection error belongs to the player (his rate is wrong in every week), so each run draws one
    lognormal factor per player (±20%) plus a smaller one per player-week (±10%). A move that only
    appears in a third of the runs is a coin flip."""
    import random

    rng = random.Random(seed)
    counts: dict[tuple, int] = {}
    caps: dict[int, int] = {}
    for _ in range(runs):
        noisy = []
        for p in players:
            q = dict(p)
            base = rng.lognormvariate(0, player_noise)
            q["noisy"] = {g: v * base * rng.lognormvariate(0, week_noise) for g, v in p["proj"].items()}
            q["total"] = sum(q["noisy"].values())
            noisy.append(q)
        r = plan(noisy, state, gws, replace(s, candidates_per_pos=min(s.candidates_per_pos, 30)), proj_key="noisy")
        g0 = r["gws"][0]
        for i in g0["in"]:
            counts[("in", i)] = counts.get(("in", i), 0) + 1
        for i in g0["out"]:
            counts[("out", i)] = counts.get(("out", i), 0) + 1
        if not g0["in"]:
            counts[("roll",)] = counts.get(("roll",), 0) + 1
        caps[g0["captain"]] = caps.get(g0["captain"], 0) + 1
    return {"runs": runs, "moves": counts, "captains": caps}
