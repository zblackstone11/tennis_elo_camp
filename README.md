# Tennis Elo Camp Tracker

A command-line tool to track player ratings for a tennis camp using a games-weighted Elo system. Supports singles and doubles matches, explicit tiebreaks, multi-set matches, match history logging, and player management.

## Project Structure

```
tennis_elo_camp/
├── elo_camp.py        # Main CLI script
├── players.json       # Stores player ratings and metadata
├── matches.json       # Stores match history
├── venv/              # Virtual environment (optional)
└── README.md          # This file
```

## Setup

1. **Clone or copy** the project folder to your local machine.  
2. **Create a virtual environment** (recommended):
   ```bash
   cd tennis_elo_camp
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   # .\venv\Scripts\activate     # Windows PowerShell
   ```
3. **Install any dependencies** (none beyond the Python standard library).  
4. **Initialize data files** (if not already present):
   ```bash
   echo "{}" > players.json
   echo "[]" > matches.json
   ```

## Usage

Run commands with the `python elo_camp.py` prefix:

### Record a Singles Match with Multiple Sets
```
python elo_camp.py record_series_singles <player_a> <player_b> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
- Each set is recorded as `<games_a>-<games_b>[kind]`, where `[kind]` is optional.
- If the kind is omitted, the system treats the score as a normal set.
- Use `[tiebreak]` explicitly only when indicating a tiebreak set.
- The match can include multiple sets.
- The winner is determined by the number of sets won, not total games.
- Example:
  ```bash
  python elo_camp.py record_series_singles Alice Bob 6-4 "7-6[tiebreak]" 5-7
  ```

### Record a Doubles Match with Multiple Sets
```
python elo_camp.py record_series_doubles <team_a1> <team_a2> <team_b1> <team_b2> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
- Similar to singles, each set is `<games_a>-<games_b>[kind]` with optional kind.
- If the kind is omitted, the system treats the score as a normal set.
- Use `[tiebreak]` explicitly only when indicating a tiebreak set.
- Example:
  ```bash
  python elo_camp.py record_series_doubles Alice Bob Charlie Dana 6-3 4-6 "7-6[tiebreak]"
  ```

### Add a Player with a Set Rating
```
python elo_camp.py add_player <name> [--singles_elo <rating>] [--doubles_elo <rating>]
```
- Adds a new player with the specified singles and/or doubles Elo rating (default 1000 for each).
- Example:
  ```bash
  python elo_camp.py add_player Eve --singles_elo 1200 --doubles_elo 1100
  ```

### View Leaderboard
```
python elo_camp.py leaderboard --mode singles|doubles --top <N>
```
- Show top N players in singles or doubles.
- Example:
  ```bash
  python elo_camp.py leaderboard --mode singles --top 5
  ```

### Rename a Player
```
python elo_camp.py rename_player <old_name> <new_name>
```
- Correct typos or update names without losing history.

### Delete a Player
```
python elo_camp.py delete_player <player_name>
```
- Remove a player and their rating data.

### Show Player Details
```
python elo_camp.py show_player <name>
```
- Displays current and peak singles and doubles ratings along with the dates those peaks were achieved.

## Elo System Details

- **Initial rating**: All players start at **1000**.  
- **Expected score**:
  ```
  E_A = 1 / (1 + 10^((R_B - R_A) / 400))
  ```
- **Actual score S**:
  ```
  games_won / (games_won + games_lost)
  ```
- **Rating update**:
  Rating changes are calculated **per set or tiebreak** using the expected and actual scores, with tiebreak sets automatically scaled within these calculations. After summing the rating changes from all sets and tiebreaks, a match-win bonus is applied to the total rating adjustment. Note that the `tiebreak_scaling` is not an additional additive term but is incorporated as part of the per-set calculation of the actual score `S`.

  The rating update formula per set is:

  ```
  R_new = R_old + K * (S - E) + match_win_bonus
  ```

  where:
  - `R_old` is the player's rating before the set,
  - `K` is the base K-factor adjusted per set,
  - `S` is the actual score for the set (with tiebreak scaling applied),
  - `E` is the expected score,
  - `match_win_bonus` is added once after summing all per-set rating changes.

  The per-set rating changes `(K * (S - E))` are summed over all sets and tiebreaks, and then the `match_win_bonus` is added once to the total rating adjustment.

