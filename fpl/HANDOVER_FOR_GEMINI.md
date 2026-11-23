# FPL handover: Definitely In It Now (2026/27)

*Written 23 Nov 2026 by Claude (Claude Code) for whoever takes over next, including Gemini. It covers everything from the original Claude Cowork task (31 Jul to 9 Oct 2026) and the Claude Code session that followed (10 Oct to 24 Oct 2026). The live numbers below were read from the official FPL API on 23 Nov 2026.*

---

## 1. Read this first

- **The manager:** a Chelsea supporter who watches every Chelsea game. FPL team **Definitely In It Now** (renamed from *In The Title Race*), **FPL entry ID 2347384**.
- **The goal:** maximum points, and **winning their mini-leagues**. They're chasing, not defending.
- **How they work:** they push back hard and expect evidence. They get frustrated when they have to ask for the same thing twice, when advice flip-flops, or when the bank and free transfers aren't tracked. Section 3 is the list of things they never want to have to ask for again.
- **Where everything lives:** GitHub repo `kamoshodi-ui/Maths`, branch **`claude/fpl-squad-research-ia4ki5`**, folder **`fpl/`**. The repo is the source of truth for the engine, the notes and the reports.

---

## 2. Current state (live from the FPL API, 23 Nov 2026)

**Gameweek:** GW11 in progress (deadline was Sat 21 Nov). **Next deadline: GW12, Fri 27 Nov 2026, 18:30 UTC.**

| Item | Value |
|---|---|
| Total points | 660 |
| Overall rank | ~1.73m |
| Bank | **£1.3m** |
| Squad value | £102.7m |
| Free transfers for GW12 | **1** (derived from the transfer history; confirm in the app) |
| Chips used | Wildcard 1 (GW6), Triple Captain (GW7) |
| Chips left in set 1 | **Bench Boost, Free Hit**. Both must be used by the **GW19 deadline (around 1 Jan 2027)** or they're lost. |
| Chips in set 2 | All four become available from GW20. |

**Squad for GW11**

| Pos | Player | Club | Price |
|---|---|---|---|
| GK | Tzolakis | Hull | £4.7m |
| GK | Dubravka (bench) | Spurs | £3.9m |
| DEF | Van Hecke | Spurs | £5.2m |
| DEF | Vušković | Brighton | £5.3m |
| DEF | De Cuyper | Brighton | £5.5m |
| DEF | Calafiori (bench) | Arsenal | £5.9m |
| DEF | Hall (bench, **75%, unspecified injury**) | Newcastle | £5.2m |
| MID | Groß | Brighton | £6.3m |
| MID | Rogers | Chelsea | £8.3m |
| MID | Palmer | Chelsea | £9.8m |
| MID | Tavernier | Bournemouth | £6.7m |
| MID | Belloumi (bench) | Hull | £5.2m |
| FWD | Haaland | Man City | £15.8m |
| FWD | N. Jackson (**captain in GW11**) | Aston Villa | £7.3m |
| FWD | Evanilson | Bournemouth | £6.6m |

**Club limits:** Brighton is at the 3-player limit (De Cuyper, Groß, Vušković). Chelsea, Hull, Spurs and Bournemouth have 2 each.

**Private mini-leagues (23 Nov)**

| League | Position |
|---|---|
| Barclays English Premier Yeet (id 186469) | 3rd of 23 |
| Mono FC Fantasy League (id 282497) | 7th of 22 |
| Footy Masters (id 1660985) | 10th of 41 |
| TalkingPoints League (id 1389988) | 29th of 102 |

They are also in Kavkas View (2,033rd of 9,352), which is too big to target.

---

## 3. The manager's rules and preferences

These come from the whole history of both chats. Follow them without being asked.

