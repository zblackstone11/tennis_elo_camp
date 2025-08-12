#!/usr/bin/env bash
set -e

# 8/12 Match Results

# Doubles
python3 elo_camp.py record_series_doubles Cadie Jack Cooper Harvey 6-3
python3 elo_camp.py record_series_doubles Owen Spencer Rhys Devin 6-4
python3 elo_camp.py record_series_doubles Liam Cadie Cooper Jack 6-4
python3 elo_camp.py record_series_doubles Harvey Spencer Lucas Owen 6-2

# Singles
python3 elo_camp.py record_series_singles Liam Lucas 6-3
python3 elo_camp.py record_series_singles Devin Rhys 1-6

# Run with command bash matches_2025-08-12.sh