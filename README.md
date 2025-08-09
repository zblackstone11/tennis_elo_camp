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

Run commands with `python3 elo_camp.py` (or `python elo_camp.py` on systems where Python 3 is the default).

### Record a Singles Match with Multiple Sets
```
python3 elo_camp.py record_series_singles <player_a> <player_b> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
> Shell tip: if your set token includes `[tiebreak]`, put it in quotes (e.g., "7-6[tiebreak]") so shells like zsh don't treat the brackets as glob patterns.
- Each set is recorded as `<games_a>-<games_b>[kind]`, where `[kind]` is optional.
- If the kind is omitted, the system treats the score as a normal set.
- Use `[tiebreak]` explicitly only when indicating a tiebreak set.
- The match can include multiple sets.
- The winner is determined by the number of sets won, not total games.
- Example:
  ```bash
  python3 elo_camp.py record_series_singles Alice Bob 6-4 "7-6[tiebreak]" 5-7
  ```

### Record a Doubles Match with Multiple Sets
```
python3 elo_camp.py record_series_doubles <team_a1> <team_a2> <team_b1> <team_b2> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
> Shell tip: if your set token includes `[tiebreak]`, put it in quotes (e.g., "10-8[tiebreak]").
- Similar to singles, each set is `<games_a>-<games_b>[kind]` with optional kind.
- If the kind is omitted, the system treats the score as a normal set.
- Use `[tiebreak]` explicitly only when indicating a tiebreak set.
- Example:
  ```bash
  python3 elo_camp.py record_series_doubles Alice Bob Charlie Dana 6-3 4-6 "7-6[tiebreak]"
  ```

### Add a Player with a Set Rating
```
python3 elo_camp.py add_player <name> [--singles_elo <rating>] [--doubles_elo <rating>]
```
- Adds a new player with the specified singles and/or doubles Elo rating (default 1000 for each).
- Example:
  ```bash
  python3 elo_camp.py add_player Eve --singles_elo 1200 --doubles_elo 1100
  ```

### View Leaderboard
```
python3 elo_camp.py leaderboard --mode singles|doubles --top <N>
```
- Show top N players in singles or doubles.
- Example:
  ```bash
  python3 elo_camp.py leaderboard --mode singles --top 5
  ```



### Show Player Details
```
python3 elo_camp.py show_player <name>
```
- Displays current and peak singles and doubles ratings along with the dates those peaks were achieved.

### Player Stats Card (`stats`)
```
python3 elo_camp.py stats <player> [--mode singles|doubles] [--last N | --since YYYY-MM-DD] [--h2h OPPONENT]
```
- Shows a detailed stats card for a player, including:
  - Current and peak rating (singles/doubles)
  - Wins, losses, and W–L record
  - Streaks (current and longest win/loss)
  - Tiebreak and bagel stats (number won/lost, record)
  - Head-to-head vs a specific opponent (with `--h2h`)
  - Momentum (recent results, rating trend)
  - Recent match results (last 5 or 10)
- **Usage examples:**
  - Singles stats for Alice:
    ```bash
    python3 elo_camp.py stats Alice --mode singles
    ```
  - Doubles stats for Bob:
    ```bash
    python3 elo_camp.py stats Bob --mode doubles
    ```
  - Stats for Alice's last 8 singles matches:
    ```bash
    python3 elo_camp.py stats Alice --mode singles --last 8
    ```
  - Stats for Charlie since July 1, 2025:
    ```bash
    python3 elo_camp.py stats Charlie --since 2025-07-01
    ```
  - Singles H2H
    ```bash
    python3 elo_camp.py stats Alice --h2h Bob
    ```
  - Doubles: H2H vs an opposing player
    ```bash
    python3 elo_camp.py stats Jill --mode doubles --h2h Rhys
    ```

-### Extended Leaderboard (`stats-leaderboard`)
```
python3 elo_camp.py stats-leaderboard --mode singles|doubles [--momentum] [--streaks] [--top N] [--last N | --since YYYY-MM-DD]
```
- Shows an extended leaderboard.
  - By default: prints rating only (Top N).
  - Add `--momentum` to include recent Elo movement; add `--streaks` to include current streaks.
  - With `--momentum`: adds recent form (e.g., last 5 results, rating change over last N matches).
  - With `--streaks`: adds current and longest win/loss streaks.
- **Usage examples:**
  - Standard singles leaderboard with stats:
    ```bash
    python3 elo_camp.py stats-leaderboard --mode singles --top 10
    ```
  - Doubles leaderboard with momentum and streaks:
    ```bash
    python3 elo_camp.py stats-leaderboard --mode doubles --momentum --streaks --top 6
    ```
  - Singles movers over the last 5 matches per player
    ```bash
    python3 elo_camp.py stats-leaderboard --mode singles --momentum --last 5
    ```