1. **Real life matters as much as FPL stats.** For every player, cover his role, whether he's the focal point, his club's form and whether it will last, his manager's style and sacking risk, European and cup rotation, and penalties and set pieces. Their words: *"the list you give me is one you'd be comfortable with me betting my house on."*
2. **Track the state yourself.** Bank, free transfers, chips, injuries and **players out on loan** (one was sitting on their bench unnoticed in September). Never ask them for what the API can tell you.
3. **An audit must include who to bring in**, not just a review of their own fifteen.
4. **Think season-long.** Bank transfers where possible, avoid hits, and avoid needing a Wildcard.
5. **Cross-check sources.** Use FPL/Opta and Understat. The manager introduced Understat and insists on it. Also check the world's top managers and **the leaders of their own mini-leagues**.
6. **Don't flip-flop.** If a recommendation changes, say exactly which piece of data changed. Don't quote only the half of a stat that supports you.
7. **Check that a duty has actually paid off.** "Penalty taker" means nothing if the team hasn't won a penalty.
8. **Club rules they stated:**
   - No second Everton player. They said: *"I'm not putting two Everton midfielders in my team."*
   - No players from likely relegation sides in the XI unless the player is a genuine talisman.
   - Wary of a third Arsenal player, especially when it means selling from a better attack.
9. **Their football views (respect them, argue only with evidence):**
   - João Pedro is the best Chelsea striker in a decade. They hated the suggestion of swapping him for an Everton player, though they did eventually sell him in GW9.
   - They don't rate Gibbs-White.
   - Caicedo is Chelsea's most important player.
   - Barco is underrated.
   - They thought the 2026/27 rule changes would curb set-piece-heavy teams like Arsenal.
10. **Delivery:** lead with a simple list of who's out and who's in, then the reasoning. Give captain, vice-captain and bench order every week.

---

## 4. Season log, GW1 to GW11 (from the FPL API)

| GW | Points | Overall rank | Transfers (hits) | Chip | Captain | Moves |
|---|---|---|---|---|---|---|
| 1 | 51 | 4.09m | — | — | Haaland | Opening squad (below) |
| 2 | 95 | 2.44m | 0 | — | | |
| 3 | 57 | 1.99m | 1 | — | | Aznou → Bobby Thomas (COV) |
| 4 | 76 | 2.01m | 0 | — | | |
| 5 | 43 | 2.50m | 2 | — | | Mbeumo → Rogers; Andrey Santos → Yalcouyé |
| 6 | 70 | 2.05m | WC | **Wildcard** | Haaland | Full rebuild (below) |
| 7 | 73 | 1.67m | 2 | **Triple Captain** (Haaland) | Haaland | Ødegaard → Saka; Isak → Barry |
| 8 | 36 | 2.47m | 2 (−4) | — | Haaland | Saka → Palmer; Janelt → Belloumi |
| 9 | 61 | 1.99m | 1 | — | Haaland | João Pedro → N. Jackson |
| 10 | 58 | 2.08m | 0 | — | Haaland | — |
| 11 | 48* | 1.73m | 3 (−4) | — | N. Jackson | Guéhi → Vušković; Gvardiol → Van Hecke; Barry → Evanilson |

*\* GW11 was still in progress on 23 Nov.*

**GW1 squad:** Kinsky; Davis, Aina, Mitchell; Mbeumo, Palmer, B. Fernandes, Szoboszlai; Calvert-Lewin, Haaland, João Pedro. Bench: Steele, Andrey Santos, van Ewijk, Aznou.

**GW6 Wildcard (21 Sep to 9 Oct):**
- **Out:** Steele, Kinsky, Thomas, van Ewijk, Mitchell, Davis, Aina, Palmer, Szoboszlai, B. Fernandes, Yalcouyé, Calvert-Lewin.
- **In:** Tzolakis, Dubravka, Calafiori, De Cuyper, Guéhi, Gvardiol, Hall, Rogers (already owned), Ødegaard, Groß, Tavernier, Janelt, Isak.
- Haaland and João Pedro were kept.
- There was churn inside the Wildcard: Trafford, Tarkowski, Schade and Bogle were bought and moved on again before the deadline.

**GW8 to GW11 decisions were made after the last Claude review.** Claude doesn't know the reasoning behind them. GW8's two moves cost a −4 because only 1 free transfer was available (see section 7, bug fixed).

---

## 5. History of the original Cowork task (31 Jul to 9 Oct 2026)

