"""Squad state, derived from the FPL API rather than from memory.

Bank, selling prices, free transfers and chips are all rebuilt from the
manager's public history on every run, so nothing has to be "kept track of".
Anything derived (rather than read directly) is marked as such in the report.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CHIP_NAMES = {"wildcard": "Wildcard", "freehit": "Free Hit", "bboost": "Bench Boost", "3xc": "Triple Captain"}
MAX_FT = 5
FIRST_HALF_LAST_GW = 19  # 2026/27: two chip sets, first set expires at the GW19 deadline


def sell_price(purchase: int, now: int) -> int:
    """FPL selling price in tenths: you keep half of any rise, rounded down; you eat all of a fall."""
    if now <= purchase:
        return now
    return purchase + (now - purchase) // 2


def derive_free_transfers(history: list[dict], chips_by_gw: dict[int, str], upto_gw: int) -> int:
    """Free transfers available for ``upto_gw + 1``.

    Rules applied: one FT accrues per gameweek, capped at 5; transfers made in a
    Wildcard or Free Hit week do not consume FTs (saved FTs are kept); GW1 is unlimited.
    """
    made = {h["event"]: h.get("event_transfers", 0) for h in history}
    ft = 1  # entering GW2
    for gw in range(2, upto_gw + 1):
        if chips_by_gw.get(gw) in ("wildcard", "freehit"):
            ft = min(MAX_FT, ft + 1)
        else:
            ft = min(MAX_FT, max(ft - made.get(gw, 0), 0) + 1)
    return ft


def chips_available(chips_used: list[dict], next_gw: int) -> list[str]:
    in_first_half = next_gw <= FIRST_HALF_LAST_GW
    used = {c["name"] for c in chips_used if (c["event"] <= FIRST_HALF_LAST_GW) == in_first_half}
    return [c for c in CHIP_NAMES if c not in used]


@dataclass
class SquadState:
    team_id: int
    team_name: str
    next_gw: int
    picks: list[dict]  # {id, purchase, now, sell}
    bank: int  # tenths of a million
    free_transfers: int
    ft_source: str
    chips_left: list[str]
    chips_used: list[dict]
    pending_transfers: list[dict] = field(default_factory=list)
    overall_rank: int | None = None
    total_points: int | None = None

    @property
    def ids(self) -> list[int]:
        return [p["id"] for p in self.picks]

    @property
    def value(self) -> int:
        return self.bank + sum(p["sell"] for p in self.picks)


def next_gameweek(bootstrap: dict) -> int:
    for e in bootstrap["events"]:
        if e["is_next"]:
            return e["id"]
    return bootstrap["events"][-1]["id"]


def build_state(client, team_id: int, ft_override: int | None = None) -> SquadState:
    boot = client.bootstrap()
    elements = {e["id"]: e for e in boot["elements"]}
    next_gw = next_gameweek(boot)
    current_gw = next_gw - 1

    entry = client.entry(team_id)
    hist = client.history(team_id)
    transfers = client.transfers(team_id)
    chips_by_gw = {c["event"]: c["name"] for c in hist.get("chips", [])}

    # The real squad: the latest GW that was not a Free Hit (a Free Hit squad reverts).
    squad_gw = current_gw
    while squad_gw > 1 and chips_by_gw.get(squad_gw) == "freehit":
        squad_gw -= 1
    picks = client.picks(team_id, squad_gw)
    owned = [p["element"] for p in picks["picks"]]
    bank = picks["entry_history"]["bank"]

    # Transfers already made for the upcoming deadline are not in any picks yet.
    pending = [t for t in transfers if t["event"] == next_gw]
    for t in sorted(pending, key=lambda t: t["time"]):
        owned = [t["element_in"] if x == t["element_out"] else x for x in owned]

    fh_weeks = {gw for gw, c in chips_by_gw.items() if c == "freehit"}
    last_buy: dict[int, int] = {}
    for t in sorted(transfers, key=lambda t: t["time"]):
        if t["event"] not in fh_weeks:
            last_buy[t["element_in"]] = t["element_in_cost"]

    rows = []
    for pid in owned:
        el = elements[pid]
        now = el["now_cost"]
        purchase = last_buy.get(pid, now - el.get("cost_change_start", 0))
        rows.append({"id": pid, "purchase": purchase, "now": now, "sell": sell_price(purchase, now)})

    if pending:  # recompute bank from the last known bank plus pending sells/buys
        for t in pending:
            out = elements[t["element_out"]]
            out_purchase = last_buy.get(t["element_out"], out["now_cost"] - out.get("cost_change_start", 0))
            bank += sell_price(out_purchase, out["now_cost"]) - t["element_in_cost"]

    if ft_override is not None:
        ft, src = ft_override, "set manually"
    else:
        ft = derive_free_transfers(hist["current"], chips_by_gw, current_gw)
        if chips_by_gw.get(next_gw) not in ("wildcard", "freehit"):
            ft = max(ft - len(pending), 0)
        src = "derived from history (confirm in the app)"

    return SquadState(
        team_id=team_id,
        team_name=entry.get("name", ""),
        next_gw=next_gw,
        picks=rows,
        bank=bank,
        free_transfers=ft,
        ft_source=src,
        chips_left=chips_available(hist.get("chips", []), next_gw),
        chips_used=hist.get("chips", []),
        pending_transfers=pending,
        overall_rank=entry.get("summary_overall_rank"),
        total_points=entry.get("summary_overall_points"),
    )
