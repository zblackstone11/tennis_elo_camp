import json
from datetime import date
import os
from datetime import datetime

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

def ensure_player(players, name):
    if name not in players:
        players[name] = {
            "singles_elo": 1000,
            "doubles_elo": 1000,
            "last_match_date": str(date.today())
        }
    return players[name]

K_FACTOR = 36

def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_rating(rating, expected, actual, k=K_FACTOR):
    return rating + k * (actual - expected)

def record_singles(players, name_a, name_b, games_a, games_b):
    ensure_player(players, name_a)
    ensure_player(players, name_b)
    p_a = players[name_a]
    p_b = players[name_b]
    # Compute expected
    exp_a = expected_score(p_a["singles_elo"], p_b["singles_elo"])
    exp_b = 1 - exp_a
    # Compute actual score
    total = games_a + games_b
    act_a = games_a / total if total else 0.5
    act_b = games_b / total if total else 0.5
    # Update ratings
    p_a["singles_elo"] = update_rating(p_a["singles_elo"], exp_a, act_a)
    p_b["singles_elo"] = update_rating(p_b["singles_elo"], exp_b, act_b)
    # Update last match date
    today = str(date.today())
    p_a["last_match_date"] = today
    p_b["last_match_date"] = today

def record_doubles(players, team_a, team_b, games_a, games_b):
    # team_a and team_b are tuples like ("Alice","Bob")
    for name in team_a + team_b:
        ensure_player(players, name)
    # Compute team average ratings
    ra = sum(players[n]["doubles_elo"] for n in team_a) / 2
    rb = sum(players[n]["doubles_elo"] for n in team_b) / 2
    exp_a = expected_score(ra, rb)
    exp_b = 1 - exp_a
    total = games_a + games_b
    act_a = games_a / total if total else 0.5
    act_b = games_b / total if total else 0.5
    today = str(date.today())
    # Update each individual
    for name in team_a:
        old = players[name]["doubles_elo"]
        players[name]["doubles_elo"] = update_rating(old, exp_a, act_a)
        players[name]["last_match_date"] = today
    for name in team_b:
        old = players[name]["doubles_elo"]
        players[name]["doubles_elo"] = update_rating(old, exp_b, act_b)
        players[name]["last_match_date"] = today

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tennis Elo Camp CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # record_singles
    ps = sub.add_parser("record_singles", help="Record singles match")
    ps.add_argument("player_a")
    ps.add_argument("player_b")
    ps.add_argument("games_a", type=int)
    ps.add_argument("games_b", type=int)
    ps.add_argument("--kind", choices=["set", "tiebreak", "super_tiebreak"], default="set",
                    help="Type of match (affects logging only)")

    # record_doubles
    pd = sub.add_parser("record_doubles", help="Record doubles match")
    pd.add_argument("team_a", nargs=2, metavar="player")
    pd.add_argument("team_b", nargs=2, metavar="player")
    pd.add_argument("games_a", type=int)
    pd.add_argument("games_b", type=int)
    pd.add_argument("--kind", choices=["set", "tiebreak", "super_tiebreak"], default="set",
                    help="Type of match (affects logging only)")

    # leaderboard
    pl = sub.add_parser("leaderboard", help="Show leaderboard")
    pl.add_argument("--mode", choices=["singles", "doubles"], default="singles")
    pl.add_argument("--top", type=int, default=10)

    args = parser.parse_args()
    players = load_players()

    if args.command == "record_singles":
        record_singles(players, args.player_a, args.player_b, args.games_a, args.games_b)
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "singles",
            "players": [args.player_a, args.player_b],
            "games": [args.games_a, args.games_b],
            "kind": args.kind
        })
        save_history(history)
        save_players(players)
        print(f"Updated singles Elo for {args.player_a} vs {args.player_b}")

    elif args.command == "record_doubles":
        record_doubles(players, tuple(args.team_a), tuple(args.team_b), args.games_a, args.games_b)
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "doubles",
            "teams": [list(args.team_a), list(args.team_b)],
            "games": [args.games_a, args.games_b],
            "kind": args.kind
        })
        save_history(history)
        save_players(players)
        print(f"Updated doubles Elo for {args.team_a} vs {args.team_b}")

    elif args.command == "leaderboard":
        # sort and display
        key = "singles_elo" if args.mode == "singles" else "doubles_elo"
        sorted_players = sorted(players.items(), key=lambda kv: kv[1][key], reverse=True)[: args.top]
        print(f"{args.mode.title()} Leaderboard:")
        for name, data in sorted_players:
            print(f"{name}: {data[key]:.1f}")