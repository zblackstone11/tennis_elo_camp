

#!/usr/bin/env bash
set -e

# 8/14 Match Results

# Doubles
python3 elo_camp.py record_series_doubles Liam Jack Cadie Lucas 4-6
python3 elo_camp.py record_series_doubles Jack Rhys Devin Lucas 5-4
python3 elo_camp.py record_series_doubles Spencer Owen Harvey Rishaan 6-3

# Singles
python3 elo_camp.py record_series_singles Spencer Harvey 4-6
python3 elo_camp.py record_series_singles Rhys Devin 6-2
python3 elo_camp.py record_series_singles Rishaan Owen 6-2
python3 elo_camp.py record_series_singles Cadie Liam "10-4[tiebreak]"
python3 elo_camp.py record_series_singles Spencer Harvey "6-9[tiebreak]"