*Inherited from Claude Cowork. Outputs from that task: "fpl-2026-27-squad-and-reasoning.md", "fpl-2026-27-squad-v2-four-locks.md" and a crest SVG, "in-the-title-race-crest.svg". They were in a zip the manager uploaded; that copy is no longer in this workspace.*

**Pre-season (31 Jul)**
- Built a "perfect 15" from heavy research into the rule changes: two chip sets, a revised bonus-points formula, unchanged defensive-contribution points (2 points for 10+ CBIT for defenders, 12+ CBIRT for midfielders and forwards), and new save buckets for goalkeepers.
- Researched all the new managers: Maresca at City, Alonso at Chelsea, Iraola at Liverpool, Carrick permanent at Man Utd, Glasner at Forest, Sage at Palace, and others.
- Team name: *"In The Title Race"*, a play on Maresca's "Not In The Title Race" meme from his time at Chelsea. They also designed a badge and wrote image prompts for it.
- Version 2 squad, built around **four locks: Haaland, Bruno Fernandes, Palmer, João Pedro**. The manager rejected Gibbs-White, asked for better midfielders and used the spare £1.5m.

**Before GW1 (11 to 21 Aug)**
- They asked whether it was safe to own Man City players after the Community Shield.
- Mosquera came out (Calafiori in), and Bruno Guimarães was replaced.
- They rejected Le Fée (Sunderland, a relegation candidate), two Everton midfielders, and a defender from a historically poor side.
- They challenged why Declan Rice wasn't suggested.
- Claude pushed hard for Mbeumo; the manager was later sarcastic about it after early results. Calvert-Lewin was bought. They locked in on 21 Aug.

**GW1 to GW5 audits (Aug to Sep)**
- They considered selling Haaland, arguing Maresca's style would limit him.
- Chelsea's midfield: Enzo Fernández left, which they were glad about, wanting a proper defensive midfielder instead.
- Repeated complaints about Claude losing track of free transfers and the bank, and missing a bench player who was out on loan.
- GW5: Mbeumo → Rogers.

**GW6 Wildcard planning (18 Sep to 9 Oct)**
- They insisted on buying early to beat price changes.
- Real-life factors had to be covered, including Chelsea conceding a lot while scoring a lot.
- They checked the squads of the leaders in their own leagues.
- They introduced **Understat** and demanded cross-checks.
- They overruled the sale of João Pedro for Barry.
- They refused a third Arsenal player.
- Final Wildcard move on 9 Oct: Bogle → Hall.

---

## 6. The Claude Code session (10 to 24 Oct 2026)

**Built the FPL engine** in `fpl/`, described in section 7. The cloud container first blocked the FPL and Understat sites; the manager opened up network access on 10 Oct.

**GW7 review (14 to 15 Oct)**
- Nine researchers covered:
  - **FPL and stats sites:** FPL API, Understat (including player match logs), Opta/The Analyst, FotMob, FBref (blocked by Cloudflare)
  - **Team news:** RotoWire, Sports Mole, club sites, press conferences
  - **Tips sites:** BeatFPL, Fantasy Football Scout, FF Fix, FF Hub, OneFPL, premierleague.com
- Three skeptics then tried to break the plan from three angles: team news and minutes, data and arithmetic, mini-league strategy. All five decisions held.
- **Decisions, all followed:** sell Isak (thigh, 0%) for Barry; Ødegaard → Saka; keep the third free transfer; **Triple Captain Haaland v Ipswich**.
- **Result:** 73 points, overall rank 2.05m → 1.67m.
- **Engine fixes from the review:**
  - Read return and ban dates from FPL's news text.
  - Allow team adjustments to vary by gameweek.
  - Blend **bookmaker goal lines** into the next gameweek. Forest v Arsenal was badly wrong on season xG alone.
  - Replace the noisy re-solve confidence measure with **head-to-head checks**.
  - Compare against **the rivals ahead** in each mini-league, using the squad after transfers.
- **Rival chip check:** most mini-league rivals had already used their first-half Triple Captain in GW3–5. The Barclays leader, Jason Marais, still had his.