- Matches consist of multiple sets, each scored individually.
- Tiebreaks are explicitly indicated by the `tiebreak` keyword; they are not inferred from scores.
- Match winner is determined by the number of sets won, not total games.

### Margin-of-Victory Scaling

An additional constant, **Margin-of-Victory Scaling** (`ALPHA_MOV`), is applied to adjust the rating change magnitude based on how decisive a set win was. This scaling rewards more dominant set victories and slightly dampens the impact of very close sets, improving predictive accuracy without overly punishing narrow losses.

The margin-of-victory multiplier per set is calculated as:

```
Multiplier = 1 + ALPHA_MOV * |2S - 1|
```

where:
- `S` is the actual score for the set (games won divided by total games),
- `ALPHA_MOV` is the margin-of-victory scaling constant (e.g., 0.20).

This multiplier is applied to the per-set rating update, effectively increasing the K-factor for more decisive set wins. For example:
- A 6–0 set (S = 1) results in approximately a +20% rating change,
- A close 7–6 set (S ≈ 0.54) results in about a +2% increase.

This approach helps to reward more decisive set wins and slightly dampens close-set impacts, improving predictive accuracy while maintaining fairness.

### Tiebreak Weighting (Proportional)

Tiebreak tokens (entered as "10-8[tiebreak]", etc.) are intentionally worth **less than a full set**. We scale the effective K for tiebreaks by their length (in equivalent games) relative to a typical set, then clamp it so very short TBs don’t swing too much and very long TBs don’t count as more than a set.

Per tiebreak token:

```
TB fraction = clamp( (eq_total / AVG_GAMES_PER_SET), TB_MIN_FRACTION, TB_MAX_FRACTION )
K_eff = K_BASE × mov_multiplier(S) × TB fraction
```

- `eq_total` is the total **equivalent games** in the tiebreak using your points→games rule (points/4).
- `AVG_GAMES_PER_SET` defaults to **10.0**.
- Clamp defaults: `TB_MIN_FRACTION = 0.30`, `TB_MAX_FRACTION = 0.70`.

**Intuition:** a typical super tiebreak like "10-8[tiebreak]" counts for about **45%** of a normal set; a very short TB is clamped to **30%**; a marathon TB is capped at **70%**. This keeps TBs meaningful but clearly less impactful than full sets.

| AVG_GAMES_PER_SET       | 10.0     | Typical number of games in a set (for TB scaling) |
| TB_MIN_FRACTION         | 0.30     | Minimum fraction of a set that a TB can count for |
| TB_MAX_FRACTION         | 0.70     | Maximum fraction of a set that a TB can count for |

### Constants


| Constant                 | Value    | Purpose                                           |
|--------------------------|----------|---------------------------------------------------|
| Starting Elo             | 1000     | Baseline rating for all new players               |
| Scale factor             | 400      | Δ of 400 ⇒ ~10:1 odds in win probability          |
| Base K-factor            | 80       | Sensitivity of rating changes per match           |
| Match-win bonus          | Variable | Additional rating bonus for winning the match     |
| Tiebreak scaling         | Variable | Adjusts rating impact for tiebreak sets            |
| Margin-of-Victory Scaling (ALPHA_MOV) | 0.20     | Adjusts rating changes based on decisiveness of set wins |

### Choosing K and Match Bonus


Recommended ranges for K-factor and match-win bonus, depending on your season/event length:

- **Short events (few matches):**
  - K ≈ 80–100
  - Match bonus ≈ 10–15% of K
- **Season-long (dozens of matches):**
  - K ≈ 40–60
  - Match bonus ≈ 8–12% of K
- **Multi-year or ongoing ladders:**
  - K ≈ 20–30
  - Match bonus ≈ 5–8% of K

**High K:** Adapts quickly to new skill levels, but ratings are more volatile (large swings from upsets or streaks).  
**Low K:** Ratings are more stable and resistant to random swings, but slow to reflect true changes in skill.

