"""
API Parser for Hockeyettan Team Data
Parses /api/tabel/{series_id} responses
"""

import json
import re
from typing import List, Dict, Optional
from core.data_models import Team


class HockeyettanAPIParser:
    """Parse Hockeyettan API responses"""
    
    @staticmethod
    def parse_tabel(json_data: str) -> List[Team]:
        """
        Parse /api/tabel/{series_id} response
        
        Expected format:
        [{"Team01t.Text": "Hudiksvalls HC",
          "Team01.Source": "https://vmix-new.hockeyettan.se/scoreImages/HUD.png",
          "Pos01.Text": 1,
          ...}]
        """
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # Handle both list and single dict
            if isinstance(data, list):
                data = data[0] if data else {}
            
            teams = []
            
            # Extract teams (up to 20)
            for i in range(1, 21):
                team_key = f"Team{i:02d}t.Text"
                logo_key = f"Team{i:02d}.Source"
                pos_key = f"Pos{i:02d}.Text"
                
                if team_key not in data:
                    continue
                
                team_name = data.get(team_key, "").strip()
                if not team_name:
                    continue
                
                logo_url = data.get(logo_key, "")
                position = data.get(pos_key)
                
                # Extract short name from logo URL
                short_name = HockeyettanAPIParser._extract_short_name(logo_url)
                
                # Build logo URLs (small and large)
                logo_small = logo_url
                logo_large = HockeyettanAPIParser._build_large_logo_url(short_name)
                
                team = Team(
                    name=team_name,
                    short_name=short_name,
                    logo_small=logo_small,
                    logo_large=logo_large,
                    position=position
                )
                
                teams.append(team)
            
            return teams
            
        except Exception as e:
            print(f"Error parsing tabel data: {e}")
            return []
    
    @staticmethod
    def _extract_short_name(logo_url: str) -> str:
        """
        Extract short name from logo URL
        https://vmix-new.hockeyettan.se/scoreImages/HUD.png -> HUD
        """
        if not logo_url:
            return ""
        
        # Extract filename
        match = re.search(r'/([^/]+)\.png', logo_url)
        if match:
            return match.group(1)
        
        return ""
    
    @staticmethod
    def _build_large_logo_url(short_name: str) -> str:
        """
        Build large logo URL from short name
        HUD -> https://vmix-new.hockeyettan.se/premagesLogo/HUD.png
        """
        if not short_name:
            return ""
        
        return f"https://vmix-new.hockeyettan.se/premagesLogo/{short_name}.png"
    
    @staticmethod
    def parse_dagens_matcher(json_data: str) -> List[Dict]:
        """
        Parse /api/round/{series_id} response (dagens matcher)
        Returns list of matches with team info
        """
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if isinstance(data, list):
                data = data[0] if data else {}
            
            matches = []
            
            # Extract up to 10 games
            for i in range(1, 11):
                home_name_key = f"G{i}HomeName.Text"
                
                if home_name_key not in data or not data.get(home_name_key):
                    continue
                
                match = {
                    'home_name': data.get(f"G{i}HomeName.Text", ""),
                    'home_short': data.get(f"G{i}NameHome.Text", ""),
                    'away_name': data.get(f"G{i}AwayName.Text", ""),
                    'away_short': data.get(f"G{i}NameAway.Text", ""),
                    'result': data.get(f"G{i}Result.Text", ""),
                    'home_logo_small': data.get(f"G{i}HomeLogo.Source", ""),
                    'home_logo_large': data.get(f"G{i}LogoHome.Source", ""),
                    'away_logo_small': data.get(f"G{i}AwayLogo.Source", ""),
                    'away_logo_large': data.get(f"G{i}LogoAway.Source", "")
                }
                
                matches.append(match)
            
            return matches
            
        except Exception as e:
            print(f"Error parsing dagens matcher: {e}")
            return []
