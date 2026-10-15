"""Turns the state, projections, plan and ownership data into a Markdown audit."""
from __future__ import annotations

from datetime import datetime, timezone

from .model import fixture_xg
from .state import CHIP_NAMES, FIRST_HALF_LAST_GW


def m(tenths: int | float) -> str:
    return f"£{tenths / 10:.1f}m"


def pct(x: float) -> str:
    return f"{x:.0%}"


def render(ctx: dict) -> str:
    st, P, plan, gws = ctx["state"], ctx["players"], ctx["plan"], ctx["gws"]
    byid = {p["id"]: p for p in P}
    owned = {p["id"]: p for p in st.picks}
    elite = ctx.get("elite")
    leagues = ctx.get("leagues") or []
    us = ctx.get("understat_players") or {}
    stab = ctx.get("stability")
    L = []
    w = L.append

    def name(i):
        p = byid[i]
        return f'{p["name"]} ({p["team"]})'

    def eo(i):
        return f'{elite["owners"].get(i, 0)}/{elite["n"]}' if elite else "–"

    g0 = plan["gws"][0]
    w(f"# FPL audit — {st.team_name}, Gameweek {st.next_gw}")
    w("")
    w(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from {ctx.get('source', 'live FPL data')}"
      + (" + Understat" if ctx.get("understat_ok") else " (Understat unavailable — FPL/Opta xG only)")
      + f". Deadline: **{ctx['deadline']}**.")
    if st.overall_rank:
        w(f"Overall: {st.total_points} pts, rank {st.overall_rank:,}.")
    w("")

    # ---------------------------------------------------------------- state
    w("## Where you stand (read from the API, not from memory)")
    w("")
    w(f"| Bank | Free transfers | Squad selling value | Chips left (set {'1, expires GW19' if st.next_gw <= FIRST_HALF_LAST_GW else '2'}) |")
    w("|---|---|---|---|")
    w(f"| {m(st.bank)} | {st.free_transfers} ({st.ft_source}) | {m(st.value)} | "
      f"{', '.join(CHIP_NAMES[c] for c in st.chips_left) or 'none'} |")
    if st.pending_transfers:
        w("")
        w("Transfers already made for this deadline: " + "; ".join(
            f'{byid[t["element_out"]]["name"]} → {byid[t["element_in"]]["name"]}' for t in st.pending_transfers))
    w("")

    # ---------------------------------------------------------------- verdict
    w("## The verdict")
    w("")
    horizon = f"GW{gws[0]}–{gws[-1]}"
    if g0["in"]:
        outs, ins = g0["out"], g0["in"]
        gain = ctx["gain"]
        w(f"**{len(ins)} transfer{'s' if len(ins) > 1 else ''}"
          + (f", {g0['hits']} hit{'s' if g0['hits'] > 1 else ''} (−{4 * g0['hits']})" if g0["hits"] else "")
          + f".** Projected gain over {horizon} versus rolling: **{gain:+.1f} pts** (net of hits and the value of a banked transfer).")
        if gain < 2.0:
            w("")
            w(f"**This is marginal.** {gain:+.1f} pts over {len(gws)} weeks is inside the noise of any projection. "
              "Rolling the transfer is an equally defensible choice — only make it if the real-life picture agrees.")
        w("")
        w("| Out | Sell | In | Buy | Proj " + horizon + " out → in | Buy beats sale | Buy beats the next-best options |")
        w("|---|---|---|---|---|---|---|")
        checks = {(c["out"], c["in"]): c for c in ctx.get("move_checks", [])}
        for o, i in _pair(outs, ins, byid):
            c = checks.get((o, i))
            bs = pct(c["beats_sale"]) if c else "–"
            alts = ", ".join(f'{byid[a]["name"]} {pct(p_)}' for a, p_ in c["alts"]) if c else "–"
            w(f'| {name(o)} | {m(owned[o]["sell"])} | {name(i)} | {m(byid[i]["price"])} | '
              f'{byid[o]["total"]:.1f} → {byid[i]["total"]:.1f} | {bs} | {alts} |')
        w("")
        w("*Head-to-head checks: how often the choice still wins if every projection is off by a realistic ±20%. "
          "Around 50% against an alternative means it's a toss-up: pick on the real-life picture. 75%+ is a clear call.*")
        w("")
        w(f"Bank after: {m(g0['bank'])}. Free transfers next week: {plan['gws'][1]['ft'] if len(plan['gws']) > 1 else '–'}.")
    else:
        w(f"**Roll the transfer.** No move beats banking it over {horizon}. "
          f"You go into GW{gws[1] if len(gws) > 1 else '?'} with {plan['gws'][1]['ft'] if len(plan['gws']) > 1 else st.free_transfers + 1} free transfers.")
    if ctx.get("by_count"):
        w("")
        w("**How many transfers?** The best plan for each number of moves this week, against rolling. "
          "The verdict takes the fewest moves that get within 0.5 pts of the best.")
        w("")
        w("| Moves | This week | Gain over " + horizon + " |")
        w("|---|---|---|")
        for n, r, g in ctx["by_count"]:
            mv = "; ".join(f"{byid[o]['name']} → {byid[i]['name']}" for o, i in _pair(r["gws"][0]["out"], r["gws"][0]["in"], byid)) or "roll"
            w(f"| {n} | {mv} | {g:+.1f} |")
    if ctx.get("avoided"):
        w("")
        w(f"*Not buying from: {', '.join(ctx['avoided'])} (your choice, via --avoid-teams).*")
    if stab:
        w("")
        moves = ", ".join(f'{k[0]} {byid[k[1]]["name"]} {v}/{stab["runs"]}' for k, v in sorted(stab["moves"].items(), key=lambda kv: -kv[1]) if len(k) == 2)
        w(f"*Full re-solves with shaken projections ({stab['runs']} runs): {moves}; rolled in {stab['moves'].get(('roll',), 0)}.*")
    w("")

    # ---------------------------------------------------------------- lineup
    w(f"## GW{g0['gw']} team")
    w("")
    by_pos = sorted(g0["xi"], key=lambda i: (byid[i]["pos"], -byid[i]["proj"].get(g0["gw"], 0)))
    shape = "-".join(str(sum(1 for i in g0["xi"] if byid[i]["pos"] == k)) for k in (2, 3, 4))
    w(f"**XI ({shape}):** " + " · ".join(
        f'{byid[i]["name"]}{" (C)" if i == g0["captain"] else " (V)" if i == g0["vice"] else ""} {byid[i]["proj"].get(g0["gw"], 0):.1f}'
        for i in by_pos))
    w("")
    w("**Bench:** " + " · ".join(f'{n + 1}. {byid[i]["name"]} {byid[i]["proj"].get(g0["gw"], 0):.1f}' for n, i in enumerate(g0["bench"])))
    w("")
    capline = f'**Captain {byid[g0["captain"]]["name"]}, vice {byid[g0["vice"]]["name"]}.**'
    cc = ctx.get("captain_check")
    if cc:
        capline += f' {byid[cc["captain"]]["name"]} outscores the next-best in your XI ({byid[cc["rival"]]["name"]}) in {pct(cc["prob"])} of shaken projections.'
    tc = ctx.get("tc_window")
    if tc:
        capline += f' **Triple Captain:** {tc}'
    if elite and elite["captains"]:
        top_cap = max(elite["captains"].items(), key=lambda kv: kv[1])
        capline += f' Top {elite["n"]} managers last GW: {byid[top_cap[0]]["name"]} captained by {top_cap[1]}.'
    w(capline)
    w("")
    if len(plan["gws"]) > 1:
        w("**Provisional plan after this week** (re-run each week; it will change as data does):")
        w("")
        for g in plan["gws"][1:]:
            mv = ", ".join(f"{byid[o]['name']} → {byid[i]['name']}" for o, i in _pair(g["out"], g["in"], byid)) or "roll"
            w(f"- GW{g['gw']}: {mv}" + (f" ({g['hits']} hit)" if g["hits"] else "") + f"; captain {byid[g['captain']]['name']}")
        w("")

    # ---------------------------------------------------------------- squad
    w("## Your fifteen")
    w("")
    head = "| Player | Pos | Price (sell) | Status | Starts (last 3) | xG/90 | xA/90 | xGI/90 last 4 | DefCon/90 | G+A vs xG+xA | Next | " + " | ".join(f"GW{g}" for g in gws) + " | Total | Top-" + (str(elite["n"]) if elite else "N") + " own |"
    w(head)
    w("|" + "---|" * (head.count("|") - 1))
    for i in sorted(owned, key=lambda i: (byid[i]["pos"], -byid[i]["total"])):
        p = byid[i]
        status = "✅" if p["avail_next"] >= 0.99 else f'⚠️ {p["avail_next"]:.0%} {p["news"]}'
        nxt = p["next"]["opp"] if p["next"] else "blank"
        w(f'| {p["name"]} ({p["team"]}) | {p["pos_name"]} | {m(p["price"])} ({m(owned[i]["sell"])}) | {status} | {p["start_rate"]:.0%}{_recent(p)} | '
          f'{p["xg90"]:.2f} | {p["xa90"]:.2f} | {_form(p)} | {p["dc90"]:.1f} | {_perf(p, us.get(i))} | {nxt} | '
          + " | ".join(f'{p["proj"].get(g, 0):.1f}' for g in gws) + f' | **{p["total"]:.1f}** | {eo(i)} |')
    w("")
    w("*Starts: model start chance (season and last three games weighted equally), with actual starts in the last three in brackets. "
      "xGI/90 last 4: Understat xG+xA per 90 over his last four league games — compare with the season xG/90 + xA/90 to see who's heating up or cooling off. "
      "G+A vs xG+xA: positive = scoring above chances (likely to cool), negative = owed. Understat where matched, else FPL/Opta.*")
    w("")

    # ---------------------------------------------------------------- alternatives
    w(f"## Best buys by position ({horizon} projection)")
    w("")
    budget_cap = st.bank + max(o["sell"] for o in st.picks)
    for pos, label in ((1, "Goalkeepers"), (2, "Defenders"), (3, "Midfielders"), (4, "Forwards")):
        pool = sorted((p for p in P if p["pos"] == pos and p["price"] <= budget_cap and p["avail_next"] > 0.5),
                      key=lambda p: -p["total"])[:8]
        w(f"**{label}**")
        w("")
        w("| Player | Price | Proj | Pts/£m | xG/90 | xA/90 | xGI/90 last 4 | Starts (last 3) | DefCon/90 | Next | Top own | Owned |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for p in pool:
            w(f'| {p["name"]} ({p["team"]}) | {m(p["price"])} | {p["total"]:.1f} | {p["total"] / (p["price"] / 10):.2f} | '
              f'{p["xg90"]:.2f} | {p["xa90"]:.2f} | {_form(p)} | {p["start_rate"]:.0%}{_recent(p)} | {p["dc90"]:.1f} | {p["next"]["opp"] if p["next"] else "blank"} | {eo(p["id"])} | '
              f'{"✓" if p["id"] in owned else ""} |')
        w("")

    # ---------------------------------------------------------------- ownership
    if elite:
        w(f"## What the top {elite['n']} managers in the world own")
        w("")
        top = sorted(elite["owners"].items(), key=lambda kv: -kv[1])[:20]
        w("| Player | Owned by | Captained by | You | Proj " + horizon + " |")
        w("|---|---|---|---|---|")
        for i, c in top:
            if i in byid:
                w(f'| {name(i)} | {c}/{elite["n"]} | {elite["captains"].get(i, 0)} | {"✓" if i in owned else "✗"} | {byid[i]["total"]:.1f} |')
        gaps = [(i, c) for i, c in top if i not in owned and c >= elite["n"] * 0.4 and i in byid]
        if gaps:
            w("")
            w("**Elite picks you don't have:** " + ", ".join(f'{byid[i]["name"]} ({c}/{elite["n"]}, model {byid[i]["total"]:.1f})' for i, c in gaps)
              + ". Where the model disagrees with the elite, the table above shows by how much — that's a judgement call, not an automatic move.")
        w("")
    for lg in leagues:
        own = lg["own"]
        w(f"## Mini-league: {lg['name']}")
        w("")
        gap = (lg["leader_total"] - lg["my_total"]) if lg["my_total"] is not None else None
        w(f"You are **{lg['my_rank']}** of {lg['size']}" + (f", {gap} pts behind {lg['leader_name']}." if gap else "."))
        w("")
        if own["n"]:
            after = set(g0["squad"])  # your squad after this week's recommended transfers
            share = lambda i: own["owners"].get(i, 0) / own["n"]
            threats = sorted((i for i in own["owners"] if i in byid and i not in after and share(i) >= 0.5),
                             key=lambda i: -byid[i]["total"])[:8]
            edges = sorted((i for i in after if share(i) <= 0.3 and byid[i]["total"] >= 8 and byid[i]["avail_next"] > 0.5),
                           key=lambda i: -byid[i]["total"])[:8]
            rows = [(i, share(i), False) for i in threats] + [(i, share(i), True) for i in edges]
            w(f"Compared with the {own['n']} rivals {'directly ahead of you' if lg['my_rank'] and lg['my_rank'] > 1 else 'chasing you'}, using your squad after this week's transfers:")
            w("")
            w("| Player | Rivals owning | You | Proj | What it means |")
            w("|---|---|---|---|---|")
            for i, share, mine in rows:
                meaning = "your differential — this is where you gain" if mine else "most leaders own him — his hauls cost you ground"
                w(f"| {name(i)} | {share:.0%} | {'✓' if mine else '✗'} | {byid[i]['total']:.1f} | {meaning} |")
            w("")

    # ---------------------------------------------------------------- league table
    ut = ctx.get("understat_teams")
    if ut:
        w("## League table: results against underlying numbers (Understat)")
        w("")
        w("Points minus expected points shows who is riding luck. A big positive gap usually closes, "
          "and a big negative one usually recovers. Non-penalty xG difference per game is the best single guide to who is actually good.")
        w("")
        w("| # | Team | P | Pts | xPts | Luck | GF–GA | npxG–npxGA per game |")
        w("|---|---|---|---|---|---|---|---|")
        rows = sorted(ut.items(), key=lambda kv: (-kv[1]["pts"], -(kv[1]["goals"] - kv[1]["conceded"]), -kv[1]["goals"]))
        for n, (tid, u) in enumerate(rows, 1):
            g = max(u["games"], 1)
            w(f'| {n} | {ctx["team_short"][tid]} | {u["games"]} | {u["pts"]} | {u["xpts"]:.1f} | {u["pts"] - u["xpts"]:+.1f} | '
              f'{u["goals"]}–{u["conceded"]} | {u["npxG"] / g:.2f}–{u["npxGA"] / g:.2f} ({(u["npxG"] - u["npxGA"]) / g:+.2f}) |')
        w("")

    # ---------------------------------------------------------------- teams
    w("## Team strength and fixtures")
    w("")
    w("Attack = expected goals per game, defence = expected goals conceded per game (model, after shrinkage). "
      "Fixture cells show the team's expected goals in that match: higher is better for attackers, "
      "and the opponent's expected goals (in brackets) lower is better for defenders.")
    w("")
    w("| Team | Attack | Defence | " + " | ".join(f"GW{g}" for g in gws) + " |")
    w("|---|---|---|" + "---|" * len(gws))
    rates = ctx["rates"]
    for t in sorted(ctx["teams"], key=lambda t: -(rates.attack[t["id"]] - rates.defence[t["id"]])):
        cells = []
        for g in gws:
            fx = ctx["fixtures"].get(t["id"], {}).get(g, [])
            cells.append(" + ".join(f'{ctx["team_short"][o]}{"" if h else "(a)"} {fixture_xg(rates, t["id"], o, h):.1f} ({fixture_xg(rates, o, t["id"], not h):.1f})' for o, h in fx) or "—")
        w(f'| {t["short_name"]} | {rates.attack[t["id"]]:.2f} | {rates.defence[t["id"]]:.2f} | ' + " | ".join(cells) + " |")
    w("")

    # ---------------------------------------------------------------- adjustments
    w("## Real-life adjustments applied (notes.json)")
    w("")
    if ctx["log"]:
        for line in ctx["log"]:
            w(f"- {line}")
    else:
        w("None. Everything above is pure data — add manager changes, role changes and injury return dates to `fpl/notes.json`.")
    w("")
    w("## Assumptions")
    w("")
    w(f"- Free transfers: {st.ft_source}. Saved transfers are kept through a Wildcard or Free Hit; cap of 5.")
    w(f"- Plan horizon {horizon}; each later week weighted ×{ctx['settings'].horizon_decay} because projections get less reliable; "
      f"a banked free transfer is worth {ctx['settings'].ft_value} pts; a hit costs {ctx['settings'].hit_cost:g}.")
    w("- Selling prices use the FPL rule (keep half of any rise, rounded down) from your actual purchase prices.")
    return "\n".join(L) + "\n"


def _form(p):
    return f'{p["recent_xgi90"]:.2f}' if p.get("recent_xgi90") is not None else "–"


def _recent(p):
    if p.get("recent_team_games"):
        return f' ({p["recent_starts"]}/{p["recent_team_games"]})'
    return ""


def _perf(p, u):
    if u:
        d = (int(u["goals"]) + int(u["assists"])) - (float(u["xG"]) + float(u["xA"]))
    else:
        d = (p["goals"] + p["assists"]) - (p["xg"] + p["xa"])
    return f"{d:+.1f}"


def _pair(outs, ins, byid):
    """Pair sales with purchases by position, for readable output."""
    ins = list(ins)
    pairs = []
    for o in sorted(outs, key=lambda i: byid[i]["pos"]):
        match = next((i for i in ins if byid[i]["pos"] == byid[o]["pos"]), ins[0] if ins else None)
        if match is not None:
            ins.remove(match)
        pairs.append((o, match))
    return pairs
