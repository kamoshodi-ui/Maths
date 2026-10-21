# Context for whoever runs the next audit (human or Claude)

This carries over from the Cowork task "FPL squad research", which ran from 31 Jul to 9 Oct 2026.
Read it before giving advice.

## The manager

- Team **Definitely In It Now** (was In The Title Race), FPL ID **2347384**. A Chelsea supporter who watches every Chelsea game.
- Goal: **maximum points, and winning the mini-leagues**. They are chasing first place.
- Thinks season-long, not one gameweek at a time. Wants to bank transfers and avoid needing a Wildcard.

## What they asked for again and again, and must not have to ask for again

1. **Real life matters as much as FPL stats.** For every player, cover: his club's form and
   trajectory, his manager's style, his role and whether he's the focal point, the risk of a
   manager change, and whether a hot or cold start will last.
2. **Keep track of the squad state**: bank, free transfers, chips, players out on loan or
   flagged. The engine now reads all of this from the API, so state it, don't guess it.
3. **An audit includes who to bring in**, not just a review of the current fifteen.
4. **Cross-check sources**: FPL/Opta, Understat, the top managers in the world, and the leaders
   of their own mini-leagues.
5. **Don't flip-flop.** If a recommendation reverses within the same audit, explain exactly
   which piece of data changed. Don't quote only the half of a stat that supports the argument.
   In Cowork, Rogers was called "owed" on his assists while his goals were running hot.
6. **Check that a duty has actually paid.** "Everton's penalty taker" meant nothing when Everton
   had won zero penalties.

## Their stated views. Respect them, and argue only with evidence.

- Won't start players from likely relegation sides unless they're a genuine talisman with big points.
- Doesn't rate Gibbs-White. Doesn't want two players from a mid-table side like Everton.
- Rates João Pedro highly; 20 of the world's top 30 managers agreed on 9 Oct. Wanted to give Palmer a run.
- Wary of a third Arsenal player, especially when it means selling from a better attack.
- Believes the 2026/27 rule changes curb set-piece-heavy teams, Arsenal in particular.
- Rates Caicedo as Chelsea's key player and Barco as underrated.

## Last known state (from Cowork, 9 Oct 2026, before the GW6 deadline)

- **Wildcard 1 played in GW6** (active from 21 Sep to the 10 Oct deadline). Two free transfers were
  saved through it, so expect **3 FTs for GW7**. Confirm in the app and use `--ft` if the
  derived number differs.
- Final GW6 move agreed: **Bogle out, Hall (NEW) in**, leaving the bank at **£0.0m**.
- Squad after that move:

  | Position | Players |
  |---|---|
  | GK | Tzolakis (HUL), Dubravka (TOT) |
  | DEF | Calafiori (ARS), Guéhi (MCI), De Cuyper (BHA), Gvardiol (MCI), Hall (NEW) |
  | MID | Rogers (CHE), Tavernier (BOU), Groß (BHA), Ødegaard (ARS), Janelt (BRE) |
  | FWD | Haaland (MCI), Isak (LIV), João Pedro (CHE) |

- **Chips:** set 1 expires at the GW19 deadline (2 Jan 2027). Wildcard 1 is used. Bench Boost,
  Triple Captain and Free Hit are not recorded as used; check this in the audit's "Where you stand" table.

## News as of 9 Oct 2026. Check it's still current before using it.

- Man City were found guilty on 114 of 115 charges. Sanctions are undecided and City are appealing. You own
  three City players (Haaland, Guéhi, Gvardiol). A points deduction doesn't change FPL scoring.
- João Pedro had a knee problem (75%) and saw a specialist over the break. Isak had a thigh/quad problem (75%).
- Liverpool: Gakpo ankle, possibly weeks. Arsenal: Havertz and Tzolis hamstrings, out for weeks.
  Bournemouth: Alex Scott tendon, out 6–8 weeks.
- Understat npxG after GW5: Brighton 12.13, Man City 11.04, Man Utd 9.82, Brentford 9.75,
  Chelsea 8.94, Arsenal 8.65, Liverpool 7.48 (13th).

## GW7 review (14–15 Oct 2026) — what was established

- State from the API: bank £0.0m, **3 FTs** (2 kept through Wildcard 1 in GW6, +1), chips left in set 1: TC, BB, FH. GW6 score 70; overall ~2.05m.
- Research covered FPL API, Understat (player match logs), Opta/The Analyst, FotMob, RotoWire, BeatFPL, FFS, FF Fix, FF Hub, OneFPL, premierleague.com, club sites. FBref blocks automated access (Cloudflare).
- Consensus: sell Isak (0%, not training as of 13 Oct); Barry is the data and expert pick to replace him (most xG after Haaland, only senior CF at Everton); Saka is the only clear upgrade on Ødegaard; Haaland v IPS is the first-half Triple Captain window; Gvardiol is rotating with O'Reilly.
- Model fixes made because of this review: return dates parsed from FPL news, per-gameweek team adjustments, bookmaker goal lines blended for the next GW (Forest v Arsenal was badly off on season xG alone), head-to-head robustness checks instead of noisy re-solves.

## GW7 result (checked 21 Oct 2026)

- Made: Isak → Barry, Ødegaard → Saka (2 FTs, no hit); Triple Captain on Haaland. Scored **73**; total 465; overall rank ~1.67m (up from ~2.05m).
- Now: bank £0.5m, **2 FTs for GW8**, chips left in set 1: **Bench Boost, Free Hit** (expire at the GW19 deadline). Wildcard 1 (GW6) and TC (GW7) used.
- GW8 deadline: Fri 23 Oct 17:30 UTC. Engine's provisional GW8 idea was Gvardiol → Thomas (COV) and Tavernier → Mbeumo — check Coventry against the manager's "no relegation sides" rule before suggesting it.
