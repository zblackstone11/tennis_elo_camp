"""
Tennis Elo Camp - Elo Rating Tracker for Tennis Matches
-------------------------------------------------------
"""
import json
from datetime import date
import os
from datetime import datetime
import re

HISTORY_FILE = "matches.json"  # File to store the list of recorded matches

PLAYERS_FILE = "players.json"  # File to store player Elo ratings and stats

def load_players():
    """Load players and their Elo ratings from PLAYERS_FILE.
    Returns a dict mapping player names to their rating info.
    """
    try:
        with open(PLAYERS_FILE) as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return data

def save_players(players):
    """Save the players dictionary to PLAYERS_FILE in JSON format."""
    with open(PLAYERS_FILE, "w") as f:
        json.dump(players, f, indent=2)

def load_history():
    """Load the match history list from HISTORY_FILE."""
    try:
        with open(HISTORY_FILE) as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    """Save the match history list to HISTORY_FILE."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_player(players, name, singles_elo=1000, doubles_elo=1000):
    """Add a new player to the players dict with specified initial Elo ratings.
    Raises ValueError if the player already exists.
    Returns the new player's data dictionary.
    """
    if name in players:
        raise ValueError(f"Player '{name}' already exists.")
    players[name] = {
        "singles_elo": singles_elo,
        "doubles_elo": doubles_elo,
        "last_match_date": str(date.today()),
        "max_singles_elo": singles_elo,
        "max_singles_date": str(date.today()),
        "max_doubles_elo": doubles_elo,
        "max_doubles_date": str(date.today())
    }
    ensure_counters_fields(players[name])
    return players[name]

def ensure_player(players, name):
    """Ensure that the player exists in the dict, creating with default ratings if missing.
    Returns the player's data dictionary.
    """
    if name not in players:
        players[name] = {
            "singles_elo": 1000,
            "doubles_elo": 1000,
            "last_match_date": str(date.today())
        }
    ensure_peak_fields(players[name])
    ensure_counters_fields(players[name])
    return players[name]

def ensure_peak_fields(p):
    """Ensure that a player's peak Elo and date fields are present."""
    if "max_singles_elo" not in p:
        p["max_singles_elo"] = p.get("singles_elo", 1000)
        p["max_singles_date"] = p.get("last_match_date", str(date.today()))
    if "max_doubles_elo" not in p:
        p["max_doubles_elo"] = p.get("doubles_elo", 1000)
        p["max_doubles_date"] = p.get("last_match_date", str(date.today()))


# --- Counters and helpers for per-mode stats and streaks
def ensure_counters_fields(p):
    """Ensure a player's per-mode counters/streak fields exist."""
    if "counters" not in p:
        p["counters"] = {}
    for mode in ("singles", "doubles"):
        if mode not in p["counters"]:
            p["counters"][mode] = {
                "matches_played": 0,
                "matches_won": 0,
                "sets_played": 0,
                "sets_won": 0,
                "tiebreaks_played": 0,
                "tiebreaks_won": 0,
                "bagels_given": 0,
                "bagels_taken": 0,
                "current_win_streak": 0,
                "best_win_streak": 0,
            }

def is_bagel(kind, a, b):
    """Return True if this set is a bagel (winner >=6 games, loser == 0)."""
    if kind != "set":
        return False
    winner = a if a > b else b
    loser = b if a > b else a
    return loser == 0 and winner >= 6

def first_set_winner(sets_logged):
    """Return 'A' if A won the first set, 'B' if B won, else None."""
    if not sets_logged:
        return None
    a, b = sets_logged[0]["games"]
    if a > b:
        return "A"
    if b > a:
        return "B"
    return None


# --- Helper functions for stats and leaderboard ---
def parse_date_yyyy_mm_dd(s):
    """Parse 'YYYY-MM-DD' into a date; return None if invalid."""
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None

def entry_mode_matches(entry, mode):
    """Return True if a history entry corresponds to the given mode ('singles' or 'doubles')."""
    t = entry.get("type")
    if mode == "singles":
        return t == "singles_series"
    if mode == "doubles":
        return t == "doubles_series"
    return False

def player_in_entry(entry, player):
    """Check if player is present in a history entry (singles or doubles)."""
    if entry.get("type") == "singles_series":
        a, b = entry.get("players", [None, None])
        return player == a or player == b
    elif entry.get("type") == "doubles_series":
        teams = entry.get("teams", [[], []])
        return any(player in team for team in teams)
    return False

def opponent_label(entry, player):
    """Return a short opponent label for printing (handles singles and doubles)."""
    if entry.get("type") == "singles_series":
        a, b = entry.get("players", [None, None])
        return b if player == a else a
    elif entry.get("type") == "doubles_series":
        teams = entry.get("teams", [[], []])
        if any(player in teams[0] for _ in [0]) and player in teams[0]:
            return " & ".join(teams[1])
        if any(player in teams[1] for _ in [0]) and player in teams[1]:
            return " & ".join(teams[0])
        # Fallback
        return " / ".join(sum(teams, []))
    return "Unknown"

def player_result_in_entry(entry, player):
    """Return 'W', 'L', or 'T' for the player in this history entry."""
    w = entry.get("winner")
    if w is None:
        return "T"
    if entry.get("type") == "singles_series":
        a, b = entry.get("players", [None, None])
        if player == a:
            return "W" if w == "A" else "L"
        elif player == b:
            return "W" if w == "B" else "L"
    elif entry.get("type") == "doubles_series":
        teams = entry.get("teams", [[], []])
        if player in teams[0]:
            return "W" if w == "A" else "L"
        if player in teams[1]:
            return "W" if w == "B" else "L"
    return "T"

def player_elo_change_in_entry(entry, player, mode):
    """Return the Elo change for player in this entry for the given mode, if present; else 0."""
    change = entry.get("elo_change", {})
    if entry.get("type") == "singles_series" and mode == "singles":
        return float(change.get(player, 0.0))
    if entry.get("type") == "doubles_series" and mode == "doubles":
        return float(change.get(player, 0.0))
    return 0.0

def sets_string(entry):
    """Compact string like '6-3, 7-6[tiebreak]' from entry['sets'].""" 
    toks = []
    for s in entry.get("sets", []):
        a, b = s.get("games", [None, None])
        kind = s.get("kind", "set")
        if kind == "tiebreak":
            toks.append(f"{a}-{b}[tiebreak]")
        else:
            toks.append(f"{a}-{b}")
    return ", ".join(toks)


