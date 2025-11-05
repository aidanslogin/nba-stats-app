"""Player statistics module"""

from nba_api.stats.endpoints import playergamelog
import pandas as pd
import numpy as np


def get_player_stats(player_id, season="2023-24"):
    """
    Fetches player offensive statistics.
    
    Args:
        player_id (str): The ID of the player
        season (str): Season in format "2023-24"
    
    Returns:
        dict: Dictionary containing season averages and trimmed last 7 games
    """
    try:
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            season_type_all_star='Regular Season'
        )
        
        games_df = game_log.get_data_frames()[0]
        
        if games_df.empty:
            return None
        
        season_stats = {
            'games': len(games_df),
            'ppg': games_df['PTS'].mean(),
            'rpg': games_df['REB'].mean(),
            'apg': games_df['AST'].mean(),
            'fg3m': games_df['FG3M'].mean(),
            'fg_pct': games_df['FG_PCT'].mean(),
            'minutes': games_df['MIN'].mean()
        }
        
        last_7 = games_df.head(min(7, len(games_df)))
        
        if len(last_7) >= 3:
            trimmed_stats = {}
            for stat in ['PTS', 'REB', 'AST', 'FG3M', 'FG_PCT', 'MIN']:
                values = last_7[stat].values
                sorted_vals = np.sort(values)
                trimmed_vals = sorted_vals[1:-1]
                trimmed_stats[stat] = np.mean(trimmed_vals)
            
            trimmed_7_stats = {
                'ppg': trimmed_stats['PTS'],
                'rpg': trimmed_stats['REB'],
                'apg': trimmed_stats['AST'],
                'fg3m': trimmed_stats['FG3M'],
                'fg_pct': trimmed_stats['FG_PCT'],
                'minutes': trimmed_stats['MIN']
            }
        else:
            trimmed_7_stats = {
                'ppg': last_7['PTS'].mean(),
                'rpg': last_7['REB'].mean(),
                'apg': last_7['AST'].mean(),
                'fg3m': last_7['FG3M'].mean(),
                'fg_pct': last_7['FG_PCT'].mean(),
                'minutes': last_7['MIN'].mean()
            }
        
        return {
            'season': season_stats,
            'trimmed_7': trimmed_7_stats,
            'last_7_games': last_7[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'FG3M', 'MIN']].head(7)
        }
        
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return None