**Chelsea discussion (24 Oct, Chelsea v Spurs)**
- On Estêvão's lack of minutes: 29 Premier League minutes and no league starts by then.
  - Alonso, 9 Oct: *"He will have his moments in some games and more minutes."*
  - Neto, Palmer and Rogers were all ahead of him, and with no European football there are no rotation games.
- The reported XI against Spurs had **no João Pedro**. The manager assumed a knock.
- The XI, as the manager and Claude read it: Penders; Acheampong, Lacroix, Colwill; Quenda (RWB), Caicedo, Henderson, Hato (LWB); Neto, Palmer; Rogers (CF).
  - With João Pedro out, Alonso moved Neto forward and brought in a wing-back, not another attacker. That's why the opening never reached Estêvão.
- Claude made a pitch diagram showing the shape with and without the ball. It's a **private** Claude page and only the manager can open it: https://claude.ai/artifact/Re7eitqrdn6J6zWSCuohYz

**Handoff files:** `fpl/HANDOFF.md` (one page, 21 Oct), `fpl/CONTEXT.md` (full context) and this file.

---

## 7. The engine (`fpl/`)

**Run it.** You need Python 3.10+ and internet access to `fantasy.premierleague.com` and `understat.com`. From the repo root:

```bash
pip install -r fpl/requirements.txt      # requests, pulp<3, highspy
python -m fpl audit                       # writes fpl/reports/gwNN-audit.md
python -m unittest discover -s fpl/tests -t .
```

Useful flags:

| Flag | What it does |
|---|---|
| `--ft N` | Override the free-transfer count |
| `--bank X` | Override the bank |
| `--wildcard GW` | Plan with a Wildcard in that gameweek |
| `--lock Name …` | Never sell these players |
| `--ban Name …` | Never buy these players |
| `--avoid-teams COV …` | Never buy from these clubs |
| `--horizon 8` | Plan over more gameweeks |
| `--ft-value 2.5` | Make the planner keener to bank transfers |
| `--elite 100` | Compare against the top 100 instead of 50 |
| `--stability N` | Run N slow full re-solves for confidence |
| `--offline fpl/.cache/<date>` | Re-run on saved data |

**What each file does**

| File | Job |
|---|---|
| `api.py` | Cached client for the FPL API; responses are saved in `fpl/.cache/<date>/`, which git ignores |
| `state.py` | Bank, selling prices (you keep half of any rise, rounded down), free transfers, chips (two sets; set 1 expires at the GW19 deadline), and transfers already made for the next deadline |
| `understat.py` | Understat team xG/xGA and player data from `https://understat.com/getLeagueData/EPL/<season>` (needs the header `X-Requested-With: XMLHttpRequest`). Clubs and players are matched to FPL by name. |
| `history.py` | Each player's starts in the last three games (FPL `element-summary`, latest game weighted most), plus his last four games' xG+xA and last season's per-90s (Understat `getPlayerData/<id>`) |
| `model.py` | Expected points, fixture by fixture (see below) |
| `optimise.py` | Multi-week transfer planner: a mixed-integer programme solved with PuLP and HiGHS (falls back to CBC) |
| `robust.py` | Head-to-head checks under ±20% projection error: buy vs sale, buy vs the next-best options, captain vs the next-best player in the XI |
| `elite.py` | What the global top N and the rivals ahead of you in each private mini-league own and captain, and which chips they've used |
| `report.py`, `__main__.py` | Write the audit. It also checks Triple Captain timing against every week up to the chip deadline. |
| `notes.json` | Real-life adjustments, explained next |

**How projections work (`model.py`)**
- **Team strength:** each team's attack and defence come from Understat xG and xGA, shrunk towards FPL's strength ratings. This season FPL only publishes the coarse overall rating.
- **Fixtures:** expected goals = attack × opponent defence / league average × home advantage (1.10). For the next gameweek, bookmaker goal lines are blended in at 70%.
- **Players:** xG and xA per 90 come from FPL/Opta, shrunk towards a prior based on price and last season.
- **Minutes:** start chance × availability. Availability comes from FPL's flag and dated return or ban in the news text, or from a `notes.json` override.
- **Points:** full 2026/27 scoring, including clean sheets and goals conceded (Poisson), defensive contributions, saves, bonus and cards.

