#!/usr/bin/env bash
set -e

# 8/7 Match Results

# Doubles
python3 elo_camp.py record_series_doubles Spencer Aliza Emma Anderson 1-6 6-2 "6-10[tiebreak]"
python3 elo_camp.py record_series_doubles Jill Rhys Liam Jack_L 1-6 6-3 "10-5[tiebreak]"

# Singles
python3 elo_camp.py record_series_singles Jack_W Aaron 3-6 0-6
python3 elo_camp.py record_series_singles Ishan Rishaan 4-6 6-2 "5-7[tiebreak]"
python3 elo_camp.py record_series_singles Emma Anderson 6-2
python3 elo_camp.py record_series_singles Noah Jack_L 6-2 6-4

# Doubles
python3 elo_camp.py record_series_doubles Rishaan Ben Aaron Jack_W 6-2 6-3