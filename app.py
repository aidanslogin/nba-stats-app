import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import time

st.title('NBA Stats Calculator')
st.write('Get detailed stats from last 3 games')

# Get player name from user
player_name = st.text_input('Enter player name (e.g., Stephen Curry):')

# Add a button to search
if st.button('Get Stats'):
    if player_name:
        # Find the player
        nba_players = players.get_players()
        player_dict = [player for player in nba_players if player['full_name'].lower() == player_name.lower()]
        
        if len(player_dict) > 0:
            player = player_dict[0]
            st.success(f"Found {player['full_name']}!")
            
            # Add a brief pause to respect NBA API rate limits
            time.sleep(1)
            
            # Fetch game logs - CURRENT SEASON 2025-26
            try:
                gamelog = playergamelog.PlayerGameLog(
                    player_id=str(player['id']), 
                    season='2025-26'
                )
                
                # Convert to dataframe
                games_df = gamelog.get_data_frames()[0]
                
                # Get last 3 games
                last_3_games = games_df.head(3)
                
                # Check if player has at least 3 games
                if len(last_3_games) < 3:
                    st.warning(f"Player only has {len(last_3_games)} games this season. Need at least 3 games.")
                    st.info("The 2025-26 season just started. Try again in a few days or use season='2024-25' for last season's data.")
                else:
                    # Create a clean table with selected stats
                    st.write(f"### Last 3 Games")
                    
                    # Select and rename columns for display
                    display_df = last_3_games[['GAME_DATE', 'MATCHUP', 'MIN', 'PTS', 'REB', 'AST', 'FG3M']].copy()
                    display_df.columns = ['Date', 'Opponent', 'Minutes', 'Points', 'Rebounds', 'Assists', '3PM']
                    
                    # Display the table
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    st.write("---")
                    
                    # Calculate averages
                    st.write("### 3-Game Averages")
                    
                    # Get lists for each stat
                    points_list = last_3_games['PTS'].tolist()
                    rebounds_list = last_3_games['REB'].tolist()
                    assists_list = last_3_games['AST'].tolist()
                    threes_list = last_3_games['FG3M'].tolist()
                    minutes_list = last_3_games['MIN'].tolist()
                    
                    # Calculate averages
                    avg_points = sum(points_list) / len(points_list)
                    avg_rebounds = sum(rebounds_list) / len(rebounds_list)
                    avg_assists = sum(assists_list) / len(assists_list)
                    avg_threes = sum(threes_list) / len(threes_list)
                    
                    # Minutes need special handling
                    total_minutes = 0
                    for min_str in minutes_list:
                        if isinstance(min_str, str) and ':' in min_str:
                            parts = min_str.split(':')
                            total_minutes += int(parts[0]) + int(parts[1])/60
                        else:
                            total_minutes += float(min_str)
                    avg_minutes = total_minutes / len(minutes_list)
                    
                    # Create averages table
                    averages_data = {
                        'Stat': ['Minutes', 'Points', 'Rebounds', 'Assists', '3-Pointers Made'],
                        'Average': [f"{avg_minutes:.1f}", f"{avg_points:.1f}", f"{avg_rebounds:.1f}", 
                                   f"{avg_assists:.1f}", f"{avg_threes:.1f}"]
                    }
                    averages_df = pd.DataFrame(averages_data)
                    
                    # Display averages table
                    st.dataframe(averages_df, use_container_width=True, hide_index=True)
                    
                    # Summary line
                    st.write("---")
                    st.success(f"### 🏀 {player['full_name']}: {avg_points:.1f} PTS | {avg_rebounds:.1f} REB | {avg_assists:.1f} AST")
                    
            except Exception as e:
                st.error(f"Error fetching game data: {str(e)}")
                
        else:
            st.error(f"Could not find player named '{player_name}'. Please check spelling.")
    else:
        st.warning("Please enter a player name first.")