**`notes.json` (how real life gets into the model).** Every entry has a dated, sourced reason, and every adjustment is printed in the audit.
- **`players`:** keyed by FPL id (names repeat across clubs). Each can set `availability`, `start_prob` (a number, or `{"<gw>": value}` that holds until the next listed gameweek) and `xgi_mult`.
- **`teams`:** keyed by short name (`LIV`, `MUN`…). `attack_mult` scales goals scored; `defence_mult` scales goals **conceded**, so above 1 means a leakier defence.
- **`market`:** bookmaker goal lines for one gameweek, as `{"gw": 7, "fixtures": {"NFO-ARS": [0.93, 1.95], …}}` (home goals, then away goals).
- **`preferences`:** `max_per_club` (EVE: 1) and `avoid_teams`.
- **Keys starting with `_`** are ignored.
- **Warning:** everything in it is from the GW7 review (14–15 Oct) and **is now stale**. Clear or refresh it before the next audit.

**Bug fixed today (23 Nov).** The free-transfer rule for Wildcard and Free Hit weeks was wrong. The engine assumed a new free transfer was added during the chip week. In fact your saved transfers are kept but no new one is added. That's why GW7 had 2 free transfers, not the 3 the audit said, and why the two GW8 moves cost −4. It's now fixed, with a test checked against this team's real history.

**Known limitations and ideas not yet built**
- No home/away splits beyond what the bookmaker blend gives the next gameweek. Splits from three games each were too noisy.
- Bookmaker lines are entered by hand into `notes.json`; nothing fetches them automatically.
- No planner for Bench Boost or Free Hit yet. Both expire at the GW19 deadline and need planning soon.
- The Coventry rule ("no relegation sides") is a judgement call, not a hard ban.
- When only one rival is ahead of you, the mini-league section says "most leaders own him".
- FBref is blocked by Cloudflare. The Analyst (Opta) and FotMob stood in for it.

---

## 8. Sources that worked

| Kind | Sources |
|---|---|
| **Data** | FPL API: `bootstrap-static/`, `fixtures/`, `entry/{id}/`, `entry/{id}/history/`, `entry/{id}/transfers/`, `entry/{id}/event/{gw}/picks/`, `element-summary/{id}/`, `leagues-classic/{id}/standings/`. Understat JSON endpoints. The Analyst's Opta feeds and Power Rankings. FotMob. |
| **Team news** | Club press conferences (Thursday and Friday), RotoWire predicted line-ups, Sports Mole, Fantasy Football Scout team news, liverpoolfc.com and other club sites |
| **Expert consensus** | BeatFPL (projected points and captain picks), Fantasy Football Scout (buy/keep/sell, Scout Picks, "Great and the Good"), FF Hub (Spreadex goal lines), FF Fix, OneFPL, premierleague.com (The Scout) |

---

## 9. Next steps

1. **GW12 review, before Fri 27 Nov 18:30 UTC:**
   - **Free transfers:** 1, bank £1.3m.
   - **Hall:** 75%, unspecified injury.
   - **Club limits:** Brighton is at the limit of 3.
   - **Stale notes:** refresh `notes.json`.
2. **Plan Bench Boost and Free Hit** before the GW19 deadline. Check whether any blank or double gameweeks have appeared since October; none were scheduled through GW19 then.
3. **Check the mini-leagues.** The goal is still to catch the leaders, so check rival ownership and chip use each week.
4. **Keep the handoff files current** (`CONTEXT.md` and this file) after each review.

---

## 10. Other things in the repo (not FPL)

The repo `kamoshodi-ui/Maths` also holds maths tutoring materials, unrelated to FPL: **"BM102 Catch-up session"**. It contains slides (`.pptx`/`.pdf`), student notes and tutor notes, in the folder `Catch-up session/` and as `BM102 Catch-up session.zip`.
