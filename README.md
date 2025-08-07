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
python elo_camp.py record_singles <player_a> <player_b> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
- Each set is recorded as `<games_a>-<games_b>[kind]`, where `[kind]` is optional and should be in square brackets with either `set` or `tiebreak`.
- The match can include multiple sets.
- The winner is determined by the number of sets won, not total games.
- Example:
  ```bash
  python elo_camp.py record_singles Alice Bob 6-4[set] 7-6[tiebreak] 5-7[set]
  ```

### Record a Doubles Match with Multiple Sets
```
python elo_camp.py record_doubles <team_a1> <team_a2> <team_b1> <team_b2> <games_a>-<games_b>[kind] [<games_a>-<games_b>[kind] ...]
```
- Similar to singles, each set is `<games_a>-<games_b>[kind]` with optional kind.
- Example:
  ```bash
  python elo_camp.py record_doubles Alice Bob Charlie Dana 6-3[set] 4-6[set] 7-6[tiebreak]
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
  ```
  R_new = R_old + K * (S - E) + match_win_bonus + tiebreak_scaling
  ```
- Matches consist of multiple sets, each scored individually.
- Tiebreaks are explicitly indicated by the `tiebreak` keyword; they are not inferred from scores.
- Match winner is determined by the number of sets won, not total games.

### Constants

| Constant           | Value | Purpose                                           |
|--------------------|-------|---------------------------------------------------|
| Starting Elo       | 1000  | Baseline rating for all new players               |
| Scale factor       | 400   | Δ of 400 ⇒ ~10:1 odds in win probability          |
| Base K-factor      | 80    | Sensitivity of rating changes per match           |
| Match-win bonus    | Variable | Additional rating bonus for winning the match  |
| Tiebreak scaling   | Variable | Adjusts rating impact for tiebreak sets         |

### Rating Difference Examples

| ΔR = R_A − R_B | Win Probability (E) | Odds (wins : losses) |
|----------------|---------------------|----------------------|
| 0              | 50%                 | 1 : 1                |
| 100            | 64%                 | 1.78 : 1             |
| 200            | 75.9%               | 3.17 : 1             |
| 300            | 84.9%               | 5.62 : 1             |
| 400            | 90.9%               | 10 : 1               |

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