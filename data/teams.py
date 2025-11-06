import json
import os

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cached_data", "teams.json")

def load_cached_teams_raw():
    try:
        if not os.path.exists(CACHE_FILE):
            print(f"Warning: Cache file not found at {CACHE_FILE}")
            return None
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading cached teams: {str(e)}")
        return None

def get_all_teams():
    cached = load_cached_teams_raw()
    if cached is None:
        return []
    team_data = cached.get("data", {})
    if "LeagueDashTeamStats" in team_data:
        return team_data["LeagueDashTeamStats"]
    return team_data

def get_cache_timestamp():
    cached = load_cached_teams_raw()
    if cached is None:
        return "Unknown"
    return cached.get("last_updated", "Unknown")

def get_cache_season():
    cached = load_cached_teams_raw()
    if cached is None:
        return "Unknown"
    return cached.get("season", "Unknown")
