"""NBA Stats Analyzer - Main Streamlit App"""

import streamlit as st
import time

# Import stats functions from stats module
from stats import get_player_stats, get_team_offense_stats, get_team_defense_stats

# Load static data from NBA API
from nba_api.stats.static import players, teams

st.set_page_config(page_title="NBA Stats Analyzer", page_icon="🏀", layout="wide")

st.title("🏀 NBA Stats Analyzer")

# Load static data
all_players = players.get_active_players()
all_teams = teams.get_teams()

# Rest of your code stays the same...


# Sidebar
st.sidebar.header("⚙️ Settings")
season = st.sidebar.selectbox(
    "Select Season",
    ['2025-26', '2024-25', '2023-24', '2022-23'],
    index=2  # Default to 2023-24
)

st.sidebar.info(f"**Current Season:** {season}")

# Tabs
tab1, tab2, tab3 = st.tabs(["👤 Player Stats", "⚔️ Team Offense", "🛡️ Team Defense"])

# TAB 1: PLAYER STATS
with tab1:
    st.header(f"👤 Player Offensive Stats - {season}")
    
    player_names = sorted([p['full_name'] for p in all_players])
    selected_player_name = st.selectbox("Select Player", player_names, key="player_select")
    
    selected_player = [p for p in all_players if p['full_name'] == selected_player_name][0]
    player_id = str(selected_player['id'])
    
    if st.button("Get Player Stats", key="player_button"):
        with st.spinner(f"Loading player data for {season}..."):
            player_data = get_player_stats(player_id, season)
            time.sleep(0.6)
        
        if player_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {season} Season Averages")
                st.metric("Games Played", player_data['season']['games'])
                st.metric("Points Per Game", f"{player_data['season']['ppg']:.1f}")
                st.metric("Rebounds", f"{player_data['season']['rpg']:.1f}")
                st.metric("Assists", f"{player_data['season']['apg']:.1f}")
                st.metric("3-Pointers Made", f"{player_data['season']['fg3m']:.1f}")
                st.metric("FG%", f"{player_data['season']['fg_pct']:.1%}")
            
            with col2:
                st.subheader("🔥 Trimmed Last 7 Games")
                st.info("Removes highest and lowest game from last 7")
                
                trend_ppg = player_data['trimmed_7']['ppg'] - player_data['season']['ppg']
                st.metric("Points Per Game", f"{player_data['trimmed_7']['ppg']:.1f}", f"{trend_ppg:+.1f}")
                
                trend_rpg = player_data['trimmed_7']['rpg'] - player_data['season']['rpg']
                st.metric("Rebounds", f"{player_data['trimmed_7']['rpg']:.1f}", f"{trend_rpg:+.1f}")
                
                trend_apg = player_data['trimmed_7']['apg'] - player_data['season']['apg']
                st.metric("Assists", f"{player_data['trimmed_7']['apg']:.1f}", f"{trend_apg:+.1f}")
            
            st.markdown("---")
            st.dataframe(player_data['last_7_games'], use_container_width=True)
        else:
            st.error(f"❌ No data available for {selected_player_name} in {season}.")

# TAB 2: TEAM OFFENSE
with tab2:
    st.header(f"⚔️ Team Offensive Stats - {season}")
    
    team_names = sorted([t['full_name'] for t in all_teams])
    selected_team_name = st.selectbox("Select Team", team_names, key="offense_select")
    
    selected_team = [t for t in all_teams if t['full_name'] == selected_team_name][0]
    team_id = str(selected_team['id'])
    
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
        else:
            st.error(f"❌ No data available for {selected_team_name} in {season}.")

# TAB 3: TEAM DEFENSE
with tab3:
    st.header(f"🛡️ Team Defensive Stats - {season}")
    
    team_names = sorted([t['full_name'] for t in all_teams])
    selected_team_name_def = st.selectbox("Select Team", team_names, key="defense_select")
    
    selected_team_def = [t for t in all_teams if t['full_name'] == selected_team_name_def][0]
    team_id_def = str(selected_team_def['id'])
    
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
        else:
            st.error(f"❌ No data available for {selected_team_name_def} in {season}.")

st.markdown("---")
st.caption(f"🏀 {season} NBA Season | Built with NBA API")
