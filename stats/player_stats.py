"""Player statistics module - reads from cached data"""

import json
import os
import glob
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog

CACHE_DIR = "cached_data/player_stats"

def find_player_cache_file(player_id):
    """Find the cached JSON file for a player by ID."""
    pattern = os.path.join(CACHE_DIR, f"{player_id}_*.json")
    files = glob.glob(pattern)
    if files:
        return files[0]
    return None

def calculate_trimmed_mean(values):
    """Remove highest and lowest value, return average of remaining values."""
    if len(values) < 3:
        return np.mean(values) if values else 0
    sorted_vals = sorted(values)
    trimmed = sorted_vals[1:-1]
    return np.mean(trimmed) if trimmed else 0

def get_player_stats(player_id, season="2025-26"):
    """Get player season statistics from cached data and live game logs."""
    try:
        cache_file = find_player_cache_file(player_id)
        
        if not cache_file:
            print(f"Player {player_id} not found in cache")
            return None
        
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        
        player_name = cached['player_name']
        data = cached['data']
        
        season_data = data.get('SeasonTotalsRegularSeason', [])
        
        if not season_data:
            print(f"No season data for {player_name}")
            return None
        
        season_stats = None
        for stat in season_data:
            stat_season = stat.get('SEASON_ID', '')
            if season in stat_season:
                season_stats = stat
                break
        
        if not season_stats:
            print(f"No stats for {player_name} in {season}")
            return None
        
        games = season_stats.get('GP', 0)
        
        if games == 0:
            return None
        
        team_id = season_stats.get('TEAM_ID', None)
        
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
        
        total_team_games = games
        missed_games_df = pd.DataFrame()
        
        if team_id:
            try:
                from nba_api.stats.endpoints import leaguegamefinder
                
                # Get all team games
                team_gamefinder = leaguegamefinder.LeagueGameFinder(
                    team_id_nullable=str(team_id),
                    season_nullable=season,
                    season_type_nullable='Regular Season'
                )
                team_games_df = team_gamefinder.get_data_frames()[0]
                total_team_games = len(team_games_df)
                
                # Get all player games
                player_gamelog_obj = playergamelog.PlayerGameLog(player_id=player_id, season=season)
                player_games_df = player_gamelog_obj.get_data_frames()[0]
                
                print(f"DEBUG: Player gamelog columns: {player_games_df.columns.tolist()}")
                
                # The column might be 'Game_ID' instead of 'GAME_ID'
                game_id_col = 'Game_ID' if 'Game_ID' in player_games_df.columns else 'GAME_ID'
                
                # Get the game IDs the player participated in
                player_game_ids = set(player_games_df[game_id_col].tolist())
                
                # Find team games the player MISSED
                missed_games_df = team_games_df[~team_games_df['GAME_ID'].isin(player_game_ids)]
                
                print(f"DEBUG: Found {len(missed_games_df)} total missed games for {player_name}")
                
                # Format for display - get last 5 missed games
                if len(missed_games_df) > 0:
                    missed_games_df = missed_games_df[['GAME_DATE', 'MATCHUP']].head(5)
                    print(f"DEBUG: Showing {len(missed_games_df)} missed games")
                    print(f"DEBUG: Missed games data:\n{missed_games_df}")
                else:
                    print("DEBUG: No missed games found")
                
            except Exception as e:
                print(f"Error getting team/missed games: {e}")
                import traceback
                traceback.print_exc()
        
        games_missed_count = total_team_games - games
        
        try:
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
            all_games = gamelog.get_data_frames()[0]
            
            games_played = all_games[all_games['MIN'].notna() & (all_games['MIN'] > 0)]
            games_df = games_played.head(7)
            
            if len(games_df) > 0:
                first_game_date = games_df.iloc[-1]['GAME_DATE']
                last_game_date = games_df.iloc[0]['GAME_DATE']
                date_range = f"{first_game_date} to {last_game_date}"
            else:
                date_range = "No games played"
            
            if len(games_df) >= 3:
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
                    'minutes': calculate_trimmed_mean(games_df['MIN'].tolist()),
                    'games_missed_season': games_missed_count,
                    'date_range': date_range
                }
                
                last_7_games = games_df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 
                                          'STL', 'BLK', 'TOV', 'FG3M', 'FG_PCT', 
                                          'FT_PCT', 'MIN']].copy()
            else:
                trimmed_7_stats = season_avg.copy()
                trimmed_7_stats['games_missed_season'] = games_missed_count
                trimmed_7_stats['date_range'] = date_range
                
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
            
            print(f"DEBUG: Returning missed_games_df with shape: {missed_games_df.shape}")
            
            return {
                'season': season_avg,
                'trimmed_7': trimmed_7_stats,
                'last_7_games': last_7_games,
                'context': {
                    'total_games': total_team_games,
                    'games_played': games,
                    'games_missed': games_missed_count
                },
                'last_5_missed_games': missed_games_df
            }
        
        except Exception as e:
            print(f"Error fetching game logs: {str(e)}")
            import traceback
            traceback.print_exc()
            
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
                'last_7_games': last_7_games,
                'context': {
                    'total_games': total_team_games,
                    'games_played': games,
                    'games_missed': games_missed_count
                },
                'last_5_missed_games': missed_games_df
            }
        
    except Exception as e:
        print(f"Error fetching player stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
