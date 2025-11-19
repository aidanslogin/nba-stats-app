"""Player statistics module - reads from cached data"""

import json
import os
import glob
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog

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

def calculate_trimmed_mean(values):
    """
    Remove highest and lowest value, return average of remaining values.
    
    Args:
        values (list): List of numeric values
    
    Returns:
        float: Trimmed mean
    """
    if len(values) < 3:
        return np.mean(values) if values else 0
    
    # Remove min and max, then average the rest
    trimmed = [v for v in values if v != min(values) and v != max(values)]
    
    # If we removed duplicates, just remove one min and one max
    if len(trimmed) < len(values) - 2:
        sorted_vals = sorted(values)
        trimmed = sorted_vals[1:-1]  # Remove first (min) and last (max)
    
    return np.mean(trimmed) if trimmed else 0

def get_player_stats(player_id, season="2025-26"):
    """
    Get player season statistics from cached data and live game logs.
    
    Args:
        player_id (str): The ID of the player
        season (str): Season in format "2025-26"
    
    Returns:
        dict: Dictionary containing season averages and trimmed last 7
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
            'spg': season_stats.get('STL', 0) / games if games > 0 else 0,
            'bpg': season_stats.get('BLK', 0) / games if games > 0 else 0,
            'topg': season_stats.get('TOV', 0) / games if games > 0 else 0,
            'fg3m': season_stats.get('FG3M', 0) / games if games > 0 else 0,
            'fg_pct': season_stats.get('FG_PCT', 0),
            'ft_pct': season_stats.get('FT_PCT', 0),
            'minutes': season_stats.get('MIN', 0) / games if games > 0 else 0
        }
        
        # Fetch last 7 games from NBA API
        try:
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
            games_df = gamelog.get_data_frames()[0].head(7)
            
            if len(games_df) >= 3:
                # Calculate trimmed means (remove highest and lowest)
                trimmed_7_stats = {
                    'games': len(games_df),
                    'ppg': calculate_trimmed_mean(games_df['PTS'].tolist()),
                    'rpg': calculate_trimmed_mean(games_df['REB'].tolist()),
                    'apg': calculate_trimmed_mean(games_df['AST'].tolist()),
                    'spg': calculate_trimmed_mean(games_df['STL'].tolist()),
                    'bpg': calculate_trimmed_mean(games_df['BLK'].tolist()),
                    'topg': calculate_trimmed_mean(games_df['TOV'].tolist()),
                    'fg3m': calculate_trimmed_mean(games_df['FG3M'].tolist()),
                    'fg_pct': calculate_trimmed_mean(games_df['FG_PCT'].tolist()),
                    'ft_pct': calculate_trimmed_mean(games_df['FT_PCT'].tolist()),
                    'minutes': calculate_trimmed_mean(games_df['MIN'].tolist())
                }
                
                # Create dataframe with last 7 games
                last_7_games = games_df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 
                                          'STL', 'BLK', 'TOV', 'FG3M', 'FG_PCT', 
                                          'FT_PCT', 'MIN']].copy()
            else:
                # Not enough games, use season averages
                trimmed_7_stats = season_avg.copy()
                last_7_games = pd.DataFrame([{
                    'GAME_DATE': 'Season Average',
                    'MATCHUP': f"{player_name} - {season}",
                    'PTS': season_avg['ppg'],
                    'REB': season_avg['rpg'],
                    'AST': season_avg['apg'],
                    'STL': season_avg['spg'],
                    'BLK': season_avg['bpg'],
                    'TOV': season_avg['topg'],
                    'FG3M': season_avg['fg3m'],
                    'FG_PCT': season_avg['fg_pct'],
                    'FT_PCT': season_avg['ft_pct'],
                    'MIN': season_avg['minutes']
                }])
        
        except Exception as e:
            print(f"Error fetching game logs: {str(e)}")
            # Fall back to season averages
            trimmed_7_stats = season_avg.copy()
            last_7_games = pd.DataFrame([{
                'GAME_DATE': 'Season Average',
                'MATCHUP': f"{player_name} - {season}",
                'PTS': season_avg['ppg'],
                'REB': season_avg['rpg'],
                'AST': season_avg['apg'],
                'STL': season_avg['spg'],
                'BLK': season_avg['bpg'],
                'TOV': season_avg['topg'],
                'FG3M': season_avg['fg3m'],
                'FG_PCT': season_avg['fg_pct'],
                'FT_PCT': season_avg['ft_pct'],
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
