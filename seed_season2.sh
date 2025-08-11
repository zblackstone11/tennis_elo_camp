#!/usr/bin/env bash
set -e

# Season 2 roster seed (same singles/doubles Elo for now) 8/11-8/15

python3 elo_camp.py add_player Cooper   --singles_elo 1200 --doubles_elo 1200
python3 elo_camp.py add_player Jack     --singles_elo 1200 --doubles_elo 1200
python3 elo_camp.py add_player Devin    --singles_elo 1000 --doubles_elo 1000
python3 elo_camp.py add_player Owen     --singles_elo  900 --doubles_elo  900
python3 elo_camp.py add_player Rishaan  --singles_elo 1000 --doubles_elo 1000
python3 elo_camp.py add_player Rhys     --singles_elo 1100 --doubles_elo 1100
python3 elo_camp.py add_player Liam     --singles_elo 1200 --doubles_elo 1200
python3 elo_camp.py add_player Harvey   --singles_elo 1100 --doubles_elo 1100
python3 elo_camp.py add_player Spencer  --singles_elo 1100 --doubles_elo 1100
python3 elo_camp.py add_player Lucas    --singles_elo 1200 --doubles_elo 1200
python3 elo_camp.py add_player Cadie    --singles_elo 1500 --doubles_elo 1500