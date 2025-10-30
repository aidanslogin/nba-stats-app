import streamlit as st
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonteamroster, commonplayerinfo
import pandas as pd
import time
from datetime import datetime

st.title('NBA Stats Calculator')
st.write('Last 5 games with trimmed average vs season average')

@st.cache_data
def get_all_players():
    return players.get_players()

@st.cache_data
def get_all_teams():
    return teams.get_teams()

@st.cache_data(ttl=3600)
def get_active_players_2025():
    """Get players on 2025-26 rosters"""
    all_players = get_all_players()
    all_teams_list = get_all_teams()
    
    active_player_ids = set()
    
    for team in all_teams_list:
        try:
            time.sleep(0.3)
            roster = commonteamroster.CommonTeamRoster(team_id=team['id'], season='2025-26')
            roster_df = roster.get_data_frames()[0]
            
            for player_id in roster_df['PLAYER_ID'].tolist():
                active_player_ids.add(player_id)
        except:
            pass
    
    active_players = [p for p in all_players if p['id'] in active_player_ids]
    
    return active_players

all_players = get_all_players()
all_teams = get_all_teams()

# Create three tabs
tab1, tab2, tab3 = st.tabs(["🔍 Search by Name", "🏀 Browse by Team", "🏈 Today's Games"])

selected_player = None
auto_load_stats = False

# TAB 1: Search by Name with Auto-suggest
with tab1:
    st.write("### Search for a Player")
    st.caption("🔴 Only showing players on 2025-26 rosters")
    
    with st.spinner('Loading active players...'):
        active_players = get_active_players_2025()
    
    st.caption(f"📊 {len(active_players)} active players available")
    
    search_input = st.text_input('Start typing player name:', placeholder='e.g., Stephen, LeBron, Luka', key='search_input')
    
    if search_input and len(search_input) > 1:
        matching_players = [p for p in active_players if search_input.lower() in p['full_name'].lower()]
        
        if matching_players:
            st.write(f"**{len(matching_players)} player(s) found:**")
            
            # Show first 10 matches as clickable buttons
            for player in matching_players[:10]:
                if st.button(f"🏀 {player['full_name']}", key=f"search_{player['id']}", use_container_width=True):
                    selected_player = player
                    auto_load_stats = True
        else:
            st.warning(f"No active players found matching '{search_input}'")
    else:
        st.info("💡 Start typing to see player suggestions")

# TAB 2: Browse by Team
with tab2:
    st.write("### Select a Team")
    team_names = sorted([team['full_name'] for team in all_teams])
    selected_team_name = st.selectbox('Choose an NBA team:', ['Select a team...'] + team_names, key='team_select')
    
    if selected_team_name and selected_team_name != 'Select a team...':
        selected_team = next(t for t in all_teams if t['full_name'] == selected_team_name)
        
        try:
            with st.spinner('Loading roster...'):
                time.sleep(0.5)
                roster = commonteamroster.CommonTeamRoster(team_id=selected_team['id'], season='2025-26')
                roster_df = roster.get_data_frames()[0]
            
            st.write(f"#### {selected_team_name} Roster ({len(roster_df)} players)")
            
            with st.spinner('Calculating playing time for each player...'):
                player_minutes = []
                
                for idx, row in roster_df.iterrows():
                    player_id = row['PLAYER_ID']
                    player_name = row['PLAYER']
                    
                    try:
                        time.sleep(0.3)
                        gamelog = playergamelog.PlayerGameLog(player_id=str(player_id), season='2025-26')
                        games = gamelog.get_data_frames()[0]
                        
                        if len(games) > 0:
                            last_games = games.head(5)
                            total_minutes = 0
                            for min_val in last_games['MIN'].tolist():
                                if isinstance(min_val, str) and ':' in min_val:
                                    parts = min_val.split(':')
                                    total_minutes += int(parts[0]) + int(parts[1])/60
                                else:
                                    total_minutes += float(min_val) if min_val else 0
                            
                            player_minutes.append({'name': player_name, 'minutes': total_minutes, 'games': len(last_games)})
                        else:
                            player_minutes.append({'name': player_name, 'minutes': 0, 'games': 0})
                    except:
                        player_minutes.append({'name': player_name, 'minutes': 0, 'games': 0})
            
            player_minutes.sort(key=lambda x: x['minutes'], reverse=True)
            
            st.write("**Click a player to view their stats:**")
            
            for pm in player_minutes:
                player_obj = next((p for p in all_players if p['full_name'] == pm['name']), None)
                if player_obj:
                    if pm['games'] > 0:
                        avg_min = pm['minutes'] / pm['games']
                        button_label = f"🏀 {pm['name']} ({avg_min:.1f} min/game)"
                    else:
                        button_label = f"🏀 {pm['name']} (No games)"
                    
                    if st.button(button_label, key=f"team_{player_obj['id']}", use_container_width=True):
                        selected_player = player_obj
                        auto_load_stats = True
            
        except Exception as e:
            st.error(f"Error loading roster: {str(e)}")

