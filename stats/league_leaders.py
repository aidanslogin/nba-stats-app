"""League leaders module - top 30 based on last 7 games from cached data"""

import json
import os
import glob
import pandas as pd
import numpy as np

CACHE_DIR = "cached_data/player_stats"

def calculate_trimmed_mean(values):
    """Remove highest and lowest value, return average of remaining values."""
    if len(values) < 3:
        return np.mean(values) if values else 0
    sorted_vals = sorted(values)
    trimmed = sorted_vals[1:-1]
    return np.mean(trimmed) if trimmed else 0

def get_player_last_7_from_cache(cache_file):
    """
    Get a player's last 7 games stats from cached file.
    
    Returns:
        dict: Player's recent form stats or None if not enough games
    """
    try:
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        
        player_name = cached['player_name']
        team_abbr = cached.get('team_abbreviation', 'FA')
        
        # Get game log from cached data
        game_log_data = cached.get('game_log', {})
        game_log = game_log_data.get('PlayerGameLog', [])
        
        if not game_log or len(game_log) < 3:
            return None
        
        # Convert to DataFrame
        games_df = pd.DataFrame(game_log)
        
        # Filter to games where player actually played
        games_played = games_df[games_df['MIN'].notna() & (games_df['MIN'] > 0)]
        
        if len(games_played) < 3:
            return None
        
        # Get last 7 games
        last_7 = games_played.head(7)
        
        # Calculate trimmed stats
        return {
            'PLAYER': player_name,
            'TEAM': team_abbr,
            'GP': len(last_7),
            'PTS': calculate_trimmed_mean(last_7['PTS'].tolist()),
            'REB': calculate_trimmed_mean(last_7['REB'].tolist()),
            'AST': calculate_trimmed_mean(last_7['AST'].tolist()),
            'STL': calculate_trimmed_mean(last_7['STL'].tolist()),
            'BLK': calculate_trimmed_mean(last_7['BLK'].tolist()),
            'FG3M': calculate_trimmed_mean(last_7['FG3M'].tolist()),
            'FG_PCT': calculate_trimmed_mean(last_7['FG_PCT'].tolist()),
            'MIN': calculate_trimmed_mean(last_7['MIN'].tolist())
        }
        
    except Exception as e:
        print(f"Error reading cache file {cache_file}: {e}")
        return None

def get_top_30_by_category():
    """
    Calculate top 30 players in each category based on last 7 games from cached data.
    
    Returns:
        dict: Dictionary with top 30 dataframes for each category
    """
    print("Reading cached player stats...")
    
    # Get all cached player files
    cache_pattern = os.path.join(CACHE_DIR, "*.json")
    cache_files = glob.glob(cache_pattern)
    
    print(f"Found {len(cache_files)} cached player files")
    
    recent_stats = []
    
    # Process each cached file
    for i, cache_file in enumerate(cache_files):
        stats = get_player_last_7_from_cache(cache_file)
        
        if stats:
            recent_stats.append(stats)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(cache_files)} files...")
    
    print(f"Successfully processed {len(recent_stats)} players with recent games")
    
    if len(recent_stats) == 0:
        print("No player stats found!")
        return {}
    
    # Convert to DataFrame
    df = pd.DataFrame(recent_stats)
    
    # Create leaderboards for each category
    leaderboards = {}
    
    # Points Per Game
    leaderboards['Points Per Game'] = (
        df.nlargest(30, 'PTS')[['PLAYER', 'TEAM', 'GP', 'PTS', 'FG_PCT', 'FG3M']]
        .reset_index(drop=True)
    )
    leaderboards['Points Per Game'].insert(0, 'RANK', range(1, len(leaderboards['Points Per Game']) + 1))
    
    # Rebounds Per Game
    leaderboards['Rebounds Per Game'] = (
        df.nlargest(30, 'REB')[['PLAYER', 'TEAM', 'GP', 'REB', 'MIN']]
        .reset_index(drop=True)
    )
    leaderboards['Rebounds Per Game'].insert(0, 'RANK', range(1, len(leaderboards['Rebounds Per Game']) + 1))
    
    # Assists Per Game
    leaderboards['Assists Per Game'] = (
        df.nlargest(30, 'AST')[['PLAYER', 'TEAM', 'GP', 'AST', 'MIN']]
        .reset_index(drop=True)
    )
    leaderboards['Assists Per Game'].insert(0, 'RANK', range(1, len(leaderboards['Assists Per Game']) + 1))
    
    # 3-Pointers Made
    leaderboards['3-Pointers Made'] = (
        df.nlargest(30, 'FG3M')[['PLAYER', 'TEAM', 'GP', 'FG3M', 'PTS']]
        .reset_index(drop=True)
    )
    leaderboards['3-Pointers Made'].insert(0, 'RANK', range(1, len(leaderboards['3-Pointers Made']) + 1))
    
    # Steals Per Game
    leaderboards['Steals Per Game'] = (
        df.nlargest(30, 'STL')[['PLAYER', 'TEAM', 'GP', 'STL', 'MIN']]
        .reset_index(drop=True)
    )
    leaderboards['Steals Per Game'].insert(0, 'RANK', range(1, len(leaderboards['Steals Per Game']) + 1))
    
    # Blocks Per Game
    leaderboards['Blocks Per Game'] = (
        df.nlargest(30, 'BLK')[['PLAYER', 'TEAM', 'GP', 'BLK', 'MIN']]
        .reset_index(drop=True)
    )
    leaderboards['Blocks Per Game'].insert(0, 'RANK', range(1, len(leaderboards['Blocks Per Game']) + 1))
    
    # Round all numeric columns to 1 decimal
    for name, board in leaderboards.items():
        for col in board.columns:
            if board[col].dtype in ['float64', 'float32']:
                board[col] = board[col].round(1)
    
    return leaderboards
