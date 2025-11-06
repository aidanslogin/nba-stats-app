import json
import os

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cached_data", "players.json")

def load_cached_players_raw():
    try:
        if not os.path.exists(CACHE_FILE):
            print(f"Warning: Cache file not found at {CACHE_FILE}")
            return None
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading cached players: {str(e)}")
        return None

def get_all_players():
    cached = load_cached_players_raw()
    if cached is None:
        return []
    player_data = cached.get("data", {})
    if "CommonAllPlayers" in player_data:
        return player_data["CommonAllPlayers"]
    return player_data

def get_cache_timestamp():
    cached = load_cached_players_raw()
    if cached is None:
        return "Unknown"
    return cached.get("last_updated", "Unknown")

def get_cache_season():
    cached = load_cached_players_raw()
    if cached is None:
        return "Unknown"
    return cached.get("season", "Unknown")