### Daily Insights (`insights`)
```
python3 elo_camp.py insights --date YYYY-MM-DD [--outfile path/to/file.txt]
```
- Writes a daily text report (leaderboards, biggest movers, active streaks, highlights/upsets) for the specified date by scanning `matches.json`.
- Example:
  ```bash
  python3 elo_camp.py insights --date 2025-08-08
  ```

> **Note:** Both `stats` and `stats-leaderboard` use `matches.json` and `players.json` for their calculations. They are most useful after you have recorded several matches.

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

  After summing the rating changes from all sets, a **match-win bonus** is applied once per match to the winner's total adjustment. The bonus depends on how expected the win was, using the pre‑match ratings:

  - **Singles:** `bonus = K_MATCH_SINGLES × (1 − E_match)` if A wins; if B wins, `bonus = K_MATCH_SINGLES × E_match`.
  - **Doubles (per player):** compute the team pre‑match expectation from the two players’ **average** ratings; the team bonus is `K_MATCH_DOUBLES × (1 − E_match)` (or `× E_match` if Team B wins) and is split equally across the two players on each side.

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
| Base K-factor            | 100      | Sensitivity of rating changes per set             |
| Match-win bonus (singles) | 15      | Bonus applied once per singles match (scaled by E_match) |
| Match-win bonus (doubles) | 15      | Team bonus split across two players (scaled by E_match) |
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

**Current config in this repo:** `K_BASE = 100`, `K_MATCH_SINGLES = 15`, `K_MATCH_DOUBLES = 15`, `ALPHA_MOV = 0.20`, tiebreak fraction clamp = 0.30–0.70. Adjust in `elo_camp.py` if you want faster/slower movement.

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
      "max_singles_elo": 1050.0,
      "max_singles_date": "2025-08-01",
      "max_doubles_elo": 1020.0,
      "max_doubles_date": "2025-07-20",
      "last_match_date": "2025-08-06",
      "counters": {
        "singles": {
          "matches_played": 12, "matches_won": 8,
          "sets_played": 24, "sets_won": 15,
          "tiebreaks_played": 3, "tiebreaks_won": 2,
          "bagels_given": 1, "bagels_taken": 0,
          "current_win_streak": 3, "best_win_streak": 4
        },
        "doubles": {
          "matches_played": 9, "matches_won": 6,
          "sets_played": 18, "sets_won": 11,
          "tiebreaks_played": 2, "tiebreaks_won": 1,
          "bagels_given": 0, "bagels_taken": 1,
          "current_win_streak": 1, "best_win_streak": 3
        }
      }
    }
  }
  ```
- **matches.json**  
  ```json
  [
    {
      "timestamp": "2025-08-08T10:15:42",
      "date": "2025-08-08",
      "type": "singles_series",
      "players": ["Alice", "Bob"],
      "sets": [
        {"games": [6,4], "kind": "set"},
        {"games": [7,6], "kind": "tiebreak"}
      ],
      "winner": "A",
      "decided_by_tiebreak": true,
      "comeback_win": false,
      "elos_before": {"Alice": 1200.0, "Bob": 1180.0},
      "elos_after": {"Alice": 1211.5, "Bob": 1168.5},
      "elo_change": {"Alice": 11.5, "Bob": -11.5}
    },
    {
      "timestamp": "2025-08-08T11:02:10",
      "date": "2025-08-08",
      "type": "doubles_series",
      "teams": [["Alice","Bob"], ["Charlie","Dana"]],
      "sets": [
        {"games": [6,3], "kind": "set"},
        {"games": [4,6], "kind": "set"},
        {"games": [10,7], "kind": "tiebreak"}
      ],
      "winner": "A",
      "decided_by_tiebreak": true,
      "comeback_win": true,
      "elos_before": {"Alice": 1100.0, "Bob": 1120.0, "Charlie": 1110.0, "Dana": 1090.0},
      "elos_after": {"Alice": 1107.3, "Bob": 1127.3, "Charlie": 1102.7, "Dana": 1082.7},
      "elo_change": {"Alice": 7.3, "Bob": 7.3, "Charlie": -7.3, "Dana": -7.3}
    }
  ]
  ```
> Fields like `decided_by_tiebreak`, `comeback_win`, `elos_before/after`, and `elo_change` are generated automatically and power the `stats`, `stats-leaderboard`, and `insights` commands.

## Extensibility

- Adjust `K_BASE`, `K_MATCH_SINGLES`, `K_MATCH_DOUBLES`, `ALPHA_MOV`, and the tiebreak fraction clamps (`TB_MIN_FRACTION`/`TB_MAX_FRACTION`, `AVG_GAMES_PER_SET`) in `elo_camp.py` for faster/slower movement.  
- Add inactivity decay, CSV export, or a “history” CLI.  
- Future: build a web front-end with FastAPI + React or Streamlit.