

#!/usr/bin/env bash
set -e
# 8/15 Match Results

python3 elo_camp.py record_series_singles Cadie Harvey 6-2
python3 elo_camp.py record_series_doubles Liam Rishaan Jack Owen 6-4
python3 elo_camp.py record_series_singles Devin Spencer 6-4
python3 elo_camp.py record_series_singles Rhys Lucas 6-1
python3 elo_camp.py record_series_singles Jack Liam 6-2
python3 elo_camp.py record_series_singles Lucas Rishaan 6-3
python3 elo_camp.py record_series_doubles Spencer Cadie Rhys Devin 7-5
python3 elo_camp.py record_series_singles Harvey Owen 6-2

# Tiebreaks
python3 elo_camp.py record_series_singles Liam Owen "7-5[tiebreak]"
python3 elo_camp.py record_series_singles Harvey Rishaan "10-8[tiebreak]"
python3 elo_camp.py record_series_singles Jack Lucas "7-5[tiebreak]"
python3 elo_camp.py record_series_singles Cadie Devin "7-3[tiebreak]"
python3 elo_camp.py record_series_singles Harvey Liam "8-6[tiebreak]"
python3 elo_camp.py record_series_singles Spencer Rhys "7-2[tiebreak]"
python3 elo_camp.py record_series_singles Rishaan Owen "7-5[tiebreak]"
python3 elo_camp.py record_series_singles Jack Spencer "7-3[tiebreak]"
python3 elo_camp.py record_series_singles Cadie Harvey "7-2[tiebreak]"
python3 elo_camp.py record_series_singles Cadie Jack "7-5[tiebreak]"