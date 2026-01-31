# core/json_exporter_v43.py
"""
Improved JSON Exporter for v4.3
Exports directly from LineupEditor data structure
"""

import json
from pathlib import Path
from typing import Dict, List


class JSONExporterV43:
    """
    Export lineup data to JSON in vMix-compatible format
    Uses kategori column directly for field mapping
    """
    
    def __init__(self, lineup_data: Dict, config: Dict):
        """
        Args:
            lineup_data: Data from LineupEditor.get_lineup_data()
            config: App config with folder paths
        """
        self.lineup_data = lineup_data
        self.config = config
    
    def export_lineup_json(self, filepath: str) -> str:
        """
        Export complete lineup to JSON
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        home = self.lineup_data['home']
        away = self.lineup_data['away']
        
        # Build JSON in exact API format
        data = {
            # Away team
            "A_TeamName.Text": away['name'],
            "A_TeamLogo.Source": away.get('logo_teams', ''),
            "A_A_LogoTeam.Source": away.get('logo_pregame', ''),
            
            # Home team
            "H_TeamName.Text": home['name'],
            "H_TeamLogo.Source": home.get('logo_teams', ''),
            "H_LogoTeam.Source": home.get('logo_pregame', ''),
            
            # Headers (static)
            "HeadlineGoalies.Text": "MÅLVAKTER",
            "HeadlineDef.Text": "BACKPAR",
            "HeadlineForw.Text": "FORWARDS",
            
            # Backgrounds (static)
            "BG.Source": "https://vmix-new.hockeyettan.se/scoreImages/lineupBG.png",
            "Divider1.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
            "Divider2.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
            "Divider3.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
        }
        
        # Get resources folder for plates
        resources_folder = self.config.get("resources_folder", "")
        plate_source = f"{resources_folder}\\lineup-PLATE.png" if resources_folder else "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
        
        # Add home players (using kategori column directly!)
        for player in home.get('players', []):
            kategori = player.get('kategori', '')
            if not kategori:
                continue  # Skip players without kategori
            
            prefix = "H_"
            data[f"{prefix}{kategori}_name.Text"] = player.get('name', '').upper()
            data[f"{prefix}{kategori}_number.Text"] = player.get('nr', '')
            data[f"{prefix}{kategori}_plate.Source"] = plate_source
            data[f"{prefix}{kategori}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Fill empty home slots
        self._fill_empty_slots(data, 'H_', plate_source)
        
        # Add away players
        for player in away.get('players', []):
            kategori = player.get('kategori', '')
            if not kategori:
                continue
            
            prefix = "A_"
            data[f"{prefix}{kategori}_name.Text"] = player.get('name', '').upper()
            data[f"{prefix}{kategori}_number.Text"] = player.get('nr', '')
            data[f"{prefix}{kategori}_plate.Source"] = plate_source
            data[f"{prefix}{kategori}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Fill empty away slots
        self._fill_empty_slots(data, 'A_', plate_source)
        
        # Wrap in array
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exporterad lineup till {Path(filepath).name}"
    
    def _fill_empty_slots(self, data: Dict, prefix: str, plate_source: str):
        """Fill empty player slots"""
        categories = [
            'GK1', 'GK2',
            'LD1', 'LD2', 'LD3', 'LD4', 'LD5',
            'RD1', 'RD2', 'RD3', 'RD4', 'RD5',
            'LW1', 'LW2', 'LW3', 'LW4', 'LW5',
            'C1', 'C2', 'C3', 'C4', 'C5',
            'RW1', 'RW2', 'RW3', 'RW4', 'RW5',
            'XD1', 'XD2', 'XD3', 'XD4', 'XD5'
        ]
        
        for cat in categories:
            name_key = f"{prefix}{cat}_name.Text"
            if name_key not in data:
                data[name_key] = ""
                data[f"{prefix}{cat}_number.Text"] = ""
                data[f"{prefix}{cat}_plate.Source"] = ""
                data[f"{prefix}{cat}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
    
    def export_scoreboard_json(self, filepath: str) -> str:
        """
        Export scoreboard data (minimal - just logos and names)
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        home = self.lineup_data['home']
        away = self.lineup_data['away']
        
        # Build minimal scoreboard
        data = {
            "HomeName.Text": home['name'],
            "AwayName.Text": away['name'],
            "HomeLogo.Source": home.get('logo_teams', ''),
            "AwayLogo.Source": away.get('logo_teams', ''),
            
            # Placeholders (will be updated by SLH or OCR)
            "HomeScore.Text": 0,
            "AwayScore.Text": 0,
            "Time.Text": "{0:20:00|mm:ss}",
            "PeriodNr.Text": 1,
            "PeriodText.Text": "PERIOD",
            
            # Empty penalties
            "HomeP1time.Text": "00:00",
            "HomeP2time.Text": "00:00",
            "AwayP1time.Text": "00:00",
            "AwayP2time.Text": "00:00",
            
            # Static images
            "HomeP1bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "HomeP2bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "AwayP1bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "AwayP2bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "PeriodSkylt.Source": "https://vmix-new.hockeyettan.se/scoreImages/periodskylt.png",
            "BG.Source": "https://vmix-new.hockeyettan.se/premagesLogo/topBG.png"
        }
        
        # Wrap in array
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exporterad scoreboard till {Path(filepath).name}"
    
    def export_match_json(self, filepath: str) -> str:
        """
        Export match stats (minimal - SLH only has basic info)
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        home = self.lineup_data['home']
        away = self.lineup_data['away']
        
        # Build minimal match data
        data = {
            "TeamNameHome.Text": home['name'],
            "TeamNameAway.Text": away['name'],
            "HomeName.Text": home['name'],
            "AwayName.Text": away['name'],
            "LogoHome.Source": home.get('logo_pregame', ''),
            "LogoAway.Source": away.get('logo_pregame', ''),
            "HomeLogo.Source": home.get('logo_teams', ''),
            "AwayLogo.Source": away.get('logo_teams', ''),
            
            # Placeholders for stats
            "HomeScore.Text": 0,
            "AwayScore.Text": 0,
            "Time.Text": "{0:20:00|mm:ss}",
            "StatsHomeGoals.Text": 0,
            "StatsAwayGoals.Text": 0,
            "StatsHomeShots.Text": "0 (0, 0, 0)",
            "StatsAwayShots.Text": "0 (0, 0, 0)",
            "StatsHomeSav.Text": 0,
            "StatsAwaySav.Text": 0,
            "StatsHomePP.Text": "0%",
            "StatsAwayPP.Text": "0%",
            "StatsHomePen.Text": "0 min",
            "StatsAwayPen.Text": "0 min",
            
            # Static
            "Headline.Text": "MATCHSTATISTIK",
            "pre_Headline.Text": "MATCHSTART",
            "HeadlineGoals.Text": "MÅL",
            "HeadlineShots.Text": "SKOTT",
            "HeadlineSav.Text": "RÄDDNINGAR",
            "HeadlinePP.Text": "POWERPLAY",
            "HeadlinePen.Text": "UTVISNINGAR",
            "Textrad1.Text": "",
            "Textrad2.Text": "",
            "TextBottom.Text": "",
            "ImgBottom.Source": "",
            "DomareNamn1.Text": "",
            "DomareNamn2.Text": "",
            "DomareNamn3.Text": "",
            "DomareTitel1.Text": "REFEREE",
            "DomareTitel2.Text": "LINESMAN",
            "DomareTitel3.Text": "LINESMAN"
        }
        
        # Wrap in array
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exporterad match till {Path(filepath).name}"
