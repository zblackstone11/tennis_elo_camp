#!/usr/bin/env bash
set -e

# 8/19 Match Results

# --- New players (safe to run once; will error if already exists) ---
python3 elo_camp.py add_player Aliya --singles_elo 1300 --doubles_elo 1200
python3 elo_camp.py add_player Ishaan --singles_elo 1000 --doubles_elo 1000

# --- Singles ---
python3 elo_camp.py record_series_singles Cadie Jack 4-5
python3 elo_camp.py record_series_singles Ishaan Rhys 0-6
python3 elo_camp.py record_series_singles Harvey Rishaan 6-4
python3 elo_camp.py record_series_singles Aliya Cadie 5-4
python3 elo_camp.py record_series_singles Rhys Harvey 5-5
python3 elo_camp.py record_series_singles Ishaan Rishaan 1-6

# --- Doubles ---
python3 elo_camp.py record_series_doubles Liam Aliya Spencer Cooper 2-4
python3 elo_camp.py record_series_doubles Jack Spencer Cooper Liam 6-3
python3 elo_camp.py record_series_doubles Ishaan Harvey Rishaan Rhys 1-6