# TAB 3: Today's Games
with tab3:
    st.write("### Today's NBA Games")
    today_str = datetime.now().strftime('%A, %B %d, %Y')
    st.write(f"**{today_str}**")
    
    todays_games = [
        {'away': 'Orlando Magic', 'home': 'Charlotte Hornets', 'time': '7:00 PM ET'},
        {'away': 'Golden State Warriors', 'home': 'Milwaukee Bucks', 'time': '8:00 PM ET'},
        {'away': 'Washington Wizards', 'home': 'Oklahoma City Thunder', 'time': '8:00 PM ET'},
        {'away': 'Miami Heat', 'home': 'San Antonio Spurs', 'time': '8:30 PM ET'}
    ]
    
    st.write(f"### {len(todays_games)} Game(s) Today")
    
    game_options = ['Select a game...']
    for game in todays_games:
        matchup_text = f"{game['away']} @ {game['home']} - {game['time']}"
        game_options.append(matchup_text)
    
    selected_game = st.selectbox('Select a game to view team rosters:', game_options, key='game_select')
    
    if selected_game and selected_game != 'Select a game...':
        game_info = next(g for g in todays_games if f"{g['away']} @ {g['home']}" in selected_game)
        
        st.write("---")
        st.write(f"### {game_info['away']} @ {game_info['home']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"#### {game_info['away']} (Away)")
            away_team_obj = next((t for t in all_teams if t['full_name'] == game_info['away']), None)
            
            if away_team_obj:
                try:
                    roster = commonteamroster.CommonTeamRoster(team_id=away_team_obj['id'], season='2025-26')
                    roster_df = roster.get_data_frames()[0]
                    
                    for player_name in sorted(roster_df['PLAYER'].tolist()):
                        player_obj = next((p for p in all_players if p['full_name'] == player_name), None)
                        if player_obj:
                            if st.button(f"🏀 {player_name}", key=f"away_{player_obj['id']}", use_container_width=True):
                                selected_player = player_obj
                                auto_load_stats = True
                except:
                    st.error("Could not load roster")
            else:
                st.warning("Team not found in database")
        
        with col2:
            st.write(f"#### {game_info['home']} (Home)")
            home_team_obj = next((t for t in all_teams if t['full_name'] == game_info['home']), None)
            
            if home_team_obj:
                try:
                    roster = commonteamroster.CommonTeamRoster(team_id=home_team_obj['id'], season='2025-26')
                    roster_df = roster.get_data_frames()[0]
                    
                    for player_name in sorted(roster_df['PLAYER'].tolist()):
                        player_obj = next((p for p in all_players if p['full_name'] == player_name), None)
                        if player_obj:
                            if st.button(f"🏀 {player_name}", key=f"home_{player_obj['id']}", use_container_width=True):
                                selected_player = player_obj
                                auto_load_stats = True
                except:
                    st.error("Could not load roster")
            else:
                st.warning("Team not found in database")

# AUTO-LOAD STATS SECTION
st.write("---")

if selected_player:
    try:
        with st.spinner('Loading player info...'):
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=selected_player['id'])
            player_details = player_info.get_normalized_dict()['CommonPlayerInfo'][0]
            position = player_details.get('POSITION', 'N/A')
            team_name = player_details.get('TEAM_NAME', 'N/A')
            jersey = player_details.get('JERSEY', 'N/A')
            height = player_details.get('HEIGHT', 'N/A')
            st.success(f"📊 **{selected_player['full_name']}** | {position} | #{jersey} | {team_name} | {height}")
    except Exception as e:
        st.success(f"📊 Showing stats for: **{selected_player['full_name']}**")
        st.caption(f"Note: Could not load full player details")
    
    # Auto-load stats when player is clicked
    try:
        with st.spinner('Loading game data...'):
            gamelog = playergamelog.PlayerGameLog(player_id=str(selected_player['id']), season='2025-26')
            games_df = gamelog.get_data_frames()[0]
        
        if len(games_df) < 5:
            st.warning(f"Player only has {len(games_df)} games this season. Need at least 5 games.")
        else:
            last_5_games = games_df.head(5)
            
            st.write(f"### Last 5 Games")
            display_df = last_5_games[['GAME_DATE', 'MATCHUP', 'MIN', 'PTS', 'REB', 'AST', 'FG3M']].copy()
            display_df.columns = ['Date', 'Opponent', 'Minutes', 'Points', 'Rebounds', 'Assists', '3PM']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.write("---")
            st.write("### Trimmed Average (Last 5 Games)")
            st.write("*Removes best and worst games, averages the middle 3*")
            
            points_5 = last_5_games['PTS'].tolist()
            rebounds_5 = last_5_games['REB'].tolist()
            assists_5 = last_5_games['AST'].tolist()
            threes_5 = last_5_games['FG3M'].tolist()
            
            def trimmed_average(values):
                sorted_values = sorted(values)
                trimmed = sorted_values[1:-1]
                return sum(trimmed) / len(trimmed)
            
            trimmed_pts = trimmed_average(points_5)
            trimmed_reb = trimmed_average(rebounds_5)
            trimmed_ast = trimmed_average(assists_5)
            trimmed_3pm = trimmed_average(threes_5)
            
            st.write(f"**Points:** Best game: {max(points_5)} (removed) | Worst game: {min(points_5)} (removed)")
            
            st.write("---")
            st.write("### Full Season Average")
            st.write(f"*Based on all {len(games_df)} games this season*")
            
            season_pts = games_df['PTS'].mean()
            season_reb = games_df['REB'].mean()
            season_ast = games_df['AST'].mean()
            season_3pm = games_df['FG3M'].mean()
            
            st.write("---")
            st.write("### 📊 Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Trimmed Avg (Last 5)")
                st.metric("Points", f"{trimmed_pts:.1f}")
                st.metric("Rebounds", f"{trimmed_reb:.1f}")
                st.metric("Assists", f"{trimmed_ast:.1f}")
                st.metric("3-Pointers", f"{trimmed_3pm:.1f}")
            
            with col2:
                st.write("#### Season Average")
                st.metric("Points", f"{season_pts:.1f}", delta=f"{trimmed_pts - season_pts:+.1f}")
                st.metric("Rebounds", f"{season_reb:.1f}", delta=f"{trimmed_reb - season_reb:+.1f}")
                st.metric("Assists", f"{season_ast:.1f}", delta=f"{trimmed_ast - season_ast:+.1f}")
                st.metric("3-Pointers", f"{season_3pm:.1f}", delta=f"{trimmed_3pm - season_3pm:+.1f}")
            
            st.write("---")
            if trimmed_pts > season_pts:
                st.success(f"🔥 {selected_player['full_name']} is performing ABOVE season average in last 5 games!")
            elif trimmed_pts < season_pts:
                st.info(f"📉 {selected_player['full_name']} is performing BELOW season average in last 5 games")
            else:
                st.info(f"➡️ {selected_player['full_name']} is consistent with season average")
                
    except Exception as e:
        st.error(f"Error fetching game data: {str(e)}")
else:
    st.info("👆 Use the tabs above to search for a player, browse by team, or select from today's games")
