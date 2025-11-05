# filepath: /Users/aidan/nba-stats-app/data/teams.py
from nba_api.stats.static import teams

def get_all_teams():
    return teams.get_teams()