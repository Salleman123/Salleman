"""
Data Manager
Handles loading/saving of seasons, teams, and matches
"""

import json
from pathlib import Path
from typing import List, Optional, Dict
from core.data_models import Season, Series, Team, Match


class DataManager:
    """Manages all data persistence"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.teams_dir = self.base_dir / "teams"
        self.matches_dir = self.base_dir / "matches"
        self.exports_dir = self.base_dir / "exports"
        
        self.teams_dir.mkdir(exist_ok=True)
        self.matches_dir.mkdir(exist_ok=True)
        self.exports_dir.mkdir(exist_ok=True)
        
        self.config_file = Path("config") / "seasons.json"
        self.config_file.parent.mkdir(exist_ok=True)
    
    # ========================================
    # Seasons
    # ========================================
    
    def load_seasons(self) -> Dict[str, Dict[str, Season]]:
        """Load all seasons from config"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            seasons = {}
            for sport, sport_data in data.items():
                seasons[sport] = {}
                for year, season_data in sport_data.items():
                    seasons[sport][year] = Season.from_dict(season_data)
            
            return seasons
        except Exception as e:
            print(f"Error loading seasons: {e}")
            return {}
    
    def save_seasons(self, seasons: Dict[str, Dict[str, Season]]):
        """Save all seasons to config"""
        data = {}
        for sport, sport_seasons in seasons.items():
            data[sport] = {}
            for year, season in sport_seasons.items():
                data[sport][year] = season.to_dict()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_season(self, sport: str, year: str) -> Optional[Season]:
        """Get specific season"""
        seasons = self.load_seasons()
        return seasons.get(sport, {}).get(year)
    
    def save_season(self, season: Season):
        """Save specific season"""
        seasons = self.load_seasons()
        
        if season.sport not in seasons:
            seasons[season.sport] = {}
        
        seasons[season.sport][season.year] = season
        self.save_seasons(seasons)
    
    def delete_season(self, sport: str, year: str):
        """Delete a season"""
        seasons = self.load_seasons()
        
        if sport in seasons and year in seasons[sport]:
            del seasons[sport][year]
            
            # Remove sport if no seasons left
            if not seasons[sport]:
                del seasons[sport]
            
            self.save_seasons(seasons)
    
    # ========================================
    # Teams
    # ========================================
    
    def save_teams(self, sport: str, year: str, series_name: str, teams: List[Team]):
        """Save teams for a series"""
        filename = f"{sport}_{year}_{series_name}.json".replace("/", "_")
        filepath = self.teams_dir / filename
        
        data = [t.to_dict() for t in teams]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_teams(self, sport: str, year: str, series_name: str) -> List[Team]:
        """Load teams for a series"""
        filename = f"{sport}_{year}_{series_name}.json".replace("/", "_")
        filepath = self.teams_dir / filename
        
        if not filepath.exists():
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Team.from_dict(t) for t in data]
        except Exception as e:
            print(f"Error loading teams: {e}")
            return []
    
    # ========================================
    # Matches
    # ========================================
    
    def save_match(self, match: Match):
        """Save match data"""
        if not match.match_id:
            raise ValueError("Match must have an ID")
        
        filepath = self.matches_dir / f"{match.match_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(match.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load_match(self, match_id: str) -> Optional[Match]:
        """Load match data"""
        filepath = self.matches_dir / f"{match_id}.json"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Match.from_dict(data)
        except Exception as e:
            print(f"Error loading match: {e}")
            return None
    
    def list_matches(self) -> List[str]:
        """List all saved match IDs"""
        return [f.stem for f in self.matches_dir.glob("*.json")]
    
    # ========================================
    # Exports
    # ========================================
    
    def get_export_path(self, filename: str) -> Path:
        """Get path for export file"""
        return self.exports_dir / filename
