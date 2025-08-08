import json
from datetime import date
import os
from datetime import datetime
import re

HISTORY_FILE = "matches.json"

PLAYERS_FILE = "players.json"

def load_players():
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
    with open(PLAYERS_FILE, "w") as f:
        json.dump(players, f, indent=2)

def load_history():
    try:
        with open(HISTORY_FILE) as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# Add a player with specified ratings
def add_player(players, name, singles_elo=1000, doubles_elo=1000):
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
    return players[name]

def ensure_player(players, name):
    if name not in players:
        players[name] = {
            "singles_elo": 1000,
            "doubles_elo": 1000,
            "last_match_date": str(date.today())
        }
    ensure_peak_fields(players[name])
    return players[name]

def ensure_peak_fields(p):
    if "max_singles_elo" not in p:
        p["max_singles_elo"] = p.get("singles_elo", 1000)
        p["max_singles_date"] = p.get("last_match_date", str(date.today()))
    if "max_doubles_elo" not in p:
        p["max_doubles_elo"] = p.get("doubles_elo", 1000)
        p["max_doubles_date"] = p.get("last_match_date", str(date.today()))


# Ratings sensitivity (per-set)
K_BASE = 80
K_MATCH_SINGLES = 12
K_MATCH_DOUBLES = 8  # applied per TEAM, then split evenly

# Tiebreak scaling: treat 4 points as ~1 game so TBs count less but still more than most games
POINTS_PER_GAME_TIEBREAK = 4.0

# Margin of Victory scaling (per set): boosts decisive sets slightly
ALPHA_MOV = 0.20  # max +20% boost on a shutout set; ~+8% on a 6-4

# Tiebreak weight vs. a full set (proportional to TB length, clamped)
AVG_GAMES_PER_SET = 10.0   # typical games in a set
TB_MIN_FRACTION = 0.30     # shortest TB still counts ~30% of a set
TB_MAX_FRACTION = 0.70     # marathon TB capped at ~70% of a set

def mov_multiplier(actual_score):
    """Return a per-set multiplier based on decisiveness.
    actual_score is A's fraction in [0,1] for that set (after TB scaling).
    Multiplier = 1 + ALPHA_MOV * |2S - 1|, so 7-6 ~1.02, 6-4 ~1.08, 6-0 = 1.20.
    """
    s = max(0.0, min(1.0, float(actual_score)))
    return 1.0 + ALPHA_MOV * abs(2.0 * s - 1.0)

def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_rating(rating, expected, actual, k=K_BASE):
    return rating + k * (actual - expected)

# --- Tiebreak and set helpers
def equivalent_games(kind, a, b):
    """Return (A_eq, B_eq). For a standalone tiebreak, down-weight points to game-equivalents.
    kind is either 'set' or 'tiebreak'.
    """
    if kind == "tiebreak":
        return a / POINTS_PER_GAME_TIEBREAK, b / POINTS_PER_GAME_TIEBREAK
    return float(a), float(b)

_SET_RE = re.compile(r"^(\d+)-(\d+)(?:\[(set|tiebreak)\])?$")

