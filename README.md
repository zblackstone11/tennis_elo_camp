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

  Ratings are updated **per set or tiebreak** using the expected and actual scores, with tiebreak sets weighted proportionally based on their length relative to a typical set. The per-set rating change incorporates a margin-of-victory scaling multiplier that adjusts the effective K-factor depending on how decisive the set win was.

  The rating update formula per set is:

  ```
  ΔR_set = K_eff × (S - E)
  ```

  where:
  - `K_eff` = `K_BASE` × margin-of-victory multiplier × tiebreak fraction (if applicable),
  - `S` is the actual score for the set,
  - `E` is the expected score for the set.

  After summing the rating changes from all sets and tiebreaks, a **match-win bonus** is applied once per match to the winner's total rating adjustment:

  ```
  ΔR_total = Σ ΔR_set + match_win_bonus
  ```

  The match-win bonus is calculated as:

  ```
  match_win_bonus = K_BASE × MATCH_WIN_BONUS_FRACTION × (1 - E_match)
  ```

  where `E_match` is the expected match win probability for the winner (computed from the players' pre-match ratings).

- Matches consist of multiple sets, each scored and weighted individually.
- Tiebreaks are explicitly indicated by the `tiebreak` keyword; they are not inferred from scores.
- Match winner is determined by the number of sets won, not total games.

### Margin-of-Victory Scaling

The **Margin-of-Victory (MOV) Scaling** adjusts the magnitude of rating changes based on the decisiveness of each set win, rewarding more dominant set victories and slightly dampening the impact of very close sets.

The MOV multiplier per set is calculated as:

```
MOV_multiplier = 1 + ALPHA_MOV × |2S - 1|
```

where:
- `S` is the actual score for the set (games won divided by total games),
- `ALPHA_MOV` is the margin-of-victory scaling constant (default **0.20**).

This multiplier is applied to the base K-factor for the set, effectively increasing the rating change for more decisive wins. For example:
- A 6–0 set (S = 1) results in approximately a +20% rating change,
- A close 7–6 set (S ≈ 0.54) results in about a +2% increase.

This approach rewards more decisive set wins and slightly reduces the impact of close-set results, improving predictive accuracy while maintaining fairness.

### Tiebreak Weighting (Proportional)

Tiebreak sets (entered as "10-8[tiebreak]", etc.) are intentionally weighted **less than a full set** to reflect their shorter length and lower impact on overall match outcome.

The effective K-factor for a tiebreak is scaled proportionally to its length in **equivalent games**, calculated as:

```
eq_total = (points_won + points_lost) / 4
```

This equivalent game count is then converted to a fraction of a typical set length (`AVG_GAMES_PER_SET`, default **10.0**), and clamped between minimum and maximum fractions:

```
TB_fraction = clamp(eq_total / AVG_GAMES_PER_SET, TB_MIN_FRACTION, TB_MAX_FRACTION)
```

where:
- `TB_MIN_FRACTION` = 0.30 (minimum fraction of a set a tiebreak can count for),
- `TB_MAX_FRACTION` = 0.70 (maximum fraction).

The effective K-factor for the tiebreak is:

```
K_eff = K_BASE × MOV_multiplier × TB_fraction
```

**Intuition:**  
- A typical super tiebreak like "10-8[tiebreak]" counts for about **45%** of a normal set;  
- Very short tiebreaks are clamped to **30%**;  
- Marathon tiebreaks are capped at **70%**.

This keeps tiebreaks meaningful but clearly less impactful than full sets, reflecting their shorter duration and importance.

| Constant                 | Value    | Purpose                                           |
|--------------------------|----------|---------------------------------------------------|
| AVG_GAMES_PER_SET        | 10.0     | Typical number of games in a set (for TB scaling) |
| TB_MIN_FRACTION          | 0.30     | Minimum fraction of a set that a TB can count for |
| TB_MAX_FRACTION          | 0.70     | Maximum fraction of a set that a TB can count for |

### Constants


| Constant                 | Value    | Purpose                                           |
|--------------------------|----------|---------------------------------------------------|
| Starting Elo             | 1000     | Baseline rating for all new players               |
| Scale factor             | 400      | Δ of 400 ⇒ ~10:1 odds in win probability          |
| Base K-factor            | 80       | Sensitivity of rating changes per set             |
| Match-win bonus fraction | 0.10     | Fraction of K_BASE used as bonus for match winner |
| Margin-of-Victory Scaling (ALPHA_MOV) | 0.20     | Adjusts rating changes based on decisiveness of set wins |
| Tiebreak fraction clamp  | 0.30–0.70| Limits impact of very short or very long tiebreaks|

### Choosing K and Match Bonus


Recommended ranges for K-factor and match-win bonus, depending on your season/event length:

- **Short events (few matches):**
  - K ≈ 80–100
  - Match bonus ≈ 8–15% of K
- **Season-long (dozens of matches):**
  - K ≈ 40–60
  - Match bonus ≈ 8–12% of K
- **Multi-year or ongoing ladders:**
  - K ≈ 20–30
  - Match bonus ≈ 5–8% of K

**High K:** Adapts quickly to new skill levels, but ratings are more volatile (large swings from upsets or streaks).  
**Low K:** Ratings are more stable and resistant to random swings, but slow to reflect true changes in skill.

**Match bonus** is applied **once per match** (to the total rating change), in addition to the per-set rating adjustments. It is computed based on the winner's expected match probability and helps reward overall match wins beyond set-by-set performance.

When using margin-of-victory scaling, the effective K-factor per set varies slightly based on the scoreline, reflecting the decisiveness of each set. When tiebreak weighting is enabled, a tiebreak’s effective K-factor is further reduced by its fractional weight, typically between 30% and 70% of a full set.

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