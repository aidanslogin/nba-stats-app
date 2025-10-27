import streamlit as st

st.title('My First NBA App')
st.write('Hello! This will be my NBA stats calculator.')

player_name = st.text_input('Enter a player name:')
st.write('You searched for:', player_name)