#
# --- Ratings sensitivity constants (per-set and match bonus)
K_BASE = 100  # Elo K-factor for each set (applies to both singles and doubles)
K_MATCH_SINGLES = 15  # Bonus Elo for winning a singles match (applied after sets)
K_MATCH_DOUBLES = 15   # Bonus Elo for winning a doubles match (split per player)

# Tiebreak scaling: treat 4 points as ~1 game so tiebreaks count less than a full set
POINTS_PER_GAME_TIEBREAK = 4.0

# Margin of Victory scaling (per set): boosts decisive sets slightly (e.g. 6-0 > 6-4)
ALPHA_MOV = 0.20  # max +20% boost on a shutout set; ~+8% on a 6-4

# Tiebreak weight vs. a full set (proportional to TB length, clamped)
AVG_GAMES_PER_SET = 10.0   # typical games in a set
TB_MIN_FRACTION = 0.30     # shortest TB still counts ~30% of a set
TB_MAX_FRACTION = 0.70     # marathon TB capped at ~70% of a set

def mov_multiplier(actual_score):
    """Return a per-set multiplier based on decisiveness.
    actual_score: Fraction of games won by A in [0,1] (after tiebreak scaling).
    Returns: float multiplier for K-factor (1.0 for 6-6, up to 1.20 for 6-0).
    """
    s = max(0.0, min(1.0, float(actual_score)))
    return 1.0 + ALPHA_MOV * abs(2.0 * s - 1.0)

def expected_score(rating_a, rating_b):
    """Compute expected win probability for rating_a vs rating_b (Elo formula)."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_rating(rating, expected, actual, k=K_BASE):
    """Update Elo rating by K * (actual - expected)."""
    return rating + k * (actual - expected)

# --- Tiebreak and set helpers
def equivalent_games(kind, a, b):
    """Convert set/tiebreak scores to game-equivalents.
    For a standalone tiebreak, down-weight points to game-equivalents.
    Args:
        kind: "set" or "tiebreak"
        a, b: integer games/points won by each side
    Returns:
        (A_eq, B_eq): float game-equivalents for each side
    """
    if kind == "tiebreak":
        # Down-weight tiebreaks: treat 4 points as one game
        return a / POINTS_PER_GAME_TIEBREAK, b / POINTS_PER_GAME_TIEBREAK
    return float(a), float(b)

# Regex to parse set tokens like "6-3", "7-6", or "10-7[tiebreak]"
_SET_RE = re.compile(r"^(\d+)-(\d+)(?:\[(set|tiebreak)\])?$")

def parse_set_token(tok):
    """Parse tokens like '6-3', '7-6', or '10-7[tiebreak]'.
    Returns (a, b, kind) where kind is 'set' or 'tiebreak'.
    Raises ValueError on invalid input.
    """
    s = str(tok).strip()
    m = _SET_RE.match(s)
    if not m:
        raise ValueError(
            f"Invalid set token '{tok}'. Use A-B or A-B[kind], e.g., 6-3, 7-6, 10-8[tiebreak]."
        )
    a, b, kind = m.groups()
    a = int(a); b = int(b)
    return a, b, (kind or "set")

def maybe_update_peak(player, mode, today):
    """Update a player's peak Elo and date if their current rating is a new maximum."""
    if mode == "singles":
        if player["singles_elo"] > player.get("max_singles_elo", float("-inf")):
            player["max_singles_elo"] = player["singles_elo"]
            player["max_singles_date"] = today
    elif mode == "doubles":
        if player["doubles_elo"] > player.get("max_doubles_elo", float("-inf")):
            player["max_doubles_elo"] = player["doubles_elo"]
            player["max_doubles_date"] = today

def record_singles(players, name_a, name_b, games_a, games_b, kind="set"):
    """Update Elo ratings for a single set or tiebreak between two singles players.
    Applies MOV and tiebreak scaling as appropriate.
    Args:
        players: player data dictionary
        name_a, name_b: player names
        games_a, games_b: games/points won by each player
        kind: "set" or "tiebreak"
    """
    ensure_player(players, name_a)
    ensure_player(players, name_b)
    p_a = players[name_a]
    p_b = players[name_b]
    # Compute expected scores
    exp_a = expected_score(p_a["singles_elo"], p_b["singles_elo"])
    exp_b = 1 - exp_a
    # Down-weight tiebreaks by converting points to equivalent games
    A_eq, B_eq = equivalent_games(kind, games_a, games_b)
    total = A_eq + B_eq
    act_a = A_eq / total if total else 0.5
    act_b = 1 - act_a
    # Per-set counters for singles
    cs_a = p_a.setdefault("counters", {}).setdefault("singles", {})
    cs_b = p_b.setdefault("counters", {}).setdefault("singles", {})
    # Ensure default keys exist if older records
    for cs in (cs_a, cs_b):
        cs.setdefault("matches_played", 0)
        cs.setdefault("matches_won", 0)
        cs.setdefault("sets_played", 0)
        cs.setdefault("sets_won", 0)
        cs.setdefault("tiebreaks_played", 0)
        cs.setdefault("tiebreaks_won", 0)
        cs.setdefault("bagels_given", 0)
        cs.setdefault("bagels_taken", 0)
        cs.setdefault("current_win_streak", 0)
        cs.setdefault("best_win_streak", 0)
    cs_a["sets_played"] += 1
    cs_b["sets_played"] += 1
    if games_a > games_b:
        cs_a["sets_won"] += 1
    elif games_b > games_a:
        cs_b["sets_won"] += 1
    if kind == "tiebreak":
        cs_a["tiebreaks_played"] += 1
        cs_b["tiebreaks_played"] += 1
        if games_a > games_b:
            cs_a["tiebreaks_won"] += 1
        elif games_b > games_a:
            cs_b["tiebreaks_won"] += 1
    if is_bagel(kind, games_a, games_b):
        if games_a > games_b:
            cs_a["bagels_given"] += 1
            cs_b["bagels_taken"] += 1
        elif games_b > games_a:
            cs_b["bagels_given"] += 1
            cs_a["bagels_taken"] += 1
    # Margin-of-victory multiplier (same for both sides to keep zero-sum)
    k_eff = K_BASE * mov_multiplier(act_a)
    # If this set is a standalone tiebreak, scale K by TB length vs a full set
    if kind == "tiebreak":
        eq_total = A_eq + B_eq  # already in game-equivalents via POINTS_PER_GAME_TIEBREAK
        tb_fraction = max(TB_MIN_FRACTION, min(TB_MAX_FRACTION, eq_total / AVG_GAMES_PER_SET))
        k_eff *= tb_fraction
    # Update ratings
    p_a["singles_elo"] = update_rating(p_a["singles_elo"], exp_a, act_a, k=k_eff)
    p_b["singles_elo"] = update_rating(p_b["singles_elo"], exp_b, act_b, k=k_eff)
    # Update last match date and peak
    today = str(date.today())
    p_a["last_match_date"] = today
    p_b["last_match_date"] = today
    maybe_update_peak(p_a, "singles", today)
    maybe_update_peak(p_b, "singles", today)

