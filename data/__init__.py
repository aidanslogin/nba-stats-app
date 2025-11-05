"""Data module for loading static NBA data"""

from .players import get_all_players
from .teams import get_all_teams

__all__ = ['get_all_players', 'get_all_teams']