def parse_set_token(tok):
    """Parse tokens like '6-3', '7-6', or '10-7[tiebreak]'.
    Returns (a, b, kind) where kind defaults to 'set' if omitted.
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
    if mode == "singles":
        if player["singles_elo"] > player.get("max_singles_elo", float("-inf")):
            player["max_singles_elo"] = player["singles_elo"]
            player["max_singles_date"] = today
    elif mode == "doubles":
        if player["doubles_elo"] > player.get("max_doubles_elo", float("-inf")):
            player["max_doubles_elo"] = player["doubles_elo"]
            player["max_doubles_date"] = today

def record_singles(players, name_a, name_b, games_a, games_b, kind="set"):
    ensure_player(players, name_a)
    ensure_player(players, name_b)
    p_a = players[name_a]
    p_b = players[name_b]
    # Compute expected
    exp_a = expected_score(p_a["singles_elo"], p_b["singles_elo"])
    exp_b = 1 - exp_a
    # Down-weight tiebreaks by converting points to equivalent games
    A_eq, B_eq = equivalent_games(kind, games_a, games_b)
    total = A_eq + B_eq
    act_a = A_eq / total if total else 0.5
    act_b = 1 - act_a
    # Margin-of-victory multiplier (same for both sides to keep zero-sum)
    k_eff = K_BASE * mov_multiplier(act_a)
    # If this token is a standalone tiebreak, scale K by TB length vs a full set
    if kind == "tiebreak":
        eq_total = A_eq + B_eq  # already in game-equivalents via POINTS_PER_GAME_TIEBREAK
        tb_fraction = max(TB_MIN_FRACTION, min(TB_MAX_FRACTION, eq_total / AVG_GAMES_PER_SET))
        k_eff *= tb_fraction
    # Update ratings
    p_a["singles_elo"] = update_rating(p_a["singles_elo"], exp_a, act_a, k=k_eff)
    p_b["singles_elo"] = update_rating(p_b["singles_elo"], exp_b, act_b, k=k_eff)
    # Update last match date
    today = str(date.today())
    p_a["last_match_date"] = today
    p_b["last_match_date"] = today
    maybe_update_peak(p_a, "singles", today)
    maybe_update_peak(p_b, "singles", today)

def record_doubles(players, team_a, team_b, games_a, games_b, kind="set"):
    # team_a and team_b are tuples like ("Alice","Bob")
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
    today = str(date.today())
    # Margin-of-victory multiplier for doubles set
    k_eff = K_BASE * mov_multiplier(act_a)
    if kind == "tiebreak":
        eq_total = A_eq + B_eq  # already in game-equivalents
        tb_fraction = max(TB_MIN_FRACTION, min(TB_MAX_FRACTION, eq_total / AVG_GAMES_PER_SET))
        k_eff *= tb_fraction
    # Update each individual
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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tennis Elo Camp CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # record_series_singles
    pss = sub.add_parser("record_series_singles", help="Record a singles match by set wins (e.g. 6-3 7-6 10-8[tiebreak])")
    pss.add_argument("player_a")
    pss.add_argument("player_b")
    pss.add_argument("sets", nargs='+', help="List set scores like 6-3 7-6 10-8[tiebreak]")

    # record_series_doubles
    psd = sub.add_parser("record_series_doubles", help="Record a doubles match by set wins (e.g. 6-3 8-6 7-6[tiebreak])")
    psd.add_argument("team_a", nargs=2, metavar="player")
    psd.add_argument("team_b", nargs=2, metavar="player")
    psd.add_argument("sets", nargs='+', help="List set scores like 6-3 8-6 7-6[tiebreak]")

    # leaderboard
    pl = sub.add_parser("leaderboard", help="Show leaderboard")
    pl.add_argument("--mode", choices=["singles", "doubles"], default="singles")
    pl.add_argument("--top", type=int, default=10)

    # add_player
    pa = sub.add_parser("add_player", help="Add a player with a set rating")
    pa.add_argument("name", help="Player name")
    pa.add_argument("--singles_elo", type=float, default=1000, help="Initial singles Elo rating")
    pa.add_argument("--doubles_elo", type=float, default=1000, help="Initial doubles Elo rating")

    # show_player
    pshow = sub.add_parser("show_player", help="Show a player's current and peak Elo")
    pshow.add_argument("name", help="Player name")

    args = parser.parse_args()
    players = load_players()

    if args.command == "record_series_singles":
        sets_logged, winner = record_series_singles(players, args.player_a, args.player_b, args.sets)
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "singles_series",
            "players": [args.player_a, args.player_b],
            "sets": sets_logged,
            "winner": winner
        })
        save_history(history)
        save_players(players)
        if winner is None:
            print(f"Recorded singles series for {args.player_a} vs {args.player_b} ({len(sets_logged)} sets) — tie. No match bonus applied.")
        else:
            print(f"Recorded singles series for {args.player_a} vs {args.player_b} ({len(sets_logged)} sets), winner {winner}.")

    elif args.command == "record_series_doubles":
        ta = tuple(args.team_a); tb = tuple(args.team_b)
        sets_logged, winner = record_series_doubles(players, ta, tb, args.sets)
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "doubles_series",
            "teams": [list(ta), list(tb)],
            "sets": sets_logged,
            "winner": winner
        })
        save_history(history)
        save_players(players)
        if winner is None:
            print(f"Recorded doubles series for {args.team_a} vs {args.team_b} ({len(sets_logged)} sets) — tie. No match bonus applied.")
        else:
            print(f"Recorded doubles series for {args.team_a} vs {args.team_b} ({len(sets_logged)} sets), winner {winner}.")

    elif args.command == "leaderboard":
        # sort and display
        key = "singles_elo" if args.mode == "singles" else "doubles_elo"
        sorted_players = sorted(players.items(), key=lambda kv: kv[1][key], reverse=True)[: args.top]
        print(f"{args.mode.title()} Leaderboard:")
        for name, data in sorted_players:
            print(f"{name}: {data[key]:.1f}")

    elif args.command == "add_player":
        try:
            add_player(players, args.name, args.singles_elo, args.doubles_elo)
            save_players(players)
            print(f"Added player {args.name} with singles Elo {args.singles_elo} and doubles Elo {args.doubles_elo}")
        except ValueError as e:
            print(e)

    elif args.command == "show_player":
        if args.name in players:
            p = players[args.name]
            print(f"{args.name}:")
            print(f"  Singles Elo: {p['singles_elo']:.1f} (peak {p.get('max_singles_elo', p['singles_elo']):.1f} on {p.get('max_singles_date', '-')})")
            print(f"  Doubles Elo: {p['doubles_elo']:.1f} (peak {p.get('max_doubles_elo', p['doubles_elo']):.1f} on {p.get('max_doubles_date', '-')})")
        else:
            print(f"Player '{args.name}' not found.")