"""Team offensive statistics module"""

from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import numpy as np


def get_team_offense_stats(team_id, season="2023-24"):
    """
    Fetches offensive statistics for a team.
    
    Args:
        team_id (str): The ID of the team
        season (str): Season in format "2023-24"
    
    Returns:
        dict: Dictionary containing season averages and trimmed last 7 games
              Returns None if no data available
    """
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable=season,
            season_type_nullable='Regular Season'
        )
        
        games_df = gamefinder.get_data_frames()[0]
        
        if games_df.empty:
            return None
        
        # Season averages
        season_stats = {
            'games': len(games_df),
            'ppg': games_df['PTS'].mean(),
            'fg_pct': games_df['FG_PCT'].mean(),
            'fg3_pct': games_df['FG3_PCT'].mean(),
            'fg3m': games_df['FG3M'].mean(),
            'stl': games_df['STL'].mean() if 'STL' in games_df.columns else None,
            'blk': games_df['BLK'].mean() if 'BLK' in games_df.columns else None,
            'reb': games_df['REB'].mean() if 'REB' in games_df.columns else None
        }
        
        # Trimmed last 7 (removes highest and lowest)
        last_7 = games_df.head(min(7, len(games_df)))
        
        if len(last_7) >= 3:
            pts_sorted = np.sort(last_7['PTS'].values)
            fg_pct_sorted = np.sort(last_7['FG_PCT'].values)
            fg3_pct_sorted = np.sort(last_7['FG3_PCT'].values)
            fg3m_sorted = np.sort(last_7['FG3M'].values)
            
            trimmed_7 = {
                'ppg': np.mean(pts_sorted[1:-1]),
                'fg_pct': np.mean(fg_pct_sorted[1:-1]),
                'fg3_pct': np.mean(fg3_pct_sorted[1:-1]),
                'fg3m': np.mean(fg3m_sorted[1:-1])
            }
        else:
            trimmed_7 = {
                'ppg': last_7['PTS'].mean(),
                'fg_pct': last_7['FG_PCT'].mean(),
                'fg3_pct': last_7['FG3_PCT'].mean(),
                'fg3m': last_7['FG3M'].mean()
            }
        
        return {
            'season': season_stats,
            'trimmed_7': trimmed_7,
            'last_7_games': last_7[['GAME_DATE', 'MATCHUP', 'WL', 'PTS', 'FG_PCT', 'FG3M']].head(7) if 'WL' in last_7.columns else last_7.head(7)
        }
        
    except Exception as e:
        print(f"Error fetching team offense: {e}")
        return None
