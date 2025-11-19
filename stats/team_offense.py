"""Team offensive statistics module"""

from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import numpy as np

def get_team_offense_stats(team_id, season="2023-24"):
    """
    Fetches comprehensive offensive statistics for a team.
    
    Args:
        team_id (str): The ID of the team
        season (str): Season in format "2023-24"
    
    Returns:
        dict: Dictionary containing offensive stats
    """
    try:
        # Get team's games
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable=season,
            season_type_nullable='Regular Season'
        )
        
        games_df = gamefinder.get_data_frames()[0]
        
        if games_df.empty:
            return None
        
        # Use games_df directly - it already has all offensive stats
        # No need to rebuild like we do for defense (which needs opponent matching)
        
        # Calculate season averages directly from games_df
        season_stats = {
            'games': len(games_df),
            'ppg': games_df['PTS'].mean(),
            'fg_pct': games_df['FG_PCT'].mean(),
            'fgm': games_df['FGM'].mean(),
            'fga': games_df['FGA'].mean(),
            'fg3_pct': games_df['FG3_PCT'].mean(),
            'fg3m': games_df['FG3M'].mean(),
            'fg3a': games_df['FG3A'].mean(),
            'ft_pct': games_df['FT_PCT'].mean(),
            'ftm': games_df['FTM'].mean(),
            'fta': games_df['FTA'].mean(),
            'ast': games_df['AST'].mean(),
            'tov': games_df['TOV'].mean(),
            'oreb': games_df['OREB'].mean(),
            'dreb': games_df['DREB'].mean(),
            'reb': games_df['REB'].mean()
        }
        
        # Calculate assist-to-turnover ratio
        season_stats['ast_tov_ratio'] = season_stats['ast'] / season_stats['tov'] if season_stats['tov'] > 0 else 0
        
        # Get last 7 games
        last_7 = games_df.head(min(7, len(games_df)))
        
        # Calculate trimmed last 7 (remove highest and lowest for PPG)
        if len(last_7) >= 3:
            pts_sorted = np.sort(last_7['PTS'].values)
            trimmed_ppg = np.mean(pts_sorted[1:-1])
        else:
            trimmed_ppg = last_7['PTS'].mean()
        
        trimmed_7 = {
            'games': len(last_7),
            'ppg': trimmed_ppg,
            'fg_pct': last_7['FG_PCT'].mean(),
            'fgm': last_7['FGM'].mean(),
            'fga': last_7['FGA'].mean(),
            'fg3_pct': last_7['FG3_PCT'].mean(),
            'fg3m': last_7['FG3M'].mean(),
            'fg3a': last_7['FG3A'].mean(),
            'ft_pct': last_7['FT_PCT'].mean(),
            'ftm': last_7['FTM'].mean(),
            'fta': last_7['FTA'].mean(),
            'ast': last_7['AST'].mean(),
            'tov': last_7['TOV'].mean(),
            'oreb': last_7['OREB'].mean(),
            'dreb': last_7['DREB'].mean(),
            'reb': last_7['REB'].mean()
        }
        
        # Calculate assist-to-turnover ratio for recent form
        trimmed_7['ast_tov_ratio'] = trimmed_7['ast'] / trimmed_7['tov'] if trimmed_7['tov'] > 0 else 0
        
        # Format display dataframe
        display_cols = ['GAME_DATE', 'MATCHUP', 'WL', 'PTS']
        display_df = last_7[display_cols].copy()
        display_df['FG%'] = (last_7['FG_PCT'] * 100).round(1)
        display_df['3PM'] = last_7['FG3M']
        display_df['3PT%'] = (last_7['FG3_PCT'] * 100).round(1)
        display_df['AST'] = last_7['AST']
        display_df['TOV'] = last_7['TOV']
        display_df['REB'] = last_7['REB']
        
        return {
            'season': season_stats,
            'trimmed_7': trimmed_7,
            'last_7_games': display_df.head(7)
        }
        
    except Exception as e:
        print(f"Error fetching team offense: {e}")
        import traceback
        traceback.print_exc()
        return None
