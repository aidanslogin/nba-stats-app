"""NBA Stats Analyzer - Main Streamlit App"""

import streamlit as st
import time

# Import stats functions from stats module
from stats import get_player_stats, get_team_offense_stats, get_team_defense_stats

# Import from cached data modules
from data.teams import get_all_teams, get_cache_timestamp as get_teams_timestamp, get_cache_season
from data.players import get_all_players, get_cache_timestamp as get_players_timestamp

st.set_page_config(page_title="NBA Stats Analyzer", page_icon="🏀", layout="wide")

st.title("🏀 NBA Stats Analyzer")

# Load data from cached modules
all_players = get_all_players()
all_teams = get_all_teams()

# Hardcoded season
season = "2025-26"

# Display cache status in sidebar
with st.sidebar:
    st.header("📊 Data Status")
    
    teams_updated = get_teams_timestamp()
    st.info(f"**Teams Cache:**\n{teams_updated}")
    
    players_updated = get_players_timestamp()
    st.info(f"**Players Cache:**\n{players_updated}")
    
    current_season = get_cache_season()
    st.metric("Season", current_season)
    
    st.metric("Teams Loaded", len(all_teams))
    st.metric("Players Loaded", len(all_players))
    
    st.markdown("---")
    st.caption("Data is cached and refreshed daily at 3 AM")

# Tabs
tab1, tab2, tab3 = st.tabs(["👤 Player Stats", "⚔️ Team Offense", "🛡️ Team Defense"])

player_data = None

# TAB 1: PLAYER STATS
with tab1:
    st.header(f"👤 Player Offensive Stats - {season}")
    
    player_names = ["Find Player"] + sorted([p['DISPLAY_FIRST_LAST'] for p in all_players])
    selected_player_name = st.selectbox("Find Player", player_names, key="player_select")
    
    if selected_player_name != "Find Player":
        selected_player = [p for p in all_players if p['DISPLAY_FIRST_LAST'] == selected_player_name][0]
        player_id = str(selected_player['PERSON_ID'])
        
        if st.button("Get Player Stats", key="player_button"):
            with st.spinner(f"Loading player data for {season}..."):
                player_data = get_player_stats(player_id, season)
                time.sleep(0.6)

        if player_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Season Average")
                st.metric("Games Played", player_data['season']['games'])
                st.metric("Points Per Game", f"{player_data['season']['ppg']:.1f}")
                st.metric("Rebounds", f"{player_data['season']['rpg']:.1f}")
                st.metric("Assists", f"{player_data['season']['apg']:.1f}")
                st.metric("3-Pointers Made", f"{player_data['season']['fg3m']:.1f}")
                st.metric("FG%", f"{player_data['season']['fg_pct']:.1%}")
            
            with col2:
                st.subheader("🔥 Recent Form")
                st.info("Season average (game logs not cached)")
                
                trend_ppg = player_data['trimmed_7']['ppg'] - player_data['season']['ppg']
                st.metric("Points Per Game", f"{player_data['trimmed_7']['ppg']:.1f}", f"{trend_ppg:+.1f}")
                
                trend_rpg = player_data['trimmed_7']['rpg'] - player_data['season']['rpg']
                st.metric("Rebounds", f"{player_data['trimmed_7']['rpg']:.1f}", f"{trend_rpg:+.1f}")
                
                trend_apg = player_data['trimmed_7']['apg'] - player_data['season']['apg']
                st.metric("Assists", f"{player_data['trimmed_7']['apg']:.1f}", f"{trend_apg:+.1f}")
            
            st.markdown("---")
            st.dataframe(player_data['last_7_games'], use_container_width=True)
            
# TAB 2: TEAM OFFENSE
with tab2:
    st.header(f"⚔️ Team Offensive Stats - {season}")
    
    team_names = sorted([t['TEAM_NAME'] for t in all_teams])
    selected_team_name = st.selectbox("Select Team", team_names, key="offense_select")
    
    selected_team = [t for t in all_teams if t['TEAM_NAME'] == selected_team_name][0]
    team_id = str(selected_team['TEAM_ID'])
    
    if st.button("Get Team Offense", key="offense_button"):
        with st.spinner(f"Loading team offense data for {season}..."):
            team_data = get_team_offense_stats(team_id, season)
            time.sleep(0.6)
        
        if team_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {season} Season Averages")
                st.metric("Games Played", team_data['season']['games'])
                st.metric("Points Per Game", f"{team_data['season']['ppg']:.1f}")
                st.metric("FG%", f"{team_data['season']['fg_pct']:.1%}")
                st.metric("3PT%", f"{team_data['season']['fg3_pct']:.1%}")
            
            with col2:
                st.subheader("🔥 Trimmed Last 7 Games")
                trend_ppg = team_data['trimmed_7']['ppg'] - team_data['season']['ppg']
                st.metric("Points Per Game", f"{team_data['trimmed_7']['ppg']:.1f}", f"{trend_ppg:+.1f}")
                st.metric("FG%", f"{team_data['trimmed_7']['fg_pct']:.1%}")
                st.metric("3PT%", f"{team_data['trimmed_7']['fg3_pct']:.1%}")
            
            st.markdown("---")
            st.dataframe(team_data['last_7_games'], use_container_width=True)

# TAB 3: TEAM DEFENSE
with tab3:
    st.header(f"🛡️ Team Defensive Stats - {season}")
    
    team_names = sorted([t['TEAM_NAME'] for t in all_teams])
    selected_team_name_def = st.selectbox("Select Team", team_names, key="defense_select")
    
    selected_team_def = [t for t in all_teams if t['TEAM_NAME'] == selected_team_name_def][0]
    team_id_def = str(selected_team_def['TEAM_ID'])
    
    if st.button("Get Team Defense", key="defense_button"):
        with st.spinner(f"Loading team defense data for {season}..."):
            defense_data = get_team_defense_stats(team_id_def, season)
            time.sleep(0.6)
        
        if defense_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {season} Season Averages")
                st.metric("Games Played", defense_data['season']['games'])
                st.metric("Opponent PPG", f"{defense_data['season']['opp_ppg']:.1f}")
            
            with col2:
                st.subheader("🔥 Trimmed Last 7 Games")
                trend = defense_data['trimmed_7']['opp_ppg'] - defense_data['season']['opp_ppg']
                st.metric("Opponent PPG", f"{defense_data['trimmed_7']['opp_ppg']:.1f}", 
                         f"{trend:+.1f}", delta_color="inverse")
            
            st.markdown("---")
            st.dataframe(defense_data['last_7_games'], use_container_width=True)

# Footer
st.markdown("---")
st.caption("Powered by Young Bull Analytics")
