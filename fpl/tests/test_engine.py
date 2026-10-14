"""Engine tests against a small synthetic league (no network needed).

Run from the repository root:  python -m unittest discover -s fpl/tests -t .
"""
import random
import unittest
from datetime import date, timedelta

from fpl.model import _availability, by_gw, project, return_gw
from fpl.optimise import SQUAD_SHAPE, PlanSettings, plan
from fpl.state import build_state, chips_available, derive_free_transfers, sell_price


def make_world(seed=1, played_gws=5, next_gw=6):
    rng = random.Random(seed)
    teams = []
    for t in range(1, 21):
        teams.append({
            "id": t, "name": f"Team{t}", "short_name": f"T{t:02d}",
            "strength_attack_home": 1000 + 20 * t, "strength_attack_away": 1000 + 20 * t,
            "strength_defence_home": 1000 + 20 * t, "strength_defence_away": 1000 + 20 * t,
        })
    elements, pid = [], 1
    for t in range(1, 21):
        for pos, n in ((1, 2), (2, 6), (3, 6), (4, 3)):
            for k in range(n):
                starter = k < {1: 1, 2: 4, 3: 4, 4: 2}[pos]
                mins = rng.randint(380, 450) if starter else rng.randint(0, 120)
                base = {1: 0.0, 2: 0.05, 3: 0.2, 4: 0.4}[pos] * (1 + t / 20)
                price = {1: 45, 2: 45, 3: 55, 4: 60}[pos] + rng.randint(0, 40) + (t // 4) * 5
                elements.append({
                    "id": pid, "web_name": f"P{pid}", "first_name": "F", "second_name": f"P{pid}",
                    "team": t, "element_type": pos, "now_cost": price, "cost_change_start": rng.choice([-2, 0, 0, 1, 3]),
                    "minutes": mins, "starts": round(mins / 88), "expected_goals": f"{base * mins / 90:.2f}",
                    "expected_assists": f"{base * 0.6 * mins / 90:.2f}", "expected_goals_conceded": f"{1.3 * mins / 90:.2f}",
                    "defensive_contribution": int(rng.uniform(3, 12) * mins / 90) if pos > 1 else 0,
                    "bonus": rng.randint(0, 6), "saves": int(3 * mins / 90) if pos == 1 else 0,
                    "yellow_cards": rng.randint(0, 2), "status": "a", "chance_of_playing_next_round": None,
                    "news": "", "selected_by_percent": f"{rng.uniform(0, 40):.1f}", "total_points": rng.randint(0, 50),
                    "form": "3.0", "goals_scored": rng.randint(0, 4), "assists": rng.randint(0, 3),
                    "penalties_order": None,
                })
                pid += 1
    fixtures, fid = [], 1
    for gw in range(1, 12):
        order = list(range(1, 21))
        rng.shuffle(order)
        for h, a in zip(order[::2], order[1::2]):
            fixtures.append({"id": fid, "event": gw, "team_h": h, "team_a": a, "finished": gw <= played_gws})
            fid += 1
    start = date(2026, 8, 21)
    events = [{"id": g, "is_next": g == next_gw, "is_current": g == next_gw - 1,
               "deadline_time": f"{start + timedelta(weeks=g - 1)}T10:00:00Z"} for g in range(1, 39)]
    return {"teams": teams, "elements": elements, "events": events}, fixtures


class FakeClient:
    def __init__(self, boot, fixtures, picks, transfers, history, chips):
        self._b, self._f, self._p, self._t = boot, fixtures, picks, transfers
        self._h = {"current": history, "chips": chips}

    def bootstrap(self): return self._b
    def fixtures(self): return self._f
    def entry(self, team_id): return {"name": "Test XI", "summary_overall_rank": 1000, "summary_overall_points": 300}
    def history(self, team_id): return self._h
    def transfers(self, team_id): return self._t
    def picks(self, team_id, gw):
        return {"picks": [{"element": e, "is_captain": False} for e in self._p], "entry_history": {"bank": 7}}


def legal_squad(boot):
    """Cheapest legal 15: the cheapest players per position, max 3 per club."""
    chosen, per_club = [], {}
    for pos, n in SQUAD_SHAPE.items():
        pool = sorted((e for e in boot["elements"] if e["element_type"] == pos), key=lambda e: e["now_cost"])
        for e in pool:
            if sum(1 for c in chosen if boot_pos(boot, c) == pos) == n:
                break
            if per_club.get(e["team"], 0) < 3:
                chosen.append(e["id"])
                per_club[e["team"]] = per_club.get(e["team"], 0) + 1
    return chosen


def boot_pos(boot, pid):
    return next(e["element_type"] for e in boot["elements"] if e["id"] == pid)


class RulesTest(unittest.TestCase):
    def test_sell_price(self):
        self.assertEqual(sell_price(50, 50), 50)
        self.assertEqual(sell_price(50, 51), 50)  # +0.1 rise: keep nothing
        self.assertEqual(sell_price(50, 52), 51)
        self.assertEqual(sell_price(50, 53), 51)  # rounds down
        self.assertEqual(sell_price(50, 47), 47)  # falls are taken in full

    def test_free_transfers(self):
        hist = [{"event": g, "event_transfers": 0} for g in range(1, 8)]
        self.assertEqual(derive_free_transfers(hist, {}, 1), 1)
        self.assertEqual(derive_free_transfers(hist, {}, 3), 3)
        self.assertEqual(derive_free_transfers(hist, {}, 7), 5)  # capped at 5
        hist[2]["event_transfers"] = 2  # GW3: 2 transfers with 2 FTs
        self.assertEqual(derive_free_transfers(hist, {}, 3), 1)
        hist[2]["event_transfers"] = 3  # a hit doesn't take FTs below zero
        self.assertEqual(derive_free_transfers(hist, {}, 3), 1)
        hist[2]["event_transfers"] = 9  # wildcard week: transfers don't consume FTs
        self.assertEqual(derive_free_transfers(hist, {3: "wildcard"}, 3), 3)

    def test_return_dates_from_news(self):
        starts = {g: date(2026, 8, 21) + timedelta(weeks=g - 1) for g in range(1, 39)}  # GW11 starts 30 Oct
        self.assertEqual(return_gw("Hamstring injury - Expected back 1 Nov", starts), 12)
        self.assertEqual(return_gw("Suspended until 30 Oct", starts), 11)
        self.assertEqual(return_gw("Expected back 5 Jan", starts), 21)  # rolls into next year
        self.assertIsNone(return_gw("Thigh injury - Unknown return date", starts))
        banned = {"status": "s", "chance_of_playing_next_round": 0, "news": "Suspended until 30 Oct"}
        self.assertEqual([_availability(banned, g - 8, g, None, starts) for g in (8, 10, 11)], [0.0, 0.0, 1.0])
        long_term = {"status": "i", "chance_of_playing_next_round": 0, "news": "Achilles - Unknown return date"}
        self.assertLess(_availability(long_term, 2, 10, None, starts), 0.5)  # no quick ramp without a date

    def test_by_gw(self):
        self.assertEqual(by_gw(None, 7), 1.0)
        self.assertEqual(by_gw(0.9, 7), 0.9)
        self.assertEqual([by_gw({"7": 0.8, "9": 1.0}, g) for g in (6, 7, 8, 9, 12)], [0.8, 0.8, 0.8, 1.0, 1.0])

    def test_chips_two_sets(self):
        used = [{"name": "wildcard", "event": 6}]
        self.assertNotIn("wildcard", chips_available(used, 7))
        self.assertIn("wildcard", chips_available(used, 20))  # second set


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot, cls.fixtures = make_world()
        owned = legal_squad(cls.boot)
        hist = [{"event": g, "event_transfers": 0} for g in range(1, 6)]
        cls.client = FakeClient(cls.boot, cls.fixtures, owned, [], hist, [])
        cls.state = build_state(cls.client, 1)
        cls.players, cls.rates, _ = project(cls.boot, cls.fixtures, 6, 4)
        cls.gws = [6, 7, 8, 9]

    def test_state(self):
        self.assertEqual(self.state.next_gw, 6)
        self.assertEqual(len(self.state.picks), 15)
        self.assertEqual(self.state.free_transfers, 5)
        self.assertEqual(self.state.bank, 7)

    def test_projections_sane(self):
        for p in self.players:
            for v in p["proj"].values():
                self.assertGreater(v, -2)
                self.assertLess(v, 15)
        # stronger attacks should project more for forwards on average
        fw = [p for p in self.players if p["pos"] == 4 and p["start_rate"] > 0.5]
        weak = [p["total"] for p in fw if p["team_id"] <= 5]
        strong = [p["total"] for p in fw if p["team_id"] >= 16]
        self.assertGreater(sum(strong) / len(strong), sum(weak) / len(weak))

    def check_plan(self, res):
        P = {p["id"]: p for p in self.players}
        for g in res["gws"]:
            self.assertEqual(len(g["squad"]), 15)
            for pos, n in SQUAD_SHAPE.items():
                self.assertEqual(sum(1 for i in g["squad"] if P[i]["pos"] == pos), n)
            clubs = {}
            for i in g["squad"]:
                clubs[P[i]["team_id"]] = clubs.get(P[i]["team_id"], 0) + 1
            self.assertLessEqual(max(clubs.values()), 3)
            self.assertEqual(len(g["xi"]), 11)
            self.assertIn(g["captain"], g["xi"])
            self.assertGreaterEqual(g["bank"], 0)
            self.assertEqual(len(g["bench"]), 4)
            self.assertEqual(P[g["bench"][-1]]["pos"], 1)  # backup keeper last

    def test_plan_legal_and_beats_roll(self):
        from dataclasses import replace
        s = PlanSettings()
        best = plan(self.players, self.state, self.gws, s)
        hold = plan(self.players, self.state, self.gws, replace(s, freeze_first=True))
        self.check_plan(best)
        self.check_plan(hold)
        self.assertEqual(hold["gws"][0]["in"], [])
        self.assertGreaterEqual(best["objective"], hold["objective"] - 1e-6)

    def test_budget_respected(self):
        res = plan(self.players, self.state, self.gws, PlanSettings())
        g0 = res["gws"][0]
        owned = {p["id"]: p for p in self.state.picks}
        P = {p["id"]: p for p in self.players}
        spent = sum(P[i]["price"] for i in g0["in"]) - sum(owned[o]["sell"] for o in g0["out"])
        self.assertEqual(self.state.bank - spent, g0["bank"])

    def test_hits_only_when_out_of_free_transfers(self):
        from dataclasses import replace
        st = replace(self.state, free_transfers=1)
        res = plan(self.players, st, self.gws, PlanSettings())
        for g in res["gws"]:
            self.assertGreaterEqual(g["hits"], max(0, len(g["in"]) - g["ft"]))

    def test_locks_and_bans(self):
        owned = self.state.ids
        some_star = max((p for p in self.players if p["id"] not in owned), key=lambda p: p["total"])
        s = PlanSettings(locked=(owned[0],), banned=(some_star["id"],))
        res = plan(self.players, self.state, self.gws, s)
        for g in res["gws"]:
            self.assertIn(owned[0], g["squad"])
            self.assertNotIn(some_star["id"], g["squad"])

    def test_notes_override(self):
        target = self.players[0]
        notes = {"players": {target["name"]: {"availability": {"6": 0.0, "8": 1.0}, "reason": "test"}}}
        players, _, log = project(self.boot, self.fixtures, 6, 4, notes=notes)
        p = next(x for x in players if x["id"] == target["id"])
        self.assertEqual(p["proj"][6], 0.0)
        self.assertEqual(p["proj"][7], 0.0)
        self.assertTrue(any("test" in line for line in log))


if __name__ == "__main__":
    unittest.main()
