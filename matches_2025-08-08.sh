#!/usr/bin/env bash
set -e

# --- New player ---
python3 elo_camp.py add_player Shreya --singles_elo 900 --doubles_elo 900

# --- Singles ---
python3 elo_camp.py record_series_singles Cadie Ben 7-6 6-2
python3 elo_camp.py record_series_singles Cadie Noah 6-1 6-0
python3 elo_camp.py record_series_singles Jill Rhys 6-0
python3 elo_camp.py record_series_singles Aaron Ishan 6-0
python3 elo_camp.py record_series_singles Jack_W Shreya 6-0
python3 elo_camp.py record_series_singles Anderson Aliza 2-6
python3 elo_camp.py record_series_singles Ben Harvey 6-1
python3 elo_camp.py record_series_singles Shreya Spencer 1-3

# --- Doubles ---
python3 elo_camp.py record_series_doubles Ben Rishaan Cadie Cooper 1-6 1-6
python3 elo_camp.py record_series_doubles Harvey Spencer Noah Jack_L 7-6
python3 elo_camp.py record_series_doubles Jill Ishan Rhys Aaron 7-5
python3 elo_camp.py record_series_doubles Shreya Aliza Liam Anderson 6-7
python3 elo_camp.py record_series_doubles Noah Jack_L Cadie Cooper 4-2
python3 elo_camp.py record_series_doubles Liam Jill Rhys Aaron 1-4