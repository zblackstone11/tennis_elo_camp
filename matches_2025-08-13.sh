#!/usr/bin/env bash
set -e

# 8/13 Match Results

# Singles
python3 elo_camp.py record_series_singles Jack Spencer 6-1
python3 elo_camp.py record_series_singles Rhys Rishaan 7-5
python3 elo_camp.py record_series_singles Cadie Liam 6-3
python3 elo_camp.py record_series_singles Harvey Lucas 6-3
python3 elo_camp.py record_series_singles Devin Owen 6-4

# Doubles
python3 elo_camp.py record_series_doubles Rhys Rishaan Owen Harvey 7-6

# Run with: bash matches_2025-08-13.sh