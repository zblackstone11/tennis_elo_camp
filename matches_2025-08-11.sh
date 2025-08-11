#!/usr/bin/env bash
set -e

# 8/11 Match Results

# Singles
python3 elo_camp.py record_series_singles Liam Spencer 0-6
python3 elo_camp.py record_series_singles Jack_L Cadie 0-6
python3 elo_camp.py record_series_singles Harvey Owen 6-1
python3 elo_camp.py record_series_singles Rhys Lucas 6-3
python3 elo_camp.py record_series_singles Spencer Cooper 6-4
python3 elo_camp.py record_series_singles Devon Rishaan 6-4
python3 elo_camp.py record_series_singles Spencer Lucas 6-2

# Doubles
python3 elo_camp.py record_series_doubles Harvey Liam Jack_L Owen 6-3
python3 elo_camp.py record_series_doubles Devon Cooper Rishaan Rhys 6-4