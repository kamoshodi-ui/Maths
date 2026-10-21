# Handoff summary: FPL season engine and weekly reviews

*Last updated 21 Oct 2026 by Claude Code. Fuller history and preferences are in `CONTEXT.md` in this folder.*

## What it is
A Python tool that runs a data-driven weekly Fantasy Premier League review for my team, **Definitely In It Now** (FPL ID 2347384, formerly In The Title Race). It replaces the Cowork task "FPL squad research", which ran from 31 Jul to 9 Oct 2026.

## Where it lives
- Repo: GitHub `kamoshodi-ui/Maths`, branch `claude/fpl-squad-research-ia4ki5`, folder `fpl/`
- `fpl/README.md`: how to run it
- `fpl/CONTEXT.md`: full handoff (my preferences, history, current state)
- `fpl/notes.json`: real-life adjustments (injuries, rotation, manager news, bookmaker goal lines, my club rules), each with a dated source
- `fpl/reports/`: weekly audits
- Run it with `pip install -r fpl/requirements.txt`, then `python -m fpl audit`

## What the engine does
- Reads my bank, selling prices, free transfers and chips straight from the FPL API, so nobody has to remember them.
- Projects every player over six gameweeks from FPL/Opta and Understat xG, starts in the last three games, last season's data and bookmaker goal lines.
- Plans transfers across the whole six weeks and only recommends a move if it beats saving the transfer.
- Checks each move head-to-head against the alternatives, and checks Triple Captain timing.
- Compares my squad with the top 50 managers and with the rivals ahead of me in each mini-league.

## Done
- Built the engine.
- Ran the full GW7 review: nine researchers covering Understat, Opta/The Analyst, FotMob, RotoWire, BeatFPL, Fantasy Football Scout, FF Fix, FF Hub, OneFPL, premierleague.com and club sites, then three skeptics who tried to break the plan. All five decisions held.
- GW7 result: transferred Isak → Barry and Ødegaard → Saka, Triple Captain on Haaland. Scored **73**, overall rank up from about 2.05m to **1.67m** (465 points).

## Current state
- Bank £0.5m, **2 free transfers for GW8**.
- Chips left before the GW19 deadline: **Bench Boost, Free Hit**. Wildcard used in GW6, Triple Captain in GW7.

## Next
The GW8 review. The deadline is **Friday 23 Oct, 17:30 UTC**. The engine's draft is Gvardiol → Bobby Thomas (Coventry) and Tavernier → Mbeumo. Coventry needs checking against my no-relegation-sides rule.

## My rules and preferences
- Maximise points and win my mini-leagues (I'm chasing; 2nd in Barclays English Premier Yeet, 39 points behind).
- Real life matters as much as stats: role, manager, team form and trajectory, sacking risk, European rotation.
- Think season-long, bank transfers, and avoid hits and wildcards.
- Always track my bank, free transfers and chips. Always include players to bring in, not just my own squad.
- Cross-check sources, including the top managers and my mini-league leaders.
- Don't flip-flop, and don't quote half a stat.
- No second Everton player, and no likely-relegation sides unless the player is a genuine talisman.
- Max 3 Arsenal.
- I'm a Chelsea fan and rate João Pedro.
