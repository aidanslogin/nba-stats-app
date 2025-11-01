import streamlit as st
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonteamroster, commonplayerinfo
import pandas as pd
import time
from datetime import datetime

st.title('NBA Stats Calculator')

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

selected_player = None

# ===== SIDE-BY-SIDE LAYOUT =====
col1, col2 = st.columns(2)

# LEFT COLUMN: SEARCH
with col1:
    st.subheader("🔍 Search Player")
    
    with st.spinner('Loading players...'):
        active_players = get_active_players_2025()
    
    player_names = sorted([p['full_name'] for p in active_players])
    
    # Searchable dropdown (Streamlit filters automatically as you type)
    selected_player_name = st.selectbox(
        'Type or select player:',
        [''] + player_names,
        key='player_search'
    )
    
    if selected_player_name:
        selected_player = next((p for p in active_players if p['full_name'] == selected_player_name), None)

# RIGHT COLUMN: TEAMS
with col2:
    st.subheader("🏀 Browse by Team")
    
    team_names = sorted([team['full_name'] for team in all_teams])
    
    # Simple dropdown for teams
    selected_team_name = st.selectbox(
        'Select team:',
        [''] + team_names,
        key='team_search'
    )
    
    if selected_team_name:
        st.session_state['selected_team_name'] = selected_team_name

# Display roster buttons if a team is selected
if 'selected_team_name' in st.session_state and st.session_state['selected_team_name']:
    selected_team_name = st.session_state['selected_team_name']
    selected_team = next(t for t in all_teams if t['full_name'] == selected_team_name)
    
    rotation_key = f"rotation_{selected_team['id']}"
    
    # Check if we already have this team's rotation in session state
    if rotation_key not in st.session_state:
        try:
            with st.spinner('Loading roster...'):
                time.sleep(0.5)
                roster = commonteamroster.CommonTeamRoster(team_id=selected_team['id'], season='2025-26')
                roster_df = roster.get_data_frames()[0]
            
            with st.spinner('Analyzing rotation...'):
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
                            
                            avg_minutes = total_minutes / len(last_games)
                            
                            player_minutes.append({
                                'name': player_name,
                                'id': player_id,
                                'minutes': total_minutes,
                                'avg_minutes': avg_minutes,
                                'games': len(last_games)
                            })
                        else:
                            player_minutes.append({
                                'name': player_name,
                                'id': player_id,
                                'minutes': 0,
                                'avg_minutes': 0,
                                'games': 0
                            })
                    except:
                        player_minutes.append({
                            'name': player_name,
                            'id': player_id,
                            'minutes': 0,
                            'avg_minutes': 0,
                            'games': 0
                        })
                
                # Sort by minutes
                player_minutes.sort(key=lambda x: x['minutes'], reverse=True)
                
                # FILTER: Top 12 OR 15+ min/game
                filtered_players = []
                for idx, pm in enumerate(player_minutes):
                    if idx < 12 or pm['avg_minutes'] >= 15:
                        filtered_players.append(pm)
                
                # Store in session state
                st.session_state[rotation_key] = filtered_players
                st.session_state[f"{rotation_key}_roster_df"] = roster_df
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display the roster if we have data
    if rotation_key in st.session_state:
        filtered_players = st.session_state[rotation_key]
        roster_df = st.session_state[f"{rotation_key}_roster_df"]
        
        st.write("")
        st.caption(f"**{selected_team_name}** - {len(filtered_players)} rotation players")
        
        # === CLICKABLE PLAYER BUTTONS ===
        cols = st.columns(4)
        
        for idx, pm in enumerate(filtered_players):
            col = cols[idx % 4]
            
            # Get position from roster
            player_position = roster_df[roster_df['PLAYER_ID'] == pm['id']]['POSITION'].values[0] if len(roster_df[roster_df['PLAYER_ID'] == pm['id']]) > 0 else ''
            button_label = f"{pm['name']} ({player_position})" if player_position else pm['name']
            
            if col.button(
                button_label,
                key=f"team_player_{pm['id']}",
                use_container_width=True
            ):
                # Set selected player when button is clicked
                selected_player = next((p for p in all_players if p['full_name'] == pm['name']), None)

