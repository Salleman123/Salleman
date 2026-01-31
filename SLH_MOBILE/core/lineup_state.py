# core/lineup_state.py
"""
Centralized lineup state management.
All lineup data flows through here.
"""

from datetime import datetime
from typing import Dict, List, Optional


class LineupState:
    """
    Holds current lineup data that can be exported to vMix or files.
    This is the single source of truth for lineup information.
    """
    
    def __init__(self):
        self.home_team = {
            'name': '',
            'logo': '',
            'players': [],
            'staff': []
        }
        self.away_team = {
            'name': '',
            'logo': '',
            'players': [],
            'staff': []
        }
        self.last_updated = None
        self.source = None  # 'api', 'swehockey', 'vmix', 'manual'
        self.source_info = ""  # Additional info about source
    
    def update_from_lineup_data(self, lineup_data):
        """
        Update state from imported LineupData object
        
        Args:
            lineup_data: LineupData object from data_source
        """
        self.home_team = {
            'name': lineup_data.home_team.get('name', ''),
            'logo': lineup_data.home_team.get('logo', ''),
            'players': lineup_data.home_team.get('players', []).copy(),
            'staff': lineup_data.home_team.get('staff', []).copy()
        }
        self.away_team = {
            'name': lineup_data.away_team.get('name', ''),
            'logo': lineup_data.away_team.get('logo', ''),
            'players': lineup_data.away_team.get('players', []).copy(),
            'staff': lineup_data.away_team.get('staff', []).copy()
        }
        self.last_updated = datetime.now()
        self.source = lineup_data.metadata.get('source', 'unknown')
        self.source_info = f"{self.source} - {self.last_updated.strftime('%Y-%m-%d %H:%M')}"
    
    def get_exportable_data(self) -> Dict:
        """
        Return dict of all exportable data with descriptive keys
        
        Returns:
            Dict mapping data keys to actual values
        """
        return {
            # Team info
            'home_name': self.home_team.get('name', ''),
            'away_name': self.away_team.get('name', ''),
            'home_logo': self.home_team.get('logo', ''),
            'away_logo': self.away_team.get('logo', ''),
            
            # Players (lists)
            'home_players': self.home_team.get('players', []),
            'away_players': self.away_team.get('players', []),
            
            # Staff (lists)
            'home_staff': self.home_team.get('staff', []),
            'away_staff': self.away_team.get('staff', []),
        }
    
    def has_data(self) -> bool:
        """Check if any lineup data is loaded"""
        return bool(
            self.home_team.get('name') or 
            self.away_team.get('name') or
            self.home_team.get('players') or
            self.away_team.get('players')
        )
    
    def get_summary(self) -> str:
        """Get human-readable summary of current state"""
        if not self.has_data():
            return "Ingen lineup inläst"
        
        home_name = self.home_team.get('name', 'Hemma')
        away_name = self.away_team.get('name', 'Borta')
        home_players = len(self.home_team.get('players', []))
        away_players = len(self.away_team.get('players', []))
        
        return f"{home_name} ({home_players}p) vs {away_name} ({away_players}p)"
    
    def clear(self):
        """Clear all lineup data"""
        self.home_team = {'name': '', 'logo': '', 'players': [], 'staff': []}
        self.away_team = {'name': '', 'logo': '', 'players': [], 'staff': []}
        self.last_updated = None
        self.source = None
        self.source_info = ""