def record_doubles(players, team_a, team_b, games_a, games_b, kind="set"):
    """Update Elo ratings for a single set or tiebreak between two doubles teams.
    Each team's Elo is the average of its two players.
    Args:
        players: player data dictionary
        team_a, team_b: tuples of player names (len=2)
        games_a, games_b: games/points won by each team
        kind: "set" or "tiebreak"
    """
    # Ensure all players exist
    for name in team_a + team_b:
        ensure_player(players, name)
    # Compute team average ratings
    ra = sum(players[n]["doubles_elo"] for n in team_a) / 2
    rb = sum(players[n]["doubles_elo"] for n in team_b) / 2
    exp_a = expected_score(ra, rb)
    exp_b = 1 - exp_a
    A_eq, B_eq = equivalent_games(kind, games_a, games_b)
    total = A_eq + B_eq
    act_a = A_eq / total if total else 0.5
    act_b = 1 - act_a
    # Per-set counters for doubles (apply to all four players)
    for name in team_a + team_b:
        p = players[name]
        cd = p.setdefault("counters", {}).setdefault("doubles", {})
        cd.setdefault("matches_played", 0)
        cd.setdefault("matches_won", 0)
        cd.setdefault("sets_played", 0)
        cd.setdefault("sets_won", 0)
        cd.setdefault("tiebreaks_played", 0)
        cd.setdefault("tiebreaks_won", 0)
        cd.setdefault("bagels_given", 0)
        cd.setdefault("bagels_taken", 0)
        cd.setdefault("current_win_streak", 0)
        cd.setdefault("best_win_streak", 0)
        cd["sets_played"] += 1
    if games_a > games_b:
        for name in team_a:
            players[name]["counters"]["doubles"]["sets_won"] += 1
    elif games_b > games_a:
        for name in team_b:
            players[name]["counters"]["doubles"]["sets_won"] += 1
    if kind == "tiebreak":
        for name in team_a + team_b:
            players[name]["counters"]["doubles"]["tiebreaks_played"] += 1
        if games_a > games_b:
            for name in team_a:
                players[name]["counters"]["doubles"]["tiebreaks_won"] += 1
        elif games_b > games_a:
            for name in team_b:
                players[name]["counters"]["doubles"]["tiebreaks_won"] += 1
    if is_bagel(kind, games_a, games_b):
        if games_a > games_b:
            for name in team_a:
                players[name]["counters"]["doubles"]["bagels_given"] += 1
            for name in team_b:
                players[name]["counters"]["doubles"]["bagels_taken"] += 1
        elif games_b > games_a:
            for name in team_b:
                players[name]["counters"]["doubles"]["bagels_given"] += 1
            for name in team_a:
                players[name]["counters"]["doubles"]["bagels_taken"] += 1
    today = str(date.today())
    # Margin-of-victory multiplier for doubles set
    k_eff = K_BASE * mov_multiplier(act_a)
    if kind == "tiebreak":
        eq_total = A_eq + B_eq  # already in game-equivalents
        tb_fraction = max(TB_MIN_FRACTION, min(TB_MAX_FRACTION, eq_total / AVG_GAMES_PER_SET))
        k_eff *= tb_fraction
    # Update each individual's doubles Elo and last match date/peak
    for name in team_a:
        old = players[name]["doubles_elo"]
        players[name]["doubles_elo"] = update_rating(old, exp_a, act_a, k=k_eff)
        players[name]["last_match_date"] = today
        maybe_update_peak(players[name], "doubles", today)
    for name in team_b:
        old = players[name]["doubles_elo"]
        players[name]["doubles_elo"] = update_rating(old, exp_b, act_b, k=k_eff)
        players[name]["last_match_date"] = today
        maybe_update_peak(players[name], "doubles", today)

# --- Match series helpers (multi-set + match bonus)
def apply_match_bonus_singles(players, name_a, name_b, Ra_start, Rb_start, winner):
    """Apply match bonus Elo after a singles series (winner gets bonus, loser loses).
    Args:
        players: player data dictionary
        name_a, name_b: player names
        Ra_start, Rb_start: starting Elo ratings before the match
        winner: "A" or "B"
    """
    E_match = expected_score(Ra_start, Rb_start)  # prob A wins
    if winner == "A":
        bonus = K_MATCH_SINGLES * (1 - E_match)
        players[name_a]["singles_elo"] += bonus
        players[name_b]["singles_elo"] -= bonus
    else:
        bonus = K_MATCH_SINGLES * E_match
        players[name_a]["singles_elo"] -= bonus
        players[name_b]["singles_elo"] += bonus

def apply_match_bonus_doubles(players, team_a, team_b, Ra_start, Rb_start, winner):
    """Apply match bonus Elo after a doubles series (split among winning/losing team).
    Args:
        players: player data dictionary
        team_a, team_b: tuples of player names (len=2)
        Ra_start, Rb_start: team average Elo at match start
        winner: "A" or "B"
    """
    E_match = expected_score(Ra_start, Rb_start)  # prob Team A wins
    if winner == "A":
        team_bonus = K_MATCH_DOUBLES * (1 - E_match)
        split = team_bonus / 2.0
        for n in team_a:
            players[n]["doubles_elo"] += split
        for n in team_b:
            players[n]["doubles_elo"] -= split
    else:
        team_bonus = K_MATCH_DOUBLES * E_match
        split = team_bonus / 2.0
        for n in team_a:
            players[n]["doubles_elo"] -= split
        for n in team_b:
            players[n]["doubles_elo"] += split

