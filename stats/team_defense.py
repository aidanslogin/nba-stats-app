"""Team defensive statistics module"""

from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import numpy as np


def get_team_defense_stats(team_id, season="2023-24"):
    """
    Fetches defensive statistics for a team.
    
    Args:
        team_id (str): The ID of the team
        season (str): Season in format "2023-24"
    
    Returns:
        dict: Dictionary containing defensive stats
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
        
        # Calculate opponent points
        if 'PLUS_MINUS' in games_df.columns:
            games_df['OPP_PTS_CALC'] = games_df['PTS'] - games_df['PLUS_MINUS']
            opp_pts_col = 'OPP_PTS_CALC'
        elif 'PTS_OPP' in games_df.columns:
            opp_pts_col = 'PTS_OPP'
        else:
            return None
        
        season_stats = {
            'games': len(games_df),
            'opp_ppg': games_df[opp_pts_col].mean()
        }
        
        last_7 = games_df.head(min(7, len(games_df)))
        
        if len(last_7) >= 3:
            opp_pts_sorted = np.sort(last_7[opp_pts_col].values)
            trimmed_7 = {
                'opp_ppg': np.mean(opp_pts_sorted[1:-1])
            }
        else:
            trimmed_7 = {
                'opp_ppg': last_7[opp_pts_col].mean()
            }
        
        display_cols = ['GAME_DATE', 'MATCHUP', 'WL'] if 'WL' in last_7.columns else ['GAME_DATE', 'MATCHUP']
        display_cols.extend(['PTS', opp_pts_col])
        
        return {
            'season': season_stats,
            'trimmed_7': trimmed_7,
            'last_7_games': last_7[display_cols].head(7)
        }
        
    except Exception as e:
        print(f"Error fetching team defense: {e}")
        return None
