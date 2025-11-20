"""
Comprehensive NBA Data Fetcher for 2025-26 Season
Fetches ALL available data in batches and caches locally.
Run this once daily to refresh all cached data.
"""

from datetime import datetime
import json
import os
import time

# SET TIMEOUT FIRST - before importing endpoints
from nba_api.stats.library.http import NBAStatsHTTP
NBAStatsHTTP.timeout = 120  # Increase from 30 to 120 seconds

# NOW import endpoints (after timeout is set)
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    commonallplayers,
    leaguestandingsv3,
    playercareerstats,
    playergamelog,
    teamgamelog
)

# Configuration
SEASON = "2025-26"
OUTPUT_DIR = "cached_data"
RATE_LIMIT_DELAY = 0.6  # Delay between individual API calls (600ms)
BATCH_DELAY = 2.0       # Longer delay between batches
BATCH_SIZE = 10         # Number of items per batch

# Track statistics
stats = {
    "total_fetches": 0,
    "successful_fetches": 0,
    "failed_fetches": 0,
    "start_time": datetime.now()
}

def create_output_dir():
    """Create cached_data directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✓ Output directory ready: {OUTPUT_DIR}/")

def fetch_and_save(endpoint_func, filename, **kwargs):
    """
    Fetch data from NBA API endpoint and save to JSON file.
    
    Args:
        endpoint_func: NBA API endpoint function
        filename: Output JSON filename
        **kwargs: Parameters for endpoint
    
    Returns:
        bool: True if successful, False otherwise
    """
    stats["total_fetches"] += 1
    
    try:
        # Call endpoint
        response = endpoint_func(**kwargs)
        data = response.get_normalized_dict()
        
        # Create output with metadata
        output = {
            "last_updated": datetime.now().isoformat(),
            "season": kwargs.get("season", SEASON),
            "data": data
        }
        
        # Save to JSON
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        stats["successful_fetches"] += 1
        print(f"  ✓ {filename}")
        time.sleep(RATE_LIMIT_DELAY)
        return True
        
    except Exception as e:
        stats["failed_fetches"] += 1
        print(f"  ✗ {filename}: {str(e)}")
        time.sleep(RATE_LIMIT_DELAY)
        return False

def fetch_all_player_stats():
    """
    Fetch season stats AND game logs for all active players.
    Uses playercareerstats endpoint and filters for 2025-26 season.
    """
    print("\n📊 Fetching all player season stats and game logs...")
    
    # First get all players
    try:
        players_response = commonallplayers.CommonAllPlayers(season=SEASON, is_only_current_season=1)
        all_players = players_response.get_normalized_dict()['CommonAllPlayers']
    except Exception as e:
        print(f"  ✗ Failed to load players: {e}")
        return
    
    print(f"  Found {len(all_players)} active players")
    
    # Create a directory for player stats
    player_stats_dir = os.path.join(OUTPUT_DIR, "player_stats")
    os.makedirs(player_stats_dir, exist_ok=True)
    
    # Process players in batches
    for batch_idx in range(0, len(all_players), BATCH_SIZE):
        batch = all_players[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        total_batches = (len(all_players) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  Batch {batch_num}/{total_batches}...")
        
        for player in batch:
            try:
                player_id = player['PERSON_ID']
                player_name = player['DISPLAY_FIRST_LAST']
                
                # Fetch player career stats (includes current season)
                career_response = playercareerstats.PlayerCareerStats(
                    player_id=str(player_id)
                )
                career_data = career_response.get_normalized_dict()
                
                time.sleep(RATE_LIMIT_DELAY)
                
                # FETCH GAME LOG FOR CURRENT SEASON
                game_log_data = []
                try:
                    gamelog_response = playergamelog.PlayerGameLog(
                        player_id=str(player_id),
                        season=SEASON
                    )
                    game_log_data = gamelog_response.get_normalized_dict()
                    print(f"    ✓ {player_name} (with game log)")
                except Exception as gl_error:
                    print(f"    ⚠ {player_name} (no game log: {str(gl_error)})")
                
                # Save to individual player file
                output = {
                    "last_updated": datetime.now().isoformat(),
                    "player_id": player_id,
                    "player_name": player_name,
                    "team_abbreviation": player.get('TEAM_ABBREVIATION', 'FA'),
                    "season": SEASON,
                    "data": career_data,
                    "game_log": game_log_data
                }
                
                safe_name = player_name.replace(' ', '_').replace('/', '_')
                filename = os.path.join(player_stats_dir, f"{player_id}_{safe_name}.json")
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=2)
                
                stats["successful_fetches"] += 1
                time.sleep(RATE_LIMIT_DELAY)
                
            except Exception as e:
                stats["failed_fetches"] += 1
                print(f"    ✗ {player_name}: {str(e)}")
                time.sleep(RATE_LIMIT_DELAY)
        
        # Longer delay between batches
        if batch_num < total_batches:
            print(f"  Waiting {BATCH_DELAY}s before next batch...")
            time.sleep(BATCH_DELAY)

def fetch_all_team_gamelogs():
    """
    Fetch recent game logs for all teams.
    """
    print("\n🏀 Fetching all team game logs...")
    
    # Get teams first
    try:
        teams_response = leaguedashteamstats.LeagueDashTeamStats(season=SEASON)
        all_teams = teams_response.get_normalized_dict()['LeagueDashTeamStats']
    except Exception as e:
        print(f"  ✗ Failed to load teams: {e}")
        return
    
    print(f"  Found {len(all_teams)} teams")
    
    # Create directory for team game logs
    team_logs_dir = os.path.join(OUTPUT_DIR, "team_gamelogs")
    os.makedirs(team_logs_dir, exist_ok=True)
    
    # Process teams in batches
    for batch_idx in range(0, len(all_teams), BATCH_SIZE):
        batch = all_teams[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        total_batches = (len(all_teams) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  Batch {batch_num}/{total_batches}...")
        
        for team in batch:
            try:
                team_id = team['TEAM_ID']
                team_name = team['TEAM_NAME']
                
                # Fetch team game log for current season
                gamelog_response = teamgamelog.TeamGameLog(
                    team_id=str(team_id),
                    season=SEASON
                )
                gamelog_data = gamelog_response.get_normalized_dict()
                
                # Save to individual team file
                output = {
                    "last_updated": datetime.now().isoformat(),
                    "team_id": team_id,
                    "team_name": team_name,
                    "season": SEASON,
                    "data": gamelog_data
                }
                
                safe_name = team_name.replace(' ', '_').replace('/', '_')
                filename = os.path.join(team_logs_dir, f"{team_id}_{safe_name}.json")
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=2)
                
                stats["successful_fetches"] += 1
                print(f"    ✓ {team_name}")
                time.sleep(RATE_LIMIT_DELAY)
                
            except Exception as e:
                stats["failed_fetches"] += 1
                print(f"    ✗ {team_name}: {str(e)}")
                time.sleep(RATE_LIMIT_DELAY)
        
        # Longer delay between batches
        if batch_num < total_batches:
            print(f"  Waiting {BATCH_DELAY}s before next batch...")
            time.sleep(BATCH_DELAY)

def main():
    """Main function - fetch all data."""
    
    print(f"\n{'='*70}")
    print(f"🏀 NBA COMPREHENSIVE DATA FETCHER - {SEASON} Season")
    print(f"{'='*70}\n")
    
    create_output_dir()
    
    # Fetch base data (fast)
    print("\n📋 Fetching base data...")
    fetch_and_save(
        leaguedashteamstats.LeagueDashTeamStats,
        "teams.json",
        season=SEASON
    )
    
    fetch_and_save(
        commonallplayers.CommonAllPlayers,
        "players.json",
        season=SEASON,
        is_only_current_season=1
    )
    
    fetch_and_save(
        leaguestandingsv3.LeagueStandingsV3,
        "standings.json",
        season=SEASON
    )
    
    # Fetch comprehensive data (slower, batch processing)
    fetch_all_player_stats()
    fetch_all_team_gamelogs()
    
    # Print summary
    elapsed = datetime.now() - stats["start_time"]
    print(f"\n{'='*70}")
    print(f"✓ FETCH COMPLETE")
    print(f"{'='*70}")
    print(f"  Total API calls: {stats['total_fetches']}")
    print(f"  Successful: {stats['successful_fetches']}")
    print(f"  Failed: {stats['failed_fetches']}")
    print(f"  Time elapsed: {elapsed.total_seconds():.1f}s")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
