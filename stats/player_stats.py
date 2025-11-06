"""Player statistics module - reads from cached data"""

import json
import os
import glob
import pandas as pd
import numpy as np

CACHE_DIR = "cached_data/player_stats"


def find_player_cache_file(player_id):
    """
    Find the cached JSON file for a player by ID.
    
    Args:
        player_id (str): The player ID to search for
    
    Returns:
        str: Path to the cache file, or None if not found
    """
    # Search for file starting with player_id
    pattern = os.path.join(CACHE_DIR, f"{player_id}_*.json")
    files = glob.glob(pattern)
    
    if files:
        return files[0]
    return None


def get_player_stats(player_id, season="2025-26"):
    """
    Get player season statistics from cached data.
    
    Args:
        player_id (str): The ID of the player
        season (str): Season in format "2025-26"
    
    Returns:
        dict: Dictionary containing season averages
        None: If player data not found in cache
    """
    try:
        # Find the player's cached file
        cache_file = find_player_cache_file(player_id)
        
        if not cache_file:
            print(f"Player {player_id} not found in cache")
            return None
        
        # Load cached data
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        
        player_name = cached['player_name']
        data = cached['data']
        
        # Get season totals for regular season
        season_data = data.get('SeasonTotalsRegularSeason', [])
        
        if not season_data:
            print(f"No season data for {player_name}")
            return None
        
        # Filter for the current season
        season_stats = None
        for stat in season_data:
            stat_season = stat.get('SEASON_ID', '')
            if season in stat_season:
                season_stats = stat
                break
        
        if not season_stats:
            print(f"No stats for {player_name} in {season}")
            return None
        
        # Extract stats from the season totals
        games = season_stats.get('GP', 0)
        
        if games == 0:
            return None
        
        # Calculate per-game averages from season totals
        season_avg = {
            'games': games,
            'ppg': season_stats.get('PTS', 0) / games if games > 0 else 0,
            'rpg': season_stats.get('REB', 0) / games if games > 0 else 0,
            'apg': season_stats.get('AST', 0) / games if games > 0 else 0,
            'fg3m': season_stats.get('FG3M', 0) / games if games > 0 else 0,
            'fg_pct': season_stats.get('FG_PCT', 0),
            'minutes': season_stats.get('MIN', 0) / games if games > 0 else 0
        }
        
        # Since we don't have game-by-game data cached, use season averages for both
        trimmed_7_stats = season_avg.copy()
        
        # Create a simple dataframe for display
        last_7_games = pd.DataFrame([{
            'GAME_DATE': 'Season Average',
            'MATCHUP': f"{player_name} - {season}",
            'PTS': season_avg['ppg'],
            'REB': season_avg['rpg'],
            'AST': season_avg['apg'],
            'FG3M': season_avg['fg3m'],
            'MIN': season_avg['minutes']
        }])
        
        return {
            'season': season_avg,
            'trimmed_7': trimmed_7_stats,
            'last_7_games': last_7_games
        }
        
    except Exception as e:
        print(f"Error fetching player stats: {str(e)}")
        return None