**Match bonus** is applied **once per match** (to the total rating change), in addition to the per-set rating adjustments. This helps reward overall match wins beyond set-by-set performance.

When using margin-of-victory scaling, the effective K-factor per set can vary slightly based on the scoreline, reflecting the decisiveness of each set. When tiebreak weighting is enabled, a tiebreak’s effective K is further reduced by its fraction, typically ~30–70% of a full set.

**Why these ranges?**  
These K-factor and match bonus recommendations are based on real-world applications of Elo across sports and games. Shorter events need higher K to adjust quickly to new information, while longer seasons or ongoing ladders benefit from lower K to reduce volatility. The match bonus helps reward closing out matches in multi-set formats like tennis, as supported by empirical studies, improving predictive accuracy compared to set-only adjustments.

### Rating Difference Examples

| ΔR = R_A − R_B | Win Probability (E_A) | Odds (wins : losses) | Win Probability (E_B) | Odds (wins : losses) for B |
|----------------|-----------------------|----------------------|-----------------------|----------------------------|
| 0              | 50.0%                 | 1.00 : 1             | 50.0%                 | 1.00 : 1                   |
| 50             | 57.1%                 | 1.33 : 1             | 42.9%                 | 0.75 : 1                   |
| 100            | 64.0%                 | 1.78 : 1             | 36.0%                 | 0.56 : 1                   |
| 150            | 70.3%                 | 2.37 : 1             | 29.7%                 | 0.42 : 1                   |
| 200            | 76.0%                 | 3.16 : 1             | 24.0%                 | 0.32 : 1                   |
| 250            | 80.8%                 | 4.22 : 1             | 19.2%                 | 0.24 : 1                   |
| 300            | 84.9%                 | 5.62 : 1             | 15.1%                 | 0.18 : 1                   |
| 350            | 88.2%                 | 7.50 : 1             | 11.8%                 | 0.13 : 1                   |
| 400            | 90.9%                 | 10.00 : 1            | 9.1%                  | 0.10 : 1                   |
| 450            | 93.0%                 | 13.34 : 1            | 7.0%                  | 0.07 : 1                   |
| 500            | 94.7%                 | 17.78 : 1            | 5.3%                  | 0.05 : 1                   |
| 550            | 96.0%                 | 23.71 : 1            | 4.0%                  | 0.04 : 1                   |
| 600            | 96.9%                 | 31.62 : 1            | 3.1%                  | 0.03 : 1                   |
| 650            | 97.7%                 | 42.17 : 1            | 2.3%                  | 0.02 : 1                   |
| 700            | 98.3%                 | 56.23 : 1            | 1.7%                  | 0.02 : 1                   |
| 750            | 98.7%                 | 74.99 : 1            | 1.3%                  | 0.01 : 1                   |
| 800            | 99.0%                 | 100.00 : 1           | 1.0%                  | 0.01 : 1                   |

*Notes:* `E_A = 1 / (1 + 10^{-(ΔR/400)})`. Odds = `E_A / (1 − E_A)`. The table is symmetric: a negative ΔR just swaps the roles of A and B. E_B = 1 - E_A. "Odds for B" = E_B / (1 − E_B).

## Data Files

- **players.json**  
  ```json
  {
    "Alice": {
      "singles_elo": 1024.5,
      "doubles_elo": 1012.3,
      "singles_peak_elo": 1050.0,
      "singles_peak_date": "2025-08-01",
      "doubles_peak_elo": 1020.0,
      "doubles_peak_date": "2025-07-20",
      "last_match_date": "2025-08-06"
    },
    ...
  }
  ```
- **matches.json**  
  ```json
  [
    {
      "timestamp": "2025-08-06T18:45:12",
      "type": "singles",
      "players": ["Alice", "Bob"],
      "sets": [
        {"score": "6-4", "kind": "set"},
        {"score": "7-6", "kind": "tiebreak"},
        {"score": "5-7", "kind": "set"}
      ]
    },
    ...
  ]
  ```

## Extensibility

- Adjust `K_FACTOR` in `elo_camp.py` for faster/slower convergence.  
- Add inactivity decay, CSV export, or a “history” CLI.  
- Future: build a web front-end with FastAPI + React or Streamlit.