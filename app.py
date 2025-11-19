"""NBA Stats Analyzer - Main Streamlit App"""

import streamlit as st
import pandas as pd
import numpy as np
import time

# Import stats functions from stats module
from stats import get_player_stats, get_team_offense_stats, get_team_defense_stats

# Import from cached data modules
from data.teams import get_all_teams, get_cache_timestamp as get_teams_timestamp, get_cache_season
from data.players import get_all_players, get_cache_timestamp as get_players_timestamp

st.set_page_config(page_title="NBA Stats Analyzer", page_icon="🏀", layout="wide")

st.title("🏀 NBA Stats Analyzer")

# Load data from cached modules and filter out WNBA
all_teams_raw = get_all_teams()
all_players_raw = get_all_players()

# Filter to NBA teams only (team IDs start with 1610612)
all_teams = [team for team in all_teams_raw if str(team['TEAM_ID']).startswith('1610612')]

# Get NBA team IDs for player filtering
nba_team_ids = {team['TEAM_ID'] for team in all_teams}

# Filter to NBA players only (must be on an NBA team)
all_players = [
    player for player in all_players_raw 
    if player.get('TEAM_ID') in nba_team_ids or player.get('TEAM_ID') == 0
]


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

# TAB 1: PLAYER STATS
with tab1:
    st.header(f"👤 Player Offensive Stats - {season}")
    
    # Player selection dropdown
    player_names = ["Find Player"] + sorted([p['DISPLAY_FIRST_LAST'] for p in all_players])
    selected_player_name = st.selectbox("Find Player", player_names, key="player_select")
    
    # Only show button if a player is selected
    if selected_player_name != "Find Player":
        selected_player = [p for p in all_players if p['DISPLAY_FIRST_LAST'] == selected_player_name][0]
        player_id = str(selected_player['PERSON_ID'])
        
        # Single button to fetch stats
        if st.button("Get Player Stats", key="player_button"):
            with st.spinner(f"Loading player data for {season}..."):
                player_data = get_player_stats(player_id, season)
                time.sleep(0.6)
                
                if player_data:
                    # Create comparison table
                    comparison_data = {
                        'Stat': ['Games Played', 'Points Per Game', 'Rebounds', 'Assists', 
                                 'Steals', 'Blocks', 'Turnovers', '3-Pointers Made',
                                 'Field Goal %', 'Free Throw %'],
                        'Season Average': [
                            f"{player_data['season']['games']}",
                            f"{player_data['season']['ppg']:.1f}",
                            f"{player_data['season']['rpg']:.1f}",
                            f"{player_data['season']['apg']:.1f}",
                            f"{player_data['season']['spg']:.1f}",
                            f"{player_data['season']['bpg']:.1f}",
                            f"{player_data['season']['topg']:.1f}",
                            f"{player_data['season']['fg3m']:.1f}",
                            f"{player_data['season']['fg_pct']:.1%}",
                            f"{player_data['season']['ft_pct']:.1%}"
                        ],
                        'Recent Form': [
                            f"{player_data['trimmed_7']['games']}",
                            f"{player_data['trimmed_7']['ppg']:.1f}",
                            f"{player_data['trimmed_7']['rpg']:.1f}",
                            f"{player_data['trimmed_7']['apg']:.1f}",
                            f"{player_data['trimmed_7']['spg']:.1f}",
                            f"{player_data['trimmed_7']['bpg']:.1f}",
                            f"{player_data['trimmed_7']['topg']:.1f}",
                            f"{player_data['trimmed_7']['fg3m']:.1f}",
                            f"{player_data['trimmed_7']['fg_pct']:.1%}",
                            f"{player_data['trimmed_7']['ft_pct']:.1%}"
                        ],
                        'Trend': [
                            '',
                            f"{player_data['trimmed_7']['ppg'] - player_data['season']['ppg']:+.1f}",
                            f"{player_data['trimmed_7']['rpg'] - player_data['season']['rpg']:+.1f}",
                            f"{player_data['trimmed_7']['apg'] - player_data['season']['apg']:+.1f}",
                            f"{player_data['trimmed_7']['spg'] - player_data['season']['spg']:+.1f}",
                            f"{player_data['trimmed_7']['bpg'] - player_data['season']['bpg']:+.1f}",
                            f"{player_data['trimmed_7']['topg'] - player_data['season']['topg']:+.1f}",
                            f"{player_data['trimmed_7']['fg3m'] - player_data['season']['fg3m']:+.1f}",
                            f"{(player_data['trimmed_7']['fg_pct'] - player_data['season']['fg_pct']):.3f}",
                            f"{(player_data['trimmed_7']['ft_pct'] - player_data['season']['ft_pct']):.3f}"
                        ]
                    }
                    
                    # Create DataFrame
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    # Styling function
                    def highlight_trend(val):
                        if val == '':
                            return ''
                        try:
                            num = float(val)
                            if num > 0:
                                return 'color: green; font-weight: bold'
                            elif num < 0:
                                return 'color: red; font-weight: bold'
                        except:
                            pass
                        return ''
                    
                    # Apply styling
                    styled_df = comparison_df.style.map(highlight_trend, subset=['Trend'])
                    
                    # Display
                    st.subheader("📊 Stats Comparison")
                    st.info("Recent Form removes highest and lowest game from last 7")
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    st.subheader("📅 Recent Games")
                    st.dataframe(player_data['last_7_games'], use_container_width=True)
                    
                else:
                    st.error(f"No data available for {selected_player_name} in {season}")

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
            # Create comparison table
            comparison_data = {
                'Stat': ['Games Played', 'Points Per Game', 'Field Goal %', 'FG Made',
                         '3-Pointers Made', '3-Point %', 'Free Throw %', 'FT Made',
                         'Assists', 'Turnovers', 'AST/TO Ratio', 'Offensive Rebounds', 
                         'Defensive Rebounds', 'Total Rebounds'],
                'Season Average': [
                    f"{team_data['season']['games']}",
                    f"{team_data['season']['ppg']:.1f}",
                    f"{team_data['season']['fg_pct']:.1%}",
                    f"{team_data['season']['fgm']:.1f}",
                    f"{team_data['season']['fg3m']:.1f}",
                    f"{team_data['season']['fg3_pct']:.1%}",
                    f"{team_data['season']['ft_pct']:.1%}",
                    f"{team_data['season']['ftm']:.1f}",
                    f"{team_data['season']['ast']:.1f}",
                    f"{team_data['season']['tov']:.1f}",
                    f"{team_data['season']['ast_tov_ratio']:.2f}",
                    f"{team_data['season']['oreb']:.1f}",
                    f"{team_data['season']['dreb']:.1f}",
                    f"{team_data['season']['reb']:.1f}"
                ],
                'Recent Form': [
                    f"{team_data['trimmed_7']['games']}",
                    f"{team_data['trimmed_7']['ppg']:.1f}",
                    f"{team_data['trimmed_7']['fg_pct']:.1%}",
                    f"{team_data['trimmed_7']['fgm']:.1f}",
                    f"{team_data['trimmed_7']['fg3m']:.1f}",
                    f"{team_data['trimmed_7']['fg3_pct']:.1%}",
                    f"{team_data['trimmed_7']['ft_pct']:.1%}",
                    f"{team_data['trimmed_7']['ftm']:.1f}",
                    f"{team_data['trimmed_7']['ast']:.1f}",
                    f"{team_data['trimmed_7']['tov']:.1f}",
                    f"{team_data['trimmed_7']['ast_tov_ratio']:.2f}",
                    f"{team_data['trimmed_7']['oreb']:.1f}",
                    f"{team_data['trimmed_7']['dreb']:.1f}",
                    f"{team_data['trimmed_7']['reb']:.1f}"
                ],
                'Trend': [
                    '',
                    f"{team_data['trimmed_7']['ppg'] - team_data['season']['ppg']:+.1f}",
                    f"{(team_data['trimmed_7']['fg_pct'] - team_data['season']['fg_pct']):.3f}",
                    f"{team_data['trimmed_7']['fgm'] - team_data['season']['fgm']:+.1f}",
                    f"{team_data['trimmed_7']['fg3m'] - team_data['season']['fg3m']:+.1f}",
                    f"{(team_data['trimmed_7']['fg3_pct'] - team_data['season']['fg3_pct']):.3f}",
                    f"{(team_data['trimmed_7']['ft_pct'] - team_data['season']['ft_pct']):.3f}",
                    f"{team_data['trimmed_7']['ftm'] - team_data['season']['ftm']:+.1f}",
                    f"{team_data['trimmed_7']['ast'] - team_data['season']['ast']:+.1f}",
                    f"{team_data['trimmed_7']['tov'] - team_data['season']['tov']:+.1f}",
                    f"{team_data['trimmed_7']['ast_tov_ratio'] - team_data['season']['ast_tov_ratio']:+.2f}",
                    f"{team_data['trimmed_7']['oreb'] - team_data['season']['oreb']:+.1f}",
                    f"{team_data['trimmed_7']['dreb'] - team_data['season']['dreb']:+.1f}",
                    f"{team_data['trimmed_7']['reb'] - team_data['season']['reb']:+.1f}"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Styling function for offensive stats
            def highlight_offensive_trend(row):
                stat = row['Stat']
                val = row['Trend']
                
                if val == '':
                    return ['', '', '', '']
                
                try:
                    num = float(val)
                    # For offensive stats, positive (increasing) is generally good
                    # Exception: turnovers where negative (decreasing) is good
                    if stat == 'Turnovers':
                        color = 'green' if num < 0 else 'red'
                    elif stat in ['Points Per Game', 'Field Goal %', 'FG Made', '3-Pointers Made', 
                                 '3-Point %', 'Free Throw %', 'FT Made', 'Assists', 'AST/TO Ratio',
                                 'Offensive Rebounds', 'Defensive Rebounds', 'Total Rebounds']:
                        color = 'green' if num > 0 else 'red'
                    else:
                        return ['', '', '', '']
                    
                    return ['', '', '', f'color: {color}; font-weight: bold']
                except:
                    return ['', '', '', '']
            
            styled_df = comparison_df.style.apply(highlight_offensive_trend, axis=1)
            
            st.subheader("📊 Offensive Stats Comparison")
            st.info("Recent Form removes highest and lowest game from last 7 for PPG")
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📅 Recent Games")
            st.dataframe(team_data['last_7_games'], use_container_width=True, hide_index=True)
        else:
            st.error(f"No offensive data available for {selected_team_name} in {season}")


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
            # Create comparison table
            comparison_data = {
                'Stat': ['Games Played', 'Opponent PPG', 'Opponent FG%', 'Opponent 3PM', 
                         'Opponent 3PT%', 'Opponent FT%', 'Opponent Rebounds', 'Opponent Assists', 
                         'Opponent Turnovers', 'Team Steals', 'Team Blocks', 
                         'Team Def Rebounds', 'Team Fouls'],
                'Season Average': [
                    f"{defense_data['season']['games']}",
                    f"{defense_data['season']['opp_ppg']:.1f}",
                    f"{defense_data['season']['opp_fg_pct']:.1%}",
                    f"{defense_data['season']['opp_fg3m']:.1f}",
                    f"{defense_data['season']['opp_fg3_pct']:.1%}",
                    f"{defense_data['season']['opp_ft_pct']:.1%}",
                    f"{defense_data['season']['opp_reb']:.1f}",
                    f"{defense_data['season']['opp_ast']:.1f}",
                    f"{defense_data['season']['opp_tov']:.1f}",
                    f"{defense_data['season']['team_stl']:.1f}",
                    f"{defense_data['season']['team_blk']:.1f}",
                    f"{defense_data['season']['team_dreb']:.1f}",
                    f"{defense_data['season']['team_pf']:.1f}"
                ],
                'Recent Form': [
                    f"{defense_data['trimmed_7']['games']}",
                    f"{defense_data['trimmed_7']['opp_ppg']:.1f}",
                    f"{defense_data['trimmed_7']['opp_fg_pct']:.1%}",
                    f"{defense_data['trimmed_7']['opp_fg3m']:.1f}",
                    f"{defense_data['trimmed_7']['opp_fg3_pct']:.1%}",
                    f"{defense_data['trimmed_7']['opp_ft_pct']:.1%}",
                    f"{defense_data['trimmed_7']['opp_reb']:.1f}",
                    f"{defense_data['trimmed_7']['opp_ast']:.1f}",
                    f"{defense_data['trimmed_7']['opp_tov']:.1f}",
                    f"{defense_data['trimmed_7']['team_stl']:.1f}",
                    f"{defense_data['trimmed_7']['team_blk']:.1f}",
                    f"{defense_data['trimmed_7']['team_dreb']:.1f}",
                    f"{defense_data['trimmed_7']['team_pf']:.1f}"
                ],
                'Trend': [
                    '',
                    f"{defense_data['trimmed_7']['opp_ppg'] - defense_data['season']['opp_ppg']:+.1f}",
                    f"{(defense_data['trimmed_7']['opp_fg_pct'] - defense_data['season']['opp_fg_pct']):.3f}",
                    f"{defense_data['trimmed_7']['opp_fg3m'] - defense_data['season']['opp_fg3m']:+.1f}",
                    f"{(defense_data['trimmed_7']['opp_fg3_pct'] - defense_data['season']['opp_fg3_pct']):.3f}",
                    f"{(defense_data['trimmed_7']['opp_ft_pct'] - defense_data['season']['opp_ft_pct']):.3f}",
                    f"{defense_data['trimmed_7']['opp_reb'] - defense_data['season']['opp_reb']:+.1f}",
                    f"{defense_data['trimmed_7']['opp_ast'] - defense_data['season']['opp_ast']:+.1f}",
                    f"{defense_data['trimmed_7']['opp_tov'] - defense_data['season']['opp_tov']:+.1f}",
                    f"{defense_data['trimmed_7']['team_stl'] - defense_data['season']['team_stl']:+.1f}",
                    f"{defense_data['trimmed_7']['team_blk'] - defense_data['season']['team_blk']:+.1f}",
                    f"{defense_data['trimmed_7']['team_dreb'] - defense_data['season']['team_dreb']:+.1f}",
                    f"{defense_data['trimmed_7']['team_pf'] - defense_data['season']['team_pf']:+.1f}"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Styling function - note that for defense, lower opponent stats are better
            def highlight_defensive_trend(row):
                stat = row['Stat']
                val = row['Trend']
                
                if val == '':
                    return ['', '', '', '']
                
                try:
                    num = float(val)
                    # For opponent stats, negative (decreasing) is good
                    # For team defensive stats (steals, blocks, rebounds), positive is good
                    # For fouls, negative is good
                    if stat in ['Opponent PPG', 'Opponent FG%', 'Opponent 3PM', 'Opponent 3PT%', 
                               'Opponent FT%', 'Opponent Rebounds', 'Opponent Assists', 'Team Fouls']:
                        color = 'green' if num < 0 else 'red'
                    elif stat in ['Opponent Turnovers', 'Team Steals', 'Team Blocks', 'Team Def Rebounds']:
                        color = 'green' if num > 0 else 'red'
                    else:
                        return ['', '', '', '']
                    
                    return ['', '', '', f'color: {color}; font-weight: bold']
                except:
                    return ['', '', '', '']
            
            styled_df = comparison_df.style.apply(highlight_defensive_trend, axis=1)
            
            st.subheader("📊 Defensive Stats Comparison")
            st.info("Recent Form removes highest and lowest game from last 7 for PPG")
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📅 Recent Games")
            st.dataframe(defense_data['last_7_games'], use_container_width=True, hide_index=True)
        else:
            st.error(f"No defensive data available for {selected_team_name_def} in {season}")


# Footer
st.markdown("---")
st.caption("Powered by Young Bull Analytics")