def record_series_singles(players, name_a, name_b, set_tokens):
    """Record a best-of series between two singles players (multiple sets/tiebreaks).
    Applies MOV, tiebreak scaling, and a match bonus to the winner.
    Args:
        players: player data dictionary
        name_a, name_b: player names
        set_tokens: list of strings like "6-3", "7-6", "10-8[tiebreak]"
    Returns:
        sets_logged: list of dicts with set scores/kinds
        winner: "A", "B", or None if tied
    """
    # Snapshot starting ratings for match-bonus expectation
    ensure_player(players, name_a)
    ensure_player(players, name_b)
    Ra0 = players[name_a]["singles_elo"]
    Rb0 = players[name_b]["singles_elo"]

    sets_logged = []
    wins_a = 0
    wins_b = 0
    for tok in set_tokens:
        a, b, kind = parse_set_token(tok)
        record_singles(players, name_a, name_b, a, b, kind=kind)
        sets_logged.append({"games": [a, b], "kind": kind})
        if a > b:
            wins_a += 1
        elif b > a:
            wins_b += 1
        # If tied, no increment.

    winner = None
    if wins_a > wins_b:
        winner = "A"
    elif wins_b > wins_a:
        winner = "B"

    # Only apply match bonus if there is a winner (no ties)
    if winner is not None:
        apply_match_bonus_singles(players, name_a, name_b, Ra0, Rb0, winner)

    # Update peaks after bonus and stamp last_match_date
    today = str(date.today())
    players[name_a]["last_match_date"] = today
    players[name_b]["last_match_date"] = today
    maybe_update_peak(players[name_a], "singles", today)
    maybe_update_peak(players[name_b], "singles", today)

    return sets_logged, winner

def record_series_doubles(players, team_a, team_b, set_tokens):
    """Record a best-of series between two doubles teams (multiple sets/tiebreaks).
    Applies MOV, tiebreak scaling, and a match bonus to the winning team.
    Args:
        players: player data dictionary
        team_a, team_b: tuples of player names (len=2)
        set_tokens: list of strings like "6-3", "7-6", "10-8[tiebreak]"
    Returns:
        sets_logged: list of dicts with set scores/kinds
        winner: "A", "B", or None if tied
    """
    for n in team_a + team_b:
        ensure_player(players, n)
    Ra0 = sum(players[n]["doubles_elo"] for n in team_a) / 2.0
    Rb0 = sum(players[n]["doubles_elo"] for n in team_b) / 2.0

    sets_logged = []
    wins_a = 0
    wins_b = 0
    for tok in set_tokens:
        a, b, kind = parse_set_token(tok)
        record_doubles(players, team_a, team_b, a, b, kind=kind)
        sets_logged.append({"games": [a, b], "kind": kind})
        if a > b:
            wins_a += 1
        elif b > a:
            wins_b += 1
        # If tied, no increment.

    winner = None
    if wins_a > wins_b:
        winner = "A"
    elif wins_b > wins_a:
        winner = "B"

    if winner is not None:
        apply_match_bonus_doubles(players, team_a, team_b, Ra0, Rb0, winner)

    today = str(date.today())
    for n in team_a + team_b:
        players[n]["last_match_date"] = today
        maybe_update_peak(players[n], "doubles", today)

    return sets_logged, winner


