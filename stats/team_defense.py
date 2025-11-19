"""Team defensive statistics module"""

from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import numpy as np

def get_team_defense_stats(team_id, season="2023-24"):
    """
    Fetches comprehensive defensive statistics for a team.
    
    Args:
        team_id (str): The ID of the team
        season (str): Season in format "2023-24"
    
    Returns:
        dict: Dictionary containing defensive stats
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
        
        # Calculate opponent points
        if 'PLUS_MINUS' in games_df.columns:
            games_df['OPP_PTS'] = games_df['PTS'] - games_df['PLUS_MINUS']
        elif 'PTS_OPP' in games_df.columns:
            games_df['OPP_PTS'] = games_df['PTS_OPP']
        else:
            return None
        
        # Get ALL games for the season (not filtered by team)
        all_gamefinder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable='Regular Season'
        )
        
        all_games_df = all_gamefinder.get_data_frames()[0]
        
        if all_games_df.empty:
            return None
        
        # Build opponent stats by matching game IDs
        opponent_data = []
        
        for idx, game in games_df.iterrows():
            game_id = game['GAME_ID']
            
            # Get both teams' data for this game
            game_matchups = all_games_df[all_games_df['GAME_ID'] == game_id]
            
            # Find opponent (the team that's NOT our team_id)
            opponent = game_matchups[game_matchups['TEAM_ID'] != int(team_id)]
            
            if not opponent.empty:
                opp_game = opponent.iloc[0]
                
                # Safely extract stats with defaults
                opponent_data.append({
                    'GAME_ID': game_id,
                    'GAME_DATE': game['GAME_DATE'],
                    'MATCHUP': game['MATCHUP'],
                    'WL': game.get('WL', 'N/A'),
                    'OPP_PTS': opp_game.get('PTS', 0),
                    'OPP_FGM': opp_game.get('FGM', 0),
                    'OPP_FGA': opp_game.get('FGA', 1),  # Avoid division by zero
                    'OPP_FG3M': opp_game.get('FG3M', 0),
                    'OPP_FG3A': opp_game.get('FG3A', 1),
                    'OPP_FTM': opp_game.get('FTM', 0),
                    'OPP_FTA': opp_game.get('FTA', 1),
                    'OPP_REB': opp_game.get('REB', 0),
                    'OPP_AST': opp_game.get('AST', 0),
                    'OPP_TOV': opp_game.get('TOV', 0),
                    'TEAM_STL': game.get('STL', 0),
                    'TEAM_BLK': game.get('BLK', 0),
                    'TEAM_DREB': game.get('DREB', 0),
                    'TEAM_PF': game.get('PF', 0)
                })
        
        if not opponent_data:
            return None
        
        opp_df = pd.DataFrame(opponent_data)
        
        # Calculate percentages after getting the data
        opp_df['OPP_FG_PCT'] = opp_df['OPP_FGM'] / opp_df['OPP_FGA']
        opp_df['OPP_FG3_PCT'] = opp_df['OPP_FG3M'] / opp_df['OPP_FG3A']
        opp_df['OPP_FT_PCT'] = opp_df['OPP_FTM'] / opp_df['OPP_FTA']
        
        # Replace any inf/nan with 0
        opp_df = opp_df.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Calculate season averages
        season_stats = {
            'games': len(opp_df),
            'opp_ppg': opp_df['OPP_PTS'].mean(),
            'opp_fg_pct': opp_df['OPP_FG_PCT'].mean(),
            'opp_fg3m': opp_df['OPP_FG3M'].mean(),
            'opp_fg3a': opp_df['OPP_FG3A'].mean(),
            'opp_fg3_pct': opp_df['OPP_FG3_PCT'].mean(),
            'opp_ft_pct': opp_df['OPP_FT_PCT'].mean(),
            'opp_reb': opp_df['OPP_REB'].mean(),
            'opp_ast': opp_df['OPP_AST'].mean(),
            'opp_tov': opp_df['OPP_TOV'].mean(),
            'team_stl': opp_df['TEAM_STL'].mean(),
            'team_blk': opp_df['TEAM_BLK'].mean(),
            'team_dreb': opp_df['TEAM_DREB'].mean(),
            'team_pf': opp_df['TEAM_PF'].mean()
        }
        
        # Get last 7 games
        last_7 = opp_df.head(min(7, len(opp_df)))
        
        # Calculate trimmed last 7 (remove highest and lowest for PPG)
        if len(last_7) >= 3:
            opp_pts_sorted = np.sort(last_7['OPP_PTS'].values)
            trimmed_ppg = np.mean(opp_pts_sorted[1:-1])
        else:
            trimmed_ppg = last_7['OPP_PTS'].mean()
        
        trimmed_7 = {
            'games': len(last_7),
            'opp_ppg': trimmed_ppg,
            'opp_fg_pct': last_7['OPP_FG_PCT'].mean(),
            'opp_fg3m': last_7['OPP_FG3M'].mean(),
            'opp_fg3a': last_7['OPP_FG3A'].mean(),
            'opp_fg3_pct': last_7['OPP_FG3_PCT'].mean(),
            'opp_ft_pct': last_7['OPP_FT_PCT'].mean(),
            'opp_reb': last_7['OPP_REB'].mean(),
            'opp_ast': last_7['OPP_AST'].mean(),
            'opp_tov': last_7['OPP_TOV'].mean(),
            'team_stl': last_7['TEAM_STL'].mean(),
            'team_blk': last_7['TEAM_BLK'].mean(),
            'team_dreb': last_7['TEAM_DREB'].mean(),
            'team_pf': last_7['TEAM_PF'].mean()
        }
        
        # Format display dataframe
        display_df = last_7[['GAME_DATE', 'MATCHUP', 'WL', 'OPP_PTS']].copy()
        display_df['OPP_FG%'] = (last_7['OPP_FG_PCT'] * 100).round(1)
        display_df['OPP_3PM'] = last_7['OPP_FG3M']
        display_df['OPP_3PT%'] = (last_7['OPP_FG3_PCT'] * 100).round(1)
        display_df['STL'] = last_7['TEAM_STL']
        display_df['BLK'] = last_7['TEAM_BLK']
        display_df['DREB'] = last_7['TEAM_DREB']
        
        return {
            'season': season_stats,
            'trimmed_7': trimmed_7,
            'last_7_games': display_df.head(7)
        }
        
    except Exception as e:
        print(f"Error fetching team defense: {e}")
        import traceback
        traceback.print_exc()
        return None
