# FPL engine

A weekly audit for **In The Title Race** (FPL team 2347384). Each run rebuilds the
team's state from the live FPL API, so it doesn't rely on anyone remembering
the bank or free transfers. It then projects every player over the next six
gameweeks, plans transfers across that whole stretch, and checks the result
against the world's best managers and your mini-league rivals.

## Run it

You need Python 3.10+. From the repository root:

```bash
pip install -r fpl/requirements.txt
python -m fpl audit                 # writes fpl/reports/gwNN-audit.md
```

Useful options:

| Option | What it does |
|---|---|
| `--ft 3` | Override free transfers if the derived number is wrong (the app is the truth) |
| `--wildcard 12` | Plan with a Wildcard played in GW12 |
| `--lock Palmer "João Pedro"` | Never sell these |
| `--ban Calvert-Lewin` | Never buy these |
| `--horizon 8` | Plan over more gameweeks |
| `--ft-value 2.5` | Make the planner keener to bank transfers |
| `--elite 100` | Compare against the top 100 overall instead of 50 |
| `--stability 0` | Skip the confidence re-runs (faster) |
| `--offline fpl/.cache/2026-10-10` | Re-run on a saved day's data |

## What's in the audit

1. **Where you stand**: bank, free transfers, selling value and chips left, read from the API.
2. **The verdict**: either the transfers to make or "roll". Each move shows its projected gain over the
   horizon, net of hits and of the value of a banked transfer. It also shows how often the same move
   survives 12 re-runs with every projection randomly shaken by ±25%. A move that only survives half
   the time is a coin flip, and the report says so.
3. **XI, bench order, captain and vice**, plus the provisional plan for the following weeks.
4. **Your fifteen**: price and sell price, flags, start rate, xG/xA/DefCon per 90, over- or
   under-performance against xG, and fixture-by-fixture projections.
5. **Best buys by position** within what you can actually afford.
6. **What the top 50 managers own and captain**, and where the model disagrees with them.
7. **Each mini-league**: your gap to first, what the leaders own that you don't, and your real differentials.
8. **Team strength and fixture ticker**, in expected goals rather than FDR colours.
9. **Every real-life adjustment applied**, each with its reason.

## Real life → `fpl/notes.json`

The numbers can't see a new manager, a role change in training or a return date
from a press conference. Put those in `notes.json`, always with a reason:

```json
{
  "players": {
    "Palmer": {"availability": {"7": 0.6, "8": 1.0}, "reason": "Alonso presser: 'touch and go' for the weekend"},
    "Rogers": {"xgi_mult": 1.1, "reason": "Moved into the central 10 role with Palmer out"}
  },
  "teams": {
    "LIV": {"attack_mult": 0.92, "reason": "Isak and Gakpo both out; 13th for npxG"}
  }
}
```

- `availability` is the chance he's available, by gameweek. Each value holds until the next listed gameweek.
- `start_prob` is the chance he starts when available.
- `xgi_mult` scales his xG and xA.
- `attack_mult` and `defence_mult` scale a team's goals scored and goals conceded.

## How projections work

See the docstring at the top of `model.py`. In short:

- **Team strength:** each team's xG and xGA per game (Understat, falling back to FPL/Opta), shrunk
  towards FPL's own team strength ratings. Five games of data can't overrule a whole season's reputation.
- **Clean sheets and goals conceded:** Poisson odds from each fixture's expected goals.
- **Attacking returns:** each player's xG and xA per 90, shrunk towards what his price implies, then scaled by fixture.
- **Minutes:** start rate × injury flag.
- **Defensive contributions and saves:** modelled from each player's per-90 rate.

The planner (`optimise.py`) is a mixed-integer programme. It enforces the
budget using real selling prices, the 3-per-club limit, formation rules,
rolling free transfers (capped at 5) and −4 hits. It also charges a small
cost per transfer, so it won't churn the squad for nothing.

## Tests

```bash
python -m unittest discover -s fpl/tests -t .
```

The tests run on a synthetic league, with no network needed. They check the
selling-price rule, free-transfer rollover, the two chip sets, squad legality,
the budget, hits, locks and bans, and notes overrides.