# --- Insights report generation ---
def generate_insights(players, date_str, outfile=None):
    """Create a daily insights text file summarizing leaderboards, movers (risers/sliders),
    streaks, highlights, a match log, and daily stats.

    Args:
        players: dict loaded from players.json
        date_str: 'YYYY-MM-DD' (filters matches by this date)
        outfile: optional path; defaults to insights_<date_str>.txt
    """
    history = load_history()
    day_entries = [e for e in history if e.get("date") == date_str]
    if not outfile:
        outfile = f"insights_{date_str}.txt"

    # --- Helpers -------------------------------------------------------------

    def movers_for_mode(mode):
        """Return list of (name, delta) sorted descending by delta for the given mode."""
        deltas = {}
        for e in day_entries:
            if entry_mode_matches(e, mode):
                for name, d in e.get("elo_change", {}).items():
                    deltas[name] = deltas.get(name, 0.0) + float(d)
        return sorted(deltas.items(), key=lambda kv: kv[1], reverse=True)

    def split_risers_sliders(mov):
        """Partition into positive and negative movers; negatives sorted ascending."""
        risers = [(n, d) for (n, d) in mov if d > 0]
        sliders = sorted([(n, d) for (n, d) in mov if d < 0], key=lambda kv: kv[1])
        return risers, sliders

    def active_streaks(mode):
        """Snapshot of current win streaks for the mode, sorted desc."""
        rows = []
        for name, pdata in players.items():
            ensure_counters_fields(pdata)
            c = pdata["counters"][mode]
            rows.append((c.get("current_win_streak", 0), name))
        rows.sort(reverse=True)
        return rows

    def highlights():
        """Upsets based on pre-match expectation, pulled from history day entries."""
        lines = []
        for e in day_entries:
            if e.get("type") == "singles_series":
                a, b = e.get("players", [None, None])
                winner = e.get("winner")
                Ra0 = e.get("elos_before", {}).get(a)
                Rb0 = e.get("elos_before", {}).get(b)
                if Ra0 is None or Rb0 is None:
                    continue
                E_A = expected_score(Ra0, Rb0)
                if winner == "A":
                    delta = float(e.get("elo_change", {}).get(a, 0.0))
                    if (Ra0 + 100 <= Rb0) or (E_A <= 0.35):
                        lines.append(f"Singles upset: {a} def. {b} {sets_string(e)} (pre-match E_A={E_A:.2f}, Δ {delta:+.1f})")
                elif winner == "B":
                    delta = float(e.get("elo_change", {}).get(b, 0.0))
                    if (Rb0 + 100 <= Ra0) or ((1 - E_A) <= 0.35):
                        lines.append(f"Singles upset: {b} def. {a} {sets_string(e)} (pre-match E_B={1-E_A:.2f}, Δ {delta:+.1f})")
            elif e.get("type") == "doubles_series":
                tA, tB = e.get("teams", [[], []])
                winner = e.get("winner")
                before = e.get("elos_before", {})
                if not before or not tA or not tB:
                    continue
                Ra0 = sum(before.get(n, players.get(n, {}).get("doubles_elo", 1000)) for n in tA) / 2.0
                Rb0 = sum(before.get(n, players.get(n, {}).get("doubles_elo", 1000)) for n in tB) / 2.0
                E_A = expected_score(Ra0, Rb0)
                teamA = " & ".join(tA); teamB = " & ".join(tB)
                if winner == "A":
                    delta = sum(float(e.get("elo_change", {}).get(n, 0.0)) for n in tA)
                    if (Ra0 + 100 <= Rb0) or (E_A <= 0.35):
                        lines.append(f"Doubles upset: {teamA} def. {teamB} {sets_string(e)} (pre E_A={E_A:.2f}, team Δ {delta:+.1f})")
                elif winner == "B":
                    delta = sum(float(e.get("elo_change", {}).get(n, 0.0)) for n in tB)
                    if (Rb0 + 100 <= Ra0) or ((1 - E_A) <= 0.35):
                        lines.append(f"Doubles upset: {teamB} def. {teamA} {sets_string(e)} (pre E_B={1-E_A:.2f}, team Δ {delta:+.1f})")
        return lines

    def daily_stats():
        """Aggregate simple counts for the day."""
        singles_matches = sum(1 for e in day_entries if e.get("type") == "singles_series")
        doubles_matches = sum(1 for e in day_entries if e.get("type") == "doubles_series")
        sets_total = sum(len(e.get("sets", [])) for e in day_entries)
        tiebreaks = sum(1 for e in day_entries for s in e.get("sets", []) if s.get("kind") == "tiebreak")
        bagels = 0
        for e in day_entries:
            for s in e.get("sets", []):
                kind = s.get("kind", "set")
                a, b = s.get("games", [0, 0])
                if kind == "set" and ((a >= 6 and b == 0) or (b >= 6 and a == 0)):
                    bagels += 1
        participants = set()
        for e in day_entries:
            if e.get("type") == "singles_series":
                a, b = e.get("players", [None, None])
                if a: participants.add(a)
                if b: participants.add(b)
            elif e.get("type") == "doubles_series":
                tA, tB = e.get("teams", [[], []])
                for n in (tA or []) + (tB or []):
                    participants.add(n)
        return {
            "singles_matches": singles_matches,
            "doubles_matches": doubles_matches,
            "sets_total": sets_total,
            "tiebreaks": tiebreaks,
            "bagels": bagels,
            "participants": len(participants),
        }

    def match_log_lines():
        """Format a compact match log for all day entries."""
        lines = []
        for e in day_entries:
            t = e.get("type")
            if t == "singles_series":
                a, b = e.get("players", [None, None])
                w = e.get("winner")
                if w == "A":
                    left = f"{a} def. {b}"
                    dlt = float(e.get("elo_change", {}).get(a, 0.0))
                elif w == "B":
                    left = f"{b} def. {a}"
                    dlt = float(e.get("elo_change", {}).get(b, 0.0))
                else:
                    left = f"{a} tied {b}"
                    dlt = 0.0
                flags = []
                if e.get("decided_by_tiebreak"):
                    flags.append("TB decider")
                if e.get("comeback_win"):
                    flags.append("comeback")
                flag_str = f" ({', '.join(flags)})" if flags else ""
                lines.append(f"[Singles] {left}  {sets_string(e)}  (Δ {dlt:+.1f}){flag_str}")
            elif t == "doubles_series":
                tA, tB = e.get("teams", [[], []])
                teamA = " & ".join(tA or [])
                teamB = " & ".join(tB or [])
                w = e.get("winner")
                if w == "A":
                    left = f"{teamA} def. {teamB}"
                    dlt = sum(float(e.get("elo_change", {}).get(n, 0.0)) for n in (tA or []))
                elif w == "B":
                    left = f"{teamB} def. {teamA}"
                    dlt = sum(float(e.get("elo_change", {}).get(n, 0.0)) for n in (tB or []))
                else:
                    left = f"{teamA} tied {teamB}"
                    dlt = 0.0
                flags = []
                if e.get("decided_by_tiebreak"):
                    flags.append("TB decider")
                if e.get("comeback_win"):
                    flags.append("comeback")
                flag_str = f" ({', '.join(flags)})" if flags else ""
                lines.append(f"[Doubles] {left}  {sets_string(e)}  (team Δ {dlt:+.1f}){flag_str}")
        return lines

    # --- Build report sections ----------------------------------------------

    # Leaderboards
    key_s = "singles_elo"; key_d = "doubles_elo"
    singles_lb = sorted(players.items(), key=lambda kv: kv[1][key_s], reverse=True)
    doubles_lb = sorted(players.items(), key=lambda kv: kv[1][key_d], reverse=True)

    # Movers
    mov_s = movers_for_mode("singles")
    mov_d = movers_for_mode("doubles")
    risers_s, sliders_s = split_risers_sliders(mov_s)
    risers_d, sliders_d = split_risers_sliders(mov_d)

    # Streaks (current, snapshot)
    st_s = active_streaks("singles")
    st_d = active_streaks("doubles")

    # Highlights & Match log
    hi = highlights()
    mlog = match_log_lines()

    # Daily stats
    stats = daily_stats()

    # Records / Milestones (new peaks reached today)
    milestones = []
    for name, pdata in players.items():
        # Peak singles
        if pdata.get("max_singles_date") == date_str:
            milestones.append(f"{name}: new singles peak {pdata.get('max_singles_elo', pdata.get('singles_elo', 0)):.1f}")
        # Peak doubles
        if pdata.get("max_doubles_date") == date_str:
            milestones.append(f"{name}: new doubles peak {pdata.get('max_doubles_elo', pdata.get('doubles_elo', 0)):.1f}")
    milestones.sort()

    # --- Write file ----------------------------------------------------------
    with open(outfile, "w") as f:
        f.write(f"Insights — {date_str}\n")
        f.write("=" * (11 + len(date_str)) + "\n\n")

        f.write("Singles Leaderboard:\n")
        for i, (name, data) in enumerate(singles_lb, 1):
            f.write(f"{i:>2}. {name:<12} {data[key_s]:.1f}\n")
        f.write("\n")

        f.write("Doubles Leaderboard:\n")
        for i, (name, data) in enumerate(doubles_lb, 1):
            f.write(f"{i:>2}. {name:<12} {data[key_d]:.1f}\n")
        f.write("\n")

        # Movers — Singles
        f.write("Top Risers (Singles, today):\n")
        if risers_s:
            for rank, (name, dlt) in enumerate(risers_s[:10], 1):
                f.write(f" +{rank}) {name:<12} {dlt:+.1f}\n")
        else:
            f.write(" (no singles risers today)\n")
        f.write("\n")

        f.write("Top Sliders (Singles, today):\n")
        if sliders_s:
            for rank, (name, dlt) in enumerate(sliders_s[:10], 1):
                f.write(f" -{rank}) {name:<12} {dlt:+.1f}\n")
        else:
            f.write(" (no singles sliders today)\n")
        f.write("\n")

        # Movers — Doubles
        f.write("Top Risers (Doubles, today):\n")
        if risers_d:
            for rank, (name, dlt) in enumerate(risers_d[:10], 1):
                f.write(f" +{rank}) {name:<12} {dlt:+.1f}\n")
        else:
            f.write(" (no doubles risers today)\n")
        f.write("\n")

        f.write("Top Sliders (Doubles, today):\n")
        if sliders_d:
            for rank, (name, dlt) in enumerate(sliders_d[:10], 1):
                f.write(f" -{rank}) {name:<12} {dlt:+.1f}\n")
        else:
            f.write(" (no doubles sliders today)\n")
        f.write("\n")

        # Streaks
        f.write("Active Win Streaks — Singles:\n")
        for i, (st, name) in enumerate(st_s[:10], 1):
            f.write(f" {i:>2}. {name:<12} {st}\n")
        f.write("\n")

        f.write("Active Win Streaks — Doubles:\n")
        for i, (st, name) in enumerate(st_d[:10], 1):
            f.write(f" {i:>2}. {name:<12} {st}\n")
        f.write("\n")

        # Daily Stats
        f.write("Daily Stats:\n")
        f.write(f" Matches — Singles: {stats['singles_matches']}, Doubles: {stats['doubles_matches']}\n")
        f.write(f" Sets: {stats['sets_total']} | Tiebreaks: {stats['tiebreaks']} | Bagels: {stats['bagels']}\n")
        f.write(f" Participants: {stats['participants']}\n")
        f.write("\n")

        # Match Log
        f.write("Match Log:\n")
        if mlog:
            for line in mlog:
                f.write(f" - {line}\n")
        else:
            f.write(" (no matches recorded for this date)\n")
        f.write("\n")

        # Highlights
        f.write("Highlights:\n")
        if hi:
            for line in hi:
                f.write(f" - {line}\n")
        else:
            f.write(" (no notable upsets flagged today)\n")
        f.write("\n")

        # Records / Milestones
        f.write("Records & Milestones:\n")
        if milestones:
            for m in milestones:
                f.write(f" - {m}\n")
        else:
            f.write(" (no new peaks recorded today)\n")

    return outfile


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tennis Elo Camp CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Subparser: record_series_singles
    # Records a singles match series between two players, with set/tiebreak scores.
    # Arguments: player_a, player_b, list of set tokens (e.g. 6-3 7-6 10-8[tiebreak])
    pss = sub.add_parser("record_series_singles", help="Record a singles match by set wins (e.g. 6-3 7-6 10-8[tiebreak])")
    pss.add_argument("player_a")
    pss.add_argument("player_b")
    pss.add_argument("sets", nargs='+', help="List set scores like 6-3 7-6 10-8[tiebreak]")

    # Subparser: record_series_doubles
    # Records a doubles match series between two teams, with set/tiebreak scores.
    # Arguments: two player names per team, list of set tokens
    psd = sub.add_parser("record_series_doubles", help="Record a doubles match by set wins (e.g. 6-3 8-6 7-6[tiebreak])")
    psd.add_argument("team_a", nargs=2, metavar="player")
    psd.add_argument("team_b", nargs=2, metavar="player")
    psd.add_argument("sets", nargs='+', help="List set scores like 6-3 8-6 7-6[tiebreak]")

    # Subparser: leaderboard
    # Shows the top N players by singles or doubles Elo.
    pl = sub.add_parser("leaderboard", help="Show leaderboard")
    pl.add_argument("--mode", choices=["singles", "doubles"], default="singles",
                    help="Show singles or doubles leaderboard (default: singles)")
    pl.add_argument("--top", type=int, default=10, help="Number of players to show (default: 10)")

    # Subparser: add_player
    # Adds a new player with optional initial singles/doubles Elo.
    pa = sub.add_parser("add_player", help="Add a player with a set rating")
    pa.add_argument("name", help="Player name")
    pa.add_argument("--singles_elo", type=float, default=1000, help="Initial singles Elo rating")
    pa.add_argument("--doubles_elo", type=float, default=1000, help="Initial doubles Elo rating")

    # Subparser: show_player
    # Shows a player's current and peak singles/doubles Elo.
    pshow = sub.add_parser("show_player", help="Show a player's current and peak Elo")
    pshow.add_argument("name", help="Player name")

    # Subparser: stats (per-player card)
    pst = sub.add_parser("stats", help="Show a player's stats card")
    pst.add_argument("name", help="Player name")
    pst.add_argument("--mode", choices=["singles", "doubles"], default="singles", help="Mode (default: singles)")
    group = pst.add_mutually_exclusive_group()
    group.add_argument("--since", type=str, help="Only consider matches on/after this date (YYYY-MM-DD) for momentum & recent list")
    group.add_argument("--last", type=int, help="Only consider the last N matches for momentum & recent list (default 5 if neither specified)")
    pst.add_argument("--h2h", type=str, help="Optional head-to-head opponent")

    # Subparser: stats-leaderboard (group summaries)
    psl = sub.add_parser("stats-leaderboard", help="Show extended leaderboard and summaries")
    psl.add_argument("--mode", choices=["singles", "doubles"], default="singles", help="Mode (default: singles)")
    psl.add_argument("--top", type=int, default=10, help="Top N by rating (default: 10)")
    psl.add_argument("--momentum", action="store_true", help="Show biggest movers (sum of Elo deltas)")
    psl.add_argument("--streaks", action="store_true", help="Show longest active win streaks")
    psl.add_argument("--since", type=str, help="For momentum: on/after YYYY-MM-DD")
    psl.add_argument("--last", type=int, help="For momentum: last N matches per player")

    # Subparser: insights (daily report file)
    pins = sub.add_parser("insights", help="Write a daily insights report to a text file")
    pins.add_argument("--date", type=str, default=str(date.today()), help="Date to summarize (YYYY-MM-DD). Default: today")
    pins.add_argument("--outfile", type=str, help="Optional output path (defaults to insights_<date>.txt)")

    args = parser.parse_args()
    players = load_players()

    if args.command == "record_series_singles":
        # Snapshot pre-match Elo
        Ra_before = players.get(args.player_a, {}).get("singles_elo", 1000)
        Rb_before = players.get(args.player_b, {}).get("singles_elo", 1000)

        sets_logged, winner = record_series_singles(players, args.player_a, args.player_b, args.sets)

        # Update match counters & streaks
        pa = players[args.player_a]
        pb = players[args.player_b]
        for p in (pa, pb):
            ensure_counters_fields(p)
        csa = pa["counters"]["singles"]
        csb = pb["counters"]["singles"]
        csa["matches_played"] += 1
        csb["matches_played"] += 1
        if winner == "A":
            csa["matches_won"] += 1
            csa["current_win_streak"] += 1
            csa["best_win_streak"] = max(csa["best_win_streak"], csa["current_win_streak"])
            csb["current_win_streak"] = 0
        elif winner == "B":
            csb["matches_won"] += 1
            csb["current_win_streak"] += 1
            csb["best_win_streak"] = max(csb["best_win_streak"], csb["current_win_streak"])
            csa["current_win_streak"] = 0
        # If tie: no change to streaks

        # Flags
        decided_by_tb = bool(sets_logged and sets_logged[-1]["kind"] == "tiebreak")
        fs_winner = first_set_winner(sets_logged)
        comeback_win = (winner is not None and fs_winner is not None and winner != fs_winner)

        # Snapshot post-match Elo
        Ra_after = players[args.player_a]["singles_elo"]
        Rb_after = players[args.player_b]["singles_elo"]

        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "date": str(date.today()),
            "type": "singles_series",
            "players": [args.player_a, args.player_b],
            "sets": sets_logged,
            "winner": winner,
            "decided_by_tiebreak": decided_by_tb,
            "comeback_win": comeback_win,
            "elos_before": {args.player_a: Ra_before, args.player_b: Rb_before},
            "elos_after": {args.player_a: Ra_after, args.player_b: Rb_after},
            "elo_change": {args.player_a: Ra_after - Ra_before, args.player_b: Rb_after - Rb_before}
        })
        save_history(history)
        save_players(players)
        if winner is None:
            print(f"Recorded singles series for {args.player_a} vs {args.player_b} ({len(sets_logged)} sets) — tie. No match bonus applied.")
        else:
            print(f"Recorded singles series for {args.player_a} vs {args.player_b} ({len(sets_logged)} sets), winner {winner}.")

    elif args.command == "record_series_doubles":
        ta = tuple(args.team_a)
        tb = tuple(args.team_b)
        # Snapshot pre-match Elo for all four players
        Ra_before = sum(players.get(n, {}).get("doubles_elo", 1000) for n in ta) / 2.0
        Rb_before = sum(players.get(n, {}).get("doubles_elo", 1000) for n in tb) / 2.0
        indiv_before = {n: players.get(n, {}).get("doubles_elo", 1000) for n in ta + tb}

        sets_logged, winner = record_series_doubles(players, ta, tb, args.sets)

        # Update match counters & streaks for all four
        for n in ta + tb:
            ensure_counters_fields(players[n])
            players[n]["counters"]["doubles"]["matches_played"] += 1
        if winner == "A":
            for n in ta:
                cd = players[n]["counters"]["doubles"]
                cd["matches_won"] += 1
                cd["current_win_streak"] += 1
                cd["best_win_streak"] = max(cd["best_win_streak"], cd["current_win_streak"])
            for n in tb:
                players[n]["counters"]["doubles"]["current_win_streak"] = 0
        elif winner == "B":
            for n in tb:
                cd = players[n]["counters"]["doubles"]
                cd["matches_won"] += 1
                cd["current_win_streak"] += 1
                cd["best_win_streak"] = max(cd["best_win_streak"], cd["current_win_streak"])
            for n in ta:
                players[n]["counters"]["doubles"]["current_win_streak"] = 0
        # If tie: no change to streaks

        decided_by_tb = bool(sets_logged and sets_logged[-1]["kind"] == "tiebreak")
        fs_winner = first_set_winner(sets_logged)
        comeback_win = (winner is not None and fs_winner is not None and winner != fs_winner)

        indiv_after = {n: players[n]["doubles_elo"] for n in ta + tb}

        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "date": str(date.today()),
            "type": "doubles_series",
            "teams": [list(ta), list(tb)],
            "sets": sets_logged,
            "winner": winner,
            "decided_by_tiebreak": decided_by_tb,
            "comeback_win": comeback_win,
            "elos_before": indiv_before,
            "elos_after": indiv_after,
            "elo_change": {n: indiv_after[n] - indiv_before[n] for n in indiv_after}
        })
        save_history(history)
        save_players(players)
        if winner is None:
            print(f"Recorded doubles series for {args.team_a} vs {args.team_b} ({len(sets_logged)} sets) — tie. No match bonus applied.")
        else:
            print(f"Recorded doubles series for {args.team_a} vs {args.team_b} ({len(sets_logged)} sets), winner {winner}.")

    elif args.command == "leaderboard":
        # Show the top N players sorted by singles or doubles Elo.
        key = "singles_elo" if args.mode == "singles" else "doubles_elo"
        sorted_players = sorted(players.items(), key=lambda kv: kv[1][key], reverse=True)[: args.top]
        print(f"{args.mode.title()} Leaderboard:")
        for name, data in sorted_players:
            print(f"{name}: {data[key]:.1f}")

    elif args.command == "add_player":
        # Add a new player with optional initial Elo ratings.
        try:
            add_player(players, args.name, args.singles_elo, args.doubles_elo)
            save_players(players)
            print(f"Added player {args.name} with singles Elo {args.singles_elo} and doubles Elo {args.doubles_elo}")
        except ValueError as e:
            print(e)

    elif args.command == "show_player":
        # Show a player's current and peak Elo ratings.
        if args.name in players:
            p = players[args.name]
            print(f"{args.name}:")
            print(f"  Singles Elo: {p['singles_elo']:.1f} (peak {p.get('max_singles_elo', p['singles_elo']):.1f} on {p.get('max_singles_date', '-')})")
            print(f"  Doubles Elo: {p['doubles_elo']:.1f} (peak {p.get('max_doubles_elo', p['doubles_elo']):.1f} on {p.get('max_doubles_date', '-')})")
        else:
            print(f"Player '{args.name}' not found.")

    elif args.command == "stats":
        name = args.name
        mode = args.mode
        if name not in players:
            print(f"Player '{name}' not found.")
            exit(1)
        p = players[name]
        # Pull counters
        ensure_counters_fields(p)
        c = p["counters"][mode]
        # Momentum window
        history = load_history()
        # Filter entries by player & mode
        entries = [e for e in history if entry_mode_matches(e, mode) and player_in_entry(e, name)]
        # Order by timestamp if present, else by date string
        def sort_key(e):
            return e.get("timestamp") or (e.get("date") or "") 
        entries.sort(key=sort_key, reverse=True)
        # Apply --since or --last
        recent = entries
        if args.since:
            d0 = parse_date_yyyy_mm_dd(args.since)
            if d0:
                recent = [e for e in entries if parse_date_yyyy_mm_dd(e.get("date","")) and parse_date_yyyy_mm_dd(e.get("date","")) >= d0]
        elif args.last:
            recent = entries[: args.last]
        else:
            recent = entries[:5]  # default window

        # Compute momentum (sum of Elo changes over the window)
        momentum = sum(player_elo_change_in_entry(e, name, mode) for e in recent)

        # Header with rating + peak
        peak_val = p.get("max_singles_elo" if mode=="singles" else "max_doubles_elo", p[f"{mode}_elo"])
        peak_date = p.get("max_singles_date" if mode=="singles" else "max_doubles_date", "-")
        print(f"{name} — {mode.title()}")
        print(f"Rating {p[f'{mode}_elo']:.2f} | Peak {peak_val:.2f} ({peak_date})")
        # Record
        mp = c.get("matches_played", 0)
        mw = c.get("matches_won", 0)
        sp = c.get("sets_played", 0)
        sw = c.get("sets_won", 0)
        print(f"Matches {mw}–{mp-mw} | Sets {sw}–{sp-sw}")
        # Streaks
        print(f"Streak {c.get('current_win_streak',0)} (Best {c.get('best_win_streak',0)})")
        # TB and bagels
        tbp = c.get("tiebreaks_played", 0)
        tbw = c.get("tiebreaks_won", 0)
        tb_pct = (100.0 * tbw / tbp) if tbp else 0.0
        print(f"Tiebreaks {tbw}–{tbp - tbw} ({tb_pct:.0f}%)")
        print(f"Bagels {c.get('bagels_given',0)} given / {c.get('bagels_taken',0)} taken")
        # Momentum
        if args.since:
            print(f"Momentum since {args.since}: {momentum:+.1f}")
        elif args.last:
            print(f"Momentum (last {args.last}): {momentum:+.1f}")
        else:
            print(f"Momentum (last 5): {momentum:+.1f}")
        # Recent results list
        print("Recent:")
        for e in recent:
            res = player_result_in_entry(e, name)
            # Build opponent label according to mode and entry
            opponent_names = []
            if e.get("type") == "singles_series":
                a, b = e.get("players", [None, None])
                opponent_names = [b if name == a else a]
            elif e.get("type") == "doubles_series":
                teams = e.get("teams", [[], []])
                # Flatten all names except the player's team
                if name in teams[0]:
                    opponent_names = teams[1] + teams[0]
                elif name in teams[1]:
                    opponent_names = teams[0] + teams[1]
                else:
                    opponent_names = sum(teams, [])
            # Clean opponent label logic
            if mode == "doubles":
                opponent_label = f"{' & '.join(opponent_names[:2])} vs {' & '.join(opponent_names[2:])}"
            else:
                opponent_label = opponent_names[0]
            delta = player_elo_change_in_entry(e, name, mode)
            print(f"  {res} vs {opponent_label:<18} {sets_string(e):<24} (Δ {delta:+.1f})")

        # Head-to-head if requested
        if args.h2h:
            opp = args.h2h
            if opp not in players:
                print(f"\n(H2H) Opponent '{opp}' not found.")
            else:
                # Filter entries where both are present in this mode
                h2h_entries = [e for e in entries if player_in_entry(e, opp)]
                h2h_matches = len(h2h_entries)
                h2h_w = sum(1 for e in h2h_entries if player_result_in_entry(e, name) == "W")
                # Compute sets W-L in head-to-head
                sets_w = 0; sets_l = 0
                for e in h2h_entries:
                    for s in e.get("sets", []):
                        a, b = s.get("games", [0,0])
                        # Determine side of 'name' in this entry
                        if e.get("type") == "singles_series":
                            a_name, b_name = e.get("players", [None, None])
                            if name == a_name:
                                if a > b: sets_w += 1
                                elif b > a: sets_l += 1
                            elif name == b_name:
                                if b > a: sets_w += 1
                                elif a > b: sets_l += 1
                        else:  # doubles
                            tA, tB = e.get("teams", [[], []])
                            if name in tA:
                                if a > b: sets_w += 1
                                elif b > a: sets_l += 1
                            elif name in tB:
                                if b > a: sets_w += 1
                                elif a > b: sets_l += 1
                print(f"\nHead-to-head vs {opp}:")
                print(f"  Matches {h2h_w}–{h2h_matches - h2h_w} | Sets {sets_w}–{sets_l}")
                if h2h_entries:
                    le = h2h_entries[0]
                    print(f"  Last: {player_result_in_entry(le, name)} {sets_string(le)} (Δ {player_elo_change_in_entry(le, name, mode):+.1f})")

    elif args.command == "stats-leaderboard":
        mode = args.mode
        key = "singles_elo" if mode == "singles" else "doubles_elo"
        # Sorted leaderboard
        sorted_players = sorted(players.items(), key=lambda kv: kv[1][key], reverse=True)[: args.top]
        print(f"{mode.title()} Leaderboard (Top {args.top}):")
        for i, (name, data) in enumerate(sorted_players, 1):
            print(f"{i:>2}. {name:<12} {data[key]:.2f}")

        history = load_history()
        if args.momentum:
            # Compute momentum since date or last N per player
            d0 = parse_date_yyyy_mm_dd(args.since) if args.since else None
            last_n = args.last
            movers = []
            for name in players.keys():
                # All entries for this player & mode
                entries = [e for e in history if entry_mode_matches(e, mode) and player_in_entry(e, name)]
                # Sort newest first
                entries.sort(key=lambda e: e.get("timestamp") or (e.get("date") or ""), reverse=True)
                if d0:
                    entries = [e for e in entries if parse_date_yyyy_mm_dd(e.get("date","")) and parse_date_yyyy_mm_dd(e.get("date","")) >= d0]
                elif last_n:
                    entries = entries[: last_n]
                else:
                    entries = entries[:5]
                delta = sum(player_elo_change_in_entry(e, name, mode) for e in entries)
                if entries:
                    movers.append((delta, name))
            movers.sort(reverse=True)  # biggest gainers first
            print("\nBiggest Movers:")
            for rank, (delta, name) in enumerate(movers[:10], 1):
                print(f" +{rank}) {name:<12} {delta:+.1f}")
            movers.sort()  # biggest droppers first
            print("\nBiggest Droppers:")
            for rank, (delta, name) in enumerate(movers[:10], 1):
                print(f" -{rank}) {name:<12} {delta:+.1f}")

        if args.streaks:
            # Longest active win streaks (need counters)
            streaks = []
            for name, data in players.items():
                ensure_counters_fields(data)
                c = data["counters"][mode]
                streaks.append((c.get("current_win_streak", 0), name))
            streaks.sort(reverse=True)
            print("\nActive Win Streaks:")
            for i, (st, name) in enumerate(streaks[:10], 1):
                print(f" {i:>2}. {name:<12} {st}")

    elif args.command == "insights":
        day = args.date
        out = generate_insights(players, day, outfile=args.outfile)
        print(f"Wrote insights to {out}")