# ===== PLAYER STATS DISPLAY =====
st.write("---")

if selected_player:
    try:
        with st.spinner('Loading...'):
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=selected_player['id'])
            player_details = player_info.get_normalized_dict()['CommonPlayerInfo'][0]
            position = player_details.get('POSITION', 'N/A')
            team_name = player_details.get('TEAM_NAME', 'N/A')
            jersey = player_details.get('JERSEY', 'N/A')
            height = player_details.get('HEIGHT', 'N/A')
            
            st.markdown(f"## {selected_player['full_name']}")
            st.markdown(f"{position} • #{jersey} • {team_name} • {height}")
            
            st.write("")
            
    except:
        st.markdown(f"## {selected_player['full_name']}")
    
    try:
        with st.spinner('Loading stats...'):
            gamelog = playergamelog.PlayerGameLog(player_id=str(selected_player['id']), season='2025-26')
            games_df = gamelog.get_data_frames()[0]
        
        if len(games_df) < 5:
            st.warning(f"Need at least 5 games ({len(games_df)} played)")
        else:
            last_5_games = games_df.head(5)
            
            points_5 = last_5_games['PTS'].tolist()
            rebounds_5 = last_5_games['REB'].tolist()
            assists_5 = last_5_games['AST'].tolist()
            threes_5 = last_5_games['FG3M'].tolist()
            
            # Calculate minutes
            minutes_5 = []
            for min_val in last_5_games['MIN'].tolist():
                if isinstance(min_val, str) and ':' in min_val:
                    parts = min_val.split(':')
                    minutes_5.append(int(parts[0]) + int(parts[1])/60)
                else:
                    minutes_5.append(float(min_val) if min_val else 0)
            
            def trimmed_average(values):
                sorted_values = sorted(values)
                trimmed = sorted_values[1:-1]
                return sum(trimmed) / len(trimmed)
            
            trimmed_pts = trimmed_average(points_5)
            trimmed_reb = trimmed_average(rebounds_5)
            trimmed_ast = trimmed_average(assists_5)
            trimmed_3pm = trimmed_average(threes_5)
            trimmed_min = trimmed_average(minutes_5)
            
            season_pts = games_df['PTS'].mean()
            season_reb = games_df['REB'].mean()
            season_ast = games_df['AST'].mean()
            season_3pm = games_df['FG3M'].mean()
            
            # Calculate season average minutes
            season_minutes = []
            for min_val in games_df['MIN'].tolist():
                if isinstance(min_val, str) and ':' in min_val:
                    parts = min_val.split(':')
                    season_minutes.append(int(parts[0]) + int(parts[1])/60)
                else:
                    season_minutes.append(float(min_val) if min_val else 0)
            season_min = sum(season_minutes) / len(season_minutes)
            
            # Stats Table
            st.caption(f"{len(games_df)} games played")
            
            stats_data = {
                'Stat': ['Points', 'Rebounds', 'Assists', '3-Pointers', 'Minutes'],
                'Season Average': [
                    f"{season_pts:.1f}",
                    f"{season_reb:.1f}",
                    f"{season_ast:.1f}",
                    f"{season_3pm:.1f}",
                    f"{season_min:.1f}"
                ],
                'Recent Form': [
                    f"{trimmed_pts:.1f} ({trimmed_pts - season_pts:+.1f})",
                    f"{trimmed_reb:.1f} ({trimmed_reb - season_reb:+.1f})",
                    f"{trimmed_ast:.1f} ({trimmed_ast - season_ast:+.1f})",
                    f"{trimmed_3pm:.1f} ({trimmed_3pm - season_3pm:+.1f})",
                    f"{trimmed_min:.1f} ({trimmed_min - season_min:+.1f})"
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            
            # CSS to hide the index column
            hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
            
            st.markdown(hide_table_row_index, unsafe_allow_html=True)
            st.table(stats_df)
                
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Select a player above")
