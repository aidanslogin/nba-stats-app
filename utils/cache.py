# filepath: /Users/aidan/nba-stats-app/utils/cache.py
import streamlit as st

@st.cache_data
def cache_data(func):
    return func()