#!/usr/bin/env bash
set -e

# 8/18 Match Results

# --- New player (safe to run; will error if already exists) ---
python3 elo_camp.py add_player Wes --singles_elo 1100 --doubles_elo 1100

# --- Singles ---
python3 elo_camp.py record_series_singles Cadie Wes 6-1
python3 elo_camp.py record_series_singles Cooper Rhys 6-4
python3 elo_camp.py record_series_singles Harvey Jack 6-1
python3 elo_camp.py record_series_singles Liam Spencer 1-6

# --- Doubles (regular sets) ---
python3 elo_camp.py record_series_doubles Cadie Liam Wes Spencer 6-2
python3 elo_camp.py record_series_doubles Harvey Rhys Cooper Jack 1-6

# --- Doubles (tiebreak-only series) ---
python3 elo_camp.py record_series_doubles Spencer Cooper Wes Harvey "7-5[tiebreak]"
python3 elo_camp.py record_series_doubles Cadie Liam Rhys Jack "5-7[tiebreak]"
python3 elo_camp.py record_series_doubles Spencer Cooper Jack Rhys "7-5[tiebreak]"
python3 elo_camp.py record_series_doubles Cadie Liam Wes Harvey "5-7[tiebreak]"