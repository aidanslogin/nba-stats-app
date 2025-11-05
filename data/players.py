# filepath: /Users/aidan/nba-stats-app/data/players.py
from nba_api.stats.static import players

def get_all_players():
    return players.get_active_players()